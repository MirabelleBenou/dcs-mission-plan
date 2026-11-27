"""La case « Relief » du Route Planner et l'altitude du sol au pointeur, jouées sur le shell construit (dist/dcs_mission_plan.html, chromium).
Aucun réseau : les requêtes hors file:/data:/blob: sont interceptées ; sous l'adresse publique des tuiles, le banc sert un relief.json du contrat
dcs-relief-tiles-v1 et des tuiles écrites ici (un ombrage, une altitude dont la moitié gauche vaut 907,0 m et la moitié droite est hors carte).
Les contrôles passent par le DOM, dans le shell."""
import json
import math
import re
import struct
import sys
import zlib
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
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tests'))
from public_host_block import build_block  # noqa: E402
from banc_attente import (attendre, attendre_images, attendre_relief_pose, attendre_relief_repos, attendre_rp, attendre_shell, attendre_theatre, exemple, viser)  # noqa: E402

PT = re.search(r"PUBLIC_TILES = '([^']+)'", build_block()).group(1)        # l'adresse publique des tuiles, lue du bloc que le Route Planner insère
BOUNDS = [[33.15, 35.15], [34.75, 36.95]]
DOC = {'format': 'dcs-relief-tiles-v1', 'theatre': 'Syria', 'edition': 'test', 'minZoom': 8, 'maxNativeZoom': 11, 'tileSize': 256, 'bounds': BOUNDS,
       'layers': {'hillshade': {'path': 'hillshade/{z}/{x}/{y}.webp'},
                  'elevation': {'path': 'elevation/{z}/{x}/{y}.png', 'encoding': 'terrain-rgb', 'base_m': -10000, 'step_m': 0.1}},
       'attribution': 'test', 'source': 'test', 'tiles_per_zoom': {}}
CHANGELOG_LINE = '- New “Relief” option in the Display menu: the terrain as DCS sees it, shaded in relief over any base map, on Caucasus, Cold War Germany and Syria.'
README_TAIL = 'terrain relief © DCS World, Eagle Dynamics SA, read in the game (non-commercial use)'
ATTR_FR = 'Relief : DCS World, Eagle Dynamics SA (usage non commercial)'
ATTR_EN = 'Relief: DCS World, Eagle Dynamics SA (non-commercial use)'


def png(w, h, pixel):
    rows = b''.join(b'\x00' + b''.join(bytes(pixel(x, y)) for x in range(w)) for y in range(h))

    def chunk(t, d):
        return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 6, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(rows)) + chunk(b'IEND', b'')


# Terrain-RGB : R = 1, G = 170 (171 dans la moitié basse), B = le numéro de la colonne du pixel ; h = -10000 + (R × 65536 + G × 256 + B) × 0,1 = 905,6 + 0,1 × colonne (+ 25,6 dans la moitié basse)
ELEV = png(256, 256, lambda x, y: (1, 170 + (y >= 128), x, 255))
HOLE = png(256, 256, lambda x, y: (0, 0, 0, 0))             # la tuile 1231 / 819 : hors carte (alpha 0)


def elev_at(px, py):
    return 905.6 + 0.1 * px + (25.6 if py >= 128 else 0)


SHADE = png(256, 256, lambda x, y: (60, 40, 20, 90))


def tile_ll(tx, ty, fx, fy, z=11):
    """Le point de la tuile (tx, ty) à la fraction (fx, fy) : (lat, lon)."""
    n = 2 ** z
    lon = (tx + fx) / n * 360 - 180
    lat = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * (ty + fy) / n))))
    return lat, lon


class Bench:
    def __init__(self):
        self.log = []
        self.doc = DOC                                       # le relief.json de Syria, que les tests peuvent changer

    def handler(self, route):
        url = route.request.url
        if url.startswith(('file:', 'data:', 'blob:')):
            return route.continue_()
        self.log.append(url)
        cors = {'Access-Control-Allow-Origin': '*'}
        if url.startswith(PT + 'relief/'):
            rest = url[len(PT + 'relief/'):]
            if rest == 'Syria/relief.json':
                return route.fulfill(status=200, headers={**cors, 'Content-Type': 'application/json'}, body=json.dumps(self.doc))
            if rest == 'Caucasus/relief.json':
                return route.fulfill(status=200, headers={**cors, 'Content-Type': 'application/json'}, body=json.dumps({**DOC, 'format': 'other'}))
            if rest.startswith('Syria/hillshade/'):
                return route.fulfill(status=200, headers={**cors, 'Content-Type': 'image/png'}, body=SHADE)
            if rest.startswith('Syria/elevation/'):
                body = HOLE if rest == 'Syria/elevation/11/1231/819.png' else ELEV
                return route.fulfill(status=200, headers={**cors, 'Content-Type': 'image/png'}, body=body)
            return route.fulfill(status=404, headers=cors, body='')
        return route.abort()

    def relief(self, part=''):
        return [u[len(PT):] for u in self.log if u.startswith(PT + 'relief/') and part in u]


