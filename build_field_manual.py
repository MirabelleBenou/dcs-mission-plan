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

# ── Schémas générés (BG « Ce qui alimente quoi », écran du RP, anatomie de la datacard) ──
# Règle de lisibilité : la couleur d'un module marque (trait, aplat à 20 %), l'encre écrit.

from fm_schemas_block import (NF, fr_typo, _esc, SCHEMAS_CSS, s0_html, build_bg_svg, build_rp_screen_svg, build_dg_anatomy_svg, panel_html, panel_ids, TABLE_IDS)
from fm_planches_block import PLANCHES_CSS, PLANCHE_ERRORS, PLATES, build_plate_hq, check_report as planche_report

_NBSP_FINE = NF   # espace fine insécable (typographie française)

BG_SVG = build_bg_svg()
RP_SCREEN_SVG = build_rp_screen_svg()
DG_ANATOMY_SVG = build_dg_anatomy_svg()
# Les planches d'écran : l'écran de l'outil au trait, des bulles numérotées, une légende numérotée ; leurs libellés viennent du dictionnaire de l'outil
HQ_PLATE_HTML = build_plate_hq()

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

/* ── La table des gestes de « Par où commencer » ── */
.fm-gt { width: 100%; border-collapse: collapse; margin: 6px 0 18px; font-size: 13px; line-height: 1.55; }
.fm-gt th { text-align: left; font-family: var(--f-stencil); font-size: 11px; letter-spacing: 2px; text-transform: uppercase; color: var(--accent-ink); padding: 6px 8px; border-bottom: 2px solid var(--chapter-accent, var(--fm-accent)); }
.fm-gt td { vertical-align: top; padding: 8px; border-bottom: 1px solid rgba(0,0,0,.18); color: var(--ink); }
.fm-gt td:first-child { width: 22%; }
@media (max-width: 700px) {
  .fm-gt, .fm-gt tbody, .fm-gt tr, .fm-gt td { display: block; width: 100%; box-sizing: border-box; }
  .fm-gt thead { display: none; }
  .fm-gt tr { border-bottom: 1px solid rgba(0,0,0,.18); padding: 6px 0; }
  .fm-gt td { border: 0; padding: 3px 0; }
  .fm-gt td:first-child { width: 100%; font-size: 14px; }
  .fm-gt td[data-h]:not(:first-child)::before { font-weight: 700; }
  body[lang="fr"] .fm-gt td[data-h]:not(:first-child)::before { content: attr(data-h) "\202F: "; }
  body[lang="en"] .fm-gt td[data-h]:not(:first-child)::before { content: attr(data-h) ": "; }
}

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
  zm.opener = el;
  zm.schema = el.classList.contains('fm-schema');
  zm.box.innerHTML = '';
  zm.box.style.width = '';
  zm.box.style.removeProperty('--zs');
  var label = '';
  var nat = null, img = null;
  if (zm.schema) {
    var svg = el.querySelector('svg');
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
# tbl (table), raw (HTML tel quel, panneaux et schémas). Les liens : [[page|texte]] (page : hq, bg, rs, fc, rp, dg, start, start:gestes).

def _typo_fr(t):
    t = t.replace('« ', '«' + _NBSP_FINE).replace(' »', _NBSP_FINE + '»')
    return fr_typo(t)

def _md(t, fr=False):
    t = _esc(t)
    t = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', t)
    t = re.sub(r'`(.+?)`', r'<code>\1</code>', t)
    t = re.sub(r'\[\[([\w:]+)\|(.+?)\]\]', r'<a href="#\1" onclick="location.hash=&#39;\1&#39;;return false">\2</a>', t)
    return _typo_fr(t) if fr else t

def _lb(lang, inner, tag='div'):
    return f'<{tag} class="lang-block" data-lang="{lang}">{inner}</{tag}>'

def _render(blocks):
    """Les blocs d'une page en HTML ; chaque bloc écrit FR puis EN (parité exacte)."""
    out, prose = [], []
    def flush():
        if prose:
            out.append('      <div class="fm-prose">\n        ' + '\n        '.join(prose) + '\n      </div>')
            prose.clear()
    for kind, fr, en in blocks:
        if kind == 'raw':
            flush(); out.append(fr)
        elif kind == 'h':
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
        elif kind == 'tbl':
            def tb(rows, f):
                head, body = rows[0], rows[1:]
                return ('<table class="fm-gt"><thead><tr>' + ''.join('<th>' + _md(c, f) + '</th>' for c in head) + '</tr></thead><tbody>'
                        + ''.join('<tr>' + ''.join('<td data-h="' + _esc(head[i]) + '">' + _md(c, f) + '</td>' for i, c in enumerate(r)) + '</tr>' for r in body)
                        + '</tbody></table>')
            prose.append(_lb('fr', tb(fr, True))); prose.append(_lb('en', tb(en, False)))
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

def _page(pid, blocks):
    if pid != 'start':
        # sous « Les gestes », les sous-sections prennent un niveau de titre en dessous (h4)
        seen, nb = False, []
        for k, f, e in blocks:
            if k == 'h' and f == 'Les gestes':
                seen = True
            elif k == 'h' and seen:
                k = 'h4'
            nb.append((k, f, e))
        blocks = nb
    style = f' style="--chapter-accent:{_ACCENT[pid]};"' if pid in _ACCENT else ''
    hero = _hero(pid, _MONO[pid], _TILE.get(pid), _ALT.get(pid, ''))
    hero = hero.replace('{TITLE}', _esc(_HERO_TXT[pid][0])).replace('{SUB}', _esc(_HERO_TXT[pid][1] or ''))
    return (f'  <section id="page-{pid}" class="fm-page hidden">\n    <div class="fm-chapter"{style}>\n\n'
            f'      <button class="fm-back-btn" onclick="navigate(\'index\')" data-i18n="btn.back">◄ Index</button>\n\n{hero}\n\n'
            + _render(blocks) + f'\n\n    </div><!-- /fm-chapter -->\n  </section><!-- /page-{pid} -->\n')

PAGES_SRC = {}

# ── Par où commencer ─────────────────────────────────────────────────────────────
PAGES_SRC['start'] = [
    ('raw', S0_HTML, ''),
    ('p', ['Mission Plan prépare une mission à deux rôles. Le **Mission Commander** la prépare pour toute l’escadre : HQ (le Wing, puis le .miz de chaque mission), le Briefing Generator (le briefing) et Recon Station (les photos). Chaque **Flight Leader** prépare le vol de son groupe : le Route Planner (la route), le Datacard Generator (la datacard du kneeboard) et le Flight Configurator (radios, emport, livrée, paquet de vol). Chaque chapitre détaille ce que son outil prend et donne dans son panneau Reçoit · Donne.'], ['Mission Plan prepares a mission in two roles. The **Mission Commander** prepares it for the whole wing: HQ (the Wing, then the .miz of each mission), the Briefing Generator (the briefing) and Recon Station (the photos). Each **Flight Leader** prepares their group’s flight: the Route Planner (the route), the Datacard Generator (the kneeboard datacard) and the Flight Configurator (radios, loadout, livery, flight package). Each chapter details what its tool takes and gives in its Receives · Gives panel.']),
    ('h', "Ouvrir Mission Plan", "Opening Mission Plan"),
    ('p', ['Ouvrez **dcs_mission_plan.html**, ou sa version en ligne : c’est l’accueil, et les six outils s’ouvrent depuis leur carte. Un outil ouvert seul n’affiche qu’une ligne qui renvoie vers Mission Plan : les échanges passent par l’accueil. Tout marche sans réseau, sauf les fonds de carte et les fiches d’aérodrome du Route Planner.'], ['Open **dcs_mission_plan.html**, or its online version: it is the home page, and the six tools open from their card. A tool opened on its own shows only a line pointing to Mission Plan: the exchanges go through the home page. Everything works offline, except the Route Planner’s base maps and airfield sheets.']),
    ('h', "Le retour au Mission Commander", "The return to the Mission Commander"),
    ('p', ['Les trois outils du Flight Leader partagent leurs groupes en direct : leur ordre n’est pas imposé, mais pour une datacard complète le Flight Configurator (emport, carburant, poids) passe avant l’export du Datacard Generator. Le seul retour qui se **fusionne** est le paquet de vol du Flight Configurator : rouvrir le fichier de travail d’un Flight Leader remplace tout le travail, et plusieurs Flight Leaders ne se rassemblent que par leurs paquets.'], ['The three Flight Leader tools share their groups live: their order is not imposed, but for a complete datacard the Flight Configurator (loadout, fuel, weight) comes before the Datacard Generator export. The only return that **merges** is the Flight Configurator’s flight package: reopening a Flight Leader’s work file replaces all the work, and several Flight Leaders come together only through their packages.']),
    ('anchor', 'gestes', ''),
    ('h', "Les gestes, et ce qu’ils gardent", "The gestures, and what they keep"),
    ('p',
     ["Les mêmes gestes ont le même sens dans tous les outils. La table dit lesquels remplacent du travail, et ce qui reste."],
     ["The same gestures mean the same thing in every tool. The table says which ones replace work, and what stays."]),
    ('tbl',
     [["Geste", "Ce qu’il fait", "Ce qu’il garde"],
      ["**Ouvrir…** (accueil), **Ouvrir ▾ › Ouvrir un travail…** (outils)", "Relit un fichier de travail et **remplace tout le travail**.", "Vos presets d’emport, le Wing, la mission d’HQ, la langue et le thème ; vos unités et réglages de cap si le fichier n’en porte pas."],
      ["**Sauvegarder** (accueil et chaque outil sauf HQ ; Ctrl+S, Cmd+S sur Mac)", "Écrit le fichier de travail de toute la suite : briefing, composition de RS, groupes, routes, calques, datacards. HQ écrit le .miz par **Sauvegarder .miz**.", "Hors du fichier : le Wing, la mission d’HQ, l’image source de RS, les presets d’emport."],
      ["**Exemple ▾** (barre de l’accueil, seulement : les outils n’ont pas ce menu ; HQ a son bouton Exemple)", "Deux lignes. **Mission Commander** : un briefing et une photo (BG, RS). **Flight Leader** : une route, un groupe et sa datacard (RP, DG, FC). Remplace le travail de ce groupe d’outils, sans question.", "L’autre groupe, vos unités et réglages de cap. Le bouton d’HQ ouvre une escadre de démonstration et garde la vôtre."],
      ["**Effacer**", "BG : le briefing. RS : l’image, les annotations, la légende et le bloc d’informations. RP, DG, FC : « Tout effacer ? » vide les groupes, les routes, les calques et les datacards des trois outils (au RP, une fenêtre à cocher). HQ : retire la mission ouverte. Après confirmation.", "RS : logos, réglages, Wing. RP, DG, FC : presets, théâtre, unités, réglages. HQ : le Wing."],
      ["**Restaurer**", "Après un Exemple ou un Ouvrir, un message le propose pendant douze secondes et rend le travail d’avant ; après deux remplacements de suite, l’état d’avant le premier.", "**Refusé** dès que vous avez saisi quelque chose : « Restauration impossible : les données ont changé depuis. »"]],
     [["Gesture", "What it does", "What it keeps"],
      ["**Open…** (home page), **Open ▾ › Open a work file…** (tools)", "Reads a work file and **replaces all the work**.", "Your loadout presets, the Wing, the HQ mission, the language and the theme; your units and heading settings if the file carries none."],
      ["**Save** (home page and every tool except HQ; Ctrl+S, Cmd+S on Mac)", "Writes the work file of the whole suite: briefing, RS composition, groups, routes, layers, datacards. HQ writes the .miz with **Save .miz**.", "Left out of the file: the Wing, the HQ mission, the RS source image, the loadout presets."],
      ["**Example ▾** (home page top bar only: the tools have no such menu; HQ has its Example button)", "Two lines. **Mission Commander**: a briefing and a photo (BG, RS). **Flight Leader**: a route, a group and its datacard (RP, DG, FC). Replaces the work of that tool group, without asking.", "The other group, your units and heading settings. HQ’s button opens a demonstration wing and keeps yours."],
      ["**Clear**", "BG: the briefing. RS: the image, the annotations, the legend and the info block. RP, DG, FC: “Clear everything?” empties the groups, routes, layers and datacards of the three tools (in the RP, a window with tick boxes). HQ: removes the open mission. After a confirmation.", "RS: logos, settings, Wing. RP, DG, FC: presets, theatre, units, settings. HQ: the Wing."],
      ["**Restore**", "After an Example or an Open, a message offers it for twelve seconds and brings back the previous work; after two replacements in a row, the state before the first.", "**Refused** as soon as you have typed something: “Cannot restore: the data has changed since.”"]]),
    ('p',
     ["Les fenêtres Sauvegarder et Exporter (RS, BG, DG, paquets de vol) demandent un nom de fichier, proposé et modifiable."],
     ["The Save and Export windows (RS, BG, DG, flight packages) ask for a file name, proposed and editable."]),
    ('h', "La fenêtre d’import commune", "The common import window"),
    ('p', ['Le Route Planner (Importer des routes…), le Datacard Generator (menu … des cartes › Importer des groupes) et le Flight Configurator (Importer des groupes…) ouvrent la même fenêtre. On choisit une source : la mission d’HQ, le briefing en cours ou un fichier (paquet de vol, ancien fichier de briefing). On coche les groupes et, pour chacun, ce qu’il apporte : route, radios, emport, livrée. Un groupe de même nom et coalition est complété, sinon créé ; les routes d’un autre théâtre ne sont pas importées, et un appareil inconnu arrive sans type, à choisir.'], ['The Route Planner (Import routes…), the Datacard Generator (cards … menu › Import groups) and the Flight Configurator (Import groups…) open the same window. You pick a source: the HQ mission, the current briefing or a file (flight package, old briefing file). You tick the groups and, for each, what it brings: route, radios, loadout, livery. A group with the same name and coalition is completed, otherwise it is created; routes from another theatre are not imported, and an unknown aircraft arrives without a type, to be chosen.']),
    ('h', "La barre du haut", "The top bar"),
    ('p', ['La barre est la même dans les six outils : les boutons de fichier juste après le sigle, puis les réglages. Quand la place manque, les boutons **perdent leur texte par étapes**, Affichage d’abord, et gardent leur icône et leur info-bulle ; au téléphone ou à la tablette, tous sont des icônes. Elle défile au doigt quand elle ne tient pas. L’icône à droite de l’en-tête d’une section **replie ou déplie toutes les sections**, dans les six outils ; au téléphone ou à la tablette, l’éditeur du BG et du DG passe en onglets.', 'Sous la barre du BG, du RP, du DG et du FC, la **ligne de mission d’HQ** dit quel .miz est ouvert dans HQ, sa date et son heure, et ce que l’outil en prend. Au RP, au DG et au FC, elle passe en rouge, « Non utilisée ici : autre théâtre », quand la mission n’est pas celle du théâtre de l’outil ; au BG, jamais.'], ['The bar is the same in all six tools: the file buttons right after the abbreviation, then the settings. When room runs out, the buttons **lose their text in stages**, Display first, and keep their icon and tooltip; on a phone or tablet, all of them are icons. It scrolls by finger when it does not fit. The icon at the right of a section header **folds or unfolds all the sections**, in all six tools; on a phone or tablet, the BG and DG editor switches to tabs.', 'Under the bar of the BG, RP, DG and FC, the **HQ mission line** says which .miz is open in HQ, its date and time, and what the tool takes from it. In the RP, DG and FC it turns red, “Not used here: other theatre”, when the mission is not on the tool’s theatre; in the BG, never.']),
    ('h', "Lire ce manuel au téléphone", "Reading this manual on a phone"),
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
    ('h', "Standard ou Avancé", "Standard or Advanced"),
    ('p', ['Le menu **Affichage ▾** de la barre choisit le format ; un point ambre sur le bouton signale Avancé. **Changer de format ne perd rien** : seules les sections affichées et les pages produites changent, et ce que vous avez saisi pour l’autre format revient quand vous y retournez.'], ['The **Display ▾** menu of the bar chooses the format; an amber dot on the button marks Advanced. **Changing format loses nothing**: only the sections shown and the pages produced change, and what you entered for the other format comes back when you return to it.']),
    ('h', "Démarrer", "Starting"),
    ('p',
     ["L’outil s’ouvre sur une **page blanche**, en Standard ; les champs vides disent en grisé ce qu’on y met, et cet indice n’est ni dans l’aperçu ni à l’export. **Effacer** vide tout le briefing, après confirmation. L’exemple et ses effets sont dans [[start:gestes|Par où commencer]]."],
     ["The tool opens on a **blank page**, in Standard; empty fields say in grey what goes in them, and that hint is neither in the preview nor in the export. **Clear** empties the whole briefing, after a confirmation. The example and its effects are in [[start:gestes|Where to start]]."]),
    ('h', "Le brief Standard", "The Standard brief"),
    ('p', ['Le brief Standard est une page de mission : situation, mission et groupes, fréquences, terrains et météo. Une date qui n’a pas la forme attendue est gardée telle quelle, et le champ prend la couleur d’avertissement. La carte, les menaces et les cibles sont communes aux deux formats : si une carte est chargée, ou si des menaces ou des cibles sont saisies, une page de carte suit, puis les pages de photos. Un bloc vide n’est pas imprimé, et une page qui déborde se poursuit sur la suivante.'], ['The Standard brief is one mission page: situation, mission and groups, frequencies, airfields and weather. A date that does not have the expected form is kept as it is, and the field takes the warning colour. The map, the threats and the targets are common to both formats: if a map is loaded, or threats or targets are entered, a map page follows, then the photo pages. An empty block is not printed, and a page that overflows continues on the next one.']),
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
    ('h', "Sauvegarder et exporter", "Saving and exporting"),
    ('p', ['Le briefing est gardé automatiquement dans le navigateur. **Ouvrir ▾ › Ouvrir un briefing…** lit un ancien fichier de briefing, le format choisi voyageant avec lui. Pour exporter, vérifiez la mise en page dans l’Aperçu, puis **Exporter** : l’export porte les pages du format en cours, en PDF (par l’impression du navigateur, Ctrl+P puis « Enregistrer en PDF », y compris sur Android) ou en PNG par page.'], ['The briefing is kept automatically in the browser. **Open ▾ › Open a briefing…** reads an old briefing file, the chosen format travelling with it. To export, check the layout in the Preview, then **Export**: the export carries the pages of the current format, as a PDF (through the browser’s print, Ctrl+P then “Save as PDF”, on Android too) or as one PNG per page.']),
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
    ('h', "Préparer la photo", "Setting up the photo"),
    ('p', ['L’image est d’abord convertie en niveaux de gris. **Contraste** accentue ou adoucit les écarts ; **Imagerie** donne l’allure d’un capteur, par stylisation du signal et non par mesure ; **Vignette**, **Grain** et **Scanlines**, éteints par défaut, ajoutent l’usure d’un tirage. Recon ne peint jamais d’élément absent de l’image.'], ['The image is first converted to greyscale. **Contrast** sharpens or softens the differences; **Imagery** gives the look of a sensor, by stylising the signal and not by measurement; **Vignette**, **Grain** and **Scanlines**, off by default, add the wear of a print. Recon never paints an element that is not in the image.']),
    ('h', "Annoter", "Annotating"),
    ('p', ['**+ AJOUTER UN MARQUAGE** dépose un cercle numéroté, à glisser sur la cible, lié à une ligne de légende du cartouche ; la numérotation se recalcule toute seule, et l’Amorce tire un trait jusqu’au point exact de la cible. **+ AJOUTER UNE LOUPE** réaffiche, agrandie, une portion de l’image traitée ; la zone et la boîte se déplacent et se redimensionnent sans déformer l’image. Les formes et les étiquettes se posent au centre, puis se déplacent. Le bandeau de classification, éteint par défaut, réserve sa place pour ne recouvrir ni le cartouche ni le bloc d’informations ; il est distinct du champ Classification du bloc.'], ['**+ ADD MARKER** drops a numbered circle, to drag onto the target, tied to a legend line of the cartouche; the numbering recalculates by itself, and the **Leader** draws a line to the exact point of the target. **+ ADD MAGNIFIER** redisplays, enlarged, a portion of the processed image; the zone and the box move and resize without distorting the image. Shapes and labels are placed at the centre, then moved. The classification banner, off by default, reserves its place so as not to cover the cartouche or the information block; it is separate from the block’s Classification field.']),
    ('h', "Le bloc d’informations et les logos", "The info block and the logos"),
    ('p', ['En bas, le **bloc d’informations** : les champs vides ne s’impriment pas. À l’ouverture de RS, le briefing du BG préremplit le bloc ; un champ déjà rempli n’est jamais écrasé. Les logos du Wing d’HQ sont proposés dans la grille Logo, marqués Wing ; vous pouvez en ajouter par une image PNG, et chaque logo se rend en couleur, en niveaux de gris ou en blanc.'], ['At the bottom, the **information block**: empty fields are not printed. When RS opens, the BG’s briefing pre-fills the block; a field already filled is never overwritten. The HQ Wing logos are offered in the Logo grid, marked Wing; you can add some from a PNG image, and each logo renders in colour, greyscale or white.']),
    ('h', "Ouvrir, sauvegarder, exporter", "Opening, saving, exporting"),
    ('p', ['**Ouvrir ▾** (Ouvrir un travail…, Ouvrir une image…) et **Sauvegarder**, Ctrl+S, rangent la composition dans le fichier de travail, sans l’image source : après un rechargement de la page, importez de nouveau l’image. **Exporter** propose un nom (la cible et l’heure), que vous pouvez changer, et écrit un PNG sans perte à la résolution de la source ; l’aperçu à l’écran est réduit. Pour mettre la photo au briefing, voir le [[bg|Briefing Generator]].'], ['**Open ▾** (Open a work file…, Open an image…) and **Save**, Ctrl+S, store the composition in the work file, without the source image: after a page reload, import the image again. **Export** proposes a name (the target and the time), which you can change, and writes a lossless PNG at the source’s resolution; the on-screen preview is reduced. To put the photo in the briefing, see the [[bg|Briefing Generator]].']),
]

# ── Route Planner ────────────────────────────────────────────────────────────────
PAGES_SRC['rp'] = [
    ('h', "À quoi ça sert", "What it's for"),
    ('p', ['Le Route Planner trace la route d’un groupe sur la carte d’un théâtre de DCS et en donne la navigation : caps, distances, temps. On y pose aussi des points de référence et des calques tactiques, et on consulte la fiche d’un terrain.'], ['The Route Planner draws a group’s route on the map of a DCS theatre and gives its navigation: headings, distances, times. You also place reference points and tactical layers, and consult an airfield sheet.']),
    ('raw', PANEL_HTML['rp'], ''),
    ('raw', f'''      <div class="fm-schema">
        {RP_SCREEN_SVG}
        <div class="fm-schema-legend">
          <span class="lang-block" data-lang="fr">Fig. 1 — L’écran du Route Planner : la carte, ses modes de toucher et le panneau.</span>
          <span class="lang-block" data-lang="en">Fig. 1 — The Route Planner screen: the map, its tap modes, and the panel.</span>
        </div>
      </div>''', ''),
    ('h', "Les gestes", "The gestures"),
    ('h', "Le théâtre et le fond", "The theatre and the base map"),
    ('p', ['Le sélecteur **Théâtre** choisit la carte de DCS ; la **Carte DCS** est grisée là où DCS n’en a pas, et la carte de navigation de Flappie n’existe que sur le Caucase. **Affichage ▾** règle le fond, les unités et ce que montre la carte ; un point ambre sur le bouton signale un réglage changé. La loupe, en haut à gauche de la carte, cherche un lieu ou un objet nommé.'], ['The **Theatre** selector chooses the DCS map; the **DCS map** is greyed out where DCS has none, and Flappie’s navigation map exists only on the Caucasus. **Display ▾** sets the base map, the units and what the map shows; an amber dot on the button marks a changed setting. The magnifier, at the top left of the map, searches for a place or a named object.']),
    ('h', "Ce que fait un toucher", "What a touch does"),
    ('p', ['En haut à droite de la carte, cinq modes disent ce que fait un toucher :'], ['At the top right of the map, five modes say what a tap does:']),
    ('ul', ['**Point** ajoute un point au bout de la route ;', '**Réf.** pose un point de référence ;', '**Lire** ne pose rien : un aérodrome ouvre sa fiche, un objet d’un calque montre la sienne ;', '**Dessin** ouvre les outils de dessin de vos calques ;', '**Règle** mesure cap et distance sur la carte sans rien poser ; quitter le mode efface la mesure.'], ['**Waypoint** adds a point at the end of the route;', '**Ref.** places a reference point;', '**Read** places nothing: an airfield opens its sheet, a layer object shows its own;', '**Draw** opens the drawing tools for your layers;', '**Ruler** measures heading and distance on the map without placing anything; leaving the mode clears the measurement.']),
    ('p',
     ["En Point et en Réf., un aérodrome touché donne un point à son nom."],
     ["In Point and Ref., a touched airfield gives a point with its name."]),
    ('h', "Construire la route", "Building the route"),
    ('p', ['En tête de la section Route, une ligne choisit la route ; + en ajoute une, … ouvre Dupliquer et Supprimer. Touchez la carte pour ajouter un point, glissez-le pour le déplacer ; le + posé sur une branche assez longue y insère un point. Le bloc Ajouter place un point par ses coordonnées ou par cap et distance.', '**Groupes…** choisit les groupes qui suivent cette route, ou en crée un ; un groupe ne suit qu’une route, et le Flight Configurator voit le même choix. Une route garde son théâtre : en changer masque les routes des autres théâtres, qui reviennent quand on y retourne.'], ['At the top of the Route section, a row chooses the route; + adds one, … opens Duplicate and Delete. Tap the map to add a point, drag it to move it; the + on a long enough leg inserts a point there. The Add block places a point by its coordinates or by heading and distance.', '**Groups…** chooses the groups that follow this route, or creates one; a group follows only one route, and the Flight Configurator sees the same choice. A route keeps its theatre: changing theatre hides the routes of the other theatres, which come back when you return.']),
    ('h', "Les points de référence", "Reference points"),
    ('p', ['Les **points de référence** marquent ce qui compte hors de la route : une cible, un repère, un terrain. Posez-les en mode Réf. ou par + Réf. ; ils ne comptent ni dans les branches ni dans le total, passent à la datacard, mais pas au Route Tool de DCS.'], ['**Reference points** mark what matters off the route: a target, a landmark, an airfield. Place them in Ref. mode or with + Ref.; they count neither in the legs nor in the total, and go to the datacard but not to the DCS Route Tool.']),
    ('h', "La navigation", "Navigation"),
    ('p', ['Les **boîtes de branche** écrivent la navigation sur la carte, une par branche ; les traits des minutes la coupent toutes les minutes. La section Navigation donne cap, temps et distance de chaque branche, et le total ; son titre dit le cap employé. Cap : Vrai ou Magnétique. En magnétique, la déclinaison est **Calculée**, d’après la date de la mission d’HQ quand elle existe, ou **Saisie** ; **Forcer** impose l’année saisie. Sans valeur saisie, le cap reste vrai et l’avertissement le dit.'], ['The **leg boxes** write the navigation on the map, one per leg; the **minute ticks** cut it every minute. The Navigation section gives each leg’s heading, time and distance, and the total; its title says which heading is used. Heading: True or Magnetic. In magnetic, the variation is **Computed**, from the HQ mission date when there is one, or **Entered**; **Override** imposes the entered year. With no value entered, the heading stays true and the warning says so.']),
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
     ["Le travail est gardé dans le navigateur. **Sauvegarder**, ou Ctrl+S, écrit le fichier de travail de la suite. **Ouvrir ▾ › Ouvrir une route ou des calques…** reconnaît ce qu’on lui donne : une route JSON, un fichier du Route Tool de DCS ou un fichier CombatFlite. **Importer des routes…** ouvre la [[start:gestes|fenêtre d’import commune]]."],
     ["The work is kept in the browser. **Save**, or Ctrl+S, writes the suite’s work file. **Open ▾ › Open a route or layers…** recognises what it is given: a JSON route, a DCS Route Tool file or a CombatFlite file. **Import routes…** opens the [[start:gestes|common import window]]."]),
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
    ('h', "Le paquet de cartes", "The deck of cards"),
    ('p', ['En tête du panneau, une ligne choisit la carte, avec sa pastille LIÉE à un groupe, LIBRE ou GROUPE SUPPRIMÉ. + ajoute une datacard liée à un groupe ; … ouvre les autres actions sur les cartes. La dernière carte ne se supprime pas : elle se vide.'], ['At the top of the panel, a row chooses the card, with its badge LINKED to a group, FREE or GROUP DELETED. + adds a datacard linked to a group; … opens the other actions on the cards. The last card cannot be deleted: it is emptied.']),
    ('h', "Remplir une carte", "Filling in a card"),
    ('p', ['Les sections de l’éditeur suivent la page. La carte d’un groupe reprend de la fiche des groupes ce que le Flight Configurator règle — unités, radios, emport, carburant et poids — et les champs partagés portent la pastille « FC » ; les canaux à imprimer se cochent ici comme au FC. Une carte libre n’est liée à rien : tout y est texte libre, sauf le type des unités. Le nom d’un terrain se choisit dans la liste des aérodromes du théâtre, qui remplit le reste ; DEP et ARR viennent de la route.'], ['The editor sections follow the page. A group’s card takes from the group sheet what the Flight Configurator sets — units, radios, loadout, fuel and weight — and the shared fields carry the “FC” badge; the channels to print are ticked here as in the FC. A free card is linked to nothing: everything in it is free text, except the units’ type. An airfield’s name is chosen from the theatre’s airfield list, which fills in the rest; DEP and ARR come from the route.']),
    ('h', "La navigation", "Navigation"),
    ('p', ['La navigation d’une datacard **est une route du Route Planner** : un point saisi, déplacé ou supprimé ici l’est aussi là-bas, et inversement ; l’heure et la note restent à la datacard. Un point sans coordonnées se place par cap et distance depuis son voisin. Les points de référence sont ceux du Route Planner ; chaque datacard choisit ceux qu’elle affiche. **Lier à une autre route** lie la carte affichée à une route du Route Planner ; … › **Une datacard par route** en crée une par route d’un coup. Les réglages de cap sont communs au Route Planner et au Datacard Generator.'], ['A datacard’s navigation **is a Route Planner route**: a point entered, moved or deleted here is so there too, and the other way round; the time and the note stay on the datacard. A point with no coordinates is placed by heading and distance from its neighbour. The reference points are the Route Planner’s; each datacard chooses which ones it shows. **Link to another route** links the displayed card to a Route Planner route; … › **One datacard per route** creates one per route at once. The heading settings are shared by the Route Planner and the Datacard Generator.']),
    ('h', "Importer", "Importing"),
    ('p', ['Les **groupes** (mission d’HQ, paquet de vol, briefing en cours) s’importent par … › **Importer des groupes**, la [[start:gestes|fenêtre d’import commune]] : une carte par groupe, avec, pour la mission d’HQ, la date, l’heure et la météo. **Ouvrir ▾ › Importer…** lit un **briefing**, en cours ou en fichier, et ajoute une datacard par vol coché, avec tout ce que le briefing en dit ; une ligne Données générales couvre un briefing sans groupe. Elle lit aussi une route ou un jeu de routes depuis un fichier : **Lier la carte à cette route** ou **Nouvelle datacard**. Restent à la main les horaires, et le carburant et l’emport quand le FC ne les donne pas. Une datacard importée vit ensuite seule : modifier le briefing ne la change pas.'], ['The **groups** (HQ mission, flight package, current briefing) are imported through … › **Import groups**, the [[start:gestes|common import window]]: one card per group, with, for the HQ mission, the date, time and weather. **Open ▾ › Import…** reads a **briefing**, current or from a file, and adds a datacard per ticked flight, with everything the briefing says about it; a General data line covers a briefing with no group. It also reads a route or a set of routes from a file: **Link the card to this route** or **New datacard**. Still to do by hand: the timings, and the fuel and loadout when the FC does not provide them. An imported datacard then lives on its own: changing the briefing does not change it.']),
    ('h', "Jour ou nuit, unités", "Day or night, units"),
    ('p', ['**Affichage ▾ › Jour | Nuit** donne à tout le paquet sa version de jour ou de nuit ; seule cette bascule compte, les thèmes de l’outil ne changent pas la datacard. Les unités, partagées avec le Route Planner et le Flight Configurator, changent les intitulés de la fiche ; les valeurs saisies ne sont pas converties, sauf celles de la ligne carburant. Le METAR, saisi ou importé, se décode en vent, visibilité, QNH et nuages, modifiables ensuite.'], ['**Display ▾ › Day | Night** gives the whole deck its day or night version; only this switch counts, the tool’s themes do not change the datacard. The units, shared with the Route Planner and the Flight Configurator, change the sheet’s labels; entered values are not converted, except those of the fuel line. The METAR, entered or imported, decodes into wind, visibility, QNH and clouds, editable afterwards.']),
    ('h', "Quand la page déborde", "When the page overflows"),
    ('p',
     ["La fiche garde toutes ses boîtes, même vides, pour être imprimée et complétée à la main. Quand tout ne tient pas, la navigation passe sur une page 2, avec un en-tête réduit. Si la page 1 déborde encore, l’éditeur affiche « Contenu tronqué » : allégez le contenu."],
     ["The sheet keeps all its boxes, even empty ones, to be printed and completed by hand. When everything does not fit, the navigation moves to a page 2, with a reduced header. If page 1 still overflows, the editor shows “Content truncated”: lighten the content."]),
    ('h', "Sauvegarder et exporter", "Saving and exporting"),
    ('p', ['Le paquet est gardé dans le navigateur. **Ouvrir ▾ › Ouvrir une datacard…** lit encore un ancien fichier de datacards, qui remplace le paquet en cours, après confirmation si celui-ci n’est pas vierge. **Exporter** propose le PDF ou le PNG : le PDF passe par l’impression du navigateur, une feuille par page ; le PNG est une image par page au format d’une page de kneeboard, et plusieurs pages partent dans un ZIP. L’export suit la version jour ou nuit affichée.'], ['The deck is kept in the browser. **Open ▾ › Open a datacard…** still reads an old datacards file, which replaces the current deck, after a confirmation if it is not blank. **Export** offers PDF or PNG: the PDF goes through the browser’s print, one sheet per page; the PNG is one image per page in the format of a kneeboard page, and several pages leave in a ZIP. The export follows the day or night version shown.']),
]

