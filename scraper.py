#!/usr/bin/env python3
"""
Airbnb Scraper — Fixed Version
===============================
Uses Playwright to load pages with JavaScript rendering,
waits for price elements to appear, and extracts from the visible DOM.

SETUP:
    pip3 install playwright
    python3 -m playwright install chromium

TEST:
    python3 scraper_v2.py test 7816774
    python3 scraper_v2.py test 740740767777327164

USAGE:
    python3 scraper_v2.py daily
    python3 scraper_v2.py export
    python3 scraper_v2.py dashboard
"""

import json
import csv
import re
import sys
import time
import random
import sqlite3
import os
import subprocess
from datetime import datetime, timedelta, date
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("Install Playwright: pip3 install playwright && python3 -m playwright install chromium")
    sys.exit(1)


# ============================================================
# COMP SET
# ============================================================

COMP_SET = [
    # 3bed T1
    {"id": "1604026291084350665", "name": "Luxury Ocean Penthouse", "seg": "3bed", "tier": 1},
    {"id": "1260779550472232920", "name": "3BR Villa nr Finns", "seg": "3bed", "tier": 1},
    {"id": "740740767777327164", "name": "Luxury 3BD 5min Berawa", "seg": "3bed", "tier": 1},
    {"id": "563299601221833197", "name": "3BR Modern Villa 8", "seg": "3bed", "tier": 1},
    {"id": "1097701933258947716", "name": "Rooftop Villa 5min Beach", "seg": "3bed", "tier": 1},
    {"id": "919973384400939699", "name": "Stylish 3BR Central Berawa", "seg": "3bed", "tier": 1},
    {"id": "1421412926075870027", "name": "Stylish 3BR near Finns", "seg": "3bed", "tier": 1},
    {"id": "7816774", "name": "Villa Brawa 8 Gated", "seg": "3bed", "tier": 1},
    {"id": "1246974698177486449", "name": "3BR Middle Berawa", "seg": "3bed", "tier": 1},
    {"id": "1186798051332352659", "name": "NEW Luxury 3-Bed Finns", "seg": "3bed", "tier": 1},
    {"id": "1343847909033077232", "name": "Japanese Villa Canggu", "seg": "3bed", "tier": 1},
    {"id": "1562145383329964039", "name": "NEW 3BR White1 Finns", "seg": "3bed", "tier": 1},
    {"id": "1563457861462943982", "name": "NEW 3BR White2 Finns", "seg": "3bed", "tier": 1},
    # 3bed T2
    {"id": "1030274998823322683", "name": "Villa Morena 5 Star", "seg": "3bed", "tier": 2},
    {"id": "1480064268798874150", "name": "Stylish 3BR Pool Rooftop", "seg": "3bed", "tier": 2},
    {"id": "1559001467158118688", "name": "Nila next to FINNS", "seg": "3bed", "tier": 2},
    {"id": "881605297614853263", "name": "Munno Villa Canggu", "seg": "3bed", "tier": 2},
    {"id": "1558989241588807313", "name": "Nila Lux 3BR Pool", "seg": "3bed", "tier": 2},
    {"id": "1445368779085312552", "name": "Leaf Villas 3BR", "seg": "3bed", "tier": 2},
    {"id": "1278728171907628525", "name": "Lavish Retreat Berawa", "seg": "3bed", "tier": 2},
    # 3bed T3
    {"id": "741532290478694882", "name": "Modern 3B 10min Finns", "seg": "3bed", "tier": 3},
    {"id": "1570757914884620958", "name": "New 3BR Pool Beach", "seg": "3bed", "tier": 3},
    {"id": "969120409631112130", "name": "Villa Melrose", "seg": "3bed", "tier": 3},
    {"id": "43024868", "name": "3BR 900m Beach", "seg": "3bed", "tier": 3},
    {"id": "1445484364412352338", "name": "3BR Near Beach Clubs", "seg": "3bed", "tier": 3},
    {"id": "557467516246068376", "name": "3BR Villa 6 7min Beach", "seg": "3bed", "tier": 3},
    {"id": "1540423622234051016", "name": "Top Location 3BR Pool", "seg": "3bed", "tier": 3},
    {"id": "1599665002844851012", "name": "La Maison Prime", "seg": "3bed", "tier": 3},
    {"id": "1177904917448183650", "name": "Luxury 3BR Batu Belig", "seg": "3bed", "tier": 3},
    {"id": "1057002811427452476", "name": "AMR Echo Beach", "seg": "3bed", "tier": 3},
    {"id": "1525816222234525034", "name": "Blanche Colonial 3BR", "seg": "3bed", "tier": 3},
    {"id": "954625449449986059", "name": "Mediterranean Berawa", "seg": "3bed", "tier": 3},
    {"id": "1260891294147423635", "name": "Stylish 3BR 5min Beach", "seg": "3bed", "tier": 3},
    {"id": "1541763311092477753", "name": "Elegant 3BR Sanctuary", "seg": "3bed", "tier": 3},
    # 4bed T1
    {"id": "42391918", "name": "4BR Walk to Finns", "seg": "4bed", "tier": 1},
    {"id": "53222117", "name": "4BR Berawa 5min Beach", "seg": "4bed", "tier": 1},
    {"id": "1132882041001951622", "name": "Classy 4BR Canggu", "seg": "4bed", "tier": 1},
    {"id": "28616815", "name": "Modern 4BR 400m Beach", "seg": "4bed", "tier": 1},
    {"id": "1577206637482043934", "name": "NEW 4BR White Finns", "seg": "4bed", "tier": 1},
    {"id": "996850033553890986", "name": "Modern Pool Villa Berawa", "seg": "4bed", "tier": 1},
    {"id": "15196766", "name": "5Bed LUX Walk Beach", "seg": "4bed", "tier": 1},
    # 4bed T2
    {"id": "915596053126277361", "name": "Hidden 4BR by OXO", "seg": "4bed", "tier": 2},
    # 4bed T3
    {"id": "1582993290173349509", "name": "Designer 4BR Berawa", "seg": "4bed", "tier": 3},
    {"id": "914823266465015236", "name": "Coastal Elegance 4BR", "seg": "4bed", "tier": 3},
    {"id": "38653259", "name": "Beachside 4BR Berawa", "seg": "4bed", "tier": 3},
    {"id": "1441230148006767836", "name": "Modern 4BR Heart Berawa", "seg": "4bed", "tier": 3},
    {"id": "1024869591443049666", "name": "Chic Tropical 4BR", "seg": "4bed", "tier": 3},
    # 6bed T1
    {"id": "39234619", "name": "Luxury 6BR 400m Finns", "seg": "6bed", "tier": 1},
    {"id": "688704203998884163", "name": "Luxury 6BR Canggu Finns", "seg": "6bed", "tier": 1},
    # 6bed T2
    {"id": "778538840882836502", "name": "Luxury 6BR Berawa Beach", "seg": "6bed", "tier": 2},
    {"id": "30131363", "name": "Stunning 6BR 400m Beach", "seg": "6bed", "tier": 2},
    {"id": "1014411261462296954", "name": "Luxury 7BR Walk Beach", "seg": "6bed", "tier": 2},
    {"id": "6035944", "name": "Beach Club Estate", "seg": "6bed", "tier": 2},
    # 6bed T3
    {"id": "1130964709355224593", "name": "Massive Atlas Villa", "seg": "6bed", "tier": 3},
    {"id": "978675715561001798", "name": "NEW BEACH LUXXE", "seg": "6bed", "tier": 3},
    {"id": "1017837371311361319", "name": "Modern Villas Berawa", "seg": "6bed", "tier": 3},
    {"id": "1268649850059160306", "name": "Cassia 7BR Berawa", "seg": "6bed", "tier": 3},
]

# ============================================================
# CONFIG
# ============================================================

DB_PATH = Path(__file__).parent / "comp_data.db"
EXPORT_DIR = Path(__file__).parent / "exports"
MIN_DELAY = 4
MAX_DELAY = 8

# Which segments to scrape. Change this when 4-bed villas are ready.
ACTIVE_SEGMENTS = ["3bed", "6bed"]

# Scrape label constants — used in save_price() and queries throughout
LABEL_WEEKDAY          = "weekday"
LABEL_WEEKEND          = "weekend"
LABEL_3N_BASELINE      = "3n_baseline"
LABEL_7N_WEEKLY        = "7n_weekly"
LABEL_28N_MONTHLY      = "28n_monthly"
LABEL_SEASONAL_PREFIX  = "seasonal_"
LABEL_LEADTIME_PREFIX  = "leadtime_"


def active_comps(tier_filter=None, limit=None, override=None):
    """Return comps in active segments, optionally filtered by tier(s).

    Args:
        tier_filter: int or list of ints — filter by tier(s)
        limit: cap returned comps (used by test-all to avoid global mutation)
        override: list of listing IDs — return only these (ignores segments/tiers)
    """
    if override:
        return [c for c in COMP_SET if c["id"] in override]
    comps = [c for c in COMP_SET if c["seg"] in ACTIVE_SEGMENTS]
    if tier_filter:
        tiers = tier_filter if isinstance(tier_filter, list) else [tier_filter]
        comps = [c for c in comps if c["tier"] in tiers]
    if limit:
        comps = comps[:limit]
    return comps


# ============================================================
# BROWSER
# ============================================================

