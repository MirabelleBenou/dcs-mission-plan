"""HQ applique un paquet : le payload écrit garde de l'unité cible ce que le Flight Configurator ne règle pas (bande du canon, armes interdites).
pkMergePayload est lue dans dist/dcs_hq.html et jouée par node ; données fabriquées."""
import json
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


def merge(cases):
    i = HQ.index("const PK_FC_KEYS = ")
    line = HQ[i:HQ.index('\n', i)]
    body = line + '\n' + fn('pkMergePayload') + '\nconst C = %s;\nconsole.log(JSON.stringify(C.map(c => pkMergePayload(c[0], c[1]))));' % json.dumps(cases)
    r = subprocess.run([NODE, '-e', body], capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


GUN = {'1': {'CLSID': '{9BFD8C90-F7AE-4e90-833B-BFD0CED0E536}'}}
RESTR = {'3': {'1': '{5CE2FF2A-645A-4197-B48D-8720AC69394F}'}}


def test_the_five_cases_of_the_piece():
    cases = [
        [{'ammo_type': 5, 'chaff': 30, 'flare': 30, 'fuel': 1000, 'gun': 10, 'pylons': {}},
         {'chaff': 60, 'flare': 60, 'fuel': 2000, 'gun': 100, 'pylons': GUN}],
        [{'ammo_type': 2, 'chaff': 30, 'flare': 30, 'fuel': 1000, 'gun': 10, 'pylons': {'1': {'CLSID': 'x'}}, 'restricted': RESTR},
         {'chaff': 60, 'flare': 60, 'fuel': 2500, 'gun': 50, 'pylons': {}}],
        [{'chaff': 1, 'flare': 1, 'fuel': '900', 'gun': 1, 'pylons': {}, 'restricted': {}},
         {'chaff': 0, 'flare': 60, 'fuel': 500, 'gun': 100, 'pylons': {}}],
        [{'ammo_type': 1, 'chaff': 0, 'flare': 192, 'fuel': 1000, 'gun': 100, 'pylons': {}, 'restricted': {'2': {'1': '{APU-60-1_R_60M}'}}},
         {'ammo_type': 3, 'chaff': 0, 'flare': 96, 'fuel': 1200, 'gun': 100, 'pylons': {}, 'restricted': {}}],
        [{'chaff': 0, 'flare': 192, 'fuel': 1000, 'gun': 100, 'pylons': {}},
         {'ammo_type': 1, 'chaff': 0, 'flare': 192, 'fuel': 1000, 'gun': 100, 'pylons': {}}],
    ]
    out = merge(cases)
    assert out[0] == {'ammo_type': 5, 'chaff': 60, 'flare': 60, 'fuel': 2000, 'gun': 100, 'pylons': GUN}
    assert out[1] == {'ammo_type': 2, 'chaff': 60, 'flare': 60, 'fuel': 2500, 'gun': 50, 'pylons': {}, 'restricted': RESTR}
    assert out[2] == {'chaff': 0, 'flare': 60, 'fuel': 500, 'gun': 100, 'pylons': {}, 'restricted': {}}
    assert out[3] == {'ammo_type': 1, 'chaff': 0, 'flare': 96, 'fuel': 1200, 'gun': 100, 'pylons': {}, 'restricted': {'2': {'1': '{APU-60-1_R_60M}'}}}
    assert out[4] == {'ammo_type': 1, 'chaff': 0, 'flare': 192, 'fuel': 1000, 'gun': 100, 'pylons': {}}


def test_null_or_unreadable_target_gives_the_package_as_is():
    pk = {'chaff': 0, 'fuel': 1, 'pylons': {}}
    out = merge([[None, pk], [[1, 2], pk], ['x', pk]])
    assert out == [pk, pk, pk]


def test_unknown_key_of_the_target_is_kept_and_package_key_is_added():
    out = merge([[{'fuel': 1, 'strange': {'a': [1, 2]}, 'restricted': {}}, {'fuel': 5, 'ammo_type': 4, 'restricted': RESTR}]])
    # la clé inconnue et restricted de la cible restent ; ammo_type du paquet, absent de la cible, s'ajoute
    assert out[0] == {'fuel': 5, 'strange': {'a': [1, 2]}, 'restricted': {}, 'ammo_type': 4}


def test_pylons_are_replaced_whole_and_arguments_are_untouched():
    tgt = {'pylons': {'1': {'CLSID': 'a'}, '2': {'CLSID': 'b'}}, 'ammo_type': 2}
    pk = {'pylons': {'1': {'CLSID': 'c'}}, 'fuel': 3}
    i = HQ.index("const PK_FC_KEYS = ")
    line = HQ[i:HQ.index('\n', i)]
    body = (line + '\n' + fn('pkMergePayload') + '\nconst t = %s, p = %s;\nconst b = JSON.stringify([t, p]);\nconst r = pkMergePayload(t, p);\n'
            'r.pylons["1"].CLSID = "zz"; r.ammo_type = 9;\nconsole.log(JSON.stringify({ r: pkMergePayload(t, p), same: b === JSON.stringify([t, p]) }));' % (json.dumps(tgt), json.dumps(pk)))
    res = subprocess.run([NODE, '-e', body], capture_output=True, text=True, timeout=60)
    assert res.returncode == 0, res.stderr
    o = json.loads(res.stdout)
    assert o['r'] == {'pylons': {'1': {'CLSID': 'c'}}, 'ammo_type': 2, 'fuel': 3}
    assert o['same']
