"""Fetch arXiv papers for ALL active profiles in a single RSS call.

Usage:
    python3 -m src.fetch_all [--force]
"""

import argparse
import json
import sys
import traceback
from datetime import date

from .config import (
    load_config, load_dotenv, get_profile,
    list_active_profiles, STATE_DIR,
)
from .fetch_arxiv import fetch_new_papers


def main():
    try:
        parser = argparse.ArgumentParser(
            description="Fetch arXiv papers for all active profiles")
        parser.add_argument("--force", action="store_true",
                            help="Run even on weekends")
        args = parser.parse_args()

        load_dotenv()

        # Check weekend
        weekday = date.today().weekday()
        if weekday in (5, 6) and not args.force:
            day_name = "Saturday" if weekday == 5 else "Sunday"
            print(f"Today is {day_name} — no arXiv updates.")
            return

        profiles = list_active_profiles()
        if not profiles:
            print("No active profiles found.")
            return

        # Collect union of categories across all profiles
        all_categories = set()
        profile_configs = {}
        for name in profiles:
            config = load_config(name)
            profile_configs[name] = config
            cats = config.get("arxiv_categories", [])
            all_categories.update(cats)

        if not all_categories:
            print("No arXiv categories configured across profiles.")
            return

        print(f"Active profiles: {', '.join(profiles)}")
        print(f"Union categories: {', '.join(sorted(all_categories))}")

        # Single fetch for all categories
        print("Fetching arXiv RSS...")
        papers = fetch_new_papers(sorted(all_categories))
        print(f"  Found {len(papers)} new papers")

        if not papers:
            print("No new papers found.")
            return

        # Write per-profile state files
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        for name in profiles:
            config = profile_configs[name]
            profile_text = get_profile(name)

            output_path = STATE_DIR / f"today_papers_{name}.json"
            output = {
                "date": date.today().isoformat(),
                "total_papers": len(papers),
                "profile": profile_text,
                "config": {
                    "scoring_threshold": config.get("scoring_threshold", 85),
                    "language": config.get("language", "en"),
                    "scoring_instructions": config.get(
                        "scoring_instructions", ""),
                },
                "papers": papers,
            }
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(output, f, indent=2, ensure_ascii=False)
            print(f"  Wrote {output_path.name}")

        print("Ready for scoring.")

    except Exception as e:
        error_msg = f"{type(e).__name__}: {e}\n\n{traceback.format_exc()}"
        print(f"\n*** ERROR in fetch_all ***\n{error_msg}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
