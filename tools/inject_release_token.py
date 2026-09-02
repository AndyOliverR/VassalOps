"""Write scoped installs token into a release staging config.local.json (CI only)."""
from __future__ import annotations

import json
import os
import sys


def write_local_config(dest: str, token: str) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(dest)) or ".", exist_ok=True)
    payload = {
        "runtime_boundaries": {
            "registration_github_repo": "AndyOliverR/vassalops-installs",
            "registration_github_token": token,
        }
    }
    with open(dest, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
        f.write("\n")


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    dest = args[0] if args else os.path.join("dist", "staging", "config.local.json")
    token = (os.environ.get("VASSALOPS_INSTALLS_PAT") or "").strip()
    if not token:
        print("VASSALOPS_INSTALLS_PAT is empty; skipped config.local.json inject.")
        return 0
    write_local_config(dest, token)
    print("Injected scoped installs token into release zip (config.local.json).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
