"""Petites corrections, lot 2 (MP-V2.1.0+10) : « ⋯ » sous 345 px, le contraste des lignes des menus au clavier, la règle des leurres sans « × 0 », le Kord sur les deux portes du Mi-24P reçu,
la poignée du Route Planner clavier ouvert, la planche haute de l'accueil du Field Manual, les icônes d'onglet du Recon Station. Joué sur le shell construit (dist/dcs_mission_plan.html, chromium, aucun réseau) ;
les contrôles passent par le DOM, jamais par une capture."""
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

def test_the_recon_station_lays_its_tab_icons_like_the_other_builds():
    src = read('build_recon_station.py')
    assert 'from brand_block import add_tab_icons as brand_tab_icons' in src and 'PAGE = brand_tab_icons(HTML)' in src
    assert 'brand_tab_icons_html' not in src and "'<title>Recon Station — Mission Plan</title>\\n' + " not in src


def test_the_phone_plate_of_the_home_screen_sits_under_the_button_row():
    fm = read('dist/dcs_field_manual.html')
    m = re.search(r'<svg class="pl-tall"[^>]*data-aria-fr="L’accueil de Mission Plan au téléphone".*?</svg>', fm, re.S)
    assert m
    rects = [tuple(float(v) for v in r) for r in re.findall(r'<rect class="sv-box" x="([\d.]+)" y="([\d.]+)" width="([\d.]+)" height="([\d.]+)"', m.group(0))]
    bar, row, menu, plate = (next(r for r in rects if r[1] == y) for y in (56.0, 106.0, 140.0, 196.0))   # la barre, la rangée de boutons, le menu Exemple ouvert, la plaque du titre (dans le groupe décalé de 12)
    assert bar[3] == 22 and row[3] == 30 and menu[3] == 36 and plate[2:] == (190.0, 34.0)
    assert plate[1] > row[1] + row[3] and plate[1] >= menu[1] + menu[3]            # sous la rangée de boutons, et le menu ouvert ne la cache pas
    assert m.group(0).count('MISSION PLAN') >= 2 and m.group(0).count('Mission Commander') == 1       # le reste ne change pas


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
    """Chaque test ferme ses contextes : le shell pèse 17 Mo par page, et des dizaines de pages ouvertes à la fois font tomber chromium."""
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


# « ⋯ » : la barre défilée, puis le recalcul. Le constat de la base : barre en « tb-over » défilée de 5 ou 6 px à 326-327 px, un recalcul pose « tb-nos » (la barre se croit entière),
# et « ⋯ » finit hors de l'écran. Sans compenser le défilement, le bord droit du dernier enfant se lisait trop à gauche.
BAR_JS = """() => { const b = document.querySelector('.toolbar'), out = [];
  for (let k = 0; k <= 8; k++) { b.scrollLeft = b.scrollWidth; if (k) b.scrollLeft = Math.min(b.scrollLeft, k); uiBarFit();
    const m = document.getElementById('tb-more-btn'), r = m.getBoundingClientRect(), shown = !m.hasAttribute('data-mp-off');
    out.push({ k, nos: b.classList.contains('tb-nos'), right: shown ? r.right : null, vw: document.documentElement.clientWidth }); }
  return out; }"""


@needs_pw
@pytest.mark.parametrize('w', [322, 326, 327, 344])
@pytest.mark.parametrize('tool', ['bg', 'rp', 'dg', 'fc', 'hq'])
def test_a_scrolled_bar_never_believes_it_fits_with_the_more_button_off_screen(browser, w, tool):
    pg = shell(browser, w, 800, touch=True)
    fr = open_tool(pg, tool, touch=True)
    res = fr.evaluate(BAR_JS)
    bad = [r for r in res if r['nos'] and r['right'] is not None and r['right'] > r['vw'] + 0.01]
    assert bad == [], bad
    assert pg.errs == []


