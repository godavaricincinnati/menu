import csv
import re
import sys
from playwright.sync_api import sync_playwright

CLOVER_URL = "https://godavari-cincinnati-mason-4.cloveronline.com/menu/all"
OUTPUT_FILE = "menu.csv"
TEMP_FILE = "menu_new.csv"
MIN_ITEMS_REQUIRED = 20

def clean(text):
    return re.sub(r"\s+", " ", text or "").strip()

def parse_item(line):
    match = re.search(r"\$(\d+(?:\.\d{2})?)", line)
    if not match:
        return None, None

    price = match.group(1)
    name = clean(line[:match.start()])
    name = re.sub(r"^\d+\.\s*", "", name).strip()
    return name, price

def main():
    rows = []

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(CLOVER_URL, wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(5000)

        text = page.inner_text("body")
        browser.close()

    current_category = "Menu"

    for raw_line in text.splitlines():
        line = clean(raw_line)

        if not line:
            continue

        if "$" not in line and len(line) > 3 and len(line) < 70:
            upper_ratio = sum(1 for c in line if c.isupper()) / max(len(line), 1)
            if upper_ratio > 0.45:
                current_category = line
            continue

        if "$" in line:
            name, price = parse_item(line)

            if name and price:
                rows.append({
                    "Category": current_category,
                    "Item Name": name,
                    "Description": "",
                    "Price": price,
                    "Available": "TRUE"
                })

    if len(rows) < MIN_ITEMS_REQUIRED:
        print(f"ERROR: Only found {len(rows)} items. Keeping old menu.csv.")
        sys.exit(1)

    with open(TEMP_FILE, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["Category", "Item Name", "Description", "Price", "Available"]
        )
        writer.writeheader()
        writer.writerows(rows)

    import os
    os.replace(TEMP_FILE, OUTPUT_FILE)

    print(f"Updated {OUTPUT_FILE} with {len(rows)} items.")

if __name__ == "__main__":
    main()
