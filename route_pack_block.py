#!/usr/bin/env python3
"""Bloc « POINTS DE PAQUET (route → mission DCS) » : packPoint, le point <k> d'un paquet de vol, une seule source pour le Route Planner et le Flight Configurator.

Le texte JavaScript est celui de packPoint du Route Planner (build_route_planner.py), au caractère près, à deux changements près : la vitesse sol par défaut
(S.groundSpeed au Route Planner) est un quatrième paramètre, gsDefault (le nom « gs » est pris par la variable locale de la fonction), et validCoord est
remplacé par packValidCoord, définie dans le bloc, de corps identique. Il exige llToDcs dans la page (bloc des projections).
Le Route Planner appelle packPoint(p, k, th, S.groundSpeed) ; le Flight Configurator, packPoint(p, k, théâtre, route_state_v1.groundSpeed) :
un paquet exporté par l'un est donc identique à l'octet, pour la même route, à celui que l'autre écrirait.

Usage (par les builds) : from route_pack_block import build_block ; texte = build_block()
"""

BLOCK_BEGIN = '/* ===== POINTS DE PAQUET (route → mission DCS) ===== */'
BLOCK_END = '/* ===== FIN DES POINTS DE PAQUET ===== */'

_JS = r"""
function packValidCoord(lat, lon) {
  return typeof lat === 'number' && typeof lon === 'number' && isFinite(lat) && isFinite(lon) && Math.abs(lat) <= 90 && Math.abs(lon) <= 180;
}

/* Le point <k> d'un paquet : avec sa source de mission, une copie de la table brute où seul ce qui a changé depuis l'import est réécrit ; sans, un point neuf */
function packPoint(p, i, th, gsDefault) {
  const xy = llToDcs(th, p.lat, p.lon);
  const d = p.dcs;
  if (d && d.raw && typeof d.raw === 'object' && !Array.isArray(d.raw) && d.orig && typeof d.orig === 'object') {
    const o = JSON.parse(JSON.stringify(d.raw)), og = d.orig;
    let moved = true;
    if (packValidCoord(og.lat, og.lon)) {
      const was = llToDcs(th, og.lat, og.lon);
      moved = Math.hypot(xy.x - was.x, xy.y - was.y) > 1;
    }
    if (moved) {
      o.x = xy.x; o.y = xy.y;
      o.type = 'Turning Point'; o.action = 'Turning Point';
      delete o.airdromeId; delete o.helipadId; delete o.linkUnit;
    }
    if (p.alt !== og.alt || p.altRef !== og.altRef) { o.alt = p.alt; o.alt_type = p.altRef === 'MSL' ? 'BARO' : 'RADIO'; }
    if (i > 0 && p.gs !== og.gs) o.speed = ((typeof p.gs === 'number' && p.gs > 0) ? p.gs : gsDefault) / 3.6;
    if (p.name !== og.name) o.name = p.name;
    return o;
  }
  const gs = (i > 0 && typeof p.gs === 'number' && p.gs > 0) ? p.gs : gsDefault;
  return {
    type: 'Turning Point', action: 'Turning Point', x: xy.x, y: xy.y, alt: p.alt, alt_type: p.altRef === 'MSL' ? 'BARO' : 'RADIO', speed: gs / 3.6, name: p.name,
    ETA: 0, ETA_locked: false, speed_locked: true, formation_template: '', task: { id: 'ComboTask', params: { tasks: {} } }
  };
}
"""


def build_block():
    """Le texte du bloc, délimité par ses deux commentaires, terminé par un saut de ligne."""
    return BLOCK_BEGIN + _JS + BLOCK_END + '\n'


if __name__ == '__main__':
    txt = build_block()
    print(f"[OK] bloc des points de paquet : {len(txt)} caractères")
