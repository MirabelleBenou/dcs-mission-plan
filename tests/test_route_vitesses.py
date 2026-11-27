"""Tenir une heure verrouillée par les vitesses (Route Planner et Datacard Generator) : la marge, la vitesse recommandée, « Appliquer », le cadenas de vitesse, les cibles de 44 px au doigt.
Sans navigateur (node, sur le bloc extrait de route_timing_block.build_block()) : les règles R5 et R6 sur un petit jeu de points de l'équateur écrit ici (la distance d'une branche est le rayon fois l'écart de
longitude, calculée ici à part) : orange dans la marge, rouge « marge », « verrous », « verrouillées » (et besoin nul), une branche verrouillée, des vitesses mêlées, « Appliquer » arrondi (km/h et kt), le cadenas.
Au navigateur (le shell construit, chromium, aucun réseau ; 1 280 × 800 à la souris et 768 × 1 024 au doigt) : la marge et sa saisie, le cadenas de vitesse, un tronçon orange (étiquettes, contour, bandeau, « Appliquer »,
la route écrite), le Datacard Generator orange égal au Route Planner, les cibles de 44 px. Les contrôles passent par le DOM, jamais par une capture."""
import json
import math
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_route_heures import (CHROMIUM, MAPT, NAVT, OFF, PTS, R, geom, hms, needs_node, needs_pw, node, open_dg, open_rp, secs, set_margin,  # noqa: E402
                               shell, tm_lock, tm_type, nav_open, dg_pick, dg_show)
from banc_attente import attendre, attendre_mise_en_page, cadre_export  # noqa: E402

ORANGE, ORANGE_LINE = 'rgb(224, 122, 18)', 'rgb(169, 86, 4)'
INK = """() => { const e = document.createElement('i'); e.style.color = 'var(--ink)'; document.body.appendChild(e); const c = getComputedStyle(e).color; e.remove(); return c; }"""      # --ink : l'encre du thème, jamais une couleur en dur
LONS = [0, 0.5, 1.2, 1.5, 2.3, 2.5]
LEG_KM = [R * math.radians(b - a) for a, b in zip(LONS, LONS[1:])]
SIZES = [(1280, 800, False), (768, 1024, True)]


# ---------------------------------------------------------------------------------------------------- le bloc, sans navigateur
def pts(**extra):
    out = [{'lat': 0, 'lon': lo} for lo in LONS]
    for k, v in extra.items():
        out[int(k[1:])].update(v)
    return out


def calc(points, margin=15, gs=220):
    return node('const p = %s; const T = rtmCompute(p, %s, %s); out({ t: T.t, clock: T.t.map(x => x === null ? null : rtmClock(x)), red: T.red, amb: T.amb, legs: T.legs, el: T.el, sec: T.sec, km: T.km });' % (json.dumps(points), gs, margin))


def times_for(speeds):
    el, s = [0.0], 0.0
    for km, v in zip(LEG_KM, speeds):
        s += km / v * 3600
        el.append(s)
    return el


@needs_node
def test_orange_within_the_margin_gives_each_free_leg_its_recommended_speed_and_b_keeps_its_time():
    ex = times_for([220] * 5)
    t0 = 32400
    want_b = t0 + ex[4] * 0.93                                  # 7 % plus court : il faut aller plus vite, dans la marge
    p = pts(p0={'t': '09:00:00', 'tLock': True}, p4={'t': hms(want_b), 'tLock': True})
    r = calc(p)
    assert r['red'] == [None] * 6 and r['amb'][4] is not None
    a = r['amb'][4]
    besoin = secs(hms(want_b)) - t0
    f = ex[4] / besoin
    assert a['a'] == 0 and a['free'] == [1, 2, 3, 4] and a['L'] == 0 and abs(a['f'] - f) < 1e-9
    for j in (1, 2, 3, 4):
        assert abs(r['legs'][j]['rec'] - 220 * f) < 1e-9 and r['legs'][j]['amb'] == 4
    assert 'rec' not in r['legs'][5]
    # les heures de a à b se calculent à ces vitesses ; b garde sa valeur ; la suite ne change pas (elle part de b)
    for i in range(4):
        assert abs(r['t'][i] - (t0 + ex[i] / f)) < 1e-6
    assert r['clock'][4] == hms(want_b) and abs(r['t'][5] - (secs(hms(want_b)) + (ex[5] - ex[4]))) < 1e-6
    # la durée totale compte les branches du tronçon à leurs vitesses recommandées : elle s'accorde à l'arrivée ; sans orange, elle est la somme des durées des branches
    assert abs(r['sec'] - (r['t'][5] - r['t'][0])) < 1e-6 and abs(r['sec'] - (besoin + ex[5] - ex[4])) < 1e-6 and r['sec'] < ex[5] - 1
    assert abs(calc(pts())['sec'] - ex[5]) < 1e-9 and abs(calc(pts(p0={'t': '09:00:00', 'tLock': True}, p4={'t': hms(t0 + ex[4]), 'tLock': True}))['sec'] - ex[5]) < 1e-9
    assert calc(p, margin=5)['red'][4]['why'] == 'm' and calc(p, margin=7)['red'][4]['why'] == 'm'                    # |f − 1| = 7,5 % : 5 et 7 ne tiennent pas, 8 tient
    assert calc(p, margin=8)['amb'][4] is not None and calc(p, margin=8)['red'][4] is None


@needs_node
def test_a_fixed_time_holds_to_five_seconds_then_is_orange_within_the_margin_and_red_beyond():
    ex = times_for([220] * 5)
    base = 32400 + ex[4]
    for off in (5, -5, 5.9, 6.5, -6.5, 120, 800):
        p = pts(p0={'t': '09:00:00', 'tLock': True}, p4={'t': hms(base + off), 'tLock': True})
        besoin = secs(hms(base + off)) - 32400
        unheld = abs(ex[4] - besoin) > 5                         # l'écart se juge sur les secondes entières posées
        r = calc(p)                                              # la marge de 15 %
        f = ex[4] / besoin
        wide = unheld and abs(f - 1) * 100 > 15
        assert (r['amb'][4] is not None) == (unheld and not wide) and (r['red'][4] is not None) == wide, (off, r['amb'][4], r['red'][4])
        if r['amb'][4] is not None:
            assert abs(r['amb'][4]['f'] - f) < 1e-9 and r['clock'][4] == hms(base + off)
        if wide:
            assert r['red'][4]['why'] == 'm'
    assert wide and unheld                                       # le dernier cas (800 s, plus de 15 %) est rouge


@needs_node
def test_the_four_red_causes_are_told_in_order_zero_need_all_locked_locked_legs_margin():
    ex = times_for([220] * 5)
    t0 = 32400
    base = pts(p0={'t': '09:00:00', 'tLock': True})
    # besoin nul
    p = json.loads(json.dumps(base)); p[3].update(t='09:00:00', tLock=True)
    assert calc(p)['red'][3]['why'] == '0' and calc(p)['amb'] == [None] * 6
    # aucune branche libre
    p = json.loads(json.dumps(base)); p[4].update(t=hms(t0 + ex[4] * 0.9), tLock=True)
    for j in (1, 2, 3, 4):
        p[j]['gs'] = 220; p[j]['gsLock'] = True
    r = calc(p)
    assert r['red'][4]['why'] == 'lk' and r['amb'] == [None] * 6
    # besoin ≤ L : les branches verrouillées prennent déjà tout le temps
    p = json.loads(json.dumps(base)); p[4].update(t=hms(t0 + ex[2] - 30), tLock=True)
    for j in (1, 2):
        p[j]['gs'] = 220; p[j]['gsLock'] = True
    r = calc(p)
    assert r['red'][4]['why'] == 'lt' and abs(r['red'][4]['L'] - ex[2]) < 1e-6
    # la marge
    p = json.loads(json.dumps(base)); p[4].update(t=hms(t0 + ex[4] * 0.5), tLock=True)
    assert calc(p)['red'][4]['why'] == 'm'


