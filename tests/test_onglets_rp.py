"""Le Route Planner au téléphone : la carte toujours visible, le panneau en quatre onglets (Route · Réf. · Calques · Nav.) dans la barre basse commune,
le partage carte / panneau, la ligne de point sur deux lignes sous 520 px, le toast au-dessus de la barre. Joué sur le shell construit (dist/dcs_mission_plan.html,
chromium, aucun réseau) ; les contrôles passent par le DOM, jamais par une capture."""
import re
import sys
import warnings
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from banc_attente import (attendre, attendre_fenetre, attendre_images, attendre_lecture_stable, attendre_mise_en_page, attendre_outil, attendre_rp,  # noqa: E402
                          attendre_shell, attendre_toast_parti, exemple)
CHROMIUM = Path('/opt/pw-browsers/chromium')
try:
    import playwright.sync_api  # noqa: F401
    HAS_PW = CHROMIUM.exists()
except ImportError:
    HAS_PW = False
needs_pw = pytest.mark.skipif(not HAS_PW, reason='playwright ou chromium absent')
SHELL = 'file://' + str(ROOT / 'dist' / 'dcs_mission_plan.html')
# Le contexte neuf a un stockage vide : l'amorce pose la langue si elle manque et n'efface rien. (Si le stockage repart vide à un rechargement, toutes les clés ensemble, avec celle de la poignée, ce n'est pas l'amorce
# ni l'application : c'est le contexte en mémoire du banc, que `reopen` remet comme il était avant de juger.)
SEED = "(() => { try { if (localStorage.getItem('lang_v1') === null) localStorage.setItem('lang_v1', '@@'); } catch (e) {} })();"

TABS = {'fr': [('route', '⟿', 'Route'), ('refs', '◆', 'Réf.'), ('layers', '▧', 'Calques'), ('nav', '🧭', 'Nav.')],
        'en': [('route', '⟿', 'Route'), ('refs', '◆', 'Ref.'), ('layers', '▧', 'Layers'), ('nav', '🧭', 'Nav.')]}
EMPTY = {'fr': 'Aucun calque. Ouvrir ▾ › Ouvrir une route ou des calques… lit un fichier CombatFlite ; le mode Dessin crée les vôtres.',
         'en': 'No layers. Open ▾ › Open a route or layers… reads a CombatFlite file; Draw mode creates your own.'}
HELP = {'fr': 'En mode Lire, touchez un objet pour lire sa fiche.', 'en': 'In Read mode, tap an item to read it.'}
ARIA = {'fr': 'Panneau du Route Planner', 'en': 'Route Planner panel'}

# fenêtre (au doigt) : H, carte, panneau (barre de 68, poignée de 44, haut du contenu à 60)
SPLIT = [(345, 590, 418, 220, 198), (360, 780, 608, 316.2, 291.8), (412, 915, 743, 386.4, 356.6), (716, 646, 474, 246.5, 227.5),
         (780, 582, 410, 213.2, 196.8), (820, 1180, 1008, 524.2, 483.8), (915, 412, 240, 140, 100), (1100, 800, 628, 326.6, 301.4)]

FM_FR = ('Sur grand écran, le panneau est à gauche et la carte à droite. Au téléphone ou à la tablette, la carte reste fixe au-dessus du panneau, qui passe en quatre onglets au bas de l’écran : '
         'Route, Réf., Calques et Nav. ; une poignée entre la carte et le panneau agrandit ou réduit la carte, et deux touchers la remettent à sa taille. '
         'Quand le clavier de l’écran s’ouvre sur un champ du panneau, la carte se réduit le temps de la saisie.')
FM_EN = ('On a big screen, the panel is on the left and the map on the right. On a phone or tablet, the map stays fixed above the panel, which switches to four tabs at the bottom of the screen: '
         'Route, Ref., Layers and Nav.; a handle between map and panel enlarges or shrinks the map, and a double tap resets its size. '
         'When the on-screen keyboard opens on a panel field, the map shrinks for the time of the entry.')
LEG_FR = ' Au téléphone et à la tablette, chaque section a son onglet au bas de l’écran.'
LEG_EN = ' On a phone or tablet, each section has its own tab at the bottom of the screen.'
LOG_TABS = ('**Tabs at the bottom on a phone**\n'
            '- On a phone or tablet, the map stays in view above the panel, which now has four tabs at the bottom of the screen — Route, Ref., Layers and Nav. — in the same bar as the Briefing and Datacard Generators; '
            'map and panel start at about half the screen each, and the handle still resizes them.\n'
            '- Below 520 px wide, a waypoint row takes two lines, the name on the first, altitude, speed and reference on the second; with a finger, its text is 16 px.\n')
LOG_PAREN = '(between 520 and 760 px wide, the Route Planner’s waypoint rows still use smaller text)'


def test_the_texts_are_where_the_lot_says():
    log = (ROOT / 'CHANGELOG.md').read_text(encoding='utf-8')
    u = log.split('\n## Unreleased\n', 1)[1].split('\n## ', 1)[0]
    rp = u.split('\n### Route Planner\n', 1)[1].split('\n### ', 1)[0]
    assert u.count(LOG_TABS) == 1 and LOG_TABS.rstrip('\n') in rp
    assert u.count(LOG_PAREN) == 1 and '(the Route Planner’s waypoint rows still use smaller text)' not in log
    fm = (ROOT / 'build_field_manual.py').read_text(encoding='utf-8')
    assert fm.count(FM_FR) == 1 and fm.count(FM_EN) == 1 and 'qui seul défile' not in fm[fm.index('"Sur tablette et téléphone"'):fm.index('"Sur tablette et téléphone"') + 900]
    pl = (ROOT / 'fm_planches_block.py').read_text(encoding='utf-8')
    assert pl.count('replie toutes les sections ou les déplie toutes. Voir plus bas.' + LEG_FR + "'],") == 1
    assert pl.count('folds all the sections or unfolds them all. See below.' + LEG_EN + "']),") == 1
    src = (ROOT / 'build_route_planner.py').read_text(encoding='utf-8')
    assert '1099' not in src and src.count("'layers.empty': '%s'," % EMPTY['fr']) == 1 and src.count("'layers.empty': '%s'," % EMPTY['en']) == 1
    for lang, key in (('fr', 'Panneau du Route Planner'), ('en', 'Route Planner panel')):
        assert src.count("'tab.bar.aria': '%s'," % key) == 1
        for _id, _ico, label in TABS[lang]:
            assert src.count("'tab.%s': '%s'," % (_id, label)) >= 1


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
    attendre_shell(pg, 60000)
    for g in ('mc', 'fl'):
        exemple(pg, g)
    pg.errs = errs
    return pg


