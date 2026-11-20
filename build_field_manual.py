#!/usr/bin/env python3
"""Build the DCS Field Manual HTML module — monofichier, offline, Mission Plan suite."""

import json
import os
import base64
import re
import subprocess
import sys
import tempfile
from shell_only_block import build_block as build_shell_only_block
from version_block import SUITE_VERSION
from ui_block import build_bar_css, build_bar_js
# La garde du module seul : premier élément du <body> (build_mission_plan.py la vérifie dans le dist/)
SHELL_ONLY_TAG = '<script data-lang-key="lang_v1">\n' + build_shell_only_block() + '</script>\n'

CONTRAST_CSS = r"""
/* MP-20 begin */
/* Contrastes (texte sous 18 px, 4,5 : 1 au moins) : couleur du texte seule, la palette commune ne bouge pas. */
:where(body[data-theme="cw-nato"]) .tb-brand-short { color: #8b9aaf; }
:where(body[data-theme="cw-nato"]) .tb-classif { color: #d4847b; }
:where(body[data-theme="cw-soviet"]) .tb-classif { color: #be7d7d; }
:where(body[data-theme="modern-nato"]) .tb-classif { color: #898989; }
:where(body[data-theme="modern-east"]) .tb-classif { color: #bd7979; }
/* MP-20 end */
"""

HERE = os.path.dirname(os.path.abspath(__file__))

BAR_CSS = build_bar_css()      # la séquence de réduction de la barre : la même que celle du bloc d'interface commun (ui_block.py), pas une copie
BAR_JS = build_bar_js()

MODULE_ID   = 'fm'

# ── Assets ──────────────────────────────────────────────────────────────────────

ASSETS_PATH = os.path.join(HERE, 'assets.json')
if not os.path.isfile(ASSETS_PATH):
    raise SystemExit(f"[ERREUR] Entrée manquante : {ASSETS_PATH} (assets.json attendu à la racine du dépôt)")
with open(ASSETS_PATH) as f:
    A = json.load(f)
print(f'✓ assets.json chargé depuis {ASSETS_PATH}')

def b64_font(key):
    return A.get(key, '')

# ── Images ──────────────────────────────────────────────────────────────────────

TILES_DIR = os.path.join(HERE, 'tiles')

def encode_image(filename):
    """Encode une image en data URI base64. Ne jamais redimensionner (règle REX)."""
    path = os.path.join(TILES_DIR, filename)
    if not os.path.isfile(path):
        raise SystemExit(f"[ERREUR] Entrée manquante : {path} (tuile {filename} attendue dans tiles/)")
    with open(path, 'rb') as f:
        b64 = base64.b64encode(f.read()).decode('ascii')
    ext = filename.rsplit('.', 1)[-1].lower()
    mime = 'image/webp' if ext == 'webp' else f'image/{ext}'
    return f'data:{mime};base64,{b64}'

RS_TILE    = encode_image('rs.webp')
FM_COVER   = encode_image('fm_cover.webp')
HQ_TILE    = encode_image('hq.webp')
BG_TILE    = encode_image('bg.webp')
DG_TILE    = encode_image('kg.webp')
RP_TILE    = encode_image('rp.webp')
FC_TILE    = encode_image('fc.webp')

if RS_TILE:
    print(f'✓ rs.webp embarqué ({len(RS_TILE)//1024} Ko base64)')
else:
    print('⚠ rs.webp introuvable', file=sys.stderr)

if HQ_TILE:
    print(f'✓ hq.webp embarqué ({len(HQ_TILE)//1024} Ko base64)')
else:
    print('⚠ hq.webp introuvable', file=sys.stderr)

if BG_TILE:
    print(f'✓ bg.webp embarqué ({len(BG_TILE)//1024} Ko base64)')
else:
    print('⚠ bg.webp introuvable', file=sys.stderr)

if DG_TILE:
    print(f'✓ kg.webp embarqué ({len(DG_TILE)//1024} Ko base64)')
else:
    print('⚠ kg.webp introuvable', file=sys.stderr)

if RP_TILE:
    print(f'✓ rp.webp embarqué ({len(RP_TILE)//1024} Ko base64)')
else:
    print('⚠ rp.webp introuvable', file=sys.stderr)

if FM_COVER:
    print(f'✓ fm_cover.webp embarqué ({len(FM_COVER)//1024} Ko base64)')
else:
    print('⚠ fm_cover.webp absent — fallback couverture SVG/typo activé', file=sys.stderr)

# ── Kraft SVG variants (identique à Recon Station) ──────────────────────────────

def _kraft_variant(b64svg, bg_color, grain_color):
    if not b64svg:
        return ''
    svg_bytes = base64.b64decode(b64svg)
    svg_str   = svg_bytes.decode('utf-8')
    svg_str   = svg_str.replace('#d6c7a3', bg_color).replace('#ccbe99', grain_color)
    return base64.b64encode(svg_str.encode('utf-8')).decode('ascii')

KRAFT_RAW   = A.get('KRAFT_SVG', '')
KRAFT_NATO  = _kraft_variant(KRAFT_RAW, '#d6c7a3', '#ccbe99')
KRAFT_SOV   = _kraft_variant(KRAFT_RAW, '#d4c075', '#c8b060')
KRAFT_MNATO = _kraft_variant(KRAFT_RAW, '#e4dfd2', '#d8d4c8')
KRAFT_MEAST = _kraft_variant(KRAFT_RAW, '#c8c1b2', '#bcb5a6')

# ── Polices ──────────────────────────────────────────────────────────────────────

SPECIAL_ELITE_B64 = b64_font('SPECIAL_ELITE')
STARDOS_400_B64   = b64_font('STARDOS_400')
STARDOS_700_B64   = b64_font('STARDOS_700')
OSWALD_500_B64    = b64_font('OSWALD_500')
OSWALD_700_B64    = b64_font('OSWALD_700')
ROBOTO_MONO_400_B64 = b64_font('ROBOTO_MONO_400')

def font_face_css():
    """Génère les @font-face. Fallback CDN si base64 absent."""
    parts = []
    if SPECIAL_ELITE_B64:
        parts.append(f"""@font-face {{
  font-family: 'Special Elite';
  font-weight: 400;
  font-display: swap;
  src: url('data:font/woff2;base64,{SPECIAL_ELITE_B64}') format('woff2');
}}""")
    else:
        parts.append("/* Special Elite : fallback CDN */")

    # Stardos Stencil 400 : le tampon de décor de la barre
    if STARDOS_400_B64:
        parts.append(f"""@font-face {{
  font-family: 'Stardos Stencil';
  font-weight: 400;
  font-display: swap;
  src: url('data:font/woff2;base64,{STARDOS_400_B64}') format('woff2');
}}""")

    if STARDOS_700_B64:
        parts.append(f"""@font-face {{
  font-family: 'Stardos Stencil';
  font-weight: 700;
  font-display: swap;
  src: url('data:font/woff2;base64,{STARDOS_700_B64}') format('woff2');
}}""")
    else:
        parts.append("/* Stardos Stencil : fallback CDN */")

    if OSWALD_500_B64:
        parts.append(f"""@font-face {{
  font-family: 'Oswald';
  font-weight: 500;
  font-display: swap;
  src: url('data:font/woff2;base64,{OSWALD_500_B64}') format('woff2');
}}""")
    if OSWALD_700_B64:
        parts.append(f"""@font-face {{
  font-family: 'Oswald';
  font-weight: 700;
  font-display: swap;
  src: url('data:font/woff2;base64,{OSWALD_700_B64}') format('woff2');
}}""")

    # Roboto Mono 400 : le bouton retour que le shell ajoute à la barre l'emploie ; une police n'apparaît jamais sans sa face embarquée (R295)
    if ROBOTO_MONO_400_B64:
        parts.append(f"""@font-face {{
  font-family: 'Roboto Mono';
  font-weight: 400;
  font-display: swap;
  src: url('data:font/woff2;base64,{ROBOTO_MONO_400_B64}') format('woff2');
}}""")
    return '\n'.join(parts)

FONT_CDN = ''   # aucune police distante : toutes sont embarquées (R295)

# ── Couverture HTML ──────────────────────────────────────────────────────────────

if FM_COVER:
    COVER_HTML = f"""<div class="cover-wrap">
        <div class="cover-img-box" style="background-image:url('{FM_COVER}')">
          <div class="cover-overlay">
            <span class="cover-suite">DCS · MISSION PLAN</span>
            <span class="cover-ref">FM-MP-01</span>
          </div>
        </div>
      </div>"""
else:
    COVER_HTML = """<div class="cover-wrap cover-svg">
        <div class="cover-svg-inner">
          <div class="cover-classif-top">DECLASSIFIED — UNCLASSIFIED</div>
          <div class="cover-title-main">FIELD MANUAL</div>
          <div class="cover-title-sub">DCS · MISSION PLAN</div>
          <div class="cover-ref-box">FM-MP-01</div>
          <div class="cover-stamp">APPROVED FOR PUBLIC RELEASE</div>
        </div>
      </div>"""

# ── RS tile src (fallback placeholder) ──────────────────────────────────────────

RS_TILE_SRC = RS_TILE if RS_TILE else "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"
HQ_TILE_SRC = HQ_TILE if HQ_TILE else "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"
BG_TILE_SRC = BG_TILE if BG_TILE else "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"
DG_TILE_SRC = DG_TILE if DG_TILE else "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"
RP_TILE_SRC = RP_TILE if RP_TILE else "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"
FC_TILE_SRC = FC_TILE

# ── Schémas générés (BG « Ce qui alimente quoi », anatomie de la datacard) ──
# Règle de lisibilité : la couleur d'un module marque (trait, aplat à 20 %), l'encre écrit.

from fm_schemas_block import (NF, fr_typo, _esc, SCHEMAS_CSS, s0_html, build_bg_svg, build_dg_anatomy_svg, panel_html, panel_ids, TABLE_IDS)
from fm_planches_block import PLANCHES_CSS, PLANCHE_ERRORS, PLATES, build_plate_hq, build_plate_fc, build_plate_dg, build_plate_rp, build_plate_bg, build_plate_rs, build_plate_start, check_report as planche_report

_NBSP_FINE = NF   # espace fine insécable (typographie française)

BG_SVG = build_bg_svg()
DG_ANATOMY_SVG = build_dg_anatomy_svg()
# Les planches d'écran : l'écran de l'outil au trait, des bulles numérotées, une légende numérotée ; leurs libellés viennent du dictionnaire de l'outil
HQ_PLATE_HTML = build_plate_hq()
FC_PLATE_HTML = build_plate_fc()
DG_PLATE_HTML = build_plate_dg()
RP_PLATE_HTML = build_plate_rp()
BG_PLATE_HTML = build_plate_bg()
RS_PLATE_HTML = build_plate_rs()
START_PLATE_HTML = build_plate_start()

BG_LEGEND_FR = (f'Fig. 1 — Comment les saisies d’une section alimentent les autres, et ce que lisent les autres outils. '
                f'S{_NBSP_FINE}: saisi en Standard{_NBSP_FINE}; A{_NBSP_FINE}: en Avancé{_NBSP_FINE}; S·A{_NBSP_FINE}: dans les deux.')
BG_LEGEND_EN = ('Fig. 1 — How entries in one section feed the others, and what the other tools read. '
                'S: entered in Standard; A: in Advanced; S·A: in both.')

# ── CSS additionnel : boîtes de schéma, zoom ─────────────────────────────────────

FM_EXTRA_CSS = SCHEMAS_CSS + PLANCHES_CSS + r'''
/* ── SCHÉMAS : la couleur du module marque, l'encre écrit ── */
.sv-box {
  fill: var(--paper-light);
}
.sv-m-hq { fill: color-mix(in srgb, #4FB286 20%, var(--paper-light)); stroke: #4FB286; }
.sv-m-bg { fill: color-mix(in srgb, #c0892a 20%, var(--paper-light)); stroke: #c0892a; }
.sv-m-rs { fill: color-mix(in srgb, #C95A9C 20%, var(--paper-light)); stroke: #C95A9C; }
.sv-m-dg { fill: color-mix(in srgb, #4f7a8e 20%, var(--paper-light)); stroke: #4f7a8e; }
.sv-m-rp { fill: color-mix(in srgb, #7ac97a 20%, var(--paper-light)); stroke: #7ac97a; }
.sv-pill { fill: var(--olive-dark); }
.sv-pill-t { fill: var(--paper-light); }
.fm-schema.tall svg { max-height: 425px; }

/* ── ZOOM : image ou schéma ouvert plein écran ── */
.fm-zoom-host { position: relative; }
[data-zoomable] { cursor: zoom-in; }
[data-zoomable]:focus-visible {
  outline: 2px solid var(--amber);
  outline-offset: 2px;
}
.fm-hero-img[data-zoomable]:focus-visible,
.cover-img-box[data-zoomable]:focus-visible { outline-offset: -3px; }
.fm-zoom-badge {
  position: absolute;
  top: 8px; right: 8px;
  z-index: 3;
  width: 26px; height: 26px;
  border-radius: 3px;
  background: rgba(26, 30, 16, .66);
  color: #f0e8d0;
  font-family: system-ui, 'Segoe UI Symbol', 'DejaVu Sans', sans-serif;
  font-size: 15px;
  line-height: 26px;
  text-align: center;
  opacity: .72;
  pointer-events: none;
  transition: opacity .12s;
}
.fm-zoom-badge::after { content: "\2922"; }
.fm-hero > .fm-zoom-badge { right: 38px; }
.fm-zoom-host:hover > .fm-zoom-badge,
.fm-zoom-host:focus-within > .fm-zoom-badge { opacity: 1; }

body.zm-open #fm-root { overflow: hidden; }
.zm {
  position: fixed;
  inset: 0;
  z-index: 5000;
  background: rgba(0, 0, 0, .94);
  color: var(--paper);
  font-family: var(--f-ui);
}
.zm[hidden] { display: none !important; }
.zm-stage {
  position: absolute;
  inset: 0;
  overflow: hidden;
  touch-action: none;
  overscroll-behavior: none;
  -webkit-user-select: none;
  user-select: none;
  cursor: default;
}
.zm.zoomed .zm-stage { cursor: grab; }
.zm.zoomed .zm-stage:active { cursor: grabbing; }
.zm-box {
  position: absolute;
  left: 0; top: 0;
  color: var(--ink);
  font-family: var(--f-typewriter);
  will-change: transform;
}
.zm-box img {
  display: block;
  width: 100%;
  height: auto;
  -webkit-user-drag: none;
  box-shadow: 0 0 0 1px var(--khaki), 0 10px 40px rgba(0, 0, 0, .6);
}
.zm-box .fm-schema {
  margin: 0;
  border: 0;
  padding: calc(20px * var(--zs, 1));
  background-color: var(--paper);
  background-image: linear-gradient(rgba(0, 0, 0, .10), rgba(0, 0, 0, .10)), var(--kraft-bg);
  background-size: auto, 400px 566px;
  box-shadow: 0 0 0 1px var(--khaki), 0 10px 40px rgba(0, 0, 0, .6);
}
.zm-box .fm-schema svg { max-height: none; width: 100%; height: auto; }
.zm-box .fm-schema-legend {
  margin-top: calc(10px * var(--zs, 1));
  font-size: calc(10px * var(--zs, 1));
  letter-spacing: calc(1.5px * var(--zs, 1));
}
.zm-bar {
  position: absolute;
  left: 50%;
  bottom: max(14px, env(safe-area-inset-bottom));
  transform: translateX(-50%);
  display: flex;
  gap: 8px;
  z-index: 2;
}
.zm-btn {
  min-width: 44px;
  height: 44px;
  padding: 0 14px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-family: var(--f-ui);
  font-size: 13px;
  letter-spacing: 2px;
  text-transform: uppercase;
  line-height: 1;
  color: var(--paper);
  background: linear-gradient(180deg, var(--olive-dark) 0%, var(--olive-deep) 100%);
  border: 1px solid var(--khaki);
  border-radius: 0;
  cursor: pointer;
  box-shadow: 0 2px 10px rgba(0, 0, 0, .5);
}
.zm-btn:hover { background: var(--olive); border-color: var(--fm-accent); }
.zm-btn:focus-visible { background: var(--olive); }
.zm-sym { width: 44px; padding: 0; font-size: 24px; letter-spacing: 0; text-transform: none; }
.zm-close {
  position: absolute;
  top: max(10px, env(safe-area-inset-top));
  right: max(10px, env(safe-area-inset-right));
  z-index: 2;
  font-size: 28px;
}
'''

ZOOM_HTML = '''<!-- ======== ZOOM (images et schémas) ======== -->
<div id="fm-zoom" class="zm" role="dialog" aria-modal="true" hidden>
  <div class="zm-stage"><div class="zm-box"></div></div>
  <div class="zm-bar" role="toolbar">
    <button type="button" class="zm-btn zm-sym" data-zm="out">&minus;</button>
    <button type="button" class="zm-btn" data-zm="fit"></button>
    <button type="button" class="zm-btn zm-sym" data-zm="in">+</button>
  </div>
  <button type="button" class="zm-btn zm-sym zm-close" data-zm="close">&times;</button>
</div>'''

# ── JS : zoom (vectoriel : on agrandit la largeur du SVG, jamais une capture) ────

