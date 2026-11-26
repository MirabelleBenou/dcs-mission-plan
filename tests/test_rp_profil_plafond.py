"""Le haut réglable du graphique du Profil du sol du Route Planner (MP-V2.1.0+21), joué sur le shell construit (dist/dcs_mission_plan.html, chromium), sans réseau : le relief de banc de test_rp_profil
(une plaine à 100 m et, dans chaque tuile, une crête nord-sud à 300 m ; Syria, tuiles du niveau 11). Les contrôles passent par le DOM, dans le shell.
Les sections suivent les règles du cadrage : l'échelle (1), la colonne (2), les bornes et le pas (3), sa présence (4), le retour à Auto et le stockage (5), le doigt et le clavier (6), le Field Manual et les textes (8, 9)."""
import hashlib
import json
import math
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tests'))
from test_rp_menaces import (Bench, SHELL, browser, display, needs_pw, sym)  # noqa: E402,F401
from test_rp_profil import east_route, pt, rects, route, tick, wait_prof  # noqa: E402,F401

NB = ' '                      # l'espace fine des milliers, en français
THREAT = [sym(0, 'sa-6', name='S6')]
# l'échelle de la base (MP-V2.1.0+20) sur ce banc : bas, haut et pas des graduations, par taille et par unité
BASE_SCALE = {(1280, 800): {'m': (0, 800, 200), 'ft': (0, 3000, 1000)}, (412, 915): {'m': (0, 1000, 500), 'ft': (0, 3000, 1000)}}
# le dessin de la base à 345 × 590 (la colonne y est absente) : sha256 de l'intérieur du SVG, unité m puis ft
BASE_SVG_SHA = {'m': '4bad7d983afbb285fb112ef269f9ae4b574f2de860caabe6d631dd78bfb34a00', 'ft': '20c35e739ab17da9fd832dccad67a20ab50d0ef3dd94a210bffa3e3a1d0e2297'}


def open_t(br, w, h, touch, lang='fr'):
    """Comme open_rp, avec le doigt au choix (une tablette de 820 px est au doigt, un écran de 1 280 px à la souris)."""
    ctx = br.new_context(viewport={'width': w, 'height': h}, has_touch=touch, is_mobile=touch)
    ctx.add_init_script("try{localStorage.setItem('lang_v1','%s')}catch(e){}" % lang)
    pg = ctx.new_page()
    pg.errs = []
    pg.on('pageerror', lambda e: pg.errs.append(str(e)))
    pg.bench = Bench()
    pg.route('**/*', pg.bench.handler)
    pg.goto('about:blank')
    pg.goto(SHELL, wait_until='commit')
    pg.wait_for_function("typeof NAV !== 'undefined' && typeof openModule === 'function'", timeout=30000)
    pg.wait_for_timeout(600)
    pg.evaluate("MP_WORK_EXAMPLE('fl')")
    pg.wait_for_timeout(1200)
    pg.evaluate("openModule('rp')")
    pg.wait_for_timeout(2300)
    fr = next(f for f in pg.frames if f != pg.main_frame and f.evaluate("typeof window.__RP !== 'undefined'"))
    return pg, fr


def start(br, w=1280, h=800, touch=None, lang='fr', items=None, pts=None):
    pg, fr = open_t(br, w, h, w < 700 if touch is None else touch, lang)
    tick(fr, pg)
    route(fr, pts or east_route(), THREAT if items is None else items)
    wait_prof(fr)
    pg.wait_for_timeout(700)
    return pg, fr


SCALE = """() => { const v = __RP.prof.view, t = Array.from(document.querySelectorAll('text.prof-ax')).filter(e => !e.classList.contains('prof-un') && e.getAttribute('text-anchor') === 'end')
    .map(e => parseFloat(e.textContent.replace(/[^0-9.-]/g, '').replace('\\u2212', '-')));
  return { bottom: v.ulo, top: v.uhi, step: t.length > 1 ? Math.abs(t[1] - t[0]) : null, ticks: t, mr: v.mr, pw: v.pw, set: v.set, topM: __RP.prof.topM }; }"""


def scale(fr):
    return fr.evaluate(SCALE)


def unit(fr, pg, u):
    fr.evaluate("S.units.altitude = '%s'; renderAll();" % u)
    pg.wait_for_timeout(500)
    wait_prof(fr)


def set_top(fr, pg, val):
    """Règle le curseur comme le ferait un glisser : la valeur, l'événement input."""
    fr.evaluate("(x) => { const i = document.querySelector('.prof-sli'); i.value = String(x); i.dispatchEvent(new Event('input', { bubbles: true })); }", val)
    pg.wait_for_timeout(200)


def auto(fr, pg):
    fr.evaluate("document.querySelector('.prof-sla').click()")
    pg.wait_for_timeout(200)


def col(fr):
    return fr.evaluate("""() => { const q = s => { const e = document.querySelector(s); if (!e) return null; const b = e.getBoundingClientRect(); return [b.x, b.y, b.width, b.height]; };
      const sl = document.querySelector('.prof-sl'), i = document.querySelector('.prof-sli'), a = document.querySelector('.prof-sla');
      return { sl: q('.prof-sl'), val: q('.prof-slv'), inp: q('.prof-sli'), auto: q('.prof-sla'), svg: q('.prof-svg'), prof: q('#rp-prof'), fb: q('.prof-fb'), g: q('.prof-g'),
        shown: !!sl && !sl.hidden && getComputedStyle(sl).display !== 'none', text: document.querySelector('.prof-slv').textContent, vw: document.querySelector('.prof-slv').scrollWidth,
        min: i.min, max: i.max, step: i.step, value: i.value, label: i.getAttribute('aria-label'), vtext: i.getAttribute('aria-valuetext'), orient: i.getAttribute('aria-orientation'), type: i.type,
        pressed: a.getAttribute('aria-pressed'), atext: a.textContent, topM: __RP.prof.topM }; }""")


