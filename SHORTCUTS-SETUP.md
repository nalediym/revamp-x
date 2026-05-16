# macOS Shortcuts setup — press-send MVP

> Per kb/output/extensions-and-hooks-press-send-2026-05-16.md:
> the "no-infrastructure" press-send path that solves ~80% of friction
> without browser-automation or maintenance.
>
> **Total setup: ~10 minutes.** Then global hotkeys turn selected text
> into a pre-filled compose window in any platform.

---

## What this gives you

A keyboard shortcut (e.g. ⌃⌘T for X, ⌃⌘B for Bluesky, ⌃⌘E for email) that:

1. Grabs the currently-selected text (or clipboard contents)
2. Builds the appropriate platform compose URL
3. Opens it in your default browser → the native compose window appears pre-filled
4. You hit Send manually

This is the **gate-at-human-eye** pattern. The send button is in the actual platform, so there's no "biometric prompt → muscle-memory tap" failure mode.

---

## Prerequisites

- The `compose-url` script ships at `~/Projects/revamp-x/scripts/compose-url.sh` (already executable)
- macOS Shortcuts.app (built-in, every macOS)

---

## Build the X shortcut (template; the others are identical with one URL change)

1. **Open Shortcuts.app**
2. **File → New Shortcut**
3. Name it: `Post to X` (or whatever you'll remember)
4. Add these actions in order:

   | # | Action | Settings |
   |---|---|---|
   | 1 | **Get Clipboard** (or `Get Selected Text` if you prefer selection-based) | — |
   | 2 | **Run Shell Script** | Shell: `/bin/bash` · Pass input: `as arguments` · Script: `/Users/naledi/Projects/revamp-x/scripts/compose-url.sh x "$1"` |
   | 3 | **Open URLs** | Input: `Shell Script Result` |

5. **Click the Shortcut info ⓘ icon → Keyboard Shortcut → set to ⌃⌘T** (or whatever you want)
6. Make sure **"Use as Quick Action"** and **"Pin in Menu Bar"** are checked if you want menu access too

**Test:** Copy "Field note from the rabbit hole 🥪" to clipboard → hit ⌃⌘T → X compose window opens pre-filled.

---

## Build the other 5 shortcuts (each is 2 min — same recipe, different platform arg)

| Shortcut name | Hotkey suggestion | Script line |
|---|---|---|
| Post to X | ⌃⌘T | `compose-url.sh x "$1"` |
| Post to Bluesky | ⌃⌘B | `compose-url.sh bluesky "$1"` |
| Post to Threads | ⌃⌘H | `compose-url.sh threads "$1"` |
| Post to Mastodon | ⌃⌘M | `compose-url.sh mastodon "$1"` |
| Email (to me) | ⌃⌘E | `compose-url.sh email "you@example.com" "" "$1"` |
| SMS | ⌃⌘S | `compose-url.sh sms "555-XXX-XXXX" "$1"` |

(Skip LinkedIn — see "Known broken" below.)

---

## Workflow with revamp-x drafts

When you have a ship-ready draft at `kb/output/ship-ready/draft-XX.md`:

```bash
# Single-tweet draft — copy + hotkey
cat kb/output/ship-ready/draft-XX.md | grep -A1 'Tweet 1/' | tail -1 | pbcopy
# then hit ⌃⌘T
```

For a thread (one tweet at a time):
1. Grab tweet N from the file → `pbcopy`
2. ⌃⌘T → compose opens → Post
3. Reply to your own post manually for tweet N+1
4. Repeat

Yes this is manual. That's the point — every send goes through your eye-on-the-actual-platform.

---

## Known broken

- **LinkedIn intent URL is unreliable as of 2026.** LinkedIn aggressively rate-limits + deprecates intent URLs. The `compose-url linkedin ...` form will print a warning. For LinkedIn, copy-paste into the manual compose at https://www.linkedin.com/feed/?shareActive=true.
- **Reddit's intent URL** requires you to know the subreddit. Useful for cross-posting to specific communities.

---

## Why this is the right MVP (per the research)

From `kb/output/extensions-and-hooks-press-send-2026-05-16.md`:

> "macOS Shortcuts + compose URLs gives ~same EV at zero maintenance, zero drift, zero CVE surface. The human eyeball *is* what's catching fabrications today; programmatic gating is theater."
>
> — critic subagent

The Shortcuts path:
- ✅ Zero servers, zero MCP, zero Playwright, zero biometric prompts
- ✅ Solves the actual friction (typing/copy-paste latency between draft and compose)
- ✅ Survives any platform DOM change (it's URL-based)
- ✅ No `<all_urls>` extension surface (the March 2026 Claude extension XSS pattern)
- ❌ Doesn't post for you — you still click Send

The "doesn't post for you" is the feature, not the bug.

---

## If you want fewer hotkeys

You can build ONE shortcut called `Post to…` that uses **Choose from List** to pick the platform before running the script. Slower per-use but uses one hotkey + zero memorization. Same recipe, swap step 1 from `Get Clipboard` to: Get Clipboard → Choose from Menu (X, Bluesky, Threads, etc.) → Run Shell Script with the chosen platform.
