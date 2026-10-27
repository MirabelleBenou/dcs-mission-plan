#!/usr/bin/env python3
"""Bloc « DÉCLINAISON MAGNÉTIQUE (WMM, comme DCS) » — une seule source pour le Route Planner et le Datacard Generator.

Lit les coefficients du World Magnetic Model (NOAA NCEI / British Geological Survey, domaine public ; les époques
1985 à 2025 que DCS World embarque) dans le dossier wmm/ à la racine du dépôt, et rend le texte JavaScript du bloc :
la table compacte des coefficients et les fonctions magDecYear, magEpoch, magVar et magYearSource.
Les deux builds insèrent ce texte tel quel : le bloc est identique à l'octet dans les deux fichiers de dist/.

Usage (par les builds) : from magvar_block import build_block ; texte = build_block()
"""

import glob
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
WMM_DIR = os.path.join(HERE, 'wmm')

BLOCK_BEGIN = '/* ===== DÉCLINAISON MAGNÉTIQUE (WMM, comme DCS) ===== */'
BLOCK_END = '/* ===== FIN DE LA DÉCLINAISON MAGNÉTIQUE ===== */'

DEGREE = 12                      # degré maximal du modèle (n = 1 … 12 : 90 lignes par fichier)
EPOCHS = list(range(1985, 2026, 5))


def _b36(n):
    """Entier relatif → base 36 (signe moins devant)."""
    if n == 0:
        return '0'
    digits = '0123456789abcdefghijklmnopqrstuvwxyz'
    s, a = '', abs(n)
    while a:
        a, r = divmod(a, 36)
        s = digits[r] + s
    return ('-' if n < 0 else '') + s


def _read_epoch(path, year):
    """Un fichier .COF → liste de 360 entiers (dixièmes : g, h, ġ, ḣ pour chaque (n, m) dans l'ordre du fichier)."""
    name = os.path.basename(path)
    try:
        with open(path, encoding='utf-8', newline=None) as f:
            lines = f.read().split('\n')
    except (OSError, UnicodeDecodeError) as e:
        raise SystemExit(f"[ERREUR] wmm/{name} : illisible ({e})")
    if not lines or not lines[0].strip():
        raise SystemExit(f"[ERREUR] wmm/{name} : en-tête absent")
    head = lines[0].split()
    try:
        epoch = float(head[0])
    except (ValueError, IndexError):
        raise SystemExit(f"[ERREUR] wmm/{name} : l'en-tête ne commence pas par l'époque : {lines[0]!r}")
    if epoch != float(year):
        raise SystemExit(f"[ERREUR] wmm/{name} : l'époque de l'en-tête ({epoch}) n'est pas {year}.0")
    expect = [(n, m) for n in range(1, DEGREE + 1) for m in range(0, n + 1)]
    vals = []
    k = 0
    for raw in lines[1:]:
        s = raw.strip()
        if not s or s.startswith('9999'):
            continue
        parts = s.split()
        if len(parts) != 6:
            raise SystemExit(f"[ERREUR] wmm/{name} : ligne illisible (6 champs attendus) : {raw!r}")
        try:
            n, m = int(parts[0]), int(parts[1])
            nums = [float(x) for x in parts[2:]]
        except ValueError:
            raise SystemExit(f"[ERREUR] wmm/{name} : ligne illisible : {raw!r}")
        if k >= len(expect) or (n, m) != expect[k]:
            raise SystemExit(f"[ERREUR] wmm/{name} : terme (n, m) inattendu ({n}, {m}) à la ligne {k + 1} des coefficients")
        for x in nums:
            t = round(x * 10)
            if abs(x * 10 - t) > 1e-6:
                raise SystemExit(f"[ERREUR] wmm/{name} : valeur à plus d'une décimale : {x} (terme {n}, {m})")
            vals.append(int(t))
        k += 1
    if k != len(expect):
        raise SystemExit(f"[ERREUR] wmm/{name} : {k} lignes de coefficients au lieu de {len(expect)}")
    return vals


