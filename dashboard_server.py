#!/usr/bin/env python3
"""
Berawa Comp Intelligence — Dashboard Server
============================================
FastAPI backend + static file serving for the React frontend.

Dev:   npm run dev:all   (starts both uvicorn + vite in parallel)
Prod:  python3 dashboard_server.py  (serves built React from dist/)
"""

import os
import sqlite3
from collections import defaultdict
from contextlib import asynccontextmanager, contextmanager
from datetime import date, timedelta
from pathlib import Path
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

DB_PATH = Path(__file__).parent / "comp_data.db"
DIST_PATH = Path(__file__).parent / "dist"
API_KEY = os.environ.get("API_KEY", "dev-key")
IS_VERCEL = bool(os.environ.get("VERCEL"))

# ─────────────────────────────────────────────────────
# Startup
# ─────────────────────────────────────────────────────

def _run_startup_migrations():
    """Create performance indexes if missing. Skip on Vercel (read-only FS)."""
    if IS_VERCEL:
        return
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_ps_label_date "
        "ON price_snapshots(scrape_label, scrape_date)"
    )
    conn.commit()
    conn.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    if DB_PATH.exists():
        _run_startup_migrations()
    yield


# ─────────────────────────────────────────────────────
# App
# ─────────────────────────────────────────────────────

app = FastAPI(title="Berawa Comp Intelligence", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_headers=["Authorization", "Content-Type"],
    allow_methods=["GET"],
)


# ─────────────────────────────────────────────────────
# Auth
# ─────────────────────────────────────────────────────

def verify_token(request: Request):
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing auth token")
    if auth[7:] != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid token")


# ─────────────────────────────────────────────────────
# DB helpers
# ─────────────────────────────────────────────────────

@contextmanager
def get_db():
    if IS_VERCEL:
        # Read-only URI connection — Vercel filesystem is immutable
        conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True, check_same_thread=False)
    else:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL")
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def _filter_clause(segment: Optional[str], tier: Optional[str]):
    """Return (WHERE additions string, params list) for segment/tier filters."""
    clauses, params = [], []
    if segment:
        clauses.append("l.segment = ?")
        params.append(segment)
    if tier:
        clauses.append("l.tier = ?")
        params.append(int(tier))
    extra = (" AND " + " AND ".join(clauses)) if clauses else ""
    return extra, params


# ─────────────────────────────────────────────────────
# Paired % helpers
# ─────────────────────────────────────────────────────

def _fetch_weekday_prices(conn, segment=None, tier=None):
    """
    Return {date: {segment: {listing_id: rate}}} for all weekday scrapes.
    Used to compute paired cohort % without re-querying.
    """
    extra, params = _filter_clause(segment, tier)
    c = conn.cursor()
    c.execute(f"""
        SELECT p.scrape_date, p.listing_id, l.segment, p.nightly_rate
        FROM price_snapshots p
        JOIN listings l ON p.listing_id = l.listing_id
        WHERE p.scrape_label = 'weekday' AND p.nightly_rate IS NOT NULL
        {extra}
        ORDER BY p.scrape_date
    """, params)
    data: dict[str, dict[str, dict]] = defaultdict(lambda: defaultdict(dict))
    for scrape_date, listing_id, seg, rate in c.fetchall():
        data[scrape_date][seg][listing_id] = rate
    return data


def _paired_pct(rates_t0: dict, rates_t1: dict):
    """
    Compute paired cohort % change.
    rates_t0/t1: {listing_id: rate}
    Returns {pct_change, n, avg_t0, avg_t1} — pct_change is None if cohort < 2.
    """
    cohort = set(rates_t0) & set(rates_t1)
    if len(cohort) < 2:
        return {"pct_change": None, "n": len(cohort), "avg_t0": None, "avg_t1": None}
    pcts = [(rates_t1[lid] - rates_t0[lid]) / rates_t0[lid] * 100 for lid in cohort]
    avg_t0 = sum(rates_t0[lid] for lid in cohort) / len(cohort)
    avg_t1 = sum(rates_t1[lid] for lid in cohort) / len(cohort)
    return {
        "pct_change": round(sum(pcts) / len(pcts), 1),
        "n": len(cohort),
        "avg_t0": round(avg_t0),
        "avg_t1": round(avg_t1),
    }


