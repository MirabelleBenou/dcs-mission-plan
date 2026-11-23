"""Tests de tools/gen_threats.py et de data/threats.json : un faux arbre pydcs fabriqué dans un dossier temporaire
(aucune copie de pydcs, aucun import), puis la table livrée et son accord avec la table d'entrée tools/threat_systems.json."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools'))
import gen_threats as gen  # noqa: E402

VEHICLES_PY = '''
class Armor:

    class Tank(unittype.VehicleType):
        id = "Tank"
        detection_range = 9000
        threat_range = 9000


class AirDefence:

    class Big_ln(unittype.VehicleType):
        id = "big ln"
        name = "big launcher"
        detection_range = 0
        threat_range = 25000
        air_weapon_dist = 25000

    class Big_sr(unittype.VehicleType):
        id = "big sr"
        name = "big search radar"
        detection_range = 70000
        threat_range = 0

    class Small_ln(unittype.VehicleType):
        id = "small \\"ln\\""
        detection_range = 10000
        threat_range = 5000

    class Gun(unittype.VehicleType):
        id = "gun"
        detection_range = 0
        threat_range = 2000

    class Radar(unittype.VehicleType):
        id = "radar"
        detection_range = 200000
        threat_range = 0

    class Light(unittype.VehicleType):
        id = "light"
        detection_range = 0
        threat_range = 0

    class Silent(unittype.VehicleType):
        id = "silent"


class Fortification:

    class Bunker(unittype.VehicleType):
        id = "bunker"
        detection_range = 1
        threat_range = 1
'''


def system(sid, pieces, kind='sam', sensor='fire-control', goldwolf=None):
    return {'id': sid, 'name_en': sid.upper(), 'name_fr': sid.upper(), 'kind': kind, 'sensor': sensor,
            'pieces': pieces, 'goldwolf': goldwolf}


def base_table():
    return {'source': 'x', 'excluded': ['light'], 'systems': [
        system('big', ['big ln', 'big sr'], goldwolf={'range_km': 35, 'ceiling_km': 8.5, 'page': 8}),
        system('small', ['small "ln"'], goldwolf={'range_km': 5.5, 'ceiling_km': 3.6, 'page': 9}),
        system('gun', ['gun'], kind='aaa', sensor='shooter'),
        system('radar', ['radar'], kind='radar', sensor='search', goldwolf={'range_km': 220, 'ceiling_km': 20, 'page': 8}),
    ]}


def run(tmp_path, table, name='out.json'):
    root = tmp_path / 'pydcs'
    (root / 'dcs').mkdir(parents=True, exist_ok=True)
    (root / 'dcs' / 'vehicles.py').write_text(VEHICLES_PY, encoding='utf-8')
    tpath = tmp_path / 'table.json'
    tpath.write_text(json.dumps(table), encoding='utf-8')
    out = tmp_path / name
    gen.main(str(root), str(tpath), str(out))
    return out


def systems(tmp_path, table):
    return {s['id']: s for s in json.loads(run(tmp_path, table).read_text(encoding='utf-8'))['systems']}


def test_largest_of_the_pieces_and_the_goldwolf_values(tmp_path):
    s = systems(tmp_path, base_table())
    assert (s['big']['fire_m'], s['big']['detect_m'], s['big']['ceiling_m']) == (25000, 70000, 8500)
    assert s['big']['goldwolf'] == {'range_m': 35000, 'ceiling_m': 8500, 'page': 8}
    assert s['big']['pieces'] == ['big ln', 'big sr']
    assert (s['small']['fire_m'], s['small']['detect_m']) == (5000, 10000)
    assert s['gun']['goldwolf'] is None and s['gun']['ceiling_m'] is None and s['gun']['gap'] is False


def test_km_are_rounded_to_the_metre(tmp_path):
    s = systems(tmp_path, base_table())
    assert s['small']['goldwolf'] == {'range_m': 5500, 'ceiling_m': 3600, 'page': 9}
    t = base_table()
    t['systems'][1]['goldwolf'] = {'range_km': 4.6, 'ceiling_km': 0.0015, 'page': 9}
    g = systems(tmp_path, t)['small']['goldwolf']
    assert g['range_m'] == 4600 and g['ceiling_m'] == 2 and isinstance(g['range_m'], int)


@pytest.mark.parametrize('km,expected', [(27.5, False), (27.6, True), (22.5, False), (22.4, True), (35, True), (25, False)])
def test_gap_on_both_sides_of_10_percent(tmp_path, km, expected):
    t = base_table()
    t['systems'][0]['goldwolf'] = {'range_km': km, 'ceiling_km': 8.5, 'page': 8}
    # ref = fire_m = 25000 : 27.5 km est exactement à 10 %, donc pas un écart
    assert systems(tmp_path, t)['big']['gap'] is expected


def test_gap_of_a_radar_is_measured_on_the_detection_range(tmp_path):
    t = base_table()
    s = systems(tmp_path, t)['radar']
    assert s['fire_m'] == 0 and s['detect_m'] == 200000
    assert s['gap'] is False                      # 220 km contre 200 km : exactement 10 %
    for km, expected in ((221, True), (180, False), (179, True)):
        t['systems'][3]['goldwolf'] = {'range_km': km, 'ceiling_km': 20, 'page': 8}
        assert systems(tmp_path, t)['radar']['gap'] is expected, km


def test_output_layout_and_two_runs_are_byte_identical(tmp_path):
    a = run(tmp_path, base_table(), 'a.json').read_bytes()
    b = run(tmp_path, base_table(), 'b.json').read_bytes()
    assert a == b and a.endswith(b'}\n') and not a.endswith(b'\n\n')
    d = json.loads(a)
    assert list(d) == ['format', 'source', 'sensor_height_m', 'gap_threshold', 'systems']
    assert d['format'] == 'dcs-threats-v1' and d['gap_threshold'] == 0.1
    assert d['sensor_height_m'] == {'search': 10, 'fire-control': 5, 'shooter': 2}
    assert list(d['systems'][0]) == ['id', 'name_en', 'name_fr', 'kind', 'sensor', 'pieces', 'fire_m', 'detect_m', 'ceiling_m', 'goldwolf', 'gap']
    assert [s['id'] for s in d['systems']] == ['big', 'small', 'gun', 'radar']
    assert b'\\u' not in a


def refuse(tmp_path, table, text):
    with pytest.raises(SystemExit) as e:
        run(tmp_path, table)
    assert text in str(e.value)


def test_refuses_a_piece_missing_from_pydcs(tmp_path):
    t = base_table()
    t['systems'][2]['pieces'] = ['gun', 'nowhere']
    refuse(tmp_path, t, 'nowhere')


def test_refuses_a_ranged_type_in_no_system(tmp_path):
    t = base_table()
    t['systems'].pop(2)
    refuse(tmp_path, t, 'gun')


def test_a_type_without_range_needs_no_system_and_a_ranged_one_may_be_excluded(tmp_path):
    t = base_table()
    t['systems'].pop(2)
    t['excluded'].append('gun')
    assert 'gun' not in systems(tmp_path, t)
    # 'silent' n'a aucune portée, 'Tank' et 'bunker' ne sont pas des AirDefence : aucun n'est exigé


def test_refuses_a_duplicate_id(tmp_path):
    t = base_table()
    t['systems'][2]['id'] = 'big'
    refuse(tmp_path, t, 'big')


def test_refuses_an_unknown_kind_or_sensor(tmp_path):
    t = base_table()
    t['systems'][0]['kind'] = 'missile'
    refuse(tmp_path, t, 'missile')
    t = base_table()
    t['systems'][0]['sensor'] = 'eyes'
    refuse(tmp_path, t, 'eyes')


# ---------- la table livrée ----------
DATA = json.loads((ROOT / 'data' / 'threats.json').read_text(encoding='utf-8'))
INPUT = json.loads((ROOT / 'tools' / 'threat_systems.json').read_text(encoding='utf-8'))


def test_delivered_table_format():
    assert DATA['format'] == 'dcs-threats-v1' and DATA['gap_threshold'] == 0.1
    assert DATA['sensor_height_m'] == {'search': 10, 'fire-control': 5, 'shooter': 2}
    assert 'Goldwolf' in DATA['source'] and 'pydcs 1.0.0' in DATA['source']
    assert len(DATA['systems']) == 57
    ids = [s['id'] for s in DATA['systems']]
    assert len(set(ids)) == 57
    for s in DATA['systems']:
        assert s['kind'] in ('sam', 'aaa', 'radar') and s['sensor'] in DATA['sensor_height_m']
        assert isinstance(s['fire_m'], int) and isinstance(s['detect_m'], int) and s['pieces']
        assert (s['goldwolf'] is None) == (s['ceiling_m'] is None)
        if s['goldwolf']:
            assert s['ceiling_m'] == s['goldwolf']['ceiling_m']
        else:
            assert s['gap'] is False
    assert sum(1 for s in DATA['systems'] if s['gap']) == 24


def test_delivered_table_known_values():
    by = {s['id']: s for s in DATA['systems']}
    sa6 = by['sa-6']
    assert (sa6['fire_m'], sa6['detect_m'], sa6['ceiling_m'], sa6['gap']) == (25000, 70000, 8500, True)
    assert sa6['goldwolf'] == {'range_m': 35000, 'ceiling_m': 8500, 'page': 8}
    assert by['sa-22']['gap'] is False
    assert by['1l13']['detect_m'] == 300000 and by['1l13']['gap'] is True


def test_input_and_delivered_tables_agree():
    assert [s['id'] for s in INPUT['systems']] == [s['id'] for s in DATA['systems']]
    for i, d in zip(INPUT['systems'], DATA['systems']):
        for k in ('name_en', 'name_fr', 'kind', 'sensor', 'pieces'):
            assert i[k] == d[k], (i['id'], k)
        g = i.get('goldwolf')
        if g is None:
            assert d['goldwolf'] is None
        else:
            assert d['goldwolf'] == {'range_m': round(g['range_km'] * 1000), 'ceiling_m': round(g['ceiling_km'] * 1000), 'page': g['page']}


def test_no_page_embeds_the_threats_yet():
    for p in (ROOT / 'dist').glob('*.html'):
        assert 'dcs-threats-v1' not in p.read_text(encoding='utf-8'), p.name
