"""Dispatch scored papers to enabled delivery channels."""

from .config import get_enabled_channels
from .channels.discord import DiscordChannel
from .channels.mastodon import MastodonChannel
from .channels.stdout import StdoutChannel

CHANNEL_CLASSES = {
    "discord": DiscordChannel,
    "mastodon": MastodonChannel,
    "stdout": StdoutChannel,
}


def notify_error(config, error_msg):
    """Send error notification to enabled channels.

    Best-effort: if notification itself fails, just print to stderr.
    """
    language = config.get("language", "en")
    if language == "ja":
        header = "⚠️ arXiv ダイジェスト エラー"
    else:
        header = "⚠️ arXiv Digest Error"

    message = f"{header}\n\n{error_msg}"

    enabled = get_enabled_channels(config)
    for name, settings in enabled:
        cls = CHANNEL_CLASSES.get(name)
        if cls is None:
            continue
        try:
            channel = cls(settings)
            channel.post_text(message)
        except Exception:
            print(f"  (Could not send error notification to {name})")


def publish(config, scored_papers, total_fetched):
    """Publish scored papers to all enabled channels.

    Args:
        config: loaded config dict
        scored_papers: list of paper dicts with score, reason, summary
        total_fetched: total number of papers fetched from arXiv
    """
    threshold = config.get("scoring_threshold", 85)
    scored_papers = [p for p in scored_papers if p.get("score", 0) >= threshold]

    if not scored_papers:
        print(f"No papers scoring >= {threshold} to publish.")
        return

    language = config.get("language", "en")
    if language == "ja":
        header = (
            f"📚 arXiv新着ダイジェスト\n"
            f"本日の新着 {total_fetched} 件中 {len(scored_papers)} 件をお届けします。"
        )
    else:
        header = (
            f"📚 arXiv Daily Digest\n"
            f"Delivering {len(scored_papers)} papers out of {total_fetched} new submissions."
        )

    enabled = get_enabled_channels(config)
    if not enabled:
        print("No channels enabled. Enable at least one in config.yaml.")
        return

    for name, settings in enabled:
        cls = CHANNEL_CLASSES.get(name)
        if cls is None:
            print(f"Channel '{name}' not implemented yet, skipping.")
            continue
        try:
            channel = cls(settings)
            channel.publish(header, scored_papers)
        except Exception as e:
            print(f"Error publishing to {name}: {e}")
