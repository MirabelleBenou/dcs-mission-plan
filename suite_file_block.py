#!/usr/bin/env python3
"""Bloc « FICHIER DE TRAVAIL DE LA SUITE » : un seul fichier JSON pour tout le travail de Mission Plan, écrit et lu par le shell seul.

Les outils n'en ont qu'un appel (window.parent.MP_WORK_SAVE(), MP_WORK_OPEN(), MP_WORK_OPEN_TEXT(texte, nom), MP_WORK_EXAMPLE(groupe)) et, s'ils diffèrent l'écriture d'une clé du fichier, une fonction
window.MP_FLUSH() que le shell appelle avant de lire le stockage. Le bloc ne s'insère que dans le shell (build_mission_plan.py) ; il ne touche pas au DOM des outils.

Quatre textes :
  build_block() — le script : SUITE_KEYS, le format, MP_WORK_SAVE (la fenêtre du nom, puis le téléchargement), MP_WORK_OPEN / MP_WORK_OPEN_TEXT (le remplacement du travail, sans question,
                  suivi du toast « Restaurer » 12 s), la restauration, le calme du stockage (les constantes et la règle de gsSettled, group_store_block.py)
  build_html()  — la fenêtre du nom : une .ui-modal, de la forme de celles des outils (feuille de ui_block.build_css(), insérée telle quelle dans le shell)
  build_css()   — les variables de couleur de ces deux feuilles (ui_block et messages_block) et la feuille du toast : la valeur qu'elles ont dans les six outils, thème par thème, posées sur la fenêtre
                  et sur #toast seulement (le shell garde ses propres --paper, --amber… pour le mur)
  THEME_VARS    — la table de ces valeurs, que le build de la suite compare au CSS de chacun des six outils

Le format (un JSON) :
  { "format": "dcs-mission-plan-work-v1", "createdAt": "<ISO 8601>", "version": "<APP_VERSION du shell>", "theatre": "<théâtre de mp_theatre_v1, ou null>",
    "keys": { "<clé>": "<la valeur au stockage, chaîne telle quelle>" } }
Une clé absente du stockage n'est pas écrite ; les valeurs sont les chaînes du stockage, à l'octet. Le fichier est indenté de deux espaces.
SUITE_KEYS = les clés de contenu des outils du Flight Leader (GS_CONTENT_KEYS de group_store_block.py, dans son ordre) + celle du briefing + celle de Recon Station (sans l'image source).
L'exemple : un seul, chargé par groupe d'outils (SUITE_GROUPS : « mc », le Mission Commander, et « fl », le Flight Leader). Le build du shell embarque les deux fichiers d'exemple (samples/example_work_fr.json et _en.json,
au format ci-dessus) dans SUITE_EXAMPLES ({ fr, en }) ; MP_WORK_EXAMPLE(g) remplace les clés du groupe par celles de l'exemple de la langue du shell et rouvre les seuls outils du groupe.
Hors du fichier : les préférences d'écran (langue, thème, replis, affichage, partages d'écran, calques de carte), la mission d'HQ (mission_snapshot_v1) et la configuration Wing (wing_config_v1).

Usage (par le build) : from suite_file_block import build_block, build_html, build_css, THEME_VARS
"""

BLOCK_BEGIN = '/* ===== FICHIER DE TRAVAIL DE LA SUITE ===== */'
BLOCK_END = '/* ===== FIN DU FICHIER DE TRAVAIL DE LA SUITE ===== */'
CSS_BEGIN = '/* ===== FICHIER DE TRAVAIL : couleurs de la fenêtre du nom et du toast ===== */'
CSS_END = '/* ===== FIN DES COULEURS DE LA FENÊTRE DU NOM ET DU TOAST ===== */'
HTML_BEGIN = '<!-- ===== FENÊTRE : SAUVEGARDER LE TRAVAIL — CHOISIR LE NOM DU FICHIER ===== -->'