@pytest.fixture(scope='module')
def browser():
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        br = p.chromium.launch(executable_path=str(CHROMIUM), args=['--no-sandbox'])
        yield br
        br.close()


def open_rp(br, w=1280, h=800, touch=False, lang='fr'):
    ctx = br.new_context(viewport={'width': w, 'height': h}, has_touch=touch, is_mobile=touch)
    ctx.add_init_script("try{localStorage.setItem('lang_v1','%s')}catch(e){}" % lang)
    pg = ctx.new_page()
    pg.errs = []
    pg.on('pageerror', lambda e: pg.errs.append(str(e)))
    pg.bench = Bench()
    pg.route('**/*', pg.bench.handler)
    pg.goto('about:blank')
    pg.goto(SHELL, wait_until='commit')
    attendre_shell(pg)
    exemple(pg, 'fl')                                     # l'exemple, théâtre Syria
    pg.evaluate("openModule('rp')")
    fr = attendre_rp(pg)
    fr.evaluate("window.__toasts = []; { const o = window.showToast; window.showToast = function (m, op) { window.__toasts.push(String(m)); return o.apply(this, arguments); }; } 0")
    return pg, fr


def menu(fr, pg, on):
    fr.evaluate("if (DSP.open !== %s) document.getElementById('btn-display').click()" % ('true' if on else 'false'))
    attendre(fr, 'DSP.open === arg', 'le menu Affichage %s (DSP.open)' % ('ouvert' if on else 'fermé'), lu='DSP.open', arg=on)
    attendre_images(fr, 2)


def tick_relief(fr, pg):
    menu(fr, pg, True)
    want = not fr.evaluate("DISP.relief")
    fr.evaluate("document.querySelector('#dsp-panel [data-k=relief]').click()")
    attendre(fr, 'DISP.relief === arg', 'la case Relief %s' % ('cochée' if want else 'décochée'), lu='DISP.relief', arg=want)
    attendre_relief_pose(fr)
    menu(fr, pg, False)


def theatre(fr, pg, tid):
    fr.evaluate("(id) => { const s = document.getElementById('theatre'); s.value = id; s.dispatchEvent(new Event('change', { bubbles: true })); }", tid)
    attendre_theatre(fr, tid)
    attendre_relief_pose(fr)


def test_texts_are_where_the_lot_says():
    log = (ROOT / 'CHANGELOG.md').read_text(encoding='utf-8')
    unreleased = log.split('\n## Unreleased\n', 1)[1].split('\n## ', 1)[0]
    rp = unreleased.split('\n### Route Planner\n', 1)[1].split('\n### ', 1)[0]
    assert rp.count(CHANGELOG_LINE) == 1 and unreleased.count(CHANGELOG_LINE) == 1
    assert rp.strip().splitlines()[rp.strip().splitlines().index(CHANGELOG_LINE) - 1] == '**Relief**'
    readme = (ROOT / 'README.md').read_text(encoding='utf-8')
    assert [ln for ln in readme.splitlines() if 'satellite imagery' in ln and ln.endswith(README_TAIL)]
    fm = (ROOT / 'build_field_manual.py').read_text(encoding='utf-8')
    i = fm.index("('h', \"Le relief\", \"Relief\")")
    j = fm.index("('h', \"La fiche d’un aérodrome\"", i)
    assert 'Eagle Dynamics SA' in fm[i:j] and fm[i:j].count('**Relief**') == 2


