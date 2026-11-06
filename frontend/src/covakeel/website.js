import './auth.js';
import './integration.css';
import { api } from './api.js';

const legacy = location.pathname;
if (legacy.startsWith('/chat/')) location.replace('/app/#' + (legacy.endsWith('/new') ? 'new' : 'chat/' + encodeURIComponent(legacy.split('/').pop())));
if (legacy === '/profile') location.replace('/app/#profile');
if (legacy === '/login' || legacy === '/register') {
  const scope = document.querySelector('#hero .ascope');
  if (legacy === '/login') scope.classList.add('signin');
  window.cvAuth(scope).show('email');
  const input = scope.querySelector('[name="email"]');
  if (legacy === '/login') { input.type = 'text'; input.placeholder = 'Email or username'; }
}
if (localStorage.getItem('token') && !location.hash) {
  api('/users/me').then(() => location.replace('/app/#new')).catch(() => {});
}
// These policy destinations were not supplied in the handoff. Keep the links
// usable without inventing legal terms, billing details, or contact information.
document.addEventListener('click', event => {
  const link = event.target.closest('a[href^="#"]');
  if (!link) return;
  const hash = link.getAttribute('href');
  if (['#google', '#email', '#phone', '#signup'].includes(hash) || document.getElementById(hash.slice(1))) return;
  event.preventDefault();
  const dialog = document.createElement('dialog');
  dialog.className = 'cv-notice';
  const heading = document.createElement('h2'); heading.textContent = link.textContent.trim();
  const text = document.createElement('p'); text.textContent = 'This page is being prepared. No payments are collected in this local preview.';
  const button = document.createElement('button'); button.className = 'btn btn-gold'; button.textContent = 'Close'; button.onclick = () => dialog.close();
  dialog.append(heading, text, button); document.body.append(dialog); dialog.showModal();
  dialog.addEventListener('close', () => dialog.remove(), { once: true });
  dialog.addEventListener('click', e => { if (e.target === dialog) dialog.close(); });
});
