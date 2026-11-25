"""Petites corrections, lot 4 (MP-V2.1.0+16) : la carte en grand pendant le cadre d'export et le dessin (téléphone et petite tablette), la garde commune des copies clé par clé,
le focus de « ⋯ » à l'accueil après la liste « Thème », une ligne grisée de « ⋯ » qui ne prend jamais le focus.
Joué sur le shell construit (dist/dcs_mission_plan.html, chromium, aucun réseau) ; les contrôles passent par le DOM, jamais par une capture."""
import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
CHROMIUM = Path('/opt/pw-browsers/chromium')
try:
    import playwright.sync_api  # noqa: F401
    HAS_PW = CHROMIUM.exists()
except ImportError:
    HAS_PW = False
needs_pw = pytest.mark.skipif(not HAS_PW, reason='playwright ou chromium absent')
SHELL = 'file://' + str(ROOT / 'dist' / 'dcs_mission_plan.html')
SEED = "(() => { try { if (localStorage.getItem('lang_v1') === null) localStorage.setItem('lang_v1', '@@'); } catch (e) {} })();"
SPLIT_SEED = "(() => { try { if (localStorage.getItem('rp_split_v1') === null) { localStorage.setItem('rp_split_v1', '263'); localStorage.setItem('rp_split_land_v1', '151'); } } catch (e) {} })();"


@pytest.fixture(scope='module')
def browser():
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        br = p.chromium.launch(executable_path=str(CHROMIUM), args=['--no-sandbox'])
        yield br
        br.close()


CONTEXTS = []


@pytest.fixture(autouse=True)
def close_contexts():
    yield
    while CONTEXTS:
        try:
            CONTEXTS.pop().close()
        except Exception:
            pass


def shell(br, w, h, lang='fr', touch=False, init=''):
    kw = dict(has_touch=True, is_mobile=True) if touch else {}
    ctx = br.new_context(viewport={'width': w, 'height': h}, locale=lang + '-' + lang.upper(), **kw)
    ctx.add_init_script(SEED.replace('@@', lang) + init)
    ctx.route('**/*', lambda r: r.continue_() if r.request.url.startswith(('file:', 'data:', 'blob:')) else r.abort())
    CONTEXTS.append(ctx)
    pg = ctx.new_page()
    pg.errs = []
    pg.on('pageerror', lambda e: pg.errs.append(str(e)[:200]))
    pg.goto(SHELL, wait_until='commit')
    pg.wait_for_function("() => typeof window.MP_WORK_EXAMPLE === 'function' && !!document.getElementById('card-hq')", timeout=60000)
    pg.wait_for_timeout(1300)
    return pg


def examples(pg):
    for g in ('mc', 'fl'):
        pg.evaluate('(g) => window.MP_WORK_EXAMPLE(g)', g)
        pg.wait_for_timeout(800)


def open_tool(pg, tid, touch=False, wait=2600):
    card = pg.locator('#card-' + tid)
    card.scroll_into_view_if_needed()
    try:
        card.tap(timeout=5000) if touch else card.click(timeout=5000)
    except Exception:
        card.click()
    pg.wait_for_selector('#iframe-' + tid, state='attached')
    pg.wait_for_timeout(wait)
    return pg.query_selector('#iframe-' + tid).content_frame()


def hide_toasts(pg, fr):
    pg.add_style_tag(content='.toast, #toast, [class*="toast"] { display: none !important; }')
    fr.evaluate("() => document.querySelectorAll('.toast, #toast').forEach(e => { e.style.display = 'none'; })")


# ---------- le texte, sans navigateur ----------

