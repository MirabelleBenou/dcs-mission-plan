#!/usr/bin/env python3
"""Build the DCS Recon Station HTML module — monofichier, canvas-native."""

import json
import os
import base64
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS_PATH = os.path.join(HERE, 'assets.json')
if not os.path.isfile(ASSETS_PATH):
    raise SystemExit(f"[ERREUR] Entrée manquante : {ASSETS_PATH} (assets.json attendu à la racine du dépôt)")

APP_VERSION = "1.0.0"

with open(ASSETS_PATH) as f:
    A = json.load(f)

# ---------- KRAFT SVG variants (same as BG) ----------
def _kraft_variant(b64svg, bg_color, grain_color):
    svg_bytes = base64.b64decode(b64svg)
    svg_str = svg_bytes.decode('utf-8')
    svg_str = svg_str.replace('#d6c7a3', bg_color).replace('#ccbe99', grain_color)
    return base64.b64encode(svg_str.encode('utf-8')).decode('ascii')

KRAFT_NATO  = _kraft_variant(A['KRAFT_SVG'], '#d6c7a3', '#ccbe99')
KRAFT_SOV   = _kraft_variant(A['KRAFT_SVG'], '#d4c075', '#c8b060')
KRAFT_MNATO = _kraft_variant(A['KRAFT_SVG'], '#e4dfd2', '#d8d4c8')
KRAFT_MEAST = _kraft_variant(A['KRAFT_SVG'], '#c8c1b2', '#bcb5a6')

# ---------- HTML ----------
HTML = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0, viewport-fit=cover">
<meta name="theme-color" content="#1a1e10">
<meta name="apple-mobile-web-app-capable" content="yes">
<title>RECON STATION</title>
<style>
/* =============================================
   DCS RECON STATION v{APP_VERSION}
   Canvas-native photo intelligence tool
   ============================================= */

@font-face {{
  font-family: 'Roboto Mono';
  font-weight: 400;
  font-display: swap;
  src: url('data:font/woff2;base64,{A["ROBOTO_MONO_400"]}') format('woff2');
}}
@font-face {{
  font-family: 'Roboto Mono';
  font-weight: 700;
  font-display: swap;
  src: url('data:font/woff2;base64,{A["ROBOTO_MONO_400"]}') format('woff2');
}}
@font-face {{
  font-family: 'Stardos Stencil';
  font-weight: 700;
  font-display: swap;
  src: url('data:font/woff2;base64,{A["STARDOS_700"]}') format('woff2');
}}
@font-face {{
  font-family: 'Oswald';
  font-weight: 500;
  font-display: swap;
  src: url('data:font/woff2;base64,{A["OSWALD_500"]}') format('woff2');
}}
@font-face {{
  font-family: 'Caveat';
  font-weight: 400;
  font-display: swap;
  src: url('data:font/woff2;base64,{A["CAVEAT_400"]}') format('woff2');
}}

:root {{
  --f-stencil:    'Stardos Stencil', 'Impact', 'Arial Narrow Bold', sans-serif;
  --f-typewriter: 'Roboto Mono', 'Courier New', monospace;
  --f-ui:         'Oswald', 'Arial Narrow', sans-serif;
  --amber:        #c0892a;
  --amber-dark:   #8a5e15;
  --green-radar:  #4f6b3a;
}}

/* THÈMES — 4 identiques à BG */
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

* {{ box-sizing: border-box; margin: 0; padding: 0; }}
html, body {{ height: 100%; overscroll-behavior: none; }}
button, input, select, textarea {{ font: inherit; cursor: pointer; }}

body {{
  font-family: var(--f-typewriter);
  background: var(--olive-deep);
  color: var(--paper);
  font-size: 14px;
  line-height: 1.5;
  overflow: hidden;
  -webkit-tap-highlight-color: transparent;
  -webkit-text-size-adjust: 100%;
}}

