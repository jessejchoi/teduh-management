import { createContext, useContext, useState } from 'react'
import FilterBar from './components/FilterBar.jsx'
import Cockpit from './components/Cockpit.jsx'
import Trends from './components/Trends.jsx'
import Occupancy from './components/Occupancy.jsx'
import SeasonalsLeadtime from './components/SeasonalsLeadtime.jsx'
import Discounts from './components/Discounts.jsx'
import Comps from './components/Comps.jsx'
import MyProperties from './components/MyProperties.jsx'

export const FilterContext = createContext({ segment: 'all', tier: 'all' })
export const useFilters = () => useContext(FilterContext)

export const COLORS = {
  bg: '#0f1117', surface: '#1a1d27', surface2: '#232735', border: '#2e3344',
  text: '#e4e6ef', muted: '#8b8fa3', accent: '#6c8cff', green: '#45d4a8',
  orange: '#ff8c6c', purple: '#c78cff', yellow: '#ffd06b', red: '#ff6b6b',
}

export const SEG_COLORS = { '3bed': '#6c8cff', '4bed': '#45d4a8', '6bed': '#ff8c6c' }
export const TIER_COLORS = { 1: '#6c8cff', 2: '#c78cff', 3: '#8b8fa3' }
export const PALETTE = [
  '#6c8cff','#45d4a8','#ff8c6c','#c78cff','#ffd06b','#ff6b6b',
  '#6bffd0','#ff6bab','#8cbaff','#d4ff6b','#6baaff','#ffab6b',
]

const TABS = [
  ['cockpit', '⬡ Cockpit'],
  ['trends', 'Trends'],
  ['occupancy', 'Occupancy'],
  ['seasonal', 'Seasonal & Lead Time'],
  ['discounts', 'Discounts'],
  ['comps', 'Comp Table'],
  ['properties', 'My Properties'],
]

const TAB_COMPONENTS = {
  cockpit: Cockpit,
  trends: Trends,
  occupancy: Occupancy,
  seasonal: SeasonalsLeadtime,
  discounts: Discounts,
  comps: Comps,
  properties: MyProperties,
}

export default function App() {
  const [tab, setTab] = useState('cockpit')
  const [segment, setSegment] = useState('all')
  const [tier, setTier] = useState('all')

  const TabContent = TAB_COMPONENTS[tab] || Cockpit

  return (
    <FilterContext.Provider value={{ segment, tier, setSegment, setTier }}>
      <div style={{
        fontFamily: "'DM Sans', system-ui, sans-serif",
        background: COLORS.bg, color: COLORS.text,
        minHeight: '100vh', padding: '1.25rem',
      }}>
        <div style={{ maxWidth: 1360, margin: '0 auto' }}>
          {/* Header */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.25rem' }}>
            <div>
              <h1 style={{ fontSize: '1.35rem', fontWeight: 700, letterSpacing: '-0.03em', marginBottom: 2 }}>
                Berawa Comp Intelligence
              </h1>
              <p style={{ color: COLORS.muted, fontSize: '0.75rem' }}>
                Live dashboard · auto-reads comp_data.db
              </p>
            </div>
            <FilterBar />
          </div>

          {/* Tabs */}
          <div style={{ display: 'flex', gap: 4, marginBottom: '1rem', flexWrap: 'wrap', borderBottom: `1px solid ${COLORS.border}`, paddingBottom: '0.5rem' }}>
            {TABS.map(([key, label]) => (
              <button key={key} onClick={() => setTab(key)} style={{
                padding: '6px 14px', fontSize: '0.78rem',
                fontWeight: tab === key ? 600 : 400,
                background: tab === key ? COLORS.surface2 : 'transparent',
                color: tab === key ? COLORS.text : COLORS.muted,
                border: `1px solid ${tab === key ? COLORS.border : 'transparent'}`,
                borderRadius: 6, cursor: 'pointer', fontFamily: 'inherit', transition: 'all 0.15s',
              }}>
                {label}
              </button>
            ))}
          </div>

          {/* Content */}
          <TabContent />
        </div>
      </div>
    </FilterContext.Provider>
  )
}
