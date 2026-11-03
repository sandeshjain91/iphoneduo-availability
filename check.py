#!/usr/bin/env python3
"""Check Apple Hong Kong in-store pickup availability for one part number.

Standard library only. Rewrites status.json only when store statuses change.
Exits 0 on network/parse errors so the previous status.json is kept.
"""
import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

PART = os.environ.get("PART_NUMBER", "").strip()
LOCATION = os.environ.get("LOCATION", "").strip() or "Yau Tsim Mong"
STATUS_FILE = os.environ.get("STATUS_FILE", "status.json")
HKT = timezone(timedelta(hours=8))
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36")


def fetch(part, location):
    qs = urllib.parse.urlencode({"fae": "true", "pl": "true", "parts.0": part, "location": location})
    url = f"https://www.apple.com/hk/shop/fulfillment-messages?{qs}"
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-HK,en;q=0.9",
        "Referer": "https://www.apple.com/hk/shop/buy-iphone/iphone-duo",
    })
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def parse(data, part):
    stores = data["body"]["content"]["pickupMessage"]["stores"]
    result = {}
    for store in stores:
        name = store.get("storeName") or store.get("storeNumber") or "unknown"
        avail = (store.get("partsAvailability") or {}).get(part) or {}
        result[name] = avail.get("pickupDisplay") or "unknown"
    return dict(sorted(result.items()))


def load_old(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def main():
    if not PART:
        print("PART_NUMBER is not set; nothing to do.", file=sys.stderr)
        return 0
    try:
        stores = parse(fetch(PART, LOCATION), PART)
    except Exception as exc:  # network, HTTP, JSON or shape errors
        print(f"Check failed, keeping old {STATUS_FILE}: {exc!r}", file=sys.stderr)
        return 0
    if not stores:
        print("No stores in response; keeping old file.", file=sys.stderr)
        return 0

    old = load_old(STATUS_FILE)
    if old and old.get("part") == PART and old.get("stores") == stores:
        print("No change.")
        return 0

    new = {
        "part": PART,
        "stores": stores,
        "changed_at": datetime.now(HKT).strftime("%Y-%m-%d %H:%M:%S HKT"),
    }
    with open(STATUS_FILE, "w", encoding="utf-8") as f:
        json.dump(new, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print("Status changed:")
    for name, status in stores.items():
        print(f"  {name}: {status}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
