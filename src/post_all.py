"""Post scored papers for ALL active profiles.

Usage:
    python3 -m src.post_all
"""

import json
import sys
import traceback

from .config import (
    load_config, load_dotenv, check_env_vars,
    list_active_profiles, STATE_DIR,
)
from .publish import publish, notify_error


def main():
    load_dotenv()

    profiles = list_active_profiles()
    if not profiles:
        print("No active profiles found.")
        return

    errors = []
    for name in profiles:
        print(f"\n--- {name} ---")
        try:
            config = load_config(name)

            missing = check_env_vars(config)
            if missing:
                for ch, var in missing:
                    print(f"  ERROR: {var} not set (required for {ch})")
                errors.append((name, f"Missing env vars: {missing}"))
                continue

            scored_path = STATE_DIR / f"scored_papers_{name}.json"
            if not scored_path.exists():
                print(f"  No scored papers at {scored_path} — skipping")
                continue

            with open(scored_path, encoding="utf-8") as f:
                data = json.load(f)

            scored_papers = data.get("scored_papers", [])
            total_fetched = data.get("total_fetched", 0)

            publish(config, scored_papers, total_fetched)
            print(f"  Done.")

        except Exception as e:
            msg = f"{type(e).__name__}: {e}"
            print(f"  ERROR: {msg}", file=sys.stderr)
            errors.append((name, msg))
            try:
                config = load_config(name)
                notify_error(config, f"Post error ({name}): {msg}")
            except Exception:
                pass

    if errors:
        print(f"\n*** {len(errors)} profile(s) had errors ***")
        for name, msg in errors:
            print(f"  {name}: {msg}")
        sys.exit(1)

    print("\nAll profiles posted successfully.")


if __name__ == "__main__":
    main()
