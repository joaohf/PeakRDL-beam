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