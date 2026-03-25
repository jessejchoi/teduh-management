import { useState, useEffect } from 'react'
import { apiFetch } from '../api.js'
import { useFilters } from '../App.jsx'
import { COLORS, SEG_COLORS } from '../constants.js'
import { Card, SectionTitle, Empty, Loading, ErrorMsg, TierBadge } from './ui.jsx'

function DiscBar({ pct }) {
  if (pct == null) return <span style={{ color: COLORS.muted }}>—</span>
  const color = pct >= 15 ? COLORS.green : pct >= 8 ? COLORS.yellow : COLORS.muted
  return <span style={{ color, fontFamily: 'monospace', fontSize: '0.78rem' }}>-{pct}%</span>
}

export default function Discounts() {
  const { segment, tier } = useFilters()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    setLoading(true)
    setError(null)
    apiFetch('discounts', { segment, tier })
      .then(setData)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [segment, tier])

  if (loading) return <Loading />
  if (error) return <ErrorMsg error={error} />

  const segs = segment === 'all' ? ['3bed', '4bed', '6bed'] : [segment]
  const hasData = data?.data && Object.values(data.data).some(arr => arr.length > 0)

  if (!hasData) {
    return <Empty text="No discount data. Run: python3 scraper_v2.py discounts" />
  }

  return (
    <div>
      <div style={{ color: COLORS.muted, fontSize: '0.72rem', marginBottom: '1rem' }}>
        As of {data.date}. Discount % = how much cheaper per-night vs 3-night baseline.
        Green = meaningful discount (≥15%), yellow = slight.
      </div>

      {segs.map(seg => {
        const rows = data.data[seg]
        if (!rows?.length) return null
        const filtered = tier === 'all' ? rows : rows.filter(r => String(r.tier) === tier)
        if (!filtered.length) return null

        return (
          <div key={seg} style={{ marginBottom: '1.5rem' }}>
            <SectionTitle style={{ color: SEG_COLORS[seg] }}>
              {seg.replace('bed', '-Bed')}
            </SectionTitle>
            <Card>
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.78rem' }}>
                  <thead>
                    <tr>
                      {['Listing', 'Tier', '3-Night', '7-Night', '7n Disc', '28-Night', '28n Disc'].map(h => (
                        <th key={h} style={{
                          textAlign: 'left', padding: '6px 10px',
                          borderBottom: `1px solid ${COLORS.border}`,
                          color: COLORS.muted, fontWeight: 500, fontSize: '0.68rem',
                          textTransform: 'uppercase',
                        }}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {filtered.map((r, i) => (
                      <tr key={i} style={{ borderBottom: `1px solid ${COLORS.border}22` }}>
                        <td style={{ padding: '6px 10px', maxWidth: 200 }}>
                          <a
                            href={`https://www.airbnb.com/rooms/${r.listing_id}`}
                            target="_blank" rel="noopener"
                            style={{ color: COLORS.accent, textDecoration: 'none', fontSize: '0.75rem' }}
                          >
                            {r.name}
                          </a>
                        </td>
                        <td style={{ padding: '6px 10px' }}><TierBadge tier={r.tier} /></td>
                        <td style={{ padding: '6px 10px', fontFamily: 'monospace', fontWeight: 600 }}>
                          ${r.rate_3n}
                        </td>
                        <td style={{ padding: '6px 10px', fontFamily: 'monospace' }}>
                          {r.rate_7n ? `$${r.rate_7n}` : '—'}
                        </td>
                        <td style={{ padding: '6px 10px' }}><DiscBar pct={r.disc_7n_pct} /></td>
                        <td style={{ padding: '6px 10px', fontFamily: 'monospace' }}>
                          {r.rate_28n ? `$${r.rate_28n}` : '—'}
                        </td>
                        <td style={{ padding: '6px 10px' }}><DiscBar pct={r.disc_28n_pct} /></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
          </div>
        )
      })}
    </div>
  )
}
