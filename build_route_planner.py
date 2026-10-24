#!/usr/bin/env python3
"""Build — DCS Route Planner v1.0.0.

Produit dist/dcs_route_planner.html : un fichier unique, hors ligne, sans serveur ;
seules les tuiles de carte (DCS Olympus, OpenTopoMap, Esri) viennent du réseau, et le
module retombe de lui-même sur la grille seule quand elles sont injoignables.
Les polices et les bibliothèques (Leaflet 1.9.4, BSD-2) viennent d'assets.json, à la
racine du dépôt.

Usage : python3 build_route_planner.py
"""

import json
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
APP_VERSION = "1.0.0"
OUT_PATH = os.path.join(HERE, 'dist', 'dcs_route_planner.html')
ASSETS_PATH = os.path.join(HERE, 'assets.json')

REQUIRED_ASSETS = ['STARDOS_700', 'OSWALD_500', 'OSWALD_700', 'ROBOTO_MONO_400', 'lib_leaflet', 'lib_leaflet_css']

if not os.path.isfile(ASSETS_PATH):
    raise SystemExit(f"[ERREUR] Entrée manquante : {ASSETS_PATH} (assets.json attendu à la racine du dépôt)")
with open(ASSETS_PATH, encoding='utf-8') as f:
    A = json.load(f)
for _k in REQUIRED_ASSETS:
    if _k not in A or not A[_k]:
        raise SystemExit(f"[ERREUR] Entrée manquante dans assets.json : {_k}")

# Contenu du bouton « Exemple » : document au format dcs-route-v1, copié tel quel.
EXAMPLE_ROUTE_JSON = r'''{
  "format": "dcs-route-v1",
  "name": "FOOTHOLD M3",
  "theatre": "Syria",
  "units": {
    "distance": "km",
    "altitude": "m"
  },
  "navDisplay": {
    "ref": "true",
    "decl": ""
  },
  "points": [
    {
      "name": "AKROTIRI",
      "lat": 34.5904,
      "lon": 32.9878,
      "alt": 0,
      "altRef": "MSL"
    },
    {
      "name": "WP1",
      "lat": 34.662,
      "lon": 32.67,
      "alt": 30,
      "altRef": "AGL"
    },
    {
      "name": "POLIS",
      "lat": 35.036,
      "lon": 32.427,
      "alt": 30,
      "altRef": "AGL"
    },
    {
      "name": "IP",
      "lat": 35.12,
      "lon": 32.605,
      "alt": 50,
      "altRef": "AGL"
    },
    {
      "name": "KARAVOSTASI",
      "lat": 35.142,
      "lon": 32.822,
      "alt": 50,
      "altRef": "AGL"
    }
  ]
}
'''

# ============================================================
# CSS
# ============================================================
CSS = r"""
/* ============================================
   ROUTE PLANNER — chrome de l'éditeur + carte
   Monofichier ; polices embarquées ; Leaflet 1.9.4 (BSD-2)
   ============================================ */

@font-face {
  font-family: 'Stardos Stencil';
  font-weight: 700;
  font-display: swap;
  src: url('data:font/woff2;base64,__STARDOS_700__') format('woff2');
}
@font-face {
  font-family: 'Roboto Mono';
  font-weight: 400;
  font-display: swap;
  src: url('data:font/woff2;base64,__ROBOTO_MONO_400__') format('woff2');
}
@font-face {
  font-family: 'Oswald';
  font-weight: 500;
  font-display: swap;
  src: url('data:font/woff2;base64,__OSWALD_500__') format('woff2');
}
@font-face {
  font-family: 'Oswald';
  font-weight: 700;
  font-display: swap;
  src: url('data:font/woff2;base64,__OSWALD_700__') format('woff2');
}

:root {
  --f-stencil: 'Stardos Stencil', 'Impact', 'Arial Narrow Bold', sans-serif;
  --f-condensed: 'Oswald', 'Arial Narrow', sans-serif;
  --f-ui: 'Oswald', 'Arial Narrow', sans-serif;
  --f-typewriter: 'Roboto Mono', 'Courier New', 'Courier', monospace;
  --f-mono: 'Roboto Mono', 'Courier New', 'Courier', monospace;
  --amber:        #c0892a;
  --amber-dark:   #8a5e15;
  --green-radar:  #4f6b3a;
}

/* ---- Thèmes de la chrome (body[data-theme]) ---- */
body, body[data-theme="cw-nato"] {
  --paper:        #d8c9a5;
  --paper-light:  #e3d6b5;
  --paper-dark:   #b8a77c;
  --paper-edge:   #8a7a52;
  --ink:          #1f1c16;
  --ink-faded:    #463f30;
  --olive:        #4a5230;
  --olive-dark:   #2c321e;
  --olive-deep:   #1a1e10;
  --khaki:        #807454;
  --khaki-light:  #a89a72;
  --rust:         #7a3a20;
  --red-stamp:    #a83524;
  --red-faded:    #c4574a;
}
body[data-theme="cw-soviet"] {
  --paper:        #d8c479;
  --paper-light:  #e8d690;
  --paper-dark:   #b8a64a;
  --paper-edge:   #8a7a30;
  --ink:          #1f1c16;
  --ink-faded:    #463f30;
  --olive:        #2a3a5a;
  --olive-dark:   #1a2540;
  --olive-deep:   #0e1830;
  --khaki:        #3a4a2e;
  --khaki-light:  #5a6a48;
  --rust:         #5e1414;
  --red-stamp:    #841e1e;
  --red-faded:    #a04040;
}
body[data-theme="modern-nato"] {
  --paper:        #e8e3d8;
  --paper-light:  #f0ece2;
  --paper-dark:   #c8c0b0;
  --paper-edge:   #948c7c;
  --ink:          #15181c;
  --ink-faded:    #3a4048;
  --olive:        #2a3038;
  --olive-dark:   #1c2026;
  --olive-deep:   #0e1014;
  --khaki:        #5c6b7a;
  --khaki-light:  #7a8a98;
  --rust:         #2a2a2a;
  --red-stamp:    #1a1a1a;
  --red-faded:    #4a4a4a;
}
body[data-theme="modern-east"] {
  --paper:        #cdc6b8;
  --paper-light:  #ddd6c8;
  --paper-dark:   #ada69a;
  --paper-edge:   #7a7466;
  --ink:          #1a1610;
  --ink-faded:    #3d3024;
  --olive:        #3d3024;
  --olive-dark:   #2a2018;
  --olive-deep:   #1a140e;
  --khaki:        #4a5238;
  --khaki-light:  #6a7256;
  --rust:         #5a1a1a;
  --red-stamp:    #7a2424;
  --red-faded:    #a04040;
}

*, *::before, *::after { box-sizing: border-box; }
html, body { height: 100%; margin: 0; overscroll-behavior: none; }
html { -webkit-text-size-adjust: 100%; }
body {
  background: var(--olive-deep); color: var(--paper);
  font-family: var(--f-ui); font-weight: 500;
  -webkit-font-smoothing: antialiased; -webkit-tap-highlight-color: transparent;
}
button, input, select { font: inherit; }

/* ---------- barre ---------- */
.toolbar {
  position: fixed; top: 0; left: 0; right: 0; height: 56px; z-index: 1000;
  background: linear-gradient(180deg, var(--olive-dark) 0%, var(--olive-deep) 100%);
  border-bottom: 2px solid var(--amber-dark); box-shadow: 0 4px 12px rgba(0,0,0,.4);
  display: flex; align-items: center; gap: 8px; padding: 0 14px;
  padding-left: max(14px, env(safe-area-inset-left)); padding-right: max(14px, env(safe-area-inset-right));
  overflow-x: auto; overflow-y: hidden; scrollbar-width: none; white-space: nowrap;
}
.toolbar::-webkit-scrollbar { display: none; }
.tb-mark { font-family: var(--f-stencil); font-weight: 700; letter-spacing: 2px; color: var(--paper-light); font-size: 15px;
  display: inline-flex; align-items: center; gap: 8px; padding-right: 12px; border-right: 1px solid var(--khaki); height: 28px; flex: none; }
.tb-mark::before { content: ''; width: 8px; height: 8px; border-radius: 50%; background: var(--amber-dark); }
.tb-group { display: inline-flex; flex: none; }
.tb-btn, .tb-sel {
  font-family: var(--f-ui); font-weight: 700; letter-spacing: 1.5px; font-size: 12px; text-transform: uppercase;
  background: transparent; color: var(--paper); border: 1px solid var(--khaki); height: 40px; min-width: 44px;
  padding: 0 12px; cursor: pointer; display: inline-flex; align-items: center; justify-content: center; gap: 6px; flex: none;
}
.tb-group .tb-btn + .tb-btn { border-left: none; }
.tb-btn.on { background: var(--amber-dark); color: var(--paper-light); border-color: var(--amber); box-shadow: inset 0 -3px 0 var(--amber); }
.tb-btn:hover, .tb-btn:focus-visible { border-color: var(--amber); outline: none; }
.tb-btn:not(.on):hover, .tb-btn:not(.on):focus-visible { background: var(--olive); color: var(--amber); }
.tb-btn:active { transform: translateY(1px); }
.tb-btn:disabled { opacity: .35; cursor: not-allowed; pointer-events: none; }
.tb-btn.danger:hover { background: var(--rust); border-color: var(--red-faded); color: var(--paper-light); }
.tb-btn svg { width: 16px; height: 16px; flex-shrink: 0; }
.tb-btn .tb-btn-label.solo { display: none; }
.tb-sel { color: var(--amber); border-color: var(--amber-dark); padding-right: 30px; appearance: none; -webkit-appearance: none;
  background: var(--olive-dark) url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='6'%3E%3Cpath d='M1 1l4 4 4-4' fill='none' stroke='%23c0892a' stroke-width='1.5'/%3E%3C/svg%3E") no-repeat right 11px center; }
.tb-sel:hover, .tb-sel:focus-visible { border-color: var(--amber); outline: none; }
.tb-sel option { background: var(--olive-dark); color: var(--paper); font-weight: 500; }
.leaflet-bar a, .leaflet-bar a:hover { font-family: var(--f-ui); font-weight: 700; }
.tb-label { font-size: 10px; font-weight: 500; letter-spacing: 1.5px; color: var(--khaki-light); text-transform: uppercase; flex: none; margin-left: 4px; }
.tb-sep { width: 1px; height: 28px; background: var(--khaki); opacity: .6; flex: none; margin: 0 2px; }
.tb-btn.primary { border-color: var(--amber); color: var(--amber); }
.tb-lang-btn {
  background: transparent; border: 1px solid var(--khaki); color: var(--paper); height: 40px; min-width: 44px; padding: 0 10px;
  cursor: pointer; display: inline-flex; align-items: center; justify-content: center; font-size: 18px; line-height: 1; flex: none;
}
.tb-lang-btn:hover, .tb-lang-btn:focus-visible { background: var(--olive); border-color: var(--amber); outline: none; }
.tb-lang-btn:active { transform: translateY(1px); }

/* ---------- application ---------- */
.app { position: fixed; top: 56px; bottom: 0; left: 0; right: 0; display: grid; grid-template-columns: 440px 1fr; }
.app > .panel { order: -1; }
.mapwrap { position: relative; z-index: 0; min-width: 0; border-left: 2px solid var(--amber-dark); }
#map { position: absolute; inset: 0; background: #e8dfc6; }
#map.grid-only { background:
  radial-gradient(ellipse at 30% 20%, rgba(255,255,255,.35), transparent 60%),
  repeating-linear-gradient(0deg, rgba(120,100,60,.035) 0 2px, transparent 2px 5px), #e6dcc2; }
#map.grid-only .leaflet-tile-pane { visibility: hidden; }
.panel { overflow-y: auto; padding: 16px; background: var(--olive-deep); counter-reset: sec; }

/* bandeau de repli */
.fallback { position: absolute; z-index: 600; left: 56px; top: 12px; max-width: calc(100% - 180px);
  background: rgba(31,28,22,.88); color: var(--paper-light); border-left: 3px solid var(--red-stamp);
  font-size: 12px; letter-spacing: .5px; padding: 8px 12px; display: none; }
.fallback.show { display: block; }

/* ---------- panneau ---------- */
.ed-section { border: 1px solid var(--khaki); background: rgba(20,24,12,.5); margin-bottom: 14px; min-width: 0; }
.ed-head { font-family: var(--f-stencil); font-weight: 700; color: var(--amber); letter-spacing: 1.5px; font-size: 14px;
  padding: 12px 14px; border-bottom: 1px solid var(--khaki); background: linear-gradient(90deg, rgba(74,82,48,.55), transparent);
  display: flex; justify-content: space-between; align-items: center; }
.ed-title::before { counter-increment: sec; content: counter(sec, decimal-leading-zero) ' \2591  '; }
.ed-head small { font-family: var(--f-ui); font-weight: 500; color: var(--khaki-light); font-size: 11px; letter-spacing: 1px; }
.ed-body { padding: 12px 14px; }
.lbl { display: block; font-size: 10.5px; letter-spacing: 1.5px; color: var(--amber); text-transform: uppercase; font-weight: 700; margin: 0 0 6px; }
.lbl::before { content: '► '; font-size: 8px; color: var(--amber-dark); }
.in { background: rgba(216,201,165,.92); border: 1px solid var(--khaki); border-left: 3px solid var(--amber-dark);
  font-family: var(--f-typewriter); font-weight: 400; font-size: 13px; color: #1f1c16; padding: 8px 9px; min-height: 40px; width: 100%; min-width: 0; border-radius: 0; }
.in::placeholder { color: rgba(31,28,22,.45); }
.in:focus { outline: none; border-left-color: var(--red-stamp); background: #ece0c2; box-shadow: 0 0 0 1px var(--amber); }
select.in { appearance: none; -webkit-appearance: none; padding-right: 22px;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='6'%3E%3Cpath d='M1 1l4 4 4-4' fill='none' stroke='%231f1c16' stroke-width='1.5'/%3E%3C/svg%3E");
  background-repeat: no-repeat; background-position: right 7px center; }
.rn { margin-bottom: 14px; }

.pt-row { display: grid; grid-template-columns: 30px 1fr 84px 76px 34px; gap: 6px; align-items: center; margin-bottom: 6px; }
.pt-row.sel .pt-num { background: var(--amber-dark); color: var(--paper-light); }
.pt-num { font-family: var(--f-stencil); font-weight: 700; color: var(--paper); border: 1px solid var(--khaki); height: 40px; background: transparent; padding: 0;
  display: flex; align-items: center; justify-content: center; font-size: 13px; cursor: pointer; }
.pt-del { height: 40px; border: 1px solid var(--khaki); background: transparent; color: var(--khaki-light); cursor: pointer; font-size: 16px; padding: 0; }
.pt-del:hover, .pt-del:focus-visible { border-color: var(--red-faded); color: var(--paper-light); background: var(--rust); outline: none; }
.pt-head { display: grid; grid-template-columns: 30px 1fr 84px 76px 34px; gap: 6px; margin-bottom: 4px; }
.pt-head span { font-size: 9.5px; letter-spacing: 1.2px; color: var(--khaki-light); text-transform: uppercase; min-width: 0; }
.hint { font-size: 11.5px; color: var(--khaki-light); letter-spacing: .3px; line-height: 1.45; margin: 8px 0 0; }
.ed-warn { font-size: 11px; letter-spacing: 1px; color: var(--amber); border-left: 3px solid var(--red-stamp); background: rgba(0,0,0,.18);
  padding: 5px 8px; margin: 6px 0 12px; }
.ed-warn[hidden] { display: none; }

.hdg { display: flex; gap: 8px; align-items: end; margin-bottom: 12px; flex-wrap: wrap; }
.hdg .tb-group .tb-btn { height: 40px; }
.hdg .decl { width: 110px; }
.hdg + .hint { margin: -4px 0 12px; }

/* fiche papier */
.sheet { background: var(--paper-light); color: #1f1c16; box-shadow: 0 2px 0 var(--paper-edge), 0 8px 18px rgba(0,0,0,.35); }
.sheet-top { background: #1f1c16; color: #f0e8d6; font-weight: 700; letter-spacing: 2px; font-size: 11px; padding: 6px 12px;
  display: flex; justify-content: space-between; }
table.nav { width: 100%; border-collapse: collapse; font-family: var(--f-mono); font-weight: 400; font-size: 12px; }
table.nav th { font-family: var(--f-ui); font-weight: 700; font-size: 10px; letter-spacing: 1.2px; text-align: left; padding: 6px 6px;
  border-bottom: 2px solid #1f1c16; text-transform: uppercase; }
table.nav td { padding: 5px 6px; border-bottom: 1px solid rgba(31,28,22,.18); vertical-align: top; }
table.nav tr.leg td { background: rgba(31,28,22,.06); color: #463f30; font-size: 11.5px; }
table.nav td.n { font-family: var(--f-stencil); font-weight: 700; width: 26px; }
table.nav td.nm { font-family: var(--f-ui); font-weight: 700; letter-spacing: .5px; font-size: 12.5px; overflow-wrap: anywhere; }
table.nav .co { display: block; font-size: 11.5px; }
table.nav .co.alt { font-family: var(--f-mono); font-weight: 400; letter-spacing: 0; color: #463f30; }
table.nav .co.dms { color: #463f30; }
table.nav td.r { text-align: right; white-space: nowrap; }
.total { display: flex; justify-content: space-between; padding: 8px 12px; font-weight: 700; letter-spacing: 1.5px; font-size: 12px;
  border-top: 2px solid #1f1c16; }
.total b { font-family: var(--f-mono); font-weight: 400; font-size: 13px; letter-spacing: 0; }

.actions { display: flex; gap: 8px; margin-top: 14px; flex-wrap: wrap; }

/* ---------- carte : marqueurs et étiquettes ---------- */
.wp-icon { width: 30px; height: 30px; }
.wp-dot { width: 30px; height: 30px; border-radius: 50%; border: 3px solid var(--route); background: rgba(240,232,214,.92);
  font-family: var(--f-stencil); font-weight: 700; color: var(--route); display: flex; align-items: center; justify-content: center;
  font-size: 13px; box-shadow: 0 0 0 2px rgba(31,28,22,.55); }
.wp-dot.sel { background: var(--route); color: #f0e8d6; }
.wp-name { position: absolute; left: 34px; top: 2px; white-space: nowrap; font-family: var(--f-ui); font-weight: 700; font-size: 12px;
  letter-spacing: 1px; color: #1f1c16; background: rgba(240,232,214,.88); padding: 1px 6px; border-left: 3px solid var(--route); }
.leg-label { white-space: nowrap; font-family: var(--f-mono); font-size: 11.5px; font-weight: 400; color: #f0e8d6; background: rgba(31,28,22,.86);
  padding: 2px 6px; transform: translate(-50%, -50%); display: inline-block; border: 1px solid var(--route); }
.leg-label-icon { width: 0; height: 0; }
.ins-icon { width: 18px; height: 18px; }
.ins { width: 18px; height: 18px; border-radius: 50%; background: #f0e8d6; border: 2px solid var(--route); color: var(--route); box-shadow: 0 0 0 1px rgba(31,28,22,.6);
  font-weight: 700; font-size: 13px; line-height: 13px; text-align: center; }
.mgrs-canvas { position: absolute; left: 0; top: 0; pointer-events: none; }
.leaflet-control-attribution { font-family: var(--f-ui); font-weight: 500; font-size: 10px !important; background: rgba(240,232,214,.8) !important; }
.leaflet-container { font-family: var(--f-ui); }
body, body[data-theme="cw-nato"] { --route: #a83524; }
body[data-theme="cw-soviet"] { --route: #841e1e; }
body[data-theme="modern-nato"] { --route: #b03a2e; }
body[data-theme="modern-east"] { --route: #7a2424; }

/* ---------- toast ---------- */
.toast {
  position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%) translateY(100px);
  background: var(--olive-dark); border: 1px solid var(--amber); color: var(--paper);
  font-family: var(--f-ui); font-weight: 700; letter-spacing: 2px; text-transform: uppercase; font-size: 12px;
  padding: 10px 20px; z-index: 20000; opacity: 0; transition: all .3s ease; pointer-events: none;
  box-shadow: 0 4px 16px rgba(0,0,0,.6); max-width: 92vw; text-align: center;
}
.toast.show { opacity: 1; transform: translateX(-50%) translateY(0); pointer-events: auto; }

/* ---------- étiquettes des boutons : seulement en très grand écran ---------- */
@media (min-width: 1801px) {
  .tb-btn .tb-btn-label.solo { display: inline; }
}

/* ---------- tablette portrait, téléphone ---------- */
@media (max-width: 1099px) {
  .app { position: static; display: block; padding-top: 56px; }
  .mapwrap { height: 58vh; min-height: 340px; border-left: none; border-bottom: 2px solid var(--amber-dark); }
  .app > .panel { order: 0; }
  .panel { overflow: visible; }
  /* Barre du haut : une seule ligne qui défile au doigt ; un fondu signale le bord qui déborde */
  .toolbar {
    --fade-w: 22px; --fade-gap: 8px;
    flex-wrap: nowrap; -webkit-overflow-scrolling: touch; overscroll-behavior-x: contain; touch-action: pan-x;
  }
  .toolbar > * { flex-shrink: 0; }
  .toolbar::before, .toolbar::after {
    content: ''; position: sticky; flex: 0 0 var(--fade-w); width: var(--fade-w); align-self: stretch;
    pointer-events: none; opacity: 0; transition: opacity .15s; z-index: 2;
  }
  .toolbar::before { left: 0; margin-right: calc(-1 * (var(--fade-w) + var(--fade-gap))); background: linear-gradient(90deg, rgba(0,0,0,.55), transparent); }
  .toolbar::after { right: 0; margin-left: calc(-1 * (var(--fade-w) + var(--fade-gap))); background: linear-gradient(270deg, rgba(0,0,0,.55), transparent); }
  .toolbar.fade-l::before, .toolbar.fade-r::after { opacity: 1; }
}
@media (max-width: 520px) {
  .pt-row, .pt-head { grid-template-columns: 28px 1fr 62px 80px 30px; gap: 4px; }
  .pt-row select.in { padding: 8px 18px 8px 6px; font-size: 12px; background-position: right 5px center; }
  .panel { padding: 10px; }
  table.nav { font-size: 11px; }
  .tb-btn { padding: 0 8px; min-width: 40px; }
}
"""
CSS = CSS.replace('__STARDOS_700__', A['STARDOS_700'])
CSS = CSS.replace('__OSWALD_500__', A['OSWALD_500'])
CSS = CSS.replace('__OSWALD_700__', A['OSWALD_700'])
CSS = CSS.replace('__ROBOTO_MONO_400__', A['ROBOTO_MONO_400'])

