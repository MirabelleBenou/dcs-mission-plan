#!/usr/bin/env python3
"""Bloc « HEURES D'UNE ROUTE » : le calcul des heures réelles d'une route, ses heures fixes, ses tronçons intenables ; une seule source pour le Route Planner et le Datacard Generator.

Injecté tel quel (identique à l'octet) dans les deux outils. Des fonctions pures, sans état de l'écran ni DOM : elles prennent les points d'une route
(lat, lon, gs, t, tLock) et la vitesse par défaut, et rendent les temps.

Les heures vivent sur les points : p.t (« HH:MM:SS », dans la référence de la datacard, sans fuseau) et p.tLock (true, seulement avec un p.t valide).
Les heures fixes sont les points verrouillés et le pivot (le seul point qui porte p.t sans verrou). Une route a des heures dès qu'un point porte p.t ;
sans heure fixe, rien ne change : le temps écoulé.

Les vitesses : p.gs (la vitesse de la branche qui arrive au point, jamais au point 0) et p.gsLock (true, seulement avec un p.gs valide) qui la verrouille. Un tronçon
dont les deux heures fixes ne tiennent pas aux vitesses de la route est orange quand les branches libres peuvent les tenir dans la marge (± %, de 1 à 50, défaut 15),
rouge sinon, avec sa cause ; l'orange porte la vitesse recommandée de chaque branche libre, et « Appliquer » l'écrit dans les points.

La distance d'une branche est celle de legCalc des deux outils (haversine, mêmes opérations dans le même ordre, même rayon) : sans heure, les chiffres sont ceux d'avant.

Usage (par les builds) : from route_timing_block import build_block ; texte = build_block()
"""

BLOCK_BEGIN = '/* ===== HEURES D\'UNE ROUTE (calcul, heures fixes, tronçons intenables) ===== */'
BLOCK_END = '/* ===== FIN DES HEURES D\'UNE ROUTE ===== */'

