"""Le profil du sol du Route Planner (MP-V2.1.0+18), joué sur le shell construit (dist/dcs_mission_plan.html, chromium), sans réseau : le banc de test_rp_menaces sert le relief
(une plaine à 100 m et, dans chaque tuile, une crête nord-sud à 300 m sur les colonnes 150 à 159 ; Syria, tuiles du niveau 11, un pixel vaut environ 64 m). Les contrôles passent par le DOM, dans le shell.
Les sections suivent celles du cadrage : la case, le bandeau, les deux chiffres de la branche, le tableau, la zone des menaces, la barre « route vue », le curseur, les tailles, le Field Manual."""
import json
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tests'))
from test_rp_menaces import (CREST_M, NBSP, PLAIN_M, TCOL, TX, TY, browser, display, needs_pw, open_rp, ready, setup, sym, tile_ll)  # noqa: E402,F401

PROF_READY = "(() => { const P = __RP.prof; return !!P.data && !P.data.fail && P.data.key === profKey() && !!P.view; })()"


def pt(name, fx, fy, alt=30, ref='AGL', tx=TX, ty=TY):
    lat, lon = tile_ll(tx, ty, fx, fy)
    return {'name': name, 'lat': lat, 'lon': lon, 'alt': alt, 'altRef': ref}


def tick(fr, pg, key='profile', on=True):
    display(fr, pg, True)
    if bool(fr.evaluate("DISP.%s" % key)) != on:
        fr.evaluate("document.querySelector('#dsp-panel [data-k=%s]').click()" % key)
        pg.wait_for_timeout(300)
    display(fr, pg, False)


def route(fr, pts, items=None):
    setup(fr, items or [], pts, wait=bool(items))


def wait_prof(fr, timeout=60000):
    fr.wait_for_function(PROF_READY, timeout=timeout)


def rects(fr):
    return fr.evaluate("""() => { const r = s => { const e = document.querySelector(s); if (!e) return null; const b = e.getBoundingClientRect(); return [Math.round(b.x * 10) / 10, Math.round(b.y * 10) / 10, Math.round(b.width * 10) / 10, Math.round(b.height * 10) / 10]; };
      return { map: r('#map'), prof: r('#rp-prof'), wrap: r('.mapwrap'), btn: r('#rp-prof button'), svg: r('.prof-svg') }; }""")


def prof_rows(fr):
    return fr.evaluate("Array.from(document.querySelectorAll('table.nav tr.prof')).map(e => e.textContent)")


def legs(fr):
    return fr.evaluate("""() => __RP.prof.data.legs.slice(1).map(l => ({ n: l.n, m: l.m, hi: l.hi >= 0 ? l.g[l.hi] : null, safe: l.safe.h, unk: l.safe.unk }))""")


# ---------- la case ----------
@needs_pw
def test_the_display_row_order_default_storage_theatres_and_dot(browser):
    pg, fr = open_rp(browser)
    assert fr.evaluate("DISP.profile") is False and fr.evaluate("DISP.profFold") is False and fr.evaluate("document.getElementById('dsp-dot').hidden") is True
    display(fr, pg, True)
    row = fr.evaluate("""(() => { const r = document.querySelector('#dsp-panel [data-k=profile]'); return { role: r.getAttribute('role'), checked: r.getAttribute('aria-checked'), cls: r.className,
        prev: r.previousElementSibling.getAttribute('data-k'), next: r.nextElementSibling.textContent.trim(), disabled: r.getAttribute('aria-disabled'), title: r.title, txt: r.textContent.trim() }; })()""")
    assert row == {'role': 'menuitemcheckbox', 'checked': 'false', 'cls': 'tbm-opt dsp-opt', 'prev': 'threats', 'next': 'Mission', 'disabled': None,
                   'title': 'Le sol sous la route, relevé dans DCS', 'txt': 'Profil du sol'}
    assert fr.evaluate("Array.from(document.querySelectorAll('#dsp-panel .dsp-opt')).slice(0, 3).map(e => e.getAttribute('data-k'))") == ['relief', 'threats', 'profile']
    fr.evaluate("document.querySelector('#dsp-panel [data-k=profile]').click()")
    pg.wait_for_timeout(300)
    assert fr.evaluate("DISP.profile") is True and fr.evaluate("document.getElementById('dsp-dot').hidden") is False
    st = json.loads(fr.evaluate("localStorage.getItem('rp_display_v1')"))
    assert st['profile'] is True and st['profFold'] is False and st['threats'] is True and st['thrStep'] == 2
    fr.evaluate("persistLayers()")
    assert 'profile' not in fr.evaluate("localStorage.getItem('route_state_v1')") and 'profile' not in (fr.evaluate("localStorage.getItem('route_layers_v1')") or '')
    display(fr, pg, False)
    # hors des trois théâtres : grisée, infobulle, aucun bandeau
    fr.evaluate("(id) => { const s = document.getElementById('theatre'); s.value = id; s.dispatchEvent(new Event('change', { bubbles: true })); }", 'Nevada')
    pg.wait_for_timeout(600)
    display(fr, pg, True)
    off = fr.evaluate("(() => { const r = document.querySelector('#dsp-panel [data-k=profile]'); return [r.getAttribute('aria-disabled'), r.title, r.getAttribute('aria-checked')]; })()")
    assert off == ['true', 'Profil du sol — absent de ce théâtre', 'false']
    fr.evaluate("document.querySelector('#dsp-panel [data-k=profile]').click()")
    pg.wait_for_timeout(200)
    assert fr.evaluate("DISP.profile") is True and fr.evaluate("document.getElementById('rp-prof')") is None       # le clic sur une ligne grisée ne change rien
    for th in ('Caucasus', 'GermanyCW', 'Syria'):
        fr.evaluate("(id) => { const s = document.getElementById('theatre'); s.value = id; s.dispatchEvent(new Event('change', { bubbles: true })); }", th)
        pg.wait_for_timeout(500)
        assert fr.evaluate("document.querySelector('#dsp-panel [data-k=profile]').getAttribute('aria-disabled')") is None, th
        assert fr.evaluate("document.querySelector('#dsp-panel [data-k=profile]').title") == 'Le sol sous la route, relevé dans DCS'
    assert pg.errs == []
    pg.context.close()


@needs_pw
def test_the_display_row_in_english(browser):
    pg, fr = open_rp(browser, lang='en')
    display(fr, pg, True)
    assert fr.evaluate("(() => { const r = document.querySelector('#dsp-panel [data-k=profile]'); return [r.textContent.trim(), r.title]; })()") == ['Ground profile', 'The ground under the route, read in DCS']
    fr.evaluate("(id) => { const s = document.getElementById('theatre'); s.value = id; s.dispatchEvent(new Event('change', { bubbles: true })); }", 'Nevada')
    pg.wait_for_timeout(500)
    assert fr.evaluate("document.querySelector('#dsp-panel [data-k=profile]').title") == 'Ground profile — not available for this theatre'
    pg.context.close()


# ---------- le bandeau ----------
@needs_pw
def test_the_strip_shrinks_the_map_folds_and_is_kept_on_reload(browser):
    pg, fr = open_rp(browser)
    route(fr, [pt('A', 100 / 256, .5, ref='MSL', alt=500), pt('B', 200 / 256, .5, ref='MSL', alt=500)])
    base = rects(fr)
    assert base['prof'] is None and fr.evaluate("document.getElementById('rp-prof')") is None                         # décoché : rien dans la page
    kids = fr.evaluate("Array.from(document.querySelector('.mapwrap').children).map(e => e.id || e.className)")
    style0 = fr.evaluate("document.querySelector('.mapwrap').getAttribute('style')")
    assert fr.evaluate("getComputedStyle(document.querySelector('.mapwrap')).getPropertyValue('--prof-h')") == ''
    tick(fr, pg)
    wait_prof(fr)
    pg.wait_for_timeout(300)
    on = rects(fr)
    cs = fr.evaluate("(() => { const c = getComputedStyle(document.getElementById('rp-prof')); return [c.backgroundColor, c.borderTopWidth, c.borderTopStyle, c.fontFamily.split(',')[0]]; })()")
    assert cs == ['rgb(26, 28, 20)', '2px', 'solid', 'Oswald']
    assert on['prof'][3] == 26 + 190 and on['prof'][2] == on['map'][2]                                   # 26 px d'en-tête, 190 px de graphique : carte large
    assert on['map'][3] == base['map'][3] - on['prof'][3] and on['map'][0] == base['map'][0] and on['map'][2] == base['map'][2]       # la carte rétrécit d'autant
    assert on['map'][1] + on['map'][3] <= on['prof'][1] + 0.5 and on['prof'][1] + on['prof'][3] == on['wrap'][1] + on['wrap'][3]       # jamais recouverte
    assert fr.evaluate("__RP.map.getSize().y") == on['map'][3]                                              # invalidateSize a été appelé
    assert fr.evaluate("document.querySelector('.prof-t').textContent") == 'PROFIL DU SOL'
    assert fr.evaluate("document.querySelector('.prof-leg').textContent").endswith('━ point le plus haut · ╍╍ sécurité') and 'menaces' not in fr.evaluate("document.querySelector('.prof-leg').textContent")
    fb = fr.evaluate("(() => { const b = document.querySelector('#rp-prof button'); return [b.textContent, b.getAttribute('aria-label'), b.getAttribute('aria-expanded')]; })()")
    assert fb == ['▾', 'Replier le profil', 'true']
    fr.evaluate("document.querySelector('#rp-prof button').click()")
    pg.wait_for_timeout(300)
    fold = rects(fr)
    assert fold['prof'][3] == 26 and fold['map'][3] == base['map'][3] - 26                                  # la carte reprend la place : 26 px restent
    assert fr.evaluate("document.querySelector('.prof-g').hidden") is True
    fb = fr.evaluate("(() => { const b = document.querySelector('#rp-prof button'); return [b.textContent, b.getAttribute('aria-label'), b.getAttribute('aria-expanded')]; })()")
    assert fb == ['▴', 'Déplier le profil', 'false']
    assert fr.evaluate("DISP.profFold") is True and json.loads(fr.evaluate("localStorage.getItem('rp_display_v1')"))['profFold'] is True
    # le rechargement garde la case et le repli
    store = fr.evaluate("localStorage.getItem('rp_display_v1')")
    pg.context.close()
    pg, fr = open_rp(browser, seed={'rp_display_v1': store})
    assert fr.evaluate("DISP.profile") is True and fr.evaluate("DISP.profFold") is True
    route(fr, [pt('A', 100 / 256, .5, ref='MSL', alt=500), pt('B', 200 / 256, .5, ref='MSL', alt=500)])
    pg.wait_for_timeout(500)
    assert rects(fr)['prof'][3] == 26
    fr.evaluate("document.querySelector('#rp-prof button').click()")
    pg.wait_for_timeout(300)
    assert rects(fr)['prof'][3] == 216
    # décoché : le bandeau part, la carte a sa taille d'avant
    tick(fr, pg, on=False)
    gone = rects(fr)
    assert fr.evaluate("document.getElementById('rp-prof')") is None and gone['map'][3] == base['map'][3] and gone['wrap'] == base['wrap']
    assert fr.evaluate("Array.from(document.querySelector('.mapwrap').children).map(e => e.id || e.className)") == kids and fr.evaluate("document.querySelector('.mapwrap').getAttribute('style')") == style0
    assert [e for e in pg.errs if 'sessionStorage' not in e] == []       # le banc de rechargement pose ses valeurs par sessionStorage : sa garde proteste sur la page vide
    pg.context.close()


@needs_pw
def test_fewer_than_two_points_say_so_and_a_theatre_without_relief_has_no_strip(browser):
    pg, fr = open_rp(browser)
    route(fr, [pt('A', .4, .5)])
    tick(fr, pg)
    pg.wait_for_timeout(500)
    assert fr.evaluate("document.getElementById('rp-prof') !== null") is True
    assert fr.evaluate("document.querySelector('.prof-svg').textContent") == 'Tracez au moins deux points.'
    fr.evaluate("(id) => { const s = document.getElementById('theatre'); s.value = id; s.dispatchEvent(new Event('change', { bubbles: true })); }", 'Nevada')
    pg.wait_for_timeout(600)
    assert fr.evaluate("document.getElementById('rp-prof')") is None and rects(fr)['map'][3] == rects(fr)['wrap'][3]
    assert pg.errs == []
    pg.context.close()


