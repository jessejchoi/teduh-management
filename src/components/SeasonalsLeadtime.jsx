import { useState, useEffect } from 'react'
import {
  BarChart, Bar, LineChart, Line,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, ReferenceLine, Cell,
} from 'recharts'
import { apiFetch } from '../api.js'
import { useFilters, COLORS, PALETTE } from '../App.jsx'
import { Card, SectionTitle, Empty, Loading, ErrorMsg } from './ui.jsx'
import { PctTooltip, CustomTooltip } from './ui.jsx'

function PctBar({ value }) {
  if (value == null) return <span style={{ color: COLORS.muted }}>—</span>
  const color = value > 10 ? COLORS.green : value < -10 ? COLORS.red : COLORS.yellow
  return (
    <span style={{ color, fontFamily: 'monospace', fontSize: '0.78rem' }}>
      {value > 0 ? '+' : ''}{value.toFixed(1)}%
    </span>
  )
}

export default function SeasonalsLeadtime() {
  const { segment, tier } = useFilters()
  const [seasonal, setSeasonal] = useState(null)
  const [leadtime, setLeadtime] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    setLoading(true)
    setError(null)
    Promise.all([
      apiFetch('seasonal', { segment, tier }),
      apiFetch('leadtime', { segment, tier }),
    ])
      .then(([s, l]) => { setSeasonal(s); setLeadtime(l); })
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [segment, tier])

  if (loading) return <Loading />
  if (error) return <ErrorMsg error={error} />

  return (
    <div>
      {/* ── Seasonal ── */}
      <SectionTitle style={{ marginBottom: 12 }}>
        Seasonal Multipliers — as % vs each listing's weekday baseline (paired)
        <span style={{ fontWeight: 400, marginLeft: 8, fontSize: '0.7rem' }}>
          {seasonal?.date || ''}
        </span>
      </SectionTitle>

      {seasonal?.data?.length > 0 ? (
        <>
          <Card style={{ marginBottom: '1.5rem' }}>
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={seasonal.data} layout="vertical" margin={{ left: 120 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={COLORS.border} />
                <XAxis
                  type="number"
                  tick={{ fill: COLORS.muted, fontSize: 10 }}
                  tickFormatter={v => `${v > 0 ? '+' : ''}${v.toFixed(0)}%`}
                />
                <YAxis type="category" dataKey="label" tick={{ fill: COLORS.muted, fontSize: 10 }} width={120} />
                <Tooltip
                  content={({ active, payload, label }) => {
                    if (!active || !payload?.length) return null
                    const d = payload[0]?.payload
                    return (
                      <div style={{
                        background: COLORS.surface2, border: `1px solid ${COLORS.border}`,
                        borderRadius: 6, padding: '8px 12px', fontSize: '0.73rem',
                      }}>
                        <div style={{ fontWeight: 600, marginBottom: 4 }}>{label}</div>
                        <div style={{ color: COLORS.muted }}>vs weekday baseline: <PctBar value={d?.pct_vs_baseline} /></div>
                        <div style={{ color: COLORS.muted }}>avg rate: ${d?.avg_seasonal}</div>
                        <div style={{ color: COLORS.muted }}>n = {d?.n} listings</div>
                      </div>
                    )
                  }}
                />
                <ReferenceLine x={0} stroke={COLORS.border} />
                <Bar dataKey="pct_vs_baseline" name="% vs baseline" radius={[0, 4, 4, 0]}>
                  {seasonal.data.map((d, i) => (
                    <Cell key={i} fill={d.pct_vs_baseline > 0 ? COLORS.green : COLORS.orange} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </Card>

          {/* Summary table */}
          <Card style={{ marginBottom: '2rem' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.78rem' }}>
              <thead>
                <tr>
                  {['Season', 'vs Baseline', 'Avg Rate', 'Baseline', 'n'].map(h => (
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
                {seasonal.data.map((d, i) => (
                  <tr key={i} style={{ borderBottom: `1px solid ${COLORS.border}22` }}>
                    <td style={{ padding: '5px 10px', fontWeight: 500 }}>{d.label}</td>
                    <td style={{ padding: '5px 10px' }}><PctBar value={d.pct_vs_baseline} /></td>
                    <td style={{ padding: '5px 10px', fontFamily: 'monospace' }}>${d.avg_seasonal}</td>
                    <td style={{ padding: '5px 10px', fontFamily: 'monospace', color: COLORS.muted }}>${d.avg_baseline}</td>
                    <td style={{ padding: '5px 10px', color: COLORS.muted }}>{d.n}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>
        </>
      ) : (
        <Empty text="No seasonal data. Run: python3 scraper_v2.py seasonal" />
      )}

      {/* ── Lead Time ── */}
      <SectionTitle style={{ marginBottom: 12 }}>
        Lead Time — relative to nearterm_14d anchor
        <span style={{ fontWeight: 400, marginLeft: 8, fontSize: '0.7rem' }}>
          {leadtime?.date || ''}
        </span>
      </SectionTitle>

      {leadtime?.immediate?.length > 0 ? (
        <>
          <Card style={{ marginBottom: '1.5rem' }}>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={leadtime.immediate} layout="vertical" margin={{ left: 130 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={COLORS.border} />
                <XAxis
                  type="number"
                  tick={{ fill: COLORS.muted, fontSize: 10 }}
                  tickFormatter={v => `${v > 0 ? '+' : ''}${v?.toFixed(0)}%`}
                />
                <YAxis type="category" dataKey="label" tick={{ fill: COLORS.muted, fontSize: 10 }} width={130} />
                <Tooltip
                  content={({ active, payload, label }) => {
                    if (!active || !payload?.length) return null
                    const d = payload[0]?.payload
                    return (
                      <div style={{
                        background: COLORS.surface2, border: `1px solid ${COLORS.border}`,
                        borderRadius: 6, padding: '8px 12px', fontSize: '0.73rem',
                      }}>
                        <div style={{ fontWeight: 600, marginBottom: 4 }}>{label}</div>
                        <div>avg rate: ${d?.avg_rate}</div>
                        {d?.pct_vs_anchor != null && (
                          <div style={{ color: COLORS.muted }}>vs anchor: <PctBar value={d?.pct_vs_anchor} /></div>
                        )}
                        <div style={{ color: COLORS.muted }}>n = {d?.n}</div>
                      </div>
                    )
                  }}
                />
                <ReferenceLine x={0} stroke={COLORS.border} />
                <Bar dataKey="pct_vs_anchor" name="% vs anchor" radius={[0, 4, 4, 0]}>
                  {leadtime.immediate.map((d, i) => (
                    <Cell key={i} fill={d.pct_vs_anchor > 0 ? COLORS.purple : COLORS.muted} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </Card>

          {/* Tracking time series */}
          {Object.entries(leadtime.tracking || {}).map(([key, points]) => {
            if (points.length < 2) return null
            const title = key.replace('track_peak_jul14', 'Peak (Jul 14)').replace('track_low_oct13', 'Low (Oct 13)')
            return (
              <div key={key} style={{ marginBottom: '1rem' }}>
                <SectionTitle>{title} — Price tracking over time (as market approaches date)</SectionTitle>
                <Card>
                  <ResponsiveContainer width="100%" height={200}>
                    <LineChart data={points}>
                      <CartesianGrid strokeDasharray="3 3" stroke={COLORS.border} />
                      <XAxis dataKey="date" tick={{ fill: COLORS.muted, fontSize: 10 }}
                        tickFormatter={d => d?.slice(5) || d} />
                      <YAxis tick={{ fill: COLORS.muted, fontSize: 10 }} tickFormatter={v => `$${v}`} />
                      <Tooltip content={<CustomTooltip />} />
                      <Line type="monotone" dataKey="avg_rate" name="Avg Rate"
                        stroke={COLORS.purple} strokeWidth={2} dot={{ r: 4 }} />
                    </LineChart>
                  </ResponsiveContainer>
                </Card>
              </div>
            )
          })}
        </>
      ) : (
        <Empty text="No lead time data. Run: python3 scraper_v2.py leadtime" />
      )}
    </div>
  )
}
