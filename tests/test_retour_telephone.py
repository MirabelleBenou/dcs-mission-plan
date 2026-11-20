"""Le geste retour du téléphone, joué sur le shell construit (dist/dcs_mission_plan.html, chromium, aucun réseau) : il ferme un niveau à la fois
(menu ou fenêtre, puis l'outil, puis la page), l'historique n'a jamais plus de deux entrées au-dessus de celle du mur, l'adresse dit l'outil ouvert,
la question avant de quitter tient tant qu'une mission d'HQ est ouverte, le retour tiré-pour-actualiser est coupé. Les contrôles passent par le DOM et l'historique."""
import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
import miz_fixture  # noqa: E402

CHROMIUM = Path('/opt/pw-browsers/chromium')
try:
    import playwright.sync_api  # noqa: F401
    HAS_PW = CHROMIUM.exists()
except ImportError:
    HAS_PW = False
needs_pw = pytest.mark.skipif(not HAS_PW, reason='playwright ou chromium absent')

SHELL = 'file://' + str(ROOT / 'dist' / 'dcs_mission_plan.html')
TOOLS = ['hq', 'bg', 'rs', 'rp', 'dg', 'fc', 'fm']

TEXT_ALL = ("- On a phone, the back gesture or button closes one level at a time: an open menu or window first, then the tool, back to the suite's home screen; "
            "only from the home screen does it leave Mission Plan. The address names the open tool, so reloading reopens it. Pull-to-refresh is off.")
TEXT_HQ = "- While a mission is open, the browser asks before the page is closed, reloaded or left: the mission is not kept after that."
TEXT_FM_FR = ("Au téléphone, le geste retour ferme un niveau à la fois : d’abord le menu ou la fenêtre ouverts, puis l’outil, qui ramène à l’accueil de la suite ; "
              "depuis l’accueil seulement, il quitte Mission Plan. Tant qu’une mission d’HQ est ouverte, le navigateur demande avant de quitter ou de recharger la page.")
TEXT_FM_EN = ("On a phone, the back gesture closes one level at a time: first the open menu or window, then the tool, which takes you back to the suite’s home screen; "
              "only from the home screen does it leave Mission Plan. While an HQ mission is open, the browser asks before leaving or reloading the page.")


def test_texts_are_where_the_lot_says():
    log = (ROOT / 'CHANGELOG.md').read_text(encoding='utf-8')
    unreleased = log.split('## Unreleased', 1)[1].split('\n---\n', 1)[0]
    assert TEXT_ALL in unreleased.split('#### HQ', 1)[0]
    assert TEXT_HQ in unreleased.split('#### HQ', 1)[1].split('#### Flight Configurator', 1)[0]
    fm = (ROOT / 'build_field_manual.py').read_text(encoding='utf-8')
    i = fm.index('"La barre du haut", "The top bar"')
    j = fm.index('"Lire ce manuel au téléphone"', i)
    assert TEXT_FM_FR in fm[i:j] and TEXT_FM_EN in fm[i:j]


# ---------- le banc : une page vierge, puis le shell (un retour du mur a ainsi où aller) ----------
@pytest.fixture(scope='module')
def browser():
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        br = p.chromium.launch(executable_path=str(CHROMIUM), args=['--no-sandbox'])
        yield br
        br.close()


def new_page(br, w=412, h=900, touch=True, url=SHELL):
    ctx = br.new_context(viewport={'width': w, 'height': h}, has_touch=touch, is_mobile=touch)
    pg = ctx.new_page()
    errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.route('**/*', lambda r: r.continue_() if r.request.url.startswith(('file:', 'data:', 'blob:')) else r.abort())
    pg.goto('about:blank')
    pg.goto(url, wait_until='commit')
    pg.wait_for_function("typeof NAV !== 'undefined' && typeof openModule === 'function'", timeout=20000)
    pg.wait_for_timeout(1500)
    pg.errs = errs
    return pg


def state(pg):
    return pg.evaluate("""() => ({ state: history.state, hash: location.hash, wall: document.getElementById('landing').style.display !== 'none',
        tool: activeModule, level: navLevel(), idx: navigation.currentEntry.index, n: navigation.entries().length })""")


def back(pg, ms=700):
    pg.evaluate('history.back()')
    pg.wait_for_timeout(ms)


def tool_win(pg, tid, code):
    return pg.evaluate('([id, code]) => iframes[id].contentWindow.eval(code)', [tid, code])


def open_tool(pg, tid):
    pg.evaluate('(id) => openModule(id)', tid)
    pg.wait_for_timeout(2300)


def go_hub_by_arrow(pg, tid):
    pg.evaluate("(id) => iframes[id].contentDocument.querySelector('.mp-back-injected').click()", tid)
    pg.wait_for_timeout(700)