@needs_pw
@pytest.mark.parametrize('w', [345, 412])
@pytest.mark.parametrize('tool,off', [('bg', 'btn-reset,btn-lang'), ('rp', 'tb-label,tb-sel,btn-clear,btn-lang'), ('dg', 'tb-label,tb-sel,btn-reset,btn-lang'),
                                      ('fc', 'tb-label,tb-sel,btn-clear,btn-lang'), ('hq', None)])
def test_at_345_and_412_the_more_button_takes_what_it_took(browser, w, tool, off):
    pg = shell(browser, w, 800, touch=True)
    fr = open_tool(pg, tool, touch=True)
    got = fr.evaluate("() => { const b = document.querySelector('.toolbar'), m = document.getElementById('tb-more-btn'); const r = m.getBoundingClientRect();"
                      " return { off: [...b.querySelectorAll('[data-mp-off]')].filter(e => e !== m).map(e => e.id || e.className.split(' ')[0]).join(','), nos: b.classList.contains('tb-nos'), inside: r.left >= 0 && r.right <= document.documentElement.clientWidth }; }")
    assert got['nos'] and got['inside']
    assert got['off'] == (off if off is not None else {345: 'btn-wing,btn-example,btn-clear,btn-lang', 412: 'btn-example,btn-clear,btn-lang'}[w]), got


# Le contraste texte / fond (4,5 : 1 au moins) de la ligne active d'un menu de la barre, atteinte au clavier (« .active » ou « :focus-visible ») : calculé sur les couleurs rendues,
# le fond de la ligne composé sur celui du panneau (un dégradé : les deux bouts).
CONTRAST_JS = """(() => {
  const cv = document.createElement('canvas'); cv.width = cv.height = 1; const cx = cv.getContext('2d', { willReadFrequently: true });
  const rgba = c => { cx.clearRect(0, 0, 1, 1); cx.fillStyle = '#000'; cx.fillStyle = c; cx.fillRect(0, 0, 1, 1); const d = cx.getImageData(0, 0, 1, 1).data; return [d[0], d[1], d[2], d[3] / 255]; };
  const over = (f, b) => [0, 1, 2].map(i => f[i] * f[3] + b[i] * (1 - f[3]));
  const lum = c => { const k = c.map(v => { v /= 255; return v <= .03928 ? v / 12.92 : Math.pow((v + .055) / 1.055, 2.4); }); return .2126 * k[0] + .7152 * k[1] + .0722 * k[2]; };
  const ratio = (a, b) => { const x = lum(a), y = lum(b); return (Math.max(x, y) + .05) / (Math.min(x, y) + .05); };
  window.__ratio = row => {
    const ps = getComputedStyle(row.closest('.tbm-panel')), cs = getComputedStyle(row);
    let stops = (ps.backgroundImage.match(/rgba?\\([^)]*\\)/g) || []).map(rgba);
    if (!stops.length) stops = [rgba(ps.backgroundColor)];
    const fg = rgba(cs.color), bg = rgba(cs.backgroundColor);
    return Math.min.apply(null, stops.map(s => { const base = over(bg, s.slice(0, 3)); return ratio(over(fg, base), base); }));
  };
})()"""
ROWS_JS = "() => [...document.querySelectorAll('.tbm-panel .tbm-opt')].filter(r => getComputedStyle(r).display !== 'none' && r.getAttribute('aria-disabled') !== 'true').length"


def reach_row(pg, fr, i):
    """La ligne i du menu ouvert, prise au clavier : le focus au clavier (« :focus-visible ») ; rend [le rapport de contraste, la ligne le dit]."""
    pg.mouse.move(2, 2)
    pg.keyboard.press('Shift')
    return fr.evaluate("""(i) => { const r = [...document.querySelectorAll('.tbm-panel .tbm-opt')].filter(r => getComputedStyle(r).display !== 'none' && r.getAttribute('aria-disabled') !== 'true')[i];
      const had = r.hasAttribute('tabindex'); if (!had) r.tabIndex = -1; r.focus(); const fv = r.matches(':focus-visible'); const q = window.__ratio(r); r.blur(); if (!had) r.removeAttribute('tabindex'); return [q, fv]; }""", i)


