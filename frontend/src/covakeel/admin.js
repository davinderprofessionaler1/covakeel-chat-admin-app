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
const PAGE_SIZE = { legal: 10, knowledge: 10 };
const state = {
  section: 'overview', documents: [], poll: null, selectedFile: null, pendingRemoval: null, removing: false,
  legalChanges: [], pendingChangeRemoval: null, removingChange: false,
  documentViews: {
    legal: { search: '', filter: 'all', page: 1 },
    knowledge: { search: '', filter: 'all', page: 1 },
  },
};

function notice(message, error = false) {
  const node = $('#notice');
  node.textContent = message;
  node.classList.toggle('error', error);
  node.hidden = !message;
}

function showFormError(form) {
  const field = [...form.elements].find((element) => element.willValidate && !element.checkValidity());
  if (!field) return false;
  const label = field.closest('label')?.textContent?.trim() || 'this field';
  const message = field.type === 'checkbox'
    ? 'Check the official sources and tick the verification box before publishing.'
    : field.validity.valueMissing ? `Enter ${label.toLowerCase()}.`
      : field.validity.tooShort ? `${label} must be at least ${field.minLength} characters.`
        : `Enter a valid ${field.type === 'url' ? 'URL' : 'value'} for ${label.toLowerCase()}.`;
  notice(message, true);
  field.focus();
  return true;
}

function metric(label, value, sub = '') {
  return `<div class="metric"><span class="label">${esc(label)}</span><strong class="value">${esc(value)}</strong><span class="sub">${esc(sub)}</span></div>`;
}

function badge(status) {
  return `<span class="badge ${esc(status)}">${esc({ indexed: 'Ready', processing: 'Processing', failed: 'Needs attention', admin: 'Admin', member: 'Member' }[status] || status)}</span>`;
}

function documentRows(documents, actions = false) {
  if (!documents.length) return '<div class="empty"><strong>No matching PDFs</strong>Try a different search or filter.</div>';
  return `<div class="table-wrap"><table><thead><tr><th>Document</th><th>Status</th><th>Pages</th><th>Chunks</th><th>Added</th>${actions ? '<th>Action</th>' : ''}</tr></thead><tbody>${documents.map((doc) => {
    const sourceUrl = /^https:\/\//i.test(doc.sourceUrl || '') ? esc(doc.sourceUrl) : '';
    const title = esc(doc.title || doc.filename);
    return `<tr>
    <td class="name">${sourceUrl ? `<a class="document-link" href="${sourceUrl}" target="_blank" rel="noopener noreferrer" aria-label="Open PDF: ${title}">${title}</a>` : title}<div class="secondary">${esc(doc.filename)}</div>${sourceUrl ? `<div class="secondary"><a href="${sourceUrl}" target="_blank" rel="noopener noreferrer">Official source ↗</a></div>` : ''}${doc.error ? `<div class="secondary">${esc(doc.error)}</div>` : ''}</td>
    <td>${badge(doc.status)}</td><td>${count(doc.pages)}</td><td>${count(doc.chunks)}</td><td>${date(doc.createdAt)}</td>
    ${actions ? `<td><button class="btn danger small" type="button" data-remove="${esc(doc.id)}" ${doc.status === 'processing' ? 'disabled' : ''}>Remove</button></td>` : ''}
  </tr>`; }).join('')}</tbody></table></div>`;
}

function documentBrowser(section) {
  const view = state.documentViews[section];
  const filterOptions = section === 'legal'
    ? [['all', 'All statuses'], ['indexed', 'Ready'], ['processing', 'Processing'], ['failed', 'Needs attention']]
    : [['all', 'All sources'], ['upload', 'Admin uploads'], ['starter', 'Starter sources']];
  return `<div class="document-browser">
    <div class="document-toolbar"><label class="document-search">Search PDFs<input id="document-search" type="search" placeholder="Title, filename or source URL" value="${esc(view.search)}" autocomplete="off"></label>
    <label class="document-filter">Filter<select id="document-filter">${filterOptions.map(([value, label]) => `<option value="${value}" ${view.filter === value ? 'selected' : ''}>${label}</option>`).join('')}</select></label></div>
    <div id="document-results"></div>
  </div>`;
}

