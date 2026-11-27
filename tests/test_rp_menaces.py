"""La couche des menaces du Route Planner, jouée sur le shell construit (dist/dcs_mission_plan.html, chromium), sans réseau : les requêtes hors file:/data:/blob: sont interceptées ;
sous l'adresse publique des tuiles, le banc sert le relief.json de Syria et des tuiles d'altitude fabriquées (une plaine à 100 m et, dans chaque tuile, une crête nord-sud à 300 m sur les colonnes 150 à 159).
Les contrôles passent par le DOM, dans le shell. Les sections de ce fichier suivent celles du cadrage : géométrie, hauteur, route, fiche, affichage, sans relief, cartouche, Worker, Field Manual."""
import hashlib
import json
import math
import re
import struct
import sys
import zlib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tests'))
from banc_attente import attendre, attendre_ecoute_storage, attendre_images, attendre_menaces, attendre_rp, attendre_shell, exemple  # noqa: E402

CHROMIUM = Path('/opt/pw-browsers/chromium')
try:
    import playwright.sync_api  # noqa: F401
    HAS_PW = CHROMIUM.exists()
except ImportError:
    HAS_PW = False
needs_pw = pytest.mark.skipif(not HAS_PW, reason='playwright ou chromium absent')

SHELL = 'file://' + str(ROOT / 'dist' / 'dcs_mission_plan.html')
sys.path.insert(0, str(ROOT))
from public_host_block import build_block  # noqa: E402

PT = re.search(r"PUBLIC_TILES = '([^']+)'", build_block()).group(1)
BOUNDS = [[33.15, 35.15], [34.75, 36.95]]
DOC = {'format': 'dcs-relief-tiles-v1', 'theatre': 'Syria', 'edition': 'test', 'minZoom': 8, 'maxNativeZoom': 11, 'tileSize': 256, 'bounds': BOUNDS,
       'layers': {'hillshade': {'path': 'hillshade/{z}/{x}/{y}.webp'},
                  'elevation': {'path': 'elevation/{z}/{x}/{y}.png', 'encoding': 'terrain-rgb', 'base_m': -10000, 'step_m': 0.1}},
       'attribution': 'test', 'source': 'test', 'tiles_per_zoom': {}}
CREST_X0, CREST_X1 = 150, 160            # les colonnes de la crête, dans chaque tuile
PLAIN_M, CREST_M = 100.0, 300.0
NBSP = ' '
# la largeur du pouce du curseur, lue dans la feuille de style de la page (un pseudo-élément ne se lit pas par getComputedStyle)
THUMB_JS = "window.thumbW = function (sel) { sel = sel || '::-webkit-slider-thumb'; for (const sh of document.styleSheets) for (const r of sh.cssRules) if (r.selectorText && r.selectorText.indexOf('#rp-thr input') === 0 && r.selectorText.indexOf(sel) !== -1) return parseFloat(r.style.width); return NaN; };\n"
# sha256 des deux figures de la page du RP du Field Manual (planche large, planche téléphone), mesurées sur le socle 8fb4e66
PLATE_RP_BASE = ['0461d458aa1c6da4dbfb551a391b97f8708e55351da7ba046e12a7aae45ff020', '05134ca6552ba21292aaf558921a3bea29d3f18730b57a6300322c4047052743']


def png(w, h, pixel):
    rows = b''.join(b'\x00' + b''.join(bytes(pixel(x, y)) for x in range(w)) for y in range(h))

    def chunk(t, d):
        return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 6, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(rows)) + chunk(b'IEND', b'')


def rgb(h):
    v = round((h + 10000) / 0.1)
    return (v >> 16, (v >> 8) & 255, v & 255, 255)


ELEV = png(256, 256, lambda x, y: rgb(CREST_M if CREST_X0 <= x < CREST_X1 else PLAIN_M))
SHADE = png(256, 256, lambda x, y: (60, 40, 20, 90))


def tile_ll(tx, ty, fx, fy, z=11):
    n = 2 ** z
    return math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * (ty + fy) / n)))), (tx + fx) / n * 360 - 180


# la menace : le pixel 100 de la tuile 1229 / 820 du niveau 11, au milieu de sa ligne
TX, TY, TCOL = 1229, 820, 100
T_LAT, T_LON = tile_ll(TX, TY, (TCOL + 0.5) / 256, 0.5)


class Bench:
    def __init__(self):
        self.log = []
        self.doc = DOC
        self.elev = ELEV

    def handler(self, route):
        url = route.request.url
        if url.startswith(('file:', 'data:', 'blob:')):
            return route.continue_()
        self.log.append(url)
        cors = {'Access-Control-Allow-Origin': '*'}
        if url.startswith(PT + 'relief/'):
            rest = url[len(PT + 'relief/'):]
            if rest == 'Syria/relief.json':
                if self.doc is None:
                    return route.fulfill(status=404, headers=cors, body='')
                return route.fulfill(status=200, headers={**cors, 'Content-Type': 'application/json'}, body=json.dumps(self.doc))
            if rest.startswith('Syria/hillshade/'):
                return route.fulfill(status=200, headers={**cors, 'Content-Type': 'image/png'}, body=SHADE)
            if rest.startswith('Syria/elevation/'):
                return route.fulfill(status=200, headers={**cors, 'Content-Type': 'image/png'}, body=self.elev)
            return route.fulfill(status=404, headers=cors, body='')
        return route.abort()


@pytest.fixture(scope='module')
def browser():
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        br = p.chromium.launch(executable_path=str(CHROMIUM), args=['--no-sandbox'])
        yield br
        br.close()


def open_rp(br, w=1280, h=800, lang='fr', init='', doc=True, seed=None):
    ctx = br.new_context(viewport={'width': w, 'height': h}, has_touch=w < 700, is_mobile=w < 700)
    ctx.add_init_script("try{localStorage.setItem('lang_v1','%s')}catch(e){}" % lang)
    if seed:
        ctx.add_init_script("(() => { if (!sessionStorage.getItem('seeded')) { const d = %s; for (const k in d) localStorage.setItem(k, d[k]); sessionStorage.setItem('seeded', '1'); } })()" % json.dumps(seed))
    if init:
        ctx.add_init_script(init)
    pg = ctx.new_page()
    pg.errs = []
    pg.on('pageerror', lambda e: pg.errs.append(str(e)))
    pg.bench = Bench()
    if not doc:
        pg.bench.doc = None
    pg.route('**/*', pg.bench.handler)
    pg.goto('about:blank')
    pg.goto(SHELL, wait_until='commit')
    attendre_shell(pg)
    exemple(pg, 'fl')
    pg.evaluate("openModule('rp')")
    fr = attendre_rp(pg)
    return pg, fr


def open_rp_qui_ecoute(br, essais=10, **kw):
    """open_rp, pour les tests où un autre outil écrit le théâtre ou la route que le Route Planner doit suivre : un cadre sourd aux évènements storage (voir attendre_ecoute_storage) est fermé et l'ouverture refaite."""
    for _ in range(essais):
        pg, fr = open_rp(br, **kw)
        if attendre_ecoute_storage(pg, fr):
            return pg, fr
        pg.context.close()
    raise AssertionError('le cadre du Route Planner est resté sourd aux évènements storage en %d ouvertures' % essais)


SIDC = {'sam': 'GPEWMS--', 'aaa': 'GPEWAH--', 'radar': 'GPESR---'}


def sym(i, system, lat=T_LAT, lon=T_LON, name='', side='H', kind='sam', **extra):
    return {'id': 't%d' % i, 'type': 'symbol', 'name': name, 'lat': lat, 'lon': lon, 'sidc': 'S' + side + SIDC[kind] + '-----', 'style': 'fill', 'size': 'm', 'formation': '', 'threat': system, **extra}


def setup(fr, items, pts=None, wait=True):
    """Remplace les calques par un calque dessiné, et (si pts) la route ; les menaces actives se calculent."""
    fr.evaluate("""([items, pts]) => {
        CF_LAYERS.length = 0;
        CF_LAYERS.push({ id: 'L1', name: 'x', visible: true, source: { kind: 'drawn', file: '' }, items: items.map(cfItem) });
        if (pts) S.points = pts.map((p, i) => Object.assign({ pid: 'p' + i }, p));
        renderAll();
    }""", [items, pts])
    if wait:
        ready(fr)


def ready(fr, timeout=30000):
    attendre_menaces(fr, timeout)


def grid(fr, i=0):
    return fr.evaluate("""(i) => { const g = Array.from(__RP.thr.grids.values())[i];
        return { z: g.z, side: g.side, K: g.K, mpp: g.mpp, gs: g.gs, zs: g.zs, R: g.R, worker: g.worker, tiles: g.tiles }; }""", i)


def hv_at(fr, dx, dy=0, i=0):
    return fr.evaluate("([dx, dy, i]) => { const g = Array.from(__RP.thr.grids.values())[i]; return g.hv[(g.K + dy) * g.side + g.K + dx]; }", [dx, dy, i])


def display(fr, pg, on):
    fr.evaluate("if (DSP.open !== %s) document.getElementById('btn-display').click()" % ('true' if on else 'false'))
    attendre(fr, 'DSP.open === arg', "le menu Affichage %s (DSP.open)" % ('ouvert' if on else 'fermé'), lu='DSP.open', arg=on)
    attendre_images(fr, 2)


def set_rank(fr, pg, r):
    fr.evaluate("(r) => { const el = document.getElementById('thr-range'); el.value = String(r); el.dispatchEvent(new Event('input', { bubbles: true })); }", r)
    pg.wait_for_timeout(250)


def tile_alpha(fr, px, py, tx=TX, ty=TY, z=11):
    """L'alpha du pixel (px, py) de la tuile (tx, ty) de la GridLayer des menaces au zoom z de la carte."""
    return fr.evaluate("""([px, py, tx, ty, z]) => {
        const zl = __RP.thr.zone;
        if (!zl) return null;
        const k = Object.keys(zl._tiles).find(q => { const c = zl._tiles[q].coords; return c.x === tx && c.y === ty && c.z === z; });
        if (!k) return undefined;
        return zl._tiles[k].el.getContext('2d').getImageData(px, py, 1, 1).data[3];
    }""", [px, py, tx, ty, z])


def view_threat(fr, pg, z=11):
    fr.evaluate("([la, lo, z]) => __RP.map.setView([la, lo], z, { animate: false })", [T_LAT, T_LON, z])
    pg.wait_for_timeout(900)


def east(fr, lat, lon, km):
    return fr.evaluate("([la, lo, km]) => { const p = legDest({ lat: la, lon: lo }, 90, km); return [p.lat, p.lon]; }", [lat, lon, km])