# Les valeurs des variables des feuilles de ui_block et de messages_block dans les six outils (HQ, Briefing Generator, Datacard Generator, Route Planner, Flight Configurator, Recon Station),
# thème par thème : les mêmes dans les six (mesurées). Le build de la suite les retrouve dans le CSS de chacun.
_F_UI = "'Oswald', 'Arial Narrow', sans-serif"
_F_STENCIL = "'Stardos Stencil', 'Impact', 'Arial Narrow Bold', sans-serif"
THEME_VARS = {
    'cw-nato': {'--amber': '#c0892a', '--amber-dark': '#8a5e15', '--green-radar': '#4f6b3a', '--khaki': '#807454', '--khaki-light': '#a89a72', '--mp-warn': '#e8806a',
                '--olive': '#4a5230', '--olive-dark': '#2c321e', '--paper': '#d8c9a5', '--paper-light': '#e3d6b5', '--f-ui': _F_UI, '--f-stencil': _F_STENCIL},
    'cw-soviet': {'--amber': '#c0892a', '--amber-dark': '#8a5e15', '--green-radar': '#4f6b3a', '--khaki': '#3a4a2e', '--khaki-light': '#5a6a48', '--mp-warn': '#e8806a',
                  '--olive': '#2a3a5a', '--olive-dark': '#1a2540', '--paper': '#d8c479', '--paper-light': '#e8d690', '--f-ui': _F_UI, '--f-stencil': _F_STENCIL},
    'modern-nato': {'--amber': '#c0892a', '--amber-dark': '#8a5e15', '--green-radar': '#4f6b3a', '--khaki': '#5c6b7a', '--khaki-light': '#7a8a98', '--mp-warn': '#e8806a',
                    '--olive': '#2a3038', '--olive-dark': '#1c2026', '--paper': '#e8e3d8', '--paper-light': '#f0ece2', '--f-ui': _F_UI, '--f-stencil': _F_STENCIL},
    'modern-east': {'--amber': '#c0892a', '--amber-dark': '#8a5e15', '--green-radar': '#4f6b3a', '--khaki': '#4a5238', '--khaki-light': '#6a7256', '--mp-warn': '#e8806a',
                    '--olive': '#3d3024', '--olive-dark': '#2a2018', '--paper': '#cdc6b8', '--paper-light': '#ddd6c8', '--f-ui': _F_UI, '--f-stencil': _F_STENCIL},
}

