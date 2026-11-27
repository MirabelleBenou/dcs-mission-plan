"""Les balises des terrains (Datacard Generator) : la pièce airfield_beacons.json (tools/gen_airfield_beacons.py), sa vérification au build, le calcul des lignes du bloc
« Balises — terrains » (lu dans dist/dcs_datacard_generator.html et joué par node, sur le petit jeu dcs-navaids-v1 de tests/dg_balises_navaids/), puis le bloc dans le shell construit
(chromium, aucun réseau, une fenêtre de 1 280 × 800) ; les contrôles passent par le DOM, jamais par une capture."""
import importlib.util
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SET = Path(__file__).resolve().parent / 'dg_balises_navaids'
NODE = shutil.which('node')
needs_node = pytest.mark.skipif(NODE is None, reason='node absent')
CHROMIUM = Path('/opt/pw-browsers/chromium')
try:
    import playwright.sync_api  # noqa: F401
    HAS_PW = CHROMIUM.exists()
except ImportError:
    HAS_PW = False
needs_pw = pytest.mark.skipif(not HAS_PW, reason='playwright ou chromium absent')
SHELL = 'file://' + str(ROOT / 'dist' / 'dcs_mission_plan.html')
SEED = "(() => { try { if (localStorage.getItem('lang_v1') === null) localStorage.setItem('lang_v1', '@@'); } catch (e) {} })();"
COMMIT = '0123456789abcdef0123456789abcdef01234567'

# La pièce attendue du petit jeu : les théâtres qui ont des balises connues (Nevada : toutes nulles, absent), leurs seuls aérodromes à balises (Charlie : aucune ; Delta : null),
# les balises brutes dans l'ordre du fichier ; JSON compact, clés triées, une fin de ligne
EXPECTED = (
    '{"format":"dcs-airfield-beacons-v1","source":{"commit":"' + COMMIT + '","repo":"MirabelleBenou/dcs-airfield-charts"},"theatres":{'
    '"Caucasus":{"Echo":[["HOMER","E",400000,null,null]]},'
    '"Syria":{"Alpha":[["ILS_GLIDESLOPE","IAA",110100000,null,null],["ILS_LOCALIZER","IAB",110100000,null,"27"],["ILS_LOCALIZER","IAA",110100000,null,"09"],'
    '["ILS_GLIDESLOPE","",108500000,null,"27"],["AIRPORT_HOMER","AL",346500,null,null],["TACAN","ALP",null,0,null],["VORTAC","ALV",113700000,84,null],'
    '["VOR_DME","ALD",112600000,null,null],["DME","",null,45,null]],'
    '"Bravo":[["PRMG_GLIDESLOPE","BR",null,22,null],["PRMG_LOCALIZER","BR",null,22,"13"],["RSBN","BRV",null,36,null],["ILS_FAR_HOMER","B",625000,null,"13"],'
    '["ILS_NEAR_HOMER","R",303000,null,"13"],["AIRPORT_HOMER_WITH_MARKER","BM",800000,null,null],["HOMER","BH",1050000,null,null],["AIRPORT_TACAN","BT",null,99,null],'
    '["VOR","BV",114300000,null,null]]}}}\n')


def gen(tmp_path, *extra):
    out = tmp_path / 'airfield_beacons.json'
    r = subprocess.run([sys.executable, '-B', str(ROOT / 'tools' / 'gen_airfield_beacons.py'), str(SET), '--commit', COMMIT, '--out', str(out), *extra],
                       capture_output=True, text=True, timeout=60)
    return r, out


# ---------- la pièce, sans navigateur ----------

def test_the_piece_is_regenerated_byte_for_byte(tmp_path):
    r, out = gen(tmp_path)
    assert r.returncode == 0, r.stderr
    assert out.read_bytes() == EXPECTED.encode('utf-8')
    first = out.read_bytes()
    r, out = gen(tmp_path)
    assert r.returncode == 0 and out.read_bytes() == first          # deux fabrications de suite : le même fichier


def test_the_generator_needs_a_full_commit(tmp_path):
    out = tmp_path / 'x.json'
    r = subprocess.run([sys.executable, '-B', str(ROOT / 'tools' / 'gen_airfield_beacons.py'), str(SET), '--commit', 'abc123', '--out', str(out)],
                       capture_output=True, text=True, timeout=60)
    assert r.returncode != 0 and '[ERREUR]' in r.stderr and not out.exists()


def test_the_generator_refuses_an_unknown_beacon_type(tmp_path):
    d = tmp_path / 'navaids'
    d.mkdir()
    s = json.loads((SET / 'Syria.json').read_text(encoding='utf-8'))
    s['airdromes'][0]['beacons'][0]['type'] = 'NDB_UNKNOWN'
    (d / 'Syria.json').write_text(json.dumps(s), encoding='utf-8')
    r = subprocess.run([sys.executable, '-B', str(ROOT / 'tools' / 'gen_airfield_beacons.py'), str(d), '--commit', COMMIT, '--out', str(tmp_path / 'x.json')],
                       capture_output=True, text=True, timeout=60)
    assert r.returncode != 0 and 'NDB_UNKNOWN' in r.stderr


def build_module():
    spec = importlib.util.spec_from_file_location('dg_build_for_test', ROOT / 'build_datacard_generator.py')
    mod = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(ROOT))
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.path.remove(str(ROOT))
    return mod


@pytest.fixture(scope='module')
def dgb():
    return build_module()


def check(dgb, tmp_path, piece):
    p = tmp_path / 'airfield_beacons.json'
    p.write_text(json.dumps(piece, ensure_ascii=False), encoding='utf-8')
    dgb.BEACONS_PATH = str(p)
    return dgb.airfield_beacons(dgb.airfield_facts())


def real_piece():
    return json.loads((ROOT / 'airfield_beacons.json').read_text(encoding='utf-8'))


def test_the_build_accepts_the_piece_of_the_repository(dgb, tmp_path):
    piece = real_piece()
    assert piece['format'] == 'dcs-airfield-beacons-v1' and re.fullmatch(r'[0-9a-f]{40}', piece['source']['commit'])
    assert check(dgb, tmp_path, piece) == piece['theatres']
    facts = json.loads((ROOT / 'airfield_facts.json').read_text(encoding='utf-8'))['theatres']
    for th, table in piece['theatres'].items():           # chaque nom d'aérodrome à balises est un aérodrome du théâtre
        names = {a[0] for a in facts[th]}
        assert set(table) <= names, th


@pytest.mark.parametrize('case', ['format', 'theatre', 'name', 'type', 'value'])
def test_the_build_refuses_a_wrong_piece(dgb, tmp_path, case):
    piece = real_piece()
    th = next(iter(piece['theatres']))
    name = next(iter(piece['theatres'][th]))
    if case == 'format':
        piece['format'] = 'dcs-airfield-beacons-v0'
    elif case == 'theatre':
        piece['theatres']['Atlantis'] = piece['theatres'][th]
    elif case == 'name':
        piece['theatres'][th]['Not An Airfield'] = piece['theatres'][th][name]
    elif case == 'type':
        piece['theatres'][th][name] = [['NDB_UNKNOWN', 'X', 400000, None, None]]
    else:
        piece['theatres'][th][name] = [['HOMER', 'X', '400 kHz', None, None]]
    with pytest.raises(SystemExit) as e:
        check(dgb, tmp_path, piece)
    assert str(e.value).startswith('[ERREUR] airfield_beacons.json')


