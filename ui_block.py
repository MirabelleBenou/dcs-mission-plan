#!/usr/bin/env python3
"""Bloc « INTERFACE COMMUNE » : la fenêtre de suite, la confirmation, le geste « Remplacer », les notes, la couleur d'avertissement,
le repli et l'export en une fenêtre, écrits une fois et injectés tels quels dans les six modules qui ont une interface à fenêtres
(HQ, Route Planner, Briefing Generator, Datacard Generator, Flight Configurator, Recon Station).

Deux textes, identiques à l'octet dans les six dist/ :
  build_css()   — la feuille : --mp-warn, .ui-modal / .ui-panel (la fenêtre de suite), .ui-btn, .ui-note / .ui-avert / .ui-bandeau,
                  .ui-fold-head / .ui-sum (le repli), .ui-seg (boutons segmentés), les champs de la fenêtre d'export
  build_block() — le script : askConfirm, replaceWithRestore, le piège du focus et Échap des fenêtres, l'état du repli (uiFold*),
                  la fenêtre d'export (uiExport*)

Le bloc ne dépend que des variables de thème communes (--olive-dark, --amber, --khaki, --khaki-light, --paper, --green-radar,
--f-stencil, --f-ui, --f-typewriter), de t() du module (clés ui.cancel, ui.close, ui.restore, ui.foldall, ui.unfoldall, ui.fmt,
ui.pages, ui.fname, ui.export, ui.all) et de showToast() du bloc de messages (messages_block.py).

Usage (par les builds) : from ui_block import build_block, build_css, fingerprint
"""
import hashlib

BLOCK_BEGIN = '/* ===== INTERFACE COMMUNE (fenêtre, confirmation, repli, notes) ===== */'
BLOCK_END = '/* ===== FIN DE L\'INTERFACE COMMUNE ===== */'
CSS_BEGIN = '/* ===== INTERFACE COMMUNE : feuille ===== */'
CSS_END = '/* ===== FIN DE LA FEUILLE DE L\'INTERFACE COMMUNE ===== */'