@needs_pw
@pytest.mark.parametrize('how', ['back', 'arrow'])
def test_each_tool_opens_one_entry_and_returns_to_the_wall(browser, how):
    pg = new_page(browser, 412, 600)
    base = state(pg)
    assert base['wall'] and not base['level'] and not base['hash']
    for tid in TOOLS:
        pg.evaluate('window.scrollTo(0, 250)')
        pg.wait_for_timeout(150)
        y0 = pg.evaluate('Math.round(window.scrollY)')
        assert y0 > 0
        open_tool(pg, tid)
        s = state(pg)
        assert s['tool'] == tid and s['hash'] == '#' + tid and s['state'] == {'mp': 1, 'tool': tid}
        assert s['idx'] - base['idx'] == 1
        if how == 'back':
            back(pg)
        else:
            go_hub_by_arrow(pg, tid)
        s = state(pg)
        assert s['wall'] and s['tool'] is None and s['hash'] == '' and s['idx'] == base['idx']
        assert pg.evaluate('Math.round(window.scrollY)') == y0          # le mur garde sa place
    back(pg)
    assert pg.url == 'about:blank'                                       # depuis le mur, le retour quitte la page
    assert pg.errs == []
    pg.context.close()


def level_cases():
    click = lambda sel: f"(() => {{ const e = document.querySelector({json.dumps(sel)}); if (!e) return 'NOEL'; e.click(); return 'ok'; }})()"
    return [
        ('hq', 'fenêtre Wing', click('#btn-wing'), '#wing-modal', 'esc'),
        ('hq', 'menu ⋯', click('#tb-more-btn'), '.tb-more-panel', 'esc'),
        ('hq', 'question', "askConfirm({ title: 'Q', text: 't', verb: 'OK', danger: true }); 'ok'", '#ui-confirm', 'cancel'),
        ('bg', 'menu ▾ Ouvrir', click('#btn-load'), '#op-panel', 'esc'),
        ('bg', 'question d\'Effacer', click('#btn-reset'), '#ui-confirm', 'cancel'),
        ('rs', 'nom de fichier', click('#btn-export'), '#fn-modal', 'x'),
        ('rp', 'panneau Affichage', click('#btn-display'), '.dsp-panel', 'esc'),
        ('rp', 'fiche', "ficheOpen('Nellis AFB', false); 'ok'", '#fiche', 'x'),
        ('dg', 'nom d\'export', click('#btn-json-export'), None, 'shell'),
        ('fc', 'nom de fichier', click('#btn-export'), '#fn-modal', 'x'),
        ('fm', 'sommaire', click('#btn-toc'), 'body.fmnav-open', 'esc'),
    ]


@needs_pw
@pytest.mark.parametrize('case', level_cases(), ids=lambda c: c[0] + ' ' + c[1])
def test_a_level_above_the_tool_closes_first(browser, case):
    tid, _name, opener, sel, own = case
    pg = new_page(browser, 412)
    pg.evaluate("MP_WORK_EXAMPLE('mc')")
    pg.wait_for_timeout(1300)
    pg.evaluate("MP_WORK_EXAMPLE('fl')")
    pg.wait_for_timeout(1800)
    open_tool(pg, tid)
    base = state(pg)
    keys = pg.evaluate('JSON.stringify(Object.keys(localStorage).sort().map(k => [k, localStorage.getItem(k).length]))')
    assert tool_win(pg, tid, opener) == 'ok'
    pg.wait_for_timeout(700)
    s = state(pg)
    assert s['level'] and s['state'] == {'mp': 2, 'tool': tid} and s['idx'] == base['idx'] + 1
    back(pg, 900)                                                           # le retour ferme le niveau, comme Échap : l'outil reste, rien n'est fait
    s = state(pg)
    assert not s['level'] and s['tool'] == tid and s['state'] == {'mp': 1, 'tool': tid} and s['idx'] == base['idx']
    assert pg.evaluate('JSON.stringify(Object.keys(localStorage).sort().map(k => [k, localStorage.getItem(k).length]))') == keys
    # le même niveau fermé par son propre geste : l'entrée est consommée, le retour suivant ramène au mur
    assert tool_win(pg, tid, opener) == 'ok'
    pg.wait_for_timeout(700)
    assert state(pg)['level']
    if own == 'esc':
        pg.keyboard.press('Escape')
    elif own == 'x':
        tool_win(pg, tid, f"document.querySelector({json.dumps(sel + ' .ui-close, ' + sel + ' .rt-close')}).click()")
    elif own == 'cancel':
        tool_win(pg, tid, "document.getElementById('ui-confirm-cancel').click()")
    else:
        pg.evaluate("document.getElementById('mp-work-close').click()")
    pg.wait_for_timeout(900)
    s = state(pg)
    assert not s['level'] and s['tool'] == tid and s['idx'] == base['idx']
    back(pg)
    assert state(pg)['wall']
    assert pg.errs == []
    pg.context.close()


