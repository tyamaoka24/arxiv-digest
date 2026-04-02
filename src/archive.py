"""Archive scored papers to date-partitioned JSON files."""

import json
from datetime import date
from pathlib import Path

ARCHIVE_DIR = Path(__file__).resolve().parent.parent / "archive"


def archive_scored_papers(profile_name, *, scored_path=None, data=None):
    """Copy scored papers to archive/{year}/{month}/{date}_{profile}.json.

    Provide either scored_path (Path to JSON file) or data (dict).
    Idempotent: re-running the same day overwrites the file.
    Returns the archive path on success, None if nothing to archive.
    """
    if data is None:
        if scored_path is None or not scored_path.exists():
            return None
        with open(scored_path, encoding="utf-8") as f:
            data = json.load(f)

    today = date.today()
    dest_dir = ARCHIVE_DIR / str(today.year) / f"{today.month:02d}"
    dest_dir.mkdir(parents=True, exist_ok=True)

    dest = dest_dir / f"{today.isoformat()}_{profile_name}.json"
    with open(dest, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"  Archived → {dest.relative_to(ARCHIVE_DIR.parent)}")
    return dest
