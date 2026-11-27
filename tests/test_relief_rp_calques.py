"""Relief actif : en mode Lire, un calque importé laisse passer le toucher vers l'altitude du sol (lot relief-rp-calques).
Le banc est celui de test_relief_rp.py (relief.json et tuiles servis par page.route, aucun réseau). Le calque de ton cru (une zone, un point) est celui d'une
fenêtre d'import : openCfImport puis le bouton « Afficher »."""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_relief_rp import (CHANGELOG_LINE, DOC, PT, ROOT, SHELL, Bench, browser, menu, needs_pw, open_rp, theatre, tick_relief, tick_relief_pose, tile_ll)  # noqa: E402,F401

LINE = ('- With it on, the ground elevation is shown next to the mouse pointer (on a phone, tap the map in Read mode), in the altitude unit you chose; '
        'in Read mode, tapping or clicking an imported layer shows the elevation instead of the layer\'s details — untick Relief to read them.')
CENTER = tile_ll(1228, 819, .5, .5)                    # le centre de la vue (zoom 11) ; la zone l'entoure, le point est à droite
TAG = """(() => { const b = document.getElementById('rp-alt'), x = document.getElementById('rp-alt-x'); return { tag: !!b && !b.hidden, ring: !!x && !x.hidden, text: b ? b.textContent : '' }; })()"""
FICHE = "document.querySelectorAll('.leaflet-popup.cf-popup').length"


class HeldBench(Bench):
    """Comme le banc, mais le relief.json de Syria peut être retenu, puis servi plus tard."""
    def __init__(self):
        super().__init__()
        self.held = None

    def handler(self, route):
        if self.held is not None and route.request.url == PT + 'relief/Syria/relief.json':
            self.log.append(route.request.url)
            self.held.append(route)
            return
        return super().handler(route)


def layer(lat, lon):
    return {'id': 'essai', 'name': 'Essai', 'visible': True, 'source': {'kind': 'combatflite', 'file': 'essai.cf'}, 'items': [
        {'id': 'z1', 'type': 'zone', 'name': 'Zone', 'kind': 'curve', 'closed': True, 'filled': True, 'color': '#cc3300', 'fillOpacity': 0.6,
         'points': [[lat + .025, lon - .03], [lat + .025, lon + .03], [lat - .025, lon + .03], [lat - .025, lon - .03]]},
        {'id': 'p1', 'type': 'point', 'name': 'Point', 'kind': 'target', 'lat': lat, 'lon': lon + .07, 'color': '#0033cc'}]}


def import_layer(fr, pg):
    fr.evaluate("(l) => { const res = { theatre: 'Syria', layers: [cfLayer(l)], pre: [true] }; openCfImport('essai.cf', res); }", layer(*CENTER))
    pg.wait_for_timeout(300)
    fr.evaluate("document.getElementById('cf-import-go').click()")
    pg.wait_for_timeout(500)


def view(fr, pg, z=11):
    fr.evaluate("([a, b, z]) => __RP.map.setView([a, b], z, {animate:false})", [CENTER[0], CENTER[1], z])
    pg.wait_for_timeout(1000)


def spot(fr, dx, dy):
    """Le point de l'écran (page) à (dx, dy) du centre de la carte."""
    box = fr.frame_element().bounding_box()
    mb = fr.evaluate("(() => { const r = __RP.map.getContainer().getBoundingClientRect(); return { l: r.left, t: r.top, w: r.width, h: r.height }; })()")
    return box['x'] + mb['l'] + mb['w'] / 2 + dx, box['y'] + mb['t'] + mb['h'] / 2 + dy


def tap(pg, fr, dx, dy):
    pg.touchscreen.tap(*spot(fr, dx, dy))
    pg.wait_for_timeout(500)


def close_fiche(fr, pg):
    fr.evaluate("__RP.map.closePopup()")
    pg.wait_for_timeout(200)


def setup(browser, touch, w, h, bench=None):
    pg, fr = open_rp(browser, w=w, h=h, touch=touch)
    if bench is not None:
        pg.bench.log.clear()
    import_layer(fr, pg)
    view(fr, pg)
    assert fr.evaluate("CF_LAYERS.length") == 1 and fr.evaluate("__RP.tapMode") == 'read'
    return pg, fr


def point_dx(fr):
    return fr.evaluate("(() => { const p = __RP.map.latLngToContainerPoint([%f, %f]), c = __RP.map.latLngToContainerPoint([%f, %f]); return p.x - c.x; })()" % (CENTER[0], CENTER[1] + .07, CENTER[0], CENTER[1]))


