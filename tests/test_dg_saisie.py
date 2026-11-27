"""Saisir sur la datacard (Datacard Generator) : côte à côte (1 280 × 800), une case simple se modifie sur place et donne le même état qu'une saisie dans l'éditeur, Échap ne change rien,
une ligne de liste ouvre sa section au rang, une valeur que l'éditeur ne permet pas d'écrire ne devient pas un champ ; le HTML de l'aperçu ne porte rien de la saisie (S0) ; le clavier d'un écran
tactile ne ferme pas la saisie ; un redessin venu d'ailleurs la valide d'abord ; un seul clic valide et ouvre la case suivante ; au téléphone (412 × 915, au doigt), toucher une boîte fait paraître
« ✎ Modifier … », qui ouvre l'onglet et focalise le champ. Joué sur le shell construit (dist/dcs_mission_plan.html, chromium, aucun réseau) ; les contrôles passent par le DOM, jamais par une
capture, et chaque geste attend un état (tests/banc_attente.py), jamais une durée."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from banc_attente import attendre, attendre_images, attendre_outil, attendre_shell, exemple  # noqa: E402

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
TV = '#preview section[data-block="times"] .dc-tv'
# le HTML de l'aperçu, la rangée du bloc des balises retirée
NOB = """() => { const c = document.getElementById('preview').cloneNode(true);
  c.querySelectorAll('section.dc-block[data-block="beacons"]').forEach(b => b.closest('.dc-row').remove()); return c.innerHTML; }"""


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
    attendre_shell(pg, delai=60000)
    exemple(pg, 'fl')
    card = pg.locator('#card-dg')
    card.scroll_into_view_if_needed()
    card.tap() if touch else card.click()
    fr = attendre_outil(pg, 'dg', delai=30000)
    attendre(fr, "!!document.querySelector('#preview .dc-page') && dgMeasurable() && !DG_UI.needLayout && curCard().times.some(x => hasText(x.value))",
             "l'aperçu de l'exemple mesuré", delai=30000)
    css = '.toast, #toast, [class*="toast"] { display: none !important; }'
    pg.add_style_tag(content=css)
    fr.add_style_tag(content=css)
    return pg, fr


def value_is(fr, path, value):
    attendre(fr, "getPath(curCard(), arg[0]) === arg[1] && document.querySelector('#editor [data-path=\"' + arg[0] + '\"]').value === arg[1]",
             '%s = %r (état et éditeur)' % (path, value), lu="[getPath(curCard(), arg[0]), document.querySelector('#editor [data-path=\"' + arg[0] + '\"]').value]", arg=[path, value])


def editor_type(fr, path, value):
    """Une saisie dans le champ de l'éditeur : le texte tapé, puis la sortie du champ"""
    fr.evaluate("(p) => { const d = document.querySelector('#editor [data-path=\"' + p + '\"]').closest('details'); if (d && !d.open) d.open = true; }", path)
    f = fr.locator('#editor [data-path="%s"]' % path)
    f.scroll_into_view_if_needed()
    f.fill(value)
    f.press('Tab')
    value_is(fr, path, value)


def open_in_place(fr, target, n=None):
    fr.locator(target).first.click()
    attendre(fr, '!!DGE.ed && !!document.activeElement.closest(".dge-ed")', 'une saisie sur place ouverte, le focus dans son champ', lu='[!!DGE.ed, document.activeElement.tagName]')
    if n is not None:
        assert fr.evaluate("() => document.querySelectorAll('.dge-ed input, .dge-ed textarea').length") == n


def in_place(pg, fr, target, values, paths):
    """Un clic sur la case de l'aperçu, la saisie dans ses champs (Tab de l'un à l'autre), Entrée"""
    open_in_place(fr, target, len(values))
    for k, v in enumerate(values):
        if k:
            pg.keyboard.press('Tab')
            assert fr.evaluate("() => !!document.activeElement.closest('.dge-ed')")
        pg.keyboard.press('Control+A')
        pg.keyboard.type(v)
    pg.keyboard.press('Enter')
    attendre(fr, '!DGE.ed && document.querySelectorAll(".dge-ed, .dge-tip").length === 0', 'la saisie validée, le calque retiré')
    for p, v in zip(paths, values):
        value_is(fr, p, v)


CASES = [
    # (la case de l'aperçu, les chemins de l'éditeur, les valeurs saisies)
    (TV + ' >> nth=3', ['times.3.value'], ['10:19']),
    ('#preview section[data-block="weather"] .dc-wgrid .wp:nth-child(3) .wv', ['weather.qnh'], ['1009 hPa']),
    ('#preview .dc-head .dc-op', ['meta.operation', 'meta.mission'], ['DESERT FOX', 'M4']),
]


