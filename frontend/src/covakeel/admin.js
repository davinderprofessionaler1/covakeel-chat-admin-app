import './admin.css';
import { BASE } from './api.js';
import { adminApi as api, adminToken, adminSignout as signout } from './admin-api.js';

const $ = (selector) => document.querySelector(selector);
const esc = (value) => String(value ?? '').replace(/[&<>"']/g, (character) => ({
  '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
})[character]);
const date = (value) => value ? new Date(value).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' }) : '—';
const count = (value) => Number(value || 0).toLocaleString('en-IN');
const titles = {
  overview: ['Overview', 'A clear view of your legal knowledge workspace.'],
  legal: ['Legal Knowledge Management', 'Add a PDF to the chatbot or replace an earlier version.'],
  knowledge: ['Knowledge base', 'Documents currently available to the chatbot.'],
  users: ['Users', 'Accounts using CoVakeel.'],
  conversations: ['Conversations', 'Chat activity by account. Message contents remain private.'],
  health: ['System health', 'Current database and AI service status.'],
  settings: ['Settings', 'Your admin account and knowledge-base configuration.'],
};
const state = { section: 'overview', documents: [], search: '', poll: null, selectedFile: null };

function notice(message, error = false) {
  const node = $('#notice');
  node.textContent = message;
  node.classList.toggle('error', error);
  node.hidden = !message;
}

function metric(label, value, sub = '') {
  return `<div class="metric"><span class="label">${esc(label)}</span><strong class="value">${esc(value)}</strong><span class="sub">${esc(sub)}</span></div>`;
}

function badge(status) {
  return `<span class="badge ${esc(status)}">${esc({ indexed: 'Ready', processing: 'Processing', failed: 'Needs attention', admin: 'Admin', member: 'Member' }[status] || status)}</span>`;
}

function documentRows(documents, actions = false) {
  if (!documents.length) return '<div class="empty"><strong>No documents yet</strong>Upload a text-based PDF to build the knowledge base.</div>';
  return `<div class="table-wrap"><table><thead><tr><th>Document</th><th>Status</th><th>Pages</th><th>Chunks</th><th>Added</th>${actions ? '<th>Action</th>' : ''}</tr></thead><tbody>${documents.map((doc) => {
    const sourceUrl = /^https:\/\//i.test(doc.sourceUrl || '') ? esc(doc.sourceUrl) : '';
    const title = esc(doc.title || doc.filename);
    return `<tr>
    <td class="name">${sourceUrl ? `<a class="document-link" href="${sourceUrl}" target="_blank" rel="noopener noreferrer" aria-label="Open PDF: ${title}">${title}</a>` : title}<div class="secondary">${esc(doc.filename)}</div>${sourceUrl ? `<div class="secondary"><a href="${sourceUrl}" target="_blank" rel="noopener noreferrer">Official source ↗</a></div>` : ''}${doc.error ? `<div class="secondary">${esc(doc.error)}</div>` : ''}</td>
    <td>${badge(doc.status)}</td><td>${count(doc.pages)}</td><td>${count(doc.chunks)}</td><td>${date(doc.createdAt)}</td>
    ${actions ? `<td><button class="btn danger small" type="button" data-remove="${esc(doc.id)}" ${doc.status === 'processing' ? 'disabled' : ''}>Remove</button></td>` : ''}
  </tr>`; }).join('')}</tbody></table></div>`;
}