# ============================================================
# HTML
# ============================================================
HTML = r"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0, viewport-fit=cover">
<meta name="theme-color" content="#1a1e10">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<title>Route Planner</title>
<!-- Leaflet 1.9.4 (BSD-2-Clause) — embarqué -->
<style>__LIB_LEAFLET_CSS__</style>
<style>
__CSS__
</style>
<script>__LIB_LEAFLET__</script>
</head>
<body data-theme="cw-nato">

<!-- ===== BARRE ===== -->
<header class="toolbar" role="toolbar" aria-label="Route Planner" data-i18n-aria-label="app.title">
  <span class="tb-mark" data-i18n="app.short">R·P</span>
  <span class="tb-label" data-i18n="tb.layer">Fond</span>
  <select class="tb-sel" id="layer" data-i18n-aria-label="tb.layer" aria-label="Fond">
    <option value="dcs" data-i18n="layer.dcs">Carte DCS</option>
    <option value="topo" data-i18n="layer.topo">Topographique</option>
    <option value="sat" data-i18n="layer.sat">Satellite</option>
    <option value="grid" data-i18n="layer.grid">Grille seule</option>
  </select>
  <button type="button" class="tb-btn" id="btn-grid" aria-pressed="true" data-i18n="tb.grid" data-i18n-title="tb.grid" title="Grille MGRS">Grille MGRS</button>
  <span class="tb-sep"></span>
  <span class="tb-label" data-i18n="tb.theatre">Théâtre</span>
  <select class="tb-sel" id="theatre" data-i18n-aria-label="tb.theatre" aria-label="Théâtre"></select>
  <span class="tb-sep"></span>
  <span class="tb-group" role="group"><button type="button" class="tb-btn" data-dist="km" aria-pressed="false" data-i18n="u.km">km</button><button type="button" class="tb-btn" data-dist="nm" aria-pressed="false" data-i18n="u.nm">NM</button></span>
  <span class="tb-group" role="group"><button type="button" class="tb-btn" data-alt="m" aria-pressed="false" data-i18n="u.m">m</button><button type="button" class="tb-btn" data-alt="ft" aria-pressed="false" data-i18n="u.ft">ft</button></span>
  <span class="tb-sep"></span>
  <button type="button" class="tb-btn" id="btn-open" data-i18n-title="tb.open.tip" title="Ouvrir une route" data-i18n-aria-label="tb.open.tip" aria-label="Ouvrir une route">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 15V3M7 8l5-5 5 5M5 21h14"/></svg>
    <span class="tb-btn-label solo" data-i18n="tb.open">Ouvrir</span></button>
  <input type="file" id="file-open" accept=".json,application/json" hidden>
  <button type="button" class="tb-btn" id="btn-save" data-i18n-title="tb.save.tip" title="Enregistrer la route (JSON)" data-i18n-aria-label="tb.save.tip" aria-label="Enregistrer la route (JSON)">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 3h11l3 3v15H5zM8 3v6h8V3M8 21v-7h8v7"/></svg>
    <span class="tb-btn-label solo" data-i18n="tb.save">Enregistrer</span></button>
  <button type="button" class="tb-btn" id="btn-example" data-i18n-title="tb.example.tip" title="Charger l'exemple" data-i18n-aria-label="tb.example.tip" aria-label="Charger l'exemple">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="8" y1="13" x2="16" y2="13"/><line x1="8" y1="17" x2="16" y2="17"/></svg>
    <span class="tb-btn-label solo" data-i18n="tb.example">Exemple</span></button>
  <button type="button" class="tb-btn danger" id="btn-clear" data-i18n-title="tb.clear.tip" title="Effacer la route" data-i18n-aria-label="tb.clear.tip" aria-label="Effacer la route">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 7h16M9 7V4h6v3M6 7l1 14h10l1-14"/></svg>
    <span class="tb-btn-label solo" data-i18n="tb.clear">Effacer</span></button>
  <select class="tb-sel" id="theme" data-i18n-title="tb.theme.tip" title="Thème graphique" data-i18n-aria-label="tb.theme.tip" aria-label="Thème graphique">
    <option value="cw-nato" data-i18n="theme.cw-nato">Cold War OTAN</option>
    <option value="cw-soviet" data-i18n="theme.cw-soviet">Cold War Soviétique</option>
    <option value="modern-nato" data-i18n="theme.modern-nato">OTAN moderne</option>
    <option value="modern-east" data-i18n="theme.modern-east">Bloc Est moderne</option>
  </select>
  <button type="button" class="tb-lang-btn" id="btn-lang" data-i18n-title="tb.lang.tip" title="Switch language / Changer de langue">🇬🇧</button>
</header>

