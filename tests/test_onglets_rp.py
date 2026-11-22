"""Le Route Planner au téléphone : la carte toujours visible, le panneau en quatre onglets (Route · Réf. · Calques · Nav.) dans la barre basse commune,
le partage carte / panneau, la ligne de point sur deux lignes sous 520 px, le toast au-dessus de la barre. Joué sur le shell construit (dist/dcs_mission_plan.html,
chromium, aucun réseau) ; les contrôles passent par le DOM, jamais par une capture."""
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
    assert u.count(LOG_TABS) == 1 and rp.rstrip('\n').endswith('\n\n' + LOG_TABS.rstrip('\n'))             # à la fin de la rubrique, une ligne vide avant
    assert u.count(LOG_PAREN) == 1 and '(the Route Planner’s waypoint rows still use smaller text)' not in log
    assert u.count('`MP-V2.1.0+6` for this one') == 1 and '+5' not in u
    assert re.search(r'^DEV_BUILD = 6$', (ROOT / 'version_block.py').read_text(encoding='utf-8'), re.M)
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


def rp(br, w, h, touch=True, lang='fr'):
    pg = shell(br, w, h, touch, lang)
    return pg, open_card(pg, 'rp')


def back(pg):
    pg.evaluate("() => { const f = document.querySelector('iframe:not([style*=\"display: none\"])'); f.contentDocument.querySelector('.mp-back-injected').click(); }")
    pg.wait_for_timeout(500)


def pick(pg, fr, name):
    fr.locator('.toolbar .tb-brand').click()
    pg.wait_for_timeout(300)
    fr.locator('.tb-sw-panel li.tbm-opt').filter(has_text=re.compile('^' + re.escape(name) + '$')).first.click()
    pg.wait_for_timeout(700)


def tab(fr, tid):
    fr.evaluate("(id) => document.querySelector('#tab-bar [data-tab=\"' + id + '\"]').click()", tid)
    fr.wait_for_timeout(250)


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
    pg.wait_for_timeout(700)
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
    info = fr.evaluate("""() => { const sec = document.getElementById('sec-layers'), n = document.getElementById('layers-empty'), c = document.getElementById('btn-layers-clear'), hp = sec.querySelector('[data-i18n="layers.help"]');
      return { shown: sec.getClientRects().length > 0, note: n.textContent, noteShown: n.getClientRects().length > 0, clear: c.getClientRects().length > 0, help: hp.textContent.slice(0, 40), helpShown: hp.getClientRects().length > 0,
               order: n.compareDocumentPosition(hp) & Node.DOCUMENT_POSITION_FOLLOWING ? 'note-then-help' : 'help-first', first: sec.querySelector('.ed-body').firstElementChild.id }; }""")
    assert info['shown'] and info['note'] == EMPTY[lang] and info['noteShown'] and not info['clear'] and info['helpShown'] and info['help'].startswith(HELP[lang][:20])
    assert info['order'] == 'note-then-help' and info['first'] == 'layers-empty'
    fr.evaluate("""() => { const res = { theatre: 'Syria', layers: [cfLayer({ id: 'essai', name: 'Essai', visible: true, source: { kind: 'combatflite', file: 'essai.cf' }, items: [{ id: 'p1', type: 'point', name: 'Point', kind: 'target', lat: 35, lon: 36, color: '#0033cc' }] })], pre: [true] }; openCfImport('essai.cf', res); }""")
    pg.wait_for_timeout(300)
    fr.evaluate("document.getElementById('cf-import-go').click()")
    pg.wait_for_timeout(600)
    info = fr.evaluate("""() => ({ rows: document.querySelectorAll('#layers-list .cf-row').length, note: document.getElementById('layers-empty').getClientRects().length > 0, clear: document.getElementById('btn-layers-clear').getClientRects().length > 0,
      tab: document.body.dataset.activeTab })""")
    assert info['rows'] == 1 and not info['note'] and info['clear']
    assert pg.errs == []
    pg2, fr2 = rp(browser, 1280, 800, False, lang)
    assert fr2.evaluate("() => document.getElementById('sec-layers').getClientRects().length") == 0         # grand écran, sans calque : masquée, comme à la base