ZOOM_JS = r'''
// ── Zoom des images et des schémas ────────────────────────────
var ZM_MAX = 4;          // zoom maximal, relatif à l'ajustement
var ZM_STEP = 1.5;       // pas des boutons + et −
var ZM_REF = 812;        // largeur de référence d'un panneau de schéma (échelle --zs)
var ZM_SIDE = 16, ZM_TOP = 60, ZM_BOTTOM = 72;   // marges réservées autour de l'ajustement

var zm = {
  dlg: null, stage: null, box: null, opener: null, schema: false,
  natW: 1, natH: 1, fitW: 1, s: 1, x: 0, y: 0,
  ptrs: {}, drag: null, pinch: null, moved: false, lastTap: null, ghost: null
};

function zmBtnLabels() {
  return [
    ['out', 'zoom.out'], ['in', 'zoom.in'], ['close', 'zoom.close']
  ];
}

function fmZoomRefresh() {
  document.querySelectorAll('[data-zoomable]').forEach(function(el) {
    el.setAttribute('aria-label', t('zoom.open'));
    el.setAttribute('title', t('zoom.open'));
  });
  if (!zm.dlg) return;
  zmBtnLabels().forEach(function(p) {
    var b = zm.dlg.querySelector('[data-zm="' + p[0] + '"]');
    if (b) { b.setAttribute('aria-label', t(p[1])); b.setAttribute('title', t(p[1])); }
  });
  var fit = zm.dlg.querySelector('[data-zm="fit"]');
  if (fit) { fit.textContent = t('zoom.fit'); fit.setAttribute('aria-label', t('zoom.fit')); fit.setAttribute('title', t('zoom.fit')); }
}

function zmView() {
  return { w: zm.stage.clientWidth, h: zm.stage.clientHeight };
}

function zmFitRect() {
  var v = zmView();
  return {
    x: ZM_SIDE, y: ZM_TOP,
    w: Math.max(80, v.w - 2 * ZM_SIDE),
    h: Math.max(80, v.h - ZM_TOP - ZM_BOTTOM)
  };
}

function zmSetWidth(w) {
  zm.box.style.width = w + 'px';
  if (zm.schema) zm.box.style.setProperty('--zs', String(w / ZM_REF));
}

function zmComputeFit() {
  var f = zmFitRect(), aspect;
  if (zm.schema) {
    zmSetWidth(1000);
    aspect = zm.box.offsetHeight / 1000;
  } else {
    aspect = zm.natH / zm.natW;
  }
  zm.fitW = Math.min(f.w, f.h / aspect);
}

function zmClamp(v, lo, hi) { return Math.max(lo, Math.min(hi, v)); }

function zmApply() {
  zm.s = zmClamp(zm.s, 1, ZM_MAX);
  var w = zm.fitW * zm.s;
  zmSetWidth(w);
  var h = zm.box.offsetHeight;
  var v = zmView(), f = zmFitRect();
  if (zm.s <= 1.0001) {
    zm.s = 1;
    zm.x = f.x + (f.w - w) / 2;
    zm.y = f.y + (f.h - h) / 2;
  } else {
    // plus grand que l'écran : pas de bord vide ; plus petit : entièrement visible
    zm.x = (w >= v.w) ? zmClamp(zm.x, v.w - w, 0) : zmClamp(zm.x, 0, v.w - w);
    zm.y = (h >= v.h) ? zmClamp(zm.y, v.h - h, 0) : zmClamp(zm.y, 0, v.h - h);
  }
  zm.box.style.transform = 'translate3d(' + zm.x + 'px,' + zm.y + 'px,0)';
  zm.dlg.classList.toggle('zoomed', zm.s > 1.0001);
}

function zmZoomAt(ns, ax, ay) {
  ns = zmClamp(ns, 1, ZM_MAX);
  if (ns === zm.s) return;
  var r = ns / zm.s;
  zm.x = ax - (ax - zm.x) * r;
  zm.y = ay - (ay - zm.y) * r;
  zm.s = ns;
  zmApply();
}

function zmZoomCenter(ns) {
  var v = zmView();
  zmZoomAt(ns, v.w / 2, v.h / 2);
}

function zmFit() {
  zm.s = 1;
  zmApply();
}

// Cloner un schéma : identifiants uniques (marqueurs, motifs) pour que les pointes de flèche s'y affichent
function zmCloneSchema(el) {
  var c = el.cloneNode(true);
  var badge = c.querySelector('.fm-zoom-badge');
  if (badge) badge.remove();
  ['role', 'tabindex', 'aria-label', 'title', 'data-zoomable'].forEach(function(a) { c.removeAttribute(a); });
  c.classList.remove('fm-zoom-host');
  var ids = [];
  c.querySelectorAll('[id]').forEach(function(n) { ids.push(n.id); });
  if (ids.length) {
    var all = c.querySelectorAll('*');
    for (var i = 0; i < all.length; i++) {
      var n = all[i];
      if (n.id) n.id = 'zm-' + n.id;
      var attrs = n.attributes;
      for (var j = 0; j < attrs.length; j++) {
        var v = attrs[j].value;
        if (v.indexOf('url(#') === -1) continue;
        ids.forEach(function(id) { v = v.split('url(#' + id + ')').join('url(#zm-' + id + ')'); });
        n.setAttribute(attrs[j].name, v);
      }
    }
  }
  return c;
}

function zmOpen(el) {
  if (typeof fmTocSet === 'function') fmTocSet(false, false);   // le zoom ne cohabite pas avec le sommaire
  zm.opener = el;
  zm.schema = el.classList.contains('fm-schema');
  zm.box.innerHTML = '';
  zm.box.style.width = '';
  zm.box.style.removeProperty('--zs');
  var label = '';
  var nat = null, img = null;
  if (zm.schema) {
    var svgs = Array.prototype.slice.call(el.querySelectorAll('svg'));
    var svg = svgs.filter(function (v) { return v.getClientRects().length; })[0] || svgs[0];   // le premier SVG affiché : au téléphone, la variante haute
    label = svg ? (svg.getAttribute('aria-label') || '') : '';
    zm.box.appendChild(zmCloneSchema(el));
  } else {
    var src = el.currentSrc || el.src || '';
    if (!src) {
      var m = /url\(["']?([^"')]+)["']?\)/.exec(getComputedStyle(el).backgroundImage || '');
      src = m ? m[1] : '';
    }
    label = el.getAttribute('alt') || 'Field Manual';
    nat = el.naturalWidth ? [el.naturalWidth, el.naturalHeight] : (el._fmNat || null);
    img = new Image();
    img.alt = '';
    img.draggable = false;
    zm.box.appendChild(img);
    img.src = src;
  }
  zm.dlg.setAttribute('aria-label', label);
  zm.dlg.hidden = false;
  document.body.classList.add('zm-open');
  var root = document.getElementById('fm-root'), bar = document.querySelector('.toolbar');
  if (root) root.inert = true;
  if (bar) bar.inert = true;
  zm.ptrs = {}; zm.drag = null; zm.pinch = null; zm.lastTap = null;
  fmZoomRefresh();
  var ready = function() {
    zmComputeFit();
    zm.s = 1;
    zmApply();
  };
  if (zm.schema) {
    ready();
  } else if (nat) {
    zm.natW = nat[0]; zm.natH = nat[1];
    ready();
  } else {
    img.onload = function() {
      zm.natW = img.naturalWidth || 1;
      zm.natH = img.naturalHeight || 1;
      if (!zm.dlg.hidden && zm.box.firstChild === img) ready();
    };
    if (img.complete && img.naturalWidth) img.onload();
  }
  var cb = zm.dlg.querySelector('[data-zm="close"]');
  if (cb) cb.focus({ preventScroll: true });
}

function zmClose() {
  if (zm.dlg.hidden) return;
  zm.dlg.hidden = true;
  zm.box.innerHTML = '';
  zm.ptrs = {}; zm.drag = null; zm.pinch = null;
  document.body.classList.remove('zm-open');
  var root = document.getElementById('fm-root'), bar = document.querySelector('.toolbar');
  if (root) root.inert = false;
  if (bar) bar.inert = false;
  var o = zm.opener;
  zm.opener = null;
  if (o && o.focus) o.focus({ preventScroll: true });
}

function zmDist(a, b) { return Math.sqrt((a.x - b.x) * (a.x - b.x) + (a.y - b.y) * (a.y - b.y)); }

function zmTwo() {
  var ids = Object.keys(zm.ptrs);
  return [zm.ptrs[ids[0]], zm.ptrs[ids[1]]];
}

function zmStartDrag() {
  var ids = Object.keys(zm.ptrs);
  if (ids.length !== 1) { zm.drag = null; return; }
  var p = zm.ptrs[ids[0]];
  zm.drag = { px: p.x, py: p.y, x: zm.x, y: zm.y };
}

function zmStartPinch() {
  var pp = zmTwo();
  zm.drag = null;
  zm.pinch = {
    d: Math.max(1, zmDist(pp[0], pp[1])),
    mx: (pp[0].x + pp[1].x) / 2, my: (pp[0].y + pp[1].y) / 2,
    s: zm.s, x: zm.x, y: zm.y
  };
}

function zmTap(x, y, ptype) {
  var now = Date.now(), lt = zm.lastTap;
  var r = zm.box.getBoundingClientRect();
  var inside = x >= r.left && x <= r.right && y >= r.top && y <= r.bottom;
  if (lt && now - lt.t < 400 && Math.abs(x - lt.x) < 30 && Math.abs(y - lt.y) < 30) {
    zm.lastTap = null;
    zmZoomAt(zm.s > 1.0001 ? 1 : 2, x, y);
    return;
  }
  zm.lastTap = { t: now, x: x, y: y };
  if (!inside && zm.s <= 1.0001) {
    if (ptype === 'touch') zm.ghost = { t: now, x: x, y: y };
    zmClose();
  }
}

function zmOnDown(e) {
  if (e.pointerType === 'mouse' && e.button !== 0) return;
  try { zm.stage.setPointerCapture(e.pointerId); } catch (err) {}
  zm.ptrs[e.pointerId] = { x: e.clientX, y: e.clientY };
  var n = Object.keys(zm.ptrs).length;
  if (n === 1) { zm.moved = false; zmStartDrag(); }
  else if (n === 2) { zm.moved = true; zmStartPinch(); }
}

function zmOnMove(e) {
  var p = zm.ptrs[e.pointerId];
  if (!p) return;
  p.x = e.clientX; p.y = e.clientY;
  var n = Object.keys(zm.ptrs).length;
  if (n >= 2 && zm.pinch) {
    var pp = zmTwo();
    var d = zmDist(pp[0], pp[1]);
    var mx = (pp[0].x + pp[1].x) / 2, my = (pp[0].y + pp[1].y) / 2;
    var ns = zmClamp(zm.pinch.s * d / zm.pinch.d, 1, ZM_MAX);
    var r = ns / zm.pinch.s;
    zm.s = ns;
    zm.x = mx - (zm.pinch.mx - zm.pinch.x) * r;
    zm.y = my - (zm.pinch.my - zm.pinch.y) * r;
    zmApply();
  } else if (zm.drag) {
    var dx = p.x - zm.drag.px, dy = p.y - zm.drag.py;
    if (Math.sqrt(dx * dx + dy * dy) > 6) zm.moved = true;
    if (zm.moved && zm.s > 1.0001) {
      zm.x = zm.drag.x + dx;
      zm.y = zm.drag.y + dy;
      zmApply();
    }
  }
}

function zmOnUp(e) {
  var p = zm.ptrs[e.pointerId];
  if (!p) return;
  delete zm.ptrs[e.pointerId];
  var n = Object.keys(zm.ptrs).length;
  if (n === 1) { zm.pinch = null; zmStartDrag(); }
  else if (n === 0) {
    zm.pinch = null; zm.drag = null;
    if (!zm.moved && e.type === 'pointerup') zmTap(e.clientX, e.clientY, e.pointerType);
  }
}

function zmOnWheel(e) {
  e.preventDefault();
  var dy = e.deltaY;
  if (e.deltaMode === 1) dy *= 16; else if (e.deltaMode === 2) dy *= 400;
  var k = e.ctrlKey ? 0.01 : 0.0015;
  zmZoomAt(zm.s * Math.exp(-dy * k), e.clientX, e.clientY);
}

function zmOnKey(e) {
  if (!zm.dlg || zm.dlg.hidden) return;
  if (e.key === 'Escape') { e.preventDefault(); zmClose(); return; }
  if (e.key === 'Tab') {
    var f = [].slice.call(zm.dlg.querySelectorAll('button'));
    if (!f.length) return;
    var i = f.indexOf(document.activeElement);
    e.preventDefault();
    f[(i + (e.shiftKey ? f.length - 1 : 1)) % f.length].focus();
    return;
  }
  if (e.key === '+' || e.key === '=') { e.preventDefault(); zmZoomCenter(zm.s * ZM_STEP); }
  else if (e.key === '-') { e.preventDefault(); zmZoomCenter(zm.s / ZM_STEP); }
  else if (e.key === '0') { e.preventDefault(); zmFit(); }
  else if (zm.s > 1.0001 && e.key.indexOf('Arrow') === 0) {
    e.preventDefault();
    var step = 80;
    if (e.key === 'ArrowLeft') zm.x += step;
    else if (e.key === 'ArrowRight') zm.x -= step;
    else if (e.key === 'ArrowUp') zm.y += step;
    else zm.y -= step;
    zmApply();
  }
}

function initZoom() {
  zm.dlg = document.getElementById('fm-zoom');
  if (!zm.dlg) return;
  zm.stage = zm.dlg.querySelector('.zm-stage');
  zm.box = zm.dlg.querySelector('.zm-box');

  document.querySelectorAll('.fm-schema, .fm-hero-img, .cover-img-box').forEach(function(el) {
    el.setAttribute('role', 'button');
    el.setAttribute('tabindex', '0');
    el.setAttribute('data-zoomable', '1');
    var host = el.classList.contains('fm-hero-img') ? el.parentNode : el;
    host.classList.add('fm-zoom-host');
    var b = document.createElement('span');
    b.className = 'fm-zoom-badge';
    b.setAttribute('aria-hidden', 'true');
    host.appendChild(b);
    el.addEventListener('click', function(e) {
      // le toucher sur le fond qui ferme la fenêtre ne doit pas rouvrir ce qui se trouve dessous
      var g = zm.ghost;
      if (g && Date.now() - g.t < 400 &&
          Math.abs(e.clientX - g.x) < 14 && Math.abs(e.clientY - g.y) < 14) { zm.ghost = null; return; }
      zmOpen(el);
    });
    el.addEventListener('keydown', function(e) {
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); zmOpen(el); }
    });
    if (el.classList.contains('cover-img-box')) {
      var m = /url\(["']?([^"')]+)["']?\)/.exec(getComputedStyle(el).backgroundImage || '');
      if (m) {
        var pre = new Image();
        pre.onload = function() { el._fmNat = [pre.naturalWidth, pre.naturalHeight]; };
        pre.src = m[1];
      }
    }
  });

  zm.dlg.querySelectorAll('[data-zm]').forEach(function(b) {
    b.addEventListener('click', function() {
      var a = b.getAttribute('data-zm');
      if (a === 'close') zmClose();
      else if (a === 'fit') zmFit();
      else if (a === 'in') zmZoomCenter(zm.s * ZM_STEP);
      else if (a === 'out') zmZoomCenter(zm.s / ZM_STEP);
    });
  });

  zm.stage.addEventListener('pointerdown', zmOnDown);
  zm.stage.addEventListener('pointermove', zmOnMove);
  zm.stage.addEventListener('pointerup', zmOnUp);
  zm.stage.addEventListener('pointercancel', zmOnUp);
  zm.stage.addEventListener('wheel', zmOnWheel, { passive: false });
  document.addEventListener('keydown', zmOnKey);
  window.addEventListener('resize', function() {
    if (zm.dlg.hidden) return;
    zmComputeFit();
    zmApply();
  });
  fmZoomRefresh();
}
'''

# ── HTML principal ───────────────────────────────────────────────────────────────

S0_HTML, S0_IDS = s0_html()
PANEL_HTML = {t: panel_html(t) for t in ('hq', 'bg', 'rs', 'rp', 'dg', 'fc')}

# ═════════════════════════════════════════════════════════════════════════════════
# Les pages du manuel : une seule source de texte, FR et EN bloc à bloc
# ═════════════════════════════════════════════════════════════════════════════════
# Un bloc = (genre, FR, EN). Genres : h (titre), p (un ou plusieurs paragraphes), ul (liste), note / warn (encadré),
# raw (HTML tel quel, panneaux et schémas). Les liens : [[page|texte]] (page : hq, bg, rs, fc, rp, dg, start, start:gestes).

def _typo_fr(t):
    t = t.replace('« ', '«' + _NBSP_FINE).replace(' »', _NBSP_FINE + '»')
    return fr_typo(t)

def _md(t, fr=False):
    t = _esc(t)
    t = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', t)
    t = re.sub(r'`(.+?)`', r'<code>\1</code>', t)
    t = re.sub(r'\[\[([\w:-]+)\|(.+?)\]\]', r'<a class="fm-lnk" href="#\1" onclick="location.hash=&#39;\1&#39;;return false">\2</a>', t)
    return _typo_fr(t) if fr else t

def _lb(lang, inner, tag='div'):
    return f'<{tag} class="lang-block" data-lang="{lang}">{inner}</{tag}>'

def _render(blocks, pid):
    """Les blocs d'une page en HTML ; chaque bloc écrit FR puis EN (parité exacte). Avant chaque titre h3, une ancre commune aux deux langues <pid>-<n> (n : rang du h3 dans la page)."""
    out, prose = [], []
    n_h3 = 0
    def flush():
        if prose:
            out.append('      <div class="fm-prose">\n        ' + '\n        '.join(prose) + '\n      </div>')
            prose.clear()
    for kind, fr, en in blocks:
        if kind == 'raw':
            flush(); out.append(fr)
        elif kind == 'h':
            n_h3 += 1
            prose.append(f'<span id="{pid}-{n_h3}"></span>')
            prose.append(_lb('fr', _md(fr, True), 'h3')); prose.append(_lb('en', _md(en), 'h3'))
        elif kind == 'h4':
            prose.append(_lb('fr', _md(fr, True), 'h4')); prose.append(_lb('en', _md(en), 'h4'))
        elif kind == 'anchor':
            prose.append(f'<span id="{fr}"></span>')
        elif kind == 'p':
            prose.append(_lb('fr', ''.join('<p>' + _md(x, True) + '</p>' for x in fr)))
            prose.append(_lb('en', ''.join('<p>' + _md(x) + '</p>' for x in en)))
        elif kind == 'ul':
            prose.append(_lb('fr', '<ul>' + ''.join('<li>' + _md(x, True) + '</li>' for x in fr) + '</ul>'))
            prose.append(_lb('en', '<ul>' + ''.join('<li>' + _md(x) + '</li>' for x in en) + '</ul>'))
        elif kind in ('note', 'warn'):
            flush()
            out.append(f'      <div class="fm-callout {kind}">\n        ' + _lb('fr', _md(fr, True)) + '\n        ' + _lb('en', _md(en)) + '\n      </div>')
    flush()
    return '\n\n'.join(out)

def _hero(pid, mono, tile, alt):
    img = f'\n        <img class="fm-hero-img" src="{globals()[tile]}" alt="{alt}" draggable="false">' if tile else ''
    sub = f'\n            <div class="fm-hero-sub" data-i18n="{pid}.hero.sub">' + '{SUB}' + '</div>' if pid != 'start' else ''
    return (f'      <div class="fm-hero">{img}\n        <div class="fm-hero-pin" aria-hidden="true"></div>\n        <div class="fm-hero-caption">\n'
            f'          <div><div class="fm-hero-monogram">{mono}</div></div>\n          <div>\n'
            f'            <div class="fm-hero-title" data-i18n="{pid}.hero.title">' + '{TITLE}' + f'</div>{sub}\n          </div>\n        </div>\n      </div>')

_HERO_TXT = {
    'start': ('Par où commencer', None), 'hq': ('HQ — Wing Command Center', 'Configuration escadre centralisée'),
    'bg': ('Briefing Generator', 'Générateur de briefings multi-sections'), 'rs': ('Recon Station', 'Compositeur photo-renseignement'),
    'rp': ('Route Planner', 'Routes, navigation et cartes de mission'), 'dg': ('Datacard Generator', 'Datacards de vol pour le kneeboard'),
    'fc': ('Flight Configurator', 'Un groupe prêt à appliquer : radios, emport, livrée'),
}
_ACCENT = {'hq': '#4FB286; --chapter-accent-rgb:79,178,134', 'fc': '#D0784A; --chapter-accent-rgb:208,120,74',
           'bg': '#c0892a; --chapter-accent-rgb:192,137,42', 'dg': '#4f7a8e; --chapter-accent-rgb:79,122,142',
           'rp': '#7ac97a; --chapter-accent-rgb:122,201,122'}
_TILE = {'hq': 'HQ_TILE_SRC', 'bg': 'BG_TILE_SRC', 'rs': 'RS_TILE_SRC', 'rp': 'RP_TILE_SRC', 'dg': 'DG_TILE_SRC', 'fc': 'FC_TILE_SRC'}
_MONO = {'start': '0', 'hq': 'HQ', 'bg': 'BG', 'rs': 'RS', 'rp': 'RP', 'dg': 'DG', 'fc': 'FC'}
_ALT = {'hq': 'HQ', 'bg': 'Briefing Generator', 'rs': 'Recon Station', 'rp': 'Route Planner', 'dg': 'Datacard Generator', 'fc': 'Flight Configurator'}

def _levels(pid, blocks):
    """Les blocs d'une page, titres au bon niveau : sous « Les gestes », les sous-sections prennent un niveau en dessous (h4)."""
    if pid == 'start':
        return list(blocks)
    seen, nb = False, []
    for k, f, e in blocks:
        if k == 'h' and f == 'Les gestes':
            seen = True
        elif k == 'h' and seen:
            k = 'h4'
        nb.append((k, f, e))
    return nb

# Les pages du manuel, dans l'ordre (le même que PAGES du script) ; le sommaire et le bas de chapitre en sont tirés
_ORDER = ['index', 'start', 'hq', 'bg', 'rs', 'rp', 'dg', 'fc']
PAGES_JS = str(_ORDER)     # la liste PAGES du script est générée d'ici : une seule liste des pages
_ACCENT_HEX = {pid: v.split(';')[0] for pid, v in _ACCENT.items()}
_ACCENT_HEX['rs'] = '#C95A9C'     # RS : l'accent est posé par la feuille (#page-rs), non par _ACCENT ; un contrôle du build relit l'accord

def _plain(h):
    return re.sub(r'<[^>]+>', '', h)

def _a_go(target, cls, inner, extra=''):
    """Un lien du manuel vers une page ou une section. Le manuel tourne dans un cadre srcdoc : un href="#…" seul se résout contre l'adresse du shell
    et le recharge dans le cadre ; fmGo() pose le hash (comme les liens du texte), le href reste pour l'accessibilité."""
    return f'<a class="{cls}" href="#{target}" onclick="fmGo(&#39;{target}&#39;);return false"{extra}>{inner}</a>'

def _title_span(pid):
    """Le titre d'une page, tel que le dictionnaire le donne (index : nav.index)."""
    key = 'nav.index' if pid == 'index' else f'{pid}.hero.title'
    return f'<span data-i18n="{key}">' + _esc('Index' if pid == 'index' else _HERO_TXT[pid][0]) + '</span>'

