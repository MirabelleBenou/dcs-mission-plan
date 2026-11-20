"""La masse au décollage comme l'éditeur de DCS : tools/gen_aircraft_masses.py (relevés fabriqués), data/aircraft_masses.json (la table livrée)
et payloadTakeoff (lue dans dist/dcs_flight_configurator.html et jouée par node, avec des données fabriquées et la table livrée)."""
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools'))
import gen_aircraft_masses as gen  # noqa: E402

FC = (ROOT / 'dist' / 'dcs_flight_configurator.html').read_text(encoding='utf-8')
DG = (ROOT / 'dist' / 'dcs_datacard_generator.html').read_text(encoding='utf-8')
TABLE = json.loads((ROOT / 'data' / 'aircraft_masses.json').read_text(encoding='utf-8'))
TYPES = json.loads((ROOT / 'data' / 'aircraft_types.json').read_text(encoding='utf-8'))
NODE = shutil.which('node')
needs_node = pytest.mark.skipif(NODE is None, reason='node absent')


# ── le générateur ─────────────────────────────────────────────────────────────
def survey():
    masses = {
        'T-1': {'EmptyWeight': '1000', 'MaxTakeOffWeight': 2000.5, 'AmmoWeight': 0},
        'T-2': {'EmptyWeight': 3000, 'MaxTakeOffWeight': 5000, 'AmmoWeight': '120',
                'props': {'1': {'id': 'Shield', 'control': 'checkbox', 'defValue': True, 'weight': 80, 'weightWhenOn': 20},
                          '2': {'id': 'Tank', 'control': 'comboList', 'defValue': 0,
                                'values': {'1': {'id': 0}, '2': {'id': 1, 'weightWhenOn': 50, 'wdf': 200}}}}},
    }
    opts = {'T-2': {'1': {'id': 'Shield', 'control': 'checkbox', 'defValue': True, 'label': 'Shield', 'weight': 80, 'weightWhenOn': 20, 'playerOnly': True},
                    '2': {'id': 'Tank', 'control': 'comboList', 'defValue': 0, 'label': 'Tank',
                          'values': {'1': {'id': 0, 'dispName': 'Empty'}, '2': {'id': 1, 'dispName': 'Full'}}}}}
    return masses, opts


def test_generator_reads_the_survey():
    out, texts = gen.build(*survey(), ['T-1', 'T-2'])
    assert out['T-1'] == {'empty': 1000, 'max': 2000.5, 'ammo': 0}
    t2 = out['T-2']
    assert (t2['empty'], t2['max'], t2['ammo']) == (3000, 5000, 120)
    assert t2['options'][0] == {'id': 'Shield', 'kind': 'check', 'def': True, 'label': 'Shield', 'weight': 80, 'weightWhenOn': 20}
    assert 'playerOnly' not in t2['options'][0]
    assert t2['options'][1]['values'] == [{'id': 0, 'label': 'Empty'}, {'id': 1, 'label': 'Full', 'weightWhenOn': 50, 'weightDependentOfFuel': 200}]
    assert {(a, b) for a, b, _ in texts} == {('T-1', 'EmptyWeight'), ('T-2', 'AmmoWeight')}


def test_generator_output_is_stable():
    out, _ = gen.build(*survey(), ['T-1', 'T-2'])
    a = gen.dumps(out)
    assert a == gen.dumps(json.loads(a))
    assert ' "T-1": {"ammo": 0, "empty": 1000, "max": 2000.5}' in a


@pytest.mark.parametrize('breaker', ['missing_type', 'unknown_key', 'bad_number', 'labels_differ'])
def test_generator_stops_instead_of_guessing(breaker):
    masses, opts = survey()
    types = ['T-1', 'T-2']
    if breaker == 'missing_type':
        types = ['T-1', 'T-2', 'T-3']
    elif breaker == 'unknown_key':
        masses['T-2']['props']['1']['weightIfOff'] = 5
    elif breaker == 'bad_number':
        masses['T-1']['EmptyWeight'] = 'lourd'
    else:
        opts['T-2']['1']['id'] = 'Other'
    with pytest.raises(SystemExit):
        gen.build(masses, opts, types)


# ── la table livrée ───────────────────────────────────────────────────────────
def test_shipped_table_covers_the_75_types_with_one_shape():
    ids = TYPES['helicopters'] + TYPES['planes']
    assert len(TABLE) == 75 and set(TABLE) == set(ids)
    for ty, e in TABLE.items():
        assert set(e) <= {'empty', 'max', 'ammo', 'options'}, ty
        assert all(isinstance(e[k], (int, float)) and not isinstance(e[k], bool) for k in ('empty', 'max', 'ammo')), ty
        for o in e.get('options', []):
            assert o['kind'] in ('check', 'list') and 'label' in o and 'def' in o, (ty, o['id'])
            if o['kind'] == 'check':
                assert isinstance(o['def'], bool) and ('weight' in o or 'weightWhenOn' in o), (ty, o['id'])
            else:
                assert o['def'] in [v['id'] for v in o['values']], (ty, o['id'])


