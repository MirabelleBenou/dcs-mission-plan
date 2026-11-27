"""La barre du haut, étapes 7 et 8 (« ⋯ » puis les écarts serrés) : la règle de uiBarFit (texte commun de ui_block, build_bar_js) jouée par node sur une barre fabriquée
(des enfants à largeur donnée, aucun navigateur, aucun réseau) ; et ce même texte, à l'octet, dans les huit livrables."""
import base64
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tests'))
from ui_block import build_bar_js  # noqa: E402
from banc_attente import attendre, attendre_barre_prete, attendre_barre_stable, attendre_fenetre  # noqa: E402

NODE = shutil.which('node')
needs_node = pytest.mark.skipif(NODE is None, reason='node absent')

# Une barre fabriquée : la même suite d'enfants que celle d'un outil (retour, sigle, fichiers, séparateur, Affichage, théâtre, Effacer, ressort, langue).
# La largeur de chaque enfant suit les étapes de la séquence (le texte part à l'étape 5, le titre à l'étape 6) ; scrollWidth = marges + enfants affichés + écarts.
HARNESS = r"""
class Cls {
  constructor(e, init) { this.e = e; this.s = new Set(init); }
  add(...c) { c.forEach(x => this.s.add(x)); } remove(...c) { c.forEach(x => this.s.delete(x)); }
  contains(c) { return this.s.has(c); } toggle(c, on) { if (on === undefined) on = !this.s.has(c); on ? this.s.add(c) : this.s.delete(c); return on; }
}
function simple(e, sel) {
  sel = sel.trim();
  if (sel[0] === '.') return e.classList.contains(sel.slice(1));
  if (sel[0] === '#') return e.id === sel.slice(1);
  if (sel[0] === '[') return e.hasAttribute(sel.slice(1, -1));
  return e.tagName.toLowerCase() === sel;
}
class El {
  constructor(tag, id, cls, w, extra) {
    this.tagName = tag.toUpperCase(); this.id = id; this.classList = new Cls(this, cls); this.w = w; this.attrs = {}; this.parentNode = null; this.disabled = false;
    Object.assign(this, extra || {});
  }
  get className() { return [...this.classList.s].join(' '); }
  set className(v) { this.classList = new Cls(this, v.split(' ').filter(Boolean)); }
  matches(sel) { return sel.split(',').some(s => simple(this, s)); }
  hasAttribute(a) { return a in this.attrs; } setAttribute(a, v) { this.attrs[a] = String(v); } removeAttribute(a) { delete this.attrs[a]; } getAttribute(a) { return a in this.attrs ? this.attrs[a] : null; }
  get previousElementSibling() { const k = this.parentNode.children, i = k.indexOf(this); return i > 0 ? k[i - 1] : null; }
  get nextElementSibling() { const k = this.parentNode.children, i = k.indexOf(this); return i >= 0 && i < k.length - 1 ? k[i + 1] : null; }
  addEventListener() {} querySelector() { return null; } remove() {}
  getBoundingClientRect() { return rectOf(this); }
  get hidden() { return !!this.hid; }
  get isConnected() { return true; }
  set textContent(v) { this._t = v; } get textContent() { return this._t || ''; }
}
let FRAC = 0;                                  /* une part fractionnaire ajoutée à la largeur des boutons et des listes (le texte réel n'a pas de largeur entière) */
function width(e, bar) {                     /* la largeur d'un enfant à l'étape où se trouve la barre */
  const c = n => bar.classList.contains(n);
  if (e.classList.contains('tb-label')) return c('tb-st3') ? 0 : 60 + FRAC;
  if (e.classList.contains('tb-brand')) return c('tb-st6') ? 34 : 220;
  if (e.classList.contains('tb-sep') || e.classList.contains('tb-files-end')) return c('tb-st6') ? 0 : 1;
  if (e.classList.contains('tb-more-btn') || e.classList.contains('tb-lang-btn') || e.classList.contains('mp-back-injected')) return 44;
  if (e.classList.contains('tbm-trigger')) return 80 + FRAC;
  if (e.id === 'btn-display') return c('tb-st4') ? 44 : 120 + FRAC;
  if (e.classList.contains('tb-btn')) return c('tb-st5') ? 44 : 130 + FRAC;
  return e.w;
}
function shown(e) { return !('data-mp-off' in e.attrs) && !e.hid && !e.baseNone; }
const bar = new El('header', '', ['toolbar'], 0);
bar.children = []; bar.scrollLeft = 0;
bar.appendChild = e => { const i = bar.children.indexOf(e); if (i >= 0) bar.children.splice(i, 1); e.parentNode = bar; bar.children.push(e); return e; };     /* comme le DOM : un enfant déjà là est déplacé */
Object.defineProperty(bar, 'lastElementChild', { get: () => bar.children[bar.children.length - 1] || null });
bar.querySelectorAll = sel => bar.children.filter(e => e.matches(sel));
Object.defineProperty(bar, 'clientWidth', { get: () => bar.cw });
const FADE = 20;                              /* le fondu du shell (mp-fade-r) est un élément de la barre : sa largeur entre dans scrollWidth tant que la classe est là */
const pads = () => { const t8 = bar.classList.contains('tb-st8'); return { gap: t8 ? 2 : 8, pad: t8 ? 2 : 14 }; };
function content() {                         /* le bord droit du dernier enfant affiché, marge de début comprise (sans la marge de fin) */
  const { gap, pad } = pads();
  const vis = bar.children.filter(e => shown(e) && width(e, bar) > 0);
  return pad + vis.reduce((a, e) => a + width(e, bar), 0) + gap * Math.max(0, vis.length - 1) + (bar.classList.contains('mp-fade-r') ? FADE + gap : 0);
}
Object.defineProperty(bar, 'scrollWidth', { get: () => {
  const { pad } = pads(), own = content() + pad;
  /* barre défilante (celle du shell) : la marge de fin compte ; « visible » (tb-nos, posé une fois la décision prise) : elle ne compte pas ; comme le vrai, scrollWidth est arrondi à l'entier */
  return Math.round(bar.classList.contains('tb-nos') ? Math.max(bar.cw, own - pad) : Math.max(bar.cw, own));
} });
/* les positions, au sous-pixel : les enfants affichés (largeur non nulle) se suivent, la marge de début puis les écarts */
function rectOf(e) {
  const { gap, pad } = pads(); let x = pad;
  for (const k of bar.children) { if (!shown(k) || width(k, bar) <= 0) continue; if (k === e) return { left: x, right: x + width(k, bar), width: width(k, bar) }; x += width(k, bar) + gap; }
  return { left: 0, right: 0, width: 0 };
}
bar.getBoundingClientRect = () => ({ left: 0, right: bar.cw, width: bar.cw });
function build(kind) {
  const L = [['button', '', ['mp-back-injected'], 44], ['div', '', ['tb-brand'], 220], ['button', 'btn-open', ['tb-btn', 'tb-file'], 130], ['button', 'btn-save', ['tb-btn', 'tb-file'], 130],
    ['button', 'btn-export', ['tb-btn', 'tb-file'], 130], ['div', '', ['tb-sep', 'tb-files-end'], 1], ['button', 'btn-display', ['tb-btn'], 120]];
  const R = [['span', '', ['tb-label'], 60], ['button', '', ['tb-sel', 'tbm-trigger'], 80, { sel: 1 }], ['select', 'theatre', ['tb-sel'], 0, { baseNone: true }],
    ['button', 'btn-wing', ['tb-btn'], 130], ['button', 'btn-clear', ['tb-btn', 'danger'], 130], ['div', '', ['tb-spacer'], 0], ['button', 'btn-lang', ['tb-lang-btn'], 44]];
  const rows = kind === 'fm' ? [['button', '', ['mp-back-injected'], 44], ['div', '', ['tb-brand'], 220], ['button', 'btn-toc', ['tb-btn'], 130], ['div', '', ['tb-spacer'], 0], ['button', 'btn-lang', [], 44]]
    : kind === 'nolist' ? L.concat(R.filter(r => r[2][0] !== 'tb-sel' && r[2][0] !== 'tb-label')) : L.concat(R);
  rows.forEach(r => bar.appendChild(new El(r[0], r[1], r[2], r[3], r[4])));
}
globalThis.document = { activeElement: null, querySelector: s => s === '.toolbar' ? bar : null, readyState: 'complete', documentElement: { lang: 'fr' }, createElement: t => new El(t, '', [], 0), addEventListener() {}, body: { appendChild() {} } };
globalThis.window = { matchMedia: q => ({ matches: bar.narrow }), addEventListener() {} };
globalThis.getComputedStyle = e => e === bar ? { paddingRight: pads().pad + 'px', paddingLeft: pads().pad + 'px', borderRightWidth: '0px', borderLeftWidth: '0px', display: 'flex', color: '' }
  : ({ display: shown(e) && width(e, bar) > 0 ? 'block' : 'none', marginRight: '0px', color: '' });
bar.cw = 1000; bar.narrow = false;
build(process.env.KIND || 'normal');
"""

