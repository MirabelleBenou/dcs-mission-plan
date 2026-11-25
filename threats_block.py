"""La couche des menaces : les données de data/threats.json lues et embarquées (Route Planner, Field Manual), le script de la couche du Route Planner et sa feuille de style.

load() refuse un fichier dont le format n'est pas « dcs-threats-v1 » ; ce qui est embarqué ne porte ni la source, ni l'écart, ni la fiche du guide de Goldwolf :
seulement ce que la couche emploie (le capteur, et par système l'id, les deux noms, la nature, le capteur, les portées de tir et de détection, le plafond).
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(HERE, 'data', 'threats.json')
FORMAT = 'dcs-threats-v1'
KINDS = ('sam', 'aaa', 'radar')
SENSORS = ('search', 'fire-control', 'shooter')


def load(path=PATH):
    if not os.path.isfile(path):
        raise SystemExit(f"[ERREUR] Entrée manquante : {path} (data/threats.json attendu)")
    with open(path, encoding='utf-8') as f:
        d = json.load(f)
    if not isinstance(d, dict) or d.get('format') != FORMAT:
        raise SystemExit(f"[ERREUR] data/threats.json : le format doit être « {FORMAT} »")
    sh = d.get('sensor_height_m')
    if not isinstance(sh, dict) or sorted(sh) != sorted(SENSORS) or not all(isinstance(v, (int, float)) and v >= 0 for v in sh.values()):
        raise SystemExit("[ERREUR] data/threats.json : sensor_height_m illisible")
    seen = set()
    for s in d.get('systems') or []:
        if (not isinstance(s.get('id'), str) or s['id'] in seen or s.get('kind') not in KINDS or s.get('sensor') not in SENSORS
                or not isinstance(s.get('name_fr'), str) or not isinstance(s.get('name_en'), str)
                or type(s.get('fire_m')) is not int or type(s.get('detect_m')) is not int
                or not (s.get('ceiling_m') is None or type(s['ceiling_m']) is int)):
            raise SystemExit(f"[ERREUR] data/threats.json : système illisible : {s.get('id')!r}")
        seen.add(s['id'])
    if not seen:
        raise SystemExit("[ERREUR] data/threats.json : aucun système")
    return d


def js_data(d):
    """La constante THREATS de la page."""
    out = {'sensor_height_m': d['sensor_height_m'],
           'systems': [{k: s[k] for k in ('id', 'name_fr', 'name_en', 'kind', 'sensor', 'fire_m', 'detect_m', 'ceiling_m')} for s in d['systems']]}
    txt = json.dumps(out, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
    return 'const THREATS = ' + txt + ';\n'


FM_COLS = {
    'fr': ('Système', 'Nature', 'Tir (km)', 'Détection (km)', 'Plafond (m)', 'Capteur'),
    'en': ('System', 'Kind', 'Fire (km)', 'Detection (km)', 'Ceiling (m)', 'Sensor'),
}
FM_KIND = {'sam': 'SAM', 'aaa': 'AAA', 'radar': 'Radar'}
FM_SENSOR = {
    'fr': {'search': 'radar de veille', 'fire-control': 'radar de conduite de tir', 'shooter': 'le tireur lui-même'},
    'en': {'search': 'search radar', 'fire-control': 'fire-control radar', 'shooter': 'the launcher itself'},
}
FM_CAPTION = {'fr': 'Les systèmes de défense aérienne du jeu : portées de tir et de détection, plafond, capteur.',
              'en': 'The game’s air defence systems: firing and detection ranges, ceiling, sensor.'}


def _grp(n, lang):
    return f'{n:,}'.replace(',', '\u202f' if lang == 'fr' else ',')


def _km(m, lang):
    """Mètres → km à une décimale, séparateurs de la langue ; 0 → « — »."""
    if not m:
        return '—'
    s = f'{m / 1000:,.1f}'.replace(',', '\u202f' if lang == 'fr' else ',')
    return s.replace('.', ',') if lang == 'fr' else s


def _m(m, lang):
    return '—' if not m else _grp(m, lang)


def fm_tables(d):
    """Le bloc « raw » de la page du Route Planner du Field Manual : une table par langue (lang-block), chacune dans une enveloppe qui défile en largeur, les systèmes dans l'ordre du fichier."""
    from html import escape
    out = []
    for lang in ('fr', 'en'):
        head = ''.join('<th scope="col"%s>%s</th>' % (' class="n"' if i in (2, 3, 4) else '', escape(c)) for i, c in enumerate(FM_COLS[lang]))
        rows = []
        for s in d['systems']:
            rows.append('<tr><th scope="row" class="s">%s</th><td>%s</td><td class="n">%s</td><td class="n">%s</td><td class="n">%s</td><td>%s</td></tr>' % (
                escape(s['name_' + lang]), FM_KIND[s['kind']], _km(s['fire_m'], lang), _km(s['detect_m'], lang), _m(s['ceiling_m'], lang), escape(FM_SENSOR[lang][s['sensor']])))
        out.append('      <div class="fm-tbl-wrap lang-block" data-lang="%s" tabindex="0" role="region" aria-label="%s"><table class="fm-tbl"><thead><tr>%s</tr></thead><tbody>\n%s\n</tbody></table></div>' % (
            lang, escape(FM_CAPTION[lang]), head, '\n'.join(rows)))
    return '\n'.join(out)


def build_block(d=None):
    d = d or load()
    return js_data(d) + JS


