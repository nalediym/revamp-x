#!/usr/bin/env python3
"""Fetch tweet bodies via X syndication endpoint.

Usage: fetch_tweets.py <ids.json> <out.json>
Idempotent — resumes from existing out.json if present.
"""
import sys, json, math, time, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

if len(sys.argv) != 3:
    sys.exit("usage: fetch_tweets.py <ids.json> <out.json>")

IDS_PATH = Path(sys.argv[1])
OUT = Path(sys.argv[2])
IDS = json.loads(IDS_PATH.read_text())
DONE = json.loads(OUT.read_text()) if OUT.exists() else {}

def tok(tid):
    n = (int(tid) / 1e15) * math.pi
    s = ""
    while n > 0:
        s = "0123456789abcdefghijklmnopqrstuvwxyz"[int(n % 36)] + s
        n = int(n / 36)
    return s.replace("0", "") or "0"

def fetch(tid):
    url = f"https://cdn.syndication.twimg.com/tweet-result?id={tid}&token={tok(tid)}&lang=en"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                d = json.loads(r.read())
            return tid, {
                "id": tid,
                "text": d.get("text", ""),
                "user": d.get("user", {}).get("screen_name"),
                "name": d.get("user", {}).get("name"),
                "created_at": d.get("created_at"),
                "lang": d.get("lang"),
                "favorite_count": d.get("favorite_count"),
                "conversation_count": d.get("conversation_count"),
                "in_reply_to_screen_name": d.get("in_reply_to_screen_name"),
                "in_reply_to_status_id_str": d.get("in_reply_to_status_id_str"),
                "parent_id": (d.get("parent") or {}).get("id_str"),
                "parent_user": ((d.get("parent") or {}).get("user") or {}).get("screen_name"),
                "parent_text": (d.get("parent") or {}).get("text"),
                "has_media": bool((d.get("mediaDetails") or d.get("photos") or d.get("video"))),
            }
        except urllib.error.HTTPError as e:
            if e.code == 404: return tid, {"id": tid, "error": "404"}
            if e.code == 429: time.sleep(2 ** attempt + 1)
            else: return tid, {"id": tid, "error": f"HTTP {e.code}"}
        except Exception as e:
            time.sleep(0.5 * (attempt + 1))
            if attempt == 2: return tid, {"id": tid, "error": str(e)[:120]}
    return tid, {"id": tid, "error": "max retries"}

todo = [t["id"] for t in IDS if t["id"] not in DONE]
print(f"Total: {len(IDS)} | Already done: {len(DONE)} | To fetch: {len(todo)}")

last_save = time.time()
with ThreadPoolExecutor(max_workers=6) as ex:
    futs = {ex.submit(fetch, tid): tid for tid in todo}
    for i, fut in enumerate(as_completed(futs), 1):
        tid, payload = fut.result()
        DONE[tid] = payload
        if i % 25 == 0 or time.time() - last_save > 5:
            OUT.write_text(json.dumps(DONE))
            last_save = time.time()
            ok = sum(1 for v in DONE.values() if "text" in v)
            err = len(DONE) - ok
            print(f"  [{i}/{len(todo)}]  ok={ok} err={err}")

OUT.write_text(json.dumps(DONE))
ok = sum(1 for v in DONE.values() if "text" in v)
err = [v for v in DONE.values() if "error" in v]
print(f"\nDone. Fetched: {ok}/{len(IDS)}  Errors: {len(err)}")
