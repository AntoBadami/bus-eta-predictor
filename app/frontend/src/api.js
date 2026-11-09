async function get(url) {
  const r = await fetch(url)
  if (!r.ok) {
    const e = await r.json().catch(() => ({}))
    throw new Error(e.detail || `Error ${r.status}`)
  }
  return r.json()
}

export const getVehicles = (direction) => get(`/api/vehicles?direction=${direction}`)
export const getEta = (busId) => get(`/api/vehicles/${encodeURIComponent(busId)}/eta`)