"""Les virages au rayon du Route Planner : l'inclinaison d'une route (Aucun, 15°, 30°, 45°), le rayon et l'anticipation de chaque virage, l'arc et la ligne du tableau.
Sans navigateur (node, sur le bloc extrait de route_turns_block.build_block()) : la règle de calcul sur un petit jeu de points écrit ici (des points de l'équateur : l'est et le nord y sont des droites de la projection et un mètre au sol
y vaut un mètre projeté ; la projection est refaite ici à part) : virage à droite, à gauche, moins de 1°, 179° et plus, une branche qui déborde, le premier et le dernier point, la latitude.
Au navigateur (le shell construit, chromium, aucun réseau ; 1 280 × 800 à la souris et 412 × 915 au doigt) : le réglage, sa note et son reflet ; la ligne du tableau d'un virage qui tient et d'un trop large (FR, EN, km, NM) ; le réglage qui suit
une route relue, une route nouvelle et une copie ; réglé sur Aucun, rien de plus que la base. Les contrôles passent par le DOM, jamais par une capture."""
import json
import math
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_route_heures import CHROMIUM, geom, needs_node, needs_pw, nav_open, open_rp, shell  # noqa: E402
from test_route_heures import browser  # noqa: E402,F401  (la fixture du module)
from banc_attente import attendre  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from route_turns_block import build_block  # noqa: E402

RE = 6378137.0
G = 9.80665
SIZES = [(1280, 800, False), (412, 915, True)]
NBSP = ' '

# La route d'essai du navigateur : sept points, la vitesse par défaut 220 km/h, OBJ et BREAK à 200
MAQ = [
    ('DÉPART', 33.745, 36.76, 0, 'AGL', None), ('COL', 33.79, 36.44, 1900, 'MSL', None), ('IP', 33.80, 36.10, 30, 'AGL', None),
    ('OBJ', 33.862, 36.035, 30, 'AGL', 200), ('BREAK', 33.8713, 36.0536, 30, 'AGL', 200), ('SORTIE', 33.70, 36.20, 30, 'AGL', None),
    ('RETOUR', 33.745, 36.76, 0, 'AGL', None)]


def maq_route(**extra):
    r = {'format': 'dcs-route-v1', 'name': 'ESSAI', 'theatre': 'Syria', 'groundSpeed': 220, 'points': []}
    for n, la, lo, al, ar, gs in MAQ:
        p = {'name': n, 'lat': la, 'lon': lo, 'alt': al, 'altRef': ar}
        if gs is not None:
            p['gs'] = gs
        r['points'].append(p)
    r.update(extra)
    return r


# ---------------------------------------------------------------------------------------------------- le calcul, refait ici à part
def merc(lat, lon):
    return RE * math.radians(lon), RE * math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))


def py_turns(pts, speeds, bank):
    """Les virages d'une route, d'après les mots de la règle (sans le bloc) : [None | { delta, R, d, wide }]"""
    n = len(pts)
    P = [merc(a, b) for a, b in pts]
    L = [0] + [math.hypot(P[j][0] - P[j - 1][0], P[j][1] - P[j - 1][1]) for j in range(1, n)]
    out = [None] * n
    for i in range(1, n - 1):
        u1 = ((P[i][0] - P[i - 1][0]) / L[i], (P[i][1] - P[i - 1][1]) / L[i])
        u2 = ((P[i + 1][0] - P[i][0]) / L[i + 1], (P[i + 1][1] - P[i][1]) / L[i + 1])
        delta = math.degrees(math.atan2(u1[0] * u2[1] - u1[1] * u2[0], u1[0] * u2[0] + u1[1] * u2[1]))
        v = speeds[i] / 3.6
        R = v * v / (G * math.tan(math.radians(bank)))
        d = R * math.tan(math.radians(min(abs(delta), 179.9)) / 2)
        k = 1 / math.cos(math.radians(pts[i][0]))
        out[i] = {'delta': delta, 'R': R, 'd': d, 'k': k, 'turn': abs(delta) >= 1, 'wide': abs(delta) >= 179}
    for j in range(1, n):
        a, b = out[j - 1], out[j]
        s = (a['d'] * a['k'] if a and a['turn'] else 0) + (b['d'] * b['k'] if b and b['turn'] else 0)
        if s > L[j]:
            for o in (a, b):
                if o and o['turn']:
                    o['wide'] = True
    return out


