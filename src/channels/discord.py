"""Discord delivery channel via webhook."""

import json
import os
import urllib.request

from .base import Channel


class DiscordChannel(Channel):
    """Post digest to a Discord channel via webhook URL."""

    def __init__(self, config):
        # Allow per-profile webhook: config webhook_url > config env_var > default env var
        env_var = config.get("env_var", "DISCORD_WEBHOOK_URL")
        self.webhook_url = config.get("webhook_url") or os.environ.get(env_var)
        if not self.webhook_url:
            raise RuntimeError(
                f"{env_var} not set. "
                "Create a webhook in Discord (channel settings > Integrations > Webhooks) "
                "and set the URL as an environment variable."
            )
        self.username = config.get("username", "arXiv Digest")
        # mention_target: "<@USER_ID>" or "<@&ROLE_ID>" — prepended to header
        self.mention_target = config.get("mention_target", "")

    @property
    def char_limit(self):
        return 2000

    def publish(self, header, papers):
        # Header message with optional mention
        if self.mention_target:
            header = f"{self.mention_target} {header}"
        self._post(header)

        # Individual paper messages
        for p in papers:
            msg = self._format_paper(p)
            self._post(msg)

        print(f"Discord: posted {len(papers) + 1} messages via webhook")

    def _format_paper(self, paper):
        """Format a single paper as a Discord message (max 2000 chars)."""
        score = paper.get("score", 0)
        cats = ", ".join(paper.get("categories", [])[:3])
        reason = paper.get("reason", "")
        summary = paper.get("summary", "")
        title = paper.get("title", "Untitled")
        url = paper.get("url", "")
        authors = paper.get("authors", [])

        # Extract last names
        last_names = []
        for a in authors:
            if ", " in a:
                last_names.append(a.split(", ")[0])
            else:
                last_names.append(a.split()[-1])
        if len(last_names) > 4:
            author_str = ", ".join(last_names[:4]) + " et al."
        else:
            author_str = ", ".join(last_names)

        parts = [
            f"**⭐ {score}/100** | {cats}",
            f"👤 {author_str}" if author_str else "",
            f"📄 **{title}**",
            "",
            reason,
        ]
        if summary:
            parts += ["", summary]
        parts += ["", url]

        # Remove consecutive empty lines
        cleaned = []
        for p in parts:
            if p == "" and cleaned and cleaned[-1] == "":
                continue
            cleaned.append(p)
        msg = "\n".join(cleaned)

        if len(msg) > 2000:
            msg = msg[:1997] + "..."

        return msg

    def post_text(self, text):
        """Post a plain text message."""
        if len(text) > 2000:
            text = text[:1997] + "..."
        self._post(text)

    def _post(self, content):
        """Post a message via Discord webhook."""
        payload = json.dumps({
            "content": content,
            "username": self.username,
        }).encode("utf-8")

        req = urllib.request.Request(
            self.webhook_url,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "arXiv-digest/1.0",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            # Discord webhooks return 204 No Content on success
            pass
