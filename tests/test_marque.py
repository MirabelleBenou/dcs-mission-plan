"""L'insigne de la famille Squadron Ready Room (MP-V2.1.0+16) : les fichiers de brand/, leurs URL data: dans les pages de dist/, les liens d'onglet,
l'accueil (plaque, écusson, signature), l'ancien logo « WG » lu comme le nouveau, le README, les licences et le CHANGELOG. Lecture des fichiers, sans navigateur."""
import base64
import hashlib
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
BRAND = ROOT / 'brand'
DIST = ROOT / 'dist'
CHROMIUM = Path('/opt/pw-browsers/chromium')
try:
    import playwright.sync_api  # noqa: F401
    HAS_PW = CHROMIUM.exists()
except ImportError:
    HAS_PW = False
needs_pw = pytest.mark.skipif(not HAS_PW, reason='playwright ou chromium absent')

SHA256 = {
    'insigne-mission-plan.svg': '26de5e2afb19d1feeb391e5385e619b9fd9a649a9e48001297c72cae6e5bcd36',
    'insigne-ready-room.svg': '92b7562ec31c1e1ab3a34aed0c1f7d9eb3299cadf088c8d76ab26f5c04b46a8e',
    'pictogramme-16.svg': '731ad7dce9e40680599b56bb8c670f58100b43c945e1e141d92c20ccb0c085b6',
    'pictogramme.svg': '2abfaa6fac56e5c4ae9e3655e1cddbb93bbe36fe639fbd7e421975b32ac9e9b7',
    'symbole.svg': '9e9826017493ce970fa3735a95247bc2e82083249158f839a1d3840fa32c4c61',
    'apple-touch-icon.png': 'b90e7f5f3424e8cc9f0c3342037a3b4fb25886406b6c8f629f08d46208b2adae',
    'favicon.ico': 'd756c1622e36f896b3c2753dd35ac86ba2a0c6635a9c7eefbde43fed7eb3dadb',
    'favicon.svg': '2abfaa6fac56e5c4ae9e3655e1cddbb93bbe36fe639fbd7e421975b32ac9e9b7',
    'icone-192.png': '954bb7c5fed7a12b07be8fcdfb14113b717bd173106fb35cf609f62e2cc38c6f',
    'icone-512.png': '5e14d03e72b48ef8ebc67c98f9f95af4eb51522404548877d108e7d8840aa33a',
    'apercu-github-mission-plan.png': '784cd091e45aa72e9c5c53ffe24ca2c79d2fede4e5106aa7715659347cc0ab63',
    'banniere-mission-plan.png': '369f2ad8161cb7a5caa5d24f7f04705ab0ffd0d2356f6251bbbfcf7826bf998b',
}
MIME = {'.svg': 'image/svg+xml', '.ico': 'image/x-icon', '.png': 'image/png'}
PAGES = ['dcs_hq', 'dcs_briefing_generator', 'dcs_recon_station', 'dcs_route_planner', 'dcs_datacard_generator', 'dcs_flight_configurator', 'dcs_field_manual']
CREDIT = 'Squadron Ready Room insignia: original artwork of the project; lettering from Oswald (SIL Open Font License 1.1), converted to outlines.'


def url(name):
    p = BRAND / name
    return 'data:' + MIME[p.suffix] + ';base64,' + base64.b64encode(p.read_bytes()).decode('ascii')


def page(name):
    return (DIST / (name + '.html')).read_text(encoding='utf-8')


def head(html):
    return html[:html.index('</head>')]


def test_brand_files_are_the_master_copies():
    assert sorted(p.name for p in BRAND.iterdir()) == sorted(list(SHA256) + ['README.md'])
    for name, sha in SHA256.items():
        assert hashlib.sha256((BRAND / name).read_bytes()).hexdigest() == sha, name


def test_brand_readme():
    txt = (BRAND / 'README.md').read_text(encoding='utf-8')
    assert CREDIT in txt and 'master files' in txt


def test_tab_icons_modules_two_links_shell_three():
    ico = '<link rel="icon" type="image/x-icon" sizes="16x16 32x32 48x48" href="' + url('favicon.ico') + '">\n'
    svg = '<link rel="icon" type="image/svg+xml" href="' + url('favicon.svg') + '">\n'
    touch = '<link rel="apple-touch-icon" sizes="180x180" href="' + url('apple-touch-icon.png') + '">\n'
    for n in PAGES:
        h = head(page(n))
        m = re.search(r'<title>[^<]*</title>\n', h)
        assert h[m.end():].startswith(ico + svg), n
        assert not h[m.end():].startswith(ico + svg + touch), n
        assert h.count('<link rel="icon"') == 2 and 'apple-touch-icon' not in h, n
    h = head(page('dcs_mission_plan'))
    m = re.search(r'<title>[^<]*</title>\n', h)
    assert h[m.end():].startswith(ico + svg + touch)
    assert h.count('<link rel="icon"') == 2 and h.count('rel="apple-touch-icon"') == 1


