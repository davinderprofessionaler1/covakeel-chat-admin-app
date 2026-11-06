// The design surfaces use the same local FastAPI endpoints and JWT session.
export const BASE = (import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');
export class ApiError extends Error {
  constructor(message, status) { super(message); this.name = 'ApiError'; this.status = status; }
}
export async function api(path, { method = 'GET', body, auth = true, signal } = {}) {
  const token = localStorage.getItem('token');
  const headers = {};
  if (auth && token) headers.Authorization = `Bearer ${token}`;
  if (body !== undefined) headers['Content-Type'] = 'application/json';
  let response;
  try { response = await fetch(BASE + path, { method, headers, body: body === undefined ? undefined : JSON.stringify(body), signal }); }
  catch (error) { if (error.name === 'AbortError') throw error; throw new ApiError('Could not connect. Please try again.', 0); }
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    const detail = typeof data.detail === 'string' ? data.detail : data.detail?.[0]?.msg;
    if (response.status === 401 && auth) { localStorage.removeItem('token'); localStorage.removeItem('cv-user'); }
    throw new ApiError(detail || `Request failed (${response.status})`, response.status);
  }
  return response.status === 204 ? null : response.json();
}
export async function login(identifier, password) {
  const result = await api('/auth/login', { method: 'POST', auth: false, body: { username: identifier.trim(), password } });
  localStorage.setItem('token', result.access_token);
  const user = await api('/users/me');
  localStorage.setItem('cv-user', JSON.stringify(user));
  return user;
}
export async function register(name, email, password) {
  const base = name.normalize('NFKD').replace(/[^a-zA-Z0-9]/g, '').slice(0, 20) || 'member';
  // getRandomValues also works over HTTP on the local Wi-Fi network.
  const suffix = Array.from(crypto.getRandomValues(new Uint8Array(4)), (byte) => byte.toString(16).padStart(2, '0')).join('');
  const username = `${base}_${suffix}`;
  await api('/users/register', { method: 'POST', auth: false, body: { username, name: name.trim(), email: email.trim().toLowerCase(), password } });
  return login(email.trim(), password);
}
export function signout() {
  localStorage.removeItem('token'); localStorage.removeItem('cv-user');
  location.assign('/');
}
