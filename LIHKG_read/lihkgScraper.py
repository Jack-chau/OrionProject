"""
LIHKG Data Scraper
------------------
Collects thread titles and comments from LIHKG public category pages,
for use as training data (e.g. a text-classification / detection model).

Usage:
    python lihkg_scraper.py --cat_id 1 --pages 5 --out lihkg_data.csv

Notes:
- Uses LIHKG's public (unofficial) JSON API, no login required for
  public categories.
- Includes a delay between requests to avoid overloading the server.
- Run responsibly: LIHKG is a public forum, but please don't hammer
  it with a high request rate, and consider anonymizing usernames
  before sharing/publishing the resulting dataset.
"""

import argparse
import csv
import time

import requests

BASE_URL = "https://lihkg.com/api_v2"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    ),
    "Accept": "application/json",
}


def get_category_threads(cat_id, page=1, count=60):
    """Fetch one page of thread listings from a category."""
    url = f"{BASE_URL}/thread/category"
    params = {"cat_id": cat_id, "page": page, "count": count, "type": "now"}
    resp = requests.get(url, headers=HEADERS, params=params, timeout=15)
    resp.raise_for_status()
    return resp.json()


def get_thread_page(thread_id, page=1):
    """Fetch one page of comments for a given thread."""
    url = f"{BASE_URL}/thread/{thread_id}/page/{page}"
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    return resp.json()


def scrape_category_threads(cat_id, max_pages, delay=1.5):
    """Collect thread metadata (id, title, etc.) across several pages."""
    threads = []
    for page in range(1, max_pages + 1):
        data = get_category_threads(cat_id, page)
        if not data.get("success"):
            print(f"  [warn] page {page}: request not successful, stopping.")
            break
        items = data.get("response", {}).get("items", [])
        if not items:
            break
        threads.extend(items)
        print(f"  fetched category page {page}, {len(items)} threads")
        time.sleep(delay)
    return threads


def scrape_thread_comments(thread_id, max_pages=None, delay=1.5):
    """Collect all comments for a single thread, following pagination."""
    comments = []
    page = 1
    while True:
        data = get_thread_page(thread_id, page)
        if not data.get("success"):
            break
        resp = data.get("response", {})
        items = resp.get("item_data", [])
        if not items:
            break
        comments.extend(items)

        total_page = resp.get("total_page", page)
        if page >= total_page or (max_pages and page >= max_pages):
            break
        page += 1
        time.sleep(delay)
    return comments


def save_to_csv(rows, filename, fieldnames):
    with open(filename, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description="Scrape LIHKG threads and comments.")
    parser.add_argument("--cat_id", type=int, default=1, help="Category ID to scrape")
    parser.add_argument("--pages", type=int, default=5, help="Number of category listing pages to fetch")
    parser.add_argument("--max_comment_pages", type=int, default=None, help="Cap comment pages per thread (default: all)")
    parser.add_argument("--delay", type=float, default=1.5, help="Delay in seconds between requests")
    parser.add_argument("--out", default="lihkg_data.csv", help="Output CSV filename")
    args = parser.parse_args()

    print(f"Fetching thread list from category {args.cat_id}...")
    threads = scrape_category_threads(args.cat_id, args.pages, args.delay)
    print(f"Found {len(threads)} threads. Fetching comments...\n")

    all_rows = []
    for i, t in enumerate(threads, 1):
        thread_id = t.get("thread_id")
        title = t.get("title", "")
        print(f"[{i}/{len(threads)}] thread {thread_id}: {title[:40]}")
        try:
            comments = scrape_thread_comments(thread_id, args.max_comment_pages, args.delay)
        except requests.RequestException as e:
            print(f"  [error] failed to fetch thread {thread_id}: {e}")
            continue

        for c in comments:
            all_rows.append({
                "thread_id": thread_id,
                "thread_title": title,
                "comment_id": c.get("msg_num"),
                "user_nickname": c.get("user_nickname"),
                "content": c.get("msg"),
                "post_time": c.get("post_time"),
                "like_count": c.get("like_count"),
                "dislike_count": c.get("dislike_count"),
            })

    fieldnames = [
        "thread_id", "thread_title", "comment_id", "user_nickname",
        "content", "post_time", "like_count", "dislike_count",
    ]
    save_to_csv(all_rows, args.out, fieldnames)
    print(f"\nDone. Saved {len(all_rows)} comments across {len(threads)} threads to {args.out}")


if __name__ == "__main__":
    main()