_CSS = r"""
:root { --mp-warn: #e8806a; }

/* ---- la fenêtre de suite ---- */
.ui-modal[hidden] { display: none !important; }
.ui-modal { position: fixed; inset: 0; z-index: 10000; display: flex; align-items: center; justify-content: center; padding: 16px; box-sizing: border-box; }
#ui-confirm { z-index: 10500; }
.ui-backdrop { position: absolute; inset: 0; background: rgba(0,0,0,.55); }
.ui-panel {
  position: relative; box-sizing: border-box; width: 440px; max-width: calc(100vw - 24px); max-height: 90vh; max-height: 90dvh; overflow: auto;
  background: var(--olive-dark); color: var(--paper); border: 1px solid var(--amber); border-top: 3px solid var(--amber);
  padding: 18px 18px 16px; box-shadow: 0 8px 40px rgba(0,0,0,.6); font-family: var(--f-ui); font-weight: 500; text-align: left;
}
.ui-panel.ui-wide { width: 720px; }
.ui-panel > h2, .ui-title { margin: 0 44px 14px 0; font-family: var(--f-stencil); font-weight: 400; font-size: 16px; letter-spacing: 1.5px; text-transform: uppercase; color: var(--amber); line-height: 1.25; overflow-wrap: anywhere; }
.ui-close {
  position: absolute; top: 0; right: 0; width: 44px; height: 44px; padding: 0; background: none; border: 0; cursor: pointer;
  color: var(--paper); font-family: inherit; font-size: 22px; line-height: 1;
}
.ui-close:hover, .ui-close:focus-visible { color: var(--amber); }
.ui-actions { display: flex; flex-wrap: wrap; justify-content: flex-end; gap: 8px; margin-top: 14px; }
.ui-btn {
  box-sizing: border-box; display: inline-flex; align-items: center; justify-content: center; gap: 6px; min-height: 44px; padding: 0 16px;
  font-family: var(--f-ui); font-weight: 500; font-size: 12px; letter-spacing: 1.5px; text-transform: uppercase;
  background: rgba(0,0,0,.2); color: var(--paper-light); border: 1px solid var(--khaki); border-radius: 0; cursor: pointer;
}
.ui-btn:hover { background: var(--olive); border-color: var(--amber); color: var(--amber); }
.ui-btn.primary { border-color: var(--amber); color: var(--amber); }
.ui-btn.primary:hover { background: var(--amber-dark, var(--olive)); color: var(--paper-light); }
.ui-btn.danger, .ui-btn.primary.danger { background: var(--mp-warn); border-color: var(--mp-warn); color: #14110a; }
.ui-btn.danger:hover, .ui-btn.primary.danger:hover { background: var(--paper-light); border-color: var(--mp-warn); color: #14110a; }
.ui-btn:disabled { opacity: .4; cursor: default; }
.ui-btn:disabled:hover { background: rgba(0,0,0,.2); border-color: var(--khaki); color: var(--paper-light); }
.ui-btn.primary:disabled:hover { border-color: var(--amber); color: var(--amber); }
.ui-btn.danger:disabled:hover { background: var(--mp-warn); border-color: var(--mp-warn); color: #14110a; }
@media (max-width: 480px) { .ui-modal { padding: 8px; } .ui-panel { padding: 14px 14px 12px; } }
@media print { .ui-modal { display: none !important; } }

/* ---- les notes ---- */
.ui-note { margin: 0; font-family: 'Roboto Mono', 'Courier New', monospace; font-weight: 400; font-size: 11px; line-height: 1.4; color: var(--khaki-light); overflow-wrap: anywhere; }
.ui-avert { margin: 6px 0 0; font-family: 'Roboto Mono', 'Courier New', monospace; font-weight: 400; font-size: 11px; line-height: 1.4; color: var(--mp-warn); overflow-wrap: anywhere; }
.ui-bandeau {
  box-sizing: border-box; margin: 0 0 12px; padding: 7px 12px; font-family: 'Roboto Mono', 'Courier New', monospace; font-weight: 400; font-size: 12px; line-height: 1.4;
  color: var(--paper-light); background: var(--olive-dark); border: 1px solid var(--khaki); border-left: 3px solid var(--khaki); overflow-wrap: anywhere;
}
.ui-bandeau.ok { border-left-color: var(--green-radar); color: var(--paper); }
.ui-bandeau.err { border-left-color: var(--mp-warn); color: var(--paper); }
#ui-confirm .ui-note { white-space: pre-line; font-size: 12px; margin: 0 0 4px; }

/* ---- le repli : un triangle plein à la couleur du module (--mp-accent), à gauche du titre ; tout l'en-tête est la cible ---- */
.ui-fold-head { display: flex; flex-wrap: wrap; align-items: center; justify-content: flex-start; min-height: 44px; box-sizing: border-box; cursor: pointer; list-style: none; user-select: none; }
.ui-fold-head::-webkit-details-marker { display: none; }
.ui-fold-head::before {
  content: ''; flex: none; width: 0; height: 0; margin: 0 14px 0 0; border-left: 7px solid var(--mp-accent, var(--amber));
  border-top: 5px solid transparent; border-bottom: 5px solid transparent; transition: transform .2s;
}
details[open] > .ui-fold-head::before, .ui-fold-head[aria-expanded="true"]::before { transform: rotate(90deg); }
.ui-sum {
  display: none; flex: 0 0 100%; box-sizing: border-box; min-width: 0; max-width: 100%; margin: -6px 0 8px; padding-left: 21px;
  font-family: 'Roboto Mono', 'Courier New', monospace; font-weight: 400; font-size: 12px; line-height: 1.4; letter-spacing: 0; text-transform: none; text-align: left;
  color: var(--khaki-light); white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
details:not([open]) > .ui-fold-head > .ui-sum:not(:empty), .ui-fold-head[aria-expanded="false"] > .ui-sum:not(:empty) { display: block; }
.ui-foldall { min-height: 44px; padding: 0 12px; font-size: 11px; white-space: nowrap; }
.ui-foldbar { display: flex; justify-content: flex-end; margin: 0 0 10px; }

/* ---- boutons segmentés et champs de la fenêtre d'export ---- */
.ui-field { margin: 0 0 14px; }
.ui-lbl { display: block; margin: 0 0 5px; font-family: var(--f-ui); font-weight: 500; font-size: 11px; letter-spacing: 1.8px; text-transform: uppercase; color: var(--amber); }
.ui-seg { display: flex; flex-wrap: wrap; margin: 0 0 6px; }
.ui-seg-btn {
  box-sizing: border-box; min-height: 44px; min-width: 56px; padding: 0 16px; margin: 0 -1px 0 0; font-family: var(--f-ui); font-weight: 500; font-size: 12px; letter-spacing: 1.5px; text-transform: uppercase;
  background: rgba(0,0,0,.2); color: var(--paper-light); border: 1px solid var(--khaki); border-radius: 0; cursor: pointer;
}
.ui-seg-btn:hover { background: var(--olive); color: var(--amber); }
.ui-seg-btn[aria-pressed="true"] { background: var(--amber-dark, var(--olive)); color: var(--paper-light); border-color: var(--amber); box-shadow: inset 0 -3px 0 var(--amber); position: relative; }
.ui-seg-btn:focus-visible { position: relative; }
.ui-seg-btn:disabled { opacity: .4; cursor: default; }
.ui-row { display: flex; align-items: center; gap: 8px; }
.ui-in {
  flex: 1 1 auto; min-width: 0; box-sizing: border-box; min-height: 44px; padding: 10px 11px; background: rgba(216,201,165,.92); border: 1px solid var(--khaki); border-left: 3px solid var(--amber-dark, var(--amber));
  font-family: 'Roboto Mono', 'Courier New', monospace; font-weight: 400; font-size: 13px; color: #1a1710; border-radius: 0;
}
.ui-in:focus { background: var(--paper-light); box-shadow: 0 0 0 1px var(--amber); }
.ui-ext { flex: none; font-family: 'Roboto Mono', 'Courier New', monospace; font-weight: 400; font-size: 13px; color: var(--khaki-light); }
.ui-pick { margin: 6px 0 0; }
.ui-pick[hidden] { display: none; }
@media print { .ui-print-hide { display: none !important; } }

/* ---- le focus visible (la même règle dans toute la suite) : un contour plein de 2 px à la couleur --amber, décalé de 2 px ; le focus à la souris ne change pas ---- */
button:focus-visible, select:focus-visible, input:focus-visible, textarea:focus-visible, summary:focus-visible, a[href]:focus-visible, [tabindex]:focus-visible, [role="button"]:focus-visible {
  outline: 2px solid var(--amber) !important; outline-offset: 2px !important;
}

/* ---- la barre : 60 px, des cibles de 44 px au moins, le texte des boutons en Oswald 700, le drapeau en Roboto Mono 400 ---- */
.toolbar { height: 60px; }
.toolbar .tb-btn, .toolbar .tb-sel, .toolbar .tb-select, .toolbar .tbm-trigger, .toolbar .tb-lang-btn, .toolbar .seg-btn, .toolbar .mp-back-injected {
  box-sizing: border-box; min-width: 44px !important; min-height: 44px !important;
}
.toolbar .tb-btn, .toolbar .tb-sel, .toolbar .tb-select, .toolbar .tbm-trigger, .toolbar .seg-btn { font-family: var(--f-ui); font-weight: 700; }
.toolbar .tb-lang-btn { font-family: 'Roboto Mono', 'Courier New', monospace; font-weight: 400; }
.toolbar .tb-seg { height: auto; min-height: 44px; }
/* dans la suite, le module laisse le thème à l'accueil : sa liste de thème n'est pas là (le drapeau reste) */
html.mp-in-shell #theme-select, html.mp-in-shell #theme, html.mp-in-shell [aria-controls="tbm-list-theme-select"], html.mp-in-shell [aria-controls="tbm-list-theme"] { display: none !important; }
/* MP-20 begin */
/* Contrastes (texte sous 18 px, 4,5 : 1 au moins) : couleur du texte seule, la palette commune ne bouge pas. */
:where(body[data-theme="cw-nato"]) .ui-lbl { color: #c49037; }
:where(body[data-theme="cw-nato"]) .toast-action { color: #c49037; }
:where(body[data-theme="cw-nato"]) .ui-note { color: #ab9e78; }
:where(body[data-theme="cw-nato"]) .ui-sum { color: #cbc2aa; }
:where(body[data-theme="cw-nato"]) .ui-panel > h2 { color: #c49037; }
:where(body[data-theme="cw-nato"]) .ui-title { color: #c49037; }
:where(body[data-theme="cw-soviet"]) .ui-note { color: #95a08a; }
:where(body[data-theme="cw-soviet"]) .ui-ext { color: #879279; }
:where(body[data-theme="cw-soviet"]) .ui-sum { color: #9fa995; }
:where(body[data-theme="modern-nato"]) .ui-note { color: #8e9ca7; }
:where(body[data-theme="modern-nato"]) .ui-sum { color: #929fab; }
:where(body[data-theme="modern-east"]) .ui-note { color: #989e8a; }
:where(body[data-theme="modern-east"]) .ui-ext { color: #888e78; }
:where(body[data-theme="modern-east"]) .ui-sum { color: #9da28f; }
/* MP-20 end */
"""

