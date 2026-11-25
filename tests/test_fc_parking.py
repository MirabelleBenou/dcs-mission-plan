"""La base de départ et la place de chaque appareil (Flight Configurator) : tools/gen_parkings.py, data/parkings.json et les fonctions fp* de dist/dcs_flight_configurator.html.
Les fonctions sont lues dans le dist et jouées par node avec de faux accessoires (aucune page, aucun réseau) ; données fabriquées, sauf les contrôles de la table livrée."""
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools'))
import gen_parkings as gen  # noqa: E402

FC = (ROOT / 'dist' / 'dcs_flight_configurator.html').read_text(encoding='utf-8')
NODE = shutil.which('node')
needs_node = pytest.mark.skipif(NODE is None, reason='node absent')


# ---------- tools/gen_parkings.py ----------
def fake_charts(folder, source='pydcs test ; fabriqué', second_source=None):
    folder.mkdir(parents=True, exist_ok=True)
    (folder / 'aircraft.json').write_text(json.dumps({
        'format': 'dcs-aircraft-sizes-v1',
        'aircraft': {'HeliA': {'heli': True, 'length': 10.0, 'width': 5.0, 'height': 3.0}, 'PlaneA': {'heli': False, 'length': 15.0, 'width': 10.0}}}), encoding='utf-8')

    def theatre(name, src, bases):
        return {'format': 'dcs-parkings-v1', 'theatre': name, 'source': src, 'airdromes': bases}

    def stand(n, pid, heli, plane, x, y, h=None):
        s = {'parking': n, 'parking_id': pid, 'heli': heli, 'plane': plane, 'x': x, 'y': y, 'length': 20.0, 'width': 12.0}
        if h is not None:
            s['height'] = h
        return s
    (folder / 'Alpha.json').write_text(json.dumps(theatre('Alpha', source, [
        {'airdromeId': 7, 'name': 'Base Sept', 'x': 1.5, 'y': 2.5, 'parkings': [stand(1, 'H1', True, False, 10, 20, 6.0), stand(2, 'P1', False, True, 30, 40), stand(3, 'B1', True, True, 50, 60)]}])), encoding='utf-8')
    (folder / 'Beta.json').write_text(json.dumps(theatre('Beta', second_source or source, [
        {'airdromeId': 9, 'name': 'Base Neuf', 'x': 0, 'y': 0, 'parkings': [stand(1, 'A', False, True, 1, 2)]}])), encoding='utf-8')


def run_gen(*args):
    return subprocess.run([sys.executable, '-B', str(ROOT / 'tools' / 'gen_parkings.py')] + [str(a) for a in args], capture_output=True, text=True)


SHA = 'a' * 40


def test_gen_parkings_shape_marks_source_and_stability(tmp_path):
    src = tmp_path / 'parkings'
    fake_charts(src)
    o1, o2 = tmp_path / 'o1.json', tmp_path / 'o2.json'
    assert run_gen(src, o1, '--commit', SHA).returncode == 0
    assert run_gen(src, o2, '--commit', SHA).returncode == 0
    assert o1.read_bytes() == o2.read_bytes()       # deux fabrications de suite : le même fichier, à l'octet
    text = o1.read_text(encoding='utf-8')
    assert text.endswith('\n') and ', ' not in text and ': ' not in text       # compact : aucun espace de mise en forme
    d = json.loads(text)
    assert d['source'] == 'pydcs test ; fabriqué ; dcs-airfield-charts ' + SHA
    assert d['aircraft'] == {'HeliA': [1, 10.0, 5.0, 3.0], 'PlaneA': [0, 15.0, 10.0, None]}
    assert list(d['theatres']) == ['Alpha', 'Beta']
    base = d['theatres']['Alpha'][0]
    assert base[:4] == [7, 'Base Sept', 1.5, 2.5]
    assert base[4] == [[1, 'H1', 10, 20, 1, 20.0, 12.0, 6.0], [2, 'P1', 30, 40, 2, 20.0, 12.0, None], [3, 'B1', 50, 60, 3, 20.0, 12.0, None]]


