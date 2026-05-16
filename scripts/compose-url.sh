#!/bin/bash
# compose-url — print a pre-filled compose URL for a target platform.
# Pipe to `pbcopy` or `open` to use it directly.
#
# Examples:
#   compose-url x "Field note from the rabbit hole" | pbcopy
#   compose-url bluesky "Just shipped revamp-x" | xargs open
#   compose-url email me@example.com "Hello" "Body text"     # builds mailto:
#   compose-url linkedin "Took a build break"                 # warning: LinkedIn intent is flaky
#
# Per kb/output/extensions-and-hooks-press-send-2026-05-16.md:
# this is the "no-infrastructure" press-send path that solves ~80% of
# friction without browser-automation or maintenance.

set -euo pipefail

PLATFORM="${1:-}"

if [ -z "$PLATFORM" ]; then
  /bin/cat <<'USAGE'
usage: compose-url <platform> <args...>

platforms:
  x         <text>                  → https://x.com/intent/tweet?text=...
  bluesky   <text>                  → https://bsky.app/intent/compose?text=...
  threads   <text>                  → https://www.threads.net/intent/post?text=...
  mastodon  <text> [instance]       → https://<instance>/share?text=... (default mastodon.social)
  linkedin  <text>                  → https://www.linkedin.com/sharing/share-offsite/?text=... (flaky)
  email     <to> <subject> <body>   → mailto:<to>?subject=...&body=...
  sms       <number> <body>         → sms:<number>?body=...
  reddit    <subreddit> <title>     → https://www.reddit.com/r/<sub>/submit?title=...
USAGE
  exit 1
fi

urlencode() {
  /usr/bin/python3 -c "import sys, urllib.parse; print(urllib.parse.quote(sys.argv[1], safe=''))" "$1"
}

case "$PLATFORM" in
  x|twitter)
    TEXT="${2:-}"
    [ -z "$TEXT" ] && { echo "usage: compose-url x <text>" >&2; exit 2; }
    /bin/echo "https://x.com/intent/tweet?text=$(urlencode "$TEXT")"
    ;;
  bluesky|bsky)
    TEXT="${2:-}"
    [ -z "$TEXT" ] && { echo "usage: compose-url bluesky <text>" >&2; exit 2; }
    /bin/echo "https://bsky.app/intent/compose?text=$(urlencode "$TEXT")"
    ;;
  threads)
    TEXT="${2:-}"
    [ -z "$TEXT" ] && { echo "usage: compose-url threads <text>" >&2; exit 2; }
    /bin/echo "https://www.threads.net/intent/post?text=$(urlencode "$TEXT")"
    ;;
  mastodon)
    TEXT="${2:-}"
    INSTANCE="${3:-mastodon.social}"
    [ -z "$TEXT" ] && { echo "usage: compose-url mastodon <text> [instance]" >&2; exit 2; }
    /bin/echo "https://${INSTANCE}/share?text=$(urlencode "$TEXT")"
    ;;
  linkedin)
    TEXT="${2:-}"
    [ -z "$TEXT" ] && { echo "usage: compose-url linkedin <text>" >&2; exit 2; }
    /bin/echo "https://www.linkedin.com/sharing/share-offsite/?text=$(urlencode "$TEXT")"
    /bin/echo "# warning: LinkedIn's intent URL is unreliable as of 2026 — may need manual paste" >&2
    ;;
  email|mailto)
    TO="${2:-}"
    SUBJECT="${3:-}"
    BODY="${4:-}"
    [ -z "$TO" ] && { echo "usage: compose-url email <to> <subject> <body>" >&2; exit 2; }
    URL="mailto:$(urlencode "$TO")"
    [ -n "$SUBJECT" ] && URL="${URL}?subject=$(urlencode "$SUBJECT")"
    [ -n "$BODY" ] && [ -n "$SUBJECT" ] && URL="${URL}&body=$(urlencode "$BODY")"
    [ -n "$BODY" ] && [ -z "$SUBJECT" ] && URL="${URL}?body=$(urlencode "$BODY")"
    /bin/echo "$URL"
    ;;
  sms)
    TO="${2:-}"
    BODY="${3:-}"
    [ -z "$TO" ] && { echo "usage: compose-url sms <number> <body>" >&2; exit 2; }
    URL="sms:$TO"
    [ -n "$BODY" ] && URL="${URL}?body=$(urlencode "$BODY")"
    /bin/echo "$URL"
    ;;
  reddit)
    SUB="${2:-}"
    TITLE="${3:-}"
    [ -z "$SUB" ] && { echo "usage: compose-url reddit <subreddit> <title>" >&2; exit 2; }
    URL="https://www.reddit.com/r/${SUB}/submit"
    [ -n "$TITLE" ] && URL="${URL}?title=$(urlencode "$TITLE")"
    /bin/echo "$URL"
    ;;
  *)
    /bin/echo "unknown platform: $PLATFORM" >&2
    /bin/echo "run 'compose-url' (no args) for usage" >&2
    exit 2
    ;;
esac
