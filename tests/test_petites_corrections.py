"""Petites corrections (MP-V2.1.0+8) : la lecture sûre d'un briefing (mergeDeep), « Restaurer » après « Ouvrir un briefing… », l'espace fine avant « ? »,
« Clear everything » au Route Planner, le bouton « Wing » d'HQ à sa place, l'avertissement d'un vol créé, la carte libre du Datacard Generator, le repli
des groupes du Flight Configurator et les textes du lot. Les contrôles passent par le DOM du shell construit (dist/dcs_mission_plan.html, chromium, aucun réseau)."""
import copy
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_hq_addprop as hqp  # noqa: E402

CHROMIUM = Path('/opt/pw-browsers/chromium')
try:
    import playwright.sync_api  # noqa: F401
    HAS_PW = CHROMIUM.exists()
except ImportError:
    HAS_PW = False
needs_pw = pytest.mark.skipif(not HAS_PW, reason='playwright ou chromium absent')
NODE = shutil.which('node')
needs_node = pytest.mark.skipif(NODE is None, reason='node absent')

SHELL = 'file://' + str(ROOT / 'dist' / 'dcs_mission_plan.html')
NB = ' '


def dist(name):
    return (ROOT / 'dist' / name).read_text(encoding='utf-8')


# ---------- les textes ----------
def test_french_questions_take_the_narrow_no_break_space():
    expect = {
        'dcs_hq.html': ["'hq.open.title': 'Ouvrir un autre .miz" + NB + "?'", "'hq.revert.title': 'Annuler les modifications" + NB + "?'",
                        "'dyn.w.why': 'Pourquoi d’autres bases n’apparaissent pas" + NB + "?'"],
        'dcs_recon_station.html': ["'clear.title': 'Effacer le Recon Station" + NB + "?'"],
        'dcs_briefing_generator.html': ["'editor.roster.delGroupConfirm': 'Supprimer ce groupe" + NB + "?'"],
    }
    for name, lines in expect.items():
        text = dist(name)
        for line in lines:
            assert line in text, (name, line)
            assert line.encode('utf-8').count(b'\xe2\x80\xaf?') == 1
    rx = re.compile(r"[A-Za-zÀ-ÿ»\)] \?(['\"<]|$)", re.M)
    for f in sorted(ROOT.glob('build_*.py')) + sorted(ROOT.glob('fm_*.py')) + sorted(ROOT.glob('*_block.py')):
        assert not rx.search(f.read_text(encoding='utf-8')), f.name


def test_route_planner_clear_everything():
    rp = dist('dcs_route_planner.html')
    assert "'clr.all': 'Clear everything'" in rp and "'clr.all': 'Tout effacer'" in rp
    for f in (ROOT / 'dist').glob('*.html'):
        assert 'Clear all' not in f.read_text(encoding='utf-8'), f.name


def test_point_ref_dropped_keys_and_unchanged_found_flight_key():
    hq = dist('dcs_hq.html')
    assert "'pk.w.pointRefDropped': '{0} : point {1} : référence à une unité de la mission du paquet ({2} = {3}) — retirée'" in hq
    assert "'pk.w.pointRefDropped': '{0}: point {1}: refers to a unit of the package’s mission ({2} = {3}) — removed'" in hq
    assert "'pk.w.pointRef': '{0} : point {1} : référence à une unité de la mission du paquet ({2} = {3}) — à vérifier'" in hq
    assert "'pk.w.pointRef': '{0}: point {1}: refers to a unit of the package’s mission ({2} = {3}) — check it'" in hq


ALL_TOOLS_2 = ["**Fixed: “⋯” on very narrow screens**\n- Below 345 px wide, after the toolbar was scrolled, “⋯” could end up off the screen; it now stays in view.",
               "**Menus easier to read from the keyboard**\n- In the toolbar's menus, the line reached with the arrow keys now has enough contrast in every theme."]
