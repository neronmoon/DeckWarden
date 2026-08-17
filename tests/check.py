#!/usr/bin/env python3
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "py_modules"))
from list_parse import parse_list_line

SHIM = ROOT / "defaults" / "bin" / "pinentry-deckwarden"


def check_pinentry() -> None:
    env = os.environ.copy()
    env["RBW_PIN"] = "test-master-pin"
    proc = subprocess.Popen(
        [str(SHIM)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
    )
    out, err = proc.communicate("GETPIN\nBYE\n", timeout=5)
    assert proc.returncode == 0, err
    assert "D test-master-pin" in out, out
    assert "OK" in out, out
    print("ok pinentry")


def check_parse() -> None:
    row = parse_list_line("abc-uuid\tSteam\tdeck@example.com")
    assert row == {
        "id": "abc-uuid",
        "name": "Steam",
        "user": "deck@example.com",
    }
    assert parse_list_line("only-id") is None
    assert parse_list_line("id-only\tNameOnly") == {
        "id": "id-only",
        "name": "NameOnly",
        "user": "",
    }
    print("ok parse")


if __name__ == "__main__":
    os.chmod(SHIM, 0o755)
    check_pinentry()
    check_parse()
    print("all checks passed")