# ─────────────────────────────────────────────────────
# API endpoints — declared BEFORE the SPA catch-all
# ─────────────────────────────────────────────────────

@app.get("/api/cockpit")
def get_cockpit(
    segment: Optional[str] = None,
    tier: Optional[str] = None,
    _=Depends(verify_token),
):
    """
    Daily briefing: market rate KPIs, WoW paired %, occupancy pulse, alerts, scrape health.
    """
    today = date.today().isoformat()
    lookahead = (date.today() + timedelta(days=14)).isoformat()

    with get_db() as conn:
        c = conn.cursor()

        # ── Latest scrape date ──
        c.execute(
            "SELECT MAX(scrape_date) FROM price_snapshots WHERE scrape_label='weekday'"
        )
        latest = c.fetchone()[0]

        # ── Market rate snapshot (point-in-time, no stat correction needed) ──
        market_rates = {}
        if latest:
            extra, params = _filter_clause(segment, tier)
            c.execute(f"""
                SELECT l.segment,
                    ROUND(AVG(CASE WHEN p.scrape_label='weekday' THEN p.nightly_rate END)) as wd,
                    ROUND(AVG(CASE WHEN p.scrape_label='weekend' THEN p.nightly_rate END)) as we,
                    COUNT(DISTINCT p.listing_id) as n
                FROM price_snapshots p
                JOIN listings l ON p.listing_id = l.listing_id
                WHERE p.scrape_date = ? AND p.nightly_rate IS NOT NULL
                  AND p.scrape_label IN ('weekday','weekend') {extra}
                GROUP BY l.segment
            """, [latest] + params)
            for row in c.fetchall():
                market_rates[row[0]] = {
                    "weekday": int(row[1]) if row[1] else None,
                    "weekend": int(row[2]) if row[2] else None,
                    "n": row[3],
                    "wow_pct": None,  # filled below
                }

        # ── WoW paired % ──
        if latest:
            wd_data = _fetch_weekday_prices(conn, segment, tier)
            dates = sorted(wd_data.keys())
            if len(dates) >= 2:
                t0, t1 = dates[-2], dates[-1]
                for seg in list(market_rates.keys()):
                    if seg in wd_data.get(t0, {}) and seg in wd_data.get(t1, {}):
                        r = _paired_pct(wd_data[t0][seg], wd_data[t1][seg])
                        if seg in market_rates:
                            market_rates[seg]["wow_pct"] = r["pct_change"]
                            market_rates[seg]["wow_n"] = r["n"]

        # ── Occupancy pulse ──
        c.execute("""
            SELECT ROUND(SUM(o.is_booked) * 100.0 / COUNT(*), 1)
            FROM occupancy_checks o
            JOIN listings l ON o.listing_id = l.listing_id
            WHERE l.tier = 1 AND o.check_date >= ?
        """, [(date.today() - timedelta(days=7)).isoformat()])
        occ_row = c.fetchone()
        occupancy_pulse = {"avg_occ_pct": occ_row[0] if occ_row[0] is not None else None}

        # ── Alerts ──
        alerts = []

        # Price drops > 20% WoW (T1 comps)
        if latest and len(dates) >= 2:
            t0, t1 = dates[-2], dates[-1]
            extra2, params2 = _filter_clause(segment, "1" if not tier else tier)
            c.execute(f"""
                SELECT l.listing_id, l.name, l.segment,
                    p0.nightly_rate as r0, p1.nightly_rate as r1
                FROM listings l
                JOIN price_snapshots p0 ON p0.listing_id = l.listing_id
                    AND p0.scrape_date = ? AND p0.scrape_label = 'weekday'
                JOIN price_snapshots p1 ON p1.listing_id = l.listing_id
                    AND p1.scrape_date = ? AND p1.scrape_label = 'weekday'
                WHERE p0.nightly_rate IS NOT NULL AND p1.nightly_rate IS NOT NULL
                  {extra2}
                HAVING (r1 - r0) / r0 * 100 < -20
            """, [t0, t1] + params2)
            for row in c.fetchall():
                pct = round((row["r1"] - row["r0"]) / row["r0"] * 100, 1)
                alerts.append({
                    "type": "price_drop",
                    "severity": "warning",
                    "message": f"{(row['name'] or row['listing_id'])[:35]} dropped {abs(pct):.0f}% WoW (${round(row['r0'])}→${round(row['r1'])})",
                    "listing_id": row["listing_id"],
                })

        # Dark listings: no price data in last 7 days
        cutoff = (date.today() - timedelta(days=7)).isoformat()
        c.execute(f"""
            SELECT l.listing_id, l.name, l.segment, MAX(p.scrape_date) as last_seen
            FROM listings l
            LEFT JOIN price_snapshots p ON p.listing_id = l.listing_id
                AND p.scrape_label = 'weekday' AND p.nightly_rate IS NOT NULL
            GROUP BY l.listing_id
            HAVING last_seen IS NULL OR last_seen < ?
            ORDER BY last_seen ASC NULLS FIRST
            LIMIT 5
        """, [cutoff])
        for row in c.fetchall():
            last = row["last_seen"] or "never"
            alerts.append({
                "type": "dark_listing",
                "severity": "info",
                "message": f"{(row['name'] or row['listing_id'])[:35]} — last seen {last}",
                "listing_id": row["listing_id"],
            })

        # Upcoming Bali events
        c.execute("""
            SELECT event_date, name, event_type FROM bali_events
            WHERE event_date BETWEEN ? AND ?
            ORDER BY event_date
        """, [today, lookahead])
        for row in c.fetchall():
            alerts.append({
                "type": "event",
                "severity": "info",
                "message": f"{row['event_date']}: {row['name']}",
                "event_type": row["event_type"],
            })

        # ── Scrape health ──
        c.execute("""
            SELECT scrape_date, COUNT(DISTINCT listing_id) as n
            FROM price_snapshots
            WHERE scrape_label = 'weekday' AND nightly_rate IS NOT NULL
            GROUP BY scrape_date
            ORDER BY scrape_date DESC LIMIT 2
        """)
        health_rows = c.fetchall()
        scrape_health = {"last_scrape": None, "ok_count": 0, "stale": True}
        if health_rows:
            last_row = health_rows[0]
            scrape_health = {
                "last_scrape": last_row["scrape_date"],
                "ok_count": last_row["n"],
                "stale": last_row["scrape_date"] < (date.today() - timedelta(days=1)).isoformat(),
            }

        return {
            "scrape_date": latest,
            "market_rates": market_rates,
            "occupancy_pulse": occupancy_pulse,
            "alerts": alerts,
            "scrape_health": scrape_health,
        }