def build_table():
    """La table compacte : { année : 'jetons en base 36, séparés par une espace' } ; 4 jetons par terme (g h ġ ḣ), en dixièmes."""
    if not os.path.isdir(WMM_DIR):
        raise SystemExit(f"[ERREUR] Dossier manquant : {WMM_DIR} (wmm/ attendu à la racine du dépôt)")
    rows = []
    for y in EPOCHS:
        p = os.path.join(WMM_DIR, f'WMM{y}.COF')
        if not os.path.isfile(p):
            raise SystemExit(f"[ERREUR] Entrée manquante : {p} (WMM{y}.COF attendu dans wmm/)")
        rows.append("  %d: '%s'" % (y, ' '.join(_b36(v) for v in _read_epoch(p, y))))
    return '{\n' + ',\n'.join(rows) + '\n}'


_JS = r"""
/* Le modèle est celui des fichiers Data/MagVar/COF de DCS World : les World Magnetic Models de la NOAA (domaine public),
   un jeu de coefficients tous les cinq ans, de 1985.0 à 2025.0 (degré 12). Table : par époque, 90 termes (n = 1 … 12,
   m = 0 … n) × quatre valeurs (g, h, ġ, ḣ) en dixièmes de nT et de nT/an, en base 36. */
const MAG_EPOCHS = [1985, 1990, 1995, 2000, 2005, 2010, 2015, 2020, 2025];
const MAG_TABLE = @@TABLE@@;
const MAG_COEF = {};

/* Les 360 coefficients d'une époque, décodés une fois */
function magCoef(ep) {
  if (!MAG_COEF[ep]) MAG_COEF[ep] = MAG_TABLE[ep].split(' ').map(s => parseInt(s, 36) / 10);
  return MAG_COEF[ep];
}

/* L'année décimale d'une date texte : AAAA-MM-JJ, AAAA-MM (le 1er du mois) ou AAAA (le 1er juillet) ; null si elle ne se lit pas */
function magDecYear(s) {
  if (typeof s !== 'string') return null;
  const m = /^\s*(\d{4})(?:-(\d{2})(?:-(\d{2}))?)?\s*$/.exec(s);
  if (!m) return null;
  const y = +m[1];
  const leap = (y % 4 === 0 && y % 100 !== 0) || y % 400 === 0;
  const dm = [31, leap ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
  const mo = m[2] === undefined ? 7 : +m[2];
  const da = m[3] === undefined ? 1 : +m[3];
  if (mo < 1 || mo > 12 || da < 1 || da > dm[mo - 1]) return null;
  let doy = da;
  for (let i = 0; i < mo - 1; i++) doy += dm[i];
  return y + (doy - 1) / (leap ? 366 : 365);
}

/* L'époque des coefficients : la plus grande de 1985, 1990 … 2025 qui soit ≤ y ; 1985 avant 1985 (le modèle de 1985 est alors prolongé vers le passé, voir magVar) */
function magEpoch(y) {
  let e = MAG_EPOCHS[0];
  for (let i = 0; i < MAG_EPOCHS.length; i++) if (MAG_EPOCHS[i] <= y) e = MAG_EPOCHS[i];
  return e;
}

/* La déclinaison magnétique en degrés (+ vers l'Est) au niveau de la mer, à la position géodésique (lat, lon) et à l'année décimale y.
   Coefficients de l'époque : g + ġ·dt, dt = y − époque, borné à 5 au plus et sans borne basse (avant 1985, les coefficients de 1985 sont prolongés vers le passé par leur variation séculaire, comme DCS) ; synthèse en harmoniques sphériques de degré 12 (Schmidt,
   rayon de référence 6 371,2 km) ; WGS84 → géocentrique, puis X et Z ramenés au repère géodésique avant l'angle (NOAA, WMM). */
function magVar(lat, lon, y) {
  if (typeof lat !== 'number' || typeof lon !== 'number' || typeof y !== 'number' || !isFinite(lat + lon + y) || Math.abs(lat) > 90) return null;
  const R = Math.PI / 180, N = 12;
  const ep = magEpoch(y), dt = Math.min(5, y - ep), C = magCoef(ep);
  const la = Math.max(-89.9999, Math.min(89.9999, lat));
  const A = 6378.137, F = 1 / 298.257223563, E2 = F * (2 - F), RE = 6371.2;
  const sg = Math.sin(la * R);
  const rc = A / Math.sqrt(1 - E2 * sg * sg);
  const px = rc * Math.cos(la * R), pz = rc * (1 - E2) * sg;
  const rr = Math.sqrt(px * px + pz * pz);
  const x = pz / rr, z = px / rr;                       /* sin et cos de la latitude géocentrique */
  const psi = Math.asin(x) - la * R;
  /* Legendre (Gauss) et dérivée par rapport à la latitude, puis passage à la semi-normalisation de Schmidt */
  const P = [1], D = [0];
  for (let n = 1; n <= N; n++) {
    for (let m = 0; m <= n; m++) {
      const i = n * (n + 1) / 2 + m;
      if (n === m) {
        const j = (n - 1) * n / 2 + m - 1;
        P[i] = z * P[j]; D[i] = z * D[j] + x * P[j];
      } else if (n === 1 && m === 0) {
        P[i] = x * P[0]; D[i] = x * D[0] - z * P[0];
      } else {
        const j1 = (n - 2) * (n - 1) / 2 + m, j2 = (n - 1) * n / 2 + m;
        if (m > n - 2) { P[i] = x * P[j2]; D[i] = x * D[j2] - z * P[j2]; }
        else {
          const k = ((n - 1) * (n - 1) - m * m) / ((2 * n - 1) * (2 * n - 3));
          P[i] = x * P[j2] - k * P[j1]; D[i] = x * D[j2] - z * P[j2] - k * D[j1];
        }
      }
    }
  }
  const Q = [1];
  for (let n = 1; n <= N; n++) {
    const i0 = n * (n + 1) / 2;
    Q[i0] = Q[(n - 1) * n / 2] * (2 * n - 1) / n;
    for (let m = 1; m <= n; m++) Q[i0 + m] = Q[i0 + m - 1] * Math.sqrt((n - m + 1) * (m === 1 ? 2 : 1) / (n + m));
  }
  const lm = lon * R;
  let bx = 0, by = 0, bz = 0;
  for (let n = 1; n <= N; n++) {
    const rn = Math.pow(RE / rr, n + 2);
    for (let m = 0; m <= n; m++) {
      const i = n * (n + 1) / 2 + m, k = 4 * (i - 1);
      const g = C[k] + C[k + 2] * dt, h = C[k + 1] + C[k + 3] * dt;
      const cm = Math.cos(m * lm), sm = Math.sin(m * lm), pq = P[i] * Q[i], dq = -D[i] * Q[i];
      bz -= rn * (g * cm + h * sm) * (n + 1) * pq;
      by += rn * (g * sm - h * cm) * m * pq;
      bx -= rn * (g * cm + h * sm) * dq;
    }
  }
  by /= z;
  const bxg = bx * Math.cos(psi) - bz * Math.sin(psi);
  return Math.atan2(by, bxg) / R;
}

/* L'année d'une route et sa source : { src: 'mission' | 'forced' | 'typed' | 'default', y (décimale), year (AAAA, texte),
   file, date } ; la mission est celle de HQ (mission_snapshot_v1), prise si son théâtre est celui de la route et sa date se lit,
   sauf si « Forcer » est enfoncé avec une année saisie valide (quatre chiffres, de 1900 à 2099) ; sinon la saisie, sinon 1985. */
function magYearSource(theatre, yearStr, force) {
  let mis = null;
  try {
    const o = JSON.parse(localStorage.getItem('mission_snapshot_v1'));
    const sm = o && o.sourceMission;
    if (sm && typeof sm === 'object' && sm.theatre === theatre && typeof sm.missionDate === 'string' && magDecYear(sm.missionDate) != null) {
      mis = { file: typeof sm.filename === 'string' ? sm.filename : '', date: sm.missionDate.trim(), y: magDecYear(sm.missionDate) };
    }
  } catch (e) { /* aucune mission lisible */ }
  const ys = (typeof yearStr === 'string' && /^\d{4}$/.test(yearStr) && +yearStr >= 1900 && +yearStr <= 2099) ? yearStr : '';
  if (mis && !(force === true && ys)) return { src: 'mission', y: mis.y, year: String(Math.floor(mis.y)), file: mis.file, date: mis.date };
  if (ys) return { src: mis ? 'forced' : 'typed', y: magDecYear(ys), year: ys, file: mis ? mis.file : '', date: '' };
  return { src: 'default', y: magDecYear('1985'), year: '1985', file: '', date: '' };
}
"""


def build_block():
    """Le texte du bloc, délimité par ses deux commentaires, sans saut de ligne final."""
    body = _JS.replace('@@TABLE@@', build_table())
    return BLOCK_BEGIN + body + BLOCK_END + '\n'


if __name__ == '__main__':
    txt = build_block()
    print(f"[OK] bloc de déclinaison : {len(txt)} caractères")
