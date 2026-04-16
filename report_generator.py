#!/usr/bin/env python3
"""
Berawa Comp Intelligence Report Generator
==========================================
Reads comp_data.db and generates a standalone HTML report with charts.

Usage:
    python report_generator.py                    # Uses comp_data.db in same directory
    python report_generator.py /path/to/comp_data.db   # Specify DB path

Output:
    comp_report_YYYY-MM-DD.html in same directory as the DB
"""

import sqlite3
import json
import sys
import os
from datetime import date, timedelta
from pathlib import Path
from collections import defaultdict


def load_chartjs():
    """Load Chart.js from local file (offline-safe) or fall back to CDN tag."""
    local = Path(__file__).parent / "chart.min.js"
    if local.exists():
        return f"<script>{local.read_text()}</script>"
    return '<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>'

# ============================================================
# DATA QUERIES
# ============================================================

def get_db_path():
    if len(sys.argv) > 1:
        return Path(sys.argv[1])
    return Path(__file__).parent / "comp_data.db"


def query_market_snapshot(conn):
    """Current T1/T2/T3 averages by segment from most recent daily scrape."""
    c = conn.cursor()

    # Find the most recent daily scrape date
    c.execute("""SELECT MAX(scrape_date) FROM price_snapshots
        WHERE scrape_label IN ('weekday', 'weekend')""")
    latest = c.fetchone()[0]
    if not latest:
        return None, None

    results = {}
    for seg in ["3bed", "4bed", "6bed"]:
        results[seg] = {}
        for tier in [1, 2, 3]:
            c.execute("""
                SELECT
                    AVG(CASE WHEN p.scrape_label='weekday' THEN p.nightly_rate END),
                    AVG(CASE WHEN p.scrape_label='weekend' THEN p.nightly_rate END),
                    COUNT(DISTINCT p.listing_id)
                FROM price_snapshots p
                JOIN listings l ON p.listing_id = l.listing_id
                WHERE l.segment=? AND l.tier=? AND p.scrape_date=?
                AND p.nightly_rate IS NOT NULL
            """, (seg, tier, latest))
            row = c.fetchone()
            if row[0]:
                results[seg][tier] = {
                    "weekday": round(row[0]),
                    "weekend": round(row[1]) if row[1] else None,
                    "spread": round((row[1] - row[0]) / row[0] * 100) if row[1] and row[0] else None,
                    "count": row[2],
                }
    return latest, results


def query_market_trends(conn):
    """T1 weekday averages over time, by segment."""
    c = conn.cursor()
    trends = {}
    for seg in ["3bed", "4bed", "6bed"]:
        c.execute("""
            SELECT p.scrape_date, AVG(p.nightly_rate)
            FROM price_snapshots p
            JOIN listings l ON p.listing_id = l.listing_id
            WHERE l.segment=? AND l.tier=1 AND p.scrape_label='weekday'
            AND p.nightly_rate IS NOT NULL
            GROUP BY p.scrape_date ORDER BY p.scrape_date
        """, (seg,))
        trends[seg] = [{"date": r[0], "avg": round(r[1])} for r in c.fetchall()]
    return trends


def query_comp_detail(conn):
    """Per-comp latest prices, rating, reviews."""
    c = conn.cursor()
    c.execute("""SELECT MAX(scrape_date) FROM price_snapshots
        WHERE scrape_label='weekday'""")
    latest = c.fetchone()[0]
    if not latest:
        return []

    c.execute("""
        SELECT l.listing_id, l.name, l.segment, l.tier, l.rating, l.review_count,
               l.min_stay, l.url,
               MAX(CASE WHEN p.scrape_label='weekday' THEN p.nightly_rate END) as weekday,
               MAX(CASE WHEN p.scrape_label='weekend' THEN p.nightly_rate END) as weekend
        FROM listings l
        LEFT JOIN price_snapshots p ON l.listing_id = p.listing_id AND p.scrape_date=?
        GROUP BY l.listing_id
        ORDER BY l.segment, l.tier, weekday DESC
    """, (latest,))

    return [dict(zip([d[0] for d in c.description], row)) for row in c.fetchall()]


def query_comp_price_history(conn):
    """Weekday price history for each T1 comp."""
    c = conn.cursor()
    c.execute("""
        SELECT p.listing_id, l.name, l.segment, p.scrape_date, p.nightly_rate
        FROM price_snapshots p
        JOIN listings l ON p.listing_id = l.listing_id
        WHERE l.tier=1 AND p.scrape_label='weekday' AND p.nightly_rate IS NOT NULL
        ORDER BY l.segment, l.name, p.scrape_date
    """)
    history = defaultdict(list)
    names = {}
    segments = {}
    for row in c.fetchall():
        lid, name, seg, dt, rate = row
        history[lid].append({"date": dt, "rate": round(rate)})
        names[lid] = name
        segments[lid] = seg
    return history, names, segments


