
ERL_KEYWORDS = {
    "case", "receive", "send", "maybe", "if"
}

def kw_filter(s: str) -> str:
    """
    Make all user identifiers 'safe' and ensure they do not collide with
    Erlang keywords.

    If an Erlang keyword is encountered, make it an atom
    """
    if s in ERL_KEYWORDS:
        s = f"'{s}'"
    return s
