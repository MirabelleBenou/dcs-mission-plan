"""Les cibles au doigt (44 px), les champs à 16 px, la barre de l'accueil qui se replie sous « ⋯ », la raison d'une ligne grisée.
Les textes (CHANGELOG, numéro de dev) et le CSS commun, lus dans les sources ; puis le shell construit (dist/dcs_mission_plan.html, chromium, aucun réseau),
joué au doigt et à la souris. Les contrôles passent par le DOM."""
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

CHROMIUM = Path('/opt/pw-browsers/chromium')
try:
    import playwright.sync_api  # noqa: F401
    HAS_PW = CHROMIUM.exists()
except ImportError:
    HAS_PW = False
needs_pw = pytest.mark.skipif(not HAS_PW, reason='playwright ou chromium absent')

SHELL = 'file://' + str(ROOT / 'dist' / 'dcs_mission_plan.html')

TEXT_TOUCH = ("**Easier to touch with a finger**\n"
              "- On a touch screen, every button, list and field is at least 44 px tall and wide; with a mouse nothing changes.\n"
              "- On a phone, fields use 16 px text, so the page no longer zooms in when you type (between 520 and 760 px wide, the Route Planner’s waypoint rows still use smaller text).\n")
TEXT_WHY = ("**Greyed-out commands say why**\n"
            "- In the “⋯” menu, a command that cannot be used shows the reason under it, such as HQ’s Example when the Wing configuration is provided by another tool.\n")
TEXT_HOME = ("### Home screen\n\n"
             "**The top bar fits on a phone**\n"
             "- What does not fit, theme and language, moves into a “⋯” menu at its right end, as in the tools; the theme name is no longer cut.\n")
TEXT_RP = ("**Map controls for the finger**\n"
           "- On a touch screen, zoom, search and the Point · Ref. · Read · Draw · Ruler modes are 44 px, and so is the handle between map and panel.\n")
TEXT_RP_TABS = ("**Tabs at the bottom on a phone**\n"
                "- On a phone or tablet, the map stays in view above the panel, which now has four tabs at the bottom of the screen — Route, Ref., Layers and Nav. — in the same bar as the Briefing and Datacard Generators; map and panel start at about half the screen each, and the handle still resizes them.\n"
                "- Below 520 px wide, a waypoint row takes two lines, the name on the first, altitude, speed and reference on the second; with a finger, its text is 16 px.\n")


def _unreleased():
    log = (ROOT / 'CHANGELOG.md').read_text(encoding='utf-8')
    return log.split('\n## Unreleased\n', 1)[1].split('\n## ', 1)[0]


def _section(text, title):
    return text.split('\n### %s\n' % title, 1)[1].split('\n### ', 1)[0]


def test_the_changelog_says_what_the_lot_says_where_it_says_it():
    u = _unreleased()
    heads = re.findall(r'^### (.+)$', u, flags=re.M)
    assert heads.index('Home screen') == heads.index('All tools') + 1 and heads.index('HQ') == heads.index('Home screen') + 1
    all_tools = _section(u, 'All tools')
    assert (TEXT_TOUCH + '\n' + TEXT_WHY.rstrip('\n')) in all_tools and all_tools.index(TEXT_TOUCH) < all_tools.index(TEXT_WHY)       # le lot mp-mobile-selecteur ajoute son entrée après celle-ci
    assert '\n' + TEXT_HOME in u and u.count(TEXT_HOME) == 1
    rp = _section(u, 'Route Planner').split('\n\n**“Clear everything”')[0]
    assert rp.rstrip('\n').endswith((TEXT_RP + '\n' + TEXT_RP_TABS).rstrip('\n'))                 # l'entrée du lot mp-mobile-rp-onglets suit aussitôt celle-ci et termine la rubrique
    assert u.count(TEXT_TOUCH) == 1 and u.count(TEXT_WHY) == 1 and u.count(TEXT_RP) == 1


def test_the_dev_build_is_7_and_the_changelog_says_so():
    import version_block
    assert version_block.DEV_BUILD == 11
    log = (ROOT / 'CHANGELOG.md').read_text(encoding='utf-8')
    assert '`MP-V2.1.0+3` is the third update since 2.1.0' in log          # la phrase d'en-tête, que le lot ne touche pas
    assert 'for this one;' in log and '`MP-V2.1.0+11` for this one' in log