@needs_node
def test_a_locked_leg_keeps_its_time_and_the_factor_is_worked_out_on_the_free_legs_only():
    ex = times_for([220] * 5)
    t0 = 32400
    p = pts(p0={'t': '09:00:00', 'tLock': True}, p4={'t': hms(t0 + ex[4] * 0.95), 'tLock': True}, p2={'gs': 200, 'gsLock': True})
    r = calc(p)
    sp = [220, 200, 220, 220, 220]
    el = times_for(sp)
    L = el[2] - el[1]
    besoin = secs(hms(t0 + ex[4] * 0.95)) - t0
    f = (el[4] - L) / (besoin - L)
    a = r['amb'][4]
    assert a is not None and a['free'] == [1, 3, 4] and abs(a['L'] - L) < 1e-6 and abs(a['f'] - f) < 1e-9
    assert 'rec' not in r['legs'][2] and r['legs'][2]['lock'] is True and all(abs(r['legs'][j]['rec'] - 220 * f) < 1e-9 for j in (1, 3, 4))
    assert abs(r['t'][2] - (t0 + (el[1] - el[0]) / f + L)) < 1e-6                       # la branche verrouillée garde sa durée
    # une vitesse verrouillée sans p.gs valide ne compte pas (gsLock exige p.gs)
    p[2].pop('gs')
    assert calc(p)['legs'][2]['lock'] is False


@needs_node
def test_mixed_speeds_give_no_common_speed_in_the_messages_and_the_percentage_is_signed():
    ex = times_for([220, 300, 220, 220, 220])
    t0 = 32400
    p = pts(p0={'t': '09:00:00', 'tLock': True}, p4={'t': hms(t0 + ex[4] * 0.97), 'tLock': True}, p2={'gs': 300})
    prog = """const p = %s; const T = rtmCompute(p, 220, 15);
      const o = { t: (k, v) => k + '|' + [v.a, v.ha, v.b, v.hb, v.n, v.v, v.k, v.m].join('|') + ' ()', speedText: x => Math.round(x) + ' km/h', fr: false, name: k => 'P' + k, margin: 15 };
      out([T.amb.map((r, i) => r ? rtmAmbMsg(p, T, i, o) : null), T.amb.map((r, i) => r ? rtmLegLabel(T, i, { t: (k, v) => k + '|' + v.v + '|' + v.n, speedText: x => Math.round(x * 10) / 10 + ' km/h', fr: false }) : null), T.legs.map((l, j) => l ? rtmLegLabel(T, j, { t: (k, v) => k + '|' + v.v + '|' + v.n, speedText: x => Math.round(x) + ' km/h', fr: false }) : '')]);""" % json.dumps(p)
    m, _x, labels = node(prog)
    msg = m[4]
    assert msg['text'].startswith('t.amb|P0|09:00:00|P4|') and msg['text'].split('|')[5] == '+3%' and msg['text'].split('|')[6] == '' and msg['text'].split('|')[7] == '4' and not msg['text'].endswith('()')
    assert labels[2] == 't.leg|%d km/h|+3%%' % round(300 * ex[4] / (secs(hms(t0 + ex[4] * 0.97)) - t0)) and labels[1].startswith('t.leg|%d km/h|' % round(220 * ex[4] / (secs(hms(t0 + ex[4] * 0.97)) - t0)))
    assert labels[5] == '' and labels[0] == ''
    # une seule branche libre : la clé « sur la branche » (t.amb.1), et sa vitesse recommandée
    p = pts(p0={'t': '09:00:00', 'tLock': True}, p1={'t': hms(t0 + ex[1] * 0.97), 'tLock': True})
    m = node("const p = %s; const T = rtmCompute(p, 220, 15); const o = { t: (k, v) => k + '|' + v.k + '|' + v.v, speedText: x => Math.round(x) + ' km/h', fr: false, name: k => 'P' + k, margin: 15 }; out(T.amb.map((r, i) => r ? rtmAmbMsg(p, T, i, o).text : null));" % json.dumps(p))
    f1 = (times_for([220] * 5)[1]) / (secs(hms(t0 + ex[1] * 0.97)) - t0)
    assert m[1] == 't.amb.1|1|%d km/h' % round(220 * f1) and m[0] is None


@needs_node
def test_apply_writes_the_free_legs_rounded_to_the_displayed_unit_and_nothing_else():
    ex = times_for([220] * 5)
    t0 = 32400
    p = pts(p0={'t': '09:00:00', 'tLock': True}, p4={'t': hms(t0 + ex[4] * 0.94), 'tLock': True}, p2={'gs': 230, 'gsLock': True}, p5={'gs': 250})
    f = (times_for([220, 230, 220, 220, 250])[4] - (times_for([220, 230, 220, 220, 250])[2] - times_for([220, 230, 220, 220, 250])[1])) / (secs(hms(t0 + ex[4] * 0.94)) - t0 - (times_for([220, 230, 220, 220, 250])[2] - times_for([220, 230, 220, 220, 250])[1]))
    kmh = node("const p = %s; const T = rtmCompute(p, 220, 15); const ok = rtmApply(p, T, 4, x => Math.round(x)); out([ok, p.map(q => q.gs === undefined ? null : q.gs), p.map(q => q.gsLock === true), rtmApply(p, T, 3, x => Math.round(x))]);" % json.dumps(p))
    assert kmh[0] is True and kmh[3] is False
    assert kmh[1][1] == round(220 * f) and kmh[1][3] == round(220 * f) and kmh[1][4] == round(220 * f)         # les branches libres, arrondies
    assert kmh[1][2] == 230 and kmh[1][5] == 250 and kmh[1][0] is None and kmh[2] == [False, False, True, False, False, False]    # la verrouillée et un autre tronçon : intactes
    nm = node("const p = %s; const T = rtmCompute(p, 220, 15); const NM = 1.852; rtmApply(p, T, 4, x => Math.round(Math.round(x / NM) * NM * 10000) / 10000); out(p.map(q => q.gs === undefined ? null : q.gs));" % json.dumps(p))
    assert nm[1] == round(round(220 * f / 1.852) * 1.852, 4) and round(nm[1] / 1.852) == round(220 * f / 1.852)
    # une fois les vitesses écrites, le tronçon se recalcule : l'écart restant est l'arrondi, sous 5 s ici
    p2 = json.loads(json.dumps(p))
    for j in (1, 3, 4):
        p2[j]['gs'] = round(220 * f)
    r = calc(p2)
    assert r['red'][4] is None and r['amb'][4] is None                         # tenu : l'écart restant est sous 5 s


