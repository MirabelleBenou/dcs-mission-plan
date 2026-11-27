"""Les caps suivent le nord du jeu : le cap Vrai affiché ou saisi est le cap grille (depuis le nord de la grille du théâtre),
au Route Planner, au Datacard Generator et au Flight Configurator ; la géométrie reste géodésique. Joué sur le shell construit
(dist/dcs_mission_plan.html, chromium), sans réseau ; les contrôles passent par le DOM."""
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tests'))
sys.path.insert(0, str(ROOT))
from test_rp_menaces import SHELL, browser, needs_pw  # noqa: E402,F401
from projection_block import build_block  # noqa: E402

ROUTES = {
    'GermanyCW': [(52.386, 11.82), (52.386689, 11.746334), (52.566033, 11.723879), (52.4789, 12.064515), (52.321073, 12.005536)],
    'Caucasus': [(42.18, 42.48), (42.348311, 42.764925), (42.609765, 42.429916)],
    'Syria': [(35.4, 38.9), (35.399821, 39.230986)],
    'Nevada': [(36.236, -115.034), (35.876344, -115.042929)],
    'MarianaIslandsWWII': [(13.48, 144.8), (13.695414, 144.967119)],
}
# les caps Vrai attendus, par branche : la grille pour les théâtres qui ont une projection, le grand cercle sinon
WANT = {'GermanyCW': ['278', '003', '120', '200'], 'Caucasus': ['045', '310'], 'Syria': ['090'], 'Nevada': ['180'], 'MarianaIslandsWWII': ['037']}


def page(name):
    return (ROOT / 'dist' / name).read_text(encoding='utf-8')


def d3(s):
    m = re.search(r'(\d{3})\s*°', s)
    return m.group(1) if m else None


def open_mod(br, mod, probe, example=False):
    ctx = br.new_context(viewport={'width': 1280, 'height': 900})
    ctx.add_init_script("try{localStorage.setItem('lang_v1','fr')}catch(e){}")
    pg = ctx.new_page()
    pg.errs = []
    pg.on('pageerror', lambda e: pg.errs.append(str(e)))
    pg.route('**/*', lambda r: r.continue_() if r.request.url.startswith(('file:', 'data:', 'blob:')) else r.abort())
    pg.goto(SHELL, wait_until='commit')
    pg.wait_for_function("typeof NAV !== 'undefined' && typeof openModule === 'function'", timeout=30000)
    pg.wait_for_timeout(600)
    if example:
        pg.evaluate("MP_WORK_EXAMPLE('fl')")
        pg.wait_for_timeout(1200)
    pg.evaluate("openModule('%s')" % mod)
    pg.wait_for_timeout(2300)
    fr = next(f for f in pg.frames if f != pg.main_frame and f.evaluate("typeof %s !== 'undefined'" % probe))
    return ctx, pg, fr


RP_SET = """([th, pts, ref, year]) => { setTheatre(th);
  S.navDisplay = Object.assign({}, S.navDisplay, { ref: ref, mode: 'calc', year: year, force: !!year });
  S.points = pts.map((p, i) => ({ pid: 'p' + i, name: 'P' + i, lat: p[0], lon: p[1], alt: 30, altRef: 'AGL' })); S.refs = []; renderAll(); }"""
RP_NAV = "() => Array.from(document.querySelectorAll('#nav-body tr.leg')).map(e => e.textContent)"
RP_RULER = """(pts) => { setTapMode('ruler'); RL.pts.length = 0; pts.forEach(p => RL.pts.push({ lat: p[0], lon: p[1] })); rlRender();
  const o = Array.from(document.querySelectorAll('.rl-label')).map(e => e.textContent); setTapMode('read'); RL.pts.length = 0; rlRender(); return o; }"""
DG_SET = """([th, pts, ref, year]) => { doc.theatre = th; dgN.ref = ref; dgN.mode = 'calc'; dgN.year = year; dgN.force = !!year;
  const c = curCard(); c.nav = pts.map(q => ({ name: '', coord: q[0] + ', ' + q[1], course: '', distance: '', altitude: '', tos: '', note: '' })); renderAll(); }"""