<!-- ===== APP ===== -->
<main class="app" id="app">
  <section class="mapwrap">
    <div id="map"></div>
    <div class="fallback" id="fallback" role="status" data-i18n="fallback">Fond indisponible — grille seule</div>
  </section>
  <aside class="panel" id="panel">
    <div class="ed-section" data-section="route">
      <div class="ed-head"><span class="ed-title" data-i18n="sec.route">Route</span><small id="pt-count"></small></div>
      <div class="ed-body">
        <div class="rn">
          <label class="lbl" for="route-name" data-i18n="f.name">Nom de la route</label>
          <input class="in" id="route-name" type="text" maxlength="60" autocomplete="off" spellcheck="false">
        </div>
        <div class="pt-head"><span data-i18n="th.no">N°</span><span data-i18n="th.name">Nom</span><span id="alt-unit"></span><span data-i18n="th.ref">Réf.</span><span></span></div>
        <div id="pts"></div>
        <p class="hint" data-i18n="help.route">Touchez la carte pour ajouter un point ; glissez un point pour le déplacer ; le « + » d'une branche insère un point.</p>
      </div>
    </div>
    <div class="ed-section" data-section="nav">
      <div class="ed-head"><span class="ed-title" data-i18n="sec.nav">Navigation</span></div>
      <div class="ed-body">
        <div class="hdg">
          <div><div class="lbl" data-i18n="f.ref">Cap</div><span class="tb-group" role="group"><button type="button" class="tb-btn" data-ref="true" aria-pressed="true" data-i18n="ref.true">Vrai</button><button type="button" class="tb-btn" data-ref="mag" aria-pressed="false" data-i18n="ref.mag">Magnétique</button></span></div>
          <div class="decl"><label class="lbl" for="decl" data-i18n="f.decl">Déclinaison (°)</label><input class="in" id="decl" type="text" inputmode="decimal" autocomplete="off" spellcheck="false" data-i18n-placeholder="f.decl.ph" placeholder="+4,5"></div>
        </div>
        <p class="hint" data-i18n="nav.decl.help"></p>
        <div class="ed-warn" id="decl-warn" role="alert" hidden data-i18n="nav.decl.warn"></div>
        <div class="sheet">
          <div class="sheet-top"><span id="nav-title"></span></div>
          <table class="nav">
            <thead><tr><th scope="col" data-i18n="nav.th.no">N°</th><th scope="col" data-i18n="nav.th.pt">Point · alt.</th><th scope="col" colspan="2" data-i18n="nav.th.co">MGRS · DMS / cap · distance</th></tr></thead>
            <tbody id="nav-body"></tbody>
          </table>
          <div class="total"><span data-i18n="nav.total">TOTAL</span><b id="nav-total"></b></div>
        </div>
        <div class="actions">
          <button type="button" class="tb-btn primary" id="btn-handoff" data-i18n="btn.handoff">→ Vers la datacard</button>
          <button type="button" class="tb-btn" id="btn-export" data-i18n="btn.export">Exporter JSON</button>
        </div>
      </div>
    </div>
  </aside>
</main>

<div class="toast" id="toast" role="status" aria-live="polite"></div>

<script>
__APP_JS__
</script>

</body>
</html>
"""

# ============================================================
# JS
# ============================================================
# Bloc de coordonnées et de branche du Datacard Generator, recopié OCTET POUR OCTET
# (de « const NAV_R_KM » à « /* Nombre lisible d'un champ Cap » exclu), puis sa fonction readNum.
GEO_BLOCK = r"""const NAV_R_KM = 6371.0088;
const NAV_NM_KM = 1.852;

const WGS_A = 6378137;
const WGS_F = 1 / 298.257223563;
const UTM_K0 = 0.9996;
const UTM_N = WGS_F / (2 - WGS_F);
const UTM_A = WGS_A / (1 + UTM_N) * (1 + UTM_N * UTM_N / 4 + Math.pow(UTM_N, 4) / 64);
const UTM_ALPHA = (function (n) {
  const n2 = n * n, n3 = n2 * n, n4 = n3 * n;
  return [
    n / 2 - 2 * n2 / 3 + 5 * n3 / 16 + 41 * n4 / 180,
    13 * n2 / 48 - 3 * n3 / 5 + 557 * n4 / 1440,
    61 * n3 / 240 - 103 * n4 / 140,
    49561 * n4 / 161280
  ];
})(UTM_N);
const UTM_BETA = (function (n) {
  const n2 = n * n, n3 = n2 * n, n4 = n3 * n;
  return [
    n / 2 - 2 * n2 / 3 + 37 * n3 / 96 - n4 / 360,
    n2 / 48 + n3 / 15 - 437 * n4 / 1440,
    17 * n3 / 480 - 37 * n4 / 840,
    4397 * n4 / 161280
  ];
})(UTM_N);
const UTM_DELTA = (function (n) {
  const n2 = n * n, n3 = n2 * n, n4 = n3 * n;
  return [
    2 * n - 2 * n2 / 3 - 2 * n3 + 116 * n4 / 45,
    7 * n2 / 3 - 8 * n3 / 5 - 227 * n4 / 45,
    56 * n3 / 15 - 136 * n4 / 35,
    4279 * n4 / 630
  ];
})(UTM_N);

const MGRS_BANDS = 'CDEFGHJKLMNPQRSTUVWX';
const MGRS_BAND_MIN_N = [1100000, 2000000, 2800000, 3700000, 4600000, 5500000, 6400000, 7300000, 8200000, 9100000,
  0, 800000, 1700000, 2600000, 3500000, 4400000, 5300000, 6200000, 7000000, 7900000];
const MGRS_COLS = 'ABCDEFGHJKLMNPQRSTUVWXYZ';   /* 24 lettres, sans I ni O */
const MGRS_ROWS = 'ABCDEFGHJKLMNPQRSTUV';       /* 20 lettres, sans I ni O */

function utmZoneFor(lat, lon) {
  let z = Math.floor((lon + 180) / 6) + 1;
  if (z < 1) z = 1;
  if (z > 60) z = 60;
  if (lat >= 56 && lat < 64 && lon >= 3 && lon < 12) z = 32;
  if (lat >= 72 && lat < 84) {
    if (lon >= 0 && lon < 9) z = 31;
    else if (lon >= 9 && lon < 21) z = 33;
    else if (lon >= 21 && lon < 33) z = 35;
    else if (lon >= 33 && lon < 42) z = 37;
  }
  return z;
}

/* lat/lon (degrés) → { zone, north, e, n } ; zone imposée facultative */
function llToUtm(lat, lon, zone) {
  const z = zone || utmZoneFor(lat, lon);
  const lon0 = ((z - 1) * 6 - 180 + 3) * Math.PI / 180;
  const phi = lat * Math.PI / 180;
  const dl = lon * Math.PI / 180 - lon0;
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
  const north = lat >= 0;
  return { zone: z, north: north, e: 500000 + UTM_K0 * UTM_A * eta, n: (north ? 0 : 10000000) + UTM_K0 * UTM_A * xi };
}

/* UTM → { lat, lon } */
function utmToLl(zone, north, e, nn) {
  const lon0 = ((zone - 1) * 6 - 180 + 3) * Math.PI / 180;
  const xi = (nn - (north ? 0 : 10000000)) / (UTM_K0 * UTM_A);
  const eta = (e - 500000) / (UTM_K0 * UTM_A);
  let xi1 = xi, eta1 = eta;
  for (let j = 1; j <= 4; j++) {
    xi1 -= UTM_BETA[j - 1] * Math.sin(2 * j * xi) * Math.cosh(2 * j * eta);
    eta1 -= UTM_BETA[j - 1] * Math.cos(2 * j * xi) * Math.sinh(2 * j * eta);
  }
  const chi = Math.asin(Math.sin(xi1) / Math.cosh(eta1));
  let phi = chi;
  for (let j = 1; j <= 4; j++) phi += UTM_DELTA[j - 1] * Math.sin(2 * j * chi);
  const lam = lon0 + Math.atan2(Math.sinh(eta1), Math.cos(xi1));
  return { lat: phi * 180 / Math.PI, lon: lam * 180 / Math.PI };
}

function mgrsBandFor(lat) {
  if (lat < -80 || lat > 84) return '';
  let i = Math.floor((lat + 80) / 8);
  if (i > 19) i = 19;
  return MGRS_BANDS.charAt(i);
}

function mgrsSet(zone) { const s = zone % 6; return s === 0 ? 6 : s; }
function mgrsColOrigin(zone) { return 'AJSAJS'.charAt(mgrsSet(zone) - 1); }
function mgrsRowOrigin(zone) { return 'AFAFAF'.charAt(mgrsSet(zone) - 1); }

/* lat/lon → « 36S VD 47535 77241 » (10 chiffres, troncature au mètre ; 10 µm de tolérance pour les mètres entiers) ;
   '' hors de la zone UTM (80°S – 84°N) */
function toMGRS(lat, lon) {
  const band = mgrsBandFor(lat);
  if (!band) return '';
  const u = llToUtm(lat, lon);
  const e = Math.floor(u.e + 1e-5), nn = Math.floor(u.n + 1e-5);
  const col = MGRS_COLS.charAt((MGRS_COLS.indexOf(mgrsColOrigin(u.zone)) + Math.floor(e / 100000) - 1) % 24);
  const row = MGRS_ROWS.charAt((MGRS_ROWS.indexOf(mgrsRowOrigin(u.zone)) + Math.floor(nn / 100000)) % 20);
  const p5 = v => String(v % 100000).padStart(5, '0');
  return pad2(u.zone) + band + ' ' + col + row + ' ' + p5(e) + ' ' + p5(nn);
}

/* Chaîne MGRS → { lat, lon } (centre de la case, y compris celle de 1 m à 10 chiffres) ou null */
function parseMGRS(s) {
  const m = /^\s*(\d{1,2})\s*([C-HJ-NP-X])\s*([A-HJ-NP-Z])\s*([A-HJ-NP-V])\s*((?:\d\s*)*)$/i.exec(s);
  if (!m) return null;
  const zone = parseInt(m[1], 10);
  if (zone < 1 || zone > 60) return null;
  const band = m[2].toUpperCase(), colL = m[3].toUpperCase(), rowL = m[4].toUpperCase();
  if (band === 'X' && (zone === 32 || zone === 34 || zone === 36)) return null;
  const groups = m[5].trim() ? m[5].trim().split(/\s+/) : [];
  if (groups.length > 2 || (groups.length === 2 && groups[0].length !== groups[1].length)) return null;
  const digits = groups.join('');
  const k = digits.length;
  if (k < 2 || k > 10 || k % 2 !== 0) return null;
  const half = k / 2;
  const cell = Math.pow(10, 5 - half);
  const de = parseInt(digits.slice(0, half), 10) * cell + cell / 2;   /* centre de la case (1 m : demi-mètre) */
  const dn = parseInt(digits.slice(half), 10) * cell + cell / 2;
  const ci = (MGRS_COLS.indexOf(colL) - MGRS_COLS.indexOf(mgrsColOrigin(zone)) + 24) % 24;
  if (ci > 7) return null;                         /* colonne absente de cette zone */
  const e100 = (ci + 1) * 100000;
  const ri = (MGRS_ROWS.indexOf(rowL) - MGRS_ROWS.indexOf(mgrsRowOrigin(zone)) + 20) % 20;
  let n100 = ri * 100000;
  const bi = MGRS_BANDS.indexOf(band);
  while (n100 < MGRS_BAND_MIN_N[bi]) n100 += 2000000;
  const ll = utmToLl(zone, band >= 'N', e100 + de, n100 + dn);
  const south = -80 + bi * 8, north = bi === 19 ? 84 : south + 8;
  if (ll.lat < south - 0.15 || ll.lat > north + 0.15) return null;   /* la case n'est pas dans la bande annoncée */
  return ll;
}

