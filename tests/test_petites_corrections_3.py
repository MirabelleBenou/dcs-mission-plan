"""Petites corrections, lot 3 (MP-V2.1.0+15) : la ligne « Supprimer » des menus, le champ Paillettes grisé, le menu « ⋯ » et les onglets bas au clavier, Exporter d'un seul geste.
Joué sur le shell construit (dist/dcs_mission_plan.html, chromium, aucun réseau) ; les contrôles passent par le DOM, jamais par une capture."""
import json
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
SEED = "(() => { try { if (localStorage.getItem('lang_v1') === null) localStorage.setItem('lang_v1', '@@'); } catch (e) {} })();"
THEMES = ['cw-nato', 'cw-soviet', 'modern-nato', 'modern-east']


def read(name):
    return (ROOT / name).read_text(encoding='utf-8')


# ----- le texte, sans navigateur -----

def test_the_four_export_buttons_carry_the_one_marker_and_every_guard_reads_it():
    marked = {'build_datacard_generator.py': 'id="btn-print" data-tb-direct', 'build_briefing_generator.py': 'id="btn-print" data-tb-direct',
              'build_recon_station.py': 'id="btn-export" data-tb-direct', 'build_flight_configurator.py': "' tb-file', None, ' data-tb-direct'"}
    for f, frag in marked.items():
        assert read(f).count(frag) == 1, f
    ui = read('ui_block.py')
    assert ui.count("[data-tb-direct]") == 1 and ui.count('uiDirectBtn') >= 4
    for f in ('build_datacard_generator.py', 'build_briefing_generator.py', 'build_recon_station.py', 'build_flight_configurator.py', 'build_route_planner.py'):
        guards = re.findall(r'function (?:mnOutside|dspOutside)\(e\) \{.*?\n\}', read(f), re.S)
        assert guards and all('uiDirectBtn(t)' in g for g in guards), f
        assert not any('btn-print' in g or 'btn-export' in g for g in guards), f
    for fn in ('uiBarMoreOutside', 'uiSwOutside', 'tbmOutside'):
        body = re.search(r'function ' + fn + r'\(ev?\) \{.*?\n\}', ui, re.S).group(0)
        assert 'uiDirectBtn' in body and 'btn-print' not in body and 'btn-export' not in body, fn


def test_the_not_carried_key_is_in_both_dictionaries():
    fc = read('build_flight_configurator.py')
    assert fc.count("'lo.notcarried': 'non emportées'") == 1 and fc.count("'lo.notcarried': 'not carried'") == 1


# ----- le navigateur -----

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


def shell(br, w, h, lang='fr', touch=False):
    kw = dict(has_touch=True, is_mobile=True) if touch else {}
    ctx = br.new_context(viewport={'width': w, 'height': h}, locale=lang + '-' + lang.upper(), **kw)
    ctx.add_init_script(SEED.replace('@@', lang))
    ctx.route('**/*', lambda r: r.continue_() if r.request.url.startswith(('file:', 'data:', 'blob:')) else r.abort())
    CONTEXTS.append(ctx)
    pg = ctx.new_page()
    pg.errs = []
    pg.on('pageerror', lambda e: pg.errs.append(str(e)[:200]))
    pg.goto(SHELL, wait_until='commit')
    pg.wait_for_function("() => typeof window.MP_WORK_EXAMPLE === 'function' && !!document.getElementById('card-hq')", timeout=60000)
    pg.wait_for_timeout(1300)
    return pg


def examples(pg):
    for g in ('mc', 'fl'):
        pg.evaluate('(g) => window.MP_WORK_EXAMPLE(g)', g)
        pg.wait_for_timeout(800)


def open_tool(pg, tid, touch=False, wait=2600):
    card = pg.locator('#card-' + tid)
    card.scroll_into_view_if_needed()
    try:
        card.tap(timeout=5000) if touch else card.click(timeout=5000)
    except Exception:
        card.click()
    pg.wait_for_selector('#iframe-' + tid, state='attached')
    pg.wait_for_timeout(wait)
    return pg.query_selector('#iframe-' + tid).content_frame()


