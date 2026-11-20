"""Le Flight Configurator, l'écran de l'équipement et de la masse (DOM, dans le shell) : le champ Canon et la ligne de détail, les cases d'options, le recalcul
d'un geste, le changement de type, la persistance de props au rechargement, l'export AddPropAircraft ; et le Datacard Generator qui donne la même masse."""
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
CHROMIUM = Path('/opt/pw-browsers/chromium')
try:
    import playwright.sync_api  # noqa: F401
    HAS_PW = CHROMIUM.exists()
except ImportError:
    HAS_PW = False
pytestmark = pytest.mark.skipif(not HAS_PW, reason='playwright ou chromium absent')

READ = """() => { const q = s => document.querySelector(s);
  return { gun: !!q('#blk-cmp input[data-k="gun"]'),
    checks: Array.from(document.querySelectorAll('.fc-eq input[type=checkbox]')).map(i => [i.getAttribute('data-eq'), i.checked]),
    total: (q('#cmp-total') || {}).innerText || '', detail: (q('#cmp-detail') || {}).innerText || '',
    take: (() => { const u = selUnit().u; return payloadTakeoff(u.type, cmpFuelIn(u), cmpStations(u.loadout), AIRCRAFT_MASSES, { gun: u.loadout ? loNumber(u.loadout.gun) : undefined, props: u.props }).takeoff; })() }; }"""


def open_fc(p, lang='en-US'):
    br = p.chromium.launch(executable_path=str(CHROMIUM), args=['--no-sandbox'])
    ctx = br.new_context(viewport={'width': 1280, 'height': 900}, locale=lang)
    pg = ctx.new_page(); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.route('**/*', lambda r: r.continue_() if r.request.url.startswith(('file:', 'data:', 'blob:')) else r.abort())
    pg.goto('file://' + str(ROOT / 'dist' / 'dcs_mission_plan.html'), wait_until='commit'); pg.wait_for_timeout(2500)
    pg.evaluate("MP_WORK_EXAMPLE('fl')"); pg.wait_for_timeout(1500)
    pg.click('#card-fc'); pg.wait_for_timeout(2000)
    return br, pg, pg.query_selector('#iframe-fc').content_frame(), errs


def test_screen_gestures_persistence_and_export():
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        br, pg, fc, errs = open_fc(p)
        try:
            # Mi-24P de l'exemple : un canon, une case, la ligne de détail
            a = fc.evaluate(READ)
            assert a['gun'] is True and a['checks'] == [['ExhaustScreen', True]]
            # la masse des emports et « emports » de la ligne de détail au dixième ; la masse d'une station en entier
            assert '1,599.6 kg' in a['total'] and 'stores 1,599.6 ' in a['detail'] and 'rounds 207.5' in a['detail']
            assert fc.evaluate("Array.from(document.querySelectorAll('.cmp-kg')).map(e => e.textContent).filter(Boolean).includes('104 kg')")
            assert 'Take-off' in a['total'] and 'rounds' in a['detail'] and 'equipment incl.' in a['detail'] and 'countermeasures weigh nothing' in a['detail']
            # décocher l'écran IR : −160 kg, au même instant
            fc.evaluate("document.querySelector('.fc-eq input[data-eq=ExhaustScreen]').click()"); pg.wait_for_timeout(300)
            b = fc.evaluate(READ)
            assert b['checks'] == [['ExhaustScreen', False]] and a['take'] - b['take'] == pytest.approx(160)
            # canon à 0 : le poids des obus s'en va
            fc.evaluate("(()=>{const i=document.querySelector('#blk-cmp input[data-k=gun]'); i.value='0'; i.dispatchEvent(new Event('input',{bubbles:true})); i.dispatchEvent(new Event('change',{bubbles:true}));})()")
            pg.wait_for_timeout(300)
            c = fc.evaluate(READ)
            assert b['take'] - c['take'] == pytest.approx(207.5) and 'rounds' in c['detail']
            # props survit au rechargement de l'état
            props = fc.evaluate("selUnit().u.props")
            assert props == {'ExhaustScreen': False}
            exp = fc.evaluate("JSON.stringify(buildPackage())")
            units = [u for f in json.loads(exp)['flights'] for u in f['units']]
            assert units[0]['AddPropAircraft'] == {'ExhaustScreen': False}
            # le type passé en Mi-8MT (avec confirmation) : plus de champ Canon, trois cases par défaut, props vidé
            fc.evaluate("() => { const s = document.querySelectorAll('select[data-k=utype]')[0]; s.value = 'Mi-8MT'; s.dispatchEvent(new Event('change', { bubbles: true })); }"); pg.wait_for_timeout(400)
            fc.evaluate("document.getElementById('ui-confirm-ok').click()"); pg.wait_for_timeout(500)
            d = fc.evaluate(READ)
            assert d['gun'] is False and [x[0] for x in d['checks']] == ['ExhaustScreen', 'AdditionalArmor', 'CargoHalfdoor'] and all(x[1] for x in d['checks'])
            assert fc.evaluate("selUnit().u.props") == {}
            assert 'rounds' not in d['detail'] and 'equipment incl.' in d['detail']
            fc.evaluate("document.querySelector('.fc-eq input[data-eq=AdditionalArmor]').click()"); pg.wait_for_timeout(300)
            e = fc.evaluate(READ)
            assert d['take'] - e['take'] == pytest.approx(419)
            assert errs == []
        finally:
            br.close()


