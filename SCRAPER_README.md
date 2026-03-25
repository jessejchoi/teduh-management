# Airbnb Competitor Scraper — Setup Guide

## Quick start

```bash
# 1. Install Python dependencies
pip install playwright

# 2. Install the browser engine (one-time, downloads ~150MB)
playwright install chromium

# 3. Test with a single listing first
python scraper.py single 7816774

# 4. If that works, run your first daily scrape
python scraper.py daily
```

## What each mode does

| Command | What it scrapes | Comps | Time estimate |
|---|---|---|---|
| `python scraper.py daily` | Weekday + weekend rate (~2 weeks out, 3-night stay) | All 56 | ~25–40 min |
| `python scraper.py weekly` | Full price matrix (10 date/length combos) + occupancy calendar | T1 prices (22) + all occupancy (56) | ~60–90 min |
| `python scraper.py monthly` | Full price matrix + occupancy for ALL comps | All 56 | ~90–120 min |
| `python scraper.py single <ID>` | Quick test of one listing | 1 | ~2 min |
| `python scraper.py export` | Dump all data to CSV files in /exports | — | instant |
| `python scraper.py dashboard` | Print pricing summary to terminal | — | instant |
| `python scraper.py occupancy` | Print occupancy summary to terminal | — | instant |

## Automate with cron

```bash
# Edit crontab
crontab -e

# Add these lines:
# Daily at 6am Bali time (WITA = UTC+8)
0 6 * * * cd /path/to/scraper && python3 scraper.py daily >> logs/daily.log 2>&1

# Weekly full scan every Monday at 7am
0 7 * * 1 cd /path/to/scraper && python3 scraper.py weekly >> logs/weekly.log 2>&1

# Monthly comprehensive scan on the 1st at 5am
0 5 1 * * cd /path/to/scraper && python3 scraper.py monthly >> logs/monthly.log 2>&1
```

## Where data lives

- **comp_data.db** — SQLite database with all scraped data
- **exports/** — CSV exports (run `python scraper.py export`)
- **logs/** — Scrape logs

## Database tables

### listings
Your comp set. Pre-seeded with all 56 listings from your research.

### price_snapshots
Every price data point. Fields:
- `listing_id` — which comp
- `scrape_date` — when we scraped
- `scrape_label` — what type (weekday, weekend, high_season_3n, etc.)
- `checkin_date` — the check-in date we searched for
- `nights` — length of stay
- `nightly_rate` — price per night shown by Airbnb
- `total_price` — total if captured
- `is_available` — 1 = bookable, 0 = blocked/booked

### occupancy_snapshots
Calendar-based occupancy estimates. Fields:
- `listing_id` — which comp
- `month` — e.g. "2026-04"
- `days_available` / `days_blocked` / `total_days`
- `occupancy_pct` — blocked/total × 100

## Price matrix labels (weekly/monthly scrapes)

| Label | Check-in | Nights | Purpose |
|---|---|---|---|
| weekday_2w_3n | Tue ~2 weeks out | 3 | Base weekday rate |
| weekend_2w_3n | Fri ~2 weeks out | 3 | Weekend premium |
| weekday_2w_7n | Tue ~2 weeks out | 7 | Weekly discount rate |
| weekday_2w_30n | Tue ~2 weeks out | 30 | Monthly discount rate |
| weekday_1m_3n | Tue ~1 month out | 3 | Medium-term base |
| weekday_3m_3n | Tue ~3 months out | 3 | Far-out pricing |
| high_season_3n | Jul 14 | 3 | Peak season rate |
| high_season_7n | Jul 14 | 7 | Peak weekly rate |
| low_season_3n | Oct 15 | 3 | Low season floor |
| low_season_7n | Oct 15 | 7 | Low season weekly |

## Handling Airbnb blocking

If you start getting empty results or errors:

1. **Increase delays** — Edit `MIN_DELAY` and `MAX_DELAY` in scraper.py (default 4–9 seconds)
2. **Reduce daily volume** — Comment out Tier 3 comps in the COMP_SET to reduce requests
3. **Add proxy rotation** — Add a proxy service like BrightData or ScraperAPI
4. **Run at off-peak hours** — 4–6am Bali time tends to get blocked less
5. **Rotate user agents** — The script uses one UA; add rotation if needed

## Adding/removing comps

Edit the `COMP_SET` list in scraper.py. Each entry needs:
```python
{"id": "AIRBNB_LISTING_ID", "name": "Display Name", "seg": "3bed", "tier": 1}
```
The listing ID is the number in the Airbnb URL: airbnb.com/rooms/**7816774**

## Running on a cheap cloud server

If you don't want to leave your laptop running, deploy to a $5/month server:

1. **DigitalOcean Droplet** ($6/mo, 1GB RAM, Ubuntu) or **Hetzner** (€3.79/mo)
2. SSH in, install Python 3.11+, pip install playwright, playwright install chromium --with-deps
3. Clone your scraper files
4. Set up cron
5. Periodically run `python scraper.py export` and download the CSVs, or set up a simple web dashboard