# ----- règle 1 : « Supprimer » sous le pointeur, au clavier et active -----

PROBE_JS = """(() => {
  const cv = document.createElement('canvas'); cv.width = cv.height = 1; const cx = cv.getContext('2d', { willReadFrequently: true });
  const rgba = c => { cx.clearRect(0, 0, 1, 1); cx.fillStyle = '#000'; cx.fillStyle = c; cx.fillRect(0, 0, 1, 1); const d = cx.getImageData(0, 0, 1, 1).data; return [d[0], d[1], d[2], d[3] / 255]; };
  const lum = c => { const k = c.map(v => { v /= 255; return v <= .03928 ? v / 12.92 : Math.pow((v + .055) / 1.055, 2.4); }); return .2126 * k[0] + .7152 * k[1] + .0722 * k[2]; };
  window.__probe = row => {
    const cs = getComputedStyle(row), bg = rgba(cs.backgroundColor), fg = rgba(cs.color), mark = row.querySelector('.tbm-mark');
    const x = lum(fg), y = lum(bg);
    return { bg: cs.backgroundColor, fg: cs.color, bgA: bg[3], ratio: (Math.max(x, y) + .05) / (Math.min(x, y) + .05), mark: mark ? getComputedStyle(mark).borderTopColor : null };
  };
  window.__var = v => { const e = document.createElement('i'); e.style.color = 'var(' + v + ')'; document.body.appendChild(e); const c = getComputedStyle(e).color; e.remove(); return c; };
})()"""
WARN = 'rgb(232, 128, 106)'
DARK = 'rgb(20, 17, 10)'


@needs_pw
@pytest.mark.parametrize('tool,trigger', [('dg', '#pk-more'), ('rp', '#rs-more')])
def test_the_delete_line_turns_to_the_warning_fill_in_the_four_themes(browser, tool, trigger):
    pg = shell(browser, 1280, 900)
    examples(pg)
    fr = open_tool(pg, tool)
    fr.evaluate(PROBE_JS)
    for theme in THEMES:
        fr.evaluate("(t) => document.body.setAttribute('data-theme', t)", theme)
        pg.wait_for_timeout(150)
        fr.locator(trigger).click()
        pg.wait_for_timeout(300)
        danger = fr.locator('.tbm-panel .tbm-opt.mn-danger')
        assert danger.count() == 1
        other = fr.locator('.tbm-panel .tbm-opt:not(.mn-danger):not([aria-disabled="true"])').first
        # au repos : le texte d'avertissement sur le fond du panneau, comme avant
        pg.mouse.move(2, 2)
        rest = fr.evaluate("() => window.__probe(document.querySelector('.tbm-panel .tbm-opt.mn-danger'))")
        assert rest['fg'] == fr.evaluate("() => window.__var('--mp-warn')") == WARN and rest['bgA'] == 0, (theme, rest)
        # survolée
        danger.hover()
        pg.wait_for_timeout(150)
        got = fr.evaluate("() => window.__probe(document.querySelector('.tbm-panel .tbm-opt.mn-danger'))")
        assert got['bg'] == WARN and got['fg'] == DARK and got['mark'] in (None, DARK) and got['ratio'] >= 6.9, (theme, 'hover', got)
        # au clavier (:focus-visible)
        pg.mouse.move(2, 2)
        pg.keyboard.press('Shift')
        got = fr.evaluate("""() => { const r = document.querySelector('.tbm-panel .tbm-opt.mn-danger'); r.tabIndex = -1; r.focus();
          return Object.assign({ fv: r.matches(':focus-visible') }, window.__probe(r)); }""")
        assert got['fv'] and got['bg'] == WARN and got['fg'] == DARK and got['mark'] in (None, DARK) and got['ratio'] >= 6.9, (theme, 'focus', got)
        fr.evaluate("() => document.querySelector('.tbm-panel .tbm-opt.mn-danger').blur()")
        # active
        got = fr.evaluate("() => { const r = document.querySelector('.tbm-panel .tbm-opt.mn-danger'); r.classList.add('active'); const o = window.__probe(r); r.classList.remove('active'); return o; }")
        assert got['bg'] == WARN and got['fg'] == DARK and got['mark'] in (None, DARK) and got['ratio'] >= 6.9, (theme, 'active', got)
        # les autres lignes ne changent pas : le fond olive du thème, jamais le fond d'avertissement
        other.hover()
        pg.wait_for_timeout(150)
        got = fr.evaluate("() => window.__probe(document.querySelector('.tbm-panel .tbm-opt:not(.mn-danger):not([aria-disabled=\"true\"]):hover'))")
        assert got['bg'] == fr.evaluate("() => window.__var('--olive')") and got['bg'] != WARN, (theme, 'other', got)
        pg.keyboard.press('Escape')
        pg.wait_for_timeout(200)
    assert pg.errs == []