def open_card(pg, tid):
    card = pg.locator('#card-' + tid)
    card.scroll_into_view_if_needed()
    card.click()
    pg.wait_for_selector('#iframe-' + tid, state='attached')
    if tid == 'rp':                                                               # la carte créée, puis la mise en page (partage carte / panneau, barre d'onglets) posée
        fr = attendre_rp(pg)
        attendre_mise_en_page(fr)
        return fr
    fr = attendre_outil(pg, tid)
    attendre_images(fr, 3)
    return fr


def rp(br, w, h, touch=True, lang='fr'):
    pg = shell(br, w, h, touch, lang)
    return pg, open_card(pg, 'rp')


def back(pg):
    pg.evaluate("() => { const f = document.querySelector('iframe:not([style*=\"display: none\"])'); f.contentDocument.querySelector('.mp-back-injected').click(); }")
    attendre(pg, "document.getElementById('landing').style.display !== 'none' && activeModule === null", 'le mur affiché, aucun outil ouvert', lu="[document.getElementById('landing').style.display, activeModule]")


TOOL_IDS = {'Datacard Generator': 'dg', 'Route Planner': 'rp', 'Briefing Generator': 'bg'}


def pick(pg, fr, name):
    """Choisit un outil dans la liste de la marque ; les actions du locator attendent la liste et ses lignes, puis l'outil choisi est ouvert (et, pour le Route Planner, remis en page)."""
    fr.locator('.toolbar .tb-brand').click()
    fr.locator('.tb-sw-panel li.tbm-opt').filter(has_text=re.compile('^' + re.escape(name) + '$')).first.click()
    tid = TOOL_IDS[name]
    nf = attendre_outil(pg, tid)
    if tid == 'rp':
        attendre_mise_en_page(nf)
    else:
        attendre_images(nf, 3)


def tab(fr, tid):
    fr.evaluate("(id) => document.querySelector('#tab-bar [data-tab=\"' + id + '\"]').click()", tid)
    attendre(fr, "document.body.dataset.activeTab === arg && document.querySelector('#tab-bar [data-tab=\"' + arg + '\"]').getAttribute('aria-selected') === 'true' "
                 "&& [...document.querySelectorAll('#panel > .ed-section')].filter(s => s.getClientRects().length > 0).map(s => s.dataset.section).join() === arg",
             "l'onglet %s seul affiché (data-active-tab, aria-selected, sections visibles)" % tid,
             lu="[document.body.dataset.activeTab, [...document.querySelectorAll('#panel > .ed-section')].filter(s => s.getClientRects().length > 0).map(s => s.dataset.section).join()]", arg=tid)
    attendre_images(fr, 2)


GEOM = """() => { const r = s => { const e = document.querySelector(s); if (!e || !e.getClientRects().length) return null; const b = e.getBoundingClientRect(); return { top: b.top, h: b.height, w: b.width, bottom: b.bottom }; };
  return { map: r('.mapwrap'), split: r('#rp-split'), panel: r('#panel'), bar: r('#tab-bar'), app: r('#app'), vh: innerHeight, doc: document.documentElement.scrollHeight, body: document.body.scrollHeight }; }"""
BAR = """() => { const bar = document.getElementById('tab-bar'), br = bar.getBoundingClientRect(), W = document.documentElement.clientWidth;
  const bs = [...bar.querySelectorAll('[role=tab]')];
  return { shown: getComputedStyle(bar).display !== 'none', role: bar.getAttribute('role'), aria: bar.getAttribute('aria-label'), h: br.height, scrolls: bar.scrollWidth > bar.clientWidth + 0.5,
    tabs: bs.map(b => { const r = b.getBoundingClientRect(), l = b.lastElementChild.getBoundingClientRect(); return { id: b.dataset.tab, ico: b.querySelector('.tab-ico').textContent, label: b.lastElementChild.textContent, w: r.width,
      fits: l.left >= r.left - 0.01 && l.right <= r.right + 0.01 && r.left >= -0.01 && r.right <= W + 0.01 && b.lastElementChild.scrollWidth <= b.lastElementChild.clientWidth + 0.5, sel: b.getAttribute('aria-selected'), cur: b.classList.contains('current') }; }) }; }"""


def check_bar(b, lang):
    assert b['shown'] and b['role'] == 'tablist' and abs(b['h'] - 68) < 0.01 and not b['scrolls'] and b['aria'] == ARIA[lang]
    assert [(t['id'], t['ico'], t['label']) for t in b['tabs']] == TABS[lang]
    ws = [t['w'] for t in b['tabs']]
    assert max(ws) - min(ws) <= 0.5 and all(t['fits'] for t in b['tabs'])
    assert [t['sel'] for t in b['tabs']].count('true') == 1 and b['tabs'][0]['sel'] == 'true' and all((t['sel'] == 'true') == t['cur'] for t in b['tabs'])


def check_split(g, em, ep, H):
    assert abs(g['map']['h'] - em) <= 1 and abs(g['panel']['h'] - ep) <= 1 and abs(g['split']['h'] - 44) < 0.01
    assert abs(g['app']['bottom'] - g['bar']['top']) <= 1 and abs(g['panel']['bottom'] - g['bar']['top']) <= 1
    assert abs(g['app']['h'] - 44 - H) <= 1 and g['doc'] <= g['vh'] and g['body'] <= g['vh']


@needs_pw
@pytest.mark.parametrize('w,h,H,em,ep', SPLIT)
def test_the_bar_and_the_split_at_the_eight_windows(browser, w, h, H, em, ep):
    pg, fr = rp(browser, w, h)
    check_bar(fr.evaluate(BAR), 'fr')
    check_split(fr.evaluate(GEOM), em, ep, H)
    assert pg.errs == []


@needs_pw
@pytest.mark.parametrize('w,h,H,em,ep', [SPLIT[0], SPLIT[2], SPLIT[6]])
def test_the_english_bar_and_split(browser, w, h, H, em, ep):
    pg, fr = rp(browser, w, h, True, 'en')
    check_bar(fr.evaluate(BAR), 'en')
    check_split(fr.evaluate(GEOM), em, ep, H)
    assert pg.errs == []


@needs_pw
def test_no_bar_and_no_handle_above_1100_px(browser):
    pg, fr = rp(browser, 1280, 800, False)
    g = fr.evaluate(GEOM)
    assert g['bar'] is None and g['split'] is None and g['map']['h'] == 740 and g['panel']['h'] == 740 and g['panel']['w'] == 440
    assert fr.evaluate("() => document.documentElement.style.getPropertyValue('--mp-toast-bottom')") == ''
    # la section Calques reste masquée sans calque ; les sections et leurs en-têtes sont là
    assert fr.evaluate("() => [...document.querySelectorAll('#panel > .ed-section')].map(s => [s.dataset.section, s.getClientRects().length > 0, !!s.querySelector('.ed-head') && s.querySelector('.ed-head').getClientRects().length > 0])") == \
        [['route', True, True], ['refs', True, True], ['layers', False, False], ['nav', True, True]]
    pg2, fr2 = rp(browser, 1101, 800, True)
    g2 = fr2.evaluate(GEOM)
    assert g2['bar'] is None and g2['split'] is None and g2['panel']['w'] == 440
    assert pg.errs == [] and pg2.errs == []


