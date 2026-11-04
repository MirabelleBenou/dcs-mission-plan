#!/usr/bin/env python3
"""Bloc « PROJECTIONS DE DCS » : TM_PARAMS, llToDcs et dcsToLl, une seule source pour les outils qui lisent des coordonnées de mission.

Le texte JavaScript est recopié, au caractère près, du Route Planner (build_route_planner.py) ; il s'appuie sur les constantes UTM_* du
bloc de coordonnées partagé (WGS84, série de Krüger), déjà présent dans la page qui l'insère. Le Datacard Generator l'inclut par son build ;
le Route Planner garde pour l'instant son propre texte, identique (l'inclure ici viendra plus tard).

Usage (par les builds) : from projection_block import build_block ; texte = build_block()
"""

BLOCK_BEGIN = '/* ===== PROJECTIONS DE DCS (Mercator transverse, un jeu de paramètres par théâtre) ===== */'
BLOCK_END = '/* ===== FIN DES PROJECTIONS DE DCS ===== */'

_JS = r"""
/* Les projections de DCS, une par théâtre (pydcs, LGPL-3.0) : Mercator transverse WGS84, échelle 0,9996, latitude d'origine 0 ;
   [ méridien central (°), faux est (m), faux nord (m) ]. DCS pose x au nord, y à l'est. Ni MarianaIslandsWWII, ni Iraq, ni Afghanistan. */
const TM_PARAMS = {
  Caucasus:       [33,   -99516.9999999732,     -4998114.999999984],
  Falklands:      [-57,  147639.99999997593,    5815417.000000032],
  GermanyCW:      [21,   35427.619999985734,    -6061633.128000011],
  Kola:           [21,   -62702.00000000087,    -7543624.999999979],
  MarianaIslands: [147,  238417.99999989968,    -1491840.000000048],
  Nevada:         [-117, -193996.80999964548,   -4410028.063999966],
  Normandy:       [-3,   -195526.00000000204,   -5484812.999999951],
  PersianGulf:    [57,   75755.99999999645,     -2894933.0000000377],
  SinaiMap:       [33,   169221.9999999585,     -3325312.9999999693],
  Syria:          [39,   282801.00000003993,    -3879865.9999999935],
  TheChannel:     [3,    99376.00000000288,     -5636889.00000001]
};

/* Mercator transverse du théâtre (série de Krüger du bloc de coordonnées) : x est le nord, y l'est, avec les faux de pydcs.
   lat/lon (degrés) → { x, y } (mètres) */
function llToDcs(theatre, lat, lon) {
  const p = TM_PARAMS[theatre];
  let d = lon - p[0];
  while (d > 180) d -= 360;
  while (d < -180) d += 360;
  const phi = lat * Math.PI / 180, dl = d * Math.PI / 180;
  const n = UTM_N, s = Math.sin(phi);
  const q = 2 * Math.sqrt(n) / (1 + n);
  const tt = Math.sinh(Math.atanh(s) - q * Math.atanh(q * s));
  const xi0 = Math.atan2(tt, Math.cos(dl));
  const eta0 = Math.atanh(Math.sin(dl) / Math.sqrt(1 + tt * tt));
  let xi = xi0, eta = eta0;
  for (let j = 1; j <= 4; j++) {
    xi += UTM_ALPHA[j - 1] * Math.sin(2 * j * xi0) * Math.cosh(2 * j * eta0);
    eta += UTM_ALPHA[j - 1] * Math.cos(2 * j * xi0) * Math.sinh(2 * j * eta0);
  }
  return { x: UTM_K0 * UTM_A * xi + p[2], y: UTM_K0 * UTM_A * eta + p[1] };
}

/* { x, y } (mètres DCS) → lat/lon (degrés) */
function dcsToLl(theatre, x, y) {
  const p = TM_PARAMS[theatre];
  const xi = (x - p[2]) / (UTM_K0 * UTM_A);
  const eta = (y - p[1]) / (UTM_K0 * UTM_A);
  let xi1 = xi, eta1 = eta;
  for (let j = 1; j <= 4; j++) {
    xi1 -= UTM_BETA[j - 1] * Math.sin(2 * j * xi) * Math.cosh(2 * j * eta);
    eta1 -= UTM_BETA[j - 1] * Math.cos(2 * j * xi) * Math.sinh(2 * j * eta);
  }
  const chi = Math.asin(Math.sin(xi1) / Math.cosh(eta1));
  let phi = chi;
  for (let j = 1; j <= 4; j++) phi += UTM_DELTA[j - 1] * Math.sin(2 * j * chi);
  let lon = p[0] + Math.atan2(Math.sinh(eta1), Math.cos(xi1)) * 180 / Math.PI;
  while (lon > 180) lon -= 360;
  while (lon < -180) lon += 360;
  return { lat: phi * 180 / Math.PI, lon: lon };
}
"""


def build_block():
    """Le texte du bloc, délimité par ses deux commentaires, terminé par un saut de ligne."""
    return BLOCK_BEGIN + _JS + BLOCK_END + '\n'


if __name__ == '__main__':
    txt = build_block()
    print(f"[OK] bloc de projections : {len(txt)} caractères")
