from typing import Optional, List

from systemrdl.walker import RDLListener, RDLWalker, WalkerAction
from systemrdl.node import AddrmapNode, RegNode, AddressableNode, FieldNode

from .state import State

class Scanner(RDLListener):
    def __init__(self, s: State) -> None:
        self.s = s
        self.msg = s.top_node.env.msg

        self.prev_reg_stack: List[RegNode]
        self.prev_reg_stack = []

        self.indent = 0

    @property
    def top_node(self) -> AddrmapNode:
        return self.s.top_node

    def run(self) -> None:
        RDLWalker().walk(self.top_node, self)
        if self.msg.had_error:
            self.msg.fatal(
                "Unable to export due to previous errors"
            )

    def enter_AddressableComponent(self, node: AddressableNode) -> Optional[WalkerAction]:
        if not isinstance(node, RegNode):
            self.prev_reg_stack.append(None)
        return WalkerAction.Continue

    def exit_AddressableComponent(self, node: AddressableNode) -> Optional[WalkerAction]:
        if not isinstance(node, RegNode):
            self.prev_reg_stack.pop()
        return WalkerAction.Continue
    
    def enter_Component(self, node):
        if not isinstance(node, FieldNode):
            print("\t"*self.indent, node.get_path_segment())
            self.indent += 1

    def enter_Field(self, node):
        # Print some stuff about the field
        bit_range_str = "[%d:%d]" % (node.high, node.low)
        sw_access_str = "sw=%s" % node.get_property('sw').name
        print("\t"*self.indent, bit_range_str, node.get_path_segment(), sw_access_str)

    def exit_Component(self, node):
        if not isinstance(node, FieldNode):
            self.indent -= 1

    def enter_Reg(self, node: RegNode) -> Optional[WalkerAction]:

        # Collect information about overlapping fields, if any.
        overlapping_fields = []
        fields = list(node.fields())
        reg_bitmask = 0
        for i, field in enumerate(fields):
            field_bitmask = ((1 << field.width) - 1) << field.low
            if field_bitmask & reg_bitmask:
                # this field overlaps with a prior one
                # Determine which one
                for prior_field in fields[0:i]:
                    if prior_field.high >= field.low:
                        if prior_field.inst_name not in overlapping_fields:
                            overlapping_fields.append(prior_field.inst_name)

                if field.inst_name not in overlapping_fields:
                    overlapping_fields.append(field.inst_name)

            reg_bitmask |= field_bitmask
        if overlapping_fields:
            # Save infor about this register for later.
            self.s.overlapping_fields[node.get_path()] = overlapping_fields


        # Check previous adjacent register for overlap
        prev_reg = self.prev_reg_stack[-1]
        if prev_reg and ((prev_reg.raw_address_offset + prev_reg.total_size) > node.raw_address_offset):
            # registers overlap!

            # Registers shall be co-located.
            # This restriction guarantees that overlaps can only happen in pairs,
            # and avoids the more complex overlap scenarios that involve multiple registers.
            if (
                prev_reg.raw_address_offset != node.raw_address_offset # Same offset
                or prev_reg.size != node.size # Same size
                or prev_reg.total_size != node.total_size # Same array footprint
            ):
                self.msg.error(
                    "C header export currently only supports registers that are co-located. "
                    f"See registers: '{prev_reg.inst_name}' and '{node.inst_name}.'",
                    node.inst.inst_src_ref
                )

            # Save information about register overlap pair
            self.ds.overlapping_reg_pairs[prev_reg.get_path()] = node.inst_name

        # Check for sparse register arrays
        if node.is_array and node.array_stride > node.size:
            self.msg.error(
                "C header export does not support sparse arrays of registers. "
                f"See register: '{node.inst_name}.'",
                node.inst.inst_src_ref
            )

        return WalkerAction.SkipDescendants

    def exit_Reg(self, node: RegNode) -> None:
        self.prev_reg_stack[-1] = node