SECS = """() => [...document.querySelectorAll('#panel > .ed-section')].map(s => { const h = s.querySelector('.ed-head'), b = s.querySelector('.ed-body');
  return { id: s.dataset.section, shown: s.getClientRects().length > 0 && getComputedStyle(s).display !== 'none', head: !!h && h.getClientRects().length > 0, icon: !!s.querySelector('.ui-foldic') && s.querySelector('.ui-foldic').getClientRects().length > 0,
    body: !!b && b.getClientRects().length > 0 && b.getBoundingClientRect().height > 0 }; })"""


@needs_pw
def test_a_tab_shows_its_section_alone_and_writes_nothing(browser):
    pg, fr = rp(browser, 1280, 800, True)                       # grand écran, au doigt : on replie Route et Navigation
    heads = lambda s: fr.evaluate("(s) => { const h = document.querySelector('#panel > .ed-section[data-section=\"' + s + '\"] .ed-head'); h.click(); }", s)  # noqa: E731
    heads('route')
    heads('nav'); heads('nav')
    assert fr.evaluate("() => [...document.querySelectorAll('#panel > .ed-section')].map(s => s.dataset.open)") == ['false', 'false', 'false', 'false']
    folds = fr.evaluate("() => localStorage.getItem('rp_folds_v1')")
    assert folds and '"route":false' in folds.replace(' ', '')
    pg.set_viewport_size({'width': 412, 'height': 915})
    attendre_fenetre(pg, 412, 915)
    attendre_mise_en_page(fr)
    attendre(fr, "getComputedStyle(document.getElementById('tab-bar')).display !== 'none'", 'la barre d\'onglets affichée à 412 px', lu="getComputedStyle(document.getElementById('tab-bar')).display")
    whole = "() => JSON.stringify(Object.keys(localStorage).sort().map(k => [k, localStorage.getItem(k)]))"
    snap = fr.evaluate(whole)
    assert 'rp_folds_v1' in snap
    for tid in ('route', 'refs', 'layers', 'nav'):
        tab(fr, tid)
        secs = fr.evaluate(SECS)
        shown = [s['id'] for s in secs if s['shown']]
        assert shown == [tid]
        s = [x for x in secs if x['id'] == tid][0]
        assert not s['head'] and not s['icon'] and s['body']
        assert fr.evaluate("() => document.body.dataset.activeTab") == tid
        assert [t for t in fr.evaluate(BAR)['tabs'] if t['sel'] == 'true'][0]['id'] == tid
    assert fr.evaluate("() => localStorage.getItem('rp_folds_v1')") == folds
    # changer d'onglet ramène le panneau en haut
    tab(fr, 'nav')
    fr.evaluate("() => { document.getElementById('panel').scrollTop = 200; }")
    assert fr.evaluate("() => document.getElementById('panel').scrollTop") > 0
    tab(fr, 'route')
    assert fr.evaluate("() => document.getElementById('panel').scrollTop") == 0
    assert fr.evaluate("() => localStorage.getItem('rp_folds_v1')") == folds
    assert fr.evaluate(whole) == snap                                                 # changer d'onglet n'écrit rien : tout localStorage, à l'octet, comme avant les quatre onglets
    assert pg.errs == []


@needs_pw
def test_the_open_tab_is_kept_when_leaving_the_tool_and_coming_back(browser):
    pg, fr = rp(browser, 412, 915)
    assert fr.evaluate("() => document.body.dataset.activeTab") == 'route'              # au chargement, Route
    tab(fr, 'nav')
    pick(pg, fr, 'Datacard Generator')
    dg = pg.query_selector('#iframe-dg').content_frame()
    pick(pg, dg, 'Route Planner')
    fr = pg.query_selector('#iframe-rp').content_frame()
    assert fr.evaluate("() => document.body.dataset.activeTab") == 'nav'
    b = fr.evaluate(BAR)
    assert [t['id'] for t in b['tabs'] if t['sel'] == 'true'] == ['nav']
    assert [s['id'] for s in fr.evaluate(SECS) if s['shown']] == ['nav']
    check_split(fr.evaluate(GEOM), 386.4, 356.6, 743)
    assert pg.errs == []


@needs_pw
@pytest.mark.parametrize('lang', ['fr', 'en'])
def test_the_layers_tab_without_a_layer_and_with_one(browser, lang):
    pg, fr = rp(browser, 345, 590, True, lang)
    tab(fr, 'layers')
    assert fr.evaluate("() => document.body.dataset.activeTab") == 'layers'
    info = fr.evaluate("""() => { const sec = document.getElementById('sec-layers'), n = document.getElementById('layers-empty'), c = document.getElementById('btn-layers-clear'), hp = sec.querySelector('[data-i18n="layers.help"]');
      return { shown: sec.getClientRects().length > 0, note: n.textContent, noteShown: n.getClientRects().length > 0, clear: c.getClientRects().length > 0, help: hp.textContent.slice(0, 40), helpShown: hp.getClientRects().length > 0,
               order: n.compareDocumentPosition(hp) & Node.DOCUMENT_POSITION_FOLLOWING ? 'note-then-help' : 'help-first', first: sec.querySelector('.ed-body').firstElementChild.id }; }""")
    assert info['shown'] and info['note'] == EMPTY[lang] and info['noteShown'] and not info['clear'] and info['helpShown'] and info['help'].startswith(HELP[lang][:20])
    assert info['order'] == 'note-then-help' and info['first'] == 'layers-empty'
    attendre(fr, "typeof openCfImport === 'function'", "l'import de calques prêt")
    fr.evaluate("""() => { const res = { theatre: 'Syria', layers: [cfLayer({ id: 'essai', name: 'Essai', visible: true, source: { kind: 'combatflite', file: 'essai.cf' }, items: [{ id: 'p1', type: 'point', name: 'Point', kind: 'target', lat: 35, lon: 36, color: '#0033cc' }] })], pre: [true] }; openCfImport('essai.cf', res); }""")
    attendre(fr, "document.getElementById('cf-import-go').getClientRects().length > 0", "la fenêtre d'import ouverte (bouton « Importer » affiché)")
    fr.evaluate("document.getElementById('cf-import-go').click()")
    attendre(fr, "document.querySelectorAll('#layers-list .cf-row').length === 1", 'le calque importé (une ligne dans la liste)', lu="document.querySelectorAll('#layers-list .cf-row').length")
    attendre_images(fr, 2)
    info = fr.evaluate("""() => ({ rows: document.querySelectorAll('#layers-list .cf-row').length, note: document.getElementById('layers-empty').getClientRects().length > 0, clear: document.getElementById('btn-layers-clear').getClientRects().length > 0,
      tab: document.body.dataset.activeTab })""")
    assert info['rows'] == 1 and not info['note'] and info['clear'] and info['tab'] == 'layers'
    fr.evaluate("() => document.querySelector('#layers-list .cf-del').click()")                  # on retire le dernier calque : la question, puis la note revient et le bouton part
    attendre(fr, "document.getElementById('ui-confirm').hidden === false", 'la question ouverte', lu="document.getElementById('ui-confirm').hidden")
    fr.evaluate("() => document.getElementById('ui-confirm-ok').click()")
    attendre(fr, "document.querySelectorAll('#layers-list .cf-row').length === 0 && document.getElementById('layers-empty').getClientRects().length > 0", 'le dernier calque retiré (liste vide, note revenue)',
             lu="[document.querySelectorAll('#layers-list .cf-row').length, document.getElementById('layers-empty').getClientRects().length]")
    attendre_images(fr, 2)
    info = fr.evaluate("""() => ({ rows: document.querySelectorAll('#layers-list .cf-row').length, note: document.getElementById('layers-empty').getClientRects().length > 0, noteText: document.getElementById('layers-empty').textContent,
      clear: document.getElementById('btn-layers-clear').getClientRects().length > 0, tab: document.body.dataset.activeTab, shown: document.getElementById('sec-layers').getClientRects().length > 0 })""")
    assert info == {'rows': 0, 'note': True, 'noteText': EMPTY[lang], 'clear': False, 'tab': 'layers', 'shown': True}
    assert pg.errs == []
    pg2, fr2 = rp(browser, 1280, 800, False, lang)
    assert fr2.evaluate("() => document.getElementById('sec-layers').getClientRects().length") == 0         # grand écran, sans calque : masquée, comme à la base