def query_occupancy(conn):
    """Occupancy data from daily checks."""
    c = conn.cursor()

    # Get date range
    c.execute("SELECT MIN(check_date), MAX(check_date) FROM occupancy_checks")
    row = c.fetchone()
    if not row or not row[0]:
        return None

    date_range = {"min": row[0], "max": row[1]}

    # Per-segment daily occupancy (% of T1 comps booked)
    c.execute("""
        SELECT o.check_date, l.segment,
               SUM(o.is_booked) as booked,
               COUNT(*) as total,
               ROUND(SUM(o.is_booked) * 100.0 / COUNT(*), 1) as occ_pct
        FROM occupancy_checks o
        JOIN listings l ON o.listing_id = l.listing_id
        WHERE l.tier = 1
        GROUP BY o.check_date, l.segment
        ORDER BY o.check_date
    """)

    occ_by_seg = defaultdict(list)
    for row in c.fetchall():
        occ_by_seg[row[1]].append({
            "date": row[0], "booked": row[2], "total": row[3], "pct": row[4]
        })

    # Per-comp cumulative occupancy
    c.execute("""
        SELECT l.listing_id, l.name, l.segment, l.tier,
               SUM(o.is_booked) as booked_days,
               COUNT(*) as checked_days,
               ROUND(SUM(o.is_booked) * 100.0 / COUNT(*), 1) as occ_pct
        FROM occupancy_checks o
        JOIN listings l ON o.listing_id = l.listing_id
        WHERE l.tier = 1
        GROUP BY l.listing_id
        ORDER BY occ_pct DESC
    """)
    comp_occ = [dict(zip([d[0] for d in c.description], row)) for row in c.fetchall()]

    return {"range": date_range, "by_segment": dict(occ_by_seg), "by_comp": comp_occ}


def query_seasonal(conn):
    """Seasonal analysis data."""
    c = conn.cursor()
    c.execute("""SELECT MAX(scrape_date) FROM price_snapshots
        WHERE scrape_label LIKE 'seasonal_%'""")
    latest = c.fetchone()[0]
    if not latest:
        return None

    results = {}
    for seg in ["3bed", "4bed", "6bed"]:
        c.execute("""
            SELECT p.scrape_label, AVG(p.nightly_rate), COUNT(*)
            FROM price_snapshots p
            JOIN listings l ON p.listing_id = l.listing_id
            WHERE l.segment=? AND l.tier IN (1,2) AND p.scrape_date=?
            AND p.scrape_label LIKE 'seasonal_%' AND p.nightly_rate IS NOT NULL
            GROUP BY p.scrape_label ORDER BY p.scrape_label
        """, (seg, latest))
        rows = c.fetchall()
        if rows:
            results[seg] = [{"label": r[0].replace("seasonal_", ""), "avg": round(r[1]), "n": r[2]} for r in rows]

    return {"date": latest, "data": results} if results else None


def query_leadtime(conn):
    """Lead time analysis data."""
    c = conn.cursor()
    c.execute("""SELECT MAX(scrape_date) FROM price_snapshots
        WHERE scrape_label LIKE 'leadtime_%'""")
    latest = c.fetchone()[0]
    if not latest:
        return None

    # Immediate lead times
    c.execute("""
        SELECT p.scrape_label, AVG(p.nightly_rate), COUNT(*)
        FROM price_snapshots p
        JOIN listings l ON p.listing_id = l.listing_id
        WHERE l.segment='3bed' AND l.tier=1 AND p.scrape_date=?
        AND p.scrape_label LIKE 'leadtime_%' AND p.nightly_rate IS NOT NULL
        GROUP BY p.scrape_label
    """, (latest,))
    rows = c.fetchall()
    immediate = [{"label": r[0].replace("leadtime_", ""), "avg": round(r[1]), "n": r[2]} for r in rows]

    # Tracking date history
    tracking = {}
    for label_prefix in ["track_peak_jul14", "track_low_oct13"]:
        c.execute("""
            SELECT p.scrape_date, AVG(p.nightly_rate), COUNT(*)
            FROM price_snapshots p
            JOIN listings l ON p.listing_id = l.listing_id
            WHERE l.segment='3bed' AND l.tier=1
            AND p.scrape_label=? AND p.nightly_rate IS NOT NULL
            GROUP BY p.scrape_date ORDER BY p.scrape_date
        """, (f"leadtime_{label_prefix}",))
        rows = c.fetchall()
        if rows:
            tracking[label_prefix] = [{"date": r[0], "avg": round(r[1]), "n": r[2]} for r in rows]

    return {"date": latest, "immediate": immediate, "tracking": tracking} if immediate else None


def query_bali_events(conn):
    """Bali demand events from bali_events table."""
    c = conn.cursor()
    try:
        c.execute("""SELECT event_date, name, event_type, notes
            FROM bali_events ORDER BY event_date""")
        return [{"date": r[0], "name": r[1], "type": r[2], "notes": r[3]} for r in c.fetchall()]
    except Exception:
        return []