def test_the_guard_is_in_ui_block_once_and_every_copy_passes_it():
    ui = (ROOT / 'ui_block.py').read_text(encoding='utf-8')
    assert ui.count("function uiKeyOk(k) { return k !== '__proto__' && k !== 'constructor' && k !== 'prototype'; }") == 1
    sites = {
        'build_flight_configurator.py': ["if (uiKeyOk(k) && ['name', 'type', 'coalition', 'route', 'routeLink', 'units'].indexOf(k) < 0) nf[k] = f[k];", 'if (uiKeyOk(k) && UNIT_KEYS.indexOf(k) < 0) nu[k] = u[k];',
                                         'if (uiKeyOk(k) && !has(ids, k)) out[k] = u.props[k];', 'Object.keys(pylons).forEach(n => { if (uiKeyOk(n) &&', 'Object.keys(cur).forEach(k => { if (uiKeyOk(k)) nx[k] = cur[k]; });'],
        'group_store_block.py': ['if (uiKeyOk(n)) o[n] = x[n];', 'if (uiKeyOk(k) && gsIsObj(e)) r[k] =', 'Object.keys(grp).forEach(k => { if (uiKeyOk(k)) print[k] = grp[k]; });', 'if (!uiKeyOk(k) || gsIsObj(print[k]) || !gsIsObj(e)) return;',
                                 'Object.keys(f).forEach(k => { if (uiKeyOk(k)) g[k] = f[k]; });'],
        'build_datacard_generator.py': ["if (uiKeyOk(k) && o && typeof o === 'object') c.radioSel[k] =", 'Object.keys(c).forEach(k => { if (uiKeyOk(k) && !Object.prototype.hasOwnProperty.call(o, k)) o[k] = c[k]; });'],
        'import_block.py': ['if (!uiKeyOk(p)) return;', 'if (uiKeyOk(c)) row[c] = tab.posts[p][c];'],
        'build_route_planner.py': ["Object.keys(mine).forEach(k => { if (uiKeyOk(k) && k !== 'points'", 'if (uiKeyOk(f) && JSON.stringify(p[f])', 'Object.keys(d.set).forEach(k => { if (uiKeyOk(k)) S[k] = d.set[k]; });', 'if (!uiKeyOk(f)) return; if (c.ch[f] === undefined)'],
        'build_hq.py': ["if (e.key && uiKeyOk(String(e.key.value))) obj[e.key.value] =", 'if (v !== undefined && uiKeyOk(String(e.key.value))) obj[e.key.value] = v;', 'if (uiKeyOk(c) && pkNum(fr) !== null) channels[c] = fr;', 'if (x === null || !uiKeyOk(k)) continue;',
                        'if (uiKeyOk(kk)) pt[kk] = v;', "if (k !== '1' && uiKeyOk(k)) pts[k] = v;"],
    }
    sites['ui_block.py'] = ["function uiCopy(o) { const r = {}; if (o && typeof o === 'object') Object.keys(o).forEach(k => { if (uiKeyOk(k)) r[k] = o[k]; }); return r; }"]
    sites['build_route_planner.py'] += ["Object.assign(uiCopy(parsed), { format: FORMAT_ID, points: [], name: '' })", 'Object.assign(uiCopy(route), { units: S.units,']
    sites['build_datacard_generator.py'] += ['Object.assign(uiCopy(d), { cards: d.cards.map(dgCanonCard) })', 'Object.assign(uiCopy(l), { after: a })', 'Object.assign(uiCopy(o), { format: ROUTE_FORMAT, theatre: C })',
                                             'Object.assign(uiCopy(st), { theatre: C })', 'routeFromObject(Object.assign(uiCopy(base), uiCopy(o)))']
    sites['group_store_block.py'] += ['Object.assign(uiCopy(fc), { gsMigrateFailed: true })']
    sites['build_hq.py'] += ['? uiCopy(wingConfig) : wingConfig', 'Object.assign(uiCopy(cur), uiCopy(aOv.addProp))', "name !== 'mission' && uiKeyOk(name)", 'otherFilesMap = uiCopy(base.otherFilesMap);', 'return Object.assign(uiCopy(u), {{']
    sites['build_recon_station.py'] = ['Object.assign(uiCopy(STATE.fields), uiCopy(saved.fields))', 'Object.assign(uiCopy(STATE), {{ schema: 2 }})']
    for f, lines in sites.items():
        src = (ROOT / f).read_text(encoding='utf-8')
        for ln in lines:
            assert src.count(ln) >= 1, (f, ln)
            assert 'Object.assign({}, ' not in ln
    for page in ('dcs_flight_configurator', 'dcs_datacard_generator', 'dcs_route_planner', 'dcs_hq', 'dcs_briefing_generator', 'dcs_recon_station'):
        d = (ROOT / 'dist' / (page + '.html')).read_text(encoding='utf-8')
        assert d.count('function uiKeyOk(') == 1 and d.count('function uiCopy(') == 1, page


# ---------- les copies, au navigateur : un fichier de travail, un paquet, une route portant « __proto__ » à chaque niveau copié ----------

FC_JS = """() => {
  const P = Object.prototype, out = {};
  const proto = o => Object.getPrototypeOf(o) === P;
  const nz = t => JSON.parse(t.replace(/"__proto__": \\{[^}]*\\}, /g, ''));          /* le même fichier sans cette clé */
  const FLIGHT = '{"__proto__": {"x": 1}, "name": "A", "type": "Mi-24P", "coalition": "red", "foo": 5, "units": [{"__proto__": {"y": 1}, "type": "Mi-24P", "name": "u", "bar": 7, "props": {"__proto__": {"z": 1}, "k": 1}, "loadout": null}]}';
  const nf = restoreFlight(JSON.parse(FLIGHT)), ref = restoreFlight(nz(FLIGHT));
  out.flight = [proto(nf), nf.x, proto(nf.units[0]), nf.units[0].y];
  const strip = f => { const c = JSON.parse(JSON.stringify(f)); delete c.fcId; c.units.forEach(u => { delete u.fcId; delete u.id; }); return c; };
  out.flightSame = JSON.stringify(Object.keys(nf).sort()) === JSON.stringify(Object.keys(ref).sort()) && nf.foo === ref.foo && nf.units[0].bar === ref.units[0].bar && nf.name === ref.name;
  const po = unitPropsOut({ type: 'Mi-24P', props: JSON.parse('{"__proto__": {"z": 1}, "k": 1}') });
  out.props = po === null ? 'null' : [proto(po), po.z, po.k];
  const cp = cleanPylons(JSON.parse('{"__proto__": {"CLSID": "q"}, "1": {"CLSID": "A"}}'));
  out.pylons = [proto(cp), Object.keys(cp), cp.CLSID];
  const f2 = { fcId: 'a', units: [], radioPrint: JSON.parse('{"__proto__": {"w": 1}, "t|1|1": {"on": false, "label": "", "mod": ""}}') };
  printSet(f2, 't|1|2', true);
  out.print = [proto(f2.radioPrint), f2.radioPrint.w, Object.keys(f2.radioPrint), f2.radioPrint['t|1|2'].on];
  const f3 = { fcId: 'b', units: [], radioPrint: JSON.parse('{"__proto__": {"t|1|2": {"on": false, "label": "leak", "mod": "x"}}, "t|1|1": {"on": false, "label": "", "mod": ""}}') };
  printSet(f3, 't|1|2', true);
  out.printLeak = [JSON.stringify(f3.radioPrint['t|1|2']), proto(f3.radioPrint)];
  const lk = gsStable(JSON.parse('{"constructor": {"a": 1}, "b": 1, "a": 2}'));
  out.stableCtor = lk;
  const g = JSON.parse('{"__proto__": {"w": 1}, "t|1|1": {"on": true, "label": "a", "mod": ""}}');
  const nn = gsPrintNorm(g);
  out.norm = [proto(nn), nn.w, Object.keys(nn)];
  const m = gsPrintMergeOf(g, JSON.parse('{"__proto__": {"v": 1}, "t|1|2": {"on": true, "label": "", "mod": ""}}'));
  out.merge = [proto(m.print), m.print.w, m.print.v, Object.keys(m.print), m.added];
  out.stable = gsStable(JSON.parse('{"__proto__": {"w": 1}, "b": 1, "a": 2}'));
  const li = gsLegacyIds([JSON.parse('{"__proto__": {"w": 1}, "name": "a"}')]);
  out.legacy = [proto(li[0]), li[0].w, li[0].name, typeof li[0].fcId];
  return out;
}"""