@needs_pw
def test_a_touch_mode_never_changes_the_tab(browser):
    pg, fr = rp(browser, 412, 915)
    n0 = fr.evaluate("() => __RP.S.refs.length")
    tab(fr, 'nav')
    assert fr.evaluate("() => document.body.dataset.activeTab") == 'nav'
    # le mode Réf. se choisit dans la barre de la carte ; on le prend par son bouton
    fr.evaluate("() => { const b = [...document.querySelectorAll('.tapmode .tb-btn')].find(x => /^(Réf\\.|Ref\\.)$/.test(x.textContent.trim())); b.click(); }")
    attendre(fr, "__RP.tapMode === 'ref'", 'le mode Réf. posé (tapMode)', lu='__RP.tapMode')
    assert fr.evaluate("() => __RP.tapMode") == 'ref' and fr.evaluate("() => document.body.dataset.activeTab") == 'nav'      # le mode posé depuis Nav. : l'onglet ne change pas
    box = fr.evaluate("() => { const r = document.getElementById('map').getBoundingClientRect(); return [r.left + r.width / 2, r.top + r.height / 2]; }")
    off = pg.evaluate("() => { const r = document.getElementById('iframe-rp').getBoundingClientRect(); return [r.left, r.top]; }")
    pg.touchscreen.tap(box[0] + off[0] - 60, box[1] + off[1] + 60)
    attendre(fr, '__RP.S.refs.length === arg', 'la référence posée par le toucher (S.refs)', lu='__RP.S.refs.length', arg=n0 + 1)
    assert fr.evaluate("() => __RP.S.refs.length") == n0 + 1 and fr.evaluate("() => document.body.dataset.activeTab") == 'nav'
    tab(fr, 'refs')
    assert fr.evaluate("() => __RP.tapMode") == 'ref'                                    # et l'inverse : un onglet ne change pas le mode
    assert pg.errs == []


def drag(pg, fr, dy):
    off = pg.evaluate("() => { const r = document.getElementById('iframe-rp').getBoundingClientRect(); return [r.left, r.top]; }")
    b = fr.evaluate("() => { const r = document.getElementById('rp-split').getBoundingClientRect(); return [r.left + r.width / 2, r.top + r.height / 2]; }")
    x, y = b[0] + off[0], b[1] + off[1]
    pg.mouse.move(x, y)
    pg.mouse.down()
    for i in range(1, 9):
        pg.mouse.move(x, y + dy * i / 8)
    pg.mouse.up()
    attendre_lecture_stable(fr, "() => [document.querySelector('.mapwrap').getBoundingClientRect().height, localStorage.getItem('rp_split_v1'), localStorage.getItem('rp_split_land_v1')]", 'la poignée lâchée (hauteur de la carte et clés du partage)')


LS_DUMP = "() => JSON.stringify(Object.keys(localStorage).map(k => [k, localStorage.getItem(k)]))"
LS_PUT = "(d) => { JSON.parse(d).forEach(kv => localStorage.setItem(kv[0], kv[1])); }"
LS_LOST = "(d) => { const had = JSON.parse(d).map(kv => kv[0]).filter(k => /^(briefing_state_v2|datacard_state_v1|fc_state_v1|recon_state_v1)$/.test(k)); return had.length > 0 && had.every(k => localStorage.getItem(k) === null); }"


def reopen(pg):
    """Recharge la page ; le shell rouvre l'outil par l'adresse. On attend que le Route Planner soit prêt et que sa carte ait cessé de bouger, sans durée fixe.
    Le contexte du banc est en mémoire : de temps en temps Chromium y perd tout localStorage à un rechargement (aucun clear() ni removeItem() de l'application, vérifié en les enveloppant ; le stockage
    repart vide, toutes les clés ensemble). Un vrai navigateur garde le stockage : on le remet comme il était et on recharge, au plus trois fois, avant de juger le comportement de l'outil."""
    snap = pg.evaluate(LS_DUMP)
    fr = None
    for _ in range(3):
        pg.reload(wait_until='commit')
        pg.wait_for_function("() => { const f = document.getElementById('iframe-rp'); return !!f && !!f.contentWindow && !!f.contentWindow.__RP && f.contentDocument.getElementById('rp-split'); }", timeout=90000)
        fr = pg.query_selector('#iframe-rp').content_frame()
        if not pg.evaluate(LS_LOST, snap):
            break
        pg.evaluate(LS_PUT, snap)                                                  # le banc a perdu le stockage : on le remet et on recharge
        warnings.warn('bench: localStorage lost across a reload, restored')
    assert not pg.evaluate(LS_LOST, snap), 'localStorage lost three reloads in a row'
    attendre_mise_en_page(fr, 60000)
    attendre_lecture_stable(fr, "() => document.querySelector('.mapwrap').getBoundingClientRect().height", 'la carte au repos (hauteur du cadre de la carte)')
    return fr


