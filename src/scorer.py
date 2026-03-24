"""Score papers using Anthropic API (Mode A)."""

import json
import os

from anthropic import Anthropic

from .config import get_profile


def score_papers(config, papers):
    """Score papers using Anthropic API.

    Args:
        config: loaded config dict
        papers: list of paper dicts from fetch_arxiv

    Returns:
        list of paper dicts with score >= threshold, enriched with
        score, reason, summary fields
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not set.")

    profile = get_profile(config.get("_profile_name"))
    threshold = config.get("scoring_threshold", 85)
    language = config.get("language", "en")
    model = config.get("scoring_model", "claude-sonnet-4-6")
    extra_instructions = config.get("scoring_instructions", "")

    # Style settings
    style = config.get("style", {})
    tone = style.get("tone", "casual")
    emoji_level = style.get("emoji_level", "moderate")

    tone_desc = {
        "casual": "casual colleague tone, friendly and approachable",
        "formal": "formal academic tone, professional",
        "neutral": "neutral tone, matter-of-fact",
    }.get(tone, "casual colleague tone")

    emoji_desc = {
        "none": "No emojis at all",
        "light": "1-2 emojis per recommendation, 0-1 per summary",
        "moderate": "3-4 emojis per recommendation, 1-2 per summary",
        "heavy": "5+ emojis per recommendation, 2-3 per summary 🔥🎯✨🧐💡🚀💥🌟👀⚡",
    }.get(emoji_level, "3-4 emojis per recommendation")

    lang_name = "日本語" if language == "ja" else "English"

    # Build prompt
    papers_json = json.dumps(
        [
            {
                "arxiv_id": p["arxiv_id"],
                "title": p["title"],
                "abstract": p["abstract"][:500],
                "authors": p["authors"][:6],
                "categories": p["categories"],
            }
            for p in papers
        ],
        ensure_ascii=False,
        indent=2,
    )

    prompt = f"""You are an arXiv paper scorer. Score each paper based on the research interest profile below.

## Research Interest Profile
{profile}

## Scoring Criteria
- Score 0-100. Only papers scoring {threshold}+ will be delivered.
- Direct overlap with research interests → high score
- Papers by frequent collaborators → high score
- Related methods/results → moderate score
- General developments in the field → low score

## Output Format
For each paper scoring {threshold} or above, output in {lang_name}:
- score: 0-100
- reason: recommendation text, max 120 chars (why this paper is interesting, {tone_desc}). Emoji: {emoji_desc}
- summary: technical summary, max 120 chars (concise explanation). Emoji: {emoji_desc}

{f"## Additional Instructions{chr(10)}{extra_instructions}" if extra_instructions else ""}

## Papers to Score
{papers_json}

## Response Format
Respond with a JSON array of scored papers (only those scoring {threshold}+):
[{{"arxiv_id": "...", "score": N, "reason": "...", "summary": "..."}}]

If no papers score {threshold}+, respond with an empty array: []
"""

    client = Anthropic(api_key=api_key)
    response = client.messages.create(
        model=model,
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )

    # Parse response
    text = response.content[0].text
    # Extract JSON from response (handle markdown code blocks)
    if "```" in text:
        json_match = text.split("```")[1]
        if json_match.startswith("json"):
            json_match = json_match[4:]
        scored = json.loads(json_match.strip())
    else:
        scored = json.loads(text.strip())

    # Merge scored data back into full paper dicts
    score_map = {s["arxiv_id"]: s for s in scored}
    result = []
    for p in papers:
        if p["arxiv_id"] in score_map:
            s = score_map[p["arxiv_id"]]
            merged = {**p, **s}
            result.append(merged)

    result.sort(key=lambda x: x.get("score", 0), reverse=True)
    return result