# ---------- la géométrie : une crête, une menace à l'ouest, la hauteur de visibilité derrière ----------
@needs_pw
def test_geometry_height_of_visibility_behind_a_crest(browser):
    pg, fr = open_rp(browser)
    setup(fr, [sym(0, 'sa-8')])
    g = grid(fr)
    assert g['z'] == 11 and g['gs'] == pytest.approx(PLAIN_M, abs=0.2) and g['zs'] == pytest.approx(105, abs=0.2)       # R = 10,3 km : le niveau le plus fin ; capteur de conduite de tir à 5 m
    assert g['side'] == 2 * math.ceil(10300 / g['mpp']) + 1 == 2 * g['K'] + 1
    d1 = (CREST_X0 - TCOL - 0.5) * g['mpp']                                    # la distance au bord ouest de la crête
    behind = []
    for km in (1, 3, 6):
        dx = (CREST_X1 - TCOL) + round(km * 1000 / g['mpp'])                    # des pixels derrière le bord est de la crête
        d = dx * g['mpp']
        want = (105 + (CREST_M - 105) * d / d1) - 100
        got = hv_at(fr, dx)
        behind.append((km, want, got))
        assert abs(got - want) <= 15, (km, want, got)
    assert hv_at(fr, -30) == 0 and hv_at(fr, -90) == 0 and hv_at(fr, 20) == 0     # côté ouest et devant la crête : vu au ras du sol
    assert hv_at(fr, 0, 0) == 0
    # rien hors du disque : les coins du carré, un pixel au-delà de la portée, les bords
    assert hv_at(fr, g['K'], g['K']) == float('inf') and hv_at(fr, -g['K'], -g['K']) == float('inf')
    assert fr.evaluate("""() => { const g = Array.from(__RP.thr.grids.values())[0]; let bad = 0;
        for (let j = 0; j < g.side; j++) for (let i = 0; i < g.side; i++) { const dx = i - g.K, dy = j - g.K; if (Math.hypot(dx, dy) * g.mpp > g.R * 1.02 && g.hv[j * g.side + i] !== Infinity) bad++; }
        return bad; }""") == 0
    assert pg.errs == []
    pg.context.close()


@needs_pw
def test_the_grid_level_and_the_tiles_read(browser):
    pg, fr = open_rp(browser)
    setup(fr, [sym(0, 'sa-10', name='S10')])             # 120 km : z10 à cette latitude
    g = grid(fr)
    assert g['z'] == 10 and g['R'] == 120000 and g['side'] == 2 * math.ceil(120000 / g['mpp']) + 1 and g['R'] / g['mpp'] <= 1024
    assert 40075016.686 * math.cos(math.radians(T_LAT)) / (256 * 2 ** 10) == pytest.approx(g['mpp'], rel=1e-9)
    assert g['tiles'] >= 36
    pg.context.close()


# ---------- la hauteur : la zone, une seule teinte ----------
@needs_pw
def test_zone_is_painted_at_the_checked_height_above_the_visibility_height(browser):
    pg, fr = open_rp(browser)
    setup(fr, [sym(0, 'sa-8')])
    view_threat(fr, pg)
    assert fr.evaluate("__RP.thr.zone.getPane() === __RP.map.getPane('threats')")
    assert fr.evaluate("__RP.thr.zone.options.pane") == 'threats'
    g = grid(fr)
    dx = 107                                                                   # 107 pixels à l'est : derrière la crête
    want = 105 + (CREST_M - 105) * dx / (CREST_X0 - TCOL - 0.5) - 100          # 426,5 m
    assert abs(hv_at(fr, dx) - want) <= 15
    col = TCOL + dx
    for rank, painted in ((6, False), (7, True), (11, True), (12, False)):                  # 300 m : non ; 500 m : oui
        set_rank(fr, pg, rank)
        assert fr.evaluate("__RP.thr.paint.H") == [0, 15, 30, 60, 100, 150, 300, 500, 1000, 2000, 3000, 4500, 6000][rank]
        assert tile_alpha(fr, col, 128) == (110 if painted else 0), rank
    set_rank(fr, pg, 2)
    assert tile_alpha(fr, 70, 128) == 110                                      # à l'ouest, vu au ras du sol
    assert tile_alpha(fr, 200, 128, TX + 1) == 0                                           # hors du disque
    assert tile_alpha(fr, 128, 200) == 110                                     # 28 px à l'est, 72 au sud : devant la crête, dans le disque
    assert pg.errs == []
    pg.context.close()


@needs_pw
def test_ceiling_cuts_the_zone_and_changing_the_height_does_not_recompute_the_grids(browser):
    pg, fr = open_rp(browser)
    setup(fr, [sym(0, 'sa-19')])                                               # plafond 3 600 m : le dernier rang offert est le rang 12 (6 000 m), jamais moins
    view_threat(fr, pg)
    assert fr.evaluate("__RP.thr.paint.H") == 30 and fr.evaluate("__RP.thrTop()") == 12
    n0 = len(pg.bench.log)
    ver = fr.evaluate("__RP.thr.ver")
    set_rank(fr, pg, 10)                                                       # 3 000 m : sous le plafond
    assert tile_alpha(fr, 70, 128) == 110
    set_rank(fr, pg, 12)                                                       # 6 000 m : au-dessus du plafond, rien n'est peint (100 + 6 000 − 100 > 3 600)
    assert tile_alpha(fr, 70, 128) == 0 and tile_alpha(fr, 60, 100) == 0
    assert fr.evaluate("__RP.thr.ver") == ver and len(pg.bench.log) == n0     # ni nouveau calcul, ni nouvelle tuile
    pg.context.close()


@needs_pw
def test_two_overlapping_threats_give_one_tint(browser):
    pg, fr = open_rp(browser)
    la, lo = east(fr, T_LAT, T_LON, -0.5)
    setup(fr, [sym(0, 'sa-8'), sym(1, 'sa-8', la, lo)])
    view_threat(fr, pg)
    assert fr.evaluate("__RP.thr.grids.size") == 2
    assert fr.evaluate("document.querySelectorAll('.leaflet-threats-pane .leaflet-layer').length") == 1       # une seule GridLayer
    assert tile_alpha(fr, 70, 128) == 110                                      # là où les deux voient : la même teinte, sans surcharge
    pg.context.close()


# ---------- la route : jugée à son altitude ----------
def route_over_the_crest(fr, west_km=3.0, east_km=7.0, alt=30, ref='AGL'):
    a = east(fr, T_LAT, T_LON, -west_km)
    b = east(fr, a[0], a[1], west_km + east_km)
    return [{'name': 'A', 'lat': a[0], 'lon': a[1], 'alt': alt, 'altRef': ref}, {'name': 'B', 'lat': b[0], 'lon': b[1], 'alt': alt, 'altRef': ref}]


def analytic_seen_km(g, west_km, agl=30):
    d1 = (CREST_X0 - TCOL - 0.5) * g['mpp']
    return west_km + d1 * (1 + agl / (CREST_M - 105)) / 1000


@needs_pw
def test_route_seen_distance_halo_and_navigation_line(browser):
    pg, fr = open_rp(browser)
    setup(fr, [sym(0, 'sa-8', name='SA-8')])
    pts = route_over_the_crest(fr)
    setup(fr, [sym(0, 'sa-8', name='SA-8')], pts)
    fr.wait_for_function("__RP.thr.seen && Object.keys(__RP.thr.seen).length > 0", timeout=20000)
    g = grid(fr)
    seen = fr.evaluate("__RP.thr.seen")
    want = analytic_seen_km(g, 3.0)
    assert list(seen) == ['1'] and seen['1'][0]['name'] == 'SA-8'
    assert abs(seen['1'][0]['km'] - want) <= 0.2, (seen, want)
    # le halo : une polyligne jaune, dans le volet de la route vue
    halo = fr.evaluate("""() => __RP.thr.halo.getLayers().map(l => ({ pane: l.options.pane, color: l.options.color, weight: l.options.weight, opacity: l.options.opacity, cap: l.options.lineCap,
        interactive: l.options.interactive, n: l.getLatLngs().length, km: l.getLatLngs().slice(1).reduce((s, p, i) => s + legCalc({ lat: l.getLatLngs()[i].lat, lon: l.getLatLngs()[i].lng }, { lat: p.lat, lon: p.lng }).km, 0) }))""")
    assert len(halo) == 1 and halo[0]['pane'] == 'thrroute' and halo[0]['color'] == '#ffd400' and halo[0]['weight'] == 20 and halo[0]['opacity'] == 0.92
    assert halo[0]['cap'] == 'butt' and halo[0]['interactive'] is False and abs(halo[0]['km'] - want) <= 0.3
    assert fr.evaluate("__RP.map.getPane('thrroute').style.zIndex") == '398' and fr.evaluate("__RP.map.getPane('threats').style.zIndex") == '260'
    # la feuille de navigation : sous la ligne de la branche vue
    row = fr.evaluate("""() => { const r = document.querySelector('#nav-body tr.thr'); return { txt: r.textContent, prev: r.previousElementSibling.className, cols: r.children.length, span: r.children[1].colSpan }; }""")
    assert row['prev'] == 'leg' and row['cols'] == 2 and row['span'] == 3
    m = re.fullmatch(r'⚠ Vu par SA-8 sur ([\d,]+) km', row['txt'])
    assert m and abs(float(m.group(1).replace(',', '.')) - want) <= 0.2
    # l'anglais, en milles marins
    fr.evaluate("unChoose('nm'); setLang('en')")
    pg.wait_for_timeout(300)
    txt = fr.evaluate("document.querySelector('#nav-body tr.thr').textContent")
    m = re.fullmatch(r'⚠ Seen by SA-8 over ([\d.]+) NM', txt)
    assert m and abs(float(m.group(1)) * 1.852 - want) <= 0.2
    assert pg.errs == []
    pg.context.close()


@needs_pw
def test_route_is_judged_at_its_own_altitude_and_only_the_chosen_route_when_shown(browser):
    pg, fr = open_rp(browser)
    items = [sym(0, 'sa-8', name='SA-8')]
    pts = route_over_the_crest(fr, alt=800)                                    # bien au-dessus de la crête : vue sur tout le disque
    setup(fr, items, pts)
    fr.wait_for_function("__RP.thr.seen && Object.keys(__RP.thr.seen).length > 0", timeout=20000)
    km = fr.evaluate("__RP.thr.seen['1'][0].km")
    assert 9 < km < 10.3 + 3.0                                                 # de l'entrée dans le disque à sa sortie, à 900 m du sol : plafond 5 100 m
    # en altitude mer, la même altitude absolue : 330 m MSL passe la crête à 30 m
    pts = route_over_the_crest(fr, alt=330, ref='MSL')
    setup(fr, items, pts)
    fr.wait_for_function("__RP.thr.seen && __RP.thr.seen['1'] && Math.abs(__RP.thr.seen['1'][0].km - %f) < 0.3" % analytic_seen_km(grid(fr), 3.0), timeout=20000)
    # des routes masquées : ni halo, ni ligne
    fr.evaluate("dspSetRoutes('none')")
    fr.wait_for_function("__RP.thr.halo.getLayers().length === 0 && !document.querySelector('#nav-body tr.thr') ", timeout=10000)
    fr.evaluate("dspSetRoutes('all')")
    fr.wait_for_function("__RP.thr.halo.getLayers().length === 1", timeout=20000)
    # au-dessus du plafond : plus vue
    pts = route_over_the_crest(fr, alt=6000, ref='MSL')
    setup(fr, items, pts)
    pg.wait_for_timeout(600)
    assert fr.evaluate("Object.keys(__RP.thr.seen || {}).length") == 0 and fr.evaluate("__RP.thr.halo.getLayers().length") == 0
    pg.context.close()


# ---------- la fiche du symbole ----------
def open_sheet(fr, item_id='t0'):
    fr.evaluate("""(id) => { setTapMode('draw'); DR.layerId = 'L1'; drSelect('L1', id); DR.sheet = true; DR.sheetKey = ''; drSyncUi(); }""", item_id)


