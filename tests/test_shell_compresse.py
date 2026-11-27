"""Le shell compressé : les sept outils y sont embarqués en gzip puis base64 et décodés à l'ouverture (dist/dcs_mission_plan.html, chromium, aucun réseau).
Sans navigateur : chaque outil embarqué, décodé en Python, égale son fichier à l'octet ; le shell tient dans son budget de 8 000 000 octets ; le build s'arrête au-delà.
Au navigateur : le décodé de la page égale le fichier ; deux ouvertures rapprochées du même outil ne font qu'un cadre et qu'un décodage ; sans DecompressionStream (ou si le décodage échoue),
aucun outil ne s'ouvre, le message dit le navigateur requis, dans la langue du shell, avec le retour à l'accueil ; l'ouverture par l'adresse et au rechargement ; la carte du Route Planner
envoyée au Briefing Generator fermé arrive dans sa fenêtre « Placer la carte ». Les contrôles passent par le DOM, dans le shell."""
import base64
import gzip
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from banc_attente import attendre, attendre_navigation_stable, attendre_outil, attendre_shell  # noqa: E402

CHROMIUM = Path('/opt/pw-browsers/chromium')
try:
    import playwright.sync_api  # noqa: F401
    HAS_PW = CHROMIUM.exists()
except ImportError:
    HAS_PW = False
needs_pw = pytest.mark.skipif(not HAS_PW, reason='playwright ou chromium absent')

SHELL_FILE = ROOT / 'dist' / 'dcs_mission_plan.html'
SHELL = 'file://' + str(SHELL_FILE)
BUDGET = 8_000_000
FILES = {'hq': 'dcs_hq.html', 'bg': 'dcs_briefing_generator.html', 'rs': 'dcs_recon_station.html', 'rp': 'dcs_route_planner.html',
         'dg': 'dcs_datacard_generator.html', 'fc': 'dcs_flight_configurator.html', 'fm': 'dcs_field_manual.html'}
OLD_FR = 'Ce navigateur est trop ancien pour Mission Plan : il faut Safari ou iOS 16.4, Chrome ou Edge 80, Firefox 113, ou plus récent.'
OLD_EN = 'This browser is too old for Mission Plan: it needs Safari or iOS 16.4, Chrome or Edge 80, Firefox 113, or later.'
BACK = {'fr': '◄ Mission Plan', 'en': '◄ Mission Plan'}


def embedded():
    """{id : base64} des outils de MODULE_HTML, lus dans le shell construit."""
    shell = SHELL_FILE.read_text(encoding='utf-8')
    block = re.search(r'const MODULE_HTML = \{(.*?)\n\};', shell, re.S).group(1)
    return dict(re.findall(r'\n\s+(\w+): "([A-Za-z0-9+/=]*)"', '\n' + block))


# ---------- sans navigateur ----------
def test_every_embedded_tool_decodes_to_its_file_byte_for_byte():
    tools = embedded()
    assert sorted(tools) == sorted(FILES), sorted(tools)
    for tid, b64 in tools.items():
        packed = base64.b64decode(b64, validate=True)
        assert packed[:2] == b'\x1f\x8b', tid                                     # du gzip, pas du HTML en base64
        assert gzip.decompress(packed) == (ROOT / 'dist' / FILES[tid]).read_bytes(), tid


def test_the_shell_is_within_its_budget():
    assert SHELL_FILE.stat().st_size <= BUDGET, SHELL_FILE.stat().st_size
    assert re.search(r'^SHELL_BUDGET = 8_000_000$', (ROOT / 'build_mission_plan.py').read_text(encoding='utf-8'), re.M)       # relever le budget est une décision : ce test change avec elle


def test_the_build_stops_over_budget():
    """Le build, budget abaissé dans une copie du script (lue en mémoire ; le fichier du shell part dans un dossier à part, jamais dans dist/) : code 1, le message, rien d'écrit."""
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / 'shell.html'
        stub = (
            "import sys\n"
            "root, out = sys.argv[1], sys.argv[2]\n"
            "sys.path.insert(0, root)\n"
            "path = root + '/build_mission_plan.py'\n"
            "src = open(path, encoding='utf-8').read()\n"
            "a, b = 'SHELL_BUDGET = 8_000_000', \"OUT_FILE = 'dist/dcs_mission_plan.html'\"\n"
            "assert src.count(a) == 1 and src.count(b) == 1\n"
            "src = src.replace(a, 'SHELL_BUDGET = 1000').replace(b, 'OUT_FILE = ' + repr(out))\n"
            "exec(compile(src, path, 'exec'), {'__name__': '__main__', '__file__': path})\n")
        r = subprocess.run([sys.executable, '-B', '-c', stub, str(ROOT), str(out)], capture_output=True, text=True, timeout=300)
        assert r.returncode == 1, (r.returncode, r.stdout[-300:], r.stderr[-300:])
        assert re.search(r'\[ERREUR\] Le shell pèse \d+ octets, au-delà du budget de 1000 octets : relever le budget est une décision — build arrêté', r.stderr), r.stderr[-400:]
        assert not out.exists()


