"""Le fond papier du Route Planner (Papier, Papier sombre : une carte vectorielle MapLibre GL JS sous Leaflet), joué sur le shell construit
(dist/dcs_mission_plan.html, chromium), à 1 280 × 800 et à 412 × 915 au doigt. Aucun réseau : les requêtes hors file:/data:/blob: sont interceptées ;
sous l'adresse publique des tuiles, le banc sert les styles (copies de ceux de l'hôte), deux petits PMTiles inventés (tests/fixtures/rp_papier/,
fabriqués par fabriquer.py) avec les requêtes partielles (Range), et un relief.json ; sprite et glyphes : 404. Les contrôles passent par le DOM, dans le shell."""
import hashlib
import json
import re
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
FIX = ROOT / 'tests' / 'fixtures' / 'rp_papier'
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
sys.path.insert(0, str(FIX))
from public_host_block import build_block  # noqa: E402
from banc_attente import attendre, attendre_images, attendre_rp, attendre_shell, attendre_theatre, exemple, viser, cadre_export  # noqa: E402
import fabriquer as FAB  # noqa: E402

PT = re.search(r"PUBLIC_TILES = '([^']+)'", build_block()).group(1)
FONDS = PT + 'fonds/'
SRC = (ROOT / 'build_route_planner.py').read_text(encoding='utf-8')
LIBS = dict(re.findall(r"\('(lib_[a-z_]+)', '__LIB_[A-Z_]+__', '([0-9a-f]{64})'\)", SRC))     # les sha256 des fichiers npm, lus dans MAP_LIBS du build
SYRIA_M = '© OpenStreetMap contributors (ODbL) · Copernicus WorldDEM-30 © DLR e.V., © Airbus DS'       # les mentions des styles servis (fixture)
CAUCASUS_M = '© OpenStreetMap contributors (ODbL) · Copernicus WorldDEM-30 © DLR e.V., © Airbus DS, Copernicus WorldDEM-90 © DLR e.V., © Airbus DS'
RELIEF_DOC = {'format': 'dcs-relief-tiles-v1', 'theatre': 'Syria', 'edition': 'test', 'minZoom': 8, 'maxNativeZoom': 11, 'tileSize': 256,
              'bounds': [[33.15, 35.15], [36.75, 37.95]],
              'layers': {'hillshade': {'path': 'hillshade/{z}/{x}/{y}.webp'},
                         'elevation': {'path': 'elevation/{z}/{x}/{y}.png', 'encoding': 'terrain-rgb', 'base_m': -10000, 'step_m': 0.1}},
              'attribution': 'test', 'source': 'test', 'tiles_per_zoom': {}}

# Ce que le contexte enregistre dans chaque cadre, avant tout script : les URL blob: créées, le texte remis à chaque Blob, les protocoles PMTiles construits,
# et (sans WebGL 2) le contexte webgl2 refusé
INIT = """(() => {
  const C = URL.createObjectURL, R = URL.revokeObjectURL; window.__blobUrls = 0; window.__made = []; window.__revoked = [];
  URL.createObjectURL = function (b) { window.__blobUrls++; const u = C.apply(this, arguments); window.__made.push([u, b && b.size]); return u; };
  URL.revokeObjectURL = function (u) { window.__revoked.push(u); return R.apply(this, arguments); };
  const B = window.Blob; window.__blobTexts = [];
  const W = function Blob(parts, opt) { if (Array.isArray(parts) && parts.length === 1 && typeof parts[0] === 'string') window.__blobTexts.push(parts[0]); return new B(parts, opt); };
  W.prototype = B.prototype; window.Blob = W;
  window.__pmProtocols = 0; let pm;
  Object.defineProperty(window, 'pmtiles', { configurable: true, get() { return pm; }, set(v) {
    if (v && typeof v.Protocol === 'function') { const P = class extends v.Protocol { constructor(...a) { super(...a); window.__pmProtocols++; } };
      v = new Proxy(v, { get(t, k) { return k === 'Protocol' ? P : t[k]; } }); }
    pm = v; } });
  if (%s) { const g = HTMLCanvasElement.prototype.getContext; HTMLCanvasElement.prototype.getContext = function (k) { return k === 'webgl2' ? null : g.apply(this, arguments); }; }
})();"""


def lire(nom):
    return (FIX / nom).read_bytes()


class Bench:
    def __init__(self):
        self.log = []
        self.styles = {'syria/style-clair.json': lire('style-clair.json'), 'syria/style-sombre.json': lire('style-sombre.json'),
                       'caucasus/style-clair.json': lire('caucasus-style-clair.json')}
        self.style_status = {}                       # adresse relative → statut HTTP forcé
        self.data = {'fond.pmtiles': lire('fond.pmtiles'), 'relief.pmtiles': lire('relief.pmtiles')}
        self.mode = {'fond.pmtiles': 'ok', 'relief.pmtiles': 'ok'}       # ok · err (500)

    def serve(self, route, name):
        body = self.data[name]
        cors = {'Access-Control-Allow-Origin': '*', 'Access-Control-Expose-Headers': 'Content-Range, Content-Length, ETag', 'Content-Type': 'application/octet-stream'}
        rng = route.request.headers.get('range')
        m = re.match(r'bytes=(\d+)-(\d+)', rng or '')
        if m:
            a, b = int(m.group(1)), min(int(m.group(2)), len(body) - 1)
            return route.fulfill(status=206, headers={**cors, 'Content-Range': 'bytes %d-%d/%d' % (a, b, len(body))}, body=body[a:b + 1])
        return route.fulfill(status=200, headers=cors, body=body)

    def handler(self, route):
        url = route.request.url
        if url.startswith(('file:', 'data:', 'blob:')):
            return route.continue_()
        self.log.append(url)
        cors = {'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Headers': '*'}
        if route.request.method == 'OPTIONS':
            return route.fulfill(status=204, headers={**cors, 'Access-Control-Allow-Methods': 'GET'}, body='')
        if url.startswith(FONDS):
            rest = url[len(FONDS):]
            name = rest.split('/')[-1]
            if rest in self.styles or rest in self.style_status:
                st = self.style_status.get(rest, 200)
                if st != 200:
                    return route.fulfill(status=st, headers=cors, body='')
                return route.fulfill(status=200, headers={**cors, 'Content-Type': 'application/json'}, body=self.styles[rest])
            if name in self.data:
                mode = self.mode[name]
                if mode == 'err':
                    return route.fulfill(status=500, headers=cors, body='')
                return self.serve(route, name)
            return route.fulfill(status=404, headers=cors, body='')
        if url.startswith(PT + 'relief/'):
            rest = url[len(PT + 'relief/'):]
            th = rest.split('/')[0]
            if rest == th + '/relief.json' and th in ('Syria', 'Caucasus'):
                return route.fulfill(status=200, headers={**cors, 'Content-Type': 'application/json'}, body=json.dumps({**RELIEF_DOC, 'theatre': th}))
            return route.fulfill(status=404, headers=cors, body='')
        return route.abort()

    def fonds(self, part=''):
        return [u[len(FONDS):] for u in self.log if u.startswith(FONDS) and part in u]


