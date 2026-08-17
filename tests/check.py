#!/usr/bin/env python3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "py_modules"))
from item_parse import entries_from_items


def check_parse() -> None:
    items = [
        {
            "id": "a1",
            "name": "Steam",
            "type": 1,
            "login": {"username": "deck@example.com", "password": "x"},
        },
        {
            "id": "n1",
            "name": "Note",
            "type": 2,
            "login": None,
        },
        {
            "id": "b2",
            "name": "Epic",
            "type": 1,
            "login": {"username": "player", "password": "y"},
        },
    ]
    entries = entries_from_items(items)
    assert entries == [
        {"id": "b2", "name": "Epic", "user": "player"},
        {"id": "a1", "name": "Steam", "user": "deck@example.com"},
    ]
    print("ok parse")


if __name__ == "__main__":
    check_parse()
    print("all checks passed")
