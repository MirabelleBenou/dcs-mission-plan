#!/usr/bin/env python3
"""Build the DCS Field Manual HTML module — monofichier, offline, Mission Plan suite."""

import json
import os
import base64
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))

APP_VERSION = '1.0.0'
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
STARDOS_700_B64   = b64_font('STARDOS_700')
OSWALD_500_B64    = b64_font('OSWALD_500')

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
    return '\n'.join(parts)

FONT_CDN = '' if (SPECIAL_ELITE_B64 and STARDOS_700_B64) else \
    '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Special+Elite&family=Stardos+Stencil:wght@700&family=Oswald:wght@500&display=swap">'

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

# ── HTML principal ───────────────────────────────────────────────────────────────

HTML = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0, viewport-fit=cover">
<title>FIELD MANUAL — DCS Mission Plan</title>
{FONT_CDN}
<style>
/* =============================================
   DCS FIELD MANUAL v{APP_VERSION}
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
  --kraft-bg: url('data:image/svg+xml;base64,{KRAFT_NATO}');
}}
body[data-theme="cw-soviet"] {{
  --paper: #d8c479; --paper-light: #e8d690; --paper-dark: #b8a64a;
  --ink: #1f1c16; --ink-faded: #463f30;
  --olive: #2a3a5a; --olive-dark: #1a2540; --olive-deep: #0e1830;
  --khaki: #3a4a2e; --khaki-light: #5a6a48;
  --red-stamp: #841e1e; --red-faded: #a04040;
  --kraft-bg: url('data:image/svg+xml;base64,{KRAFT_SOV}');
}}
body[data-theme="modern-nato"] {{
  --paper: #e8e3d8; --paper-light: #f0ece2; --paper-dark: #c8c0b0;
  --ink: #15181c; --ink-faded: #3a4048;
  --olive: #2a3038; --olive-dark: #1c2026; --olive-deep: #0e1014;
  --khaki: #5c6b7a; --khaki-light: #7a8a98;
  --red-stamp: #1a1a1a; --red-faded: #4a4a4a;
  --kraft-bg: url('data:image/svg+xml;base64,{KRAFT_MNATO}');
}}
body[data-theme="modern-east"] {{
  --paper: #cdc6b8; --paper-light: #ddd6c8; --paper-dark: #ada69a;
  --ink: #1a1610; --ink-faded: #3d3024;
  --olive: #3d3024; --olive-dark: #2a2018; --olive-deep: #1a140e;
  --khaki: #4a5238; --khaki-light: #6a7256;
  --red-stamp: #7a2424; --red-faded: #a04040;
  --kraft-bg: url('data:image/svg+xml;base64,{KRAFT_MEAST}');
}}

/* ── Reset & base ── */
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
html, body {{ height: 100%; overscroll-behavior: none; }}
button, input, select, textarea {{ font: inherit; cursor: pointer; }}

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
  height: 56px;
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

.fm-brand {{
  display: flex;
  align-items: baseline;
  gap: 10px;
  flex-shrink: 0;
}}
.fm-brand-logo {{
  font-family: var(--f-stencil);
  font-size: 18px;
  font-weight: 700;
  letter-spacing: 2px;
  color: var(--fm-accent);
  text-transform: uppercase;
  white-space: nowrap;
  border: 1px solid var(--fm-accent);
  padding: 2px 8px;
  line-height: 1;
}}
.fm-brand-name {{
  font-family: var(--f-ui);
  font-size: 11px;
  letter-spacing: 3px;
  color: var(--khaki-light);
  text-transform: uppercase;
  white-space: nowrap;
}}

.tb-sep {{ width: 1px; height: 28px; background: var(--khaki); opacity: .4; flex-shrink: 0; }}
.tb-spacer {{ flex: 1; }}
.tb-version {{
  font-family: var(--f-ui);
  font-size: 10px;
  letter-spacing: 1.5px;
  color: var(--fm-accent);
  opacity: .7;
  text-transform: uppercase;
  white-space: nowrap;
}}

#btn-lang {{
  background: transparent;
  border: 1px solid var(--khaki);
  color: var(--paper);
  height: 36px;
  min-width: 40px;
  padding: 0 8px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  transition: all .15s;
  flex-shrink: 0;
}}
#btn-lang:hover, #btn-lang:focus-visible {{
  background: var(--olive);
  border-color: var(--fm-accent);
  outline: none;
}}

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
}}
@media (min-width: 900px) {{
  .fm-plaque-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
  }}
  .fm-plaque-grid .fm-plaque:first-child {{
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
  outline: 2px solid var(--chapter-accent, var(--fm-accent));
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
  font-family: var(--f-ui);
  font-size: 11px;
  letter-spacing: 1px;
  color: var(--khaki);
  text-transform: uppercase;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}}
.fm-plaque-badge {{
  font-family: var(--f-stencil);
  font-size: 9px;
  letter-spacing: 2px;
  padding: 3px 8px;
  text-transform: uppercase;
  flex-shrink: 0;
}}
.fm-plaque.active .fm-plaque-badge {{
  color: var(--chapter-accent, var(--fm-accent));
  border: 1px solid var(--chapter-accent, var(--fm-accent));
}}
.fm-plaque.soon .fm-plaque-badge {{
  color: var(--khaki);
  border: 1px solid var(--khaki);
  position: absolute;
  top: 12px; right: 14px;
}}
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
.fm-back-btn:focus-visible {{ outline: 2px solid var(--fm-accent); outline-offset: 2px; }}

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
  color: var(--chapter-accent, var(--fm-accent));
  text-transform: uppercase;
  margin-bottom: 12px;
  padding-left: 12px;
  border-left: 3px solid var(--chapter-accent, var(--fm-accent));
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
  background: rgba(0,0,0,.2);
  padding: 20px;
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
  opacity: .65;
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
  color: var(--chapter-accent, var(--fm-accent));
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