BAR = build_bar_js()


def run(body, kind='normal'):
    r = subprocess.run([NODE, '-e', HARNESS + '\n' + BAR + '\n' + body], capture_output=True, text=True, timeout=60, env={'KIND': kind, 'PATH': ''})
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


SNAP = r"""
const snap = () => ({
  steps: ['tb-st1', 'tb-st2', 'tb-st3', 'tb-st4', 'tb-st5', 'tb-st6'].filter(c => bar.classList.contains(c)).length,
  st7: bar.classList.contains('tb-st7'), st8: bar.classList.contains('tb-st8'), over: bar.classList.contains('tb-over'), nos: bar.classList.contains('tb-nos'), fade: bar.classList.contains('mp-fade-r'),
  end: bar.cw - content(), padEnd: pads().pad, last: bar.lastElementChild === UIMORE.btn || !UIMORE.btn,
  more: !!(UIMORE.btn && !('data-mp-off' in UIMORE.btn.attrs)),
  off: bar.children.filter(e => ('data-mp-off' in e.attrs) && e !== UIMORE.btn).map(e => e.id || e.className),
  left: bar.children.slice(0, 7).every(e => shown(e)),
  fits: bar.scrollWidth <= bar.clientWidth,
});
const fit = (w, narrow) => { bar.cw = w; bar.narrow = narrow; uiBarFit(); return snap(); };
"""


@needs_node
def test_les_six_etapes_d_abord_puis_rien_de_plus_qu_il_ne_faut():
    out = run(SNAP + """
const r = {};
for (const w of [1400, 1000, 800, 700]) r[w] = fit(w, false);
console.log(JSON.stringify(r));""")
    for w, s in out.items():
        assert not s['more'] and not s['st7'] and not s['st8'] and s['off'] == [], (w, s)
        assert s['fits'], (w, s)
    assert out['1400']['steps'] == 0 and 0 < out['800']['steps'] <= 6


@needs_node
def test_l_etape_7_fait_partir_le_dernier_d_abord_et_garde_le_groupe_de_gauche():
    out = run(SNAP + """
const seq = [];
for (let w = 700; w >= 330; w -= 5) { const s = fit(w, w < 760); seq.push([w, s]); }
console.log(JSON.stringify(seq));""")
    vus = []
    for w, s in out:
        assert s['left'], (w, s)                                      # ◄, le sigle, les fichiers et Affichage restent
        assert s['steps'] == 6 or not s['st7'], (w, s)                # l'étape 7 n'est prise qu'après les six
        assert s['more'] == s['st7'] == bool(s['off']), (w, s)        # « ⋯ » paraît quand quelque chose est parti, jamais autrement
        if s['off']:
            part = [x for x in s['off'] if x in ('btn-wing', 'btn-clear', 'btn-lang') or x.startswith('tb-sel')]
            # ce qui est parti est toujours la fin de la liste Théâtre, Wing, Effacer, langue
            fin = ['tb-sel tbm-trigger', 'btn-wing', 'btn-clear', 'btn-lang']
            assert part == fin[len(fin) - len(part):], (w, s)
            if part not in vus:
                vus.append(part)
    # une fenêtre plus étroite ne montre jamais plus : les parties s'allongent par la fin
    assert all(len(b) >= len(a) for a, b in zip(vus, vus[1:])), vus
    assert len(vus) >= 3, vus                                          # la barre fabriquée passe par plusieurs états


@needs_node
def test_l_etape_8_n_est_prise_qu_apres_le_depart_de_tout_ce_qui_peut_partir():
    out = run(SNAP + """
const seq = [];
for (let w = 700; w >= 250; w -= 2) { const s = fit(w, true); seq.push([w, s]); }
console.log(JSON.stringify(seq));""")
    trouve8 = False
    for w, s in out:
        if s['st8']:
            trouve8 = True
            assert s['st7'] and s['steps'] == 6, (w, s)
            assert s['off'].count('btn-lang') == 1 and 'btn-clear' in s['off'] and 'btn-wing' in s['off'] and any(x.startswith('tb-sel') for x in s['off']), (w, s)
        if s['st7'] and not s['st8']:
            assert s['fits'], (w, s)
        if s['fits'] and not s['st8']:
            continue
        if not s['fits']:
            assert s['st8'] and s['over'], (w, s)                      # il ne tient plus du tout : « tb-over » (la barre redéfile, « ⋯ » reste atteignable)
    assert trouve8