# ----- règle 2 : le champ Paillettes grisé -----

LIMITS = json.loads(read('data/aircraft_limits.json'))
LABELS_JS = """([type, lang]) => {
  CURRENT_LANG = lang;
  const f = { units: [{ type: type, props: {} }] };
  const d = document.createElement('div'); d.innerHTML = cmpSettingsHtml(f, 0, null);
  const o = {};
  d.querySelectorAll('.ed-field').forEach(e => { const i = e.querySelector('input[data-k]'); if (i) o[i.getAttribute('data-k')] = [e.querySelector('label').textContent, i.disabled]; });
  CURRENT_LANG = 'fr';
  return o;
}"""


@needs_pw
def test_only_the_greyed_chaff_field_says_not_carried(browser):
    pg = shell(browser, 1280, 900)
    examples(pg)
    fr = open_tool(pg, 'fc')
    word = {'fr': 'non emportées', 'en': 'not carried'}
    names = {'fr': ('Leurres', 'Paillettes'), 'en': ('Flares', 'Chaff')}
    seen = {'fr': {}, 'en': {}}
    greyed = 0
    for lang in ('fr', 'en'):
        for typ in LIMITS:
            try:
                o = fr.evaluate(LABELS_JS, [typ, lang])
            except Exception:
                continue                       # un type sans masses connues n'a pas de champs à montrer
            seen[lang][typ] = o
            flare, chaff = o.get('flare'), o.get('chaff')
            if flare:
                assert flare[0].startswith(names[lang][0] + ' · ') and word[lang] not in flare[0] and not flare[1], (lang, typ, flare)
            if chaff:
                assert chaff[0].startswith(names[lang][1] + ' · '), (lang, typ, chaff)
                if chaff[1]:
                    greyed += 1
                    assert chaff[0] == names[lang][1] + ' · ' + word[lang], (lang, typ, chaff)
                else:
                    assert word[lang] not in chaff[0], (lang, typ, chaff)
                    if flare and LIMITS[typ].get('charge_total') is not None:
                        assert chaff[0].split(' · ', 1)[1] == flare[0].split(' · ', 1)[1], (lang, typ, chaff, flare)   # un champ non grisé garde sa règle, au caractère près
    assert len(seen['fr']) >= 100 and greyed >= 2
    assert seen['fr']['Mi-8MT']['flare'][0] == 'Leurres · max 128' and seen['fr']['Mi-8MT']['chaff'] == ['Paillettes · non emportées', True]
    assert seen['en']['Mi-8MT']['flare'][0] == 'Flares · max 128' and seen['en']['Mi-8MT']['chaff'] == ['Chaff · not carried', True]
    assert seen['fr']['Mi-24P']['flare'][0] == 'Leurres · leurres + paillettes ≤ 192' and seen['fr']['Mi-24P']['chaff'] == ['Paillettes · leurres + paillettes ≤ 192', False]
    assert seen['en']['Mi-24P']['chaff'] == ['Chaff · flares + chaff ≤ 192', False]
    assert pg.errs == []


# ----- règle 3 : « ⋯ » au clavier -----