def test_gen_parkings_refuses_what_it_cannot_read(tmp_path):
    src = tmp_path / 'p'
    fake_charts(src, second_source='une autre ligne source')
    r = run_gen(src, tmp_path / 'o.json', '--commit', SHA)
    assert r.returncode == 1 and 'source' in r.stderr
    src2 = tmp_path / 'p2'
    fake_charts(src2)
    (src2 / 'Beta.json').write_text(json.dumps({'format': 'autre', 'theatre': 'Beta', 'airdromes': []}), encoding='utf-8')
    r = run_gen(src2, tmp_path / 'o2.json', '--commit', SHA)
    assert r.returncode == 1 and 'format' in r.stderr
    r = run_gen(src, tmp_path / 'o3.json')       # hors dépôt git et sans --commit : pas de commit, pas de fichier
    assert r.returncode == 1 and 'commit' in r.stderr and not (tmp_path / 'o3.json').exists()


# ---------- data/parkings.json (la table livrée) ----------
def test_delivered_table_is_consistent_and_embedded():
    raw = (ROOT / 'data' / 'parkings.json').read_text(encoding='utf-8')
    d = json.loads(raw)
    assert re.search(r'dcs-airfield-charts [0-9a-f]{40}$', d['source'])
    assert raw == json.dumps(d, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n'
    for th, bases in d['theatres'].items():
        ids = [b[0] for b in bases]
        assert len(ids) == len(set(ids)), th
        for b in bases:
            ns = [s[0] for s in b[4]]
            assert len(ns) == len(set(ns)), (th, b[1])
            for s in b[4]:
                assert s[4] in (1, 2, 3) and s[5] > 0 and s[6] > 0, (th, b[1], s)
    for ty, a in d['aircraft'].items():
        assert a[0] in (0, 1) and a[1] > 0 and a[2] > 0, ty
    assert json.dumps(d, ensure_ascii=False, sort_keys=True, separators=(',', ':')) in FC        # la même table, embarquée dans le Flight Configurator
    ak = [b for b in d['theatres']['Syria'] if b[0] == 44][0]
    assert ak[1] == 'Akrotiri' and len(ak[4]) == 45
    h1 = [s for s in ak[4] if s[1] == 'H1'][0]
    assert h1[:5] == [36, 'H1', -35799.94, -269506.88, 1]


# ---------- Les fonctions fp* du Flight Configurator ----------
def fn(name):
    i = FC.index('function %s(' % name)
    j = FC.index('{', i)
    depth, k = 0, j
    while True:
        c = FC[k]
        if c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0:
                return FC[i:k + 1]
        k += 1


def const_line(name):
    m = re.search(r'^const %s = .*$' % name, FC, re.M)
    assert m, name
    return m.group(0)


# Des places à la main : H1 hélico 20x12 h6 ; P1 avion 30x14 sans hauteur ; B1 les deux, 12x8 ; X1 hélico 10x5 (égale à HeliA : trop petite)
THEATRES = {'Alpha': [[7, 'Base Sept', 100, 200, [
    [1, 'H1', 10, 20, 1, 20.0, 12.0, 6.0], [2, 'P1', 30, 40, 2, 30.0, 14.0, None], [3, 'B1', 50, 60, 3, 12.0, 8.0, 4.0], [4, 'X1', 70, 80, 1, 10.0, 5.0, 3.0]]],
    [8, 'Base Huit', 500, 600, [[1, 'Z1', 1, 1, 1, 50.0, 50.0, 50.0]]]]}
AIRCRAFT = {'HeliA': [1, 10.0, 5.0, 3.0], 'HeliB': [1, 8.0, 4.0, 2.0], 'PlaneA': [0, 15.0, 10.0, None], 'PlaneB': [0, 11.0, 6.0, 3.5]}

PRELUDE = '\n'.join([
    fn('uiKeyOk'),       # la garde commune de ui_block.py, telle que la page la porte
    "const PARKINGS = " + json.dumps({'aircraft': AIRCRAFT, 'theatres': THEATRES}) + ";",
    "const has = (o, k) => Object.prototype.hasOwnProperty.call(o, k);",
    "const isObj = o => !!o && typeof o === 'object' && !Array.isArray(o);",
    "const GAME_AIRCRAFT_TYPES = { helicopters: ['HeliUnknown'], airplanes: ['PlaneUnknown'] };",
    "let TH = 'Alpha'; function rTh() { return TH; }",
    "const thOk = id => ['Alpha', 'Beta', 'Nowhere'].indexOf(id) >= 0;",
    "let S = { flights: [] }; function refreshAll() {}",
    "function flightTypes(f) { const o = []; f.units.forEach(u => { if (u.type && o.indexOf(u.type) < 0) o.push(u.type); }); return o; }",
    const_line('FP_STARTS'), const_line('FP'),
    fn('fpTheatre'), fn('fpBaseOf'), fn('fpStartOf'), fn('fpStandOf'), fn('fpAc'), fn('fpIsHeli'), fn('fpFits'), fn('fpNat'), fn('fpGroupStands'), fn('fpTakenBy'),
    fn('fpSetBase'), fn('fpSetStart'), fn('fpSetStand'), fn('fpKeepStand'), fn('fpStampBases'), fn('fpDropStale'), fn('fpDepartureOut'), fn('fpStandOut'), fn('fpCarryDepartures'),
    "function U(type, stand) { return { type: type, stand: stand === undefined ? null : stand }; }",
    "function F(name, base, start, units) { return { fcId: name, name: name, base: base, start: start, units: units }; }",
])


def run(body):
    r = subprocess.run([NODE, '-e', PRELUDE + '\n' + body], capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


@needs_node
def test_fits_follows_the_pydcs_rule():
    out = run("""
      const T = fpTheatre('Alpha').byId[7], by = id => T.st.find(s => s.id === id);
      const r = {};
      ['HeliA', 'HeliB', 'PlaneA', 'PlaneB', 'HeliUnknown', 'PlaneUnknown', 'NoSuch', ''].forEach(ty => { r[ty] = T.st.filter(s => fpFits(s, ty)).map(s => s.id); });
      console.log(JSON.stringify(r));
    """)
    assert out['HeliA'] == ['H1', 'B1']          # X1 : à taille égale, pas plus petite ; P1 : marquée avion seulement
    assert out['HeliB'] == ['H1', 'B1', 'X1']
    assert out['PlaneA'] == ['P1']               # B1 : 12 m < 15 m ; hauteur inconnue de PlaneA : non comparée
    assert out['PlaneB'] == ['P1', 'B1']
    assert out['HeliUnknown'] == ['H1', 'B1', 'X1']     # un type que la table ne connaît pas : les marques seules (la liste des hélicoptères du jeu dit qu'il en est un)
    assert out['PlaneUnknown'] == ['P1', 'B1']
    assert out['NoSuch'] == ['P1', 'B1']                # ni l'un ni l'autre connu : un avion
    assert out[''] == []


@needs_node
def test_state_changes_keep_the_group_coherent():
    out = run("""
      const f = F('G', null, 'air', [U('HeliA'), U('HeliA')]); S.flights = [f];
      const r = {};
      r.none = [fpBaseOf(f), fpStartOf(f)];
      fpSetBase(f, '7'); r.set = [f.base, f.start, fpBaseOf(f).name];
      fpSetStart(f, 'parkingHot'); r.hot = f.start;
      fpSetStart(f, 'air'); r.refused = f.start;               // « en vol » n'est pas un départ de base
      fpSetStand(f, f.units[0], '1'); fpSetStand(f, f.units[1], '3'); r.stands = f.units.map(u => u.stand);
      fpSetStand(f, f.units[1], '99'); r.unknownStand = f.units[1].stand;
      fpSetStand(f, f.units[1], 'abc'); r.junk = f.units[1].stand;
      f.units[1].type = 'PlaneB'; fpKeepStand(f, f.units[1]); r.keptB1 = f.units[1].stand;       // B1 prend encore PlaneB
      f.units[0].type = 'PlaneA'; fpKeepStand(f, f.units[0]); r.droppedH1 = f.units[0].stand;      // H1 est une place d'hélico
      fpSetBase(f, '7'); r.sameBase = f.units[1].stand;                                          // la même base : rien ne bouge
      fpSetBase(f, '8'); r.other = [f.base, f.start, f.units.map(u => u.stand)];
      fpSetBase(f, ''); r.cleared = [f.base, f.start];
      r.th = f.baseTh;
      const g = F('H', 7, 'parkingHot', [U('HeliA', 1)]);              // un groupe d'avant le lot : sans baseTh
      const k = F('K', 7, 'parking', [U('HeliA', 1)]); k.baseTh = 'Alpha';
      S.flights = [f, g, k];
      fpStampBases(); r.stamped = S.flights.map(x => x.baseTh);
      TH = 'Beta'; r.noneNow = S.flights.map(x => fpBaseOf(x));         // lus d'un autre théâtre : sans base
      r.dropped = fpDropStale(); r.all = S.flights.map(x => [x.base, x.baseTh, x.start, x.units.map(u => u.stand)]);
      TH = 'Alpha'; r.back = S.flights.map(x => fpBaseOf(x));
      console.log(JSON.stringify(r));
    """)
    assert out['none'] == [None, 'air']
    assert out['set'] == [7, 'parking', 'Base Sept']
    assert out['hot'] == 'parkingHot' and out['refused'] == 'parkingHot'
    assert out['stands'] == [1, 3] and out['unknownStand'] == 3 and out['junk'] == 3
    assert out['keptB1'] == 3 and out['droppedH1'] is None and out['sameBase'] == 3
    assert out['other'] == [8, 'parkingHot', [None, None]]       # une autre base : les places sont vidées, le départ reste
    assert out['cleared'] == [None, 'air']
    assert out['th'] == ''       # « Aucune » : plus de théâtre de base
    assert out['stamped'] == ['', 'Alpha', 'Alpha']      # f est sans base : rien à dater ; g (d'avant le lot) prend le théâtre de lecture ; k l'a déjà
    assert out['noneNow'] == [None, None, None] and out['dropped'] is True
    assert out['all'] == [[None, '', 'air', [None, None]], [None, '', 'air', [None]], [None, '', 'air', [None]]]
    assert out['back'] == [None, None, None]       # le retour sur le théâtre d'origine ne les ramène pas


@needs_node
def test_unreadable_values_read_as_none():
    out = run("""
      const r = {};
      const a = F('A', 12345, 'parking', [U('HeliA', 1)]);           // une base que le théâtre n'a pas
      r.a = [fpBaseOf(a), fpStartOf(a), fpStandOf(a, a.units[0])];
      const b = F('B', 7, 'parkingHot', [U('HeliA', 99), U('HeliA', 1)]);
      r.b = [fpStartOf(b), fpStandOf(b, b.units[0]), fpStandOf(b, b.units[1]).id];
      const c = F('C', '7', 'parking', [U('HeliA', 1)]);               // une base écrite en texte : illisible
      r.c = fpBaseOf(c);
      TH = 'Nowhere'; r.d = fpBaseOf(b); TH = 'Alpha';
      console.log(JSON.stringify(r));
    """)
    assert out['a'] == [None, 'air', None]
    assert out['b'] == ['parkingHot', None, 'H1']
    assert out['c'] is None and out['d'] is None


@needs_node
def test_taken_by_spans_groups_of_the_same_base_only():
    out = run("""
      const a = F('A', 7, 'parking', [U('HeliA', 1), U('HeliA')]), b = F('B', 7, 'parking', [U('HeliA', 3)]), c = F('C', 8, 'parking', [U('HeliA', 1)]), d = F('D', null, 'air', [U('HeliA')]);
      S.flights = [a, b, c, d];
      const T7 = fpTheatre('Alpha').byId[7], m = fpTakenBy(T7, a.units[1]);
      console.log(JSON.stringify({ keys: [...m.keys()].sort(), by: [...m.entries()].map(([n, o]) => [n, o.f.name, o.fi, o.ui]), self: [...fpTakenBy(T7, a.units[0]).keys()] }));
    """)
    assert out['keys'] == [1, 3]       # la place 1 du groupe C est dans une autre base
    assert out['by'] == [[1, 'A', 0, 0], [3, 'B', 1, 0]] and out['self'] == [3]


@needs_node
def test_package_departure_and_stand_out():
    out = run("""
      const r = {};
      const none = F('N', null, 'ground', [U('HeliA')]);
      r.none = [fpDepartureOut(none), fpStandOut(none, none.units[0])];
      const g = F('G', 7, 'parking', [U('HeliA', 1), U('HeliB'), U('HeliA', 3)]);
      r.dep = fpDepartureOut(g); r.st = g.units.map(u => fpStandOut(g, u));
      const e = F('E', 7, 'parking', []);              // sans unité : aucune place offerte
      r.empty = fpDepartureOut(e).stands;
      const m = F('M', 7, 'parkingHot', [U('HeliA'), U('PlaneA')]);       // un hélico et un avion : aucune place ne les prend tous deux
      r.mixed = fpDepartureOut(m).stands;
      console.log(JSON.stringify(r));
    """)
    assert out['none'] == [{'start': 'ground', 'airdromeId': None, 'airdrome': None, 'x': None, 'y': None, 'stands': []}, None]
    assert out['dep'] == {'start': 'parking', 'airdromeId': 7, 'airdrome': 'Base Sept', 'x': 100, 'y': 200, 'stands': [
        {'parking': 1, 'parking_id': 'H1', 'x': 10, 'y': 20}, {'parking': 3, 'parking_id': 'B1', 'x': 50, 'y': 60}]}
    assert out['st'] == [{'parking': 1, 'parking_id': 'H1', 'x': 10, 'y': 20}, None, {'parking': 3, 'parking_id': 'B1', 'x': 50, 'y': 60}]
    assert out['empty'] == [] and out['mixed'] == []


@needs_node
def test_opening_a_package_carries_the_departure():
    out = run("""
      const g1 = F('CAESAR', null, 'air', [U('HeliA'), U('HeliA')]), g2 = F('HIND', null, 'air', [U('HeliA')]), g3 = F('Autre', null, 'air', [U('HeliA')]);
      g1.fcId = 'a'; g2.fcId = 'b'; g3.fcId = 'c';
      const pkg = { flights: [
        { groupName: 'CAESAR', departure: { start: 'parking', airdromeId: 7 }, units: [{ name: 'u1', stand: { parking: 1 } }, { name: 'u2', stand: { parking: 99 } }] },
        { groupName: 'HIND', departure: { start: 'parkingHot', airdromeId: 7 }, units: [{ name: 'u3', stand: null }] },
        { groupName: 'Autre', departure: { start: 'ground', airdromeId: null }, units: [{ name: 'u4' }] } ] };
      const src = { theatre: 'Alpha', rows: pkg.flights.map(x => ({ name: x.groupName, managed: true, units: x.units })) };       // l'import commun lit les unités du paquet sans les copier
      fpCarryDepartures([g1, g2, g3], src, pkg);
      const r = [g1, g2, g3].map(g => [g.base, g.start, g.units.map(u => u.stand)]);
      const miss = [F('X', null, 'air', [U('HeliA')])]; miss[0].fcId = 'x';
      const px = { flights: [{ groupName: 'X', departure: { start: 'parking', airdromeId: 7 }, units: [{ stand: { parking: 1 } }] }] };
      fpCarryDepartures(miss, { theatre: 'Inconnu', rows: [{ name: 'X', managed: true, units: px.flights[0].units }] }, px);
      console.log(JSON.stringify({ r: r, otherTheatre: [miss[0].base, miss[0].start, miss[0].units[0].stand] }));
    """)
    assert out['r'] == [[7, 'parking', [1, None]], [7, 'parkingHot', [None]], [None, 'ground', [None]]]       # une place que la base n'a pas : aucune
    assert out['otherTheatre'] == [None, 'air', None]


@needs_node
def test_restore_flight_reads_junk_as_default():
    stubs = '\n'.join([
        fn('uiKeyOk'),
        "const isObj = o => !!o && typeof o === 'object' && !Array.isArray(o);", "const str = v => (typeof v === 'string' ? v : '');",
        "const MAX_UNITS = 8, PAYLOAD_TYPES = ['HeliA', 'PlaneA'];", const_line('FP_STARTS'), "const UNIT_KEYS = ['type', 'name', 'callsign', 'csRaw', 'onboard', 'livery', 'folded', 'radios', 'loadout', 'payloadIn', 'stand', 'props', 'addPropIn'];",
        "const thOk = id => ['Alpha', 'Beta'].indexOf(id) >= 0;", "function newId() { return 'id'; }", "function newUnit(type) { return { type: type, name: '', callsign: '', onboard: '', livery: '', radios: {}, loadout: null, folded: false }; }",
        "function fcNewUnit(type) { const u = newUnit(type); u.stand = null; u.props = {}; return u; }", "function fcPropsRead(type, raw) { return isObj(raw) ? raw : {}; }", "function newFlight() { return { fcId: 'n', name: '', coalition: '', route: null, base: null, baseTh: '', start: 'air', units: [] }; }",
        "function gsRouteCopy(p) { return { points: p }; }", "function ridOk() { return false; }", "function loBring() {}", "function loSnap() { return {}; }", "function loadoutFromPayload() { return null; }",
        fn('restoreFlight')])
    r = subprocess.run([NODE, '-e', stubs + """
      const out = {};
      const mk = (base, start, stand) => restoreFlight({ fcId: 'x', name: 'G', base: base, start: start, units: [{ type: 'HeliA', stand: stand }] });
      const show = f => [f.base, f.start, f.units[0].stand];
      out.legacy = show(restoreFlight({ fcId: 'x', name: 'G', units: [{ type: 'HeliA' }] }));        // un groupe d'avant le lot
      out.ok = show(mk(7, 'parkingHot', 3));
      out.baseText = show(mk('7', 'parking', 3));
      out.baseNeg = show(mk(-1, 'parking', 3));
      out.noBase = show(mk(null, 'parking', 3));         // un départ sur la place sans base : en vol
      out.hotNoBase = show(mk(null, 'parkingHot', 3));
      out.airWithBase = show(mk(7, 'air', 3));            // une base, mais « en vol » : sur la place
      out.junkStart = show(mk(7, 'xyz', 3));
      out.standJunk = show(mk(7, 'parking', 'a'));
      out.standNeg = show(mk(7, 'parking', -2));
      out.standNoBase = show(mk(null, 'ground', 3));      // la place n'a de sens que dans une base
      const th = (base, bt) => restoreFlight({ fcId: 'x', name: 'G', base: base, baseTh: bt, units: [{ type: 'HeliA' }] }).baseTh;
      out.th = [th(7, 'Alpha'), th(7, 'Beta'), th(7, 'Nowhere'), th(7, 5), th(7, undefined), th(null, 'Alpha')];       // le théâtre de la base : gardé s'il est lisible, sinon vide ; sans base, vide
      console.log(JSON.stringify(out));
    """], capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr
    o = json.loads(r.stdout)
    assert o['legacy'] == [None, 'air', None] and o['ok'] == [7, 'parkingHot', 3]
    assert o['baseText'] == [None, 'air', None] and o['baseNeg'] == [None, 'air', None]
    assert o['noBase'] == [None, 'air', None] and o['hotNoBase'] == [None, 'air', None]
    assert o['airWithBase'] == [7, 'parking', 3] and o['junkStart'] == [7, 'parking', 3]
    assert o['standJunk'] == [7, 'parking', None] and o['standNeg'] == [7, 'parking', None]
    assert o['standNoBase'] == [None, 'ground', None]


# ---------- Addendum 1 : une base ne vaut que dans son théâtre (Q1, Q2), une place qui ne prend plus le type ne compte pas (Q3) ----------
@needs_node
def test_base_is_read_only_in_the_theatre_it_was_chosen_in():
    out = run("""
      const r = {};
      const f = F('G', null, 'air', [U('HeliA'), U('HeliA')]); S.flights = [f];
      fpSetBase(f, '7'); fpSetStand(f, f.units[0], '1');
      r.chosen = [f.base, f.baseTh, fpBaseOf(f).name, fpStandOut(f, f.units[0]).parking_id, fpDepartureOut(f).airdromeId];
      TH = 'Beta';       // le théâtre où l'on lit les bases a changé (clé commune passée à un autre théâtre, FC fermé) : le groupe est sans base partout
      r.beta = [fpBaseOf(f), fpStartOf(f), fpStandOf(f, f.units[0]), fpStandOut(f, f.units[0]), fpDepartureOut(f), fpGroupStands(f, fpTheatre('Alpha').byId[7]).length > 0];
      r.dropped = fpDropStale(); r.after = [f.base, f.baseTh, f.start, f.units.map(u => u.stand)];
      TH = 'Alpha'; r.back = [fpBaseOf(f), fpStandOf(f, f.units[0])];        // le retour ne les ramène pas : elles sont tombées
      r.droppedAgain = fpDropStale();
      console.log(JSON.stringify(r));
    """)
    assert out['chosen'] == [7, 'Alpha', 'Base Sept', 'H1', 7]
    assert out['beta'][:3] == [None, 'air', None] and out['beta'][3] is None
    assert out['beta'][4] == {'start': 'air', 'airdromeId': None, 'airdrome': None, 'x': None, 'y': None, 'stands': []}
    assert out['dropped'] is True and out['after'] == [None, '', 'air', [None, None]]
    assert out['back'] == [None, None] and out['droppedAgain'] is False


@needs_node
def test_legacy_group_without_theatre_is_read_in_the_current_one_and_stamped_before_a_change():
    out = run("""
      const r = {};
      const g = F('G', 7, 'parkingHot', [U('HeliA', 1)]);          // un groupe d'avant le lot, ou livré avant l'addendum : base sans baseTh
      S.flights = [g];
      r.read = [fpBaseOf(g).name, fpStandOf(g, g.units[0]).id, fpStartOf(g)];
      r.noDrop = fpDropStale();                                      // sans théâtre de base, rien n'est périmé
      fpStampBases(); r.stamp = g.baseTh;
      TH = 'Beta'; r.dropped = fpDropStale(); r.after = [g.base, g.start, g.units[0].stand];
      console.log(JSON.stringify(r));
    """)
    assert out['read'] == ['Base Sept', 'H1', 'parkingHot'] and out['noDrop'] is False and out['stamp'] == 'Alpha'
    assert out['dropped'] is True and out['after'] == [None, 'air', None]


@needs_node
def test_base_kept_while_the_theatre_where_bases_are_read_does_not_change():
    out = run("""
      const r = {};
      const f = F('G', null, 'air', [U('HeliA')]); S.flights = [f];
      fpSetBase(f, '7'); fpSetStand(f, f.units[0], '1');
      // le bandeau : l'écran passe à Beta, la fiche reste sur Alpha, rTh() lit toujours Alpha ; « Revenir à Alpha » ne change pas rTh()
      fpStampBases(); r.d1 = fpDropStale(); r.d2 = fpDropStale();
      r.kept = [f.base, f.baseTh, fpStandOf(f, f.units[0]).id];
      console.log(JSON.stringify(r));
    """)
    assert out['d1'] is False and out['d2'] is False and out['kept'] == [7, 'Alpha', 'H1']


@needs_node
def test_a_stand_the_type_does_not_take_counts_as_no_stand():
    out = run("""
      const r = {};
      const f = F('G', 7, 'parking', [U('HeliA', 1), U('HeliA', 3)]); S.flights = [f];
      r.before = f.units.map(u => fpStandOut(f, u) && fpStandOut(f, u).parking_id);
      f.units[0].type = 'PlaneA';           // retypé hors du module (l'import d'un groupe existant) : H1 est une place d'hélico
      r.after = [fpStandOf(f, f.units[0]), fpStandOut(f, f.units[0])];
      r.takenFree = [...fpTakenBy(fpBaseOf(f), f.units[1]).keys()];       // elle ne retient plus rien
      r.stored = f.units[0].stand;         // la valeur écrite reste : seule la lecture l'ignore
      r.sum = fpGroupStands(f, fpBaseOf(f)).map(s => s.id);
      console.log(JSON.stringify(r));
    """)
    assert out['before'] == ['H1', 'B1'] and out['after'] == [None, None] and out['takenFree'] == [] and out['stored'] == 1


# ---------- Addendum 2 : « Ouvrir » juge les bases du fichier contre le théâtre du fichier (R1) ----------
@needs_node
def test_drop_stale_can_judge_against_the_theatre_of_an_opened_file():
    out = run("""
      const r = {};
      TH = 'Beta';       // la fiche portait un autre théâtre avant l'ouverture : rTh() lit encore l'ancien
      const a = F('A', 7, 'parking', [U('HeliA', 1)]), b = F('B', 7, 'parkingHot', [U('HeliA', 3)]), c = F('C', 7, 'parking', [U('HeliA', 1)]);
      a.baseTh = 'Alpha'; b.baseTh = 'Alpha'; c.baseTh = 'Beta';        // les deux premiers viennent d'un fichier Alpha ; c, d'un fichier incohérent
      S.flights = [a, b, c];
      r.dropped = fpDropStale('Alpha');
      r.after = S.flights.map(x => [x.base, x.baseTh, x.start, x.units.map(u => u.stand)]);
      const d = F('D', 7, 'parking', [U('HeliA', 1)]); d.baseTh = 'Alpha'; S.flights = [d];
      r.byDefault = fpDropStale();            // sans argument : contre rTh() (Beta), comme avant
      console.log(JSON.stringify(r));
    """)
    assert out['dropped'] is True
    assert out['after'] == [[7, 'Alpha', 'parking', [1]], [7, 'Alpha', 'parkingHot', [3]], [None, '', 'air', [None]]]
    assert out['byDefault'] is True