def create_browser():
    pw = sync_playwright().start()
    browser = pw.chromium.launch(
        headless=True,
        args=[
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-setuid-sandbox",
        ]
    )
    context = browser.new_context(
        viewport={"width": 1920, "height": 1080},
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        locale="en-US",
        timezone_id="Asia/Makassar",
    )
    # Hide automation indicators
    context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
        window.chrome = { runtime: {} };
    """)
    return pw, browser, context


# ============================================================
# EXTRACTION — The core fix
# ============================================================

def extract_price_from_page(page, listing_id, checkin, checkout):
    """
    Load listing with dates and extract price from the RENDERED page.
    Uses JavaScript extraction first (most reliable), then body text fallback.
    """
    url = f"https://www.airbnb.com/rooms/{listing_id}?check_in={checkin}&check_out={checkout}&adults=2&currency=USD"

    nights = (datetime.strptime(checkout, "%Y-%m-%d") - datetime.strptime(checkin, "%Y-%m-%d")).days

    result = {
        "nightly_rate": None,
        "total_price": None,
        "is_available": True,
        "rating": None,
        "review_count": None,
        "nights": nights,
        "min_stay_detected": None,
        "min_stay_not_met": False,
        "dates_unavailable": False,
    }

    try:
        print(f"    Loading {url[:80]}...")
        page.goto(url, wait_until="domcontentloaded", timeout=45000)

        # Dismiss popups
        time.sleep(1.5)
        for dismiss_attempt in range(3):
            try:
                page.keyboard.press("Escape")
                time.sleep(0.5)
                for sel in ['button[aria-label="Close"]', '[data-testid="close-button"]',
                            'div[role="dialog"] button', 'button:has-text("Close")',
                            'button:has-text("Got it")', 'button:has-text("OK")']:
                    try:
                        btn = page.query_selector(sel)
                        if btn and btn.is_visible():
                            btn.click()
                            time.sleep(0.5)
                            break
                    except Exception:
                        continue
                dialog = page.query_selector('div[role="dialog"]')
                if not dialog or not dialog.is_visible():
                    break
            except Exception:
                break

        body_text = ""
        price_found = False

        MIN_STAY_RE = r'(?:(\d+)\s*(?:-\s*)?night\s*minimum|[Mm]inimum\s+stay\s+(?:is\s+)?(\d+)\s*nights?)'
        UNAVAIL_SIGNALS = [
            "this listing is unavailable", "listing isn't available",
            "those dates are not available", "those dates aren't available",
            "these dates aren't available", "these dates are unavailable",
            "not available for your dates", "dates are not available",
        ]

        # Wait up to 10 seconds for price to render.
        # Check immediately first — skip the initial sleep if the price is already
        # in the DOM (saves ~2s on fast pages). Sleep only between failed attempts.
        for attempt in range(6):
            body_text = page.inner_text("body")
            body_lower = body_text.lower()

            # CAPTCHA / bot detection check — bail early, don't waste time waiting
            # for a price that will never appear. Checked first so the loop breaks
            # before spending more time on a blocked page.
            if attempt == 0:
                captcha_signals = [
                    "verify you're human", "verify you are human",
                    "i'm not a robot", "complete the captcha",
                    "security check", "prove you're not a robot",
                    "please verify", "unusual traffic",
                ]
                if any(sig in body_lower for sig in captcha_signals):
                    print(f"    → CAPTCHA/bot detection — skipping (marking as scrape failure)")
                    result["is_available"] = False
                    result["_captcha"] = True
                    break

            # Check for min-stay language first on every attempt, before the
            # unavailability check, so we can distinguish "min stay not met"
            # from a genuine booking on the same body read.
            min_stay_match = re.search(MIN_STAY_RE, body_text, re.IGNORECASE)
            if min_stay_match:
                result["min_stay_detected"] = int(min_stay_match.group(1) or min_stay_match.group(2))

            # Check ALL unavailability phrases — now includes "those dates" phrasing
            # that was previously only caught after all price extraction attempts failed.
            if any(sig in body_lower for sig in UNAVAIL_SIGNALS):
                if result["min_stay_detected"]:
                    result["min_stay_not_met"] = True
                    result["is_available"] = True
                    print(f"    → {result['min_stay_detected']}-night minimum (available but min stay not met)")
                else:
                    result["is_available"] = False
                    result["dates_unavailable"] = True
                    print(f"    → Listing unavailable for these dates")
                break

            # Min-stay detected without unavailability text and it exceeds our search
            # length — price won't render for this stay; break early so the caller
            # can retry with the correct night count.
            if result["min_stay_detected"] and result["min_stay_detected"] > nights:
                result["min_stay_not_met"] = True
                print(f"    → {result['min_stay_detected']}-night minimum detected")
                break

            # Check if a real price ($ followed by digits) has appeared
            if re.search(r'\$\s*\d', body_text) or "Rp" in body_text or "IDR" in body_text:
                break

            # Price not found yet — wait before retry
            time.sleep(2)

        if not result["is_available"] or result.get("min_stay_not_met"):
            pass  # Skip price extraction — booked or min stay not met (retry handled by caller)
        else:
            # ========================================
            # METHOD 1: JavaScript — extract from Airbnb's internal data
            # Most reliable: reads structured data, not rendered text
            # One retry with a 5s wait (data may not be loaded yet on first attempt)
            # ========================================
            for js_attempt in range(2):
                if price_found:
                    break
                if js_attempt > 0:
                    print(f"    (JS retry, waiting 5s...)")
                    time.sleep(5)
                try:
                    js_price = page.evaluate("""() => {
                    const r = { nightly: null, total: null, nights: null };

                    // Search script tags for pricing data
                    for (const s of document.querySelectorAll('script')) {
                        const t = s.textContent || '';
                        if (t.length < 50) continue;

                        // priceForDisplay: "$350"
                        let m = t.match(/"priceForDisplay"\\s*:\\s*"([^"]+)"/);
                        if (m) {
                            const nums = m[1].match(/[\\d,]+/g);
                            if (nums) r.nightly = parseFloat(nums[0].replace(/,/g, ''));
                        }

                        // priceString: "$350"
                        if (!r.nightly) {
                            m = t.match(/"priceString"\\s*:\\s*"[^"]*?([\\d,]+)[^"]*?"/);
                            if (m) r.nightly = parseFloat(m[1].replace(/,/g, ''));
                        }

                        // discountedPrice or originalPrice
                        if (!r.nightly) {
                            m = t.match(/"(?:discounted|original)Price"\\s*:\\s*"?\\$?\\s*([\\d,.]+)/);
                            if (m) r.nightly = parseFloat(m[1].replace(/,/g, ''));
                        }

                        // total amount
                        if (!r.total) {
                            m = t.match(/"total"\\s*:\\s*\\{\\s*"amount"\\s*:\\s*([\\d.]+)/);
                            if (m) r.total = parseFloat(m[1]);
                        }
                    }

                    // Try booking panel text directly (known test IDs)
                    const panel = document.querySelector('[data-testid="book-it-default"], [data-section-id="BOOK_IT_SIDEBAR"]');
                    if (panel && !r.nightly) {
                        const t = panel.innerText;
                        let m = t.match(/\\$(\\d[\\d,]*)\\s*(?:per\\s+|\\/?\\s*)?night/i);
                        if (m) r.nightly = parseFloat(m[1].replace(/,/g, ''));
                        if (!r.nightly) {
                            m = t.match(/\\$(\\d[\\d,]*)\\s*for\\s*(\\d+)\\s*night/i);
                            if (m) {
                                r.total = parseFloat(m[1].replace(/,/g, ''));
                                r.nights = parseInt(m[2]);
                                r.nightly = Math.round(r.total / r.nights);
                            }
                        }
                        if (!r.nightly) {
                            m = t.match(/\\$(\\d[\\d,]*)\\s*x\\s*\\d+\\s*night/i);
                            if (m) r.nightly = parseFloat(m[1].replace(/,/g, ''));
                        }
                    }

                    // Broad DOM scan: find any short element whose text matches
                    // a price+night pattern — catches panels with changed test IDs
                    if (!r.nightly) {
                        const els = document.querySelectorAll('span, div, button, h2');
                        for (const el of els) {
                            const t = (el.innerText || '').trim();
                            if (t.length > 60) continue;
                            let m = t.match(/\\$(\\d[\\d,]*)\\s*(?:\\/\\s*|per\\s+)?night/i);
                            if (m) { r.nightly = parseFloat(m[1].replace(/,/g,'')); break; }
                            m = t.match(/\\$(\\d[\\d,]*)\\s*x\\s*\\d+\\s*night/i);
                            if (m) { r.nightly = parseFloat(m[1].replace(/,/g,'')); break; }
                        }
                    }

                    // Broad script tag scan for additional JSON keys Airbnb uses
                    if (!r.nightly) {
                        for (const s of document.querySelectorAll('script')) {
                            const t = s.textContent || '';
                            if (t.length < 50) continue;
                            for (const key of ['basePrice','unitPrice','nightlyPrice','rate','displayPrice']) {
                                const m = t.match(new RegExp('"' + key + '"\\\\s*:\\\\s*"?\\\\$?\\\\s*([\\\\d,.]+)'));
                                if (m) {
                                    const v = parseFloat(m[1].replace(/,/g,''));
                                    if (v > 50 && v < 5000) { r.nightly = v; break; }
                                }
                            }
                            if (r.nightly) break;
                        }
                    }

                    return r;
                }""")

                    if js_price and js_price.get("nightly") and js_price["nightly"] > 0:
                        rate = js_price["nightly"]
                        # Sanity: is this a total disguised as nightly?
                        if rate > 800 and nights > 1:
                            per_night = rate / nights
                            if 80 <= per_night <= 800:
                                result["total_price"] = round(rate)
                                result["nightly_rate"] = round(per_night)
                                price_found = True
                                print(f"    (JS: ${rate:.0f} total ÷ {nights}n = ${result['nightly_rate']}/night)")
                        if not price_found and rate < 5000:
                            result["nightly_rate"] = round(rate)
                            price_found = True
                            if js_price.get("total"):
                                result["total_price"] = round(js_price["total"])
                            print(f"    (JS: ${rate:.0f}/night)")
                except Exception:
                    pass  # Try again on next iteration

            # ========================================
            # METHOD 2: Body text with aggressive line merging
            # ========================================
            if not price_found and body_text:
                # Merge lone "$" lines with the next numeric line
                lines = body_text.split('\n')
                merged_lines = []
                i_line = 0
                while i_line < len(lines):
                    line = lines[i_line].strip()
                    if line in ('$', 'US$'):
                        for j in range(1, 9):
                            if i_line + j < len(lines):
                                next_line = lines[i_line + j].strip()
                                if re.match(r'[\d,]+', next_line):
                                    merged_lines.append(f"${next_line}")
                                    i_line += j + 1
                                    break
                        else:
                            merged_lines.append(line)
                            i_line += 1
                    else:
                        merged_lines.append(line)
                        i_line += 1
                processed = '\n'.join(merged_lines)
                # Also collapse "$ 350" → "$350"
                processed = re.sub(r'\$\s+(\d)', r'$\1', processed)

                # Pattern A: "$X,XXX for N nights"
                m = re.search(r'(?:US)?\$([\d,]+)\s*for\s*(\d+)\s*nights?', processed, re.IGNORECASE)
                if m:
                    total = float(m.group(1).replace(",", ""))
                    dn = int(m.group(2))
                    result["total_price"] = total
                    result["nightly_rate"] = round(total / dn)
                    price_found = True
                    print(f"    (text: ${total:.0f} for {dn} nights = ${result['nightly_rate']}/night)")

                # Pattern B: "$XXX night" / "$XXX per night" / "$XXX / night"
                if not price_found:
                    m = re.search(r'(?:US)?\$([\d,]+)\s*(?:/\s*|per\s+)?night(?!s)', processed, re.IGNORECASE)
                    if m:
                        result["nightly_rate"] = float(m.group(1).replace(",", ""))
                        price_found = True

                # Pattern C: "$XXX x N nights"
                if not price_found:
                    m = re.search(r'(?:US)?\$([\d,]+)\s*x\s*\d+\s*nights?', processed, re.IGNORECASE)
                    if m:
                        result["nightly_rate"] = float(m.group(1).replace(",", ""))
                        price_found = True

                # Pattern D: aria-labels
                if not price_found:
                    try:
                        for el in page.query_selector_all('[aria-label]')[:50]:
                            label = el.get_attribute("aria-label") or ""
                            m = re.search(r'\$([\d,]+)\s*per\s*night', label, re.IGNORECASE)
                            if m:
                                result["nightly_rate"] = float(m.group(1).replace(",", ""))
                                price_found = True
                                break
                    except Exception:
                        pass

                # Pattern E: "Total ... $X" → divide
                if not price_found:
                    m = re.search(r'[Tt]otal\s*(?:before\s*taxes\s*)?(?:of\s*)?\$([\d,]+)', processed)
                    if m and nights > 0:
                        result["total_price"] = float(m.group(1).replace(",", ""))
                        result["nightly_rate"] = round(result["total_price"] / nights)
                        price_found = True
                        print(f"    (total ${result['total_price']:.0f} ÷ {nights}n)")

                # Pattern F: ratio analysis on all dollar amounts
                if not price_found:
                    all_prices = re.findall(r'(?:US)?\$([\d,]+)', processed)
                    amounts = sorted(set(
                        float(p.replace(",", "")) for p in all_prices
                        if 30 <= float(p.replace(",", "")) <= 10000
                    ))
                    if len(amounts) >= 2:
                        for idx, small in enumerate(amounts):
                            for large in amounts[idx+1:]:
                                ratio = large / small if small > 0 else 0
                                if abs(ratio - nights) < nights * 0.15:
                                    result["nightly_rate"] = round(small)
                                    result["total_price"] = round(large)
                                    price_found = True
                                    break
                            if price_found:
                                break
                    if not price_found and amounts:
                        for amt in amounts:
                            per_night = amt / nights
                            if 80 <= per_night <= 800:
                                result["nightly_rate"] = round(per_night)
                                result["total_price"] = round(amt)
                                price_found = True
                                break

            # METHOD 3: IDR fallback
            # Finds ALL IDR amounts, converts each to USD, then applies the same
            # ratio analysis as Pattern F to find the nightly/total pair.
            # Floor is $100/night — anything below is almost certainly a fee
            # (cleaning, service) rather than the room rate in the Berawa comp set.
            if not price_found and body_text:
                rp_matches = re.findall(r'(?:Rp|IDR)\s*\.?\s*([\d.,]+)', body_text)
                usd_amounts = []
                for raw in rp_matches:
                    try:
                        rp = float(raw.replace(".", "").replace(",", ""))
                        usd = rp / 16000
                        if 100 <= usd / max(nights, 1) <= 1500:
                            usd_amounts.append(usd)
                    except ValueError:
                        pass
                usd_amounts = sorted(set(round(u) for u in usd_amounts))

                if len(usd_amounts) >= 2:
                    # Look for a nightly/total pair (same ratio analysis as Pattern F)
                    for idx, small in enumerate(usd_amounts):
                        for large in usd_amounts[idx+1:]:
                            ratio = large / small if small > 0 else 0
                            if abs(ratio - nights) < nights * 0.15:
                                result["nightly_rate"] = round(small)
                                result["total_price"] = round(large)
                                price_found = True
                                print(f"    (IDR → ${result['nightly_rate']}/night, total ${result['total_price']})")
                                break
                        if price_found:
                            break
                if not price_found and usd_amounts:
                    # Single IDR amount above floor — treat as nightly rate
                    result["nightly_rate"] = round(usd_amounts[0] / nights)
                    result["total_price"] = round(usd_amounts[0])
                    price_found = True
                    print(f"    (IDR → ${result['nightly_rate']}/night)")

            # ========================================
            # DETECT: booked vs extraction failure
            # ========================================
            if not price_found:
                # Check unavailability FIRST — Airbnb may still have "Reserve"
                # text elsewhere on the page even when dates are blocked.
                # Scroll + re-read to catch lazy-loaded booking widget content
                page.evaluate("window.scrollTo(0, 600)")
                time.sleep(2)
                body_text = page.inner_text("body")
                body_lower = body_text.lower() if body_text else ""
                dates_unavailable = any(p in body_lower for p in [
                    "those dates are not available", "those dates aren't available",
                    "these dates aren't available", "these dates are unavailable",
                    "not available for your dates", "dates are not available",
                ])
                # Detect min stay via booking widget — body.inner_text() misses it
                # because Airbnb renders the widget outside the normal DOM flow.
                # Strategy: grab the whole booking widget text and regex it.
                if not result["min_stay_detected"]:
                    try:
                        # Try multiple selectors — Airbnb uses different ones across markets
                        widget_text = ""
                        for sel in [
                            '[data-testid="book-it-default"]',
                            '[data-section-id="BOOK_IT_SIDEBAR"]',
                            '[data-testid="bookItSection"]',
                        ]:
                            try:
                                loc = page.locator(sel).first
                                widget_text = loc.text_content(timeout=3000) or ""
                                if widget_text:
                                    break
                            except Exception:
                                continue
                        if widget_text:
                            m = re.search(
                                r'[Mm]inimum\s+stay\s+(?:is\s+)?(\d+)\s*nights?'
                                r'|(\d+)\s*(?:-\s*)?night\s*minimum',
                                widget_text, re.IGNORECASE
                            )
                            if m:
                                live_min = int(m.group(1) or m.group(2))
                                result["min_stay_detected"] = live_min
                                result["min_stay_not_met"] = True
                                result["is_available"] = True
                                print(f"    → {live_min}-night minimum (widget: '{widget_text.strip()[:60]}')")
                    except Exception:
                        pass  # widget not found — not a min stay issue

                if dates_unavailable:
                    result["is_available"] = False
                    result["dates_unavailable"] = True
                    print(f"    → BOOKED (dates blocked — no price rendered)")
                elif result.get("min_stay_not_met"):
                    pass  # handled above — extract_with_minstay_retry will retry
                else:
                    has_reserve = False
                    try:
                        has_reserve = page.evaluate("""() => {
                            const btn = document.querySelector('button[data-testid="homes-pdp-cta-btn"]');
                            // "Change dates" reuses this test-id — check text to confirm it's Reserve
                            if (btn && /Reserve|Request to book/i.test(btn.innerText || '')) return true;
                            const text = document.body.innerText;
                            return /Reserve|Request to book/i.test(text);
                        }""")
                    except Exception:
                        pass

                if not dates_unavailable and not result.get("min_stay_not_met") and has_reserve:
                    print(f"    → EXTRACTION FAILED (listing available but could not parse price)")
                    if body_text:
                        lines = body_text.split('\n')
                        dollar_lines = [l.strip() for l in lines if '$' in l and len(l.strip()) < 100]
                        if dollar_lines:
                            print(f"    → DEBUG $ lines: {dollar_lines[:3]}")
                        # Show context around the lone '$'
                        for idx, l in enumerate(lines):
                            if l.strip() in ('$', 'US$'):
                                ctx = lines[max(0, idx-2):idx+8]
                                print(f"    → DEBUG context: {[x.strip() for x in ctx if x.strip()]}")
                        # Dump all short non-empty lines to spot the price number
                        short_lines = [l.strip() for l in lines if 2 <= len(l.strip()) <= 30]
                        print(f"    → DEBUG all short lines: {short_lines[:40]}")
                    # Save screenshot so we can see what the page actually looks like
                    shot_path = f"debug_extract_{listing_id}.png"
                    try:
                        page.screenshot(path=shot_path, full_page=False)
                        print(f"    → Screenshot saved: {shot_path}")
                    except Exception as e:
                        print(f"    → Screenshot failed: {e}")
                elif not dates_unavailable and "add dates" in body_lower:
                    print(f"    → Dates didn't apply — page showing generic view")
                elif not dates_unavailable:
                    result["is_available"] = False
                    print(f"    → BOOKED (no Reserve button, no price found)")

        # ========================================
        # Extract rating and review count
        # ========================================
        if body_text:
            rating_match = re.search(r'(?:Rated\s+)?([\d.]+)\s+out\s+of\s+5', body_text)
            if rating_match:
                result["rating"] = float(rating_match.group(1))
            review_match = re.search(r'(\d+)\s+reviews?', body_text)
            if review_match:
                result["review_count"] = int(review_match.group(1))

        # ========================================
        # Sanity check: catch total-as-nightly
        # ========================================
        if result["nightly_rate"] and nights > 1:
            rate = result["nightly_rate"]
            total = result["total_price"]
            if total and rate > total:
                result["nightly_rate"] = round(total / nights)
                result["total_price"] = rate
                print(f"    (sanity: swapped → ${result['nightly_rate']}/night)")
            elif not total and rate > 800:
                per_night = rate / nights
                if 80 <= per_night <= 800:
                    result["total_price"] = rate
                    result["nightly_rate"] = round(per_night)
                    print(f"    (sanity: ${rate:.0f} → ${result['nightly_rate']}/night ÷ {nights}n)")

    except Exception as e:
        print(f"    → Error loading page: {e}")
        result["is_available"] = False

    return result


def extract_with_minstay_retry(page, listing_id, checkin_str, nights, conn=None):
    """
    Wrapper around extract_price_from_page that retries with longer stay
    if the listing has a minimum stay requirement above our search length.

    Returns the same result dict as extract_price_from_page, with the actual
    nights used reflected in result["nights"].
    """
    checkout_str = (datetime.strptime(checkin_str, "%Y-%m-%d") + timedelta(days=nights)).strftime("%Y-%m-%d")
    result = extract_price_from_page(page, listing_id, checkin_str, checkout_str)

    # Airbnb now shows "Those dates are not available" for min-stay violations instead
    # of explicit "X-night minimum" text.  When the first call came back with
    # dates_unavailable (not a real booking) and we don't have a min_stay_detected yet,
    # look up the known min_stay from the DB and treat it as a min-stay issue.
    if result["dates_unavailable"] and not result["min_stay_detected"] and not result["nightly_rate"] and conn:
        try:
            row = conn.execute(
                "SELECT min_stay FROM listings WHERE listing_id=?", (listing_id,)
            ).fetchone()
            known_min = row[0] if row and row[0] else None
        except Exception:
            known_min = None

        probe_nights = None
        if known_min and known_min > nights:
            probe_nights = known_min
            print(f"    → 'Those dates unavailable' — retrying with known min_stay={known_min}n...")
        # No blind 7n probe: the polling loop already checks for min-stay language on
        # every attempt, so reaching here with min_stay_detected=None means Airbnb
        # showed no min-stay text — treat as genuinely booked.

        if probe_nights and probe_nights > nights:
            probe_checkout = (datetime.strptime(checkin_str, "%Y-%m-%d") + timedelta(days=probe_nights)).strftime("%Y-%m-%d")
            time.sleep(random.uniform(8, 12))
            probe_result = extract_price_from_page(page, listing_id, checkin_str, probe_checkout)
            if probe_result["nightly_rate"]:
                result["nightly_rate"] = probe_result["nightly_rate"]
                result["total_price"] = probe_result["total_price"]
                result["is_available"] = True
                result["nights"] = probe_nights
                result["min_stay_detected"] = probe_nights
                result["min_stay_not_met"] = True
                result["rating"] = probe_result["rating"] or result["rating"]
                result["review_count"] = probe_result["review_count"] or result["review_count"]
                print(f"    → Confirmed min-stay={probe_nights}n: ${result['nightly_rate']}/night")
            else:
                # Probe also failed — genuinely booked, not a min-stay issue
                print(f"    → {probe_nights}n probe also blocked — listing is genuinely booked")

    # If we got a min_stay that's higher than our search, retry with the right length
    if result["min_stay_detected"] and result["min_stay_detected"] > nights and not result["nightly_rate"]:
        retry_nights = result["min_stay_detected"]
        retry_checkout = (datetime.strptime(checkin_str, "%Y-%m-%d") + timedelta(days=retry_nights)).strftime("%Y-%m-%d")

        print(f"    → Retrying with {retry_nights} nights (min stay requirement)...")
        time.sleep(random.uniform(8, 12))  # Longer delay — same listing twice is riskier

        retry_result = extract_price_from_page(page, listing_id, checkin_str, retry_checkout)

        if retry_result["nightly_rate"]:
            result["nightly_rate"] = retry_result["nightly_rate"]
            result["total_price"] = retry_result["total_price"]
            result["is_available"] = True
            result["nights"] = retry_nights
            result["rating"] = retry_result["rating"] or result["rating"]
            result["review_count"] = retry_result["review_count"] or result["review_count"]
            print(f"    → Got price at {retry_nights}n: ${result['nightly_rate']}/night")

    # Update min_stay on listing record if we detected one
    if result["min_stay_detected"] and conn:
        try:
            conn.execute("UPDATE listings SET min_stay=? WHERE listing_id=?",
                         (result["min_stay_detected"], listing_id))
            conn.commit()
        except Exception:
            pass  # Column might not exist yet in older DBs

    return result

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS listings (
        listing_id TEXT PRIMARY KEY, name TEXT, segment TEXT, tier INTEGER,
        url TEXT, rating REAL, review_count INTEGER, min_stay INTEGER,
        last_scraped TEXT, added_date TEXT DEFAULT CURRENT_TIMESTAMP)""")
    c.execute("""CREATE TABLE IF NOT EXISTS price_snapshots (
        id INTEGER PRIMARY KEY AUTOINCREMENT, listing_id TEXT, scrape_date TEXT,
        scrape_label TEXT, checkin_date TEXT, nights INTEGER, nightly_rate REAL,
        total_price REAL, is_available INTEGER DEFAULT 1, currency TEXT DEFAULT 'USD',
        FOREIGN KEY (listing_id) REFERENCES listings(listing_id))""")
    c.execute("""CREATE TABLE IF NOT EXISTS occupancy_checks (
        id INTEGER PRIMARY KEY AUTOINCREMENT, listing_id TEXT, check_date TEXT,
        is_booked INTEGER, scrape_date TEXT,
        FOREIGN KEY (listing_id) REFERENCES listings(listing_id))""")
    c.execute("""CREATE TABLE IF NOT EXISTS bali_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT, event_date TEXT NOT NULL,
        name TEXT NOT NULL, event_type TEXT, notes TEXT,
        UNIQUE(event_date, name))""")
    c.execute("""CREATE TABLE IF NOT EXISTS my_properties (
        id INTEGER PRIMARY KEY AUTOINCREMENT, property_id TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL, bedrooms INTEGER, airbnb_listing_id TEXT,
        location TEXT DEFAULT 'Berawa', notes TEXT,
        added_date TEXT DEFAULT CURRENT_TIMESTAMP)""")
    c.execute("""CREATE TABLE IF NOT EXISTS my_bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT, property_id TEXT NOT NULL,
        checkin TEXT NOT NULL, checkout TEXT NOT NULL, nightly_rate REAL,
        total_amount REAL, nights INTEGER, guest_name TEXT,
        platform TEXT DEFAULT 'airbnb', booking_date TEXT,
        status TEXT DEFAULT 'confirmed', notes TEXT,
        imported_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (property_id) REFERENCES my_properties(property_id))""")

    c.execute("""CREATE TABLE IF NOT EXISTS min_stay_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        listing_id TEXT NOT NULL,
        min_stay INTEGER NOT NULL,
        scrape_date TEXT NOT NULL,
        detection_method TEXT,
        UNIQUE(listing_id, scrape_date),
        FOREIGN KEY (listing_id) REFERENCES listings(listing_id))""")

    c.execute("CREATE INDEX IF NOT EXISTS idx_ps_lid ON price_snapshots(listing_id, scrape_date)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_oc_lid ON occupancy_checks(listing_id, check_date)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_msh_lid ON min_stay_history(listing_id, scrape_date)")
    # UNIQUE index: prevents duplicate (listing, date, label, checkin) rows
    c.execute("""CREATE UNIQUE INDEX IF NOT EXISTS idx_ps_unique
        ON price_snapshots(listing_id, scrape_date, scrape_label, checkin_date)""")

    # Migration: add min_stay column if missing (existing DBs from before this update)
    try:
        c.execute("SELECT min_stay FROM listings LIMIT 1")
    except sqlite3.OperationalError:
        c.execute("ALTER TABLE listings ADD COLUMN min_stay INTEGER")

    conn.commit()
    return conn