_JS = r"""
const RTM_R_KM = 6371.0088, RTM_DAY = 86400, RTM_TOL = 5, RTM_MARGIN_DEFAULT = 15;

/* Une heure stockée : « HH:MM:SS », 00-23, 00-59, 00-59 */
function rtmValid(s) {
  const m = typeof s === 'string' ? /^(\d{2}):(\d{2}):(\d{2})$/.exec(s) : null;
  return !!m && +m[1] <= 23 && +m[2] <= 59 && +m[3] <= 59;
}
/* Une heure stockée valide → secondes depuis minuit */
function rtmSecs(s) { const m = /^(\d{2}):(\d{2}):(\d{2})$/.exec(s); return +m[1] * 3600 + +m[2] * 60 + +m[3]; }
/* Une saisie « hh:mm:ss » ou « hh:mm » (un ou deux chiffres par champ) → secondes, ou null */
function rtmParse(s) {
  const m = typeof s === 'string' ? /^\s*(\d{1,2}):(\d{1,2})(?::(\d{1,2}))?\s*$/.exec(s) : null;
  if (!m) return null;
  const h = +m[1], mi = +m[2], se = m[3] === undefined ? 0 : +m[3];
  return (h <= 23 && mi <= 59 && se <= 59) ? h * 3600 + mi * 60 + se : null;
}
function rtmPad(n) { return (n < 10 ? '0' : '') + n; }
/* Des secondes (non arrondies, hors de [0 ; 86 400[ s'il le faut) → « HH:MM:SS » : à la seconde la plus proche (0,5 s vers le haut), modulo 24 h */
function rtmClock(sec) {
  const n = (((Math.floor(sec + 0.5)) % RTM_DAY) + RTM_DAY) % RTM_DAY;
  return rtmPad(Math.floor(n / 3600)) + ':' + rtmPad(Math.floor(n / 60) % 60) + ':' + rtmPad(n % 60);
}
/* … → « HH:MM » : l'heure à la seconde, arrondie à la minute la plus proche (30 s vers le haut) */
function rtmClockMin(sec) {
  const n = (((Math.floor(sec + 0.5)) % RTM_DAY) + RTM_DAY) % RTM_DAY;
  const m = Math.floor((n + 30) / 60) % 1440;
  return rtmPad(Math.floor(m / 60)) + ':' + rtmPad(m % 60);
}
/* Les champs d'heure d'un point lu (src) recopiés sur dst s'ils sont valides, écartés sinon */
function rtmRead(src, dst) {
  if (src && rtmValid(src.t)) { dst.t = src.t; if (src.tLock === true) dst.tLock = true; }
}
/* La vitesse d'une branche lue (src) recopiée sur dst : p.gs (nombre fini > 0, jamais au point 0, k : son rang) et son verrou p.gsLock (seulement avec un p.gs valide) */
function rtmReadGs(src, dst, k) {
  if (k > 0 && src && typeof src.gs === 'number' && isFinite(src.gs) && src.gs > 0) { dst.gs = src.gs; if (src.gsLock === true) dst.gsLock = true; }
}
/* La marge des vitesses (± %) : un entier de 1 à 50, sinon 15 */
function rtmMargin(x) { return (typeof x === 'number' && isFinite(x) && Math.floor(x) === x && x >= 1 && x <= 50) ? x : RTM_MARGIN_DEFAULT; }
/* Une route lue d'un coup : plusieurs heures sans verrou ne tiennent pas (un seul pivot) ; seule celle du point de plus petit rang reste */
function rtmOnePivot(points) {
  let seen = false;
  for (let i = 0; i < points.length; i++) {
    const p = points[i];
    if (!p || !rtmValid(p.t) || p.tLock === true) continue;
    if (seen) { delete p.t; delete p.tLock; } else seen = true;
  }
  return points;
}
/* Distance (km) d'une branche : la formule de legCalc */
function rtmKm(a, b) {
  const r = Math.PI / 180;
  const p1 = a.lat * r, p2 = b.lat * r, dl = (b.lon - a.lon) * r;
  const h = Math.sin((p2 - p1) / 2) * Math.sin((p2 - p1) / 2) + Math.cos(p1) * Math.cos(p2) * Math.sin(dl / 2) * Math.sin(dl / 2);
  return 2 * RTM_R_KM * Math.asin(Math.min(1, Math.sqrt(h)));
}
/* Les temps d'une route : { n, legs (par branche : km, v, sec, lock ; rec et amb sur une branche libre d'un tronçon orange), el (temps écoulé non arrondi), km, sec (la durée totale, les branches orange à leurs vitesses recommandées), has (une heure fixe au moins), fixed, lock, t (secondes non arrondies, ou null sans heure), red, amb }.
   Entre deux heures fixes a et b qui ne tiennent pas à 5 s près : L est le temps des branches verrouillées (gsLock), les autres sont libres, f = (actuel − L) / (besoin − L) ;
   red[b] : null, ou { a, besoin, actuel, f, L, why } : why '0' (besoin nul), 'lk' (aucune branche libre), 'lt' (besoin ≤ L), 'm' (|f − 1| × 100 au-delà de la marge) ;
   amb[b] : null, ou { a, besoin, actuel, f, L, free (les rangs des branches libres) } : dans la marge ; chaque branche libre prend v × f (legs[i].rec), et les heures de a à b se calculent à ces vitesses (b garde sa valeur) */
function rtmCompute(points, gsDefault, margin) {
  const n = points.length, legs = [null], el = [0], mg = rtmMargin(margin);
  let km = 0, sec = 0;
  for (let i = 1; i < n; i++) {
    const k = rtmKm(points[i - 1], points[i]);
    const p = points[i], own = typeof p.gs === 'number' && p.gs > 0, v = own ? p.gs : gsDefault;
    const sc = k / v * 3600;
    legs.push({ km: k, v: v, sec: sc, lock: own && p.gsLock === true });
    km += k; sec += sc;
    el.push(sec);
  }
  const fixed = [], lock = [], t = [], red = [], amb = [], F = [];
  for (let i = 0; i < n; i++) {
    const ok = rtmValid(points[i].t);
    fixed.push(ok); lock.push(ok && points[i].tLock === true); t.push(null); red.push(null); amb.push(null);
    if (ok) F.push(i);
  }
  if (F.length) {
    const T = i => rtmSecs(points[i].t);
    const f0 = F[0], l0 = F[F.length - 1];
    for (let i = 0; i < f0; i++) t[i] = T(f0) - (el[f0] - el[i]);
    for (let i = l0; i < n; i++) t[i] = T(l0) + (el[i] - el[l0]);
    for (let k = 0; k + 1 < F.length; k++) {
      const a = F[k], b = F[k + 1];
      const besoin = (((T(b) - T(a)) % RTM_DAY) + RTM_DAY) % RTM_DAY, actuel = el[b] - el[a];
      if (Math.abs(actuel - besoin) <= RTM_TOL) { for (let i = a; i < b; i++) t[i] = T(a) + (el[i] - el[a]); continue; }
      let L = 0;
      const free = [];
      for (let j = a + 1; j <= b; j++) { if (legs[j].lock) L += legs[j].sec; else free.push(j); }
      const info = { a: a, besoin: besoin, actuel: actuel, f: null, L: L, why: '' };
      if (besoin === 0) info.why = '0';
      else if (!free.length) info.why = 'lk';
      else if (besoin <= L) info.why = 'lt';
      else {
        info.f = (actuel - L) / (besoin - L);
        if (Math.abs(info.f - 1) * 100 > mg) info.why = 'm';
      }
      if (info.why !== '') {
        red[b] = info;
        for (let i = a; i < b; i++) t[i] = T(a) + (el[i] - el[a]);
      } else {
        info.free = free;
        amb[b] = info;
        free.forEach(j => { legs[j].rec = legs[j].v * info.f; legs[j].amb = b; });
        let s = T(a);
        for (let i = a; i < b; i++) { t[i] = s; s += legs[i + 1].amb === b ? legs[i + 1].sec / info.f : legs[i + 1].sec; }
      }
    }
    F.forEach(i => { t[i] = T(i); });
  }
  sec = 0;       /* la durée totale compte les branches d'un tronçon orange à leurs vitesses recommandées (la durée et l'arrivée s'accordent) ; sans orange, c'est la somme des durées des branches */
  for (let i = 1; i < n; i++) sec += legs[i].amb !== undefined && amb[legs[i].amb] ? legs[i].sec / amb[legs[i].amb].f : legs[i].sec;
  return { n: n, legs: legs, el: el, km: km, sec: sec, has: F.length > 0, fixed: fixed, lock: lock, t: t, red: red, amb: amb };
}
/* Les vitesses d'un tronçon orange (b : son point d'arrivée) écrites dans les branches libres : v × f arrondie par round (km/h → km/h de l'unité affichée, entier) ; une branche verrouillée et les autres tronçons ne bougent pas ; faux sans tronçon orange en b */
function rtmApply(points, tm, b, round) {
  const a = tm && tm.amb[b];
  if (!a) return false;
  a.free.forEach(j => { points[j].gs = round(tm.legs[j].v * a.f); });
  return true;
}
/* Verrouiller la vitesse de la branche qui arrive au point i (jamais le point 0) : sans p.gs, la vitesse par défaut est écrite d'abord */
function rtmLockGs(points, i, gsDefault) {
  const p = points[i];
  if (!p || i < 1) return false;
  if (!(typeof p.gs === 'number' && isFinite(p.gs) && p.gs > 0)) p.gs = gsDefault;
  p.gsLock = true;
  return true;
}
/* Déverrouiller : p.gsLock part, p.gs reste */
function rtmUnlockGs(points, i) {
  const p = points[i];
  if (!p) return false;
  delete p.gsLock;
  return true;
}
/* Taper l'heure du point i (sec : secondes, ou null pour la vider) : un point non verrouillé devient le pivot (l'heure des autres points non verrouillés est retirée) ; un point verrouillé change de valeur et garde son verrou ; taper ne verrouille jamais */
function rtmType(points, i, sec) {
  const p = points[i];
  if (!p) return false;
  if (sec === null) { delete p.t; delete p.tLock; return true; }
  p.t = rtmClock(sec);
  if (p.tLock !== true) points.forEach((q, k) => { if (k !== i && q.tLock !== true) delete q.t; });
  return true;
}
/* Verrouiller le point i : son heure affichée (tm : rtmCompute des points tels qu'ils sont) devient p.t, avec p.tLock ; faux sans heure à fixer */
function rtmLock(points, i, tm) {
  const p = points[i];
  if (!p || !tm || tm.t[i] === null) return false;
  p.t = rtmClock(tm.t[i]); p.tLock = true;
  return true;
}
/* Déverrouiller le point i : p.tLock et p.t sont retirés, sauf si c'était la seule heure fixe de la route : p.t reste, le point devient le pivot */
function rtmUnlock(points, i) {
  const p = points[i];
  if (!p) return false;
  const other = points.some((q, k) => k !== i && rtmValid(q.t));
  delete p.tLock;
  if (other) delete p.t;
  return true;
}
/* Le pourcentage du message : (f − 1) × 100 à l'entier le plus proche, au moins 1 en valeur absolue, toujours signé (« + » ou « − » U+2212) ; en français, espace fine insécable avant « % » */
function rtmPct(f, fr) {
  let n = Math.round((f - 1) * 100);
  if (n === 0) n = f >= 1 ? 1 : -1;
  return (n < 0 ? '−' : '+') + Math.abs(n) + (fr ? ' %' : '%');
}
/* mm:ss d'une durée en secondes (comme l'ETE : à la seconde la plus proche, minutes sur deux chiffres au moins) */
function rtmMmss(sec) { const n = Math.floor(sec + 0.5); return rtmPad(Math.floor(n / 60)) + ':' + rtmPad(n % 60); }
/* La vitesse commune des branches libres d'un tronçon (rangs free) multipliée par f, en km/h ; null si elles n'ont pas toutes la même vitesse */
function rtmCommon(tm, free, f) {
  let v = null;
  for (let k = 0; k < free.length; k++) {
    const w = tm.legs[free[k]].v;
    if (v === null) v = w; else if (w !== v) return null;
  }
  return v === null ? null : v * f;
}
/* Les branches libres d'un tronçon (a → b) : toutes celles qui ne sont pas verrouillées */
function rtmFree(tm, a, b) { const out = []; for (let j = a + 1; j <= b; j++) if (!tm.legs[j].lock) out.push(j); return out; }
/* Le texte d'un message à partir de son modèle : les variables, l'élision « d’ » devant une voyelle ou un h en français (une fonction : aucun « $ » d'un nom n'est interprété), « () » sans vitesse commune retiré ;
   head : le premier membre, jusqu'au premier « : » qui suit les heures marks (l'une après l'autre : une heure porte elle-même des « : ») */
function rtmFinish(text, vars, o, marks) {
  if (o.fr) {
    const ap = ' de ' + vars.a + ' à ';
    if (/^[aeiouàâäéèêëîïôöùûüœæh]/i.test(vars.a)) text = text.replace(ap, () => ' d’' + vars.a + ' à ');
  }
  text = text.replace(' ()', '');
  let from = 0;
  marks.forEach(m => { from = Math.max(0, text.indexOf(m, from)) + m.length; });
  const c = text.slice(from).search(/ ?:/);
  return { text: text, head: c < 0 ? '' : text.slice(0, from + c), n: vars.n };
}
/* Le message d'un tronçon intenable (sa cause dit pourquoi) : { text, head (le premier membre, avant « : »), n (le pourcentage, '' sans) } ; o : { t (le dictionnaire), speedText (km/h → texte dans l'unité affichée), fr, name (i → nom du point), margin } */
function rtmRedMsg(points, tm, i, o) {
  const r = tm.red[i], a = r.a;
  const nm = k => { const s = o.name(k); return typeof s === 'string' && s.trim() !== '' ? s.trim() : String(k); };
  const rr = rtmClock(rtmSecs(points[a].t) + r.actuel);
  const vars = { p: nm(i), h: rtmClock(tm.t[i]), a: nm(a), b: nm(i), r: rr, n: '', v: '', m: String(rtmMargin(o.margin)), d: '' };
  let key = 't.red.0';
  if (r.why === 'm') {
    key = 't.red.m'; vars.n = rtmPct(r.f, o.fr);
    const v = rtmCommon(tm, rtmFree(tm, a, i), r.f);
    if (v !== null) vars.v = o.speedText(v);
  } else if (r.why === 'lk') key = 't.red.lk';
  else if (r.why === 'lt') { key = 't.red.lt'; vars.d = rtmMmss(r.L); }
  return rtmFinish(o.t(key, vars), vars, o, [vars.h]);
}
/* Le message d'un tronçon orange (b = i) : « Heures verrouillées {a} {ha} → {b} {hb} : tenues à {n} ({v}) sur les {k} branches, dans la marge ±{m} % » ; une seule branche libre : « sur la branche » (t.amb.1) */
function rtmAmbMsg(points, tm, i, o) {
  const r = tm.amb[i], a = r.a;
  const nm = k => { const s = o.name(k); return typeof s === 'string' && s.trim() !== '' ? s.trim() : String(k); };
  const vars = { a: nm(a), b: nm(i), ha: rtmClock(tm.t[a]), hb: rtmClock(tm.t[i]), n: rtmPct(r.f, o.fr), v: '', k: String(r.free.length), m: String(rtmMargin(o.margin)) };
  const v = rtmCommon(tm, r.free, r.f);
  if (v !== null) vars.v = o.speedText(v);
  return rtmFinish(o.t(r.free.length === 1 ? 't.amb.1' : 't.amb', vars), vars, o, [vars.ha, vars.hb]);
}
/* Le message d'un tronçon orange au Datacard Generator (aucune vitesse) : « {p} à {h} : à tenir par les vitesses de {a} à {b} ({n}) ; appliquez-les au Route Planner. » */
function rtmAmbDgMsg(points, tm, i, o) {
  const r = tm.amb[i], a = r.a;
  const nm = k => { const s = o.name(k); return typeof s === 'string' && s.trim() !== '' ? s.trim() : String(k); };
  const vars = { p: nm(i), h: rtmClock(tm.t[i]), a: nm(a), b: nm(i), n: rtmPct(r.f, o.fr) };
  return rtmFinish(o.t('t.amb.dg', vars), vars, o, [vars.h]);
}
/* L'étiquette d'une branche libre d'un tronçon orange : « → 240 km/h (+9 %) » ; '' pour une autre branche */
function rtmLegLabel(tm, j, o) {
  const l = tm.legs[j];
  if (!l || l.amb === undefined) return '';
  return o.t('t.leg', { v: o.speedText(l.rec), n: rtmPct(tm.amb[l.amb].f, o.fr) });
}
/* Le message en HTML : le premier membre et le pourcentage en gras ; esc : l'échappement de l'outil */
function rtmRedHtml(m, esc) {
  const h = m.head, rest = m.text.slice(h.length);
  const j = m.n !== '' ? rest.indexOf(m.n) : -1;
  const tail = j < 0 ? esc(rest) : esc(rest.slice(0, j)) + '<b>' + esc(m.n) + '</b>' + esc(rest.slice(j + m.n.length));
  return (h !== '' ? '<b>' + esc(h) + '</b>' : '') + tail;
}
"""


def build_block():
    """Le texte du bloc, délimité par ses deux commentaires, terminé par un saut de ligne."""
    return BLOCK_BEGIN + _JS + BLOCK_END + '\n'


if __name__ == '__main__':
    txt = build_block()
    print(f"[OK] bloc des heures d'une route : {len(txt)} caractères")