CHANGELOG = {
    '### HQ': ["**The Wing button keeps its place**\n- The Wing button now always sits between Flight packages and Example, whether or not the wing is set up; until it is, the button stays highlighted.",
              "**A clearer warning on a created flight**\n- When a package creates a flight, a waypoint that pointed to a unit of the package’s mission is reported as removed, no longer as to be checked."],
    '### Flight Configurator': ["**Folded groups stay folded**\n- A group you fold, on its own or with Fold all, is still folded when you come back or reload.", "**Fixed: countermeasure limits without chaff**\n- For an aircraft that carries no chaff, such as the Mi-8MT, the limit now reads “max 128” instead of a formula with “chaff × 0”.",
                                    "**The Kord on both doors is reported**\n- A Mi-24P loadout received with something on both doors — from a file, a preset or a copy — now shows the conflict under both doors, like any other rule."],
    '### Briefing Generator': ["**Restore after opening a briefing**\n- Open a briefing… now offers Restore for 12 seconds, like the other tools: it brings back the briefing you had before.",
                               "**Fixed: briefing files are read safely**\n- A briefing file, or a briefing kept by the browser, can no longer change how the page works through special keys such as __proto__."],
    '### Route Planner': ["**“Clear everything”, as in the other tools**\n- In English, the button of the Clear window now reads “Clear everything”.",
                          "**Fixed: the map height after typing**\n- On a phone, moving the handle while the on-screen keyboard is open no longer keeps the map small once the keyboard closes.",
                          "**Threats layer**\n- A hostile SAM, AAA or radar symbol can be given its system, among the game’s 57 air defence systems; with Threats ticked in Display, the map shows where an aircraft at the checked height above the ground is seen and within firing range, masked by DCS’s relief, with the firing and detection ranges. On a theatre without relief, only the ranges are drawn.\n- Where the route is seen at its planned altitude, it is outlined in yellow, and the navigation sheet says by which threat and over what distance.\n- The checked height goes up to 20,000 ft (6,000 m) at least, whatever the ceilings; above a system’s ceiling, that system no longer tints.\n- Ceilings now come from Whiskey 188’s DCS SAM Threat Guide, taken from the game’s files, for the systems it covers; otherwise from Goldwolf’s DCS Threats Guide."],
    '### Datacard Generator': ["**Fixed: a free card kept its last aircraft**\n- When every crew line of a free card goes back to “to pick”, the Aircraft and Count fields empty instead of keeping the last aircraft found."],
    '### Field Manual': ["**The HQ screen drawn with the Wing button in its place**\n- The two drawings of the HQ screen show the toolbar in its new order.",
                         "**The home screen drawn with its insignia**\n- The two drawings of the home screen show the insignia and the family's icon.",
                         "**The phone drawing of the home screen in the right order**\n- The title plate now sits under the toolbar buttons, as on screen.",
                         "**Threats**\n- The Route Planner page explains the threats layer and lists the game’s air defence systems with their ranges and ceilings."],
}


def test_changelog_entries_end_their_sections():
    log = (ROOT / 'CHANGELOG.md').read_text(encoding='utf-8')
    unreleased = log.split('\n## Unreleased\n', 1)[1].split('\n## ', 1)[0]
    for head, entries in CHANGELOG.items():
        sec = unreleased.split('\n' + head + '\n', 1)[1].split('\n### ', 1)[0].rstrip('\n')
        assert sec.endswith('\n\n'.join(entries)), head
    assert 'MP-V2.1.0+15` for this one' in unreleased and 'MP-V2.1.0+8' not in log
    all_tools = unreleased.split('\n### All tools\n', 1)[1].split('\n### ', 1)[0]
    assert all_tools.rstrip('\n').endswith('a wing still on the former “WG” logo shows the new one and still counts as not set up.\n\n' + '\n\n'.join(ALL_TOOLS_2))


def test_hq_legend_numbers_follow_the_toolbar():
    sys.path.insert(0, str(ROOT))
    import fm_planches_block as fp
    rows = fp._hq_legend_rows()
    nums = [r[0] for r in rows]
    assert nums == sorted(nums) == list(range(1, 13))
    src = (ROOT / 'fm_planches_block.py').read_text(encoding='utf-8')
    order = [m.group(1) for m in re.finditer(r"\(\d+, \[L\('hq', '([a-zA-Z.]+)'\)", src[src.index('def _hq_legend_rows'):src.index('def build_plate_hq')])][:7]
    assert order == ['tb.open', 'tb.save', 'tb.revert', 'tb.pk', 'tb.wing', 'toolbar.example', 'tb.clear']


# ---------- mergeDeep ----------
def merge_deep_source():
    text = dist('dcs_briefing_generator.html')
    i = text.index('function mergeDeep(')
    j = text.index('{', i)
    depth, k = 0, j
    while True:
        c = text[k]
        if c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0:
                return text[i:k + 1]
        k += 1