@needs_node
def test_the_speed_padlock_and_the_stored_fields_follow_the_rules():
    r = node("""
      const mk = () => [0, 0.5, 1.2].map(l => ({ lat: 0, lon: l }));
      const p = mk(); const log = [];
      log.push(rtmLockGs(p, 0, 220));                                          // jamais au point 0
      log.push(rtmLockGs(p, 1, 220), p[1].gs, p[1].gsLock);                    // sans p.gs : la vitesse par défaut d'abord
      p[2].gs = 250; log.push(rtmLockGs(p, 2, 220), p[2].gs, p[2].gsLock);     // avec p.gs : il reste
      rtmUnlockGs(p, 1); log.push(p[1].gs, p[1].gsLock === undefined);         // déverrouiller : p.gs reste
      const d = {}; rtmReadGs({ gs: 300, gsLock: true }, d, 2); const e = {}; rtmReadGs({ gs: 300, gsLock: true }, e, 0); const f = {}; rtmReadGs({ gsLock: true }, f, 2); const g = {}; rtmReadGs({ gs: -1, gsLock: true }, g, 2); const h = {}; rtmReadGs({ gs: 300 }, h, 1);
      log.push([d, e, f, g, h]);
      log.push([15, 1, 50, 0, 51, 2.5, '20', null, 7].map(rtmMargin));
      out(log);""")
    assert r[0] is False and r[1:4] == [True, 220, True] and r[4:7] == [True, 250, True] and r[7:9] == [220, True]
    assert r[9] == [{'gs': 300, 'gsLock': True}, {}, {}, {}, {'gs': 300}]
    assert r[10] == [15, 1, 50, 15, 15, 15, 15, 15, 7]


# ---------------------------------------------------------------------------------------------------- le navigateur
@pytest.fixture(scope='module')
def browser():
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        br = p.chromium.launch(executable_path=str(CHROMIUM), args=['--no-sandbox'])
        yield br
        br.close()


def hit(loc, touch):
    """Le geste réel : le toucher au doigt, le clic à la souris"""
    loc.scroll_into_view_if_needed()
    if touch:
        loc.tap()
    else:
        loc.click()


def route_tab(fr):
    fr.evaluate("() => rpSetTab('route')")
    attendre(fr, "!!document.querySelector('#pts .pt-row.pts')", 'les lignes de points')


def lock_speed(fr, i, touch):
    route_tab(fr)
    hit(fr.locator('#pts .pt-row.pts').nth(i).locator('.gs-lock'), touch)
    attendre(fr, 'S.points[arg].gsLock === true', 'la vitesse du point %d verrouillée' % i, arg=i, lu='S.points[arg].gsLock')


def lock_two(fr, pg, margin=None):
    """deux heures verrouillées, 09:45 → 10:14 (points 0 et 4)"""
    nav_open(fr)
    tm_type(fr, pg, 0, '09:45'); tm_lock(fr, 0)
    tm_type(fr, pg, 4, '10:14'); tm_lock(fr, 4)
    if margin:
        set_margin(fr, margin)


def haversine(a, b):
    r = math.pi / 180
    p1, p2, dl = a['lat'] * r, b['lat'] * r, (b['lon'] - a['lon']) * r
    h = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(min(1, math.sqrt(h)))


def expect(points, a, b, ta, tb, margin, gsdef=220):
    """Le tronçon a → b calculé ici, à part du bloc : f, L, les vitesses recommandées, les heures de a à b"""
    legs = []
    for i in range(1, len(points)):
        p = points[i]
        v = p['gs'] if isinstance(p.get('gs'), (int, float)) and p['gs'] > 0 else gsdef
        legs.append((haversine(points[i - 1], p), v, p.get('gsLock') is True and isinstance(p.get('gs'), (int, float))))
    sec = [km / v * 3600 for km, v, _l in legs]
    L = sum(s for s, (_k, _v, lk) in zip(sec[a:b], legs[a:b]) if lk)
    actuel = sum(sec[a:b])
    besoin = (tb - ta) % 86400
    f = (actuel - L) / (besoin - L)
    t, s = [ta], ta
    for j in range(a, b):
        s += sec[j] if legs[j][2] else sec[j] / f
        t.append(s)
    plain, s = [ta], ta
    for j in range(a, b):
        s += sec[j]
        plain.append(s)
    return {'f': f, 'L': L, 'besoin': besoin, 'actuel': actuel, 'rec': {j + 1: legs[j][1] * f for j in range(a, b) if not legs[j][2]}, 't': t, 'plain': plain}


def pct(f, fr):
    n = round((f - 1) * 100) or (1 if f >= 1 else -1)
    return ('−' if n < 0 else '+') + str(abs(n)) + (' %' if fr else '%')


def amb_text(names, ex, k, common, margin, fr, ha, hb):
    n = pct(ex['f'], fr)
    v = ' (%d km/h)' % round(common) if common is not None else ''
    if fr:
        return 'Heures verrouillées %s %s → %s %s : tenues à %s%s sur %s, dans la marge ±%d %%.' % (names[0], ha, names[1], hb, n, v, 'la branche' if k == 1 else 'les %d branches' % k, margin)
    return 'Locked times %s %s → %s %s: met at %s%s on %s, within the ±%d%% margin.' % (names[0], ha, names[1], hb, n, v, 'the leg' if k == 1 else 'the %d legs' % k, margin)


READ = """() => ({ pts: S.points.map(p => ({ t: p.t || null, tLock: p.tLock === true, gs: typeof p.gs === 'number' ? p.gs : null, gsLock: p.gsLock === true, lat: p.lat, lon: p.lon, name: p.name })),
  state: [...document.querySelectorAll('.wp-time')].map(e => e.classList.contains('red') ? 'red' : e.classList.contains('amb') ? 'amb' : 'none'), clocks: timing().h.t.map(x => x === null ? null : rtmClock(x)) })"""


