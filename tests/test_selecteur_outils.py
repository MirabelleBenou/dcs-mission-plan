"""Changer d'outil depuis la barre, joué sur le shell construit (dist/dcs_mission_plan.html, chromium, aucun réseau) : la marque de la barre (le sigle, ou le titre) est un bouton « ▾ » qui ouvre la liste
des outils dans l'ordre de l'accueil ; choisir un outil l'affiche comme depuis l'accueil, avec son travail ; l'historique n'ajoute qu'une entrée ; le clavier parcourt la liste ; à 1 280 px aucun outil ne prend
une étape de plus de la barre. Les contrôles passent par le DOM."""
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
ORDER = ['hq', 'bg', 'rs', 'rp', 'dg', 'fc', 'fm']
NAME = {'hq': 'HQ', 'bg': 'Briefing Generator', 'rs': 'Recon Station', 'rp': 'Route Planner', 'dg': 'Datacard Generator', 'fc': 'Flight Configurator', 'fm': 'Field Manual'}
LIST = ['◄ Mission Plan', 'Mission Commander', 'HQ', 'Briefing Generator', 'Recon Station', 'Flight Leader', 'Route Planner', 'Datacard Generator', 'Flight Configurator', '', 'Field Manual']
# les étapes de la barre prises à 1 280 × 800 à la souris, avant le lot (le chevron ne doit en ajouter aucune) : le plus haut numéro d'étape pris par outil
BASE_STEPS_1280 = {'hq': 1, 'bg': 1, 'rs': 0, 'rp': 1, 'dg': 1, 'fc': 1, 'fm': 0}

CHANGELOG_ENTRY = ("**Switch tools from the toolbar**\n"
                   "- The tool’s name or abbreviation at the start of the toolbar, with ▾, opens the list of tools in the home screen’s order, the open one marked; one more touch opens another tool, which keeps its work.")
ENTRY_TABS = ("**Seven tabs at the bottom on a phone**\n"
              "- In the Briefing Generator and the Datacard Generator, the editor’s tabs all fit at the bottom of the screen, seven of the same width, in both formats of the briefing; a tab that groups several sections shows each of them, foldable, without repeating its title.")
ENTRY_TOUCHES = ("**Switching tools: finishing touches**\n"
                 "- With the list of tools or “⋯” open, a touch on another menu of the toolbar opens it; the tool’s name follows a language change at once and screen readers hear the name shown.")
ENTRY_INSIGNIA = ("**The Squadron Ready Room family insignia**\n"
                  "- Every page of the suite carries the family's icon in the browser tab and when pinned to a phone's home screen.\n"
                  "- The default wing logo, in HQ and the Briefing Generator, is now the Squadron Ready Room insignia; a wing still on the former “WG” logo shows the new one and still counts as not set up.")
ENTRY_NARROW = "**Fixed: “⋯” on very narrow screens**\n- Below 345 px wide, after the toolbar was scrolled, “⋯” could end up off the screen; it now stays in view."
ENTRY_MENUS = "**Menus easier to read from the keyboard**\n- In the toolbar's menus, the line reached with the arrow keys now has enough contrast in every theme."
ENTRY_LOT3 = ''.join('\n\n' + e for e in ["**Menus: the “Delete” line stands out**\n- In the Datacard Generator's and the Route Planner's menus, the “Delete” line under the pointer or reached with the arrow keys now turns red with dark text, readable in every theme.", "**The “⋯” menu from the keyboard**\n- The arrow keys move through the “⋯” menu, like the other toolbar menus.", "**Export in one tap**\n- With a list or a menu open, one tap on Export closes it and opens the export window, as the toolbar menus already did.", "**Bottom tabs from the keyboard**\n- On a narrow screen, the arrow keys move between the bottom tabs, and each tab is tied to its section for screen readers.", "**Fixed: every file is read safely**\n- In every tool, special keys such as __proto__ in a work file, a package, a route, a datacard file, a mission or what the browser kept are now ignored, as the Briefing Generator already did."])
ENTRY_KEYBOARD = ("**The tab bar steps aside for the keyboard**\n"
                  "- On a phone, while the on-screen keyboard is open, the tab bar at the bottom of the Briefing Generator, the Datacard Generator and the Route Planner hides, so the field you type in stays in view; in the Route Planner, a search on the map gets the whole height.")
