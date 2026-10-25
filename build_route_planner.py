#!/usr/bin/env python3
"""Build — DCS Route Planner v1.2.0.

Produit dist/dcs_route_planner.html : un fichier unique, hors ligne, sans serveur ;
seules les tuiles de carte (DCS Olympus, OpenTopoMap, Esri) viennent du réseau, et le
module retombe de lui-même sur la grille seule quand elles sont injoignables.
Les polices et les bibliothèques (Leaflet 1.9.4, BSD-2) viennent d'assets.json, à la
racine du dépôt ; les aérodromes DCS (noms et positions, pydcs, LGPL-3.0) viennent d'airfields.json.

Usage : python3 build_route_planner.py
"""

import json
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
APP_VERSION = "1.2.0"
OUT_PATH = os.path.join(HERE, 'dist', 'dcs_route_planner.html')
ASSETS_PATH = os.path.join(HERE, 'assets.json')
AIRFIELDS_PATH = os.path.join(HERE, 'airfields.json')

REQUIRED_ASSETS = ['STARDOS_700', 'OSWALD_500', 'OSWALD_700', 'ROBOTO_MONO_400', 'lib_leaflet', 'lib_leaflet_css']

if not os.path.isfile(ASSETS_PATH):
    raise SystemExit(f"[ERREUR] Entrée manquante : {ASSETS_PATH} (assets.json attendu à la racine du dépôt)")
with open(ASSETS_PATH, encoding='utf-8') as f:
    A = json.load(f)
for _k in REQUIRED_ASSETS:
    if _k not in A or not A[_k]:
        raise SystemExit(f"[ERREUR] Entrée manquante dans assets.json : {_k}")

# Aérodromes DCS : { "format": "dcs-airfields-v1", "theatres": { "<théâtre>": [ ["Nom", lat, lon, "a" | "h"], … ] } }
if not os.path.isfile(AIRFIELDS_PATH):
    raise SystemExit(f"[ERREUR] Entrée manquante : {AIRFIELDS_PATH} (airfields.json attendu à la racine du dépôt)")
with open(AIRFIELDS_PATH, encoding='utf-8') as f:
    AF = json.load(f)
if not isinstance(AF, dict) or AF.get('format') != 'dcs-airfields-v1' or not isinstance(AF.get('theatres'), dict):
    raise SystemExit("[ERREUR] airfields.json : le format doit être « dcs-airfields-v1 » avec une table « theatres »")