@needs_node
def test_la_decision_ne_depend_pas_de_l_etat_d_avant():
    out = run(SNAP + """
const largeurs = [420, 360, 345, 520, 330, 412, 345, 700, 345];
const ref = {};
for (const w of [330, 345, 360, 412, 420, 520, 700]) { ref[w] = fit(w, w < 760); }
const apres = {};
for (const w of largeurs) apres[w] = fit(w, w < 760);
console.log(JSON.stringify({ ref, apres }));""")
    for w, s in out['apres'].items():
        assert s == out['ref'][w], (w, s, out['ref'][w])


@needs_node
def test_une_barre_sans_groupe_de_fichiers_ne_perd_rien():
    out = run(SNAP.replace("bar.children.slice(0, 7).every(e => shown(e))", "bar.children.every(e => shown(e))") + """
const r = {};
for (const w of [345, 300, 250]) r[w] = fit(w, true);
console.log(JSON.stringify(r));""", kind='fm')
    for w, s in out.items():
        assert not s['more'] and s['off'] == [] and not s['st7'] and not s['st8'], (w, s)


@needs_node
def test_une_barre_sans_liste_part_dans_le_meme_ordre():
    out = run(SNAP + """
const seq = [];
for (let w = 420; w >= 330; w -= 5) seq.push([w, fit(w, true)]);
console.log(JSON.stringify(seq));""", kind='nolist')
    for w, s in out:
        part = [x for x in s['off'] if x in ('btn-wing', 'btn-clear', 'btn-lang')]
        assert part == ['btn-wing', 'btn-clear', 'btn-lang'][3 - len(part):], (w, s)


def test_le_texte_commun_est_le_meme_dans_les_huit_livrables():
    for f in ('dcs_hq.html', 'dcs_route_planner.html', 'dcs_briefing_generator.html', 'dcs_datacard_generator.html', 'dcs_flight_configurator.html',
              'dcs_recon_station.html', 'dcs_field_manual.html'):
        html = (ROOT / 'dist' / f).read_text(encoding='utf-8')
        assert BAR in html, f
        assert html.count('function uiBarMore(') == 1, f
    # le shell embarque les outils sous leur forme codée (base64 de leur HTML) : on les décode et le texte y est, une fois par outil (les sept du mur)
    shell = (ROOT / 'dist' / 'dcs_mission_plan.html').read_text(encoding='utf-8')
    vus = 0
    for blob in re.findall(r'[A-Za-z0-9+/=]{20000,}', shell):
        try:
            html = base64.b64decode(blob).decode('utf-8')
        except Exception:
            continue
        if 'function uiBarFit(' in html:
            assert BAR in html and html.count('function uiBarMore(') == 1
            vus += 1
    assert vus == 7, vus


def test_l_etape_8_serre_tout_espace_entre_enfants_a_2_px():
    from ui_block import build_bar_css
    css = build_bar_css()
    assert '.toolbar.tb-st8 { column-gap: 2px !important; padding-left: 2px !important; padding-right: 2px !important; }' in css
    assert '.toolbar.tb-st8 > * { margin-left: 0 !important; margin-right: 0 !important; }' in css      # ressort (marge négative du RP comprise) et ◄ (marge posée par le shell)
    for f in ('dcs_hq.html', 'dcs_route_planner.html', 'dcs_field_manual.html'):
        assert css in (ROOT / 'dist' / f).read_text(encoding='utf-8'), f


@needs_node
def test_la_decision_se_prend_barre_defilante_marge_de_fin_comprise():
    """Addendum 2, point 1 : « ⋯ » ne s'installe pas dans la marge de fin. La décision des étapes 7 et 8 se prend comme celle des étapes 1 à 6 (marge de fin dans scrollWidth) ;
    « visible » (tb-nos) ne se pose qu'une fois la décision prise et que tout tient."""
    out = run(SNAP + """
const seq = [];
for (let w = 700; w >= 250; w -= 1) { const s = fit(w, true); seq.push([w, s]); }
console.log(JSON.stringify(seq));""")
    vus7 = vus8 = 0
    for w, s in out:
        if s['st7'] and not s['over']:
            assert s['nos'], (w, s)                                    # tout tient : la barre ne défile plus
            assert s['end'] >= s['padEnd'] - 0.01, (w, s)             # le bord droit de « ⋯ » laisse la marge de fin (14 px, 2 px à l'étape 8)
            vus7 += 1
            vus8 += s['st8']
        if s['st7'] and s['over']:
            assert not s['nos'], (w, s)                                # il ne tient plus du tout : la barre défile (le shell)
        if not s['st7']:
            assert not s['nos'], (w, s)
    assert vus7 > 20 and vus8 > 5, (vus7, vus8)


@needs_node
def test_le_fondu_du_shell_n_entre_pas_dans_la_mesure_sous_760_px():
    """Addendum 2, point 9 : mp-fade-r se retire avant la mesure sous 760 px aussi ; la décision ne lit pas l'état d'avant (P3). Hors de l'étape 7, le fondu revient comme il était."""
    out = run(SNAP + """
const r = [];
for (let w = 600; w >= 330; w -= 1) {
  bar.classList.remove('mp-fade-r');
  const sans = fit(w, true);
  bar.classList.add('mp-fade-r');
  const avec = fit(w, true);
  r.push([w, sans, avec]);
}
for (const w of [800, 700, 650]) {                              // au-dessus de 760 px aussi
  bar.classList.remove('mp-fade-r'); const sans = fit(w, false);
  bar.classList.add('mp-fade-r'); const avec = fit(w, false);
  r.push([w, sans, avec]);
}
console.log(JSON.stringify(r));""")
    for w, sans, avec in out:
        a, b = dict(sans), dict(avec)
        for k in ('fade', 'end', 'fits'):                                   # la place libre et « tient » dépendent du fondu rendu après coup, pas la décision
            a.pop(k), b.pop(k)
        assert a == b, (w, sans, avec)
        assert avec['fade'] == (not avec['st7']), (w, avec)           # le fondu qui était là revient sauf à l'étape 7
        assert not sans['fade'], (w, sans)