DG_CAPS = """() => ({ calc: navLegs(curCard()).map(o => o.calc ? o.calc.cap : null), dom: Array.from(document.querySelectorAll('[data-path$=".course"]')).map(e => e.value) })"""
FC_SET = """([th, pts, nav]) => { S.theatre = th; if (typeof GS !== 'undefined') GS.theatre = th;
  const f = { name: 'x', route: { points: {} } };
  pts.forEach((q, i) => { const p = llToDcs(th, q[0], q[1]); f.route.points[String(i + 1)] = { x: p.x, y: p.y, name: 'P' + i }; });
  const geo = routeGeo(f), L = routeLegs(geo, declSource(nav, ''));
  const rp = Object.assign({}, rpRead()); rp.state = Object.assign({}, rp.state, { nav: nav });
  const html = routeViewHtml(f, 0, rp);
  return { hdg: L.legs.map(l => l.hdg), dom: (html.match(/<td class="rt-r">[0-9]{3}°<\\/td>/g) || []).map(s => s.replace(/<[^>]*>/g, '').replace('°', '')) }; }"""
VRAI = {'mode': 'manual', 'decl': '0', 'year': '', 'force': False, 'ref': 'mag'}      # le Flight Configurator est toujours magnétique : une déclinaison saisie à 0 donne le cap Vrai


def mag(year):
    return {'mode': 'calc', 'decl': '', 'year': year, 'force': True, 'ref': 'mag'}


# ---------- le texte : un seul bloc de projection, trois pages, aucune copie ----------
def test_one_projection_block_in_the_three_tools():
    blk = build_block()
    rp, dg, fc = page('dcs_route_planner.html'), page('dcs_datacard_generator.html'), page('dcs_flight_configurator.html')
    for h in (rp, dg, fc):
        assert h.count(blk) == 1 and h.count('const TM_PARAMS = {') == 1 and h.count('function llToDcs(') == 1 and h.count('function dcsToLl(') == 1
        assert h.count('function gridBrg(') == 1 and h.count('function gridDest(') == 1 and h.count('function gridOrigin(') == 1


# ---------- C2 : les caps affichés, les trois outils ----------
@needs_pw
def test_displayed_headings_follow_the_grid_in_the_route_planner(browser):
    ctx, pg, fr = open_mod(browser, 'rp', '__RP')
    for k, pts in ROUTES.items():
        fr.evaluate(RP_SET, [k, pts, 'true', ''])
        pg.wait_for_timeout(200)
        assert [d3(x) for x in fr.evaluate(RP_NAV)] == WANT[k], k
        assert [d3(x) for x in fr.evaluate(RP_RULER, pts)] == WANT[k], k
    assert pg.errs == []
    ctx.close()


@needs_pw
def test_displayed_headings_follow_the_grid_in_the_datacard_generator(browser):
    ctx, pg, d = open_mod(browser, 'dg', 'navLegs')
    for k, pts in ROUTES.items():
        d.evaluate(DG_SET, [k, pts, 'true', ''])
        pg.wait_for_timeout(250)
        r = d.evaluate(DG_CAPS)
        assert r['calc'][1:] == WANT[k] and r['dom'][-len(WANT[k]):] == WANT[k], k
    assert pg.errs == []
    ctx.close()


@needs_pw
def test_displayed_headings_follow_the_grid_in_the_flight_configurator(browser):
    ctx, pg, f = open_mod(browser, 'fc', 'routeLegs', example=True)
    for k, pts in ROUTES.items():
        if k == 'MarianaIslandsWWII':
            continue       # sans projection de DCS, le Flight Configurator ne lit pas la route
        r = f.evaluate(FC_SET, [k, pts, VRAI])
        assert r['hdg'] == WANT[k] and r['dom'] == WANT[k], k
    assert pg.errs == []
    ctx.close()