@needs_node
def test_merge_deep_ignores_the_dangerous_keys_at_every_level():
    src = merge_deep_source() + r"""
    const raw = '{"meta":{"title":"T","__proto__":{"p2":1}},"__proto__":{"p1":1},"constructor":{"prototype":{"p3":1}},"prototype":{"p4":1},"sitac":{"__proto__":{"p5":1},"metar":"M","constructor":{"x":1}},"phases":[{"title":"A"}]}';
    const out = mergeDeep({ meta: { title: 'd', classification: 'c' }, sitac: { metar: '' } }, JSON.parse(raw));
    console.log(JSON.stringify({ polluted: [({}).p1, ({}).p2, ({}).p3, ({}).p4, ({}).p5, Object.prototype.p3, Object.p4].map(x => x === undefined),
      ctor: typeof ({}).constructor, own: Object.keys(out), meta: out.meta, sitac: out.sitac, phases: out.phases }));
    """
    r = subprocess.run([NODE, '-e', src], capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr
    o = json.loads(r.stdout)
    assert all(o['polluted']) and o['ctor'] == 'function'
    assert o['own'] == ['meta', 'sitac', 'phases']
    assert o['meta'] == {'title': 'T', 'classification': 'c'} and o['sitac'] == {'metar': 'M'} and o['phases'] == [{'title': 'A'}]


@needs_node
def test_merge_deep_never_descends_into_an_inherited_key():
    src = merge_deep_source() + r"""
    const nativeCall = Object.prototype.hasOwnProperty.call, nativeToString = ({}).toString;
    const defaults = { meta: { title: 'd' }, sitac: { metar: '' } };
    const a = mergeDeep(JSON.parse(JSON.stringify(defaults)), JSON.parse('{"hasOwnProperty":{"call":1},"meta":{"title":"T"}}'));
    const b = mergeDeep(JSON.parse(JSON.stringify(defaults)), JSON.parse('{"toString":{"x":1},"sitac":{"metar":"M"}}'));
    const c = mergeDeep({ list: [1], meta: { title: 'd' } }, JSON.parse('{"list":{"a":1},"meta":{"title":"U","sub":{"k":2}}}'));
    console.log(JSON.stringify({ call: Object.prototype.hasOwnProperty.call === nativeCall, ts: ({}).toString === nativeToString, tsType: typeof ({}).toString, hasCall: typeof Object.prototype.hasOwnProperty.call,
      a: a, b: b, c: c, own: [Object.prototype.hasOwnProperty.call(a, 'hasOwnProperty'), Object.prototype.hasOwnProperty.call(b, 'toString')] }));
    """
    r = subprocess.run([NODE, '-e', src], capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr
    o = json.loads(r.stdout)
    assert o['call'] and o['ts'] and o['tsType'] == 'function' and o['hasCall'] == 'function'
    assert o['a'] == {'meta': {'title': 'T'}, 'sitac': {'metar': ''}, 'hasOwnProperty': {'call': 1}} and o['own'] == [True, True]
    assert o['b'] == {'meta': {'title': 'd'}, 'sitac': {'metar': 'M'}, 'toString': {'x': 1}}
    assert o['c'] == {'list': {'a': 1}, 'meta': {'title': 'U', 'sub': {'k': 2}}}


# ---------- le banc du navigateur ----------
SEED = "(() => { try { if (!sessionStorage.getItem('seeded')) { sessionStorage.setItem('seeded', '1'); localStorage.clear(); localStorage.setItem('lang_v1', '@@LANG@@'); } } catch (e) {} })();"


@pytest.fixture(scope='module')
def browser():
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        br = p.chromium.launch(executable_path=str(CHROMIUM), args=['--no-sandbox'])
        yield br
        br.close()


def route(r):
    if r.request.url.startswith(('file:', 'data:', 'blob:')):
        r.continue_()
    else:
        r.abort()


def shell(browser, lang='fr', w=1280, h=800, touch=False):
    kw = dict(has_touch=True, is_mobile=True) if touch else {}
    ctx = browser.new_context(viewport={'width': w, 'height': h}, locale=lang + '-' + lang.upper(), **kw)
    ctx.add_init_script(SEED.replace('@@LANG@@', lang))
    ctx.route('**/*', route)
    pg = ctx.new_page()
    errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)[:200]))
    pg.goto(SHELL, wait_until='commit')
    pg.wait_for_function("() => typeof window.MP_WORK_EXAMPLE === 'function' && !!document.getElementById('card-hq')", timeout=60000)
    pg.wait_for_timeout(1300)
    return ctx, pg, errs


def examples(pg):
    for g in ('mc', 'fl'):
        pg.evaluate("(g) => window.MP_WORK_EXAMPLE(g)", g)
        pg.wait_for_timeout(900)


def open_tool(pg, mod):
    card = pg.locator('#card-' + mod)
    card.scroll_into_view_if_needed()
    try:
        card.tap(timeout=5000)
    except Exception:
        card.click()
    pg.wait_for_selector('#iframe-' + mod, state='attached')
    pg.wait_for_timeout(2600)
    return pg.query_selector('#iframe-' + mod).content_frame()