MORE_ROWS_JS = "() => [...document.querySelectorAll('.tb-more-panel .tbm-opt')].map(r => ({ t: r.textContent.trim(), act: r.classList.contains('active'), foc: r === document.activeElement, dis: r.getAttribute('aria-disabled') === 'true', ti: r.getAttribute('tabindex') }))"


def focused_row(fr):
    rows = fr.evaluate(MORE_ROWS_JS)
    foc = [i for i, r in enumerate(rows) if r['foc']]
    return rows, (foc[0] if foc else None)


@needs_pw
@pytest.mark.parametrize('tool', ['bg', 'rp'])
def test_the_more_menu_walks_from_the_keyboard_at_345(browser, tool):
    pg = shell(browser, 345, 800)
    fr = open_tool(pg, tool)
    if tool == 'rp':
        fr.evaluate("() => { document.getElementById('btn-clear').disabled = true; uiBarFit(); }")       # une ligne grisée au milieu : jamais atteinte
        pg.wait_for_timeout(300)
    fr.locator('#tb-more-btn').focus()
    pg.keyboard.press('Enter')
    pg.wait_for_timeout(250)
    rows, cur = focused_row(fr)
    n = len(rows)
    assert n >= 2 and all(r['ti'] == '-1' for r in rows)
    ok = [i for i, r in enumerate(rows) if not r['dis']]
    assert cur == ok[0] and rows[cur]['act'] and sum(r['act'] for r in rows) == 1
    if tool == 'rp':
        assert any(r['dis'] for r in rows)
    seq = [cur]
    for _ in range(len(ok) + 1):
        pg.keyboard.press('ArrowDown')
        seq.append(focused_row(fr)[1])
    assert seq == [ok[i % len(ok)] for i in range(len(ok) + 2)], seq              # jusqu'au bout, puis une fois de plus : la première ; aucune ligne grisée
    pg.keyboard.press('ArrowUp')
    assert focused_row(fr)[1] == ok[((len(ok) + 1) % len(ok) - 1) % len(ok)]
    pg.keyboard.press('Home')
    pg.keyboard.press('ArrowUp')
    assert focused_row(fr)[1] == ok[-1]                                   # ↑ depuis la première : la dernière, en boucle
    pg.keyboard.press('Home')
    assert focused_row(fr)[1] == ok[0]
    pg.keyboard.press('End')
    assert focused_row(fr)[1] == ok[-1]
    assert sum(r['act'] for r in focused_row(fr)[0]) == 1
    # Entrée sur la langue : la langue change, le menu se ferme
    lang0 = fr.evaluate('() => CURRENT_LANG')
    langrow = [i for i, r in enumerate(rows) if r['t'].lower().startswith(('langue', 'language'))][0]
    pg.keyboard.press('Home')
    while focused_row(fr)[1] != langrow:
        pg.keyboard.press('ArrowDown')
    pg.keyboard.press('Enter')
    pg.wait_for_timeout(400)
    assert fr.evaluate('() => CURRENT_LANG') != lang0 and fr.evaluate("() => !document.querySelector('.tb-more-panel')")
    assert fr.evaluate("() => document.activeElement.id") == 'tb-more-btn'
    # Espace ouvre, Échap ferme et rend le focus à « ⋯ »
    pg.keyboard.press(' ')
    pg.wait_for_timeout(250)
    assert fr.evaluate("() => !!document.querySelector('.tb-more-panel') && document.activeElement.classList.contains('tbm-opt')")
    pg.keyboard.press('Escape')
    pg.wait_for_timeout(200)
    assert fr.evaluate("() => !document.querySelector('.tb-more-panel') && document.activeElement.id") == 'tb-more-btn'
    # ↓ ouvre aussi ; Tab ferme
    pg.keyboard.press('ArrowDown')
    pg.wait_for_timeout(250)
    assert fr.evaluate("() => !!document.querySelector('.tb-more-panel')")
    pg.keyboard.press('Tab')
    pg.wait_for_timeout(200)
    assert fr.evaluate("() => !document.querySelector('.tb-more-panel')")
    assert pg.errs == []