def options(fr):
    return fr.evaluate("Array.from(document.querySelectorAll('#dr-sheet select[data-f=threat] option')).map(o => [o.value, o.textContent, o.selected])")


@needs_pw
def test_sheet_lists_the_systems_of_the_symbol_kind_sorted_by_name(browser):
    pg, fr = open_rp(browser)
    setup(fr, [sym(0, '', kind='sam', threat=None), sym(1, '', kind='aaa'), sym(2, '', kind='radar'), sym(3, '', kind='sam', side='F'), sym(4, '', kind='sam')], wait=False)
    fr.evaluate("CF_LAYERS[0].items.forEach(it => { delete it.threat; }); drawLayers();")
    for i, n in ((0, 26), (1, 18), (2, 13)):
        open_sheet(fr, 't%d' % i)
        o = options(fr)
        assert len(o) == n + 1 and o[0] == ['', 'Aucun', True], i
        names = [x[1] for x in o[1:]]
        assert len(set(names)) == n
        assert names == fr.evaluate("(k) => thrListFor(k).map(s => thrSysName(s))", ['sam', 'aaa', 'radar'][i])
        assert fr.evaluate("(k) => { const a = thrListFor(k).map(s => thrSysName(s)); return JSON.stringify(a) === JSON.stringify(a.slice().sort((x, y) => x.localeCompare(y, 'fr'))); }", ['sam', 'aaa', 'radar'][i])
    fr.evaluate("setLang('en')")
    open_sheet(fr, 't0')
    assert options(fr)[0][1] == 'None'
    fr.evaluate("setLang('fr')")
    for i in (3,):                                                             # un symbole ami : pas de champ
        open_sheet(fr, 't%d' % i)
        assert fr.evaluate("!document.querySelector('#dr-sheet select[data-f=threat]')")
    # un symbole à venir (brouillon) : pas de champ non plus
    fr.evaluate("DR.tool = 'symbol'; DR.draft = drNewDraft('symbol'); DR.draft.it.sidc = 'SH' + 'GPEWMS--' + '-----'; DR.sel = null; DR.sheet = true; DR.sheetKey = ''; drSyncUi();")
    assert fr.evaluate("!document.querySelector('#dr-sheet select[data-f=threat]') && !!document.querySelector('#dr-sheet')")
    assert pg.errs == []
    pg.context.close()


@needs_pw
def test_sheet_info_line_choice_units_and_unknown_values(browser):
    pg, fr = open_rp(browser)
    setup(fr, [sym(0, '', kind='sam'), sym(1, '', kind='radar'), sym(2, 'zz-9', kind='sam'), sym(3, '', kind='aaa')], wait=False)
    fr.evaluate("delete CF_LAYERS[0].items[0].threat; delete CF_LAYERS[0].items[1].threat; delete CF_LAYERS[0].items[3].threat; drawLayers();")
    open_sheet(fr, 't0')
    pick = lambda v: fr.evaluate("(v) => { const s = document.querySelector('#dr-sheet select[data-f=threat]'); s.value = v; s.dispatchEvent(new Event('change', { bubbles: true })); }", v)
    info = lambda: fr.evaluate("document.getElementById('dr-f-threat-info').textContent")
    assert info() == ''
    pick('sa-6')
    assert fr.evaluate("CF_LAYERS[0].items[0].threat") == 'sa-6'
    assert info() == f'Tir 25,0 km · détection 70,0 km · plafond 8{NBSP}000 m · capteur : radar de conduite de tir'
    pick('sa-15-m2')
    assert info() == f'Tir 16,0 km · détection 32,0 km · plafond 6{NBSP}000 m · capteur : radar de conduite de tir'
    pick('igla')
    assert info().endswith('capteur : le tireur lui-même') and f'plafond 3{NBSP}600 m' in info()
    pick('chaparral')
    assert f'plafond 3{NBSP}600 m' in info()
    # un système qui reste sans plafond : un canon antiaérien
    open_sheet(fr, 't3')
    pick('zsu-57-2')
    assert info().endswith('capteur : le tireur lui-même') and 'plafond non connu' in info()
    pick('')
    open_sheet(fr, 't0')
    pick('sa-6')
    fr.evaluate("unChoose('nm'); unChoose('ft')")
    open_sheet(fr, 't0')
    assert info() == f'Tir 13,5 NM · détection 37,8 NM · plafond 26{NBSP}247 ft · capteur : radar de conduite de tir'
    fr.evaluate("setLang('en')")
    open_sheet(fr, 't0')
    assert info() == 'Fire 13.5 NM · detection 37.8 NM · ceiling 26,247 ft · sensor: fire-control radar'
    fr.evaluate("setLang('fr'); unChoose('km'); unChoose('m')")
    # un radar : sans tir
    open_sheet(fr, 't1')
    pick('1l13')
    assert info() == f'Détection 300 km · plafond 20{NBSP}000 m · capteur : radar de veille'
    pick('55g6')
    assert info() == f'Détection 400 km · plafond 20{NBSP}000 m · capteur : radar de veille'
    # une valeur hors table : choisie, nommée « (inconnu) », ne dessine rien
    open_sheet(fr, 't2')
    o = options(fr)
    assert ['zz-9', 'zz-9 (inconnu)', True] in o and sum(1 for x in o if x[2]) == 1 and len(o) == 26 + 2
    assert info() == ''
    assert fr.evaluate("CF_LAYERS[0].items[2].threat") == 'zz-9'
    assert fr.evaluate("__RP.thr.act.map(a => a.it.id)") == ['t0', 't1']
    assert fr.evaluate("__RP.thr.act.every(a => a.it.id !== 't2')")
    # « Aucun » retire le champ
    open_sheet(fr, 't0')
    pick('')
    assert fr.evaluate("'threat' in CF_LAYERS[0].items[0]") is False
    # la fiche en mode Lire : une ligne « Système : nom »
    pick('sa-6')
    fr.evaluate("setTapMode('read')")
    html = fr.evaluate("cfFiche(CF_LAYERS[0].items[0]).textContent")
    assert 'Système : SA-6 Kub Gainful' in html
    assert 'Système' not in fr.evaluate("cfFiche(CF_LAYERS[0].items[2]).textContent")
    assert pg.errs == []
    pg.context.close()


@needs_pw
def test_the_field_follows_the_side_and_the_kind_and_survives_copy_and_cfitem(browser):
    pg, fr = open_rp(browser)
    setup(fr, [sym(0, 'sa-6', kind='sam')], wait=False)
    ev = lambda js, *a: fr.evaluate(js, list(a)[0] if len(a) == 1 else (list(a) or None))
    it = "CF_LAYERS[0].items[0]"
    # même nature : le système reste ; une autre nature, ou un code hors des trois : il s'efface
    assert fr.evaluate("(() => { const it = %s; symSet(it, 'sym', 'GPEWMS--'); return it.threat; })()" % it) == 'sa-6'
    assert fr.evaluate("(() => { const it = %s; symSet(it, 'sym', 'GPEWAH--'); return it.threat === undefined; })()" % it) is True
    fr.evaluate("%s.threat = 'sa-6'" % it)
    assert fr.evaluate("(() => { const it = %s; symSet(it, 'sym', 'GPUCI---'); return it.threat === undefined; })()" % it) is True
    # l'ami ne porte pas de système ; le retour à l'ennemi ne le rend pas
    fr.evaluate("(() => { const it = %s; symSet(it, 'sym', 'GPEWMS--'); it.threat = 'sa-6'; symSet(it, 'side', 'F'); })()" % it)
    assert fr.evaluate("%s.threat === undefined" % it) is True
    fr.evaluate("(() => { const it = %s; symSet(it, 'side', 'H'); })()" % it)
    assert fr.evaluate("%s.threat === undefined" % it) is True
    # une valeur inconnue reste choisie quand on change de symbole dans la même nature
    fr.evaluate("(() => { const it = %s; it.threat = 'zz-9'; symSet(it, 'sym', 'GPEWMS--'); })()" % it)
    assert fr.evaluate("%s.threat" % it) == 'zz-9'
    # drSetField : symbole seulement ; '' retire
    assert fr.evaluate("drSetField({ type: 'point' }, 'threat', 'sa-6')") is False
    assert fr.evaluate("(() => { const it = %s; return [drSetField(it, 'threat', 'sa-6'), it.threat, drSetField(it, 'threat', ''), 'threat' in it, drSetField(it, 'threat', 'Bad Value')]; })()" % it) == [True, 'sa-6', True, False, False]
    # cfItem : garde le lisible, omet l'illisible, ne refuse pas l'objet
    raw = {'type': 'symbol', 'lat': 33.8, 'lon': 36.0, 'sidc': 'SHGPEWMS-------'}
    out = fr.evaluate("(raw) => [cfItem({ ...raw, threat: 'sa-6' }), cfItem({ ...raw, threat: 'SA 6' }), cfItem({ ...raw, threat: 7 }), cfItem({ ...raw, threat: 'x'.repeat(41) }), cfItem({ ...raw, threat: '' }), cfItem({ ...raw, threat: 'a' }), cfItem(raw)]", raw)
    assert out[0]['threat'] == 'sa-6' and all('threat' not in o for o in (out[1], out[2], out[3], out[4], out[6])) and out[5]['threat'] == 'a'
    assert all(o is not None and o['type'] == 'symbol' for o in out)
    assert list(out[0])[-1] == 'threat'
    # un symbole neuf n'a pas de champ ; la copie le garde
    assert fr.evaluate("'threat' in drNewSymbol({ lat: 33.8, lng: 36.0 })") is False
    fr.evaluate("%s.threat = 'sa-6'; setTapMode('draw'); DR.layerId = 'L1'; drSelect('L1', 't0'); drCopy();" % it)
    assert fr.evaluate("CF_LAYERS[0].items.map(i => i.threat)") == ['sa-6', 'sa-6']
    stored = json.loads(fr.evaluate("localStorage.getItem('route_layers_v1')"))
    assert [i.get('threat') for i in stored['layers'][0]['items']] == ['sa-6', 'sa-6']
    assert pg.errs == []
    pg.context.close()