for _th, _list in AF['theatres'].items():
    for _a in _list:
        if not (isinstance(_a, list) and len(_a) == 4 and isinstance(_a[0], str) and isinstance(_a[1], (int, float))
                and isinstance(_a[2], (int, float)) and _a[3] in ('a', 'h')):
            raise SystemExit(f"[ERREUR] airfields.json : entrée illisible dans {_th} : {_a!r}")

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
  ],
  "refs": [
    {
      "name": "ÎLE PETRA",
      "lat": 35.184,
      "lon": 32.8445,
      "alt": 0,
      "altRef": "MSL"
    },
    {
      "name": "PONT KARAVOSTASI",
      "lat": 35.1395,
      "lon": 32.8262,
      "alt": 15,
      "altRef": "AGL"
    },
    {
      "name": "SA-9 SUSPECT",
      "lat": 35.121,
      "lon": 32.87,
      "alt": 120,
      "altRef": "MSL"
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

/* ---------- Listes de la barre au thème de l'interface (lot mp-ui-listes) ----------
   Le <select> reste dans la page, masqué ; un bouton de mêmes classes prend sa place (voir initToolbarMenus). */
select[data-tbm-src] { display: none !important; }
.tbm-trigger { display: inline-block; text-align: left; white-space: nowrap; }
.tbm-lbl { display: block; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; text-align: left; padding: 4px 0; margin: -3.25px 0 -2.75px; pointer-events: none; }
.tbm-lbl::after { content: attr(data-w); display: block; height: 0; overflow: hidden; visibility: hidden; white-space: pre; }
@supports (width: calc-size(max-content, round(up, size, 1px))) { .tbm-lbl::after { width: calc-size(max-content, round(up, size, 1px)); } }
.tbm-trigger-open { border-color: var(--amber) !important; }
.tbm-panel {
  position: fixed; z-index: 10500; min-width: 180px; max-width: min(340px, calc(100vw - 16px));
  max-height: min(62vh, 440px); overflow-y: auto; overscroll-behavior: contain;
  background: linear-gradient(180deg, var(--olive-dark) 0%, var(--olive-deep) 100%);
  border: 1px solid var(--amber-dark); border-top: 3px solid var(--amber);
  box-shadow: 0 12px 28px rgba(0,0,0,.55), 0 2px 0 rgba(0,0,0,.35);
  padding: 4px 0; margin: 0; list-style: none; scrollbar-width: thin; scrollbar-color: var(--amber-dark) transparent;
  transform-origin: top left; animation: tbm-in .12s ease-out;
}
.tbm-panel, .tbm-panel:focus, .tbm-panel:focus-visible { outline: none; }
@keyframes tbm-in { from { opacity: 0; transform: translateY(-4px); } to { opacity: 1; transform: none; } }
.tbm-head {
  font-family: var(--f-ui); font-weight: 500; font-size: 10px; letter-spacing: 1.8px; text-transform: uppercase;
  color: var(--khaki-light); padding: 8px 14px 6px; border-bottom: 1px solid rgba(168,154,114,.25); margin-bottom: 2px;
}
.tbm-opt {
  position: relative; display: flex; align-items: center; gap: 10px; min-height: 44px; padding: 0 16px 0 18px;
  font-family: var(--f-ui); font-weight: 500; font-size: 13px; letter-spacing: 1.3px; text-transform: uppercase;
  color: var(--paper); cursor: pointer; white-space: nowrap; user-select: none;
}
.tbm-opt + .tbm-opt { border-top: 1px solid rgba(168,154,114,.14); }
.tbm-opt .tbm-mark { width: 7px; height: 7px; flex: none; transform: rotate(45deg); border: 1px solid var(--khaki); }
.tbm-opt.active, .tbm-opt:hover { background: var(--olive); color: var(--amber); }
.tbm-opt.active .tbm-mark, .tbm-opt:hover .tbm-mark { border-color: var(--amber); }
.tbm-opt[aria-selected="true"] { color: var(--amber); font-weight: 700; }
.tbm-opt[aria-selected="true"]::before { content: ''; position: absolute; left: 0; top: 6px; bottom: 6px; width: 3px; background: var(--amber); }
.tbm-opt[aria-selected="true"] .tbm-mark { background: var(--amber); border-color: var(--amber); }
.tbm-opt[aria-disabled="true"] { color: var(--khaki); cursor: not-allowed; background: none; }
.tbm-opt[aria-disabled="true"] .tbm-mark { border-style: dashed; border-color: var(--khaki); background: none; }
.tbm-opt[aria-disabled="true"] .tbm-note { color: var(--khaki); font-size: 10px; letter-spacing: 1px; margin-left: auto; padding-left: 14px; }
@media (prefers-reduced-motion: reduce) { .tbm-panel { animation: none; } }
@media print { .tbm-panel { display: none; } }
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
.fallback { position: absolute; z-index: 600; left: 56px; top: 12px; max-width: calc(100% - 56px - 180px);
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
.pt-head[hidden] { display: none; }
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

.sheet-top.sub { border-top: 2px solid #f0e8d6; }
#nav-refs-wrap[hidden] { display: none; }

.actions { display: flex; gap: 8px; margin-top: 14px; flex-wrap: wrap; }

/* bloc « Ajouter » : un point par ses coordonnées, ou par cap et distance depuis le dernier point */
.add-block { margin-top: 14px; padding-top: 12px; border-top: 1px dashed var(--khaki); }
.add-block .tb-group { display: flex; width: 100%; margin-bottom: 10px; }
.add-block .tb-group .tb-btn { flex: 1 1 0; min-width: 0; padding: 0 8px; font-size: 11px; letter-spacing: 1px; }
.add-fields { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.add-fields[hidden], .add-coord[hidden] { display: none; }
.add-fields .lbl, .add-coord .lbl { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.add-from { font-size: 11.5px; color: var(--khaki-light); letter-spacing: .3px; line-height: 1.45; margin: 0 0 8px; overflow-wrap: anywhere; }
.add-actions { display: flex; gap: 8px; margin-top: 10px; flex-wrap: wrap; }
.add-actions .tb-btn { flex: 1 1 0; }

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
/* points de référence : un losange de 24 px, sa lettre, le nom sur l'étiquette papier des points */
.rf-icon { width: 24px; height: 24px; }
.rf-dot { width: 24px; height: 24px; box-sizing: border-box; transform: rotate(45deg); background: #1f1c16; border: 2px solid #f0e8d6;
  display: flex; align-items: center; justify-content: center; box-shadow: 0 0 0 1.5px rgba(31,28,22,.55); }
.rf-dot span { transform: rotate(-45deg); font-family: var(--f-ui); font-weight: 700; font-size: 13px; line-height: 1; color: #f0e8d6; }
.rf-dot.sel { background: var(--route); }
.rf-icon .wp-name { left: 34px; top: 2px; }
/* aérodromes : un rond (terrain à piste) ou un carré à « H » (hélistation), dessinés selon le zoom (classes de la couche) */
.af-icon { display: none; box-sizing: border-box; background: #f0e8d6; border: 2.5px solid #1f1c16; }
.af-icon::before { content: ''; position: absolute; left: -9px; top: -9px; right: -9px; bottom: -9px; }
.af-a { width: 12px; height: 12px; border-radius: 50%; }
.af-a::after { content: ''; position: absolute; left: 50%; top: 50%; width: 4px; height: 4px; margin: -2px 0 0 -2px; border-radius: 50%; background: #1f1c16; }
.af-h { width: 10px; height: 10px; border-width: 2px; align-items: center; justify-content: center; }
.af-h b { font-family: var(--f-ui); font-weight: 700; font-size: 8px; line-height: 1; color: #1f1c16; }
.af-name { display: none; position: absolute; left: 14px; top: 50%; transform: translateY(-50%); white-space: nowrap;
  font-family: var(--f-ui); font-weight: 500; font-size: 11px; line-height: 1.3; color: #1f1c16; background: rgba(240,232,214,.8); padding: 0 4px; }
.af-h .af-name { left: 12px; }
.leaflet-airfields-pane.afz7 .af-a { display: block; }
.leaflet-airfields-pane.afz10 .af-h { display: flex; }
.leaflet-airfields-pane.afz9 .af-a .af-name { display: block; }
.leaflet-airfields-pane.afz12 .af-h .af-name { display: block; }
/* ce que pose un toucher sur la carte : Point · Réf. */
.tapmode { background: var(--olive-deep); border: 2px solid var(--amber-dark); box-shadow: 0 2px 8px rgba(0,0,0,.4); }
.tapmode .tb-btn { height: 36px; min-width: 0; padding: 0 10px; font-size: 11px; letter-spacing: 1px; }
#btn-airfields:disabled { pointer-events: auto; cursor: not-allowed; }
.leaflet-control-attribution { font-family: var(--f-ui); font-weight: 500; font-size: 10px !important; background: rgba(240,232,214,.8) !important; }
.leaflet-container { font-family: var(--f-ui); }
body, body[data-theme="cw-nato"] { --route: #a83524; }
body[data-theme="cw-soviet"] { --route: #841e1e; }
body[data-theme="modern-nato"] { --route: #b03a2e; }
body[data-theme="modern-east"] { --route: #7a2424; }

/* ---------- fenêtres du Route Tool (au style de la fenêtre d'import du Datacard Generator) ---------- */
.rt-modal[hidden] { display: none !important; }
.rt-modal { position: fixed; inset: 0; z-index: 10000; display: flex; align-items: center; justify-content: center; padding: 16px; }
.rt-backdrop { position: absolute; inset: 0; background: rgba(0,0,0,.55); backdrop-filter: blur(2px); }
.rt-panel { position: relative; background: var(--paper); color: var(--ink); border: 2px solid var(--ink); border-radius: 4px;
  padding: 24px 28px; max-width: 520px; width: 100%; max-height: 92vh; max-height: 92dvh; overflow-y: auto; box-shadow: 0 8px 40px rgba(0,0,0,.5);
  font-family: var(--f-typewriter); font-weight: 400; }
.rt-close { position: absolute; top: 4px; right: 6px; width: 44px; height: 44px; background: none; border: none; color: var(--ink);
  font-size: 26px; line-height: 1; cursor: pointer; padding: 0; font-family: inherit; }
.rt-close:hover, .rt-close:focus-visible { color: var(--amber-dark); outline: none; }
.rt-panel h2 { font-family: var(--f-stencil); font-weight: 700; font-size: 20px; letter-spacing: 2px; margin: 0 40px 14px 0; text-transform: uppercase; overflow-wrap: anywhere; }
.rt-file { font-size: 12px; margin: 0 0 14px; overflow-wrap: anywhere; opacity: .85; }
.rt-block { margin-bottom: 14px; }
.rt-lbl { display: block; font-family: var(--f-stencil); font-weight: 700; font-size: 13px; letter-spacing: 2px; text-transform: uppercase; margin: 0 0 6px; }
.rt-in { display: block; width: 100%; min-width: 0; min-height: 44px; padding: 8px 10px; background: rgba(255,255,255,.35); color: var(--ink);
  border: 1px solid var(--ink); border-radius: 2px; font-family: var(--f-typewriter); font-weight: 400; font-size: 13px; }
.rt-in:focus { outline: 2px solid var(--amber); outline-offset: 1px; }
/* la liste Théâtre prend le composant des listes de la barre (le <select> reste, masqué) ; même aspect fermé que le <select> */
.rt-in.tbm-trigger { display: block; text-align: start; cursor: pointer; padding-right: 28px;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='6'%3E%3Cpath d='M1 1l4 4 4-4' fill='none' stroke='%231f1c16' stroke-width='1.5'/%3E%3C/svg%3E");
  background-repeat: no-repeat; background-position: right 10px center; }
.rt-in.tbm-trigger .tbm-lbl { margin: 0; padding: 0; }
select.rt-in { appearance: none; -webkit-appearance: none; padding-right: 28px; cursor: pointer;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='6'%3E%3Cpath d='M1 1l4 4 4-4' fill='none' stroke='%231f1c16' stroke-width='1.5'/%3E%3C/svg%3E");
  background-repeat: no-repeat; background-position: right 10px center; }
.rt-note { font-size: 11.5px; line-height: 1.45; margin: 6px 0 0; opacity: .8; overflow-wrap: anywhere; }
.rt-warn { opacity: 1; border-left: 3px solid var(--amber-dark); padding-left: 8px; }
.rt-warn[hidden] { display: none; }
.rt-list { max-height: 280px; overflow-y: auto; border: 1px solid rgba(0,0,0,.25); border-radius: 2px; padding: 4px 10px; margin-bottom: 14px; background: rgba(255,255,255,.25); }
.rt-row { display: flex; align-items: center; gap: 10px; min-height: 44px; padding: 6px 0; font-size: 13px; cursor: pointer; }
.rt-row + .rt-row { border-top: 1px dashed rgba(0,0,0,.2); }
.rt-row input { accent-color: var(--amber); width: 18px; height: 18px; flex: none; margin: 0; }
.rt-nm { flex: 1 1 auto; min-width: 0; overflow-wrap: anywhere; }
.rt-n { flex: none; font-size: 11px; opacity: .75; white-space: nowrap; }
.rt-actions { display: flex; gap: 10px; flex-wrap: wrap; justify-content: space-between; margin-top: 16px; }
.rt-actions.col { flex-direction: column; flex-wrap: nowrap; }
.rt-btn { min-height: 44px; min-width: 44px; padding: 8px 18px; background: transparent; color: var(--ink); border: 2px solid var(--ink); border-radius: 2px;
  font-family: var(--f-stencil); font-weight: 700; font-size: 13px; letter-spacing: 2px; line-height: 1.25; text-transform: uppercase; text-align: center;
  cursor: pointer; flex: 1 1 auto; overflow-wrap: anywhere; }
.rt-btn:hover, .rt-btn:focus-visible { background: rgba(0,0,0,.06); border-color: var(--amber-dark); outline: none; }
.rt-fn { text-transform: none; letter-spacing: 1px; }
.rt-btn.go { background: var(--amber); color: #f6efdc; border-color: var(--amber); }
.rt-btn.go:hover, .rt-btn.go:focus-visible { background: var(--ink); border-color: var(--ink); color: #f6efdc; }
.rt-btn:disabled { opacity: .4; cursor: not-allowed; pointer-events: none; }
#btn-export-rt:disabled { pointer-events: auto; cursor: not-allowed; }
@media (max-width: 520px) {
  .rt-panel { padding: 18px 16px; }
  .rt-panel h2 { font-size: 17px; letter-spacing: 1.5px; }
  .rt-btn { padding: 8px 12px; letter-spacing: 1.5px; }
}
@media print { .rt-modal { display: none; } }

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

/* ---------- barre du haut : une seule ligne qui défile quand elle déborde (à tout écran : avec « Lieux » et « Aérodromes », elle
   ne tient plus sur un portable) ; un fondu signale le bord qui déborde ---------- */
.toolbar {
  --fade-w: 22px; --fade-gap: 8px;
  flex-wrap: nowrap; -webkit-overflow-scrolling: touch; overscroll-behavior-x: contain; touch-action: pan-x;
}
.toolbar > * { flex-shrink: 0; }
.toolbar::before, .toolbar::after {
  content: ''; position: sticky; flex: 0 0 var(--fade-w); width: var(--fade-w); align-self: stretch;
  pointer-events: none; opacity: 0; transition: opacity .15s; z-index: 2;
}
.toolbar::before { left: 0; margin-right: calc(-1 * (var(--fade-w) + var(--fade-gap))); background: inherit; mask-image: linear-gradient(90deg, #000, transparent); -webkit-mask-image: linear-gradient(90deg, #000, transparent); }
.toolbar::after { right: 0; margin-left: calc(-1 * (var(--fade-w) + var(--fade-gap))); background: inherit; mask-image: linear-gradient(270deg, #000, transparent); -webkit-mask-image: linear-gradient(270deg, #000, transparent); }
.toolbar.fade-l::before, .toolbar.fade-r::after { opacity: 1; }

/* ---------- tablette portrait, téléphone ---------- */
@media (max-width: 1099px) {
  .app { position: static; display: block; padding-top: 56px; }
  .mapwrap { height: 58vh; min-height: 340px; border-left: none; border-bottom: 2px solid var(--amber-dark); }
  .app > .panel { order: 0; }
  .panel { overflow: visible; }
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
  <button type="button" class="tb-btn" id="btn-places" aria-pressed="false" data-i18n="tb.places" data-i18n-title="tb.places.tip" title="Noms de lieux (Esri)">Lieux</button>
  <button type="button" class="tb-btn" id="btn-airfields" aria-pressed="true" data-i18n="tb.airfields" data-i18n-title="tb.airfields.tip" title="Aérodromes et hélistations DCS">Aérodromes</button>
  <span class="tb-sep"></span>
  <span class="tb-label" data-i18n="tb.theatre">Théâtre</span>
  <select class="tb-sel" id="theatre" data-i18n-aria-label="tb.theatre" aria-label="Théâtre"></select>
  <span class="tb-sep"></span>
  <span class="tb-group" role="group"><button type="button" class="tb-btn" data-dist="km" aria-pressed="false" data-i18n="u.km">km</button><button type="button" class="tb-btn" data-dist="nm" aria-pressed="false" data-i18n="u.nm">NM</button></span>
  <span class="tb-group" role="group"><button type="button" class="tb-btn" data-alt="m" aria-pressed="false" data-i18n="u.m">m</button><button type="button" class="tb-btn" data-alt="ft" aria-pressed="false" data-i18n="u.ft">ft</button></span>
  <span class="tb-sep"></span>
  <button type="button" class="tb-btn" id="btn-open" data-i18n-title="tb.open.tip" title="Ouvrir une route (JSON) ou un fichier du Route Tool de DCS" data-i18n-aria-label="tb.open.tip" aria-label="Ouvrir une route (JSON) ou un fichier du Route Tool de DCS">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 15V3M7 8l5-5 5 5M5 21h14"/></svg>
    <span class="tb-btn-label solo" data-i18n="tb.open">Ouvrir</span></button>
  <input type="file" id="file-open" hidden>
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
        <div class="add-block" id="add-block">
          <div class="lbl" data-i18n="add.title">Ajouter</div>
          <span class="tb-group" role="group"><button type="button" class="tb-btn" data-addmode="coord" aria-pressed="true" data-i18n="add.coord">Coordonnées</button><button type="button" class="tb-btn" data-addmode="hd" aria-pressed="false" data-i18n="add.hd">Cap et distance</button></span>
          <div class="add-coord" id="add-coord">
            <input class="in" id="add-coord-in" type="text" inputmode="text" autocomplete="off" autocapitalize="off" spellcheck="false" data-i18n-placeholder="add.coord.ph" data-i18n-aria-label="add.coord" placeholder="MGRS, DMS, DDM ou décimal" aria-label="Coordonnées">
          </div>
          <div id="add-hd" hidden>
            <p class="add-from" id="add-from"></p>
            <div class="add-fields">
              <div><label class="lbl" for="add-hdg" data-i18n="add.hdg">Cap (°)</label><input class="in" id="add-hdg" type="text" inputmode="decimal" autocomplete="off" spellcheck="false"></div>
              <div><label class="lbl" for="add-dist" id="add-dist-lbl"></label><input class="in" id="add-dist" type="text" inputmode="decimal" autocomplete="off" spellcheck="false"></div>
            </div>
          </div>
          <div class="add-actions">
            <button type="button" class="tb-btn primary" id="btn-add-wp" data-i18n="add.wp">+ Point</button>
            <button type="button" class="tb-btn" id="btn-add-ref" data-i18n="add.ref">+ Réf.</button>
          </div>
        </div>
        <p class="hint" data-i18n="help.route">Touchez la carte pour ajouter un point ; glissez un point pour le déplacer ; le « + » d'une branche insère un point.</p>
      </div>
    </div>
    <div class="ed-section" data-section="refs">
      <div class="ed-head"><span class="ed-title" data-i18n="sec.refs">Points de référence</span><small id="ref-count"></small></div>
      <div class="ed-body">
        <div class="pt-head" id="ref-head" hidden><span>#</span><span data-i18n="th.name">Nom</span><span id="alt-unit2"></span><span data-i18n="th.ref">Réf.</span><span></span></div>
        <div id="refs"></div>
        <p class="hint" data-i18n="help.refs">Choisissez « Réf. » en haut de la carte, puis touchez la carte ; glissez une référence pour la déplacer.</p>
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
          <div id="nav-refs-wrap" hidden>
            <div class="sheet-top sub"><span data-i18n="nav.refs">POINTS DE RÉFÉRENCE</span></div>
            <table class="nav"><tbody id="nav-refs"></tbody></table>
          </div>
        </div>
        <div class="actions">
          <button type="button" class="tb-btn primary" id="btn-handoff" data-i18n="btn.handoff">→ Vers la datacard</button>
          <button type="button" class="tb-btn" id="btn-export" data-i18n="btn.export">Exporter JSON</button>
          <button type="button" class="tb-btn" id="btn-export-rt" data-i18n="btn.exportRt">Exporter vers le Route Tool</button>
        </div>
      </div>
    </div>
  </aside>
</main>

<div class="toast" id="toast" role="status" aria-live="polite"></div>

<!-- ===== FENÊTRE : OUVRIR UNE ROUTE DU ROUTE TOOL ===== -->
<div class="rt-modal" id="rt-open-modal" hidden role="dialog" aria-modal="true" aria-labelledby="rt-open-title">
  <div class="rt-backdrop" id="rt-open-backdrop"></div>
  <div class="rt-panel" role="document">
    <button type="button" class="rt-close" id="rt-open-close" data-i18n-aria-label="modal.close" aria-label="Fermer">&times;</button>
    <h2 id="rt-open-title" data-i18n="rt.open.title">Ouvrir une route du Route Tool</h2>
    <p class="rt-file" id="rt-open-file"></p>
    <div class="rt-block">
      <label class="rt-lbl" for="rt-theatre" data-i18n="tb.theatre">Théâtre</label>
      <select class="rt-in" id="rt-theatre"></select>
      <p class="rt-note" data-i18n="rt.open.theatreNote">Le théâtre décide de la conversion des coordonnées.</p>
    </div>
    <div class="rt-list" id="rt-routes" role="radiogroup"></div>
    <p class="rt-note rt-warn" id="rt-replace-note" hidden data-i18n="rt.open.replace">La route en cours est remplacée.</p>
    <div class="rt-actions">
      <button type="button" class="rt-btn" id="rt-open-cancel" data-i18n="rt.cancel">Annuler</button>
      <button type="button" class="rt-btn go" id="rt-open-go" data-i18n="rt.open.go">Ouvrir la route</button>
    </div>
  </div>
</div>

<!-- ===== FENÊTRE : EXPORTER VERS LE ROUTE TOOL ===== -->
<div class="rt-modal" id="rt-export-modal" hidden role="dialog" aria-modal="true" aria-labelledby="rt-export-title">
  <div class="rt-backdrop" id="rt-export-backdrop"></div>
  <div class="rt-panel" role="document">
    <button type="button" class="rt-close" id="rt-export-close" data-i18n-aria-label="modal.close" aria-label="Fermer">&times;</button>
    <h2 id="rt-export-title" data-i18n="rt.exp.title">Exporter vers le Route Tool</h2>
    <div class="rt-block">
      <label class="rt-lbl" for="rt-name" data-i18n="rt.exp.name">Nom de la route dans le Route Tool</label>
      <input class="rt-in" id="rt-name" type="text" autocomplete="off" spellcheck="false">
    </div>
    <p class="rt-note" id="rt-help"></p>
    <p class="rt-note rt-warn" id="rt-refs-note" hidden data-i18n="rt.exp.refs">Les points de référence ne passent pas au Route Tool.</p>
    <div class="rt-actions col">
      <button type="button" class="rt-btn go" id="rt-add"></button>
      <button type="button" class="rt-btn" id="rt-new" data-i18n="rt.exp.new">Créer un fichier neuf</button>
      <button type="button" class="rt-btn" id="rt-export-cancel" data-i18n="rt.cancel">Annuler</button>
    </div>
    <input type="file" id="file-rt" hidden>
  </div>
</div>

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
   ROUTE PLANNER v1.2.0
   Une route sur une carte (points posés, saisis par coordonnées
   ou par cap et distance), des points de référence, les noms de lieux
   et les aérodromes DCS : caps, distances, MGRS et DMS,
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
const MAX_REFS = 12;
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

/* Aérodromes DCS par théâtre : [ nom, lat, lon, « a » (terrain à piste) ou « h » (hélistation) ] — pydcs, LGPL-3.0 */
const AIRFIELDS = __AIRFIELDS__;

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
const PLACES_URL = 'https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}';

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
    'tb.places': 'Lieux',
    'tb.places.tip': 'Noms de lieux (Esri)',
    'tb.airfields': 'Aérodromes',
    'tb.airfields.tip': 'Aérodromes et hélistations DCS',
    'tb.airfields.off': 'Aérodromes — absents de ce théâtre',
    'tb.theatre': 'Théâtre',
    'u.km': 'km',
    'u.nm': 'NM',
    'u.m': 'm',
    'u.ft': 'ft',
    'tb.open': 'Ouvrir',
    'tb.open.tip': 'Ouvrir une route (JSON) ou un fichier du Route Tool de DCS',
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
    'attr.places': 'Lieux © Esri, HERE, Garmin, OpenStreetMap contributors',
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
    'tap.wp': 'Point',
    'tap.ref': 'Réf.',
    'tap.title': 'Ce que pose un toucher sur la carte',
    'add.title': 'Ajouter',
    'add.coord': 'Coordonnées',
    'add.hd': 'Cap et distance',
    'add.coord.ph': 'MGRS, DMS, DDM ou décimal',
    'add.hdg': 'Cap (°)',
    'add.dist': 'Distance ({u})',
    'add.from': 'depuis {name}',
    'add.first': 'Posez d\'abord un point.',
    'add.wp': '+ Point',
    'add.ref': '+ Réf.',
    'sec.refs': 'Points de référence',
    'help.refs': 'Choisissez « Réf. » en haut de la carte, puis touchez la carte\u202f; glissez une référence pour la déplacer.',
    'nav.refs': 'POINTS DE RÉFÉRENCE',
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
    'btn.exportRt': 'Exporter vers le Route Tool',
    'tb.rt.off': 'Route Tool indisponible pour ce théâtre',
    'err.rt': 'Fichier du Route Tool non reconnu.',
    'modal.close': 'Fermer',
    'rt.cancel': 'Annuler',
    'rt.open.title': 'Ouvrir une route du Route Tool',
    'rt.open.file': 'Fichier\u202f: {name}',
    'rt.open.theatreNote': 'Le théâtre décide de la conversion des coordonnées.',
    'rt.open.untitled': 'Route sans nom',
    'rt.open.n': '{n} points',
    'rt.open.n1': '{n} point',
    'rt.open.replace': 'La route en cours est remplacée.',
    'rt.open.go': 'Ouvrir la route',
    'rt.exp.title': 'Exporter vers le Route Tool',
    'rt.exp.name': 'Nom de la route dans le Route Tool',
    'rt.exp.help': 'Le Route Tool range toutes les routes d\'une carte dans un seul fichier, {t}.lua, dans Saved Games\\DCS\\Config\\RouteToolPresets. Pour garder vos routes, ouvrez d\'abord ce fichier\u202f: la route y est ajoutée. Sans fichier, un fichier neuf ne contient que cette route.',
    'rt.exp.add': 'Ajouter à mon fichier {t}.lua…',
    'rt.exp.new': 'Créer un fichier neuf',
    'rt.exp.refs': 'Les points de référence ne passent pas au Route Tool.',
    'toast.rtOpened': 'Route ouverte depuis le Route Tool ✓',
    'toast.dropped': '{n} points écartés (30 au plus)',
    'toast.rtOther': 'Ce fichier est celui de {theatre}\u202f: choisissez {t}.lua.',
    'toast.rtTaken': 'Nom déjà pris\u202f: route enregistrée sous « {name} ».',
    'toast.rtReady': '{t}.lua prêt\u202f: copiez-le dans Saved Games\\DCS\\Config\\RouteToolPresets (il remplace l\'ancien).',
    'toast.standalone': 'Route enregistrée : ouvrez le Datacard Generator, puis Importer → Route en cours.',
    'toast.max': '30 points au plus.',
    'toast.maxRefs': '12 points de référence au plus.',
    'toast.refsDropped': '{n} points de référence écartés (12 au plus)',
    'toast.pointAdded': 'Point ajouté\u202f: {name}',
    'toast.refAdded': 'Référence ajoutée\u202f: {name}',
    'toast.badCoord': 'Coordonnées non reconnues.',
    'toast.badHd': 'Cap ou distance invalide.',
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
    'tb.places': 'Places',
    'tb.places.tip': 'Place names (Esri)',
    'tb.airfields': 'Airfields',
    'tb.airfields.tip': 'DCS airfields and helipads',
    'tb.airfields.off': 'Airfields — not available for this theatre',
    'tb.theatre': 'Theatre',
    'u.km': 'km',
    'u.nm': 'NM',
    'u.m': 'm',
    'u.ft': 'ft',
    'tb.open': 'Open',
    'tb.open.tip': 'Open a route (JSON) or a DCS Route Tool file',
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
    'attr.places': 'Places © Esri, HERE, Garmin, OpenStreetMap contributors',
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
    'tap.wp': 'Waypoint',
    'tap.ref': 'Ref.',
    'tap.title': 'What a tap on the map adds',
    'add.title': 'Add',
    'add.coord': 'Coordinates',
    'add.hd': 'Heading and distance',
    'add.coord.ph': 'MGRS, DMS, DDM or decimal',
    'add.hdg': 'Heading (°)',
    'add.dist': 'Distance ({u})',
    'add.from': 'from {name}',
    'add.first': 'Place a waypoint first.',
    'add.wp': '+ Waypoint',
    'add.ref': '+ Ref.',
    'sec.refs': 'Reference points',
    'help.refs': 'Choose “Ref.” at the top of the map, then tap the map; drag a reference to move it.',
    'nav.refs': 'REFERENCE POINTS',
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
    'btn.exportRt': 'Export to the Route Tool',
    'tb.rt.off': 'Route Tool not available for this theatre',
    'err.rt': 'Unrecognised Route Tool file.',
    'modal.close': 'Close',
    'rt.cancel': 'Cancel',
    'rt.open.title': 'Open a Route Tool route',
    'rt.open.file': 'File: {name}',
    'rt.open.theatreNote': 'The theatre sets how coordinates are converted.',
    'rt.open.untitled': 'Untitled route',
    'rt.open.n': '{n} waypoints',
    'rt.open.n1': '{n} waypoint',
    'rt.open.replace': 'The current route is replaced.',
    'rt.open.go': 'Open route',
    'rt.exp.title': 'Export to the Route Tool',
    'rt.exp.name': 'Route name in the Route Tool',
    'rt.exp.help': 'The Route Tool keeps all routes of a map in one file, {t}.lua, in Saved Games\\DCS\\Config\\RouteToolPresets. To keep your routes, open that file first: the route is added to it. Without it, a new file holds only this route.',
    'rt.exp.add': 'Add to my {t}.lua file…',
    'rt.exp.new': 'Create a new file',
    'rt.exp.refs': 'Reference points are not exported to the Route Tool.',
    'toast.rtOpened': 'Route opened from the Route Tool ✓',
    'toast.dropped': '{n} waypoints dropped (30 at most)',
    'toast.rtOther': 'This file belongs to {theatre}: choose {t}.lua.',
    'toast.rtTaken': 'Name already taken: route saved as “{name}”.',
    'toast.rtReady': '{t}.lua ready: copy it into Saved Games\\DCS\\Config\\RouteToolPresets (it replaces the old one).',
    'toast.standalone': 'Route saved: open the Datacard Generator, then Import → Current route.',
    'toast.max': '30 waypoints at most.',
    'toast.maxRefs': '12 reference points at most.',
    'toast.refsDropped': '{n} reference points dropped (12 at most)',
    'toast.pointAdded': 'Waypoint added: {name}',
    'toast.refAdded': 'Reference added: {name}',
    'toast.badCoord': 'Coordinates not recognised.',
    'toast.badHd': 'Invalid heading or distance.',
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

function showToast(msg, ms) {
  const el = $('toast');
  el.textContent = msg;
  el.classList.add('show');
  clearTimeout(showToast._h);
  showToast._h = setTimeout(() => el.classList.remove('show'), ms || 2200);
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
    refs: [],
    ui: { layer: 'topo', grid: true, places: false, airfields: true }
  };
}

let S = defaultState();
let sel = -1;                 /* point sélectionné (non enregistré) */
let selR = -1;                /* point de référence sélectionné (non enregistré) */
let tapMode = 'wp';           /* ce que pose un toucher sur la carte : 'wp' (point) ou 'ref' (référence) — non enregistré */
let addMode = 'coord';        /* bloc Ajouter : 'coord' ou 'hd' (cap et distance) — non enregistré */

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

/* REF<k> : k le plus petit entier ≥ (rang + 1) qu'aucune référence ne porte déjà sous la forme REF<k> */
function nextRefName(refs, rank) {
  const used = {};
  refs.forEach(p => { used[p.name] = true; });
  let k = rank + 1;
  while (used['REF' + k]) k++;
  return 'REF' + k;
}

/* La lettre d'une référence : A, B, C… selon son rang */
function refLetter(i) { return String.fromCharCode(65 + i); }

/* Un objet lu (fichier ou stockage) → { route, dropped, droppedRefs } ; null si ce n'est pas une route dcs-route-v1.
   Un point (ou une référence) dont lat ou lon n'est pas un nombre dans les bornes est écarté ; au-delà de 30 points
   (12 références), le reste est écarté (dropped, droppedRefs les comptent) ; les champs absents prennent leurs défauts. */
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
    points: [],
    refs: []
  };
  let dropped = 0, droppedRefs = 0;
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
  if (Array.isArray(src.refs)) src.refs.forEach(p => {
    if (!p || typeof p !== 'object' || !validCoord(p.lat, p.lon)) return;
    if (route.refs.length >= MAX_REFS) { droppedRefs++; return; }
    route.refs.push({
      name: typeof p.name === 'string' ? p.name : nextRefName(route.refs, route.refs.length),
      lat: r7(p.lat), lon: r7(p.lon),
      alt: (typeof p.alt === 'number' && isFinite(p.alt)) ? p.alt : 0,
      altRef: p.altRef === 'MSL' ? 'MSL' : 'AGL'
    });
  });
  return { route: route, dropped: dropped, droppedRefs: droppedRefs };
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
        S = Object.assign(res.route, { ui: {
          layer: LAYER_IDS.indexOf(ui.layer) !== -1 ? ui.layer : 'topo', grid: typeof ui.grid === 'boolean' ? ui.grid : true,
          places: typeof ui.places === 'boolean' ? ui.places : false, airfields: typeof ui.airfields === 'boolean' ? ui.airfields : true } });
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
    points: S.points.map(p => ({ name: p.name, lat: p.lat, lon: p.lon, alt: p.alt, altRef: p.altRef })),
    refs: S.refs.map(p => ({ name: p.name, lat: p.lat, lon: p.lon, alt: p.alt, altRef: p.altRef }))
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
let refGroup = null;
let placesLayer = null;
let afLayer = null;
let afKey = '';
let tapCtl = null;
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
  const pts = S.points.concat(S.refs);
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
  syncPlaces();
  scheduleGrid();
}

/* La surcouche des noms de lieux : dans son panneau (au-dessus du fond, sous la grille), sur tous les fonds ; hors du repli :
   ses échecs ne comptent pas et, en repli, elle n'est pas affichée */
function syncPlaces() {
  if (!mapCreated) return;
  const want = !!S.ui.places && !inFallback;
  if (want && !placesLayer) {
    placesLayer = L.tileLayer(PLACES_URL, { pane: 'places', maxNativeZoom: 19, maxZoom: 18, attribution: t('attr.places') });
    placesLayer.addTo(map);
  } else if (!want && placesLayer) {
    map.removeLayer(placesLayer);
    placesLayer = null;
  }
}

/* Les aérodromes du théâtre choisi, dans leur panneau (au-dessus de la grille, sous les références et la route).
   Tous les marqueurs sont portés par la couche ; le zoom décide de ce qui se dessine (classes du panneau, CSS). */
function airfieldsOf(theatre) { return Object.prototype.hasOwnProperty.call(AIRFIELDS, theatre) ? AIRFIELDS[theatre] : null; }

function syncAfZoom() {
  const pane = map.getPane('airfields');
  const z = map.getZoom();
  [['afz7', 7], ['afz9', 9], ['afz10', 10], ['afz12', 12]].forEach(c => pane.classList.toggle(c[0], z >= c[1]));
}

function syncAirfields() {
  if (!mapCreated) return;
  const list = airfieldsOf(S.theatre);
  const key = list && S.ui.airfields ? S.theatre : '';
  if (key === afKey) return;
  afKey = key;
  if (afLayer) { map.removeLayer(afLayer); afLayer = null; }
  if (!key) return;
  afLayer = L.layerGroup();
  list.forEach(a => {
    const heli = a[3] === 'h';
    const mk = L.marker([a[1], a[2]], {
      pane: 'airfields', keyboard: false, title: a[0],
      icon: L.divIcon({
        className: 'af-icon ' + (heli ? 'af-h' : 'af-a'), iconSize: heli ? [10, 10] : [12, 12], iconAnchor: heli ? [5, 5] : [6, 6],
        html: (heli ? '<b>H</b>' : '') + '<span class="af-name">' + esc(a[0]) + '</span>'
      })
    });
    mk.on('click', ev => { L.DomEvent.stop(ev); addFromAirfield(a[1], a[2], a[0].toUpperCase()); });
    mk.addTo(afLayer);
  });
  afLayer.addTo(map);
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
  if (placesLayer) {
    ctl.removeAttribution(placesLayer.options.attribution);
    placesLayer.options.attribution = t('attr.places');
    ctl.addAttribution(placesLayer.options.attribution);
  }
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
  /* Les noms de lieux : au-dessus du fond, sous le canevas de la grille */
  const placesPane = map.createPane('places');
  placesPane.style.zIndex = 300;
  placesPane.style.pointerEvents = 'none';
  /* Le canevas de la grille : au-dessus des tuiles, sous la route */
  const pane = map.createPane('mgrs');
  pane.style.zIndex = 350;
  pane.style.pointerEvents = 'none';
  /* Les aérodromes : au-dessus de la grille, sous les références et la route ; les références : sous les points */
  map.createPane('airfields').style.zIndex = 380;
  map.createPane('refs').style.zIndex = 450;
  gridCanvas = document.createElement('canvas');
  gridCanvas.className = 'mgrs-canvas';
  pane.appendChild(gridCanvas);
  refGroup = L.layerGroup().addTo(map);
  routeGroup = L.layerGroup().addTo(map);
  map.on('move zoom viewreset resize', scheduleGrid);
  map.on('zoomend', drawRoute);
  map.on('zoomend', syncAfZoom);
  syncAfZoom();
  createTapControl();
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
      sel = i; selR = -1;
      persistState();
      setTimeout(() => { drawRoute(); drawRefs(); syncRows(); renderNav(); }, 0);
    });
    mk.on('click', ev => { L.DomEvent.stop(ev); selectPoint(i); });
    mk.addTo(routeGroup);
  });
}

/* Les points de référence : un losange et sa lettre, sans ligne qui les relie ; sous les points de la route */
function rfIcon(p, i) {
  return L.divIcon({
    className: 'rf-icon', iconSize: [24, 24], iconAnchor: [12, 12],
    html: '<div class="rf-dot' + (i === selR ? ' sel' : '') + '"><span>' + refLetter(i) + '</span></div><div class="wp-name">' + esc(p.name) + '</div>'
  });
}

function drawRefs() {
  if (!refGroup) return;
  refGroup.clearLayers();
  S.refs.forEach((p, i) => {
    const mk = L.marker([p.lat, p.lon], { pane: 'refs', draggable: true, autoPan: true, zIndexOffset: i === selR ? 1000 : 0, icon: rfIcon(p, i), title: p.name });
    mk.on('drag', ev => {
      const q = ev.target.getLatLng();
      p.lat = r7(q.lat); p.lon = r7(q.lng);
      renderNav();
    });
    mk.on('dragend', () => {
      selR = i; sel = -1;
      persistState();
      setTimeout(() => { drawRoute(); drawRefs(); syncRows(); renderNav(); }, 0);
    });
    mk.on('click', ev => { L.DomEvent.stop(ev); selectRef(i); });
    mk.addTo(refGroup);
  });
}

function selectPoint(i) {
  sel = i; selR = -1;
  drawRoute();
  drawRefs();
  syncRows();
}

function selectRef(i) {
  selR = i; sel = -1;
  drawRoute();
  drawRefs();
  syncRows();
}

function newPointFrom(src, lat, lon, rank) {
  return { name: nextName(S.points, rank), lat: r7(lat), lon: r7(lon), alt: src ? src.alt : 0, altRef: src ? src.altRef : 'AGL' };
}

/* Un point d'une référence neuve : altitude et référence de la référence précédente, sinon 0 et MSL */
function newRefFrom(src, lat, lon, rank) {
  return { name: nextRefName(S.refs, rank), lat: r7(lat), lon: r7(lon), alt: src ? src.alt : 0, altRef: src ? src.altRef : 'MSL' };
}

/* Ajoute un point à la fin de la route (null au plafond) ; name : le nom imposé (un aérodrome), sinon WP<k> */
function addPoint(lat, lon, name) {
  if (S.points.length >= MAX_POINTS) { showToast(t('toast.max')); return null; }
  const last = S.points.length ? S.points[S.points.length - 1] : null;
  const p = newPointFrom(last, lat, lon, S.points.length);
  if (name) p.name = name;
  S.points.push(p);
  sel = S.points.length - 1; selR = -1;
  afterEdit(true);
  return p;
}

/* Ajoute un point de référence à la fin de la liste (null au plafond) */
function addRef(lat, lon, name) {
  if (S.refs.length >= MAX_REFS) { showToast(t('toast.maxRefs')); return null; }
  const last = S.refs.length ? S.refs[S.refs.length - 1] : null;
  const p = newRefFrom(last, lat, lon, S.refs.length);
  if (name) p.name = name;
  S.refs.push(p);
  selR = S.refs.length - 1; sel = -1;
  afterEdit(true);
  return p;
}

/* Selon le mode du contrôle de la carte : un point de route ou une référence */
function addAt(lat, lon, name) {
  return tapMode === 'ref' ? addRef(lat, lon, name) : addPoint(lat, lon, name);
}

function onMapClick(ev) { addAt(ev.latlng.lat, ev.latlng.lng); }

/* Aérodrome touché : le point ou la référence porte son nom en majuscules, et un toast le dit */
function addFromAirfield(lat, lon, name) {
  const p = addAt(lat, lon, name);
  if (p) showToast(t(tapMode === 'ref' ? 'toast.refAdded' : 'toast.pointAdded', { name: p.name }));
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

function deleteRef(i) {
  S.refs.splice(i, 1);
  if (selR > i) selR--;
  else if (selR === i) selR = Math.min(i, S.refs.length - 1);
  afterEdit(true);
}

/* Après une modification des listes : enregistrer, redessiner la carte, la fiche et (si rebuild) les rangées */
function afterEdit(rebuildRows) {
  persistState();
  drawRoute();
  drawRefs();
  if (rebuildRows) { renderPts(); renderRefs(); } else syncRows();
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

/* Les rangées des points de référence : le gabarit des rangées de points, la lettre à la place du numéro */
function renderRefs() {
  $('refs').innerHTML = S.refs.map((p, i) =>
    '<div class="pt-row' + (i === selR ? ' sel' : '') + '" data-i="' + i + '"><button type="button" class="pt-num" data-act="select">' + refLetter(i) + '</button>' +
    '<input class="in" data-k="name" type="text" autocomplete="off" spellcheck="false" value="' + esc(p.name) + '">' +
    '<input class="in" data-k="alt" type="text" inputmode="numeric" autocomplete="off" value="' + altValue(p.alt) + '">' +
    '<select class="in" data-k="altRef"><option value="AGL"' + (p.altRef === 'AGL' ? ' selected' : '') + '>' + esc(t('ref.AGL')) + '</option>' +
    '<option value="MSL"' + (p.altRef === 'MSL' ? ' selected' : '') + '>' + esc(t('ref.MSL')) + '</option></select>' +
    '<button type="button" class="pt-del" data-act="delete" title="' + esc(t('tip.delete')) + '" aria-label="' + esc(t('tip.delete')) + '">×</button></div>').join('');
  $('ref-head').hidden = !S.refs.length;
  $('alt-unit2').textContent = t('th.alt', { u: t(S.units.altitude === 'ft' ? 'u.ft' : 'u.m') });
  $('ref-count').textContent = String(S.refs.length);
}

function syncRows() {
  document.querySelectorAll('#pts .pt-row').forEach(r => r.classList.toggle('sel', parseInt(r.dataset.i, 10) === sel));
  document.querySelectorAll('#refs .pt-row').forEach(r => r.classList.toggle('sel', parseInt(r.dataset.i, 10) === selR));
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
  /* Les points de référence : après le total ; ni dans les branches ni dans le total */
  let rr = '';
  S.refs.forEach((p, i) => {
    rr += '<tr><td class="n">' + refLetter(i) + '</td><td class="nm">' + esc(p.name) + '<span class="co alt">' + esc(altText(p)) + '</span></td>' +
      '<td colspan="2"><span class="co">' + esc(toMGRS(p.lat, p.lon)) + '</span><span class="co dms">' + esc(toDMS(p.lat, p.lon)) + '</span></td></tr>';
  });
  $('nav-refs').innerHTML = rr;
  $('nav-refs-wrap').hidden = !S.refs.length;
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
  const rtb = $('btn-export-rt');
  const hasRt = hasRouteTool(S.theatre);
  rtb.disabled = !S.points.length || !hasRt;
  if (hasRt) rtb.removeAttribute('title'); else rtb.title = t('tb.rt.off');
  $('theme').value = document.body.dataset.theme;
  const pl = $('btn-places');
  pl.classList.toggle('on', !!S.ui.places);
  pl.setAttribute('aria-pressed', S.ui.places ? 'true' : 'false');
  const af = $('btn-airfields');
  const hasAf = !!airfieldsOf(S.theatre);
  af.disabled = !hasAf;
  af.classList.toggle('on', hasAf && !!S.ui.airfields);
  af.setAttribute('aria-pressed', hasAf && S.ui.airfields ? 'true' : 'false');
  af.title = t(hasAf ? 'tb.airfields.tip' : 'tb.airfields.off');
  syncAdd();
}

function renderAll() {
  renderTheatreOptions();
  $('theatre').value = S.theatre;
  $('route-name').value = S.name;
  $('decl').value = S.navDisplay.decl;
  renderPts();
  renderRefs();
  renderNav();
  drawRoute();
  drawRefs();
  syncTapControl();
  syncAirfields();
  syncControls();
}

/* ============= AJOUTER UN POINT : COORDONNÉES, OU CAP ET DISTANCE ============= */
function setAddMode(m) {
  addMode = m === 'hd' ? 'hd' : 'coord';
  syncAdd();
}

function syncAdd() {
  document.querySelectorAll('[data-addmode]').forEach(b => {
    const on = b.dataset.addmode === addMode;
    b.classList.toggle('on', on);
    b.setAttribute('aria-pressed', on ? 'true' : 'false');
  });
  const last = S.points.length ? S.points[S.points.length - 1] : null;
  $('add-coord').hidden = addMode !== 'coord';
  $('add-hd').hidden = addMode !== 'hd';
  $('add-from').textContent = last ? t('add.from', { name: last.name }) : t('add.first');
  $('add-dist-lbl').textContent = t('add.dist', { u: t(S.units.distance === 'nm' ? 'u.nm' : 'u.km') });
  const off = addMode === 'hd' && !last;
  $('btn-add-wp').disabled = off;
  $('btn-add-ref').disabled = off;
}

/* La position à ajouter, lue du bloc Ajouter ; null (et un toast) si elle est illisible */
function readAddPosition() {
  if (addMode === 'coord') {
    const g = parseCoord($('add-coord-in').value);
    if (!g) { showToast(t('toast.badCoord')); return null; }
    return { lat: r7(g.lat), lon: r7(g.lon) };
  }
  const last = S.points.length ? S.points[S.points.length - 1] : null;
  if (!last) return null;
  const cap = readNum($('add-hdg').value), dist = readNum($('add-dist').value);
  if (cap == null || cap > 360 || dist == null || !(dist > 0)) { showToast(t('toast.badHd')); return null; }
  /* cap magnétique (navigation en cap magnétique et déclinaison lisible) : le point se calcule au cap vrai cap + déclinaison */
  const d = declValue();
  const brg = d == null ? cap : (((cap + d) % 360) + 360) % 360;
  const km = S.units.distance === 'nm' ? dist * NM_KM : dist;
  const p = legDest(last, brg, km);
  return { lat: r7(p.lat), lon: r7(p.lon) };
}

/* « + Point » (kind 'wp') ou « + Réf. » (kind 'ref') : la carte se recentre sur le point sans changer de zoom ;
   le champ Coordonnées se vide, Cap et Distance restent (on enchaîne) */
function addFromInput(kind) {
  const pos = readAddPosition();
  if (!pos) return;
  const p = kind === 'ref' ? addRef(pos.lat, pos.lon) : addPoint(pos.lat, pos.lon);
  if (!p) return;
  if (addMode === 'coord') $('add-coord-in').value = '';
  map.setView([pos.lat, pos.lon], map.getZoom(), { animate: false });
  showToast(t(kind === 'ref' ? 'toast.refAdded' : 'toast.pointAdded', { name: p.name }));
}

/* ============= CONTRÔLE DE LA CARTE : CE QUE POSE UN TOUCHER ============= */
function createTapControl() {
  const Ctl = L.Control.extend({
    options: { position: 'topright' },
    onAdd: function () {
      const d = L.DomUtil.create('div', 'tapmode tb-group');
      d.setAttribute('role', 'group');
      d.id = 'tapmode';
      d.innerHTML = '<button type="button" class="tb-btn" data-tap="wp"></button><button type="button" class="tb-btn" data-tap="ref"></button>';
      L.DomEvent.disableClickPropagation(d);
      L.DomEvent.disableScrollPropagation(d);
      d.addEventListener('click', e => {
        const b = e.target.closest('[data-tap]');
        if (b) setTapMode(b.dataset.tap);
      });
      return d;
    }
  });
  tapCtl = new Ctl();
  tapCtl.addTo(map);
  syncTapControl();
}

function setTapMode(m) {
  tapMode = m === 'ref' ? 'ref' : 'wp';
  syncTapControl();
}

function syncTapControl() {
  const d = $('tapmode');
  if (!d) return;
  d.title = t('tap.title');
  d.setAttribute('aria-label', t('tap.title'));
  d.querySelectorAll('[data-tap]').forEach(b => {
    const on = b.dataset.tap === tapMode;
    b.textContent = t('tap.' + b.dataset.tap);
    b.classList.toggle('on', on);
    b.setAttribute('aria-pressed', on ? 'true' : 'false');
  });
}

/* Saisie dans une rangée : l'état change, la rangée n'est pas reconstruite (le focus reste) */
function onRowInput(ev, kind) {
  const row = ev.target.closest('.pt-row');
  if (!row) return;
  const p = (kind === 'ref' ? S.refs : S.points)[parseInt(row.dataset.i, 10)];
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
  if (k === 'name') { if (kind === 'ref') drawRefs(); else drawRoute(); }
  renderNav();
}

function onRowChange(ev, kind) {
  const row = ev.target.closest('.pt-row');
  if (!row || ev.target.dataset.k !== 'alt') return;
  const p = (kind === 'ref' ? S.refs : S.points)[parseInt(row.dataset.i, 10)];
  if (p) ev.target.value = altValue(p.alt);
}

function onRowClick(ev, kind) {
  const row = ev.target.closest('.pt-row');
  if (!row) return;
  const i = parseInt(row.dataset.i, 10);
  const btn = ev.target.closest('button');
  if (!btn) return;
  const list = kind === 'ref' ? S.refs : S.points;
  if (btn.dataset.act === 'delete') { if (kind === 'ref') deleteRef(i); else deletePoint(i); }
  else if (btn.dataset.act === 'select' && list[i]) {
    map.setView([list[i].lat, list[i].lon], map.getZoom(), { animate: false });
    if (kind === 'ref') selectRef(i); else selectPoint(i);
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
  S.refs = route.refs;
  sel = -1; selR = -1;
  resolveLayer();
  persistState();
  renderAll();
  setBase();
  frameRoute();
}

/* « Ouvrir » : le contenu décide — un texte qui commence par « presets » est un fichier du Route Tool (fenêtre de choix),
   sinon une route JSON dcs-route-v1 */
function openRouteFile(file) {
  readFileBytes(file, bytes => {
    const text = bytesToText(bytes);
    if (/^\s*presets/.test(text)) {
      const data = parseRouteTool(text);
      if (!data || !data.routes.length) { showToast(t('err.rt')); return; }
      openRouteToolModal(file.name, data);
      return;
    }
    let parsed;
    try { parsed = JSON.parse(text); } catch (e) { showToast(t('err.json')); return; }
    const res = parseRoute(parsed);
    if (!res) { showToast(t('err.json')); return; }
    if (S.points.length && !confirm(t('confirm.open'))) return;
    setRoute(res.route);
    showToast((res.dropped ? t('toast.openedDropped', { n: res.dropped }) : t('toast.opened')) +
      (res.droppedRefs ? ' · ' + t('toast.refsDropped', { n: res.droppedRefs }) : ''));
  }, () => showToast(t('err.json')));
}

function loadExample() {
  if (!confirm(t('confirm.example'))) return;
  setRoute(parseRoute(JSON.parse(JSON.stringify(EXAMPLE_ROUTE))).route);
}

function clearRoute() {
  if (!confirm(t('confirm.clear'))) return;
  S.name = '';
  S.points = [];
  S.refs = [];
  sel = -1; selR = -1;
  persistState();
  renderAll();
  setTheatreView();
}

/* ============= LE ROUTE TOOL DE DCS : PROJECTIONS, LECTURE, ÉCRITURE ============= */
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

function hasRouteTool(id) { return Object.prototype.hasOwnProperty.call(TM_PARAMS, id); }
function routeToolTheatres() { return THEATRES.filter(x => hasRouteTool(x.id)); }

/* Le théâtre que nomme un fichier : son nom sans extension, ou ce nom suivi d'un espace ou d'une parenthèse
   (« Syria (1).lua »), sans casse ; '' si aucun */
function theatreOfFileName(name) {
  const low = String(name == null ? '' : name).replace(/\.[^.\\/]*$/, '').toLowerCase();
  for (let i = 0; i < THEATRES.length; i++) {
    const id = THEATRES[i].id.toLowerCase();
    if (low === id || (low.indexOf(id) === 0 && /^[ (]/.test(low.charAt(id.length)))) return THEATRES[i].id;
  }
  return '';
}

/* ---- Lecteur Lua minimal : tables, chaînes, nombres, true / false / nil, commentaires « -- ». Ni eval, ni motif de lignes.
   Une table lue : { items: [ { k, v } ] } (k : chaîne ou nombre) ; lève une erreur si le texte sort de ce sous-ensemble. ---- */
function luaParse(src) {
  const n = src.length;
  let i = 0;
  const bad = () => { throw new Error('lua'); };
  const isSpace = c => c === 32 || c === 9 || c === 10 || c === 13 || c === 12 || c === 11;
  const isIdStart = c => (c >= 65 && c <= 90) || (c >= 97 && c <= 122) || c === 95;
  const isDigit = c => c >= 48 && c <= 57;

  function skip() {
    for (;;) {
      while (i < n && isSpace(src.charCodeAt(i))) i++;
      if (src.charAt(i) === '-' && src.charAt(i + 1) === '-') {
        i += 2;
        const lm = /^\[(=*)\[/.exec(src.slice(i, i + 40));
        if (lm) {
          const close = ']' + lm[1] + ']';
          const e = src.indexOf(close, i + lm[0].length);
          if (e < 0) bad();
          i = e + close.length;
        } else {
          while (i < n && src.charAt(i) !== '\n') i++;
        }
        continue;
      }
      return;
    }
  }

  function readString() {
    const q = src.charAt(i++);
    let out = '';
    for (;;) {
      if (i >= n) bad();
      const ch = src.charAt(i++);
      if (ch === q) return out;
      if (ch === '\n' || ch === '\r') bad();
      if (ch !== '\\') { out += ch; continue; }
      const e = src.charAt(i++);
      const map = { n: '\n', t: '\t', r: '\r', a: '\x07', b: '\b', f: '\f', v: '\v', '\\': '\\', '"': '"', "'": "'" };
      if (Object.prototype.hasOwnProperty.call(map, e)) out += map[e];
      else if (e === '\n') out += '\n';
      else if (isDigit(e.charCodeAt(0))) {
        let d = e;
        while (d.length < 3 && isDigit(src.charCodeAt(i))) d += src.charAt(i++);
        const v = parseInt(d, 10);
        if (v > 255) bad();
        out += String.fromCharCode(v);
      } else bad();
    }
  }

  const NUM = /-?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?/y;
  function readNumber() {
    NUM.lastIndex = i;
    const m = NUM.exec(src);
    if (!m) bad();
    i += m[0].length;
    const v = parseFloat(m[0]);
    if (!isFinite(v)) bad();
    return v;
  }

  function readIdent() {
    const s = i;
    while (i < n && (isIdStart(src.charCodeAt(i)) || isDigit(src.charCodeAt(i)))) i++;
    return src.slice(s, i);
  }

  function keyword(id) {
    if (id === 'true') return true;
    if (id === 'false') return false;
    if (id === 'nil') return null;
    return bad();
  }

  function readValue(depth) {
    if (depth > 64) bad();
    skip();
    const c = src.charAt(i);
    if (c === '{') return readTable(depth + 1);
    if (c === '"' || c === "'") return readString();
    if (c === '-' || c === '.' || isDigit(src.charCodeAt(i))) return readNumber();
    if (isIdStart(src.charCodeAt(i))) return keyword(readIdent());
    return bad();
  }

  function readTable(depth) {
    i++;                                  /* « { » */
    const items = [];
    let auto = 1;
    for (;;) {
      skip();
      const c = src.charAt(i);
      if (c === '}') { i++; return { items: items }; }
      if (i >= n) bad();
      let k, v;
      if (c === '[') {
        i++;
        k = readValue(depth);
        if (typeof k !== 'string' && typeof k !== 'number') bad();
        skip();
        if (src.charAt(i++) !== ']') bad();
        skip();
        if (src.charAt(i++) !== '=') bad();
        v = readValue(depth);
      } else if (isIdStart(src.charCodeAt(i))) {
        const id = readIdent();
        skip();
        if (src.charAt(i) === '=' && src.charAt(i + 1) !== '=') { i++; k = id; v = readValue(depth); }
        else { k = auto++; v = keyword(id); }
      } else {
        k = auto++;
        v = readValue(depth);
      }
      items.push({ k: k, v: v });
      skip();
      const s = src.charAt(i);
      if (s === ',' || s === ';') i++;
      else if (s !== '}') bad();
    }
  }

  skip();
  if (src.substr(i, 7) !== 'presets') bad();
  i += 7;
  skip();
  if (src.charAt(i++) !== '=') bad();
  const v = readValue(0);
  skip();
  if (src.charAt(i) === ';') { i++; skip(); }
  if (i < n) bad();
  return v;
}

function luaIsTable(v) { return !!v && typeof v === 'object' && Array.isArray(v.items); }
function luaGet(tbl, key) {
  let r;
  tbl.items.forEach(it => { if (it.k === key) r = it.v; });
  return r;
}

/* Le texte d'un fichier du Route Tool → { routes: [ { name, points: [ { x, y, alt, altRef, name } ] } ] } ; null s'il ne se lit pas.
   Les routes gardent l'ordre du fichier, les points celui de leurs indices ; un point sans x ni y numériques est écarté. */
function parseRouteTool(text) {
  let tbl;
  try { tbl = luaParse(text); } catch (e) { return null; }
  if (!luaIsTable(tbl)) return null;
  const routes = [];
  for (let a = 0; a < tbl.items.length; a++) {
    const it = tbl.items[a];
    if (!luaIsTable(it.v)) return null;
    const idx = it.v.items.filter(p => typeof p.k === 'number' && Math.floor(p.k) === p.k && luaIsTable(p.v));
    idx.sort((p, q) => p.k - q.k);
    const points = [];
    idx.forEach(p => {
      const x = luaGet(p.v, 'x'), y = luaGet(p.v, 'y'), alt = luaGet(p.v, 'alt'), nm = luaGet(p.v, 'name');
      if (typeof x !== 'number' || typeof y !== 'number') return;
      points.push({ x: x, y: y, alt: typeof alt === 'number' ? alt : 0,
        altRef: luaGet(p.v, 'alt_type') === 'RADIO' ? 'AGL' : 'MSL', name: typeof nm === 'string' ? nm : '' });
    });
    routes.push({ name: String(it.k), points: points });
  }
  return { routes: routes };
}

/* Un nombre à la façon de Lua (%.14g) : 14 chiffres significatifs, sans zéros de fin ; sous 1e-4, 0 */
function luaNum(v) {
  if (typeof v !== 'number' || !isFinite(v) || Math.abs(v) < 1e-4) return '0';
  return String(Number(v.toPrecision(14)));
}
function luaStr(s) {
  return '"' + String(s == null ? '' : s).replace(/\\/g, '\\\\').replace(/"/g, '\\"').replace(/\r\n|\r|\n/g, '\\n') + '"';
}

/* Le bloc d'une route, à la forme de DCS (LF, tabulations ; ETA 0 et non verrouillé : DCS recalcule les heures) */
function routeToolBlock(name, points, theatre) {
  let s = '\t[' + luaStr(name) + '] = \n\t{\n';
  points.forEach((p, k) => {
    const c = llToDcs(theatre, p.lat, p.lon);
    s += '\t\t[' + (k + 1) + '] = \n\t\t{\n' +
      '\t\t\t["alt"] = ' + luaNum(p.alt) + ',\n' +
      '\t\t\t["type"] = "Turning Point",\n' +
      '\t\t\t["ETA"] = 0,\n' +
      '\t\t\t["ETA_locked"] = false,\n' +
      '\t\t\t["y"] = ' + luaNum(c.y) + ',\n' +
      '\t\t\t["x"] = ' + luaNum(c.x) + ',\n' +
      '\t\t\t["name"] = ' + luaStr(p.name) + ',\n' +
      '\t\t\t["action"] = "Turning Point",\n' +
      '\t\t\t["alt_type"] = "' + (p.altRef === 'AGL' ? 'RADIO' : 'BARO') + '",\n' +
      '\t\t\t["speed_locked"] = false,\n' +
      '\t\t}, -- end of [' + (k + 1) + ']\n';
  });
  return s + '\t}, -- end of [' + luaStr(name) + ']\n';
}

const RT_END = '} -- end of presets';

/* Le plus petit nom libre : « nom », puis « nom (2) », « nom (3) »… */
function freeRouteName(name, taken) {
  if (taken.indexOf(name) === -1) return name;
  let k = 2;
  while (taken.indexOf(name + ' (' + k + ')') !== -1) k++;
  return name + ' (' + k + ')';
}

/* Les octets d'un fichier existant + le bloc → les trois morceaux du fichier neuf, ou null sans ligne « } -- end of presets » :
   tout ce qui précède la dernière de ces lignes reste tel quel, octet pour octet */
function appendRouteBlock(bytes, block) {
  const pat = new TextEncoder().encode(RT_END);
  for (let p = bytes.length - pat.length; p >= 0; p--) {
    if (p > 0 && bytes[p - 1] !== 10) continue;
    let ok = true;
    for (let j = 0; j < pat.length; j++) if (bytes[p + j] !== pat[j]) { ok = false; break; }
    if (ok) return [bytes.subarray(0, p), new TextEncoder().encode(block), bytes.subarray(p)];
  }
  return null;
}

function readFileBytes(file, done, fail) {
  const reader = new FileReader();
  reader.onload = () => done(new Uint8Array(reader.result));
  reader.onerror = fail;
  reader.readAsArrayBuffer(file);
}
function bytesToText(bytes) {
  try { return new TextDecoder('utf-8').decode(bytes); } catch (e) { return ''; }
}

/* ---- Fenêtres : « Ouvrir une route du Route Tool » et « Exporter vers le Route Tool » ---- */
const RT = { fileName: '', routes: [], theatre: 'Caucasus', sel: 0, opener: null };

function rtVisible(id) { return !$(id).hidden; }
function rtShow(id, opener, focusId) {
  RT.opener = opener || null;
  $(id).hidden = false;
  let f = $(focusId);
  if (f && f.hasAttribute('data-tbm-src')) f = f.previousElementSibling;   /* le <select> est masqué : le focus va à son bouton */
  if (f) f.focus({ preventScroll: true });
}
function rtHide(id) {
  if (TBM.cur) tbmClose(false);      /* la liste ouverte se ferme avec la fenêtre */
  $(id).hidden = true;
  const o = RT.opener;
  RT.opener = null;
  if (o && o.focus && !o.disabled) { try { o.focus({ preventScroll: true }); } catch (e) { /* ignore */ } }
}
function rtCloseAll() {
  if (rtVisible('rt-open-modal')) rtHide('rt-open-modal');
  if (rtVisible('rt-export-modal')) rtHide('rt-export-modal');
}
/* Tab reste dans la fenêtre ouverte */
function rtTrap(ev) {
  if (ev.key !== 'Tab') return;
  const m = rtVisible('rt-open-modal') ? $('rt-open-modal') : (rtVisible('rt-export-modal') ? $('rt-export-modal') : null);
  if (!m) return;
  const els = Array.prototype.filter.call(m.querySelectorAll('button, input, select'), e => !e.disabled && !e.hidden && e.type !== 'hidden' && e.offsetParent !== null);
  if (!els.length) return;
  const first = els[0], last = els[els.length - 1];
  if (ev.shiftKey && (document.activeElement === first || !m.contains(document.activeElement))) { ev.preventDefault(); last.focus(); }
  else if (!ev.shiftKey && (document.activeElement === last || !m.contains(document.activeElement))) { ev.preventDefault(); first.focus(); }
}

function rtPointsLabel(n) { return t(n === 1 ? 'rt.open.n1' : 'rt.open.n', { n: n }); }

function rtOpenRender() {
  $('rt-open-file').textContent = t('rt.open.file', { name: RT.fileName });
  $('rt-theatre').innerHTML = routeToolTheatres().map(x => '<option value="' + x.id + '">' + esc(t('th.' + x.id)) + '</option>').join('');
  $('rt-theatre').value = RT.theatre;
  $('rt-routes').innerHTML = RT.routes.map((r, i) =>
    '<label class="rt-row"><input type="radio" name="rt-route" value="' + i + '"' + (i === RT.sel ? ' checked' : '') + '>' +
    '<span class="rt-nm">' + esc(r.name === '' ? t('rt.open.untitled') : r.name) + '</span>' +
    '<span class="rt-n">' + esc(rtPointsLabel(r.points.length)) + '</span></label>').join('');
  $('rt-replace-note').hidden = !S.points.length;
}

/* Un fichier du Route Tool lu : la fenêtre s'ouvre, le théâtre préchoisi */
function openRouteToolModal(fileName, data) {
  const named = theatreOfFileName(fileName);
  RT.fileName = fileName;
  RT.routes = data.routes;
  RT.sel = 0;
  RT.theatre = hasRouteTool(named) ? named : (hasRouteTool(S.theatre) ? S.theatre : routeToolTheatres()[0].id);
  rtOpenRender();
  rtShow('rt-open-modal', $('btn-open'), 'rt-theatre');
}

function rtOpenGo() {
  const r = RT.routes[RT.sel];
  if (!r) return;
  const th = RT.theatre;
  const pts = [];
  let dropped = 0;
  r.points.forEach(p => {
    const ll = dcsToLl(th, p.x, p.y);
    if (!validCoord(ll.lat, ll.lon)) return;
    if (pts.length >= MAX_POINTS) { dropped++; return; }
    pts.push({ name: p.name !== '' ? p.name : nextName(pts, pts.length), lat: r7(ll.lat), lon: r7(ll.lon), alt: p.alt, altRef: p.altRef });
  });
  rtHide('rt-open-modal');
  setRoute({ name: r.name, theatre: th, units: S.units, navDisplay: S.navDisplay, points: pts, refs: [] });
  showToast(t('toast.rtOpened') + (dropped ? ' · ' + t('toast.dropped', { n: dropped }) : ''));
}

function rtExportName() {
  const v = $('rt-name').value.trim();
  return v !== '' ? v : t('app.title');
}

function rtExportRender() {
  /* le nom du fichier garde sa casse (le bouton est en capitales) */
  $('rt-add').innerHTML = esc(t('rt.exp.add', { t: '\u0001' })).replace('\u0001.lua', '<span class="rt-fn">' + esc(S.theatre) + '.lua</span>');
  $('rt-help').textContent = t('rt.exp.help', { t: S.theatre });
  $('rt-refs-note').hidden = !S.refs.length;
}

function openExportRouteTool() {
  if (!S.points.length || !hasRouteTool(S.theatre)) return;
  $('rt-name').value = S.name.trim() !== '' ? S.name.trim() : t('app.title');
  rtExportRender();
  rtShow('rt-export-modal', $('btn-export-rt'), 'rt-name');
}

/* Remet le fichier au navigateur : partage (tablette) ou téléchargement, sous le nom exact <théâtre>.lua, UTF-8 sans BOM */
function deliverLua(parts, fname, msg) {
  const blob = new Blob(parts, { type: 'application/octet-stream' });
  if (navigator.share && navigator.canShare) {
    try {
      const file = new File(parts, fname, { type: 'text/plain' });
      if (navigator.canShare({ files: [file] })) {
        navigator.share({ files: [file], title: t('app.title'), text: fname }).catch(() => {
          fallbackDownload(blob, fname, msg);
        });
        return;
      }
    } catch (e) { /* repli ci-dessous */ }
  }
  fallbackDownload(blob, fname, msg);
}

function rtFinish(parts, name, finalName) {
  const fname = S.theatre + '.lua';
  rtHide('rt-export-modal');
  let msg = t('toast.rtReady', { t: S.theatre });
  if (finalName !== name) msg = t('toast.rtTaken', { name: finalName }) + ' ' + msg;
  deliverLua(parts, fname, '');
  showToast(msg, 6500);
}

/* « Créer un fichier neuf » */
function rtExportNew() {
  const name = rtExportName();
  const block = routeToolBlock(name, S.points, S.theatre);
  rtFinish([new TextEncoder().encode('presets = \n{\n' + block + RT_END + '\n')], name, name);
}

/* « Ajouter à mon fichier… » : le fichier choisi est lu, contrôlé, puis reçoit la route avant sa dernière ligne de fin */
function rtExportAdd(file) {
  const th = S.theatre;
  readFileBytes(file, bytes => {
    const data = parseRouteTool(bytesToText(bytes));
    if (!data) { showToast(t('err.rt')); return; }
    const named = theatreOfFileName(file.name);
    if (named && named !== th) { showToast(t('toast.rtOther', { theatre: t('th.' + named), t: th })); return; }
    const name = rtExportName();
    const finalName = freeRouteName(name, data.routes.map(r => r.name));
    const parts = appendRouteBlock(bytes, routeToolBlock(finalName, S.points, th));
    if (!parts) { showToast(t('err.rt')); return; }
    rtFinish(parts, name, finalName);
  }, () => showToast(t('err.rt')));
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
  const mq = { matches: true };   /* à tout écran : la barre défile dès qu'elle déborde */
  const update = () => {
    const max = bar.scrollWidth - bar.clientWidth;
    bar.classList.toggle('fade-l', mq.matches && max > 6 && bar.scrollLeft > 1);          /* un débord de quelques pixels n'appelle pas de fondu */
    bar.classList.toggle('fade-r', mq.matches && max > 6 && bar.scrollLeft < max - 1);
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
  /* Les polices embarquées changent la largeur des libellés sans évènement de taille */
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(update).catch(() => {});
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
  if (rtVisible('rt-open-modal')) rtOpenRender();
  if (rtVisible('rt-export-modal')) rtExportRender();
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
  $('btn-places').addEventListener('click', () => {
    S.ui.places = !S.ui.places;
    persistState();
    syncPlaces();
    syncControls();
  });
  $('btn-airfields').addEventListener('click', () => {
    if (!airfieldsOf(S.theatre)) return;
    S.ui.airfields = !S.ui.airfields;
    persistState();
    syncAirfields();
    syncControls();
  });
  $('theatre').addEventListener('change', e => {
    const wasDcs = S.ui.layer === 'dcs';
    S.theatre = theatreOf(e.target.value).id;
    persistState();
    setTheatreView();
    if (wasDcs) setBase();        /* la couche DCS change avec le théâtre (ou passe en Topographique) */
    syncAirfields();
    syncControls();
  });
  document.querySelectorAll('[data-dist]').forEach(b => b.addEventListener('click', () => {
    S.units.distance = b.dataset.dist === 'nm' ? 'nm' : 'km';
    persistState(); renderPts(); renderNav(); drawRoute(); syncControls();
  }));
  document.querySelectorAll('[data-alt]').forEach(b => b.addEventListener('click', () => {
    S.units.altitude = b.dataset.alt === 'ft' ? 'ft' : 'm';
    persistState(); renderPts(); renderRefs(); renderNav(); syncControls();
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
  pts.addEventListener('input', ev => onRowInput(ev, 'wp'));
  pts.addEventListener('change', ev => onRowChange(ev, 'wp'));
  pts.addEventListener('click', ev => onRowClick(ev, 'wp'));
  const refs = $('refs');
  refs.addEventListener('input', ev => onRowInput(ev, 'ref'));
  refs.addEventListener('change', ev => onRowChange(ev, 'ref'));
  refs.addEventListener('click', ev => onRowClick(ev, 'ref'));
  document.querySelectorAll('[data-addmode]').forEach(b => b.addEventListener('click', () => setAddMode(b.dataset.addmode)));
  $('btn-add-wp').addEventListener('click', () => addFromInput('wp'));
  $('btn-add-ref').addEventListener('click', () => addFromInput('ref'));
  ['add-coord-in', 'add-hdg', 'add-dist'].forEach(id => $(id).addEventListener('keydown', ev => {
    if (ev.key !== 'Enter') return;
    ev.preventDefault();
    if (!$('btn-add-wp').disabled) addFromInput('wp');
  }));

  const fileOpen = $('file-open');
  $('btn-open').addEventListener('click', () => { fileOpen.value = ''; fileOpen.click(); });
  fileOpen.addEventListener('change', () => { if (fileOpen.files && fileOpen.files[0]) openRouteFile(fileOpen.files[0]); });
  $('btn-save').addEventListener('click', downloadJson);
  $('btn-export').addEventListener('click', downloadJson);
  $('btn-export-rt').addEventListener('click', openExportRouteTool);
  ['rt-open-backdrop', 'rt-open-close', 'rt-open-cancel'].forEach(id => $(id).addEventListener('click', () => rtHide('rt-open-modal')));
  ['rt-export-backdrop', 'rt-export-close', 'rt-export-cancel'].forEach(id => $(id).addEventListener('click', () => rtHide('rt-export-modal')));
  $('rt-theatre').addEventListener('change', e => { if (hasRouteTool(e.target.value)) RT.theatre = e.target.value; });
  $('rt-routes').addEventListener('change', e => { const k = parseInt(e.target.value, 10); if (k >= 0 && k < RT.routes.length) RT.sel = k; });
  $('rt-open-go').addEventListener('click', rtOpenGo);
  const fileRt = $('file-rt');
  $('rt-add').addEventListener('click', () => { fileRt.value = ''; fileRt.click(); });
  fileRt.addEventListener('change', () => { if (fileRt.files && fileRt.files[0]) rtExportAdd(fileRt.files[0]); });
  $('rt-new').addEventListener('click', rtExportNew);
  document.addEventListener('keydown', ev => {
    if (ev.key === 'Escape' && (rtVisible('rt-open-modal') || rtVisible('rt-export-modal'))) { ev.preventDefault(); rtCloseAll(); }
    else rtTrap(ev);
  });
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
    drawRefs();
  }).observe(document.body, { attributes: true, attributeFilter: ['data-theme'] });

  /* De retour en ligne : retenter le fond choisi */
  window.addEventListener('online', () => { if (inFallback) setBase(); });
}

/* ============= DÉMARRAGE ============= */
/* ============= LISTES DE LA BARRE — thème de l'interface (lot mp-ui-listes) =============
   Le <select> reste dans la page (id, options, écouteurs) : il garde la valeur, mais il est masqué.
   Un <button> de mêmes classes prend sa place et porte le libellé de l'option choisie ; la liste ouverte
   est un <ul role="listbox"> posé en fin de <body> (la barre défile et couperait ce qui déborde).
   Le libellé suit toujours le <select> : mutations du DOM (options reconstruites, traduites, désactivées,
   title) et affectations par le code (value, selectedIndex) interceptées sur l'instance. */
const TBM = { cur: null, bound: false, swallow: false };

function initToolbarMenus(specs) {
  specs.forEach(sp => tbmAttach(document.getElementById(sp[0]), sp[1]));
  if (TBM.bound) return;
  TBM.bound = true;
  document.addEventListener('pointerdown', tbmOutside, true);
  window.addEventListener('click', tbmSwallowClick, true);
  window.addEventListener('resize', () => tbmClose(false));
  window.addEventListener('blur', () => tbmClose(false));
  window.addEventListener('scroll', tbmScrolled, true);
}

function tbmAttach(sel, labelFn) {
  if (!sel || !sel.parentNode || sel.hasAttribute('data-tbm-src')) return;
  const btn = document.createElement('button');
  btn.type = 'button';
  btn.className = sel.className + ' tbm-trigger';
  btn.setAttribute('aria-haspopup', 'listbox');
  btn.setAttribute('aria-expanded', 'false');
  btn.setAttribute('aria-controls', 'tbm-list-' + sel.id);
  const lbl = document.createElement('span');
  lbl.className = 'tbm-lbl';
  btn.appendChild(lbl);
  const m = { sel: sel, btn: btn, lbl: lbl, labelFn: labelFn, panel: null, active: -1, type: '', typeTimer: 0, x0: 0, y0: 0 };
  sel.parentNode.insertBefore(btn, sel);
  sel.setAttribute('data-tbm-src', '');
  ['value', 'selectedIndex'].forEach(k => {
    const d = Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype, k);
    if (!d || !d.set) return;
    Object.defineProperty(sel, k, {
      configurable: true, enumerable: true,
      get() { return d.get.call(this); },
      set(v) { d.set.call(this, v); tbmSync(m); }
    });
  });
  new MutationObserver(() => tbmSync(m)).observe(sel, {
    childList: true, subtree: true, characterData: true, attributes: true,
    attributeFilter: ['title', 'aria-label', 'disabled', 'label', 'selected', 'value']
  });
  sel.addEventListener('change', () => tbmSync(m));
  ['focus', 'mouseover'].forEach(ev => btn.addEventListener(ev, () => tbmSync(m)));   /* filet : option.selected posé par le code */
  btn.addEventListener('click', () => { if (m.panel) tbmClose(true); else tbmOpen(m); });
  btn.addEventListener('keydown', e => {
    if (e.key === 'Enter' || e.key === ' ' || e.key === 'ArrowDown' || e.key === 'ArrowUp') {
      e.preventDefault();
      if (!m.panel) tbmOpen(m);
    }
  });
  tbmSync(m);
}

/* Le libellé affiché = l'option choisie ; la largeur = l'option la plus large (comme le <select>) */
function tbmSync(m) {
  const sel = m.sel, o = sel.options, i = sel.selectedIndex;
  const txt = i >= 0 && o[i] ? o[i].label : '';
  if (m.lbl.textContent !== txt) m.lbl.textContent = txt;
  const all = [];
  for (let k = 0; k < o.length; k++) all.push(o[k].label);
  const w = all.join(String.fromCharCode(10));
  if (m.lbl.getAttribute('data-w') !== w) m.lbl.setAttribute('data-w', w);
  let name = '';
  try { name = m.labelFn(); } catch (e) { name = ''; }
  m.btn.setAttribute('aria-label', name);
  if (sel.hasAttribute('title')) m.btn.title = sel.title; else m.btn.removeAttribute('title');
  m.btn.disabled = sel.disabled;
}

function tbmOpen(m) {
  if (TBM.cur) tbmClose(false);
  if (m.sel.disabled) return;
  tbmSync(m);
  const sel = m.sel, opts = sel.options, name = m.labelFn();
  const ul = document.createElement('ul');
  ul.className = 'tbm-panel';
  ul.id = 'tbm-list-' + sel.id;
  ul.setAttribute('role', 'listbox');
  ul.setAttribute('aria-label', name);
  ul.tabIndex = -1;
  const head = document.createElement('li');
  head.className = 'tbm-head';
  head.setAttribute('role', 'presentation');
  head.textContent = name;
  ul.appendChild(head);
  for (let k = 0; k < opts.length; k++) {
    const o = opts[k], li = document.createElement('li');
    li.className = 'tbm-opt';
    li.id = 'tbm-' + sel.id + '-' + k;
    li.setAttribute('role', 'option');
    li.setAttribute('aria-selected', k === sel.selectedIndex ? 'true' : 'false');
    li.setAttribute('data-i', String(k));
    const mark = document.createElement('span');
    mark.className = 'tbm-mark';
    const txt = document.createElement('span');
    txt.className = 'tbm-txt';
    let label = o.label, note = '';
    if (o.disabled) {
      li.setAttribute('aria-disabled', 'true');
      const j = label.indexOf(' — ');
      if (j >= 0) { note = label.slice(j + 3); label = label.slice(0, j); }
    }
    txt.textContent = label;
    li.appendChild(mark);
    li.appendChild(txt);
    if (note) {
      const n = document.createElement('span');
      n.className = 'tbm-note';
      n.textContent = note;
      li.appendChild(n);
    }
    ul.appendChild(li);
  }
  ul.addEventListener('keydown', e => tbmKey(m, e));
  ul.addEventListener('click', e => {
    const li = e.target.closest ? e.target.closest('.tbm-opt') : null;
    if (!li || li.getAttribute('aria-disabled') === 'true') return;
    tbmChoose(m, Number(li.getAttribute('data-i')));
  });
  ul.addEventListener('mousemove', e => {
    const li = e.target.closest ? e.target.closest('.tbm-opt') : null;
    if (!li || li.getAttribute('aria-disabled') === 'true') return;
    const k = Number(li.getAttribute('data-i'));
    if (k !== m.active) tbmSetActive(m, k, false);
  });
  document.body.appendChild(ul);
  m.panel = ul;
  TBM.cur = m;
  m.btn.classList.add('tbm-trigger-open');
  m.btn.setAttribute('aria-expanded', 'true');
  tbmPlace(m);
  let k0 = sel.selectedIndex;
  if (k0 < 0 || (opts[k0] && opts[k0].disabled)) k0 = tbmFirst(m, 1);
  tbmSetActive(m, k0, 'center');
  ul.focus({ preventScroll: true });
}

/* Sous le bouton (4 px), bord gauche aligné, au moins aussi large, à 8 px au moins des bords de la fenêtre */
function tbmPlace(m) {
  const r = m.btn.getBoundingClientRect(), p = m.panel;
  const vw = document.documentElement.clientWidth, vh = window.innerHeight;
  const top = r.bottom + 4;
  m.x0 = r.left; m.y0 = r.top;
  p.style.minWidth = Math.max(180, r.width) + 'px';
  p.style.top = top + 'px';
  p.style.left = r.left + 'px';
  p.style.maxHeight = Math.max(60, Math.min(0.62 * vh, 440, vh - top - 12)) + 'px';
  const w = p.getBoundingClientRect().width;
  let left = r.left;
  if (left + w > vw - 8) left = vw - 8 - w;
  if (left < 8) left = 8;
  p.style.left = left + 'px';
}

function tbmFirst(m, d) {
  const o = m.sel.options;
  let k = d > 0 ? 0 : o.length - 1;
  for (; k >= 0 && k < o.length; k += d) if (!o[k].disabled) return k;
  return -1;
}

function tbmSetActive(m, k, reveal) {
  const p = m.panel;
  if (!p) return;
  const prev = p.querySelector('.tbm-opt.active');
  if (prev) prev.classList.remove('active');
  m.active = k;
  const li = k >= 0 ? p.querySelector('.tbm-opt[data-i="' + k + '"]') : null;
  if (!li) { p.removeAttribute('aria-activedescendant'); return; }
  li.classList.add('active');
  p.setAttribute('aria-activedescendant', li.id);
  if (!reveal) return;
  const t = li.offsetTop, h = li.offsetHeight;
  if (k === tbmFirst(m, 1)) p.scrollTop = 0;
  else if (t < p.scrollTop) p.scrollTop = t;
  else if (t + h > p.scrollTop + p.clientHeight) p.scrollTop = reveal === 'center' ? Math.max(0, t - (p.clientHeight - h) / 2) : t + h - p.clientHeight;
}

function tbmStep(m, d) {
  const o = m.sel.options;
  for (let k = m.active + d; k >= 0 && k < o.length; k += d) {
    if (!o[k].disabled) { tbmSetActive(m, k, true); return; }
  }
}

/* Saisie de lettres : première option qui commence par elles, remise à zéro après 0,7 s */
function tbmType(m, ch) {
  clearTimeout(m.typeTimer);
  m.type += ch.toLowerCase();
  m.typeTimer = setTimeout(() => { m.type = ''; }, 700);
  const o = m.sel.options;
  for (let k = 0; k < o.length; k++) {
    if (!o[k].disabled && o[k].label.toLowerCase().indexOf(m.type) === 0) { tbmSetActive(m, k, true); return; }
  }
}

function tbmKey(m, e) {
  const k = e.key;
  if (k === 'ArrowDown' || k === 'ArrowUp') { e.preventDefault(); tbmStep(m, k === 'ArrowDown' ? 1 : -1); }
  else if (k === 'Home') { e.preventDefault(); tbmSetActive(m, tbmFirst(m, 1), true); }
  else if (k === 'End') { e.preventDefault(); tbmSetActive(m, tbmFirst(m, -1), true); }
  else if (k === 'Enter' || k === ' ') { e.preventDefault(); if (m.active >= 0) tbmChoose(m, m.active); }
  else if (k === 'Escape') { e.preventDefault(); e.stopPropagation(); tbmClose(true); }
  else if (k === 'Tab') { tbmClose(true); }   /* sans preventDefault : le focus part du bouton vers le contrôle suivant */
  else if (k.length === 1 && !e.ctrlKey && !e.metaKey && !e.altKey) { e.preventDefault(); tbmType(m, k); }
}

/* Choisir : si la valeur change, le <select> la prend et reçoit un évènement change (qui bouillonne) */
function tbmChoose(m, k) {
  const sel = m.sel, o = sel.options[k];
  if (!o || o.disabled) return;
  const changed = k !== sel.selectedIndex;
  tbmClose(true);
  if (!changed) return;
  sel.selectedIndex = k;
  sel.dispatchEvent(new Event('change', { bubbles: true }));
}

function tbmClose(refocus) {
  const m = TBM.cur;
  if (!m) return;
  TBM.cur = null;
  clearTimeout(m.typeTimer);
  m.type = '';
  if (m.panel) m.panel.remove();
  m.panel = null;
  m.active = -1;
  m.btn.classList.remove('tbm-trigger-open');
  m.btn.setAttribute('aria-expanded', 'false');
  if (refocus) m.btn.focus({ preventScroll: true });
}

/* Un toucher ou un clic hors de la liste et du bouton la ferme, sans agir ailleurs (le clic qui suit est avalé) ;
   le bouton d'une autre liste ferme celle-ci et s'ouvre ensuite par son propre clic. */
function tbmOutside(e) {
  const m = TBM.cur;
  if (!m) return;
  const t = e.target;
  if (m.panel.contains(t) || m.btn.contains(t)) return;
  const other = t && t.closest ? t.closest('.tbm-trigger') : null;
  tbmClose(false);
  if (other) return;
  TBM.swallow = true;
  const rel = () => { document.removeEventListener('pointerup', rel, true); document.removeEventListener('pointercancel', rel, true); setTimeout(() => { TBM.swallow = false; }, 350); };
  document.addEventListener('pointerup', rel, true);
  document.addEventListener('pointercancel', rel, true);
}

function tbmSwallowClick(e) {
  if (!TBM.swallow) return;
  TBM.swallow = false;
  e.stopPropagation();
  e.preventDefault();
}

/* Le défilement de la barre (ou de la page) déplace le bouton : la liste se ferme */
function tbmScrolled(e) {
  const m = TBM.cur;
  if (!m || !m.panel) return;
  if (e.target === m.panel || (e.target.nodeType && m.panel.contains(e.target))) return;
  const r = m.btn.getBoundingClientRect();
  if (Math.abs(r.left - m.x0) > 0.5 || Math.abs(r.top - m.y0) > 0.5) tbmClose(false);
}

function init() {
  initLang();
  applyTheme(loadTheme(), false);
  applyI18nStatic();
  updateFlagButton();
  initToolbarMenus([['layer', () => t('tb.layer')], ['theatre', () => t('tb.theatre')], ['theme', () => t('tb.theme.tip')], ['rt-theatre', () => t('tb.theatre')]]);   /* les listes de la barre au thème de l'interface */
  loadState();
  createMap();
  bindEvents();
  renderAll();
  frameRoute();
  setBase();
  syncPlaces();
  syncAirfields();
  persistState();
  /* Les polices embarquées servent au canevas : redessiner la grille une fois chargées */
  if (document.fonts && document.fonts.load) {
    Promise.all([
      document.fonts.load("700 15px 'Stardos Stencil'"),
      document.fonts.load("700 11px 'Oswald'")
    ]).then(() => document.fonts.ready).then(scheduleGrid).catch(() => {});
  }
  window.__RP = { map: map, get S() { return S; }, drawGrid: drawGrid, setBase: setBase, get baseLayers() { return baseLayers; }, get inFallback() { return inFallback; },
    get placesLayer() { return placesLayer; }, get airfieldLayer() { return afLayer; }, get tapMode() { return tapMode; } };
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

    airfields_js = json.dumps(AF['theatres'], ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
    js = JS.replace('__EXAMPLE_ROUTE__', example_js).replace('__AIRFIELDS__', airfields_js)
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
