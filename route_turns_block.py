#!/usr/bin/env python3
"""Bloc « VIRAGES D'UNE ROUTE » : le rayon et l'anticipation de chaque virage d'une route, d'après la vitesse sol de la branche qui arrive et l'inclinaison choisie ; le Route Planner seul.

Une fonction pure, sans état de l'écran ni DOM : elle prend les points (lat, lon), la vitesse sol (km/h) de la branche qui arrive à chaque point et l'inclinaison (0, 15, 30 ou 45 degrés),
et rend, pour chaque point intermédiaire, l'angle signé du virage, son rayon et son anticipation au sol, s'il tient sur ses deux branches, et les extrémités et le centre de son arc.

La géométrie se fait dans la projection de la carte, la sphérique de Mercator d'EPSG:3857 (rayon 6 378 137 m, celle de L.CRS.EPSG3857) : les branches y sont des droites ; au point i, un mètre au sol
vaut k = 1 / cos(lat) mètres projetés. Le rayon au sol est R = v² / (g · tan φ), l'anticipation au sol d = R · tan(|Δ| / 2).

Usage (par le build) : from route_turns_block import build_block ; texte = build_block()
"""

BLOCK_BEGIN = '/* ===== VIRAGES D\'UNE ROUTE (rayon, anticipation, arc) ===== */'
BLOCK_END = '/* ===== FIN DES VIRAGES D\'UNE ROUTE ===== */'

