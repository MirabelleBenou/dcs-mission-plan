"""Tests de tools/gen_aircraft_templates.py et de data/aircraft_templates.json : un faux arbre pydcs fabriqué dans un dossier temporaire
(aucune copie de pydcs, aucun import), puis la table livrée et sa copie embarquée dans dist/dcs_hq.html."""
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools'))
import gen_aircraft_templates as gen  # noqa: E402

TASK_PY = '''
class MainTask:
    id = None
    name = None


class CAS(MainTask):
    id = 31
    name = "CAS"


class CAP(MainTask):
    id = 11
    name = "CAP"


class GroundAttack(MainTask):
    id = 32
    name = "Ground Attack"
'''

HELI_PY = '''
class HelicopterType(FlyingType):
    helicopter = True


class Mi_24P(HelicopterType):
    id = "Mi-24P"
    flyable = True
    width = 17.3
    length = 20.953
    fuel_max = 1701
    chaff = 0
    flare = 192

    panel_radio = {
        2: {
            "channels": {
                2: 25.7,
                1: 21.5,
            },
        },
        1: {
            "channels": {
                2: 135,
                1: 127.5,
            },
        },
    }

    property_defaults: Dict[str, Any] = {
        "LeftEngineResource": 90,
        "NS430allow": True,
        "OverrideIFF": None,
    }

    tasks = [task.CAS]
    task_default = task.CAS


class Mi_24V(HelicopterType):
    id = "Mi-24V"
    width = 1
'''

PLANE_PY = '''
class PlaneType(FlyingType):
    pass


class F_4E_45MC(PlaneType):
    id = "F-4E-45MC"
    flyable = True
    width = 11.7
    length = 19.2
    fuel_max = 5510.5
    chaff = 120
    flare = 30
    radio_frequency = 305
    task_default = task.GroundAttack
'''


def faux_pydcs(tmp_path, planes=PLANE_PY, helis=HELI_PY):
    root = tmp_path / 'pydcs'
    (root / 'dcs').mkdir(parents=True)
    (root / 'dcs' / 'task.py').write_text(TASK_PY, encoding='utf-8')
    (root / 'dcs' / 'helicopters.py').write_text(helis, encoding='utf-8')
    (root / 'dcs' / 'planes.py').write_text(planes, encoding='utf-8')
    types = tmp_path / 'types.json'
    types.write_text(json.dumps({'helicopters': ['Mi-24P'], 'planes': ['F-4E-45MC']}), encoding='utf-8')
    return root, types


def run(tmp_path, **kw):
    root, types = faux_pydcs(tmp_path, **kw)
    out = tmp_path / 'out.json'
    gen.main(str(root), str(types), str(out))
    return out


def test_lit_les_classes_en_texte(tmp_path):
    out = run(tmp_path)
    t = json.loads(out.read_text(encoding='utf-8'))
    assert list(t['types']) == ['Mi-24P', 'F-4E-45MC']
    h, p = t['types']['Mi-24P'], t['types']['F-4E-45MC']
    assert h['heli'] is True and p['heli'] is False
    assert h['task_default'] == 'CAS' and p['task_default'] == 'Ground Attack'
    assert h['fuel_max'] == 1701 and p['fuel_max'] == 5510.5
    assert h['radio_frequency'] == 251 and p['radio_frequency'] == 305       # la classe qui ne dit rien prend la valeur de la classe mère de pydcs
    assert h['width'] == 17.3 and h['length'] == 20.953


def test_postes_et_canaux_dans_l_ordre_numerique(tmp_path):
    t = json.loads(run(tmp_path).read_text(encoding='utf-8'))
    pr = t['types']['Mi-24P']['panel_radio']
    assert list(pr) == ['1', '2']
    assert list(pr['1']) == ['1', '2'] and pr['1']['1'] == 127.5 and pr['2']['2'] == 25.7
    assert 'panel_radio' not in t['types']['F-4E-45MC']      # un type sans panel_radio : pas de clé


def test_cle_absente_jamais_null(tmp_path):
    t = json.loads(run(tmp_path).read_text(encoding='utf-8'))
    p = t['types']['F-4E-45MC']
    assert 'property_defaults' not in p
    # un None de pydcs est un « nil » : la clé n'est pas reprise
    assert t['types']['Mi-24P']['property_defaults'] == {'LeftEngineResource': 90, 'NS430allow': True}

    def nulls(o):
        if o is None:
            return True
        if isinstance(o, dict):
            return any(nulls(v) for v in o.values())
        return False
    assert not nulls(t)


