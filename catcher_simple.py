import os
import time
import json
import requests

BASE_URL = "https://schaledb.com"
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Connection": "keep-alive",
}

REGIONS = ["cn", "en", "jp", "kr", "th", "tw", "zh"]
LANG_DATA_TYPES = ["students", "items"]
GLOBAL_DATA_TYPES = ["crafting", "groups"]


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def make_session():
    s = requests.Session()
    s.headers.update(HEADERS)
    return s


def fetch(url, dest_path, session, retries=3):
    if os.path.isfile(dest_path) and os.path.getsize(dest_path) > 0:
        return "skipped"
    ensure_dir(os.path.dirname(dest_path))
    for attempt in range(retries):
        try:
            r = session.get(url, timeout=30)
            if r.status_code == 200:
                with open(dest_path, "wb") as f:
                    f.write(r.content)
                return "ok"
            time.sleep(2 * attempt)
        except Exception:
            time.sleep(2 * attempt)
    return "error"


def main():
    s = make_session()

    print("Downloading global data:")
    for dtype in GLOBAL_DATA_TYPES:
        url = f"{BASE_URL}/data/{dtype}.min.json"
        dest = os.path.join(DATA_DIR, f"{dtype}.min.json")
        status = fetch(url, dest, s)
        print(f"  [{status}] {dtype}.min.json")

    for region in REGIONS:
        print(f"\nDownloading region: {region}")
        region_dir = os.path.join(DATA_DIR, region)
        ensure_dir(region_dir)
        for dtype in LANG_DATA_TYPES:
            url = f"{BASE_URL}/data/{region}/{dtype}.min.json"
            dest = os.path.join(region_dir, f"{dtype}.min.json")
            status = fetch(url, dest, s)
            print(f"  [{status}] {region}/{dtype}.min.json")

    print("\nDone.")


if __name__ == "__main__":
    main()