_JS = r"""
const RTN_R = 6378137, RTN_G = 9.80665, RTN_BANKS = [0, 15, 30, 45];
const RTN_NONE_DEG = 1, RTN_UTURN_DEG = 179, RTN_ARC_STEP_DEG = 3, RTN_ARC_MIN_SEG = 4;

/* L'inclinaison d'une route lue : 0 (Aucun), 15, 30 ou 45 ; toute autre valeur donne 0 */
function rtnBank(x) { return RTN_BANKS.indexOf(x) !== -1 ? x : 0; }
/* lat, lon (degrés) → x, y projetés (mètres) de la sphérique de Mercator d'EPSG:3857 */
function rtnMerc(lat, lon) {
  const r = Math.PI / 180;
  return { x: RTN_R * lon * r, y: RTN_R * Math.log(Math.tan(Math.PI / 4 + lat * r / 2)) };
}
/* x, y projetés → [lat, lon] (degrés) */
function rtnInv(x, y) { return [(2 * Math.atan(Math.exp(y / RTN_R)) - Math.PI / 2) * 180 / Math.PI, x / RTN_R * 180 / Math.PI]; }
/* Les virages d'une route : un élément par point (null au premier, au dernier et sans inclinaison) ;
   { i, delta (degrés, signé : positif à gauche), side ('left' | 'right'), turn (|Δ| ≥ 1°), v (m/s), R, d (mètres au sol), k, fits, wide (turn et pas fits),
     uturn (|Δ| ≥ 179° : un demi-tour), t1, t2, c ([lat, lon] ; null si wide ou pas de virage), a0, sweep (radians, dans le plan projeté), rk (rayon projeté) } ;
   speeds[i] : la vitesse sol (km/h) de la branche qui arrive au point i. Un demi-tour est trop large d'office, sans rayon ni anticipation (R et d valent 0) : il compte 0 dans la somme des anticipations de ses deux branches. */
function rtnCompute(points, speeds, bank) {
  const n = points.length, out = new Array(n).fill(null), phi = rtnBank(bank);
  if (phi === 0 || n < 3) return out;
  const P = points.map(p => rtnMerc(p.lat, p.lon));
  const len = [0];
  for (let j = 1; j < n; j++) len.push(Math.hypot(P[j].x - P[j - 1].x, P[j].y - P[j - 1].y));
  for (let i = 1; i < n - 1; i++) {
    const v = speeds[i] / 3.6, k = 1 / Math.cos(points[i].lat * Math.PI / 180);
    const o = { i: i, delta: 0, side: '', turn: false, v: v, R: 0, d: 0, k: k, fits: true, wide: false, uturn: false, t1: null, t2: null, c: null, a0: 0, sweep: 0, rk: 0 };
    out[i] = o;
    if (!(len[i] > 0) || !(len[i + 1] > 0) || !isFinite(v) || !(v > 0)) continue;
    const u1 = { x: (P[i].x - P[i - 1].x) / len[i], y: (P[i].y - P[i - 1].y) / len[i] };
    const u2 = { x: (P[i + 1].x - P[i].x) / len[i + 1], y: (P[i + 1].y - P[i].y) / len[i + 1] };
    const dl = Math.atan2(u1.x * u2.y - u1.y * u2.x, u1.x * u2.x + u1.y * u2.y);
    o.delta = dl * 180 / Math.PI;
    const a = Math.abs(o.delta);
    if (a < RTN_NONE_DEG) continue;
    o.turn = true;
    if (a >= RTN_UTURN_DEG) { o.uturn = true; o.fits = false; continue; }
    o.side = dl > 0 ? 'left' : 'right';
    o.R = v * v / (RTN_G * Math.tan(phi * Math.PI / 180));
    o.d = o.R * Math.tan(a * Math.PI / 360);
  }
  /* une branche déborde quand les anticipations de ses deux bouts (projetées) dépassent sa longueur : les virages de ses deux bouts sont trop larges */
  for (let j = 1; j < n; j++) {
    const a = out[j - 1], b = out[j];
    const da = a && a.turn ? a.d * a.k : 0, db = b && b.turn ? b.d * b.k : 0;
    if (da + db > len[j]) { if (a && a.turn) a.fits = false; if (b && b.turn) b.fits = false; }
  }
  for (let i = 1; i < n - 1; i++) {
    const o = out[i];
    if (!o.turn) continue;
    o.wide = !o.fits;
    if (o.wide) continue;
    const dk = o.d * o.k;
    const u1 = { x: (P[i].x - P[i - 1].x) / len[i], y: (P[i].y - P[i - 1].y) / len[i] };
    const u2 = { x: (P[i + 1].x - P[i].x) / len[i + 1], y: (P[i + 1].y - P[i].y) / len[i + 1] };
    const T1 = { x: P[i].x - u1.x * dk, y: P[i].y - u1.y * dk }, T2 = { x: P[i].x + u2.x * dk, y: P[i].y + u2.y * dk };
    const nx = o.side === 'left' ? -u1.y : u1.y, ny = o.side === 'left' ? u1.x : -u1.x;
    o.rk = o.R * o.k;
    const C = { x: T1.x + nx * o.rk, y: T1.y + ny * o.rk };
    o.a0 = Math.atan2(T1.y - C.y, T1.x - C.x);
    o.sweep = o.delta * Math.PI / 180;
    o.t1 = rtnInv(T1.x, T1.y); o.t2 = rtnInv(T2.x, T2.y); o.c = rtnInv(C.x, C.y);
    o.cx = C.x; o.cy = C.y;
  }
  return out;
}
/* L'arc d'un virage qui tient : une suite de [lat, lon] de T1 à T2, un segment tous les 3° au plus (quatre au moins) */
function rtnArc(o) {
  if (!o || !o.turn || o.wide || !o.t1) return [];
  const a = Math.abs(o.delta), m = Math.max(RTN_ARC_MIN_SEG, Math.ceil(a / RTN_ARC_STEP_DEG - 1e-9)), pts = [];
  for (let s = 0; s <= m; s++) {
    if (s === 0) { pts.push(o.t1.slice()); continue; }
    if (s === m) { pts.push(o.t2.slice()); continue; }
    const ang = o.a0 + o.sweep * s / m;
    pts.push(rtnInv(o.cx + o.rk * Math.cos(ang), o.cy + o.rk * Math.sin(ang)));
  }
  return pts;
}
"""


def build_block():
    """Le texte du bloc, délimité par ses deux commentaires, terminé par un saut de ligne."""
    return BLOCK_BEGIN + _JS + BLOCK_END + '\n'


if __name__ == '__main__':
    txt = build_block()
    print(f"[OK] bloc des virages d'une route : {len(txt)} caractères")