@app.get("/api/overview")
def get_overview(
    segment: Optional[str] = None,
    tier: Optional[str] = None,
    _=Depends(verify_token),
):
    """Market snapshot table: segment × tier grid for the latest scrape."""
    with get_db() as conn:
        c = conn.cursor()
        c.execute(
            "SELECT MAX(scrape_date) FROM price_snapshots WHERE scrape_label='weekday'"
        )
        latest = c.fetchone()[0]
        if not latest:
            return {"date": None, "segments": {}}

        extra, params = _filter_clause(segment, tier)
        c.execute(f"""
            SELECT l.segment, l.tier,
                ROUND(AVG(CASE WHEN p.scrape_label='weekday' THEN p.nightly_rate END)) as wd,
                ROUND(AVG(CASE WHEN p.scrape_label='weekend' THEN p.nightly_rate END)) as we,
                COUNT(DISTINCT CASE WHEN p.scrape_label='weekday' THEN p.listing_id END) as n
            FROM price_snapshots p
            JOIN listings l ON p.listing_id = l.listing_id
            WHERE p.scrape_date = ? AND p.nightly_rate IS NOT NULL {extra}
            GROUP BY l.segment, l.tier
            ORDER BY l.segment, l.tier
        """, [latest] + params)

        result = defaultdict(dict)
        for row in c.fetchall():
            result[row[0]][row[1]] = {
                "weekday": int(row[2]) if row[2] else None,
                "weekend": int(row[3]) if row[3] else None,
                "spread": round((row[3] - row[2]) / row[2] * 100) if row[2] and row[3] else None,
                "count": row[4],
            }
        return {"date": latest, "segments": dict(result)}