@needs_pw
def test_a_question_over_a_window_closes_alone_and_the_entry_is_restored(browser):
    pg = new_page(browser, 412)
    open_tool(pg, 'hq')
    base = state(pg)
    tool_win(pg, 'hq', "document.getElementById('btn-wing').click()")
    pg.wait_for_timeout(600)
    tool_win(pg, 'hq', "askConfirm({ title: 'Q', text: 't', verb: 'OK', danger: true }); 1")
    pg.wait_for_timeout(600)
    assert state(pg)['idx'] == base['idx'] + 1                               # une fenêtre et une question : un seul niveau
    back(pg, 900)
    s = state(pg)
    assert tool_win(pg, 'hq', "document.getElementById('ui-confirm').hidden") is True
    assert tool_win(pg, 'hq', "document.getElementById('wing-modal').hidden") is False
    assert s['state'] == {'mp': 2, 'tool': 'hq'} and s['idx'] == base['idx'] + 1     # l'entrée du niveau 2 est rétablie
    back(pg, 900)
    assert tool_win(pg, 'hq', "document.getElementById('wing-modal').hidden") is True
    assert state(pg)['idx'] == base['idx'] and state(pg)['tool'] == 'hq'
    back(pg, 900)
    assert state(pg)['wall']
    pg.context.close()


@needs_pw
def test_never_more_than_two_entries_above_the_wall(browser):
    pg = new_page(browser, 412)
    wall = pg.evaluate('navigation.currentEntry.index')
    png = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
    worst = 0

    def check():
        nonlocal worst
        s = state(pg)
        worst = max(worst, s['idx'] - wall, s['n'] - 1 - wall)
    for tid in ['hq', 'bg', 'rs', 'rp', 'dg']:
        open_tool(pg, tid); check()
        go_hub_by_arrow(pg, tid); check()
    for tid in ['fc', 'fm', 'hq', 'bg', 'rs']:
        open_tool(pg, tid); check()
        back(pg, 800); check()
    open_tool(pg, 'rp'); check()
    tool_win(pg, 'rp', "document.getElementById('btn-export-menu').click()")
    pg.wait_for_timeout(600); check()
    pg.evaluate("MP_SEND_MAP({ dataUrl: %s, name: 't', theatre: 'caucasus', width: 1, height: 1 })" % json.dumps(png))
    pg.wait_for_timeout(2500); check()
    s = state(pg)
    assert s['tool'] == 'bg' and s['state'] == {'mp': 1, 'tool': 'bg'} and s['hash'] == '#bg'      # l'entrée est remplacée, non ajoutée
    back(pg, 800)
    assert state(pg)['wall']
    assert worst <= 2
    pg.context.close()


@needs_pw
def test_forward_onto_an_entry_that_says_more_than_the_screen_goes_back_silently(browser):
    pg = new_page(browser, 412)
    base = state(pg)
    open_tool(pg, 'hq')
    back(pg)
    pg.evaluate('history.forward()')
    pg.wait_for_timeout(900)
    s = state(pg)
    assert s['wall'] and s['idx'] == base['idx'] and not s['level']          # rien ne s'est rouvert
    open_tool(pg, 'hq')
    tool_win(pg, 'hq', "document.getElementById('btn-wing').click()")
    pg.wait_for_timeout(600)
    back(pg, 900)
    pg.evaluate('history.forward()')
    pg.wait_for_timeout(900)
    s = state(pg)
    assert s['tool'] == 'hq' and not s['level'] and s['state'] == {'mp': 1, 'tool': 'hq'}
    assert tool_win(pg, 'hq', "document.getElementById('wing-modal').hidden") is True
    pg.context.close()


@needs_pw
@pytest.mark.parametrize('what', ['tool', 'window', 'menu'])
def test_reload_reopens_the_tool_without_a_dead_entry(browser, what):
    pg = new_page(browser, 412)
    base = state(pg)
    tid = 'bg' if what == 'menu' else 'hq'
    open_tool(pg, tid)
    if what == 'window':
        tool_win(pg, tid, "document.getElementById('btn-wing').click()")
    elif what == 'menu':
        tool_win(pg, tid, "document.getElementById('btn-load').click()")
    pg.wait_for_timeout(600)
    pg.reload(wait_until='commit')
    pg.wait_for_function("typeof NAV !== 'undefined'", timeout=20000)
    pg.wait_for_timeout(2800)
    s = state(pg)
    assert s['tool'] == tid and not s['level'] and s['state'] == {'mp': 1, 'tool': tid} and s['hash'] == '#' + tid
    assert s['idx'] == base['idx'] + 1
    back(pg, 900)
    assert state(pg)['wall']                                                 # le premier retour fait quelque chose
    pg.context.close()