function renderOverview(summary, documents) {
  const recent = documents.filter((doc) => doc.status === 'indexed').slice(0, 5);
  $('#section-content').innerHTML = `
    <div class="grid">${metric('Legal documents', count(summary.documents), 'Available to the chatbot')}${metric('Knowledge chunks', count(summary.indexedChunks), 'Searchable passages')}${metric('Users', count(summary.users), 'Registered accounts')}${metric('Conversations', count(summary.conversations), 'Across all accounts')}</div>
    <div class="section-head"><div><h2>Workspace activity</h2><p>Keep the legal library current from one place.</p></div><a class="btn" href="#legal">Add document ↗</a></div>
    <div class="split"><div class="card"><h2>Recent documents</h2>${recent.length ? `<ul class="quick-list">${recent.map((doc) => `<li><span>${esc(doc.title || doc.filename)}</span><small>${date(doc.createdAt)}</small></li>`).join('')}</ul>` : '<p>No indexed documents yet.</p>'}</div>
    <div class="stack"><div class="card"><h2>AI research</h2><p><span class="status-dot ${summary.rag.configured ? '' : 'warn'}"></span>${summary.rag.configured ? 'Configured and ready for questions' : 'Needs configuration'}</p></div><div class="card"><h2>Processing queue</h2><p>${count(summary.processing)} document${summary.processing === 1 ? '' : 's'} processing</p></div></div></div>`;
}

function renderLegal(documents) {
  $('#section-content').innerHTML = `
    <div id="drop-zone" class="upload-zone"><div><p class="eyebrow">ADD TO KNOWLEDGE</p><h2>Upload a legal PDF</h2><p>Text-based PDFs up to 20 MB. Uploading the same filename replaces the version used for future answers.</p></div><div class="upload-actions"><input id="pdf-file" type="file" accept=".pdf,application/pdf" hidden><button id="choose-pdf" class="btn" type="button">Choose PDF ↗</button></div></div>
    <form id="upload-form" class="upload-form"><div id="selected-pdf" class="secondary">No PDF selected</div><label>Document title<input id="pdf-title" name="title" maxlength="180" placeholder="e.g. Finance Act, 2023" required></label><label>Official source URL <span class="secondary">(optional)</span><input id="pdf-source" name="source" type="url" maxlength="500" placeholder="https://..."></label><button id="upload-pdf" class="btn" type="submit" disabled>Upload to knowledge base</button></form>
    <p class="hint">Scanned image PDFs need OCR first. Existing chat answers are not rewritten; new questions use the updated index.</p>
    <div class="section-head"><div><h2>Document library</h2><p>Review processing and remove documents you no longer want in answers.</p></div><button class="btn ghost small" id="refresh-docs" type="button">Refresh</button></div>
    ${documentRows(documents, true)}`;
  $('#choose-pdf').onclick = () => $('#pdf-file').click();
  $('#pdf-file').onchange = (event) => selectFile(event.target.files?.[0]);
  $('#upload-form').onsubmit = (event) => { event.preventDefault(); upload(state.selectedFile); };
  $('#refresh-docs').onclick = () => navigate('legal');
  const zone = $('#drop-zone');
  zone.ondragover = (event) => { event.preventDefault(); zone.classList.add('drag'); };
  zone.ondragleave = () => zone.classList.remove('drag');
  zone.ondrop = (event) => { event.preventDefault(); zone.classList.remove('drag'); selectFile(event.dataTransfer.files?.[0]); };
  document.querySelectorAll('[data-remove]').forEach((button) => {
    button.onclick = () => removeDocument(button.dataset.remove, documents.find((doc) => doc.id === button.dataset.remove)?.filename);
  });
}

function renderKnowledge(documents) {
  const active = documents.filter((doc) => doc.status === 'indexed');
  $('#section-content').innerHTML = `<div class="grid">${metric('Indexed documents', count(active.length), 'Ready for retrieval')}${metric('Searchable chunks', count(active.reduce((sum, doc) => sum + doc.chunks, 0)), 'From current documents')}${metric('New uploads', count(active.filter((doc) => doc.origin === 'upload').length), 'Added by admins')}${metric('Starter sources', count(active.filter((doc) => doc.origin === 'starter').length), 'Original indexed PDFs')}</div>
    <div class="section-head"><div><h2>Indexed sources</h2><p>Only these documents can be retrieved for new answers.</p></div><a class="btn ghost small" href="#legal">Manage documents</a></div>${documentRows(active)}`;
}

function table(headers, rows, empty) {
  if (!rows.length) return `<div class="empty"><strong>${esc(empty)}</strong>Nothing to display yet.</div>`;
  return `<div class="table-wrap"><table><thead><tr>${headers.map((item) => `<th>${esc(item)}</th>`).join('')}</tr></thead><tbody>${rows.join('')}</tbody></table></div>`;
}

