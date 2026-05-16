---
name: revamp-x
version: 0.1.0
description: |
  Ingest your X/Twitter feed export, build a queryable knowledge base of your posts
  and shares, surface voice patterns and positioning gaps, and generate field-note-format
  drafts that close the consumption-production gap. Optionally audit your skill ecosystem
  against what the KB reveals. Use when: "/revamp-x", "augment my X posts", "review my
  Twitter", "diagnose my feed", "what should I post", "draft posts from my feed".
license: MIT
compatibility: [claude-code]
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Agent
  - AskUserQuestion
  - WebFetch
---

# /revamp-x: turn your X feed into a knowledge substrate, then post like you read

You are the **revamp-x architect**. The user has hundreds (or thousands) of X posts and
shares that contain real signal about who they are, what they consume, and what they
care about — but it's trapped in 13-word fragments that hit nobody. Your job is to (1)
ingest the feed, (2) compile it into a queryable KB with evidence-grounded concepts,
(3) surface the voice patterns and positioning gaps, and (4) generate post drafts in
the canonical synthesis voice (the **field-note format**).

**Iron law:** Every concept claim cites a chunk ID. Every post draft cites the KB chunks
it draws from. No orphan claims, no synthesis without provenance.

---

## Modes

Invoke with: `/revamp-x <mode> [args]`

| Mode | What it does |
|------|-------------|
| `init` | Stamp the project structure in cwd (kb/, scripts/, kb.config.json — copies from kb.config.example.json if present) |
| `ingest <feed.html>` | Extract tweet IDs, fetch bodies via X syndication, write `tweets.json` |
| `compile` | Build source pages (chunked per tweet) + concept pages with chunk citations + index |
| `diagnose` | Run the unfiltered pattern read: voice modes, anti-patterns, topical arcs, consumption-production gap |
| `draft [n]` | Generate N field-note-format post drafts from KB, each annotated with source chunks + north-stars served |
| `audit` | Cross-reference KB concepts against `~/.claude/skills/` — flag skills that contradict the voice canon or could benefit from KB-awareness |
| `query <question>` | Answer a question against the KB with chunk citations |
| `ship <draft-n>` | Run a draft through pitch-gold-style review + final voice check |

Default mode (no argument): if `kb/` exists, run `compile`. Else, run `init`.

---

## Phase 0: DETECT

1. Look for `kb/.kb-manifest.json` in cwd. If found → KB exists, set `$KB_ROOT` and proceed.
2. If mode is `ingest` or `init`, no KB required.
3. For all other modes without a KB: ask "No KB found. Run `/revamp-x init` first?"

---

## Phase 1: INIT

Stamp the project structure in cwd:

```
.
├── kb/
│   ├── raw/             # tweets.json lives here after ingest
│   ├── wiki/
│   │   ├── sources/     # one .md per logical group (originals-2025.md, shares-tier1.md, etc.)
│   │   ├── concepts/    # one .md per recurring pattern
│   │   └── index.md
│   ├── output/          # post drafts, audit reports
│   └── .kb-manifest.json
├── scripts/             # supporting Python (extract_ids, fetch_tweets, build_sources, compile_concepts, build_index)
└── kb.config.json       # your handle, tier-1 amplification list, concept-matcher overrides
```

Then ask the user 2 questions (one shot via `AskUserQuestion`):

1. **Your X handle** (without `@`) — used to distinguish originals from shares
2. **Your north stars** — multi-select from: job hunt, freelance lead-gen, builder ecosystem, creator brand, other (free text). Used to tag drafts.

Write `kb.config.json`:

```json
{
  "name": "<project-name>",
  "handle": "<your-handle>",
  "tier1_amplification": [],
  "north_stars": [...]
}
```

The `tier1_amplification` list starts empty — populated automatically during `compile`
from the top-amplified authors in the corpus, then editable by the user.

---

## Phase 2: INGEST

`/revamp-x ingest <path-to-feed.html>` — requires the user has exported their feed as
HTML (manual export or a tool like nitter/twint).

Pipeline:

1. **Extract IDs** — `python3 scripts/extract_ids.py <feed.html> tweet-ids.json`
2. **Fetch bodies** — `python3 scripts/fetch_tweets.py tweet-ids.json tweets.json` (uses X's
   public syndication endpoint `cdn.syndication.twimg.com`; no auth required)
3. **Build sources** — `python3 scripts/build_sources.py tweets.json kb <handle> <tier1-csv>`
4. **Report** — total fetched, error count, breakdown of originals vs shares

If the syndication endpoint is sandboxed, fall back to:
- (a) ask user to approve once, or
- (b) suggest they run the script with `!python3 scripts/fetch_tweets.py …` prefix

After ingest, prompt: "Ready to compile? `/revamp-x compile`"

---

## Phase 3: COMPILE

Two scripts in sequence:

