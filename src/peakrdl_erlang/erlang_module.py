from typing import TextIO, Set, Optional, List
import os
import re

from systemrdl.walker import RDLListener, RDLWalker, WalkerAction
from systemrdl.node import AddrmapNode, AddressableNode, RegNode, FieldNode, Node, MemNode

from .state import State
# from .identifier_filter import kw_filter as kwf
# from . import utils

class ErlangModuleGenerator(RDLListener):
    def __init__(self, s: State) -> None:
        self.s = s

        # self.defined_namespace: Set[str]
        # self.defined_namespace = set()
        # self.indent_level = 0

        self.root_node: AddrmapNode
        self.root_node = None

        self.f: TextIO
        self.f = None # type: ignore

    def run(self, path: str, top_nodes: List[AddrmapNode]) -> None:
        with open(path, "w", encoding='utf-8') as f:
            self.f = f

            context = {
                # "ds": self.ds,
                "module": re.sub(r"[^\w]", "_", os.path.basename(path)),
                # "top_nodes": top_nodes,
                # "get_struct_name": utils.get_struct_name,
            }

            # Stream header via jinja
            template = self.s.jj_env.get_template("module.erl")
            template.stream(context).dump(f)
            f.write("\n")

            # Ensure newline before EOF
            f.write("\n")