@needs_pw
def test_the_flight_configurator_and_the_group_store_copy_a_work_file_without_its_special_keys(browser):
    pg = shell(browser, 1200, 800)
    fr = open_tool(pg, 'fc')
    o = fr.evaluate(FC_JS)
    assert o['flight'] == [True, None, True, None], o
    assert o['flightSame'] is True
    assert o['props'] == [True, None, 1], o
    assert o['pylons'] == [True, ['1'], None], o
    assert o['print'] == [True, None, ['t|1|1', 't|1|2'], True], o
    assert o['norm'] == [True, None, ['t|1|1']], o
    assert o['merge'] == [True, None, None, ['t|1|1', 't|1|2'], 1], o
    assert o['stable'] == '{"a":2,"b":1}', o
    assert o['printLeak'] == ['{"on":true,"label":"","mod":""}', True], o
    assert o['stableCtor'] == '{"a":2,"b":1}', o
    assert o['legacy'] == [True, None, 'a', 'string'], o
    assert pg.errs == []


@needs_pw
def test_the_datacard_generator_copies_a_datacard_file_without_its_special_keys(browser):
    pg = shell(browser, 1200, 800)
    fr = open_tool(pg, 'dg')
    o = fr.evaluate("""() => {
      const P = Object.prototype, proto = o => Object.getPrototypeOf(o) === P;
      const c = JSON.parse('{"__proto__": {"x": 1}, "name": "c", "gsId": "g1", "radioSel": {"__proto__": {"w": {"on": true}}, "t|1|1": {"on": true, "label": "a", "mod": ""}}}');
      const n = normalizeCard(c), k = dgCanonCard(JSON.parse('{"__proto__": {"x": 1}, "foo": 1, "constructor": {"a": 1}}'));
      return { sel: [proto(n.radioSel), n.radioSel.w, Object.keys(n.radioSel)], card: [proto(n), n.x], canon: [proto(k), k.x, Object.keys(k).slice(-1)] };
    }""")
    assert o['sel'] == [True, None, ['t|1|1']], o
    assert o['card'] == [True, None], o
    assert o['canon'] == [True, None, ['foo']], o
    assert pg.errs == []


@needs_pw
def test_the_route_planner_replays_a_route_state_without_its_special_keys(browser):
    pg = shell(browser, 1200, 800)
    fr = open_tool(pg, 'rp')
    o = fr.evaluate("""() => {
      const P = Object.prototype, proto = o => Object.getPrototypeOf(o) === P;
      const base = { a: 1, points: [{ pid: 'p1', name: 'x' }], refs: [] };
      const mine = JSON.parse('{"__proto__": {"x": 1}, "a": 2, "points": [{"pid": "p1", "name": "y", "__proto__": {"q": 1}}], "refs": []}');
      const d = rpDiff(base, mine);
      const keep = JSON.stringify(S);
      rpApply({ set: JSON.parse('{"__proto__": {"zz": 1}, "theatre": "' + S.theatre + '"}'), lists: { points: { changed: [{ pid: 'nope', ch: {} }], added: [], removed: [] }, refs: { changed: [], added: [], removed: [] } } });
      return { set: [proto(d.set), d.set.x, Object.keys(d.set)], ch: d.lists.points.changed.map(c => [Object.keys(c.ch), proto(c.ch), c.ch.q]), applied: [proto(S), S.zz], same: JSON.stringify(S) === keep };
    }""")
    assert o['set'] == [True, None, ['a']], o
    assert o['ch'] == [[['name'], True, None]], o
    assert o['applied'] == [True, None] and o['same'] is True, o
    assert pg.errs == []