@needs_node
def test_more_reste_le_dernier_enfant_de_la_barre():
    """Addendum 2, point 7 : le shell déplace #btn-lang en fin de barre au chargement de l'outil, après « ⋯ » : le recalcul remet « ⋯ » au bout."""
    out = run(SNAP + """
const r = {};
r.avant = fit(345, true);
const lang = bar.children.find(e => e.id === 'btn-lang');
bar.appendChild(lang);                                           // le geste du shell
r.deplace = bar.lastElementChild === lang;
r.apres = fit(345, true);
r.dernier = bar.lastElementChild === UIMORE.btn;
r.langue_parti = lang.hasAttribute('data-mp-off');
console.log(JSON.stringify(r));""")
    assert out['avant']['more'] and out['deplace'] and out['dernier'] and out['apres']['last'], out
    assert out['langue_parti'] and out['apres']['off'] == out['avant']['off'], out


@needs_node
def test_la_decision_des_etapes_7_et_8_se_prend_au_sous_pixel():
    """Addendum 3, point 2 : scrollWidth est arrondi à l'entier ; un « ⋯ » qui entre de 0,02 à 0,34 px dans la marge de fin tenait pour la base. La décision des étapes 7 et 8 se prend sur les positions,
    sans arrondi : le bord droit de « ⋯ » (et du dernier enfant) laisse la marge de fin entière, au sous-pixel, à toute largeur et quelle que soit la part fractionnaire des largeurs de texte."""
    out = run(SNAP + """
const r = [];
for (const f of [0, 0.11, 0.25, 0.37, 0.5, 0.63, 0.9]) {
  FRAC = f;
  for (let w = 700; w >= 250; w -= 1) { const s = fit(w, true); r.push([f, w, s, Math.round(content() + pads().pad) <= bar.cw]); }
}
console.log(JSON.stringify(r));""")
    vus = favorise = 0
    for f, w, s, arrondi in out:
        if s['st7'] and not s['over']:
            vus += 1
            assert s['end'] >= s['padEnd'] - 1e-9, (f, w, s)          # au sous-pixel : la marge de fin est entière
            assert s['nos'], (f, w, s)
        if s['st7'] and s['over']:
            assert s['st8'] and not s['nos'], (f, w, s)                  # il ne tient pas même serré : « tb-over »
    assert vus > 500, vus
    # la barre fabriquée sait montrer l'écart : des largeurs où l'arrondi de scrollWidth aurait fait tenir un « ⋯ » entré dans la marge
    out2 = run(SNAP + """
const r = [];
for (const f of [0.11, 0.37, 0.5]) {
  FRAC = f;
  for (let w = 700; w >= 250; w -= 1) {
    const s = fit(w, true);
    if (!s.st7) continue;
    /* l'état juste avant le dernier départ : si c'était l'arrondi qui décidait, serait-on resté plus tôt ? */
    r.push([f, w, s.end, s.padEnd]);
  }
}
console.log(JSON.stringify(r));""")
    assert any(0 <= end - pad < 1 for f, w, end, pad in out2), 'la barre fabriquée ne passe par aucune largeur où l\'arrondi compterait'


@needs_node
def test_la_decision_a_une_signature_stable():
    """Addendum 3, point 1 : un recalcul qui garde la même décision (les mêmes éléments dans « ⋯ », la même étape) laisse le menu ouvert ; la signature (UIMORE.sig) le dit."""
    out = run(SNAP + """
const r = { stable: [], par_largeur: {} };
for (let w = 700; w >= 330; w -= 1) {
  const a = fit(w, true), s1 = UIMORE.sig; fit(w, true); const s2 = UIMORE.sig; fit(w, true); const s3 = UIMORE.sig;
  r.stable.push([w, s1 === s2 && s2 === s3]);
  r.par_largeur[w] = s1;
}
r.sans_more = (() => { fit(1400, false); return UIMORE.sig; })();
console.log(JSON.stringify(r));""")
    assert all(ok for w, ok in out['stable']), [w for w, ok in out['stable'] if not ok]
    sigs = [out['par_largeur'][str(w)] for w in range(700, 329, -1)]
    assert len(set(sigs)) >= 4, set(sigs)                                  # elle change avec la décision (étape, éléments partis, étape 8)
    assert any(a == b for a, b in zip(sigs, sigs[1:])), 'elle ne change pas à chaque largeur'
    assert out['sans_more'].endswith(':'), out['sans_more']                # sans « ⋯ » : aucun élément parti


# ---------- le menu « ⋯ » dans un vrai DOM (Chromium) : une barre fabriquée avec la feuille et les scripts communs de ui_block ----------
CHROMIUM = Path('/opt/pw-browsers/chromium')
try:
    import playwright.sync_api  # noqa: F401
    HAS_PW = CHROMIUM.exists()
except ImportError:
    HAS_PW = False

FLAG = '<svg viewBox="0 0 20 14" width="20" height="14"><rect width="7" height="14" fill="#002395"/><rect x="7" width="6" height="14" fill="#fff"/><rect x="13" width="7" height="14" fill="#ed2939"/></svg>'
ICON = '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 7h16M9 7V4h6v3M6 7l1 13h10l1-13"/></svg>'