@needs_pw
def test_row_first_off_by_default_kept_in_the_screen_settings_only(browser):
    pg, fr = open_rp(browser)
    assert fr.evaluate("DISP.relief") is False and fr.evaluate("document.getElementById('dsp-dot').hidden") is True
    menu(fr, pg, True)
    row = fr.evaluate("""(() => { const r = document.querySelector('#dsp-panel [data-k=relief]'); return { role: r.getAttribute('role'), checked: r.getAttribute('aria-checked'),
        cls: r.className, prev: r.previousElementSibling.textContent.trim(), next: r.nextElementSibling.textContent.trim(), title: r.title, txt: r.textContent.trim() }; })()""")
    assert row == {'role': 'menuitemcheckbox', 'checked': 'false', 'cls': 'tbm-opt dsp-opt', 'prev': 'Afficher sur la carte', 'next': 'Menaces', 'title': 'Relief du terrain, relevé dans DCS', 'txt': 'Relief'}
    menu(fr, pg, False)
    before = fr.evaluate("localStorage.getItem('route_state_v1')")
    n0 = len(pg.bench.relief())
    tick_relief(fr, pg)
    assert fr.evaluate("localStorage.getItem('route_state_v1')") == before                       # le fichier de travail ne change pas, à l'octet
    assert json.loads(fr.evaluate("localStorage.getItem('rp_display_v1')"))['relief'] is True
    assert fr.evaluate("document.getElementById('dsp-dot').hidden") is False                      # le point ambre
    assert pg.bench.relief()[n0:] == ['relief/Syria/relief.json']
    pane = fr.evaluate("(() => { const p = __RP.map.getPane('relief'); return { z: p.style.zIndex, pe: p.style.pointerEvents, layer: !!__RP.reliefLayer }; })()")
    assert pane == {'z': '250', 'pe': 'none', 'layer': True}
    viser(fr, 33.85, 35.95, 10)
    attendre(fr, "document.querySelectorAll('.leaflet-relief-pane img').length > 0", "des tuiles d'ombrage posées dans le volet du relief", lu="document.querySelectorAll('.leaflet-relief-pane img').length")
    assert pg.bench.relief('hillshade') and fr.evaluate("document.querySelectorAll('.leaflet-relief-pane img').length") > 0
    # un autre chargement du module, le même stockage : la case reste cochée
    saved = fr.evaluate("Object.fromEntries(Object.entries(localStorage))")
    pg.context.close()
    pg2, fr2 = None, None
    ctx = browser.new_context(viewport={'width': 1280, 'height': 800})
    ctx.add_init_script("(() => { if (!sessionStorage.getItem('seeded')) { const d = %s; for (const k in d) localStorage.setItem(k, d[k]); sessionStorage.setItem('seeded', '1'); } })()" % json.dumps(saved))
    pg2 = ctx.new_page()
    bench = Bench()
    pg2.route('**/*', bench.handler)
    pg2.goto(SHELL + '#rp', wait_until='commit')
    attendre_shell(pg2)
    fr2 = attendre_rp(pg2)                                                                         # l'adresse #rp ouvre le Route Planner
    attendre(fr2, '!!__RP.reliefLayer', 'la couche de relief reposée au chargement', lu='!!__RP.reliefLayer')
    assert fr2.evaluate("DISP.relief") is True and fr2.evaluate("!!__RP.reliefLayer") is True
    ctx.close()


@needs_pw
def test_row_is_greyed_out_where_there_is_no_relief_and_the_keyboard_reaches_it_elsewhere(browser):
    pg, fr = open_rp(browser)
    menu(fr, pg, True)
    fr.evaluate("document.getElementById('dsp-panel').focus()")
    for _ in range(40):                                                                           # ↓ jusqu'à la ligne Relief, puis Entrée la coche
        if fr.evaluate("document.activeElement && document.activeElement.getAttribute('data-k') === 'relief'"):
            break
        pg.keyboard.press('ArrowDown')
    assert fr.evaluate("document.activeElement.getAttribute('data-k')") == 'relief'
    pg.keyboard.press('Enter')
    attendre(fr, "DISP.relief === true && document.querySelector('#dsp-panel [data-k=relief]').getAttribute('aria-checked') === 'true'", 'la case Relief cochée au clavier', lu="[DISP.relief, document.querySelector('#dsp-panel [data-k=relief]').getAttribute('aria-checked')]")
    assert fr.evaluate("DISP.relief") is True and fr.evaluate("document.querySelector('#dsp-panel [data-k=relief]').getAttribute('aria-checked')") == 'true'
    menu(fr, pg, False)
    n0 = len(pg.bench.relief())
    theatre(fr, pg, 'Nevada')
    menu(fr, pg, True)
    row = fr.evaluate("(() => { const r = document.querySelector('#dsp-panel [data-k=relief]'); return [r.getAttribute('aria-disabled'), r.getAttribute('aria-checked'), r.title]; })()")
    assert row == ['true', 'false', 'Relief — absent de ce théâtre']
    fr.evaluate("document.querySelector('#dsp-panel [data-k=relief]').click()")
    attendre_images(fr, 3)                                                                         # le clic sur la ligne grisée ne change rien : le rendu passe avant qu'on le constate
    assert fr.evaluate("DISP.relief") is True and fr.evaluate("!!__RP.reliefLayer") is False and pg.bench.relief()[n0:] == []
    assert pg.errs == []
    pg.context.close()


@needs_pw
def test_failures_are_announced_once_per_theatre(browser):
    pg, fr = open_rp(browser)
    tick_relief(fr, pg)
    theatre(fr, pg, 'GermanyCW')
    assert fr.evaluate("__toasts") == ['⚠ Relief indisponible : le serveur des tuiles ne répond pas.']
    theatre(fr, pg, 'Caucasus')
    assert fr.evaluate("__toasts")[1:] == ['⚠ Relief indisponible : la description reçue du serveur est illisible.']
    n0 = len(pg.bench.relief())
    for th in ('GermanyCW', 'Caucasus', 'GermanyCW', 'Syria'):
        theatre(fr, pg, th)
    assert len(fr.evaluate("__toasts")) == 2 and [u for u in pg.bench.relief()[n0:] if u.endswith('relief.json')] == []
    assert fr.evaluate("DISP.relief") is True and fr.evaluate("!!__RP.reliefLayer") is True       # la case est restée cochée ; Syria a son relief
    fr.evaluate("setLang('en')")
    theatre(fr, pg, 'GermanyCW')
    assert len(fr.evaluate("__toasts")) == 2
    assert pg.errs == []
    pg.context.close()