FM_FR = ("Le nom de l’outil, ou son sigle, au début de la barre, ouvre la liste des outils (▾), dans l’ordre de l’accueil, l’outil ouvert marqué : un toucher de plus ouvre un autre outil, qui garde son travail. "
         "En tête de la liste, **◄ Mission Plan** ramène à l’accueil.")
FM_EN = ("The tool’s name, or its abbreviation, at the start of the bar opens the list of tools (▾), in the home screen’s order, the open tool marked: one more touch opens another tool, which keeps its work. "
         "At the top of the list, **◄ Mission Plan** goes back to the home screen.")
FM_BACK_FR = "Au téléphone, le geste retour ferme un niveau à la fois"


def test_texts_are_where_the_lot_says():
    log = (ROOT / 'CHANGELOG.md').read_text(encoding='utf-8')
    unreleased = log.split('\n## Unreleased\n', 1)[1].split('\n## ', 1)[0]
    all_tools = unreleased.split('\n### All tools\n', 1)[1].split('\n### ', 1)[0].rstrip('\n')
    assert all_tools.endswith('\n\n' + CHANGELOG_ENTRY + '\n\n' + ENTRY_TABS + '\n\n' + ENTRY_TOUCHES + '\n\n' + ENTRY_KEYBOARD + '\n\n' + ENTRY_INSIGNIA + '\n\n' + ENTRY_NARROW + '\n\n' + ENTRY_MENUS + ENTRY_LOT3)       # le lot mp-mobile-onglets ajoute ses deux entrées après celle-ci ; le lot du clavier la sienne, qui termine la rubrique
    assert 'MP-V2.1.0+16` for this one' in all_tools and 'MP-V2.1.0+3' not in all_tools
    fm = (ROOT / 'build_field_manual.py').read_text(encoding='utf-8')
    i = fm.index('"La barre du haut", "The top bar"')
    j = fm.index('"Lire ce manuel au téléphone"', i)
    seg = fm[i:j]
    assert seg.count(FM_FR) == 1 and seg.count(FM_EN) == 1
    assert seg.index(FM_BACK_FR) < seg.index(FM_FR) and seg.index('On a phone, the back gesture') < seg.index(FM_EN)
    assert seg[seg.index(FM_BACK_FR):seg.index(FM_FR)].count("('p',") == 1            # le paragraphe neuf suit aussitôt celui du geste retour
    assert re.search(r'^DEV_BUILD = 16$', (ROOT / 'version_block.py').read_text(encoding='utf-8'), re.M)
    assert 'MP-V2.1.0+16' in (ROOT / 'dist' / 'dcs_mission_plan.html').read_text(encoding='utf-8')


@pytest.fixture(scope='module')
def browser():
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        br = p.chromium.launch(executable_path=str(CHROMIUM), args=['--no-sandbox'])
        yield br
        br.close()


SEED = "(() => { try { if (!sessionStorage.getItem('seeded')) { sessionStorage.setItem('seeded', '1'); localStorage.clear(); localStorage.setItem('lang_v1', '@@'); } } catch (e) {} })();"


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
    for g in ('fl', 'mc'):
        pg.evaluate('(g) => window.MP_WORK_EXAMPLE(g)', g)
        pg.wait_for_timeout(700)
    pg.errs = errs
    return pg


def open_card(pg, tid, wait=2300):
    if tid == 'fm':
        pg.evaluate("() => document.getElementById('btn-fm').click()")
    else:
        card = pg.locator('#card-' + tid)
        card.scroll_into_view_if_needed()
        card.click()
    pg.wait_for_selector('#iframe-' + tid, state='attached')
    pg.wait_for_timeout(wait)
    return pg.query_selector('#iframe-' + tid).content_frame()