def test_the_common_stylesheet_has_the_finger_rules_under_coarse_pointers_only():
    src = (ROOT / 'ui_block.py').read_text(encoding='utf-8')
    i = src.index('@media (pointer: coarse) {')
    block44 = src[i:src.index('}\n}', i)]
    assert 'min-width: 44px; min-height: 44px' in block44 and ':where(' in block44
    j = src.index('@media (pointer: coarse) and (max-width: 759px) {')
    block16 = src[j:src.index('}\n}', j)]
    assert 'font-size: 16px' in block16 and ':is(' in block16
    # la règle des 44 px n'existe qu'une fois, dans la requête « pointeur grossier » (l'autre 44 px de la feuille est le bouton « ⋯ », déjà là avant le lot)
    assert src.count('{ min-width: 44px; min-height: 44px; }') == 1 and src.index('{ min-width: 44px; min-height: 44px; }') < src.index('@media (pointer: coarse) and (max-width: 759px)')
    assert '.tb-more-why' in src and 'color: var(--paper)' in src[src.index('.tb-more-why'):src.index('.tb-more-why') + 300]      # la raison se lit : la couleur du texte du menu
    assert ':not(.leaflet-container *)' in block44 and block44.startswith('@media (pointer: coarse) {\n  :where(')           # rien dans une carte Leaflet, à spécificité nulle
    assert 'getAttribute(\'data-mp-why\')' in src and 'u.el.title' not in src[src.index('function uiBarMoreWhy'):src.index('function uiBarMoreWhy') + 400]


def test_the_route_planner_rules_are_for_the_finger_alone():
    src = (ROOT / 'build_route_planner.py').read_text(encoding='utf-8')
    i = src.index('@media (pointer: coarse) {\n  .in { min-height: 44px; }')
    j = src.index('"""\nCSS = CSS.replace(', i)
    block = src[i:j]
    assert '.rp-split { height: 44px; }' in block and 'minmax(0, 1fr)' in block
    assert block.count('@media (pointer: coarse)') == block.count('@media')
    # la ligne de point : la hauteur seule, aucun 16 px jusqu'à 759 px, la police d'avant (le reste est listé au rapport du lot)
    assert '(max-width: 759px)' in block and 'font-size: 16px' not in block


# ---------- le shell construit ----------
@pytest.fixture(scope='module')
def browser():
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        br = p.chromium.launch(executable_path=str(CHROMIUM), args=['--no-sandbox'])
        yield br
        br.close()


def new_page(br, w, h, touch, lang='fr', seed=''):
    ctx = br.new_context(viewport={'width': w, 'height': h}, has_touch=touch, is_mobile=touch, locale=lang + '-' + lang.upper())
    ctx.add_init_script("(() => { try { if (!sessionStorage.getItem('seeded')) { sessionStorage.setItem('seeded', '1'); localStorage.clear(); localStorage.setItem('lang_v1', '%s'); } } catch (e) {} })();" % lang)
    if seed:
        ctx.add_init_script(seed)
    pg = ctx.new_page()
    errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.route('**/*', lambda r: r.continue_() if r.request.url.startswith(('file:', 'data:', 'blob:')) else r.abort())
    pg.goto('about:blank')
    pg.goto(SHELL, wait_until='commit')
    pg.wait_for_function("typeof openModule === 'function'", timeout=20000)
    pg.wait_for_timeout(1500)
    pg.errs = errs
    return pg


RAIL = """() => {
  const vis = e => { if (!e) return false; const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0 && !e.hasAttribute('data-mp-off'); };
  const R = e => { const r = e.getBoundingClientRect(); return [Math.round(r.width * 10) / 10, Math.round(r.height * 10) / 10]; };
  const ctrl = document.querySelector('.rail .ctrl'), more = document.getElementById('tb-more-btn');
  const theme = ctrl.querySelector('.tbm-trigger'), flag = document.getElementById('flag-btn');
  return { more: vis(more), moreSize: more ? R(more) : null, theme: vis(theme), flag: vis(flag), fm: vis(document.getElementById('btn-fm')),
    open: vis(document.getElementById('btn-work-open')), save: vis(document.getElementById('btn-work-save')), example: vis(document.getElementById('btn-example')),
    scroll: [ctrl.scrollWidth, ctrl.clientWidth], pageOverflow: document.documentElement.scrollWidth > innerWidth + 1,
    sizes: Object.fromEntries(['btn-work-open', 'btn-work-save', 'btn-example', 'btn-fm', 'flag-btn'].map(id => [id, vis(document.getElementById(id)) ? R(document.getElementById(id)) : null])) }; }"""