@needs_pw
def test_elevation_is_read_from_the_terrain_rgb_tile_and_kept_in_a_small_cache(browser):
    pg, fr = open_rp(browser)
    tick_relief(fr, pg)
    ask = lambda la, lo: fr.evaluate("([a, b]) => __RP.reliefAltAt(a, b)", [la, lo])
    for fx, fy in ((.25, .25), (.75, .25), (.25, .75), (.9, .9)):                                  # le pixel floor(fraction × 256), colonne et ligne
        la, lo = tile_ll(1228, 819, fx, fy)
        assert abs(ask(la, lo) - elev_at(math.floor(fx * 256), math.floor(fy * 256))) < 1e-6
    assert ask(*tile_ll(1231, 819, .5, .5)) is None                                                # alpha 0 : hors carte
    assert ask(*tile_ll(1231, 820, .5, .5)) is not None
    assert ask(33.10, 35.60) is None and ask(34.80, 35.90) is None and ask(33.8, 37.0) is None and ask(33.8, 35.1) is None      # hors des bornes
    # une seule requête par tuile, même pour des appels simultanés
    asked = lambda t: len([u for u in pg.bench.relief('elevation') if u.endswith('/elevation/11/%d/%d.png' % t)])       # A6 : par fetch, le cache du navigateur ne cache plus ces requêtes
    la, lo = tile_ll(1229, 819, .25, .25)
    both = fr.evaluate("([a, b]) => Promise.all([__RP.reliefAltAt(a, b), __RP.reliefAltAt(a, b), __RP.reliefAltAt(a, b)])", [la, lo])
    assert len(both) == 3 and all(abs(v - elev_at(64, 64)) < 1e-6 for v in both)
    assert asked((1229, 819)) == 1
    # 64 tuiles au plus : la plus ancienne sort la première
    inside = lambda t: BOUNDS[0][0] <= tile_ll(*t, .25, .5)[0] <= BOUNDS[1][0] and BOUNDS[0][1] <= tile_ll(*t, .25, .5)[1] <= BOUNDS[1][1]
    tiles = [t for t in ((x, y) for x in range(1223, 1236) for y in range(810, 826)) if inside(t)][:70]
    assert len(tiles) == 70
    first = tiles[0]
    fr.evaluate("""async (ts) => { for (const [la, lo] of ts) await __RP.reliefAltAt(la, lo); }""", [list(tile_ll(x, y, .25, .5)) for x, y in tiles])
    count = asked
    assert count(first) == 1 and count(tiles[-1]) == 1
    fr.evaluate("([a, b]) => __RP.reliefAltAt(a, b)", list(tile_ll(*tiles[-1], .25, .5)))
    fr.evaluate("([a, b]) => __RP.reliefAltAt(a, b)", list(tile_ll(*first, .25, .5)))
    attendre_images(fr, 2)                                                                         # les deux appels sont rendus (evaluate attend les promesses) : les requêtes sont comptées
    assert count(tiles[-1]) == 1 and count(first) == 2
    # sans relief posé : null
    tick_relief(fr, pg)
    assert ask(*tile_ll(1228, 819, .25, .5)) is None
    assert pg.errs == []
    pg.context.close()


