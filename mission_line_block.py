#!/usr/bin/env python3
"""Bloc « LIGNE DE LA MISSION D'HQ » : la ligne fixe sous la barre qui dit qu'un .miz est chargé dans HQ, lequel (date, heure de départ, fichier) et ce que l'outil en prend.
Écrit une fois, injecté tel quel dans le Flight Configurator, le Route Planner et le Datacard Generator.

Trois textes, identiques à l'octet dans les trois dist/ :
  build_block() — le script : lecture de mission_snapshot_v1 (la mission d'HQ, lue ici comme le bloc d'import lit la sienne), texte FR et EN, la ligne
  build_css()   — la feuille : la ligne (position, jetons des thèmes), --mp-top (le haut du contenu), l'impression
  verify(html)  — le garde-fou de build

La ligne est un <div class="mp-ml" role="status"> posé juste après .toolbar ; il est caché sans mission (hidden) et la classe mp-ml-on du <body> pose --mp-top à 86 px
(60 px sans elle) : le contenu (.app) prend top: var(--mp-top, 60px). Elle se lit par textContent seulement (le nom de fichier vient du disque).

Le module lui donne, par mlSetup({ lang, read, theatreName, livery, importDetail, onLayout }) :
  lang()          'fr' | 'en'
  read()          { theatre, src, calc } : son théâtre courant, la src de son propre appel à magYearSource, et vrai s'il emploie une déclinaison calculée
                  (cap magnétique à déclinaison calculée) : sans elle, aucun élément de déclinaison
  theatreName(id) le nom du théâtre dans la langue du module
  livery          vrai au Flight Configurator seul (l'élément « Livrées »)
  importDetail    vrai au Datacard Generator seul (« (date, heure, météo) » dans l'élément d'import)
  onLayout()      facultatif : rappelé quand la ligne paraît ou disparaît (le contenu change de hauteur)
et appelle mlRefresh() partout où il refait déjà ce qu'il montre de l'année et de son théâtre.

Il lit magvar_block.py (magRouteDate : la date d'une mission, lisible ou rien).

Usage (par les builds) : from mission_line_block import build_block, build_css, verify
"""

import json
import re

BLOCK_BEGIN = "/* ===== LIGNE DE LA MISSION D'HQ ===== */"
BLOCK_END = "/* ===== FIN DE LA LIGNE DE LA MISSION D'HQ ===== */"
CSS_BEGIN = "/* ===== LIGNE DE LA MISSION D'HQ : feuille ===== */"
CSS_END = "/* ===== FIN DE LA FEUILLE DE LA LIGNE ===== */"

# Les textes, au caractère près : [large, étroit]. {n} : le nombre de vols, {u} : « vol » ou « vols » (« flight », « flights »).
TEXTS = {
    'fr': {
        'lbl': 'MISSION D’HQ',
        'decl': ['Déclinaison ✓', 'Déclinaison'],
        'forcee': ['Déclinaison : année forcée', 'Décl. forcée'],
        'liv': ['Livrées ✓', 'Livrées'],
        'imp': ['Import : {n} {u} ✓', '{n} {u}'],
        'impd': ['Import : {n} {u} (date, heure, météo) ✓', '{n} {u}'],
        'one': 'vol',
        'many': 'vols',
        'out': ['Non utilisée ici : autre théâtre', 'Autre théâtre'],
    },
    'en': {
        'lbl': 'HQ MISSION',
        'decl': ['Declination ✓', 'Declination'],
        'forcee': ['Declination: year overridden', 'Decl. overridden'],
        'liv': ['Liveries ✓', 'Liveries'],
        'imp': ['Import: {n} {u} ✓', '{n} {u}'],
        'impd': ['Import: {n} {u} (date, time, weather) ✓', '{n} {u}'],
        'one': 'flight',
        'many': 'flights',
        'out': ['Not used here: other theatre', 'Other theatre'],
    },
}

# La seule couleur écrite en dur : la surcharge de contraste de la suite (MP-20), au thème cw-nato, pour l'étiquette
MP20_COLOR = '#c49037'