@pytest.mark.parametrize('target,paths,values', CASES, ids=['times', 'weather', 'operation-mission'])
def test_a_simple_value_changed_in_place_gives_the_editor_state(browser, target, paths, values):
    pg, fr = open_dg(browser, 1280, 800)
    assert not fr.evaluate("() => DG_TABS.matches")
    before = fr.evaluate(DOC)
    old = [fr.evaluate("(p) => document.querySelector('#editor [data-path=\"' + p + '\"]').value", p) for p in paths]
    in_place(pg, fr, target, values, paths)
    after = fr.evaluate(DOC)
    assert after != before
    for p, v in zip(paths, old):         # la valeur d'avant, puis la même saisie, par l'éditeur
        editor_type(fr, p, v)
    assert fr.evaluate(DOC) == before
    for p, v in zip(paths, values):
        editor_type(fr, p, v)
    assert fr.evaluate(DOC) == after
    assert pg.errs == []


def test_escape_changes_nothing(browser):
    pg, fr = open_dg(browser, 1280, 800)
    before = fr.evaluate(DOC)
    open_in_place(fr, TV + ' >> nth=1')
    pg.keyboard.press('Control+A')
    pg.keyboard.type('23:59')
    pg.keyboard.press('Escape')
    attendre(fr, '!DGE.ed && document.querySelectorAll(".dge-ed, .dge-tip").length === 0', 'la saisie annulée, le calque retiré')
    assert fr.evaluate(DOC) == before
    assert pg.errs == []


def test_the_preview_html_carries_nothing_of_the_editing(browser):
    """S0 : #preview, sans la rangée des balises, a le même HTML avant un survol, pendant et après, pendant une saisie, après une saisie annulée, après une saisie validée puis remise"""
    pg, fr = open_dg(browser, 1280, 800)
    ref = fr.evaluate(NOB)
    fr.locator('#preview section[data-block="times"]').hover()
    attendre(fr, 'document.querySelectorAll(".dge-box .dge-pen").length === 1', 'le contour et le ✎ du survol posés')
    assert fr.evaluate(NOB) == ref
    pg.mouse.move(2, 2)
    attendre(fr, 'document.querySelectorAll(".dge-box").length === 0', 'le survol retiré')
    assert fr.evaluate(NOB) == ref
    open_in_place(fr, TV + ' >> nth=0')
    assert fr.evaluate(NOB) == ref
    pg.keyboard.press('Control+A')
    pg.keyboard.type('23:59')
    pg.keyboard.press('Escape')
    attendre(fr, '!DGE.ed', 'la saisie annulée')
    assert fr.evaluate(NOB) == ref
    old = fr.evaluate("() => curCard().times[0].value")
    in_place(pg, fr, TV + ' >> nth=0', ['23:59'], ['times.0.value'])
    assert fr.evaluate(NOB) != ref
    in_place(pg, fr, TV + ' >> nth=0', [old], ['times.0.value'])
    pg.mouse.move(2, 2)
    attendre(fr, 'document.querySelectorAll(".dge-box").length === 0', 'le survol retiré')
    assert fr.evaluate(NOB) == ref
    assert pg.errs == []


def test_a_crew_line_opens_its_section_at_its_row(browser):
    pg, fr = open_dg(browser, 1280, 800)
    before = fr.evaluate(DOC)
    fr.locator('#preview section[data-block="crew"] tbody tr').nth(1).click()
    attendre(fr, "document.querySelector('#ed-sections > details[data-section=\"group\"]').open && !!document.activeElement.closest('#editor .li')",
             'la section Groupe ouverte, le focus dans une ligne', lu='document.activeElement.tagName')
    assert fr.evaluate("() => document.querySelectorAll('.dge-ed, .dge-tip').length") == 0          # une liste ne se modifie pas sur place
    row = fr.evaluate("() => { const li = document.activeElement.closest('#editor .li'); return li ? [li.dataset.unit || null, li.dataset.list || null, li.dataset.i || null] : null; }")
    assert row in (['1', None, None], [None, 'crew', '1'])                # carte liée : l'unité 2 ; carte libre : la ligne 2
    assert fr.evaluate(DOC) == before
    assert pg.errs == []


