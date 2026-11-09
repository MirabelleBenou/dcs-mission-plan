#!/usr/bin/env python3
"""Bloc « THÉÂTRE D'UNE ROUTE » : routeTheatre, routesOfTheatre — une seule source pour le Route Planner, le Flight Configurator et le Datacard Generator.

Le théâtre d'une route est celui où elle a été créée : il se pose une fois, à sa naissance (route neuve : le théâtre courant ; route ouverte d'un fichier, d'un jeu de routes, de l'exemple, reprise
d'un groupe : le théâtre sous lequel elle entre), et ne change plus. Il n'est jamais déduit de la position de ses points. Ce qui est visible d'un jeu de routes (route_set_v1) ne dépend que de deux
données stockées : le théâtre commun C (mp_theatre_v1) et le champ theatre de chaque route.
Une route d'avant le lot (sans theatre) prend le théâtre de référence ref : celui de route_state_v1 s'il est valide (le théâtre du Route Planner quand ces routes ont été enregistrées), sinon celui de
mp_theatre_v1, sinon Caucasus ; chaque module calcule ref pareil. Le Route Planner écrit ce théâtre dans route_set_v1 ; les deux autres modules ne l'écrivent jamais, ils lisent la route comme le Route
Planner l'écrira.
Les trois builds insèrent ce texte tel quel : le bloc est identique à l'octet dans les trois fichiers de dist/.

Usage (par les builds) : from route_theatre_block import build_block ; texte = build_block()
"""

BLOCK_BEGIN = '/* ===== THÉÂTRE D\'UNE ROUTE (routeTheatre, routesOfTheatre) ===== */'
BLOCK_END = '/* ===== FIN DU THÉÂTRE D\'UNE ROUTE ===== */'

_JS = r"""
const RT_THEATRES = ['Caucasus', 'GermanyCW', 'Syria', 'PersianGulf', 'Normandy', 'TheChannel', 'Nevada', 'MarianaIslands', 'MarianaIslandsWWII', 'Kola', 'SinaiMap', 'Iraq', 'Afghanistan', 'Falklands'];
function rtThOk(id) { return typeof id === 'string' && RT_THEATRES.indexOf(id) !== -1; }

/* Le théâtre d'une route : son champ theatre s'il est un des quatorze, sinon ref (le théâtre de référence des routes d'avant le lot) */
function routeTheatre(route, ref) {
  return route && rtThOk(route.theatre) ? route.theatre : ref;
}

/* Les routes du théâtre C (l'ordre est gardé) */
function routesOfTheatre(routes, C) {
  return routes.filter(r => routeTheatre(r, C) === C);
}
"""


def build_block():
    return BLOCK_BEGIN + '\n' + _JS.strip('\n') + '\n' + BLOCK_END + '\n'
