import { useFilters, COLORS } from '../App.jsx'

const selectStyle = {
  marginLeft: 6, background: COLORS.surface2, color: COLORS.text,
  border: `1px solid ${COLORS.border}`, borderRadius: 4,
  padding: '4px 8px', fontSize: '0.78rem', fontFamily: 'inherit', cursor: 'pointer',
}

export default function FilterBar() {
  const { segment, tier, setSegment, setTier } = useFilters()

  return (
    <div style={{ display: 'flex', gap: '1rem', alignItems: 'center', fontSize: '0.78rem' }}>
      <label style={{ color: COLORS.muted }}>
        Segment:
        <select value={segment} onChange={e => setSegment(e.target.value)} style={selectStyle}>
          <option value="all">All</option>
          <option value="3bed">3-Bed</option>
          <option value="4bed">4-Bed</option>
          <option value="6bed">6-Bed</option>
        </select>
      </label>
      <label style={{ color: COLORS.muted }}>
        Tier:
        <select value={tier} onChange={e => setTier(e.target.value)} style={selectStyle}>
          <option value="all">All</option>
          <option value="1">T1 Direct</option>
          <option value="2">T2 Aspirational</option>
          <option value="3">T3 Floor</option>
        </select>
      </label>
    </div>
  )
}