# ---------- l'affichage : la case, la hauteur, les crans ----------
@needs_pw
def test_display_row_default_storage_and_dot(browser):
    pg, fr = open_rp(browser)
    assert fr.evaluate("DISP.threats") is True and fr.evaluate("DISP.thrStep") == 2 and fr.evaluate("document.getElementById('dsp-dot').hidden") is True
    display(fr, pg, True)
    row = fr.evaluate("""(() => { const r = document.querySelector('#dsp-panel [data-k=threats]'); return { role: r.getAttribute('role'), checked: r.getAttribute('aria-checked'), cls: r.className,
        prev: r.previousElementSibling.getAttribute('data-k'), next: r.nextElementSibling.textContent.trim(), disabled: r.getAttribute('aria-disabled'), title: r.title, txt: r.textContent.trim() }; })()""")
    assert row == {'role': 'menuitemcheckbox', 'checked': 'true', 'cls': 'tbm-opt dsp-opt', 'prev': 'relief', 'next': 'Profil du sol', 'disabled': None,
                   'title': 'Zones de tir et de détection des symboles ennemis SAM, AAA et Radar qui ont un système', 'txt': 'Menaces'}
    fr.evaluate("persistLayers()")                                             # route_layers_v1 existe : on y vérifie que l'affichage n'entre pas
    before = fr.evaluate("localStorage.getItem('route_state_v1')")
    fr.evaluate("document.querySelector('#dsp-panel [data-k=threats]').click()")
    pg.wait_for_timeout(300)
    assert fr.evaluate("DISP.threats") is False and fr.evaluate("document.getElementById('dsp-dot').hidden") is False
    st = json.loads(fr.evaluate("localStorage.getItem('rp_display_v1')"))
    assert st['threats'] is False and st['thrStep'] == 2
    assert fr.evaluate("localStorage.getItem('route_state_v1')") == before
    layers = fr.evaluate("localStorage.getItem('route_layers_v1')")
    assert layers is not None and 'thrStep' not in layers and 'threats' not in json.loads(layers)
    display(fr, pg, False)
    # jamais grisée, même sans relief
    fr.evaluate("(id) => { const s = document.getElementById('theatre'); s.value = id; s.dispatchEvent(new Event('change', { bubbles: true })); }", 'Nevada')
    pg.wait_for_timeout(600)
    display(fr, pg, True)
    assert fr.evaluate("document.querySelector('#dsp-panel [data-k=threats]').getAttribute('aria-disabled')") is None
    assert pg.errs == []
    pg.context.close()


@needs_pw
def test_height_is_kept_read_back_in_ft_and_the_last_step_follows_the_ceilings(browser):
    pg, fr = open_rp(browser)
    setup(fr, [sym(0, 'sa-8')])
    ticks = lambda: fr.evaluate("Array.from(document.querySelectorAll('#rp-thr .thr-tk')).map(e => e.textContent)")
    assert ticks() == ['0', '30', '100', '300', '2' + NBSP + '000', '6' + NBSP + '000']       # plafond 5 100 m : le rang 12 (6 000 m) clôt la suite
    assert fr.evaluate("document.getElementById('thr-range').max") == '12' and fr.evaluate("document.getElementById('thr-v').textContent") == '30 m sol'
    set_rank(fr, pg, 7)
    assert fr.evaluate("DISP.thrStep") == 7 and json.loads(fr.evaluate("localStorage.getItem('rp_display_v1')"))['thrStep'] == 7
    assert fr.evaluate("document.getElementById('thr-v').textContent") == '500 m sol'
    fr.evaluate("unChoose('ft')")
    pg.wait_for_timeout(300)
    assert ticks() == ['0', '100', '300', '1' + NBSP + '000', '6' + NBSP + '500', '20' + NBSP + '000']
    assert fr.evaluate("document.getElementById('thr-range').max") == '12' and fr.evaluate("document.getElementById('thr-v').textContent") == '1' + NBSP + '500 ft sol'
    fr.evaluate("setLang('en')")
    pg.wait_for_timeout(300)
    assert fr.evaluate("document.getElementById('thr-v').textContent") == '1,500 ft AGL'
    assert fr.evaluate("Math.abs(__RP.thrH() - 1500 * FT_M) < 1e-9")
    fr.evaluate("setLang('fr'); unChoose('m')")
    # le dernier rang offert : le premier qui atteint le plus grand plafond connu ; sans plafond connu, le rang 12 ; jamais moins que le rang 12 (6 000 m ; 20 000 ft)
    top = lambda items: (setup(fr, items), fr.evaluate("__RP.thrTop()"))[1]
    assert top([sym(0, 'sa-8'), sym(1, 'sa-5', *east(fr, T_LAT, T_LON, 1))]) == 18                       # 40 000 m : au-delà du dernier rang (30 000 m), le dernier rang
    assert top([sym(0, 'stinger')]) == 12 and top([sym(0, 'stinger'), sym(1, 'sa-19', *east(fr, T_LAT, T_LON, 1))]) == 12
    assert top([sym(0, 'sa-6')]) == 13                                                                     # 8 000 m : le rang 13 (8 000 m)
    fr.evaluate("unChoose('ft')")
    assert fr.evaluate("__RP.thrTop()") == 14                                                              # 8 000 m : 26 000 ft n'y atteint pas, 33 000 ft si
    for items, want in (([sym(0, 'stinger')], 12), ([sym(0, 'sa-19')], 12), ([sym(0, 'sa-8')], 12), ([sym(0, 'sa-5')], 18)):                  # en ft aussi
        assert top(items) == want
    assert fr.evaluate("[thrStepM(12), thrSteps()[12]]") == [20000 * fr.evaluate("FT_M"), 20000]
    fr.evaluate("unChoose('m')")
    # le rang gardé n'est pas réécrit quand il dépasse : la hauteur est celle du dernier rang offert
    fr.evaluate("DISP.thrStep = 15; saveDisplay();")
    setup(fr, [sym(0, 'stinger')])
    assert fr.evaluate("[DISP.thrStep, __RP.thrRank(), __RP.thrH()]") == [15, 12, 6000]
    assert json.loads(fr.evaluate("localStorage.getItem('rp_display_v1')"))['thrStep'] == 15
    assert pg.errs == []
    pg.context.close()


@needs_pw
def test_display_settings_are_read_back_at_the_next_opening(browser):
    pg, fr = open_rp(browser)
    setup(fr, [sym(0, 'sa-8')])
    set_rank(fr, pg, 5)
    display(fr, pg, True)
    fr.evaluate("document.querySelector('#dsp-panel [data-k=threats]').click()")
    pg.wait_for_timeout(300)
    saved = fr.evaluate("Object.fromEntries(Object.entries(localStorage))")
    pg.context.close()
    pg2, fr2 = open_rp(browser, seed=saved)
    assert fr2.evaluate("[DISP.threats, DISP.thrStep]") == [False, 5]
    pg2.context.close()


@needs_pw
def test_unticking_removes_the_panes_content_the_zone_and_the_box(browser):
    pg, fr = open_rp(browser)
    setup(fr, [sym(0, 'sa-8', name='SA-8')], route_over_the_crest(fr))
    fr.wait_for_function("__RP.thr.halo.getLayers().length === 1", timeout=20000)
    view_threat(fr, pg)
    assert fr.evaluate("document.querySelectorAll('.leaflet-threats-pane path').length") == 2 and fr.evaluate("!document.getElementById('rp-thr').hidden")
    display(fr, pg, True)
    fr.evaluate("document.querySelector('#dsp-panel [data-k=threats]').click()")
    pg.wait_for_timeout(500)
    display(fr, pg, False)
    assert fr.evaluate("""({ zone: __RP.thr.zone, circles: __RP.thr.circ.getLayers().length, halo: __RP.thr.halo.getLayers().length, hidden: document.getElementById('rp-thr').hidden,
        tiles: document.querySelectorAll('.leaflet-threats-pane canvas').length, paths: document.querySelectorAll('.leaflet-threats-pane path, .leaflet-thrroute-pane path').length,
        grids: __RP.thr.grids.size, row: !!document.querySelector('#nav-body tr.thr') })""") == {'zone': None, 'circles': 0, 'halo': 0, 'hidden': True, 'tiles': 0, 'paths': 0, 'grids': 0, 'row': False}
    display(fr, pg, True)
    fr.evaluate("document.querySelector('#dsp-panel [data-k=threats]').click()")
    pg.wait_for_timeout(500)
    ready(fr)
    assert fr.evaluate("__RP.thr.circ.getLayers().length") == 2 and fr.evaluate("!document.getElementById('rp-thr').hidden")
    pg.context.close()


@needs_pw
def test_circles_are_drawn_by_kind(browser):
    pg, fr = open_rp(browser)
    setup(fr, [sym(0, 'sa-6'), sym(1, '1l13', *east(fr, T_LAT, T_LON, 40), kind='radar'), sym(2, 'bofors-40', *east(fr, T_LAT, T_LON, 80), kind='aaa'),
               sym(3, 'sa-6', side='F', lat=T_LAT + 0.1)])
    c = fr.evaluate("__RP.thr.circ.getLayers().map(l => ({ r: l.getRadius(), w: l.options.weight, o: l.options.opacity, d: l.options.dashArray || null, c: l.options.color, f: l.options.fill, p: l.options.pane, i: l.options.interactive }))")
    assert c == [{'r': 70000, 'w': 1.2, 'o': 0.8, 'd': '6 6', 'c': '#c8102e', 'f': False, 'p': 'threats', 'i': False},
                 {'r': 25000, 'w': 1.6, 'o': 1, 'd': None, 'c': '#c8102e', 'f': False, 'p': 'threats', 'i': False},
                 {'r': 300000, 'w': 1.6, 'o': 1, 'd': None, 'c': '#c8102e', 'f': False, 'p': 'threats', 'i': False},      # le radar : sa détection en trait plein
                 {'r': 2000, 'w': 1.6, 'o': 1, 'd': None, 'c': '#c8102e', 'f': False, 'p': 'threats', 'i': False}]     # Bofors : détection nulle, pas de tireté ; l'ami : rien
    pg.context.close()


# ---------- sans relief ----------
@needs_pw
def test_theatre_without_relief_has_the_circles_only(browser):
    pg, fr = open_rp(browser)
    setup(fr, [sym(0, 'sa-6')], wait=False)
    fr.evaluate("(id) => { const s = document.getElementById('theatre'); s.value = id; s.dispatchEvent(new Event('change', { bubbles: true })); }", 'Nevada')
    pg.wait_for_timeout(1200)
    n0 = len([u for u in pg.bench.log if '/relief/' in u])
    state = fr.evaluate("""({ state: __RP.thr.state, circles: __RP.thr.circ.getLayers().length, zone: __RP.thr.zone, grids: __RP.thr.grids.size, range: !!document.getElementById('thr-range'),
        src: document.querySelector('#rp-thr .thr-src').textContent, grid: document.querySelectorAll('.leaflet-threats-pane .leaflet-layer').length, toasts: document.querySelectorAll('.toast, .mp-toast').length })""")
    assert state['state'] == 'none' and state['circles'] == 2 and state['zone'] is None and state['grids'] == 0 and state['range'] is False and state['grid'] == 0
    assert state['src'] == 'sans relief : portées seules'
    assert fr.evaluate("document.querySelectorAll('#rp-thr .thr-sw').length") == 2                              # la légende des seuls cercles
    assert not [u for u in pg.bench.log if 'Nevada' in u]
    fr.evaluate("setLang('en')")
    pg.wait_for_timeout(300)
    assert fr.evaluate("document.querySelector('#rp-thr .thr-src').textContent") == 'no relief: ranges only'
    assert pg.errs == []
    pg.context.close()


@needs_pw
def test_failed_description_has_the_circles_only_and_no_toast_of_its_own(browser):
    pg, fr = open_rp(browser, doc=False)
    fr.evaluate("window.__toasts = []; { const o = window.showToast; window.showToast = function (m, op) { window.__toasts.push(String(m)); return o.apply(this, arguments); }; } 0")
    setup(fr, [sym(0, 'sa-6')], wait=False)
    fr.wait_for_function("__RP.thr.state === 'err'", timeout=15000)
    assert fr.evaluate("document.querySelector('#rp-thr .thr-src').textContent") == 'relief indisponible : portées seules'
    assert fr.evaluate("[__RP.thr.circ.getLayers().length, __RP.thr.zone, __RP.thr.grids.size, !!document.getElementById('thr-range')]") == [2, None, 0, False]
    assert fr.evaluate("__toasts") == []                                                                         # la case Relief n'est pas cochée : aucun toast
    pg.context.close()