@pytest.fixture(scope='module')
def browser():
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        br = p.chromium.launch(executable_path=str(CHROMIUM), args=['--no-sandbox'])
        yield br
        br.close()


def open_rp(br, w=1280, h=800, touch=False, lang='fr', nogl=False, seed=None, theatre=None):
    ctx = br.new_context(viewport={'width': w, 'height': h}, has_touch=touch, is_mobile=touch)
    ctx.add_init_script(INIT % ('true' if nogl else 'false'))
    ctx.add_init_script("try{localStorage.setItem('lang_v1','%s')}catch(e){}" % lang)
    if seed:
        ctx.add_init_script("(() => { if (!sessionStorage.getItem('seeded')) { const d = %s; for (const k in d) localStorage.setItem(k, d[k]); sessionStorage.setItem('seeded', '1'); } })()" % json.dumps(seed))
    pg = ctx.new_page()
    pg.errs = []
    pg.on('pageerror', lambda e: pg.errs.append(str(e) + ' @ ' + str(getattr(e, 'stack', ''))[:600]))
    pg.bench = Bench()
    pg.route('**/*', pg.bench.handler)
    if seed:
        pg.goto(SHELL + '#rp', wait_until='commit')
        attendre_shell(pg)
        return pg, attendre_rp(pg)
    pg.goto('about:blank')
    pg.goto(SHELL, wait_until='commit')
    attendre_shell(pg)
    exemple(pg, 'fl')                                      # l'exemple, théâtre Syria
    pg.evaluate("openModule('rp')")
    fr = attendre_rp(pg)
    if theatre:
        set_theatre(fr, theatre)
    return pg, fr


def close(pg):
    pg.context.close()


def set_theatre(fr, tid):
    fr.evaluate("(id) => { const s = document.getElementById('theatre'); s.value = id; s.dispatchEvent(new Event('change', { bubbles: true })); }", tid)
    attendre_theatre(fr, tid)


def menu(fr, on):
    fr.evaluate("if (DSP.open !== %s) document.getElementById('btn-display').click()" % ('true' if on else 'false'))
    attendre(fr, 'DSP.open === arg', 'le menu Affichage %s' % ('ouvert' if on else 'fermé'), lu='DSP.open', arg=on)
    attendre_images(fr, 2)


def rows(fr):
    menu(fr, True)
    r = fr.evaluate("[...document.querySelectorAll('#dsp-panel [data-base]')].map(b => ({ id: b.getAttribute('data-base'), txt: b.textContent, off: b.getAttribute('aria-disabled') === 'true', title: b.title }))")
    menu(fr, False)
    return r


def choose(fr, lid):
    """Choisit un fond par le menu Affichage (un clic sur sa ligne)."""
    menu(fr, True)
    fr.evaluate("(id) => document.querySelector('#dsp-panel [data-base=\"' + id + '\"]').click()", lid)
    attendre(fr, 'S.ui.layer === arg', 'le fond %s choisi' % lid, lu='S.ui.layer', arg=lid)
    menu(fr, False)


PAPER_UP = "!!paperGl() && tileOk > 0 && paperGl().loaded() && !inFallback"
PAPER_UP_LU = "({ gl: !!paperGl(), tileOk: tileOk, tileErr: tileErr, loaded: !!paperGl() && paperGl().loaded(), inFallback: inFallback, layer: S.ui.layer })"


def paper_up(fr, delai=20000):
    attendre(fr, PAPER_UP, 'le fond papier posé (carte MapLibre, premier idle, chargée, hors du repli)', lu=PAPER_UP_LU, delai=delai)
    attendre_images(fr, 2)


def attribution(fr):
    return fr.evaluate("__RP.map.attributionControl.getContainer().textContent")


def settle_gl(fr):
    """La carte MapLibre a rattrapé la vue de Leaflet (le pont la suit à 32 ms au plus) et ne bouge plus."""
    attendre(fr, """(() => { const g = paperGl(); if (!g) return false; const c = __RP.map.getCenter(), k = g.getCenter();
        return Math.abs(k.lng - c.lng) < 1e-9 && Math.abs(k.lat - c.lat) < 1e-9 && Math.abs(g.getZoom() - (__RP.map.getZoom() - 1)) < 1e-9 && g.loaded() && !g.isMoving(); })()""",
             'la carte MapLibre à la vue de Leaflet, au repos', lu="(() => { const g = paperGl(); return g ? [g.getCenter(), g.getZoom(), __RP.map.getCenter(), __RP.map.getZoom()] : null; })()")
    attendre_images(fr, 3)


# Un point connu, dans le repère du conteneur de la carte : Leaflet sans son arrondi (project), MapLibre (project ramené par la position de son conteneur)
PROJ = """([lat, lon]) => { const m = __RP.map, g = paperGl(), z = m.getZoom();
  const lp = m.project([lat, lon], z).subtract(m.getPixelOrigin()).add(m._getMapPanePos());
  const mr = m.getContainer().getBoundingClientRect(), gr = g.getContainer().getBoundingClientRect(), gp = g.project([lon, lat]);
  return { leaflet: [lp.x, lp.y], gl: [gp.x + gr.left - mr.left, gp.y + gr.top - mr.top] }; }"""


def proj(fr, lat, lon):
    r = fr.evaluate(PROJ, [lat, lon])
    return r['leaflet'], r['gl']


