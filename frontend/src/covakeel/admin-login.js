import './admin.css';
import './admin-login.css';
import { adminApi, adminLogin, adminToken } from './admin-api.js';

const next = new URLSearchParams(location.search).get('next');
const destination = next?.startsWith('/admin/') && !next.startsWith('/admin/login/') ? next : '/admin/';
if (new URLSearchParams(location.search).has('signed_out')) {
  localStorage.removeItem('cv-admin-token');
} else if (adminToken()) {
  adminApi('/admin/settings').then(() => location.replace(destination)).catch(() => {
    localStorage.removeItem('cv-admin-token');
  });
}

const form = document.querySelector('#admin-login-form');
const errorNode = document.querySelector('#login-error');
const button = document.querySelector('#login-button');

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  errorNode.hidden = true;
  const email = form.elements.email;
  const password = form.elements.password;
  if (!email.value.trim() || !email.checkValidity()) {
    errorNode.textContent = email.value.trim() ? 'Enter a valid admin email address.' : 'Enter your admin email address.';
    errorNode.hidden = false;
    email.focus();
    return;
  }
  if (!password.value) {
    errorNode.textContent = 'Enter your admin password.';
    errorNode.hidden = false;
    password.focus();
    return;
  }
  button.disabled = true;
  button.textContent = 'Signing in…';
  try {
    await adminLogin(form.elements.email.value, form.elements.password.value);
    location.assign(destination);
  } catch (error) {
    errorNode.textContent = error.status === 401 ? 'Email or password is incorrect.'
      : error.status === 403 ? 'This account does not have admin access.' : error.message;
    errorNode.hidden = false;
  } finally {
    button.disabled = false;
    button.textContent = 'Sign in to admin ↗';
  }
});