function filteredDocuments(section) {
  const view = state.documentViews[section];
  const query = view.search.trim().toLocaleLowerCase();
  return state.documents.filter((doc) => {
    if (section === 'knowledge' && doc.status !== 'indexed') return false;
    if (view.filter !== 'all' && (section === 'legal' ? doc.status : doc.origin) !== view.filter) return false;
    return !query || [doc.title, doc.filename, doc.sourceUrl].some((value) => String(value || '').toLocaleLowerCase().includes(query));
  });
}

function pageButtons(page, totalPages) {
  if (totalPages <= 1) return '';
  const pages = new Set([1, totalPages]);
  for (let number = Math.max(1, page - 2); number <= Math.min(totalPages, page + 2); number += 1) pages.add(number);
  let previous = 0;
  const numbers = [...pages].sort((a, b) => a - b).map((number) => {
    const gap = number > previous + 1 ? '<span class="page-gap" aria-hidden="true">…</span>' : '';
    previous = number;
    return `${gap}<button type="button" data-page="${number}" class="page-button ${number === page ? 'current' : ''}" ${number === page ? 'aria-current="page"' : ''} aria-label="Page ${number}">${number}</button>`;
  }).join('');
  return `<nav class="document-pages" aria-label="Document pages"><button type="button" data-page="${page - 1}" class="page-button" ${page === 1 ? 'disabled' : ''}>Previous</button>${numbers}<button type="button" data-page="${page + 1}" class="page-button" ${page === totalPages ? 'disabled' : ''}>Next</button></nav>`;
}

function renderDocumentResults(section) {
  const results = $('#document-results');
  if (!results) return;
  const view = state.documentViews[section];
  const pageSize = PAGE_SIZE[section];
  const all = section === 'legal' ? state.documents : state.documents.filter((doc) => doc.status === 'indexed');
  const matching = filteredDocuments(section);
  const totalPages = Math.max(1, Math.ceil(matching.length / pageSize));
  view.page = Math.min(Math.max(1, view.page), totalPages);
  const start = (view.page - 1) * pageSize;
  const end = Math.min(start + pageSize, matching.length);
  results.innerHTML = `<div class="document-count" role="status">${count(all.length)} total PDF${all.length === 1 ? '' : 's'} · ${count(matching.length)} matching · ${matching.length ? `Showing ${count(start + 1)}–${count(end)}` : 'Showing 0'}</div>
    ${all.length ? documentRows(matching.slice(start, end), section === 'legal') : '<div class="empty"><strong>No PDFs yet</strong>Add a PDF to make it searchable.</div>'}
    ${pageButtons(view.page, totalPages)}`;
  results.querySelectorAll('[data-page]').forEach((button) => {
    button.onclick = () => { view.page = Number(button.dataset.page); renderDocumentResults(section); };
  });
  results.querySelectorAll('[data-remove]').forEach((button) => {
    button.onclick = () => showRemoveDialog(state.documents.find((doc) => doc.id === button.dataset.remove));
  });
}

function bindDocumentBrowser(section) {
  $('#document-search').oninput = (event) => {
    state.documentViews[section].search = event.target.value;
    state.documentViews[section].page = 1;
    renderDocumentResults(section);
  };
  $('#document-filter').onchange = (event) => {
    state.documentViews[section].filter = event.target.value;
    state.documentViews[section].page = 1;
    renderDocumentResults(section);
  };
  renderDocumentResults(section);
}

function renderOverview(summary, documents) {
  const recent = documents.filter((doc) => doc.status === 'indexed').slice(0, 5);
  $('#section-content').innerHTML = `
    <div class="grid">${metric('Legal documents', count(summary.documents), 'Available to the chatbot')}${metric('Knowledge chunks', count(summary.indexedChunks), 'Searchable passages')}${metric('Users', count(summary.users), 'Registered accounts')}${metric('Conversations', count(summary.conversations), 'Across all accounts')}</div>
    <div class="section-head"><div><h2>Workspace activity</h2><p>Keep the legal library current from one place.</p></div><a class="btn" href="#legal">Add document ↗</a></div>
    <div class="split"><div class="card"><h2>Recent documents</h2>${recent.length ? `<ul class="quick-list">${recent.map((doc) => `<li><span>${esc(doc.title || doc.filename)}</span><small>${date(doc.createdAt)}</small></li>`).join('')}</ul>` : '<p>No indexed documents yet.</p>'}</div>
    <div class="stack"><div class="card"><h2>AI research</h2><p><span class="status-dot ${summary.rag.configured ? '' : 'warn'}"></span>${summary.rag.configured ? 'Configured and ready for questions' : 'Needs configuration'}</p></div><div class="card"><h2>Processing queue</h2><p>${count(summary.processing)} document${summary.processing === 1 ? '' : 's'} processing</p></div></div></div>`;
}