# ---------- le cartouche ----------
@needs_pw
def test_box_desktop_layout_and_hidden_in_draw_ruler_and_export_modes(browser):
    pg, fr = open_rp(browser)
    assert fr.evaluate("document.getElementById('rp-thr').hidden") is True                                      # aucune menace active
    setup(fr, [sym(0, 'sa-8')])
    box = fr.evaluate("""(() => { const b = document.getElementById('rp-thr'), r = b.getBoundingClientRect(), m = document.getElementById('map').getBoundingClientRect(), cs = getComputedStyle(b);
        return { hidden: b.hidden, left: Math.round(r.left - m.left), bottom: Math.round(m.bottom - r.bottom), bg: cs.backgroundColor, color: cs.color, font: cs.fontFamily.slice(0, 6), z: cs.zIndex,
        title: b.querySelector('.thr-t').textContent, src: b.querySelector('.thr-src').textContent, label: b.querySelector('label').textContent, val: b.querySelector('#thr-v').textContent,
        accent: getComputedStyle(b.querySelector('input')).accentColor, min: b.querySelector('input').min, max: b.querySelector('input').max, step: b.querySelector('input').step,
        small: Array.from(b.querySelectorAll('*')).filter(e => e.children.length === 0 && e.textContent.trim() && parseFloat(getComputedStyle(e).fontSize) < 10).length,
        legend: Array.from(b.querySelectorAll('.thr-leg > span')).map(e => e.textContent), parent: b.parentNode.id, mapw: m.width }; })()""")
    assert box['hidden'] is False and box['parent'] == 'map' and box['mapw'] >= 760 and box['left'] <= 12 and box['z'] == '500'
    assert box['bg'] == 'rgba(26, 28, 20, 0.92)' and box['color'] == 'rgb(232, 220, 184)' and box['font'] == 'Oswald'
    assert box['title'] == 'MENACES' and box['src'] == 'relief DCS · pydcs' and box['label'] == 'Hauteur vérifiée' and box['val'] == '30 m sol'
    assert (box['min'], box['max'], box['step']) == ('0', '12', '1') and box['small'] == 0 and box['accent'] != 'auto'
    assert box['legend'] == ['vu à 30 m du sol, à portée de tir', 'portée de tir', 'détection', 'route vue, à son altitude prévue']
    # chaque repère est sous son cran
    ok = fr.evaluate(THUMB_JS + """(() => { const rg = document.getElementById('thr-range'), r = rg.getBoundingClientRect(), max = +rg.max, th = thumbW();
        return Array.from(document.querySelectorAll('#rp-thr .thr-tk')).map((e, i) => { const k = [0, 2, 4, 6, 9, 12][i], c = e.getBoundingClientRect(), want = r.left + th / 2 + (r.width - th) * k / max;
          return Math.abs((c.left + c.width / 2) - want) < 1.5 && c.top >= r.bottom - 6; }); })()""")
    assert all(ok) and len(ok) == 6
    assert fr.evaluate(THUMB_JS + "[thumbW(), getComputedStyle(document.getElementById('thr-range')).appearance]") == [16, 'none']
    rp = (ROOT / 'dist' / 'dcs_route_planner.html').read_text(encoding='utf-8')
    assert re.search(r'#rp-thr input\[type="range"\]::-moz-range-thumb \{[^}]*appearance: none;[^}]*width: 16px;', rp)       # Firefox : lu dans la source, Chromium ignore ce pseudo-élément
    fr.evaluate("setLang('en')")
    pg.wait_for_timeout(200)
    assert fr.evaluate("[document.querySelector('#rp-thr .thr-t').textContent, document.querySelector('#rp-thr label').textContent, document.getElementById('thr-v').textContent]") == ['THREATS', 'Checked height', '30 m AGL']
    fr.evaluate("setLang('fr')")
    # mode Dessin, mode Règle : caché ; le retour le rend
    for mode in ('draw', 'ruler'):
        fr.evaluate("(m) => setTapMode(m)", mode)
        assert fr.evaluate("document.getElementById('rp-thr').hidden") is True, mode
        assert fr.evaluate("document.querySelector('.leaflet-threats-pane') && true")
    fr.evaluate("setTapMode('read')")
    assert fr.evaluate("document.getElementById('rp-thr').hidden") is False
    fr.evaluate("expOpen()")
    assert fr.evaluate("document.getElementById('rp-thr').hidden") is True
    fr.evaluate("expClose()")
    assert fr.evaluate("document.getElementById('rp-thr').hidden") is False
    # les gestes ne passent pas à la carte
    fr.evaluate("window.__clicks = 0; __RP.map.on('click mousedown', () => { window.__clicks++; });")
    off = pg.evaluate("(() => { const f = document.querySelector('iframe#iframe-rp, iframe[name=iframe-rp]').getBoundingClientRect(); return [f.left, f.top]; })()")
    inr = fr.evaluate("(() => { const r = document.querySelector('#rp-thr .thr-t').getBoundingClientRect(); return [r.left + 4, r.top + 4]; })()")
    pg.mouse.click(off[0] + inr[0], off[1] + inr[1])
    pg.wait_for_timeout(200)
    assert fr.evaluate("window.__clicks") == 0
    # l'image exportée l'exclut
    fr.evaluate("""window.__ig = null; { const o = window.html2canvas; window.html2canvas = (el, opts) => { window.__ig = opts.ignoreElements; return o(el, opts); }; } 0""")
    fr.evaluate("expShoot({ x: 0, y: 0, w: 300, h: 200 }).catch(() => 0)")
    pg.wait_for_timeout(300)
    assert fr.evaluate("window.__ig(document.getElementById('rp-thr'))") is True and fr.evaluate("window.__ig(document.getElementById('map'))") is False
    assert pg.errs == []
    pg.context.close()


@needs_pw
def test_ticks_do_not_overlap_at_760_and_at_the_last_ranks_12_14_and_18(browser):
    pg, fr = open_rp(browser, w=780, h=800)
    assert 760 <= fr.evaluate("document.getElementById('map').clientWidth") <= 800
    for items, top, ranks in (([sym(0, 'stinger')], 12, [0, 2, 4, 6, 9, 12]), ([sym(0, 'sa-6')], 14, [0, 2, 4, 6, 9, 14]), ([sym(0, 'sa-5')], 18, [0, 2, 4, 6, 9, 18])):
        setup(fr, items)
        assert fr.evaluate("__RP.thrTop()") == top
        for unit in ('m', 'ft'):
            fr.evaluate("(u) => unChoose(u === 'm' ? 'm' : 'ft')", unit)
            pg.wait_for_timeout(200)
            boxes = fr.evaluate("Array.from(document.querySelectorAll('#rp-thr .thr-tk')).map(e => { const r = e.getBoundingClientRect(); return [r.left, r.right, r.width]; })")
            assert len(boxes) == len(ranks), (top, unit)
            assert fr.evaluate("Math.round(document.getElementById('rp-thr').getBoundingClientRect().width)") == 280
            for a, b in zip(boxes, boxes[1:]):
                assert a[1] <= b[0] - 2, (top, unit, a, b)
            r = fr.evaluate("(() => { const b = document.getElementById('rp-thr').getBoundingClientRect(); return [b.left, b.right]; })()")
            assert boxes[0][0] >= r[0] - 1 and boxes[-1][1] <= r[1] + 1
    pg.context.close()


@needs_pw
def test_box_on_a_phone_is_a_pill_with_two_44px_buttons(browser):
    pg, fr = open_rp(browser, w=412, h=860)
    setup(fr, [sym(0, 'sa-8')])
    info = lambda: fr.evaluate("""(() => { const b = document.getElementById('rp-thr'), r = b.getBoundingClientRect(), bs = Array.from(b.querySelectorAll('.thr-b'));
        return { h: Math.round(r.height), pill: b.classList.contains('thr-pill'), mapw: document.getElementById('map').getBoundingClientRect().width, t: b.querySelector('.thr-t').textContent, v: b.querySelector('.thr-v').textContent,
          btn: bs.map(x => { const q = x.getBoundingClientRect(); return [Math.round(q.width), Math.round(q.height), x.getAttribute('aria-label'), x.textContent, x.disabled]; }), range: !!document.getElementById('thr-range'), step: DISP.thrStep }; })()""")
    i = info()
    assert i['pill'] and i['h'] == 44 and i['mapw'] < 760 and i['t'] == 'MENACES' and i['v'] == '30 m sol' and i['range'] is False
    # la pastille part repliée : « ± » seul, de 44 × 44 px ; on la déplie d'abord, puis « − » et « + » se mesurent comme à la base
    assert fr.evaluate("(() => { const f = document.querySelector('#rp-thr .thr-fold'), r = f.getBoundingClientRect(); return [f.textContent, f.getAttribute('aria-expanded'), Math.round(r.width), Math.round(r.height)]; })()") == ['±', 'false', 44, 44]
    assert fr.evaluate("Array.from(document.querySelectorAll('#rp-thr .thr-b')).every(e => getComputedStyle(e).display === 'none')")
    fr.evaluate("document.querySelector('#rp-thr .thr-fold').click()")
    assert fr.evaluate("(() => { const f = document.querySelector('#rp-thr .thr-fold'), r = f.getBoundingClientRect(); return [f.textContent, f.getAttribute('aria-expanded'), Math.round(r.width), Math.round(r.height)]; })()") == ['‹', 'true', 44, 44]
    assert info()['btn'] == [[44, 44, 'Plus bas', '−', False], [44, 44, 'Plus haut', '+', False]]
    assert fr.evaluate("""(() => { const b = document.getElementById('rp-thr'), r = b.getBoundingClientRect(), cs = getComputedStyle(b);
        return parseFloat(cs.borderTopWidth) + parseFloat(cs.borderBottomWidth) + parseFloat(cs.borderRightWidth) === 0 && Array.from(b.querySelectorAll('.thr-b')).every(x => { const q = x.getBoundingClientRect();
          return q.top >= r.top && q.bottom <= r.bottom && q.right <= r.right && q.height === 44 && r.height === 44; }); })()""")
    fr.evaluate("document.querySelector('#rp-thr .thr-b[data-d=\"1\"]').click()")
    assert info()['step'] == 3 and info()['v'] == '60 m sol'
    fr.evaluate("document.querySelector('#rp-thr .thr-b[data-d=\"-1\"]').click(); document.querySelector('#rp-thr .thr-b[data-d=\"-1\"]').click(); document.querySelector('#rp-thr .thr-b[data-d=\"-1\"]').click()")
    i = info()
    assert i['step'] == 0 and i['v'] == '0 m sol' and [b[4] for b in i['btn']] == [True, False]                  # grisé au bas bout
    fr.evaluate("for (let k = 0; k < 20; k++) document.querySelector('#rp-thr .thr-b[data-d=\"1\"]').click()")
    i = info()
    assert i['step'] == 12 and i['v'] == '6' + NBSP + '000 m sol' and [b[4] for b in i['btn']] == [False, True]    # grisé au haut bout (plafond 5 100 m)
    fr.evaluate("setLang('en')")
    pg.wait_for_timeout(200)
    assert [b[2] for b in info()['btn']] == ['Lower', 'Higher']
    # un vrai toucher sur « + » : le rang monte, la carte ne reçoit rien
    fr.evaluate("DISP.thrStep = 4; saveDisplay(); thrBoxRender(); thrBoxValue(); window.__taps = 0; __RP.map.on('click mousedown', () => { window.__taps++; });")
    pg.wait_for_timeout(200)
    off = pg.evaluate("(() => { const f = document.getElementById('iframe-rp').getBoundingClientRect(); return [f.left, f.top]; })()")
    bt = fr.evaluate("(() => { const r = document.querySelector('#rp-thr .thr-b[data-d=\"1\"]').getBoundingClientRect(); return [r.left + r.width / 2, r.top + r.height / 2]; })()")
    pg.touchscreen.tap(off[0] + bt[0], off[1] + bt[1])
    pg.wait_for_timeout(300)
    assert fr.evaluate("DISP.thrStep") == 5 and fr.evaluate("window.__taps") == 0
    assert pg.errs == []
    pg.context.close()