def test_a_read_only_value_does_not_become_a_field(browser):
    pg, fr = open_dg(browser, 1280, 800)
    assert fr.evaluate("() => dgFuelView(curCard()) !== null")             # l'exemple : carburant et poids calculés d'après le FC
    before = fr.evaluate(DOC)
    fr.locator('#preview section[data-block="fuel"] .dc-fuel .fv').first.click()
    attendre(fr, "document.querySelector('#ed-sections > details[data-section=\"fuel\"]').open && !!document.activeElement.closest('#ed-sections > details[data-section=\"fuel\"]')",
             'la section Carburant ouverte, le focus dedans', lu='document.activeElement.tagName')
    assert fr.evaluate("() => document.querySelectorAll('.dge-ed').length") == 0
    assert fr.evaluate(DOC) == before
    assert pg.errs == []


def test_the_touch_keyboard_keeps_the_field_open(browser):
    """Côte à côte, au doigt : le clavier d'un écran tactile réduit la hauteur du cadre ; la saisie reste ouverte, la frappe s'écrit"""
    pg, fr = open_dg(browser, 1280, 800, touch=True)
    assert not fr.evaluate("() => DG_TABS.matches")
    fr.locator(TV).nth(0).tap()
    attendre(fr, '!!DGE.ed && !!document.activeElement.closest(".dge-ed")', 'une saisie sur place ouverte')
    pg.set_viewport_size({'width': 1280, 'height': 470})
    attendre(fr, 'innerHeight < 600', 'le cadre réduit en hauteur', lu='innerHeight')
    attendre_images(fr, 3)                                                  # l'évènement resize est passé
    assert fr.evaluate("() => !!DGE.ed && !!document.activeElement.closest('.dge-ed')")
    pg.keyboard.press('Control+A')
    pg.keyboard.type('07:07')
    pg.keyboard.press('Enter')
    attendre(fr, '!DGE.ed', 'la saisie validée')
    value_is(fr, 'times.0.value', '07:07')
    assert pg.errs == []


def test_a_redraw_from_elsewhere_commits_the_field_first(browser):
    """Le shell change la langue pendant une saisie sur place : la frappe est écrite, le calque retiré"""
    pg, fr = open_dg(browser, 1280, 800)
    open_in_place(fr, TV + ' >> nth=0')
    pg.keyboard.press('Control+A')
    pg.keyboard.type('05:55')
    fr.evaluate("() => setLang('en')")
    attendre(fr, "CURRENT_LANG === 'en' && !DGE.ed", 'la langue changée, la saisie fermée')
    assert fr.evaluate(OVERLAY) == 0
    value_is(fr, 'times.0.value', '05:55')
    assert fr.evaluate("() => JSON.parse(localStorage.getItem('datacard_state_v1')).cards[curIdx].times[0].value") == '05:55'
    assert pg.errs == []


def test_one_click_commits_and_opens_the_next_box(browser):
    pg, fr = open_dg(browser, 1280, 800)
    open_in_place(fr, TV + ' >> nth=1')
    pg.keyboard.press('Control+A')
    pg.keyboard.type('09:46')
    fr.locator('#preview section[data-block="weather"] .dc-wgrid .wp:nth-child(1)').click()
    attendre(fr, "!!DGE.ed && DGE.ed.paths[0] === 'weather.wind' && !!document.activeElement.closest('.dge-ed')", 'la case Vent ouverte sur place, du même clic',
             lu='DGE.ed && DGE.ed.paths')
    value_is(fr, 'times.1.value', '09:46')
    assert pg.errs == []


def test_on_a_phone_a_touched_box_gets_its_button(browser):
    pg, fr = open_dg(browser, 412, 915, touch=True)
    assert fr.evaluate("() => DG_TABS.matches")
    fr.locator('#tab-bar button[data-tab="preview"]').tap()
    attendre(fr, "document.body.dataset.activeTab === 'preview'", "l'onglet Aperçu")
    before = fr.evaluate(DOC)
    fr.locator(TV).nth(2).tap()
    attendre(fr, "!!document.querySelector('.dge-go')", 'le bouton paru')
    assert fr.evaluate("() => document.querySelectorAll('.dge-ed').length") == 0          # rien ne s'écrit sur place
    btn = fr.evaluate("() => { const b = document.querySelector('.dge-go'); const r = b.getBoundingClientRect(), z = document.querySelector('#preview section[data-block=\"times\"]').getBoundingClientRect(); return { text: b.textContent, h: r.height, below: r.top >= z.bottom - 1 }; }")
    assert btn['text'] == '✎ Modifier HORAIRES' and btn['h'] >= 44 and btn['below']
    fr.locator('.dge-go').tap()
    attendre(fr, "document.body.dataset.activeTab === 'mission' && document.activeElement.dataset.path === 'times.2.value'", "l'onglet Mission, le champ focalisé",
             lu='[document.body.dataset.activeTab, document.activeElement.dataset.path]')
    assert fr.evaluate(OVERLAY) == 0
    assert fr.evaluate(DOC) == before
    assert pg.errs == []
