"""HQ crée un vol sur sa place (lot vol-parking) : la lecture du départ et des places du paquet, les appareils de la mission qui prennent une place, le plan des places (ordre du paquet, places retenues,
places demandées par les unités d'après), et l'écriture du groupe (TakeOffParking / TakeOffParkingHot, parking des unités) comme pydcs.
Les fonctions sont lues dans dist/dcs_hq.html et jouées par node, avec de faux accessoires (aucun .miz, aucune page) ; données fabriquées."""
import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
HQ = (ROOT / 'dist' / 'dcs_hq.html').read_text(encoding='utf-8')
NODE = shutil.which('node')
pytestmark = pytest.mark.skipif(NODE is None, reason='node absent')


def fn(name):
    i = HQ.index('function %s(' % name)
    j = HQ.index('{', i)
    depth, k = 0, j
    while True:
        c = HQ[k]
        if c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0:
                return HQ[i:k + 1]
        k += 1


def const_line(name):
    m = re.search(r'^const %s = .*$' % name, HQ, re.M)
    assert m, name
    return m.group(0)


PRELUDE = '\n'.join([
    "function t(k) { return k; }",
    "function tf(k) { return [k].concat(Array.prototype.slice.call(arguments, 1)).join('|'); }",
    const_line('PK_STAND_R'), const_line('PK_CALLSIGNS'), const_line('PK_CS_RE'), const_line('DEL_ALL_CATS'), const_line('PK_SPEED_HELI'),
    fn('pkNum'), fn('pkStandOf'), fn('pkDepartureOf'), fn('pkOnStand'), fn('pkStandKey'), fn('pkStandTaken'), fn('pkStandNat'), fn('pkStandPlan'),
    fn('pkNameKey'), fn('pkIsNum'), fn('pkRoutePoint'), fn('pkClean'), fn('pkUnitName'), fn('pkAirStart'), fn('pkGroupFlags'), fn('pkCsOfNode'),
    fn('_astGetKey'), fn('dynNum'), fn('dynStr'), fn('delRoot'), fn('delEachList'), fn('pkMissionScan'), fn('pkBuildGroup'),
    # une arborescence Lua fabriquée : des tables, des nombres et des chaînes, comme le lecteur du .miz les donne
    """function N(v) {
      if (typeof v === 'number') return { kind: 'number', value: v };
      if (typeof v === 'string') return { kind: 'string', value: v };
      return { kind: 'table', entries: Object.keys(v).map(k => ({ key: /^\\d+$/.test(k) ? { kind: 'int', value: Number(k) } : { kind: 'string', value: k }, value: N(v[k]) })) };
    }""",
    "function unitsOf(arr) { const o = {}; arr.forEach((u, i) => { o[i + 1] = u; }); return o; }",
    "function groupsOf(arr) { const o = {}; arr.forEach((g, i) => { o[i + 1] = g; }); return o; }",
    # les accessoires de pkBuildGroup
    "function pkTpl(type) { return { heli: true, width: 4, task_default: 'CAS', radio_frequency: 251, property_defaults: {}, fuel_max: 500, flare: 192, chaff: 0 }; }",
    "function pkSideCountries() { return [{ name: 'Russia', node: N({}) }]; }",
    "function pkCountryCsForm() { return 'number'; }",
    "function pkCallsigns(fl) { return fl.units.map((u, i) => 100 + i); }",
    "function pkWingLivery() { return ''; }",
    "function pkRadioArg() { return ''; }", "function pkChanArg() { return ''; }",
])