# ---------- C3 : Mahlwinkel ----------
@needs_pw
def test_mahlwinkel_first_leg_true_278_magnetic_follows_the_cockpit_compass(browser):
    pts = ROUTES['GermanyCW']
    ctx, pg, fr = open_mod(browser, 'rp', '__RP')
    for year, want in (('2020', 274), ('1985', 278)):
        nav = [d3(x) for x in (fr.evaluate(RP_SET, ['GermanyCW', pts, 'mag', year]) or fr.evaluate(RP_NAV))]
        assert abs(int(nav[0]) - want) <= 1, (year, nav)
    ctx.close()
    ctx, pg, d = open_mod(browser, 'dg', 'navLegs')
    for year, want in (('2020', 274), ('1985', 278)):
        d.evaluate(DG_SET, ['GermanyCW', pts, 'mag', year])
        pg.wait_for_timeout(250)
        assert abs(int(d.evaluate(DG_CAPS)['calc'][1]) - want) <= 1, year
    ctx.close()
    ctx, pg, f = open_mod(browser, 'fc', 'routeLegs', example=True)
    for year, want in (('2020', 274), ('1985', 278)):
        assert abs(int(f.evaluate(FC_SET, ['GermanyCW', pts, mag(year)])['hdg'][0]) - want) <= 1, year
    ctx.close()


# ---------- C4 : les caps saisis ----------
@needs_pw
def test_typed_heading_and_distance_place_the_point_at_the_grid_heading_in_the_route_planner(browser):
    ctx, pg, fr = open_mod(browser, 'rp', '__RP')
    for k, pts in ROUTES.items():
        for ref in ('true', 'mag'):
            fr.evaluate(RP_SET, [k, [pts[0]], ref, ''])
            fr.evaluate("() => { setAddMode('hd'); document.getElementById('add-hdg').value = '045'; document.getElementById('add-dist').value = '30'; document.getElementById('btn-add-wp').click(); }")
            pg.wait_for_timeout(250)
            cells = fr.evaluate("() => Array.from(document.querySelectorAll('#nav-body tr.leg td[colspan=\"2\"], #nav-body tr.leg td.r')).map(e => e.textContent)")
            assert d3(cells[0]) == '045' and cells[1].startswith('30,0'), (k, ref, cells)
    assert pg.errs == []
    ctx.close()


@needs_pw
def test_typed_heading_and_distance_place_the_point_at_the_grid_heading_in_the_datacard_generator(browser):
    ctx, pg, d = open_mod(browser, 'dg', 'navLegs')
    for k, pts in ROUTES.items():
        for ref in ('true', 'mag'):
            d.evaluate(DG_SET, [k, [pts[0]], ref, ''])
            d.evaluate("() => { const c = curCard(); c.nav.push({ name: '', coord: '', course: '045', distance: '30', altitude: '', tos: '', note: '' }); renderAll(); }")
            est = d.evaluate("() => { const o = navLegs(curCard())[1]; return o.est ? [o.est.lat, o.est.lon] : null; }")
            assert est, (k, ref)
            d.evaluate("(a) => { const c = curCard(); c.nav[1].coord = a[0] + ', ' + a[1]; c.nav[1].course = ''; c.nav[1].distance = ''; renderAll(); }", est)
            assert d.evaluate("() => { const o = navLegs(curCard())[1].calc; return [o.cap, o.dist]; }") == ['045', '30'], (k, ref)
            # le champ Cap quitté (dgPosByLeg), puis la distance seule qui change : le cap reste
            p = d.evaluate("() => { const c = curCard(); c.nav[1] = { name: '', coord: '', course: '', distance: '30', altitude: '', tos: '', note: '' }; const p = dgPosByLeg(c, 1, 'course', '045'); return p ? [p.lat, p.lon] : null; }")
            assert p == pytest.approx(est, abs=1e-7), (k, ref)
            d.evaluate("(a) => { const c = curCard(); c.nav[1].coord = a[0] + ', ' + a[1]; renderAll(); }", p)
            q = d.evaluate("() => { const p = dgPosByLeg(curCard(), 1, 'distance', '45'); return p ? [p.lat, p.lon] : null; }")
            d.evaluate("(a) => { const c = curCard(); c.nav[1].coord = a[0] + ', ' + a[1]; renderAll(); }", q)
            assert d.evaluate("() => { const o = navLegs(curCard())[1].calc; return [o.cap, o.dist]; }") == ['045', '45'], (k, ref)
    assert pg.errs == []
    ctx.close()


