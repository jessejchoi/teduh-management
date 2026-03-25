import { useState, useEffect } from 'react'
import { apiFetch } from '../api.js'
import { useFilters, COLORS, SEG_COLORS } from '../App.jsx'
import { Card, SectionTitle, Empty, Loading, ErrorMsg, TierBadge } from './ui.jsx'

function WoWBadge({ pct }) {
  if (pct == null) return null
  const color = pct > 0 ? COLORS.green : pct < 0 ? COLORS.red : COLORS.muted
  return (
    <span style={{ color, fontSize: '0.68rem', fontFamily: 'monospace', marginLeft: 6 }}>
      {pct > 0 ? '▲' : pct < 0 ? '▼' : '→'}{Math.abs(pct).toFixed(1)}%
    </span>
  )
}

export default function Comps() {
  const { segment, tier } = useFilters()
  const [data, setData] = useState(null)
  const [sortKey, setSortKey] = useState('weekday')
  const [sortDir, setSortDir] = useState(-1)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    setLoading(true)
    setError(null)
    apiFetch('comps', { segment, tier })
      .then(setData)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [segment, tier])

  if (loading) return <Loading />
  if (error) return <ErrorMsg error={error} />

  const comps = data?.comps || []
  if (!comps.length) return <Empty text="No comp data found for the selected filters." />

  const toggle = (key) => {
    if (sortKey === key) setSortDir(d => -d)
    else { setSortKey(key); setSortDir(-1) }
  }

  const sorted = [...comps].sort((a, b) => {
    const va = a[sortKey] ?? -Infinity
    const vb = b[sortKey] ?? -Infinity
    return (va > vb ? 1 : -1) * sortDir
  })

  const segs = segment === 'all' ? ['3bed', '4bed', '6bed'] : [segment]
  const headers = [
    { key: 'name', label: 'Listing' },
    { key: 'segment', label: 'Seg' },
    { key: 'tier', label: 'Tier' },
    { key: 'rating', label: 'Rating' },
    { key: 'review_count', label: 'Reviews' },
    { key: 'min_stay', label: 'Min Stay' },
    { key: 'weekday', label: 'Weekday' },
    { key: 'weekend', label: 'Weekend' },
    { key: 'wow_pct', label: 'WoW %' },
  ]

  return (
    <div>
      <div style={{ color: COLORS.muted, fontSize: '0.72rem', marginBottom: '0.75rem' }}>
        As of {data?.date}. WoW % = weekday rate change vs previous scrape (paired per-listing).
        Click column headers to sort.
      </div>
      <Card>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.78rem' }}>
            <thead>
              <tr>
                {headers.map(h => (
                  <th
                    key={h.key}
                    onClick={() => toggle(h.key)}
                    style={{
                      textAlign: 'left', padding: '7px 10px',
                      borderBottom: `1px solid ${COLORS.border}`,
                      color: sortKey === h.key ? COLORS.accent : COLORS.muted,
                      fontWeight: 500, fontSize: '0.68rem',
                      textTransform: 'uppercase', letterSpacing: '0.04em',
                      cursor: 'pointer', userSelect: 'none', whiteSpace: 'nowrap',
                    }}
                  >
                    {h.label} {sortKey === h.key ? (sortDir === -1 ? '↓' : '↑') : ''}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {sorted.map((comp, i) => (
                <tr
                  key={comp.listing_id}
                  style={{ borderBottom: `1px solid ${COLORS.border}22` }}
                >
                  <td style={{ padding: '6px 10px', maxWidth: 220 }}>
                    <a
                      href={`https://www.airbnb.com/rooms/${comp.listing_id}`}
                      target="_blank" rel="noopener"
                      style={{ color: COLORS.accent, textDecoration: 'none' }}
                    >
                      {(comp.name || comp.listing_id).slice(0, 40)}
                    </a>
                  </td>
                  <td style={{ padding: '6px 10px', color: SEG_COLORS[comp.segment] }}>
                    {comp.segment?.replace('bed', '-Bed')}
                  </td>
                  <td style={{ padding: '6px 10px' }}><TierBadge tier={comp.tier} /></td>
                  <td style={{ padding: '6px 10px', fontFamily: 'monospace', fontSize: '0.75rem' }}>
                    {comp.rating || '—'}
                  </td>
                  <td style={{ padding: '6px 10px', fontFamily: 'monospace', fontSize: '0.75rem' }}>
                    {comp.review_count || '—'}
                  </td>
                  <td style={{ padding: '6px 10px', fontFamily: 'monospace', fontSize: '0.75rem' }}>
                    {comp.min_stay ? `${comp.min_stay}n` : '—'}
                  </td>
                  <td style={{ padding: '6px 10px', fontFamily: 'monospace', fontWeight: 600 }}>
                    {comp.weekday ? `$${comp.weekday}` : '—'}
                  </td>
                  <td style={{ padding: '6px 10px', fontFamily: 'monospace' }}>
                    {comp.weekend ? `$${comp.weekend}` : '—'}
                  </td>
                  <td style={{ padding: '6px 10px' }}>
                    <WoWBadge pct={comp.wow_pct} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  )
}