def to_wall(pg):
    pg.evaluate("() => { const f = document.querySelector('iframe:not([style*=\"display: none\"])'); const b = f && f.contentDocument.querySelector('.mp-back-injected'); if (b) b.click(); }")
    pg.wait_for_timeout(500)


def nav(pg):
    return pg.evaluate("""() => ({ active: activeModule, shown: Object.keys(iframes).filter(k => iframes[k].style.display !== 'none'), state: history.state, hash: location.hash,
        idx: navigation.currentEntry.index, wall: document.getElementById('landing').style.display !== 'none', y: Math.round(window.scrollY) })""")


def pick(pg, fr, name):
    fr.locator('.toolbar .tb-brand').click()
    pg.wait_for_timeout(300)
    fr.locator('.tb-sw-panel li.tbm-opt').filter(has_text=re.compile('^' + re.escape(name) + '$')).first.click()
    pg.wait_for_timeout(700)


@needs_pw
def test_the_mark_is_a_button_and_the_list_fits_without_scrolling(browser):
    pg = shell(browser, 345, 590)
    for tid in ORDER:
        fr = open_card(pg, tid)
        b = fr.evaluate("""() => { const e = document.querySelector('.toolbar .tb-brand'), r = e.getBoundingClientRect(), bar = document.querySelector('.toolbar').getBoundingClientRect();
            return { vis: [...e.children].filter(c => getComputedStyle(c).display !== 'none').map(c => c.textContent.replace(/░/g, ' ').replace(/\\s+/g, ' ').trim()).join(' '), role: e.getAttribute('role'), hp: e.getAttribute('aria-haspopup'), ex: e.getAttribute('aria-expanded'), name: e.getAttribute('aria-label'), title: e.title, tab: e.tabIndex, h: r.height,
                     inside: r.left >= bar.left && r.right <= bar.right, over: document.querySelector('.toolbar').classList.contains('tb-over'), sw: [document.querySelector('.toolbar').scrollWidth, document.querySelector('.toolbar').clientWidth],
                     prev: e.previousElementSibling && e.previousElementSibling.className } }""")
        assert b['role'] == 'button' and b['hp'] == 'menu' and b['ex'] == 'false' and b['name'] == b['vis'] + ', changer d’outil' and b['title'] == 'Changer d’outil' and b['tab'] == 0, (tid, b)
        assert b['h'] >= 43.99 and b['inside'] and not b['over'] and b['sw'][0] <= b['sw'][1], (tid, b)
        fr.locator('.toolbar .tb-brand').tap()
        pg.wait_for_timeout(350)
        r = fr.evaluate("""() => { const p = document.querySelector('.tb-sw-panel'), q = p.getBoundingClientRect(), lis = [...p.querySelectorAll('li')];
            return { ex: document.querySelector('.toolbar .tb-brand').getAttribute('aria-expanded'), inside: q.left >= 0 && q.right <= document.documentElement.clientWidth && q.bottom <= innerHeight, scroll: [p.scrollHeight, p.clientHeight],
                     texts: lis.map(li => li.classList.contains('tb-sw-sep') ? '' : li.textContent), h: lis.filter(li => li.classList.contains('tbm-opt')).map(li => Math.round(li.getBoundingClientRect().height)),
                     cur: lis.filter(li => li.getAttribute('aria-current') === 'page').map(li => li.textContent), marks: lis.filter(li => li.querySelector('.tbm-mark')).length,
                     groups: lis.filter(li => li.classList.contains('tbm-group')).length } }""")
        assert r['ex'] == 'true' and r['inside'] and r['scroll'][0] <= r['scroll'][1], (tid, r)
        assert r['texts'] == LIST and set(r['h']) == {44} and r['cur'] == [NAME[tid]] and r['marks'] == 1 and r['groups'] == 2, (tid, r)
        fr.locator('.toolbar .tb-brand').tap()
        pg.wait_for_timeout(250)
        assert not fr.evaluate("() => !!document.querySelector('.tb-sw-panel')")
        to_wall(pg)
    assert not pg.errs


