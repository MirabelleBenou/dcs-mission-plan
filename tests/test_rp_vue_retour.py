"""Route Planner (MP-V2.1.0+20) : quitter le RP pour un autre outil puis y revenir ne déplace plus la carte.
Joué sur le shell construit (dist/dcs_mission_plan.html, chromium), sans réseau : le banc de test_rp_menaces sert le relief. Les contrôles passent par le DOM, jamais par une capture.
Jusqu'à 1 100 px de large (là où la carte et le panneau se partagent l'écran), le retour rend le centre (±1 px à l'écran) et le zoom de la vue vue juste avant le départ, quel que soit le mode,
avec ou sans le Profil du sol ; tourné pendant l'absence, le même centre et le même zoom, à la hauteur de la nouvelle orientation ; au-dessus de 1 100 px, aucun appel de plus."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tests'))
from test_rp_menaces import (browser, display, needs_pw, open_rp, ready, setup, sym)  # noqa: E402,F401
from test_rp_menaces_pastille import DRIFT, STORE, VIEW  # noqa: E402,F401
from test_rp_profil import tick  # noqa: E402

SIZES = [(345, 590), (412, 860), (915, 412), (1100, 800)]
OTHERS = ('dg', 'bg', 'hq')
RECT = """() => { const r = s => { const e = document.querySelector(s); if (!e) return null; const b = e.getBoundingClientRect(); return [Math.round(b.width * 10) / 10, Math.round(b.height * 10) / 10]; };
  return { map: r('#map'), prof: r('#rp-prof'), wrap: r('.mapwrap'), fold: !!DISP.profFold, ph: __RP.prof.h }; }"""
CALLS = "window.__calls = []; ['invalidateSize', 'setView', 'panBy'].forEach(n => { const f = __RP.map[n]; __RP.map[n] = function () { window.__calls.push(n); return f.apply(this, arguments); }; });"


def aim(fr, pg):
    fr.evaluate("__RP.map.setView([34.2, 36.0], 9, { animate: false })")
    pg.wait_for_timeout(500)


def prepare(fr, pg, how):
    """La vue d'avant le départ : celle qu'on vient de poser, déplacée de 100 px, ou zoomée d'un cran."""
    if how == 'moved':
        fr.evaluate("__RP.map.panBy([100, 0], { animate: false })")
    elif how == 'zoomed':
        fr.evaluate("__RP.map.setZoom(__RP.map.getZoom() + 1, { animate: false })")
    pg.wait_for_timeout(400)


def trip(pg, other, away=1200, back=1700):
    pg.evaluate("openModule('%s')" % other)
    pg.wait_for_timeout(away)
    pg.evaluate("openModule('rp')")
    pg.wait_for_timeout(back)


def same(fr, v0, v1, what=''):
    d = fr.evaluate(DRIFT, [v0, v1])
    assert v1['z'] == v0['z'] and d <= 1, (what, v0, v1, d)


# ---------- règle 1 : le retour garde la vue ----------
@needs_pw
@pytest.mark.parametrize('w,h', SIZES)
@pytest.mark.parametrize('other', OTHERS)
def test_coming_back_from_another_tool_keeps_the_centre_and_the_zoom(browser, w, h, other):
    pg, fr = open_rp(browser, w=w, h=h)
    setup(fr, [sym(0, 'sa-8')])
    aim(fr, pg)
    v0 = fr.evaluate(VIEW)
    trip(pg, other)
    v1 = fr.evaluate(VIEW)
    same(fr, v0, v1, (w, h, other))
    assert abs(v1['h'] - v0['h']) <= 1 and abs(v1['w'] - v0['w']) <= 1, (v0, v1)       # la carte revient à sa hauteur gardée
    assert pg.errs == []
    pg.context.close()