@app.get("/api/trends")
def get_trends(
    segment: Optional[str] = None,
    tier: Optional[str] = None,
    _=Depends(verify_token),
):
    """
    Paired % change time series.
    Each point = paired cohort % change vs previous scrape date.
    Also returns absolute T1 weekday avg series (point-in-time, labeled as such).
    """
    with get_db() as conn:
        wd_data = _fetch_weekday_prices(conn, segment, tier)
        dates = sorted(wd_data.keys())

        if len(dates) < 2:
            return {"pct_series": [], "rate_series": [], "message": "Need 2+ daily scrapes to show trends."}

        segs = [segment] if segment else ["3bed", "4bed", "6bed"]

        pct_series = []   # [{date, 3bed: pct, 4bed: pct, ...}]
        rate_series = []  # [{date, 3bed: avg_rate, ...}]

        for i in range(1, len(dates)):
            t0, t1 = dates[i - 1], dates[i]
            pct_entry = {"date": t1}
            rate_entry = {"date": t1}

            for seg in segs:
                r0 = wd_data[t0].get(seg, {})
                r1 = wd_data[t1].get(seg, {})
                p = _paired_pct(r0, r1)
                pct_entry[seg] = p["pct_change"]
                rate_entry[seg] = p["avg_t1"]

            pct_series.append(pct_entry)
            rate_series.append(rate_entry)

        # Also prepend the first date's absolute rates for the rate chart
        first = {"date": dates[0]}
        for seg in segs:
            r = wd_data[dates[0]].get(seg, {})
            first[seg] = round(sum(r.values()) / len(r)) if r else None
        rate_series.insert(0, first)

        return {"pct_series": pct_series, "rate_series": rate_series}


@app.get("/api/occupancy")
def get_occupancy(
    segment: Optional[str] = None,
    tier: Optional[str] = None,
    _=Depends(verify_token),
):
    """Occupancy data from occupancy_checks table."""
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT MIN(check_date), MAX(check_date) FROM occupancy_checks")
        row = c.fetchone()
        if not row or not row[0]:
            return {"range": None, "by_segment": {}, "by_comp": []}

        extra, params = _filter_clause(segment, tier or "1")

        # Daily occupancy % by segment
        c.execute(f"""
            SELECT o.check_date, l.segment,
                ROUND(SUM(o.is_booked) * 100.0 / COUNT(*), 1) as occ_pct
            FROM occupancy_checks o
            JOIN listings l ON o.listing_id = l.listing_id
            WHERE 1=1 {extra}
            GROUP BY o.check_date, l.segment
            ORDER BY o.check_date
        """, params)
        by_segment = defaultdict(list)
        for row in c.fetchall():
            by_segment[row["segment"]].append({"date": row["check_date"], "pct": row["occ_pct"]})

        # Per-comp cumulative
        c.execute(f"""
            SELECT l.listing_id, l.name, l.segment, l.tier,
                SUM(o.is_booked) as booked,
                COUNT(*) as total,
                ROUND(SUM(o.is_booked) * 100.0 / COUNT(*), 1) as occ_pct
            FROM occupancy_checks o
            JOIN listings l ON o.listing_id = l.listing_id
            WHERE 1=1 {extra}
            GROUP BY l.listing_id
            ORDER BY occ_pct DESC
        """, params)
        by_comp = [dict(row) for row in c.fetchall()]

        return {
            "range": {"min": row["check_date"] if row else None, "max": None},
            "by_segment": dict(by_segment),
            "by_comp": by_comp,
        }


