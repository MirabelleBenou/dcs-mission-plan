"""La piste et le vent (Datacard Generator) : la règle afRwyModel / afPickEnd / afRwyLabel, lue dans dist/dcs_datacard_generator.html et jouée par node
(déclinaisons de l'exemple d'attendus fournies, aucune page, aucun réseau)."""
import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
DG = (ROOT / 'dist' / 'dcs_datacard_generator.html').read_text(encoding='utf-8')
NODE = shutil.which('node')
needs_node = pytest.mark.skipif(NODE is None, reason='node absent')


def fn(name):
    m = re.search(r'^function ' + name + r'\(', DG, re.M)
    assert m, name
    i = DG.index('{', m.start())
    d = 0
    for k in range(i, len(DG)):
        d += (DG[k] == '{') - (DG[k] == '}')
        if d == 0:
            return DG[m.start():k + 1]
    raise AssertionError(name)


PRELUDE = '\n'.join([
    "const str = v => v == null ? '' : String(v);",
    "const DECL = { A: 3.21, N: 14.17, K: 5.07 };",
    "function magVar(lat, lon, y) { return DECL[lat]; }",
    "function dgNavYear(c) { return { y: 1989.22 }; }",
    "const T = { 'f.rwy.rec': 'recommandée', 'f.rwy.tail': 'vent arrière' }; function t(k) { return T[k]; }",
    fn('afEnds'), fn('afWindVec'), fn('afRwyModel'), fn('afPickEnd'), fn('afRwyLabel'),
    "const AKR = ['Akrotiri', 'A', 0, ['10/28']], NEL = ['Nellis', 'N', 0, ['03L/21R', '03R/21L']], KUT = ['Kutaisi', 'K', 0, ['25/07']];",
    "const card = w => ({ weather: { wind: w } });",
    "const show = (row, w) => { const c = card(w), m = afRwyModel(row, c); return { pick: afPickEnd(row, c), labels: afEnds(row).map(e => afRwyLabel(e, m)), tail: m ? m.ends.map(x => [x.end, x.tail]) : null }; };",
])


def run(body):
    r = subprocess.run([NODE, '-e', PRELUDE + '\n' + body], capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


@needs_node
def test_rule_on_the_expected_values():
    out = run("""console.log(JSON.stringify({
      a1: show(AKR, '280/08'), a2: show(AKR, '100/12'), a3: show(AKR, '190/10'), a4: show(AKR, '250/12G20'),
      n1: show(NEL, '030/15'), n2: show(NEL, '200/06'), k1: show(KUT, '250/10') }));""")
    assert out['a1']['pick'] == '28' and out['a1']['labels'] == ['10 · vent arrière', '28 · recommandée']
    assert out['a1']['tail'] == [['10', 8], ['28', -8]]
    assert out['a2']['pick'] == '10' and out['a2']['labels'] == ['10 · recommandée', '28 · vent arrière']
    assert out['a3']['pick'] == '10' and out['a3']['labels'] == ['10 · recommandée', '28 · vent arrière']      # 0,56 kt arrière : arrondi à 1
    assert out['a3']['tail'] == [['10', -1], ['28', 1]]
    assert out['a4']['pick'] == '28' and out['a4']['labels'] == ['10 · vent arrière', '28 · recommandée']      # rafales ignorées
    assert out['n1']['pick'] == '03L'                                                        # égalité : le premier
    assert out['n1']['labels'] == ['03L · recommandée', '21R · vent arrière', '03R', '21L · vent arrière']
    assert out['n2']['pick'] == '21R' and out['n2']['labels'] == ['03L · vent arrière', '21R · recommandée', '03R · vent arrière', '21L']
    assert out['k1']['pick'] == '25' and out['k1']['labels'] == ['25 · recommandée', '07 · vent arrière']


@needs_node
def test_no_readable_wind_gives_no_mark():
    out = run("""const r = {}; ['VRB/05', '000/00', 'CALME', 'CALM', '', 'abc', null].forEach(w => { r[String(w)] = show(AKR, w); }); console.log(JSON.stringify(r));""")
    for w, v in out.items():
        assert v['pick'] == '10' and v['labels'] == ['10', '28'] and v['tail'] is None, w         # sans vent lisible : le premier sens, les sens seuls
