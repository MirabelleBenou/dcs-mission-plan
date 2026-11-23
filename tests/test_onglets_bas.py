"""La barre d'onglets du bas du Datacard Generator et du Briefing Generator (sept onglets de même largeur, sections repliables d'un onglet, toast au-dessus),
et les finitions du sélecteur d'outil (un toucher sur un autre menu, nom accessible). Joué sur le shell construit (dist/dcs_mission_plan.html, chromium, aucun réseau) ; les contrôles passent par le DOM."""
import re
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
SEED = "(() => { try { if (!sessionStorage.getItem('seeded')) { sessionStorage.setItem('seeded', '1'); localStorage.clear(); localStorage.setItem('lang_v1', '@@'); } } catch (e) {} })();"

DG_FR = [('mission', '▣', 'Mission'), ('group', '✈', 'Groupe'), ('nav', '🧭', 'Nav.'), ('radio', '📻', 'Radio'), ('weather', '☁', 'Météo'), ('meta', '⚙', 'Méta'), ('preview', '◈', 'Aperçu')]
BGS_EN = [('header', '▤', 'Header'), ('s-situation', '▣', 'Sitac'), ('s-mission', '✈', 'Mission'), ('s-coord', '📻', 'Coord.'), ('s-photos', '🖼', 'Photos'), ('meta', '⚙', 'Meta'), ('preview', '◈', 'Preview')]
BGF_FR = [('header', '▤', 'En-tête'), ('sitac', '▣', 'Sitac'), ('mission', '✈', 'Mission'), ('radio', '📻', 'Coord.'), ('annexes', '📎', 'Annexes'), ('meta', '⚙', 'Méta'), ('preview', '◈', 'Aperçu')]

DG_FM_FR = ' Au téléphone et à la tablette, l’éditeur passe en sept onglets au bas de l’écran ; un onglet qui regroupe plusieurs sections les montre chacune, repliable.'
DG_FM_EN = ' On a phone or tablet, the editor switches to seven tabs at the bottom of the screen; a tab that groups several sections shows each of them, foldable.'
BG_FM_FR = 'Au téléphone et à la tablette, l’éditeur passe en sept onglets au bas de l’écran ; au format Avancé, un onglet regroupe plusieurs sections, chacune repliable.'
BG_FM_EN = 'On a phone or tablet, the editor switches to seven tabs at the bottom of the screen; in Advanced, a tab groups several sections, each of them foldable.'


def test_the_texts_are_where_the_lot_says():
    log = (ROOT / 'CHANGELOG.md').read_text(encoding='utf-8')
    u = log.split('\n## Unreleased\n', 1)[1].split('\n## ', 1)[0]
    assert u.count('**Seven tabs at the bottom on a phone**') == 1 and u.count('**Switching tools: finishing touches**') == 1
    assert u.index('**Seven tabs') < u.index('**Switching tools: finishing') < u.index('### Home screen')
    assert re.search(r'^DEV_BUILD = 11$', (ROOT / 'version_block.py').read_text(encoding='utf-8'), re.M)
    fm = (ROOT / 'fm_planches_block.py').read_text(encoding='utf-8')
    for t in (DG_FM_FR, DG_FM_EN, BG_FM_FR, BG_FM_EN):
        assert fm.count(t) == 1
    assert 'Au téléphone, l’éditeur passe en onglets.' not in fm and 'the editor switches to tabs.' not in fm


@pytest.fixture(scope='module')
def browser():
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        br = p.chromium.launch(executable_path=str(CHROMIUM), args=['--no-sandbox'])
        yield br
        br.close()


def shell(br, w, h, touch=True, lang='fr'):
    kw = dict(has_touch=True, is_mobile=True) if touch else {}
    ctx = br.new_context(viewport={'width': w, 'height': h}, locale=lang + '-' + lang.upper(), **kw)
    ctx.add_init_script(SEED.replace('@@', lang))
    ctx.route('**/*', lambda r: r.continue_() if r.request.url.startswith(('file:', 'data:', 'blob:')) else r.abort())
    pg = ctx.new_page()
    errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(SHELL, wait_until='commit')
    pg.wait_for_function("() => typeof window.MP_WORK_EXAMPLE === 'function' && !!document.getElementById('card-hq')", timeout=60000)
    pg.wait_for_timeout(1300)
    for g in ('mc', 'fl'):
        pg.evaluate('(g) => window.MP_WORK_EXAMPLE(g)', g)
        pg.wait_for_timeout(700)
    pg.errs = errs
    return pg


def open_card(pg, tid, wait=2300):
    card = pg.locator('#card-' + tid)
    card.scroll_into_view_if_needed()
    card.click()
    pg.wait_for_selector('#iframe-' + tid, state='attached')
    pg.wait_for_timeout(wait)
    return pg.query_selector('#iframe-' + tid).content_frame()


