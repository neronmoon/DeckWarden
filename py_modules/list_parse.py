def parse_list_line(line: str) -> dict[str, str] | None:
    parts = line.rstrip("\n").split("\t")
    if len(parts) < 2:
        return None
    return {
        "id": parts[0],
        "name": parts[1],
        "user": parts[2] if len(parts) > 2 else "",
    }