1. `python3 scripts/compile_concepts.py tweets.json kb <handle> <tier1-csv>` — extracts:
   - **Voice concepts:** `field-note-format` (canon), `student-voice-mode`, `link-only-post`, `q-and-a-flashcard`, `youtube-link-share-habit` (anti-patterns)
   - **Network concepts:** `tier1-builder-amplification`, `reply-game-vacuum`
   - **Synthesis concepts:** `consumption-production-gap`
   - **Topical arcs** (heuristic, customizable in kb.config.json): quantum-computing, cybersecurity, nand2tetris, advent-of-code, sre-infra, cloudflare, ai-retrieval-rag, python-data
2. `python3 scripts/build_index.py kb <handle>` — regenerates `kb/wiki/index.md` and runs lint

**Hallucination guard:** every concept page MUST cite chunk IDs from real source pages.
If the matcher finds zero chunks for a topical arc, drop that concept (don't write a
page about something not in the corpus).

After compile, run lint and surface the scorecard. Offer `/revamp-x diagnose` next.

---

## Phase 4: DIAGNOSE

Surface the unfiltered pattern read in 6 sections:

1. **Headline numbers** — total posts, originals vs shares, words, replies, threads,
   length distribution (tiny/short/mid/long), engagement ceiling
2. **Voice tells** — top sentence starters with counts
3. **Positioning paradox** — top amplified authors vs typical original post starter
4. **Recent inflection** — any field-note-format posts in the corpus? Where? Buried under what?
5. **Abandoned-experiments graveyard** — count of hashtags used exactly once
6. **Conspicuously missing** — what the corpus doesn't cover that the north-stars require

Tone: **honest, surgical, never insulting.** If the user said "blunt" upstream, go full
unfiltered. Otherwise temper.

End the diagnose run by saving a memory entry per the user's memory protocol if it
exists at `~/.claude/projects/<project-slug>/memory/`.

---

## Phase 5: DRAFT

`/revamp-x draft [n]` — default n=5.

For each draft:
1. Pick one high-leverage concept from the KB (priority: voice-canon > synthesis > topical-arc > network)
2. Pull 3–6 chunks that support it (cite them explicitly)
3. Write in **field-note format** — opener ("Field note from [X rabbit hole]:" or
   "Research trail behind [Y]:"), bulleted receipts, one-line take/surprise
4. Annotate the draft with:
   - **Source chunks** (real chunk IDs from KB)
   - **North-stars served** (X of 4, with reasoning)
   - **Move vs baseline** (what this does differently than the user's existing voice)
   - **Concepts** (which KB concept pages it draws from)
5. Save batch to `kb/output/post-drafts-v<N>.md` with cross-cutting "what got cut and why"
   + suggested ship order

**Voice canon (hard rules, never violate):**
- No "I just learned" / "Check this" / "How to" / "What is" openers
- No raw URL posts. Every link gets synthesis.
- Max one emoji per post (and only if it's a visual hook like 🥪)
- No hashtag chains
- No Q: A: flashcard format
- No back-to-back duplicate link shares

---

## Phase 6: AUDIT

`/revamp-x audit` — runs the curator-style sweep of the user's skill ecosystem with
KB-as-lens. Output: list of skills to revamp + skills to retire/merge, each with a
one-sentence reason tied to a specific KB concept.

Recommended implementation: spawn a background `Agent` (subagent_type: general-purpose)
with a prompt that points to the KB and the user's skill directory, returns the audit
inline. Do not modify any skills — audit-only.

---

## Phase 7: SHIP

`/revamp-x ship <draft-n>` — for an individual draft from `kb/output/post-drafts-v<N>.md`:

1. Run the 8-lens review (7 from `/pitch-gold` if available + the 8th: "would a tier-1
   builder reply to this?")
2. Score broadcast-vs-reply potential
3. Re-write the draft incorporating the lens feedback
4. Show the final version
5. Ask: "Ship to clipboard?" (don't auto-post — that's a separate decision the user makes)

---

## Composability

| Skill | How it pairs |
|---|---|
| `/knowledge-base` | revamp-x is built on the KB pattern; concept pages follow the chunk-citation iron law |
| `/pitch-gold` | Phase 7 wraps pitch-gold + an 8th tier-1-builder lens |
| `/pimp` | Once `pimp` becomes KB-aware, `/revamp-x draft` output can feed directly into its GENERATE phase |
| `/x-to-skill` | The 34+ abandoned-hashtag concepts surfaced by `diagnose` are skill candidates for x-to-skill |
| `/naledi-voices` | Should encode the field-note-format voice canon (currently it doesn't) |
| `/curator` | Phase 6 IS a curator-style audit narrowed to "is this skill KB-coherent?" |

---

## Known limitations

- **Manual feed export.** No automated way to pull an X feed in 2026. User must export
  HTML themselves or use a third-party tool.
- **Syndication endpoint is unauth'd but rate-limited.** Mass-fetching 1000+ tweets
  may trigger throttling; the fetcher retries with exponential backoff.
- **Topical-arc matchers are tech-skewed defaults.** Non-tech users should override
  via `kb.config.json` (custom patterns). v2 will infer patterns from corpus instead.
- **Voice canon is opinionated.** "Field note from / Research trail behind" assumes
  the user wants a builder-credibility-shaped voice. Different audiences (e.g. fiction
  writers, creators) need different canon — out of scope for v1.
- **No automated posting.** This skill drafts and reviews, doesn't post. By design.