@needs_pw
@pytest.mark.parametrize('w,h,touch', SIZES)
def test_margin_field_and_speed_padlocks_are_aligned_and_follow_the_rules(browser, w, h, touch):
    pg = shell(browser, w, h, touch=touch)
    fr = open_rp(pg)
    nav_open(fr)
    # la marge à côté de la vitesse sol : même largeur, même hauteur, libellés alignés
    g = fr.evaluate("""() => { const q = id => { const e = document.getElementById(id), l = document.querySelector('label[for="' + id + '"]'), r = e.getBoundingClientRect(), lr = l.getBoundingClientRect();
      return { w: r.width, h: r.height, top: r.top, left: r.left, lt: lr.top, lb: lr.bottom, ll: lr.left, text: l.textContent, v: e.value }; }; return { gs: q('gs-def'), mg: q('mg-def') }; }""")
    gs, mg = g['gs'], g['mg']
    assert abs(gs['w'] - mg['w']) < 0.6 and abs(gs['h'] - mg['h']) < 0.6 and abs(gs['top'] - mg['top']) < 0.6 and abs(gs['lt'] - mg['lt']) < 0.6 and abs(gs['lb'] - mg['lb']) < 0.6, g
    assert mg['left'] > gs['left'] + gs['w'] - 1 and abs(mg['ll'] - mg['left']) < 0.6 and mg['text'] == 'Marge (± %)' and mg['v'] == '15'
    assert fr.evaluate("() => document.getElementById('mg-note').textContent") == 'Marge : variation permise des vitesses pour tenir les heures verrouillées.'
    # saisie : un entier de 1 à 50 ; à la frappe, il s'écrit s'il n'est pas le début d'une saisie plus longue ; en quittant le champ, hors bornes il rend la valeur d'avant l'entrée
    m = fr.locator('#mg-def')
    spm = lambda: fr.evaluate('() => S.speedMargin')
    m.fill('30')
    assert spm() == 30
    for bad in ('0', '51', 'abc', '7,5', ''):
        m.fill(bad)
        assert spm() == 30, bad                                                                                      # hors règle : rien ne change pendant la frappe
    m.evaluate('e => e.dispatchEvent(new Event("change", { bubbles: true }))')
    assert m.input_value() == '15' and spm() == 15                                                                   # en quittant : la valeur d'avant l'entrée (15), pas celle de la dernière frappe valide
    # taper « 60 » depuis 15 : « 6 » ne peut pas devenir un entier de 1 à 50 (il s'écrit), « 60 » est hors bornes : le champ rend 15
    m.click(); m.press('Control+A'); m.press('6')
    assert spm() == 6
    m.press('0')
    assert m.input_value() == '60' and spm() == 6
    m.press('Tab')
    attendre(fr, 'S.speedMargin === 15', 'la marge rendue à 15', lu='S.speedMargin')
    assert m.input_value() == '15' and fr.evaluate("() => JSON.parse(localStorage.getItem('route_state_v1')).speedMargin") == 15
    # un chiffre de 1 à 5 peut être le début de 10 à 50 : il attend la suite, et s'écrit en quittant le champ ; deux chiffres s'écrivent à la frappe
    m.click(); m.press('Control+A'); m.press('3')
    assert spm() == 15
    m.press('Tab')
    attendre(fr, 'S.speedMargin === 3', 'la marge à 3', lu='S.speedMargin')
    m.click(); m.press('Control+A'); m.press('5')
    assert spm() == 3
    m.press('0')
    assert spm() == 50
    m.press('Tab')
    m.click(); m.press('Control+A'); m.type('1'); m.press('Tab')
    attendre(fr, 'S.speedMargin === 1', 'la marge à 1', lu='S.speedMargin')
    m.click(); m.press('Control+A'); m.type('15'); m.press('Tab')
    attendre(fr, 'S.speedMargin === 15', 'la marge à 15', lu='S.speedMargin')
    assert fr.evaluate("() => JSON.parse(localStorage.getItem('route_state_v1')).speedMargin") == 15 and m.input_value() == '15'
    # le cadenas de vitesse : un par point sauf le 0, à l'intérieur du champ, ni colonne ni largeur de plus
    route_tab(fr)
    assert fr.evaluate("() => [...document.querySelectorAll('#pts .pt-row.pts')].map(r => r.querySelectorAll('.gs-lock').length)") == [0, 1, 1, 1, 1, 1]
    d = fr.evaluate("""() => { const r = document.querySelectorAll('#pts .pt-row.pts')[2], i = r.querySelector('[data-k=gs]').getBoundingClientRect(), b = r.querySelector('.gs-lock').getBoundingClientRect(), e = r.querySelector('[data-k=gs]');
      const z = document.querySelectorAll('#pts .pt-row.pts')[0].querySelector('[data-k=gs]').getBoundingClientRect();
      return { iw: i.width, ih: i.height, bl: b.left - i.left, br: i.right - b.right, bt: b.top - i.top, bb: i.bottom - b.bottom, bw: b.width, bh: b.height, zw: z.width, sw: e.scrollWidth, cw: e.clientWidth }; }""")
    assert abs(d['iw'] - 62) <= 1 and abs(d['iw'] - d['zw']) < 0.6                                                  # la colonne VIT. de la base
    assert d['bl'] >= 0 and d['br'] >= -0.5 and d['br'] <= 2 and d['bt'] >= -0.5 and d['bb'] >= -0.5                    # dans le champ, à droite
    assert abs(d['bw'] - (24 if touch else 20)) < 0.6 and abs(d['bh'] - d['ih']) < 1.2 and (d['ih'] >= 43.9 if touch else True)
    # le cadenas ouvert se voit : contraste d'au moins 3 : 1 sur le fond du champ
    ratio = fr.evaluate("""() => { const r = document.querySelectorAll('#pts .pt-row.pts')[2], b = r.querySelector('.gs-lock'), i = r.querySelector('[data-k=gs]');
      const rgb = c => c.match(/[\\d.]+/g).map(Number), fg = rgb(getComputedStyle(b).color), bg = rgb(getComputedStyle(i).backgroundColor), o = parseFloat(getComputedStyle(b).opacity);
      const lum = c => { const f = v => { v /= 255; return v <= .03928 ? v / 12.92 : Math.pow((v + .055) / 1.055, 2.4); }; return .2126 * f(c[0]) + .7152 * f(c[1]) + .0722 * f(c[2]); };
      const mix = [0, 1, 2].map(k => o * fg[k] + (1 - o) * bg[k]), L1 = lum(mix), L2 = lum(bg.slice(0, 3));
      return [(Math.max(L1, L2) + .05) / (Math.min(L1, L2) + .05), o]; }""")
    assert ratio[0] >= 3 and ratio[1] >= 0.62, ratio
    assert d['sw'] <= d['cw']                                                                                        # « 220 » se lit, le cadenas déduit
    lbl = lambda: fr.evaluate("() => { const b = document.querySelectorAll('#pts .pt-row.pts')[2].querySelector('.gs-lock'); return [b.getAttribute('aria-label'), b.title, b.hasAttribute('aria-pressed')]; }")
    assert lbl() == ['Verrouiller la vitesse', 'Verrouiller la vitesse', False]
    hit(fr.locator('#pts .pt-row.pts').nth(2).locator('.gs-lock'), touch)                                           # sans p.gs : la vitesse par défaut d'abord
    attendre(fr, 'S.points[2].gsLock === true', 'le verrou posé', lu='S.points[2].gsLock')
    assert fr.evaluate("() => [S.points[2].gs, S.points[2].gsLock, document.querySelectorAll('#pts .pt-row.pts')[2].querySelector('[data-k=gs]').value]") == [220, True, '220']
    assert lbl() == ['Déverrouiller la vitesse', 'Déverrouiller la vitesse', False]
    row = fr.locator('#pts .pt-row.pts').nth(2)
    row.locator('[data-k=gs]').fill('1100')                                                                          # quatre chiffres à côté du cadenas, sans élargir la colonne
    fit = fr.evaluate("() => { const e = document.querySelectorAll('#pts .pt-row.pts')[2].querySelector('[data-k=gs]'); return [e.value, e.scrollWidth <= e.clientWidth, e.getBoundingClientRect().width]; }")
    assert fit[0] == '1100' and fit[1] is True and abs(fit[2] - 62) <= 1, fit
    row.locator('[data-k=gs]').fill('250')                                                                           # une vitesse verrouillée se saisit encore : le verrou reste
    assert fr.evaluate("() => [S.points[2].gs, S.points[2].gsLock]") == [250, True]
    hit(row.locator('.gs-lock'), touch)
    attendre(fr, 'S.points[2].gsLock !== true', 'le verrou retiré', lu='S.points[2].gsLock')
    assert fr.evaluate("() => [S.points[2].gs, S.points[2].gsLock === undefined]") == [250, True] and lbl()[0] == 'Verrouiller la vitesse'       # déverrouiller garde p.gs
    hit(row.locator('.gs-lock'), touch)
    attendre(fr, 'S.points[2].gsLock === true', 'reverrouillé', lu='S.points[2].gsLock')
    row.locator('.gs-lock').focus(); pg.keyboard.press('Enter')                                                       # au clavier : le focus reste sur le cadenas de la même ligne
    attendre(fr, 'S.points[2].gsLock !== true', 'le verrou retiré au clavier', lu='S.points[2].gsLock')
    assert fr.evaluate("() => [document.activeElement.classList.contains('gs-lock'), document.activeElement.closest('.pt-row').dataset.i]") == [True, '2']
    pg.keyboard.press('Space')
    attendre(fr, 'S.points[2].gsLock === true', 'reverrouillé au clavier', lu='S.points[2].gsLock')
    assert fr.evaluate("() => [document.activeElement.classList.contains('gs-lock'), document.activeElement.closest('.pt-row').dataset.i]") == [True, '2']
    row.locator('[data-k=gs]').fill('')                                                                              # vider : plus de vitesse, plus de verrou
    assert fr.evaluate("() => [S.points[2].gs === undefined, S.points[2].gsLock === undefined]") == [True, True] and lbl()[0] == 'Verrouiller la vitesse'
    # au doigt : le n° et la croix font au moins 44 × 44, la colonne VIT. reste celle de la base
    t = fr.evaluate("""() => { const r = document.querySelectorAll('#pts .pt-row.pts')[1], n = r.querySelector('.pt-num').getBoundingClientRect(), x = r.querySelector('.pt-del').getBoundingClientRect(); return { nw: n.width, nh: n.height, xw: x.width, xh: x.height }; }""")
    if touch:
        assert t['nw'] >= 43.9 and t['nh'] >= 43.9 and t['xw'] >= 43.9 and t['xh'] >= 43.9, t
    else:
        assert t['nw'] <= 31 and t['xw'] <= 35, t                                                                    # à la souris, rien ne change
    assert pg.errs == []