def page_html(extra=''):
    from ui_block import build_bar_css, build_bar_js, build_tbm_block, build_tbm_css
    css = ('<style>:root{--olive-dark:#2c2a1e;--olive-deep:#1f1d14;--olive:#3a3726;--amber:#c0892a;--amber-dark:#8a6420;--paper:#d8c9a5;--khaki:#807454;--khaki-light:#b8a878;--f-ui:sans-serif;--f-typewriter:monospace}'
           'body{margin:0;background:#1f1d14;color:#d8c9a5;font:13px sans-serif}'
           '.toolbar{display:flex;align-items:center;gap:8px;padding:0 14px;height:60px;box-sizing:border-box;overflow-x:auto;overflow-y:hidden}'
           '.tb-btn,.tb-sel{box-sizing:border-box;height:44px;min-height:44px;padding:0 12px;display:inline-flex;align-items:center;gap:6px;white-space:nowrap;flex:none;color:#d8c9a5;background:#2c2a1e;border:1px solid #8a6420}'
           '.tb-btn:disabled{color:#807454}.tb-lang-btn{width:44px;padding:0;justify-content:center}.tb-spacer{flex:1 0 0;margin-left:-10px}.tb-brand-short{display:none}.tb-sep{width:1px;height:20px;background:#807454}'
           '.tb-brand{white-space:nowrap}</style>'
           '<style>' + build_bar_css() + '</style><style>' + build_tbm_css() + '</style>')
    body = ('<header class="toolbar"><button class="tb-btn mp-back-injected" id="btn-back" style="width:44px;padding:0">&#9664;</button>'
            '<div class="tb-brand"><span class="tb-brand-main">Route Planner</span><span class="tb-brand-short">RP</span></div>'
            '<button class="tb-btn tb-file" id="btn-open">' + ICON + '<span class="tb-btn-label">Ouvrir</span></button>'
            '<button class="tb-btn tb-file" id="btn-save">' + ICON + '<span class="tb-btn-label">Sauvegarder</span></button>'
            '<button class="tb-btn tb-file" id="btn-export">' + ICON + '<span class="tb-btn-label">Exporter</span></button>'
            '<div class="tb-sep tb-files-end"></div>'
            '<button class="tb-btn" id="btn-display">' + ICON + '<span>Affichage</span></button>'
            '<span class="tb-label">Théâtre</span><select class="tb-sel" id="theatre"><option value="a">Syrie</option><option value="b">Allemagne</option><option value="c">Caucase</option></select>'
            '<button class="tb-btn danger" id="btn-clear">' + ICON + '<span class="tb-btn-label">Effacer</span></button>'
            '<div class="tb-spacer"></div>'
            '<button class="tb-lang-btn tb-btn" id="btn-lang">' + FLAG + '</button></header>'
            '<main style="padding:80px 8px"><button id="probe">probe</button></main>')
    js = ('<script>' + build_tbm_block() + '\nTBM.cfg = { others: () => {}, trig: ".tbm-trigger, #btn-display" };\n'
          'window.clicks = { probe: 0, display: 0, lang: 0 };\n'
          'document.getElementById("probe").addEventListener("click", () => window.clicks.probe++);\n'
          'document.getElementById("btn-display").addEventListener("click", () => window.clicks.display++);\n'
          'document.getElementById("btn-lang").addEventListener("click", () => window.clicks.lang++);\n'
          'initToolbarMenus([["theatre", () => "Théâtre", undefined, true]]);\n</script>'
          + extra + '<script>' + build_bar_js() + '</script>')
    return '<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">' + css + '</head><body>' + body + js + '</body></html>'