/* Plaques accents individuels */
.fm-plaque[data-module="rs"]  {{ --chapter-accent: #C95A9C; --chapter-accent-rgb: 201,90,156; }}
.fm-plaque[data-module="hq"]  {{ --chapter-accent: #4FB286; --chapter-accent-rgb: 79,178,134; }}
.fm-plaque[data-module="bg"]  {{ --chapter-accent: #c0892a; --chapter-accent-rgb: 192,137,42; }}
.fm-plaque[data-module="rp"]  {{ --chapter-accent: #7ac97a; --chapter-accent-rgb: 122,201,122; }}
.fm-plaque[data-module="dg"]  {{ --chapter-accent: #8fb0c0; --chapter-accent-rgb: 143,176,192; }}

</style>
</head>
<body data-theme="cw-nato">

<!-- ======== TOOLBAR ======== -->
<header class="toolbar">
  <div class="fm-brand">
    <span class="fm-brand-logo" aria-label="Field Manual">F·M</span>
    <span class="fm-brand-name" data-i18n="brand.name">Field Manual</span>
  </div>
  <div class="tb-sep" aria-hidden="true"></div>
  <div class="tb-spacer"></div>
  <span class="tb-version">v{APP_VERSION}</span>
  <button id="btn-lang" aria-label="Changer de langue" title="Switch language">
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
          <p>La suite DCS Mission Plan regroupe des outils de préparation de mission entièrement hors-ligne, distribués sous forme de fichiers HTML autonomes. Aucune installation requise, aucune dépendance réseau : chaque outil s'ouvre directement dans votre navigateur.</p>
          <p>Ce manuel documente l'utilisation de chaque module : fonctionnalités, interface, flux de travail, et limites à connaître. Il est conçu pour être parcouru chapitre par chapitre, ou consulté ponctuellement.</p>
        </div>
        <div class="lang-block" data-lang="en">
          <p>The DCS Mission Plan suite brings together fully offline mission preparation tools, distributed as self-contained HTML files. No installation required, no network dependency: each tool opens directly in your browser.</p>
          <p>This manual documents how to use each module: features, interface, workflow, and caveats worth knowing. It is designed to be read chapter by chapter, or consulted as needed.</p>
        </div>
      </div>

      <!-- Index -->
      <p class="fm-section-title" data-i18n="index.title">Modules documentés</p>

      <div class="fm-plaque-grid">

        <!-- HQ -->
        <div class="fm-plaque active" data-module="hq" tabindex="0" role="button"
             aria-label="HQ — Wing Command Center"
             onclick="navigate('hq')"
             onkeydown="if(event.key==='Enter'||event.key===' '){{event.preventDefault();navigate('hq')}}">
          <div class="fm-plaque-monogram">HQ</div>
          <div class="fm-plaque-info">
            <div class="fm-plaque-name">HQ</div>
            <div class="fm-plaque-desc" data-i18n="index.hq.desc">Wing Command Center — configuration escadre</div>
          </div>
          <div class="fm-plaque-badge" data-i18n="index.badge.active">Manuel</div>
        </div>

        <!-- BG -->
        <div class="fm-plaque active" data-module="bg" tabindex="0" role="button"
             aria-label="BG — Briefing Generator"
             onclick="navigate('bg')"
             onkeydown="if(event.key==='Enter'||event.key===' '){{event.preventDefault();navigate('bg')}}">
          <div class="fm-plaque-monogram">BG</div>
          <div class="fm-plaque-info">
            <div class="fm-plaque-name">Briefing Generator</div>
            <div class="fm-plaque-desc" data-i18n="index.bg.desc">Générateur de briefings multi-sections</div>
          </div>
          <div class="fm-plaque-badge" data-i18n="index.badge.active">Manuel</div>
        </div>

        <!-- RS -->
        <div class="fm-plaque active" data-module="rs" tabindex="0" role="button"
             aria-label="RS — Recon Station"
             onclick="navigate('rs')"
             onkeydown="if(event.key==='Enter'||event.key===' '){{event.preventDefault();navigate('rs')}}">
          <div class="fm-plaque-monogram">RS</div>
          <div class="fm-plaque-info">
            <div class="fm-plaque-name">Recon Station</div>
            <div class="fm-plaque-desc" data-i18n="index.rs.desc">Compositeur photo-renseignement canvas</div>
          </div>
          <div class="fm-plaque-badge" data-i18n="index.badge.active">Manuel</div>
        </div>

        <!-- RP — À venir -->
        <div class="fm-plaque soon" data-module="rp" aria-hidden="true">
          <div class="fm-plaque-monogram" style="opacity:.4;">RP</div>
          <div class="fm-plaque-info">
            <div class="fm-plaque-name">Route Planner</div>
            <div class="fm-plaque-desc" data-i18n="index.rp.desc">Planification d'itinéraires</div>
          </div>
          <div class="fm-soon-stamp" data-i18n-soon><!-- rempli par JS --></div>
        </div>

        <!-- DG — À venir -->
        <div class="fm-plaque soon" data-module="dg" aria-hidden="true">
          <div class="fm-plaque-monogram" style="opacity:.4;">DG</div>
          <div class="fm-plaque-info">
            <div class="fm-plaque-name">Datacard</div>
            <div class="fm-plaque-desc" data-i18n="index.dg.desc">Génération de datacards</div>
          </div>
          <div class="fm-soon-stamp" data-i18n-soon><!-- rempli par JS --></div>
        </div>

      </div><!-- /fm-plaque-grid -->
    </div>
  </section><!-- /page-index -->


  <!-- ===== PAGE RS — Chapitre-gabarit : Recon Station ===== -->
  <section id="page-rs" class="fm-page hidden">
    <div class="fm-chapter">

      <!-- Retour -->
      <button class="fm-back-btn" onclick="navigate('index')" data-i18n="btn.back">◄ Index</button>

      <!-- Héros -->
      <div class="fm-hero">
        <img class="fm-hero-img" src="{RS_TILE_SRC}" alt="Recon Station" draggable="false">
        <div class="fm-hero-pin" aria-hidden="true"></div>
        <div class="fm-hero-caption">
          <div>
            <div class="fm-hero-monogram">RS</div>
          </div>
          <div>
            <div class="fm-hero-title" data-i18n="rs.hero.title">Recon Station</div>
            <div class="fm-hero-sub" data-i18n="rs.hero.sub">Compositeur photo-renseignement</div>
          </div>
        </div>
      </div>

      <!-- À quoi ça sert -->
      <div class="fm-prose">
        <h3 data-i18n="rs.whatfor.title">À quoi ça sert</h3>
        <div class="lang-block" data-lang="fr">
          <p>Recon Station transforme une capture d'écran DCS — ou n'importe quelle image — en photo d'analyse de reconnaissance, prête à glisser dans un briefing. Le principe : partir d'une vraie image, lui donner l'allure d'un capteur (optique, infrarouge ou radar), puis poser par-dessus une couche d'annotations — cibles, légendes, loupes, bandeau de classification, logos. L'export est un PNG sans perte, à la résolution exacte de la source. Les sections ci-dessous détaillent chaque réglage et son effet.</p>
        </div>
        <div class="lang-block" data-lang="en">
          <p>Recon Station turns a DCS screenshot — or any image — into a reconnaissance analysis photo, ready to drop into a briefing. The idea: start from a real image, give it the look of a sensor (optical, infrared, or radar), then overlay a layer of annotations — targets, legends, loupes, classification banner, logos. Export is a lossless PNG at the source's exact resolution. The sections below detail each control and its effect.</p>
        </div>
      </div>

      <!-- Schéma SVG — anatomie d'une photo recon (où se place chaque élément) -->
      <div class="fm-schema">
        <svg viewBox="0 0 720 380" xmlns="http://www.w3.org/2000/svg" role="img"
             aria-label="Anatomie d'une photo recon">
          <defs>
            <marker id="lead" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto">
              <path d="M0,0 L7,3.5 L0,7 Z" fill="currentColor" opacity=".55"/>
            </marker>
            <pattern id="hatch" width="6" height="6" patternTransform="rotate(45)" patternUnits="userSpaceOnUse">
              <line x1="0" y1="0" x2="0" y2="6" stroke="#C95A9C" stroke-width="2" opacity=".7"/>
            </pattern>
          </defs>

          <text x="360" y="26" text-anchor="middle" font-size="13" letter-spacing="3" fill="currentColor" opacity=".75" class="lang-block" data-lang="fr">ANATOMIE D'UNE PHOTO RECON</text>
          <text x="360" y="26" text-anchor="middle" font-size="13" letter-spacing="3" fill="currentColor" opacity=".75" class="lang-block" data-lang="en">ANATOMY OF A RECON PHOTO</text>
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
            <text x="512" y="112" class="lang-block" data-lang="fr">Cartouche : N° + légende</text>
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
      </div>

      <!-- Référence par fonction -->
      <div class="fm-prose">
        <h3 class="lang-block" data-lang="fr">Préparer la photo</h3>
        <h3 class="lang-block" data-lang="en">Setting up the photo</h3>
        <div class="lang-block" data-lang="fr"><p>L'image est d'abord convertie en niveaux de gris. Le curseur <strong>Contraste</strong> accentue ou adoucit les écarts de luminosité. Le sélecteur <strong>Type d'imagerie</strong> applique ensuite l'allure d'un capteur : <strong>EO visible</strong> garde un rendu photographique net ; <strong>IR blanc chaud</strong> fait ressortir les sources chaudes en clair sur fond sombre ; <strong>IR noir chaud</strong> inverse (chaud = sombre) ; <strong>SAR</strong> donne le grain granuleux et le moucheté d'une image radar. Ce sont des stylisations du signal, pas des mesures réelles. Enfin <strong>Vignette</strong>, <strong>Grain</strong> et <strong>Scanlines</strong> (éteints par défaut) ajoutent l'usure d'un tirage : bords assombris, bruit argentique, lignes de balayage. Chaque effet est un curseur d'intensité appliqué en temps réel.</p></div>
        <div class="lang-block" data-lang="en"><p>The image is first converted to greyscale. The <strong>Contrast</strong> slider sharpens or softens brightness differences. The <strong>Imaging type</strong> selector then applies a sensor look: <strong>EO visible</strong> keeps a crisp photographic render; <strong>IR white-hot</strong> brings hot sources up bright on a dark background; <strong>IR black-hot</strong> inverts it (hot = dark); <strong>SAR</strong> gives the grainy speckle of a radar image. These are signal stylisations, not real measurements. Finally <strong>Vignette</strong>, <strong>Grain</strong>, and <strong>Scanlines</strong> (off by default) add print wear: darkened edges, film noise, scan lines. Each effect is an intensity slider applied in real time.</p></div>
      </div>

      <div class="fm-prose">
        <h3 class="lang-block" data-lang="fr">Le bloc d'informations</h3>
        <h3 class="lang-block" data-lang="en">The information block</h3>
        <div class="lang-block" data-lang="fr"><p>En bas, centré, un bloc renseigne le contexte de la prise : <strong>Cible, Coordonnées, Cap, Altitude, Mission, Capteur, Date-heure (DTG), Équipage, Classification</strong>. Tous les champs sont libres ; laissez vides ceux qui ne s'appliquent pas. Réglez la couleur du texte en <strong>blanc ou noir</strong> selon que le bas de la photo est sombre ou clair.</p></div>
        <div class="lang-block" data-lang="en"><p>At the bottom, centred, a block carries the shot's context: <strong>Target, Coordinates, Course, Altitude, Mission, Sensor, Date-time (DTG), Crew, Classification</strong>. All fields are free text; leave blank those that don't apply. Set the text colour <strong>white or black</strong> depending on whether the bottom of the photo is dark or light.</p></div>
      </div>

      <div class="fm-prose">
        <h3 class="lang-block" data-lang="fr">Cibles : cartouche et marqueurs</h3>
        <h3 class="lang-block" data-lang="en">Targets: cartouche and markers</h3>
        <div class="lang-block" data-lang="fr"><p><strong>« + Ajouter un marquage »</strong> dépose un cercle numéroté que vous faites glisser (souris ou tactile) sur la cible ; le numéro s'inscrit à côté du cercle pour ne pas la masquer. Chaque marqueur est lié à une <strong>ligne de légende</strong> dans le cartouche en haut à droite, et la numérotation se recalcule seule quand vous réordonnez ou supprimez. Couleur <strong>rouge, noir ou blanc</strong>. Activez l'<strong>Amorce</strong> pour tirer un trait du cercle au point exact de la cible (point déplaçable). Pour une ligne de légende sans cercle sur la photo, décochez <strong>« Point visible »</strong>.</p></div>
        <div class="lang-block" data-lang="en"><p><strong>"+ Add a marking"</strong> drops a numbered circle you drag (mouse or touch) onto the target; the number sits beside the circle so it never hides it. Each marker is tied to a <strong>legend line</strong> in the top-right cartouche, and numbering recomputes itself when you reorder or delete. Colour <strong>red, black, or white</strong>. Turn on the <strong>Leader line</strong> to draw from the circle to the exact target point (draggable). For a legend line with no circle on the photo, untick <strong>"Visible point"</strong>.</p></div>
      </div>

      <div class="fm-prose">
        <h3 class="lang-block" data-lang="fr">Loupe</h3>
        <h3 class="lang-block" data-lang="en">Loupe</h3>
        <div class="lang-block" data-lang="fr"><p><strong>« + Ajouter une loupe »</strong> ré-affiche, agrandie, une portion de l'image traitée : une petite zone source sur la photo, reliée en pointillés à une boîte zoomée. Zone et boîte se <strong>déplacent et se redimensionnent</strong> (poignée en bas à droite) ; le ratio reste couplé, donc l'image agrandie <strong>n'est jamais déformée</strong>. Bordure blanche, noire ou rouge, et libellé optionnel.</p></div>
        <div class="lang-block" data-lang="en"><p><strong>"+ Add a loupe"</strong> re-shows a magnified portion of the processed image: a small source area on the photo, linked by a dashed line to a zoomed box. Area and box <strong>move and resize</strong> (bottom-right handle); the ratio stays coupled, so the magnified image is <strong>never distorted</strong>. White, black, or red border, and an optional label.</p></div>
      </div>

      <div class="fm-prose">
        <h3 class="lang-block" data-lang="fr">Formes et étiquettes</h3>
        <h3 class="lang-block" data-lang="en">Shapes and labels</h3>
        <div class="lang-block" data-lang="fr"><p>Cinq <strong>formes</strong> se posent au centre puis se déplacent : ellipse, rectangle (<strong>pivotable</strong>, poignée dédiée), polygone (points éditables, fermeture), flèche (tête pleine) et crochet. Trois styles d'<strong>étiquette</strong> : <strong>tampon</strong> (boîte pleine, texte inversé), <strong>cursif</strong> (police façon crayon gras) et <strong>nu</strong> (texte simple avec halo de lisibilité). Couleur rouge, noir ou blanc pour chaque élément.</p></div>
        <div class="lang-block" data-lang="en"><p>Five <strong>shapes</strong> drop at centre then move: ellipse, rectangle (<strong>rotatable</strong>, dedicated handle), polygon (editable points, closing), arrow (solid head), and bracket. Three <strong>label</strong> styles: <strong>stamp</strong> (filled box, inverted text), <strong>cursive</strong> (grease-pencil font), and <strong>plain</strong> (simple text with a legibility halo). Red, black, or white colour per element.</p></div>
      </div>

      <div class="fm-prose">
        <h3 class="lang-block" data-lang="fr">Bandeau de classification</h3>
        <h3 class="lang-block" data-lang="en">Classification banner</h3>
        <div class="lang-block" data-lang="fr"><p>Deux barres pleine largeur, en <strong>haut et en bas</strong>, éteintes par défaut : <strong>UNCLASSIFIED</strong> (vert), <strong>CONFIDENTIAL</strong> (bleu), <strong>SECRET</strong> (rouge), <strong>TOP SECRET</strong> (orange). Les libellés ne sont <strong>pas traduits</strong> (marquage standard). Ce bandeau est distinct du champ <em>Classification</em> du bloc d'informations ; quand il est actif, la place est réservée pour ne recouvrir ni le cartouche ni le bloc info.</p></div>
        <div class="lang-block" data-lang="en"><p>Two full-width bars, <strong>top and bottom</strong>, off by default: <strong>UNCLASSIFIED</strong> (green), <strong>CONFIDENTIAL</strong> (blue), <strong>SECRET</strong> (red), <strong>TOP SECRET</strong> (orange). The labels are <strong>not translated</strong> (standard marking). This banner is distinct from the <em>Classification</em> field in the information block; when on, space is reserved so it covers neither the cartouche nor the info block.</p></div>
      </div>

      <div class="fm-prose">
        <h3 class="lang-block" data-lang="fr">Logos</h3>
        <h3 class="lang-block" data-lang="en">Logos</h3>
        <div class="lang-block" data-lang="fr"><p>Aucun logo par défaut. Ajoutez-en par <strong>upload d'image</strong>, ou <strong>importez une configuration d'escadre</strong> (fichier .json) exportée depuis HQ ou le Briefing Generator : Recon récupère alors le logo d'escadre et ceux des escadrons. Chaque logo est réduit proportionnellement et se rend en <strong>couleur, niveaux de gris (défaut) ou blanc</strong> (silhouette).</p></div>
        <div class="lang-block" data-lang="en"><p>No logo by default. Add one by <strong>image upload</strong>, or <strong>import a wing configuration</strong> (.json file) exported from HQ or the Briefing Generator: Recon then pulls in the wing logo and the squadron logos. Each logo is scaled down proportionally and renders in <strong>colour, greyscale (default), or white</strong> (silhouette).</p></div>
      </div>

      <div class="fm-prose">
        <h3 class="lang-block" data-lang="fr">Exporter</h3>
        <h3 class="lang-block" data-lang="en">Export</h3>
        <div class="lang-block" data-lang="fr"><p>L'export produit un <strong>PNG sans perte à la résolution native</strong> de la source, nommé automatiquement d'après la cible et l'horodatage. L'aperçu à l'écran est en résolution réduite : seul le fichier exporté reflète la qualité finale.</p></div>
        <div class="lang-block" data-lang="en"><p>Export produces a <strong>lossless PNG at the source's native resolution</strong>, auto-named from the target and timestamp. The on-screen preview is lower resolution: only the exported file reflects final quality.</p></div>
      </div>

            <!-- Callout NOTE -->
      <div class="fm-callout note">
        <div class="lang-block" data-lang="fr">Export PNG lossless — L'export produit un fichier PNG aux dimensions exactes de l'image source, sans aucune recompression. La résolution d'aperçu est inférieure ; seul l'export reflète la qualité finale.</div>
        <div class="lang-block" data-lang="en">Lossless PNG export — The export produces a PNG file at the exact dimensions of the source image, with no recompression. Preview resolution is lower; only the export reflects final quality.</div>
      </div>

      <!-- Callout WARN -->
      <div class="fm-callout warn">
        <div class="lang-block" data-lang="fr">L'image source n'est jamais persistée — Recon Station sauvegarde automatiquement vos paramètres et annotations entre sessions, mais pas l'image elle-même (trop volumineuse pour le stockage local). Après un rechargement de page, vous devrez recharger votre image source.</div>
        <div class="lang-block" data-lang="en">The source image is never persisted — Recon Station automatically saves your settings and annotations between sessions, but not the image itself (too large for local storage). After a page reload, you will need to reload your source image.</div>
      </div>

      <!-- Callout NOTE — principe effet/annotation -->
      <div class="fm-callout note">
        <div class="lang-block" data-lang="fr">Effet ou annotation — Recon ne peint jamais d'éléments absents de l'image. Les effets transforment les pixels déjà présents ; les annotations se posent par-dessus sans toucher la photo. Même la loupe ne fait que ré-afficher un agrandissement de l'image traitée — elle n'invente rien.</div>
        <div class="lang-block" data-lang="en">Effect or annotation — Recon never paints in elements that aren't in the image. Effects transform the pixels already there; annotations sit on top without touching the photo. Even the loupe only re-shows a magnified crop of the processed image — it invents nothing.</div>
      </div>

    </div><!-- /fm-chapter -->
  </section><!-- /page-rs -->


  <!-- ===== PAGE HQ ===== -->
  <section id="page-hq" class="fm-page hidden">
    <div class="fm-chapter" style="--chapter-accent:#4FB286; --chapter-accent-rgb:79,178,134;">

      <button class="fm-back-btn" onclick="navigate('index')" data-i18n="btn.back">◄ Index</button>

      <div class="fm-hero">
        <img class="fm-hero-img" src="{HQ_TILE_SRC}" alt="HQ" draggable="false">
        <div class="fm-hero-pin" aria-hidden="true"></div>
        <div class="fm-hero-caption">
          <div><div class="fm-hero-monogram">HQ</div></div>
          <div>
            <div class="fm-hero-title" data-i18n="hq.hero.title">HQ — Wing Command Center</div>
            <div class="fm-hero-sub" data-i18n="hq.hero.sub">Configuration escadre centralisée</div>
          </div>
        </div>
      </div>

      <!-- À quoi ça sert -->
      <div class="fm-prose">
        <h3 class="lang-block" data-lang="fr">À quoi ça sert</h3>
        <h3 class="lang-block" data-lang="en">What it's for</h3>
        <div class="lang-block" data-lang="fr"><p>HQ est le <strong>poste de commandement</strong> de la suite : un module de support pour les <strong>Mission Commanders</strong> et les <strong>Flight Leaders</strong>. Il fait deux choses. D'abord, c'est le <strong>seul endroit où définir l'identité de l'escadre</strong> et de ses escadrons ; cette identité est ensuite partagée automatiquement avec les autres modules — le Briefing Generator s'en sert pour son branding et ses escadrons, Recon Station pour ses logos. Ensuite, HQ sait <strong>charger une mission DCS (.miz)</strong> pour en lire les vols clients, leurs fréquences, leurs livrées et la météo. Réinjecter des modifications dans un .miz (rôle Commander) s'activera avec l'arrivée des modules Flight Lead.</p></div>
        <div class="lang-block" data-lang="en"><p>HQ is the suite's <strong>command post</strong>: a support module for <strong>Mission Commanders</strong> and <strong>Flight Leaders</strong>. It does two things. First, it is the <strong>single place to define the wing's identity</strong> and its squadrons; that identity is then shared automatically with the other modules — the Briefing Generator uses it for branding and squadrons, Recon Station for its logos. Second, HQ can <strong>load a DCS mission (.miz)</strong> to read its client flights, their frequencies, liveries, and weather. Writing changes back into a .miz (Commander role) will activate when the Flight Lead modules arrive.</p></div>
      </div>

      <!-- Schéma SVG — flux du hub -->
      <div class="fm-schema">
        <svg viewBox="0 0 720 380" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="HQ — le hub de la suite">
          <defs>
            <marker id="ha" markerWidth="8" markerHeight="8" refX="6.5" refY="3.5" orient="auto"><path d="M0,0 L8,3.5 L0,7 Z" fill="currentColor" opacity=".6"/></marker>
            <marker id="haf" markerWidth="8" markerHeight="8" refX="6.5" refY="3.5" orient="auto"><path d="M0,0 L8,3.5 L0,7 Z" fill="currentColor" opacity=".35"/></marker>
          </defs>

          <text x="360" y="26" text-anchor="middle" font-size="13" letter-spacing="3" fill="currentColor" opacity=".75" class="lang-block" data-lang="fr">HQ — LE HUB DE LA SUITE</text>
          <text x="360" y="26" text-anchor="middle" font-size="13" letter-spacing="3" fill="currentColor" opacity=".75" class="lang-block" data-lang="en">HQ — THE SUITE'S HUB</text>
          <line x1="120" y1="34" x2="600" y2="34" stroke="currentColor" stroke-width=".6" opacity=".3"/>

          <rect x="48" y="92" width="86" height="42" fill="none" stroke="currentColor" stroke-width="1.2"/>
          <text x="91" y="112" text-anchor="middle" font-size="12" fill="currentColor">.miz</text>
          <text x="91" y="126" text-anchor="middle" font-size="8" fill="currentColor" opacity=".7">mission</text>
          <line x1="134" y1="113" x2="286" y2="113" stroke="currentColor" stroke-width="1.2" opacity=".6" marker-end="url(#ha)"/>
          <text x="210" y="105" text-anchor="middle" font-size="9" fill="currentColor" opacity=".7" class="lang-block" data-lang="fr">charger</text>
          <text x="210" y="105" text-anchor="middle" font-size="9" fill="currentColor" opacity=".7" class="lang-block" data-lang="en">load</text>

          <rect x="288" y="84" width="150" height="64" rx="3" fill="none" stroke="#4FB286" stroke-width="2"/>
          <text x="363" y="116" text-anchor="middle" font-size="22" fill="#4FB286" letter-spacing="2">HQ</text>
          <text x="363" y="134" text-anchor="middle" font-size="8.5" fill="currentColor" opacity=".7" class="lang-block" data-lang="fr">poste de commandement</text>
          <text x="363" y="134" text-anchor="middle" font-size="8.5" fill="currentColor" opacity=".7" class="lang-block" data-lang="en">command post</text>

          <line x1="438" y1="113" x2="512" y2="113" stroke="currentColor" stroke-width="1.2" opacity=".35" stroke-dasharray="4 3" marker-end="url(#haf)"/>
          <rect x="514" y="86" width="172" height="58" rx="3" fill="none" stroke="currentColor" stroke-width="1" stroke-dasharray="4 3" opacity=".5"/>
          <text x="600" y="108" text-anchor="middle" font-size="9.5" fill="currentColor" opacity=".6" class="lang-block" data-lang="fr">Snapshot de mission</text>
          <text x="600" y="108" text-anchor="middle" font-size="9.5" fill="currentColor" opacity=".6" class="lang-block" data-lang="en">Mission snapshot</text>
          <text x="600" y="124" text-anchor="middle" font-size="9.5" fill="currentColor" opacity=".6" class="lang-block" data-lang="fr">→ modules Flight Lead</text>
          <text x="600" y="124" text-anchor="middle" font-size="9.5" fill="currentColor" opacity=".6" class="lang-block" data-lang="en">→ Flight Lead modules</text>
          <text x="600" y="137" text-anchor="middle" font-size="8.5" fill="currentColor" opacity=".5" class="lang-block" data-lang="fr">(à venir)</text>
          <text x="600" y="137" text-anchor="middle" font-size="8.5" fill="currentColor" opacity=".5" class="lang-block" data-lang="en">(coming)</text>

          <line x1="363" y1="148" x2="363" y2="196" stroke="currentColor" stroke-width="1.2" opacity=".6" marker-end="url(#ha)"/>
          <rect x="250" y="198" width="226" height="32" rx="3" fill="none" stroke="currentColor" stroke-width="1.4"/>
          <text x="363" y="214" text-anchor="middle" font-size="11" fill="currentColor">wing_config</text>
          <text x="363" y="226" text-anchor="middle" font-size="8" fill="currentColor" opacity=".7" class="lang-block" data-lang="fr">identité d'escadre partagée</text>
          <text x="363" y="226" text-anchor="middle" font-size="8" fill="currentColor" opacity=".7" class="lang-block" data-lang="en">shared wing identity</text>

          <line x1="320" y1="230" x2="270" y2="276" stroke="currentColor" stroke-width="1.2" opacity=".6" marker-end="url(#ha)"/>
          <line x1="406" y1="230" x2="456" y2="276" stroke="currentColor" stroke-width="1.2" opacity=".6" marker-end="url(#ha)"/>
          <rect x="170" y="278" width="140" height="46" rx="3" fill="none" stroke="#c0892a" stroke-width="1.6"/>
          <text x="240" y="300" text-anchor="middle" font-size="12" fill="#c0892a">Briefing Generator</text>
          <text x="240" y="315" text-anchor="middle" font-size="8" fill="currentColor" opacity=".6" class="lang-block" data-lang="fr">branding + escadrons</text>
          <text x="240" y="315" text-anchor="middle" font-size="8" fill="currentColor" opacity=".6" class="lang-block" data-lang="en">branding + squadrons</text>
          <rect x="416" y="278" width="140" height="46" rx="3" fill="none" stroke="#C95A9C" stroke-width="1.6"/>
          <text x="486" y="300" text-anchor="middle" font-size="12" fill="#C95A9C">Recon Station</text>
          <text x="486" y="315" text-anchor="middle" font-size="8" fill="currentColor" opacity=".6">logos</text>

          <text x="360" y="352" text-anchor="middle" font-size="9" fill="currentColor" opacity=".55" class="lang-block" data-lang="fr">HQ édite — les autres consomment</text>
          <text x="360" y="352" text-anchor="middle" font-size="9" fill="currentColor" opacity=".55" class="lang-block" data-lang="en">HQ edits — the others consume</text>
        </svg>
        <div class="fm-schema-legend">
          <span class="lang-block" data-lang="fr">Fig. 1 — HQ édite l'identité d'escadre ; les autres modules la consomment.</span>
          <span class="lang-block" data-lang="en">Fig. 1 — HQ edits the wing identity; the other modules consume it.</span>
        </div>
      </div>

      <!-- Créateur de Wing : identité -->
      <div class="fm-prose">
        <h3 class="lang-block" data-lang="fr">Le créateur de Wing — l'identité de l'escadre</h3>
        <h3 class="lang-block" data-lang="en">The Wing builder — the wing's identity</h3>
        <div class="lang-block" data-lang="fr"><p>C'est ici que vous décrivez votre escadre, une fois pour toutes : <strong>Nom court</strong> et <strong>Nom complet</strong> ; <strong>Titre d'application</strong> (le titre affiché en tête des briefings) ; <strong>Logo d'escadre</strong> (une image, réduite automatiquement) ; <strong>Tampon HQ</strong> (la mention tamponnée, type « HQ ░ MON ESCADRE »). Chaque champ se répercute sur le branding des autres modules.</p></div>
        <div class="lang-block" data-lang="en"><p>This is where you describe your wing, once and for all: <strong>Short name</strong> and <strong>Full name</strong>; <strong>App title</strong> (the title shown at the top of briefings); <strong>Wing logo</strong> (an image, scaled down automatically); <strong>HQ stamp</strong> (the stamped line, e.g. "HQ ░ MY WING"). Each field flows through to the other modules' branding.</p></div>
      </div>

      <!-- Créateur de Wing : escadrons -->
      <div class="fm-prose">
        <h3 class="lang-block" data-lang="fr">Les escadrons</h3>
        <h3 class="lang-block" data-lang="en">The squadrons</h3>
        <div class="lang-block" data-lang="fr"><p>Ajoutez autant d'escadrons que nécessaire. Pour chacun : <strong>nom</strong>, <strong>surnom</strong> (optionnel), <strong>callsign</strong> (l'identité radio, ex. FRANKEN), <strong>appareils</strong> (ex. Mi-24P, Mi-8) et <strong>logo</strong>. Le callsign sert de base aux indicatifs automatiques des pilotes dans le Briefing Generator (ex. « ANTON 1-1 »), toujours modifiables ensuite.</p></div>
        <div class="lang-block" data-lang="en"><p>Add as many squadrons as needed. For each: <strong>name</strong>, <strong>nickname</strong> (optional), <strong>callsign</strong> (the radio identity, e.g. FRANKEN), <strong>aircraft</strong> (e.g. Mi-24P, Mi-8), and <strong>logo</strong>. The callsign seeds the pilots' automatic call signs in the Briefing Generator (e.g. "ANTON 1-1"), always editable afterwards.</p></div>
      </div>

      <!-- Créateur de Wing : partager -->
      <div class="fm-prose">
        <h3 class="lang-block" data-lang="fr">Partager la configuration</h3>
        <h3 class="lang-block" data-lang="en">Sharing the configuration</h3>
        <div class="lang-block" data-lang="fr"><p>Tout est <strong>sauvegardé automatiquement</strong> à chaque modification, et propagé en direct aux autres modules. <strong>Exportez</strong> la configuration en fichier <code>.json</code> pour la distribuer à l'escadre ; chacun l'<strong>importe</strong> pour retrouver exactement le même branding. Un bouton <strong>réinitialise</strong> au wing par défaut.</p></div>
        <div class="lang-block" data-lang="en"><p>Everything is <strong>saved automatically</strong> on every change, and propagated live to the other modules. <strong>Export</strong> the configuration as a <code>.json</code> file to hand it to the wing; everyone <strong>imports</strong> it to get exactly the same branding. A button <strong>resets</strong> to the default wing.</p></div>
      </div>

      <!-- Charger une mission -->
      <div class="fm-prose">
        <h3 class="lang-block" data-lang="fr">Charger une mission</h3>
        <h3 class="lang-block" data-lang="en">Loading a mission</h3>
        <div class="lang-block" data-lang="fr"><p>HQ ouvre un <strong>.miz</strong> et en extrait un <strong>instantané en lecture seule</strong> : les vols clients (hélicoptères et avions pilotables), présentés par leur <strong>callsign</strong>, avec leurs fréquences radio, la fréquence de groupe, la livrée et la météo de la mission. L'instantané est partagé avec les autres modules et exportable. À cette étape, HQ <strong>lit</strong> — il ne modifie rien.</p></div>
        <div class="lang-block" data-lang="en"><p>HQ opens a <strong>.miz</strong> and extracts a <strong>read-only snapshot</strong>: the client flights (player-flyable helicopters and planes), shown by their <strong>callsign</strong>, with their radio frequencies, group frequency, livery, and the mission weather. The snapshot is shared with the other modules and exportable. At this stage HQ <strong>reads</strong> — it changes nothing.</p></div>
      </div>

      <!-- Commander à venir -->
      <div class="fm-callout note">
        <div class="lang-block" data-lang="fr">Le rôle Commander arrive — HQ embarque déjà de quoi réinjecter des modifications ciblées (fréquences, livrées, routes…) dans un .miz et produire une mission corrigée. Cette fonction s'activera quand les modules Flight Lead permettront de préparer ces modifications. D'ici là, HQ se concentre sur l'identité d'escadre et la lecture de mission.</div>
        <div class="lang-block" data-lang="en">The Commander role is coming — HQ already carries what it needs to write targeted changes (frequencies, liveries, routes…) back into a .miz and produce a corrected mission. This will activate once the Flight Lead modules let you prepare those changes. Until then, HQ focuses on wing identity and mission reading.</div>
      </div>

    </div><!-- /fm-chapter -->
  </section><!-- /page-hq -->


  <!-- ===== PAGE BG ===== -->
  <section id="page-bg" class="fm-page hidden">
    <div class="fm-chapter" style="--chapter-accent:#c0892a; --chapter-accent-rgb:192,137,42;">

      <button class="fm-back-btn" onclick="navigate('index')" data-i18n="btn.back">◄ Index</button>

      <div class="fm-hero">
        <img class="fm-hero-img" src="{BG_TILE_SRC}" alt="Briefing Generator" draggable="false">
        <div class="fm-hero-pin" aria-hidden="true"></div>
        <div class="fm-hero-caption">
          <div><div class="fm-hero-monogram">BG</div></div>
          <div>
            <div class="fm-hero-title" data-i18n="bg.hero.title">Briefing Generator</div>
            <div class="fm-hero-sub" data-i18n="bg.hero.sub">Générateur de briefings multi-sections</div>
          </div>
        </div>
      </div>

      <!-- À quoi ça sert -->
      <div class="fm-prose">
        <h3 class="lang-block" data-lang="fr">À quoi ça sert</h3>
        <h3 class="lang-block" data-lang="en">What it’s for</h3>
        <div class="lang-block" data-lang="fr"><p>Le Briefing Generator assemble un <strong>briefing de mission complet, multi-pages</strong>, prêt à imprimer ou à emporter en vol : couverture, situation tactique, aperçu de mission, plan radio, missions individuelles, équipage, cartes et annexes. On remplit des sections dans l’éditeur, on prévisualise la mise en page A4, puis on exporte en <strong>PDF</strong> ou en <strong>PNG par page</strong> (genouillères). L’identité d’escadre (logo, noms, escadrons) est <strong>héritée de HQ</strong>. Quatre thèmes, tout hors-ligne.</p></div>
        <div class="lang-block" data-lang="en"><p>The Briefing Generator assembles a <strong>complete, multi-page mission briefing</strong>, ready to print or take into the cockpit: cover, tactical situation, mission overview, radio plan, individual missions, crew, charts, and annexes. You fill sections in the editor, preview the A4 layout, then export to <strong>PDF</strong> or <strong>per-page PNG</strong> (kneeboards). The wing identity (logo, names, squadrons) is <strong>inherited from HQ</strong>. Four themes, fully offline.</p></div>
      </div>

      <!-- Schéma SVG -->
      <div class="fm-schema">
        <svg viewBox="0 0 720 380" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Ce qui alimente quoi">
          <defs>
            <marker id="bm" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto"><path d="M0,0 L7,3.5 L0,7 Z" fill="currentColor" opacity=".6"/></marker>
          </defs>
          <text x="360" y="24" text-anchor="middle" font-size="13" letter-spacing="3" fill="currentColor" opacity=".75" class="lang-block" data-lang="fr">CE QUI ALIMENTE QUOI</text>
          <text x="360" y="24" text-anchor="middle" font-size="13" letter-spacing="3" fill="currentColor" opacity=".75" class="lang-block" data-lang="en">WHAT FEEDS WHAT</text>
          <line x1="120" y1="32" x2="600" y2="32" stroke="currentColor" stroke-width=".6" opacity=".3"/>

          <rect x="16" y="66" width="96" height="42" rx="3" fill="none" stroke="#4FB286" stroke-width="1.8"/>
          <text x="64" y="84" text-anchor="middle" font-size="12" fill="#4FB286">HQ</text>
          <text x="64" y="98" text-anchor="middle" font-size="7.5" fill="currentColor" opacity=".7">wing_config</text>

          <rect x="156" y="66" width="96" height="42" rx="3" fill="none" stroke="currentColor" stroke-width="1.4"/>
          <text x="204" y="91" text-anchor="middle" font-size="11" fill="currentColor" class="lang-block" data-lang="fr">Escadrons</text>
          <text x="204" y="91" text-anchor="middle" font-size="11" fill="currentColor" class="lang-block" data-lang="en">Squadrons</text>

          <rect x="296" y="66" width="96" height="42" rx="3" fill="none" stroke="#c0892a" stroke-width="1.8"/>
          <text x="344" y="91" text-anchor="middle" font-size="11" fill="#c0892a">Missions</text>

          <rect x="436" y="66" width="96" height="42" rx="3" fill="none" stroke="currentColor" stroke-width="1.4"/>
          <text x="484" y="84" text-anchor="middle" font-size="10" fill="currentColor" class="lang-block" data-lang="fr">Appareil</text>
          <text x="484" y="84" text-anchor="middle" font-size="10" fill="currentColor" class="lang-block" data-lang="en">Aircraft</text>
          <text x="484" y="98" text-anchor="middle" font-size="7.5" fill="currentColor" opacity=".7" class="lang-block" data-lang="fr">sélectionné</text>
          <text x="484" y="98" text-anchor="middle" font-size="7.5" fill="currentColor" opacity=".7" class="lang-block" data-lang="en">selected</text>

          <rect x="576" y="66" width="100" height="42" rx="3" fill="none" stroke="currentColor" stroke-width="1.4"/>
          <text x="626" y="91" text-anchor="middle" font-size="10.5" fill="currentColor" class="lang-block" data-lang="fr">Plan radio</text>
          <text x="626" y="91" text-anchor="middle" font-size="10.5" fill="currentColor" class="lang-block" data-lang="en">Radio plan</text>

          <line x1="112" y1="87" x2="154" y2="87" stroke="currentColor" stroke-width="1.2" opacity=".6" marker-end="url(#bm)"/>
          <text x="133" y="80" text-anchor="middle" font-size="7.5" fill="currentColor" opacity=".7" class="lang-block" data-lang="fr">identité</text>
          <text x="133" y="80" text-anchor="middle" font-size="7.5" fill="currentColor" opacity=".7" class="lang-block" data-lang="en">identity</text>
          <line x1="252" y1="87" x2="294" y2="87" stroke="currentColor" stroke-width="1.2" opacity=".6" marker-end="url(#bm)"/>
          <text x="273" y="80" text-anchor="middle" font-size="7.5" fill="currentColor" opacity=".7" class="lang-block" data-lang="fr">escadron</text>
          <text x="273" y="80" text-anchor="middle" font-size="7.5" fill="currentColor" opacity=".7" class="lang-block" data-lang="en">squadron</text>
          <line x1="392" y1="87" x2="434" y2="87" stroke="currentColor" stroke-width="1.2" opacity=".6" marker-end="url(#bm)"/>
          <text x="413" y="80" text-anchor="middle" font-size="7.5" fill="currentColor" opacity=".7" class="lang-block" data-lang="fr">type choisi</text>
          <text x="413" y="80" text-anchor="middle" font-size="7.5" fill="currentColor" opacity=".7" class="lang-block" data-lang="en">type chosen</text>
          <line x1="532" y1="87" x2="574" y2="87" stroke="currentColor" stroke-width="1.2" opacity=".6" marker-end="url(#bm)"/>
          <text x="553" y="80" text-anchor="middle" font-size="7" fill="currentColor" opacity=".7" class="lang-block" data-lang="fr">réf radio</text>
          <text x="553" y="80" text-anchor="middle" font-size="7" fill="currentColor" opacity=".7" class="lang-block" data-lang="en">radio ref</text>

          <rect x="250" y="190" width="140" height="42" rx="3" fill="none" stroke="currentColor" stroke-width="1.4"/>
          <text x="320" y="215" text-anchor="middle" font-size="11" fill="currentColor" class="lang-block" data-lang="fr">Équipage</text>
          <text x="320" y="215" text-anchor="middle" font-size="11" fill="currentColor" class="lang-block" data-lang="en">Crew</text>
          <path d="M204,108 C204,160 270,165 280,189" fill="none" stroke="currentColor" stroke-width="1.2" opacity=".55" marker-end="url(#bm)"/>
          <text x="214" y="150" font-size="7.5" fill="currentColor" opacity=".7" class="lang-block" data-lang="fr">callsign → indicatifs</text>
          <text x="214" y="150" font-size="7.5" fill="currentColor" opacity=".7" class="lang-block" data-lang="en">callsign → call signs</text>
          <path d="M344,108 C344,150 350,160 350,189" fill="none" stroke="currentColor" stroke-width="1.2" opacity=".55" marker-end="url(#bm)"/>
          <text x="356" y="150" font-size="7.5" fill="currentColor" opacity=".7" class="lang-block" data-lang="fr">groupes liés</text>
          <text x="356" y="150" font-size="7.5" fill="currentColor" opacity=".7" class="lang-block" data-lang="en">linked groups</text>

          <rect x="40" y="296" width="150" height="42" rx="3" fill="none" stroke="currentColor" stroke-width="1.4"/>
          <text x="115" y="315" text-anchor="middle" font-size="10.5" fill="currentColor" class="lang-block" data-lang="fr">Aérodromes / FARP</text>
          <text x="115" y="315" text-anchor="middle" font-size="10.5" fill="currentColor" class="lang-block" data-lang="en">Airfields / FARPs</text>
          <text x="115" y="329" text-anchor="middle" font-size="7.5" fill="currentColor" opacity=".7">ICAO</text>
          <rect x="250" y="296" width="120" height="42" rx="3" fill="none" stroke="currentColor" stroke-width="1.4"/>
          <text x="310" y="321" text-anchor="middle" font-size="11" fill="currentColor">METAR</text>
          <line x1="190" y1="317" x2="248" y2="317" stroke="currentColor" stroke-width="1.2" opacity=".6" marker-end="url(#bm)"/>
          <text x="219" y="310" text-anchor="middle" font-size="7" fill="currentColor" opacity=".7" class="lang-block" data-lang="fr">pré-rempli</text>
          <text x="219" y="310" text-anchor="middle" font-size="7" fill="currentColor" opacity=".7" class="lang-block" data-lang="en">pre-filled</text>

          <rect x="470" y="296" width="160" height="42" rx="3" fill="none" stroke="currentColor" stroke-width="1.4" stroke-dasharray="4 3" opacity=".75"/>
          <text x="550" y="315" text-anchor="middle" font-size="10.5" fill="currentColor" class="lang-block" data-lang="fr">Métadonnées</text>
          <text x="550" y="315" text-anchor="middle" font-size="10.5" fill="currentColor" class="lang-block" data-lang="en">Metadata</text>
          <text x="550" y="329" text-anchor="middle" font-size="7.5" fill="currentColor" opacity=".7" class="lang-block" data-lang="fr">en-têtes &amp; pieds de page</text>
          <text x="550" y="329" text-anchor="middle" font-size="7.5" fill="currentColor" opacity=".7" class="lang-block" data-lang="en">page headers &amp; footers</text>
        </svg>
        <div class="fm-schema-legend">
          <span class="lang-block" data-lang="fr">Fig. 1 — Comment les saisies d’une section alimentent les autres.</span>
          <span class="lang-block" data-lang="en">Fig. 1 — How entries in one section feed the others.</span>
        </div>
      </div>

      <!-- Métadonnées & couverture -->
      <div class="fm-prose">
        <h3 class="lang-block" data-lang="fr">Le squelette : métadonnées &amp; couverture</h3>
        <h3 class="lang-block" data-lang="en">The skeleton: metadata &amp; cover</h3>
        <div class="lang-block" data-lang="fr"><p>Les <strong>Métadonnées</strong> (opération, mission, date, classification, référence du document) alimentent l’en-tête et le pied de toutes les pages. La <strong>Couverture</strong> porte le titre, un narratif d’introduction et une carte du théâtre.</p></div>
        <div class="lang-block" data-lang="en"><p><strong>Metadata</strong> (operation, mission, date, classification, document reference) feed the header and footer of every page. The <strong>Cover</strong> carries the title, an intro narrative, and a theatre map.</p></div>
      </div>

      <!-- SITAC -->
      <div class="fm-prose">
        <h3 class="lang-block" data-lang="fr">Situation tactique (SITAC)</h3>
        <h3 class="lang-block" data-lang="en">Tactical situation (SITAC)</h3>
        <div class="lang-block" data-lang="fr"><p>Décrivez la situation par points, ajoutez une carte tactique, et renseignez le <strong>METAR</strong>. L’<strong>Assistant METAR</strong> vous évite la saisie à la main : soit un formulaire guidé (vent, visibilité, nuages, QNH, température…), soit l’<strong>import d’un .miz</strong> dont il extrait automatiquement la météo de la mission. Le champ METAR reste éditable librement.</p></div>
        <div class="lang-block" data-lang="en"><p>Describe the situation as bullet points, add a tactical map, and fill in the <strong>METAR</strong>. The <strong>METAR Assistant</strong> spares you manual entry: either a guided form (wind, visibility, clouds, QNH, temperature…), or <strong>importing a .miz</strong> from which it extracts the mission weather automatically. The METAR field stays freely editable.</p></div>
      </div>

      <!-- Aperçu mission -->
      <div class="fm-prose">
        <h3 class="lang-block" data-lang="fr">Aperçu de mission</h3>
        <h3 class="lang-block" data-lang="en">Mission overview</h3>
        <div class="lang-block" data-lang="fr"><p>Objectifs, menaces, et une liste structurée d’<strong>aérodromes &amp; FARP</strong> : pour chacun, code <strong>ICAO</strong>, bascule <strong>FARP</strong>, nom, piste en service ou cap, et case <strong>ATC</strong>. Chaque entrée se range proprement dans l’aperçu.</p></div>
        <div class="lang-block" data-lang="en"><p>Objectives, threats, and a structured list of <strong>airfields &amp; FARPs</strong>: for each, <strong>ICAO</strong> code, <strong>FARP</strong> toggle, name, active runway or heading, and an <strong>ATC</strong> box. Each entry lays out cleanly in the preview.</p></div>
      </div>

      <!-- Plan radio -->
      <div class="fm-prose">
        <h3 class="lang-block" data-lang="fr">Plan radio</h3>
        <h3 class="lang-block" data-lang="en">Radio plan</h3>
        <div class="lang-block" data-lang="fr"><p>Un plan <strong>global</strong> (nombre d’entrées illimité ; jusqu’à six retenues à l’aperçu) plus des plans <strong>par appareil</strong>, avec une référence radio propre à chaque type. De quoi cadrer fréquences et canaux pour toute la formation.</p></div>
        <div class="lang-block" data-lang="en"><p>A <strong>global</strong> plan (unlimited entries; up to six shown in the preview) plus <strong>per-aircraft</strong> plans, with a radio reference specific to each type. Everything you need to set frequencies and channels for the whole formation.</p></div>
      </div>

      <!-- Missions individuelles -->
      <div class="fm-prose">
        <h3 class="lang-block" data-lang="fr">Missions individuelles</h3>
        <h3 class="lang-block" data-lang="en">Individual missions</h3>
        <div class="lang-block" data-lang="fr"><p>Autant de missions que nécessaire, parcourues par les flèches (ajouter, dupliquer, réordonner, supprimer). Chacune : titre, escadron, appareil et sous-groupe, objectif, <strong>étapes d’exécution</strong> ordonnables (avec sous-tâches), plan de vol, niveau de menace, notes et images.</p></div>
        <div class="lang-block" data-lang="en"><p>As many missions as needed, browsed with arrows (add, duplicate, reorder, delete). Each one: title, squadron, aircraft and subgroup, objective, orderable <strong>execution steps</strong> (with sub-tasks), flight plan, threat level, notes, and images.</p></div>
      </div>

      <!-- Équipage -->
      <div class="fm-prose">
        <h3 class="lang-block" data-lang="fr">Équipage</h3>
        <h3 class="lang-block" data-lang="en">Crew</h3>
        <div class="lang-block" data-lang="fr"><p>Constituez les groupes de pilotes rattachés aux missions. Les indicatifs sont proposés automatiquement à partir du callsign de l’escadron (ex. « ANTON 1-1 ») et restent modifiables.</p></div>
        <div class="lang-block" data-lang="en"><p>Build the pilot groups attached to the missions. Call signs are suggested automatically from the squadron callsign (e.g. “ANTON 1-1”) and stay editable.</p></div>
      </div>

      <!-- Charts & Annexes -->
      <div class="fm-prose">
        <h3 class="lang-block" data-lang="fr">Charts &amp; annexes</h3>
        <h3 class="lang-block" data-lang="en">Charts &amp; annexes</h3>
        <div class="lang-block" data-lang="fr"><p><strong>Charts</strong> : une liste illimitée de cartes d’aéroport (image + titre). <strong>Annexes</strong> : des pages libres illimitées pour tout ce qui ne rentre pas ailleurs. Les images trop lourdes sont recompressées automatiquement.</p></div>
        <div class="lang-block" data-lang="en"><p><strong>Charts</strong>: an unlimited list of airfield charts (image + title). <strong>Annexes</strong>: unlimited free pages for anything that doesn’t fit elsewhere. Oversized images are recompressed automatically.</p></div>
      </div>

      <!-- Identité d’escadre HQ — CALLOUT -->
      <div class="fm-callout note">
        <div class="lang-block" data-lang="fr">L’escadre se gère dans HQ — la création et la modification de l’escadre (logo, noms, escadrons) se font désormais dans le module HQ. Ici, l’onglet Wing n’affiche plus que le branding hérité, en lecture seule, et se met à jour automatiquement quand HQ change. (En usage autonome, l’import manuel d’une config <code>.json</code> reste un dépannage possible.)</div>
        <div class="lang-block" data-lang="en">The wing lives in HQ — creating and editing the wing (logo, names, squadrons) now happens in the HQ module. Here, the Wing tab only shows the inherited branding, read-only, and updates automatically when HQ changes. (In standalone use, importing a <code>.json</code> config remains a possible fallback.)</div>
      </div>

      <!-- Sauvegarder & reprendre -->
      <div class="fm-prose">
        <h3 class="lang-block" data-lang="fr">Sauvegarder &amp; reprendre</h3>
        <h3 class="lang-block" data-lang="en">Save &amp; resume</h3>
        <div class="lang-block" data-lang="fr"><p>Le briefing est <strong>sauvegardé automatiquement</strong> dans le navigateur. Exportez-le en fichier <code>.json</code> pour l’archiver, le partager ou le reprendre sur une autre machine ; réimportez-le pour continuer ; un bouton permet de repartir de zéro.</p></div>
        <div class="lang-block" data-lang="en"><p>The briefing is <strong>saved automatically</strong> in the browser. Export it as a <code>.json</code> file to archive, share, or resume it on another machine; re-import to continue; a button lets you start over.</p></div>
      </div>

      <!-- Exporter -->
      <div class="fm-prose">
        <h3 class="lang-block" data-lang="fr">Exporter le briefing</h3>
        <h3 class="lang-block" data-lang="en">Exporting the briefing</h3>
        <div class="lang-block" data-lang="fr"><p>Vérifiez la mise en page en mode <strong>Aperçu</strong>, puis exportez. Le <strong>PDF</strong> passe par l’impression du navigateur (<kbd>Ctrl</kbd>+<kbd>P</kbd> → « Enregistrer en PDF »), y compris sur Android. L’<strong>export PNG par page</strong> produit des images individuelles, idéales en genouillères.</p></div>
        <div class="lang-block" data-lang="en"><p>Check the layout in <strong>Preview</strong> mode, then export. The <strong>PDF</strong> goes through the browser’s print (<kbd>Ctrl</kbd>+<kbd>P</kbd> → “Save as PDF”), including on Android. The <strong>per-page PNG export</strong> produces individual images, ideal as kneeboards.</p></div>
      </div>

    </div><!-- /fm-chapter -->
  </section><!-- /page-bg -->

</main><!-- /fm-root -->

<script>
/* =============================================
   DCS FIELD MANUAL — JS
   Routing · i18n · Thème
   ============================================= */

// ── i18n ──────────────────────────────────────
var I18N = {{
  fr: {{
    'brand.name':       'Field Manual',
    'index.title':      'Modules documentés',
    'index.badge.active': 'Manuel',
    'index.hq.desc':    'Wing Command Center — configuration escadre',
    'index.bg.desc':    'Générateur de briefings multi-sections',
    'index.rs.desc':    'Compositeur photo-renseignement canvas',
    'index.rp.desc':    "Planification d\u2019itin\u00e9raires",
    'index.dg.desc':    'Génération de datacards',
    'index.soon':       'À VENIR',
    'btn.back':         '◄ Index',
    'rs.hero.title':    'Recon Station',
    'rs.hero.sub':      'Compositeur photo-renseignement',
    'rs.whatfor.title': 'À quoi ça sert',
    'rs.steps.title':   'Prise en main',
    'rs.schema.legend': 'Fig. 1 — Pipeline de composition et ordre de rendu des calques',
    'hq.hero.title':    'HQ — Wing Command Center',
    'hq.hero.sub':      'Configuration escadre centralisée',
    'bg.hero.title':    'Briefing Generator',
    'bg.hero.sub':      'Générateur de briefings multi-sections',
    'stub.coming':      'Chapitre en préparation'
  }},
  en: {{
    'brand.name':       'Field Manual',
    'index.title':      'Documented Modules',
    'index.badge.active': 'Manual',
    'index.hq.desc':    'Wing Command Center — wing configuration',
    'index.bg.desc':    'Multi-section briefing generator',
    'index.rs.desc':    'Canvas photo-intelligence composer',
    'index.rp.desc':    'Route planning',
    'index.dg.desc':    'Datacard generation',
    'index.soon':       'COMING',
    'btn.back':         '◄ Index',
    'rs.hero.title':    'Recon Station',
    'rs.hero.sub':      'Photo-intelligence composer',
    'rs.whatfor.title': 'What it does',
    'rs.steps.title':   'Getting started',
    'rs.schema.legend': 'Fig. 1 — Composition pipeline and layer render order',
    'hq.hero.title':    'HQ — Wing Command Center',
    'hq.hero.sub':      'Centralised wing configuration',
    'bg.hero.title':    'Briefing Generator',
    'bg.hero.sub':      'Multi-section briefing generator',
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
  // Tampons "À VENIR / COMING" sur les plaques soon
  document.querySelectorAll('.fm-soon-stamp').forEach(function(el) {{
    el.textContent = t('index.soon');
  }});
  // Lang attribute sur body
  document.body.lang = CURRENT_LANG;
  document.documentElement.lang = CURRENT_LANG;
  // Drapeau
  updateFlag();
}}

// ── Drapeaux SVG inline ───────────────────────
var FLAG_FR = '<svg viewBox="0 0 20 14" width="22" height="15" xmlns="http://www.w3.org/2000/svg"><rect width="7" height="14" fill="#002395"/><rect x="7" width="6" height="14" fill="#fff"/><rect x="13" width="7" height="14" fill="#ED2939"/></svg>';
var FLAG_EN = '<svg viewBox="0 0 20 14" width="22" height="15" xmlns="http://www.w3.org/2000/svg"><rect width="20" height="14" fill="#012169"/><path d="M0,0 L20,14 M20,0 L0,14" stroke="#fff" stroke-width="2.8"/><path d="M0,0 L20,14 M20,0 L0,14" stroke="#C8102E" stroke-width="1.6"/><rect x="8" width="4" height="14" fill="#fff"/><rect y="5" width="20" height="4" fill="#fff"/><rect x="9" width="2" height="14" fill="#C8102E"/><rect y="6" width="20" height="2" fill="#C8102E"/></svg>';

function updateFlag() {{
  var btn = document.getElementById('btn-lang');
  if (!btn) return;
  // On montre le drapeau de la langue VERS laquelle on bascule
  btn.innerHTML = CURRENT_LANG === 'fr' ? FLAG_EN : FLAG_FR;
  btn.setAttribute('aria-label', CURRENT_LANG === 'fr' ? 'Switch to English' : 'Passer en français');
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
var PAGES = ['index', 'rs', 'hq', 'bg'];

function showPage(id) {{
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
  // Persister la dernière page
  try {{ localStorage.setItem(KEY_STATE, JSON.stringify({{page: id}})); }} catch(e) {{}}
}}

function navigate(id) {{
  location.hash = '#' + id;
}}

function onHashChange() {{
  var hash = location.hash.replace('#', '') || 'index';
  showPage(hash);
}}

// ── Init ──────────────────────────────────────
function init() {{
  initTheme();
  initLang();
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

os.makedirs(os.path.join(HERE, 'dist'), exist_ok=True)
OUTPUT_PATH = os.path.join(HERE, 'dist', 'dcs_field_manual.html')
with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
    f.write(HTML)

size_kb = os.path.getsize(OUTPUT_PATH) // 1024
print(f'\n[OK] dcs_field_manual.html écrit ({size_kb} Ko)')

# ── Vérifications ────────────────────────────────────────────────────────────────

with open(OUTPUT_PATH, 'r', encoding='utf-8') as f:
    src = f.read()

def grep_ok(pattern, label):
    found = pattern in src
    status = 'OK' if found else 'MISSING'
    print(f'  [{status}] {label}')
    return found

def grep_absent(pattern, label):
    found = pattern in src
    status = 'FAIL' if found else 'OK'
    print(f'  [{status}] ABSENT: {label}')
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
grep_ok('--fm-accent:', '--fm-accent présent')
grep_ok('--chapter-accent: #C95A9C', '--chapter-accent RS')
grep_ok('--chapter-accent: #4FB286', '--chapter-accent HQ')
grep_ok('--chapter-accent: #c0892a', '--chapter-accent BG')
grep_ok('class="toolbar"',  'toolbar présent')
grep_absent('MT_onModuleSave', 'MT_onModuleSave absent')
grep_absent('app-header',      'app-header absent')
grep_absent('4th VEAW',        '4th VEAW absent')
grep_absent('KHR-26',          'KHR-26 absent')
grep_absent('Mi-24P',          'Mi-24P absent')

# Vérifier les paires lang-block
fr_count = src.count('data-lang="fr"')
en_count = src.count('data-lang="en"')
status = 'OK' if fr_count == en_count else 'FAIL'
print(f'  [{status}] paires lang-block : fr={fr_count} en={en_count}')

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

if all_ok:
    print('\n[BUILD DONE]')
else:
    print('\n[BUILD FAIL] Corriger les erreurs JS ci-dessus.', file=sys.stderr)
    sys.exit(1)