function documentSummary(section) {
  const documents = state.documents;
  const active = documents.filter((doc) => doc.status === 'indexed');
  if (section === 'legal') return `${metric('Total PDFs', count(documents.length), 'In the document library')}${metric('Ready', count(active.length), 'Available to the chatbot')}${metric('Processing', count(documents.filter((doc) => doc.status === 'processing').length), 'Indexing now')}${metric('Needs attention', count(documents.filter((doc) => doc.status === 'failed').length), 'Review or reupload')}`;
  return `${metric('Indexed documents', count(active.length), 'Ready for retrieval')}${metric('Searchable chunks', count(active.reduce((sum, doc) => sum + doc.chunks, 0)), 'From current documents')}${metric('New uploads', count(active.filter((doc) => doc.origin === 'upload').length), 'Added by admins')}${metric('Starter sources', count(active.filter((doc) => doc.origin === 'starter').length), 'Original indexed PDFs')}`;
}

function renderLegal() {
  state.selectedFile = null;
  $('#section-content').innerHTML = `
    <div id="document-summary" class="grid">${documentSummary('legal')}</div>
    <div id="drop-zone" class="upload-zone"><div><p class="eyebrow">ADD TO KNOWLEDGE</p><h2>Add a legal PDF</h2><p>Choose a text-based PDF up to 20 MB, paste a direct HTTPS PDF link, or use a CBIC notification or circular viewer link. The same filename replaces the version used for future answers.</p></div><div class="upload-actions"><input id="pdf-file" type="file" accept=".pdf,application/pdf" hidden><button id="choose-pdf" class="btn" type="button">Choose PDF ↗</button></div></div>
    <form id="upload-form" class="upload-form" novalidate><div id="selected-pdf" class="secondary">Choose a PDF or paste its link.</div><label>Document title<input id="pdf-title" name="title" maxlength="180" placeholder="e.g. Finance Act, 2023" required></label><label>PDF URL <span class="secondary">(or source for a chosen file)</span><input id="pdf-source" name="source" type="url" maxlength="500" placeholder="https://example.gov.in/document.pdf"></label><button id="upload-pdf" class="btn" type="submit" disabled>Add to knowledge base</button></form>
    <p class="hint">Scanned image PDFs need OCR first. Existing chat answers are not rewritten; new questions use the updated index.</p>
    <div class="section-head"><div><h2>Reviewed law changes</h2><p>Link an older rule to a later version and its commencement evidence. The chatbot uses these records for dated comparisons.</p></div></div>
    <details class="card change-editor"><summary>Add a reviewed change</summary>
      <p class="secondary">Check the official Act, amendment and commencement notification before publishing. A document year alone does not establish when a change took effect.</p>
      <form id="change-form" class="change-form" novalidate>
        <label>Law keyword<input name="law_keyword" placeholder="e.g. CGST" maxlength="100" required></label>
        <label>Provision<input name="provision" placeholder="e.g. Section 16(4)" maxlength="100" required></label>
        <label class="wide">Earlier position<textarea name="before_text" rows="3" minlength="10" maxlength="2000" required></textarea></label>
        <label class="wide">Later position<textarea name="after_text" rows="3" minlength="10" maxlength="2000" required></textarea></label>
        <label>Earlier version valid from<input name="before_from" type="date" required></label>
        <label>Change effective from<input name="effective_from" type="date" required></label>
        <label>Verified through<input name="verified_through" type="date" required></label>
        <label>Earlier official source URL<input name="before_source_url" type="url" placeholder="https://...gov.in/..." maxlength="500" required></label>
        <label>Later official source URL<input name="after_source_url" type="url" placeholder="https://...gov.in/..." maxlength="500" required></label>
        <label>Commencement official source URL<input name="commencement_source_url" type="url" placeholder="https://...gov.in/..." maxlength="500" required></label>
        <label class="change-confirm wide"><input name="confirmed" type="checkbox" required>I checked both positions and the effective date against the linked official sources.</label>
        <button class="btn" type="submit">Publish reviewed change</button>
      </form>
    </details>
    <div id="change-list"></div>
    <div class="section-head"><div><h2>Document library</h2><p>Review processing and remove documents you no longer want in answers.</p></div><button class="btn ghost small" id="refresh-docs" type="button">Refresh</button></div>
    ${documentBrowser('legal')}`;
  $('#choose-pdf').onclick = () => $('#pdf-file').click();
  $('#pdf-file').onchange = (event) => selectFile(event.target.files?.[0]);
  $('#pdf-source').oninput = updateUploadChoice;
  $('#upload-form').onsubmit = (event) => { event.preventDefault(); upload(state.selectedFile); };
  $('#change-form').onsubmit = publishChange;
  $('#refresh-docs').onclick = refreshDocumentData;
  const zone = $('#drop-zone');
  zone.ondragover = (event) => { event.preventDefault(); zone.classList.add('drag'); };
  zone.ondragleave = () => zone.classList.remove('drag');
  zone.ondrop = (event) => { event.preventDefault(); zone.classList.remove('drag'); selectFile(event.dataTransfer.files?.[0]); };
  bindDocumentBrowser('legal');
  renderChangeList();
}

