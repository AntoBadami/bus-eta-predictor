async function request(url, options) {
  const res = await fetch(url, options)
  const data = await res.json().catch(() => ({}))
  if (!res.ok) throw new Error(data.detail || `Error ${res.status}`)
  return data
}

export const getVehicles = (direction) => request(`/api/vehicles?direction=${direction}`)
export const getStops = (direction) => request(`/api/stops?direction=${direction}`)
export const getEta = (payload) =>
  request('/api/eta', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })