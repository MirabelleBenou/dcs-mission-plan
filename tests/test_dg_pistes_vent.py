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


# ---------- la note (afWarnText) ----------
WARN_PRELUDE = PRELUDE + '\n' + '\n'.join([
    "const AF_UI = { other: new Set() };",
    "const ROWS = { Akrotiri: AKR, Nellis: NEL, Naqoura: ['Naqoura', 'A', 0, []], Solo: ['Solo', 'A', 0, ['10']] };",
    "function afFind(n) { return Object.prototype.hasOwnProperty.call(ROWS, n) ? ROWS[n] : null; }",
    "Object.assign(T, { 'f.rwy.warn': 'W {n} {rwy} {best}', 'f.rwy.warn1': 'W1 {n} {rwy}' });",
    "function t(k, v) { let s = T[k]; if (v) Object.keys(v).forEach(x => { s = s.split('{' + x + '}').join(String(v[x])); }); return s; }",
    fn('afWarnText'),
    "const W = (name, rwy, wind) => afWarnText({ name: name, runway: rwy }, card(wind));",
])


@needs_node
def test_warning_text_states():
    out = run_w("""console.log(JSON.stringify({
      tail: W('Akrotiri', '10', '280/08'), into: W('Akrotiri', '28', '280/08'), one: W('Akrotiri', '28', '190/10'),
      trimmed: W('Akrotiri', ' 10 ', '280/08'), notEnd: W('Akrotiri', '99', '280/08'), empty: W('Akrotiri', '', '280/08'),
      free: W('Zzz', '10', '280/08'), blank: W('', '', '280/08'), noRwy: W('Naqoura', '10', '280/08'), calm: W('Akrotiri', '10', 'CALME'),
      solo: W('Solo', '10', '280/08'), nellis: W('Nellis', '21R', '030/15') }));""")
    assert out['tail'] == 'W 8 10 28'
    assert out['into'] == '' and out['notEnd'] == '' and out['empty'] == ''
    assert out['one'] == 'W 1 28 10'
    assert out['trimmed'] == out['tail']               # Q2 : sans les espaces de tête et de fin
    assert out['free'] == '' and out['blank'] == '' and out['noRwy'] == '' and out['calm'] == ''      # Q1 : aucune note hors rangée à liste des sens
    assert out['solo'] == 'W1 8 10'                    # le sens est lui-même la recommandée
    assert out['nellis'] == 'W 15 21R 03L'


def run_w(body):
    r = subprocess.run([NODE, '-e', WARN_PRELUDE + '\n' + body], capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


# ---------- Q1 : la note suit l'état de sa rangée (DOM, dans le shell) ----------
CHROMIUM = Path('/opt/pw-browsers/chromium')
try:
    import playwright.sync_api  # noqa: F401
    HAS_PW = CHROMIUM.exists()
except ImportError:
    HAS_PW = False


@pytest.mark.skipif(not HAS_PW, reason='playwright ou chromium absent')
def test_stale_note_is_removed_when_the_row_loses_its_runway_list():
    from playwright.sync_api import sync_playwright
    shell = 'file://' + str(ROOT / 'dist' / 'dcs_mission_plan.html')
    with sync_playwright() as p:
        br = p.chromium.launch(executable_path=str(CHROMIUM), args=['--no-sandbox'])
        try:
            def fresh():
                pg = br.new_page(viewport={'width': 1280, 'height': 900})
                pg.route('**/*', lambda r: r.continue_() if r.request.url.startswith(('file:', 'data:', 'blob:')) else r.abort())
                pg.goto(shell, wait_until='commit'); pg.wait_for_timeout(2500)
                pg.evaluate("MP_WORK_EXAMPLE('fl')"); pg.wait_for_timeout(2500)
                pg.evaluate("MP_OPEN_MODULE('dg')"); pg.wait_for_timeout(2500)
                return pg, pg.frames[1]
            wind = """(w)=>{const e=document.querySelector('[data-path="weather.wind"]'); e.value=w; e.dispatchEvent(new Event('input',{bubbles:true}));}"""
            pick = """(v)=>{const s=document.querySelector('select[data-af="0"]'); s.value=v; s.dispatchEvent(new Event('input',{bubbles:true})); s.dispatchEvent(new Event('change',{bubbles:true}));}"""
            count = "()=>document.querySelectorAll('#editor [data-afwarn=\"0\"]').length"
            for gesture in ('@other', '', 'Naqoura'):
                pg, f = fresh()
                f.evaluate(wind, '280/08'); pg.wait_for_timeout(150)
                assert f.evaluate(count) == 1
                f.evaluate(pick, gesture); pg.wait_for_timeout(200)
                assert f.evaluate(count) == 0, gesture
                for w in ('100/12', '280/08'):
                    f.evaluate(wind, w); pg.wait_for_timeout(150)
                    assert f.evaluate(count) == 0, (gesture, w)
                f.evaluate(pick, 'Akrotiri'); pg.wait_for_timeout(200)
                assert f.evaluate("()=>curCard().fields[0].runway") == '28' and f.evaluate(count) == 0
                f.evaluate("()=>{const s=document.querySelector('select[data-afr=\"0\"]'); s.value='10'; s.dispatchEvent(new Event('input',{bubbles:true})); s.dispatchEvent(new Event('change',{bubbles:true}));}"); pg.wait_for_timeout(200)
                assert f.evaluate(count) == 1
                assert f.evaluate("()=>document.querySelector('#editor [data-afwarn=\"0\"]').getAttribute('role')") == 'status'
                pg.close()
        finally:
            br.close()