# --------------------------------------------------------------------------------------------------------------------------------------------------
def test_libraries_inert_once_and_fixture_remade_to_the_byte(tmp_path):
    # les cinq bibliothèques d'assets.json, à l'octet des fichiers npm (les sha256 de MAP_LIBS, dans le build)
    assert len(LIBS) == 5
    assets = json.loads((ROOT / 'assets.json').read_text(encoding='utf-8'))
    for k, sha in LIBS.items():
        assert hashlib.sha256(assets[k].encode('utf-8')).hexdigest() == sha, k
    # la page : les cinq textes, inertes, une fois chacun
    html = (ROOT / 'dist' / 'dcs_route_planner.html').read_text(encoding='utf-8')
    for k in LIBS:
        tag = '<script type="text/plain" id="%s">' % k.replace('_', '-')
        assert html.count(tag) == 1 and html.count(tag + assets[k] + '</script>') == 1, k
    # les deux fonds sont des fonds du module
    ids = re.search(r"const LAYER_IDS = \[([^\]]*)\];", SRC).group(1)
    assert "'papier'" in ids and "'papier-sombre'" in ids
    # la fixture : refaite à l'octet par son script
    import shutil
    import subprocess
    shutil.copy(FIX / 'fabriquer.py', tmp_path / 'fabriquer.py')
    subprocess.run([sys.executable, '-B', str(tmp_path / 'fabriquer.py')], check=True, capture_output=True)
    for n in ('fond.pmtiles', 'relief.pmtiles'):
        assert (tmp_path / n).read_bytes() == (FIX / n).read_bytes(), n


@needs_pw
@pytest.mark.parametrize('w,h,touch', [(1280, 800, False), (412, 915, True)])
def test_rows_in_place_greyed_off_their_theatres_and_nothing_loaded_before_a_choice(browser, w, h, touch):
    pg, fr = open_rp(browser, w, h, touch)
    assert fr.evaluate("S.theatre") == 'Syria'
    r = rows(fr)
    assert [x['id'] for x in r] == ['dcs', 'papier', 'papier-sombre', 'topo', 'sat', 'grid']
    assert [(x['txt'], x['off']) for x in r[1:3]] == [(fr.evaluate("t('bm.papier')"), False), (fr.evaluate("t('bm.papierSombre')"), False)]
    # avant tout choix : rien de MapLibre (aucune URL blob:, pas de maplibregl, aucune requête du fond papier)
    assert fr.evaluate("[window.__blobUrls, typeof globalThis.maplibregl, PP.libs, document.querySelectorAll('.leaflet-gl-layer').length]") == [0, 'undefined', None, 0]
    assert pg.bench.fonds() == []
    set_theatre(fr, 'MarianaIslands')
    r = rows(fr)
    assert [x['id'] for x in r] == ['dcs', 'papier', 'papier-sombre', 'topo', 'sat', 'grid']
    off = fr.evaluate("t('bm.papier.off')")
    assert off and off != fr.evaluate("t('layer.dcsOff')") and [(x['off'], x['title']) for x in r[1:3]] == [(True, off), (True, off)]
    # une ligne grisée ne choisit rien
    menu(fr, True)
    fr.evaluate("document.querySelector('#dsp-panel [data-base=papier]').click()")
    menu(fr, False)
    assert fr.evaluate("S.ui.layer") == 'topo' and fr.evaluate("window.__blobUrls") == 0
    set_theatre(fr, 'Syria')
    choose(fr, 'papier')
    paper_up(fr)
    assert pg.errs == []
    close(pg)