@needs_pw
def test_choosing_a_tool_shows_it_with_its_work_and_adds_one_entry_only(browser):
    pg = shell(browser, 412, 915)
    pg.evaluate('window.scrollTo(0, 1500)')
    pg.wait_for_timeout(300)
    base = nav(pg)
    fr = open_card(pg, 'rp')
    wall_y = pg.evaluate('NAV.wallY')
    assert wall_y > 1000
    assert nav(pg)['idx'] - base['idx'] == 1
    pick(pg, fr, 'Datacard Generator')
    dg = pg.query_selector('#iframe-dg').content_frame()
    dg.locator('[data-path="meta.operation"]').fill('OPERATION TEST 42')
    dg.evaluate("() => document.querySelector('[data-path=\"meta.operation\"]').dispatchEvent(new Event('change', { bubbles: true }))")
    dg.evaluate("() => document.querySelectorAll('#tab-bar [role=tab]')[3].click()")
    pg.wait_for_timeout(400)
    dg.evaluate("() => { document.getElementById('editor').scrollTop = 300; }")
    pg.wait_for_timeout(250)
    top = dg.evaluate("() => Math.round(document.getElementById('editor').scrollTop)")
    assert top > 0
    pick(pg, dg, 'Flight Configurator')
    s = nav(pg)
    assert s['active'] == 'fc' and s['shown'] == ['fc'] and s['state'] == {'mp': 1, 'tool': 'fc'} and s['hash'] == '#fc' and s['idx'] - base['idx'] == 1
    fc = pg.query_selector('#iframe-fc').content_frame()
    pick(pg, fc, 'Route Planner')
    pick(pg, pg.query_selector('#iframe-rp').content_frame(), 'Datacard Generator')
    dg = pg.query_selector('#iframe-dg').content_frame()
    assert dg.evaluate("() => document.querySelector('[data-path=\"meta.operation\"]').value") == 'OPERATION TEST 42'
    assert dg.evaluate("() => [Math.round(document.getElementById('editor').scrollTop), [...document.querySelectorAll('#tab-bar [role=tab]')].findIndex(t => t.classList.contains('current'))]") == [top, 3]
    # la ligne de l'outil ouvert ne fait que fermer ; liste ouverte, le retour ne ferme qu'elle
    idx0 = nav(pg)['idx']
    pick(pg, dg, 'Datacard Generator')
    assert nav(pg)['active'] == 'dg' and nav(pg)['idx'] == idx0 and not dg.evaluate("() => !!document.querySelector('.tb-sw-panel')")
    dg.locator('.toolbar .tb-brand').click()
    pg.wait_for_timeout(500)
    pg.evaluate('history.back()')
    pg.wait_for_timeout(900)
    assert nav(pg)['active'] == 'dg' and not dg.evaluate("() => !!document.querySelector('.tb-sw-panel')")
    # un retour de plus : le mur, au défilement qu'il avait
    pg.evaluate('history.back()')
    pg.wait_for_timeout(1100)
    s = nav(pg)
    assert s['wall'] and s['active'] is None and s['idx'] == base['idx'] and abs(s['y'] - wall_y) <= 1 and s['state'] in (None, {'mp': 0})
    # « ◄ Mission Plan » fait ce que fait « ◄ »
    fr = open_card(pg, 'bg')
    pick(pg, fr, '◄ Mission Plan')
    s = nav(pg)
    assert s['wall'] and s['active'] is None and not s['hash']
    assert not pg.errs


