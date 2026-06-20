"""Parse the `usb_path = alias` match file (one camera per line)."""


def parse_match(path):
    """Read the match file and return {alias: usb_path}.

    Blank lines and `#` comments are ignored; each line is split on the first `=`.
    """
    matches = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            pair = _parse_line(line)
            if pair is not None:
                usb_path, alias = pair
                matches[alias] = usb_path
    return matches


def _parse_line(line):
    """Return (usb_path, alias), or None for blank/comment/invalid lines."""
    line = line.strip()
    if not line or line.startswith("#"):
        return None
    if "=" not in line:
        return None
    usb_path, alias = line.split("=", 1)
    return usb_path.strip(), alias.strip()
