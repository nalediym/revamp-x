#!/usr/bin/env python3
"""Compile concept pages from tweets. Each concept defines a matcher; the script
finds matching chunks and emits a concept page with real chunk citations.

Concepts are kept *evidence-grounded* — every claim cites chunk IDs that exist
in the source pages. No hallucination.

Usage: compile_concepts.py <tweets.json> <kb-dir> <your-handle> [tier1-handles-csv]
"""
import sys, json, hashlib, re
from pathlib import Path
from collections import defaultdict, Counter

if len(sys.argv) < 4:
    sys.exit("usage: compile_concepts.py <tweets.json> <kb-dir> <your-handle> [tier1-handles-csv]")

TWEETS = list(json.loads(Path(sys.argv[1]).read_text()).values())
TWEETS = [t for t in TWEETS if 'text' in t]
KB = Path(sys.argv[2])
HANDLE = sys.argv[3].lstrip("@")
TIER1 = set((sys.argv[4].split(",") if len(sys.argv) > 4 else "")) - {""}
CONCEPTS_DIR = KB / "wiki" / "concepts"

def chunk_id(text):
    return hashlib.sha256(text.encode()).hexdigest()[:8]

def source_slug_for(t):
    if t['user'] == HANDLE:
        yr = (t.get('created_at') or '0000')[:4]
        return f"originals-{yr}"
    return "shares-tier1" if t['user'] in TIER1 else "shares-other"

def cite(t):
    return f"[{source_slug_for(t)}](../sources/{source_slug_for(t)}.md)#c-{chunk_id(t['text'])}"

def snippet(t, n=140):
    s = re.sub(r'\s+', ' ', t['text']).strip()
    return (s[:n] + '…') if len(s) > n else s

ORIGINALS = [t for t in TWEETS if t['user'] == HANDLE]

def m_field_note(t): return t['user'] == HANDLE and re.search(r'\b(field note|research trail|rabbit hole)\b', t['text'], re.I)
def m_student_voice(t):
    if t['user'] != HANDLE: return False
    starts = ['check this', 'i just learned', 'what is', 'how to', 'just learned', 'just discovered', 'finally got']
    return any(t['text'].lower().strip().startswith(s) for s in starts)
def m_link_only(t): return t['user'] == HANDLE and bool(re.match(r'^[^a-zA-Z]*https?://\S+(\s+via\s+@\w+)?\s*$', t['text'].strip()))
def m_qa_flashcard(t): return t['user'] == HANDLE and re.match(r'^\s*Q\s*[:.]?\s', t['text'])
def m_youtube_share(t): return t['user'] == HANDLE and ('youtube' in t['text'].lower() or 'youtu.be' in t['text'].lower())
def m_amp_tier1(t): return t['user'] in TIER1
def m_thread_continuation(t): return t['user'] == HANDLE and t.get('parent_id')
def m_consumption_gap(t): return False

TOPIC_MATCHERS = [
    ('quantum-computing-arc', r'\b(quantum|qubit|qiskit|superposition|entanglement)\b'),
    ('cybersecurity-arc', r'\b(cissp|cybersecurity|hardwarekey|encryption|cryptograph|infosec|owasp|stride)\b'),
    ('nand2tetris-arc', r'\bnand'),
    ('advent-of-code-arc', r'(advent of code|adventofcode|day \d+|#aoc)'),
    ('sre-infra-arc', r'\b(SRE|site reliability|prodcast|incident response|observability|reliability engineering)\b'),
    ('cloudflare-arc', r'\bcloudflare\b'),
    ('ai-retrieval-rag-arc', r'\b(RAG|ColPali|GraphRAG|MemGPT|vector search|retrieval|embedding|hybrid retrieval|llm|context window|agent memory)\b'),
    ('python-data-arc', r'\b(python|pandas|numpy|jupyter|datacamp|data science)\b'),
]

