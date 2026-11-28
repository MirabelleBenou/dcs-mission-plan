"""Le trait à main levée de l'outil Ligne du mode Dessin du Route Planner, et les outils du dessin au doigt sur un téléphone étroit.
Sans navigateur (node, sur le bloc extrait de route_freehand_block.build_block()) : la simplification sur de petits traits écrits ici (une droite bruitée sous 2 px, un angle droit, un point exactement à 2 px du segment,
un point dont la projection tombe hors du segment, deux points égaux, un trait qui revient à son départ) et le plafond de 500 sommets (1 300 points en dents de scie de 7 px).
Au navigateur (le shell construit, chromium, aucun réseau ; 1 280 × 800 à la souris et 412 × 915 au doigt) : la bascule et son reflet ; un trait crée une ligne ordinaire, l'outil reste Ligne, rien n'est choisi ; un trait de moins de 8 px
et un toucher ne créent rien ; la carte ne bouge pas pendant le trait ; touch-action ; la carte se déplace de nouveau quand la bascule s'éteint ; le doigt (CDP) : un doigt dessine, un second l'annule ; la ligne se relit
du JSON du calque et part à l'export comme une ligne par touchers. Les contrôles passent par le DOM, jamais par une capture."""
import json
import math
import random
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_route_heures import CHROMIUM, needs_node, needs_pw, open_rp, shell  # noqa: E402
from test_route_heures import browser  # noqa: E402,F401  (la fixture du module)
from banc_attente import attendre, cadre_export, poser_mode, viser  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from route_freehand_block import build_block  # noqa: E402