@needs_pw
def test_the_more_menu_opened_with_a_finger_has_no_active_row_and_the_list_row_opens_with_enter(browser):
    pg = shell(browser, 345, 800, touch=True)
    fr = open_tool(pg, 'rp', touch=True)
    fr.locator('#tb-more-btn').tap()
    pg.wait_for_timeout(300)
    rows = fr.evaluate(MORE_ROWS_JS)
    assert rows and not any(r['act'] or r['foc'] for r in rows)
    pg.keyboard.press('Escape')
    pg.wait_for_timeout(200)
    fr.locator('#tb-more-btn').focus()
    pg.keyboard.press('Enter')
    pg.wait_for_timeout(250)
    first = fr.evaluate(MORE_ROWS_JS)[0]['t']
    assert first.lower().startswith(('théâtre', 'theatre'))
    pg.keyboard.press('Enter')                                        # « Théâtre ▸ » : la liste s'ouvre comme au clic
    pg.wait_for_timeout(400)
    assert fr.evaluate("() => !document.querySelector('.tb-more-panel') && !!document.querySelector('.tbm-panel')")
    assert pg.errs == []


# ----- règle 4 : Exporter d'un geste -----

EXPORT = {'dg': '#btn-print', 'bg': '#btn-print', 'fc': '#btn-export', 'rs': '#btn-export'}
MENUS = {'dg': ['#btn-display', '#btn-json-import', '#pk-pick', '#pk-more'], 'bg': ['#btn-display', '#btn-load'], 'fc': ['#btn-display', '#btn-open'], 'rs': ['#btn-open']}
OPEN_JS = "() => document.querySelectorAll('.tbm-panel').length"
MODAL_JS = "() => [...document.querySelectorAll('.ui-modal')].filter(m => getComputedStyle(m).display !== 'none' && !m.hidden).map(m => m.id)"
PROBE_BTN_JS = """() => { let b = document.getElementById('mp-probe'); if (!b) { b = document.createElement('button'); b.id = 'mp-probe'; b.type = 'button';
  b.style.cssText = 'position:fixed;left:0;bottom:0;width:100%;height:6px;padding:0;border:0;z-index:2147483647';       /* une bande sous tout panneau : la liste des outils remplit la fenêtre à 345 px */ b.addEventListener('click', () => { window.__probeClicks = (window.__probeClicks || 0) + 1; }); document.body.appendChild(b); }
  window.__probeClicks = 0; }"""


def press(pg, fr, sel, touch):
    box = fr.locator(sel).first.bounding_box()
    x, y = box['x'] + box['width'] / 2, box['y'] + box['height'] / 2
    pg.touchscreen.tap(x, y) if touch else pg.mouse.click(x, y)
    pg.wait_for_timeout(450)


def visible(fr, sel):
    return fr.evaluate("(s) => { const e = document.querySelector(s); return !!e && !e.closest('[data-mp-off]') && getComputedStyle(e).display !== 'none' && e.getBoundingClientRect().width > 0; }", sel)


def kinds(fr, tool):
    """Les sortes d'ouvert que l'outil a à cette largeur : la liste des outils, « ⋯ », une liste au thème, chaque menu du module."""
    out = [('tools', '.tb-switch')]
    if visible(fr, '#tb-more-btn'):
        out.append(('more', '#tb-more-btn'))
    for s in ('.toolbar .tbm-trigger',):
        if visible(fr, s):
            out.append(('list', s))
    for s in MENUS[tool]:
        if visible(fr, s):
            out.append(('menu ' + s, s))
    return out