CSS = r"""
/* la couche des menaces (lot mp-rp-menaces-couche) */
#rp-thr { position: absolute; left: 10px; bottom: 28px; z-index: 500; box-sizing: border-box; width: 280px; max-width: calc(100% - 20px); padding: 7px 10px 8px;
  font: 500 12px/1.3 var(--f-ui); letter-spacing: .03em; background: rgba(26,28,20,.92); color: #e8dcb8; border: 1px solid var(--amber); border-radius: 2px; }
#rp-thr .thr-h, #rp-thr .thr-r { display: flex; justify-content: space-between; align-items: baseline; gap: 10px; }
#rp-thr .thr-t { color: var(--amber); font-weight: 700; letter-spacing: .16em; font-size: 12px; }
#rp-thr .thr-src { font-size: 11px; text-align: right; }
#rp-thr .thr-r { margin-top: 6px; }
#rp-thr .thr-r label { font-size: 12px; }
#rp-thr .thr-r b { font-weight: 700; font-size: 13px; }
#rp-thr input[type="range"] { -webkit-appearance: none; appearance: none; display: block; width: 100%; height: 22px; margin: 2px 0 0; padding: 0; background: transparent; accent-color: var(--amber); cursor: pointer; }
#rp-thr input[type="range"]::-webkit-slider-runnable-track { height: 4px; border-radius: 2px; background: rgba(232,220,184,.35); }
#rp-thr input[type="range"]::-moz-range-track { height: 4px; border-radius: 2px; background: rgba(232,220,184,.35); }
#rp-thr input[type="range"]::-webkit-slider-thumb { -webkit-appearance: none; appearance: none; box-sizing: border-box; width: 16px; height: 16px; margin-top: -6px; border: 0; border-radius: 50%; background: var(--amber); }
#rp-thr input[type="range"]::-moz-range-thumb { -moz-appearance: none; appearance: none; box-sizing: border-box; width: 16px; height: 16px; border: 0; border-radius: 50%; background: var(--amber); }
#rp-thr .thr-ticks { position: relative; height: 14px; margin: 0 0 6px; }
#rp-thr .thr-tk { position: absolute; top: 0; transform: translateX(-50%); font-size: 10px; line-height: 14px; white-space: nowrap; }
#rp-thr .thr-leg { display: flex; flex-wrap: wrap; gap: 3px 14px; font-size: 11px; line-height: 15px; }
#rp-thr .thr-leg span { display: inline-flex; align-items: center; gap: 6px; }
#rp-thr .thr-sw { display: inline-block; flex: none; width: 18px; height: 10px; box-sizing: border-box; }
#rp-thr .thr-sw.zone { background: rgba(200,16,46,.43); border: 1px solid #c8102e; }
#rp-thr .thr-sw.fire { height: 0; border-top: 2px solid #c8102e; }
#rp-thr .thr-sw.det { height: 0; border-top: 2px dashed #c8102e; }
#rp-thr .thr-sw.halo { height: 7px; background: #ffd400; }
#rp-thr.thr-pill { display: flex; align-items: center; gap: 8px; width: auto; height: 44px; padding: 0 0 0 10px; bottom: 10px; left: auto; right: 8px; border: 0; box-shadow: inset 0 0 0 1px var(--amber); }
#rp-thr.thr-pill .thr-v { font-weight: 700; font-size: 13px; white-space: nowrap; }
#rp-thr.thr-pill .thr-src { font-size: 11px; }
#rp-thr[hidden] { display: none; }       /* après .thr-pill (même spécificité) : décoché, la pastille disparaît aussi */
#rp-thr .thr-b { flex: none; box-sizing: border-box; width: 44px; height: 44px; margin: 0; padding: 0; border: 0; border-left: 1px solid rgba(232,220,184,.35); border-radius: 0; background: transparent;
  color: #e8dcb8; font: 700 24px/1 var(--f-ui); cursor: pointer; touch-action: manipulation; }
#rp-thr .thr-b:disabled { opacity: .4; cursor: default; }
#rp-thr .thr-fold { flex: none; box-sizing: border-box; width: 44px; height: 44px; margin: 0; padding: 0; border: 0; border-left: 1px solid rgba(232,220,184,.35); border-radius: 0; background: transparent;
  color: #c8923a; font: 700 17px/1 var(--f-ui); cursor: pointer; touch-action: manipulation; }       /* l'ambre un peu éclairci : 4,5 : 1 au moins sur le fond de la pastille, même sur une carte blanche */
#rp-thr.thr-shut .thr-b { display: none; }
.leaflet-threats-pane, .leaflet-thrroute-pane { pointer-events: none; }
table.nav tr.thr td { background: rgba(158,27,20,.07); color: #9e1b14; font-family: var(--f-ui); font-weight: 600; font-size: 12px; letter-spacing: .3px; white-space: normal; overflow-wrap: anywhere; }
.dr-thr-info { margin-top: 4px; font-size: 12px; line-height: 1.35; color: var(--khaki-light); }
.dr-thr-info:empty { display: none; }
"""

