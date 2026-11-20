"""HQ et l'équipement d'appareil : l'instantané porte l'AddPropAircraft de chaque unité ; un paquet appliqué l'écrit (fusion avec celui de la mission
sur un vol trouvé, table créée si besoin, gabarit plus clés du paquet sur un vol créé) ; sans la partie Emport, rien n'est écrit. Le .miz est fabriqué
(tests/miz_fixture.py), le paquet est écrit ici, le .miz sauvegardé est relu en texte."""
import json
import re
import sys
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
import miz_fixture  # noqa: E402

CHROMIUM = Path('/opt/pw-browsers/chromium')
try:
    import playwright.sync_api  # noqa: F401
    HAS_PW = CHROMIUM.exists()
except ImportError:
    HAS_PW = False
needs_pw = pytest.mark.skipif(not HAS_PW, reason='playwright ou chromium absent')

ROUTE = {'points': {'1': {'type': 'Turning Point', 'action': 'Turning Point', 'x': 100, 'y': 200, 'alt': 500, 'alt_type': 'BARO', 'speed': 50,
                           'task': {'id': 'ComboTask', 'params': {'tasks': {}}}}}}
DEPART = {'start': 'air', 'airdromeId': None, 'airdrome': None, 'x': None, 'y': None, 'stands': []}


def flight(name, unit, typ, payload, props):
    return {'groupName': name, 'coalition': 'blue', 'groupFrequency': None, 'route': ROUTE, 'departure': DEPART,
            'units': [{'name': unit, 'type': typ, 'callsign': 'Enfield11', 'liveryId': 'standard', 'radios': None, 'payload': payload, 'stand': None, 'AddPropAircraft': props}]}


PACKAGE = {'format': 'dcs-flight-package-v2', 'createdAt': '2026-11-20T00:00:00.000Z', 'createdBy': 'test', 'theatre': 'Syria', 'missionDate': '1985-06-15', 'flights': [
    flight('HIND', 'HIND-1', 'Mi-8MT', {'chaff': 0, 'flare': 128, 'fuel': '1929', 'gun': 100, 'pylons': {}},
           {'ExhaustScreen': False, 'AdditionalArmor': False, 'CargoHalfdoor': True, 'zzUnknownKey': 'garder', 'zzFcOnly': 1}),
    flight('CAESAR', 'CAESAR-1', 'Mi-24P', {'ammo_type': 1, 'chaff': 0, 'flare': 192, 'fuel': 1701, 'gun': 100, 'pylons': {}, 'restricted': {}}, {'ExhaustScreen': True}),
    flight('NEWBIRD', 'NEWBIRD-1', 'Mi-8MT', {'chaff': 0, 'flare': 128, 'fuel': '1929', 'gun': 100, 'pylons': {}},
           {'ExhaustScreen': True, 'AdditionalArmor': True, 'CargoHalfdoor': False}),
]}


def props_of(miz_path, unit):
    """L'AddPropAircraft d'une unité du .miz, lu en texte : {clé: valeur} ; None si l'unité n'en a pas."""
    text = zipfile.ZipFile(miz_path).read('mission').decode('utf-8')
    i = text.index('["name"] = "%s"' % unit)
    nxt = text.find('["unitId"]', i)          # la table de l'unité suivante (le nom de l'indicatif vient aussi sous « name »)
    m = re.compile(r'\["AddPropAircraft"\]\s*=\s*\{(.*?)\},\s*-- end of \["AddPropAircraft"\]', re.S).search(text, i, nxt if nxt > 0 else len(text))
    if not m:
        return None
    out = {}
    for k, v in re.findall(r'\["([^"]+)"\]\s*=\s*("[^"]*"|[-\w.]+),', m.group(1)):
        out[k] = json.loads(v) if v[0] == '"' else {'true': True, 'false': False}.get(v, None) if v in ('true', 'false') else float(v) if '.' in v else int(v)
    return out


