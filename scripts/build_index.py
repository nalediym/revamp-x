#!/usr/bin/env python3
"""Build kb/wiki/index.md and run lint scorecard.

Usage: build_index.py <kb-dir> [your-handle]
"""
import sys, json, re
from pathlib import Path
from collections import defaultdict
from datetime import datetime

if len(sys.argv) < 2:
    sys.exit("usage: build_index.py <kb-dir> [your-handle]")

KB = Path(sys.argv[1])
HANDLE = sys.argv[2].lstrip("@") if len(sys.argv) > 2 else "you"
INDEX = KB / "wiki" / "index.md"
MANIFEST = json.loads((KB / ".kb-manifest.json").read_text())
SOURCES = sorted((KB / "wiki" / "sources").glob("*.md"))
CONCEPTS = sorted((KB / "wiki" / "concepts").glob("*.md"))

def parse_meta(p):
    text = p.read_text()
    meta = {}
    for line in text.split('\n'):
        m = re.match(r'>\s+\*\*([\w ]+):\*\*\s+(.+)', line)
        if m: meta[m.group(1).lower().replace(' ', '_')] = m.group(2).strip()
    title_m = re.search(r'^# (.+)', text, re.M)
    meta['title'] = title_m.group(1) if title_m else p.stem
    meta['words'] = len(text.split())
    meta['raw'] = text
    return meta

src_meta = {p.stem: parse_meta(p) for p in SOURCES}
con_meta = {p.stem: parse_meta(p) for p in CONCEPTS}

by_cat = defaultdict(list)
for name, m in con_meta.items():
    by_cat[m.get('category', 'uncategorized')].append((name, m))

total_words = sum(m['words'] for m in src_meta.values()) + sum(m['words'] for m in con_meta.values())
total_chunks = sum(s['chunks'] for s in MANIFEST['sources'])

idx = [f"""# Knowledge Base Index — @{HANDLE} feed

> Auto-maintained by `/revamp-x compile`. Do not edit manually.
> Last compiled: {datetime.now().strftime('%Y-%m-%d %H:%M')}
> Sources: {len(SOURCES)} | Concepts: {len(CONCEPTS)} | Chunks: {total_chunks} | Words: {total_words:,}

## Sources
"""]
for slug, m in sorted(src_meta.items()):
    src_entry = next((s for s in MANIFEST['sources'] if s['slug'] == slug), {})
    idx.append(f"- [{m['title']}](sources/{slug}.md) — {src_entry.get('chunks','?')} chunks · {m['words']:,} words")

idx.append("\n## Concepts\n")
cat_order = ['voice-canon', 'topical-arc', 'network', 'synthesis', 'anti-pattern']
for cat in cat_order + [c for c in by_cat if c not in cat_order]:
    if cat not in by_cat: continue
    idx.append(f"\n### {cat}")
    for name, m in sorted(by_cat[cat]):
        idx.append(f"- [{m['title']}](concepts/{name}.md) — `{m.get('confidence','?')}` · {m.get('matches_in_corpus','?')}")

idx.append("\n## Recent Queries\n<!-- auto-populated by query mode, max 20 entries -->\n")
INDEX.write_text('\n'.join(idx))
MANIFEST['last_compiled'] = datetime.now().isoformat()
(KB / ".kb-manifest.json").write_text(json.dumps(MANIFEST, indent=2))

print(f"Index: {INDEX}")
print(f"  {len(SOURCES)} sources · {len(CONCEPTS)} concepts · {total_chunks} chunks · {total_words:,} words")

# ─── LINT ───
issues = defaultdict(list)
all_pages = set(p.stem for p in SOURCES) | set(p.stem for p in CONCEPTS)
for p in list(SOURCES) + list(CONCEPTS):
    text = p.read_text()
    for m in re.finditer(r'\]\(\.\./(sources|concepts)/([\w-]+)\.md\)', text):
        if m.group(2) not in all_pages:
            issues['broken-links'].append(f"{p.name} → {m.group(2)}")
for name, m in con_meta.items():
    if m['words'] < 100: issues['thin-concepts'].append(f"{name} ({m['words']} words)")
    if 'c-' not in m['raw'] and m.get('category') != 'synthesis':
        issues['missing-provenance'].append(name)
for p in list(SOURCES) + list(CONCEPTS):
    n = p.read_text().count('<!-- human notes below -->')
    if n == 0: issues['missing-marker'].append(p.name)
    if n > 1: issues['dup-marker'].append(p.name)

print(f"\n=== LINT ===")
checks = [('Broken links','broken-links','FAIL'),('Missing provenance','missing-provenance','FAIL'),
          ('Thin concepts','thin-concepts','WARN'),('Marker missing','missing-marker','WARN'),
          ('Marker dup','dup-marker','FAIL')]
overall = 'HEALTHY'
print(f"| Check | Status | Count |\n|-------|--------|-------|")
for label, key, sev in checks:
    n = len(issues.get(key, []))
    st = 'PASS' if n == 0 else sev
    if st == 'FAIL': overall = 'NEEDS ATTENTION'
    print(f"| {label} | {st} | {n} |")
print(f"\nOverall: {overall}")
for key, items in issues.items():
    if items:
        print(f"\n[{key}]")
        for it in items[:5]: print(f"  - {it}")
        if len(items) > 5: print(f"  ... +{len(items)-5} more")
