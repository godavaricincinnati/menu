#!/usr/bin/env python3
"""
Menu scraper for godavari-cincinnati-mason-4.cloveronline.com
Extracts: Category, Item Name, Description, Price, Available
Writes to menu.csv — will NOT overwrite if no data is extracted.
"""

import csv
import sys
import time
import os
from datetime import datetime

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("[ERROR] Missing dependencies. Install with:")
    print("  pip install requests beautifulsoup4")
    sys.exit(1)

# ── Config ────────────────────────────────────────────────────────────────────
URL = "https://godavari-cincinnati-mason-4.cloveronline.com/menu/all"
OUTPUT_FILE = "menu.csv"
HEADERS_CSV = ["Category", "Item Name", "Description", "Price", "Available"]

REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def fetch_page(url: str, retries: int = 3, delay: float = 2.0) -> BeautifulSoup | None:
    """Fetch URL with retry logic; return BeautifulSoup or None on failure."""
    for attempt in range(1, retries + 1):
        try:
            print(f"[{attempt}/{retries}] Fetching {url} ...")
            resp = requests.get(url, headers=REQUEST_HEADERS, timeout=20)
            resp.raise_for_status()
            return BeautifulSoup(resp.text, "html.parser")
        except requests.RequestException as exc:
            print(f"  [WARN] Request failed: {exc}")
            if attempt < retries:
                print(f"  Retrying in {delay}s ...")
                time.sleep(delay)
    print("[ERROR] All fetch attempts failed.")
    return None


def clean(text: str | None) -> str:
    """Strip and normalise whitespace."""
    if not text:
        return ""
    return " ".join(text.strip().split())


def parse_price(raw: str) -> str:
    """Return a clean price string like '$12.99', or '' if none found."""
    import re
    match = re.search(r"\$[\d,]+\.?\d*", raw)
    return match.group(0) if match else clean(raw)


# ── Core parser ───────────────────────────────────────────────────────────────

def extract_menu(soup: BeautifulSoup) -> list[dict]:
    """
    Walk the Clover Online menu DOM and return a list of item dicts.

    Clover Online typically renders:
      <section class="category-items"> or similar wrapper
        <h2 class="category-name"> / <div class="category-header">
        <div class="item-card"> / <li class="menu-item">
            .item-name / .item-title
            .item-description
            .item-price / .price
            .item-available / availability badge  (optional)
    """
    items: list[dict] = []

    # ── Strategy 1: structured category → item hierarchy ──────────────────
    # Try several common Clover / generic menu selectors
    category_blocks = (
        soup.select("section.category-items")
        or soup.select("div.category-section")
        or soup.select("div[class*='category']")
    )

    if category_blocks:
        for block in category_blocks:
            # Category name
            cat_el = (
                block.find(class_=lambda c: c and "category" in c and ("name" in c or "header" in c or "title" in c))
                or block.find(["h2", "h3", "h4"])
            )
            category = clean(cat_el.get_text()) if cat_el else "Uncategorised"

            # Item cards within this category
            item_cards = (
                block.select("div.item-card")
                or block.select("li.menu-item")
                or block.select("div[class*='item']")
            )

            for card in item_cards:
                items.append(_parse_card(card, category))

    # ── Strategy 2: flat item list (no category wrapper) ──────────────────
    if not items:
        all_cards = (
            soup.select("div.item-card")
            or soup.select("li.menu-item")
            or soup.select("div[class*='menu-item']")
        )
        for card in all_cards:
            items.append(_parse_card(card, ""))

    # ── Strategy 3: JSON-LD / script tag data ─────────────────────────────
    if not items:
        items = _try_json_ld(soup)

    # ── Strategy 4: broad fallback — any element with a price ─────────────
    if not items:
        items = _broad_fallback(soup)

    return [i for i in items if i.get("Item Name")]   # drop empties


def _parse_card(card, category: str) -> dict:
    """Extract fields from a single item card element."""
    import re

    # Name — try explicit class selectors first, then first heading/strong
    name_el = (
        card.find(class_=lambda c: c and any(k in c for k in ("item-name", "item-title", "menu-item-name")))
        or card.find(["h3", "h4", "h5", "strong"])
    )
    name = clean(name_el.get_text()) if name_el else ""

    # Description
    desc_el = (
        card.find(class_=lambda c: c and ("description" in c or "desc" in c))
        or card.find("p")
    )
    description = clean(desc_el.get_text()) if desc_el else ""
    # Avoid echoing the name as description
    if description == name:
        description = ""

    # Price
    price_el = card.find(class_=lambda c: c and "price" in c)
    raw_price = clean(price_el.get_text()) if price_el else ""
    if not raw_price:
        # Search entire card text for a dollar amount
        raw_price = re.search(r"\$[\d,]+\.?\d*", card.get_text()) 
        raw_price = raw_price.group(0) if raw_price else ""
    price = parse_price(raw_price) if raw_price else ""

    # Available
    avail_el = card.find(class_=lambda c: c and ("avail" in c or "stock" in c or "soldout" in c or "unavailable" in c))
    if avail_el:
        text = clean(avail_el.get_text()).lower()
        available = "No" if any(k in text for k in ("unavailable", "sold out", "out of stock")) else "Yes"
    else:
        available = "Yes"   # default: assume available

    return {
        "Category": category,
        "Item Name": name,
        "Description": description,
        "Price": price,
        "Available": available,
    }