@needs_pw
def test_libraries_once_style_read_once_per_variant_transformed_and_its_credits(browser):
    pg, fr = open_rp(browser)
    choose(fr, 'papier')
    paper_up(fr)
    # les bibliothèques : le texte remis à chaque Blob du RP est l'octet du fichier npm ; la version ; le protocole une fois
    shas = fr.evaluate("""Promise.all(window.__blobTexts.map(async t => { const d = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(t));
        return [...new Uint8Array(d)].map(b => b.toString(16).padStart(2, '0')).join(''); }))""")
    assert shas[:2] == [LIBS['lib_maplibre_gl'], LIBS['lib_maplibre_gl_worker']]
    assert fr.evaluate("maplibregl.getVersion()") == '6.17.0'
    fr.evaluate("window.__proto0 = maplibregl.config.REGISTERED_PROTOCOLS.pmtiles; 0")
    assert fr.evaluate("typeof window.__proto0") == 'function' and fr.evaluate("window.__pmProtocols") == 1
    assert fr.evaluate("document.querySelectorAll('style').length > 0 && [...document.querySelectorAll('style')].some(s => s.textContent.indexOf('.maplibregl-map{') === 0)")
    # la couche : le panneau des tuiles, sous le relief (250) ; non interactive
    assert fr.evaluate("[paperGl().getContainer().parentNode === __RP.map.getPane('tilePane'), paperGl()._interactive === false || !paperGl().getCanvasContainer().classList.contains('maplibregl-interactive')]") == [True, True]
    assert fr.evaluate("getComputedStyle(document.querySelector('.leaflet-gl-layer')).pointerEvents") == 'none'
    # le style posé
    st = fr.evaluate("(() => { const s = paperGl().getStyle(); return { n: s.layers.length, ids: s.layers.map(l => l.id), fond: s.sources.fond.url, relief: s.sources.relief.url, sprite: s.sprite, glyphs: s.glyphs }; })()")
    assert st['n'] == 26 and not [i for i in st['ids'] if i.startswith('grille')]
    assert st['fond'] == 'pmtiles://' + FONDS + 'syria/fond.pmtiles' and st['relief'] == 'pmtiles://' + FONDS + 'syria/relief.pmtiles'
    assert st['glyphs'] == FONDS + 'syria/glyphs/{fontstack}/{range}.pbf'
    assert st['sprite'] in (FONDS + 'syria/sprite/papier', [{'id': 'default', 'url': FONDS + 'syria/sprite/papier'}])
    assert fr.evaluate("paperGl().getLayoutProperty('relief', 'visibility')") in ('visible', None)
    # la mention, FR puis EN
    fr_txt = fr.evaluate("t('attr.papier', { m: arg })" .replace('arg', json.dumps(SYRIA_M)))
    assert SYRIA_M in fr_txt and fr_txt in attribution(fr)
    fr.evaluate("setLang('en')")
    en_txt = fr.evaluate("t('attr.papier', { m: arg })".replace('arg', json.dumps(SYRIA_M)))
    assert en_txt != fr_txt and SYRIA_M in en_txt
    attendre(fr, "__RP.map.attributionControl.getContainer().textContent.indexOf(arg) !== -1", 'la mention en anglais', lu="__RP.map.attributionControl.getContainer().textContent", arg=en_txt)
    fr.evaluate("setLang('fr')")
    attendre(fr, "__RP.map.attributionControl.getContainer().textContent.indexOf(arg) !== -1", 'la mention en français', lu="__RP.map.attributionControl.getContainer().textContent", arg=fr_txt)
    # trois choix : une lecture par variante
    choose(fr, 'papier-sombre')
    paper_up(fr)
    assert fr.evaluate("paperGl().getStyle().name") == 'papier-sombre' and fr.evaluate("paperGl().getStyle().layers.length") == 26
    choose(fr, 'papier')
    paper_up(fr)
    assert [u for u in pg.bench.fonds('/style-')] == ['syria/style-clair.json', 'syria/style-sombre.json']
    # le Relief de DCS : la couche relief du style cachée, puis rendue, sans relire le style
    menu(fr, True)
    fr.evaluate("document.querySelector('#dsp-panel [data-k=relief]').click()")
    menu(fr, False)
    attendre(fr, "reliefLive() && paperGl().getLayoutProperty('relief', 'visibility') === 'none'", 'le relief du style caché sous le Relief de DCS', lu="[reliefLive(), paperGl().getLayoutProperty('relief', 'visibility')]")
    menu(fr, True)
    fr.evaluate("document.querySelector('#dsp-panel [data-k=relief]').click()")
    menu(fr, False)
    attendre(fr, "!reliefLive() && paperGl().getLayoutProperty('relief', 'visibility') === 'visible'", 'le relief du style rendu', lu="[reliefLive(), paperGl().getLayoutProperty('relief', 'visibility')]")
    assert len(pg.bench.fonds('/style-')) == 2
    # Relief coché avant le choix : le style se pose avec son relief caché
    menu(fr, True)
    fr.evaluate("document.querySelector('#dsp-panel [data-k=relief]').click()")
    menu(fr, False)
    attendre(fr, "reliefLive()", 'le Relief de DCS actif', lu='reliefLive()')
    choose(fr, 'topo')
    choose(fr, 'papier')
    paper_up(fr)
    assert fr.evaluate("paperGl().getLayoutProperty('relief', 'visibility')") == 'none'
    # Caucasus : son style, sa mention ; le protocole n'est pas ajouté de nouveau
    set_theatre(fr, 'Caucasus')
    paper_up(fr)
    assert fr.evaluate("S.ui.layer") == 'papier' and pg.bench.fonds('/style-')[-1] == 'caucasus/style-clair.json'
    assert fr.evaluate("t('attr.papier', { m: arg })".replace('arg', json.dumps(CAUCASUS_M))) in attribution(fr) and SYRIA_M + ' ·' not in attribution(fr)
    assert fr.evaluate("[maplibregl.config.REGISTERED_PROTOCOLS.pmtiles === window.__proto0, window.__pmProtocols, window.__blobTexts.length >= 2]") == [True, 1, True]
    assert fr.evaluate("paperGl().getStyle().sources.fond.url") == 'pmtiles://' + FONDS + 'caucasus/fond.pmtiles'
    assert pg.errs == []
    close(pg)


@needs_pw
@pytest.mark.parametrize('w,h,touch', [(1280, 800, False), (412, 915, True)])
def test_a_kept_paper_map_comes_back_as_the_dcs_map_where_it_cannot_be_drawn(browser, w, h, touch):
    # un fond papier gardé dans route_state_v1, ouvert sur un théâtre sans papier
    pg, fr = open_rp(browser, w, h, touch)
    choose(fr, 'papier')
    paper_up(fr)
    saved = fr.evaluate("Object.fromEntries(Object.entries(localStorage))")
    close(pg)
    st = json.loads(saved['route_state_v1'])
    assert st['ui']['layer'] == 'papier'
    st['theatre'] = 'MarianaIslands'
    seed = dict(saved, route_state_v1=json.dumps(st), mp_theatre_v1=json.dumps({'theatre': 'MarianaIslands'}))
    pg, fr = open_rp(browser, w, h, touch, seed=seed)
    attendre_theatre(fr, 'MarianaIslands')
    assert fr.evaluate("S.ui.layer") == 'dcs' and json.loads(fr.evaluate("localStorage.getItem('route_state_v1')"))['ui']['layer'] == 'dcs'
    assert fr.evaluate("[window.__blobUrls, typeof globalThis.maplibregl]") == [0, 'undefined'] and pg.bench.fonds() == []
    assert pg.errs == []
    close(pg)
    # sans WebGL 2 (le contexte refusé par le banc), sur Syria : grisées, et le fond gardé revient en Carte DCS
    pg, fr = open_rp(browser, w, h, touch, nogl=True, seed=saved)
    attendre_theatre(fr, 'Syria')
    assert fr.evaluate("S.ui.layer") == 'dcs'
    r = rows(fr)
    nogl = fr.evaluate("t('bm.papier.nogl')")
    assert nogl and nogl != fr.evaluate("t('bm.papier.off')") and [(x['id'], x['off'], x['title']) for x in r[1:3]] == [('papier', True, nogl), ('papier-sombre', True, nogl)]
    assert fr.evaluate("[window.__blobUrls, typeof globalThis.maplibregl]") == [0, 'undefined'] and pg.bench.fonds() == []
    assert pg.errs == []
    close(pg)


