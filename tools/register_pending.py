"""CLI: one-shot pending install registration (used by bootstrap)."""
from __future__ import annotations

import json
import sys

from src.execution.local_auth import maybe_register_pending


def main() -> int:
    result = maybe_register_pending()
    print(json.dumps(result))
    if result.get("skipped"):
        return 0
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