@needs_pw
@pytest.mark.parametrize('tool,trigger', [('rp', '#btn-open'), ('rp', '#btn-export-menu'), ('rp', '#btn-display'), ('fc', '#btn-open'), ('dg', '#btn-json-import'), ('bg', '#btn-load'), ('rs', '#btn-open'),
                                          ('rp', '#tb-more-btn'), ('bg', '#tb-more-btn'), ('rp', '.tb-switch')])
def test_the_line_reached_with_the_keyboard_reads_in_the_four_themes(browser, tool, trigger):
    pg = shell(browser, 412, 900)
    fr = open_tool(pg, tool)
    fr.evaluate(CONTRAST_JS)
    for theme in THEMES:
        fr.evaluate("(t) => document.body.setAttribute('data-theme', t)", theme)
        if trigger == '#tb-more-btn' or trigger == '.tb-switch':
            fr.locator(trigger).first.click()
        else:
            fr.locator(trigger).focus()
            pg.keyboard.press('ArrowDown')
            pg.wait_for_timeout(250)
            if not fr.evaluate("() => !!document.querySelector('.tbm-panel')"):
                fr.locator(trigger).click()
        pg.wait_for_timeout(300)
        n = fr.evaluate(ROWS_JS)
        assert n >= 1, (theme, n)
        for i in range(min(n, 3)):
            q, fv = reach_row(pg, fr, i)
            assert fv and q >= 4.5, (tool, trigger, theme, i, q)
            fr.evaluate("(i) => { const r = [...document.querySelectorAll('.tbm-panel .tbm-opt')].filter(r => getComputedStyle(r).display !== 'none' && r.getAttribute('aria-disabled') !== 'true')[i]; r.classList.add('active'); window.__q = window.__ratio(r); r.classList.remove('active'); }", i)
            assert fr.evaluate('() => window.__q') >= 4.5, (tool, trigger, theme, i, 'active')
        pg.keyboard.press('Escape')
        pg.wait_for_timeout(250)


@needs_pw
def test_the_example_menu_of_the_home_screen_reads_in_the_four_themes(browser):
    pg = shell(browser, 412, 900)
    pg.evaluate(CONTRAST_JS)
    for theme in THEMES:
        pg.evaluate("(t) => document.body.setAttribute('data-theme', t)", theme)
        pg.locator('#btn-example').focus()
        pg.keyboard.press('ArrowDown')
        pg.wait_for_timeout(300)
        if not pg.evaluate("() => !!document.querySelector('.tbm-panel')"):
            pg.locator('#btn-example').click()
            pg.wait_for_timeout(300)
        assert pg.evaluate(ROWS_JS) == 2
        q, fv = reach_row(pg, pg, 0)
        assert fv and q >= 4.5, (theme, q)
        pg.keyboard.press('Escape')
        pg.wait_for_timeout(250)


# ----- la règle des leurres -----

LIMITS = json.loads(read('data/aircraft_limits.json'))
UNIT = {'fr': ('leurres', 'paillettes'), 'en': ('flares', 'chaff')}


def expected_rule(lang, lim):
    fs, cs, n = lim['flare_charge_size'], lim['chaff_charge_size'], lim['charge_total']
    f, c = UNIT[lang]
    w = lambda k: '' if k == 1 else ' × %d' % k
    if fs == 0 and cs == 0:
        return 'max 0'
    if cs == 0:
        return 'max %d' % n if fs == 1 else '%s × %d ≤ %d' % (f, fs, n)
    if fs == 0:
        return 'max %d' % n if cs == 1 else '%s × %d ≤ %d' % (c, cs, n)
    return '%s%s + %s%s ≤ %d' % (f, w(fs), c, w(cs), n)