def names_of(fr):
    return fr.evaluate("() => S.points.map(p => p.name)")


@needs_pw
@pytest.mark.parametrize('w,h,touch,lang', [(1280, 800, False, 'fr'), (768, 1024, True, 'en')])
def test_an_orange_leg_shows_its_label_outline_banner_and_apply_writes_the_route(browser, w, h, touch, lang):
    fr_ = lang == 'fr'
    pg = shell(browser, w, h, touch=touch, lang=lang)
    fr = open_rp(pg)
    lock_two(fr, pg)
    st = fr.evaluate(READ)
    assert st['pts'][0]['tLock'] and st['pts'][4]['tLock'] and st['state'] == ['none', 'none', 'none', 'none', 'amb', 'none']
    ex = expect(st['pts'], 0, 4, secs('09:45:00'), secs('10:14:00'), 15)
    clk = [hms(x) for x in ex['t']]
    assert fr.evaluate(NAVT)[:5] == clk and fr.evaluate(MAPT)[:5] == clk and st['clocks'][:5] == clk                   # les heures de a à b, à ces vitesses ; b à son heure
    # la pastille orange : variable commune, texte à l'encre, sans ⚠, avec le cadenas de b
    css = fr.evaluate("""() => { const m = document.querySelectorAll('.wp-time')[4], t = document.querySelector('#nav-body .tm-t.amb'); return [getComputedStyle(m).backgroundColor, getComputedStyle(m).color, m.textContent, m.querySelectorAll('svg').length, getComputedStyle(t).backgroundColor, t.textContent]; }""")
    ink = fr.evaluate(INK)
    assert css[0] == ORANGE and css[1] == ink and sum(int(x) for x in re.findall(r'\d+', ink)[:3]) < 200 and '⚠' not in css[2] and css[3] == 1 and css[4] == ORANGE and '⚠' not in css[5]
    # les boîtes (complète) : contour orange, une étiquette en pastille sous chacune
    names = names_of(fr)
    labels = fr.evaluate("() => [...document.querySelectorAll('.amb-box')].map(e => e.textContent)")
    want = '→ %d km/h (%s)' % (round(220 * ex['f']), pct(ex['f'], fr_))
    assert labels == [want] * 4 and fr.evaluate("() => [...document.querySelectorAll('.lb-amb')].map(e => +e.dataset.leg)") == [1, 2, 3, 4]
    box = fr.evaluate("""() => { const b = document.querySelector('.lb-amb'), l = b.querySelector('.amb-lab'), p = b.querySelector('.lb-bg'), r = b.getBoundingClientRect(), q = l.getBoundingClientRect();
      return [getComputedStyle(p).stroke, getComputedStyle(l).backgroundColor, getComputedStyle(l).color, document.querySelectorAll('.lb:not(.lb-amb)').length, q.width > 0]; }""")
    assert box == [ORANGE_LINE, ORANGE, ink, 1, True]                                                  # la branche 5, hors du tronçon, garde sa boîte et son trait
    # le bandeau : le bandeau commun (pas « err »), son filet orange, le texte, puis « Appliquer »
    ban = fr.evaluate("""() => [...document.querySelectorAll('#nav-amb .ui-bandeau')].map(e => ({ cls: e.className, text: e.querySelector('.amb-t').textContent, bold: [...e.querySelectorAll('b')].map(b => b.textContent), bl: getComputedStyle(e).borderLeftColor, btn: e.querySelector('button').textContent, bh: e.querySelector('button').getBoundingClientRect().height }))""")
    assert len(ban) == 1 and 'err' not in ban[0]['cls'] and ban[0]['bl'] == ORANGE and ban[0]['btn'] == ('Appliquer' if fr_ else 'Apply') and (ban[0]['bh'] >= 43.9 if touch else True)
    assert ban[0]['text'] == amb_text((names[0], names[4]), ex, 4, 220 * ex['f'], 15, fr_, '09:45:00', '10:14:00')
    assert ban[0]['bold'] == [('Heures verrouillées ' if fr_ else 'Locked times ') + names[0] + ' 09:45:00 → ' + names[4] + ' 10:14:00', pct(ex['f'], fr_)]
    assert fr.evaluate("() => document.getElementById('nav-red').hidden") is True
    # « Aucune » : l'étiquette seule, au milieu de la branche, sans boîte
    fr.evaluate("() => { S.legBoxes = 'none'; persistState(); drawDecorNow(); }")
    long_legs = fr.evaluate("() => S.points.slice(1).filter((q, k) => map.latLngToContainerPoint([S.points[k].lat, S.points[k].lon]).distanceTo(map.latLngToContainerPoint([q.lat, q.lon])) >= LEG_LABEL_MIN_PX).length")
    solo = fr.evaluate("() => [document.querySelectorAll('.lb').length, [...document.querySelectorAll('.amb-solo')].map(e => e.textContent), document.querySelectorAll('.leg-label').length]")
    assert solo[0] == 0 and solo[1] == [want] * 4 and solo[2] == long_legs                                                           # une étiquette seule par branche orange (1 à 4), sans condition de longueur ; les lignes « cap · distance » restent celles des branches d'au moins 120 px
    # très loin : les branches sont plus courtes que les 60 px d'une boîte et que les 120 px d'une ligne « cap · distance » ; chaque branche orange a encore son étiquette
    fr.evaluate("() => { window.__z = map.getZoom(); map.setZoom(4, { animate: false }); drawDecorNow(); }")
    short = fr.evaluate("() => [[...document.querySelectorAll('.amb-solo')].map(e => e.textContent), document.querySelectorAll('.leg-label').length]")
    assert short == [[want] * 4, 0], short
    fr.evaluate("() => { S.legBoxes = 'full'; persistState(); drawDecorNow(); }")
    short = fr.evaluate("() => [[...document.querySelectorAll('.amb-solo')].map(e => e.textContent), document.querySelectorAll('.lb').length, document.querySelectorAll('.amb-box').length]")
    assert short == [[want] * 4, 0, 0], short                                                                       # avec boîtes : la boîte n'est pas dessinée, l'étiquette seule au milieu de la branche
    fr.evaluate("() => { map.setZoom(window.__z, { animate: false }); drawDecorNow(); }")
    # « Appliquer » : p.gs de chaque branche libre, l'entier de l'unité ; ni point 0 ni autre champ ; la route se recalcule
    pack0 = fr.evaluate("() => JSON.stringify(packRoutePoints({ points: S.points.map(p => Object.assign({}, p)) }))")
    hit(fr.locator('#nav-amb [data-apply="4"]'), touch)
    attendre(fr, "S.points[1].gs !== undefined", 'les vitesses écrites', lu='S.points[1].gs')
    sp = round(220 * ex['f'])
    after = fr.evaluate(READ)
    assert [p['gs'] for p in after['pts']] == [None, sp, sp, sp, sp, None] and not any(p['gsLock'] for p in after['pts'])
    assert after['pts'][0]['t'] == '09:45:00' and after['pts'][4]['t'] == '10:14:00' and after['pts'][4]['tLock']
    ex2 = expect(after['pts'], 0, 4, secs('09:45:00'), secs('10:14:00'), 15)
    held = abs(ex2['actuel'] - ex2['besoin']) <= 5
    clk2 = [hms(x) for x in (ex2['plain'][:-1] + [secs('10:14:00')] if held else ex2['t'])]                                                # tenu : les heures aux vitesses de la route
    assert fr.evaluate(NAVT)[:5] == clk2 and abs(ex2['f'] - 1) < 0.01 and after['clocks'][:5] == clk2
    if held:                                                                  # l'arrondi laisse l'écart sous 5 s : tenu, plus de signe
        assert after['state'] == ['none'] * 6 and fr.evaluate("() => document.querySelectorAll('#nav-amb .ui-bandeau, .amb-lab, .lb-amb').length") == 0
    else:
        assert after['state'][4] == 'amb' and pct(ex2['f'], fr_) in fr.evaluate("() => document.querySelector('#nav-amb .amb-t').textContent")
    # la route écrite : le paquet .miz porte les vitesses appliquées (packPoint, comme toute p.gs)
    pack = fr.evaluate("() => packRoutePoints({ points: S.points.map(p => Object.assign({}, p)) })")
    spd = [round(pack[str(k + 1)]['speed'] * 3.6, 3) for k in range(6)]
    assert spd[1:5] == [float(sp)] * 4 and spd[5] == 220.0 and pack0 != json.dumps(pack)
    assert fr.evaluate("() => JSON.parse(localStorage.getItem('route_state_v1')).points.map(p => p.gs === undefined ? null : p.gs)") == [None, sp, sp, sp, sp, None]
    assert pg.errs == []