def test_shell_home_screen():
    html = page('dcs_mission_plan')
    picto = url('pictogramme.svg')
    assert ('<span class="mark"><img class="mp-plate-picto" src="' + picto + '" alt="" width="24" height="24">DCS · MISSION PLAN</span>') in html
    assert '.plate .mp-plate-picto{vertical-align:-6px; margin-right:10px;}' in html
    crest = '<img id="mp-crest" src="' + url('insigne-mission-plan.svg') + '" alt="Mission Plan" data-source="mp">'
    tab = html[html.index('<div class="tab reveal d2">'):html.index('<div class="wall-stage">')]
    assert tab.count(crest) == 1 and tab.count('id="mp-crest"') == 1 and html.count('id="mp-crest"') == 1
    credits = html[html.index('<div id="credits">'):]
    assert credits.startswith('<div id="credits">\n    <div class="mp-signature"><img src="' + picto + '" alt="" width="18" height="18">Squadron Ready Room family</div>\n    <p>Based on Mission Plan')
    assert '#credits .mp-signature{text-align:center; font:500 12px var(--f-ui); letter-spacing:2.5px; text-transform:uppercase; color:#C9A64A; margin:0 0 8px; opacity:.9;}' in html
    # l'insigne de la Ready Room : une fois, dans le script de l'écusson
    assert html.count("var MP_CREST_RR = '" + url('insigne-ready-room.svg') + "';") == 1
    assert "'crest.wingAlt': 'Emblème de l’escadre'" in html and "'crest.wingAlt': 'Wing emblem'" in html
    assert 'MP-V2.1.0+21' in html
    assert re.search(r'^DEV_BUILD = 21$', (ROOT / 'version_block.py').read_text(encoding='utf-8'), re.M)


def test_former_wg_logo_is_kept_once_each():
    import brand_block
    old = brand_block.LEGACY_WG_LOGO_DATAURL
    assert len(old) == 770 and base64.b64decode(old.split(',', 1)[1]).decode().count('>WG<') == 1
    for n in ('dcs_hq', 'dcs_briefing_generator'):
        assert page(n).count(old) == 1, n
    for n in ('dcs_datacard_generator', 'dcs_field_manual', 'dcs_flight_configurator', 'dcs_mission_plan', 'dcs_recon_station', 'dcs_route_planner'):
        assert old not in page(n), n
    for f in sorted(ROOT.glob('*.py')) + sorted((ROOT / 'tests').glob('*.py')):
        if f.name in ('brand_block.py', 'test_marque.py'):
            continue
        assert old not in f.read_text(encoding='utf-8'), f.name
    master = (BRAND / 'insigne-ready-room.svg').read_bytes()
    for n in ('dcs_hq', 'dcs_briefing_generator'):
        h = page(n)
        # le logo par défaut du Wing, dans la configuration écrite par défaut (une chaîne de script : les guillemets y sont protégés) : décodé, c'est le fichier de brand/, à l'octet
        m = re.findall(r'\\"appTitle\\": \\"(?:[^"\\]|\\u[0-9a-f]{4})*\\", \\"logo\\": \\"data:image/svg\+xml;base64,([A-Za-z0-9+/=]+)\\"', h)
        assert len(m) == 1 and base64.b64decode(m[0]) == master, n
        assert 'function wingLegacyLogo(cfg)' in h and h.count('const LEGACY_WG_LOGO = ') == 1, n


def test_readme_licences_changelog():
    readme = (ROOT / 'README.md').read_text(encoding='utf-8')
    assert readme.startswith('![Mission Plan — part of the Squadron Ready Room family](brand/banniere-mission-plan.png)\n\n# DCS Mission Plan\n')
    assert readme.count('- ' + CREDIT + '\n') == 1
    assert readme.index('- Fonts embedded in every tool:') < readme.index('- ' + CREDIT)
    lic = (ROOT / 'fonts' / 'LICENSES.md').read_text(encoding='utf-8')
    assert lic.endswith(CREDIT + ' The insignia files are in [`../brand/`](../brand/).\n')
    log = (ROOT / 'CHANGELOG.md').read_text(encoding='utf-8')
    unreleased = log.split('\n## Unreleased\n', 1)[1].split('\n## ', 1)[0]
    entries = {
        '### All tools': ["**The Squadron Ready Room family insignia**\n- Every page of the suite carries the family's icon in the browser tab and when pinned to a phone's home screen.\n- The default wing logo, in HQ and the Briefing Generator, is now the Squadron Ready Room insignia; a wing still on the former “WG” logo shows the new one and still counts as not set up.",
                         "**Fixed: “⋯” on very narrow screens**\n- Below 345 px wide, after the toolbar was scrolled, “⋯” could end up off the screen; it now stays in view.",
                         "**Menus easier to read from the keyboard**\n- In the toolbar's menus, the line reached with the arrow keys now has enough contrast in every theme.",
                         "**Menus: the “Delete” line stands out**\n- In the Datacard Generator's and the Route Planner's menus, the “Delete” line under the pointer or reached with the arrow keys now turns red with dark text, readable in every theme.",
                         "**The “⋯” menu from the keyboard**\n- The arrow keys move through the “⋯” menu, like the other toolbar menus.",
                         "**Export in one tap**\n- With a list or a menu open, one tap on Export closes it and opens the export window, as the toolbar menus already did.",
                         "**Bottom tabs from the keyboard**\n- On a narrow screen, the arrow keys move between the bottom tabs, and each tab is tied to its section for screen readers.",
                         "**Fixed: every file is read safely**\n- In every tool, special keys such as __proto__ in a work file, a package, a route, a datacard file, a mission or what the browser kept are now ignored, as the Briefing Generator already did."],
        '### Home screen': ["**The Mission Plan insignia**\n- The home screen shows the Mission Plan insignia beside its title — on a phone, as a seal on the title's corner — and the family's icon in the top bar; when the Squadron Ready Room opens Mission Plan, your wing's emblem takes its place.\n- A *Squadron Ready Room family* line sits above the credits.",
                         "**Fixed: keyboard focus after choosing a theme**\n- After choosing a theme from “⋯” with the keyboard, or closing the list with Escape, the focus goes back to “⋯”."],
        '### Field Manual': ["**The home screen drawn with its insignia**\n- The two drawings of the home screen show the insignia and the family's icon.",
                         "**The phone drawing of the home screen in the right order**\n- The title plate now sits under the toolbar buttons, as on screen.",
                         "**Threats**\n- The Route Planner page explains the threats layer and lists the game’s air defence systems with their ranges and ceilings."],
    }
    for head_, es in entries.items():
        sec = unreleased.split('\n' + head_ + '\n', 1)[1].split('\n### ', 1)[0].rstrip('\n')
        assert sec.endswith('\n\n'.join(es)), head_


