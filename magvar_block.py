#!/usr/bin/env python3
"""Bloc « DÉCLINAISON MAGNÉTIQUE (WMM, comme DCS) » — une seule source pour le Route Planner et le Datacard Generator.

Lit les coefficients du World Magnetic Model (NOAA NCEI / British Geological Survey, domaine public ; les époques
1985 à 2025 que DCS World embarque) dans le dossier wmm/ à la racine du dépôt, ceux de l'International Geomagnetic
Reference Field, 12e génération (IAGA, au format geomag70 de la NOAA ; les époques 1900 à 1985, que DCS World embarque
aussi) dans le dossier igrf/, et rend le texte JavaScript du bloc : les deux tables compactes de coefficients et les
fonctions magDecYear, magModel, magVar et magYearSource. Comme DCS : une année entière jusqu'à 1985 → IGRF au 1er janvier
de cette année ; plus tard → le WMM de l'époque précédente.
Les deux builds insèrent ce texte tel quel : le bloc est identique à l'octet dans les deux fichiers de dist/.

Usage (par les builds) : from magvar_block import build_block ; texte = build_block()
"""

import glob
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
WMM_DIR = os.path.join(HERE, 'wmm')
IGRF_DIR = os.path.join(HERE, 'igrf')
IGRF_FILE = 'IGRF12.COF'

BLOCK_BEGIN = '/* ===== DÉCLINAISON MAGNÉTIQUE (WMM, comme DCS) ===== */'
BLOCK_END = '/* ===== FIN DE LA DÉCLINAISON MAGNÉTIQUE ===== */'

DEGREE = 12                      # degré maximal du modèle (n = 1 … 12 : 90 lignes par fichier)
EPOCHS = list(range(1985, 2026, 5))
IGRF_FIRST = 1900                # première époque IGRF embarquée
IGRF_LAST = 1985                 # dernière année entière calculée en IGRF (et dernière époque embarquée)
IGRF_EPOCHS = list(range(IGRF_FIRST, IGRF_LAST + 1, 5))
IGRF_DEGREE = 10                 # degré des époques IGRF de 1900 à 1985 (n = 1 … 10 : 65 termes par époque)


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


def _read_igrf(path):
    """igrf/IGRF12.COF → { époque : liste de 130 entiers (dixièmes : g, h pour chaque (n, m) dans l'ordre du fichier) }
    pour les seules époques IGRF_FIRST … IGRF_LAST. Chaque bloc s'ouvre par une ligne d'en-tête (nom, époque, degré …)
    suivie d'une ligne « n m g h ġ ḣ … » par terme."""
    name = 'igrf/' + os.path.basename(path)
    try:
        with open(path, encoding='utf-8', newline=None) as f:
            lines = f.read().split('\n')
    except (OSError, UnicodeDecodeError) as e:
        raise SystemExit(f"[ERREUR] {name} : illisible ({e})")
    blocks = {}                  # époque → (degré, [(n, m, g, h), …])
    cur = None
    for raw in lines:
        s = raw.strip()
        if not s:
            continue
        parts = s.split()
        if not parts[0].lstrip('-').isdigit():          # ligne d'en-tête
            try:
                epoch, degree = float(parts[1]), int(parts[2])
            except (ValueError, IndexError):
                raise SystemExit(f"[ERREUR] {name} : en-tête illisible : {raw!r}")
            cur = []
            blocks[epoch] = (degree, cur)
            continue
        if cur is None:
            raise SystemExit(f"[ERREUR] {name} : ligne de coefficients avant tout en-tête : {raw!r}")
        if len(parts) < 6:
            raise SystemExit(f"[ERREUR] {name} : ligne illisible (6 champs au moins attendus) : {raw!r}")
        try:
            n, m = int(parts[0]), int(parts[1])
            g, h = float(parts[2]), float(parts[3])
        except ValueError:
            raise SystemExit(f"[ERREUR] {name} : ligne illisible : {raw!r}")
        cur.append((n, m, g, h))
    expect = [(n, m) for n in range(1, IGRF_DEGREE + 1) for m in range(0, n + 1)]
    out = {}
    for y in IGRF_EPOCHS:
        if float(y) not in blocks:
            raise SystemExit(f"[ERREUR] {name} : époque {y}.0 manquante")
        degree, terms = blocks[float(y)]
        if degree != IGRF_DEGREE:
            raise SystemExit(f"[ERREUR] {name} : l'époque {y}.0 est de degré {degree}, {IGRF_DEGREE} attendu")
        if [(n, m) for n, m, _, _ in terms] != expect:
            raise SystemExit(f"[ERREUR] {name} : époque {y}.0 : termes (n, m) inattendus ({len(terms)} lignes, {len(expect)} attendues)")
        vals = []
        for n, m, g, h in terms:
            for x in (g, h):
                t = round(x * 10)
                if abs(x * 10 - t) > 1e-6:
                    raise SystemExit(f"[ERREUR] {name} : époque {y}.0 : valeur à plus d'une décimale : {x} (terme {n}, {m})")
                vals.append(int(t))
        out[y] = vals
    return out