BAR = """() => { const bar = document.getElementById('tab-bar'), br = bar.getBoundingClientRect(), W = document.documentElement.clientWidth;
  const bs = [...bar.querySelectorAll('[role=tab]')].filter(b => b.getClientRects().length);
  return { shown: getComputedStyle(bar).display !== 'none', role: bar.getAttribute('role'), h: br.height, scrolls: bar.scrollWidth > bar.clientWidth + 0.5,
    tabs: bs.map(b => { const r = b.getBoundingClientRect(), l = b.lastElementChild.getBoundingClientRect(); return { id: b.dataset.tab, ico: b.querySelector('.tab-ico').textContent, label: b.lastElementChild.textContent, w: r.width, h: r.height,
      fits: l.left >= r.left - 0.01 && l.right <= r.right + 0.01 && r.left >= -0.01 && r.right <= W + 0.01, sel: b.getAttribute('aria-selected'), cur: b.classList.contains('current') }; }) }; }"""


def check_bar(b, exp):
    assert b['shown'] and b['role'] == 'tablist' and abs(b['h'] - 68) < 0.01 and not b['scrolls']
    assert [(t['id'], t['ico'], t['label']) for t in b['tabs']] == exp
    ws = [t['w'] for t in b['tabs']]
    assert max(ws) - min(ws) <= 0.5 and all(t['fits'] and t['h'] >= 44 for t in b['tabs'])
    assert [t['sel'] for t in b['tabs']].count('true') == 1 and all((t['sel'] == 'true') == t['cur'] for t in b['tabs'])


@needs_pw
@pytest.mark.parametrize('w,h', [(345, 590), (412, 915), (820, 1180)])
def test_the_datacard_and_briefing_bars_have_seven_equal_tabs(browser, w, h):
    pg = shell(browser, w, h)
    f = open_card(pg, 'dg')
    check_bar(f.evaluate(BAR), DG_FR)
    pg.evaluate("() => { const f = document.querySelector('iframe:not([style*=\"display: none\"])'); f.contentDocument.querySelector('.mp-back-injected').click(); }")
    pg.wait_for_timeout(500)
    f = open_card(pg, 'bg')
    check_bar(f.evaluate(BAR), [('header', '▤', 'En-tête'), ('s-situation', '▣', 'Sitac'), ('s-mission', '✈', 'Mission'), ('s-coord', '📻', 'Coord.'), ('s-photos', '🖼', 'Photos'), ('meta', '⚙', 'Méta'), ('preview', '◈', 'Aperçu')])
    f.evaluate("() => setFormat('full')")
    pg.wait_for_timeout(400)
    check_bar(f.evaluate(BAR), BGF_FR)
    assert pg.errs == []


@needs_pw
def test_the_english_labels_and_no_bar_with_a_mouse(browser):
    pg = shell(browser, 345, 590, True, 'en')
    f = open_card(pg, 'bg')
    check_bar(f.evaluate(BAR), BGS_EN)
    pg2 = shell(browser, 1280, 800, False)
    g = open_card(pg2, 'dg')
    assert g.evaluate("() => getComputedStyle(document.getElementById('tab-bar')).display") == 'none'
    assert g.evaluate("() => document.documentElement.style.getPropertyValue('--mp-toast-bottom')") == ''
    assert pg.errs == [] and pg2.errs == []


SECS = """() => [...document.querySelectorAll('#editor details.ed-section')].filter(d => d.getClientRects().length).map(d => { const s = d.querySelector(':scope > summary');
  return { id: d.dataset.section, open: d.open, head: getComputedStyle(s).display !== 'none', icon: !!s.querySelector('.ui-foldic') }; })"""


@needs_pw
def test_a_tab_shows_its_sections_foldable_and_keeps_the_wide_screen_state(browser):
    pg = shell(browser, 412, 915)
    f = open_card(pg, 'dg')
    before = f.evaluate("() => localStorage.getItem('dg_folds_v1')")
    f.evaluate("() => document.querySelector('#tab-bar [data-tab=\"group\"]').click()")
    s = f.evaluate(SECS)
    assert [x['id'] for x in s] == ['group'] and not s[0]['head'] and s[0]['open'] and not s[0]['icon'] and f.evaluate("() => document.querySelectorAll('.panel-mobile-header').length") == 0
    f.evaluate("() => document.querySelector('#tab-bar [data-tab=\"nav\"]').click()")
    s = f.evaluate(SECS)
    assert [x['id'] for x in s] == ['nav', 'refs', 'fields'] and all(x['head'] and x['icon'] and x['open'] for x in s)
    f.evaluate("() => document.querySelector('#editor details[data-section=\"nav\"] > summary .ui-foldic').click()")
    pg.wait_for_timeout(300)
    assert [x['open'] for x in f.evaluate(SECS)] == [False, False, False]
    f.evaluate("() => document.querySelector('#tab-bar [data-tab=\"weather\"]').click()")
    assert all(x['open'] for x in f.evaluate(SECS))                 # « Tout replier » n'agit que sur les sections de l'onglet
    assert f.evaluate("() => localStorage.getItem('dg_folds_v1')") == before
    assert f.evaluate("() => JSON.parse(localStorage.getItem('dg_folds_tabs_v1'))") == {'nav': False, 'refs': False, 'fields': False}
    assert pg.errs == []


