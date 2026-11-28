"""Route Planner : nos captures de la carte F10 sur Syria (« Carte DCS » et « Satellite »), jouées sur le shell construit (chromium, 1 280 x 800).
Aucun réseau : les requêtes hors file:/data:/blob: sont notées puis servies (nos tuiles, les tuiles des autres théâtres) ou refusées. Les contrôles
passent par le DOM et les requêtes."""
import math
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tests'))
sys.path.insert(0, str(ROOT / 'tests' / 'fixtures' / 'rp_papier'))
from banc_attente import attendre, attendre_images, viser  # noqa: E402
import fabriquer as FAB  # noqa: E402
import test_rp_papier as TP  # noqa: E402
from test_rp_papier import PT, needs_pw, open_rp, close, set_theatre, choose, attribution  # noqa: E402,F401

browser = TP.browser
ALT = PT + 'alt-syria/'
SAT = PT + 'sat-syria/'
BOUNDS = (31.00, 32.10, 38.25, 41.15)              # sud, ouest, nord, est
MIRROR_HOST = 'https://miroir.test'
MIRROR_CFG = '{"configSchemaVersion":1,"dcs":{"url":"/dcs/{key}/{z}/{x}/{y}.png"}}'
OLYMPUS = 'https://maps.dcsolympus.com/'
ESRI = 'https://server.arcgisonline.com/'
ED_FR = 'Carte DCS © Eagle Dynamics'
ED_EN = 'DCS map © Eagle Dynamics'
TILE = FAB.png(256, 256, (40, 120, 200))
CORS = {'Access-Control-Allow-Origin': '*', 'Content-Type': 'image/png'}


def tile_box(z, x, y):
    n = 2.0 ** z
    lat = lambda yy: math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * yy / n))))
    return lat(y + 1), x / n * 360 - 180, lat(y), (x + 1) / n * 360 - 180


def inside(u):
    m = re.search(r'/(\d+)/(\d+)/(\d+)\.(?:png|webp)$', u)
    z, x, y = map(int, m.groups())
    s, w, n, e = tile_box(z, x, y)
    return 8 <= z <= 15 and s < BOUNDS[2] and n > BOUNDS[0] and w < BOUNDS[3] and e > BOUNDS[1]


def serve_tiles(pg):
    """Sert toute tuile demandée (la nôtre, celles de l'hôte, d'Olympus, d'Esri) pour que la page l'affiche ; tout est noté dans pg.bench.log."""
    base = pg.bench.handler

    def h(route):
        url = route.request.url
        if url.startswith((PT + 'alt-', PT + 'sat-', MIRROR_HOST, OLYMPUS, ESRI)):
            pg.bench.log.append(url)
            return route.fulfill(status=200, headers=CORS, body=TILE)
        return base(route)
    pg.unroute('**/*')
    pg.route('**/*', h)


def tiles_seen(fr):
    return fr.evaluate("__RP.baseLayers.reduce((n, l) => n + l.getContainer().querySelectorAll('img.leaflet-tile-loaded').length, 0)")


def pose(fr, lat, lon, z, attend=True):
    viser(fr, lat, lon, z)
    attendre_images(fr, 4)
    if attend:
        attendre(fr, "__RP.baseLayers.every(l => l.getContainer().querySelectorAll('img.leaflet-tile:not(.leaflet-tile-loaded)').length === 0) && __RP.baseLayers.some(l => l.getContainer().querySelectorAll('img.leaflet-tile-loaded').length > 0)",
                 'les tuiles de la vue chargées', lu="__RP.baseLayers.map(l => l.getContainer().querySelectorAll('img.leaflet-tile').length)", delai=20000)


