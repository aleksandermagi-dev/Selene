from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from selene.db import connect, init_db  # noqa: E402
from selene.public_safe_showcase import run_public_safe_showcase  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run Selene's public-safe showcase in disposable state."
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Print compact JSON instead of the default readable output.",
    )
    args = parser.parse_args()

    with tempfile.TemporaryDirectory(prefix="selene-public-showcase-") as temp_dir:
        db_path = Path(temp_dir) / "showcase.sqlite3"
        conn = connect(db_path)
        try:
            init_db(conn)
            result = run_public_safe_showcase(conn)
            result["state_boundary"]["temporary_database_deleted_after_exit"] = True
        finally:
            conn.close()

        print(
            json.dumps(
                result,
                indent=None if args.compact else 2,
                sort_keys=True,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