@needs_pw
def test_the_charge_rule_never_writes_times_zero_and_the_other_types_do_not_change(browser):
    pg = shell(browser, 1280, 900)
    examples(pg)
    fr = open_tool(pg, 'fc')
    got = {}
    for lang in ('fr', 'en'):
        got[lang] = fr.evaluate("(l) => { CURRENT_LANG = l; const o = {}; Object.keys(AIRCRAFT_LIMITS).forEach(k => { const cl = chargeLimit(AIRCRAFT_LIMITS[k]); o[k] = cl ? chargeRule(cl) : null; }); return o; }", lang)
    fr.evaluate("() => { CURRENT_LANG = 'fr'; }")
    assert len(LIMITS) >= 170
    for lang in ('fr', 'en'):
        for typ, lim in LIMITS.items():
            txt = got[lang][typ]
            if all(isinstance(lim.get(k), (int, float)) for k in ('charge_total', 'flare_charge_size', 'chaff_charge_size')):
                assert txt == expected_rule(lang, lim), (lang, typ, txt)
                assert '× 0' not in txt, (lang, typ, txt)
            else:
                assert txt is None
    assert got['fr']['Mi-8MT'] == 'max 128' and got['en']['Mi-8MT'] == 'max 128'
    assert got['fr']['Mi-24P'] == 'leurres + paillettes ≤ 192' and got['en']['Mi-24P'] == 'flares + chaff ≤ 192'
    assert got['fr']['A-10A'] == 'leurres × 2 + paillettes ≤ 480' and got['en']['A-10A'] == 'flares × 2 + chaff ≤ 480'
    assert got['fr']['F-5E'] == 'max 0'
    assert pg.errs == []


@needs_pw
def test_the_refusal_toast_of_the_mi8mt_says_the_same_rule(browser):
    pg = shell(browser, 1280, 900)
    examples(pg)
    fr = open_tool(pg, 'fc')
    out = fr.evaluate("""() => { const o = {}; ['fr', 'en'].forEach(l => { CURRENT_LANG = l; o[l] = [loCheck('Mi-8MT', null, 'flare', '200', false).err, loCheck('A-10A', null, 'flare', '300', false).err, loCheck('Mi-24P', null, 'flare', '300', false).err]; }); CURRENT_LANG = 'fr'; return o; }""")
    assert out['fr'][0] == '⚠ Au-delà du maximum : max 128 (200 demandé)'
    assert out['en'][0] == '⚠ Above the maximum: max 128 (200 requested)' and out['en'][2].startswith('⚠ Above the maximum: flares + chaff ≤ 192 (')
    assert out['fr'][2].startswith('⚠ Au-delà du maximum : leurres + paillettes ≤ 192 (') and out['fr'][1].startswith('⚠ Au-delà du maximum : leurres × 2 + paillettes ≤ 480 (')
    assert pg.errs == []


# ----- les portes du Mi-24P -----

