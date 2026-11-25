"""Route Planner au téléphone (MP-V2.1.0+17) : la pastille des menaces disparaît au décochage, se pose en bas à droite, 6 px au-dessus des crédits de la carte, part repliée (« ± » montre « − » et « + ») ;
la carte en grand (cadre d'export, dessin) garde son centre et son zoom.
Joué sur le shell construit (dist/dcs_mission_plan.html, chromium), sans réseau : le banc de test_rp_menaces sert le relief. Les contrôles passent par le DOM, jamais par une capture."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tests'))
from test_rp_menaces import (browser, display, needs_pw, open_rp, ready, setup, sym)  # noqa: E402,F401

BOX = """() => { const q = s => document.querySelector(s), b = q('#rp-thr'), cs = getComputedStyle(b), r = b.getBoundingClientRect(), m = q('#map').getBoundingClientRect();
  return { hidden: b.hidden, display: cs.display, w: r.width, h: r.height, pill: b.classList.contains('thr-pill'), style: b.getAttribute('style'), mapw: m.width, bottom: parseFloat(cs.bottom) }; }"""
GAP = """() => { const q = s => document.querySelector(s), b = q('#rp-thr').getBoundingClientRect(), a = q('.leaflet-control-attribution').getBoundingClientRect(), m = q('#map').getBoundingClientRect();
  const hit = (x, y) => x.left < y.right && y.left < x.right && x.top < y.bottom && y.top < x.bottom;
  const ctl = Array.from(document.querySelectorAll('#map .leaflet-control, #map .rp-search-btn, #map #tapmode, #map .rl-bar, #map [role=status], #map [role=alert]')).filter(e => !e.contains(q('#rp-thr'))).map(e => e.getBoundingClientRect()).filter(e => e.width > 0 && e.height > 0);
  return { gap: a.top - b.bottom, ah: a.height, over: ctl.filter(e => hit(e, b)).length, inside: b.top >= m.top && b.left >= m.left && b.right <= m.right && b.bottom <= m.bottom }; }"""
FOLD = """() => { const q = s => document.querySelector(s), b = q('#rp-thr'), f = q('#rp-thr .thr-fold'), r = e => { const x = e.getBoundingClientRect(); return [Math.round(x.width * 10) / 10, Math.round(x.height * 10) / 10]; };
  const vis = Array.from(b.querySelectorAll('.thr-b')).filter(e => getComputedStyle(e).display !== 'none');
  return { pill: r(b), fold: f ? r(f) : null, text: f ? f.textContent : null, exp: f ? f.getAttribute('aria-expanded') : null, label: f ? f.getAttribute('aria-label') : null,
    focus: !!f && document.activeElement === f, steps: vis.map(e => [e.textContent].concat(r(e))), v: (q('#thr-v') || {}).textContent, title: b.querySelector('.thr-t').textContent, shut: b.classList.contains('thr-shut'),
    sepf: f ? getComputedStyle(f).borderLeftWidth : null, sepb: (b.querySelector('.thr-b') ? getComputedStyle(b.querySelector('.thr-b')).borderLeftWidth : null), range: !!q('#thr-range') }; }"""
STORE = "() => JSON.stringify(Object.keys(localStorage).sort().map(k => [k, localStorage.getItem(k)]))"


def tick_threats(fr, pg):
    display(fr, pg, True)
    fr.evaluate("document.querySelector('#dsp-panel [data-k=threats]').click()")
    pg.wait_for_timeout(500)
    display(fr, pg, False)


def tick_relief(fr, pg):
    display(fr, pg, True)
    fr.evaluate("document.querySelector('#dsp-panel [data-k=relief]').click()")
    pg.wait_for_timeout(900)
    display(fr, pg, False)


def settle(pg, n=3):
    for _ in range(n):
        pg.evaluate("() => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))")
    pg.wait_for_timeout(120)


def gap(fr):
    return fr.evaluate(GAP)


def tap_on(pg, fr, sel):
    off = pg.evaluate("(() => { const f = document.getElementById('iframe-rp').getBoundingClientRect(); return [f.left, f.top]; })()")
    c = fr.evaluate("(s) => { const r = document.querySelector(s).getBoundingClientRect(); return [r.left + r.width / 2, r.top + r.height / 2]; }", sel)
    pg.touchscreen.tap(off[0] + c[0], off[1] + c[1])
    pg.wait_for_timeout(250)


# ---------- règle 1 : décoché, la pastille disparaît ----------
@needs_pw
@pytest.mark.parametrize('w,h', [(345, 590), (360, 780), (412, 860), (1280, 800)])
def test_unticked_the_box_is_not_shown_pill_included(browser, w, h):
    pg, fr = open_rp(browser, w=w, h=h)
    setup(fr, [sym(0, 'sa-8')])
    on = fr.evaluate(BOX)
    assert on['hidden'] is False and on['display'] != 'none' and on['w'] > 0 and on['h'] > 0 and on['pill'] == (w < 760)
    for step in range(2):
        tick_threats(fr, pg)
        off = fr.evaluate(BOX)
        assert off['hidden'] is True and off['display'] == 'none' and off['w'] == 0 and off['h'] == 0, (step, off)
        tick_threats(fr, pg)
        again = fr.evaluate(BOX)
        assert again['hidden'] is False and again['display'] == on['display'] and again['w'] == on['w'] and again['h'] == on['h'], (step, again)
    # les autres conditions d'affichage ne changent pas : le dessin, la règle et l'export le cachent encore ; le retour le rend
    for mode in ('draw', 'ruler'):
        fr.evaluate("(m) => setTapMode(m)", mode)
        assert fr.evaluate("document.getElementById('rp-thr').hidden") is True and fr.evaluate(BOX)['display'] == 'none', mode
    fr.evaluate("setTapMode('read')")
    assert fr.evaluate(BOX)['display'] == on['display']
    fr.evaluate("expOpen()")
    assert fr.evaluate(BOX)['display'] == 'none'
    fr.evaluate("expClose()")
    assert fr.evaluate(BOX)['display'] == on['display']
    assert pg.errs == []
    pg.context.close()


# ---------- règle 2 : 6 px au-dessus des crédits, la mesure suit ----------
@needs_pw
@pytest.mark.parametrize('w,h', [(345, 590), (360, 780), (412, 860)])
def test_the_pill_sits_6px_above_the_map_credits_in_both_languages_with_and_without_relief(browser, w, h):
    pg, fr = open_rp(browser, w=w, h=h, lang='fr')
    setup(fr, [sym(0, 'sa-8')])
    assert fr.evaluate(BOX)['pill'] is True
    seen = set()
    for lang in ('fr', 'en'):
        fr.evaluate("(l) => setLang(l)", lang)
        for relief in (False, True, False):
            if fr.evaluate("DISP.relief") != relief:
                tick_relief(fr, pg)
            settle(pg)
            g = gap(fr)
            seen.add(g['ah'])
            assert abs(g['gap'] - 6) <= 1 and g['over'] == 0 and g['inside'] is True, (w, lang, relief, g)
    # la mention change de hauteur pendant que la pastille est affichée : elle suit
    h0 = gap(fr)['ah']
    fr.evaluate("__RP.map.attributionControl.addAttribution('Données de test, ' + 'une très longue mention de carte, '.repeat(14))")
    settle(pg)
    g = gap(fr)
    assert g['ah'] > h0 + 5 and abs(g['gap'] - 6) <= 1 and g['over'] == 0, (h0, g)
    fr.evaluate("__RP.map.attributionControl.removeAttribution('Données de test, ' + 'une très longue mention de carte, '.repeat(14))")
    settle(pg)
    g = gap(fr)
    assert g['ah'] == h0 and abs(g['gap'] - 6) <= 1, (h0, g)
    # le fond de carte change : la mention aussi, la pastille suit
    ids = fr.evaluate("LAYER_IDS.filter(i => i !== S.ui.layer)")
    for i in ids[:3]:
        fr.evaluate("(i) => dspSetBase(i)", i)
        settle(pg)
        g = gap(fr)
        assert abs(g['gap'] - 6) <= 1 and g['over'] == 0, (i, g)
    assert pg.errs == []
    pg.context.close()


@needs_pw
def test_the_pill_follows_the_credits_when_the_phone_turns_and_the_wide_box_is_left_alone(browser):
    pg, fr = open_rp(browser, w=360, h=780)
    setup(fr, [sym(0, 'sa-8')])
    assert abs(gap(fr)['gap'] - 6) <= 1
    # paysage étroit (740 de large) : toujours une pastille
    pg.set_viewport_size({'width': 740, 'height': 360})
    settle(pg, 5)
    b = fr.evaluate(BOX)
    g = gap(fr)
    assert b['pill'] is True and b['mapw'] < 760 and abs(g['gap'] - 6) <= 1 and g['over'] == 0, (b, g)
    # 915 × 412 : la carte est large, le cartouche large ne reçoit rien (ni classe, ni style en ligne, ni écart propre à la pastille)
    pg.set_viewport_size({'width': 915, 'height': 412})
    settle(pg, 5)
    b = fr.evaluate(BOX)
    g = gap(fr)
    assert b['pill'] is False and b['style'] is None and b['bottom'] == 28 and b['mapw'] >= 760, (b, g)       # le cartouche large recouvre déjà des contrôles à la base à cette hauteur de carte (140 px) : non corrigé, non mesuré ici
    pg.set_viewport_size({'width': 360, 'height': 780})
    settle(pg, 5)
    assert fr.evaluate(BOX)['pill'] is True and abs(gap(fr)['gap'] - 6) <= 1
    assert pg.errs == []
    pg.context.close()


@needs_pw
def test_the_wide_box_is_the_same_as_before_at_1280_and_1440(browser):
    for w, h in ((1280, 800), (1440, 900)):
        pg, fr = open_rp(browser, w=w, h=h)
        setup(fr, [sym(0, 'sa-8')])
        r = fr.evaluate("""() => { const b = document.getElementById('rp-thr'), cs = getComputedStyle(b), q = b.getBoundingClientRect(), m = document.getElementById('map').getBoundingClientRect();
          return { cls: b.className, style: b.getAttribute('style'), left: q.left - m.left, bottom: m.bottom - q.bottom, w: q.width, h: q.height, cb: cs.bottom, disp: cs.display, kids: b.children.length,
            fold: !!b.querySelector('.thr-fold'), btn: b.querySelectorAll('.thr-b').length, range: !!document.getElementById('thr-range') }; }""")
        assert r['cls'] == '' and r['style'] is None and r['left'] == 10 and r['bottom'] == 28 and r['w'] == 280 and r['cb'] == '28px' and r['fold'] is False and r['btn'] == 0 and r['range'] is True, r
        pg.context.close()


# ---------- règle 3 : repliée par défaut ----------
@needs_pw
def test_the_pill_starts_folded_and_the_plus_minus_button_unfolds_and_folds_by_touch_and_keyboard(browser):
    pg, fr = open_rp(browser, w=345, h=590)
    setup(fr, [sym(0, 'sa-8')])
    ls0, ss0, disp0 = fr.evaluate(STORE), pg.evaluate(STORE), fr.evaluate("JSON.stringify(DISP)")
    f = fr.evaluate(FOLD)
    assert f['pill'][1] == 44 and f['fold'] == [44, 44] and f['text'] == '±' and f['exp'] == 'false' and f['label'] == 'Régler la hauteur' and f['steps'] == [] and f['shut'] is True and f['range'] is False, f
    assert f['title'] == 'MENACES' and f['v'] == '30 m sol'
    folded_w = f['pill'][0]
    # un toucher déplie
    tap_on(pg, fr, '#rp-thr .thr-fold')
    f = fr.evaluate(FOLD)
    assert f['text'] == '‹' and f['exp'] == 'true' and f['label'] == 'Replier' and f['focus'] is True and f['shut'] is False, f
    assert f['steps'] == [['−', 44, 44], ['+', 44, 44]] and f['fold'] == [44, 44] and f['pill'][1] == 44 and f['pill'][0] == folded_w + 88 and f['sepf'] == f['sepb'] == '1px', f
    # un toucher replie
    tap_on(pg, fr, '#rp-thr .thr-fold')
    f = fr.evaluate(FOLD)
    assert f['text'] == '±' and f['exp'] == 'false' and f['focus'] is True and f['steps'] == [] and f['pill'][0] == folded_w, f
    # le clavier : Entrée déplie, Espace replie, le focus reste
    fr.evaluate("document.querySelector('#rp-thr .thr-fold').focus()")
    pg.keyboard.press('Enter')
    pg.wait_for_timeout(150)
    f = fr.evaluate(FOLD)
    assert f['exp'] == 'true' and f['text'] == '‹' and f['focus'] is True and len(f['steps']) == 2, f
    pg.keyboard.press('Space')
    pg.wait_for_timeout(150)
    f = fr.evaluate(FOLD)
    assert f['exp'] == 'false' and f['text'] == '±' and f['focus'] is True and f['steps'] == [], f
    # le clic de la souris
    fr.evaluate("document.querySelector('#rp-thr .thr-fold').click()")
    assert fr.evaluate(FOLD)['exp'] == 'true'
    # le geste d'état n'a rien écrit : le stockage de la page et celui de l'outil sont ceux d'avant (ni DISP, ni fichier de travail)
    assert fr.evaluate(STORE) == ls0 and pg.evaluate(STORE) == ss0
    assert fr.evaluate("JSON.stringify(DISP)") == disp0
    # « − » et « + » font ce qu'ils font : la hauteur monte d'un cran
    fr.evaluate("document.querySelector('#rp-thr .thr-b[data-d=\"1\"]').click()")
    assert fr.evaluate("[DISP.thrStep, document.getElementById('thr-v').textContent]") == [3, '60 m sol']
    assert pg.errs == []
    pg.context.close()


@needs_pw
def test_the_fold_button_says_it_in_english_and_a_recalculation_keeps_the_state(browser):
    pg, fr = open_rp(browser, w=360, h=780)
    setup(fr, [sym(0, 'sa-8')])
    fr.evaluate("setLang('en')")
    settle(pg)
    f = fr.evaluate(FOLD)
    assert f['label'] == 'Set the height' and f['text'] == '±' and f['title'] == 'THREATS' and f['v'] == '30 m AGL', f
    fr.evaluate("document.querySelector('#rp-thr .thr-fold').click()")
    f = fr.evaluate(FOLD)
    assert f['label'] == 'Fold' and f['text'] == '‹' and f['exp'] == 'true' and [s[0] for s in f['steps']] == ['−', '+'], f
    assert fr.evaluate("[...document.querySelectorAll('#rp-thr .thr-b')].map(e => e.getAttribute('aria-label'))") == ['Lower', 'Higher']
    # la langue, les unités, l'état du relief, la hauteur maximale : le cartouche est refait, l'état courant reste
    fr.evaluate("setLang('fr')")
    settle(pg)
    f = fr.evaluate(FOLD)
    assert f['exp'] == 'true' and f['label'] == 'Replier' and f['text'] == '‹' and len(f['steps']) == 2 and f['v'] == '30 m sol', f
    fr.evaluate("S.units.altitude = 'ft'; renderAll();")
    settle(pg)
    f = fr.evaluate(FOLD)
    assert f['exp'] == 'true' and len(f['steps']) == 2 and f['v'].endswith('ft sol'), f
    fr.evaluate("S.units.altitude = 'm'; renderAll();")
    tick_relief(fr, pg)
    settle(pg)
    assert fr.evaluate(FOLD)['exp'] == 'true'
    assert fr.evaluate("document.querySelectorAll('#rp-thr .thr-fold').length") == 1
    assert pg.errs == []
    pg.context.close()


@needs_pw
def test_every_opening_of_the_route_planner_starts_folded(browser):
    pg, fr = open_rp(browser, w=360, h=780)
    setup(fr, [sym(0, 'sa-8')])
    fr.evaluate("document.querySelector('#rp-thr .thr-fold').click()")
    assert fr.evaluate(FOLD)['exp'] == 'true'
    # le shell réaffiche l'outil : repliée
    pg.evaluate("openModule('dg')")
    pg.wait_for_timeout(1500)
    pg.evaluate("openModule('rp')")
    pg.wait_for_timeout(800)
    f = fr.evaluate(FOLD)
    assert f['exp'] == 'false' and f['text'] == '±' and f['steps'] == [], f
    # le rechargement : repliée
    fr.evaluate("document.querySelector('#rp-thr .thr-fold').click()")
    assert fr.evaluate(FOLD)['exp'] == 'true'
    pg.reload(wait_until='commit')
    pg.wait_for_function("typeof NAV !== 'undefined' && typeof openModule === 'function'", timeout=30000)
    pg.wait_for_timeout(800)
    pg.evaluate("openModule('rp')")
    pg.wait_for_timeout(2300)
    fr2 = next(x for x in pg.frames if x != pg.main_frame and x.evaluate("typeof window.__RP !== 'undefined'"))
    assert fr2.evaluate("__RP.thr.open") is False                                   # en mémoire, à la création du cartouche : repliée
    if fr2.evaluate("S.theatre") != 'Syria':                                         # le théâtre de l'exemple n'est pas toujours déjà écrit au rechargement
        fr2.evaluate("(id) => { const s = document.getElementById('theatre'); s.value = id; s.dispatchEvent(new Event('change', { bubbles: true })); }", 'Syria')
        pg.wait_for_timeout(900)
    setup(fr2, [sym(0, 'sa-8')])
    f = fr2.evaluate(FOLD)
    assert f['exp'] == 'false' and f['text'] == '±' and f['steps'] == [], f
    assert pg.errs == []
    pg.context.close()


@needs_pw
def test_without_the_tint_the_pill_has_no_button_and_nothing_changes(browser):
    pg, fr = open_rp(browser, w=360, h=780, doc=False)
    setup(fr, [sym(0, 'sa-8')], wait=False)
    pg.wait_for_timeout(1500)
    r = fr.evaluate("""() => { const b = document.getElementById('rp-thr'); return { state: __RP.thr.state, pill: b.classList.contains('thr-pill'), shut: b.classList.contains('thr-shut'), hidden: b.hidden,
      fold: !!b.querySelector('.thr-fold'), btn: b.querySelectorAll('button').length, src: b.querySelector('.thr-src').textContent, h: b.getBoundingClientRect().height }; }""")
    assert r['state'] == 'err' and r['pill'] is True and r['shut'] is False and r['hidden'] is False and r['fold'] is False and r['btn'] == 0 and r['h'] == 44 and r['src'], r
    g = gap(fr)
    assert abs(g['gap'] - 6) <= 1 and g['over'] == 0, g
    assert pg.errs == []
    pg.context.close()


@needs_pw
def test_the_fold_glyphs_have_a_contrast_of_4_5_on_the_pill_in_the_four_themes(browser):
    pg, fr = open_rp(browser, w=360, h=780)
    setup(fr, [sym(0, 'sa-8')])
    js = """(th) => { document.body.setAttribute('data-theme', th);
      const lum = c => { const f = v => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); }; return 0.2126 * f(c[0]) + 0.7152 * f(c[1]) + 0.0722 * f(c[2]); };
      const num = s => s.match(/[\\d.]+/g).map(Number), b = document.getElementById('rp-thr'), f = b.querySelector('.thr-fold');
      const bg = num(getComputedStyle(b).backgroundColor), a = bg.length > 3 ? bg[3] : 1, fg = num(getComputedStyle(f).color);
      const out = {};
      [[255, 255, 255], [240, 232, 214], [0, 0, 0]].forEach(m => { const c = [0, 1, 2].map(i => a * bg[i] + (1 - a) * m[i]), l1 = lum(fg), l2 = lum(c); out[m.join(',')] = (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05); });
      return out; }"""
    for th in ('cw-nato', 'cw-soviet', 'modern-east', 'modern-nato'):
        for state in (False, True):
            fr.evaluate("(o) => { const f = document.querySelector('#rp-thr .thr-fold'); if ((f.getAttribute('aria-expanded') === 'true') !== o) f.click(); }", state)
            c = fr.evaluate(js, th)
            assert min(c.values()) >= 4.5, (th, state, c)
    assert pg.errs == []
    pg.context.close()


# ---------- règle 4 : la carte en grand garde son centre ----------
VIEW = "() => { const m = __RP.map, c = m.getCenter(), s = m.getSize(); return { lat: c.lat, lng: c.lng, z: m.getZoom(), w: s.x, h: s.y }; }"
DRIFT = """([a, b]) => { const m = __RP.map; return m.project(L.latLng(a.lat, a.lng), a.z).distanceTo(m.project(L.latLng(b.lat, b.lng), a.z)); }"""


def aim(fr, pg):
    fr.evaluate("__RP.map.setView([34.2, 36.0], 9, { animate: false })")
    pg.wait_for_timeout(500)


@needs_pw
@pytest.mark.parametrize('w,h', [(345, 590), (915, 412)])
def test_the_big_map_keeps_its_centre_and_zoom_in_and_out_for_the_export_and_the_drawing(browser, w, h):
    pg, fr = open_rp(browser, w=w, h=h)
    setup(fr, [sym(0, 'sa-8')])
    aim(fr, pg)
    v0 = fr.evaluate(VIEW)
    for kind in ('export', 'draw'):
        if kind == 'export':
            fr.evaluate("expOpen()")
        else:
            fr.evaluate("setTapMode('draw')")
        pg.wait_for_timeout(600)
        vin = fr.evaluate(VIEW)
        assert vin['h'] > v0['h'] + 20, (kind, v0, vin)                      # la carte a bien pris de la hauteur
        assert vin['z'] == v0['z'] and fr.evaluate(DRIFT, [v0, vin]) <= 1, (kind, 'entrée', v0, vin, fr.evaluate(DRIFT, [v0, vin]))
        if kind == 'export':
            fr.evaluate("expClose()")
        else:
            fr.evaluate("setTapMode('read')")
        pg.wait_for_timeout(600)
        vout = fr.evaluate(VIEW)
        assert abs(vout['h'] - v0['h']) <= 1
        assert vout['z'] == v0['z'] and fr.evaluate(DRIFT, [v0, vout]) <= 1, (kind, 'sortie', v0, vout, fr.evaluate(DRIFT, [v0, vout]))
    # l'export puis le dessin l'un dans l'autre : le centre reste
    fr.evaluate("setTapMode('draw')")
    pg.wait_for_timeout(400)
    fr.evaluate("expOpen()")
    pg.wait_for_timeout(500)
    assert fr.evaluate(DRIFT, [v0, fr.evaluate(VIEW)]) <= 1
    fr.evaluate("expClose()")
    pg.wait_for_timeout(500)
    fr.evaluate("setTapMode('read')")
    pg.wait_for_timeout(500)
    vend = fr.evaluate(VIEW)
    assert vend['z'] == v0['z'] and fr.evaluate(DRIFT, [v0, vend]) <= 1 and abs(vend['h'] - v0['h']) <= 1
    # le cadre d'export se calcule comme à la base, sur la vue recentrée : au plus grand qui tient, centré dans la place au-dessus de la barre
    fr.evaluate("expOpen()")
    pg.wait_for_timeout(500)
    e = fr.evaluate("() => ({ r: EXP.rect, W: document.getElementById('map').clientWidth })")
    assert e['r'] and abs(e['r']['x'] - round((e['W'] - e['r']['w']) / 2)) <= 1
    fr.evaluate("expClose()")
    assert pg.errs == []
    pg.context.close()


@needs_pw
def test_dragging_the_handle_keeps_the_top_left_corner_as_before(browser):
    pg, fr = open_rp(browser, w=345, h=590)
    setup(fr, [sym(0, 'sa-8')])
    aim(fr, pg)
    tl0 = fr.evaluate("(() => { const p = __RP.map.containerPointToLatLng([0, 0]); return [p.lat, p.lng]; })()")
    v0 = fr.evaluate(VIEW)
    off = pg.evaluate("(() => { const f = document.getElementById('iframe-rp').getBoundingClientRect(); return [f.left, f.top]; })()")
    c = fr.evaluate("(() => { const r = document.getElementById('rp-split').getBoundingClientRect(); return [r.left + r.width / 2, r.top + r.height / 2]; })()")
    x, y = off[0] + c[0], off[1] + c[1]
    pg.mouse.move(x, y)
    pg.mouse.down()
    pg.mouse.move(x, y + 30, steps=4)
    pg.mouse.move(x, y + 60, steps=4)
    pg.mouse.up()
    pg.wait_for_timeout(500)
    v1 = fr.evaluate(VIEW)
    assert v1['h'] > v0['h'] + 20, (v0, v1)
    pt = fr.evaluate("(tl) => { const p = __RP.map.latLngToContainerPoint(L.latLng(tl[0], tl[1])); return [p.x, p.y]; }", tl0)
    assert abs(pt[0]) <= 1 and abs(pt[1]) <= 1, pt                                    # le coin haut gauche est resté en place
    assert fr.evaluate(DRIFT, [v0, v1]) > 20                                          # le centre, lui, a glissé : c'est le comportement de la base
    assert pg.errs == []
    pg.context.close()


# ---------- le texte et le numéro ----------
def test_the_field_manual_says_it_and_the_build_number_is_17():
    fm = (ROOT / 'dist' / 'dcs_field_manual.html').read_text(encoding='utf-8')
    rp = fm[fm.index('<section id="page-rp"'):fm.index('<!-- /page-rp -->')]
    assert 'au téléphone, c’est une pastille repliée, en bas à droite au-dessus des crédits de la carte : <strong>±</strong> y montre <strong>−</strong> et <strong>+</strong>.' in rp
    assert 'on a phone it is a folded pill at the bottom right, above the map credits: <strong>±</strong> shows <strong>−</strong> and <strong>+</strong>.' in rp
    assert 'une pastille avec <strong>−</strong>' not in rp and 'it is a pill with' not in rp
    assert 'DEV_BUILD = 17' in (ROOT / 'version_block.py').read_text(encoding='utf-8')
    rpd = (ROOT / 'dist' / 'dcs_route_planner.html').read_text(encoding='utf-8')
    for k in ('thr.set', 'thr.fold'):
        assert rpd.count("    '%s': '" % k) == 2, k
    css = rpd[rpd.index('#rp-thr.thr-pill {'):]
    assert css.index('#rp-thr[hidden] { display: none; }') > css.index('#rp-thr.thr-pill {') and '!important' not in css[css.index('#rp-thr[hidden]'):css.index('#rp-thr[hidden]') + 60]


# ---------- règle 2 (décision) : calée à droite, rien ne recouvre aucun contrôle de la carte ----------
NEAR = """() => { const q = s => document.querySelector(s), b = q('#rp-thr').getBoundingClientRect(), m = q('#map').getBoundingClientRect();
  const hit = (x, y) => x.left < y.right && y.left < x.right && x.top < y.bottom && y.top < x.bottom;
  const els = Array.from(document.querySelectorAll('#map .leaflet-control, #map .rp-search-btn, #map #tapmode, #map .rl-bar, #map [role=status], #map [role=alert]')).filter(e => !e.contains(q('#rp-thr')) && e.getBoundingClientRect().width > 0);
  const d = els.map(e => { const r = e.getBoundingClientRect(); return { over: hit(r, b), dy: Math.max(r.top - b.bottom, b.top - r.bottom), dx: Math.max(r.left - b.right, b.left - r.right), cls: String(e.className).slice(0, 30) }; });
  return { right: Math.round((m.right - b.right) * 10) / 10, over: d.filter(x => x.over).map(x => x.cls), near: d.filter(x => !x.over).sort((x, y) => Math.max(x.dx, x.dy) - Math.max(y.dx, y.dy))[0] || null }; }"""


@needs_pw
@pytest.mark.parametrize('w,h', [(345, 590), (360, 640), (360, 780), (412, 732), (740, 360), (600, 360)])
def test_the_pill_sits_at_the_right_and_covers_no_map_control_folded_or_unfolded(browser, w, h):
    pg, fr = open_rp(browser, w=w, h=h)
    setup(fr, [sym(0, 'sa-8')])
    for lang in ('fr', 'en'):
        fr.evaluate("(l) => setLang(l)", lang)
        for open_ in (False, True):
            fr.evaluate("(o) => { const f = document.querySelector('#rp-thr .thr-fold'); if ((f.getAttribute('aria-expanded') === 'true') !== o) f.click(); }", open_)
            settle(pg)
            n = fr.evaluate(NEAR)
            g = gap(fr)
            assert fr.evaluate(BOX)['pill'] is True and abs(n['right'] - 8) <= 1 and n['over'] == [] and g['inside'] is True and abs(g['gap'] - 6) <= 1, (w, h, lang, open_, n, g)
    assert pg.errs == []
    pg.context.close()


# ---------- règle 4 : le centre pris quand la carte a une taille ----------
@needs_pw
@pytest.mark.parametrize('w,h', [(345, 590), (915, 412)])
def test_the_big_map_keeps_its_centre_when_the_tool_is_left_and_come_back_to_during_the_drawing(browser, w, h):
    pg, fr = open_rp(browser, w=w, h=h)
    setup(fr, [sym(0, 'sa-8')])
    aim(fr, pg)
    v0 = fr.evaluate(VIEW)
    fr.evaluate("setTapMode('draw')")
    pg.wait_for_timeout(600)
    pg.evaluate("openModule('dg')")
    pg.wait_for_timeout(1200)
    pg.evaluate("openModule('rp')")
    pg.wait_for_timeout(1500)
    v1 = fr.evaluate(VIEW)
    assert fr.evaluate("tapMode") == 'read' and v1['z'] == v0['z'] and abs(v1['h'] - v0['h']) <= 1 and fr.evaluate(DRIFT, [v0, v1]) <= 1, (v0, v1, fr.evaluate(DRIFT, [v0, v1]))
    # l'export : le cadre RESTE ouvert quand le shell cache puis réaffiche le RP (mesuré) ; la carte reste en grand, le centre aussi ; la fermeture rend la hauteur
    fr.evaluate("expOpen()")
    pg.wait_for_timeout(600)
    pg.evaluate("openModule('dg')")
    pg.wait_for_timeout(1200)
    assert fr.evaluate("EXP.on") is True
    pg.evaluate("openModule('rp')")
    pg.wait_for_timeout(1500)
    assert fr.evaluate("EXP.on") is True and fr.evaluate("document.body.classList.contains('rp-mapfull-exp')")
    vo = fr.evaluate(VIEW)
    assert vo['h'] > v0['h'] + 20 and vo['z'] == v0['z'] and fr.evaluate(DRIFT, [v0, vo]) <= 1, (v0, vo)
    fr.evaluate("expClose()")
    pg.wait_for_timeout(600)
    v2 = fr.evaluate(VIEW)
    assert abs(v2['h'] - v0['h']) <= 1 and v2['z'] == v0['z'] and fr.evaluate(DRIFT, [v0, v2]) <= 1, (v0, v2)
    assert pg.errs == []
    pg.context.close()


@needs_pw
def test_above_1100_px_the_big_map_calls_no_move_at_all(browser):
    pg, fr = open_rp(browser, w=1280, h=800)
    setup(fr, [sym(0, 'sa-8')])
    aim(fr, pg)
    fr.evaluate("window.__ev = {}; ['movestart', 'moveend'].forEach(n => __RP.map.on(n, () => { __ev[n] = (__ev[n] || 0) + 1; }))")
    for a, b in (("expOpen()", "expClose()"), ("setTapMode('draw')", "setTapMode('read')")):
        fr.evaluate(a)
        pg.wait_for_timeout(700)
        fr.evaluate(b)
        pg.wait_for_timeout(700)
    assert fr.evaluate("window.__ev") == {}
    assert pg.errs == []
    pg.context.close()