def query_discounts(conn):
    """Discount analysis: 3n/7n/28n comparisons from most recent discounts scrape."""
    c = conn.cursor()
    c.execute("""SELECT MAX(scrape_date) FROM price_snapshots
        WHERE scrape_label IN ('3n_baseline', '7n_weekly', '28n_monthly')""")
    latest = c.fetchone()[0]
    if not latest:
        return None

    results = {}
    for seg in ["3bed", "4bed", "6bed"]:
        c.execute("""
            SELECT l.name, l.tier,
                MAX(CASE WHEN p.scrape_label='3n_baseline' THEN p.nightly_rate END) as rate_3n,
                MAX(CASE WHEN p.scrape_label='7n_weekly' THEN p.nightly_rate END) as rate_7n,
                MAX(CASE WHEN p.scrape_label='28n_monthly' THEN p.nightly_rate END) as rate_28n
            FROM price_snapshots p
            JOIN listings l ON p.listing_id = l.listing_id
            WHERE l.segment=? AND p.scrape_date=?
            AND p.scrape_label IN ('3n_baseline', '7n_weekly', '28n_monthly')
            GROUP BY l.listing_id
            HAVING rate_3n IS NOT NULL
            ORDER BY l.tier, rate_3n DESC
        """, (seg, latest))
        rows = c.fetchall()
        if rows:
            results[seg] = [
                {"name": r[0], "tier": r[1],
                 "rate_3n": round(r[2]) if r[2] else None,
                 "rate_7n": round(r[3]) if r[3] else None,
                 "rate_28n": round(r[4]) if r[4] else None,
                 "disc_7n": round((1 - r[3]/r[2]) * 100) if r[2] and r[3] else None,
                 "disc_28n": round((1 - r[4]/r[2]) * 100) if r[2] and r[4] else None,
                } for r in rows
            ]

    return {"date": latest, "data": results} if results else None


def query_my_properties(conn):
    """Own property data and bookings summary."""
    c = conn.cursor()
    try:
        c.execute("SELECT * FROM my_properties ORDER BY bedrooms")
        props = [dict(zip([d[0] for d in c.description], r)) for r in c.fetchall()]
        for p in props:
            c.execute("""SELECT COUNT(*), AVG(nightly_rate), MIN(checkin), MAX(checkout)
                FROM my_bookings WHERE property_id=? AND status='confirmed'""",
                (p["property_id"],))
            row = c.fetchone()
            p["booking_count"] = row[0] or 0
            p["avg_rate"] = round(row[1]) if row[1] else None
            p["first_checkin"] = row[2]
            p["last_checkout"] = row[3]
        return props
    except Exception:
        return []


def query_stats(conn):
    """Overall DB stats."""
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM listings")
    listings = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM price_snapshots")
    snapshots = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM occupancy_checks")
    occ_checks = c.fetchone()[0]
    c.execute("SELECT MIN(scrape_date), MAX(scrape_date) FROM price_snapshots")
    row = c.fetchone()
    date_range = f"{row[0]} → {row[1]}" if row[0] else "No data"
    c.execute("SELECT COUNT(DISTINCT scrape_date) FROM price_snapshots")
    scrape_days = c.fetchone()[0]
    return {
        "listings": listings, "snapshots": snapshots, "occ_checks": occ_checks,
        "date_range": date_range, "scrape_days": scrape_days
    }


# ============================================================
# HTML GENERATION
# ============================================================

