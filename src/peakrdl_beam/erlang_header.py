from typing import TextIO, Set, Optional, List
import os
import re

from systemrdl.walker import RDLListener, RDLWalker, WalkerAction
from systemrdl.node import AddrmapNode, AddressableNode, RegNode, FieldNode, Node, MemNode

from .state import State
from .identifier_filter import kw_filter as kwf
from . import utils

class ErlangHeaderGenerator(RDLListener):
    def __init__(self, s: State) -> None:
        self.s = s

        self.defined_namespace: Set[str]
        self.defined_namespace = set()
        self.indent_level = 0

        self.root_node: AddrmapNode
        self.root_node = None

        self.f: TextIO
        self.f = None # type: ignore

    def run(self, base_path: str, top_nodes: List[AddrmapNode]) -> None:
        path = base_path + f".{self.s.flavor.header_extension}"

        with open(path, "w", encoding='utf-8') as f:
            self.f = f

            context = {
                "module": re.sub(r"[^\w]", "_", os.path.basename(path).split('.')[0]),
            }

            # Stream header via jinja
            template = self.s.jj_env.get_template("header.hrl")
            template.stream(context).dump(f)
            f.write("\n")

            # Generate definitions
            for node in top_nodes:
                self.root_node = node
                RDLWalker().walk(node, self)

            # Ensure newline before EOF
            f.write("\n")

    def push_indent(self) -> None:
        self.indent_level += 1

    def pop_indent(self) -> None:
        self.indent_level -= 1

    def write(self, s: str) -> None:
        if self.indent_level:
            self.f.write("    " * self.indent_level)
        self.f.write(s)

    def get_node_prefix(self, node: AddressableNode) -> str:
        return utils.get_node_prefix(self.s, self.root_node, node)

    def get_struct_name(self, node: AddressableNode) -> str:
        return utils.get_struct_name(self.s, self.root_node, node)

    def get_friendly_name(self, node: Node) -> str:
        return utils.get_friendly_name(self.s, self.root_node, node)

    def write_bitfields(self, grp_name: str, regwidth: int, fields: List[FieldNode]) -> None:
        if not fields:
            return
        
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
                pfields.append(f"    {kwf(field.inst_name)}:{field.width:d}")
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
                pfields.append(f"    {kwf(field.inst_name)}:{field.width:d}")
                #self.write(f"{kwf(field.inst_name)}:{field.width:d},\n")
                current_offset += field.width
        
        self.write(",\n".join(pfields))

    def write_define_bit_syntax(self, grp_name: str, union_name: str, regwidth: int, fields: List[FieldNode]) -> None:
        if not fields:
            return
        
        self.write(f"-define({union_name},\n")
        #self.push_indent()
        self.write_bitfields(grp_name, regwidth, fields)
        #self.pop_indent()
        self.write(f"\n).\n")

    def write_record(self, node: RegNode) -> None:
        union_name = self.get_struct_name(node)
        pfields = []

        self.write(f"-record({union_name}, {{\n")
        
        for field in node.fields():
            pfields.append(f"    {kwf(field.inst_name.lower())}")

        self.write(",\n".join(pfields))

        self.write("\n}).\n")

    def enter_Reg(self, node: RegNode) -> Optional[WalkerAction]:
        prefix = self.get_node_prefix(node).upper()

        if prefix in self.defined_namespace:
            return WalkerAction.SkipDescendants
        self.defined_namespace.add(prefix)

        self.write(f"\n% {self.get_friendly_name(node)}\n")

        for field in node.fields():
            field_prefix = prefix + "__" + field.inst_name.upper()

            bm = ((1 << field.width) - 1) << field.low
            self.write(f"-define({field_prefix}_bm, 16#{bm:x}).\n")
            self.write(f"-define({field_prefix}_bp, {field.low:d}).\n")
            self.write(f"-define({field_prefix}_bw, {field.width:d}).\n")

            reset = field.get_property('reset')
            if isinstance(reset, int):
                self.write(f"-define({field_prefix}_reset, 16#{reset:x}).\n")

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

        # Sort fields into their respective categories
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

        regwidth = node.get_property('regwidth')

        self.write_define_bit_syntax("f", union_name.upper() + "_f", regwidth, f_fields)
        self.write_define_bit_syntax("fr", union_name.upper() + "_fr", regwidth, fr_fields)
        self.write_define_bit_syntax("fw", union_name.upper() + "_fw", regwidth, fw_fields)

        print(f"{union_name}")

        self.write_record(node)