ROWS = """() => { const p = document.querySelector('.tb-more-panel'); if (!p) return null;
  return [...p.querySelectorAll('.tbm-opt')].map(li => ({ txt: li.innerText.replace(/\\s+/g, ' ').trim(), chev: !!li.querySelector('.tb-more-chev'), why: !!li.querySelector('.tb-more-why') })); }"""


@needs_pw
@pytest.mark.parametrize('w,h', [(345, 590), (412, 915)])
def test_on_a_phone_the_home_bar_folds_the_language_and_the_theme_under_more(browser, w, h):
    pg = new_page(browser, w, h, True)
    r = pg.evaluate(RAIL)
    assert r['more'] and r['moreSize'] == [44, 44]
    assert not r['theme'] and not r['flag']
    assert r['open'] and r['save'] and r['example'] and r['fm']              # les fichiers et le Manuel restent
    assert r['scroll'][0] <= r['scroll'][1] + 1 and not r['pageOverflow']      # la barre ne défile plus, la page non plus
    for k, size in r['sizes'].items():
        if size:
            assert size[0] >= 43.5 and size[1] >= 43.5, (k, size)
    pg.locator('#tb-more-btn').tap()
    pg.wait_for_timeout(400)
    rows = pg.evaluate(ROWS)
    names = [x['txt'].upper() for x in rows]
    assert len(rows) == 2                                                     # le thème (une liste) et la langue : rien d'autre
    assert sum(1 for x in rows if x['chev']) == 1                             # « Thème ▸ » ouvre une liste
    assert any('THÈME' in n or 'THEME' in n for n in names) and any('LANGUE' in n or 'LANGUAGE' in n for n in names)
    assert pg.errs == []


@needs_pw
def test_on_a_phone_a_theme_is_chosen_from_the_menu_and_the_language_toggles(browser):
    pg = new_page(browser, 345, 590, True)
    pg.locator('#tb-more-btn').tap()
    pg.wait_for_timeout(300)
    rows = pg.evaluate(ROWS)
    t = [i for i, x in enumerate(rows) if x['chev']][0]
    pg.locator('.tb-more-panel .tbm-opt').nth(t).tap()
    pg.wait_for_timeout(400)
    assert pg.evaluate(ROWS) is None                                          # la liste remplace le menu
    pg.locator('.tbm-panel .tbm-opt').nth(2).tap()
    pg.wait_for_timeout(400)
    assert pg.evaluate("() => document.body.getAttribute('data-theme')") == 'modern-nato'
    pg.locator('#tb-more-btn').tap()
    pg.wait_for_timeout(300)
    before = pg.evaluate("() => document.documentElement.lang")
    lang = [i for i, x in enumerate(pg.evaluate(ROWS)) if not x['chev']][0]
    pg.locator('.tb-more-panel .tbm-opt').nth(lang).tap()
    pg.wait_for_timeout(500)
    assert pg.evaluate("() => document.documentElement.lang") != before
    pg.locator('#tb-more-btn').tap()
    pg.wait_for_timeout(300)
    assert pg.evaluate(ROWS) is not None
    pg.mouse.click(172, 570)                                                  # un toucher dehors ferme le menu
    pg.wait_for_timeout(300)
    assert pg.evaluate(ROWS) is None
    assert pg.errs == []


@needs_pw
def test_with_a_mouse_the_home_bar_keeps_everything_in_view(browser):
    pg = new_page(browser, 1280, 800, False)
    r = pg.evaluate(RAIL)
    assert not r['more'] and r['theme'] and r['flag'] and r['fm'] and r['open'] and r['save'] and r['example']
    assert pg.evaluate("() => document.querySelectorAll('.rail [data-mp-off]').length") == 0
    assert pg.errs == []


