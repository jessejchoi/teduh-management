import { useState, useEffect, useMemo, useCallback } from "react";
import * as d3 from "d3";
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Area, AreaChart, Cell } from "recharts";

const COLORS = {
  bg: "#0f1117", surface: "#1a1d27", surface2: "#232735", border: "#2e3344",
  text: "#e4e6ef", muted: "#8b8fa3", accent: "#6c8cff", green: "#45d4a8",
  orange: "#ff8c6c", purple: "#c78cff", yellow: "#ffd06b", red: "#ff6b6b",
};
const TIER_COLORS = { 1: COLORS.accent, 2: COLORS.purple, 3: COLORS.muted };
const SEG_COLORS = { "3bed": COLORS.accent, "4bed": COLORS.green, "6bed": COLORS.orange };
const PALETTE = ["#6c8cff","#45d4a8","#ff8c6c","#c78cff","#ffd06b","#ff6b6b","#6bffd0","#ff6bab","#8cbaff","#d4ff6b","#6baaff","#ffab6b","#ab6bff"];

function parseCSV(text) {
  const rows = d3.csvParse(text);
  return rows.map(r => {
    const o = { ...r };
    ["nightly_rate","total_price","rating","review_count","tier","nights","is_available","occupancy_pct","days_available","days_blocked","total_days","min_stay"].forEach(k => {
      if (o[k] !== undefined && o[k] !== "") o[k] = +o[k];
    });
    return o;
  });
}

const Tab = ({ active, onClick, children }) => (
  <button onClick={onClick} style={{
    padding: "8px 16px", fontSize: "0.8rem", fontWeight: active ? 600 : 400,
    background: active ? COLORS.surface2 : "transparent", color: active ? COLORS.text : COLORS.muted,
    border: `1px solid ${active ? COLORS.border : "transparent"}`, borderRadius: 6, cursor: "pointer",
    fontFamily: "inherit", transition: "all 0.15s"
  }}>{children}</button>
);

const Card = ({ children, style }) => (
  <div style={{ background: COLORS.surface, border: `1px solid ${COLORS.border}`, borderRadius: 10, padding: "1rem", ...style }}>{children}</div>
);

const TierBadge = ({ tier }) => (
  <span style={{
    padding: "2px 8px", borderRadius: 4, fontSize: "0.7rem", fontWeight: 600, fontFamily: "'JetBrains Mono', monospace",
    background: `${TIER_COLORS[tier]}22`, color: TIER_COLORS[tier]
  }}>T{tier}</span>
);

const Empty = ({ text }) => (
  <div style={{ color: COLORS.muted, fontStyle: "italic", padding: "2rem", textAlign: "center" }}>{text}</div>
);

const StatCard = ({ label, value, sub }) => (
  <Card style={{ textAlign: "center", minWidth: 120 }}>
    <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: "1.6rem", fontWeight: 700 }}>{value}</div>
    <div style={{ color: COLORS.muted, fontSize: "0.75rem", marginTop: 4 }}>{label}</div>
    {sub && <div style={{ color: COLORS.muted, fontSize: "0.7rem", fontFamily: "'JetBrains Mono', monospace", marginTop: 4 }}>{sub}</div>}
  </Card>
);

const CustomTooltip = ({ active, payload, label, prefix = "$" }) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{ background: COLORS.surface2, border: `1px solid ${COLORS.border}`, borderRadius: 6, padding: "8px 12px", fontSize: "0.75rem" }}>
      <div style={{ color: COLORS.muted, marginBottom: 4 }}>{label}</div>
      {payload.map((p, i) => (
        <div key={i} style={{ color: p.color }}>{p.name}: {prefix}{Math.round(p.value)}</div>
      ))}
    </div>
  );
};

// ========== MAIN DASHBOARD ==========