def test_datacard_generator_gives_the_same_mass_as_the_flight_configurator():
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        br, pg, fc, errs = open_fc(p)
        try:
            fc.evaluate("document.querySelector('.fc-eq input[data-eq=ExhaustScreen]').click()"); pg.wait_for_timeout(300)
            fcw = fc.evaluate("(() => { const out = []; S.flights.forEach(f => f.units.forEach(u => out.push(payloadTakeoff(u.type, cmpFuelIn(u), cmpStations(u.loadout), AIRCRAFT_MASSES, { gun: u.loadout ? loNumber(u.loadout.gun) : undefined, props: u.props }).takeoff))); return out; })()")
            fc.evaluate("document.querySelector('.mp-back-injected').click()"); pg.wait_for_timeout(500)
            pg.evaluate("MP_OPEN_MODULE('dg')"); pg.wait_for_timeout(2500)
            dg = pg.query_selector('#iframe-dg').content_frame()
            lots = dg.evaluate("DGG.flights.map(f => dgFuelLots(f))")
            dgw = sorted(l['weight'] for fl in lots for l in fl for _ in l['ranks'])
            assert len(fcw) == 2 and fcw[0] != fcw[1] and fcw[1] - fcw[0] == pytest.approx(160)       # l'option décochée de la première unité seule
            assert dgw == pytest.approx(sorted(fcw))                                                    # le DG donne les mêmes poids que le FC, unité pour unité
        finally:
            br.close()


def test_unknown_keys_are_exported_for_a_type_without_options_and_a_type_change_warns():
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        br, pg, fc, errs = open_fc(p)
        try:
            # C3 : Ka-50 n'a pas d'option dans la table ; une clé hors table (importée d'HQ) est exportée, sans clé le champ reste absent
            out = fc.evaluate("""() => {
              const u = restoreFlight({ fcId: 'x', name: 'G', units: [{ type: 'Ka-50', addPropIn: { zzInconnue: 7 } }] }).units[0];
              return { keys: u.props, kept: unitPropsOut(u), none: unitPropsOut({ type: 'Ka-50', props: {} }), mi24: unitPropsOut({ type: 'Mi-24P', props: { zz: 1 } }) }; }""")
            assert out['keys'] == {'zzInconnue': 7} and out['kept'] == {'zzInconnue': 7} and out['none'] is None
            assert out['mi24'] == {'ExhaustScreen': True, 'zz': 1}
            # C4 : une unité sans radios ni emport mais avec des options (props non vide) demande confirmation au changement de type ; sans options, non
            def change(props):
                fc.evaluate("(props) => { const u = S.flights[0].units[0]; u.loadout = null; u.radios = {}; u.props = props; u.type = 'Mi-24P'; renderAll(); }", props)
                pg.wait_for_timeout(300)
                fc.evaluate("() => { const s = document.querySelectorAll('select[data-k=utype]')[0]; s.value = 'Mi-8MT'; s.dispatchEvent(new Event('change', { bubbles: true })); }")
                pg.wait_for_timeout(400)
                shown = fc.evaluate("() => { const b = document.getElementById('ui-confirm-ok'); return !!b && !b.closest('.ui-modal').hidden; }")
                if shown:
                    fc.evaluate("document.getElementById('ui-confirm-cancel').click()")
                    pg.wait_for_timeout(300)
                return shown
            assert change({'ExhaustScreen': False}) is True
            assert change({}) is False
            assert errs == []
        finally:
            br.close()


def test_retype_warnings_count_the_options_as_unit_data_in_the_import_and_the_datacard_generator():
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        br, pg, fc, errs = open_fc(p)
        try:
            # C4, l'import : impRetype avertit pour une unité dont seules les options (props) sont à perdre ; pas pour une unité vide
            warns = fc.evaluate("""() => {
              const f = S.flights[0], u = f.units[0], res = [];
              u.loadout = null; u.radios = {}; delete u.payloadIn;
              [{ ExhaustScreen: false }, {}].forEach(pr => { u.props = pr; u.type = 'Mi-24P'; const st = { warn: [] }; impRetype(st, f, 0, 0, u, 'Mi-8MT'); res.push(st.warn.length); });
              return res; }""")
            assert warns == [1, 0]
            # C4, le Datacard Generator : dgUnitHasData
            fc.evaluate("document.querySelector('.mp-back-injected').click()"); pg.wait_for_timeout(500)
            pg.evaluate("MP_OPEN_MODULE('dg')"); pg.wait_for_timeout(2500)
            dg = pg.query_selector('#iframe-dg').content_frame()
            r = dg.evaluate("[dgUnitHasData({ type: 'Mi-24P', props: { ExhaustScreen: false } }), dgUnitHasData({ type: 'Mi-24P', props: {} }), dgUnitHasData({ type: 'Mi-24P' })]")
            assert r == [True, False, False]
            assert errs == []
        finally:
            br.close()