def run(body):
    r = subprocess.run([NODE, '-e', PRELUDE + '\n' + body], capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


def test_departure_and_stand_are_read_or_ignored():
    out = run("""
      const st = (n, id, x, y) => ({ parking: n, parking_id: id, x: x, y: y });
      const r = {};
      r.air = pkDepartureOf({ start: 'air', airdromeId: null, stands: [] });
      r.ground = pkDepartureOf({ start: 'ground' });
      r.parking = pkDepartureOf({ start: 'parking', airdromeId: 44, airdrome: 'Akrotiri', x: 1, y: 2, stands: [st(36, 'H1', 10, 20), st(36, 'dup', 0, 0), { parking: 'x' }, null, st(35, 'H2', 11, 21)] });
      r.hot = pkDepartureOf({ start: 'parkingHot', airdromeId: 44, x: 1, y: 2 });                     // sans nom : l'identifiant
      r.junk = [pkDepartureOf(null), pkDepartureOf([]), pkDepartureOf({}), pkDepartureOf({ start: 'fly' }), pkDepartureOf({ start: 'parking', airdromeId: '44', x: 1, y: 2 }), pkDepartureOf({ start: 'parking', airdromeId: 44, x: 1 })];
      r.stand = [pkStandOf(st(36, 'H1', 1, 2)), pkStandOf(null), pkStandOf(st(-1, 'H1', 1, 2)), pkStandOf(st(1.5, 'H1', 1, 2)), pkStandOf({ parking: 1, parking_id: '', x: 1, y: 2 }), pkStandOf({ parking: 1, parking_id: 'A', x: 'a', y: 2 })];
      r.on = [pkOnStand({ dep: r.parking }), pkOnStand({ dep: r.hot }), pkOnStand({ dep: r.air }), pkOnStand({ dep: null })];
      console.log(JSON.stringify(r));
    """)
    assert out['air'] == {'start': 'air'} and out['ground'] == {'start': 'ground'}
    assert out['parking']['airdromeId'] == 44 and out['parking']['airdrome'] == 'Akrotiri'
    assert [s['id'] for s in out['parking']['stands']] == ['H1', 'H2']        # un doublon de parking, une place illisible : écartés
    assert out['hot']['airdrome'] == '44' and out['hot']['start'] == 'parkingHot' and out['hot']['stands'] == []
    assert out['junk'] == [None] * 6                                           # illisible ou absent : le lot A
    assert out['stand'][0] == {'n': 36, 'id': 'H1', 'x': 1, 'y': 2} and out['stand'][1:] == [None] * 5
    assert out['on'] == [True, True, False, False]


def test_mission_scan_reads_aircraft_positions_only():
    out = run("""
      const u = (x, y, extra) => Object.assign({ x: x, y: y, name: 'n' + x, unitId: 1 }, extra || {});
      const mission = N({ coalition: {
        blue: { country: { 1: { name: 'USA',
          plane: { group: groupsOf([{ groupId: 1, name: 'P', units: unitsOf([u(1, 1, { skill: 'Client' }), u(2, 2)]) }]) },
          helicopter: { group: groupsOf([{ groupId: 2, name: 'H', units: unitsOf([u(3, 3)]) }]) },
          vehicle: { group: groupsOf([{ groupId: 3, name: 'V', units: unitsOf([u(4, 4)]) }]) },
          static: { group: groupsOf([
            { groupId: 4, name: 'S1', units: unitsOf([u(5, 5, { category: 'Planes' })]) },
            { groupId: 5, name: 'S2', units: unitsOf([u(6, 6, { category: 'Helicopters' })]) },
            { groupId: 6, name: 'S3', units: unitsOf([u(7, 7, { category: 'Fortifications' })]) },
            { groupId: 7, name: 'S4', units: unitsOf([u(8, 8)]) } ]) } } } },
        red: { country: { 1: { name: 'Russia', ship: { group: groupsOf([{ groupId: 8, name: 'B', units: unitsOf([u(9, 9)]) }]) } } } } } });
      const sc = pkMissionScan({ ast: mission });
      console.log(JSON.stringify({ air: sc.air.map(a => a.x).sort((a, b) => a - b), maxG: sc.maxG, units: sc.units.size }));
    """)
    assert out['air'] == [1, 2, 3, 5, 6]       # les unités avion et hélicoptère, les statiques avion et hélicoptère ; ni véhicule, ni navire, ni fortification, ni statique sans catégorie
    assert out['maxG'] == 8 and out['units'] == 9


def test_stand_is_taken_within_ten_meters_of_its_center():
    out = run("""
      const sc = { air: [{ x: 100, y: 100 }] };
      const at = (dx, dy) => pkStandTaken(sc, { x: 100 + dx, y: 100 + dy });
      console.log(JSON.stringify([at(0, 0), at(9.9, 0), at(0, -9.9), at(10, 0), at(7.1, 7.1), at(15, 0)]));
    """)
    assert out == [True, True, True, False, False, False]


STANDS = """
  const S = [['H1', 36, 0, 0], ['H2', 35, 40, 0], ['H3', 34, 0, 60], ['H4', 33, 50, 63.6], ['H5', 32, 200, 0], ['A1', 43, 500, 0]].map(a => ({ id: a[0], n: a[1], x: a[2], y: a[3] }));
  const byId = id => S.find(s => s.id === id);
  const dep = (start) => ({ start: start || 'parking', airdromeId: 44, airdrome: 'Akrotiri', x: 0, y: 0, stands: S.slice() });
  const U = (req, pick) => ({ name: '', type: 'Mi-24P', stand: req ? byId(req) : null, pick: pick === undefined ? null : pick });
  const F = (name, units, o) => Object.assign({ groupName: name, dep: dep(), units: units, create: true, canCreate: true, supBy: null, why: null, whyArgs: [], offer: true, sp: null }, o || {});
  const ids = f => f.sp ? f.sp.map(e => e.chosen && e.chosen.id) : null;
  const seqOf = fs => fs.map(fl => ({ pk: {}, fl: fl }));
"""


def test_plan_keeps_free_places_and_replaces_taken_ones_by_the_nearest_free():
    out = run(STANDS + """
      const sc = { air: [{ x: 0, y: 0 }] };       // un appareil de la mission sur H1
      const a = F('A', [U('H1'), U('H2')]), b = F('B', [U('H3')]);
      pkStandPlan(seqOf([a, b]), sc);
      const r = { a: ids(a), b: ids(b), taken: a.sp.map(e => e.taken), lists: a.sp.map(e => e.cands && e.cands.map(c => [c.s.id, Math.round(c.d)])) };
      console.log(JSON.stringify(r));
    """)
    # A-1 : H1 prise ; les candidates : ni H1 (mission), ni H2 (demandée plus loin), ni H3 (demandée par B) : H4 à 81 m en tête, puis H5 (200 m), A1 (500 m)
    assert out['a'] == ['H4', 'H2'] and out['b'] == ['H3']
    assert out['taken'] == [True, False]
    assert out['lists'][0] == [['H4', 81], ['H5', 200], ['A1', 500]] and out['lists'][1] is None


def test_plan_variant_unchecked_flight_frees_its_places():
    out = run(STANDS + """
      const sc = { air: [{ x: 0, y: 0 }] };
      const a = F('A', [U('H1'), U('H2')]), b = F('B', [U('H3')], { create: false });
      pkStandPlan(seqOf([a, b]), sc);
      console.log(JSON.stringify({ a: ids(a), b: b.sp, first: a.sp[0].cands.map(c => [c.s.id, Math.round(c.d)]) }));
    """)
    assert out['a'] == ['H3', 'H2'] and out['b'] is None            # H3 n'est plus demandée : elle devient la plus proche, à 60 m
    assert out['first'][0] == ['H3', 60]


def test_plan_places_taken_by_earlier_units_and_flights():
    out = run(STANDS + """
      const sc = { air: [] };
      // B demande H1 que A garde (A passe d'abord) ; C n'a pas de place : la plus proche de la base, puis de celle de l'unité d'avant
      const a = F('A', [U('H1')]), b = F('B', [U('H1')]), c = F('C', [U(null), U(null)]);
      pkStandPlan(seqOf([a, b, c]), sc);
      console.log(JSON.stringify({ a: ids(a), b: ids(b), c: ids(c), bt: b.sp[0].taken, cTaken: c.sp.map(e => e.taken), cReq: c.sp.map(e => e.req) }));
    """)
    assert out['a'] == ['H1'] and out['b'] == ['H2'] and out['bt'] is True
    assert out['c'] == ['H3', 'H4']                                  # H1 et H2 retenues plus haut ; de la base : H3 (60 m) ; de H3 : H4 (à 50 m) plutôt que H5
    assert out['cTaken'] == [False, False] and out['cReq'] == [None, None]


def test_plan_user_pick_is_followed_and_recalculated():
    out = run(STANDS + """
      const sc = { air: [{ x: 0, y: 0 }] };
      const a = F('A', [U('H1', 32), U('H2')]), b = F('B', [U('H3')]);
      pkStandPlan(seqOf([a, b]), sc);
      const r1 = ids(a), b1 = ids(b);
      const a2 = F('A', [U('H1', 99), U('H2')]);       // une place qui n'est plus offerte : la plus proche
      pkStandPlan(seqOf([a2]), sc);
      console.log(JSON.stringify({ r1: r1, b1: b1, r2: ids(a2) }));
    """)
    assert out['r1'] == ['H5', 'H2'] and out['b1'] == ['H3']
    assert out['r2'] == ['H3', 'H2']


def test_plan_without_free_stand_refuses_the_flight_and_returns_its_places():
    out = run(STANDS + """
      const sc = { air: S.map(s => ({ x: s.x, y: s.y })) };      // toutes prises
      const a = F('A', [U('H1')]);
      pkStandPlan(seqOf([a]), sc);
      const sc2 = { air: [{ x: 0, y: 0 }] };
      // A garde H2 puis n'a plus rien pour sa 2e unité (sans place) ; son H2 doit revenir à B
      const dd = dep(); dd.stands = [byId('H1'), byId('H2')];
      const p = F('P', [U('H2'), U('H1')], { dep: dd }), q = F('Q', [U('H2')], { dep: dd });
      pkStandPlan(seqOf([p, q]), sc2);
      console.log(JSON.stringify({ why: a.why, args: a.whyArgs, can: a.canCreate, offer: a.offer, chosen: ids(a), p: [p.why, p.canCreate, ids(p)], q: [q.why, q.canCreate, ids(q)] }));
    """)
    assert out['why'] == 'noStand' and out['args'] == ['Akrotiri'] and out['can'] is False and out['offer'] is True and out['chosen'] == [None]
    # P : H2 libre, H1 prise (mission) et aucune autre place : P est refusé ; Q retrouve H2 que P a rendue
    assert out['p'][0] == 'noStand' and out['p'][1] is False
    assert out['q'] == [None, True, ['H2']]


def test_plan_ignores_what_is_not_a_flight_to_create_on_a_stand():
    out = run(STANDS + """
      const sc = { air: [] };
      const air = F('Air', [U('H1')], { dep: { start: 'air' } });
      const lotA = F('LotA', [U('H1')], { dep: null });
      const off = F('Off', [U('H1')], { create: false });
      const sup = F('Sup', [U('H1')], { supBy: {} });
      const bad = F('Bad', [U('H1')], { canCreate: false });
      const ok = F('Ok', [U('H1')]);
      pkStandPlan(seqOf([air, lotA, off, sup, bad, ok]), sc);
      console.log(JSON.stringify({ sp: [air, lotA, off, sup, bad].map(f => f.sp), ok: ids(ok) }));
    """)
    assert out['sp'] == [None] * 5 and out['ok'] == ['H1']      # aucun d'eux ne retient H1


# ----- l'écriture -----
BUILD = """
  const fl = (o) => Object.assign({ groupName: 'CAESAR', side: 'red', country: 'Russia', heli: true, start: 'parking', dep: { start: 'parking', airdromeId: 44, airdrome: 'Akrotiri', x: -35778.63, y: -268906.12, stands: [] },
    chk: { route: true, radios: true, loadout: true, livery: true }, avail: { route: true, radios: false, loadout: false, livery: false }, groupFrequency: null,
    route: { 1: { x: -35775.78, y: -268903.87, alt: 0, alt_type: 'BARO', type: 'Turning Point', action: 'Turning Point', speed: 61.11, name: 'AKROTIRI' }, 2: { x: -26026.17, y: -297606.2, alt: 30, alt_type: 'RADIO', speed: 61.11, name: 'WP1' } },
    units: [{ name: '', type: 'Mi-24P', onboardNum: '', radios: [], liveryId: null, addProp: null, payload: null }, { name: '', type: 'Mi-24P', onboardNum: '', radios: [], liveryId: null, addProp: null, payload: null }],
    sp: [{ chosen: { n: 33, id: 'H4', x: -35850.55, y: -269570.47 } }, { chosen: { n: 35, id: 'H2', x: -35829.12, y: -269466.06 } }] }, o || {});
  const work = { ast: N({ coalition: { red: { country: { 1: { name: 'Russia' } } } } }) };
  const pt = (g, k) => { const p = g.route.points[k]; return p ? { type: p.type, action: p.action, airdromeId: p.airdromeId === undefined ? null : p.airdromeId, x: p.x, y: p.y, alt: p.alt, alt_type: p.alt_type, speed: p.speed, ETA_locked: p.ETA_locked, name: p.name } : null; };
  const un = u => ({ parking: u.parking, parking_id: u.parking_id, x: u.x, y: u.y, alt: u.alt, alt_type: u.alt_type, speed: u.speed, heading: u.heading, psi: u.psi });
"""


def test_build_group_on_the_stand_follows_pydcs():
    out = run(BUILD + """
      const g = pkBuildGroup(work, fl()).group, r = {};
      r.n = Object.keys(g.route.points).length; r.p1 = pt(g, 1); r.p2 = pt(g, 2);
      r.units = Object.values(g.units).map(un); r.gxy = [g.x, g.y];
      console.log(JSON.stringify(r));
    """)
    assert out['n'] == 2                       # le point AKROTIRI du paquet, à 4 m de la base, est remplacé
    assert out['p1'] == {'type': 'TakeOffParking', 'action': 'From Parking Area', 'airdromeId': 44, 'x': -35850.55, 'y': -269570.47, 'alt': 0, 'alt_type': 'BARO', 'speed': 0, 'ETA_locked': True, 'name': ''}
    assert out['p2']['name'] == 'WP1' and out['p2']['airdromeId'] is None and out['p2']['ETA_locked'] is False
    assert out['units'] == [
        {'parking': 33, 'parking_id': 'H4', 'x': -35850.55, 'y': -269570.47, 'alt': 0, 'alt_type': 'BARO', 'speed': 0, 'heading': 0, 'psi': 0},
        {'parking': 35, 'parking_id': 'H2', 'x': -35829.12, 'y': -269466.06, 'alt': 0, 'alt_type': 'BARO', 'speed': 0, 'heading': 0, 'psi': 0}]
    assert out['gxy'] == [-35850.55, -269570.47]       # le groupe est au point 1


def test_build_group_hot_start_and_a_first_point_far_from_the_base_is_kept_as_point_2():
    out = run(BUILD + """
      const o = fl({ start: 'parkingHot', route: { 1: { x: -20000, y: -280000, alt: 100, alt_type: 'RADIO', speed: 61.11, name: 'IP', airdromeId: 44 }, 2: { x: -15000, y: -285000, alt: 100, alt_type: 'RADIO', speed: 61.11, name: 'OBJ' } } });
      o.dep.start = 'parkingHot'; o.units.pop(); o.sp.pop();
      const g = pkBuildGroup(work, o).group, r = {};
      r.n = Object.keys(g.route.points).length; r.p1 = pt(g, 1); r.p2 = pt(g, 2); r.p3 = pt(g, 3); r.units = Object.values(g.units).map(un);
      console.log(JSON.stringify(r));
    """)
    assert out['n'] == 3
    assert out['p1']['type'] == 'TakeOffParkingHot' and out['p1']['action'] == 'From Parking Area Hot' and out['p1']['airdromeId'] == 44
    assert out['p2'] == {'type': 'Turning Point', 'action': 'Turning Point', 'airdromeId': None, 'x': -20000, 'y': -280000, 'alt': 100, 'alt_type': 'RADIO', 'speed': 61.11, 'ETA_locked': False, 'name': 'IP'}
    assert out['p3']['name'] == 'OBJ' and len(out['units']) == 1


def test_build_group_in_the_air_and_on_the_ground_stay_as_before():
    out = run(BUILD + """
      const air = pkBuildGroup(work, fl({ start: 'air', dep: null, sp: null })).group, gnd = pkBuildGroup(work, fl({ start: 'ground', dep: { start: 'ground' }, sp: null })).group;
      console.log(JSON.stringify({ air: [pt(air, 1), air.units[1].parking, air.units[1].heading !== 0 || air.units[1].alt > 0], gnd: [pt(gnd, 1), Object.keys(gnd.route.points).length] }));
    """)
    air, gnd = out['air'], out['gnd']
    assert air[0]['type'] == 'Turning Point' and air[0]['airdromeId'] is None and air[0]['ETA_locked'] is True and air[0]['alt'] > 0
    assert air[1] is None and air[2] is True          # une unité en vol : aucune place, une altitude
    assert gnd[0]['type'] == 'TakeOffGround' and gnd[0]['action'] == 'From Ground Area' and gnd[1] == 2


def test_build_group_on_the_stand_refuses_a_plan_without_a_place():
    r = subprocess.run([NODE, '-e', PRELUDE + '\n' + BUILD + """
      try { pkBuildGroup(work, fl({ sp: null })); console.log('no error'); } catch (e) { console.log('error ' + JSON.stringify(e.pkErrors)); }
      try { const o = fl(); o.sp[1].chosen = null; pkBuildGroup(work, o); console.log('no error'); } catch (e) { console.log('error ' + JSON.stringify(e.pkErrors)); }
    """], capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr
    assert r.stdout.splitlines() == ['error [{"key":"pk.e.created","args":[]}]'] * 2
