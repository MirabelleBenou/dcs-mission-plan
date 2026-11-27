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
from banc_attente import attendre, attendre_navigation_stable, attendre_outil, attendre_python, attendre_shell, exemple  # noqa: E402

CHROMIUM = Path('/opt/pw-browsers/chromium')
try:
    import playwright.sync_api  # noqa: F401
    HAS_PW = CHROMIUM.exists()
except ImportError:
    HAS_PW = False
needs_pw = pytest.mark.skipif(not HAS_PW, reason='playwright ou chromium absent')

SHELL = 'file://' + str(ROOT / 'dist' / 'dcs_mission_plan.html')
TOOLS = ['hq', 'bg', 'rs', 'rp', 'dg', 'fc', 'fm']

TEXT_ALL_1 = "- The back gesture or button closes an open menu or window first, then the tool, back to the suite's home screen; only from the home screen does it leave Mission Plan."
TEXT_ALL_2 = "- The address names the open tool, so reloading reopens it. Pull-to-refresh is off."
TEXT_HQ = "- The browser asks before the page is closed, reloaded or left: the mission is not kept after that."
TEXT_FM_FR = ("Au téléphone, le geste retour ferme un niveau à la fois : d’abord le menu ou la fenêtre ouverts, puis l’outil, qui ramène à l’accueil de la suite ; "
              "depuis l’accueil seulement, il quitte Mission Plan. Tant qu’une mission d’HQ est ouverte, le navigateur demande avant de quitter ou de recharger la page.")
TEXT_FM_EN = ("On a phone, the back gesture closes one level at a time: first the open menu or window, then the tool, which takes you back to the suite’s home screen; "
              "only from the home screen does it leave Mission Plan. While an HQ mission is open, the browser asks before leaving or reloading the page.")


def test_texts_are_where_the_lot_says():
    log = (ROOT / 'CHANGELOG.md').read_text(encoding='utf-8')
    unreleased = log.split('\n## Unreleased\n', 1)[1].split('\n## ', 1)[0]
    all_tools = unreleased.split('\n### All tools\n', 1)[1].split('\n### ', 1)[0].splitlines()
    assert all_tools.index(TEXT_ALL_1) + 1 == all_tools.index(TEXT_ALL_2)
    hq = unreleased.split('\n### HQ\n', 1)[1].split('\n### ', 1)[0]
    assert hq.count(TEXT_HQ) == 1 and unreleased.count(TEXT_HQ) == 1
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


NO_NAV_API = "if (window.top !== window) { try { Object.defineProperty(window, 'navigation', { value: undefined, configurable: true }); } catch (e) {} }"


def new_page(br, w=412, h=900, touch=True, url=SHELL, no_nav_api=False):
    ctx = br.new_context(viewport={'width': w, 'height': h}, has_touch=touch, is_mobile=touch)
    if no_nav_api:                                  # les cadres des outils sans l'API de navigation (Safari avant 26.2, Firefox avant 147) ; le shell la garde, pour lire ses entrées
        ctx.add_init_script(NO_NAV_API)
    ctx.add_init_script("window.addEventListener('popstate', () => { window.__pop = (window.__pop || 0) + 1; });")          # compte les retours reçus par la page : le geste est arrivé
    pg = ctx.new_page()
    errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.route('**/*', lambda r: r.continue_() if r.request.url.startswith(('file:', 'data:', 'blob:')) else r.abort())
    pg.goto('about:blank')
    pg.goto(url, wait_until='commit')
    attendre_shell(pg)
    if url != SHELL and url[len(SHELL):] in ('#hq', '#fm'):                         # l'adresse nomme un outil : il s'ouvre à la suite
        attendre_outil(pg, url[len(SHELL) + 1:])
    attendre_navigation_stable(pg)
    pg.errs = errs
    return pg


def state(pg):
    return pg.evaluate("""() => ({ state: history.state, hash: location.hash, wall: document.getElementById('landing').style.display !== 'none',
        tool: activeModule, level: navLevel(), idx: navigation.currentEntry.index, n: navigation.entries().length })""")


def back(pg):
    """Le geste retour : attend que la page l'ait reçu (popstate) puis que la navigation soit au repos."""
    pg.evaluate('() => { window.__pop0 = window.__pop || 0; history.back(); }')
    attendre(pg, '(window.__pop || 0) > window.__pop0', 'le retour reçu par la page (popstate)', lu='[window.__pop, window.__pop0]')
    attendre_navigation_stable(pg)