@needs_pw
@pytest.mark.parametrize('lang,unit,label,suffix', [('fr', 'm', 'Alt. sol', 'm'), ('en', 'ft', 'Ground', 'ft')])
def test_tag_follows_the_mouse_and_stays_inside_the_map(browser, lang, unit, label, suffix):
    pg, fr = open_rp(browser, lang=lang)
    tick_relief(fr, pg)
    menu(fr, pg, True)
    fr.evaluate("(u) => document.querySelector('#dsp-panel [data-un=\"' + u + '\"]').click()", unit)
    menu(fr, pg, False)
    la, lo = tile_ll(1228, 819, .25, .5)
    viser(fr, la, lo, 11)
    box = fr.frame_element().bounding_box()
    mb = fr.evaluate("(() => { const r = __RP.map.getContainer().getBoundingClientRect(); return { l: r.left, t: r.top, w: r.width, h: r.height }; })()")
    fr.evaluate("""() => { window.__last = null; __RP.map.getContainer().addEventListener('pointermove', ev => { if (ev.pointerType === 'mouse') {
        const ll = __RP.map.mouseEventToLatLng(ev); window.__last = [ll.lat, ll.lng]; } }, true); }""")

    def expect():
        h = fr.evaluate("([a, b]) => __RP.reliefAltAt(a, b)", fr.evaluate("window.__last"))
        return f'{label} ' + (f'{round(h)} m' if unit == 'm' else f'{round(h / 0.3048)} ft')

    def read():
        return fr.evaluate("""(() => { const b = document.getElementById('rp-alt'), c = __RP.map.getContainer().getBoundingClientRect(), r = b.getBoundingClientRect();
            return { hidden: b.hidden, text: b.textContent, l: r.left - c.left, t: r.top - c.top, w: r.width, h: r.height }; })()""")

    def move(x, y):
        pg.mouse.move(box['x'] + mb['l'] + x, box['y'] + mb['t'] + y)
        attendre_relief_repos(fr)
    cx, cy = mb['w'] / 2, mb['h'] / 2                                                              # le centre de la carte : le point (lat, lon), pixel 64
    move(cx - 100, cy)
    s = read()
    assert not s['hidden'] and s['text'] == expect() and abs(s['l'] - (cx - 100 + 14)) <= 1 and abs(s['t'] - (cy + 14)) <= 1
    move(mb['w'] - 20, cy)                                                                         # près du bord droit : à gauche du point
    s = read()
    assert not s['hidden'] and s['text'] == expect() and abs(s['l'] + s['w'] - (mb['w'] - 20 - 14)) <= 1 and s['l'] + s['w'] <= mb['w']
    move(cx - 100, mb['h'] - 20)                                                                   # près du bord bas : au-dessus du point
    s = read()
    assert not s['hidden'] and abs(s['t'] + s['h'] - (mb['h'] - 20 - 14)) <= 1
    pg.mouse.move(2, 2)                                                                            # hors de la carte
    attendre(fr, "(document.getElementById('rp-alt') || { hidden: true }).hidden === true", 'le cartouche masqué hors de la carte', lu="(document.getElementById('rp-alt') || { hidden: true }).hidden")
    assert read()['hidden'] is True
    assert pg.errs == []
    pg.context.close()


@needs_pw
def test_touch_in_read_mode_shows_the_tag_and_the_ring_and_nothing_else(browser):
    pg, fr = open_rp(browser, w=412, h=900, touch=True)
    tick_relief(fr, pg)
    la, lo = tile_ll(1228, 819, .25, .5)
    viser(fr, la, lo, 11)
    box = fr.frame_element().bounding_box()
    mb = fr.evaluate("(() => { const r = __RP.map.getContainer().getBoundingClientRect(); return { l: r.left, t: r.top, w: r.width, h: r.height }; })()")
    at = lambda dx, dy: (box['x'] + mb['l'] + mb['w'] / 2 + dx, box['y'] + mb['t'] + mb['h'] / 2 + dy)
    read = lambda: fr.evaluate("""(() => { const b = document.getElementById('rp-alt'), x = document.getElementById('rp-alt-x');
        return b ? { hidden: b.hidden, text: b.textContent, ring: !x.hidden, n: __RP.S.points.length, mode: __RP.tapMode } : null; })()""")
    n = fr.evaluate("__RP.S.points.length")
    fr.evaluate("""() => { window.__tap = null; __RP.map.on('click', e => { window.__tap = [e.latlng.lat, e.latlng.lng]; }); }""")
    pg.touchscreen.tap(*at(-60, 40))
    attendre(fr, "!(document.getElementById('rp-alt') || { hidden: true }).hidden", 'le cartouche posé au toucher', lu="(document.getElementById('rp-alt') || { hidden: true }).hidden")
    attendre_relief_repos(fr)
    h = fr.evaluate("([a, b]) => __RP.reliefAltAt(a, b)", fr.evaluate("window.__tap"))
    assert read() == {'hidden': False, 'text': f'Alt. sol {round(h)} m', 'ring': True, 'n': n, 'mode': 'read'}      # en mode Lire, rien d'autre qu'avant
    fr.evaluate("__RP.map.panBy([30, 20], {animate:false})")
    attendre(fr, "(document.getElementById('rp-alt') || { hidden: true }).hidden === true && (document.getElementById('rp-alt-x') || { hidden: true }).hidden === true", 'le cartouche et l\'anneau masqués par le déplacement', lu="[(document.getElementById('rp-alt') || { hidden: true }).hidden, (document.getElementById('rp-alt-x') || { hidden: true }).hidden]")
    assert read()['hidden'] is True and read()['ring'] is False                                    # un déplacement de la carte les masque
    pg.touchscreen.tap(*at(-60, 40))
    attendre(fr, "!(document.getElementById('rp-alt') || { hidden: true }).hidden", 'le cartouche posé au toucher', lu="(document.getElementById('rp-alt') || { hidden: true }).hidden")
    attendre_relief_repos(fr)
    assert read()['hidden'] is False
    fr.evaluate("document.querySelector('#tapmode [data-tap=wp]').click()")
    attendre(fr, "__RP.tapMode === 'wp' && (document.getElementById('rp-alt') || { hidden: true }).hidden === true", 'le mode Point posé, le cartouche masqué', lu="[__RP.tapMode, (document.getElementById('rp-alt') || { hidden: true }).hidden]")
    assert read()['hidden'] is True                                                                # le changement de mode aussi
    pg.touchscreen.tap(*at(80, 80))
    attendre(fr, '__RP.S.points.length === arg', 'un point posé en mode Point', lu='__RP.S.points.length', arg=n + 1)
    attendre_relief_repos(fr)
    s = read()
    assert s['n'] == n + 1 and s['hidden'] is True and s['mode'] == 'wp'                           # en mode Point : un point, pas de cartouche
    assert pg.errs == []
    pg.context.close()