# Les valeurs de payloadRuleConflicts, hors la règle des portes (« oneof »), sur 55 types à règles, 40 emports tirés (graine fixe) par type, chaque station, et les emports des exemples : l'empreinte relevée à la base (994e471).
GOLDEN_JS = r"""() => {
  let seed = 12345; const rnd = () => { seed |= 0; seed = seed + 0x6D2B79F5 | 0; let t = Math.imul(seed ^ seed >>> 15, 1 | seed); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; };
  const types = Object.keys(Object.assign({}, PAYLOAD_RULES, PAYLOAD_GAME_RULES)).filter(ty => has(AIRCRAFT_PYLONS.types, ty)).sort();
  let n = 0, parts = 0, h = 2166136261;
  const mix = s => { for (let i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619) >>> 0; } };
  types.forEach(ty => {
    const pyl = AIRCRAFT_PYLONS.types[ty], keys = Object.keys(pyl).sort((a, b) => Number(a) - Number(b));
    for (let k = 0; k < 40; k++) {
      const st = {}; keys.forEach(s => { const l = pyl[s]; st[s] = (rnd() < .45 || !l.length) ? '' : AIRCRAFT_PYLONS.clsids[l[Math.floor(rnd() * l.length)]]; });
      keys.forEach(s => { if (st[s] === '') return; const out = payloadRuleConflicts(ty, st, s, st[s]).filter(x => x.rule !== 'oneof'); mix(ty + '|' + k + '|' + s + '|' + JSON.stringify(out)); n++; parts += out.length; });
    }
  });
  S.flights.forEach(g => g.units.forEach(u => { if (!u.loadout) return; const pyl = AIRCRAFT_PYLONS.types[u.type]; if (!pyl) return; const st = {}; Object.keys(pyl).forEach(s => { st[s] = (u.loadout.pylons[s] && u.loadout.pylons[s].CLSID) || ''; });
    Object.keys(st).forEach(s => { if (st[s] === '') return; const out = payloadRuleConflicts(u.type, st, s, st[s]).filter(x => x.rule !== 'oneof'); mix('ex|' + u.type + '|' + s + '|' + JSON.stringify(out)); n++; parts += out.length; }); }));
  const pyl = AIRCRAFT_PYLONS.types['Mi-24P'], L = AIRCRAFT_PYLONS.clsids[pyl['7'][0]], R = AIRCRAFT_PYLONS.clsids[pyl['8'][0]], one = AIRCRAFT_PYLONS.clsids[pyl['1'][0]];
  const st0 = {}; Object.keys(pyl).forEach(s => { st0[s] = ''; });
  const raw = [['7', L, {}], ['8', R, {}], ['7', L, { '8': R }], ['8', R, { '7': L }], ['1', one, { '7': L, '8': R }]].map(a => { const st = Object.assign({}, st0, a[2]); st[a[0]] = a[1]; return payloadRuleConflicts('Mi-24P', st, a[0], a[1]); });
  const other = Object.keys(PAYLOAD_RULES).filter(t => t !== 'Mi-24P').every(t => payloadOneOfOthers(t, '7').length === 0);
  return { types: types.length, calls: n, entries: parts, hash: h.toString(16), raw, other }; }"""


@needs_pw
def test_payload_rule_conflicts_gives_the_same_values_and_reports_only_the_two_doors(browser):
    pg = shell(browser, 1280, 900)
    examples(pg)
    fr = open_tool(pg, 'fc')
    r = fr.evaluate(GOLDEN_JS)
    assert (r['types'], r['calls'], r['entries'], r['hash']) == (55, 9600, 1226, 'c37938cb')
    assert r['raw'] == [[], [], [{'st': '8', 'rule': 'oneof'}], [{'st': '7', 'rule': 'oneof'}], []] and r['other']
    assert pg.errs == []


KORD_DOM = """() => { const r = {}; document.querySelectorAll('#blk-cmp .cmp-row').forEach(row => { const n = row.getAttribute('data-st'); const rl = row.querySelector('.cmp-rule'); const oo = row.querySelector('.cmp-oneof');
  r[n] = { rule: rl ? rl.textContent : null, sel: row.querySelector('select').value, oo: oo && !oo.hidden ? oo.textContent : '' }; });
  const keep = document.querySelector('#blk-cmp [data-act="cmp-save"]'), u = selUnit();
  return { rows: r, keepDisabled: keep ? keep.disabled : null, keepTitle: keep ? keep.getAttribute('title') : null, blocked: cmpBlocked(cmpStations(u.u.loadout)) }; }"""