@needs_pw
@pytest.mark.parametrize('lang', ['fr', 'en'])
def test_a_command_that_cannot_be_used_says_why_under_its_text(browser, lang):
    seed = "try { localStorage.setItem('wing_config_v1', JSON.stringify({ managedBy: 'Another Tool', shortName: 'TST' })); } catch (e) {}"
    pg = new_page(browser, 345, 590, True, lang, seed)
    pg.evaluate("() => openModule('hq')")
    pg.wait_for_selector('#iframe-hq', state='attached')
    pg.wait_for_timeout(2600)
    f = pg.query_selector('#iframe-hq').content_frame()
    f.evaluate("() => document.getElementById('tb-more-btn').click()")
    pg.wait_for_timeout(500)
    rows = f.evaluate("""() => [...document.querySelectorAll('.tb-more-panel .tbm-opt')].map(li => ({ txt: li.innerText.replace(/\\s+/g, ' ').trim().toUpperCase(),
        off: li.getAttribute('aria-disabled') === 'true', why: (li.querySelector('.tb-more-why') || {}).innerText || '',
        size: li.querySelector('.tb-more-why') ? getComputedStyle(li.querySelector('.tb-more-why')).fontSize : '',
        color: li.querySelector('.tb-more-why') ? getComputedStyle(li.querySelector('.tb-more-why')).color : '' }))""")
    pap = f.evaluate("() => { const t = document.createElement('span'); t.style.color = 'var(--paper)'; document.body.appendChild(t); const c = getComputedStyle(t).color; t.remove(); return c; }")
    ex = [x for x in rows if x['txt'].startswith(('EXEMPLE', 'EXAMPLE'))][0]
    assert ex['off'] and ex['size'] == '12px'
    assert ex['color'] == pap                                                   # la raison prend la couleur du texte du menu, pas le gris des lignes grisées
    assert ex['why'] == ('Configuration fournie par Another Tool' if lang == 'fr' else 'Configuration provided by Another Tool')
    # un toucher sur la ligne grisée n'ouvre rien et laisse le menu ouvert
    idx = rows.index(ex)
    f.locator('.tb-more-panel .tbm-opt').nth(idx).dispatch_event('click')
    pg.wait_for_timeout(500)
    assert f.evaluate("() => [...document.querySelectorAll('.ui-modal')].filter(m => m.getBoundingClientRect().height > 0).length") == 0
    assert f.evaluate("() => !!document.querySelector('.tb-more-panel')")
    # les lignes actives n'ont pas de seconde ligne
    assert all(not x['why'] for x in rows if not x['off'])
    # « Effacer » grisé (aucune mission) a un title mais aucune raison donnée : pas de seconde ligne
    clear = [x for x in rows if x['txt'].startswith(('EFFACER', 'CLEAR'))][0]
    assert clear['off'] and clear['why'] == ''
    assert pg.errs == []


@needs_pw
def test_without_a_managed_wing_the_example_row_is_active_and_has_no_second_line(browser):
    pg = new_page(browser, 345, 590, True)
    pg.evaluate("() => openModule('hq')")
    pg.wait_for_selector('#iframe-hq', state='attached')
    pg.wait_for_timeout(2600)
    f = pg.query_selector('#iframe-hq').content_frame()
    f.evaluate("() => document.getElementById('tb-more-btn').click()")
    pg.wait_for_timeout(500)
    rows = f.evaluate("""() => [...document.querySelectorAll('.tb-more-panel .tbm-opt')].map(li => ({ txt: li.innerText.replace(/\\s+/g, ' ').trim().toUpperCase(),
        off: li.getAttribute('aria-disabled') === 'true', col: !!li.querySelector('.tb-more-col') }))""")
    ex = [x for x in rows if x['txt'].startswith(('EXEMPLE', 'EXAMPLE'))][0]
    assert not ex['off'] and not ex['col'] and ex['txt'] in ('EXEMPLE', 'EXAMPLE')
    assert pg.errs == []


