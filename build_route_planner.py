#!/usr/bin/env python3
"""Build — DCS Route Planner v1.8.1.

Produit dist/dcs_route_planner.html : un fichier unique, hors ligne, sans serveur ;
seules les tuiles de carte (DCS Olympus, OpenTopoMap, Esri) viennent du réseau, et le
module retombe de lui-même sur la grille seule quand elles sont injoignables.
Les polices et les bibliothèques (Leaflet 1.9.4, BSD-2) viennent d'assets.json, à la
racine du dépôt ; les aérodromes DCS (noms et positions, pydcs, LGPL-3.0) viennent d'airfields.json ;
les villes DCS (noms et positions) viennent de towns.json ; la déclinaison magnétique (coefficients WMM 1985–2025, comme DCS) vient du dossier wmm/
via magvar_block.py.

Usage : python3 build_route_planner.py
"""

import json
import os
import re
import shutil
import subprocess
import sys

from magvar_block import build_block as build_magvar_block

HERE = os.path.dirname(os.path.abspath(__file__))
APP_VERSION = "1.8.1"
OUT_PATH = os.path.join(HERE, 'dist', 'dcs_route_planner.html')
ASSETS_PATH = os.path.join(HERE, 'assets.json')
AIRFIELDS_PATH = os.path.join(HERE, 'airfields.json')
TOWNS_PATH = os.path.join(HERE, 'towns.json')

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

# Villes DCS : { "format": "dcs-towns-v1", "theatres": { "<théâtre>": [ ["Nom", lat, lon], … ] } }
def _is_num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)

if not os.path.isfile(TOWNS_PATH):
    raise SystemExit(f"[ERREUR] Entrée manquante : {TOWNS_PATH} (towns.json attendu à la racine du dépôt)")
with open(TOWNS_PATH, encoding='utf-8') as f:
    TW = json.load(f)
if not isinstance(TW, dict) or TW.get('format') != 'dcs-towns-v1' or not isinstance(TW.get('theatres'), dict):
    raise SystemExit("[ERREUR] towns.json : le format doit être « dcs-towns-v1 » avec une table « theatres »")
for _th, _list in TW['theatres'].items():
    if not isinstance(_list, list):
        raise SystemExit(f"[ERREUR] towns.json : la liste de {_th} est illisible")
    for _a in _list:
        if not (isinstance(_a, list) and len(_a) == 3 and isinstance(_a[0], str) and _is_num(_a[1]) and _is_num(_a[2])):
            raise SystemExit(f"[ERREUR] towns.json : entrée illisible dans {_th} : {_a!r}")

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

/* ---------- Listes des formulaires au thème de l'interface (lot mp-ui-listes-formulaires) ----------
   Le bouton d'une référence d'altitude garde la boîte, le texte et le chevron du <select.in> ; la liste ouverte garde la police,
   la casse et la graisse du champ (celles de la fiche Dessin et de la fenêtre Route Tool aussi). */
.in.tbm-trigger {
  display: block; text-align: left; cursor: pointer; contain: inline-size; letter-spacing: normal; text-transform: none; padding-right: 22px;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='6'%3E%3Cpath d='M1 1l4 4 4-4' fill='none' stroke='%231f1c16' stroke-width='1.5'/%3E%3C/svg%3E"); background-repeat: no-repeat; background-position: right 7px center;
}
.in.tbm-trigger .tbm-lbl { margin: 0; padding: 0; line-height: 22px; }
.in.tbm-trigger .tbm-lbl::after { display: none; }
.in.tbm-trigger.tbm-trigger-open {
  outline: none; border-left-color: var(--red-stamp); background-color: #ece0c2; box-shadow: 0 0 0 1px var(--amber);
  border-top-color: var(--khaki) !important; border-right-color: var(--khaki) !important; border-bottom-color: var(--khaki) !important;
}
@media (max-width: 520px) {
  .pt-row.pts .in.tbm-trigger { padding: 8px 14px 8px 5px; background-position: right 4px center; }
  .pt-row .in.tbm-trigger { padding: 8px 18px 8px 6px; font-size: 12px; background-position: right 5px center; }
}

.tbm-panel.tbm-p-field { max-width: calc(100vw - 16px); }
.tbm-panel.tbm-p-field .tbm-opt {
  font-family: var(--f-typewriter); font-weight: 400; font-size: 14px; letter-spacing: .2px; text-transform: none;
}
.tbm-panel.tbm-p-field .tbm-opt[aria-selected="true"] { font-weight: 400; }
.tbm-panel.tbm-up { border-top: 1px solid var(--amber-dark); border-bottom: 3px solid var(--amber); transform-origin: bottom left; }
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
  font-size: 12px; letter-spacing: .5px; padding: 8px 12px; display: none; overflow-wrap: anywhere; }
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
.pt-row.pts, .pt-head.pts { grid-template-columns: 30px minmax(0, 1fr) 58px 62px 66px 34px; }
.pt-row.pts input.in[data-k="alt"], .pt-row.pts input.in[data-k="gs"] { padding: 8px 5px 8px 7px; }
.in:disabled { background: transparent; border: 1px dashed var(--amber-dark); color: var(--khaki-light); -webkit-text-fill-color: var(--khaki-light);
  text-align: center; cursor: not-allowed; opacity: 1; padding-left: 5px; }
.hint { font-size: 11.5px; color: var(--khaki-light); letter-spacing: .3px; line-height: 1.45; margin: 8px 0 0; }
.ed-warn { font-size: 11px; letter-spacing: 1px; color: var(--amber); border-left: 3px solid var(--red-stamp); background: rgba(0,0,0,.18);
  padding: 5px 8px; margin: 6px 0 12px; }
.ed-warn[hidden] { display: none; }