def seed_listings(conn):
    for comp in COMP_SET:
        # NOTE: tier is intentionally excluded from ON CONFLICT update to preserve
        # any manual tier edits made directly in the DB.
        conn.execute("""INSERT INTO listings (listing_id, name, segment, tier, url)
            VALUES (?, ?, ?, ?, ?) ON CONFLICT(listing_id) DO UPDATE SET
            name=excluded.name, segment=excluded.segment""",
            (comp["id"], comp["name"], comp["seg"], comp["tier"],
             f"https://www.airbnb.com/rooms/{comp['id']}"))
    conn.commit()


def seed_bali_events(conn):
    """Seed known Bali demand events. INSERT OR IGNORE — safe to run repeatedly."""
    events = [
        # Nyepi (Bali Day of Silence) — everything closes, no movement
        ("2026-03-28", "Nyepi Eve (Ogoh-Ogoh)", "cultural", "Parade night before Nyepi — high demand"),
        ("2026-03-29", "Nyepi 2026", "cultural", "Bali Day of Silence — airport closed, no movement allowed"),
        # Galungan / Kuningan
        ("2026-04-08", "Galungan 2026", "cultural", "Hindu celebration — local high demand"),
        ("2026-04-18", "Kuningan 2026", "cultural", "End of Galungan period"),
        # Australian school holidays (major demand driver for Bali)
        ("2026-04-06", "Aus School Hols Start (Apr)", "demand", "Australian Easter school holidays begin"),
        ("2026-04-19", "Aus School Hols End (Apr)", "demand", "Australian Easter school holidays end"),
        ("2026-07-04", "Aus School Hols Start (Jul)", "demand", "Australian winter school holidays begin"),
        ("2026-07-19", "Aus School Hols End (Jul)", "demand", "Australian winter school holidays end"),
        ("2026-09-19", "Aus School Hols Start (Sep)", "demand", "Australian spring school holidays begin"),
        ("2026-10-04", "Aus School Hols End (Sep)", "demand", "Australian spring school holidays end"),
        ("2026-12-19", "Aus School Hols Start (Dec)", "demand", "Australian summer school holidays begin"),
        ("2027-01-28", "Aus School Hols End (Dec)", "demand", "Australian summer school holidays end"),
        # Christmas / NYE peak
        ("2026-12-24", "Christmas Eve", "peak", "Christmas / NYE peak period begins"),
        ("2026-12-25", "Christmas Day", "peak", None),
        ("2026-12-31", "New Year's Eve 2026", "peak", "Highest demand night of year"),
        ("2027-01-01", "New Year's Day 2027", "peak", None),
        # Indonesian national holidays that affect domestic travel
        ("2026-08-17", "Indonesian Independence Day", "national", "Indonesian long weekend"),
    ]
    for event_date, name, event_type, notes in events:
        conn.execute("""INSERT OR IGNORE INTO bali_events (event_date, name, event_type, notes)
            VALUES (?, ?, ?, ?)""", (event_date, name, event_type, notes))
    conn.commit()
    inserted = conn.execute("SELECT COUNT(*) FROM bali_events").fetchone()[0]
    print(f"  Bali events seeded: {inserted} total in DB")


