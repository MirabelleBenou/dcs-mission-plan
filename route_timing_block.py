#!/usr/bin/env python3
"""Bloc « HEURES D'UNE ROUTE » : le calcul des heures réelles d'une route, ses heures fixes, ses tronçons intenables ; une seule source pour le Route Planner et le Datacard Generator.

Injecté tel quel (identique à l'octet) dans les deux outils. Des fonctions pures, sans état de l'écran ni DOM : elles prennent les points d'une route
(lat, lon, gs, t, tLock) et la vitesse par défaut, et rendent les temps.

Les heures vivent sur les points : p.t (« HH:MM:SS », dans la référence de la datacard, sans fuseau) et p.tLock (true, seulement avec un p.t valide).
Les heures fixes sont les points verrouillés et le pivot (le seul point qui porte p.t sans verrou). Une route a des heures dès qu'un point porte p.t ;
sans heure fixe, rien ne change : le temps écoulé.

La distance d'une branche est celle de legCalc des deux outils (haversine, mêmes opérations dans le même ordre, même rayon) : sans heure, les chiffres sont ceux d'avant.

Usage (par les builds) : from route_timing_block import build_block ; texte = build_block()
"""

BLOCK_BEGIN = '/* ===== HEURES D\'UNE ROUTE (calcul, heures fixes, tronçons intenables) ===== */'
BLOCK_END = '/* ===== FIN DES HEURES D\'UNE ROUTE ===== */'

_JS = r"""
const RTM_R_KM = 6371.0088, RTM_DAY = 86400, RTM_TOL = 5;

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
/* Distance (km) d'une branche : la formule de legCalc */
function rtmKm(a, b) {
  const r = Math.PI / 180;
  const p1 = a.lat * r, p2 = b.lat * r, dl = (b.lon - a.lon) * r;
  const h = Math.sin((p2 - p1) / 2) * Math.sin((p2 - p1) / 2) + Math.cos(p1) * Math.cos(p2) * Math.sin(dl / 2) * Math.sin(dl / 2);
  return 2 * RTM_R_KM * Math.asin(Math.min(1, Math.sqrt(h)));
}
/* Les temps d'une route : { n, legs (par branche : km, v, sec), el (temps écoulé non arrondi), km, sec, has (une heure fixe au moins), fixed, lock, t (secondes non arrondies, ou null sans heure), red }.
   red[i] : null, ou { a, besoin, actuel, f } quand l'heure fixe du point i ne tient pas à 5 s près depuis la fixe qui la précède (f : actuel / besoin, null si besoin = 0) */
function rtmCompute(points, gsDefault) {
  const n = points.length, legs = [null], el = [0];
  let km = 0, sec = 0;
  for (let i = 1; i < n; i++) {
    const k = rtmKm(points[i - 1], points[i]);
    const p = points[i], v = (typeof p.gs === 'number' && p.gs > 0) ? p.gs : gsDefault;
    const sc = k / v * 3600;
    legs.push({ km: k, v: v, sec: sc });
    km += k; sec += sc;
    el.push(sec);
  }
  const fixed = [], lock = [], t = [], red = [], F = [];
  for (let i = 0; i < n; i++) {
    const ok = rtmValid(points[i].t);
    fixed.push(ok); lock.push(ok && points[i].tLock === true); t.push(null); red.push(null);
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
      for (let i = a; i < b; i++) t[i] = T(a) + (el[i] - el[a]);
      if (Math.abs(actuel - besoin) > RTM_TOL) red[b] = { a: a, besoin: besoin, actuel: actuel, f: besoin > 0 ? actuel / besoin : null };
    }
    F.forEach(i => { t[i] = T(i); });
  }
  return { n: n, legs: legs, el: el, km: km, sec: sec, has: F.length > 0, fixed: fixed, lock: lock, t: t, red: red };
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
/* Le message d'un tronçon intenable : { text, head (le premier membre, avant « : »), n (le pourcentage, '' sans) } ; o : { t (le dictionnaire), speedText (km/h → texte dans l'unité affichée), fr, name (i → nom du point) } */
function rtmRedMsg(points, tm, i, o) {
  const r = tm.red[i], a = r.a;
  const nm = k => { const s = o.name(k); return typeof s === 'string' && s.trim() !== '' ? s.trim() : String(k); };
  const rr = rtmClock(rtmSecs(points[a].t) + r.actuel);
  const vars = { p: nm(i), h: rtmClock(tm.t[i]), a: nm(a), b: nm(i), r: rr, n: '', v: '' };
  let key = 't.red.0';
  if (r.f !== null) {
    vars.n = rtmPct(r.f, o.fr);
    let same = true;
    for (let k = a + 2; k <= i; k++) if (tm.legs[k].v !== tm.legs[a + 1].v) same = false;
    if (same) { key = 't.red'; vars.v = o.speedText(tm.legs[a + 1].v * r.f); } else key = 't.red.nv';
  }
  let text = o.t(key, vars);
  if (o.fr) {
    const ap = ' de ' + vars.a + ' à ';
    if (/^[aeiouyàâäéèêëîïôöùûüœæh]/i.test(vars.a)) text = text.replace(ap, ' d’' + vars.a + ' à ');
  }
  const from = Math.max(0, text.indexOf(vars.h)) + vars.h.length, c = text.slice(from).search(/\u202f?:/);       /* le premier « : » après l'heure du message (l'heure en porte elle-même) */
  return { text: text, head: c < 0 ? '' : text.slice(0, from + c), n: vars.n };
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