@needs_pw
@pytest.mark.parametrize('w,h,touch', SIZES)
def test_a_locked_speed_is_not_applied_two_stretches_apply_one_at_a_time_and_kt_rounds_to_the_unit(browser, w, h, touch):
    pg = shell(browser, w, h, touch=touch)
    fr = open_rp(pg)
    nav_open(fr)
    tm_type(fr, pg, 0, '09:45'); tm_lock(fr, 0); tm_type(fr, pg, 4, '10:15'); tm_lock(fr, 4)                       # la branche du point 2 verrouillée (à 220)
    lock_speed(fr, 2, touch)
    nav_open(fr)
    st = fr.evaluate(READ)
    assert st['state'][4] == 'amb' and st['pts'][2]['gs'] == 220 and st['pts'][2]['gsLock']
    ex = expect(st['pts'], 0, 4, secs('09:45:00'), secs('10:15:00'), 15)
    assert ex['L'] > 0 and sorted(ex['rec']) == [1, 3, 4] and fr.evaluate("() => [...document.querySelectorAll('.lb-amb')].map(e => +e.dataset.leg)") == [1, 3, 4]
    txt = fr.evaluate("() => document.querySelector('#nav-amb .amb-t').textContent")
    assert 'sur les 3 branches' in txt and '(' in txt
    hit(fr.locator('#nav-amb [data-apply="4"]'), touch)
    attendre(fr, "S.points[1].gs !== undefined", 'les vitesses écrites', lu='S.points[1].gs')
    after = fr.evaluate(READ)['pts']
    sp = round(220 * ex['f'])
    assert [p['gs'] for p in after[1:5]] == [sp, 220, sp, sp] and after[2]['gsLock'] is True and not any(p['gsLock'] for k, p in enumerate(after) if k != 2)
    # kt : l'entier de l'unité affichée (la règle de readSpeed), sur une route neuve de deux tronçons
    fr.evaluate("() => { S.units = { distance: 'nm', altitude: 'ft' }; S.points.forEach(p => { delete p.gs; delete p.gsLock; delete p.t; delete p.tLock; }); persistState(); renderAll(); }")
    nav_open(fr)
    tm_type(fr, pg, 0, '09:45'); tm_lock(fr, 0); tm_type(fr, pg, 2, '10:04:30'); tm_lock(fr, 2)                       # un premier tronçon 0 → 2
    tm_type(fr, pg, 4, '10:14'); tm_lock(fr, 4)                                                                   # un second 2 → 4
    st = fr.evaluate(READ)
    a1 = expect(st['pts'], 0, 2, secs('09:45:00'), secs('10:04:30'), 15)
    a2 = expect(st['pts'], 2, 4, secs('10:04:30'), secs('10:14:00'), 15)
    amb = fr.evaluate("() => timing().h.amb.map(r => r ? r.a : null)")
    assert amb == [None, None, 0, None, 2, None]
    first = fr.evaluate("() => [...document.querySelectorAll('#nav-amb [data-apply]')].map(e => +e.dataset.apply)")
    assert first == [2, 4]
    hit(fr.locator('#nav-amb [data-apply="%d"]' % first[0]), touch)                                               # « Appliquer » d'un seul tronçon
    attendre(fr, "S.points.some(p => p.gs !== undefined)", 'des vitesses écrites', lu='S.points.map(p => p.gs)')
    FOC = "() => { const a = document.activeElement; return a ? [a.id, a.dataset.apply || null] : null; }"
    assert fr.evaluate(FOC) == ['', str(first[1])]                                                                    # le focus va à « Appliquer » du bandeau suivant
    written = fr.evaluate("() => S.points.map(p => p.gs === undefined ? null : p.gs)")
    lo, hi = (1, 2) if first[0] == 2 else (3, 4)
    other = (3, 4) if first[0] == 2 else (1, 2)
    exp = (a1 if first[0] == 2 else a2)['rec']
    for j in range(lo, hi + 1):
        n = round(exp[j] / 1.852)
        assert abs(written[j] - round(n * 1.852, 4)) < 1e-9 and round(written[j] / 1.852) == n, (j, written, exp)            # kt entiers, stockés en km/h
    assert all(written[j] is None for j in other)                                                                   # l'autre tronçon ne bouge pas
    assert fr.evaluate("() => document.querySelectorAll('#pts .pt-row.pts')[%d].querySelector('[data-k=gs]').value" % lo) == str(round(exp[lo] / 1.852))
    pg.keyboard.press('Enter')                                                                                      # « Appliquer » du dernier bandeau, au clavier : il n'en reste plus, le focus va au champ de la marge
    attendre(fr, "document.querySelectorAll('#nav-amb [data-apply]').length === 0", 'plus de bandeau orange')
    assert fr.evaluate(FOC) == ['mg-def', None]
    assert pg.errs == []


