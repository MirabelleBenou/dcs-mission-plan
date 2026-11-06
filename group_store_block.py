#!/usr/bin/env python3
"""Bloc « GROUPES PARTAGÉS (flight_set_v1) » : la fiche des groupes du Flight Leader, une seule source pour le Route Planner et le Flight Configurator.

Une clé de stockage, flight_set_v1, que les deux modules lisent et écrivent : { format: 'dcs-flight-set-v1', theatre, flights: [ groupe, … ] }.
Un groupe est le vol du Flight Configurator tel qu'il est dans son état (fcId, name, coalition, route, routeLink, units, …) ; toute clé inconnue d'un groupe
ou d'une unité est gardée telle quelle. Un groupe peut n'avoir aucune unité (units: []).

Une seule façon d'écrire : relire la clé, changer le seul groupe touché, écrire (gsPutFlight, gsRemoveFlight, gsSetTheatre). Seule gsReplaceAll écrit toute la liste.
Rien ici ne touche au DOM, à t() ni au réseau ; tout accès au stockage est en try/catch : sans stockage, l'écran marche.

gsMigrate(packFn) : au premier chargement de l'un des deux modules, la fiche est bâtie des groupes de fc_state_v1 puis des routes de route_set_v1 qui portent un lien
par nom ; packFn(route, théâtre) rend les points de la route au format du paquet (ou null : la route est laissée de côté).

Usage (par les builds) : from group_store_block import build_block ; texte = build_block()
"""

BLOCK_BEGIN = '/* ===== GROUPES PARTAGÉS (flight_set_v1) ===== */'
BLOCK_END = '/* ===== FIN DES GROUPES PARTAGÉS ===== */'