@needs_pw
def test_the_route_planner_map_controls_and_the_handle_are_44_px_with_a_finger(browser):
    pg = new_page(browser, 412, 915, True)
    pg.evaluate("() => openModule('rp')")
    pg.wait_for_selector('#iframe-rp', state='attached')
    pg.wait_for_timeout(2800)
    f = pg.query_selector('#iframe-rp').content_frame()
    m = f.evaluate("""() => { const R = e => { const r = e.getBoundingClientRect(); return [Math.round(r.width * 10) / 10, Math.round(r.height * 10) / 10]; };
        const search = [...document.querySelectorAll('button, a, [role=button]')].find(e => /Rechercher sur la carte|Search the map/i.test(e.getAttribute('aria-label') || e.title || ''));
        const sp = document.getElementById('rp-split'), g = sp.querySelector('.grip'), a = sp.getBoundingClientRect(), b = g.getBoundingClientRect();
        return { zin: R(document.querySelector('.leaflet-control-zoom-in')), zout: R(document.querySelector('.leaflet-control-zoom-out')), search: R(search),
          modes: [...document.querySelectorAll('#tapmode .tb-btn')].map(R), split: R(sp), centered: Math.abs((b.top + b.height / 2) - (a.top + a.height / 2)) <= 3 }; }""")
    assert m['zin'] == [44, 44] and m['zout'] == [44, 44] and m['search'] == [44, 44]
    assert len(m['modes']) == 5 and all(h == 44 and w >= 43.5 for w, h in m['modes'])
    assert m['split'][1] == 44 and m['centered']
    assert pg.errs == []


@needs_pw
def test_on_a_phone_fields_are_16_px_and_with_a_mouse_they_are_not_touched(browser):
    pg = new_page(browser, 345, 590, True)
    pg.evaluate("() => openModule('bg')")
    pg.wait_for_selector('#iframe-bg', state='attached')
    pg.wait_for_timeout(2600)
    f = pg.query_selector('#iframe-bg').content_frame()
    small = f.evaluate("""() => [...document.querySelectorAll('input:not([type=checkbox]):not([type=radio]):not([type=hidden]):not([type=range]):not([type=file]):not([type=color]), select, textarea')]
        .filter(e => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0 && parseFloat(getComputedStyle(e).fontSize) < 16; }).length""")
    assert small == 0
    pg2 = new_page(browser, 1280, 800, False)
    pg2.evaluate("() => openModule('bg')")
    pg2.wait_for_selector('#iframe-bg', state='attached')
    pg2.wait_for_timeout(2600)
    g = pg2.query_selector('#iframe-bg').content_frame()
    sizes = g.evaluate("""() => [...document.querySelectorAll('input[type=text], select')].filter(e => e.getBoundingClientRect().width > 0).map(e => parseFloat(getComputedStyle(e).fontSize))""")
    assert sizes and max(sizes) < 16
    assert pg.errs == [] and pg2.errs == []


def _open(pg, tid, wait=2600):
    pg.evaluate("(id) => openModule(id)", tid)
    pg.wait_for_selector('#iframe-' + tid, state='attached')
    pg.wait_for_timeout(wait)
    return pg.query_selector('#iframe-' + tid).content_frame()


@needs_pw
@pytest.mark.parametrize('w,h', [(345, 590), (412, 915)])
def test_the_briefing_generator_bottom_tabs_keep_their_content_floor_and_the_phase_bar_has_44_px_columns(browser, w, h):
    pg = new_page(browser, w, h, True)
    f = _open(pg, 'bg')
    r = f.evaluate("""() => { const bs = [...document.querySelectorAll('.tab-bar button')].filter(b => b.getBoundingClientRect().width > 0);
        return { n: bs.length, floor: [...new Set(bs.map(b => getComputedStyle(b).minWidth))],
          spill: bs.filter(b => { const r = b.getBoundingClientRect(), g = document.createRange(); g.selectNodeContents(b); return [...g.getClientRects()].some(q => q.width > 0 && (r.left - q.left > 1 || q.right - r.right > 1)); }).map(b => b.innerText.trim()),
          widths: bs.map(b => Math.round(b.getBoundingClientRect().width * 10) / 10) }; }""")
    assert r['n'] >= 4 and r['floor'] == ['auto'] and r['spill'] == []             # le texte reste dans sa case ; les onglets ne sont pas égalisés par un plancher de 44 px
    f.evaluate("() => { setFormat('full'); }")
    pg.wait_for_timeout(600)
    f.evaluate("() => { document.querySelector('.tab-bar button[data-tab=\"mission\"]').click(); }")
    pg.wait_for_timeout(800)
    p = f.evaluate("""() => { const bar = [...document.querySelectorAll('.phase-bar')].find(b => b.getBoundingClientRect().width > 0);
        const cols = getComputedStyle(bar).gridTemplateColumns.split(' ').map(parseFloat);
        return { cols: cols, over: [...bar.children].some((c, i) => i < cols.length && c.getBoundingClientRect().width > cols[i] + 0.5) }; }""")
    assert p['cols'][0] == 44 and p['cols'][2:] == [44, 44, 44, 44] and p['cols'][1] >= 40 and not p['over']
    assert pg.errs == []