def open_hq(p, tmp_path):
    shell = 'file://' + str(ROOT / 'dist' / 'dcs_mission_plan.html')
    br = p.chromium.launch(executable_path=str(CHROMIUM), args=['--no-sandbox'])
    ctx = br.new_context(viewport={'width': 1280, 'height': 900}, locale='en-US', accept_downloads=True)
    pg = ctx.new_page()
    pg.route('**/*', lambda r: r.continue_() if r.request.url.startswith(('file:', 'data:', 'blob:')) else r.abort())
    pg.goto(shell, wait_until='commit'); pg.wait_for_timeout(2500)
    pg.click('#card-hq'); pg.wait_for_timeout(1500)
    hq = pg.query_selector('#iframe-hq').content_frame()
    miz = tmp_path / 'essai.miz'
    miz_fixture.make(str(miz))
    pkg = tmp_path / 'paquet.json'
    pkg.write_text(json.dumps(PACKAGE), encoding='utf-8')
    hq.set_input_files('#miz-file-input', str(miz)); pg.wait_for_timeout(2500)
    return br, pg, hq, pkg


def save_miz(pg, hq, dest):
    hq.evaluate("document.getElementById('btn-save').click()"); pg.wait_for_timeout(600)
    with pg.expect_download(timeout=20000) as dl:
        hq.evaluate("document.getElementById('fn-go').click()")
    dl.value.save_as(str(dest))


@needs_pw
def test_snapshot_applied_package_and_unticked_loadout(tmp_path):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        br, pg, hq, pkg = open_hq(p, tmp_path)
        try:
            snap = hq.evaluate("HQ_SNAPSHOT.flights.map(f => f.units.map(u => ({ name: u.name, has: 'addProp' in u, addProp: u.addProp })))")
            assert snap[0][0]['addProp'] == {'AdditionalArmor': False, 'zzUnknownKey': 'garder'}
            assert snap[1][0]['has'] is False
            assert hq.evaluate('HQ_SNAPSHOT.schema') == 'dcs-mission-snapshot-v2'
            # sans la partie Emport : rien d'écrit sur les vols trouvés, le vol créé garde les défauts du gabarit
            hq.set_input_files('#pk-file-input', str(pkg)); pg.wait_for_timeout(1500)
            hq.evaluate("document.querySelector('[data-pkc=create]').click()"); pg.wait_for_timeout(400)
            n = hq.evaluate("() => { let n = 0; document.querySelectorAll('input[data-part=\"loadout\"]').forEach(i => { if (i.checked && !i.disabled) { i.click(); n++; } }); return n; }")
            assert n == 3
            hq.evaluate("document.getElementById('pk-apply-btn').click()"); pg.wait_for_timeout(3000)
            out1 = tmp_path / 'sans_emport.miz'
            save_miz(pg, hq, out1)
        finally:
            br.close()
    assert props_of(out1, 'HIND-1') == {'AdditionalArmor': False, 'zzUnknownKey': 'garder'}
    assert props_of(out1, 'CAESAR-1') is None
    created = props_of(out1, 'NEWBIRD-1')
    assert created is not None and created['CargoHalfdoor'] is True and 'zzFcOnly' not in created      # la valeur du paquet (false) n'est pas écrite


@needs_pw
def test_applied_with_the_loadout_part(tmp_path):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        br, pg, hq, pkg = open_hq(p, tmp_path)
        try:
            hq.set_input_files('#pk-file-input', str(pkg)); pg.wait_for_timeout(1500)
            hq.evaluate("document.querySelector('[data-pkc=create]').click()"); pg.wait_for_timeout(400)
            hq.evaluate("document.getElementById('pk-apply-btn').click()"); pg.wait_for_timeout(3000)
            out2 = tmp_path / 'avec_emport.miz'
            save_miz(pg, hq, out2)
        finally:
            br.close()
    # vol trouvé : les clés du paquet par-dessus celles de la mission ; la clé hors table, gardée
    assert props_of(out2, 'HIND-1') == {'ExhaustScreen': False, 'AdditionalArmor': False, 'CargoHalfdoor': True, 'zzUnknownKey': 'garder', 'zzFcOnly': 1}
    # un Mi-24P sans table : elle est créée
    assert props_of(out2, 'CAESAR-1') == {'ExhaustScreen': True}
    # vol créé : le gabarit du type, les clés du paquet par-dessus
    created = props_of(out2, 'NEWBIRD-1')
    assert created['CargoHalfdoor'] is False and created['AdditionalArmor'] is True and created['ExhaustScreen'] is True and 'RightEngineResource' in created