@needs_pw
def test_a_red_stretch_tells_its_cause_and_the_export_asks_only_for_red_not_for_orange(browser):
    pg = shell(browser, 1280, 800)
    fr = open_rp(pg)
    lock_two(fr, pg)
    fr.evaluate("""() => { window.__shots = []; window.html2canvas = function () { window.__shots.push({ lb: document.querySelectorAll('.lb-amb').length, lab: document.querySelectorAll('.amb-lab').length, amb: document.querySelectorAll('.wp-time.amb').length,
      times: [...document.querySelectorAll('.wp-time')].map(e => e.textContent + '|' + e.querySelectorAll('svg').length), stroke: [...document.querySelectorAll('.lb-bg')].map(e => getComputedStyle(e).stroke) }); return Promise.reject(new Error('banc')); }; }""")
    cadre_export(fr, True)
    assert fr.evaluate("() => document.querySelectorAll('.amb-lab').length") == 4
    fr.evaluate('() => { expGo(); }')                                                                              # orange : aucune confirmation
    attendre(fr, 'window.__shots.length === 1', "le rendu parti sans question")
    assert fr.evaluate("() => (c => !c || c.hidden)(document.getElementById('ui-confirm'))") is True
    shot = fr.evaluate('() => window.__shots[0]')
    assert shot['lb'] == 0 and shot['lab'] == 0 and shot['amb'] == 0 and ORANGE_LINE not in shot['stroke'] and all('⚠' not in x for x in shot['times'])
    attendre(fr, 'EXP.busy === false', "l'export terminé (le banc l'a fait échouer)")
    assert fr.evaluate("() => [document.querySelectorAll('.amb-lab').length, document.querySelectorAll('.lb-amb').length, document.querySelectorAll('.wp-time.amb').length]") == [4, 4, 1]       # l'écran retrouve son orange
    cadre_export(fr, False)
    # rouge : la cause dit pourquoi ; la confirmation reste pour le rouge
    set_margin(fr, 5)
    assert fr.evaluate("() => [document.getElementById('nav-red').hidden, document.querySelectorAll('#nav-amb .ui-bandeau').length, document.querySelectorAll('.amb-lab').length, document.querySelectorAll('.wp-time.red').length]") == [False, 0, 0, 1]
    assert 'au-delà de la marge de ±5 %' in fr.evaluate("() => document.getElementById('nav-red').textContent")
    cadre_export(fr, True)
    fr.evaluate('() => { expGo(); }')
    attendre(fr, "!document.getElementById('ui-confirm').hidden", 'la confirmation du rouge affichée')
    fr.locator('#ui-confirm-cancel').click()
    attendre(fr, "document.getElementById('ui-confirm').hidden", 'la confirmation fermée')
    assert fr.evaluate('() => window.__shots.length') == 1
    assert pg.errs == []


@needs_pw
@pytest.mark.parametrize('w,h,touch', SIZES)
def test_datacard_orange_equals_the_route_planner_and_the_route_is_read_back_with_its_locks(browser, w, h, touch):
    pg = shell(browser, w, h, touch=touch)
    fr = open_rp(pg)
    lock_two(fr, pg)
    lock_speed(fr, 3, touch)                                                                                     # une vitesse verrouillée suit la route jusqu'au DG
    nav_open(fr)
    set_margin(fr, 20)
    rp = fr.evaluate("() => ({ secs: timing().h.t.map(x => rtmClock(x)), mins: timing().h.t.map(x => rtmClockMin(x)), amb: timing().h.amb.map(r => !!r), red: timing().h.red.map(r => !!r), margin: S.speedMargin })")
    assert rp['margin'] == 20 and rp['amb'] == [False, False, False, False, True, False]
    dg = open_dg(pg)
    attendre(dg, "dgRTcalc(curCard()).tm.has === true", 'la route a des heures')
    dg_pick(dg, 3, 5)                                                                                            # TOT : le point 4
    d = dg.evaluate("""() => { const rt = dgRTcalc(curCard()); return { secs: rt.tm.t.map(x => rtmClock(x)), amb: rt.tm.amb.map(r => !!r), red: rt.tm.red.map(r => !!r), margin: rt.margin, lock: rt.pts.map(p => p.gsLock === true), gs: rt.pts.map(p => p.gs === undefined ? null : p.gs),
      pastilles: [...document.querySelectorAll('#preview .tm-amb')].map(e => e.textContent), bg: getComputedStyle(document.querySelector('#preview .tm-amb')).backgroundColor, rouges: document.querySelectorAll('#preview .tm-red').length,
      ban: [...document.querySelectorAll('#editor [data-nav-amb]')].map(e => e.className + '|' + e.textContent), banRed: document.querySelectorAll('#editor [data-nav-red]').length, ambin: document.querySelectorAll('#editor .tm-ambin').length,
      tos: [...document.querySelectorAll('#preview table.dc-nav tbody tr')].map(r => r.children[r.children.length - 2].textContent).slice(0, 6) }; }""")
    assert d['secs'] == rp['secs'] and d['amb'] == rp['amb'] and d['red'] == rp['red'] and d['margin'] == 20                      # les heures égales à la seconde, l'orange compris
    assert d['lock'] == [False, False, False, True, False, False] and d['gs'][3] == 220                              # gsLock et p.gs suivent la route jusqu'au DG
    assert d['tos'] == rp['mins'] and d['pastilles'] == ['10:14:00', '10:14'] and d['bg'] == ORANGE and d['rouges'] == 0
    names = dg.evaluate("() => dgRTcalc(curCard()).pts.map(p => p.name)")
    f = expect(fr.evaluate(READ)['pts'], 0, 4, secs('09:45:00'), secs('10:14:00'), 20)['f']
    assert len(d['ban']) == 1 and 'ui-bandeau amb' in d['ban'][0] and 'err' not in d['ban'][0].split('|')[0] and d['banRed'] == 0 and d['ambin'] >= 2
    assert d['ban'][0].split('|', 1)[1] == '%s à 10:14:00 : à tenir par les vitesses d’%s à %s (%s) ; appliquez-les au Route Planner.' % (names[4], names[0], names[4], pct(f, True))
    assert '⚠' not in d['pastilles'][0] + d['pastilles'][1]
    # les exports : ni pastille, ni classe orange, aucune confirmation
    html = dg.evaluate("() => allExportPages().map(p => p.html).join('')")
    assert 'tm-amb' not in html and 'tm-ambin' not in html and '10:14:00' in html and '>10:14<' in html
    assert dg.evaluate("() => dgExportRedOk({ page: 'all' })") is True and dg.evaluate("() => (c => !c || c.hidden)(document.getElementById('ui-confirm'))") is True
    dg.evaluate("() => { DGX.print = null; fillPrintRoot(); }")
    pr = dg.evaluate("() => document.getElementById('print-root').innerHTML")
    assert 'tm-amb' not in pr and '10:14:00' in pr
    dg.evaluate('() => clearPrintRoot()')
    # la route relue : gsLock et speedMargin suivent (Ouvrir un travail : parseRoute ; la copie de la route : routeFromObject et dgEnterRoute au DG) ; aucun gsLock au point 0
    back = dg.evaluate("""() => { const o = { format: ROUTE_FORMAT, name: 'x', speedMargin: 33, points: [{ name: 'A', lat: 1, lon: 2, gs: 250, gsLock: true }, { name: 'B', lat: 1, lon: 3, gs: 250, gsLock: true }, { name: 'C', lat: 1, lon: 4, gsLock: true }, { name: 'D', lat: 1, lon: 5, gs: -3, gsLock: true }] };
      return routeFromObject(o).points.map(p => [p.gs === undefined ? null : p.gs, p.gsLock === true]); }""")
    assert back == [[None, False], [250, True], [None, False], [None, False]]
    fr2 = open_rp(pg)
    rd = fr2.evaluate("""() => { const o = JSON.parse(JSON.stringify(S)); o.speedMargin = 33; o.points[0].gsLock = true; o.points[1].gsLock = true; o.points[1].gs = 200; o.points[2].gsLock = true; delete o.points[2].gs;
      const r = parseRoute(o).route, bad = parseRoute(Object.assign(JSON.parse(JSON.stringify(S)), { speedMargin: 51 })).route, bad2 = parseRoute(Object.assign(JSON.parse(JSON.stringify(S)), { speedMargin: 2.5 })).route, none = parseRoute(Object.assign(JSON.parse(JSON.stringify(S)), { speedMargin: undefined })).route;
      return { m: r.speedMargin, locks: r.points.map(p => p.gsLock === true), mm: [bad.speedMargin, bad2.speedMargin, none.speedMargin], kept: r.points[3].gsLock === true && r.points[3].gs === 220 }; }""")
    assert rd['m'] == 33 and rd['locks'] == [False, True, False, True, False, False] and rd['mm'] == [15, 15, 15] and rd['kept']
    assert pg.errs == []