JS = r"""
/* ============= LES MENACES (lot mp-rp-menaces-couche) =============
   Un symbole OTAN ennemi SAM, AAA ou Radar peut porter un système (champ « threat » de l'objet, dans route_layers_v1). Avec la case « Menaces » du menu Affichage, la carte montre :
   - les cercles de portée (volet « threats », 260), toujours ;
   - sur un théâtre qui a son relief, la zone vue (une seule GridLayer, une seule teinte) : où un aéronef à la hauteur vérifiée au-dessus du sol est vu de la menace et à sa portée de tir,
     masqué par le relief de DCS, ligne de vue à plat (ni courbure, ni réfraction) ; la grille de chaque menace se calcule une fois (un Worker) ; changer la hauteur ne la recalcule pas ;
   - la route choisie, jugée à sa propre altitude : un halo jaune sous la route vue (volet « thrroute », 398) et, à la feuille de navigation, par quelles menaces et sur quelle distance ;
   - le cartouche #rp-thr : la hauteur vérifiée (au téléphone, une pastille avec « − » et « + »), la source, la légende.
   Rien ne s'écrit dans le fichier de travail : seul le champ « threat » de l'objet ; la case et la hauteur sont des réglages d'écran (rp_display_v1). */
const THR_ID_RE = /^[a-z0-9][a-z0-9-]{0,39}$/;
const THR_NATURE = { 'GPEWMS--': 'sam', 'GPEWAH--': 'aaa', 'GPESR---': 'radar' };
const THR_BY_ID = {};
THREATS.systems.forEach(s => { THR_BY_ID[s.id] = s; });
const THR_STEPS = {
  m: [0, 15, 30, 60, 100, 150, 300, 500, 1000, 2000, 3000, 4500, 6000, 8000, 10000, 15000, 20000, 25000, 30000],
  ft: [0, 50, 100, 200, 300, 500, 1000, 1500, 3000, 6500, 10000, 15000, 20000, 26000, 33000, 50000, 65000, 82000, 100000]
};
const THR_RANK_DEF = 2;        /* la hauteur vérifiée au départ : 30 m (100 ft) */
const THR_RANK_MIN = 12;       /* le dernier rang offert au moins : 6 000 m (20 000 ft) */
const THR_TILES_MAX = 512;     /* tuiles d'altitude gardées au plus, dans un cache qui n'est pas celui du relief */
const THR_PX_MAX = 1024;       /* le rayon d'une grille, en pixels, au niveau choisi */
const THR_RAY_STEP = 0.5;      /* un échantillon tous les 0,5 pixel le long d'un rayon */
const THR_SAMPLE_M = 100;      /* un échantillon de route tous les 100 m */
const THR_NARROW = 760;        /* sous cette largeur de carte, le cartouche est une pastille */
const THR_RED = '#c8102e';
const THR_ZONE_ALPHA = 110;    /* rgba(200, 16, 46, 0.43) */
const THR = {
  tiles: new Map(),            /* adresse de la tuile d'altitude → { p: promesse de ses mètres (Float32Array de 65 536) ou de null } */
  canvas: null,
  grids: new Map(),            /* clé (système, lat, lon, théâtre) → grille calculée */
  jobs: new Map(),             /* clé → le calcul en cours */
  bad: new Set(),              /* les clés dont le calcul a échoué : pas de nouvel essai tant que la menace reste active */
  ver: 0,                      /* monte à chaque grille posée ou retirée */
  act: [], desc: null, state: '',
  circ: null, halo: null, circSig: '', haloSig: '',
  zone: null, zoneSig: '', paint: { H: 0, list: [] },
  seen: null, routeSig: '', routeSeq: 0, routeTimer: 0,
  box: null, boxSig: '', raf: 0, open: false,       /* open : la pastille dépliée (« − » et « + » vus) ; en mémoire seulement, repliée à chaque ouverture du RP */
  blob: ''
};

function thrNature(sidc) { return typeof sidc === 'string' && sidc.length >= 10 ? (THR_NATURE[symCode(sidc)] || '') : ''; }
/* Un symbole porte une menace : du camp Ennemi, d'une des trois natures, avec un champ « threat » dont le système a la nature du symbole */
function thrCarries(it) {
  if (!it || it.type !== 'symbol' || it.sidc[1] !== 'H' || !thrNature(it.sidc) || typeof it.threat !== 'string' || it.threat === '') return false;
  const sys = THR_BY_ID[it.threat];
  return !sys || sys.kind === thrNature(it.sidc);       /* le système d'une autre nature (venu d'un fichier) ne se dessine pas */
}
function thrSysName(sys) { return CURRENT_LANG === 'fr' ? sys.name_fr : sys.name_en; }
function thrSteps() { return THR_STEPS[S.units.altitude === 'ft' ? 'ft' : 'm']; }
function thrStepM(rank) { const v = thrSteps()[rank]; return S.units.altitude === 'ft' ? v * FT_M : v; }
/* Le dernier rang offert : le premier dont la hauteur atteint le plus grand plafond connu des menaces actives ; jamais moins que le rang 12 (6 000 m ; 20 000 ft) ; sans plafond connu, le rang 12 */
function thrTop() {
  let ceil = -1;
  THR.act.forEach(a => { if (a.sys.ceiling_m != null && a.sys.ceiling_m > ceil) ceil = a.sys.ceiling_m; });
  if (ceil < 0) return THR_RANK_MIN;
  const n = thrSteps().length;
  for (let i = 0; i < n; i++) if (thrStepM(i) >= ceil) return Math.max(i, THR_RANK_MIN);
  return n - 1;
}
/* Le rang gardé n'est pas réécrit quand il dépasse le dernier rang offert : la hauteur employée est celle de ce dernier rang */
function thrRank() { return Math.max(0, Math.min(DISP.thrStep, thrTop())); }
function thrH() { return thrStepM(thrRank()); }
function thrNum(v) { return String(Math.round(v)).replace(/\B(?=(\d{3})+(?!\d))/g, CURRENT_LANG === 'fr' ? ' ' : ','); }
function thrAlt(m) { return thrNum(altValue(m)) + ' ' + t(S.units.altitude === 'ft' ? 'u.ft' : 'u.m'); }
function thrHText() { return t('thr.h.v', { v: thrNum(thrSteps()[thrRank()]), u: t(S.units.altitude === 'ft' ? 'u.ft' : 'u.m') }); }

/* ---- la fiche du symbole ---- */
function thrListFor(kind) {
  return THREATS.systems.filter(s => s.kind === kind).sort((a, b) => thrSysName(a).localeCompare(thrSysName(b), CURRENT_LANG));
}
function thrInfoLine(it) {
  const sys = typeof it.threat === 'string' ? THR_BY_ID[it.threat] : null;
  if (!sys) return '';
  const ceil = sys.ceiling_m == null ? t('thr.ceil.none') : t('thr.ceil', { v: thrAlt(sys.ceiling_m) });
  const parts = [];
  if (sys.kind !== 'radar' && sys.fire_m > 0) parts.push(t('thr.p.fire', { v: fmtDist(sys.fire_m / 1000) }));
  if (sys.detect_m > 0) parts.push(t('thr.p.det', { v: fmtDist(sys.detect_m / 1000) }));
  parts.push(t('thr.p.tail', { ceil: ceil, sensor: t('thr.sensor.' + sys.sensor) }));
  const first = parts[0].charAt(0).toUpperCase() + parts[0].slice(1);
  return [first].concat(parts.slice(1)).join(' · ');
}
function thrFieldHtml(it) {
  const kind = thrNature(it.sidc), cur = typeof it.threat === 'string' ? it.threat : '';
  const list = thrListFor(kind);
  let o = '<option value=""' + (cur === '' ? ' selected' : '') + '>' + esc(t('thr.none')) + '</option>';
  if (cur !== '' && !list.some(s => s.id === cur)) {
    const sys = THR_BY_ID[cur];
    o += '<option value="' + esc(cur) + '" selected>' + esc(sys ? t('thr.other', { n: thrSysName(sys) }) : t('thr.unknown', { id: cur })) + '</option>';
  }
  list.forEach(s => { o += '<option value="' + esc(s.id) + '"' + (cur === s.id ? ' selected' : '') + '>' + esc(thrSysName(s)) + '</option>'; });
  return '<select id="dr-f-threat" data-f="threat">' + o + '</select><div class="dr-thr-info" id="dr-f-threat-info">' + esc(thrInfoLine(it)) + '</div>';
}
function thrInfoRefresh(it) { const e = $('dr-f-threat-info'); if (e) e.textContent = thrInfoLine(it); }

/* ---- les menaces actives ---- */
function thrActive() {
  const out = [];
  if (!DISP.threats) return out;
  CF_LAYERS.forEach(l => {
    if (!l.visible) return;
    l.items.forEach(it => {
      if (!thrCarries(it) || !cfItemShown(l, it)) return;
      const sys = THR_BY_ID[it.threat];
      if (!sys) return;
      out.push({ it: it, sys: sys, R: sys.kind === 'radar' ? sys.detect_m : sys.fire_m, key: sys.id + '|' + it.lat + '|' + it.lon + '|' + S.theatre,
        name: hasText(it.name) ? it.name.trim() : thrSysName(sys) });
    });
  });
  return out;
}

/* ---- le sol : les tuiles d'altitude (Terrain-RGB) du relief de DCS, dans un cache à part ---- */
function thrMercV(lat) { const sn = Math.sin(lat * Math.PI / 180); return 0.5 - Math.log((1 + sn) / (1 - sn)) / (4 * Math.PI); }
function thrMpp(lat, z) { return 40075016.686 * Math.cos(lat * Math.PI / 180) / (256 * Math.pow(2, z)); }
/* Les mètres d'une tuile (Float32Array de 65 536), ou null : tuile absente, illisible, hors carte ; un pixel d'alpha 0 vaut 0 m */
function thrTile(url, meta) {
  const hit = THR.tiles.get(url);
  if (hit) return hit;
  const p = fetch(url, { mode: 'cors' })
    .then(r => (r.ok ? r.blob() : null))
    .then(blob => (blob ? createImageBitmap(blob, { colorSpaceConversion: 'none', premultiplyAlpha: 'none' }) : null))
    .then(bm => {
      if (!bm) return null;
      try {
        if (bm.width !== 256 || bm.height !== 256) return null;
        if (!THR.canvas) { THR.canvas = document.createElement('canvas'); THR.canvas.width = 256; THR.canvas.height = 256; }
        const cx = THR.canvas.getContext('2d', { willReadFrequently: true });
        cx.clearRect(0, 0, 256, 256);
        cx.drawImage(bm, 0, 0);
        const d = cx.getImageData(0, 0, 256, 256).data, out = new Float32Array(65536);
        for (let i = 0; i < 65536; i++) {
          const k = i * 4;
          out[i] = d[k + 3] === 0 ? 0 : meta.base + (d[k] * 65536 + d[k + 1] * 256 + d[k + 2]) * meta.step;
        }
        return out;
      } catch (e) { return null; } finally { if (bm.close) bm.close(); }
    })
    .catch(() => null);
  THR.tiles.set(url, p);
  while (THR.tiles.size > THR_TILES_MAX) THR.tiles.delete(THR.tiles.keys().next().value);
  return p;
}
function thrTileUrl(th, meta, z, tx, ty) { return RELIEF_BASE + th + '/' + fillTile(meta.elev, z, tx, ty); }
/* Le sol d'un carré de pixels du niveau z (Float32Array de side × side) ; hors des bornes du relief, tuile absente ou alpha 0 : 0 m */
function thrReadGround(th, meta, z, px0, py0, side) {
  const n = 256 * Math.pow(2, z), b = meta.bounds;
  const xmin = (b[0][1] + 180) / 360 * n, xmax = (b[1][1] + 180) / 360 * n, ymin = thrMercV(b[1][0]) * n, ymax = thrMercV(b[0][0]) * n;
  const g = new Float32Array(side * side);
  const tx0 = Math.floor(px0 / 256), tx1 = Math.floor((px0 + side - 1) / 256), ty0 = Math.floor(py0 / 256), ty1 = Math.floor((py0 + side - 1) / 256), lim = Math.pow(2, z);
  const want = [];
  for (let ty = ty0; ty <= ty1; ty++) for (let tx = tx0; tx <= tx1; tx++) {
    if (tx < 0 || ty < 0 || tx >= lim || ty >= lim) continue;
    if ((tx + 1) * 256 <= xmin || tx * 256 >= xmax || (ty + 1) * 256 <= ymin || ty * 256 >= ymax) continue;       /* une tuile hors des bornes du relief : pas de requête, le sol y vaut 0 */
    want.push({ tx: tx, ty: ty, p: thrTile(thrTileUrl(th, meta, z, tx, ty), meta) });
  }
  return Promise.all(want.map(w => w.p)).then(arr => {
    arr.forEach((d, i) => {
      if (!d) return;
      const tx = want[i].tx, ty = want[i].ty;
      const ax0 = Math.max(px0, tx * 256), ax1 = Math.min(px0 + side, tx * 256 + 256), ay0 = Math.max(py0, ty * 256), ay1 = Math.min(py0 + side, ty * 256 + 256);
      for (let py = ay0; py < ay1; py++) {
        const yc = py + 0.5;
        if (yc < ymin || yc > ymax) continue;
        const row = (py - py0) * side - px0, trow = (py - ty * 256) * 256 - tx * 256;
        for (let px = ax0; px < ax1; px++) {
          const xc = px + 0.5;
          if (xc < xmin || xc > xmax) continue;
          g[row + px] = d[trow + px];
        }
      }
    });
    return { g: g, tiles: want.length };
  });
}

/* ---- le calcul d'une grille : la hauteur de visibilité hv (Float32, mètres au-dessus du sol), à plat ----
   Cette fonction est le code du Worker : elle ne lit rien de la page (elle s'écrit dans un Blob telle quelle).
   m = { g (le sol, side × side), side, K (le demi-côté), mpp (mètres par pixel), R (portée, m), zs (altitude du capteur, m) } ; rend hv (Infinity hors du disque et là où rien ne voit). */
function thrCalc(m) {
  const g = m.g, side = m.side, K = m.K, mpp = m.mpp, R = m.R, zs = m.zs;
  const hv = new Float32Array(side * side);
  hv.fill(Infinity);
  const c = K + 0.5, rpx = R / mpp, step = 0.5;
  const ray = function (ex, ey) {
    const dx = ex + 0.5 - c, dy = ey + 0.5 - c, len = Math.sqrt(dx * dx + dy * dy);
    if (!(len > 0)) return;
    const ux = dx / len, uy = dy / len, maxT = Math.min(len, rpx) + 1e-9;
    let pmax = -Infinity;
    for (let k = 1; ; k++) {
      const tt = k * step;
      if (tt > maxT) break;
      const idx = Math.floor(c + uy * tt) * side + Math.floor(c + ux * tt), gg = g[idx], d = tt * mpp;
      let h = zs + pmax * d - gg;
      if (!(h > 0)) h = 0;
      if (h < hv[idx]) hv[idx] = h;
      const sl = (gg - zs) / d;
      if (sl > pmax) pmax = sl;
    }
  };
  for (let i = 0; i < side; i++) { ray(i, 0); ray(i, side - 1); }
  for (let j = 1; j < side - 1; j++) { ray(0, j); ray(side - 1, j); }
  /* un pixel du disque qu'aucun rayon ne touche prend le plus petit h de ses voisins touchés ; hors du disque : rien */
  const fill = [], r2 = rpx * rpx;
  for (let j = 0; j < side; j++) {
    for (let i = 0; i < side; i++) {
      const idx = j * side + i, ddx = i + 0.5 - c, ddy = j + 0.5 - c;
      if (ddx * ddx + ddy * ddy > r2) { hv[idx] = Infinity; continue; }
      if (hv[idx] !== Infinity) continue;
      let best = Infinity;
      for (let dj = -1; dj <= 1; dj++) {
        const jj = j + dj;
        if (jj < 0 || jj >= side) continue;
        for (let di = -1; di <= 1; di++) {
          const ii = i + di;
          if ((di === 0 && dj === 0) || ii < 0 || ii >= side) continue;
          const v = hv[jj * side + ii];
          if (v < best) best = v;
        }
      }
      if (best !== Infinity) fill.push(idx, best);
    }
  }
  for (let q = 0; q < fill.length; q += 2) hv[fill[q]] = fill[q + 1];
  return hv;
}
function thrWorkerSrc() { return thrCalc.toString() + '\nself.onmessage = function (e) { var r = thrCalc(e.data); self.postMessage(r, [r.buffer]); };'; }
/* Dans un Worker (fait d'un Blob) ; si le Worker manque, lève ou échoue, le même code tourne sur la page */
function thrRunCalc(msg, noWorker, job) {
  const t0 = performance.now();
  const inline = () => ({ hv: thrCalc(msg), worker: false, ms: performance.now() - t0 });
  return new Promise((res, rej) => {
    let w = null, done = false;
    const page = () => { try { res(inline()); } catch (e) { rej(e); } };       /* le calcul de la page qui lève : la promesse échoue, elle ne reste jamais pendante */
    if (noWorker || typeof Worker !== 'function' || typeof Blob !== 'function' || !window.URL || !URL.createObjectURL) { page(); return; }
    const kill = () => { try { if (w) w.terminate(); } catch (e) { /* ignore */ } w = null; };
    const fail = () => { if (done) return; done = true; kill(); if (job) job.cancel = null; page(); };
    if (job) job.cancel = () => { if (done) return; done = true; kill(); job.cancel = null; rej(new Error('cancelled')); };      /* un calcul périmé : son Worker s'arrête */
    try {
      if (!THR.blob) THR.blob = URL.createObjectURL(new Blob([thrWorkerSrc()], { type: 'text/javascript' }));
      w = new Worker(THR.blob);
      w.onmessage = ev => { if (done) return; done = true; kill(); if (job) job.cancel = null; res({ hv: ev.data, worker: true, ms: performance.now() - t0 }); };
      w.onerror = ev => { if (ev && ev.preventDefault) ev.preventDefault(); fail(); };
      const copy = msg.g.slice();       /* le Worker reçoit une copie du sol, transférée ; la page garde le sien */
      w.postMessage(Object.assign({}, msg, { g: copy }), [copy.buffer]);
    } catch (e) { fail(); }
  });
}

/* Le niveau d'une grille : le plus grand de minZoom à maxNativeZoom tel que R / mpp ≤ 1 024 ; à défaut, minZoom */
function thrLevel(meta, lat, R) {
  for (let z = meta.maxNativeZoom; z >= meta.minZoom; z--) if (R / thrMpp(lat, z) <= THR_PX_MAX) return z;
  return meta.minZoom;
}
/* La grille d'une menace a = { sys, it: { lat, lon }, R } ; opt.noWorker : le calcul sur la page */
function thrBuildGrid(a, th, meta, opt, job) {
  const lat = a.it.lat, lon = a.it.lon, R = a.R, z = thrLevel(meta, lat, R), n = 256 * Math.pow(2, z);
  const cx = Math.floor((lon + 180) / 360 * n), cy = Math.floor(thrMercV(lat) * n);
  const mpp = thrMpp(lat, z), K = Math.ceil(R / mpp), side = 2 * K + 1, px0 = cx - K, py0 = cy - K;
  const t0 = performance.now();
  return thrReadGround(th, meta, z, px0, py0, side).then(rd => {
    const gs = rd.g[K * side + K], zs = gs + THREATS.sensor_height_m[a.sys.sensor];
    const msg = { g: rd.g, side: side, K: K, mpp: mpp, R: R, zs: zs };
    return thrRunCalc(msg, !!(opt && opt.noWorker), job).then(r => {
      return { sys: a.sys, lat: lat, lon: lon, z: z, side: side, K: K, px0: px0, py0: py0, mpp: mpp, R: R, gs: gs, zs: zs, g: rd.g, hv: r.hv,
        ceil: a.sys.ceiling_m, tiles: rd.tiles, worker: r.worker, calcMs: r.ms, ms: performance.now() - t0 };
    });
  });
}

function thrStartGrid(a, th, meta) {
  const key = a.key;
  if (THR.grids.has(key) || THR.jobs.has(key) || THR.bad.has(key)) return;
  const job = { key: key };
  THR.jobs.set(key, job);
  thrBuildGrid(a, th, meta, null, job).then(gr => {
    if (THR.jobs.get(key) !== job) return;           /* périmé : la menace a cessé d'être active, ou le théâtre a changé */
    THR.jobs.delete(key);
    THR.grids.set(key, gr);
    THR.ver++;
    thrSync();
  }, () => {
    if (THR.jobs.get(key) !== job) return;
    THR.jobs.delete(key);
    THR.bad.add(key);
    thrSync();
  });
}

/* ---- la zone : une seule GridLayer, une seule teinte, là où au moins une menace voit à la hauteur H ---- */
function thrReady() {
  const out = [];
  THR.act.forEach(a => { const g = THR.grids.get(a.key); if (g) out.push(g); });
  return out;
}
function thrPaintTile(cv, coords) {
  const c2 = cv.getContext('2d'), img = c2.createImageData(256, 256), d = img.data, H = THR.paint.H;
  let any = false;
  THR.paint.list.forEach(gr => {
    const s = Math.pow(2, gr.z - coords.z), gx0 = coords.x * 256 * s, gy0 = coords.y * 256 * s, size = 256 * s;
    if (gx0 + size <= gr.px0 || gy0 + size <= gr.py0 || gx0 >= gr.px0 + gr.side || gy0 >= gr.py0 + gr.side) return;
    const hv = gr.hv, g = gr.g, side = gr.side, cap = gr.ceil == null ? Infinity : gr.ceil - H + gr.gs;
    for (let py = 0; py < 256; py++) {
      const gy = Math.floor((coords.y * 256 + py + 0.5) * s) - gr.py0;
      if (gy < 0 || gy >= side) continue;
      for (let px = 0; px < 256; px++) {
        const gx = Math.floor((coords.x * 256 + px + 0.5) * s) - gr.px0;
        if (gx < 0 || gx >= side) continue;
        const i = gy * side + gx;
        if (hv[i] <= H && g[i] <= cap) { const k = (py * 256 + px) * 4; d[k] = 200; d[k + 1] = 16; d[k + 2] = 46; d[k + 3] = THR_ZONE_ALPHA; any = true; }
      }
    }
  });
  if (any) c2.putImageData(img, 0, 0);
}
let ThrZone = null;
function thrZoneClass() {
  if (!ThrZone) ThrZone = L.GridLayer.extend({
    createTile: function (coords) {
      const cv = document.createElement('canvas');
      cv.width = 256; cv.height = 256;
      thrPaintTile(cv, coords);
      return cv;
    }
  });
  return ThrZone;
}
function thrZoneSync() {
  const list = THR.state === 'ok' ? thrReady() : [];
  if (!list.length) {
    if (THR.zone) { map.removeLayer(THR.zone); THR.zone = null; THR.zoneSig = ''; }
    THR.paint = { H: 0, list: [] };       /* aucune grille retirée ne reste référencée */
    return;
  }
  const H = thrH(), sig = THR.ver + '|' + H + '|' + list.map(g => g.sys.id + g.lat + g.lon).join(';');
  THR.paint = { H: H, list: list };
  if (!THR.zone) {
    THR.zoneSig = sig;
    THR.zone = new (thrZoneClass())({ pane: 'threats', zIndex: -1, tileSize: 256, minZoom: 3, maxZoom: 18, updateWhenIdle: false, keepBuffer: 2, attribution: t('attr.relief') });
    THR.zone.addTo(map);
  } else if (sig !== THR.zoneSig) {
    THR.zoneSig = sig;
    THR.zone.redraw();
  }
}

/* ---- les cercles : la portée de tir, la détection (sans relief aussi) ---- */
function thrCircles() {
  const sig = THR.act.map(a => a.key + '|' + a.R + '|' + a.sys.detect_m).join(';');
  if (sig === THR.circSig) return;
  THR.circSig = sig;
  THR.circ.clearLayers();
  THR.act.forEach(a => {
    const c = [a.it.lat, a.it.lon], base = { pane: 'threats', interactive: false, fill: false, color: THR_RED, className: 'thr-circle' };
    if (a.sys.kind === 'radar') {
      if (a.sys.detect_m > 0) L.circle(c, Object.assign({ radius: a.sys.detect_m, weight: 1.6, opacity: 1 }, base)).addTo(THR.circ);
      return;
    }
    if (a.sys.detect_m > 0) L.circle(c, Object.assign({ radius: a.sys.detect_m, weight: 1.2, opacity: 0.8, dashArray: '6 6' }, base)).addTo(THR.circ);
    if (a.sys.fire_m > 0) L.circle(c, Object.assign({ radius: a.sys.fire_m, weight: 1.6, opacity: 1 }, base)).addTo(THR.circ);
  });
}

/* ---- la route vue, à sa propre altitude ---- */
function thrGroundNow(tiles, th, meta, lat, lon) {
  const b = meta.bounds;
  if (lat < b[0][0] || lat > b[1][0] || lon < b[0][1] || lon > b[1][1]) return 0;
  const z = meta.maxNativeZoom, n = 256 * Math.pow(2, z), X = (lon + 180) / 360 * n, Y = thrMercV(lat) * n;
  const tx = Math.floor(X / 256), ty = Math.floor(Y / 256), d = tiles.get(thrTileUrl(th, meta, z, tx, ty));
  if (!d) return 0;
  return d[Math.min(255, Math.floor(Y - ty * 256)) * 256 + Math.min(255, Math.floor(X - tx * 256))];
}
/* Les échantillons d'une branche, de 100 m en 100 m, extrémités comprises : { s (m), lat, lon, w (m, la moitié des intervalles qui le touchent) } */
function thrLegSamples(a, b) {
  const L0 = legCalc(a, b), m = L0.km * 1000;
  if (!(m > 0)) return null;
  const ss = [];
  for (let s = 0; s < m - 1e-6; s += THR_SAMPLE_M) ss.push(s);
  ss.push(m);
  return { brg: L0.brg, m: m, list: ss.map((s, i) => {
    const p = i === 0 ? { lat: a.lat, lon: a.lon } : (i === ss.length - 1 ? { lat: b.lat, lon: b.lon } : legDest(a, L0.brg, s / 1000));
    const w = ((i > 0 ? s - ss[i - 1] : 0) + (i < ss.length - 1 ? ss[i + 1] - s : 0)) / 2;
    return { s: s, lat: p.lat, lon: p.lon, w: w };
  }) };
}
/* Les menaces qui jugent la route : celles dont la grille est prête (une menace en échec est seulement écartée) */
function thrRouteActs() { return THR.act.filter(a => !THR.bad.has(a.key)); }
function thrRouteWanted() {
  if (!(DISP.threats && routeShown() && S.points.length > 1 && THR.state === 'ok' && THR.jobs.size === 0)) return false;
  const acts = thrRouteActs();
  return acts.length > 0 && acts.every(a => THR.grids.has(a.key));
}
function thrRouteSig() {
  if (!thrRouteWanted()) return 'off';
  return JSON.stringify([S.theatre, THR.ver, thrRouteActs().map(a => a.key + '|' + a.name), S.points.map(p => [p.lat, p.lon, p.alt, p.altRef])]);
}
function thrRouteSync() {
  const sig = thrRouteSig();
  if (sig === THR.routeSig) return;
  THR.routeSig = sig;
  clearTimeout(THR.routeTimer);
  const seq = ++THR.routeSeq;
  if (sig === 'off') { thrRouteSet(null, []); return; }
  THR.routeTimer = setTimeout(() => { thrRouteCompute(seq); }, 60);
}
function thrRouteCompute(seq) {
  const th = S.theatre, meta = THR.desc && THR.desc.meta, pts = S.points.map(p => ({ lat: p.lat, lon: p.lon, alt: p.alt, altRef: p.altRef })), acts = thrRouteActs();
  const grids = acts.map(a => THR.grids.get(a.key));
  if (!meta || grids.some(g => !g)) return;
  const legs = [null];
  let needGround = false;
  for (let i = 1; i < pts.length; i++) {
    const lg = thrLegSamples(pts[i - 1], pts[i]);
    legs.push(lg);
    if (lg && (pts[i - 1].altRef === 'AGL' || pts[i].altRef === 'AGL')) needGround = true;
  }
  const want = new Map();
  if (needGround) {
    const z = meta.maxNativeZoom, n = 256 * Math.pow(2, z);
    const bb = meta.bounds;
    legs.forEach(lg => { if (lg) lg.list.forEach(sp => {
      if (sp.lat < bb[0][0] || sp.lat > bb[1][0] || sp.lon < bb[0][1] || sp.lon > bb[1][1]) return;       /* hors des bornes : le sol vaut 0 sans lecture */
      const tx = Math.floor((sp.lon + 180) / 360 * n / 256), ty = Math.floor(thrMercV(sp.lat) * n / 256);
      const u = thrTileUrl(th, meta, z, tx, ty);
      if (!want.has(u)) want.set(u, thrTile(u, meta));
    }); });
  }
  const urls = Array.from(want.keys());
  Promise.all(urls.map(u => want.get(u))).then(arr => {
    if (seq !== THR.routeSeq) return;
    const tiles = new Map();
    urls.forEach((u, i) => tiles.set(u, arr[i]));
    const seen = {}, flat = [];
    for (let i = 1; i < pts.length; i++) {
      const lg = legs[i], a = pts[i - 1], b = pts[i];
      if (!lg) continue;
      const mixed = a.altRef !== b.altRef;
      const gA = a.altRef === 'AGL' ? thrGroundNow(tiles, th, meta, a.lat, a.lon) : 0, gB = b.altRef === 'AGL' ? thrGroundNow(tiles, th, meta, b.lat, b.lon) : 0;
      const kms = acts.map(() => 0);
      lg.list.forEach((sp, k) => {
        const f = sp.s / lg.m;
        let alt;
        if (!mixed && a.altRef === 'AGL') alt = a.alt + (b.alt - a.alt) * f + thrGroundNow(tiles, th, meta, sp.lat, sp.lon);
        else if (!mixed) alt = a.alt + (b.alt - a.alt) * f;
        else { const ea = a.altRef === 'AGL' ? a.alt + gA : a.alt, eb = b.altRef === 'AGL' ? b.alt + gB : b.alt; alt = ea + (eb - ea) * f; }
        const u = (sp.lon + 180) / 360, v = thrMercV(sp.lat);
        let any = false;
        grids.forEach((gr, q) => {
          const nn = 256 * Math.pow(2, gr.z), gx = Math.floor(u * nn) - gr.px0, gy = Math.floor(v * nn) - gr.py0;
          if (gx < 0 || gy < 0 || gx >= gr.side || gy >= gr.side) return;
          const idx = gy * gr.side + gx;
          if (!(alt - gr.g[idx] >= gr.hv[idx])) return;
          if (gr.ceil != null && alt - gr.gs > gr.ceil) return;
          kms[q] += sp.w / 1000;
          any = true;
        });
        flat.push({ a: a, lg: lg, k: k, sp: sp, seen: any });
      });
      const items = [];
      acts.forEach((ac, q) => { if (kms[q] > 0) items.push({ name: ac.name, km: kms[q] }); });
      items.sort((x, y) => y.km - x.km);
      if (items.length) seen[i] = items;
    }
    /* une suite d'échantillons vus (d'une branche à l'autre si les deux bouts le sont) : de la moitié de l'intervalle avant le premier à la moitié de l'intervalle après le dernier */
    const runs = [];
    let cur = null;
    const edge = (e, dir) => {
      const l = e.lg.list, nb = l[e.k + dir];
      return nb ? thrPointAt(e.a, e.lg, e.sp.s + (nb.s - e.sp.s) / 2) : { lat: e.sp.lat, lon: e.sp.lon };
    };
    flat.forEach((e, n) => {
      if (e.seen) {
        if (!cur) { cur = [edge(e, -1)]; }
        cur.push({ lat: e.sp.lat, lon: e.sp.lon });
        if (!(flat[n + 1] && flat[n + 1].seen)) { cur.push(edge(e, 1)); runs.push(cur); cur = null; }
      }
    });
    thrRouteSet(seen, runs);
  });
}
function thrPointAt(a, lg, s) { return s <= 0 ? { lat: a.lat, lon: a.lon } : (s >= lg.m ? lg.list[lg.list.length - 1] : legDest(a, lg.brg, s / 1000)); }
function thrRouteSet(seen, runs) {
  const sig = JSON.stringify(seen || null);
  const was = JSON.stringify(THR.seen || null);
  THR.seen = seen;
  const hs = JSON.stringify(runs.map(r => r.map(p => [Math.round(p.lat * 1e6), Math.round(p.lon * 1e6)])));
  if (hs !== THR.haloSig) {
    THR.haloSig = hs;
    THR.halo.clearLayers();
    runs.forEach(r => {
      L.polyline(r.map(p => [p.lat, p.lon]), { pane: 'thrroute', interactive: false, color: '#ffd400', weight: 20, opacity: 0.92, lineCap: 'butt', lineJoin: 'round', className: 'thr-halo' }).addTo(THR.halo);
    });
  }
  if (sig !== was) renderNav();
}
/* La ligne sous la ligne d'une branche vue, à la feuille de navigation */
function thrNavRow(i) {
  const items = THR.seen && THR.seen[i];
  if (!items || !items.length) return '';
  const txt = t('nav.thr', { l: items.map(x => t('nav.thr.item', { n: x.name, d: fmtDist(x.km) })).join(' · ') });
  return '<tr class="thr"><td></td><td colspan="3">' + esc(txt) + '</td></tr>';
}

/* ---- le cartouche #rp-thr ---- */
function thrBoxEl() {
  if (THR.box) return THR.box;
  const el = document.createElement('div');
  el.id = 'rp-thr'; el.hidden = true;
  map.getContainer().appendChild(el);
  L.DomEvent.disableClickPropagation(el);
  L.DomEvent.disableScrollPropagation(el);
  el.addEventListener('input', ev => { if (ev.target && ev.target.id === 'thr-range') thrSetRank(parseInt(ev.target.value, 10)); });
  el.addEventListener('click', ev => {
    const f = ev.target.closest ? ev.target.closest('.thr-fold') : null;
    if (f) { THR.open = !THR.open; thrFoldApply(); return; }
    const b = ev.target.closest ? ev.target.closest('.thr-b') : null;
    if (b && !b.disabled) thrSetRank(thrRank() + parseInt(b.dataset.d, 10));
  });
  THR.box = el;
  return el;
}
function thrSetRank(r) {
  if (!(r >= 0)) return;
  DISP.thrStep = Math.max(0, Math.min(thrTop(), r));
  saveDisplay();
  thrBoxValue();
  if (!THR.raf) THR.raf = requestAnimationFrame(() => { THR.raf = 0; thrZoneSync(); });
}
function thrBoxValue() {
  const el = THR.box;
  if (!el || el.hidden) return;
  const r = thrRank(), top = thrTop();
  const v = el.querySelector('#thr-v'), rg = el.querySelector('#thr-range');
  if (v) v.textContent = thrHText();
  const lz = el.querySelector('#thr-lz');
  if (lz) lz.textContent = t('thr.leg.zone', { h: thrAlt(thrH()) });
  if (rg) { rg.value = String(r); rg.setAttribute('aria-valuetext', thrHText()); }
  el.querySelectorAll('.thr-b').forEach(b => { b.disabled = parseInt(b.dataset.d, 10) < 0 ? r <= 0 : r >= top; });
}
function thrBoxRender() {
  if (!mapCreated || !THR.circ) return;
  const el = thrBoxEl();
  const show = THR.act.length > 0 && tapMode !== 'draw' && tapMode !== 'ruler' && !EXP.on;
  el.hidden = !show;
  if (!show) return;
  const W = $('map').clientWidth, narrow = W < THR_NARROW, top = thrTop(), st = THR.state;
  const hasZone = st === 'ok' || st === 'wait';
  const sig = [CURRENT_LANG, S.units.altitude, narrow ? 1 : 0, hasZone ? 1 : 0, st, top].join('|');
  if (sig !== THR.boxSig) {
    THR.boxSig = sig;
    const src = t(st === 'none' ? 'thr.src.none' : st === 'err' ? 'thr.src.err' : 'thr.src.relief');
    const title = '<b class="thr-t">' + esc(t('thr.title')) + '</b>';
    el.classList.toggle('thr-pill', narrow);
    if (narrow) {
      el.innerHTML = title + (hasZone ? '<span class="thr-v" id="thr-v"></span><button type="button" class="thr-b" data-d="-1" aria-label="' + esc(t('thr.lower')) + '">−</button>' +
        '<button type="button" class="thr-b" data-d="1" aria-label="' + esc(t('thr.higher')) + '">+</button><button type="button" class="thr-fold"></button>' : '<span class="thr-src">' + esc(src) + '</span>');
    } else {
      let h = '<div class="thr-h">' + title + '<span class="thr-src">' + esc(src) + '</span></div>';
      if (hasZone) {
        const marks = [0, 2, 4, 6, 9].filter(k => k <= top);
        if (marks.indexOf(top) === -1) marks.push(top);
        const steps = thrSteps();
        h += '<div class="thr-r"><label for="thr-range">' + esc(t('thr.h')) + '</label><b id="thr-v"></b></div>' +
          '<input type="range" id="thr-range" min="0" max="' + top + '" step="1" value="0" aria-label="' + esc(t('thr.h')) + '">' +
          '<div class="thr-ticks">' + marks.map(k => '<span class="thr-tk" style="left: calc(8px + (100% - 16px) * ' + (top ? k / top : 0) + ')">' + esc(thrNum(steps[k])) + '</span>').join('') + '</div>';
      }
      h += '<div class="thr-leg">' + (hasZone ? '<span><i class="thr-sw zone"></i><span id="thr-lz"></span></span>' : '') +
        '<span><i class="thr-sw fire"></i>' + esc(t('thr.leg.fire')) + '</span><span><i class="thr-sw det"></i>' + esc(t('thr.leg.det')) + '</span>' +
        (hasZone ? '<span><i class="thr-sw halo"></i>' + esc(t('thr.leg.route')) + '</span>' : '') + '</div>';
      el.innerHTML = h;
    }
  }
  thrFoldApply();
  thrBoxValue();
  thrBoxPlace();
}
/* La pastille avec la teinte : repliée (titre, valeur, « ± ») ou dépliée (« − », « + », « ‹ ») ; le bouton n'est jamais refait par le geste, le focus y reste */
function thrFoldApply() {
  const el = THR.box;
  if (!el) return;
  const f = el.querySelector('.thr-fold');
  el.classList.toggle('thr-shut', !!f && !THR.open);
  if (!f) return;
  f.textContent = THR.open ? '‹' : '±';
  f.setAttribute('aria-expanded', THR.open ? 'true' : 'false');
  f.setAttribute('aria-label', t(THR.open ? 'thr.fold' : 'thr.set'));
}
/* À chaque ouverture du RP (le shell le réaffiche) : repliée */
function thrFoldReset() { THR.open = false; thrFoldApply(); }
/* En pastille (calée à droite, right: 8px) : le bas de la pastille est 6 px au-dessus du haut de la mention de la carte, mesuré ; le cartouche large ne reçoit rien */
function thrBoxPlace() {
  const el = THR.box;
  if (!el) return;
  if (!el.classList.contains('thr-pill')) {
    if (el.style.bottom) { el.style.removeProperty('bottom'); if (!el.getAttribute('style')) el.removeAttribute('style'); }
    return;
  }
  const c = map.getContainer(), a = map.attributionControl && map.attributionControl.getContainer();
  const ar = a ? a.getBoundingClientRect() : null;
  if (!ar || !ar.width || !ar.height) { el.style.removeProperty('bottom'); if (!el.getAttribute('style')) el.removeAttribute('style'); return; }       /* pas de mention vue : le bas de la feuille de style */
  const cr = c.getBoundingClientRect();
  el.style.bottom = Math.max(0, cr.top + c.clientTop + c.clientHeight - ar.top + 6) + 'px';
}

/* ---- la synchronisation : un seul point d'entrée, peu coûteux quand rien n'a changé ---- */
function thrSync() {
  if (!mapCreated || !THR.circ) return;
  const act = thrActive(), th = S.theatre;
  THR.act = act;
  let state = '';
  if (act.length) {
    if (!reliefTheatre(th)) state = 'none';
    else {
      let d = THR.desc;
      if (!d || d.th !== th) {
        const rec = { th: th, st: 'wait', meta: null };
        THR.desc = d = rec;
        reliefDesc(th).then(m => { rec.st = 'ok'; rec.meta = m; if (THR.desc === rec) thrSync(); }, () => { rec.st = 'err'; if (THR.desc === rec) thrSync(); });
      }
      state = d.st;
    }
  }
  THR.state = state;
  const keys = new Set(act.map(a => a.key));
  let changed = false;
  THR.grids.forEach((g, k) => { if (!keys.has(k) || state !== 'ok') { THR.grids.delete(k); changed = true; } });
  THR.jobs.forEach((j, k) => { if (!keys.has(k) || state !== 'ok') { if (j.cancel) j.cancel(); THR.jobs.delete(k); } });
  THR.bad.forEach(k => { if (!keys.has(k) || state !== 'ok') THR.bad.delete(k); });
  if (changed) THR.ver++;
  if (state === 'ok') act.forEach(a => thrStartGrid(a, th, THR.desc.meta));
  thrCircles();
  thrZoneSync();
  thrRouteSync();
  thrBoxRender();
}
function thrInit() {
  THR.circ = L.layerGroup().addTo(map);
  THR.halo = L.layerGroup().addTo(map);
  map.on('resize', thrBoxRender);
  const at = map.attributionControl && map.attributionControl.getContainer();
  if (at && window.ResizeObserver) new ResizeObserver(() => thrBoxPlace()).observe(at);       /* la mention change de hauteur (relief, fond, langue, largeur) : la pastille suit */
}
/* Un calcul de grille pour les essais et les mesures : { ms, calcMs, worker, z, side, tiles } */
function thrProbe(sysId, lat, lon, noWorker) {
  const sys = THR_BY_ID[sysId], th = S.theatre, meta = THR.desc && THR.desc.meta;
  if (!sys || !meta) return Promise.reject(new Error('no relief'));
  return thrBuildGrid({ sys: sys, it: { lat: lat, lon: lon }, R: sys.kind === 'radar' ? sys.detect_m : sys.fire_m }, th, meta, { noWorker: !!noWorker });
}
"""
