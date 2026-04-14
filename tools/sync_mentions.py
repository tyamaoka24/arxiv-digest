#!/usr/bin/env python3
"""Regenerate DISCORD_MENTION_* entries in .env from research-collab.

The canonical source of subscriber Discord IDs is
    ~/Claude/research-collab/collaborators.yaml
(git-crypt'd, layer 3). This script reads that file, finds entries whose
`id` matches an arxiv-digest profile directory and which have a
`discord_id` set, and writes the corresponding DISCORD_MENTION_<ID>
entries into the local `.env` (creating it if absent).

Run this after setting up a new machine — once `research-collab` is
unlocked (see ~/Claude/secrets-config/CLAUDE.md for the git-crypt key
restore procedure), execute:

    python3 -m tools.sync_mentions

Non-mention entries in `.env` (webhooks, API keys) are preserved; only
lines matching `^DISCORD_MENTION_<NAME>=` are replaced.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = REPO_ROOT / ".env"
COLLAB_PATH = Path.home() / "Claude" / "research-collab" / "collaborators.yaml"
PROFILES_DIR = REPO_ROOT / "profiles"


def load_mentions() -> dict[str, str]:
    """Return {profile_id_upper: "<@NNN>"} for profiles with a discord_id."""
    if not COLLAB_PATH.exists():
        sys.exit(
            f"error: {COLLAB_PATH} not found. "
            f"git clone the research-collab repo and git-crypt unlock it first "
            f"(see ~/Claude/secrets-config/CLAUDE.md)."
        )
    with COLLAB_PATH.open() as f:
        entries = yaml.safe_load(f) or []
    profile_ids = {p.name for p in PROFILES_DIR.iterdir() if p.is_dir()}

    out: dict[str, str] = {}
    for e in entries:
        pid = e.get("id")
        did = e.get("discord_id")
        if pid and did and pid in profile_ids:
            out[pid.upper()] = f"<@{did}>"
    return out


def patch_env(mentions: dict[str, str]) -> None:
    """Write/replace DISCORD_MENTION_<NAME>=<@NNN> lines in .env."""
    lines: list[str] = []
    if ENV_PATH.exists():
        lines = ENV_PATH.read_text().splitlines()

    pat = re.compile(r"^DISCORD_MENTION_([A-Z0-9_]+)=")
    seen: set[str] = set()
    new_lines: list[str] = []
    for line in lines:
        m = pat.match(line)
        if m:
            name = m.group(1)
            if name in mentions:
                new_lines.append(f"DISCORD_MENTION_{name}={mentions[name]}")
                seen.add(name)
            # else: profile removed from registry — drop the line
        else:
            new_lines.append(line)

    for name, val in mentions.items():
        if name not in seen:
            new_lines.append(f"DISCORD_MENTION_{name}={val}")

    # Trailing newline hygiene.
    content = "\n".join(new_lines)
    if not content.endswith("\n"):
        content += "\n"

    ENV_PATH.write_text(content)
    ENV_PATH.chmod(0o600)
    print(f"wrote {len(mentions)} DISCORD_MENTION_* entries to {ENV_PATH}")
    for name in sorted(mentions):
        print(f"  DISCORD_MENTION_{name}")


if __name__ == "__main__":
    patch_env(load_mentions())