# ---------- les deux chiffres de la branche ----------
@needs_pw
def test_a_leg_across_the_crest_and_a_leg_that_runs_beside_it(browser):
    pg, fr = open_rp(browser)
    tick(fr, pg)
    # une branche qui coupe la crête : point le plus haut 300 m, sécurité 600 m et 2 000 ft
    route(fr, [pt('A', 100 / 256, .5), pt('B', 200 / 256, .5)])
    wait_prof(fr)
    pg.wait_for_timeout(400)
    g = legs(fr)[0]
    assert g['hi'] == pytest.approx(CREST_M, abs=0.01) and g['safe'] == pytest.approx(CREST_M, abs=0.01) and g['unk'] is False
    assert prof_rows(fr) == ['▲ Point le plus haut 300 m · sécurité 600 m']
    fr.evaluate("unChoose('ft')")
    pg.wait_for_timeout(500)
    assert prof_rows(fr) == ['▲ Point le plus haut 984 ft · sécurité 2' + NBSP + '000 ft']
    fr.evaluate("unChoose('m')")
    pg.wait_for_timeout(300)
    # une branche à moins de 5 NM de la crête sans la couper : 100 m, 600 m
    route(fr, [pt('A', 100 / 256, .3), pt('B', 100 / 256, .7)])
    wait_prof(fr)
    pg.wait_for_timeout(400)
    g = legs(fr)[0]
    assert g['hi'] == pytest.approx(PLAIN_M, abs=0.01) and g['safe'] == pytest.approx(CREST_M, abs=0.01)
    assert prof_rows(fr) == ['▲ Point le plus haut 100 m · sécurité 600 m']
    # le texte est en gras aux valeurs, sur le fond ambré, sous la ligne de branche
    d = fr.evaluate("""() => { const r = document.querySelector('table.nav tr.prof'), p = r.previousElementSibling; return { prev: p.className, bold: Array.from(r.querySelectorAll('b')).map(b => b.textContent), bg: getComputedStyle(r.cells[1]).backgroundColor }; }""")
    assert d == {'prev': 'leg', 'bold': ['100 m', '600 m'], 'bg': 'rgba(192, 137, 42, 0.16)'}
    assert pg.errs == []
    pg.context.close()


@needs_pw
def test_a_corridor_that_leaves_the_relief_is_marked_with_at_least(browser):
    pg, fr = open_rp(browser)
    tick(fr, pg)
    # à 0,05° du bord ouest du relief (35,15° E) : le couloir de 5 NM en sort
    route(fr, [{'name': 'A', 'lat': 33.60, 'lon': 35.20, 'alt': 30, 'altRef': 'AGL'}, {'name': 'B', 'lat': 33.80, 'lon': 35.20, 'alt': 30, 'altRef': 'AGL'}])
    wait_prof(fr)
    pg.wait_for_timeout(400)
    g = legs(fr)[0]
    assert g['unk'] is True and g['safe'] == pytest.approx(CREST_M, abs=0.01)
    assert prof_rows(fr) == ['▲ Point le plus haut 100 m · sécurité ≥ 600 m'] or prof_rows(fr) == ['▲ Point le plus haut 300 m · sécurité ≥ 600 m']
    fr.evaluate("unChoose('ft')")
    pg.wait_for_timeout(400)
    assert prof_rows(fr)[0].endswith('sécurité ≥ 2' + NBSP + '000 ft')
    # tout le couloir dans le relief : pas de « ≥ »
    route(fr, [pt('A', 100 / 256, .3), pt('B', 100 / 256, .7)])
    wait_prof(fr)
    pg.wait_for_timeout(400)
    assert '≥' not in prof_rows(fr)[0]
    assert pg.errs == []
    pg.context.close()