def test_deux_rendus_identiques_a_l_octet(tmp_path):
    a = run(tmp_path).read_bytes()
    b = tmp_path / 'b.json'
    gen.main(str(tmp_path / 'pydcs'), str(tmp_path / 'types.json'), str(b))
    assert a == b.read_bytes()


def test_type_introuvable_arrete(tmp_path):
    root, types = faux_pydcs(tmp_path)
    types.write_text(json.dumps({'helicopters': ['Mi-24P', 'Absent'], 'planes': ['F-4E-45MC']}), encoding='utf-8')
    with pytest.raises(SystemExit) as e:
        gen.main(str(root), str(types), str(tmp_path / 'o.json'))
    assert 'Absent' in str(e.value)


def test_poste_de_forme_inconnue_arrete(tmp_path):
    helis = HELI_PY.replace('"channels": {\n                2: 135,\n                1: 127.5,\n            },', '"channels": {\n                2: 135,\n                1: 127.5,\n            },\n            "modulations": {},')
    root, types = faux_pydcs(tmp_path, helis=helis)
    with pytest.raises(SystemExit):
        gen.main(str(root), str(types), str(tmp_path / 'o.json'))


def test_tache_inconnue_arrete(tmp_path):
    root, types = faux_pydcs(tmp_path, planes=PLANE_PY.replace('task.GroundAttack', 'task.Inconnue'))
    with pytest.raises(SystemExit):
        gen.main(str(root), str(types), str(tmp_path / 'o.json'))


# ---- la table livrée ----
TABLE = json.loads((ROOT / 'data' / 'aircraft_templates.json').read_text(encoding='utf-8'))['types']
TYPES = json.loads((ROOT / 'data' / 'aircraft_types.json').read_text(encoding='utf-8'))


def test_table_livree_a_les_types_du_jeu_sans_null():
    assert list(TABLE) == TYPES['helicopters'] + TYPES['planes']
    assert 'null' not in (ROOT / 'data' / 'aircraft_templates.json').read_text(encoding='utf-8')
    assert [k for k, v in TABLE.items() if v['heli']] == TYPES['helicopters']


def test_table_livree_valeurs_connues():
    h = TABLE['Mi-24P']
    assert (h['heli'], h['task_default'], h['fuel_max'], h['chaff'], h['flare'], h['radio_frequency']) == (True, 'CAS', 1701, 0, 192, 251)
    assert (h['length'], h['width']) == (20.953, 17.3)
    assert len(h['property_defaults']) == 14 and list(h['panel_radio']) == ['1', '2']
    assert len(h['panel_radio']['1']) == 20 and h['panel_radio']['1']['1'] == 127.5
    m = TABLE['Mi-8MT']
    assert (m['heli'], m['task_default'], m['fuel_max'], m['flare'], m['width']) == (True, 'Transport', 1929, 128, 21.33)
    assert len(m['property_defaults']) == 9
    f = TABLE['F-4E-45MC']
    assert (f['heli'], f['task_default'], f['fuel_max'], f['chaff'], f['flare'], f['radio_frequency'], f['width']) == (False, 'CAP', 5510.5, 120, 30, 305, 11.7)
    assert len(f['property_defaults']) == 23
    assert len(f['panel_radio']['1']) == 18 and f['panel_radio']['1']['1'] == 305


def test_postes_d_accord_avec_la_table_des_radios():
    radios = json.loads((ROOT / 'data' / 'aircraft_radios.json').read_text(encoding='utf-8'))['types']
    for ty, v in TABLE.items():
        assert {k: len(c) for k, c in v.get('panel_radio', {}).items()} == {k: n for k, n in radios[ty].items()}, ty


def test_copie_embarquee_dans_hq_egale_au_fichier():
    html = ROOT / 'dist' / 'dcs_hq.html'
    if not html.exists():
        pytest.skip('dist/dcs_hq.html absent')
    m = re.search(r'/\* AIRCRAFT_TEMPLATES:BEGIN \*/\n[^\n]*\nconst AIRCRAFT_TEMPLATES = (.*);\n/\* AIRCRAFT_TEMPLATES:END \*/', html.read_text(encoding='utf-8'))
    assert m and json.loads(m.group(1)) == TABLE


def test_le_script_se_lance_en_ligne_de_commande(tmp_path):
    root, types = faux_pydcs(tmp_path)
    out = tmp_path / 'cli.json'
    r = subprocess.run([sys.executable, '-B', str(ROOT / 'tools' / 'gen_aircraft_templates.py'), str(root), str(types), str(out)], capture_output=True, text=True)
    assert r.returncode == 0 and '2 types' in r.stdout
