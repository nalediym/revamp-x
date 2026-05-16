#!/usr/bin/env python3
"""Generate KB source pages from tweets.json.

Usage: build_sources.py <tweets.json> <kb-dir> <your-handle> [tier1-handles-csv]
"""
import sys, json, hashlib, re
from pathlib import Path
from collections import defaultdict, Counter

if len(sys.argv) < 4:
    sys.exit("usage: build_sources.py <tweets.json> <kb-dir> <your-handle> [tier1-handles-csv]")

TWEETS_PATH = Path(sys.argv[1])
KB = Path(sys.argv[2])
HANDLE = sys.argv[3].lstrip("@")
TIER1 = set((sys.argv[4].split(",") if len(sys.argv) > 4 else "")) - {""}

TWEETS = json.loads(TWEETS_PATH.read_text())
SOURCES_DIR = KB / "wiki" / "sources"
RAW_DIR = KB / "raw"
MANIFEST_PATH = KB / ".kb-manifest.json"

RAW_TWEETS = RAW_DIR / "tweets.json"
RAW_TWEETS.write_text(TWEETS_PATH.read_text())
RAW_HASH = hashlib.sha256(RAW_TWEETS.read_bytes()).hexdigest()

def chunk_id(text):
    return hashlib.sha256(text.encode()).hexdigest()[:8]

def fmt_chunk(t):
    cid = chunk_id(t['text'])
    date = (t.get('created_at') or '')[:10]
    likes = t.get('favorite_count') or 0
    repls = t.get('conversation_count') or 0
    media = "📎" if t.get('has_media') else ""
    reply_to = f" → @{t['in_reply_to_screen_name']}" if t.get('in_reply_to_screen_name') else ""
    head = f"### c-{cid}: [{date}] @{t['user']}{reply_to} ♥{likes} 💬{repls} {media}".rstrip()
    body = "> " + t['text'].replace('\n', '\n> ')
    return head + "\n" + body + "\n"

def build_source_page(title, summary, tweets, source_tag):
    likes_total = sum((t.get('favorite_count') or 0) for t in tweets)
    words_total = sum(len(t['text'].split()) for t in tweets)
    chunks_md = "\n".join(fmt_chunk(t) for t in tweets)
    return f"""# {title}

> **Source:** [tweets.json](../../raw/tweets.json) (filtered slice — `{source_tag}`)
> **Hash:** {RAW_HASH}
> **Status:** fresh
> **Chunks:** {len(tweets)}
> **Total likes:** {likes_total} | **Total words:** {words_total:,}

## Summary
{summary}

## Chunks
{chunks_md}

<!-- human notes below -->
"""

by_year = defaultdict(list)
shares_tier1 = []
shares_other = []
for t in TWEETS.values():
    if 'text' not in t: continue
    if t['user'] == HANDLE:
        yr = (t.get('created_at') or '0000')[:4]
        by_year[yr].append(t)
    else:
        (shares_tier1 if t['user'] in TIER1 else shares_other).append(t)

manifest = {"version": 1, "sources": []}

for yr, tweets in sorted(by_year.items()):
    if not tweets: continue
    slug = f"originals-{yr}"
    tweets_sorted = sorted(tweets, key=lambda x: x.get('created_at') or '')
    page = build_source_page(f"Originals — {yr}",
                             f"All {len(tweets)} originals from @{HANDLE} in {yr}.",
                             tweets_sorted, slug)
    (SOURCES_DIR / f"{slug}.md").write_text(page)
    manifest['sources'].append({"slug": slug, "chunks": len(tweets), "tweet_type": "original", "year": yr})

if shares_tier1:
    tier1_sorted = sorted(shares_tier1, key=lambda x: ((x.get('user') or ''), (x.get('created_at') or '')))
    auth_breakdown = Counter(t['user'] for t in shares_tier1)
    summary = f"{len(shares_tier1)} amplified posts from tier-1 accounts. Top: " + ", ".join(f"@{a}({c})" for a,c in auth_breakdown.most_common(10))
    (SOURCES_DIR / "shares-tier1.md").write_text(
        build_source_page("Shares — Tier 1", summary, tier1_sorted, "shares-tier1"))
    manifest['sources'].append({"slug": "shares-tier1", "chunks": len(shares_tier1), "tweet_type": "share", "tier": 1})

if shares_other:
    other_sorted = sorted(shares_other, key=lambda x: ((x.get('user') or ''), (x.get('created_at') or '')))
    summary = f"{len(shares_other)} amplified posts from ~{len(set(t['user'] for t in shares_other))} other accounts (long tail)."
    (SOURCES_DIR / "shares-other.md").write_text(
        build_source_page("Shares — Long tail", summary, other_sorted, "shares-other"))
    manifest['sources'].append({"slug": "shares-other", "chunks": len(shares_other), "tweet_type": "share", "tier": 2})

MANIFEST_PATH.write_text(json.dumps(manifest, indent=2))
print(f"Sources: {len(manifest['sources'])}  |  Chunks: {sum(s['chunks'] for s in manifest['sources'])}")
for s in manifest['sources']:
    print(f"  {s['slug']}: {s['chunks']}")