# ── Flight Configurator ──────────────────────────────────────────────────────────
PAGES_SRC['fc'] = [
    ('h', "À quoi ça sert", "What it's for"),
    ('p', ['Le Flight Configurator est l’outil du Flight Leader : il prépare un ou plusieurs groupes — identité, radios, emport composé sur la vue de face de l’appareil, livrée — et les exporte en paquet de vol que le Mission Commander applique à sa mission avec HQ. HQ retrouve chaque groupe par son nom et sa coalition ; chaque partie est facultative, et une partie laissée vide n’est pas touchée.'], ['The Flight Configurator is the Flight Leader’s tool: it prepares one or more groups — identity, radios, loadout composed on the aircraft’s front view, livery — and exports them as a flight package that the Mission Commander applies to their mission with HQ. HQ finds each group by its name and coalition; each part is optional, and a part left empty is not touched.']),
    ('raw', PANEL_HTML['fc'], ''),
    ('h', "Les gestes", "The gestures"),
    ('h', "Les groupes et les unités", "Groups and units"),
    ('p', ['**Ajoutez un groupe** : nom, coalition, et pour chaque unité son type, son nom, son indicatif, son numéro de bord et sa livrée. Deux groupes d’une même coalition ne portent pas le même nom : l’export est refusé. Changer le type d’une unité efface ses radios et son emport, avec confirmation. Vos groupes sont partagés avec le Route Planner et le Datacard Generator : un groupe créé ou renommé dans l’un apparaît dans les autres.'], ['**Add a group**: name, coalition, and for each unit its type, its name, its call sign, its tail number and its livery. Two groups of the same coalition do not share a name: the export is refused. Changing a unit’s type clears its radios and loadout, with confirmation. Your groups are shared with the Route Planner and the Datacard Generator: a group created or renamed in one appears in the others.']),
    ('h', "La route", "The route"),
    ('p', ['Le bloc **ROUTE** parle du groupe de l’unité choisie. Un groupe n’a qu’une route : on la choisit parmi celles du Route Planner en touchant une vignette, celles que le Route Planner lie à ce groupe d’abord ; **Changer de route** rouvre le choix, **Retirer** la vide. Le groupe garde une copie des points : c’est elle que le paquet porte. La reprise est automatique : quand le Route Planner enregistre, chaque groupe lié reprend les points de sa route et son nom ; si la route est supprimée au Route Planner, elle est retirée des groupes qui la suivaient.'], ['The **ROUTE** block is about the chosen unit’s group. A group has one route only: you choose it among the Route Planner’s by tapping a thumbnail, the ones the Route Planner links to this group first; **Change route** reopens the choice, **Remove** empties it. The group keeps a copy of the points: that is what the package carries. The pick-up is automatic: when the Route Planner saves, each linked group takes up its route’s points and its name; if the route is deleted in the Route Planner, it is removed from the groups that followed it. ']),
    ('h', "Les radios", "The radios"),
    ('p', ['Pour chaque poste de l’appareil, un champ par canal, numéroté comme au cockpit. Une fréquence se saisit en MHz et doit tomber dans la bande du poste, que le module écrit sous son titre : une valeur hors bande est refusée avec un message qui cite la bande ; une valeur hors bande déjà présente, importée par exemple, est gardée et signalée sans bloquer l’export. **Recopier sur les autres unités du groupe** écrit les mêmes canaux sur les unités du même type. Les hélicoptères ont aussi un poste HF : la mission ne le règle pas et HQ ne l’écrit jamais, mais la datacard le reprend. La case devant un canal l’imprime sur la datacard du groupe : le Datacard Generator montre le même choix, mais le paquet de vol ne le porte pas.'], ['For each radio of the aircraft, one field per channel, numbered as in the cockpit. A frequency is typed in MHz and must fall inside the radio’s band, which the module writes under its title: an out-of-band value is refused with a message that quotes the band; an out-of-band value already present, imported for instance, is kept and flagged without blocking the export. **Copy to the other units of the group** writes the same channels on the units of the same type. The helicopters also have an **HF** radio: the mission does not set it and HQ never writes it, but the datacard picks it up. The box in front of a channel prints it on the group’s datacard: the Datacard Generator shows the same choice, but the flight package does not carry it.']),
    ('h', "L’emport", "The loadout"),
    ('p', ['L’**unité choisie**, que l’on touche sur sa carte, a son emport affiché à droite : la vue de face de l’appareil, avec une case par station et la liste des armes permises. La masse totale et la masse estimée au décollage s’affichent, en orange au-delà du maximum recommandé. **Symétrique** pose sur la station jumelle l’arme miroir. Une arme qui ne peut pas aller avec le reste est grisée, avec les stations qui la gênent ; le Kord du Mi-24P n’a qu’une porte. Dessous, carburant, leurres, paillettes et canon : une valeur tapée hors limite est refusée.', '**Mes presets** : « Garder dans mes presets… » enregistre l’emport sous un nom ; « Charger des presets (.lua) » reprend les fichiers de presets de l’escadre ; « Partir de » propose ces presets et une copie de l’emport d’une autre unité du même type. Les presets vivent dans le navigateur seulement : ni le fichier de travail, ni Ouvrir, Exemple ou Effacer n’y touchent, et le paquet ne porte jamais un preset, mais un emport.'], ['The **chosen unit**, which you tap on its card, has its loadout shown on the right: the aircraft’s front view, with one box per station and the list of permitted weapons. The total mass and the estimated take-off mass are shown, in orange beyond the recommended maximum. **Symmetric** places the mirror weapon on the twin station. A weapon that cannot go with the rest is greyed out, with the stations that obstruct it; the Mi-24P’s Kord has only one door. Below, fuel, flares, chaff and gun: a typed value out of range is refused.', '**My presets**: “Keep in my presets…” saves the loadout under a name; “Load presets (.lua)” takes up the wing’s preset files; “Start from” offers those presets and a copy of another unit’s loadout of the same type. Presets live in the browser only: neither the work file, nor Open, Example or Clear touch them, and the package never carries a preset, but a loadout.']),
    ('h', "La livrée", "The livery"),
    ('p',
     ["Le champ est une liste, celle du type de l’unité : les livrées du jeu et les livrées custom déclarées dans la fenêtre Wing d’HQ. Il affiche toujours un nom, et c’est ce nom que le paquet emporte. Tant que vous n’en choisissez pas, c’est la livrée de l’unité dans la mission ouverte dans HQ, sinon la livrée par défaut du type déclarée dans Wing, sinon la première de la liste. À l’application du paquet, HQ laisse décocher la livrée."],
     ["The field is a list, the unit type’s: the game’s liveries and the custom liveries declared in HQ’s Wing window. It always shows a name, and that name is what the package carries. Until you choose one, it is the unit’s livery in the mission open in HQ, otherwise the type’s default livery declared in Wing, otherwise the first in the list. When the package is applied, HQ lets you untick the livery."]),
    ('h', "Importer, sauvegarder, exporter", "Importing, saving, exporting"),
    ('p',
     ["**Importer des groupes…** ouvre la [[start:gestes|fenêtre d’import commune]] ; une unité sans type se règle une fois son type choisi. **Ouvrir ▾ › Ouvrir une configuration…** lit encore l’ancien fichier du module, avec vos groupes et « Mes presets ». **Exporter** écrit le paquet de vol : HQ applique ses parties cochées au groupe de même nom. **Retirer ce groupe** le retire de tous les outils. Si les groupes sont sur un autre théâtre, un bandeau propose d’y revenir ou de retirer leurs routes."],
     ["**Import groups…** opens the [[start:gestes|common import window]]; a unit with no type is set up once its type is chosen. **Open ▾ › Open a configuration…** still reads the module’s old file, with your groups and “My presets”. **Export** writes the flight package: HQ applies its ticked parts to the group with the same name. **Remove this group** removes it from all tools. If the groups are on another theatre, a banner offers to go back there or to remove their routes."]),
    ('note',
     "Crédits — Les tables d’armes viennent de **pydcs** (LGPL-3.0-or-later), reprises de Mission Tools ; les dessins de la vue de face sont de **Goldwolf** (DCS Reference Guide), utilisés avec son accord et **hors de la licence AGPL** du dépôt (voir `data/views/LICENSE.md`). Limite : le module écrit l’emport qu’on compose ; il ne dit pas que DCS l’acceptera.",
     "Credits — The weapon tables come from **pydcs** (LGPL-3.0-or-later), taken from Mission Tools; the front-view drawings are by **Goldwolf** (DCS Reference Guide), used with his permission and **outside the repository’s AGPL licence** (see `data/views/LICENSE.md`). Limit: the module writes the loadout you compose; it does not say that DCS will accept it."),
]

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