.hdg { display: flex; gap: 8px; align-items: end; margin-bottom: 12px; flex-wrap: wrap; }
.hdg .tb-group .tb-btn { height: 40px; }
.hdg .decl { width: 110px; }
.hdg + .hint { margin: -4px 0 12px; }
.nav-set { gap: 12px 16px; }
.nav-set .gs { width: 132px; }
.nav-set .gs .lbl { white-space: nowrap; }
.nav-set .lbl { margin-bottom: 6px; }
/* lot mp-rp-declinaison : maquette_declinaison.css (valeur pour valeur) — la déclinaison calculée */
.hdg.dv-row { margin-bottom: 8px; }
.dv-year { width: 92px; }
.dv-year .in:disabled { opacity: .55; }
.dv-nolbl::before { content: none; }          /* le libellé vide au-dessus de « Forcer » : sans son ► */
.dv-src { font-size: 11.5px; letter-spacing: .3px; color: var(--khaki-light); line-height: 1.45; margin: 0 0 12px; }
.dv-src b { color: var(--amber); font-weight: 700; letter-spacing: 1px; text-transform: uppercase; font-size: 10.5px; margin-right: 6px; }
.dv-src .dv-file { color: #f0e8d6; }
#nav-body .dv-leg { color: var(--red-stamp); letter-spacing: .5px; }   /* la ligne « VAR −2,1° » d'un point : .co.alt.dv-leg */

/* fiche papier */
.sheet { background: var(--paper-light); color: #1f1c16; box-shadow: 0 2px 0 var(--paper-edge), 0 8px 18px rgba(0,0,0,.35); }
.sheet-top { background: #1f1c16; color: #f0e8d6; font-weight: 700; letter-spacing: 2px; font-size: 11px; padding: 6px 12px;
  display: flex; justify-content: space-between; }
table.nav { width: 100%; border-collapse: collapse; font-family: var(--f-mono); font-weight: 400; font-size: 12px; }
table.nav th { font-family: var(--f-ui); font-weight: 700; font-size: 10px; letter-spacing: 1.2px; text-align: left; padding: 6px 6px;
  border-bottom: 2px solid #1f1c16; text-transform: uppercase; }
table.nav td { padding: 5px 6px; border-bottom: 1px solid rgba(31,28,22,.18); vertical-align: top; }
table.nav tr.leg td { background: rgba(31,28,22,.06); color: #463f30; font-size: 11.5px; white-space: nowrap; }
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
/* temps écoulé sous le nom de chaque point ; chiffres des minutes ; boîtes de branche */
.wp-time { position: absolute; left: 34px; top: 22px; white-space: nowrap; font-family: var(--f-mono); font-weight: 400; font-size: 11px;
  line-height: 16px; color: #f0e8d6; background: var(--route); padding: 0 5px; }
.rp-tick-icon, .rp-tickn-icon { width: 0; height: 0; }
.rp-tick { position: absolute; top: -2.25px; height: 4.5px; transform-origin: 50% 50%; background: rgba(31,28,22,.45); }
.rp-tick > i { position: absolute; left: 0; right: 0; top: 1px; height: 2.5px; background: var(--route); }
.rp-tick.blk { background: rgba(240,232,214,.7); }
.rp-tick.blk > i { background: #1f1c16; }
.rp-tickn { display: inline-block; white-space: nowrap; transform: translate(-50%, -50%); font-family: var(--f-condensed); font-weight: 700; font-size: 12.5px; line-height: 1;
  color: var(--route); background: transparent;
  text-shadow: 0 0 2px rgba(240,232,214,.95), 0 0 2px rgba(240,232,214,.95), 0 0 3px rgba(240,232,214,.8); }
.rp-tickn.blk { color: #1f1c16; }
.lb-icon { width: 0; height: 0; }
.lb-pos { position: absolute; left: 0; top: 0; width: 0; height: 0; }
.lb { position: absolute; transform-origin: 50% 50%; box-sizing: border-box; user-select: none; -webkit-user-select: none; touch-action: none;
  filter: drop-shadow(0 1px 2px rgba(31,28,22,.55)); font-family: var(--f-mono); font-weight: 400; font-size: 12px; color: #1f1c16; }
.lb .lb-shape { position: absolute; left: 0; top: 0; display: block; overflow: visible; pointer-events: none; z-index: 0; }   /* « .leaflet-map-pane svg » lui donnerait z-index 200 */
.lb-bg { fill: rgba(240,232,214,.94); stroke: var(--route); stroke-width: 1.6; stroke-linejoin: miter; }
.lb-ln { fill: none; stroke: var(--route); stroke-width: 1.6; }
.lb-r { position: absolute; z-index: 1; left: 0; width: 100%; height: 19px; line-height: 19px; text-align: center; white-space: nowrap; }
.lb-r.lb-ete { color: var(--route); }
.lb-nm { position: absolute; z-index: 1; left: 0; width: 100%; height: 16px; line-height: 16px; padding: 0 4px; text-align: center; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  font-family: var(--f-condensed); font-weight: 700; font-size: 12px; letter-spacing: 1px; color: var(--route); }
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
#btn-airfields:disabled, #btn-towns:disabled { pointer-events: auto; cursor: not-allowed; }
/* villes DCS (lot rp-v1.5.0) : un point de 5 px et le nom à côté, posés sans chevauchement (pane « towns », z-index 370) ;
   le rectangle de l'étiquette est celui du bloc .tw, calculé en pixels (voir syncTowns) */
.tw-icon { width: 0; height: 0; }
.tw { position: absolute; display: block; cursor: pointer; }
.tw-dot { position: absolute; display: block; box-sizing: border-box; width: 5px; height: 5px; border-radius: 50%; background: #2e2a22; border: 1px solid #f0e8d6; }
.tw-nm { position: absolute; display: block; white-space: nowrap; font-family: var(--f-condensed); font-weight: 500; font-size: 11px; line-height: 13px; color: #2e2a22;
  text-shadow: 0 0 2px rgba(240,232,214,.95), 0 0 2px rgba(240,232,214,.95), 0 0 3px rgba(240,232,214,.8); }
.tw-nm.tw-cap { font-weight: 700; }     /* un nom entièrement en capitales (une grande ville) : Oswald 700, déjà embarquée */
/* recherche sur la carte : la loupe sous le zoom, son panneau à sa droite, l'anneau qui signale le résultat */
.rp-search .rp-search-btn { display: flex; align-items: center; justify-content: center; color: #1f1c16; }
.rp-search .rp-search-btn svg { display: block; width: 16px; height: 16px; flex: none; }
.sr-panel { position: absolute; top: 0; left: calc(100% + 6px); pointer-events: auto; box-sizing: border-box;
  background: var(--olive-deep); border: 2px solid var(--amber-dark); box-shadow: 0 2px 8px rgba(0,0,0,.4); cursor: default; }
.sr-panel[hidden] { display: none; }
.sr-head { display: flex; align-items: stretch; height: 44px; }
.sr-in { flex: 1 1 auto; min-width: 0; height: 44px; box-sizing: border-box; margin: 0; padding: 0 12px; border: 0; border-radius: 0; outline: none; -webkit-appearance: none; appearance: none;
  background: var(--paper-light); color: #1f1c16; font-family: var(--f-ui); font-weight: 500; font-size: 15px; }
.sr-in::placeholder { color: rgba(31,28,22,.5); }
.sr-in::-webkit-search-cancel-button, .sr-in::-webkit-search-decoration { -webkit-appearance: none; display: none; }
.sr-in:focus { box-shadow: inset 0 -3px 0 var(--amber); }
.sr-x { flex: none; width: 44px; height: 44px; margin: 0; padding: 0; border: 0; border-left: 1px solid var(--khaki); background: transparent; color: var(--paper);
  font-family: var(--f-ui); font-weight: 500; font-size: 26px; line-height: 1; cursor: pointer; }
.sr-x:hover, .sr-x:focus-visible { background: var(--olive); color: var(--amber); outline: none; }
.sr-list { overflow-y: auto; overscroll-behavior: contain; scrollbar-width: thin; scrollbar-color: var(--amber-dark) transparent; }
.sr-list[hidden] { display: none; }
.sr-row { display: flex; align-items: center; gap: 10px; min-height: 44px; box-sizing: border-box; padding: 0 12px; border-top: 1px solid rgba(168,154,114,.25); cursor: pointer; user-select: none; -webkit-user-select: none; }
.sr-row.active { background: var(--olive); }
.sr-row.none { cursor: default; }
.sr-nm { flex: 1 1 auto; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-family: var(--f-ui); font-weight: 500; font-size: 14px; color: var(--paper-light); }
.sr-kd { flex: 0 1 auto; min-width: 0; max-width: 50%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-family: var(--f-ui); font-weight: 500; font-size: 11px; letter-spacing: 1px; color: var(--amber); }
.sr-ring-icon { width: 0; height: 0; }
.sr-ring { position: absolute; left: 0; top: 0; display: block; box-sizing: border-box; width: 12px; height: 12px; margin: -6px 0 0 -6px; border: 3px solid #ff6a00; border-radius: 50%;
  background: transparent; pointer-events: none; animation: sr-pulse 1s ease-out 3 both; }
@keyframes sr-pulse {
  from { width: 12px; height: 12px; margin: -6px 0 0 -6px; opacity: 1; }
  to { width: 44px; height: 44px; margin: -22px 0 0 -22px; opacity: 0; }
}
@media (prefers-reduced-motion: reduce) { .sr-ring { animation: none; width: 32px; height: 32px; margin: -16px 0 0 -16px; } }
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

/* ---------- calques CombatFlite (lot rp-v1.4.0) ---------- */
.ed-section[hidden] { display: none; }
/* le pane des calques (z-index 390) : le tracé vectoriel dessous, les symboles et les noms (marqueurs) dessus ;
   « .leaflet-map-pane svg » donnerait z-index 200 à son SVG, au-dessus de tout marqueur de petite ordonnée */
.leaflet-map-pane .leaflet-layers-pane > svg { z-index: 0; max-width: none !important; max-height: none !important; }
.cf-pt-icon { width: 18px; height: 18px; }
.cf-pt-icon::before { content: ''; position: absolute; left: -9px; top: -9px; right: -9px; bottom: -9px; }   /* toucher de 36 px */
.cf-pt-icon svg { position: absolute; left: 0; top: 0; z-index: 0; display: block; overflow: visible; pointer-events: none; }
.cf-pt-nm { position: absolute; z-index: 1; left: 22px; top: 50%; transform: translateY(-50%); white-space: nowrap; pointer-events: none;
  font-family: var(--f-condensed); font-weight: 500; font-size: 10.5px; line-height: 1.2; color: #1f1c16;
  text-shadow: 0 0 2px rgba(240,232,214,.95), 0 0 2px rgba(240,232,214,.95), 0 0 3px rgba(240,232,214,.8); }
.cf-name-icon, .cf-tx-icon { width: 0; height: 0; }
.cf-name { position: absolute; z-index: 1; display: inline-block; transform: translate(-50%, -50%); white-space: nowrap; pointer-events: none;
  font-family: var(--f-condensed); font-weight: 700; font-size: 11px; line-height: 1;
  text-shadow: 0 0 2px rgba(240,232,214,.95), 0 0 2px rgba(240,232,214,.95), 0 0 3px rgba(240,232,214,.8); }
.cf-tx { position: absolute; z-index: 1; display: block; transform: translate(-50%, -50%); box-sizing: border-box; white-space: pre; text-align: center;
  font-family: var(--f-condensed); line-height: 1.15; padding: 2px 6px; user-select: none; -webkit-user-select: none; }
.cf-popup .leaflet-popup-content-wrapper { background: var(--paper-light); color: var(--ink); border: 2px solid var(--ink); border-radius: 2px; box-shadow: 0 4px 16px rgba(0,0,0,.45); }
.cf-popup .leaflet-popup-tip { background: var(--paper-light); box-shadow: none; }
.cf-popup .leaflet-popup-content { margin: 10px 14px 12px; min-width: 150px; font-family: var(--f-typewriter); font-weight: 400; font-size: 12px; line-height: 1.45; }
.cf-popup a.leaflet-popup-close-button { top: 0; right: 0; width: 44px; height: 44px; padding: 0; font: 400 26px/44px var(--f-typewriter); color: var(--ink); text-align: center; }
.cf-popup a.leaflet-popup-close-button:hover, .cf-popup a.leaflet-popup-close-button:focus-visible { color: var(--amber-dark); outline: none; }
.cf-f-nm { font-family: var(--f-condensed); font-weight: 700; font-size: 14px; letter-spacing: .5px; line-height: 1.25; margin: 0 0 4px; padding-right: 30px; overflow-wrap: anywhere; }
.cf-f-l { overflow-wrap: anywhere; }
.cf-f-mgrs { font-family: var(--f-mono); font-weight: 400; margin-top: 2px; }
.cf-fiche .rt-btn { display: block; width: 100%; margin-top: 10px; min-height: 44px; padding: 8px 12px; letter-spacing: 1.5px; font-size: 12px; text-transform: none; }
/* section « Calques » du panneau */
.cf-row { display: flex; align-items: center; gap: 4px; min-height: 44px; }
.cf-vis { display: flex; align-items: center; justify-content: center; width: 44px; height: 44px; flex: none; cursor: pointer; }
.cf-vis input { width: 20px; height: 20px; margin: 0; accent-color: var(--amber); cursor: pointer; }
.cf-main { flex: 1 1 auto; min-width: 0; display: flex; flex-wrap: wrap; align-items: baseline; justify-content: space-between; gap: 0 10px; padding: 4px 0; }
.cf-nm { font-family: var(--f-ui); font-weight: 500; font-size: 14px; color: var(--paper); overflow-wrap: anywhere; }
.cf-n { margin-left: auto; font-family: var(--f-ui); font-weight: 500; font-size: 11px; color: var(--khaki-light); text-align: right; }
.cf-del { width: 44px; height: 44px; flex: none; padding: 0; border: 1px solid var(--khaki); background: transparent; color: var(--khaki-light); font-size: 24px; line-height: 1; cursor: pointer; }
.cf-del:hover, .cf-del:focus-visible { border-color: var(--red-faded); color: var(--paper-light); background: var(--rust); outline: none; }
.cf-clear { width: 100%; height: 44px; margin-top: 8px; }
/* fenêtres « Calques CombatFlite » et « Exporter » : la structure des fenêtres du Route Tool, la livrée de la maquette */
.cf-modal .rt-panel { background: var(--olive-dark); color: var(--paper); border: 1px solid var(--khaki); border-radius: 0; padding: 16px 20px; max-width: 460px; font-family: var(--f-ui); font-weight: 500; }
.cf-modal .rt-panel h2 { font-family: var(--f-stencil); font-weight: 700; font-size: 17px; letter-spacing: 2px; text-transform: none; color: var(--amber); margin: 4px 44px 10px 0; }
.cf-modal .rt-close { color: var(--paper); font-size: 30px; }
.cf-modal .rt-close:hover, .cf-modal .rt-close:focus-visible { color: var(--amber); }
.cf-modal .rt-file { font-size: 12px; margin: 0 0 2px; opacity: 1; color: var(--khaki-light); }
.cf-modal .rt-note { font-size: 12px; opacity: 1; color: var(--khaki-light); margin: 0 0 8px; }
.cf-modal .rt-list { max-height: none; overflow: visible; border: none; background: none; padding: 0; margin: 0 0 12px; }
.cf-modal .rt-row { gap: 12px; padding: 0; font-size: 14px; }
.cf-modal .rt-row + .rt-row { border-top: 1px solid rgba(168,154,114,.25); }
.cf-modal .rt-row input { width: 20px; height: 20px; accent-color: var(--amber); }
.cf-modal .rt-nm { font-weight: 500; }
.cf-modal .rt-n { white-space: normal; text-align: right; max-width: 55%; font-size: 11px; opacity: 1; color: var(--khaki-light); }
.cf-modal .rt-actions { justify-content: flex-end; gap: 8px; margin-top: 4px; }
.cf-modal .rt-btn { flex: 0 0 auto; padding: 8px 16px; font-family: var(--f-ui); font-weight: 700; font-size: 12px; letter-spacing: 1.5px; color: var(--paper); border: 2px solid var(--khaki); }
.cf-modal .rt-btn:hover, .cf-modal .rt-btn:focus-visible { background: var(--olive); border-color: var(--amber); color: var(--amber); }
.cf-modal .rt-btn.go { background: transparent; color: var(--amber); border-color: var(--amber); }
.cf-modal .rt-btn.go:hover, .cf-modal .rt-btn.go:focus-visible { background: var(--olive); color: var(--paper-light); }
.cf-modal .rt-btn:disabled { opacity: .35; }

/* ---------- toast ---------- */
.toast {
  position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%) translateY(100px);
  background: var(--olive-dark); border: 1px solid var(--amber); color: var(--paper);
  font-family: var(--f-ui); font-weight: 700; letter-spacing: 2px; text-transform: uppercase; font-size: 12px;
  padding: 10px 20px; z-index: 20000; opacity: 0; transition: all .3s ease; pointer-events: none;
  box-shadow: 0 4px 16px rgba(0,0,0,.6); max-width: 92vw; text-align: center;
}
.toast.show { opacity: 1; transform: translateX(-50%) translateY(0); pointer-events: auto; }

/* ---------- le mode Dessin et la séparation carte / panneau (lot rp-v1.6.0) : les valeurs de la maquette, une pour une ---------- */
.rp-drawing .leaflet-overlay-pane, .rp-drawing .leaflet-marker-pane, .rp-drawing .leaflet-refs-pane,
.rp-drawing .leaflet-legticks-pane, .rp-drawing .leaflet-legnums-pane, .rp-drawing .leaflet-legboxes-pane {
  opacity: .32; pointer-events: none !important; }
.rp-drawing .leaflet-overlay-pane *, .rp-drawing .leaflet-marker-pane *, .rp-drawing .leaflet-refs-pane *,
.rp-drawing .leaflet-legnums-pane *, .rp-drawing .leaflet-legboxes-pane *,
.rp-drawing .leaflet-airfields-pane *, .rp-drawing .leaflet-towns-pane * { pointer-events: none !important; }
.leaflet-drawedit-pane { z-index: 640; }

.tapmode .tb-btn[data-tap="draw"] { gap: 5px; }
.tapmode .tb-btn[data-tap="draw"] svg { width: 13px; height: 13px; flex: none; }

/* la barre du bas */
.dr-ui { position: absolute; left: 10px; right: 10px; bottom: 26px; z-index: 1000; display: flex; flex-direction: column; gap: 6px;
  pointer-events: none; font-family: var(--f-ui); }
.dr-ui > * { pointer-events: auto; }
.dr-ui[hidden] { display: none; }
.dr-hint { align-self: center; max-width: 100%; box-sizing: border-box; display: flex; align-items: center; gap: 8px;
  background: var(--olive-deep); border: 2px solid var(--amber-dark); box-shadow: 0 2px 8px rgba(0,0,0,.4);
  color: var(--paper-light); padding: 4px 4px 4px 12px; min-height: 44px; }
.dr-hint[hidden] { display: none; }
.dr-hint .dr-msg { font-family: var(--f-ui); font-weight: 500; font-size: 13px; letter-spacing: .3px; line-height: 1.25; }
.dr-hint .dr-msg b { font-weight: 700; color: var(--amber); letter-spacing: 1.2px; text-transform: uppercase; margin-right: 6px; }
.dr-hint .tb-btn { height: 36px; font-size: 11px; padding: 0 10px; border-color: var(--khaki); }
.dr-hint .tb-btn.go { background: var(--amber-dark); color: var(--paper-light); border-color: var(--amber); }
.dr-hint .dr-acts { display: flex; gap: 4px; flex: none; }

.dr-bar { display: flex; align-items: stretch; gap: 8px; background: var(--olive-deep); border: 2px solid var(--amber-dark);
  box-shadow: 0 2px 8px rgba(0,0,0,.45); padding: 6px; box-sizing: border-box; }
.dr-chip { display: flex; flex-direction: column; justify-content: center; align-items: flex-start; gap: 1px; min-width: 0; flex: 0 1 150px;
  background: transparent; border: 1px solid var(--khaki); color: var(--paper-light); padding: 4px 26px 4px 10px; position: relative; cursor: pointer;
  text-align: left; min-height: 52px; font-family: var(--f-ui); }
.dr-chip small { font-weight: 700; font-size: 9.5px; letter-spacing: 1.5px; color: var(--amber); text-transform: uppercase; }
.dr-chip span { font-weight: 500; font-size: 14px; letter-spacing: .3px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 100%; }
.dr-chip::after { content: ''; position: absolute; right: 9px; top: 50%; width: 7px; height: 7px; margin-top: -6px;
  border-right: 2px solid var(--amber); border-bottom: 2px solid var(--amber); transform: rotate(45deg); }
.dr-chip.open::after { transform: rotate(-135deg); margin-top: -2px; }
.dr-tools { display: flex; flex: 1 1 auto; justify-content: flex-end; gap: 0; min-width: 0; }
.dr-tool { display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 3px; flex: 1 1 0; min-width: 44px; max-width: 72px;
  min-height: 52px; background: transparent; color: var(--paper); border: 1px solid var(--khaki); border-left: none; cursor: pointer; padding: 4px 2px; }
.dr-tool:first-child { border-left: 1px solid var(--khaki); }
.dr-tool svg { width: 22px; height: 22px; display: block; }
.dr-tool i { font-style: normal; font-weight: 700; font-size: 9.5px; letter-spacing: 1px; text-transform: uppercase; line-height: 1; }
.dr-tool.on { background: var(--amber-dark); color: var(--paper-light); border-color: var(--amber); box-shadow: inset 0 -3px 0 var(--amber); }
.dr-tool.danger { color: #f0a090; }
.dr-sel { flex: 1 1 auto; min-width: 0; display: flex; flex-direction: column; justify-content: center; padding: 0 6px; color: var(--paper-light); }
.dr-sel small { font-weight: 700; font-size: 9.5px; letter-spacing: 1.5px; color: var(--amber); text-transform: uppercase; }
.dr-sel span { font-family: var(--f-mono); font-size: 13px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.dr-bar.selmode .dr-tools { flex: 0 0 auto; }
.dr-bar.selmode .dr-tool { width: 60px; flex: none; }

/* le menu des calques */
.dr-pop { position: absolute; left: 0; bottom: calc(100% + 6px); width: 280px; max-width: 100%; box-sizing: border-box;
  background: var(--olive-deep); border: 2px solid var(--amber-dark); box-shadow: 0 4px 14px rgba(0,0,0,.5); color: var(--paper-light); padding: 6px; }
.dr-pop[hidden] { display: none; }
.dr-pop h4 { margin: 4px 6px 6px; font-weight: 700; font-size: 10px; letter-spacing: 1.5px; color: var(--amber); text-transform: uppercase; }
.dr-ly { display: flex; align-items: center; gap: 10px; min-height: 44px; padding: 0 8px; border: 1px solid transparent; cursor: pointer; }
.dr-ly.on { border-color: var(--amber); background: rgba(192,137,42,.16); }
.dr-ly .nm { flex: 1; font-weight: 500; font-size: 14px; }
.dr-ly .n { font-family: var(--f-mono); font-size: 11px; color: var(--khaki-light); }
.dr-ly.ro { cursor: default; opacity: .7; }
.dr-ly .lock { width: 14px; height: 14px; color: var(--khaki-light); flex: none; }
.dr-ly .dot { width: 14px; height: 14px; border-radius: 50%; border: 2px solid var(--khaki-light); flex: none; box-sizing: border-box; }
.dr-ly.on .dot { border-color: var(--amber); background: radial-gradient(circle, var(--amber) 0 3px, transparent 4px); }
.dr-new { display: flex; gap: 4px; margin-top: 6px; border-top: 1px dashed var(--khaki); padding-top: 6px; }
.dr-new input { flex: 1; min-width: 0; height: 40px; box-sizing: border-box; font-family: var(--f-mono); font-size: 14px; padding: 0 8px;
  background: var(--paper-light); color: var(--ink); border: 1px solid var(--khaki); border-left: 3px solid var(--amber-dark); }
.dr-new .tb-btn { height: 40px; }

/* la fiche de propriétés (feuille du bas) */
.dr-sheet { position: absolute; right: 10px; bottom: 100px; width: 340px; max-width: calc(100% - 20px); box-sizing: border-box; z-index: 1001;
  background: var(--olive-deep); border: 2px solid var(--amber-dark); box-shadow: 0 4px 14px rgba(0,0,0,.5); color: var(--paper-light);
  padding: 10px 12px 12px; font-family: var(--f-ui); max-height: calc(100% - 130px); overflow: auto; }
.dr-sheet[hidden] { display: none; }
.dr-sheet .sh-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px; }
.dr-sheet .sh-head b { font-weight: 700; font-size: 11px; letter-spacing: 1.5px; color: var(--amber); text-transform: uppercase; }
.dr-sheet .sh-x { width: 40px; height: 40px; background: transparent; border: 1px solid var(--khaki); color: var(--paper); font-size: 18px; cursor: pointer; }
.dr-f { margin-top: 8px; }
.dr-f > label { display: block; font-weight: 700; font-size: 9.5px; letter-spacing: 1.5px; color: var(--amber); text-transform: uppercase; margin-bottom: 4px; }
.dr-f input[type=text], .dr-f input[type=number], .dr-f select { width: 100%; height: 40px; box-sizing: border-box; font-family: var(--f-mono); font-size: 14px;
  padding: 0 8px; background: var(--paper-light); color: var(--ink); border: 1px solid var(--khaki); border-left: 3px solid var(--amber-dark); }
.dr-row2 { display: flex; gap: 8px; } .dr-row2 > .dr-f { flex: 1; min-width: 0; }
.dr-sw { display: flex; gap: 6px; flex-wrap: wrap; }
.dr-sw button { width: 36px; height: 36px; border: 2px solid var(--khaki); cursor: pointer; padding: 0; position: relative; }
.dr-sw button.on { border-color: var(--amber); box-shadow: 0 0 0 2px var(--olive-deep), 0 0 0 4px var(--amber); }
.dr-seg { display: flex; } .dr-seg .tb-btn { flex: 1; height: 40px; min-width: 0; padding: 0 6px; }
.dr-seg .tb-btn svg { width: 28px; height: 10px; }
.dr-f-in { flex: 0 0 132px !important; }

/* poignées : 44 px de cible, 16 px visibles */
.dr-h { background: none; border: none; }
.dr-h i { position: absolute; left: 50%; top: 50%; width: 16px; height: 16px; margin: -8px 0 0 -8px; box-sizing: border-box;
  background: var(--paper-light); border: 2px solid var(--amber-dark); box-shadow: 0 1px 3px rgba(0,0,0,.6); }
.dr-h.v i { border-radius: 2px; }
.dr-h.v.on i { background: var(--amber); border-color: var(--ink); width: 20px; height: 20px; margin: -10px 0 0 -10px; }
.dr-h.r i { border-radius: 50%; background: var(--amber); border-color: var(--ink); }
.dr-h.mid i { width: 14px; height: 14px; margin: -7px 0 0 -7px; border-radius: 50%; background: rgba(227,214,181,.75); border: 1.5px solid var(--amber-dark);
  font-style: normal; font-weight: 700; font-size: 12px; line-height: 10px; text-align: center; color: var(--amber-dark); }
.dr-h.mv i { width: 26px; height: 26px; margin: -13px 0 0 -13px; border-radius: 50%; background: var(--olive-deep); border-color: var(--amber); color: var(--amber); }
.dr-h.mv i svg { width: 16px; height: 16px; margin: 3px; display: block; }
.dr-h.first i { width: 22px; height: 22px; margin: -11px 0 0 -11px; background: var(--amber); }
.dr-rlab { background: var(--olive-deep); color: var(--amber); font-family: var(--f-mono); font-size: 12px; padding: 2px 6px; border: 1px solid var(--amber-dark);
  white-space: nowrap; transform: translate(calc(-100% - 16px), -11px); display: inline-block; }

@media (max-width: 600px) {
  .dr-ui { left: 6px; right: 6px; }
  .dr-bar { flex-wrap: wrap; gap: 6px; }
  .dr-chip { flex: 1 1 100%; min-height: 40px; flex-direction: row; align-items: center; gap: 8px; }
  .dr-chip small { font-size: 9px; }
  .dr-tool { min-height: 50px; }
  .dr-bar.selmode .dr-chip { display: none; }
  .dr-bar.selmode .dr-tool { width: 52px; }
  .dr-sheet { left: 6px; right: 6px; width: auto; max-width: none; bottom: 94px; }
  .dr-hint .dr-msg { font-size: 12px; }
  .dr-sheet { padding: 8px 10px 10px; bottom: 90px; max-height: calc(100% - 100px); }
  .dr-f { margin-top: 6px; }
  .dr-sw { gap: 5px; } .dr-sw button { width: 34px; height: 34px; }
  .dr-f-in { flex: 0 0 120px !important; }
  .dr-sheet .sh-x { width: 36px; height: 36px; }
}
.rp-drawing .leaflet-layers-pane, .rp-drawing .leaflet-layers-pane * { pointer-events: none !important; }

/* la séparation carte / panneau : en portrait seulement */
.rp-split { display: none; }
@media (max-width: 1099px) and ((min-height: 600px) or (orientation: portrait)) {
  .app { grid-template-rows: auto 26px minmax(0, 1fr) !important; }
  .mapwrap { border-bottom: none !important; }
  .rp-split { display: flex; align-items: center; justify-content: center; height: 26px; cursor: row-resize; touch-action: none; user-select: none;
    background: var(--olive-deep); border-top: 2px solid var(--amber-dark); border-bottom: 1px solid var(--khaki); position: relative; z-index: 2; }
  .rp-split .grip { width: 64px; height: 10px; box-sizing: border-box; border-top: 2px solid var(--khaki-light); border-bottom: 2px solid var(--khaki-light);
    position: relative; }
  .rp-split .grip::after { content: ''; position: absolute; left: 0; right: 0; top: 2px; border-top: 2px solid var(--khaki-light); }
  .rp-split.on, .rp-split:hover { background: var(--olive-dark); }
  .rp-split.on .grip, .rp-split.on .grip::after { border-color: var(--amber); }
}

/* lot rp-v1.7.0 : maquette_dessin_17.css (R297, valeur pour valeur) — orbites, boîtes, courbes, FLOT, couloirs ; les réglages pendant la création.
   .dr-h.v.rot (losange) n'est plus utilisé : la boîte a des barrettes de bord (.dr-h.v.edge) et une poignée de rotation (.dr-h.r.rot) ; la règle reste, sans élément. */
.dr-h.v.rot i { background: var(--amber); border-color: var(--ink); transform: rotate(45deg); }
.mq-step { display: flex; align-items: stretch; height: 40px; }
.mq-step .tb-btn { height: 40px; min-width: 40px; padding: 0; font-size: 18px; }
.mq-step span { flex: 1; display: flex; align-items: center; justify-content: center; min-width: 30px; font-family: var(--f-mono); font-size: 15px;
  background: var(--paper-light); color: var(--ink); border-top: 1px solid var(--khaki); border-bottom: 1px solid var(--khaki); }
.mq-gshow { flex: 0 0 132px !important; }
.mq-turn { flex: 0 0 150px !important; }
.mq-cw { flex: 0 0 110px !important; }
.mq-flip { width: 100%; height: 40px; }
@media (max-width: 600px) {
  .dr-tool { min-width: 0; padding: 4px 0; }
  .dr-tool i { font-size: 8.5px; letter-spacing: .4px; }
  .dr-tool svg { width: 21px; height: 21px; }
  .mq-gshow { flex: 0 0 104px !important; }
  .mq-turn { flex: 0 0 132px !important; }
  .mq-cw { flex: 0 0 96px !important; }
  .dr-sheet .dr-row2 { gap: 6px; }
}
.dr-h.v.edge i { width: 22px; height: 10px; margin: -5px 0 0 -11px; border-radius: 2px; background: var(--paper-light); }
.dr-h.v.corner i { width: 14px; height: 14px; margin: -7px 0 0 -7px; border-radius: 2px; background: var(--paper-light); border: 2px solid var(--amber-dark); }
.dr-h.r.rot i { width: 22px; height: 22px; margin: -11px 0 0 -11px; }
.dr-h.r.rot i::after { content: '⟳'; position: absolute; inset: 0; font: 700 15px/18px var(--f-ui); color: var(--ink); text-align: center; }
.dr-hint .tb-btn.mq-props svg { width: 18px; height: 18px; }
.dr-hint .tb-btn.mq-props.on { background: var(--amber-dark); border-color: var(--amber); }

/* ce que la maquette ne dit pas (lot rp-v1.7.0) : « À gauche » et « Afficher / Masquer » tiennent sur une ligne dans les 150 / 132 px (104 sous 600 px) de la maquette */
.mq-turn .dr-seg .tb-btn, .mq-gshow .dr-seg .tb-btn { font-size: 10.5px; letter-spacing: .6px; padding: 0 3px; white-space: nowrap; }
@media (max-width: 600px) { .mq-turn .dr-seg .tb-btn, .mq-gshow .dr-seg .tb-btn { letter-spacing: 0; padding: 0 1px; } }
/* ce que la maquette ne dit pas : le svg du pane d'édition sous ses poignées, leurs gestes, le cadenas, les rangées du menu, le message sans boutons */
.leaflet-map-pane .leaflet-drawedit-pane > svg { z-index: 0; max-width: none !important; max-height: none !important; }
.dr-h { touch-action: none; -webkit-user-select: none; user-select: none; cursor: grab; }
.dr-rlab-icon { width: 0; height: 0; }
.dr-hint .dr-acts[hidden] { display: none; }
.dr-tool:hover, .dr-tool:focus-visible, .dr-chip:hover, .dr-chip:focus-visible { border-color: var(--amber); outline: none; }
.dr-ly .lock svg { display: block; width: 14px; height: 14px; }
.dr-ly .nm { min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.dr-ly .tb-btn { flex: none; align-self: stretch; height: auto; min-height: 40px; padding: 0 8px; font-size: 10px; letter-spacing: 1px; }
.dr-seg .tb-btn + .tb-btn { border-left: none; }
.dr-sheet .sh-x:hover, .dr-sheet .sh-x:focus-visible { border-color: var(--amber); outline: none; }
.dr-f input:focus, .dr-f select:focus, .dr-new input:focus { outline: none; border-left-color: var(--red-stamp); box-shadow: 0 0 0 1px var(--amber); }
.rp-split:focus-visible { outline: 2px solid var(--amber); outline-offset: -2px; }
/* la liste « Type » de la fiche prend la liste du module (le <select> reste, masqué) ; le bouton garde l'aspect d'un champ de la fiche
   (les valeurs de « .dr-f select ») et un chevron de la puce « Calque » ; rien de .tb-sel ni de .tbm-trigger n'en change l'aspect fermé */
.dr-f .tbm-trigger { display: block; position: relative; width: 100%; height: 40px; box-sizing: border-box; margin: 0; text-align: left; cursor: pointer;
  font-family: var(--f-mono); font-size: 14px; font-weight: 400; line-height: normal; letter-spacing: normal; text-transform: none; white-space: nowrap;
  padding: 0 8px; background: var(--paper-light); color: var(--ink); border: 1px solid var(--khaki); border-left: 3px solid var(--amber-dark); border-radius: 0; }
.dr-f .tbm-trigger .tbm-lbl { margin: 0; padding: 0; }
.dr-f .tbm-trigger::after { content: ''; position: absolute; right: 9px; top: 50%; width: 7px; height: 7px; margin-top: -6px;
  border-right: 2px solid var(--amber); border-bottom: 2px solid var(--amber); transform: rotate(45deg); pointer-events: none; }
.dr-f .tbm-trigger.tbm-trigger-open::after { transform: rotate(-135deg); margin-top: -2px; }
.dr-f .tbm-trigger:focus-visible { outline: none; border-left-color: var(--red-stamp); box-shadow: 0 0 0 1px var(--amber); }

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
/* En portrait (sous 1 100 px de large, à partir de 600 px de haut, ou toute fenêtre plus haute que large : le clavier virtuel ne la fait pas
   changer de mise en page) la page ne défile plus : la carte reste en haut, à sa hauteur, et seul le panneau, dessous, défile.
   Sous 600 px de haut en paysage, la page défile comme ci-dessus. */
@media (max-width: 1099px) and ((min-height: 600px) or (orientation: portrait)) {
  .app { position: fixed; top: 56px; bottom: 0; left: 0; right: 0; padding-top: 0; display: grid; grid-template-columns: minmax(0, 1fr); grid-template-rows: auto minmax(0, 1fr); }
  .mapwrap { min-width: 0; }
  .panel { overflow-y: auto; overscroll-behavior: contain; -webkit-overflow-scrolling: touch; min-height: 0; }
}
@media (max-width: 520px) {
  .pt-row, .pt-head { grid-template-columns: 28px 1fr 62px 80px 30px; gap: 4px; }
  .pt-row.pts, .pt-head.pts { grid-template-columns: 28px minmax(0, 1fr) 62px 54px 64px 30px; }
  .pt-row.pts select.in { padding: 8px 14px 8px 5px; background-position: right 4px center; }
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
  <button type="button" class="tb-btn" id="btn-towns" aria-pressed="true" data-i18n="tb.towns" data-i18n-title="tb.towns.tip" title="Villes DCS (à partir du zoom 10)">Villes</button>
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
    <div class="dr-ui" id="dr-ui" hidden>
      <div class="dr-hint" id="dr-hint" role="status" hidden><span class="dr-msg" id="dr-msg"></span><span class="dr-acts" id="dr-acts"></span></div>
      <div class="dr-bar" id="dr-bar" role="toolbar"></div>
      <div class="dr-pop" id="dr-pop" hidden>
        <h4 data-i18n="dr.menu.title">Dessiner dans</h4>
        <div id="dr-ly-list"></div>
        <div class="dr-new"><input type="text" id="dr-ly-name" maxlength="40" autocomplete="off" spellcheck="false" data-i18n-placeholder="dr.menu.name" data-i18n-aria-label="dr.menu.name" placeholder="Nom du calque" aria-label="Nom du calque"><button type="button" class="tb-btn" data-dr="newlayer" data-i18n="dr.menu.add">+ Calque</button></div>
      </div>
    </div>
    <div class="dr-sheet" id="dr-sheet" role="group" hidden></div>
  </section>
  <div class="rp-split" id="rp-split" role="separator" aria-orientation="horizontal" tabindex="0" data-i18n-title="sp.title" data-i18n-aria-label="sp.title" title="Glissez pour agrandir ou réduire la carte ; touchez deux fois pour revenir à la taille d'origine" aria-label="Glissez pour agrandir ou réduire la carte ; touchez deux fois pour revenir à la taille d'origine"><div class="grip"></div></div>
  <aside class="panel" id="panel">
    <div class="ed-section" data-section="route">
      <div class="ed-head"><span class="ed-title" data-i18n="sec.route">Route</span><small id="pt-count"></small></div>
      <div class="ed-body">
        <div class="rn">
          <label class="lbl" for="route-name" data-i18n="f.name">Nom de la route</label>
          <input class="in" id="route-name" type="text" maxlength="60" autocomplete="off" spellcheck="false">
        </div>
        <div class="pt-head pts"><span data-i18n="th.no">N°</span><span data-i18n="th.name">Nom</span><span id="alt-unit"></span><span id="spd-unit"></span><span data-i18n="th.ref">Réf.</span><span></span></div>
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
    <div class="ed-section" data-section="layers" id="sec-layers" hidden>
      <div class="ed-head"><span class="ed-title" data-i18n="sec.layers">Calques</span><small id="layers-count"></small></div>
      <div class="ed-body">
        <div id="layers-list"></div>
        <button type="button" class="tb-btn cf-clear" id="btn-layers-clear" data-i18n="layers.removeAll">Retirer tous les calques</button>
        <p class="hint" data-i18n="layers.help">En mode Lire, touchez un objet pour lire sa fiche. En mode Point ou Réf., une cible touchée devient un point de la route ou une référence. En mode Dessin, vous créez et modifiez vos propres calques.</p>
      </div>
    </div>
    <div class="ed-section" data-section="nav">
      <div class="ed-head"><span class="ed-title" data-i18n="sec.nav">Navigation</span></div>
      <div class="ed-body">
        <div class="hdg nav-set">
          <div><div class="lbl" data-i18n="f.lbx">Boîtes de branche</div><span class="tb-group" role="group" data-i18n-aria-label="f.lbx" aria-label="Boîtes de branche"><button type="button" class="tb-btn" data-lbx="none" aria-pressed="false" data-i18n="lbx.none">Aucune</button><button type="button" class="tb-btn" data-lbx="min" aria-pressed="false" data-i18n="lbx.min">Minimale</button><button type="button" class="tb-btn" data-lbx="full" aria-pressed="true" data-i18n="lbx.full">Complète</button></span></div>
          <div class="gs"><label class="lbl" for="gs-def" id="gs-lbl"></label><input class="in" id="gs-def" type="text" inputmode="numeric" autocomplete="off" spellcheck="false"></div>
          <div><div class="lbl" data-i18n="f.trace">Tracé</div><span class="tb-group" role="group" data-i18n-aria-label="f.trace" aria-label="Tracé"><button type="button" class="tb-btn" data-trc="route" aria-pressed="true" data-i18n="col.route">Couleur</button><button type="button" class="tb-btn" data-trc="black" aria-pressed="false" data-i18n="col.black">Noir</button></span></div>
          <div><div class="lbl" data-i18n="f.ticks">Traits des minutes</div><span class="tb-group" role="group" data-i18n-aria-label="f.ticks" aria-label="Traits des minutes"><button type="button" class="tb-btn" data-tck="route" aria-pressed="true" data-i18n="col.route">Couleur</button><button type="button" class="tb-btn" data-tck="black" aria-pressed="false" data-i18n="col.black">Noir</button></span></div>
        </div>
        <div class="hdg">
          <div><div class="lbl" data-i18n="f.ref">Cap</div><span class="tb-group" role="group"><button type="button" class="tb-btn" data-ref="true" aria-pressed="true" data-i18n="ref.true">Vrai</button><button type="button" class="tb-btn" data-ref="mag" aria-pressed="false" data-i18n="ref.mag">Magnétique</button></span></div>
        </div>
        <div id="dv-wrap" hidden>
          <div class="hdg dv-row">
            <div><div class="lbl" data-i18n="f.dv">Déclinaison</div><span class="tb-group" role="group" data-i18n-aria-label="f.dv" aria-label="Déclinaison"><button type="button" class="tb-btn" data-dvm="calc" aria-pressed="true" data-i18n="dv.calc">Calculée</button><button type="button" class="tb-btn" data-dvm="manual" aria-pressed="false" data-i18n="dv.manual">Saisie</button></span></div>
            <div class="dv-year" id="dv-year-w"><label class="lbl" for="dv-year" data-i18n="f.dvy">Année</label><input class="in" id="dv-year" type="text" inputmode="numeric" maxlength="4" autocomplete="off" spellcheck="false" placeholder="1985"></div>
            <div id="dv-force-w"><div class="lbl dv-nolbl" aria-hidden="true"></div><button type="button" class="tb-btn" id="dv-force" aria-pressed="false" data-i18n="dv.force">Forcer</button></div>
            <div class="decl" id="dv-decl-w"><label class="lbl" for="decl" data-i18n="f.decl">Déclinaison (°)</label><input class="in" id="decl" type="text" inputmode="decimal" autocomplete="off" spellcheck="false" data-i18n-placeholder="f.decl.ph" placeholder="+4,5"></div>
          </div>
          <p class="hint" id="dv-help" data-i18n="nav.decl.help"></p>
          <div class="ed-warn" id="decl-warn" role="alert" hidden data-i18n="nav.decl.warn"></div>
          <p class="dv-src" id="dv-src"></p>
        </div>
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

<!-- ===== FENÊTRE : CALQUES D'UN FICHIER COMBATFLITE ===== -->
<div class="rt-modal cf-modal" id="cf-import-modal" hidden role="dialog" aria-modal="true" aria-labelledby="cf-import-title">
  <div class="rt-backdrop" id="cf-import-backdrop"></div>
  <div class="rt-panel" role="document">
    <button type="button" class="rt-close" id="cf-import-close" data-i18n-aria-label="modal.close" aria-label="Fermer">&times;</button>
    <h2 id="cf-import-title" data-i18n="cf.import.title">Calques CombatFlite</h2>
    <p class="rt-file" id="cf-import-file"></p>
    <p class="rt-note" data-i18n="cf.import.note">Cochez les calques à afficher. Ils restent en lecture seule.</p>
    <div class="rt-list" id="cf-import-list"></div>
    <div class="rt-actions">
      <button type="button" class="rt-btn" id="cf-import-cancel" data-i18n="rt.cancel">Annuler</button>
      <button type="button" class="rt-btn go" id="cf-import-go" data-i18n="cf.import.go">Afficher</button>
    </div>
  </div>
</div>

<!-- ===== FENÊTRE : EXPORTER — CHOISIR CE QU'EMPORTE LE FICHIER ===== -->
<div class="rt-modal cf-modal" id="cf-export-modal" hidden role="dialog" aria-modal="true" aria-labelledby="cf-export-title">
  <div class="rt-backdrop" id="cf-export-backdrop"></div>
  <div class="rt-panel" role="document">
    <button type="button" class="rt-close" id="cf-export-close" data-i18n-aria-label="modal.close" aria-label="Fermer">&times;</button>
    <h2 id="cf-export-title" data-i18n="cf.exp.title">Exporter</h2>
    <div class="rt-list" id="cf-export-list"></div>
    <div class="rt-actions">
      <button type="button" class="rt-btn" id="cf-export-cancel" data-i18n="rt.cancel">Annuler</button>
      <button type="button" class="rt-btn go" id="cf-export-go" data-i18n="cf.exp.go">Exporter</button>
    </div>
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
   ROUTE PLANNER v1.8.1
   Une route sur une carte (points posés, saisis par coordonnées
   ou par cap et distance), des points de référence, les noms de lieux,
   les villes et les aérodromes DCS, une recherche sur la carte : caps, distances, vitesse sol et minutage,
   MGRS et DMS, envoyés dans la navigation d'une datacard ; les calques
   d'un fichier CombatFlite (.cf), en lecture seule, à part de la route ; le dessin tactile de calques propres
   (cercles, zones, lignes, points, textes). Monofichier ; seules les tuiles de carte viennent du réseau.
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
const GS_DEFAULT = 220;        /* vitesse sol par défaut de la route, km/h */
const GS_MAX_IN = 2000;        /* saisie d'une vitesse : entier de 1 à 2 000, dans l'unité affichée */
const LEGBOX_IDS = ['none', 'min', 'full'];
const BOX_MIN_PX = 60;         /* une branche de moins de 60 px à l'écran n'a pas de boîte */
const BOX_ROW_H = 19;          /* hauteur d'une ligne de la boîte */
const BOX_GAP = 16;            /* écart par défaut entre la branche et le bord de la boîte */
const BOX_LIMIT = 20000;       /* garde-fou : une place plus lointaine (en pixels) se lit comme absente */
const BOX_DIMS = { full: { w: 104, roof: 24, rows: 5 }, min: { w: 92, roof: 12, rows: 2 } };
const TICK_DENSE_PX = 7;       /* pixels par minute à partir desquels on trace un trait par minute */
const TICK_NUM_GAP = 24;       /* écart minimal entre deux chiffres, en pixels */
const TICK_NUM_OFF = 20;       /* chiffre à 20 px à gauche du tracé */
const TICK_END_MIN = 0.05;     /* pas de trait à moins de 3 s du point d'arrivée (minutes) */
const TICK_CULL_ABOVE = 300;   /* au-delà de ce nombre de traits sur une branche, seuls ceux de l'écran sont dessinés */
const KEY_LAYERS = 'route_layers_v1';
const LAYERS_FORMAT = 'dcs-layers-v1';
const LAYERS_Z = 390;          /* le pane des calques : au-dessus du fond, de la grille et des aérodromes, sous la route, les références et les boîtes */
const CF_NAMES_ZOOM = 11;      /* le nom d'un point de calque : à partir du zoom 11 */
const CF_FILL_K = 0.4;         /* remplissages atténués à 40 % de l'opacité du fichier */
const NM_M = 1852;
const CF_ITEM_TYPES = ['zone', 'circle', 'orbit', 'box', 'point', 'text'];
const CF_ZONE_KINDS = ['lines', 'curve', 'flot', 'corridor'];
const CF_POINT_KINDS = ['target', 'dmpi', 'exit', 'lz', 'other'];
const CF_DASHES = ['solid', 'dot', 'dash'];
const CF_COUNT_ORDER = ['zone', 'circle', 'point', 'orbit', 'box', 'text'];

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

/* Villes DCS par théâtre : [ nom, lat, lon ] — les noms tels qu'ils sont écrits dans les cartes de DCS */
const TOWNS = __TOWNS__;

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
    'tb.towns': 'Villes',
    'tb.towns.tip': 'Villes DCS (à partir du zoom 10)',
    'tb.towns.off': 'Villes — absentes de ce théâtre',
    'sr.title': 'Rechercher sur la carte',
    'sr.ph': 'Ville, aérodrome, point…',
    'sr.close': 'Fermer',
    'sr.none': 'Aucun résultat',
    'sr.k.wp': 'Point {n}',
    'sr.k.ref': 'Réf. {n}',
    'sr.k.af': 'Aérodrome',
    'sr.k.hp': 'Hélistation',
    'sr.k.town': 'Ville',
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
    'th.spd.kmh': 'Vit. km/h',
    'th.spd.kt': 'Vit. kt',
    'spd.none': '—',
    'u.kmh': 'km/h',
    'u.kt': 'kt',
    'f.lbx': 'Boîtes de branche',
    'lbx.none': 'Aucune',
    'lbx.min': 'Minimale',
    'lbx.full': 'Complète',
    'f.gs': 'Vitesse sol ({u})',
    'f.trace': 'Tracé',
    'f.ticks': 'Traits des minutes',
    'col.route': 'Couleur',
    'col.black': 'Noir',
    'lb.true': '°V',
    'lb.mag': '°M',
    'lb.ete': 'ETE',
    'lb.tip': 'Glissez la boîte pour la déplacer',
    'tick.fmt': '{k}\u2032',
    'nav.leg': '↓ {cap}° · {spd} · ETE {ete}',
    'nav.t': 'T {t}',
    'nav.total.v': '{d} · {t}',
    'ref.AGL': 'SOL',
    'ref.MSL': 'MER',
    'refl.AGL': 'sol',
    'refl.MSL': 'mer',
    'help.route': 'Touchez la carte pour ajouter un point\u202f; glissez un point pour le déplacer\u202f; le « + » d\'une branche insère un point.',
    'tip.insert': 'Insérer un point',
    'tip.delete': 'Supprimer',
    'tap.wp': 'Point',
    'tap.ref': 'Réf.',
    'tap.read': 'Lire',
    'tap.title': 'Ce que fait un toucher sur la carte',
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
    'nav.title.calc': 'NAVIGATION — CAP MAGNÉTIQUE · VAR {a} ({min} à {max}°)',
    'nav.title.calc1': 'NAVIGATION — CAP MAGNÉTIQUE · VAR {a} ({v}°)',
    'nav.title.calc0': 'NAVIGATION — CAP MAGNÉTIQUE · VAR {a}',
    'nav.var': 'VAR {v}°',
    'f.dv': 'Déclinaison',
    'f.dvy': 'Année',
    'dv.calc': 'Calculée',
    'dv.manual': 'Saisie',
    'dv.force': 'Forcer',
    'dv.tag.mission': 'MISSION',
    'dv.tag.forced': 'FORCÉE',
    'dv.tag.typed': 'SAISIE',
    'dv.tag.default': 'PAR DÉFAUT',
    'dv.src.mission': '{file} · {date}',
    'dv.src.forced': 'la mission chargée ({file}) est ignorée',
    'dv.src.typed': 'année tapée, aucune mission de ce théâtre',
    'dv.src.default': '1985, aucune mission de ce théâtre ni année saisie',
    'dv.src.model': 'Modèle de DCS (WMM {e}) · par branche, au point de départ',
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
    'confirm.clear': 'Effacer la route ?',
    'err.cf': 'Fichier CombatFlite non reconnu.',
    'err.cfBrowser': 'Ce navigateur ne sait pas lire les fichiers CombatFlite.',
    'err.layersQuota': 'Calques trop lourds pour le navigateur : ils ne seront pas gardés après rechargement.',
    'cf.import.title': 'Calques CombatFlite',
    'cf.file': 'Fichier : {name} · théâtre {t}',
    'cf.import.note': 'Cochez les calques à afficher. Ils restent en lecture seule.',
    'cf.import.go': 'Afficher',
    'cf.n.zone.1': '{n} zone',
    'cf.n.zone.n': '{n} zones',
    'cf.n.circle.1': '{n} cercle',
    'cf.n.circle.n': '{n} cercles',
    'cf.n.point.1': '{n} point',
    'cf.n.point.n': '{n} points',
    'cf.n.orbit.1': '{n} orbite',
    'cf.n.orbit.n': '{n} orbites',
    'cf.n.box.1': '{n} boîte',
    'cf.n.box.n': '{n} boîtes',
    'cf.n.text.1': '{n} texte',
    'cf.n.text.n': '{n} textes',
    'cf.empty': 'vide',
    'toast.cfShown.1': '{n} calque affiché ✓',
    'toast.cfShown.n': '{n} calques affichés ✓',
    'toast.cfTheatre': 'théâtre inconnu ({t}), gardé : {theatre}',
    'sec.layers': 'Calques',
    'layers.count.1': '{n} calque',
    'layers.count.n': '{n} calques',
    'layers.remove': 'Retirer ce calque',
    'layers.removeAll': 'Retirer tous les calques',
    'layers.help': 'En mode Lire, touchez un objet pour lire sa fiche. En mode Point ou Réf., une cible touchée devient un point de la route ou une référence. En mode Dessin, vous créez et modifiez vos propres calques.',
    'confirm.layer': 'Retirer le calque « {name} » ?',
    'confirm.layers': 'Retirer tous les calques ?',
    'cf.k.lines': 'Zone',
    'cf.k.curve': 'Courbe',
    'cf.k.flot': 'FLOT',
    'cf.k.corridor': 'Couloir',
    'cf.nm': '{w} NM',
    'cf.p.target': 'Cible',
    'cf.p.dmpi': 'DMPI',
    'cf.p.exit': 'Point de sortie',
    'cf.p.lz': 'LZ',
    'cf.p.other': 'Point',
    'cf.mhz': '{f} MHz',
    'cf.toRef': '→ Point de référence',
    'cf.exp.title': 'Exporter',
    'cf.exp.route': 'La route',
    'cf.exp.routeN': '{n} points · {m} réf.',
    'cf.exp.go': 'Exporter',
    'toast.layersAdded.1': '{n} calque ajouté ✓ (fichier sans route : la route n\'est pas touchée)',
    'toast.layersAdded.n': '{n} calques ajoutés ✓ (fichier sans route : la route n\'est pas touchée)',
    'tap.draw': 'Dessin',
    'dr.tool.select': 'Choisir',
    'dr.tool.circle': 'Cercle',
    'dr.tool.zone': 'Zone',
    'dr.tool.line': 'Ligne',
    'dr.tool.point': 'Point',
    'dr.tool.text': 'Texte',
    'dr.g.circle': 'Cercle',
    'dr.g.zone': 'Zone',
    'dr.g.line': 'Ligne',
    'dr.g.point': 'Point',
    'dr.g.text': 'Texte',
    'dr.g.orbit': 'Orbite',
    'dr.g.box': 'Boîte',
    'dr.chip': 'Calque',
    'dr.chip.new': 'Nouveau calque',
    'dr.msg.select': 'Touchez un objet du calque pour le modifier.',
    'dr.msg.circle': 'Touchez la carte\u202f: le centre. Le rayon s\'ajuste ensuite à la poignée.',
    'dr.msg.zone': 'Touchez la carte pour poser les sommets.',
    'dr.msg.point': 'Touchez la carte pour poser le point.',
    'dr.msg.text': 'Touchez la carte pour poser le texte.',
    'dr.nv.1': '{n} sommet',
    'dr.nv.n': '{n} sommets',
    'dr.build.add': '— touchez pour en ajouter',
    'dr.build.close': '— touchez le premier pour fermer',
    'dr.finish': 'Terminer',
    'dr.undo': 'Retirer le dernier sommet',
    'dr.cancel': 'Abandonner',
    'dr.b.vtx': 'Sommet',
    'dr.b.props': 'Réglages',
    'dr.b.copy': 'Copier',
    'dr.b.del': 'Suppr.',
    'dr.b.ok': 'OK',
    'dr.vtx.n': 'sommet {n}',
    'dr.sheet': '{g} · réglages',
    'dr.f.name': 'Nom',
    'dr.f.unnamed': 'sans nom',
    'dr.f.text': 'Texte',
    'dr.f.color': 'Couleur',
    'dr.f.radius': 'Rayon (NM)',
    'dr.f.alt': 'Alt. max',
    'dr.f.alt.ph': 'FL120',
    'dr.f.line': 'Trait',
    'dr.dash.solid': 'Plein',
    'dr.dash.dash': 'Tirets',
    'dr.dash.dot': 'Pointillés',
    'dr.f.fill': 'Intérieur',
    'dr.f.none': 'Vide',
    'dr.f.filled': 'Plein',
    'dr.f.type': 'Type',
    'dr.f.frame': 'Cadre',
    'dr.f.noBg': 'Sans fond',
    'dr.f.whiteBg': 'Fond blanc',
    'dr.f.close': 'Fermer',
    'dr.p.lz': 'Zone de poser',
    'dr.p.other': 'Autre',
    'dr.new.text': 'TEXTE',
    'dr.new.pt': 'PT {n}',
    'dr.new.layer': 'Tracés',
    'dr.new.layerN': 'Tracés {n}',
    'dr.menu.title': 'Dessiner dans',
    'dr.menu.name': 'Nom du calque',
    'dr.menu.add': '+ Calque',
    'dr.menu.copy': 'Copier pour dessiner',
    'dr.menu.copyName': '{name} (copie)',
    'dr.menu.ro': 'Calque CombatFlite\u202f: lecture seule',
    'dr.cf': 'CF',
    'dr.t.created': 'Calque « {name} » créé',
    'dr.t.zone': 'Une zone a au moins trois sommets.',
    'dr.t.line': 'Une ligne a au moins deux sommets.',
    'dr.t.min': 'Il faut au moins {n} sommets.',
    'dr.confirmDel': 'Supprimer « {name} »\u202f?',
    'dr.tool.orbit': 'Orbite',
    'dr.tool.box': 'Boîte',
    'dr.msg.orbit': 'Touchez l\'entrée de l\'orbite, puis sa sortie.',
    'dr.msg.orbit2': 'Touchez la sortie de l\'orbite.',
    'dr.msg.box': 'Touchez le début de l\'axe de la boîte, puis sa fin.',
    'dr.msg.box2': 'Touchez la fin de l\'axe.',
    'dr.lab.box': '{l} × {w} NM',
    'dr.sheet.draft': '{g} · réglages · à venir',
    'dr.f.width': 'Largeur (NM)',
    'dr.f.length': 'Longueur (NM)',
    'dr.f.turn': 'Virage',
    'dr.turn.r': 'À droite',
    'dr.turn.l': 'À gauche',
    'dr.f.mission': 'Mission',
    'dr.f.mission.ph': 'AAR, CAP, AWACS…',
    'dr.f.frq': 'Fréquence',
    'dr.f.frq.ph': '251.000',
    'dr.f.minAlt': 'Alt. min',
    'dr.f.minAlt.ph': 'FL150',
    'dr.f.maxAlt.ph': 'FL250',
    'dr.f.gridH': 'Grille · lignes',
    'dr.f.gridV': 'Grille · colonnes',
    'dr.f.grid': 'Grille',
    'dr.grid.show': 'Afficher',
    'dr.grid.hide': 'Masquer',
    'dr.f.shape': 'Tracé',
    'dr.shape.lines': 'Droit',
    'dr.shape.curve': 'Courbe',
    'dr.lt.line': 'Ligne',
    'dr.lt.flot': 'FLOT',
    'dr.lt.corridor': 'Couloir',
    'dr.f.enemy': 'Côté ennemi',
    'dr.f.flip': 'Inverser',
    'dr.d.corr': 'Couloir {w} NM',
    'dr.step.dec': 'Moins',
    'dr.step.inc': 'Plus',
    'sp.title': 'Glissez pour agrandir ou réduire la carte\u202f; touchez deux fois pour revenir à la taille d\'origine'
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
    'tb.towns': 'Towns',
    'tb.towns.tip': 'DCS towns (from zoom 10)',
    'tb.towns.off': 'Towns — not available for this theatre',
    'sr.title': 'Search the map',
    'sr.ph': 'Town, airfield, waypoint…',
    'sr.close': 'Close',
    'sr.none': 'No results',
    'sr.k.wp': 'Waypoint {n}',
    'sr.k.ref': 'Ref. {n}',
    'sr.k.af': 'Airfield',
    'sr.k.hp': 'Helipad',
    'sr.k.town': 'Town',
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
    'th.spd.kmh': 'Spd km/h',
    'th.spd.kt': 'Spd kt',
    'spd.none': '—',
    'u.kmh': 'km/h',
    'u.kt': 'kt',
    'f.lbx': 'Leg boxes',
    'lbx.none': 'None',
    'lbx.min': 'Minimal',
    'lbx.full': 'Full',
    'f.gs': 'Ground speed ({u})',
    'f.trace': 'Route line',
    'f.ticks': 'Minute marks',
    'col.route': 'Colour',
    'col.black': 'Black',
    'lb.true': '°T',
    'lb.mag': '°M',
    'lb.ete': 'ETE',
    'lb.tip': 'Drag the box to move it',
    'tick.fmt': '{k}\u2032',
    'nav.leg': '↓ {cap}° · {spd} · ETE {ete}',
    'nav.t': 'T {t}',
    'nav.total.v': '{d} · {t}',
    'ref.AGL': 'AGL',
    'ref.MSL': 'MSL',
    'refl.AGL': 'AGL',
    'refl.MSL': 'MSL',
    'help.route': 'Tap the map to add a waypoint; drag a waypoint to move it; a leg\'s “+” inserts a waypoint.',
    'tip.insert': 'Insert a waypoint',
    'tip.delete': 'Delete',
    'tap.wp': 'Waypoint',
    'tap.ref': 'Ref.',
    'tap.read': 'Read',
    'tap.title': 'What a tap on the map does',
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
    'nav.title.calc': 'NAVIGATION — MAGNETIC HEADING · VAR {a} ({min} to {max}°)',
    'nav.title.calc1': 'NAVIGATION — MAGNETIC HEADING · VAR {a} ({v}°)',
    'nav.title.calc0': 'NAVIGATION — MAGNETIC HEADING · VAR {a}',
    'nav.var': 'VAR {v}°',
    'f.dv': 'Variation',
    'f.dvy': 'Year',
    'dv.calc': 'Computed',
    'dv.manual': 'Entered',
    'dv.force': 'Override',
    'dv.tag.mission': 'MISSION',
    'dv.tag.forced': 'OVERRIDDEN',
    'dv.tag.typed': 'ENTERED',
    'dv.tag.default': 'DEFAULT',
    'dv.src.mission': '{file} · {date}',
    'dv.src.forced': 'the loaded mission ({file}) is ignored',
    'dv.src.typed': 'typed year, no mission for this theatre',
    'dv.src.default': '1985, no mission for this theatre nor typed year',
    'dv.src.model': 'DCS model (WMM {e}) · per leg, at its start point',
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
    'confirm.clear': 'Clear the route?',
    'err.cf': 'Unrecognised CombatFlite file.',
    'err.cfBrowser': 'This browser cannot read CombatFlite files.',
    'err.layersQuota': 'Layers too large for the browser: they will not be kept after reload.',
    'cf.import.title': 'CombatFlite layers',
    'cf.file': 'File: {name} · theatre {t}',
    'cf.import.note': 'Tick the layers to show. They are read-only.',
    'cf.import.go': 'Show',
    'cf.n.zone.1': '{n} zone',
    'cf.n.zone.n': '{n} zones',
    'cf.n.circle.1': '{n} ring',
    'cf.n.circle.n': '{n} rings',
    'cf.n.point.1': '{n} point',
    'cf.n.point.n': '{n} points',
    'cf.n.orbit.1': '{n} orbit',
    'cf.n.orbit.n': '{n} orbits',
    'cf.n.box.1': '{n} box',
    'cf.n.box.n': '{n} boxes',
    'cf.n.text.1': '{n} text',
    'cf.n.text.n': '{n} texts',
    'cf.empty': 'empty',
    'toast.cfShown.1': '{n} layer shown ✓',
    'toast.cfShown.n': '{n} layers shown ✓',
    'toast.cfTheatre': 'unknown theatre ({t}), kept: {theatre}',
    'sec.layers': 'Layers',
    'layers.count.1': '{n} layer',
    'layers.count.n': '{n} layers',
    'layers.remove': 'Remove this layer',
    'layers.removeAll': 'Remove all layers',
    'layers.help': 'In Read mode, tap an item to read it. In Waypoint or Ref. mode, a tapped target becomes a waypoint or a reference point. In Draw mode, you create and edit your own layers.',
    'confirm.layer': 'Remove layer “{name}”?',
    'confirm.layers': 'Remove all layers?',
    'cf.k.lines': 'Zone',
    'cf.k.curve': 'Curve',
    'cf.k.flot': 'FLOT',
    'cf.k.corridor': 'Corridor',
    'cf.nm': '{w} NM',
    'cf.p.target': 'Target',
    'cf.p.dmpi': 'DMPI',
    'cf.p.exit': 'Exit point',
    'cf.p.lz': 'LZ',
    'cf.p.other': 'Point',
    'cf.mhz': '{f} MHz',
    'cf.toRef': '→ Reference point',
    'cf.exp.title': 'Export',
    'cf.exp.route': 'The route',
    'cf.exp.routeN': '{n} waypoints · {m} ref.',
    'cf.exp.go': 'Export',
    'toast.layersAdded.1': '{n} layer added ✓ (no route in the file: the route is unchanged)',
    'toast.layersAdded.n': '{n} layers added ✓ (no route in the file: the route is unchanged)',
    'tap.draw': 'Draw',
    'dr.tool.select': 'Select',
    'dr.tool.circle': 'Circle',
    'dr.tool.zone': 'Zone',
    'dr.tool.line': 'Line',
    'dr.tool.point': 'Point',
    'dr.tool.text': 'Text',
    'dr.g.circle': 'Circle',
    'dr.g.zone': 'Zone',
    'dr.g.line': 'Line',
    'dr.g.point': 'Point',
    'dr.g.text': 'Text',
    'dr.g.orbit': 'Orbit',
    'dr.g.box': 'Box',
    'dr.chip': 'Layer',
    'dr.chip.new': 'New layer',
    'dr.msg.select': 'Tap an object in the layer to edit it.',
    'dr.msg.circle': 'Tap the map: the centre. Then set the radius with the handle.',
    'dr.msg.zone': 'Tap the map to place the vertices.',
    'dr.msg.point': 'Tap the map to place the point.',
    'dr.msg.text': 'Tap the map to place the text.',
    'dr.nv.1': '{n} vertex',
    'dr.nv.n': '{n} vertices',
    'dr.build.add': '— tap to add more',
    'dr.build.close': '— tap the first one to close',
    'dr.finish': 'Finish',
    'dr.undo': 'Remove the last vertex',
    'dr.cancel': 'Cancel',
    'dr.b.vtx': 'Vertex',
    'dr.b.props': 'Settings',
    'dr.b.copy': 'Copy',
    'dr.b.del': 'Delete',
    'dr.b.ok': 'OK',
    'dr.vtx.n': 'vertex {n}',
    'dr.sheet': '{g} · settings',
    'dr.f.name': 'Name',
    'dr.f.unnamed': 'unnamed',
    'dr.f.text': 'Text',
    'dr.f.color': 'Colour',
    'dr.f.radius': 'Radius (NM)',
    'dr.f.alt': 'Max alt.',
    'dr.f.alt.ph': 'FL120',
    'dr.f.line': 'Line',
    'dr.dash.solid': 'Solid',
    'dr.dash.dash': 'Dashed',
    'dr.dash.dot': 'Dotted',
    'dr.f.fill': 'Fill',
    'dr.f.none': 'None',
    'dr.f.filled': 'Filled',
    'dr.f.type': 'Type',
    'dr.f.frame': 'Frame',
    'dr.f.noBg': 'No background',
    'dr.f.whiteBg': 'White background',
    'dr.f.close': 'Close',
    'dr.p.lz': 'LZ',
    'dr.p.other': 'Point',
    'dr.new.text': 'TEXT',
    'dr.new.pt': 'PT {n}',
    'dr.new.layer': 'Drawings',
    'dr.new.layerN': 'Drawings {n}',
    'dr.menu.title': 'Draw in',
    'dr.menu.name': 'Layer name',
    'dr.menu.add': '+ Layer',
    'dr.menu.copy': 'Copy to draw',
    'dr.menu.copyName': '{name} (copy)',
    'dr.menu.ro': 'CombatFlite layer: read-only',
    'dr.cf': 'CF',
    'dr.t.created': 'Layer “{name}” created',
    'dr.t.zone': 'A zone needs at least three vertices.',
    'dr.t.line': 'A line needs at least two vertices.',
    'dr.t.min': 'At least {n} vertices are needed.',
    'dr.confirmDel': 'Delete “{name}”?',
    'dr.tool.orbit': 'Orbit',
    'dr.tool.box': 'Box',
    'dr.msg.orbit': 'Tap the orbit\'s entry point, then its exit.',
    'dr.msg.orbit2': 'Tap the orbit\'s exit point.',
    'dr.msg.box': 'Tap the start of the box axis, then its end.',
    'dr.msg.box2': 'Tap the end of the axis.',
    'dr.lab.box': '{l} × {w} NM',
    'dr.sheet.draft': '{g} · settings · upcoming',
    'dr.f.width': 'Width (NM)',
    'dr.f.length': 'Length (NM)',
    'dr.f.turn': 'Turn',
    'dr.turn.r': 'Right',
    'dr.turn.l': 'Left',
    'dr.f.mission': 'Mission',
    'dr.f.mission.ph': 'AAR, CAP, AWACS…',
    'dr.f.frq': 'Frequency',
    'dr.f.frq.ph': '251.000',
    'dr.f.minAlt': 'Min alt.',
    'dr.f.minAlt.ph': 'FL150',
    'dr.f.maxAlt.ph': 'FL250',
    'dr.f.gridH': 'Grid · rows',
    'dr.f.gridV': 'Grid · columns',
    'dr.f.grid': 'Grid',
    'dr.grid.show': 'Show',
    'dr.grid.hide': 'Hide',
    'dr.f.shape': 'Shape',
    'dr.shape.lines': 'Straight',
    'dr.shape.curve': 'Curve',
    'dr.lt.line': 'Line',
    'dr.lt.flot': 'FLOT',
    'dr.lt.corridor': 'Corridor',
    'dr.f.enemy': 'Enemy side',
    'dr.f.flip': 'Flip',
    'dr.d.corr': 'Corridor {w} NM',
    'dr.step.dec': 'Less',
    'dr.step.inc': 'More',
    'sp.title': 'Drag to resize the map; double-tap to restore its size'
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

@@MAGVAR_BLOCK@@
/* ============= MODÈLE ============= */
function defaultState() {
  return {
    format: FORMAT_ID, name: '', theatre: 'Caucasus',
    units: { distance: 'km', altitude: 'm' },
    navDisplay: { ref: 'true', decl: '', mode: 'calc', year: '', force: false },
    groundSpeed: GS_DEFAULT, legBoxes: 'full',
    points: [],
    refs: [],
    ui: { layer: 'topo', grid: true, places: false, towns: true, airfields: true, trace: 'route', ticks: 'route' }
  };
}

let S = defaultState();
let sel = -1;                 /* point sélectionné (non enregistré) */
let selR = -1;                /* point de référence sélectionné (non enregistré) */
let tapMode = 'wp';           /* ce que fait un toucher sur la carte : 'wp' (pose un point), 'ref' (pose une référence), 'read' (ouvre les fiches des calques, ne pose rien) ou 'draw' (dessine dans un calque) — non enregistré */
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

/* La place d'une boîte lue : { along, side } en entiers, sinon null (la place par défaut s'applique) */
function readBox(b) {
  if (!b || typeof b !== 'object' || Array.isArray(b)) return null;
  if (!Number.isInteger(b.along) || !Number.isInteger(b.side)) return null;
  if (Math.abs(b.along) > BOX_LIMIT || Math.abs(b.side) > BOX_LIMIT) return null;
  return { along: b.along, side: b.side };
}

/* Les réglages de cap lus : le mode de déclinaison est gardé s'il est connu ; sinon « Saisie » quand une valeur saisie se lit
   (une route d'avant ce mode ne change pas), « Calculée » sinon. L'année : les chiffres tapés (quatre au plus) ; Forcer : true seulement si true. */
function readNavDisplay(nd) {
  const decl = str(nd.decl);
  return {
    ref: nd.ref === 'mag' ? 'mag' : 'true',
    decl: decl,
    mode: (nd.mode === 'calc' || nd.mode === 'manual') ? nd.mode : (parseDecl(decl) != null ? 'manual' : 'calc'),
    year: (typeof nd.year === 'string' && /^\d{1,4}$/.test(nd.year)) ? nd.year : '',
    force: nd.force === true
  };
}

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
    navDisplay: readNavDisplay(nd),
    groundSpeed: (typeof src.groundSpeed === 'number' && isFinite(src.groundSpeed) && src.groundSpeed > 0) ? src.groundSpeed : GS_DEFAULT,
    legBoxes: LEGBOX_IDS.indexOf(src.legBoxes) !== -1 ? src.legBoxes : 'full',
    points: [],
    refs: []
  };
  let dropped = 0, droppedRefs = 0;
  src.points.forEach(p => {
    if (!p || typeof p !== 'object' || !validCoord(p.lat, p.lon)) return;
    if (route.points.length >= MAX_POINTS) { dropped++; return; }
    const q = {
      name: typeof p.name === 'string' ? p.name : nextName(route.points, route.points.length),
      lat: r7(p.lat), lon: r7(p.lon),
      alt: (typeof p.alt === 'number' && isFinite(p.alt)) ? p.alt : 0,
      altRef: p.altRef === 'MSL' ? 'MSL' : 'AGL'
    };
    /* gs : la vitesse de la branche qui arrive au point, jamais sur le point 0 ; box : la place de sa boîte */
    if (route.points.length > 0 && typeof p.gs === 'number' && isFinite(p.gs) && p.gs > 0) q.gs = p.gs;
    if (route.points.length > 0) { const bx = readBox(p.box); if (bx) q.box = bx; }
    route.points.push(q);
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
          places: typeof ui.places === 'boolean' ? ui.places : false, towns: typeof ui.towns === 'boolean' ? ui.towns : true,
          airfields: typeof ui.airfields === 'boolean' ? ui.airfields : true,
          trace: ui.trace === 'black' ? 'black' : 'route', ticks: ui.ticks === 'black' ? 'black' : 'route' } });
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
    navDisplay: { ref: S.navDisplay.ref, decl: S.navDisplay.decl, mode: S.navDisplay.mode, year: S.navDisplay.year, force: S.navDisplay.force },
    groundSpeed: S.groundSpeed, legBoxes: S.legBoxes,
    points: S.points.map((p, i) => {
      const o = { name: p.name, lat: p.lat, lon: p.lon, alt: p.alt, altRef: p.altRef };
      if (i > 0 && typeof p.gs === 'number') o.gs = p.gs;
      if (i > 0 && p.box) o.box = { along: p.box.along, side: p.box.side };
      return o;
    }),
    refs: S.refs.map(p => ({ name: p.name, lat: p.lat, lon: p.lon, alt: p.alt, altRef: p.altRef }))
  };
}

function theatreOf(id) { return THEATRES.find(x => x.id === id) || THEATRES[0]; }
function dcsKey() { return theatreOf(S.theatre).dcs; }

/* « Carte DCS » choisie sur un théâtre qui n'en a pas : la couche passe en Topographique */
function resolveLayer() {
  if (S.ui.layer === 'dcs' && !dcsKey()) S.ui.layer = 'topo';
}

/* Le théâtre change (la route est gardée) : la liste de la barre, ou un fichier CombatFlite qui nomme le sien */
function setTheatre(id) {
  const wasDcs = S.ui.layer === 'dcs';
  S.theatre = theatreOf(id).id;
  persistState();
  setTheatreView();
  if (wasDcs) setBase();        /* la couche DCS change avec le théâtre (ou passe en Topographique) */
  syncAirfields();
  syncControls();
}

/* ============= UNITÉS, DISTANCES, CAPS ============= */
/* La déclinaison : calculée (le modèle de DCS, à l'année de la route) ou saisie ; seul le cap magnétique en a besoin */
function navIsMag() { return S.navDisplay.ref === 'mag' && (S.navDisplay.mode === 'calc' || parseDecl(S.navDisplay.decl) != null); }
function navIsCalc() { return S.navDisplay.ref === 'mag' && S.navDisplay.mode === 'calc'; }
/* L'année de la route et sa source : la mission de HQ (même théâtre), la saisie, ou 1985 */
function navYear() { return magYearSource(S.theatre, S.navDisplay.year, S.navDisplay.force); }
/* La déclinaison (°, + vers l'Est) au point p, ou null en cap vrai ; ys : l'année déjà lue, sinon elle se lit ici */
function declAt(p, ys) {
  if (S.navDisplay.ref !== 'mag') return null;
  if (S.navDisplay.mode === 'calc') return magVar(p.lat, p.lon, (ys || navYear()).y);
  return parseDecl(S.navDisplay.decl);
}
/* Une déclinaison au dixième : signe − (U+2212) ou +, virgule en FR, aucun signe pour 0,0 */
function fmtVar(v) {
  const r = Math.round(v * 10) / 10;
  if (r === 0) return decimal('0.0');
  return (r < 0 ? '\u2212' : '+') + decimal(Math.abs(r).toFixed(1));
}

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

/* Cap (vrai, ou magnétique = vrai − déclinaison du point de départ) et distance d'une branche */
function legInfo(a, b, ys) {
  const L = legCalc(a, b);
  const d = declAt(a, ys);
  const brg = d == null ? L.brg : (((L.brg - d) % 360) + 360) % 360;
  return { cap: fmtHdg(brg), km: L.km };
}

/* ============= VITESSE SOL ET TEMPS ============= */
function r4(v) { return Math.round(v * 1e4) / 1e4; }

/* À la seconde la plus proche (0,5 s vers le haut) */
function secRound(s) { return Math.floor(s + 0.5); }
/* Temps de branche : MM:SS (minutes sur deux chiffres au moins) */
function fmtEte(s) { const n = secRound(s); return pad2(Math.floor(n / 60)) + ':' + pad2(n % 60); }
/* Temps écoulé : HH+MM+SS */
function fmtElapsed(s) { const n = secRound(s); return pad2(Math.floor(n / 3600)) + '+' + pad2(Math.floor(n / 60) % 60) + '+' + pad2(n % 60); }

/* Vitesse (km/h) de la branche qui arrive au point i : la sienne, sinon celle de la route ; le point 0 n'en a pas */
function legSpeed(i) {
  const p = S.points[i];
  return (i > 0 && p && typeof p.gs === 'number' && p.gs > 0) ? p.gs : S.groundSpeed;
}
/* km/h → entier dans l'unité affichée (km/h, ou kt quand la distance est en NM) */
function speedDisp(kmh) { return Math.round(S.units.distance === 'nm' ? kmh / NM_KM : kmh); }
function speedText(kmh) { return speedDisp(kmh) + ' ' + t(S.units.distance === 'nm' ? 'u.kt' : 'u.kmh'); }
/* Une saisie de vitesse (unité affichée) → km/h ; null si elle est hors règle (entier de 1 à 2 000) */
function readSpeed(s) {
  const v = readNum(s);
  if (v == null) return null;
  const n = Math.round(v);
  if (n < 1 || n > GS_MAX_IN) return null;
  return S.units.distance === 'nm' ? r4(n * NM_KM) : n;
}

/* Le minutage de la route : par branche (cap, distance, vitesse, durée non arrondie en secondes) et temps écoulé à chaque point
   (somme non arrondie des durées qui précèdent) */
function timing() {
  const pts = S.points, legs = [null], el = [0];
  const ys = navIsCalc() ? navYear() : null;
  let km = 0, sec = 0;
  for (let i = 1; i < pts.length; i++) {
    const l = legInfo(pts[i - 1], pts[i], ys);
    const v = legSpeed(i);
    const sc = l.km / v * 3600;
    legs.push({ cap: l.cap, km: l.km, v: v, sec: sc });
    km += l.km; sec += sc;
    el.push(sec);
  }
  return { legs: legs, el: el, km: km, sec: sec };
}

/* ============= CALQUES COMBATFLITE : MODÈLE dcs-layers-v1, LECTURE DU .cf, STOCKAGE ============= */
/* Les calques vivent à part de la route : sous route_layers_v1, jamais dans route_state_v1. Un calque :
   { id, name, visible, source: { kind: 'combatflite' | 'drawn', file }, items: [ … ] } ; six types d'objets (longueurs en NM, angles en degrés
   vrais, opacités de 0 à 1) — le dessin du lot suivant édite ce même modèle. */
let CF_LAYERS = [];

function cfRandId() {
  try { if (window.crypto && typeof window.crypto.randomUUID === 'function') return window.crypto.randomUUID(); } catch (e) { /* repli ci-dessous */ }
  return 'cf-' + Math.random().toString(36).slice(2, 12) + Date.now().toString(36);
}

function cfNum(v) { return (typeof v === 'number' && isFinite(v)) ? v : null; }
function cfLat(v) { const n = cfNum(v); return (n != null && Math.abs(n) <= 90) ? n : null; }
function cfLon(v) { const n = cfNum(v); return (n != null && Math.abs(n) <= 180) ? n : null; }
function cfColor(v, d) { return (typeof v === 'string' && /^#[0-9a-fA-F]{6}$/.test(v)) ? v.toLowerCase() : d; }
function cfOpa(v, d) { const n = cfNum(v); return n == null ? d : Math.max(0, Math.min(1, n)); }
function cfPos(v, d, max) { const n = cfNum(v); return (n != null && n > 0) ? Math.min(n, max) : d; }
function cfInt(v, d, max) { const n = cfNum(v); return n == null ? d : Math.max(1, Math.min(max, Math.round(n))); }
function cfPick(v, list, d) { return list.indexOf(v) !== -1 ? v : d; }

/* Un objet lu (fichier JSON, stockage, ou objet brut du .cf) → l'objet du modèle, dans l'ordre des champs du cadrage ; null s'il est
   illisible : type inconnu, une coordonnée qui n'est pas un nombre dans les bornes, une zone de moins de 2 points, une taille absente */
function cfItem(src) {
  if (!src || typeof src !== 'object' || Array.isArray(src) || CF_ITEM_TYPES.indexOf(src.type) === -1) return null;
  const type = src.type;
  const id = (typeof src.id === 'string' && src.id !== '') ? src.id : cfRandId();
  const name = str(src.name);
  if (type === 'zone') {
    if (!Array.isArray(src.points)) return null;
    const pts = [];
    for (let i = 0; i < src.points.length; i++) {
      const p = src.points[i];
      if (!Array.isArray(p)) return null;
      const la = cfLat(p[0]), lo = cfLon(p[1]);
      if (la == null || lo == null) return null;
      pts.push([la, lo]);
    }
    if (pts.length < 2) return null;
    return { id: id, type: type, name: name, kind: cfPick(src.kind, CF_ZONE_KINDS, 'lines'), points: pts, closed: src.closed === true, filled: src.filled === true,
      widthNm: cfPos(src.widthNm, 5, 1000), color: cfColor(src.color, '#000000'), lineOpacity: cfOpa(src.lineOpacity, 1), fillOpacity: cfOpa(src.fillOpacity, 0.5),
      lineWidth: cfPos(src.lineWidth, 2, 30), dash: cfPick(src.dash, CF_DASHES, 'solid') };
  }
  const lat = cfLat(src.lat), lon = cfLon(src.lon);
  if (lat == null || lon == null) return null;
  if (type === 'circle') {
    const r = cfPos(src.radiusNm, 0, 100000);
    if (!(r > 0)) return null;
    return { id: id, type: type, name: name, lat: lat, lon: lon, radiusNm: r, filled: src.filled === true, color: cfColor(src.color, '#000000'),
      lineOpacity: cfOpa(src.lineOpacity, 1), fillOpacity: cfOpa(src.fillOpacity, 0.5), lineWidth: cfPos(src.lineWidth, 2, 30), dash: cfPick(src.dash, CF_DASHES, 'solid'),
      maxAlt: str(src.maxAlt), showName: src.showName === true };
  }
  if (type === 'orbit') {
    const lat2 = cfLat(src.lat2), lon2 = cfLon(src.lon2);
    if (lat2 == null || lon2 == null) return null;
    let brg = cfNum(src.brg);
    if (brg == null) brg = legCalc({ lat: lat2, lon: lon2 }, { lat: lat, lon: lon }).brg;
    return { id: id, type: type, name: name, lat: lat, lon: lon, lat2: lat2, lon2: lon2, brg: brg, widthNm: cfPos(src.widthNm, 10, 1000), clockwise: src.clockwise === true,
      kind: str(src.kind), minAlt: str(src.minAlt), maxAlt: str(src.maxAlt), frq: str(src.frq), color: cfColor(src.color, '#000000') };
  }
  if (type === 'box') {
    const brg = cfNum(src.brg), len = cfPos(src.lengthNm, 0, 100000), wid = cfPos(src.widthNm, 0, 100000);
    if (brg == null || !(len > 0) || !(wid > 0)) return null;
    return { id: id, type: type, name: name, lat: lat, lon: lon, brg: brg, lengthNm: len, widthNm: wid, gridH: cfInt(src.gridH, 1, 100), gridV: cfInt(src.gridV, 1, 100),
      showGrid: src.showGrid === true, kind: str(src.kind), minAlt: str(src.minAlt), maxAlt: str(src.maxAlt), color: cfColor(src.color, '#000000'),
      lineWidth: cfPos(src.lineWidth, 2, 30), filled: src.filled === true, fillOpacity: cfOpa(src.fillOpacity, 0.5) };
  }
  if (type === 'point') {
    return { id: id, type: type, name: name, lat: lat, lon: lon, kind: cfPick(src.kind, CF_POINT_KINDS, 'other'), note: str(src.note), color: cfColor(src.color, '#000000') };
  }
  return { id: id, type: type, name: name, lat: lat, lon: lon, text: typeof src.text === 'string' ? src.text : '', bg: cfColor(src.bg, '#ffffff'), fg: cfColor(src.fg, '#000000'),
    size: cfPos(src.size, 40, 400), bold: src.bold === true, border: src.border === true, filled: src.filled === true };
}

/* Un calque lu → le calque du modèle ; null s'il est illisible (pas un objet, pas de tableau d'objets) ; ses objets illisibles sont écartés */
function cfLayer(src) {
  if (!src || typeof src !== 'object' || Array.isArray(src) || !Array.isArray(src.items)) return null;
  const items = [];
  src.items.forEach(it => { const o = cfItem(it); if (o) items.push(o); });
  const so = (src.source && typeof src.source === 'object' && !Array.isArray(src.source)) ? src.source : {};
  return { id: (typeof src.id === 'string' && src.id !== '') ? src.id : cfRandId(), name: str(src.name), visible: src.visible !== false,
    source: so.kind === 'drawn' ? { kind: 'drawn', file: '' } : { kind: 'combatflite', file: str(so.file) }, items: items };
}

/* Des calques s'ajoutent aux calques présents ; un calque de même id remplace le sien, à sa place */
function cfMerge(list) {
  list.forEach(l => {
    const k = CF_LAYERS.findIndex(x => x.id === l.id);
    if (k >= 0) CF_LAYERS[k] = l; else CF_LAYERS.push(l);
  });
}

function persistLayers() {
  try { localStorage.setItem(KEY_LAYERS, JSON.stringify({ format: LAYERS_FORMAT, layers: CF_LAYERS })); return true; }
  catch (e) { showToast(t('err.layersQuota'), 4500); return false; }     /* les calques restent en mémoire */
}

function loadLayers() {
  CF_LAYERS = [];
  try {
    const raw = localStorage.getItem(KEY_LAYERS);
    if (!raw) return;
    const o = JSON.parse(raw);
    if (o && typeof o === 'object' && o.format === LAYERS_FORMAT && Array.isArray(o.layers)) cfMerge(o.layers.map(cfLayer).filter(Boolean));
  } catch (e) { CF_LAYERS = []; }
}

/* ---- Le zip d'un .cf : répertoire central, entrée « mission.xml » (sans casse), méthode 0 (stockée) ou 8 (deflate) ---- */
function zipIsZip(bytes) { return bytes.length >= 2 && bytes[0] === 0x50 && bytes[1] === 0x4B; }

/* → { method, data, size } ; null si le zip est tronqué, chiffré, sans mission.xml */
function zipFindEntry(b) {
  const n = b.length;
  if (n < 22) return null;
  const dv = new DataView(b.buffer, b.byteOffset, b.byteLength);
  let e = -1;
  for (let i = n - 22; i >= 0 && i >= n - 22 - 65535; i--) if (dv.getUint32(i, true) === 0x06054b50) { e = i; break; }
  if (e < 0) return null;
  const count = dv.getUint16(e + 10, true), cdSize = dv.getUint32(e + 12, true), cdOff = dv.getUint32(e + 16, true);
  if (cdOff + cdSize > e) return null;
  let p = cdOff;
  for (let k = 0; k < count; k++) {
    if (p + 46 > n || dv.getUint32(p, true) !== 0x02014b50) return null;
    const flags = dv.getUint16(p + 8, true), method = dv.getUint16(p + 10, true), csz = dv.getUint32(p + 20, true), usz = dv.getUint32(p + 24, true);
    const nl = dv.getUint16(p + 28, true), xl = dv.getUint16(p + 30, true), cl = dv.getUint16(p + 32, true), lho = dv.getUint32(p + 42, true);
    if (p + 46 + nl > n) return null;
    const name = new TextDecoder('utf-8').decode(b.subarray(p + 46, p + 46 + nl));
    if (name.toLowerCase() === 'mission.xml') {
      if ((flags & 1) || lho + 30 > n || dv.getUint32(lho, true) !== 0x04034b50) return null;
      const start = lho + 30 + dv.getUint16(lho + 26, true) + dv.getUint16(lho + 28, true);
      if (start + csz > n || usz > 64 * 1048576) return null;
      return { method: method, data: b.subarray(start, start + csz), size: usz };
    }
    p += 46 + nl + xl + cl;
  }
  return null;
}

async function zipInflate(ent) {
  if (ent.method === 0) return ent.data;
  if (ent.method !== 8) throw new Error('cf');
  const buf = await new Response(new Blob([ent.data]).stream().pipeThrough(new DecompressionStream('deflate-raw'))).arrayBuffer();
  return new Uint8Array(buf);
}

/* ---- Le XML de CombatFlite ---- */
function cfKid(el, name) { for (let c = el.firstElementChild; c; c = c.nextElementSibling) if (c.nodeName === name) return c; return null; }
function cfKids(el, name) { const out = []; for (let c = el.firstElementChild; c; c = c.nextElementSibling) if (c.nodeName === name) out.push(c); return out; }
function cfS(el, name) { const k = cfKid(el, name); return k ? k.textContent.trim() : ''; }
function cfN(el, name) { const s = cfS(el, name); if (s === '') return null; const n = Number(s); return isFinite(n) ? n : null; }
function cfB(el, name) { return cfS(el, name).toLowerCase() === 'true'; }
/* un entier ARGB signé (-16776961) → #rrggbb des 24 bits bas, en minuscules ; l'alpha est ignoré */
function cfArgb(el, name) { const n = cfN(el, name); return n == null ? null : '#' + ((n & 0xFFFFFF) >>> 0).toString(16).padStart(6, '0'); }
/* une opacité de 0 à 255 → 0 à 1 */
function cfOp(el, name) { const n = cfN(el, name); return n == null ? null : n / 255; }
function cfDashOf(s) { const l = s.toLowerCase(); return l === 'dot' ? 'dot' : (l === 'dash' ? 'dash' : 'solid'); }

function cfRawZone(el) {
  const pts = [];
  const pp = cfKid(el, 'Polypoints');
  if (pp) cfKids(pp, 'Polypoint').forEach(q => { pts.push([cfN(q, 'Lat'), cfN(q, 'Lon')]); });
  return { id: cfS(el, 'Tag'), type: 'zone', name: cfS(el, 'Name'), kind: cfS(el, 'Type').toLowerCase(), points: pts, closed: cfB(el, 'Closed'), filled: cfB(el, 'Filled'),
    widthNm: cfN(el, 'CorridorWidth'), color: cfArgb(el, 'Color'), lineOpacity: cfOp(el, 'LineOpacity'), fillOpacity: cfOp(el, 'FillOpacity'),
    lineWidth: cfN(el, 'LineThickness'), dash: cfDashOf(cfS(el, 'LineStyle')) };
}
function cfRawCircle(el) {
  return { id: cfS(el, 'Tag'), type: 'circle', name: cfS(el, 'Name'), lat: cfN(el, 'Lat'), lon: cfN(el, 'Lon'), radiusNm: cfN(el, 'Radius'), filled: cfB(el, 'Filled'),
    color: cfArgb(el, 'Color'), lineOpacity: cfOp(el, 'LineOpacity'), fillOpacity: cfOp(el, 'FillOpacity'), lineWidth: cfN(el, 'LineThickness'), dash: cfDashOf(cfS(el, 'LineStyle')),
    maxAlt: cfS(el, 'MaxAlt'), showName: cfB(el, 'ShowCenterLabel') };
}
function cfRawOrbit(el) {
  return { id: cfS(el, 'Tag'), type: 'orbit', name: cfS(el, 'Name'), lat: cfN(el, 'Lat'), lon: cfN(el, 'Lon'), lat2: cfN(el, 'Lat2'), lon2: cfN(el, 'Lon2'), brg: cfN(el, 'Brg'),
    widthNm: cfN(el, 'Width'), clockwise: cfB(el, 'Clockwise'), kind: cfS(el, 'Type'), minAlt: cfS(el, 'MinAlt'), maxAlt: cfS(el, 'MaxAlt'), frq: cfS(el, 'Frq'), color: cfArgb(el, 'Color') };
}
function cfRawBox(el) {
  return { id: cfS(el, 'Tag'), type: 'box', name: cfS(el, 'Name'), lat: cfN(el, 'Lat'), lon: cfN(el, 'Lon'), brg: cfN(el, 'Brg'), lengthNm: cfN(el, 'Length'), widthNm: cfN(el, 'Width'),
    gridH: cfN(el, 'GRGHorizontalSegments'), gridV: cfN(el, 'GRGVerticalSegments'), showGrid: cfB(el, 'ShowGRGLines'), kind: cfS(el, 'Type'), minAlt: cfS(el, 'MinAlt'), maxAlt: cfS(el, 'MaxAlt'),
    color: cfArgb(el, 'Color'), lineWidth: cfN(el, 'LineThickness'), filled: cfB(el, 'Filled'), fillOpacity: cfOp(el, 'FillOpacity') };
}
function cfRawPoint(el) {
  const k = cfS(el, 'Type').toLowerCase();
  return { id: cfS(el, 'Tag'), type: 'point', name: cfS(el, 'Name'), lat: cfN(el, 'Lat'), lon: cfN(el, 'Lon'),
    kind: k === 'target' ? 'target' : (k === 'dmpi' ? 'dmpi' : (k === 'exit pt' ? 'exit' : (k === 'lz' ? 'lz' : 'other'))),
    note: cfS(el, 'Comment'), color: cfArgb(el, 'Color') };
}
function cfRawText(el) {
  const k = cfKid(el, 'Text');
  return { id: cfS(el, 'Tag'), type: 'text', name: cfS(el, 'Name'), lat: cfN(el, 'Lat'), lon: cfN(el, 'Lon'), text: k ? k.textContent : '', bg: cfArgb(el, 'BackColor'), fg: cfArgb(el, 'ForeColor'),
    size: cfN(el, 'FontSize'), bold: cfB(el, 'Bold'), border: cfB(el, 'Border'), filled: cfB(el, 'Filled') };
}

const CF_GROUPS = [['Polygons', 'Polygon', cfRawZone], ['Circles', 'Circle', cfRawCircle], ['Orbits', 'Orbit', cfRawOrbit],
  ['AORs', 'AOR', cfRawBox], ['RefPoints', 'RefPoint', cfRawPoint], ['ITBs', 'ITB', cfRawText]];

/* La racine « Mission » → { theatre, layers, pre } : un calque par « Airspace », dans l'ordre du fichier ; pre[k] : le calque k est pré-coché
   (au moins un de ses objets porte Enabled à True) */
function cfParseMission(root, fileName) {
  const layers = [], pre = [];
  cfKids(root, 'Airspace').forEach(a => {
    const raw = [];
    let enabled = false;
    CF_GROUPS.forEach(g => {
      const box = cfKid(a, g[0]);
      if (!box) return;
      cfKids(box, g[1]).forEach(el => { if (cfB(el, 'Enabled')) enabled = true; raw.push(g[2](el)); });
    });
    const l = cfLayer({ id: cfS(a, 'Tag'), name: cfS(a, 'Name'), visible: true, source: { kind: 'combatflite', file: fileName }, items: raw });
    if (l) { layers.push(l); pre.push(enabled); }
  });
  return { theatre: cfS(root, 'Theater'), layers: layers, pre: pre };
}

/* Les octets d'un .cf → { theatre, layers, pre } ; lève 'nods' sans DecompressionStream, 'cf' pour un fichier non reconnu */
async function cfRead(bytes, fileName) {
  const ent = zipFindEntry(bytes);
  if (!ent) throw new Error('cf');
  if (ent.method === 8 && typeof DecompressionStream !== 'function') throw new Error('nods');
  const xml = await zipInflate(ent);
  const doc = new DOMParser().parseFromString(new TextDecoder('utf-8').decode(xml), 'application/xml');
  const root = doc.documentElement;
  if (!root || root.nodeName !== 'Mission' || doc.getElementsByTagName('parsererror').length) throw new Error('cf');
  return cfParseMission(root, fileName);
}

/* Le théâtre que nomme un .cf : son identifiant dans le Route Planner (sans casse), sinon '' */
function cfTheatreId(raw) {
  const low = String(raw == null ? '' : raw).trim().toLowerCase();
  for (let i = 0; i < THEATRES.length; i++) if (THEATRES[i].id.toLowerCase() === low) return THEATRES[i].id;
  return '';
}

/* « 8 zones · 3 points · 1 boîte · 1 texte » ; « vide » sans objet */
function cfCounts(items) {
  const c = {};
  items.forEach(i => { c[i.type] = (c[i.type] || 0) + 1; });
  const parts = CF_COUNT_ORDER.filter(k => c[k]).map(k => t('cf.n.' + k + (c[k] === 1 ? '.1' : '.n'), { n: c[k] }));
  return parts.length ? parts.join(' · ') : t('cf.empty');
}

/* ============= CARTE ============= */
let map = null;
let routeGroup = null;
let decorGroup = null;        /* traits des minutes, chiffres, boîtes de branche, étiquettes « cap · distance » */
let ptMarkers = [];           /* les marqueurs des points de la route, dans l'ordre */
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

/* Le bandeau de repli ne passe jamais sous le contrôle #tapmode : son bord droit reste à 8 px au moins à gauche du contrôle
   (il passe alors sur plusieurs lignes) ; si la place à gauche du contrôle est sous 90 px (écran de moins de 400 px), il se pose sous le contrôle */
const FB_LEFT = 56, FB_GAP = 8, FB_MIN = 90;
function fallbackLayout() {
  const f = $('fallback'), tm = $('tapmode');
  if (!f || !tm || !f.offsetParent) return;
  const host = f.offsetParent.getBoundingClientRect(), tr = tm.getBoundingClientRect();
  if (!tr.width) return;
  const avail = Math.floor(tr.left - host.left - FB_GAP - FB_LEFT);
  if (avail >= FB_MIN) {
    f.style.top = '';
    f.style.maxWidth = avail + 'px';
  } else {
    f.style.top = Math.ceil(tr.bottom - host.top + FB_GAP) + 'px';
    f.style.maxWidth = Math.max(120, Math.floor(host.width - FB_LEFT - 10)) + 'px';
  }
}

function setFallback(on) {
  inFallback = on;
  $('fallback').classList.toggle('show', on);
  if (on) fallbackLayout();
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

function syncAirfieldsNow() {
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

/* Les aérodromes sont des obstacles pour les villes : elles se recalculent quand ils changent */
function syncAirfields() {
  syncAirfieldsNow();
  syncTowns();
}

/* ============= VILLES DCS ============= */
/* Les villes du théâtre, dans leur panneau « towns » (z-index 370 : au-dessus de la grille, sous les aérodromes et les calques).
   À partir du zoom 10, posées sans chevauchement : les villes proches de la route d'abord, puis un ordre stable ; elles évitent aussi
   les points de la route, les références, les boîtes de branche et les aérodromes affichés. Le résultat ne dépend que de la vue,
   de la route et des obstacles. */
const TOWNS_ZOOM = 10;         /* les villes se dessinent à partir de ce zoom */
const TW_NEAR_NM = 10;         /* groupe A : les villes à 10 NM ou moins de la route */
const TW_DOT = 5;              /* le point : 5 px */
const TW_GAP = 4;              /* du point au nom : 4 px */
const TW_H = 13;               /* hauteur de la ligne du nom */
const TW_MARGIN = 2;           /* marge de l'étiquette, tout autour, pour la pose : 2 px à partir du zoom 11 */
const TW_MARGIN_Z10 = 8;       /* ... et 8 px au zoom 10 (zoom < 11) */
const TW_PAD = 0.1;            /* emprise des candidates : la vue agrandie de 10 % de chaque côté */
const TW_FONT = '500 11px Oswald, "Arial Narrow", sans-serif';
const TW_FONT_CAP = '700 11px Oswald, "Arial Narrow", sans-serif';   /* le nom d'une ville « capitales » : Oswald 700 */
function twMargin(z) { return z < 11 ? TW_MARGIN_Z10 : TW_MARGIN; }

let twLayer = null;            /* le groupe des étiquettes posées, dans l'ordre de priorité */
let twSig = '';                /* ce qui est posé (théâtre, villes, côtés) : inchangé, le DOM n'est pas refait */
let twHold = false;            /* vrai pendant un glisser (un point, une référence, une boîte) : rien n'est recalculé */
let twInfo = null;             /* le dernier calcul (candidates, obstacles), pour les contrôles */
let twCtx = null;
const twWidths = new Map();    /* largeur du nom, à la police réelle, par nom */
const twLists = {};            /* par théâtre : les villes dans l'ordre stable (capitales d'abord, puis FNV-1a, puis nom) */

let twHoldT = 0;
function twDragStart() { twHold = true; clearTimeout(twHoldT); twHoldT = setTimeout(() => { twHold = false; }, 60000); }
function twDragEnd() { twHold = false; clearTimeout(twHoldT); }

function townsOf(theatre) { return Object.prototype.hasOwnProperty.call(TOWNS, theatre) ? TOWNS[theatre] : null; }

/* FNV-1a 32 bits du nom en UTF-8 (base 0x811c9dc5, multiplicateur 0x01000193), non signé */
function fnv1a(s) {
  const b = new TextEncoder().encode(s);
  let h = 0x811c9dc5;
  for (let i = 0; i < b.length; i++) h = Math.imul(h ^ b[i], 0x01000193) >>> 0;
  return h >>> 0;
}

/* Un nom entièrement en capitales : au moins une lettre, aucune minuscule */
function twIsCaps(n) { return /\p{L}/u.test(n) && !/\p{Ll}/u.test(n); }

function twList(theatre) {
  if (twLists[theatre]) return twLists[theatre];
  const raw = townsOf(theatre);
  if (!raw) return null;
  const list = raw.map((a, i) => ({ i: i, n: a[0], lat: a[1], lon: a[2], caps: twIsCaps(a[0]), h: fnv1a(a[0]) }));
  list.sort((a, b) => (a.caps === b.caps ? 0 : a.caps ? -1 : 1) || (a.h - b.h) || (a.n < b.n ? -1 : a.n > b.n ? 1 : 0));
  twLists[theatre] = list;
  return list;
}

/* La largeur du nom (sans ses espaces de bout, que la page ne dessine pas), à la police réelle (graisse comprise : 700 pour un nom
   entièrement en capitales, 500 sinon), mise en cache par nom */
function twWidth(name) {
  let w = twWidths.get(name);
  if (w !== undefined) return w;
  const k = name.trim();
  try {
    if (!twCtx) twCtx = document.createElement('canvas').getContext('2d');
    twCtx.font = twIsCaps(name) ? TW_FONT_CAP : TW_FONT;
    w = twCtx.measureText(k).width;
  } catch (e) { w = k.length * 6; }
  twWidths.set(name, w);
  return w;
}

/* Distance de la ville à la route : au segment le plus proche entre deux points consécutifs (sur la sphère du bloc de coordonnées) ;
   un seul point : la distance à ce point */
function twVec(lat, lon) {
  const la = lat * Math.PI / 180, lo = lon * Math.PI / 180, c = Math.cos(la);
  return [c * Math.cos(lo), c * Math.sin(lo), Math.sin(la)];
}
function twCross(a, b) { return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]; }
function twDot(a, b) { return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]; }
function twAngle(a, b) { const c = twCross(a, b); return Math.atan2(Math.hypot(c[0], c[1], c[2]), twDot(a, b)); }

function twRoutePrep() {
  const v = S.points.map(p => twVec(p.lat, p.lon));
  const segs = [];
  for (let i = 1; i < v.length; i++) {
    const n = twCross(v[i - 1], v[i]), l = Math.hypot(n[0], n[1], n[2]);
    segs.push({ a: v[i - 1], b: v[i], n: l > 1e-12 ? [n[0] / l, n[1] / l, n[2] / l] : null });
  }
  return { v: v, segs: segs };
}

/* → km ; Infinity sans point */
function twRouteDistKm(P, rt) {
  if (!rt.v.length) return Infinity;
  if (rt.v.length === 1) return twAngle(P, rt.v[0]) * NAV_R_KM;
  let best = Infinity;
  rt.segs.forEach(sg => {
    let ang = Math.min(twAngle(P, sg.a), twAngle(P, sg.b));
    if (sg.n) {
      const pd = twDot(P, sg.n);
      const c = [P[0] - pd * sg.n[0], P[1] - pd * sg.n[1], P[2] - pd * sg.n[2]], cl = Math.hypot(c[0], c[1], c[2]);
      if (cl > 1e-12) {
        const u = [c[0] / cl, c[1] / cl, c[2] / cl];
        if (twDot(twCross(sg.a, u), sg.n) >= 0 && twDot(twCross(u, sg.b), sg.n) >= 0) ang = Math.min(ang, Math.asin(Math.min(1, Math.abs(pd))));
      }
    }
    if (ang < best) best = ang;
  });
  return best * NAV_R_KM;
}

/* Les obstacles, en pixels de la carte (lus dans le DOM de la carte) : les marqueurs des points de la route et des références avec leur nom,
   les boîtes de branche, les chiffres des minutes, et les aérodromes affichés au zoom courant avec leur nom s'il est visible. Le contrôle
   Point · Réf. · Lire, la loupe, les traits des minutes et le tracé n'en sont pas. */
function twObstacles() {
  /* « moveend » précède « viewreset » : après un grand déplacement, les marqueurs ne sont pas encore replacés ; on les replace avant de les lire */
  const fresh = m => { if (m && m.update && m._icon) m.update(); };
  ptMarkers.forEach(fresh);
  if (refGroup) refGroup.eachLayer(fresh);
  if (decorGroup) decorGroup.eachLayer(m => { if (m.options && (m.options.pane === 'legboxes' || m.options.pane === 'legnums')) fresh(m); });
  if (afLayer) afLayer.eachLayer(fresh);
  const base = map.getContainer().getBoundingClientRect();
  const out = [];
  const push = (kind, el) => {
    const r = el.getBoundingClientRect();
    if (!(r.width > 0 && r.height > 0)) return;
    out.push({ kind: kind, l: r.left - base.left, t: r.top - base.top, r: r.right - base.left, b: r.bottom - base.top });
  };
  ptMarkers.forEach(m => {
    const el = m.getElement && m.getElement();
    if (el) el.querySelectorAll('.wp-dot, .wp-name, .wp-time').forEach(e => push('wp', e));
  });
  if (refGroup) refGroup.eachLayer(m => {
    const el = m.getElement && m.getElement();
    if (el) el.querySelectorAll('.rf-dot, .wp-name').forEach(e => push('ref', e));
  });
  const boxes = map.getPane('legboxes');
  if (boxes) boxes.querySelectorAll('.lb').forEach(e => push('box', e));
  const nums = map.getPane('legnums');          /* les chiffres des minutes (les traits et le tracé n'en sont pas) */
  if (nums) nums.querySelectorAll('.rp-tickn').forEach(e => push('tickn', e));
  if (afLayer) afLayer.eachLayer(m => {
    const el = m.getElement && m.getElement();
    if (!el) return;
    push('af', el);
    const nm = el.querySelector('.af-name');
    if (nm) push('af', nm);
  });
  return out;
}

function twHits(r, rects) {
  for (let i = 0; i < rects.length; i++) {
    const o = rects[i];
    if (r.l < o.r && r.r > o.l && r.t < o.b && r.b > o.t) return true;
  }
  return false;
}

/* Le rectangle de l'étiquette (le point et le nom, sans marge) autour de l'ancre (x, y) ; side : « r » (nom à droite) ou « l » */
function twRect(x, y, w, side) {
  const half = TW_DOT / 2, hh = TW_H / 2;
  return side === 'r' ? { l: x - half, t: y - hh, r: x + half + TW_GAP + w, b: y + hh }
                      : { l: x - half - TW_GAP - w, t: y - hh, r: x + half, b: y + hh };
}
function twGrow(r, m) { return { l: r.l - m, t: r.t - m, r: r.r + m, b: r.b + m }; }

function twIcon(e, side, w) {
  const half = TW_DOT / 2, hh = TW_H / 2, tot = TW_DOT + TW_GAP + w;
  const dotTop = (TW_H - TW_DOT) / 2;
  const nm = '<span class="tw-nm' + (e.caps ? ' tw-cap' : '') + '" style="left:' + (side === 'r' ? TW_DOT + TW_GAP : 0) + 'px;top:0;width:' + w + 'px;height:' + TW_H + 'px">' + esc(e.n) + '</span>';
  const dot = '<i class="tw-dot" style="left:' + (side === 'r' ? 0 : w + TW_GAP) + 'px;top:' + dotTop + 'px"></i>';
  return L.divIcon({
    className: 'tw-icon', iconSize: [0, 0], iconAnchor: [0, 0],
    html: '<div class="tw tw-' + side + '" style="left:' + (side === 'r' ? -half : -(half + TW_GAP + w)) + 'px;top:' + (-hh) + 'px;width:' + tot + 'px;height:' + TW_H + 'px">' +
      (side === 'r' ? dot + nm : nm + dot) + '</div>'
  });
}

/* Recalculé au zoom et au déplacement, à toute modification de la route, des références ou d'une boîte de branche, au changement
   de théâtre et à l'interrupteur — jamais pendant un glisser */
function syncTowns() {
  if (!mapCreated || !twLayer || twHold) return;
  const list = S.ui.towns ? twList(S.theatre) : null;
  if (!list || map.getZoom() < TOWNS_ZOOM || !mapSized()) {
    if (twSig !== '') { twLayer.clearLayers(); twSig = ''; }
    twInfo = null;
    return;
  }
  /* 1 · les candidates : la vue agrandie de 10 % de chaque côté */
  const bd = map.getBounds().pad(TW_PAD), s = bd.getSouth(), n = bd.getNorth(), w = bd.getWest(), e = bd.getEast();
  const cand = list.filter(c => c.lat >= s && c.lat <= n && c.lon >= w && c.lon <= e);
  /* 2 · la priorité : A (à 10 NM ou moins de la route, par distance), puis B (capitales) et C (les autres), dans l'ordre stable de la liste */
  const rt = twRoutePrep();
  const near = [], rest = [];
  cand.forEach(c => {
    const d = rt.v.length ? twRouteDistKm(twVec(c.lat, c.lon), rt) / NM_KM : Infinity;
    if (d <= TW_NEAR_NM) near.push({ c: c, d: d }); else rest.push(c);
  });
  near.sort((a, b) => (a.d - b.d) || (a.c.n < b.c.n ? -1 : a.c.n > b.c.n ? 1 : 0));
  const order = near.map(x => x.c).concat(rest);
  /* 3 · les obstacles, 4 · le glouton : à droite, sinon à gauche, sinon rien */
  const obs = twObstacles();
  const mg = twMargin(map.getZoom());
  const placed = [], res = [];
  order.forEach(c => {
    const a = map.layerPointToContainerPoint(map.latLngToLayerPoint([c.lat, c.lon]).round());
    const wd = twWidth(c.n);
    const rr = twRect(a.x, a.y, wd, 'r'), rl = twRect(a.x, a.y, wd, 'l');
    let side = null, rect = null;
    if (!twHits(twGrow(rr, mg), obs) && !twHits(twGrow(rr, mg), placed)) { side = 'r'; rect = rr; }
    else if (!twHits(twGrow(rl, mg), obs) && !twHits(twGrow(rl, mg), placed)) { side = 'l'; rect = rl; }
    if (side) placed.push(rect);
    res.push({ c: c, w: wd, side: side, rect: rect, right: rr, left: rl });
  });
  twInfo = { zoom: map.getZoom(), margin: mg, obstacles: obs, candidates: res };
  const shown = res.filter(x => x.side);
  const sig = S.theatre + '|' + shown.map(x => x.c.i + x.side + x.w).join(',');
  if (sig === twSig) return;
  twSig = sig;
  twLayer.clearLayers();
  shown.forEach(x => {
    const c = x.c;
    const mk = L.marker([c.lat, c.lon], { pane: 'towns', keyboard: false, title: c.n, icon: twIcon(c, x.side, x.w) });
    /* une ville agit comme un aérodrome : un point de route (mode Point), une référence (mode Réf.), rien en mode Lire */
    mk.on('click', ev => { L.DomEvent.stop(ev); addFromAirfield(c.lat, c.lon, c.n.toUpperCase()); });
    twLayer.addLayer(mk);
  });
}

/* Pour les contrôles : les étiquettes posées (nom, côté, rectangle), les candidates non posées (leurs deux places) et les obstacles */
function townsReport() {
  if (!twInfo) return null;
  const rd = r => r ? { l: r.l, t: r.t, r: r.r, b: r.b } : null;
  return {
    zoom: twInfo.zoom, margin: twInfo.margin, obstacles: twInfo.obstacles.map(o => ({ kind: o.kind, l: o.l, t: o.t, r: o.r, b: o.b })),
    candidates: twInfo.candidates.map(x => ({ name: x.c.n, side: x.side, width: x.w, rect: rd(x.rect), right: rd(x.right), left: rd(x.left) }))
  };
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
  /* Les villes DCS : au-dessus de la grille, sous les aérodromes (380) et les calques (390) */
  map.createPane('towns').style.zIndex = 370;
  /* L'anneau de la recherche : au-dessus de tout, sans toucher */
  const ringPane = map.createPane('ring');
  ringPane.style.zIndex = 650;
  ringPane.style.pointerEvents = 'none';
  map.createPane('refs').style.zIndex = 450;
  /* Les chiffres des minutes : au-dessus des références, sous les points ; les boîtes de branche : au-dessus des points */
  map.createPane('legticks').style.zIndex = 420;        /* les traits des minutes : au-dessus de la route, sous les références */
  map.createPane('legnums').style.zIndex = 455;
  map.createPane('legboxes').style.zIndex = 620;
  /* Les calques CombatFlite : au-dessus du fond, de la grille et des aérodromes, sous la route, les références et les boîtes de branche */
  map.createPane('layers').style.zIndex = LAYERS_Z;
  /* Le mode Dessin : poignées, contour de sélection et tracé en cours, au-dessus des boîtes de branche (620) et sous l'anneau de la recherche (650) */
  map.createPane('drawedit').style.zIndex = 640;
  gridCanvas = document.createElement('canvas');
  gridCanvas.className = 'mgrs-canvas';
  pane.appendChild(gridCanvas);
  twLayer = L.layerGroup().addTo(map);
  cfGroup = L.layerGroup().addTo(map);
  refGroup = L.layerGroup().addTo(map);
  routeGroup = L.layerGroup().addTo(map);
  decorGroup = L.layerGroup().addTo(map);
  map.on('move zoom viewreset resize', scheduleGrid);
  map.on('zoomend', drawRoute);
  map.on('zoomend', syncAfZoom);
  map.on('zoomend', cfSyncPointNames);
  syncAfZoom();
  map.on('moveend', syncTowns);          /* après zoomend : les classes des aérodromes et la route sont à jour */
  createTapControl();
  createSearchControl();
  map.on('click', onMapClick);
  /* Le conteneur change de taille (fenêtre, rotation, iframe rendue visible par le shell) */
  const wrap = $('map');
  const onSize = () => {
    if (!wrap.clientWidth || !wrap.clientHeight) return;
    map.invalidateSize({ animate: false });
    if (pendingView) { const f = pendingView; pendingView = null; f(); }
    scheduleGrid();
    syncTowns();
  };
  if (window.ResizeObserver) new ResizeObserver(onSize).observe(wrap);
  window.addEventListener('resize', onSize);
}

/* En portrait (la page ne défile pas), un champ du panneau qui prend le focus est amené en vue dans le panneau, y compris
   après le redimensionnement du viewport visuel (clavier virtuel) ; la carte ne bouge pas */
const PORTRAIT_FIXED_MQ = '(max-width: 1099px) and ((min-height: 600px) or (orientation: portrait))';
function revealPanelField(el) {
  if (!window.matchMedia || !window.matchMedia(PORTRAIT_FIXED_MQ).matches) return;
  const go = () => { try { el.scrollIntoView({ block: 'center', inline: 'nearest' }); } catch (e) { /* ignore */ } };
  go();
  const vv = window.visualViewport;
  if (!vv) return;
  const again = () => { vv.removeEventListener('resize', again); if (document.activeElement === el) go(); };
  vv.addEventListener('resize', again);
  setTimeout(() => vv.removeEventListener('resize', again), 1000);
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

function wpIcon(p, i, tm) {
  return L.divIcon({
    className: 'wp-icon', iconSize: [30, 30], iconAnchor: [15, 15],
    html: '<div class="wp-dot' + (i === sel ? ' sel' : '') + '">' + i + '</div><div class="wp-name">' + esc(p.name) + '</div>' +
      '<div class="wp-time">' + esc(fmtElapsed(tm.el[i])) + '</div>'
  });
}

/* Le temps écoulé sous chaque point, remis à jour pendant qu'un point se déplace (les marqueurs ne sont pas refaits) */
function updateTimes() {
  const tm = timing();
  ptMarkers.forEach((m, k) => {
    const el = m.getElement && m.getElement();
    const n = el && el.querySelector('.wp-time');
    if (n) n.textContent = fmtElapsed(tm.el[k]);
  });
}

function drawRoute() {
  if (!routeGroup) return;
  routeGroup.clearLayers();
  linePair = null;
  ptMarkers = [];
  const pts = S.points;
  const tm = timing();
  const ll = pts.map(p => [p.lat, p.lon]);
  if (ll.length > 1) {
    /* Tracé noir : la ligne #1f1c16 de 4 px sur un liseré papier de 8 px ; sinon le tracé de la couleur du thème */
    const black = S.ui.trace === 'black';
    linePair = [
      L.polyline(ll, black ? { color: '#f0e8d6', weight: 8, opacity: 0.75, lineCap: 'round', lineJoin: 'round', interactive: false }
                           : { color: '#1f1c16', weight: 9, opacity: 0.45, lineCap: 'round', lineJoin: 'round', interactive: false }).addTo(routeGroup),
      L.polyline(ll, black ? { color: '#1f1c16', weight: 4, opacity: 1, lineCap: 'round', lineJoin: 'round', interactive: false }
                           : { color: routeColor(), weight: 5, opacity: 1, lineCap: 'round', lineJoin: 'round', interactive: false }).addTo(routeGroup)
    ];
  }
  for (let i = 1; i < pts.length; i++) {
    const a = pts[i - 1], b = pts[i];
    const pa = map.latLngToContainerPoint([a.lat, a.lon]), pb = map.latLngToContainerPoint([b.lat, b.lon]);
    const px = pa.distanceTo(pb);
    if (px >= INSERT_MIN_PX && tapMode !== 'read' && tapMode !== 'draw') {      /* en mode Lire ou Dessin, pas de « + » d'insertion */
      const q = [a.lat + (b.lat - a.lat) * INSERT_AT, a.lon + (b.lon - a.lon) * INSERT_AT];
      const ins = L.marker(q, {
        zIndexOffset: 400, keyboard: false, title: t('tip.insert'),
        icon: L.divIcon({ className: 'ins-icon', iconSize: [18, 18], iconAnchor: [9, 9], html: '<div class="ins">+</div>' })
      }).addTo(routeGroup);
      ins.on('click', ev => { L.DomEvent.stop(ev); if (tapMode !== 'read' && tapMode !== 'draw') insertPoint(i, q[0], q[1]); });
    }
  }
  pts.forEach((p, i) => {
    const mk = L.marker([p.lat, p.lon], { draggable: true, autoPan: true, zIndexOffset: i === sel ? 2000 : 1000, icon: wpIcon(p, i, tm), title: p.name });
    ptMarkers.push(mk);
    mk.on('dragstart', twDragStart);
    mk.on('drag', ev => {
      const q = ev.target.getLatLng();
      p.lat = r7(q.lat); p.lon = r7(q.lng);
      if (linePair) { const l2 = S.points.map(x => [x.lat, x.lon]); linePair.forEach(pl => pl.setLatLngs(l2)); }
      renderNav();
      drawDecor();
      updateTimes();
    });
    mk.on('dragend', () => {
      twDragEnd();
      sel = i; selR = -1;
      persistState();
      setTimeout(() => { drawRoute(); drawRefs(); syncRows(); renderNav(); }, 0);
    });
    mk.on('click', ev => { L.DomEvent.stop(ev); selectPoint(i); });
    mk.addTo(routeGroup);
  });
  drawDecor();
}

/* ============= TRAITS DES MINUTES, CHIFFRES ET BOÎTES DE BRANCHE ============= */
/* Les traits d'une branche : un trait coupe le tracé à angle droit à chaque minute entière (recomptée depuis le début de la branche),
   ou toutes les 5 minutes quand la branche est trop serrée ; pa : départ à l'écran, (ux, uy) : vecteur unitaire du sens du vol, len : longueur en px */
function drawTicks(i, pa, ux, uy, len, leg) {
  const T = leg.sec / 60;                       /* durée de la branche en minutes */
  if (!(T > 0) || !(len > 0)) return;
  const p = len / T;                            /* pixels par minute */
  let step;
  if (p >= TICK_DENSE_PX) step = 1;
  else if (5 * p >= TICK_DENSE_PX) step = 5;
  else return;
  const rx = -uy, ry = ux;                      /* à droite du sens du vol */
  const black = S.ui.ticks === 'black';
  const nEvery = Math.max(1, Math.ceil(TICK_NUM_GAP / (step * p)));   /* un chiffre sur n traits */
  const size = map.getSize();
  const cull = T / step > TICK_CULL_ABOVE;
  let j = 0;
  for (let k = step; k < T && T - k >= TICK_END_MIN; k += step) {
    j++;
    const f = k / T;
    const cx = pa.x + ux * len * f, cy = pa.y + uy * len * f;
    if (cull && (cx < -60 || cy < -60 || cx > size.x + 60 || cy > size.y + 60)) continue;
    /* le trait : 12 px de long (6 de chaque côté), 18 px aux multiples de 5 ; épaisseur 2,5 px sur un liseré de 4,5 px.
       Un bloc tourné, posé au pixel près (le marqueur Leaflet est arrondi : le reste sous-pixel passe par .lb-pos) */
    const tl = k % 5 === 0 ? 18 : 12;
    const tll = map.containerPointToLatLng([cx, cy]);
    const ab = map.project(tll);
    const fx = Math.round((ab.x - Math.round(ab.x)) * 100) / 100, fy = Math.round((ab.y - Math.round(ab.y)) * 100) / 100;
    const ang = Math.round(Math.atan2(ry, rx) * 180 / Math.PI * 1000) / 1000;
    L.marker(tll, {
      pane: 'legticks', interactive: false, keyboard: false,
      icon: L.divIcon({ className: 'rp-tick-icon', iconSize: [0, 0],
        html: '<div class="lb-pos" style="transform:translate(' + fx + 'px,' + fy + 'px)"><div class="rp-tick rp-leg' + i + (black ? ' blk' : '') + (tl === 18 ? ' rp-tick5' : '') +
          '" data-leg="' + i + '" data-k="' + k + '" style="width:' + tl + 'px;left:' + (-tl / 2) + 'px;transform:rotate(' + ang + 'deg)"><i></i></div></div>' })
    }).addTo(decorGroup);
    if (j % nEvery === 0) {
      /* le chiffre : 20 px à gauche du tracé dans le sens du vol, côté opposé aux boîtes */
      const nl = map.containerPointToLatLng([cx - rx * TICK_NUM_OFF, cy - ry * TICK_NUM_OFF]);
      L.marker(nl, {
        pane: 'legnums', interactive: false, keyboard: false,
        icon: L.divIcon({ className: 'rp-tickn-icon', iconSize: [0, 0], html: '<span class="rp-tickn' + (black ? ' blk' : '') + '">' + esc(t('tick.fmt', { k: k })) + '</span>' })
      }).addTo(decorGroup);
    }
  }
}

/* Le contenu d'une boîte : [cap, distance, vitesse, altitude d'arrivée, ETE] ; la minimale ne garde que les deux premières */
function boxLines(i, leg, mode) {
  const p = S.points[i];
  const lines = [leg.cap + t(navIsMag() ? 'lb.mag' : 'lb.true'), fmtDist(leg.km)];
  if (mode === 'full') { lines.push(speedText(leg.v)); lines.push(altText(p)); lines.push(t('lb.ete') + ' ' + fmtEte(leg.sec)); }
  return lines;
}

/* La boîte en maison : toit (le nom du point d'arrivée) puis les lignes. Toit en haut (up), ou toit en bas avec le nom au-dessus du toit
   et les lignes au-dessus du nom, dans le même ordre ; rot : l'angle appliqué ; (fx, fy) : le reste sous-pixel du centre */
function boxHtml(i, leg, mode, up, rot, fx, fy) {
  const D = BOX_DIMS[mode], w = D.w, roof = D.roof, rows = D.rows, H = roof + rows * BOX_ROW_H, e = 0.8, m = w / 2;
  const lines = boxLines(i, leg, mode);
  let d, ys = [];
  if (up) {
    d = 'M' + e + ',' + roof + ' L' + m + ',' + e + ' L' + (w - e) + ',' + roof + ' L' + (w - e) + ',' + (H - e) + ' L' + e + ',' + (H - e) + ' Z';
    for (let k = 0; k < rows; k++) ys.push(roof + k * BOX_ROW_H);
  } else {
    const base = rows * BOX_ROW_H;
    d = 'M' + e + ',' + e + ' L' + (w - e) + ',' + e + ' L' + (w - e) + ',' + base + ' L' + m + ',' + (H - e) + ' L' + e + ',' + base + ' Z';
    for (let k = 1; k <= rows; k++) ys.push(k * BOX_ROW_H);
  }
  const ln = ys.map(y => 'M' + e + ',' + y + ' H' + (w - e)).join(' ');
  const nm = '<div class="lb-nm" style="top:' + (up ? roof - 17 : rows * BOX_ROW_H + 1) + 'px">' + (mode === 'full' ? esc(S.points[i].name.toUpperCase()) : '') + '</div>';
  const rowsHtml = lines.map((tx, k) =>
    '<div class="lb-r' + (mode === 'full' && k === 4 ? ' lb-ete' : '') + '" style="top:' + ((up ? roof : 0) + k * BOX_ROW_H) + 'px">' + esc(tx) + '</div>').join('');
  return '<div class="lb-pos" style="transform:translate(' + fx + 'px,' + fy + 'px)">' +
    '<div class="lb lb-' + mode + (up ? ' lb-up' : ' lb-down') + '" data-leg="' + i + '" data-rot="' + rot + '" style="width:' + w + 'px;height:' + H + 'px;left:' + (-w / 2) + 'px;top:' + (-H / 2) + 'px;transform:rotate(' + rot + 'deg)">' +
    '<svg class="lb-shape" width="' + w + '" height="' + H + '" viewBox="0 0 ' + w + ' ' + H + '" aria-hidden="true"><path class="lb-bg" d="' + d + '"/><path class="lb-ln" d="' + ln + '"/></svg>' +
    (up ? nm + rowsHtml : rowsHtml + nm) + '</div></div>';
}

/* La boîte de la branche (i-1 → i) : parallèle à sa branche, la pointe du toit dans le sens du tracé ; sa place est gardée en pixels
   (along le long du tracé, side à sa droite) depuis le milieu de la branche à l'écran */
function drawBox(i, pa, pb, len, leg) {
  const mode = S.legBoxes, D = BOX_DIMS[mode];
  const p = S.points[i];
  const ux = (pb.x - pa.x) / len, uy = (pb.y - pa.y) / len;
  const rx = -uy, ry = ux;
  const mx = (pa.x + pb.x) / 2, my = (pa.y + pb.y) / 2;
  const along = p.box ? p.box.along : 0, side = p.box ? p.box.side : D.w / 2 + BOX_GAP;
  const cx = mx + along * ux + side * rx, cy = my + along * uy + side * ry;
  const h = Math.atan2(pb.x - pa.x, -(pb.y - pa.y)) * 180 / Math.PI;      /* cap à l'écran : 0 vers le haut, sens horaire */
  const up = Math.abs(h) <= 90;
  const rot = Math.round((up ? h : (h > 0 ? h - 180 : h + 180)) * 1000) / 1000;
  const ll = map.containerPointToLatLng([cx, cy]);
  const ab = map.project(ll);
  const fx = Math.round((ab.x - Math.round(ab.x)) * 100) / 100, fy = Math.round((ab.y - Math.round(ab.y)) * 100) / 100;
  /* le trait de rappel : sous la boîte, du milieu de la branche à son centre */
  if (Math.abs(along) > 40 || Math.abs(side) > D.w / 2 + 36) {
    L.polyline([map.containerPointToLatLng([mx, my]), ll], { color: routeColor(), weight: 1.4, opacity: 1, dashArray: '4 4', lineCap: 'butt', interactive: false, className: 'rp-recall rp-leg' + i }).addTo(decorGroup);
  }
  const mk = L.marker(ll, {
    pane: 'legboxes', draggable: true, autoPan: false, keyboard: false, title: t('lb.tip'),
    icon: L.divIcon({ className: 'lb-icon', iconSize: [0, 0], html: boxHtml(i, leg, mode, up, rot, fx, fy) })
  }).addTo(decorGroup);
  const sp = map.latLngToContainerPoint(ll);
  mk.on('click', ev => { L.DomEvent.stop(ev); });
  mk.on('dragstart', twDragStart);
  mk.on('dragend', () => {
    twDragEnd();
    const q = map.latLngToContainerPoint(mk.getLatLng());
    const dx = cx + (q.x - sp.x) - mx, dy = cy + (q.y - sp.y) - my;
    const clamp = v => Math.max(-BOX_LIMIT, Math.min(BOX_LIMIT, Math.round(v)));
    if (S.points[i]) S.points[i].box = { along: clamp(dx * ux + dy * uy), side: clamp(dx * rx + dy * ry) };
    persistState();
    setTimeout(drawDecor, 0);
  });
}

/* Tout ce qui se dessine le long des branches ; redessiné au zoom, à chaque changement de la route ou des réglages */
function drawDecorNow() {
  if (!decorGroup) return;
  decorGroup.clearLayers();
  const pts = S.points;
  if (pts.length < 2) return;
  const tm = timing();
  const px = pts.map(p => map.latLngToContainerPoint([p.lat, p.lon]));
  for (let i = 1; i < pts.length; i++) {
    const pa = px[i - 1], pb = px[i];
    const len = pa.distanceTo(pb);
    const leg = tm.legs[i];
    if (len > 0) drawTicks(i, pa, (pb.x - pa.x) / len, (pb.y - pa.y) / len, len, leg);
    if (S.legBoxes === 'none') {
      /* « Aucune » : l'étiquette « cap · distance » de toujours */
      if (len >= LEG_LABEL_MIN_PX) {
        const a = pts[i - 1], b = pts[i];
        L.marker([(a.lat + b.lat) / 2, (a.lon + b.lon) / 2], {
          interactive: false, keyboard: false,
          icon: L.divIcon({ className: 'leg-label-icon', iconSize: [0, 0], html: '<span class="leg-label">' + leg.cap + '° · ' + esc(fmtDist(leg.km)) + '</span>' })
        }).addTo(decorGroup);
      }
    } else if (len >= BOX_MIN_PX) {
      drawBox(i, pa, pb, len, leg);
    }
  }
}

function drawDecor() {
  drawDecorNow();
  syncTowns();       /* les boîtes de branche sont des obstacles pour les villes */
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
    mk.on('dragstart', twDragStart);
    mk.on('drag', ev => {
      const q = ev.target.getLatLng();
      p.lat = r7(q.lat); p.lon = r7(q.lng);
      renderNav();
    });
    mk.on('dragend', () => {
      twDragEnd();
      selR = i; sel = -1;
      persistState();
      setTimeout(() => { drawRoute(); drawRefs(); syncRows(); renderNav(); }, 0);
    });
    mk.on('click', ev => { L.DomEvent.stop(ev); selectRef(i); });
    mk.addTo(refGroup);
  });
  syncTowns();
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
  if (SR.open) { srClose(); return null; }       /* un toucher sur la carte, la recherche ouverte : il ferme le panneau et ne pose rien */
  if (tapMode === 'read' || tapMode === 'draw') return null;
  return tapMode === 'ref' ? addRef(lat, lon, name) : addPoint(lat, lon, name);
}

function onMapClick(ev) {
  if (tapMode === 'draw') { drMapClick(ev); return; }
  addAt(ev.latlng.lat, ev.latlng.lng);
}

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
  if (S.points.length) { delete S.points[0].gs; delete S.points[0].box; }   /* le point 0 n'a ni vitesse ni boîte */
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

/* ============= CALQUES : GÉOMÉTRIE ET DESSIN ============= */
let cfGroup = null;           /* les objets des calques visibles, dans le pane « layers » (z-index 390) */
let cfPointMarks = [];        /* les symboles de points : { mk, name } — le nom ne se dessine qu'à partir du zoom 11 */

const CF_RAD = Math.PI / 180;

/* La destination sur la sphère (rayon 6 371 008,8 m) : [lat, lon], un cap (degrés vrais) et une distance en NM */
function cfDest(p, brg, nm) { const d = legDest({ lat: p[0], lon: p[1] }, brg, nm * NM_KM); return [d.lat, d.lon]; }

/* La boîte de CombatFlite : ses quatre coins (NO, NE, SE, SO), les traits de sa grille, le milieu du côté NO–NE */
function cfBoxGeom(b) {
  const no = cfDest([b.lat, b.lon], b.brg - 90, b.widthNm / 2);
  const ne = cfDest(no, b.brg, b.lengthNm);
  const se = cfDest(ne, b.brg + 90, b.widthNm);
  const so = cfDest(se, b.brg + 180, b.lengthNm);
  const grid = [];
  for (let k = 1; k < b.gridH; k++) { const a = cfDest(no, b.brg, b.lengthNm * k / b.gridH); grid.push([a, cfDest(a, b.brg + 90, b.widthNm)]); }
  for (let k = 1; k < b.gridV; k++) { const a = cfDest(no, b.brg + 90, b.widthNm * k / b.gridV); grid.push([a, cfDest(a, b.brg, b.lengthNm)]); }
  return { corners: [no, ne, se, so], grid: grid, nameAt: [(no[0] + ne[0]) / 2, (no[1] + ne[1]) / 2] };
}

/* L'hippodrome : la branche d'arrivée va de (lat2, lon2) à (lat, lon) au cap brg ; le virage est à la gauche de brg (clockwise faux) ou à sa
   droite ; deux branches écartées de widthNm, reliées par deux demi-cercles de diamètre widthNm. Repère métrique local autour de (lat, lon). */
function cfOrbitGeom(o) {
  const kx = Math.cos(o.lat * CF_RAD) * 111320, ky = 110540;
  const xy = (la, lo) => [(lo - o.lon) * kx, (la - o.lat) * ky];
  const ll = p => [o.lat + p[1] / ky, o.lon + p[0] / kx];
  const th = o.brg * CF_RAD, ux = Math.sin(th), uy = Math.cos(th);
  const nx = o.clockwise ? uy : -uy, ny = o.clockwise ? -ux : ux;          /* le côté du virage : la gauche de brg, ou sa droite */
  const w = o.widthNm * NM_M, r = w / 2;
  const a0 = xy(o.lat2, o.lon2), a1 = [0, 0];
  const pts = [a0, a1];
  const cx1 = a1[0] + nx * r, cy1 = a1[1] + ny * r;                        /* centre du demi-cercle d'arrivée */
  for (let k = 1; k <= 12; k++) { const a = Math.PI * k / 12; pts.push([cx1 + r * (-Math.cos(a) * nx + Math.sin(a) * ux), cy1 + r * (-Math.cos(a) * ny + Math.sin(a) * uy)]); }
  const cx0 = a0[0] + nx * r, cy0 = a0[1] + ny * r;                        /* centre du demi-cercle de départ */
  for (let k = 0; k <= 12; k++) { const a = Math.PI * k / 12; pts.push([cx0 + r * (Math.cos(a) * nx - Math.sin(a) * ux), cy0 + r * (Math.cos(a) * ny - Math.sin(a) * uy)]); }
  const outer = [(a0[0] + a1[0]) / 2 + nx * w, (a0[1] + a1[1]) / 2 + ny * w];
  return { path: pts.map(ll), nameAt: ll(outer) };
}

/* Une bande de widthNm centrée sur la ligne : les côtés décalés de widthNm / 2, la direction en un point étant celle de ses deux voisins */
function cfBand(pts, widthNm) {
  const half = widthNm * NM_M / 2, left = [], right = [];
  for (let i = 0; i < pts.length; i++) {
    const a = pts[Math.max(0, i - 1)], b = pts[Math.min(pts.length - 1, i + 1)], p = pts[i];
    const kx = Math.cos(p[0] * CF_RAD) * 111320, ky = 110540;
    let dx = (b[1] - a[1]) * kx, dy = (b[0] - a[0]) * ky;
    const m = Math.hypot(dx, dy) || 1;
    dx /= m; dy /= m;
    const nx = -dy, ny = dx;
    left.push([p[0] + ny * half / ky, p[1] + nx * half / kx]);
    right.push([p[0] - ny * half / ky, p[1] - nx * half / kx]);
  }
  return left.concat(right.reverse());
}

/* La courbe de Catmull-Rom qui passe par les points, fermée : 8 segments par côté */
function cfSpline(pts) {
  const n = pts.length, out = [];
  const g = i => pts[((i % n) + n) % n];
  for (let i = 0; i < n; i++) {
    const p0 = g(i - 1), p1 = g(i), p2 = g(i + 1), p3 = g(i + 2);
    for (let k = 0; k < 8; k++) {
      const u = k / 8, u2 = u * u, u3 = u2 * u;
      out.push([0, 1].map(c => 0.5 * (2 * p1[c] + (-p0[c] + p2[c]) * u + (2 * p0[c] - 5 * p1[c] + 4 * p2[c] - p3[c]) * u2 + (-p0[c] + 3 * p1[c] - 3 * p2[c] + p3[c]) * u3)));
    }
  }
  return out;
}

/* Les demi-cercles d'un FLOT : rayon 1,1 NM, un tous les 3 NM le long de chaque segment, du côté gauche du sens des points ;
   chacun est une suite de points (de derrière, par la gauche, à devant) */
function cfFlotBumps(pts) {
  const out = [];
  for (let i = 0; i + 1 < pts.length; i++) {
    const a = pts[i], b = pts[i + 1];
    const kx = Math.cos((a[0] + b[0]) / 2 * CF_RAD) * 111320, ky = 110540;
    const dx = (b[1] - a[1]) * kx, dy = (b[0] - a[0]) * ky;
    const len = Math.hypot(dx, dy);
    if (!(len > 0)) continue;
    const ux = dx / len, uy = dy / len, nx = -uy, ny = ux;
    const nm = len / NM_M, n = Math.floor(nm / 3);
    if (n < 1) continue;
    const first = (nm - 3 * (n - 1)) / 2, r = 1.1 * NM_M;
    for (let j = 0; j < n; j++) {
      const c = (first + 3 * j) * NM_M, cx = ux * c, cy = uy * c, arc = [];
      for (let s = 0; s <= 12; s++) {
        const th = Math.PI - Math.PI * s / 12;
        arc.push([a[0] + (cy + r * (Math.cos(th) * uy + Math.sin(th) * ny)) / ky, a[1] + (cx + r * (Math.cos(th) * ux + Math.sin(th) * nx)) / kx]);
      }
      out.push(arc);
    }
  }
  return out;
}

function cfMean(pts) {
  let la = 0, lo = 0;
  pts.forEach(p => { la += p[0]; lo += p[1]; });
  return [la / pts.length, lo / pts.length];
}

/* Le style commun : contour à la couleur, à lineOpacity, d'au moins 1,5 px ; tirets selon dash ; remplissage (cfFill) à 0,4 × fillOpacity */
function cfReading() { return tapMode === 'read'; }

function cfPathStyle(it, extra) {
  const o = { pane: 'layers', interactive: cfReading(), color: it.color, opacity: typeof it.lineOpacity === 'number' ? it.lineOpacity : 1, weight: Math.max(1.5, it.lineWidth || 2), fill: false,
    lineJoin: 'round', bubblingMouseEvents: false, className: 'cf-obj cf-' + it.type, cfId: it.id, cfType: it.type, cfName: it.name };
  if (it.dash === 'dot') o.dashArray = '2 6'; else if (it.dash === 'dash') o.dashArray = '8 6';
  return Object.assign(o, extra || {});
}
function cfFill(it) { return { fill: true, fillColor: it.color, fillOpacity: CF_FILL_K * it.fillOpacity }; }

function cfTagEl(layer, it) {
  const el = layer.getElement && layer.getElement();
  if (!el) return;
  el.setAttribute('data-cf-id', it.id);
  el.setAttribute('data-cf-type', it.type);
  el.setAttribute('data-cf-name', it.name);
}

function cfBindPopup(layer, it) {
  if (!cfReading()) return;
  layer.bindPopup(() => cfFiche(it), { className: 'cf-popup', maxWidth: 280, minWidth: 150, autoPanPadding: [16, 16] });
}

/* Un objet vectoriel : touchable (fiche) seulement en mode Lire ; sinon il laisse passer le toucher */
function cfAddObj(layer, it) {
  cfBindPopup(layer, it);
  layer.addTo(cfGroup);
  cfTagEl(layer, it);
}

/* Un trait épais et invisible sous un contour mince : le doigt le trouve (un contour sans remplissage ne se touche qu'à sa ligne) */
function cfAddHit(geo, it, circle) {
  if (!cfReading()) return;
  const o = { pane: 'layers', color: '#000000', opacity: 0, weight: 18, fill: false, bubblingMouseEvents: false, className: 'cf-hit', cfHit: true };
  const h = circle ? L.circle(geo.c, Object.assign({ radius: geo.r }, o)) : L.polyline(geo, o);
  cfBindPopup(h, it);
  h.addTo(cfGroup);
}

function cfNameMarker(at, text, color) {
  if (!text) return;
  L.marker(at, { pane: 'layers', interactive: false, keyboard: false, zIndexOffset: 200000,
    icon: L.divIcon({ className: 'cf-name-icon', iconSize: [0, 0], html: '<span class="cf-name" style="color:' + color + '">' + esc(text) + '</span>' }) }).addTo(cfGroup);
}

function cfDrawZone(it) {
  const pts = it.points, mid = pts[Math.floor(pts.length / 2)];
  let nameAt = mid;
  if (it.kind === 'corridor') {
    const poly = L.polygon(cfBand(pts, it.widthNm), cfPathStyle(it, Object.assign({ weight: 1.5 }, cfFill(it))));
    cfAddObj(poly, it);
    L.polyline(pts, { pane: 'layers', color: it.color, opacity: it.lineOpacity, weight: 1.5, dashArray: '6 6', fill: false, interactive: false, className: 'cf-center' }).addTo(cfGroup);
  } else if (it.kind === 'flot') {
    cfAddHit(pts, it, false);
    cfAddObj(L.polyline(pts, cfPathStyle(it)), it);
    L.polyline(cfFlotBumps(pts), { pane: 'layers', color: it.color, opacity: it.lineOpacity, weight: 2.5, fill: false, interactive: false, className: 'cf-bumps' }).addTo(cfGroup);
  } else {
    let ring = pts, closed = it.closed;
    if (it.kind === 'curve' && pts.length >= 3) { ring = cfSpline(pts); closed = true; }
    nameAt = cfMean(pts);
    if (closed) {
      if (!it.filled) cfAddHit(ring.concat([ring[0]]), it, false);
      cfAddObj(L.polygon(ring, cfPathStyle(it, it.filled ? cfFill(it) : {})), it);
    } else {
      cfAddHit(ring, it, false);
      cfAddObj(L.polyline(ring, cfPathStyle(it)), it);
    }
  }
  cfNameMarker(nameAt, it.name, it.color);
}

function cfDrawCircle(it) {
  const c = [it.lat, it.lon], r = it.radiusNm * NM_M;
  if (!it.filled) cfAddHit({ c: c, r: r }, it, true);
  cfAddObj(L.circle(c, cfPathStyle(it, Object.assign({ radius: r }, it.filled ? cfFill(it) : {}))), it);
  if (it.showName) cfNameMarker(c, it.name, it.color);
}

function cfDrawOrbit(it) {
  const g = cfOrbitGeom(it);
  cfAddHit(g.path, it, false);
  cfAddObj(L.polyline(g.path, cfPathStyle(it, { weight: 2.5, dashArray: '10 6' })), it);
  cfNameMarker(g.nameAt, it.name, it.color);
}

function cfDrawBox(it) {
  const g = cfBoxGeom(it);
  cfAddHit(g.corners.concat([g.corners[0]]), it, false);
  cfAddObj(L.polygon(g.corners, cfPathStyle(it, it.filled ? cfFill(it) : {})), it);
  if (it.showGrid && g.grid.length) {
    L.polyline(g.grid, { pane: 'layers', color: it.color, opacity: 1, weight: 1.2, dashArray: '4 4', fill: false, interactive: false, className: 'cf-grid' }).addTo(cfGroup);
  }
  cfNameMarker(g.nameAt, it.name, it.color);
}

/* Le symbole d'un point : 18 px, à la couleur, sur un fond papier */
function cfSymbolSvg(kind, color) {
  let g;
  if (kind === 'target') g = '<circle cx="9" cy="9" r="6"/><path d="M9 1.5V16.5M1.5 9H16.5"/>';
  else if (kind === 'dmpi') g = '<path d="M4 4L14 14M14 4L4 14"/>';
  else if (kind === 'exit') g = '<path d="M9 3L15.5 14.5H2.5Z"/>';
  else if (kind === 'lz') g = '<circle cx="9" cy="9" r="6.5"/><path d="M6.7 5.8V12.2M11.3 5.8V12.2M6.7 9H11.3"/>';
  else g = '<rect x="4.5" y="4.5" width="9" height="9"/>';
  return '<svg width="18" height="18" viewBox="0 0 18 18" aria-hidden="true"><circle cx="9" cy="9" r="9" fill="rgba(240,232,214,.85)"/>' +
    '<g stroke="' + color + '" stroke-width="2" fill="none" stroke-linejoin="miter">' + g + '</g></svg>';
}

function cfDrawPoint(it) {
  const mk = L.marker([it.lat, it.lon], { pane: 'layers', zIndexOffset: 100000, keyboard: false, title: it.name,
    icon: L.divIcon({ className: 'cf-pt-icon', iconSize: [18, 18], iconAnchor: [9, 9], popupAnchor: [0, -11], html: cfSymbolSvg(it.kind, it.color) }) });
  if (cfReading()) cfBindPopup(mk, it);
  else mk.on('click', ev => { L.DomEvent.stop(ev); addFromAirfield(it.lat, it.lon, it.name); });   /* une cible agit comme un aérodrome */
  mk.addTo(cfGroup);
  cfTagEl(mk, it);
  cfPointMarks.push({ mk: mk, name: it.name });
}

/* Un cadre de texte centré sur son point : il ne s'ouvre pas et laisse passer le toucher */
function cfDrawText(it) {
  const fs = Math.max(6, Math.round(it.size / 4));
  const lines = it.text.split(/\r\n|\r|\n/).map(s => s.trim()).join('\n');
  const style = 'background:' + (it.filled ? it.bg : 'transparent') + ';color:' + it.fg + ';border:' + (it.border ? '2px solid ' + it.fg : '0 none') +
    ';font-weight:' + (it.bold ? 700 : 500) + ';font-size:' + fs + 'px';
  const mk = L.marker([it.lat, it.lon], { pane: 'layers', interactive: false, zIndexOffset: 100000, keyboard: false,
    icon: L.divIcon({ className: 'cf-tx-icon', iconSize: [0, 0], html: '<div class="cf-tx" style="' + style + '">' + esc(lines) + '</div>' }) });
  mk.addTo(cfGroup);
  cfTagEl(mk, it);
}

function cfDrawItem(it) {
  if (it.type === 'zone') cfDrawZone(it);
  else if (it.type === 'circle') cfDrawCircle(it);
  else if (it.type === 'orbit') cfDrawOrbit(it);
  else if (it.type === 'box') cfDrawBox(it);
  else if (it.type === 'point') cfDrawPoint(it);
  else if (it.type === 'text') cfDrawText(it);
}

/* Le nom d'un point : dans le DOM du symbole à partir du zoom 11, absent en dessous */
function cfSyncPointNames() {
  if (!map) return;
  const on = map.getZoom() >= CF_NAMES_ZOOM;
  cfPointMarks.forEach(m => {
    const el = m.mk.getElement && m.mk.getElement();
    if (!el) return;
    const has = el.querySelector('.cf-pt-nm');
    if (on && m.name && !has) {
      const s = document.createElement('span');
      s.className = 'cf-pt-nm';
      s.textContent = m.name;
      el.appendChild(s);
    } else if ((!on || !m.name) && has) has.remove();
  });
}

/* Les calques visibles, dans l'ordre de la section (le premier dessous) */
function drawLayers() {
  if (!cfGroup) return;
  cfGroup.clearLayers();
  cfPointMarks = [];
  CF_LAYERS.forEach(l => { if (l.visible) l.items.forEach(cfDrawItem); });
  cfSyncPointNames();
}

/* La fiche d'un objet (popup) : son nom, puis ce que dit son type ; un point offre « → Point de référence » */
function cfFmtNm(v) { return decimal(Number.isInteger(v) ? String(v) : (Math.round(v * 10) / 10).toFixed(1)); }

/* L'altitude d'un cercle ne s'affiche pas quand elle est vide ou vaut le nombre 0 (« 0 », « 0.0 »), espaces mis de côté */
function cfAltShown(v) {
  const s = String(v == null ? '' : v).replace(/\s+/g, '');
  if (s === '') return false;
  return !(/^[+-]?(\d+([.,]\d*)?|[.,]\d+)$/.test(s) && Number(s.replace(',', '.')) === 0);
}

function cfFiche(it) {
  const d = document.createElement('div');
  d.className = 'cf-fiche';
  const line = (cls, txt) => { const e = document.createElement('div'); e.className = cls; e.textContent = txt; d.appendChild(e); };
  const alts = [it.minAlt, it.maxAlt].filter(Boolean).join(' – ');
  if (it.name) line('cf-f-nm', it.name);
  if (it.type === 'circle') {
    line('cf-f-l', t('cf.nm', { w: decimal((Math.round(it.radiusNm * 10) / 10).toFixed(1)) }));
    if (cfAltShown(it.maxAlt)) line('cf-f-l', it.maxAlt);
  } else if (it.type === 'zone') {
    line('cf-f-l', t('cf.k.' + it.kind));
    if (it.kind === 'corridor') line('cf-f-l', t('cf.nm', { w: cfFmtNm(it.widthNm) }));
  } else if (it.type === 'orbit') {
    if (it.kind) line('cf-f-l', it.kind);
    if (alts) line('cf-f-l', alts);
    if (it.frq) line('cf-f-l', t('cf.mhz', { f: it.frq }));
  } else if (it.type === 'box') {
    if (it.kind) line('cf-f-l', it.kind);
    if (alts) line('cf-f-l', alts);
  } else if (it.type === 'point') {
    line('cf-f-l', t('cf.p.' + it.kind));
    line('cf-f-mgrs', toMGRS(it.lat, it.lon));
    if (it.note) line('cf-f-l', it.note);
    const b = document.createElement('button');
    b.type = 'button';
    b.className = 'rt-btn go';
    b.textContent = t('cf.toRef');
    b.addEventListener('click', ev => {
      L.DomEvent.stop(ev);
      const p = addRef(it.lat, it.lon, it.name);       /* le chemin d'aujourd'hui : le refus au-delà de 12 est le sien */
      map.closePopup();
      if (p) showToast(t('toast.refAdded', { name: p.name }));
    });
    d.appendChild(b);
  }
  return d;
}

/* ============= DESSIN : LE QUATRIÈME MODE DU CONTRÔLE (lot rp-v1.6.0) ============= */
/* Un toucher pose, une poignée ajuste. Le mode édite les calques de source.kind « drawn » : les mêmes objets que le modèle dcs-layers-v1, aucun champ
   de plus ; seuls les calques s'enregistrent (route_layers_v1), jamais le mode, le calque actif, l'outil, la sélection ni la couleur. */
const DR_ICONS = {
  pen: "<svg viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2.2\" stroke-linejoin=\"round\"><path d=\"M4 20l1.2-4.6L16.5 4.1a2 2 0 0 1 2.8 0l.6.6a2 2 0 0 1 0 2.8L8.6 18.8z\"/><path d=\"M14.5 6l3.5 3.5\"/></svg>",
  select: "<svg viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linejoin=\"round\"><path d=\"M6 3l12 9-5.2 1.1L15.6 20l-2.6 1.1-2.8-6.9L6 18z\"/></svg>",
  circle: "<svg viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\"><circle cx=\"12\" cy=\"12\" r=\"8.5\"/><circle cx=\"12\" cy=\"12\" r=\"1.6\" fill=\"currentColor\"/><path d=\"M12 12h8.5\" stroke-dasharray=\"2 2\"/></svg>",
  zone: "<svg viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linejoin=\"round\"><path d=\"M4 8l8-5 8 6-3 11H7z\" fill=\"currentColor\" fill-opacity=\".22\"/><rect x=\"2.5\" y=\"6.5\" width=\"3\" height=\"3\" fill=\"currentColor\"/><rect x=\"18.5\" y=\"7.5\" width=\"3\" height=\"3\" fill=\"currentColor\"/></svg>",
  line: "<svg viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linejoin=\"round\"><path d=\"M3 18l6-9 6 5 6-9\"/><rect x=\"7.5\" y=\"7.5\" width=\"3\" height=\"3\" fill=\"currentColor\"/><rect x=\"13.5\" y=\"12.5\" width=\"3\" height=\"3\" fill=\"currentColor\"/></svg>",
  point: "<svg viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\"><circle cx=\"12\" cy=\"12\" r=\"6\"/><path d=\"M12 2v5M12 17v5M2 12h5M17 12h5\"/></svg>",
  text: "<svg viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2.2\"><path d=\"M5 6V4h14v2M12 4v16M9 20h6\"/></svg>",
  props: "<svg viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\"><path d=\"M4 7h10M18 7h2M4 17h4M12 17h8\"/><circle cx=\"16\" cy=\"7\" r=\"2\"/><circle cx=\"10\" cy=\"17\" r=\"2\"/></svg>",
  dup: "<svg viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\"><rect x=\"8\" y=\"8\" width=\"12\" height=\"12\"/><path d=\"M4 16V4h12\"/></svg>",
  del: "<svg viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\"><path d=\"M4 7h16M9 7V4h6v3M6 7l1 13h10l1-13M10 11v6M14 11v6\"/></svg>",
  ok: "<svg viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2.6\"><path d=\"M4 12.5l5 5L20 6.5\"/></svg>",
  move: "<svg viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2.2\"><path d=\"M12 2v20M2 12h20M12 2l-3 3M12 2l3 3M12 22l-3-3M12 22l3-3M2 12l3-3M2 12l3 3M22 12l-3-3M22 12l-3 3\"/></svg>",
  lock: "<svg viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\"><rect x=\"5\" y=\"11\" width=\"14\" height=\"10\"/><path d=\"M8 11V7a4 4 0 0 1 8 0v4\"/></svg>",
  vtx: "<svg viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\"><rect x=\"8\" y=\"8\" width=\"8\" height=\"8\"/><path d=\"M3 3l18 18\"/></svg>",
  orbit: "<svg viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\"><path d=\"M7 7h10a5 5 0 0 1 0 10H7A5 5 0 0 1 7 7z\" stroke-dasharray=\"3.2 2.2\"/><path d=\"M15 4.5l2.5 2.5L15 9.5\" stroke-dasharray=\"none\"/></svg>",
  box: "<svg viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\"><rect x=\"3.5\" y=\"4.5\" width=\"17\" height=\"15\"/><path d=\"M9.2 4.5v15M14.8 4.5v15M3.5 9.5h17M3.5 14.5h17\" stroke-width=\"1\" stroke-dasharray=\"2 1.6\"/></svg>"
};

const DR_COLORS = ['#000000', '#c8102e', '#1f4fa8', '#2e7d32', '#e07b00', '#7b2d8e', '#ffffff'];
const DR_COLOR0 = '#c8102e';   /* la couleur d'un objet neuf, au départ de la session */
const DR_TOOLS = ['select', 'circle', 'zone', 'line', 'point', 'text', 'orbit', 'box'];
const DR_HIT = { circle: 22, path: 22, point: 26, text: 34 };   /* rayons de toucher, en pixels */
const DR_COPY_PX = 24;         /* une copie : 24 px à droite, 24 px en bas, au zoom courant */
const DR_MOVE_TOL = 4;         /* un glisser de poignée commence au-delà de 4 px */
const DR_MIN_NM = 0.5;         /* la largeur d'une orbite, les dimensions d'une boîte : au moins 0,5 NM */
const DR_ROT_PX = 40;          /* la poignée de rotation d'une boîte : 40 px au-delà du milieu du bord avant */
const DR_GRID_MAX = 10;        /* la grille d'une boîte : de 1 à 10 */
const DR_DASH_SVG = {
  solid: '<svg viewBox="0 0 28 10" aria-hidden="true"><path d="M1 5H27" fill="none" stroke="currentColor" stroke-width="2"/></svg>',
  dash: '<svg viewBox="0 0 28 10" aria-hidden="true"><path d="M1 5H27" fill="none" stroke="currentColor" stroke-width="2" stroke-dasharray="5 4"/></svg>',
  dot: '<svg viewBox="0 0 28 10" aria-hidden="true"><path d="M1 5H27" fill="none" stroke="currentColor" stroke-width="2" stroke-dasharray="1.5 3"/></svg>'
};

/* L'état du dessin : en mémoire seulement (ni le mode, ni le calque actif, ni la sélection, ni l'outil, ni la couleur ne s'enregistrent) */
const DR = {
  layerId: null,        /* le calque actif (où l'on dessine) */
  tool: 'select',       /* select · circle · zone · line · point · text · orbit · box */
  build: null,          /* une zone, une ligne, une orbite ou une boîte en cours : { kind, pts: [[lat, lon], …] } */
  draft: null,          /* le brouillon des réglages de l'objet à venir : { n, tool, it, vals, flip } (jamais enregistré) */
  lab: null,            /* l'étiquette d'une poignée de boîte en cours de glisser : { at, text } */
  draftN: 0,
  sel: null,            /* l'objet choisi : { lid, id } */
  vtx: -1,              /* le sommet choisi de l'objet choisi */
  sheet: false,         /* la fiche « Réglages » est ouverte */
  menu: false,          /* le menu des calques est ouvert */
  color: DR_COLOR0,     /* la dernière couleur choisie dans une fiche */
  hs: [],               /* les poignées : { mk, pos, tap, start, move, end } */
  contour: null, preview: [], rlab: null, raf: 0, sheetKey: ''
};

function drOn() { return tapMode === 'draw'; }
function drDrawn() { return CF_LAYERS.filter(l => l.source.kind === 'drawn'); }
function drLayer() { return CF_LAYERS.find(l => l.id === DR.layerId && l.source.kind === 'drawn') || null; }

/* L'objet choisi : { l, it }, sinon null (le calque retiré, masqué ou devenu de lecture seule le défait) */
function drSel() {
  if (!DR.sel) return null;
  const l = CF_LAYERS.find(x => x.id === DR.sel.lid);
  if (!l || l.source.kind !== 'drawn' || !l.visible) return null;
  const it = l.items.find(x => x.id === DR.sel.id);
  return it ? { l: l, it: it } : null;
}

/* Une zone fermée (ou une courbe) est une surface ; les autres zones sont des lignes */
function drIsArea(it) { return it.type === 'zone' && ((it.kind === 'lines' && it.closed === true) || (it.kind === 'curve' && it.points.length >= 3)); }
function drGenre(it) { return it.type === 'zone' ? (drIsArea(it) ? 'zone' : 'line') : it.type; }
function drKindLabel(k) { return k === 'lz' ? t('dr.p.lz') : (k === 'other' ? t('dr.p.other') : t('cf.p.' + k)); }

/* Le tracé d'un objet à contour : { pts, closed } (zone, orbite, boîte) */
function drPath(it) {
  if (it.type === 'zone') {
    if (it.kind === 'corridor') return { pts: cfBand(it.points, it.widthNm), closed: true };          /* un couloir se choisit dans sa bande */
    if (it.kind === 'curve' && it.points.length >= 3) return { pts: cfSpline(it.points), closed: true };
    return { pts: it.points, closed: it.kind === 'lines' && it.closed === true };
  }
  if (it.type === 'orbit') return { pts: cfOrbitGeom(it).path, closed: true };
  if (it.type === 'box') return { pts: cfBoxGeom(it).corners, closed: true };
  return null;
}

/* ---- Toucher : l'objet du calque actif le plus proche ---- */
function drSegDist(p, a, b) {
  const dx = b.x - a.x, dy = b.y - a.y, l2 = dx * dx + dy * dy;
  let u = l2 ? ((p.x - a.x) * dx + (p.y - a.y) * dy) / l2 : 0;
  u = Math.max(0, Math.min(1, u));
  return Math.hypot(p.x - (a.x + u * dx), p.y - (a.y + u * dy));
}

function drInside(p, q) {
  let on = false;
  for (let i = 0, j = q.length - 1; i < q.length; j = i++) {
    if ((q[i].y > p.y) !== (q[j].y > p.y) && p.x < (q[j].x - q[i].x) * (p.y - q[i].y) / (q[j].y - q[i].y) + q[i].x) on = !on;
  }
  return on;
}

/* La distance (px) de p à l'objet s'il est touché, sinon -1 */
function drHit(it, p) {
  if (it.type === 'circle') {
    const c = map.latLngToContainerPoint([it.lat, it.lon]);
    const r = c.distanceTo(map.latLngToContainerPoint(cfDest([it.lat, it.lon], 90, it.radiusNm)));
    const dc = p.distanceTo(c), d = Math.abs(dc - r);
    return (d <= DR_HIT.circle || (it.filled && dc <= r)) ? d : -1;
  }
  if (it.type === 'point' || it.type === 'text') {
    const d = p.distanceTo(map.latLngToContainerPoint([it.lat, it.lon]));
    return d <= DR_HIT[it.type] ? d : -1;
  }
  const g = drPath(it);
  if (!g) return -1;
  const q = g.pts.map(x => map.latLngToContainerPoint(x)), n = q.length;
  let d = Infinity;
  for (let i = 0; i + 1 < n; i++) d = Math.min(d, drSegDist(p, q[i], q[i + 1]));
  if (g.closed && n > 2) d = Math.min(d, drSegDist(p, q[n - 1], q[0]));
  const area = g.closed && (it.type !== 'zone' || it.filled === true || it.kind === 'corridor');
  return (d <= DR_HIT.path || (area && drInside(p, q))) ? d : -1;
}

function drPickAt(p) {
  const l = drLayer();
  let best = null, bd = Infinity;
  if (l && l.visible) l.items.forEach(it => { const d = drHit(it, p); if (d >= 0 && d <= bd) { best = it; bd = d; } });   /* à égalité, le dernier */
  if (best) drSelect(l.id, best.id); else drDeselect();
}

/* ---- Le calque actif ---- */
function drFreeName() {
  const used = {};
  CF_LAYERS.forEach(l => { used[l.name] = true; });
  const base = t('dr.new.layer');
  if (!used[base]) return base;
  let n = 2;
  while (used[t('dr.new.layerN', { n: n })]) n++;
  return t('dr.new.layerN', { n: n });
}

function drMakeLayer(name) {
  const l = { id: cfRandId(), name: name, visible: true, source: { kind: 'drawn', file: '' }, items: [] };
  CF_LAYERS.push(l);
  DR.layerId = l.id;
  showToast(t('dr.t.created', { name: name }));
  return l;
}

/* Le calque où l'on crée : l'actif, sinon un calque « Tracés » neuf ; créer rend le calque visible */
function drEnsureLayer() {
  let l = drLayer();
  if (!l) l = drMakeLayer(drFreeName());
  l.visible = true;
  return l;
}

/* ---- Créer ---- */
function drAdd(it) {
  const l = drEnsureLayer();
  drApplyDraft(it);       /* seuls les réglages changés dans la fiche « à venir » passent à l'objet */
  l.items.push(it);
  persistLayers();
  renderLayers();
  drawLayers();
  DR.tool = 'select';
  DR.build = null;
  DR.draft = null;        /* la fiche, si elle est ouverte, reste ouverte sur l'objet créé */
  drClearPreview();
  drSelect(l.id, it.id);
}

function drLL(ll) { return [r7(ll.lat), r7(ll.lng)]; }

function drNewCircle(ll) {
  return { id: cfRandId(), type: 'circle', name: '', lat: r7(ll.lat), lon: r7(ll.lng), radiusNm: 5, filled: false, color: DR.color, lineOpacity: 1, fillOpacity: 0.5,
    lineWidth: 2, dash: 'solid', maxAlt: '', showName: true };
}

function drNewPoint(ll) {
  const l = drLayer();
  const n = (l ? l.items.filter(i => i.type === 'point').length : 0) + 1;
  return { id: cfRandId(), type: 'point', name: t('dr.new.pt', { n: n }), lat: r7(ll.lat), lon: r7(ll.lng), kind: 'target', note: '', color: DR.color };
}

function drNewText(ll) {
  return { id: cfRandId(), type: 'text', name: '', lat: r7(ll.lat), lon: r7(ll.lng), text: t('dr.new.text'), bg: '#ffffff', fg: '#000000', size: 48, bold: true, border: true, filled: true };
}

function drNewZone(pts, area) {
  return { id: cfRandId(), type: 'zone', name: '', kind: 'lines', points: pts.map(p => [p[0], p[1]]), closed: area, filled: area, widthNm: 5, color: DR.color,
    lineOpacity: 1, fillOpacity: 0.5, lineWidth: 2, dash: 'solid' };
}

function dr1(v) { return Math.round(v * 10) / 10; }
/* Un cap vrai au dixième, dans [0 ; 360[ */
function drBrg(v) { const n = Math.round(v * 10) % 3600; return (n < 0 ? n + 3600 : n) / 10; }

/* L'orbite : le premier toucher est l'entrée (lat2, lon2), le second la sortie (lat, lon) ; brg = cap vrai de l'entrée vers la sortie */
function drNewOrbit(a, b) {
  const brg = legCalc({ lat: a[0], lon: a[1] }, { lat: b[0], lon: b[1] }).brg;
  return { id: cfRandId(), type: 'orbit', name: '', lat: b[0], lon: b[1], lat2: a[0], lon2: a[1], brg: Math.round(brg * 100) / 100, widthNm: 10, clockwise: true,
    kind: '', minAlt: '', maxAlt: '', frq: '', color: DR.color };
}

/* La boîte : le premier toucher est le début de l'axe (milieu du bord arrière), le second sa fin ; widthNm = lengthNm */
function drNewBox(a, b) {
  const v = legCalc({ lat: a[0], lon: a[1] }, { lat: b[0], lon: b[1] });
  const len = Math.max(DR_MIN_NM, dr1(v.km / NM_KM));
  return { id: cfRandId(), type: 'box', name: '', lat: a[0], lon: a[1], brg: drBrg(v.brg), lengthNm: len, widthNm: len, gridH: 3, gridV: 3, showGrid: true,
    kind: '', minAlt: '', maxAlt: '', color: DR.color, lineWidth: 2, filled: false, fillOpacity: 0.5 };
}

/* Terminer la zone ou la ligne en cours (quiet : sans toast) ; false si elle n'a pas assez de sommets (une orbite ou une boîte ne se termine pas : deux touchers) */
function drFinish(quiet) {
  const b = DR.build;
  if (!b || b.kind === 'orbit' || b.kind === 'box') return false;
  const area = b.kind === 'zone';
  if (b.pts.length < (area ? 3 : 2)) { if (!quiet) showToast(t(area ? 'dr.t.zone' : 'dr.t.line')); return false; }
  drAdd(drNewZone(b.pts, area));
  return true;
}

/* Abandonner la création en cours, ou quitter un outil de pose : retour à Choisir, rien n'est écrit */
function drCancel() {
  DR.build = null;
  DR.tool = 'select';
  DR.draft = null;        /* ✕, Échap et le retour à Choisir ferment la fiche et oublient le brouillon */
  DR.sheet = false;
  drClearPreview();
  drBuildHandles();
  drSyncUi();
}

function drSetTool(x) {
  if (DR_TOOLS.indexOf(x) === -1 || x === DR.tool) return;
  const sheet = DR.sheet;
  if (DR.build) {
    if (drFinish(true)) { DR.sel = null; DR.vtx = -1; DR.sheet = false; }   /* assez de sommets : la zone se termine, rien n'est choisi */
    DR.build = null;
  }
  DR.tool = x;
  DR.menu = false;
  DR.draft = x === 'select' ? null : drNewDraft(x);                         /* un outil de création : le brouillon de l'objet à venir */
  DR.sheet = x === 'select' ? false : sheet;                                /* changer d'outil, fiche ouverte : elle se rouvre sur le brouillon du nouvel outil */
  DR.sheetKey = '';
  DR.build = (x === 'zone' || x === 'line' || x === 'orbit' || x === 'box') ? { kind: x, pts: [] } : null;
  drClearPreview();
  drBuildHandles();
  drContour();
  drSyncUi();
}

/* Un toucher sur la carte, en mode Dessin */
function drMapClick(ev) {
  if (SR.open) { srClose(); return; }
  if (DR.menu) { DR.menu = false; drSyncUi(); return; }
  const ll = ev.latlng;
  const tool = DR.tool;
  if (tool === 'select') { drPickAt(ev.containerPoint); return; }
  if (tool === 'circle') { drAdd(drNewCircle(ll)); return; }
  if (tool === 'point') { drAdd(drNewPoint(ll)); return; }
  if (tool === 'text') {
    drAdd(drNewText(ll));
    DR.sheet = true;
    drSyncUi();
    const f = $('dr-f-text');
    if (f) { f.focus(); f.select(); }
    return;
  }
  if (DR.build) {
    DR.build.pts.push(drLL(ll));
    const b = DR.build;
    if (b.kind === 'orbit' && b.pts.length === 2) { drAdd(drNewOrbit(b.pts[0], b.pts[1])); return; }     /* l'entrée, puis la sortie */
    if (b.kind === 'box' && b.pts.length === 2) { drAdd(drNewBox(b.pts[0], b.pts[1])); return; }       /* le début de l'axe, puis sa fin */
    drBuildRefresh();
  }
}

function drBuildRefresh() {
  drBuildPreview();
  drBuildHandles();
  drSyncUi();
}

/* ---- Le tracé en cours ---- */
function drClearPreview() {
  DR.preview.forEach(x => { if (map) map.removeLayer(x); });
  DR.preview = [];
}

function drBuildPreview() {
  drClearPreview();
  const b = DR.build;
  if (!b || !drOn()) return;
  if (b.kind !== 'zone' && b.kind !== 'line') return;
  const dash = DR.draft ? DR.draft.it.dash : 'solid';                         /* la couleur et le trait du brouillon */
  const st = { pane: 'drawedit', color: DR.color, weight: 2.5, opacity: 1, interactive: false, lineJoin: 'round', lineCap: 'round' };
  if (dash === 'dot') st.dashArray = '2 6'; else if (dash === 'dash') st.dashArray = '8 6';
  if (b.pts.length >= 2) DR.preview.push(L.polyline(b.pts, st).addTo(map));
  if (b.kind === 'zone' && b.pts.length >= 3) {
    DR.preview.push(L.polyline([b.pts[b.pts.length - 1], b.pts[0]], Object.assign({}, st, { dashArray: '6 6', opacity: 0.7 })).addTo(map));
  }
}

/* ---- Sélection ---- */
function drSelect(lid, id) {
  DR.sel = { lid: lid, id: id };
  DR.vtx = -1;
  DR.menu = false;
  drBuildHandles();
  drContour();
  drSyncUi();
}

function drDeselect() {
  DR.sel = null;
  DR.vtx = -1;
  DR.sheet = false;
  drBuildHandles();
  drContour();
  drSyncUi();
}

/* Le contour de la sélection : la forme de l'objet, #c0892a, 7 px, 0,45, non touchable */
function drContour() {
  if (DR.contour) { map.removeLayer(DR.contour); DR.contour = null; }
  const s = drSel();
  if (!s || !drOn() || DR.build) return;
  const it = s.it, st = { pane: 'drawedit', color: '#c0892a', weight: 7, opacity: 0.45, fill: false, interactive: false, lineJoin: 'round', lineCap: 'round' };
  if (it.type === 'circle') DR.contour = L.circle([it.lat, it.lon], Object.assign({ radius: it.radiusNm * NM_M }, st));
  else {
    const g = drPath(it);
    if (g) DR.contour = g.closed ? L.polygon(g.pts, st) : L.polyline(g.pts, st);
  }
  if (DR.contour) DR.contour.addTo(map);
}

/* L'étiquette d'une poignée de mesure, à gauche d'elle : le rayon d'un cercle, la largeur d'une orbite (dès que l'orbite est choisie), la mesure
   de la poignée de boîte tirée (DR.lab) */
function drLabInfo(it) {
  if (it.type === 'circle') return { at: cfDest([it.lat, it.lon], 90, it.radiusNm), text: t('cf.nm', { w: cfFmtNm(it.radiusNm) }) };
  if (it.type === 'orbit') return { at: cfOrbitGeom(it).nameAt, text: t('cf.nm', { w: cfFmtNm(it.widthNm) }) };
  if (it.type === 'box' && DR.lab) return { at: DR.lab.at(), text: DR.lab.text() };
  return null;
}

function drRlab() {
  const s = drSel(), info = (s && drOn() && !DR.build) ? drLabInfo(s.it) : null;
  if (!info) {
    if (DR.rlab) { map.removeLayer(DR.rlab); DR.rlab = null; }
    return;
  }
  if (!DR.rlab) {
    DR.rlab = L.marker(info.at, { pane: 'drawedit', interactive: false, keyboard: false, zIndexOffset: 300,
      icon: L.divIcon({ className: 'dr-rlab-icon', iconSize: [0, 0], html: '<span class="dr-rlab"></span>' }) }).addTo(map);
  }
  DR.rlab.setLatLng(info.at);
  const el = DR.rlab.getElement();
  if (el && el.firstChild) el.firstChild.textContent = info.text;
}

/* ---- Les poignées : 44 px de cible, 16 px visibles ---- */
function drMk(cls, pos, cb) {
  const mid = cls.indexOf('mid') !== -1;
  const inner = mid ? '+' : (cls.indexOf('mv') !== -1 ? DR_ICONS.move : '');
  const mk = L.marker(pos(), { pane: 'drawedit', keyboard: false, bubblingMouseEvents: false, zIndexOffset: mid ? 0 : 100,
    icon: L.divIcon({ className: 'dr-h ' + cls, iconSize: [44, 44], iconAnchor: [22, 22], html: '<i>' + inner + '</i>' }) }).addTo(map);
  const h = Object.assign({ mk: mk, pos: pos }, cb || {});
  drBind(h);
  DR.hs.push(h);
  return h;
}

/* Un toucher (sans glisser) appelle h.tap ; un glisser appelle h.start, h.move(delta en px, évènement) puis h.end ; la carte ne bouge pas */
function drBind(h) {
  const el = h.mk.getElement();
  if (!el) return;
  el.style.touchAction = 'none';
  L.DomEvent.disableClickPropagation(el);       /* ni mousedown ni touchstart n'atteignent la carte ; un clic sur la poignée n'est pas un clic de carte */
  let st = null;
  el.addEventListener('pointerdown', e => {
    if (e.pointerType === 'mouse' && e.button !== 0) return;
    st = { id: e.pointerId, p0: map.mouseEventToContainerPoint(e), moved: false };
    try { el.setPointerCapture(e.pointerId); } catch (x) { /* ignore */ }
  });
  el.addEventListener('pointermove', e => {
    if (!st || e.pointerId !== st.id) return;
    const d = map.mouseEventToContainerPoint(e).subtract(st.p0);
    if (!st.moved) {
      if (Math.hypot(d.x, d.y) < DR_MOVE_TOL) return;
      st.moved = true;
      if (h.start) h.start();
    }
    if (h.move) h.move(d, e);
  });
  const stop = e => {
    if (!st || e.pointerId !== st.id) return;
    const was = st;
    st = null;
    try { el.releasePointerCapture(e.pointerId); } catch (x) { /* ignore */ }
    if (was.moved) { if (h.end) h.end(); }
    else if (e.type === 'pointerup' && h.tap) h.tap();
  };
  el.addEventListener('pointerup', stop);
  el.addEventListener('pointercancel', stop);
}

/* Déplacer des couples (lat, lon) d'un objet du même vecteur, en pixels du zoom courant */
function drMoveCb(it, pairs, post) {
  let base = null;
  return {
    start: () => { const z = map.getZoom(); base = pairs.map(f => map.project(L.latLng(it[f[0]], it[f[1]]), z)); },
    move: d => {
      const z = map.getZoom();
      pairs.forEach((f, i) => { const ll = map.unproject(base[i].add(d), z); it[f[0]] = r7(ll.lat); it[f[1]] = r7(ll.lng); });
      if (post) post();
      drLive();
    },
    end: () => drCommit()
  };
}

/* Déplacer tous les sommets d'une zone ou d'une ligne */
function drMovePts(it) {
  let base = null;
  return {
    start: () => { const z = map.getZoom(); base = it.points.map(p => map.project(L.latLng(p[0], p[1]), z)); },
    move: d => {
      const z = map.getZoom();
      it.points = base.map(b => drLL(map.unproject(b.add(d), z)));
      drLive();
    },
    end: () => drCommit()
  };
}

/* Déplacer un seul sommet (zone ou ligne de l'objet choisi, ou tracé en cours) */
function drVertexCb(pts, k, live, done) {
  let base = null;
  return {
    start: () => { base = map.project(L.latLng(pts()[k][0], pts()[k][1]), map.getZoom()); },
    move: d => { pts()[k] = drLL(map.unproject(base.add(d), map.getZoom())); live(); },
    end: done
  };
}

function drMid(it, a, b) {
  const z = map.getZoom();
  return map.unproject(map.project(L.latLng(it.points[a][0], it.points[a][1]), z).add(map.project(L.latLng(it.points[b][0], it.points[b][1]), z)).divideBy(2), z);
}

/* ---- Les poignées de l'orbite ---- */
/* Le cap d'une orbite : de l'entrée (lat2, lon2) vers la sortie (lat, lon) */
function drOrbitBrg(it) {
  it.brg = Math.round(legCalc({ lat: it.lat2, lon: it.lon2 }, { lat: it.lat, lon: it.lon }).brg * 100) / 100;
}

function drOrbitHandles(it) {
  drMk('v', () => L.latLng(it.lat2, it.lon2), drMoveCb(it, [['lat2', 'lon2']], () => drOrbitBrg(it)));       /* l'entrée : seule, brg se recalcule */
  drMk('v', () => L.latLng(it.lat, it.lon), drMoveCb(it, [['lat', 'lon']], () => drOrbitBrg(it)));           /* la sortie */
  drMk('r', () => { const a = cfOrbitGeom(it).nameAt; return L.latLng(a[0], a[1]); }, {
    move: (d, e) => {
      /* la largeur : la distance du doigt à la droite entrée → sortie ; le côté du doigt décide du virage (à droite de l'axe : clockwise) */
      const F = map.mouseEventToLatLng(e), en = { lat: it.lat2, lon: it.lon2 };
      const ax = legCalc(en, { lat: it.lat, lon: it.lon }), fg = legCalc(en, { lat: F.lat, lon: F.lng });
      const xt = fg.km * Math.sin((fg.brg - ax.brg) * CF_RAD) / NM_KM;
      if (xt > 0) it.clockwise = true; else if (xt < 0) it.clockwise = false;
      it.widthNm = Math.max(DR_MIN_NM, dr1(Math.abs(xt)));
      drLive();
    },
    end: () => drCommit()
  });
  drMk('mv', () => L.latLng((it.lat + it.lat2) / 2, (it.lon + it.lon2) / 2), drMoveCb(it, [['lat', 'lon'], ['lat2', 'lon2']]));   /* les deux extrémités ensemble */
  drRlab();
}

/* ---- Les poignées de la boîte ---- */
function drBoxMid(a, b) { return L.latLng((a[0] + b[0]) / 2, (a[1] + b[1]) / 2); }
const DR_BOX_EDGE = {      /* le milieu de chaque bord, des coins [NO, NE, SE, SO] */
  left: g => drBoxMid(g.corners[0], g.corners[1]),
  front: g => drBoxMid(g.corners[1], g.corners[2]),
  right: g => drBoxMid(g.corners[2], g.corners[3]),
  back: g => drBoxMid(g.corners[3], g.corners[0])
};

/* Un bord se tire seul, le long de sa normale ; le bord opposé reste en place. Tout se mesure contre l'état du début du glisser, sur la boîte telle
   que cfBoxGeom la dessine (ses coins se calculent de proche en proche : mesurer au doigt par un grand cercle ferait dériver une boîte de 30 NM de
   ~0,1 NM). Deux inconnues, la dimension p et un décalage s du début de l'axe ; deux équations : le milieu du bord tiré suit le doigt (déplacement
   en pixels de la poignée), le milieu du bord opposé reste où il était. Un doigt immobile ou parallèle au bord ne change donc rien. */
function drBoxEdgeCb(it, side, h) {
  const opp = { front: 'back', back: 'front', left: 'right', right: 'left' }[side];
  const isLen = side === 'front' || side === 'back';
  /* [∂(bord tiré)/∂p, ∂(bord tiré)/∂s], [∂(bord opposé)/∂p, ∂(bord opposé)/∂s], dans la coordonnée du bord (le long de l'axe, ou en travers) */
  const J = { front: [1, 1, 0, 1], back: [0, 1, 1, 1], right: [0.5, 1, -0.5, 1], left: [-0.5, -1, 0.5, -1] }[side];
  const det = J[0] * J[3] - J[1] * J[2];
  const dir = { front: 0, back: 0, right: 90, left: -90 }[side];       /* le sens du décalage s, relativement à brg */
  let B = null, M0 = null, coord = null, o0 = 0;
  const build = (p, s) => {
    const st = cfDest([B.lat, B.lon], B.brg + dir, s);
    return { lat: st[0], lon: st[1], brg: B.brg, lengthNm: isLen ? p : B.len, widthNm: isLen ? B.wid : p, gridH: 1, gridV: 1 };
  };
  const mid = (box, sd) => DR_BOX_EDGE[sd](cfBoxGeom(box));
  return {
    start: () => {
      B = { lat: it.lat, lon: it.lon, brg: it.brg, len: it.lengthNm, wid: it.widthNm };
      const kd = NAV_R_KM * 1000 * CF_RAD, kx = Math.cos(B.lat * CF_RAD) * kd, sb = Math.sin(B.brg * CF_RAD), cb = Math.cos(B.brg * CF_RAD);
      coord = ll => {       /* le repère plan local, en mètres : le long de l'axe, ou en travers (à droite) */
        const x = (ll.lng - B.lon) * kx, y = (ll.lat - B.lat) * kd;
        return isLen ? x * sb + y * cb : x * cb - y * sb;
      };
      const base = build(isLen ? B.len : B.wid, 0);
      M0 = mid(base, side);
      o0 = coord(mid(base, opp));
      DR.lab = { at: () => h.pos(), text: () => t('cf.nm', { w: cfFmtNm(isLen ? it.lengthNm : it.widthNm) }) };
    },
    move: d => {
      const z = map.getZoom();
      const tc = coord(map.unproject(map.project(M0, z).add(d), z));
      let p = isLen ? B.len : B.wid, s = 0;
      for (let k = 0; k < 6; k++) {
        const box = build(p, s);
        const rd = (coord(mid(box, side)) - tc) / NM_M, ro = (coord(mid(box, opp)) - o0) / NM_M;
        p = Math.max(DR_MIN_NM, p + (-rd * J[3] + ro * J[1]) / det);
        s += (-ro * J[0] + rd * J[2]) / det;
      }
      p = Math.max(DR_MIN_NM, dr1(p));
      for (let k = 0; k < 3; k++) s -= (coord(mid(build(p, s), opp)) - o0) / NM_M / J[3];     /* le bord opposé, remis où il était */
      const nb = build(p, s);
      if (p === (isLen ? B.len : B.wid) && Math.abs(s) < 1e-6) { it.lat = B.lat; it.lon = B.lon; }
      else { it.lat = r7(nb.lat); it.lon = r7(nb.lon); }
      if (isLen) it.lengthNm = p; else it.widthNm = p;
      drLive();
    },
    end: () => drCommit()
  };
}

/* Un angle se tire avec le coin opposé immobile, brg inchangé. Même méthode que les bords : tout se mesure contre l'état du début du glisser, dans le repère
   plan local de la boîte (le long de l'axe a, en travers c), puis le coin opposé est remis exactement où il était sur la boîte telle que cfBoxGeom la dessine. */
function drBoxCornerCb(it, k, h) {
  const sa = (k === 1 || k === 2) ? 1 : -1, sc = (k === 2 || k === 3) ? 1 : -1, opp = (k + 2) % 4;      /* sa : coin avant (+) ou arrière ; sc : côté droit (+) ou gauche */
  let B = null, kd = 0, kx = 0, sb = 0, cb = 0, C0 = null, O0 = null, oa = 0, oc = 0;
  const xy = ll => { const a = Array.isArray(ll) ? ll : [ll.lat, ll.lng]; return [(a[1] - B.lon) * kx, (a[0] - B.lat) * kd]; };
  const ac = p => [p[0] * sb + p[1] * cb, p[0] * cb - p[1] * sb];
  return {
    start: () => {
      B = { lat: it.lat, lon: it.lon, brg: it.brg, len: it.lengthNm, wid: it.widthNm };
      kd = NAV_R_KM * 1000 * CF_RAD; kx = Math.cos(B.lat * CF_RAD) * kd; sb = Math.sin(B.brg * CF_RAD); cb = Math.cos(B.brg * CF_RAD);
      const g = cfBoxGeom(it).corners;
      C0 = L.latLng(g[k]); O0 = xy(g[opp]); [oa, oc] = ac(O0);
      DR.lab = { at: () => h.pos(), text: () => t('dr.lab.box', { l: cfFmtNm(it.lengthNm), w: cfFmtNm(it.widthNm) }) };
    },
    move: d => {
      const z = map.getZoom(), T = map.project(C0, z).add(d);
      /* le coin opposé remis où il était : le début de l'axe se déduit des dimensions (le milieu du bord arrière) */
      const place = (len, wid) => {
        const a = sa > 0 ? oa : oa - len * NM_M, c = oc + sc * wid * NM_M / 2;
        let lat = B.lat + (a * cb - c * sb) / kd, lon = B.lon + (a * sb + c * cb) / kx;
        for (let n = 0; n < 3; n++) {
          const o = xy(cfBoxGeom({ lat: lat, lon: lon, brg: B.brg, lengthNm: len, widthNm: wid, gridH: 1, gridV: 1 }).corners[opp]);
          lat -= (o[1] - O0[1]) / kd; lon -= (o[0] - O0[0]) / kx;
        }
        return { lat: lat, lon: lon, brg: B.brg, lengthNm: len, widthNm: wid, gridH: 1, gridV: 1 };
      };
      /* les dimensions qui posent le coin tiré sous le doigt, sur la boîte telle que cfBoxGeom la dessine (la largeur d'une boîte n'est pas la même en
         degrés au nord et au sud : un repère plan unique se tromperait de ~0,4 % sur 20 NM) */
      const f = ac(xy(map.unproject(T, z)));
      let len = Math.max(DR_MIN_NM, sa * (f[0] - oa) / NM_M), wid = Math.max(DR_MIN_NM, sc * (f[1] - oc) / NM_M);
      for (let n = 0; n < 5; n++) {
        const q = cfBoxGeom(place(len, wid)).corners.map(c => map.project(L.latLng(c), z));
        const e = T.subtract(q[k]);
        const ua = q[1].subtract(q[0]), uc = q[2].subtract(q[1]), la = Math.hypot(ua.x, ua.y) || 1, lc = Math.hypot(uc.x, uc.y) || 1;
        len = Math.max(DR_MIN_NM, len + sa * (e.x * ua.x + e.y * ua.y) / la / (la / len));
        wid = Math.max(DR_MIN_NM, wid + sc * (e.x * uc.x + e.y * uc.y) / lc / (lc / wid));
      }
      len = Math.max(DR_MIN_NM, dr1(len)); wid = Math.max(DR_MIN_NM, dr1(wid));
      if (len === B.len && wid === B.wid) { it.lat = B.lat; it.lon = B.lon; }
      else { const nb = place(len, wid); it.lat = r7(nb.lat); it.lon = r7(nb.lon); }
      it.lengthNm = len; it.widthNm = wid;
      drLive();
    },
    end: () => drCommit()
  };
}

/* La poignée de rotation : 40 px au-delà du milieu du bord avant, dans l'axe (à l'écran) */
function drBoxRotPos(it) {
  const g = cfBoxGeom(it), c = cfMean(g.corners), f = DR_BOX_EDGE.front(g);
  const pc = map.latLngToContainerPoint(c), pf = map.latLngToContainerPoint(L.latLng(f));
  let dx = pf.x - pc.x, dy = pf.y - pc.y;
  const m = Math.hypot(dx, dy);
  if (m < 0.5) { dx = Math.sin(it.brg * CF_RAD); dy = -Math.cos(it.brg * CF_RAD); } else { dx /= m; dy /= m; }
  return map.containerPointToLatLng(L.point(pf.x + dx * DR_ROT_PX, pf.y + dy * DR_ROT_PX));
}

/* La boîte tourne autour de son centre (la moyenne de ses quatre coins) : le début de l'axe se replace pour que le centre ne bouge pas */
function drBoxPivot(it, brg, c0) {
  it.brg = brg;
  const st = cfDest(c0, brg + 180, it.lengthNm / 2);
  it.lat = st[0]; it.lon = st[1];
  for (let k = 0; k < 3; k++) {
    const m = cfMean(cfBoxGeom(it).corners);
    it.lat += c0[0] - m[0]; it.lon += c0[1] - m[1];
  }
  it.lat = r7(it.lat); it.lon = r7(it.lon);
}

function drBoxHandles(it) {
  ['left', 'front', 'right', 'back'].forEach(side => {
    const along = side === 'front' || side === 'back';
    const h = drMk('v edge', () => DR_BOX_EDGE[side](cfBoxGeom(it)), {});
    const cb = drBoxEdgeCb(it, side, h);
    h.start = cb.start; h.move = cb.move; h.end = cb.end;
    h.upd = () => {                     /* la barrette suit le sens de son bord, et le garde pendant une rotation */
      const el = h.mk.getElement(), i = el && el.querySelector('i');
      if (i) i.style.transform = 'rotate(' + (along ? it.brg : it.brg + 90) + 'deg)';
    };
    h.upd();
  });
  for (let k = 0; k < 4; k++) {
    const h = drMk('v corner', () => L.latLng(cfBoxGeom(it).corners[k]), {});
    const cb = drBoxCornerCb(it, k, h);
    h.start = cb.start; h.move = cb.move; h.end = cb.end;
    h.upd = () => {       /* au-dessus des bords ; en dessous de 88 px de côté à l'écran, le bord l'emporte */
      const q = cfBoxGeom(it).corners.map(c => map.latLngToContainerPoint(L.latLng(c)));
      h.mk.setZIndexOffset(Math.min(q[0].distanceTo(q[1]), q[1].distanceTo(q[2])) > 88 ? 3000 : -3000);
    };
    h.upd();
  }
  let c0 = null;
  const rot = drMk('r rot', () => drBoxRotPos(it), {
    start: () => {
      c0 = cfMean(cfBoxGeom(it).corners);
      DR.lab = { at: () => rot.pos(), text: () => fmtHdg(it.brg) + '°' };
    },
    move: (d, e) => {
      const F = map.mouseEventToLatLng(e);
      drBoxPivot(it, drBrg(legCalc({ lat: c0[0], lon: c0[1] }, { lat: F.lat, lon: F.lng }).brg), c0);
      drLive();
    },
    end: () => drCommit()
  });
  rot.mk.setZIndexOffset(6000);
  drMk('mv', () => { const m = cfMean(cfBoxGeom(it).corners); return L.latLng(m[0], m[1]); }, drMoveCb(it, [['lat', 'lon']])).mk.setZIndexOffset(9000);
}

/* Refaire les poignées de ce qu'on édite : le tracé en cours, ou l'objet choisi ; keep : la poignée en cours de glisser, qui devient le sommet keepIdx */
function drBuildHandles(keep, keepIdx) {
  DR.hs.forEach(h => { if (h !== keep) map.removeLayer(h.mk); });
  DR.hs = keep ? [keep] : [];
  if (DR.rlab && !keep) { map.removeLayer(DR.rlab); DR.rlab = null; }
  if (!drOn()) return;
  const b = DR.build;
  if (b) {
    b.pts.forEach((p, k) => {
      const first = k === 0 && b.kind === 'zone' && b.pts.length >= 3;
      const h = drMk('v' + (first ? ' first' : ''), () => L.latLng(b.pts[k][0], b.pts[k][1]),
        drVertexCb(() => b.pts, k, () => { drBuildPreview(); drPlaceHandles(); }, () => { drBuildPreview(); drBuildHandles(); }));
      if (first) h.tap = () => drFinish(false);
    });
    return;
  }
  const s = drSel();
  if (!s) return;
  const it = s.it;
  if (it.type === 'circle') {
    drMk('v', () => L.latLng(it.lat, it.lon), drMoveCb(it, [['lat', 'lon']]));
    drMk('r', () => { const a = cfDest([it.lat, it.lon], 90, it.radiusNm); return L.latLng(a[0], a[1]); }, {
      move: (d, e) => {
        const ll = map.mouseEventToLatLng(e);
        const nm = legCalc({ lat: it.lat, lon: it.lon }, { lat: ll.lat, lon: ll.lng }).km / NM_KM;
        it.radiusNm = Math.max(0.1, Math.round(nm * 10) / 10);
        drLive();
      },
      end: () => drCommit()
    });
    drRlab();
  } else if (it.type === 'zone') {
    const n = it.points.length, area = drIsArea(it);
    for (let k = 0; k < n; k++) {
      if (keep && k === keepIdx) continue;
      const h = drMk('v' + (DR.vtx === k ? ' on' : ''), () => L.latLng(it.points[k][0], it.points[k][1]), drVertexCb(() => it.points, k, drLive, drCommit));
      h.tap = () => { DR.vtx = DR.vtx === k ? -1 : k; drBuildHandles(); drSyncUi(); };
    }
    const segs = area ? n : n - 1;
    for (let k = 0; k < segs; k++) {
      const ia = k, ib = (k + 1) % n, at = k + 1;
      const h = drMk('mid', () => drMid(it, ia, ib), {});
      h.tap = () => {
        const ll = h.pos();
        it.points.splice(at, 0, drLL(ll));
        DR.vtx = at;
        drChanged();
      };
      h.start = () => {
        const ll = h.pos();
        it.points.splice(at, 0, drLL(ll));
        if (DR.vtx >= at) DR.vtx++;
        const el = h.mk.getElement();
        el.classList.remove('mid');
        el.classList.add('v');
        const i = el.querySelector('i');
        if (i) i.textContent = '';
        h.pos = () => L.latLng(it.points[at][0], it.points[at][1]);
        h.tap = null;
        const cb = drVertexCb(() => it.points, at, drLive, drCommit);
        h.start = cb.start; h.move = cb.move; h.end = cb.end;
        cb.start();
        drBuildHandles(h, at);
      };
    }
    drMk('mv', () => { const m = cfMean(it.points); return L.latLng(m[0], m[1]); }, drMovePts(it));
  } else if (it.type === 'orbit') {
    drOrbitHandles(it);
  } else if (it.type === 'box') {
    drBoxHandles(it);
  } else {
    drMk('v', () => L.latLng(it.lat, it.lon), drMoveCb(it, [['lat', 'lon']]));     /* point, texte */
  }
}

function drPlaceHandles() {
  DR.hs.forEach(h => { if (h.pos) h.mk.setLatLng(h.pos()); if (h.upd) h.upd(); });
}

/* Pendant un glisser : l'objet, le contour, les poignées et l'étiquette suivent (une fois par image) ; rien ne s'enregistre */
function drLive() {
  if (DR.raf) return;
  DR.raf = requestAnimationFrame(() => { DR.raf = 0; drLiveNow(); });
}

function drLiveNow() {
  if (DR.raf) { cancelAnimationFrame(DR.raf); DR.raf = 0; }
  drawLayers();
  drContour();
  drPlaceHandles();
  drRlab();
  drUpdateDesc();
}

/* La fin d'un glisser : la seule écriture de route_layers_v1 */
function drCommit() {
  DR.lab = null;
  drLiveNow();
  persistLayers();
  drBuildHandles();
  if (DR.sheet) drRenderSheet(true);      /* la fiche suit ce que le glisser a changé (virage…) */
  drSyncUi();
}

/* Un changement discret (insertion d'un sommet, réglage) : écrire, redessiner, refaire les poignées */
function drChanged() {
  persistLayers();
  drawLayers();
  drContour();
  drBuildHandles();
  drSyncUi();
}

/* ---- La barre, le message, le menu ---- */
function drDesc(it) {
  const nm = hasText(it.name) ? it.name : '';
  const join = x => nm ? nm + ' · ' + x : x;
  if (it.type === 'circle') return join(t('cf.nm', { w: cfFmtNm(it.radiusNm) }));
  if (it.type === 'zone') {
    if (it.kind === 'flot') return join(t('cf.k.flot'));
    if (it.kind === 'corridor') return join(t('dr.d.corr', { w: cfFmtNm(it.widthNm) }));
    return join(t(cfOne(it.points.length) ? 'dr.nv.1' : 'dr.nv.n', { n: it.points.length }));
  }
  if (it.type === 'orbit') return join(t('cf.nm', { w: cfFmtNm(it.widthNm) }) + ' · ' + t(it.clockwise ? 'dr.turn.r' : 'dr.turn.l'));
  if (it.type === 'box') return join(cfFmtNm(it.lengthNm) + ' × ' + t('cf.nm', { w: cfFmtNm(it.widthNm) }) + ' · ' + it.gridH + ' × ' + it.gridV);
  if (it.type === 'point') return join(drKindLabel(it.kind));
  if (it.type === 'text') return it.text.replace(/\s*[\r\n]+\s*/g, ' ').trim();
  return nm || t('dr.g.' + drGenre(it));
}

function drUpdateDesc() {
  const s = drSel(), el = document.querySelector('#dr-bar .dr-sel span');
  if (s && el) el.textContent = drDesc(s.it);
  /* la fiche ouverte suit le rayon, la largeur, la longueur, sauf si on y écrit */
  if (s) [['dr-f-radius', 'radiusNm'], ['dr-f-width', 'widthNm'], ['dr-f-length', 'lengthNm']].forEach(f => {
    const r = $(f[0]);
    if (r && s.it[f[1]] != null && document.activeElement !== r) r.value = decimal(String(s.it[f[1]]));
  });
}

function drToolBtn(attrs, icon, label, cls) {
  return '<button type="button" class="dr-tool' + (cls ? ' ' + cls : '') + '" ' + attrs + ' title="' + esc(label) + '" aria-label="' + esc(label) + '">' +
    DR_ICONS[icon] + '<i>' + esc(label) + '</i></button>';
}

function drRenderBar() {
  const bar = $('dr-bar'), s = drSel();
  bar.className = 'dr-bar' + (s ? ' selmode' : '');
  bar.setAttribute('aria-label', t('tap.draw'));
  let h = '';
  if (!s) {
    const l = drLayer();
    h += '<button type="button" class="dr-chip' + (DR.menu ? ' open' : '') + '" data-dr="chip" aria-haspopup="true" aria-expanded="' + (DR.menu ? 'true' : 'false') + '">' +
      '<small>' + esc(t('dr.chip')) + '</small><span>' + esc(l ? l.name : t('dr.chip.new')) + '</span></button>';
    h += '<div class="dr-tools" role="group">' + DR_TOOLS.map(k =>
      drToolBtn('data-dr="tool" data-tool="' + k + '" aria-pressed="' + (DR.tool === k ? 'true' : 'false') + '"', k, t('dr.tool.' + k), DR.tool === k ? 'on' : '')).join('') + '</div>';
  } else {
    const it = s.it;
    h += '<div class="dr-sel"><small>' + esc(t('dr.g.' + drGenre(it)) + (DR.vtx >= 0 ? ' · ' + t('dr.vtx.n', { n: DR.vtx + 1 }) : '')) + '</small><span>' + esc(drDesc(it)) + '</span></div>';
    h += '<div class="dr-tools" role="group">' +
      (DR.vtx >= 0 ? drToolBtn('data-dr="vtx"', 'vtx', t('dr.b.vtx')) : '') +
      drToolBtn('data-dr="props" aria-pressed="' + (DR.sheet ? 'true' : 'false') + '"', 'props', t('dr.b.props'), DR.sheet ? 'on' : '') +
      drToolBtn('data-dr="dup"', 'dup', t('dr.b.copy')) +
      drToolBtn('data-dr="del"', 'del', t('dr.b.del'), 'danger') +
      drToolBtn('data-dr="ok"', 'ok', t('dr.b.ok')) + '</div>';
  }
  bar.innerHTML = h;
}

function drRenderHint() {
  const hint = $('dr-hint'), msg = $('dr-msg'), acts = $('dr-acts');
  if (drSel() || DR.menu) { hint.hidden = true; return; }
  hint.hidden = false;
  const tool = DR.tool, b = DR.build;
  let m = '', a = '';
  if (tool === 'select') m = esc(t('dr.msg.select'));
  else if (tool === 'circle') m = esc(t('dr.msg.circle'));
  else if (tool === 'point') m = esc(t('dr.msg.point'));
  else if (tool === 'text') m = esc(t('dr.msg.text'));
  else if (tool === 'orbit' || tool === 'box') m = esc(t('dr.msg.' + tool + (b && b.pts.length ? '2' : '')));
  else {
    const n = b ? b.pts.length : 0;
    if (!n) m = esc(t('dr.msg.zone'));
    else m = '<b>' + esc(t(cfOne(n) ? 'dr.nv.1' : 'dr.nv.n', { n: n })) + '</b> ' + esc(t('dr.build.add')) + (tool === 'zone' && n >= 3 ? ' ' + esc(t('dr.build.close')) : '');
    a += '<button type="button" class="tb-btn" data-dr="undo" title="' + esc(t('dr.undo')) + '" aria-label="' + esc(t('dr.undo')) + '">↶</button>' +
      '<button type="button" class="tb-btn go" data-dr="finish">' + esc(t('dr.finish')) + '</button>';
  }
  if (tool !== 'select') {
    /* les réglages de l'objet à venir : le bouton avant ↶ / Terminer / ✕ */
    a = '<button type="button" class="tb-btn mq-props' + (DR.sheet ? ' on' : '') + '" data-dr="props" aria-pressed="' + (DR.sheet ? 'true' : 'false') + '" title="' + esc(t('dr.b.props')) +
      '" aria-label="' + esc(t('dr.b.props')) + '">' + DR_ICONS.props + '</button>' + a;
  }
  if (tool !== 'select') a += '<button type="button" class="tb-btn" data-dr="cancel" title="' + esc(t('dr.cancel')) + '" aria-label="' + esc(t('dr.cancel')) + '">✕</button>';
  msg.innerHTML = m;
  acts.innerHTML = a;
  acts.hidden = !a;
}

function drRenderPop() {
  const pop = $('dr-pop');
  if (!DR.menu || !drOn()) { pop.hidden = true; return; }
  pop.hidden = false;
  $('dr-ly-list').innerHTML = CF_LAYERS.map(l => {
    if (l.source.kind === 'drawn') {
      return '<div class="dr-ly' + (l.id === DR.layerId ? ' on' : '') + '" data-dr="layer" data-id="' + esc(l.id) + '" role="button" tabindex="0">' +
        '<span class="dot"></span><span class="nm">' + esc(l.name) + '</span><span class="n">' + l.items.length + '</span></div>';
    }
    return '<div class="dr-ly ro" data-id="' + esc(l.id) + '" title="' + esc(t('dr.menu.ro')) + '"><span class="lock">' + DR_ICONS.lock + '</span>' +
      '<span class="nm">' + esc(l.name) + '</span><span class="n">' + esc(t('dr.cf')) + '</span>' +
      '<button type="button" class="tb-btn" data-dr="copylayer" data-id="' + esc(l.id) + '">' + esc(t('dr.menu.copy')) + '</button></div>';
  }).join('');
}

/* ---- La fiche « Réglages » : celle de l'objet choisi, ou (draft) celle de l'objet à venir, aux mêmes champs ---- */
function drSheetHtml(it, draft) {
  const g = drGenre(it);
  const f = (label, id, body, cls) => '<div class="dr-f' + (cls ? ' ' + cls : '') + '"><label' + (id ? ' for="' + id + '"' : '') + '>' + esc(label) + '</label>' + body + '</div>';
  const col = it.type === 'text' ? it.fg : it.color;
  const seg = (field, items) => '<div class="dr-seg" role="group">' + items.map(x =>
    '<button type="button" class="tb-btn' + (x.on ? ' on' : '') + '" data-f="' + field + '" data-v="' + x.v + '" aria-pressed="' + (x.on ? 'true' : 'false') + '"' +
    (x.label ? ' title="' + esc(x.label) + '" aria-label="' + esc(x.label) + '"' : '') + '>' + x.html + '</button>').join('') + '</div>';
  const num = (id, fld, v) => '<input type="text" id="' + id + '" data-f="' + fld + '" inputmode="decimal" autocomplete="off" value="' + esc(decimal(String(v))) + '">';
  const txt = (id, fld, v, ph) => '<input type="text" id="' + id + '" data-f="' + fld + '" autocomplete="off" spellcheck="false" placeholder="' + esc(t(ph)) + '" value="' + esc(v) + '">';
  const step = (fld, v) => '<div class="mq-step" role="group">' +
    '<button type="button" class="tb-btn" data-f="' + fld + '" data-v="' + Math.max(1, v - 1) + '" title="' + esc(t('dr.step.dec')) + '" aria-label="' + esc(t('dr.step.dec')) + '">−</button>' +
    '<span>' + v + '</span>' +
    '<button type="button" class="tb-btn" data-f="' + fld + '" data-v="' + Math.min(DR_GRID_MAX, v + 1) + '" title="' + esc(t('dr.step.inc')) + '" aria-label="' + esc(t('dr.step.inc')) + '">+</button></div>';
  const yn = (field, on, yes, no) => seg(field, [{ v: '1', on: !!on, html: esc(t(yes)) }, { v: '0', on: !on, html: esc(t(no)) }]);   /* le « oui » d'abord */
  const alts = () => '<div class="dr-row2">' + f(t('dr.f.minAlt'), 'dr-f-minalt', txt('dr-f-minalt', 'minAlt', it.minAlt, 'dr.f.minAlt.ph')) +
    f(t('dr.f.alt'), 'dr-f-alt', txt('dr-f-alt', 'maxAlt', it.maxAlt, 'dr.f.maxAlt.ph')) + '</div>';
  let h = '<div class="sh-head"><b>' + esc(t(draft ? 'dr.sheet.draft' : 'dr.sheet', { g: t('dr.g.' + g) })) + '</b><button type="button" class="sh-x" data-dr="props" title="' + esc(t('dr.f.close')) +
    '" aria-label="' + esc(t('dr.f.close')) + '">×</button></div>';
  if (it.type === 'text') h += f(t('dr.f.text'), 'dr-f-text', '<input type="text" id="dr-f-text" data-f="text" autocomplete="off" spellcheck="false" value="' + esc(it.text) + '">');
  else h += f(t('dr.f.name'), 'dr-f-name', '<input type="text" id="dr-f-name" data-f="name" autocomplete="off" spellcheck="false" placeholder="' + esc(t('dr.f.unnamed')) + '" value="' + esc(it.name) + '">');
  h += f(t('dr.f.color'), '', '<div class="dr-sw" role="group">' + DR_COLORS.map(c =>
    '<button type="button" data-f="color" data-v="' + c + '" style="background:' + c + '" aria-label="' + c + '" aria-pressed="' + (col === c ? 'true' : 'false') + '"' + (col === c ? ' class="on"' : '') + '></button>').join('') + '</div>');
  if (it.type === 'circle') {
    h += '<div class="dr-row2">' + f(t('dr.f.radius'), 'dr-f-radius', num('dr-f-radius', 'radius', it.radiusNm)) +
      f(t('dr.f.alt'), 'dr-f-alt', '<input type="text" id="dr-f-alt" data-f="maxAlt" autocomplete="off" spellcheck="false" placeholder="' + esc(t('dr.f.alt.ph')) + '" value="' + esc(it.maxAlt) + '">') + '</div>';
  }
  if (it.type === 'orbit') {
    h += '<div class="dr-row2">' + f(t('dr.f.width'), 'dr-f-width', num('dr-f-width', 'width', it.widthNm)) +
      f(t('dr.f.turn'), '', yn('turn', it.clockwise, 'dr.turn.r', 'dr.turn.l'), 'mq-turn') + '</div>';
    h += '<div class="dr-row2">' + f(t('dr.f.mission'), 'dr-f-mission', txt('dr-f-mission', 'mission', it.kind, 'dr.f.mission.ph')) +
      f(t('dr.f.frq'), 'dr-f-frq', txt('dr-f-frq', 'frq', it.frq, 'dr.f.frq.ph')) + '</div>';
    h += alts();
  }
  if (it.type === 'box') {
    h += '<div class="dr-row2">' + f(t('dr.f.length'), 'dr-f-length', num('dr-f-length', 'length', it.lengthNm)) +
      f(t('dr.f.width'), 'dr-f-width', num('dr-f-width', 'width', it.widthNm)) + '</div>';
    h += '<div class="dr-row2">' + f(t('dr.f.gridH'), '', step('gridH', it.gridH)) + f(t('dr.f.gridV'), '', step('gridV', it.gridV)) + '</div>';
    h += '<div class="dr-row2">' + f(t('dr.f.grid'), '', yn('showGrid', it.showGrid, 'dr.grid.show', 'dr.grid.hide'), 'mq-gshow') +
      f(t('dr.f.fill'), '', seg('fill', [{ v: '0', on: !it.filled, html: esc(t('dr.f.none')) }, { v: '1', on: !!it.filled, html: esc(t('dr.f.filled')) }])) + '</div>';
    h += alts();
  }
  if (it.type === 'circle' || it.type === 'zone') {
    const dash = ['solid', 'dash', 'dot'].map(v => ({ v: v, on: it.dash === v, html: DR_DASH_SVG[v], label: t('dr.dash.' + v) }));
    let row = f(t('dr.f.line'), '', seg('dash', dash));
    if (g !== 'line') row += f(t('dr.f.fill'), '', seg('fill', [{ v: '0', on: !it.filled, html: esc(t('dr.f.none')) }, { v: '1', on: !!it.filled, html: esc(t('dr.f.filled')) }]), 'dr-f-in');
    h += '<div class="dr-row2">' + row + '</div>';
  }
  if (it.type === 'zone' && g === 'zone') {
    h += f(t('dr.f.shape'), '', seg('shape', [{ v: 'lines', on: it.kind !== 'curve', html: esc(t('dr.shape.lines')) }, { v: 'curve', on: it.kind === 'curve', html: esc(t('dr.shape.curve')) }]));
  }
  if (it.type === 'zone' && g === 'line') {
    const lt = it.kind === 'flot' ? 'flot' : (it.kind === 'corridor' ? 'corridor' : 'lines');
    let row = f(t('dr.f.type'), '', seg('ltype', [{ v: 'lines', on: lt === 'lines', html: esc(t('dr.lt.line')) }, { v: 'flot', on: lt === 'flot', html: esc(t('dr.lt.flot')) },
      { v: 'corridor', on: lt === 'corridor', html: esc(t('dr.lt.corridor')) }]));
    if (lt === 'corridor') row += f(t('dr.f.width'), 'dr-f-width', num('dr-f-width', 'width', it.widthNm), 'mq-cw');
    if (lt === 'flot') {
      const on = draft && DR.draft && DR.draft.flip;
      row += f(t('dr.f.enemy'), '', '<button type="button" class="tb-btn mq-flip' + (on ? ' on' : '') + '" data-f="flip" data-v="1"' + (draft ? ' aria-pressed="' + (on ? 'true' : 'false') + '"' : '') +
        '><span aria-hidden="true">⇄</span> ' + esc(t('dr.f.flip')) + '</button>', 'mq-cw');
    }
    h += '<div class="dr-row2">' + row + '</div>';
  }
  if (it.type === 'point') {
    h += f(t('dr.f.type'), 'dr-f-kind', '<select id="dr-f-kind" data-f="kind">' + CF_POINT_KINDS.map(k =>
      '<option value="' + k + '"' + (it.kind === k ? ' selected' : '') + '>' + esc(drKindLabel(k)) + '</option>').join('') + '</select>');
  }
  if (it.type === 'text') {
    h += f(t('dr.f.frame'), '', seg('frame', [{ v: '0', on: !it.filled, html: esc(t('dr.f.noBg')) }, { v: '1', on: !!it.filled, html: esc(t('dr.f.whiteBg')) }]));
  }
  return h;
}

/* Les listes de la fiche passent par la liste du module (tbmAttach) : le <select> reste, masqué ; la fiche se reconstruit, le
   rattachement se refait sur le <select> neuf, et une liste ouverte sur l'ancien se ferme avant qu'il ne disparaisse */
const DR_LIST_LABELS = { kind: 'dr.f.type' };
function drSheetListClose() {
  const sh = $('dr-sheet');
  if (TBM.cur && sh && sh.contains(TBM.cur.sel)) tbmClose(false);
}
function drSheetLists() {
  $('dr-sheet').querySelectorAll('select[data-f]').forEach(sel => tbmAttach(sel, () => t(DR_LIST_LABELS[sel.dataset.f] || 'dr.f.type'), 'sheet'));
}

/* La fiche s'ouvre sur l'objet choisi (outil Choisir), ou, avec un outil de création, sur le brouillon de l'objet à venir : { it, draft } ou null */
function drSheetTarget() {
  const s = drSel();
  if (DR.tool === 'select') return s ? { it: s.it, draft: false } : null;
  return DR.draft ? { it: DR.draft.it, draft: true } : null;
}

/* La fiche « à venir » se pose d'après le message, mesuré : son bas à 6 px au-dessus du message, sa hauteur bornée à la place qui reste (carte + 10 px),
   160 px au moins (elle couvre alors le haut de la carte, jamais le message). La fiche d'un objet choisi garde sa place de feuille du bas. */
const DR_SHEET_GAP = 6, DR_SHEET_TOP = 10, DR_SHEET_MIN = 160;
function drPlaceSheet() {
  const sh = $('dr-sheet'), hint = $('dr-hint'), wrap = sh && sh.offsetParent;
  if (!sh || !hint) return;
  if (sh.hidden || !sh.classList.contains('mq-draft') || hint.hidden || !wrap) { sh.style.bottom = ''; sh.style.maxHeight = ''; return; }
  const w = wrap.getBoundingClientRect(), h = hint.getBoundingClientRect();
  const top = w.top + wrap.clientTop, base = h.top - DR_SHEET_GAP;
  sh.style.bottom = Math.round((top + wrap.clientHeight) - base) + 'px';
  sh.style.maxHeight = Math.max(DR_SHEET_MIN, Math.floor(base - (top + DR_SHEET_TOP))) + 'px';
}
let drSheetRo = null;
function drWatchSheet() {
  if (drSheetRo || !window.ResizeObserver) return;
  drSheetRo = new ResizeObserver(() => drPlaceSheet());
  drSheetRo.observe($('dr-hint')); drSheetRo.observe($('dr-sheet')); drSheetRo.observe($('dr-sheet').parentNode);
}

function drRenderSheet(force) {
  const sh = $('dr-sheet'), tg = drSheetTarget();
  if (!DR.sheet || !tg) { drSheetListClose(); sh.hidden = true; sh.classList.remove('mq-draft'); DR.sheetKey = ''; drPlaceSheet(); return; }
  const key = (tg.draft ? 'draft/' + DR.draft.n : DR.sel.lid + '/' + DR.sel.id) + '/' + CURRENT_LANG;
  sh.hidden = false;
  sh.classList.toggle('mq-draft', tg.draft);
  if (key !== DR.sheetKey || force) { drSheetListClose(); DR.sheetKey = key; sh.innerHTML = drSheetHtml(tg.it, tg.draft); drSheetLists(); }
  drWatchSheet();
  drPlaceSheet();
}

/* Tout ce que montre le mode, remis d'aplomb */
function drSyncUi() {
  if (!drOn() || !$('dr-ui')) return;
  const s = drSel();
  if (DR.sel && !s) { DR.sel = null; DR.vtx = -1; DR.sheet = false; }
  if (DR.sheet && !drSheetTarget()) DR.sheet = false;
  if (DR.vtx >= 0 && (!s || !s.it.points || DR.vtx >= s.it.points.length)) DR.vtx = -1;
  drRenderBar();
  drRenderHint();
  drRenderPop();
  drRenderSheet(false);
  drPlaceSheet();
}

/* Les champs numériques de la fiche : leur champ de l'objet */
const DR_NUM_F = { radius: 'radiusNm', length: 'lengthNm', width: 'widthNm' };

/* Un réglage posé sur un objet (le choisi, un neuf, ou le brouillon) ; false s'il ne le concerne pas ou s'il est illisible */
function drSetField(it, f, v) {
  const ty = it.type, ob = ty === 'orbit' || ty === 'box';
  if (f === 'name') { if (ty === 'text') return false; it.name = v; }
  else if (f === 'text') { if (ty !== 'text') return false; it.text = v; }
  else if (f === 'maxAlt') { if (ty !== 'circle' && !ob) return false; it.maxAlt = v; }
  else if (f === 'minAlt') { if (!ob) return false; it.minAlt = v; }
  else if (f === 'frq') { if (ty !== 'orbit') return false; it.frq = v; }
  else if (f === 'mission') { if (!ob) return false; it.kind = v; }
  else if (f === 'radius' || f === 'length' || f === 'width') {
    const n = readNum(v);
    if (n == null || !(n > 0)) return false;
    if (f === 'radius' && ty === 'circle') it.radiusNm = Math.min(n, 100000);
    else if (f === 'length' && ty === 'box') it.lengthNm = Math.min(n, 100000);
    else if (f === 'width' && (ty === 'box' || ty === 'orbit' || ty === 'zone')) it.widthNm = Math.min(n, ty === 'box' ? 100000 : 1000);
    else return false;
  } else if (f === 'color') { if (ty === 'text') it.fg = v; else it.color = v; DR.color = v; }
  else if (f === 'dash') it.dash = v;
  else if (f === 'fill' || f === 'frame') it.filled = v === '1';
  else if (f === 'kind') { if (CF_POINT_KINDS.indexOf(v) !== -1) it.kind = v; }
  else if (f === 'turn') { if (ty !== 'orbit') return false; it.clockwise = v === '1'; }
  else if (f === 'showGrid') { if (ty !== 'box') return false; it.showGrid = v === '1'; }
  else if (f === 'gridH' || f === 'gridV') {
    if (ty !== 'box') return false;
    it[f] = Math.max(1, Math.min(DR_GRID_MAX, Math.round(Number(v)) || 1));
  } else if (f === 'shape') {
    if (ty !== 'zone') return false;
    it.kind = v === 'curve' ? 'curve' : 'lines';
    if (it.kind === 'lines') it.closed = true;
  } else if (f === 'ltype') {
    if (ty !== 'zone') return false;
    it.kind = v === 'flot' ? 'flot' : (v === 'corridor' ? 'corridor' : 'lines');
    it.closed = false;
    it.filled = it.kind === 'corridor';
    if (it.kind === 'corridor' && !(it.widthNm > 0)) it.widthNm = 5;
  } else return false;
  return true;
}

/* Un réglage de la fiche : sur un objet il s'applique et s'enregistre aussitôt ; sur le brouillon il se retient (rien ne s'enregistre) */
function drApply(tg, f, v) {
  const it = tg.it;
  if (f === 'flip') { drFlip(tg); return; }
  if (!drSetField(it, f, v)) return;
  if (tg.draft) {
    DR.draft.vals[f] = v;
    drBuildPreview();
    return;
  }
  persistLayers();
  drawLayers();
  drContour();
  drPlaceHandles();
  drRlab();
  drRenderBar();
}

/* ⇄ Inverser : l'ordre des sommets d'un FLOT se renverse (les festons changent de côté) ; sur le brouillon, au moment de la création */
function drFlip(tg) {
  if (tg.draft) { DR.draft.flip = !DR.draft.flip; return; }
  if (tg.it.type !== 'zone') return;
  tg.it.points = tg.it.points.slice().reverse();
  DR.vtx = -1;
  drChanged();
}

/* À la création : seuls les réglages changés dans la fiche « à venir » passent à l'objet ; la géométrie vient des touchers */
function drNewDraft(tool) {
  const z = { lat: 0, lng: 0 }, p = [[0, 0], [0, 0], [0, 0]];
  let it;
  if (tool === 'circle') it = drNewCircle(z);
  else if (tool === 'zone') it = drNewZone(p, true);
  else if (tool === 'line') it = drNewZone(p, false);
  else if (tool === 'point') { it = drNewPoint(z); it.name = ''; }
  else if (tool === 'text') it = drNewText(z);
  else if (tool === 'orbit') it = drNewOrbit([0, 0], [0, 0.1]);
  else it = drNewBox([0, 0], [0, 0.1]);
  return { n: ++DR.draftN, tool: tool, it: it, vals: {}, flip: false };
}

function drApplyDraft(it) {
  const d = DR.draft;
  if (!d) return;
  Object.keys(d.vals).forEach(f => {
    if (f === 'length') return;                                          /* la longueur d'une boîte vient des touchers */
    if (f === 'name' && it.type === 'point' && !hasText(d.vals[f])) return;      /* un point garde « PT {n} » sauf nom saisi */
    drSetField(it, f, d.vals[f]);
  });
  if (d.flip && it.type === 'zone') it.points = it.points.slice().reverse();
}

function drCopy() {
  const s = drSel();
  if (!s) return;
  const z = map.getZoom(), c = JSON.parse(JSON.stringify(s.it));
  const sh = (la, lo) => drLL(map.unproject(map.project(L.latLng(la, lo), z).add([DR_COPY_PX, DR_COPY_PX]), z));
  c.id = cfRandId();
  if (c.type === 'zone') c.points = c.points.map(p => sh(p[0], p[1]));
  else {
    const a = sh(c.lat, c.lon);
    c.lat = a[0]; c.lon = a[1];
    if (c.type === 'orbit') { const b = sh(c.lat2, c.lon2); c.lat2 = b[0]; c.lon2 = b[1]; }
  }
  s.l.items.push(c);
  persistLayers();
  renderLayers();
  drawLayers();
  drSelect(s.l.id, c.id);
}

function drDelete() {
  const s = drSel();
  if (!s) return;
  const name = hasText(s.it.name) ? s.it.name : t('dr.g.' + drGenre(s.it));
  if (!confirm(t('dr.confirmDel', { name: name }))) return;
  s.l.items = s.l.items.filter(x => x !== s.it);
  persistLayers();
  renderLayers();
  drawLayers();
  drDeselect();
}

/* « Sommet » : retire le sommet choisi, sauf sous 3 sommets (zone) ou 2 (ligne) */
function drRemoveVertex() {
  const s = drSel();
  if (!s || s.it.type !== 'zone' || DR.vtx < 0) return;
  const min = drIsArea(s.it) ? 3 : 2;
  if (s.it.points.length <= min) { showToast(t('dr.t.min', { n: min })); return; }
  s.it.points.splice(DR.vtx, 1);
  DR.vtx = -1;
  drChanged();
}

/* Les calques : « + Calque » et « Copier pour dessiner » */
function drNewLayer() {
  const inp = $('dr-ly-name');
  const name = inp.value.trim().slice(0, 40) || drFreeName();
  drMakeLayer(name);
  inp.value = '';
  DR.menu = false;
  persistLayers();
  renderLayers();
  drawLayers();
  drSyncUi();
}

function drCopyLayer(src) {
  if (!src) return;
  const name = t('dr.menu.copyName', { name: src.name });
  const l = { id: cfRandId(), name: name, visible: true, source: { kind: 'drawn', file: '' },
    items: src.items.map(it => Object.assign(JSON.parse(JSON.stringify(it)), { id: cfRandId() })) };
  CF_LAYERS.push(l);
  DR.layerId = l.id;
  DR.menu = false;
  persistLayers();
  renderLayers();
  drawLayers();
  showToast(t('dr.t.created', { name: name }));
  drSyncUi();
}

/* Les calques ont changé (visibilité, retrait, import) : le calque actif et la sélection se revalident */
function drAfterLayers() {
  if (!drOn()) return;
  if (DR.layerId && !drLayer()) DR.layerId = null;
  if (DR.sel && !drSel()) { DR.sel = null; DR.vtx = -1; DR.sheet = false; }
  drBuildHandles();
  drContour();
  drSyncUi();
}

function drEnter() {
  DR.draft = null; DR.lab = null;
  DR.tool = 'select'; DR.build = null; DR.sel = null; DR.vtx = -1; DR.sheet = false; DR.menu = false;
  if (!drLayer()) { const l = drDrawn()[0]; DR.layerId = l ? l.id : null; }
  map.getContainer().classList.add('rp-drawing');
  $('dr-ui').hidden = false;
  drSyncUi();
}

function drExit() {
  if (DR.build) { drFinish(true); DR.build = null; }       /* assez de sommets : elle se termine ; sinon elle s'abandonne sans rien écrire */
  DR.tool = 'select'; DR.sel = null; DR.vtx = -1; DR.sheet = false; DR.menu = false; DR.draft = null; DR.lab = null;
  drClearPreview();
  drBuildHandles();
  drContour();
  drRlab();
  map.getContainer().classList.remove('rp-drawing');
  drSheetListClose();
  $('dr-ui').hidden = true;
  $('dr-sheet').hidden = true;
  $('dr-pop').hidden = true;
}

function drOnZoom() {
  if (!drOn()) return;
  drBuildPreview();
  drBuildHandles();
  drContour();
}

function drOnClick(ev) {
  const b = ev.target.closest ? ev.target.closest('[data-dr]') : null;
  if (!b) return;
  const a = b.dataset.dr;
  if (a === 'chip') { DR.menu = !DR.menu; drSyncUi(); }
  else if (a === 'tool') drSetTool(b.dataset.tool);
  else if (a === 'layer') { DR.layerId = b.dataset.id; DR.menu = false; drSyncUi(); }
  else if (a === 'copylayer') drCopyLayer(CF_LAYERS.find(l => l.id === b.dataset.id));
  else if (a === 'newlayer') drNewLayer();
  else if (a === 'undo') { if (DR.build) { DR.build.pts.pop(); drBuildRefresh(); } }
  else if (a === 'finish') drFinish(false);
  else if (a === 'cancel') drCancel();
  else if (a === 'vtx') drRemoveVertex();
  else if (a === 'props') { if (drSheetTarget()) { DR.sheet = !DR.sheet; DR.sheetKey = ''; drSyncUi(); } }
  else if (a === 'dup') drCopy();
  else if (a === 'del') drDelete();
  else if (a === 'ok') drDeselect();
}

function drOnSheet(ev) {
  const tg = drSheetTarget();
  if (!tg) return;
  if (ev.type === 'click') {
    const b = ev.target.closest ? ev.target.closest('button[data-f]') : null;
    if (!b) return;
    drApply(tg, b.dataset.f, b.dataset.v);
    drRenderSheet(true);
  } else {
    const el = ev.target;
    if (!el || !el.dataset || !el.dataset.f) return;
    if (ev.type === 'change' && DR_NUM_F[el.dataset.f]) { el.value = decimal(String(tg.it[DR_NUM_F[el.dataset.f]])); return; }
    if (ev.type === 'input' && el.tagName === 'SELECT') return;
    if (ev.type === 'change' && el.tagName !== 'SELECT') return;
    drApply(tg, el.dataset.f, el.value);
  }
}

function drInit() {
  const ui = $('dr-ui'), sh = $('dr-sheet');
  /* Rien de ce qui est touché dans la barre, le message, le menu ou la fiche n'atteint la carte */
  [ui, sh].forEach(el => {
    ['click', 'dblclick', 'mousedown', 'mouseup', 'touchstart', 'pointerdown', 'contextmenu', 'wheel'].forEach(n =>
      el.addEventListener(n, e => { e.stopPropagation(); }, { passive: n === 'wheel' || n === 'touchstart' }));
  });
  ui.addEventListener('click', drOnClick);
  sh.addEventListener('click', ev => { if (ev.target.closest && ev.target.closest('[data-dr]')) drOnClick(ev); else drOnSheet(ev); });
  sh.addEventListener('input', drOnSheet);
  sh.addEventListener('change', drOnSheet);
  $('dr-ly-name').addEventListener('keydown', ev => {
    ev.stopPropagation();
    if (ev.key === 'Enter') { ev.preventDefault(); drNewLayer(); }
  });
  $('dr-pop').addEventListener('keydown', ev => {
    const row = ev.target.closest ? ev.target.closest('.dr-ly[data-dr="layer"]') : null;
    if (row && (ev.key === 'Enter' || ev.key === ' ')) { ev.preventDefault(); DR.layerId = row.dataset.id; DR.menu = false; drSyncUi(); }
  });
  map.on('zoomend', drOnZoom);
  document.addEventListener('keydown', ev => {
    if (ev.key !== 'Escape' || !drOn() || SR.open || RT_MODALS.some(rtVisible)) return;
    if (DR.menu) { DR.menu = false; drSyncUi(); }
    else if (DR.build || DR.tool !== 'select') drCancel();
    else if (DR.sheet && drSel()) { DR.sheet = false; drSyncUi(); }
    else if (drSel()) drDeselect();
  });
}

/* ============= LA SÉPARATION CARTE / PANNEAU (portrait) ============= */
const KEY_SPLIT = 'rp_split_v1';
const SP_MIN = 220, SP_MIN_F = 0.25, SP_MAX_F = 0.85, SP_STEP = 40, SP_DBL_MS = 350;
const SP = { el: null, wrap: null, mq: null, h: null, drag: null, raf: 0, want: 0, last: 0 };

function spBounds() {
  const H = $('app').getBoundingClientRect().height;
  return [Math.max(SP_MIN, SP_MIN_F * H), SP_MAX_F * H];
}
function spClamp(h) { const b = spBounds(); return Math.max(b[0], Math.min(b[1], h)); }
function spHeight() { return SP.wrap.getBoundingClientRect().height; }

function spResize() { if (map && mapCreated) map.invalidateSize({ animate: false, pan: false }); }

function spApply(h) {
  SP.wrap.style.height = h + 'px';
  SP.wrap.style.minHeight = '0';
  spResize();
}

function spClear() {
  if (!SP.wrap.style.height && !SP.wrap.style.minHeight) return;
  SP.wrap.style.height = '';
  SP.wrap.style.minHeight = '';
  spResize();
}

function spSave() { try { localStorage.setItem(KEY_SPLIT, String(Math.round(SP.h))); } catch (e) { /* stockage indisponible */ } }
function spForget() { try { localStorage.removeItem(KEY_SPLIT); } catch (e) { /* stockage indisponible */ } }

/* En portrait : la hauteur retenue, bornée ; en paysage : celle de la base */
function spSync() {
  if (!SP.el) return;
  if (SP.mq.matches && SP.h != null) spApply(spClamp(SP.h));
  else spClear();
}

function spSet(h) {
  SP.h = Math.round(spClamp(h));
  spApply(SP.h);
  spSave();
}

function spReset() {
  SP.h = null;
  spClear();
  spForget();
}

function spInit() {
  SP.el = $('rp-split');
  SP.wrap = document.querySelector('.mapwrap');
  if (!SP.el || !SP.wrap) return;
  SP.mq = window.matchMedia(PORTRAIT_FIXED_MQ);
  try {
    const raw = localStorage.getItem(KEY_SPLIT);
    const n = raw == null ? NaN : Number(raw);
    if (isFinite(n) && n > 0) SP.h = n;
  } catch (e) { /* stockage indisponible */ }
  const flush = () => {
    if (SP.raf) { cancelAnimationFrame(SP.raf); SP.raf = 0; }
    if (SP.drag) spApply(SP.want);
  };
  SP.el.addEventListener('pointerdown', e => {
    if (e.pointerType === 'mouse' && e.button !== 0) return;
    SP.drag = { id: e.pointerId, y0: e.clientY, h0: spHeight(), moved: false };
    SP.want = SP.drag.h0;
    try { SP.el.setPointerCapture(e.pointerId); } catch (x) { /* ignore */ }
    SP.el.classList.add('on');
  });
  SP.el.addEventListener('pointermove', e => {
    const d = SP.drag;
    if (!d || e.pointerId !== d.id) return;
    const dy = e.clientY - d.y0;
    if (!d.moved && Math.abs(dy) < 3) return;
    d.moved = true;
    SP.want = Math.round(spClamp(d.h0 + dy));
    if (!SP.raf) SP.raf = requestAnimationFrame(() => { SP.raf = 0; if (SP.drag) spApply(SP.want); });      /* au plus une fois par image */
  });
  const up = e => {
    const d = SP.drag;
    if (!d || e.pointerId !== d.id) return;
    flush();
    SP.drag = null;
    SP.el.classList.remove('on');
    try { SP.el.releasePointerCapture(e.pointerId); } catch (x) { /* ignore */ }
    if (d.moved) { SP.h = SP.want; spSave(); SP.last = 0; return; }
    if (e.type !== 'pointerup') return;
    const now = performance.now();
    if (SP.last && now - SP.last <= SP_DBL_MS) { SP.last = 0; spReset(); }      /* deux touchers sans glisser : la hauteur d'origine */
    else SP.last = now;
  };
  SP.el.addEventListener('pointerup', up);
  SP.el.addEventListener('pointercancel', up);
  SP.el.addEventListener('keydown', e => {
    if (e.key !== 'ArrowUp' && e.key !== 'ArrowDown') return;
    e.preventDefault();
    spSet(spHeight() + (e.key === 'ArrowDown' ? SP_STEP : -SP_STEP));
  });
  const onChange = () => spSync();
  if (SP.mq.addEventListener) SP.mq.addEventListener('change', onChange); else if (SP.mq.addListener) SP.mq.addListener(onChange);
  window.addEventListener('resize', onChange);
  spSync();
}

/* ============= PANNEAU ============= */
function renderPts() {
  const dflt = speedDisp(S.groundSpeed);
  $('pts').innerHTML = S.points.map((p, i) =>
    '<div class="pt-row pts' + (i === sel ? ' sel' : '') + '" data-i="' + i + '"><button type="button" class="pt-num" data-act="select">' + i + '</button>' +
    '<input class="in" data-k="name" type="text" autocomplete="off" spellcheck="false" value="' + esc(p.name) + '">' +
    '<input class="in" data-k="alt" type="text" inputmode="numeric" autocomplete="off" value="' + altValue(p.alt) + '">' +
    (i === 0 ? '<input class="in" data-k="gs" type="text" disabled tabindex="-1" aria-label="' + esc(t(S.units.distance === 'nm' ? 'th.spd.kt' : 'th.spd.kmh')) + '" value="' + esc(t('spd.none')) + '">'
             : '<input class="in" data-k="gs" type="text" inputmode="numeric" autocomplete="off" aria-label="' + esc(t(S.units.distance === 'nm' ? 'th.spd.kt' : 'th.spd.kmh')) + '" value="' + (typeof p.gs === 'number' ? speedDisp(p.gs) : '') + '" placeholder="' + dflt + '">') +
    '<select class="in" data-k="altRef"><option value="AGL"' + (p.altRef === 'AGL' ? ' selected' : '') + '>' + esc(t('ref.AGL')) + '</option>' +
    '<option value="MSL"' + (p.altRef === 'MSL' ? ' selected' : '') + '>' + esc(t('ref.MSL')) + '</option></select>' +
    '<button type="button" class="pt-del" data-act="delete" title="' + esc(t('tip.delete')) + '" aria-label="' + esc(t('tip.delete')) + '">×</button></div>').join('');
  $('alt-unit').textContent = t('th.alt', { u: t(S.units.altitude === 'ft' ? 'u.ft' : 'u.m') });
  $('spd-unit').textContent = t(S.units.distance === 'nm' ? 'th.spd.kt' : 'th.spd.kmh');
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

/* La vitesse par défaut, en exemple grisé dans les champs vides de la colonne */
function syncSpeedPlaceholders() {
  const d = String(speedDisp(S.groundSpeed));
  document.querySelectorAll('#pts input[data-k="gs"]:not(:disabled)').forEach(el => { el.placeholder = d; });
}

function syncRows() {
  document.querySelectorAll('#pts .pt-row').forEach(r => r.classList.toggle('sel', parseInt(r.dataset.i, 10) === sel));
  document.querySelectorAll('#refs .pt-row').forEach(r => r.classList.toggle('sel', parseInt(r.dataset.i, 10) === selR));
}

function navTitle() {
  if (!navIsMag()) return t('nav.title.true');
  if (!navIsCalc()) return t('nav.title.mag', { d: decimal(String(parseDecl(S.navDisplay.decl))) });
  const ys = navYear(), n = S.points.length;
  if (n < 2) return t('nav.title.calc0', { a: ys.year });
  let lo = Infinity, hi = -Infinity;
  for (let i = 0; i < n - 1; i++) { const v = declAt(S.points[i], ys); if (v < lo) lo = v; if (v > hi) hi = v; }
  const a = fmtVar(lo), b = fmtVar(hi);
  return a === b ? t('nav.title.calc1', { a: ys.year, v: a }) : t('nav.title.calc', { a: ys.year, min: a, max: b });
}

/* La ligne de source de l'année (deux lignes) : le mot en gras, le nom du fichier en .dv-file */
function dvFill(key, file, date) {
  return esc(t(key)).split('{date}').join(esc(date)).split('{file}').join('<span class="dv-file">' + esc(file) + '</span>');
}
function dvSrcHtml(ys) {
  let h = '<b>' + esc(t('dv.tag.' + ys.src)) + '</b> ' + dvFill('dv.src.' + ys.src, ys.file, ys.date);
  return h + '<br>' + esc(t('dv.src.model', { e: magEpoch(ys.y) }));
}

function renderNav() {
  $('nav-title').textContent = navTitle();
  const tm = timing();
  const calc = navIsCalc(), ys = calc ? navYear() : null;
  let rows = '';
  S.points.forEach((p, i) => {
    if (i > 0) {
      const lg = tm.legs[i];
      rows += '<tr class="leg"><td></td><td colspan="2">' + esc(t('nav.leg', { cap: lg.cap, spd: speedText(lg.v), ete: fmtEte(lg.sec) })) + '</td><td class="r">' + esc(fmtDist(lg.km)) + '</td></tr>';
    }
    rows += '<tr><td class="n">' + i + '</td><td class="nm">' + esc(p.name) + '<span class="co alt">' + esc(altText(p)) + '</span><span class="co alt tm">' + esc(t('nav.t', { t: fmtElapsed(tm.el[i]) })) + '</span>' +
      (calc ? '<span class="co alt dv-leg">' + esc(t('nav.var', { v: fmtVar(declAt(p, ys)) })) + '</span>' : '') + '</td>' +
      '<td colspan="2"><span class="co">' + esc(toMGRS(p.lat, p.lon)) + '</span><span class="co dms">' + esc(toDMS(p.lat, p.lon)) + '</span></td></tr>';
  });
  $('nav-body').innerHTML = rows;
  $('nav-total').textContent = t('nav.total.v', { d: fmtDist(tm.km), t: fmtElapsed(tm.sec) });
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
  mark('data-lbx', S.legBoxes);
  mark('data-trc', S.ui.trace);
  mark('data-tck', S.ui.ticks);
  $('gs-lbl').textContent = t('f.gs', { u: t(S.units.distance === 'nm' ? 'u.kt' : 'u.kmh') });
  const gsIn = $('gs-def');
  if (document.activeElement !== gsIn) gsIn.value = speedDisp(S.groundSpeed);
  syncSpeedPlaceholders();
  syncDecl();
  $('btn-handoff').disabled = S.points.length === 0;
  const rtb = $('btn-export-rt');
  const hasRt = hasRouteTool(S.theatre);
  rtb.disabled = !S.points.length || !hasRt;
  if (hasRt) rtb.removeAttribute('title'); else rtb.title = t('tb.rt.off');
  $('theme').value = document.body.dataset.theme;
  const pl = $('btn-places');
  pl.classList.toggle('on', !!S.ui.places);
  pl.setAttribute('aria-pressed', S.ui.places ? 'true' : 'false');
  const tw = $('btn-towns');
  const hasTw = !!townsOf(S.theatre);
  tw.disabled = !hasTw;
  tw.classList.toggle('on', hasTw && !!S.ui.towns);
  tw.setAttribute('aria-pressed', hasTw && S.ui.towns ? 'true' : 'false');
  tw.title = t(hasTw ? 'tb.towns.tip' : 'tb.towns.off');
  const af = $('btn-airfields');
  const hasAf = !!airfieldsOf(S.theatre);
  af.disabled = !hasAf;
  af.classList.toggle('on', hasAf && !!S.ui.airfields);
  af.setAttribute('aria-pressed', hasAf && S.ui.airfields ? 'true' : 'false');
  af.title = t(hasAf ? 'tb.airfields.tip' : 'tb.airfields.off');
  syncAdd();
}

/* La rangée Déclinaison (en cap magnétique seulement) : Calculée ou Saisie ; en Calculée l'année, Forcer et la ligne de source */
function syncDecl() {
  const mag = S.navDisplay.ref === 'mag', calc = S.navDisplay.mode === 'calc';
  $('dv-wrap').hidden = !mag;
  const bar = $('dv-wrap').querySelectorAll('[data-dvm]');
  bar.forEach(b => {
    const on = b.dataset.dvm === S.navDisplay.mode;
    b.classList.toggle('on', on);
    b.setAttribute('aria-pressed', on ? 'true' : 'false');
  });
  $('dv-year-w').hidden = !calc;
  $('dv-force-w').hidden = !calc;
  $('dv-decl-w').hidden = calc;
  $('dv-help').hidden = calc;
  $('dv-src').hidden = !calc;
  $('decl-warn').hidden = calc || !(mag && parseDecl(S.navDisplay.decl) == null);
  if (!mag || !calc) return;
  const ys = navYear(), mis = ys.src === 'mission' || ys.src === 'forced';
  const yin = $('dv-year'), fb = $('dv-force');
  const lock = ys.src === 'mission' && !S.navDisplay.force;     /* la mission fait foi : le champ montre son année, sans la laisser modifier */
  yin.disabled = lock;
  if (document.activeElement !== yin) yin.value = lock ? ys.year : S.navDisplay.year;
  fb.parentNode.style.visibility = mis ? '' : 'hidden';
  fb.disabled = !mis;
  fb.classList.toggle('on', !!S.navDisplay.force);
  fb.setAttribute('aria-pressed', S.navDisplay.force ? 'true' : 'false');
  $('dv-src').innerHTML = dvSrcHtml(ys);
}

function renderAll() {
  renderTheatreOptions();
  $('theatre').value = S.theatre;
  $('route-name').value = S.name;
  $('decl').value = S.navDisplay.decl;
  renderPts();
  renderRefs();
  renderLayers();
  renderNav();
  drawRoute();
  drawRefs();
  syncTapControl();
  srSyncTexts();
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
  /* cap magnétique (navigation en cap magnétique et déclinaison lisible) : le point se calcule au cap vrai cap + déclinaison
     du point dont on part (calculée au point, ou saisie) */
  const d = declAt(last);
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
      d.innerHTML = '<button type="button" class="tb-btn" data-tap="wp"></button><button type="button" class="tb-btn" data-tap="ref"></button><button type="button" class="tb-btn" data-tap="read"></button><button type="button" class="tb-btn" data-tap="draw"></button>';
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
  if (window.ResizeObserver) {
    const ro = new ResizeObserver(() => fallbackLayout());
    ro.observe($('tapmode')); ro.observe($('map'));
  }
  window.addEventListener('resize', fallbackLayout);
}

function setTapMode(m) {
  const was = tapMode;
  tapMode = m === 'ref' ? 'ref' : m === 'read' ? 'read' : m === 'draw' ? 'draw' : 'wp';
  syncTapControl();
  if (tapMode !== was) {
    if (map) map.closePopup();
    if (was === 'draw') drExit();
    if (tapMode === 'draw') drEnter();
    drawLayers();   /* les objets ne sont touchables qu'en mode Lire ; une cible agit comme un aérodrome dans les deux autres */
    drawRoute();    /* les « + » d'insertion ne s'affichent pas en mode Lire */
  }
}

function syncTapControl() {
  const d = $('tapmode');
  if (!d) return;
  d.title = t('tap.title');
  d.setAttribute('aria-label', t('tap.title'));
  d.querySelectorAll('[data-tap]').forEach(b => {
    const on = b.dataset.tap === tapMode;
    if (b.dataset.tap === 'draw') b.innerHTML = DR_ICONS.pen + esc(t('tap.draw'));
    else b.textContent = t('tap.' + b.dataset.tap);
    b.classList.toggle('on', on);
    b.setAttribute('aria-pressed', on ? 'true' : 'false');
  });
  fallbackLayout();
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
  } else if (k === 'gs') {
    if (kind === 'ref' || parseInt(row.dataset.i, 10) === 0) return;
    if (ev.target.value.trim() === '') delete p.gs;           /* vide : la vitesse de la route s'applique */
    else { const v = readSpeed(ev.target.value); if (v == null) return; p.gs = v; }
  } else if (k === 'altRef') p.altRef = ev.target.value === 'MSL' ? 'MSL' : 'AGL';
  else return;
  persistState();
  if (k === 'name') { if (kind === 'ref') drawRefs(); else drawRoute(); }
  else if (kind !== 'ref') { drawDecor(); updateTimes(); }       /* altitude, référence, vitesse : boîtes, traits et temps écoulés */
  renderNav();
}

function onRowChange(ev, kind) {
  const row = ev.target.closest('.pt-row');
  const k = ev.target.dataset.k;
  if (!row || (k !== 'alt' && k !== 'gs')) return;
  const p = (kind === 'ref' ? S.refs : S.points)[parseInt(row.dataset.i, 10)];
  if (!p) return;
  if (k === 'alt') ev.target.value = altValue(p.alt);
  else if (kind !== 'ref' && parseInt(row.dataset.i, 10) > 0) ev.target.value = typeof p.gs === 'number' ? speedDisp(p.gs) : '';
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

/* ============= RECHERCHE SUR LA CARTE ============= */
/* Une loupe sous le zoom ; son panneau à droite : un champ, une croix, au plus 8 résultats. Choisir centre la carte (zoom 11 au moins)
   et signale la position par un anneau qui pulse 3 s ; cela n'ajoute jamais rien à la route. */
const SR_MIN = 2;              /* caractères avant la liste */
const SR_ROWS = 8;             /* rangées au plus */
const SR_ZOOM = 11;            /* zoom de la carte après le choix : celui-ci au moins */
const SR_RING_MS = 3000;       /* l'anneau reste 3 s */
const SR = { open: false, q: '', rows: [], active: 0, ring: null, ringTimer: 0, norms: {} };

/* Sans accents ni majuscules : décomposition NFD, marques retirées, minuscules */
function srNorm(s) { return String(s).normalize('NFD').replace(/\p{M}/gu, '').toLowerCase(); }

/* La position du nom d'un objet de calque : celle de son nom (zone, orbite, boîte), son centre (cercle), sa position (point) */
function cfNameAt(it) {
  if (it.type === 'zone') {
    const pts = it.points;
    return (it.kind === 'corridor' || it.kind === 'flot') ? pts[Math.floor(pts.length / 2)] : cfMean(pts);
  }
  if (it.type === 'orbit') return cfOrbitGeom(it).nameAt;
  if (it.type === 'box') return cfBoxGeom(it).nameAt;
  return [it.lat, it.lon];
}

/* Tout ce qui se cherche, sur le théâtre en cours : points de la route, références, objets nommés des calques visibles, aérodromes
   et hélistations, villes. kind : l'ordre des genres (0 point · 1 référence · 2 objet de calque · 3 aérodrome ou hélistation · 4 ville) */
function srItems() {
  const out = [];
  const add = (kind, name, lat, lon, genre) => { if (typeof name === 'string' && name !== '') out.push({ kind: kind, name: name, nn: srNorm(name), lat: lat, lon: lon, genre: genre }); };
  S.points.forEach((p, i) => add(0, p.name, p.lat, p.lon, t('sr.k.wp', { n: i + 1 })));
  S.refs.forEach((p, i) => add(1, p.name, p.lat, p.lon, t('sr.k.ref', { n: i + 1 })));
  CF_LAYERS.forEach(l => {
    if (!l.visible) return;
    l.items.forEach(it => {
      if (it.type === 'text' || typeof it.name !== 'string' || it.name.trim() === '') return;
      const at = cfNameAt(it);
      add(2, it.name, at[0], at[1], l.name);
    });
  });
  const af = airfieldsOf(S.theatre);
  if (af) af.forEach(a => add(3, a[0], a[1], a[2], t(a[3] === 'h' ? 'sr.k.hp' : 'sr.k.af')));
  const tw = townsOf(S.theatre);
  if (tw) {
    if (!SR.norms[S.theatre]) SR.norms[S.theatre] = tw.map(a => srNorm(a[0]));
    const nn = SR.norms[S.theatre], g = t('sr.k.town');
    tw.forEach((a, i) => { if (a[0] !== '') out.push({ kind: 4, name: a[0], nn: nn[i], lat: a[1], lon: a[2], genre: g }); });
  }
  return out;
}

/* La requête passe par norm puis trim ; rang 0 : le nom commence par elle ; rang 1 : un de ses mots (suites de lettres et de chiffres)
   commence par elle ; rang 2 : il la contient. Tri : rang, genre, nom normalisé (unités de code), nom ; les 8 premiers. */
function srSearch(q) {
  const k = srNorm(q).trim();
  if (k.length < SR_MIN) return null;
  const hits = [];
  srItems().forEach(it => {
    let rank = -1;
    if (it.nn.startsWith(k)) rank = 0;
    else if (it.nn.split(/[^\p{L}\p{N}]+/u).some(w => w !== '' && w.startsWith(k))) rank = 1;
    else if (it.nn.indexOf(k) !== -1) rank = 2;
    if (rank >= 0) { it.rank = rank; hits.push(it); }
  });
  hits.sort((a, b) => (a.rank - b.rank) || (a.kind - b.kind) || (a.nn < b.nn ? -1 : a.nn > b.nn ? 1 : 0) || (a.name < b.name ? -1 : a.name > b.name ? 1 : 0));
  return hits.slice(0, SR_ROWS);
}

function srPlace() {
  const p = $('sr-panel');
  if (!p || !map) return;
  const sz = map.getSize();
  p.style.width = Math.max(120, Math.min(340, sz.x - 70)) + 'px';
  /* le haut du panneau est aligné sur celui de la loupe */
  const btn = document.querySelector('.rp-search-btn');
  p.style.top = '0px';
  p.style.top = (btn.getBoundingClientRect().top - p.getBoundingClientRect().top) + 'px';
  /* la liste défile plutôt que de déborder de la carte */
  const top = p.getBoundingClientRect().top - map.getContainer().getBoundingClientRect().top;
  const list = $('sr-list');
  list.style.maxHeight = Math.max(44, sz.y - top - 44 - 4 - 12) + 'px';
}

function srRender() {
  const list = $('sr-list'), input = $('sr-in');
  const rows = srSearch(SR.q);
  SR.rows = rows || [];
  if (SR.active >= SR.rows.length) SR.active = Math.max(0, SR.rows.length - 1);
  if (!rows) {
    list.hidden = true;
    list.innerHTML = '';
    input.removeAttribute('aria-activedescendant');
    input.setAttribute('aria-expanded', 'false');
    return;
  }
  list.hidden = false;
  input.setAttribute('aria-expanded', 'true');
  if (!rows.length) {
    list.innerHTML = '<div class="sr-row none" role="presentation"><span class="sr-nm">' + esc(t('sr.none')) + '</span></div>';
    input.removeAttribute('aria-activedescendant');
  } else {
    list.innerHTML = rows.map((r, i) =>
      '<div class="sr-row' + (i === SR.active ? ' active' : '') + '" role="option" id="sr-opt-' + i + '" data-i="' + i + '" aria-selected="' + (i === SR.active ? 'true' : 'false') + '">' +
      '<span class="sr-nm">' + esc(r.name) + '</span><span class="sr-kd">' + esc(r.genre) + '</span></div>').join('');
    input.setAttribute('aria-activedescendant', 'sr-opt-' + SR.active);
  }
  srPlace();
}

function srSetActive(i, scroll) {
  if (!SR.rows.length) return;
  SR.active = Math.max(0, Math.min(SR.rows.length - 1, i));
  const list = $('sr-list');
  list.querySelectorAll('.sr-row[data-i]').forEach(r => {
    const on = parseInt(r.dataset.i, 10) === SR.active;
    r.classList.toggle('active', on);
    r.setAttribute('aria-selected', on ? 'true' : 'false');
    if (on && scroll) r.scrollIntoView({ block: 'nearest' });
  });
  $('sr-in').setAttribute('aria-activedescendant', 'sr-opt-' + SR.active);
}

function srOpen() {
  if (!map || SR.open) return;
  SR.open = true;
  document.querySelector('.rp-search-btn').setAttribute('aria-expanded', 'true');
  const p = $('sr-panel'), input = $('sr-in');
  p.hidden = false;
  input.value = SR.q;
  SR.active = 0;
  srRender();
  srPlace();
  input.focus();
  input.select();
}

function srClose() {
  if (!SR.open) return;
  SR.open = false;
  document.querySelector('.rp-search-btn').setAttribute('aria-expanded', 'false');
  $('sr-panel').hidden = true;
  const input = $('sr-in');
  if (document.activeElement === input) input.blur();
}

/* L'anneau : sur la position, un cercle de 3 px de trait qui passe de 12 à 44 px en s'effaçant, trois fois 1 s, puis retiré ;
   un nouveau choix remplace celui qui est en cours */
function srRing(lat, lon) {
  srClearRing();
  SR.ring = L.marker([lat, lon], { pane: 'ring', interactive: false, keyboard: false,
    icon: L.divIcon({ className: 'sr-ring-icon', iconSize: [0, 0], iconAnchor: [0, 0], html: '<span class="sr-ring"></span>' }) }).addTo(map);
  SR.ringTimer = setTimeout(srClearRing, SR_RING_MS);
}
function srClearRing() {
  clearTimeout(SR.ringTimer);
  SR.ringTimer = 0;
  if (SR.ring) { map.removeLayer(SR.ring); SR.ring = null; }
}

/* Choisir : le panneau se ferme, la carte se centre sur le résultat (zoom courant, 11 au moins, sans animation), l'anneau pulse ;
   rien n'est ajouté à la route */
function srChoose(i) {
  const r = SR.rows[i];
  if (!r) return;
  srClose();
  map.setView([r.lat, r.lon], Math.max(map.getZoom(), SR_ZOOM), { animate: false });
  srRing(r.lat, r.lon);
}

function srSyncTexts() {
  const b = document.querySelector('.rp-search-btn');
  if (!b) return;
  b.title = t('sr.title');
  b.setAttribute('aria-label', t('sr.title'));
  const input = $('sr-in');
  input.placeholder = t('sr.ph');
  input.setAttribute('aria-label', t('sr.title'));
  const x = $('sr-x');
  x.title = t('sr.close');
  x.setAttribute('aria-label', t('sr.close'));
  if (SR.open) srRender();
}

function createSearchControl() {
  const Ctl = L.Control.extend({
    options: { position: 'topleft' },
    onAdd: function () {
      const d = L.DomUtil.create('div', 'leaflet-control rp-search');
      d.innerHTML =
        '<div class="leaflet-bar"><a class="rp-search-btn" href="#" role="button" aria-haspopup="dialog" aria-expanded="false" aria-controls="sr-panel">' +
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" aria-hidden="true"><circle cx="10" cy="10" r="6.5"/><path d="M15 15l6 6"/></svg></a></div>' +
        '<div class="sr-panel" id="sr-panel" role="search" hidden>' +
        '<div class="sr-head"><input class="sr-in" id="sr-in" type="search" autocomplete="off" autocapitalize="off" spellcheck="false" enterkeyhint="search" role="combobox" aria-autocomplete="list" aria-controls="sr-list" aria-expanded="false">' +
        '<button type="button" class="sr-x" id="sr-x">&times;</button></div>' +
        '<div class="sr-list" id="sr-list" role="listbox" hidden></div></div>';
      L.DomEvent.disableClickPropagation(d);
      L.DomEvent.disableScrollPropagation(d);
      d.querySelector('.rp-search-btn').addEventListener('click', ev => { ev.preventDefault(); if (SR.open) srClose(); else srOpen(); });
      const input = d.querySelector('#sr-in');
      input.addEventListener('input', () => { SR.q = input.value; SR.active = 0; srRender(); });
      input.addEventListener('keydown', ev => {
        ev.stopPropagation();           /* ni la carte ni la page ne lisent les touches du champ */
        if (ev.key === 'ArrowDown') { ev.preventDefault(); srSetActive(SR.active + 1, true); }
        else if (ev.key === 'ArrowUp') { ev.preventDefault(); srSetActive(SR.active - 1, true); }
        else if (ev.key === 'Enter') { ev.preventDefault(); if (SR.rows.length) srChoose(SR.active); }
        else if (ev.key === 'Escape') { ev.preventDefault(); srClose(); }
      });
      d.querySelector('#sr-x').addEventListener('click', () => srClose());
      const list = d.querySelector('#sr-list');
      list.addEventListener('click', ev => {
        const row = ev.target.closest ? ev.target.closest('.sr-row[data-i]') : null;
        if (row) srChoose(parseInt(row.dataset.i, 10));
      });
      list.addEventListener('mousemove', ev => {
        const row = ev.target.closest ? ev.target.closest('.sr-row[data-i]') : null;
        if (row && parseInt(row.dataset.i, 10) !== SR.active) srSetActive(parseInt(row.dataset.i, 10), false);
      });
      return d;
    }
  });
  new Ctl().addTo(map);
  document.addEventListener('keydown', ev => { if (ev.key === 'Escape' && SR.open) { ev.preventDefault(); srClose(); } });
  map.on('resize', () => { if (SR.open) srPlace(); });
  srSyncTexts();
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

/* sel (avec des calques) : { route, layers: [id…] } — la route décochée laisse points et refs vides ; les calques cochés, dans l'ordre de la section,
   forment le champ « layers » ; sans sel : le fichier d'avant les calques, à l'octet */
function downloadJson(sel) {
  const obj = exportObject();
  if (sel) {
    if (!sel.route) { obj.points = []; obj.refs = []; }
    const chosen = CF_LAYERS.filter(l => sel.layers.indexOf(l.id) !== -1);
    if (chosen.length) obj.layers = chosen;
  }
  const blob = new Blob([JSON.stringify(obj, null, 2)], { type: 'application/json' });
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
  S.groundSpeed = route.groundSpeed;
  S.legBoxes = route.legBoxes;
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
    if (zipIsZip(bytes)) {          /* un .cf (zip de CombatFlite) se reconnaît à ses deux premiers octets, « PK » */
      cfRead(bytes, file.name).then(res => openCfImport(file.name, res))
        .catch(e => showToast(t(e && e.message === 'nods' ? 'err.cfBrowser' : 'err.cf')));
      return;
    }
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
    /* « layers » : des calques qui s'ajoutent aux calques présents (un même id remplace le sien) ; sans route dans le fichier, la route n'est pas touchée */
    const lays = Array.isArray(parsed.layers) ? parsed.layers.map(cfLayer).filter(Boolean) : [];
    if (!res.route.points.length && lays.length) {
      cfMerge(lays);
      if (layersChanged()) showToast(t(cfOne(lays.length) ? 'toast.layersAdded.1' : 'toast.layersAdded.n', { n: lays.length }), 4500);
      return;
    }
    if (S.points.length && !confirm(t('confirm.open'))) return;
    setRoute(res.route);
    let msg = (res.dropped ? t('toast.openedDropped', { n: res.dropped }) : t('toast.opened')) +
      (res.droppedRefs ? ' · ' + t('toast.refsDropped', { n: res.droppedRefs }) : '');
    if (lays.length) { cfMerge(lays); if (layersChanged()) msg += ' · ' + t(cfOne(lays.length) ? 'toast.cfShown.1' : 'toast.cfShown.n', { n: lays.length }); }
    showToast(msg);
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

const RT_MODALS = ['rt-open-modal', 'rt-export-modal', 'cf-import-modal', 'cf-export-modal'];
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
  RT_MODALS.forEach(id => { if (rtVisible(id)) rtHide(id); });
}
/* Tab reste dans la fenêtre ouverte */
function rtTrap(ev) {
  if (ev.key !== 'Tab') return;
  const id = RT_MODALS.filter(rtVisible)[0];
  const m = id ? $(id) : null;
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
  setRoute({ name: r.name, theatre: th, units: S.units, navDisplay: S.navDisplay, groundSpeed: S.groundSpeed, legBoxes: S.legBoxes, points: pts, refs: [] });
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

/* ============= CALQUES : SECTION DU PANNEAU, FENÊTRES D'IMPORT ET D'EXPORT ============= */
/* FR : le singulier jusqu'à 1 (0 compris) ; EN : le singulier pour 1 seulement */
function cfOne(n) { return CURRENT_LANG === 'fr' ? n < 2 : n === 1; }

/* Les calques ont changé : enregistrer (false si le stockage refuse), refaire la section et la carte */
function layersChanged() {
  const ok = persistLayers();
  renderLayers();
  drawLayers();
  drAfterLayers();
  return ok;
}

function renderLayers() {
  const n = CF_LAYERS.length;
  $('sec-layers').hidden = !n;
  $('layers-count').textContent = t(n === 1 ? 'layers.count.1' : 'layers.count.n', { n: n });
  $('layers-list').innerHTML = CF_LAYERS.map(l =>
    '<div class="cf-row" data-id="' + esc(l.id) + '" title="' + esc(l.source.file) + '">' +
    '<label class="cf-vis"><input type="checkbox" data-act="vis"' + (l.visible ? ' checked' : '') + ' aria-label="' + esc(l.name) + '"></label>' +
    '<div class="cf-main"><span class="cf-nm">' + esc(l.name) + '</span><span class="cf-n">' + esc(cfCounts(l.items)) + '</span></div>' +
    '<button type="button" class="cf-del" data-act="del" title="' + esc(t('layers.remove')) + '" aria-label="' + esc(t('layers.remove')) + '">×</button></div>').join('');
}

function cfLayerOfRow(el) {
  const row = el.closest('.cf-row');
  return row ? CF_LAYERS.find(x => x.id === row.dataset.id) : null;
}

function removeLayer(l) {
  if (!confirm(t('confirm.layer', { name: l.name }))) return;
  CF_LAYERS = CF_LAYERS.filter(x => x !== l);
  layersChanged();
}

function removeAllLayers() {
  if (!CF_LAYERS.length || !confirm(t('confirm.layers'))) return;
  CF_LAYERS = [];
  layersChanged();
}

/* ---- Fenêtre « Calques CombatFlite » : un .cf lu, les calques à cocher ---- */
const CFI = { fileName: '', theatre: '', known: true, layers: [], checked: [] };

function cfTheatreMsg() { return t('toast.cfTheatre', { t: CFI.theatre, theatre: t('th.' + S.theatre) }); }

function cfImportRender() {
  const tid = cfTheatreId(CFI.theatre);
  $('cf-import-file').textContent = t('cf.file', { name: CFI.fileName, t: tid ? t('th.' + tid) : CFI.theatre });
  $('cf-import-list').innerHTML = CFI.layers.map((l, i) =>
    '<label class="rt-row"><input type="checkbox" data-i="' + i + '"' + (CFI.checked[i] ? ' checked' : '') + '>' +
    '<span class="rt-nm">' + esc(l.name) + '</span><span class="rt-n">' + esc(cfCounts(l.items)) + '</span></label>').join('');
}

/* Le théâtre du fichier, s'il est connu, devient celui du Route Planner (comme un choix à la liste : la route reste) ; sinon il reste et un toast le dit */
function openCfImport(fileName, res) {
  CFI.fileName = fileName;
  CFI.theatre = res.theatre;
  CFI.layers = res.layers;
  CFI.checked = res.pre.slice();
  const id = cfTheatreId(res.theatre);
  CFI.known = !!id;
  if (id) { if (id !== S.theatre) setTheatre(id); }
  else showToast(cfTheatreMsg(), 5000);
  cfImportRender();
  rtShow('cf-import-modal', $('btn-open'), 'cf-import-go');
  const first = $('cf-import-list').querySelector('input');
  if (first) first.focus({ preventScroll: true });
}

/* « Afficher » : les calques cochés s'ajoutent aux calques présents (un même id remplace le sien) ; la carte ne bouge pas */
function cfImportGo() {
  const picked = CFI.layers.filter((l, i) => CFI.checked[i]).map(l => Object.assign({}, l, { visible: true }));
  cfMerge(picked);
  rtHide('cf-import-modal');
  if (!layersChanged()) return;
  let msg = t(cfOne(picked.length) ? 'toast.cfShown.1' : 'toast.cfShown.n', { n: picked.length });
  if (!CFI.known) msg += ' · ' + cfTheatreMsg();
  showToast(msg, CFI.known ? 2600 : 5000);
}

/* ---- Fenêtre « Exporter » : la route et les calques que le fichier emporte ---- */
const CFE = { route: true, checked: [] };

function cfExportRender() {
  $('cf-export-list').innerHTML =
    '<label class="rt-row"><input type="checkbox" data-k="route"' + (CFE.route ? ' checked' : '') + '><span class="rt-nm">' + esc(t('cf.exp.route')) + '</span>' +
    '<span class="rt-n">' + esc(t('cf.exp.routeN', { n: S.points.length, m: S.refs.length })) + '</span></label>' +
    CF_LAYERS.map((l, i) =>
      '<label class="rt-row"><input type="checkbox" data-i="' + i + '"' + (CFE.checked[i] ? ' checked' : '') + '>' +
      '<span class="rt-nm">' + esc(l.name) + '</span><span class="rt-n">' + esc(cfCounts(l.items)) + '</span></label>').join('');
  cfExportSync();
}

/* Exporter sans rien de coché est désactivé */
function cfExportSync() { $('cf-export-go').disabled = !(CFE.route || CFE.checked.some(Boolean)); }

function openCfExport(opener) {
  CFE.route = true;
  CFE.checked = CF_LAYERS.map(l => l.visible);
  cfExportRender();
  rtShow('cf-export-modal', opener, 'cf-export-go');
}

function cfExportGo() {
  const sel = { route: CFE.route, layers: CF_LAYERS.filter((l, i) => CFE.checked[i]).map(l => l.id) };
  rtHide('cf-export-modal');
  downloadJson(sel);
}

/* « Enregistrer » et « Exporter JSON » : sans calque, le fichier d'aujourd'hui, sans fenêtre ; avec des calques, la fenêtre « Exporter » */
function onSaveClick(ev) {
  if (!CF_LAYERS.length) { downloadJson(); return; }
  openCfExport(ev && ev.currentTarget);
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
  if (rtVisible('cf-import-modal')) cfImportRender();
  if (rtVisible('cf-export-modal')) cfExportRender();
  map.closePopup();
  if (drOn()) { DR.sheetKey = ''; drRlab(); drSyncUi(); }
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
  $('btn-towns').addEventListener('click', () => {
    if (!townsOf(S.theatre)) return;
    S.ui.towns = !S.ui.towns;
    persistState();
    syncTowns();
    syncControls();
  });
  $('btn-airfields').addEventListener('click', () => {
    if (!airfieldsOf(S.theatre)) return;
    S.ui.airfields = !S.ui.airfields;
    persistState();
    syncAirfields();
    syncControls();
  });
  $('theatre').addEventListener('change', e => setTheatre(e.target.value));
  document.querySelectorAll('[data-dist]').forEach(b => b.addEventListener('click', () => {
    S.units.distance = b.dataset.dist === 'nm' ? 'nm' : 'km';
    persistState(); renderPts(); renderNav(); drawRoute(); syncControls();
  }));
  document.querySelectorAll('[data-alt]').forEach(b => b.addEventListener('click', () => {
    S.units.altitude = b.dataset.alt === 'ft' ? 'ft' : 'm';
    persistState(); renderPts(); renderRefs(); renderNav(); drawDecor(); syncControls();
  }));
  document.querySelectorAll('[data-ref]').forEach(b => b.addEventListener('click', () => {
    S.navDisplay.ref = b.dataset.ref === 'mag' ? 'mag' : 'true';
    persistState(); renderNav(); drawRoute(); syncControls();
  }));
  document.querySelectorAll('[data-lbx]').forEach(b => b.addEventListener('click', () => {
    S.legBoxes = LEGBOX_IDS.indexOf(b.dataset.lbx) !== -1 ? b.dataset.lbx : 'full';
    persistState(); drawDecor(); syncControls();
  }));
  document.querySelectorAll('[data-trc]').forEach(b => b.addEventListener('click', () => {
    S.ui.trace = b.dataset.trc === 'black' ? 'black' : 'route';
    persistState(); drawRoute(); syncControls();
  }));
  document.querySelectorAll('[data-tck]').forEach(b => b.addEventListener('click', () => {
    S.ui.ticks = b.dataset.tck === 'black' ? 'black' : 'route';
    persistState(); drawDecor(); syncControls();
  }));
  /* La vitesse sol de la route : mêmes règles que la colonne ; une saisie hors règle (ou vide) ne change rien, le champ reprend sa valeur en quittant */
  $('gs-def').addEventListener('input', e => {
    const v = readSpeed(e.target.value);
    if (v == null) return;
    S.groundSpeed = v;
    persistState(); renderNav(); drawDecor(); updateTimes(); syncSpeedPlaceholders();
  });
  $('gs-def').addEventListener('change', e => { e.target.value = speedDisp(S.groundSpeed); });
  $('decl').addEventListener('input', e => {
    S.navDisplay.decl = e.target.value;
    persistState(); renderNav(); drawRoute(); syncControls();
  });
  document.querySelectorAll('[data-dvm]').forEach(b => b.addEventListener('click', () => {
    S.navDisplay.mode = b.dataset.dvm === 'manual' ? 'manual' : 'calc';
    persistState(); renderNav(); drawRoute(); syncControls();
  }));
  $('dv-force').addEventListener('click', () => {
    S.navDisplay.force = !S.navDisplay.force;
    persistState(); renderNav(); drawRoute(); syncControls();
  });
  $('dv-year').addEventListener('input', e => {
    const v = e.target.value.replace(/\D/g, '').slice(0, 4);
    if (e.target.value !== v) e.target.value = v;
    S.navDisplay.year = v;
    persistState(); renderNav(); drawRoute(); syncControls();
  });
  /* HQ charge une autre mission pendant que le Route Planner est ouvert : l'année se relit */
  window.addEventListener('storage', e => {
    if (e.key === 'mission_snapshot_v1' && navIsCalc()) { renderNav(); drawRoute(); syncControls(); }
  });
  $('route-name').addEventListener('input', e => { S.name = e.target.value; persistState(); });
  $('panel').addEventListener('focusin', ev => {
    const el = ev.target;
    if (el && /^(INPUT|TEXTAREA|SELECT)$/.test(el.tagName)) revealPanelField(el);
  });
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
  /* la sélection est remise à zéro après lecture : choisir deux fois le même fichier le relit */
  fileOpen.addEventListener('change', () => { const f = fileOpen.files && fileOpen.files[0]; if (f) openRouteFile(f); fileOpen.value = ''; });
  $('btn-save').addEventListener('click', onSaveClick);
  $('btn-export').addEventListener('click', onSaveClick);
  $('btn-export-rt').addEventListener('click', openExportRouteTool);
  ['rt-open-backdrop', 'rt-open-close', 'rt-open-cancel'].forEach(id => $(id).addEventListener('click', () => rtHide('rt-open-modal')));
  ['rt-export-backdrop', 'rt-export-close', 'rt-export-cancel'].forEach(id => $(id).addEventListener('click', () => rtHide('rt-export-modal')));
  $('rt-theatre').addEventListener('change', e => { if (hasRouteTool(e.target.value)) RT.theatre = e.target.value; });
  $('rt-routes').addEventListener('change', e => { const k = parseInt(e.target.value, 10); if (k >= 0 && k < RT.routes.length) RT.sel = k; });
  $('rt-open-go').addEventListener('click', rtOpenGo);
  /* les calques CombatFlite : la section du panneau, les fenêtres d'import et d'export */
  $('layers-list').addEventListener('change', ev => {
    const l = ev.target.dataset.act === 'vis' ? cfLayerOfRow(ev.target) : null;
    if (!l) return;
    l.visible = ev.target.checked;
    persistLayers();
    drawLayers();
    drAfterLayers();
  });
  $('layers-list').addEventListener('click', ev => {
    const b = ev.target.closest('button[data-act="del"]');
    const l = b ? cfLayerOfRow(b) : null;
    if (l) removeLayer(l);
  });
  $('btn-layers-clear').addEventListener('click', removeAllLayers);
  ['cf-import-backdrop', 'cf-import-close', 'cf-import-cancel'].forEach(id => $(id).addEventListener('click', () => rtHide('cf-import-modal')));
  ['cf-export-backdrop', 'cf-export-close', 'cf-export-cancel'].forEach(id => $(id).addEventListener('click', () => rtHide('cf-export-modal')));
  $('cf-import-go').addEventListener('click', cfImportGo);
  $('cf-import-list').addEventListener('change', ev => {
    const i = parseInt(ev.target.dataset.i, 10);
    if (i >= 0 && i < CFI.checked.length) CFI.checked[i] = ev.target.checked;
  });
  $('cf-export-go').addEventListener('click', cfExportGo);
  $('cf-export-list').addEventListener('change', ev => {
    if (ev.target.dataset.k === 'route') CFE.route = ev.target.checked;
    else { const i = parseInt(ev.target.dataset.i, 10); if (i >= 0 && i < CFE.checked.length) CFE.checked[i] = ev.target.checked; }
    cfExportSync();
  });
  const fileRt = $('file-rt');
  $('rt-add').addEventListener('click', () => { fileRt.value = ''; fileRt.click(); });
  fileRt.addEventListener('change', () => { if (fileRt.files && fileRt.files[0]) rtExportAdd(fileRt.files[0]); });
  $('rt-new').addEventListener('click', rtExportNew);
  document.addEventListener('keydown', ev => {
    if (ev.key === 'Escape' && RT_MODALS.some(rtVisible)) { ev.preventDefault(); rtCloseAll(); }
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
const TBM = { cur: null, bound: false, swallow: false, n: 0, all: [], map: new WeakMap(), label: null, mo: null, ro: null };

function initToolbarMenus(specs) {
  specs.forEach(sp => tbmAttach(document.getElementById(sp[0]), sp[1], sp[2]));
  if (TBM.bound) return;
  TBM.bound = true;
  document.addEventListener('pointerdown', tbmOutside, true);
  window.addEventListener('click', tbmSwallowClick, true);
  window.addEventListener('resize', () => tbmClose(false));
  window.addEventListener('blur', () => tbmClose(false));
  window.addEventListener('scroll', tbmScrolled, true);
}

/* ----- Listes des formulaires (lot mp-ui-listes-formulaires) -----
   Tout <select> hors de la barre du haut passe par le même composant, présent au chargement ou inséré ensuite
   (formulaire reconstruit, rangée ajoutée, onglet ouvert) : un observateur le rattache dès son insertion, et
   détache le bouton d'un <select> qui quitte la page (la liste ouverte sur lui se ferme). labelFn(select) donne l'intitulé. */
function initFormMenus(labelFn) {
  TBM.label = labelFn;
  tbmScan(document.body);
  if (TBM.mo) return;
  TBM.mo = new MutationObserver(recs => {
    for (let i = TBM.all.length - 1; i >= 0; i--) if (!TBM.all[i].sel.isConnected) tbmForget(TBM.all[i]);
    recs.forEach(r => r.addedNodes.forEach(n => { if (n.nodeType === 1) tbmScan(n); }));
  });
  TBM.mo.observe(document.body, { childList: true, subtree: true });
}

function tbmScan(root) {
  if (!TBM.label || !root || root.nodeType !== 1 || root.classList.contains('tbm-panel')) return;
  if (root.tagName !== 'SELECT' && !root.firstElementChild) return;
  const list = root.tagName === 'SELECT' ? [root] : Array.prototype.slice.call(root.querySelectorAll('select'));
  list.forEach(s => {
    if (TBM.map.has(s) || (s.closest && s.closest('header.toolbar'))) return;
    tbmAttach(s, () => TBM.label(s), 'field');
  });
}

function tbmForget(m) {
  if (TBM.cur === m) tbmClose(false);
  if (m.mo) m.mo.disconnect();
  if (TBM.ro) TBM.ro.unobserve(m.btn);
  if (m.btn.parentNode) m.btn.parentNode.removeChild(m.btn);
  TBM.map.delete(m.sel);
  const i = TBM.all.indexOf(m);
  if (i >= 0) TBM.all.splice(i, 1);
}

/* Un champ de moins de 120 px de large : chevron à 8 px du bord (12 px sinon) */
function tbmNarrow(btn) {
  const w = btn.offsetWidth;
  if (w > 0) btn.classList.toggle('tbm-narrow', w < 120);
}

/* mode : rien (liste de la barre) · 'field' (liste de formulaire, bouton d'un champ) · 'sheet' (liste de formulaire,
   bouton fermé déjà habillé par le module) */
function tbmAttach(sel, labelFn, mode) {
  if (!sel || !sel.parentNode || TBM.map.has(sel)) return;
  const uid = sel.id || 'f' + (++TBM.n);
  const btn = document.createElement('button');
  btn.type = 'button';
  btn.className = sel.className + ' tbm-trigger' + (mode === 'field' ? ' tbm-field' : '');
  btn.setAttribute('aria-haspopup', 'listbox');
  btn.setAttribute('aria-expanded', 'false');
  btn.setAttribute('aria-controls', 'tbm-list-' + uid);
  const lbl = document.createElement('span');
  lbl.className = 'tbm-lbl';
  btn.appendChild(lbl);
  const m = { sel: sel, btn: btn, lbl: lbl, labelFn: labelFn, panel: null, active: -1, type: '', typeTimer: 0, x0: 0, y0: 0, uid: uid, form: !!mode, mo: null };
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
  m.mo = new MutationObserver(() => tbmSync(m));
  m.mo.observe(sel, {
    childList: true, subtree: true, characterData: true, attributes: true,
    attributeFilter: ['title', 'aria-label', 'disabled', 'label', 'selected', 'value']
  });
  TBM.map.set(sel, m);
  TBM.all.push(m);
  if (mode === 'field' && window.ResizeObserver) {
    if (!TBM.ro) TBM.ro = new ResizeObserver(es => es.forEach(e => tbmNarrow(e.target)));
    TBM.ro.observe(btn);
  }
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
  ul.className = 'tbm-panel' + (m.form ? ' tbm-p-field' : '');
  ul.id = 'tbm-list-' + m.uid;
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
    li.id = 'tbm-' + m.uid + '-' + k;
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

/* Sous le bouton (4 px), bord gauche aligné, au moins aussi large, à 8 px au moins des bords de la fenêtre.
   Liste de formulaire : la place utile va du bas de la barre du haut au haut de la barre d'onglets fixée en bas (portrait),
   sinon au bas de la fenêtre ; dessous si elle y tient entière, sinon dessus si la place y est plus grande (classe tbm-up). */
function tbmPlace(m) {
  const r = m.btn.getBoundingClientRect(), p = m.panel;
  const vw = document.documentElement.clientWidth, vh = window.innerHeight;
  let top = r.bottom + 4;
  m.x0 = r.left; m.y0 = r.top;
  if (m.form) {
    const tb = document.querySelector('header.toolbar'), bar = document.querySelector('.tab-bar');
    const lo = tb ? tb.getBoundingClientRect().bottom : 0;
    let hi = vh;
    if (bar) {
      const bs = getComputedStyle(bar), br = bar.getBoundingClientRect();
      if (bs.position === 'fixed' && bs.display !== 'none' && br.height > 0 && br.top > lo) hi = Math.min(hi, br.top);
    }
    const cap = Math.min(0.62 * vh, 440);
    const below = hi - (r.bottom + 4) - 12, above = (r.top - 4) - lo - 12;
    p.style.minWidth = Math.min(Math.max(180, r.width), vw - 16) + 'px';
    p.style.maxHeight = 'none';
    const up = Math.min(p.offsetHeight, cap) > below && above > below;
    p.style.maxHeight = Math.max(60, Math.min(cap, up ? above : below)) + 'px';
    p.classList.toggle('tbm-up', up);
    p.style.top = (up ? r.top - 4 - p.offsetHeight : r.bottom + 4) + 'px';
    p.style.left = r.left + 'px';
    const fw = p.getBoundingClientRect().width;
    let fl = r.left;
    if (fl + fw > vw - 8) fl = vw - 8 - fw;
    if (fl < 8) fl = 8;
    p.style.left = fl + 'px';
    return;
  }
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
  if (m.form) sel.dispatchEvent(new Event('input', { bubbles: true }));   /* comme le contrôle natif : input puis change */
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
  initToolbarMenus([['layer', () => t('tb.layer')], ['theatre', () => t('tb.theatre')], ['theme', () => t('tb.theme.tip')], ['rt-theatre', () => t('tb.theatre'), 'sheet']]);   /* les listes de la barre au thème de l'interface */
  initFormMenus(sel => (sel.dataset.k === 'altRef' ? t('th.ref') : ''));   /* les listes des formulaires */
  loadState();
  loadLayers();
  createMap();
  bindEvents();
  drInit();
  spInit();
  renderAll();
  drawLayers();
  frameRoute();
  setBase();
  syncPlaces();
  syncAirfields();
  syncTowns();
  persistState();
  /* Les polices embarquées servent au canevas : redessiner la grille une fois chargées */
  if (document.fonts && document.fonts.load) {
    Promise.all([
      document.fonts.load("700 15px 'Stardos Stencil'"),
      document.fonts.load("700 11px 'Oswald'"),
      document.fonts.load("500 11px 'Oswald'")
    ]).then(() => document.fonts.ready).then(() => { scheduleGrid(); twWidths.clear(); syncTowns(); }).catch(() => {});
  }
  window.__RP = { map: map, get decorGroup() { return decorGroup; }, timing: timing, get S() { return S; }, drawGrid: drawGrid, setBase: setBase, get baseLayers() { return baseLayers; }, get inFallback() { return inFallback; },
    get placesLayer() { return placesLayer; }, get airfieldLayer() { return afLayer; }, get tapMode() { return tapMode; },
    get townsLayer() { return twLayer; }, townsReport: townsReport, get search() { return SR; },
    get layers() { return CF_LAYERS; }, get layersGroup() { return cfGroup; }, get draw() { return DR; }, get split() { return SP; } };
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
    towns_js = json.dumps(TW['theatres'], ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
    js = JS.replace('__EXAMPLE_ROUTE__', example_js).replace('__AIRFIELDS__', airfields_js).replace('__TOWNS__', towns_js)
    js = js.replace('@@GEO_BLOCK@@\n', GEO_BLOCK).replace('@@READNUM_BLOCK@@\n', READNUM_BLOCK).replace('@@MAGVAR_BLOCK@@\n', build_magvar_block())
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
