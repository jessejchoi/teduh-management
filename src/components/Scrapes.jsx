import { useState } from 'react'
import { Card, SectionTitle } from './ui.jsx'
import { COLORS } from '../constants.js'

const SCRAPE_MODES = [
  {
    command: 'python3 scraper.py daily',
    title: 'Daily',
    description: 'Weekday + weekend rate scrape for roughly 2 weeks out on a 3-night stay.',
    scope: 'All 56 comps',
    timing: '~25–40 min',
  },
  {
    command: 'python3 scraper.py discounts',
    title: 'Discounts',
    description: 'Scrapes 3-night, 7-night, and 28-night rates for T1+T2 comps to measure weekly and monthly discounts.',
    scope: 'T1+T2 comps',
    timing: '~60–90 min',
  },
  {
    command: 'python3 scraper.py seasonal',
    title: 'Seasonal',
    description: 'Scrapes rates across six seasonal windows for T1+T2 comps.',
    scope: 'T1+T2 comps',
    timing: '~90–120 min',
  },
  {
    command: 'python3 scraper.py leadtime',
    title: 'Lead Time',
    description: 'Scrapes near-term and future tracking dates to build lead-time pricing curves.',
    scope: 'T1+T2 comps',
    timing: '~60–90 min',
  },
  {
    command: 'python3 scraper.py full',
    title: 'Full',
    description: 'Runs daily, discounts, seasonal, and leadtime sequentially in one long job.',
    scope: 'Combined run',
    timing: '~2.5–3 hrs',
  },
  {
    command: 'python3 scraper.py minstay',
    title: 'Min Stay Audit',
    description: 'Audits minimum-stay requirements directly from listing pages.',
    scope: 'Audit run',
    timing: 'varies',
  },
  {
    command: 'python3 scraper.py test <ID>',
    title: 'Single Listing Test',
    description: 'Quick smoke test for one Airbnb listing ID before running a wider scrape.',
    scope: '1 comp',
    timing: '~2 min',
  },
  {
    command: 'python3 scraper.py test-all',
    title: 'Test All',
    description: 'Runs the major scrape modes on a 2-comp sample, or one specified listing ID.',
    scope: '2 comps by default',
    timing: '~10–15 min',
  },
  {
    command: 'python3 scraper.py export',
    title: 'Export',
    description: 'Dumps data to CSV files in `/exports`.',
    scope: 'No scrape',
    timing: 'instant',
  },
  {
    command: 'python3 scraper.py dashboard',
    title: 'Terminal Summary',
    description: 'Prints the pricing dashboard summary in the terminal.',
    scope: 'No scrape',
    timing: 'instant',
  },
  {
    command: 'python3 scraper.py occupancy',
    title: 'Occupancy Summary',
    description: 'Prints the occupancy summary in the terminal.',
    scope: 'No scrape',
    timing: 'instant',
  },
]

const COMMAND_PREFIX = 'cd ~/documents/coding/teduh-management &&'

export default function Scrapes() {
  const [copiedCommand, setCopiedCommand] = useState(null)

  async function copyCommand(command) {
    try {
      await navigator.clipboard.writeText(`${COMMAND_PREFIX} ${command}`)
      setCopiedCommand(command)
      window.setTimeout(() => {
        setCopiedCommand(current => (current === command ? null : current))
      }, 1500)
    } catch {
      setCopiedCommand(null)
    }
  }

  return (
    <div>
      <SectionTitle>Scrape Command Reference</SectionTitle>
      <div style={{ color: COLORS.muted, fontSize: '0.76rem', marginBottom: '1rem' }}>
        Commands from `SCRAPER_README.md`, kept here as a quick in-app reference.
      </div>

      <div style={{ display: 'grid', gap: 12 }}>
        {SCRAPE_MODES.map(mode => (
          <Card key={mode.command} style={{ padding: '0.9rem 1rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, alignItems: 'flex-start', flexWrap: 'wrap' }}>
              <div>
                <div style={{ fontSize: '0.84rem', fontWeight: 600, marginBottom: 6 }}>
                  {mode.title}
                </div>
                <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
                  <code style={{
                    display: 'inline-block',
                    background: COLORS.surface2,
                    border: `1px solid ${COLORS.border}`,
                    borderRadius: 6,
                    padding: '6px 8px',
                    fontSize: '0.76rem',
                    color: COLORS.text,
                  }}>
                    {mode.command}
                  </code>
                  <button
                    onClick={() => copyCommand(mode.command)}
                    style={{
                      padding: '6px 10px',
                      fontSize: '0.72rem',
                      background: copiedCommand === mode.command ? COLORS.green : COLORS.surface2,
                      color: copiedCommand === mode.command ? COLORS.bg : COLORS.text,
                      border: `1px solid ${copiedCommand === mode.command ? COLORS.green : COLORS.border}`,
                      borderRadius: 6,
                      cursor: 'pointer',
                      fontFamily: 'inherit',
                    }}
                  >
                    {copiedCommand === mode.command ? 'Copied' : 'Copy'}
                  </button>
                </div>
              </div>
              <div style={{ textAlign: 'right', fontSize: '0.72rem', color: COLORS.muted }}>
                <div>{mode.scope}</div>
                <div>{mode.timing}</div>
              </div>
            </div>
            <div style={{ marginTop: 10, fontSize: '0.78rem', color: COLORS.text }}>
              {mode.description}
            </div>
          </Card>
        ))}
      </div>
    </div>
  )
}