@needs_pw
def test_fallback_on_a_missing_or_bad_style_or_a_failing_base_and_back(browser):
    pg, fr = open_rp(browser)
    viser(fr, *FAB.tile_ll(4096, 4096), 11)                                               # sur la tuile du banc
    fms = fr.evaluate("FALLBACK_MS")
    bench = pg.bench
    BANNER = "inFallback && document.getElementById('fallback').classList.contains('show')"

    def wait_banner(t0):
        attendre(fr, BANNER, 'le bandeau de repli', lu="[inFallback, tileOk, tileErr, timerElapsed]", delai=fms + 6000)
        return (time.monotonic() - t0) * 1000

    def other_then_paper():
        """Retenter, c'est choisir un autre fond puis le papier ; la Grille sort du repli (Topo, requêtes coupées, y resterait)."""
        choose(fr, 'grid')
        attendre(fr, "!inFallback", 'la grille choisie : hors du repli', lu='inFallback')
        choose(fr, 'papier')
        return time.monotonic()

    # le style en 404
    bench.style_status['syria/style-clair.json'] = 404
    choose(fr, 'papier')
    t0 = time.monotonic()
    assert wait_banner(t0) <= fms + 3000
    assert fr.evaluate("S.ui.layer") == 'papier' and json.loads(fr.evaluate("localStorage.getItem('route_state_v1')"))['ui']['layer'] == 'papier'
    # le style illisible (JSON tronqué, puis sans sources) : relu à chaque choix (un échec ne se garde pas)
    bench.style_status.pop('syria/style-clair.json')
    bench.styles['syria/style-clair.json'] = b'{"version": 8, "sources": '
    assert wait_banner(other_then_paper()) <= fms + 3000
    bench.styles['syria/style-clair.json'] = json.dumps({'version': 8, 'layers': []}).encode()
    assert wait_banner(other_then_paper()) <= fms + 3000
    assert bench.fonds('/style-').count('syria/style-clair.json') == 3
    # l'archive du fond en 500, le relief servi (l'idle libre) : le fond est en échec, le bandeau vient à FALLBACK_MS
    bench.styles['syria/style-clair.json'] = lire('style-clair.json')
    bench.mode.update({'fond.pmtiles': 'err', 'relief.pmtiles': 'ok'})
    t0 = other_then_paper()
    attendre(fr, "!!paperGl() && tileErr > 0", "l'archive du fond en échec", lu="[!!paperGl(), tileErr, tileOk]", delai=10000)
    el = wait_banner(t0)
    assert fms - 300 <= el <= fms + 3000 and fr.evaluate("[tileOk, S.ui.layer]") == [0, 'papier']
    # le fond servi : un autre fond, puis le papier ; le fond revient (son archive relue), le bandeau part
    bench.mode['fond.pmtiles'] = 'ok'
    other_then_paper()
    attendre(fr, "!!paperGl() && tileOk > 0 && !inFallback && !document.getElementById('fallback').classList.contains('show')", 'le fond revenu, le bandeau parti', lu=PAPER_UP_LU, delai=20000)
    attendre(fr, "paperGl().querySourceFeatures('fond', { sourceLayer: 'routes' }).length > 0 && tileErr === 0", 'les routes du fond lues de nouveau (son archive relue)',
             lu="[paperGl().querySourceFeatures('fond', { sourceLayer: 'routes' }).length, tileErr]")
    # le relief en 500, le fond servi : pas de repli (une carte sans relief reste utilisable) ; sprite et glyphes en 404 non plus
    bench.mode['relief.pmtiles'] = 'err'
    choose(fr, 'papier-sombre')
    attendre(fr, "!!paperGl() && timerElapsed && tileOk > 0", 'FALLBACK_MS passé sur le fond papier sombre', lu="[!!paperGl(), timerElapsed, tileOk, tileErr]", delai=fms + 6000)
    attendre_images(fr, 5)
    assert [u for u in bench.fonds() if u.endswith('relief.pmtiles')] and [u for u in bench.fonds() if 'sprite' in u or 'glyphs' in u]      # demandés, en échec
    assert fr.evaluate("[inFallback, tileErr, document.getElementById('fallback').classList.contains('show')]") == [False, 0, False]
    assert pg.errs == []
    close(pg)


@needs_pw
def test_the_libraries_are_tried_again_after_a_failure_without_posting_twice(browser):
    pg, fr = open_rp(browser)
    viser(fr, *FAB.tile_ll(4096, 4096), 11)
    good = fr.evaluate("document.getElementById('lib-maplibre-gl').textContent.length")
    fr.evaluate("window.__lib = document.getElementById('lib-maplibre-gl').textContent; document.getElementById('lib-maplibre-gl').textContent = 'export const x = ;'; 0")
    choose(fr, 'papier')
    attendre(fr, "inFallback && document.getElementById('fallback').classList.contains('show') && PP.libs === null", 'le repli, la promesse des bibliothèques oubliée', lu="[inFallback, PP.libs]")
    assert fr.evaluate("[typeof globalThis.maplibregl, !!PP.css, PP.scripts, window.__pmProtocols]") == ['undefined', True, False, 0]
    fr.evaluate("document.getElementById('lib-maplibre-gl').textContent = window.__lib; 0")
    choose(fr, 'grid')
    attendre(fr, "!inFallback", 'la grille choisie : hors du repli', lu='inFallback')
    choose(fr, 'papier')
    paper_up(fr)
    css = fr.evaluate("[...document.querySelectorAll('style')].filter(s => s.textContent.indexOf('.maplibregl-map{') === 0).length")
    scripts = fr.evaluate("[...document.head.querySelectorAll('script')].filter(s => s.textContent === document.getElementById('lib-pmtiles').textContent || s.textContent === document.getElementById('lib-maplibre-gl-leaflet').textContent).length")
    assert [css, scripts, fr.evaluate("window.__pmProtocols"), fr.evaluate("maplibregl.getVersion()")] == [1, 2, 1, '6.17.0'] and good > 1000000
    # les URL blob: des deux essais du module révoquées, celle du worker gardée
    made = fr.evaluate("window.__made")
    mods = [u for u, n in made if n == 1110272 or n == len('export const x = ;')]
    workers = [u for u, n in made if n == 520114]
    revoked = fr.evaluate("window.__revoked")
    assert len(mods) == 2 and all(u in revoked for u in mods) and len(workers) == 1 and workers[0] not in revoked
    # le pont après un retrait : _transitionEnd et _resize demandent une image, la couche part avant elle ; aucune erreur
    fr.evaluate("(() => { const l = __RP.baseLayers[0]; l._transitionEnd(); l._resize(); dspSetBase('grid'); })(); 0")
    attendre_images(fr, 5)
    assert pg.errs == []
    close(pg)


def _tile_px(fx, fy):
    return FAB.tile_ll(fx, fy)


