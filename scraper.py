import csv
import re
import requests
from bs4 import BeautifulSoup

CLOVER_URL = "https://godavari-cincinnati-mason-4.cloveronline.com/menu/all"
OUTPUT_FILE = "menu.csv"

def clean(text):
    return re.sub(r"\s+", " ", text or "").strip()

def split_item_price(text):
    match = re.search(r"\s+\$(\d+(?:\.\d{2})?)$", text)
    if not match:
        return clean(text), ""

    price = match.group(1)
    name = clean(text[:match.start()])
    return name, price

def main():
    response = requests.get(CLOVER_URL, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    text = soup.get_text("\n")

    rows = []
    current_category = ""

    for line in text.splitlines():
        line = clean(line)

        if not line:
            continue

        if line.isupper() and "$" not in line and len(line) > 2:
            current_category = line
            continue

        if "$" in line and current_category:
            name, price = split_item_price(line)

            if name and price:
                rows.append({
                    "Category": current_category,
                    "Item Name": name,
                    "Description": "",
                    "Price": price,
                    "Available": "TRUE"
                })

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["Category", "Item Name", "Description", "Price", "Available"]
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"Created {OUTPUT_FILE} with {len(rows)} items.")

if __name__ == "__main__":
    main()