@needs_pw
@pytest.mark.parametrize('lang,phrase,rule,title', [('fr', 'une seule porte porte le Kord', 'Incompatible avec la station {0} : {1}', 'Corrigez les stations signalées pour garder cet emport dans vos presets'),
                                                     ('en', 'only one door carries the Kord', 'Clashes with station {0}: {1}', 'Fix the flagged stations to keep this loadout in your presets')])
def test_a_received_loadout_with_the_kord_on_both_doors_is_reported_under_both(browser, lang, phrase, rule, title):
    pg = shell(browser, 1280, 900, lang=lang)
    examples(pg)
    fr = open_tool(pg, 'fc')
    ids = fr.evaluate("() => ({ l: AIRCRAFT_PYLONS.clsids[110], r: AIRCRAFT_PYLONS.clsids[111] })")
    assert ids == {'l': 'KORD_12_7_MI24_L', 'r': 'KORD_12_7_MI24_R'}
    # un fichier de travail : le Kord gauche en 7 et le droit en 8, rien d'autre ; le shell le rouvre
    pg.evaluate("""(c) => { const fs = JSON.parse(localStorage.getItem('flight_set_v1')); const u = fs.flights[0].units[0]; u.loadout.pylons = { '7': { CLSID: c.l }, '8': { CLSID: c.r } }; localStorage.setItem('flight_set_v1', JSON.stringify(fs)); }""", ids)
    pg.reload(wait_until='commit')
    pg.wait_for_function("() => typeof window.MP_WORK_EXAMPLE === 'function' && !!document.getElementById('card-hq')", timeout=60000)
    pg.wait_for_selector('#iframe-fc', state='attached', timeout=30000)
    pg.wait_for_timeout(3500)
    fr = pg.query_selector('#iframe-fc').content_frame()
    got = fr.evaluate(KORD_DOM)
    assert got['rows']['7']['rule'] == rule.format(8, phrase) and got['rows']['8']['rule'] == rule.format(7, phrase), got['rows']
    assert got['rows']['7']['sel'] == 'KORD_12_7_MI24_L' and got['rows']['8']['sel'] == 'KORD_12_7_MI24_R'        # rien n'est vidé
    assert all(got['rows'][n]['rule'] is None for n in got['rows'] if n not in ('7', '8'))
    assert got['blocked'] is True and got['keepDisabled'] is True and got['keepTitle'] == title      # comme tout autre conflit reçu : « Garder dans mes presets » est désactivé
    # et le geste : une porte vide ne grise pas le Kord parce que l'autre l'a ; le choisir vide l'autre, avec son message, sans la phrase
    opts = fr.evaluate("""() => { const sel = document.querySelector('#blk-cmp .cmp-row[data-st="7"] select'); return [...sel.options].filter(o => /KORD/.test(o.value)).map(o => [o.value, o.disabled, o.textContent.indexOf('—') >= 0]); }""")
    assert opts and all(not o[1] and not o[2] for o in opts), opts
    assert pg.errs == []


@needs_pw
def test_the_gesture_on_the_two_doors_is_unchanged(browser):
    pg = shell(browser, 1280, 900)
    examples(pg)
    fr = open_tool(pg, 'fc')
    fr.evaluate("() => { selUnit().u.loadout = null; renderRight(); }")
    pg.wait_for_timeout(500)

    def pick(n):
        fr.locator('#blk-cmp .cmp-row[data-st="%s"] .tbm-trigger' % n).click()
        pg.wait_for_timeout(300)
        fr.locator('.tbm-panel .tbm-opt').filter(has_text='Kord').first.click()
        pg.wait_for_timeout(400)
    pick(7)
    a = fr.evaluate(KORD_DOM)
    assert a['rows']['7']['sel'] == 'KORD_12_7_MI24_L' and a['rows']['8']['sel'] == '' and not a['blocked']
    pick(8)
    b = fr.evaluate(KORD_DOM)
    assert b['rows']['7']['sel'] == '' and b['rows']['8']['sel'] == 'KORD_12_7_MI24_R' and b['rows']['8']['oo'] == 'Une seule porte : retiré de la station 7'
    assert b['rows']['7']['rule'] is None and b['rows']['8']['rule'] is None and not b['blocked'] and b['keepDisabled'] is False
    assert pg.errs == []