@needs_pw
@pytest.mark.parametrize('addr, tool', [('#hq', 'hq'), ('#fm', 'fm'), ('#zz', None), ('#HQ', None)])
def test_the_address_names_the_tool(browser, addr, tool):
    pg = new_page(browser, 412, url=SHELL + addr)
    pg.wait_for_timeout(1500)
    s = state(pg)
    assert s['tool'] == tool
    if tool:
        assert s['state'] == {'mp': 1, 'tool': tool} and s['hash'] == addr
        back(pg, 900)
        s = state(pg)
        assert s['wall'] and s['hash'] == ''
    else:
        assert s['wall'] and s['hash'] == ''                                 # inconnue : le mur, l'adresse nettoyée
    pg.context.close()


@needs_pw
def test_the_field_manual_pages_do_not_add_entries(browser):
    pg = new_page(browser, 412)
    base = state(pg)
    open_tool(pg, 'fm')
    tool_win(pg, 'fm', "document.getElementById('btn-toc').click()")
    pg.wait_for_timeout(500)
    assert state(pg)['level']
    tool_win(pg, 'fm', "document.querySelectorAll('#fmnav-panel a.fmnav-ch')[2].click()")
    pg.wait_for_timeout(900)
    assert tool_win(pg, 'fm', "location.hash") == '#hq'
    s = state(pg)
    assert not s['level'] and s['idx'] == base['idx'] + 1 and s['n'] - 1 - base['idx'] <= 2
    back(pg, 900)
    assert state(pg)['wall']
    pg.context.close()


@needs_pw
def test_the_browser_asks_before_leaving_only_while_an_hq_mission_is_open(browser, tmp_path):
    miz = tmp_path / 'essai.miz'
    miz_fixture.make(str(miz))
    pg = new_page(browser, 412)
    dialogs = []
    pg.on('dialog', lambda d: (dialogs.append(d.type), d.dismiss()))
    ctrl = pg.context.new_page()
    assert pg.evaluate("localStorage.getItem('mission_snapshot_v1')") is None
    pg.close(run_before_unload=True)
    ctrl.wait_for_timeout(800)
    assert pg.is_closed() and dialogs == []                                  # sans mission, aucune question
    pg = new_page(browser, 412)
    pg.on('dialog', lambda d: (dialogs.append(d.type), d.dismiss()))
    ctrl = pg.context.new_page()
    open_tool(pg, 'hq')
    hq = pg.query_selector('#iframe-hq').content_frame()
    hq.set_input_files('#miz-file-input', str(miz))
    pg.wait_for_timeout(3000)
    assert pg.evaluate("localStorage.getItem('mission_snapshot_v1')") is not None
    keys = pg.evaluate('JSON.stringify(Object.keys(localStorage).sort().map(k => [k, localStorage.getItem(k).length]))')
    pg.close(run_before_unload=True)
    ctrl.wait_for_timeout(800)
    assert dialogs == ['beforeunload'] and not pg.is_closed()                # « Rester » garde tout
    assert pg.evaluate('JSON.stringify(Object.keys(localStorage).sort().map(k => [k, localStorage.getItem(k).length]))') == keys
    assert state(pg)['tool'] == 'hq'
    # « Effacer » d'HQ retire la mission : plus de question
    dialogs.clear()
    tool_win(pg, 'hq', "document.getElementById('btn-clear').click()")
    pg.wait_for_timeout(600)
    tool_win(pg, 'hq', "document.getElementById('ui-confirm-ok').click()")
    pg.wait_for_timeout(1500)
    assert pg.evaluate("localStorage.getItem('mission_snapshot_v1')") is None
    pg.close(run_before_unload=True)
    ctrl.wait_for_timeout(800)
    assert pg.is_closed() and dialogs == []


@needs_pw
def test_pull_to_refresh_is_off_in_the_shell_and_every_tool(browser):
    pg = new_page(browser, 412)
    css = "(d) => [getComputedStyle(d.documentElement).overscrollBehaviorY, getComputedStyle(d.body).overscrollBehaviorY]"
    assert pg.evaluate("(" + css + ")(document)") == ['none', 'none']
    for tid in TOOLS:
        open_tool(pg, tid)
        assert pg.evaluate("(id) => (" + css + ")(iframes[id].contentDocument)", tid) == ['none', 'none'], tid
        pg.evaluate('goHub()')
        pg.wait_for_timeout(200)
    pg.context.close()
