#!/usr/bin/env python3
"""
Build news.json for the F1 2026 globe dashboard.

Pulls RSS/Atom from several F1 outlets, merges them, drops near-duplicate
stories, prunes anything older than MAX_AGE_DAYS, sorts newest-first and
writes a small JSON file the dashboard fetches same-origin (no CORS).

Standard library only - nothing to install.
"""

import json
import re
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from xml.etree import ElementTree as ET

# --------------------------------------------------------------------------
MAX_AGE_DAYS = 14      # anything older than this is dropped automatically
MAX_ITEMS    = 40      # cap the ticker so the file stays small
TIMEOUT      = 20
UA           = "Mozilla/5.0 (compatible; f1-dashboard-news/1.0)"

FEEDS = [
    # verified live (BBC returns items; RaceFans/The Race are standard WordPress feeds)
    ("BBC Sport",    "https://feeds.bbci.co.uk/sport/formula1/rss.xml"),
    ("RaceFans",     "https://www.racefans.net/feed/"),
    ("The Race",     "https://www.the-race.com/formula-1/feed/"),
    # directory-verified fallbacks
    ("GrandPrix",    "https://www.grandprix.com/rss.xml"),
    ("F1technical",  "https://www.f1technical.net/rss/news.xml"),
    # plausible but unverified - watch the Action log
    ("Sky Sports",   "https://www.skysports.com/rss/12040"),
    ("PlanetF1",     "https://www.planetf1.com/feed"),
    # Motorsport Network pair: bot protection causes redirect loops for
    # non-browser clients; may return nothing from a GitHub runner.
    ("Autosport",    "https://www.autosport.com/rss/feed/f1"),
    ("Motorsport",   "https://www.motorsport.com/rss/f1/news"),
]
# --------------------------------------------------------------------------

NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "dc":   "http://purl.org/dc/elements/1.1/",
}


def fetch(url: str) -> bytes | None:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return r.read()
    except Exception as e:                      # noqa: BLE001
        print(f"  ! fetch failed: {e}", file=sys.stderr)
        return None


def parse_date(raw: str | None) -> datetime | None:
    if not raw:
        return None
    raw = raw.strip()
    # RFC 822 (RSS)
    try:
        d = parsedate_to_datetime(raw)
        if d.tzinfo is None:
            d = d.replace(tzinfo=timezone.utc)
        return d.astimezone(timezone.utc)
    except Exception:                            # noqa: BLE001
        pass
    # ISO 8601 (Atom)
    try:
        d = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if d.tzinfo is None:
            d = d.replace(tzinfo=timezone.utc)
        return d.astimezone(timezone.utc)
    except Exception:                            # noqa: BLE001
        return None


def clean_title(t: str) -> str:
    t = re.sub(r"<[^>]+>", "", t)                # strip any inline html
    t = (t.replace("&amp;", "&").replace("&#039;", "'").replace("&quot;", '"')
          .replace("&lt;", "<").replace("&gt;", ">").replace("&nbsp;", " "))
    return re.sub(r"\s+", " ", t).strip()


def norm_key(t: str) -> str:
    """Loose key so the same story from two outlets collapses to one."""
    t = t.lower()
    t = re.sub(r"[^a-z0-9 ]+", "", t)
    words = [w for w in t.split() if len(w) > 3]
    return " ".join(sorted(words)[:7])


def parse_feed(source: str, xml: bytes) -> list[dict]:
    out: list[dict] = []
    try:
        root = ET.fromstring(xml)
    except ET.ParseError as e:
        print(f"  ! xml parse failed: {e}", file=sys.stderr)
        return out

    # --- RSS 2.0 ---
    for item in root.iter("item"):
        title = item.findtext("title") or ""
        link = item.findtext("link") or ""
        date = (item.findtext("pubDate")
                or item.findtext("{http://purl.org/dc/elements/1.1/}date"))
        d = parse_date(date)
        if title and d:
            out.append({"title": clean_title(title), "url": link.strip(),
                        "source": source, "published": d})

    # --- Atom ---
    for entry in root.findall("atom:entry", NS):
        title = entry.findtext("atom:title", default="", namespaces=NS)
        link_el = entry.find("atom:link", NS)
        link = link_el.get("href", "") if link_el is not None else ""
        date = (entry.findtext("atom:published", namespaces=NS)
                or entry.findtext("atom:updated", namespaces=NS))
        d = parse_date(date)
        if title and d:
            out.append({"title": clean_title(title), "url": link.strip(),
                        "source": source, "published": d})
    return out


def main() -> None:
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=MAX_AGE_DAYS)

    collected: list[dict] = []
    for source, url in FEEDS:
        print(f"- {source}")
        xml = fetch(url)
        if not xml:
            continue
        items = parse_feed(source, xml)
        print(f"    {len(items)} items")
        collected.extend(items)

    # prune old, dedupe, sort
    fresh = [i for i in collected if i["published"] >= cutoff]
    print(f"\n{len(collected)} fetched -> {len(fresh)} within {MAX_AGE_DAYS} days")

    seen: set[str] = set()
    deduped: list[dict] = []
    for i in sorted(fresh, key=lambda x: x["published"], reverse=True):
        k = norm_key(i["title"])
        if not k or k in seen:
            continue
        seen.add(k)
        deduped.append(i)

    final = deduped[:MAX_ITEMS]
    print(f"{len(deduped)} after dedupe -> writing {len(final)}")

    payload = {
        "generated": now.isoformat(timespec="seconds"),
        "max_age_days": MAX_AGE_DAYS,
        "count": len(final),
        "items": [
            {
                "title": i["title"],
                "url": i["url"],
                "source": i["source"],
                "published": i["published"].isoformat(timespec="seconds"),
            }
            for i in final
        ],
    }

    if not final:
        # never overwrite a good file with an empty one
        print("No fresh items - leaving existing news.json untouched.", file=sys.stderr)
        sys.exit(0)

    with open("news.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)
    print("wrote news.json")


if __name__ == "__main__":
    main()