KEYS = "() => [localStorage.getItem('rp_split_v1'), localStorage.getItem('rp_split_land_v1')]"


@needs_pw
@pytest.mark.parametrize('w,h,H,em,ep,key', [(412, 915, 743, 386.4, 356.6, 0), (915, 412, 240, 140, 100, 1)])
def test_the_handle_drags_remembers_clamps_and_resets(browser, w, h, H, em, ep, key):
    pg, fr = rp(browser, w, h)
    m0 = fr.evaluate(GEOM)['map']['h']
    assert abs(m0 - em) <= 1
    drag(pg, fr, 40)
    m1 = fr.evaluate(GEOM)['map']['h']
    assert abs(m1 - (m0 + 40)) <= 1
    keys = fr.evaluate(KEYS)
    assert keys[key] is not None and abs(float(keys[key]) - m1) <= 1 and keys[1 - key] is None
    fr = reopen(pg)
    assert abs(fr.evaluate(GEOM)['map']['h'] - m1) <= 1
    # 9 999 : 85 % de H ; 50 : la borne basse
    fr.evaluate("(k) => { localStorage.setItem(k, '9999'); }", 'rp_split_v1' if key == 0 else 'rp_split_land_v1')
    fr.evaluate("() => window.dispatchEvent(new Event('resize'))")
    attendre_images(fr, 2)
    # la lecture de la clé se fait au chargement : on recharge l'outil
    fr = reopen(pg)
    assert abs(fr.evaluate(GEOM)['map']['h'] - 0.85 * H) <= 1
    fr.evaluate("(k) => { localStorage.setItem(k, '50'); }", 'rp_split_v1' if key == 0 else 'rp_split_land_v1')
    fr = reopen(pg)
    assert abs(fr.evaluate(GEOM)['map']['h'] - max(140 if key else 220, 0.25 * H)) <= 1
    # deux touchers : le partage du tableau, la clé effacée
    off = pg.evaluate("() => { const r = document.getElementById('iframe-rp').getBoundingClientRect(); return [r.left, r.top]; }")
    b = fr.evaluate("() => { const r = document.getElementById('rp-split').getBoundingClientRect(); return [r.left + r.width / 2, r.top + r.height / 2]; }")
    pg.mouse.click(b[0] + off[0], b[1] + off[1])
    pg.mouse.click(b[0] + off[0], b[1] + off[1])
    attendre(fr, "localStorage.getItem(arg) === null", 'le partage remis à celui du tableau (clé effacée)', lu='localStorage.getItem(arg)', arg='rp_split_v1' if key == 0 else 'rp_split_land_v1')
    attendre_lecture_stable(fr, "() => document.querySelector('.mapwrap').getBoundingClientRect().height", 'la carte à la taille du tableau')
    assert abs(fr.evaluate(GEOM)['map']['h'] - em) <= 1 and fr.evaluate(KEYS)[key] is None
    assert pg.errs == []


KBM = """() => { const r = s => { const e = document.querySelector(s); if (!e || !e.getClientRects().length) return null; const b = e.getBoundingClientRect(); return { top: b.top, bottom: b.bottom, h: b.height }; };
  const bar = document.getElementById('tab-bar'), f = document.activeElement;
  return { vh: innerHeight, app: r('#app'), map: r('.mapwrap'), split: r('#rp-split'), panel: r('#panel'), bar: bar && bar.getClientRects().length ? r('#tab-bar') : null,
    barDisplay: bar ? getComputedStyle(bar).display : null, field: f && f.id ? r('#' + f.id) : null, kb: document.documentElement.classList.contains('ui-kb'),
    toast: getComputedStyle(document.documentElement).getPropertyValue('--mp-toast-bottom').trim() }; }"""
KB_WINDOWS = [(345, 590, 200), (360, 640, 260), (412, 915, 330), (915, 412, 200)]


BAR_DISPLAY = "getComputedStyle(document.getElementById('tab-bar')).display"


def kb_apres(pg, fr, w, h, ouvert):
    """Attend la mise en page après le changement de fenêtre du clavier : la fenêtre à la taille donnée, la barre d'onglets cachée (clavier ouvert) ou revenue, puis deux lectures égales de toute la géométrie."""
    attendre_fenetre(pg, w, h)
    attendre(fr, BAR_DISPLAY + (" === 'none'" if ouvert else " !== 'none'") + " && document.documentElement.classList.contains('ui-kb') === " + ('true' if ouvert else 'false'),
             'la barre d\'onglets %s et ui-kb %s' % ('cachée' if ouvert else 'revenue', 'posé' if ouvert else 'retiré'), lu='[' + BAR_DISPLAY + ", document.documentElement.classList.contains('ui-kb')]")
    attendre_images(fr, 3)
    attendre_lecture_stable(fr, KBM, 'la géométrie du Route Planner au repos')


def kb_open(pg, fr, field, w, h, d):
    """Le clavier de l'écran, simulé : le champ prend le focus, la fenêtre visible perd d pixels."""
    fr.evaluate("(id) => document.getElementById(id).focus()", field)
    attendre(fr, 'document.activeElement.id === arg', 'le champ %s a le focus' % field, lu='document.activeElement.id', arg=field)
    pg.set_viewport_size({'width': w, 'height': h - d})
    kb_apres(pg, fr, w, h - d, True)


def kb_close(pg, fr, w, h):
    fr.evaluate("() => document.activeElement.blur()")
    pg.set_viewport_size({'width': w, 'height': h})
    kb_apres(pg, fr, w, h, False)


def kb_expected_map(g, land):
    """Règle 4 : H' va du haut de #app au bas de la fenêtre visible, poignée retirée ; carte = min(borne basse, H' - 100), jamais moins de 60 px."""
    hp = g['vh'] - g['app']['top'] - g['split']['h']
    low = max(140 if land else 220, 0.25 * hp)
    return hp, max(60, min(low, hp - 100))