def back_to_wall(pg):
    pg.evaluate("() => { const f = document.querySelector('iframe:not([style*=\"display: none\"])'); const b = f && f.contentDocument.querySelector('.mp-back-injected'); if (b) b.click(); }")
    pg.wait_for_timeout(500)


TOAST = """() => { const t = document.getElementById('toast'); if (!t) return null; const b = t.querySelector('.toast-action');
  return { text: (t.querySelector('span') || {}).textContent || '', action: b ? b.textContent : null, show: t.classList.contains('show') }; }"""
STO = "() => localStorage.getItem('briefing_state_v2')"
BRIEF = {'meta': {'title': 'Sonde', 'operation': 'OpSonde', 'classification': 'unclass'}, 'phases': [{'title': 'P1'}]}


def load_bg(fr, obj, wait=1300):
    fr.evaluate("""([txt, name]) => loadJsonFile(new File([txt], name, { type: 'application/json' }))""", [obj if isinstance(obj, str) else json.dumps(obj), 'x.json'])
    fr.wait_for_timeout(wait)


# ---------- BG : Ouvrir un briefing… se restaure ----------
@needs_pw
@pytest.mark.parametrize('lang,loaded,label,refused', [
    ('fr', 'Briefing chargé ✓ · ', 'Restaurer', 'Restauration impossible : les données ont changé depuis.'),
    ('en', 'Briefing loaded ✓ · ', 'Restore', 'Cannot restore: the data has changed since.')])
def test_bg_open_a_briefing_offers_restore(browser, lang, loaded, label, refused):
    ctx, pg, errs = shell(browser, lang)
    try:
        examples(pg)
        bg = open_tool(pg, 'bg')
        before = bg.evaluate(STO)
        state_before = bg.evaluate("() => JSON.stringify(state)")
        load_bg(bg, BRIEF)
        t = bg.evaluate(TOAST)
        assert t['text'] == loaded and t['action'] == label and t['show']
        assert bg.evaluate("() => state.meta.operation") == 'OpSonde'
        bg.wait_for_timeout(8700)
        t = bg.evaluate(TOAST)
        assert t['action'] == label and t['show']                           # encore là à 10 s
        bg.evaluate("() => document.querySelector('#toast .toast-action').click()")
        bg.wait_for_timeout(1500)
        assert bg.evaluate("() => JSON.stringify(state)") == state_before
        assert bg.evaluate(STO) == before                                   # à l'octet
        # ouvrir, modifier, restaurer : refus, rien ne change
        load_bg(bg, BRIEF, 800)
        bg.evaluate("() => { const e = document.querySelector('[data-bind=\"meta.operation\"]'); e.value = 'Modifie'; e.dispatchEvent(new Event('input', { bubbles: true })); }")
        bg.wait_for_timeout(600)
        mid = bg.evaluate(STO)
        bg.evaluate("() => { const b = document.querySelector('#toast .toast-action'); if (b) b.click(); }")
        bg.wait_for_timeout(800)
        t = bg.evaluate(TOAST)
        assert t['text'] == bg.evaluate("() => uiT('ui.restore.refused')") and t['text'].replace(NB, ' ') == refused and t['action'] is None
        assert bg.evaluate("() => state.meta.operation") == 'Modifie' and bg.evaluate(STO) == mid
        # un escadron absent du wing : son texte suit, dans le même toast
        b2 = copy.deepcopy(BRIEF)
        b2['phases'][0]['squadron'] = 'zzz_absent'
        load_bg(bg, b2, 1000)
        t = bg.evaluate(TOAST)
        assert t['text'].startswith(loaded) and 'zzz_absent' in t['text'] and t['text'].endswith(' · ') and t['action'] == label
        # des images recompressées : le texte suit aussi
        bg.evaluate("() => { window.__r = recompressOversizedImagesInState; recompressOversizedImagesInState = async () => 2; }")
        load_bg(bg, BRIEF, 1000)
        t = bg.evaluate(TOAST)
        assert t['text'].startswith(loaded) and '2' in t['text'] and t['text'].endswith(' · ') and t['action'] == label
        bg.evaluate("() => { recompressOversizedImagesInState = window.__r; }")
        # les refus ne changent pas : toast d'erreur sans action, briefing et stockage inchangés
        s, js = bg.evaluate(STO), bg.evaluate("() => JSON.stringify(state)")
        for bad in ('{pas du json', '{"foo": 1}'):
            load_bg(bg, bad, 800)
            t = bg.evaluate(TOAST)
            assert t['action'] is None and t['text'].startswith('⚠')
            assert bg.evaluate(STO) == s and bg.evaluate("() => JSON.stringify(state)") == js
        assert errs == []
    finally:
        ctx.close()