# ----- la poignée du Route Planner, clavier ouvert -----

W, H, D = 412, 915, 330
SPLIT_GEOM = "() => document.querySelector('.mapwrap').getBoundingClientRect().height"
SPLIT_KEY = "() => localStorage.getItem('rp_split_v1')"


def handle_xy(pg, fr):
    off = pg.evaluate("() => { const r = document.getElementById('iframe-rp').getBoundingClientRect(); return [r.left, r.top]; }")
    b = fr.evaluate("() => { const r = document.getElementById('rp-split').getBoundingClientRect(); return [r.left + r.width / 2, r.top + r.height / 2]; }")
    return b[0] + off[0], b[1] + off[1]


def drag(pg, fr, dy):
    x, y = handle_xy(pg, fr)
    pg.mouse.move(x, y)
    pg.mouse.down()
    for i in range(1, 9):
        pg.mouse.move(x, y + dy * i / 8)
    pg.mouse.up()
    pg.wait_for_timeout(300)


def double_tap(pg, fr):
    x, y = handle_xy(pg, fr)
    pg.mouse.move(x, y)
    pg.mouse.down(); pg.mouse.up()
    pg.wait_for_timeout(80)
    pg.mouse.down(); pg.mouse.up()
    pg.wait_for_timeout(400)


def kb_open(pg, fr):
    fr.evaluate("(id) => document.getElementById(id).focus()", 'route-name')
    pg.wait_for_timeout(200)
    pg.set_viewport_size({'width': W, 'height': H - D})
    pg.wait_for_timeout(900)
    assert fr.evaluate("() => document.documentElement.classList.contains('ui-kb')")


def kb_close(pg, fr):
    fr.evaluate("() => document.activeElement.blur()")
    pg.wait_for_timeout(400)
    pg.set_viewport_size({'width': W, 'height': H})
    pg.wait_for_timeout(900)


@needs_pw
def test_the_handle_writes_nothing_while_the_keyboard_is_open_and_the_map_comes_back(browser):
    pg = shell(browser, W, H, touch=True)
    examples(pg)
    fr = open_tool(pg, 'rp', touch=True, wait=2800)
    drag(pg, fr, 40)                                        # clavier fermé : la hauteur est gardée
    kept_map, kept_key = fr.evaluate(SPLIT_GEOM), fr.evaluate(SPLIT_KEY)
    assert kept_key is not None and abs(float(kept_key) - kept_map) <= 1
    kb_open(pg, fr)
    assert abs(fr.evaluate(SPLIT_GEOM) - 220) <= 1                                       # la carte à sa hauteur du clavier
    drag(pg, fr, -30)
    assert fr.evaluate(SPLIT_KEY) == kept_key                                            # glisser : rien d'écrit
    kb_close(pg, fr)
    assert abs(fr.evaluate(SPLIT_GEOM) - kept_map) <= 1 and fr.evaluate(SPLIT_KEY) == kept_key
    kb_open(pg, fr)
    double_tap(pg, fr)                                                                   # deux touchers : rien d'écrit ni d'effacé
    assert fr.evaluate(SPLIT_KEY) == kept_key
    kb_close(pg, fr)
    assert abs(fr.evaluate(SPLIT_GEOM) - kept_map) <= 1 and fr.evaluate(SPLIT_KEY) == kept_key
    drag(pg, fr, 25)                                                                     # clavier fermé : comme avant
    assert abs(float(fr.evaluate(SPLIT_KEY)) - (kept_map + 25)) <= 1
    double_tap(pg, fr)
    assert fr.evaluate(SPLIT_KEY) is None
    assert pg.errs == []