@needs_pw
def test_apply_caps_the_recommended_speed_at_the_input_limit(browser):
    pg = shell(browser, 1280, 800)
    fr = open_rp(pg)
    nav_open(fr)
    fr.locator('#gs-def').fill('1900')
    attendre(fr, 'S.groundSpeed === 1900', 'la vitesse de la route à 1900', lu='S.groundSpeed')
    tm_type(fr, pg, 0, '09:00'); tm_lock(fr, 0); tm_type(fr, pg, 4, '09:03:15'); tm_lock(fr, 4)                    # +12,6 % : la vitesse recommandée (2 139) dépasse 2 000
    attendre(fr, "timing().h.amb[4] !== null", 'le tronçon orange', lu='timing().h.amb[4]')
    assert fr.evaluate("() => timing().h.legs[1].rec") > 2000
    hit(fr.locator('#nav-amb [data-apply="4"]'), False)
    attendre(fr, "S.points[1].gs !== undefined", 'les vitesses écrites', lu='S.points[1].gs')
    assert fr.evaluate("() => S.points.map(p => p.gs === undefined ? null : p.gs)") == [None, 2000, 2000, 2000, 2000, None]      # plafonnée comme une saisie
    assert pg.errs == []


@needs_pw
@pytest.mark.parametrize('how', ['up', 'remove'])
def test_datacard_a_point_that_arrives_at_rank_zero_loses_its_speed_and_its_padlock(browser, how):
    pg = shell(browser, 1280, 800)
    fr = open_rp(pg)
    lock_speed(fr, 1, False)                                                                                        # la branche qui arrive au point 1 : 220, verrouillée
    dg = open_dg(pg)
    attendre(dg, "dgRouteInfo(curCard()).state === 'linked'", 'la carte suit la route', lu='dgRouteInfo(curCard()).state')
    GS = "() => rwReadState().points.map(p => [p.name, p.gs === undefined ? null : p.gs, p.gsLock === true])"
    before = dg.evaluate(GS)
    assert before[0][1:] == [None, False] and before[1][1:] == [220, True]
    if how == 'up':
        dg.evaluate("() => dgNavAct(curCard(), 'up', 1)")                                                           # le point 1 passe au rang 0
    else:
        dg.evaluate("() => dgNavAct(curCard(), 'remove', 0)")                                                       # le point 0 part : le point 1 devient le rang 0
        dg.locator('#ui-confirm button.danger').click()
    attendre(dg, "rwReadState().points[0].name === arg", 'le point 1 au rang 0', arg=before[1][0], lu='rwReadState().points.map(p => p.name)')
    assert dg.evaluate("() => rwMinimalState(null, null)")['speedMargin'] == 15                                      # l'état minimal que le DG écrit sans Route Planner porte la marge par défaut
    after = dg.evaluate(GS)
    assert after[0][0] == before[1][0] and after[0][1:] == [None, False]                                              # ni vitesse ni verrou au rang 0
    assert pg.errs == []


DG_WRITES_POINT_3 = """() => { const set = rwReadSet(); const r = rwUpdateRoute(set.routes[set.active].rid, route => { route.points[3].t = '10:12:30'; route.points[3].tLock = true; }); return r.ok; }"""
RP_POINTS_STORED = "() => JSON.parse(localStorage.getItem('route_state_v1')).points.map(p => [p.t || null, p.tLock === true])"
DEAF = "() => { window.rpReloadSoon = () => {}; }"       # le cadre ne reçoit pas l'évènement « storage » (le navigateur ne le livre pas toujours à un cadre du shell) : ce que son écouteur ferait est supprimé


@needs_pw
def test_the_route_planner_reads_back_what_the_datacard_wrote_when_it_is_shown_again_even_without_a_storage_event(browser):
    pg = shell(browser, 1280, 860)
    fr = open_rp(pg)
    nav_open(fr)
    tm_type(fr, pg, 4, '10:17'); tm_lock(fr, 4)
    fr.evaluate(DEAF)
    dg = open_dg(pg)
    assert dg.evaluate(DG_WRITES_POINT_3) is True
    pg.wait_for_timeout(400)                                                                                       # le temps qu'un évènement « storage » aurait mis (150 ms) : il ne vient pas, le Route Planner caché n'a rien relu
    assert fr.evaluate("() => S.points.map(p => [p.t || null, p.tLock === true])") == [[None, False]] * 4 + [['10:17:00', True], [None, False]]
    fr = open_rp(pg)                                                                                               # il redevient visible : il se relit
    attendre(fr, "S.points[3].tLock === true", 'le Route Planner a relu la route du Datacard Generator', lu="S.points.map(p => [p.t || null, p.tLock === true])")
    assert fr.evaluate("() => S.points.map(p => [p.t || null, p.tLock === true])") == [[None, False]] * 3 + [['10:12:30', True], ['10:17:00', True], [None, False]]
    assert pg.errs == []


@needs_pw
def test_the_route_planner_never_overwrites_a_datacard_write_it_did_not_hear_about(browser):
    pg = shell(browser, 1280, 860)
    fr = open_rp(pg)
    nav_open(fr)
    tm_type(fr, pg, 4, '10:17'); tm_lock(fr, 4)
    fr.evaluate(DEAF)
    dg = open_dg(pg)
    assert dg.evaluate(DG_WRITES_POINT_3) is True
    # le Route Planner, caché et sourd, écrit (le nom de la route) : il relit d'abord, rejoue sa seule saisie, puis écrit ; l'heure du point 3 posée au Datacard Generator reste
    fr.evaluate("() => { S.name = 'AUTRE'; persistState(); }")
    assert dg.evaluate(RP_POINTS_STORED) == [[None, False]] * 3 + [['10:12:30', True], ['10:17:00', True], [None, False]]
    assert fr.evaluate("() => [S.name, S.points.map(p => [p.t || null, p.tLock === true])]") == ['AUTRE'] + [[[None, False]] * 3 + [['10:12:30', True], ['10:17:00', True], [None, False]]]
    assert fr.evaluate("() => JSON.parse(localStorage.getItem('route_state_v1')).name") == 'AUTRE'
    assert pg.errs == []