@needs_pw
def test_the_export_keeps_the_paper_map_its_credits_and_a_sharp_pixel_ratio(browser):
    pg, fr = open_rp(browser)
    pg.evaluate("window.MP_SEND_MAP = (o) => { window.__sent = o; }")
    for k in ('grid', 'towns', 'airfields'):                                              # rien par-dessus les pixels mesurés
        if fr.evaluate("(k) => dspState(k).on", k):
            fr.evaluate("(k) => dspToggle(k)", k)
    fr.evaluate("() => { RSET.routes = [blankRoute()]; RSET.active = 0; S.name = ''; S.points = RSET.routes[0].points; S.refs = []; sel = -1; persistState(); renderAll(); }")
    choose(fr, 'papier')
    paper_up(fr)
    lat, lon = _tile_px(3000, 4300)                                                        # 0,25 px par unité de tuile à ce zoom
    viser(fr, lat, lon, 12)
    settle_gl(fr)
    cadre_export(fr, True)
    settle_gl(fr)
    fr.evaluate("""() => { const o = window.html2canvas; window.__pr = null; window.html2canvas = function () { window.__pr = paperGl().getPixelRatio(); return o.apply(this, arguments); };
        window.__txt = []; const f = CanvasRenderingContext2D.prototype.fillText; CanvasRenderingContext2D.prototype.fillText = function (t) { window.__txt.push(String(t)); return f.apply(this, arguments); }; }""")
    rect = fr.evaluate("EXP.rect")
    scale = fr.evaluate("EXP_LONG / Math.max(EXP.rect.w, EXP.rect.h)")
    # les points mesurés, dans le repère du conteneur : la route trunk (y = 4096) à x = 3600, la mer à x = 1000
    pts = {k: proj(fr, *_tile_px(*v))[0] for k, v in {'trunk': (3600, FAB.TRUNK_Y), 'sea': (1800, 4300), 'land': (3600, 5000)}.items()}
    fr.evaluate("expGo()")
    attendre(pg, '!!window.__sent', 'la carte envoyée', lu='!!window.__sent', delai=30000)
    assert fr.evaluate("window.__pr") == max(1, scale)
    attendre(fr, "paperGl().getPixelRatio() === window.devicePixelRatio", 'le rapport de pixels revenu', lu='paperGl().getPixelRatio()')
    # la mention dans l'image
    assert SYRIA_M in drawn(fr), fr.evaluate("window.__txt")
    sent = pg.evaluate("window.__sent")
    W = 1600 if rect['w'] >= rect['h'] else round(1600 * 2 / 3)
    k = W / rect['w']
    # l'image lue dans la page : une colonne autour de la route, des pixels de la mer et de la terre (le relief uni)
    img = {n: [(p[0] - rect['x']) * k, (p[1] - rect['y']) * k] for n, p in pts.items()}
    got = fr.evaluate("""([url, img]) => new Promise(res => { const im = new Image(); im.onload = () => { const c = document.createElement('canvas'); c.width = im.width; c.height = im.height;
        const g = c.getContext('2d'); g.drawImage(im, 0, 0); const px = (x, y) => [...g.getImageData(Math.round(x), Math.round(y), 1, 1).data].slice(0, 3);
        const col = []; for (let dy = -30; dy <= 30; dy++) col.push(px(img.trunk[0], img.trunk[1] + dy));
        res({ col: col, sea: px(img.sea[0], img.sea[1]), land: px(img.land[0], img.land[1]) }); }; im.src = url; })""", [sent['dataUrl'], img])
    dist = lambda a, b: max(abs(x - y) for x, y in zip(a, b))  # noqa: E731
    assert dist(got['sea'], (0xdf, 0xe5, 0xdf)) <= 12, got['sea']
    assert dist(got['land'], FAB.RELIEF_RGB) <= 14, got['land']
    dark = [i - 30 for i, c in enumerate(got['col']) if sum(c) < 3 * 110]
    assert dark, got['col']
    centre = (min(dark) + max(dark)) / 2
    assert abs(centre) <= 2, (dark, centre)
    # le Caucase en portrait, Relief de DCS coché : les mentions ne tiennent pas en une ligne ; sur deux, entières
    fr.evaluate("expClose(); 0")
    set_theatre(fr, 'Caucasus')
    paper_up(fr)
    menu(fr, True)
    fr.evaluate("document.querySelector('#dsp-panel [data-k=relief]').click()")
    menu(fr, False)
    attendre(fr, "reliefLive()", 'le Relief de DCS posé', lu='[RE.key, !!RE.layer, !!RE.meta]')
    cadre_export(fr, True)
    fr.evaluate("expSetOrient('portrait'); 0")
    attendre_images(fr, 3)
    fr.evaluate("window.__txt = []; 0")
    pg.evaluate("window.__sent = null")
    fr.evaluate("expGo()")
    attendre(pg, '!!window.__sent', 'la carte envoyée (portrait)', lu='!!window.__sent', delai=30000)
    lines = [x for x in fr.evaluate("window.__txt") if 'OpenStreetMap' in x or 'WorldDEM' in x or 'Eagle Dynamics' in x]
    relief = re.sub(r'\s+', ' ', fr.evaluate("t('attr.relief')"))
    assert len(lines) == 2 and not [x for x in lines if x.endswith('…')], lines
    assert CAUCASUS_M in drawn(fr) and relief in drawn(fr), (lines, relief)
    assert pg.errs == []
    close(pg)


def drawn(fr):
    """Les textes dessinés dans l'image, joints par une espace, les blancs ramenés à l'espace (comme expAttribution())."""
    return re.sub(r'\s+', ' ', ' '.join(fr.evaluate("window.__txt")))