_JS = r"""
/* ---- dans la suite : le module le sait par window.self !== window.top, à son démarrage ---- */
try { if (window.self !== window.top) document.documentElement.classList.add('mp-in-shell'); } catch (e) { document.documentElement.classList.add('mp-in-shell'); }

/* ---- la liste de thème suit le thème appliqué (le shell pousse data-theme sur le body du module) ---- */
(function uiThemeFollow() {
  const sync = () => {
    const th = document.body && document.body.getAttribute('data-theme');
    const s = document.getElementById('theme-select') || document.getElementById('theme');
    if (th && s && s.value !== th) s.value = th;
  };
  const go = () => { sync(); new MutationObserver(sync).observe(document.body, { attributes: true, attributeFilter: ['data-theme'] }); };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', go); else go();
})();

const UIK = { cf: null, top: null, restore: null, ex: null };
function uiT(key, fb) { let v; try { v = t(key); } catch (e) { v = key; } return (v === undefined || v === key) ? (fb !== undefined ? fb : key) : v; }

/* ---- la fenêtre de suite : Échap (= ✕ = Annuler) et le piège du focus, pour la fenêtre du dessus ---- */
function uiModalsOpen() { return Array.prototype.filter.call(document.querySelectorAll('.ui-modal'), m => !m.hidden); }
function uiTopModal() { const c = document.getElementById('ui-confirm'); if (c && !c.hidden) return c; const l = uiModalsOpen(); return l.length ? l[l.length - 1] : null; }
function uiFocusables(m) {
  return Array.prototype.filter.call(m.querySelectorAll('button, input, select, textarea, a[href], [tabindex]'), e =>
    !e.disabled && !e.hidden && e.type !== 'hidden' && e.tabIndex >= 0 && e.getClientRects().length > 0);
}
window.addEventListener('keydown', () => { UIK.top = uiTopModal(); }, true);
window.addEventListener('keydown', e => {
  const m = UIK.top; UIK.top = null;
  if (!m || m.hidden || e.defaultPrevented) return;
  if (e.key === 'Escape') {
    const x = m.querySelector('.ui-close');
    if (x) { e.preventDefault(); x.click(); }
  } else if (e.key === 'Tab') {
    const els = uiFocusables(m);
    if (!els.length) return;
    const first = els[0], last = els[els.length - 1], a = document.activeElement;
    if (e.shiftKey && (a === first || !m.contains(a))) { e.preventDefault(); last.focus(); }
    else if (!e.shiftKey && (a === last || !m.contains(a))) { e.preventDefault(); first.focus(); }
  }
});

/* ---- askConfirm({ title, text, verb, danger }) → promesse : true (le verbe) ou false (Annuler, ✕, Échap, fond) ---- */
function uiConfirmEl() {
  let m = document.getElementById('ui-confirm');
  if (m) return m;
  const mk = (tag, cls, id) => { const e = document.createElement(tag); if (cls) e.className = cls; if (id) e.id = id; return e; };
  m = mk('div', 'ui-modal', 'ui-confirm');
  m.hidden = true;
  m.setAttribute('role', 'dialog'); m.setAttribute('aria-modal', 'true'); m.setAttribute('aria-labelledby', 'ui-confirm-title');
  const bd = mk('div', 'ui-backdrop', 'ui-confirm-backdrop');
  const p = mk('div', 'ui-panel'); p.setAttribute('role', 'document');
  const x = mk('button', 'ui-close', 'ui-confirm-close'); x.type = 'button'; x.textContent = '×';
  const h = mk('h2', 'ui-title', 'ui-confirm-title');
  const tx = mk('p', 'ui-note', 'ui-confirm-text');
  const ac = mk('div', 'ui-actions');
  const no = mk('button', 'ui-btn', 'ui-confirm-cancel'); no.type = 'button';
  const ok = mk('button', 'ui-btn primary', 'ui-confirm-ok'); ok.type = 'button';
  ac.appendChild(no); ac.appendChild(ok);
  p.appendChild(x); p.appendChild(h); p.appendChild(tx); p.appendChild(ac);
  m.appendChild(bd); m.appendChild(p);
  (document.body || document.documentElement).appendChild(m);
  const end = v => { if (UIK.cf) UIK.cf.done(v); };
  x.addEventListener('click', () => end(false));
  no.addEventListener('click', () => end(false));
  ok.addEventListener('click', () => end(true));
  bd.addEventListener('click', e => { if (e.detail >= 2 && UIK.cf && performance.now() - UIK.cf.at < 400) return; end(false); });
  return m;
}
function askConfirm(o) {
  o = o || {};
  if (UIK.cf) UIK.cf.done(false);                      /* une seule question à la fois */
  const m = uiConfirmEl();
  const opener = document.activeElement;
  const $ = id => document.getElementById(id);
  $('ui-confirm-title').textContent = o.title || '';
  const tx = $('ui-confirm-text');
  tx.textContent = o.text || ''; tx.hidden = !o.text;
  $('ui-confirm-close').setAttribute('aria-label', uiT('ui.close'));
  $('ui-confirm-cancel').textContent = uiT('ui.cancel');
  const ok = $('ui-confirm-ok');
  ok.textContent = o.verb || 'OK';
  ok.className = 'ui-btn primary' + (o.danger ? ' danger' : '');
  return new Promise(resolve => {
    UIK.cf = {
      at: performance.now(),
      done: v => {
        UIK.cf = null; m.hidden = true;
        if (opener && opener.focus && opener.isConnected && !opener.disabled) { try { opener.focus({ preventScroll: true }); } catch (e) { /* ignore */ } }
        resolve(!!v);
      }
    };
    m.hidden = false;
    (o.danger ? $('ui-confirm-cancel') : ok).focus({ preventScroll: true });
  });
}

/* ---- le geste « Remplacer » : on fait, on garde l'ancien, un toast à action « Restaurer » 12 s ----
   o.keys : les clés de localStorage que l'action écrit ; o.mem() : copie de l'état en mémoire ; o.back(copie) : remet l'état et redessine ;
   o.run() : l'action (rend false si rien n'a changé ; peut rendre une promesse) ; o.msg : la phrase du résultat, sans « · » (ou une fonction qui la rend, une fois l'action faite). Un second remplacement efface la copie du premier. */
function replaceWithRestore(o) {
  /* Tant que le toast « Restaurer » d'un premier remplacement est à l'écran, un second garde la copie du premier (et relance le toast) : « Restaurer » rend l'état d'avant le premier geste.
     Le toast fermé ou expiré, la copie suivante remplace l'ancienne. Même geste = même fonction o.back (comparée par son texte : les gestes d'un module ont chacun la leur). */
  const prev = UIK.restore;
  const live = !!(prev && UIK.restoreN === showToast._n && mpToastEl().classList.contains('show') && prev.back && o.back && String(prev.back) === String(o.back));
  let snap;
  if (live) snap = prev;
  else {
    const mem = o.mem ? o.mem() : null;                 /* d'abord la copie en mémoire (un module peut y vider son écriture en attente), puis les clés */
    const ls = {};
    (o.keys || []).forEach(k => { try { ls[k] = localStorage.getItem(k); } catch (e) { ls[k] = null; } });
    snap = { ls: ls, mem: mem, back: o.back };
    UIK.restore = null;
  }
  const fin = r => {
    if (r === false) return false;
    UIK.restore = snap;
    showToast((typeof o.msg === 'function' ? o.msg() : o.msg) + ' ·', { action: { label: uiT('ui.restore'), fn: () => uiRestore(snap) }, ms: 12000 });
    UIK.restoreN = showToast._n;
    return true;
  };
  const r = o.run();
  return (r && typeof r.then === 'function') ? r.then(fin) : fin(r);
}
function uiRestoreKeys(snap) {
  Object.keys(snap.ls).forEach(k => { try { if (snap.ls[k] === null) localStorage.removeItem(k); else localStorage.setItem(k, snap.ls[k]); } catch (e) { /* ignore */ } });
}
function uiRestore(snap) {
  if (UIK.restore !== snap) return;
  UIK.restore = null;
  uiRestoreKeys(snap);
  try { if (snap.back) snap.back(snap.mem); } catch (e) { console.warn('[ui] restauration', e); }
  uiRestoreKeys(snap);                                /* le stockage redevient, à l'octet, celui d'avant le geste */
}

/* ---- le repli : l'état se garde par module (<module>_folds_v1 : { section: true (ouverte) | false (repliée) }) ---- */
function uiFoldRead(key) {
  try { const o = JSON.parse(localStorage.getItem(key)); return (o && typeof o === 'object' && !Array.isArray(o)) ? o : {}; } catch (e) { return {}; }
}
function uiFoldOpen(key, id, defOpen) { const o = uiFoldRead(key); return typeof o[id] === 'boolean' ? o[id] : !!defOpen; }
function uiFoldSave(key, id, open) {
  const o = uiFoldRead(key);
  o[id] = !!open;
  try { localStorage.setItem(key, JSON.stringify(o)); } catch (e) { /* ignore */ }
}
function uiFoldSaveAll(key, map) {
  const o = uiFoldRead(key);
  Object.keys(map).forEach(k => { o[k] = !!map[k]; });
  try { localStorage.setItem(key, JSON.stringify(o)); } catch (e) { /* ignore */ }
}
/* La ligne de résumé d'un en-tête replié : text vide = rien. */
function uiSum(head, text) {
  if (!head) return;
  let s = head.querySelector(':scope > .ui-sum');
  const v = (text === undefined || text === null) ? '' : String(text);
  if (!v) { if (s) s.remove(); return; }
  if (!s) { s = document.createElement('span'); s.className = 'ui-sum'; head.appendChild(s); }
  if (s.textContent !== v) s.textContent = v;
}
function uiFoldAllLabel(anyOpen) { return uiT(anyOpen ? 'ui.foldall' : 'ui.unfoldall'); }
function uiJoin(parts) { return parts.filter(p => p !== undefined && p !== null && String(p).trim() !== '').map(p => String(p).trim()).join(' · '); }

/* ---- la fenêtre d'export (BG, DG) : format, pages, nom du fichier ----
   cfg : modal (id de la fenêtre), title, note { pdf, png }, pages [{ id, label, dis }], page (le choix de départ), pick (élément montré sous les pages quand page === 'pick'),
         defName(fmt, page) → nom sans extension, ext(fmt, page) → '.pdf' | '.png' | '.zip', count(page) → nombre de pages choisies, clean(nom), go({ fmt, page, name }) */
function uiExportEl(id) { return document.getElementById(id); }
function uiExportBuild(cfg) {
  const m = uiExportEl(cfg.modal), body = m.querySelector('.ui-xbody');
  const mk = (tag, cls, id) => { const e = document.createElement(tag); if (cls) e.className = cls; if (id) e.id = id; return e; };
  body.textContent = '';
  const f1 = mk('div', 'ui-field');
  const l1 = mk('span', 'ui-lbl', 'export-fmt-lbl'); l1.textContent = uiT('ui.fmt');
  const s1 = mk('div', 'ui-seg'); s1.setAttribute('role', 'group'); s1.setAttribute('aria-labelledby', 'export-fmt-lbl');
  ['pdf', 'png'].forEach(v => {
    const b = mk('button', 'ui-seg-btn', 'export-fmt-' + v); b.type = 'button'; b.dataset.v = v; b.textContent = v.toUpperCase();
    b.addEventListener('click', () => { UIK.ex.fmt = v; uiExportSync(true); });
    s1.appendChild(b);
  });
  const n1 = mk('p', 'ui-note', 'export-fmt-note');
  f1.appendChild(l1); f1.appendChild(s1); f1.appendChild(n1);
  const f2 = mk('div', 'ui-field');
  const l2 = mk('span', 'ui-lbl', 'export-pg-lbl'); l2.textContent = uiT('ui.pages');
  const s2 = mk('div', 'ui-seg'); s2.setAttribute('role', 'group'); s2.setAttribute('aria-labelledby', 'export-pg-lbl');
  cfg.pages.forEach(p => {
    const b = mk('button', 'ui-seg-btn', 'export-pg-' + p.id); b.type = 'button'; b.dataset.v = p.id; b.textContent = p.label; if (p.dis) b.disabled = true;
    b.addEventListener('click', () => { UIK.ex.page = p.id; uiExportSync(true); });
    s2.appendChild(b);
  });
  f2.appendChild(l2); f2.appendChild(s2);
  if (cfg.pick) { const w = mk('div', 'ui-pick', 'export-pick'); w.appendChild(cfg.pick); f2.appendChild(w); }
  const f3 = mk('div', 'ui-field');
  const l3 = mk('label', 'ui-lbl'); l3.setAttribute('for', 'export-png-fname'); l3.textContent = uiT('ui.fname');
  const r3 = mk('div', 'ui-row');
  const inp = mk('input', 'ui-in', 'export-png-fname');
  inp.type = 'text'; inp.autocomplete = 'off'; inp.setAttribute('autocapitalize', 'off'); inp.spellcheck = false; inp.maxLength = 100;
  inp.addEventListener('input', () => { UIK.ex.name = inp.value; UIK.ex.edited = true; uiExportSync(false); });
  inp.addEventListener('keydown', e => { if (e.key === 'Enter') { e.preventDefault(); if (!e.repeat) uiExportGo(); } });
  const ext = mk('span', 'ui-ext', 'export-png-ext');
  r3.appendChild(inp); r3.appendChild(ext); f3.appendChild(l3); f3.appendChild(r3);
  const ac = mk('div', 'ui-actions');
  const no = mk('button', 'ui-btn', 'export-cancel'); no.type = 'button'; no.textContent = uiT('ui.cancel');
  no.addEventListener('click', uiExportClose);
  const go = mk('button', 'ui-btn primary', 'export-png-go'); go.type = 'button';
  const gl = mk('span', '', 'export-go-label'); gl.textContent = uiT('ui.export');
  const gc = mk('span', '', 'export-png-count');
  go.appendChild(gl); go.appendChild(gc);
  go.addEventListener('click', uiExportGo);
  ac.appendChild(no); ac.appendChild(go);
  body.appendChild(f1); body.appendChild(f2); body.appendChild(f3); body.appendChild(ac);
}
function uiExportSync(rename) {
  const x = UIK.ex; if (!x) return;
  const c = x.cfg, $ = id => document.getElementById(id);
  ['pdf', 'png'].forEach(v => $('export-fmt-' + v).setAttribute('aria-pressed', String(x.fmt === v)));
  c.pages.forEach(p => $('export-pg-' + p.id).setAttribute('aria-pressed', String(x.page === p.id)));
  $('export-fmt-note').textContent = c.note[x.fmt];
  const pk = $('export-pick'); if (pk) pk.hidden = x.page !== 'pick';
  const inp = $('export-png-fname');
  if (rename && !x.edited) { x.name = c.clean(c.defName(x.fmt, x.page)); inp.value = x.name; }
  $('export-png-ext').textContent = c.ext(x.fmt, x.page);
  const n = c.count(x.page);
  $('export-png-count').textContent = (x.fmt === 'png' && n > 1) ? ' (' + n + ')' : '';
  $('export-png-go').disabled = n === 0 || c.clean(x.name) === '' || x.busy;
}
function uiExportOpen(cfg) {
  const m = uiExportEl(cfg.modal);
  UIK.ex = { cfg: cfg, fmt: 'pdf', page: cfg.page || 'all', name: '', edited: false, busy: false, opener: document.activeElement, at: performance.now() };
  m.querySelector('.ui-title').textContent = cfg.title;
  m.querySelector('.ui-close').setAttribute('aria-label', uiT('ui.close'));
  uiExportBuild(cfg);
  uiExportSync(true);
  m.hidden = false;
  const go = document.getElementById('export-png-go');
  (go && !go.disabled ? go : document.getElementById('export-fmt-pdf')).focus({ preventScroll: true });       /* le bouton principal, comme toute fenêtre de suite */
}
/* Le module change ce que la fenêtre propose (cases cochées, pages) : elle se met à jour sans toucher au nom écrit à la main. */
function uiExportRefresh(rename) { if (UIK.ex) uiExportSync(rename !== false); }
function uiExportClose() {
  const x = UIK.ex; if (!x) return;
  const m = uiExportEl(x.cfg.modal);
  m.hidden = true;
  UIK.ex = null;
  const o = x.opener;
  if (o && o.focus && o.isConnected && !o.disabled) { try { o.focus({ preventScroll: true }); } catch (e) { /* ignore */ } }
}
function uiExportGo() {
  const x = UIK.ex; if (!x || x.busy) return;
  const c = x.cfg, name = c.clean(x.name);
  if (name === '' || c.count(x.page) === 0) return;
  c.go({ fmt: x.fmt, page: x.page, name: name });
}
function uiExportBusy(on) { if (UIK.ex) { UIK.ex.busy = !!on; document.getElementById('export-png-go').disabled = !!on || document.getElementById('export-png-go').disabled; if (!on) uiExportSync(false); } }
function uiExportBind(modalId) {
  const m = document.getElementById(modalId);
  m.querySelector('.ui-close').addEventListener('click', uiExportClose);
  m.querySelector('.ui-backdrop').addEventListener('click', e => { if (e.detail >= 2 && UIK.ex && performance.now() - UIK.ex.at < 400) return; uiExportClose(); });
}
/* Le PDF : le nom saisi devient le titre du document le temps de l'impression, les pages non choisies sont masquées (hide : les éléments à masquer ; last : la dernière page visible, qui reçoit .ui-print-last pour que le module n'y force pas de saut de page) ; puis tout revient. */
function uiPrintAs(name, hide, last) {
  const title = document.title, hidden = (hide || []).filter(Boolean);
  let done = false;
  const apply = () => { document.title = name; hidden.forEach(e => e.classList.add('ui-print-hide')); if (last) last.classList.add('ui-print-last'); };
  const undo = () => {
    if (done) return; done = true;
    window.removeEventListener('beforeprint', apply); window.removeEventListener('afterprint', undo);
    document.title = title; hidden.forEach(e => e.classList.remove('ui-print-hide')); if (last) last.classList.remove('ui-print-last');
  };
  window.addEventListener('beforeprint', apply);
  window.addEventListener('afterprint', undo);
  apply();
  setTimeout(() => { try { window.print(); } catch (e) { undo(); } }, 50);
}
"""


def build_block():
    """Le script du bloc, délimité par ses deux commentaires, terminé par un saut de ligne."""
    return BLOCK_BEGIN + _JS + BLOCK_END + '\n'


def build_css():
    """La feuille du bloc, délimitée par ses deux commentaires, terminée par un saut de ligne."""
    return CSS_BEGIN + _CSS + CSS_END + '\n'


def fingerprint():
    """L'empreinte du bloc (feuille puis script) : sha256, 16 premiers caractères."""
    return hashlib.sha256((build_css() + build_block()).encode('utf-8')).hexdigest()[:16]


def verify(html):
    """Garde-fou de build : le bloc (feuille et script) est dans le livrable, tel quel ; imprime l'empreinte."""
    if build_css() not in html or build_block() not in html:
        raise SystemExit("[ERREUR] bloc d'interface commun absent du livrable ou modifié")
    print("[OK] bloc d'interface commun inséré tel quel, empreinte %s" % fingerprint())


if __name__ == '__main__':
    print(f"[OK] bloc d'interface : script {len(build_block())} caractères, feuille {len(build_css())}, empreinte {fingerprint()}")
