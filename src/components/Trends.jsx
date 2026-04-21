import { useState, useEffect } from 'react'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer, ReferenceLine,
} from 'recharts'
import { apiFetch } from '../api.js'
import { useFilters } from '../App.jsx'
import { COLORS, SEG_COLORS } from '../constants.js'
import { Card, SectionTitle, Empty, Loading, ErrorMsg } from './ui.jsx'

function formatPct(v) {
  // Null guard — never return NaN
  if (v == null) return '—'
  return `${v > 0 ? '+' : ''}${v.toFixed(1)}%`
}

function formatShortDate(d) {
  return d?.slice(5) || d || '—'
}

function DateModeToggle({ value, onChange }) {
  return (
    <div style={{ display: 'flex', gap: 6 }}>
      {[['scrape_date', 'Scrape Date'], ['checkin_date', 'Listing Date']].map(([k, label]) => (
        <button key={k} onClick={() => onChange(k)} style={{
          padding: '5px 12px',
          fontSize: '0.75rem',
          background: value === k ? COLORS.accent : COLORS.surface2,
          color: value === k ? '#fff' : COLORS.muted,
          border: `1px solid ${value === k ? COLORS.accent : COLORS.border}`,
          borderRadius: 5,
          cursor: 'pointer',
          fontFamily: 'inherit',
        }}>
          {label}
        </button>
      ))}
    </div>
  )
}

function TrendsTooltip({ active, payload, label, labelPrefix, kind = 'pct' }) {
  if (!active || !payload?.length) return null
  return (
    <div style={{
      background: COLORS.surface2,
      border: `1px solid ${COLORS.border}`,
      borderRadius: 6,
      padding: '8px 12px',
      fontSize: '0.73rem',
    }}>
      <div style={{ color: COLORS.muted, marginBottom: 4 }}>
        {labelPrefix}: {label || '—'}
      </div>
      {payload[0]?.payload?.scrape_date && (
        <div style={{ color: COLORS.muted, marginBottom: 4 }}>
          Scrape date: {payload[0].payload.scrape_date}
        </div>
      )}
      {payload[0]?.payload?.checkin_date && (
        <div style={{ color: COLORS.muted, marginBottom: 4 }}>
          Listing date: {payload[0].payload.checkin_date}
        </div>
      )}
      {payload.map((p, i) => (
        <div key={i} style={{ color: p.color }}>
          {p.name}: {p.value != null
            ? kind === 'pct'
              ? formatPct(p.value)
              : `$${Math.round(p.value)}`
            : '—'}
        </div>
      ))}
    </div>
  )
}

export default function Trends() {
  const { segment, tier } = useFilters()
  const [data, setData] = useState(null)
  const [pctDateMode, setPctDateMode] = useState('scrape_date')
  const [rateDateMode, setRateDateMode] = useState('scrape_date')
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
      {!hasData ? (
        <Empty text={data?.message || 'Need 2+ daily scrapes to show trends.'} />
      ) : (
        <>
          <div style={{ marginBottom: '1.5rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, alignItems: 'center', marginBottom: 8, flexWrap: 'wrap' }}>
              <SectionTitle style={{ marginBottom: 0 }}>
                Week-on-Week % Change — T{tier === 'all' ? '1+' : tier} weekday avg
                <span style={{ fontWeight: 400, marginLeft: 8, fontSize: '0.7rem' }}>
                  (paired cohort — only listings present on both dates)
                </span>
              </SectionTitle>
              <DateModeToggle value={pctDateMode} onChange={setPctDateMode} />
            </div>
            <Card>
              <ResponsiveContainer width="100%" height={320}>
                <LineChart key={`pct-${pctDateMode}`} data={pctSeries}>
                  <CartesianGrid strokeDasharray="3 3" stroke={COLORS.border} />
                  <XAxis key={pctDateMode} dataKey={pctDateMode} tick={{ fill: COLORS.muted, fontSize: 11 }}
                    tickFormatter={formatShortDate} />
                  <YAxis tick={{ fill: COLORS.muted, fontSize: 11 }}
                    tickFormatter={v => v != null ? `${v > 0 ? '+' : ''}${v.toFixed(1)}%` : '—'} />
                  <Tooltip content={<TrendsTooltip labelPrefix={pctDateMode === 'scrape_date' ? 'Scrape date' : 'Listing date'} kind="pct" />} />
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
              Each point = avg of individual listing % changes vs prior scrape. Paired means we only use listings with a price on both comparison dates.
            </div>
          </div>
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, alignItems: 'center', marginBottom: 8, flexWrap: 'wrap' }}>
              <SectionTitle style={{ marginBottom: 0 }}>
                T{tier === 'all' ? '1+' : tier} Weekday Avg Rate — point-in-time snapshot
                <span style={{ fontWeight: 400, marginLeft: 8, fontSize: '0.7rem', color: COLORS.orange }}>
                  Note: composition may change between dates — use WoW % for trend analysis
                </span>
              </SectionTitle>
              <DateModeToggle value={rateDateMode} onChange={setRateDateMode} />
            </div>
            <Card>
              <ResponsiveContainer width="100%" height={320}>
                <LineChart key={`rate-${rateDateMode}`} data={rateSeries}>
                  <CartesianGrid strokeDasharray="3 3" stroke={COLORS.border} />
                  <XAxis key={rateDateMode} dataKey={rateDateMode} tick={{ fill: COLORS.muted, fontSize: 11 }}
                    tickFormatter={formatShortDate} />
                  <YAxis tick={{ fill: COLORS.muted, fontSize: 11 }}
                    tickFormatter={v => `$${Math.round(v)}`} />
                  <Tooltip content={<TrendsTooltip labelPrefix={rateDateMode === 'scrape_date' ? 'Scrape date' : 'Listing date'} kind="rate" />} />
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
          </div>
        </>
      )}
    </div>
  )
}