/* Un nombre de lat/lon : degrés [minutes [secondes]] → valeur absolue en degrés, ou null */
function parseDegPart(s, maxDeg) {
  const m = /^\s*(\d+(?:\.\d+)?)\s*°?\s*(?:(\d+(?:\.\d+)?)\s*'?\s*(?:(\d+(?:\.\d+)?)\s*"?)?)?\s*$/.exec(s);
  if (!m) return null;
  const d = parseFloat(m[1]);
  const mi = m[2] != null ? parseFloat(m[2]) : null;
  const se = m[3] != null ? parseFloat(m[3]) : null;
  if (mi != null && m[1].indexOf('.') !== -1) return null;          /* degrés décimaux : ni minutes ni secondes */
  if (se != null && m[2].indexOf('.') !== -1) return null;          /* minutes décimales : pas de secondes */
  if (mi != null && mi >= 60) return null;
  if (se != null && se >= 60) return null;
  const v = d + (mi || 0) / 60 + (se || 0) / 3600;
  if (v > maxDeg) return null;
  return v;
}

/* DMS pointé : « 36.49.30N/34.44.29E », « 36.49.30N 34.44.29E », « N36.49.30/E034.44.29 » (x en majuscules) */
function parseDottedDms(x) {
  const C = '(?:([NSEW])\\s*)?(\\d{1,3})\\.(\\d{2})\\.(\\d{2})(?:\\s*([NSEW]))?';
  const m = new RegExp('^' + C + '(?:\\s*[\\/,;]\\s*|\\s+)' + C + '$').exec(x);
  if (!m) return null;
  const one = (a, b, c, d, e, maxDeg, pos, neg) => {
    if ((a ? 1 : 0) + (e ? 1 : 0) !== 1) return null;
    const h = a || e;
    if (h !== pos && h !== neg) return null;
    const dg = parseInt(b, 10), mi = parseInt(c, 10), se = parseInt(d, 10);
    if (mi >= 60 || se >= 60) return null;
    const v = dg + mi / 60 + se / 3600;
    if (v > maxDeg) return null;
    return h === neg ? -v : v;
  };
  const lat = one(m[1], m[2], m[3], m[4], m[5], 90, 'N', 'S');
  const lon = one(m[6], m[7], m[8], m[9], m[10], 180, 'E', 'W');
  return (lat == null || lon == null) ? null : { lat: lat, lon: lon };
}

function parseLatLon(s) {
  let x = s.toUpperCase().replace(/[′’´‘]/g, "'").replace(/[″”“]/g, '"').replace(/''/g, '"').replace(/[º˚]/g, '°');
  x = x.trim();
  if (!x) return null;
  const dm = parseDottedDms(x);
  if (dm) return dm;
  const letters = [];
  const re = /[NSEW]/g;
  let mm;
  while ((mm = re.exec(x)) !== null) letters.push({ ch: mm[0], i: mm.index });
  if (letters.length === 0) {
    const m = /^([+-]?\d+(?:\.\d+)?)\s*°?\s*[,;\/\s]\s*([+-]?\d+(?:\.\d+)?)\s*°?$/.exec(x);
    if (!m) return null;
    const lat = parseFloat(m[1]), lon = parseFloat(m[2]);
    if (Math.abs(lat) > 90 || Math.abs(lon) > 180) return null;
    return { lat: lat, lon: lon };
  }
  if (letters.length !== 2) return null;
  const a = letters[0], b = letters[1];
  if ('NS'.indexOf(a.ch) === -1 || 'EW'.indexOf(b.ch) === -1) return null;
  let latS, lonS;
  if (a.i === 0 && b.i < x.length - 1) { latS = x.slice(1, b.i); lonS = x.slice(b.i + 1); }          /* N35… E032… */
  else if (a.i > 0 && b.i === x.length - 1) { latS = x.slice(0, a.i); lonS = x.slice(a.i + 1, b.i); } /* 35…N 032…E */
  else return null;
  latS = latS.replace(/^[\s,;\/]+|[\s,;\/]+$/g, '');
  lonS = lonS.replace(/^[\s,;\/]+|[\s,;\/]+$/g, '');
  const la = parseDegPart(latS, 90), lo = parseDegPart(lonS, 180);
  if (la == null || lo == null) return null;
  return { lat: a.ch === 'S' ? -la : la, lon: b.ch === 'W' ? -lo : lo };
}

/* Chaîne saisie → { lat, lon } ou null (MGRS d'abord, puis latitude / longitude) */
function parseCoord(s) {
  if (typeof s !== 'string' || !s.trim()) return null;
  const g = parseMGRS(s);
  if (g) return g;
  return parseLatLon(s);
}

function fmtDms(v, pos, neg, w) {
  const h = v < 0 ? neg : pos;
  const tot = Math.round(Math.abs(v) * 3600);
  const d = Math.floor(tot / 3600), mi = Math.floor((tot % 3600) / 60), se = tot % 60;
  return h + String(d).padStart(w, '0') + '°' + pad2(mi) + "'" + pad2(se) + '"';
}
/* « N35°02'11" E032°25'29" » */
function toDMS(lat, lon) { return fmtDms(lat, 'N', 'S', 2) + ' ' + fmtDms(lon, 'E', 'W', 3); }

/* Cap initial du grand cercle (vrai, 0–360) et distance (km) entre deux points */
function legCalc(a, b) {
  const r = Math.PI / 180;
  const p1 = a.lat * r, p2 = b.lat * r, dl = (b.lon - a.lon) * r;
  const y = Math.sin(dl) * Math.cos(p2);
  const x = Math.cos(p1) * Math.sin(p2) - Math.sin(p1) * Math.cos(p2) * Math.cos(dl);
  const brg = (Math.atan2(y, x) / r + 360) % 360;
  const h = Math.sin((p2 - p1) / 2) * Math.sin((p2 - p1) / 2) + Math.cos(p1) * Math.cos(p2) * Math.sin(dl / 2) * Math.sin(dl / 2);
  const km = 2 * NAV_R_KM * Math.asin(Math.min(1, Math.sqrt(h)));
  return { brg: brg, km: km };
}

function fmtHdg(deg) {
  const n = Math.round(deg) % 360;
  return n === 0 ? '360' : String(n).padStart(3, '0');
}

/* Déclinaison saisie (« 3,5 », « -2.5 », « 3° ») → nombre, ou null si illisible */
function parseDecl(s) {
  if (typeof s !== 'string') return null;
  const m = /^\s*([+-]?\d+(?:[.,]\d+)?)\s*°?\s*$/.exec(s);
  if (!m) return null;
  const v = parseFloat(m[1].replace(',', '.'));
  return (isFinite(v) && Math.abs(v) <= 90) ? v : null;
}

/* Les lignes de la datacard qui comptent : une rangée dont aucun champ n'est rempli n'existe pas pour la navigation. */
const NAV_KEYS = ['name', 'coord', 'course', 'distance', 'altitude', 'tos', 'note'];

/* Point d'arrivée du grand cercle depuis a, au cap initial brg (vrai, °) sur km kilomètres */
function legDest(a, brg, km) {
  const r = Math.PI / 180;
  const d = km / NAV_R_KM, th = brg * r, p1 = a.lat * r, l1 = a.lon * r;
  const p2 = Math.asin(Math.sin(p1) * Math.cos(d) + Math.cos(p1) * Math.sin(d) * Math.cos(th));
  const l2 = l1 + Math.atan2(Math.sin(th) * Math.sin(d) * Math.cos(p1), Math.cos(d) - Math.sin(p1) * Math.sin(p2));
  return { lat: p2 / r, lon: ((l2 / r + 540) % 360) - 180 };
}

/* Point X tel que le cap initial de X vers b vaut brg (vrai) et la distance de X à b vaut km ; null si non convergent */
function legOrigin(b, brg, km) {
  let th = (brg + 180) % 360;
  for (let it = 0; it < 200; it++) {
    const x = legDest(b, th, km);
    const L = legCalc(x, b);
    let e = brg - L.brg;
    e = ((e + 540) % 360) - 180;
    if (Math.abs(e) < 0.00001) return x;
    th = ((th + e) % 360 + 360) % 360;
  }
  return null;
}

"""
READNUM_BLOCK = r"""/* Nombre lisible d'un champ Cap / Distance (virgule ou point décimal), sinon null */
function readNum(s) {
  if (typeof s !== 'string') return null;
  const m = /^\s*(\d+(?:[.,]\d+)?)\s*$/.exec(s);
  return m ? parseFloat(m[1].replace(',', '.')) : null;
}

"""

JS = r"""
'use strict';

/* =====================================================
   ROUTE PLANNER v1.0.0
   Une route sur une carte : caps, distances, MGRS et DMS,
   envoyés dans la navigation d'une datacard.
   Monofichier ; seules les tuiles de carte viennent du réseau.
   ===================================================== */

const KEY_STATE = 'route_state_v1';
const KEY_HANDOFF = 'route_handoff_v1';
const KEY_THEME = 'theme_v1';
const KEY_LANG = 'lang_v1';
const FORMAT_ID = 'dcs-route-v1';
const THEME_IDS = ['cw-nato', 'cw-soviet', 'modern-nato', 'modern-east'];
const LAYER_IDS = ['dcs', 'topo', 'sat', 'grid'];
const MAX_POINTS = 30;
const NM_KM = 1.852;
const FT_M = 0.3048;
const FALLBACK_MS = 4000;      /* délai avant le repli en grille seule */
const LEG_LABEL_MIN_PX = 120;  /* étiquette « cap · distance » : branche d'au moins 120 px */
const INSERT_MIN_PX = 60;      /* « + » d'insertion : branche d'au moins 60 px */
const INSERT_AT = 0.28;        /* position du « + » sur la branche */

/* Théâtres : cadrage (centre, zoom) et clé de la couche Olympus ('' : aucune) */
const THEATRES = [
  { id: 'Caucasus',           c: [43.0, 41.6],     z: 7, dcs: 'alt-caucasus' },
  { id: 'GermanyCW',          c: [51.2, 10.4],     z: 7, dcs: 'alt-GermanyCW' },
  { id: 'Syria',              c: [34.8, 35.8],     z: 7, dcs: 'alt-syria' },
  { id: 'PersianGulf',        c: [26.3, 55.6],     z: 7, dcs: 'alt-persiangulf' },
  { id: 'Normandy',           c: [49.6, 0.0],      z: 7, dcs: 'alt-Normandy' },
  { id: 'TheChannel',         c: [50.9, 1.6],      z: 8, dcs: '' },
  { id: 'Nevada',             c: [36.6, -115.5],   z: 7, dcs: 'alt-nevada' },
  { id: 'MarianaIslands',     c: [14.8, 145.4],    z: 8, dcs: 'alt-marianaislands-modern' },
  { id: 'MarianaIslandsWWII', c: [14.8, 145.4],    z: 8, dcs: 'alt-MarianaIslandsWWII' },
  { id: 'Kola',               c: [68.3, 28.5],     z: 6, dcs: '' },
  { id: 'SinaiMap',           c: [30.4, 33.2],     z: 7, dcs: '' },
  { id: 'Iraq',               c: [34.4, 42.6],     z: 7, dcs: '' },
  { id: 'Afghanistan',        c: [33.4, 66.3],     z: 7, dcs: '' },
  { id: 'Falklands',          c: [-51.7, -59.0],   z: 7, dcs: '' }
];
const THEATRE_IDS = THEATRES.map(x => x.id);

/* Couches Olympus : [minNativeZoom, maxNativeZoom, minZoom], empilées dans cet ordre (config.json d'Olympus du 24 octobre) */
const DCS_LEVELS = {
  'alt-syria':                 [[1, 15, 1], [16, 16, 16], [17, 17, 17]],
  'alt-caucasus':              [[1, 13, 1], [13, 16, 13], [16, 18, 16]],
  'alt-nevada':                [[1, 13, 1], [13, 16, 13], [16, 17, 16]],
  'alt-marianaislands-modern': [[1, 13, 1], [13, 18, 13]],
  'alt-MarianaIslandsWWII':    [[1, 13, 1], [13, 14, 13], [14, 15, 14], [15, 18, 15]],
  'alt-persiangulf':           [[1, 12, 1], [13, 14, 13], [15, 16, 15], [17, 17, 17]],
  'alt-GermanyCW':             [[1, 11, 1], [13, 13, 11], [15, 15, 13]],
  'alt-Normandy':              [[1, 11, 1], [12, 13, 12], [13, 14, 13], [14, 15, 14], [15, 17, 15]]
};
const DCS_URL = 'https://maps.dcsolympus.com/maps/{key}/{z}/{x}/{y}.png';
const TOPO_URL = 'https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png';
const SAT_URL = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}';

/* Contenu du bouton « Exemple » (document dcs-route-v1) */
const EXAMPLE_ROUTE = __EXAMPLE_ROUTE__;