def node_turns(pts, speeds, bank, extra=''):
    js = build_block() + '\nconst o = rtnCompute(%s, %s, %s); const r = o.map(x => x && Object.assign({}, x, { arc: rtnArc(x) }));\n%s\nprocess.stdout.write(JSON.stringify(r));\n' % (
        json.dumps([{'lat': a, 'lon': b} for a, b in pts]), json.dumps(speeds), bank, extra)
    r = subprocess.run(['node', '-e', js], capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


def v_ms(kmh):
    return kmh / 3.6


def radius(kmh, bank):
    return v_ms(kmh) ** 2 / (G * math.tan(math.radians(bank)))


L_DEG = 0.2                                         # 22,2 km de l'équateur : de la place pour un virage de 660 m
EQ_LEFT = [(0, 0), (0, L_DEG), (L_DEG, L_DEG)]       # à l'est, puis au nord : à gauche de 90°
EQ_RIGHT = [(0, 0), (0, L_DEG), (-L_DEG, L_DEG)]     # à l'est, puis au sud : à droite de 90°


@needs_node
@pytest.mark.parametrize('bank', [15, 30, 45])
def test_a_left_and_a_right_turn_have_the_radius_and_the_lead_of_the_bank(bank):
    R = radius(220, bank)
    for pts, side, sign in ((EQ_LEFT, 'left', 1), (EQ_RIGHT, 'right', -1)):
        r = node_turns(pts, [None, 220, 220], bank)
        assert r[0] is None and r[2] is None                                           # ni le premier ni le dernier point
        o = r[1]
        assert o['turn'] is True and o['side'] == side and o['fits'] is True and o['wide'] is False
        assert abs(o['delta'] - sign * 90) < 1e-6 and abs(o['R'] - R) < 1e-6 and abs(o['d'] - R) < 1e-6      # tan(45°) = 1 : l'anticipation vaut le rayon
        assert o['k'] == 1
        # l'arc : de T1 (R avant le point sur la branche qui arrive) à T2 (R après, sur celle qui part), tangent aux deux branches, du côté du virage
        x1, y1 = merc(*o['t1']); x2, y2 = merc(*o['t2']); cx, cy = merc(*o['c'])
        bx, by = merc(0, L_DEG)
        assert abs(x1 - (bx - R)) < 1e-3 and abs(y1 - by) < 1e-3
        assert abs(x2 - bx) < 1e-3 and abs(y2 - (by + sign * R)) < 1e-3
        assert abs(cx - (bx - R)) < 1e-3 and abs(cy - (by + sign * R)) < 1e-3          # le centre est du côté du virage
        arc = [merc(*q) for q in o['arc']]
        assert len(arc) == 31 and all(abs(math.hypot(x - cx, y - cy) - R) < 1e-3 for x, y in arc)       # 90° : un segment tous les 3° : 30 segments
        assert abs(arc[0][0] - x1) < 1e-6 and abs(arc[-1][1] - y2) < 1e-6
        mid = arc[15]
        assert abs(math.hypot(mid[0] - cx, mid[1] - cy) - R) < 1e-3                    # le milieu à R du centre


@needs_node
def test_the_radius_follows_the_speed_of_the_leg_that_arrives_and_the_bank():
    r = node_turns(EQ_LEFT, [None, 300, 100], 30)
    assert abs(r[1]['R'] - radius(300, 30)) < 1e-6                                     # la vitesse de la branche qui arrive (celle du point 1), pas celle de la suivante
    assert abs(radius(220, 30) - 659.6) < 0.5 and abs(radius(220, 15) - 1420.9) < 0.5 and abs(radius(220, 45) - 380.8) < 0.5
    assert node_turns(EQ_LEFT, [None, 220, 220], 0) == [None, None, None]              # sans inclinaison : rien
    assert node_turns(EQ_LEFT, [None, 220, 220], 20) == [None, None, None]             # une inclinaison inconnue vaut Aucun
    assert node_turns(EQ_LEFT[:2], [None, 220], 30) == [None, None]                    # deux points : pas de virage


@needs_node
def test_under_one_degree_is_no_turn_and_179_degrees_or_more_is_too_wide_at_once():
    dy = L_DEG * math.tan(math.radians(0.5))
    r = node_turns([(0, 0), (0, L_DEG), (dy, 2 * L_DEG)], [None, 220, 220], 30)[1]      # 0,5° à gauche
    assert r['turn'] is False and r['d'] == 0 and r['arc'] == [] and r['wide'] is False and abs(r['delta'] - 0.5) < 1e-3
    r = node_turns([(0, 0), (0, L_DEG), (-dy, 2 * L_DEG)], [None, 220, 220], 30)[1]     # 0,5° à droite
    assert r['turn'] is False and r['side'] == '' and r['arc'] == []
    r = node_turns([(0, 0), (0, L_DEG), (dy * 2.01, 2 * L_DEG)], [None, 220, 220], 30)[1]          # un peu plus de 1° : un virage
    assert r['turn'] is True
    # des branches de 222 km : de la place pour 150 km d'anticipation ; 178,5° tient, 179,5° est trop large d'office
    big = 2.0
    dy1 = big * math.tan(math.radians(1.5))
    r = node_turns([(0, 0), (0, big), (dy1, 0)], [None, 220, 220], 30)[1]
    assert abs(abs(r['delta']) - 178.5) < 0.01 and r['fits'] is True and r['wide'] is False and len(r['arc']) > 4
    dy2 = big * math.tan(math.radians(0.5))
    r = node_turns([(0, 0), (0, big), (dy2, 0)], [None, 220, 220], 30)[1]
    assert abs(abs(r['delta']) - 179.5) < 0.01 and r['turn'] is True and r['fits'] is False and r['wide'] is True and r['arc'] == [] and r['t1'] is None
    assert math.isfinite(r['d']) and r['d'] < 1e7                                      # l'anticipation reste un nombre lisible (179,9° au plus)


@needs_node
def test_a_leg_that_overflows_makes_the_turns_at_both_its_ends_too_wide_and_a_turn_that_has_room_stays():
    # B → C : 1,1 km ; un virage de 90° à B et un à C prennent chacun 660 m à 30° : 1 320 m > 1 112 m
    pts = [(0, 0), (0, 0.01), (0.01, 0.01), (0.01, 0.2)]
    r = node_turns(pts, [None, 220, 220, 220], 30)
    assert r[1]['side'] == 'left' and r[2]['side'] == 'right'
    assert r[1]['wide'] is True and r[2]['wide'] is True and r[1]['arc'] == [] and r[2]['arc'] == []
    r = node_turns(pts, [None, 220, 220, 220], 45)                                     # 381 m chacun : 762 m ≤ 1 112 m, ils tiennent tous les deux
    assert r[1]['wide'] is False and r[2]['wide'] is False and len(r[1]['arc']) == 31 and len(r[2]['arc']) == 31
    # A → B : 835 m ; le virage de B prend 660 m (C est droit : d = 0 ne compte pas) : il tient ; à 556 m, il ne tient plus
    pts = [(0, 0), (0, 0.0075), (0.2, 0.0075), (0.4, 0.0075)]
    r = node_turns(pts, [None, 220, 220, 220], 30)
    assert r[1]['wide'] is False and r[2]['turn'] is False and r[2]['wide'] is False and len(r[1]['arc']) > 4
    pts = [(0, 0), (0, 0.005), (0.2, 0.005)]
    assert node_turns(pts, [None, 220, 220], 30)[1]['wide'] is True                   # A → B : 556 m < 660 m


@needs_node
def test_the_geometry_is_worked_in_the_projection_so_a_metre_on_the_ground_is_secant_latitude_projected_metres():
    # à 60° de latitude, un mètre au sol vaut 2 m projetés : l'arc et son rayon se tracent à l'échelle projetée, l'anticipation au sol reste d
    la = 60.0
    pts = [(la, 10.0), (la, 10.05), (la + 0.05, 10.05)]                                # à l'est, puis (en projection) vers le nord
    r = node_turns(pts, [None, 220, 220], 30)[1]
    R = radius(220, 30)
    assert abs(r['k'] - 2) < 1e-9 and r['turn'] is True and abs(abs(r['delta']) - 90) < 1e-6
    bx, by = merc(*pts[1])
    x1, y1 = merc(*r['t1'])
    assert abs(math.hypot(x1 - bx, y1 - by) - R * 2) < 1e-3                            # d·k projetés
    cx, cy = merc(*r['c'])
    arc = [merc(*q) for q in r['arc']]
    assert all(abs(math.hypot(x - cx, y - cy) - R * 2) < 1e-3 for x, y in arc)         # rayon projeté R·k
    # sur le sol, les extrémités sont à d (≈ R) du point : haversine, au pour cent près
    def hav(a, b):
        p1, p2, dl = math.radians(a[0]), math.radians(b[0]), math.radians(b[1] - a[1])
        h = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
        return 2 * 6371008.8 * math.asin(math.sqrt(h))
    assert abs(hav(pts[1], r['t1']) / R - 1) < 0.01 and abs(hav(pts[1], r['t2']) / R - 1) < 0.01


@needs_node
def test_the_block_agrees_with_the_rule_written_apart_on_the_route_of_the_browser_tests():
    pts = [(a, b) for _n, a, b, *_ in MAQ]
    sp = [None] + [m[5] or 220 for m in MAQ[1:]]
    for bank in (15, 30, 45):
        r, w = node_turns(pts, sp, bank), py_turns(pts, sp, bank)
        for i in range(1, len(MAQ) - 1):
            assert abs(r[i]['delta'] - w[i]['delta']) < 1e-9 and abs(r[i]['R'] - w[i]['R']) < 1e-6 and abs(r[i]['d'] - w[i]['d']) < 1e-6 and r[i]['wide'] is w[i]['wide'], (bank, i)
    r30 = node_turns(pts, sp, 30)
    assert round(abs(r30[3]['delta'])) == 100 and round(r30[3]['R']) == 545 and round(r30[3]['d']) == 650                # le repère : à 30°, OBJ 100°, R 545 m, d 650 m
    assert [i for i in range(1, 6) if node_turns(pts, sp, 15)[i]['wide']] == [3, 4]                                      # à 15°, OBJ et BREAK sont trop larges
    assert not any(o['wide'] for o in r30[1:6]) and not any(o['wide'] for o in node_turns(pts, sp, 45)[1:6])


# ---------------------------------------------------------------------------------------------------- le navigateur
def fmt_m(m, fr, nm=False):
    if nm:
        s = '%.2f' % (m / 1852)
        return (s.replace('.', ',') if fr else s) + ' NM'
    r = int(math.floor(m / 10 + 0.5)) * 10
    return format(r, ',').replace(',', NBSP if fr else ',') + ' m'


def expected_rows(bank, fr, nm=False, pts=None, speeds=None, names=None):
    """Les lignes `tr.nav-turn` attendues, par indice de point : (texte, trop large)"""
    pts = pts or [(a, b) for _n, a, b, *_ in MAQ]
    speeds = speeds or ([None] + [m[5] or 220 for m in MAQ[1:]])
    names = names or [m[0] for m in MAQ]
    out = {}
    for i, o in enumerate(py_turns(pts, speeds, bank)):
        if not o or not o['turn'] or abs(o['delta']) < 10:
            continue
        a, left = int(math.floor(abs(o['delta']) + 0.5)), o['delta'] > 0
        r, d = fmt_m(o['R'], fr, nm), fmt_m(o['d'], fr, nm)
        if o['wide']:
            side = ('à gauche' if left else 'à droite') if fr else ('left' if left else 'right')
            txt = ('⚠ virage de %d° %s%s: %s d’anticipation, la branche ne suffit pas' % (a, side, NBSP, d)) if fr else '⚠ %d° %s turn: needs %s lead, the leg is too short' % (a, side, d)
        elif fr:
            txt = '%s virage de %d° %s · rayon %s · commencer %s avant %s' % ('↰' if left else '↱', a, 'à gauche' if left else 'à droite', r, d, names[i])
        else:
            txt = '%s %d° %s turn · radius %s · start %s before %s' % ('↰' if left else '↱', a, 'left' if left else 'right', r, d, names[i])
        out[i] = (txt, o['wide'])
    return out


READ_ROWS = """() => [...document.querySelectorAll('#nav-body tr')].map((tr, k, all) => ({ cls: tr.className, text: tr.textContent.trim(), cells: tr.children.length, span: tr.children.length > 1 ? tr.children[1].colSpan : 0,
  prev: k > 0 ? all[k - 1].className : '', n: tr.querySelector('td.n') ? tr.querySelector('td.n').textContent : null }))"""


def load_route(fr, route):
    """Ouvre la route par l'interface de lecture de fichier du Route Planner, et attend qu'elle soit celle de la route en cours"""
    fr.set_input_files('#file-open', {'name': 'essai.json', 'mimeType': 'application/json', 'buffer': json.dumps(route).encode()})
    attendre(fr, "S.name === arg && S.points.length === %d" % len(route['points']), 'la route %s ouverte' % route['name'], arg=route['name'], lu='[S.name, S.points.length]')


def pick_bank(fr, bank, touch):
    b = fr.locator('[data-trn="%d"]' % bank)
    b.scroll_into_view_if_needed()
    b.tap() if touch else b.click()
    attendre(fr, 'S.turnBank === arg', "l'inclinaison %d" % bank, arg=bank, lu='S.turnBank')


def rows_after_points(fr):
    return {r['n']: r for r in fr.evaluate(READ_ROWS) if r['n'] is not None}


@needs_pw
@pytest.mark.parametrize('w,h,touch', SIZES)
def test_the_bank_group_its_note_and_its_reflection(browser, w, h, touch):
    pg = shell(browser, w, h, touch=touch)
    fr = open_rp(pg)
    nav_open(fr)
    # le groupe : après « Traits des minutes », dans .nav-set ; quatre boutons ; Aucun d'abord
    g = fr.evaluate("""() => { const set = document.querySelector('.nav-set'), cells = [...set.children], i = cells.findIndex(c => c.querySelector('[data-trn]')), lbl = cells[i].querySelector('.lbl');
      return { n: cells.length, i: i, prev: cells[i - 1].querySelector('.lbl').textContent, lbl: lbl.textContent, aria: cells[i].querySelector('[role=group]').getAttribute('aria-label'),
        btn: [...cells[i].querySelectorAll('[data-trn]')].map(b => [b.dataset.trn, b.textContent, b.getAttribute('aria-pressed'), b.classList.contains('on')]) }; }""")
    assert g['prev'] == 'Traits des minutes' and g['lbl'] == 'Virages (inclinaison)' and g['aria'] == 'Virages (inclinaison)' and g['i'] == g['n'] - 1
    assert g['btn'] == [['0', 'Aucun', 'true', True], ['15', '15°', 'false', False], ['30', '30°', 'false', False], ['45', '45°', 'false', False]]
    note = lambda: fr.evaluate("() => { const n = document.getElementById('trn-note'); return { hidden: n.hidden, shown: n.getClientRects().length > 0, text: n.innerText, warn: !document.getElementById('trn-warn').hidden }; }")
    assert note()['hidden'] is True and note()['shown'] is False
    assert fr.evaluate("() => S.turnBank") == 0
    # la note vient sous celle de la marge
    assert fr.evaluate("() => document.getElementById('mg-note').nextElementSibling.id") == 'trn-note'
    load_route(fr, maq_route())
    pick_bank(fr, 30, touch)
    n = note()
    assert n['shown'] is True and n['warn'] is False and n['text'] == 'Rayon d’après la vitesse sol de la branche qui arrive et l’inclinaison' + NBSP + '; le minutage reste de point à point.'
    assert fr.evaluate("() => [...document.querySelectorAll('[data-trn]')].map(b => b.getAttribute('aria-pressed') + b.classList.contains('on'))") == ['falsefalse', 'falsefalse', 'truetrue', 'falsefalse']
    stored = fr.evaluate("() => JSON.parse(localStorage.getItem('route_state_v1')).turnBank")
    assert stored == 30
    # 15° : deux virages trop larges, dits sur la ligne suivante ; 45° : plus aucun
    pick_bank(fr, 15, touch)
    n = note()
    assert n['warn'] is True and n['text'].split('\n')[-1] == '⚠ 2 virages trop larges pour leur branche, cerclés en orange.' and n['text'].split('\n')[0].startswith('Rayon d’après')
    pick_bank(fr, 45, touch)
    assert note()['warn'] is False
    pick_bank(fr, 0, touch)
    assert note()['hidden'] is True and fr.evaluate("() => JSON.parse(localStorage.getItem('route_state_v1')).turnBank") == 0
    assert pg.errs == []


@needs_pw
def test_the_note_and_the_group_in_english_and_one_wide_turn_is_told_in_the_singular(browser):
    pg = shell(browser, 1280, 800, lang='en')
    fr = open_rp(pg)
    nav_open(fr)
    assert fr.evaluate("() => [document.querySelector('[data-trn=\"0\"]').textContent, document.querySelector('.nav-set [data-trn]').closest('div').querySelector('.lbl').textContent]") == ['None', 'Turns (bank)']
    r = {'format': 'dcs-route-v1', 'name': 'UN SEUL', 'theatre': 'Syria', 'points': [
        {'name': 'A', 'lat': 33.7, 'lon': 36.0}, {'name': 'B', 'lat': 33.7, 'lon': 36.012}, {'name': 'C', 'lat': 33.9, 'lon': 36.012}]}
    pts = [(p['lat'], p['lon']) for p in r['points']]
    assert [i for i, o in enumerate(py_turns(pts, [None, 220, 220], 15)) if o and o['wide']] == [1]          # à 15° : une branche de 1,1 km ne suffit pas à 1 420 m
    assert [i for i, o in enumerate(py_turns(pts, [None, 220, 220], 30)) if o and o['wide']] == []
    load_route(fr, r)
    pick_bank(fr, 15, False)
    assert fr.evaluate("() => document.getElementById('trn-note').innerText").split('\n')[-1] == '⚠ 1 turn too wide for the leg, circled in orange.'
    assert fr.evaluate("() => [...document.querySelectorAll('#nav-body tr.nav-turn')].map(e => e.textContent.trim())") == ['⚠ 90° left turn: needs 1,420 m lead, the leg is too short']
    pick_bank(fr, 30, False)
    assert fr.evaluate("() => document.getElementById('trn-note').innerText") == 'Radius from the incoming leg’s ground speed and the bank angle; timings stay point to point.'
    assert pg.errs == []


@needs_pw
@pytest.mark.parametrize('lang', ['fr', 'en'])
def test_the_table_has_one_line_under_each_turn_of_ten_degrees_or_more_and_none_at_aucun(browser, lang):
    pg = shell(browser, 1280, 800, lang=lang)
    fr = open_rp(pg)
    nav_open(fr)
    load_route(fr, maq_route())
    base = [r['text'] for r in fr.evaluate(READ_ROWS)]
    assert not any('nav-turn' in r['cls'] for r in fr.evaluate(READ_ROWS))
    fr_ = lang == 'fr'
    for bank in (15, 30, 45):
        pick_bank(fr, bank, False)
        rows = fr.evaluate(READ_ROWS)
        want = expected_rows(bank, fr_)
        turns = [(k, r) for k, r in enumerate(rows) if 'nav-turn' in r['cls']]
        assert len(turns) == len(want) == sum(1 for o in py_turns([(a, b) for _n, a, b, *_ in MAQ], [None] + [m[5] or 220 for m in MAQ[1:]], bank) if o and abs(o['delta']) >= 10)
        for (k, r), (i, (txt, bad)) in zip(turns, sorted(want.items())):
            assert r['text'] == txt, (bank, i)
            assert r['cells'] == 2 and r['span'] == 3                                              # une cellule vide, puis les colonnes 2 à 4 fusionnées
            assert ('bad' in r['cls'].split()) is bad
            assert rows[k - 1]['n'] == str(i)                                                      # juste après la ligne du point
        # la ligne d'un virage trop large est dans la pastille orange, les autres n'en ont pas
        pil = fr.evaluate("() => [...document.querySelectorAll('#nav-body tr.nav-turn')].map(tr => { const s = tr.querySelector('.trn-bad'); return s ? getComputedStyle(s).backgroundColor : ''; })")
        assert [bool(p) for p in pil] == [w[1] for _i, w in sorted(want.items())]
        assert all(p in ('', 'rgb(224, 122, 18)') for p in pil)                                    # --mp-sig-orange
    # sur Aucun : le texte du tableau est celui d'avant, ligne pour ligne
    pick_bank(fr, 30, False)
    pick_bank(fr, 0, False)
    assert [r['text'] for r in fr.evaluate(READ_ROWS)] == base
    assert pg.errs == []


@needs_pw
def test_the_distances_are_metres_to_ten_in_km_mode_with_thin_spaces_in_french_and_nautical_miles_in_nm_mode(browser):
    # des branches longues et lentes : un rayon de plus de 1 000 m, pour les milliers
    r = maq_route()
    for lang in ('fr', 'en'):
        pg = shell(browser, 1280, 800, lang=lang)
        fr = open_rp(pg)
        nav_open(fr)
        load_route(fr, r)
        pick_bank(fr, 15, False)
        got = [x['text'] for x in fr.evaluate(READ_ROWS) if 'nav-turn' in x['cls']]
        assert got == [t for _i, (t, _b) in sorted(expected_rows(15, lang == 'fr').items())]
        assert any(('1' + NBSP + '420 m') in x for x in got) if lang == 'fr' else any('1,420 m' in x for x in got)
        # les unités en NM : deux décimales, la virgule par decimal()
        fr.evaluate("() => { S.units.distance = 'nm'; persistState(); renderAll(); }")
        attendre(fr, "S.units.distance === 'nm' && /NM/.test(document.getElementById('nav-total').textContent)", 'la route en NM', lu="document.getElementById('nav-total').textContent")
        got = [x['text'] for x in fr.evaluate(READ_ROWS) if 'nav-turn' in x['cls']]
        assert got == [t for _i, (t, _b) in sorted(expected_rows(15, lang == 'fr', nm=True).items())]
        assert any(('0,77 NM' if lang == 'fr' else '0.77 NM') in x for x in got)
        pg.context.close()


@needs_pw
@pytest.mark.parametrize('w,h,touch', SIZES)
def test_the_setting_follows_a_route_read_a_new_route_and_a_copy_and_a_bad_value_reads_as_aucun(browser, w, h, touch):
    pg = shell(browser, w, h, touch=touch)
    fr = open_rp(pg)
    nav_open(fr)
    # la lecture : toute valeur autre que 0, 15, 30 ou 45 donne Aucun
    got = fr.evaluate("""() => [45, 30, 15, 0, 20, '30', null, undefined, -15, 15.5, 45.0000001, [], {}].map(v => { const o = { format: FORMAT_ID, points: [{ lat: 1, lon: 1 }, { lat: 2, lon: 2 }] }; if (v !== undefined) o.turnBank = v; return parseRoute(o).route.turnBank; })""")
    assert got == [45, 30, 15, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    assert fr.evaluate("() => defaultState().turnBank") == 0
    # une route lue dans une route active vide : tout le fichier, le réglage compris
    fr.evaluate("() => { RSET.routes = [blankRoute()]; RSET.active = 0; S.name = ''; S.points = RSET.routes[0].points; S.refs = []; sel = -1; persistState(); renderAll(); }")
    load_route(fr, maq_route(name='UN', turnBank=45))
    assert fr.evaluate("() => [S.turnBank, document.querySelector('[data-trn=\"45\"]').getAttribute('aria-pressed'), RSET.routes.length]") == [45, 'true', 1]
    # une route de plus ouverte d'un fichier : les réglages restent ceux de la route en cours
    load_route(fr, maq_route(name='DEUX', turnBank=15))
    assert fr.evaluate("() => [S.turnBank, RSET.routes.length]") == [45, 2]
    pick_bank(fr, 30, touch)
    # une route nouvelle et une copie reprennent celui de la route en cours
    fr.evaluate("() => addRoute()")
    attendre(fr, 'RSET.routes.length === 3', 'une route nouvelle')
    assert fr.evaluate("() => [S.turnBank, S.points.length]") == [30, 0]
    fr.evaluate("() => activateRoute(0)")
    attendre(fr, "S.name === 'UN'", 'la première route active')
    fr.evaluate("() => duplicateRoute()")
    attendre(fr, 'RSET.routes.length === 4', 'une copie')
    assert fr.evaluate("() => [S.turnBank, S.points.length, document.querySelector('[data-trn=\"30\"]').getAttribute('aria-pressed')]") == [30, 7, 'true']
    # le réglage est enregistré (route_state_v1), et la lecture que fait l'outil à son ouverture (loadState : parseRoute) le rend
    assert fr.evaluate("() => JSON.parse(localStorage.getItem('route_state_v1')).turnBank") == 30
    assert fr.evaluate("() => parseRoute(JSON.parse(localStorage.getItem(KEY_STATE))).route.turnBank") == 30
    assert pg.errs == []


@needs_pw
def test_at_aucun_nothing_is_added_and_at_a_bank_the_arcs_the_dots_and_the_circles_are_the_only_new_layers(browser):
    pg = shell(browser, 1280, 800)
    fr = open_rp(pg)
    nav_open(fr)
    load_route(fr, maq_route())
    cnt = lambda: fr.evaluate("() => ({ n: routeGroup.getLayers().length, turn: routeGroup.getLayers().filter(l => /rp-turn/.test(l.options.className || '')).length, body: document.getElementById('nav-body').textContent, total: document.getElementById('nav-total').textContent })")
    a = cnt()
    assert a['turn'] == 0
    for bank in (15, 30, 45):
        pick_bank(fr, bank, False)
        b = cnt()
        tn = py_turns([(x, y) for _n, x, y, *_ in MAQ], [None] + [m[5] or 220 for m in MAQ[1:]], bank)
        fit = sum(1 for o in tn if o and o['turn'] and not o['wide']); wide = sum(1 for o in tn if o and o['turn'] and o['wide'])
        assert b['turn'] == 3 * fit + wide and b['n'] == a['n'] + b['turn']                         # par virage qui tient : le liseré, le pointillé, le point ; par virage trop large : le cercle
        assert b['total'] == a['total']
    pick_bank(fr, 0, False)
    assert cnt() == a
    # le cercle orange est en pointillé, sans remplissage, de 19 px de rayon, du trait orange de C13 bis
    pick_bank(fr, 15, False)
    c = fr.evaluate("""() => { const l = routeGroup.getLayers().find(x => /rp-turn-bad/.test(x.options.className || '')), e = l.getElement(), cs = getComputedStyle(e);
      return { r: l.getRadius(), dash: l.options.dashArray, w: l.options.weight, fill: l.options.fill, stroke: cs.stroke, sw: cs.strokeWidth }; }""")
    assert c['r'] == 19 and c['dash'] == '6 4' and c['w'] == 3 and c['fill'] is False and c['stroke'] == 'rgb(169, 86, 4)'          # --mp-sig-orange-line
    pick_bank(fr, 30, False)
    d = fr.evaluate("""() => { const ls = routeGroup.getLayers().filter(x => /rp-turn/.test(x.options.className || '')), q = n => ls.filter(x => x.options.className === n);
      const h = q('rp-turn-halo')[0].options, a = q('rp-turn-arc')[0].options, p = q('rp-turn-dot')[0].options;
      return { halo: [h.color, h.weight, h.opacity], arc: [a.weight, a.dashArray, a.color], dot: [p.radius, p.weight, p.color, p.fillColor], black: S.ui.trace }; }""")
    assert d['halo'] == ['#f0e8d6', 5, 0.8] and d['arc'][:2] == [2.4, '5 4'] and d['dot'][:3] == [4, 2, '#f0e8d6'] and d['dot'][3] == d['arc'][2]
    fr.evaluate("() => { S.ui.trace = 'black'; persistState(); drawRoute(); syncControls(); }")
    d = fr.evaluate("() => routeGroup.getLayers().filter(x => /rp-turn-(arc|dot)/.test(x.options.className || '')).map(x => x.options.color + '|' + x.options.fillColor)")
    assert all(x in ('#1f1c16|null', '#f0e8d6|#1f1c16') for x in d), d                          # tracé Noir : l'arc et le point en #1f1c16
    assert pg.errs == []