@pytest.mark.skipif(not HAS_PW, reason='playwright ou chromium absent')
def test_le_menu_dans_un_vrai_dom():
    """Addendum 2, points 1 à 8 sur une barre fabriquée à 345 px : marge de fin, toucher hors du menu, focus, icône grisée, ARIA, alignement, « ⋯ » dernier enfant, « ⋯ » comme déclencheur."""
    from playwright.sync_api import sync_playwright
    html = page_html()
    with sync_playwright() as p:
        br = p.chromium.launch(executable_path=str(CHROMIUM), args=['--no-sandbox'])
        try:
            def fresh(w=345):
                c = br.new_context(viewport={'width': w, 'height': 640}, has_touch=True, is_mobile=True)
                pg = c.new_page()
                errs = []
                pg.on('pageerror', lambda e: errs.append(str(e)))
                pg.set_content(html)
                attendre_barre_prete(pg)
                return c, pg, errs
            state = """() => { const tb = document.querySelector('.toolbar'), m = tb.querySelector('.tb-more-btn'), cs = getComputedStyle(tb), r = m && m.getBoundingClientRect();
              return { cls: [...tb.classList], padR: parseFloat(cs.paddingRight), cw: tb.clientWidth, right: r ? r.right : null, shown: !!(r && r.width > 0), last: tb.lastElementChild === m, active: document.activeElement === m, ox: cs.overflowX, id: m && m.id }; }"""
            menu = """() => { const p = document.querySelector('.tb-more-panel'); if (!p) return null; const r = p.getBoundingClientRect(), ul = p.querySelector('ul'), m = document.querySelector('.tb-more-btn').getBoundingClientRect();
              return { l: r.left, r: r.right, mr: m.right, W: document.documentElement.clientWidth, ulRole: ul.getAttribute('role'), panelRole: p.getAttribute('role'), lab: ul.getAttribute('aria-labelledby'),
                items: [...p.querySelectorAll('li')].map(li => ({ role: li.getAttribute('role'), txt: li.textContent.trim(), dis: li.getAttribute('aria-disabled'), tcol: getComputedStyle(li).color, icol: li.querySelector('svg') ? getComputedStyle(li.querySelector('svg')).color : null })) }; }"""
            panel = "() => !!document.querySelector('.tb-more-panel')"
            clicks = "() => ({ ...window.clicks })"
            liste = "!!document.querySelector('.tbm-panel:not(.tb-more-panel)')"

            def plus(on=True):             # le menu « ⋯ » est ouvert (ou fermé)
                attendre(pg, "!!document.querySelector('.tb-more-panel') === arg", 'le menu « ⋯ » %s' % ('ouvert' if on else 'fermé'), lu="!!document.querySelector('.tb-more-panel')", arg=on)
            for w in (345, 412):
                c, pg, errs = fresh(w)
                st = pg.evaluate(state)
                assert st['shown'] and st['last'] and st['id'] == 'tb-more-btn', (w, st)
                if 'tb-nos' in st['cls']:
                    assert st['right'] <= st['cw'] - st['padR'] + 0.01, (w, st)                  # point 1 : « ⋯ » n'est pas dans la marge de fin
                    assert st['ox'] == 'visible', (w, st)
                c.close()
            c, pg, errs = fresh(300)                                                                                 # la barre fabriquée est plus courte que celles des outils : l'étape 8 y paraît à 300 px
            st = pg.evaluate(state)
            assert 'tb-st8' in st['cls'] and st['padR'] == 2 and abs(st['right'] - (st['cw'] - 2)) < 0.01, st      # étape 8 : 2 px
            # 5, 6 : ARIA et alignement ; 4 : ligne grisée
            pg.evaluate("() => { document.getElementById('btn-clear').disabled = true; }"); attendre_barre_stable(pg)
            pg.locator('.tb-more-btn').tap(); plus(True)
            m = pg.evaluate(menu)
            assert m['ulRole'] == 'menu' and m['panelRole'] is None and m['lab'] == 'tb-more-btn', m                  # point 5
            assert all(i['role'] == 'menuitem' for i in m['items']), m
            assert abs(m['r'] - m['mr']) <= 0.5 and m['r'] <= m['W'] - 2 + 0.01 and m['l'] >= 2 - 0.01, m           # point 6
            grise = [i for i in m['items'] if i['dis'] == 'true']
            assert len(grise) == 1 and grise[0]['icol'] == grise[0]['tcol'], m                                     # point 4
            ok = [i for i in m['items'] if i['dis'] != 'true' and i['icol']]
            assert ok, m
            pg.evaluate("() => { document.getElementById('btn-clear').disabled = false; }"); attendre_barre_stable(pg)
            # 2 : « ⋯ » ouvert, un toucher sur un autre menu de la barre (Affichage) ferme « ⋯ » et ouvre ce menu, en un seul geste (son clic passe : ici il compte 1) ; la sonde, elle, ne reçoit pas le clic de fermeture
            if not pg.evaluate(panel):
                pg.locator('.tb-more-btn').tap(); plus(True)
            pg.locator('#btn-display').tap()
            attendre(pg, "!document.querySelector('.tb-more-panel') && window.clicks.display === 1", 'le menu « ⋯ » fermé et le clic d\'Affichage compté (1)', lu='[!!document.querySelector(".tb-more-panel"), window.clicks.display]')
            assert not pg.evaluate(panel) and pg.evaluate(clicks)['display'] == 1, pg.evaluate(clicks)
            pg.locator('.tb-more-btn').tap(); plus(True)
            pg.locator('#probe').tap()
            attendre(pg, '!document.querySelector(".tb-more-panel") && TBM.swallow === false', 'le menu « ⋯ » fermé et le clic de fermeture avalé (TBM.swallow retombé)', lu='[!!document.querySelector(".tb-more-panel"), TBM.swallow]')
            assert not pg.evaluate(panel) and pg.evaluate(clicks)['probe'] == 0
            pg.locator('#probe').tap()
            attendre(pg, 'window.clicks.probe === 1', 'le clic de la sonde compté (1)', lu='window.clicks.probe')
            assert pg.evaluate(clicks)['probe'] == 1
            # 3 : le théâtre choisi depuis « ⋯ » : le focus revient à « ⋯ » ; 8 : un toucher sur « ⋯ » liste ouverte ouvre le menu du premier coup
            pg.locator('.tb-more-btn').tap(); plus(True)
            pg.locator('.tb-more-panel li', has_text='Théâtre').first.tap()
            attendre(pg, liste, 'la liste du théâtre ouverte depuis « ⋯ »', lu=liste)
            assert pg.evaluate("() => !!document.querySelector('.tbm-panel:not(.tb-more-panel)')")
            pg.locator('.tb-more-btn').tap()
            attendre(pg, '!!document.querySelector(".tb-more-panel") && !(%s)' % liste, 'le menu « ⋯ » ouvert du premier coup, la liste fermée', lu='[!!document.querySelector(".tb-more-panel"), %s]' % liste)
            assert pg.evaluate(panel) and not pg.evaluate("() => !!document.querySelector('.tbm-panel:not(.tb-more-panel)')")
            pg.locator('.tb-more-panel li', has_text='Théâtre').first.tap()
            attendre(pg, liste, 'la liste du théâtre ouverte depuis « ⋯ »', lu=liste)
            pg.locator('.tbm-panel:not(.tb-more-panel) .tbm-opt', has_text='Allemagne').first.tap()
            attendre(pg, "document.getElementById('theatre').value === 'b' && document.activeElement === document.querySelector('.tb-more-btn')", 'le théâtre choisi (b) et le focus revenu à « ⋯ »',
                     lu="[document.getElementById('theatre').value, document.activeElement && document.activeElement.id]")
            assert pg.evaluate("() => document.getElementById('theatre').value") == 'b'
            st = pg.evaluate(state)
            assert st['active'] and st['shown'], st
            # 7 : le shell déplace #btn-lang en fin de barre : « ⋯ » revient au bout
            pg.evaluate("() => { const tb = document.querySelector('.toolbar'); tb.appendChild(document.getElementById('btn-lang')); }")
            attendre(pg, "document.querySelector('.toolbar').lastElementChild === document.querySelector('.tb-more-btn')", '« ⋯ » revenu au bout de la barre', lu="document.querySelector('.toolbar').lastElementChild.id")
            assert pg.evaluate(state)['last']
            assert not errs, errs
            c.close()
        finally:
            br.close()


FAKE_DSP = r"""<script>
/* ce que font Affichage, Ouvrir, Exporter dans les modules : un menu qui se ferme au toucher hors de lui (dspOutside, mnOutside) et avale le clic qui suit, sauf sur un de leurs déclencheurs (MENU_TRIG) */
window.dsp = { open: false, panel: null };
const dspBtn = document.getElementById('btn-display');
const dspClose = () => { if (dsp.panel) dsp.panel.remove(); dsp.panel = null; dsp.open = false; dspBtn.setAttribute('aria-expanded', 'false'); };
dspBtn.addEventListener('click', () => {
  if (dsp.open) { dspClose(); return; }
  dsp.panel = document.createElement('div'); dsp.panel.id = 'fake-dsp'; dsp.panel.style.cssText = 'position:fixed;top:300px;left:10px;width:200px;height:120px;background:#2c2a1e;z-index:50';
  document.body.appendChild(dsp.panel); dsp.open = true; dspBtn.setAttribute('aria-expanded', 'true');
});
document.addEventListener('pointerdown', e => {
  if (!dsp.open) return;
  const t = e.target;
  if (dsp.panel.contains(t) || dspBtn.contains(t)) return;
  const other = t && t.closest ? t.closest('.tbm-trigger, #btn-display') : null;
  dspClose();
  if (other) return;
  tbmSwallowNext();
}, true);
</script>"""