function renderChangeList() {
  const node = $('#change-list');
  if (!node) return;
  node.innerHTML = state.legalChanges.length ? `<div class="change-list">${state.legalChanges.map((item) => `<article class="card change-card">
    <div class="change-card-head"><div><h3>${esc(item.law_keyword)} · ${esc(item.provision)}</h3><span class="secondary">Effective ${esc(item.effective_from)} · Verified through ${esc(item.verified_through)}</span></div><button class="btn danger small" type="button" data-remove-change="${esc(item.id)}">Remove</button></div>
    <div class="change-positions"><p><strong>Before:</strong> ${esc(item.before_text)}</p><p><strong>Later:</strong> ${esc(item.after_text)}</p></div>
    <div class="change-sources"><a href="${esc(item.before_source_url)}" target="_blank" rel="noopener noreferrer">Earlier source ↗</a><a href="${esc(item.after_source_url)}" target="_blank" rel="noopener noreferrer">Later source ↗</a><a href="${esc(item.commencement_source_url)}" target="_blank" rel="noopener noreferrer">Effective date ↗</a></div>
  </article>`).join('')}</div>`
    : '<div class="empty"><strong>No reviewed changes yet</strong>Current-versus-earlier answers stay unverified until an admin publishes a checked record.</div>';
  node.querySelectorAll('[data-remove-change]').forEach((button) => {
    button.onclick = () => showRemoveChangeDialog(state.legalChanges.find((item) => item.id === button.dataset.removeChange));
  });
}

function showRemoveChangeDialog(item) {
  if (!item) return;
  state.pendingChangeRemoval = item;
  $('#remove-change-name').textContent = `${item.law_keyword} · ${item.provision}`;
  $('#remove-change-error').hidden = true;
  $('#remove-change-dialog').showModal();
  $('#remove-change-cancel').focus();
}

async function confirmRemoveChange() {
  const item = state.pendingChangeRemoval;
  if (!item || state.removingChange) return;
  state.removingChange = true;
  const confirmButton = $('#remove-change-confirm');
  const cancelButton = $('#remove-change-cancel');
  confirmButton.disabled = true;
  cancelButton.disabled = true;
  confirmButton.textContent = 'Removing…';
  try {
    await api('/admin/legal-changes/' + encodeURIComponent(item.id), { method: 'DELETE' });
    $('#remove-change-dialog').close();
    state.legalChanges = state.legalChanges.filter((change) => change.id !== item.id);
    renderChangeList();
    notice('Reviewed change removed.');
  } catch (error) {
    $('#remove-change-error').textContent = error.message;
    $('#remove-change-error').hidden = false;
  } finally {
    state.removingChange = false;
    confirmButton.disabled = false;
    cancelButton.disabled = false;
    confirmButton.textContent = 'Remove change';
  }
}

async function publishChange(event) {
  event.preventDefault();
  const form = event.currentTarget;
  if (showFormError(form)) return;
  const button = form.querySelector('button[type="submit"]');
  const payload = Object.fromEntries(new FormData(form));
  delete payload.confirmed;
  button.disabled = true;
  try {
    const item = await api('/admin/legal-changes', { method: 'POST', body: payload });
    state.legalChanges.unshift(item);
    form.reset(); renderChangeList(); notice('Reviewed change published for new chatbot answers.');
  } catch (error) { notice(error.message, true); }
  finally { button.disabled = false; }
}

