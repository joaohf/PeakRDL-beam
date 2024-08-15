import os

from typing import Any, Union

from systemrdl.node import RootNode, AddrmapNode, MemNode, RegfileNode

from .scanner import Scanner
from .state import State
from .erlang_module import ErlangModuleGenerator
from .erlang_header import ErlangHeaderGenerator

class ErlangExporter:
    def export(self, node: Union[RootNode, AddrmapNode], path: str, **kwargs: Any) -> None:
        """
        Parameters
        ----------
        node: AddrmapNode
            Top-level SystemRDL node to export.
        path: str
            Output header file path
        flavor: BeamLanguage
            Select which supported BEAM language to use
        bitfield_order_ltoh: bool
            The packing order of C struct bitfields is implementation defined.
            If True, packing will assume low-to-high bit-packing order.
        """
        # If it is the root node, skip to top addrmap
        if isinstance(node, RootNode):
            top_node = node.top
        else:
            top_node = node

        s = State(top_node, kwargs)

        # Check for stray kwargs
        if kwargs:
            raise TypeError(f"got an unexpected keyword argument '{list(kwargs.keys())[0]}'")

        # Validate and collect info for export
        Scanner(s).run()

        top_nodes = []
        if s.explode_top:
            for child in top_node.children():
                if isinstance(child, (AddrmapNode, MemNode, RegfileNode)):
                    top_nodes.append(child)
        else:
            top_nodes.append(top_node)

        (base_path, ext) = os.path.splitext(path)

        # Write output
        ErlangModuleGenerator(s).run(base_path, top_nodes)
        ErlangHeaderGenerator(s).run(base_path, top_nodes)
