#!/usr/bin/env python3
"""Bloc « INTERFACE COMMUNE » : la fenêtre de suite, la confirmation, le geste « Remplacer », les notes, la couleur d'avertissement,
le repli et l'export en une fenêtre, écrits une fois et injectés tels quels dans les six modules qui ont une interface à fenêtres
(HQ, Route Planner, Briefing Generator, Datacard Generator, Flight Configurator, Recon Station).

Quatre textes, identiques à l'octet dans les six dist/ (les deux derniers, la liste au thème de l'interface, y sont posés à la place où chaque module avait sa copie, @@TBM_CSS@@ et @@TBM_JS@@) :
  build_css()   — la feuille : --mp-warn, .ui-modal / .ui-panel (la fenêtre de suite), .ui-btn, .ui-note / .ui-avert / .ui-bandeau,
                  .ui-fold-head / .ui-sum (le repli), .ui-seg (boutons segmentés), les champs de la fenêtre d'export
  build_block() — le script : askConfirm, replaceWithRestore, le piège du focus et Échap des fenêtres, l'état du repli (uiFold*),
                  la fenêtre d'export (uiExport*)
  build_tbm_css() / build_tbm_block() — le composant des listes déroulantes au thème de l'interface (tbm* : le bouton qui remplace le <select> masqué, le panneau, la liste,
                  la recherche, le clavier, le placement au-dessus du clavier de l'écran) : une seule copie pour HQ, Route Planner, Briefing Generator, Datacard Generator,
                  Flight Configurator et Recon Station ; ce qui diffère d'un module à l'autre se règle par TBM.cfg (voir l'en-tête du script)

Le bloc ne dépend que des variables de thème communes (--olive-dark, --amber, --khaki, --khaki-light, --paper, --green-radar,
--f-stencil, --f-ui, --f-typewriter), de t() du module (clés ui.cancel, ui.close, ui.restore, ui.restore.refused, ui.foldall, ui.unfoldall, ui.fmt,
ui.pages, ui.fname, ui.export, ui.all, et f.search pour la recherche d'une liste) et de showToast() du bloc de messages (messages_block.py).

askConfirm({ title, text, verb, danger, cancel } : cancel, facultatif, est le libellé du bouton de renoncement (« Annuler » par défaut).

Usage (par les builds) : from ui_block import build_block, build_css, fingerprint
"""
import hashlib