def build_toc():
    """Le panneau de sommaire : une ligne par page, sous chacune une ligne par titre h3, générés depuis PAGES_SRC."""
    rows = []
    for pid in _ORDER:
        sty = f' style="--a:{_ACCENT_HEX.get(pid, "var(--fm-accent)")}"'
        code = '' if pid == 'index' else _MONO[pid]
        rows.append('    ' + _a_go(pid, 'fmnav-ch', f'<span class="fmnav-code">{code}</span><span class="fmnav-t">' + _title_span(pid) + '</span>',
                                   f' data-page="{pid}"{sty}'))
        if pid == 'index':
            continue
        n = 0
        for k, f, e in _levels(pid, PAGES_SRC[pid]):
            if k != 'h':
                continue
            n += 1
            rows.append('    ' + _a_go(f'{pid}:{pid}-{n}', 'fmnav-sec',
                                       _lb('fr', _plain(_md(f, True)), 'span') + _lb('en', _plain(_md(e)), 'span')))
    return ('<div class="fmnav-ov" id="fmnav-ov" aria-hidden="true" onclick="fmTocSet(false,false)"></div>\n'
            '<nav class="fmnav-panel" id="fmnav-panel" inert data-i18n-aria-label="nav.contents" aria-label="Sommaire">\n'
            '  <div class="fmnav-head"><span data-i18n="nav.contents">Sommaire</span>'
            '<button type="button" id="fmnav-x" class="tb-btn fmnav-x" onclick="fmTocSet(false,true)" data-i18n-aria-label="nav.close" aria-label="Fermer le sommaire" data-i18n-title="nav.close" title="Fermer le sommaire">×</button></div>\n'
            + '\n'.join(rows) + '\n</nav>')

def build_pn(pid):
    """Le bas de chapitre : le chapitre précédent et le suivant (ordre de _ORDER ; « Par où commencer » n'a pas de précédent, le FC pas de suivant)."""
    i = _ORDER.index(pid)
    def box(j, cls, key, label):
        if j < 1 or j >= len(_ORDER):
            return '<span></span>'
        q = _ORDER[j]
        return _a_go(q, cls, f'<span class="fmnav-k" data-i18n="{key}">{label}</span><span class="fmnav-n">{_MONO[q]} · ' + _title_span(q) + '</span>')
    return ('\n      <div class="fmnav-pn">' + box(i - 1, 'fmnav-pv', 'nav.prev', '◄ Chapitre précédent')
            + box(i + 1, 'fmnav-nx', 'nav.next', 'Chapitre suivant ►') + '</div>\n')

def _page(pid, blocks):
    blocks = _levels(pid, blocks)
    style = f' style="--chapter-accent:{_ACCENT[pid]};"' if pid in _ACCENT else ''
    hero = _hero(pid, _MONO[pid], _TILE.get(pid), _ALT.get(pid, ''))
    hero = hero.replace('{TITLE}', _esc(_HERO_TXT[pid][0])).replace('{SUB}', _esc(_HERO_TXT[pid][1] or ''))
    return (f'  <section id="page-{pid}" class="fm-page hidden">\n    <div class="fm-chapter"{style}>\n\n'
            f'{hero}\n\n'
            + _render(blocks, pid) + '\n' + build_pn(pid) + f'\n    </div><!-- /fm-chapter -->\n  </section><!-- /page-{pid} -->\n')

PAGES_SRC = {}

# ── Par où commencer ─────────────────────────────────────────────────────────────
PAGES_SRC['start'] = [
    ('raw', S0_HTML, ''),
    ('p', ['Mission Plan prépare une mission à deux rôles. Le **Mission Commander** la prépare pour toute l’escadre : HQ (le Wing, puis le .miz de chaque mission), le Briefing Generator (le briefing) et Recon Station (les photos). Chaque **Flight Leader** prépare le vol de son groupe : le Route Planner (la route), le Datacard Generator (la datacard du kneeboard) et le Flight Configurator (radios, emport, livrée, paquet de vol). Chaque chapitre détaille ce que son outil prend et donne dans son panneau Reçoit · Donne.'], ['Mission Plan prepares a mission in two roles. The **Mission Commander** prepares it for the whole wing: HQ (the Wing, then the .miz of each mission), the Briefing Generator (the briefing) and Recon Station (the photos). Each **Flight Leader** prepares their group’s flight: the Route Planner (the route), the Datacard Generator (the kneeboard datacard) and the Flight Configurator (radios, loadout, livery, flight package). Each chapter details what its tool takes and gives in its Receives · Gives panel.']),
    ('h', "Ouvrir Mission Plan", "Opening Mission Plan"),
    ('p', ['Ouvrez **dcs_mission_plan.html**, ou sa version en ligne : c’est l’accueil, et les six outils s’ouvrent depuis leur carte. Un outil ouvert seul n’affiche qu’une ligne qui renvoie vers Mission Plan : les échanges passent par l’accueil. Tout marche sans réseau, sauf les fonds de carte et les fiches d’aérodrome du Route Planner.'], ['Open **dcs_mission_plan.html**, or its online version: it is the home page, and the six tools open from their card. A tool opened on its own shows only a line pointing to Mission Plan: the exchanges go through the home page. Everything works offline, except the Route Planner’s base maps and airfield sheets.']),
    ('h', "Le retour au Mission Commander", "The return to the Mission Commander"),
    ('p', ['Les trois outils du Flight Leader partagent leurs groupes en direct : leur ordre n’est pas imposé, mais pour une datacard complète le Flight Configurator (emport, carburant, poids) passe avant l’export du Datacard Generator. Le seul retour qui se **fusionne** est le paquet de vol du Flight Configurator : rouvrir le fichier de travail d’un Flight Leader remplace tout le travail, et plusieurs Flight Leaders ne se rassemblent que par leurs paquets.'], ['The three Flight Leader tools share their groups live: their order is not imposed, but for a complete datacard the Flight Configurator (loadout, fuel, weight) comes before the Datacard Generator export. The only return that **merges** is the Flight Configurator’s flight package: reopening a Flight Leader’s work file replaces all the work, and several Flight Leaders come together only through their packages.']),
    ('h', "Les gestes, et ce qu’ils gardent", "The gestures, and what they keep"),
    ('p',
     ["Les mêmes gestes ont le même sens dans tous les outils. La planche, puis les lignes qui la suivent, disent lesquels remplacent du travail, et ce qui reste."],
     ["The same gestures mean the same thing in every tool. The drawing, then the lines that follow it, say which ones replace work, and what stays."]),
    ('raw', START_PLATE_HTML, ''),
    ('p',
     ["**Effacer**, après confirmation : au BG, il vide le briefing ; à RS, l’image, les annotations, la légende et le bloc d’informations ; au RP, au DG et au FC, « Tout effacer ? » vide les groupes, les routes, les calques et les datacards des trois outils (au RP, une fenêtre à cocher) ; à HQ, il retire la mission ouverte. Il garde : à RS, les logos, les réglages, le Wing ; au RP, au DG et au FC, les presets, le théâtre, les unités, les réglages ; à HQ, le Wing.",
      "**Restaurer** : après un Exemple ou un Ouvrir, un message le propose pendant douze secondes et rend le travail d’avant ; après deux remplacements de suite, l’état d’avant le premier. Il est **refusé** dès que vous avez saisi quelque chose : « Restauration impossible : les données ont changé depuis. »"],
     ["**Clear**, after a confirmation: in the BG, it empties the briefing; in RS, the image, the annotations, the legend and the info block; in the RP, DG and FC, “Clear everything?” empties the groups, routes, layers and datacards of the three tools (in the RP, a window with tick boxes); in HQ, it removes the open mission. It keeps: in RS, the logos, settings, Wing; in the RP, DG and FC, the presets, theatre, units, settings; in HQ, the Wing.",
      "**Restore**: after an Example or an Open, a message offers it for twelve seconds and brings back the previous work; after two replacements in a row, the state before the first. It is **refused** as soon as you have typed something: “Cannot restore: the data has changed since.”"]),
    ('p',
     ["Les fenêtres Sauvegarder et Exporter (RS, BG, DG, paquets de vol) demandent un nom de fichier, proposé et modifiable."],
     ["The Save and Export windows (RS, BG, DG, flight packages) ask for a file name, proposed and editable."]),
    ('h', "La fenêtre d’import commune", "The common import window"),
    ('p', ['Le Route Planner (Importer des routes…), le Datacard Generator (menu … des cartes › Importer des groupes) et le Flight Configurator (Importer des groupes…) ouvrent la même fenêtre. On choisit une source : la mission d’HQ, le briefing en cours ou un fichier (paquet de vol, ancien fichier de briefing). On coche les groupes et, pour chacun, ce qu’il apporte : route, radios, emport, livrée. Un groupe de même nom et coalition est complété, sinon créé ; les routes d’un autre théâtre ne sont pas importées, et un appareil inconnu arrive sans type, à choisir.'], ['The Route Planner (Import routes…), the Datacard Generator (cards … menu › Import groups) and the Flight Configurator (Import groups…) open the same window. You pick a source: the HQ mission, the current briefing or a file (flight package, old briefing file). You tick the groups and, for each, what it brings: route, radios, loadout, livery. A group with the same name and coalition is completed, otherwise it is created; routes from another theatre are not imported, and an unknown aircraft arrives without a type, to be chosen.']),
    ('h', "La barre du haut", "The top bar"),
    ('p', ['La barre est la même dans les six outils : les boutons de fichier juste après le sigle, puis les réglages. Quand la place manque, les boutons **perdent leur texte par étapes**, Affichage d’abord, et gardent leur icône et leur info-bulle ; au téléphone ou à la tablette, tous sont des icônes. Quand elle ne tient toujours pas, au téléphone, les réglages qui suivent les boutons de fichier et Affichage passent dans « ⋯ », au bout à droite, en commençant par le dernier. L’icône à droite de l’en-tête d’une section **replie ou déplie toutes les sections**, dans les six outils ; au téléphone ou à la tablette, l’éditeur du BG et du DG passe en onglets.', 'Sous la barre du BG, du RP, du DG et du FC, la **ligne de mission d’HQ** dit quel .miz est ouvert dans HQ, sa date et son heure, et ce que l’outil en prend. Au RP, au DG et au FC, elle passe en rouge, « Non utilisée ici : autre théâtre », quand la mission n’est pas celle du théâtre de l’outil ; au BG, jamais.'], ['The bar is the same in all six tools: the file buttons right after the abbreviation, then the settings. When room runs out, the buttons **lose their text in stages**, Display first, and keep their icon and tooltip; on a phone or tablet, all of them are icons. When it still does not fit, on a phone, the settings after the file buttons and Display move into “⋯”, at the right end, starting with the last one. The icon at the right of a section header **folds or unfolds all the sections**, in all six tools; on a phone or tablet, the BG and DG editor switches to tabs.', 'Under the bar of the BG, RP, DG and FC, the **HQ mission line** says which .miz is open in HQ, its date and time, and what the tool takes from it. In the RP, DG and FC it turns red, “Not used here: other theatre”, when the mission is not on the tool’s theatre; in the BG, never.']),
    ('h', "Lire ce manuel au téléphone", "Reading this manual on a phone"),
    ('p',
     ["**Index** et **Sommaire**, dans la barre, restent à portée de main : Index ramène à la page d’entrée du manuel, Sommaire ouvre la liste de ses pages et de leurs sections, et un toucher y mène. En bas de chaque chapitre, le précédent et le suivant. **◄ Mission Plan** quitte le manuel."],
     ["**Index** and **Contents**, in the bar, stay within reach: Index goes back to the manual’s front page, Contents opens the list of its pages and their sections, and one touch takes you there. At the bottom of each chapter, the previous one and the next one. **◄ Mission Plan** leaves the manual."]),
    ('p',
     ["Touchez un schéma pour l’agrandir ; pincez ou utilisez + pour zoomer. Sur un téléphone, la carte d’ensemble prend une forme verticale."],
     ["Touch a diagram to enlarge it; pinch or use + to zoom. On a phone, the suite map takes a vertical shape."]),
]

# ── HQ ───────────────────────────────────────────────────────────────────────────
PAGES_SRC['hq'] = [
    ('h', "À quoi ça sert", "What it's for"),
    ('p', ['HQ fait deux choses. C’est le seul endroit où saisir l’identité de l’escadre, le **Wing**, que les autres outils reprennent. Et il ouvre la mission de DCS (.miz) pour en lire les groupes, la date, l’heure et la météo, les offrir aux autres outils et, à la fin, y réécrire ce que les Flight Leaders ont préparé.'], ['HQ does two things. It is the only place to enter the wing’s identity, the **Wing**, which the other tools take up. And it opens the DCS mission (.miz) to read its groups, date, time and weather, offer them to the other tools and, at the end, write back into it what the Flight Leaders prepared.']),
    ('raw', PANEL_HTML['hq'], ''),
    ('h', "Les gestes", "The gestures"),
    ('raw', HQ_PLATE_HTML, ''),
    ('h', "Le Wing", "The Wing"),
    ('p', ['La fenêtre **Wing** décrit l’escadre une fois pour toutes ; le callsign d’un escadron sert de base aux indicatifs automatiques du Briefing Generator, modifiables ensuite. Les **livrées custom** se déclarent aussi ici, avec leurs appareils : le Flight Configurator les propose dans la liste des livrées de chaque type. Sous elles, la **livrée par défaut** de chaque appareil est celle que le Flight Configurator affiche quand la mission d’HQ n’en donne pas ; sans choix, c’est la première de sa liste. Les livrées custom et la livrée par défaut se replient comme les escadrons, et sont fermées à l’ouverture de la page.', 'Un bouton la réinitialise. Quand la configuration est fournie par un autre outil, la fenêtre la montre sans laisser la modifier : une note dit où elle se modifie, et l’Exemple d’HQ est inactif. Après **Exemple**, **Restaurer ma configuration** reste en tête de la fenêtre tant que la sauvegarde existe ; un nouveau clic sur Exemple ne la remplace jamais. Un Flight Leader n’a pas le Wing dans son fichier de travail : pour avoir les escadrons dans son HQ, donnez-lui le fichier d’**Exporter config**.'],
          ['The **Wing** window describes the wing once and for all; a squadron’s callsign seeds the Briefing Generator’s automatic call signs, editable afterwards. The wing’s **custom liveries** are declared here too, with their aircraft: the Flight Configurator offers them in each type’s livery list. Below them, each aircraft’s **default livery** is the one the Flight Configurator shows when the mission open in HQ doesn’t give it one; without a choice, it is the first in its list. The custom liveries and the default livery fold like the squadrons, and are closed when the page opens.', 'A button resets it. When the configuration is provided by another tool, the window shows it without letting you change it: a note says where to edit it, and HQ’s Example is off. After **Example**, **Restore my configuration** stays at the top of the window while the backup exists; a new click on Example never replaces it. A Flight Leader does not get the Wing in their work file: for the squadrons in their HQ, give them the **Export config** file.']),
    ('h', "Les paquets de vol", "Flight packages"),
    ('p', ['**Appliquer à la mission** modifie la mission ouverte sans rien télécharger, comme Supprimer et Dynamic Spawn : chacun ajoute 1 au compteur de Sauvegarder .miz. La mission ouverte n’est partagée avec les autres outils que tant que son .miz est ouvert : recharger la page l’oublie.'], ['**Apply to the mission** changes the open mission without downloading anything, like Delete and Dynamic Spawn: each adds 1 to the Save .miz counter. The open mission is shared with the other tools only while its .miz is open: reloading the page forgets it.']),
    ('p',
     ["**Créer ce vol dans la mission** : un vol que la mission n’a pas. Quand son paquet porte un départ du Flight Configurator, la liste « Départ » devient une ligne, et le vol part comme le Flight Leader l’a réglé : sur ses places, à froid ou moteurs en route, ou en vol ou au sol au point 1. Une place déjà prise dans la mission (un appareil, ou un objet statique avion ou hélicoptère, à moins de 10 m de son centre) ou retenue par un vol précédent est remplacée par la plus proche des places libres qui conviennent, que vous changez dans la liste ; sans place libre, le vol n’est pas créé et le compte rendu dit pourquoi. Le point 1 du paquet est remplacé par le point de la place quand il est à moins de 3 000 m de la base ; plus loin, il devient le point 2."],
     ["**Create this flight in the mission**: a flight the mission lacks. When its package carries a departure from the Flight Configurator, the “Start” list becomes a line, and the flight starts as the Flight Leader set it: on its stands, cold or with engines running, or in the air or on the ground at waypoint 1. A stand already taken in the mission (an aircraft, or a static airplane or helicopter, within 10 m of its center) or kept by an earlier flight is replaced by the nearest free stand that fits, which you change in the list; with no free stand, the flight is not created and the report says why. Waypoint 1 of the package is replaced by the stand’s point when it is within 3,000 m of the base; farther away, it becomes waypoint 2."]),
    ('h', "Dynamic Spawn", "Dynamic Spawn"),
    ('p', ['Seuls sont proposés les lieux dont le Dynamic Spawn est activé dans l’éditeur de mission et dont la liste d’appareils contient le type du template ; la fenêtre dit pourquoi les autres ne le sont pas.'], ['Only places whose Dynamic Spawn is enabled in the mission editor and whose aircraft list contains the template’s type are offered; the window says why the others are not.']),
]

# ── Briefing Generator ───────────────────────────────────────────────────────────
PAGES_SRC['bg'] = [
    ('h', "À quoi ça sert", "What it's for"),
    ('p', ['Le Briefing Generator prépare le briefing de la mission, prêt à imprimer ou à emporter en vol, dans l’un de **deux formats** : **Standard**, une page de mission, et **Avancé**, un dossier de plusieurs pages. On remplit les sections dans l’éditeur, on vérifie la mise en page dans l’aperçu, puis on exporte.'], ['The Briefing Generator prepares the mission briefing, ready to print or take into the cockpit, in one of **two formats**: **Standard**, one mission page, and **Advanced**, a multi-page file. You fill in the sections in the editor, check the layout in the preview, then export.']),
    ('raw', PANEL_HTML['bg'], ''),
    ('raw', f'''      <div class="fm-schema tall">
        {BG_SVG}
        <div class="fm-schema-legend">
          <span class="lang-block" data-lang="fr">{BG_LEGEND_FR}</span>
          <span class="lang-block" data-lang="en">{BG_LEGEND_EN}</span>
        </div>
      </div>''', ''),
    ('h', "Les gestes", "The gestures"),
    ('raw', BG_PLATE_HTML, ''),
    ('p', ['L’exemple et ses effets sont dans [[start:gestes|Par où commencer]].'], ['The example and its effects are in [[start:gestes|Where to start]].']),
    ('h', "Le brief Avancé", "The Advanced brief"),
    ('p', ['Le brief Avancé garde l’En-tête et la Méta du Standard ; toutes ses autres sections lui sont propres. La section **Configuration Wing** est en lecture seule : le Wing se modifie dans HQ. Les indicatifs de l’équipage sont proposés à partir du callsign des escadrons d’HQ, et restent modifiables.'], ['The Advanced brief keeps the Standard’s Header and Meta; all its other sections are its own. The **Wing configuration** section is read-only: the Wing is edited in HQ. Crew call signs are proposed from the callsign of HQ’s squadrons, and stay editable.']),
    ('h', "Le METAR", "The METAR"),
    ('p',
     ["L’assistant METAR a deux voies : un formulaire guidé, ou **Reprendre de la mission d’HQ**, qui lit la météo, la date et l’heure de la mission ouverte dans HQ (grisé tant qu’HQ n’a pas de mission), puis **Insérer dans METAR**. Le champ METAR reste modifiable."],
     ["The METAR assistant has two routes: a guided form, or **Take from HQ mission**, which reads the weather, date and time of the mission open in HQ (greyed out while HQ has no mission), then **Insert into METAR**. The METAR field stays editable."]),
    ('h', "La carte et la photo", "The map and the photo"),
    ('p',
     ["La carte du Route Planner arrive par **Placer la carte du Route Planner**, après l’**Exporter ▾ › Image pour le briefing…** du Route Planner, dans la même session de l’accueil. La photo de Recon Station n’arrive pas toute seule : exportez le PNG dans Recon Station, puis ajoutez l’image dans la section **Photos**."],
     ["The Route Planner map arrives through **Place the Route Planner map**, after the Route Planner’s **Export ▾ › Image for the briefing…**, in the same home-page session. The Recon Station photo does not arrive by itself: export the PNG in Recon Station, then add the image in the **Photos** section."]),
]