@needs_pw
def test_the_ground_is_read_without_the_relief_box_and_a_missing_tile_leaves_a_gap(browser):
    pg, fr = open_rp(browser)
    assert fr.evaluate("DISP.relief") is False and fr.evaluate("RE.layer") is None
    tick(fr, pg)
    route(fr, [pt('A', 100 / 256, .5), pt('B', 200 / 256, .5)])
    wait_prof(fr)
    assert fr.evaluate("RE.layer") is None and fr.evaluate("__RP.prof.data.flat.g.every(v => v === v)") is True
    # la tuile d'altitude d'à côté manque : le sol y est inconnu (un trou)
    pg.context.close()
    pg, fr = open_rp(browser)

    def missing(rt):
        if '/elevation/' in rt.request.url and rt.request.url.endswith('/%d/%d.png' % (TX + 1, TY)):
            return rt.fulfill(status=404, headers={'Access-Control-Allow-Origin': '*'}, body='')
        return rt.fallback()
    pg.route('**/elevation/**', missing)
    tick(fr, pg)
    route(fr, [pt('A', 200 / 256, .5), pt('B', 100 / 256, .5, tx=TX + 1)])
    wait_prof(fr)
    pg.wait_for_timeout(300)
    r = fr.evaluate("""() => { const g = __RP.prof.data.flat.g; let nan = 0, ok = 0; for (let i = 0; i < g.length; i++) { if (g[i] !== g[i]) nan++; else ok++; } return { nan: nan, ok: ok, total: g.length }; }""")
    assert r['nan'] > 0 and r['ok'] > 0
    # un trou au graphique : plus d'une suite de sol dans le bord
    assert fr.evaluate("document.querySelector('.prof-edge').getAttribute('d').split('M').length") >= 2
    # la valeur de la sécurité est précédée de « ≥ » : un pixel du couloir est inconnu
    assert prof_rows(fr)[0].count('≥') == 1
    assert pg.errs == []
    pg.context.close()


# ---------- les menaces sur le profil ----------
def east_route(alt=30, ref='AGL'):
    return [pt('A', 60 / 256, .5, alt, ref), pt('B', 250 / 256, .5, alt, ref)]


@needs_pw
def test_the_zone_starts_at_the_larger_of_the_ground_and_the_visibility_height_and_ends_at_the_ceiling(browser):
    pg, fr = open_rp(browser)
    tick(fr, pg)
    route(fr, east_route(), [sym(0, 'sa-8', name='S8')])
    wait_prof(fr)
    pg.wait_for_timeout(800)
    z = fr.evaluate("__RP.prof.zones.map(z => ({ id: z.id, name: z.name, top: z.top, n: z.runs.length }))")
    assert len(z) == 1 and z[0]['id'] == 'sa-8' and z[0]['name'] == 'S8' and z[0]['n'] >= 1
    chk = fr.evaluate("""() => {
      const P = __RP.prof, F = P.data.flat, a = thrRouteActs()[0], gr = THR.grids.get(a.key), out = [], want = [170, 190, 210];
      const nn = 256 * Math.pow(2, gr.z);
      for (const col of want) {
        // l'échantillon le plus proche de la colonne col de la tuile de la menace
        let best = -1, bd = 1e9;
        for (let k = 0; k < F.N; k++) { const px = (F.lon[k] + 180) / 360 * nn - 1229 * 256; if (Math.abs(px - col) < bd) { bd = Math.abs(px - col); best = k; } }
        const k = best, gx = Math.floor((F.lon[k] + 180) / 360 * nn) - gr.px0, gy = Math.floor(thrMercV(F.lat[k]) * nn) - gr.py0, idx = gy * gr.side + gx;
        const run = P.zones[0].runs.find(r => r.s.some(q => q.k === k)), q = run && run.s.find(q => q.k === k);
        out.push({ col: col, k: k, ground: F.g[k], gridG: gr.g[idx], hv: gr.hv[idx], lo: q ? q.lo : null, top: P.zones[0].top, gs: gr.gs, ceil: gr.ceil });
      }
      return out; }""")
    for c in chk:
        assert c['lo'] is not None, c
        assert abs(c['lo'] - max(c['ground'], c['gridG'] + c['hv'])) <= 1, c                         # le bas : max(sol, g + hv), à 1 m près
        assert abs(c['top'] - (c['gs'] + c['ceil'])) <= 1, c                                          # le haut : gs + plafond
        assert c['lo'] > c['ground'] + 5, c                                                           # derrière la crête : au-dessus du sol
    # une seule teinte : un groupe à l'opacité 0,55
    g = fr.evaluate("""() => { const p = document.querySelector('path.prof-zone'), grp = p.parentNode; return [grp.getAttribute('opacity'), grp.getAttribute('fill'), p.getAttribute('data-th'), document.querySelectorAll('path.prof-zone').length]; }""")
    assert g[0] == '0.55' and g[1] == '#c8102e' and g[2] == 'sa-8'
    assert fr.evaluate("document.querySelector('.prof-zname').textContent") == 'S8'
    assert 'vu et à portée de tir des menaces' in fr.evaluate("document.querySelector('.prof-leg').textContent")
    # « Menaces » décochée : ni zone, ni barre, la légende de base
    tick(fr, pg, 'threats', False)
    pg.wait_for_timeout(500)
    assert fr.evaluate("document.querySelectorAll('path.prof-zone, rect.prof-seen').length") == 0
    assert fr.evaluate("document.querySelector('.prof-leg').textContent") == '━ point le plus haut · ╍╍ sécurité'
    assert pg.errs == []
    pg.context.close()