# ---------- le Worker ----------
CHECKSUM = """() => { const g = Array.from(__RP.thr.grids.values())[0]; let s1 = 0, n = 0, inf = 0, mx = 0;
    for (let i = 0; i < g.hv.length; i++) { const v = g.hv[i]; if (v === Infinity) inf++; else { s1 += v * (1 + (i % 7)); n++; if (v > mx) mx = v; } }
    return { s1: s1, n: n, inf: inf, mx: mx, worker: g.worker, z: g.z, side: g.side }; }"""


@needs_pw
def test_the_grid_is_the_same_with_or_without_a_worker(browser):
    pg, fr = open_rp(browser)
    setup(fr, [sym(0, 'sa-8')])
    a = fr.evaluate(CHECKSUM)
    assert a['worker'] is True
    both = fr.evaluate("""async ([la, lo]) => { const w = await __RP.thrProbe('sa-8', la, lo, false), p = await __RP.thrProbe('sa-8', la, lo, true); let diff = 0;
        for (let i = 0; i < w.hv.length; i++) if (w.hv[i] !== p.hv[i]) diff++;
        return { diff: diff, w: w.worker, p: p.worker, len: w.hv.length, wms: w.calcMs, pms: p.calcMs }; }""", [T_LAT, T_LON])
    assert both['diff'] == 0 and both['w'] is True and both['p'] is False and both['len'] == a['side'] ** 2
    pg.context.close()
    pg2, fr2 = open_rp(browser, init='delete window.Worker')                                   # le Worker retiré avant l'ouverture
    assert fr2.evaluate("typeof Worker") == 'undefined'
    setup(fr2, [sym(0, 'sa-8')])
    b = fr2.evaluate(CHECKSUM)
    assert b['worker'] is False and {k: b[k] for k in ('s1', 'n', 'inf', 'mx', 'z', 'side')} == {k: a[k] for k in ('s1', 'n', 'inf', 'mx', 'z', 'side')}
    view_threat(fr2, pg2)
    assert tile_alpha(fr2, 70, 128) == 110
    assert pg2.errs == []
    pg2.context.close()


@needs_pw
def test_a_worker_that_fails_falls_back_to_the_page(browser):
    pg, fr = open_rp(browser, init="window.Worker = function () { throw new Error('no worker'); }")
    setup(fr, [sym(0, 'sa-8')])
    assert fr.evaluate("Array.from(__RP.thr.grids.values())[0].worker") is False and hv_at(fr, -30) == 0
    pg.context.close()


# ---------- le Field Manual ----------
def test_field_manual_page_section_and_table():
    fm = (ROOT / 'dist' / 'dcs_field_manual.html').read_text(encoding='utf-8')
    rp = fm[fm.index('<section id="page-rp"'):fm.index('<!-- /page-rp -->')]
    h = re.search(r'<h4 class="lang-block" data-lang="fr">Les menaces</h4>\s*<h4 class="lang-block" data-lang="en">Threats</h4>', rp)
    assert h and rp.index('Le relief') < h.start() < rp.index('La fiche d’un aérodrome')
    sec = rp[h.start():rp.index('La fiche d’un aérodrome')]
    for needle in ('Goldwolf', 'pydcs', 'DCS Threats Guide', 'à plat', 'fouillis du sol', '10 m', '5 m', '2 m', 'halo jaune', 'Navigation', 'hauteur vérifiée', 'réglages d’écran', 'Un théâtre sans relief'):
        assert needle in sec, needle
    for needle in ('Goldwolf', 'pydcs', 'DCS Threats Guide', 'flat', 'ground clutter', '10 m', 'yellow halo', 'checked height', 'screen settings', 'A theatre without relief', 'Draw'):
        assert needle in sec, needle
    tables = re.findall(r'<div class="fm-tbl-wrap lang-block" data-lang="(fr|en)"[^>]*>\s*<table class="fm-tbl">(.*?)</table></div>', sec, re.S)
    assert [t[0] for t in tables] == ['fr', 'en']
    data = json.loads((ROOT / 'data' / 'threats.json').read_text(encoding='utf-8'))['systems']
    for lang, body in tables:
        rows = re.findall(r'<tr><th scope="row" class="s">(.*?)</th><td>(.*?)</td><td class="n">(.*?)</td><td class="n">(.*?)</td><td class="n">(.*?)</td><td>(.*?)</td></tr>', body)
        assert len(rows) == 57
        head = re.findall(r'<th scope="col"[^>]*>(.*?)</th>', body)
        assert head == (['Système', 'Nature', 'Tir (km)', 'Détection (km)', 'Plafond (m)', 'Capteur'] if lang == 'fr' else ['System', 'Kind', 'Fire (km)', 'Detection (km)', 'Ceiling (m)', 'Sensor'])
        for r, s in zip(rows, data):
            assert r[0].replace('&amp;', '&') == s['name_' + lang] and r[1] == {'sam': 'SAM', 'aaa': 'AAA', 'radar': 'Radar'}[s['kind']]
            dec = ',' if lang == 'fr' else '.'
            want = lambda m: '—' if not m else ('%.1f' % (m / 1000)).replace('.', dec)
            assert (r[2], r[3]) == (want(s['fire_m']), want(s['detect_m']))
            sep = NBSP if lang == 'fr' else ','
            assert r[4] == ('—' if s['ceiling_m'] is None else format(s['ceiling_m'], ',').replace(',', sep))
    by = {r[0]: r for r in re.findall(r'<tr><th scope="row" class="s">(.*?)</th><td>(.*?)</td><td class="n">(.*?)</td><td class="n">(.*?)</td><td class="n">(.*?)</td><td>(.*?)</td></tr>', tables[0][1], re.S)}
    assert by['SA-6 Kub Gainful'][2:5] == ('25,0', '70,0', '8' + NBSP + '000')
    assert by['1L13 Nebo Box Spring'][2] == '—' and by['M48 Chaparral'][4] == '3' + NBSP + '600'
    assert 'overflow-x: auto' in fm[fm.index('.fm-tbl-wrap {'):fm.index('.fm-tbl-wrap {') + 200]


def test_field_manual_rp_plate_does_not_show_the_threats_and_the_page_holds_no_data_marker():
    fm = (ROOT / 'dist' / 'dcs_field_manual.html').read_text(encoding='utf-8')
    rp = fm[fm.index('<section id="page-rp"'):fm.index('<!-- /page-rp -->')]
    figs = [hashlib.sha256(re.search(r'<svg class="%s".*?</svg>' % c, rp, re.S).group(0).encode()).hexdigest() for c in ('pl-wide', 'pl-tall')]
    assert figs == PLATE_RP_BASE, figs                                         # les deux figures du RP : celles du FM du socle 8fb4e66, à l'octet
    for p in (ROOT / 'dist').glob('*.html'):
        assert 'dcs-threats-v1' not in p.read_text(encoding='utf-8'), p.name
    rp = (ROOT / 'dist' / 'dcs_route_planner.html').read_text(encoding='utf-8')
    d = json.loads((ROOT / 'data' / 'threats.json').read_text(encoding='utf-8'))
    assert rp.count('const THREATS = ') == 1
    emb = json.loads(re.search(r'const THREATS = (\{.*?\});\n', rp).group(1))
    assert list(emb) == ['sensor_height_m', 'systems'] and len(emb['systems']) == 57 and emb['sensor_height_m'] == d['sensor_height_m']
    assert all(list(s) == ['id', 'name_fr', 'name_en', 'kind', 'sensor', 'fire_m', 'detect_m', 'ceiling_m'] for s in emb['systems'])
    assert not re.search(r'goldwolf|whiskey|"gap"|gap_threshold', re.search(r'const THREATS = .*?;\n', rp).group(0), re.I)


def test_dictionaries_hold_every_new_key_in_both_languages():
    rp = (ROOT / 'dist' / 'dcs_route_planner.html').read_text(encoding='utf-8')
    keys = ['dsp.threats', 'dsp.threats.tip', 'dr.f.threat', 'thr.none', 'thr.unknown', 'thr.p.fire', 'thr.p.det', 'thr.p.tail', 'thr.other', 'thr.ceil.none', 'thr.sensor.search', 'thr.sensor.fire-control', 'thr.sensor.shooter',
            'cf.threat', 'thr.title', 'thr.src.relief', 'thr.src.none', 'thr.src.err', 'thr.h', 'thr.h.v', 'thr.leg.zone', 'thr.leg.fire', 'thr.leg.det', 'thr.leg.route', 'thr.lower', 'thr.higher', 'nav.thr', 'nav.thr.item', 'thr.ceil']
    for k in keys:
        assert len(re.findall(r"^    '%s': '" % re.escape(k), rp, re.M)) == 2, k


# ====================== reprises de la réception (addendum 2) ======================
RELIEF_CREDIT_FR = 'Relief : DCS World, Eagle Dynamics SA (usage non commercial)'


def attrib(fr):
    return fr.evaluate("document.querySelector('.leaflet-control-attribution').textContent")


