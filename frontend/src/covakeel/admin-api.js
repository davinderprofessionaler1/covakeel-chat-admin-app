import { ApiError, BASE } from './api.js';

const TOKEN_KEY = 'cv-admin-token';

export const adminToken = () => localStorage.getItem(TOKEN_KEY);

export async function adminApi(path, { method = 'GET', body, signal } = {}) {
  const headers = {};
  const token = adminToken();
  if (token) headers.Authorization = `Bearer ${token}`;
  if (body !== undefined) headers['Content-Type'] = 'application/json';
  let response;
  try {
    response = await fetch(BASE + path, {
      method, headers, signal,
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch (error) {
    if (error.name === 'AbortError') throw error;
    throw new ApiError('Could not connect. Please try again.', 0);
  }
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    if (response.status === 401) localStorage.removeItem(TOKEN_KEY);
    throw new ApiError(data.detail || `Request failed (${response.status})`, response.status);
  }
  return response.status === 204 ? null : response.json();
}

export async function adminLogin(email, password) {
  const response = await fetch(BASE + '/auth/admin/login', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username: email.trim(), password }),
  }).catch(() => { throw new ApiError('Could not connect. Please try again.', 0); });
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new ApiError(data.detail || `Request failed (${response.status})`, response.status);
  }
  localStorage.setItem(TOKEN_KEY, (await response.json()).access_token);
}

export function adminSignout() {
  localStorage.removeItem(TOKEN_KEY);
  location.assign('/admin/login/');
}
