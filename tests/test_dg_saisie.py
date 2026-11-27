"""Saisir sur la datacard (Datacard Generator) : côte à côte (1 280 × 800), une case simple se modifie sur place et donne le même état qu'une saisie dans l'éditeur, Échap ne change rien,
une ligne de liste ouvre sa section au rang, une valeur que l'éditeur ne permet pas d'écrire ne devient pas un champ ; au téléphone (412 × 915, au doigt), toucher une boîte fait paraître
« ✎ Modifier … », qui ouvre l'onglet et focalise le champ. Joué sur le shell construit (dist/dcs_mission_plan.html, chromium, aucun réseau) ; les contrôles passent par le DOM, jamais par une capture."""
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
CHROMIUM = Path('/opt/pw-browsers/chromium')
try:
    import playwright.sync_api  # noqa: F401
    HAS_PW = CHROMIUM.exists()
except ImportError:
    HAS_PW = False
pytestmark = pytest.mark.skipif(not HAS_PW, reason='playwright ou chromium absent')
SHELL = 'file://' + str(ROOT / 'dist' / 'dcs_mission_plan.html')
SEED = "(() => { try { if (localStorage.getItem('lang_v1') === null) localStorage.setItem('lang_v1', '@@'); } catch (e) {} })();"
DOC = '() => JSON.stringify(doc)'
OVERLAY = "() => document.querySelectorAll('.dge-ed, .dge-tip, .dge-box, .dge-go').length"


@pytest.fixture(scope='module')
def browser():
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        br = p.chromium.launch(executable_path=str(CHROMIUM), args=['--no-sandbox'])
        yield br
        br.close()


CONTEXTS = []


@pytest.fixture(autouse=True)
def close_contexts():
    yield
    while CONTEXTS:
        try:
            CONTEXTS.pop().close()
        except Exception:
            pass


def open_dg(br, w, h, touch=False, lang='fr'):
    kw = dict(has_touch=True, is_mobile=True) if touch else {}
    ctx = br.new_context(viewport={'width': w, 'height': h}, locale=lang + '-' + lang.upper(), **kw)
    ctx.add_init_script(SEED.replace('@@', lang))
    ctx.route('**/*', lambda r: r.continue_() if r.request.url.startswith(('file:', 'data:', 'blob:')) else r.abort())
    CONTEXTS.append(ctx)
    pg = ctx.new_page()
    pg.errs = []
    pg.on('pageerror', lambda e: pg.errs.append(str(e)[:200]))
    pg.goto(SHELL, wait_until='commit')
    pg.wait_for_function("() => typeof window.MP_WORK_EXAMPLE === 'function' && !!document.getElementById('card-dg')", timeout=60000)
    pg.wait_for_timeout(1300)
    pg.evaluate("() => window.MP_WORK_EXAMPLE('fl')")
    pg.wait_for_timeout(900)
    card = pg.locator('#card-dg')
    card.scroll_into_view_if_needed()
    card.tap() if touch else card.click()
    pg.wait_for_selector('#iframe-dg', state='attached')
    pg.wait_for_timeout(2600)
    fr = pg.query_selector('#iframe-dg').content_frame()
    fr.wait_for_function("() => !!document.querySelector('#preview .dc-page')", timeout=30000)
    css = '.toast, #toast, [class*="toast"] { display: none !important; }'
    pg.add_style_tag(content=css)
    fr.add_style_tag(content=css)
    return pg, fr


def editor_type(pg, fr, path, value):
    """Une saisie dans le champ de l'éditeur : le texte tapé, puis la sortie du champ"""
    f = fr.locator('#editor [data-path="%s"]' % path)
    f.scroll_into_view_if_needed()
    f.fill(value)
    f.press('Tab')
    pg.wait_for_timeout(250)


def in_place(pg, fr, target, values):
    """Un clic sur la case de l'aperçu, la saisie dans ses champs (Tab de l'un à l'autre), Entrée"""
    fr.locator(target).first.click()
    pg.wait_for_timeout(250)
    n = fr.evaluate("() => document.querySelectorAll('.dge-ed input, .dge-ed textarea').length")
    assert n == len(values)
    for k, v in enumerate(values):
        if k:
            pg.keyboard.press('Tab')
        assert fr.evaluate("() => !!document.activeElement.closest('.dge-ed')")
        pg.keyboard.press('Control+A')
        pg.keyboard.type(v)
    pg.keyboard.press('Enter')
    pg.wait_for_timeout(300)
    assert fr.evaluate(OVERLAY) == 0


CASES = [
    # (la case de l'aperçu, les chemins de l'éditeur, les valeurs saisies)
    ('#preview section[data-block="times"] .dc-trow:nth-child(4) .dc-tv', ['times.3.value'], ['10:19']),
    ('#preview section[data-block="weather"] .dc-wgrid .wp:nth-child(3) .wv', ['weather.qnh'], ['1009 hPa']),
    ('#preview .dc-head .dc-op', ['meta.operation', 'meta.mission'], ['DESERT FOX', 'M4']),
]


