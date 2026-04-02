"""Mode B step 3: read scored_papers.json → publish to channels.

Usage:
    python3 -m src.post [--profile NAME]
"""

import argparse
import json
import sys
import traceback

from .archive import archive_scored_papers
from .config import load_config, load_dotenv, check_env_vars, DEFAULT_PROFILE, STATE_DIR
from .publish import publish, notify_error


def main():
    config = None
    try:
        # Load .env before anything else
        load_dotenv()

        parser = argparse.ArgumentParser(description="Publish scored papers")
        parser.add_argument("--profile", default=DEFAULT_PROFILE,
                            help="Profile name from profiles/ directory (default: %(default)s)")
        args = parser.parse_args()

        config = load_config(args.profile)

        # Check for missing env vars before attempting to publish
        missing = check_env_vars(config)
        if missing:
            for ch, var in missing:
                print(f"ERROR: {var} is not set (required for {ch} channel).")
            print("\nSet the variable in your shell or create a .env file in the repo root:")
            print("  echo 'MASTODON_ACCESS_TOKEN=your-token' >> .env")
            print("\nSee docs/setup-guide.md for details.")
            sys.exit(1)

        # Use profile-specific state file if it exists, else default
        if args.profile != DEFAULT_PROFILE:
            scored_path = STATE_DIR / f"scored_papers_{args.profile}.json"
            if not scored_path.exists():
                scored_path = STATE_DIR / "scored_papers.json"
        else:
            scored_path = STATE_DIR / "scored_papers.json"
        if not scored_path.exists():
            print(f"No scored papers found at {scored_path}")
            print("Run scoring first (Claude Code scheduled task step 2).")
            return

        with open(scored_path, encoding="utf-8") as f:
            data = json.load(f)

        scored_papers = data.get("scored_papers", [])
        total_fetched = data.get("total_fetched", 0)

        publish(config, scored_papers, total_fetched)

        try:
            archive_scored_papers(args.profile, scored_path=scored_path)
        except Exception as e:
            print(f"  WARNING: archive failed: {e}")

        print("Done.")

    except Exception as e:
        error_msg = f"{type(e).__name__}: {e}\n\n{traceback.format_exc()}"
        print(f"\n*** ERROR in post ***\n{error_msg}", file=sys.stderr)
        if config:
            notify_error(config, f"Post error: {type(e).__name__}: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
