"""
LIHKG Data Scraper (cloudscraper version)
------------------------------------------
Same as before, but uses cloudscraper instead of plain requests.
cloudscraper is a Python library built specifically to get past
Cloudflare's "is this a real browser?" challenge automatically -
something plain `requests` cannot do, no matter how good the
headers/cookies look.

Install first:
    pip install cloudscraper

Usage:
    python lihkg_scraper_cloudscraper.py --cat_id 1 --pages 5 --out lihkg_data.csv
"""

import argparse
import csv
import time

import cloudscraper