_JS = r"""
const KEY_FLIGHT_SET = 'flight_set_v1', FLIGHT_SET_FORMAT = 'dcs-flight-set-v1';
const GS_KEY_FC = 'fc_state_v1', GS_KEY_ROUTES = 'route_set_v1', GS_KEY_ROUTE = 'route_state_v1';

function gsIsObj(v) { return !!v && typeof v === 'object' && !Array.isArray(v); }
function gsLsGet(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }
function gsLsSet(k, v) { try { localStorage.setItem(k, v); return true; } catch (e) { return false; } }
function gsJson(k) { try { const r = gsLsGet(k); return r === null ? null : JSON.parse(r); } catch (e) { return null; } }
/* Le JSON d'une valeur à clés triées : deux groupes égaux se comparent par leur texte, quel que soit l'ordre de leurs clés */
function gsStable(v) {
  return JSON.stringify(v, (k, x) => {
    if (!gsIsObj(x)) return x;
    const o = {};
    Object.keys(x).sort().forEach(n => { o[n] = x[n]; });
    return o;
  });
}
/* L'identifiant d'un groupe neuf : « f » et trois nombres aléatoires en base 36 */
function gsNewId() {
  try {
    const a = new Uint32Array(3);
    crypto.getRandomValues(a);
    return 'f' + Array.prototype.map.call(a, x => x.toString(36)).join('');
  } catch (e) { return 'f' + Math.random().toString(36).slice(2, 10) + Date.now().toString(36); }
}
/* Un camp qui n'est ni rouge ni bleu est « aucun » ('') ; un nom se compare rogné des deux côtés, la casse compte */
function gsSide(c) { return c === 'red' || c === 'blue' ? c : ''; }
function gsNameKey(s) { return typeof s === 'string' ? s.trim() : ''; }

/* La fiche lue et vérifiée : { theatre, flights } ; clé absente ou illisible : null. Un groupe sans fcId, ou dont le fcId est déjà pris, est écarté. */
function gsRead() {
  const o = gsJson(KEY_FLIGHT_SET);
  if (!gsIsObj(o) || o.format !== FLIGHT_SET_FORMAT || !Array.isArray(o.flights)) return null;
  const seen = new Set(), flights = [];
  o.flights.forEach(f => {
    if (!gsIsObj(f) || typeof f.fcId !== 'string' || f.fcId === '' || seen.has(f.fcId)) return;
    seen.add(f.fcId);
    flights.push(f);
  });
  return { theatre: typeof o.theatre === 'string' ? o.theatre : '', flights: flights };
}
function gsWrite(theatre, flights) {
  return gsLsSet(KEY_FLIGHT_SET, JSON.stringify({ format: FLIGHT_SET_FORMAT, theatre: typeof theatre === 'string' ? theatre : '', flights: flights }));
}
/* Remplace le groupe de même fcId (à sa place) ou ajoute f à la fin ; relit d'abord. Vrai si la fiche porte f à la fin (écrite, ou déjà identique). */
function gsPutFlight(f) {
  if (!gsIsObj(f) || typeof f.fcId !== 'string' || f.fcId === '') return false;
  const g = gsRead() || { theatre: '', flights: [] };
  const i = g.flights.findIndex(x => x.fcId === f.fcId);
  if (i >= 0) {
    if (gsStable(g.flights[i]) === gsStable(f)) return true;
    g.flights[i] = f;
  } else g.flights.push(f);
  return gsWrite(g.theatre, g.flights);
}
function gsRemoveFlight(fcId) {
  const g = gsRead();
  if (!g) return true;
  const n = g.flights.filter(x => x.fcId !== fcId);
  if (n.length === g.flights.length) return true;
  return gsWrite(g.theatre, n);
}
function gsSetTheatre(th) {
  const g = gsRead();
  if (g && g.theatre === th) return true;
  return gsWrite(th, g ? g.flights : []);
}
/* Écrit tout : l'ouverture d'un fichier de travail du Flight Configurator */
function gsReplaceAll(theatre, flights) {
  return gsWrite(theatre, flights.filter(gsIsObj));
}

/* La migration : la fiche n'existe pas encore (ou ne se lit pas).
   1. les groupes de fc_state_v1 (avec leur fcId) et son théâtre ; à défaut le théâtre de route_state_v1 ; à défaut '' ;
   2. dans l'ordre de route_set_v1, chaque route qui porte un lien par nom (flight) : les groupes de même nom rogné (casse exacte) et même camp :
      un seul, sans route : il la prend ; un seul qui a déjà une route : rien ; aucun : un groupe neuf sans unité ; plusieurs : rien.
      Pas de route retenue sans théâtre commun : le théâtre de la fiche et celui de route_state_v1 doivent être le même ;
   3. écrit la fiche (même vide), puis réécrit fc_state_v1 en { v: 2, sel, mine }. route_set_v1 n'est pas touché.
   Rend vrai si la fiche a été écrite. */
function gsMigrate(packFn) {
  if (gsRead() !== null) return false;
  const fc = gsJson(GS_KEY_FC), st = gsIsObj(fc) && gsIsObj(fc.state) ? fc.state : null;
  const rs = gsJson(GS_KEY_ROUTE), rsTheatre = gsIsObj(rs) && typeof rs.theatre === 'string' ? rs.theatre : '';
  const flights = [], seen = new Set();
  if (st && Array.isArray(st.flights)) st.flights.forEach(f => {
    if (!gsIsObj(f)) return;
    if (typeof f.fcId !== 'string' || f.fcId === '') f.fcId = gsNewId();
    if (seen.has(f.fcId)) return;
    seen.add(f.fcId);
    flights.push(f);
  });
  const theatre = st && typeof st.theatre === 'string' && st.theatre !== '' ? st.theatre : rsTheatre;
  const set = gsJson(GS_KEY_ROUTES);
  if (theatre !== '' && theatre === rsTheatre && gsIsObj(set) && Array.isArray(set.routes) && typeof packFn === 'function') {
    set.routes.forEach(r => {
      if (!gsIsObj(r) || !gsIsObj(r.flight) || typeof r.rid !== 'string' || !/^[a-z0-9]{6,32}$/.test(r.rid)) return;
      const name = gsNameKey(r.flight.groupName), side = gsSide(r.flight.coalition);
      if (name === '') return;
      const hits = flights.filter(f => gsNameKey(f.name) === name && gsSide(f.coalition) === side);
      if (hits.length > 1 || (hits.length === 1 && hits[0].route)) return;
      let pts = null;
      try { pts = packFn(r, theatre); } catch (e) { pts = null; }
      if (!gsIsObj(pts)) return;
      const link = { rid: r.rid, name: typeof r.name === 'string' ? r.name : '' };
      if (hits.length === 1) { hits[0].route = { points: pts }; hits[0].routeLink = link; }
      else flights.push({ fcId: gsNewId(), name: r.flight.groupName, coalition: side, route: { points: pts }, routeLink: link, units: [] });
    });
  }
  if (!gsWrite(theatre, flights)) return false;
  if (gsIsObj(fc)) {
    const sel = st && gsIsObj(st.sel) ? st.sel : (gsIsObj(fc.sel) ? fc.sel : { f: 0, u: 0 });
    gsLsSet(GS_KEY_FC, JSON.stringify({ v: 2, sel: sel, mine: gsIsObj(fc.mine) ? fc.mine : {} }));
  }
  return true;
}
"""


def build_block():
    """Le texte du bloc, délimité par ses deux commentaires, terminé par un saut de ligne."""
    return BLOCK_BEGIN + _JS + BLOCK_END + '\n'


if __name__ == '__main__':
    txt = build_block()
    print(f"[OK] bloc des groupes partagés : {len(txt)} caractères")