@needs_pw
def test_bg_proto_key_in_a_file_or_in_storage_pollutes_nothing(browser):
    ctx, pg, errs = shell(browser, 'fr')
    try:
        bg = open_tool(pg, 'bg')
        load_bg(bg, '{"meta":{"title":"P","operation":"OpP"},"phases":[{"title":"Q"}],"__proto__":{"pollue":1},"sitac":{"__proto__":{"pollue2":1},"metar":"M"}}', 1000)
        assert bg.evaluate("() => [({}).pollue, ({}).pollue2, state.meta.operation, state.phases[0].title, state.sitac.metar]") == [None, None, 'OpP', 'Q', 'M']
        bg.evaluate("""() => localStorage.setItem('briefing_state_v2', '{"meta":{"title":"S","operation":"OpS"},"phases":[{"title":"Z"}],"__proto__":{"polluS":1},"constructor":{"prototype":{"polluC":1}}}')""")
        bg.evaluate("() => loadState()")
        assert bg.evaluate("() => [({}).polluS, ({}).polluC, state.meta.operation, state.phases[0].title]") == [None, None, 'OpS', 'Z']
        assert errs == []
    finally:
        ctx.close()


@needs_pw
def test_bg_inherited_keys_in_a_file_leave_the_native_functions_alone(browser):
    ctx, pg, errs = shell(browser, 'fr')
    try:
        bg = open_tool(pg, 'bg')
        check = "() => [Object.prototype.hasOwnProperty.call === window.__call, ({}).toString === window.__ts, typeof ({}).toString]"
        bg.evaluate("() => { window.__call = Object.prototype.hasOwnProperty.call; window.__ts = ({}).toString; }")
        load_bg(bg, '{"meta":{"title":"H1","operation":"OpH1"},"phases":[{"title":"Q"}],"hasOwnProperty":{"call":1}}', 1000)
        assert bg.evaluate("() => state.meta.operation") == 'OpH1' and bg.evaluate(check) == [True, True, 'function']
        load_bg(bg, '{"meta":{"title":"H2","operation":"OpH2"},"phases":[{"title":"Q"}],"toString":{"x":1}}', 1000)
        assert bg.evaluate("() => state.meta.operation") == 'OpH2' and bg.evaluate(check) == [True, True, 'function']
        load_bg(bg, BRIEF, 1000)                                            # un briefing normal s'ouvre encore
        assert bg.evaluate("() => [state.meta.operation, state.phases[0].title]") == ['OpSonde', 'P1']
        assert errs == []
    finally:
        ctx.close()


@needs_pw
def test_bg_an_error_in_the_middle_brings_back_the_briefing_and_its_toast_comes_last(browser):
    ctx, pg, errs = shell(browser, 'fr')
    try:
        examples(pg)
        bg = open_tool(pg, 'bg')
        load_bg(bg, BRIEF, 1200)                                            # un briefing A ouvert : « Briefing chargé ✓ · Restaurer »
        assert bg.evaluate(TOAST)['action'] == 'Restaurer'
        bg.wait_for_timeout(500)
        before, js = bg.evaluate(STO), bg.evaluate("() => JSON.stringify(state)")
        op = bg.evaluate("() => document.querySelector('[data-bind=\"meta.operation\"]').value")
        load_bg(bg, '{"meta":{},"phases":[null]}', 1500)
        t = bg.evaluate(TOAST)
        assert t['show'] and t['action'] is None and t['text'].startswith('⚠') and t['text'] == bg.evaluate("() => t('msg.failed')")   # l'erreur, pas « Restaurer »
        assert bg.evaluate("() => JSON.stringify(state)") == js and bg.evaluate(STO) == before
        assert bg.evaluate("() => document.querySelector('[data-bind=\"meta.operation\"]').value") == op == 'OpSonde'      # l'éditeur montre le briefing d'avant
        assert errs == []
    finally:
        ctx.close()


# ---------- HQ : la barre ----------
BAR = """() => Array.from(document.querySelector('header.toolbar').children).filter(e => e.tagName === 'BUTTON' && getComputedStyle(e).display !== 'none' && !e.hidden).map(e => e.id || e.className)"""


