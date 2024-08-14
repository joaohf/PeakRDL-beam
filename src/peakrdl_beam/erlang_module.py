from typing import TextIO, Set, Optional, List
import os
import io
import re

from systemrdl.walker import RDLListener, RDLWalker, WalkerAction
from systemrdl.node import AddrmapNode, AddressableNode, RegNode, FieldNode, Node, MemNode

from .state import State
from .identifier_filter import kw_filter as kwf
from . import utils

class ErlangModuleGenerator(RDLListener):
    def __init__(self, s: State) -> None:
        self.s = s

        self.defined_namespace: Set[str]
        self.defined_namespace = set()
        self.exported_functions: Set[str]
        self.exported_functions = set()
        self.indent_level = 0

        self.root_node: AddrmapNode
        self.root_node = None

        self.f: io.StringIO
        self.f = io.StringIO() # type: ignore

    def run(self, base_path: str, top_nodes: List[AddrmapNode]) -> None:
        path = base_path + f".{self.s.flavor.module_extension}"

        # Generate definitions
        for node in top_nodes:
            self.root_node = node
            RDLWalker().walk(node, self)

        with open(path, "w", encoding='utf-8') as f:
            context = {
                "module": re.sub(r"[^\w]", "_", os.path.basename(path).split('.')[0]),
                "exported_functions": self.exported_functions
            }

            # Stream header via jinja
            template = self.s.jj_env.get_template("module.erl")
            template.stream(context).dump(f)
            f.write("\n")

            f.write(self.f.getvalue())

            # Ensure newline before EOF
            f.write("\n")

    def push_indent(self) -> None:
        self.indent_level += 1

    def pop_indent(self) -> None:
        self.indent_level -= 1

    def write(self, s: str, indent=True) -> None:
        if self.indent_level and indent:
            self.f.write("    " * self.indent_level)
        self.f.write(s)

    def get_node_prefix(self, node: AddressableNode) -> str:
        return utils.get_node_prefix(self.s, self.root_node, node)

    def get_struct_name(self, node: AddressableNode) -> str:
        return utils.get_struct_name(self.s, self.root_node, node)

    def get_friendly_name(self, node: Node) -> str:
        return utils.get_friendly_name(self.s, self.root_node, node)

    def write_bitfields(self, fields: List[FieldNode]) -> None:
        if not fields:
            return
        
        pfields = []

        for field in fields:
            pfields.append(f"        {kwf(field.inst_name.lower())} = {field.inst_name.upper()}")
        
        self.write(",\n".join(pfields))
        self.write("\n")

    def write_serialize_arguments(self, fields: List[FieldNode]) -> None:
        if not fields:
            return
        
        pfields = []

        for field in fields:
            pfields.append(f"{field.inst_name.upper()}")
        
        self.write(", ".join(pfields))

    def write_bit_syntax(self, regwidth: int, fields: List[FieldNode]) -> None:
        if not fields:
            return
        
        self.write("<<")
        
        pfields = []
        # if regwidth > 64:
        #     # TODO: add support for this
        #     self.root_node.env.msg.fatal(
        #         "C header bit-fields for registers wider than 64-bits is not supported yet",
        #         fields[0].parent.inst.inst_src_ref
        #     )

        if self.s.bitfield_order_ltoh:
            # TODO: double check it
            # Bits are packed in struct LSb --> MSb
            current_offset = 0
            for field in fields:
                # if field.low > current_offset:
                #     self.write(f"uint{regwidth}_t :{field.low - current_offset:d};\n")
                #     current_offset = field.low
                pfields.append(f"{field.inst_name.upper()}:{field.width:d}")
                #self.write(f"{kwf(field.inst_name)}:{field.width:d},\n")
                current_offset += field.width

            # if current_offset < regwidth:
            #     self.write(f"uint{regwidth}_t :{regwidth - current_offset:d};\n")
        else:
            # TODO: double check it
            # Bits are packed in struct MSb --> LSb
            current_offset = 0
            for field in fields:
                # if field.low > current_offset:
                #     self.write(f"uint{regwidth}_t :{field.low - current_offset:d};\n")
                #     current_offset = field.low
                pfields.append(f"{field.inst_name.upper()}:{field.width:d}")
                #self.write(f"{kwf(field.inst_name)}:{field.width:d},\n")
                current_offset += field.width
        
        self.write(", ".join(pfields), False)

        self.write(">>", False)

    def write_deserialize_function(self, fields: List[FieldNode], func_name, macro_name, union_name, node: RegNode):
        if not fields:
            return
        
        func_name = "des_" + func_name

        self.exported_functions.add(func_name + "/1")
        self.write("\n")
        name_str = node.get_property('name', default=None)
        desc_str = node.get_property('desc', default=None)

        self.write(f"%% @doc Deserialize '{name_str}' register\n")
        self.write_function_description(desc_str)
        self.write("%% @end\n")

        self.write(f"{func_name}(<<?{macro_name}>>) ->\n")
            
        self.push_indent()
        self.write(f"#{union_name}{{\n")
        self.pop_indent()
            
        self.write_bitfields(fields)

        self.push_indent()
        self.write("}.\n")
        self.pop_indent()

    def write_serialize_function(self, fields: List[FieldNode], func_name, arity, node: RegNode):
        if not fields:
            return
        
        func_name = "ser_" + func_name

        regwidth = node.get_property('regwidth')

        self.exported_functions.add(func_name + f"/{arity}")
        self.write("\n")
        name_str = node.get_property('name', default=None)
        desc_str = node.get_property('desc', default=None)

        self.write(f"%% @doc Serialize '{name_str}' register\n")
        self.write_function_description(desc_str)
        self.write("%% @end\n")

        # function clause
        self.write(f"{func_name}(")
        # function body
        self.write_serialize_arguments(fields)
        self.write(") ->\n")

        self.push_indent()
        self.write_bit_syntax(regwidth, fields)

        self.pop_indent()
        self.write(".\n")

    def write_function_description(self, description):
        if not description:
            return

        desc_str = "\n".join([ "%% " + s for s in description.splitlines()])

        # Use verbatim quoting for function description
        self.write(f"%% ```\n{desc_str}\n%% '''\n")
    
    def enter_Reg(self, node: RegNode) -> Optional[WalkerAction]:
        prefix = self.get_node_prefix(node).upper()

        if prefix in self.defined_namespace:
            return WalkerAction.SkipDescendants
        self.defined_namespace.add(prefix)

        # self.write(f"\n% {self.get_friendly_name(node)}\n")

        # for field in node.fields():
        #     field_prefix = prefix + "__" + field.inst_name.upper()

        #     bm = ((1 << field.width) - 1) << field.low
        #     self.write(f"-define({field_prefix}_bm, 16#{bm:x}).\n")
        #     self.write(f"-define({field_prefix}_bp, {field.low:d}).\n")
        #     self.write(f"-define({field_prefix}_bw, {field.width:d}).\n")

        #     reset = field.get_property('reset')
        #     if isinstance(reset, int):
        #         self.write(f"-define({field_prefix}_reset, 16#{reset:x}).\n")

        # No need to traverse fields
        return WalkerAction.SkipDescendants


    def exit_Reg(self, node: RegNode) -> None:
        if not self.s.generate_bitfields:
            return

        union_name = self.get_struct_name(node)
        if union_name in self.defined_namespace:
            # Already defined. Skip
            return
        self.defined_namespace.add(union_name)

        # # Sort fields into their respective categories
        overlapping_fields = self.s.overlapping_fields.get(node.get_path(), [])
        fr_fields = []
        fw_fields = []
        f_fields = []
        for field in node.fields():
            if field.inst_name in overlapping_fields:
                # Is an overlapping field.
                # Guaranteed to be either read-only or write-only
                if field.is_sw_readable:
                    fr_fields.append(field)
                else:
                    fw_fields.append(field)
            else:
                f_fields.append(field)
        
        arity_f = len(f_fields)
        func_name_f = union_name + "_f"
        macro_name_f = union_name.upper() + "_f"
        arity_fr = len(fr_fields)
        func_name_fr = union_name + "_fr"
        macro_name_fr = union_name.upper() + "_fr"
        arity_fw = len(fw_fields)
        func_name_fw = union_name + "_fw"
        macro_name_fw = union_name.upper() + "_fw"

        self.write_deserialize_function(f_fields, func_name_f, macro_name_f, union_name, node)
        self.write_serialize_function(f_fields, func_name_f, arity_f, node)

        self.write_deserialize_function(fw_fields, func_name_fw, macro_name_fw, union_name, node)
        self.write_serialize_function(fw_fields, func_name_fw, arity_fw, node)

        self.write_deserialize_function(fr_fields, func_name_fr, macro_name_fr, union_name, node)
        self.write_serialize_function(fr_fields, func_name_fr, arity_fr, node)