# ---------- au navigateur ----------
@pytest.fixture(scope='module')
def browser():
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        br = p.chromium.launch(executable_path=str(CHROMIUM), args=['--no-sandbox'])
        yield br
        br.close()


SEED = "(() => { try { if (!sessionStorage.getItem('seeded')) { sessionStorage.setItem('seeded', '1'); localStorage.clear(); localStorage.setItem('lang_v1', '@@'); } } catch (e) {} })();"
NO_DS = "try { delete window.DecompressionStream; } catch (e) {} window.DecompressionStream = undefined;"          # un navigateur d'avant mars 2023


def new_page(br, lang='fr', w=1280, h=800, url=SHELL, init=None):
    ctx = br.new_context(viewport={'width': w, 'height': h}, locale=lang + '-' + lang.upper())
    ctx.add_init_script(SEED.replace('@@', lang))
    if init:
        ctx.add_init_script(init)
    pg = ctx.new_page()
    errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.route('**/*', lambda r: r.continue_() if r.request.url.startswith(('file:', 'data:', 'blob:')) else r.abort())
    pg.goto('about:blank')
    pg.goto(url, wait_until='commit')
    attendre_shell(pg)
    pg.errs = errs
    return pg


LOADING = """() => { const ld = document.getElementById('module-loading'), b = ld.querySelector('button'), p = ld.querySelector('p');
  return { hidden: ld.classList.contains('hidden'), err: ld.hasAttribute('data-err'), msg: p ? p.textContent : null, btn: b ? b.textContent : null,
           btnH: b ? Math.round(b.getBoundingClientRect().height) : 0, btnW: b ? Math.round(b.getBoundingClientRect().width) : 0,
           frames: Object.keys(iframes), dom: document.querySelectorAll('#module-view iframe').length, active: activeModule,
           wall: document.getElementById('landing').style.display !== 'none' }; }"""


@needs_pw
def test_the_page_decodes_the_biggest_tool_to_its_file(browser):
    pg = new_page(browser)
    got = pg.evaluate("() => decodeModule(MODULE_HTML.fc)")                      # une promesse de la chaîne
    assert got.encode('utf-8') == (ROOT / 'dist' / FILES['fc']).read_bytes()
    assert pg.evaluate("() => decodeModule(MODULE_HTML.fm) instanceof Promise")
    assert pg.errs == []


@needs_pw
def test_two_close_openings_of_one_tool_make_one_frame_and_one_decoding(browser):
    pg = new_page(browser)
    pg.evaluate("() => { window.__dec = 0; const d = decodeModule; decodeModule = function (b) { window.__dec++; return d(b); }; }")
    r = pg.evaluate("""() => { openModule('rp'); openModule('rp');
      return { frames: Object.keys(iframes), dom: document.querySelectorAll('#iframe-rp').length, loading: !document.getElementById('module-loading').classList.contains('hidden'), active: activeModule }; }""")
    assert r == {'frames': ['rp'], 'dom': 1, 'loading': True, 'active': 'rp'}, r        # le cadre est rangé tout de suite, « Chargement… » à l'écran
    attendre_outil(pg, 'rp')
    attendre_navigation_stable(pg)
    assert pg.evaluate("() => [window.__dec, document.querySelectorAll('#module-view iframe').length, Object.keys(iframes)]") == [1, 1, ['rp']]
    assert pg.errs == []


@needs_pw
def test_back_to_the_wall_while_the_tool_decodes_breaks_nothing(browser):
    pg = new_page(browser)
    pg.evaluate("() => { openModule('fc'); goHub(); }")                              # le cadre se remplit, caché
    r = pg.evaluate(LOADING)
    assert r['hidden'] and r['wall'] and r['active'] is None and r['frames'] == ['fc'], r
    attendre(pg, "document.getElementById('iframe-fc').contentDocument.readyState === 'complete' && document.getElementById('iframe-fc').contentDocument.location.href === 'about:srcdoc'",
             "le cadre du Flight Configurator rempli (srcdoc chargé)", lu="document.getElementById('iframe-fc').contentDocument.location.href")
    r = pg.evaluate("() => ({ shown: document.getElementById('iframe-fc').style.display, wall: document.getElementById('landing').style.display !== 'none', active: activeModule })")
    assert r == {'shown': 'none', 'wall': True, 'active': None}, r
    pg.evaluate("() => openModule('fc')")                                            # il se rouvre, sans nouveau décodage
    attendre_outil(pg, 'fc')
    assert pg.evaluate("() => document.querySelectorAll('#module-view iframe').length") == 1
    assert pg.errs == []