def _try_json_ld(soup: BeautifulSoup) -> list[dict]:
    """Try to pull menu data from JSON-LD <script> tags."""
    import json, re
    items = []
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
            # Support both single object and list
            entries = data if isinstance(data, list) else [data]
            for entry in entries:
                if entry.get("@type") in ("Menu", "FoodEstablishment"):
                    for section in entry.get("hasMenuSection", []):
                        cat = section.get("name", "")
                        for item in section.get("hasMenuItem", []):
                            offers = item.get("offers", {})
                            price = offers.get("price", "")
                            currency = offers.get("priceCurrency", "$")
                            items.append({
                                "Category": cat,
                                "Item Name": item.get("name", ""),
                                "Description": item.get("description", ""),
                                "Price": f"{currency}{price}" if price else "",
                                "Available": "Yes",
                            })
        except (json.JSONDecodeError, AttributeError):
            continue
    return items


def _broad_fallback(soup: BeautifulSoup) -> list[dict]:
    """
    Last-resort: find any element whose sibling or child contains a price.
    Groups items under the nearest preceding heading.
    """
    import re
    items = []
    price_pattern = re.compile(r"\$\d+")
    current_category = "Menu"

    for el in soup.find_all(["h2", "h3", "h4", "li", "div", "tr"]):
        text = clean(el.get_text())
        if not text:
            continue
        if el.name in ("h2", "h3", "h4") and not price_pattern.search(text):
            current_category = text
            continue
        price_match = price_pattern.search(text)
        if price_match:
            # Strip the price from the text to get the name
            name = price_pattern.sub("", text).strip(" -|:")
            name = " ".join(name.split())
            if name:
                items.append({
                    "Category": current_category,
                    "Item Name": name,
                    "Description": "",
                    "Price": parse_price(price_match.group(0)),
                    "Available": "Yes",
                })
    return items


# ── CSV writer ────────────────────────────────────────────────────────────────

def write_csv(items: list[dict], filepath: str) -> None:
    """Write items to CSV. Creates a timestamped backup if the file exists."""
    if os.path.exists(filepath):
        backup = f"{filepath}.bak_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        os.rename(filepath, backup)
        print(f"[INFO] Existing file backed up → {backup}")

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=HEADERS_CSV)
        writer.writeheader()
        writer.writerows(items)
    print(f"[OK] {len(items)} item(s) written to {filepath}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    print("=" * 60)
    print("Godavari Menu Scraper")
    print("=" * 60)

    soup = fetch_page(URL)
    if soup is None:
        print("[ABORT] Could not fetch the page. menu.csv has NOT been modified.")
        sys.exit(1)

    items = extract_menu(soup)

    if not items:
        print(
            "[WARN] No menu items were extracted from the page.\n"
            "       This may mean the site renders via JavaScript (SPA)\n"
            "       or the page structure has changed.\n"
            "       menu.csv has NOT been modified (fallback protection)."
        )
        # ── Hint: try Playwright if BS4 finds nothing ──────────────────────
        print("\n[TIP]  If the menu is loaded by JavaScript, try:\n"
              "       pip install playwright && playwright install chromium\n"
              "       Then replace requests+BS4 with:\n"
              "         from playwright.sync_api import sync_playwright\n"
              "         with sync_playwright() as p:\n"
              "             browser = p.chromium.launch()\n"
              "             page = browser.new_page()\n"
              "             page.goto(URL)\n"
              "             page.wait_for_load_state('networkidle')\n"
              "             html = page.content()\n"
              "             browser.close()\n"
              "         soup = BeautifulSoup(html, 'html.parser')")
        sys.exit(0)

    write_csv(items, OUTPUT_FILE)
    print("\nSample (first 5 rows):")
    print(f"{'Category':<20} {'Item Name':<30} {'Price':<10} {'Available'}")
    print("-" * 75)
    for row in items[:5]:
        print(f"{row['Category']:<20} {row['Item Name']:<30} {row['Price']:<10} {row['Available']}")


if __name__ == "__main__":
    main()