def generate_html(db_path):
    conn = sqlite3.connect(db_path)

    stats = query_stats(conn)
    latest_date, market = query_market_snapshot(conn)
    trends = query_market_trends(conn)
    comps = query_comp_detail(conn)
    history, hist_names, hist_segs = query_comp_price_history(conn)
    occupancy = query_occupancy(conn)
    seasonal = query_seasonal(conn)
    leadtime = query_leadtime(conn)
    bali_events = query_bali_events(conn)
    discounts = query_discounts(conn)
    my_props = query_my_properties(conn)

    conn.close()

    today = date.today().isoformat()
    chartjs_tag = load_chartjs()

    # Build the HTML
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Berawa Comp Report — {today}</title>
{chartjs_tag}
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
:root {{
    --bg: #0f1117;
    --surface: #1a1d27;
    --surface-2: #232735;
    --border: #2e3344;
    --text: #e4e6ef;
    --text-muted: #8b8fa3;
    --accent: #6c8cff;
    --accent-2: #45d4a8;
    --accent-3: #ff8c6c;
    --accent-4: #c78cff;
    --red: #ff6b6b;
    --green: #45d4a8;
    --yellow: #ffd06b;
}}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
    font-family: 'DM Sans', sans-serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.6;
    padding: 2rem;
    max-width: 1400px;
    margin: 0 auto;
}}
h1 {{
    font-size: 1.8rem;
    font-weight: 700;
    margin-bottom: 0.25rem;
    letter-spacing: -0.03em;
}}
h2 {{
    font-size: 1.2rem;
    font-weight: 600;
    color: var(--accent);
    margin: 2.5rem 0 1rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid var(--border);
    letter-spacing: -0.02em;
}}
h3 {{
    font-size: 0.95rem;
    font-weight: 600;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin: 1.5rem 0 0.75rem;
}}
.subtitle {{
    color: var(--text-muted);
    font-size: 0.9rem;
    margin-bottom: 2rem;
}}
.stat-row {{
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
    margin-bottom: 1.5rem;
}}
.stat {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 0.75rem 1rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.8rem;
}}
.stat span {{ color: var(--text-muted); font-family: 'DM Sans', sans-serif; }}
.card {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 1.25rem;
    margin-bottom: 1rem;
}}
.grid-3 {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(380px, 1fr)); gap: 1rem; }}
.grid-2 {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(500px, 1fr)); gap: 1rem; }}
.tier-badge {{
    display: inline-block;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 0.7rem;
    font-weight: 600;
    font-family: 'JetBrains Mono', monospace;
}}
.tier-1 {{ background: rgba(108,140,255,0.15); color: var(--accent); }}
.tier-2 {{ background: rgba(199,140,255,0.15); color: var(--accent-4); }}
.tier-3 {{ background: rgba(139,143,163,0.15); color: var(--text-muted); }}
table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 0.85rem;
}}
th {{
    text-align: left;
    padding: 0.5rem 0.75rem;
    border-bottom: 1px solid var(--border);
    color: var(--text-muted);
    font-weight: 500;
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}}
td {{
    padding: 0.5rem 0.75rem;
    border-bottom: 1px solid var(--border);
}}
td.mono {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.8rem;
}}
tr:hover {{ background: var(--surface-2); }}
a {{ color: var(--accent); text-decoration: none; }}
a:hover {{ text-decoration: underline; }}
.chart-wrap {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 1.25rem;
    margin-bottom: 1rem;
}}
.chart-wrap canvas {{ max-height: 300px; }}
.empty {{ color: var(--text-muted); font-style: italic; padding: 2rem; text-align: center; }}
.market-card {{
    text-align: center;
}}
.market-card .price {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.8rem;
    font-weight: 700;
}}
.market-card .label {{
    color: var(--text-muted);
    font-size: 0.8rem;
    margin-top: 0.25rem;
}}
.market-card .detail {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.8rem;
    color: var(--text-muted);
    margin-top: 0.5rem;
}}
.occ-bar {{
    display: flex;
    align-items: center;
    gap: 0.5rem;
}}
.occ-bar-inner {{
    height: 14px;
    border-radius: 3px;
    background: var(--accent);
    transition: width 0.3s;
}}
.occ-bar-track {{
    flex: 1;
    height: 14px;
    border-radius: 3px;
    background: var(--surface-2);
    overflow: hidden;
}}
@media (max-width: 768px) {{
    body {{ padding: 1rem; }}
    .grid-3 {{ grid-template-columns: 1fr; }}
    .grid-2 {{ grid-template-columns: 1fr; }}
}}
</style>
</head>
<body>

<h1>Berawa Comp Intelligence</h1>
<p class="subtitle">Generated {today} &middot; Data: {stats['date_range']} &middot; {stats['scrape_days']} scrape days &middot; {stats['snapshots']:,} price points &middot; {stats['occ_checks']:,} occupancy checks</p>

"""

    # ========== MARKET OVERVIEW ==========
    html += '<h2>Market Overview</h2>\n'

    if market:
        for seg in ["3bed", "4bed", "6bed"]:
            if seg not in market or not market[seg]:
                continue
            seg_label = seg.replace("bed", "-Bed")
            html += f'<h3>{seg_label}</h3>\n<div class="grid-3">\n'
            for tier in [1, 2, 3]:
                if tier not in market[seg]:
                    continue
                d = market[seg][tier]
                tier_label = {1: "T1 Direct", 2: "T2 Aspirational", 3: "T3 Floor"}[tier]
                tier_cls = f"tier-{tier}"
                wkend = f"Wkend ${d['weekend']}" if d['weekend'] else "—"
                spread = f"+{d['spread']}%" if d['spread'] and d['spread'] > 0 else ""
                html += f"""<div class="card market-card">
    <span class="tier-badge {tier_cls}">{tier_label}</span>
    <div class="price" style="margin-top:0.5rem">${d['weekday']}</div>
    <div class="label">weekday avg · {d['count']} comps</div>
    <div class="detail">{wkend} {spread}</div>
</div>\n"""
            html += '</div>\n'
    else:
        html += '<p class="empty">No daily data yet. Run: python scraper_v2.py daily</p>\n'

    # ========== MARKET TRENDS CHART ==========
    html += '<h2>Market Trends</h2>\n'
    if any(trends.get(s) for s in ["3bed", "4bed", "6bed"]):
        html += """<div class="chart-wrap"><canvas id="trendChart"></canvas></div>