@needs_pw
def test_the_recon_station_sliders_are_44_px_tall_and_draw_their_rail_on_the_track(browser):
    pg = new_page(browser, 412, 915, True)
    f = _open(pg, 'rs')
    r = f.evaluate("""() => { const e = document.getElementById('contrast-slider'); const cs = getComputedStyle(e); return { minH: cs.minHeight, bg: cs.backgroundColor }; }""")
    assert r['minH'] == '44px' and r['bg'] == 'rgba(0, 0, 0, 0)'                      # l'élément ne porte plus le dessin
    # la piste (4 px, khaki, 2 px d'arrondi) et le pouce recentré : le CSS du module (le rendu est comparé au pixel près à la base par le banc du lot)
    src = (ROOT / 'build_recon_station.py').read_text(encoding='utf-8')
    blk = src[src.index('@media (pointer: coarse) {{\n  .ed-slider {{ background: transparent; }}'):]
    blk = blk[:blk.index('}}\n\n')]
    assert '::-webkit-slider-runnable-track {{ height: 4px; background: var(--khaki); border-radius: 2px; }}' in blk
    assert '::-moz-range-track {{ height: 4px; background: var(--khaki); border-radius: 2px; }}' in blk
    assert '::-webkit-slider-thumb {{ margin-top: -5px; }}' in blk
    pg2 = new_page(browser, 1280, 800, False)                                          # à la souris, la base : le rail est sur l'élément, 4 px
    g = _open(pg2, 'rs')
    m = g.evaluate("""() => { const e = document.getElementById('contrast-slider'); const cs = getComputedStyle(e); return { h: cs.height, minH: cs.minHeight, bg: cs.backgroundColor }; }""")
    assert m['h'] == '4px' and m['minH'] != '44px' and m['bg'] != 'rgba(0, 0, 0, 0)'
    assert pg.errs == [] and pg2.errs == []


@needs_pw
def test_the_44_px_rule_does_not_reach_inside_a_map_except_the_controls_the_route_planner_asks_for(browser):
    pg = new_page(browser, 412, 915, True)
    f = _open(pg, 'rp', 2800)
    r = f.evaluate("""() => { const m = document.querySelector('.leaflet-container');
        const mk = (tag, role) => { const e = document.createElement(tag); if (role) e.setAttribute('role', role); e.textContent = 'x'; m.appendChild(e); const h = getComputedStyle(e).minHeight; e.remove(); return h; };
        const out = document.createElement('button'); out.textContent = 'x'; document.body.appendChild(out); const outside = getComputedStyle(out).minHeight; out.remove();
        const R = e => { const q = e.getBoundingClientRect(); return [Math.round(q.width), Math.round(q.height)]; };
        return { inButton: mk('button'), inRole: mk('a', 'button'), inSelect: mk('select'), outside: outside,
          zoom: R(document.querySelector('.leaflet-control-zoom-in')), search: R(document.querySelector('.rp-search-btn')), modes: [...document.querySelectorAll('#tapmode .tb-btn')].map(b => R(b)[1]) }; }""")
    assert r['inButton'] != '44px' and r['inRole'] != '44px' and r['inSelect'] != '44px'      # un bouton, une croix de fiche (a role=button) ou une liste dans la carte : la règle ne les atteint pas
    assert r['outside'] == '44px'                                                              # hors de la carte, elle joue
    assert r['zoom'] == [44, 44] and r['search'] == [44, 44] and r['modes'] == [44] * 5       # les commandes que le RP demande
    assert pg.errs == []