@needs_pw
@pytest.mark.parametrize('w,h,d', KB_WINDOWS)
def test_the_keyboard_on_a_panel_field_hides_the_bar_keeps_the_field_in_view_and_gives_back_the_state(browser, w, h, d):
    pg, fr = rp(browser, w, h)
    drag(pg, fr, 30)                                                              # une hauteur gardée : elle doit revenir
    before, keys = fr.evaluate(KBM), fr.evaluate(KEYS)
    assert before['bar'] is not None and before['barDisplay'] != 'none'
    assert keys[0 if h > w else 1] is not None
    kb_open(pg, fr, 'route-name', w, h, d)
    g = fr.evaluate(KBM)
    hp, em = kb_expected_map(g, w > h)
    assert g['kb'] and g['vh'] == h - d and g['bar'] is None and g['barDisplay'] == 'none'
    assert abs(g['map']['h'] - em) <= 1 and abs(g['panel']['h'] - (hp - em)) <= 1
    f = g['field']
    assert f and f['top'] >= g['panel']['top'] - 1 and f['bottom'] <= g['panel']['bottom'] + 1 and f['bottom'] <= g['vh'] and f['top'] >= 0     # le champ entier est dans le panneau visible, au-dessus du bas de la fenêtre
    fr.evaluate("() => showToast('Essai')")                                       # le toast suit : à 20 px du bas de la fenêtre visible
    attendre(fr, '(%s)() !== null' % TOAST, 'le toast affiché', lu='(%s)()' % TOAST)
    attendre_lecture_stable(fr, TOAST, 'le toast posé')
    t = fr.evaluate(TOAST)
    assert t and abs(t['gap'] - 20) <= 1
    assert fr.evaluate(KEYS) == keys                                              # rien n'est écrit pendant le clavier
    kb_close(pg, fr, w, h)
    a = fr.evaluate(KBM)
    assert not a['kb'] and a['bar'] and abs(a['bar']['top'] - before['bar']['top']) <= 1 and a['toast'] == before['toast']
    assert abs(a['map']['h'] - before['map']['h']) <= 1 and abs(a['panel']['h'] - before['panel']['h']) <= 1 and abs(a['app']['bottom'] - before['app']['bottom']) <= 1
    assert fr.evaluate(KEYS) == keys
    assert pg.errs == []


@needs_pw
@pytest.mark.parametrize('w,h,d', [(345, 590, 200), (360, 640, 260)])
def test_the_map_search_gets_the_whole_height_with_at_least_three_whole_results(browser, w, h, d):
    pg, fr = rp(browser, w, h)
    before, keys = fr.evaluate(KBM), fr.evaluate(KEYS)
    fr.evaluate("() => document.querySelector('.rp-search-btn').click()")
    attendre(fr, "!!document.getElementById('sr-in') && document.getElementById('sr-in').getClientRects().length > 0", 'la recherche de la carte ouverte (champ affiché)')
    fr.evaluate("() => { const i = document.getElementById('sr-in'); i.focus(); i.value = 'al'; i.dispatchEvent(new Event('input', { bubbles: true })); }")
    attendre(fr, "document.querySelectorAll('#sr-list .sr-row[data-i]').length >= 3", 'au moins trois résultats listés', lu="document.querySelectorAll('#sr-list .sr-row[data-i]').length")
    pg.set_viewport_size({'width': w, 'height': h - d})
    attendre_fenetre(pg, w, h - d)
    attendre(fr, BAR_DISPLAY + " === 'none'", 'la barre d\'onglets cachée', lu=BAR_DISPLAY)
    attendre_images(fr, 3)
    attendre_lecture_stable(fr, KBM, 'la géométrie du Route Planner au repos')
    g = fr.evaluate(KBM)
    hp = g['vh'] - g['app']['top'] - g['split']['h']
    assert g['bar'] is None and abs(g['map']['h'] - hp) <= 1 and g['split'] and g['panel'] is None          # toute la hauteur H' à la carte, le panneau à 0, la poignée reste
    rows = fr.evaluate("""() => { const l = document.getElementById('sr-list'), lr = l.getBoundingClientRect();
      return { rows: [...l.querySelectorAll('.sr-row[data-i]')].map(e => { const b = e.getBoundingClientRect(); return b.top >= lr.top - 0.5 && b.bottom <= lr.bottom + 0.5 && b.top >= 0 && b.bottom <= innerHeight; }), top: lr.top, bottom: lr.bottom, vh: innerHeight }; }""")
    assert rows['rows'].count(True) >= 3, rows
    assert fr.evaluate(KEYS) == keys                                              # rien n'est écrit pendant le clavier
    kb_close(pg, fr, w, h)
    a = fr.evaluate(KBM)
    assert a['bar'] and abs(a['map']['h'] - before['map']['h']) <= 1 and abs(a['panel']['h'] - before['panel']['h']) <= 1 and abs(a['bar']['top'] - before['bar']['top']) <= 1
    assert pg.errs == []


@needs_pw
@pytest.mark.parametrize('tid,field', [('dg', None), ('bg', None)])
def test_the_keyboard_hides_the_bar_of_the_datacard_and_briefing_generators_then_gives_it_back(browser, tid, field):
    pg = shell(browser, 345, 590)
    f = open_card(pg, tid)
    pick = """() => { const e = [...document.querySelectorAll('#editor input[type=text], #editor input:not([type]), #editor textarea')].find(x => x.getClientRects().length && !x.disabled && !x.readOnly);
      if (!e) return null; if (!e.id) e.id = 'kb-probe'; e.scrollIntoView({ block: 'center' }); e.focus(); return e.id; }"""
    bar = "() => { const b = document.getElementById('tab-bar'); return [getComputedStyle(b).display, b.getClientRects().length > 0, getComputedStyle(document.documentElement).getPropertyValue('--mp-toast-bottom').trim()]; }"
    assert f.evaluate(bar)[1]
    toast0 = f.evaluate(bar)[2]
    attendre(f, '!!(%s)()' % pick.replace('e.focus(); return e.id;', 'return e.id;'), 'un champ de saisie affiché dans l\'éditeur')
    assert f.evaluate(pick)
    attendre(f, "['INPUT', 'TEXTAREA'].includes(document.activeElement.tagName)", 'le champ a le focus', lu='document.activeElement.tagName')
    pg.set_viewport_size({'width': 345, 'height': 390})
    attendre_fenetre(pg, 345, 390)
    attendre(f, "getComputedStyle(document.getElementById('tab-bar')).display === 'none' && document.documentElement.classList.contains('ui-kb')", 'la barre cachée et ui-kb posé')
    attendre_images(f, 3)
    assert f.evaluate("() => document.activeElement.tagName") in ('INPUT', 'TEXTAREA')
    b = f.evaluate(bar)
    assert b[0] == 'none' and not b[1] and f.evaluate("() => document.documentElement.classList.contains('ui-kb')")
    f.evaluate("() => showToast('Essai')")                                       # le toast du shell : à 20 px du bas de la fenêtre visible
    TSHELL = "() => { const e = document.getElementById('toast'), r = e.getBoundingClientRect(); return [e.classList.contains('show'), r.bottom, innerHeight]; }"
    attendre(pg, "document.getElementById('toast').classList.contains('show')", 'le toast du shell affiché')
    attendre_lecture_stable(pg, TSHELL, 'le toast du shell posé')
    t = pg.evaluate("() => { const e = document.getElementById('toast'), r = e.getBoundingClientRect(); return { show: e.classList.contains('show'), gap: innerHeight - r.bottom }; }")
    assert t['show'] and abs(t['gap'] - 20) <= 1, t
    f.evaluate("() => document.activeElement.blur()")
    pg.set_viewport_size({'width': 345, 'height': 590})
    attendre_fenetre(pg, 345, 590)
    attendre(f, "getComputedStyle(document.getElementById('tab-bar')).display !== 'none' && !document.documentElement.classList.contains('ui-kb')", 'la barre revenue et ui-kb retiré')
    attendre_images(f, 3)
    b = f.evaluate(bar)
    assert b[0] != 'none' and b[1] and b[2] == toast0 and not f.evaluate("() => document.documentElement.classList.contains('ui-kb')")
    assert pg.errs == []


