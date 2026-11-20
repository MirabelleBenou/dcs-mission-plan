"""La barre du haut, étapes 7 et 8 (« ⋯ » puis les écarts serrés) : la règle de uiBarFit (texte commun de ui_block, build_bar_js) jouée par node sur une barre fabriquée
(des enfants à largeur donnée, aucun navigateur, aucun réseau) ; et ce même texte, à l'octet, dans les huit livrables."""
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from ui_block import build_bar_js  # noqa: E402

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
  get hidden() { return !!this.hid; }
  set textContent(v) { this._t = v; } get textContent() { return this._t || ''; }
}
function width(e, bar) {                     /* la largeur d'un enfant à l'étape où se trouve la barre */
  const c = n => bar.classList.contains(n);
  if (e.classList.contains('tb-label')) return c('tb-st3') ? 0 : 60;
  if (e.classList.contains('tb-brand')) return c('tb-st6') ? 34 : 220;
  if (e.classList.contains('tb-sep') || e.classList.contains('tb-files-end')) return c('tb-st6') ? 0 : 1;
  if (e.classList.contains('tb-more-btn') || e.classList.contains('tb-lang-btn') || e.classList.contains('mp-back-injected')) return 44;
  if (e.classList.contains('tbm-trigger')) return 80;
  if (e.id === 'btn-display') return c('tb-st4') ? 44 : 120;
  if (e.classList.contains('tb-btn')) return c('tb-st5') ? 44 : 130;
  return e.w;
}
function shown(e) { return !('data-mp-off' in e.attrs) && !e.hid && !e.baseNone; }
const bar = new El('header', '', ['toolbar'], 0);
bar.children = []; bar.scrollLeft = 0;
bar.appendChild = e => { e.parentNode = bar; bar.children.push(e); return e; };
bar.querySelectorAll = sel => bar.children.filter(e => e.matches(sel));
Object.defineProperty(bar, 'clientWidth', { get: () => bar.cw });
Object.defineProperty(bar, 'scrollWidth', { get: () => {
  const t8 = bar.classList.contains('tb-st8'), gap = t8 ? 2 : 8, pad = t8 ? 4 : 14;
  const vis = bar.children.filter(e => shown(e) && width(e, bar) > 0);
  const own = pad * 2 + vis.reduce((a, e) => a + width(e, bar), 0) + gap * Math.max(0, vis.length - 1);
  return bar.classList.contains('tb-st7') && !bar.classList.contains('tb-over') ? Math.max(bar.cw, own - pad) : Math.max(bar.cw, own);     /* overflow: visible : la marge de fin ne compte pas */
} });
function build(kind) {
  const L = [['button', '', ['mp-back-injected'], 44], ['div', '', ['tb-brand'], 220], ['button', 'btn-open', ['tb-btn', 'tb-file'], 130], ['button', 'btn-save', ['tb-btn', 'tb-file'], 130],
    ['button', 'btn-export', ['tb-btn', 'tb-file'], 130], ['div', '', ['tb-sep', 'tb-files-end'], 1], ['button', 'btn-display', ['tb-btn'], 120]];
  const R = [['span', '', ['tb-label'], 60], ['button', '', ['tb-sel', 'tbm-trigger'], 80, { sel: 1 }], ['select', 'theatre', ['tb-sel'], 0, { baseNone: true }],
    ['button', 'btn-wing', ['tb-btn'], 130], ['button', 'btn-clear', ['tb-btn', 'danger'], 130], ['div', '', ['tb-spacer'], 0], ['button', 'btn-lang', ['tb-lang-btn'], 44]];
  const rows = kind === 'fm' ? [['button', '', ['mp-back-injected'], 44], ['div', '', ['tb-brand'], 220], ['button', 'btn-toc', ['tb-btn'], 130], ['div', '', ['tb-spacer'], 0], ['button', 'btn-lang', [], 44]]
    : kind === 'nolist' ? L.concat(R.filter(r => r[2][0] !== 'tb-sel' && r[2][0] !== 'tb-label')) : L.concat(R);
  rows.forEach(r => bar.appendChild(new El(r[0], r[1], r[2], r[3], r[4])));
}
globalThis.document = { querySelector: s => s === '.toolbar' ? bar : null, readyState: 'complete', documentElement: { lang: 'fr' }, createElement: t => new El(t, '', [], 0), addEventListener() {}, body: { appendChild() {} } };
globalThis.window = { matchMedia: q => ({ matches: bar.narrow }), addEventListener() {} };
globalThis.getComputedStyle = e => ({ display: shown(e) ? 'block' : 'none', color: '' });
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
  st7: bar.classList.contains('tb-st7'), st8: bar.classList.contains('tb-st8'), over: bar.classList.contains('tb-over'),
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
    # le shell embarque les outils : le texte y est aussi, sous leur forme codée, donc seul le fichier existe à vérifier
    assert (ROOT / 'dist' / 'dcs_mission_plan.html').exists()