@needs_pw
@pytest.mark.parametrize('w,h', SIZES)
def test_coming_back_keeps_a_moved_or_zoomed_view_in_every_tap_mode(browser, w, h):
    pg, fr = open_rp(browser, w=w, h=h)
    setup(fr, [sym(0, 'sa-8')])
    aim(fr, pg)
    for mode in ('read', 'wp', 'ref', 'ruler'):
        for how in ('moved', 'zoomed'):
            fr.evaluate("(m) => setTapMode(m)", mode)
            prepare(fr, pg, how)
            v0 = fr.evaluate(VIEW)
            assert fr.evaluate("__RP.tapMode") == mode
            trip(pg, 'dg' if how == 'moved' else 'bg')
            v1 = fr.evaluate(VIEW)
            same(fr, v0, v1, (w, h, mode, how))
            assert abs(v1['h'] - v0['h']) <= 1
            assert fr.evaluate("__RP.tapMode") == 'read'                                  # le RP revient en Lire, comme à la base
    assert pg.errs == []
    pg.context.close()


@needs_pw
@pytest.mark.parametrize('w,h', [(412, 860), (1100, 800)])
@pytest.mark.parametrize('mode', ('read', 'wp'))
def test_coming_back_with_the_ground_profile_open_keeps_the_view_and_the_strip(browser, w, h, mode):
    pg, fr = open_rp(browser, w=w, h=h)
    setup(fr, [sym(0, 'sa-8')])
    tick(fr, pg)
    fr.wait_for_function("document.getElementById('rp-prof') !== null && __RP.prof.shown === true", timeout=20000)
    aim(fr, pg)
    for fold in (False, True):
        if fr.evaluate("!!DISP.profFold") != fold:
            fr.evaluate("document.querySelector('#rp-prof .prof-fb').click()")
            pg.wait_for_timeout(500)
        for how in ('aimed', 'moved', 'zoomed'):
            fr.evaluate("(m) => setTapMode(m)", mode)
            prepare(fr, pg, how)
            v0, r0 = fr.evaluate(VIEW), fr.evaluate(RECT)
            assert r0['prof'] is not None and r0['ph'] > 0 and r0['fold'] is fold
            trip(pg, 'dg')
            v1, r1 = fr.evaluate(VIEW), fr.evaluate(RECT)
            same(fr, v0, v1, (w, h, mode, fold, how))
            assert r1['fold'] is fold and r1['ph'] == r0['ph'], (r0, r1)                  # le bandeau garde son état replié et sa hauteur
            for k in ('map', 'prof', 'wrap'):
                assert abs(r1[k][0] - r0[k][0]) <= 1 and abs(r1[k][1] - r0[k][1]) <= 1, (k, r0, r1)
    assert pg.errs == []
    pg.context.close()


# ---------- règle 2 : tourné pendant l'absence ----------
@needs_pw
@pytest.mark.parametrize('w,h,w2,h2', [(345, 590, 590, 345), (915, 412, 412, 915)])
def test_rotated_while_away_the_same_centre_and_zoom_come_back_at_the_new_orientation_height(browser, w, h, w2, h2):
    pg, fr = open_rp(browser, w=w, h=h)
    setup(fr, [sym(0, 'sa-8')])
    aim(fr, pg)
    for how in ('aimed', 'moved', 'zoomed'):
        prepare(fr, pg, how)
        v0 = fr.evaluate(VIEW)
        pg.evaluate("openModule('dg')")
        pg.wait_for_timeout(1200)
        pg.set_viewport_size({'width': w2, 'height': h2})
        pg.wait_for_timeout(800)
        pg.evaluate("openModule('rp')")
        pg.wait_for_timeout(1700)
        v1 = fr.evaluate(VIEW)
        same(fr, v0, v1, (how, w2, h2))
        want = fr.evaluate("Math.round(spClamp(spGet() != null ? spGet() : SP_DEF_F * spPlace()))")
        assert abs(v1['h'] - want) <= 1 and abs(v1['w'] - w2) <= 1, (v1, want)          # la hauteur de la nouvelle orientation
        pg.set_viewport_size({'width': w, 'height': h})                                  # et on remet l'appareil dans l'autre sens pour le tour suivant
        pg.wait_for_timeout(800)
        v0 = None
        aim(fr, pg)
    assert pg.errs == []
    pg.context.close()