_JS = r"""
const SUITE_FORMAT = 'dcs-mission-plan-work-v1';
const SUITE_KEYS = ['fc_state_v1', 'flight_set_v1', 'flight_set_v1_illisible', 'route_set_v1', 'route_state_v1', 'route_layers_v1', 'datacard_state_v1', 'mp_theatre_v1', 'mp_units_v1', 'mp_nav_v1', 'khr26_briefing_state_v2', 'recon_state_v1'];
/* Les deux groupes de l'exemple : leurs outils et leurs clés. mp_units_v1 et mp_nav_v1 (des réglages) ne sont d'aucun groupe : un exemple ne les écrit ni ne les retire. Le build vérifie que les deux listes de clés sont disjointes et que leur union avec ces deux clés est SUITE_KEYS. */
const SUITE_GROUPS = {
  mc: { tools: ['bg', 'rs'], keys: ['khr26_briefing_state_v2', 'recon_state_v1'] },
  fl: { tools: ['rp', 'dg', 'fc'], keys: ['fc_state_v1', 'flight_set_v1', 'flight_set_v1_illisible', 'route_set_v1', 'route_state_v1', 'route_layers_v1', 'datacard_state_v1', 'mp_theatre_v1'] }
};
/* Les outils dont l'iframe est retirée quand le travail est remplacé (ils lisent les clés ci-dessus) ; HQ et le Field Manual n'en lisent aucune : ils restent (le .miz d'HQ reste chargé) */
const SUITE_DROP = ['bg', 'dg', 'rp', 'fc', 'rs'];
/* Le calme du stockage, mesuré comme gsSettled (group_store_block.py) : aucune écriture des clés pendant SUITE_CALM_MS, constaté à deux relectures de suite (toutes les SUITE_CALM_STEP_MS), au plus SUITE_CALM_MAX_MS */
const SUITE_CALM_MS = 400, SUITE_CALM_MAX_MS = 3000, SUITE_CALM_STEP_MS = 50;
const SUITE = { restore: null, toastN: 0, name: '', at: 0, from: null, busy: false, give: {} };

function suiteGet(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }
function suiteRead(keys) { const o = {}; (keys || SUITE_KEYS).forEach(k => { o[k] = suiteGet(k); }); return o; }
/* Écrit la table clé → texte ou null, pour les clés de la portée (toutes les clés par défaut) : les clés absentes sont retirées d'abord (de la place se libère), puis les autres sont écrites.
   Une clé hors de la portée n'est ni écrite ni retirée. Faux si une écriture a échoué (stockage plein). */
function suiteWriteAll(map, keys) {
  const ks = keys || SUITE_KEYS;
  let ok = true;
  ks.forEach(k => { if (typeof map[k] !== 'string') { try { localStorage.removeItem(k); } catch (e) { ok = false; } } });
  ks.forEach(k => { if (typeof map[k] === 'string') { try { localStorage.setItem(k, map[k]); } catch (e) { ok = false; } } });
  return ok;
}
/* Chaque outil vivant écrit d'abord sa saisie en attente (MP_FLUSH), puis le stockage est lu */
function suiteFlush(id) {
  const ids = id ? [id] : Object.keys(iframes);
  ids.forEach(i => {
    try { const w = iframes[i] && iframes[i].contentWindow; if (w && typeof w.MP_FLUSH === 'function') w.MP_FLUSH(); }
    catch (e) { console.warn('[M·P] écriture en attente de ' + i + ' : ' + e); }
  });
}
/* Le nom d'un fichier choisi : la règle des noms de fichier des outils (cleanFname) — sans « .json », accents ôtés, tout ce qui n'est pas lettre, chiffre, _ + - devient « _ » ; vide si rien ne reste */
function suiteCleanName(v) {
  return String(v === undefined || v === null ? '' : v).trim().replace(/\.json$/i, '').normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/[^A-Za-z0-9_+-]+/g, '_').replace(/_{2,}/g, '_').replace(/^_+|_+$/g, '').slice(0, 100);
}
function suiteDefaultName() {
  const d = new Date(), p = n => String(n).padStart(2, '0');
  return 'mission_plan_' + d.getFullYear() + '-' + p(d.getMonth() + 1) + '-' + p(d.getDate());
}
/* Le texte du fichier : les clés sont lues à ce moment, chaînes du stockage à l'octet */
function suiteWorkText() {
  const now = suiteRead(), keys = {};
  SUITE_KEYS.forEach(k => { if (now[k] !== null) keys[k] = now[k]; });
  let th = null;
  try { const o = JSON.parse(now.mp_theatre_v1); if (o && typeof o.theatre === 'string' && o.theatre !== '') th = o.theatre; } catch (e) { th = null; }
  return JSON.stringify({ format: SUITE_FORMAT, createdAt: new Date().toISOString(), version: APP_VERSION, theatre: th, keys: keys }, null, 2);
}

/* ---- la fenêtre du nom (une .ui-modal) ---- */
function suiteModal() { return document.getElementById('mp-work-modal'); }
function suiteFrom() {
  if (activeModule && iframes[activeModule]) {
    try { return { win: iframes[activeModule].contentWindow, el: iframes[activeModule].contentDocument.activeElement }; } catch (e) { /* le module garde le clavier */ }
  }
  return { win: null, el: document.activeElement };
}
function suiteSaveSync() { document.getElementById('mp-work-go').disabled = SUITE.busy || suiteCleanName(SUITE.name) === ''; }
function suiteModalClose() {
  const m = suiteModal();
  if (!m || m.hidden) return;
  m.hidden = true;
  const f = SUITE.from;
  SUITE.from = null;
  try {
    if (f && f.win) { f.win.focus(); if (f.el && f.el.isConnected && f.el.focus) f.el.focus({ preventScroll: true }); }
    else if (f && f.el && f.el.isConnected && f.el.focus && f.el !== document.body && !f.el.disabled) f.el.focus({ preventScroll: true });
    else { const l = document.getElementById('landing'); if (l && activeModule === null) l.focus({ preventScroll: true }); }
  } catch (e) { /* le focus est facultatif */ }
}
/* Le fichier est lu après le calme : chaque outil vivant écrit sa saisie en attente (MP_FLUSH), le shell attend que les clés ne bougent plus (suiteSettled, 3 s au plus), puis lit. Le bouton reste désactivé pendant l'attente ; fermer la fenêtre l'annule. */
async function suiteSaveGo() {
  const name = suiteCleanName(SUITE.name);
  if (name === '' || SUITE.busy) return;
  SUITE.busy = true;
  suiteSaveSync();
  suiteFlush();
  await suiteSettled();
  SUITE.busy = false;
  const m = suiteModal();
  if (!m || m.hidden) return;
  suiteSaveSync();
  const text = suiteWorkText();
  suiteModalClose();
  const url = URL.createObjectURL(new Blob([text], { type: 'application/json' }));
  const a = document.createElement('a');
  a.href = url;
  a.download = name + '.json';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
/* « Sauvegarder » (le bouton de l'accueil, celui de chaque outil, Ctrl+S) : chaque outil vivant écrit sa saisie en attente, puis la fenêtre du nom s'ouvre */
window.MP_WORK_SAVE = function () {
  const m = suiteModal();
  if (!m || !m.hidden) return;
  suiteFlush();
  SUITE.from = suiteFrom();
  SUITE.name = suiteCleanName(suiteDefaultName());
  SUITE.at = performance.now();
  const f = document.getElementById('mp-work-name');
  f.value = SUITE.name;
  suiteSaveSync();
  m.hidden = false;
  f.focus({ preventScroll: true });
  f.select();
};
function suiteBind() {
  ['mp-work-close', 'mp-work-cancel'].forEach(id => document.getElementById(id).addEventListener('click', suiteModalClose));
  /* le fond ignore les clics des 400 ms qui suivent l'ouverture : le 2e clic d'un double-clic sur « Sauvegarder » ne ferme pas la fenêtre */
  document.getElementById('mp-work-backdrop').addEventListener('click', () => { if (performance.now() - SUITE.at > 400) suiteModalClose(); });
  document.getElementById('mp-work-go').addEventListener('click', suiteSaveGo);
  const f = document.getElementById('mp-work-name');
  f.addEventListener('input', e => { SUITE.name = e.target.value; suiteSaveSync(); });
  f.addEventListener('keydown', e => { if (e.key === 'Enter') { e.preventDefault(); if (!e.repeat) suiteSaveGo(); } });
  /* Échap (= la croix) et le piège du focus de la fenêtre */
  window.addEventListener('keydown', e => {
    const m = suiteModal();
    if (!m || m.hidden || e.defaultPrevented) return;
    if (e.key === 'Escape') { e.preventDefault(); suiteModalClose(); }
    else if (e.key === 'Tab') {
      const els = Array.prototype.filter.call(m.querySelectorAll('button, input'), x => !x.disabled && x.getClientRects().length > 0);
      if (!els.length) return;
      const first = els[0], last = els[els.length - 1], a = document.activeElement;
      if (e.shiftKey && (a === first || !m.contains(a))) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && (a === last || !m.contains(a))) { e.preventDefault(); first.focus(); }
    }
  }, true);
}

/* ---- le calme du stockage ---- */
function suiteSettled() {
  return new Promise(res => {
    const t0 = Date.now(), vals = SUITE_KEYS.map(suiteGet);
    let last = t0, calm = 0, tm = 0;
    const onSt = e => { if (e.key === null || SUITE_KEYS.indexOf(e.key) >= 0) last = Date.now(); };
    window.addEventListener('storage', onSt);
    const tick = () => {
      const now = Date.now();
      SUITE_KEYS.forEach((k, i) => { const v = suiteGet(k); if (v !== vals[i]) { vals[i] = v; last = now; } });
      calm = now - last >= SUITE_CALM_MS ? calm + 1 : 0;
      if (calm >= 2 || now - t0 >= SUITE_CALM_MAX_MS) { window.removeEventListener('storage', onSt); res(); return; }
      tm = setTimeout(tick, SUITE_CALM_STEP_MS);
    };
    tm = setTimeout(tick, SUITE_CALM_STEP_MS);
  });
}

/* ---- remplacer le travail : on fait, on garde l'ancien, un toast « Restaurer » 12 s, jamais de question ---- */
/* b. les iframes des outils retirés (les cinq par défaut, ceux d'un groupe pour un exemple) partent (leurs écritures en attente d'abord, par MP_FLUSH puis à pagehide) ; c. les clés de la portée (toutes par défaut) sont photographiées ;
   d. elles sont écrites (celles qui manquent sont retirées ; un stockage plein remet la photographie à l'octet) ; e. si l'on était dans l'un de ces outils, il est rouvert, iframe neuve. Rend { ok, snap }. */
function suiteReplace(next, tools, keys, give) {
  const was = activeModule, drop = tools || SUITE_DROP, ks = keys || SUITE_KEYS, mem = {};
  drop.forEach(id => {
    const f = iframes[id];
    if (!f) return;
    suiteFlush(id);
    /* l'image source d'un outil qui la garde hors du stockage (le Recon Station) : prise en mémoire avant le retrait, pour « Restaurer » */
    try { const w = f.contentWindow; if (w && typeof w.MP_IMG_TAKE === 'function') { const m = w.MP_IMG_TAKE(); if (m) mem[id] = m; } }
    catch (e) { console.warn('[M·P] image de ' + id + ' : ' + e); }
    f.remove();
    delete iframes[id];
    delete barSync[id];
  });
  if (give) Object.keys(give).forEach(id => { SUITE.give[id] = give[id]; });       /* rendue à l'outil rouvert, à son « load » (suiteOnLoad) */
  const snap = suiteRead(ks);
  const ok = suiteWriteAll(next, ks);
  if (!ok) { suiteWriteAll(snap, ks); suiteWriteAll(snap, ks); }
  if (was && drop.indexOf(was) >= 0) openModule(was);
  return { ok: ok, snap: snap, mem: mem };
}
/* La restauration en attente, si son toast est encore à l'écran */
function suiteLive() {
  const toastEl = document.getElementById('toast');
  return SUITE.restore && SUITE.toastN === showToast._n && toastEl && toastEl.classList.contains('show') ? SUITE.restore : null;
}
/* Le remplacement du travail, de l'exemple d'un groupe ou d'un fichier, sans question : { keys, tools } sa portée, next la table des clés de cette portée.
   Une seule restauration en attente : tant que le toast « Restaurer » d'un premier remplacement est à l'écran, la photographie reste celle d'avant le premier (comme replaceWithRestore) ;
   la portée de « Restaurer » devient l'union des deux (toutes les clés et les cinq outils si l'un est un fichier). Rend la restauration, ou null si l'écriture a échoué. */
function suiteDo(next, keys, tools, toast) {
  const keep = suiteLive();
  const res = suiteReplace(next, tools, keys);
  if (!res.ok) { showToast(t('work.err.full'), { type: 'err' }); return null; }
  const r = { snap: res.snap, keys: keys.slice(), tools: tools.slice(), ref: null, pending: null, n: 0, mem: res.mem };
  if (keep) {
    SUITE_KEYS.forEach(k => { if (keep.keys.indexOf(k) >= 0 && r.keys.indexOf(k) < 0) r.keys.push(k); });
    tools = SUITE_DROP.filter(id => keep.tools.indexOf(id) >= 0 || r.tools.indexOf(id) >= 0);
    r.tools = tools;
    keep.keys.forEach(k => { r.snap[k] = keep.snap[k]; });
    r.mem = Object.assign({}, res.mem, keep.mem);       /* la photographie reste celle d'avant le premier remplacement : ses images aussi */
  }
  SUITE.restore = r;
  /* la référence de « Restaurer » : le stockage relu une fois les outils rouverts calmes */
  suiteTake(r);
  showToast(toast + ' ·', { action: { label: t('ui.restore'), fn: () => suiteRestore(r) }, ms: 12000 });
  SUITE.toastN = showToast._n;
  return r;
}
/* La référence de « Restaurer » : prise après le calme, compté à partir de l'appel ; une prise plus récente remplace la précédente (r.n). r.pending est vrai tant qu'une prise est en cours. */
function suiteTake(r) {
  const n = ++r.n;
  r.pending = suiteSettled().then(() => { if (r.n === n) { r.ref = suiteRead(); r.pending = null; } });
}
/* Au « load » de l'iframe d'un des outils de la restauration en attente (rouverte par l'ouverture ou ouverte ensuite) : ses écritures de démarrage différées partent tout de suite (MP_FLUSH), puis la référence est reprise,
   calme compté depuis ce load. Un outil d'un autre groupe ne touche aucune clé de la portée : il ne reprend rien. */
function suiteOnLoad(id) {
  const gm = SUITE.give[id];
  if (gm) {
    delete SUITE.give[id];
    try { const w = iframes[id] && iframes[id].contentWindow; if (w && typeof w.MP_IMG_GIVE === 'function') w.MP_IMG_GIVE(gm); }
    catch (e) { console.warn('[M·P] image de ' + id + ' : ' + e); }
  }
  const r = suiteLive();
  if (!r || r.tools.indexOf(id) < 0) return;
  suiteFlush(id);
  r.ref = null;
  suiteTake(r);
}
window.MP_WORK_OPEN_TEXT = function (text, name) {
  let o;
  try { o = JSON.parse(text); } catch (e) { console.warn('[M·P] fichier de travail : JSON illisible', e); showToast(t('work.err.json'), { type: 'err' }); return false; }
  const isObj = v => !!v && typeof v === 'object' && !Array.isArray(v);
  if (!isObj(o) || o.format !== SUITE_FORMAT || !isObj(o.keys) || Object.keys(o.keys).some(k => typeof o.keys[k] !== 'string')) { showToast(t('work.err.format'), { type: 'err' }); return false; }
  if (!SUITE_KEYS.some(k => typeof o.keys[k] === 'string')) { showToast(t('work.err.empty'), { type: 'err' }); return false; }
  const next = {};
  SUITE_KEYS.forEach(k => { next[k] = typeof o.keys[k] === 'string' ? o.keys[k] : null; });
  return !!suiteDo(next, SUITE_KEYS, SUITE_DROP, t('work.opened').replace('{0}', String(name || '')));
};
/* L'exemple d'un groupe : les clés du groupe prennent la valeur de l'exemple de la langue du shell (ou sont retirées si l'exemple ne les porte pas), les outils du groupe seuls sont rouverts ;
   les autres outils gardent leur iframe et leurs clés. */
window.MP_WORK_EXAMPLE = function (g) {
  const grp = SUITE_GROUPS[g];
  if (!grp) { console.warn('[M·P] exemple : groupe inconnu ' + g); return false; }
  if (typeof adoptStoredLang === 'function') adoptStoredLang();       /* la langue se lit au clic : le drapeau d'un outil n'est relu par le shell qu'à l'ouverture d'un outil */
  const ex = SUITE_EXAMPLES[CURRENT_LANG === 'en' ? 'en' : 'fr'], next = {};
  grp.keys.forEach(k => { next[k] = typeof ex.keys[k] === 'string' ? ex.keys[k] : null; });
  return !!suiteDo(next, grp.keys, grp.tools, t('work.example.' + g));
};
window.MP_WORK_OPEN = function () {
  const inp = document.createElement('input');
  inp.type = 'file';
  inp.accept = '.json,application/json';
  inp.addEventListener('change', () => {
    const f = inp.files && inp.files[0];
    if (!f) return;
    const rd = new FileReader();
    rd.onload = () => window.MP_WORK_OPEN_TEXT(String(rd.result), f.name);
    rd.onerror = () => showToast(t('work.err.json'), { type: 'err' });
    rd.readAsText(f);
  });
  inp.click();
};
/* « Restaurer » : refusé si une clé a changé depuis la référence (une saisie, un autre geste) ; sinon la photographie revient, par le même chemin que l'ouverture, sans nouveau « Restaurer » */
async function suiteRestore(r) {
  if (SUITE.restore !== r) return;
  while (r.pending) { await r.pending; if (SUITE.restore !== r) return; }
  const now = suiteRead(r.keys);
  if (r.keys.some(k => now[k] !== r.ref[k])) { SUITE.restore = null; showToast(t('ui.restore.refused'), { type: 'err' }); return; }
  SUITE.restore = null;
  if (!suiteReplace(r.snap, r.tools, r.keys, r.mem).ok) showToast(t('work.err.full'), { type: 'err' });
}
"""