/* ============= i18n FR / EN ============= */
const I18N = {
  fr: {
    'app.title': 'Route Planner',
    'app.short': 'R·P',
    'tb.layer': 'Fond',
    'layer.dcs': 'Carte DCS',
    'layer.topo': 'Topographique',
    'layer.sat': 'Satellite',
    'layer.grid': 'Grille seule',
    'layer.dcsOff': 'Carte DCS — absente de ce théâtre',
    'tb.grid': 'Grille MGRS',
    'tb.theatre': 'Théâtre',
    'u.km': 'km',
    'u.nm': 'NM',
    'u.m': 'm',
    'u.ft': 'ft',
    'tb.open': 'Ouvrir',
    'tb.open.tip': 'Ouvrir une route',
    'tb.save': 'Enregistrer',
    'tb.save.tip': 'Enregistrer la route (JSON)',
    'tb.example': 'Exemple',
    'tb.example.tip': 'Charger l\'exemple',
    'tb.clear': 'Effacer',
    'tb.clear.tip': 'Effacer la route',
    'tb.theme.tip': 'Thème graphique',
    'tb.lang.tip': 'Switch language / Changer de langue',
    'theme.cw-nato': 'Cold War OTAN',
    'theme.cw-soviet': 'Cold War Soviétique',
    'theme.modern-nato': 'OTAN moderne',
    'theme.modern-east': 'Bloc Est moderne',
    'th.Caucasus': 'Caucase',
    'th.GermanyCW': 'Allemagne (guerre froide)',
    'th.Syria': 'Syrie',
    'th.PersianGulf': 'Golfe Persique',
    'th.Normandy': 'Normandie',
    'th.TheChannel': 'Manche',
    'th.Nevada': 'Nevada',
    'th.MarianaIslands': 'Mariannes',
    'th.MarianaIslandsWWII': 'Mariannes 1944',
    'th.Kola': 'Kola',
    'th.SinaiMap': 'Sinaï',
    'th.Iraq': 'Irak',
    'th.Afghanistan': 'Afghanistan',
    'th.Falklands': 'Atlantique Sud',
    'attr.dcs': 'Carte DCS © <a href="https://github.com/Pax1601/DCSOlympus">DCS Olympus</a>',
    'attr.topo': 'Données © <a href="https://www.openstreetmap.org/copyright">contributeurs OpenStreetMap</a>, SRTM · style © <a href="https://opentopomap.org">OpenTopoMap</a> (CC-BY-SA)',
    'attr.sat': 'Esri, Maxar, Earthstar Geographics, and the GIS User Community',
    'fallback': 'Fond indisponible — grille seule',
    'sec.route': 'Route',
    'sec.points': '{n} points',
    'f.name': 'Nom de la route',
    'th.no': 'N°',
    'th.name': 'Nom',
    'th.alt': 'Alt. ({u})',
    'th.ref': 'Réf.',
    'ref.AGL': 'SOL',
    'ref.MSL': 'MER',
    'refl.AGL': 'sol',
    'refl.MSL': 'mer',
    'help.route': 'Touchez la carte pour ajouter un point\u202f; glissez un point pour le déplacer\u202f; le « + » d\'une branche insère un point.',
    'tip.insert': 'Insérer un point',
    'tip.delete': 'Supprimer',
    'sec.nav': 'Navigation',
    'f.ref': 'Cap',
    'ref.true': 'Vrai',
    'ref.mag': 'Magnétique',
    'f.decl': 'Déclinaison (°)',
    'f.decl.ph': '+4,5',
    'nav.decl.help': 'en degrés, + vers l\'Est\u202f; lue au CDU de l\'A-10C (POSINFO), au DED du F-16 (MVAR) ou à l\'HSI du F/A-18',
    'nav.decl.warn': 'Déclinaison manquante\u202f: cap vrai affiché',
    'nav.title.true': 'NAVIGATION — CAP VRAI',
    'nav.title.mag': 'NAVIGATION — CAP MAGNÉTIQUE (DÉCL. {d}°)',
    'nav.th.no': 'N°',
    'nav.th.pt': 'Point · alt.',
    'nav.th.co': 'MGRS · DMS / cap · distance',
    'nav.total': 'TOTAL',
    'btn.handoff': '→ Vers la datacard',
    'btn.export': 'Exporter JSON',
    'toast.standalone': 'Route enregistrée : ouvrez le Datacard Generator, puis Importer → Route en cours.',
    'toast.max': '30 points au plus.',
    'toast.opened': 'Route ouverte ✓',
    'toast.openedDropped': 'Route ouverte ✓ · {n} points écartés (30 au plus)',
    'zoom.in': 'Zoom avant',
    'zoom.out': 'Zoom arrière',
    'toast.saved': 'Route enregistrée ✓',
    'err.json': 'Fichier non reconnu.',
    'confirm.open': 'Remplacer la route en cours ?',
    'confirm.example': 'Charger l\'exemple à la place de la route en cours ?',
    'confirm.clear': 'Effacer la route ?'
  },
  en: {
    'app.title': 'Route Planner',
    'app.short': 'R·P',
    'tb.layer': 'Map',
    'layer.dcs': 'DCS map',
    'layer.topo': 'Topographic',
    'layer.sat': 'Satellite',
    'layer.grid': 'Grid only',
    'layer.dcsOff': 'DCS map — not available for this theatre',
    'tb.grid': 'MGRS grid',
    'tb.theatre': 'Theatre',
    'u.km': 'km',
    'u.nm': 'NM',
    'u.m': 'm',
    'u.ft': 'ft',
    'tb.open': 'Open',
    'tb.open.tip': 'Open a route',
    'tb.save': 'Save',
    'tb.save.tip': 'Save the route (JSON)',
    'tb.example': 'Example',
    'tb.example.tip': 'Load the example',
    'tb.clear': 'Clear',
    'tb.clear.tip': 'Clear the route',
    'tb.theme.tip': 'Graphic theme',
    'tb.lang.tip': 'Switch language / Changer de langue',
    'theme.cw-nato': 'Cold War NATO',
    'theme.cw-soviet': 'Cold War Soviet',
    'theme.modern-nato': 'Modern NATO',
    'theme.modern-east': 'Modern East Bloc',
    'th.Caucasus': 'Caucasus',
    'th.GermanyCW': 'Cold War Germany',
    'th.Syria': 'Syria',
    'th.PersianGulf': 'Persian Gulf',
    'th.Normandy': 'Normandy',
    'th.TheChannel': 'The Channel',
    'th.Nevada': 'Nevada',
    'th.MarianaIslands': 'Mariana Islands',
    'th.MarianaIslandsWWII': 'Mariana Islands WWII',
    'th.Kola': 'Kola',
    'th.SinaiMap': 'Sinai',
    'th.Iraq': 'Iraq',
    'th.Afghanistan': 'Afghanistan',
    'th.Falklands': 'South Atlantic',
    'attr.dcs': 'DCS map © <a href="https://github.com/Pax1601/DCSOlympus">DCS Olympus</a>',
    'attr.topo': 'Map data © <a href="https://www.openstreetmap.org/copyright">OpenStreetMap contributors</a>, SRTM · style © <a href="https://opentopomap.org">OpenTopoMap</a> (CC-BY-SA)',
    'attr.sat': 'Esri, Maxar, Earthstar Geographics, and the GIS User Community',
    'fallback': 'Map unavailable — grid only',
    'sec.route': 'Route',
    'sec.points': '{n} waypoints',
    'f.name': 'Route name',
    'th.no': 'No.',
    'th.name': 'Name',
    'th.alt': 'Alt. ({u})',
    'th.ref': 'Ref.',
    'ref.AGL': 'AGL',
    'ref.MSL': 'MSL',
    'refl.AGL': 'AGL',
    'refl.MSL': 'MSL',
    'help.route': 'Tap the map to add a waypoint; drag a waypoint to move it; a leg\'s “+” inserts a waypoint.',
    'tip.insert': 'Insert a waypoint',
    'tip.delete': 'Delete',
    'sec.nav': 'Navigation',
    'f.ref': 'Heading',
    'ref.true': 'True',
    'ref.mag': 'Magnetic',
    'f.decl': 'Variation (°)',
    'f.decl.ph': '+4.5',
    'nav.decl.help': 'in degrees, + East; read on the A-10C CDU (POSINFO), the F-16 DED (MVAR) or the F/A-18 HSI',
    'nav.decl.warn': 'Variation missing: true heading shown',
    'nav.title.true': 'NAVIGATION — TRUE HEADING',
    'nav.title.mag': 'NAVIGATION — MAGNETIC HEADING (VAR {d}°)',
    'nav.th.no': 'No.',
    'nav.th.pt': 'Waypoint · alt.',
    'nav.th.co': 'MGRS · DMS / heading · distance',
    'nav.total': 'TOTAL',
    'btn.handoff': '→ To the datacard',
    'btn.export': 'Export JSON',
    'toast.standalone': 'Route saved: open the Datacard Generator, then Import → Current route.',
    'toast.max': '30 waypoints at most.',
    'toast.opened': 'Route opened ✓',
    'toast.openedDropped': 'Route opened ✓ · {n} waypoints dropped (30 at most)',
    'zoom.in': 'Zoom in',
    'zoom.out': 'Zoom out',
    'toast.saved': 'Route saved ✓',
    'err.json': 'Unrecognised file.',
    'confirm.open': 'Replace the current route?',
    'confirm.example': 'Load the example instead of the current route?',
    'confirm.clear': 'Clear the route?'
  }
};

let CURRENT_LANG = 'fr';

function t(key, vars) {
  const dict = I18N[CURRENT_LANG] || I18N.fr;
  let s;
  if (key in dict) s = dict[key];
  else if (key in I18N.fr) s = I18N.fr[key];
  else { console.warn('[i18n] missing key:', key); s = key; }
  if (vars) Object.keys(vars).forEach(k => { s = s.split('{' + k + '}').join(String(vars[k])); });
  return s;
}

function initLang() {
  /* Lecture seule : la clé de langue n'est écrite que quand la personne change de langue. */
  try {
    const stored = localStorage.getItem(KEY_LANG);
    if (stored === 'fr' || stored === 'en') { CURRENT_LANG = stored; document.documentElement.lang = CURRENT_LANG; return; }
  } catch (e) { /* localStorage indisponible */ }
  const nav = (navigator.language || 'fr').toLowerCase();
  CURRENT_LANG = nav.startsWith('fr') ? 'fr' : 'en';
  document.documentElement.lang = CURRENT_LANG;
}

function applyI18nStatic() {
  document.querySelectorAll('[data-i18n]').forEach(el => { el.textContent = t(el.dataset.i18n); });
  document.querySelectorAll('[data-i18n-title]').forEach(el => { el.title = t(el.dataset.i18nTitle); });
  document.querySelectorAll('[data-i18n-placeholder]').forEach(el => { el.placeholder = t(el.dataset.i18nPlaceholder); });
  document.querySelectorAll('[data-i18n-aria-label]').forEach(el => { el.setAttribute('aria-label', t(el.dataset.i18nAriaLabel)); });
  document.title = t('app.title');
}

function updateFlagButton() {
  const btn = document.getElementById('btn-lang');
  if (btn) btn.textContent = CURRENT_LANG === 'fr' ? '🇬🇧' : '🇫🇷';
}