def forward(pg):
    pg.evaluate('() => { window.__pop0 = window.__pop || 0; history.forward(); }')
    attendre(pg, '(window.__pop || 0) > window.__pop0', "l'avance reçue par la page (popstate)", lu='[window.__pop, window.__pop0]')
    attendre_navigation_stable(pg)


def leave(pg):
    """Le retour depuis le mur quitte la page : l'adresse devient about:blank."""
    pg.evaluate('history.back()')
    pg.wait_for_url('about:blank')


def tool_attendre(pg, tid, expr, etat):
    """Attend qu'une expression évaluée dans le cadre de l'outil soit vraie."""
    attendre(pg, 'iframes[arg[0]].contentWindow.eval(arg[1])', etat, lu='iframes[arg[0]].contentWindow.eval(arg[1])', arg=[tid, expr])


def tool_win(pg, tid, code):
    return pg.evaluate('([id, code]) => iframes[id].contentWindow.eval(code)', [tid, code])


def open_tool(pg, tid):
    pg.evaluate('(id) => openModule(id)', tid)
    attendre_outil(pg, tid)
    attendre_navigation_stable(pg)


def go_hub_by_arrow(pg, tid):
    pg.evaluate("(id) => iframes[id].contentDocument.querySelector('.mp-back-injected').click()", tid)
    attendre(pg, "document.getElementById('landing').style.display !== 'none' && activeModule === null", 'le mur affiché, aucun outil ouvert', lu="[document.getElementById('landing').style.display, activeModule]")
    attendre_navigation_stable(pg)


@needs_pw
@pytest.mark.parametrize('how', ['back', 'arrow'])
def test_each_tool_opens_one_entry_and_returns_to_the_wall(browser, how):
    pg = new_page(browser, 412, 600)
    base = state(pg)
    assert base['wall'] and not base['level'] and not base['hash']
    for tid in TOOLS:
        pg.evaluate('window.scrollTo(0, 250)')
        attendre(pg, 'Math.round(window.scrollY) > 0', 'le mur défilé (scrollY > 0)', lu='window.scrollY')
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
    leave(pg)
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
    exemple(pg, 'mc')
    exemple(pg, 'fl')
    open_tool(pg, tid)
    base = state(pg)
    keys = pg.evaluate('JSON.stringify(Object.keys(localStorage).sort().map(k => [k, localStorage.getItem(k).length]))')
    assert tool_win(pg, tid, opener) == 'ok'
    attendre(pg, '!!navLevel()', 'un niveau ouvert au-dessus de l\'outil (navLevel)', lu='navLevel()')
    attendre_navigation_stable(pg)
    s = state(pg)
    assert s['level'] and s['state'] == {'mp': 2, 'tool': tid} and s['idx'] == base['idx'] + 1
    back(pg)                                                           # le retour ferme le niveau, comme Échap : l'outil reste, rien n'est fait
    s = state(pg)
    assert not s['level'] and s['tool'] == tid and s['state'] == {'mp': 1, 'tool': tid} and s['idx'] == base['idx']
    assert pg.evaluate('JSON.stringify(Object.keys(localStorage).sort().map(k => [k, localStorage.getItem(k).length]))') == keys
    # le même niveau fermé par son propre geste : l'entrée est consommée, le retour suivant ramène au mur
    assert tool_win(pg, tid, opener) == 'ok'
    attendre(pg, '!!navLevel()', 'un niveau ouvert au-dessus de l\'outil (navLevel)', lu='navLevel()')
    attendre_navigation_stable(pg)
    assert state(pg)['level']
    if own == 'esc':
        pg.keyboard.press('Escape')
    elif own == 'x':
        tool_win(pg, tid, f"document.querySelector({json.dumps(sel + ' .ui-close, ' + sel + ' .rt-close')}).click()")
    elif own == 'cancel':
        tool_win(pg, tid, "document.getElementById('ui-confirm-cancel').click()")
    else:
        pg.evaluate("document.getElementById('mp-work-close').click()")
    attendre(pg, '!navLevel()', 'le niveau fermé par son propre geste (navLevel nul)', lu='navLevel()')
    attendre_navigation_stable(pg)
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
    tool_attendre(pg, 'hq', "document.getElementById('wing-modal').hidden === false", 'la fenêtre Wing ouverte')
    attendre_navigation_stable(pg)
    tool_win(pg, 'hq', "askConfirm({ title: 'Q', text: 't', verb: 'OK', danger: true }); 1")
    tool_attendre(pg, 'hq', "document.getElementById('ui-confirm').hidden === false", 'la question ouverte')
    attendre_navigation_stable(pg)
    assert state(pg)['idx'] == base['idx'] + 1                               # une fenêtre et une question : un seul niveau
    back(pg)
    s = state(pg)
    assert tool_win(pg, 'hq', "document.getElementById('ui-confirm').hidden") is True
    assert tool_win(pg, 'hq', "document.getElementById('wing-modal').hidden") is False
    assert s['state'] == {'mp': 2, 'tool': 'hq'} and s['idx'] == base['idx'] + 1     # l'entrée du niveau 2 est rétablie
    back(pg)
    assert tool_win(pg, 'hq', "document.getElementById('wing-modal').hidden") is True
    assert state(pg)['idx'] == base['idx'] and state(pg)['tool'] == 'hq'
    back(pg)
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
        back(pg); check()
    open_tool(pg, 'rp'); check()
    tool_win(pg, 'rp', "document.getElementById('btn-export-menu').click()")
    attendre(pg, '!!navLevel()', 'le menu Exporter ouvert (navLevel)', lu='navLevel()')
    attendre_navigation_stable(pg); check()
    pg.evaluate("MP_SEND_MAP({ dataUrl: %s, name: 't', theatre: 'caucasus', width: 1, height: 1 })" % json.dumps(png))
    attendre_outil(pg, 'bg')                                                                # la carte envoyée ouvre le Briefing Generator
    attendre_navigation_stable(pg); check()
    s = state(pg)
    assert s['tool'] == 'bg' and s['state'] == {'mp': 1, 'tool': 'bg'} and s['hash'] == '#bg'      # l'entrée est remplacée, non ajoutée
    back(pg)
    assert state(pg)['wall']
    assert worst <= 2
    pg.context.close()