<script>
new Chart(document.getElementById('trendChart'), {
    type: 'line',
    data: {
        datasets: [
"""
        colors = {"3bed": "#6c8cff", "4bed": "#45d4a8", "6bed": "#ff8c6c"}
        labels = {"3bed": "3-Bed T1", "4bed": "4-Bed T1", "6bed": "6-Bed T1"}
        for seg in ["3bed", "4bed", "6bed"]:
            if trends.get(seg):
                points = json.dumps([{"x": p["date"], "y": p["avg"]} for p in trends[seg]])
                html += f"""            {{
                label: '{labels[seg]}',
                data: {points},
                borderColor: '{colors[seg]}',
                backgroundColor: '{colors[seg]}22',
                fill: false,
                tension: 0.3,
                pointRadius: 3,
                borderWidth: 2,
            }},
"""
        html += """        ]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
            x: { type: 'category', grid: { color: '#2e334422' }, ticks: { color: '#8b8fa3', font: { size: 11 } } },
            y: { grid: { color: '#2e334444' }, ticks: { color: '#8b8fa3', callback: v => '$' + v } }
        },
        plugins: {
            legend: { labels: { color: '#e4e6ef', usePointStyle: true, padding: 20 } },
            tooltip: { callbacks: { label: ctx => ctx.dataset.label + ': $' + ctx.parsed.y } }
        }
    }
});
</script>
"""
    else:
        html += '<p class="empty">Need 2+ daily scrapes to show trends.</p>\n'

    # ========== BALI EVENTS ==========
    html += '<h2>Bali Demand Calendar</h2>\n'
    if bali_events:
        type_colors = {"cultural": "#c78cff", "peak": "#ffd06b", "demand": "#45d4a8",
                       "national": "#ff8c6c", None: "#8b8fa3"}
        html += '<div class="card"><table>\n'
        html += '<tr><th>Date</th><th>Event</th><th>Type</th><th>Notes</th></tr>\n'
        for e in bali_events:
            color = type_colors.get(e["type"], "#8b8fa3")
            html += f'<tr><td class="mono">{e["date"]}</td>'
            html += f'<td><strong>{e["name"]}</strong></td>'
            html += f'<td><span style="color:{color};font-size:0.75rem;font-weight:600;text-transform:uppercase">{e["type"] or "—"}</span></td>'
            html += f'<td style="color:var(--text-muted);font-size:0.8rem">{e["notes"] or ""}</td></tr>\n'
        html += '</table></div>\n'
    else:
        html += '<p class="empty">No events seeded yet. Run daily scrape to seed Bali events.</p>\n'

    # ========== COMP DETAIL TABLE ==========
    html += '<h2>Comp Detail</h2>\n'
    if comps:
        for seg in ["3bed", "4bed", "6bed"]:
            seg_comps = [c for c in comps if c["segment"] == seg]
            if not seg_comps:
                continue
            seg_label = seg.replace("bed", "-Bed")
            html += f'<h3>{seg_label}</h3>\n<div class="card"><table>\n'
            html += '<tr><th>Listing</th><th>Tier</th><th>Rating</th><th>Reviews</th><th>Min Stay</th><th>Weekday</th><th>Weekend</th></tr>\n'
            for c in seg_comps:
                tier_cls = f"tier-{c['tier']}"
                name_short = (c['name'] or '?')[:45]
                url = c.get('url', '#')
                rating = f"{c['rating']:.2f}" if c['rating'] else "—"
                reviews = str(c['review_count'] or "—")
                minstay = f"{c['min_stay']}n" if c['min_stay'] else "—"
                wd = f"${c['weekday']:.0f}" if c['weekday'] else "—"
                we = f"${c['weekend']:.0f}" if c['weekend'] else "—"
                html += f'<tr><td><a href="{url}" target="_blank">{name_short}</a></td>'
                html += f'<td><span class="tier-badge {tier_cls}">T{c["tier"]}</span></td>'
                html += f'<td class="mono">{rating}</td><td class="mono">{reviews}</td>'
                html += f'<td class="mono">{minstay}</td><td class="mono">{wd}</td><td class="mono">{we}</td></tr>\n'
            html += '</table></div>\n'
    else:
        html += '<p class="empty">No comp data yet.</p>\n'

    # ========== PRICE HISTORY CHARTS ==========
    html += '<h2>Price History (T1 Comps)</h2>\n'
    chart_id = 0  # global counter for unique canvas IDs — initialized here, used in all chart sections
    if history:
        for seg in ["3bed", "4bed", "6bed"]:
            seg_lids = [lid for lid, s in hist_segs.items() if s == seg]
            if not seg_lids:
                continue
            seg_label = seg.replace("bed", "-Bed")
            chart_id += 1
            html += f'<h3>{seg_label}</h3>\n<div class="chart-wrap"><canvas id="hist{chart_id}"></canvas></div>\n'
            html += f'<script>\nnew Chart(document.getElementById("hist{chart_id}"), {{\n'
            html += '    type: "line",\n    data: { datasets: [\n'

            palette = ["#6c8cff","#45d4a8","#ff8c6c","#c78cff","#ffd06b","#ff6b6b",
                       "#6bffd0","#ff6bab","#8cbaff","#d4ff6b","#6baaff","#ffab6b","#ab6bff"]
            for idx, lid in enumerate(seg_lids):
                if lid not in history:
                    continue
                points = json.dumps([{"x": p["date"], "y": p["rate"]} for p in history[lid]])
                color = palette[idx % len(palette)]
                name_esc = hist_names[lid].replace("'", "\\'")[:30]
                html += f"""        {{
            label: '{name_esc}',
            data: {points},
            borderColor: '{color}',
            fill: false, tension: 0.3, pointRadius: 2, borderWidth: 1.5,
        }},\n"""

            html += """    ]},
    options: {
        responsive: true, maintainAspectRatio: false,
        scales: {
            x: { type: 'category', grid: { color: '#2e334422' }, ticks: { color: '#8b8fa3', font: { size: 10 } } },
            y: { grid: { color: '#2e334444' }, ticks: { color: '#8b8fa3', callback: v => '$' + v } }
        },
        plugins: {
            legend: { labels: { color: '#e4e6ef', usePointStyle: true, padding: 12, font: { size: 10 } } },
            tooltip: { callbacks: { label: ctx => ctx.dataset.label + ': $' + ctx.parsed.y } }
        }
    }
});\n</script>\n"""
    else:
        html += '<p class="empty">Need 2+ daily scrapes to show history.</p>\n'

    # ========== OCCUPANCY ==========
    html += '<h2>Occupancy</h2>\n'
    if occupancy:
        r = occupancy["range"]
        html += f'<p style="color:var(--text-muted);font-size:0.85rem;margin-bottom:1rem">Tracking period: {r["min"]} → {r["max"]}</p>\n'

        # Occupancy trend chart
        if any(occupancy["by_segment"].get(s) for s in ["3bed", "4bed", "6bed"]):
            html += '<div class="chart-wrap"><canvas id="occChart"></canvas></div>\n'
            html += '<script>\nnew Chart(document.getElementById("occChart"), {\n'
            html += '    type: "line",\n    data: { datasets: [\n'
            colors = {"3bed": "#6c8cff", "4bed": "#45d4a8", "6bed": "#ff8c6c"}
            for seg in ["3bed", "4bed", "6bed"]:
                if seg not in occupancy["by_segment"]:
                    continue
                points = json.dumps([{"x": p["date"], "y": p["pct"]} for p in occupancy["by_segment"][seg]])
                seg_label = seg.replace("bed", "-Bed") + " T1"
                html += f"""        {{
            label: '{seg_label}',
            data: {points},
            borderColor: '{colors[seg]}',
            fill: false, tension: 0.3, pointRadius: 3, borderWidth: 2,
        }},\n"""
            html += """    ]},
    options: {
        responsive: true, maintainAspectRatio: false,
        scales: {
            x: { type: 'category', grid: { color: '#2e334422' }, ticks: { color: '#8b8fa3', font: { size: 10 } } },
            y: { min: 0, max: 100, grid: { color: '#2e334444' }, ticks: { color: '#8b8fa3', callback: v => v + '%' } }
        },
        plugins: {
            legend: { labels: { color: '#e4e6ef', usePointStyle: true, padding: 20 } },
            tooltip: { callbacks: { label: ctx => ctx.dataset.label + ': ' + ctx.parsed.y + '%' } }
        }
    }
});\n</script>\n"""

        # Per-comp occupancy bars
        if occupancy["by_comp"]:
            html += '<h3>Per-Comp Occupancy (T1)</h3>\n<div class="card"><table>\n'
            html += '<tr><th>Listing</th><th>Segment</th><th style="width:40%">Occupancy</th><th>Rate</th></tr>\n'
            for c in occupancy["by_comp"]:
                name = (c["name"] or "?")[:40]
                pct = c["occ_pct"]
                color = "#45d4a8" if pct >= 70 else "#ffd06b" if pct >= 50 else "#ff6b6b"
                html += f'<tr><td>{name}</td><td>{c["segment"]}</td>'
                html += f'<td><div class="occ-bar"><div class="occ-bar-track"><div class="occ-bar-inner" style="width:{pct}%;background:{color}"></div></div>'
                html += f'<span class="mono" style="font-size:0.8rem;min-width:3rem">{pct}%</span></div></td>'
                html += f'<td class="mono">{c["booked_days"]}/{c["checked_days"]}d</td></tr>\n'
            html += '</table></div>\n'
    else:
        html += '<p class="empty">No occupancy data yet. Run daily scrapes for 7+ days.</p>\n'

    # ========== SEASONAL ==========
    html += '<h2>Seasonal Analysis</h2>\n'
    if seasonal:
        html += f'<p style="color:var(--text-muted);font-size:0.85rem;margin-bottom:1rem">From scrape: {seasonal["date"]}</p>\n'
        for seg in ["3bed", "4bed", "6bed"]:
            if seg not in seasonal["data"]:
                continue
            seg_label = seg.replace("bed", "-Bed")
            chart_id += 1
            data = seasonal["data"][seg]
            labels = json.dumps([d["label"] for d in data])
            values = json.dumps([d["avg"] for d in data])
            html += f'<h3>{seg_label} (T1+T2)</h3>\n<div class="chart-wrap"><canvas id="season{chart_id}"></canvas></div>\n'
            html += f"""<script>