@needs_pw
def test_relief_credit_follows_the_zone_even_with_relief_unticked_and_is_shown_once(browser):
    pg, fr = open_rp(browser)
    assert fr.evaluate("DISP.relief") is False and RELIEF_CREDIT_FR not in attrib(fr)
    setup(fr, [sym(0, 'sa-8')])
    assert fr.evaluate("__RP.thr.zone.options.attribution") == RELIEF_CREDIT_FR
    assert attrib(fr).count(RELIEF_CREDIT_FR) == 1 and RELIEF_CREDIT_FR in fr.evaluate("expAttribution()")      # sur la carte et dans l'image exportée
    fr.evaluate("setLang('en')")
    pg.wait_for_timeout(300)
    assert attrib(fr).count('Relief: DCS World, Eagle Dynamics SA (non-commercial use)') == 1 and 'usage non' not in attrib(fr)
    assert fr.evaluate("__RP.thr.zone.options.attribution") == 'Relief: DCS World, Eagle Dynamics SA (non-commercial use)'
    fr.evaluate("setLang('fr')")
    # le Relief coché en plus : une seule mention
    display(fr, pg, True)
    fr.evaluate("document.querySelector('#dsp-panel [data-k=relief]').click()")
    fr.wait_for_function("DISP.relief === true && !!__RP.reliefLayer", timeout=15000)
    display(fr, pg, False)
    assert attrib(fr).count(RELIEF_CREDIT_FR) == 1 and fr.evaluate("expAttribution()").count(RELIEF_CREDIT_FR) == 1
    # la zone retirée : la mention reste pour le Relief ; Relief décoché aussi, elle part
    display(fr, pg, True)
    fr.evaluate("document.querySelector('#dsp-panel [data-k=threats]').click()")
    pg.wait_for_timeout(400)
    assert attrib(fr).count(RELIEF_CREDIT_FR) == 1
    fr.evaluate("document.querySelector('#dsp-panel [data-k=relief]').click()")
    pg.wait_for_timeout(400)
    display(fr, pg, False)
    assert RELIEF_CREDIT_FR not in attrib(fr)
    # la zone seule, puis retirée : la mention part
    display(fr, pg, True)
    fr.evaluate("document.querySelector('#dsp-panel [data-k=threats]').click()")
    fr.wait_for_function("!!__RP.thr.zone", timeout=15000)
    assert RELIEF_CREDIT_FR in attrib(fr)
    fr.evaluate("document.querySelector('#dsp-panel [data-k=threats]').click()")
    pg.wait_for_timeout(400)
    assert RELIEF_CREDIT_FR not in attrib(fr)
    assert pg.errs == []
    pg.context.close()


@needs_pw
def test_no_grid_that_left_the_set_is_kept_anywhere(browser):
    pg, fr = open_rp(browser)
    la, lo = east(fr, T_LAT, T_LON, 4)
    setup(fr, [sym(0, 'sa-8'), sym(1, 'sa-8', la, lo)])
    assert fr.evaluate("__RP.thr.paint.list.length") == 2
    fr.evaluate("CF_LAYERS[0].items.pop(); renderAll();")                      # une menace s'en va : sa grille ne reste dans aucune structure
    pg.wait_for_timeout(400)
    assert fr.evaluate("__RP.thr.grids.size") == 1 and fr.evaluate("__RP.thr.paint.list.every(g => Array.from(__RP.thr.grids.values()).includes(g))")
    assert fr.evaluate("__RP.thr.paint.list.length") == 1
    display(fr, pg, True)
    fr.evaluate("document.querySelector('#dsp-panel [data-k=threats]').click()")
    pg.wait_for_timeout(500)
    assert fr.evaluate("[__RP.thr.grids.size, __RP.thr.paint.list.length, __RP.thr.paint.H, __RP.thr.zone]") == [0, 0, 0, None]
    pg.context.close()


NO_WORKER = 'delete window.Worker'
FAIL_ONCE = """(function () { /* le calcul de la page lève pour la portée de 25 000 m (un SA-6) */
  const t = setInterval(function () { if (typeof window.thrCalc === 'function' && !window.__thrOrig) { window.__thrOrig = window.thrCalc; window.thrCalc = function (m) { if (m.R === 25000) throw new Error('boom'); return window.__thrOrig(m); }; clearInterval(t); } }, 5);
})();"""


@needs_pw
def test_a_page_calculation_that_throws_marks_the_key_bad_and_leaves_no_job(browser):
    pg, fr = open_rp(browser, init=NO_WORKER + ';' + FAIL_ONCE)
    fr.wait_for_function("!!window.__thrOrig", timeout=10000)
    setup(fr, [sym(0, 'sa-6')], wait=False)
    fr.wait_for_function("__RP.thr.bad.size === 1 && __RP.thr.jobs.size === 0", timeout=15000)
    assert fr.evaluate("[__RP.thr.grids.size, __RP.thr.zone, __RP.thr.circ.getLayers().length]") == [0, None, 2]       # les cercles restent
    pg.context.close()


@needs_pw
def test_route_is_judged_when_no_calculation_runs_and_a_failed_threat_is_only_left_out(browser):
    pg, fr = open_rp(browser, init=NO_WORKER + ';' + FAIL_ONCE)
    fr.wait_for_function("!!window.__thrOrig", timeout=10000)
    la, lo = east(fr, T_LAT, T_LON, 0.2)
    items = [sym(0, 'sa-8', name='SA-8'), sym(1, 'sa-6', la, lo, name='SA-6')]
    pts = route_over_the_crest(fr)
    setup(fr, items, pts, wait=False)
    fr.wait_for_function("__RP.thr.bad.size === 1 && __RP.thr.jobs.size === 0 && __RP.thr.grids.size === 1 && !!__RP.thr.seen", timeout=20000)
    g = grid(fr)
    seen = fr.evaluate("__RP.thr.seen")
    assert [x['name'] for x in seen['1']] == ['SA-8'] and abs(seen['1'][0]['km'] - analytic_seen_km(g, 3.0)) <= 0.2
    assert fr.evaluate("__RP.thr.halo.getLayers().length") == 1 and fr.evaluate("!!document.querySelector('#nav-body tr.thr')")
    pg.context.close()


def tile_xy(url):
    m = re.search(r'/Syria/elevation/(\d+)/(\d+)/(\d+)\.png', url)
    return tuple(int(v) for v in m.groups()) if m else None


def bounds_tiles(z=11):
    n = 2 ** z
    xs = [(BOUNDS[0][1] + 180) / 360 * n, (BOUNDS[1][1] + 180) / 360 * n]
    ys = [(1 - math.asinh(math.tan(math.radians(la))) / math.pi) / 2 * n for la in (BOUNDS[1][0], BOUNDS[0][0])]
    return int(xs[0]), int(xs[1]), int(ys[0]), int(ys[1])


@needs_pw
def test_no_tile_is_requested_outside_the_bounds_for_a_route_or_a_grid_and_ground_there_is_zero(browser):
    pg, fr = open_rp(browser)
    x0, x1, y0, y1 = bounds_tiles()
    lon_edge = BOUNDS[0][1] + 0.01                                             # une menace à 0,9 km du bord ouest de la description
    setup(fr, [sym(0, 'sa-8', lat=T_LAT, lon=lon_edge)])
    g = fr.evaluate("""() => { const q = Array.from(__RP.thr.grids.values())[0]; const row = q.K * q.side;
        return { west: q.g[row + q.K - 100], gs: q.gs, side: q.side, K: q.K, hv: q.hv[row + q.K - 100], mpp: q.mpp }; }""")
    assert g['west'] == 0 and 0 < g['hv'] < 105 and g['gs'] > 0 and g['K'] * g['mpp'] > 5000          # le bord ouest de la grille est hors des bornes : 0 m
    log = [tile_xy(u) for u in pg.bench.log if tile_xy(u)]
    assert log and all(x0 <= x <= x1 and y0 <= y <= y1 for _, x, y in log), [t for t in log if not (x0 <= t[1] <= x1 and y0 <= t[2] <= y1)]
    # une route qui sort des bornes, jugée : aucune tuile nouvelle hors des bornes
    a = (T_LAT, lon_edge + 0.02)
    b = (T_LAT, BOUNDS[0][1] - 0.3)
    pts = [{'name': 'A', 'lat': a[0], 'lon': a[1], 'alt': 30, 'altRef': 'AGL'}, {'name': 'B', 'lat': b[0], 'lon': b[1], 'alt': 30, 'altRef': 'AGL'}]
    n0 = len(pg.bench.log)
    setup(fr, [sym(0, 'sa-8', lat=T_LAT, lon=lon_edge)], pts)
    pg.wait_for_timeout(1500)
    new = [tile_xy(u) for u in pg.bench.log[n0:] if tile_xy(u)]
    assert all(x0 <= x <= x1 and y0 <= y <= y1 for _, x, y in new), new
    assert fr.evaluate("__RP.thr.routeSeq") >= 1 and pg.errs == []
    pg.context.close()


STALE_WORKER = """(function () { window.__term = 0; window.__made = 0;
  window.Worker = function () { window.__made++; var self = this; this.postMessage = function () {}; this.terminate = function () { window.__term++; }; };
})();"""
WORKER_SPY = """(function () { const W = window.Worker; window.__pm = [];
  window.Worker = function (u) { const w = new W(u), p = w.postMessage.bind(w); w.postMessage = function (m, t) { window.__pm.push({ n: t ? t.length : 0, own: !!t && t[0] === m.g.buffer, len: m.g.length }); return p(m, t); }; return w; };
})();"""


@needs_pw
def test_a_stale_calculation_terminates_its_worker(browser):
    pg, fr = open_rp(browser, init=STALE_WORKER)
    setup(fr, [sym(0, 'sa-8')], wait=False)
    fr.wait_for_function("__RP.thr.jobs.size === 1 && window.__made === 1", timeout=15000)
    assert fr.evaluate("window.__term") == 0
    fr.evaluate("CF_LAYERS[0].items.length = 0; renderAll();")                 # la menace s'en va : le calcul est périmé
    pg.wait_for_timeout(400)
    assert fr.evaluate("[window.__term, __RP.thr.jobs.size, __RP.thr.grids.size]") == [1, 0, 0]
    # la clé remplacée (la menace déplacée) : le Worker du calcul périmé s'arrête aussi
    setup(fr, [sym(0, 'sa-8')], wait=False)
    fr.wait_for_function("window.__made === 2 && __RP.thr.jobs.size === 1", timeout=15000)
    la, lo = east(fr, T_LAT, T_LON, 1)
    fr.evaluate("([la, lo]) => { Object.assign(CF_LAYERS[0].items[0], { lat: la, lon: lo }); renderAll(); }", [la, lo])
    fr.wait_for_function("window.__made === 3", timeout=15000)
    assert fr.evaluate("window.__term") == 2 and fr.evaluate("__RP.thr.jobs.size") == 1
    pg.context.close()


@needs_pw
def test_the_ground_sent_to_the_worker_is_a_transferred_copy_and_the_page_keeps_its_own(browser):
    pg, fr = open_rp(browser, init=WORKER_SPY)
    setup(fr, [sym(0, 'sa-8')])
    pm = fr.evaluate("window.__pm")
    assert len(pm) == 1 and pm[0]['n'] == 1 and pm[0]['own'] is True
    kept = fr.evaluate("(() => { const q = Array.from(__RP.thr.grids.values())[0]; return [q.g.length, q.g.byteLength, q.g[q.K * q.side + q.K], q.gs, q.worker]; })()")
    assert kept[0] == pm[0]['len'] and kept[1] == 4 * kept[0] and kept[2] == kept[3] and kept[4] is True        # le sol de la page n'est pas détaché
    pg.context.close()