@needs_pw
def test_forward_onto_an_entry_that_says_more_than_the_screen_goes_back_silently(browser):
    pg = new_page(browser, 412)
    base = state(pg)
    open_tool(pg, 'hq')
    back(pg)
    forward(pg)
    s = state(pg)
    assert s['wall'] and s['idx'] == base['idx'] and not s['level']          # rien ne s'est rouvert
    open_tool(pg, 'hq')
    tool_win(pg, 'hq', "document.getElementById('btn-wing').click()")
    tool_attendre(pg, 'hq', "document.getElementById('wing-modal').hidden === false", 'la fenêtre Wing ouverte')
    attendre_navigation_stable(pg)
    back(pg)
    forward(pg)
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
    if what != 'tool':
        attendre(pg, '!!navLevel()', 'un niveau ouvert au-dessus de l\'outil (navLevel)', lu='navLevel()')
        attendre_navigation_stable(pg)
    pg.reload(wait_until='commit')
    attendre_shell(pg)
    attendre_outil(pg, tid)                                                  # l'adresse rouvre l'outil
    attendre_navigation_stable(pg)
    s = state(pg)
    assert s['tool'] == tid and not s['level'] and s['state'] == {'mp': 1, 'tool': tid} and s['hash'] == '#' + tid
    assert s['idx'] == base['idx'] + 1
    back(pg)
    assert state(pg)['wall']                                                 # le premier retour fait quelque chose
    pg.context.close()


@needs_pw
@pytest.mark.parametrize('addr, tool', [('#hq', 'hq'), ('#fm', 'fm'), ('#zz', None), ('#HQ', None)])
def test_the_address_names_the_tool(browser, addr, tool):
    pg = new_page(browser, 412, url=SHELL + addr)
    s = state(pg)
    assert s['tool'] == tool
    if tool:
        assert s['state'] == {'mp': 1, 'tool': tool} and s['hash'] == addr
        back(pg)
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
    attendre(pg, '!!navLevel()', 'le sommaire ouvert (navLevel)', lu='navLevel()')
    attendre_navigation_stable(pg)
    assert state(pg)['level']
    tool_win(pg, 'fm', "document.querySelectorAll('#fmnav-panel a.fmnav-ch')[2].click()")
    tool_attendre(pg, 'fm', "location.hash === '#hq'", 'la page HQ du manuel ouverte (adresse #hq)')
    attendre_navigation_stable(pg)
    assert tool_win(pg, 'fm', "location.hash") == '#hq'
    s = state(pg)
    assert not s['level'] and s['idx'] == base['idx'] + 1 and s['n'] - 1 - base['idx'] <= 2
    back(pg)
    assert state(pg)['wall']
    pg.context.close()


