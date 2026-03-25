// Shared UI primitives used across all tab components
import { COLORS, TIER_COLORS } from '../App.jsx'

export const Card = ({ children, style }) => (
  <div style={{
    background: COLORS.surface, border: `1px solid ${COLORS.border}`,
    borderRadius: 10, padding: '1rem', ...style,
  }}>
    {children}
  </div>
)

export const SectionTitle = ({ children, style }) => (
  <h3 style={{ fontSize: '0.82rem', color: COLORS.muted, marginBottom: 8, fontWeight: 500, ...style }}>
    {children}
  </h3>
)

export const Empty = ({ text }) => (
  <div style={{ color: COLORS.muted, fontStyle: 'italic', padding: '2rem', textAlign: 'center', fontSize: '0.85rem' }}>
    {text}
  </div>
)

export const Loading = () => (
  <div style={{ color: COLORS.muted, padding: '2rem', textAlign: 'center', fontSize: '0.85rem' }}>
    Loading…
  </div>
)

export const ErrorMsg = ({ error }) => (
  <div style={{ color: COLORS.red, padding: '2rem', textAlign: 'center', fontSize: '0.85rem' }}>
    {error}
  </div>
)

export const TierBadge = ({ tier }) => (
  <span style={{
    padding: '2px 7px', borderRadius: 4, fontSize: '0.68rem', fontWeight: 600,
    fontFamily: "'JetBrains Mono', monospace",
    background: `${TIER_COLORS[tier]}22`, color: TIER_COLORS[tier],
  }}>
    T{tier}
  </span>
)

export const StatCard = ({ label, value, sub, color, trend }) => (
  <Card style={{ textAlign: 'center', minWidth: 130 }}>
    <div style={{
      fontFamily: "'JetBrains Mono', monospace",
      fontSize: '1.55rem', fontWeight: 700,
      color: color || COLORS.text,
    }}>
      {value ?? '—'}
    </div>
    <div style={{ color: COLORS.muted, fontSize: '0.72rem', marginTop: 4 }}>{label}</div>
    {sub != null && (
      <div style={{
        fontSize: '0.72rem', fontFamily: "'JetBrains Mono', monospace",
        marginTop: 4,
        color: typeof sub === 'number'
          ? sub > 0 ? COLORS.green : sub < 0 ? COLORS.red : COLORS.muted
          : COLORS.muted,
      }}>
        {sub}
      </div>
    )}
  </Card>
)

export const CustomTooltip = ({ active, payload, label, prefix = '$', suffix = '' }) => {
  if (!active || !payload?.length) return null
  return (
    <div style={{
      background: COLORS.surface2, border: `1px solid ${COLORS.border}`,
      borderRadius: 6, padding: '8px 12px', fontSize: '0.73rem',
    }}>
      <div style={{ color: COLORS.muted, marginBottom: 4 }}>{label}</div>
      {payload.map((p, i) => (
        <div key={i} style={{ color: p.color }}>
          {p.name}: {p.value != null ? `${prefix}${typeof p.value === 'number' ? p.value.toFixed(prefix === '$' ? 0 : 1) : p.value}${suffix}` : '—'}
        </div>
      ))}
    </div>
  )
}

export const PctTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div style={{
      background: COLORS.surface2, border: `1px solid ${COLORS.border}`,
      borderRadius: 6, padding: '8px 12px', fontSize: '0.73rem',
    }}>
      <div style={{ color: COLORS.muted, marginBottom: 4 }}>{label}</div>
      {payload.map((p, i) => (
        <div key={i} style={{ color: p.color }}>
          {p.name}: {p.value != null ? `${p.value > 0 ? '+' : ''}${p.value.toFixed(1)}%` : '—'}
        </div>
      ))}
    </div>
  )
}
