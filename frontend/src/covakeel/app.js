import { api, signout } from './api.js';
import './integration.css';
/* CoVakeel app (chat window) · 2 November 2026 · every place marked demo is waiting for a real call */
(async () => {
  const B = document.body, $ = (s, r = document) => r.querySelector(s), $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const CHATS = [], IC = {"chat": "<svg viewBox=\"0 0 24 24\" width=\"20\" height=\"20\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.6\" stroke-linecap=\"round\" stroke-linejoin=\"round\" aria-hidden=\"true\"><path d=\"M4.5 6.5a2.5 2.5 0 0 1 2.5-2.5h10a2.5 2.5 0 0 1 2.5 2.5v7a2.5 2.5 0 0 1-2.5 2.5H10l-4.5 4v-4h0a1 1 0 0 1-1-1z\"/></svg>", "folder": "<svg viewBox=\"0 0 24 24\" width=\"20\" height=\"20\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.6\" stroke-linecap=\"round\" stroke-linejoin=\"round\" aria-hidden=\"true\"><path d=\"M3.5 7a2 2 0 0 1 2-2h4l2 2h7a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2h-13a2 2 0 0 1-2-2z\"/></svg>", "chev": "<svg viewBox=\"0 0 24 24\" width=\"18\" height=\"18\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.9\" stroke-linecap=\"round\" stroke-linejoin=\"round\" aria-hidden=\"true\"><path d=\"M9 6l6 6-6 6\"/></svg>"}, AIHEAD = "<div class=\"ai-h\"><span class=\"ai-m\" aria-hidden=\"true\"><svg class=\"ai-mk\" viewBox=\"0 0 200 200\" aria-hidden=\"true\"><circle class=\"d\" cx=\"100.00\" cy=\"100.00\" r=\"9.50\"/><circle class=\"d\" cx=\"100.00\" cy=\"76.00\" r=\"9.50\"/><circle class=\"d\" cx=\"120.78\" cy=\"88.00\" r=\"9.50\"/><circle class=\"d\" cx=\"120.78\" cy=\"112.00\" r=\"9.50\"/><circle class=\"d\" cx=\"100.00\" cy=\"124.00\" r=\"9.50\"/><circle class=\"d\" cx=\"79.22\" cy=\"112.00\" r=\"9.50\"/><circle class=\"d\" cx=\"79.22\" cy=\"88.00\" r=\"9.50\"/><circle class=\"d\" cx=\"100.00\" cy=\"54.00\" r=\"9.32\"/><circle class=\"d\" cx=\"123.00\" cy=\"60.16\" r=\"9.32\"/><circle class=\"d\" cx=\"139.84\" cy=\"77.00\" r=\"9.32\"/><circle class=\"d\" cx=\"146.00\" cy=\"100.00\" r=\"9.32\"/><circle class=\"d\" cx=\"139.84\" cy=\"123.00\" r=\"9.32\"/><circle class=\"d\" cx=\"123.00\" cy=\"139.84\" r=\"9.32\"/><circle class=\"d\" cx=\"100.00\" cy=\"146.00\" r=\"9.32\"/><circle class=\"d\" cx=\"77.00\" cy=\"139.84\" r=\"9.32\"/><circle class=\"d\" cx=\"60.16\" cy=\"123.00\" r=\"9.32\"/><circle class=\"d\" cx=\"54.00\" cy=\"100.00\" r=\"9.32\"/><circle class=\"d\" cx=\"60.16\" cy=\"77.00\" r=\"9.32\"/><circle class=\"d\" cx=\"77.00\" cy=\"60.16\" r=\"9.32\"/><circle class=\"d\" cx=\"100.00\" cy=\"32.00\" r=\"6.60\"/><circle class=\"d\" cx=\"123.26\" cy=\"36.10\" r=\"6.60\"/><circle class=\"d\" cx=\"143.71\" cy=\"47.91\" r=\"6.60\"/><circle class=\"d\" cx=\"158.89\" cy=\"66.00\" r=\"6.60\"/><circle class=\"d\" cx=\"166.97\" cy=\"88.19\" r=\"6.60\"/><circle class=\"d\" cx=\"166.97\" cy=\"111.81\" r=\"6.60\"/><circle class=\"d\" cx=\"158.89\" cy=\"134.00\" r=\"6.60\"/><circle class=\"d\" cx=\"143.71\" cy=\"152.09\" r=\"6.60\"/><circle class=\"d\" cx=\"123.26\" cy=\"163.90\" r=\"6.60\"/><circle class=\"d\" cx=\"100.00\" cy=\"168.00\" r=\"6.60\"/><circle class=\"d\" cx=\"76.74\" cy=\"163.90\" r=\"6.60\"/><circle class=\"d\" cx=\"56.29\" cy=\"152.09\" r=\"6.60\"/><circle class=\"d\" cx=\"41.11\" cy=\"134.00\" r=\"6.60\"/><circle class=\"d\" cx=\"33.03\" cy=\"111.81\" r=\"6.60\"/><circle class=\"d\" cx=\"33.03\" cy=\"88.19\" r=\"6.60\"/><circle class=\"d\" cx=\"41.11\" cy=\"66.00\" r=\"6.60\"/><circle class=\"d\" cx=\"56.29\" cy=\"47.91\" r=\"6.60\"/><circle class=\"d\" cx=\"76.74\" cy=\"36.10\" r=\"6.60\"/><circle class=\"d\" cx=\"100.00\" cy=\"10.00\" r=\"3.40\"/><circle class=\"d\" cx=\"123.29\" cy=\"13.07\" r=\"3.40\"/><circle class=\"d\" cx=\"145.00\" cy=\"22.06\" r=\"3.40\"/><circle class=\"d\" cx=\"163.64\" cy=\"36.36\" r=\"3.40\"/><circle class=\"d\" cx=\"177.94\" cy=\"55.00\" r=\"3.40\"/><circle class=\"d\" cx=\"186.93\" cy=\"76.71\" r=\"3.40\"/><circle class=\"d\" cx=\"190.00\" cy=\"100.00\" r=\"3.40\"/><circle class=\"d\" cx=\"186.93\" cy=\"123.29\" r=\"3.40\"/><circle class=\"d\" cx=\"177.94\" cy=\"145.00\" r=\"3.40\"/><circle class=\"d\" cx=\"163.64\" cy=\"163.64\" r=\"3.40\"/><circle class=\"d\" cx=\"145.00\" cy=\"177.94\" r=\"3.40\"/><circle class=\"d\" cx=\"123.29\" cy=\"186.93\" r=\"3.40\"/><circle class=\"d\" cx=\"100.00\" cy=\"190.00\" r=\"3.40\"/><circle class=\"d\" cx=\"76.71\" cy=\"186.93\" r=\"3.40\"/><circle class=\"d\" cx=\"55.00\" cy=\"177.94\" r=\"3.40\"/><circle class=\"d\" cx=\"36.36\" cy=\"163.64\" r=\"3.40\"/><circle class=\"d\" cx=\"22.06\" cy=\"145.00\" r=\"3.40\"/><circle class=\"d\" cx=\"13.07\" cy=\"123.29\" r=\"3.40\"/><circle class=\"d\" cx=\"10.00\" cy=\"100.00\" r=\"3.40\"/><circle class=\"d\" cx=\"13.07\" cy=\"76.71\" r=\"3.40\"/><circle class=\"d\" cx=\"22.06\" cy=\"55.00\" r=\"3.40\"/><circle class=\"d\" cx=\"36.36\" cy=\"36.36\" r=\"3.40\"/><circle class=\"d\" cx=\"55.00\" cy=\"22.06\" r=\"3.40\"/><circle class=\"d\" cx=\"76.71\" cy=\"13.07\" r=\"3.40\"/></svg></span><b>CoVakeel AI</b><span class=\"ai-s\">{s}</span></div>";
  const TODAY = new Date();                       // demo: the live app uses the real date
  let account;
  try { account = await api('/users/me'); }
  catch (error) {
    if (error.status === 401 || !localStorage.getItem('token')) location.replace('/login');
    else {
      const message = document.createElement('p'); message.textContent = error.message;
      message.style.cssText = 'margin:auto;padding:24px;color:var(--err)';
      document.body.replaceChildren(message);
    }
    return;
  }
  localStorage.setItem('cv-user', JSON.stringify(account));
  const toChat = c => ({ k: c.id, t: c.title || 'Untitled', m: 'Library', d: c.createdAt.slice(0, 10) });
  let initialError = '';
  try { CHATS.push(...(await api('/conversations/')).map(toChat)); }
  catch (error) { initialError = error.message; }
  let currentChatId = null, sending = false, viewRevision = 0;
  const dock = () => innerWidth >= 900;
  const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const day = d => new Date(d + 'T12:00:00');
  const ago = d => Math.round((TODAY - day(d)) / 864e5);
  const fmt = d => ago(d) === 0 ? 'Today' : day(d).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' });
  const setHash = h => { try { if (location.hash !== h) history.replaceState(null, '', h); } catch (e) {} };

  // toast
  const toast = $('#toast'); let tt;
  const say = m => { toast.textContent = m; toast.classList.add('in'); clearTimeout(tt); tt = setTimeout(() => toast.classList.remove('in'), 2400); };
  document.addEventListener('click', e => { const d = e.target.closest('[data-demo]'); if (d) { e.preventDefault(); say(d.dataset.demo); if (d.closest('#um')) setUm(false); } });

  // side menu: on phones it slides in; on wide screens it folds to icons
  const isOpen = () => dock() ? !B.classList.contains('side-col') : B.classList.contains('side-open');
  const sync = () => { const o = isOpen(); $$('[data-side-toggle]').forEach(b => { b.setAttribute('aria-expanded', String(o)); b.setAttribute('aria-label', o ? 'Close menu' : 'Open menu'); b.title = o ? 'Close menu' : 'Open menu'; }); };
  const setOpen = on => { B.classList.toggle('side-open', on); sync(); };
  $$('[data-side-toggle]').forEach(b => b.addEventListener('click', () => {
    if (dock()) { B.classList.toggle('side-col'); setUm(false); sync(); }
    else { const on = !B.classList.contains('side-open'); setOpen(on); if (on) $('.sd-new').focus(); else $('.m-top [data-side-toggle]').focus(); } }));
  $('.ca-scrim').addEventListener('click', () => setOpen(false));
  addEventListener('resize', () => { if (dock()) B.classList.remove('side-open'); sync(); ph(); });

  // account menu (opens from your name)
  const avBtn = $('#av-btn'), um = $('#um');
  const setUm = on => { um.hidden = !on; avBtn.setAttribute('aria-expanded', String(on)); };
  avBtn.addEventListener('click', e => { e.stopPropagation(); const on = um.hidden; setUm(on); if (on) $('.um-i', um).focus(); });
  document.addEventListener('click', e => { if (!um.hidden && !e.target.closest('#um') && !e.target.closest('#av-btn')) setUm(false); });
  document.addEventListener('keydown', e => { if (e.key !== 'Escape') return;
    if (!um.hidden) { setUm(false); avBtn.focus(); } else if (B.classList.contains('side-open') && !dock()) { setOpen(false); $('.m-top [data-side-toggle]').focus(); } });

  // screens
  const VIEWS = ['ask', 'chats', 'proj', 'profile', 'subs'];
  function go(v, sub) {
    if (v === 'profile' && sub === 'subs') v = 'subs';
    if (!VIEWS.includes(v)) v = 'ask';
    B.dataset.view = v;
    $$('.ca-view').forEach(s => { s.hidden = s.dataset.v !== v; });
    $$('.sd-nav [data-go]').forEach(b => b.dataset.go === v ? b.setAttribute('aria-current', 'page') : b.removeAttribute('aria-current'));
    const sec = v === 'profile' && { addr: 'sec-addr', mode: 'sec-mode', pass: 'sec-pass' }[sub];
    if (v !== 'ask') { mark(null); title(''); }
    if (!dock()) setOpen(false);
    setUm(false);
    if (v !== 'ask') setHash('#' + v);
    const s = $('.ca-view[data-v="' + v + '"]'); if (s && v !== 'ask') s.scrollTop = 0;
    if (sec) requestAnimationFrame(() => $('#' + sec).scrollIntoView({ block: 'start' }));
  }
  document.addEventListener('click', e => { const g = e.target.closest('[data-go]'); if (!g) return; e.preventDefault();
    const [v, s] = g.dataset.go.split('/'); go(v, s); if (g.dataset.focus) setTimeout(() => $('#' + g.dataset.focus).focus(), 30); });

  // chat
  const V = $('.v-ask'), thread = $('#thread'), sc = $('#ask-sc'), q = $('#q'), send = $('.send');
  const ph = () => { q.placeholder = V.classList.contains('fresh') ? (innerWidth < 480 ? 'Ask a tax question' : 'How can CoVakeel AI help you today?') : 'Reply to CoVakeel AI'; };
  const hr = new Date().getHours(); $('#hello-t').textContent = hr < 12 ? 'Good morning' : hr < 17 ? 'Good afternoon' : 'Good evening';
  const mark = k => $$('.sd-c').forEach(x => x.classList.toggle('on', x.dataset.open === k));
  const title = t => { $('#c-title').textContent = t; $('#m-title').textContent = t; B.classList.toggle('in-chat', !!t); };
  const short = t => t.length > 48 ? t.slice(0, 46) + '…' : t;
  function fresh() { currentChatId = null; viewRevision++; go('ask'); V.classList.add('fresh'); thread.innerHTML = ''; mark(null); title(''); q.value = ''; grow(); ph(); setHash('#new'); }
  function chatMode() { V.classList.remove('fresh'); ph(); }
  async function openChat(k) {
    const c = CHATS.find(x => x.k === k); if (!c) return fresh();
    const revision = ++viewRevision; currentChatId = k;
    go('ask'); chatMode(); mark(k); title(c.t); setHash('#chat/' + k);
    thread.replaceChildren();
    const loading = document.createElement('p'); loading.className = 'note'; loading.textContent = 'Opening your chat…'; thread.append(loading);
    try {
      const messages = await api('/messages/by_conversation/' + encodeURIComponent(k));
      if (revision !== viewRevision) return;
      thread.replaceChildren();
      for (const message of messages) {
        const element = renderMessage(message); thread.append(element);
        if (message.sender === 'assistant') loadSources(message.id, element);
      }
      sc.scrollTop = 0;
    } catch (error) {
      if (revision !== viewRevision) return;
      loading.textContent = error.message; loading.classList.add('cv-error');
    }
  }
  function appendAnswerInline(parent, value) {
    const pieces = value.split(/(\*\*[^*]+\*\*|`[^`]+`|\[\d+(?:,\s*\d+)*\]|\*[^*\n]+\*)/g);
    for (const piece of pieces) {
      if (/^\[\d+(?:,\s*\d+)*\]$/.test(piece)) {
        for (const number of piece.slice(1, -1).split(',').map(x => x.trim())) {
          const citation = document.createElement('button'); citation.type = 'button'; citation.className = 'cite';
          citation.dataset.citation = number; citation.textContent = '[' + number + ']';
          citation.setAttribute('aria-label', 'Open cited source ' + number); parent.append(citation);
        }
      } else if ((piece.startsWith('**') && piece.endsWith('**')) || (piece.startsWith('`') && piece.endsWith('`')) || (piece.startsWith('*') && piece.endsWith('*'))) {
        const tag = piece.startsWith('**') ? 'strong' : piece.startsWith('`') ? 'code' : 'em';
        const inline = document.createElement(tag); inline.textContent = piece.slice(tag === 'strong' ? 2 : 1, tag === 'strong' ? -2 : -1); parent.append(inline);
      } else parent.append(document.createTextNode(piece));
    }
  }
  function renderAnswer(answer, text) {
    const lines = text.split(/\r?\n/);
    const isHeading = line => /^#{1,4}\s+/.test(line);
    const isRule = line => /^\s*(?:---+|___+)\s*$/.test(line);
    const isBullet = line => /^\s*[-*•]\s+/.test(line);
    const isNumbered = line => /^\s*\d+[.)]\s+/.test(line);
    const isTable = line => /^\s*\|.*\|\s*$/.test(line);
    let i = 0;
    while (i < lines.length) {
      const line = lines[i].trim();
      if (!line) { i++; continue; }
      if (isHeading(line)) {
        const level = Math.min(4, line.match(/^#+/)[0].length + 1);
        const heading = document.createElement('h' + level); appendAnswerInline(heading, line.replace(/^#{1,4}\s+/, '')); answer.append(heading); i++; continue;
      }
      if (isRule(line)) { answer.append(document.createElement('hr')); i++; continue; }
      if (isBullet(line) || isNumbered(line)) {
        const numbered = isNumbered(line), list = document.createElement(numbered ? 'ol' : 'ul');
        while (i < lines.length && (numbered ? isNumbered(lines[i]) : isBullet(lines[i]))) {
          const item = document.createElement('li'); appendAnswerInline(item, lines[i].trim().replace(numbered ? /^\d+[.)]\s+/ : /^[-*•]\s+/, ''));
          list.append(item); i++;
        }
        answer.append(list); continue;
      }
      if (isTable(line)) {
        const wrap = document.createElement('div'); wrap.className = 'cv-answer-table';
        const table = document.createElement('table'); let rowIndex = 0;
        while (i < lines.length && isTable(lines[i])) {
          const cells = lines[i].trim().slice(1, -1).split('|').map(cell => cell.trim()); i++;
          if (cells.every(cell => /^:?-{3,}:?$/.test(cell))) continue;
          const row = document.createElement('tr');
          for (const cell of cells) { const col = document.createElement(rowIndex ? 'td' : 'th'); appendAnswerInline(col, cell); row.append(col); }
          table.append(row); rowIndex++;
        }
        wrap.append(table); answer.append(wrap); continue;
      }
      if (line.startsWith('>')) {
        const quote = document.createElement('blockquote'); const content = [];
        while (i < lines.length && lines[i].trim().startsWith('>')) { content.push(lines[i].trim().replace(/^>\s?/, '')); i++; }
        appendAnswerInline(quote, content.join(' ')); answer.append(quote); continue;
      }
      const paragraph = document.createElement('p'), content = [];
      while (i < lines.length && lines[i].trim() && !isHeading(lines[i].trim()) && !isRule(lines[i]) && !isBullet(lines[i]) && !isNumbered(lines[i]) && !isTable(lines[i]) && !lines[i].trim().startsWith('>')) {
        content.push(lines[i].trim()); i++;
      }
      appendAnswerInline(paragraph, content.join(' ')); answer.append(paragraph);
    }
  }
  function renderMessage(message) {
    const node = document.createElement('div'); node.className = 'msg ' + (message.sender === 'user' ? 'user' : 'ai');
    node.dataset.messageId = message.id;
    if (message.sender === 'assistant') node.innerHTML = AIHEAD.replace('{s}', '');
    const answer = document.createElement('div'); answer.className = message.sender === 'assistant' ? 'ans ans-live' : '';
    if (message.sender === 'assistant') renderAnswer(answer, message.text);
    else answer.textContent = message.text;
    node.append(answer);
    if (message.sender === 'assistant') {
      const actions = document.createElement('div'); actions.className = 'act';
      actions.innerHTML = `<button class="ib" data-copy aria-label="Copy answer" title="Copy answer">${IC.chat}</button><button class="ib cv-export" data-export="docx" aria-label="Download answer as Word document" title="Download Word document">DOC</button><button class="ib cv-export" data-export="pdf" aria-label="Download answer as PDF" title="Download PDF">PDF</button><button class="ib" data-save aria-label="Save answer" title="Save answer" aria-pressed="false">${IC.folder}</button><button class="ib" data-fb="yes" aria-label="Helpful" title="Helpful" aria-pressed="false"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M7 10v11H3V10h4zm0 0 5-8 2 1v6h5l2 2-2 9H7"/></svg></button><button class="ib" data-fb="no" aria-label="Not helpful" title="Not helpful" aria-pressed="false"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M7 14V3H3v11h4zm0 0 5 8 2-1v-6h5l2-2-2-9H7"/></svg></button>`;
      const saved = JSON.parse(localStorage.getItem('cv-saved:' + account.id) || '{}');
      actions.querySelector('[data-save]').setAttribute('aria-pressed', String(!!saved[message.id]));
      node.append(actions);
    }
    return node;
  }
  async function loadSources(id, node) {
    try {
      const sources = await api('/messages/' + encodeURIComponent(id) + '/sources');
      if (!sources.length || !node.isConnected) return;
      const grouped = new Map();
      for (const source of sources) {
        const name = source.filename || source.metadata?.filename || 'Library document';
        const key = source.metadata?.citation_id ? 'citation:' + source.metadata.citation_id : name;
        if (!grouped.has(key)) grouped.set(key, []);
        grouped.get(key).push(source);
      }
      node.querySelector('.ai-s').textContent = grouped.size + (grouped.size === 1 ? ' source' : ' sources');
      const heading = document.createElement('div'); heading.className = 'cv-citations-head';
      heading.textContent = 'Citations · ' + grouped.size + (grouped.size === 1 ? ' document' : ' documents');
      node.insertBefore(heading, node.querySelector('.act'));
      let index = 0;
      for (const [, passages] of grouped) {
        index++;
        const card = document.createElement('div'); card.className = 'src';
        const filename = passages[0].filename || passages[0].metadata?.filename || 'Library document';
        const citation = passages[0].metadata?.citation_id || index;
        card.dataset.citation = citation;
        const pages = [...new Set(passages.map(p => p.metadata?.page).filter(Boolean))].sort((a,b) => a-b);
        const label = passages.length + (passages.length === 1 ? ' passage' : ' passages') + (pages.length ? ' · Pages ' + pages.join(', ') : '');
        const title = passages[0]?.metadata?.title || filename.replace(/_/g, ' ').replace(/\.pdf$/i, '');
        const reviewed = passages[0]?.metadata?.source_type === 'reviewed legal change';
        card.innerHTML = `<button class="src-h" type="button" aria-expanded="false"><span class="num">${esc(citation)}</span><span class="src-t"><b>${esc(title)}</b><span>${esc(reviewed ? 'Source-reviewed summary · ' + label : label)}</span></span><span class="src-c"><span class="m-o">${reviewed ? 'Review summary' : 'Read source'}</span><span class="m-c">Close</span></span>${IC.chev}</button><div class="law" hidden></div>`;
        const law = card.querySelector('.law'); law.tabIndex = 0; law.setAttribute('aria-label', 'Retrieved library passages');
        for (const passage of passages) {
          const section = document.createElement('div'); section.className = 'cv-passage';
          if (passage.metadata?.page) { const heading = document.createElement('b'); heading.textContent = 'Page ' + passage.metadata.page; section.append(heading); }
          const text = document.createElement('p'); text.textContent = passage.content; text.style.whiteSpace = 'pre-wrap'; section.append(text); law.append(section);
        }
        const source = passages[0];
        const officialUrl = source?.metadata?.source_url;
        const actions = document.createElement('div'); actions.className = 'cv-source-actions';
        if (/^https:\/\//i.test(officialUrl || '')) {
          const link = document.createElement('a');
          link.href = officialUrl; link.target = '_blank'; link.rel = 'noopener noreferrer';
          link.className = 'cv-source-open'; link.textContent = 'Official website ↗';
          actions.append(link);
        }
        if (source?.metadata?.document_id) {
          const openPdf = document.createElement('button'); openPdf.type = 'button';
          openPdf.className = 'cv-pdf-open'; openPdf.dataset.sourceId = source.id;
          openPdf.textContent = 'Open source PDF ↗'; actions.prepend(openPdf);
          const downloadPdf = document.createElement('button'); downloadPdf.type = 'button';
          downloadPdf.className = 'cv-pdf-download'; downloadPdf.dataset.sourceId = source.id;
          downloadPdf.dataset.filename = filename; downloadPdf.textContent = 'Download source PDF';
          actions.append(downloadPdf);
        }
        if (actions.childElementCount) card.append(actions);
        node.insertBefore(card, node.querySelector('.act'));
      }
    } catch { if (node.isConnected) node.querySelector('.ai-s').textContent = 'Sources unavailable'; }
  }
  $$('[data-new]').forEach(b => b.addEventListener('click', e => { e.preventDefault(); fresh(); setTimeout(() => q.focus({ preventScroll: true }), 30); }));
  document.addEventListener('click', e => { const o = e.target.closest('[data-open]'); if (o) openChat(o.dataset.open); });
  const grow = () => { q.style.height = 'auto'; q.style.height = Math.min(q.scrollHeight, 200) + 'px'; send.disabled = sending || !q.value.trim(); };
  q.addEventListener('input', grow);
  q.addEventListener('keydown', e => { if (e.key === 'Enter' && !e.shiftKey && innerWidth >= 900) { e.preventDefault(); $('#comp').requestSubmit(); } });
  const bottom = () => { sc.scrollTop = sc.scrollHeight; };
  async function ask(text) {
    if (sending || !text.trim()) return;
    sending = true; grow();
    const revision = viewRevision;
    let destination = currentChatId;
    const think = document.createElement('div'); think.className = 'msg think';
    think.innerHTML = '<span class="dots" aria-hidden="true"><i></i><i></i><i></i></span><span>Reading the law…</span>';
    try {
      if (!destination) {
        const conversation = await api('/conversations/', { method: 'POST', body: { title: short(text) } });
        destination = conversation.id;
        CHATS.unshift(toChat(conversation)); renderSidebar(); renderChats();
        if (revision !== viewRevision) return;
        currentChatId = destination; chatMode(); mark(destination); title(conversation.title); setHash('#chat/' + destination);
      }
      thread.append(renderMessage({ id: 'pending-user', sender: 'user', text }));
      thread.append(think); bottom();
      const response = await api('/chat/?' + new URLSearchParams({ conversationId: destination, text }), { method: 'POST' });
      if (revision !== viewRevision || currentChatId !== destination) return;
      think.remove();
      const answer = renderMessage(response); thread.append(answer); await loadSources(response.id, answer); bottom();
    } catch (error) {
      think.remove();
      if (revision === viewRevision) {
        const notice = document.createElement('div'); notice.className = 'msg cv-error'; notice.setAttribute('role', 'alert'); notice.textContent = error.message;
        thread.append(notice); bottom();
        q.value = text;
      }
      say(error.message);
    } finally { sending = false; grow(); if (revision === viewRevision) q.focus({ preventScroll: true }); }
  }
  $('#comp').addEventListener('submit', e => { e.preventDefault(); const t = q.value.trim(); if (!t) return; q.value = ''; grow(); ask(t); });
  document.addEventListener('click', e => { const s = e.target.closest('[data-ask]'); if (s) ask(s.textContent.trim(), s.dataset.kind); });
  // sources, copy, feedback
  const pdfUrls = new Set();
  addEventListener('beforeunload', () => pdfUrls.forEach(url => URL.revokeObjectURL(url)));
  const sourcePdfPath = (msgId, sourceId) => '/messages/' + encodeURIComponent(msgId) + '/sources/' + encodeURIComponent(sourceId) + '/pdf';
  function downloadBlob(blob, filename) {
    const url = URL.createObjectURL(blob), link = document.createElement('a');
    link.href = url; link.download = filename.replace(/[/\\]/g, '_');
    document.body.append(link); link.click(); link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 30000);
  }
  async function openIndexedPdf(msgId, sourceId) {
    const tab = window.open('about:blank', '_blank');
    if (!tab) return say('Allow pop-ups to open the PDF in a new tab');
    tab.opener = null;
    try {
      const blob = await api(sourcePdfPath(msgId, sourceId), { responseType: 'blob' });
      const url = URL.createObjectURL(blob); pdfUrls.add(url); tab.location.replace(url);
    } catch (error) { tab.close(); say(error.message); }
  }
  const toggleSrc = (h, on) => { h.setAttribute('aria-expanded', String(on)); h.nextElementSibling.hidden = !on; };
  document.addEventListener('click', e => {
    const h = e.target.closest('.src-h'); if (h) toggleSrc(h, h.getAttribute('aria-expanded') !== 'true');
    const c = e.target.closest('.cite'); if (c) { const s = [...c.closest('.msg').querySelectorAll('.src')].find(x => x.dataset.citation === c.dataset.citation);
      if (!s) return; toggleSrc($('.src-h', s), true);
      const official = s.querySelector('.cv-source-open'), local = s.querySelector('.cv-pdf-open');
      if (local) local.click(); else if (official) official.click();
      else s.scrollIntoView({ block: 'nearest', behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' });
      s.classList.remove('flash'); void s.offsetWidth; s.classList.add('flash'); setTimeout(() => s.classList.remove('flash'), 1600); }
    const openPdf = e.target.closest('.cv-pdf-open');
    if (openPdf) openIndexedPdf(openPdf.closest('.msg').dataset.messageId, openPdf.dataset.sourceId);
    const downloadPdf = e.target.closest('.cv-pdf-download');
    if (downloadPdf) api(sourcePdfPath(downloadPdf.closest('.msg').dataset.messageId, downloadPdf.dataset.sourceId) + '?download=true', { responseType: 'blob' })
      .then(blob => downloadBlob(blob, downloadPdf.dataset.filename || 'source.pdf'), error => say(error.message));
    const exportButton = e.target.closest('[data-export]');
    if (exportButton) {
      const format = exportButton.dataset.export, msgId = exportButton.closest('.msg').dataset.messageId;
      exportButton.disabled = true;
      api('/messages/' + encodeURIComponent(msgId) + '/export/' + format, { responseType: 'blob' })
        .then(blob => downloadBlob(blob, 'CoVakeel-answer-' + msgId.slice(0, 8) + '.' + format), error => say(error.message))
        .finally(() => { exportButton.disabled = false; });
    }
    const cp = e.target.closest('[data-copy]'); if (cp) { const a = cp.closest('.msg').querySelector('.ans');
      (navigator.clipboard ? navigator.clipboard.writeText(a.innerText) : Promise.reject()).then(() => say('Answer copied'), () => say('Select the text to copy it')); }
    const f = e.target.closest('[data-fb]'); if (f) { const on = f.getAttribute('aria-pressed') !== 'true';
      f.parentElement.querySelectorAll('[data-fb]').forEach(x => x.setAttribute('aria-pressed', 'false')); f.setAttribute('aria-pressed', String(on)); if (on) say('Thanks for the feedback'); }
  });

  const clearBtn = i => { const b = $('[data-clear="' + i.id + '"]'); if (b) b.hidden = !i.value; };
  document.addEventListener('click', e => { const b = e.target.closest('[data-clear]'); if (!b) return; const i = $('#' + b.dataset.clear); i.value = ''; i.dispatchEvent(new Event('input')); i.focus(); });
  // your chats
  const wq = $('#ws-q'), wm = $('#ws-mod'), wp = $('#ws-per'), wsort = $('#ws-sort');
  function renderSidebar() {
    $('#sd-list').innerHTML = CHATS.map(c => `<li><button class="sd-c${c.k === currentChatId ? ' on' : ''}" data-open="${c.k}" title="${esc(c.t)}">${esc(c.t)}</button></li>`).join('');
  }
  renderSidebar();
  function renderChats() {
    const t = wq.value.trim().toLowerCase(), m = wm.value, p = +wp.value || 0;
    const L = CHATS.filter(c => (!t || c.t.toLowerCase().includes(t)) && (!m || c.m === m) && (!p || ago(c.d) < p))
      .sort((a, b) => wsort.value === 'old' ? a.d.localeCompare(b.d) : b.d.localeCompare(a.d));
    $('#ws-chats').innerHTML = L.map(c => `<li class="cv-chat-row"><button type="button" class="row" data-open="${c.k}"><span class="row-ic">${IC.chat}</span><span class="row-t"><b>${esc(c.t)}</b><span><span class="tag">${c.m}</span>${fmt(c.d)}</span></span></button><span class="cv-row-tools"><button class="ib" type="button" data-rename="${c.k}" aria-label="Rename chat" title="Rename chat"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="m14 5 5 5M4 20l4-1L20 7l-4-4L4 15v5z"/></svg></button><button class="ib" type="button" data-delete="${c.k}" aria-label="Delete chat" title="Delete chat"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M4 7h16M9 7V4h6v3M6 7l1 14h10l1-14M10 10v7M14 10v7"/></svg></button></span></li>`).join('');
    $('#ws-chats').hidden = !L.length; $('#ws-chats-0').hidden = !!L.length;
    $('#ws-n').textContent = L.length + (L.length === 1 ? ' chat' : ' chats');
    $('#ws-foot').textContent = L.length ? `Showing 1 to ${L.length} of ${L.length}` : '';
    $('[data-reset]').hidden = !(t || m || p || wsort.value !== 'new');
    clearBtn(wq);
  }
  [wq, wm, wp, wsort].forEach(x => x.addEventListener(x === wq ? 'input' : 'change', renderChats));
  $('[data-reset]').addEventListener('click', () => { wq.value = ''; wm.value = ''; wp.value = ''; wsort.value = 'new'; renderChats(); wq.focus(); });
  renderChats();
  // Projects are kept per account on this device.
  const projects = JSON.parse(localStorage.getItem('cv-projects:' + account.id) || '[]'), pq = $('#pj-q'), pjf = $('#pj-form'), pjn = $('#pj-name');
  function renderProj() {
    const t = pq.value.trim().toLowerCase(), L = projects.filter(p => !t || p.n.toLowerCase().includes(t));
    $('#pj-list').innerHTML = L.map(p => `<li class="pj"><span class="row-ic">${IC.folder}</span><b>${esc(p.n)}</b><span>0 chats · Created ${fmt(p.d).toLowerCase()}</span></li>`).join('');
    $('#pj-list').hidden = !L.length; $('#pj-0').hidden = !!L.length || !pjf.hidden && !projects.length;
    $('#pj-0 b').textContent = projects.length ? 'No projects match' : 'No projects yet';
    $('#pj-n').textContent = L.length + (L.length === 1 ? ' project' : ' projects'); clearBtn(pq);
  }
  pq.addEventListener('input', renderProj);
  $('[data-newproj]').addEventListener('click', () => { pjf.hidden = false; renderProj(); pjn.focus(); });
  $('[data-pjcancel]').addEventListener('click', () => { pjf.hidden = true; pjn.value = ''; $('.ferr', pjf).hidden = true; pjn.closest('.fld').classList.remove('bad'); renderProj(); });
  pjf.addEventListener('submit', e => { e.preventDefault(); const n = pjn.value.trim();
    if (!n) { pjn.closest('.fld').classList.add('bad'); const er = $('.ferr', pjf); er.textContent = 'Give the project a name.'; er.hidden = false; pjn.focus(); return; }
    projects.unshift({ n, d: new Date().toISOString().slice(0,10) }); localStorage.setItem('cv-projects:' + account.id, JSON.stringify(projects)); pjn.value = ''; pjf.hidden = true; $('.ferr', pjf).hidden = true; pjn.closest('.fld').classList.remove('bad'); renderProj(); say('Project created'); });
  pjn.addEventListener('input', () => { pjn.closest('.fld').classList.remove('bad'); $('.ferr', pjf).hidden = true; });
  renderProj();

  // settings: colour mode. Auto follows the device; Light or Dark is kept on this device
  const MODES = ['auto', 'light', 'dark'], NAMES = { auto: 'Auto', light: 'Light', dark: 'Dark' };
  const savedMode = () => { try { const t = localStorage.getItem('cv-theme'); return t === 'light' || t === 'dark' ? t : 'auto'; } catch (e) { return 'auto'; } };
  function setMode(m, save) {
    if (m === 'auto') document.documentElement.removeAttribute('data-theme'); else document.documentElement.setAttribute('data-theme', m);
    $$('[data-mode-set]').forEach(b => { const on = b.dataset.modeSet === m; b.setAttribute('aria-checked', String(on)); b.tabIndex = on ? 0 : -1; });
    if (save) { try { if (m === 'auto') localStorage.removeItem('cv-theme'); else localStorage.setItem('cv-theme', m); } catch (e) {} say(NAMES[m] + ' mode on'); }
  }
  $$('[data-mode-set]').forEach(b => {
    b.addEventListener('click', () => setMode(b.dataset.modeSet, true));
    b.addEventListener('keydown', e => { const k = { ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1 }[e.key]; if (!k) return; e.preventDefault();
      const n = MODES[(MODES.indexOf(b.dataset.modeSet) + k + MODES.length) % MODES.length]; setMode(n, true); $('[data-mode-set="' + n + '"]').focus(); });
  });
  setMode(savedMode(), false);

  // profile
  const fail = (f, n, m) => { const i = f.elements[n]; i.closest('.fld').classList.add('bad'); i.setAttribute('aria-invalid', 'true'); i.focus();
    const er = $(':scope > .ferr', f); er.textContent = m; er.hidden = false; return false; };
  const okf = f => { $$('.fld.bad', f).forEach(x => x.classList.remove('bad')); $$('[aria-invalid]', f).forEach(x => x.removeAttribute('aria-invalid')); $(':scope > .ferr', f).hidden = true; };
  $$('form.form').forEach(f => f.addEventListener('input', e => { const fl = e.target.closest('.fld'); if (fl) fl.classList.remove('bad'); e.target.removeAttribute('aria-invalid'); $(':scope > .ferr', f).hidden = true; }));
  const fi = $('#f-info');
  fi.addEventListener('submit', async e => { e.preventDefault(); okf(fi); const v = n => fi.elements[n].value.trim();
    if (!v('first')) return fail(fi, 'first', 'Enter your first name.');
    const pn = v('phone').replace(/\D/g, ''), cc = $('.cc select', fi).value;
    if (!v('email') && !pn) return fail(fi, 'email', 'Add your email or your mobile number. One is enough.');
    if (v('email') && !/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(v('email'))) return fail(fi, 'email', 'Enter a valid email.');
    if (pn && (cc === '+91' ? !/^[6-9]\d{9}$/.test(pn) : !/^\d{6,14}$/.test(pn))) return fail(fi, 'phone', cc === '+91' ? 'Enter a 10 digit Indian mobile number.' : 'Enter a valid mobile number.');
    fi.elements.agst.value = v('agst').toUpperCase();
    if (!v('state')) return fail(fi, 'state', 'Choose your state.');
    if (v('apin') && !/^[1-9]\d{5}$/.test(v('apin'))) return fail(fi, 'apin', 'Enter a 6 digit PIN code.');
    if (v('agst') && !/^\d{2}[A-Z]{5}\d{4}[A-Z][1-9A-Z]Z[0-9A-Z]$/.test(v('agst'))) return fail(fi, 'agst', 'This GSTIN does not look right. Check the 15 characters.');
    const name = v('last') ? v('first') + ' ' + v('last') : v('first');
    const submit = fi.querySelector('[type="submit"]'); submit.disabled = true;
    try {
      account = await api('/users/' + account.id, { method: 'PUT', body: {
        name, email: v('email') || null, profile: Object.fromEntries(new FormData(fi))
      } });
      localStorage.setItem('cv-user', JSON.stringify(account));
    } catch (error) { submit.disabled = false; return fail(fi, 'email', error.message); }
    submit.disabled = false;
    $$('[data-uname]').forEach(x => { x.textContent = name; }); $$('[data-ufirst]').forEach(x => { x.textContent = v('first'); });
    $$('[data-uemail]').forEach(x => { x.textContent = v('email') || cc + ' ' + v('phone'); });
    $$('[data-uinit]').forEach(x => { x.textContent = (v('first')[0] + (v('last')[0] || '')).toUpperCase(); });
    avBtn.setAttribute('aria-label', 'Your account, ' + name);
    say('Changes saved'); });
  $('[data-cancel]', fi).addEventListener('click', () => { fi.reset(); okf(fi); $('.cc-c', fi).textContent = '+91'; });
  const ccs = $('.cc select', fi), flag = $('.cc-f', fi).innerHTML;
  ccs.addEventListener('change', () => { const o = ccs.selectedOptions[0]; $('.cc-c', fi).textContent = ccs.value;
    $('.cc-f', fi).innerHTML = o.dataset.iso === 'IN' ? flag : `<span class="cc-iso">${o.dataset.iso}</span>`; });
  const fp = $('#f-pass');
  fp.addEventListener('submit', async e => { e.preventDefault(); okf(fp); const v = n => fp.elements[n].value;
    if (!v('cur')) return fail(fp, 'cur', 'Enter your current password.');
    if (v('new').length < 8) return fail(fp, 'new', 'Use at least 8 characters.');
    if (v('new') === v('cur')) return fail(fp, 'new', 'Choose a password you have not used here.');
    if (v('rep') !== v('new')) return fail(fp, 'rep', 'The two new passwords do not match.');
    const submit = fp.querySelector('[type="submit"]'); submit.disabled = true;
    try {
      await api('/auth/login', { method: 'POST', auth: false, body: { username: account.username, password: v('cur') } });
      await api('/users/' + account.id, { method: 'PUT', body: { password: v('new') } });
    } catch (error) { submit.disabled = false; return fail(fp, 'cur', error.status === 401 ? 'Your current password is incorrect.' : error.message); }
    submit.disabled = false;
    fp.reset(); $$('.eye', fp).forEach(b => { b.setAttribute('aria-pressed', 'false'); b.setAttribute('aria-label', 'Show password'); }); say('Password changed'); });
  $('[data-cancel]', fp).addEventListener('click', () => { fp.reset(); okf(fp); });
  document.addEventListener('click', e => { const b = e.target.closest('.eye'); if (!b) return; const i = b.parentElement.querySelector('input'), on = b.getAttribute('aria-pressed') !== 'true';
    i.type = on ? 'text' : 'password'; b.setAttribute('aria-pressed', String(on)); b.setAttribute('aria-label', on ? 'Hide password' : 'Show password'); });

  function hydrateAccount() {
    const name = account.name || account.username;
    const first = account.profile?.first || name.split(' ')[0];
    const parts = name.trim().split(/\s+/);
    $$('[data-uname]').forEach(x => { x.textContent = name; });
    $$('[data-ufirst]').forEach(x => { x.textContent = first; });
    $$('[data-uemail]').forEach(x => { x.textContent = account.email || account.username; });
    $$('[data-uinit]').forEach(x => { x.textContent = parts.slice(0,2).map(p => p[0]).join('').toUpperCase(); });
    avBtn.setAttribute('aria-label', 'Your account, ' + name);
    for (const input of fi.elements) {
      if (!input.name) continue;
      input.value = account.profile?.[input.name] || (input.name === 'first' ? first : input.name === 'last' ? parts.slice(1).join(' ') : input.name === 'email' ? account.email || '' : '');
    }
    const country = $('.cc select', fi); if (!country.value) country.value = '+91';
    $('.cc-c', fi).textContent = country.value;
  }
  hydrateAccount();
  if (account.isAdmin && import.meta.env.VITE_INCLUDE_ADMIN !== 'false') {
    const link = document.createElement('a');
    link.className = 'um-i';
    link.href = '/admin/';
    link.innerHTML = '<svg aria-hidden="true" fill="none" height="20" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="1.6" viewBox="0 0 24 24" width="20"><path d="M4 20V4h16v16M8 8h8M8 12h8M8 16h5"/></svg>Admin workspace';
    $('#um').insertBefore(link, $('#um .sd-hr'));
  }
  $('[data-cancel]', fi).addEventListener('click', hydrateAccount);
  document.addEventListener('click', e => {
    if (e.target.closest('[data-signout]')) { e.preventDefault(); signout(); }
    if (e.target.closest('[data-upgrade]')) { e.preventDefault(); location.assign('/#pricing'); }
    const save = e.target.closest('[data-save]');
    if (save) {
      const message = save.closest('.msg'), key = 'cv-saved:' + account.id;
      const saved = JSON.parse(localStorage.getItem(key) || '{}');
      if (saved[message.dataset.messageId]) delete saved[message.dataset.messageId];
      else saved[message.dataset.messageId] = { text: message.querySelector('.ans').textContent, conversationId: currentChatId };
      localStorage.setItem(key, JSON.stringify(saved));
      save.setAttribute('aria-pressed', String(!!saved[message.dataset.messageId]));
      say(saved[message.dataset.messageId] ? 'Answer saved on this device' : 'Saved answer removed');
    }
  });
  document.addEventListener('click', event => {
    const action = event.target.closest('[data-rename],[data-delete]');
    if (!action) return;
    const remove = action.hasAttribute('data-delete');
    const id = action.dataset.delete || action.dataset.rename;
    const chat = CHATS.find(c => c.k === id); if (!chat) return;
    const dialog = document.createElement('dialog'); dialog.className = 'cv-notice';
    const heading = document.createElement('h2'); heading.textContent = remove ? 'Delete this chat?' : 'Rename chat';
    const form = document.createElement('form');
    const input = document.createElement(remove ? 'p' : 'input');
    if (remove) input.textContent = chat.t;
    else { input.value = chat.t; input.required = true; input.maxLength = 120; input.setAttribute('aria-label', 'Chat title'); input.className = 'cv-rename'; }
    const controls = document.createElement('div'); controls.className = 'btns';
    const cancel = document.createElement('button'); cancel.type = 'button'; cancel.className = 'btn btn-panel'; cancel.textContent = 'Cancel'; cancel.onclick = () => dialog.close();
    const submit = document.createElement('button'); submit.type = 'submit'; submit.className = 'btn btn-gold'; submit.textContent = remove ? 'Delete chat' : 'Save';
    controls.append(cancel, submit); form.append(input, controls); dialog.append(heading, form); document.body.append(dialog); dialog.showModal();
    dialog.addEventListener('close', () => { dialog.remove(); action.focus(); }, { once: true });
    form.addEventListener('submit', async e => {
      e.preventDefault(); submit.disabled = true;
      try {
        if (remove) {
          await api('/conversations/' + id, { method: 'DELETE' });
          CHATS.splice(CHATS.indexOf(chat), 1); if (currentChatId === id) fresh();
        } else {
          const next = input.value.trim(); if (!next) { input.focus(); submit.disabled = false; return; }
          await api('/conversations/' + id, { method: 'PUT', body: { title: next } });
          chat.t = next; if (currentChatId === id) title(next);
        }
        renderSidebar(); renderChats(); dialog.close(); say(remove ? 'Chat deleted' : 'Chat renamed');
      } catch (error) { submit.disabled = false; say(error.message); }
    });
  });
  if (initialError) say(initialError);
  // start where the link points: #new, #chat/car, #chats, #proj, #profile, #subs
  const MAP = { workspace: 'chats', projects: 'proj', home: 'new', ask: 'new' };
  let [hv, hs] = location.hash.slice(1).split('/'); if (hv === 'settings') { hv = 'profile'; hs = 'mode'; } hv = MAP[hv] || hv;
  sync();
  if (hv === 'chat' && hs && hs !== 'new') openChat(hs); else if (VIEWS.includes(hv) && hv !== 'ask') go(hv, hs); else fresh();
})();