@needs_pw
def test_a_touch_mode_never_changes_the_tab(browser):
    pg, fr = rp(browser, 412, 915)
    n0 = fr.evaluate("() => __RP.S.refs.length")
    # le mode Réf. se choisit dans la barre de la carte ; on le prend par son bouton
    fr.evaluate("() => { const b = [...document.querySelectorAll('.tapmode .tb-btn')].find(x => /^(Réf\\.|Ref\\.)$/.test(x.textContent.trim())); b.click(); }")
    pg.wait_for_timeout(300)
    assert fr.evaluate("() => __RP.tapMode") == 'ref'
    box = fr.evaluate("() => { const r = document.getElementById('map').getBoundingClientRect(); return [r.left + r.width / 2, r.top + r.height / 2]; }")
    off = pg.evaluate("() => { const r = document.getElementById('iframe-rp').getBoundingClientRect(); return [r.left, r.top]; }")
    pg.touchscreen.tap(box[0] + off[0] - 60, box[1] + off[1] + 60)
    pg.wait_for_timeout(500)
    assert fr.evaluate("() => __RP.S.refs.length") == n0 + 1 and fr.evaluate("() => document.body.dataset.activeTab") == 'route'
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
    pg.wait_for_timeout(300)


def reopen(pg):
    """Recharge la page ; le shell rouvre l'outil par l'adresse. On attend que le Route Planner soit prêt et que sa carte ait cessé de bouger, sans durée fixe."""
    pg.reload(wait_until='commit')
    pg.wait_for_function("() => { const f = document.getElementById('iframe-rp'); return !!f && !!f.contentWindow && !!f.contentWindow.__RP && f.contentDocument.getElementById('rp-split'); }", timeout=90000)
    fr = pg.query_selector('#iframe-rp').content_frame()
    last, same = None, 0
    for _ in range(80):
        h = fr.evaluate("() => document.querySelector('.mapwrap').getBoundingClientRect().height")
        same = same + 1 if h == last else 0
        last = h
        if same >= 4:
            break
        pg.wait_for_timeout(250)
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
    pg.wait_for_timeout(300)
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
    pg.wait_for_timeout(300)
    assert abs(fr.evaluate(GEOM)['map']['h'] - em) <= 1 and fr.evaluate(KEYS)[key] is None
    assert pg.errs == []


@needs_pw
def test_the_on_screen_keyboard_shrinks_the_map_to_its_low_bound(browser):
    pg, fr = rp(browser, 412, 915)
    drag(pg, fr, 40)
    kept = fr.evaluate(GEOM)['map']['h']
    fr.evaluate("() => document.getElementById('route-name').focus()")
    pg.set_viewport_size({'width': 412, 'height': 715})
    pg.wait_for_timeout(900)
    g = fr.evaluate(GEOM)
    f = fr.evaluate("() => { const r = document.getElementById('route-name').getBoundingClientRect(), p = document.getElementById('panel').getBoundingClientRect(); return [r.top >= p.top - 0.5 && r.bottom <= p.bottom + 0.5, p.height]; }")
    assert abs(g['map']['h'] - 220) <= 1 and f[0] and f[1] > 100
    fr.evaluate("() => document.activeElement.blur()")
    pg.wait_for_timeout(500)
    pg.set_viewport_size({'width': 412, 'height': 915})
    pg.wait_for_timeout(700)
    assert abs(fr.evaluate(GEOM)['map']['h'] - kept) <= 1                         # elle revient, la hauteur gardée n'a pas bougé
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
        row.locator('.tbm-trigger').tap()                                       # la liste Réf. : on choisit MER (MSL)
        pg.wait_for_timeout(300)
        fr.locator('.tbm-panel li.tbm-opt').filter(has_text=re.compile('^(MER|MSL)$')).first.tap()
        pg.wait_for_timeout(300)
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
    if w == 716:                                                              # les largeurs de cdp/base.json à 716
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
    pg.wait_for_timeout(13000)                                                  # le toast « Restaurer » de l'exemple est parti
    fr.evaluate("() => showToast('Essai')")
    fr.wait_for_timeout(400)
    t = fr.evaluate(TOAST)
    assert t and abs(t['gap'] - 12) <= 1 and not t['overlaps']
    assert pg.errs == []


@needs_pw
def test_the_toast_stays_20_px_from_the_bottom_with_a_mouse(browser):
    pg, fr = rp(browser, 1280, 800, False)
    pg.wait_for_timeout(13000)
    fr.evaluate("() => showToast('Essai')")
    fr.wait_for_timeout(400)
    t = fr.evaluate(TOAST)
    assert t and abs(t['gap'] - 20) <= 1
    assert pg.errs == []