@pytest.mark.skipif(not HAS_PW, reason='playwright ou chromium absent')
def test_le_menu_reste_ouvert_tant_que_la_decision_est_la_meme():
    """Addendum 3, point 1 : un recalcul (police chargée, attribut reposé à la même valeur, contenu de la barre sans effet sur la décision) ne ferme pas le menu « ⋯ » ni la liste ouverte depuis lui ;
    une décision qui change, le redimensionnement, les gestes prévus le ferment ; un menu resté ouvert pendant que « ⋯ » se déplace reste aligné sur lui."""
    from playwright.sync_api import sync_playwright
    html = page_html()
    with sync_playwright() as p:
        br = p.chromium.launch(executable_path=str(CHROMIUM), args=['--no-sandbox'])
        try:
            def fresh(w=345):
                c = br.new_context(viewport={'width': w, 'height': 640}, has_touch=True, is_mobile=True)
                pg = c.new_page()
                errs = []
                pg.on('pageerror', lambda e: errs.append(str(e)))
                pg.set_content(html)
                attendre_barre_prete(pg)
                return c, pg, errs
            panel = "() => !!document.querySelector('.tb-more-panel')"
            liste = "() => !!document.querySelector('.tbm-panel:not(.tb-more-panel)')"
            align = "() => { const p = document.querySelector('.tb-more-panel'); if (!p) return null; return Math.abs(p.getBoundingClientRect().right - document.querySelector('.tb-more-btn').getBoundingClientRect().right); }"
            align_liste = "() => { const p = document.querySelector('.tbm-panel:not(.tb-more-panel)'); if (!p) return null; return Math.abs(p.getBoundingClientRect().right - document.querySelector('.tb-more-btn').getBoundingClientRect().right); }"

            def plus(on=True):             # le menu « ⋯ » est ouvert (ou fermé)
                attendre(pg, "!!document.querySelector('.tb-more-panel') === arg", 'le menu « ⋯ » %s' % ('ouvert' if on else 'fermé'), lu="!!document.querySelector('.tb-more-panel')", arg=on)

            def liste_ouverte(on=True):    # la liste du théâtre ouverte depuis « ⋯ » (ou fermée)
                attendre(pg, "!!document.querySelector('.tbm-panel:not(.tb-more-panel)') === arg", 'la liste du théâtre %s' % ('ouverte' if on else 'fermée'), lu="!!document.querySelector('.tbm-panel:not(.tb-more-panel)')", arg=on)

            def recalculs():               # trois recalculs sans changement : la police des lignes qui finit de charger, un attribut reposé à la même valeur
                for _ in range(3):
                    pg.evaluate("() => document.fonts.dispatchEvent(new Event('loadingdone'))")
                    attendre_barre_stable(pg)
                    pg.evaluate(noop)
                    attendre_barre_stable(pg)
            noop = ("() => { const e = document.getElementById('btn-open'); e.setAttribute('hidden', ''); e.removeAttribute('hidden'); "
                    "const d = document.getElementById('btn-display'); d.setAttribute('style', d.getAttribute('style') || ''); d.hidden = false; }")
            c, pg, errs = fresh(345)
            sig0 = pg.evaluate("() => UIMORE.sig")
            pg.locator('.tb-more-btn').tap(); plus(True)
            assert pg.evaluate(panel)
            # un recalcul sans changement : la police des lignes qui finit de charger, un attribut reposé à la même valeur (plusieurs fois)
            recalculs()
            assert pg.evaluate(panel) and pg.evaluate("() => UIMORE.sig") == sig0
            assert pg.evaluate("() => document.querySelector('.tb-more-btn').getAttribute('aria-expanded')") == 'true'
            # le texte d'une ligne change sans que la décision change : la ligne se refait, le menu reste ouvert
            pg.evaluate("() => { document.querySelector('#btn-clear').disabled = true; }")
            attendre(pg, "!!document.querySelector('.tb-more-panel') && document.querySelector('.tb-more-panel li[aria-disabled=true]') !== null", 'la ligne grisée refaite dans le menu resté ouvert', lu="[!!document.querySelector('.tb-more-panel'), !!document.querySelector('.tb-more-panel li[aria-disabled=true]')]")
            assert pg.evaluate(panel) and pg.evaluate("() => document.querySelector('.tb-more-panel li[aria-disabled=true]') !== null")
            pg.evaluate("() => { document.querySelector('#btn-clear').disabled = false; }")
            attendre(pg, "!!document.querySelector('.tb-more-panel') && document.querySelector('.tb-more-panel li[aria-disabled=true]') === null", 'la ligne dégrisée refaite dans le menu resté ouvert', lu="[!!document.querySelector('.tb-more-panel'), !!document.querySelector('.tb-more-panel li[aria-disabled=true]')]")
            assert pg.evaluate(panel) and pg.evaluate("() => document.querySelector('.tb-more-panel li[aria-disabled=true]') === null")
            # « ⋯ » se déplace pendant que la décision reste la même : le menu reste aligné sur lui
            x0 = pg.evaluate("() => document.querySelector('.tb-more-btn').getBoundingClientRect().right")
            pg.evaluate("() => { document.querySelector('.toolbar').style.paddingRight = '18px'; }")
            attendre(pg, "document.querySelector('.tb-more-btn').getBoundingClientRect().right < arg - 3", '« ⋯ » déplacé vers la gauche par la marge de la barre', lu="document.querySelector('.tb-more-btn').getBoundingClientRect().right", arg=x0)
            attendre_barre_stable(pg)
            x1 = pg.evaluate("() => document.querySelector('.tb-more-btn').getBoundingClientRect().right")
            assert pg.evaluate("() => UIMORE.sig") == sig0 and x1 < x0 - 3, (x0, x1)
            assert pg.evaluate(panel) and pg.evaluate(align) <= 0.5
            pg.evaluate("() => { document.querySelector('.toolbar').style.paddingRight = ''; }")
            attendre(pg, "Math.abs(document.querySelector('.tb-more-btn').getBoundingClientRect().right - arg) < 1", '« ⋯ » revenu à sa place', lu="document.querySelector('.tb-more-btn').getBoundingClientRect().right", arg=x0)
            attendre_barre_stable(pg)
            assert pg.evaluate(panel) and pg.evaluate(align) <= 0.5
            # une décision qui change (un élément sort de « ⋯ ») ferme le menu
            pg.evaluate("() => { document.getElementById('btn-clear').style.display = 'none'; }")
            plus(False)
            assert not pg.evaluate(panel), 'la décision a changé : le menu se ferme'
            assert pg.evaluate("() => document.querySelector('.tb-more-btn').getAttribute('aria-expanded')") == 'false'
            pg.evaluate("() => { document.getElementById('btn-clear').style.display = ''; }"); attendre_barre_stable(pg)
            # le redimensionnement ferme le menu
            pg.locator('.tb-more-btn').tap(); plus(True)
            assert pg.evaluate(panel)
            pg.set_viewport_size({'width': 346, 'height': 640}); attendre_fenetre(pg, 346, 640)
            plus(False)
            assert not pg.evaluate(panel), 'le redimensionnement ferme le menu'
            # la liste ouverte depuis le menu suit la même règle : elle reste (et reste alignée sur « ⋯ »), puis se ferme quand la décision change
            pg.locator('.tb-more-btn').tap(); plus(True)
            pg.locator('.tb-more-panel li', has_text='Théâtre').first.tap(); liste_ouverte(True)
            assert pg.evaluate(liste) and not pg.evaluate(panel)
            recalculs()
            assert pg.evaluate(liste), 'la liste ouverte depuis « ⋯ » reste ouverte tant que la décision est la même'
            xl = pg.evaluate("() => document.querySelector('.tb-more-btn').getBoundingClientRect().right")
            pg.evaluate("() => { document.querySelector('.toolbar').style.paddingRight = '18px'; }")
            attendre(pg, "document.querySelector('.tb-more-btn').getBoundingClientRect().right < arg - 3", '« ⋯ » déplacé vers la gauche par la marge de la barre', lu="document.querySelector('.tb-more-btn').getBoundingClientRect().right", arg=xl)
            attendre_barre_stable(pg)
            assert pg.evaluate(liste) and pg.evaluate(align_liste) <= 0.5
            pg.evaluate("() => { document.querySelector('.toolbar').style.paddingRight = ''; }")
            attendre(pg, "Math.abs(document.querySelector('.tb-more-btn').getBoundingClientRect().right - arg) < 1", '« ⋯ » revenu à sa place', lu="document.querySelector('.tb-more-btn').getBoundingClientRect().right", arg=xl)
            attendre_barre_stable(pg)
            pg.evaluate("() => { document.getElementById('btn-clear').style.display = 'none'; }")
            liste_ouverte(False)
            assert not pg.evaluate(liste), 'la décision a changé : la liste se ferme aussi'
            pg.evaluate("() => { document.getElementById('btn-clear').style.display = ''; }"); attendre_barre_stable(pg)
            # le redimensionnement ferme la liste (comme avant)
            pg.locator('.tb-more-btn').tap(); plus(True)
            pg.locator('.tb-more-panel li', has_text='Théâtre').first.tap(); liste_ouverte(True)
            assert pg.evaluate(liste)
            pg.set_viewport_size({'width': 345, 'height': 640}); attendre_fenetre(pg, 345, 640)
            liste_ouverte(False)
            assert not pg.evaluate(liste) and not pg.evaluate(panel)
            assert not errs, errs
            c.close()
        finally:
            br.close()