/* ============= UTILITAIRES ============= */
function escapeHtml(str) {
  return String(str == null ? '' : str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}
const esc = escapeHtml;

function hasText(v) { return typeof v === 'string' && v.trim() !== ''; }
function str(v) {
  if (typeof v === 'string') return v;
  if (typeof v === 'number' && isFinite(v)) return String(v);
  return '';
}
function pad2(n) { return String(n).padStart(2, '0'); }
const $ = id => document.getElementById(id);

function showToast(msg) {
  const el = $('toast');
  el.textContent = msg;
  el.classList.add('show');
  clearTimeout(showToast._h);
  showToast._h = setTimeout(() => el.classList.remove('show'), 2200);
}

/* ============= COORDONNÉES DE NAVIGATION ============= */
/* Recopié à l'identique du Datacard Generator : constantes WGS84, UTM, MGRS, lectures, DMS, cap et distance. */
@@GEO_BLOCK@@
@@READNUM_BLOCK@@
/* ============= MODÈLE ============= */
function defaultState() {
  return {
    format: FORMAT_ID, name: '', theatre: 'Caucasus',
    units: { distance: 'km', altitude: 'm' },
    navDisplay: { ref: 'true', decl: '' },
    points: [],
    ui: { layer: 'topo', grid: true }
  };
}

let S = defaultState();
let sel = -1;                 /* point sélectionné (non enregistré) */

function r7(v) { return Math.round(v * 1e7) / 1e7; }

function validCoord(lat, lon) {
  return typeof lat === 'number' && typeof lon === 'number' && isFinite(lat) && isFinite(lon) && Math.abs(lat) <= 90 && Math.abs(lon) <= 180;
}

/* WP<k> : le plus petit entier k ≥ 0 qu'aucun point ne porte déjà sous la forme WP<k> */
function nextName(points, rank) {
  const used = {};
  points.forEach(p => { used[p.name] = true; });
  let k = rank > 0 ? rank : 0;
  while (used['WP' + k]) k++;
  return 'WP' + k;
}

/* Un objet lu (fichier ou stockage) → { route, dropped } ; null si ce n'est pas une route dcs-route-v1.
   Un point dont lat ou lon n'est pas un nombre dans les bornes est écarté ; au-delà de 30 points, le reste est écarté
   (dropped les compte) ; les champs absents prennent leurs défauts. */
function parseRoute(src) {
  if (!src || typeof src !== 'object' || Array.isArray(src) || src.format !== FORMAT_ID || !Array.isArray(src.points)) return null;
  const d = defaultState();
  const un = (src.units && typeof src.units === 'object') ? src.units : {};
  const nd = (src.navDisplay && typeof src.navDisplay === 'object') ? src.navDisplay : {};
  const route = {
    format: FORMAT_ID,
    name: str(src.name),
    theatre: THEATRE_IDS.indexOf(src.theatre) !== -1 ? src.theatre : d.theatre,
    units: { distance: un.distance === 'nm' ? 'nm' : 'km', altitude: un.altitude === 'ft' ? 'ft' : 'm' },
    navDisplay: { ref: nd.ref === 'mag' ? 'mag' : 'true', decl: str(nd.decl) },
    points: []
  };
  let dropped = 0;
  src.points.forEach(p => {
    if (!p || typeof p !== 'object' || !validCoord(p.lat, p.lon)) return;
    if (route.points.length >= MAX_POINTS) { dropped++; return; }
    route.points.push({
      name: typeof p.name === 'string' ? p.name : nextName(route.points, route.points.length),
      lat: r7(p.lat), lon: r7(p.lon),
      alt: (typeof p.alt === 'number' && isFinite(p.alt)) ? p.alt : 0,
      altRef: p.altRef === 'MSL' ? 'MSL' : 'AGL'
    });
  });
  return { route: route, dropped: dropped };
}

function persistState() {
  try { localStorage.setItem(KEY_STATE, JSON.stringify(S)); } catch (e) { /* quota ou stockage indisponible */ }
}

function loadState() {
  try {
    const raw = localStorage.getItem(KEY_STATE);
    if (raw) {
      const o = JSON.parse(raw);
      const res = parseRoute(o);
      if (res) {
        const ui = (o.ui && typeof o.ui === 'object') ? o.ui : {};
        S = Object.assign(res.route, { ui: { layer: LAYER_IDS.indexOf(ui.layer) !== -1 ? ui.layer : 'topo', grid: typeof ui.grid === 'boolean' ? ui.grid : true } });
        return;
      }
    }
  } catch (e) { /* état illisible : route neuve */ }
  S = defaultState();
}

/* Le fichier exporté : l'état sans « ui » */
function exportObject() {
  return {
    format: FORMAT_ID, name: S.name, theatre: S.theatre,
    units: { distance: S.units.distance, altitude: S.units.altitude },
    navDisplay: { ref: S.navDisplay.ref, decl: S.navDisplay.decl },
    points: S.points.map(p => ({ name: p.name, lat: p.lat, lon: p.lon, alt: p.alt, altRef: p.altRef }))
  };
}

function theatreOf(id) { return THEATRES.find(x => x.id === id) || THEATRES[0]; }
function dcsKey() { return theatreOf(S.theatre).dcs; }

/* « Carte DCS » choisie sur un théâtre qui n'en a pas : la couche passe en Topographique */
function resolveLayer() {
  if (S.ui.layer === 'dcs' && !dcsKey()) S.ui.layer = 'topo';
}

/* ============= UNITÉS, DISTANCES, CAPS ============= */
function declValue() { return S.navDisplay.ref === 'mag' ? parseDecl(S.navDisplay.decl) : null; }

function decimal(s) { return CURRENT_LANG === 'fr' ? s.replace('.', ',') : s; }

/* Une décimale sous 100, entier au-delà ; virgule en FR ; suffixe km ou NM */
function fmtDist(km) {
  const nm = S.units.distance === 'nm';
  const v = nm ? km / NM_KM : km;
  const r = Math.round(v * 10) / 10;
  const txt = r < 100 ? r.toFixed(1) : String(Math.round(v));
  return decimal(txt) + ' ' + t(nm ? 'u.nm' : 'u.km');
}

/* Altitude (mètres) → entier dans l'unité choisie */
function altValue(m) { return Math.round(S.units.altitude === 'ft' ? m / FT_M : m); }
function altText(p) { return altValue(p.alt) + ' ' + t(S.units.altitude === 'ft' ? 'u.ft' : 'u.m') + ' ' + t('refl.' + p.altRef); }

/* Cap (vrai, ou magnétique = vrai − déclinaison) et distance d'une branche */
function legInfo(a, b) {
  const L = legCalc(a, b);
  const d = declValue();
  const brg = d == null ? L.brg : (((L.brg - d) % 360) + 360) % 360;
  return { cap: fmtHdg(brg), km: L.km };
}

/* ============= CARTE ============= */
let map = null;
let routeGroup = null;
let linePair = null;
let gridCanvas = null;
let gridQueued = false;
let pendingView = null;
let mapCreated = false;

let baseLayers = [];
let baseGen = 0;
let tileOk = 0, tileErr = 0, tileTimer = null, timerElapsed = false;
let inFallback = false;

function displayLayer() { return inFallback ? 'grid' : S.ui.layer; }

function mapSized() { const s = map.getSize(); return s.x > 0 && s.y > 0; }

/* Une vue à appliquer ; différée tant que le conteneur n'a pas de taille (module caché par le shell) */
function applyView(fn) {
  if (mapSized()) { pendingView = null; fn(); }
  else pendingView = fn;
}

function setTheatreView() {
  const th = theatreOf(S.theatre);
  applyView(() => map.setView(th.c, th.z, { animate: false }));
}

function frameRoute() {
  const pts = S.points;
  if (!pts.length) { setTheatreView(); return; }
  applyView(() => {
    if (pts.length === 1) { map.setView([pts[0].lat, pts[0].lon], 11, { animate: false }); return; }
    map.fitBounds(L.latLngBounds(pts.map(p => [p.lat, p.lon])).pad(0.25), { animate: false, maxZoom: 15 });
  });
}

function attrText(id) { return id === 'grid' ? '' : t('attr.' + id); }

function tileLayersFor(id) {
  const attribution = attrText(id);
  if (id === 'topo') return [L.tileLayer(TOPO_URL, { subdomains: 'abc', maxNativeZoom: 17, maxZoom: 18, attribution: attribution })];
  if (id === 'sat') return [L.tileLayer(SAT_URL, { maxNativeZoom: 19, maxZoom: 18, attribution: attribution })];
  if (id === 'dcs') {
    const key = dcsKey();
    return (DCS_LEVELS[key] || []).map(lv => L.tileLayer(DCS_URL.replace('{key}', key),
      { minNativeZoom: lv[0], maxNativeZoom: lv[1], minZoom: lv[2], maxZoom: 18, attribution: attribution }));
  }
  return [];
}

function updateMapClass() {
  $('map').classList.toggle('grid-only', displayLayer() === 'grid');
}

function setFallback(on) {
  inFallback = on;
  $('fallback').classList.toggle('show', on);
  updateMapClass();
  scheduleGrid();
}

function clearBase() {
  baseGen++;
  clearTimeout(tileTimer);
  baseLayers.forEach(l => map.removeLayer(l));
  baseLayers = [];
}

function checkFallback() {
  if (timerElapsed && tileOk === 0 && tileErr > 0 && S.ui.layer !== 'grid') setFallback(true);
}

/* (Re)crée le fond de ui.layer. Le repli en grille seule ne change pas ui.layer ; choisir à nouveau le fond retente. */
function setBase() {
  clearBase();
  const before = S.ui.layer;
  resolveLayer();
  if (S.ui.layer !== before) persistState();
  syncLayerSelect();
  tileOk = 0; tileErr = 0; timerElapsed = false;
  const id = S.ui.layer;
  if (id === 'grid') { setFallback(false); return; }
  if (navigator.onLine === false) { setFallback(true); return; }
  const gen = baseGen;
  baseLayers = tileLayersFor(id);
  baseLayers.forEach(l => {
    l.on('tileload', () => { if (gen !== baseGen) return; tileOk++; if (inFallback) setFallback(false); });
    l.on('tileerror', () => { if (gen !== baseGen) return; tileErr++; checkFallback(); });
    l.addTo(map);
  });
  tileTimer = setTimeout(() => { if (gen !== baseGen) return; timerElapsed = true; checkFallback(); }, FALLBACK_MS);
  updateMapClass();
  scheduleGrid();
}

/* Langue : les attributions changent sans refaire les couches */
function refreshZoomTitles() {
  const zi = document.querySelector('.leaflet-control-zoom-in'), zo = document.querySelector('.leaflet-control-zoom-out');
  if (zi) { zi.title = t('zoom.in'); zi.setAttribute('aria-label', t('zoom.in')); }
  if (zo) { zo.title = t('zoom.out'); zo.setAttribute('aria-label', t('zoom.out')); }
}
function refreshAttribution() {
  refreshZoomTitles();
  const ctl = map.attributionControl;
  baseLayers.forEach(l => {
    ctl.removeAttribution(l.options.attribution);
    l.options.attribution = attrText(S.ui.layer);
    ctl.addAttribution(l.options.attribution);
  });
}

function createMap() {
  map = L.map('map', {
    zoomControl: true, attributionControl: true, worldCopyJump: false,
    zoomSnap: 1, minZoom: 3, maxZoom: 18,
    zoomAnimation: false, markerZoomAnimation: false, fadeAnimation: false,
    doubleClickZoom: false
  });
  mapCreated = true;
  map.attributionControl.setPrefix('<a href="https://leafletjs.com" target="_blank" rel="noopener" title="Leaflet">Leaflet</a>');
  refreshZoomTitles();
  /* Une vue d'abord (le cadrage du théâtre), même si le conteneur n'a pas encore de taille */
  const th0 = theatreOf(S.theatre);
  map.setView(th0.c, th0.z, { animate: false });
  /* Un clic sur un lien d'attribution ne doit pas faire quitter le module (iframe) */
  map.attributionControl.getContainer().addEventListener('click', e => {
    const a = e.target.closest && e.target.closest('a');
    if (!a) return;
    e.preventDefault();
    window.open(a.href, '_blank', 'noopener');
  });
  /* Le canevas de la grille : au-dessus des tuiles, sous la route */
  const pane = map.createPane('mgrs');
  pane.style.zIndex = 350;
  pane.style.pointerEvents = 'none';
  gridCanvas = document.createElement('canvas');
  gridCanvas.className = 'mgrs-canvas';
  pane.appendChild(gridCanvas);
  routeGroup = L.layerGroup().addTo(map);
  map.on('move zoom viewreset resize', scheduleGrid);
  map.on('zoomend', drawRoute);
  map.on('click', onMapClick);
  /* Le conteneur change de taille (fenêtre, rotation, iframe rendue visible par le shell) */
  const wrap = $('map');
  const onSize = () => {
    if (!wrap.clientWidth || !wrap.clientHeight) return;
    map.invalidateSize({ animate: false });
    if (pendingView) { const f = pendingView; pendingView = null; f(); }
    scheduleGrid();
  };
  if (window.ResizeObserver) new ResizeObserver(onSize).observe(wrap);
  window.addEventListener('resize', onSize);
}

/* ============= GRILLE MGRS ============= */
function scheduleGrid() {
  if (gridQueued || !mapCreated) return;
  gridQueued = true;
  requestAnimationFrame(drawGrid);
}

function gridLabel(g, text, x, y, dark) {
  g.font = '700 11px Oswald, sans-serif';
  g.textAlign = 'center';
  g.textBaseline = 'middle';
  const wdt = g.measureText(text).width + 8;
  g.fillStyle = dark ? 'rgba(20,20,16,.7)' : 'rgba(240,232,214,.85)';
  g.fillRect(x - wdt / 2, y - 8, wdt, 16);
  g.fillStyle = dark ? '#f0e8d6' : '#1f1c16';
  g.fillText(text, x, y + 0.5);
  g.textAlign = 'start';
}

/* Cherche par dichotomie, sur une ligne de la grille (paramètre p entre lo et hi), le point dont la coordonnée écran vaut target.
   at(p) → point écran ; axis 'x' ou 'y' ; la coordonnée est croissante (inc) ou décroissante avec p. Renvoie le point écran ou null. */
function crossAt(at, axis, lo, hi, target, inc) {
  let a = lo, b = hi;
  const fa = at(a)[axis] - target, fb = at(b)[axis] - target;
  if (inc ? (fa > 0 || fb < 0) : (fa < 0 || fb > 0)) return null;
  for (let i = 0; i < 40; i++) {
    const m = (a + b) / 2, pm = at(m);
    if ((pm[axis] < target) === inc) a = m; else b = m;
  }
  return at((a + b) / 2);
}

function drawGrid() {
  gridQueued = false;
  if (!map || !gridCanvas) return;
  const size = map.getSize();
  if (!size.x || !size.y) return;
  const dpr = window.devicePixelRatio || 1;
  const cw = Math.round(size.x * dpr), ch = Math.round(size.y * dpr);
  if (gridCanvas.width !== cw) gridCanvas.width = cw;
  if (gridCanvas.height !== ch) gridCanvas.height = ch;
  gridCanvas.style.width = size.x + 'px';
  gridCanvas.style.height = size.y + 'px';
  L.DomUtil.setPosition(gridCanvas, map.containerPointToLayerPoint([0, 0]).round());
  const g = gridCanvas.getContext('2d');
  g.setTransform(dpr, 0, 0, dpr, 0, 0);
  g.clearRect(0, 0, size.x, size.y);
  if (!S.ui.grid) return;

  const z = map.getZoom();
  const b = map.getBounds();
  const s = Math.max(-80, b.getSouth()), n = Math.min(84, b.getNorth());
  const w = Math.max(-180, b.getWest()), e = Math.min(179.999999, b.getEast());
  if (!(s < n) || !(w < e)) return;
  const P = (lat, lon) => map.latLngToContainerPoint([lat, lon]);
  const dark = displayLayer() === 'sat' || displayLayer() === 'dcs';
  const ink = dark ? 'rgba(240,232,214,.85)' : 'rgba(31,28,22,.62)';
  const halo = dark ? 'rgba(20,20,16,.45)' : 'rgba(240,232,214,.55)';
  /* Niveaux : < 6 limites de zones seules ; 6–8 : 100 km ; 9–11 : 100 km et 10 km ; ≥ 12 : 100 km, 10 km et 1 km */
  const levels = z >= 12 ? [100000, 10000, 1000] : z >= 9 ? [100000, 10000] : z >= 6 ? [100000] : [];
  const widths = [1.4, 1, 0.7];
  const north = (s + n) / 2 >= 0;
  const z0 = Math.floor((w + 180) / 6) + 1, z1 = Math.floor((e + 180) / 6) + 1;

  if (levels.length) for (let zn = Math.max(1, z0); zn <= Math.min(60, z1); zn++) {
    const lo = -180 + (zn - 1) * 6, hi = lo + 6;
    const a = Math.max(w, lo), c = Math.min(e, hi);
    if (a >= c) continue;
    const x0 = P(n, lo).x, x1 = P(n, hi).x;
    g.save();
    g.beginPath(); g.rect(x0, 0, x1 - x0, size.y); g.clip();
    let eMin = Infinity, eMax = -Infinity, nMin = Infinity, nMax = -Infinity;
    for (let i = 0; i <= 6; i++) for (let j = 0; j <= 6; j++) {
      const u = llToUtm(s + (n - s) * i / 6, a + (c - a) * j / 6, zn);
      eMin = Math.min(eMin, u.e); eMax = Math.max(eMax, u.e); nMin = Math.min(nMin, u.n); nMax = Math.max(nMax, u.n);
    }
    const NSEG = 24;
    const drawn = [];
    levels.forEach((sp, li) => {
      const ea = Math.floor(eMin / sp) * sp, eb = Math.ceil(eMax / sp) * sp, na = Math.floor(nMin / sp) * sp, nb = Math.ceil(nMax / sp) * sp;
      if ((eb - ea) / sp > 220 || (nb - na) / sp > 220) return;     /* trop de lignes : niveau non dessiné */
      const lines = [];
      for (let E = ea; E <= eb; E += sp) {
        if (li > 0 && E % levels[li - 1] === 0) continue;
        const pts = [];
        for (let k = 0; k <= NSEG; k++) { const ll = utmToLl(zn, north, E, na + (nb - na) * k / NSEG); pts.push(P(ll.lat, ll.lon)); }
        lines.push(pts);
      }
      for (let N = na; N <= nb; N += sp) {
        if (li > 0 && N % levels[li - 1] === 0) continue;
        const pts = [];
        for (let k = 0; k <= NSEG; k++) { const ll = utmToLl(zn, north, ea + (eb - ea) * k / NSEG, N); pts.push(P(ll.lat, ll.lon)); }
        lines.push(pts);
      }
      drawn.push({ sp: sp, width: widths[li], lines: lines, ea: ea, eb: eb, na: na, nb: nb });
    });
    /* les halos d'abord, puis les traits : l'encre reste au-dessus aux croisements */
    [[halo, 2], [ink, 0]].forEach(pass => {
      drawn.forEach(d => {
        g.beginPath();
        d.lines.forEach(pts => { pts.forEach((p, k) => { if (k) g.lineTo(p.x, p.y); else g.moveTo(p.x, p.y); }); });
        g.strokeStyle = pass[0]; g.lineWidth = d.width + pass[1]; g.lineJoin = 'round'; g.stroke();
      });
    });
    /* les deux chiffres des kilomètres sur les lignes du niveau le plus fin : abscisses au bord bas, ordonnées au bord gauche */
    const fin = drawn.length ? drawn[drawn.length - 1] : null;
    if (fin && fin.sp < 100000) {
      const yl = size.y - 12, xl = Math.max(x0, 0) + 16;
      const posOf = (zE, zN) => { const ll = utmToLl(zn, north, zE, zN); return P(ll.lat, ll.lon); };
      for (let E = fin.ea; E <= fin.eb; E += fin.sp) {
        const p = crossAt(nn => posOf(E, nn), 'y', fin.na, fin.nb, yl, false);
        if (p && p.x >= x0 && p.x <= x1) gridLabel(g, pad2(Math.floor((E % 100000) / 1000)), p.x, yl, dark);
      }
      for (let N = fin.na; N <= fin.nb; N += fin.sp) {
        const p = crossAt(ee => posOf(ee, N), 'x', fin.ea, fin.eb, xl, true);
        if (p) gridLabel(g, pad2(Math.floor((N % 100000) / 1000)), xl, p.y, dark);
      }
    }
    /* les lettres des carrés de 100 km (zoom 6 à 12) : deux lettres, puis la zone et la bande */
    if (z >= 6 && z <= 12) {
      g.textAlign = 'center'; g.textBaseline = 'middle';
      for (let E = Math.floor(eMin / 1e5) * 1e5; E < eMax; E += 1e5) for (let N = Math.floor(nMin / 1e5) * 1e5; N < nMax; N += 1e5) {
        const ll = utmToLl(zn, north, E + 50000, N + 50000);
        if (ll.lon < lo || ll.lon > hi) continue;
        const col = MGRS_COLS.charAt((MGRS_COLS.indexOf(mgrsColOrigin(zn)) + Math.floor(E / 1e5) - 1 + 24) % 24);
        const row = MGRS_ROWS.charAt((MGRS_ROWS.indexOf(mgrsRowOrigin(zn)) + Math.floor(N / 1e5)) % 20);
        const p = P(ll.lat, ll.lon);
        g.fillStyle = dark ? 'rgba(240,232,214,.55)' : 'rgba(31,28,22,.30)';
        g.font = '700 ' + (z >= 9 ? 20 : 15) + 'px "Stardos Stencil", sans-serif';
        g.fillText(col + row, p.x, p.y);
        g.font = '700 10px Oswald, sans-serif';
        g.fillText(pad2(zn) + mgrsBandFor(ll.lat), p.x, p.y + (z >= 9 ? 16 : 13));
      }
      g.textAlign = 'start';
    }
    g.restore();
  }

  /* limites des zones (6° de longitude) et des bandes (8° de latitude) */
  g.save();
  g.setLineDash([8, 5]); g.strokeStyle = 'rgba(168,53,36,.75)'; g.lineWidth = 1.6;
  for (let lon = Math.ceil((w + 180) / 6) * 6 - 180; lon <= e; lon += 6) {
    const p = P(n, lon); g.beginPath(); g.moveTo(p.x, 0); g.lineTo(p.x, size.y); g.stroke();
  }
  for (let lat = Math.ceil((s + 80) / 8) * 8 - 80; lat <= n && lat <= 72; lat += 8) {
    const p = P(lat, w); g.beginPath(); g.moveTo(0, p.y); g.lineTo(size.x, p.y); g.stroke();
  }
  g.restore();
}

/* ============= ROUTE SUR LA CARTE ============= */
function routeColor() {
  return getComputedStyle(document.body).getPropertyValue('--route').trim() || '#a83524';
}

function wpIcon(p, i) {
  return L.divIcon({
    className: 'wp-icon', iconSize: [30, 30], iconAnchor: [15, 15],
    html: '<div class="wp-dot' + (i === sel ? ' sel' : '') + '">' + i + '</div><div class="wp-name">' + esc(p.name) + '</div>'
  });
}

function drawRoute() {
  if (!routeGroup) return;
  routeGroup.clearLayers();
  linePair = null;
  const pts = S.points;
  const ll = pts.map(p => [p.lat, p.lon]);
  if (ll.length > 1) {
    linePair = [
      L.polyline(ll, { color: '#1f1c16', weight: 9, opacity: 0.45, lineCap: 'round', lineJoin: 'round', interactive: false }).addTo(routeGroup),
      L.polyline(ll, { color: routeColor(), weight: 5, opacity: 1, lineCap: 'round', lineJoin: 'round', interactive: false }).addTo(routeGroup)
    ];
  }
  for (let i = 1; i < pts.length; i++) {
    const a = pts[i - 1], b = pts[i];
    const pa = map.latLngToContainerPoint([a.lat, a.lon]), pb = map.latLngToContainerPoint([b.lat, b.lon]);
    const px = pa.distanceTo(pb);
    if (px >= LEG_LABEL_MIN_PX) {
      const l = legInfo(a, b);
      L.marker([(a.lat + b.lat) / 2, (a.lon + b.lon) / 2], {
        interactive: false, keyboard: false,
        icon: L.divIcon({ className: 'leg-label-icon', iconSize: [0, 0], html: '<span class="leg-label">' + l.cap + '° · ' + esc(fmtDist(l.km)) + '</span>' })
      }).addTo(routeGroup);
    }
    if (px >= INSERT_MIN_PX) {
      const q = [a.lat + (b.lat - a.lat) * INSERT_AT, a.lon + (b.lon - a.lon) * INSERT_AT];
      const ins = L.marker(q, {
        zIndexOffset: 400, keyboard: false, title: t('tip.insert'),
        icon: L.divIcon({ className: 'ins-icon', iconSize: [18, 18], iconAnchor: [9, 9], html: '<div class="ins">+</div>' })
      }).addTo(routeGroup);
      ins.on('click', ev => { L.DomEvent.stop(ev); insertPoint(i, q[0], q[1]); });
    }
  }
  pts.forEach((p, i) => {
    const mk = L.marker([p.lat, p.lon], { draggable: true, autoPan: true, zIndexOffset: i === sel ? 2000 : 1000, icon: wpIcon(p, i), title: p.name });
    mk.on('drag', ev => {
      const q = ev.target.getLatLng();
      p.lat = r7(q.lat); p.lon = r7(q.lng);
      if (linePair) { const l2 = S.points.map(x => [x.lat, x.lon]); linePair.forEach(pl => pl.setLatLngs(l2)); }
      renderNav();
    });
    mk.on('dragend', () => {
      sel = i;
      persistState();
      setTimeout(() => { drawRoute(); syncRows(); renderNav(); }, 0);
    });
    mk.on('click', ev => { L.DomEvent.stop(ev); selectPoint(i); });
    mk.addTo(routeGroup);
  });
}

function selectPoint(i) {
  sel = i;
  drawRoute();
  syncRows();
}

function newPointFrom(src, lat, lon, rank) {
  return { name: nextName(S.points, rank), lat: r7(lat), lon: r7(lon), alt: src ? src.alt : 0, altRef: src ? src.altRef : 'AGL' };
}

function onMapClick(ev) {
  if (S.points.length >= MAX_POINTS) { showToast(t('toast.max')); return; }
  const last = S.points.length ? S.points[S.points.length - 1] : null;
  S.points.push(newPointFrom(last, ev.latlng.lat, ev.latlng.lng, S.points.length));
  sel = S.points.length - 1;
  afterEdit(true);
}

/* Insère un point dans la branche (i-1 → i), à son rang ; altitude et référence du point suivant */
function insertPoint(i, lat, lon) {
  if (S.points.length >= MAX_POINTS) { showToast(t('toast.max')); return; }
  S.points.splice(i, 0, newPointFrom(S.points[i], lat, lon, i));
  sel = i;
  afterEdit(true);
}

function deletePoint(i) {
  S.points.splice(i, 1);
  if (sel > i) sel--;
  else if (sel === i) sel = Math.min(i, S.points.length - 1);
  afterEdit(true);
}

/* Après une modification de la liste : enregistrer, redessiner la carte, la fiche et (si rebuild) les rangées */
function afterEdit(rebuildRows) {
  persistState();
  drawRoute();
  if (rebuildRows) renderPts(); else syncRows();
  renderNav();
  syncControls();
}

/* ============= PANNEAU ============= */
function renderPts() {
  $('pts').innerHTML = S.points.map((p, i) =>
    '<div class="pt-row' + (i === sel ? ' sel' : '') + '" data-i="' + i + '"><button type="button" class="pt-num" data-act="select">' + i + '</button>' +
    '<input class="in" data-k="name" type="text" autocomplete="off" spellcheck="false" value="' + esc(p.name) + '">' +
    '<input class="in" data-k="alt" type="text" inputmode="numeric" autocomplete="off" value="' + altValue(p.alt) + '">' +
    '<select class="in" data-k="altRef"><option value="AGL"' + (p.altRef === 'AGL' ? ' selected' : '') + '>' + esc(t('ref.AGL')) + '</option>' +
    '<option value="MSL"' + (p.altRef === 'MSL' ? ' selected' : '') + '>' + esc(t('ref.MSL')) + '</option></select>' +
    '<button type="button" class="pt-del" data-act="delete" title="' + esc(t('tip.delete')) + '" aria-label="' + esc(t('tip.delete')) + '">×</button></div>').join('');
  $('alt-unit').textContent = t('th.alt', { u: t(S.units.altitude === 'ft' ? 'u.ft' : 'u.m') });
  $('pt-count').textContent = t('sec.points', { n: S.points.length });
}

function syncRows() {
  document.querySelectorAll('#pts .pt-row').forEach(r => r.classList.toggle('sel', parseInt(r.dataset.i, 10) === sel));
}

function navTitle() {
  const d = declValue();
  return d == null ? t('nav.title.true') : t('nav.title.mag', { d: decimal(String(d)) });
}

function renderNav() {
  $('nav-title').textContent = navTitle();
  let rows = '', total = 0;
  S.points.forEach((p, i) => {
    if (i > 0) {
      const l = legInfo(S.points[i - 1], p);
      total += l.km;
      rows += '<tr class="leg"><td></td><td colspan="2">↓ ' + l.cap + '°</td><td class="r">' + esc(fmtDist(l.km)) + '</td></tr>';
    }
    rows += '<tr><td class="n">' + i + '</td><td class="nm">' + esc(p.name) + '<span class="co alt">' + esc(altText(p)) + '</span></td>' +
      '<td colspan="2"><span class="co">' + esc(toMGRS(p.lat, p.lon)) + '</span><span class="co dms">' + esc(toDMS(p.lat, p.lon)) + '</span></td></tr>';
  });
  $('nav-body').innerHTML = rows;
  $('nav-total').textContent = fmtDist(total);
}

function renderTheatreOptions() {
  $('theatre').innerHTML = THEATRES.map(x => '<option value="' + x.id + '">' + esc(t('th.' + x.id)) + '</option>').join('');
}

function syncLayerSelect() {
  const sl = $('layer');
  const opt = sl.querySelector('option[value="dcs"]');
  const has = !!dcsKey();
  opt.disabled = !has;
  opt.textContent = t(has ? 'layer.dcs' : 'layer.dcsOff');
  sl.value = S.ui.layer;
}

/* Les contrôles de la barre et du panneau reflètent l'état */
function syncControls() {
  syncLayerSelect();
  $('theatre').value = S.theatre;
  const grid = $('btn-grid');
  grid.classList.toggle('on', !!S.ui.grid);
  grid.setAttribute('aria-pressed', S.ui.grid ? 'true' : 'false');
  const mark = (attr, val) => document.querySelectorAll('[' + attr + ']').forEach(b => {
    const on = b.getAttribute(attr) === val;
    b.classList.toggle('on', on);
    b.setAttribute('aria-pressed', on ? 'true' : 'false');
  });
  mark('data-dist', S.units.distance);
  mark('data-alt', S.units.altitude);
  mark('data-ref', S.navDisplay.ref);
  $('decl-warn').hidden = !(S.navDisplay.ref === 'mag' && parseDecl(S.navDisplay.decl) == null);
  $('btn-handoff').disabled = S.points.length === 0;
  $('theme').value = document.body.dataset.theme;
}

function renderAll() {
  renderTheatreOptions();
  $('theatre').value = S.theatre;
  $('route-name').value = S.name;
  $('decl').value = S.navDisplay.decl;
  renderPts();
  renderNav();
  drawRoute();
  syncControls();
}

/* Saisie dans une rangée : l'état change, la rangée n'est pas reconstruite (le focus reste) */
function onRowInput(ev) {
  const row = ev.target.closest('.pt-row');
  if (!row) return;
  const p = S.points[parseInt(row.dataset.i, 10)];
  if (!p) return;
  const k = ev.target.dataset.k;
  if (k === 'name') p.name = ev.target.value;
  else if (k === 'alt') {
    const v = readNum(ev.target.value);
    if (v == null) return;
    const n = Math.min(99999, Math.round(v));
    p.alt = S.units.altitude === 'ft' ? n * FT_M : n;
  } else if (k === 'altRef') p.altRef = ev.target.value === 'MSL' ? 'MSL' : 'AGL';
  else return;
  persistState();
  if (k === 'name') drawRoute();
  renderNav();
}

function onRowChange(ev) {
  const row = ev.target.closest('.pt-row');
  if (!row || ev.target.dataset.k !== 'alt') return;
  const p = S.points[parseInt(row.dataset.i, 10)];
  if (p) ev.target.value = altValue(p.alt);
}

function onRowClick(ev) {
  const row = ev.target.closest('.pt-row');
  if (!row) return;
  const i = parseInt(row.dataset.i, 10);
  const btn = ev.target.closest('button');
  if (!btn) return;
  if (btn.dataset.act === 'delete') deletePoint(i);
  else if (btn.dataset.act === 'select' && S.points[i]) {
    sel = i;
    map.setView([S.points[i].lat, S.points[i].lon], map.getZoom(), { animate: false });
    drawRoute();
    syncRows();
  }
}

/* ============= FICHIERS ============= */
function stamp() {
  const d = new Date();
  return d.getFullYear() + pad2(d.getMonth() + 1) + pad2(d.getDate()) + '_' + pad2(d.getHours()) + pad2(d.getMinutes()) + pad2(d.getSeconds());
}
function slug(s) {
  return str(s).trim().toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/[^a-z0-9]+/g, '_').replace(/^_+|_+$/g, '');
}