BLOCK_BEGIN = '/* ===== INTERFACE COMMUNE (fenêtre, confirmation, repli, notes) ===== */'
BLOCK_END = '/* ===== FIN DE L\'INTERFACE COMMUNE ===== */'
CSS_BEGIN = '/* ===== INTERFACE COMMUNE : feuille ===== */'
CSS_END = '/* ===== FIN DE LA FEUILLE DE L\'INTERFACE COMMUNE ===== */'
TBM_BEGIN = '/* ===== LISTES AU THÈME DE L\'INTERFACE (tbm*) ===== */'
TBM_END = '/* ===== FIN DES LISTES AU THÈME DE L\'INTERFACE ===== */'
TBM_CSS_BEGIN = '/* ===== LISTES AU THÈME DE L\'INTERFACE : feuille ===== */'
TBM_CSS_END = '/* ===== FIN DE LA FEUILLE DES LISTES ===== */'

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
/* la fenêtre coupe ce qui déborde : le contour reste à l'intérieur de la croix */
.ui-close:focus-visible { outline-offset: -4px; }
/* le lien de la fenêtre d'import : même couleur de contour que le reste */
button.imp-link:focus-visible { outline-color: var(--amber); }
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
.ui-seg-btn[aria-pressed="true"] { background: var(--amber-dark, var(--olive)); color: #fff; border-color: var(--amber); box-shadow: inset 0 -3px 0 var(--amber); position: relative; }
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
button:focus-visible, select:focus-visible, input:focus-visible, textarea:focus-visible, summary:focus-visible,
a[href]:focus-visible, [tabindex]:focus-visible, [role="button"]:focus-visible {
  outline: 2px solid var(--amber); outline-offset: 2px;
}

/* ---- la barre : 60 px, des cibles de 44 px au moins, le texte des boutons en Oswald 700, le drapeau en Roboto Mono 400 ---- */
.toolbar { height: 60px; }
.toolbar .tb-btn, .toolbar .tb-sel, .toolbar .tb-select, .toolbar .tbm-trigger, .toolbar .tb-lang-btn, .toolbar .seg-btn, .toolbar .mp-back-injected {
  box-sizing: border-box; min-width: 44px !important; min-height: 44px !important;
}
.toolbar .tb-btn, .toolbar .tb-sel, .toolbar .tb-select, .toolbar .tbm-trigger, .toolbar .seg-btn { font-family: var(--f-ui); font-weight: 700; }
.toolbar .tb-lang-btn { font-family: 'Roboto Mono', 'Courier New', monospace; font-weight: 400; }
.toolbar .tb-seg { height: auto; min-height: 44px; }
/* le séparateur qui suit le groupe des fichiers : visible à toutes les largeurs (les modules masquent les leurs quand la barre se resserre) */
.toolbar > .tb-sep.tb-files-end { display: block; }
/* dans la suite, le module laisse le thème à l'accueil : sa liste de thème n'est pas là (le drapeau reste) */
html.mp-in-shell #theme-select, html.mp-in-shell #theme, html.mp-in-shell [aria-controls="tbm-list-theme-select"], html.mp-in-shell [aria-controls="tbm-list-theme"] { display: none !important; }
/* la barre qui manque de place se réduit dans un seul ordre, par la même règle « s'il tient » (uiBarFit, classes tb-st1 à tb-st4, cumulatives) : 1 le tampon de décor (et le tampon posé par le shell), 2 le numéro de version,
   3 le texte des boutons (icônes seules), 4 le titre long, qui passe au sigle court (titre et sous-titre masqués) ; aucun seuil de largeur propre à un outil ne retire plus rien de cela */
.toolbar.tb-fit, .toolbar.tb-fit * { transition: none !important; }
.toolbar.tb-st1 .tb-classif, .toolbar.tb-st1 .mp-wing-stamp { display: none; }
.toolbar.tb-st2 .tb-version { display: none; }
.toolbar.tb-st3 .tb-btn .tb-btn-label { display: none; }
.toolbar.tb-st3 .tb-btn { padding: 0 10px; width: auto; }
.toolbar.tb-st4 .tb-brand-main, .toolbar.tb-st4 .tb-brand-sub, .toolbar.tb-st4 .tb-brand + .tb-sep { display: none; }
.toolbar.tb-st4 .tb-brand-short { display: inline; }
/* la barre au téléphone : une seule règle de réduction, un seul seuil (sous 760 px, celui de la suite) pour tous les outils à barre. Le libellé d'une liste de la barre (« Théâtre ») est masqué (la liste garde son nom accessible) ;
   dans la suite, un bouton de réglage à texte et à icône (Affichage) n'a plus que l'icône (son infobulle et son nom accessible gardent son nom : uiBarDisplaySync) */
@media (max-width: 759px) {
  .toolbar .tb-label { display: none; }
  html.mp-in-shell #btn-display > span, html.mp-in-shell #btn-display > .dsp-chev { display: none; }
}
/* MP-20 begin */
/* Contrastes (texte sous 18 px, 4,5 : 1 au moins) : couleur du texte seule, la palette commune ne bouge pas. */
:where(body[data-theme="cw-nato"]) .ui-lbl { color: #c49037; }
:where(body[data-theme="cw-nato"]) .toast-action { color: #c49037; }
:where(body[data-theme="cw-nato"]) .toolbar .tb-select:not(:hover):not(:focus-visible) { color: #c49037; }   /* le libellé de la liste de thème, hors de la suite (au repos ; le survol garde sa couleur) */
/* au focus clavier, le libellé de la liste de thème (fond de survol) prend une couleur qui tient 4,5 : 1 dans les quatre thèmes */
.toolbar .tb-select:focus-visible, .toolbar .tb-sel:focus-visible { color: var(--paper-light); }
/* le bouton « Remise à zéro » du HQ et du BG : une seule couleur par thème (la plus claire des deux anciennes), la même dans les deux outils ; :not(:hover) pour que le survol garde la sienne */
:where(body[data-theme="cw-nato"]) .wing-action-reset:not(:hover) { color: #c17064; }
:where(body[data-theme="cw-soviet"]) .wing-action-reset:not(:hover) { color: #b27171; }
:where(body[data-theme="modern-nato"]) .wing-action-reset:not(:hover) { color: #818181; }
:where(body[data-theme="modern-east"]) .wing-action-reset:not(:hover) { color: #aa7373; }
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

/* ---- la barre : le même ordre à toutes les largeurs, écrit dans le HTML de chaque module (retour, sigle, .tb-lead s'il y en a un, les boutons de fichier .tb-file,
   le séparateur .tb-files-end, puis le reste) ; rien ne se déplace selon la largeur. Seul HQ déplace son « Wing » (.tb-lead tant que le wing n'est pas configuré), et pas selon la largeur.
   Ce qui suit ne sert qu'à raccourcir sans déplacer : la réduction de la barre est écrite une fois, dans la feuille (sous 760 px : libellé de liste masqué, Affichage à l'icône dans la suite) ;
   uiBarDisplaySync() tient l'infobulle et le nom accessible d'Affichage ; le passage de 760 px, dans les deux sens, est suivi sans rechargement (uiBarChanged() du module, s'il en a une). ---- */
const UIBAR = { mq: null };
/* ---- la réduction de la barre : une seule séquence. Elle part de l'état le plus complet et retire, tant que son contenu déborde (scrollWidth > clientWidth), l'étape suivante : 1 le tampon, 2 la version, 3 le texte des boutons, 4 le titre long.
   Elle s'arrête dès que tout tient. La décision se prend toujours en repartant de l'état complet (classes retirées, ainsi que le fondu du shell, mp-fade-r, sans transition le temps de la mesure) : elle ne dépend que de la largeur, de la langue et du contenu,
   jamais de l'état d'avant, donc pas de bascule en boucle ; une fenêtre plus étroite ne montre jamais plus. Sous 760 px, les quatre étapes sont toujours prises.
   Recalculée au chargement, après les polices, au redimensionnement, au changement de langue et quand le contenu de la barre change (un bouton, un tampon qui apparaît). ---- */
const UISTEPS = ['tb-st1', 'tb-st2', 'tb-st3', 'tb-st4'];
function uiBarStep(bar, k) { UISTEPS.forEach((c, i) => bar.classList.toggle(c, i < k)); }
function uiBarFit() {
  const bar = document.querySelector('.toolbar');
  if (!bar || !bar.clientWidth) return;                 /* un outil masqué (largeur nulle) garde son état */
  let k = 4;
  const fade = bar.classList.contains('mp-fade-r');
  bar.classList.add('tb-fit');                          /* sans transition le temps de la mesure : la largeur lue est celle de l'état final, jamais celle d'une animation en cours */
  if (!(window.matchMedia && window.matchMedia('(max-width: 759px)').matches)) {
    bar.classList.remove('mp-fade-r');
    for (k = 0; k < 4; k++) { uiBarStep(bar, k); if (bar.scrollWidth <= bar.clientWidth) break; }
    if (fade) bar.classList.add('mp-fade-r');
  }
  uiBarStep(bar, k);
  void bar.scrollWidth;                                 /* l'état final est calculé avant le retour des transitions : rien ne s'anime */
  bar.classList.remove('tb-fit');
}
function uiBarFitInit() {
  const bar = document.querySelector('.toolbar');
  if (!bar) return;
  let queued = false;
  const later = () => { if (queued) return; queued = true; Promise.resolve().then(() => { queued = false; uiBarFit(); }); };
  if (window.ResizeObserver) new ResizeObserver(later).observe(bar);
  window.addEventListener('resize', later);
  if (window.MutationObserver) new MutationObserver(rs => { if (rs.some(r => !(r.target === bar && r.attributeName === 'class'))) later(); })
    .observe(bar, { childList: true, subtree: true, characterData: true, attributes: true, attributeFilter: ['hidden', 'class', 'style', 'disabled'] });
  try { if (document.fonts) { document.fonts.ready.then(later); document.fonts.addEventListener('loadingdone', later); } } catch (e) { /* sans polices : les mesures suivent */ }
  uiBarFit();
}
if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', uiBarFitInit); else uiBarFitInit();
function uiBarCompact() { return document.documentElement.classList.contains('mp-in-shell') && !!UIBAR.mq && UIBAR.mq.matches; }
/* Affichage réduit à l'icône (sous 760 px, dans la suite) : l'infobulle et le nom accessible disent « Affichage » ; sinon, ceux du bouton entier (data-i18n-title, et data-i18n-aria-label s'il en a un) */
function uiBarDisplaySync() {
  const d = document.getElementById('btn-display'), lbl = d && d.querySelector(':scope > span');
  if (!d || !lbl) return;
  let title, aria;
  if (uiBarCompact()) { title = aria = lbl.textContent.trim(); }
  else {
    title = d.dataset.i18nTitle ? uiT(d.dataset.i18nTitle, d.title) : d.title;
    aria = d.dataset.i18nAriaLabel ? uiT(d.dataset.i18nAriaLabel, title) : null;
  }
  if (d.title !== title) d.title = title;
  if (aria === null) { if (d.hasAttribute('aria-label')) d.removeAttribute('aria-label'); }
  else if (d.getAttribute('aria-label') !== aria) d.setAttribute('aria-label', aria);
}
function uiBarInit() {
  if (UIBAR.mq || !window.matchMedia) return;
  UIBAR.mq = window.matchMedia('(max-width: 759px)');
  const dsp = document.getElementById('btn-display');
  if (dsp && window.MutationObserver) new MutationObserver(uiBarDisplaySync).observe(dsp, { attributes: true, attributeFilter: ['title', 'aria-label'], childList: true, characterData: true, subtree: true });
  const go = () => { uiBarDisplaySync(); try { if (typeof uiBarChanged === 'function') uiBarChanged(); } catch (e) { /* le module réagit au passage de 760 px */ } };
  if (UIBAR.mq.addEventListener) UIBAR.mq.addEventListener('change', go); else UIBAR.mq.addListener(go);
  go();
}
if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', uiBarInit); else uiBarInit();

const UIK = { cf: null, top: null, restore: null, ex: null };
function uiT(key, fb) { let v; try { v = t(key); } catch (e) { v = key; } return (v === undefined || v === key) ? (fb !== undefined ? fb : key) : v; }

/* ---- la fenêtre de suite : Échap (= croix = Annuler) et le piège du focus, pour la fenêtre du dessus ---- */
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

/* ---- askConfirm({ title, text, verb, danger, cancel }) → promesse : true (le verbe) ou false (le bouton de renoncement, la croix, Échap, le fond) ;
   cancel (facultatif) : le libellé du bouton de renoncement, « Annuler » (ui.cancel) s'il manque — dit à chaque appel, la fenêtre est resservie ---- */
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
  $('ui-confirm-cancel').textContent = o.cancel || uiT('ui.cancel');
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
    snap = { ls: ls, mem: mem, back: o.back, keys: (o.keys || []).slice(), after: null };
    UIK.restore = null;
  }
  const fin = r => {
    if (r === false) return false;
    snap.after = uiKeysNow(snap.keys);                  /* l'état écrit après le remplacement : « Restaurer » ne vaut que tant qu'il est encore là */
    UIK.restore = snap;
    showToast((typeof o.msg === 'function' ? o.msg() : o.msg) + ' ·', { action: { label: uiT('ui.restore'), fn: () => uiRestore(snap) }, ms: 12000 });
    UIK.restoreN = showToast._n;
    return true;
  };
  const r = o.run();
  return (r && typeof r.then === 'function') ? r.then(fin) : fin(r);
}
function uiKeysNow(keys) {
  const r = {};
  keys.forEach(k => { try { r[k] = localStorage.getItem(k); } catch (e) { r[k] = null; } });
  return r;
}
function uiRestoreKeys(snap) {
  Object.keys(snap.ls).forEach(k => { try { if (snap.ls[k] === null) localStorage.removeItem(k); else localStorage.setItem(k, snap.ls[k]); } catch (e) { /* ignore */ } });
}
function uiRestore(snap) {
  if (UIK.restore !== snap) return;
  UIK.restore = null;
  if (snap.after) {                                   /* une de ces clés a changé depuis (Tout effacer, un autre outil, un autre geste) : rien n'est écrit, rien ne revient */
    const now = uiKeysNow(snap.keys);
    if (snap.keys.some(k => now[k] !== snap.after[k])) { showToast(uiT('ui.restore.refused'), { type: 'err' }); return; }
  }
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


_TBM_CSS = r"""
/* ---------- Listes de la barre au thème de l'interface ----------
   Le <select> reste dans la page, masqué ; un bouton de mêmes classes prend sa place (voir initToolbarMenus). */
select[data-tbm-src] { display: none !important; }
.tbm-trigger { display: inline-block; text-align: left; white-space: nowrap; }
.tbm-lbl { display: block; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; text-align: left; padding: 4px 0; margin: -3.25px 0 -2.75px; pointer-events: none; }
.tbm-lbl::after { content: attr(data-w); display: block; height: 0; overflow: hidden; visibility: hidden; white-space: pre; }
@supports (width: calc-size(max-content, round(up, size, 1px))) { .tbm-lbl::after { width: calc-size(max-content, round(up, size, 1px)); } }
.tbm-trigger-open { border-color: var(--amber) !important; }
.tbm-panel {
  position: fixed; z-index: 10500; min-width: 180px; max-width: min(340px, calc(100vw - 16px));
  max-height: min(62vh, 440px); overflow-y: auto; overscroll-behavior: contain;
  background: linear-gradient(180deg, var(--olive-dark) 0%, var(--olive-deep) 100%);
  border: 1px solid var(--amber-dark); border-top: 3px solid var(--amber);
  box-shadow: 0 12px 28px rgba(0,0,0,.55), 0 2px 0 rgba(0,0,0,.35);
  padding: 4px 0; margin: 0; list-style: none; scrollbar-width: thin; scrollbar-color: var(--amber-dark) transparent;
  transform-origin: top left; animation: tbm-in .12s ease-out;
}
@keyframes tbm-in { from { opacity: 0; transform: translateY(-4px); } to { opacity: 1; transform: none; } }
.tbm-head {
  font-family: var(--f-ui); font-weight: 500; font-size: 10px; letter-spacing: 1.8px; text-transform: uppercase;
  color: var(--khaki-light); padding: 8px 14px 6px; border-bottom: 1px solid rgba(168,154,114,.25); margin-bottom: 2px;
}
.tbm-opt {
  position: relative; display: flex; align-items: center; gap: 10px; min-height: 44px; padding: 0 16px 0 18px;
  font-family: var(--f-ui); font-weight: 500; font-size: 13px; letter-spacing: 1.3px; text-transform: uppercase;
  color: var(--paper); cursor: pointer; white-space: nowrap; user-select: none;
}
.tbm-opt + .tbm-opt { border-top: 1px solid rgba(168,154,114,.14); }
.tbm-list .tbm-group { margin-top: 2px; border-top: 1px solid rgba(168,154,114,.25); list-style: none; }
.tbm-opt .tbm-mark { width: 7px; height: 7px; flex: none; transform: rotate(45deg); border: 1px solid var(--khaki); }
.tbm-opt.active, .tbm-opt:hover { background: var(--olive); color: var(--amber); }
.tbm-opt.active .tbm-mark, .tbm-opt:hover .tbm-mark { border-color: var(--amber); }
.tbm-opt[aria-selected="true"] { color: var(--amber); font-weight: 700; }
.tbm-opt[aria-selected="true"]::before { content: ''; position: absolute; left: 0; top: 6px; bottom: 6px; width: 3px; background: var(--amber); }
.tbm-opt[aria-selected="true"] .tbm-mark { background: var(--amber); border-color: var(--amber); }
.tbm-opt[aria-disabled="true"] { color: var(--khaki); cursor: not-allowed; background: none; }
.tbm-opt[aria-disabled="true"] .tbm-mark { border-style: dashed; border-color: var(--khaki); background: none; }
.tbm-opt[aria-disabled="true"] .tbm-note { color: var(--khaki); font-size: 10px; letter-spacing: 1px; margin-left: auto; padding-left: 14px; }
.tbm-off { display: none !important; }
/* La recherche en tête d'une liste (option data-search du <select>) : collée en haut du panneau qui défile */
.tbm-list { margin: 0; padding: 0; list-style: none; outline: none; }
.tbm-search { position: sticky; top: 0; z-index: 2; padding: 6px 10px; background: var(--olive-dark); border-bottom: 1px solid rgba(168,154,114,.25); }
.tbm-q { display: block; width: 100%; min-height: 36px; box-sizing: border-box; padding: 6px 10px; font-family: var(--f-typewriter); font-size: 13px; letter-spacing: .2px; color: #1f1c16; background: rgba(216, 201, 165, .92); border: 1px solid var(--khaki); border-left: 3px solid var(--amber-dark); border-radius: 0; outline: none; }
.tbm-q:focus { border-left-color: var(--red-stamp); box-shadow: 0 0 0 1px var(--amber); }
.tbm-q::placeholder { color: #6b6450; opacity: 1; }
.tbm-none { margin: 0; padding: 0; list-style: none; cursor: default; }
.tbm-msg { font-family: var(--f-typewriter); font-size: 13px; color: var(--khaki-light); }
.tbm-msg:not(:empty) { padding: 12px 18px; }
@media (prefers-reduced-motion: reduce) { .tbm-panel { animation: none; } }
@media print { .tbm-panel { display: none; } }
.tbm-panel.tbm-p-field { max-width: calc(100vw - 16px); }
.tbm-panel.tbm-p-field .tbm-opt {
  font-family: var(--f-typewriter); font-weight: 400; font-size: 13px; letter-spacing: .2px; text-transform: none;
}
.tbm-panel.tbm-p-field .tbm-opt[aria-selected="true"] { font-weight: 400; }
.tbm-panel.tbm-up { border-top: 1px solid var(--amber-dark); border-bottom: 3px solid var(--amber); transform-origin: bottom left; }
"""

_TBM_JS = r"""
/* ============= LISTES AU THÈME DE L'INTERFACE (composant commun des six modules) =============
   Le <select> reste dans la page (id, options, écouteurs) : il garde la valeur, mais il est masqué.
   Un <button> de mêmes classes prend sa place et porte le libellé de l'option choisie ; la liste ouverte
   est un <ul role="listbox"> posé en fin de <body> (la barre défile et couperait ce qui déborde).
   Le libellé suit toujours le <select> : mutations du DOM (options reconstruites, traduites, désactivées,
   title) et affectations par le code (value, selectedIndex) interceptées sur l'instance.
   Ce que le <select> demande par ses attributs : data-search (une recherche en tête de la liste ; data-search-empty : le texte sans résultat), data-keep (une option qui reste malgré la recherche),
   data-right (le texte à droite d'une option), data-repick (un choix identique à la valeur envoie quand même « change »), des <optgroup> (leur titre dans la liste).
   Ce que le module règle, une fois, avant initToolbarMenus : TBM.cfg = { others, trig, short, fitTitle }
     others() : ferme ce qui doit l'être quand une liste s'ouvre (le menu, le panneau du module) ; trig : le sélecteur des boutons qui ouvrent une liste ou un menu (le clic hors de la liste sur l'un d'eux
     ne s'avale pas) ; short(select, option) : le libellé abrégé du bouton fermé, ou rien (le théâtre au téléphone) ; fitTitle : le bouton qui prend la largeur de l'option (fit) porte son nom entier en infobulle. */
const TBM = { cur: null, bound: false, swallow: false, n: 0, all: [], map: new WeakMap(), label: null, mo: null, ro: null, cfg: {} };

function initToolbarMenus(specs) {
  specs.forEach(sp => tbmAttach(document.getElementById(sp[0]), sp[1], sp[2], sp[3]));
  if (TBM.bound) return;
  TBM.bound = true;
  document.addEventListener('pointerdown', tbmOutside, true);
  window.addEventListener('click', tbmSwallowClick, true);
  window.addEventListener('resize', tbmResized);
  window.addEventListener('blur', () => tbmClose(false));
  window.addEventListener('scroll', tbmScrolled, true);
  if (window.visualViewport) { window.visualViewport.addEventListener('resize', tbmVvChanged); window.visualViewport.addEventListener('scroll', tbmVvChanged); }
}

/* ----- Listes des formulaires -----
   Tout <select> hors de la barre du haut passe par le même composant, présent au chargement ou inséré ensuite
   (formulaire reconstruit, rangée ajoutée, onglet ouvert) : un observateur le rattache dès son insertion, et
   détache le bouton d'un <select> qui quitte la page (la liste ouverte sur lui se ferme). labelFn(select) donne l'intitulé. */
function initFormMenus(labelFn) {
  TBM.label = labelFn;
  tbmScan(document.body);
  if (TBM.mo) return;
  TBM.mo = new MutationObserver(recs => {
    for (let i = TBM.all.length - 1; i >= 0; i--) if (!TBM.all[i].sel.isConnected) tbmForget(TBM.all[i]);
    recs.forEach(r => r.addedNodes.forEach(n => { if (n.nodeType === 1) tbmScan(n); }));
  });
  TBM.mo.observe(document.body, { childList: true, subtree: true });
}

function tbmScan(root) {
  if (!TBM.label || !root || root.nodeType !== 1 || root.classList.contains('tbm-panel')) return;
  if (root.tagName !== 'SELECT' && !root.firstElementChild) return;
  const list = root.tagName === 'SELECT' ? [root] : Array.prototype.slice.call(root.querySelectorAll('select'));
  list.forEach(s => {
    if (TBM.map.has(s) || (s.closest && s.closest('header.toolbar'))) return;
    tbmAttach(s, () => TBM.label(s), 'field');
  });
}

function tbmForget(m) {
  if (TBM.cur === m) tbmClose(false);
  if (m.mo) m.mo.disconnect();
  if (TBM.ro) TBM.ro.unobserve(m.btn);
  if (m.btn.parentNode) m.btn.parentNode.removeChild(m.btn);
  TBM.map.delete(m.sel);
  const i = TBM.all.indexOf(m);
  if (i >= 0) TBM.all.splice(i, 1);
}

/* Un champ de moins de 120 px de large : chevron à 8 px du bord (12 px sinon) */
function tbmNarrow(btn) {
  const w = btn.offsetWidth;
  if (w > 0) btn.classList.toggle('tbm-narrow', w < 120);
}

/* mode : rien (liste de la barre) · 'field' (liste de formulaire, bouton d'un champ) · 'sheet' (liste de formulaire,
   bouton fermé déjà habillé par le module) ; fit : le bouton prend la largeur de l'option choisie (comme au Route Planner) ;
   un <select data-search> reçoit une recherche en tête de sa liste */
function tbmAttach(sel, labelFn, mode, fit) {
  if (!sel || !sel.parentNode || TBM.map.has(sel)) return;
  const uid = sel.id || 'f' + (++TBM.n);
  const btn = document.createElement('button');
  btn.type = 'button';
  btn.className = sel.className + ' tbm-trigger' + (mode === 'field' ? ' tbm-field' : '');
  btn.setAttribute('aria-haspopup', 'listbox');
  btn.setAttribute('aria-expanded', 'false');
  btn.setAttribute('aria-controls', 'tbm-list-' + uid);
  const lbl = document.createElement('span');
  lbl.className = 'tbm-lbl';
  btn.appendChild(lbl);
  const m = { sel: sel, btn: btn, lbl: lbl, labelFn: labelFn, panel: null, active: -1, type: '', typeTimer: 0, x0: 0, y0: 0, uid: uid, form: !!mode, fit: !!fit, search: sel.hasAttribute('data-search'), q: null, lis: [], list: null, none: null, noneLi: null, bar: null, empty: '', up: undefined, mo: null };
  sel.parentNode.insertBefore(btn, sel);
  sel.setAttribute('data-tbm-src', '');
  ['value', 'selectedIndex'].forEach(k => {
    const d = Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype, k);
    if (!d || !d.set) return;
    Object.defineProperty(sel, k, {
      configurable: true, enumerable: true,
      get() { return d.get.call(this); },
      set(v) { d.set.call(this, v); tbmSync(m); }
    });
  });
  m.mo = new MutationObserver(() => tbmSync(m));
  m.mo.observe(sel, {
    childList: true, subtree: true, characterData: true, attributes: true,
    attributeFilter: ['title', 'aria-label', 'disabled', 'label', 'selected', 'value']
  });
  TBM.map.set(sel, m);
  TBM.all.push(m);
  if (mode === 'field' && window.ResizeObserver) {
    if (!TBM.ro) TBM.ro = new ResizeObserver(es => es.forEach(e => tbmNarrow(e.target)));
    TBM.ro.observe(btn);
  }
  sel.addEventListener('change', () => tbmSync(m));
  ['focus', 'mouseover'].forEach(ev => btn.addEventListener(ev, () => tbmSync(m)));   /* filet : option.selected posé par le code */
  btn.addEventListener('click', () => { if (m.panel) tbmClose(true); else tbmOpen(m); });
  btn.addEventListener('keydown', e => {
    if (e.key === 'Enter' || e.key === ' ' || e.key === 'ArrowDown' || e.key === 'ArrowUp') {
      e.preventDefault();
      if (!m.panel) tbmOpen(m);
    }
  });
  tbmSync(m);
}

/* Le libellé affiché = l'option choisie ; la largeur = l'option la plus large (comme le <select>) */
function tbmSync(m) {
  const sel = m.sel, o = sel.options, i = sel.selectedIndex;
  let txt = i >= 0 && o[i] ? o[i].label : '';
  const full = txt;
  if (txt && TBM.cfg.short) txt = TBM.cfg.short(sel, o[i]) || txt;       /* le libellé abrégé du module (le théâtre au téléphone) */
  if (m.lbl.textContent !== txt) m.lbl.textContent = txt;
  const all = [];
  for (let k = 0; k < o.length; k++) all.push(o[k].label);
  const w = m.fit ? txt : all.join(String.fromCharCode(10));       /* fit : le bouton prend la largeur de l'option choisie */
  if (m.lbl.getAttribute('data-w') !== w) m.lbl.setAttribute('data-w', w);
  let name = '';
  try { name = m.labelFn(); } catch (e) { name = ''; }
  m.btn.setAttribute('aria-label', name);
  if (sel.hasAttribute('title')) m.btn.title = sel.title; else if (TBM.cfg.fitTitle && m.fit && full) m.btn.title = full; else m.btn.removeAttribute('title');       /* fitTitle : nom entier en infobulle (le bouton peut le tronquer) */
  m.btn.disabled = sel.disabled;
}

function tbmOpen(m) {
  if (TBM.cur) tbmClose(false);
  if (TBM.cfg.others) TBM.cfg.others();
  if (m.sel.disabled) return;
  tbmSync(m);
  const sel = m.sel, opts = sel.options, name = m.labelFn();
  const panel = document.createElement('div');
  panel.className = 'tbm-panel' + (m.form ? ' tbm-p-field' : '');
  panel.id = 'tbm-panel-' + m.uid;
  const head = document.createElement('div');
  head.className = 'tbm-head';
  head.setAttribute('aria-hidden', 'true');
  head.textContent = name;
  panel.appendChild(head);
  const ul = document.createElement('ul');
  ul.className = 'tbm-list';
  ul.id = 'tbm-list-' + m.uid;
  ul.setAttribute('role', 'listbox');
  ul.setAttribute('aria-label', name);
  ul.tabIndex = -1;
  let real = 0;
  for (let k = 0; k < opts.length; k++) if (opts[k].value !== '' && !opts[k].hasAttribute('data-keep')) real++;
  m.q = null; m.none = null; m.noneLi = null; m.bar = null; m.list = ul; m.lis = [];
  if (m.search) {
    /* le champ de recherche est un combobox hors de la listbox (modèle ARIA) ; sans aucune option à chercher, pas de champ : seule la ligne neutre le dit */
    if (real > 0) {
      const bar = document.createElement('div');
      bar.className = 'tbm-search';
      const q = document.createElement('input');
      q.type = 'text';
      q.className = 'tbm-q';
      q.setAttribute('role', 'combobox');
      q.setAttribute('aria-controls', ul.id);
      q.setAttribute('aria-expanded', 'true');
      q.setAttribute('aria-autocomplete', 'list');
      q.setAttribute('placeholder', t('f.search'));
      q.setAttribute('aria-label', t('f.search'));
      q.setAttribute('autocomplete', 'off');
      q.setAttribute('autocapitalize', 'off');
      q.setAttribute('spellcheck', 'false');
      q.setAttribute('enterkeyhint', 'search');
      q.addEventListener('input', () => tbmFilter(m));
      bar.appendChild(q);
      panel.appendChild(bar);
      m.q = q; m.bar = bar;
    }
    /* la ligne neutre (L4) : dans la liste, entre « Choisir… » ou les aérodromes et « Autre… » ; elle est transparente pour la listbox (role presentation) et son texte est dans une zone aria-live qui existe toujours, vide tant qu'il y a des résultats */
    const none = document.createElement('li');
    none.className = 'tbm-none';
    none.setAttribute('role', 'presentation');
    const msg = document.createElement('div');
    msg.className = 'tbm-msg';
    msg.setAttribute('aria-live', 'polite');
    m.empty = sel.getAttribute('data-search-empty') || '';
    if (real === 0) msg.textContent = m.empty;
    none.appendChild(msg);
    m.none = msg;
    m.noneLi = none;
  }
  let grp = null;
  for (let k = 0; k < opts.length; k++) {
    const o = opts[k], li = document.createElement('li');
    const og = o.parentNode && o.parentNode.tagName === 'OPTGROUP' ? o.parentNode : null;       /* un groupe d'options : son titre, une fois, avant la première */
    if (og !== grp) {
      grp = og;
      if (og) {
        const gh = document.createElement('li');
        gh.className = 'tbm-head tbm-group';
        gh.setAttribute('role', 'presentation');
        gh.textContent = og.label;
        ul.appendChild(gh);
      }
    }
    li.className = 'tbm-opt';
    if (o.hasAttribute('data-keep')) li.setAttribute('data-keep', '');
    li.id = 'tbm-' + m.uid + '-' + k;
    li.setAttribute('role', 'option');
    li.setAttribute('aria-selected', k === sel.selectedIndex ? 'true' : 'false');
    li.setAttribute('data-i', String(k));
    const mark = document.createElement('span');
    mark.className = 'tbm-mark';
    const txt = document.createElement('span');
    txt.className = 'tbm-txt';
    let label = o.label, note = '';
    if (o.disabled) {
      li.setAttribute('aria-disabled', 'true');
      const j = label.indexOf(' — ');
      if (j >= 0) { note = label.slice(j + 3); label = label.slice(0, j); }
    }
    if (o.hasAttribute('data-right')) note = o.getAttribute('data-right');      /* une option qui porte son texte de droite (le vol lié d'une route) */
    txt.textContent = label;
    li.appendChild(mark);
    li.appendChild(txt);
    if (note) {
      const n = document.createElement('span');
      n.className = 'tbm-note';
      n.textContent = note;
      li.appendChild(n);
    }
    ul.appendChild(li);
    m.lis.push(li);
  }
  if (m.noneLi) ul.insertBefore(m.noneLi, m.lis.find(x => x.hasAttribute('data-keep')) || null);
  panel.appendChild(ul);
  panel.addEventListener('keydown', e => tbmKey(m, e));
  panel.addEventListener('click', e => {
    const li = e.target.closest ? e.target.closest('.tbm-opt') : null;
    if (!li || li.getAttribute('aria-disabled') === 'true') return;
    tbmChoose(m, Number(li.getAttribute('data-i')));
  });
  panel.addEventListener('mousemove', e => {
    const li = e.target.closest ? e.target.closest('.tbm-opt') : null;
    if (!li || li.getAttribute('aria-disabled') === 'true') return;
    const k = Number(li.getAttribute('data-i'));
    if (k !== m.active) tbmSetActive(m, k, false);
  });
  document.body.appendChild(panel);
  m.panel = panel;
  TBM.cur = m;
  m.btn.classList.add('tbm-trigger-open');
  m.btn.setAttribute('aria-expanded', 'true');
  m.up = undefined;
  tbmPlace(m);
  let k0 = sel.selectedIndex;
  if (k0 < 0 || (opts[k0] && opts[k0].disabled)) k0 = tbmFirst(m, 1);
  tbmSetActive(m, k0, 'center');
  if (m.q && window.matchMedia && window.matchMedia('(hover: hover) and (pointer: fine)').matches) m.q.focus({ preventScroll: true });       /* la recherche a le focus sur ordinateur, pas au toucher (le clavier de l'écran ne s'ouvre pas seul) */
  else ul.focus({ preventScroll: true });
}

/* Sans casse ni accents */
function tbmNorm(x) { return String(x).normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase(); }
/* La recherche : au fil de la frappe, une partie du nom ; « Autre… » (data-keep) reste ; sans résultat, une ligne neutre ; l'option active devient la première trouvée */
function tbmFilter(m) {
  const q = tbmNorm(m.q.value.trim()), o = m.sel.options;
  let n = 0, first = -1;
  m.lis.forEach((li, k) => {
    const keep = li.hasAttribute('data-keep');
    const show = q === '' || keep || (o[k].value !== '' && tbmNorm(o[k].label).indexOf(q) >= 0);
    li.classList.toggle('tbm-off', !show);
    if (q !== '' && !keep && show) { n++; if (first < 0) first = k; }
  });
  const none = q !== '' && n === 0;
  m.none.textContent = none ? m.empty : '';       /* la ligne sans résultat est annoncée (aria-live) quand son texte apparaît */
  if (m.form) tbmPlace(m, true);       /* la liste a changé de hauteur : ouverte vers le haut, elle reste accrochée au bouton */
  if (q === '') { m.panel.scrollTop = 0; tbmSetActive(m, m.sel.selectedIndex >= 0 ? m.sel.selectedIndex : tbmFirst(m, 1), true); return; }
  if (first < 0) first = m.lis.findIndex(li => li.hasAttribute('data-keep'));
  m.panel.scrollTop = 0;
  tbmSetActive(m, first, true);
}
function tbmOff(m, k) { return !!(m.lis[k] && m.lis[k].classList.contains('tbm-off')); }

/* Sous le bouton (4 px), bord gauche aligné, au moins aussi large, à 8 px au moins des bords de la fenêtre.
   Liste de formulaire : la place utile va du bas de la barre du haut au haut de la barre d'onglets fixée en bas (portrait),
   sinon au bas de la fenêtre ; dessous si elle y tient entière, sinon dessus si la place y est plus grande (classe tbm-up). Appelée à l'ouverture, après chaque filtrage (sens gardé : keepDir)
   et quand la fenêtre est redimensionnée ou défilée pendant que la recherche a le focus (le clavier de l'écran). */
/* La zone visible, en coordonnées de la fenêtre : le visualViewport quand il existe (sur Chrome Android et iOS, le clavier de l'écran ne réduit que lui), sinon la fenêtre ;
   dans un cadre (le shell), la fenêtre du cadre : le shell la fait suivre le clavier, et le visualViewport d'un cadre n'est pas fiable */
function tbmVis() {
  const v = window.visualViewport;
  if (v && v.height > 0 && v.width > 0 && window.parent === window) return { top: v.offsetTop, bottom: v.offsetTop + v.height, left: v.offsetLeft, right: v.offsetLeft + v.width };
  return { top: 0, bottom: window.innerHeight, left: 0, right: document.documentElement.clientWidth };
}
function tbmScroller(el) {
  for (let e = el.parentElement; e && e !== document.documentElement; e = e.parentElement) {
    const o = getComputedStyle(e).overflowY;
    if ((o === 'auto' || o === 'scroll') && e.scrollHeight > e.clientHeight + 1) return e;
  }
  return null;
}
/* Pendant la recherche : le bouton sorti de la zone visible (clavier, défilement) est ramené au centre de celle-ci, puis la liste se replace */
function tbmReveal(m) {
  const r = m.btn.getBoundingClientRect(), vis = tbmVis(), tb = document.querySelector('header.toolbar');
  const lo = Math.max(vis.top, tb ? tb.getBoundingClientRect().bottom : 0);
  if (r.bottom <= vis.bottom - 8 && r.top >= lo) return;
  const d = (r.top + r.height / 2) - (lo + (vis.bottom - lo) / 2), sc = tbmScroller(m.btn);
  if (sc) sc.scrollTop += d; else window.scrollBy(0, d);
}
function tbmPlace(m, keepDir) {
  const r = m.btn.getBoundingClientRect(), p = m.panel;
  const vis = tbmVis(), vw = vis.right, vh = vis.bottom;       /* la zone visible (visualViewport) : le clavier de l'écran ne réduit parfois que celle-ci */
  let top = r.bottom + 4;
  m.x0 = r.left; m.y0 = r.top;
  if (m.form) {
    const tb = document.querySelector('header.toolbar'), bar = document.querySelector('.tab-bar');
    const lo = Math.max(vis.top, tb ? tb.getBoundingClientRect().bottom : 0);
    let hi = vh;
    if (bar) {
      const bs = getComputedStyle(bar), br = bar.getBoundingClientRect();
      if (bs.position === 'fixed' && bs.display !== 'none' && br.height > 0 && br.top > lo) hi = Math.min(hi, br.top);
    }
    const cap = tbmKb(m) ? Math.max(60, vh - lo - 8) : Math.min(0.62 * (vh - vis.top), 440);       /* pendant la recherche au toucher (clavier de l'écran) : plus de plafond, toute la hauteur visible */
    const below = hi - (r.bottom + 4) - 12, above = (r.top - 4) - lo - 12;
    p.style.minWidth = Math.min(Math.max(180, r.width), vw - 16) + 'px';
    p.style.maxHeight = 'none';
    const up = keepDir && m.up !== undefined ? m.up : Math.min(p.offsetHeight, cap) > below && above > below;       /* keepDir : le sens choisi à l'ouverture ne change pas pendant la frappe */
    m.up = up;
    p.style.maxHeight = Math.max(60, Math.min(cap, up ? above : below, vh - lo - 8)) + 'px';
    p.classList.toggle('tbm-up', up);
    let ty = up ? r.top - 4 - p.offsetHeight : r.bottom + 4;
    ty = Math.max(lo, Math.min(ty, vh - 4 - p.offsetHeight));       /* le bouton hors de la zone visible et sans rien à défiler : la liste reste dans la zone visible */
    p.style.top = ty + 'px';
    p.style.left = r.left + 'px';
    const fw = p.getBoundingClientRect().width;
    let fl = r.left;
    if (fl + fw > vw - 8) fl = vw - 8 - fw;
    if (fl < vis.left + 8) fl = vis.left + 8;
    p.style.left = fl + 'px';
    return;
  }
  p.style.minWidth = Math.max(180, r.width) + 'px';
  p.style.top = top + 'px';
  p.style.left = r.left + 'px';
  p.style.maxHeight = Math.max(60, Math.min(0.62 * (vh - vis.top), 440, vh - top - 12)) + 'px';
  const w = p.getBoundingClientRect().width;
  let left = r.left;
  if (left + w > vw - 8) left = vw - 8 - w;
  if (left < vis.left + 8) left = vis.left + 8;
  p.style.left = left + 'px';
}

function tbmFirst(m, d) {
  const o = m.sel.options;
  let k = d > 0 ? 0 : o.length - 1;
  for (; k >= 0 && k < o.length; k += d) if (!o[k].disabled && !tbmOff(m, k)) return k;
  return -1;
}

function tbmSetActive(m, k, reveal) {
  const p = m.panel;
  if (!p) return;
  const prev = p.querySelector('.tbm-opt.active');
  if (prev) prev.classList.remove('active');
  m.active = k;
  const li = k >= 0 ? p.querySelector('.tbm-opt[data-i="' + k + '"]') : null;
  const holders = [m.list, m.q].filter(Boolean);       /* la listbox, et le champ de recherche quand il y en a un */
  if (!li) { holders.forEach(h => h.removeAttribute('aria-activedescendant')); return; }
  li.classList.add('active');
  holders.forEach(h => h.setAttribute('aria-activedescendant', li.id));
  if (!reveal) return;
  const t = li.offsetTop, h = li.offsetHeight, sh = m.bar ? m.bar.offsetHeight : 0;       /* la recherche collée en haut cache les sh premiers pixels */
  if (k === tbmFirst(m, 1)) p.scrollTop = 0;
  else if (t - sh < p.scrollTop) p.scrollTop = Math.max(0, t - sh);
  else if (t + h > p.scrollTop + p.clientHeight) p.scrollTop = reveal === 'center' ? Math.max(0, t - sh - (p.clientHeight - sh - h) / 2) : t + h - p.clientHeight;
}

function tbmStep(m, d) {
  const o = m.sel.options;
  for (let k = m.active + d; k >= 0 && k < o.length; k += d) {
    if (!o[k].disabled && !tbmOff(m, k)) { tbmSetActive(m, k, true); return; }
  }
}

/* Saisie de lettres : première option qui commence par elles, remise à zéro après 0,7 s */
function tbmType(m, ch) {
  clearTimeout(m.typeTimer);
  m.type += ch.toLowerCase();
  m.typeTimer = setTimeout(() => { m.type = ''; }, 700);
  const o = m.sel.options;
  for (let k = 0; k < o.length; k++) {
    if (!o[k].disabled && !tbmOff(m, k) && o[k].label.toLowerCase().indexOf(m.type) === 0) { tbmSetActive(m, k, true); return; }
  }
}

/* Les touches dans le champ de recherche : ↓ passe à la première option, Entrée choisit l'option active, Échap ferme ; le reste est de la frappe */
function tbmQKey(m, e) {
  const k = e.key;
  if (k === 'ArrowDown') { e.preventDefault(); tbmSetActive(m, tbmFirst(m, 1), true); m.list.focus({ preventScroll: true }); }
  else if (k === 'ArrowUp') e.preventDefault();
  else if (k === 'Enter') { e.preventDefault(); if (m.active >= 0 && !tbmOff(m, m.active)) tbmChoose(m, m.active); }
  else if (k === 'Escape') { e.preventDefault(); e.stopPropagation(); tbmClose(true); }
  else if (k === 'Tab') tbmClose(true);
}

function tbmKey(m, e) {
  const k = e.key;
  if (m.q && e.target === m.q) { tbmQKey(m, e); return; }
  if (m.q && k === 'ArrowUp' && m.active === tbmFirst(m, 1) && e.target !== m.q) { e.preventDefault(); m.q.focus({ preventScroll: true }); return; }       /* ↑ sur la première option : le focus revient au champ */
  if (m.q && k.length === 1 && k !== ' ' && !e.ctrlKey && !e.metaKey && !e.altKey) {       /* une lettre tapée sur la liste va à la recherche ; Espace, non : il choisit l'option active (dans le champ, il se tape) */
    e.preventDefault();
    m.q.focus({ preventScroll: true });
    m.q.value += k;
    tbmFilter(m);
    return;
  }
  if (k === 'ArrowDown' || k === 'ArrowUp') { e.preventDefault(); tbmStep(m, k === 'ArrowDown' ? 1 : -1); }
  else if (k === 'Home') { e.preventDefault(); tbmSetActive(m, tbmFirst(m, 1), true); }
  else if (k === 'End') { e.preventDefault(); tbmSetActive(m, tbmFirst(m, -1), true); }
  else if (k === 'Enter' || k === ' ') { e.preventDefault(); if (m.active >= 0) tbmChoose(m, m.active); }
  else if (k === 'Escape') { e.preventDefault(); e.stopPropagation(); tbmClose(true); }
  else if (k === 'Tab') { tbmClose(true); }   /* sans preventDefault : le focus part du bouton vers le contrôle suivant */
  else if (k.length === 1 && !e.ctrlKey && !e.metaKey && !e.altKey) { e.preventDefault(); tbmType(m, k); }
}

/* Choisir : si la valeur change, le <select> la prend et reçoit un évènement change (qui bouillonne) ; un <select data-repick> (le champ Livrée) le reçoit aussi quand on re-choisit sa valeur : le nom affiché devient un choix */
function tbmChoose(m, k) {
  const sel = m.sel, o = sel.options[k];
  if (!o || o.disabled) return;
  const changed = k !== sel.selectedIndex;
  tbmClose(true);
  if (!changed && !sel.hasAttribute('data-repick')) return;
  sel.selectedIndex = k;
  if (m.form) sel.dispatchEvent(new Event('input', { bubbles: true }));   /* comme le contrôle natif : input puis change */
  sel.dispatchEvent(new Event('change', { bubbles: true }));
}

function tbmClose(refocus) {
  const m = TBM.cur;
  if (!m) return;
  TBM.cur = null;
  clearTimeout(m.typeTimer);
  m.type = '';
  if (m.panel) m.panel.remove();
  m.panel = null;
  m.q = null; m.bar = null; m.none = null; m.noneLi = null; m.list = null; m.lis = [];
  m.active = -1;
  m.btn.classList.remove('tbm-trigger-open');
  m.btn.setAttribute('aria-expanded', 'false');
  if (refocus) m.btn.focus({ preventScroll: true });
}

/* Un toucher ou un clic hors de la liste et du bouton la ferme, sans agir ailleurs (le clic qui suit est avalé) ;
   le bouton d'une autre liste ferme celle-ci et s'ouvre ensuite par son propre clic. */
function tbmOutside(e) {
  const m = TBM.cur;
  if (!m) return;
  const t = e.target;
  if (m.panel.contains(t) || m.btn.contains(t)) return;
  const other = t && t.closest ? t.closest(TBM.cfg.trig || '.tbm-trigger') : null;
  tbmClose(false);
  if (other) return;
  tbmSwallowNext();
}

/* Le clic qui suit le toucher hors de la liste est avalé (aussi pour les menus du module) */
function tbmSwallowNext() {
  TBM.swallow = true;
  const rel = () => { document.removeEventListener('pointerup', rel, true); document.removeEventListener('pointercancel', rel, true); setTimeout(() => { TBM.swallow = false; }, 350); };
  document.addEventListener('pointerup', rel, true);
  document.addEventListener('pointercancel', rel, true);
}

function tbmSwallowClick(e) {
  if (!TBM.swallow) return;
  TBM.swallow = false;
  e.stopPropagation();
  e.preventDefault();
}

/* Le champ de recherche a le focus : le clavier de l'écran redimensionne la fenêtre ou fait défiler la page ; la liste ne se ferme pas, elle se replace */
function tbmSearching(m) { return !!(m && m.panel && m.q && document.activeElement === m.q); }

/* La recherche au toucher : le clavier de l'écran est ouvert (pas de souris : sur ordinateur la recherche a le focus dès l'ouverture, sans clavier) */
function tbmKb(m) { return tbmSearching(m) && !(window.matchMedia && window.matchMedia('(hover: hover) and (pointer: fine)').matches); }
/* La hauteur qu'il faut pour le champ et quatre options entières (ou toutes, s'il y en a moins) */
function tbmNeed(m) {
  const p = m.panel, h0 = p.style.maxHeight, sy = p.scrollTop;
  p.style.maxHeight = 'none';
  p.scrollTop = 0;
  const pr = p.getBoundingClientRect();
  const opts = m.lis.filter(li => !li.classList.contains('tbm-off'));
  let need = p.offsetHeight;
  if (opts.length) {
    const last = opts[Math.min(4, opts.length) - 1].getBoundingClientRect();
    need = Math.min(need, last.bottom - pr.top + 4);
  }
  p.style.maxHeight = h0;
  p.scrollTop = sy;
  return need;
}
/* Si la place sous le bouton ne suffit pas, le bouton remonte en haut de la zone visible (sous la barre, 8 px) : vrai quand la place sous lui suffit ensuite */
function tbmFit(m) {
  const vis = tbmVis(), tb = document.querySelector('header.toolbar'), bar = document.querySelector('.tab-bar');
  const lo = Math.max(vis.top, tb ? tb.getBoundingClientRect().bottom : 0);
  let hi = vis.bottom;
  if (bar) {
    const bs = getComputedStyle(bar), br = bar.getBoundingClientRect();
    if (bs.position === 'fixed' && bs.display !== 'none' && br.height > 0 && br.top > lo) hi = Math.min(hi, br.top);
  }
  const below = () => hi - (m.btn.getBoundingClientRect().bottom + 4) - 12;
  const need = tbmNeed(m);
  if (below() >= need) return false;
  const d = m.btn.getBoundingClientRect().top - (lo + 8);
  if (Math.abs(d) > 0.5) {
    const sc = tbmScroller(m.btn);
    if (sc) sc.scrollTop += d; else window.scrollBy(0, d);
    const rest = m.btn.getBoundingClientRect().top - (lo + 8);
    if (sc && Math.abs(rest) > 0.5) window.scrollBy(0, rest);
  }
  return below() >= need;
}

/* Le redimensionnement de la fenêtre ferme la liste, sauf pendant la recherche (elle se replace, le bouton ramené à l'écran) */
function tbmResized() {
  const m = TBM.cur;
  if (tbmSearching(m)) { tbmFollow(m); return; }
  tbmClose(false);
}
function tbmFollow(m) {
  if (!m.form) return;
  tbmReveal(m);
  if (tbmKb(m) && tbmFit(m)) { m.up = false; tbmPlace(m, true); return; }
  tbmPlace(m);
}
/* Le visualViewport (zone visible) change — clavier de l'écran, zoom : sans effet hors recherche ; pendant la recherche la liste se replace dans la zone visible */
function tbmVvChanged() {
  const m = TBM.cur;
  if (tbmSearching(m)) tbmFollow(m);
}

/* Le défilement de la barre (ou de la page) déplace le bouton : la liste se ferme, sauf pendant la recherche (le bouton sorti de la zone visible est ramené, la liste se replace) */
function tbmScrolled(e) {
  const m = TBM.cur;
  if (!m || !m.panel) return;
  if (e.target === m.panel || (e.target.nodeType && m.panel.contains(e.target))) return;
  const r = m.btn.getBoundingClientRect();
  if (Math.abs(r.left - m.x0) > 0.5 || Math.abs(r.top - m.y0) > 0.5) {
    if (tbmSearching(m)) { tbmFollow(m); return; }
    tbmClose(false);
  }
}
"""


def build_block():
    """Le script du bloc, délimité par ses deux commentaires, terminé par un saut de ligne."""
    return BLOCK_BEGIN + _JS + BLOCK_END + '\n'


def build_css():
    """La feuille du bloc, délimitée par ses deux commentaires, terminée par un saut de ligne."""
    return CSS_BEGIN + _CSS + CSS_END + '\n'


def build_tbm_css():
    """La feuille des listes au thème de l'interface, délimitée, terminée par un saut de ligne."""
    return TBM_CSS_BEGIN + _TBM_CSS + TBM_CSS_END + '\n'


def build_tbm_block():
    """Le script des listes au thème de l'interface (tbm*), délimité, terminé par un saut de ligne."""
    return TBM_BEGIN + _TBM_JS + TBM_END + '\n'


def fingerprint():
    """L'empreinte du bloc (feuille, script, puis les listes : feuille et script) : sha256, 16 premiers caractères."""
    return hashlib.sha256((build_css() + build_block() + build_tbm_css() + build_tbm_block()).encode('utf-8')).hexdigest()[:16]


def verify(html):
    """Garde-fou de build : le bloc (feuille et script) est dans le livrable, tel quel ; imprime l'empreinte."""
    if build_css() not in html or build_block() not in html:
        raise SystemExit("[ERREUR] bloc d'interface commun absent du livrable ou modifié")
    if build_tbm_css() not in html or build_tbm_block() not in html:
        raise SystemExit("[ERREUR] listes au thème de l'interface (tbm*) absentes du livrable ou modifiées")
    if html.count('function tbmOpen(') != 1 or html.count('const TBM = ') != 1 or html.count('position: fixed; z-index: 10500; min-width: 180px') != 1:
        raise SystemExit("[ERREUR] les listes au thème de l'interface (tbm*) ne sont pas en un seul exemplaire dans le livrable")
    if '@@TBM_' in html:
        raise SystemExit("[ERREUR] un emplacement des listes (@@TBM_…) est resté dans le livrable")
    print("[OK] bloc d'interface commun inséré tel quel, empreinte %s" % fingerprint())


def verify_bar(html):
    """Garde-fou de build : l'ordre de la barre est celui du HTML, le même à toutes les largeurs (retour, sigle, boutons de fichier .tb-file,
    séparateur .tb-files-end, puis le reste) ; plus aucun déplacement selon la largeur."""
    import re
    m = re.search(r'<header class="toolbar".*?</header>', html, re.S)
    if not m:
        raise SystemExit("[ERREUR] barre introuvable dans le livrable")
    bar = m.group(0)
    tags = re.findall(r'<(button|select)\b([^>]*)>|<(?:div|span) class="([^"]*\btb-files-end\b[^"]*)"', bar)
    seq = []
    for tag, attrs, sep in tags:
        if sep:
            seq.append('|')
        elif tag == 'button':
            c = re.search(r'class="([^"]*)"', attrs)
            seq.append('F' if c and 'tb-file' in c.group(1).split() else 'B')
        else:
            seq.append('S')
    s = ''.join(seq)
    if not re.match(r'^F+\|', s):
        raise SystemExit("[ERREUR] barre : les boutons de fichier ne sont pas en tête, suivis du séparateur (%s)" % s)
    if 'F' in s[s.index('|'):]:
        raise SystemExit("[ERREUR] barre : un bouton de fichier après le séparateur (%s)" % s)
    for old_name in ('uiBarPlace', '_uiMark'):
        if old_name in html:
            raise SystemExit("[ERREUR] barre : le déplacement selon la largeur (%s) est encore dans le livrable" % old_name)
    print("[OK] barre : fichiers d'abord, séparateur, puis le reste, dans le HTML (%s)" % s)


if __name__ == '__main__':
    print(f"[OK] bloc d'interface : script {len(build_block())} caractères, feuille {len(build_css())}, listes {len(build_tbm_block())} + {len(build_tbm_css())}, empreinte {fingerprint()}")