# ── Recon Station ────────────────────────────────────────────────────────────────
RS_ANATOMY_HTML = '''      <div class="fm-schema">
        <svg viewBox="0 0 720 380" xmlns="http://www.w3.org/2000/svg" role="img"
             aria-label="Anatomie d'une photo recon" data-aria-fr="Anatomie d'une photo recon" data-aria-en="Anatomy of a recon photo">
          <defs>
            <marker id="lead" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto">
              <path d="M0,0 L7,3.5 L0,7 Z" fill="currentColor" opacity=".55"/>
            </marker>
            <pattern id="hatch" width="6" height="6" patternTransform="rotate(45)" patternUnits="userSpaceOnUse">
              <line x1="0" y1="0" x2="0" y2="6" stroke="#C95A9C" stroke-width="2" opacity=".7"/>
            </pattern>
          </defs>

          <text x="360" y="26" text-anchor="middle" font-size="13" letter-spacing="3" fill="currentColor" opacity=".9" class="lang-block" data-lang="fr">ANATOMIE D'UNE PHOTO RECON</text>
          <text x="360" y="26" text-anchor="middle" font-size="13" letter-spacing="3" fill="currentColor" opacity=".9" class="lang-block" data-lang="en">ANATOMY OF A RECON PHOTO</text>
          <line x1="120" y1="34" x2="600" y2="34" stroke="currentColor" stroke-width=".6" opacity=".3"/>

          <!-- PHOTO (fond sombre, repères clairs) -->
          <rect x="250" y="64" width="220" height="240" fill="#2b2f26" stroke="currentColor" stroke-width="1.2"/>
          <rect x="250" y="64"  width="220" height="18" fill="url(#hatch)"/>
          <rect x="250" y="286" width="220" height="18" fill="url(#hatch)"/>
          <rect x="258" y="248" width="34" height="24" fill="none" stroke="#e8e3d8" stroke-width="1" opacity=".8"/>
          <text x="275" y="263" text-anchor="middle" font-size="9" fill="#e8e3d8" opacity=".8">LOGO</text>
          <rect x="396" y="92" width="66" height="48" fill="none" stroke="#e8e3d8" stroke-width="1" opacity=".85"/>
          <text x="403" y="106" font-size="9" fill="#e8e3d8" opacity=".85">1 ___</text>
          <text x="403" y="120" font-size="9" fill="#e8e3d8" opacity=".85">2 ___</text>
          <text x="403" y="134" font-size="9" fill="#e8e3d8" opacity=".85">3 ___</text>
          <line x1="331" y1="176" x2="356" y2="160" stroke="#C95A9C" stroke-width="1.6"/>
          <circle cx="320" cy="182" r="11" fill="none" stroke="#C95A9C" stroke-width="1.8"/>
          <text x="320" y="186" text-anchor="middle" font-size="11" fill="#C95A9C">1</text>
          <circle cx="356" cy="160" r="2.2" fill="#C95A9C"/>
          <rect x="294" y="206" width="30" height="24" fill="none" stroke="#e8e3d8" stroke-dasharray="3 2" stroke-width="1" opacity=".8"/>
          <rect x="398" y="160" width="64" height="52" fill="none" stroke="#e8e3d8" stroke-width="1.4"/>
          <line x1="324" y1="212" x2="398" y2="186" stroke="#e8e3d8" stroke-dasharray="3 2" stroke-width="1" opacity=".7"/>
          <text x="430" y="190" text-anchor="middle" font-size="11" fill="#e8e3d8" opacity=".7">&#8853;</text>
          <rect x="300" y="250" width="120" height="28" fill="none" stroke="#e8e3d8" stroke-width="1" opacity=".85"/>
          <text x="360" y="268" text-anchor="middle" font-size="8.5" fill="#e8e3d8" opacity=".85">TGT · COORDS · DTG</text>

          <!-- Labels gauche -->
          <line x1="214" y1="73"  x2="250" y2="73"  stroke="currentColor" stroke-width="1" opacity=".55" marker-end="url(#lead)"/>
          <line x1="214" y1="260" x2="258" y2="260" stroke="currentColor" stroke-width="1" opacity=".55" marker-end="url(#lead)"/>
          <line x1="214" y1="182" x2="307" y2="182" stroke="currentColor" stroke-width="1" opacity=".55" marker-end="url(#lead)"/>
          <g font-size="12.5" fill="currentColor" text-anchor="end">
            <text x="208" y="77"  class="lang-block" data-lang="fr">Bandeau de classification</text>
            <text x="208" y="77"  class="lang-block" data-lang="en">Classification banner</text>
            <text x="208" y="264" class="lang-block" data-lang="fr">Logo</text>
            <text x="208" y="264" class="lang-block" data-lang="en">Logo</text>
            <text x="208" y="186" class="lang-block" data-lang="fr">Marqueur + amorce</text>
            <text x="208" y="186" class="lang-block" data-lang="en">Marker + leader line</text>
          </g>

          <!-- Labels droite -->
          <line x1="506" y1="108" x2="464" y2="116" stroke="currentColor" stroke-width="1" opacity=".55" marker-end="url(#lead)"/>
          <line x1="506" y1="186" x2="464" y2="186" stroke="currentColor" stroke-width="1" opacity=".55" marker-end="url(#lead)"/>
          <g font-size="12.5" fill="currentColor" text-anchor="start">
            <text x="512" y="112" class="lang-block" data-lang="fr">Cartouche : N° + légende</text>
            <text x="512" y="112" class="lang-block" data-lang="en">Cartouche: No. + legend</text>
            <text x="512" y="190" class="lang-block" data-lang="fr">Loupe (agrandissement)</text>
            <text x="512" y="190" class="lang-block" data-lang="en">Loupe (magnification)</text>
          </g>

          <!-- Label bas -->
          <line x1="360" y1="326" x2="360" y2="280" stroke="currentColor" stroke-width="1" opacity=".55" marker-end="url(#lead)"/>
          <text x="360" y="336" text-anchor="middle" font-size="12.5" fill="currentColor" class="lang-block" data-lang="fr">Bloc d'informations</text>
          <text x="360" y="336" text-anchor="middle" font-size="12.5" fill="currentColor" class="lang-block" data-lang="en">Information block</text>
        </svg>
        <div class="fm-schema-legend">
          <span class="lang-block" data-lang="fr">Fig. 1 — Où se place chaque élément sur la photo composée.</span>
          <span class="lang-block" data-lang="en">Fig. 1 — Where each element sits on the composed photo.</span>
        </div>
      </div>'''
PAGES_SRC['rs'] = [
    ('h', "À quoi ça sert", "What it's for"),
    ('p', ['Recon Station transforme une capture d’écran DCS, ou n’importe quelle image, en **photo d’analyse de reconnaissance** : on donne à l’image l’allure d’un capteur, puis on pose par-dessus des annotations. L’export est un PNG sans perte, à la résolution de la source.'], ['Recon Station turns a DCS screenshot, or any image, into a **reconnaissance analysis photo**: you give the image the look of a sensor, then lay annotations over it. The export is a lossless PNG, at the source’s resolution.']),
    ('raw', PANEL_HTML['rs'], ''),
    ('raw', RS_ANATOMY_HTML, ''),
    ('h', "Les gestes", "The gestures"),
    ('raw', RS_PLATE_HTML, ''),
    ('p', ['Pour mettre la photo au briefing, voir le [[bg|Briefing Generator]].'], ['To put the photo in the briefing, see the [[bg|Briefing Generator]].']),
]

# ── Route Planner ────────────────────────────────────────────────────────────────
PAGES_SRC['rp'] = [
    ('h', "À quoi ça sert", "What it's for"),
    ('p', ['Le Route Planner trace la route d’un groupe sur la carte d’un théâtre de DCS et en donne la navigation : caps, distances, temps. On y pose aussi des points de référence et des calques tactiques, et on consulte la fiche d’un terrain.'], ['The Route Planner draws a group’s route on the map of a DCS theatre and gives its navigation: headings, distances, times. You also place reference points and tactical layers, and consult an airfield sheet.']),
    ('raw', PANEL_HTML['rp'], ''),
    ('h', "Les gestes", "The gestures"),
    ('raw', RP_PLATE_HTML, ''),
    ('h', "Les points de référence", "Reference points"),
    ('p', ['Les **points de référence** marquent ce qui compte hors de la route : une cible, un repère, un terrain. Posez-les en mode Réf. ou par + Réf. ; ils ne comptent ni dans les branches ni dans le total, passent à la datacard, mais pas au Route Tool de DCS.'], ['**Reference points** mark what matters off the route: a target, a landmark, an airfield. Place them in Ref. mode or with + Ref.; they count neither in the legs nor in the total, and go to the datacard but not to the DCS Route Tool.']),
    ('h', "La navigation", "Navigation"),
    ('p', ['La section Navigation donne cap, temps et distance de chaque branche, et le total ; son titre dit le cap employé. Cap : Vrai ou Magnétique. En magnétique, la déclinaison est **Calculée**, d’après la date de la mission d’HQ quand elle existe, ou **Saisie** ; **Forcer** impose l’année saisie. Sans valeur saisie, le cap reste vrai et l’avertissement le dit.'], ['The Navigation section gives each leg’s heading, time and distance, and the total; its title says which heading is used. Heading: True or Magnetic. In magnetic, the variation is **Computed**, from the HQ mission date when there is one, or **Entered**; **Override** imposes the entered year. With no value entered, the heading stays true and the warning says so.']),
    ('p', ['**DISS-15** — Pour un Mi-24P ou un Mi-8MTV2, le réglage DISS-15 de la section Navigation ajoute sous chaque point ses valeurs pour l’indicateur de coordonnées : avant ou arrière, gauche ou droite, en km depuis le premier point, angle de carte à 000. Le nord est celui de l’appareil du premier groupe de la route : nord de la grille pour le Mi-24P, dont le KM-2 se règle à la valeur indiquée, nord magnétique pour le Mi-8MTV2. Chaque point est un point de recalage : au-dessus de lui, posez les compteurs à ses valeurs.'], ['**DISS-15** — For a Mi-24P or a Mi-8MTV2, the DISS-15 setting of the Navigation section adds under each waypoint its values for the coordinate indicator: forward or aft, left or right, in km from the first waypoint, map angle 000. The north is that of the aircraft of the route’s first group: grid north for the Mi-24P, whose KM-2 is set to the value shown, magnetic north for the Mi-8MTV2. Each waypoint is an update point: over it, set the counters to its values.']),
    ('h', "La fiche d’un aérodrome", "An airfield sheet"),
    ('p',
     ["En mode **Lire**, avec les Aérodromes affichés, touchez un aérodrome : sa fiche s’ouvre, avec les pages d’une chart de DCS Airfield Charts. Elle **vient du réseau**, au toucher, et un terrain peut n’avoir pas encore de fiche."],
     ["In **Read** mode, with Airfields shown, touch an airfield: its sheet opens, with the pages of a DCS Airfield Charts chart. It **comes from the network**, on touch, and an airfield may not have a sheet yet."]),
    ('h', "Dessiner ses calques", "Drawing your layers"),
    ('p', ['Le mode **Dessin** ouvre une barre au pied de la carte. Son bouton Calque dit où vous dessinez : un de vos calques, un nouveau par + Calque, ou une copie modifiable d’un calque CombatFlite par Copier pour dessiner. Sans calque, le premier objet en crée un. Une zone ou une ligne se termine par Terminer, et un objet choisi se modifie à ses poignées. La section Calques du panneau liste les calques, à cocher pour les montrer ; ils sont gardés dans le navigateur.'], ['The **Draw** mode opens a bar at the foot of the map. Its Layer button says where you draw: one of your layers, a new one with + Layer, or an editable copy of a CombatFlite layer with Copy to draw. With no layer, the first object creates one. A zone or a line ends with Finish, and a chosen object is edited by its handles. The panel’s Layers section lists the layers, to tick to show them; they are kept in the browser.']),
    ('h', "Les calques CombatFlite", "CombatFlite layers"),
    ('p',
     ["**Ouvrir ▾ › Ouvrir une route ou des calques…** lit aussi un fichier CombatFlite (.cf) : la fenêtre en liste les calques ; cochez ceux à afficher, puis **Afficher**.  Ces calques sont en lecture seule : en mode Lire, un objet touché montre sa fiche et propose → Point de référence. Un fichier .cf ne touche jamais la route."],
     ["**Open ▾ › Open a route or layers…** also reads a CombatFlite (.cf) file: the window lists its layers; tick the ones to show, then **Show**.  These layers are read-only: in Read mode, a touched object shows its sheet and offers → Reference point. A .cf file never touches the route."]),
    ('h', "Ouvrir, importer, sauvegarder", "Opening, importing, saving"),
    ('p',
     ["Le travail est gardé dans le navigateur. **Sauvegarder**, ou Ctrl+S, écrit le fichier de travail de la suite. **Ouvrir ▾ › Ouvrir une route ou des calques…** reconnaît ce qu’on lui donne : une route JSON, un fichier du Route Tool de DCS ou un fichier CombatFlite. **Importer des routes…** ouvre la [[start:start-4|fenêtre d’import commune]]."],
     ["The work is kept in the browser. **Save**, or Ctrl+S, writes the suite’s work file. **Open ▾ › Open a route or layers…** recognises what it is given: a JSON route, a DCS Route Tool file or a CombatFlite file. **Import routes…** opens the [[start:start-4|common import window]]."]),
    ('h', "Le Route Tool de DCS", "The DCS Route Tool"),
    ('p', ['Le Route Tool range toutes les routes d’une carte dans un fichier <théâtre>.lua, dans `Saved Games\\DCS\\Config\\RouteToolPresets`. **Ouvrir une route ou des calques…** sur ce fichier ouvre une fenêtre : choisissez le théâtre et la route ; elle remplace la route en cours. **Exporter ▾ › Route Tool…** demande un nom, puis ajoute la route à votre fichier, ou crée un fichier neuf ; copiez-le ensuite dans RouteToolPresets. La ligne est grisée sur un théâtre sans Route Tool.'], ['The Route Tool keeps all of a map’s routes in a <theatre>.lua file, in `Saved Games\\DCS\\Config\\RouteToolPresets`. **Open a route or layers…** on that file opens a window: choose the theatre and the route; it replaces the current route. **Export ▾ › Route Tool…** asks for a name, then adds the route to your file, or creates a new file; copy it afterwards into RouteToolPresets. The line is greyed out on a theatre with no Route Tool.']),
    ('h', "L’image pour le briefing", "The image for the briefing"),
    ('p',
     ["**Exporter ▾ › Image pour le briefing…** pose sur la carte un cadre d’export, Paysage ou Portrait : déplacez et zoomez la carte sous le cadre, puis **Exporter**. L’image part au Briefing Generator de la même session. Un fond venu d’un autre site peut manquer dans l’image : un message le signale."],
     ["**Export ▾ › Image for the briefing…** places an export frame on the map, Landscape or Portrait: move and zoom the map under the frame, then **Export**. The image goes to the Briefing Generator in the same session. A base map from another site may be missing from the image: a message says so."]),
    ('h', "Sur tablette et téléphone", "On tablets and phones"),
    ('p', ['Sur grand écran, le panneau est à gauche et la carte à droite. Au téléphone ou à la tablette, la carte reste fixe au-dessus du panneau, qui seul défile ; une poignée entre les deux agrandit ou réduit la carte, et deux touchers la remettent à sa taille. Quand le clavier de l’écran s’ouvre sur un champ du panneau, la carte se réduit le temps de la saisie.'], ['On a big screen, the panel is on the left and the map on the right. On a phone or tablet, the map stays fixed above the panel, which alone scrolls; a handle between the two enlarges or shrinks the map, and a double tap resets its size. When the on-screen keyboard opens on a panel field, the map shrinks for the time of the entry.']),
    ('warn',
     "Le cap de la règle de l’éditeur — La règle de l’éditeur de mission de DCS mesure un **cap grille**, ni vrai ni magnétique : il diffère du cap du Route Planner, jusqu’à une dizaine de degrés sur la carte Allemagne (guerre froide). Pour comparer, prenez le cap **Vrai** du Route Planner ; l’écart qui reste est la convergence de la grille.",
     "The editor ruler’s heading — The DCS mission editor’s ruler measures a **grid heading**, neither true nor magnetic: it differs from the Route Planner heading, by up to about ten degrees on the Germany (Cold War) map. To compare, take the Route Planner’s **True** heading; the remaining gap is the grid convergence."),
    ('note',
     "Hors ligne — Sans connexion, les fonds de carte et les fiches ne se chargent pas : la carte n’affiche que sa grille, avec le bandeau **Fond indisponible — grille seule**. La route, les références, la navigation et les calques restent utilisables.",
     "Offline — Without a connection, base maps and sheets do not load: the map shows only its grid, with the **Base map unavailable — grid only** banner. The route, references, navigation and layers stay usable."),
]

# ── Datacard Generator ───────────────────────────────────────────────────────────
PAGES_SRC['dg'] = [
    ('h', "À quoi ça sert", "What it's for"),
    ('p', ['Le Datacard Generator produit la **datacard** d’un groupe : une fiche d’une page, au format d’une page de kneeboard, qui réunit ce dont l’équipage a besoin en l’air. On en tient un paquet, une par groupe, et on l’exporte en PNG pour le kneeboard de DCS ou en PDF pour l’imprimer.'], ['The Datacard Generator produces a group’s **datacard**: a one-page sheet, in the format of a kneeboard page, that gathers what the crew needs in the air. You keep a deck, one per group, and export it as PNG for the DCS kneeboard or as PDF to print it.']),
    ('raw', PANEL_HTML['dg'], ''),
    ('raw', f'''      <div class="fm-schema">
        {DG_ANATOMY_SVG}
        <div class="fm-schema-legend">
          <span class="lang-block" data-lang="fr">Fig. 1 — L’anatomie d’une datacard : où se range chaque bloc.</span>
          <span class="lang-block" data-lang="en">Fig. 1 — Anatomy of a datacard: where each block goes.</span>
        </div>
      </div>''', ''),
    ('h', "Les gestes", "The gestures"),
    ('raw', DG_PLATE_HTML, ''),
    ('h', "Une carte libre", "A free card"),
    ('p', ['Une carte libre n’est liée à rien : tout y est texte libre, sauf le type des unités.'], ['A free card is linked to nothing: everything in it is free text, except the units’ type.']),
    ('h', "Le poids au décollage", "Take-off weight"),
    ('p',
     ["Le carburant et le poids au décollage de chaque unité suivent la même règle que le Flight Configurator, celle de l’éditeur de mission de DCS : l’appareil à vide avec ses options d’équipement, le carburant, les emports et les obus du canon au pourcentage choisi. Les leurres et les paillettes ne pèsent rien."],
     ["Each unit’s fuel and take-off weight follow the same rule as the Flight Configurator, the DCS mission editor’s: the empty aircraft with its equipment options, the fuel, the stores and the gun rounds at the chosen percentage. Flares and chaff weigh nothing."]),
    ('h', "La navigation", "Navigation"),
    ('p', ['Un point sans coordonnées se place par cap et distance depuis son voisin. Les points de référence sont ceux du Route Planner ; chaque datacard choisit ceux qu’elle affiche. **Lier à une autre route** lie la carte affichée à une route du Route Planner ; … › **Une datacard par route** en crée une par route d’un coup. Les réglages de cap sont communs au Route Planner et au Datacard Generator.'], ['A point with no coordinates is placed by heading and distance from its neighbour. The reference points are the Route Planner’s; each datacard chooses which ones it shows. **Link to another route** links the displayed card to a Route Planner route; … › **One datacard per route** creates one per route at once. The heading settings are shared by the Route Planner and the Datacard Generator.']),
    ('p', ['**Cap / distance + DISS** — Pour une datacard de Mi-24P ou de Mi-8MTV2, cet affichage ajoute au cap et à la distance les valeurs du DISS-15 de chaque point, depuis le premier. Le titre du bloc dit ce qu’il faut régler : angle de carte 000, puis nord de la grille et valeur du KM-2 pour le Mi-24P, nord magnétique pour le Mi-8MTV2.'], ['**Heading / distance + DISS** — For a Mi-24P or Mi-8MTV2 datacard, this display adds to heading and distance each waypoint’s DISS-15 values, from the first one. The block title tells what to set: map angle 000, then grid north and the KM-2 value for the Mi-24P, magnetic north for the Mi-8MTV2.']),
    ('h', "Importer", "Importing"),
    ('p', ['Les **groupes** (mission d’HQ, paquet de vol, briefing en cours) s’importent par … › **Importer des groupes**, la [[start:start-4|fenêtre d’import commune]] : une carte par groupe, avec, pour la mission d’HQ, la date, l’heure et la météo. **Ouvrir ▾ › Importer…** lit un **briefing**, en cours ou en fichier, et ajoute une datacard par vol coché, avec tout ce que le briefing en dit ; une ligne Données générales couvre un briefing sans groupe. Elle lit aussi une route ou un jeu de routes depuis un fichier : **Lier la carte à cette route** ou **Nouvelle datacard**. Restent à la main les horaires, et le carburant et l’emport quand le FC ne les donne pas. Une datacard importée vit ensuite seule : modifier le briefing ne la change pas.'], ['The **groups** (HQ mission, flight package, current briefing) are imported through … › **Import groups**, the [[start:start-4|common import window]]: one card per group, with, for the HQ mission, the date, time and weather. **Open ▾ › Import…** reads a **briefing**, current or from a file, and adds a datacard per ticked flight, with everything the briefing says about it; a General data line covers a briefing with no group. It also reads a route or a set of routes from a file: **Link the card to this route** or **New datacard**. Still to do by hand: the timings, and the fuel and loadout when the FC does not provide them. An imported datacard then lives on its own: changing the briefing does not change it.']),
    ('h', "Quand la page déborde", "When the page overflows"),
    ('p',
     ["La fiche garde toutes ses boîtes, même vides, pour être imprimée et complétée à la main. Quand tout ne tient pas, la navigation passe sur une page 2, avec un en-tête réduit. Si la page 1 déborde encore, l’éditeur affiche « Contenu tronqué » : allégez le contenu."],
     ["The sheet keeps all its boxes, even empty ones, to be printed and completed by hand. When everything does not fit, the navigation moves to a page 2, with a reduced header. If page 1 still overflows, the editor shows “Content truncated”: lighten the content."]),
    ('h', "Sauvegarder", "Saving"),
    ('p', ['Le paquet est gardé dans le navigateur. **Ouvrir ▾ › Ouvrir une datacard…** lit encore un ancien fichier de datacards, qui remplace le paquet en cours, après confirmation si celui-ci n’est pas vierge.'], ['The deck is kept in the browser. **Open ▾ › Open a datacard…** still reads an old datacards file, which replaces the current deck, after a confirmation if it is not blank.']),
]

