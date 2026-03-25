# TODOS — Berawa Comp Intelligence Tool

## P1 — High Priority

### Pricing Advisor: "What should I charge tonight?"
**What:** A `python3 scraper_v2.py advise` command that outputs recommended rates for
your own villas based on current comp market data.

**Why:** Turns the tool from a research tool into an operating tool. Daily pricing
decisions should take 30 seconds, not 10 minutes of manual analysis.

**Pros:** High-leverage. Directly reduces time spent on pricing. Pays for itself day 1.

**Cons:** Need 30+ days of baseline data to calibrate. Wrong model = wrong
recommendations — risk of underpricing during peaks or overpricing during low demand.

**Context:** Build after first full month of daily scrape data. The model is:
  `recommend = T1_avg_for_date × positioning_pct × leadtime_multiplier × seasonal_multiplier`
  Where:
  - `T1_avg_for_date` = T1 comp weekday or weekend avg for check-in date
  - `positioning_pct` = your target position (10th/25th/50th/75th percentile vs T1)
  - `leadtime_multiplier` = from leadtime mode data (e.g., last-min = 1.05x if comps charge more)
  - `seasonal_multiplier` = from seasonal mode data for that time of year

**Effort:** M (human: 2 days → CC+gstack: ~30 min)
**Priority:** P1
**Depends on:** 30+ days of daily scrape data, own_property tables in DB


---

## P2 — Medium Priority

### Proxy Rotation Support
**What:** Add `PROXY_URL` environment variable support to `create_browser()` in
scraper_v2.py. If the env var is set, Playwright uses it. If not, runs without proxy.

**Why:** Single IP + one user agent string = eventually blocked by Airbnb. This is
when, not if. Proxy support lets you recover without code changes.

**Pros:** Extends scraper lifetime indefinitely once implemented. Small code change.

**Cons:** ~$29-49/mo for BrightData or ScraperAPI. Only worth paying if you get blocked.

**Context:** Don't pay for proxies preemptively. When Airbnb starts blocking (you'll
see >40% failure rate in the scrape health monitor), add `PROXY_URL=http://user:pass@proxy`
to a `.env` file and the scraper should pick it up automatically.

**Effort:** S (human: 2 hrs → CC+gstack: 10 min)
**Priority:** P2
**Depends on:** Getting blocked (use as trigger)


---

## P3 — Lower Priority

### VRBO/Expedia Comp Coverage
**What:** Add VRBO listing IDs for the top 10-15 T1 comps and scrape their prices in
parallel with Airbnb. Store in `price_snapshots` with `source='vrbo'` column.

**Why:** Some Berawa villas price 10-20% higher on VRBO due to lower OTA fees. Knowing
this tells you: (1) whether there's room to charge more on Airbnb, (2) whether comps
are using platform-specific pricing strategies.

**Pros:** More complete picture. Potential to find underpricing on your own listings.

**Cons:** VRBO scraper is a separate build. Manual mapping of comps to VRBO IDs needed.
More complex page structure — VRBO is more aggressively anti-scraping than Airbnb.

**Context:** Only worth building after Airbnb data is stable and you've validated the
existing tool runs cleanly for 30+ days. Start by manually checking 3-4 top comps on
VRBO vs Airbnb to see if price discrepancy even exists at scale.

**Effort:** L (human: 1 week → CC+gstack: ~1 hour)
**Priority:** P3
**Depends on:** Stable Airbnb scraper, manual VRBO ID research


---

## P2 (additional) — Airbnb Host CSV Importer

### my_bookings importer (Airbnb host CSV)
**What:** A `python3 scraper_v2.py import-bookings <file.csv>` command that reads the
Airbnb host reservations CSV export and loads it into `my_bookings`.

**Why:** Airbnb's host dashboard lets you export all reservations. Rather than typing
each booking in manually, a one-shot importer back-fills the history automatically.

**Pros:** Back-fill historical data quickly after launch. Re-import anytime to catch up.

**Cons:** Airbnb's CSV format could change. One-time tool, low reuse value.

**Context:** Write after launch when you have actual bookings to import. In Airbnb host
dashboard: Reservations → Export CSV. Fields to parse: check_in, check_out,
amount_earned (= nightly_rate × nights or total, need to normalize), booking_date.
Map to my_bookings: property_id (manual, based on listing), checkin, checkout,
nightly_rate, booked_date, source='airbnb'.

**Effort:** S (human: 2 hrs → CC+gstack: 10 min)
**Priority:** P2
**Depends on:** Having actual bookings to import (post-launch)


---

## P3 (additional) — Telegram Alerting

### Daily price alert push to Telegram
**What:** After `run_price_alerts()` in the daily scrape run, push the alert summary
as a Telegram message to your phone via a bot. Triggered by existing cron job.

**Why:** The scraper already generates price change alerts and dark listing warnings.
They currently print to terminal / log file. Pushing to Telegram means you're notified
at 6am when the cron runs without ever opening your laptop.

**Pros:** Zero new data collection — reuses `run_price_alerts()` output. Small code change.
Push means you don't need to remember to check the dashboard.

**Cons:** Requires creating a Telegram bot (5 min, one-time). If scraper runs frequently,
could become noisy — needs dedup logic (don't alert same dark listing every day).

**Context:** In Telegram: create a bot via @BotFather → get `TELEGRAM_BOT_TOKEN`.
Send yourself a message to get your `TELEGRAM_CHAT_ID`. Add both as env vars.
In `scraper_v2.py`, after `run_price_alerts()`, call `requests.post(telegram_url, json={...})`.
Add alert dedup: track last-alerted date per listing_id in a simple JSON file or new DB table.

**Effort:** S (human: 2 hrs → CC+gstack: 10 min)
**Priority:** P3
**Depends on:** Stable daily scrape cron running cleanly