@needs_pw
def test_the_field_manual_pages_do_not_add_entries_without_the_navigation_api(browser):
    pg = new_page(browser, 412, no_nav_api=True)
    open_tool(pg, 'fm')
    assert tool_win(pg, 'fm', 'typeof navigation') == 'undefined'
    base = state(pg)
    tool_win(pg, 'fm', "document.getElementById('btn-toc').click()")
    tool_attendre(pg, 'fm', "document.body.classList.contains('fmnav-open')", 'le sommaire ouvert')
    tool_win(pg, 'fm', "document.querySelectorAll('#fmnav-panel a.fmnav-ch')[2].click()")      # le sommaire, puis le lien du bas de chapitre, un lien du texte, navigate(), le sommaire encore
    tool_attendre(pg, 'fm', "location.hash === '#hq'", 'la page HQ du manuel ouverte (adresse #hq)')
    attendre_navigation_stable(pg)
    assert tool_win(pg, 'fm', 'location.hash') == '#hq'
    tool_win(pg, 'fm', "(document.querySelector('.fmnav-pn a.fmnav-nx:not([hidden])') || document.querySelector('.fmnav-pn a')).click()")
    attendre_navigation_stable(pg)
    tool_win(pg, 'fm', "(document.querySelector('a.fm-lnk') || { click() {} }).click()")
    attendre_navigation_stable(pg)
    tool_win(pg, 'fm', "navigate('index')")
    tool_attendre(pg, 'fm', "location.hash === '#index'", 'la page Index du manuel ouverte (adresse #index)')
    attendre_navigation_stable(pg)
    assert tool_win(pg, 'fm', 'location.hash') == '#index'
    tool_win(pg, 'fm', "document.getElementById('btn-toc').click()")
    tool_attendre(pg, 'fm', "document.body.classList.contains('fmnav-open')", 'le sommaire ouvert')
    tool_win(pg, 'fm', "document.querySelectorAll('#fmnav-panel a.fmnav-ch')[1].click()")
    tool_attendre(pg, 'fm', "!document.body.classList.contains('fmnav-open')", 'le sommaire refermé par le choix d\'un chapitre')
    attendre_navigation_stable(pg)
    s = state(pg)
    assert s['state'] == {'mp': 1, 'tool': 'fm'} and not s['level']
    assert s['idx'] == base['idx'] and s['n'] == base['n'] + 1                 # seule reste l'entrée « en avant » du niveau 2 consommé : aucune page n'a ajouté d'entrée
    assert pg.evaluate('navigation.entries().filter(e => e.getState() && e.getState().mp === 0).length') == 0     # aucune entrée {mp:0} en double
    back(pg)
    assert state(pg)['wall'] and state(pg)['state'] is None
    leave(pg)
    assert pg.url == 'about:blank'
    assert pg.errs == []
    pg.context.close()


@needs_pw
def test_the_arrow_after_field_manual_pages_goes_back_to_the_wall_without_the_navigation_api(browser):
    pg = new_page(browser, 412, no_nav_api=True)
    open_tool(pg, 'fm')
    for k in (1, 2, 3):
        tool_win(pg, 'fm', "document.getElementById('btn-toc').click()")
        tool_attendre(pg, 'fm', "document.body.classList.contains('fmnav-open')", 'le sommaire ouvert')
        tool_win(pg, 'fm', "document.querySelectorAll('#fmnav-panel a.fmnav-ch')[%d].click()" % k)
        tool_attendre(pg, 'fm', "!document.body.classList.contains('fmnav-open')", "le sommaire refermé par le choix d'un chapitre")
        attendre_navigation_stable(pg)
    go_hub_by_arrow(pg, 'fm')
    s = state(pg)
    assert s['wall'] and s['state'] is None
    leave(pg)
    assert pg.url == 'about:blank'
    pg.context.close()


@needs_pw
def test_a_window_closes_by_its_cross_never_by_escape(browser):
    pg = new_page(browser, 412)
    open_tool(pg, 'rs')
    tool_win(pg, 'rs', "SOURCE_READY = true; RSD.tool = 'rect'; rsdSyncUi(); 1")            # une image, l'outil de dessin Rectangle
    tool_win(pg, 'rs', "document.getElementById('btn-reset').click()")
    tool_attendre(pg, 'rs', "document.getElementById('ui-confirm').hidden === false", 'la question ouverte')
    attendre_navigation_stable(pg)
    assert tool_win(pg, 'rs', "document.getElementById('ui-confirm').hidden") is False
    back(pg)
    assert tool_win(pg, 'rs', "document.getElementById('ui-confirm').hidden") is True
    assert tool_win(pg, 'rs', 'RSD.tool') == 'rect'                                         # Échap l'aurait remis à « select »
    assert tool_win(pg, 'rs', 'SOURCE_READY') is True                                        # rien d'effacé
    back(pg)
    assert state(pg)['wall']
    pg.context.close()


