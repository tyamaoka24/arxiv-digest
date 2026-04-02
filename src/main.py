"""Mode A entry point: fetch → score (API) → publish.

Usage:
    python3 -m src.main [--profile NAME]
"""

import argparse
import sys
import traceback
from datetime import date

from .archive import archive_scored_papers
from .config import load_config, load_dotenv, check_env_vars, DEFAULT_PROFILE
from .fetch_arxiv import fetch_new_papers
from .profile_update import check_for_profile_updates
from .scorer import score_papers
from .publish import publish, notify_error


def main():
    config = None
    try:
        # Load .env before anything else
        load_dotenv()

        parser = argparse.ArgumentParser(description="arXiv digest (Mode A)")
        parser.add_argument("--profile", default=DEFAULT_PROFILE,
                            help="Profile name from profiles/ directory (default: %(default)s)")
        args = parser.parse_args()

        config = load_config(args.profile)

        # Check for missing env vars early
        missing = check_env_vars(config)
        if missing:
            for ch, var in missing:
                print(f"WARNING: {var} is not set (required for {ch} channel).")
            print("Publishing may fail. Set variables or create a .env file.")
        config["_profile_name"] = args.profile
        categories = config.get("arxiv_categories", [])

        if not categories:
            print("No arXiv categories configured. Set arxiv_categories in config.yaml.")
            return

        # Check weekend
        weekday = date.today().weekday()
        if weekday in (5, 6):
            day_name = "Saturday" if weekday == 5 else "Sunday"
            print(f"Today is {day_name} — no arXiv updates.")
            return

        # Fetch
        print("Fetching arXiv RSS...")
        papers = fetch_new_papers(categories)
        print(f"  Found {len(papers)} new papers")

        if not papers:
            print("No new papers found.")
            return

        # Score
        print("Scoring papers with API...")
        scored = score_papers(config, papers)
        print(f"  {len(scored)} papers scored above threshold")

        # Publish
        publish(config, scored, len(papers))

        # Archive
        try:
            archive_scored_papers(
                args.profile,
                data={"total_fetched": len(papers), "scored_papers": scored},
            )
        except Exception as e:
            print(f"  WARNING: archive failed: {e}")

        # Auto-update INSPIRE profiles if registrants have new papers
        print("Checking for profile updates...")
        updated = check_for_profile_updates(papers)
        if updated:
            names = ", ".join(n for n, _ in updated)
            print(f"  Updated INSPIRE profiles: {names}")
        else:
            print("  No profile updates needed.")

        print("Done.")

    except Exception as e:
        error_msg = f"{type(e).__name__}: {e}\n\n{traceback.format_exc()}"
        print(f"\n*** ERROR ***\n{error_msg}", file=sys.stderr)
        if config:
            notify_error(config, f"{type(e).__name__}: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