_CSS = r"""
:root { --mp-top: 60px; }
body.mp-ml-on { --mp-top: 86px; }
.mp-ml {
  position: fixed; top: 60px; left: 0; right: 0; height: 26px; z-index: 900; box-sizing: border-box; margin: 0; padding: 0 14px;
  display: flex; align-items: center; gap: 10px; overflow: hidden; white-space: nowrap;
  background: var(--olive-dark); border-bottom: 1px solid var(--amber); color: var(--paper);
  font-size: 11px; line-height: 25px;
}
.mp-ml[hidden] { display: none; }
.mp-ml.narrow { gap: 8px; padding: 0 10px; }
.mp-ml > span { flex: none; }
.mp-ml > .mp-ml-dot { width: 8px; height: 8px; box-sizing: border-box; border-radius: 50%; background: var(--amber); }
.mp-ml > .mp-ml-lbl { font-family: 'Oswald', 'Arial Narrow', sans-serif; font-weight: 700; font-size: 11px; letter-spacing: 1.5px; }
.mp-ml-lbl { color: var(--amber); }
:where(body[data-theme="cw-nato"]) .mp-ml-lbl { color: @@MP20@@; }
.mp-ml > .mp-ml-when, .mp-ml > .mp-ml-file { font-family: 'Roboto Mono', 'Courier New', monospace; font-weight: 400; font-size: 11px; }
.mp-ml > .mp-ml-file { flex: 0 1 auto; min-width: 0; overflow: hidden; text-overflow: ellipsis; }
.mp-ml > .mp-ml-file::before { content: '·'; margin-right: 10px; }
.mp-ml > .mp-ml-right { margin-left: auto; font-family: 'Oswald', 'Arial Narrow', sans-serif; font-weight: 500; font-size: 11px; letter-spacing: .5px; }
.mp-ml.warn { border-bottom-color: var(--mp-warn); }
.mp-ml.warn > .mp-ml-dot { background: transparent; border: 2px solid var(--mp-warn); }
.mp-ml.warn > .mp-ml-lbl, .mp-ml.warn > .mp-ml-right { color: var(--mp-warn); }
.mp-ml > .mp-ml-sr { position: absolute; width: 1px; height: 1px; margin: -1px; padding: 0; border: 0; overflow: hidden; clip: rect(0 0 0 0); clip-path: inset(50%); white-space: nowrap; }
@media print { .mp-ml { display: none !important; } }
"""