@needs_pw
@pytest.mark.parametrize('touch,w', [(True, 345), (False, 1440)])
@pytest.mark.parametrize('tool', ['dg', 'bg', 'fc', 'rs'])
def test_one_tap_on_export_closes_what_is_open_and_opens_the_window(browser, tool, touch, w):
    pg = shell(browser, w, 900, touch=touch)
    examples(pg)
    fr = open_tool(pg, tool, touch=touch)
    fr.evaluate(PROBE_BTN_JS)
    for d in (pg, fr):
        d.evaluate("() => document.querySelectorAll('.toast, #toast').forEach(e => { e.style.pointerEvents = 'none'; })")       # le toast « Restaurer » de l'exemple ne couvre pas la bande neutre
    ex = EXPORT[tool]
    assert fr.evaluate("(s) => document.querySelector(s).hasAttribute('data-tb-direct') && !document.querySelector(s).disabled", ex)
    ks = kinds(fr, tool)
    assert len(ks) >= (2 if tool == 'rs' else 3), ks
    for name, sel in ks:
        # un toucher sur Exporter : l'ouvert se ferme, la fenêtre d'export s'ouvre
        press(pg, fr, sel, touch)
        assert fr.evaluate(OPEN_JS) >= 1, (tool, name, 'ne s\'ouvre pas')
        press(pg, fr, ex, touch)
        assert fr.evaluate(OPEN_JS) == 0, (tool, name, 'reste ouvert')
        mods = fr.evaluate(MODAL_JS)
        assert len(mods) == 1 and mods[0] in ('export-modal', 'fn-modal'), (tool, name, mods)
        pg.keyboard.press('Escape')
        pg.wait_for_timeout(300)
        assert fr.evaluate(MODAL_JS) == []
        # un toucher sur une zone neutre : fermé, le clic est avalé ; le toucher suivant agit normalement
        press(pg, fr, sel, touch)
        assert fr.evaluate(OPEN_JS) >= 1
        fr.evaluate("() => { window.__probeClicks = 0; }")
        press(pg, fr, '#mp-probe', touch)
        assert fr.evaluate(OPEN_JS) == 0 and fr.evaluate('() => window.__probeClicks') == 0 and fr.evaluate(MODAL_JS) == [], (tool, name, 'neutre')
        press(pg, fr, '#mp-probe', touch)
        assert fr.evaluate('() => window.__probeClicks') == 1, (tool, name, 'le toucher suivant')
    assert pg.errs == []


@needs_pw
@pytest.mark.parametrize('touch,w', [(True, 345), (False, 1440)])
def test_export_greyed_in_the_recon_station_closes_what_is_open_and_opens_nothing(browser, touch, w):
    pg = shell(browser, w, 900, touch=touch)
    fr = open_tool(pg, 'rs', touch=touch)
    assert fr.evaluate("() => document.getElementById('btn-export').disabled")
    for name, sel in kinds(fr, 'rs'):
        press(pg, fr, sel, touch)
        assert fr.evaluate(OPEN_JS) >= 1, name
        press(pg, fr, '#btn-export', touch)
        assert fr.evaluate(OPEN_JS) == 0 and fr.evaluate(MODAL_JS) == [], name
    assert pg.errs == []


# ----- règle 5 : les onglets bas au clavier -----

TABS_JS = """() => [...document.querySelectorAll('.ui-tabbar > [role="tab"]')].map(b => ({ id: b.id, tab: b.dataset.tab, sel: b.getAttribute('aria-selected'), ti: b.getAttribute('tabindex'), shown: getComputedStyle(b).display !== 'none',
  ctl: (b.getAttribute('aria-controls') || '').split(' ').filter(x => x), foc: b === document.activeElement }))"""
PANELS_JS = """() => { const bad = []; document.querySelectorAll('.ui-tabbar > [role="tab"]').forEach(b => { (b.getAttribute('aria-controls') || '').split(' ').filter(x => x).forEach(id => {
  const e = document.getElementById(id); if (!e) { bad.push(['missing', b.id, id]); return; }
  if (e.getAttribute('role') !== 'tabpanel' || e.getAttribute('aria-labelledby') !== b.id) bad.push(['panel', b.id, id]); }); });
  document.querySelectorAll('[role="tabpanel"]').forEach(p => { const t = document.getElementById(p.getAttribute('aria-labelledby')); if (!t || (t.getAttribute('aria-controls') || '').split(' ').indexOf(p.id) < 0) { if (t && getComputedStyle(t).display === 'none') return; bad.push(['reverse', p.id]); } });
  return bad; }"""