@needs_pw
@pytest.mark.parametrize('lang', ['fr', 'en'])
def test_hq_wing_button_keeps_its_place(browser, lang):
    ctx, pg, errs = shell(browser, lang)
    try:
        hq = open_tool(pg, 'hq')
        want = ['mp-back-injected', 'btn-open', 'btn-save', 'btn-packages', 'btn-wing', 'btn-example', 'btn-clear', 'btn-lang']
        assert hq.evaluate(BAR) == want
        assert hq.evaluate("() => document.getElementById('btn-wing').classList.contains('primary')") is True
        assert hq.evaluate("() => document.querySelectorAll('.tb-lead').length") == 0
        hq.evaluate("() => document.getElementById('btn-example').click()")           # la configuration d'exemple d'HQ : le wing est configuré
        hq.wait_for_timeout(1500)
        assert hq.evaluate(BAR) == want
        assert hq.evaluate("() => document.getElementById('btn-wing').classList.contains('primary')") is False
        assert hq.evaluate("() => document.querySelectorAll('.tb-lead').length") == 0
        assert errs == []
    finally:
        ctx.close()


@needs_pw
@pytest.mark.parametrize('w,h', [(345, 590), (412, 915)])
def test_hq_toolbar_on_a_phone_nothing_off_screen(browser, w, h):
    ctx, pg, errs = shell(browser, 'fr', w, h, True)
    try:
        hq = open_tool(pg, 'hq')
        info = hq.evaluate("""() => { const W = innerWidth; const vis = Array.from(document.querySelector('header.toolbar').children).filter(e => e.tagName === 'BUTTON' && getComputedStyle(e).display !== 'none' && !e.hidden);
          return vis.filter(e => { const r = e.getBoundingClientRect(); return r.right > W + 0.5 || r.left < -0.5; }).map(e => e.id || e.className); }""")
        assert info == []
        bar = hq.evaluate(BAR)
        assert bar[:4] == ['mp-back-injected', 'btn-open', 'btn-save', 'btn-packages'] and bar[-1] == 'tb-more-btn'
        assert errs == []
    finally:
        ctx.close()


# ---------- DG : une carte libre qui perd ses types ----------
SNAP = """() => { const c = doc.cards[curIdx]; const g = p => { const e = document.querySelector('#editor [data-path="' + p + '"]'); return e ? { v: e.value, ro: e.readOnly } : null; };
  return { aircraft: g('flight.aircraft'), count: g('flight.count'), fa: c.flight.aircraft, fc: c.flight.count }; }"""


def set_type(dg, i, v):
    dg.evaluate("""([i, v]) => { const el = document.querySelector('#editor [data-dg-type="' + i + '"]'); el.value = v; el.dispatchEvent(new Event('change', { bubbles: true })); }""", [i, v])
    dg.wait_for_timeout(300)


@needs_pw
def test_dg_free_card_that_loses_its_types_empties_aircraft_and_count(browser):
    ctx, pg, errs = shell(browser, 'fr')
    try:
        dg = open_tool(pg, 'dg')
        for _ in range(2):
            dg.evaluate("() => document.querySelector('#editor [data-act=\"add\"][data-list=\"crew\"]').click()")
            dg.wait_for_timeout(300)
        set_type(dg, 0, 'F-14B')
        set_type(dg, 1, 'FA-18C_hornet')
        s = dg.evaluate(SNAP)
        assert s['fa'] == 'F-14B + FA-18C_hornet' and s['fc'] == 2 and s['aircraft']['ro'] is True
        set_type(dg, 0, '')
        s = dg.evaluate(SNAP)
        assert s['fa'] == 'FA-18C_hornet' and s['fc'] == 1                  # un type reste : le groupe se déduit encore
        set_type(dg, 1, '')
        s = dg.evaluate(SNAP)
        assert s['fa'] == '' and s['fc'] is None
        assert s['aircraft'] == {'v': '', 'ro': False} and s['count'] == {'v': '', 'ro': False}      # vides et saisissables
        # les lignes vidées
        set_type(dg, 0, 'F-14B')
        assert dg.evaluate(SNAP)['fa'] == 'F-14B'
        dg.evaluate("() => document.querySelector('#editor [data-act=\"remove\"][data-list=\"crew\"][data-i=\"1\"]').click()")
        dg.wait_for_timeout(300)
        dg.evaluate("() => document.querySelector('#editor [data-act=\"remove\"][data-list=\"crew\"][data-i=\"0\"]').click()")
        dg.wait_for_timeout(300)
        s = dg.evaluate(SNAP)
        assert s['fa'] == '' and s['fc'] is None and s['aircraft']['ro'] is False
        assert errs == []
    finally:
        ctx.close()