new Chart(document.getElementById("season{chart_id}"), {{
    type: 'bar',
    data: {{
        labels: {labels},
        datasets: [{{ label: 'Avg nightly rate', data: {values},
            backgroundColor: ['#6c8cff44','#6c8cff44','#45d4a844','#45d4a888','#ff6b6b44','#ffd06b88'],
            borderColor: ['#6c8cff','#6c8cff','#45d4a8','#45d4a8','#ff6b6b','#ffd06b'],
            borderWidth: 1.5 }}]
    }},
    options: {{
        responsive: true, maintainAspectRatio: false,
        scales: {{
            x: {{ grid: {{ display: false }}, ticks: {{ color: '#8b8fa3' }} }},
            y: {{ grid: {{ color: '#2e334444' }}, ticks: {{ color: '#8b8fa3', callback: v => '$' + v }} }}
        }},
        plugins: {{
            legend: {{ display: false }},
            tooltip: {{ callbacks: {{ label: ctx => '$' + ctx.parsed.y }} }}
        }}
    }}
}});
</script>\n"""
    else:
        html += '<p class="empty">No seasonal data yet. Run: python scraper_v2.py seasonal</p>\n'

    # ========== LEAD TIME ==========
    html += '<h2>Lead Time Analysis</h2>\n'
    if leadtime:
        html += f'<p style="color:var(--text-muted);font-size:0.85rem;margin-bottom:1rem">From scrape: {leadtime["date"]} · 3-Bed T1 only</p>\n'

        # Immediate lead times bar chart
        if leadtime["immediate"]:
            chart_id += 1
            imm = leadtime["immediate"]
            labels = json.dumps([d["label"] for d in imm])
            values = json.dumps([d["avg"] for d in imm])
            html += f'<h3>Immediate (same-season)</h3>\n<div class="chart-wrap"><canvas id="lead{chart_id}"></canvas></div>\n'
            html += f"""<script>
