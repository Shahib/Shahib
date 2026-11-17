#!/usr/bin/env python3
"""Search Wikimedia Commons for photos and save them to your Downloads folder.

Usage:  python3 get_umrah_photos.py
Needs only Python 3 (no pip installs). Saves a credits.txt with author/licence.
"""
import html
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

API = "https://commons.wikimedia.org/w/api.php"
UA = "photo-fetch-script/1.0 (personal use)"

# (filename, search query). Commons search is keyword-based, so queries are short.
ITEMS = [
    ("14-bukit-marwah.jpg", "Marwah hill Mecca"),
    ("15-tahallul-cukur.jpg", "pilgrim head shaving barber Mecca"),
    ("16-tahallul-wanita.jpg", "cutting hair scissors close up"),
    ("17-solat-jenazah.jpg", "funeral prayer Masjid al-Haram"),
    ("18-barang-keperluan.jpg", "ihram clothes sandals umrah"),
    ("19-hotel-madinah.jpg", "Medina hotels near Prophet's Mosque"),
    ("20-raudhah.jpg", "Rawdah Prophet's Mosque green carpet"),
]


def out_dir():
    # ChromeOS: Downloads shared with Linux shows up here
    for p in ("/mnt/chromeos/MyFiles/Downloads", os.path.expanduser("~/Downloads")):
        if os.path.isdir(p):
            return p
    p = os.path.expanduser("~/Downloads")
    os.makedirs(p, exist_ok=True)
    return p


def get(url, binary=False):
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=60) as r:
                data = r.read()
            return data if binary else json.loads(data)
        except Exception as e:  # retry on 429 / network blips
            if attempt == 3:
                raise
            time.sleep(2 * (attempt + 1))


def search(query):
    params = {
        "action": "query", "format": "json", "generator": "search",
        "gsrsearch": query, "gsrnamespace": 6, "gsrlimit": 15,
        "prop": "imageinfo", "iiprop": "url|mime|size|extmetadata",
        "iiurlwidth": 1600,
    }
    data = get(API + "?" + urllib.parse.urlencode(params))
    pages = sorted(data.get("query", {}).get("pages", {}).values(),
                   key=lambda p: p.get("index", 0))
    good = []
    for p in pages:
        ii = (p.get("imageinfo") or [{}])[0]
        if ii.get("mime") == "image/jpeg" and ii.get("width", 0) >= 800:
            good.append((p["title"], ii))
    return good


def clean(s):
    return html.unescape(re.sub(r"<[^>]+>", "", s or "")).strip()


def main():
    dest = out_dir()
    print("Saving to:", dest)
    credits = []
    for fname, query in ITEMS:
        try:
            results = search(query)
        except Exception as e:
            print(f"[FAIL] {fname}: {e}")
            continue
        if not results:
            print(f"[NONE] {fname}: no JPEG results for '{query}'")
            continue
        title, ii = results[0]
        url = ii.get("thumburl") or ii["url"]
        with open(os.path.join(dest, fname), "wb") as f:
            f.write(get(url, binary=True))
        meta = ii.get("extmetadata", {})
        line = (f"{fname}\n  {title}\n  author: {clean(meta.get('Artist', {}).get('value'))}\n"
                f"  licence: {clean(meta.get('LicenseShortName', {}).get('value'))}\n"
                f"  page: {ii.get('descriptionurl')}\n"
                f"  other candidates: {'; '.join(t for t, _ in results[1:4])}\n")
        credits.append(line)
        print(f"[OK]   {fname}  <-  {title}")
    with open(os.path.join(dest, "umrah-photo-credits.txt"), "w") as f:
        f.write("\n".join(credits))
    print("Done. Check each photo; the search takes the top match, which may not fit.")


if __name__ == "__main__":
    sys.exit(main())