@needs_pw
@pytest.mark.parametrize('lang, msg', [('fr', OLD_FR), ('en', OLD_EN)])
def test_an_old_browser_opens_no_tool_and_says_so(browser, lang, msg):
    pg = new_page(browser, lang, init=NO_DS)
    assert pg.evaluate("() => typeof DecompressionStream") == 'undefined'
    for essai in (1, 2):                                                             # un outil réessayé redit le message
        pg.evaluate("() => openModule('rp')")
        attendre(pg, "!document.getElementById('module-loading').classList.contains('hidden') && document.getElementById('module-loading').hasAttribute('data-err')",
                 'le message du navigateur trop ancien à l\'écran', lu="document.getElementById('module-loading').className")
        r = pg.evaluate(LOADING)
        assert r['msg'] == msg and r['btn'] == BACK[lang], (essai, r)
        assert r['btnH'] >= 44 and r['btnW'] >= 44, r                                # une cible tactile
        assert r['frames'] == [] and r['dom'] == 0 and r['active'] == 'rp', r        # aucun outil, aucun cadre gardé
        pg.locator('#module-loading button').click()
        r = pg.evaluate(LOADING)
        assert r['hidden'] and r['wall'] and r['active'] is None and not r['err'], r  # l'accueil, utilisable
        attendre_navigation_stable(pg)
    pg.locator('#card-hq').click()                                                   # une carte de l'accueil répond : le message revient
    attendre(pg, "document.getElementById('module-loading').hasAttribute('data-err')", 'le message pour HQ', lu="document.getElementById('module-loading').className")
    assert pg.evaluate("() => document.querySelector('#module-loading p').textContent") == msg
    assert pg.errs == []


@needs_pw
def test_the_message_follows_the_language_of_the_shell(browser):
    pg = new_page(browser, 'fr', init=NO_DS)
    pg.evaluate("() => openModule('hq')")
    attendre(pg, "document.getElementById('module-loading').hasAttribute('data-err')", 'le message à l\'écran', lu="document.getElementById('module-loading').className")
    pg.evaluate("() => setLang('en')")
    r = pg.evaluate(LOADING)
    assert r['msg'] == OLD_EN and r['btn'] == BACK['en'] and not r['hidden'], r
    assert pg.errs == []


@needs_pw
def test_a_decoding_that_fails_says_the_same_and_keeps_no_frame(browser):
    pg = new_page(browser)
    pg.evaluate("() => { MODULE_HTML.hq = 'AAAA'; }")                                # du base64 valide qui n'est pas du gzip
    pg.evaluate("() => openModule('hq')")
    attendre(pg, "document.getElementById('module-loading').hasAttribute('data-err')", 'le message à l\'écran', lu="document.getElementById('module-loading').className")
    r = pg.evaluate(LOADING)
    assert r['msg'] == OLD_FR and r['frames'] == [] and r['dom'] == 0, r
    pg.locator('#module-loading button').click()
    assert pg.evaluate(LOADING)['wall']
    pg.evaluate("() => openModule('bg')")                                            # un autre outil s'ouvre
    attendre_outil(pg, 'bg')
    assert pg.errs == []


@needs_pw
def test_a_tool_opened_by_the_address_and_after_a_reload(browser):
    pg = new_page(browser, url=SHELL + '#rp')
    attendre_outil(pg, 'rp')
    attendre_navigation_stable(pg)
    s = pg.evaluate("() => ({ tool: activeModule, hash: location.hash, state: history.state, frames: Object.keys(iframes) })")
    assert s == {'tool': 'rp', 'hash': '#rp', 'state': {'mp': 1, 'tool': 'rp'}, 'frames': ['rp']}, s
    pg.reload(wait_until='commit')
    attendre_shell(pg)
    attendre_outil(pg, 'rp')
    attendre_navigation_stable(pg)
    s = pg.evaluate("() => ({ tool: activeModule, hash: location.hash, state: history.state, dom: document.querySelectorAll('#module-view iframe').length })")
    assert s == {'tool': 'rp', 'hash': '#rp', 'state': {'mp': 1, 'tool': 'rp'}, 'dom': 1}, s
    assert pg.errs == []


@needs_pw
def test_the_route_planner_map_sent_to_a_closed_briefing_generator_arrives_in_its_window(browser):
    pg = new_page(browser)
    assert pg.evaluate("() => Object.keys(iframes)") == []
    pg.evaluate("""() => { const c = document.createElement('canvas'); c.width = c.height = 8; c.getContext('2d').fillRect(0, 0, 8, 8);
      MP_SEND_MAP({ dataUrl: c.toDataURL('image/jpeg'), name: 'carte', theatre: 'caucasus', width: 8, height: 8 }); }""")
    fr = attendre_outil(pg, 'bg')                                                    # la carte envoyée ouvre le Briefing Generator
    attendre(fr, "!document.getElementById('rpmap-modal').hidden && document.getElementById('rpmap-title').getBoundingClientRect().width > 0",
             "la fenêtre « Placer la carte » ouverte dans le Briefing Generator", lu="[document.getElementById('rpmap-modal').hidden, document.getElementById('rpmap-img').src.length]")
    assert fr.evaluate("() => document.getElementById('rpmap-title').textContent") == 'Placer la carte du Route Planner'
    assert pg.evaluate("() => MP_TAKE_MAP()") is None                                # le BG l'a prise
    assert pg.errs == []
