#!/usr/bin/env python3
"""Search and download stock media from Unsplash (photos) and Pixabay (photos, videos).

Keys come from the environment, never the command line:
  UNSPLASH_ACCESS_KEY   Unsplash "Access Key" (https://unsplash.com/oauth/applications)
  PIXABAY_API_KEY       Pixabay API key (https://pixabay.com/api/docs/)

Examples:
  scripts/stock.py unsplash photo "city at night" -n 5 --orientation landscape
  scripts/stock.py pixabay photo "mountain sunrise" -n 3
  scripts/stock.py pixabay video "ocean waves" -n 2 --size large
  scripts/stock.py pixabay video "abstract particles" --search-only   # list results, no download

Files land in assets/stock/<source>/<type>/ (or --out) and every download is
recorded in credits.json next to it, with the author and source page for attribution.
"""
import argparse
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

UA = {"User-Agent": "video-studio/1.0"}


def get_json(url, headers=None):
    req = urllib.request.Request(url, headers={**UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def download(url, dest, headers=None):
    req = urllib.request.Request(url, headers={**UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=300) as r, open(dest, "wb") as f:
        while chunk := r.read(1 << 20):
            f.write(chunk)
    return dest


def slug(s, n=40):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:n] or "item"


def need(var):
    v = os.environ.get(var)
    if not v:
        sys.exit(f"error: {var} is not set. Add it in the cloud environment's settings, then start a new session.")
    return v


def unsplash_photos(a):
    key = need("UNSPLASH_ACCESS_KEY")
    auth = {"Authorization": f"Client-ID {key}", "Accept-Version": "v1"}
    q = {"query": a.query, "per_page": min(a.n, 30), "content_filter": "high"}
    if a.orientation:
        q["orientation"] = {"vertical": "portrait"}.get(a.orientation, a.orientation)
    if a.color:
        q["color"] = a.color
    data = get_json("https://api.unsplash.com/search/photos?" + urllib.parse.urlencode(q), auth)
    for p in data["results"][: a.n]:
        url = p["urls"]["raw"] + "&" + urllib.parse.urlencode({"w": a.width, "fm": "jpg", "q": 85})
        yield {
            "id": p["id"],
            "file": f"unsplash-{slug(p.get('alt_description') or a.query)}-{p['id']}.jpg",
            "url": url,
            "preview": p["urls"]["small"],
            "size": f"{p['width']}x{p['height']}",
            "author": p["user"]["name"],
            "author_url": p["user"]["links"]["html"] + "?utm_source=video-studio&utm_medium=referral",
            "page": p["links"]["html"],
            "license": "Unsplash License",
            "credit": f"Photo by {p['user']['name']} on Unsplash",
            # API guidelines: hit this endpoint whenever a photo is actually downloaded.
            "_track": (p["links"]["download_location"], auth),
        }


def pixabay(a, kind):
    key = need("PIXABAY_API_KEY")
    q = {"key": key, "q": a.query, "per_page": max(3, min(a.n, 200)), "safesearch": "true"}
    if a.orientation and kind == "photo":
        q["orientation"] = a.orientation if a.orientation != "landscape" else "horizontal"
    if a.color and kind == "photo":
        q["colors"] = a.color
    base = "https://pixabay.com/api/videos/?" if kind == "video" else "https://pixabay.com/api/?"
    data = get_json(base + urllib.parse.urlencode(q))
    for h in data["hits"][: a.n]:
        name = slug(h.get("tags", a.query))
        if kind == "video":
            order = {"large": ["large", "medium", "small", "tiny"], "medium": ["medium", "small", "large", "tiny"],
                     "small": ["small", "tiny", "medium"]}[a.size]
            v = next(h["videos"][s] for s in order if h["videos"].get(s, {}).get("url"))
            url, size, ext = v["url"], f"{v['width']}x{v['height']} {h['duration']}s", "mp4"
            preview = h["videos"]["tiny"].get("thumbnail", "")
        else:
            url = h.get("largeImageURL") or h["webformatURL"]
            size, ext = f"{h['imageWidth']}x{h['imageHeight']}", url.rsplit(".", 1)[-1].split("?")[0]
            preview = h["previewURL"]
        yield {
            "id": h["id"],
            "file": f"pixabay-{name}-{h['id']}.{ext}",
            "url": url,
            "preview": preview,
            "size": size,
            "author": h["user"],
            "author_url": f"https://pixabay.com/users/{h['user']}-{h['user_id']}/",
            "page": h["pageURL"],
            "license": "Pixabay Content License",
            "credit": f"{'Video' if kind == 'video' else 'Image'} by {h['user']} from Pixabay",
        }


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("source", choices=["unsplash", "pixabay"])
    p.add_argument("kind", choices=["photo", "video"])
    p.add_argument("query")
    p.add_argument("-n", type=int, default=5, help="how many results")
    p.add_argument("--orientation", choices=["landscape", "vertical", "squarish"])
    p.add_argument("--color", help="color filter, e.g. blue, black_and_white")
    p.add_argument("--width", type=int, default=2400, help="Unsplash download width in px")
    p.add_argument("--size", choices=["large", "medium", "small"], default="large", help="Pixabay video rendition")
    p.add_argument("--out", help="output directory")
    p.add_argument("--search-only", action="store_true", help="print results as JSON, download nothing")
    a = p.parse_args()

    if a.source == "unsplash" and a.kind == "video":
        p.error("Unsplash has photos only; use pixabay for video")
    items = unsplash_photos(a) if a.source == "unsplash" else pixabay(a, a.kind)

    out = Path(a.out or f"assets/stock/{a.source}/{a.kind}s")
    credits_path = out / "credits.json"
    credits = json.loads(credits_path.read_text()) if credits_path.exists() else {}
    results = []
    for it in items:
        track = it.pop("_track", None)
        if a.search_only:
            results.append(it)
            continue
        out.mkdir(parents=True, exist_ok=True)
        dest = out / it["file"]
        if not dest.exists():
            print(f"↓ {it['file']}  ({it['size']}, {it['author']})", file=sys.stderr)
            download(it["url"], dest)
            if track:
                get_json(*track)
        credits[it["file"]] = {k: it[k] for k in ("author", "author_url", "page", "license", "credit", "size")}
        results.append(str(dest))
    if not a.search_only and results:
        credits_path.write_text(json.dumps(credits, indent=2) + "\n")
    print(json.dumps(results, indent=2))
    if not results:
        print("no results", file=sys.stderr)


if __name__ == "__main__":
    main()