# ── Flight Configurator ──────────────────────────────────────────────────────────
PAGES_SRC['fc'] = [
    ('h', "À quoi ça sert", "What it's for"),
    ('p', ['Le Flight Configurator est l’outil du Flight Leader : il prépare un ou plusieurs groupes — identité, radios, emport composé sur la vue de face de l’appareil, livrée — et les exporte en paquet de vol que le Mission Commander applique à sa mission avec HQ. HQ retrouve chaque groupe par son nom et sa coalition ; chaque partie est facultative, et une partie laissée vide n’est pas touchée.'], ['The Flight Configurator is the Flight Leader’s tool: it prepares one or more groups — identity, radios, loadout composed on the aircraft’s front view, livery — and exports them as a flight package that the Mission Commander applies to their mission with HQ. HQ finds each group by its name and coalition; each part is optional, and a part left empty is not touched.']),
    ('raw', PANEL_HTML['fc'], ''),
    ('h', "Les gestes", "The gestures"),
    ('raw', FC_PLATE_HTML, ''),
    ('p', ['**Types d’appareils** — La liste propose les 75 appareils pilotables du jeu, par hélicoptères puis avions, avec une recherche. Ce qui manque à un type est dit à sa place : pas de poste programmable dans l’éditeur, bande non contrôlée, pas d’emport, pas de dessin, pas de livrée du jeu.'], ['**Aircraft types** — The list offers the game’s 75 flyable aircraft, helicopters then planes, with a search. What a type lacks is said in its place: no radio preset in the mission editor, band not checked, no loadout, no drawing, no game livery.']),
    ('h', "La route", "The route"),
    ('p', ['Un groupe n’a qu’une route : on la choisit parmi celles du Route Planner en touchant une vignette, celles que le Route Planner lie à ce groupe d’abord. Le groupe garde une copie des points : c’est elle que le paquet porte. La reprise est automatique : quand le Route Planner enregistre, chaque groupe lié reprend les points de sa route et son nom ; si la route est supprimée au Route Planner, elle est retirée des groupes qui la suivaient.'], ['A group has one route only: you choose it among the Route Planner’s by tapping a thumbnail, the ones the Route Planner links to this group first. The group keeps a copy of the points: that is what the package carries. The pick-up is automatic: when the Route Planner saves, each linked group takes up its route’s points and its name; if the route is deleted in the Route Planner, it is removed from the groups that followed it. ']),
    ('h', "Le départ et les places", "Departure and stands"),
    ('p',
     ["**Base de départ** liste les aérodromes du théâtre, du plus proche au plus éloigné du point 1 de la route (sans route, par nom) ; « Aucune » laisse le groupe partir du point 1. **Départ** dit comment : sur la place, à froid ou moteurs en route, quand il y a une base ; en vol ou au sol au point 1 sinon. Avec une base, chaque unité a sa **Place** : une liste des places qui prennent son appareil (un hélicoptère sur une place d’hélicoptère, un avion sur une place d’avion, l’appareil plus petit que la place), ou le bouton **Plan**, qui montre l’aérodrome dessiné par DCS Airfield Charts avec les places dessus ; on touche une place pour la prendre. Une place prise par une autre unité du Flight Configurator, de n’importe quel groupe, n’est plus offerte. Changer de base vide les places du groupe, changer de théâtre vide les bases et les places, changer le type d’une unité vide sa place si elle n’y tient plus."],
     ["**Departure base** lists the airfields of the theatre, from the nearest to the farthest from waypoint 1 of the route (without a route, by name); “None” lets the group start at waypoint 1. **Start** tells how: on the stand, cold or with engines running, when there is a base; in the air or on the ground at waypoint 1 otherwise. With a base, each unit has its **Stand**: a list of the stands that take its aircraft (a helicopter on a helicopter stand, an airplane on an airplane stand, the aircraft smaller than the stand), or the **Map** button, which shows the airfield drawn by DCS Airfield Charts with the stands on it; you tap a stand to take it. A stand taken by another unit of the Flight Configurator, of any group, is no longer offered. Changing the base clears the group’s stands, changing the theatre clears the bases and the stands, and changing a unit’s type clears its stand if it no longer fits."]),
    ('p',
     ["Le paquet porte le départ de chaque groupe (`departure` : le départ, la base et les places qui prennent tous ses appareils) et la place de chaque unité (`stand`) ; un paquet sans eux se lit comme avant. Une unité sans place est permise : l’export le dit dans la barre, et HQ prendra une place libre. Le plan est lu sur l’hébergement public de la suite ; sans réponse, la fenêtre montre les places seules."],
     ["The package carries each group’s departure (`departure`: the start, the base and the stands that take all its aircraft) and each unit’s stand (`stand`); a package without them is read as before. A unit without a stand is allowed: the export says so in the bar, and HQ will take a free one. The map is read from the suite’s public host; with no answer, the window shows the stands alone."]),
    ('h', "Les radios", "The radios"),
    ('p', ['Une fréquence se saisit en MHz et doit tomber dans la bande du poste, que le module écrit sous son titre : une valeur hors bande est refusée avec un message qui cite la bande ; une valeur hors bande déjà présente, importée par exemple, est gardée et signalée sans bloquer l’export. Les hélicoptères ont aussi un poste HF : la mission ne le règle pas et HQ ne l’écrit jamais, mais la datacard le reprend.'], ['A frequency is typed in MHz and must fall inside the radio’s band, which the module writes under its title: an out-of-band value is refused with a message that quotes the band; an out-of-band value already present, imported for instance, is kept and flagged without blocking the export. The helicopters also have an **HF** radio: the mission does not set it and HQ never writes it, but the datacard picks it up.']),
    ('h', "L’emport", "The loadout"),
    ('p', ['Les presets vivent dans le navigateur seulement : ni le fichier de travail, ni Ouvrir, Exemple ou Effacer n’y touchent, et le paquet ne porte jamais un preset, mais un emport.'], ['Presets live in the browser only: neither the work file, nor Open, Example or Clear touch them, and the package never carries a preset, but a loadout.']),
    ('p',
     ["La **masse au décollage** s’additionne comme dans l’éditeur de mission de DCS : l’appareil à vide, avec ses options d’équipement, plus le carburant, les emports et les obus du canon au pourcentage du champ Canon, plus, pour certains avions, la cuve dont la masse suit le carburant (le réservoir de mélange MW-50 du Bf 109, par exemple). Les leurres et les paillettes ne pèsent rien. La ligne de détail sous la masse des emports donne chaque terme ; le champ Canon n’existe que pour un appareil qui a un canon."],
     ["The **take-off mass** adds up as in the DCS mission editor: the empty aircraft, with its equipment options, plus the fuel, the stores and the gun rounds at the percentage of the Gun field, plus, for some aircraft, the tank whose mass follows the fuel (the Bf 109’s MW-50 mix tank, for instance). Flares and chaff weigh nothing. The detail line under the loadout mass gives each term; the Gun field only exists for an aircraft that has a gun."]),
    ('p',
     ["Le bloc **Équipement · options de l’éditeur de DCS** règle, pour chaque unité, les options que l’éditeur propose à son type : une case par option, une liste quand l’option a plusieurs valeurs. Chaque case ou valeur porte sa masse, et un geste recalcule la masse au décollage. Le paquet de vol porte ces options pour chaque unité (`AddPropAircraft`) ; à l’application, HQ les écrit dans la mission, pour un groupe retrouvé comme pour un groupe créé, avec l’emport. Les options de la mission, importées d’HQ avec l’emport, se retrouvent dans le bloc ; changer le type d’une unité les remet aux valeurs du jeu."],
     ["The **Equipment · DCS editor options** block sets, for each unit, the options that the editor offers for its type: one box per option, a list when the option has several values. Each box or value carries its mass, and a gesture recomputes the take-off mass. The flight package carries these options for each unit (`AddPropAircraft`); when it is applied, HQ writes them to the mission, for a found group as for a created one, along with the loadout. The mission’s own options, imported from HQ with the loadout, show up in the block; changing a unit’s type puts them back to the game’s values."]),
    ('h', "La livrée", "The livery"),
    ('p',
     ["Le champ est une liste, celle du type de l’unité : les livrées du jeu et les livrées custom déclarées dans la fenêtre Wing d’HQ. Il affiche toujours un nom, et c’est ce nom que le paquet emporte. Tant que vous n’en choisissez pas, c’est la livrée de l’unité dans la mission ouverte dans HQ, sinon la livrée par défaut du type déclarée dans Wing, sinon la première de la liste. À l’application du paquet, HQ laisse décocher la livrée."],
     ["The field is a list, the unit type’s: the game’s liveries and the custom liveries declared in HQ’s Wing window. It always shows a name, and that name is what the package carries. Until you choose one, it is the unit’s livery in the mission open in HQ, otherwise the type’s default livery declared in Wing, otherwise the first in the list. When the package is applied, HQ lets you untick the livery."]),
    ('h', "Importer", "Importing"),
    ('p',
     ["**Importer des groupes…** ouvre la [[start:start-4|fenêtre d’import commune]] ; une unité sans type se règle une fois son type choisi. **Ouvrir ▾ › Ouvrir une configuration…** lit encore l’ancien fichier du module, avec vos groupes et « Mes presets ». Si les groupes sont sur un autre théâtre, un bandeau propose d’y revenir ou de retirer leurs routes."],
     ["**Import groups…** opens the [[start:start-4|common import window]]; a unit with no type is set up once its type is chosen. **Open ▾ › Open a configuration…** still reads the module’s old file, with your groups and “My presets”. If the groups are on another theatre, a banner offers to go back there or to remove their routes."]),
    ('note',
     "Crédits — Les tables d’armes viennent de **pydcs** (LGPL-3.0-or-later), reprises de Mission Tools ; les places des aérodromes viennent de **pydcs** (LGPL-3.0-or-later) et les plans qui les portent de **DCS Airfield Charts** ; les dessins de la vue de face sont de **Goldwolf** (DCS Reference Guide), utilisés avec son accord et **hors de la licence AGPL** du dépôt (voir `data/views/LICENSE.md`). Limite : le module écrit l’emport qu’on compose ; il ne dit pas que DCS l’acceptera.",
     "Credits — The weapon tables come from **pydcs** (LGPL-3.0-or-later), taken from Mission Tools; the airfield stands come from **pydcs** (LGPL-3.0-or-later) and the maps that carry them from **DCS Airfield Charts**; the front-view drawings are by **Goldwolf** (DCS Reference Guide), used with his permission and **outside the repository’s AGPL licence** (see `data/views/LICENSE.md`). Limit: the module writes the loadout you compose; it does not say that DCS will accept it."),
]

TOC_HTML = build_toc()
PAGES_HTML = '\n\n'.join(_page(pid, PAGES_SRC[pid]) for pid in ('start', 'hq', 'bg', 'rs', 'rp', 'dg', 'fc'))

HTML = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0, viewport-fit=cover">
<title>Field Manual — Mission Plan</title>
{FONT_CDN}
<style>
/* =============================================
   DCS FIELD MANUAL v{SUITE_VERSION}
   Documentation module — Mission Plan suite
   ============================================= */

{font_face_css()}

:root {{
  --f-stencil:    'Stardos Stencil', 'Impact', 'Arial Narrow Bold', sans-serif;
  --f-typewriter: 'Special Elite', 'Courier New', monospace;
  --f-ui:         'Oswald', 'Arial Narrow', sans-serif;
  --amber:        #c0892a;
  --amber-dark:   #8a5e15;
  --green-radar:  #4f6b3a;
  /* Accent du module Field Manual */
  --fm-accent:    #7E8FA6;
  --fm-accent-dark: #5a6a7a;
}}

/* ── THÈMES (clonés verbatim depuis build_recon_station.py) ── */
body[data-theme="cw-nato"] {{
  --paper: #d8c9a5; --paper-light: #e3d6b5; --paper-dark: #b8a77c;
  --ink: #1f1c16; --ink-faded: #463f30;
  --olive: #4a5230; --olive-dark: #2c321e; --olive-deep: #1a1e10;
  --khaki: #807454; --khaki-light: #a89a72;
  --red-stamp: #a83524; --red-faded: #c4574a;
  --rust: #7a3a20;
  --kraft-bg: url('data:image/svg+xml;base64,{KRAFT_NATO}');
}}
body[data-theme="cw-soviet"] {{
  --paper: #d8c479; --paper-light: #e8d690; --paper-dark: #b8a64a;
  --ink: #1f1c16; --ink-faded: #463f30;
  --olive: #2a3a5a; --olive-dark: #1a2540; --olive-deep: #0e1830;
  --khaki: #3a4a2e; --khaki-light: #5a6a48;
  --red-stamp: #841e1e; --red-faded: #a04040;
  --rust: #5e1414;
  --kraft-bg: url('data:image/svg+xml;base64,{KRAFT_SOV}');
}}
body[data-theme="modern-nato"] {{
  --paper: #e8e3d8; --paper-light: #f0ece2; --paper-dark: #c8c0b0;
  --ink: #15181c; --ink-faded: #3a4048;
  --olive: #2a3038; --olive-dark: #1c2026; --olive-deep: #0e1014;
  --khaki: #5c6b7a; --khaki-light: #7a8a98;
  --red-stamp: #1a1a1a; --red-faded: #4a4a4a;
  --rust: #2a2a2a;
  --kraft-bg: url('data:image/svg+xml;base64,{KRAFT_MNATO}');
}}
body[data-theme="modern-east"] {{
  --paper: #cdc6b8; --paper-light: #ddd6c8; --paper-dark: #ada69a;
  --ink: #1a1610; --ink-faded: #3d3024;
  --olive: #3d3024; --olive-dark: #2a2018; --olive-deep: #1a140e;
  --khaki: #4a5238; --khaki-light: #6a7256;
  --red-stamp: #7a2424; --red-faded: #a04040;
  --rust: #5a1a1a;
  --kraft-bg: url('data:image/svg+xml;base64,{KRAFT_MEAST}');
}}

/* ── Reset & base ── */
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
html, body {{ height: 100%; overscroll-behavior: none; }}
button, input, select, textarea {{ font: inherit; cursor: pointer; }}
/* le focus visible : la même règle que le bloc d'interface commun des autres modules */
button:focus-visible, select:focus-visible, input:focus-visible, textarea:focus-visible, summary:focus-visible,
a[href]:focus-visible, [tabindex]:focus-visible, [role="button"]:focus-visible {{
  outline: 2px solid var(--amber); outline-offset: 2px;
}}

body {{
  font-family: var(--f-typewriter);
  background: var(--olive-deep);
  color: var(--paper);
  font-size: 14px;
  line-height: 1.6;
  overflow: hidden;
  -webkit-tap-highlight-color: transparent;
  -webkit-text-size-adjust: 100%;
  display: flex;
  flex-direction: column;
  height: 100vh;
}}

/* ── TOOLBAR ── */
.toolbar {{
  position: relative;
  flex-shrink: 0;
  height: 60px;
  background: linear-gradient(180deg, var(--olive-dark) 0%, var(--olive-deep) 100%);
  border-bottom: 2px solid var(--fm-accent-dark);
  display: flex;
  align-items: center;
  padding: 0 14px;
  gap: 8px;
  z-index: 1000;
  box-shadow: 0 4px 12px rgba(0,0,0,.4);
  padding-left: max(14px, env(safe-area-inset-left));
  padding-right: max(14px, env(safe-area-inset-right));
}}

.tb-brand {{ display: flex; flex-direction: column; line-height: 1.1; gap: 1px; flex-shrink: 0; }}
.tb-brand-main {{
  font-family: var(--f-stencil);
  font-size: 16px;
  font-weight: 700;
  letter-spacing: 3px;
  color: var(--fm-accent);
  text-transform: uppercase;
  white-space: nowrap;
}}
.tb-brand-sub {{
  font-family: var(--f-ui);
  font-size: 10px;
  letter-spacing: 2px;
  color: var(--khaki-light);
  text-transform: uppercase;
  white-space: nowrap;
}}

.tb-sep {{ width: 1px; height: 28px; background: var(--khaki); opacity: .4; flex-shrink: 0; }}
.tb-spacer {{ flex: 1; }}

#btn-lang {{
  background: transparent;
  border: 1px solid var(--khaki);
  color: var(--paper);
  box-sizing: border-box;
  height: 44px;
  min-width: 44px;
  min-height: 44px;
  padding: 0 8px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-family: 'Roboto Mono', 'Courier New', monospace;
  font-weight: 400;
  font-size: 16px;
  transition: all .15s;
  flex-shrink: 0;
}}
#btn-lang:hover, #btn-lang:focus-visible {{
  background: var(--olive);
  border-color: var(--fm-accent);
}}


/* Le bouton commun de la barre, recopié du Datacard Generator (build_datacard_generator.py) : le Field Manual n'en avait que les règles de réduction. Le 44 px est celui de la barre commune (ui_block.py) */
.tb-btn {{
  font-family: var(--f-ui);
  font-weight: 700;
  letter-spacing: 1.5px;
  font-size: 12px;
  text-transform: uppercase;
  background: transparent;
  color: var(--paper);
  border: 1px solid var(--khaki);
  padding: 0 14px;
  height: 40px;
  min-width: 44px;
  cursor: pointer;
  transition: all .15s ease;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  white-space: nowrap;
  flex-shrink: 0;
}}
.tb-btn:hover, .tb-btn:focus-visible {{
  background: var(--olive);
  border-color: var(--amber);
  color: var(--amber);
}}
.tb-btn:active {{ transform: translateY(1px); }}
.tb-btn svg {{ width: 16px; height: 16px; flex-shrink: 0; }}
.tb-btn[hidden] {{ display: none; }}
.toolbar .tb-btn {{ min-height: 44px; }}
/* Sommaire ouvert : le style du survol, comme un bouton à menu ouvert */
#btn-toc[aria-expanded="true"] {{ background: var(--olive); border-color: var(--amber); color: var(--amber); }}