_JS = r"""
const ML_KEY = 'mission_snapshot_v1';
const ML_SCHEMAS = ['dcs-mission-snapshot-v1', 'dcs-mission-snapshot-v2'];       /* ceux de l'import (IMP_HQ_SCHEMAS) */
const ML_I18N = @@TEXTS@@;
const ML = { hooks: null, el: null, mq: null, raw: null, snap: null, sig: '', on: false };
function mlLang() { try { return ML.hooks.lang() === 'en' ? 'en' : 'fr'; } catch (e) { return 'fr'; } }
function mlPad(n) { return n < 10 ? '0' + n : String(n); }
/* La mission d'HQ, lue de la clé (relue seulement quand son texte change) : { theatre, file, date (AAAA-MM-JJ lisible, sinon ''), time (secondes, sinon -1), n (vols) } ou null */
function mlSnap() {
  let raw = null;
  try { raw = localStorage.getItem(ML_KEY); } catch (e) { raw = null; }
  if (raw === null) { ML.raw = null; ML.snap = null; return null; }
  if (raw !== ML.raw) {
    ML.raw = raw; ML.snap = null;
    try {
      const o = JSON.parse(raw), sm = o && typeof o === 'object' ? o.sourceMission : null;
      if (ML_SCHEMAS.indexOf(o.schema) >= 0 && Array.isArray(o.flights) && sm && typeof sm === 'object' && typeof sm.theatre === 'string' && sm.theatre !== '') {
        ML.snap = {
          theatre: sm.theatre, file: typeof sm.filename === 'string' ? sm.filename : '', date: magRouteDate(sm.missionDate),
          time: (typeof sm.startTime === 'number' && isFinite(sm.startTime) && sm.startTime >= 0) ? sm.startTime : -1,
          n: o.flights.length
        };
      }
    } catch (e) { ML.snap = null; }
  }
  return ML.snap;
}
/* Les éléments de droite d'une mission utilisée, dans l'ordre : déclinaison (seulement si le module l'emploie, calculée), livrées (FC), import ; w : 0 large, 1 étroit */
function mlItems(h, st, sn, tx, w) {
  const items = [];
  if (st.calc && st.src === 'mission') items.push(tx.decl[w]);
  else if (st.calc && st.src === 'forced') items.push(tx.forcee[w]);
  if (h.livery) items.push(tx.liv[w]);
  if (sn.n > 0) items.push(tx[h.importDetail ? 'impd' : 'imp'][w].replace('{n}', String(sn.n)).replace('{u}', sn.n === 1 ? tx.one : tx.many));
  return items;
}
function mlShow(on) {
  if (ML.el) ML.el.hidden = !on;
  document.body.classList.toggle('mp-ml-on', on);
  if (on !== ML.on) { ML.on = on; if (!on) ML.sig = ''; try { if (ML.hooks.onLayout) ML.hooks.onLayout(); } catch (e) { /* facultatif */ } }
}
function mlSpan(cls, text) { const s = document.createElement('span'); s.className = cls; s.textContent = text; s.setAttribute('aria-hidden', 'true'); return s; }
function mlRefresh() {
  const h = ML.hooks;
  if (!h || !ML.el) return;
  const sn = mlSnap();
  if (!sn) { mlShow(false); return; }
  let st = null;
  try { st = h.read() || null; } catch (e) { st = null; }       /* le module ne dit rien : ni « utilisée » ni « hors », partie droite vide */
  const lang = mlLang(), tx = ML_I18N[lang], wide = !ML.mq || ML.mq.matches, w = wide ? 0 : 1;
  const used = st ? sn.theatre === st.theatre : null;
  const right = used === null ? '' : (used ? mlItems(h, st, sn, tx, w).join(' · ') : tx.out[w]);
  let name = sn.theatre;
  try { name = h.theatreName(sn.theatre) || name; } catch (e) { /* le nom brut */ }
  const dateWide = sn.date === '' ? '' : sn.date.slice(8, 10) + '.' + sn.date.slice(5, 7) + '.' + sn.date.slice(0, 4);
  const dateNarrow = sn.date === '' ? '' : sn.date.slice(8, 10) + '.' + sn.date.slice(5, 7) + '.' + sn.date.slice(2, 4);
  const hhmm = sn.time < 0 ? '' : mlPad(Math.floor(sn.time / 3600) % 24) + ':' + mlPad(Math.floor(sn.time / 60) % 60) + 'Z';
  const when = [wide ? dateWide : dateNarrow, hhmm].filter(x => x !== '').join(' · ');
  const file = sn.file === '' ? name : sn.file + ' (' + name + ')';
  /* le texte large complet, quelle que soit la largeur : l'étiquette, date · heure, fichier (théâtre), puis les éléments de droite ou « hors » */
  const aria = [tx.lbl, [dateWide, hhmm].filter(x => x !== '').join(' · '), file, used === null ? '' : (used ? mlItems(h, st, sn, tx, 0).join(' · ') : tx.out[0])].filter(x => x !== '').join(' · ');
  const sig = JSON.stringify([lang, wide, used, when, file, right, aria]);
  if (sig === ML.sig && !ML.el.hidden) return;
  ML.sig = sig;
  const el = ML.el;
  el.textContent = '';
  el.classList.toggle('warn', used === false);
  el.classList.toggle('narrow', !wide);
  el.setAttribute('aria-label', aria);
  const dot = document.createElement('span');
  dot.className = 'mp-ml-dot';
  dot.setAttribute('aria-hidden', 'true');
  el.appendChild(dot);
  if (wide) el.appendChild(mlSpan('mp-ml-lbl', tx.lbl));
  if (when !== '') el.appendChild(mlSpan('mp-ml-when', when));
  if (wide) el.appendChild(mlSpan('mp-ml-file', file));
  if (right !== '') el.appendChild(mlSpan('mp-ml-right', right));
  const sr = document.createElement('span');       /* ce que lit le lecteur d'écran : le texte large complet ; les parties visibles sont masquées au lecteur */
  sr.className = 'mp-ml-sr';
  sr.textContent = aria;
  el.appendChild(sr);
  mlShow(true);
}
function mlSetup(hooks) {
  ML.hooks = hooks;
  const tb = document.querySelector('.toolbar');
  if (!tb || ML.el) return;
  const el = document.createElement('div');
  el.className = 'mp-ml';
  el.setAttribute('role', 'status');
  el.hidden = true;
  tb.insertAdjacentElement('afterend', el);
  ML.el = el;
  ML.mq = window.matchMedia('(min-width: 760px)');
  if (ML.mq.addEventListener) ML.mq.addEventListener('change', mlRefresh); else if (ML.mq.addListener) ML.mq.addListener(mlRefresh);
  window.addEventListener('storage', e => { if (e.key === ML_KEY || e.key === null) mlRefresh(); });
  document.addEventListener('visibilitychange', () => { if (document.visibilityState === 'visible') mlRefresh(); });
  mlRefresh();
}
"""


def build_block():
    """Le script du bloc, délimité par ses deux commentaires, terminé par un saut de ligne."""
    return BLOCK_BEGIN + _JS.replace('@@TEXTS@@', json.dumps(TEXTS, ensure_ascii=False)) + BLOCK_END + '\n'


def build_css():
    """La feuille du bloc, délimitée par ses deux commentaires, terminée par un saut de ligne."""
    return CSS_BEGIN + _CSS.replace('@@MP20@@', MP20_COLOR) + CSS_END + '\n'


