// Centralized API fetch — adds Bearer auth and strips 'all' filter values.
// In dev: Vite proxies /api/* → localhost:5001
// In prod: same origin as FastAPI, relative /api/* works directly

const API_KEY = import.meta.env.VITE_API_KEY || 'dev-key'

function buildParams(filters = {}) {
  const params = new URLSearchParams()
  for (const [key, val] of Object.entries(filters)) {
    if (val && val !== 'all') {
      params.set(key, val)
    }
  }
  params.set('api_key', API_KEY)
  const str = params.toString()
  return str ? `?${str}` : ''
}

export async function apiFetch(path, filters = {}) {
  const url = `/api/${path}${buildParams(filters)}`
  const res = await fetch(url, {
    headers: { Authorization: `Bearer ${API_KEY}` },
  })
  if (res.status === 401) throw new Error('Unauthorized — check VITE_API_KEY')
  if (!res.ok) throw new Error(`API error ${res.status}: ${await res.text()}`)
  return res.json()
}