function renderUsers(users) {
  $('#section-content').innerHTML = `<div class="grid">${metric('Registered users', count(users.length), 'Most recent 200 accounts')}${metric('Administrators', count(users.filter((user) => user.isAdmin).length), 'Server-assigned role')}</div><div class="section-head"><div><h2>Accounts</h2><p>View account details without changing user data.</p></div></div>${table(['Name', 'Email / username', 'Role', 'Joined'], users.map((user) => `<tr><td class="name">${esc(user.name || user.username)}</td><td>${esc(user.email || user.username)}</td><td>${badge(user.isAdmin ? 'admin' : 'member')}</td><td>${date(user.createdAt)}</td></tr>`), 'No users found')}`;
}

function renderConversations(conversations) {
  $('#section-content').innerHTML = `<div class="section-head"><div><h2>Conversation activity</h2><p>Titles and owners only; private message text is not shown here.</p></div></div>${table(['Title', 'Account', 'Created', 'Last updated'], conversations.map((item) => `<tr><td class="name">${esc(item.title)}</td><td>${esc(item.owner)}</td><td>${date(item.createdAt)}</td><td>${date(item.updatedAt)}</td></tr>`), 'No conversations found')}`;
}

function renderHealth(health) {
  const ragLabel = health.rag.configured ? 'Configured' : 'Needs attention';
  $('#section-content').innerHTML = `<div class="grid">${metric('Database', health.database, 'MongoDB connection')}${metric('AI & retrieval', ragLabel, health.rag.initialized ? 'Model loaded' : 'Loads on first question')}${metric('Indexed documents', count(health.indexedDocuments), 'Ready for new questions')}${metric('Free disk', health.freeDiskGb + ' GB', 'Local storage available')}</div>
    <div class="section-head"><h2>Service details</h2><button class="btn ghost small" id="refresh-health" type="button">Refresh</button></div><div class="card"><dl class="details"><dt>Document queue</dt><dd>${count(health.processingDocuments)} processing</dd><dt>Failed uploads</dt><dd>${count(health.failedDocuments)}</dd><dt>Searchable chunks</dt><dd>${count(health.indexedChunks)}</dd><dt>RAG configuration</dt><dd>${esc(health.rag.missing.length ? health.rag.missing.join('; ') : 'All required configuration is present')}</dd></dl></div>`;
  $('#refresh-health').onclick = () => navigate('health');
}

function renderSettings(settings) {
  $('#section-content').innerHTML = `<div class="split"><div class="card"><h2>Knowledge settings</h2><dl class="details"><dt>Admin email</dt><dd>${esc(settings.adminEmail || 'Not set')}</dd><dt>Gemini model</dt><dd>${esc(settings.model)}</dd><dt>Vector collection</dt><dd>${esc(settings.collection)}</dd><dt>PDF limit</dt><dd>${count(settings.maxPdfMb)} MB per document</dd></dl></div><div class="card"><h2>Account & appearance</h2><p>Use your CoVakeel account to access this workspace. Admin permissions are assigned on the server.</p><div class="settings-actions"><button class="btn ghost" id="theme-toggle" type="button">Toggle theme</button><button class="btn ghost" id="admin-signout" type="button">Sign out</button></div></div></div>`;
  $('#theme-toggle').onclick = () => { const next = document.documentElement.dataset.theme === 'light' ? 'dark' : 'light'; document.documentElement.dataset.theme = next; localStorage.setItem('cv-theme', next); };
  $('#admin-signout').onclick = signout;
}

function selectFile(file) {
  if (!file) return;
  if (!file.name.toLowerCase().endsWith('.pdf') || file.size > 20 * 1024 * 1024) { notice('Choose a PDF up to 20 MB.', true); return; }
  state.selectedFile = file;
  $('#selected-pdf').textContent = file.name;
  $('#pdf-title').value = file.name.replace(/\.pdf$/i, '').replace(/[_-]+/g, ' ');
  $('#upload-pdf').disabled = false;
  notice('');
}