ROW = """() => { const row = document.querySelector('#pts .pt-row.pts'), rr = row.getBoundingClientRect(), q = k => row.querySelector(k);
  const r = e => { const b = e.getBoundingClientRect(); return { l: b.left - rr.left, t: b.top - rr.top, w: b.width, h: b.height }; };
  const fs = e => getComputedStyle(e).fontSize;
  const head = document.querySelector('.pt-head.pts'), hr = [...head.children].map(c => { const b = c.getBoundingClientRect(); return { s: c.textContent, l: b.left, t: b.top, w: b.width }; });
  const ref = q('.tbm-trigger');
  return { row: { w: rr.width, h: rr.height }, num: r(q('.pt-num')), name: r(q('[data-k=name]')), alt: r(q('[data-k=alt]')), gs: r(q('[data-k=gs]')), ref: r(ref), del: r(q('.pt-del')),
    fs: { name: fs(q('[data-k=name]')), alt: fs(q('[data-k=alt]')), gs: fs(q('[data-k=gs]')), ref: fs(ref) }, head: hr, rowLeft: rr.left, n: document.querySelectorAll('#pts .pt-row.pts').length,
    dash: [...document.querySelectorAll('#pts .pt-row.pts')].map(x => getComputedStyle(x).borderTopStyle), refsRow: (() => { const x = document.querySelector('#refs .pt-row'); return x ? getComputedStyle(x).borderTopStyle : null; })() }; }"""


@needs_pw
@pytest.mark.parametrize('w,h', [(345, 590), (412, 915)])
def test_the_waypoint_row_takes_two_lines_below_520_px_with_a_finger(browser, w, h):
    pg, fr = rp(browser, w, h)
    m = fr.evaluate(ROW)
    n, nm, al, gs, rf, de = m['num'], m['name'], m['alt'], m['gs'], m['ref'], m['del']
    assert abs(n['w'] - 44) <= .5 and abs(de['w'] - 44) <= .5 and n['h'] >= 88 - 1 and abs(n['h'] - m['row']['h']) <= 1 and abs(de['h'] - m['row']['h']) <= 1       # n° et ✕ : 44 de large, les deux lignes
    assert nm['t'] < al['t'] - 20 and abs(al['t'] - gs['t']) <= 1 and abs(al['t'] - rf['t']) <= 1                                                              # le nom en haut, trois champs dessous
    assert abs(al['w'] - gs['w']) <= 1 and abs(gs['w'] - rf['w']) <= 1                                                                                          # trois largeurs égales
    assert abs(nm['l'] - al['l']) <= 1 and abs(nm['l'] + nm['w'] - (rf['l'] + rf['w'])) <= 1 and abs(nm['l'] - (n['l'] + n['w'] + 4)) <= 1.5 and abs(de['l'] - (nm['l'] + nm['w'] + 4)) <= 1.5
    assert all(v == '16px' for v in m['fs'].values())
    hd = {x['s']: x for x in m['head']}
    assert hd['N°']['t'] < hd['Alt. (m)']['t'] and abs(hd['Nom']['t'] - hd['N°']['t']) <= 1 and abs(hd['Alt. (m)']['l'] - (m['rowLeft'] + al['l'])) <= 1.5 and abs(hd['Réf.']['l'] - (m['rowLeft'] + rf['l'])) <= 1.5 and abs(hd['Vit. km/h']['l'] - (m['rowLeft'] + gs['l'])) <= 1.5
    assert m['n'] == 6 and m['dash'][0] != 'dashed' and all(d == 'dashed' for d in m['dash'][1:]) and m['refsRow'] in (None, 'none')
    # saisir un nom, une altitude, une vitesse, changer la référence : S.points porte les valeurs
    if w == 345:
        row = fr.locator('#pts .pt-row.pts').nth(1)
        row.locator('[data-k=name]').fill('ESSAI')
        row.locator('[data-k=alt]').fill('123')
        row.locator('[data-k=gs]').fill('77')
        row.locator('.tbm-trigger').tap()                                       # la liste Réf. : on choisit MER (MSL) ; le locator attend la liste affichée
        fr.locator('.tbm-panel li.tbm-opt').filter(has_text=re.compile('^(MER|MSL)$')).first.tap()
        attendre(fr, "__RP.S.points[1].altRef === 'MSL'", 'la référence MER (MSL) posée sur le point 2', lu='__RP.S.points[1].altRef')
        p = fr.evaluate("() => { const p = __RP.S.points[1]; return [p.name, p.alt, p.gs, p.altRef]; }")
        assert p[0] == 'ESSAI' and p[3] == 'MSL' and p[1] == 123 and abs(p[2] - 77) < 1
    assert pg.errs == []


@needs_pw
def test_the_waypoint_row_with_a_mouse_below_520_px_keeps_the_text_of_the_base(browser):
    pg, fr = rp(browser, 400, 800, False)
    m = fr.evaluate(ROW)
    assert m['num']['t'] == 0 and m['name']['t'] < m['alt']['t'] and abs(m['alt']['t'] - m['ref']['t']) <= 1 and abs(m['num']['w'] - 44) <= .5
    assert m['fs'] == {'name': '13px', 'alt': '13px', 'gs': '13px', 'ref': '12px'}
    assert pg.errs == []


@needs_pw
@pytest.mark.parametrize('w,h', [(520, 900), (716, 646)])
def test_the_waypoint_row_keeps_one_line_from_520_px(browser, w, h):
    pg, fr = rp(browser, w, h)
    m = fr.evaluate(ROW)
    assert abs(m['name']['t'] - m['alt']['t']) <= 1 and abs(m['alt']['t'] - m['ref']['t']) <= 1 and m['row']['h'] <= 46
    assert m['num']['w'] <= 31 and m['del']['w'] <= 35 and m['fs']['name'] == '13px' and m['fs']['ref'] == '12px'
    if w == 716:                                                              # les largeurs de la version d'avant à 716
        assert abs(m['name']['w'] - 374) <= 1 and abs(m['alt']['w'] - 58) <= 1 and abs(m['gs']['w'] - 62) <= 1 and abs(m['ref']['w'] - 66) <= 1
    assert all(d != 'dashed' for d in m['dash'])
    assert pg.errs == []