@pytest.mark.skipif(not HAS_PW, reason='playwright ou chromium absent')
def test_un_toucher_sur_more_avec_un_menu_de_module_ouvert_ouvre_le_menu_du_premier_coup():
    """Addendum 3, point 3 : le menu d'un module (Affichage, Ouvrir, Exporter) ouvert, un toucher sur « ⋯ » ferme ce menu et ouvre « ⋯ » du premier coup (tbmSwallowClick laisse passer « ⋯ ») ;
    un toucher ailleurs reste avalé."""
    from playwright.sync_api import sync_playwright
    html = page_html(FAKE_DSP)
    with sync_playwright() as p:
        br = p.chromium.launch(executable_path=str(CHROMIUM), args=['--no-sandbox'])
        try:
            c = br.new_context(viewport={'width': 345, 'height': 640}, has_touch=True, is_mobile=True)
            pg = c.new_page()
            errs = []
            pg.on('pageerror', lambda e: errs.append(str(e)))
            pg.set_content(html); attendre_barre_prete(pg)
            panel = "() => !!document.querySelector('.tb-more-panel')"
            dsp = "() => !!document.getElementById('fake-dsp')"

            def plus(on=True):             # le menu « ⋯ » est ouvert (ou fermé)
                attendre(pg, "!!document.querySelector('.tb-more-panel') === arg", 'le menu « ⋯ » %s' % ('ouvert' if on else 'fermé'), lu="!!document.querySelector('.tb-more-panel')", arg=on)

            def module(on=True):           # le menu du module (Affichage, factice) est ouvert (ou fermé)
                attendre(pg, "!!document.getElementById('fake-dsp') === arg", 'le menu du module %s' % ('ouvert' if on else 'fermé'), lu="!!document.getElementById('fake-dsp')", arg=on)
            assert pg.evaluate("() => !!document.querySelector('.tb-more-btn') && document.querySelector('.tb-more-btn').getBoundingClientRect().width > 0")
            pg.locator('#btn-display').tap(); module(True)
            assert pg.evaluate(dsp)
            pg.locator('.tb-more-btn').tap()
            attendre(pg, "!document.getElementById('fake-dsp') && !!document.querySelector('.tb-more-panel')", 'le menu du module fermé et « ⋯ » ouvert du premier coup', lu="[!!document.getElementById('fake-dsp'), !!document.querySelector('.tb-more-panel')]")
            assert not pg.evaluate(dsp) and pg.evaluate(panel), 'le menu du module se ferme, « ⋯ » s\'ouvre du premier coup'
            assert pg.evaluate("() => document.querySelector('.tb-more-btn').getAttribute('aria-expanded')") == 'true'
            attendre(pg, 'TBM.swallow === false', 'le clic suivant plus avalé (TBM.swallow retombé)', lu='TBM.swallow')       # la garde du clic suivant retombe d\'elle-même ; le menu doit rester ouvert après
            attendre_barre_stable(pg)
            assert pg.evaluate(panel)
            # le menu du module ouvert, un toucher ailleurs (la sonde) : le menu se ferme, le clic est avalé (comme avant)
            pg.locator('.tb-more-btn').tap(); plus(False)                                       # ferme « ⋯ »
            pg.locator('#btn-display').tap(); module(True)
            assert pg.evaluate(dsp)
            pg.locator('#probe').tap()
            attendre(pg, "!document.getElementById('fake-dsp') && TBM.swallow === false", 'le menu du module fermé et le clic de fermeture avalé (TBM.swallow retombé)', lu="[!!document.getElementById('fake-dsp'), TBM.swallow]")
            assert not pg.evaluate(dsp) and pg.evaluate("() => window.clicks.probe") == 0
            pg.locator('#probe').tap()
            attendre(pg, 'window.clicks.probe === 1', 'le clic de la sonde compté (1)', lu='window.clicks.probe')
            assert pg.evaluate("() => window.clicks.probe") == 1
            # le clic avalé ne reste pas armé : « ⋯ » s'ouvre au toucher suivant, puis se referme au suivant
            pg.locator('.tb-more-btn').tap(); plus(True)
            assert pg.evaluate(panel)
            pg.locator('.tb-more-btn').tap(); plus(False)
            assert not pg.evaluate(panel)
            assert not errs, errs
            c.close()
        finally:
            br.close()
