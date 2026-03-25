import { useState, useEffect } from 'react'
import {
  AreaChart, Area, BarChart, Bar, XAxis, YAxis,
  CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell,
} from 'recharts'
import { apiFetch } from '../api.js'
import { useFilters } from '../App.jsx'
import { COLORS, SEG_COLORS } from '../constants.js'
import { Card, SectionTitle, Empty, Loading, ErrorMsg, TierBadge } from './ui.jsx'
import { CustomTooltip } from './ui.jsx'

export default function Occupancy() {
  const { segment, tier } = useFilters()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    setLoading(true)
    setError(null)
    apiFetch('occupancy', { segment, tier })
      .then(setData)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [segment, tier])

  if (loading) return <Loading />
  if (error) return <ErrorMsg error={error} />

  const segs = segment === 'all' ? ['3bed', '4bed', '6bed'] : [segment]

  // Build unified daily trend series
  const allDates = [
    ...new Set(
      Object.values(data?.by_segment || {}).flatMap(arr => arr.map(r => r.date))
    ),
  ].sort()

  const trendData = allDates.map(dt => {
    const entry = { date: dt.slice(5) }
    for (const seg of segs) {
      const found = data?.by_segment?.[seg]?.find(r => r.date === dt)
      entry[seg] = found?.pct ?? null
    }
    return entry
  })

  const compOcc = data?.by_comp || []

  return (
    <div>
      {trendData.length > 1 ? (
        <>
          <SectionTitle>Daily Occupancy Rate (T{tier === 'all' ? '1' : tier})</SectionTitle>
          <Card style={{ marginBottom: '1.5rem' }}>
            <ResponsiveContainer width="100%" height={280}>
              <AreaChart data={trendData}>
                <CartesianGrid strokeDasharray="3 3" stroke={COLORS.border} />
                <XAxis dataKey="date" tick={{ fill: COLORS.muted, fontSize: 10 }} />
                <YAxis domain={[0, 100]} tick={{ fill: COLORS.muted, fontSize: 10 }}
                  tickFormatter={v => `${v}%`} />
                <Tooltip content={<CustomTooltip prefix="" suffix="%" />} />
                <Legend wrapperStyle={{ fontSize: '0.75rem' }} />
                {segs.map(seg => (
                  <Area
                    key={seg}
                    type="monotone"
                    dataKey={seg}
                    name={seg.replace('bed', '-Bed')}
                    stroke={SEG_COLORS[seg]}
                    fill={SEG_COLORS[seg] + '22'}
                    connectNulls={false}
                  />
                ))}
              </AreaChart>
            </ResponsiveContainer>
          </Card>
        </>
      ) : (
        <Empty text="Need 2+ days of occupancy checks. Run: python3 scraper_v2.py run" />
      )}

      {compOcc.length > 0 && (
        <>
          <SectionTitle>Cumulative Occupancy by Comp</SectionTitle>
          <Card>
            <ResponsiveContainer width="100%" height={Math.max(220, compOcc.length * 28)}>
              <BarChart data={compOcc} layout="vertical" margin={{ left: 140 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={COLORS.border} />
                <XAxis type="number" domain={[0, 100]} tick={{ fill: COLORS.muted, fontSize: 10 }}
                  tickFormatter={v => `${v}%`} />
                <YAxis
                  type="category"
                  dataKey="name"
                  tick={{ fill: COLORS.muted, fontSize: 10 }}
                  width={140}
                  tickFormatter={v => (v || '').slice(0, 25)}
                />
                <Tooltip
                  content={({ active, payload, label }) => {
                    if (!active || !payload?.length) return null
                    const d = payload[0]?.payload
                    return (
                      <div style={{
                        background: COLORS.surface2, border: `1px solid ${COLORS.border}`,
                        borderRadius: 6, padding: '8px 12px', fontSize: '0.73rem',
                      }}>
                        <div style={{ color: COLORS.muted, marginBottom: 4 }}>{label}</div>
                        <div>{d?.occ_pct}% ({d?.booked}/{d?.total} days)</div>
                      </div>
                    )
                  }}
                />
                <Bar dataKey="occ_pct" name="Occupancy" radius={[0, 4, 4, 0]}>
                  {compOcc.map((d, i) => (
                    <Cell
                      key={i}
                      fill={d.occ_pct >= 70 ? COLORS.green : d.occ_pct >= 50 ? COLORS.yellow : COLORS.red}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </>
      )}

      {!trendData.length && !compOcc.length && (
        <Empty text="No occupancy data yet. Run the daily scraper to collect check-in/out data." />
      )}
    </div>
  )
}