def frame_texts(fr):
    """Les textes de l'échelle (la sécurité, le nom des menaces) dont la boîte sort du cadre du graphique."""
    return fr.evaluate("""() => { const v = __RP.prof.view, out = [];
      document.querySelectorAll('#rp-prof svg text.prof-sv, #rp-prof svg text.prof-zname').forEach(e => { const b = e.getBBox(); if (b.y < v.mt - 0.01 || b.y + b.height > v.axisY + 0.01) out.push([e.className.baseVal, b.y, b.height]); });
      return out; }""")


# ---------- règle 1 : l'échelle ----------
@needs_pw
@pytest.mark.parametrize('w,h', [(1280, 800), (412, 915)])
def test_auto_is_the_scale_of_the_base_and_pressing_auto_gives_it_back(browser, w, h):
    pg, fr = start(browser, w, h)
    for u in ('m', 'ft'):
        unit(fr, pg, u)
        sc = scale(fr)
        assert (sc['bottom'], sc['top'], sc['step']) == BASE_SCALE[(w, h)][u] and sc['set'] is False and sc['topM'] is None, (u, sc)
        assert col(fr)['pressed'] == 'true' and col(fr)['atext'] == 'AUTO'
        before = fr.evaluate("document.querySelector('.prof-svg').innerHTML")
        c = col(fr)
        set_top(fr, pg, c['min'])
        moved = scale(fr)
        assert moved['set'] is True and moved['top'] == float(c['min']) and col(fr)['pressed'] == 'false', moved
        assert fr.evaluate("document.querySelector('.prof-svg').innerHTML") != before
        auto(fr, pg)
        assert scale(fr) == sc and col(fr)['pressed'] == 'true' and fr.evaluate("document.querySelector('.prof-svg').innerHTML") == before       # Auto : le même dessin, à l'octet
    assert pg.errs == []
    pg.context.close()


@needs_pw
@pytest.mark.parametrize('u', ['m', 'ft'])
def test_without_the_column_the_drawing_is_the_base_drawing(browser, u):
    pg, fr = start(browser, 345, 590)
    unit(fr, pg, u)
    assert col(fr)['shown'] is False and scale(fr)['mr'] == 8
    svg = fr.evaluate("document.querySelector('.prof-svg').innerHTML")
    assert 'prof-clip-top' not in svg and '<g clip-path' not in svg.replace('<g clip-path="url(#prof-clip)"', '')
    assert hashlib.sha256(svg.encode('utf-8')).hexdigest() == BASE_SVG_SHA[u]
    assert pg.errs == []
    pg.context.close()