@needs_pw
def test_hq_reads_a_mission_table_and_a_package_without_special_keys(browser):
    pg = shell(browser, 1200, 800)
    fr = open_tool(pg, 'hq')
    o = fr.evaluate("""() => {
      const P = Object.prototype, proto = o => Object.getPrototypeOf(o) === P;
      const node = { kind: 'table', entries: [{ key: { value: '__proto__' }, value: { kind: 'table', entries: [{ key: { value: 'x' }, value: { kind: 'number', value: 1 } }] } },
                                              { key: { value: 'prototype' }, value: { kind: 'number', value: 3 } }, { key: { value: 'a' }, value: { kind: 'number', value: 2 } }] };
      const v = astToValue(node);
      const c = pkClean(JSON.parse('{"__proto__": {"x": 1}, "a": {"constructor": 1, "prototype": 2, "b": 2}}'));
      const pk = pkNormalize(JSON.parse('{"format": "dcs-flight-package-v1", "theatre": "Syria", "flights": [{"groupName": "G", "aircraftType": "Mi-24P", "units": [{"name": "u", "radios": [{"radioIndex": 1, "channels": {"__proto__": 5, "1": 251}}]}]}]}'), 'p.json');
      const ch = pk.pk ? pk.pk.flights[0].units[0].radios : null;
      return { ast: [proto(v), v.x, Object.keys(v)], clean: [proto(c), JSON.stringify(c)], radios: ch && ch.length ? Object.keys(ch[0].channels) : ch };
    }""")
    assert o['ast'] == [True, None, ['a']], o
    assert o['clean'] == [True, '{"a":{"b":2}}'], o
    assert o['radios'] == ['1'], o
    assert pg.errs == []


# ---------- la carte en grand, au Route Planner ----------

RECT_JS = """(s) => { const e = document.querySelector(s); if (!e) return null; const cs = getComputedStyle(e); if (cs.display === 'none' || cs.visibility === 'hidden') return null;
  const q = e.getBoundingClientRect(); if (!q.width && !q.height) return null; return { l: q.left, t: q.top, r: q.right, b: q.bottom, w: q.width, h: q.height }; }"""
LS_JS = "() => [localStorage.getItem('rp_split_v1'), localStorage.getItem('rp_split_land_v1')]"


def rect(fr, sel):
    return fr.evaluate(RECT_JS, sel)


def layout(fr):
    return {k: rect(fr, s) for k, s in (('map', '#map'), ('panel', '#panel'), ('split', '#rp-split'), ('tabs', '#tab-bar'), ('tapmode', '#tapmode'), ('bar', '#export-bar'), ('hint', '#export-bar .eb-hint'),
                                         ('frame', '#export-frame'), ('attr', '.leaflet-control-attribution'), ('drui', '#dr-ui'), ('app', '#app'))}


def tap(pg, fr, sel, touch=True):
    fr.evaluate("(s) => document.querySelector(s).scrollIntoView({ block: 'nearest' })", sel)
    b = rect(fr, sel)
    x, y = b['l'] + b['w'] / 2, b['t'] + b['h'] / 2
    # le cadre de l'outil est dans la page du shell : ses coordonnées sont celles de la fenêtre de l'outil, décalées de l'iframe
    off = fr.evaluate("() => { const f = window.frameElement; const q = f ? f.getBoundingClientRect() : { left: 0, top: 0 }; return [q.left, q.top]; }")
    (pg.touchscreen.tap if touch else pg.mouse.click)(x + off[0], y + off[1])
    pg.wait_for_timeout(500)


def assert_full(fr, L, before, inner_h, label):
    m = L['map']
    app_top = L['app']['t']
    assert abs(m['t'] - app_top) <= 1 and abs(m['b'] - inner_h) <= 1, (label, 'la carte ne prend pas toute la hauteur', m, app_top, inner_h)
    assert L['panel'] is None and L['split'] is None and L['tabs'] is None, (label, 'panneau, poignée ou onglets visibles', L['panel'], L['split'], L['tabs'])
    assert fr.evaluate(LS_JS) == before, (label, 'une mémoire du partage a été écrite')


@needs_pw
@pytest.mark.parametrize('w,h', [(345, 590), (915, 412)])
def test_the_frame_of_the_export_takes_the_whole_map_and_everything_comes_back(browser, w, h):
    pg = shell(browser, w, h, touch=True, init=SPLIT_SEED)
    examples(pg)
    fr = open_tool(pg, 'rp', touch=True)
    hide_toasts(pg, fr)
    ls0 = fr.evaluate(LS_JS)
    assert ls0 == ['263', '151']
    B = layout(fr)
    assert B['panel'] and B['split'] and B['tabs'] and B['tapmode'], B
    inner_h = fr.evaluate('() => innerHeight')
    fr.evaluate('() => expOpen()')
    pg.wait_for_timeout(700)
    for orient in ('landscape', 'portrait'):
        if orient == 'portrait':
            tap(pg, fr, '#export-bar [data-exo="portrait"]')
        L = layout(fr)
        assert_full(fr, L, ls0, inner_h, orient)
        assert L['tapmode'] is None, (orient, 'la barre des modes reste')
        bar, fr_, at, hint, m = L['bar'], L['frame'], L['attr'], L['hint'], L['map']
        assert abs(bar['l'] - m['l']) <= 1 and abs(bar['w'] - m['w']) <= 1, (orient, 'la barre n\'a pas toute la largeur', bar, m)
        assert at and bar['b'] <= at['t'] + 1, (orient, 'la barre recouvre la mention Leaflet', bar, at)
        assert hint and hint['t'] >= bar['t'] - 1 and hint['b'] <= bar['b'] + 1 and fr.evaluate("() => document.querySelector('#export-bar .eb-hint').textContent.trim().length > 10"), (orient, 'la consigne', hint, bar)
        assert fr_['b'] <= bar['t'] + 0.5 and fr_['t'] >= m['t'] - 0.5 and fr_['l'] >= m['l'] - 0.5 and fr_['r'] <= m['r'] + 0.5, (orient, 'le cadre n\'est pas au-dessus de la barre', fr_, bar)
        ratio = fr_['w'] / fr_['h']
        assert abs(ratio - (1.5 if orient == 'landscape' else 2 / 3)) < 0.03, (orient, ratio)
        assert fr.evaluate("() => EXP.rect && EXP.rect.w > 0") is True
    # un changement de taille de la fenêtre recalcule le cadre dans la place au-dessus de la barre
    pg.set_viewport_size({'width': w + 15, 'height': h + 40})
    pg.wait_for_timeout(900)
    L = layout(fr)
    inner2 = fr.evaluate('() => innerHeight')
    assert_full(fr, L, ls0, inner2, 'redimensionné')
    assert L['frame']['b'] <= L['bar']['t'] + 0.5 and L['frame']['t'] >= L['map']['t'] - 0.5, ('redimensionné', L['frame'], L['bar'])
    pg.set_viewport_size({'width': w, 'height': h})
    pg.wait_for_timeout(900)
    tap(pg, fr, '#export-bar [data-exo="landscape"]')
    tap(pg, fr, '#exp-cancel')
    pg.wait_for_timeout(500)
    A = layout(fr)
    assert A['frame'] is None and A['bar'] is None
    assert abs(A['map']['h'] - B['map']['h']) <= 1, ('la carte ne retrouve pas sa hauteur', A['map'], B['map'])
    for k in ('panel', 'split', 'tabs', 'tapmode'):
        assert A[k] and abs(A[k]['t'] - B[k]['t']) <= 1 and abs(A[k]['h'] - B[k]['h']) <= 1, (k, A[k], B[k])
    assert fr.evaluate(LS_JS) == ls0
    assert pg.errs == []