@app.get("/api/seasonal")
def get_seasonal(
    segment: Optional[str] = None,
    tier: Optional[str] = None,
    _=Depends(verify_token),
):
    """
    Seasonal multipliers as paired % vs each listing's own weekday baseline.
    Uses dynamic label discovery — no hardcoded seasonal label values.
    """
    with get_db() as conn:
        c = conn.cursor()
        c.execute(
            "SELECT MAX(scrape_date) FROM price_snapshots WHERE scrape_label LIKE 'seasonal_%'"
        )
        latest = c.fetchone()[0]
        if not latest:
            return {"date": None, "data": {}}

        extra, params = _filter_clause(segment, tier)

        # Weekday baselines on the same scrape date
        c.execute(f"""
            SELECT p.listing_id, p.nightly_rate
            FROM price_snapshots p
            JOIN listings l ON p.listing_id = l.listing_id
            WHERE p.scrape_label = 'weekday' AND p.scrape_date = ?
              AND p.nightly_rate IS NOT NULL {extra}
        """, [latest] + params)
        baselines = {row[0]: row[1] for row in c.fetchall()}

        # All seasonal rates on same date
        c.execute(f"""
            SELECT p.listing_id, p.scrape_label, p.nightly_rate
            FROM price_snapshots p
            JOIN listings l ON p.listing_id = l.listing_id
            WHERE p.scrape_date = ? AND p.scrape_label LIKE 'seasonal_%'
              AND p.nightly_rate IS NOT NULL {extra}
        """, [latest] + params)

        by_label: dict[str, dict] = defaultdict(dict)
        for lid, label, rate in c.fetchall():
            by_label[label][lid] = rate

        result = []
        for label in sorted(by_label):
            rates = by_label[label]
            cohort = {lid for lid in rates if lid in baselines}
            if not cohort:
                continue
            pcts = [(rates[lid] - baselines[lid]) / baselines[lid] * 100 for lid in cohort]
            result.append({
                "label": label.replace("seasonal_", ""),
                "pct_vs_baseline": round(sum(pcts) / len(pcts), 1),
                "n": len(cohort),
                "avg_seasonal": round(sum(rates[lid] for lid in cohort) / len(cohort)),
                "avg_baseline": round(sum(baselines[lid] for lid in cohort) / len(cohort)),
            })

        return {"date": latest, "data": result}


@app.get("/api/leadtime")
def get_leadtime(
    segment: Optional[str] = None,
    tier: Optional[str] = None,
    _=Depends(verify_token),
):
    """
    Leadtime analysis.
    Immediate: paired % vs nearterm_14d anchor for each horizon.
    Tracking: time series of prices for specific future dates.
    """
    with get_db() as conn:
        c = conn.cursor()
        c.execute(
            "SELECT MAX(scrape_date) FROM price_snapshots WHERE scrape_label LIKE 'leadtime_%'"
        )
        latest = c.fetchone()[0]
        if not latest:
            return {"date": None, "immediate": [], "tracking": {}}

        extra, params = _filter_clause(segment, tier)

        # Anchor: nearterm_14d rates
        c.execute(f"""
            SELECT p.listing_id, p.nightly_rate
            FROM price_snapshots p
            JOIN listings l ON p.listing_id = l.listing_id
            WHERE p.scrape_date = ? AND p.scrape_label = 'leadtime_nearterm_14d'
              AND p.nightly_rate IS NOT NULL {extra}
        """, [latest] + params)
        anchor = {row[0]: row[1] for row in c.fetchall()}

        # All leadtime rates on latest date (non-tracking)
        c.execute(f"""
            SELECT p.listing_id, p.scrape_label, p.nightly_rate
            FROM price_snapshots p
            JOIN listings l ON p.listing_id = l.listing_id
            WHERE p.scrape_date = ? AND p.scrape_label LIKE 'leadtime_%'
              AND p.scrape_label NOT LIKE '%track_%'
              AND p.nightly_rate IS NOT NULL {extra}
        """, [latest] + params)

        by_label: dict[str, dict] = defaultdict(dict)
        for lid, label, rate in c.fetchall():
            by_label[label][lid] = rate

        immediate = []
        for label in sorted(by_label):
            rates = by_label[label]
            cohort = {lid for lid in rates if lid in anchor} if anchor else set(rates.keys())
            if not cohort:
                continue
            if anchor and cohort:
                pcts = [(rates[lid] - anchor[lid]) / anchor[lid] * 100 for lid in cohort]
                pct_vs_anchor = round(sum(pcts) / len(pcts), 1)
            else:
                pct_vs_anchor = None
            immediate.append({
                "label": label.replace("leadtime_", ""),
                "avg_rate": round(sum(rates[lid] for lid in cohort) / len(cohort)),
                "pct_vs_anchor": pct_vs_anchor,
                "n": len(cohort),
            })

        # Tracking time series (avg — composition is fixed for specific future dates)
        tracking = {}
        c.execute(f"""
            SELECT p.scrape_label, p.scrape_date,
                ROUND(AVG(p.nightly_rate)) as avg_rate, COUNT(*) as n
            FROM price_snapshots p
            JOIN listings l ON p.listing_id = l.listing_id
            WHERE p.scrape_label LIKE '%track_%' AND p.nightly_rate IS NOT NULL {extra}
            GROUP BY p.scrape_label, p.scrape_date
            ORDER BY p.scrape_label, p.scrape_date
        """, params)
        for row in c.fetchall():
            key = row["scrape_label"].replace("leadtime_", "")
            if key not in tracking:
                tracking[key] = []
            tracking[key].append({"date": row["scrape_date"], "avg_rate": row["avg_rate"], "n": row["n"]})

        return {"date": latest, "immediate": immediate, "tracking": tracking}