TOAST = """() => { const t = [...document.querySelectorAll('.toast, #toast, .mp-toast')].find(e => e.getClientRects().length && getComputedStyle(e).visibility !== 'hidden');
  if (!t) return null; const r = t.getBoundingClientRect(), b = document.getElementById('tab-bar'), br = b && b.getClientRects().length ? b.getBoundingClientRect() : null;
  return { gap: br ? br.top - r.bottom : innerHeight - r.bottom, overlaps: br ? r.bottom > br.top : false }; }"""


@needs_pw
@pytest.mark.parametrize('w,h', [(345, 590), (412, 915)])
def test_the_toast_sits_12_px_above_the_bar(browser, w, h):
    pg, fr = rp(browser, w, h)
    attendre_toast_parti(pg, fr)                                                # le toast « Restaurer » de l'exemple est parti (12 s par construction de showToast)
    fr.evaluate("() => showToast('Essai')")
    attendre(fr, '(%s)() !== null' % TOAST, 'le toast affiché', lu='(%s)()' % TOAST)
    attendre_lecture_stable(fr, TOAST, 'le toast posé')
    t = fr.evaluate(TOAST)
    assert t and abs(t['gap'] - 12) <= 1 and not t['overlaps']
    assert pg.errs == []


@needs_pw
def test_the_toast_stays_20_px_from_the_bottom_with_a_mouse(browser):
    pg, fr = rp(browser, 1280, 800, False)
    attendre_toast_parti(pg, fr)                                                # le toast « Restaurer » de l'exemple est parti (12 s par construction de showToast)
    fr.evaluate("() => showToast('Essai')")
    attendre(fr, '(%s)() !== null' % TOAST, 'le toast affiché', lu='(%s)()' % TOAST)
    attendre_lecture_stable(fr, TOAST, 'le toast posé')
    t = fr.evaluate(TOAST)
    assert t and abs(t['gap'] - 20) <= 1
    assert pg.errs == []


# au-dessus de 1 100 px : les valeurs de la version d'avant (1280 x 800, souris) : la ligne de point (étiquette, largeur, hauteur, décalage haut, taille du texte) et les sections (id, masquée, repli, hauteur)
BASE_PTROW = [['button.pt-num', 30, 40, 0, None], ['input:name', 98, 40, 0, '13px'], ['input:alt', 58, 40, 0, '13px'], ['input:gs', 62, 40, 0, '13px'], ['button.in', 66, 40, 0, '13px'], ['select:altRef', 0, 0, None, '13px'], ['button.pt-del', 34, 40, 0, None]]
BASE_SECS = {'fr': [['route', False, 'true', 852], ['refs', False, 'false', 64], ['layers', True, 'false', 0], ['nav', False, 'false', 64]],
             'en': [['route', False, 'true', 837], ['refs', False, 'false', 64], ['layers', True, 'false', 0], ['nav', False, 'false', 64]]}
PTROW = """() => { const row = document.querySelector('#pts .pt-row.pts'), rr = row.getBoundingClientRect();
  return { cells: [...row.children].map(c => { const r = c.getBoundingClientRect(), i = c.matches('.in') ? c : c.querySelector('.in');
      return [c.tagName.toLowerCase() + (c.dataset.k ? ':' + c.dataset.k : (c.className ? '.' + String(c.className).split(' ')[0] : '')), Math.round(r.width * 10) / 10, Math.round(r.height), c.dataset.k === 'altRef' ? null : Math.round(r.top - rr.top), i ? getComputedStyle(i).fontSize : null]; }),
    h: Math.round(rr.height), secs: [...document.querySelectorAll('#panel > .ed-section')].map(s => [s.dataset.section, s.hidden, s.dataset.open, Math.round(s.getBoundingClientRect().height)]) }; }"""


@needs_pw
@pytest.mark.parametrize('lang', ['fr', 'en'])
def test_above_1100_px_the_waypoint_row_and_the_folds_are_those_of_the_base(browser, lang):
    pg, fr = rp(browser, 1280, 800, False, lang)
    m = fr.evaluate(PTROW)
    assert m['h'] == 40 and len(m['cells']) == len(BASE_PTROW)
    for got, exp in zip(m['cells'], BASE_PTROW):
        assert got[0] == exp[0] and abs(got[1] - exp[1]) <= 1 and got[2] == exp[2] and got[3] == exp[3] and got[4] == exp[4], (got, exp)
    for got, exp in zip(m['secs'], BASE_SECS[lang]):
        assert got[:3] == exp[:3] and abs(got[3] - exp[3]) <= 1, (got, exp)
    assert len(m['secs']) == 4 and pg.errs == []


REFROWS = """() => { const rows = [...document.querySelectorAll('#refs .pt-row')];
  return rows.map(row => { const rr = row.getBoundingClientRect(); return { h: rr.height, cells: [...row.children].filter(c => c.getClientRects().length).map(c => { const r = c.getBoundingClientRect(); return [r.top - rr.top, r.height, r.left - rr.left, r.width]; }), w: rr.width, sw: row.scrollWidth, cw: row.clientWidth }; }); }"""


@needs_pw
@pytest.mark.parametrize('w,h,touch', [(345, 590, True), (412, 915, True), (400, 800, False)])
def test_every_reference_point_row_stays_on_one_line_below_520_px(browser, w, h, touch):
    pg, fr = rp(browser, w, h, touch)
    for i in range(4):
        fr.evaluate("(i) => { addRef(35 + i * 0.1, 36 + i * 0.1, 'REF' + i); }", i)
    attendre(fr, '__RP.S.refs.length >= 4', 'les quatre références posées (S.refs)', lu='__RP.S.refs.length')
    tab(fr, 'refs')                                                               # la barre d'onglets est là jusqu'à 1 100 px, souris ou doigt
    fr.wait_for_function("() => { const rows = [...document.querySelectorAll('#refs .pt-row')]; return rows.length >= 4 && rows.every(r => r.getClientRects().length && r.getBoundingClientRect().height > 0); }", timeout=10000)       # les quatre lignes sont posées
    attendre_mise_en_page(fr)                                                     # et la mise en page de l'onglet est faite avant la mesure : les lignes ont cessé de bouger
    attendre_lecture_stable(fr, REFROWS, 'les lignes de références au repos')
    rows = fr.evaluate(REFROWS)
    assert len(rows) >= 4
    for r in rows:
        tops = [round(c[0]) for c in r['cells']]
        assert len(r['cells']) >= 4 and max(tops) - min(tops) <= 1 and r['h'] <= 50 and r['sw'] <= r['cw'] + 1, r          # une seule ligne : les cellules à la même hauteur, la ligne à une cellule de haut, rien qui déborde
        assert all(c[1] <= 48 for c in r['cells'])
    assert pg.errs == []