new Chart(document.getElementById("lead{chart_id}"), {{
    type: 'bar',
    data: {{
        labels: {labels},
        datasets: [{{ label: 'Avg nightly rate', data: {values},
            backgroundColor: '#6c8cff44', borderColor: '#6c8cff', borderWidth: 1.5 }}]
    }},
    options: {{
        responsive: true, maintainAspectRatio: false,
        indexAxis: 'y',
        scales: {{
            y: {{ grid: {{ display: false }}, ticks: {{ color: '#8b8fa3' }} }},
            x: {{ grid: {{ color: '#2e334444' }}, ticks: {{ color: '#8b8fa3', callback: v => '$' + v }} }}
        }},
        plugins: {{
            legend: {{ display: false }},
            tooltip: {{ callbacks: {{ label: ctx => '$' + ctx.parsed.x }} }}
        }}
    }}
}});
</script>\n"""

        # Tracking date history
        if leadtime["tracking"]:
            html += '<h3>Longitudinal Tracking (far-out curve)</h3>\n'
            for label, points in leadtime["tracking"].items():
                if len(points) < 2:
                    html += f'<p class="empty">{label}: only {len(points)} data point. Run weekly to build curve.</p>\n'
                    continue
                chart_id += 1
                data_points = json.dumps([{"x": p["date"], "y": p["avg"]} for p in points])
                title = label.replace("track_peak_jul14", "Peak (Jul 14)").replace("track_low_oct13", "Low (Oct 13)")
                html += f'<div class="chart-wrap"><canvas id="track{chart_id}"></canvas></div>\n'
                html += f"""<script>