def build_igrf_table():
    """La table IGRF compacte : { année : 'jetons en base 36' } ; 2 jetons par terme (g h), en dixièmes, 1900 à 1985."""
    p = os.path.join(IGRF_DIR, IGRF_FILE)
    if not os.path.isdir(IGRF_DIR):
        raise SystemExit(f"[ERREUR] Dossier manquant : {IGRF_DIR} (igrf/ attendu à la racine du dépôt)")
    if not os.path.isfile(p):
        raise SystemExit(f"[ERREUR] Entrée manquante : {p} ({IGRF_FILE} attendu dans igrf/)")
    data = _read_igrf(p)
    rows = ["  %d: '%s'" % (y, ' '.join(_b36(v) for v in data[y])) for y in IGRF_EPOCHS]
    return '{\n' + ',\n'.join(rows) + '\n}'


_JS = r"""
/* Le modèle est celui des fichiers de DCS World, qui calcule ainsi la déclinaison d'une date de mission :
   - une année entière Y jusqu'à MAG_IGRF_LAST (1985) : l'IGRF-12 (IAGA ; fichier COF_IGRF/IGRF12.COF), au 1er janvier de Y sans
     la date : coefficients g, h interpolés linéairement entre les deux époques de cinq ans qui encadrent Y (1900 pour les années
     plus anciennes), degré 10. Table MAG_IGRF_TABLE : par époque de 1900 à 1985, 65 termes (n = 1 … 10, m = 0 … n) × deux valeurs
     (g, h) en dixièmes de nT, en base 36 ;
   - une année entière Y après 1985 : le World Magnetic Model de la NOAA (domaine public ; fichiers Data/MagVar/COF) de l'époque la plus
     grande strictement inférieure à Y (2020 → WMM 2015, 2025 → WMM 2020, 2026 et après → WMM 2025), à la date exacte : g + ġ·dt, dt = y − époque,
     sans borne. Un jeu de coefficients tous les cinq ans, de 1985.0 à 2025.0 (degré 12). Table MAG_TABLE : par époque, 90 termes
     (n = 1 … 12, m = 0 … n) × quatre valeurs (g, h, ġ, ḣ) en dixièmes de nT et de nT/an, en base 36. */
const MAG_IGRF_LAST = @@IGRF_LAST@@;
const MAG_IGRF_TABLE = @@IGRF_TABLE@@;
const MAG_IGRF_COEF = {};
const MAG_EPOCHS = [1985, 1990, 1995, 2000, 2005, 2010, 2015, 2020, 2025];
const MAG_TABLE = @@TABLE@@;
const MAG_COEF = {};

/* Les 360 coefficients d'une époque, décodés une fois */
function magCoef(ep) {
  if (!MAG_COEF[ep]) MAG_COEF[ep] = MAG_TABLE[ep].split(' ').map(s => parseInt(s, 36) / 10);
  return MAG_COEF[ep];
}

/* Les 130 valeurs (g, h) d'une époque IGRF, décodées */
function magIgrfEpoch(ep) {
  return MAG_IGRF_TABLE[ep].split(' ').map(s => parseInt(s, 36) / 10);
}

/* Les 360 coefficients de l'IGRF à l'année entière Y (au plus MAG_IGRF_LAST), au 1er janvier : t = max(1900, Y), e l'époque ≤ t,
   g(t) = g(e) + (g(e + 5) − g(e))·(t − e)/5, de même pour h ; même disposition que ceux du WMM (g, h, ġ, ḣ), ġ et ḣ à zéro, les termes
   de degré 11 et 12 à zéro ; calculés une fois par année */
function magIgrfCoef(Y) {
  const t = Math.max(1900, Y);
  if (!MAG_IGRF_COEF[t]) {
    const e = 1900 + 5 * Math.floor((t - 1900) / 5);
    const a = magIgrfEpoch(e), b = t === e ? a : magIgrfEpoch(e + 5);
    const C = new Array(360).fill(0);
    for (let j = 0; j < 65; j++) {
      C[4 * j] = a[2 * j] + (b[2 * j] - a[2 * j]) * (t - e) / 5;
      C[4 * j + 1] = a[2 * j + 1] + (b[2 * j + 1] - a[2 * j + 1]) * (t - e) / 5;
    }
    MAG_IGRF_COEF[t] = C;
  }
  return MAG_IGRF_COEF[t];
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

/* L'époque WMM d'une année entière Y : la plus grande de 1985, 1990 … 2025 strictement inférieure à Y (1985 si aucune) */
function magWmmEpoch(Y) {
  let e = MAG_EPOCHS[0];
  for (let i = 0; i < MAG_EPOCHS.length; i++) if (MAG_EPOCHS[i] < Y) e = MAG_EPOCHS[i];
  return e;
}

/* Le modèle de DCS pour l'année décimale y, tel qu'on le nomme à l'écran : 'IGRF <Y>' (Y entière de y, 1900 au plus tôt) jusqu'à
   MAG_IGRF_LAST, 'WMM <époque>' ensuite */
function magModel(y) {
  const Y = Math.floor(y);
  return Y <= MAG_IGRF_LAST ? 'IGRF ' + Math.max(1900, Y) : 'WMM ' + magWmmEpoch(Y);
}

/* La déclinaison magnétique en degrés (+ vers l'Est) au niveau de la mer, à la position géodésique (lat, lon) et à l'année décimale y.
   Coefficients : ceux de l'IGRF au 1er janvier de l'année entière de y jusqu'à MAG_IGRF_LAST, sinon ceux du WMM de l'époque précédente, g + ġ·dt,
   dt = y − époque, sans borne (voir plus haut) ; synthèse en harmoniques sphériques de degré 12 (Schmidt,
   rayon de référence 6 371,2 km ; les termes absents de l'IGRF, de degré 11 et 12, sont à zéro) ; WGS84 → géocentrique, puis X et Z ramenés au repère géodésique avant l'angle (NOAA, WMM). */
function magVar(lat, lon, y) {
  if (typeof lat !== 'number' || typeof lon !== 'number' || typeof y !== 'number' || !isFinite(lat + lon + y) || Math.abs(lat) > 90) return null;
  const R = Math.PI / 180, N = 12;
  const Y = Math.floor(y), igrf = Y <= MAG_IGRF_LAST;
  const ep = igrf ? 0 : magWmmEpoch(Y), dt = igrf ? 0 : y - ep, C = igrf ? magIgrfCoef(Y) : magCoef(ep);
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
    body = _JS.replace('@@IGRF_LAST@@', str(IGRF_LAST)).replace('@@IGRF_TABLE@@', build_igrf_table()).replace('@@TABLE@@', build_table())
    return BLOCK_BEGIN + body + BLOCK_END + '\n'


if __name__ == '__main__':
    txt = build_block()
    print(f"[OK] bloc de déclinaison : {len(txt)} caractères")