# ---------------------------------------------------------------------------------------------------- le bloc, sans navigateur
def node_stroke(pts, extra=''):
    js = build_block() + '\nconst P = %s; const r = rfhStroke(P); %s\nprocess.stdout.write(JSON.stringify(Object.assign({ reach: rfhReach(P) }, r)));\n' % (json.dumps(pts), extra)
    r = subprocess.run(['node', '-e', js], capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


@needs_node
def test_a_noisy_straight_stroke_keeps_its_two_ends_and_a_right_angle_keeps_three_points():
    noisy = [[i * 10, 0 if i in (0, 29) else (1.9 if i % 2 else -1.9)] for i in range(30)]               # des écarts de 1,9 px au plus de la droite des deux bouts
    r = node_stroke(noisy)
    assert r['idx'] == [0, 29] and r['tol'] == 2
    angle = [[i * 10, 0] for i in range(11)] + [[100, i * 10] for i in range(1, 11)]
    assert node_stroke(angle)['idx'] == [0, 10, 20]


@needs_node
def test_a_point_at_exactly_two_px_is_dropped_and_a_point_projecting_outside_the_segment_is_judged_at_its_end():
    assert node_stroke([[0, 0], [5, 2], [10, 0]])['idx'] == [0, 2]                  # exactement 2 px : pas strictement au-delà
    assert node_stroke([[0, 0], [5, 2.001], [10, 0]])['idx'] == [0, 1, 2]
    r = node_stroke([[0, 0], [20, 0.5], [10, 0]])                                    # (20, 0.5) se projette hors du segment [0,0]-[10,0] : jugé à 10,01 du bout ; à la droite il serait à 0,5 (non gardé)
    assert r['idx'] == [0, 1, 2]


@needs_node
def test_two_equal_points_count_for_one_and_a_stroke_back_to_its_start_stays_open_with_its_far_points():
    assert node_stroke([[0, 0], [0, 0], [10, 0], [10, 0], [10, 0]])['idx'] == [0, 2]
    assert node_stroke([[3, 3], [3, 3]])['idx'] == [0]
    loop = [[0, 0], [30, 0], [30, 30], [0, 30], [0, 0]]                              # le premier et le dernier points sont égaux : le segment est un point, la distance est celle à ce point
    r = node_stroke(loop)
    assert r['idx'][0] == 0 and r['idx'][-1] == 4 and len(r['idx']) >= 3 and abs(r['reach'] - 30 * math.sqrt(2)) < 1e-9


@needs_node
def test_over_500_vertices_the_tolerance_doubles_until_500_at_most_remain_and_stops_at_the_first_tolerance_that_passes():
    saw = [[i * 7, (7 if i % 2 else 0)] for i in range(1300)]
    low = node_stroke(saw, 'const half = rfhSimplify(P, r.tol / 2).length, two = rfhSimplify(P, 2).length;')
    assert low['tol'] >= 4 and len(low['idx']) <= 500
    n = json.loads(subprocess.run(['node', '-e', build_block() + '\nconst P = %s; const r = rfhStroke(P);\nprocess.stdout.write(JSON.stringify([rfhSimplify(P, 2).length, rfhSimplify(P, r.tol / 2).length]));' % json.dumps(saw)], capture_output=True, text=True).stdout)
    assert n[0] > 500 and n[1] > 500                                                 # à 2 px et à la moitié de la tolérance finale : plus de 500 ; le doublement s'arrête à la première qui passe
    rnd = random.Random(3)
    noise = [[i * 0.6, rnd.uniform(-25, 25)] for i in range(1300)]                  # un second trait : plus de 500 sommets à 2 px, mais le rendu final tombe entre 3 et 500
    r = json.loads(subprocess.run(['node', '-e', build_block() + '\nconst P = %s; const r = rfhStroke(P);\nprocess.stdout.write(JSON.stringify([r.tol, r.idx.length, rfhSimplify(P, 2).length, rfhSimplify(P, r.tol / 2).length]));' % json.dumps(noise)], capture_output=True, text=True).stdout)
    assert r[2] > 500 and r[3] > 500 and r[0] >= 4 and 3 <= r[1] <= 500, r


# ---------------------------------------------------------------------------------------------------- le navigateur
def origin(pg, fr):
    """Le coin de la carte, en coordonnées de la page du shell (le Route Planner est dans un cadre)"""
    b = pg.query_selector('#iframe-rp').bounding_box()
    r = fr.evaluate("() => { const r = document.getElementById('map').getBoundingClientRect(); return [r.left + document.getElementById('map').clientLeft, r.top + document.getElementById('map').clientTop]; }")
    return b['x'] + r[0], b['y'] + r[1]


def mouse_stroke(pg, ox, oy, pts):
    """Un trait à la souris : pts en pixels de la carte"""
    pg.mouse.move(ox + pts[0][0], oy + pts[0][1])
    pg.mouse.down()
    for x, y in pts[1:]:
        pg.mouse.move(ox + x, oy + y)
    pg.mouse.up()


def wave(x0, y0, n, dx=3.0, amp=70.0, k=0.05):
    return [[x0 + i * dx, y0 + amp * math.sin(i * k)] for i in range(n)]


def to_draw_line(fr, free=True):
    poser_mode(fr, 'draw')
    fr.evaluate("(f) => { drSetTool('line'); DR.free = f; drSyncUi(); }", free)


STATE = """() => ({ tool: DR.tool, sel: DR.sel, drag: __RP.map.dragging.enabled(), cls: document.getElementById('map').classList.contains('rp-freehand'),
  ta: getComputedStyle(document.getElementById('map')).touchAction, items: CF_LAYERS.reduce((a, l) => a.concat(l.items), []), build: DR.build && DR.build.pts.length, stroke: !!DR.stroke })"""
LINES = "() => CF_LAYERS.reduce((a, l) => a.concat(l.items), []).filter(i => i.type === 'zone')"


@needs_pw
def test_the_freehand_switch_is_in_the_hint_bar_with_one_line_and_no_vertex_and_follows_its_state(browser):
    pg = shell(browser, 1280, 800)
    fr = open_rp(pg)
    viser(fr, 33.865, 36.06, 12)
    poser_mode(fr, 'draw')
    fr.evaluate("() => drSetTool('line')")
    sw = "() => { const b = document.querySelector('#dr-acts [data-dr=\"free\"]'); return b && { cls: b.className, pressed: b.getAttribute('aria-pressed'), title: b.title, label: b.getAttribute('aria-label'), span: b.querySelector('span').textContent, svg: b.querySelectorAll('svg').length, first: b === document.querySelector('#dr-acts').firstElementChild }; }"
    s = fr.evaluate(sw)
    assert s['first'] and s['pressed'] == 'false' and 'on' not in s['cls'].split() and s['title'] == s['label'] == s['span'] == 'Main levée' and s['svg'] == 1
    assert fr.evaluate("() => document.getElementById('dr-msg').textContent") == 'Touchez la carte pour poser les sommets.'
    assert fr.evaluate("() => [...document.querySelectorAll('#dr-acts [data-dr]')].map(b => b.dataset.dr)") == ['free', 'props', 'cancel']       # ni ↶ ni Terminer sans sommet
    fr.locator('#dr-acts [data-dr="free"]').click()
    s = fr.evaluate(sw)
    assert s['pressed'] == 'true' and 'on' in s['cls'].split()
    assert fr.evaluate("() => document.getElementById('dr-msg').textContent") == 'Glissez pour dessiner. La molette zoome.'
    assert fr.evaluate(STATE)['drag'] is False and fr.evaluate(STATE)['cls'] is True
    # la zone sans sommet : ni ↶ ni Terminer non plus, et pas de bascule
    fr.evaluate("() => drSetTool('zone')")
    assert fr.evaluate("() => [...document.querySelectorAll('#dr-acts [data-dr]')].map(b => b.dataset.dr)") == ['props', 'cancel']
    # un sommet posé (bascule éteinte) : pas de bascule, ↶ et Terminer reviennent
    fr.evaluate("() => { drSetTool('line'); DR.free = false; drSyncUi(); }")
    fr.evaluate("() => drMapClick({ latlng: __RP.map.getCenter(), containerPoint: __RP.map.getSize().divideBy(2) })")
    assert fr.evaluate("() => [...document.querySelectorAll('#dr-acts [data-dr]')].map(b => b.dataset.dr)") == ['props', 'undo', 'finish', 'cancel']
    assert pg.errs == []
    pg.context.close()


@needs_pw
def test_a_mouse_stroke_makes_an_ordinary_line_and_the_tool_stays_line_with_nothing_chosen(browser):
    pg = shell(browser, 1280, 800)
    fr = open_rp(pg)
    viser(fr, 33.865, 36.06, 12)
    to_draw_line(fr)
    ox, oy = origin(pg, fr)
    c0 = fr.evaluate("() => __RP.map.getCenter()")
    # pendant le trait, la carte ne bouge pas
    pg.mouse.move(ox + 300, oy + 300)
    pg.mouse.down()
    for x, y in wave(300, 300, 30)[1:]:
        pg.mouse.move(ox + x, oy + y)
    mid = fr.evaluate(STATE)
    assert mid['stroke'] is True and fr.evaluate("() => __RP.map.getCenter()") == c0 and mid['drag'] is False and mid['ta'] == 'none'
    pg.mouse.up()
    st = fr.evaluate(STATE)
    lines = fr.evaluate(LINES)
    assert len(lines) == 1 and lines[0]['kind'] == 'lines' and lines[0]['closed'] is False and len(lines[0]['points']) >= 2
    assert st['tool'] == 'line' and st['sel'] is None and st['stroke'] is False and st['cls'] is True and st['build'] == 0
    assert fr.evaluate("() => DR.free") is True and fr.evaluate("() => !!document.querySelector('#dr-acts [data-dr=\"free\"].on')") is True
    # un second trait, une seconde ligne
    mouse_stroke(pg, ox, oy, wave(250, 500, 30))
    assert len(fr.evaluate(LINES)) == 2
    # un trait de moins de 8 px, un clic : rien ne se crée, aucun sommet n'est posé
    mouse_stroke(pg, ox, oy, [[500, 400], [503, 402], [506, 404], [504, 401]])
    pg.mouse.click(ox + 600, oy + 400)
    st = fr.evaluate(STATE)
    assert len(fr.evaluate(LINES)) == 2 and st['build'] == 0 and st['sel'] is None
    # la bascule éteinte : la carte se déplace de nouveau, touch-action est celui de la base
    fr.locator('#dr-acts [data-dr="free"]').click()
    st = fr.evaluate(STATE)
    assert st['drag'] is True and st['cls'] is False and st['ta'] == 'none'                # Leaflet remet leaflet-touch-drag : none, la valeur de la base
    pg.mouse.move(ox + 300, oy + 300)
    pg.mouse.down()
    pg.mouse.move(ox + 380, oy + 340, steps=6)
    pg.mouse.up()
    c1 = fr.evaluate("() => __RP.map.getCenter()")
    assert c1 != c0                                                                         # la carte s'est déplacée
    assert len(fr.evaluate(LINES)) == 2
    # Ligne reprise dans la même ouverture : la bascule garde son dernier état (éteinte) ; rallumée, puis une autre outil et retour : allumée
    fr.evaluate("() => { DR.free = true; drSetTool('circle'); drSetTool('line'); }")
    assert fr.evaluate("() => DR.free") is True and fr.evaluate(STATE)['drag'] is False
    # un Échap pendant un trait l'annule, rien ne se crée
    pg.mouse.move(ox + 200, oy + 300)
    pg.mouse.down()
    pg.mouse.move(ox + 260, oy + 340, steps=5)
    assert fr.evaluate(STATE)['stroke'] is True
    pg.keyboard.press('Escape')
    pg.mouse.up()
    assert fr.evaluate(STATE)['stroke'] is False and len(fr.evaluate(LINES)) == 2 and fr.evaluate("() => DR.tool") == 'line'
    # le brouillon (et sa couleur) : le trait suivant a la couleur choisie
    fr.evaluate("() => { DR.draft = DR.draft || drNewDraft('line'); drApply({ it: DR.draft.it, draft: true }, 'color', '#1f4fa8'); }")
    mouse_stroke(pg, ox, oy, wave(250, 200, 30))
    assert fr.evaluate(LINES)[-1]['color'] == '#1f4fa8'
    assert pg.errs == []
    pg.context.close()
    # une réouverture du Route Planner : la bascule est éteinte
    pg2 = shell(browser, 1280, 800)
    fr2 = open_rp(pg2)
    poser_mode(fr2, 'draw')
    fr2.evaluate("() => drSetTool('line')")
    assert fr2.evaluate("() => DR.free") is False and fr2.evaluate(STATE)['drag'] is True
    pg2.context.close()


def container_px(fr, pts):
    # sans l'arrondi de latLngToContainerPoint : la projection au zoom courant, moins le coin de la carte
    return fr.evaluate("(P) => P.map(p => { const m = __RP.map, c = m.project(L.latLng(p[0], p[1]), m.getZoom()).subtract(m.getPixelBounds().min); return [c.x, c.y]; })", pts)


@needs_pw
def test_the_vertices_of_the_line_are_those_of_the_block_function_applied_to_the_points_received(browser):
    pg = shell(browser, 1280, 800)
    fr = open_rp(pg)
    viser(fr, 33.865, 36.06, 12)
    to_draw_line(fr)
    ox, oy = origin(pg, fr)
    rect = fr.evaluate("() => { const r = document.getElementById('map').getBoundingClientRect(); return [r.left, r.top]; }")
    bx = pg.query_selector('#iframe-rp').bounding_box()
    for k, pts in enumerate((wave(150, 350, 40, dx=9, amp=60, k=0.35), wave(120, 330, 330, dx=1.6, amp=90, k=0.07))):
        # les points reçus : ceux que la page lit (clientX, clientY du cadre), ramenés à la carte
        sent = [[round(ox + x) - ox, round(oy + y) - oy] for x, y in pts]
        mouse_stroke(pg, ox, oy, [[round(ox + x) - ox, round(oy + y) - oy] for x, y in pts])
        line = fr.evaluate(LINES)[k]
        got = container_px(fr, line['points'])
        keep = fr.evaluate("(P) => rfhStroke(P).idx", sent)
        want = [sent[i] for i in keep]
        assert len(got) == len(want) >= 2, (k, len(got), len(want))
        # les points sont pris en coordonnées de calque : au pixel de la carte près d'une translation (la vue n'a pas bougé), 0,05 px
        dx = got[0][0] - want[0][0]
        dy = got[0][1] - want[0][1]
        assert abs(dx) < 0.5 and abs(dy) < 0.5, (k, dx, dy)
        assert all(abs(g[0] - w[0] - dx) < 0.05 and abs(g[1] - w[1] - dy) < 0.05 for g, w in zip(got, want)), (k, got[:3], want[:3])
    assert len(fr.evaluate(LINES)[1]['points']) <= 500
    assert pg.errs == []
    pg.context.close()


# ---- au doigt : CDP Input.dispatchTouchEvent
def touch(cdp, kind, pts):
    cdp.send('Input.dispatchTouchEvent', {'type': kind, 'touchPoints': [{'x': x, 'y': y, 'id': i} for i, (x, y) in enumerate(pts)]})


@needs_pw
def test_at_the_finger_one_finger_draws_and_a_second_cancels_the_stroke_and_two_fingers_move_the_map(browser):
    pg = shell(browser, 412, 915, touch=True)
    fr = open_rp(pg)
    viser(fr, 33.865, 36.06, 12)
    to_draw_line(fr)
    assert fr.evaluate("() => document.getElementById('dr-msg').textContent") == 'Dessinez du doigt. Deux doigts déplacent la carte.'
    assert fr.evaluate(STATE)['ta'] == 'none' and fr.evaluate(STATE)['drag'] is False
    ox, oy = origin(pg, fr)
    cdp = pg.context.new_cdp_session(pg)
    fr.evaluate("() => { window.__ev = []; ['pointerdown', 'pointerup', 'pointercancel'].forEach(n => document.getElementById('map').addEventListener(n, e => window.__ev.push(n), true)); }")
    c0 = fr.evaluate("() => __RP.map.getCenter()")
    # un doigt dessine, la carte ne bouge pas, le navigateur ne prend pas le doigt
    touch(cdp, 'touchStart', [(ox + 100, oy + 400)])
    for i in range(1, 26):
        touch(cdp, 'touchMove', [(ox + 100 + i * 8, oy + 400 + 40 * math.sin(i / 4))])
    assert fr.evaluate(STATE)['stroke'] is True and fr.evaluate("() => __RP.map.getCenter()") == c0
    touch(cdp, 'touchEnd', [])
    lines = fr.evaluate(LINES)
    assert len(lines) == 1 and lines[0]['closed'] is False and fr.evaluate("() => __RP.map.getCenter()") == c0 and 'pointercancel' not in fr.evaluate("() => window.__ev")
    assert fr.evaluate(STATE)['tool'] == 'line' and fr.evaluate(STATE)['sel'] is None
    # un toucher : rien
    touch(cdp, 'touchStart', [(ox + 200, oy + 300)])
    touch(cdp, 'touchEnd', [])
    assert len(fr.evaluate(LINES)) == 1 and fr.evaluate(STATE)['build'] == 0
    # un second doigt annule le trait en cours, rien n'est créé, puis la carte se déplace à deux doigts
    touch(cdp, 'touchStart', [(ox + 100, oy + 500)])
    for i in range(1, 10):
        touch(cdp, 'touchMove', [(ox + 100 + i * 8, oy + 500)])
    assert fr.evaluate(STATE)['stroke'] is True
    touch(cdp, 'touchStart', [(ox + 172, oy + 500), (ox + 300, oy + 500)])
    assert fr.evaluate(STATE)['stroke'] is False
    for i in range(1, 15):
        touch(cdp, 'touchMove', [(ox + 172 + i * 6, oy + 500 + i * 4), (ox + 300 + i * 6, oy + 500 + i * 4)])
    touch(cdp, 'touchEnd', [])
    assert len(fr.evaluate(LINES)) == 1 and fr.evaluate("() => __RP.map.getCenter()") != c0
    assert 'pointercancel' not in fr.evaluate("() => window.__ev")
    # le déplacement revient à chaque sortie de l'état
    outs = {
        'bascule éteinte': "() => { DR.free = false; drSyncUi(); }",
        'autre outil': "() => { DR.free = true; drSetTool('circle'); }",
        'objet choisi': "() => { DR.free = true; drSetTool('line'); const l = CF_LAYERS.find(x => x.items.length); drSelect(l.id, l.items[0].id); }",
        'autre mode': "() => { drDeselect(); drSetTool('line'); setTapMode('ref'); }",
        'sortie du dessin': "() => { setTapMode('draw'); drSetTool('line'); setTapMode('read'); }",
        'drExit': "() => { setTapMode('draw'); drSetTool('line'); drExit(); }",
    }
    for name, js in outs.items():
        if name != 'bascule éteinte':
            fr.evaluate("() => { if (tapMode !== 'draw') setTapMode('draw'); drDeselect(); drSetTool('line'); DR.free = true; drSyncUi(); }")
        assert fr.evaluate(STATE)['drag'] is False or name == 'bascule éteinte', name
        fr.evaluate(js)
        st = fr.evaluate(STATE)
        assert st['drag'] is True and st['cls'] is False and st['ta'] == 'none', (name, st)
    assert pg.errs == []
    pg.context.close()


@needs_pw
def test_the_freehand_line_reads_back_from_the_layer_json_and_leaves_for_the_export_like_a_touch_line(browser):
    pg = shell(browser, 1280, 800)
    fr = open_rp(pg)
    viser(fr, 33.865, 36.06, 12)
    to_draw_line(fr, free=False)
    ox, oy = origin(pg, fr)
    # la ligne par touchers : deux sommets, Terminer
    for x, y in ((220, 300), (600, 360)):
        pg.mouse.click(ox + x, oy + y)
    fr.locator('#dr-acts [data-dr="finish"]').click()
    fr.evaluate("() => { drDeselect(); drSetTool('line'); DR.free = true; drSyncUi(); }")                 # Terminer choisit la ligne : on la lâche, puis Ligne et la main levée
    mouse_stroke(pg, ox, oy, wave(150, 480, 60, dx=7, amp=50, k=0.12))
    items = fr.evaluate(LINES)
    assert len(items) == 2
    keys = lambda it: sorted(it.keys())  # noqa: E731
    assert keys(items[0]) == keys(items[1]) and all(type(items[0][k]) is type(items[1][k]) for k in items[0])        # mêmes champs, mêmes types
    assert items[0]['kind'] == items[1]['kind'] == 'lines' and items[1]['closed'] is False and items[1]['dash'] == 'solid'
    # le JSON du calque, relu
    stored = json.loads(fr.evaluate("() => localStorage.getItem('route_layers_v1')"))
    assert stored['format'] == 'dcs-layers-v1' and [i['points'] for l in stored['layers'] for i in l['items']] == [i['points'] for i in items]
    fr.evaluate("() => { loadLayers(); renderLayers(); drawLayers(); }")
    back = fr.evaluate(LINES)
    assert [i['points'] for i in back] == [i['points'] for i in items] and keys(back[1]) == keys(items[1])
    # l'export vers le briefing : le trait des deux lignes est dans le calque rendu (ses sommets, comme ceux de la ligne par touchers), et l'export part
    poser_mode(fr, 'read')
    counts = fr.evaluate("() => [...document.querySelectorAll('.leaflet-layers-pane path')].map(p => (p.getAttribute('d') || '').split('L').length)")
    assert counts.count(2) >= 1 and counts.count(len(items[1]['points'])) >= 1, (counts, len(items[1]['points']))
    fr.evaluate("() => { window.__shots = []; window.html2canvas = function () { window.__shots.push(document.querySelectorAll('.leaflet-layers-pane path').length); return Promise.reject(new Error('banc')); }; }")
    cadre_export(fr, True)
    fr.evaluate('() => { expGo(); }')
    attendre(fr, 'window.__shots.length === 1', "le rendu parti (html2canvas appelé)")
    assert pg.errs == []
    pg.context.close()


@needs_pw
def test_a_stroke_left_open_by_a_lost_pointer_up_is_dropped_and_the_next_complete_stroke_makes_the_only_line(browser):
    pg = shell(browser, 1280, 800)
    fr = open_rp(pg)
    viser(fr, 33.865, 36.06, 12)
    to_draw_line(fr)
    ox, oy = origin(pg, fr)
    cdp = pg.context.new_cdp_session(pg)
    # 1. le bouton relâché sans pointerup : le mouvement suivant, bouton gauche absent, abandonne le trait
    pg.mouse.move(ox + 200, oy + 300)
    pg.mouse.down()
    pg.mouse.move(ox + 260, oy + 340, steps=4)
    assert fr.evaluate(STATE)['stroke'] is True
    cdp.send('Input.dispatchMouseEvent', {'type': 'mouseMoved', 'x': ox + 300, 'y': oy + 360, 'button': 'none', 'buttons': 0})
    assert fr.evaluate(STATE)['stroke'] is False and len(fr.evaluate(LINES)) == 0
    pg.mouse.up()
    # 2. un pointerdown du même pointeur sur un trait resté ouvert : l'ancien s'abandonne, le neuf commence
    pg.mouse.move(ox + 200, oy + 300)
    pg.mouse.down()
    pg.mouse.move(ox + 260, oy + 340, steps=4)
    cdp.send('Input.dispatchMouseEvent', {'type': 'mousePressed', 'x': ox + 300, 'y': oy + 200, 'button': 'left', 'buttons': 1, 'clickCount': 1})
    assert fr.evaluate("() => DR.stroke && DR.stroke.pts.length") == 1
    for x, y in wave(300, 200, 30)[1:]:
        pg.mouse.move(ox + x, oy + y)
    pg.mouse.up()
    lines = fr.evaluate(LINES)
    assert len(lines) == 1 and fr.evaluate(STATE)['stroke'] is False
    first = container_px(fr, [lines[0]['points'][0]])[0]
    assert abs(first[0] - 300) < 1.5 and abs(first[1] - 200) < 1.5                  # la ligne est celle du second trait
    # 3. la capture perdue abandonne le trait
    pg.mouse.move(ox + 200, oy + 400)
    pg.mouse.down()
    pg.mouse.move(ox + 260, oy + 440, steps=4)
    assert fr.evaluate(STATE)['stroke'] is True
    fr.evaluate("() => document.getElementById('map').releasePointerCapture(DR.stroke.id)")
    attendre(fr, 'DR.stroke === null', 'le trait abandonné à la capture perdue')
    pg.mouse.up()
    assert len(fr.evaluate(LINES)) == 1 and pg.errs == []
    pg.context.close()
