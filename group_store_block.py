#!/usr/bin/env python3
"""Bloc « GROUPES PARTAGÉS (flight_set_v1) » : la fiche des groupes du Flight Leader, une seule source pour le Route Planner et le Flight Configurator.

Une clé de stockage, flight_set_v1, que les deux modules lisent et écrivent : { format: 'dcs-flight-set-v1', theatre, flights: [ groupe, … ] }.
Un groupe est le vol du Flight Configurator tel qu'il est dans son état (fcId, name, coalition, route, routeLink, units, …) ; toute clé inconnue d'un groupe
ou d'une unité est gardée telle quelle. Un groupe peut n'avoir aucune unité (units: []).

Une seule façon d'écrire : relire la clé, changer le seul groupe touché, écrire (gsPutFlight, gsRemoveFlight, gsSetTheatre). Seule gsReplaceAll écrit toute la liste.
Retirer un groupe (gsRemoveFlight) retire aussi sa datacard de datacard_state_v1 (gsDropCard) : un groupe supprimé l'est partout.
gsClearAll() : le « Tout effacer » des trois outils du Flight Leader (Flight Configurator, Route Planner, Datacard Generator), une seule fois pour les trois (voir plus bas).
Un échec d'écriture (stockage plein) appelle une fois par série d'échecs gsOnSaveFail() si le module la définit (son toast).
Une route porte, facultative, la date de la mission d'où elle vient (route.missionDate, AAAA-MM-JJ) : gsRouteCopy la recopie, gsMigrate la reprend de route_set_v1 ; magRouteDate (bloc de la déclinaison) la valide.
Rien ici ne touche au DOM, à t() ni au réseau ; tout accès au stockage est en try/catch : sans stockage, l'écran marche.

gsMigrate(packFn) : au premier chargement de l'un des deux modules, la fiche est bâtie des groupes de fc_state_v1 puis des routes de route_set_v1 qui portent un lien
par nom ; packFn(route, théâtre) rend les points de la route au format du paquet (ou null : la route est laissée de côté).

Usage (par les builds) : from group_store_block import build_block ; texte = build_block()
"""

BLOCK_BEGIN = '/* ===== GROUPES PARTAGÉS (flight_set_v1) ===== */'
BLOCK_END = '/* ===== FIN DES GROUPES PARTAGÉS ===== */'