@needs_pw
@pytest.mark.parametrize('w,h', [(1280, 800), (412, 915)])
def test_a_set_top_sets_the_graduations_and_the_zone_climbs_to_the_ceiling(browser, w, h):
    pg, fr = start(browser, w, h, items=[sym(0, 'sa-8', name='S8')])             # un SA-8 : plafond à 5 100 m ; au-dessus du haut, la zone est coupée
    for u, val in (('m', 6100), ('ft', 20000)):
        unit(fr, pg, u)
        set_top(fr, pg, val)
        sc = scale(fr)
        assert (sc['bottom'], sc['top'], sc['set']) == (0, val, True), sc
        assert sorted(sc['ticks']) == [k * sc['step'] for k in range(int(val // sc['step']) + 1)], sc                 # les graduations se recalculent sur le haut réglé
        z = fr.evaluate("""() => { const p = document.querySelector('path.prof-zone'), b = p.getBBox(), v = __RP.prof.view, c = __RP.prof.zones[0].top;
          return { y0: b.y, y1: b.y + b.height, yc: v.Y(Math.min(c, v.uhi / v.uf)), mt: v.mt, ceil: c }; }""")
        assert abs(z['y0'] - z['yc']) < 0.6 and z['y0'] > z['mt'] + 1, (u, z)        # 6 100 m et 20 000 ft sont au-dessus du plafond de 5 100 m : la zone s'arrête à son plafond, en dessous du haut
    unit(fr, pg, 'm')
    set_top(fr, pg, 3000)
    z = fr.evaluate("""() => { const b = document.querySelector('path.prof-zone').getBBox(); return [b.y, __RP.prof.view.mt]; }""")
    assert abs(z[0] - z[1]) < 0.01                                                    # un haut sous le plafond : la zone est coupée au haut
    assert fr.evaluate("document.querySelector('path.prof-zone').parentNode.getAttribute('clip-path')") == 'url(#prof-clip)'
    assert pg.errs == []
    pg.context.close()


@needs_pw
def test_the_zone_of_a_sa_6_climbs_to_the_top_at_6100_m_and_at_20000_ft(browser):
    pg, fr = start(browser)                                                           # un SA-6 : plafond à 8 100 m, plus haut que 20 000 ft (6 096 m)
    for u, val in (('m', 6100), ('ft', 20000)):
        unit(fr, pg, u)
        set_top(fr, pg, val)
        z = fr.evaluate("() => { const b = document.querySelector('path.prof-zone').getBBox(); return [b.y, __RP.prof.view.mt, __RP.prof.zones[0].top]; }")
        assert z[2] == 8100 and abs(z[0] - z[1]) < 0.01, (u, z)
    assert pg.errs == []
    pg.context.close()


@needs_pw
@pytest.mark.parametrize('w,h', [(1280, 800), (412, 915)])
def test_no_text_is_drawn_outside_the_frame_at_any_top_and_what_is_above_is_cut(browser, w, h):
    pg, fr = start(browser, w, h)
    for u in ('m', 'ft'):
        unit(fr, pg, u)
        c = col(fr)
        lo, hi, st = float(c['min']), float(c['max']), float(c['step'])
        n = int((hi - lo) / st)
        res = fr.evaluate("""([lo, st, n]) => { const i = document.querySelector('.prof-sli'), out = [];
          for (let k = 0; k <= n; k++) {
            i.value = String(lo + k * st); i.dispatchEvent(new Event('input', { bubbles: true }));
            const v = __RP.prof.view, bad = [];
            document.querySelectorAll('#rp-prof svg text.prof-sv, #rp-prof svg text.prof-zname').forEach(e => { const b = e.getBBox(); if (b.y < v.mt - 0.01 || b.y + b.height > v.axisY + 0.01) bad.push([e.className.baseVal, b.y, b.height]); });
            out.push({ top: v.uhi, want: lo + k * st, bad: bad, sv: document.querySelectorAll('text.prof-sv').length, line: document.querySelectorAll('line.prof-safe').length, clip: document.querySelectorAll('g[clip-path="url(#prof-clip-top)"]').length }); }
          return out; }""", [lo, st, n])
        assert len(res) == n + 1
        for r in res:
            assert r['top'] == r['want'] and r['bad'] == [] and r['line'] == 1 and r['clip'] == 3, (u, r)
        assert res[0]['sv'] == 0 and res[-1]['sv'] == 1, (u, res[0], res[-1])          # un chiffre de sécurité au-dessus du haut ne s'affiche pas ; plus bas dans le cadre, il s'affiche
        k = next(i for i, r in enumerate(res) if r['sv'] == 1)
        assert all(r['sv'] == 1 for r in res[k:]) and all(r['sv'] == 0 for r in res[:k])
        assert frame_texts(fr) == []
    assert pg.errs == []
    pg.context.close()


@needs_pw
def test_a_ground_above_the_top_is_cut_and_the_cursor_dot_stays_in_the_frame(browser):
    pg, fr = start(browser, pts=[pt('A', 60 / 256, .5, 1500, 'MSL'), pt('B', 250 / 256, .5, 1500, 'MSL')])
    set_top(fr, pg, 300)
    r = fr.evaluate("""() => { const v = __RP.prof.view, out = {}; const g = document.querySelector('#rp-prof svg g[clip-path="url(#prof-clip-top)"]');
      const c = document.getElementById('prof-clip-top').firstElementChild;
      out.clip = [parseFloat(c.getAttribute('x')), parseFloat(c.getAttribute('y')), parseFloat(c.getAttribute('width')), parseFloat(c.getAttribute('height'))];
      out.v = [v.mt, v.W, v.gh]; out.fill = !!document.querySelector('#rp-prof svg g[clip-path] path.prof-fill'); out.line = !!document.querySelector('#rp-prof svg g[clip-path] polyline.prof-line'); return out; }""")
    assert r['clip'] == [0, r['v'][0], r['v'][1], r['v'][2] - r['v'][0]] and r['fill'] and r['line'], r
    assert frame_texts(fr) == []
    assert pg.errs == []
    pg.context.close()


# ---------- règle 3 : les bornes et le pas ----------
@needs_pw
def test_bounds_and_steps_in_metres_and_in_feet(browser):
    pg, fr = start(browser)
    unit(fr, pg, 'm')
    c = col(fr)
    assert (c['min'], c['max'], c['step']) == ('300', '6100', '100') and c['type'] == 'range' and c['orient'] == 'vertical'
    unit(fr, pg, 'ft')
    c = col(fr)
    assert (c['min'], c['max'], c['step']) == ('1000', '20000', '500')                  # 300 m = 984 ft, arrondi au pas supérieur ; 20 000 ft
    # en Auto : la valeur affichée est le haut de l'échelle, la poignée s'y tient
    assert c['text'] == '3' + NB + '000 ft' and c['value'] == '3000' and c['vtext'] == '3' + NB + '000 ft'
    set_top(fr, pg, 20000)
    c = col(fr)
    assert c['text'] == '20' + NB + '000 ft' and c['vtext'] == c['text'] and c['value'] == '20000' and c['topM'] == pytest.approx(20000 * 0.3048)
    # changer d'unité garde le haut réglé, arrondi au pas de la nouvelle unité : 20 000 ft = 6 096 m → 6 100 m
    unit(fr, pg, 'm')
    c = col(fr)
    assert c['text'] == '6' + NB + '100 m' and c['value'] == '6100' and c['pressed'] == 'false' and scale(fr)['set'] is True and scale(fr)['top'] == 6100
    set_top(fr, pg, 1700)
    unit(fr, pg, 'ft')
    c = col(fr)
    assert c['text'] == '5' + NB + '500 ft' and c['value'] == '5500' and scale(fr)['top'] == 5500        # 1 700 m = 5 577 ft → 5 500 ft
    unit(fr, pg, 'm')
    assert col(fr)['text'] == '1' + NB + '700 m'                                       # et revenu : 5 500 ft = 1 676 m → 1 700 m
    assert pg.errs == []
    pg.context.close()


@needs_pw
def test_bounds_follow_the_ground_and_a_high_route_raises_the_top(browser):
    # un sol à 1 000 m : le bas de l'échelle est 500 m, le curseur commence à 800 m (1 000 ft de plus en pieds : 2 625 → 3 000 ft)
    pg, fr = open_t(browser, 1280, 800, False)
    pg.bench.elev = __import__('test_rp_menaces').png(256, 256, lambda x, y: __import__('test_rp_menaces').rgb(1000))
    tick(fr, pg)
    route(fr, [pt('A', 60 / 256, .5, 1500, 'MSL'), pt('B', 250 / 256, .5, 1500, 'MSL')])
    wait_prof(fr)
    pg.wait_for_timeout(700)
    c = col(fr)
    assert (c['min'], c['max'], c['step']) == ('800', '6100', '100'), c
    unit(fr, pg, 'ft')
    assert (col(fr)['min'], col(fr)['max'], col(fr)['step']) == ('3000', '20000', '500')
    # une route à 7 000 m : le haut automatique dépasse 6 100 m, le curseur monte au haut automatique arrondi au pas supérieur
    route(fr, [pt('A', 60 / 256, .5, 7000, 'MSL'), pt('B', 250 / 256, .5, 7000, 'MSL')])
    wait_prof(fr)
    pg.wait_for_timeout(700)
    unit(fr, pg, 'm')
    c, sc = col(fr), scale(fr)
    assert sc['top'] > 6100 and float(c['max']) == math.ceil(sc['top'] / 100) * 100 and float(c['value']) == float(c['max']), (c, sc)
    unit(fr, pg, 'ft')
    c, sc = col(fr), scale(fr)
    assert sc['top'] > 20000 and float(c['max']) == math.ceil(sc['top'] / 500) * 500, (c, sc)
    assert pg.errs == []
    pg.context.close()


# ---------- règles 2 et 4 : la colonne, sa place, sa présence ----------
@needs_pw
@pytest.mark.parametrize('w,h,touch', [(1280, 800, False), (820, 1180, True), (412, 915, True)])
def test_the_column_is_44_px_beside_the_graph_and_covers_nothing(browser, w, h, touch):
    pg, fr = start(browser, w, h, touch)
    c = col(fr)
    assert c['shown'] is True
    sv, sl, fb, pf = c['svg'], c['sl'], c['fb'], c['prof']
    assert sl[2] == 44 and abs(sl[0] + sl[2] - (sv[0] + sv[2])) < 0.01 and sl[1] == sv[1] and sl[3] == sv[3]       # 44 px de large, collée au bord droit du graphique, de sa hauteur
    assert sl[1] >= fb[1] + fb[3] - 0.01 and sl[1] + sl[3] <= pf[1] + pf[3] + 0.01 and sl[0] >= pf[0]              # sous l'en-tête et le bouton de repli, dans le bandeau
    v, i, a = c['val'], c['inp'], c['auto']
    assert abs(v[1] - sl[1]) < 0.01 and v[2] == 44 and v[3] == 16 and c['vw'] <= 44                                 # la valeur au-dessus
    assert a[2] == 44 and abs(a[1] + a[3] - (sl[1] + sl[3])) < 0.01 and a[3] == (44 if touch else 24)             # AUTO dessous, 44 × 44 au doigt
    assert i[2] == 44 and i[3] > i[2] and abs(i[1] - (v[1] + v[3])) < 1 and abs(i[1] + i[3] - a[1]) < 1           # le curseur vertical entre les deux, sur 44 px de large
    assert i[3] >= 40
    assert c['label'] == 'Haut du graphique' and c['atext'] == 'AUTO' and c['text'] == c['vtext']
    # la marge droite : rien du tracé sous la colonne
    r = fr.evaluate("""() => { const v = __RP.prof.view, W = v.W, lim = W - 44, bad = [];
      document.querySelectorAll('#rp-prof svg *').forEach(e => { if (!e.getBBox || e.closest('defs') || e.tagName === 'svg' || e.tagName === 'g') return; const b = e.getBBox(); if (b.width && b.x + b.width > lim + 0.01) bad.push([e.tagName, e.getAttribute('class'), b.x + b.width]); });
      return { mr: v.mr, plotRight: W - v.mr, lim: lim, bad: bad, over: [document.getElementById('rp-prof').scrollWidth, document.getElementById('rp-prof').clientWidth], page: [document.documentElement.scrollWidth, window.innerWidth] }; }""")
    assert r['mr'] == 52 and r['plotRight'] <= r['lim'] and r['bad'] == [], r
    assert r['over'][0] == r['over'][1] and r['page'][0] <= r['page'][1], r
    assert pg.errs == []
    pg.context.close()


@needs_pw
def test_the_column_is_absent_on_a_low_graph_and_when_folded_and_the_scale_is_auto_then(browser):
    pg, fr = start(browser, 412, 915)
    assert col(fr)['shown'] is True
    set_top(fr, pg, 2000)
    assert scale(fr)['top'] == 2000 and scale(fr)['set'] is True
    # le téléphone plié : 345 × 590, un graphique de 60 px
    pg.set_viewport_size({'width': 345, 'height': 590})
    pg.wait_for_timeout(900)
    wait_prof(fr)
    c, sc = col(fr), scale(fr)
    assert rects(fr)['svg'][3] == 60 and c['shown'] is False and sc['set'] is False and sc['mr'] == 8 and sc['top'] in (800, 1000), (c, sc)
    assert fr.evaluate("document.querySelector('.prof-sl').hidden") is True and c['sl'][2] == 0
    assert fr.evaluate("document.querySelector('#rp-prof').scrollWidth") == fr.evaluate("document.querySelector('#rp-prof').clientWidth")
    # le haut réglé ne s'applique pas tant que la colonne est absente ; il revient avec elle
    pg.set_viewport_size({'width': 412, 'height': 915})
    pg.wait_for_timeout(900)
    wait_prof(fr)
    assert col(fr)['shown'] is True and scale(fr)['top'] == 2000 and scale(fr)['set'] is True
    # le bandeau replié : pas de colonne
    fr.evaluate("document.querySelector('#rp-prof .prof-fb').click()")
    pg.wait_for_timeout(400)
    assert col(fr)['shown'] is False
    fr.evaluate("document.querySelector('#rp-prof .prof-fb').click()")
    pg.wait_for_timeout(500)
    wait_prof(fr)
    assert col(fr)['shown'] is True and scale(fr)['top'] == 2000
    assert pg.errs == []
    pg.context.close()


@needs_pw
def test_a_graph_of_100_px_holds_the_column_with_a_44_px_auto(browser):
    pg, fr = open_t(browser, 412, 915, True)
    tick(fr, pg)
    route(fr, east_route(), THREAT)
    wait_prof(fr)
    # une carte de 412 × 915 qui n'a que 100 px de graphique : la hauteur de .mapwrap fixe gh (la carte garde 140 px)
    for hgt in (580, 560):
        pg.set_viewport_size({'width': 412, 'height': hgt})
        pg.wait_for_timeout(900)
        wait_prof(fr)
        r = rects(fr)
        gh = r['svg'][3]
        c = col(fr)
        if gh >= 100:
            i, a = c['inp'], c['auto']
            assert c['shown'] is True and a[2] == 44 and a[3] == 44 and i[3] >= 40 and i[2] == 44, (gh, c)
            assert i[1] >= c['val'][1] + 16 - 1 and i[1] + i[3] <= a[1] + 1
        else:
            assert c['shown'] is False, (gh, c)
    pg.set_viewport_size({'width': 412, 'height': 915})
    pg.wait_for_timeout(900)
    # le seuil exact : 100 px → présente, 99 px → absente
    for gh, want in ((100, True), (99, False)):
        fr.evaluate("""(gh) => { const G = profGeom; window.__oldGeom = window.__oldGeom || G; profGeom = function () { const g = window.__oldGeom(); g.gh = gh; g.slOk = gh >= PROF_SL_MIN_GH; g.H = g.head + gh; return g; }; PROF.rsig = ''; profRender(); }""", gh)
        pg.wait_for_timeout(400)
        c = col(fr)
        assert c['shown'] is want, (gh, c)
        if want:
            assert c['sl'][3] == 100 and c['auto'][3] == 44 and c['inp'][3] >= 40, c
    assert pg.errs == []
    pg.context.close()


# ---------- règle 5 : le retour à Auto, le stockage ----------
@needs_pw
def test_back_to_auto_at_another_route_a_new_route_a_deletion_the_theatre_and_the_reload_but_not_at_a_point_move(browser):
    pg, fr = start(browser)
    base = scale(fr)
    assert base['set'] is False
    # le même parcours : modifier les points garde le haut réglé
    set_top(fr, pg, 2500)
    assert scale(fr)['top'] == 2500
    fr.evaluate("S.points[1].lat += 1e-6; renderAll();")                                 # un point déplacé
    pg.wait_for_timeout(1700)
    wait_prof(fr)
    assert scale(fr)['top'] == 2500 and scale(fr)['set'] is True and col(fr)['pressed'] == 'false'
    fr.evaluate("S.points[0].alt = 700; renderAll();")                                    # une altitude
    pg.wait_for_timeout(500)
    wait_prof(fr)
    assert scale(fr)['top'] == 2500
    fr.evaluate("S.points.push(Object.assign({}, S.points[1], { pid: 'pz', name: 'C' })); S.points[2].lat += 0.01; renderAll();")        # un point ajouté
    pg.wait_for_timeout(1700)
    wait_prof(fr)
    assert scale(fr)['top'] == 2500 and scale(fr)['set'] is True
    fr.evaluate("S.points.pop(); renderAll();")
    pg.wait_for_timeout(1700)
    wait_prof(fr)
    # une route neuve : Auto
    fr.evaluate("addRoute()")
    pg.wait_for_timeout(600)
    assert fr.evaluate("__RP.prof.topM") is None
    # revenir à la première route : Auto aussi (une autre route)
    fr.evaluate("activateRoute(0)")
    pg.wait_for_timeout(1800)
    wait_prof(fr)
    assert scale(fr)['set'] is False and scale(fr)['topM'] is None
    set_top(fr, pg, 3000)
    assert scale(fr)['top'] == 3000
    fr.evaluate("activateRoute(1)")                                                       # la route neuve, vide
    pg.wait_for_timeout(600)
    assert fr.evaluate("__RP.prof.topM") is None
    fr.evaluate("void deleteRoute()")                                                          # la route vide choisie est supprimée sans question : la première revient
    pg.wait_for_timeout(1800)
    wait_prof(fr)
    assert fr.evaluate("RSET.routes.length") == 1 and scale(fr)['set'] is False
    # la route choisie supprimée : une copie (choisie), réglée, puis supprimée
    fr.evaluate("duplicateRoute()")
    pg.wait_for_timeout(1800)
    wait_prof(fr)
    assert fr.evaluate("RSET.routes.length") == 2 and scale(fr)['set'] is False
    set_top(fr, pg, 3000)
    assert scale(fr)['top'] == 3000
    fr.evaluate("void deleteRoute()")
    pg.wait_for_timeout(500)
    fr.evaluate("document.getElementById('ui-confirm-ok').click()")
    pg.wait_for_timeout(1800)
    wait_prof(fr)
    assert fr.evaluate("RSET.routes.length") == 1 and fr.evaluate("__RP.prof.topM") is None and scale(fr)['set'] is False
    set_top(fr, pg, 3000)
    assert scale(fr)['top'] == 3000
    # un autre théâtre : Auto
    fr.evaluate("(id) => { const s = document.getElementById('theatre'); s.value = id; s.dispatchEvent(new Event('change', { bubbles: true })); }", 'Caucasus')
    pg.wait_for_timeout(800)
    assert fr.evaluate("__RP.prof.topM") is None
    fr.evaluate("(id) => { const s = document.getElementById('theatre'); s.value = id; s.dispatchEvent(new Event('change', { bubbles: true })); }", 'Syria')
    pg.wait_for_timeout(1200)
    assert fr.evaluate("__RP.prof.topM") is None
    assert pg.errs == []
    pg.context.close()


@needs_pw
def test_back_to_auto_at_a_reload_and_nothing_is_written(browser):
    pg, fr = start(browser)
    store = "JSON.stringify(Object.keys(localStorage).sort().map(k => [k, localStorage.getItem(k)]))"
    work = "JSON.stringify([setObject(), S.points, S.units, S.ui])"
    s0, w0 = fr.evaluate(store), fr.evaluate(work)
    disp = json.loads(fr.evaluate("localStorage.getItem('rp_display_v1')"))
    assert 'topM' not in disp and 'top' not in disp
    for val in (1000, 6100, 300):
        set_top(fr, pg, val)
    pg.wait_for_timeout(300)
    assert fr.evaluate("__RP.prof.topM") == 300
    assert fr.evaluate(store) == s0 and fr.evaluate(work) == w0                          # le stockage du navigateur et le fichier de travail : identiques
    unit(fr, pg, 'ft')
    s1, w1 = fr.evaluate(store), fr.evaluate(work)
    auto(fr, pg)
    set_top(fr, pg, 5000)
    assert fr.evaluate(store) == s1 and fr.evaluate(work) == w1                          # en pieds aussi : rien d'écrit
    d1 = dict(json.loads(s1))
    assert 'rp_display_v1' in d1 and all('topM' not in v and 'prof-sl' not in v for v in d1.values())
    # un rechargement : Auto
    pg.reload(wait_until='commit')
    pg.wait_for_function("typeof NAV !== 'undefined' && typeof openModule === 'function'", timeout=30000)
    pg.wait_for_timeout(2000)
    pg.evaluate("openModule('rp')")
    pg.wait_for_timeout(2500)
    fr2 = next(f for f in pg.frames if f != pg.main_frame and f.evaluate("typeof window.__RP !== 'undefined'"))
    assert fr2.evaluate("__RP.prof.topM") is None
    assert pg.errs == []
    pg.context.close()


# ---------- règle 6 : le clavier et le glisser ----------
@needs_pw
@pytest.mark.parametrize('lang,label,unit_', [('fr', 'Haut du graphique', 'm'), ('en', 'Top of the graph', 'm')])
def test_the_keyboard_sets_the_top_by_one_step_and_enter_goes_back_to_auto(browser, lang, label, unit_):
    pg, fr = start(browser, lang=lang)
    c = col(fr)
    assert c['label'] == label and c['atext'] == 'AUTO' and c['pressed'] == 'true'
    fr.evaluate("document.querySelector('.prof-sli').focus()")
    start_v = float(col(fr)['value'])
    pg.keyboard.press('ArrowUp')
    pg.wait_for_timeout(200)
    c = col(fr)
    assert float(c['value']) == start_v + 100 and scale(fr)['top'] == start_v + 100 and c['pressed'] == 'false', c
    assert c['vtext'] == c['text'] and c['text'].endswith(' m')
    pg.keyboard.press('ArrowUp')
    pg.keyboard.press('ArrowDown')
    pg.wait_for_timeout(200)
    assert float(col(fr)['value']) == start_v + 100 and scale(fr)['top'] == start_v + 100
    pg.keyboard.press('Home')
    pg.wait_for_timeout(200)
    assert scale(fr)['top'] == 300 and col(fr)['value'] == '300'
    pg.keyboard.press('Home')
    pg.keyboard.press('ArrowDown')
    pg.wait_for_timeout(200)
    assert scale(fr)['top'] == 300                                                       # jamais sous le bas + 300 m
    # AUTO à Entrée
    fr.evaluate("document.querySelector('.prof-sla').focus()")
    pg.keyboard.press('Enter')
    pg.wait_for_timeout(300)
    c = col(fr)
    assert c['pressed'] == 'true' and scale(fr)['set'] is False and scale(fr)['top'] == 800 and fr.evaluate("document.activeElement.className") == 'prof-sla'
    # en pieds : un pas de 500 ft ; le texte a son unité
    unit(fr, pg, 'ft')
    fr.evaluate("document.querySelector('.prof-sli').focus()")
    v0 = float(col(fr)['value'])
    pg.keyboard.press('ArrowUp')
    pg.wait_for_timeout(200)
    c = col(fr)
    assert float(c['value']) == v0 + 500 and c['text'].endswith(' ft') and c['vtext'] == c['text'], c
    assert pg.errs == []
    pg.context.close()


def thumb_xy(c, frac):
    """Le centre de la poignée d'un curseur vertical : le bas du rectangle est le minimum."""
    x, y, w, h = c['inp']
    return x + w / 2, y + h - 8 - frac * (h - 16)


def map_state(fr):
    return fr.evaluate("(() => { const m = __RP.map, c = m.getCenter(); return [c.lat, c.lng, m.getZoom(), S.points.length, document.querySelectorAll('.rp-prof-dot').length]; })()")


@needs_pw
def test_dragging_the_slider_with_the_mouse_moves_neither_the_profile_cursor_nor_the_map(browser):
    pg, fr = start(browser)
    m0 = map_state(fr)
    c = col(fr)
    assert fr.evaluate("__RP.prof.cur") is None
    # un glisser, sans curseur du profil
    x, y = thumb_xy(c, (float(c['value']) - float(c['min'])) / (float(c['max']) - float(c['min'])))
    pg.mouse.move(x, y)
    pg.mouse.down()
    pg.mouse.move(x, y - 40, steps=5)
    pg.mouse.move(x, y - 80, steps=5)
    pg.mouse.up()
    pg.wait_for_timeout(300)
    c2 = col(fr)
    assert float(c2['value']) > float(c['value']) and c2['pressed'] == 'false' and scale(fr)['top'] == float(c2['value'])
    assert fr.evaluate("__RP.prof.cur") is None and fr.evaluate("document.querySelector('.prof-bub').hidden") is True
    assert map_state(fr) == m0
    # un curseur du profil posé, puis le même glisser : le curseur reste au même échantillon, avec sa bulle
    sv = c2['svg']
    pg.mouse.move(sv[0] + 300, sv[1] + 90)
    pg.wait_for_timeout(300)
    k0 = fr.evaluate("__RP.prof.cur")
    txt0 = fr.evaluate("document.querySelector('.prof-bub').textContent")
    assert k0 is not None
    x, y = thumb_xy(c2, (float(c2['value']) - float(c2['min'])) / (float(c2['max']) - float(c2['min'])))
    pg.mouse.move(x, y)                                                                  # de la zone du graphique à la colonne : le curseur du profil reste
    assert fr.evaluate("__RP.prof.cur") == k0
    pg.mouse.down()
    pg.mouse.move(x, y + 40, steps=5)
    pg.mouse.up()
    pg.wait_for_timeout(300)
    assert fr.evaluate("__RP.prof.cur") == k0 and fr.evaluate("document.querySelector('.prof-bub').hidden") is False and fr.evaluate("document.querySelector('.prof-bub').textContent").split(' · ')[0] == txt0.split(' · ')[0]
    assert fr.evaluate("document.querySelectorAll('.rp-prof-dot').length") == 1 and fr.evaluate("document.querySelectorAll('#prof-cur .prof-cl').length") == 1
    b = fr.evaluate("""() => { const g = document.querySelector('.prof-g').getBoundingClientRect(), b = document.querySelector('.prof-bub').getBoundingClientRect(), s = document.querySelector('.prof-sl').getBoundingClientRect(); return [b.left - g.left, b.right <= s.left + 0.01]; }""")
    assert b[0] >= -0.01 and b[1] is True                                                # la bulle ne recouvre pas la colonne
    # la souris quitte la colonne : le curseur du profil s'efface
    pg.mouse.move(5, 5)
    pg.wait_for_timeout(250)
    assert fr.evaluate("__RP.prof.cur") is None and fr.evaluate("document.querySelectorAll('.rp-prof-dot').length") == 0
    assert map_state(fr)[:4] == m0[:4]
    assert pg.errs == []
    pg.context.close()


def touch_drag(pg, x0, y0, x1, y1, steps=6):
    cdp = pg.context.new_cdp_session(pg)
    cdp.send('Input.dispatchTouchEvent', {'type': 'touchStart', 'touchPoints': [{'x': x0, 'y': y0, 'id': 1}]})
    for k in range(1, steps + 1):
        cdp.send('Input.dispatchTouchEvent', {'type': 'touchMove', 'touchPoints': [{'x': x0 + (x1 - x0) * k / steps, 'y': y0 + (y1 - y0) * k / steps, 'id': 1}]})
    cdp.send('Input.dispatchTouchEvent', {'type': 'touchEnd', 'touchPoints': []})
    cdp.detach()


@needs_pw
def test_touching_and_dragging_the_slider_with_a_finger_moves_neither_the_profile_cursor_nor_the_map(browser):
    pg, fr = start(browser, 412, 915)
    m0 = map_state(fr)
    c = col(fr)
    sv = c['svg']
    # le curseur du profil posé au toucher
    pg.touchscreen.tap(sv[0] + 150, sv[1] + 60)
    pg.wait_for_timeout(300)
    k0 = fr.evaluate("__RP.prof.cur")
    assert k0 is not None and fr.evaluate("document.querySelector('.prof-bub').hidden") is False
    txt0 = fr.evaluate("document.querySelector('.prof-bub').textContent").split(' · ')[0]
    # toucher la colonne (AUTO, la valeur) : le curseur du profil reste
    a = c['auto']
    pg.touchscreen.tap(a[0] + 22, a[1] + 22)
    pg.wait_for_timeout(300)
    assert fr.evaluate("__RP.prof.cur") == k0 and fr.evaluate("document.querySelector('.prof-bub').hidden") is False
    # un glisser du doigt sur le curseur
    x, y = thumb_xy(c, (float(c['value']) - float(c['min'])) / (float(c['max']) - float(c['min'])))
    touch_drag(pg, x, y, x, y - 60)
    pg.wait_for_timeout(400)
    c2 = col(fr)
    assert float(c2['value']) > float(c['value']) and c2['pressed'] == 'false' and scale(fr)['top'] == float(c2['value']), (c, c2)
    assert fr.evaluate("__RP.prof.cur") == k0 and fr.evaluate("document.querySelector('.prof-bub').textContent").split(' · ')[0] == txt0
    assert map_state(fr)[:4] == m0[:4] and fr.evaluate("document.querySelectorAll('.rp-prof-dot').length") == 1
    # AUTO au doigt : 44 × 44, l'échelle revient
    a = c2['auto']
    assert a[2] >= 44 and a[3] >= 44
    pg.touchscreen.tap(a[0] + 22, a[1] + 22)
    pg.wait_for_timeout(300)
    assert scale(fr)['set'] is False and col(fr)['pressed'] == 'true' and fr.evaluate("__RP.prof.cur") == k0
    assert map_state(fr)[:4] == m0[:4]
    # un toucher hors du graphique et de la colonne efface toujours le curseur du profil
    pg.touchscreen.tap(200, 100)
    pg.wait_for_timeout(300)
    assert fr.evaluate("__RP.prof.cur") is None
    assert pg.errs == []
    pg.context.close()


# ---------- règles 8 et 9 : le Field Manual, les textes, le numéro ----------
def test_the_field_manual_the_texts_the_changelog_and_the_number_say_it():
    fm = (ROOT / 'dist' / 'dcs_field_manual.html').read_text(encoding='utf-8')
    rp = fm[fm.index('<section id="page-rp"'):fm.index('<!-- /page-rp -->')].replace(' ', ' ').replace('\xa0', ' ')
    fr_s = ('À droite du graphique, un <strong>curseur</strong> règle le haut de l’échelle, jusqu’à 20 000 ft : plus haut pour voir les menaces jusqu’à leur plafond, plus bas pour regarder le sol de près ; '
            '<strong>AUTO</strong> revient à l’échelle automatique, comme chaque nouvelle route. Il manque quand le graphique est trop bas.')
    en_s = ('On the right of the graph, a <strong>slider</strong> sets the top of the scale, up to 20,000 ft: higher to see the threats up to their ceiling, lower to look at the ground up close; '
            '<strong>AUTO</strong> goes back to the automatic scale, as each new route does. It is absent when the graph is too low.')
    assert rp.count(fr_s) == 1 and rp.count(en_s) == 1
    # le troisième élément du paragraphe, après « Le profil est un réglage d'écran… » : la phrase suit la deuxième dans le même paragraphe
    for a, b in (('Le profil est un réglage d’écran, hors du fichier de travail.', fr_s), ('The profile is a screen setting, outside the work file.', en_s)):
        i = rp.index(a)
        assert rp.index(b) > i and rp[i:rp.index(b)].count('<p') == 1 and rp[i:rp.index(b)].count('</p>') == 1 or rp[i + len(a):rp.index(b)] in ('</p><p>', '</p>\n<p>', ' ')
    assert rp.index('Le profil du sol') < rp.index(fr_s) < rp.index('La fiche d’un aérodrome')
    rpd = (ROOT / 'dist' / 'dcs_route_planner.html').read_text(encoding='utf-8')
    assert rpd.count("    'prof.top': 'Haut du graphique',") == 1 and rpd.count("    'prof.top': 'Top of the graph',") == 1
    log = (ROOT / 'CHANGELOG.md').read_bytes()
    assert hashlib.sha256(log).hexdigest() == 'fa8c60b56dbb7259e65e0b2fde3ce123696092e75eee529296c526b4633c55cb'
    text = log.decode('utf-8')
    assert text.count('`MP-V2.1.0+21` for this one') == 1
    prof = text.split('Unreleased', 1)[1]
    assert prof.index('A slider on the right of the graph sets its top, up to 20,000 ft') > prof.index('Ground profile under the route')
    assert re.search(r'^DEV_BUILD = 21$', (ROOT / 'version_block.py').read_text(encoding='utf-8'), re.M)
    assert 'MP-V2.1.0+21' in (ROOT / 'dist' / 'dcs_mission_plan.html').read_text(encoding='utf-8')