def test_fm_planches_draw_picto_and_crest():
    fm = page('dcs_field_manual')
    for aria in ('aria-label="L’accueil de Mission Plan, avec le menu Exemple ouvert"', 'aria-label="L’accueil de Mission Plan au téléphone"'):
        assert fm.count(aria) == 1, aria
        i = fm.index(aria)
        svg = fm[i:fm.index('</svg>', i)]
        assert svg.count('r="5" fill="none"') == 1, aria       # le pictogramme de la plaque de la barre
        assert svg.count('opacity=".10" stroke="currentColor" stroke-width="1.2"') == 1, aria   # l'écusson


# ----- L'écusson de l'accueil, dans le shell : ce que montre la plaque du titre selon le stockage, et sa taille selon la largeur -----
PNG_1PX = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=='
CREST_CASES = [
    ('virgin storage', None, 'mp'),
    ('managedBy and a PNG logo', {'managedBy': 'RR', 'wing': {'logo': PNG_1PX, 'fullName': 'Test Wing'}}, 'wing'),
    ('managedBy and an https: logo', {'managedBy': 'RR', 'wing': {'logo': 'https://example.org/logo.png'}}, 'rr'),
    ('HQ wing without managedBy', {'wing': {'logo': PNG_1PX, 'fullName': 'Test Wing'}}, 'mp'),
]


@pytest.fixture(scope='module')
def browser():
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        br = p.chromium.launch(executable_path=str(CHROMIUM), args=['--no-sandbox'])
        yield br
        br.close()


@needs_pw
@pytest.mark.parametrize('label,cfg,source', CREST_CASES)
def test_the_home_crest_shows_what_the_storage_says_at_three_sizes(browser, label, cfg, source):
    for w, size in ((345, '64px'), (412, '72px'), (1440, '120px')):
        ctx = browser.new_context(viewport={'width': w, 'height': 900})
        seed = "(() => { try { if (localStorage.getItem('lang_v1') === null) localStorage.setItem('lang_v1', 'en'); } catch (e) {} })();"
        ctx.add_init_script(seed + ("localStorage.setItem('wing_config_v1', %s);" % json.dumps(json.dumps(cfg)) if cfg else ''))
        ctx.route('**/*', lambda r: r.continue_() if r.request.url.startswith(('file:', 'data:', 'blob:')) else r.abort())
        pg = ctx.new_page()
        pg.goto('file://' + str(DIST / 'dcs_mission_plan.html'), wait_until='commit')
        pg.wait_for_function("() => !!document.getElementById('mp-crest') && !!document.getElementById('card-hq')", timeout=60000)
        try:
            pg.wait_for_function("([src, w]) => { const e = document.getElementById('mp-crest'); return !!e && e.getAttribute('data-source') === src && getComputedStyle(e).width === w && !!e.getAttribute('src'); }", arg=[source, size], timeout=10000)
        except Exception:
            pass                     # le diagnostic ci-dessous dit ce que la page montrait
        got = pg.evaluate("() => { const e = document.getElementById('mp-crest'); return !e ? null : [e.getAttribute('data-source'), getComputedStyle(e).width, (e.getAttribute('src') || '').slice(0, 14)]; }")
        assert got is not None and got[0] == source and got[1] == size and got[2], (label, w, got)
        if source == 'wing':
            assert got[2] == 'data:image/png'
        ctx.close()
