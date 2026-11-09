#!/usr/bin/env python3
"""Bloc « THÉÂTRE D'UNE ROUTE » : theatreOfPoint, routeTheatre, routesOfTheatre — une seule source pour le Route Planner, le Flight Configurator et le Datacard Generator.

Ce qui est visible d'un jeu de routes (route_set_v1) ne dépend que de deux données stockées : le théâtre commun C (mp_theatre_v1) et le champ theatre de chaque route. Une route sans theatre
(stockage d'avant le lot) reçoit celui de son premier point : le théâtre dont le centre est le plus proche, le théâtre de référence gardé s'il est à moins de 150 km du plus proche ; sans point,
ou à plus de 1 500 km de tout centre, le théâtre de référence. Le Route Planner écrit ce théâtre dans route_set_v1 ; les deux autres modules ne l'écrivent jamais, ils lisent la route comme
le Route Planner l'écrira.
Le bloc porte sa propre table des centres (les quatorze théâtres, dans l'ordre du Route Planner) : il ne dépend d'aucune autre table de la page.
Les trois builds insèrent ce texte tel quel : le bloc est identique à l'octet dans les trois fichiers de dist/.

Usage (par les builds) : from route_theatre_block import build_block ; texte = build_block()
"""

BLOCK_BEGIN = '/* ===== THÉÂTRE D\'UNE ROUTE (routeTheatre, routesOfTheatre) ===== */'
BLOCK_END = '/* ===== FIN DU THÉÂTRE D\'UNE ROUTE ===== */'

_JS = r"""
const RT_CENTRES = {
  Caucasus: [43.0, 41.6], GermanyCW: [51.2, 10.4], Syria: [34.8, 35.8], PersianGulf: [26.3, 55.6], Normandy: [49.6, 0.0], TheChannel: [50.9, 1.6], Nevada: [36.6, -115.5],
  MarianaIslands: [14.8, 145.4], MarianaIslandsWWII: [14.8, 145.4], Kola: [68.3, 28.5], SinaiMap: [30.4, 33.2], Iraq: [34.4, 42.6], Afghanistan: [33.4, 66.3], Falklands: [-51.7, -59.0]
};
function rtThOk(id) { return typeof id === 'string' && Object.prototype.hasOwnProperty.call(RT_CENTRES, id); }

/* Le théâtre d'un point (route d'un stockage sans theatre) : voir l'en-tête du bloc */
function theatreOfPoint(p, cur) {
  if (!p || typeof p.lat !== 'number' || typeof p.lon !== 'number') return cur;
  const R = 6371, rad = Math.PI / 180;
  const d = c => { const a = Math.sin((c[0] - p.lat) * rad / 2) ** 2 + Math.cos(p.lat * rad) * Math.cos(c[0] * rad) * Math.sin((c[1] - p.lon) * rad / 2) ** 2; return 2 * R * Math.asin(Math.sqrt(a)); };
  let best = null;
  Object.keys(RT_CENTRES).forEach(id => { const k = d(RT_CENTRES[id]); if (!best || k < best.k) best = { id: id, k: k }; });
  const dc = d(RT_CENTRES[rtThOk(cur) ? cur : 'Caucasus']);
  if (best.k > 1500) return cur;
  return dc <= best.k + 150 ? cur : best.id;
}

/* Le théâtre d'une route : son champ theatre s'il est un des quatorze, sinon celui de son premier point (ref : le théâtre de référence) */
function routeTheatre(route, ref) {
  if (route && rtThOk(route.theatre)) return route.theatre;
  return theatreOfPoint(route && Array.isArray(route.points) ? route.points[0] : null, ref);
}

/* Les routes du théâtre C (l'ordre est gardé) */
function routesOfTheatre(routes, C) {
  return routes.filter(r => routeTheatre(r, C) === C);
}
"""


def build_block():
    return BLOCK_BEGIN + '\n' + _JS.strip('\n') + '\n' + BLOCK_END + '\n'