@needs_pw
@pytest.mark.parametrize('tid, opener, win', [
    ('hq', "document.getElementById('btn-wing').click()", 'wing-modal'),
    ('fc', "document.getElementById('btn-export').click()", 'fn-modal'),
])
def test_a_back_that_skips_two_entries_closes_the_levels_one_by_one_down_to_the_wall(browser, tid, opener, win):
    pg = new_page(browser, 412)
    if tid == 'fc':                                    # le Flight Configurator exporte une fois une mission chargée
        exemple(pg, 'mc')
        exemple(pg, 'fl')
    open_tool(pg, tid)
    tool_win(pg, tid, opener)
    tool_attendre(pg, tid, "document.getElementById('%s').hidden === false" % win, 'la fenêtre ouverte')
    attendre_navigation_stable(pg)
    tool_win(pg, tid, "askConfirm({ title: 'Q', text: 't', verb: 'OK', danger: true }); 1")
    tool_attendre(pg, tid, "document.getElementById('ui-confirm').hidden === false", 'la question ouverte')
    attendre_navigation_stable(pg)
    assert tool_win(pg, tid, "document.getElementById('%s').hidden" % win) is False
    assert state(pg)['state'] == {'mp': 2, 'tool': tid}
    pg.evaluate('() => { window.__pop0 = window.__pop || 0; history.go(-2); }')
    attendre(pg, '!navLevel() && activeModule === null', 'les niveaux fermés un à un jusqu\'au mur (navLevel nul, aucun outil)', lu='[navLevel(), activeModule, window.__pop, window.__pop0]')
    attendre_navigation_stable(pg)
    s = state(pg)
    assert s['wall'] and s['state'] is None and not s['level']
    assert pg.errs == []
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
    attendre_python(ctrl, lambda: pg.is_closed(), 'la page fermée sans question')
    assert pg.is_closed() and dialogs == []                                  # sans mission, aucune question
    pg = new_page(browser, 412)
    pg.on('dialog', lambda d: (dialogs.append(d.type), d.dismiss()))
    ctrl = pg.context.new_page()
    open_tool(pg, 'hq')
    hq = pg.query_selector('#iframe-hq').content_frame()
    hq.set_input_files('#miz-file-input', str(miz))
    attendre(pg, "localStorage.getItem('mission_snapshot_v1') !== null", 'la mission chargée dans HQ (instantané enregistré)', lu="localStorage.getItem('mission_snapshot_v1') === null", delai=30000)
    assert pg.evaluate("localStorage.getItem('mission_snapshot_v1')") is not None
    keys = pg.evaluate('JSON.stringify(Object.keys(localStorage).sort().map(k => [k, localStorage.getItem(k).length]))')
    pg.close(run_before_unload=True)
    attendre_python(ctrl, lambda: dialogs == ['beforeunload'], 'la question du navigateur posée (beforeunload)')
    assert dialogs == ['beforeunload'] and not pg.is_closed()                # « Rester » garde tout
    assert pg.evaluate('JSON.stringify(Object.keys(localStorage).sort().map(k => [k, localStorage.getItem(k).length]))') == keys
    assert state(pg)['tool'] == 'hq'
    # « Effacer » d'HQ retire la mission : plus de question
    dialogs.clear()
    tool_win(pg, 'hq', "document.getElementById('btn-clear').click()")
    tool_attendre(pg, 'hq', "document.getElementById('ui-confirm').hidden === false", 'la question ouverte')
    tool_win(pg, 'hq', "document.getElementById('ui-confirm-ok').click()")
    attendre(pg, "localStorage.getItem('mission_snapshot_v1') === null", 'la mission retirée (instantané effacé)', lu="localStorage.getItem('mission_snapshot_v1') === null")
    attendre_navigation_stable(pg)
    pg.close(run_before_unload=True)
    attendre_python(ctrl, lambda: pg.is_closed(), 'la page fermée sans question')
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
        attendre(pg, "document.getElementById('landing').style.display !== 'none' && activeModule === null", 'le mur affiché, aucun outil ouvert', lu="[document.getElementById('landing').style.display, activeModule]")
    pg.context.close()
