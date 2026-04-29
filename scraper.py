#!/usr/bin/env python3
import csv
import os
import re
import sys
import time
from datetime import datetime

import requests
from bs4 import BeautifulSoup

URL = "https://godavari-cincinnati-mason-4.cloveronline.com/menu/all"
OUTPUT_FILE = "menu.csv"
TEMP_FILE = "menu_new.csv"

HEADERS_CSV = ["Category", "Item Name", "Description", "Price", "Available"]
MIN_ITEMS_REQUIRED = 50

REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

CATEGORY_ORDER = {
    "GODAVARI SPECIALITIES": 10,
    "KIDS SPECIAL": 20,
    "COMBOS": 30,
    "FAMILY PACKS": 40,
    "SOUPS": 50,
    "VEG-APPETIZERS": 60,
    "NON - VEG APPETIZERS": 70,
    "NON-VEG APPETIZERS": 70,
    "CHAATS": 80,
    "SNACKS": 90,
    "TANDOOR": 100,
    "SOUTH INDIAN DOSA VARIETIES": 110,
    "GODAVARI-CHINESE SPECIALITIES": 120,
    "ROTI BASKET": 130,
    "VEG- ENTREES": 140,
    "VEG ENTREES": 140,
    "NON-VEGETARIAN ENTREES": 150,
    "BIRYANI/RICE SPECIALITIES": 160,
    "DRINKS": 170,
    "BEER": 180,
    "WINE": 190,
    "SPIRITS": 200,
    "DESSERTS": 210,
    "ICE CREAMS": 220,
    "EXTRA ITEMS": 230,
}

REMOVE_NAMES_OR_CATEGORIES = {
    "MENU",
    "SNACKS_OLD",
    "SNACKS OLD",
    "DANCE EVENT",
}

SKIP_TEXT = {
    "ADD TO ORDER",
    "ORDER NOW",
    "VIEW CART",
    "CHECKOUT",
    "CATEGORIES",
    "MENU",
    "BACK",
    "NEXT",
}


def clean(text):
    return re.sub(r"\s+", " ", str(text or "")).strip()


def norm(text):
    return clean(text).upper()


def clean_price(text):
    match = re.search(r"\$?\s*(\d+(?:\.\d{1,2})?)", text)
    if not match:
        return ""
    return f"{float(match.group(1)):.2f}"


def fetch_page():
    for attempt in range(1, 4):
        try:
            print(f"[{attempt}/3] Fetching Clover menu...")
            response = requests.get(URL, headers=REQUEST_HEADERS, timeout=30)
            response.raise_for_status()
            return BeautifulSoup(response.text, "html.parser")
        except requests.RequestException as exc:
            print(f"[WARN] Request failed: {exc}")
            time.sleep(2)

    return None


def is_category_line(line):
    n = norm(line)
    return n in CATEGORY_ORDER


def should_remove(value):
    return norm(value) in REMOVE_NAMES_OR_CATEGORIES


def extract_lines(soup):
    body = soup.find("body") or soup
    text = body.get_text("\n")
    return [clean(line) for line in text.splitlines() if clean(line)]


def parse_lines(lines):
    rows = []
    current_category = ""
    pending_name = ""
    original_order = 0

    for line in lines:
        line = clean(line)
        nline = norm(line)

        if not line or nline in SKIP_TEXT:
            continue

        if is_category_line(line):
            current_category = CATEGORY_ORDER_MATCH(nline)
            pending_name = ""
            continue

        if should_remove(line):
            pending_name = ""
            continue

        if not current_category or should_remove(current_category):
            continue

        if "$" in line:
            price = clean_price(line)
            name_part = clean(re.sub(r"\$?\s*\d+(?:\.\d{1,2})?", "", line))

            if name_part:
                item_name = name_part
            else:
                item_name = pending_name

            item_name = clean(item_name)

            if (
                item_name
                and price
                and not should_remove(item_name)
                and norm(item_name) not in SKIP_TEXT
                and len(item_name) > 1
            ):
                rows.append({
                    "Category": current_category,
                    "Item Name": item_name,
                    "Description": "",
                    "Price": price,
                    "Available": "TRUE",
                    "_Order": original_order,
                })
                original_order += 1

            pending_name = ""
            continue

        # Likely item name line before price line
        if len(line) <= 120 and not is_noise(line):
            pending_name = line

    return rows


def CATEGORY_ORDER_MATCH(nline):
    for cat in CATEGORY_ORDER:
        if norm(cat) == nline:
            return cat
    return nline


def is_noise(line):
    n = norm(line)

    if n in SKIP_TEXT:
        return True

    if any(x in n for x in ["CLOVER", "POWERED BY", "PRIVACY", "TERMS"]):
        return True

    if len(line) < 2:
        return True

    return False


def dedupe(rows):
    seen = set()
    clean_rows = []

    for row in rows:
        key = (
            norm(row["Category"]),
            norm(row["Item Name"]),
            row["Price"],
        )

        if key in seen:
            continue

        seen.add(key)
        clean_rows.append(row)

    return clean_rows


def sort_rows(rows):
    return sorted(
        rows,
        key=lambda r: (
            CATEGORY_ORDER.get(norm(r["Category"]), 999),
            r["_Order"],
        )
    )


def write_csv_safely(rows):
    if len(rows) < MIN_ITEMS_REQUIRED:
        print(f"[ERROR] Only found {len(rows)} items. Keeping old menu.csv.")
        sys.exit(1)

    final_rows = [
        {
            "Category": r["Category"],
            "Item Name": r["Item Name"],
            "Description": r["Description"],
            "Price": r["Price"],
            "Available": r["Available"],
        }
        for r in rows
    ]

    with open(TEMP_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=HEADERS_CSV)
        writer.writeheader()
        writer.writerows(final_rows)

    if os.path.exists(OUTPUT_FILE):
        backup = f"{OUTPUT_FILE}.bak_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        with open(OUTPUT_FILE, "r", encoding="utf-8") as old_file:
            old_content = old_file.read()
        with open(backup, "w", encoding="utf-8") as backup_file:
            backup_file.write(old_content)
        print(f"[INFO] Backup created: {backup}")

    os.replace(TEMP_FILE, OUTPUT_FILE)
    print(f"[OK] Wrote {len(final_rows)} clean items to {OUTPUT_FILE}")


def main():
    soup = fetch_page()

    if soup is None:
        print("[ERROR] Could not fetch Clover page. Existing menu.csv was not changed.")
        sys.exit(1)

    lines = extract_lines(soup)
    rows = parse_lines(lines)
    rows = dedupe(rows)
    rows = sort_rows(rows)

    print(f"[INFO] Extracted {len(rows)} valid items.")

    print("\nCategory order found:")
    for cat in dict.fromkeys([r["Category"] for r in rows]):
        print(f" - {cat}")

    write_csv_safely(rows)


if __name__ == "__main__":
    main()
