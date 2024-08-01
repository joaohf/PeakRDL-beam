from typing import Dict
import enum

class BeamLanguages(enum.Enum):

    def __init__(self, name: str, d: Dict[str, str]) -> None:
        self.module_extension = d.get("module_extension")
        self.header_extension = d.get("header_extension")

        # Prevent Enum from flattening members into aliases
        self._value_ = name

    erlang = "erlang", {
        "module_extension": "erl",
        "header_extension": "hrl"
    }

    elixir = "elixir", {
        "module_extension": "ex",
        "header_extension": ""
    }

    default = erlang