@needs_pw
def test_dg_free_card_never_deduced_keeps_a_typed_aircraft(browser):
    ctx, pg, errs = shell(browser, 'fr')
    try:
        dg = open_tool(pg, 'dg')
        dg.evaluate("() => { const e = document.querySelector('#editor [data-path=\"flight.aircraft\"]'); e.value = 'Mi-24P custom'; e.dispatchEvent(new Event('input', { bubbles: true })); }")
        dg.wait_for_timeout(300)
        dg.evaluate("() => document.querySelector('#editor [data-act=\"add\"][data-list=\"crew\"]').click()")
        dg.wait_for_timeout(300)
        assert dg.evaluate(SNAP)['fa'] == 'Mi-24P custom'
        dg.evaluate("() => document.querySelector('#editor [data-act=\"remove\"][data-list=\"crew\"][data-i=\"0\"]').click()")
        dg.wait_for_timeout(300)
        s = dg.evaluate(SNAP)
        assert s['fa'] == 'Mi-24P custom' and s['aircraft']['v'] == 'Mi-24P custom' and s['aircraft']['ro'] is False
        assert errs == []
    finally:
        ctx.close()


# ---------- FC : le repli d'un groupe se garde ----------
OPEN = "() => S.flights.map((f, i) => flightOpen(f, i))"


def work_text(pg):
    return re.sub(r'"createdAt": "[^"]*"', '"createdAt": ""', pg.evaluate("() => suiteWorkText()"))


LS_DUMP = "() => JSON.stringify(Object.keys(localStorage).map(k => [k, localStorage.getItem(k)]))"
LS_PUT = "(d) => { JSON.parse(d).forEach(kv => localStorage.setItem(kv[0], kv[1])); }"


def reopen_fc(pg):
    """Recharge la page ; le shell rouvre l'outil par l'adresse. Le contexte du banc est en mémoire : de temps en temps Chromium y perd tout localStorage à un rechargement
    (aucun clear() de l'application) ; un vrai navigateur le garde : on remet le stockage comme il était et on recharge, au plus trois fois."""
    snap = pg.evaluate(LS_DUMP)
    fr = None
    for _ in range(3):
        pg.reload(wait_until='commit')
        pg.wait_for_function("() => typeof window.MP_WORK_EXAMPLE === 'function' && !!document.getElementById('card-hq')", timeout=60000)
        pg.wait_for_timeout(1300)
        if pg.evaluate("() => localStorage.getItem('fc_state_v1') === null") and '"fc_state_v1"' in snap:
            pg.evaluate(LS_PUT, snap)
            continue
        pg.wait_for_selector('#iframe-fc', state='attached', timeout=30000)
        pg.wait_for_timeout(2600)
        fr = pg.query_selector('#iframe-fc').content_frame()
        break
    assert fr is not None, 'localStorage lost three reloads in a row'
    fr.wait_for_function("() => typeof S !== 'undefined' && S.flights && S.flights.length > 0", timeout=30000)
    return fr


@needs_pw
def test_fc_folded_group_stays_folded_after_a_reload(browser):
    ctx, pg, errs = shell(browser, 'fr')
    try:
        examples(pg)
        fc = open_tool(pg, 'fc')
        fcid = fc.evaluate("() => S.flights[0].fcId")
        assert fc.evaluate(OPEN) == [True] and fc.evaluate("() => localStorage.getItem('fc_folds_v1')") is None
        w0 = work_text(pg)
        fc.evaluate("() => document.querySelector('.fc-flight[data-f=\"0\"] .fc-fold').click()")
        fc.wait_for_timeout(400)
        assert json.loads(fc.evaluate("() => localStorage.getItem('fc_folds_v1')")) == {'g:' + fcid: False}
        assert work_text(pg) == w0                                          # le fichier de travail n'en porte rien
        fc = reopen_fc(pg)
        assert fc.evaluate(OPEN) == [False]
        fc.evaluate("() => document.querySelector('.fc-flight[data-f=\"0\"] .fc-fold').click()")
        fc.wait_for_timeout(400)
        assert json.loads(fc.evaluate("() => localStorage.getItem('fc_folds_v1')")) == {'g:' + fcid: True}
        fc = reopen_fc(pg)
        assert fc.evaluate(OPEN) == [True]
        fc.evaluate("() => document.querySelector('#col-flights .fc-fhead .ui-foldic').click()")        # « Tout replier »
        fc.wait_for_timeout(400)
        assert work_text(pg) == w0
        fc = reopen_fc(pg)
        assert fc.evaluate(OPEN) == [False]
        fc.evaluate("() => document.querySelector('#col-flights .fc-fhead .ui-foldic').click()")        # « Tout déplier »
        fc.wait_for_timeout(400)
        fc = reopen_fc(pg)
        assert fc.evaluate(OPEN) == [True]
        # une clé de groupe disparu s'en va à la prochaine écriture ; les boîtes gardent la leur
        fc.evaluate("() => localStorage.setItem('fc_folds_v1', JSON.stringify(Object.assign(JSON.parse(localStorage.getItem('fc_folds_v1')), { 'g:disparu': false, route: false })))")
        fc.evaluate("() => document.querySelector('.fc-flight[data-f=\"0\"] .fc-fold').click()")
        fc.wait_for_timeout(400)
        assert json.loads(fc.evaluate("() => localStorage.getItem('fc_folds_v1')")) == {'g:' + fcid: False, 'route': False}
        assert errs == []
    finally:
        ctx.close()


