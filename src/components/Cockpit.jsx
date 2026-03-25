import { useState, useEffect } from 'react'
import { apiFetch } from '../api.js'
import { useFilters, COLORS, SEG_COLORS } from '../App.jsx'
import { Card, StatCard, Empty, Loading, ErrorMsg, SectionTitle } from './ui.jsx'

function AlertCard({ alerts }) {
  if (!alerts?.length) {
    return (
      <Card>
        <SectionTitle>Alerts</SectionTitle>
        <div style={{ color: COLORS.green, fontSize: '0.82rem' }}>✓ No alerts</div>
      </Card>
    )
  }

  const colors = { warning: COLORS.orange, info: COLORS.muted, critical: COLORS.red }
  const icons = { price_drop: '↓', dark_listing: '◌', event: '◈' }

  return (
    <Card>
      <SectionTitle>Alerts ({alerts.length})</SectionTitle>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
        {alerts.map((a, i) => (
          <div key={i} style={{
            display: 'flex', gap: 8, alignItems: 'flex-start',
            fontSize: '0.78rem', color: colors[a.severity] || COLORS.muted,
          }}>
            <span style={{ fontFamily: 'monospace', minWidth: 12 }}>
              {icons[a.type] || '•'}
            </span>
            <span>{a.message}</span>
          </div>
        ))}
      </div>
    </Card>
  )
}

function ScrapeHealth({ health }) {
  if (!health) return null
  const stale = health.stale
  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 6,
      fontSize: '0.72rem', color: stale ? COLORS.orange : COLORS.green,
    }}>
      <span style={{ fontSize: '0.7rem' }}>{stale ? '⚠' : '●'}</span>
      {stale
        ? `Stale — last scrape: ${health.last_scrape || 'never'}`
        : `Live — last scrape: ${health.last_scrape}`}
      {health.ok_count > 0 && <span style={{ color: COLORS.muted }}>({health.ok_count} listings)</span>}
    </div>
  )
}

export default function Cockpit() {
  const { segment, tier } = useFilters()
  const [data, setData] = useState(null)
  const [overview, setOverview] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    setLoading(true)
    setError(null)
    Promise.all([
      apiFetch('cockpit', { segment, tier }),
      apiFetch('overview', { segment, tier }),
    ])
      .then(([cockpit, ov]) => { setData(cockpit); setOverview(ov); })
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [segment, tier])

  if (loading) return <Loading />
  if (error) return <ErrorMsg error={error} />

  const segs = segment === 'all' ? ['3bed', '4bed', '6bed'] : [segment]

  return (
    <div>
      {/* Scrape health */}
      <div style={{ marginBottom: '0.75rem' }}>
        <ScrapeHealth health={data?.scrape_health} />
      </div>

      {/* KPI cards */}
      <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginBottom: '1.5rem' }}>
        {segs.map(seg => {
          const mr = data?.market_rates?.[seg]
          if (!mr) return null
          const wow = mr.wow_pct
          const wowStr = wow != null ? `${wow > 0 ? '+' : ''}${wow.toFixed(1)}% WoW` : null
          return (
            <StatCard
              key={seg}
              label={`T${tier === 'all' ? '1+' : tier} ${seg.replace('bed', '-Bed')} weekday`}
              value={mr.weekday ? `$${mr.weekday}` : '—'}
              sub={wowStr ? (wow > 0 ? `▲ ${wowStr}` : wow < 0 ? `▼ ${wowStr}` : `→ ${wowStr}`) : null}
              color={COLORS.text}
            />
          )
        })}
        {data?.occupancy_pulse?.avg_occ_pct != null && (
          <StatCard
            label="T1 Occ (7d)"
            value={`${data.occupancy_pulse.avg_occ_pct}%`}
          />
        )}
      </div>

      {/* Alerts + Overview grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '1rem', marginBottom: '1.5rem' }}>
        <AlertCard alerts={data?.alerts} />

        {/* Market snapshot table */}
        <Card>
          <SectionTitle>Market Snapshot — {overview?.date || '—'}</SectionTitle>
          {overview?.segments && Object.keys(overview.segments).length > 0 ? (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.78rem' }}>
                <thead>
                  <tr>
                    {['Segment', 'Tier', 'Weekday', 'Weekend', 'Spread', 'N'].map(h => (
                      <th key={h} style={{
                        textAlign: 'left', padding: '6px 10px',
                        borderBottom: `1px solid ${COLORS.border}`,
                        color: COLORS.muted, fontWeight: 500, fontSize: '0.68rem',
                        textTransform: 'uppercase', letterSpacing: '0.04em',
                      }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(overview.segments).flatMap(([seg, tiers]) =>
                    Object.entries(tiers)
                      .filter(([t]) => tier === 'all' || t === tier)
                      .map(([t, d]) => (
                        <tr key={`${seg}-${t}`} style={{ borderBottom: `1px solid ${COLORS.border}22` }}>
                          <td style={{ padding: '5px 10px', color: SEG_COLORS[seg] || COLORS.text }}>
                            {seg.replace('bed', '-Bed')}
                          </td>
                          <td style={{ padding: '5px 10px', fontFamily: 'monospace', fontSize: '0.72rem' }}>T{t}</td>
                          <td style={{ padding: '5px 10px', fontFamily: 'monospace', fontWeight: 600 }}>
                            {d.weekday ? `$${d.weekday}` : '—'}
                          </td>
                          <td style={{ padding: '5px 10px', fontFamily: 'monospace' }}>
                            {d.weekend ? `$${d.weekend}` : '—'}
                          </td>
                          <td style={{ padding: '5px 10px', fontFamily: 'monospace', color: COLORS.muted }}>
                            {d.spread != null ? `+${d.spread}%` : '—'}
                          </td>
                          <td style={{ padding: '5px 10px', color: COLORS.muted }}>{d.count}</td>
                        </tr>
                      ))
                  )}
                </tbody>
              </table>
            </div>
          ) : (
            <Empty text="No data yet. Run: python3 scraper_v2.py run" />
          )}
        </Card>
      </div>

      {/* Data quality note */}
      {data?.market_rates && Object.values(data.market_rates).some(r => r.wow_pct != null) && (
        <div style={{ color: COLORS.muted, fontSize: '0.7rem', marginTop: '0.5rem' }}>
          WoW % uses paired cohort analysis — only listings with data on both days counted.
          n = listings in cohort.
        </div>
      )}
    </div>
  )
}
