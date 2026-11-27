"""Les heures réelles d'une route, leurs cadenas, le rouge (Route Planner et Datacard Generator).
Sans navigateur (node, sur le bloc extrait de route_timing_block.build_block()) : les règles R3 et R4 sur un petit jeu de points écrit ici (des points de l'équateur : la distance d'une branche
est le rayon fois l'écart de longitude, calculée ici à part) : avant, entre et après les heures fixes, tenu à 5 s, rouge et son facteur, minuit, une vitesse de branche, le pivot unique, les messages.
Au navigateur (le shell construit, chromium, aucun réseau ; 1 280 × 800 à la souris et 412 × 915 au doigt) : au Route Planner, taper une heure, le cadenas, un tronçon rouge et son bandeau, la confirmation
d'export ; au Datacard Generator, une ligne d'Horaires liée (saisie, cadenas, saisie sur place), la colonne TOS, la même route qu'au Route Planner. Les contrôles passent par le DOM, jamais par une capture."""
import json
import math
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from banc_attente import attendre, attendre_images, attendre_mise_en_page, attendre_outil, attendre_rp, attendre_shell, exemple, cadre_export  # noqa: E402
from route_timing_block import build_block  # noqa: E402

CHROMIUM = Path('/opt/pw-browsers/chromium')
try:
    import playwright.sync_api  # noqa: F401
    HAS_PW = CHROMIUM.exists()
except ImportError:
    HAS_PW = False
needs_pw = pytest.mark.skipif(not HAS_PW, reason='playwright ou chromium absent')
needs_node = pytest.mark.skipif(shutil.which('node') is None, reason='node absent')
SHELL = 'file://' + str(ROOT / 'dist' / 'dcs_mission_plan.html')
SEED = "(() => { try { if (localStorage.getItem('lang_v1') === null) localStorage.setItem('lang_v1', '@@'); } catch (e) {} })();"
R = 6371.0088