@needs_pw
def test_fc_restore_after_opening_a_configuration_brings_back_the_fold(browser):
    ctx, pg, errs = shell(browser, 'fr')
    try:
        examples(pg)
        fc = open_tool(pg, 'fc')
        fc.evaluate("() => document.querySelector('.fc-flight[data-f=\"0\"] .fc-fold').click()")
        fc.wait_for_timeout(400)
        assert fc.evaluate(OPEN) == [False]
        cfg = fc.evaluate("""() => { const f = JSON.parse(JSON.stringify(S.flights[0])); f.fcId = 'autre-groupe-1'; f.name = 'AUTRE';
          return JSON.stringify({ fc: { state: { theatre: S.theatre, flights: [f], sel: { f: 0, u: 0 } } } }); }""")
        fc.evaluate("([txt]) => openFile(new File([txt], 'config.json', { type: 'application/json' }))", [cfg])
        fc.wait_for_timeout(2500)
        assert fc.evaluate("() => S.flights.map(f => f.name)") == ['AUTRE']
        assert fc.evaluate(OPEN) == [True]                                  # le groupe du fichier suit la règle (un seul groupe : ouvert)
        t = fc.evaluate(TOAST)
        assert t['action'] == 'Restaurer'
        fc.evaluate("() => document.querySelector('#toast .toast-action').click()")
        fc.wait_for_timeout(1500)
        assert fc.evaluate("() => S.flights.length") == 1 and fc.evaluate("() => S.flights[0].name") != 'AUTRE'
        assert fc.evaluate(OPEN) == [False]                                 # comme après un rechargement : replié
        assert errs == []
    finally:
        ctx.close()


# ---------- HQ : l'avertissement d'un vol créé et celui d'un vol trouvé ----------
@needs_pw
def test_hq_created_flight_reports_a_dropped_point_reference_a_found_one_stays_to_check(browser, tmp_path):
    pk = copy.deepcopy(hqp.PACKAGE)
    for f in pk['flights']:
        f['route'] = {'points': {'1': hqp.ROUTE['points']['1'], '2': {'type': 'Turning Point', 'action': 'Turning Point', 'x': 300, 'y': 400, 'alt': 500,
                                                                       'alt_type': 'BARO', 'speed': 50, 'linkUnit': 7, 'task': {'id': 'ComboTask', 'params': {'tasks': {}}}}}}
    miz, pkg = tmp_path / 'essai.miz', tmp_path / 'paquet.json'
    hqp.miz_fixture.make(str(miz), False)
    pkg.write_text(json.dumps(pk), encoding='utf-8')
    ctx, pg, errs = shell(browser, 'en')
    try:
        hq = open_tool(pg, 'hq')
        hq.set_input_files('#miz-file-input', str(miz))
        pg.wait_for_timeout(2500)
        hq.set_input_files('#pk-file-input', str(pkg))
        pg.wait_for_timeout(1500)
        hq.evaluate("document.querySelector('[data-pkc=create]').click()")
        pg.wait_for_timeout(400)
        hq.evaluate("document.getElementById('pk-apply-btn').click()")
        pg.wait_for_timeout(3000)
        lines = hq.evaluate("() => Array.from(document.querySelectorAll('#pk-report .pk-rep > .w')).map(e => e.innerText)")
    finally:
        ctx.close()
    assert '⚠ NEWBIRD: point 2: refers to a unit of the package’s mission (linkUnit = 7) — removed' in lines
    assert '⚠ HIND: point 2: refers to a unit of the package’s mission (linkUnit = 7) — check it' in lines
    assert not any(l.startswith('⚠ NEWBIRD') and 'check it' in l for l in lines)
    assert not any(l.startswith('⚠ HIND') and 'removed' in l for l in lines)
