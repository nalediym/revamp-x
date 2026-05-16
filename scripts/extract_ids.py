#!/usr/bin/env python3
"""Extract tweet IDs from a naledicodes-style feed HTML export.

Usage: extract_ids.py <feed.html> <out.json>
"""
import sys, re, json
from pathlib import Path

if len(sys.argv) != 3:
    sys.exit("usage: extract_ids.py <feed.html> <out.json>")

html = Path(sys.argv[1]).read_text()
m = re.search(r'(?:const|let|var)\s+\w+\s*=\s*(\[[\s\S]*?\]);', html)
if not m:
    sys.exit("no embedded TWEETS array found in HTML")

data = json.loads(m.group(1))
Path(sys.argv[2]).write_text(json.dumps(data))
print(f"wrote {len(data)} ids to {sys.argv[2]}")