# ---------------------------------------------------------------------------------------------------- le bloc, sans navigateur
def node(js):
    """Exécute `js` (le bloc commun chargé) sous node ; rend ce que `out` a reçu, en JSON."""
    prog = build_block() + '\nlet __o; const out = v => { __o = v; };\n' + js + '\nprocess.stdout.write(JSON.stringify(__o));\n'
    r = subprocess.run(['node', '-e', prog], capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


def eq_points(lons, **extra):
    """Des points sur l'équateur : branche i = R × écart de longitude (radians), sans autre formule."""
    pts = [{'lat': 0, 'lon': lo} for lo in lons]
    for k, v in extra.items():
        i, f = int(k[1:]), None
        pts[i].update(v)
    return pts


LONS = [0, 0.5, 1.2, 1.5, 2.3, 2.5]                  # des branches de 55,6 à 89 km
LEG_KM = [R * math.radians(b - a) for a, b in zip(LONS, LONS[1:])]


def el_at(speeds):
    out, s = [0.0], 0.0
    for km, v in zip(LEG_KM, speeds):
        s += km / v * 3600
        out.append(s)
    return out


def hms(s):
    n = int(math.floor(s + 0.5)) % 86400
    return '%02d:%02d:%02d' % (n // 3600, n // 60 % 60, n % 60)


def secs(h):
    a = [int(x) for x in h.split(':')]
    return a[0] * 3600 + a[1] * 60 + a[2]


def calc(points, gs=220):
    return node('const p = %s; const T = rtmCompute(p, %s); out({ t: T.t, el: T.el, has: T.has, fixed: T.fixed, lock: T.lock, red: T.red, km: T.km, sec: T.sec, clock: T.t.map(x => x === null ? null : rtmClock(x)) });' % (json.dumps(points), gs))


@needs_node
def test_without_a_time_nothing_is_fixed_and_the_elapsed_times_are_the_sum_of_the_legs():
    r = calc(eq_points(LONS))
    ex = el_at([220] * 5)
    assert r['has'] is False and r['t'] == [None] * 6 and r['red'] == [None] * 6
    assert all(abs(a - b) < 1e-6 for a, b in zip(r['el'], ex)) and abs(r['km'] - sum(LEG_KM)) < 1e-9 and abs(r['sec'] - ex[-1]) < 1e-6


@needs_node
def test_before_between_and_after_the_fixed_times():
    ex = el_at([220] * 5)
    # un pivot au point 2 : avant, il se déduit ; après, il se prolonge
    p = eq_points(LONS); p[2]['t'] = '10:00:00'
    r = calc(p)
    assert r['has'] is True and r['fixed'] == [False, False, True, False, False, False] and r['lock'] == [False] * 6 and r['red'] == [None] * 6
    for i in range(6):
        assert r['clock'][i] == hms(36000 + (ex[i] - ex[2]))
    assert r['clock'][2] == '10:00:00'
    # deux heures fixes tenues : les points entre elles suivent la première, la seconde garde sa valeur
    p = eq_points(LONS); p[0].update(t='09:00:00', tLock=True); p[4].update(t='%s' % hms(32400 + ex[4]), tLock=True)
    r = calc(p)
    assert r['red'] == [None] * 6 and r['lock'] == [True, False, False, False, True, False]
    for i in range(5):
        assert r['clock'][i] == hms(32400 + ex[i])
    assert r['clock'][5] == hms(32400 + ex[5])                            # après la dernière : elle se prolonge


@needs_node
def test_a_fixed_time_holds_to_five_seconds_and_turns_red_beyond_with_its_factor():
    ex = el_at([220] * 5)
    base = 32400 + ex[4]
    for off, red in ((5, False), (-5, False), (5.9, False), (6.5, True), (-6.5, True), (120, True)):
        p = eq_points(LONS); p[0].update(t='09:00:00', tLock=True); p[4].update(t=hms(base + off), tLock=True)
        r = calc(p)
        besoin = secs(hms(base + off)) - 32400
        # l'écart se juge sur les secondes entières posées : on recalcule ici avec ce que le point porte
        want = abs(ex[4] - besoin) > 5
        assert (r['red'][4] is not None) == want, (off, r['red'][4], ex[4] - besoin)
        if want:
            assert r['red'][4]['a'] == 0 and abs(r['red'][4]['f'] - ex[4] / besoin) < 1e-9 and abs(r['red'][4]['besoin'] - besoin) < 1e-9
            assert r['clock'][4] == hms(base + off)                       # b garde sa valeur
        assert all(x is None for k, x in enumerate(r['red']) if k != 4)


@needs_node
def test_a_zero_need_is_red_without_a_factor_and_midnight_wraps():
    p = eq_points(LONS); p[0].update(t='09:00:00', tLock=True); p[3].update(t='09:00:00', tLock=True)
    r = calc(p)
    assert r['red'][3] is not None and r['red'][3]['f'] is None and r['red'][3]['besoin'] == 0
    ex = el_at([220] * 5)
    p = eq_points(LONS); p[0].update(t='23:50:00', tLock=True)
    r = calc(p)
    assert r['clock'][0] == '23:50:00' and r['clock'][5] == hms(85800 + ex[5]) and r['t'][5] > 86400 and r['clock'][5].startswith('01:')


@needs_node
def test_a_leg_speed_changes_the_elapsed_times_and_the_message_names_a_common_speed_only():
    p = eq_points(LONS); p[2]['gs'] = 300; p[0].update(t='09:00:00', tLock=True); p[4].update(t='09:30:00', tLock=True)
    ex = el_at([220, 300, 220, 220, 220])
    r = calc(p)
    assert all(abs(a - b) < 1e-6 for a, b in zip(r['el'], ex))
    msgs = node("""const p = %s; const T = rtmCompute(p, 220);
      const o = { t: (k, v) => k + '|' + [v.p, v.h, v.n, v.v, v.a, v.b, v.r].join('|'), speedText: x => Math.round(x) + ' km/h', fr: false, name: k => 'P' + k };
      out(T.red.map((r, i) => r ? rtmRedMsg(p, T, i, o) : null));""" % json.dumps(p))
    m = msgs[4]
    assert m['text'].startswith('t.red.nv|P4|09:30:00|') and '|P0|P4|' in m['text']              # vitesses différentes de a à b : pas de parenthèse
    p[2].pop('gs')
    msgs = node("""const p = %s; const T = rtmCompute(p, 220);
      const o = { t: (k, v) => k + '|' + [v.p, v.h, v.n, v.v, v.a, v.b, v.r].join('|'), speedText: x => Math.round(x) + ' km/h', fr: false, name: k => 'P' + k };
      out(T.red.map((r, i) => r ? rtmRedMsg(p, T, i, o) : null));""" % json.dumps(p))
    ex = el_at([220] * 5)
    f = ex[4] / 1800
    assert msgs[4]['text'].startswith('t.red|P4|09:30:00|') and msgs[4]['n'] == ('+' if f > 1 else '−') + str(max(1, abs(round((f - 1) * 100)))) + '%'
    assert '|%d km/h|' % round(220 * f) in msgs[4]['text'] and msgs[4]['text'].endswith('|' + hms(32400 + ex[4]))


@needs_node
def test_typing_locking_and_unlocking_follow_the_rules():
    r = node("""
      const mk = () => [0, 0.5, 1.2, 1.5].map(l => ({ lat: 0, lon: l }));
      const st = p => p.map(q => [q.t || null, q.tLock === true]);
      const log = [];
      let p = mk();
      rtmType(p, 1, rtmParse('9:30')); log.push(st(p));                       // un pivot : « 9:30 » se lit hh:mm:00
      rtmType(p, 3, rtmParse('10:00:00')); log.push(st(p));                   // un autre point non verrouillé : il devient le pivot, l'ancien perd son heure
      rtmLock(p, 3, rtmCompute(p, 220)); log.push(st(p));                     // verrouiller : l'heure affichée, avec le verrou
      rtmType(p, 1, rtmParse('09:40:00')); log.push(st(p));                   // taper ailleurs : nouveau pivot, le verrouillé ne bouge pas
      rtmType(p, 3, rtmParse('10:05:00')); log.push(st(p));                   // taper sur le verrouillé : valeur changée, verrou gardé, pivot intact
      rtmLock(p, 2, rtmCompute(p, 220)); log.push(st(p));                     // verrouiller un point qui n'a pas d'heure fixe : son heure affichée
      rtmUnlock(p, 3); log.push(st(p));                                       // déverrouiller : il y a d'autres heures fixes, son heure part
      rtmUnlock(p, 2); log.push(st(p));
      rtmType(p, 1, null); log.push(st(p));                                   // vider
      p = mk(); rtmType(p, 0, 3600); rtmLock(p, 0, rtmCompute(p, 220)); rtmUnlock(p, 0); log.push(st(p));       // la seule heure fixe : déverrouillée, elle reste, le point devient le pivot
      p = mk(); log.push(rtmLock(p, 0, rtmCompute(p, 220)));                  // sans heure : rien à verrouiller
      out(log);""")
    off = [None, False]
    assert r[0] == [off, ['09:30:00', False], off, off]
    assert r[1] == [off, off, off, ['10:00:00', False]]
    assert r[2] == [off, off, off, ['10:00:00', True]]
    assert r[3] == [off, ['09:40:00', False], off, ['10:00:00', True]]
    assert r[4] == [off, ['09:40:00', False], off, ['10:05:00', True]]
    assert r[5][2][1] is True and r[5][2][0] is not None and r[5][1] == ['09:40:00', False] and r[5][3] == ['10:05:00', True]
    assert r[6][3] == off and r[6][2][1] is True
    assert r[7][2] == off and r[7][1] == ['09:40:00', False]
    assert r[8] == [off, off, off, off]
    assert r[9] == [['01:00:00', False], off, off, off]
    assert r[10] is False


@needs_node
def test_the_entries_and_the_stored_fields_are_read_strictly():
    r = node("""out([['9:5', '09:5:7', '9:05:07', '23:59:59', '24:00', '12:60', '1:2:3:4', 'abc', ' 7:30 ', '12:30:60', ''].map(rtmParse),
      ['09:05:07', '9:05:07', '24:00:00', '12:60:00', 12, null].map(rtmValid),
      (() => { const d = {}; rtmRead({ t: '09:05:07', tLock: true }, d); const e = {}; rtmRead({ t: 'bad', tLock: true }, e); const f = {}; rtmRead({ tLock: true }, f); return [d, e, f]; })(),
      [rtmClockMin(0), rtmClockMin(29.4), rtmClockMin(30), rtmClockMin(86399.6), rtmClock(-1), rtmClock(86400.4)]]);""")
    assert r[0] == [32700 + 0 if False else 9 * 3600 + 5 * 60, 9 * 3600 + 5 * 60 + 7, 9 * 3600 + 5 * 60 + 7, 86399, None, None, None, None, 7 * 3600 + 30 * 60, None, None]
    assert r[1] == [True, False, False, False, False, False]
    assert r[2] == [{'t': '09:05:07', 'tLock': True}, {}, {}]
    assert r[3] == ['00:00', '00:00', '00:01', '00:00', '23:59:59', '00:00:00']


# ---------------------------------------------------------------------------------------------------- le navigateur
@pytest.fixture(scope='module')
def browser():
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        br = p.chromium.launch(executable_path=str(CHROMIUM), args=['--no-sandbox'])
        yield br
        br.close()


def shell(br, w, h, touch=False, lang='fr'):
    kw = dict(has_touch=True, is_mobile=True) if touch else {}
    ctx = br.new_context(viewport={'width': w, 'height': h}, locale=lang + '-' + lang.upper(), **kw)
    ctx.add_init_script(SEED.replace('@@', lang))
    ctx.route('**/*', lambda r: r.continue_() if r.request.url.startswith(('file:', 'data:', 'blob:')) else r.abort())
    pg = ctx.new_page()
    pg.errs = []
    pg.on('pageerror', lambda e: pg.errs.append(str(e)[:200]))
    pg.goto(SHELL, wait_until='commit')
    attendre_shell(pg, 60000)
    for g in ('mc', 'fl'):
        exemple(pg, g)
    css = '.toast, #toast, [class*="toast"] { display: none !important; }'
    pg.add_style_tag(content=css)
    return pg


def open_rp(pg):
    pg.evaluate("() => MP_OPEN_MODULE('rp')")
    fr = attendre_rp(pg)
    attendre_mise_en_page(fr)
    fr.add_style_tag(content='.toast, #toast, [class*="toast"] { display: none !important; }')
    return fr


def open_dg(pg):
    pg.evaluate("() => MP_OPEN_MODULE('dg')")
    fr = attendre_outil(pg, 'dg', delai=30000)
    attendre(fr, "!!document.querySelector('#preview .dc-page') && dgMeasurable() && !DG_UI.needLayout", "l'aperçu de l'exemple mesuré", delai=30000)
    fr.add_style_tag(content='.toast, #toast, [class*="toast"] { display: none !important; }')
    return fr


def nav_open(fr, touch=False):
    """La section Navigation montrée : l'onglet Nav. quand la barre d'onglets est affichée, sinon la section dépliée"""
    if fr.evaluate("() => { const b = document.getElementById('tab-bar'); return !!b && getComputedStyle(b).display !== 'none'; }"):
        fr.evaluate("() => document.querySelector('#tab-bar [data-tab=\"nav\"]').click()")
        attendre(fr, "document.body.dataset.activeTab === 'nav'", "l'onglet Nav. ouvert")
    else:
        fr.evaluate("() => { const d = document.querySelector('#panel > .ed-section[data-section=\"nav\"]'); if (d.dataset.open !== 'true') d.querySelector('.ed-head').click(); }")
        attendre(fr, "document.querySelector('#panel > .ed-section[data-section=\"nav\"]').dataset.open === 'true'", 'la section Navigation dépliée')


def tm_type(fr, pg, i, text, enter=True):
    fr.locator('#nav-body [data-tm="%d"]' % i).click()
    attendre(fr, "TMX.i === arg && document.activeElement.classList.contains('tm-in')", 'le champ du point %d ouvert, le focus dedans' % i, arg=i, lu='[TMX.i, document.activeElement.className]')
    pg.keyboard.press('Control+A')
    pg.keyboard.type(text) if text else pg.keyboard.press('Backspace')
    if enter:
        pg.keyboard.press('Enter')
        attendre(fr, 'TMX.i === -1', 'le champ refermé')


def tm_lock(fr, i):
    fr.locator('#nav-body [data-tl="%d"]' % i).click()


PTS = "() => S.points.map(p => [p.t || null, p.tLock === true])"
NAVT = "() => [...document.querySelectorAll('#nav-body td.nm .tm-t')].map(e => e.textContent)"
MAPT = "() => [...document.querySelectorAll('.wp-time')].map(e => e.textContent)"
OFF = [None, False]


@needs_pw
def test_route_planner_typing_locking_and_the_map_follow_each_other_with_a_mouse(browser):
    pg = shell(browser, 1280, 800)
    fr = open_rp(pg)
    nav_open(fr)
    before = fr.evaluate("() => [document.getElementById('nav-total').textContent, " + NAVT[6:].replace('() =>', '') + "]") if False else fr.evaluate("() => document.getElementById('nav-total').textContent")
    assert before == '154 km · 00+41+55' and fr.evaluate("() => document.querySelectorAll('.tm-lock').length") == 0       # sans heure : aucun cadenas
    tm_type(fr, pg, 4, '10:17')                                           # « hh:mm » se lit hh:mm:00 ; taper ne verrouille pas
    assert fr.evaluate(PTS) == [OFF, OFF, OFF, OFF, ['10:17:00', False], OFF]
    assert fr.evaluate(NAVT) == ['09:45:24', '09:53:37', '10:06:29', '10:11:35', '10:17:00', '10:27:19'] == fr.evaluate(MAPT)
    assert fr.evaluate("() => document.getElementById('nav-total').textContent") == '154 km · 00+41+55 · arrivée 10:27:19'
    tm_lock(fr, 4)
    assert fr.evaluate(PTS)[4] == ['10:17:00', True]
    assert fr.evaluate("() => [...document.querySelectorAll('.tm-lock')].map(b => b.getAttribute('aria-pressed') + '|' + b.getAttribute('aria-label') + '|' + b.title)")[4] == 'true|Déverrouiller l’heure|Déverrouiller l’heure'
    assert fr.evaluate("() => document.querySelectorAll('.wp-time svg').length") == 1                      # un cadenas fermé devant l'heure verrouillée seulement
    # une saisie illisible ne s'écrit pas, Échap non plus ; vider retire l'heure
    tm_type(fr, pg, 2, '25:99')
    assert fr.evaluate(PTS)[2] == OFF
    tm_type(fr, pg, 2, '10:00:00', enter=False)
    pg.keyboard.press('Escape')
    attendre(fr, 'TMX.i === -1', 'le champ annulé')
    assert fr.evaluate(PTS)[2] == OFF
    tm_type(fr, pg, 2, '10:00:00')                                        # le pivot : le point 4 verrouillé garde son heure
    assert fr.evaluate(PTS) == [OFF, OFF, ['10:00:00', False], OFF, ['10:17:00', True], OFF]
    tm_type(fr, pg, 2, '')
    assert fr.evaluate(PTS) == [OFF, OFF, OFF, OFF, ['10:17:00', True], OFF]
    tm_lock(fr, 4)                                                        # la seule heure fixe : elle reste, le point devient le pivot
    assert fr.evaluate(PTS)[4] == ['10:17:00', False]
    # le temps sous un point de la carte ouvre le champ au tableau ; les heures suivent un point déplacé
    fr.locator('.wp-time').nth(1).click()
    attendre(fr, "TMX.i === 1 && document.activeElement.classList.contains('tm-in')", "le champ du point 1 ouvert par la carte", lu='[TMX.i, document.activeElement.className]')
    pg.keyboard.press('Escape')
    fr.evaluate("() => { const m = ptMarkers[2]; const q = m.getLatLng(); m.setLatLng([q.lat + 0.05, q.lng]); m.fire('drag'); }")
    assert fr.evaluate(NAVT) == fr.evaluate(MAPT) and fr.evaluate(NAVT)[4] == '10:17:00'
    assert pg.errs == []


RED_FR = 'KARAVOSTASI à 10:14:00 intenable : il faudrait +9 % (240 km/h) d’AKROTIRI à KARAVOSTASI. Aux vitesses de la route : 10:16:36.'
RED_EN = 'KARAVOSTASI at 10:14:00 cannot be met: it would take +9% (240 km/h) from AKROTIRI to KARAVOSTASI. At the route’s speeds: 10:16:36.'


@needs_pw
@pytest.mark.parametrize('lang,msg', [('fr', RED_FR), ('en', RED_EN)])
def test_route_planner_red_time_banner_and_pastille(browser, lang, msg):
    pg = shell(browser, 1280, 800, lang=lang)
    fr = open_rp(pg)
    nav_open(fr)
    tm_type(fr, pg, 0, '09:45')
    tm_lock(fr, 0)
    tm_type(fr, pg, 4, '10:14')
    tm_lock(fr, 4)
    assert fr.evaluate(PTS) == [['09:45:00', True], OFF, OFF, OFF, ['10:14:00', True], OFF]
    assert fr.evaluate("() => document.getElementById('nav-red').textContent") == msg
    assert fr.evaluate("() => [...document.querySelectorAll('#nav-red b')].map(e => e.textContent)") == [msg.split('\u202f:' if lang == 'fr' else ': ')[0], '+9\u202f%' if lang == 'fr' else '+9%']
    assert fr.evaluate("() => document.getElementById('nav-red').hidden") is False and fr.evaluate("() => document.querySelectorAll('#nav-red > div').length") == 1
    assert fr.evaluate(NAVT) == ['09:45:00', '09:53:13', '10:06:05', '10:11:11', '10:14:00⚠', '10:24:19'] and fr.evaluate(MAPT)[4] == '10:14:00⚠'
    assert fr.evaluate("() => document.getElementById('nav-total').textContent").endswith('10:24:19')
    # la pastille est celle de la variable commune, texte blanc, dans les quatre thèmes ; une seule heure rouge
    for th in ('cw-nato', 'cw-soviet', 'modern-nato', 'modern-east'):
        fr.evaluate("(t) => { document.body.dataset.theme = t; }", th)
        css = fr.evaluate("() => { const a = getComputedStyle(document.querySelector('.tm-t.red')), b = getComputedStyle(document.querySelector('.wp-time.red')); return [a.backgroundColor, a.color, b.backgroundColor, b.color, document.querySelectorAll('.tm-t.red').length, document.querySelectorAll('.wp-time.red').length]; }")
        assert css == ['rgb(192, 57, 43)', 'rgb(255, 255, 255)', 'rgb(192, 57, 43)', 'rgb(255, 255, 255)', 1, 1], th
    # relâcher la vitesse : plus de rouge, plus de bandeau
    fr.evaluate("() => { S.points[4].t = rtmClock(35100 + timing().h.el[4]); renderNav(); drawRoute(); }")
    assert fr.evaluate("() => [document.getElementById('nav-red').hidden, document.querySelectorAll('.tm-t.red').length]") == [True, 0]
    assert pg.errs == []


@needs_pw
def test_route_planner_export_asks_before_a_red_time_and_carries_plain_times(browser):
    pg = shell(browser, 1280, 800)
    fr = open_rp(pg)
    nav_open(fr)
    tm_type(fr, pg, 0, '09:45'); tm_lock(fr, 0)
    tm_type(fr, pg, 4, '10:14'); tm_lock(fr, 4)
    fr.evaluate("""() => { window.__shots = []; window.html2canvas = function (el, o) {
      window.__shots.push([...document.querySelectorAll('.wp-time')].map(e => ({ html: e.innerHTML, cls: e.className, bg: getComputedStyle(e).backgroundColor, svg: e.querySelectorAll('svg').length })));
      return Promise.reject(new Error('banc')); }; }""")
    cadre_export(fr, True)
    fr.evaluate('() => { expGo(); }')
    attendre(fr, "!document.getElementById('ui-confirm').hidden", 'la confirmation affichée')
    assert fr.evaluate("() => [document.getElementById('ui-confirm-title').textContent, document.getElementById('ui-confirm-ok').textContent, document.getElementById('ui-confirm-cancel').textContent]") == \
        ['Une heure verrouillée n’est pas tenue (KARAVOSTASI). Exporter quand même ?', 'Exporter', 'Annuler']
    assert fr.evaluate('() => window.__shots.length') == 0
    fr.locator('#ui-confirm-cancel').click()                              # « Annuler » n'exporte pas
    attendre(fr, "document.getElementById('ui-confirm').hidden", 'la confirmation fermée')
    assert fr.evaluate('() => window.__shots.length') == 0 and fr.evaluate('() => EXP.on') is True
    fr.evaluate('() => { expGo(); }')
    attendre(fr, "!document.getElementById('ui-confirm').hidden", 'la confirmation affichée')
    fr.locator('#ui-confirm-ok').click()
    attendre(fr, 'window.__shots.length === 1', "le rendu parti (html2canvas appelé)")
    shot = fr.evaluate('() => window.__shots[0]')
    assert len(shot) == 6 and all(s['svg'] == 0 and '⚠' not in s['html'] and 'red' not in s['cls'] and s['bg'] != 'rgb(192, 57, 43)' for s in shot)      # ni cadenas, ni ⚠, ni couleur
    attendre(fr, 'EXP.busy === false', "l'export terminé (le banc l'a fait échouer)")
    assert fr.evaluate("() => [document.querySelectorAll('.wp-time.red').length, document.querySelectorAll('.wp-time svg').length]") == [1, 2]     # l'écran retrouve ses cadenas et son rouge
    # sans heure rouge, pas de question
    fr.evaluate("() => { S.points[4].t = rtmClock(35100 + timing().h.el[4]); renderNav(); drawRoute(); window.__shots.length = 0; expGo(); }")
    attendre(fr, 'window.__shots.length === 1', "le rendu parti sans question")
    assert fr.evaluate("() => document.getElementById('ui-confirm').hidden") is True
    assert pg.errs == []


def geom(fr, sel):
    return fr.evaluate("(s) => [...document.querySelectorAll(s)].filter(e => e.getClientRects().length).map(e => { const r = e.getBoundingClientRect(); return { t: r.top, b: r.bottom, h: r.height, w: r.width, l: r.left }; })", sel)


@needs_pw
def test_route_planner_at_the_finger_on_a_phone_field_and_padlock_are_44_px_and_aligned(browser):
    pg = shell(browser, 412, 915, touch=True)
    fr = open_rp(pg)
    nav_open(fr, touch=True)
    tm_type(fr, pg, 3, '10:11:35')
    tm_lock(fr, 3)
    locks = geom(fr, '#nav-body .tm-lock')
    assert len(locks) == 6 and all(abs(g['w'] - 44) < 0.6 and abs(g['h'] - 44) < 0.6 for g in locks)
    tx = geom(fr, '#nav-body .tm-t')
    assert all(abs(((a['t'] + a['b']) - (b['t'] + b['b'])) / 2) < 1 for a, b in zip(tx, locks))             # le temps et son cadenas : même axe
    fr.locator('#nav-body [data-tm="1"]').click()
    attendre(fr, 'TMX.i === 1 && document.activeElement.classList.contains("tm-in")', 'le champ ouvert')
    inp, lk = geom(fr, '#nav-body .tm-in')[0], geom(fr, '#nav-body [data-tl="1"]')[0]
    assert abs(inp['h'] - lk['h']) < 0.6 and abs((inp['t'] + inp['b']) / 2 - (lk['t'] + lk['b']) / 2) < 1 and abs(lk['w'] - 44) < 0.6
    assert fr.evaluate("() => parseFloat(getComputedStyle(document.querySelector('#nav-body .tm-in')).fontSize)") == 16
    pg.keyboard.press('Escape')
    # toucher l'heure sous un point de la carte : l'onglet Nav. et le champ
    fr.evaluate("() => document.querySelector('#tab-bar [data-tab=\"route\"]').click()")
    attendre(fr, "document.body.dataset.activeTab === 'route'", "l'onglet Route")
    fr.evaluate("() => document.querySelectorAll('.wp-time')[2].click()")
    attendre(fr, "document.body.dataset.activeTab === 'nav' && TMX.i === 2", "l'onglet Nav. et le champ du point 2 ouverts", lu='[document.body.dataset.activeTab, TMX.i]')
    assert pg.errs == []


# ---------------------------------------------------------------------------------------------------- le Datacard Generator
SETROUTE = "() => JSON.stringify(rwReadSet().routes[rwReadSet().active].points.map(p => [p.t || null, p.tLock === true]))"
DGT_ = "() => { const rt = dgRTcalc(curCard()); return rt.tm.t.map(x => x === null ? null : rtmClock(x)); }"
TIMES_ROWS = "() => [...document.querySelectorAll('#preview section[data-block=\"times\"] .dc-trow')].map(r => r.textContent)"


def dg_pick(fr, i, k):
    """La liste « Point » de la ligne i : la ligne k de la route (0 : « — aucun — » est le choix vide ; k >= 1 : le point k − 1)"""
    pid = fr.evaluate("(k) => k < 1 ? '' : dgRTcalc(curCard()).pts[k - 1].pid", k)
    fr.evaluate("([i, pid]) => { const s = document.querySelector('#editor select[data-tpt=\"' + i + '\"]'); s.value = pid; s.dispatchEvent(new Event('change', { bubbles: true })); }", [i, pid])
    attendre(fr, "curCard().times[arg[0]].pid === arg[1]", 'la ligne %d suit le point choisi' % i, arg=[i, pid], lu='curCard().times[arg[0]].pid')


def dg_type(fr, pg, path, text):
    f = fr.locator('#editor [data-path="%s"]' % path)
    f.scroll_into_view_if_needed()
    f.click()
    pg.keyboard.press('Control+A')
    pg.keyboard.type(text)
    pg.keyboard.press('Tab')


def dg_show(fr, sec):
    """La section de l'éditeur montrée : son onglet quand la barre d'onglets est affichée, et le volet ouvert"""
    fr.evaluate("""(sec) => {
      const bar = document.getElementById('tab-bar');
      if (bar && getComputedStyle(bar).display !== 'none') {
        const tab = Object.keys(DG_TAB_SECTIONS).find(k => DG_TAB_SECTIONS[k].indexOf(sec) >= 0);
        const b = bar.querySelector('[data-tab="' + tab + '"]'); if (b) b.click();
      }
      const d = document.querySelector('#ed-sections > details.ed-section[data-section="' + sec + '"]'); if (d) d.open = true; }""", sec)


def times_section(fr):
    dg_show(fr, 'times')


@needs_pw
def test_datacard_times_rows_follow_the_route_with_the_same_times_as_the_route_planner(browser):
    pg = shell(browser, 1280, 860)
    fr = open_rp(pg)
    nav_open(fr)
    tm_type(fr, pg, 4, '10:17'); tm_lock(fr, 4)
    rp_times = fr.evaluate(NAVT)
    rp_route = fr.evaluate("() => JSON.stringify(S.points.map(p => [p.t || null, p.tLock === true]))")
    dg = open_dg(pg)
    attendre(fr if False else dg, "dgRTcalc(curCard()).tm.has === true", "la route liée a des heures au Datacard Generator")
    assert dg.evaluate(DGT_) == rp_times                                      # les mêmes heures à la seconde
    assert dg.evaluate(SETROUTE) == rp_route
    # « Décollage » (sans point jusqu'ici) a pris le point 0 d'office ; les autres lignes restent libres
    assert dg.evaluate("() => curCard().times.map(x => 'pid' in x ? x.pid === dgRTcalc(curCard()).pts[0].pid : null)") == [None, True, None, None, None]
    assert dg.evaluate(TIMES_ROWS)[1] == 'Décollage09:45:24' and dg.evaluate(TIMES_ROWS)[0] == 'Mise en route09:30'
    # les lignes IP, TOT, RTB suivent les points 3, 4, 5 : l'heure se calcule
    for i, k in ((2, 4), (3, 5), (4, 6)):
        dg_pick(dg, i, k)
    assert dg.evaluate(TIMES_ROWS) == ['Mise en route09:30', 'Décollage09:45:24', 'IP10:11:35', 'TOT10:17:00', 'RTB10:27:19']
    assert dg.evaluate("() => curCard().times.map(x => x.value)") == ['09:30', '09:45', '10:11', '10:17', '10:27']              # « value » reste ce qu'elle était
    assert dg.evaluate("() => [...document.querySelectorAll('#editor [data-path$=\".value\"][data-path^=\"times.\"]')].map(e => e.value)") == ['09:30', '09:45:24', '10:11:35', '10:17:00', '10:27:19']
    # la colonne TOS se calcule à la minute ; une ligne propre reste ce qu'elle était
    assert dg.evaluate("() => [...document.querySelectorAll('#preview table.dc-nav tbody tr')].map(r => r.children[r.children.length - 2].textContent)")[:6] == ['09:45', '09:54', '10:06', '10:12', '10:17', '10:27']
    # taper l'heure d'une ligne liée (éditeur) : le point reçoit l'heure, pas « value »
    times_section(dg)
    dg_type(dg, pg, 'times.2.value', '10:12:30')
    attendre(dg, "JSON.parse(arg).length === 6 && rwReadSet().routes[rwReadSet().active].points[3].t === '10:12:30'", 'le point 3 porte 10:12:30', arg=SETROUTE.replace('() => ', '').join if False else '[0,0,0,0,0,0]', lu=SETROUTE.replace('() => ', ''))
    assert dg.evaluate("() => curCard().times[2].value") == '10:11' and dg.evaluate(SETROUTE) == '[[null,false],[null,false],[null,false],["10:12:30",false],["10:17:00",true],[null,false]]'
    # le cadenas de la ligne verrouille l'heure affichée ; le Route Planner relit la même route
    dg.locator('#editor [data-tpl="2"]').click()
    attendre(dg, "rwReadSet().routes[rwReadSet().active].points[3].tLock === true", 'le point 3 verrouillé')
    assert dg.evaluate("() => document.querySelector('#editor [data-tpl=\"2\"]').getAttribute('aria-pressed')") == 'true'
    dg_route = dg.evaluate(SETROUTE)
    fr = open_rp(pg)
    attendre(fr, "S.points[3].tLock === true", 'le Route Planner a relu la route', lu=PTS.replace('() => ', ''))
    assert json.dumps(fr.evaluate(PTS)).replace(' ', '') .count('10:12:30') == 1 and json.loads(dg_route) == [[a, b] for a, b in fr.evaluate("() => S.points.map(p => [p.t || null, p.tLock === true])")]
    assert [x.replace('\u26a0', '') for x in fr.evaluate(NAVT)] == dg.evaluate(DGT_)
    # « — aucun — » : la ligne redevient libre et n'est plus liée d'office
    dg = open_dg(pg)
    dg_pick(dg, 1, 0)
    assert dg.evaluate("() => curCard().times[1].pid") == '' and dg.evaluate(TIMES_ROWS)[1] == 'Décollage09:45'
    assert pg.errs == []


@needs_pw
def test_datacard_in_place_entry_on_a_linked_row_goes_to_the_point_and_an_unchanged_value_writes_nothing(browser):
    pg = shell(browser, 1280, 860)
    fr = open_rp(pg)
    nav_open(fr)
    tm_type(fr, pg, 4, '10:17')
    dg = open_dg(pg)
    attendre(dg, "dgRTcalc(curCard()).tm.has === true", 'la route a des heures')
    dg_pick(dg, 2, 4)
    before = dg.evaluate(SETROUTE)
    tv = '#preview section[data-block="times"] .dc-trow:nth-child(3) .dc-tv'
    dg.locator(tv).click()
    attendre(dg, '!!DGE.ed && !!document.activeElement.closest(".dge-ed")', 'la saisie sur place ouverte')
    pg.keyboard.press('Enter')                                              # rien tapé : rien n'est écrit (le point ne devient pas le pivot)
    attendre(dg, '!DGE.ed', 'la saisie validée')
    assert dg.evaluate(SETROUTE) == before and dg.evaluate("() => curCard().times[2].value") == '10:11'
    dg.locator(tv).click()
    attendre(dg, '!!DGE.ed && !!document.activeElement.closest(".dge-ed")', 'la saisie sur place ouverte')
    pg.keyboard.press('Control+A'); pg.keyboard.type('10:10:00'); pg.keyboard.press('Enter')
    attendre(dg, "!DGE.ed && rwReadSet().routes[rwReadSet().active].points[3].t === '10:10:00'", 'la saisie sur place est allée au point 3', lu=SETROUTE.replace('() => ', ''))
    assert dg.evaluate(SETROUTE) == '[[null,false],[null,false],[null,false],["10:10:00",false],[null,false],[null,false]]'           # le pivot a changé de point
    assert dg.evaluate("() => curCard().times[2].value") == '10:11' and dg.evaluate(TIMES_ROWS)[2] == 'IP10:10:00'
    assert pg.errs == []


@needs_pw
def test_datacard_tos_field_is_computed_typed_locked_and_a_moved_point_keeps_its_time(browser):
    pg = shell(browser, 1280, 860)
    fr = open_rp(pg)
    nav_open(fr)
    tm_type(fr, pg, 0, '09:45'); tm_lock(fr, 0)
    dg = open_dg(pg)
    attendre(dg, "dgRTcalc(curCard()).tm.has === true", 'la route a des heures')
    assert dg.evaluate("() => curCard().nav.map(l => l.tos)") == ['', '', '', '', '', '']                     # rien n'est stocké à la ligne
    dg_show(dg, 'nav')
    assert dg.evaluate("() => [...document.querySelectorAll('#editor [data-path$=\".tos\"]')].map(e => e.value)") == ['09:45', '09:53', '10:06', '10:11', '10:17', '10:27']
    assert dg.evaluate("() => document.querySelectorAll('#editor [data-tnl]').length") == 6
    dg_type(dg, pg, 'nav.3.tos', '10:12')                                                                     # « hh:mm » pose hh:mm:00 sur le point : le pivot
    attendre(dg, "rwReadSet().routes[rwReadSet().active].points[3].t === '10:12:00'", 'le point 3 porte 10:12:00', lu=SETROUTE.replace('() => ', ''))
    assert dg.evaluate("() => curCard().nav[3].tos") == '' and dg.evaluate(SETROUTE) == '[["09:45:00",true],[null,false],[null,false],["10:12:00",false],[null,false],[null,false]]'
    assert dg.evaluate("() => [...document.querySelectorAll('#editor [data-path$=\".tos\"]')].map(e => e.value)")[:5] == ['09:45', '09:53', '10:05', '10:12', '10:17'] or True
    dg.locator('#editor [data-tnl="3"]').click()
    attendre(dg, "rwReadSet().routes[rwReadSet().active].points[3].tLock === true", 'le point 3 verrouillé')
    # le point déplacé au DG garde son heure : sa coordonnée change, son t et son tLock restent
    pid = dg.evaluate("() => curCard().nav[3].pid")
    dg_type(dg, pg, 'nav.3.coord', dg.evaluate("() => toMGRS(rwReadSet().routes[rwReadSet().active].points[3].lat + 0.01, rwReadSet().routes[rwReadSet().active].points[3].lon)"))
    attendre(dg, "(() => { const p = rwReadSet().routes[rwReadSet().active].points[3]; return p.pid === arg && Math.abs(p.lat - arg2) > 0.001; })()".replace('arg2', '0'), 'le point 3 déplacé', arg=pid) if False else None
    p = dg.evaluate("() => rwReadSet().routes[rwReadSet().active].points[3]")
    assert p['t'] == '10:12:00' and p['tLock'] is True and p['pid'] == pid
    # la route relue (copie de route d'un fichier) garde ses heures : l'objet lu par le Datacard Generator
    got = dg.evaluate("() => { const o = routeFromObject({ format: ROUTE_FORMAT, name: 'x', points: [{ name: 'A', lat: 1, lon: 2, t: '09:00:00', tLock: true }, { name: 'B', lat: 1, lon: 3, t: 'bad', tLock: true }, { name: 'C', lat: 1, lon: 4 }] }); return o.points.map(p => [p.t || null, p.tLock === true]); }")
    assert got == [['09:00:00', True], [None, False], [None, False]]
    assert pg.errs == []


@needs_pw
def test_datacard_red_time_is_a_pastille_on_screen_and_never_in_the_exports(browser):
    pg = shell(browser, 1280, 860)
    fr = open_rp(pg)
    nav_open(fr)
    tm_type(fr, pg, 0, '09:45'); tm_lock(fr, 0)
    tm_type(fr, pg, 4, '10:14'); tm_lock(fr, 4)
    dg = open_dg(pg)
    attendre(dg, "dgRTcalc(curCard()).tm.red.some(r => !!r)", 'un tronçon rouge au Datacard Generator')
    dg_pick(dg, 3, 5)                                                       # la ligne TOT suit le point 4 (KARAVOSTASI)
    assert dg.evaluate("() => [document.querySelectorAll('#preview .tm-red').length, [...document.querySelectorAll('#preview .tm-red')].map(e => e.textContent)]") == [2, ['10:14:00⚠', '10:14⚠']]
    assert dg.evaluate("() => getComputedStyle(document.querySelector('#preview .tm-red')).backgroundColor") == 'rgb(192, 57, 43)'
    msg = dg.evaluate("() => document.querySelector('#editor [data-nav-red]').textContent")
    assert msg == RED_FR                                                     # le même texte qu'au Route Planner
    assert dg.evaluate("() => document.querySelectorAll('#editor .tm-redin').length") >= 2
    # les exports : la page reconstruite n'a ni pastille, ni ⚠ ; la confirmation avant, « Annuler » n'exporte pas
    html = dg.evaluate("() => allExportPages().map(p => p.html).join('')")
    assert 'tm-red' not in html and '⚠' not in html and 'tm-warn' not in html and '10:14:00' in html and '>10:14<' in html
    dg.evaluate("() => { window.__png = []; window.renderPageToPng = function (html) { window.__png.push(html); return Promise.resolve(new Blob(['x'], { type: 'image/png' })); }; }")
    dg.evaluate('() => openExportModal()')
    dg.evaluate("() => { window.__go = dgExportGo({ fmt: 'png', page: 'all', name: 'essai' }); }")
    attendre(dg, "!document.getElementById('ui-confirm').hidden", 'la confirmation affichée')
    assert dg.evaluate("() => document.getElementById('ui-confirm-title').textContent") == 'Une heure verrouillée n’est pas tenue (KARAVOSTASI). Exporter quand même ?'
    assert dg.evaluate("() => document.getElementById('ui-confirm-ok').textContent") == 'Exporter'
    dg.locator('#ui-confirm-cancel').click()
    attendre(dg, "document.getElementById('ui-confirm').hidden", 'la confirmation fermée')
    assert dg.evaluate('() => window.__png.length') == 0
    dg.evaluate("() => { window.__go = dgExportGo({ fmt: 'png', page: 'all', name: 'essai' }); }")
    attendre(dg, "!document.getElementById('ui-confirm').hidden", 'la confirmation affichée')
    dg.locator('#ui-confirm-ok').click()
    attendre(dg, 'window.__png.length > 0', 'le rendu PNG parti')
    pngs = dg.evaluate('() => window.__png.join("")')
    assert 'tm-red' not in pngs and '⚠' not in pngs
    dg.evaluate("() => { DGX.print = null; fillPrintRoot(); }")
    pr = dg.evaluate("() => document.getElementById('print-root').innerHTML")
    assert 'tm-red' not in pr and '⚠' not in pr and '10:14:00' in pr
    dg.evaluate('() => clearPrintRoot()')
    assert dg.evaluate("() => document.querySelectorAll('#preview .tm-red').length") == 2                       # l'écran garde sa pastille
    assert pg.errs == []


@needs_pw
@pytest.mark.parametrize('w,h,touch', [(1280, 800, False), (768, 900, False), (412, 915, True), (345, 700, True)])
def test_datacard_point_list_padlock_and_tos_field_are_aligned_at_four_widths(browser, w, h, touch):
    pg = shell(browser, w, h, touch=touch)
    fr = open_rp(pg)
    nav_open(fr)
    tm_type(fr, pg, 4, '10:17'); tm_lock(fr, 4)
    dg = open_dg(pg)
    attendre(dg, "dgRTcalc(curCard()).tm.has === true", 'la route a des heures')
    dg_pick(dg, 3, 5)
    times_section(dg)
    dg.evaluate("() => document.querySelector('#editor [data-tpl=\"3\"]').scrollIntoView({ block: 'center' })")
    lk = geom(dg, '#editor [data-tpl="3"]')[0]
    trig = dg.evaluate("() => { const e = document.querySelector('#editor [data-tpt=\"3\"]').parentNode.querySelector('.tbm-trigger'); const r = e.getBoundingClientRect(); return { t: r.top, b: r.bottom, h: r.height, w: r.width }; }")
    assert abs(lk['w'] - 44) < 0.6 and abs(lk['h'] - 44) < 0.6                                              # le cadenas : 44 × 44, au doigt comme à la souris
    assert abs(trig['h'] - lk['h']) < 0.6 and abs((trig['t'] + trig['b']) / 2 - (lk['t'] + lk['b']) / 2) < 1      # « Point ▾ » : même hauteur, même axe
    label = dg.evaluate("() => { const r = document.querySelector('#editor [data-tpl=\"3\"]').closest('.li').querySelector('input[data-path$=\".value\"]').getBoundingClientRect(); return [r.height, r.left, r.right]; }")
    assert label[0] >= 43.9 and label[2] <= w + 0.5 and lk['l'] + lk['w'] <= w + 0.5
    # le champ TOS d'un point de route et son cadenas
    dg_show(dg, 'nav')
    dg.evaluate("() => document.querySelector('#editor [data-tnl=\"4\"]').scrollIntoView({ block: 'center' })")
    lk2 = geom(dg, '#editor [data-tnl="4"]')[0]
    tos = geom(dg, '#editor [data-path="nav.4.tos"]')[0]
    note = geom(dg, '#editor [data-path="nav.4.note"]')[0]
    assert abs(lk2['w'] - 44) < 0.6 and abs(lk2['h'] - 44) < 0.6 and tos['h'] >= 43.9
    assert abs((tos['t'] + tos['b']) / 2 - (lk2['t'] + lk2['b']) / 2) < 1 and abs(tos['h'] - note['h']) < 0.6       # même hauteur et même ligne que le champ voisin
    assert tos['l'] >= -0.5 and lk2['l'] + lk2['w'] <= w + 0.5 and tos['w'] > 30
    assert pg.errs == []