@needs_pw
@pytest.mark.parametrize('w,h,touch', [(1280, 800, False), (412, 915, True), (345, 590, True)])
def test_the_paper_map_follows_leaflet_to_the_pixel(browser, w, h, touch):
    pg, fr = open_rp(browser, w, h, touch)
    fr.evaluate("() => { RSET.routes = [blankRoute()]; RSET.active = 0; S.name = ''; S.points = RSET.routes[0].points; S.refs = []; sel = -1; persistState(); renderAll(); }")
    choose(fr, 'papier')
    paper_up(fr)
    known = _tile_px(5000, 4096)
    viser(fr, *_tile_px(4800, 4300), 12)
    settle_gl(fr)

    def check(label):
        settle_gl(fr)
        le, gl = proj(fr, *known)
        assert abs(le[0] - gl[0]) <= 1 and abs(le[1] - gl[1]) <= 1, (label, le, gl)

    check('vue')
    fr.evaluate("__RP.map.panBy([137, -61], { animate: false })")
    check('déplacement')
    fr.evaluate("__RP.map.setZoom(__RP.map.getZoom() + 1)")
    check('zoom +1')
    fr.evaluate("__RP.map.setZoom(__RP.map.getZoom() - 2)")
    check('zoom −2')
    # au zoom 12 : une branche de route du RP posée sur la route trunk du fond coïncide avec elle, à 1 px
    a, b = _tile_px(4096 - 400, FAB.TRUNK_Y), _tile_px(4096 + 400, FAB.TRUNK_Y)                  # 200 px à ce zoom, dans la vue aux trois tailles
    viser(fr, (a[0] + b[0]) / 2, (a[1] + b[1]) / 2, 12)
    fr.evaluate("([a, b]) => { addPoint(a[0], a[1]); addPoint(b[0], b[1]); }", [list(a), list(b)])
    attendre(fr, "S.points.length === 2", 'deux points')
    settle_gl(fr)
    m = fr.evaluate("""([a, b]) => { const m = __RP.map, mr = m.getContainer().getBoundingClientRect(), g = paperGl(), gr = g.getContainer().getBoundingClientRect();
        let leg = null; routeGroup.eachLayer(l => { if (!leg && l instanceof L.Polyline && !(l instanceof L.Polygon) && l._parts && l._parts.length && l._parts[0].length === 2) leg = l; });
        const pane = m._getMapPanePos(), part = leg._parts[0].map(p => [p.x + pane.x, p.y + pane.y]);
        const ga = g.project([a[1], a[0]]), gb = g.project([b[1], b[0]]);
        const mid = [(ga.x + gb.x) / 2, (ga.y + gb.y) / 2];
        const cv = document.createElement('canvas'), src = g.getCanvas(), pr = g.getPixelRatio(); cv.width = src.width; cv.height = src.height;
        const c2 = cv.getContext('2d'); c2.drawImage(src, 0, 0); const col = [], r0 = Math.floor(mid[1] * pr) - 20;
        for (let r = r0; r <= r0 + 40; r++) col.push([r, ...c2.getImageData(Math.floor(mid[0] * pr), r, 1, 1).data]);
        return { leg: part, gl: [[ga.x + gr.left - mr.left, ga.y + gr.top - mr.top], [gb.x + gr.left - mr.left, gb.y + gr.top - mr.top]], col: col, pr: pr,
                 legY: (part[0][1] + part[1][1]) / 2 - (gr.top - mr.top) }; }""", [list(a), list(b)])
    for (lx, ly), (gx, gy) in zip(m['leg'], m['gl']):
        assert abs(lx - gx) <= 1 and abs(ly - gy) <= 1, m
    # la route du fond, lue dans le canevas de MapLibre (ses lignes de pixels, centres en r + 0,5), contre la branche que Leaflet dessine (repère du conteneur MapLibre)
    road = [(c[0] + 0.5) / m['pr'] for c in m['col'] if c[4] > 0 and max(abs(c[1] - FAB.RELIEF_RGB[0]), abs(c[2] - FAB.RELIEF_RGB[1]), abs(c[3] - FAB.RELIEF_RGB[2])) > 30]
    assert road, m['col']
    assert abs((min(road) + max(road)) / 2 - m['legY']) <= 1, (road, m['legY'])
    assert pg.errs == []
    close(pg)


# --------------------------------------------------------------------------------------------------------------------------------------------------
# Le niveau 14 du miroir sur GermanyCW : une couche du miroir seul, [14, 14, 14], entre la couche 13 et la 15 ; la 16 au-dessus de tout
OLYMPUS = 'https://maps.dcsolympus.com/maps/'
MIRROR_GCW = PT + 'alt-GermanyCW/'
T14 = (8542, 5438)
MISSING = {'15/17084/10876.png', '15/17084/10877.png'}         # le miroir sert toute tuile, sauf ces deux-là (le niveau 15 manque sous la moitié ouest de 14/8542/5438)
LAYER_OPTS = "__RP.baseLayers.map(l => [l.options.minNativeZoom, l.options.maxNativeZoom, l.options.minZoom, !!l.options.mirrorOnly])"


def mirror_handler(pg):
    base = pg.bench.handler
    tile = FAB.png(256, 256, (40, 120, 200))

    def h(route):
        url = route.request.url
        if url.startswith(MIRROR_GCW):
            pg.bench.log.append(url)
            rest = url[len(MIRROR_GCW):]
            if rest not in MISSING:
                return route.fulfill(status=200, headers={'Access-Control-Allow-Origin': '*', 'Content-Type': 'image/png'}, body=tile)
            return route.fulfill(status=404, headers={'Access-Control-Allow-Origin': '*'}, body='')
        return base(route)
    return h


