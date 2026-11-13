#!/usr/bin/env python3
"""Bloc « ÉCRITURE D'UNE ROUTE » : le seul chemin par lequel un module autre que le Route Planner écrit une route.

Injecté tel quel au Route Planner (qui y prend l'identifiant stable pid : tirage, validité, attribution) et au Datacard Generator (qui y écrit).
Il lit et réécrit à l'instant (jamais une copie gardée) :
  1. route_set_v1 : la route par son rid (créée si neuve), les autres routes (masquées comprises) et « active » intacts ;
  2. route_state_v1 si cette route est l'active de route_set_v1 (le Route Planner la prend pour source à son chargement) ; les autres champs (unités, vitesse, ui, réglages) intacts ;
  3. la copie du groupe qui la suit (routeLink.rid), par gsPutFlight, avec la règle de gsSyncRoutes du Route Planner : deux points au moins, théâtre de la fiche = celui de la route
     (ou fiche sans théâtre), théâtre avec projection ; même résultat que si le Route Planner avait enregistré.
Les références ne sont pas à une route : elles sont celles du Route Planner (route_state_v1.refs, S.refs), communes à la mission ; seul route_state_v1 change pour elles.
Une écriture qui échoue (stockage plein, 12 routes déjà sur le théâtre, 30 points, 12 références) ne laisse rien d'écrit à moitié : les clés déjà écrites sont remises comme elles étaient ;
la valeur rendue le dit ({ ok: false, why }), l'appelant l'annonce.
pid : chaîne [a-z0-9]{8,16}, unique dans sa liste ; il n'entre jamais dans le paquet de vol, la copie de route d'un groupe (gsPackRoute ne le recopie pas) ni l'export du Route Tool.

La route porte, facultative, la date de la mission d'où elle vient (route.missionDate, AAAA-MM-JJ lisible par magRouteDate) : elle suit la route dans route_set_v1, route_state_v1 (la route active) et la copie du groupe ; modifier les points ne l'efface pas.

Dépend, dans la page : magRouteDate (bloc de la déclinaison), routeTheatre / rtThOk (bloc du théâtre d'une route), gsRead, gsPutFlight, gsPackRoute, gsStable, gsIsObj, gsSetTheatre (bloc des groupes), TM_PARAMS (bloc des projections, facultatif :
sans lui, aucune copie de groupe n'est écrite).

Usage (par les builds) : from route_write_block import build_block ; texte = build_block()
"""

BLOCK_BEGIN = '/* ===== ÉCRITURE D\'UNE ROUTE (route_set_v1, route_state_v1, copie du groupe) ===== */'
BLOCK_END = '/* ===== FIN DE L\'ÉCRITURE D\'UNE ROUTE ===== */'