@needs_pw
@pytest.mark.parametrize('w,h', [(345, 590), (915, 412)])
def test_drawing_takes_the_whole_map_and_leaves_it_back(browser, w, h):
    pg = shell(browser, w, h, touch=True, init=SPLIT_SEED)
    examples(pg)
    fr = open_tool(pg, 'rp', touch=True)
    hide_toasts(pg, fr)
    ls0 = fr.evaluate(LS_JS)
    B = layout(fr)
    inner_h = fr.evaluate('() => innerHeight')
    tap(pg, fr, '#tapmode [data-tap="draw"]')
    pg.wait_for_timeout(500)
    L = layout(fr)
    assert_full(fr, L, ls0, inner_h, 'dessin')
    assert L['tapmode'] is not None, 'la barre des modes sert à sortir du dessin'
    assert L['drui'] and L['drui']['b'] <= L['map']['b'] + 0.5 and L['drui']['t'] >= L['map']['t'] - 0.5 and L['drui']['h'] < L['map']['h'], L['drui']
    assert fr.evaluate("() => !document.body.classList.contains('rp-mapfull-exp') && document.body.classList.contains('rp-mapfull')")
    tap(pg, fr, '#tapmode [data-tap="read"]')
    pg.wait_for_timeout(500)
    A = layout(fr)
    assert abs(A['map']['h'] - B['map']['h']) <= 1
    for k in ('panel', 'split', 'tabs'):
        assert A[k] and abs(A[k]['t'] - B[k]['t']) <= 1, (k, A[k], B[k])
    assert fr.evaluate(LS_JS) == ls0
    # le dessin ouvert puis l'export : l'export sort du dessin (la carte reste en grand, pour l'export) ; l'annuler rend le dessin, donc la carte en grand ; en sortir rend la hauteur gardée
    tap(pg, fr, '#tapmode [data-tap="draw"]')
    fr.evaluate('() => expOpen()')
    pg.wait_for_timeout(600)
    assert fr.evaluate("() => document.body.classList.contains('rp-mapfull-exp')") and rect(fr, '#tapmode') is None
    tap(pg, fr, '#exp-cancel')
    pg.wait_for_timeout(500)
    assert fr.evaluate("() => tapMode === 'draw' && document.body.classList.contains('rp-mapfull') && !document.body.classList.contains('rp-mapfull-exp')")
    assert abs(layout(fr)['map']['h'] - (inner_h - L['app']['t'])) <= 1 and rect(fr, '#tapmode') is not None
    tap(pg, fr, '#tapmode [data-tap="read"]')
    pg.wait_for_timeout(500)
    assert abs(layout(fr)['map']['h'] - B['map']['h']) <= 1 and fr.evaluate(LS_JS) == ls0
    assert pg.errs == []


@needs_pw
def test_above_1100_px_nothing_changes_for_the_export_or_the_drawing(browser):
    for w, h in ((1440, 900), (1101, 700)):
        pg = shell(browser, w, h, touch=False, init=SPLIT_SEED)
        examples(pg)
        fr = open_tool(pg, 'rp')
        hide_toasts(pg, fr)
        B = layout(fr)
        fr.evaluate('() => expOpen()')
        pg.wait_for_timeout(600)
        L = layout(fr)
        assert not fr.evaluate("() => document.body.classList.contains('rp-mapfull') || document.body.classList.contains('rp-mapfull-exp')")
        for k in ('map', 'panel', 'tapmode'):
            assert L[k] == B[k], (w, k, L[k], B[k])
        assert L['bar']['w'] < L['map']['w'] and L['frame']['b'] < L['bar']['t'] + L['bar']['h']
        fr.evaluate('() => expClose()')
        fr.evaluate("() => setTapMode('draw')")
        pg.wait_for_timeout(500)
        D = layout(fr)
        assert not fr.evaluate("() => document.body.classList.contains('rp-mapfull')")
        for k in ('map', 'panel', 'tapmode'):
            assert D[k] == B[k], (w, k, D[k], B[k])
        assert pg.errs == []
        pg.context.close()


