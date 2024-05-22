from typing import Any, Union

from systemrdl.node import RootNode, AddrmapNode, MemNode, RegfileNode

from .scanner import Scanner
from .state import State
from .erlang_module import ErlangModuleGenerator

class ErlangExporter:
    def export(self, node: Union[RootNode, AddrmapNode], path: str, **kwargs: Any) -> None:
        """
        Parameters
        ----------
        node: AddrmapNode
            Top-level SystemRDL node to export.
        path: str
            Output header file path
        """
        # If it is the root node, skip to top addrmap
        if isinstance(node, RootNode):
            top_node = node.top
        else:
            top_node = node

        s = State(top_node, kwargs)

        Scanner(s).run()

        ErlangModuleGenerator(s).run(path, top_node)