function renderKnowledge() {
  $('#section-content').innerHTML = `<div id="document-summary" class="grid">${documentSummary('knowledge')}</div>
    <div class="section-head"><div><h2>Indexed sources</h2><p>Only these documents can be retrieved for new answers.</p></div><a class="btn ghost small" href="#legal">Manage documents</a></div>${documentBrowser('knowledge')}`;
  bindDocumentBrowser('knowledge');
}

async function refreshDocumentData() {
  try {
    state.documents = await api('/admin/documents');
    if (state.section !== 'legal' && state.section !== 'knowledge') return;
    $('#document-summary').innerHTML = documentSummary(state.section);
    renderDocumentResults(state.section);
    notice('');
    if (!state.documents.some((doc) => doc.status === 'processing')) {
      clearInterval(state.poll);
      state.poll = null;
    }
  } catch (error) { notice(error.message, true); }
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
  $('#section-content').innerHTML = `<div class="split"><div class="card"><h2>Knowledge settings</h2><dl class="details"><dt>Admin email</dt><dd>${esc(settings.adminEmail || 'Not set')}</dd><dt>Claude model</dt><dd>${esc(settings.model)}</dd><dt>Vector collection</dt><dd>${esc(settings.collection)}</dd><dt>PDF limit</dt><dd>${count(settings.maxPdfMb)} MB per document</dd></dl></div><div class="card"><h2>Account & appearance</h2><p>Use your CoVakeel account to access this workspace. Admin permissions are assigned on the server.</p><div class="settings-actions"><button class="btn ghost" id="theme-toggle" type="button">Toggle theme</button><button class="btn ghost" id="admin-signout" type="button">Sign out</button></div></div></div>`;
  $('#theme-toggle').onclick = () => { const next = document.documentElement.dataset.theme === 'light' ? 'dark' : 'light'; document.documentElement.dataset.theme = next; localStorage.setItem('cv-theme', next); };
  $('#admin-signout').onclick = signout;
}

function selectFile(file) {
  if (!file) return;
  if (!file.name.toLowerCase().endsWith('.pdf') || file.size > 20 * 1024 * 1024) { notice('Choose a PDF up to 20 MB.', true); return; }
  state.selectedFile = file;
  $('#selected-pdf').textContent = file.name;
  $('#pdf-title').value = file.name.replace(/\.pdf$/i, '').replace(/[_-]+/g, ' ');
  updateUploadChoice();
  notice('');
}

function updateUploadChoice() {
  const source = $('#pdf-source').value.trim();
  if (!state.selectedFile && source && !$('#pdf-title').value.trim()) {
    try {
      const parsed = new URL(source);
      const filename = decodeURIComponent(parsed.pathname.split('/').pop() || '');
      if (/\.pdf$/i.test(filename)) $('#pdf-title').value = filename.replace(/\.pdf$/i, '').replace(/[_-]+/g, ' ');
      else {
        const viewer = cbicViewerMatch(parsed);
        if (viewer) $('#pdf-title').value = `CBIC ${viewer[3].toLowerCase() === 'circulars' ? 'circular' : 'notification'} ${viewer[1]} (${viewer[2].toUpperCase()})`;
      }
    } catch { /* The submit handler reports an invalid URL. */ }
  }
  $('#upload-pdf').disabled = !state.selectedFile && !source;
  $('#upload-pdf').textContent = state.selectedFile ? 'Upload to knowledge base' : 'Import PDF from link';
}

function cbicViewerMatch(parsed) {
  return parsed.hostname === 'taxinformation.cbic.gov.in' && !parsed.search
    ? parsed.pathname.match(/^\/view-pdf\/([1-9][0-9]{0,11})\/(ENG|HINDI)\/(Notifications|Circulars)\/?$/i)
    : null;
}