@needs_pw
def test_keyboard_and_mouse_and_the_more_menu(browser):
    pg = shell(browser, 1280, 800, touch=False)
    fr = open_card(pg, 'bg')
    fr.evaluate("() => document.querySelector('.mp-back-injected').focus()")
    pg.keyboard.press('Tab')
    assert fr.evaluate("() => document.activeElement.classList.contains('tb-brand')")
    pg.keyboard.press('Enter')
    pg.wait_for_timeout(300)
    assert fr.evaluate("() => document.querySelector('.toolbar .tb-brand').getAttribute('aria-expanded')") == 'true'
    seq = [fr.evaluate('() => document.activeElement.textContent')]
    for _ in range(7):
        pg.keyboard.press('ArrowDown')
        seq.append(fr.evaluate('() => document.activeElement.textContent'))
    assert seq == ['◄ Mission Plan', 'HQ', 'Briefing Generator', 'Recon Station', 'Route Planner', 'Datacard Generator', 'Flight Configurator', 'Field Manual']
    pg.keyboard.press('ArrowDown')
    assert fr.evaluate('() => document.activeElement.textContent') == '◄ Mission Plan'
    for _ in range(3):
        pg.keyboard.press('ArrowDown')
    assert fr.evaluate('() => document.activeElement.textContent') == 'Recon Station'
    pg.keyboard.press('Enter')
    pg.wait_for_timeout(1800)
    assert nav(pg)['active'] == 'rs'
    rs = pg.query_selector('#iframe-rs').content_frame()
    rs.evaluate("() => document.querySelector('.toolbar .tb-brand').focus()")
    pg.keyboard.press('Enter')
    pg.wait_for_timeout(300)
    pg.keyboard.press('Escape')
    pg.wait_for_timeout(300)
    assert rs.evaluate("() => !document.querySelector('.tb-sw-panel') && document.activeElement.classList.contains('tb-brand')")
    rs.locator('.toolbar .tb-brand').click()
    pg.wait_for_timeout(300)
    pg.mouse.click(700, 500)
    pg.wait_for_timeout(400)
    assert rs.evaluate("() => !document.querySelector('.tb-sw-panel')")
    pg.context.close()
    # « ⋯ » ouvert (412 px, doigt) : la marque le ferme et ouvre la liste, et l'inverse
    pg = shell(browser, 412, 915)
    fr = open_card(pg, 'hq')
    st = "() => ({ more: !!document.querySelector('.tb-more-panel'), sw: !!document.querySelector('.tb-sw-panel'), n: document.querySelectorAll('.tbm-panel').length })"
    fr.locator('#tb-more-btn').tap()
    pg.wait_for_timeout(350)
    assert fr.evaluate(st) == {'more': True, 'sw': False, 'n': 1}
    fr.locator('.toolbar .tb-brand').tap()
    pg.wait_for_timeout(350)
    assert fr.evaluate(st) == {'more': False, 'sw': True, 'n': 1}
    fr.locator('#tb-more-btn').tap()
    pg.wait_for_timeout(350)
    assert fr.evaluate(st) == {'more': True, 'sw': False, 'n': 1}
    assert not pg.errs


GAP = """() => { const b = document.querySelector('.toolbar .tb-brand'); let n = b.nextElementSibling; while (n && getComputedStyle(n).display === 'none') n = n.nextElementSibling;
    return Math.round((n.getBoundingClientRect().left - b.getBoundingClientRect().right) * 100) / 100; }"""


@needs_pw
@pytest.mark.parametrize('lang', ['fr', 'en'])
def test_the_mark_adds_no_toolbar_step_at_1280(browser, lang):
    pg = shell(browser, 1280, 800, touch=False, lang=lang)
    for tid in ORDER:
        fr = open_card(pg, tid, 1800)
        pg.wait_for_timeout(500)
        top = fr.evaluate("""() => { const bar = document.querySelector('.toolbar'); return bar.classList.contains('tb-st8') ? 8 : bar.classList.contains('tb-st7') ? 7 : [...bar.classList].filter(x => /^tb-st[1-6]$/.test(x)).length; }""")
        assert top <= BASE_STEPS_1280[tid], (tid, top)
        assert fr.evaluate(GAP) >= 0.5, tid          # la zone de la marque ne chevauche pas l'élément suivant
        to_wall(pg)


@needs_pw
def test_the_mark_does_not_overlap_the_next_element_on_a_tablet(browser):
    pg = shell(browser, 820, 1180)
    for tid in ORDER:
        fr = open_card(pg, tid, 1800)
        pg.wait_for_timeout(400)
        assert fr.evaluate(GAP) >= 0.5, tid
        to_wall(pg)