/* ---------- Le panneau de sommaire : la matière des listes de la suite (ui_block.py, .tbm-panel, .tbm-head, .tbm-opt) ---------- */
.fmnav-ov {{ position: fixed; inset: 60px 0 0 0; z-index: 998; display: none; background: rgba(10,12,6,.35); }}
body.fmnav-open .fmnav-ov {{ display: block; }}
.fmnav-panel {{
  position: fixed; top: 60px; right: 0; bottom: 0; z-index: 999;
  width: min(380px, calc(100vw - 32px)); box-sizing: border-box; overflow-x: hidden; overflow-y: auto; overscroll-behavior: contain; padding: 0 0 32px;
  background: linear-gradient(180deg, var(--olive-dark) 0%, var(--olive-deep) 100%);
  border-top: 3px solid var(--amber); border-left: 1px solid var(--amber-dark);
  box-shadow: 0 12px 28px rgba(0,0,0,.55), 0 2px 0 rgba(0,0,0,.35);
  scrollbar-width: thin; scrollbar-color: var(--amber-dark) transparent;
  transform: translateX(calc(100% + 48px)); transition: transform .18s ease-out;   /* fermé : hors de la vue, ombre comprise (elle porte à gauche de 38 px) ; l'attribut inert l'ôte du clavier */
}}
body.fmnav-open .fmnav-panel {{ transform: none; }}
@media (prefers-reduced-motion: reduce) {{
  .fmnav-panel {{ transition: none; }}
}}
@media print {{
  .fmnav-panel, .fmnav-ov {{ display: none !important; }}
}}
.fmnav-head {{
  display: flex; align-items: center; justify-content: space-between; padding: 8px 8px 8px 14px; margin-bottom: 2px;
  border-bottom: 1px solid rgba(168,154,114,.25);
  font-family: var(--f-ui); font-weight: 500; font-size: 10px; letter-spacing: 1.8px; text-transform: uppercase; color: color-mix(in srgb, var(--paper) 72%, var(--olive-dark));
}}
.fmnav-x {{ font-size: 16px; padding: 0; width: 44px; height: 44px; }}
.fmnav-ch, .fmnav-sec {{ position: relative; box-sizing: border-box; text-decoration: none; color: var(--paper); }}
.fmnav-ch {{
  display: grid; grid-template-columns: 40px minmax(0, 1fr); align-items: center; min-height: 44px; margin-top: 8px; padding: 0 14px 0 17px;
  font-family: var(--f-ui); font-weight: 700; font-size: 12px; letter-spacing: 1.5px; text-transform: uppercase;
}}
.fmnav-t {{ min-width: 0; overflow-wrap: anywhere; }}
.fmnav-code {{ font-family: var(--f-stencil); font-weight: 700; font-size: 13px; letter-spacing: 1px; color: color-mix(in srgb, var(--a) 62%, #f2e8cf); }}
.fmnav-sec {{
  display: flex; align-items: center; min-height: 40px; padding: 4px 14px 4px 57px;
  font-family: var(--f-ui); font-weight: 500; font-size: 13px; letter-spacing: .3px; text-transform: none;
  border-top: 1px solid rgba(168,154,114,.14); overflow-wrap: anywhere;
}}
.fmnav-sec > .lang-block {{ min-width: 0; }}
/* Les mêmes tons que les listes de la suite (ui_block.py, .tbm-head, .tbm-opt) : contraste de 4,5 au moins, haut et bas du dégradé, quatre thèmes */
.fmnav-ch:hover, .fmnav-sec:hover, .fmnav-ch:focus-visible, .fmnav-sec:focus-visible {{ background: var(--olive); color: color-mix(in srgb, var(--amber) 55%, #fff); }}
a.fmnav-ch:focus-visible, a.fmnav-sec:focus-visible {{ outline-offset: -2px; }}
.fmnav-ch[aria-current="page"] {{ color: color-mix(in srgb, var(--amber) 55%, #fff); font-weight: 700; }}
.fmnav-ch[aria-current="page"]::before {{ content: ''; position: absolute; left: 0; top: 6px; bottom: 6px; width: 3px; background: var(--amber); }}

/* ---------- Barre du haut commune aux sept modules ----------
   La marque du Field Manual : le titre et son sous-titre à l'accent du module, le sigle (F·M) quand le titre ne tient plus. Aucun seuil de largeur propre au Field Manual : la barre se réduit comme celle des autres outils,
   par la séquence commune du bloc d'interface (ui_block.py : build_bar_css, build_bar_js), « s'il tient » : le tampon de décor et celui que pose le shell, la version, puis (rien à retirer ici : ni liste ni Affichage ; mais deux boutons à texte, Index et Sommaire, qui perdent leur libellé à l'étape 5) le titre. */
.tb-brand-main, .tb-brand-short {{ color: #7E8FA6; }}
.tb-brand-short {{ display: none; font-family: var(--f-stencil); font-size: 16px; font-weight: 700; letter-spacing: 3px; white-space: nowrap; }}
.tb-classif {{ font-family: var(--f-stencil); font-weight: 400; font-size: 11px; letter-spacing: 3px; color: var(--red-faded); border: 1px solid var(--red-faded); padding: 4px 10px; white-space: nowrap; flex-shrink: 0; }}
#btn-lang svg {{ display: block; }}
.tb-brand-sub {{ font-weight: 500; }}
{BAR_CSS}
/* ── ROOT SCROLL ── */
#fm-root:focus {{ outline: none; }}
#fm-root {{
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  color: var(--ink);
  background: var(--kraft-bg), var(--paper);
  background-repeat: repeat;
  background-size: 400px 566px, auto;
}}

/* ── PAGE SYSTEM ── */
.fm-page {{ display: block; }}
.fm-page.hidden {{ display: none; }}

/* ── INDEX PAGE ── */
#page-index {{
  max-width: 900px;
  margin: 0 auto;
  padding: 32px 24px 64px;
}}

/* ── COUVERTURE ── */
.cover-wrap {{
  margin-bottom: 32px;
  border: 1px solid var(--khaki);
  box-shadow: 0 6px 24px rgba(0,0,0,.5), inset 0 0 60px rgba(0,0,0,.2);
  position: relative;
  overflow: hidden;
}}
.cover-img-box {{
  width: 100%;
  height: 260px;
  background-size: cover;
  background-position: center 25%;
  position: relative;
}}
.cover-img-box::after {{
  content: "";
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 1;
  background: linear-gradient(to top, rgba(0,0,0,.72) 0%, rgba(0,0,0,.32) 30%, transparent 58%);
}}
.cover-overlay {{
  position: absolute;
  bottom: 0; left: 0;
  padding: 16px 20px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  z-index: 2;
}}
.cover-suite {{
  font-weight: 500;   /* Oswald 500, la face que le navigateur dessinait déjà pour 400 */
  font-weight: 500;   /* Oswald 500, la face que le navigateur dessinait déjà pour 400 */
  font-family: var(--f-ui);
  font-size: 12px;
  letter-spacing: 3px;
  color: rgba(255,255,255,.75);
  text-transform: uppercase;
}}
.cover-ref {{
  font-family: var(--f-stencil);
  font-size: 18px;
  color: var(--fm-accent);
  letter-spacing: 2px;
}}

/* Fallback couverture SVG */
.cover-svg {{ background: var(--olive-dark); }}
.cover-svg-inner {{
  padding: 40px 32px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  text-align: center;
  border: 2px solid var(--khaki);
  margin: 8px;
}}
.cover-classif-top {{
  font-family: var(--f-ui);
  font-size: 10px;
  letter-spacing: 3px;
  color: var(--red-stamp);
  text-transform: uppercase;
  border: 1px solid var(--red-stamp);
  padding: 3px 10px;
}}
.cover-title-main {{
  font-family: var(--f-stencil);
  font-size: 42px;
  color: var(--fm-accent);
  letter-spacing: 6px;
  line-height: 1;
}}
.cover-title-sub {{
  font-family: var(--f-ui);
  font-size: 14px;
  letter-spacing: 4px;
  color: var(--khaki-light);
  text-transform: uppercase;
}}
.cover-ref-box {{
  font-family: var(--f-typewriter);
  font-size: 16px;
  color: var(--paper);
  border: 1px solid var(--fm-accent);
  padding: 4px 14px;
  letter-spacing: 2px;
}}
.cover-stamp {{
  font-family: var(--f-stencil);
  font-size: 11px;
  color: var(--red-stamp);
  letter-spacing: 2px;
  opacity: .7;
  margin-top: 8px;
}}

/* ── INTRO ── */
.fm-intro {{
  border-top: 1px solid var(--khaki);
  border-bottom: 1px solid var(--khaki);
  padding: 20px 0;
  margin-bottom: 36px;
}}
.fm-intro p {{
  color: var(--ink);
  font-size: 13px;
  line-height: 1.7;
  margin-bottom: 10px;
  opacity: .9;
}}
.fm-intro p:last-child {{ margin-bottom: 0; }}

/* ── SECTION TITLE ── */
.fm-section-title {{
  font-family: var(--f-stencil);
  font-size: 13px;
  letter-spacing: 4px;
  color: var(--fm-accent);
  text-transform: uppercase;
  margin-bottom: 20px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--fm-accent);
  opacity: .8;
}}

/* ── PLAQUES INDEX ── */
.fm-plaque-grid {{
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-bottom: 32px;
}}
.fm-section-title + .fm-plaque-grid, .fm-intro + .fm-plaque-grid {{ margin-top: 0; }}
@media (min-width: 900px) {{
  .fm-plaque-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
  }}
  .fm-plaque-grid .fm-plaque.fm-plaque-wide {{
    grid-column: 1 / -1;
  }}
}}

.fm-plaque {{
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 20px;
  background: linear-gradient(135deg, rgba(255,255,255,.04), rgba(0,0,0,.15));
  border: 1px solid var(--khaki);
  position: relative;
  overflow: hidden;
  transition: translate .12s ease, box-shadow .12s ease;
  text-decoration: none;
  color: inherit;
}}
.fm-plaque::before {{
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, rgba(var(--chapter-accent-rgb),.08) 0%, transparent 50%);
  pointer-events: none;
}}
.fm-plaque.active {{
  cursor: pointer;
  border-color: color-mix(in srgb, var(--chapter-accent, var(--fm-accent)) 40%, var(--khaki));
}}
.fm-plaque.active:hover {{
  translate: 0 -2px;
  box-shadow: 0 6px 20px rgba(0,0,0,.35);
  border-color: var(--chapter-accent, var(--fm-accent));
}}
.fm-plaque.active:focus-visible {{
  outline: 2px solid var(--amber);
  outline-offset: 2px;
}}
.fm-plaque.soon {{
  opacity: .5;
  cursor: default;
  pointer-events: none;
}}

.fm-plaque-monogram {{
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: var(--chapter-accent, var(--fm-accent));
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: var(--f-stencil);
  font-size: 16px;
  font-weight: 700;
  color: #fff;
  flex-shrink: 0;
  letter-spacing: 1px;
}}
.fm-plaque-info {{
  flex: 1;
  min-width: 0;
}}
.fm-plaque-name {{
  font-family: var(--f-stencil);
  font-size: 15px;
  letter-spacing: 2px;
  color: var(--ink);
  margin-bottom: 3px;
}}
.fm-plaque-desc {{
  font-weight: 500;   /* idem */
  font-weight: 500;   /* idem */
  font-family: var(--f-ui);
  font-size: 11px;
  letter-spacing: 1px;
  color: var(--khaki);
  text-transform: uppercase;
  white-space: normal;        /* la description passe à la ligne au lieu d'être coupée */
  overflow-wrap: break-word;
}}
.fm-plaque-wide .fm-plaque-desc {{ white-space: normal; }}       /* la plaque 0 : sa description passe à la ligne au lieu d'être coupée */
/* Tampon SOON en diagonal */
.fm-plaque.soon .fm-soon-stamp {{
  position: absolute;
  top: 50%; right: 16px;
  transform: rotate(-8deg) translateY(-50%);
  font-family: var(--f-stencil);
  font-size: 22px;
  letter-spacing: 3px;
  color: var(--red-stamp);
  border: 2px solid var(--red-stamp);
  padding: 2px 8px;
  opacity: .45;
  pointer-events: none;
}}

/* ── CHAPITRE PAGE ── */
/* La couleur d'un module marque, l'encre écrit : l'encre d'accent (50 % accent, 50 % encre) porte le texte. */
.fm-chapter, .fm-plaque, .fm-stub-placeholder {{
  --accent-ink: color-mix(in srgb, var(--chapter-accent, var(--fm-accent)) 40%, var(--ink));
}}
.fm-chapter {{
  max-width: 860px;
  margin: 0 auto;
  padding: 32px 24px 80px;
}}

/* Bas de chapitre : le chapitre précédent et le suivant (le style de l'ancien bouton « ◄ Index » : bord à l'accent du manuel, libellé Oswald) */
.fmnav-pn {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-top: 48px; padding-top: 20px; border-top: 1px solid var(--fm-accent); }}
.fmnav-pn a {{ display: flex; flex-direction: column; gap: 4px; padding: 12px 14px; text-decoration: none; border: 1px solid var(--fm-accent); transition: all .12s; }}
.fmnav-pn a:hover {{ background: rgba(126,143,166,.12); }}
.fmnav-nx {{ text-align: right; align-items: flex-end; }}
.fmnav-k {{ font-family: var(--f-ui); font-size: 11px; letter-spacing: 2px; text-transform: uppercase; color: var(--ink-faded); }}
.fmnav-n {{ font-family: var(--f-stencil); font-size: 13px; letter-spacing: 1.5px; color: var(--accent-ink); overflow-wrap: anywhere; }}
@media (max-width: 759px) {{
  .fmnav-pn {{ grid-template-columns: 1fr; gap: 10px; }}
  .fmnav-pn > span:empty {{ display: none; }}
}}

/* ── HERO ── */
.fm-hero {{
  margin-bottom: 32px;
  border: 1px solid var(--chapter-accent, var(--fm-accent));
  box-shadow: 0 4px 20px rgba(0,0,0,.4);
  position: relative;
  overflow: hidden;
}}
.fm-hero-img {{
  width: 100%;
  height: 200px;
  object-fit: cover;
  display: block;
  /* punaise simulée */
  position: relative;
}}
.fm-hero-pin {{
  position: absolute;
  top: 10px; right: 18px;
  width: 12px; height: 12px;
  border-radius: 50%;
  background: var(--chapter-accent, var(--fm-accent));
  box-shadow: 0 2px 6px rgba(0,0,0,.5);
}}
.fm-hero-caption {{
  padding: 12px 16px;
  background: linear-gradient(180deg, var(--olive-dark) 0%, var(--olive-deep) 100%);
  display: flex;
  align-items: center;
  gap: 14px;
  border-top: 2px solid var(--chapter-accent, var(--fm-accent));
}}
.fm-hero-monogram {{
  font-family: var(--f-stencil);
  font-size: 24px;
  color: var(--chapter-accent, var(--fm-accent));
  flex-shrink: 0;
  letter-spacing: 2px;
}}
.fm-hero-title {{
  font-family: var(--f-stencil);
  font-size: 18px;
  letter-spacing: 3px;
  color: var(--paper);
}}
.fm-hero-sub {{
  font-family: var(--f-ui);
  font-size: 10px;
  letter-spacing: 2px;
  color: var(--chapter-accent, var(--fm-accent));
  text-transform: uppercase;
  opacity: .8;
}}

/* ── PROSE ── */
.fm-prose {{
  margin-bottom: 28px;
}}
.fm-prose h3 {{
  font-family: var(--f-stencil);
  font-size: 14px;
  letter-spacing: 3px;
  color: var(--accent-ink);
  text-transform: uppercase;
  margin-bottom: 12px;
  padding-left: 12px;
  border-left: 3px solid var(--chapter-accent, var(--fm-accent));
}}
.fm-prose h4 {{
  font-family: var(--f-stencil);
  font-size: 11.5px;
  letter-spacing: 1.5px;
  color: var(--accent-ink);
  text-transform: uppercase;
  margin: 18px 0 8px;
  padding-left: 10px;
  border-left: 2px solid color-mix(in srgb, var(--chapter-accent, var(--fm-accent)) 55%, transparent);
}}
.fm-prose p {{
  font-size: 13px;
  line-height: 1.75;
  color: var(--ink);
  opacity: .9;
  margin-bottom: 10px;
}}
.fm-prose ol, .fm-prose ul {{
  padding-left: 20px;
  margin-bottom: 10px;
}}
.fm-prose li {{
  font-size: 13px;
  line-height: 1.7;
  color: var(--ink);
  opacity: .9;
  margin-bottom: 4px;
}}

/* Lang blocks */
.lang-block {{ display: block; }}
body[lang="en"] .lang-block[data-lang="fr"] {{ display: none; }}
body[lang="fr"] .lang-block[data-lang="en"] {{ display: none; }}

/* ── CALLOUTS ── */
.fm-callout {{
  margin: 20px 0;
  padding: 14px 16px;
  position: relative;
  font-size: 13px;
  line-height: 1.65;
}}
.fm-callout::before {{
  display: block;
  font-family: var(--f-stencil);
  font-size: 10px;
  letter-spacing: 3px;
  text-transform: uppercase;
  margin-bottom: 8px;
  padding-bottom: 6px;
  border-bottom: 1px solid currentColor;
}}
.fm-callout.note {{
  border: 1px solid var(--fm-accent);
  border-left: 3px solid var(--fm-accent);
  background: rgba(126,143,166,.07);
  color: var(--ink);
}}
.fm-callout.note::before {{
  content: '— NOTE';
  color: var(--fm-accent);
}}
.fm-callout.warn {{
  border: 1px solid var(--red-stamp);
  border-left: 3px solid var(--red-stamp);
  background: rgba(168,53,36,.07);
  color: var(--ink);
}}
.fm-callout.warn::before {{
  content: '▲ ATTENTION';
  color: var(--red-stamp);
}}

.fm-callout a, a.fm-lnk {{
  color: var(--accent-ink);
  text-decoration: underline;
  text-decoration-color: var(--chapter-accent, var(--fm-accent));
}}

kbd {{
  font-family: var(--f-typewriter);
  font-size: 11px;
  background: var(--olive-dark);
  border: 1px solid var(--khaki);
  border-bottom-width: 2px;
  border-radius: 3px;
  padding: 1px 6px;
  color: var(--paper);
  display: inline-block;
  margin: 0 2px;
}}

.fm-callout.key {{
  border: 1px solid var(--khaki);
  background: rgba(128,116,84,.07);
  color: var(--ink);
  display: flex;
  align-items: flex-start;
  gap: 12px;
}}
.fm-callout.key::before {{
  content: none;
}}
.fm-callout-key-icon {{
  font-family: var(--f-stencil);
  font-size: 9px;
  letter-spacing: 2px;
  color: var(--khaki-light);
  white-space: nowrap;
  margin-top: 2px;
  text-transform: uppercase;
}}

/* ── SCHÉMA SVG ── */
.fm-schema {{
  margin: 28px 0;
  border: 1px solid var(--khaki);
  background: rgba(0,0,0,.10);
  padding: 20px;
  position: relative;
}}
.fm-schema svg {{
  display: block;
  width: 100%;
  height: auto;
  max-height: 380px;
}}
.fm-schema-legend {{
  margin-top: 10px;
  font-family: var(--f-ui);
  font-size: 10px;
  letter-spacing: 1.5px;
  color: var(--ink);
  text-transform: uppercase;
  text-align: center;
  opacity: .85;
}}

/* ── STUB ── */
.fm-stub {{
  max-width: 860px;
  margin: 0 auto;
  padding: 32px 24px 80px;
}}
.fm-stub-placeholder {{
  margin-top: 32px;
  padding: 40px;
  border: 1px dashed var(--khaki);
  text-align: center;
  opacity: .45;
}}
.fm-stub-placeholder p {{
  font-family: var(--f-stencil);
  font-size: 18px;
  letter-spacing: 4px;
  color: var(--accent-ink);
  text-transform: uppercase;
}}
.fm-stub-placeholder small {{
  font-family: var(--f-ui);
  font-size: 10px;
  letter-spacing: 2px;
  color: var(--khaki);
  text-transform: uppercase;
  display: block;
  margin-top: 8px;
}}

/* ── CHAPTER ACCENT OVERRIDES ── */
#page-rs  {{ --chapter-accent: #C95A9C; --chapter-accent-rgb: 201,90,156; }}
#page-hq  {{ --chapter-accent: #4FB286; --chapter-accent-rgb: 79,178,134; }}
#page-bg  {{ --chapter-accent: #c0892a; --chapter-accent-rgb: 192,137,42; }}
#page-dg  {{ --chapter-accent: #4f7a8e; --chapter-accent-rgb: 79,122,142; }}
#page-rp  {{ --chapter-accent: #7ac97a; --chapter-accent-rgb: 122,201,122; }}
#page-fc  {{ --chapter-accent: #D0784A; --chapter-accent-rgb: 208,120,74; }}

/* Plaques accents individuels */
.fm-plaque[data-module="rs"]  {{ --chapter-accent: #C95A9C; --chapter-accent-rgb: 201,90,156; }}
.fm-plaque[data-module="hq"]  {{ --chapter-accent: #4FB286; --chapter-accent-rgb: 79,178,134; }}
.fm-plaque[data-module="bg"]  {{ --chapter-accent: #c0892a; --chapter-accent-rgb: 192,137,42; }}
.fm-plaque[data-module="rp"]  {{ --chapter-accent: #7ac97a; --chapter-accent-rgb: 122,201,122; }}
.fm-plaque[data-module="dg"]  {{ --chapter-accent: #4f7a8e; --chapter-accent-rgb: 79,122,142; }}
.fm-plaque[data-module="fc"]  {{ --chapter-accent: #D0784A; --chapter-accent-rgb: 208,120,74; }}

/* Exception écrite à R295, pour le contenu des pages du manuel seulement : `strong`, `b` et le reste du contenu gardent le gras du rendu d'origine
   (700 demandé sur Special Elite, qui n'a que sa face 400 : gras synthétisé par le navigateur). La barre et l'interface du manuel restent dans la règle. */
{FM_EXTRA_CSS}
{CONTRAST_CSS}</style>
</head>
<body data-theme="cw-nato">

<!-- ======== TOOLBAR ======== -->
<header class="toolbar">
  <div class="tb-brand">
    <span class="tb-brand-main">FIELD MANUAL</span>
    <span class="tb-brand-short">F·M</span>
    <span class="tb-brand-sub" data-i18n="brand.sub">░ MANUEL OPÉRATIONNEL</span>
  </div>
  <div class="tb-sep" aria-hidden="true"></div>
  <button type="button" id="btn-index" class="tb-btn" onclick="navigate('index')" data-i18n-title="nav.index.tip" title="Retour à l’index du manuel" data-i18n-aria-label="nav.index.tip" aria-label="Retour à l’index du manuel">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>
    <span class="tb-btn-label" data-i18n="nav.index">Index</span>
  </button>
  <button type="button" id="btn-toc" class="tb-btn" onclick="fmTocSet(!fmTocIsOpen(),false)" aria-controls="fmnav-panel" aria-expanded="false" data-i18n-title="nav.contents.tip" title="Sommaire — toutes les pages du manuel et leurs sections" data-i18n-aria-label="nav.contents.tip" aria-label="Sommaire — toutes les pages du manuel et leurs sections">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/></svg>
    <span class="tb-btn-label" data-i18n="nav.contents">Sommaire</span>
  </button>
  <div class="tb-spacer"></div>
  <div class="tb-classif">TRAINING // UNCLASSIFIED</div>
  <button id="btn-lang" aria-label="Passer en anglais" title="Passer en anglais">
    <svg id="flag-svg" viewBox="0 0 20 14" width="22" height="15" xmlns="http://www.w3.org/2000/svg">
      <!-- flag FR par défaut -->
      <rect width="7" height="14" fill="#002395"/>
      <rect x="7" width="6" height="14" fill="#fff"/>
      <rect x="13" width="7" height="14" fill="#ED2939"/>
    </svg>
  </button>
</header>

<!-- ======== SOMMAIRE (panneau) ======== -->
{TOC_HTML}

<!-- ======== MAIN ROOT ======== -->
<main id="fm-root" tabindex="-1">

  <!-- ===== PAGE INDEX ===== -->
  <section id="page-index" class="fm-page">
    <div style="max-width:900px; margin:0 auto; padding:32px 24px 64px;">

      <!-- Couverture -->
      {COVER_HTML}

      <!-- Intro -->
      <div class="fm-intro">
        <div class="lang-block" data-lang="fr">
          <p>La suite DCS Mission Plan tient dans un seul fichier, dcs_mission_plan.html, ou sa version en ligne : on l’ouvre dans le navigateur, et tout marche sans réseau, sauf les fonds de carte et les fiches d’aérodrome du Route Planner.</p>
        </div>
        <div class="lang-block" data-lang="en">
          <p>The DCS Mission Plan suite fits in a single file, dcs_mission_plan.html, or its online version: you open it in the browser, and everything works offline, except the Route Planner’s base maps and airfield sheets.</p>
        </div>
      </div>

      <!-- Index -->
      <div class="fm-plaque-grid">

        <!-- 0 · Par où commencer -->
        <div class="fm-plaque active fm-plaque-wide" data-module="start" tabindex="0" role="button"
             aria-label="0 — Par où commencer"
             onclick="navigate('start')"
             onkeydown="if(event.key==='Enter'||event.key===' '){{event.preventDefault();navigate('start')}}">
          <div class="fm-plaque-monogram">0</div>
          <div class="fm-plaque-info">
            <div class="fm-plaque-name" data-i18n="index.start.name">Par où commencer</div>
            <div class="fm-plaque-desc" data-i18n="index.start.desc">Suite, rôles, gestes</div>
          </div>
        </div>

      </div><!-- /fm-plaque-grid -->

      <p class="fm-section-title">Mission Commander</p>

      <div class="fm-plaque-grid">

        <!-- HQ -->
        <div class="fm-plaque active" data-module="hq" tabindex="0" role="button"
             aria-label="HQ — Wing Command Center"
             onclick="navigate('hq')"
             onkeydown="if(event.key==='Enter'||event.key===' '){{event.preventDefault();navigate('hq')}}">
          <div class="fm-plaque-monogram">HQ</div>
          <div class="fm-plaque-info">
            <div class="fm-plaque-name">HQ</div>
            <div class="fm-plaque-desc" data-i18n="index.hq.desc">Wing, .miz, paquets de vol</div>
          </div>
        </div>

        <!-- BG -->
        <div class="fm-plaque active" data-module="bg" tabindex="0" role="button"
             aria-label="BG — Briefing Generator"
             onclick="navigate('bg')"
             onkeydown="if(event.key==='Enter'||event.key===' '){{event.preventDefault();navigate('bg')}}">
          <div class="fm-plaque-monogram">BG</div>
          <div class="fm-plaque-info">
            <div class="fm-plaque-name">Briefing Generator</div>
            <div class="fm-plaque-desc" data-i18n="index.bg.desc">Briefings Standard et Avancé</div>
          </div>
        </div>

        <!-- RS -->
        <div class="fm-plaque active" data-module="rs" tabindex="0" role="button"
             aria-label="RS — Recon Station"
             onclick="navigate('rs')"
             onkeydown="if(event.key==='Enter'||event.key===' '){{event.preventDefault();navigate('rs')}}">
          <div class="fm-plaque-monogram">RS</div>
          <div class="fm-plaque-info">
            <div class="fm-plaque-name">Recon Station</div>
            <div class="fm-plaque-desc" data-i18n="index.rs.desc">Photos de reconnaissance</div>
          </div>
        </div>

      </div><!-- /fm-plaque-grid -->

      <p class="fm-section-title">Flight Leader</p>

      <div class="fm-plaque-grid">

        <!-- RP -->
        <div class="fm-plaque active" data-module="rp" tabindex="0" role="button"
             aria-label="RP — Route Planner"
             onclick="navigate('rp')"
             onkeydown="if(event.key==='Enter'||event.key===' '){{event.preventDefault();navigate('rp')}}">
          <div class="fm-plaque-monogram">RP</div>
          <div class="fm-plaque-info">
            <div class="fm-plaque-name">Route Planner</div>
            <div class="fm-plaque-desc" data-i18n="index.rp.desc">Routes, carte, navigation</div>
          </div>
        </div>

        <!-- DG -->
        <div class="fm-plaque active" data-module="dg" tabindex="0" role="button"
             aria-label="DG — Datacard Generator"
             onclick="navigate('dg')"
             onkeydown="if(event.key==='Enter'||event.key===' '){{event.preventDefault();navigate('dg')}}">
          <div class="fm-plaque-monogram">DG</div>
          <div class="fm-plaque-info">
            <div class="fm-plaque-name">Datacard Generator</div>
            <div class="fm-plaque-desc" data-i18n="index.dg.desc">Datacards du kneeboard</div>
          </div>
        </div>

        <!-- FC -->
        <div class="fm-plaque active" data-module="fc" tabindex="0" role="button"
             aria-label="FC — Flight Configurator"
             onclick="navigate('fc')"
             onkeydown="if(event.key==='Enter'||event.key===' '){{event.preventDefault();navigate('fc')}}">
          <div class="fm-plaque-monogram">FC</div>
          <div class="fm-plaque-info">
            <div class="fm-plaque-name">Flight Configurator</div>
            <div class="fm-plaque-desc" data-i18n="index.fc.desc">Groupes, radios, emport</div>
          </div>
        </div>

      </div><!-- /fm-plaque-grid -->
    </div>
  </section><!-- /page-index -->


{PAGES_HTML}


</main><!-- /fm-root -->

{ZOOM_HTML}

<script>
/* =============================================
   DCS FIELD MANUAL — JS
   Routing · i18n · Thème
   ============================================= */

// ── i18n ──────────────────────────────────────
var I18N = {{
  fr: {{
    'brand.name':       'Field Manual',
    'brand.sub':        '░ MANUEL OPÉRATIONNEL',
    'index.start.name': 'Par où commencer',
    'index.start.desc': "Suite, rôles, gestes",
    'start.hero.title': 'Par où commencer',
    'index.hq.desc': "Wing, .miz, paquets de vol",
    'index.fc.desc': "Groupes, radios, emport",
    'index.bg.desc': "Briefings Standard et Avancé",
    'index.rs.desc': "Photos de reconnaissance",
    'index.rp.desc': "Routes, carte, navigation",
    'index.dg.desc': "Datacards du kneeboard",
    'index.soon':       'À VENIR',
    'nav.index':        'Index',
    'nav.index.tip':    'Retour à l’index du manuel',
    'nav.contents':     'Sommaire',
    'nav.contents.tip': 'Sommaire — toutes les pages du manuel et leurs sections',
    'nav.close':        'Fermer le sommaire',
    'nav.prev':         '◄ Chapitre précédent',
    'nav.next':         'Chapitre suivant ►',
    'rs.hero.title':    'Recon Station',
    'rs.hero.sub':      'Compositeur photo-renseignement',
    'rs.whatfor.title': 'À quoi ça sert',
    'rs.steps.title':   'Prise en main',
    'rs.schema.legend': 'Fig. 1 — Pipeline de composition et ordre de rendu des calques',
    'hq.hero.title':    'HQ — Wing Command Center',
    'hq.hero.sub':      'Configuration escadre centralisée',
    'fc.hero.title':    'Flight Configurator',
    'fc.hero.sub':      'Un groupe prêt à appliquer : radios, emport, livrée',
    'bg.hero.title':    'Briefing Generator',
    'bg.hero.sub':      'Générateur de briefings multi-sections',
    'dg.hero.title':    'Datacard Generator',
    'dg.hero.sub':      'Datacards de vol pour le kneeboard',
    'rp.hero.title':    'Route Planner',
    'rp.hero.sub':      'Routes, navigation et cartes de mission',
    'zoom.open':        'Agrandir',
    'zoom.close':       'Fermer',
    'zoom.in':          'Zoomer',
    'zoom.out':         'Dézoomer',
    'zoom.fit':         'Ajuster',
    'stub.coming':      'Chapitre en préparation'
  }},
  en: {{
    'brand.name':       'Field Manual',
    'brand.sub':        '░ OPERATIONAL MANUAL',
    'index.start.name': 'Where to start',
    'index.start.desc': 'Suite, roles, gestures',
    'start.hero.title': 'Where to start',
    'index.hq.desc':    'Wing, .miz, flight packages',
    'index.fc.desc':    'Groups, radios, loadout',
    'index.bg.desc':    'Standard and Advanced briefings',
    'index.rs.desc':    'Reconnaissance photos',
    'index.rp.desc':    'Routes, map, navigation',
    'index.dg.desc':    'Kneeboard datacards',
    'index.soon':       'COMING',
    'nav.index':        'Index',
    'nav.index.tip':    'Back to the manual’s index',
    'nav.contents':     'Contents',
    'nav.contents.tip': 'Contents — every page of the manual and its sections',
    'nav.close':        'Close the contents',
    'nav.prev':         '◄ Previous chapter',
    'nav.next':         'Next chapter ►',
    'rs.hero.title':    'Recon Station',
    'rs.hero.sub':      'Photo-intelligence composer',
    'rs.whatfor.title': 'What it does',
    'rs.steps.title':   'Getting started',
    'rs.schema.legend': 'Fig. 1 — Composition pipeline and layer render order',
    'hq.hero.title':    'HQ — Wing Command Center',
    'hq.hero.sub':      'Centralised wing configuration',
    'fc.hero.title':    'Flight Configurator',
    'fc.hero.sub':      'A group ready to apply: radios, loadout, livery',
    'bg.hero.title':    'Briefing Generator',
    'bg.hero.sub':      'Multi-section briefing generator',
    'dg.hero.title':    'Datacard Generator',
    'dg.hero.sub':      'Flight datacards for the kneeboard',
    'rp.hero.title':    'Route Planner',
    'rp.hero.sub':      'Routes, navigation and mission maps',
    'zoom.open':        'Enlarge',
    'zoom.close':       'Close',
    'zoom.in':          'Zoom in',
    'zoom.out':         'Zoom out',
    'zoom.fit':         'Fit',
    'stub.coming':      'Chapter in preparation'
  }}
}};

var CURRENT_LANG = 'fr';
var KEY_LANG  = 'lang_v1';
var KEY_THEME = 'theme_v1';
var KEY_STATE = 'fm_state_v1';

function t(key) {{
  var d = I18N[CURRENT_LANG] || I18N['fr'];
  return d[key] !== undefined ? d[key] : (I18N['fr'][key] || key);
}}

function applyI18n() {{
  document.querySelectorAll('[data-i18n]').forEach(function(el) {{
    el.textContent = t(el.getAttribute('data-i18n'));
  }});
  document.querySelectorAll('[data-i18n-title]').forEach(function(el) {{
    el.title = t(el.getAttribute('data-i18n-title'));
  }});
  document.querySelectorAll('[data-i18n-aria-label]').forEach(function(el) {{
    el.setAttribute('aria-label', t(el.getAttribute('data-i18n-aria-label')));
  }});
  // Les titres des schémas (aria-label) suivent la langue
  document.querySelectorAll('svg[data-aria-fr]').forEach(function(el) {{
    el.setAttribute('aria-label', el.getAttribute(CURRENT_LANG === 'en' ? 'data-aria-en' : 'data-aria-fr'));
  }});
  // Tampons "À VENIR / COMING" sur les plaques soon
  document.querySelectorAll('.fm-soon-stamp').forEach(function(el) {{
    el.textContent = t('index.soon');
  }});
  // Lang attribute sur body
  document.body.lang = CURRENT_LANG;
  document.documentElement.lang = CURRENT_LANG;
  // Drapeau
  updateFlag();
  // Libellés du zoom (images et schémas)
  fmZoomRefresh();
  // La barre se recalcule à la langue (le sous-titre et le drapeau changent)
  uiBarFit();
}}

// ── Drapeaux SVG inline ───────────────────────
var FLAG_FR = '<svg viewBox="0 0 20 14" width="22" height="15" xmlns="http://www.w3.org/2000/svg"><rect width="7" height="14" fill="#002395"/><rect x="7" width="6" height="14" fill="#fff"/><rect x="13" width="7" height="14" fill="#ED2939"/></svg>';
var FLAG_EN = '<svg viewBox="0 0 20 14" width="22" height="15" xmlns="http://www.w3.org/2000/svg"><rect width="20" height="14" fill="#012169"/><path d="M0,0 L20,14 M20,0 L0,14" stroke="#fff" stroke-width="2.8"/><path d="M0,0 L20,14 M20,0 L0,14" stroke="#C8102E" stroke-width="1.6"/><rect x="8" width="4" height="14" fill="#fff"/><rect y="5" width="20" height="4" fill="#fff"/><rect x="9" width="2" height="14" fill="#C8102E"/><rect y="6" width="20" height="2" fill="#C8102E"/></svg>';

function updateFlag() {{
  var btn = document.getElementById('btn-lang');
  if (!btn) return;
  // On montre le drapeau de la langue VERS laquelle on bascule
  btn.innerHTML = CURRENT_LANG === 'fr' ? FLAG_EN : FLAG_FR;
  var tip = CURRENT_LANG === 'fr' ? 'Passer en anglais' : 'Switch to French';
  btn.title = tip;
  btn.setAttribute('aria-label', tip);
}}

function setLang(lang) {{
  if (lang !== 'fr' && lang !== 'en') return;
  CURRENT_LANG = lang;
  try {{ localStorage.setItem(KEY_LANG, lang); }} catch(e) {{}}
  applyI18n();
}}

function toggleLang() {{
  setLang(CURRENT_LANG === 'fr' ? 'en' : 'fr');
}}

function initLang() {{
  try {{
    var stored = localStorage.getItem(KEY_LANG);
    if (stored === 'fr' || stored === 'en') CURRENT_LANG = stored;
  }} catch(e) {{}}
}}

// ── Thème ─────────────────────────────────────
function initTheme() {{
  try {{
    var stored = localStorage.getItem(KEY_THEME);
    if (stored) document.body.setAttribute('data-theme', stored);
  }} catch(e) {{}}
  if (!document.body.getAttribute('data-theme')) {{
    document.body.setAttribute('data-theme', 'cw-nato');
  }}
}}

// ── Routing hash ──────────────────────────────
var PAGES = {PAGES_JS};

function showPage(id, anchor) {{
  if (PAGES.indexOf(id) === -1) id = 'index';
  fmTocSync(id);
  PAGES.forEach(function(pid) {{
    var el = document.getElementById('page-' + pid);
    if (!el) return;
    if (pid === id) {{
      el.classList.remove('hidden');
    }} else {{
      el.classList.add('hidden');
    }}
  }});
  var root = document.getElementById('fm-root');
  if (root) root.scrollTop = 0;
  // Une ancre (#start:gestes) : on descend jusqu'à l'élément de la page
  if (anchor) {{
    var tgt = document.querySelector('#page-' + id + ' [id="' + anchor + '"]');
    // Une ancre qui n'est pas celle d'un titre (la planche de l'accueil) : on descend jusqu'au titre de sa section, juste au-dessus, pour qu'il se lise sous la barre
    if (tgt && !new RegExp('^' + id + '-[0-9]+$').test(anchor)) {{
      var cs = document.querySelectorAll('#page-' + id + ' [id^="' + id + '-"]'), pv = null;
      for (var ci = 0; ci < cs.length; ci++) {{
        if (/^[a-z]+-[0-9]+$/.test(cs[ci].id) && (tgt.compareDocumentPosition(cs[ci]) & 2)) pv = cs[ci];
      }}
      if (pv) tgt = pv;
    }}
    if (tgt && tgt.scrollIntoView) tgt.scrollIntoView();
  }}
  // Persister la dernière page
  try {{ localStorage.setItem(KEY_STATE, JSON.stringify({{page: id}})); }} catch(e) {{}}
}}

function navigate(id) {{
  location.hash = '#' + id;
}}

// ── Sommaire (panneau) et liens de page ───────
function fmTocIsOpen() {{ return document.body.classList.contains('fmnav-open'); }}

// Ouvre ou ferme le panneau ; focus sur × à l'ouverture, sur le bouton Sommaire à la fermeture si back
function fmTocSet(open, back) {{
  var b = document.getElementById('btn-toc'), x = document.getElementById('fmnav-x'), p = document.getElementById('fmnav-panel');
  if (!b || !x || !p || open === fmTocIsOpen()) return;
  document.body.classList.toggle('fmnav-open', open);
  b.setAttribute('aria-expanded', open ? 'true' : 'false');
  p.inert = !open;            // fermé : inert (hors du clavier et des aides techniques) ; ouvert : le focus de × se donne aussitôt, une fois
  if (open) {{
    var cur = p.querySelector('[aria-current]');      // la page courante est en vue dans le panneau
    if (cur) cur.scrollIntoView({{ block: 'nearest', inline: 'nearest' }});
    x.focus({{ preventScroll: true }});
  }} else if (back) b.focus();
}}

// Un lien du sommaire ou du bas de chapitre (le manuel est dans un cadre srcdoc : jamais de href seul) ; le même hash ne déclenche pas hashchange
function fmGo(h) {{
  fmTocSet(false, false);
  if (location.hash === '#' + h) onHashChange(); else location.hash = '#' + h;
  // le panneau devenu inert ne garde pas le focus : il revient au contenu du manuel (au clavier, le lecteur est dans la page)
  var r = document.getElementById('fm-root');
  if (r) r.focus({{ preventScroll: true }});
}}

// La page affichée : Index absent de l'index, aria-current sur la seule ligne de la page
function fmTocSync(id) {{
  var bi = document.getElementById('btn-index');
  if (bi) {{
    var had = (document.activeElement === bi);
    bi.hidden = (id === 'index');
    if (had && bi.hidden) {{ var tb = document.getElementById('btn-toc'); if (tb) tb.focus(); }}   // Index se masque : le focus ne tombe pas sur body
  }}
  document.querySelectorAll('.fmnav-ch').forEach(function(a) {{
    if (a.getAttribute('data-page') === id) a.setAttribute('aria-current', 'page'); else a.removeAttribute('aria-current');
  }});
}}

function onHashChange() {{
  var hash = (location.hash.replace('#', '') || 'index').split(':');
  showPage(hash[0], hash[1]);
}}

{ZOOM_JS}

// ── Réduction de la barre : la séquence commune (ui_block.py) ──
{BAR_JS}
// ── Init ──────────────────────────────────────
function init() {{
  initTheme();
  initLang();
  initZoom();
  applyI18n();

  document.getElementById('btn-lang').addEventListener('click', toggleLang);

  window.addEventListener('hashchange', function() {{ fmTocSet(false, false); }});
  window.addEventListener('hashchange', onHashChange);
  document.addEventListener('keydown', function(e) {{
    if (e.key === 'Escape' && fmTocIsOpen() && !document.body.classList.contains('zm-open')) {{ e.preventDefault(); fmTocSet(false, true); }}
  }});
  onHashChange();
}}

document.addEventListener('DOMContentLoaded', init);
</script>
</body>
</html>
"""

# ── Écriture ─────────────────────────────────────────────────────────────────────

HTML = HTML.replace('<body data-theme="cw-nato">\n', '<body data-theme="cw-nato">\n' + SHELL_ONLY_TAG, 1)

os.makedirs(os.path.join(HERE, 'dist'), exist_ok=True)
OUTPUT_PATH = os.path.join(HERE, 'dist', 'dcs_field_manual.html')
with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
    f.write(HTML)

size_kb = os.path.getsize(OUTPUT_PATH) // 1024
print(f'\n[OK] dcs_field_manual.html écrit ({size_kb} Ko)')

# ── Vérifications ────────────────────────────────────────────────────────────────

with open(OUTPUT_PATH, 'r', encoding='utf-8') as f:
    src = f.read()

# Un [MISSING] ou un [FAIL] fait sortir le build en 1, une fois tous les contrôles écrits (comme node --check).
CHECK_ERRORS = []

def grep_ok(pattern, label):
    found = pattern in src
    status = 'OK' if found else 'MISSING'
    print(f'  [{status}] {label}')
    if not found:
        CHECK_ERRORS.append('MISSING ' + label)
    return found

def grep_absent(pattern, label):
    found = pattern in src
    status = 'FAIL' if found else 'OK'
    print(f'  [{status}] ABSENT: {label}')
    if found:
        CHECK_ERRORS.append('FAIL ABSENT ' + label)
    return not found

print('\n-- Vérifications --')
grep_ok('body[data-theme="cw-nato"]',     '4 thèmes présents : cw-nato')
grep_ok('body[data-theme="cw-soviet"]',   'cw-soviet')
grep_ok('body[data-theme="modern-nato"]', 'modern-nato')
grep_ok('body[data-theme="modern-east"]', 'modern-east')
grep_ok('id="page-index"',  'page-index présent')
grep_ok('id="page-rs"',     'page-rs présent')
grep_ok('id="page-hq"',     'page-hq présent')
grep_ok('id="page-bg"',     'page-bg présent')
grep_ok('id="page-dg"',     'page-dg présent')
grep_ok('id="page-fc"',     'page-fc présent')
grep_ok('Goldwolf',          'crédit de Goldwolf')
grep_ok('--fm-accent:', '--fm-accent présent')
grep_ok('--chapter-accent: #C95A9C', '--chapter-accent RS')
grep_ok('--chapter-accent: #4FB286', '--chapter-accent HQ')
grep_ok('--chapter-accent: #c0892a', '--chapter-accent BG')
grep_ok('--chapter-accent: #4f7a8e', '--chapter-accent DG')
grep_ok('--chapter-accent: #D0784A', '--chapter-accent FC')
grep_ok('class="toolbar"',  'toolbar présent')
# La barre : la séquence de réduction est celle du bloc d'interface commun (ui_block.py), au caractère ; aucun seuil de largeur propre au manuel
grep_ok(BAR_CSS, 'barre : la séquence (feuille) est celle du bloc commun')
grep_ok(BAR_JS,  'barre : la séquence (script) est celle du bloc commun')
if src.count(BAR_CSS) != 1 or src.count(BAR_JS) != 1:
    CHECK_ERRORS.append('FAIL barre : la séquence commune n\'est pas en un seul exemplaire')
grep_absent('max-width: 1359px', 'barre : plus de seuil à 1359 px')
grep_absent('max-width: 1100px', 'barre : plus de seuil à 1100 px')
_bar_media = [l for l in src.splitlines() if l.lstrip().startswith('@media') and ('.tb-' in l or '.toolbar' in l)]
print('  [%s] ABSENT: règle @media qui touche la barre (%d)' % ('OK' if not _bar_media else 'FAIL', len(_bar_media)))
if _bar_media:
    CHECK_ERRORS.append('FAIL ABSENT règle @media sur la barre')
grep_absent('@@BAR', 'emplacement de la séquence résolu')
grep_ok('id="fm-zoom"',     'fenêtre de zoom présente')
grep_ok('role="dialog" aria-modal="true"', 'fenêtre de zoom : role=dialog, aria-modal')
grep_ok('--accent-ink:',    '--accent-ink présent')
# Les schémas de flux (HQ, RP, DG, FC) sont retirés avec leur code : leurs contrôles de marqueur propre sont remplacés par ceux des schémas redessinés
grep_ok('id="bm"',          'schéma BG : marqueur propre')
grep_ok('id="dga"',         'schéma anatomie de la datacard : marqueur propre')
grep_absent('id="dgf"',     'figure 2 DG (flux) retirée')
grep_absent('Du groupe au paquet', 'schéma de flux du FC retiré')
grep_absent('LE HUB DE LA SUITE',  'schéma de flux d\'HQ retiré')
grep_ok('class="fm-plate" id="gestes"', 'Par où commencer : la planche des gestes a son ancre')
grep_ok('Les gestes, et ce qu’ils gardent', 'Par où commencer : la section des gestes')
grep_ok('Restauration impossible', 'Par où commencer : Restaurer refusé (FR)')
grep_ok('Cannot restore: the data has changed since.', 'Par où commencer : Restaurer refusé (EN)')
grep_ok('viewBox="0 0 720 425"', 'schéma BG refait (720 × 425)')
grep_absent('MT_onModuleSave', 'MT_onModuleSave absent')
grep_absent('app-header',      'app-header absent')
grep_absent('4th VEAW',        '4th VEAW absent')
grep_absent('KHR-26',          'KHR-26 absent')
# Les deux formats du Briefing Generator s'appellent Standard et Avancé, partout dans le manuel
for _old in ('brief simplifié', 'brief complet', 'quick brief', 'full brief', 'simplifiée', 'quick-brief'):
    grep_absent(_old, 'ancien nom de format « ' + _old + ' » absent')

# La livrée : le champ du Flight Configurator affiche toujours un nom ; la livrée par défaut d'un type se déclare dans la fenêtre Wing de HQ
grep_ok('Il affiche toujours un nom, et c’est ce nom que le paquet emporte.', 'Flight Configurator : le champ Livrée affiche toujours un nom (FR)')
grep_ok('It always shows a name, and that name is what the package carries.', 'Flight Configurator : le champ Livrée affiche toujours un nom (EN)')
grep_ok('Sous elles, la <strong>livrée par défaut</strong> de chaque appareil', 'HQ : la livrée par défaut de chaque appareil (FR)')
grep_ok('Below them, each aircraft’s <strong>default livery</strong>', 'HQ : la livrée par défaut de chaque appareil (EN)')
# Route Planner : le libellé de l'entrée d'Ouvrir ▾ dit qu'elle lit aussi les calques CombatFlite ; HQ : la fenêtre Wing en lecture seule, les boîtes de livrées repliables
# l'ancien libellé n'est plus cité nulle part dans le manuel rendu : « route » suivi aussitôt de « … » ou de trois points ASCII (le nouveau a « ou des calques » / « or layers » entre les deux)
for _pat, _lg in ((r'Ouvrir une route\s*(?:…|\.{3})', 'FR'), (r'Open a route\s*(?:…|\.{3})', 'EN')):
    _old = re.findall(_pat, src)
    print('  [%s] ABSENT: Route Planner : l\'ancien libellé (%s) n\'est plus cité (%d)' % ('OK' if not _old else 'FAIL', _lg, len(_old)))
    if _old:
        CHECK_ERRORS.append('FAIL ABSENT ancien libellé Route Planner ' + _lg)
for _lab, _lg in (('Ouvrir une route ou des calques…', 'FR'), ('Open a route or layers…', 'EN')):
    _n = src.count(_lab)
    print('  [%s] Route Planner : « %s » cité au moins trois fois (%d)' % ('OK' if _n >= 3 else 'ÉCHEC', _lab, _n))
    if _n < 3:
        CHECK_ERRORS.append('libellé Route Planner ' + _lg)
grep_ok('Quand la configuration est fournie par un autre outil, la fenêtre la montre sans laisser la modifier\u202f: une note dit où elle se modifie, et l’Exemple d’HQ est inactif.', 'HQ : le Wing fourni par un autre outil est en lecture seule (FR)')
grep_ok('When the configuration is provided by another tool, the window shows it without letting you change it: a note says where to edit it, and HQ’s Example is off.', 'HQ : le Wing fourni par un autre outil est en lecture seule (EN)')
grep_ok('Les livrées custom et la livrée par défaut se replient comme les escadrons, et sont fermées à l’ouverture de la page.', 'HQ : les boîtes de livrées se replient (FR)')
grep_ok('The custom liveries and the default livery fold like the squadrons, and are closed when the page opens.', 'HQ : les boîtes de livrées se replient (EN)')
grep_absent('Inchangée', 'plus d\'« Inchangée » dans le manuel')
grep_absent('Unchanged', 'plus d\'« Unchanged » dans le manuel')

# La navigation du manuel : Index et Sommaire dans la barre, le panneau de sommaire, une ancre par h3, le bas de chapitre ; l'ancien bouton « ◄ Index » n'existe plus
print('\n-- Navigation (barre, sommaire, bas de chapitre) --')
_hdr = src[src.index('<header class="toolbar">'):src.index('</header>')]
_ord = [_hdr.find(k) for k in ('class="tb-brand"', 'class="tb-sep"', 'id="btn-index"', 'id="btn-toc"', 'class="tb-spacer"', 'class="tb-classif"', 'id="btn-lang"')]
print('  [%s] barre : sigle, séparateur, Index, Sommaire, espace, classification, langue, dans cet ordre' % ('OK' if all(x >= 0 for x in _ord) and _ord == sorted(_ord) else 'FAIL'))
if not (all(x >= 0 for x in _ord) and _ord == sorted(_ord)):
    CHECK_ERRORS.append('FAIL barre : ordre')
for _id in ('btn-index', 'btn-toc'):
    _b = re.search(r'<button type="button" id="' + _id + r'" class="tb-btn"[^>]*>.*?</button>', _hdr, re.S)
    _ok = bool(_b) and '<svg' in _b.group(0) and 'class="tb-btn-label"' in _b.group(0) and 'aria-label=' in _b.group(0) and 'title=' in _b.group(0)
    print('  [%s] bouton %s : tb-btn, icône SVG, libellé, infobulle, aria-label' % ('OK' if _ok else 'FAIL', _id))
    if not _ok:
        CHECK_ERRORS.append('FAIL bouton ' + _id)
grep_ok('aria-controls="fmnav-panel" aria-expanded="false"', 'Sommaire : aria-controls et aria-expanded')
grep_ok('<nav class="fmnav-panel" id="fmnav-panel"', 'sommaire : le panneau est dans le HTML du build')
grep_ok('id="fmnav-x"', 'sommaire : le bouton ×')
grep_ok('<nav class="fmnav-panel" id="fmnav-panel" inert', 'sommaire : fermé, le panneau est inert')
_pr = re.findall(r'(?:body\.fmnav-open )?\.fmnav-panel\s*\{[^}]*\}', src)
print('  [%s] sommaire : aucune déclaration visibility dans les règles du panneau (%d règles lues)' % ('OK' if _pr and not any('visibility' in r_ for r_ in _pr) else 'FAIL', len(_pr)))
if not _pr or any('visibility' in r_ for r_ in _pr):
    CHECK_ERRORS.append('FAIL visibility sur le panneau')
grep_absent('fm-back-btn', 'l\'ancien bouton « ◄ Index » de la page (et sa règle)')
grep_absent('btn.back', 'la clé btn.back (plus lue)')
_rows = re.findall(r'<a class="fmnav-ch" href="#(\w+)"', src)
print('  [%s] sommaire : huit lignes de page, dans l\'ordre de PAGES (%s)' % ('OK' if _rows == _ORDER else 'FAIL', ','.join(_rows)))
if _rows != _ORDER:
    CHECK_ERRORS.append('FAIL sommaire : lignes de page')
_h3 = {pid: len(re.findall(r'<h3 class="lang-block" data-lang="fr"', re.search(r'<section id="page-' + pid + r'".*?<!-- /page-' + pid + ' -->', src, re.S).group(0))) for pid in _ORDER[1:]}
_anc = re.findall(r'<span id="(\w+)-(\d+)"></span>', src)
_sec = re.findall(r'<a class="fmnav-sec" href="#(\w+):(\w+-\d+)"', src)
_okanc = all(sorted(int(n) for p_, n in _anc if p_ == pid) == list(range(1, _h3[pid] + 1)) for pid in _ORDER[1:]) and len(_anc) == len(set(_anc)) == sum(_h3.values())
_oksec = [(a, b) for a, b in _sec] == [(a, f'{a}-{n}') for a, n in _anc]
# le texte FR / EN de chaque ligne de section est celui du h3 qui suit son ancre
_h3s = re.findall(r'<span id="(\w+-\d+)"></span>\s*<h3 class="lang-block" data-lang="fr">(.*?)</h3>\s*<h3 class="lang-block" data-lang="en">(.*?)</h3>', src, re.S)
_lines = re.findall(r'<a class="fmnav-sec" href="#\w+:(\w+-\d+)"[^>]*><span class="lang-block" data-lang="fr">(.*?)</span><span class="lang-block" data-lang="en">(.*?)</span></a>', src, re.S)
_oksec = _oksec and len(_h3s) == len(_lines) == len(_sec) and all(a == b and _plain(c) == d and _plain(e) == f for (a, c, e), (b, d, f) in zip(_h3s, _lines))
print('  [%s] sommaire : une ligne de section par ancre (%d)' % ('OK' if _oksec else 'FAIL', len(_sec)))
print('  [%s] ancres des h3 : une par titre, numérotées de 1 à n dans chaque page (%d)' % ('OK' if _okanc else 'FAIL', len(_anc)))
if not _okanc: CHECK_ERRORS.append('FAIL ancres des h3')
if not _oksec: CHECK_ERRORS.append('FAIL lignes de section')
_pn = len(re.findall(r'<div class="fmnav-pn">', src))
print('  [%s] bas de chapitre : une paire de cases par page sauf l\'index (%d)' % ('OK' if _pn == 7 else 'FAIL', _pn))
if _pn != 7: CHECK_ERRORS.append('FAIL bas de chapitre')
_i = [m.start() for m in re.finditer(r'<div class="fmnav-pn">', src)]
_lastchild = all(re.match(r'<div class="fmnav-pn">.*?</div>\s*</div><!-- /fm-chapter -->', src[k:], re.S) for k in _i)
print('  [%s] bas de chapitre : dernier enfant de .fm-chapter' % ('OK' if _lastchild else 'FAIL'))
if not _lastchild: CHECK_ERRORS.append('FAIL bas de chapitre : place')
# la couleur d'accent du sigle au sommaire est celle de la page (la feuille #page-xx)
_bad = [_pid for _pid, _hex in _ACCENT_HEX.items() if not re.search(r'#page-' + _pid + r'\s*\{\s*--chapter-accent:\s*' + re.escape(_hex) + ';', src)]
if _bad:
    CHECK_ERRORS.append('FAIL accent des sigles du sommaire : ' + ','.join(_bad))
print('  [%s] accents des sigles du sommaire = ceux des chapitres' % ('OK' if not _bad else 'FAIL ' + ','.join(_bad)))
grep_ok('id="fmnav-ov"', 'sommaire : le voile')
grep_ok('data-i18n-aria-label="nav.close"', 'sommaire : × nommé (FR/EN)')

# Vérifier les paires lang-block
fr_count = src.count('data-lang="fr"')
en_count = src.count('data-lang="en"')
status = 'OK' if fr_count == en_count else 'FAIL'
print(f'  [{status}] paires lang-block : fr={fr_count} en={en_count}')
if fr_count != en_count:
    CHECK_ERRORS.append('FAIL paires lang-block')

# Les planches d'écran : chaque libellé dessiné vient du dictionnaire de son outil (lu dans son source), et aucun <text> n'échappe aux deux fonctions
print('\n-- Planches d\'écran --')
for _pl in PLATES:
    print('  [OK] ' + planche_report(_pl))
    for _m in _pl.mixed:
        print('        texte mixte (donnée + libellé), à relire : ' + _m)
for _e in PLANCHE_ERRORS:
    print('  [FAIL] ' + _e)
    CHECK_ERRORS.append(_e)
_np = len(re.findall(r'class="fm-plate"', src))
print('  [%s] planches posées dans la page : %d, construites : %d' % ('OK' if _np == len(PLATES) else 'FAIL', _np, len(PLATES)))
if _np != len(PLATES):
    CHECK_ERRORS.append('FAIL planches posées')

# ── node --check sur TOUS les scripts inline ──────────────────────────────────────

print('\n-- node --check scripts inline --')
src_nocomments = re.sub(r'<!--.*?-->', '', src, flags=re.S)
scripts = re.findall(r'<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>', src_nocomments, flags=re.S)
print(f'  {len(scripts)} script(s) inline trouvé(s)')
all_ok = True
for i, script in enumerate(scripts):
    with tempfile.NamedTemporaryFile(suffix='.js', mode='w', encoding='utf-8', delete=False) as tmp:
        tmp.write(script)
        tmp_path = tmp.name
    result = subprocess.run(['node', '--check', tmp_path], capture_output=True, text=True)
    os.unlink(tmp_path)
    if result.returncode != 0:
        print(f'  [FAIL] Script #{i+1} : {result.stderr.strip()[:200]}')
        all_ok = False
    else:
        print(f'  [OK] Script #{i+1} ({len(script)//1024} Ko) — node --check PASS')

if not all_ok:
    CHECK_ERRORS.append('node --check')

if not CHECK_ERRORS:
    print('\n[BUILD DONE]')
else:
    print('\n[BUILD ÉCHEC] ' + str(len(CHECK_ERRORS)) + ' contrôle(s) en échec : ' + ' ; '.join(CHECK_ERRORS), file=sys.stderr)
    sys.exit(1)