@needs_pw
def test_relief_never_changes_the_fallback_and_credits_its_source_only_while_shown(browser):
    pg, fr = open_rp(browser)
    viser(fr, 33.85, 35.95, 10)
    attr = lambda: fr.evaluate("document.querySelector('.leaflet-control-attribution').textContent")
    assert 'Relief' not in attr()
    tick_relief(fr, pg)
    assert ATTR_FR in attr()
    fr.evaluate("setLang('en')")
    assert ATTR_EN in attr() and ATTR_FR not in attr()
    menu(fr, pg, True)
    fr.evaluate("document.querySelector('#dsp-panel [data-base=topo]').click()")
    menu(fr, pg, False)
    attendre(fr, 'timerElapsed === true && __RP.inFallback === true', 'le repli en grille seule (le délai FALLBACK_MS de l\'application écoulé, fonds en ligne bloqués)', lu='[timerElapsed, __RP.inFallback]', delai=20000)
    shaded = fr.evaluate("({ fb: __RP.inFallback, tiles: document.querySelectorAll('.leaflet-relief-pane img').length })")
    assert shaded['fb'] is True and shaded['tiles'] > 0                                            # l'ombrage reste visible en repli
    tick_relief(fr, pg)
    assert 'Relief' not in attr()
    fr.evaluate("__RP.setBase()")
    attendre(fr, 'timerElapsed === true && __RP.inFallback === true', 'le repli en grille seule (le délai FALLBACK_MS de l\'application écoulé, fonds en ligne bloqués)', lu='[timerElapsed, __RP.inFallback]', delai=20000)
    assert fr.evaluate("__RP.inFallback") is True                                                  # le même repli sans Relief
    assert pg.errs == []
    pg.context.close()


def tap_at(pg, fr, dx, dy):
    box = fr.frame_element().bounding_box()
    mb = fr.evaluate("(() => { const r = __RP.map.getContainer().getBoundingClientRect(); return { l: r.left, t: r.top, w: r.width, h: r.height }; })()")
    pg.touchscreen.tap(box['x'] + mb['l'] + mb['w'] / 2 + dx, box['y'] + mb['t'] + mb['h'] / 2 + dy)
    attendre_relief_repos(fr)


TAG = """(() => { const b = document.getElementById('rp-alt'), x = document.getElementById('rp-alt-x'); return { tag: !!b && !b.hidden, ring: !!x && !x.hidden, text: b ? b.textContent : '' }; })()"""


@needs_pw
def test_nothing_is_read_below_min_zoom_and_an_absent_tile_waits_for_the_pointer(browser):
    pg, fr = open_rp(browser)
    tick_relief(fr, pg)
    box_ = lambda: (fr.frame_element().bounding_box(), fr.evaluate("(() => { const r = __RP.map.getContainer().getBoundingClientRect(); return { l: r.left, t: r.top, w: r.width, h: r.height }; })()"))
    viser(fr, 33.95, 36.05, 8)                                                                    # minZoom 8 : le plus bas zoom où la carte se lit ; le centre des bornes
    box, mb = box_()
    n0 = len(pg.bench.relief('elevation'))
    for k in range(40):                                                                           # 40 positions espacées de 20 px, sans pause
        pg.mouse.move(box['x'] + mb['l'] + mb['w'] / 2 - 780 + 20 * k, box['y'] + mb['t'] + mb['h'] / 2)       # de loin à gauche jusqu'au centre : les huit dernières positions sont dans les bornes
    assert len(pg.bench.relief('elevation')) - n0 <= 1
    attendre(fr, "RE.dwell !== 0 || RE.pend !== '' || RE.shown !== null || (document.getElementById('rp-alt') || { hidden: true }).hidden === false", "le pointeur au repos : l'attente de la tuile (RELIEF_DWELL) est partie ou la lecture est faite", lu='[RE.raf, RE.dwell, RE.pend]')
    attendre_relief_repos(fr)                                                                     # puis une pause : la tuile du dernier pixel se demande (RELIEF_DWELL, le délai de l'application, écoulé)
    assert len(pg.bench.relief('elevation')) - n0 == 1
    assert fr.evaluate(TAG)['tag'] is True
    # sous minZoom : rien, ni cartouche ni requête, à la souris comme au toucher
    viser(fr, 33.85, 35.95, 5)
    n0 = len(pg.bench.relief('elevation'))
    pg.mouse.move(box['x'] + mb['l'] + 300, box['y'] + mb['t'] + 300)
    pg.mouse.move(box['x'] + mb['l'] + 310, box['y'] + mb['t'] + 305)
    attendre_relief_repos(fr)
    assert fr.evaluate(TAG)['tag'] is False and len(pg.bench.relief('elevation')) == n0
    viser(fr, 33.85, 35.95, 7)
    pg.mouse.move(box['x'] + mb['l'] + 320, box['y'] + mb['t'] + 310)
    attendre_relief_repos(fr)
    assert fr.evaluate(TAG)['tag'] is False and len(pg.bench.relief('elevation')) == n0
    assert pg.errs == []
    pg.context.close()