def test_the_piece_goes_into_the_datacard_generator_only():
    dg = (ROOT / 'dist' / 'dcs_datacard_generator.html').read_text(encoding='utf-8')
    compact = json.dumps(real_piece()['theatres'], ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
    assert dg.count('const AIRFIELD_BEACONS = ' + compact + ';') == 1
    for other in ('dcs_route_planner.html', 'dcs_flight_configurator.html', 'dcs_briefing_generator.html', 'dcs_hq.html', 'dcs_recon_station.html'):
        assert 'AIRFIELD_BEACONS' not in (ROOT / 'dist' / other).read_text(encoding='utf-8'), other


# ---------- le calcul des lignes, joué par node sur le petit jeu ----------

DG = (ROOT / 'dist' / 'dcs_datacard_generator.html').read_text(encoding='utf-8')


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


def const(name):
    m = re.search(r'^const ' + name + r' = .*;$', DG, re.M)
    assert m, name
    return m.group(0)


def lines(fields, lang, theatre='Syria'):
    piece = json.loads(EXPECTED)['theatres']
    names = sorted({n for th in piece.values() for n in th} | {'Charlie', 'Delta'})
    T = {'fr': {'dc.bt.ndb': 'NDB', 'dc.bt.far': 'NDB extérieur', 'dc.bt.near': 'NDB intérieur', 'dc.role.dep': 'DEP', 'dc.role.arr': 'ARR', 'dc.role.alt': 'ALT'},
         'en': {'dc.bt.ndb': 'NDB', 'dc.bt.far': 'Outer NDB', 'dc.bt.near': 'Inner NDB', 'dc.role.dep': 'DEP', 'dc.role.arr': 'ARR', 'dc.role.alt': 'ALT'}}[lang]
    src = '\n'.join([
        'const AIRFIELD_BEACONS = ' + json.dumps(piece) + ';',
        'const T = ' + json.dumps(T) + '; function t(k) { return T[k]; }',
        'const NAMES = ' + json.dumps(names) + ';',
        'function dgTheatre() { return ' + json.dumps(theatre) + '; }',
        "function str(v) { return v == null ? '' : String(v); }",
        "function afFind(name) { const n = str(name).trim(); return NAMES.indexOf(n) >= 0 ? [n] : null; }",
        const('BCN_ORDER'), const('BCN_GS'), const('BCN_LOC'),
        fn('bcnLinesOf'), fn('bcnFreq'), fn('bcnValue'), fn('bcnType'), fn('dgBeaconLines'),
        'const c = { fields: ' + json.dumps([{'role': r, 'icao': '', 'name': n, 'runway': '', 'frequency': ''} for r, n in fields]) + ' };',
        'console.log(JSON.stringify(dgBeaconLines(c).map(l => [l.fi, l.role, l.name, l.type, l.cs, l.value, l.rwy])));',
    ])
    r = subprocess.run([NODE, '-e', src], capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


@needs_node
def test_the_lines_of_the_block_on_the_small_set():
    out = lines([('dep', ' Alpha '), ('arr', 'Bravo'), ('alt', 'Alpha'), ('', 'Charlie'), ('', 'Delta'), ('alt', 'Zulu')], 'fr')
    assert out == [
        # Alpha (DEP ; listé une fois, sous son premier rôle) : NDB, TACAN, VOR/DME, DME, VORTAC, puis les ILS par piste ; à piste égale, l'indicatif vide d'abord
        [0, 'DEP', 'Alpha', 'NDB', 'AL', '346.5 kHz', ''],               # un kHz fractionnaire
        [0, 'DEP', 'Alpha', 'TACAN', 'ALP', '—', ''],                    # canal 0 : absent ; sans fréquence : « — »
        [0, 'DEP', 'Alpha', 'VOR/DME', 'ALD', '112.60', ''],
        [0, 'DEP', 'Alpha', 'DME', '', '45', ''],                        # sans fréquence : le canal
        [0, 'DEP', 'Alpha', 'VORTAC', 'ALV', '113.70 · 84', ''],
        [0, 'DEP', 'Alpha', 'ILS', 'IAA', '110.10', '09'],               # la descente sans piste rejoint l'alignement de même indicatif
        [0, 'DEP', 'Alpha', 'ILS', '', '108.50', '27'],                  # une descente sans alignement fait sa ligne
        [0, 'DEP', 'Alpha', 'ILS', 'IAB', '110.10', '27'],               # un alignement seul
        # Bravo (ARR) : HOMER, AIRPORT_HOMER_WITH_MARKER, NDB extérieur et intérieur, RSBN, PRMG assemblé, AIRPORT_TACAN, VOR
        [1, 'ARR', 'Bravo', 'NDB', 'BH', '1050 kHz', ''],
        [1, 'ARR', 'Bravo', 'NDB', 'BM', '800 kHz', ''],
        [1, 'ARR', 'Bravo', 'NDB extérieur', 'B', '625 kHz', '13'],
        [1, 'ARR', 'Bravo', 'NDB intérieur', 'R', '303 kHz', '13'],
        [1, 'ARR', 'Bravo', 'RSBN', 'BRV', '36', ''],
        [1, 'ARR', 'Bravo', 'PRMG', 'BR', '22', '13'],                   # la descente rejoint l'alignement de même canal ; la piste vient de l'alignement
        [1, 'ARR', 'Bravo', 'TACAN', 'BT', '99', ''],
        [1, 'ARR', 'Bravo', 'VOR', 'BV', '114.30', ''],
    ]


@needs_node
def test_the_english_types_and_a_theatre_without_beacons():
    en = lines([('dep', 'Bravo')], 'en')
    assert [x[3] for x in en] == ['NDB', 'NDB', 'Outer NDB', 'Inner NDB', 'RSBN', 'PRMG', 'TACAN', 'VOR']
    assert lines([('', 'Echo')], 'fr', 'Caucasus') == [[0, '', 'Echo', 'NDB', 'E', '400 kHz', '']]      # sans rôle : vide
    assert lines([('dep', 'Alpha')], 'fr', 'Nevada') == []
    assert lines([('dep', 'Charlie'), ('arr', 'Zulu')], 'fr') == []


# ---------- le bloc, dans le shell construit ----------

@pytest.fixture(scope='module')
def browser():
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        br = p.chromium.launch(executable_path=str(CHROMIUM), args=['--no-sandbox'])
        yield br
        br.close()


def open_dg(br, lang='fr'):
    ctx = br.new_context(viewport={'width': 1280, 'height': 800}, locale=lang + '-' + lang.upper())
    ctx.add_init_script(SEED.replace('@@', lang))
    ctx.route('**/*', lambda r: r.continue_() if r.request.url.startswith(('file:', 'data:', 'blob:')) else r.abort())
    pg = ctx.new_page()
    pg.errs = []
    pg.on('pageerror', lambda e: pg.errs.append(str(e)[:200]))
    pg.goto(SHELL, wait_until='commit')
    pg.wait_for_function("() => typeof window.MP_WORK_EXAMPLE === 'function' && !!document.getElementById('card-dg')", timeout=60000)
    pg.wait_for_timeout(1300)
    pg.evaluate("() => window.MP_WORK_EXAMPLE('fl')")
    pg.wait_for_timeout(900)
    pg.locator('#card-dg').click()
    pg.wait_for_selector('#iframe-dg', state='attached')
    pg.wait_for_timeout(2600)
    fr = pg.query_selector('#iframe-dg').content_frame()
    fr.wait_for_function("() => !!document.querySelector('#preview .dc-page')", timeout=30000)
    return ctx, pg, fr


ROWS = "() => [...document.querySelectorAll('#preview section.dc-block[data-block=\"beacons\"] tbody tr')].map(tr => [...tr.children].map(td => td.textContent))"


@needs_pw
def test_the_example_has_the_beacons_of_its_airfield(browser):
    ctx, pg, fr = open_dg(browser)
    try:
        fields = fr.evaluate("() => curCard().fields.map(f => [f.role, f.name])")
        th = fr.evaluate("() => dgTheatre()")
        rows = fr.evaluate(ROWS)
        raw = real_piece()['theatres'][th]
        known = [(r, n) for r, n in fields if n in raw]
        assert known, fields
        first = known[0][1]
        assert {n for r, n in known} == {first}                    # l'exemple : un seul aérodrome à balises (DEP et ALT)
        assert rows and all(x[0] == 'DEP' and x[1] == first for x in rows)
        gs = [b for b in raw[first] if b[0].endswith('_GLIDESLOPE')]
        assert len(rows) == len(raw[first]) - len(gs)              # chaque descente a rejoint son alignement
        assert sorted(x[3] for x in rows) == sorted(b[1] for b in raw[first] if not b[0].endswith('_GLIDESLOPE'))
        head = fr.evaluate("() => [...document.querySelectorAll('#preview section.dc-block[data-block=\"beacons\"] thead th')].map(th => th.textContent)")
        assert head == ['', 'TERRAIN', 'TYPE', 'INDICATIF', 'FRÉQ · CANAL', 'PISTE']
        assert fr.evaluate("() => document.querySelector('#preview section.dc-block[data-block=\"beacons\"] .dc-bh').textContent") == 'BALISES — TERRAINS'
        # le bloc suit les points de référence, sur la page qui les porte
        order = fr.evaluate("() => [...document.querySelectorAll('#preview .dc-page')].map(p => [...p.querySelectorAll('.dc-block')].map(b => b.dataset.block))")
        page = next(p for p in order if 'refs' in p)
        assert page.index('beacons') == page.index('refs') + 1
        assert pg.errs == []
    finally:
        ctx.close()


@needs_pw
def test_a_theatre_without_beacons_has_no_block(browser):
    ctx, pg, fr = open_dg(browser)
    try:
        assert fr.evaluate(ROWS)
        fr.evaluate("() => { const s = document.getElementById('theatre'); s.value = 'Nevada'; s.dispatchEvent(new Event('change', { bubbles: true })); }")
        pg.wait_for_timeout(600)
        assert fr.evaluate("() => document.querySelectorAll('#preview [data-block=\"beacons\"]').length") == 0
        fr.evaluate("() => { const s = document.getElementById('theatre'); s.value = 'Syria'; s.dispatchEvent(new Event('change', { bubbles: true })); }")
        pg.wait_for_timeout(600)
        assert fr.evaluate(ROWS)                                   # le théâtre revient : le bloc aussi (le plan en cache suit le théâtre)
        assert pg.errs == []
    finally:
        ctx.close()