export default function Dashboard() {
  const [prices, setPrices] = useState(null);
  const [listings, setListings] = useState(null);
  const [occupancy, setOccupancy] = useState(null);
  const [tab, setTab] = useState("overview");
  const [segFilter, setSegFilter] = useState("all");
  const [tierFilter, setTierFilter] = useState("all");

  const handleFile = useCallback((setter) => (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => setter(parseCSV(ev.target.result));
    reader.readAsText(file);
  }, []);

  const hasData = prices && prices.length > 0;
  const hasListings = listings && listings.length > 0;
  const hasOcc = occupancy && occupancy.length > 0;

  // Derived data
  const filtered = useMemo(() => {
    if (!hasData) return [];
    return prices.filter(p => {
      if (segFilter !== "all" && p.segment !== segFilter) return false;
      if (tierFilter !== "all" && p.tier !== +tierFilter) return false;
      return true;
    });
  }, [prices, segFilter, tierFilter, hasData]);

  // Market overview: per segment per tier, latest date
  const overview = useMemo(() => {
    if (!hasData) return null;
    const dates = [...new Set(prices.map(p => p.scrape_date))].sort();
    const latestDate = dates[dates.length - 1];
    const latest = prices.filter(p => p.scrape_date === latestDate);

    const result = {};
    for (const seg of ["3bed", "4bed", "6bed"]) {
      result[seg] = {};
      for (const tier of [1, 2, 3]) {
        const rows = latest.filter(p => p.segment === seg && p.tier === tier && p.scrape_label === "weekday" && p.nightly_rate);
        const weRows = latest.filter(p => p.segment === seg && p.tier === tier && p.scrape_label === "weekend" && p.nightly_rate);
        if (rows.length) {
          const avg = d3.mean(rows, d => d.nightly_rate);
          const weAvg = weRows.length ? d3.mean(weRows, d => d.nightly_rate) : null;
          result[seg][tier] = { avg: Math.round(avg), weekend: weAvg ? Math.round(weAvg) : null, count: rows.length };
        }
      }
    }
    return { date: latestDate, data: result, totalDates: dates.length };
  }, [prices, hasData]);

  // T1 trend over time
  const trends = useMemo(() => {
    if (!hasData) return null;
    const t1weekday = prices.filter(p => p.tier === 1 && p.scrape_label === "weekday" && p.nightly_rate);
    const byDateSeg = d3.rollups(t1weekday, v => Math.round(d3.mean(v, d => d.nightly_rate)), d => d.scrape_date, d => d.segment);
    const dates = [...new Set(t1weekday.map(d => d.scrape_date))].sort();
    return dates.map(dt => {
      const entry = { date: dt.slice(5) };
      const dateGroup = byDateSeg.find(([d]) => d === dt);
      if (dateGroup) dateGroup[1].forEach(([seg, avg]) => { entry[seg] = avg; });
      return entry;
    });
  }, [prices, hasData]);

  // Comp price history
  const compHistory = useMemo(() => {
    if (!hasData) return null;
    const t1weekday = filtered.filter(p => p.tier === 1 && p.scrape_label === "weekday" && p.nightly_rate);
    const byComp = d3.groups(t1weekday, d => d.listing_id);
    const dates = [...new Set(t1weekday.map(d => d.scrape_date))].sort();

    return { dates, comps: byComp.map(([lid, rows]) => {
      const name = rows[0].name?.slice(0, 25) || lid;
      const seg = rows[0].segment;
      const series = {};
      rows.forEach(r => { series[r.scrape_date] = r.nightly_rate; });
      return { lid, name, seg, series };
    })};
  }, [filtered, hasData]);

  // Seasonal data
  const seasonalData = useMemo(() => {
    if (!hasData) return null;
    const seasonal = prices.filter(p => p.scrape_label?.startsWith("seasonal_") && p.nightly_rate);
    if (!seasonal.length) return null;
    const latestDate = d3.max(seasonal, d => d.scrape_date);
    const latest = seasonal.filter(p => p.scrape_date === latestDate);

    const result = {};
    for (const seg of ["3bed", "4bed", "6bed"]) {
      const segRows = latest.filter(p => p.segment === seg);
      if (!segRows.length) continue;
      const bySeason = d3.rollups(segRows, v => Math.round(d3.mean(v, d => d.nightly_rate)), d => d.scrape_label.replace("seasonal_", ""));
      result[seg] = bySeason.map(([label, avg]) => ({ label, avg }));
    }
    return { date: latestDate, data: result };
  }, [prices, hasData]);

  // Lead time data
  const leadtimeData = useMemo(() => {
    if (!hasData) return null;
    const lt = prices.filter(p => p.scrape_label?.startsWith("leadtime_") && p.nightly_rate);
    if (!lt.length) return null;
    const latestDate = d3.max(lt, d => d.scrape_date);
    const latest = lt.filter(p => p.scrape_date === latestDate && p.segment === "3bed" && p.tier === 1);

    const immediate = d3.rollups(
      latest.filter(p => !p.scrape_label.includes("track_")),
      v => Math.round(d3.mean(v, d => d.nightly_rate)),
      d => d.scrape_label.replace("leadtime_", "")
    ).map(([label, avg]) => ({ label, avg }));

    // Tracking history
    const tracking = {};
    for (const prefix of ["track_peak_jul14", "track_low_oct13"]) {
      const trackRows = lt.filter(p => p.scrape_label === `leadtime_${prefix}` && p.segment === "3bed" && p.tier === 1);
      if (trackRows.length) {
        const byDate = d3.rollups(trackRows, v => Math.round(d3.mean(v, d => d.nightly_rate)), d => d.scrape_date);
        tracking[prefix] = byDate.sort((a, b) => a[0].localeCompare(b[0])).map(([dt, avg]) => ({ date: dt.slice(5), avg }));
      }
    }
    return { date: latestDate, immediate, tracking };
  }, [prices, hasData]);

  // Occupancy
  const occData = useMemo(() => {
    if (!hasOcc) return null;
    const byDateSeg = d3.rollups(
      occupancy.filter(o => o.tier === 1),
      v => Math.round(d3.sum(v, d => d.is_booked) / v.length * 100),
      d => d.check_date, d => d.segment
    );
    const dates = [...new Set(occupancy.map(d => d.check_date))].sort();
    const trend = dates.map(dt => {
      const entry = { date: dt.slice(5) };
      const dateGroup = byDateSeg.find(([d]) => d === dt);
      if (dateGroup) dateGroup[1].forEach(([seg, pct]) => { entry[seg] = pct; });
      return entry;
    });

    // Per-comp cumulative
    const compOcc = d3.rollups(
      occupancy.filter(o => o.tier === 1),
      v => ({ booked: d3.sum(v, d => d.is_booked), total: v.length, pct: Math.round(d3.sum(v, d => d.is_booked) / v.length * 100), name: v[0].name, seg: v[0].segment }),
      d => d.listing_id
    ).map(([lid, data]) => ({ lid, ...data })).sort((a, b) => b.pct - a.pct);

    return { trend, compOcc };
  }, [occupancy, hasOcc]);

  return (
    <div style={{ fontFamily: "'DM Sans', sans-serif", background: COLORS.bg, color: COLORS.text, minHeight: "100vh", padding: "1.5rem" }}>
      <div style={{ maxWidth: 1300, margin: "0 auto" }}>

        {/* Header */}
        <h1 style={{ fontSize: "1.5rem", fontWeight: 700, letterSpacing: "-0.03em", marginBottom: 4 }}>
          Berawa Comp Intelligence
        </h1>
        <p style={{ color: COLORS.muted, fontSize: "0.8rem", marginBottom: "1.5rem" }}>
          Interactive dashboard · Upload CSV exports from scraper
        </p>

        {/* File Upload */}
        <Card style={{ marginBottom: "1.5rem" }}>
          <div style={{ display: "flex", gap: "1.5rem", flexWrap: "wrap", alignItems: "center" }}>
            <label style={{ fontSize: "0.8rem" }}>
              <span style={{ color: COLORS.muted }}>Prices CSV: </span>
              <input type="file" accept=".csv" onChange={handleFile(setPrices)} style={{ fontSize: "0.75rem" }} />
            </label>
            <label style={{ fontSize: "0.8rem" }}>
              <span style={{ color: COLORS.muted }}>Listings CSV: </span>
              <input type="file" accept=".csv" onChange={handleFile(setListings)} style={{ fontSize: "0.75rem" }} />
            </label>
            <label style={{ fontSize: "0.8rem" }}>
              <span style={{ color: COLORS.muted }}>Occupancy CSV: </span>
              <input type="file" accept=".csv" onChange={handleFile(setOccupancy)} style={{ fontSize: "0.75rem" }} />
            </label>
            {hasData && <span style={{ fontSize: "0.75rem", color: COLORS.green }}>✓ {prices.length.toLocaleString()} price rows loaded</span>}
          </div>
        </Card>

        {!hasData ? (
          <Card>
            <Empty text="Upload CSV files from the scraper's export mode to get started. Run: python scraper_v2.py export" />
            <div style={{ textAlign: "center", color: COLORS.muted, fontSize: "0.8rem", marginTop: "1rem" }}>
              <p>Expected files from the <code style={{ color: COLORS.accent }}>exports/</code> folder:</p>
              <p style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: "0.75rem", marginTop: 8 }}>
                prices_YYYY-MM-DD.csv · listings_YYYY-MM-DD.csv · occupancy_YYYY-MM-DD.csv
              </p>
            </div>
          </Card>
        ) : (
          <>
            {/* Tabs */}
            <div style={{ display: "flex", gap: 4, marginBottom: "1rem", flexWrap: "wrap" }}>
              {[["overview", "Market Overview"], ["trends", "Pricing Trends"], ["occupancy", "Occupancy"], ["seasonal", "Seasonal & Lead Time"], ["comps", "Comp Table"]].map(([k, label]) => (
                <Tab key={k} active={tab === k} onClick={() => setTab(k)}>{label}</Tab>
              ))}
            </div>

            {/* Filters */}
            <div style={{ display: "flex", gap: "1rem", marginBottom: "1rem", fontSize: "0.8rem" }}>
              <label style={{ color: COLORS.muted }}>Segment:
                <select value={segFilter} onChange={e => setSegFilter(e.target.value)} style={{
                  marginLeft: 6, background: COLORS.surface2, color: COLORS.text, border: `1px solid ${COLORS.border}`,
                  borderRadius: 4, padding: "4px 8px", fontSize: "0.8rem", fontFamily: "inherit"
                }}>
                  <option value="all">All</option>
                  <option value="3bed">3-Bed</option>
                  <option value="4bed">4-Bed</option>
                  <option value="6bed">6-Bed</option>
                </select>
              </label>
              <label style={{ color: COLORS.muted }}>Tier:
                <select value={tierFilter} onChange={e => setTierFilter(e.target.value)} style={{
                  marginLeft: 6, background: COLORS.surface2, color: COLORS.text, border: `1px solid ${COLORS.border}`,
                  borderRadius: 4, padding: "4px 8px", fontSize: "0.8rem", fontFamily: "inherit"
                }}>
                  <option value="all">All</option>
                  <option value="1">T1 Direct</option>
                  <option value="2">T2 Aspirational</option>
                  <option value="3">T3 Floor</option>
                </select>
              </label>
            </div>

            {/* ========== OVERVIEW TAB ========== */}
            {tab === "overview" && overview && (
              <div>
                <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: "1.5rem" }}>
                  <StatCard label="Latest Scrape" value={overview.date} />
                  <StatCard label="Scrape Days" value={overview.totalDates} />
                  <StatCard label="Price Points" value={prices.length.toLocaleString()} />
                </div>

                {["3bed", "4bed", "6bed"].map(seg => {
                  if (segFilter !== "all" && segFilter !== seg) return null;
                  const d = overview.data[seg];
                  if (!d || !Object.keys(d).length) return null;
                  return (
                    <div key={seg} style={{ marginBottom: "1.5rem" }}>
                      <h3 style={{ fontSize: "0.9rem", fontWeight: 600, color: SEG_COLORS[seg], marginBottom: 8 }}>{seg.replace("bed", "-Bed")}</h3>
                      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 8 }}>
                        {[1, 2, 3].map(tier => {
                          if (tierFilter !== "all" && +tierFilter !== tier) return null;
                          if (!d[tier]) return null;
                          const t = d[tier];
                          return (
                            <Card key={tier} style={{ textAlign: "center" }}>
                              <TierBadge tier={tier} />
                              <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: "1.5rem", fontWeight: 700, marginTop: 8 }}>${t.avg}</div>
                              <div style={{ color: COLORS.muted, fontSize: "0.7rem" }}>weekday avg · {t.count} comps</div>
                              {t.weekend && <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: "0.75rem", color: COLORS.muted, marginTop: 4 }}>
                                Wkend ${t.weekend} {t.avg > 0 ? `+${Math.round((t.weekend - t.avg) / t.avg * 100)}%` : ""}
                              </div>}
                            </Card>
                          );
                        })}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}

            {/* ========== TRENDS TAB ========== */}
            {tab === "trends" && (
              <div>
                {trends && trends.length > 1 ? (
                  <>
                    <h3 style={{ fontSize: "0.85rem", color: COLORS.muted, marginBottom: 8 }}>T1 Weekday Avg Over Time</h3>
                    <Card>
                      <ResponsiveContainer width="100%" height={300}>
                        <LineChart data={trends}>
                          <CartesianGrid strokeDasharray="3 3" stroke={COLORS.border} />
                          <XAxis dataKey="date" tick={{ fill: COLORS.muted, fontSize: 11 }} />
                          <YAxis tick={{ fill: COLORS.muted, fontSize: 11 }} tickFormatter={v => `$${v}`} />
                          <Tooltip content={<CustomTooltip />} />
                          <Legend wrapperStyle={{ fontSize: "0.75rem" }} />
                          {(segFilter === "all" || segFilter === "3bed") && <Line type="monotone" dataKey="3bed" name="3-Bed" stroke={SEG_COLORS["3bed"]} strokeWidth={2} dot={{ r: 3 }} />}
                          {(segFilter === "all" || segFilter === "4bed") && <Line type="monotone" dataKey="4bed" name="4-Bed" stroke={SEG_COLORS["4bed"]} strokeWidth={2} dot={{ r: 3 }} />}
                          {(segFilter === "all" || segFilter === "6bed") && <Line type="monotone" dataKey="6bed" name="6-Bed" stroke={SEG_COLORS["6bed"]} strokeWidth={2} dot={{ r: 3 }} />}
                        </LineChart>
                      </ResponsiveContainer>
                    </Card>
                  </>
                ) : <Empty text="Need 2+ daily scrapes to show trends." />}

                {compHistory && compHistory.comps.length > 0 && compHistory.dates.length > 1 && (
                  <>
                    <h3 style={{ fontSize: "0.85rem", color: COLORS.muted, marginTop: "1.5rem", marginBottom: 8 }}>Individual T1 Comp Prices</h3>
                    {["3bed", "4bed", "6bed"].map(seg => {
                      if (segFilter !== "all" && segFilter !== seg) return null;
                      const segComps = compHistory.comps.filter(c => c.seg === seg);
                      if (!segComps.length) return null;
                      const chartData = compHistory.dates.map(dt => {
                        const entry = { date: dt.slice(5) };
                        segComps.forEach(c => { if (c.series[dt]) entry[c.lid] = c.series[dt]; });
                        return entry;
                      });
                      return (
                        <div key={seg} style={{ marginBottom: "1rem" }}>
                          <h4 style={{ fontSize: "0.8rem", color: SEG_COLORS[seg], marginBottom: 4 }}>{seg.replace("bed", "-Bed")}</h4>
                          <Card>
                            <ResponsiveContainer width="100%" height={280}>
                              <LineChart data={chartData}>
                                <CartesianGrid strokeDasharray="3 3" stroke={COLORS.border} />
                                <XAxis dataKey="date" tick={{ fill: COLORS.muted, fontSize: 10 }} />
                                <YAxis tick={{ fill: COLORS.muted, fontSize: 10 }} tickFormatter={v => `$${v}`} />
                                <Tooltip content={<CustomTooltip />} />
                                <Legend wrapperStyle={{ fontSize: "0.65rem" }} />
                                {segComps.map((c, i) => (
                                  <Line key={c.lid} type="monotone" dataKey={c.lid} name={c.name} stroke={PALETTE[i % PALETTE.length]} strokeWidth={1.5} dot={false} />
                                ))}
                              </LineChart>
                            </ResponsiveContainer>
                          </Card>
                        </div>
                      );
                    })}
                  </>
                )}
              </div>
            )}

            {/* ========== OCCUPANCY TAB ========== */}
            {tab === "occupancy" && (
              <div>
                {occData ? (
                  <>
                    {occData.trend.length > 1 && (
                      <>
                        <h3 style={{ fontSize: "0.85rem", color: COLORS.muted, marginBottom: 8 }}>Daily Occupancy Rate (T1)</h3>
                        <Card>
                          <ResponsiveContainer width="100%" height={280}>
                            <AreaChart data={occData.trend}>
                              <CartesianGrid strokeDasharray="3 3" stroke={COLORS.border} />
                              <XAxis dataKey="date" tick={{ fill: COLORS.muted, fontSize: 10 }} />
                              <YAxis domain={[0, 100]} tick={{ fill: COLORS.muted, fontSize: 10 }} tickFormatter={v => `${v}%`} />
                              <Tooltip content={<CustomTooltip prefix="" />} />
                              <Legend wrapperStyle={{ fontSize: "0.75rem" }} />
                              {(segFilter === "all" || segFilter === "3bed") && <Area type="monotone" dataKey="3bed" name="3-Bed" stroke={SEG_COLORS["3bed"]} fill={SEG_COLORS["3bed"] + "22"} />}
                              {(segFilter === "all" || segFilter === "4bed") && <Area type="monotone" dataKey="4bed" name="4-Bed" stroke={SEG_COLORS["4bed"]} fill={SEG_COLORS["4bed"] + "22"} />}
                              {(segFilter === "all" || segFilter === "6bed") && <Area type="monotone" dataKey="6bed" name="6-Bed" stroke={SEG_COLORS["6bed"]} fill={SEG_COLORS["6bed"] + "22"} />}
                            </AreaChart>
                          </ResponsiveContainer>
                        </Card>
                      </>
                    )}

                    {occData.compOcc.length > 0 && (
                      <>
                        <h3 style={{ fontSize: "0.85rem", color: COLORS.muted, marginTop: "1.5rem", marginBottom: 8 }}>Cumulative Occupancy by Comp</h3>
                        <Card>
                          <ResponsiveContainer width="100%" height={Math.max(200, occData.compOcc.length * 28)}>
                            <BarChart data={occData.compOcc} layout="vertical" margin={{ left: 120 }}>
                              <CartesianGrid strokeDasharray="3 3" stroke={COLORS.border} />
                              <XAxis type="number" domain={[0, 100]} tick={{ fill: COLORS.muted, fontSize: 10 }} tickFormatter={v => `${v}%`} />
                              <YAxis type="category" dataKey="name" tick={{ fill: COLORS.muted, fontSize: 10 }} width={120} />
                              <Tooltip content={<CustomTooltip prefix="" />} />
                              <Bar dataKey="pct" name="Occupancy" radius={[0, 4, 4, 0]}>
                                {occData.compOcc.map((d, i) => (
                                  <Cell key={i} fill={d.pct >= 70 ? COLORS.green : d.pct >= 50 ? COLORS.yellow : COLORS.red} />
                                ))}
                              </Bar>
                            </BarChart>
                          </ResponsiveContainer>
                        </Card>
                      </>
                    )}
                  </>
                ) : <Empty text="Upload occupancy CSV to see data." />}
              </div>
            )}

            {/* ========== SEASONAL & LEAD TIME TAB ========== */}
            {tab === "seasonal" && (
              <div>
                {seasonalData ? (
                  <>
                    <h3 style={{ fontSize: "0.85rem", color: COLORS.muted, marginBottom: 8 }}>Seasonal Rates (T1+T2) — {seasonalData.date}</h3>
                    {["3bed", "4bed", "6bed"].map(seg => {
                      if (segFilter !== "all" && segFilter !== seg) return null;
                      if (!seasonalData.data[seg]) return null;
                      return (
                        <div key={seg} style={{ marginBottom: "1rem" }}>
                          <h4 style={{ fontSize: "0.8rem", color: SEG_COLORS[seg], marginBottom: 4 }}>{seg.replace("bed", "-Bed")}</h4>
                          <Card>
                            <ResponsiveContainer width="100%" height={220}>
                              <BarChart data={seasonalData.data[seg]}>
                                <CartesianGrid strokeDasharray="3 3" stroke={COLORS.border} />
                                <XAxis dataKey="label" tick={{ fill: COLORS.muted, fontSize: 10 }} />
                                <YAxis tick={{ fill: COLORS.muted, fontSize: 10 }} tickFormatter={v => `$${v}`} />
                                <Tooltip content={<CustomTooltip />} />
                                <Bar dataKey="avg" name="Avg Rate" fill={SEG_COLORS[seg]} radius={[4, 4, 0, 0]} fillOpacity={0.7} />
                              </BarChart>
                            </ResponsiveContainer>
                          </Card>
                        </div>
                      );
                    })}
                  </>
                ) : <Empty text="No seasonal data. Run: python scraper_v2.py seasonal" />}

                {leadtimeData ? (
                  <>
                    <h3 style={{ fontSize: "0.85rem", color: COLORS.muted, marginTop: "2rem", marginBottom: 8 }}>Lead Time (3-Bed T1) — {leadtimeData.date}</h3>
                    {leadtimeData.immediate.length > 0 && (
                      <Card style={{ marginBottom: "1rem" }}>
                        <ResponsiveContainer width="100%" height={180}>
                          <BarChart data={leadtimeData.immediate} layout="vertical" margin={{ left: 100 }}>
                            <CartesianGrid strokeDasharray="3 3" stroke={COLORS.border} />
                            <XAxis type="number" tick={{ fill: COLORS.muted, fontSize: 10 }} tickFormatter={v => `$${v}`} />
                            <YAxis type="category" dataKey="label" tick={{ fill: COLORS.muted, fontSize: 10 }} width={100} />
                            <Tooltip content={<CustomTooltip />} />
                            <Bar dataKey="avg" name="Avg Rate" fill={COLORS.purple} radius={[0, 4, 4, 0]} fillOpacity={0.7} />
                          </BarChart>
                        </ResponsiveContainer>
                      </Card>
                    )}

                    {Object.entries(leadtimeData.tracking).map(([key, points]) => {
                      if (points.length < 2) return <Empty key={key} text={`${key}: Only ${points.length} data point. Run weekly to build curve.`} />;
                      const title = key.replace("track_peak_jul14", "Peak Season (Jul 14)").replace("track_low_oct13", "Low Season (Oct 13)");
                      return (
                        <div key={key} style={{ marginBottom: "1rem" }}>
                          <h4 style={{ fontSize: "0.8rem", color: COLORS.purple, marginBottom: 4 }}>{title} — Longitudinal Tracking</h4>
                          <Card>
                            <ResponsiveContainer width="100%" height={200}>
                              <LineChart data={points}>
                                <CartesianGrid strokeDasharray="3 3" stroke={COLORS.border} />
                                <XAxis dataKey="date" tick={{ fill: COLORS.muted, fontSize: 10 }} />
                                <YAxis tick={{ fill: COLORS.muted, fontSize: 10 }} tickFormatter={v => `$${v}`} />
                                <Tooltip content={<CustomTooltip />} />
                                <Line type="monotone" dataKey="avg" name="Avg Rate" stroke={COLORS.purple} strokeWidth={2} dot={{ r: 4 }} />
                              </LineChart>
                            </ResponsiveContainer>
                          </Card>
                        </div>
                      );
                    })}
                  </>
                ) : <Empty text="No lead time data. Run: python scraper_v2.py leadtime" />}
              </div>
            )}

            {/* ========== COMP TABLE TAB ========== */}
            {tab === "comps" && (
              <div>
                <Card>
                  <div style={{ overflowX: "auto" }}>
                    <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.8rem" }}>
                      <thead>
                        <tr>
                          {["Listing", "Seg", "Tier", "Rating", "Reviews", "Min Stay", "Weekday", "Weekend"].map(h => (
                            <th key={h} style={{ textAlign: "left", padding: "8px 10px", borderBottom: `1px solid ${COLORS.border}`, color: COLORS.muted, fontWeight: 500, fontSize: "0.7rem", textTransform: "uppercase", letterSpacing: "0.04em" }}>{h}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {(() => {
                          const latest = d3.max(prices, d => d.scrape_date);
                          const latestPrices = prices.filter(p => p.scrape_date === latest);
                          const comps = d3.groups(latestPrices, d => d.listing_id);
                          return comps.filter(([, rows]) => {
                            if (segFilter !== "all" && rows[0].segment !== segFilter) return false;
                            if (tierFilter !== "all" && rows[0].tier !== +tierFilter) return false;
                            return true;
                          }).map(([lid, rows]) => {
                            const r = rows[0];
                            const wd = rows.find(p => p.scrape_label === "weekday")?.nightly_rate;
                            const we = rows.find(p => p.scrape_label === "weekend")?.nightly_rate;
                            return (
                              <tr key={lid} style={{ borderBottom: `1px solid ${COLORS.border}` }}>
                                <td style={{ padding: "6px 10px" }}>
                                  <a href={`https://www.airbnb.com/rooms/${lid}`} target="_blank" rel="noopener" style={{ color: COLORS.accent, textDecoration: "none" }}>{(r.name || lid).slice(0, 40)}</a>
                                </td>
                                <td style={{ padding: "6px 10px" }}>{r.segment}</td>
                                <td style={{ padding: "6px 10px" }}><TierBadge tier={r.tier} /></td>
                                <td style={{ padding: "6px 10px", fontFamily: "'JetBrains Mono', monospace", fontSize: "0.75rem" }}>{r.rating || "—"}</td>
                                <td style={{ padding: "6px 10px", fontFamily: "'JetBrains Mono', monospace", fontSize: "0.75rem" }}>{r.review_count || "—"}</td>
                                <td style={{ padding: "6px 10px", fontFamily: "'JetBrains Mono', monospace", fontSize: "0.75rem" }}>{r.min_stay ? `${r.min_stay}n` : "—"}</td>
                                <td style={{ padding: "6px 10px", fontFamily: "'JetBrains Mono', monospace", fontSize: "0.75rem" }}>{wd ? `$${Math.round(wd)}` : "—"}</td>
                                <td style={{ padding: "6px 10px", fontFamily: "'JetBrains Mono', monospace", fontSize: "0.75rem" }}>{we ? `$${Math.round(we)}` : "—"}</td>
                              </tr>
                            );
                          });
                        })()}
                      </tbody>
                    </table>
                  </div>
                </Card>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
