"""
Step 2 — Feed aggregator.

Reads config/feeds.yaml, pulls recent entries from every Substack
publication feed and every Medium tag feed, drops anything already sent
in a previous issue, and writes the resulting pool to data/candidates.json
for the scoring step (score_candidates.py) to consume.

Usage:
    python scripts/fetch_candidates.py
"""

import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import feedparser
import yaml

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "config" / "feeds.yaml"
SEEN_PATH = ROOT / "data" / "seen.json"
OUTPUT_PATH = ROOT / "data" / "candidates.json"

MEDIUM_TAG_FEED = "https://medium.com/feed/tag/{tag}"


def load_config() -> dict:
    with open(CONFIG_PATH, "r") as f:
        return yaml.safe_load(f)


def load_seen() -> set:
    if not SEEN_PATH.exists():
        return set()
    with open(SEEN_PATH, "r") as f:
        return set(json.load(f))


def save_seen(seen: set) -> None:
    SEEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(SEEN_PATH, "w") as f:
        json.dump(sorted(seen), f, indent=2)


def entry_to_candidate(entry, source_name: str) -> dict | None:
    link = entry.get("link")
    if not link:
        return None

    published_struct = entry.get("published_parsed") or entry.get("updated_parsed")
    if published_struct:
        published = datetime.fromtimestamp(time.mktime(published_struct), tz=timezone.utc)
    else:
        published = None

    excerpt = entry.get("summary", "")
    # Strip anything that looks like HTML tags from the excerpt — keep it plain
    import re
    excerpt = re.sub("<[^<]+?>", "", excerpt).strip()
    if len(excerpt) > 500:
        excerpt = excerpt[:500].rsplit(" ", 1)[0] + "..."

    return {
        "title": entry.get("title", "").strip(),
        "link": link,
        "source": source_name,
        "excerpt": excerpt,
        "published": published.isoformat() if published else None,
    }


def fetch_feed(url: str, source_name: str, max_age_days: int) -> list[dict]:
    parsed = feedparser.parse(url)
    if parsed.bozo and not parsed.entries:
        print(f"  ! could not read feed for {source_name} ({url}): {parsed.bozo_exception}")
        return []

    cutoff = datetime.now(timezone.utc) - timedelta(days=max_age_days)
    candidates = []
    for entry in parsed.entries:
        candidate = entry_to_candidate(entry, source_name)
        if candidate is None:
            continue
        if candidate["published"]:
            published_dt = datetime.fromisoformat(candidate["published"])
            if published_dt < cutoff:
                continue
        candidates.append(candidate)
    return candidates


def main():
    config = load_config()
    seen = load_seen()
    max_age_days = config.get("max_age_days", 10)

    all_candidates = []

    for pub in config.get("substack_publications", []):
        print(f"Fetching {pub['name']}...")
        all_candidates.extend(fetch_feed(pub["url"], pub["name"], max_age_days))

    for tag in config.get("medium_tags", []):
        url = MEDIUM_TAG_FEED.format(tag=tag)
        print(f"Fetching Medium tag '{tag}'...")
        all_candidates.extend(fetch_feed(url, f"Medium: {tag}", max_age_days))

    # Dedupe against previously-sent links, and against duplicates within this run
    fresh, links_this_run = [], set()
    for candidate in all_candidates:
        link = candidate["link"]
        if link in seen or link in links_this_run:
            continue
        links_this_run.add(link)
        fresh.append(candidate)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(fresh, f, indent=2)

    print(f"\n{len(fresh)} fresh candidates written to {OUTPUT_PATH}")
    print("(seen.json is only updated after an issue is actually generated,")
    print(" so re-running this script is safe and won't lose candidates.)")


if __name__ == "__main__":
    main()