def test_texts():
    log = (ROOT / 'CHANGELOG.md').read_text(encoding='utf-8')
    unreleased = log.split('\n## Unreleased\n', 1)[1].split('\n## ', 1)[0]
    rp = unreleased.split('\n### Route Planner\n', 1)[1].split('\n### ', 1)[0]
    lines = rp.strip().splitlines()
    assert lines.index(CHANGELOG_LINE) + 1 == lines.index(LINE) and rp.count(LINE) == 1 and unreleased.count(LINE) == 1
    fm = (ROOT / 'build_field_manual.py').read_text(encoding='utf-8')
    i = fm.index("('h', \"Le relief\", \"Relief\")")
    j = fm.index("('h', \"La fiche d’un aérodrome\"", i)
    assert 'décochez Relief' in fm[i:j] and 'untick Relief' in fm[i:j]


@needs_pw
def test_touch_with_relief_shows_the_elevation_and_no_sheet_and_without_relief_the_sheet(browser):
    pg, fr = setup(browser, True, 412, 900)
    n = fr.evaluate("__RP.S.points.length")
    # sans Relief : la fiche, comme avant, aucun cartouche
    tap(pg, fr, 0, 0)
    assert fr.evaluate(FICHE) == 1 and fr.evaluate(TAG)['tag'] is False
    close_fiche(fr, pg)
    tick_relief_pose(fr, pg)
    assert fr.evaluate("reliefLive()") is True
    dx = point_dx(fr)
    for x, y in ((0, 0), (dx, 0)):                                                                # la zone, puis le point
        tap(pg, fr, x, y)
        t = fr.evaluate(TAG)
        assert fr.evaluate(FICHE) == 0 and t['tag'] is True and t['ring'] is True and t['text'].startswith('Alt. sol ')
        assert fr.evaluate("__RP.S.points.length") == n and fr.evaluate("__RP.tapMode") == 'read'
    ring = fr.evaluate("(() => { const r = document.getElementById('rp-alt-x').getBoundingClientRect(), c = document.getElementById('rp-alt').parentElement.getBoundingClientRect(); return [r.left + r.width / 2 - c.left, r.top + r.height / 2 - c.top]; })()")
    want = fr.evaluate("(() => { const p = __RP.map.latLngToContainerPoint([%f, %f]); return [p.x, p.y]; })()" % (CENTER[0], CENTER[1] + .07))
    assert abs(ring[0] - want[0]) < 30 and abs(ring[1] - want[1]) < 30                              # l'anneau est au toucher (à quelques pixels : le doigt a pris le point)
    # Relief décoché : le même toucher rouvre la fiche, sans cartouche
    tick_relief_pose(fr, pg)
    assert fr.evaluate("reliefLive()") is False
    tap(pg, fr, 0, 0)
    assert fr.evaluate(FICHE) == 1 and fr.evaluate(TAG)['tag'] is False
    close_fiche(fr, pg)
    tap(pg, fr, dx, 0)
    assert fr.evaluate(FICHE) == 1 and fr.evaluate(TAG)['tag'] is False
    assert pg.errs == []
    pg.context.close()


@needs_pw
def test_mouse_click_with_relief_opens_nothing_and_the_hover_tag_stays(browser):
    pg, fr = setup(browser, False, 1280, 800)
    tick_relief_pose(fr, pg)
    x, y = spot(fr, 0, 0)
    pg.mouse.move(x - 5, y - 5)
    pg.mouse.move(x, y)
    pg.wait_for_timeout(600)
    assert fr.evaluate(TAG)['tag'] is True
    text = fr.evaluate(TAG)['text']
    pg.mouse.click(x, y)
    pg.wait_for_timeout(500)
    assert fr.evaluate(FICHE) == 0 and fr.evaluate(TAG) == {'tag': True, 'ring': False, 'text': text}
    # Relief décoché : le clic ouvre la fiche
    tick_relief_pose(fr, pg)
    pg.mouse.click(x, y)
    pg.wait_for_timeout(500)
    assert fr.evaluate(FICHE) == 1
    assert pg.errs == []
    pg.context.close()


@needs_pw
def test_an_open_sheet_closes_when_relief_comes_on_without_reload(browser):
    pg, fr = setup(browser, True, 412, 900)
    fr.evaluate("window.__same = 1")
    tap(pg, fr, 0, 0)
    assert fr.evaluate(FICHE) == 1
    tick_relief_pose(fr, pg)
    assert fr.evaluate(FICHE) == 0 and fr.evaluate("window.__same") == 1                          # fermée, sans recharger
    assert fr.evaluate("document.querySelectorAll('.cf-hit').length") == 0                        # plus de trait de touche
    assert fr.evaluate("document.querySelectorAll('.leaflet-layers-pane .cf-obj.leaflet-interactive').length") == 0
    tap(pg, fr, 0, 0)
    assert fr.evaluate(FICHE) == 0 and fr.evaluate(TAG)['ring'] is True
    tick_relief_pose(fr, pg)                                                                           # décochée : le calque se touche de nouveau tout de suite
    assert fr.evaluate("document.querySelectorAll('.cf-hit, .leaflet-layers-pane .cf-obj.leaflet-interactive').length") > 0
    assert pg.errs == []
    pg.context.close()