_HTML = r"""<div class="ui-modal" id="mp-work-modal" hidden role="dialog" aria-labelledby="mp-work-title" aria-modal="true">
  <div class="ui-backdrop" id="mp-work-backdrop"></div>
  <div class="ui-panel" role="document">
    <button type="button" class="ui-close" id="mp-work-close" data-i18n-aria="ui.close" aria-label="Fermer">×</button>
    <h2 class="ui-title" id="mp-work-title" data-i18n="work.name.title">Sauvegarder le travail</h2>
    <div class="ui-field"><label class="ui-lbl" for="mp-work-name" data-i18n="work.name.label">Nom du fichier</label><div class="ui-row"><input class="ui-in" id="mp-work-name" type="text" autocomplete="off" autocapitalize="off" spellcheck="false" maxlength="100"><span class="ui-ext">.json</span></div></div>
    <div class="ui-actions">
      <button type="button" class="ui-btn" id="mp-work-cancel" data-i18n="ui.cancel">Annuler</button>
      <button type="button" class="ui-btn primary" id="mp-work-go" data-i18n="work.save.btn">Sauvegarder</button>
    </div>
  </div>
</div>
"""


def build_block():
    """Le script du bloc, délimité par ses deux commentaires, terminé par un saut de ligne."""
    return BLOCK_BEGIN + _JS + BLOCK_END + '\n'


def build_html():
    """La fenêtre du nom, précédée de son commentaire, terminée par un saut de ligne."""
    return HTML_BEGIN + '\n' + _HTML


def build_css():
    """Les variables de couleur et de police de ui_block et messages_block, thème par thème, posées sur la fenêtre du nom et sur #toast."""
    out = [CSS_BEGIN]
    for th, vs in THEME_VARS.items():
        out.append('[data-theme="%s"] #mp-work-modal, [data-theme="%s"] #toast {' % (th, th))
        out.append('  ' + ' '.join('%s: %s;' % (k, v) for k, v in vs.items()))
        out.append('}')
    out.append(CSS_END)
    return '\n'.join(out) + '\n'


if __name__ == '__main__':
    print(f"[OK] bloc du fichier de travail : script {len(build_block())} caractères, fenêtre {len(build_html())}, feuille {len(build_css())}")