@needs_pw
def test_a_phone_export_gives_an_image_of_the_frame_ratio(browser):
    pg = shell(browser, 345, 590, touch=True)
    examples(pg)
    fr = open_tool(pg, 'rp', touch=True)
    hide_toasts(pg, fr)
    pg.evaluate("() => { window.__sent = []; window.MP_SEND_MAP = d => { window.__sent.push(d); return true; }; }")
    fr.evaluate('() => expOpen()')
    pg.wait_for_timeout(600)
    sent = []
    for orient, want in (('landscape', 1.5), ('portrait', 2 / 3)):
        tap(pg, fr, '#export-bar [data-exo="%s"]' % orient)
        fr.evaluate("() => { try { return parent.MP_SEND_MAP && 1; } catch (e) { return 0; } }")
        tap(pg, fr, '#exp-go')
        pg.wait_for_function("() => window.__sent.length > %d" % len(sent), timeout=60000)
        got = pg.evaluate("() => window.__sent")
        d = got[len(sent)]
        sent = got
        assert abs(d['width'] / (d['height'] - 64) - want) < 0.01, (orient, d['width'], d['height'])       # l'image : la carte du cadre (3:2 ou 2:3) et le bandeau de 64 px dessous
        pg.wait_for_timeout(800)
        if not fr.evaluate('() => EXP.on'):
            fr.evaluate('() => expOpen()')
            pg.wait_for_timeout(600)
    assert pg.errs == []


# ---------- l'accueil : le focus de « ⋯ » ----------

@needs_pw
def test_the_home_theme_list_gives_the_focus_back_to_the_more_button(browser):
    pg = shell(browser, 345, 800)
    assert pg.evaluate("() => !!document.getElementById('tb-more-btn') && !document.getElementById('tb-more-btn').hasAttribute('data-mp-off')")
    rows_js = "() => [...document.querySelectorAll('.tb-more-panel .tbm-opt')].map(r => r.textContent.trim())"
    focus_js = "() => document.activeElement && document.activeElement.id"

    def open_theme_list():
        pg.locator('#tb-more-btn').focus()
        pg.keyboard.press('Enter')
        pg.wait_for_timeout(250)
        rows = pg.evaluate(rows_js)
        k = next(i for i, t in enumerate(rows) if re.match(r'(Thème|Theme)', t))
        for _ in range(k):
            pg.keyboard.press('ArrowDown')
        pg.keyboard.press('Enter')                                  # Entrée sur « Thème ▸ » : la liste s'ouvre
        pg.wait_for_timeout(350)
        assert pg.evaluate("() => !document.querySelector('.tb-more-panel') && !!document.querySelector('.tbm-panel')")

    open_theme_list()
    pg.keyboard.press('Escape')
    pg.wait_for_timeout(250)
    assert pg.evaluate("() => !document.querySelector('.tbm-panel')") and pg.evaluate(focus_js) == 'tb-more-btn', pg.evaluate(focus_js)
    open_theme_list()
    pg.keyboard.press('ArrowDown')
    pg.keyboard.press('Enter')                                       # un choix
    pg.wait_for_timeout(350)
    assert pg.evaluate("() => !document.querySelector('.tbm-panel')") and pg.evaluate(focus_js) == 'tb-more-btn', pg.evaluate(focus_js)
    assert pg.errs == []


@needs_pw
@pytest.mark.parametrize('how', ['touch', 'mouse'])
def test_a_greyed_row_of_the_more_menu_never_takes_the_focus(browser, how):
    pg = shell(browser, 345, 800, touch=(how == 'touch'))
    fr = open_tool(pg, 'rp', touch=(how == 'touch'))
    hide_toasts(pg, fr)
    fr.evaluate("() => { const b = document.getElementById('btn-clear'); b.disabled = true; b.setAttribute('data-mp-why', 'une raison'); uiBarFit(); }")
    pg.wait_for_timeout(300)
    tap(pg, fr, '#tb-more-btn', touch=(how == 'touch'))
    state_js = "() => [...document.querySelectorAll('.tb-more-panel .tbm-opt')].map(r => ({ dis: r.getAttribute('aria-disabled') === 'true', act: r.classList.contains('active'), foc: r === document.activeElement }))"
    rows = fr.evaluate(state_js)
    assert any(r['dis'] for r in rows) and not any(r['act'] or r['foc'] for r in rows)
    k = next(i for i, r in enumerate(rows) if r['dis'])
    tap(pg, fr, '.tb-more-panel .tbm-opt:nth-child(%d)' % (k + 1), touch=(how == 'touch'))
    rows = fr.evaluate(state_js)
    assert len(rows) and not any(r['act'] or r['foc'] for r in rows), rows            # le toucher sur la ligne grisée ne lui donne ni le focus ni .active
    fr.evaluate("() => { document.getElementById('btn-clear').setAttribute('data-mp-why', 'une autre raison'); uiBarFit(); }")       # un recalcul : les lignes se refont
    pg.wait_for_timeout(400)
    rows = fr.evaluate(state_js)
    assert any(r['dis'] for r in rows) and not any(r['act'] or r['foc'] for r in rows), rows
    assert fr.evaluate("() => !document.activeElement || !document.activeElement.closest || !document.activeElement.closest('.tb-more-panel')")
    # au clavier, rien ne change : les lignes grisées sont sautées, la première ligne active prend le focus
    fr.evaluate("() => { uiBarMoreClose(); }")
    fr.locator('#tb-more-btn').focus()
    pg.keyboard.press('Enter')
    pg.wait_for_timeout(250)
    rows = fr.evaluate(state_js)
    assert sum(r['act'] for r in rows) == 1 and any(r['foc'] and not r['dis'] for r in rows)
    assert pg.errs == []