function fallbackDownload(blob, fname, toastMsg) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = fname;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  setTimeout(() => URL.revokeObjectURL(url), 1000);
  if (toastMsg) showToast(toastMsg);
}

function downloadJson() {
  const blob = new Blob([JSON.stringify(exportObject(), null, 2)], { type: 'application/json' });
  const fname = 'route_' + (slug(S.name) || 'route') + '_' + stamp() + '.json';
  if (navigator.share && navigator.canShare) {
    try {
      const file = new File([blob], fname, { type: 'application/json' });
      if (navigator.canShare({ files: [file] })) {
        navigator.share({ files: [file], title: t('app.title'), text: fname }).catch(() => {
          fallbackDownload(blob, fname, t('toast.saved'));
        });
        return;
      }
    } catch (e) { /* repli ci-dessous */ }
  }
  fallbackDownload(blob, fname, t('toast.saved'));
}

/* Met une route lue à la place de la route en cours (unités, théâtre, cap et déclinaison compris ; la couche et la grille restent) */
function setRoute(route) {
  S.name = route.name;
  S.theatre = route.theatre;
  S.units = route.units;
  S.navDisplay = route.navDisplay;
  S.points = route.points;
  sel = -1;
  resolveLayer();
  persistState();
  renderAll();
  setBase();
  frameRoute();
}