@needs_pw
def test_the_route_seen_bar_is_the_set_the_map_halo_is_drawn_from(browser):
    pg, fr = open_rp(browser)
    tick(fr, pg)
    fr.evaluate("window.__runs = []; const o = thrRouteSet; thrRouteSet = function (s, r) { window.__runs.push(r); return o.apply(this, arguments); }; 0")
    route(fr, east_route(), [sym(0, 'sa-8', name='S8')])
    wait_prof(fr)
    pg.wait_for_timeout(1200)
    runs = fr.evaluate("window.__runs[window.__runs.length - 1]")
    bars = fr.evaluate("Array.from(document.querySelectorAll('rect.prof-seen')).map(e => [parseFloat(e.getAttribute('data-d0')), parseFloat(e.getAttribute('data-d1')), e.getAttribute('height'), e.getAttribute('y')])")
    assert runs and len(bars) == len(runs)
    # la distance, le long de la route, du premier et du dernier point de chaque suite de thrRouteSet
    along = fr.evaluate("""(runs) => {
      const pts = S.points, out = [];
      const at = p => { let cum = 0; for (let i = 1; i < pts.length; i++) { const a = pts[i - 1], b = pts[i], ab = legCalc(a, b).km * 1000, ap = legCalc(a, p).km * 1000, pb = legCalc(p, b).km * 1000;
        if (Math.abs(ap + pb - ab) < 1) return cum + ap; cum += ab; } return null; };
      runs.forEach(r => out.push([at(r[0]) / 1000, at(r[r.length - 1]) / 1000]));
      return out; }""", runs)
    for b, a in zip(bars, along):
        assert abs(b[0] - a[0]) < 0.002 and abs(b[1] - a[1]) < 0.002, (b, a)
    assert all(b[2] == '5' for b in bars)
    axis = fr.evaluate("__RP.prof.view.axisY")
    assert all(float(b[3]) == axis + 1 for b in bars)                                                # sous l'axe horizontal
    # la zone et la barre disparaissent avec la menace
    fr.evaluate("CF_LAYERS.length = 0; renderAll();")
    pg.wait_for_timeout(1000)
    assert fr.evaluate("document.querySelectorAll('path.prof-zone, rect.prof-seen').length") == 0
    assert pg.errs == []
    pg.context.close()


@needs_pw
def test_the_navigation_rows_come_before_the_threat_row_and_the_table_is_the_base_when_unticked(browser):
    pg, fr = open_rp(browser)
    route(fr, east_route(), [sym(0, 'sa-8', name='S8')])
    pg.wait_for_timeout(800)
    base = fr.evaluate("document.getElementById('nav-body').innerHTML")
    assert 'class="thr"' in base and 'class="prof"' not in base
    tick(fr, pg)
    wait_prof(fr)
    pg.wait_for_timeout(500)
    order = fr.evaluate("Array.from(document.querySelectorAll('#nav-body tr')).map(e => e.className)")
    assert order == ['', 'leg', 'prof', 'thr', '']
    assert fr.evaluate("document.querySelector('#nav-body tr.prof').nextElementSibling.className") == 'thr'
    thr_text = fr.evaluate("document.querySelector('#nav-body tr.thr').textContent")
    tick(fr, pg, on=False)
    pg.wait_for_timeout(500)
    assert fr.evaluate("document.getElementById('nav-body').innerHTML") == base                           # case décochée : le tableau de la base
    assert fr.evaluate("document.querySelector('#nav-body tr.thr').textContent") == thr_text               # les lignes « Vu par … » ne changent pas
    assert pg.errs == []
    pg.context.close()