def _fn_body(html, name):
    """Le texte de la fonction JavaScript `name` du livrable : sa ligne si elle tient sur une ligne, sinon jusqu'à l'accolade fermante en tête de ligne."""
    i = html.find('function %s(' % name)
    if i < 0:
        return ''
    j = html.find('\n', i)
    line = html[i:j]
    if line.rstrip().endswith('}'):
        return line
    k = html.find('\n}', i)
    return html[i:k + 2] if k >= 0 else ''


def verify(html, fn, reads, calls):
    """Garde-fou de build, par module : le bloc (feuille et script) est dans le livrable, tel quel et une fois ; le contenu prend son haut de --mp-top ;
    une seule couleur écrite en dur (la surcharge MP-20) ; textes FR et EN de mêmes clés ; la ligne s'initialise une fois ; la fonction que le module donne (fn)
    lit la source de l'année de son propre appel (reads : navYear( au Route Planner, dgNavYear( au Datacard Generator, declSource( au Flight Configurator) ;
    le module rafraîchit la ligne exactement `calls` fois (les appels mlRefresh() hors du bloc) ; magRouteDate, que le bloc lit, est dans la page ;
    les schémas lus sont ceux de l'import."""
    if html.count(build_css()) != 1 or html.count(build_block()) != 1:
        raise SystemExit("[ERREUR] ligne de la mission d'HQ : bloc absent du livrable, modifié ou en double")
    apps = re.findall(r'(?m)^\s*\.app\s*\{[^}]*\}', html)
    bad = [a for a in apps if 'top:' in a and 'var(--mp-top, 60px)' not in a]
    if not apps or bad or not any('var(--mp-top, 60px)' in a for a in apps):
        raise SystemExit("[ERREUR] ligne de la mission d'HQ : une règle .app ne prend pas son haut de var(--mp-top, 60px) : %s" % bad)
    if html.count('mlSetup({') != 1:
        raise SystemExit("[ERREUR] ligne de la mission d'HQ : mlSetup n'est pas appelée exactement une fois")
    body = _fn_body(html, fn)
    if not body or reads not in body:
        raise SystemExit("[ERREUR] ligne de la mission d'HQ : %s ne lit pas %s (corps : %r)" % (fn, reads, body[:120]))
    if 'read: %s,' % fn not in html:
        raise SystemExit("[ERREUR] ligne de la mission d'HQ : mlSetup ne reçoit pas %s" % fn)
    n = len(re.findall(r'\bmlRefresh\(\)', html)) - len(re.findall(r'\bmlRefresh\(\)', build_block()))
    if n != calls:
        raise SystemExit("[ERREUR] ligne de la mission d'HQ : %d appels mlRefresh() hors du bloc, %d attendus" % (n, calls))
    if 'function magRouteDate(' not in html:
        raise SystemExit("[ERREUR] ligne de la mission d'HQ : magRouteDate, que le bloc lit, n'est pas dans la page")
    colors = set(c.lower() for c in re.findall(r'#[0-9a-fA-F]{3,8}\b', _CSS.replace('@@MP20@@', MP20_COLOR)))
    if colors != {MP20_COLOR}:
        raise SystemExit("[ERREUR] ligne de la mission d'HQ : couleurs écrites en dur autres que la surcharge MP-20 : %s" % sorted(colors))
    if set(TEXTS['fr']) != set(TEXTS['en']):
        raise SystemExit("[ERREUR] ligne de la mission d'HQ : les textes FR et EN n'ont pas les mêmes clés")
    if 'textContent' not in _JS or 'innerHTML' in _JS:
        raise SystemExit("[ERREUR] ligne de la mission d'HQ : le texte doit s'écrire par textContent seulement")
    m = re.search(r"const IMP_HQ_SCHEMAS = (\[.*?\]);", html)
    m2 = re.search(r"const ML_SCHEMAS = (\[.*?\]);", html)
    if not m or not m2 or m.group(1) != m2.group(1):
        raise SystemExit("[ERREUR] ligne de la mission d'HQ : ses schémas ne sont pas ceux de l'import (IMP_HQ_SCHEMAS)")
    print("[OK] ligne de la mission d'HQ : bloc inséré tel quel (script %d, feuille %d caractères), .app prend son haut de --mp-top, %s lit %s, %d appels mlRefresh()" % (len(build_block()), len(build_css()), fn, reads, calls))


if __name__ == '__main__':
    print("[OK] bloc de la ligne de la mission d'HQ : script %d caractères, feuille %d" % (len(build_block()), len(build_css())))
