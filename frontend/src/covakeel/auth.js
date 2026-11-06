import { login, register } from './api.js';
/* CoVakeel sign up and sign in · 1 Nov 2026 · final · same code as website/index.html.
   Search for "demo" to find each step waiting for the real call (Google, send code, check code). */
/* CoVakeel sign up and sign in. Each .ascope (the hero, the popup) runs its own copy of the flow.
   Steps marked "demo" are where the real calls go: Google, send code, check code. */
window.cvAuth = (root) => {
  if (root._cv) return root._cv;
  const $ = (s, el = root) => el.querySelector(s), $$ = (s, el = root) => [...el.querySelectorAll(s)];
  const panels = $$('[data-af]');
  const boxes = $$('.otp input'), st = $('.otp-st'), re = $('.otp-re'), sec = $('[data-sec]'), to = $('[data-to]');
  let from = 'phone', tick = null;
  const clear = () => { $$('.af-err').forEach(x => { x.hidden = true; }); $$('.fld.bad').forEach(x => x.classList.remove('bad')); };
  const show = (s, focus = true) => {
    clear();
    panels.forEach(p => { const on = p.dataset.af === s; p.hidden = !on; p.classList.remove('up');  // the hero intro plays once only
      if (on && focus) { p.classList.remove('af-in'); void p.offsetWidth; p.classList.add('af-in'); } });
    if (s === 'otp') { boxes.forEach(b => { b.value = ''; b.disabled = false; }); st.hidden = true; st.classList.remove('done'); countdown(); }
    if (focus) { const f = $(`[data-af="${s}"] input:not([disabled])`) || $(`[data-af="${s}"] a, [data-af="${s}"] button`);
      if (f && f.offsetParent) f.focus({ preventScroll: s === 'choose' }); }
    dispatchEvent(new Event('resize'));
  };
  const countdown = (n = 60) => { clearInterval(tick); re.disabled = true; re.classList.remove('ready'); sec.textContent = n;
    tick = setInterval(() => { n -= 1; sec.textContent = n; if (n <= 0) { clearInterval(tick); re.disabled = false; re.classList.add('ready'); } }, 1000); };
  const fmt = d => d.length === 10 ? d.slice(0, 5) + ' ' + d.slice(5) : d;
  const signin = () => root.classList.contains('signin');
  const busy = (f, on) => { f.classList.toggle('busy', on); $$('input,select,button', f).forEach(x => x.disabled = on); };
  function check(f) {
    const k = f.dataset.kind, v = n => (f.elements[n] ? f.elements[n].value.trim() : '');
    const bad = (n, m) => { const i = f.elements[n]; if (i) { i.closest('.fld').classList.add('bad'); i.focus(); } return m; };
    $$('.fld.bad', f).forEach(x => x.classList.remove('bad'));
    if (!signin() && v('name').length < 2) return bad('name', 'Please enter your name.');
    if (k === 'email') {
      if (!signin() && !/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(v('email'))) return bad('email', 'Please enter a valid email address.');
      if (signin() && !v('email')) return bad('email', 'Enter your email or username.');
      if ((!signin() && v('password').length < 8) || (signin() && !v('password'))) return bad('password', signin() ? 'Enter your password.' : 'Your password needs at least 8 characters.');
    } else {
      const d = v('phone').replace(/\D/g, ''), cc = $('select', f).value;
      if (cc === '+91' ? d.length !== 10 : (d.length < 6 || d.length > 12)) return bad('phone', cc === '+91' ? 'Please enter your 10 digit mobile number.' : 'Please enter a valid mobile number.');
    }
    return '';
  }
  $$('form.af-form').forEach(f => {
    const err = $('.af-err', f);
    f.addEventListener('input', e => { const fl = e.target.closest('.fld'); if (fl) fl.classList.remove('bad'); err.hidden = true; });
    f.addEventListener('submit', async e => { e.preventDefault(); const m = check(f);
      if (m) { err.textContent = m; err.hidden = false; return; }
      if (f.dataset.kind === 'phone') {
        err.textContent = 'Phone sign in is not available yet. Please continue with email.';
        err.hidden = false; return;
      }
      err.hidden = true; busy(f, true);
      try {
        const email = f.elements.email.value.trim(), password = f.elements.password.value;
        if (signin()) await login(email, password);
        else await register(f.elements.name.value, email, password);
        location.assign('/app/#new');
      } catch (error) {
        err.textContent = error.status === 401 ? 'Email or password is incorrect.' : error.message;
        err.hidden = false;
      } finally { busy(f, false); }
    });
  });
  const pw = $('[name="password"]');
  root.addEventListener('click', e => {
    const a = e.target.closest('a[href="#email"],a[href="#phone"],a[href="#google"],[data-go],[data-mode],[data-edit],.eye,.otp-re');
    if (!a || !root.contains(a)) return;
    if (a.matches('a[href="#google"]')) { e.preventDefault(); show('email'); const er = $('[data-kind="email"] .af-err'); er.textContent = 'Google sign in is not available yet. Please continue with email.'; er.hidden = false; return; }  // demo: start Google sign in here
    if (a.matches('a[href="#email"],a[href="#phone"]')) { e.preventDefault(); show(a.hash.slice(1)); return; }
    if (a.matches('[data-go]')) { show(a.dataset.go); return; }
    if (a.matches('[data-mode]')) { clear(); root.classList.toggle('signin'); if (pw) pw.autocomplete = signin() ? 'current-password' : 'new-password';
      const emailInput = $('[name="email"]'); if (emailInput) { emailInput.type = signin() ? 'text' : 'email'; emailInput.placeholder = signin() ? 'Email or username' : 'Enter your email'; }
      const vis = panels.find(p => !p.hidden); const f = vis && $('input:not([disabled])', vis); if (f && f.offsetParent) f.focus(); return; }
    if (a.matches('[data-edit]')) { clearInterval(tick); show(from); return; }
    if (a.matches('.eye')) { const on = a.getAttribute('aria-pressed') !== 'true'; a.setAttribute('aria-pressed', String(on));
      a.setAttribute('aria-label', on ? 'Hide password' : 'Show password'); pw.type = on ? 'text' : 'password'; return; }
    if (a.matches('.otp-re')) { show('otp'); }  // demo: send the code again here
  });
  // country code
  const sel = $('.cc select');
  if (sel) { const flag = $('.cc-f').innerHTML;
    sel.addEventListener('change', () => { const o = sel.selectedOptions[0];
      $('.cc-c').textContent = sel.value; $('.cc-f').innerHTML = o.dataset.iso === 'IN' ? flag : `<span class="cc-iso">${o.dataset.iso}</span>`; }); }
  // six code boxes: type, paste, autofill, backspace, arrows
  const done = () => { if (!boxes.every(b => /^\d$/.test(b.value))) return;
    boxes.forEach(b => { b.disabled = true; }); st.hidden = false; st.classList.remove('done');
    st.textContent = 'Code sign in is not available yet. Please continue with email.'; };  // demo: check the code here, then open CoVakeel
  const fill = (i, s) => { [...s].slice(0, 6 - i).forEach((d, k) => { boxes[i + k].value = d; }); boxes[Math.min(i + s.length, 5)].focus(); done(); };
  boxes.forEach((b, i) => {
    b.addEventListener('input', () => { const d = b.value.replace(/\D/g, '');
      if (d.length > 1) { fill(i, d); return; } b.value = d; if (d && i < 5) boxes[i + 1].focus(); done(); });
    b.addEventListener('keydown', e => {
      if (e.key === 'Backspace' && !b.value && i > 0) { e.preventDefault(); boxes[i - 1].value = ''; boxes[i - 1].focus(); }
      else if (e.key === 'ArrowLeft' && i > 0) { e.preventDefault(); boxes[i - 1].focus(); }
      else if (e.key === 'ArrowRight' && i < 5) { e.preventDefault(); boxes[i + 1].focus(); } });
    b.addEventListener('paste', e => { const d = (e.clipboardData || window.clipboardData).getData('text').replace(/\D/g, '');
      if (d) { e.preventDefault(); fill(0, d.slice(0, 6)); } });
    b.addEventListener('focus', () => b.select());
  });
  return (root._cv = { show, busy, root });
};
document.querySelectorAll('.ascope').forEach(r => window.cvAuth(r));
/* popup: every link to #signup opens it (header Get Started, plan buttons) */
(() => {
  const M = document.getElementById('signup-modal'); if (!M) return;
  const card = M.querySelector('.am-card'), api = window.cvAuth(card); let last = null;
  const open = () => { last = document.activeElement; card.classList.remove('signin'); api.show('choose', false);
    M.hidden = false; document.documentElement.classList.add('m-open'); requestAnimationFrame(() => M.classList.add('on')); card.focus({ preventScroll: true }); };
  const close = () => { M.classList.remove('on'); document.documentElement.classList.remove('m-open');
    setTimeout(() => { M.hidden = true; }, 220); if (last && last.focus) last.focus({ preventScroll: true }); };
  document.addEventListener('click', e => { const a = e.target.closest('a[href="#signup"]'); if (a) { e.preventDefault(); open(); } });
  M.addEventListener('click', e => { if (e.target === M || e.target.closest('.am-x')) close(); });
  document.addEventListener('keydown', e => { if (M.hidden) return;
    if (e.key === 'Escape') { close(); return; }
    if (e.key === 'Tab') { const f = [...card.querySelectorAll('a[href],button:not([disabled]),input:not([disabled]),select:not([disabled])')].filter(x => x.offsetParent);
      if (!f.length) return; const a = f[0], z = f[f.length - 1];
      if (e.shiftKey && (document.activeElement === a || document.activeElement === card)) { e.preventDefault(); z.focus(); }
      else if (!e.shiftKey && document.activeElement === z) { e.preventDefault(); a.focus(); } } });
})();