SHOWN_JS = "() => document.body.dataset.activeTab"


def walk_tabs(pg, fr, expect_active_visible):
    tabs = fr.evaluate(TABS_JS)
    vis = [t for t in tabs if t['shown']]
    cur = [t for t in tabs if t['sel'] == 'true']
    assert len(cur) == 1 and [t['tab'] for t in tabs if t['ti'] == '0'] == [cur[0]['tab']]
    assert all(t['ti'] == '-1' for t in tabs if t is not cur[0])
    assert fr.evaluate(PANELS_JS) == []
    fr.locator('.ui-tabbar > [role="tab"][aria-selected="true"]').focus()
    names = [t['tab'] for t in vis]
    i = names.index(cur[0]['tab'])
    for key, j in (('ArrowRight', (i + 1) % len(names)), ('ArrowLeft', i), ('End', len(names) - 1), ('Home', 0), ('ArrowLeft', len(names) - 1), ('ArrowRight', 0)):
        pg.keyboard.press(key)
        pg.wait_for_timeout(150)
        now = fr.evaluate(TABS_JS)
        sel = [t for t in now if t['sel'] == 'true']
        assert len(sel) == 1 and sel[0]['tab'] == names[j] and sel[0]['foc'] and [t['tab'] for t in now if t['ti'] == '0'] == [names[j]], (key, names[j], sel)
        assert fr.evaluate(SHOWN_JS) == names[j]
        assert fr.evaluate(PANELS_JS) == []
    return names


@needs_pw
@pytest.mark.parametrize('tool,fmt', [('dg', None), ('rp', None), ('bg', 'full'), ('bg', 'simple')])
def test_the_bottom_tabs_follow_the_tabs_pattern_at_412(browser, tool, fmt):
    pg = shell(browser, 412, 915, touch=True)
    examples(pg)
    fr = open_tool(pg, tool, touch=True)
    if fmt:
        fr.evaluate("(f) => { state.meta.format = f; applyFormatUi(); }", fmt)
        pg.wait_for_timeout(500)
    names = walk_tabs(pg, fr, True)
    want = {'dg': ['mission', 'group', 'nav', 'radio', 'weather', 'meta', 'preview'], 'rp': ['route', 'refs', 'layers', 'nav'],
            'bg': ['header', 'sitac', 'mission', 'radio', 'annexes', 'meta', 'preview'] if fmt == 'full' else ['header', 's-situation', 's-mission', 's-coord', 's-photos', 'meta', 'preview']}[tool]
    assert names == want, names                                    # un onglet masqué par le format est sauté
    tabs = fr.evaluate(TABS_JS)
    assert all(t['id'] for t in tabs)
    if tool == 'bg':
        hidden = [t for t in tabs if not t['shown']]
        assert hidden and all(t['ti'] == '-1' and not t['ctl'] for t in hidden)
    if tool == 'dg':
        assert next(t for t in tabs if t['tab'] == 'nav')['ctl'] == ['tp-nav', 'tp-refs', 'tp-fields'] or len(next(t for t in tabs if t['tab'] == 'nav')['ctl']) == 3
    assert pg.errs == []


@needs_pw
@pytest.mark.parametrize('tool', ['dg', 'rp', 'bg'])
def test_above_1100_px_there_is_no_tab_bar_and_the_arrow_keys_do_nothing_to_it(browser, tool):
    pg = shell(browser, 1440, 900)
    examples(pg)
    fr = open_tool(pg, tool)
    assert fr.evaluate("() => getComputedStyle(document.querySelector('.ui-tabbar')).display") == 'none'
    before = fr.evaluate(SHOWN_JS)
    pg.keyboard.press('ArrowRight')
    assert fr.evaluate(SHOWN_JS) == before
    assert pg.errs == []