new Chart(document.getElementById("track{chart_id}"), {{
    type: 'line',
    data: {{
        datasets: [{{ label: '{title}', data: {data_points},
            borderColor: '#c78cff', fill: false, tension: 0.3, pointRadius: 4, borderWidth: 2 }}]
    }},
    options: {{
        responsive: true, maintainAspectRatio: false,
        scales: {{
            x: {{ type: 'category', grid: {{ color: '#2e334422' }}, ticks: {{ color: '#8b8fa3' }} }},
            y: {{ grid: {{ color: '#2e334444' }}, ticks: {{ color: '#8b8fa3', callback: v => '$' + v }} }}
        }},
        plugins: {{
            legend: {{ labels: {{ color: '#e4e6ef' }} }},
            tooltip: {{ callbacks: {{ label: ctx => '$' + ctx.parsed.y }} }}
        }}
    }}
}});
</script>\n"""
    else:
        html += '<p class="empty">No lead time data yet. Run: python scraper_v2.py leadtime</p>\n'

    # ========== DISCOUNT ANALYSIS ==========
    html += '<h2>Discount Analysis (3n / 7n / 28n)</h2>\n'
    if discounts:
        html += f'<p style="color:var(--text-muted);font-size:0.85rem;margin-bottom:1rem">From scrape: {discounts["date"]} · Same check-in, different lengths</p>\n'
        for seg in ["3bed", "4bed", "6bed"]:
            if seg not in discounts["data"]:
                continue
            seg_label = seg.replace("bed", "-Bed")
            html += f'<h3>{seg_label}</h3>\n<div class="card"><table>\n'
            html += '<tr><th>Listing</th><th>Tier</th><th>3-night</th><th>7-night</th><th>7n disc</th><th>28-night</th><th>28n disc</th></tr>\n'
            for r in discounts["data"][seg]:
                tier_cls = f"tier-{r['tier']}"
                name_short = r["name"][:40]
                r3 = f"${r['rate_3n']}" if r["rate_3n"] else "—"
                r7 = f"${r['rate_7n']}" if r["rate_7n"] else "—"
                r28 = f"${r['rate_28n']}" if r["rate_28n"] else "—"
                d7 = f"-{r['disc_7n']}%" if r["disc_7n"] else "—"
                d28 = f"-{r['disc_28n']}%" if r["disc_28n"] else "—"
                d7_color = "color:var(--green)" if r["disc_7n"] and r["disc_7n"] > 5 else ""
                d28_color = "color:var(--green)" if r["disc_28n"] and r["disc_28n"] > 10 else ""
                html += f'<tr><td>{name_short}</td>'
                html += f'<td><span class="tier-badge {tier_cls}">T{r["tier"]}</span></td>'
                html += f'<td class="mono">{r3}</td><td class="mono">{r7}</td>'
                html += f'<td class="mono" style="{d7_color}">{d7}</td>'
                html += f'<td class="mono">{r28}</td>'
                html += f'<td class="mono" style="{d28_color}">{d28}</td></tr>\n'
            html += '</table></div>\n'
    else:
        html += '<p class="empty">No discount data yet. Run: python scraper_v2.py discounts</p>\n'

    # ========== OWN PROPERTY vs COMP ==========
    html += '<h2>My Properties vs Market</h2>\n'
    if my_props:
        html += '<div class="grid-2">\n'
        for p in my_props:
            beds = p.get("bedrooms") or "?"
            rate = f"${p['avg_rate']}/night avg" if p["avg_rate"] else "No bookings yet"
            bookings = f"{p['booking_count']} booking{'s' if p['booking_count'] != 1 else ''}"
            html += f"""<div class="card">
    <strong>{p['name']}</strong>
    <div style="color:var(--text-muted);font-size:0.85rem;margin-top:0.5rem">{beds}BR · {p.get('location', 'Berawa')}</div>
    <div class="mono" style="font-size:1.1rem;margin-top:0.75rem">{rate}</div>
    <div style="color:var(--text-muted);font-size:0.8rem;margin-top:0.25rem">{bookings}</div>
</div>\n"""
        html += '</div>\n'
    else:
        html += """<div class="card" style="text-align:center;padding:2rem">
    <div style="color:var(--text-muted);font-size:0.9rem">
        <strong>Own-property data will appear here after launch.</strong><br><br>
        Add your villas: insert rows into <code>my_properties</code> table.<br>
        Import bookings: <code>python scraper_v2.py import-bookings reservations.csv</code>
    </div>
</div>\n"""

    # ========== FOOTER ==========
    html += f"""
<div style="margin-top:3rem;padding-top:1rem;border-top:1px solid var(--border);color:var(--text-muted);font-size:0.75rem">
    Generated by report_generator.py · {stats['listings']} listings tracked · {stats['snapshots']:,} price snapshots · {stats['occ_checks']:,} occupancy checks
</div>
</body>
</html>"""

    return html


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    db_path = get_db_path()
    if not db_path.exists():
        print(f"Database not found: {db_path}")
        print("Run the scraper first, or specify path: python report_generator.py /path/to/comp_data.db")
        sys.exit(1)

    html = generate_html(db_path)
    output_path = db_path.parent / f"comp_report_{date.today().isoformat()}.html"
    with open(output_path, "w") as f:
        f.write(html)

    print(f"Report generated: {output_path}")
    print(f"Open in browser: file://{output_path.resolve()}")