@needs_pw
def test_touch_below_min_zoom_reads_nothing(browser):
    pg, fr = open_rp(browser, w=412, h=900, touch=True)
    tick_relief(fr, pg)
    viser(fr, 33.85, 35.95, 6)
    n0 = len(pg.bench.relief('elevation'))
    tap_at(pg, fr, 0, 0)
    assert fr.evaluate(TAG)['tag'] is False and fr.evaluate(TAG)['ring'] is False and len(pg.bench.relief('elevation')) == n0
    pg.context.close()


@needs_pw
def test_a_touch_on_a_marker_clears_the_tag_and_opens_the_sheet_and_a_touch_closing_the_search_shows_none(browser):
    pg, fr = open_rp(browser, w=412, h=900, touch=True)
    tick_relief(fr, pg)
    la, lo = 33.852, 35.987                                                                       # Rayak
    viser(fr, la, lo, 11)
    tap_at(pg, fr, -50, 40)
    assert fr.evaluate(TAG)['tag'] is True and fr.evaluate(TAG)['ring'] is True
    tap_at(pg, fr, 0, 0)                                                                          # le marqueur de l'aérodrome
    attendre(fr, "rtVisible('fiche') === true", 'la fiche de l\'aérodrome ouverte', lu="rtVisible('fiche')")
    assert fr.evaluate(TAG)['tag'] is False and fr.evaluate(TAG)['ring'] is False
    assert fr.evaluate("rtVisible('fiche')") is True
    fr.evaluate("document.getElementById('fiche-fermer').click()")
    attendre(fr, "rtVisible('fiche') === false", 'la fiche de l\'aérodrome fermée', lu="rtVisible('fiche')")
    fr.evaluate("document.querySelector('.rp-search-btn').click()")                               # la recherche ouverte : un toucher sur la carte la ferme, sans cartouche
    attendre(fr, 'SR.open === true', 'la recherche ouverte (SR.open)', lu='SR.open')
    assert fr.evaluate("SR.open") is True
    tap_at(pg, fr, -50, 40)
    assert fr.evaluate("SR.open") is False and fr.evaluate(TAG)['tag'] is False
    assert pg.errs == []
    pg.context.close()


@needs_pw
def test_the_kind_of_a_click_comes_from_the_last_pointerdown(browser):
    pg, fr = open_rp(browser)
    tick_relief(fr, pg)
    viser(fr, *tile_ll(1228, 819, .25, .25), 11)
    click = """(type) => { const h = __RP.map.getContainer(), r = h.getBoundingClientRect(), o = { clientX: r.left + r.width / 2 - 40, clientY: r.top + r.height / 2 + 40, bubbles: true };
        h.dispatchEvent(new PointerEvent('pointerdown', { ...o, pointerType: type })); h.dispatchEvent(new MouseEvent('click', o)); }"""     # le click ne porte aucun pointerType
    fr.evaluate(click, 'mouse')
    attendre_relief_repos(fr)
    assert fr.evaluate(TAG)['ring'] is False and fr.evaluate(TAG)['tag'] is False                 # souris : pas d'anneau
    fr.evaluate(click, 'touch')
    attendre(fr, "!(document.getElementById('rp-alt') || { hidden: true }).hidden", 'le cartouche posé au toucher', lu="(document.getElementById('rp-alt') || { hidden: true }).hidden")
    attendre_relief_repos(fr)
    assert fr.evaluate(TAG)['ring'] is True and fr.evaluate(TAG)['tag'] is True                   # doigt : le cartouche et l'anneau
    assert pg.errs == []
    pg.context.close()


