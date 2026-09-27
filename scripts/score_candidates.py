"""
Step 3 — AI scoring layer.

Reads data/candidates.json (from fetch_candidates.py) and TASTE_PROFILE.md,
sends each candidate to Claude for a relevance score + magazine-caption
blurb, and writes the top N (default 7) to data/picks.json for the
issue-generation step to consume.

Requires an ANTHROPIC_API_KEY environment variable.

Usage:
    python scripts/score_candidates.py
"""

import json
import os
from pathlib import Path

from anthropic import Anthropic

ROOT = Path(__file__).resolve().parent.parent
CANDIDATES_PATH = ROOT / "data" / "candidates.json"
TASTE_PROFILE_PATH = ROOT / "TASTE_PROFILE.md"
OUTPUT_PATH = ROOT / "data" / "picks.json"

MODEL = "claude-sonnet-5"
PICKS_PER_ISSUE = 7

SCORING_PROMPT = """You are curating a personal weekly reading digest. Below is \
the taste profile that defines what belongs in it, followed by a candidate \
article's title and excerpt.

<taste_profile>
{taste_profile}
</taste_profile>

<candidate>
Title: {title}
Source: {source}
Excerpt: {excerpt}
</candidate>

Score this candidate from 0-10 on how well it matches the taste profile \
(10 = exactly the kind of thing that belongs, 0 = clearly wrong fit, e.g. \
a listicle or generic productivity content).

Then write a one-line blurb in a magazine-caption voice (per the profile's \
"Blurb voice" section) that would sell this piece to the reader if it's \
picked — under 20 words, no quotation marks around it.

Also pick ONE tag for it: neuroscience, psychology, self-growth, or \
beautiful-writing.

Respond with ONLY a JSON object, no other text, in exactly this shape:
{{"score": <int 0-10>, "blurb": "<string>", "tag": "<string>"}}"""


def load_taste_profile() -> str:
    return TASTE_PROFILE_PATH.read_text()


def load_candidates() -> list[dict]:
    if not CANDIDATES_PATH.exists():
        raise FileNotFoundError(
            f"{CANDIDATES_PATH} not found — run fetch_candidates.py first."
        )
    with open(CANDIDATES_PATH, "r") as f:
        return json.load(f)


def score_candidate(client: Anthropic, taste_profile: str, candidate: dict) -> dict:
    prompt = SCORING_PROMPT.format(
        taste_profile=taste_profile,
        title=candidate["title"],
        source=candidate["source"],
        excerpt=candidate["excerpt"],
    )
    response = client.messages.create(
        model=MODEL,
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = response.content[0].text.strip()
    # Guard against the model wrapping the JSON in markdown fences anyway
    raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        print(f"  ! could not parse scoring response for '{candidate['title']}': {raw!r}")
        return {"score": 0, "blurb": "", "tag": "self-growth"}
    return result


def main():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise SystemExit("ANTHROPIC_API_KEY environment variable is not set.")

    client = Anthropic(api_key=api_key)
    taste_profile = load_taste_profile()
    candidates = load_candidates()

    if not candidates:
        print("No candidates to score — data/candidates.json is empty.")
        OUTPUT_PATH.write_text("[]")
        return

    scored = []
    for i, candidate in enumerate(candidates, 1):
        print(f"Scoring {i}/{len(candidates)}: {candidate['title'][:60]}...")
        result = score_candidate(client, taste_profile, candidate)
        scored.append({**candidate, **result})

    scored.sort(key=lambda c: c["score"], reverse=True)
    picks = scored[:PICKS_PER_ISSUE]

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(picks, f, indent=2)

    print(f"\nTop {len(picks)} picks written to {OUTPUT_PATH}:")
    for p in picks:
        print(f"  [{p['score']}] {p['title']} — {p['blurb']}")


if __name__ == "__main__":
    main()