@needs_pw
@pytest.mark.parametrize('mirror', [False, True])
@pytest.mark.parametrize('fond', ['dcs', 'sat'])
def test_syria_shows_only_our_tiles_in_their_zone_with_their_credit(browser, fond, mirror):
    pg, fr = open_rp(browser)
    serve_tiles(pg)
    if mirror:
        fr.evaluate("(c) => localStorage.setItem('map_layers_v1', c)", MIRROR_CFG)
        assert fr.evaluate("readMirrorUrl()") == '/dcs/{key}/{z}/{x}/{y}.png'
    assert fr.evaluate("S.theatre") == 'Syria'
    prefix, ext = (ALT, '.png') if fond == 'dcs' else (SAT, '.webp')
    # la vue du théâtre (zoom 7), puis deux vues dans l'emprise, puis une vue hors de l'emprise
    n0 = len(pg.bench.log)
    choose(fr, fond)
    pose(fr, 34.8, 35.8, 7)
    pose(fr, 33.5, 36.3, 12)
    pose(fr, 36.2, 37.2, 15)
    got = pg.bench.log[n0:]
    assert got and all(u.startswith(prefix) and u.endswith(ext) for u in got), got
    assert all(inside(u) for u in got), [u for u in got if not inside(u)]
    zs = {int(u[len(prefix):].split('/')[0]) for u in got}
    assert min(zs) == 8 and max(zs) == 15, zs
    # la couche : une seule, avec les options de la règle
    assert fr.evaluate("__RP.baseLayers.length") == 1
    o = fr.evaluate("(() => { const l = __RP.baseLayers[0], b = l.options.bounds; return [l.options.minNativeZoom, l.options.maxNativeZoom, l.options.maxZoom, !!l.options.mirrorOnly, [b[0][0], b[0][1], b[1][0], b[1][1]]]; })()")
    assert o == [8, 15, 18, False, list(BOUNDS)], o
    # hors de l'emprise : aucune demande
    n1 = len(pg.bench.log)
    pose(fr, 29.0, 45.5, 10, attend=False)
    pose(fr, 28.5, 46.0, 12, attend=False)
    assert pg.bench.log[n1:] == [], pg.bench.log[n1:]
    # ni miroir, ni Olympus, ni Esri, tout du long
    assert not [u for u in pg.bench.log if u.startswith((MIRROR_HOST, OLYMPUS, ESRI))], pg.bench.log
    assert not [u for u in pg.bench.log if '/outils/tuiles/' in u]
    # la mention, puis le changement de langue
    assert ED_FR in attribution(fr).replace(' ', ' '), attribution(fr)
    assert 'Olympus' not in attribution(fr) and 'Esri' not in attribution(fr)
    assert fr.evaluate("document.querySelector('.leaflet-control-attribution a[href=\"https://www.digitalcombatsimulator.com/\"]').textContent") == 'Eagle Dynamics'
    fr.evaluate("setLang('en'); 0")
    attendre(fr, "__RP.map.attributionControl.getContainer().textContent.indexOf('DCS map') !== -1", 'la mention en anglais', lu="__RP.map.attributionControl.getContainer().textContent")
    assert ED_EN in attribution(fr).replace(' ', ' '), attribution(fr)
    assert pg.errs == []
    close(pg)


@needs_pw
def test_the_menu_keeps_its_rows_and_the_other_theatres_are_as_before(browser):
    pg, fr = open_rp(browser)
    serve_tiles(pg)
    syria = [(r['id'], r['txt']) for r in TP.rows(fr)]
    assert [i for i, _ in syria][:3] == ['dcs', 'topo', 'sat'] or {'dcs', 'topo', 'sat'} <= {i for i, _ in syria}, syria
    set_theatre(fr, 'Caucasus')
    cau = [(r['id'], r['txt']) for r in TP.rows(fr)]
    assert {'dcs', 'topo', 'sat'} <= {i for i, _ in cau}
    assert dict(syria)['dcs'] == dict(cau)['dcs'] and dict(syria)['sat'] == dict(cau)['sat']
    # Caucase : « Carte DCS » (copie publique, puis Olympus) et « Satellite » (Esri), attributions d'origine
    n0 = len(pg.bench.log)
    choose(fr, 'dcs')
    pose(fr, 43.0, 41.6, 8)
    got = pg.bench.log[n0:]
    assert got and all(u.startswith((PT + 'alt-caucasus/', OLYMPUS)) for u in got), got
    assert not [u for u in got if u.startswith((ALT, SAT))]
    assert 'DCS Olympus' in attribution(fr) and 'Eagle Dynamics' not in attribution(fr)
    n1 = len(pg.bench.log)
    choose(fr, 'sat')
    pose(fr, 43.0, 41.6, 8)
    got = pg.bench.log[n1:]
    assert got and all(u.startswith(ESRI) for u in got), got
    assert 'Esri' in attribution(fr) and 'Eagle Dynamics' not in attribution(fr)
    # GermanyCW : Carte DCS avec ses niveaux de la base (5 couches avec le miroir)
    set_theatre(fr, 'GermanyCW')
    choose(fr, 'dcs')
    attendre(fr, "__RP.baseLayers.length === 5", 'les cinq couches de GermanyCW', lu="__RP.baseLayers.length")
    assert fr.evaluate("__RP.baseLayers.map(l => [l.options.minNativeZoom, l.options.maxNativeZoom, l.options.minZoom, !!l.options.mirrorOnly])") == \
        [[1, 11, 1, False], [13, 13, 11, False], [14, 14, 14, True], [15, 15, 13, False], [16, 16, 16, True]]
    assert pg.errs == []
    close(pg)