def test_numbers_written_as_text_by_the_game_are_numbers():
    assert TABLE['Mi-8MT']['empty'] == 8866
    assert not any(isinstance(v, str) for e in TABLE.values() for k, v in e.items() if k != 'options')


# ── la règle ──────────────────────────────────────────────────────────────────
def rule_js():
    i = FC.index('function payloadNum(')
    j = FC.index('// Le plus grand nombre de leurres', i)
    k = FC.index('function payloadDefaults(')
    return FC[k:FC.index('\n}\n', k) + 3] + '\n' + FC[i:j]


def take(cases, masses=None, limits=None):
    body = ('const payloadHas = (o, k) => Object.prototype.hasOwnProperty.call(o, k);\n'
            'const AIRCRAFT_LIMITS = %s;\nfunction payloadPylons() { return []; }\nfunction payloadWeaponMass() { return null; }\n'
            % json.dumps(limits or {'Mi-24P': {'fuel_max': 1701}, 'Bf-109K-4': {'fuel_max': 296}}) + rule_js()
            + '\nconst M = %s;\nconst C = %s;\nconsole.log(JSON.stringify(C.map(c => payloadTakeoff(c[0], c[1], {}, M, c[2]))));'
            % (json.dumps(masses or TABLE), json.dumps(cases)))
    r = subprocess.run([NODE, '-e', body], capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


@needs_node
def test_rule_on_the_shipped_table():
    m24, bf = TABLE['Mi-24P'], TABLE['Bf-109K-4']
    out = take([['Mi-24P', 1701, None], ['Mi-24P', 1701, {'gun': 50}], ['Mi-24P', 1701, {'gun': 0}], ['Mi-24P', 1701, {'props': {'ExhaustScreen': False}}],
                ['Bf-109K-4', 296, None], ['Bf-109K-4', 0, None], ['Bf-109K-4', 148, {'props': {'MW50TankContents': 0}}]])
    base = m24['empty'] + 1701 + m24['ammo']
    assert out[0]['takeoff'] == pytest.approx(base) and out[0]['ammo'] == pytest.approx(m24['ammo'])
    assert out[1]['takeoff'] == pytest.approx(base - m24['ammo'] / 2)
    assert out[2]['takeoff'] == pytest.approx(base - m24['ammo'])
    assert out[3]['takeoff'] == pytest.approx(base - 160) and out[3]['options'] == pytest.approx(-160)
    mw = [o for o in bf['options'] if o['kind'] == 'list'][0]
    wdf = [v for v in mw['values'] if v['id'] == mw['def']][0].get('weightDependentOfFuel', 0)
    assert wdf > 0
    assert out[4]['wdf'] == pytest.approx(wdf) and out[5]['wdf'] == pytest.approx(wdf * 0.1)
    assert out[4]['takeoff'] > out[5]['takeoff'] + 296 - 1


@needs_node
def test_rule_on_made_up_data():
    masses = {'X': {'empty': 1000, 'max': 3000, 'ammo': 100,
                    'options': [{'id': 'A', 'kind': 'check', 'def': True, 'label': 'A', 'weight': 30, 'weightWhenOn': 10},
                                {'id': 'B', 'kind': 'check', 'def': False, 'label': 'B', 'weightWhenOn': 7},
                                {'id': 'L', 'kind': 'list', 'def': 0, 'label': 'L', 'values': [{'id': 0, 'label': 'none'}, {'id': 1, 'label': 'water', 'weightWhenOn': 5, 'weightDependentOfFuel': 40}]}]}}
    limits = {'X': {'fuel_max': 200}}
    out = take([['X', 100, None],                                   # défauts : A coché (+10), B décoché (-0), liste vide
                ['X', 100, {'props': {'A': False}}],                 # A décoché : -30
                ['X', 100, {'props': {'B': True, 'L': 1}}],          # B +7 ; liste +5 ; wdf 40 × min(1, 0,1 + 100/200)
                ['X', 100, {'props': {'A': 'oui', 'L': 9}}],         # valeurs hors règle : les défauts
                ['X', 100, {'gun': 'abc'}],                          # canon illisible : 100
                ['X', 100, {'gun': 250}],                            # canon borné à 100
                ['X', 100, {'gun': -5}],                             # canon borné à 0
                ['Z', 100, None]], masses=masses, limits=limits)     # type inconnu
    assert out[0]['takeoff'] == 1000 + 10 + 100 + 100
    assert out[1]['takeoff'] == 1000 - 30 + 100 + 100
    assert out[2]['takeoff'] == pytest.approx(1000 + 10 + 7 + 5 + 100 + 100 + 40 * 0.6)
    assert out[3]['takeoff'] == 1000 + 10 + 100 + 100
    assert out[4]['takeoff'] == 1210 and out[5]['takeoff'] == 1210 and out[6]['takeoff'] == 1110
    assert out[7]['takeoff'] is None and out[7]['empty'] is None


def test_one_rule_in_both_modules():
    i = FC.index('function payloadNum(')
    j = FC.index('// Le plus grand nombre de leurres', i)
    assert FC[i:j] in DG