# ---------- règle 3 : ce qui ne change pas ----------
@needs_pw
@pytest.mark.parametrize('w,h', [(345, 590), (915, 412)])
def test_a_view_asked_while_the_tool_was_hidden_wins_the_new_theatre_is_framed(browser, w, h):
    pg, fr = open_rp(browser, w=w, h=h)
    setup(fr, [sym(0, 'sa-8')])
    aim(fr, pg)
    pg.evaluate("openModule('dg')")
    pg.wait_for_timeout(1200)
    pg.evaluate("localStorage.setItem('mp_theatre_v1', JSON.stringify({ theatre: 'Caucasus' }))")
    fr.wait_for_function("S.theatre === 'Caucasus'", timeout=8000)
    pg.wait_for_timeout(600)
    pg.evaluate("openModule('rp')")
    pg.wait_for_timeout(1700)
    r = fr.evaluate("() => { const c = __RP.map.getCenter(), t = theatreOf('Caucasus'); return { th: S.theatre, tap: tapMode, z: __RP.map.getZoom(), tz: t.z, dist: __RP.map.project(c, t.z).distanceTo(__RP.map.project(L.latLng(t.c[0], t.c[1]), t.z)) }; }")
    assert r['th'] == 'Caucasus' and r['tap'] == 'read' and r['z'] == r['tz'] and r['dist'] <= 1, r
    assert pg.errs == []
    pg.context.close()


@needs_pw
@pytest.mark.parametrize('w,h', [(345, 590), (412, 860), (915, 412), (1100, 800)])
def test_going_and_coming_back_writes_nothing_to_the_storage(browser, w, h):
    pg, fr = open_rp(browser, w=w, h=h)
    setup(fr, [sym(0, 'sa-8')])
    aim(fr, pg)
    prepare(fr, pg, 'moved')
    trip(pg, 'dg')                       # le premier passage charge l'autre outil, qui écrit ses propres clés : la mesure commence après
    trip(pg, 'hq')
    s0 = fr.evaluate(STORE)
    for other in ('dg', 'hq', 'bg'):
        trip(pg, other)
        assert fr.evaluate(STORE) == s0, other
    assert pg.errs == []
    pg.context.close()


@needs_pw
@pytest.mark.parametrize('other', OTHERS)
def test_above_1100_px_leaving_and_coming_back_calls_nothing_more_on_the_map(browser, other):
    pg, fr = open_rp(browser, w=1280, h=800)
    setup(fr, [sym(0, 'sa-8')])
    aim(fr, pg)
    v0 = fr.evaluate(VIEW)
    fr.evaluate(CALLS)
    trip(pg, other)
    calls = fr.evaluate("window.__calls")
    assert calls.count('setView') == 0 and calls.count('panBy') == 0 and calls.count('invalidateSize') <= 1, (other, calls)    # le seul appel est celui de la base, au retour
    same(fr, v0, fr.evaluate(VIEW), other)
    assert pg.errs == []
    pg.context.close()


@needs_pw
@pytest.mark.parametrize('w,h', [(345, 590), (412, 860)])
def test_dragging_the_handle_after_coming_back_keeps_the_top_left_corner_as_before(browser, w, h):
    pg, fr = open_rp(browser, w=w, h=h)
    setup(fr, [sym(0, 'sa-8')])
    aim(fr, pg)
    trip(pg, 'dg')
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
    assert fr.evaluate(DRIFT, [v0, v1]) > 20                                          # le centre, lui, a glissé : le comportement de la base
    assert pg.errs == []
    pg.context.close()