@needs_pw
def test_unticked_the_map_is_the_base(browser):
    pg, fr = open_rp(browser)
    route(fr, east_route())
    pg.wait_for_timeout(500)
    a = fr.evaluate("""() => { const q = s => { const b = document.querySelector(s).getBoundingClientRect(); return [b.x, b.y, b.width, b.height]; };
      return { map: q('#map'), wrap: q('.mapwrap'), nav: q('#nav-body'), size: [__RP.map.getSize().x, __RP.map.getSize().y], prof: document.getElementById('rp-prof') }; }""")
    assert a['prof'] is None and a['map'][3] == a['wrap'][3] and a['size'] == [a['map'][2], a['map'][3]]
    assert pg.errs == []
    pg.context.close()


# ---------- le curseur ----------
@needs_pw
def test_the_cursor_bubble_stays_in_the_frame_and_the_map_gets_a_yellow_dot(browser):
    pg, fr = open_rp(browser)
    tick(fr, pg)
    route(fr, east_route(), [sym(0, 'sa-8', name='S8')])
    wait_prof(fr)
    pg.wait_for_timeout(1000)
    sv = fr.evaluate("(() => { const b = document.querySelector('.prof-svg').getBoundingClientRect(); return [b.x, b.y, b.width, b.height]; })()")
    seen_txt = None
    for fx in (0.0, 0.02, 0.35, 0.5, 0.98, 1.0):
        pg.mouse.move(sv[0] + fx * (sv[2] - 1) + (0.5 if fx == 0 else 0), sv[1] + 90)
        pg.wait_for_timeout(250)
        r = fr.evaluate("""() => { const b = document.querySelector('.prof-bub').getBoundingClientRect(), g = document.querySelector('.prof-g').getBoundingClientRect();
          return { hidden: document.querySelector('.prof-bub').hidden, l: b.left - g.left, r: g.right - b.right, txt: document.querySelector('.prof-bub').textContent,
                   line: !!document.querySelector('#prof-cur .prof-cl'), dot: !!document.querySelector('#prof-cur .prof-cd'), mark: document.querySelectorAll('.rp-prof-dot').length }; }""")
        assert r['hidden'] is False and r['l'] >= -0.01 and r['r'] >= -0.01 and r['line'] and r['mark'] == 1, (fx, r)
        assert r['txt'].startswith(('0,0 km', '0,1 km', '0,2 km', '2', '1', '3', '4', '5', '6', '7', '8', '9')) and ' · sol ' in r['txt'], r
        if 'vu dès' in r['txt']:
            seen_txt = r['txt']
    assert seen_txt is not None and seen_txt.endswith('(S8)'), seen_txt
    # le rond jaune est à l'échantillon de la route
    p = fr.evaluate("""() => { const P = __RP.prof, k = P.cur, F = P.data.flat; const m = P.mark.getLatLng(); return [m.lat - F.lat[k], m.lng - F.lon[k]]; }""")
    assert p == [0, 0]
    pg.mouse.move(5, 5)
    pg.wait_for_timeout(250)
    assert fr.evaluate("document.querySelector('.prof-bub').hidden") is True and fr.evaluate("document.querySelectorAll('.rp-prof-dot').length") == 0
    assert pg.errs == []
    pg.context.close()


