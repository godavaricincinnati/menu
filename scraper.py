import csv
import re
import sys
import requests
from bs4 import BeautifulSoup

CLOVER_URL = "https://godavari-cincinnati-mason-4.cloveronline.com/menu/all"
OUTPUT_FILE = "menu.csv"
TEMP_FILE = "menu_new.csv"
MIN_ITEMS_REQUIRED = 20

def clean(text):
    return re.sub(r"\s+", " ", text or "").strip()

def split_item_price(text):
    match = re.search(r"\$(\d+(?:\.\d{2})?)", text)
    if not match:
        return "", ""

    price = match.group(1)
    name = clean(text[:match.start()])
    return name, price

def main():
    response = requests.get(
        CLOVER_URL,
        timeout=30,
        headers={
            "User-Agent": "Mozilla/5.0"
        }
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    text = soup.get_text("\n")

    rows = []
    current_category = "Menu"

    for line in text.splitlines():
        line = clean(line)

        if not line:
            continue

        # Category guess
        if "$" not in line and len(line) > 3 and len(line) < 60:
            current_category = line
            continue

        # Item with price
        if "$" in line:
            name, price = split_item_price(line)

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