@needs_pw
def test_grid_inverse_functions_and_theatres_without_a_projection(browser):
    ctx, pg, fr = open_mod(browser, 'rp', '__RP')
    r = fr.evaluate("""() => { const out = {}, a = { lat: 52.386, lon: 11.82 };
      for (const th of ['GermanyCW', 'Caucasus', 'Syria', 'Nevada']) {
        const p = th === 'GermanyCW' ? a : th === 'Caucasus' ? { lat: 42.18, lon: 42.48 } : th === 'Syria' ? { lat: 35.4, lon: 38.9 } : { lat: 36.236, lon: -115.034 };
        const x = gridDest(th, p, 123.4, 80), o = gridOrigin(th, p, 123.4, 80);
        out[th] = [gridBrg(th, p, x), legCalc(p, x).km, gridBrg(th, o, p), legCalc(o, p).km];
      }
      const q = { lat: 13.48, lon: 144.8 }, w = { lat: 13.695414, lon: 144.967119 };
      out.none = [gridBrg('MarianaIslandsWWII', q, w), legCalc(q, w).brg, gridBrg('Iraq', q, w) === legCalc(q, w).brg, gridBrg('Afghanistan', q, w) === legCalc(q, w).brg,
        gridDest('Iraq', q, 45, 30).lat === legDest(q, 45, 30).lat];
      return out; }""")
    for th in ('GermanyCW', 'Caucasus', 'Syria', 'Nevada'):
        assert r[th][0] == pytest.approx(123.4, abs=1e-6) and r[th][1] == pytest.approx(80, abs=1e-6), th
        assert r[th][2] == pytest.approx(123.4, abs=1e-5) and r[th][3] == pytest.approx(80, abs=1e-6), th
    assert r['none'][0] == r['none'][1] and r['none'][2:] == [True, True, True]
    ctx.close()


# ---------- C2 bis : l'étiquette de rotation d'une boîte ----------
@needs_pw
def test_box_rotation_label_shows_the_grid_heading_of_its_axis_and_leaves_the_stored_one(browser):
    ctx, pg, fr = open_mod(browser, 'rp', '__RP')
    js = """([th, b]) => { setTheatre(th); setTapMode('draw'); CF_LAYERS.length = 0;
      const it = cfItem({ type: 'box', id: 'B1', name: '', lat: b[0], lon: b[1], brg: b[2], lengthNm: 5, widthNm: 5 });
      CF_LAYERS.push({ id: 'L1', name: 'x', visible: true, source: { kind: 'drawn', file: '' }, items: [it] }); DR.layerId = 'L1';
      map.setView([b[0], b[1]], 10, { animate: false }); drawLayers(); drSelect('L1', 'B1'); drBuildHandles();
      const rot = DR.hs.find(h => h.mk.getElement().classList.contains('rot')), before = it.brg; rot.start(); drRlab();
      const o = { text: DR.lab.text(), shown: document.querySelector('.dr-rlab').textContent, before: before, after: it.brg, lat: it.lat, lon: it.lon };
      DR.lab = null; drRlab(); setTapMode('read'); return o; }"""
    g = fr.evaluate(js, ['GermanyCW', [52.386, 11.82, 270.907]])
    assert g['text'] == '278°' and g['shown'] == '278°' and g['before'] == g['after'] == 270.907 and (g['lat'], g['lon']) == (52.386, 11.82)
    m = fr.evaluate(js, ['MarianaIslandsWWII', [13.48, 144.8, 37]])
    assert m['text'] == '037°' and m['shown'] == '037°' and m['before'] == m['after'] == 37
    assert pg.errs == []
    ctx.close()