@needs_pw
def test_the_briefing_keeps_the_place_of_the_tab_when_the_format_changes_and_folds_meta_in_advanced(browser):
    pg = shell(browser, 412, 915)
    f = open_card(pg, 'bg')
    f.evaluate("() => setActiveTab('s-photos')")
    f.evaluate("() => setFormat('full')")
    assert f.evaluate("() => document.body.dataset.activeTab") == 'annexes'
    f.evaluate("() => setActiveTab('radio')")
    f.evaluate("() => setFormat('simple')")
    assert f.evaluate("() => document.body.dataset.activeTab") == 's-coord'
    f.evaluate("() => setFormat('full')")
    f.evaluate("() => setActiveTab('meta')")
    assert [(x['id'], x['open']) for x in f.evaluate(SECS)] == [('wing', True), ('meta', False)]
    assert f.evaluate("() => localStorage.getItem('bg_folds_v1')") is None
    assert pg.errs == []


@needs_pw
def test_the_toast_sits_12_px_above_the_bar(browser):
    pg = shell(browser, 345, 590)
    open_card(pg, 'dg')
    pg.evaluate("() => window.MP_WORK_EXAMPLE('fl')")
    pg.wait_for_timeout(450)
    t = pg.evaluate("() => { const r = document.getElementById('toast').getBoundingClientRect(); return { show: document.getElementById('toast').classList.contains('show'), bottom: r.bottom, vh: innerHeight }; }")
    assert t['show'] and abs((t['vh'] - 68) - t['bottom'] - 12) <= 1
    assert pg.errs == []


@needs_pw
def test_a_touch_on_another_toolbar_menu_opens_it_and_the_name_follows_the_language(browser):
    pg = shell(browser, 412, 915)
    f = open_card(pg, 'rp')
    f.locator('.toolbar .tb-brand').tap()
    pg.wait_for_timeout(350)
    assert f.evaluate("() => !!document.querySelector('.tb-sw-panel')")
    f.locator('#btn-open').tap()
    pg.wait_for_timeout(500)
    assert f.evaluate("() => !document.querySelector('.tb-sw-panel') && document.getElementById('btn-open').getAttribute('aria-expanded') === 'true'")
    f.evaluate("() => document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }))")
    pg.wait_for_timeout(250)
    name = "() => { const b = document.querySelector('.toolbar .tb-brand'); return [b.getAttribute('aria-label'), b.title, [...b.children].filter(c => getComputedStyle(c).display !== 'none').map(c => c.textContent.replace(/░/g, ' ').replace(/\\s+/g, ' ').trim()).join(' ')]; }"
    a = f.evaluate(name)
    assert a[0] == a[2] + ', changer d’outil' and a[1] == 'Changer d’outil'
    f.evaluate("() => document.getElementById('btn-lang').click()")
    pg.wait_for_timeout(500)
    b = f.evaluate(name)
    assert b[0] == b[2] + ', switch tool' and b[1] == 'Switch tool'
    assert pg.errs == []


TOUCH = "(s) => { const e = document.querySelector(s); e.dispatchEvent(new PointerEvent('pointerdown', { bubbles: true, pointerType: 'touch' })); e.dispatchEvent(new PointerEvent('pointerup', { bubbles: true, pointerType: 'touch' })); e.click(); }"       # la liste ouverte recouvre parfois le bouton : le geste est envoyé au bouton lui-même


@needs_pw
@pytest.mark.parametrize('tool,trig', [('rp', '#rs-more'), ('dg', '#pk-pick'), ('dg', '#pk-more')])
def test_a_content_button_does_not_open_from_an_open_list_or_more(browser, tool, trig):
    pg = shell(browser, 412, 915)
    f = open_card(pg, tool)
    st = "(s) => { const e = document.querySelector(s); return [e.getAttribute('aria-expanded'), !!document.querySelector('.tb-sw-panel'), !!document.querySelector('.tb-more-panel'), [...document.querySelectorAll('.tbm-panel:not(.tb-sw-panel):not(.tb-more-panel)')].filter(x => x.getClientRects().length).length]; }"
    f.locator('.toolbar .tb-brand').tap()
    pg.wait_for_timeout(350)
    f.evaluate(TOUCH, trig)
    pg.wait_for_timeout(500)
    a = f.evaluate(st, trig)
    assert a[0] in (None, 'false') and not a[1] and a[3] == 0, a
    f.locator('#tb-more-btn').tap()
    pg.wait_for_timeout(350)
    assert f.evaluate("() => !!document.querySelector('.tb-more-panel')")
    f.evaluate(TOUCH, trig)
    pg.wait_for_timeout(500)
    b = f.evaluate(st, trig)
    assert b[0] in (None, 'false') and not b[2] and b[3] == 0, b
    assert pg.errs == []