async function upload(file) {
  if (!file) return;
  if (!file.name.toLowerCase().endsWith('.pdf') || file.size > 20 * 1024 * 1024) { notice('Choose a PDF up to 20 MB.', true); return; }
  const title = $('#pdf-title').value.trim();
  const source = $('#pdf-source').value.trim();
  if (!title) { notice('Enter a document title.', true); return; }
  if (source && !source.startsWith('https://')) { notice('Official source URL must start with https://', true); return; }
  const button = $('#upload-pdf'); if (button) { button.disabled = true; button.textContent = 'Uploading…'; }
  try {
    const params = new URLSearchParams({ filename: file.name, title });
    if (source) params.set('source_url', source);
    const response = await fetch(BASE + '/admin/documents?' + params, {
      method: 'POST', headers: { Authorization: 'Bearer ' + adminToken(), 'Content-Type': 'application/pdf' }, body: file,
    });
    const result = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(result.detail || `Upload failed (${response.status})`);
    await navigate('legal');
    notice(`${title} uploaded. Indexing is running; the status will update automatically.`);
  } catch (error) { notice(error.message, true); }
  finally { if (button?.isConnected) { button.disabled = false; button.textContent = 'Upload to knowledge base'; } }
}

async function removeDocument(id, filename) {
  if (!confirm(`Remove “${filename}” from future chatbot answers?`)) return;
  try { await api('/admin/documents/' + encodeURIComponent(id), { method: 'DELETE' }); await navigate('legal'); notice(`${filename} removed from the knowledge base.`); }
  catch (error) { notice(error.message, true); }
}

async function navigate(section) {
  section = titles[section] ? section : 'overview';
  state.section = section;
  if (location.hash !== '#' + section) history.replaceState(null, '', '#' + section);
  document.querySelectorAll('.nav a').forEach((link) => { const active = link.dataset.section === section; link.classList.toggle('active', active); link.setAttribute('aria-current', active ? 'page' : 'false'); });
  $('.sidebar').classList.remove('open');
  $('#section-title').textContent = titles[section][0];
  $('#section-intro').textContent = titles[section][1];
  $('#section-content').innerHTML = '<div class="loading">Loading…</div>';
  notice('');
  try {
    if (section === 'overview') {
      const [summary, documents] = await Promise.all([api('/admin/overview'), api('/admin/documents')]);
      renderOverview(summary, documents);
    } else if (section === 'legal' || section === 'knowledge') {
      const documents = await api('/admin/documents');
      state.documents = documents;
      if (section === 'legal') renderLegal(documents); else renderKnowledge(documents);
    } else if (section === 'users') renderUsers(await api('/admin/users?limit=200'));
    else if (section === 'conversations') renderConversations(await api('/admin/conversations?limit=200'));
    else if (section === 'health') renderHealth(await api('/admin/health'));
    else renderSettings(await api('/admin/settings'));
  } catch (error) { $('#section-content').innerHTML = `<div class="empty"><strong>Could not load this section</strong>${esc(error.message)}</div>`; }
  clearInterval(state.poll);
  if (section === 'legal' && state.documents.some((doc) => doc.status === 'processing')) {
    state.poll = setInterval(() => navigate('legal'), 4000);
  }
}

async function start() {
  const loginUrl = '/admin/login/?next=' + encodeURIComponent(location.pathname + location.hash);
  if (!adminToken()) { location.replace(loginUrl); return; }
  try {
    const settings = await api('/admin/settings');
    $('#admin-email').textContent = settings.adminEmail || 'Admin account';
    window.addEventListener('hashchange', () => navigate(location.hash.slice(1)));
    $('#menu-toggle').onclick = () => $('.sidebar').classList.toggle('open');
    $('#sidebar-signout').onclick = signout;
    navigate(location.hash.slice(1) || 'overview');
  } catch {
    localStorage.removeItem('cv-admin-token');
    location.replace(loginUrl);
  }
}
window.addEventListener('pageshow', () => {
  if (!adminToken()) location.replace('/admin/login/');
});
start();