@needs_pw
def test_level_14_of_the_mirror_over_cold_war_germany_between_levels_13_and_15(browser):
    pg, fr = open_rp(browser)
    pg.unroute('**/*')
    pg.route('**/*', mirror_handler(pg))
    set_theatre(fr, 'GermanyCW')
    choose(fr, 'dcs')
    attendre(fr, "S.ui.layer === 'dcs' && dcsKey() === 'alt-GermanyCW' && __RP.baseLayers.length === 5", 'la Carte DCS de GermanyCW, cinq couches', lu=LAYER_OPTS)
    assert fr.evaluate(LAYER_OPTS) == [[1, 11, 1, False], [13, 13, 11, False], [14, 14, 14, True], [15, 15, 13, False], [16, 16, 16, True]]
    # l'ordre dans le DOM : 11, 13, 14, 15, 16 (même zIndex : l'ordre du DOM est l'ordre d'empilement)
    order = fr.evaluate("""(() => { const kids = [...__RP.map.getPane('tilePane').children];
        return __RP.baseLayers.map(l => [l.options.maxNativeZoom, kids.indexOf(l.getContainer()), getComputedStyle(l.getContainer()).zIndex]); })()""")
    assert [o[1] for o in order] == sorted(o[1] for o in order) and len({o[2] for o in order}) == 1, order
    lat, lon = FAB.tile_ll(4096, 4096, z=14, x=T14[0], y=T14[1])
    viser(fr, lat, lon, 15)
    attendre(fr, """[...__RP.baseLayers[2].getContainer().querySelectorAll('img.leaflet-tile-loaded')].some(i => i.src.indexOf('/14/8542/5438.png') !== -1)
        && [...__RP.baseLayers[3].getContainer().querySelectorAll('img.leaflet-tile-loaded')].some(i => i.src.indexOf('/15/17085/10876.png') !== -1)""",
             'la tuile 14/8542/5438 et la 15/17085/10876 du miroir affichées', lu="__RP.baseLayers.map(l => [...l.getContainer().querySelectorAll('img')].map(i => i.src.split('/').slice(-3).join('/') + (i.classList.contains('leaflet-tile-loaded') ? '+' : '')))", delai=20000)
    attendre_images(fr, 5)
    log = pg.bench.log
    assert MIRROR_GCW + '14/8542/5438.png' in log and MIRROR_GCW + '15/17084/10876.png' in log
    assert not [u for u in log if u.startswith(OLYMPUS) and '/14/' in u], [u for u in log if u.startswith(OLYMPUS)]
    # la 15, là où elle existe, couvre la 14 : elle est dans une couche posée après, au même endroit
    geo = fr.evaluate("""(() => { const f = (l, s) => [...l.getContainer().querySelectorAll('img')].find(i => i.src.indexOf(s) !== -1).getBoundingClientRect();
        const a = f(__RP.baseLayers[2], '/14/8542/5438.png'), b = f(__RP.baseLayers[3], '/15/17085/10876.png'); return [a.left, a.top, a.right, a.bottom, b.left, b.top, b.right, b.bottom]; })()""")
    assert geo[0] - 1 <= geo[4] and geo[6] <= geo[2] + 1 and geo[1] - 1 <= geo[5] and geo[7] <= geo[3] + 1, geo
    assert fr.evaluate("mirrorCut") is False
    # Syria : les couches DCS de la base (DCS_LEVELS seul, aucune du miroir seul)
    set_theatre(fr, 'Syria')
    attendre(fr, "dcsKey() === 'alt-syria' && S.ui.layer === 'dcs'", 'la Carte DCS de Syria', lu='[dcsKey(), S.ui.layer]')
    syria = fr.evaluate(LAYER_OPTS)
    assert syria == fr.evaluate("DCS_LEVELS[dcsKey()].map(lv => [lv[0], lv[1], lv[2], false])") == [[1, 15, 1, False], [16, 16, 16, False], [17, 17, 17, False]]
    set_theatre(fr, 'GermanyCW')
    attendre(fr, "dcsKey() === 'alt-GermanyCW' && __RP.baseLayers.length === 5", 'la Carte DCS de GermanyCW de nouveau', lu=LAYER_OPTS)
    viser(fr, lat, lon, 15)
    # miroir coupé : aucune couche, aucune demande de niveau 14
    n0 = len(log)
    fr.evaluate("mirrorCut = true; setBase(); 0")
    attendre(fr, "__RP.baseLayers.length === 3", 'les couches sans le miroir seul', lu=LAYER_OPTS)
    fr.evaluate("__RP.map.panBy([300, 200], { animate: false })")
    attendre_images(fr, 10)
    assert fr.evaluate(LAYER_OPTS) == [[1, 11, 1, False], [13, 13, 11, False], [15, 15, 13, False]]
    assert not [u for u in log[n0:] if '/14/' in u], log[n0:]
    assert pg.errs == []
    close(pg)


@needs_pw
def test_404s_of_a_mirror_only_layer_do_not_cut_the_mirror(browser):
    """Au zoom 14 sur GermanyCW : les 404 du niveau 14 (miroir seul) arrivent d'abord, quinze au moins, avant le premier 200 du miroir ; il n'est pas coupé."""
    pg, fr = open_rp(browser)
    set_theatre(fr, 'GermanyCW')
    lat, lon = FAB.tile_ll(4096, 4096, z=14, x=T14[0], y=T14[1])
    viser(fr, lat, lon, 14)
    base = pg.bench.handler
    st = {'n404': 0, 'held': []}
    tile = FAB.png(256, 256, (40, 120, 200))

    def h(route):
        url = route.request.url
        if not url.startswith(MIRROR_GCW):
            return base(route)
        pg.bench.log.append(url)
        if url[len(MIRROR_GCW):].startswith('14/'):
            st['n404'] += 1
            return route.fulfill(status=404, headers={'Access-Control-Allow-Origin': '*'}, body='')
        st['held'].append(route)                       # les autres niveaux attendent : aucun 200 avant les 404 du niveau 14
        return None
    pg.unroute('**/*')
    pg.route('**/*', h)
    assert fr.evaluate("[mirrorOk, mirrorFail, mirrorCut, S.ui.layer]") == [0, 0, False, 'topo']
    choose(fr, 'dcs')
    # quinze tuiles du niveau 14 en échec, vues par la page, avant le moindre 200
    attendre(fr, "__RP.baseLayers.length === 5 && [...__RP.baseLayers[2].getContainer().querySelectorAll('img')].filter(i => i.complete && i.naturalWidth === 0 && i.getAttribute('src')).length >= 15",
             'quinze 404 du niveau 14 reçus par la page', lu="[__RP.baseLayers.length, mirrorOk, mirrorFail, mirrorCut]", delai=20000)
    attendre_images(fr, 3)
    assert fr.evaluate("[mirrorOk, mirrorFail, mirrorCut]") == [0, 0, False] and st['n404'] >= 15 and st['held'], st
    held, st['held'] = st['held'], []
    for r in held:
        r.fulfill(status=200, headers={'Access-Control-Allow-Origin': '*', 'Content-Type': 'image/png'}, body=tile)
    attendre(fr, "[...__RP.baseLayers[1].getContainer().querySelectorAll('img.leaflet-tile-loaded')].length > 0", 'les tuiles 13 du miroir chargées ensuite',
             lu="[mirrorOk, mirrorFail, mirrorCut]")
    assert fr.evaluate("[mirrorCut, mirrorFail]") == [False, 0] and fr.evaluate("mirrorOk") > 0
    for r in st['held']:
        r.fulfill(status=200, headers={'Access-Control-Allow-Origin': '*', 'Content-Type': 'image/png'}, body=tile)
    assert not [u for u in pg.bench.log if u.startswith(OLYMPUS)]
    assert pg.errs == []
    close(pg)