@needs_pw
def test_zero_detection_or_fire_has_no_part_in_the_sheet_line_and_other_kind_is_not_carried(browser):
    pg, fr = open_rp(browser)
    setup(fr, [sym(0, '', kind='aaa'), sym(1, 'sa-6', kind='aaa'), sym(2, 'sa-8', kind='aaa')], wait=False)
    fr.evaluate("delete CF_LAYERS[0].items[0].threat; drawLayers();")
    open_sheet(fr, 't0')
    pick = lambda v: fr.evaluate("(v) => { const s = document.querySelector('#dr-sheet select[data-f=threat]'); s.value = v; s.dispatchEvent(new Event('change', { bubbles: true })); }", v)
    info = lambda: fr.evaluate("document.getElementById('dr-f-threat-info').textContent")
    pick('bofors-40')
    assert info() == f'Tir 2,0 km · plafond 3{NBSP}000 m · capteur : le tireur lui-même'
    assert 'détection' not in info() and '0,0' not in info()
    fr.evaluate("setLang('en')")
    open_sheet(fr, 't0')
    assert info().startswith('Fire 2.0 km · ceiling 3,000 m') and 'detection' not in info()
    fr.evaluate("setLang('fr')")
    # un système d'une autre nature (un SA-6 sur un symbole AAA) : le symbole ne porte pas de menace ; l'option le dit, choisie
    fr.evaluate("drawLayers()")
    assert fr.evaluate("__RP.thr.act.map(a => a.it.id)") == ['t0']
    open_sheet(fr, 't1')
    o = options(fr)
    assert ['sa-6', 'SA-6 Kub Gainful (autre nature)', True] in o and sum(1 for x in o if x[2]) == 1
    assert fr.evaluate("CF_LAYERS[0].items[1].threat") == 'sa-6'
    fr.evaluate("setLang('en')")
    open_sheet(fr, 't1')
    assert ['sa-6', 'SA-6 Kub Gainful (other kind)', True] in options(fr) or any(x[2] and x[1].endswith('(other kind)') for x in options(fr))
    fr.evaluate("setLang('fr')")
    assert fr.evaluate("__RP.thr.circ.getLayers().length") == 1                 # seul le bofors se dessine
    assert pg.errs == []
    pg.context.close()


# ---------- la géométrie, oblique, minimum par pixel, sans trou, sol 0 hors bornes ----------
@needs_pw
def test_geometry_oblique_ray_behind_the_crest_at_45_degrees(browser):
    pg, fr = open_rp(browser)
    setup(fr, [sym(0, 'sa-8')])
    g = grid(fr)
    d1 = 49.5 * math.sqrt(2) * g['mpp']                                        # du centre au bord ouest de la crête, sur le rayon à 45°
    for dxy in (80, 100, 130):                                                 # sud-est, derrière la crête (x de 150 à 160 coupé entre 70 et 80 pixels du centre)
        d = math.hypot(dxy, dxy) * g['mpp']
        if d > g['R']:
            continue
        want = 105 + (CREST_M - 105) * d / d1 - 100
        got = hv_at(fr, dxy, dxy)
        assert abs(got - want) <= 25, (dxy, want, got)
    # nord-est aussi (le dessin est symétrique en y)
    d = math.hypot(90, 90) * g['mpp']
    assert abs(hv_at(fr, 90, -90) - (105 + (CREST_M - 105) * d / d1 - 100)) <= 25
    pg.context.close()


def ref_hv(g, side, K, mpp, R, zs):
    """La règle du cadrage, écrite à part : rayons du centre à chaque pixel du bord, pas de 0,5 pixel, pente maximale des échantillons précédents, minimum par pixel, voisins pour les pixels sans rayon."""
    INF = float('inf')
    hv = [INF] * (side * side)
    c = K + 0.5
    rpx = R / mpp

    def ray(ex, ey):
        dx, dy = ex + 0.5 - c, ey + 0.5 - c
        ln = math.sqrt(dx * dx + dy * dy)
        if not ln > 0:
            return
        ux, uy = dx / ln, dy / ln
        mx = min(ln, rpx) + 1e-9
        pmax = -INF
        k = 1
        while True:
            tt = k * 0.5
            if tt > mx:
                break
            idx = math.floor(c + uy * tt) * side + math.floor(c + ux * tt)
            gg, d = g[idx], tt * mpp
            h = zs + pmax * d - gg
            if not h > 0:
                h = 0
            if h < hv[idx]:
                hv[idx] = h
            sl = (gg - zs) / d
            if sl > pmax:
                pmax = sl
            k += 1
    for i in range(side):
        ray(i, 0)
        ray(i, side - 1)
    for j in range(1, side - 1):
        ray(0, j)
        ray(side - 1, j)
    fill = []
    r2 = rpx * rpx
    for j in range(side):
        for i in range(side):
            idx = j * side + i
            ddx, ddy = i + 0.5 - c, j + 0.5 - c
            if ddx * ddx + ddy * ddy > r2:
                hv[idx] = INF
                continue
            if hv[idx] != INF:
                continue
            best = INF
            for dj in (-1, 0, 1):
                for di in (-1, 0, 1):
                    jj, ii = j + dj, i + di
                    if (di == 0 and dj == 0) or not (0 <= jj < side and 0 <= ii < side):
                        continue
                    best = min(best, hv[jj * side + ii])
            if best != INF:
                fill.append((idx, best))
    for idx, v in fill:
        hv[idx] = v
    return hv


@needs_pw
def test_calculation_keeps_the_minimum_per_pixel_has_no_hole_in_the_disk_and_matches_the_rule(browser):
    import random
    rnd = random.Random(7)
    pg, fr = open_rp(browser)
    K, mpp, R, zs = 40, 30.0, 1100.0, 12.0
    side = 2 * K + 1
    g = [0.0] * (side * side)
    for _ in range(14):                                                        # des buttes aléatoires, mais toujours les mêmes
        cx, cy, r, h = rnd.randint(0, side - 1), rnd.randint(0, side - 1), rnd.randint(2, 6), rnd.randint(15, 90)
        for j in range(side):
            for i in range(side):
                if (i - cx) ** 2 + (j - cy) ** 2 <= r * r:
                    g[j * side + i] = max(g[j * side + i], float(h))
    got = fr.evaluate("(m) => { m.g = Float32Array.from(m.g); return Array.from(__RP.thrCalc(m)); }", {'g': g, 'side': side, 'K': K, 'mpp': mpp, 'R': R, 'zs': zs})
    want = ref_hv(g, side, K, mpp, R, zs)
    inf = float('inf')
    assert len(got) == len(want) == side * side
    for q, (a, b) in enumerate(zip(got, want)):
        assert (a == inf) == (b == inf) and (a == inf or abs(a - b) < 1e-3), (q, a, b)
    c, rpx = K + 0.5, R / mpp
    inside = [q for q in range(side * side) if (q % side + 0.5 - c) ** 2 + (q // side + 0.5 - c) ** 2 <= rpx * rpx]
    assert inside and all(got[q] != inf for q in inside)                      # aucun pixel du disque sans valeur
    assert all(got[q] == inf for q in range(side * side) if q not in set(inside))
    # un pixel touché par deux rayons garde le plus petit : un mur d'un pixel au centre-est ne cache pas ce qu'un autre rayon voit
    flat = [0.0] * (side * side)
    flat[K * side + K + 5] = 60.0
    h2 = fr.evaluate("(m) => { m.g = Float32Array.from(m.g); return Array.from(__RP.thrCalc(m)); }", {'g': flat, 'side': side, 'K': K, 'mpp': mpp, 'R': R, 'zs': zs})
    assert h2[K * side + K + 5] == 0 and h2[K * side + K + 8] > 0              # derrière le mur, sur l'axe : masqué
    assert h2[(K + 6) * side + K + 8] == ref_hv(flat, side, K, mpp, R, zs)[(K + 6) * side + K + 8]
    pg.context.close()


# ---------- la route mêlée : AGL → MSL ----------
def seen_mixed_km(g, alt_start_agl, alt_end_msl, west_km=3.0, east_km=7.0):
    d1 = (CREST_X0 - TCOL - 0.5) * g['mpp']
    d2 = (CREST_X1 - TCOL - 0.5) * g['mpp']
    total_m, step = (west_km + east_km) * 1000, 25.0
    ea, eb, tot = alt_start_agl + PLAIN_M, alt_end_msl, 0.0
    for i in range(int(total_m / step)):
        s = (i + 0.5) * step
        d = s - west_km * 1000
        if abs(d) > g['R']:
            continue
        alt = ea + (eb - ea) * s / total_m
        if d < d1:
            ok = alt >= PLAIN_M
        elif d < d2:
            ok = alt >= CREST_M
        else:
            ok = alt - PLAIN_M >= g['zs'] + (CREST_M - g['zs']) * d / d1 - PLAIN_M
        tot += step if ok else 0
    return tot / 1000


@needs_pw
def test_mixed_agl_to_msl_leg_is_judged_by_the_third_case_of_the_rule(browser):
    pg, fr = open_rp(browser)
    items = [sym(0, 'sa-8', name='SA-8')]
    setup(fr, items)
    g = grid(fr)
    a = east(fr, T_LAT, T_LON, -3.0)
    b = east(fr, a[0], a[1], 10.0)
    pts = [{'name': 'A', 'lat': a[0], 'lon': a[1], 'alt': 30, 'altRef': 'AGL'}, {'name': 'B', 'lat': b[0], 'lon': b[1], 'alt': 450, 'altRef': 'MSL'}]
    setup(fr, items, pts)
    fr.wait_for_function("__RP.thr.seen && !!__RP.thr.seen['1']", timeout=20000)
    km = fr.evaluate("__RP.thr.seen['1'][0].km")
    want = seen_mixed_km(g, 30, 450)
    assert 6.5 < want < 7.5 and abs(km - want) <= 0.2, (km, want)              # ni « tout en AGL » (10 km), ni « A en MSL » (le début à 30 m du niveau de la mer : masqué)


def test_field_manual_rp_threats_gives_the_checked_height_range():
    fm = (ROOT / 'dist' / 'dcs_field_manual.html').read_text(encoding='utf-8')
    rp = fm[fm.index('<section id="page-rp"'):fm.index('<!-- /page-rp -->')]
    assert 'au téléphone, c’est une pastille repliée, en bas à droite au-dessus des crédits de la carte\u202f: <strong>±</strong> y montre <strong>−</strong> et <strong>+</strong>. Elle va de 0 à 20 000 ft (6 000 m) au moins, plus haut si un système affiché a un plafond plus haut\u202f; au-dessus de son plafond, un système ne teinte plus.' in rp
    assert 'on a phone it is a folded pill at the bottom right, above the map credits: <strong>±</strong> shows <strong>−</strong> and <strong>+</strong>. It goes from 0 to 20,000 ft (6,000 m) at least, higher if a system shown has a higher ceiling; above its ceiling, a system no longer tints.' in rp


def test_field_manual_rp_threats_credits_both_guides():
    fm = (ROOT / 'dist' / 'dcs_field_manual.html').read_text(encoding='utf-8')
    rp = fm[fm.index('<section id="page-rp"'):fm.index('<!-- /page-rp -->')]
    assert 'les plafonds viennent du DCS SAM Threat Guide de [107th] Whiskey 188 (V2.1, relevé dans les fichiers du jeu) et, pour les systèmes qu’il ne couvre pas, du DCS Threats Guide de Goldwolf (le Tor M2 prend le plafond du Tor)\u202f; nous les remercions tous deux.' in rp
    assert 'the ceilings come from [107th] Whiskey 188’s DCS SAM Threat Guide (V2.1, taken from the game’s files) and, for the systems it does not cover, from Goldwolf’s DCS Threats Guide (the Tor M2 takes the Tor’s), with thanks to both.' in rp
    assert 'les plafonds viennent du DCS Threats Guide de Goldwolf, que nous remercions.' not in rp
    assert 'the ceilings come from Goldwolf’s DCS Threats Guide, with thanks.' not in rp