@needs_pw
def test_the_pointer_on_a_map_control_hides_the_tag(browser):
    pg, fr = open_rp(browser)
    tick_relief(fr, pg)
    viser(fr, *tile_ll(1228, 819, .25, .25), 11)
    box = fr.frame_element().bounding_box()
    mb = fr.evaluate("(() => { const r = __RP.map.getContainer().getBoundingClientRect(); return { l: r.left, t: r.top, w: r.width, h: r.height }; })()")
    pg.mouse.move(box['x'] + mb['l'] + mb['w'] / 2, box['y'] + mb['t'] + mb['h'] / 2)
    attendre(fr, "!(document.getElementById('rp-alt') || { hidden: true }).hidden", 'le cartouche posé à la souris', lu="(document.getElementById('rp-alt') || { hidden: true }).hidden")
    attendre_relief_repos(fr)
    assert fr.evaluate(TAG)['tag'] is True
    for sel in ('.leaflet-control-zoom-in', '.leaflet-control-attribution'):
        r = fr.evaluate("(s) => { const b = document.querySelector(s).getBoundingClientRect(); return [b.left + b.width / 2, b.top + b.height / 2]; }", sel)
        pg.mouse.move(box['x'] + mb['w'] / 2 + mb['l'], box['y'] + mb['t'] + mb['h'] / 2)
        attendre(fr, "!(document.getElementById('rp-alt') || { hidden: true }).hidden", 'le cartouche posé à la souris', lu="(document.getElementById('rp-alt') || { hidden: true }).hidden")
        attendre_relief_repos(fr)
        assert fr.evaluate(TAG)['tag'] is True
        pg.mouse.move(box['x'] + r[0], box['y'] + r[1])
        attendre(fr, "(document.getElementById('rp-alt') || { hidden: true }).hidden === true", 'le cartouche masqué sur un contrôle de la carte', lu="(document.getElementById('rp-alt') || { hidden: true }).hidden")
        attendre_relief_repos(fr)
        assert fr.evaluate(TAG)['tag'] is False
    assert pg.errs == []
    pg.context.close()


@needs_pw
def test_a_description_with_another_tile_size_or_latitudes_off_the_mercator_is_unreadable(browser):
    pg, fr = open_rp(browser)
    pg.bench.doc = {**DOC, 'tileSize': 512}
    tick_relief(fr, pg)
    attendre(fr, "__toasts.length === 1", "l'échec annoncé (un toast)", lu='__toasts')
    assert fr.evaluate("__toasts") == ['⚠ Relief indisponible : la description reçue du serveur est illisible.'] and fr.evaluate("!!__RP.reliefLayer") is False
    tick_relief(fr, pg)
    tick_relief(fr, pg)                                                                           # décocher puis recocher : pas de second toast
    attendre_images(fr, 3)
    assert len(fr.evaluate("__toasts")) == 1
    pg.context.close()
    pg, fr = open_rp(browser)
    pg.bench.doc = {**DOC, 'bounds': [[33.15, 35.15], [85.1, 36.95]]}
    tick_relief(fr, pg)
    attendre(fr, "__toasts.length === 1", "l'échec annoncé (un toast)", lu='__toasts')
    assert len(fr.evaluate("__toasts")) == 1 and fr.evaluate("!!__RP.reliefLayer") is False
    pg.context.close()


@needs_pw
def test_the_export_leaves_the_tag_and_the_ring_out_of_the_image(browser):
    pg, fr = open_rp(browser, w=412, h=900, touch=True)
    pg.evaluate("window.MP_SEND_MAP = (o) => { window.__sent = o; }")
    tick_relief(fr, pg)
    viser(fr, *tile_ll(1228, 819, .25, .25), 11)
    tap_at(pg, fr, -50, 40)
    assert fr.evaluate(TAG)['tag'] is True
    fr.evaluate("expOpen()")                                                                      # l'ouverture du cadre les efface
    attendre(fr, "EXP.on === true && (document.getElementById('rp-alt') || { hidden: true }).hidden === true", "le cadre d'export ouvert, le cartouche effacé", lu="[EXP.on, (document.getElementById('rp-alt') || { hidden: true }).hidden]")
    attendre_relief_repos(fr)
    assert fr.evaluate(TAG)['tag'] is False
    tap_at(pg, fr, -60, 60)                                                                       # un toucher dans le cadre les montre de nouveau (le cadre garde la carte en lecture)
    fr.evaluate("""() => { const o = window.html2canvas; window.__ign = null; window.html2canvas = function (el, opts) {
        window.__ign = ['rp-alt', 'rp-alt-x'].map(id => opts.ignoreElements(document.getElementById(id))); return o.apply(this, arguments); }; }""")
    fr.evaluate("expGo()")
    attendre(pg, '!!window.__sent', "la carte envoyée (MP_SEND_MAP appelé après le rendu html2canvas)", lu='window.__sent', delai=30000)
    assert fr.evaluate("window.__ign") == [True, True]                                            # le rendu les ignore
    assert pg.evaluate("!!window.__sent") is True
    assert pg.errs == []
    pg.context.close()