async function upload(file) {
  if (file && (!file.name.toLowerCase().endsWith('.pdf') || file.size > 20 * 1024 * 1024)) { notice('Choose a PDF up to 20 MB.', true); return; }
  const title = $('#pdf-title').value.trim();
  const source = $('#pdf-source').value.trim();
  if (!title) { notice('Enter a document title.', true); return; }
  if (!file && !source) { notice('Choose a PDF or paste a direct PDF link.', true); return; }
  if (source && !source.startsWith('https://')) { notice('PDF URL must start with https://', true); $('#pdf-source').focus(); return; }
  if (source) {
    try { new URL(source); }
    catch { notice('Enter a valid HTTPS PDF URL.', true); $('#pdf-source').focus(); return; }
  }
  if (!file) {
    try {
      const parsed = new URL(source);
      if (!/\.pdf$/i.test(parsed.pathname) && !cbicViewerMatch(parsed)) throw new Error();
    } catch { notice('Enter a direct HTTPS .pdf link or a CBIC notification or circular viewer link.', true); return; }
  }
  const button = $('#upload-pdf'); if (button) { button.disabled = true; button.textContent = file ? 'Uploading…' : 'Importing…'; }
  try {
    let response;
    if (file) {
      const params = new URLSearchParams({ filename: file.name, title });
      if (source) params.set('source_url', source);
      response = await fetch(BASE + '/admin/documents?' + params, {
        method: 'POST', headers: { Authorization: 'Bearer ' + adminToken(), 'Content-Type': 'application/pdf' }, body: file,
      });
    } else {
      response = await fetch(BASE + '/admin/documents/from-url', {
        method: 'POST', headers: { Authorization: 'Bearer ' + adminToken(), 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: source, title }),
      });
    }
    const result = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(result.detail || `Import failed (${response.status})`);
    await navigate('legal');
    notice(`${title} added. Indexing is running; the status will update automatically.`);
  } catch (error) { notice(error.message, true); }
  finally { if (button?.isConnected) updateUploadChoice(); }
}

function showRemoveDialog(doc) {
  if (!doc) return;
  state.pendingRemoval = doc;
  $('#remove-document-title').textContent = doc.title || doc.filename;
  $('#remove-document-filename').textContent = doc.filename;
  $('#remove-dialog-error').hidden = true;
  $('#remove-dialog').showModal();
  $('#remove-cancel').focus();
}

async function confirmRemoveDocument() {
  const doc = state.pendingRemoval;
  if (!doc || state.removing) return;
  state.removing = true;
  const confirmButton = $('#remove-confirm');
  const cancelButton = $('#remove-cancel');
  confirmButton.disabled = true;
  cancelButton.disabled = true;
  confirmButton.textContent = 'Removing…';
  try {
    await api('/admin/documents/' + encodeURIComponent(doc.id), { method: 'DELETE' });
    $('#remove-dialog').close();
    await navigate('legal');
    notice(`${doc.filename} removed from the knowledge base.`);
  } catch (error) {
    $('#remove-dialog-error').textContent = error.message;
    $('#remove-dialog-error').hidden = false;
  } finally {
    state.removing = false;
    confirmButton.disabled = false;
    cancelButton.disabled = false;
    confirmButton.textContent = 'Remove document';
  }
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
    } else if (section === 'legal') {
      [state.documents, state.legalChanges] = await Promise.all([api('/admin/documents'), api('/admin/legal-changes')]);
      renderLegal();
    } else if (section === 'knowledge') {
      state.documents = await api('/admin/documents');
      renderKnowledge();
    } else if (section === 'users') renderUsers(await api('/admin/users?limit=200'));
    else if (section === 'conversations') renderConversations(await api('/admin/conversations?limit=200'));
    else if (section === 'health') renderHealth(await api('/admin/health'));
    else renderSettings(await api('/admin/settings'));
  } catch (error) { $('#section-content').innerHTML = `<div class="empty"><strong>Could not load this section</strong>${esc(error.message)}</div>`; }
  clearInterval(state.poll);
  if (section === 'legal' && state.documents.some((doc) => doc.status === 'processing')) {
    state.poll = setInterval(refreshDocumentData, 4000);
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
    $('#remove-cancel').onclick = () => $('#remove-dialog').close();
    $('#remove-confirm').onclick = confirmRemoveDocument;
    $('#remove-dialog').addEventListener('close', () => { state.pendingRemoval = null; });
    $('#remove-dialog').addEventListener('cancel', (event) => { if (state.removing) event.preventDefault(); });
    $('#remove-change-cancel').onclick = () => $('#remove-change-dialog').close();
    $('#remove-change-confirm').onclick = confirmRemoveChange;
    $('#remove-change-dialog').addEventListener('close', () => { state.pendingChangeRemoval = null; });
    $('#remove-change-dialog').addEventListener('cancel', (event) => { if (state.removingChange) event.preventDefault(); });
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