_JS = r"""
const KEY_FLIGHT_SET = 'flight_set_v1', KEY_FLIGHT_SET_BAD = 'flight_set_v1_illisible', FLIGHT_SET_FORMAT = 'dcs-flight-set-v1';
const GS_KEY_FC = 'fc_state_v1', GS_KEY_ROUTES = 'route_set_v1', GS_KEY_ROUTE = 'route_state_v1', GS_KEY_DG = 'datacard_state_v1', GS_KEY_LAYERS = 'route_layers_v1';
/* Les clés de contenu des trois outils du Flight Leader (Flight Configurator, Route Planner, Datacard Generator), écrites une seule fois : ce que le geste « Remplacer » (Exemple, ouverture d'un fichier) photographie
   pour « Restaurer », quel que soit l'outil où l'on est. Les groupes, leurs routes et calques, les datacards, le théâtre, les unités et les réglages de cap communs. Ni la langue, ni le thème, ni les replis. */
const GS_CONTENT_KEYS = ['fc_state_v1', 'flight_set_v1', 'flight_set_v1_illisible', 'route_set_v1', 'route_state_v1', 'route_layers_v1', 'datacard_state_v1', 'mp_theatre_v1', 'mp_units_v1', 'mp_nav_v1'];
/* Un geste « Remplacer » se termine par gsSettled : les autres outils ouverts dans la page suivent le geste par évènement « storage » et, après un court calme, réécrivent leurs copies (les datacards gardent la dernière copie de la route) ;
   « Restaurer » ne compare le stockage à ce qu'il était qu'une fois ce calme passé, sinon il se croirait devant des données changées. À rendre par run (replaceWithRestore attend la promesse) : run: () => { …; return gsSettled(); }. Faux (rien n'a changé) passe tel quel.
   Le calme est mesuré, pas supposé : aucune écriture des clés de contenu (GS_CONTENT_KEYS) pendant GS_CALM_MS, qu'elle vienne d'un autre outil (évènement « storage ») ou de cette page (le texte des clés relu toutes les GS_CALM_STEP_MS) ;
   il doit se retrouver à deux relectures de suite (une écriture qui tombe juste à l'échéance, comme la reprise du Route Planner après 400 ms, repart de zéro) ; au bout de GS_CALM_MAX_MS on continue comme avant, calme ou non. */
const GS_CALM_MS = 400, GS_CALM_MAX_MS = 3000, GS_CALM_STEP_MS = 50;
function gsSettled(r) {
  if (r === false) return false;
  return new Promise(res => {
    const t0 = Date.now(), vals = GS_CONTENT_KEYS.map(gsLsGet);
    let last = t0, calm = 0, tm = 0;
    const onSt = e => { if (e.key === null || GS_CONTENT_KEYS.indexOf(e.key) >= 0) last = Date.now(); };
    window.addEventListener('storage', onSt);
    const tick = () => {
      const now = Date.now();
      GS_CONTENT_KEYS.forEach((k, i) => { const v = gsLsGet(k); if (v !== vals[i]) { vals[i] = v; last = now; } });
      calm = now - last >= GS_CALM_MS ? calm + 1 : 0;
      if (calm >= 2 || now - t0 >= GS_CALM_MAX_MS) { window.removeEventListener('storage', onSt); res(r); return; }
      tm = setTimeout(tick, GS_CALM_STEP_MS);
    };
    tm = setTimeout(tick, GS_CALM_STEP_MS);
  });
}

function gsIsObj(v) { return !!v && typeof v === 'object' && !Array.isArray(v); }
function gsLsGet(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }
function gsLsSet(k, v) { try { localStorage.setItem(k, v); return true; } catch (e) { return false; } }
function gsLsDel(k) { try { localStorage.removeItem(k); return true; } catch (e) { return false; } }
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
/* Les canaux à imprimer sur la datacard d'un groupe : radioPrint, « type|poste|canal » → { on, label, mod }, une clé de groupe comme les autres (le Flight Configurator coche, le Datacard Generator coche, nomme et module ;
   le paquet de vol ne la porte pas). gsPrintNorm en rend une copie lisible : seules les entrées objets sont gardées, on est un booléen, label et mod des textes. */
function gsPrintNorm(o) {
  const r = {};
  if (gsIsObj(o)) Object.keys(o).forEach(k => {
    const e = o[k];
    if (gsIsObj(e)) r[k] = { on: e.on === true, label: typeof e.label === 'string' ? e.label : '', mod: typeof e.mod === 'string' ? e.mod : '' };
  });
  return r;
}
/* La migration de radioPrint, une fois : un groupe qui n'a pas encore radioPrint et dont la datacard liée (cards : les cartes du document des datacards, gsId = fcId du groupe) a des canaux cochés prend ceux de la carte ;
   ensuite le groupe fait foi. Les deux outils l'appellent à leur chargement (le Datacard Generator avec les cartes qu'il vient de lire, le Flight Configurator sans argument : les cartes sont alors lues dans datacard_state_v1).
   Rend vrai si un groupe a été écrit. */
function gsPrintMigrate(cards) {
  if (cards === undefined) { const d = gsJson(GS_KEY_DG); cards = gsIsObj(d) ? d.cards : null; }
  if (!Array.isArray(cards)) return false;
  const g = gsRead();
  if (g === null) return false;
  let any = false;
  g.flights.forEach(f => {
    if (gsIsObj(f.radioPrint)) return;
    const c = cards.find(x => gsIsObj(x) && x.gsId === f.fcId && gsIsObj(x.radioSel) && Object.keys(x.radioSel).some(k => gsIsObj(x.radioSel[k]) && x.radioSel[k].on === true));
    if (!c) return;
    const nf = JSON.parse(JSON.stringify(f));
    nf.radioPrint = gsPrintNorm(c.radioSel);
    if (gsPutFlight(nf)) any = true;
  });
  return any;
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

/* Les groupes d'un état v1 (fc_state_v1, fichier de travail) avec un fcId chacun, le même partout : un groupe sans fcId (ou dont le fcId est déjà pris) reçoit 'fv1' + son rang dans la liste ;
   une seule fonction, pour la migration (RP ou FC) et pour le FC qui lit l'état. Rend une copie de la liste (les groupes changés sont des copies), les entrées qui ne sont pas des objets sont gardées. */
function gsLegacyIds(list) {
  const seen = new Set();
  list.forEach(f => { if (gsIsObj(f) && typeof f.fcId === 'string' && f.fcId !== '') seen.add(f.fcId); });
  const used = new Set();
  return list.map((f, i) => {
    if (!gsIsObj(f)) return f;
    let id = typeof f.fcId === 'string' ? f.fcId : '';
    if (id === '' || used.has(id)) {
      id = 'fv1' + i;
      while (used.has(id) || (seen.has(id) && id !== f.fcId)) id += 'x';
      f = Object.assign({}, f, { fcId: id });
    }
    used.add(id);
    return f;
  });
}

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
let GS_FAILED = false;
function gsNoteWrite(ok) {
  if (ok) { GS_FAILED = false; return; }
  if (GS_FAILED) return;
  GS_FAILED = true;
  try { if (typeof gsOnSaveFail === 'function') gsOnSaveFail(); } catch (e) { /* le toast est facultatif */ }
}
function gsWrite(theatre, flights) {
  const ok = gsLsSet(KEY_FLIGHT_SET, JSON.stringify({ format: FLIGHT_SET_FORMAT, theatre: typeof theatre === 'string' ? theatre : '', flights: flights }));
  gsNoteWrite(ok);
  return ok;
}
/* Les points d'une route lue brute (route_set_v1) au format du paquet, à la vitesse sol gs (km/h) ; null sans projection du théâtre. Un point sans coordonnées valides est écarté. */
function gsPackRoute(r, th, gs) {
  if (!Object.prototype.hasOwnProperty.call(TM_PARAMS, th)) return null;
  const o = {};
  (Array.isArray(r.points) ? r.points : []).filter(p => gsIsObj(p) && packValidCoord(p.lat, p.lon)).forEach((p, k) => { o[String(k + 1)] = packPoint(p, k, th, gs); });
  return o;
}
/* La copie de route d'un groupe : { points } et, si la route a reçu une date de sa source (AAAA-MM-JJ lisible, magRouteDate du bloc de la déclinaison), missionDate. La date suit la route : toute copie en passe par ici. */
function gsRouteCopy(pts, date) {
  const r = { points: pts }, d = magRouteDate(date);
  if (d !== '') r.missionDate = d;
  return r;
}
/* Seule la migration fait naître la fiche : une écriture sur une fiche absente la fait d'abord ; si la migration ne peut pas écrire, l'écriture rend faux et rien n'est écrit. */
let GS_PACKER = null;
function gsEnsure() {
  if (gsRead() !== null) return true;
  gsMigrate(GS_PACKER);
  return gsRead() !== null;
}
/* Remplace le groupe de même fcId (à sa place) ou ajoute f à la fin ; relit d'abord. Vrai si la fiche porte f à la fin (écrite, ou déjà identique). */
function gsPutFlight(f) {
  if (!gsIsObj(f) || typeof f.fcId !== 'string' || f.fcId === '') return false;
  if (!gsEnsure()) return false;
  const g = gsRead();
  const i = g.flights.findIndex(x => x.fcId === f.fcId);
  if (i >= 0) {
    if (gsStable(g.flights[i]) === gsStable(f)) return true;
    g.flights[i] = f;
  } else g.flights.push(f);
  return gsWrite(g.theatre, g.flights);
}
/* La datacard d'un groupe retiré : les cartes de datacard_state_v1 qui portent son fcId (gsId) sont retirées ; le reste du document est gardé tel quel (ses réglages, ses autres cartes).
   Un document absent ou illisible n'est pas touché. Les modules qui montrent des datacards se relisent par l'évènement « storage » de la clé. */
function gsDropCard(fcId) {
  const d = gsJson(GS_KEY_DG);
  if (!gsIsObj(d) || !Array.isArray(d.cards)) return false;
  const n = d.cards.filter(c => !(gsIsObj(c) && c.gsId === fcId));
  if (n.length === d.cards.length) return false;
  d.cards = n;
  return gsLsSet(GS_KEY_DG, JSON.stringify(d));
}
function gsRemoveFlight(fcId) {
  if (!gsEnsure()) return false;
  const g = gsRead();
  const n = g.flights.filter(x => x.fcId !== fcId);
  if (n.length === g.flights.length) return true;
  if (!gsWrite(g.theatre, n)) return false;
  gsDropCard(fcId);       /* la fiche d'abord : sans elle, la datacard reste */
  return true;
}
function gsSetTheatre(th) {
  if (!gsEnsure()) return false;
  const g = gsRead();
  if (g.theatre === th) return true;
  return gsWrite(th, g.flights);
}
/* Écrit tout : l'ouverture d'un fichier de travail du Flight Configurator */
function gsReplaceAll(theatre, flights) {
  return gsWrite(theatre, flights.filter(gsIsObj));
}

/* La migration : la fiche n'existe pas encore (ou ne se lit pas).
   1. les groupes de fc_state_v1 (avec leur fcId) et son théâtre ; à défaut le théâtre de route_state_v1 ; à défaut '' ;
   2. dans l'ordre de route_set_v1, chaque route du théâtre de la fiche (son champ theatre, sinon celui de route_state_v1 : routeTheatre) qui porte un lien par nom (flight) : les groupes de même nom rogné (casse exacte) et même camp :
      un seul, sans route : il la prend ; un seul qui a déjà une route : rien ; aucun : un groupe neuf sans unité ; plusieurs : rien.
      Pas de route retenue sans théâtre commun : le théâtre de la fiche et celui de route_state_v1 doivent être le même ;
   3. écrit la fiche (même vide), puis, seulement si elle est écrite, réécrit fc_state_v1 en { v: 2, sel, mine } : un stockage plein laisse fc_state_v1 tel qu'il est. route_set_v1 n'est pas touché.
   Une fiche qui existe sans se lire est recopiée sous flight_set_v1_illisible (une seule fois) avant d'être remplacée ; si la copie échoue, rien n'est remplacé.
   Un échec pose gsMigrateFailed dans fc_state_v1 ; une migration retentée ne fait alors que l'étape 1 (les liens par nom ne sont posés qu'au premier essai réussi d'un module qui n'a jamais échoué).
   Rend vrai si la fiche a été écrite. */
function gsMigrateFail() {
  /* le premier échec est noté dans fc_state_v1 : une migration retentée ne refait pas l'étape 2 */
  const fc = gsJson(GS_KEY_FC);
  if (gsIsObj(fc) && fc.gsMigrateFailed !== true) gsLsSet(GS_KEY_FC, JSON.stringify(Object.assign({}, fc, { gsMigrateFailed: true })));
  return false;
}
function gsMigrate(packFn) {
  if (typeof packFn === 'function') GS_PACKER = packFn;
  if (gsRead() !== null) return false;
  const bad = gsLsGet(KEY_FLIGHT_SET);       // une fiche qui existe mais ne se lit pas : sa valeur est gardée telle quelle, une seule fois, avant d'être remplacée ; sans copie, pas de remplacement
  if (bad !== null && gsLsGet(KEY_FLIGHT_SET_BAD) === null && !gsLsSet(KEY_FLIGHT_SET_BAD, bad)) { gsNoteWrite(false); return gsMigrateFail(); }
  const fc = gsJson(GS_KEY_FC), st = gsIsObj(fc) && gsIsObj(fc.state) ? fc.state : null;
  const retry = gsIsObj(fc) && fc.gsMigrateFailed === true;       // un premier essai a échoué : seulement l'étape 1
  const rs = gsJson(GS_KEY_ROUTE), rsTheatre = gsIsObj(rs) && typeof rs.theatre === 'string' ? rs.theatre : '';
  const flights = [], seen = new Set();
  if (st && Array.isArray(st.flights)) gsLegacyIds(st.flights).forEach(f => {
    if (!gsIsObj(f)) return;
    seen.add(f.fcId);
    flights.push(f);
  });
  const theatre = st && typeof st.theatre === 'string' && st.theatre !== '' ? st.theatre : rsTheatre;
  const set = gsJson(GS_KEY_ROUTES);
  if (!retry && theatre !== '' && theatre === rsTheatre && gsIsObj(set) && Array.isArray(set.routes) && typeof packFn === 'function') {
    set.routes.forEach(r => {
      if (!gsIsObj(r) || !gsIsObj(r.flight) || typeof r.rid !== 'string' || !/^[a-z0-9]{6,32}$/.test(r.rid)) return;
      if (routeTheatre(r, rsTheatre) !== theatre) return;       /* une route d'un autre théâtre (masquée au Route Planner) ne se lie à aucun groupe : elle n'est pas de ce théâtre */
      const name = gsNameKey(r.flight.groupName), side = gsSide(r.flight.coalition);
      if (name === '') return;
      const hits = flights.filter(f => gsNameKey(f.name) === name && gsSide(f.coalition) === side);
      if (hits.length > 1 || (hits.length === 1 && hits[0].route)) return;
      let pts = null;
      try { pts = packFn(r, theatre); } catch (e) { pts = null; }
      if (!gsIsObj(pts)) return;
      const link = { rid: r.rid, name: typeof r.name === 'string' ? r.name : '' };
      if (hits.length === 1) { hits[0].route = gsRouteCopy(pts, r.missionDate); hits[0].routeLink = link; }
      else flights.push({ fcId: gsNewId(), name: r.flight.groupName, coalition: side, route: gsRouteCopy(pts, r.missionDate), routeLink: link, units: [] });
    });
  }
  if (!gsWrite(theatre, flights)) return gsMigrateFail();
  if (gsIsObj(fc)) {
    const sel = st && gsIsObj(st.sel) ? st.sel : (gsIsObj(fc.sel) ? fc.sel : { f: 0, u: 0 });
    gsLsSet(GS_KEY_FC, JSON.stringify({ v: 2, sel: sel, mine: gsIsObj(fc.mine) ? fc.mine : {} }));
  }
  return true;
}

/* « Tout effacer » des trois outils du Flight Leader : ce qui est effacé, ce qui reste.
   Effacé : les groupes (flight_set_v1 : une fiche vide, son théâtre gardé ; fc_state_v1 : la sélection revient au premier groupe), les routes de tous les théâtres (route_set_v1 retirée), la route, ses références
   et sa date (route_state_v1), les calques (route_layers_v1 retirée), toutes les datacards (datacard_state_v1 : aucune carte), libres et liées.
   Reste : les presets d'emport (fc_state_v1.mine), les réglages de route_state_v1 (théâtre, unités, cap, vitesse, boîtes, affichage), le mode et le théâtre du document des datacards, mp_theatre_v1, mp_units_v1, mp_nav_v1,
   la langue, le thème, les replis, l'affichage ; HQ (mission_snapshot_v1), le Briefing Generator, Recon Station et wing_config_v1 ne sont jamais touchés. La copie d'anciens groupes qu'un module a gardée de la fiche
   (flight_set_v1_illisible) est retirée aussi : un groupe effacé ne doit pas revenir de là.
   Les clés qui se lisent s'écrivent d'abord, la fiche en dernier : un module qui suit les évènements « storage » relit les groupes une fois le reste en place. Rend faux si une écriture a échoué. */
function gsClearAll() {
  let ok = true;
  const set = (k, v) => { if (!gsLsSet(k, v)) ok = false; };
  const del = k => { if (gsLsGet(k) !== null && !gsLsDel(k)) ok = false; };
  del(GS_KEY_ROUTES);
  del(GS_KEY_LAYERS);
  del(KEY_FLIGHT_SET_BAD);
  const rs = gsJson(GS_KEY_ROUTE);
  if (gsIsObj(rs)) { rs.name = ''; rs.points = []; rs.refs = []; delete rs.missionDate; set(GS_KEY_ROUTE, JSON.stringify(rs)); }
  else del(GS_KEY_ROUTE);
  const dg = gsJson(GS_KEY_DG);
  if (gsIsObj(dg)) { dg.cards = []; set(GS_KEY_DG, JSON.stringify(dg)); }
  else del(GS_KEY_DG);
  const fc = gsJson(GS_KEY_FC);
  if (gsIsObj(fc)) set(GS_KEY_FC, JSON.stringify({ v: 2, sel: { f: 0, u: 0 }, mine: gsIsObj(fc.mine) ? fc.mine : {} }));
  const g = gsRead();
  if (!gsWrite(g ? g.theatre : '', [])) ok = false;
  return ok;
}
"""


def build_block():
    """Le texte du bloc, délimité par ses deux commentaires, terminé par un saut de ligne."""
    return BLOCK_BEGIN + _JS + BLOCK_END + '\n'


if __name__ == '__main__':
    txt = build_block()
    print(f"[OK] bloc des groupes partagés : {len(txt)} caractères")