# ---------- les copies d'objets lus : un fichier de routes, de datacards, une fiche, un état gardé ----------

@needs_pw
def test_opening_a_route_set_keeps_the_units_and_the_settings_of_the_route_planner(browser):
    pg = shell(browser, 1200, 800)
    fr = open_tool(pg, 'rp')
    o = fr.evaluate("""() => {
      const P = Object.prototype, units0 = JSON.stringify(defaultState().units), gs0 = defaultState().groundSpeed;
      const pt = (n, la, lo) => '{"__proto__": {"alt": 9999}, "name": "' + n + '", "lat": ' + la + ', "lon": ' + lo + ', "alt": 100, "altRef": "AGL"}';
      const th = S.theatre;
      const f = JSON.parse('{"format": "dcs-route-set-v1", "theatre": "' + th + '", "active": 0, "__proto__": {"units": {"distance": "nm", "altitude": "ft"}, "groundSpeed": 999, "name": "leak"},' +
        ' "routes": [{"__proto__": {"name": "leak2"}, "name": "R1", "theatre": "' + th + '", "points": [' + pt('A', 42, 43) + ',' + pt('B', 42.1, 43.1) + ']}]}');
      openRouteSet(f);
      return { units0: units0, units: JSON.stringify(S.units), gs0: gs0, gs: S.groundSpeed, proto: [Object.getPrototypeOf(S) === P, ({}).units === undefined, ({}).alt === undefined],
        n: S.points.length, alts: S.points.map(p => p.alt), name: S.name, units1: JSON.stringify(RSET.routes[RSET.active].units || null) };
    }""")
    assert o['units'] == o['units0'] and o['units'] == '{"distance":"km","altitude":"m"}', o
    assert o['gs'] == o['gs0'] and o['proto'] == [True, True, True], o
    assert o['n'] == 2 and o['alts'] == [100, 100] and o['name'] == 'R1', o
    assert pg.errs == []


@needs_pw
def test_the_datacard_generator_copies_its_documents_and_routes_without_special_keys(browser):
    pg = shell(browser, 1200, 800)
    fr = open_tool(pg, 'dg')
    o = fr.evaluate("""() => {
      const P = Object.prototype, proto = x => Object.getPrototypeOf(x) === P;
      const d = dgCanonDoc(JSON.parse('{"__proto__": {"x": 1}, "format": "f", "cards": []}'));
      const c = { nav: [JSON.parse('{"__proto__": {"x": 1}, "name": "zz", "coord": "", "after": ""}')] };
      const m = dgMergeNav(c, { points: [] });
      const C = dgCommonTheatre();
      const pts = '[{"__proto__": {"alt": 777}, "name": "A", "lat": 42, "lon": 43, "alt": 10, "altRef": "AGL"}, {"name": "B", "lat": 42.1, "lon": 43.1}]';
      const set = biSetFromFile(JSON.parse('{"__proto__": {"units": {"distance": "nm", "altitude": "ft"}}, "active": 0, "routes": [{"name": "R", "theatre": "' + C + '", "points": ' + pts + '}]}'));
      localStorage.setItem(KEY_ROUTE, '{"format": "dcs-route-v1", "__proto__": {"units": {"distance": "nm", "altitude": "ft"}}, "theatre": "' + C + '", "name": "S", "points": ' + pts + '}');
      localStorage.setItem(KEY_ROUTESET, '{"format": "dcs-route-set-v1", "active": 0, "routes": [{"name": "R", "theatre": "' + C + '", "points": ' + pts + '}]}');
      const rs = biReadRouteSet();
      return { doc: [proto(d), d.x, d.format], nav: [m.length, proto(m[0]), m[0] && m[0].x, m[0] && m[0].name],
        set: set ? [JSON.stringify(set.route.units), set.route.points.map(p => p.alt)] : null, read: rs.length ? [JSON.stringify(rs[0].route.units), rs[0].route.points.map(p => p.alt)] : null };
    }""")
    assert o['doc'] == [True, None, 'f'], o
    assert o['nav'] == [1, True, None, 'zz'], o
    assert o['set'] == ['{"distance":"km","altitude":"m"}', [10, 0]], o
    assert o['read'] == ['{"distance":"km","altitude":"m"}', [10, 0]], o
    assert pg.errs == []


@needs_pw
def test_a_failed_migration_note_keeps_the_work_state_without_special_keys(browser):
    pg = shell(browser, 1200, 800)
    fr = open_tool(pg, 'fc')
    o = fr.evaluate("""() => {
      localStorage.setItem(GS_KEY_FC, '{"__proto__": {"a": 1}, "constructor": 5, "v": 2, "sel": "k"}');
      gsMigrateFail();
      const s = JSON.parse(localStorage.getItem(GS_KEY_FC));
      return { keys: Object.keys(s).sort(), failed: s.gsMigrateFailed, a: s.a, sel: s.sel };
    }""")
    assert o['keys'] == ['gsMigrateFailed', 'sel', 'v'] and o['failed'] is True and o['a'] is None and o['sel'] == 'k', o
    assert pg.errs == []