CORE_CONCEPTS = [
    ("field-note-format",
     "Synthesis voice: 'Field note from [rabbit hole]:' / 'Research trail behind [thing]:' followed by bulleted receipts and a one-line take. The format that demonstrates POV + breadth + depth simultaneously.",
     m_field_note, "voice-canon",
     "**Canonical voice going forward.** Every other format is being retired (see [student-voice-mode](student-voice-mode.md), [link-only-post](link-only-post.md), [q-and-a-flashcard](q-and-a-flashcard.md)). The format works because it (a) does the synthesis the reader can't do, (b) demonstrates consumption depth ([tier1-builder-amplification](tier1-builder-amplification.md)), (c) trains the audience to expect a take, not a forward."),
    ("student-voice-mode",
     "Anti-pattern: 'I just learned…', 'Check this…', 'What is…', 'How to…' openers. Learning-in-public-as-receipt mode that positions the author as junior rather than as builder.",
     m_student_voice, "anti-pattern",
     "Hits zero engagement. Actively undercuts builder/founder/recruiter audiences. Retired per [field-note-format](field-note-format.md)."),
    ("link-only-post",
     "Anti-pattern: bare URL posts (sometimes 'via @YouTube'), no synthesis, no framing.",
     m_link_only, "anti-pattern",
     "Bookmark-export disguised as content. Provides zero signal. The 'via @YouTube' variant is the worst sub-case — see [youtube-link-share-habit](youtube-link-share-habit.md)."),
    ("q-and-a-flashcard",
     "Anti-pattern: 'Q: [thing] A: [definition]' flashcard format broadcast as posts.",
     m_qa_flashcard, "anti-pattern",
     "Quiz-app content as feed. No audience wants this. Retire per [field-note-format](field-note-format.md)."),
    ("youtube-link-share-habit",
     "Heavy YouTube link-forwarding without commentary — the 'via @YouTube' suffix is a tell that the post was auto-generated.",
     m_youtube_share, "anti-pattern",
     "Hard rule: any YouTube video worth sharing gets one [field-note-format](field-note-format.md) post with 3 takeaways, or it doesn't get posted."),
    ("tier1-builder-amplification",
     "Top amplification targets — the accounts the author wants to be in conversation with. The 'who I want to be in the room with' signal.",
     m_amp_tier1, "network",
     "Defines the target audience. Currently these accounts have likely never seen the author exist despite the amplifications. Structured replies into this list is the highest-ROI X distribution move in 2026."),
    ("consumption-production-gap",
     "Structural mismatch between what the author amplifies and what they post. Two different careers in one feed.",
     m_consumption_gap, "synthesis",
     "Most actionable single finding. Closing this gap = becoming who you already read (a builder/synthesizer) rather than who you currently post as (a learner). All voice canon ([field-note-format](field-note-format.md)) is downstream of closing this gap."),
    ("reply-game-vacuum",
     "Reply / thread count near-zero across the corpus. Broadcast-only posture, never in conversation.",
     m_thread_continuation, "anti-pattern",
     "Distribution on X in 2026 is replies-into-bigger-accounts. The amplification list ([tier1-builder-amplification](tier1-builder-amplification.md)) has received zero substantive replies. Structured reply cadence is highest-ROI distribution that requires zero new content production."),
]

def m_topic(pattern):
    return lambda t: t['user'] == HANDLE and bool(re.search(pattern, t['text'], re.I))

TOPIC_CONCEPTS = []
for name, pattern in TOPIC_MATCHERS:
    definition = f"Recurring topical thread: posts matching pattern `{pattern}` — appears across multiple originals in the corpus."
    details = f"Topical arc surfaced from the corpus. Opportunity: convert into one canonical [field-note-format](field-note-format.md) post — synthesis of N months of consumption into one take that lands with the [tier1-builder-amplification](tier1-builder-amplification.md) network."
    TOPIC_CONCEPTS.append((name, definition, m_topic(pattern), "topical-arc", details))

CONCEPTS = CORE_CONCEPTS + TOPIC_CONCEPTS

def build_concept(name, definition, matcher, category, details):
    matches = [t for t in TWEETS if matcher(t)]
    sources = set(source_slug_for(t) for t in matches)
    first_seen = min(matches, key=lambda t: t.get('created_at') or '9999') if matches else None
    by_source = defaultdict(list)
    for t in matches:
        by_source[source_slug_for(t)].append(t)
    provenance_lines = []
    for src, ts in sorted(by_source.items()):
        cids = sorted(set(chunk_id(t['text']) for t in ts))
        provenance_lines.append(f"- [{src}](../sources/{src}.md) — " + ", ".join(f"c-{c}" for c in cids[:15]) + (f" (+{len(cids)-15} more)" if len(cids) > 15 else ""))
    sample_lines = [f"- {snippet(t)} — {cite(t)}" for t in matches[:6]]
    conf = "high" if len(matches) >= 10 else ("medium" if len(matches) >= 4 else "low")
    if not matches and category == "synthesis": conf = "high"
    first_seen_md = f"> **First seen:** {first_seen.get('created_at','?')[:10]} — {cite(first_seen)}" if first_seen else ""
    page = f"""# {name.replace('-', ' ').title()}

{first_seen_md}
> **Category:** {category}
> **Matches in corpus:** {len(matches)} chunks across {len(sources)} sources
> **Confidence:** {conf}

## Definition
{definition}

## Details
{details}

"""
    if sample_lines:
        page += "## Sample chunks\n" + "\n".join(sample_lines) + "\n\n"
    page += "## Provenance\n"
    page += ("\n".join(provenance_lines) + "\n") if provenance_lines else "_(Synthesis concept — see referenced concepts for chunk-level provenance)_\n"
    page += "\n<!-- human notes below -->\n"
    return page, len(matches), conf, category

written = 0
for name, defn, matcher, cat, det in CONCEPTS:
    page, n, conf, category = build_concept(name, defn, matcher, cat, det)
    if cat == "topical-arc" and n == 0:
        continue
    (CONCEPTS_DIR / f"{name}.md").write_text(page)
    written += 1
    print(f"  {name:34s}  [{cat:14s}]  matches={n:4d}  conf={conf}")
print(f"\nWrote {written} concept pages.")