@app.get("/api/discounts")
def get_discounts(
    segment: Optional[str] = None,
    tier: Optional[str] = None,
    _=Depends(verify_token),
):
    """Per-listing discount analysis: 3n vs 7n vs 28n."""
    with get_db() as conn:
        c = conn.cursor()
        c.execute(
            "SELECT MAX(scrape_date) FROM price_snapshots "
            "WHERE scrape_label IN ('3n_baseline','7n_weekly','28n_monthly')"
        )
        latest = c.fetchone()[0]
        if not latest:
            return {"date": None, "data": {}}

        extra, params = _filter_clause(segment, tier)
        c.execute(f"""
            SELECT l.listing_id, l.name, l.segment, l.tier,
                MAX(CASE WHEN p.scrape_label='3n_baseline' THEN p.nightly_rate END) as r3n,
                MAX(CASE WHEN p.scrape_label='7n_weekly'   THEN p.nightly_rate END) as r7n,
                MAX(CASE WHEN p.scrape_label='28n_monthly' THEN p.nightly_rate END) as r28n
            FROM price_snapshots p
            JOIN listings l ON p.listing_id = l.listing_id
            WHERE p.scrape_date = ?
              AND p.scrape_label IN ('3n_baseline','7n_weekly','28n_monthly')
              AND p.nightly_rate IS NOT NULL {extra}
            GROUP BY l.listing_id
            HAVING r3n IS NOT NULL
            ORDER BY l.segment, l.tier, r3n DESC
        """, [latest] + params)

        result: dict[str, list] = defaultdict(list)
        for row in c.fetchall():
            r3n, r7n, r28n = row["r3n"], row["r7n"], row["r28n"]
            result[row["segment"]].append({
                "listing_id": row["listing_id"],
                "name": (row["name"] or row["listing_id"])[:45],
                "tier": row["tier"],
                "rate_3n": round(r3n),
                "rate_7n": round(r7n) if r7n else None,
                "rate_28n": round(r28n) if r28n else None,
                "disc_7n_pct": round((1 - r7n / r3n) * 100) if r3n and r7n else None,
                "disc_28n_pct": round((1 - r28n / r3n) * 100) if r3n and r28n else None,
            })

        return {"date": latest, "data": dict(result)}