def save_price(conn, listing_id, label, checkin, nights, nightly_rate, total_price=None, is_available=True):
    # INSERT OR REPLACE enforces idempotency via idx_ps_unique.
    # Re-running a scrape for the same (listing, date, label, checkin) overwrites
    # the previous value rather than creating a duplicate row.
    conn.execute("""INSERT OR REPLACE INTO price_snapshots
        (listing_id, scrape_date, scrape_label, checkin_date, nights, nightly_rate, total_price, is_available)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (listing_id, date.today().isoformat(), label, checkin, nights,
         nightly_rate, total_price, 1 if is_available else 0))
    conn.commit()


def update_meta(conn, listing_id, rating=None, review_count=None):
    updates, params = [], []
    if rating: updates.append("rating=?"); params.append(rating)
    if review_count: updates.append("review_count=?"); params.append(review_count)
    updates.append("last_scraped=?"); params.append(datetime.now().strftime("%Y-%m-%d %H:%M"))
    params.append(listing_id)
    if updates:
        conn.execute(f"UPDATE listings SET {','.join(updates)} WHERE listing_id=?", params)
        conn.commit()


# ============================================================
# TEST MODE — Run this first to verify extraction works
# ============================================================

def run_test(listing_id):
    """Test scraping a single listing with verbose output."""
    print(f"\n{'='*60}")
    print(f"TEST SCRAPE — Listing {listing_id}")
    print(f"{'='*60}\n")

    comp = next((c for c in COMP_SET if c["id"] == listing_id), None)
    if comp:
        print(f"Name: {comp['name']}")
        print(f"Segment: {comp['seg']} | Tier: {comp['tier']}")
    else:
        print(f"(Not in comp set — scraping anyway)")

    pw, browser, context = create_browser()
    page = context.new_page()

    # Test 1: Load without dates (should get rating/reviews but no price)
    print(f"\n--- Test 1: No dates (expect rating + reviews, no price) ---")
    url_no_dates = f"https://www.airbnb.com/rooms/{listing_id}"
    try:
        page.goto(url_no_dates, wait_until="domcontentloaded", timeout=45000)
        time.sleep(5)
        body = page.inner_text("body")

        # Save first 500 chars for debugging
        print(f"\nPage title: {page.title()}")
        print(f"Body text preview (first 500 chars):")
        print(body[:500])
        print("...")

        # Check for rating
        rating_match = re.search(r'(?:Rated\s+)?([\d.]+)\s+out\s+of\s+5', body)
        review_match = re.search(r'(\d+)\s+reviews?', body)
        print(f"\nRating found: {rating_match.group(1) if rating_match else 'NO'}")
        print(f"Reviews found: {review_match.group(1) if review_match else 'NO'}")

        # Check for any dollar amounts
        prices = re.findall(r'\$\s*([\d,]+)', body)
        print(f"Dollar amounts on page: {prices[:10]}")

    except Exception as e:
        print(f"Error: {e}")

    time.sleep(3)

    # Test 2: Load WITH dates (should get price)
    today = date.today()
    checkin = today + timedelta(days=14)
    # Adjust to Tuesday
    while checkin.weekday() != 1:
        checkin += timedelta(days=1)
    checkout = checkin + timedelta(days=3)

    print(f"\n--- Test 2: With dates {checkin} to {checkout} ({(checkout-checkin).days} nights) ---")

    # First, let's see ALL dollar amounts on the page for debugging
    url_with_dates = f"https://www.airbnb.com/rooms/{listing_id}?check_in={checkin}&check_out={checkout}&adults=2&currency=USD"
    try:
        page.goto(url_with_dates, wait_until="domcontentloaded", timeout=45000)
        time.sleep(6)
        body = page.inner_text("body")

        # Show all dollar amounts found
        all_dollar = re.findall(r'\$\s*[\d,]+', body)
        print(f"\nAll dollar amounts on page: {all_dollar[:15]}")

        # Show text around "night" keyword
        night_idx = body.lower().find("night")
        if night_idx >= 0:
            snippet = body[max(0, night_idx-40):night_idx+40]
            print(f"Text around 'night': ...{snippet}...")

        # Show text around "total"
        total_idx = body.lower().find("total")
        if total_idx >= 0:
            snippet = body[max(0, total_idx-40):total_idx+40]
            print(f"Text around 'total': ...{snippet}...")

    except Exception as e:
        print(f"Debug page load error: {e}")

    # Now run the actual extraction
    result = extract_price_from_page(page, listing_id, checkin.isoformat(), checkout.isoformat())

    print(f"\nResults:")
    print(f"  Nightly rate: {'$' + str(result['nightly_rate']) if result['nightly_rate'] else 'NOT FOUND'}")
    print(f"  Total price: {'$' + str(result['total_price']) if result['total_price'] else 'N/A'}")
    print(f"  Available: {result['is_available']}")
    print(f"  Min stay: {result['min_stay_detected'] or 'not detected'}")
    print(f"  Rating: {result['rating']}")
    print(f"  Reviews: {result['review_count']}")

    # Test 3: Try weekend dates
    time.sleep(3)
    fri = checkin + timedelta(days=3)  # Friday after the Tuesday
    while fri.weekday() != 4:
        fri += timedelta(days=1)
    fri_out = fri + timedelta(days=3)

    print(f"\n--- Test 3: Weekend {fri} to {fri_out} (compare price) ---")
    result_wkend = extract_price_from_page(page, listing_id, fri.isoformat(), fri_out.isoformat())
    print(f"  Weekend rate: {'$' + str(result_wkend['nightly_rate']) if result_wkend['nightly_rate'] else 'NOT FOUND'}")

    if result['nightly_rate'] and result_wkend['nightly_rate']:
        spread = round((result_wkend['nightly_rate'] - result['nightly_rate']) / result['nightly_rate'] * 100)
        print(f"  Weekend premium: {'+' if spread >= 0 else ''}{spread}%")

    # Save a screenshot for debugging
    screenshot_path = Path(__file__).parent / f"debug_screenshot_{listing_id}.png"
    page.screenshot(path=str(screenshot_path), full_page=False)
    print(f"\nScreenshot saved: {screenshot_path}")

    browser.close()
    pw.stop()

    print(f"\n{'='*60}")
    if result['nightly_rate']:
        print("SUCCESS — Price extraction is working!")
        print(f"You can now run: python3 scraper_v2.py daily")
    else:
        print("PRICE NOT FOUND — Check the screenshot to see what Airbnb showed.")
        print("Possible issues:")
        print("  1. Airbnb is showing a CAPTCHA or bot detection page")
        print("  2. Listing is unavailable for the dates tested")
        print("  3. Page structure has changed (need to update extraction patterns)")
        print(f"\nOpen {screenshot_path} to see what the page looks like.")
    print(f"{'='*60}\n")


# ============================================================
# SCRAPE HEALTH + PRICE ALERTS
# ============================================================

def print_scrape_health(success, booked, fail):
    """Print a scrape health summary. Warns if >20% true failure rate.

    Args:
        success: price successfully extracted
        booked:  listing confirmed booked (is_available=False) — scraper worked, just no price
        fail:    scraper could not determine price or status (CAPTCHA, extraction failure)
    """
    total = success + booked + fail
    if total == 0:
        print("\n  SCRAPE HEALTH: no data (0 attempts)")
        return
    fail_pct = fail / total * 100
    status = "WARNING" if fail_pct > 20 else "OK"
    print(f"\n{'='*60}")
    print(f"SCRAPE HEALTH — {date.today()}")
    print(f"{'='*60}")
    print(f"  Price found: {success}/{total} ({round(success/total*100)}%)")
    print(f"  Booked:      {booked}/{total} ({round(booked/total*100)}%) — scraper OK, listing unavailable")
    print(f"  Failed:      {fail}/{total} ({round(fail_pct)}%) — could not determine price or status")
    if fail_pct > 20:
        print(f"  WARNING: {round(fail_pct)}% true failure rate exceeds 20% threshold.")
        print(f"  Possible causes: CAPTCHA, IP block, Airbnb layout change.")
        print(f"  Run 'python3 scraper.py test 7816774' to diagnose.")
    else:
        print(f"  Status: {status}")
    print(f"{'='*60}")


def run_price_alerts(conn):
    """
    Detect significant price changes and dark listings since last week.

    Methodology:
    - Rolling 3-day average per label (weekday/weekend) to smooth noise
    - Compare today's average vs 3-7 days ago average for the SAME label
    - Alert if >15% change
    - Dark listing: comp not seen with is_available=1 in >7 days but not
      showing as consistently booked (gap > 7 days in scrape_date)
    - Guard: skips if fewer than 4 days of baseline data
    """
    c = conn.cursor()
    today = date.today()
    today_str = today.isoformat()

    # Guard: need at least 4 days of data to compare
    days_of_data = c.execute(
        "SELECT COUNT(DISTINCT scrape_date) FROM price_snapshots WHERE scrape_label IN (?, ?)",
        (LABEL_WEEKDAY, LABEL_WEEKEND)
    ).fetchone()[0]
    if days_of_data < 4:
        print(f"\n  Price alerts: skipped (only {days_of_data} days of data — need 4+)")
        return

    print(f"\n{'='*60}")
    print(f"PRICE CHANGE ALERTS — {today_str}")
    print(f"{'='*60}")

    alerts = []

    for label in [LABEL_WEEKDAY, LABEL_WEEKEND]:
        # Get all listings that have data today
        c.execute("""SELECT DISTINCT listing_id FROM price_snapshots
            WHERE scrape_date = ? AND scrape_label = ? AND nightly_rate IS NOT NULL""",
            (today_str, label))
        listing_ids = [r[0] for r in c.fetchall()]

        for lid in listing_ids:
            # Today's rate
            c.execute("""SELECT AVG(nightly_rate) FROM price_snapshots
                WHERE listing_id = ? AND scrape_date = ? AND scrape_label = ?
                AND nightly_rate IS NOT NULL""", (lid, today_str, label))
            today_avg = c.fetchone()[0]
            if not today_avg:
                continue

            # Rolling 3-day average from 3-7 days ago (same label)
            cutoff_start = (today - timedelta(days=7)).isoformat()
            cutoff_end   = (today - timedelta(days=3)).isoformat()
            c.execute("""SELECT AVG(nightly_rate) FROM price_snapshots
                WHERE listing_id = ? AND scrape_label = ?
                AND scrape_date BETWEEN ? AND ?
                AND nightly_rate IS NOT NULL""",
                (lid, label, cutoff_start, cutoff_end))
            baseline_avg = c.fetchone()[0]
            if not baseline_avg:
                continue

            pct_change = (today_avg - baseline_avg) / baseline_avg * 100
            if abs(pct_change) >= 15:
                c.execute("SELECT name FROM listings WHERE listing_id = ?", (lid,))
                name = (c.fetchone() or ["?"])[0]
                direction = "▲" if pct_change > 0 else "▼"
                alerts.append({
                    "name": name, "label": label,
                    "today": round(today_avg), "baseline": round(baseline_avg),
                    "pct": round(pct_change), "direction": direction
                })

    # Dark listing detection: listings with no conclusive scrape result in >7 days.
    # "Conclusive" = either a price was found OR the listing was confirmed booked
    # (is_available=0). Rows with nightly_rate=NULL and is_available=1 are true
    # scrape failures and do NOT count — so a listing hitting CAPTCHA every day
    # still shows as dark.
    cutoff_dark = (today - timedelta(days=7)).isoformat()
    c.execute("""SELECT l.listing_id, l.name, l.segment, l.tier,
            MAX(p.scrape_date) as last_seen
        FROM listings l
        LEFT JOIN price_snapshots p ON l.listing_id = p.listing_id
            AND p.scrape_label IN (?, ?)
            AND (p.nightly_rate IS NOT NULL OR p.is_available = 0)
        WHERE l.segment IN ({})
        GROUP BY l.listing_id
        HAVING last_seen IS NULL OR last_seen < ?
        ORDER BY l.tier, l.name""".format(
            ",".join("?" * len(ACTIVE_SEGMENTS))),
        [LABEL_WEEKDAY, LABEL_WEEKEND] + ACTIVE_SEGMENTS + [cutoff_dark])
    dark_listings = c.fetchall()

    # Report
    if alerts:
        print(f"\n  PRICE CHANGES (≥15% vs 3-7d rolling avg):")
        print(f"  {'Name':<35} {'Label':<8} {'Today':>8} {'Baseline':>10} {'Change':>8}")
        print(f"  {'-'*72}")
        for a in sorted(alerts, key=lambda x: abs(x["pct"]), reverse=True):
            print(f"  {a['name']:<35} {a['label']:<8} ${a['today']:>7} "
                  f"${a['baseline']:>9} {a['direction']}{abs(a['pct'])}%")
    else:
        print(f"\n  No significant price changes (all within ±15%)")

    if dark_listings:
        print(f"\n  DARK LISTINGS (no successful scrape in >7 days):")
        for lid, name, seg, tier, last_seen in dark_listings:
            last_str = last_seen or "never"
            print(f"  T{tier} {seg}: {name} — last seen: {last_str}")
        print(f"  → Possible renovation, delisting, or scrape failure.")
    else:
        print(f"\n  No dark listings detected.")

    print(f"{'='*60}")


# ============================================================
# CONFIRM & PUSH
# ============================================================

def confirm_and_push(today, mode_label):
    """Print scrape summary, ask for confirmation, then push to git or rollback."""
    conn = sqlite3.connect(DB_PATH)

    ps_count = conn.execute(
        "SELECT COUNT(*) FROM price_snapshots WHERE scrape_date=?", (today,)
    ).fetchone()[0]
    oc_count = conn.execute(
        "SELECT COUNT(*) FROM occupancy_checks WHERE scrape_date=?", (today,)
    ).fetchone()[0]
    ms_count = conn.execute(
        "SELECT COUNT(*) FROM min_stay_history WHERE scrape_date=?", (today,)
    ).fetchone()[0]

    print(f"\n{'='*60}")
    print(f"SCRAPE COMPLETE — {today} ({mode_label})")
    print(f"  Price snapshots today:  {ps_count}")
    if oc_count:
        print(f"  Occupancy checks today: {oc_count}")
    if ms_count:
        print(f"  Min-stay records today: {ms_count}")
    print(f"{'='*60}")

    answer = input("\nResults look good? Push to Vercel? (y/n): ").strip().lower()

    if answer == "y":
        conn.close()
        print("\nPushing to Vercel...")
        subprocess.run(["git", "add", "comp_data.db"], check=True)
        commit = subprocess.run(
            ["git", "commit", "-m", f"{mode_label} scrape snapshot — {today}"],
            capture_output=True, text=True,
        )
        if commit.returncode != 0:
            print(commit.stdout.strip() or commit.stderr.strip())
        else:
            push = subprocess.run(["git", "push"], capture_output=True, text=True)
            if push.returncode != 0:
                print(f"Push failed: {push.stderr.strip()}")
            else:
                print("Pushed. Vercel will redeploy in ~60 seconds.")
    else:
        print("\nRolling back today's data...")
        conn.execute("DELETE FROM price_snapshots WHERE scrape_date=?", (today,))
        conn.execute("DELETE FROM occupancy_checks WHERE scrape_date=?", (today,))
        conn.execute("DELETE FROM min_stay_history WHERE scrape_date=?", (today,))
        conn.commit()
        conn.close()
        print("Done. DB unchanged.")


# ============================================================
# DAILY SCRAPE
# ============================================================

def get_daily_dates():
    today = date.today()
    base = today + timedelta(days=14)
    # Find next Tuesday and Friday
    tue = base + timedelta(days=(1 - base.weekday()) % 7)
    fri = base + timedelta(days=(4 - base.weekday()) % 7)
    if fri <= tue:
        fri += timedelta(days=7)
    return {
        "weekday": (tue.isoformat(), (tue + timedelta(days=3)).isoformat(), 3),
        "weekend": (fri.isoformat(), (fri + timedelta(days=3)).isoformat(), 3),
    }


def run_daily(_limit=None, _override=None, skip_confirm=False):
    conn = init_db()
    seed_listings(conn)
    seed_bali_events(conn)
    dates = get_daily_dates()

    pw, browser, context = create_browser()
    page = context.new_page()

    all_comps = active_comps(limit=_limit, override=_override)
    total = len(all_comps)
    print(f"\n{'='*60}")
    print(f"DAILY SCRAPE — {date.today()}")
    print(f"{'='*60}")
    print(f"Segments: {', '.join(ACTIVE_SEGMENTS)}")
    print(f"Listings: {total}")
    print(f"Weekday: {dates['weekday'][0]} to {dates['weekday'][1]}")
    print(f"Weekend: {dates['weekend'][0]} to {dates['weekend'][1]}")
    print(f"{'='*60}\n")

    success = 0
    booked = 0
    fail = 0

    for i, comp in enumerate(all_comps, 1):
        print(f"[{i}/{total}] {comp['name']} (T{comp['tier']} {comp['seg']})")

        for label, (checkin, checkout, nights) in dates.items():
            result = extract_with_minstay_retry(page, comp["id"], checkin, nights, conn)

            # Fallback when extraction fails but listing appears available (not booked, no min-stay hit).
            # Strategy is label-aware to avoid saving a weekday rate under the weekend label:
            #   weekday: shift checkin ±2/+4 days, keep same night count
            #   weekend: try shorter stays anchored to the same Friday (Fri→Sun, Sat→Mon)
            if not result["nightly_rate"] and result["is_available"] and not result["min_stay_detected"]:
                if label == LABEL_WEEKEND:
                    fri = datetime.strptime(checkin, "%Y-%m-%d")
                    fallbacks = [
                        (fri.strftime("%Y-%m-%d"), 2),                              # Fri→Sun
                        ((fri + timedelta(days=1)).strftime("%Y-%m-%d"), 2),        # Sat→Mon
                    ]
                    for alt_ci, alt_nights in fallbacks:
                        time.sleep(random.uniform(1, 3))
                        result = extract_with_minstay_retry(page, comp["id"], alt_ci, alt_nights, conn)
                        if result["nightly_rate"]:
                            checkin = alt_ci
                            nights = alt_nights
                            break
                else:
                    # Only fallback is Monday (-1 day): Mon→Thu, all weekday nights,
                    # still ~2 weeks out. No further fallbacks — a wrong lead time
                    # is worse than a missing data point.
                    for offset in [-1]:
                        alt_ci = (datetime.strptime(checkin, "%Y-%m-%d") + timedelta(days=offset)).strftime("%Y-%m-%d")
                        time.sleep(random.uniform(1, 3))
                        result = extract_with_minstay_retry(page, comp["id"], alt_ci, nights, conn)
                        if result["nightly_rate"]:
                            checkin = alt_ci
                            break

            actual_nights = result.get("nights", nights)
            save_price(conn, comp["id"], label, checkin, actual_nights,
                       result["nightly_rate"], result["total_price"], result["is_available"])

            if result["nightly_rate"]:
                print(f"    {label}: ${result['nightly_rate']:.0f}/night")
                success += 1
            elif not result["is_available"]:
                print(f"    {label}: BOOKED")
                booked += 1
            else:
                print(f"    {label}: SCRAPE FAIL")
                fail += 1

            # Update metadata if found
            if result["rating"]:
                update_meta(conn, comp["id"], result["rating"], result["review_count"])

            time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))

        time.sleep(random.uniform(1, 3))

    # Run occupancy check using the same browser session
    run_daily_occupancy(page, conn)

    browser.close()
    pw.stop()

    # Scrape health summary + price change alerts
    print_scrape_health(success, booked, fail)
    run_price_alerts(conn)

    conn.close()
    if not skip_confirm:
        confirm_and_push(date.today().isoformat(), "daily")


# ============================================================
# DAILY OCCUPANCY CHECK (runs as part of daily)
# ============================================================

def run_daily_occupancy(page, conn):
    """Check if T1 comps are booked for tomorrow. Builds backward-looking occupancy over time.

    Uses known min_stay from listing record when available to avoid false
    positives (1-night search on a 3-night-minimum listing = 'unavailable').
    """
    t1_comps = active_comps(tier_filter=[1])
    tomorrow = date.today() + timedelta(days=1)
    tomorrow_str = tomorrow.isoformat()

    print(f"\n--- OCCUPANCY CHECK: {tomorrow_str} ({len(t1_comps)} T1 comps) ---\n")

    # Load known min_stays from DB
    cursor = conn.cursor()
    min_stays = {}
    for comp in t1_comps:
        cursor.execute("SELECT min_stay FROM listings WHERE listing_id=?", (comp["id"],))
        row = cursor.fetchone()
        if row and row[0]:
            min_stays[comp["id"]] = row[0]

    booked = 0
    available = 0

    for i, comp in enumerate(t1_comps, 1):
        # Use known min_stay if available, otherwise default to 1 night
        stay_nights = min_stays.get(comp["id"], 1)
        checkout = tomorrow + timedelta(days=stay_nights)
        checkout_str = checkout.isoformat()

        url = f"https://www.airbnb.com/rooms/{comp['id']}?check_in={tomorrow_str}&check_out={checkout_str}&adults=2&currency=USD"

        try:
            page.goto(url, wait_until="domcontentloaded", timeout=30000)

            # Dismiss popups
            time.sleep(1)
            try:
                close_btns = page.query_selector_all('button[aria-label="Close"], div[role="dialog"] button')
                for btn in close_btns:
                    if btn.is_visible():
                        btn.click()
                        time.sleep(0.5)
                        break
            except Exception:
                pass

            time.sleep(1.5)
            body = page.inner_text("body")

            # Check for min-stay message — if we didn't know this comp's min stay,
            # record it and retry with correct length
            min_stay_match = re.search(r'(?:(\d+)\s*(?:-\s*)?night\s*minimum|[Mm]inimum\s+stay\s+(?:is\s+)?(\d+)\s*nights?)', body, re.IGNORECASE)
            if min_stay_match and comp["id"] not in min_stays:
                detected_min = int(min_stay_match.group(1) or min_stay_match.group(2))
                # Save to DB for future runs
                try:
                    conn.execute("UPDATE listings SET min_stay=? WHERE listing_id=?",
                                 (detected_min, comp["id"]))
                    conn.commit()
                except Exception:
                    pass
                # Retry with correct length
                retry_co = (tomorrow + timedelta(days=detected_min)).isoformat()
                retry_url = f"https://www.airbnb.com/rooms/{comp['id']}?check_in={tomorrow_str}&check_out={retry_co}&adults=2&currency=USD"
                print(f"  [{i}/{len(t1_comps)}] {comp['name']}: {detected_min}n minimum detected, retrying...")
                time.sleep(random.uniform(6, 10))
                page.goto(retry_url, wait_until="domcontentloaded", timeout=30000)
                time.sleep(2)
                body = page.inner_text("body")

            is_booked = ("unavailable" in body.lower() or
                         "not available" in body.lower() or
                         "already booked" in body.lower())

            # Double-check: if unavailable but min-stay message present and
            # we STILL haven't retried with enough nights, mark as unknown
            if is_booked and min_stay_match:
                detected_min = int(min_stay_match.group(1) or min_stay_match.group(2))
                if stay_nights < detected_min:
                    # Our search was too short — this isn't a real booking
                    print(f"  [{i}/{len(t1_comps)}] {comp['name']}: SKIP (min stay {detected_min}n > search {stay_nights}n)")
                    time.sleep(random.uniform(1.5, 3))
                    continue

            # Save to DB
            conn.execute("""INSERT INTO occupancy_checks
                (listing_id, check_date, is_booked, scrape_date)
                VALUES (?, ?, ?, ?)""",
                (comp["id"], tomorrow_str, 1 if is_booked else 0, date.today().isoformat()))

            status = "BOOKED" if is_booked else "available"
            if is_booked:
                booked += 1
            else:
                available += 1
            print(f"  [{i}/{len(t1_comps)}] {comp['name']}: {status}")

        except Exception as e:
            print(f"  [{i}/{len(t1_comps)}] {comp['name']}: ERROR ({e})")

        time.sleep(random.uniform(1.5, 3))

    conn.commit()
    total = booked + available
    if total > 0:
        print(f"\n  T1 occupancy for {tomorrow_str}: {booked}/{total} booked ({round(booked/total*100)}%)")


# ============================================================
# DISCOUNTS MODE — Reverse-engineer comp discount structures
# ============================================================

def run_discounts(_limit=None, _override=None, skip_confirm=False):
    """
    For T1+T2 comps, check 3-night, 7-night, and 28-night rates
    starting on the same Tuesday ~3 weeks out.
    Same start date isolates the length-of-stay variable.
    """
    conn = init_db()
    seed_listings(conn)

    # Find Tuesday ~3 weeks out
    base = date.today() + timedelta(days=21)
    tue = base + timedelta(days=(1 - base.weekday()) % 7)

    stays = [
        (LABEL_3N_BASELINE, 3),
        (LABEL_7N_WEEKLY, 7),
        (LABEL_28N_MONTHLY, 28),
    ]

    t1_t2 = active_comps(tier_filter=[1, 2], limit=_limit, override=_override)

    pw, browser, context = create_browser()
    page = context.new_page()

    print(f"\n{'='*60}")
    print(f"DISCOUNT ANALYSIS — {date.today()}")
    print(f"{'='*60}")
    print(f"Check-in: {tue} (same for all lengths)")
    print(f"Lengths: 3n, 7n, 28n")
    print(f"Comps: {len(t1_t2)} (T1 + T2, segments: {', '.join(ACTIVE_SEGMENTS)})")
    print(f"Total requests: ~{len(t1_t2) * 3}")
    print(f"{'='*60}\n")

    results_summary = []

    for i, comp in enumerate(t1_t2, 1):
        print(f"[{i}/{len(t1_t2)}] {comp['name']} (T{comp['tier']} {comp['seg']})")
        comp_rates = {}

        # SMART SKIP: Check 3-night baseline first. If booked, skip 7n and 28n.
        # Uses retry wrapper — if 3n doesn't meet min stay, retries at min stay length.
        baseline_label, baseline_nights = stays[0]  # 3n_baseline
        checkin = tue.isoformat()

        result = extract_with_minstay_retry(page, comp["id"], checkin, baseline_nights, conn)
        actual_nights = result.get("nights", baseline_nights)
        save_price(conn, comp["id"], baseline_label, checkin, actual_nights,
                   result["nightly_rate"], result["total_price"], result["is_available"])

        if not result["nightly_rate"]:
            status = "BOOKED" if not result["is_available"] else "SCRAPE FAIL"
            print(f"    {baseline_label}: {status} — skipping longer stays")
            time.sleep(random.uniform(1, 3))
            continue

        comp_rates[baseline_label] = result["nightly_rate"]
        actual_note = f" (retried at {actual_nights}n)" if actual_nights != baseline_nights else ""
        print(f"    {baseline_label} ({actual_nights}n): ${result['nightly_rate']:.0f}/night (baseline){actual_note}")

        # Check remaining stay lengths
        for label, nights in stays[1:]:  # Skip baseline, check 7n and 28n
            checkin = tue.isoformat()

            time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))
            result = extract_with_minstay_retry(page, comp["id"], checkin, nights, conn)
            actual_nights_inner = result.get("nights", nights)

            save_price(conn, comp["id"], label, checkin, actual_nights_inner,
                       result["nightly_rate"], result["total_price"], result["is_available"])

            if result["nightly_rate"]:
                comp_rates[label] = result["nightly_rate"]
                print(f"    {label} ({actual_nights_inner}n): ${result['nightly_rate']:.0f}/night")
            else:
                status = "BOOKED" if not result["is_available"] else "SCRAPE FAIL"
                print(f"    {label} ({nights}n): {status}")

            time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))

        # Calculate discounts for this comp
        if "3n_baseline" in comp_rates:
            base_rate = comp_rates["3n_baseline"]
            weekly_rate = comp_rates.get("7n_weekly")
            monthly_rate = comp_rates.get("28n_monthly")

            weekly_disc = round((1 - weekly_rate / base_rate) * 100) if weekly_rate else None
            monthly_disc = round((1 - monthly_rate / base_rate) * 100) if monthly_rate else None

            disc_str = f"  → Weekly: {weekly_disc}% off" if weekly_disc is not None else ""
            disc_str += f" | Monthly: {monthly_disc}% off" if monthly_disc is not None else ""
            if disc_str:
                print(disc_str)

            results_summary.append({
                "name": comp["name"], "seg": comp["seg"], "tier": comp["tier"],
                "base": base_rate, "weekly": weekly_rate, "monthly": monthly_rate,
                "weekly_disc": weekly_disc, "monthly_disc": monthly_disc,
            })

        time.sleep(random.uniform(1, 3))

    browser.close()
    pw.stop()

    # Print summary
    print(f"\n{'='*60}")
    print(f"DISCOUNT SUMMARY")
    print(f"{'='*60}\n")

    for seg in ["3bed", "4bed", "6bed"]:
        seg_results = [r for r in results_summary if r["seg"] == seg]
        if not seg_results:
            continue

        print(f"--- {seg.upper()} ---")
        weekly_discs = [r["weekly_disc"] for r in seg_results if r["weekly_disc"] is not None]
        monthly_discs = [r["monthly_disc"] for r in seg_results if r["monthly_disc"] is not None]

        if weekly_discs:
            print(f"  Weekly discount:  avg {round(sum(weekly_discs)/len(weekly_discs))}% "
                  f"(range {min(weekly_discs)}–{max(weekly_discs)}%) "
                  f"[{len(weekly_discs)} comps with data]")
        if monthly_discs:
            print(f"  Monthly discount: avg {round(sum(monthly_discs)/len(monthly_discs))}% "
                  f"(range {min(monthly_discs)}–{max(monthly_discs)}%) "
                  f"[{len(monthly_discs)} comps with data]")
        else:
            print(f"  Monthly discount: insufficient data (most comps booked for 28n)")
        print()

    conn.close()
    if not skip_confirm:
        confirm_and_push(date.today().isoformat(), "discounts")


# ============================================================
# MINSTAY AUDIT MODE — Discover and track minimum stay requirements
# ============================================================

def run_minstay_audit(_override=None, skip_confirm=False):
    """
    For every active comp, discover the current minimum stay requirement
    and record it longitudinally in min_stay_history.

    Detection strategy (per listing):
      1. Load a 1-night search. If Airbnb renders explicit min-stay text
         ("3-night minimum"), we have the answer immediately — method="text".
         If a price is returned, min_stay=1.
      2. If unavailable with no text, probe [2,3,4,5,7] nights until a
         length either gets a price or shows min-stay text — method="probe".

    Also keeps listings.min_stay up to date as a convenience cache for the
    occupancy check (which uses it to avoid false "booked" results on short searches).

    Usage:
        python3 scraper.py minstay
    """
    conn = init_db()
    seed_listings(conn)

    all_comps = active_comps(override=_override)
    total = len(all_comps)
    today = date.today().isoformat()

    # Next Tuesday from tomorrow — soon enough to reflect current min_stay settings
    base = date.today() + timedelta(days=1)
    checkin_date = base + timedelta(days=(1 - base.weekday()) % 7)
    checkin = checkin_date.isoformat()

    print(f"\n{'='*60}")
    print(f"MINSTAY AUDIT — {today}")
    print(f"{'='*60}")
    print(f"Segments: {', '.join(ACTIVE_SEGMENTS)}")
    print(f"Listings: {total}")
    print(f"Probe check-in: {checkin} (Tue, ~4 weeks out)")
    print(f"{'='*60}\n")

    pw, browser, context = create_browser()
    page = context.new_page()

    confirmed = 0
    unknown = 0
    changed = 0
    summary_rows = []

    # Load previous min_stay values for change detection
    prev_min_stays = {
        row[0]: row[1]
        for row in conn.execute("SELECT listing_id, min_stay FROM listings")
    }

    for i, comp in enumerate(all_comps, 1):
        print(f"[{i}/{total}] {comp['name']} (T{comp['tier']} {comp['seg']})")

        detected_min = None
        method = None

        # Step 1: 1-night probe
        checkout_1n = (checkin_date + timedelta(days=1)).isoformat()
        result = extract_price_from_page(page, comp["id"], checkin, checkout_1n)

        if result.get("_captcha"):
            print(f"    → CAPTCHA — skipping")
            unknown += 1
            summary_rows.append((comp["name"], prev_min_stays.get(comp["id"]), None, "captcha"))
            time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))
            continue
        elif result["nightly_rate"]:
            detected_min = 1
            method = "text"
            print(f"    → min_stay=1 (price found on 1n)")
        elif result["min_stay_detected"]:
            detected_min = result["min_stay_detected"]
            method = "text"
            print(f"    → min_stay={detected_min} (explicit text, 1n probe)")
        else:
            # Step 2: probe longer lengths on the same checkin date.
            # When min_stay text isn't shown, the first length that returns a
            # price tells us the minimum. Break immediately on text or price.
            for probe_nights in [2, 3, 4, 5, 7]:
                time.sleep(random.uniform(5, 8))
                probe_checkout = (checkin_date + timedelta(days=probe_nights)).isoformat()
                probe_result = extract_price_from_page(page, comp["id"], checkin, probe_checkout)

                if probe_result.get("_captcha"):
                    print(f"    → CAPTCHA on {probe_nights}n probe — bailing")
                    break
                elif probe_result["min_stay_detected"]:
                    detected_min = probe_result["min_stay_detected"]
                    method = "probe"
                    print(f"    → min_stay={detected_min} (explicit text, {probe_nights}n probe)")
                    break
                elif probe_result["nightly_rate"]:
                    detected_min = probe_nights
                    method = "probe"
                    print(f"    → min_stay={probe_nights} (price found on {probe_nights}n probe)")
                    break

            # Step 3: if the original date appears genuinely booked across all
            # lengths, try two alternative Tuesdays. A different week sidesteps
            # the booking and will still show min_stay text if a requirement exists.
            if detected_min is None:
                for week_offset in [7, 14]:
                    probe_ci_date = checkin_date + timedelta(days=week_offset)
                    probe_ci = probe_ci_date.isoformat()
                    probe_co = (probe_ci_date + timedelta(days=1)).isoformat()
                    time.sleep(random.uniform(5, 8))
                    probe_result = extract_price_from_page(page, comp["id"], probe_ci, probe_co)

                    if probe_result.get("_captcha"):
                        print(f"    → CAPTCHA on +{week_offset}d probe — bailing")
                        break
                    elif probe_result["min_stay_detected"]:
                        detected_min = probe_result["min_stay_detected"]
                        method = "probe"
                        print(f"    → min_stay={detected_min} (explicit text, +{week_offset}d probe)")
                        break
                    elif probe_result["nightly_rate"]:
                        detected_min = 1
                        method = "probe"
                        print(f"    → min_stay=1 (price found on +{week_offset}d probe)")
                        break

        if detected_min is not None:
            conn.execute("""INSERT OR REPLACE INTO min_stay_history
                (listing_id, min_stay, scrape_date, detection_method)
                VALUES (?, ?, ?, ?)""", (comp["id"], detected_min, today, method))
            conn.execute("UPDATE listings SET min_stay=? WHERE listing_id=?",
                         (detected_min, comp["id"]))
            conn.commit()
            confirmed += 1

            prev = prev_min_stays.get(comp["id"])
            was_changed = prev is not None and prev != detected_min
            if was_changed:
                changed += 1
            summary_rows.append((comp["name"], prev, detected_min, method))
        else:
            print(f"    → unknown (all probes blocked — possibly booked far out)")
            unknown += 1
            summary_rows.append((comp["name"], prev_min_stays.get(comp["id"]), None, "unknown"))

        time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))

    browser.close()
    pw.stop()

    # Summary
    print(f"\n{'='*60}")
    print(f"MINSTAY AUDIT RESULTS — {today}")
    print(f"{'='*60}")
    print(f"  Confirmed: {confirmed}/{total} | Unknown: {unknown}/{total} | Changed: {changed}")
    print(f"\n  {'Name':<38} {'Prev':>5} {'New':>5} {'Method':<8}")
    print(f"  {'-'*60}")
    for name, prev, new, meth in summary_rows:
        prev_str = str(prev) if prev is not None else "—"
        new_str  = str(new)  if new  is not None else "?"
        flag = " ← CHANGED" if (prev is not None and new is not None and prev != new) else ""
        print(f"  {name:<38} {prev_str:>5} {new_str:>5} {meth:<8}{flag}")
    print(f"{'='*60}\n")

    conn.close()
    if not skip_confirm:
        confirm_and_push(date.today().isoformat(), "minstay")


# ============================================================
# SEASONAL MODE — Rate comparison across seasons
# ============================================================

def run_seasonal(_limit=None, _override=None, skip_confirm=False):
    """
    For T1+T2 comps, check 3-night Tuesday rates across 6 seasonal windows.
    Same day-of-week and length isolates the seasonal variable.
    """
    conn = init_db()
    seed_listings(conn)

    today = date.today()

    # Define seasonal check-in Tuesdays
    def next_tuesday_near(target_date):
        """Find the Tuesday closest to target_date."""
        d = target_date
        while d.weekday() != 1:
            d += timedelta(days=1)
        return d

    seasons = [
        ("current", next_tuesday_near(today + timedelta(days=21))),
        ("shoulder_apr", next_tuesday_near(date(2026, 4, 14))),
        ("high_jun", next_tuesday_near(date(2026, 6, 16))),
        ("peak_jul", next_tuesday_near(date(2026, 7, 14))),
        ("low_oct", next_tuesday_near(date(2026, 10, 13))),
        ("nye_dec", next_tuesday_near(date(2026, 12, 29))),
    ]

    # Remove any seasons that are in the past
    seasons = [(label, d) for label, d in seasons if d > today]

    t1_t2 = active_comps(tier_filter=[1, 2], limit=_limit, override=_override)

    pw, browser, context = create_browser()
    page = context.new_page()

    print(f"\n{'='*60}")
    print(f"SEASONAL ANALYSIS — {date.today()}")
    print(f"{'='*60}")
    print(f"Seasons to check:")
    for label, d in seasons:
        print(f"  {label}: {d} (Tue, 3 nights)")
    print(f"Comps: {len(t1_t2)} (T1 + T2, segments: {', '.join(ACTIVE_SEGMENTS)})")
    print(f"Total requests: ~{len(t1_t2) * len(seasons)}")
    print(f"{'='*60}\n")

    for i, comp in enumerate(t1_t2, 1):
        print(f"[{i}/{len(t1_t2)}] {comp['name']} (T{comp['tier']} {comp['seg']})")

        for label, checkin_date in seasons:
            checkin = checkin_date.isoformat()

            result = extract_with_minstay_retry(page, comp["id"], checkin, 3, conn)
            actual_nights = result.get("nights", 3)

            save_price(conn, comp["id"], f"seasonal_{label}", checkin, actual_nights,
                       result["nightly_rate"], result["total_price"], result["is_available"])

            if result["nightly_rate"]:
                print(f"    {label}: ${result['nightly_rate']:.0f}/night")
            else:
                status = "BOOKED" if not result["is_available"] else "SCRAPE FAIL"
                print(f"    {label}: {status}")

            time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))

        time.sleep(random.uniform(1, 3))

    browser.close()
    pw.stop()

    # Print seasonal summary
    print(f"\n{'='*60}")
    print(f"SEASONAL SUMMARY")
    print(f"{'='*60}\n")

    c = conn.cursor()
    today_str = date.today().isoformat()

    for seg in ["3bed", "4bed", "6bed"]:
        seg_comps = [comp["id"] for comp in t1_t2 if comp["seg"] == seg]
        if not seg_comps:
            continue

        print(f"--- {seg.upper()} (T1+T2) ---")

        # Build per-comp rate dict: {listing_id: {season_label: rate}}
        comp_rates = {}
        for comp_id in seg_comps:
            c.execute("""SELECT scrape_label, nightly_rate FROM price_snapshots
                WHERE listing_id = ? AND scrape_date = ?
                AND scrape_label LIKE 'seasonal_%' AND nightly_rate IS NOT NULL""",
                (comp_id, today_str))
            rates = {row[0]: row[1] for row in c.fetchall()}
            if rates:
                comp_rates[comp_id] = rates

        baseline_label = "seasonal_current"

        print(f"  {'Season':<15} {'Avg rate':>10} {'vs current':>12} {'Paired n':>10}")
        print(f"  {'-'*50}")

        for label, _ in seasons:
            full_label = f"seasonal_{label}"

            # Paired analysis: only comps with BOTH current AND this season
            paired_mults = []
            paired_rates = []
            for cr in comp_rates.values():
                if full_label in cr and baseline_label in cr:
                    base = cr[baseline_label]
                    this = cr[full_label]
                    paired_rates.append(this)
                    if base > 0:
                        paired_mults.append(this / base)

            # Fallback to all rates if no paired data
            if not paired_rates:
                paired_rates = [cr[full_label] for cr in comp_rates.values() if full_label in cr]

            avg_rate = round(sum(paired_rates) / len(paired_rates)) if paired_rates else None
            avg_mult = round(sum(paired_mults) / len(paired_mults), 2) if paired_mults else None

            if avg_rate:
                mult_str = f"{avg_mult:.2f}x" if avg_mult is not None else "—"
                paired_n = f"n={len(paired_mults)}"
                print(f"  {label:<15} ${avg_rate:>9.0f} {mult_str:>12} {paired_n:>10}")
            else:
                print(f"  {label:<15} {'—':>10} {'—':>12} {'n=0':>10}")

        print()

    conn.close()
    if not skip_confirm:
        confirm_and_push(date.today().isoformat(), "seasonal")


# ============================================================
# LEADTIME MODE — How pricing changes as dates approach
# ============================================================

# Fixed tracking dates for longitudinal far-out analysis.
# Check these every weekly run to build a curve over 8-12 weeks.
# Pick dates that represent peak and low seasons.
TRACKING_DATES = {
    "track_peak_jul14": date(2026, 7, 14),   # Peak season Tuesday
    "track_low_oct13": date(2026, 10, 13),    # Low season Tuesday
}


def run_leadtime(_limit=None, _override=None, skip_confirm=False):
    """
    For T1 3-bed comps, check the same type of date (Tuesday, 3n)
    at different lead times to see how pricing shifts.

    IMMEDIATE checks (same-season snapshot — changes each run):
      lastmin_3d:   ~3 days out
      nearterm_14d: ~14 days out (anchor — skip comp if booked)
      medium_30d:   ~30 days out

    LONGITUDINAL checks (fixed dates — builds far-out curve over weeks):
      track_peak_jul14: Jul 14 2026 (peak season)
      track_low_oct13:  Oct 13 2026 (low season)
    """
    conn = init_db()
    seed_listings(conn)

    today = date.today()

    def next_tuesday_after(d):
        while d.weekday() != 1:
            d += timedelta(days=1)
        return d

    # Three immediate lead times, all Tuesdays, all 3-night stays
    immediate_leads = [
        ("lastmin_3d", next_tuesday_after(today + timedelta(days=2))),
        ("nearterm_14d", next_tuesday_after(today + timedelta(days=14))),
        ("medium_30d", next_tuesday_after(today + timedelta(days=30))),
    ]

    # Longitudinal tracking dates — only include if still in the future
    tracking_leads = [
        (label, d) for label, d in TRACKING_DATES.items()
        if d > today
    ]

    all_leads = immediate_leads + tracking_leads

    # T1 3-bed only (most relevant for your launch pricing)
    all_t1 = active_comps(tier_filter=[1], limit=_limit, override=_override)
    t1_3bed = [c for c in all_t1 if c["seg"] == "3bed"]

    pw, browser, context = create_browser()
    page = context.new_page()

    print(f"\n{'='*60}")
    print(f"LEAD TIME ANALYSIS — {date.today()}")
    print(f"{'='*60}")
    print(f"Immediate lead times:")
    for label, d in immediate_leads:
        days_out = (d - today).days
        print(f"  {label}: {d} ({days_out} days out)")
    print(f"Longitudinal tracking dates:")
    for label, d in tracking_leads:
        days_out = (d - today).days
        print(f"  {label}: {d} ({days_out} days out)")
    if not tracking_leads:
        print(f"  (all tracking dates have passed — update TRACKING_DATES)")
    print(f"Comps: {len(t1_3bed)} (T1 3-bed)")
    max_loads = len(t1_3bed) * len(all_leads)
    print(f"Max requests: ~{max_loads} (fewer with smart skip)")
    print(f"{'='*60}\n")

    for i, comp in enumerate(t1_3bed, 1):
        print(f"[{i}/{len(t1_3bed)}] {comp['name']}")

        # SMART SKIP: Check 14-day anchor FIRST.
        #   BOOKED    → skip entire comp (genuinely busy, other lead times useless)
        #   SCRAPE FAIL → try 30-day as backup anchor before giving up
        anchor_label, anchor_date = immediate_leads[1]  # nearterm_14d
        anchor_checkin = anchor_date.isoformat()

        anchor_result = extract_with_minstay_retry(page, comp["id"], anchor_checkin, 3, conn)
        anchor_nights = anchor_result.get("nights", 3)
        save_price(conn, comp["id"], f"leadtime_{anchor_label}", anchor_checkin, anchor_nights,
                   anchor_result["nightly_rate"], anchor_result["total_price"], anchor_result["is_available"])

        if not anchor_result["nightly_rate"]:
            if not anchor_result["is_available"]:
                # Genuinely booked — skip all remaining lead times for this comp
                print(f"    {anchor_label} (anchor): BOOKED — skipping remaining lead times")
                time.sleep(random.uniform(1, 3))
                continue
            elif anchor_result.get("min_stay_detected"):
                print(f"    {anchor_label} (anchor): MIN STAY {anchor_result['min_stay_detected']}n — skipping")
                time.sleep(random.uniform(1, 3))
                continue
            else:
                # Scrape failure — try 30d as backup anchor before giving up
                backup_label, backup_date = immediate_leads[2]  # medium_30d
                backup_checkin = backup_date.isoformat()
                print(f"    {anchor_label} (anchor): SCRAPE FAIL — trying {backup_label} as backup anchor...")
                time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))
                backup_result = extract_with_minstay_retry(page, comp["id"], backup_checkin, 3, conn)
                backup_nights = backup_result.get("nights", 3)
                save_price(conn, comp["id"], f"leadtime_{backup_label}", backup_checkin, backup_nights,
                           backup_result["nightly_rate"], backup_result["total_price"], backup_result["is_available"])
                if backup_result["nightly_rate"]:
                    # Promote 30d to anchor and continue — mark 14d as missing
                    anchor_label = backup_label
                    anchor_result = backup_result
                    anchor_nights = backup_nights
                    print(f"    {backup_label} (backup anchor): ${backup_result['nightly_rate']:.0f}/night")
                else:
                    backup_status = "BOOKED" if not backup_result["is_available"] else "SCRAPE FAIL"
                    print(f"    {backup_label} (backup anchor): {backup_status} — skipping comp")
                    time.sleep(random.uniform(1, 3))
                    continue

        print(f"    {anchor_label} (anchor): ${anchor_result['nightly_rate']:.0f}/night")
        prices_collected = 1

        # Now check the other lead times (skip the anchor since we already did it)
        for label, checkin_date in all_leads:
            if label == anchor_label:
                continue

            checkin = checkin_date.isoformat()

            time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))
            result = extract_with_minstay_retry(page, comp["id"], checkin, 3, conn)
            actual_nights = result.get("nights", 3)

            save_price(conn, comp["id"], f"leadtime_{label}", checkin, actual_nights,
                       result["nightly_rate"], result["total_price"], result["is_available"])

            if result["nightly_rate"]:
                days_out = (checkin_date - today).days
                tag = " [tracking]" if label.startswith("track_") else ""
                print(f"    {label}: ${result['nightly_rate']:.0f}/night ({days_out}d out){tag}")
                prices_collected += 1
            else:
                status = "BOOKED" if not result["is_available"] else "SCRAPE FAIL"
                if result.get("min_stay_detected"):
                    status = f"MIN STAY {result['min_stay_detected']}n"
                print(f"    {label}: {status}")

        total_checks = len(all_leads)
        print(f"    → {prices_collected}/{total_checks} lead times captured")
        time.sleep(random.uniform(1, 3))

    browser.close()
    pw.stop()

    # ================================================================
    # SUMMARY — Immediate lead time analysis
    # ================================================================
    print(f"\n{'='*60}")
    print(f"LEAD TIME SUMMARY (T1 3-bed)")
    print(f"{'='*60}\n")

    c = conn.cursor()
    today_str = date.today().isoformat()
    t1_ids = [comp["id"] for comp in t1_3bed]
    ph = ",".join("?" * len(t1_ids))

    # Build dict of {listing_id: {label: rate}} for today's scrape
    comp_rates = {}
    for comp in t1_3bed:
        c.execute("""SELECT scrape_label, nightly_rate FROM price_snapshots
            WHERE listing_id = ? AND scrape_date = ?
            AND scrape_label LIKE 'leadtime_%' AND nightly_rate IS NOT NULL""",
            (comp["id"], today_str))
        rates = {row[0]: row[1] for row in c.fetchall()}
        if rates:
            comp_rates[comp["id"]] = {"name": comp["name"], "rates": rates}

    # Immediate lead times: paired analysis vs 14-day baseline
    baseline_label = "leadtime_nearterm_14d"

    print(f"  IMMEDIATE (same-season snapshot):")
    print(f"  {'Lead time':<20} {'Avg rate':>10} {'vs 14-day':>12} {'Paired n':>10} {'PriceLabs implication'}")
    print(f"  {'-'*80}")

    for label, d in immediate_leads:
        full_label = f"leadtime_{label}"
        days_out = (d - today).days

        all_rates = [cr["rates"][full_label] for cr in comp_rates.values() if full_label in cr["rates"]]

        # Paired: only comps that have BOTH this label AND the baseline
        paired_deltas = []
        paired_rates = []
        for cr in comp_rates.values():
            if full_label in cr["rates"] and baseline_label in cr["rates"]:
                base_rate = cr["rates"][baseline_label]
                this_rate = cr["rates"][full_label]
                paired_rates.append(this_rate)
                if base_rate > 0:
                    delta_pct = (this_rate - base_rate) / base_rate * 100
                    paired_deltas.append(delta_pct)

        # Use paired rates for display (same sample as % comparison)
        avg_rate = round(sum(paired_rates) / len(paired_rates)) if paired_rates else (
            round(sum(all_rates) / len(all_rates)) if all_rates else None)
        avg_delta = round(sum(paired_deltas) / len(paired_deltas)) if paired_deltas else None

        if avg_rate:
            delta_str = f"{'+' if avg_delta >= 0 else ''}{avg_delta}%" if avg_delta is not None else "—"
            paired_n = f"n={len(paired_deltas)}"

            implication = ""
            if avg_delta is not None:
                if label == "lastmin_3d":
                    if avg_delta > 5:
                        implication = f"→ Comps charge MORE last-min (+{avg_delta}%). Don't discount."
                    elif avg_delta < -5:
                        implication = f"→ Comps discount last-min by {abs(avg_delta)}%"
                    else:
                        implication = "→ Flat last-minute (no adjustment)"
                elif label == "nearterm_14d":
                    implication = "→ BASELINE"
                elif label == "medium_30d":
                    if avg_delta < -5:
                        implication = f"→ Comps price {abs(avg_delta)}% lower at {days_out}d. Slight far-out discount."
                    elif avg_delta > 5:
                        implication = f"→ Comps charge +{avg_delta}% premium at {days_out}d out"
                    else:
                        implication = "→ Flat (no 30-day adjustment)"

            print(f"  {label:<20} ${avg_rate:>9} {delta_str:>12} {paired_n:>10} {implication}")
        else:
            print(f"  {label:<20} {'—':>10} {'—':>12} {'n=0':>10}")

    # Tracking dates: show current snapshot + historical trend if available
    if tracking_leads:
        print(f"\n  LONGITUDINAL (fixed tracking dates — run weekly to build curve):")
        print(f"  {'Tracking date':<20} {'Today rate':>10} {'Days out':>10} {'History':>40}")
        print(f"  {'-'*85}")

        for label, d in tracking_leads:
            full_label = f"leadtime_{label}"
            days_out = (d - today).days

            # Today's rates
            today_rates = [cr["rates"][full_label] for cr in comp_rates.values() if full_label in cr["rates"]]
            today_avg = round(sum(today_rates) / len(today_rates)) if today_rates else None

            # Historical rates for this tracking label (all previous scrape dates)
            c.execute(f"""SELECT scrape_date, AVG(nightly_rate) FROM price_snapshots
                WHERE listing_id IN ({ph}) AND scrape_label = ?
                AND nightly_rate IS NOT NULL
                GROUP BY scrape_date ORDER BY scrape_date""",
                t1_ids + [full_label])
            history = c.fetchall()

            hist_str = ""
            if len(history) > 1:
                # Show trend: date=$avg, date=$avg, ...
                hist_parts = [f"{row[0][5:]}=${row[1]:.0f}" for row in history[-6:]]  # Last 6 data points
                hist_str = " | ".join(hist_parts)
                # Calculate overall trend
                first_avg = history[0][1]
                last_avg = history[-1][1]
                if first_avg > 0:
                    trend_pct = (last_avg - first_avg) / first_avg * 100
                    trend_dir = "↑" if trend_pct > 0 else "↓"
                    hist_str += f"  {trend_dir}{abs(trend_pct):.0f}%"
            elif len(history) == 1:
                hist_str = "(first data point — run weekly to build curve)"
            else:
                hist_str = "(no data yet)"

            if today_avg:
                print(f"  {label:<20} ${today_avg:>9} {days_out:>8}d  {hist_str}")
            else:
                print(f"  {label:<20} {'—':>10} {days_out:>8}d  {hist_str}")

    # Per-comp detail
    all_labels = [l for l, _ in all_leads]
    label_headers = [l.replace("track_peak_", "pk_").replace("track_low_", "lo_").replace("leadtime_", "")
                     for l in all_labels]
    col_width = max(7, max(len(h) for h in label_headers) + 1)

    print(f"\n  Per-comp detail:")
    header = f"  {'Name':<30}" + "".join(f"{h:>{col_width}}" for h in label_headers)
    print(header)
    print(f"  {'-'*(30 + col_width * len(all_labels))}")

    for lid, cr in comp_rates.items():
        if baseline_label not in cr["rates"]:
            continue
        rates = cr["rates"]
        cols = []
        for label, _ in all_leads:
            fl = f"leadtime_{label}"
            cols.append(f"${rates[fl]:.0f}" if fl in rates else "—")
        row = f"  {cr['name']:<30}" + "".join(f"{c:>{col_width}}" for c in cols)
        print(row)

    conn.close()
    if not skip_confirm:
        confirm_and_push(date.today().isoformat(), "leadtime")


# ============================================================
# TEST-ALL MODE — Quick validation of every mode (2 comps each)
# ============================================================

def run_test_all(listing_id=None):
    """Run every scrape mode with limited comps. Quick validation.
    If listing_id is provided, runs all modes on just that one comp.
    Otherwise runs on 2 comps.

    Uses active_comps(limit=..., override=...) instead of mutating globals —
    no global state side effects, KeyboardInterrupt-safe.
    """
    if listing_id:
        comp = next((c for c in COMP_SET if c["id"] == listing_id), None)
        if not comp:
            print(f"Listing {listing_id} not found in comp set.")
            return
        test_override = [listing_id]
        test_limit = None
        desc = f"1 comp: {comp['name']} ({comp['seg']} T{comp['tier']})"
    else:
        test_override = None
        test_limit = 2
        desc = "2 comps"

    print(f"\n{'='*60}")
    print(f"TEST-ALL — Validating all modes with {desc}")
    print(f"{'='*60}")
    print(f"Active segments: {', '.join(ACTIVE_SEGMENTS)}")
    print(f"This should take ~10-15 minutes total.\n")

    modes = [
        ("DAILY", lambda: run_daily(_limit=test_limit, _override=test_override)),
        ("DISCOUNTS", lambda: run_discounts(_limit=test_limit, _override=test_override)),
        ("SEASONAL", lambda: run_seasonal(_limit=test_limit, _override=test_override)),
        ("LEADTIME", lambda: run_leadtime(_limit=test_limit, _override=test_override)),
    ]

    results = {}
    for name, func in modes:
        print(f"\n{'='*60}")
        print(f"TESTING: {name}")
        print(f"{'='*60}")
        try:
            func()
            results[name] = "✓ OK"
        except Exception as e:
            results[name] = f"✗ ERROR: {e}"
            print(f"\n  ERROR in {name}: {e}")

    print(f"\n{'='*60}")
    print(f"TEST-ALL RESULTS")
    print(f"{'='*60}")
    for name, status in results.items():
        print(f"  {name:<15} {status}")
    print(f"\nIf all OK, run each mode for real without the 2-comp limit.")
    print(f"Data from this test run IS saved to the database (it's real data, just less of it).")


# ============================================================
# FULL MODE — Everything
# ============================================================

def run_full():
    """Run all analysis modes in sequence."""
    print(f"\n{'='*60}")
    print(f"FULL ANALYSIS — {date.today()}")
    print(f"This will take approximately 2.5–3 hours.")
    print(f"{'='*60}\n")

    run_daily(skip_confirm=True)
    print("\n\n")
    run_discounts(skip_confirm=True)
    print("\n\n")
    run_seasonal(skip_confirm=True)
    print("\n\n")
    run_leadtime(skip_confirm=True)

    confirm_and_push(date.today().isoformat(), "full")


# ============================================================
# EXPORT
# ============================================================

def export_csv():
    conn = sqlite3.connect(DB_PATH)
    EXPORT_DIR.mkdir(exist_ok=True)
    today_str = date.today().isoformat()

    c = conn.cursor()

    # 1. Listings
    c.execute("""SELECT listing_id, name, segment, tier, rating, review_count,
                        min_stay, url, last_scraped
                 FROM listings ORDER BY segment, tier, name""")
    rows = c.fetchall()
    cols = [d[0] for d in c.description]
    filepath = EXPORT_DIR / f"listings_{today_str}.csv"
    with open(filepath, "w", newline="") as f:
        w = csv.writer(f); w.writerow(cols); w.writerows(rows)
    print(f"Exported {len(rows)} listings to {filepath}")

    # 2. All price snapshots with listing metadata
    c.execute("""SELECT p.listing_id, p.scrape_date, p.scrape_label, p.checkin_date,
                        p.nights, p.nightly_rate, p.total_price, p.is_available, p.currency,
                        l.name, l.segment, l.tier, l.rating, l.review_count, l.min_stay
                 FROM price_snapshots p
                 JOIN listings l ON p.listing_id = l.listing_id
                 ORDER BY p.scrape_date DESC, l.segment, l.tier""")
    rows = c.fetchall()
    cols = [d[0] for d in c.description]
    filepath2 = EXPORT_DIR / f"prices_{today_str}.csv"
    with open(filepath2, "w", newline="") as f:
        w = csv.writer(f); w.writerow(cols); w.writerows(rows)
    print(f"Exported {len(rows)} price points to {filepath2}")

    # 3. Occupancy checks with listing metadata
    c.execute("""SELECT o.listing_id, o.check_date, o.is_booked, o.scrape_date,
                        l.name, l.segment, l.tier
                 FROM occupancy_checks o
                 JOIN listings l ON o.listing_id = l.listing_id
                 ORDER BY o.check_date DESC, l.segment""")
    rows = c.fetchall()
    cols = [d[0] for d in c.description]
    filepath3 = EXPORT_DIR / f"occupancy_{today_str}.csv"
    with open(filepath3, "w", newline="") as f:
        w = csv.writer(f); w.writerow(cols); w.writerows(rows)
    print(f"Exported {len(rows)} occupancy checks to {filepath3}")

    conn.close()
    print(f"\nAll exports in: {EXPORT_DIR}/")
    print(f"  listings_{today_str}.csv")
    print(f"  prices_{today_str}.csv")
    print(f"  occupancy_{today_str}.csv")


# ============================================================
# DASHBOARD
# ============================================================

def print_dashboard():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    latest = c.execute("SELECT MAX(scrape_date) FROM price_snapshots").fetchone()[0]

    if not latest:
        print("No data yet. Run: python3 scraper_v2.py test 7816774")
        return

    print(f"\n{'='*70}")
    print(f"COMPETITOR DASHBOARD — {latest}")
    print(f"{'='*70}\n")

    for seg in ["3bed", "4bed", "6bed"]:
        print(f"--- {seg.upper()} ---")
        for tier in [1, 2, 3]:
            c.execute("""
                SELECT l.name, l.rating, l.review_count,
                    MAX(CASE WHEN p.scrape_label='weekday' THEN p.nightly_rate END) as wd,
                    MAX(CASE WHEN p.scrape_label='weekend' THEN p.nightly_rate END) as we
                FROM listings l
                LEFT JOIN price_snapshots p ON l.listing_id = p.listing_id AND p.scrape_date = ?
                WHERE l.segment = ? AND l.tier = ?
                GROUP BY l.listing_id
                ORDER BY wd DESC
            """, (latest, seg, tier))
            rows = c.fetchall()
            if not rows:
                continue

            tier_labels = {1: "T1 DIRECT", 2: "T2 ASPIRATIONAL", 3: "T3 FLOOR"}
            print(f"\n  {tier_labels[tier]}")
            print(f"  {'Name':<35} {'Wkday':>7} {'Wkend':>7} {'Spread':>7} {'Rate':>5} {'Rev':>5}")
            print(f"  {'-'*70}")

            wd_prices, we_prices = [], []
            for r in rows:
                name = (r[0] or "?")[:34]
                wd = f"${r[3]:.0f}" if r[3] else "—"
                we = f"${r[4]:.0f}" if r[4] else "—"
                spread = ""
                if r[3] and r[4]:
                    sp = round((r[4] - r[3]) / r[3] * 100)
                    spread = f"+{sp}%" if sp >= 0 else f"{sp}%"
                    wd_prices.append(r[3])
                    we_prices.append(r[4])
                elif r[3]:
                    wd_prices.append(r[3])
                rating = f"{r[1]:.1f}" if r[1] else "—"
                reviews = str(r[2] or "—")
                print(f"  {name:<35} {wd:>7} {we:>7} {spread:>7} {rating:>5} {reviews:>5}")

            if wd_prices:
                wd_avg = round(sum(wd_prices) / len(wd_prices))
                we_avg = round(sum(we_prices) / len(we_prices)) if we_prices else 0
                print(f"  {'-'*70}")
                print(f"  {'AVERAGE':<35} ${wd_avg:>6} ${we_avg:>6}")
        print()

    conn.close()


# ============================================================
# OCCUPANCY REPORT
# ============================================================

def print_occupancy():
    """Print backward-looking occupancy estimates from daily checks."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Check how many days of data we have
    days_of_data = c.execute("SELECT COUNT(DISTINCT scrape_date) FROM occupancy_checks").fetchone()[0]

    if days_of_data == 0:
        print("No occupancy data yet. Run 'daily' mode for at least 7 days to build occupancy estimates.")
        return

    print(f"\n{'='*70}")
    print(f"OCCUPANCY ESTIMATES — based on {days_of_data} days of daily checks")
    print(f"{'='*70}")

    if days_of_data < 7:
        print(f"\n  NOTE: Only {days_of_data} days of data. Need 7+ for meaningful estimates.\n")

    # Last 30 days (or however many we have)
    cutoff = (date.today() - timedelta(days=30)).isoformat()

    for seg in ["3bed", "4bed", "6bed"]:
        t1_comps = [comp for comp in active_comps(tier_filter=[1]) if comp["seg"] == seg]
        if not t1_comps:
            continue

        print(f"\n--- {seg.upper()} T1 (last {min(days_of_data, 30)} days) ---\n")
        print(f"  {'Name':<35} {'Booked':>8} {'Checked':>8} {'Occ %':>7}")
        print(f"  {'-'*60}")

        seg_booked = 0
        seg_total = 0

        for comp in t1_comps:
            row = c.execute("""
                SELECT SUM(is_booked), COUNT(*) FROM occupancy_checks
                WHERE listing_id = ? AND scrape_date >= ?
            """, (comp["id"], cutoff)).fetchone()

            booked = row[0] or 0
            total = row[1] or 0

            if total > 0:
                pct = round(booked / total * 100)
                bar = "█" * (pct // 5) + "░" * (20 - pct // 5)
                print(f"  {comp['name']:<35} {booked:>8} {total:>8} {pct:>6}% {bar}")
                seg_booked += booked
                seg_total += total
            else:
                print(f"  {comp['name']:<35} {'—':>8} {'—':>8} {'—':>7}")

        if seg_total > 0:
            seg_pct = round(seg_booked / seg_total * 100)
            print(f"  {'-'*60}")
            print(f"  {'SEGMENT AVERAGE':<35} {seg_booked:>8} {seg_total:>8} {seg_pct:>6}%")

    print(f"\n{'='*70}")
    print(f"Compare against your own occupancy to see if you're above or below market.")
    print(f"{'='*70}\n")

    conn.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 scraper_v2.py test <listing_id>   # Test single listing")
        print("  python3 scraper_v2.py test-all             # Quick test all modes (2 comps each, ~10 min)")
        print("  python3 scraper_v2.py test-all <listing_id>  # Test all modes on one specific comp")
        print("  python3 scraper_v2.py daily                # Weekday + weekend rates + occupancy check")
        print("  python3 scraper_v2.py discounts            # 3n/7n/28n rates for T1+T2 (monthly)")
        print("  python3 scraper_v2.py seasonal             # Rates across 6 seasons for T1+T2 (monthly)")
        print("  python3 scraper_v2.py leadtime             # Rates at 3d/14d/30d + tracking dates (weekly)")
        print("  python3 scraper_v2.py full                 # All modes in one run (~2.5 hrs)")
        print("  python3 scraper_v2.py export               # Export all data to CSV")
        print("  python3 scraper_v2.py dashboard            # Print pricing summary")
        print("  python3 scraper_v2.py occupancy            # Print occupancy summary (needs 7+ days of daily data)")
        print("")
        print("Start with: python3 scraper_v2.py test 7816774")
        sys.exit(1)

    mode = sys.argv[1].lower()

    if mode == "test":
        lid = sys.argv[2] if len(sys.argv) > 2 else "7816774"
        run_test(lid)
    elif mode == "test-all":
        lid = sys.argv[2] if len(sys.argv) > 2 else None
        run_test_all(lid)
    elif mode == "daily":
        run_daily()
    elif mode == "discounts":
        run_discounts()
    elif mode == "seasonal":
        run_seasonal()
    elif mode == "leadtime":
        run_leadtime()
    elif mode == "minstay":
        run_minstay_audit()
    elif mode == "full":
        run_full()
    elif mode == "export":
        export_csv()
    elif mode == "dashboard":
        print_dashboard()
    elif mode == "occupancy":
        print_occupancy()
    else:
        print(f"Unknown mode: {mode}")