@pytest.mark.parametrize('target,paths,values', CASES, ids=['times', 'weather', 'operation-mission'])
def test_a_simple_value_changed_in_place_gives_the_editor_state(browser, target, paths, values):
    pg, fr = open_dg(browser, 1280, 800)
    assert not fr.evaluate("() => DG_TABS.matches")
    before = fr.evaluate(DOC)
    old = [fr.evaluate("(p) => document.querySelector('#editor [data-path=\"' + p + '\"]').value", p) for p in paths]
    in_place(pg, fr, target, values)
    after = fr.evaluate(DOC)
    assert after != before
    assert [fr.evaluate("(p) => getPath(curCard(), p)", p) for p in paths] == values
    assert [fr.evaluate("(p) => document.querySelector('#editor [data-path=\"' + p + '\"]').value", p) for p in paths] == values      # l'éditeur suit
    for p, v in zip(paths, old):         # la valeur d'avant, puis la même saisie, par l'éditeur
        editor_type(pg, fr, p, v)
    assert fr.evaluate(DOC) == before
    for p, v in zip(paths, values):
        editor_type(pg, fr, p, v)
    assert fr.evaluate(DOC) == after
    assert pg.errs == []


def test_escape_changes_nothing(browser):
    pg, fr = open_dg(browser, 1280, 800)
    before = fr.evaluate(DOC)
    fr.locator('#preview section[data-block="times"] .dc-tv').nth(1).click()
    pg.wait_for_timeout(250)
    assert fr.evaluate("() => document.activeElement.closest('.dge-ed') !== null")
    pg.keyboard.press('Control+A')
    pg.keyboard.type('23:59')
    pg.keyboard.press('Escape')
    pg.wait_for_timeout(300)
    assert fr.evaluate(OVERLAY) == 0
    assert fr.evaluate(DOC) == before
    assert pg.errs == []


def test_a_crew_line_opens_its_section_at_its_row(browser):
    pg, fr = open_dg(browser, 1280, 800)
    before = fr.evaluate(DOC)
    fr.locator('#preview section[data-block="crew"] tbody tr').nth(1).click()
    pg.wait_for_timeout(300)
    assert fr.evaluate("() => document.querySelectorAll('.dge-ed, .dge-tip').length") == 0          # une liste ne se modifie pas sur place
    assert fr.evaluate("() => document.querySelector('#ed-sections > details[data-section=\"group\"]').open")
    row = fr.evaluate("() => { const li = document.activeElement.closest('#editor .li'); return li ? [li.dataset.unit || null, li.dataset.list || null, li.dataset.i || null] : null; }")
    assert row in (['1', None, None], [None, 'crew', '1'])                # carte liée : l'unité 2 ; carte libre : la ligne 2
    assert fr.evaluate(DOC) == before
    assert pg.errs == []


def test_a_read_only_value_does_not_become_a_field(browser):
    pg, fr = open_dg(browser, 1280, 800)
    assert fr.evaluate("() => dgFuelView(curCard()) !== null")             # l'exemple : carburant et poids calculés d'après le FC
    before = fr.evaluate(DOC)
    fr.locator('#preview section[data-block="fuel"] .dc-fuel .fv').first.click()
    pg.wait_for_timeout(300)
    assert fr.evaluate("() => document.querySelectorAll('.dge-ed').length") == 0
    assert fr.evaluate("() => document.querySelector('#ed-sections > details[data-section=\"fuel\"]').open")
    assert fr.evaluate("() => !!document.activeElement.closest('#ed-sections > details[data-section=\"fuel\"]')")
    assert fr.evaluate(DOC) == before
    assert pg.errs == []


def test_on_a_phone_a_touched_box_gets_its_button(browser):
    pg, fr = open_dg(browser, 412, 915, touch=True)
    assert fr.evaluate("() => DG_TABS.matches")
    fr.locator('#tab-bar button[data-tab="preview"]').tap()
    pg.wait_for_timeout(400)
    before = fr.evaluate(DOC)
    fr.locator('#preview section[data-block="times"] .dc-tv').nth(2).tap()
    pg.wait_for_timeout(300)
    assert fr.evaluate("() => document.querySelectorAll('.dge-ed').length") == 0          # rien ne s'écrit sur place
    btn = fr.evaluate("() => { const b = document.querySelector('.dge-go'); const r = b.getBoundingClientRect(), z = document.querySelector('#preview section[data-block=\"times\"]').getBoundingClientRect(); return { text: b.textContent, h: r.height, below: r.top >= z.bottom - 1 }; }")
    assert btn['text'] == '✎ Modifier HORAIRES' and btn['h'] >= 44 and btn['below']
    fr.locator('.dge-go').tap()
    pg.wait_for_timeout(400)
    assert fr.evaluate("() => document.body.dataset.activeTab") == 'mission'
    assert fr.evaluate("() => document.activeElement.dataset.path") == 'times.2.value'
    assert fr.evaluate(OVERLAY) == 0
    assert fr.evaluate(DOC) == before
    assert pg.errs == []
