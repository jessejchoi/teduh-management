"""
Critical path tests for paired cohort % calculation.

These test the core statistical fix — the whole reason for this rebuild.
Run with: pytest tests/
"""
import sqlite3
import sys
from contextlib import contextmanager
from pathlib import Path

# Allow importing dashboard_server from project root
sys.path.insert(0, str(Path(__file__).parent.parent))

import dashboard_server
from dashboard_server import _paired_pct


def make_db():
    """In-memory SQLite DB with minimal schema for paired % testing."""
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript("""
        CREATE TABLE listings (
            listing_id TEXT PRIMARY KEY,
            name TEXT, segment TEXT, tier INTEGER,
            url TEXT, rating REAL, review_count INTEGER,
            superhost INTEGER DEFAULT 0, last_scraped TEXT,
            added_date TEXT DEFAULT CURRENT_TIMESTAMP, min_stay INTEGER
        );
        CREATE TABLE price_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            listing_id TEXT, scrape_date TEXT, scrape_label TEXT,
            checkin_date TEXT, nights INTEGER,
            nightly_rate REAL, total_price REAL,
            is_available INTEGER DEFAULT 1, min_nights INTEGER,
            currency TEXT DEFAULT 'USD'
        );
        CREATE UNIQUE INDEX idx_ps_unique
            ON price_snapshots(listing_id, scrape_date, scrape_label, checkin_date);
    """)
    return conn


def test_paired_pct_averages_individual_changes():
    """
    Paired % must average individual listing % changes, NOT compute (avg_t1 - avg_t0) / avg_t0.

    Listing A: $200 → $220  (+10%)
    Listing B: $100 → $90   (-10%)

    Correct:  avg(+10%, -10%) = 0.0%
    WRONG:    ($220+$90 - $200-$100) / ($200+$100) = $10/$300 = +3.3%
    """
    rates_t0 = {"A": 200.0, "B": 100.0}
    rates_t1 = {"A": 220.0, "B": 90.0}

    result = _paired_pct(rates_t0, rates_t1)

    assert result["pct_change"] == 0.0, (
        f"Expected 0.0% but got {result['pct_change']}% — "
        "paired % must average individual % changes, not compute on group averages"
    )
    assert result["n"] == 2
    assert result["avg_t0"] == 150   # (200+100)/2
    assert result["avg_t1"] == 155   # (220+90)/2


def test_cohort_excludes_missing_t0():
    """
    Listings missing data at either date must be excluded from the cohort.

    Listing A: t0=$200, t1=$220   (+10%)
    Listing B: t0=$100, t1=$90    (-10%)
    Listing C: t0=None, t1=$300   (should be EXCLUDED — no t0)

    Expected: n=2 (C excluded), pct_change = 0.0%
    """
    rates_t0 = {"A": 200.0, "B": 100.0}           # C is missing in t0
    rates_t1 = {"A": 220.0, "B": 90.0, "C": 300.0}  # C has t1 data

    result = _paired_pct(rates_t0, rates_t1)

    assert result["n"] == 2, (
        f"Expected n=2 (C excluded) but got n={result['n']}"
    )
    assert result["pct_change"] == 0.0
    # Listing C ($300) should NOT inflate the result
    assert result["avg_t1"] == 155  # only A+B: (220+90)/2, not (220+90+300)/3


def test_returns_null_when_cohort_too_small():
    """Cohort with < 2 listings returns pct_change=None."""
    # Only 1 listing in common
    result = _paired_pct({"A": 200.0}, {"A": 220.0, "B": 300.0})
    assert result["pct_change"] is None
    assert result["n"] == 1


def test_empty_cohort():
    """No overlap between t0 and t1 listings returns pct_change=None."""
    result = _paired_pct({"A": 200.0}, {"B": 300.0})
    assert result["pct_change"] is None
    assert result["n"] == 0


def test_get_trends_returns_series_instead_of_500(monkeypatch):
    """Regression: get_trends must not crash when it looks up checkin dates."""
    conn = make_db()
    conn.row_factory = sqlite3.Row
    conn.executemany(
        """
        INSERT INTO listings (listing_id, name, segment, tier, url, rating, review_count, superhost, last_scraped, min_stay)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            ("A", "Villa A", "3bed", 1, "https://example.com/a", 4.9, 10, 1, "2026-04-20", 2),
            ("B", "Villa B", "3bed", 1, "https://example.com/b", 4.8, 8, 0, "2026-04-20", 2),
        ],
    )
    conn.executemany(
        """
        INSERT INTO price_snapshots (
            listing_id, scrape_date, scrape_label, checkin_date, nights,
            nightly_rate, total_price, is_available, min_nights, currency
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            ("A", "2026-04-20", "weekday", "2026-05-01", 2, 200.0, 400.0, 1, 2, "USD"),
            ("B", "2026-04-20", "weekday", "2026-05-01", 2, 100.0, 200.0, 1, 2, "USD"),
            ("A", "2026-04-21", "weekday", "2026-05-01", 2, 220.0, 440.0, 1, 2, "USD"),
            ("B", "2026-04-21", "weekday", "2026-05-01", 2, 90.0, 180.0, 1, 2, "USD"),
        ],
    )

    @contextmanager
    def fake_get_db():
        try:
            yield conn
        finally:
            pass

    monkeypatch.setattr(dashboard_server, "get_db", fake_get_db)

    payload = dashboard_server.get_trends()
    assert payload["pct_series"] == [
        {
            "date": "2026-04-21",
            "scrape_date": "2026-04-21",
            "checkin_date": "2026-05-01",
            "3bed": 0.0,
            "4bed": None,
            "6bed": None,
        }
    ]
    assert payload["rate_series"] == [
        {
            "date": "2026-04-20",
            "scrape_date": "2026-04-20",
            "checkin_date": "2026-05-01",
            "3bed": 150,
            "4bed": None,
            "6bed": None,
        },
        {
            "date": "2026-04-21",
            "scrape_date": "2026-04-21",
            "checkin_date": "2026-05-01",
            "3bed": 155,
            "4bed": None,
            "6bed": None,
        },
    ]
    conn.close()
