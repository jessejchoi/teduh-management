#!/usr/bin/env python3
"""
Diagnostic: dumps everything Playwright can see on a listing page.
Usage: python3 diagnose.py 38653259
"""
import sys, time, re
from datetime import date, timedelta
from playwright.sync_api import sync_playwright

listing_id = sys.argv[1] if len(sys.argv) > 1 else "38653259"

# Optional: python3 diagnose.py <listing_id> <checkin> <checkout>
# e.g.:  python3 diagnose.py 38653259 2026-04-17 2026-04-20
if len(sys.argv) >= 4:
    checkin  = sys.argv[2]
    checkout = sys.argv[3]
else:
    # Same dates the daily scraper would use
    base = date.today() + timedelta(days=14)
    tue = base + timedelta(days=(1 - base.weekday()) % 7)
    checkin  = tue.isoformat()
    checkout = (tue + timedelta(days=3)).isoformat()

url = f"https://www.airbnb.com/rooms/{listing_id}?check_in={checkin}&check_out={checkout}&adults=2&currency=USD"
print(f"URL: {url}\n")

with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(url, wait_until="domcontentloaded", timeout=45000)
    time.sleep(6)

    # Scroll to booking widget
    page.evaluate("window.scrollTo(0, 600)")
    time.sleep(3)

    # 1. Full inner_text
    body = page.inner_text("body")
    with open("diag_body.txt", "w") as f:
        f.write(body)
    print(f"[1] body inner_text saved to diag_body.txt ({len(body)} chars)")

    # 2. Check for key phrases
    for phrase in ["minimum stay", "those dates", "these dates", "change dates",
                   "reserve", "minimum", "night"]:
        found = phrase.lower() in body.lower()
        print(f"    '{phrase}' in body: {found}")

    # 3. Try Playwright locators
    print("\n[2] Playwright locator checks:")
    for selector in [
        "text=/minimum stay/i",
        "text=/change dates/i",
        "text=/those dates/i",
        "[data-section-id='BOOK_IT_SIDEBAR']",
        "[data-testid='book-it-default']",
        "[data-testid='homes-pdp-cta-btn']",
    ]:
        try:
            loc = page.locator(selector)
            count = loc.count()
            if count > 0:
                txt = loc.first.text_content(timeout=1000) or ""
                print(f"    FOUND ({count}x) '{selector}': {txt.strip()[:300]}")
            else:
                print(f"    not found: '{selector}'")
        except Exception as e:
            print(f"    error '{selector}': {e}")

    # 4. Dump full page HTML (booking widget area)
    html = page.content()
    with open("diag_page.html", "w") as f:
        f.write(html)
    print(f"\n[3] Full HTML saved to diag_page.html ({len(html)} chars)")

    # 5. Screenshot
    page.screenshot(path="diag_screenshot.png", full_page=False)
    print("[4] Screenshot saved to diag_screenshot.png")

    browser.close()

print("\nSearch diag_page.html for 'minimum' to find the booking widget HTML structure.")
