// API 客户端
const TOKEN_KEY = 'nutrivision_token'
const USER_KEY = 'nutrivision_user'

export function getToken() { return localStorage.getItem(TOKEN_KEY) }
export function getUser() {
  try { return JSON.parse(localStorage.getItem(USER_KEY) || 'null') } catch { return null }
}
export function setSession(token, username) {
  localStorage.setItem(TOKEN_KEY, token)
  localStorage.setItem(USER_KEY, JSON.stringify({ username }))
}
export function clearSession() {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(USER_KEY)
}

async function requestText(path, { method = 'GET' } = {}) {
  const headers = {}
  const token = getToken()
  if (token) headers['Authorization'] = `Bearer ${token}`
  const res = await fetch(`/api${path}`, { method, headers })
  if (res.status === 401) {
    clearSession()
    window.location.href = '/login'
    throw new Error('登录已过期')
  }
  if (!res.ok) {
    let msg = `请求失败 (${res.status})`
    try { const d = await res.json(); msg = d.detail || msg } catch {}
    throw new Error(msg)
  }
  return res.text()
}

async function request(path, { method = 'GET', body, formData } = {}) {
  const headers = {}
  const token = getToken()
  if (token) headers['Authorization'] = `Bearer ${token}`
  let payload = body
  if (formData) {
    payload = formData
  } else if (body) {
    headers['Content-Type'] = 'application/json'
    payload = JSON.stringify(body)
  }
  const res = await fetch(`/api${path}`, { method, headers, body: payload })
  if (res.status === 401) {
    clearSession()
    window.location.href = '/login'
    throw new Error('登录已过期')
  }
  if (!res.ok) {
    let msg = `请求失败 (${res.status})`
    try { const d = await res.json(); msg = d.detail || msg } catch {}
    throw new Error(msg)
  }
  return res.json()
}

export const api = {
  register: (username, password) => request('/auth/register', { method: 'POST', body: { username, password } }),
  login: (username, password) => request('/auth/login', { method: 'POST', body: { username, password } }),
  me: () => request('/auth/me'),
  analyze: (formData) => request('/analyze', { method: 'POST', formData }),
  history: (date) => request(`/history${date ? `?date=${date}` : ''}`),
  saveHistory: (item) => request('/history', { method: 'POST', body: item }),
  deleteHistory: (id) => request(`/history/${id}`, { method: 'DELETE' }),
  updateHistory: (id, item) => request(`/history/${id}`, { method: 'PUT', body: item }),
  clearHistory: () => request('/history', { method: 'DELETE' }),
  getPlan: () => request('/plan'),
  updatePlan: (target_calories, goal, reminder_enabled, protein_goal, carb_goal, fat_goal, profile, calorie_mode, adjustment) => request('/plan', { method: 'PUT', body: { target_calories, goal, reminder_enabled, protein_goal, carb_goal, fat_goal, ...(profile || {}), calorie_mode, adjustment } }),
  getDay: (date) => request(`/day?date=${date || ''}`),
  getStats: (days) => request(`/stats?days=${days || 7}`),
  searchProducts: (q) => request(`/products?q=${encodeURIComponent(q)}`),
  getProfile: () => request('/profile'),
  updateProfile: (profile) => request('/profile', { method: 'PUT', body: profile }),
  getTips: () => request('/tips'),
  getBadges: () => request('/badges'),
  getReport: (days) => requestText(`/report?days=${days || 7}`),
  getCompensate: (date) => request(`/compensate?date_str=${date || ''}`),
}