/* ---------- Barre du haut commune aux sept modules ----------
   La marque du Field Manual : le titre et son sous-titre à l'accent du module, le sigle (F·M) quand le titre ne tient plus. Aucun seuil de largeur propre au Field Manual : la barre se réduit comme celle des autres outils,
   par la séquence commune du bloc d'interface (ui_block.py : build_bar_css, build_bar_js), « s'il tient » : le tampon de décor et celui que pose le shell, la version, puis (rien à retirer ici : ni liste, ni Affichage, ni bouton à texte) le titre. */
.tb-brand-main, .tb-brand-short {{ color: #7E8FA6; }}
.tb-brand-short {{ display: none; font-family: var(--f-stencil); font-size: 16px; font-weight: 700; letter-spacing: 3px; white-space: nowrap; }}
.tb-classif {{ font-family: var(--f-stencil); font-weight: 400; font-size: 11px; letter-spacing: 3px; color: var(--red-faded); border: 1px solid var(--red-faded); padding: 4px 10px; white-space: nowrap; flex-shrink: 0; }}
#btn-lang svg {{ display: block; }}
.tb-brand-sub {{ font-weight: 500; }}
{BAR_CSS}
/* ── ROOT SCROLL ── */
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

/* Bouton retour index */
.fm-back-btn {{
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-family: var(--f-ui);
  font-size: 11px;
  letter-spacing: 2px;
  text-transform: uppercase;
  color: var(--fm-accent);
  background: transparent;
  border: 1px solid var(--fm-accent);
  padding: 6px 14px;
  cursor: pointer;
  margin-bottom: 28px;
  transition: all .12s;
}}
.fm-back-btn:hover {{ background: rgba(126,143,166,.12); }}

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

.fm-callout a {{
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

<!-- ======== MAIN ROOT ======== -->
<main id="fm-root">

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
    'btn.back':         '◄ Index',
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
    'btn.back':         '◄ Index',
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
var PAGES = ['index', 'start', 'hq', 'bg', 'rs', 'rp', 'dg', 'fc'];

function showPage(id, anchor) {{
  if (PAGES.indexOf(id) === -1) id = 'index';
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
    if (tgt && tgt.scrollIntoView) tgt.scrollIntoView();
  }}
  // Persister la dernière page
  try {{ localStorage.setItem(KEY_STATE, JSON.stringify({{page: id}})); }} catch(e) {{}}
}}

function navigate(id) {{
  location.hash = '#' + id;
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

  window.addEventListener('hashchange', onHashChange);
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
grep_ok('id="rps"',         'schéma écran du RP : marqueur propre')
grep_ok('id="dga"',         'schéma anatomie de la datacard : marqueur propre')
grep_absent('id="dgf"',     'figure 2 DG (flux) retirée')
grep_absent('Du groupe au paquet', 'schéma de flux du FC retiré')
grep_absent('LE HUB DE LA SUITE',  'schéma de flux d\'HQ retiré')
grep_ok('id="gestes"',      'Par où commencer : la table des gestes a son ancre')
grep_ok('class="fm-gt"',    'Par où commencer : la table des gestes')
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
