#!/usr/bin/env python3
"""Bloc « TRAIT À MAIN LEVÉE » : la simplification d'un trait dessiné à main levée sur la carte ; le Route Planner seul.

Une fonction pure, sans état de l'écran ni DOM : elle prend les points [x, y] du trait (en pixels) et rend les indices gardés (Douglas-Peucker).
  · le premier et le dernier point sont gardés ; entre deux points gardés a et b, le point de plus grande distance au SEGMENT [a, b] (pas à la droite) est gardé si cette distance dépasse
    strictement la tolérance, et l'on recommence de part et d'autre ; à égalité, le premier de l'ordre du trait ;
  · tolérance de 2 px ; s'il reste plus de 500 sommets, la tolérance double (4, 8…) jusqu'à 500 au plus ;
  · deux points consécutifs égaux comptent pour un (le premier de la série est celui qui est gardé).

Usage (par le build) : from route_freehand_block import build_block ; texte = build_block()
"""

BLOCK_BEGIN = '/* ===== TRAIT À MAIN LEVÉE (simplification, Douglas-Peucker) ===== */'
BLOCK_END = '/* ===== FIN DU TRAIT À MAIN LEVÉE ===== */'

_JS = r"""
const RFH_TOL = 2, RFH_MAX = 500, RFH_TAP_PX = 8;

/* La distance du point p au segment [a, b] (au segment, pas à la droite) ; un segment réduit à un point : la distance à ce point */
function rfhSegDist(p, a, b) {
  const dx = b[0] - a[0], dy = b[1] - a[1], l2 = dx * dx + dy * dy;
  let u = l2 ? ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / l2 : 0;
  u = Math.max(0, Math.min(1, u));
  return Math.hypot(p[0] - (a[0] + u * dx), p[1] - (a[1] + u * dy));
}
/* Les indices des points, deux points consécutifs égaux comptant pour un (le premier de la série) */
function rfhDistinct(pts) {
  const out = [];
  for (let i = 0; i < pts.length; i++) {
    if (!out.length || pts[i][0] !== pts[out[out.length - 1]][0] || pts[i][1] !== pts[out[out.length - 1]][1]) out.push(i);
  }
  return out;
}
/* Douglas-Peucker à la tolérance tol : les indices gardés (croissants) de pts */
function rfhSimplify(pts, tol) {
  const d = rfhDistinct(pts), n = d.length;
  if (n <= 2) return d;
  const keep = new Array(n).fill(false);
  keep[0] = true; keep[n - 1] = true;
  const stack = [[0, n - 1]];
  while (stack.length) {
    const r = stack.pop(), lo = r[0], hi = r[1];
    if (hi - lo < 2) continue;
    let best = -1, bd = tol;                      /* strictement au-delà de la tolérance ; à égalité de distance, le premier de l'ordre du trait */
    for (let i = lo + 1; i < hi; i++) {
      const dist = rfhSegDist(pts[d[i]], pts[d[lo]], pts[d[hi]]);
      if (dist > bd) { bd = dist; best = i; }
    }
    if (best < 0) continue;
    keep[best] = true;
    stack.push([lo, best], [best, hi]);
  }
  const out = [];
  for (let i = 0; i < n; i++) if (keep[i]) out.push(d[i]);
  return out;
}
/* Le trait rendu : { idx: les indices gardés, tol: la tolérance finale } ; plus de 500 sommets à 2 px : la tolérance double jusqu'à 500 au plus */
function rfhStroke(pts) {
  let tol = RFH_TOL, idx = rfhSimplify(pts, tol);
  while (idx.length > RFH_MAX) { tol *= 2; idx = rfhSimplify(pts, tol); }
  return { idx: idx, tol: tol };
}
/* Le plus grand écart du trait à son point de départ (pixels) : sous RFH_TAP_PX, c'est un toucher */
function rfhReach(pts) {
  let m = 0;
  for (let i = 1; i < pts.length; i++) m = Math.max(m, Math.hypot(pts[i][0] - pts[0][0], pts[i][1] - pts[0][1]));
  return m;
}
"""


def build_block():
    """Le texte du bloc, délimité par ses deux commentaires, terminé par un saut de ligne."""
    return BLOCK_BEGIN + _JS + BLOCK_END + '\n'


if __name__ == '__main__':
    txt = build_block()
    print(f"[OK] bloc du trait à main levée : {len(txt)} caractères")