/* ======== TOOLBAR ======== */
.toolbar {{
  position: fixed;
  top: 0; left: 0; right: 0;
  height: 56px;
  background: linear-gradient(180deg, var(--olive-dark) 0%, var(--olive-deep) 100%);
  border-bottom: 2px solid var(--amber-dark);
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
  color: var(--amber);
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
.tb-select {{
  font-family: var(--f-ui);
  font-weight: 500;
  letter-spacing: 1px;
  font-size: 12px;
  text-transform: uppercase;
  background-color: var(--olive-dark);
  color: var(--amber);
  border: 1px solid var(--amber-dark);
  padding: 0 28px 0 10px;
  height: 36px;
  cursor: pointer;
  appearance: none;
  background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 12 8'><path d='M1 1l5 5 5-5' fill='none' stroke='%23c0892a' stroke-width='2'/></svg>");
  background-repeat: no-repeat;
  background-position: right 8px center;
  background-size: 10px 6px;
  transition: all .15s;
  white-space: nowrap;
}}
.tb-select:hover, .tb-select:focus-visible {{
  background-color: var(--olive);
  border-color: var(--amber);
  outline: none;
}}
.tb-select option {{ background-color: var(--olive-dark); color: var(--paper); }}
.tb-lang-btn {{
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
  font-size: 18px;
  transition: all .15s;
}}
.tb-lang-btn:hover, .tb-lang-btn:focus-visible {{
  background: var(--olive);
  border-color: var(--amber);
  outline: none;
}}
.tb-spacer {{ flex: 1; }}
.tb-version {{
  font-size: 11px;
  opacity: .45;
  color: var(--amber);
  letter-spacing: .5px;
  user-select: none;
  white-space: nowrap;
}}

/* ======== MAIN LAYOUT ======== */
.app {{
  position: fixed;
  top: 56px; bottom: 0; left: 0; right: 0;
  display: grid;
  grid-template-columns: 420px 1fr;
  background: var(--olive-deep);
}}

/* ======== EDITOR PANEL ======== */
.editor {{
  background: linear-gradient(180deg, var(--olive-dark) 0%, var(--olive-deep) 100%);
  border-right: 2px solid var(--amber-dark);
  overflow-y: auto;
  overscroll-behavior: contain;
  padding: 14px 14px 80px 14px;
  color: var(--paper);
}}
.editor::-webkit-scrollbar {{ width: 8px; }}
.editor::-webkit-scrollbar-track {{ background: var(--olive-deep); }}
.editor::-webkit-scrollbar-thumb {{ background: var(--khaki); border: 2px solid var(--olive-deep); }}

.ed-section {{
  margin-bottom: 10px;
  border: 1px solid var(--khaki);
  background: rgba(20,24,12,.5);
}}
.ed-section > summary {{
  cursor: pointer;
  padding: 10px 14px;
  background: linear-gradient(90deg, var(--olive) 0%, var(--olive-dark) 100%);
  font-family: var(--f-stencil);
  font-size: 12px;
  letter-spacing: 2px;
  color: var(--amber);
  list-style: none;
  display: flex; align-items: center; justify-content: space-between;
  border-bottom: 1px solid var(--amber-dark);
  user-select: none;
  min-height: 42px;
}}
.ed-section > summary::-webkit-details-marker {{ display: none; }}
.ed-section > summary::after {{
  content: '◄';
  font-size: 10px;
  color: var(--paper);
  transition: transform .2s;
}}
.ed-section[open] > summary::after {{ transform: rotate(-90deg); }}
.ed-section > .ed-body {{ padding: 12px; }}

/* Form fields */
.ed-row {{
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}}
.ed-label {{
  font-family: var(--f-ui);
  font-size: 11px;
  letter-spacing: 1.5px;
  color: var(--khaki-light);
  text-transform: uppercase;
  white-space: nowrap;
  min-width: 72px;
  flex-shrink: 0;
}}
.ed-input {{
  flex: 1;
  background: var(--olive-deep);
  border: 1px solid var(--khaki);
  color: var(--paper);
  padding: 6px 8px;
  font-family: var(--f-typewriter);
  font-size: 12px;
  transition: border-color .15s;
}}
.ed-input:focus {{ border-color: var(--amber); outline: none; }}
.ed-input::placeholder {{ color: var(--khaki); opacity: .6; }}
.ed-toggle-row {{
  display: flex;
  align-items: center;
  gap: 8px;
  font-family: var(--f-typewriter);
  font-size: 11px;
  color: var(--paper-light);
  cursor: pointer;
}}
.ed-toggle-row input[type=checkbox] {{
  accent-color: var(--amber);
  width: 14px; height: 14px;
}}
.ed-select {{
  flex: 1;
  background: var(--olive-deep);
  border: 1px solid var(--khaki);
  color: var(--paper);
  padding: 5px 8px;
  font-family: var(--f-typewriter);
  font-size: 11px;
  cursor: pointer;
}}
.ed-select:focus {{ border-color: var(--amber); outline: none; }}
.label-text-input {{
  width: 100%;
  margin-top: 4px;
  box-sizing: border-box;
}}

/* Contrast slider */
.ed-slider {{
  -webkit-appearance: none;
  width: 100%;
  height: 4px;
  background: var(--khaki);
  border-radius: 2px;
  outline: none;
  cursor: pointer;
}}
.ed-slider::-webkit-slider-thumb {{
  -webkit-appearance: none;
  width: 14px; height: 14px;
  border-radius: 50%;
  background: var(--amber);
  cursor: pointer;
}}

/* Drop zone */
.drop-zone {{
  border: 2px dashed var(--khaki);
  padding: 24px 16px;
  text-align: center;
  cursor: pointer;
  transition: all .2s;
  color: var(--khaki-light);
  font-family: var(--f-ui);
  font-size: 12px;
  letter-spacing: 1.5px;
  text-transform: uppercase;
}}
.drop-zone:hover, .drop-zone.dragover {{
  border-color: var(--amber);
  background: rgba(192,137,42,.08);
  color: var(--amber);
}}
.drop-zone.has-image {{
  border-style: solid;
  border-color: var(--green-radar);
  color: var(--green-radar);
}}

/* Cartouche editor */
.cartouche-row {{
  display: grid;
  grid-template-columns: 32px 1fr 28px 28px;
  gap: 4px;
  margin-bottom: 4px;
  align-items: center;
}}
.cartouche-num {{
  background: var(--olive-deep);
  border: 1px solid var(--khaki);
  color: var(--amber);
  text-align: center;
  padding: 5px 4px;
  font-family: var(--f-typewriter);
  font-size: 12px;
  font-weight: 700;
}}
.btn-remove-row {{
  background: var(--olive-dark);
  border: 1px solid var(--red-faded);
  color: var(--red-faded);
  padding: 4px 6px;
  cursor: pointer;
  font-size: 14px;
  transition: all .15s;
  display: flex; align-items: center; justify-content: center;
  line-height: 1;
}}
.btn-remove-row:hover {{ background: var(--red-stamp); color: white; border-color: var(--red-stamp); }}

/* Checkbox point visible */
.cartouche-point-toggle {{
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  user-select: none;
}}
.cartouche-point-toggle input[type="checkbox"] {{
  position: absolute;
  opacity: 0;
  width: 0; height: 0;
}}
.point-marker {{
  display: flex; align-items: center; justify-content: center;
  width: 28px; height: 28px;
  border: 1px solid var(--khaki);
  background: var(--olive-dark);
  color: var(--khaki);
  font-size: 14px;
  transition: all .15s;
  cursor: pointer;
}}
.cartouche-point-toggle input:checked + .point-marker {{
  border-color: #E22;
  color: #E22;
  background: rgba(238,34,34,.12);
}}
.btn-add-row {{
  margin-top: 8px;
  background: var(--olive-dark);
  border: 1px solid var(--amber-dark);
  color: var(--amber);
  padding: 7px 14px;
  cursor: pointer;
  font-family: var(--f-ui);
  font-size: 11px;
  letter-spacing: 1.5px;
  text-transform: uppercase;
  transition: all .15s;
  width: 100%;
}}
.btn-add-row:hover {{ background: var(--olive); border-color: var(--amber); }}
.btn-add-inset {{
  border-color: var(--green-radar);
  color: var(--green-radar);
  margin-top: 4px;
}}
.btn-add-inset:hover {{ border-color: #6fa56b; color: #6fa56b; }}
/* Toolbox formes (Lot 1) */
.shapes-toolbox {{
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
  margin-bottom: 8px;
}}
.shapes-toolbox button {{
  background: var(--olive-dark);
  border: 1px solid var(--amber-dark);
  color: var(--amber);
  padding: 6px 10px;
  font-family: var(--f-ui);
  font-size: 12px;
  letter-spacing: 1px;
  cursor: pointer;
  transition: all .15s;
  flex: 1;
  min-width: 44px;
}}
.shapes-toolbox button:hover {{ background: var(--olive); border-color: var(--amber); }}
/* Éditeur formes */
.shape-row {{
  border: 1px solid var(--khaki);
  background: rgba(20,24,12,.4);
  margin-bottom: 5px;
  padding: 7px 8px;
}}
.shape-row-header {{
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 4px;
}}
.shape-badge {{
  font-family: var(--f-stencil);
  font-size: 10px;
  letter-spacing: 2px;
  color: var(--amber);
  text-transform: uppercase;
  flex: 1;
}}
.shape-color-group {{
  display: flex;
  gap: 3px;
}}
.shape-color-group button {{
  background: var(--olive-dark);
  border: 1px solid var(--khaki);
  color: var(--khaki-light);
  padding: 3px 7px;
  font-family: var(--f-ui);
  font-size: 10px;
  letter-spacing: 1px;
  text-transform: uppercase;
  cursor: pointer;
  transition: all .15s;
}}
.shape-color-group button.active {{
  border-color: var(--amber);
  color: var(--amber);
  background: rgba(192,137,42,.12);
}}
.shape-poly-controls {{
  display: flex;
  gap: 4px;
  margin-top: 4px;
}}
.shape-poly-btn {{
  background: var(--olive-dark);
  border: 1px solid var(--khaki);
  color: var(--khaki-light);
  padding: 3px 8px;
  font-family: var(--f-ui);
  font-size: 10px;
  letter-spacing: 1px;
  text-transform: uppercase;
  cursor: pointer;
  transition: all .15s;
}}
.shape-poly-btn:hover {{ border-color: var(--amber-dark); color: var(--amber); }}
.shape-poly-btn.active {{
  border-color: var(--amber);
  color: var(--amber);
  background: rgba(192,137,42,.12);
}}
#shapes-editor {{
  margin-top: 6px;
}}
.amorce-row {{
  padding: 0 4px 4px 4px;
  margin-top: -2px;
}}
.amorce-toggle {{
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  user-select: none;
}}
.amorce-toggle input[type="checkbox"] {{
  position: absolute;
  opacity: 0;
  width: 0; height: 0;
}}
.amorce-marker {{
  display: inline-flex;
  align-items: center;
  padding: 3px 8px;
  background: var(--olive-dark);
  border: 1px solid var(--khaki);
  color: var(--khaki-light);
  font-family: var(--f-ui);
  font-size: 10px;
  letter-spacing: 1px;
  text-transform: uppercase;
  transition: all .15s;
  cursor: pointer;
}}
.amorce-toggle input:checked + .amorce-marker {{
  border-color: var(--amber-dark);
  color: var(--amber);
  background: rgba(192,137,42,.1);
}}
.inset-row {{
  border: 1px solid var(--green-radar);
  background: rgba(79,107,58,.08);
  margin-bottom: 6px;
  padding: 8px;
}}
.inset-row-header {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
}}
.inset-num {{
  font-family: var(--f-stencil);
  font-size: 11px;
  letter-spacing: 2px;
  color: var(--green-radar);
  text-transform: uppercase;
}}
.inset-color-group {{
  display: flex;
  gap: 3px;
}}
.inset-color-group button {{
  background: var(--olive-dark);
  border: 1px solid var(--khaki);
  color: var(--khaki-light);
  padding: 3px 7px;
  font-family: var(--f-ui);
  font-size: 10px;
  letter-spacing: 1px;
  text-transform: uppercase;
  cursor: pointer;
  transition: all .15s;
}}
.inset-color-group button.active {{
  border-color: var(--amber);
  color: var(--amber);
  background: rgba(192,137,42,.12);
}}
.inset-label-row {{
  display: flex;
  gap: 6px;
  align-items: center;
  margin-top: 5px;
}}
.inset-label-input {{
  flex: 1;
  background: var(--olive-deep);
  border: 1px solid var(--khaki);
  color: var(--paper);
  padding: 4px 7px;
  font-family: var(--f-typewriter);
  font-size: 11px;
}}
.inset-label-input:focus {{ border-color: var(--amber); outline: none; }}

/* Logo picker */
.logo-grid {{
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 6px;
  margin-bottom: 8px;
}}
.logo-thumb {{
  aspect-ratio: 1;
  border: 2px solid var(--khaki);
  cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  background: rgba(0,0,0,.3);
  padding: 4px;
  transition: all .15s;
  overflow: hidden;
}}
.logo-thumb img {{ width: 100%; height: 100%; object-fit: contain; }}
.logo-thumb.active {{
  border-color: var(--amber);
  background: rgba(192,137,42,.15);
}}
.logo-thumb:hover {{ border-color: var(--khaki-light); }}
.logo-thumb-custom {{ position: relative; }}
.logo-thumb-del {{
  position: absolute; top: 2px; right: 2px;
  background: rgba(20,10,10,.90);
  border: 1px solid var(--red-faded);
  color: var(--red-faded);
  width: 34px; height: 34px;      /* cible tactile ≥34px (G3) */
  font-size: 13px; line-height: 1;
  display: flex; align-items: center; justify-content: center;
  cursor: pointer; padding: 0;
  opacity: 1;                     /* toujours visible — plus de gating :hover (G3) */
  transition: background .15s, border-color .15s, color .15s;
}}
.logo-thumb-del:hover {{ background: var(--red-stamp); color: #fff; border-color: var(--red-stamp); }}
.logo-thumb-none {{
  color: var(--khaki);
  font-family: var(--f-ui);
  font-size: 10px;
  letter-spacing: 1px;
  text-align: center;
}}

/* Export button */
.btn-export {{
  width: 100%;
  background: linear-gradient(180deg, var(--olive) 0%, var(--olive-dark) 100%);
  border: 2px solid var(--amber);
  color: var(--amber);
  padding: 12px;
  font-family: var(--f-stencil);
  font-size: 14px;
  letter-spacing: 3px;
  text-transform: uppercase;
  cursor: pointer;
  transition: all .2s;
  margin-top: 4px;
}}
.btn-export:hover:not(:disabled) {{
  background: linear-gradient(180deg, var(--amber-dark) 0%, var(--olive) 100%);
  color: var(--paper);
}}
.btn-export:disabled {{
  opacity: .35;
  cursor: not-allowed;
}}

/* Replace image button */
.btn-replace {{
  width: 100%;
  background: var(--olive-dark);
  border: 1px solid var(--khaki);
  color: var(--khaki-light);
  padding: 7px;
  font-family: var(--f-ui);
  font-size: 11px;
  letter-spacing: 1.5px;
  text-transform: uppercase;
  cursor: pointer;
  transition: all .15s;
  margin-top: 6px;
}}
.btn-replace:hover {{ border-color: var(--amber-dark); color: var(--amber); }}

/* Upload logo btn */
.btn-upload-logo {{
  background: var(--olive-dark);
  border: 1px dashed var(--khaki);
  color: var(--khaki-light);
  padding: 7px 12px;
  font-family: var(--f-ui);
  font-size: 11px;
  letter-spacing: 1.5px;
  text-transform: uppercase;
  cursor: pointer;
  transition: all .15s;
  width: 100%;
  text-align: center;
  display: block;
  margin-top: 6px;
}}
.btn-upload-logo:hover {{ border-color: var(--amber-dark); color: var(--amber); }}

/* Logo mode — boutons segmentés */
.logo-mode-label {{
  font-family: var(--f-ui);
  font-size: 10px;
  letter-spacing: 1.5px;
  color: var(--khaki-light);
  text-transform: uppercase;
  margin-top: 10px;
  margin-bottom: 4px;
}}
.logo-mode {{
  display: flex;
  gap: 4px;
}}
.logo-mode button {{
  flex: 1;
  background: var(--olive-dark);
  border: 1px solid var(--khaki);
  color: var(--khaki-light);
  padding: 6px 4px;
  font-family: var(--f-ui);
  font-size: 10px;
  letter-spacing: 1.5px;
  text-transform: uppercase;
  cursor: pointer;
  transition: all .15s;
}}
.logo-mode button:hover {{ border-color: var(--amber-dark); color: var(--amber); }}
.logo-mode button.active {{
  background: var(--olive);
  border-color: var(--amber);
  color: var(--amber);
  font-weight: 700;
}}

/* ======== PREVIEW PANEL ======== */
.preview {{
  position: relative;
  background: #111;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}}
.preview-inner {{
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
}}
#preview-canvas {{
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
  display: block;
  image-rendering: -webkit-optimize-contrast;
  image-rendering: crisp-edges;
}}
.preview-placeholder {{
  text-align: center;
  color: var(--khaki);
  font-family: var(--f-ui);
  font-size: 13px;
  letter-spacing: 2px;
  text-transform: uppercase;
  opacity: .5;
  user-select: none;
  pointer-events: none;
}}
.preview-placeholder svg {{
  width: 64px; height: 64px;
  margin-bottom: 12px;
  opacity: .3;
}}

/* ======== TOAST ======== */
.toast-container {{
  position: fixed;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 9999;
  display: flex;
  flex-direction: column;
  gap: 6px;
  pointer-events: none;
}}
.toast {{
  background: var(--olive-dark);
  border: 1px solid var(--amber-dark);
  color: var(--paper);
  padding: 10px 18px;
  font-family: var(--f-ui);
  font-size: 12px;
  letter-spacing: 1.5px;
  text-transform: uppercase;
  pointer-events: none;
  opacity: 0;
  transition: opacity .3s;
  white-space: nowrap;
  box-shadow: 0 4px 16px rgba(0,0,0,.5);
}}
.toast.show {{ opacity: 1; }}
.toast.ok {{ border-color: var(--green-radar); }}
.toast.err {{ border-color: var(--red-faded); color: var(--red-faded); }}

/* ======== RESPONSIVE — tablette <1100px ======== */
@media (max-width: 1100px) {{
  .app {{
    grid-template-columns: 1fr;
    grid-template-rows: 1fr auto;
  }}
  .editor {{
    border-right: none;
    border-top: 2px solid var(--amber-dark);
    order: 2;
    max-height: 50vh;
    padding-bottom: 20px;
  }}
  .preview {{
    order: 1;
    min-height: 40vh;
  }}
  /* Tab bar */
  .tab-bar {{
    display: flex;
    position: fixed;
    bottom: 0; left: 0; right: 0;
    height: 48px;
    background: var(--olive-deep);
    border-top: 1px solid var(--amber-dark);
    z-index: 900;
  }}
  .tab-btn {{
    flex: 1;
    background: none;
    border: none;
    color: var(--khaki-light);
    font-family: var(--f-ui);
    font-size: 10px;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    cursor: pointer;
    padding: 6px 4px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 2px;
    transition: all .15s;
  }}
  .tab-btn.active {{ color: var(--amber); }}
  .tab-btn svg {{ width: 18px; height: 18px; }}
  /* En mode tablette, afficher uniquement la zone active */
  .app[data-active-tab="editor"] .preview {{ display: none; }}
  .app[data-active-tab="editor"] .editor {{ max-height: calc(100vh - 56px - 48px); order: 1; }}
  .app[data-active-tab="preview"] .editor {{ display: none; }}
  .app[data-active-tab="preview"] .preview {{ min-height: calc(100vh - 56px - 48px); order: 1; }}
}}
@media (min-width: 1101px) {{
  .tab-bar {{ display: none; }}
}}
</style>
</head>
<body data-theme="cw-nato">

<!-- TOOLBAR -->
<header class="toolbar" role="toolbar" aria-label="Recon Station">
  <div class="tb-brand">
    <span class="tb-brand-main">RECON STATION</span>
    <span class="tb-brand-sub">░ PHOTO INTELLIGENCE</span>
  </div>
  <div class="tb-sep"></div>
  <select class="tb-select" id="theme-select" data-i18n-title="toolbar.theme.tooltip" title="Thème graphique">
    <option value="cw-nato"     data-i18n="theme.cw-nato">Cold War OTAN</option>
    <option value="cw-soviet"   data-i18n="theme.cw-soviet">Cold War Soviétique</option>
    <option value="modern-nato" data-i18n="theme.modern-nato">OTAN moderne</option>
    <option value="modern-east" data-i18n="theme.modern-east">Bloc Est moderne</option>
  </select>
  <button class="tb-lang-btn" id="btn-lang" title="Switch language / Changer de langue">🇬🇧</button>
  <div class="tb-spacer"></div>
  <span class="tb-version">v{APP_VERSION}</span>
</header>

<!-- MAIN APP -->
<div class="app" id="app" data-active-tab="editor">

  <!-- EDITOR -->
  <div class="editor" id="editor-panel" role="complementary">

    <!-- Section Image -->
    <details class="ed-section" open>
      <summary data-i18n="editor.image.title">IMAGE SOURCE</summary>
      <div class="ed-body">
        <div class="drop-zone" id="drop-zone" tabindex="0"
             data-i18n-aria-label="editor.image.dropzone.aria"
             aria-label="Zone de dépôt d'image">
          <div id="drop-zone-text" data-i18n="editor.image.drop">↓ DÉPOSER UNE IMAGE ICI</div>
          <div style="font-size:11px;margin-top:6px;opacity:.6" data-i18n="editor.image.drop.hint">PNG · JPEG — cliquer pour parcourir</div>
        </div>
        <input type="file" id="file-source" accept="image/png,image/jpeg,image/webp" hidden>
        <button class="btn-replace" id="btn-replace" data-i18n="editor.image.replace">↺ REMPLACER L'IMAGE</button>
      </div>
    </details>

    <!-- Section Rendu -->
    <details class="ed-section" open>
      <summary data-i18n="editor.render.title">RENDU</summary>
      <div class="ed-body">
        <div class="ed-row">
          <span class="ed-label" data-i18n="editor.render.contrast">CONTRASTE</span>
          <input type="range" class="ed-slider" id="contrast-slider" min="100" max="130" value="105" step="1">
          <span id="contrast-val" style="min-width:36px;text-align:right;font-family:var(--f-typewriter);font-size:12px;color:var(--amber)">105%</span>
        </div>
      </div>
    </details>

    <!-- Section Couleur texte -->
    <details class="ed-section" open>
      <summary data-i18n="editor.text.title">COULEUR DU TEXTE</summary>
      <div class="ed-body">
        <div class="logo-mode" id="text-color-group" role="group" aria-label="Couleur du texte">
          <button type="button" data-text-color="#fff" data-i18n="editor.text.white">Blanc</button>
          <button type="button" data-text-color="#000" data-i18n="editor.text.black">Noir</button>
        </div>
      </div>
    </details>

    <!-- Section Effets -->
    <details class="ed-section" open>
      <summary data-i18n="editor.fx.title">EFFETS</summary>
      <div class="ed-body">
        <div class="ed-row">
          <span class="ed-label" data-i18n="editor.fx.sensor">Imagerie</span>
          <select id="sensor-mode" class="ed-select">
            <option value="eo"       data-i18n="editor.fx.sensor.eo">EO</option>
            <option value="ir-white" data-i18n="editor.fx.sensor.irw">IR Blanc</option>
            <option value="ir-black" data-i18n="editor.fx.sensor.irb">IR Noir</option>
            <option value="sar"      data-i18n="editor.fx.sensor.sar">SAR</option>
          </select>
        </div>
        <div class="ed-row">
          <span class="ed-label" data-i18n="editor.fx.vignette">Vignette</span>
          <input type="range" class="ed-slider" id="fx-vignette" min="0" max="100" value="0" step="1">
          <span class="fx-val" id="fx-vignette-val" style="min-width:36px;text-align:right;font-family:var(--f-typewriter);font-size:12px;color:var(--amber)">0</span>
        </div>
        <div class="ed-row">
          <span class="ed-label" data-i18n="editor.fx.grain">Grain</span>
          <input type="range" class="ed-slider" id="fx-grain" min="0" max="100" value="0" step="1">
          <span class="fx-val" id="fx-grain-val" style="min-width:36px;text-align:right;font-family:var(--f-typewriter);font-size:12px;color:var(--amber)">0</span>
        </div>
        <div class="ed-row">
          <span class="ed-label" data-i18n="editor.fx.scanlines">Lignes capteur</span>
          <input type="range" class="ed-slider" id="fx-scanlines" min="0" max="100" value="0" step="1">
          <span class="fx-val" id="fx-scanlines-val" style="min-width:36px;text-align:right;font-family:var(--f-typewriter);font-size:12px;color:var(--amber)">0</span>
        </div>
      </div>
    </details>

    <!-- Section Bloc info -->
    <details class="ed-section" open>
      <summary data-i18n="editor.info.title">BLOC D'INFORMATIONS</summary>
      <div class="ed-body">
        <div class="ed-row">
          <span class="ed-label">Target</span>
          <input class="ed-input" id="f-target" type="text" data-i18n-placeholder="editor.info.target.ph" placeholder="Nom de l'objectif">
        </div>
        <div class="ed-row">
          <span class="ed-label">Coords</span>
          <input class="ed-input" id="f-coords" type="text" data-i18n-placeholder="editor.info.coords.ph" placeholder="N00°00.0 E000°00.0">
        </div>
        <div class="ed-row">
          <span class="ed-label">Crs</span>
          <input class="ed-input" id="f-crs" type="text" data-i18n-placeholder="editor.info.crs.ph" placeholder="000°" style="max-width:80px">
          <span class="ed-label" style="min-width:30px">Alt</span>
          <input class="ed-input" id="f-alt" type="text" data-i18n-placeholder="editor.info.alt.ph" placeholder="0000ft" style="max-width:80px">
        </div>
        <div class="ed-row">
          <span class="ed-label">Msn</span>
          <input class="ed-input" id="f-msn" type="text" data-i18n-placeholder="editor.info.msn.ph" placeholder="Nom de la mission">
        </div>
        <div class="ed-row">
          <span class="ed-label">Sensor</span>
          <input class="ed-input" id="f-sensor" type="text" data-i18n-placeholder="editor.info.sensor.ph" placeholder="Capteur">
        </div>
        <div class="ed-row">
          <span class="ed-label">DTG</span>
          <input class="ed-input" id="f-dtg" type="text" data-i18n-placeholder="editor.info.dtg.ph" placeholder="DD.MM.YYYY">
        </div>
        <div class="ed-row">
          <span class="ed-label">Crew</span>
          <input class="ed-input" id="f-crew" type="text" data-i18n-placeholder="editor.info.crew.ph" placeholder="Callsign">
        </div>
        <div class="ed-row">
          <span class="ed-label">Class</span>
          <input class="ed-input" id="f-class" type="text" data-i18n-placeholder="editor.info.class.ph" placeholder="Conf / Unclas…">
        </div>
      </div>
    </details>

    <!-- Section Logo -->
    <details class="ed-section" open>
      <summary data-i18n="editor.logo.title">LOGO</summary>
      <div class="ed-body">
        <div class="logo-grid" id="logo-grid"></div>
        <label class="btn-upload-logo" for="file-logo" data-i18n="editor.logo.upload">↑ IMPORTER UN LOGO PNG</label>
        <input type="file" id="file-logo" accept="image/png,image/webp" hidden>
        <label class="btn-upload-logo" for="file-wing" data-i18n="editor.logo.importWing" style="margin-top:4px">↑ IMPORTER CONFIG WING (BG)</label>
        <input type="file" id="file-wing" accept=".json,application/json" hidden>
        <div class="logo-mode-label" data-i18n="editor.logo.mode.title">RENDU DU LOGO</div>
        <div class="logo-mode" id="logo-mode" role="group" aria-label="Rendu du logo">
          <button type="button" data-logo-mode="color" data-i18n="editor.logo.mode.color">COULEUR</button>
          <button type="button" data-logo-mode="gray"  data-i18n="editor.logo.mode.gray">GRIS</button>
          <button type="button" data-logo-mode="white" data-i18n="editor.logo.mode.white">BLANC</button>
        </div>
      </div>
    </details>

    <!-- Section Cartouche -->
    <details class="ed-section" open>
      <summary data-i18n="editor.cartouche.title">CARTOUCHE</summary>
      <div class="ed-body">
        <div id="cartouche-editor"></div>
        <button class="btn-add-row" id="btn-add-cartouche" data-i18n="editor.cartouche.add">+ AJOUTER UN MARQUAGE</button>
        <button class="btn-add-row btn-add-inset" id="btn-add-inset" data-i18n="editor.inset.add">+ AJOUTER UNE LOUPE</button>
        <div id="inset-editor"></div>
      </div>
    </details>

    <!-- Section Formes (Lot 1) -->
    <details class="ed-section" open>
      <summary data-i18n="editor.shapes.title">FORMES</summary>
      <div class="ed-body">
        <div class="shapes-toolbox">
          <button type="button" id="btn-add-ellipse" title="Ellipse" data-i18n-title="editor.shapes.ellipse.tooltip">◯</button>
          <button type="button" id="btn-add-rect"    title="Rectangle" data-i18n-title="editor.shapes.rect.tooltip">▭</button>
          <button type="button" id="btn-add-poly"    title="Polygone" data-i18n-title="editor.shapes.poly.tooltip">⬡</button>
          <button type="button" id="btn-add-arrow"   title="Flèche" data-i18n-title="editor.shapes.arrow.tooltip">→</button>
          <button type="button" id="btn-add-bracket" title="Crochet" data-i18n-title="editor.shapes.bracket.tooltip">⊐</button>
        </div>
        <div id="shapes-editor"></div>
        <button class="btn-add-row btn-add-inset" id="btn-add-label" data-i18n="editor.label.add" data-i18n-title="editor.label.add.tooltip">+ LABEL</button>
        <div id="label-editor"></div>
      </div>
    </details>

    <!-- Section Couleur marquages -->
    <details class="ed-section" open>
      <summary data-i18n="editor.marker.color">COULEUR DES MARQUAGES</summary>
      <div class="ed-body">
        <div class="logo-mode" id="marker-color-group" role="group" aria-label="Couleur des marquages">
          <button type="button" data-marker-color="red"   data-i18n="editor.marker.red">Rouge</button>
          <button type="button" data-marker-color="black" data-i18n="editor.marker.black">Noir</button>
          <button type="button" data-marker-color="white" data-i18n="editor.marker.white">Blanc</button>
        </div>
      </div>
    </details>

    <!-- Section Classification (R2-B Lot 2) -->
    <details class="ed-section">
      <summary data-i18n="editor.classif.title">CLASSIFICATION</summary>
      <div class="ed-body">
        <label class="ed-toggle-row">
          <input type="checkbox" id="classif-enable">
          <span data-i18n="editor.classif.enable">Activer le bandeau</span>
        </label>
        <div class="ed-row" style="margin-top:6px">
          <span class="ed-label" data-i18n="editor.classif.level">NIVEAU</span>
          <select id="classif-level" class="ed-select">
            <option value="UNCLASSIFIED">UNCLASSIFIED</option>
            <option value="CONFIDENTIAL">CONFIDENTIAL</option>
            <option value="SECRET">SECRET</option>
            <option value="TOP SECRET">TOP SECRET</option>
          </select>
        </div>
      </div>
    </details>

    <!-- Section Export -->
    <details class="ed-section" open>
      <summary data-i18n="editor.export.title">EXPORT</summary>
      <div class="ed-body">
        <button class="btn-export" id="btn-export" disabled data-i18n="editor.export.btn">
          ↓ EXPORTER PNG
        </button>
        <p style="margin-top:8px;font-family:var(--f-ui);font-size:10px;letter-spacing:1px;color:var(--khaki);text-align:center" data-i18n="editor.export.hint">Export pleine résolution · lossless</p>
      </div>
    </details>

  </div><!-- /editor -->

  <!-- PREVIEW -->
  <div class="preview" id="preview-panel" role="main">
    <div class="preview-inner">
      <div class="preview-placeholder" id="preview-placeholder">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <rect x="3" y="3" width="18" height="18" rx="2"/>
          <circle cx="8.5" cy="8.5" r="1.5"/>
          <polyline points="21 15 16 10 5 21"/>
        </svg>
        <div data-i18n="preview.empty">IMPORTER UNE IMAGE POUR COMMENCER</div>
      </div>
      <canvas id="preview-canvas" hidden></canvas>
    </div>
  </div>

</div><!-- /app -->

<!-- TAB BAR (tablette) -->
<nav class="tab-bar" role="tablist" aria-label="Navigation">
  <button class="tab-btn active" id="tab-editor" role="tab" aria-selected="true" data-tab="editor" data-i18n-aria-label="tab.editor.aria">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
      <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
      <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
    </svg>
    <span data-i18n="tab.editor">ÉDITEUR</span>
  </button>
  <button class="tab-btn" id="tab-preview" role="tab" aria-selected="false" data-tab="preview" data-i18n-aria-label="tab.preview.aria">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
      <rect x="3" y="3" width="18" height="18" rx="2"/>
      <circle cx="8.5" cy="8.5" r="1.5"/>
      <polyline points="21 15 16 10 5 21"/>
    </svg>
    <span data-i18n="tab.preview">APERÇU</span>
  </button>
</nav>

<!-- TOAST -->
<div class="toast-container" id="toast-container" aria-live="polite"></div>

<!-- HIDDEN CANVAS (export full-res) -->
<canvas id="export-canvas" hidden></canvas>

<script>
'use strict';

// =============================================================
//  RECON STATION — v{APP_VERSION}
//  Canvas-native photo intelligence composer
// =============================================================

const APP_VERSION = '{APP_VERSION}';

// ── i18n ──────────────────────────────────────────────────────
const I18N = {{
  fr: {{
    'toolbar.theme.tooltip': 'Thème graphique',
    'toolbar.lang.tooltip': 'Passer en anglais',
    'theme.cw-nato': 'Cold War OTAN',
    'theme.cw-soviet': 'Cold War Soviétique',
    'theme.modern-nato': 'OTAN moderne',
    'theme.modern-east': 'Bloc Est moderne',
    'editor.image.title': 'IMAGE SOURCE',
    'editor.image.drop': '↓ DÉPOSER UNE IMAGE ICI',
    'editor.image.drop.hint': 'PNG · JPEG — cliquer pour parcourir',
    'editor.image.dropzone.aria': "Zone de dépôt d\u2019image",
    'editor.image.replace': "↺ REMPLACER L\u2019IMAGE",
    'editor.render.title': 'RENDU',
    'editor.render.contrast': 'CONTRASTE',
    'editor.info.title': "BLOC D\u2019INFORMATIONS",
    'editor.info.target.ph': "Nom de l\u2019objectif",
    'editor.info.coords.ph': 'N00°00.0 E000°00.0',
    'editor.info.crs.ph': '000°',
    'editor.info.alt.ph': '0000ft',
    'editor.info.msn.ph': 'Nom de la mission',
    'editor.info.sensor.ph': 'Capteur',
    'editor.info.dtg.ph': 'DD.MM.YYYY',
    'editor.info.crew.ph': 'Callsign',
    'editor.info.class.ph': 'Conf / Unclas…',
    'editor.logo.title': 'LOGO',
    'editor.logo.upload': '↑ IMPORTER UN LOGO PNG',
    'editor.cartouche.title': 'CARTOUCHE',
    'editor.cartouche.add': '+ AJOUTER UN MARQUAGE',
    'editor.cartouche.remove.aria': 'Supprimer la ligne',
    'editor.cartouche.label.ph': 'Label…',
    'editor.cartouche.point': 'Point visible',
    'editor.logo.mode.title': 'RENDU DU LOGO',
    'editor.logo.mode.color': 'COULEUR',
    'editor.logo.mode.gray': 'GRIS',
    'editor.logo.mode.white': 'BLANC',
    'editor.export.title': 'EXPORT',
    'editor.export.btn': '↓ EXPORTER PNG',
    'editor.export.hint': 'Export pleine résolution · lossless',
    'preview.empty': 'IMPORTER UNE IMAGE POUR COMMENCER',
    'tab.editor': 'ÉDITEUR',
    'tab.preview': 'APERÇU',
    'tab.editor.aria': 'Onglet éditeur',
    'tab.preview.aria': 'Onglet aperçu',
    'toast.lang': 'Langue : Français',
    'toast.theme': 'Thème appliqué',
    'toast.no-image': 'Aucune image source — veuillez en importer une',
    'toast.export.start': 'Export en cours…',
    'toast.export.done': 'Image exportée',
    'toast.state-restored': 'Paramètres restaurés — importer une image pour continuer',
    'toast.image-loaded': 'Image chargée',
    'editor.text.title': 'COULEUR DU TEXTE',
    'editor.text.white': 'Blanc',
    'editor.text.black': 'Noir',
    'editor.marker.color': 'COULEUR DES MARQUAGES',
    'editor.marker.red': 'Rouge',
    'editor.marker.black': 'Noir',
    'editor.marker.white': 'Blanc',
    'toast.fileMustBeImage': 'Le fichier doit être une image',
    'toast.logoInvalid': 'Logo invalide',
    'editor.logo.removeCustom': 'Supprimer le logo importé',
    'editor.logo.importWing': 'Importer config wing (BG)',
    'toast.jsonInvalid': 'JSON illisible',
    'toast.noLogoInJson': 'Aucun logo dans ce fichier',
    'toast.logosImported': '{{n}} logo(s) importé(s) ✓',
    'editor.fx.title': 'EFFETS',
    'editor.fx.vignette': 'Vignette',
    'editor.fx.grain': 'Grain',
    'editor.fx.scanlines': 'Lignes capteur',
    'editor.fx.sensor': 'Imagerie',
    'editor.fx.sensor.eo':  'EO (visible)',
    'editor.fx.sensor.irw': 'IR Blanc chaud',
    'editor.fx.sensor.irb': 'IR Noir chaud',
    'editor.fx.sensor.sar': 'SAR',
    // R2-B Lot 1
    'editor.shapes.title': 'FORMES',
    'editor.shapes.ellipse': 'ELLIPSE',
    'editor.shapes.ellipse.tooltip': 'Ajouter une ellipse',
    'editor.shapes.rect': 'RECT',
    'editor.shapes.rect.tooltip': 'Ajouter un rectangle',
    'editor.shapes.poly': 'POLY',
    'editor.shapes.poly.tooltip': 'Ajouter un polygone',
    'editor.shapes.arrow': 'FLÈCHE',
    'editor.shapes.arrow.tooltip': 'Ajouter une flèche',
    'editor.shapes.bracket': 'CROCHET',
    'editor.shapes.bracket.tooltip': 'Ajouter un crochet',
    'editor.shapes.remove.aria': 'Supprimer la forme',
    'editor.shapes.poly.addpt': 'point',
    'editor.shapes.poly.close': 'fermer',
    'editor.shapes.poly.open': 'ouvrir',
    // R2-A
    'editor.cartouche.amorce': 'Amorce',
    'editor.cartouche.amorce.tooltip': 'Relier un point de la photo par un trait',
    'editor.cartouche.amorce.aria': 'Toggle amorce',
    'editor.inset.add': '+ AJOUTER UNE LOUPE',
    'editor.inset.label': 'LOUPE',
    'editor.inset.remove.aria': 'Supprimer la loupe',
    'editor.inset.caption': 'LÉGENDE',
    'editor.inset.caption.ph': 'Label optionnel…',
    'inset.color.white': 'BLANC',
    'inset.color.black': 'NOIR',
    'inset.color.red': 'ROUGE',
    // R2-B Lot 2
    'editor.label.add': '+ LABEL',
    'editor.label.add.tooltip': 'Ajouter un label',
    'editor.label.text.ph': 'Texte…',
    'editor.label.style': 'STYLE',
    'editor.label.style.stamp': 'TAMPON',
    'editor.label.style.cursive': 'CURSIF',
    'editor.label.style.plain': 'NU',
    'editor.label.remove.aria': 'Supprimer le label',
    'editor.classif.title': 'CLASSIFICATION',
    'editor.classif.enable': 'Activer le bandeau',
    'editor.classif.level': 'NIVEAU',
  }},
  en: {{
    'toolbar.theme.tooltip': 'Graphic theme',
    'toolbar.lang.tooltip': 'Switch to French',
    'theme.cw-nato': 'Cold War NATO',
    'theme.cw-soviet': 'Cold War Soviet',
    'theme.modern-nato': 'Modern NATO',
    'theme.modern-east': 'Modern East Bloc',
    'editor.image.title': 'SOURCE IMAGE',
    'editor.image.drop': '↓ DROP IMAGE HERE',
    'editor.image.drop.hint': 'PNG · JPEG — click to browse',
    'editor.image.dropzone.aria': 'Image drop zone',
    'editor.image.replace': '↺ REPLACE IMAGE',
    'editor.render.title': 'RENDER',
    'editor.render.contrast': 'CONTRAST',
    'editor.info.title': 'INFO BLOCK',
    'editor.info.target.ph': 'Target name',
    'editor.info.coords.ph': 'N00°00.0 E000°00.0',
    'editor.info.crs.ph': '000°',
    'editor.info.alt.ph': '0000ft',
    'editor.info.msn.ph': 'Mission name',
    'editor.info.sensor.ph': 'Sensor',
    'editor.info.dtg.ph': 'DD.MM.YYYY',
    'editor.info.crew.ph': 'Callsign',
    'editor.info.class.ph': 'Conf / Unclas…',
    'editor.logo.title': 'LOGO',
    'editor.logo.upload': '↑ IMPORT PNG LOGO',
    'editor.cartouche.title': 'LEGEND',
    'editor.cartouche.add': '+ ADD MARKER',
    'editor.cartouche.remove.aria': 'Remove row',
    'editor.cartouche.label.ph': 'Label…',
    'editor.cartouche.point': 'Show marker',
    'editor.logo.mode.title': 'LOGO RENDERING',
    'editor.logo.mode.color': 'COLOR',
    'editor.logo.mode.gray': 'GRAY',
    'editor.logo.mode.white': 'WHITE',
    'editor.export.title': 'EXPORT',
    'editor.export.btn': '↓ EXPORT PNG',
    'editor.export.hint': 'Full resolution · lossless',
    'preview.empty': 'IMPORT AN IMAGE TO BEGIN',
    'tab.editor': 'EDITOR',
    'tab.preview': 'PREVIEW',
    'tab.editor.aria': 'Editor tab',
    'tab.preview.aria': 'Preview tab',
    'toast.lang': 'Language: English',
    'toast.theme': 'Theme applied',
    'toast.no-image': 'No source image — please import one',
    'toast.export.start': 'Exporting…',
    'toast.export.done': 'Image exported',
    'toast.state-restored': 'Settings restored — import an image to continue',
    'toast.image-loaded': 'Image loaded',
    'editor.text.title': 'TEXT COLOR',
    'editor.text.white': 'White',
    'editor.text.black': 'Black',
    'editor.marker.color': 'MARKER COLOR',
    'editor.marker.red': 'Red',
    'editor.marker.black': 'Black',
    'editor.marker.white': 'White',
    'toast.fileMustBeImage': 'File must be an image',
    'toast.logoInvalid': 'Invalid logo',
    'editor.logo.removeCustom': 'Remove imported logo',
    'editor.logo.importWing': 'Import wing config (BG)',
    'toast.jsonInvalid': 'Invalid JSON',
    'toast.noLogoInJson': 'No logo in this file',
    'toast.logosImported': '{{n}} logo(s) imported ✓',
    'editor.fx.title': 'EFFECTS',
    'editor.fx.vignette': 'Vignette',
    'editor.fx.grain': 'Grain',
    'editor.fx.scanlines': 'Scan lines',
    'editor.fx.sensor': 'Imagery',
    'editor.fx.sensor.eo':  'EO (visible)',
    'editor.fx.sensor.irw': 'IR White-hot',
    'editor.fx.sensor.irb': 'IR Black-hot',
    'editor.fx.sensor.sar': 'SAR',
    // R2-B Lot 1
    'editor.shapes.title': 'SHAPES',
    'editor.shapes.ellipse': 'ELLIPSE',
    'editor.shapes.ellipse.tooltip': 'Add ellipse',
    'editor.shapes.rect': 'RECT',
    'editor.shapes.rect.tooltip': 'Add rectangle',
    'editor.shapes.poly': 'POLY',
    'editor.shapes.poly.tooltip': 'Add polygon',
    'editor.shapes.arrow': 'ARROW',
    'editor.shapes.arrow.tooltip': 'Add arrow',
    'editor.shapes.bracket': 'BRACKET',
    'editor.shapes.bracket.tooltip': 'Add bracket',
    'editor.shapes.remove.aria': 'Remove shape',
    'editor.shapes.poly.addpt': 'point',
    'editor.shapes.poly.close': 'close',
    'editor.shapes.poly.open': 'open',
    // R2-A
    'editor.cartouche.amorce': 'Leader',
    'editor.cartouche.amorce.tooltip': 'Link a photo point with a leader line',
    'editor.cartouche.amorce.aria': 'Toggle leader line',
    'editor.inset.add': '+ ADD MAGNIFIER',
    'editor.inset.label': 'MAGNIFIER',
    'editor.inset.remove.aria': 'Remove magnifier',
    'editor.inset.caption': 'CAPTION',
    'editor.inset.caption.ph': 'Optional label…',
    'inset.color.white': 'WHITE',
    'inset.color.black': 'BLACK',
    'inset.color.red': 'RED',
    // R2-B Lot 2
    'editor.label.add': '+ LABEL',
    'editor.label.add.tooltip': 'Add a label',
    'editor.label.text.ph': 'Text…',
    'editor.label.style': 'STYLE',
    'editor.label.style.stamp': 'STAMP',
    'editor.label.style.cursive': 'CURSIVE',
    'editor.label.style.plain': 'PLAIN',
    'editor.label.remove.aria': 'Remove label',
    'editor.classif.title': 'CLASSIFICATION',
    'editor.classif.enable': 'Enable banner',
    'editor.classif.level': 'LEVEL',
  }}
}};

let CURRENT_LANG = 'fr';

function t(key, fallback) {{
  const dict = I18N[CURRENT_LANG] || I18N.fr;
  if (key in dict) return dict[key];
  if (fallback !== undefined) return fallback;
  if (key in I18N.fr) return I18N.fr[key];
  console.warn('[i18n] missing key:', key);
  return key;
}}

// ── State ─────────────────────────────────────────────────────
const KEY_STATE = 'recon_state_v1';
const KEY_THEME = 'theme_v1';
const KEY_LANG  = 'lang_v1';

let STATE = {{
  fields: {{
    target: '', coords: '', crs: '', alt: '',
    msn: '', sensor: '', dtg: '', crew: '', class_: ''
  }},
  cartouche: [],
  logos: [],          // [{{ id, name, b64(dataURL) }}] — logos utilisateur
  logoId: 'none',     // id dans STATE.logos ou 'none'
  contrast: 105,
  logoMode: 'gray',    // 'color' | 'gray' | 'white'  (défaut Gris)
  textColor: '#fff',   // '#fff' | '#000'
  markerColor: 'red',  // 'red' | 'black' | 'white'
  fxVignette: 0,       // 0..100
  fxGrain: 0,          // 0..100
  fxScanlines: 0,      // 0..100
  sensorMode: 'eo',    // R2-C : 'eo' | 'ir-white' | 'ir-black' | 'sar'
  annotations: [],     // R2-A : insets (loupes)
  classification: {{ enabled: false, level: 'UNCLASSIFIED' }},  // R2-B Lot 2
}};

// Source image — non persistée
let SOURCE_IMG   = null;   // HTMLImageElement chargée
let SOURCE_READY = false;
const LOGO_CACHE = {{}};    // id → HTMLImageElement déjà chargée
let RENDER_TOKEN = 0;      // garde-fou de concurrence

// ── uid() helper ────────────────────────────────────────────
function uid() {{ return 'l' + Date.now().toString(36) + Math.random().toString(36).slice(2,6); }}


// ── Roboto Mono FontFace registration ─────────────────────────
// On enregistre la FontFace manuellement pour que canvas 2D la trouve
const ROBOTO_MONO_B64 = '{A["ROBOTO_MONO_400"]}';
const CAVEAT_B64 = '{A["CAVEAT_400"]}';
let fontsReady = false;
let fontsReadyPromise = null;

async function ensureFonts() {{
  if (fontsReady) return;
  if (!fontsReadyPromise) {{
    const ff400 = new FontFace('Roboto Mono',
      `url(data:font/woff2;base64,${{ROBOTO_MONO_B64}})`,
      {{ weight: '400', style: 'normal' }}
    );
    const ff700 = new FontFace('Roboto Mono',
      `url(data:font/woff2;base64,${{ROBOTO_MONO_B64}})`,
      {{ weight: '700', style: 'normal' }}
    );
    const ffCaveat = new FontFace('Caveat',
      `url(data:font/woff2;base64,${{CAVEAT_B64}})`,
      {{ weight: '400', style: 'normal' }}
    );
    fontsReadyPromise = Promise.all([ff400.load(), ff700.load(), ffCaveat.load()]).then(faces => {{
      faces.forEach(f => document.fonts.add(f));
      return document.fonts.ready;
    }}).then(() => {{
      fontsReady = true;
    }});
  }}
  return fontsReadyPromise;
}}

// ── Toast ──────────────────────────────────────────────────────
function showToast(msg, type='', duration=2800) {{
  const tc = document.getElementById('toast-container');
  const el = document.createElement('div');
  el.className = 'toast' + (type ? ' ' + type : '');
  el.textContent = msg;
  tc.appendChild(el);
  requestAnimationFrame(() => {{
    requestAnimationFrame(() => {{ el.classList.add('show'); }});
  }});
  setTimeout(() => {{
    el.classList.remove('show');
    setTimeout(() => el.remove(), 400);
  }}, duration);
}}

// ── Theme ──────────────────────────────────────────────────────
function loadTheme() {{
  const saved = localStorage.getItem(KEY_THEME) || 'cw-nato';
  document.body.setAttribute('data-theme', saved);
  const sel = document.getElementById('theme-select');
  if (sel) sel.value = saved;
}}

function applyTheme(val) {{
  document.body.setAttribute('data-theme', val);
  localStorage.setItem(KEY_THEME, val);
  showToast(t('toast.theme'), 'ok', 1600);
}}

// ── Lang ───────────────────────────────────────────────────────
function loadLang() {{
  const saved = localStorage.getItem(KEY_LANG);
  if (saved === 'fr' || saved === 'en') {{
    CURRENT_LANG = saved;
  }} else {{
    CURRENT_LANG = (navigator.language || 'fr').startsWith('fr') ? 'fr' : 'en';
  }}
  applyI18nStatic();
  updateFlagButton();
  document.documentElement.lang = CURRENT_LANG;
}}

function setLang(lang) {{
  CURRENT_LANG = lang;
  localStorage.setItem(KEY_LANG, lang);
  document.documentElement.lang = lang;
  applyI18nStatic();
  rerenderDynamic();
  updateFlagButton();
  schedulePreview();
  showToast(t('toast.lang'), 'ok', 1800);
}}

function updateFlagButton() {{
  const btn = document.getElementById('btn-lang');
  if (!btn) return;
  btn.textContent = CURRENT_LANG === 'fr' ? '🇬🇧' : '🇫🇷';
  btn.title = t('toolbar.lang.tooltip');
}}

function applyI18nStatic() {{
  document.querySelectorAll('[data-i18n]').forEach(el => {{
    el.textContent = t(el.dataset.i18n);
  }});
  document.querySelectorAll('[data-i18n-title]').forEach(el => {{
    el.title = t(el.dataset.i18nTitle);
  }});
  document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {{
    el.placeholder = t(el.dataset.i18nPlaceholder);
  }});
  document.querySelectorAll('[data-i18n-aria-label]').forEach(el => {{
    el.setAttribute('aria-label', t(el.dataset.i18nAriaLabel));
  }});
}}

function rerenderDynamic() {{
  renderCartoucheEditor();
  renderInsetEditor();
  renderShapesEditor();
  renderLabelEditor();
  renderLogoMode();
  renderTextColor();
  renderMarkerColor();
  // Le logo grid n'a pas de texte i18n (logos visuels)
}}

// ── State persistence ──────────────────────────────────────────
function collectState() {{
  STATE.fields.target  = document.getElementById('f-target').value;
  STATE.fields.coords  = document.getElementById('f-coords').value;
  STATE.fields.crs     = document.getElementById('f-crs').value;
  STATE.fields.alt     = document.getElementById('f-alt').value;
  STATE.fields.msn     = document.getElementById('f-msn').value;
  STATE.fields.sensor  = document.getElementById('f-sensor').value;
  STATE.fields.dtg     = document.getElementById('f-dtg').value;
  STATE.fields.crew    = document.getElementById('f-crew').value;
  STATE.fields.class_  = document.getElementById('f-class').value;
  STATE.contrast       = parseInt(document.getElementById('contrast-slider').value, 10) || 105;
  STATE.fxVignette  = parseInt(document.getElementById('fx-vignette').value,  10) || 0;
  STATE.fxGrain     = parseInt(document.getElementById('fx-grain').value,     10) || 0;
  STATE.fxScanlines = parseInt(document.getElementById('fx-scanlines').value, 10) || 0;
  STATE.sensorMode  = document.getElementById('sensor-mode').value || 'eo';
}}

function saveState() {{
  collectState();
  try {{
    const toSave = Object.assign({{}}, STATE, {{ schema: 2 }});
    localStorage.setItem(KEY_STATE, JSON.stringify(toSave));
  }} catch(e) {{}}
}}

function restoreState() {{
  const raw = localStorage.getItem(KEY_STATE);
  if (!raw) return false;
  try {{
    const saved = JSON.parse(raw);
    if (saved.fields)    STATE.fields    = {{ ...STATE.fields, ...saved.fields }};
    if (saved.cartouche) STATE.cartouche = saved.cartouche;
    // B2 migration : entrées v1.0.0 sans x/y → point:false (pas de marqueur surprise)
    STATE.cartouche.forEach(e => {{
      if (typeof e.x !== 'number') {{ e.x = 0.5; e.y = 0.5; e.point = false; }}
    }});
    // G1 migration : ancien logoCustom → STATE.logos
    if (Array.isArray(saved.logos)) STATE.logos = saved.logos;
    else if (saved.logoCustom) STATE.logos.push({{ id: uid(), name: 'IMPORT', b64: saved.logoCustom }});
    if ('logoId' in saved) STATE.logoId = saved.logoId;
    // Vérifier que logoId existe encore dans STATE.logos
    if (STATE.logoId !== 'none' && !STATE.logos.find(l => l.id === STATE.logoId)) STATE.logoId = 'none';
    if ('contrast' in saved) STATE.contrast = saved.contrast;
    if ('logoMode'    in saved) STATE.logoMode    = saved.logoMode;
    if ('fxVignette'  in saved) STATE.fxVignette  = saved.fxVignette;
    if ('fxGrain'     in saved) STATE.fxGrain     = saved.fxGrain;
    if ('fxScanlines'  in saved) STATE.fxScanlines  = saved.fxScanlines;
    if ('textColor'    in saved) STATE.textColor    = saved.textColor;
    if ('markerColor'  in saved) STATE.markerColor  = saved.markerColor;
    // R2-C : sensorMode (absent → 'eo')
    STATE.sensorMode = ['eo','ir-white','ir-black','sar'].includes(saved.sensorMode)
      ? saved.sensorMode : 'eo';
    // R2-A migration
    STATE.annotations = Array.isArray(saved.annotations) ? saved.annotations : [];
    STATE.annotations.forEach(a => {{ if (!a.id) a.id = uid(); }});
    // R2-B Lot 2 : classification (champ absent → défaut)
    if (saved.classification && typeof saved.classification === 'object') {{
      STATE.classification = {{ enabled: !!saved.classification.enabled, level: saved.classification.level || 'UNCLASSIFIED' }};
    }}
    return true;
  }} catch(e) {{ return false; }}
}}

function applyStateToForm() {{
  const f = STATE.fields;
  document.getElementById('f-target').value = f.target  || '';
  document.getElementById('f-coords').value = f.coords  || '';
  document.getElementById('f-crs').value    = f.crs     || '';
  document.getElementById('f-alt').value    = f.alt     || '';
  document.getElementById('f-msn').value    = f.msn     || '';
  document.getElementById('f-sensor').value = f.sensor  || '';
  document.getElementById('f-dtg').value    = f.dtg     || '';
  document.getElementById('f-crew').value   = f.crew    || '';
  document.getElementById('f-class').value  = f.class_  || '';
  const cSlider = document.getElementById('contrast-slider');
  cSlider.value = STATE.contrast;
  document.getElementById('contrast-val').textContent = STATE.contrast + '%';
  const fxSliders = [['fx-vignette','fxVignette'],['fx-grain','fxGrain'],['fx-scanlines','fxScanlines']];
  fxSliders.forEach(([id, key]) => {{
    const sl = document.getElementById(id);
    if (sl) {{ sl.value = STATE[key] || 0; document.getElementById(id+'-val').textContent = STATE[key] || 0; }}
  }});
  const smSel = document.getElementById('sensor-mode');
  if (smSel) smSel.value = STATE.sensorMode || 'eo';
}}

// ── Source image loading ───────────────────────────────────────
function loadImageFile(file) {{
  if (!file || !file.type.startsWith('image/')) return;
  const reader = new FileReader();
  reader.onload = async e => {{
    const img = new Image();
    img.onload = () => {{
      SOURCE_IMG   = img;
      SOURCE_READY = true;
      document.getElementById('drop-zone').classList.add('has-image');
      document.getElementById('drop-zone-text').textContent =
        file.name + ' — ' + img.naturalWidth + '×' + img.naturalHeight + 'px';
      document.getElementById('btn-export').disabled = false;
      document.getElementById('preview-placeholder').hidden = true;
      document.getElementById('preview-canvas').hidden = false;
      showToast(t('toast.image-loaded'), 'ok', 1800);
      schedulePreview();
    }};
    img.src = e.target.result;
  }};
  reader.readAsDataURL(file);
}}

// ── Logo loading ───────────────────────────────────────────────
const LOGO_MAX_SIZE = 512;   // côté long — préserve les exports haute résolution

function loadLogoFile(file) {{
  if (!file) return;
  if (!file.type.startsWith('image/')) {{ showToast(t('toast.fileMustBeImage'), 'err'); return; }}
  const reader = new FileReader();
  reader.onload = e => {{
    const img = new Image();
    img.onload = () => {{
      let {{ naturalWidth: w, naturalHeight: h }} = img;
      // Réduction proportionnelle — jamais de carré forcé, alpha conservé
      if (w > LOGO_MAX_SIZE || h > LOGO_MAX_SIZE) {{
        if (w >= h) {{ h = Math.round(h * LOGO_MAX_SIZE / w); w = LOGO_MAX_SIZE; }}
        else        {{ w = Math.round(w * LOGO_MAX_SIZE / h); h = LOGO_MAX_SIZE; }}
      }}
      const tmp = document.createElement('canvas');
      tmp.width = w; tmp.height = h;
      const tc = tmp.getContext('2d');
      tc.drawImage(img, 0, 0, w, h);   // pas de fond → alpha conservé
      const newLogo = {{ id: uid(), name: 'IMPORT', b64: tmp.toDataURL('image/png') }};
      STATE.logos.push(newLogo);
      STATE.logoId = newLogo.id;
      saveState();
      renderLogoGrid();
      schedulePreview();
    }};
    img.onerror = () => showToast(t('toast.logoInvalid'), 'err');
    img.src = e.target.result;
  }};
  reader.readAsDataURL(file);
}}

// ── Import config wing BG (G2) ────────────────────────────────
function importWingLogos(file) {{
  const r = new FileReader();
  r.onload = e => {{
    let cfg;
    try {{ cfg = JSON.parse(e.target.result); }}
    catch (_) {{ showToast(t('toast.jsonInvalid'), 'err'); return; }}
    const added = [];
    const push = (name, b64) => {{
      if (typeof b64 === 'string' && b64.startsWith('data:image/'))
        added.push({{ id: uid(), name: String(name || 'LOGO').slice(0, 24), b64 }});
    }};
    if (cfg.wing) push(cfg.wing.shortName || 'WING', cfg.wing.logo);
    (cfg.squadrons || []).forEach(sq => push(sq.id, sq.logo));
    if (!added.length) {{ showToast(t('toast.noLogoInJson'), 'err'); return; }}
    STATE.logos.push(...added);
    STATE.logoId = added[0].id;
    saveState(); renderLogoGrid(); schedulePreview();
    showToast(t('toast.logosImported').replace('{{n}}', added.length), 'ok');
  }};
  r.readAsText(file);
}}

// ── Logo grid render ───────────────────────────────────────────
function renderLogoGrid() {{
  const grid = document.getElementById('logo-grid');
  if (!grid) return;
  // Construire depuis NONE + STATE.logos (G3)
  const allLogos = [{{ id: 'none', name: 'NONE', b64: null }}, ...STATE.logos];

  grid.innerHTML = allLogos.map(lg => {{
    const active = STATE.logoId === lg.id ? 'active' : '';
    if (lg.id === 'none') {{
      return `<div class="logo-thumb ${{active}}" data-logo-id="none" tabindex="0" title="Aucun logo">
        <div class="logo-thumb-none">∅</div>
      </div>`;
    }}
    // Logos utilisateur : ✕ toujours visible (tactile)
    const src = lg.b64 || '';
    return `<div class="logo-thumb logo-thumb-custom ${{active}}" data-logo-id="${{lg.id}}" tabindex="0" title="${{lg.name}}">
      ${{src ? `<img src="${{src}}" alt="${{lg.name}}">` : '<div class="logo-thumb-none">?</div>'}}
      <button class="logo-thumb-del" data-del-id="${{lg.id}}"
              title="${{t('editor.logo.removeCustom')}}" aria-label="${{t('editor.logo.removeCustom')}}">✕</button>
    </div>`;
  }}).join('');

  // Sélection
  grid.querySelectorAll('.logo-thumb').forEach(el => {{
    el.addEventListener('click', ev => {{
      if (ev.target.closest('.logo-thumb-del')) return;
      STATE.logoId = el.dataset.logoId || 'none';
      saveState();
      renderLogoGrid();
      schedulePreview();
    }});
    el.addEventListener('keydown', e => {{
      if (e.key === 'Enter' || e.key === ' ') {{ e.preventDefault(); el.click(); }}
    }});
  }});

  // Suppression (G3)
  grid.querySelectorAll('.logo-thumb-del').forEach(btn => {{
    btn.addEventListener('click', ev => {{
      ev.stopPropagation();
      const delId = btn.dataset.delId;
      STATE.logos = STATE.logos.filter(l => l.id !== delId);
      if (STATE.logoId === delId) STATE.logoId = 'none';
      saveState();
      renderLogoGrid();
      schedulePreview();
    }});
  }});
}}

// ── Logo mode render ───────────────────────────────────────────
function renderLogoMode() {{
  const group = document.getElementById('logo-mode');
  if (!group) return;
  group.querySelectorAll('button').forEach(btn => {{
    btn.classList.toggle('active', btn.dataset.logoMode === (STATE.logoMode || 'gray'));
  }});
}}

// ── Text color render ─────────────────────────────────────────
function renderTextColor() {{
  const group = document.getElementById('text-color-group');
  if (!group) return;
  group.querySelectorAll('button').forEach(btn => {{
    btn.classList.toggle('active', btn.dataset.textColor === (STATE.textColor || '#fff'));
  }});
}}

// ── Marker color render ────────────────────────────────────────
function renderMarkerColor() {{
  const group = document.getElementById('marker-color-group');
  if (!group) return;
  group.querySelectorAll('button').forEach(btn => {{
    btn.classList.toggle('active', btn.dataset.markerColor === (STATE.markerColor || 'red'));
  }});
}}

// ── Cartouche editor render ────────────────────────────────────
function renderCartoucheEditor() {{
  const container = document.getElementById('cartouche-editor');
  if (!container) return;
  container.innerHTML = STATE.cartouche.map((row, i) => `
    <div class="cartouche-row">
      <div class="cartouche-num">${{i + 1}}</div>
      <input class="ed-input cartouche-label-input" type="text"
             data-idx="${{i}}"
             placeholder="${{t('editor.cartouche.label.ph')}}"
             value="${{escapeAttr(row.label)}}">
      <label class="cartouche-point-toggle" title="${{t('editor.cartouche.point')}}">
        <input type="checkbox" class="cartouche-point-cb" data-idx="${{i}}"
               ${{row.point !== false ? 'checked' : ''}}>
        <span class="point-marker">◎</span>
      </label>
      <button class="btn-remove-row" data-idx="${{i}}"
              aria-label="${{t('editor.cartouche.remove.aria')}}" title="✕">✕</button>
    </div>
    ${{row.point !== false ? `<div class="amorce-row">
      <label class="amorce-toggle" title="${{t('editor.cartouche.amorce.tooltip')}}">
        <input type="checkbox" class="amorce-cb" data-idx="${{i}}"
               ${{row.target ? 'checked' : ''}}>
        <span class="amorce-marker">⤵ ${{t('editor.cartouche.amorce')}}</span>
      </label>
    </div>` : ''}}
  `).join('');

  container.querySelectorAll('.cartouche-label-input').forEach(inp => {{
    inp.addEventListener('input', () => {{
      STATE.cartouche[parseInt(inp.dataset.idx, 10)].label = inp.value;
      saveState();
      schedulePreview();
    }});
  }});
  container.querySelectorAll('.cartouche-point-cb').forEach(cb => {{
    cb.addEventListener('change', () => {{
      const e = STATE.cartouche[parseInt(cb.dataset.idx, 10)];
      if (typeof e.x !== 'number') {{ e.x = 0.5; e.y = 0.5; }}
      e.point = cb.checked;
      saveState();
      schedulePreview();
    }});
  }});
  container.querySelectorAll('.btn-remove-row').forEach(btn => {{
    btn.addEventListener('click', () => {{
      const idx = parseInt(btn.dataset.idx, 10);
      STATE.cartouche.splice(idx, 1);
      if (STATE.cartouche.length === 0) STATE.cartouche.push({{ label: '', x: 0.5, y: 0.5, point: false }});
      saveState();
      renderCartoucheEditor();
      schedulePreview();
    }});
  }});
  // R2-A toggle amorce
  container.querySelectorAll('.amorce-cb').forEach(cb => {{
    cb.addEventListener('change', () => {{
      const e = STATE.cartouche[parseInt(cb.dataset.idx, 10)];
      if (cb.checked) {{
        if (!e.target) e.target = {{
          x: Math.min(0.95, (e.x || 0.5) + 0.08),
          y: Math.min(0.95, (e.y || 0.5) + 0.08)
        }};
      }} else {{
        delete e.target;
      }}
      saveState();
      schedulePreview();
    }});
  }});
}}

// ── Inset editor (R2-A) ──────────────────────────────────────
function renderInsetEditor() {{
  const container = document.getElementById('inset-editor');
  if (!container) return;
  const insets = (STATE.annotations || []).filter(a => a.type === 'inset');
  if (insets.length === 0) {{ container.innerHTML = ''; return; }}
  container.innerHTML = insets.map((ins, i) => {{
    const colBtns = ['white','black','red'].map(c =>
      `<button type="button" class="inset-color-btn${{ins.color===c?' active':''}}" data-inset-id="${{ins.id}}" data-color="${{c}}">${{t('inset.color.'+c)}}</button>`
    ).join('');
    return `<div class="inset-row">
      <div class="inset-row-header">
        <span class="inset-num">⊞ ${{t('editor.inset.label')}} ${{i+1}}</span>
        <div class="inset-color-group">${{colBtns}}</div>
        <button class="btn-remove-row btn-remove-inset" data-inset-id="${{ins.id}}"
                aria-label="${{t('editor.inset.remove.aria')}}" title="✕">✕</button>
      </div>
      <div class="inset-label-row">
        <span class="ed-label" style="min-width:44px">${{t('editor.inset.caption')}}</span>
        <input class="inset-label-input" type="text"
               data-inset-id="${{ins.id}}"
               placeholder="${{t('editor.inset.caption.ph')}}"
               value="${{escapeAttr(ins.label || '')}}">
      </div>
    </div>`;
  }}).join('');
  container.querySelectorAll('.btn-remove-inset').forEach(btn => {{
    btn.addEventListener('click', () => {{
      STATE.annotations = STATE.annotations.filter(a => a.id !== btn.dataset.insetId);
      saveState(); renderInsetEditor(); schedulePreview();
    }});
  }});
  container.querySelectorAll('.inset-color-btn').forEach(btn => {{
    btn.addEventListener('click', () => {{
      const ins = STATE.annotations.find(a => a.id === btn.dataset.insetId);
      if (ins) {{ ins.color = btn.dataset.color; saveState(); renderInsetEditor(); schedulePreview(); }}
    }});
  }});
  container.querySelectorAll('.inset-label-input').forEach(inp => {{
    inp.addEventListener('input', () => {{
      const ins = STATE.annotations.find(a => a.id === inp.dataset.insetId);
      if (ins) {{ ins.label = inp.value; saveState(); schedulePreview(); }}
    }});
  }});
}}

// ── Shapes editor (R2-B Lot 1) ───────────────────────────────
function renderShapesEditor() {{
  const container = document.getElementById('shapes-editor');
  if (!container) return;
  const shapes = (STATE.annotations || []).filter(a =>
    ['ellipse','rect','poly','arrow','bracket'].includes(a.type));
  if (shapes.length === 0) {{ container.innerHTML = ''; return; }}

  const TYPE_LABELS = {{
    ellipse: t('editor.shapes.ellipse'), rect: t('editor.shapes.rect'),
    poly: t('editor.shapes.poly'), arrow: t('editor.shapes.arrow'),
    bracket: t('editor.shapes.bracket')
  }};

  container.innerHTML = shapes.map((sh, i) => {{
    const colBtns = ['red','black','white'].map(c =>
      `<button type="button" class="shape-color-btn${{sh.color===c?' active':''}}"
               data-shape-id="${{sh.id}}" data-color="${{c}}">${{t('inset.color.'+c)}}</button>`
    ).join('');
    const polyExtra = sh.type === 'poly' ? `
      <div class="shape-poly-controls">
        <button class="shape-poly-btn" data-shape-id="${{sh.id}}" data-action="add-pt">+ ${{t('editor.shapes.poly.addpt')}}</button>
        <button class="shape-poly-btn${{sh.closed?' active':''}}" data-shape-id="${{sh.id}}" data-action="toggle-close">${{sh.closed ? t('editor.shapes.poly.open') : t('editor.shapes.poly.close')}}</button>
      </div>` : '';
    return `<div class="shape-row">
      <div class="shape-row-header">
        <span class="shape-badge">${{TYPE_LABELS[sh.type] || sh.type}} ${{i+1}}</span>
        <div class="shape-color-group">${{colBtns}}</div>
        <button class="btn-remove-row btn-remove-shape" data-shape-id="${{sh.id}}"
                aria-label="${{t('editor.shapes.remove.aria')}}" title="✕">✕</button>
      </div>
      ${{polyExtra}}
    </div>`;
  }}).join('');

  container.querySelectorAll('.btn-remove-shape').forEach(btn => {{
    btn.addEventListener('click', () => {{
      STATE.annotations = STATE.annotations.filter(a => a.id !== btn.dataset.shapeId);
      saveState(); renderShapesEditor(); schedulePreview();
    }});
  }});
  container.querySelectorAll('.shape-color-btn').forEach(btn => {{
    btn.addEventListener('click', () => {{
      const sh = STATE.annotations.find(a => a.id === btn.dataset.shapeId);
      if (sh) {{ sh.color = btn.dataset.color; saveState(); renderShapesEditor(); schedulePreview(); }}
    }});
  }});
  container.querySelectorAll('[data-action="add-pt"]').forEach(btn => {{
    btn.addEventListener('click', () => {{
      const sh = STATE.annotations.find(a => a.id === btn.dataset.shapeId);
      if (sh && sh.pts) {{
        const last = sh.pts[sh.pts.length-1];
        sh.pts.push({{ x: Math.min(0.95, last.x+0.04), y: Math.min(0.95, last.y+0.04) }});
        saveState(); renderShapesEditor(); schedulePreview();
      }}
    }});
  }});
  container.querySelectorAll('[data-action="toggle-close"]').forEach(btn => {{
    btn.addEventListener('click', () => {{
      const sh = STATE.annotations.find(a => a.id === btn.dataset.shapeId);
      if (sh) {{ sh.closed = !sh.closed; saveState(); renderShapesEditor(); schedulePreview(); }}
    }});
  }});
}}

// ── Escape helpers ─────────────────────────────────────────────
function escapeAttr(str) {{
  return (str || '').replace(/&/g,'&amp;').replace(/"/g,'&quot;').replace(/'/g,'&#39;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}}

// ── renderLabelEditor (R2-B Lot 2) ────────────────────────────
function renderLabelEditor() {{
  const container = document.getElementById('label-editor');
  if (!container) return;
  const labels2 = (STATE.annotations || []).filter(a => a.type === 'label');
  if (labels2.length === 0) {{ container.innerHTML = ''; return; }}

  container.innerHTML = labels2.map((lb, i) => {{
    const styleBtns = ['stamp','cursive','plain'].map(st2 =>
      `<button type="button" class="shape-color-btn${{lb.style===st2?' active':''}}"
               data-label-id="${{lb.id}}" data-style="${{st2}}">${{t('editor.label.style.'+st2)}}</button>`
    ).join('');
    const colBtns = ['red','black','white'].map(c =>
      `<button type="button" class="shape-color-btn${{lb.color===c?' active':''}}"
               data-label-id="${{lb.id}}" data-label-color="${{c}}">${{t('inset.color.'+c)}}</button>`
    ).join('');
    return `<div class="shape-row">
      <div class="shape-row-header">
        <span class="shape-badge">LABEL ${{i+1}}</span>
        <button class="btn-remove-row btn-remove-label" data-label-id="${{lb.id}}"
                aria-label="${{t('editor.label.remove.aria')}}" title="✕">✕</button>
      </div>
      <input type="text" class="label-text-input ed-input" data-label-id="${{lb.id}}"
             value="${{escapeAttr(lb.text)}}" placeholder="${{escapeAttr(t('editor.label.text.ph'))}}">
      <div class="shape-color-group" style="margin-top:4px">${{styleBtns}}</div>
      <div class="shape-color-group" style="margin-top:4px">${{colBtns}}</div>
    </div>`;
  }}).join('');

  container.querySelectorAll('.btn-remove-label').forEach(btn => {{
    btn.addEventListener('click', () => {{
      STATE.annotations = STATE.annotations.filter(a => a.id !== btn.dataset.labelId);
      saveState(); renderLabelEditor(); schedulePreview();
    }});
  }});
  container.querySelectorAll('.label-text-input').forEach(inp => {{
    inp.addEventListener('input', () => {{
      const lb = STATE.annotations.find(a => a.id === inp.dataset.labelId);
      if (lb) {{ lb.text = inp.value; saveState(); schedulePreview(); }}
    }});
  }});
  container.querySelectorAll('[data-style]').forEach(btn => {{
    btn.addEventListener('click', () => {{
      const lb = STATE.annotations.find(a => a.id === btn.dataset.labelId);
      if (lb) {{ lb.style = btn.dataset.style; saveState(); renderLabelEditor(); schedulePreview(); }}
    }});
  }});
  container.querySelectorAll('[data-label-color]').forEach(btn => {{
    btn.addEventListener('click', () => {{
      const lb = STATE.annotations.find(a => a.id === btn.dataset.labelId);
      if (lb) {{ lb.color = btn.dataset.labelColor; saveState(); renderLabelEditor(); schedulePreview(); }}
    }});
  }});
}}

// ── Fonctions effets photo (D3) ───────────────────────────────────

function applyVignette(ctx, W, H, a) {{
  if (a <= 0) return;
  const g = ctx.createRadialGradient(W/2, H/2, Math.min(W,H)*0.35,
                                     W/2, H/2, Math.max(W,H)*0.78);
  g.addColorStop(0, 'rgba(0,0,0,0)');
  g.addColorStop(1, `rgba(0,0,0,${{0.85*a}})`);
  ctx.save(); ctx.fillStyle = g; ctx.fillRect(0,0,W,H); ctx.restore();
}}

function noiseTile() {{
  const n = document.createElement('canvas'); n.width = n.height = 128;
  const nc = n.getContext('2d'); const id = nc.createImageData(128,128);
  for (let i=0; i<id.data.length; i+=4) {{
    const v = Math.random()*255;
    id.data[i]=id.data[i+1]=id.data[i+2]=v; id.data[i+3]=255;
  }}
  nc.putImageData(id,0,0); return n;
}}
function applyGrain(ctx, W, H, a) {{
  if (a <= 0) return;
  ctx.save();
  ctx.globalCompositeOperation = 'overlay';
  ctx.globalAlpha = 0.35 * a;
  const pat = ctx.createPattern(noiseTile(), 'repeat');
  if (pat && pat.setTransform && typeof DOMMatrix !== 'undefined') {{
    pat.setTransform(new DOMMatrix([2, 0, 0, 2, 0, 0]));  // grain ~2× plus gros
  }}
  ctx.fillStyle = pat;
  ctx.fillRect(0, 0, W, H);
  ctx.restore();
}}
function applyScanlines(ctx, W, H, a) {{
  if (a <= 0) return;
  ctx.save();
  ctx.globalAlpha = 0.30 * a; ctx.fillStyle = '#000';
  const step = Math.max(2, Math.round(H/540)*2);
  for (let y=0; y<H; y+=step*2) ctx.fillRect(0, y, W, step);
  ctx.restore();
}}

// ── R2-C : preset capteur (appliqué sur le base offscreen) ─────
function applySensorPreset(ctx, W, H, mode) {{
  if (!mode || mode === 'eo') return;

  const id = ctx.getImageData(0, 0, W, H);
  const d  = id.data;

  if (mode === 'ir-white' || mode === 'ir-black') {{
    // Courbe en S (crush tonal) : accentue noirs + hautes lumières
    const lut = new Uint8Array(256);
    for (let i = 0; i < 256; i++) {{
      // Normalise en [0,1], applique S-curve, remet en [0,255]
      const t = i / 255;
      // Courbe S douce : f(t) = t² * (3 − 2t) * 1.1 clampé
      const s2 = t * t * (3 - 2 * t);
      // Boost léger des hautes lumières, crush des basses
      lut[i] = Math.min(255, Math.round(
        (s2 * 1.15 - 0.05) * 255
      ));
      if (lut[i] < 0) lut[i] = 0;
    }}
    for (let i = 0; i < d.length; i += 4) {{
      let v = lut[d[i]];
      if (mode === 'ir-black') v = 255 - v;
      d[i] = d[i+1] = d[i+2] = v;
    }}
    ctx.putImageData(id, 0, 0);

    // Bloom léger sur hautes lumières (offscreen temp, jamais caché)
    if (mode === 'ir-white') {{
      const bloom = document.createElement('canvas');
      bloom.width = W; bloom.height = H;
      const bc = bloom.getContext('2d');
      bc.drawImage(ctx.canvas, 0, 0);
      // Isoler seulement les zones claires (threshold ~180)
      const bid = bc.getImageData(0, 0, W, H);
      const bd = bid.data;
      for (let i = 0; i < bd.length; i += 4) {{
        const v = bd[i];
        const alpha = v > 160 ? Math.round((v - 160) / 95 * 200) : 0;
        bd[i+3] = alpha;
      }}
      bc.putImageData(bid, 0, 0);
      // Flou + composite lighten
      ctx.save();
      ctx.filter = `blur(${{Math.max(2, Math.round(W / 320))}}px)`;
      ctx.globalCompositeOperation = 'lighten';
      ctx.globalAlpha = 0.55;
      ctx.drawImage(bloom, 0, 0);
      ctx.restore();
    }}

  }} else if (mode === 'sar') {{
    // Contraste élevé (écrase les mi-tons)
    const lut2 = new Uint8Array(256);
    for (let i = 0; i < 256; i++) {{
      const t = (i - 128) * 2.2 + 128;
      lut2[i] = Math.max(0, Math.min(255, Math.round(t)));
    }}
    for (let i = 0; i < d.length; i += 4) {{
      const v = lut2[d[i]];
      d[i] = d[i+1] = d[i+2] = v;
    }}
    ctx.putImageData(id, 0, 0);

    // Speckle multiplicatif via tuile de bruit temporaire (sans cache permanent)
    const tSz = 128;
    const spk = document.createElement('canvas');
    spk.width = tSz; spk.height = tSz;
    const sc = spk.getContext('2d');
    const sid = sc.createImageData(tSz, tSz);
    const sd = sid.data;
    for (let i = 0; i < sd.length; i += 4) {{
      // Bruit multiplicatif : centré sur 128 (neutre × 1), écart-type ~40
      const n = Math.max(0, Math.min(255, Math.round(
        128 + (Math.random() + Math.random() + Math.random() - 1.5) * 55
      )));
      sd[i] = sd[i+1] = sd[i+2] = n;
      sd[i+3] = 255;
    }}
    sc.putImageData(sid, 0, 0);
    // Répéter la tuile sur toute l'image en composite 'multiply'
    ctx.save();
    ctx.globalCompositeOperation = 'multiply';
    ctx.globalAlpha = 0.70;
    const pat = ctx.createPattern(spk, 'repeat');
    if (pat) {{ ctx.fillStyle = pat; ctx.fillRect(0, 0, W, H); }}
    ctx.restore();
  }}
}}

// ── Canvas composition ─────────────────────────────────────────
// composeRecon(ctx, W, H, state, logoImg, sourceImg)
// Tous les offsets / tailles sont en pixels du canvas natif

function composeRecon(ctx, W, H, st, logoImg) {{
  if (!SOURCE_IMG) return;

  const contrast = st.contrast || 105;

  // Facteur d'échelle base : W = 1920 de référence
  const scale = W / 1920;
  const s = v => Math.round(v * scale);

  // ── Offscreen base : image traitée (gris + contraste + effets) ──
  const base = document.createElement('canvas');
  base.width = W; base.height = H;
  const bctx = base.getContext('2d');
  bctx.filter = `grayscale(1) contrast(${{contrast}}%)`;
  bctx.drawImage(SOURCE_IMG, 0, 0, W, H);
  bctx.filter = 'none';
  applySensorPreset(bctx, W, H, st.sensorMode || 'eo');
  applyVignette(bctx, W, H, (st.fxVignette   || 0) / 100);
  applyGrain(bctx, W, H,    (st.fxGrain      || 0) / 100);
  applyScanlines(bctx, W, H,(st.fxScanlines  || 0) / 100);
  ctx.drawImage(base, 0, 0);

  // ── Bloc info bas-centre ───────────────────────────────────
  // Fond semi-transparent noir sous le bloc
  const blockH = s(148);
  const bannerH = (st.classification && st.classification.enabled) ? s(30) : 0;
  const blockY = H - blockH - s(12) - bannerH;
  const blockW = W * 0.60;
  const blockX = (W - blockW) / 2;

  // Logo à gauche du bloc
  const logoSize = s(100);
  const logoX = blockX - logoSize - s(24);
  const logoY = blockY + (blockH - logoSize) / 2;

  if (logoImg && logoImg.naturalWidth) {{
    const iw = logoImg.naturalWidth  || logoImg.width;
    const ih = logoImg.naturalHeight || logoImg.height;
    const k  = Math.min(logoSize / iw, logoSize / ih);  // contain → ratio conservé
    const dw = iw * k, dh = ih * k;
    const dx = logoX + (logoSize - dw) / 2;
    const dy = logoY + (logoSize - dh) / 2;
    const mode = st.logoMode || 'gray';

    if (mode === 'white') {{
      // Silhouette blanche via canvas offscreen — source-in préserve alpha
      const off = document.createElement('canvas');
      off.width  = Math.max(1, Math.round(dw));
      off.height = Math.max(1, Math.round(dh));
      const octx = off.getContext('2d');
      octx.drawImage(logoImg, 0, 0, off.width, off.height);
      octx.globalCompositeOperation = 'source-in';
      octx.fillStyle = '#fff';
      octx.fillRect(0, 0, off.width, off.height);
      ctx.drawImage(off, dx, dy, dw, dh);
    }} else if (mode === 'gray') {{
      ctx.save();
      ctx.filter = 'grayscale(1)';
      ctx.drawImage(logoImg, dx, dy, dw, dh);
      ctx.restore();
    }} else {{
      ctx.drawImage(logoImg, dx, dy, dw, dh);
    }}
    // Pas de cercle ni de clip (supprimé C2)
  }}

  // Texte du bloc
  const baseFont = s(28);
  const boldFont = s(26);
  const lineH    = s(34);
  const TXT = st.textColor || '#fff';   // E2 : couleur texte pilotée

  // Largeur des champs de valeur (avec filet de soulignement)
  function drawField(label, value, x, y, fieldW) {{
    // Label gras
    ctx.font = `700 ${{boldFont}}px "Gunplay","Roboto Mono",monospace`;
    ctx.fillStyle = TXT;
    ctx.textBaseline = 'alphabetic';
    const lw = ctx.measureText(label).width;
    ctx.fillText(label, x, y);

    // Valeur gras (E2)
    ctx.font = `700 ${{baseFont}}px "Gunplay","Roboto Mono",monospace`;
    ctx.fillStyle = TXT;
    const valX = x + lw;
    ctx.fillText(value, valX, y);

    // Filet sous la valeur (même largeur que fieldW)
    const lineY = y + s(4);
    ctx.beginPath();
    ctx.moveTo(valX, lineY);
    ctx.lineTo(valX + fieldW, lineY);
    ctx.strokeStyle = TXT;
    ctx.lineWidth = s(1);
    ctx.stroke();
  }}

  const f = st.fields;
  const lx = blockX;  // left margin du bloc
  const colMid = blockX + blockW * 0.52;  // 2e colonne

  // L1 : Target · Coords
  const y1 = blockY + lineH;
  drawField('Target : ', f.target, lx, y1, s(280));
  drawField('Coords: ', f.coords, colMid, y1, s(320));

  // L2 : Crs · Alt · Msn · Sensor
  const y2 = y1 + lineH;
  drawField('Crs: ', f.crs, lx, y2, s(70));
  drawField('Alt: ', f.alt, lx + s(180), y2, s(90));
  drawField('Msn: ', f.msn, lx + s(380), y2, s(220));
  drawField('Sensor : ', f.sensor, colMid + s(60), y2, s(220));

  // L3 : DTG · Crew
  const y3 = y2 + lineH;
  drawField('DTG : ', f.dtg, lx, y3, s(320));
  drawField('Crew: ', f.crew, colMid, y3, s(280));

  // L4 : Class centré
  const y4 = y3 + lineH;
  const classLabel = 'Class: ';
  ctx.font = `700 ${{boldFont}}px "Gunplay","Roboto Mono",monospace`;
  const classLabelW = ctx.measureText(classLabel).width;
  ctx.font = `400 ${{baseFont}}px "Gunplay","Roboto Mono",monospace`;
  const classValW = ctx.measureText(f.class_ || '').width;
  const totalClassW = classLabelW + classValW + s(80);
  const classX = blockX + (blockW - totalClassW) / 2;
  drawField('Class: ', f.class_, classX, y4, s(200));

  // ── Cartouche haut-droite (I1: omis si vide) ─────────────────
  const cartRows = (st.cartouche || []);
  if (cartRows.length > 0) {{
  const cartW  = s(300);
  const cartMg = s(18);
  const cartX  = W - cartW - cartMg;
  const cartY  = cartMg + bannerH;
  const rowH   = s(34);
  const cartH  = rowH * (cartRows.length + 1) + s(4); // +1 header

  // Fond blanc
  ctx.fillStyle = 'rgba(255,255,255,0.94)';
  ctx.fillRect(cartX, cartY, cartW, cartH);

  // Bordure noire
  ctx.strokeStyle = '#000000';
  ctx.lineWidth = s(2);
  ctx.strokeRect(cartX, cartY, cartW, cartH);

  // Header N° | Label
  const hdrFont = s(22);
  ctx.font = `700 ${{hdrFont}}px "Gunplay","Roboto Mono",monospace`;
  ctx.fillStyle = '#000000';
  ctx.textBaseline = 'middle';
  const numColW = s(46);
  ctx.fillText('N°', cartX + s(10), cartY + rowH/2);
  // Séparateur vertical
  ctx.beginPath();
  ctx.moveTo(cartX + numColW, cartY);
  ctx.lineTo(cartX + numColW, cartY + cartH);
  ctx.strokeStyle = '#000000';
  ctx.lineWidth = s(1.5);
  ctx.stroke();
  ctx.fillText('Label', cartX + numColW + s(10), cartY + rowH/2);

  // Ligne séparatrice après header
  ctx.beginPath();
  ctx.moveTo(cartX, cartY + rowH);
  ctx.lineTo(cartX + cartW, cartY + rowH);
  ctx.stroke();

  // Lignes
  const rowFont = s(21);
  ctx.font = `400 ${{rowFont}}px "Gunplay","Roboto Mono",monospace`;
  cartRows.forEach((row, i) => {{
    const ry = cartY + rowH * (i + 1);
    // Fond alternance légère
    if (i % 2 === 0) {{
      ctx.fillStyle = 'rgba(0,0,0,0.04)';
      ctx.fillRect(cartX + s(1), ry, cartW - s(2), rowH - s(1));
    }}
    ctx.fillStyle = '#000000';
    ctx.fillText(String(i + 1), cartX + s(10), ry + rowH/2);
    // Truncate label si trop long
    const maxLabelW = cartW - numColW - s(20);
    let label = row.label || '';
    ctx.font = `400 ${{rowFont}}px "Gunplay","Roboto Mono",monospace`;
    while (label.length > 0 && ctx.measureText(label).width > maxLabelW) {{
      label = label.slice(0, -1);
    }}
    ctx.fillText(label, cartX + numColW + s(10), ry + rowH/2);
    // Ligne séparatrice
    if (i < cartRows.length - 1) {{
      ctx.beginPath();
      ctx.moveTo(cartX, ry + rowH);
      ctx.lineTo(cartX + cartW, ry + rowH);
      ctx.strokeStyle = 'rgba(0,0,0,0.25)';
      ctx.lineWidth = s(0.8);
      ctx.stroke();
    }}
  }});

  }} // fin if cartRows.length > 0

  // ── Loupes / insets (R2-A) ──────────────────────────────────
  const insets = (st.annotations || []).filter(a => a.type === 'inset');
  insets.forEach(ins => {{
    const src = ins.src, box = ins.box;
    if (!src || !box) return;
    const sx = src.x * W, sy = src.y * H, sw = src.w * W, sh = src.h * H;
    const bx = box.x * W, by = box.y * H, bw = box.w * W, bh = box.h * H;
    const ICOL = {{ red:'#E22', black:'#000', white:'#fff' }}[ins.color || 'white'];

    // Crop traité agrandi dans la boîte
    ctx.imageSmoothingEnabled = true;
    ctx.drawImage(base, sx, sy, sw, sh, bx, by, bw, bh);

    // Bordure boîte
    ctx.strokeStyle = ICOL;
    ctx.lineWidth = s(2);
    ctx.strokeRect(bx, by, bw, bh);

    // Liseré pointillé zone source
    ctx.lineWidth = s(1.5);
    ctx.setLineDash([s(6), s(4)]);
    ctx.strokeRect(sx, sy, sw, sh);
    ctx.setLineDash([]);

    // Amorce : relier les bords les plus proches entre src et box
    const scx = sx + sw/2, scy = sy + sh/2;
    const bcx = bx + bw/2, bcy = by + bh/2;
    const acsx = scx + Math.sign(bcx - scx) * sw/2;
    const acsy = scy + Math.sign(bcy - scy) * sh/2;
    const acbx = bcx - Math.sign(bcx - scx) * bw/2;
    const acby = bcy - Math.sign(bcy - scy) * bh/2;
    ctx.beginPath();
    ctx.moveTo(acsx, acsy);
    ctx.lineTo(acbx, acby);
    ctx.strokeStyle = ICOL;
    ctx.lineWidth = s(1.5);
    ctx.stroke();

    // Label optionnel sous la boîte
    if (ins.label) {{
      ctx.font = `400 ${{s(22)}}px "Roboto Mono",monospace`;
      ctx.fillStyle = ICOL;
      ctx.textBaseline = 'top';
      ctx.textAlign = 'left';
      ctx.fillText(ins.label, bx, by + bh + s(4));
      ctx.textBaseline = 'middle';
      ctx.textAlign = 'start';
    }}
  }});

  // ── Formes libres (R2-B Lot 1) ───────────────────────────────
  const shapes = (st.annotations || []).filter(a =>
    ['ellipse','rect','poly','arrow','bracket'].includes(a.type));

  function shapeColor(c) {{
    return {{ red:'#E22', black:'#000', white:'#fff' }}[c || 'red'];
  }}
  function strokeWithHalo(ctx, col, lw, drawFn) {{
    // Halo pour lisibilité sur fond clair
    if (col === '#fff' || col === '#000') {{
      ctx.save();
      ctx.lineWidth = lw + s(3);
      ctx.strokeStyle = col === '#fff' ? 'rgba(0,0,0,0.45)' : 'rgba(255,255,255,0.35)';
      drawFn();
      ctx.restore();
    }}
    ctx.lineWidth = lw;
    ctx.strokeStyle = col;
    drawFn();
  }}

  shapes.forEach(sh => {{
    const COL = shapeColor(sh.color);
    ctx.save();
    ctx.strokeStyle = COL;
    ctx.lineWidth = s(2.5);
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';

    if (sh.type === 'ellipse') {{
      const cx = sh.cx*W, cy = sh.cy*H, rx = sh.rx*W, ry = sh.ry*H;
      strokeWithHalo(ctx, COL, s(2.5), () => {{
        ctx.beginPath();
        ctx.ellipse(cx, cy, rx, ry, 0, 0, Math.PI*2);
        ctx.stroke();
      }});
    }} else if (sh.type === 'rect') {{
      const rx2 = sh.x*W, ry2 = sh.y*H, rw = sh.w*W, rh = sh.h*H;
      const ang = (sh.angle || 0) * Math.PI / 180;
      ctx.translate(rx2 + rw/2, ry2 + rh/2);
      ctx.rotate(ang);
      strokeWithHalo(ctx, COL, s(2.5), () => {{
        ctx.beginPath();
        ctx.strokeRect(-rw/2, -rh/2, rw, rh);
      }});
    }} else if (sh.type === 'poly') {{
      const pts = sh.pts || [];
      if (pts.length < 2) {{ ctx.restore(); return; }}
      strokeWithHalo(ctx, COL, s(2.5), () => {{
        ctx.beginPath();
        ctx.moveTo(pts[0].x*W, pts[0].y*H);
        for (let i=1; i<pts.length; i++) ctx.lineTo(pts[i].x*W, pts[i].y*H);
        if (sh.closed) ctx.closePath();
        ctx.stroke();
      }});
    }} else if (sh.type === 'arrow') {{
      const ax1=sh.x1*W, ay1=sh.y1*H, ax2=sh.x2*W, ay2=sh.y2*H;
      const adx=ax2-ax1, ady=ay2-ay1, alen=Math.hypot(adx,ady)||1;
      const headLen = s(22), headW = s(11);
      const ux=adx/alen, uy=ady/alen;
      const px=-uy, py=ux;
      // Shaft
      strokeWithHalo(ctx, COL, s(2.5), () => {{
        ctx.beginPath();
        ctx.moveTo(ax1, ay1);
        ctx.lineTo(ax2 - ux*headLen, ay2 - uy*headLen);
        ctx.stroke();
      }});
      // Tête pleine
      ctx.fillStyle = COL;
      ctx.beginPath();
      ctx.moveTo(ax2, ay2);
      ctx.lineTo(ax2 - ux*headLen + px*headW, ay2 - uy*headLen + py*headW);
      ctx.lineTo(ax2 - ux*headLen - px*headW, ay2 - uy*headLen - py*headW);
      ctx.closePath();
      ctx.fill();
    }} else if (sh.type === 'bracket') {{
      const bx1=sh.x1*W, by1=sh.y1*H, bx2=sh.x2*W, by2=sh.y2*H;
      const bdx=bx2-bx1, bdy=by2-by1, blen=Math.hypot(bdx,bdy)||1;
      const bux=bdx/blen, buy=bdy/blen;
      const bpx=-buy*((sh.depth||0.04)*Math.min(W,H));
      const bpy= bux*((sh.depth||0.04)*Math.min(W,H));
      strokeWithHalo(ctx, COL, s(2.5), () => {{
        ctx.beginPath();
        ctx.moveTo(bx1+bpx, by1+bpy); ctx.lineTo(bx1, by1);
        ctx.lineTo(bx2, by2);
        ctx.lineTo(bx2+bpx, by2+bpy);
        ctx.stroke();
      }});
    }}
    ctx.restore();
  }});

  // ── Labels (R2-B Lot 2) ──────────────────────────────────────
  const labels = (st.annotations || []).filter(a => a.type === 'label');
  labels.forEach(lb => {{
    if (!lb.text) return;
    const lx2 = lb.x * W, ly2 = lb.y * H;
    const LCOLmap = {{ red:'#E22', black:'#000', white:'#fff' }};
    const LCOL = LCOLmap[lb.color || 'red'];
    ctx.save();

    if (lb.style === 'stamp') {{
      // Boîte pleine + texte Roboto Mono inversé
      const fsize = s(22);
      ctx.font = `700 ${{fsize}}px "Roboto Mono",monospace`;
      const tw = ctx.measureText(lb.text).width;
      const pad = s(8);
      const bw2 = tw + pad * 2, bh2 = fsize + pad * 1.4;
      ctx.fillStyle = LCOL;
      ctx.fillRect(lx2 - bw2/2, ly2 - bh2/2, bw2, bh2);
      const textFill = (lb.color === 'white') ? '#111' : '#fff';
      ctx.fillStyle = textFill;
      ctx.textBaseline = 'middle';
      ctx.textAlign = 'center';
      ctx.fillText(lb.text, lx2, ly2);
    }} else if (lb.style === 'cursive') {{
      // Caveat + halo de lisibilité
      const fsize = s(36);
      ctx.font = `400 ${{fsize}}px "Caveat",cursive`;
      ctx.textBaseline = 'middle';
      ctx.textAlign = 'center';
      strokeWithHalo(ctx, LCOL, s(3), () => {{
        ctx.strokeText(lb.text, lx2, ly2);
      }});
      ctx.fillStyle = LCOL;
      ctx.fillText(lb.text, lx2, ly2);
    }} else {{
      // plain : Roboto Mono + halo
      const fsize = s(22);
      ctx.font = `400 ${{fsize}}px "Roboto Mono",monospace`;
      ctx.textBaseline = 'middle';
      ctx.textAlign = 'center';
      strokeWithHalo(ctx, LCOL, s(3), () => {{
        ctx.strokeText(lb.text, lx2, ly2);
      }});
      ctx.fillStyle = LCOL;
      ctx.fillText(lb.text, lx2, ly2);
    }}
    ctx.restore();
  }});

  // ── Bandeau classification (R2-B Lot 2) — z-max ──────────────
  if (st.classification && st.classification.enabled) {{
    const CLASSIF_COLORS = {{
      'UNCLASSIFIED': '#007a33',
      'CONFIDENTIAL': '#003087',
      'SECRET':       '#c8102e',
      'TOP SECRET':   '#ff8200'
    }};
    const level = st.classification.level || 'UNCLASSIFIED';
    const barColor = CLASSIF_COLORS[level] || '#007a33';
    const barH = bannerH;   // même valeur que celle utilisée pour blockY/cartY
    const cfsize = s(18);
    ctx.save();
    // Barre haute
    ctx.fillStyle = barColor;
    ctx.fillRect(0, 0, W, barH);
    // Barre basse
    ctx.fillRect(0, H - barH, W, barH);
    // Texte centré blanc gras
    ctx.fillStyle = '#fff';
    ctx.font = `700 ${{cfsize}}px "Roboto Mono",monospace`;
    ctx.textBaseline = 'middle';
    ctx.textAlign = 'center';
    ctx.fillText(level, W/2, barH/2);
    ctx.fillText(level, W/2, H - barH/2);
    ctx.restore();
  }}

  // ── Cercles numérotés (H2 : couleur pilotée) ─────────────────────
  const MK = {{ red:'#E22', black:'#000', white:'#fff' }}[st.markerColor || 'red'];
  ctx.textBaseline = 'middle';
  STATE.cartouche.forEach((e, i) => {{
    if (!e.point) return;
    const pcx = e.x * W;
    const pcy = e.y * H;
    const pr  = s(34);

    // ── Amorce (R2-A) : trait bord du cercle → target ───────────
    if (e.target) {{
      const tx = e.target.x * W, ty = e.target.y * H;
      const dx = tx - pcx, dy = ty - pcy;
      const d  = Math.hypot(dx, dy) || 1;
      const asx = pcx + dx/d * pr, asy = pcy + dy/d * pr;
      // Halo
      ctx.beginPath();
      ctx.moveTo(asx, asy); ctx.lineTo(tx, ty);
      ctx.lineWidth = s(5);
      ctx.strokeStyle = 'rgba(0,0,0,0.45)';
      ctx.stroke();
      // Trait
      ctx.beginPath();
      ctx.moveTo(asx, asy); ctx.lineTo(tx, ty);
      ctx.lineWidth = s(2.5);
      ctx.strokeStyle = MK;
      ctx.stroke();
      // Point cible
      ctx.beginPath();
      ctx.arc(tx, ty, s(5), 0, Math.PI*2);
      ctx.fillStyle = MK;
      ctx.fill();
    }}

    // Cercle
    ctx.beginPath();
    ctx.arc(pcx, pcy, pr, 0, Math.PI*2);
    ctx.strokeStyle = MK;
    ctx.lineWidth = s(3);
    ctx.stroke();

    // Numéro à côté (droite du cercle) — ne masque pas l'objet
    const nx  = pcx + pr + s(10);
    const ny  = pcy;
    const lab = String(i + 1);
    ctx.font = `700 ${{s(30)}}px "Gunplay","Roboto Mono",monospace`;
    ctx.textAlign = 'left';
    // Halo lisibilité (conservé pour blanc/rouge sur fond clair)
    ctx.lineWidth = s(4);
    ctx.strokeStyle = 'rgba(0,0,0,0.55)';
    ctx.strokeText(lab, nx, ny);
    ctx.fillStyle = MK;
    ctx.fillText(lab, nx, ny);
  }});
  ctx.textAlign = 'start';  // reset
}}

// ── Preview scheduling ─────────────────────────────────────────
let _previewTimeout = null;
function schedulePreview() {{
  clearTimeout(_previewTimeout);
  _previewTimeout = setTimeout(renderPreview, 60);
}}

async function renderPreview() {{
  if (!SOURCE_READY || !SOURCE_IMG) return;
  const token = ++RENDER_TOKEN;
  await ensureFonts();
  collectState();
  const logoImg = await getLogoImage();     // résolu AVANT tout effacement (cache → quasi instantané)
  if (token !== RENDER_TOKEN) return;       // rendu plus récent en route → abandon
  const W = SOURCE_IMG.naturalWidth;
  const H = SOURCE_IMG.naturalHeight;
  const canvas = document.getElementById('preview-canvas');
  const ctx    = canvas.getContext('2d');
  canvas.width  = W;                        // effacement juste avant le dessin SYNCHRONE
  canvas.height = H;
  composeRecon(ctx, W, H, STATE, logoImg);
  drawEditOverlays(ctx, W, H);
}}

// ── Overlays d'édition (poignées resize, points target) ──────
// Aperçu uniquement — jamais inclus dans composeRecon (non exportés)
function drawEditOverlays(ctx, W, H) {{
  const scale = W / 1920;
  const s = v => Math.round(v * scale);
  const HW = s(22);

  // Poignées resize insets
  (STATE.annotations || []).filter(a => a.type === 'inset').forEach(ins => {{
    if (ins.box) {{
      const bx = (ins.box.x + ins.box.w) * W;
      const by = (ins.box.y + ins.box.h) * H;
      ctx.fillStyle = 'rgba(255,255,255,0.85)';
      ctx.strokeStyle = '#000';
      ctx.lineWidth = s(1.5);
      ctx.fillRect(bx - HW/2, by - HW/2, HW, HW);
      ctx.strokeRect(bx - HW/2, by - HW/2, HW, HW);
      ctx.beginPath();
      ctx.moveTo(bx - HW*0.3, by + HW*0.3);
      ctx.lineTo(bx + HW*0.3, by - HW*0.3);
      ctx.moveTo(bx,           by + HW*0.3);
      ctx.lineTo(bx + HW*0.3, by);
      ctx.strokeStyle = '#333';
      ctx.lineWidth = s(2);
      ctx.stroke();
    }}
    if (ins.src) {{
      const sx = (ins.src.x + ins.src.w) * W;
      const sy = (ins.src.y + ins.src.h) * H;
      ctx.fillStyle = 'rgba(255,255,100,0.80)';
      ctx.strokeStyle = '#000';
      ctx.lineWidth = s(1.5);
      ctx.fillRect(sx - HW/2, sy - HW/2, HW, HW);
      ctx.strokeRect(sx - HW/2, sy - HW/2, HW, HW);
      ctx.beginPath();
      ctx.moveTo(sx - HW*0.3, sy + HW*0.3);
      ctx.lineTo(sx + HW*0.3, sy - HW*0.3);
      ctx.moveTo(sx,           sy + HW*0.3);
      ctx.lineTo(sx + HW*0.3, sy);
      ctx.strokeStyle = '#333';
      ctx.lineWidth = s(2);
      ctx.stroke();
    }}
  }});

  // Poignées formes libres (Lot 1)
  (STATE.annotations || []).forEach(sh => {{
    const COL2 = {{ red:'#E22', black:'#000', white:'#fff' }}[sh.color || 'red'];
    const HH = HW;

    function handleRect(hx, hy, fill) {{
      ctx.fillStyle = fill || 'rgba(255,255,255,0.85)';
      ctx.strokeStyle = '#000'; ctx.lineWidth = s(1.5);
      ctx.fillRect(hx - HH/2, hy - HH/2, HH, HH);
      ctx.strokeRect(hx - HH/2, hy - HH/2, HH, HH);
    }}
    function handleCirc(hx, hy, fill) {{
      ctx.fillStyle = fill || 'rgba(255,255,255,0.85)';
      ctx.strokeStyle = '#000'; ctx.lineWidth = s(1.5);
      ctx.beginPath(); ctx.arc(hx, hy, HH/2, 0, Math.PI*2);
      ctx.fill(); ctx.stroke();
    }}

    if (sh.type === 'ellipse') {{
      // Poignée resize = coin de la bbox
      handleRect((sh.cx + sh.rx)*W, (sh.cy + sh.ry)*H, 'rgba(255,200,50,0.9)');
    }} else if (sh.type === 'rect') {{
      const rx2=(sh.x+sh.w/2)*W, ry2=(sh.y+sh.h/2)*H;
      const rw=sh.w*W, rh=sh.h*H;
      const ang=(sh.angle||0)*Math.PI/180;
      // Coin bas-droit (resize)
      const cbrx= rx2 + Math.cos(ang)*(rw/2) - Math.sin(ang)*(rh/2) * (-1);
      const cbry= ry2 + Math.sin(ang)*(rw/2) + Math.cos(ang)*(rh/2);
      // Rotation handle = au-dessus du rect
      const rotDist = rh/2 + s(30);
      const rhx = rx2 - Math.sin(ang)*rotDist;
      const rhy = ry2 - Math.cos(ang)*rotDist;
      handleRect(rx2 + (rw/2)*Math.cos(ang) - (rh/2)*Math.sin(ang),
                 ry2 + (rw/2)*Math.sin(ang) + (rh/2)*Math.cos(ang),
                 'rgba(255,200,50,0.9)');
      handleCirc(rhx, rhy, 'rgba(100,200,255,0.9)');
    }} else if (sh.type === 'poly') {{
      (sh.pts || []).forEach(pt => {{
        handleCirc(pt.x*W, pt.y*H, 'rgba(255,255,255,0.85)');
      }});
    }} else if (sh.type === 'arrow' || sh.type === 'bracket') {{
      handleCirc(sh.x1*W, sh.y1*H, 'rgba(255,255,255,0.85)');
      handleCirc(sh.x2*W, sh.y2*H, 'rgba(255,200,50,0.9)');
    }}
  }});

  // Croix pour points target (amorce)
  STATE.cartouche.forEach(e => {{
    if (!e.point || !e.target) return;
    const tx = e.target.x * W;
    const ty = e.target.y * H;
    const r = s(10);
    ctx.lineWidth = s(3.5);
    ctx.strokeStyle = 'rgba(0,0,0,0.55)';
    ctx.beginPath();
    ctx.moveTo(tx - r, ty); ctx.lineTo(tx + r, ty);
    ctx.moveTo(tx, ty - r); ctx.lineTo(tx, ty + r);
    ctx.stroke();
    ctx.lineWidth = s(2);
    ctx.strokeStyle = 'rgba(255,255,255,0.9)';
    ctx.beginPath();
    ctx.moveTo(tx - r, ty); ctx.lineTo(tx + r, ty);
    ctx.moveTo(tx, ty - r); ctx.lineTo(tx, ty + r);
    ctx.stroke();
  }});
}}

// ── Logo image resolution ──────────────────────────────────────
function getLogoImage() {{
  return new Promise(resolve => {{
    const id = STATE.logoId;
    if (!id || id === 'none') return resolve(null);
    const logo = STATE.logos.find(l => l.id === id);
    if (!logo || !logo.b64) return resolve(null);
    const cached = LOGO_CACHE[id];
    if (cached && cached.complete && cached.naturalWidth) return resolve(cached);
    const img = new Image();
    img.onload  = () => {{ LOGO_CACHE[id] = img; resolve(img); }};
    img.onerror = () => resolve(null);
    img.src = logo.b64;
  }});
}}

// ── Export PNG ─────────────────────────────────────────────────
async function exportPNG() {{
  if (!SOURCE_READY || !SOURCE_IMG) {{
    showToast(t('toast.no-image'), 'err');
    return;
  }}
  showToast(t('toast.export.start'), '', 1500);
  await ensureFonts();

  const W = SOURCE_IMG.naturalWidth;
  const H = SOURCE_IMG.naturalHeight;
  const canvas = document.getElementById('export-canvas');
  const ctx    = canvas.getContext('2d');
  canvas.width  = W;
  canvas.height = H;

  collectState();
  const logoImg = await getLogoImage();
  composeRecon(ctx, W, H, STATE, logoImg);

  canvas.toBlob(blob => {{
    if (!blob) {{ showToast('Export failed', 'err'); return; }}
    const target  = STATE.fields.target || '';
    const slug    = target.replace(/[^a-zA-Z0-9-]/g, '_').replace(/_+/g, '_').slice(0, 40);
    const ts      = Date.now();
    const fname   = slug ? `recon_${{slug}}_${{ts}}.png` : `recon_${{ts}}.png`;
    const url     = URL.createObjectURL(blob);
    const a       = document.createElement('a');
    a.href        = url;
    a.download    = fname;
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 5000);
    showToast(t('toast.export.done'), 'ok');
  }}, 'image/png');
}}

// ── Event wiring ───────────────────────────────────────────────
function initEvents() {{
  // Theme
  document.getElementById('theme-select').addEventListener('change', e => applyTheme(e.target.value));

  // Lang
  document.getElementById('btn-lang').addEventListener('click', () => {{
    setLang(CURRENT_LANG === 'fr' ? 'en' : 'fr');
  }});

  // Drop zone
  const dz = document.getElementById('drop-zone');
  dz.addEventListener('click', () => document.getElementById('file-source').click());
  dz.addEventListener('keydown', e => {{ if (e.key === 'Enter' || e.key === ' ') {{ e.preventDefault(); dz.click(); }} }});
  dz.addEventListener('dragover', e => {{ e.preventDefault(); dz.classList.add('dragover'); }});
  dz.addEventListener('dragleave', () => dz.classList.remove('dragover'));
  dz.addEventListener('drop', e => {{
    e.preventDefault();
    dz.classList.remove('dragover');
    const file = e.dataTransfer.files[0];
    if (file) loadImageFile(file);
  }});

  // File input source
  document.getElementById('file-source').addEventListener('change', e => {{
    if (e.target.files[0]) loadImageFile(e.target.files[0]);
    e.target.value = '';
  }});

  // Replace button
  document.getElementById('btn-replace').addEventListener('click', () => {{
    document.getElementById('file-source').click();
  }});

  // Contrast slider
  document.getElementById('contrast-slider').addEventListener('input', e => {{
    STATE.contrast = parseInt(e.target.value, 10);
    document.getElementById('contrast-val').textContent = STATE.contrast + '%';
    saveState();
    schedulePreview();
  }});

  // R2-C : sélecteur capteur
  document.getElementById('sensor-mode').addEventListener('change', e => {{
    STATE.sensorMode = e.target.value;
    saveState();
    schedulePreview();
  }});

  // Form fields
  ['f-target','f-coords','f-crs','f-alt','f-msn','f-sensor','f-dtg','f-crew','f-class'].forEach(id => {{
    const el = document.getElementById(id);
    if (el) {{
      el.addEventListener('input', () => {{ saveState(); schedulePreview(); }});
    }}
  }});

  // Logo mode buttons
  document.querySelectorAll('#logo-mode button').forEach(btn => {{
    btn.addEventListener('click', () => {{
      STATE.logoMode = btn.dataset.logoMode;
      renderLogoMode();
      saveState();
      schedulePreview();
    }});
  }});

  // Text color buttons (E3)
  document.querySelectorAll('#text-color-group button').forEach(btn => {{
    btn.addEventListener('click', () => {{
      STATE.textColor = btn.dataset.textColor;
      renderTextColor();
      saveState();
      schedulePreview();
    }});
  }});

  // Marker color buttons (H3)
  document.querySelectorAll('#marker-color-group button').forEach(btn => {{
    btn.addEventListener('click', () => {{
      STATE.markerColor = btn.dataset.markerColor;
      renderMarkerColor();
      saveState();
      schedulePreview();
    }});
  }});

  // Logo file input
  document.getElementById('file-logo').addEventListener('change', e => {{
    if (e.target.files[0]) loadLogoFile(e.target.files[0]);
    e.target.value = '';
  }});

  // G2 : import config wing BG
  document.getElementById('file-wing').addEventListener('change', e => {{
    if (e.target.files[0]) importWingLogos(e.target.files[0]);
    e.target.value = '';
  }});

  // Add cartouche row — B1 : entrée enrichie avec coordonnées en cascade
  document.getElementById('btn-add-cartouche').addEventListener('click', () => {{
    const k = STATE.cartouche.length;
    STATE.cartouche.push({{
      label: '',
      x: Math.min(0.90, 0.50 + k * 0.03),
      y: Math.min(0.90, 0.50 + k * 0.03),
      point: true
    }});
    saveState();
    renderCartoucheEditor();
    schedulePreview();
  }});

  // R2-B Lot 1 : toolbox formes
  const _mkColor = () => STATE.markerColor || 'red';
  const _shapeDefaults = {{
    ellipse: () => ({{ id:uid(), type:'ellipse', cx:0.50, cy:0.50, rx:0.08, ry:0.05, color:_mkColor() }}),
    rect:    () => ({{ id:uid(), type:'rect',    x:0.40,  y:0.40, w:0.18, h:0.12, angle:0, color:_mkColor() }}),
    poly:    () => ({{ id:uid(), type:'poly',    pts:[{{x:0.40,y:0.45}},{{x:0.50,y:0.35}},{{x:0.60,y:0.45}}], closed:false, color:_mkColor() }}),
    arrow:   () => ({{ id:uid(), type:'arrow',   x1:0.35, y1:0.50, x2:0.65, y2:0.50, color:_mkColor() }}),
    bracket: () => ({{ id:uid(), type:'bracket', x1:0.40, y1:0.40, x2:0.60, y2:0.60, depth:0.04, color:_mkColor() }}),
  }};
  ['ellipse','rect','poly','arrow','bracket'].forEach(t2 => {{
    const btn = document.getElementById('btn-add-'+t2);
    if (!btn) return;
    btn.addEventListener('click', () => {{
      STATE.annotations = STATE.annotations || [];
      STATE.annotations.push(_shapeDefaults[t2]());
      saveState(); renderShapesEditor(); schedulePreview();
    }});
  }});

  // R2-A : ajouter une loupe
  document.getElementById('btn-add-inset').addEventListener('click', () => {{
    STATE.annotations = STATE.annotations || [];
    const _sw = 0.12, _sh = 0.12, _bw = 0.22;
    STATE.annotations.push({{
      id: uid(),
      type: 'inset',
      src: {{ x: 0.35, y: 0.35, w: _sw, h: _sh }},
      box: {{ x: 0.02, y: 0.02, w: _bw, h: _bw * (_sh / _sw) }},
      color: 'white',
      label: ''
    }});
    saveState();
    renderInsetEditor();
    schedulePreview();
  }});

  // R2-B Lot 2 : ajouter un label
  document.getElementById('btn-add-label').addEventListener('click', () => {{
    STATE.annotations = STATE.annotations || [];
    const k = (STATE.annotations || []).filter(a => a.type === 'label').length;
    STATE.annotations.push({{
      id: uid(),
      type: 'label',
      x: Math.min(0.90, 0.50 + k * 0.03),
      y: Math.min(0.90, 0.40 + k * 0.03),
      text: '',
      style: 'stamp',
      color: STATE.markerColor || 'red'
    }});
    saveState(); renderLabelEditor(); schedulePreview();
  }});

  // R2-B Lot 2 : classification
  const classifEnable = document.getElementById('classif-enable');
  const classifLevel  = document.getElementById('classif-level');
  if (classifEnable) {{
    classifEnable.checked = STATE.classification.enabled;
    classifEnable.addEventListener('change', () => {{
      STATE.classification.enabled = classifEnable.checked;
      saveState(); schedulePreview();
    }});
  }}
  if (classifLevel) {{
    classifLevel.value = STATE.classification.level;
    classifLevel.addEventListener('change', () => {{
      STATE.classification.level = classifLevel.value;
      saveState(); schedulePreview();
    }});
  }}

  // Export
  // Sliders effets
  [['fx-vignette','fxVignette'],['fx-grain','fxGrain'],['fx-scanlines','fxScanlines']].forEach(([id, key]) => {{
    const sl = document.getElementById(id);
    if (!sl) return;
    sl.addEventListener('input', () => {{
      STATE[key] = parseInt(sl.value, 10);
      document.getElementById(id+'-val').textContent = sl.value;
      saveState();
      schedulePreview();
    }});
  }});

  document.getElementById('btn-export').addEventListener('click', exportPNG);

  // Tabs (mobile)
  document.querySelectorAll('.tab-btn').forEach(btn => {{
    btn.addEventListener('click', () => {{
      const tab = btn.dataset.tab;
      document.getElementById('app').dataset.activeTab = tab;
      document.querySelectorAll('.tab-btn').forEach(b => {{
        b.classList.toggle('active', b.dataset.tab === tab);
        b.setAttribute('aria-selected', b.dataset.tab === tab ? 'true' : 'false');
      }});
    }});
  }});

  // R2-A — Drag étendu : markers, targets, box/src insets, poignées resize
  const cv = document.getElementById('preview-canvas');
  cv.style.touchAction = 'none';

  let dragState = null;
  let dragOffX = 0, dragOffY = 0;

  const toNorm = ev => {{
    const rect = cv.getBoundingClientRect();
    return {{
      x: (ev.clientX - rect.left)  / rect.width,
      y: (ev.clientY - rect.top)   / rect.height
    }};
  }};

  const SLOP = 0.04;
  const RSLOP = 0.035;

  function hitTestAll(p) {{
    const annots = (STATE.annotations || []).filter(a => a.type === 'inset');
    // 1. Poignées resize (priorité max)
    for (const ins of annots) {{
      if (ins.box) {{
        const bx2 = ins.box.x + ins.box.w, by2 = ins.box.y + ins.box.h;
        if (Math.hypot(bx2 - p.x, by2 - p.y) < RSLOP)
          return {{ type:'resize-box', ins }};
      }}
      if (ins.src) {{
        const sx2 = ins.src.x + ins.src.w, sy2 = ins.src.y + ins.src.h;
        if (Math.hypot(sx2 - p.x, sy2 - p.y) < RSLOP)
          return {{ type:'resize-src', ins }};
      }}
    }}
    // 1b. Poignées formes libres (Lot 1)
    const fshapes = (STATE.annotations || []).filter(a =>
      ['ellipse','rect','poly','arrow','bracket'].includes(a.type));
    for (const sh of fshapes) {{
      if (sh.type === 'ellipse') {{
        const hx=sh.cx+sh.rx, hy=sh.cy+sh.ry;
        if (Math.hypot(hx - p.x, hy - p.y) < RSLOP)
          return {{ type:'resize-ellipse', sh }};
      }} else if (sh.type === 'rect') {{
        const ang=(sh.angle||0)*Math.PI/180;
        const rcx=sh.x+sh.w/2, rcy=sh.y+sh.h/2;
        const brx=rcx+(sh.w/2)*Math.cos(ang)-(sh.h/2)*Math.sin(ang);
        const bry=rcy+(sh.w/2)*Math.sin(ang)+(sh.h/2)*Math.cos(ang);
        if (Math.hypot(brx - p.x, bry - p.y) < RSLOP)
          return {{ type:'resize-rect', sh }};
        const rhx=rcx - Math.sin(ang)*(sh.h/2 + 0.04);
        const rhy=rcy - Math.cos(ang)*(sh.h/2 + 0.04);
        if (Math.hypot(rhx - p.x, rhy - p.y) < RSLOP)
          return {{ type:'rotate-rect', sh, cx:rcx, cy:rcy }};
      }} else if (sh.type === 'poly') {{
        for (let pi=0; pi<(sh.pts||[]).length; pi++) {{
          const pt=sh.pts[pi];
          if (Math.hypot(pt.x - p.x, pt.y - p.y) < SLOP)
            return {{ type:'drag-poly-pt', sh, pi }};
        }}
      }} else if (sh.type === 'arrow' || sh.type === 'bracket') {{
        if (Math.hypot(sh.x2 - p.x, sh.y2 - p.y) < SLOP)
          return {{ type:'drag-shape-p2', sh }};
        if (Math.hypot(sh.x1 - p.x, sh.y1 - p.y) < SLOP)
          return {{ type:'drag-shape-p1', sh }};
      }}
    }}
    // 1c. Corps des formes libres
    for (const sh of fshapes) {{
      if (sh.type === 'ellipse') {{
        const edx=(p.x-sh.cx)/(sh.rx||0.01), edy=(p.y-sh.cy)/(sh.ry||0.01);
        if (edx*edx+edy*edy <= 1.2)
          return {{ type:'drag-ellipse', sh, ox:p.x-sh.cx, oy:p.y-sh.cy }};
      }} else if (sh.type === 'rect') {{
        if (p.x>=sh.x&&p.x<=sh.x+sh.w&&p.y>=sh.y&&p.y<=sh.y+sh.h)
          return {{ type:'drag-rect', sh, ox:p.x-sh.x, oy:p.y-sh.y }};
      }} else if (sh.type === 'poly') {{
        if ((sh.pts||[]).length>0) {{
          const c0=sh.pts[0];
          if (Math.hypot(c0.x-p.x, c0.y-p.y) < SLOP*2)
            return {{ type:'drag-poly-group', sh, ox:p.x, oy:p.y, snapX:sh.pts.map(q=>q.x), snapY:sh.pts.map(q=>q.y) }};
        }}
      }} else if (sh.type === 'arrow' || sh.type === 'bracket') {{
        const mx=(sh.x1+sh.x2)/2, my=(sh.y1+sh.y2)/2;
        if (Math.hypot(mx-p.x, my-p.y) < SLOP*1.5)
          return {{ type:'drag-shape-mid', sh, ox:p.x, oy:p.y }};
      }}
    }}

    // 2. Corps box
    for (const ins of annots) {{
      if (!ins.box) continue;
      const b = ins.box;
      if (p.x >= b.x && p.x <= b.x+b.w && p.y >= b.y && p.y <= b.y+b.h)
        return {{ type:'drag-box', ins, ox: p.x-b.x, oy: p.y-b.y }};
    }}
    // 3. Corps src
    for (const ins of annots) {{
      if (!ins.src) continue;
      const s2 = ins.src;
      if (p.x >= s2.x && p.x <= s2.x+s2.w && p.y >= s2.y && p.y <= s2.y+s2.h)
        return {{ type:'drag-src', ins, ox: p.x-s2.x, oy: p.y-s2.y }};
    }}
    // 4. Points target
    for (let i=0; i<STATE.cartouche.length; i++) {{
      const e = STATE.cartouche[i];
      if (e.point && e.target && Math.hypot(e.target.x - p.x, e.target.y - p.y) < SLOP)
        return {{ type:'target', idx: i }};
    }}
    // 5. Cercles markers
    for (let i=0; i<STATE.cartouche.length; i++) {{
      const e = STATE.cartouche[i];
      if (e.point && Math.hypot(e.x - p.x, e.y - p.y) < SLOP)
        return {{ type:'marker', idx: i }};
    }}
    // 6. Labels (R2-B Lot 2)
    const lbls = (STATE.annotations || []).filter(a => a.type === 'label');
    for (const lb of lbls) {{
      if (Math.hypot(lb.x - p.x, lb.y - p.y) < SLOP)
        return {{ type:'drag-label', lb, ox: p.x - lb.x, oy: p.y - lb.y }};
    }}
    return null;
  }}

  cv.addEventListener('pointerdown', ev => {{
    const p = toNorm(ev);
    const hit = hitTestAll(p);
    if (hit) {{
      dragState = hit;
      dragOffX = hit.ox || 0;
      dragOffY = hit.oy || 0;
      cv.setPointerCapture(ev.pointerId);
    }}
  }});

  cv.addEventListener('pointermove', ev => {{
    if (!dragState) return;
    ev.preventDefault();
    const p = toNorm(ev);
    const cl = (v, lo, hi) => Math.min(hi, Math.max(lo, v));
    if (dragState.type === 'marker') {{
      const e = STATE.cartouche[dragState.idx];
      e.x = cl(p.x, 0, 1); e.y = cl(p.y, 0, 1);
    }} else if (dragState.type === 'target') {{
      const e = STATE.cartouche[dragState.idx];
      if (e.target) {{ e.target.x = cl(p.x, 0, 1); e.target.y = cl(p.y, 0, 1); }}
    }} else if (dragState.type === 'drag-box') {{
      const b = dragState.ins.box;
      b.x = cl(p.x - dragOffX, 0, 1 - b.w);
      b.y = cl(p.y - dragOffY, 0, 1 - b.h);
    }} else if (dragState.type === 'drag-src') {{
      const s2 = dragState.ins.src;
      s2.x = cl(p.x - dragOffX, 0, 1 - s2.w);
      s2.y = cl(p.y - dragOffY, 0, 1 - s2.h);
    }} else if (dragState.type === 'resize-box') {{
      const b = dragState.ins.box;
      b.w = cl(p.x - b.x, 0.05, 0.85);
      b.h = cl(p.y - b.y, 0.04, 0.85);
      // Conformer src au ratio de la box
      const s2b = dragState.ins.src;
      if (b.w > 0) {{
        s2b.h = cl(s2b.w * (b.h / b.w), 0.03, 0.70);
        if (s2b.y + s2b.h > 1) s2b.y = 1 - s2b.h;
      }}
    }} else if (dragState.type === 'resize-src') {{
      const s2 = dragState.ins.src;
      s2.w = cl(p.x - s2.x, 0.03, 0.70);
      s2.h = cl(p.y - s2.y, 0.03, 0.70);
      // Conformer box au ratio de la src
      const bs = dragState.ins.box;
      if (s2.w > 0) {{
        bs.h = cl(bs.w * (s2.h / s2.w), 0.04, 0.85);
        if (bs.y + bs.h > 1) bs.y = 1 - bs.h;
      }}
    }} else if (dragState.type === 'resize-ellipse') {{
      const sh=dragState.sh;
      sh.rx = cl(p.x - sh.cx, 0.01, 0.5);
      sh.ry = cl(p.y - sh.cy, 0.01, 0.5);
    }} else if (dragState.type === 'resize-rect') {{
      const sh=dragState.sh;
      const ang=(sh.angle||0)*Math.PI/180;
      const rcx=sh.x+sh.w/2, rcy=sh.y+sh.h/2;
      // Rotation inverse pour trouver le coin en coords locales
      const dx=p.x-rcx, dy=p.y-rcy;
      const lx= dx*Math.cos(-ang) - dy*Math.sin(-ang);
      const ly= dx*Math.sin(-ang) + dy*Math.cos(-ang);
      sh.w = cl(lx*2, 0.02, 0.95);
      sh.h = cl(ly*2, 0.01, 0.95);
      sh.x = rcx - sh.w/2; sh.y = rcy - sh.h/2;
    }} else if (dragState.type === 'rotate-rect') {{
      const sh=dragState.sh;
      const rcx=dragState.cx, rcy=dragState.cy;
      sh.angle = Math.atan2(p.x-rcx, -(p.y-rcy)) * 180/Math.PI;
    }} else if (dragState.type === 'drag-ellipse') {{
      const sh=dragState.sh;
      sh.cx = cl(p.x - dragOffX, sh.rx, 1-sh.rx);
      sh.cy = cl(p.y - dragOffY, sh.ry, 1-sh.ry);
    }} else if (dragState.type === 'drag-rect') {{
      const sh=dragState.sh;
      sh.x = cl(p.x - dragOffX, 0, 1-sh.w);
      sh.y = cl(p.y - dragOffY, 0, 1-sh.h);
    }} else if (dragState.type === 'drag-poly-pt') {{
      const sh=dragState.sh, pi=dragState.pi;
      sh.pts[pi].x = cl(p.x, 0, 1);
      sh.pts[pi].y = cl(p.y, 0, 1);
    }} else if (dragState.type === 'drag-poly-group') {{
      const sh=dragState.sh;
      const ddx=p.x-dragState.ox, ddy=p.y-dragState.oy;
      dragState.ox=p.x; dragState.oy=p.y;
      sh.pts.forEach(pt => {{ pt.x=cl(pt.x+ddx,0,1); pt.y=cl(pt.y+ddy,0,1); }});
    }} else if (dragState.type === 'drag-shape-p1') {{
      dragState.sh.x1=cl(p.x,0,1); dragState.sh.y1=cl(p.y,0,1);
    }} else if (dragState.type === 'drag-shape-p2') {{
      dragState.sh.x2=cl(p.x,0,1); dragState.sh.y2=cl(p.y,0,1);
    }} else if (dragState.type === 'drag-shape-mid') {{
      const sh=dragState.sh;
      const ddx=p.x-dragState.ox, ddy=p.y-dragState.oy;
      dragState.ox=p.x; dragState.oy=p.y;
      sh.x1=cl(sh.x1+ddx,0,1); sh.y1=cl(sh.y1+ddy,0,1);
      sh.x2=cl(sh.x2+ddx,0,1); sh.y2=cl(sh.y2+ddy,0,1);
    }} else if (dragState.type === 'drag-label') {{
      dragState.lb.x = cl(p.x - dragOffX, 0, 1);
      dragState.lb.y = cl(p.y - dragOffY, 0, 1);
    }}
    schedulePreview();
  }});

  cv.addEventListener('pointerup', () => {{
    if (dragState) {{ dragState = null; saveState(); }}
  }});
}}

// ── Init ───────────────────────────────────────────────────────
async function init() {{
  loadTheme();
  loadLang();

  const hasState = restoreState();
  applyStateToForm();
  renderLogoGrid();
  renderLogoMode();
  renderTextColor();
  renderMarkerColor();
  renderCartoucheEditor();
  renderInsetEditor();
  renderShapesEditor();
  renderLabelEditor();
  // Sync classification UI
  const _ce = document.getElementById('classif-enable');
  const _cl = document.getElementById('classif-level');
  if (_ce) _ce.checked = STATE.classification.enabled;
  if (_cl) _cl.value   = STATE.classification.level;

  initEvents();

  if (hasState) {{
    showToast(t('toast.state-restored'), '', 3500);
  }}

  await ensureFonts();
}}

init();
</script>
</body>
</html>
"""

# ---------- Build output ----------
os.makedirs(os.path.join(HERE, 'dist'), exist_ok=True)
OUTPUT_PATH = os.path.join(HERE, 'dist', 'dcs_recon_station.html')

with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
    f.write(HTML)

print(f"[OK] dcs_recon_station.html written ({os.path.getsize(OUTPUT_PATH)//1024} KB)")

# ---------- Vérifications ----------
import subprocess, sys

with open(OUTPUT_PATH, 'r', encoding='utf-8') as f:
    src = f.read()

def grep_present(pattern, label):
    found = pattern in src
    status = "OK" if found else "MISSING"
    print(f"  [{status}] {label}")
    return found

def grep_absent(pattern, label):
    found = pattern in src
    status = "FAIL" if found else "OK"
    print(f"  [{status}] ABSENT: {label}")
    return not found

print("\n-- Vérifications --")
grep_present('composeRecon', 'composeRecon présent')
grep_present("toBlob(blob", "toBlob PNG présent")
grep_present("image/png", "format PNG présent")
grep_present("Roboto Mono", "Police Roboto Mono présente")
grep_present("Gunplay", "Police Gunplay fallback présente")
grep_present("ensureFonts", "ensureFonts présent")
grep_present("document.fonts.ready", "fonts.ready présent")
grep_present("grayscale(1)", "grayscale appliqué")
grep_present("recon_state_v1", "clé state localStorage")
grep_present("theme_v1", "clé theme localStorage")
grep_present("lang_v1", "clé lang localStorage")
grep_present('data-i18n', "attributs i18n présents")
grep_present('I18N', "objet I18N présent")
grep_present("function t(key", "fonction t() présente")
grep_present("logoMode", "logoMode dans STATE")
grep_present("source-in", "mode source-in logo blanc")
grep_present("e.point", "champ point dans cartouche")
grep_present("cartouche-point-cb", "checkbox point visible")
grep_present("renderLogoMode", "renderLogoMode présent")
grep_present("pointerdown", "pointerdown drag présent")
grep_present("touchAction", "touch-action présent")
grep_present("applyVignette", "applyVignette présent")
grep_present("applyGrain", "applyGrain présent")
grep_present("applyScanlines", "applyScanlines présent")
grep_present("RENDER_TOKEN", "RENDER_TOKEN présent")
grep_present("LOGO_CACHE", "LOGO_CACHE présent")
grep_present("token !== RENDER_TOKEN", "garde concurrence token")
grep_present("STATE.logos", "STATE.logos tableau logos")
grep_present("importWingLogos", "importWingLogos présent")
grep_present("Math.min(logoSize", "contain ratio logo")
grep_absent("STATE.logoCustom", "STATE.logoCustom supprimé")
grep_absent("160-SQN", "160-SQN supprimé")
grep_absent("__custom__", "__custom__ supprimé")
grep_present("textColor", "textColor dans STATE")
grep_present("markerColor", "markerColor dans STATE")
grep_present("0.35 * a", "grain renforcé 0.35")
grep_present("MK", "MK couleur marqueurs")
grep_present("if (cartRows.length > 0)", "cartouche conditionnel")
grep_absent("const RED = '#E22'", "RED remplacé par MK")
grep_absent("html2canvas", "html2canvas absent")
grep_absent("toDataURL('image/jpeg'", "pas de toDataURL JPEG")
grep_absent("4th VEAW", "aucune référence 4th VEAW")
grep_absent("KHR-26", "aucune référence KHR-26")
grep_absent("Mi-24P", "aucune référence Mi-24P")
# R2-A
grep_present("STATE.annotations", "STATE.annotations présent")
grep_present("schema: 2", "schema:2 dans saveState")
grep_present("renderInsetEditor", "renderInsetEditor présent")
grep_present("drawEditOverlays", "drawEditOverlays présent")
grep_present("amorce-cb", "toggle amorce présent")
grep_present("btn-add-inset", "bouton loupe présent")
grep_present("resize-box", "hit-test resize-box présent")
grep_present("resize-src", "hit-test resize-src présent")
grep_present("base.getContext", "canvas offscreen base présent")
grep_present("drawImage(base,", "blit base → ctx présent")
grep_present("editor.inset.add", "clé i18n inset.add")
grep_present("editor.cartouche.amorce", "clé i18n amorce")
# R2-B Lot 1
grep_present("renderShapesEditor", "renderShapesEditor présent")
grep_present("strokeWithHalo", "strokeWithHalo présent")
grep_present("type:'ellipse'", "type ellipse présent")
grep_present("type:'arrow'", "type arrow présent")
grep_present("type:'bracket'", "type bracket présent")
grep_present("btn-add-ellipse", "bouton ellipse présent")
grep_present("rotate-rect", "rotate-rect hit-test présent")
grep_present("drag-poly-pt", "drag-poly-pt présent")
grep_present("editor.shapes.title", "clé i18n shapes.title")
# R2-B Lot 2
grep_present("'Caveat'", "CAVEAT_400 dans assets (font-family Caveat)")
grep_present("font-family: 'Caveat'", "font-face Caveat CSS présent")
grep_present("CAVEAT_B64", "CAVEAT_B64 const présente")
grep_present("ffCaveat", "FontFace Caveat enregistrée")
grep_present("type: 'label'", "type label présent")
grep_present("renderLabelEditor", "renderLabelEditor présent")
grep_present("btn-add-label", "bouton + Label présent")
grep_present("lb.style === 'stamp'", "rendu stamp présent")
grep_present("lb.style === 'cursive'", "rendu cursive présent")
grep_present("drag-label", "drag-label hit-test présent")
grep_present("STATE.classification", "STATE.classification présent")
grep_present("classif-enable", "toggle classif présent")
grep_present("classif-level", "select niveau classif présent")
grep_present("UNCLASSIFIED", "niveau UNCLASSIFIED présent")
grep_present("SECRET", "niveau SECRET présent")
grep_present("barH = bannerH", "bandeau réutilise bannerH")
grep_present("bannerH", "bannerH défini (correction A)")
grep_present("blockY = H - blockH - s(12) - bannerH", "blockY réserve bannerH")
grep_present("cartY  = cartMg + bannerH", "cartY réserve bannerH")
grep_present("bs.h = cl(bs.w * (s2.h / s2.w)", "ratio loupe resize-src (correction B)")
grep_present("s2b.h = cl(s2b.w * (b.h / b.w)", "ratio loupe resize-box (correction B)")
grep_present("editor.classif.title", "clé i18n classif.title")
grep_present("editor.label.add", "clé i18n label.add")
grep_present("z-max", "commentaire z-max bandeau")
# z-order : formes APRÈS loupes
src_body = src[src.find('composeRecon'):]
insets_pos = src_body.find('Loupes / insets')
shapes_pos = src_body.find('Formes libres')
labels_pos = src_body.find('Labels (R2-B')
band_pos   = src_body.find('Bandeau classification')
if insets_pos < shapes_pos < labels_pos < band_pos:
  print("  [OK] z-order : loupes → formes → labels → bandeau")
else:
  print(f"  [FAIL] z-order incorrect: insets={insets_pos} shapes={shapes_pos} labels={labels_pos} band={band_pos}")
# R2-C
grep_present("applySensorPreset", "applySensorPreset présent")
grep_present("sensorMode", "sensorMode dans STATE")
grep_present("ir-white", "mode ir-white présent")
grep_present("ir-black", "mode ir-black présent")
grep_present("sensor-mode", "select sensor-mode présent")
grep_present("editor.fx.sensor", "clé i18n sensor")
grep_present("bloom", "bloom ir-white présent")
grep_present("globalCompositeOperation = 'multiply'", "composite multiply SAR")
grep_present("applySensorPreset(bctx", "appel preset dans composeRecon")
# Vérifier ordre : preset avant vignette
sensor_pos = src.find('applySensorPreset(bctx')
vignette_pos = src.find('applyVignette(bctx')
if sensor_pos < vignette_pos:
  print("  [OK] ordre : preset → vignette")
else:
  print(f"  [FAIL] ordre incorrect preset={sensor_pos} vignette={vignette_pos}")

print("\n[BUILD DONE]")
