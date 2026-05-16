# revamp-x

> Turn your X feed into a knowledge substrate, then post like you read.

A Claude Code skill that ingests your X/Twitter feed, compiles it into a queryable
knowledge base of your posts and shares, surfaces the voice patterns and positioning
gaps in your timeline, and generates field-note-format drafts that close the gap
between **what you consume** and **what you post**.

```
feed.html  →  559 tweets fetched  →  KB w/ chunked citations  →  pattern read  →  drafts
                                                                                    ↓
                                                                              ship-ready
```

---

## The premise (autobiographical)

I built revamp-x because of my own feed. **413 original posts in 9 years.
14 total likes across all of them.** My top-engaged post was a Matt Pocock video forward.

But when I audited my *shares* — what I quietly boost — the picture was different:
founder/infra/AI-builder accounts on rotation, technical takes I'd silently file away,
hardware history I returned to. The diet I was *consuming* and the diet I was *posting*
were from two different careers.

revamp-x is the substrate that makes that gap visible — and the toolchain that helps
close it. If you have a similar pattern (you're not the only one), it may work for you
too. The defaults are tech-skewed because I'm tech-skewed; the matchers in
`kb.config.json` are overridable.

---

## What it does

`/revamp-x` runs against your local feed export and produces:

1. **A KB** with one source page per logical group (originals-by-year, shares-tier1,
   shares-other) and one concept page per recurring pattern (voice modes, anti-patterns,
   topical arcs, network effects).
2. **An evidence-grounded diagnosis** — every concept cites the actual chunk IDs that
   support it. No orphan claims.
3. **Post drafts in the field-note format** — the only voice in your corpus that
   demonstrates POV + breadth + depth simultaneously. Each draft annotated with: source
   chunks, north-stars served, move vs your baseline voice.
4. **A skill-ecosystem audit** (optional) — cross-references your `~/.claude/skills/`
   against KB concepts. Surfaces which skills contradict the voice canon or would
   benefit from KB-awareness.

---

## Install

```bash
git clone https://github.com/<you>/revamp-x ~/Projects/revamp-x
cd ~/Projects/revamp-x
cp kb.config.example.json kb.config.json     # then edit kb.config.json with your handle + north-stars
ln -s ~/Projects/revamp-x ~/.claude/skills/revamp-x
```

That's it. The skill is now available as `/revamp-x` in any Claude Code session.

> `kb.config.json` is gitignored — it's your personal config. The repo ships `kb.config.example.json` as a template.

Requires: Python 3.10+, internet access for the X syndication endpoint, an X feed
export as HTML.

---

## Usage

```bash
# In any Claude Code session in a fresh directory:
/revamp-x init                          # asks for your handle + north-stars
/revamp-x ingest path/to/feed.html      # fetches all tweet bodies (~3 min for 1000 tweets)
/revamp-x compile                       # builds KB sources + concepts + index
/revamp-x diagnose                      # the unfiltered pattern read
/revamp-x draft 5                       # generates 5 field-note drafts
/revamp-x audit                         # optional: cross-references against your skills
/revamp-x ship draft-1                  # 8-lens review + clipboard
```

---

## The field-note format

The canonical voice the skill drafts in:

```
Field note from [the X rabbit hole]:

[One sentence that reframes what most people think about X.]

• [Receipt 1] — concrete
• [Receipt 2] — concrete
• [Receipt 3] — concrete
• [Receipt 4] — concrete
• [Receipt 5] — concrete

[What surprised you. The thing the reader couldn't have synthesized themselves.]
```

It works because (a) it does the synthesis the reader can't do themselves, (b) it
demonstrates the depth of your consumption diet, (c) it trains your audience to expect
a take, not a forward.

Anti-patterns the skill refuses to draft in:

- "Check this…" / "I just learned…" / "How to…" / "What is…" (student-voice-mode)
- Raw URL posts (link-only-post)
- "Q: [thing] A: [definition]" (q-and-a-flashcard)
- "via @YouTube" link forwards (youtube-link-share-habit)
- Hashtag chains (#WebDev #DevTools #DevBadges)
- More than one emoji per post

---

## How it's built

| Phase | What happens | Files |
|---|---|---|
| Extract | Pull tweet IDs from feed HTML | `scripts/extract_ids.py` |
| Fetch | Resolve bodies via X syndication endpoint | `scripts/fetch_tweets.py` |
| Build sources | One source page per logical group, each tweet a chunk with content-addressed ID | `scripts/build_sources.py` |
| Compile concepts | Pattern-match against text for voice modes, anti-patterns, topical arcs | `scripts/compile_concepts.py` |
| Build index + lint | Regenerate `kb/wiki/index.md`, run health scorecard | `scripts/build_index.py` |
| Diagnose | LLM-generated honest pattern read (handled by Claude in-session) | inline |
| Draft | LLM-generated field-note posts citing chunks (handled by Claude in-session) | inline |
| Audit | Curator-style sweep of `~/.claude/skills/` against KB concepts (spawns subagent) | inline |

All scripts are dependency-free Python (stdlib only). The KB pattern is borrowed from
[Andrej Karpathy's LLM knowledge base](https://twitter.com/karpathy/status/...) and
implemented over [/knowledge-base](https://github.com/<you>/knowledge-base) skill
conventions.

---

## Why I built this

I had **413 original X posts. 14 total likes across all time.** My top engaged post
was a Matt Pocock video forward.

But I was amplifying @garrytan, @charles_irl, @CloudflareDev, @sama, @boristane,
@googlesre, @hasantoxr. The diet I consumed was builder/infra/AI-frontier. The diet
I posted was DataCamp-tutorial-extract. Two careers, one feed.

The fix wasn't "post more." It was: **make the synthesis the consumption already implied
visible.** That's what revamp-x does, and it works because the substrate (every tweet
chunk-cited and queryable) makes synthesis cheap and provenance free.

The bet: in 2026 the X accounts that grow are the ones doing synthesis at depth, not
volume. The skill makes that cheap.

---

## License

MIT.

---

## Status

v0.1 — built 2026-05-16. Single-user-tested (mine). The opinionated parts (voice
canon, topical-arc matchers) are tech-skewed; non-tech users will need to override
via `kb.config.json`.