@needs_pw
@pytest.mark.parametrize('tid', ['Nevada', 'GermanyCW'])
def test_no_relief_on_the_theatre_the_sheet_opens_as_before(browser, tid):
    pg, fr = setup(browser, True, 412, 900)
    tick_relief_pose(fr, pg)                                                                           # la case reste cochée sur le théâtre suivant
    theatre(fr, pg, tid)
    pg.wait_for_timeout(600)
    assert fr.evaluate("DISP.relief") is True and fr.evaluate("reliefLive()") is False
    view(fr, pg)
    tap(pg, fr, 0, 0)
    assert fr.evaluate(FICHE) == 1 and fr.evaluate(TAG)['tag'] is False
    close_fiche(fr, pg)
    tap(pg, fr, point_dx(fr), 0)
    assert fr.evaluate(FICHE) == 1
    assert pg.errs == []
    pg.context.close()


@needs_pw
def test_relief_json_late_the_sheet_opens_before_and_not_after(browser):
    ctx = browser.new_context(viewport={'width': 412, 'height': 900}, has_touch=True, is_mobile=True)
    ctx.add_init_script("try{localStorage.setItem('lang_v1','fr')}catch(e){}")
    pg = ctx.new_page()
    pg.errs = []
    pg.on('pageerror', lambda e: pg.errs.append(str(e)))
    pg.bench = HeldBench()
    pg.bench.held = []
    pg.route('**/*', pg.bench.handler)
    pg.goto('about:blank')
    pg.goto(SHELL, wait_until='commit')
    pg.wait_for_function("typeof NAV !== 'undefined' && typeof openModule === 'function'", timeout=30000)
    pg.wait_for_timeout(600)
    pg.evaluate("MP_WORK_EXAMPLE('fl')")
    pg.wait_for_timeout(1200)
    pg.evaluate("openModule('rp')")
    pg.wait_for_timeout(2300)
    fr = next(f for f in pg.frames if f != pg.main_frame and f.evaluate("typeof window.__RP !== 'undefined'"))
    import_layer(fr, pg)
    view(fr, pg)
    tick_relief(fr, pg)                                                                           # relief.json est tenu en retard : la couche ne peut pas être posée
    assert len(pg.bench.held) == 1 and fr.evaluate("reliefLive()") is False
    pg.wait_for_timeout(2000)                                                                     # relief.json en retard de 2 s
    tap(pg, fr, 0, 0)
    assert fr.evaluate(FICHE) == 1 and fr.evaluate(TAG)['tag'] is False                           # avant son arrivée : la fiche
    r = pg.bench.held.pop()
    r.fulfill(status=200, headers={'Access-Control-Allow-Origin': '*', 'Content-Type': 'application/json'}, body=json.dumps(DOC))
    pg.wait_for_timeout(1500)
    assert fr.evaluate("reliefLive()") is True and fr.evaluate(FICHE) == 0                        # à son arrivée, la fiche ouverte se ferme
    close_fiche(fr, pg)
    tap(pg, fr, 0, 0)
    assert fr.evaluate(FICHE) == 0 and fr.evaluate(TAG)['ring'] is True                           # après : l'altitude
    assert pg.errs == []
    ctx.close()


@needs_pw
def test_point_mode_with_relief_a_touch_on_the_layer_lays_a_point(browser):
    pg, fr = setup(browser, True, 412, 900)
    tick_relief_pose(fr, pg)
    fr.evaluate("setTapMode('wp')")
    pg.wait_for_timeout(300)
    n = fr.evaluate("__RP.S.points.length")
    tap(pg, fr, 0, 0)
    assert fr.evaluate("__RP.S.points.length") == n + 1 and fr.evaluate(TAG)['tag'] is False and fr.evaluate(FICHE) == 0
    tap(pg, fr, point_dx(fr), 0)                                                                  # sur le point du calque : une cible agit comme un aérodrome, comme avant
    assert fr.evaluate("__RP.S.points.length") == n + 2 and fr.evaluate(FICHE) == 0
    assert pg.errs == []
    pg.context.close()


@needs_pw
def test_an_airfield_keeps_its_sheet_with_relief(browser):
    pg, fr = setup(browser, True, 412, 900)
    tick_relief_pose(fr, pg)
    fr.evaluate("([a, b]) => __RP.map.setView([a, b], 11, {animate:false})", [33.852, 35.987])    # Rayak
    pg.wait_for_timeout(1000)
    tap(pg, fr, 0, 0)
    assert fr.evaluate("rtVisible('fiche')") is True and fr.evaluate(TAG)['tag'] is False
    assert pg.errs == []
    pg.context.close()
