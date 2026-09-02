"""CLI: launch/close handshake (used by bootstrap and apply-after-exit)."""
from __future__ import annotations

import argparse
import json
import os
import sys


def _root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def main() -> int:
    parser = argparse.ArgumentParser(description="VassalOps launch/close handshake")
    parser.add_argument("--reason", default="launch", choices=("launch", "close"))
    parser.add_argument("--apply", action="store_true", help="Apply a newer GitHub Release now")
    parser.add_argument("--stage", action="store_true", help="Download update for apply-after-exit")
    parser.add_argument("--apply-pending", action="store_true", help="Apply a staged zip only")
    args = parser.parse_args()

    root = _root()
    os.chdir(root)
    if root not in sys.path:
        sys.path.insert(0, root)

    if args.apply_pending:
        from src.execution.product_update import apply_pending_update

        result = apply_pending_update(root)
        print(json.dumps(result))
        return 0 if result.get("ok") else 1

    from src.execution.handshake import run_handshake

    result = run_handshake(
        reason=args.reason,
        apply_product=args.apply,
        stage_product=args.stage,
        root=root,
    )
    print(json.dumps(result))
    if result.get("skipped"):
        return 0
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
