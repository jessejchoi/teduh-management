import { useState, useEffect } from 'react'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer, ReferenceLine,
} from 'recharts'
import { apiFetch } from '../api.js'
import { useFilters } from '../App.jsx'
import { COLORS, SEG_COLORS } from '../constants.js'
import { Card, SectionTitle, Empty, Loading, ErrorMsg } from './ui.jsx'
import { PctTooltip, CustomTooltip } from './ui.jsx'

function formatPct(v) {
  // Null guard — never return NaN
  if (v == null) return '—'
  return `${v > 0 ? '+' : ''}${v.toFixed(1)}%`
}

export default function Trends() {
  const { segment, tier } = useFilters()
  const [data, setData] = useState(null)
  const [view, setView] = useState('pct') // 'pct' | 'rate'
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    setLoading(true)
    setError(null)
    apiFetch('trends', { segment, tier })
      .then(setData)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [segment, tier])

  if (loading) return <Loading />
  if (error) return <ErrorMsg error={error} />

  const segs = segment === 'all' ? ['3bed', '4bed', '6bed'] : [segment]
  const pctSeries = data?.pct_series || []
  const rateSeries = data?.rate_series || []
  const hasData = pctSeries.length > 0

  return (
    <div>
      {/* View toggle */}
      <div style={{ display: 'flex', gap: 6, marginBottom: '1rem' }}>
        {[['pct', 'WoW % Change (paired)'], ['rate', 'Market Rate (absolute)']].map(([k, label]) => (
          <button key={k} onClick={() => setView(k)} style={{
            padding: '5px 12px', fontSize: '0.75rem',
            background: view === k ? COLORS.accent : COLORS.surface2,
            color: view === k ? '#fff' : COLORS.muted,
            border: `1px solid ${view === k ? COLORS.accent : COLORS.border}`,
            borderRadius: 5, cursor: 'pointer', fontFamily: 'inherit',
          }}>
            {label}
          </button>
        ))}
      </div>

      {!hasData ? (
        <Empty text={data?.message || 'Need 2+ daily scrapes to show trends.'} />
      ) : view === 'pct' ? (
        <>
          <SectionTitle>
            Week-on-Week % Change — T{tier === 'all' ? '1+' : tier} weekday avg
            <span style={{ fontWeight: 400, marginLeft: 8, fontSize: '0.7rem' }}>
              (paired cohort — only listings present on both dates)
            </span>
          </SectionTitle>
          <Card>
            <ResponsiveContainer width="100%" height={320}>
              <LineChart data={pctSeries}>
                <CartesianGrid strokeDasharray="3 3" stroke={COLORS.border} />
                <XAxis dataKey="date" tick={{ fill: COLORS.muted, fontSize: 11 }}
                  tickFormatter={d => d?.slice(5) || d} />
                <YAxis tick={{ fill: COLORS.muted, fontSize: 11 }}
                  tickFormatter={v => v != null ? `${v > 0 ? '+' : ''}${v.toFixed(1)}%` : '—'} />
                <Tooltip content={<PctTooltip />} />
                <Legend wrapperStyle={{ fontSize: '0.75rem' }} />
                <ReferenceLine y={0} stroke={COLORS.border} strokeWidth={1.5} />
                {segs.map(seg => (
                  <Line
                    key={seg}
                    type="monotone"
                    dataKey={seg}
                    name={seg.replace('bed', '-Bed')}
                    stroke={SEG_COLORS[seg]}
                    strokeWidth={2}
                    dot={{ r: 3 }}
                    connectNulls={false}
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </Card>
          <div style={{ color: COLORS.muted, fontSize: '0.7rem', marginTop: 6 }}>
            Each point = avg of individual listing % changes vs prior day. Listings missing either date are excluded.
          </div>
        </>
      ) : (
        <>
          <SectionTitle>
            T{tier === 'all' ? '1+' : tier} Weekday Avg Rate — point-in-time snapshot
            <span style={{ fontWeight: 400, marginLeft: 8, fontSize: '0.7rem', color: COLORS.orange }}>
              Note: composition may change between dates — use WoW % for trend analysis
            </span>
          </SectionTitle>
          <Card>
            <ResponsiveContainer width="100%" height={320}>
              <LineChart data={rateSeries}>
                <CartesianGrid strokeDasharray="3 3" stroke={COLORS.border} />
                <XAxis dataKey="date" tick={{ fill: COLORS.muted, fontSize: 11 }}
                  tickFormatter={d => d?.slice(5) || d} />
                <YAxis tick={{ fill: COLORS.muted, fontSize: 11 }}
                  tickFormatter={v => `$${Math.round(v)}`} />
                <Tooltip content={<CustomTooltip />} />
                <Legend wrapperStyle={{ fontSize: '0.75rem' }} />
                {segs.map(seg => (
                  <Line
                    key={seg}
                    type="monotone"
                    dataKey={seg}
                    name={seg.replace('bed', '-Bed')}
                    stroke={SEG_COLORS[seg]}
                    strokeWidth={2}
                    dot={{ r: 3 }}
                    connectNulls={false}
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </Card>
        </>
      )}
    </div>
  )
}