@app.get("/api/comps")
def get_comps(
    segment: Optional[str] = None,
    tier: Optional[str] = None,
    _=Depends(verify_token),
):
    """Per-comp current rates, metadata, and week-on-week change."""
    with get_db() as conn:
        c = conn.cursor()
        c.execute(
            "SELECT MAX(scrape_date) FROM price_snapshots WHERE scrape_label='weekday'"
        )
        latest = c.fetchone()[0]
        if not latest:
            return {"date": None, "comps": []}

        extra, params = _filter_clause(segment, tier)
        c.execute(f"""
            SELECT l.listing_id, l.name, l.segment, l.tier,
                l.rating, l.review_count, l.min_stay, l.url,
                MAX(CASE WHEN p.scrape_label='weekday' THEN p.nightly_rate END) as weekday,
                MAX(CASE WHEN p.scrape_label='weekend' THEN p.nightly_rate END) as weekend
            FROM listings l
            LEFT JOIN price_snapshots p ON l.listing_id = p.listing_id AND p.scrape_date = ?
            WHERE 1=1 {extra}
            GROUP BY l.listing_id
            ORDER BY l.segment, l.tier, weekday DESC
        """, [latest] + params)
        comps = [dict(row) for row in c.fetchall()]

        # Attach WoW % for each comp
        wd_data = _fetch_weekday_prices(conn, segment, tier)
        dates = sorted(wd_data.keys())
        wow_map: dict[str, Optional[float]] = {}
        if len(dates) >= 2:
            t0, t1 = dates[-2], dates[-1]
            for seg_rates in wd_data[t0].values():
                for lid, r0 in seg_rates.items():
                    r1_dict = {k: v for seg_r in wd_data[t1].values() for k, v in seg_r.items()}
                    if lid in r1_dict:
                        wow_map[lid] = round((r1_dict[lid] - r0) / r0 * 100, 1)

        for comp in comps:
            comp["wow_pct"] = wow_map.get(comp["listing_id"])
            if comp["weekday"]:
                comp["weekday"] = round(comp["weekday"])
            if comp["weekend"]:
                comp["weekend"] = round(comp["weekend"])

        return {"date": latest, "comps": comps}


@app.get("/api/properties")
def get_properties(_=Depends(verify_token)):
    """Own villa data and bookings vs market comparison."""
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM my_properties ORDER BY bedrooms")
        properties = [dict(row) for row in c.fetchall()]

        for prop in properties:
            pid = prop["property_id"]
            c.execute("""
                SELECT checkin, checkout, nightly_rate, nights, platform, status
                FROM my_bookings WHERE property_id = ? AND status = 'confirmed'
                ORDER BY checkin DESC
            """, [pid])
            prop["bookings"] = [dict(r) for r in c.fetchall()]

            # Revenue pace: bookings in last 30 days created
            c.execute("""
                SELECT COUNT(*), ROUND(AVG(nightly_rate)), ROUND(SUM(nightly_rate * nights))
                FROM my_bookings
                WHERE property_id = ? AND status = 'confirmed'
                  AND checkin >= ?
            """, [pid, (date.today() - timedelta(days=30)).isoformat()])
            r = c.fetchone()
            prop["pace_30d"] = {
                "booking_count": r[0] or 0,
                "avg_rate": r[1],
                "total_revenue": r[2],
            }

        # T1 market median for comparison
        c.execute("""
            SELECT l.segment, ROUND(AVG(p.nightly_rate)) as t1_median
            FROM price_snapshots p
            JOIN listings l ON p.listing_id = l.listing_id
            WHERE l.tier = 1 AND p.scrape_label = 'weekday'
              AND p.scrape_date = (
                  SELECT MAX(scrape_date) FROM price_snapshots WHERE scrape_label='weekday'
              )
              AND p.nightly_rate IS NOT NULL
            GROUP BY l.segment
        """)
        t1_medians = {row["segment"]: row["t1_median"] for row in c.fetchall()}

        return {
            "properties": properties,
            "t1_medians": t1_medians,
            "has_data": len(properties) > 0,
        }


# ─────────────────────────────────────────────────────
# Static files + SPA fallback (AFTER all /api routes)
# ─────────────────────────────────────────────────────

if DIST_PATH.exists():
    app.mount("/assets", StaticFiles(directory=str(DIST_PATH / "assets")), name="assets")

    @app.get("/{full_path:path}")
    def spa_fallback(full_path: str):
        index = DIST_PATH / "index.html"
        if index.exists():
            return FileResponse(str(index))
        raise HTTPException(status_code=404, detail="Build not found. Run: npm run build")
else:
    @app.get("/")
    def root():
        return {"message": "API running. Build frontend with: npm run build"}


# ─────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("dashboard_server:app", host="0.0.0.0", port=5001, reload=False)
