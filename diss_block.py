#!/usr/bin/env python3
"""Bloc « VALEURS DU DISS-15 » : une seule source pour le Route Planner et le Datacard Generator.

Le DISS-15 du Mi-24P et du Mi-8MTV2 compte, depuis un point 000 (le premier point), l'avance et l'écart latéral en km dans le repère d'un nord. DCS intègre
dans sa grille (x au nord, y à l'est) : le calcul se fait sur la grille (llToDcs), jamais par cap et distance géodésiques. Le nord est celui de la grille pour le
Mi-24P (et sans type), le nord magnétique du premier point pour le Mi-8MTV2 ; l'angle de carte est toujours 000.

Le texte JavaScript exige llToDcs, TM_PARAMS et magVar déjà présents dans la page qui l'insère (le Datacard Generator les a par projection_block.py et
magvar_block.py ; le Route Planner a sa propre copie de llToDcs, identique). Les deux builds insèrent ce texte tel quel, à un repère @@DISS_BLOCK@@ : le bloc est
identique à l'octet dans les deux fichiers de dist/.

Usage (par les builds) : from diss_block import build_block, verify ; texte = build_block() ; verify(js, 'Datacard Generator')
"""

BLOCK_BEGIN = '/* ===== VALEURS DU DISS-15 (Mi-24P, Mi-8MTV2) ===== */'
BLOCK_END = '/* ===== FIN DES VALEURS DU DISS-15 ===== */'

_JS = r"""
/* Les valeurs du DISS-15 du point p depuis l'origine o (le point 000, premier point de la route) :
   { fwd, right } en km, fwd > 0 en avant, right > 0 à droite.
   rot : le nord de l'axe « avant » de l'appareil quand l'angle de carte vaut 000, en degrés depuis le nord de la grille
   de DCS, + vers l'Est : 0 si le cap de l'appareil est le cap grille (Mi-24P, KM-2 réglé), la déclinaison au point 000
   s'il est magnétique (Mi-8MTV2). A : l'angle de carte (0 par défaut). Les écarts se prennent sur la grille de DCS
   (llToDcs : x au nord, y à l'est), jamais sur le cap géodésique. */
function dissXY(theatre, o, p, rot, A) {
  const a = llToDcs(theatre, o.lat, o.lon), b = llToDcs(theatre, p.lat, p.lon);
  const dx = (b.x - a.x) / 1000, dy = (b.y - a.y) / 1000;
  const r = ((rot || 0) + (A || 0)) * Math.PI / 180;
  return { fwd: dx * Math.cos(r) + dy * Math.sin(r), right: -dx * Math.sin(r) + dy * Math.cos(r), dx: dx, dy: dy };
}
/* Au dixième de km, la moitié s'éloigne de zéro ; le côté se lit sur la valeur arrondie (aucun côté pour 0,0) */
function dissRound(v) { const r = Math.round(Math.abs(v) * 10) / 10; return v < 0 ? -r : r; }

/* Le nord de l'appareil : 'grid' (Mi-24P, et type vide), 'mag' (Mi-8MT, Mi-8MTV2), null (tout autre type : pas de DISS-15) ;
   le type se compare rogné, sans la casse */
function dissKind(type) {
  const s = typeof type === 'string' ? type.trim().toLowerCase() : '';
  if (s === '' || s === 'mi-24p') return 'grid';
  if (s === 'mi-8mt' || s === 'mi-8mtv2') return 'mag';
  return null;
}
/* Le théâtre a une grille de DCS : ses paramètres sont dans TM_PARAMS (ni Iraq, ni Afghanistan, ni MarianaIslandsWWII) */
function dissTheatreOk(th) { return typeof th === 'string' && Object.prototype.hasOwnProperty.call(TM_PARAMS, th); }
/* D0, la déclinaison (°, + vers l'Est) au premier point : la valeur saisie quand le cap magnétique est en Saisie et lisible (manual : un nombre, sinon null) ;
   sinon (cap vrai, ou magnétique calculée) la déclinaison du modèle à l'année y (décimale : magYearSource(...).y), comme le reste de la navigation */
function dissD0(lat, lon, manual, y) { return typeof manual === 'number' && isFinite(manual) ? manual : magVar(lat, lon, y); }
/* Le nord de l'axe « avant » pour l'appareil : 0 (nord de la grille) ou D0 (nord magnétique) */
function dissRot(kind, d0) { return kind === 'mag' ? d0 : 0; }
/* Le texte d'une valeur, le seul endroit où il s'écrit : « AV 52,8 », « AR 3,0 », « G 48,3 », « D 2,1 » (EN : FWD, AFT, L, R ; point décimal) ; « 0,0 » sans côté.
   axis : 'fwd' (avant, arrière) ou 'right' (droite, gauche) ; lang : 'fr' ou 'en' */
function dissText(v, axis, lang) {
  const fr = lang === 'fr', r = dissRound(v), n = Math.abs(r).toFixed(1), num = fr ? n.replace('.', ',') : n;
  if (r === 0) return num;
  const side = axis === 'fwd' ? (r > 0 ? (fr ? 'AV' : 'FWD') : (fr ? 'AR' : 'AFT')) : (r > 0 ? (fr ? 'D' : 'R') : (fr ? 'G' : 'L'));
  return side + ' ' + num;
}
/* Les deux textes d'un point p depuis l'origine o : { fwd, right } ; rot et lang comme ci-dessus ; angle de carte 000 */
function dissCells(theatre, o, p, rot, lang) {
  const d = dissXY(theatre, o, p, rot, 0);
  return { fwd: dissText(d.fwd, 'fwd', lang), right: dissText(d.right, 'right', lang) };
}
/* Les textes de chaque point de pts (des { lat, lon } ou null : un point sans position) ; l'origine est le premier ; sans position à l'origine, rien nulle part */
function dissRows(theatre, pts, rot, lang) {
  const o = pts.length ? pts[0] : null;
  return pts.map(p => (o && p) ? dissCells(theatre, o, p, rot, lang) : null);
}
"""

# Les noms que le texte du bloc exige de la page qui l'insère
REQUIRES = ('llToDcs', 'TM_PARAMS', 'magVar')


def build_block():
    """Le texte du bloc, délimité par ses deux commentaires, sans saut de ligne final."""
    return BLOCK_BEGIN + _JS + BLOCK_END + '\n'


def verify(js, who):
    """Le bloc est dans le script de la page, tel quel et une seule fois ; ses trois prérequis y sont ; aucun repère @@DISS_BLOCK@@ ne reste."""
    blk = build_block()
    if js.count(BLOCK_BEGIN) != 1 or js.count(BLOCK_END) != 1 or js.count(blk) != 1:
        raise SystemExit("[ERREUR] %s : le bloc des valeurs du DISS-15 n'est pas inséré tel quel, une seule fois" % who)
    if '@@DISS_BLOCK@@' in js:
        raise SystemExit("[ERREUR] %s : le repère @@DISS_BLOCK@@ n'a pas été remplacé" % who)
    for name in REQUIRES:
        if ('function %s(' % name) not in js and ('const %s = ' % name) not in js:
            raise SystemExit("[ERREUR] %s : %s manque à la page, le bloc du DISS-15 en a besoin" % (who, name))
    print("[OK] %s : bloc des valeurs du DISS-15 inséré tel quel, une seule fois (%d caractères)" % (who, len(blk)))


if __name__ == '__main__':
    print("[OK] bloc du DISS-15 : %d caractères" % len(build_block()))