_JS = r"""
const RW_KEY_SET = 'route_set_v1', RW_KEY_STATE = 'route_state_v1', RW_KEY_FLIGHT = 'flight_set_v1', RW_KEY_UNITS = 'mp_units_v1', RW_KEY_NAV = 'mp_nav_v1', RW_KEY_TH = 'mp_theatre_v1';
const RW_SET_FORMAT = 'dcs-route-set-v1', RW_ROUTE_FORMAT = 'dcs-route-v1';
const RW_MAX_POINTS = 30, RW_MAX_REFS = 12, RW_MAX_ROUTES = 12, RW_GS_DEFAULT = 220;
const RW_CHARS = 'abcdefghijklmnopqrstuvwxyz0123456789';

function rwObj(v) { return !!v && typeof v === 'object' && !Array.isArray(v); }
function rwClone(v) { return JSON.parse(JSON.stringify(v)); }
function rwPidValid(s) { return typeof s === 'string' && /^[a-z0-9]{8,16}$/.test(s); }
function rwRidValid(s) { return typeof s === 'string' && /^[a-z0-9]{6,32}$/.test(s); }
/* 12 caractères [a-z0-9] tirés par crypto.getRandomValues (repli Math.random), absents de taken : la règle de newRid du Route Planner */
function rwRand(taken) {
  const used = taken || new Set();
  for (;;) {
    let out = '';
    try {
      const a = new Uint8Array(48);
      crypto.getRandomValues(a);
      for (let i = 0; i < a.length && out.length < 12; i++) if (a[i] < 252) out += RW_CHARS[a[i] % 36];      /* 252 = 7 × 36 : pas de biais */
    } catch (e) { out = ''; }
    while (out.length < 12) out += RW_CHARS[Math.floor(Math.random() * 36)];
    if (!used.has(out)) return out;
  }
}
function rwNewPid(taken) { return rwRand(taken); }
function rwNewRid(taken) { return rwRand(taken); }
/* Chaque élément porte un pid valide et distinct ; vrai si un pid a été tiré */
function rwAssignPids(list) {
  const seen = new Set();
  let drawn = false;
  list.forEach(p => { if (rwObj(p) && rwPidValid(p.pid) && !seen.has(p.pid)) seen.add(p.pid); else if (rwObj(p)) p.pid = null; });
  list.forEach(p => { if (rwObj(p) && !p.pid) { p.pid = rwNewPid(seen); seen.add(p.pid); drawn = true; } });
  return drawn;
}
function rwValidCoord(lat, lon) {
  return typeof lat === 'number' && typeof lon === 'number' && isFinite(lat) && isFinite(lon) && Math.abs(lat) <= 90 && Math.abs(lon) <= 180;
}
function rwGet(k) { try { const r = localStorage.getItem(k); return r === null ? null : JSON.parse(r); } catch (e) { return null; } }
function rwRaw(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }
function rwHasProj(th) { return typeof TM_PARAMS === 'object' && TM_PARAMS !== null && Object.prototype.hasOwnProperty.call(TM_PARAMS, th); }

/* Le jeu de routes lu : l'objet brut (toutes les routes, masquées comprises, gardées telles quelles) ; null s'il est absent, d'un autre format ou sans liste de routes */
function rwReadSet() {
  const o = rwGet(RW_KEY_SET);
  if (!rwObj(o) || o.format !== RW_SET_FORMAT || !Array.isArray(o.routes)) return null;
  o.routes = o.routes.filter(r => rwObj(r) && Array.isArray(r.points));
  if (!o.routes.length) return null;
  if (!(Number.isInteger(o.active) && o.active >= 0 && o.active < o.routes.length)) o.active = 0;
  return o;
}
/* L'état lu : route_state_v1 s'il se lit comme une route (format et liste de points), sinon null */
function rwReadState() {
  const o = rwGet(RW_KEY_STATE);
  return rwObj(o) && o.format === RW_ROUTE_FORMAT && Array.isArray(o.points) ? o : null;
}
/* Le théâtre de référence des routes d'avant le lot : celui de route_state_v1 s'il est valide, sinon mp_theatre_v1, sinon Caucasus */
function rwRefTheatre(st) {
  if (rwObj(st) && rtThOk(st.theatre)) return st.theatre;
  const k = rwGet(RW_KEY_TH);
  return rwObj(k) && rtThOk(k.theatre) ? k.theatre : 'Caucasus';
}
/* Le Route Planner prend route_state_v1 pour source de la route active : ici aussi, la route active du jeu prend le nom et les points de l'état (du même théâtre) avant tout changement */
function rwFresh(set, st) {
  const act = set.routes[set.active];
  if (act && st && routeTheatre(act, rwRefTheatre(st)) === rwRefTheatre(st)) {
    act.name = typeof st.name === 'string' ? st.name : act.name; act.points = st.points;
    const d = magRouteDate(st.missionDate);       /* la date de la route active suit son état comme son nom et ses points ; un état sans date lisible laisse celle du jeu */
    if (d !== '') act.missionDate = d;
  }
  return act;
}
/* Les routes du jeu qui sont du théâtre th (la règle du théâtre d'une route) */
function rwRoutesOf(set, th, st) {
  const ref = rwRefTheatre(st);
  return set ? set.routes.filter(r => routeTheatre(r, ref) === th) : [];
}
/* Une route lue pour l'appelant : { rid, name, theatre, points (copies), active } ; null si le rid n'y est pas. Les points sans pid en reçoivent un (non écrit : rwUpdateRoute l'écrit). */
function rwFind(rid) {
  const set = rwReadSet(), st = rwReadState();
  if (!set) return null;
  rwFresh(set, st);
  const i = set.routes.findIndex(r => r.rid === rid);
  return i < 0 ? null : set.routes[i];
}

/* Écrit toutes les clés ou aucune : celles déjà écrites sont remises comme elles étaient */
function rwCommit(items) {
  const old = items.map(it => rwRaw(it.k));
  let n = 0;
  try {
    for (; n < items.length; n++) localStorage.setItem(items[n].k, items[n].v);
    return true;
  } catch (e) {
    rwRestore(items.slice(0, n), old.slice(0, n));
    return false;
  }
}
function rwRestore(items, old) {
  items.forEach((it, i) => { try { if (old[i] === null) localStorage.removeItem(it.k); else localStorage.setItem(it.k, old[i]); } catch (e) { /* rien de plus à faire */ } });
}

/* Un état minimal que parseRoute du Route Planner accepte : les défauts du Route Planner, le théâtre commun ; la route active du jeu (nom, points) si le jeu existe */
function rwMinimalState(set, th) {
  const act = set ? set.routes[set.active] : null;
  const un = rwGet(RW_KEY_UNITS), nv = rwGet(RW_KEY_NAV);
  const nd = rwObj(nv) ? nv : {};
  return {
    format: RW_ROUTE_FORMAT, name: act && typeof act.name === 'string' ? act.name : '', theatre: act && rtThOk(act.theatre) ? act.theatre : (rtThOk(th) ? th : rwRefTheatre(null)),
    units: { distance: rwObj(un) && un.distance === 'nm' ? 'nm' : 'km', altitude: rwObj(un) && un.altitude === 'ft' ? 'ft' : 'm' },
    navDisplay: { ref: nd.ref === 'mag' ? 'mag' : 'true', decl: typeof nd.decl === 'string' ? nd.decl : '', mode: nd.mode === 'manual' ? 'manual' : 'calc', year: typeof nd.year === 'string' && /^\d{1,4}$/.test(nd.year) ? nd.year : '', force: nd.force === true },
    groundSpeed: RW_GS_DEFAULT, legBoxes: 'full',
    points: act ? act.points : [], refs: [],
    ui: { layer: 'topo', grid: true, places: false, towns: true, airfields: true, trace: 'route', ticks: 'route' }
  };
}

function rwGs(st) { return rwObj(st) && typeof st.groundSpeed === 'number' && st.groundSpeed > 0 ? st.groundSpeed : RW_GS_DEFAULT; }
/* La copie d'un groupe qui prend la route r (ses points au format du paquet : pts) */
function rwGroupTakes(f, r, pts) {
  const nf = rwClone(f);
  nf.route = gsRouteCopy(rwClone(pts), r.missionDate);       /* la date de la route la suit */
  nf.routeLink = { rid: r.rid, name: r.name };
  return nf;
}
function rwCopyDate(f) { return gsIsObj(f.route) ? magRouteDate(f.route.missionDate) : ''; }       /* la date que la copie de route d'un groupe porte ('' : aucune) */
function rwPackable(route, th, g) {
  if (!rwHasProj(th) || route.points.length < 2) return false;
  return g.theatre === '' || g.theatre === th;
}
/* Les groupes qui suivent la route reçoivent sa copie (la règle de gsSyncRoutes) ; faux si l'écriture d'un groupe échoue */
function rwSyncGroups(route, th, st) {
  if (typeof gsRead !== 'function') return true;
  const g = gsRead();
  if (!g) return true;
  if (!rwPackable(route, th, g)) return true;
  const pts = gsPackRoute(route, th, rwGs(st));
  if (!pts) return true;
  for (let i = 0; i < g.flights.length; i++) {
    const f = g.flights[i], l = f.routeLink;
    if (!gsIsObj(l) || l.rid !== route.rid) continue;
    if (gsStable(f.route && f.route.points !== undefined ? f.route.points : null) === gsStable(pts) && l.name === route.name && rwCopyDate(f) === magRouteDate(route.missionDate)) continue;
    if (g.theatre === '') { gsSetTheatre(th); g.theatre = th; }
    if (!gsPutFlight(rwGroupTakes(f, route, pts))) return false;
  }
  return true;
}
/* Le groupe fcId suit la route : routeLink posé ; sa copie de points avec, quand la route la permet (deux points, théâtre) ; une copie plus ancienne reste sinon */
function rwLinkFlight(fcId, route, th, st) {
  if (typeof gsRead !== 'function') return false;
  const g = gsRead(), f = g ? g.flights.find(x => x.fcId === fcId) : null;
  if (!f) return false;
  let nf;
  const pts = rwPackable(route, th, g) ? gsPackRoute(route, th, rwGs(st)) : null;
  if (pts) { if (g.theatre === '') { gsSetTheatre(th); } nf = rwGroupTakes(f, route, pts); }
  else { nf = rwClone(f); nf.routeLink = { rid: route.rid, name: route.name }; }
  return gsPutFlight(nf);
}

/* Écrit le jeu, l'état (si la route est l'active, ou si l'état doit naître) et les groupes qui la suivent. o.link : { fcId } un groupe qui prend la route ; o.state : l'état à écrire (déjà changé) */
function rwWrite(set, route, o) {
  o = o || {};
  const st0 = rwReadState();
  let st = o.state || null;
  const act = set.routes[set.active];
  const isAct = !!route && !!act && act.rid === route.rid;
  if (isAct) {
    if (!st) st = st0 ? rwClone(st0) : rwMinimalState(set, route.theatre);
    st.name = route.name; st.points = route.points;       /* la route active : route_state_v1 fait foi pour elle au chargement du Route Planner */
    if (magRouteDate(route.missionDate) !== '') st.missionDate = route.missionDate; else delete st.missionDate;       /* ... sa date avec elle */
  }
  const items = [{ k: RW_KEY_SET, v: JSON.stringify(set) }];
  if (st) items.push({ k: RW_KEY_STATE, v: JSON.stringify(st) });
  const flightRaw = rwRaw(RW_KEY_FLIGHT);
  if (!rwCommit(items)) return { ok: false, why: 'full' };
  const th = route ? routeTheatre(route, rwRefTheatre(st || st0)) : '';
  let good = true;
  if (route && o.link && o.link.fcId) good = rwLinkFlight(o.link.fcId, route, th, st || st0);
  if (good && route) good = rwSyncGroups(route, th, st || st0);
  if (!good) {
    rwRestore(items, items.map(it => (it.k === RW_KEY_SET ? o.oldSet : o.oldState)));
    try { if (flightRaw === null) localStorage.removeItem(RW_KEY_FLIGHT); else localStorage.setItem(RW_KEY_FLIGHT, flightRaw); } catch (e) { /* idem */ }
    return { ok: false, why: 'full' };
  }
  return { ok: true, route: route };
}

/* Change la route rid : mut(route) modifie son nom ou ses points (objets bruts ; faux : rien n'est écrit). Rend { ok, route } ou { ok: false, why : 'none' | 'gone' | 'abort' | 'max' | 'full' } */
function rwUpdateRoute(rid, mut, o) {
  const set = rwReadSet(), st = rwReadState();
  if (!set) return { ok: false, why: 'none' };
  const oldSet = rwRaw(RW_KEY_SET), oldState = rwRaw(RW_KEY_STATE);
  rwFresh(set, st);
  const route = set.routes.find(r => r.rid === rid);
  if (!route) return { ok: false, why: 'gone' };
  if (mut && mut(route) === false) return { ok: false, why: 'abort' };
  if (route.points.length > RW_MAX_POINTS) return { ok: false, why: 'pts' };
  rwAssignPids(route.points);
  return rwWrite(set, route, Object.assign({ oldSet: oldSet, oldState: oldState }, o || {}));
}

/* Une route neuve, au théâtre th : { name, theatre, points, fcId?, missionDate? } ; le groupe fcId la suit. Rend { ok, rid, route } ou { ok: false, why: 'max' | 'full' | 'link' }.
   12 routes sur le théâtre : refus. Un jeu absent naît ; l'état du Route Planner qui n'avait pas de jeu devient la route 1 (rien ne se perd). */
function rwCreateRoute(o) {
  let set = rwReadSet();
  const st0 = rwReadState();
  const oldSet = rwRaw(RW_KEY_SET), oldState = rwRaw(RW_KEY_STATE);
  const th = o.theatre;
  if (!set) {
    set = { format: RW_SET_FORMAT, active: 0, routes: [] };
    if (st0 && st0.points.length) {
      const r0 = { rid: rwNewRid(new Set()), name: typeof st0.name === 'string' ? st0.name : '', points: st0.points, flight: null, theatre: rtThOk(st0.theatre) ? st0.theatre : rwRefTheatre(null) };
      if (magRouteDate(st0.missionDate) !== '') r0.missionDate = st0.missionDate;       /* l'état qui devient la route 1 garde sa date */
      set.routes.push(r0);
    }
  } else rwFresh(set, st0);
  if (rwRoutesOf(set, th, st0).length >= RW_MAX_ROUTES) return { ok: false, why: 'max' };
  const taken = new Set(set.routes.map(r => r.rid));
  const route = { rid: rwNewRid(taken), name: String(o.name || '').slice(0, 60), points: (o.points || []).slice(0, RW_MAX_POINTS), flight: null, theatre: th };
  if (magRouteDate(o.missionDate) !== '') route.missionDate = o.missionDate;       /* o.missionDate : la date d'une route dont celle-ci est la copie (route importée d'un groupe, route d'un fichier) ; une route tracée de rien n'en a pas */
  rwAssignPids(route.points);
  set.routes.push(route);
  if (set.routes.length === 1) set.active = 0;
  const r = rwWrite(set, route, { link: o.fcId ? { fcId: o.fcId } : null, oldSet: oldSet, oldState: oldState });
  if (!r.ok) return r;
  if (o.fcId && !rwLinkedTo(o.fcId, route.rid)) return { ok: true, rid: route.rid, route: route, link: false };
  return { ok: true, rid: route.rid, route: route, link: true };
}
function rwLinkedTo(fcId, rid) {
  const g = typeof gsRead === 'function' ? gsRead() : null, f = g ? g.flights.find(x => x.fcId === fcId) : null;
  return !!f && gsIsObj(f.routeLink) && f.routeLink.rid === rid;
}
/* Le groupe fcId suit désormais la route rid (une route par groupe) */
function rwLinkRoute(fcId, rid) {
  const set = rwReadSet(), st = rwReadState();
  if (!set) return { ok: false, why: 'none' };
  rwFresh(set, st);
  const route = set.routes.find(r => r.rid === rid);
  if (!route) return { ok: false, why: 'gone' };
  const flightRaw = rwRaw(RW_KEY_FLIGHT);
  const ok = rwLinkFlight(fcId, route, routeTheatre(route, rwRefTheatre(st)), st);
  if (!ok) { try { if (flightRaw === null) localStorage.removeItem(RW_KEY_FLIGHT); else localStorage.setItem(RW_KEY_FLIGHT, flightRaw); } catch (e) { /* idem */ } return { ok: false, why: 'full' }; }
  return { ok: true, route: route };
}

/* Les références : celles du Route Planner (route_state_v1.refs). mut(refs) modifie la liste (faux : rien n'est écrit). Seul route_state_v1 change ; un état absent naît minimal. */
function rwUpdateRefs(mut) {
  const set = rwReadSet(), st0 = rwReadState();
  const oldState = rwRaw(RW_KEY_STATE);
  const st = st0 ? st0 : rwMinimalState(set, null);
  if (!Array.isArray(st.refs)) st.refs = [];
  if (mut && mut(st.refs) === false) return { ok: false, why: 'abort' };
  if (st.refs.length > RW_MAX_REFS) return { ok: false, why: 'refs' };
  rwAssignPids(st.refs);
  if (!rwCommit([{ k: RW_KEY_STATE, v: JSON.stringify(st) }])) return { ok: false, why: 'full' };
  return { ok: true, refs: st.refs };
}
/* Les réglages de cap communs (mp_nav_v1) : route_state_v1.navDisplay leur reste égal ; un état absent n'est pas créé pour eux */
function rwSetNavDisplay(n) {
  const st = rwReadState();
  if (!st) return true;
  st.navDisplay = { ref: n.ref, decl: n.decl, mode: n.mode, year: n.year, force: n.force };
  return rwCommit([{ k: RW_KEY_STATE, v: JSON.stringify(st) }]);
}
"""


def build_block():
    """Le texte du bloc, délimité par ses deux commentaires, terminé par un saut de ligne."""
    return BLOCK_BEGIN + _JS + BLOCK_END + '\n'


if __name__ == '__main__':
    txt = build_block()
    print(f"[OK] bloc d'écriture d'une route : {len(txt)} caractères")