function openRouteFile(file) {
  const reader = new FileReader();
  reader.onload = () => {
    let parsed;
    try { parsed = JSON.parse(reader.result); } catch (e) { showToast(t('err.json')); return; }
    const res = parseRoute(parsed);
    if (!res) { showToast(t('err.json')); return; }
    if (S.points.length && !confirm(t('confirm.open'))) return;
    setRoute(res.route);
    showToast(res.dropped ? t('toast.openedDropped', { n: res.dropped }) : t('toast.opened'));
  };
  reader.onerror = () => showToast(t('err.json'));
  reader.readAsText(file);
}

function loadExample() {
  if (!confirm(t('confirm.example'))) return;
  setRoute(parseRoute(JSON.parse(JSON.stringify(EXAMPLE_ROUTE))).route);
}

function clearRoute() {
  if (!confirm(t('confirm.clear'))) return;
  S.name = '';
  S.points = [];
  sel = -1;
  persistState();
  renderAll();
  setTheatreView();
}

/* ============= VERS LA DATACARD ============= */
function sendToDatacard() {
  if (!S.points.length) return;
  persistState();
  let open = null;
  try {
    if (window.parent && window.parent !== window && typeof window.parent.MP_OPEN_MODULE === 'function') open = window.parent.MP_OPEN_MODULE;
  } catch (e) { open = null; }
  if (!open) { showToast(t('toast.standalone')); return; }
  try { localStorage.setItem(KEY_HANDOFF, String(Date.now())); } catch (e) { /* stockage indisponible */ }
  open.call(window.parent, 'dg');
}

/* ============= BARRE ET THÈME ============= */
function revealInScroller(bar, el) {
  if (!bar || !el || bar.scrollWidth <= bar.clientWidth) return;
  const b = bar.getBoundingClientRect();
  const r = el.getBoundingClientRect();
  if (r.left < b.left) bar.scrollLeft += r.left - b.left - 8;
  else if (r.right > b.right) bar.scrollLeft += r.right - b.right + 8;
}

function initScrollBar(bar) {
  if (!bar) return;
  const mq = window.matchMedia('(max-width: 1099px)');
  const update = () => {
    const max = bar.scrollWidth - bar.clientWidth;
    bar.classList.toggle('fade-l', mq.matches && bar.scrollLeft > 1);
    bar.classList.toggle('fade-r', mq.matches && bar.scrollLeft < max - 1);
  };
  const child = x => { while (x && x.parentNode !== bar) x = x.parentNode; return x; };
  bar.addEventListener('scroll', update, { passive: true });
  /* Un appui sur un contrôle partiellement visible le ramène entier dans la vue, puis l'active */
  bar.addEventListener('click', e => { if (mq.matches) revealInScroller(bar, child(e.target)); }, true);
  bar.addEventListener('focusin', e => { if (mq.matches) revealInScroller(bar, child(e.target)); });
  /* Molette verticale → défilement horizontal */
  bar.addEventListener('wheel', e => {
    if (!mq.matches || bar.scrollWidth <= bar.clientWidth) return;
    if (Math.abs(e.deltaY) > Math.abs(e.deltaX)) { bar.scrollLeft += e.deltaY; e.preventDefault(); }
  }, { passive: false });
  window.addEventListener('resize', update);
  if (window.ResizeObserver) new ResizeObserver(update).observe(bar);
  /* Le shell ajoute son bouton de retour après le chargement */
  new MutationObserver(update).observe(bar, { childList: true, subtree: true, characterData: true });
  update();
}

/* Thème de la chrome : n'écrit la clé partagée que sur un choix explicite */
function loadTheme() {
  try {
    const raw = localStorage.getItem(KEY_THEME);
    if (raw && THEME_IDS.indexOf(raw) !== -1) return raw;
  } catch (e) { /* ignore */ }
  return 'cw-nato';
}
function applyTheme(id, persist) {
  if (THEME_IDS.indexOf(id) === -1) id = 'cw-nato';
  document.body.dataset.theme = id;
  const sl = $('theme');
  if (sl) sl.value = id;
  if (persist) { try { localStorage.setItem(KEY_THEME, id); } catch (e) { /* ignore */ } }
}

function setLang(lang) {
  if (lang !== 'fr' && lang !== 'en') return;
  if (lang === CURRENT_LANG) return;
  CURRENT_LANG = lang;
  try { localStorage.setItem(KEY_LANG, lang); } catch (e) { /* ignore */ }
  document.documentElement.lang = lang;
  applyI18nStatic();
  updateFlagButton();
  renderAll();
  refreshAttribution();
}

/* ============= CÂBLAGE ============= */
function bindEvents() {
  $('layer').addEventListener('change', e => {
    S.ui.layer = LAYER_IDS.indexOf(e.target.value) !== -1 ? e.target.value : 'topo';
    persistState();
    setBase();
  });
  $('btn-grid').addEventListener('click', () => {
    S.ui.grid = !S.ui.grid;
    persistState();
    syncControls();
    scheduleGrid();
  });
  $('theatre').addEventListener('change', e => {
    const wasDcs = S.ui.layer === 'dcs';
    S.theatre = theatreOf(e.target.value).id;
    persistState();
    setTheatreView();
    if (wasDcs) setBase();        /* la couche DCS change avec le théâtre (ou passe en Topographique) */
    syncControls();
  });
  document.querySelectorAll('[data-dist]').forEach(b => b.addEventListener('click', () => {
    S.units.distance = b.dataset.dist === 'nm' ? 'nm' : 'km';
    persistState(); renderPts(); renderNav(); drawRoute(); syncControls();
  }));
  document.querySelectorAll('[data-alt]').forEach(b => b.addEventListener('click', () => {
    S.units.altitude = b.dataset.alt === 'ft' ? 'ft' : 'm';
    persistState(); renderPts(); renderNav(); syncControls();
  }));
  document.querySelectorAll('[data-ref]').forEach(b => b.addEventListener('click', () => {
    S.navDisplay.ref = b.dataset.ref === 'mag' ? 'mag' : 'true';
    persistState(); renderNav(); drawRoute(); syncControls();
  }));
  $('decl').addEventListener('input', e => {
    S.navDisplay.decl = e.target.value;
    persistState(); renderNav(); drawRoute(); syncControls();
  });
  $('route-name').addEventListener('input', e => { S.name = e.target.value; persistState(); });
  const pts = $('pts');
  pts.addEventListener('input', onRowInput);
  pts.addEventListener('change', onRowChange);
  pts.addEventListener('click', onRowClick);

  const fileOpen = $('file-open');
  $('btn-open').addEventListener('click', () => { fileOpen.value = ''; fileOpen.click(); });
  fileOpen.addEventListener('change', () => { if (fileOpen.files && fileOpen.files[0]) openRouteFile(fileOpen.files[0]); });
  $('btn-save').addEventListener('click', downloadJson);
  $('btn-export').addEventListener('click', downloadJson);
  $('btn-example').addEventListener('click', loadExample);
  $('btn-clear').addEventListener('click', clearRoute);
  $('btn-handoff').addEventListener('click', sendToDatacard);
  $('theme').addEventListener('change', e => { applyTheme(e.target.value, true); drawRoute(); });
  $('btn-lang').addEventListener('click', () => setLang(CURRENT_LANG === 'fr' ? 'en' : 'fr'));
  initScrollBar(document.querySelector('.toolbar'));

  /* Le shell règle le thème en posant body[data-theme] : suivre sans réécrire la clé, et recolorer la route */
  new MutationObserver(() => {
    const sl = $('theme');
    const cur = document.body.dataset.theme;
    if (sl && cur && sl.value !== cur && THEME_IDS.indexOf(cur) !== -1) sl.value = cur;
    drawRoute();
  }).observe(document.body, { attributes: true, attributeFilter: ['data-theme'] });

  /* De retour en ligne : retenter le fond choisi */
  window.addEventListener('online', () => { if (inFallback) setBase(); });
}

/* ============= DÉMARRAGE ============= */
function init() {
  initLang();
  applyTheme(loadTheme(), false);
  applyI18nStatic();
  updateFlagButton();
  loadState();
  createMap();
  bindEvents();
  renderAll();
  frameRoute();
  setBase();
  persistState();
  /* Les polices embarquées servent au canevas : redessiner la grille une fois chargées */
  if (document.fonts && document.fonts.load) {
    Promise.all([
      document.fonts.load("700 15px 'Stardos Stencil'"),
      document.fonts.load("700 11px 'Oswald'")
    ]).then(() => document.fonts.ready).then(scheduleGrid).catch(() => {});
  }
  window.__RP = { map: map, get S() { return S; }, drawGrid: drawGrid, setBase: setBase, get baseLayers() { return baseLayers; }, get inFallback() { return inFallback; } };
}

if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
else init();

"""

# ============================================================
# ASSEMBLAGE
# ============================================================
def build():
    try:
        example = json.loads(EXAMPLE_ROUTE_JSON)
    except ValueError as e:
        raise SystemExit(f"[ERREUR] Route d'exemple illisible : {e}")
    if example.get('format') != 'dcs-route-v1':
        raise SystemExit("[ERREUR] La route d'exemple n'est pas au format dcs-route-v1")
    example_js = json.dumps(example, ensure_ascii=False, indent=2).replace('</', '<\\/')

    js = JS.replace('__EXAMPLE_ROUTE__', example_js)
    js = js.replace('@@GEO_BLOCK@@\n', GEO_BLOCK).replace('@@READNUM_BLOCK@@\n', READNUM_BLOCK)
    if '@@' in js:
        raise SystemExit("[ERREUR] Marqueur @@ non remplacé dans le script")
    lib = A['lib_leaflet']
    if '</script' in lib.lower():
        raise SystemExit("[ERREUR] Leaflet contient </script : impossible de l'embarquer en ligne")

    html = HTML
    html = html.replace('__CSS__', CSS)
    html = html.replace('__LIB_LEAFLET_CSS__', A['lib_leaflet_css'])
    html = html.replace('__LIB_LEAFLET__', lib)
    html = html.replace('__APP_JS__', js)

    # Contrôles de construction
    left = re.findall(r'__[A-Z0-9_]{4,}__', re.sub(r'<script>.*?</script>', '', html, flags=re.S)[:])
    left = [x for x in left if x not in ('__proto__',)]
    if left:
        raise SystemExit(f"[ERREUR] Marqueurs non remplacés : {sorted(set(left))}")
    if re.search(r'<script[^>]+src=', html, re.I):
        raise SystemExit("[ERREUR] Une balise <script src> subsiste : le fichier doit rester autonome")
    if re.search(r'<link[^>]+rel=["\']?stylesheet', html, re.I):
        raise SystemExit("[ERREUR] Une feuille de style externe subsiste")

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, 'w', encoding='utf-8', newline='\n') as f:
        f.write(html)

    # Syntaxe du script applicatif, si node est disponible
    node = shutil.which('node')
    if node:
        tmp = OUT_PATH + '.check.js'
        try:
            with open(tmp, 'w', encoding='utf-8') as f:
                f.write(js)
            r = subprocess.run([node, '--check', tmp], capture_output=True, text=True)
            if r.returncode != 0:
                raise SystemExit("[ERREUR] Syntaxe JS invalide :\n" + r.stderr)
        finally:
            if os.path.exists(tmp):
                os.remove(tmp)
    size = os.path.getsize(OUT_PATH)
    print(f"[OK] {os.path.relpath(OUT_PATH, HERE)} — {size / 1024:.0f} Ko — v{APP_VERSION}")


if __name__ == '__main__':
    build()
