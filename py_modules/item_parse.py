def entries_from_items(items: list) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    for item in items:
        if item.get("type") != 1:
            continue
        login = item.get("login") or {}
        entries.append(
            {
                "id": item.get("id") or "",
                "name": item.get("name") or "",
                "user": login.get("username") or "",
            }
        )
    entries.sort(key=lambda e: e["name"].lower())
    return entries
