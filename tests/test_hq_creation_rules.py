"""Les règles de la création d'un vol absent par HQ (addendum 1) : A1 noms uniques, A2 théâtre, A4 indicatifs, A6 données du paquet.
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
    """Le texte d'une fonction de premier niveau : de « function name( » à son accolade fermante."""
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
    fn('uiKeyOk'),       # la garde commune de ui_block.py, telle que la page la porte
    "function t(k) { return k; }",
    "function tf(k) { return [k].concat(Array.prototype.slice.call(arguments, 1)).join('|'); }",
    const_line('PK_CALLSIGNS'), const_line('PK_CS_RE'),
    fn('pkNameKey'), fn('pkIsNum'), fn('pkClean'), fn('pkUnitName'), fn('pkNameWhy'), fn('pkCallsigns'), fn('pkWhyText'),
    const_line('PK_SIDES'), fn('pkSideOf'), fn('pkRoutePoint'), fn('pkCreateState'),
])


def run(body):
    src = PRELUDE + '\n' + body
    r = subprocess.run([NODE, '-e', src], capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


def test_a6_pkclean_removes_null_and_dangerous_keys():
    out = run("""
      const raw = JSON.parse('{"a":null,"b":{"c":null,"d":1,"__proto__":{"p":1},"constructor":{"x":1},"prototype":2},"e":[1,null,{"f":null,"g":2}]}');
      const c = pkClean(raw);
      console.log(JSON.stringify({ c: c, polluted: ({}).p === undefined, own: Object.keys(c.b) }));
    """)
    assert out['c'] == {'b': {'d': 1}, 'e': [1, {'g': 2}]}
    assert out['own'] == ['d'] and out['polluted']


def test_a6_state_unreadable_first_point():
    out = run("""
      const AIRCRAFT_TEMPLATES = { 'Mi-24P': { heli: true } };
      function pkTpl(ty) { return AIRCRAFT_TEMPLATES[ty] || null; }
      function pkSideCountries() { return [{ name: 'Russia', clients: 0 }]; }
      function pkDefaultCountry(l) { return l[0].name; }
      const ctx = { theatre: 'Caucasus' }, pk = { theatre: 'Caucasus' }, sc = { groups: new Set(), units: new Set() };
      const mk = p1 => ({ coalition: 'red', groupName: 'G', units: [{ name: '', type: 'Mi-24P' }], route: { '1': p1 } });
      const res = {};
      for (const [k, p1] of [['noX', { y: 1 }], ['text', { x: '1', y: 2 }], ['nan', { x: NaN, y: 2 }], ['ok', { x: 1, y: 2 }]]) { const fl = mk(p1); pkCreateState(ctx, fl, pk, sc); res[k] = fl.why; }
      console.log(JSON.stringify(res));
    """)
    assert out == {'noX': 'badRoute', 'text': 'badRoute', 'nan': 'badRoute', 'ok': None}


def test_a2_theatre_differs_or_missing():
    out = run("""
      const AIRCRAFT_TEMPLATES = { 'Mi-24P': { heli: true } };
      function pkTpl(ty) { return AIRCRAFT_TEMPLATES[ty] || null; }
      function pkSideCountries() { return [{ name: 'Russia', clients: 0 }]; }
      function pkDefaultCountry(l) { return l[0].name; }
      const sc = { groups: new Set(), units: new Set() };
      const res = {};
      for (const [k, pkTh, ctxTh] of [['same', 'Caucasus', 'Caucasus'], ['diff', 'Syria', 'Caucasus'], ['noMission', 'Syria', ''], ['noPackage', '', 'Caucasus']]) {
        const fl = { coalition: 'red', groupName: 'G', units: [{ name: '', type: 'Mi-24P' }], route: { '1': { x: 1, y: 2 } } };
        pkCreateState({ theatre: ctxTh }, fl, { theatre: pkTh }, sc);
        res[k] = [fl.why, fl.whyArgs, pkWhyText(fl.why || 'x', fl.whyArgs)];
      }
      console.log(JSON.stringify(res));
    """)
    assert out['same'][0] is None
    assert out['diff'][0] == 'theatre' and out['diff'][1] == ['Syria', 'Caucasus']
    assert out['diff'][2] == 'pk.why.theatre|Syria|Caucasus'
    assert out['noMission'][0] == 'theatre' and out['noPackage'][0] == 'theatre'


def test_a1_names_group_unit_and_inside_the_flight():
    out = run("""
      const sc = { groups: new Set(['Colt 1', 'Hind 3']), units: new Set(['Colt 1-1', 'Shared']) };
      const u = (n) => ({ name: n });
      const res = {
        group: pkNameWhy({ groupName: '  Colt 1 ', units: [u('')] }, sc),
        unit: pkNameWhy({ groupName: 'Zulu', units: [u('Shared')] }, sc),
        unitDefault: pkNameWhy({ groupName: 'Colt 1', units: [u('')] }, { groups: new Set(), units: sc.units }),
        twice: pkNameWhy({ groupName: 'Zulu', units: [u('A'), u(' A ')] }, sc),
        free: pkNameWhy({ groupName: 'Zulu', units: [u(''), u('')] }, sc),
        trimmed: [pkUnitName({ groupName: ' Zulu ' }, u(''), 0), pkUnitName({ groupName: 'Zulu' }, u(' X '), 1)],
      };
      console.log(JSON.stringify(res));
    """)
    assert out['group'] == 'nameTaken'
    assert out['unit'] == 'unitNameTaken'
    assert out['unitDefault'] == 'unitNameTaken'      # « Colt 1-1 » : le nom donné à l'unité par défaut
    assert out['twice'] == 'unitNameTaken'
    assert out['free'] is None
    assert out['trimmed'] == ['Zulu-1', 'X']


CS = """
  const sc0 = (extra) => Object.assign({ maxNum: 104, cs: new Set() }, extra || {});
  const cs = (units, form, sc, label) => { const w = []; const out = pkCallsigns({ units: units.map(c => ({ callsign: c })) }, sc || sc0(), form, label || 'G', w); return { out: out, w: w }; };
"""


def test_a4_numbers_follow_the_highest_and_replace_bad_ones():
    out = run(CS + """
      const a = cs([null, null], 'number');
      const b = cs([500, null], 'number');
      const c = cs([0, 1.5, -2, 7], 'number');
      console.log(JSON.stringify({ a: a, b: b, c: c }));
    """)
    assert out['a']['out'] == [105, 106] and out['a']['w'] == []
    assert out['b']['out'] == [500, 501]
    assert out['c']['out'] == [105, 106, 107, 7]
    assert [w['args'][1:] for w in out['c']['w']] == [['0', '105'], ['1.5', '106'], ['-2', '107']]


def test_a4_table_without_numbers_is_completed_from_its_name():
    out = run(CS + """
      const a = cs([{ name: 'Colt81' }, null, { name: 'Dodge23' }], 'table');
      console.log(JSON.stringify(a));
    """)
    o = out['out']
    assert o[0] == {'1': 4, '2': 8, '3': 1, 'name': 'Colt81'}
    assert o[1] == {'1': 4, '2': 8, '3': 2, 'name': 'Colt82'}      # même nom et même vol, place = rang + 1
    assert o[2] == {'1': 5, '2': 2, '3': 3, 'name': 'Dodge23'}
    assert out['w'] == []


def test_a4_unrecognised_table_is_replaced_with_a_warning_and_free_flight_search_skips_taken():
    out = run(CS + """
      const taken = new Set(['1:1', '1:2', '1:3', '1:4', '1:5', '1:6', '1:7', '1:8', '1:9', '2:1']);
      const a = cs([{ name: 'Bogus' }, { name: 'Colt10' }, { name: 'Zulu11' }], 'table', sc0({ cs: taken }));
      console.log(JSON.stringify(a));
    """)
    assert out['out'][0] == {'1': 2, '2': 2, '3': 1, 'name': 'Springfield21'}      # Enfield 1 à 9 et Springfield 1 pris
    assert out['out'][1] == {'1': 2, '2': 2, '3': 2, 'name': 'Springfield22'}      # « Colt10 » : pas de chiffre 1-9 pour la place
    assert [w['args'][1] for w in out['w']] == ['Bogus', 'Colt10', 'Zulu11']


def test_a4_package_callsigns_count_as_taken_and_none_left_stops():
    out = run(CS + """
      const a = cs([{ 1: 1, 2: 1, 3: 1, name: 'Enfield11' }, null], 'table');
      const all = new Set(); for (let r = 1; r <= 8; r++) for (let v = 1; v <= 9; v++) all.add(r + ':' + v);
      let stop = null;
      try { cs([null], 'table', sc0({ cs: all })); } catch (e) { stop = !!e.pkNoCallsign; }
      console.log(JSON.stringify({ a: a, stop: stop }));
    """)
    assert out['a']['out'][0]['name'] == 'Enfield11'
    assert out['a']['out'][1] == {'1': 1, '2': 1, '3': 2, 'name': 'Enfield12'}      # le vol de l'indicatif complet précédent
    assert out['stop'] is True
