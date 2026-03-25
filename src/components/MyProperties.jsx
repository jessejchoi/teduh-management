import { useState, useEffect } from 'react'
import { apiFetch } from '../api.js'
import { COLORS } from '../constants.js'
import { Card, SectionTitle, Empty, Loading, ErrorMsg, StatCard } from './ui.jsx'

function SetupInstructions() {
  return (
    <Card>
      <SectionTitle>My Properties — Setup Required</SectionTitle>
      <div style={{ color: COLORS.muted, fontSize: '0.82rem', lineHeight: 1.7 }}>
        <p style={{ marginBottom: '0.75rem' }}>No properties configured yet. To get started:</p>
        <ol style={{ paddingLeft: '1.25rem' }}>
          <li style={{ marginBottom: 6 }}>
            Add your villa:{' '}
            <code style={{ background: COLORS.surface2, padding: '2px 6px', borderRadius: 4, fontSize: '0.78rem', color: COLORS.accent }}>
              python3 scraper_v2.py add-property --name "Villa Name" --segment 3bed
            </code>
          </li>
          <li style={{ marginBottom: 6 }}>
            Import bookings:{' '}
            <code style={{ background: COLORS.surface2, padding: '2px 6px', borderRadius: 4, fontSize: '0.78rem', color: COLORS.accent }}>
              python3 scraper_v2.py import-bookings reservations.csv
            </code>
            <span style={{ marginLeft: 8, color: COLORS.muted, fontSize: '0.75rem' }}>
              (from Airbnb host dashboard → Reservations → Export CSV)
            </span>
          </li>
        </ol>
        <p style={{ marginTop: '0.75rem', fontSize: '0.75rem', color: COLORS.muted }}>
          See SCRAPER_README.md for full instructions.
        </p>
      </div>
    </Card>
  )
}

export default function MyProperties() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    setLoading(true)
    setError(null)
    apiFetch('properties')
      .then(setData)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <Loading />
  if (error) return <ErrorMsg error={error} />
  if (!data?.has_data) return <SetupInstructions />

  return (
    <div>
      {data.properties.map(prop => {
        const t1Median = data.t1_medians?.[`${prop.bedrooms}bed`]
        const hasBookings = prop.bookings?.length > 0

        return (
          <div key={prop.property_id} style={{ marginBottom: '1.5rem' }}>
            <SectionTitle style={{ fontSize: '0.95rem', color: COLORS.text, fontWeight: 600 }}>
              {prop.name}
              <span style={{ fontWeight: 400, marginLeft: 8, color: COLORS.muted, fontSize: '0.75rem' }}>
                {prop.bedrooms}BR · {prop.location}
              </span>
            </SectionTitle>

            {/* KPI row */}
            <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginBottom: '1rem' }}>
              <StatCard
                label="Bookings (30d)"
                value={prop.pace_30d.booking_count}
              />
              {prop.pace_30d.avg_rate && (
                <StatCard
                  label="Avg Nightly Rate"
                  value={`$${prop.pace_30d.avg_rate}`}
                  sub={t1Median ? `T1 median: $${t1Median}` : null}
                />
              )}
              {prop.pace_30d.total_revenue && (
                <StatCard
                  label="Revenue (30d)"
                  value={`$${prop.pace_30d.total_revenue.toLocaleString()}`}
                />
              )}
              {prop.pace_30d.avg_rate && t1Median && (
                <StatCard
                  label="vs T1 Market"
                  value={`${((prop.pace_30d.avg_rate - t1Median) / t1Median * 100).toFixed(1)}%`}
                  color={prop.pace_30d.avg_rate >= t1Median ? COLORS.green : COLORS.orange}
                />
              )}
            </div>

            {/* Bookings list */}
            {hasBookings ? (
              <Card>
                <SectionTitle>Recent Bookings</SectionTitle>
                <div style={{ overflowX: 'auto' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.78rem' }}>
                    <thead>
                      <tr>
                        {['Check-in', 'Check-out', 'Nights', 'Rate/Night', 'Platform'].map(h => (
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
                      {prop.bookings.slice(0, 20).map((b, i) => (
                        <tr key={i} style={{ borderBottom: `1px solid ${COLORS.border}22` }}>
                          <td style={{ padding: '5px 10px', fontFamily: 'monospace', fontSize: '0.75rem' }}>{b.checkin}</td>
                          <td style={{ padding: '5px 10px', fontFamily: 'monospace', fontSize: '0.75rem' }}>{b.checkout}</td>
                          <td style={{ padding: '5px 10px', fontFamily: 'monospace', fontSize: '0.75rem' }}>{b.nights || '—'}</td>
                          <td style={{ padding: '5px 10px', fontFamily: 'monospace', fontWeight: 600 }}>
                            {b.nightly_rate ? `$${Math.round(b.nightly_rate)}` : '—'}
                          </td>
                          <td style={{ padding: '5px 10px', color: COLORS.muted, fontSize: '0.75rem' }}>{b.platform || 'airbnb'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                {prop.bookings.length > 20 && (
                  <div style={{ color: COLORS.muted, fontSize: '0.72rem', marginTop: 6 }}>
                    Showing 20 of {prop.bookings.length} bookings
                  </div>
                )}
              </Card>
            ) : (
              <Card>
                <Empty text="No bookings imported yet. Run: python3 scraper_v2.py import-bookings reservations.csv" />
              </Card>
            )}
          </div>
        )
      })}
    </div>
  )
}