# ---------- les tailles ----------
@needs_pw
@pytest.mark.parametrize('w,h,lang', [(412, 915, 'fr'), (345, 590, 'en')])
def test_the_strip_on_a_phone_fits_the_touch_button_and_the_bubble(browser, w, h, lang):
    pg, fr = open_rp(browser, w, h, lang)
    route(fr, [pt('DÉPART', 60 / 256, .5), pt('COL', 150 / 256, .5, 1900, 'MSL'), pt('RETOUR', 250 / 256, .5)])
    before = rects(fr)
    tick(fr, pg)
    wait_prof(fr)
    pg.wait_for_timeout(500)
    on = rects(fr)
    assert on['prof'][3] == 26 + 130 and on['prof'][2] == on['map'][2]
    assert abs(on['map'][3] - (before['map'][3] - 156)) < 0.1 and on['map'][3] > 0
    assert on['prof'][1] + on['prof'][3] == on['wrap'][1] + on['wrap'][3]                                  # au-dessus de la poignée, dans la carte
    assert on['btn'][2] == 44 and on['btn'][3] == 44
    sw = fr.evaluate("(() => { const e = document.getElementById('rp-prof'); return [e.scrollWidth, e.clientWidth, document.querySelector('.prof-svg').scrollWidth]; })()")
    assert sw[0] == sw[1]
    assert fr.evaluate("document.querySelector('.prof-leg').hidden") is True                                # pas de légende au téléphone
    # les noms sont coupés à 4 lettres, sauf le premier et le dernier
    assert fr.evaluate("Array.from(document.querySelectorAll('.prof-pn')).map(e => e.textContent)") == ['0 DÉPART', '1 COL', '2 RETOUR']
    sv = fr.evaluate("(() => { const b = document.querySelector('.prof-svg').getBoundingClientRect(); return [b.x, b.y, b.width, b.height]; })()")
    for fx in (0.0, 1.0):
        pg.touchscreen.tap(sv[0] + fx * (sv[2] - 1) + (1 if fx == 0 else 0), sv[1] + 80)
        pg.wait_for_timeout(300)
        r = fr.evaluate("""() => { const b = document.querySelector('.prof-bub').getBoundingClientRect(), g = document.querySelector('.prof-g').getBoundingClientRect(); return { hidden: document.querySelector('.prof-bub').hidden, l: b.left - g.left, r: g.right - b.right }; }""")
        assert r['hidden'] is False and r['l'] >= -0.01 and r['r'] >= -0.01, (fx, r)
    # le toucher reste jusqu'au toucher suivant hors du graphique
    pg.touchscreen.tap(w / 2, 100)
    pg.wait_for_timeout(300)
    assert fr.evaluate("document.querySelector('.prof-bub').hidden") is True
    # repli au doigt : 26 px restent
    fr.evaluate("document.querySelector('#rp-prof button').click()")
    pg.wait_for_timeout(300)
    assert rects(fr)['prof'][3] == 26 and abs(rects(fr)['map'][3] - (before['map'][3] - 26)) < 0.1
    assert pg.errs == []
    pg.context.close()


# ---------- le Field Manual et les textes ----------
def test_the_field_manual_and_the_texts_say_it():
    fm = (ROOT / 'dist' / 'dcs_field_manual.html').read_text(encoding='utf-8')
    rp = fm[fm.index('<section id="page-rp"'):fm.index('<!-- /page-rp -->')].replace('\u202f', ' ').replace('\xa0', ' ')
    assert 'Profil du sol ouvre, sous la carte, le profil de la route.' in rp and 'Ground profile opens the route’s profile under the map.' in rp
    assert rp.index('Les systèmes de défense aérienne') < rp.index('Cochez <strong>Profil du sol</strong>') < rp.index('La fiche d’un aérodrome')
    assert 'Tick <strong>Ground profile</strong> in <strong>Display ▾</strong>' in rp and 'on a phone as on a computer. It shows the <strong>ground under the chosen route</strong>' in rp
    assert 'arrondi au-dessus à 50 m ou à 100 ft (tirets verts) ; « ≥ » la précède quand une part de ce couloir sort du relief.' in rp
    assert 'Le profil est un réglage d’écran, hors du fichier de travail.' in rp and 'The profile is a screen setting, outside the work file.' in rp
    rpd = (ROOT / 'dist' / 'dcs_route_planner.html').read_text(encoding='utf-8')
    for k in ('dsp.profile', 'dsp.profile.tip', 'dsp.profile.off', 'prof.title', 'prof.empty', 'prof.ground', 'prof.seen', 'prof.leg', 'prof.fold', 'prof.unfold', 'prof.legend', 'prof.legend.base'):
        assert rpd.count("    '%s': '" % k) == 2, k
    assert "'prof.legend': '▇ vu et à portée de tir des menaces (jusqu\\'au plafond) · ▬ route vue (sous l\\'axe) · ━ point le plus haut · ╍╍ sécurité'," in rpd
    assert "'prof.legend': '▇ seen and within firing range of threats (up to ceiling) · ▬ route seen (below the axis) · ━ highest point · ╍╍ safety'," in rpd
    assert "'prof.leg': '▲ Point le plus haut **{h}** · sécurité **{s}**'," in rpd and "'prof.leg': '▲ Highest point **{h}** · safety **{s}**'," in rpd
    assert "{ g: '', k: 'profile', l: 'dsp.profile' }," in rpd and rpd.index("k: 'threats'") < rpd.index("k: 'profile'") < rpd.index("k: 'routes'")