@needs_pw
def test_the_recon_station_reads_its_saved_fields_without_special_keys(browser):
    pg = shell(browser, 1200, 800)
    fr = open_tool(pg, 'rs')
    o = fr.evaluate("""() => {
      const keys0 = Object.keys(STATE.fields).sort();
      localStorage.setItem(KEY_STATE, '{"fields": {"__proto__": {"x": 1}, "constructor": "c", "' + keys0[0] + '": "valeur"}}');
      restoreState();
      return { keys0: keys0, keys: Object.keys(STATE.fields).sort(), first: STATE.fields[keys0[0]], proto: Object.getPrototypeOf(STATE.fields) === Object.prototype };
    }""")
    assert o['keys'] == o['keys0'] and o['first'] == 'valeur' and o['proto'] is True, o
    assert pg.errs == []


# ---------- HQ, joué par node : la route d'un paquet remplace celle du groupe sans clé spéciale ----------

NODE = shutil.which('node')


def hq_fn(src, name):
    i = src.index('function %s(' % name)
    j = src.index('{', i)
    depth, k = 0, j
    while True:
        c = src[k]
        depth += c == '{'
        depth -= c == '}'
        if depth == 0:
            return src[i:k + 1]
        k += 1


@pytest.mark.skipif(NODE is None, reason='node absent')
def test_hq_plans_a_package_route_without_special_keys():
    src = (ROOT / 'dist' / 'dcs_hq.html').read_text(encoding='utf-8')
    pre = '\n'.join([hq_fn(src, n) for n in ('uiKeyOk', 'pkPlanFlight', 'pkIsNum', 'pkStartsElsewhere', 'pkTheatreOf')] + [
        "function _extractRouteAndPayloads() { return { pointsNode: { kind: 'table', entries: [{ key: { kind: 'int', value: 1 }, value: {} }] } }; }",
        "function luaTableReproducible() { return true; }", "function astToValue() { return { x: 0, y: 0, type: 'Turning Point' }; }",
    ])
    body = """
      const fl = { groupName: 'G', units: [], chk: { route: true, radios: false, loadout: false, livery: false }, avail: { route: true, radios: true, loadout: true, livery: true },
        route: JSON.parse('{"__proto__": {"x": 1, "y": 1}, "1": {"x": 0, "y": 0}, "2": {"x": 5, "y": 5}, "3": {"x": 6, "y": 6}}') };
      const r = pkPlanFlight({ theatre: 'Syria', ast: {} }, { theatre: 'Syria' }, fl, { group: { groupId: 7, pointsPos: true }, units: [] });
      const pts = r.plan.replacements.route.points;
      console.log(JSON.stringify({ proto: Object.getPrototypeOf(pts) === Object.prototype, x: pts.x === undefined, keys: Object.keys(pts), n: r.done.route }));
    """
    r = subprocess.run([NODE, '-e', pre + '\n' + body], capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr
    o = json.loads(r.stdout)
    assert o == {'proto': True, 'x': True, 'keys': ['1', '2', '3'], 'n': 3}, o


# ---------- le dessin, le clavier à l'écran ouvert : la carte en grand ne couvre pas la barre de dessin ----------

@needs_pw
def test_the_on_screen_keyboard_keeps_the_drawing_bar_above_it(browser):
    pg = shell(browser, 345, 590, touch=True, init=SPLIT_SEED)
    examples(pg)
    fr = open_tool(pg, 'rp', touch=True)
    hide_toasts(pg, fr)
    tap(pg, fr, '#tapmode [data-tap="draw"]')
    pg.wait_for_timeout(500)
    o = fr.evaluate("""() => {
      const root = document.documentElement;
      root.classList.add('ui-kb'); root.style.setProperty('--ui-kb-bottom', '250px'); spSync();       /* ce que fait le clavier à l'écran : la classe, la marge, puis la mise en page */
      const top = innerHeight - 250, r = s => { const e = document.querySelector(s); if (!e) return null; const b = e.getBoundingClientRect(); return { t: b.top, b: b.bottom, h: b.height }; };
      const out = { full: document.body.classList.contains('rp-mapfull'), top: top, app: r('.app'), drui: r('#dr-ui'), map: r('#map') };
      root.classList.remove('ui-kb'); root.style.removeProperty('--ui-kb-bottom'); spSync();
      out.after = r('.app');
      return out;
    }""")
    assert o['full'] and o['drui'] and o['drui']['h'] > 0, o
    assert o['app']['b'] <= o['top'] + 0.5, o
    assert o['drui']['b'] <= o['top'] + 0.5, o
    assert abs(o['after']['b'] - 590) <= 1, o
    assert pg.errs == []


@pytest.mark.skipif(NODE is None, reason='node absent')
def test_hq_builds_a_group_from_a_package_route_without_special_keys():
    import test_hq_parking as HP
    out = HP.run(HP.BUILD + """
      const route = JSON.parse('{"__proto__": {"x": 1}, "1": {"x": -35775.78, "y": -268903.87, "alt": 0, "alt_type": "BARO", "type": "Turning Point", "action": "Turning Point", "speed": 61.11, "name": "A"},' +
        ' "2": {"__proto__": {"x": 1}, "constructor": 4, "x": -26026.17, "y": -297606.2, "alt": 30, "alt_type": "RADIO", "speed": 61.11, "name": "B", "foo": 3}}');
      const g = pkBuildGroup(work, fl({ route: route })).group, P = Object.prototype;
      const p2 = g.route.points[2];
      console.log(JSON.stringify({ n: Object.keys(g.route.points).length, protos: Object.values(g.route.points).map(p => Object.getPrototypeOf(p) === P), keys: Object.keys(p2).filter(k => ['foo', 'constructor', '__proto__', 'x'].indexOf(k) >= 0).sort() }));
    """)
    assert out['n'] == 2 and out['protos'] == [True, True] and out['keys'] == ['foo', 'x'], out
