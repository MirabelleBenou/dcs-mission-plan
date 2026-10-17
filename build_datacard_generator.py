#!/usr/bin/env python3
"""Build — DCS Datacard Generator v1.0.0.

Produit dist/dcs_datacard_generator.html : un fichier unique, hors ligne, sans
serveur et sans ressource externe. Les polices et les bibliothèques (html2canvas,
JSZip) viennent d'assets.json, à la racine du dépôt.

Usage : python3 build_datacard_generator.py
"""

import json
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
APP_VERSION = "1.0.0"
OUT_PATH = os.path.join(HERE, 'dist', 'dcs_datacard_generator.html')
ASSETS_PATH = os.path.join(HERE, 'assets.json')

REQUIRED_ASSETS = ['STARDOS_700', 'OSWALD_500', 'ROBOTO_MONO_400', 'lib_html2canvas', 'lib_jszip']

if not os.path.isfile(ASSETS_PATH):
    raise SystemExit(f"[ERREUR] Entrée manquante : {ASSETS_PATH} (assets.json attendu à la racine du dépôt)")
with open(ASSETS_PATH, encoding='utf-8') as f:
    A = json.load(f)
for _k in REQUIRED_ASSETS:
    if _k not in A or not A[_k]:
        raise SystemExit(f"[ERREUR] Entrée manquante dans assets.json : {_k}")

# Contenu du bouton « Exemple » : document au format dcs-datacard-v1, copié tel quel.
EXAMPLE_DOC_JSON = r'''{
  "format": "dcs-datacard-v1",
  "mode": "day",
  "cards": [
    {
      "meta": {
        "classification": "confidential",
        "docRef": "FH-M3-1989",
        "operation": "FOOTHOLD",
        "mission": "M3",
        "date": "1989-03-22",
        "time": "10:00 L"
      },
      "flight": {
        "callsign": "CAESAR",
        "aircraft": "Mi-24P",
        "count": 2,
        "task": "CAS / Défense de zone",
        "threat": "high"
      },
      "units": {
        "mass": "kg",
        "distance": "km",
        "altitude": "m"
      },
      "mission": {
        "objective": "Un convoi blindé quitte KARAVOSTASI pour reprendre POLIS : l'intercepter avant la FARP.",
        "execution": [
          "Décollage POLIS",
          "Chemin côtier jusqu'à l'IP",
          "Priorité SAM / AAA, puis APC / MBT",
          "RTB POLIS selon SITAC"
        ]
      },
      "times": [
        {
          "label": "Mise en route",
          "value": "09:30"
        },
        {
          "label": "Décollage",
          "value": "09:45"
        },
        {
          "label": "IP",
          "value": "10:05"
        },
        {
          "label": "TOT",
          "value": "10:12"
        },
        {
          "label": "RTB",
          "value": "10:40"
        }
      ],
      "crew": [
        {
          "callsign": "CAESAR 1-1",
          "pilot": "VIPER",
          "crew": "HUSKER",
          "board": "41"
        },
        {
          "callsign": "CAESAR 1-2",
          "pilot": "FALCON",
          "crew": "BEAR",
          "board": "44"
        }
      ],
      "nav": [
        {
          "name": "POLIS FARP",
          "course": "",
          "distance": "",
          "altitude": "",
          "tos": "09:45",
          "note": "Départ"
        },
        {
          "name": "CÔTE 1",
          "course": "252",
          "distance": "14",
          "altitude": "50",
          "tos": "09:53",
          "note": ""
        },
        {
          "name": "IP",
          "course": "059",
          "distance": "32",
          "altitude": "50",
          "tos": "10:05",
          "note": "Île + rivière"
        },
        {
          "name": "TGT KARAVOSTASI",
          "course": "118",
          "distance": "9",
          "altitude": "30",
          "tos": "10:12",
          "note": "Axe côtier"
        },
        {
          "name": "POLIS FARP",
          "course": "296",
          "distance": "28",
          "altitude": "100",
          "tos": "10:40",
          "note": "RTB"
        }
      ],
      "radios": [
        {
          "name": "R-863",
          "channels": [
            {
              "channel": "0",
              "label": "Groupe 1",
              "frequency": "127.50",
              "modulation": "AM"
            },
            {
              "channel": "1",
              "label": "Groupe 2",
              "frequency": "135.00",
              "modulation": "AM"
            },
            {
              "channel": "3",
              "label": "Mission",
              "frequency": "265.00",
              "modulation": "AM"
            },
            {
              "channel": "7",
              "label": "ATC",
              "frequency": "270.00",
              "modulation": "AM"
            }
          ]
        },
        {
          "name": "R-828",
          "channels": [
            {
              "channel": "0",
              "label": "Tactique",
              "frequency": "21.50",
              "modulation": "FM"
            }
          ]
        }
      ],
      "fields": [
        {
          "role": "dep",
          "icao": "",
          "name": "POLIS",
          "runway": "",
          "frequency": "127.50"
        },
        {
          "role": "arr",
          "icao": "",
          "name": "POLIS",
          "runway": "",
          "frequency": "127.50"
        },
        {
          "role": "alt",
          "icao": "LCRA",
          "name": "Akrotiri",
          "runway": "10",
          "frequency": "270.00"
        }
      ],
      "weather": {
        "metar": "LCRA 221000Z 18002KT 9999 SCT082 20/15 Q1013",
        "wind": "180/02",
        "visibility": "≥ 10 km",
        "qnh": "1013 hPa",
        "clouds": "SCT 8200 ft"
      },
      "fuel": {
        "joker": "600",
        "bingo": "450"
      },
      "loadout": [
        "4 × 9M114 Shturm",
        "2 × B-8V20 (S-8)",
        "GSh-30-2 · 250 obus"
      ],
      "threats": [
        "SA-13",
        "SA-9",
        "MANPADS",
        "ZSU-23-4",
        "BMP-2"
      ],
      "notes": "Repère : petite île + rivière à 8 km de l'objectif."
    }
  ]
}'''

CSS = r"""
/* ============================================
   DATACARD GENERATOR — chrome de l'éditeur + datacard
   Monofichier, hors ligne, polices embarquées
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

:root {
  --f-stencil: 'Stardos Stencil', 'Impact', 'Arial Narrow Bold', sans-serif;
  --f-condensed: 'Impact', 'Arial Narrow', 'Helvetica Condensed', sans-serif;
  --f-ui: 'Oswald', 'Arial Narrow', sans-serif;
  --f-typewriter: 'Roboto Mono', 'Courier New', 'Courier', monospace;
  --f-mono: 'Roboto Mono', 'Courier New', 'Courier', monospace;
  --amber:        #c0892a;
  --amber-dark:   #8a5e15;
  --green-radar:  #4f6b3a;
}

/* ---- Thèmes de la chrome (body[data-theme]) : ils ne touchent jamais la datacard ---- */
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

* { box-sizing: border-box; margin: 0; padding: 0; }
html, body { height: 100%; overscroll-behavior: none; }
button { font: inherit; cursor: pointer; }
input, select, textarea { font: inherit; }

body {
  font-family: var(--f-typewriter);
  background: var(--olive-deep);
  color: var(--ink);
  font-size: 14px;
  line-height: 1.5;
  overflow: hidden;
  -webkit-tap-highlight-color: transparent;
  -webkit-text-size-adjust: 100%;
}

/* ============ TOOLBAR ============ */
.toolbar {
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
}
.tb-brand {
  display: flex; align-items: center; gap: 10px;
  color: var(--paper);
  font-family: var(--f-stencil);
  font-weight: 700;
  letter-spacing: 2px;
  font-size: 15px;
  border-right: 1px solid var(--khaki);
  padding-right: 12px;
  margin-right: 4px;
  white-space: nowrap;
  flex-shrink: 0;
}
.tb-brand::before {
  content: '';
  display: inline-block;
  width: 8px; height: 8px;
  background: var(--amber);
  border-radius: 50%;
  box-shadow: 0 0 8px var(--amber);
  animation: pulse 2s ease-in-out infinite;
}
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50%      { opacity: .4; }
}
.tb-btn {
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
}
.tb-btn:hover, .tb-btn:focus-visible {
  background: var(--olive);
  border-color: var(--amber);
  color: var(--amber);
  outline: none;
}
.tb-btn:active { transform: translateY(1px); }
.tb-btn.danger:hover {
  background: var(--rust);
  border-color: var(--red-faded);
  color: var(--paper-light);
}
.tb-btn svg { width: 16px; height: 16px; flex-shrink: 0; }
.tb-btn .tb-short { display: none; }

.tb-select {
  font-family: var(--f-ui);
  font-weight: 700;
  letter-spacing: 1.5px;
  font-size: 12px;
  text-transform: uppercase;
  background-color: var(--olive-dark);
  color: var(--amber);
  border: 1px solid var(--amber-dark);
  padding: 0 32px 0 12px;
  height: 40px;
  cursor: pointer;
  transition: all .15s ease;
  white-space: nowrap;
  appearance: none;
  -webkit-appearance: none;
  -moz-appearance: none;
  flex-shrink: 0;
  background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 12 8'><path d='M1 1l5 5 5-5' fill='none' stroke='%23c0892a' stroke-width='2'/></svg>");
  background-repeat: no-repeat;
  background-position: right 10px center;
  background-size: 10px 6px;
}
.tb-select:hover, .tb-select:focus-visible {
  background-color: var(--olive);
  border-color: var(--amber);
  outline: none;
}
.tb-select option {
  background-color: var(--olive-dark);
  color: var(--paper);
}
.tb-spacer { flex: 1; min-width: 0; }
.tb-version {
  font-size: 11px;
  opacity: 0.5;
  color: var(--amber);
  letter-spacing: 0.5px;
  align-self: center;
  margin-left: 8px;
  user-select: none;
}
.tb-lang-btn {
  background: transparent;
  border: 1px solid var(--khaki);
  color: var(--paper);
  height: 40px;
  min-width: 44px;
  padding: 0 10px;
  cursor: pointer;
  transition: all .15s ease;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  line-height: 1;
  flex-shrink: 0;
}
.tb-lang-btn:hover, .tb-lang-btn:focus-visible {
  background: var(--olive);
  border-color: var(--amber);
  outline: none;
}
.tb-lang-btn:active { transform: translateY(1px); }

/* Sélecteur à deux positions Day | Night : la position active est pleine, soulignée d'ambre */
.tb-seg {
  display: inline-flex;
  align-items: stretch;
  height: 40px;
  flex-shrink: 0;
  border: 1px solid var(--khaki);
}
.tb-seg .seg-btn {
  font-family: var(--f-ui);
  font-weight: 700;
  letter-spacing: 1.5px;
  font-size: 12px;
  text-transform: uppercase;
  background: transparent;
  color: var(--paper);
  border: 0;
  padding: 0 14px;
  cursor: pointer;
  white-space: nowrap;
  transition: all .15s ease;
}
.tb-seg .seg-btn + .seg-btn { border-left: 1px solid var(--khaki); }
.tb-seg .seg-btn:hover, .tb-seg .seg-btn:focus-visible {
  background: var(--olive);
  color: var(--amber);
  outline: none;
}
.tb-seg .seg-btn.active,
.tb-seg .seg-btn.active:hover {
  background: var(--amber-dark);
  color: #f6efdc;
  box-shadow: inset 0 -3px 0 var(--amber);
}

/* ============ MAIN APP ============ */
.app {
  position: fixed;
  top: 56px; bottom: 0; left: 0; right: 0;
  display: grid;
  grid-template-columns: 460px 1fr;
  background: var(--olive-deep);
}
.editor {
  background:
    repeating-linear-gradient(0deg, transparent 0, transparent 2px, rgba(0,0,0,.04) 2px, rgba(0,0,0,.04) 3px),
    linear-gradient(180deg, var(--olive-dark) 0%, var(--olive-deep) 100%);
  border-right: 2px solid var(--amber-dark);
  overflow-y: auto;
  overflow-x: hidden;
  overscroll-behavior: contain;
  padding: 16px 16px 80px 16px;
  color: var(--paper);
  min-width: 0;
}
.editor::-webkit-scrollbar { width: 10px; }
.editor::-webkit-scrollbar-track { background: var(--olive-deep); }
.editor::-webkit-scrollbar-thumb { background: var(--khaki); border: 2px solid var(--olive-deep); }

/* Paquet de datacards */
.pack-bar {
  margin-bottom: 14px;
  border: 1px solid var(--amber-dark);
  background: rgba(20, 24, 12, .6);
  padding: 10px 12px;
  display: flex; flex-direction: column; gap: 10px;
}
.pack-title {
  font-family: var(--f-stencil);
  font-weight: 700;
  font-size: 14px;
  letter-spacing: 2px;
  color: var(--amber);
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.pack-btns { display: flex; flex-wrap: wrap; gap: 6px; }
.pack-btn {
  font-family: var(--f-ui);
  font-weight: 700;
  letter-spacing: 1.2px;
  font-size: 11px;
  text-transform: uppercase;
  background: transparent;
  color: var(--paper);
  border: 1px solid var(--khaki);
  padding: 0 10px;
  min-height: 36px;
  min-width: 40px;
  white-space: nowrap;
}
.pack-btn:hover:not(:disabled), .pack-btn:focus-visible {
  background: var(--olive);
  border-color: var(--amber);
  color: var(--amber);
  outline: none;
}
.pack-btn:disabled { opacity: .35; cursor: not-allowed; }
.pack-btn.danger:hover:not(:disabled) { background: var(--rust); border-color: var(--red-faded); color: var(--paper-light); }

/* Sections */
.ed-section {
  contain: layout;
  margin-bottom: 14px;
  border: 1px solid var(--khaki);
  background: rgba(20, 24, 12, .5);
  min-width: 0;
}
.ed-section > summary {
  cursor: pointer;
  padding: 12px 14px;
  background: linear-gradient(90deg, var(--olive) 0%, var(--olive-dark) 100%);
  font-family: var(--f-stencil);
  font-weight: 700;
  font-size: 13px;
  letter-spacing: 2px;
  color: var(--amber);
  list-style: none;
  display: flex; align-items: center; justify-content: space-between;
  border-bottom: 1px solid var(--amber-dark);
  user-select: none;
  min-height: 48px;
}
.ed-section > summary::-webkit-details-marker { display: none; }
.ed-section > summary::after {
  content: '◄';
  font-size: 10px;
  color: var(--paper);
  transition: transform .2s;
}
.ed-section[open] > summary::after { transform: rotate(-90deg); }
.ed-section > summary:hover { color: var(--paper-light); }
.ed-content {
  padding: 14px;
  display: flex; flex-direction: column; gap: 14px;
  min-width: 0;
}
.panel-mobile-header { display: none; }

.ed-field { display: flex; flex-direction: column; gap: 5px; min-width: 0; }
.ed-field label {
  font-family: var(--f-ui);
  font-weight: 700;
  font-size: 11px;
  letter-spacing: 1.8px;
  text-transform: uppercase;
  color: var(--amber);
  display: flex; align-items: center; gap: 6px;
}
.ed-field label::before {
  content: '►';
  color: var(--rust);
  font-size: 8px;
}
.ed-field input[type=text],
.ed-field input[type=number],
.ed-field textarea,
.ed-field select {
  background: rgba(216, 201, 165, .92);
  border: 1px solid var(--khaki);
  border-left: 3px solid var(--amber-dark);
  font-family: var(--f-typewriter);
  font-size: 13px;
  color: #1f1c16;
  padding: 10px 11px;
  min-height: 44px;
  transition: all .15s;
  resize: vertical;
  width: 100%;
  min-width: 0;
}
.ed-field input:focus,
.ed-field textarea:focus,
.ed-field select:focus {
  outline: none;
  border-left-color: var(--red-stamp);
  background: #ece0c2;
  box-shadow: 0 0 0 1px var(--amber);
}
.ed-field textarea { min-height: 70px; line-height: 1.4; }
.ed-field-row { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.ed-field-row.three { grid-template-columns: 1fr 1fr 1fr; }
.ed-help {
  font-family: var(--f-ui);
  font-size: 11px;
  letter-spacing: 1px;
  color: var(--khaki-light);
}

/* Listes */
.ed-list { display: flex; flex-direction: column; gap: 8px; }
.li {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 40px;
  gap: 8px;
  align-items: start;
  padding: 8px;
  border: 1px dashed var(--khaki);
  background: rgba(0,0,0,.14);
  min-width: 0;
}
.li-main { display: flex; flex-direction: column; gap: 8px; min-width: 0; }
.li-ctl { display: flex; flex-direction: column; gap: 4px; }
.li-grid { display: grid; gap: 8px; min-width: 0; }
.li-grid.g2 { grid-template-columns: 1fr 1fr; }
.li-grid.g3 { grid-template-columns: 1fr 1fr 1fr; }
.li-grid.g4 { grid-template-columns: 1fr 1fr 1fr 1fr; }
.li-grid.g5 { grid-template-columns: 1fr 1fr 1fr 1fr 1fr; }
.li-grid.gs { grid-template-columns: minmax(0, 1fr); }
.li-sub {
  margin-left: 6px;
  padding-left: 8px;
  border-left: 2px solid var(--amber-dark);
  display: flex; flex-direction: column; gap: 8px;
}
.ed-btn-icon {
  background: var(--rust);
  border: 1px solid var(--red-faded);
  color: var(--paper-light);
  font-family: var(--f-ui);
  font-weight: 700;
  cursor: pointer;
  padding: 0;
  transition: background .15s;
  font-size: 15px;
  line-height: 1;
  min-width: 40px;
  min-height: 34px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.ed-btn-icon:hover { background: var(--red-stamp); }
.ed-btn-icon:active { transform: translateY(1px); }
.ed-btn-icon.neutral { background: var(--olive); border-color: var(--khaki); }
.ed-btn-icon.neutral:hover { background: var(--olive-dark); }
.ed-btn-icon:disabled { opacity: .35; cursor: not-allowed; }
.ed-btn-add {
  background: transparent;
  border: 1px dashed var(--amber);
  color: var(--amber);
  font-family: var(--f-ui);
  font-weight: 700;
  letter-spacing: 1.5px;
  padding: 10px;
  min-height: 44px;
  cursor: pointer;
  font-size: 12px;
  text-transform: uppercase;
  transition: all .15s;
}
.ed-btn-add:hover { background: var(--olive); color: var(--paper-light); }
.ed-btn-add:active { transform: translateY(1px); }
.ed-btn-add:disabled { opacity: .35; cursor: not-allowed; }
.ed-btn-add.sm { min-height: 36px; padding: 6px 10px; font-size: 11px; }

/* Aperçu */
.preview-wrap {
  overflow: auto;
  overscroll-behavior: contain;
  background: var(--olive-deep);
  padding: 20px 20px 60px 20px;
  min-width: 0;
}
.preview-wrap::-webkit-scrollbar { width: 12px; height: 12px; }
.preview-wrap::-webkit-scrollbar-track { background: var(--olive-deep); }
.preview-wrap::-webkit-scrollbar-thumb { background: var(--khaki); border: 2px solid var(--olive-deep); }
.dc-warn {
  margin: 0 auto 14px auto;
  max-width: 1000px;
  background: var(--red-stamp);
  color: #f6efdc;
  border: 1px solid var(--red-faded);
  font-family: var(--f-ui);
  font-weight: 700;
  letter-spacing: 1.2px;
  font-size: 12px;
  text-transform: uppercase;
  padding: 10px 14px;
}
.dc-warn[hidden] { display: none; }

/* ============ ONGLETS (tablette) ============ */
.tab-bar {
  display: none;
  position: fixed;
  bottom: 0; left: 0; right: 0;
  background: linear-gradient(180deg, var(--olive-dark) 0%, var(--olive-deep) 100%);
  border-top: 2px solid var(--amber-dark);
  padding: 6px 4px;
  padding-bottom: max(6px, env(safe-area-inset-bottom));
  z-index: 999;
  gap: 2px;
}
.tab-bar button {
  flex: 1 1 0;
  min-width: 0;
  background: transparent;
  border: 1px solid transparent;
  color: var(--khaki-light);
  font-family: var(--f-ui);
  font-weight: 700;
  font-size: 10px;
  letter-spacing: .3px;
  line-height: 1.15;
  text-transform: uppercase;
  padding: 6px 2px;
  min-height: 54px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  overflow: hidden;
  transition: all .15s;
}
.tab-bar button.current {
  background: var(--olive);
  color: var(--amber);
  border-color: var(--amber-dark);
}
.tab-bar button:active { transform: translateY(1px); }

/* ============ TOAST ============ */
.toast {
  position: fixed;
  bottom: 20px; left: 50%;
  transform: translateX(-50%) translateY(100px);
  background: var(--olive-dark);
  border: 1px solid var(--amber);
  color: var(--paper);
  font-family: var(--f-ui);
  font-weight: 700;
  letter-spacing: 2px;
  text-transform: uppercase;
  font-size: 12px;
  padding: 10px 20px;
  z-index: 20000;
  opacity: 0;
  transition: all .3s ease;
  pointer-events: none;
  box-shadow: 0 4px 16px rgba(0,0,0,.6);
  max-width: 92vw;
  text-align: center;
}
.toast.show {
  opacity: 1;
  transform: translateX(-50%) translateY(0);
  pointer-events: auto;
}

/* ============ FENÊTRES (export, import du briefing) ============ */
.export-modal[hidden] { display: none !important; }
.export-modal {
  position: fixed;
  inset: 0;
  z-index: 10000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
}
.export-modal-backdrop {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.55);
  backdrop-filter: blur(2px);
}
.export-modal-panel {
  position: relative;
  background: var(--paper, #f4ead5);
  color: #1f1c16;
  border: 2px solid #1f1c16;
  border-radius: 4px;
  padding: 24px 28px;
  max-width: 520px;
  width: 100%;
  max-height: 92vh;
  overflow-y: auto;
  box-shadow: 0 8px 40px rgba(0, 0, 0, 0.5);
  font-family: var(--f-typewriter);
}
.export-modal-close {
  position: absolute;
  top: 8px;
  right: 12px;
  background: none;
  border: none;
  color: #1f1c16;
  font-size: 24px;
  line-height: 1;
  cursor: pointer;
  padding: 4px 8px;
  font-family: inherit;
}
.export-modal-close:hover { color: var(--amber, #c8901f); }
.export-modal h2 {
  font-family: var(--f-stencil);
  font-weight: 700;
  font-size: 20px;
  letter-spacing: 2px;
  margin: 0 28px 14px 0;
  text-transform: uppercase;
}
.export-modal-choices {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}
.export-choice {
  background: transparent;
  border: 2px solid #1f1c16;
  border-radius: 3px;
  padding: 20px 14px;
  cursor: pointer;
  font-family: inherit;
  color: inherit;
  text-align: center;
  transition: background 0.15s, border-color 0.15s, transform 0.1s;
}
.export-choice:hover {
  background: rgba(0, 0, 0, 0.05);
  border-color: var(--amber, #c8901f);
  transform: translateY(-1px);
}
.export-choice:focus-visible { outline: 2px solid var(--amber, #c8901f); outline-offset: 2px; }
.export-choice-icon { font-size: 32px; margin-bottom: 8px; }
.export-choice-label {
  font-family: var(--f-stencil);
  font-weight: 700;
  font-size: 18px;
  letter-spacing: 2px;
  margin-bottom: 6px;
}
.export-choice-desc { font-size: 11px; opacity: 0.75; letter-spacing: 0.5px; line-height: 1.35; }
.export-png-config h3, .imp-block h3 {
  font-family: var(--f-stencil);
  font-weight: 700;
  font-size: 14px;
  letter-spacing: 2px;
  margin: 0 0 10px;
  text-transform: uppercase;
}
.export-png-actions-top { display: flex; gap: 8px; margin-bottom: 10px; }
.export-png-toggle {
  background: transparent;
  border: 1px solid #1f1c16;
  padding: 4px 10px;
  font-family: inherit;
  font-size: 11px;
  letter-spacing: 0.5px;
  cursor: pointer;
  color: inherit;
  border-radius: 2px;
}
.export-png-toggle:hover { background: rgba(0, 0, 0, 0.06); border-color: var(--amber, #c8901f); }
.export-png-list {
  max-height: 280px;
  overflow-y: auto;
  border: 1px solid rgba(0, 0, 0, 0.2);
  border-radius: 2px;
  padding: 6px 10px;
  margin-bottom: 14px;
  background: rgba(255, 255, 255, 0.25);
}
.export-png-page-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 5px 0;
  font-size: 12px;
  cursor: pointer;
}
.export-png-page-cb { accent-color: var(--amber, #c8901f); }
.export-png-page-num {
  font-family: var(--f-stencil);
  font-weight: 700;
  letter-spacing: 1px;
  min-width: 60px;
}
.export-png-page-hint {
  opacity: 0.8;
  font-size: 11px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.export-png-actions-bottom { display: flex; justify-content: space-between; gap: 10px; }
.export-png-back, .export-png-go {
  background: transparent;
  border: 2px solid #1f1c16;
  padding: 8px 18px;
  font-family: var(--f-stencil);
  font-weight: 700;
  letter-spacing: 2px;
  font-size: 13px;
  cursor: pointer;
  color: inherit;
  border-radius: 2px;
  text-transform: uppercase;
}
.export-png-back:hover { background: rgba(0, 0, 0, 0.05); }
.export-png-go {
  background: var(--amber, #c8901f);
  color: #f6efdc;
  border-color: var(--amber, #c8901f);
}
.export-png-go:hover { background: #1f1c16; border-color: #1f1c16; }
.export-png-go:disabled { opacity: 0.4; cursor: not-allowed; pointer-events: none; }
.imp-block { margin-bottom: 14px; }
.imp-src {
  display: flex; align-items: center; gap: 10px;
  padding: 6px 0;
  font-size: 13px;
  cursor: pointer;
}
.imp-src.off { opacity: .5; cursor: not-allowed; }
.imp-src input { accent-color: var(--amber, #c8901f); }
.imp-note { font-size: 11px; opacity: .75; margin: 0 0 6px 26px; line-height: 1.35; }
.imp-file { display: flex; align-items: center; gap: 10px; margin: 2px 0 6px 26px; font-size: 11px; }
.imp-file[hidden] { display: none; }
.imp-filebtn {
  background: transparent;
  border: 1px solid #1f1c16;
  padding: 4px 10px;
  font-family: inherit;
  font-size: 11px;
  cursor: pointer;
  color: inherit;
  border-radius: 2px;
}
.imp-filebtn:hover { background: rgba(0, 0, 0, 0.06); border-color: var(--amber, #c8901f); }
.imp-filename { opacity: .75; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.imp-empty { font-size: 12px; opacity: .7; padding: 6px 0; }

/* ============ DATACARD ============ */
.dc-sheet {
  width: calc(1000px * var(--s, 1));
  height: calc(1414px * var(--s, 1));
  margin: 0 auto 28px auto;
  position: relative;
  overflow: hidden;
  box-shadow: 0 8px 24px rgba(0,0,0,.5), 0 2px 4px rgba(0,0,0,.3);
  flex-shrink: 0;
}
.dc-sheet > .dc-page {
  transform: scale(var(--s, 1));
  transform-origin: 0 0;
}

.dc-page[data-mode="day"] {
  --dc-pg: #f1ecdf;  --dc-ink: #14130f;  --dc-blk: #fbf8f0;  --dc-bd: #14130f;
  --dc-bh-bg: #14130f;  --dc-bh-fg: #f1ecdf;
  --dc-band-bg: #14130f;  --dc-band-fg: #f1ecdf;
  --dc-alt: #ece6d6;  --dc-acc: #3d4a22;
  --dc-hi: #a3261a;  --dc-mod: #9a6b16;  --dc-lo: #4a5a2a;
  --dc-dot: #9a9480;  --dc-metar: #e2dccb;  --dc-muted: #5a5646;
  --dc-pill-fg: #f1ecdf;  --dc-rule: #14130f;
}
.dc-page[data-mode="night"] {
  --dc-pg: #121310;  --dc-ink: #d6cfb8;  --dc-blk: #1a1b16;  --dc-bd: #3e3f33;
  --dc-bh-bg: #2a2b22;  --dc-bh-fg: #e2d9bf;
  --dc-band-bg: #26271f;  --dc-band-fg: #c9a45a;
  --dc-alt: #202119;  --dc-acc: #c9a45a;
  --dc-hi: #d0604c;  --dc-mod: #c08a2a;  --dc-lo: #7d8f52;
  --dc-dot: #4a4a3e;  --dc-metar: #24251d;  --dc-muted: #9a9378;
  --dc-pill-fg: #f1ecdf;  --dc-rule: #d6cfb8;
}

.dc-page {
  position: relative;
  width: 1000px;
  height: 1414px;
  overflow: hidden;
  background: var(--dc-pg);
  color: var(--dc-ink);
  font-family: 'Oswald', 'Arial Narrow', sans-serif;
  font-weight: 500;
  font-size: 20px;
  line-height: 1.25;
  display: flex;
  flex-direction: column;
  -webkit-print-color-adjust: exact;
  print-color-adjust: exact;
}
.dc-page * { box-sizing: border-box; margin: 0; padding: 0; }

.dc-top, .dc-foot {
  flex: 0 0 32px;
  height: 32px;
  background: var(--dc-band-bg);
  color: var(--dc-band-fg);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 26px;
  font-size: 15px;
  letter-spacing: 3px;
  text-transform: uppercase;
  white-space: nowrap;
}
.dc-top span, .dc-foot span { color: var(--dc-band-fg); }

.dc-head {
  flex: 0 0 143px;
  height: 143px;
  display: flex;
  justify-content: space-between;
  padding: 10px 30px 0 30px;
  border-bottom: 3px solid var(--dc-rule);
  overflow: hidden;
}
.dc-hl { display: flex; flex-direction: column; min-width: 0; flex: 1 1 auto; }
.dc-cs {
  font-family: 'Stardos Stencil', 'Impact', sans-serif;
  font-weight: 700;
  font-size: 82px;
  line-height: 90px;
  height: 90px;
  letter-spacing: 1px;
  color: var(--dc-ink);
  white-space: nowrap;
  overflow: hidden;
}
.dc-sub {
  margin-top: 4px;
  font-size: 22px;
  line-height: 30px;
  height: 30px;
  letter-spacing: 2px;
  color: var(--dc-ink);
  white-space: nowrap;
  overflow: hidden;
}
.dc-hr {
  display: flex; flex-direction: column; align-items: flex-end;
  flex: 0 0 auto;
  max-width: 470px;
  padding-top: 0;
}
.dc-ttl {
  font-family: 'Stardos Stencil', 'Impact', sans-serif;
  font-weight: 700;
  font-size: 36px;
  line-height: 40px;
  letter-spacing: 7px;
  color: var(--dc-acc);
  margin-right: -7px;
}
.dc-op {
  font-size: 22px; line-height: 28px; letter-spacing: 1.5px;
  color: var(--dc-ink);
  white-space: nowrap; overflow: hidden; max-width: 470px;
}
.dc-dt {
  font-family: 'Roboto Mono', 'Courier New', monospace;
  font-weight: 400;
  font-size: 21px; line-height: 27px;
  color: var(--dc-ink);
  white-space: nowrap; overflow: hidden; max-width: 470px;
}
.dc-pill {
  margin-top: 6px;
  font-size: 19px; line-height: 26px; letter-spacing: 2px;
  padding: 0 11px;
  color: var(--dc-pill-fg);
  white-space: nowrap;
}
.dc-pill.thr-high { background: var(--dc-hi); }
.dc-pill.thr-moderate { background: var(--dc-mod); }
.dc-pill.thr-low { background: var(--dc-lo); }
.dc-head.dc-head2 { flex: 0 0 62px; height: 62px; padding-top: 4px; align-items: center; }
.dc-head2 .dc-cs { font-size: 46px; line-height: 54px; height: 54px; }
.dc-head2 .dc-ttl { font-size: 36px; line-height: 50px; }

.dc-body {
  flex: 1 1 auto;
  min-height: 0;
  overflow: hidden;
  padding: 13px 30px 0 30px;
}
.dc-row { display: flex; gap: 13px; margin-bottom: 10px; align-items: stretch; }
.dc-row > .dc-block, .dc-row > .dc-col { flex: 1 1 0; min-width: 0; }
.dc-r1.dc-two > :first-child { flex: 0 0 564px; }
.dc-r1.dc-two > :last-child { flex: 0 0 363px; }
.dc-r4.dc-two > :first-child { flex: 0 0 515px; }
.dc-r4.dc-two > :last-child { flex: 0 0 412px; }
.dc-r5 { gap: 14px; }
.dc-col { display: flex; flex-direction: column; gap: 8px; }
.dc-col > .dc-block:last-child { flex: 1 1 auto; }

.dc-block {
  border: 2px solid var(--dc-bd);
  background: var(--dc-blk);
  display: flex;
  flex-direction: column;
  min-width: 0;
}
.dc-bh {
  flex: 0 0 30px;
  height: 30px;
  line-height: 30px;
  background: var(--dc-bh-bg);
  color: var(--dc-bh-fg);
  padding: 0 14px;
  font-size: 17px;
  font-weight: 500;
  letter-spacing: 4px;
  text-transform: uppercase;
  white-space: nowrap;
  overflow: hidden;
}
.dc-bb { padding: 10px 12px 10px 12px; flex: 1 1 auto; min-width: 0; }

/* Mission */
.dc-obj { font-size: 22px; line-height: 27px; margin-bottom: 10px; white-space: pre-line; overflow-wrap: anywhere; }
.dc-steps { list-style: none; }
.dc-steps li { display: flex; font-size: 21px; line-height: 26.5px; padding-left: 8px; }
.dc-steps .n { flex: 0 0 22px; }
.dc-steps .x { flex: 1 1 auto; min-width: 0; overflow-wrap: anywhere; }

/* Horaires */
.dc-times { padding-top: 4px; }
.dc-trow {
  display: flex; justify-content: space-between; align-items: baseline;
  border-bottom: 1px dotted var(--dc-dot);
  height: 36px; line-height: 36px;
  padding: 0 4px;
}
.dc-trow:last-child { border-bottom: 0; }
.dc-tl {
  font-size: 15px; letter-spacing: 2.5px; text-transform: uppercase;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis; flex: 1 1 auto; min-width: 0; padding-right: 8px;
}
.dc-tv {
  font-family: 'Roboto Mono', 'Courier New', monospace;
  font-weight: 400; font-size: 28px; white-space: nowrap; flex: 0 0 auto;
}

/* Tableaux */
.dc-tab { width: 100%; border-collapse: collapse; table-layout: fixed; }
.dc-tab th {
  font-size: 13px; font-weight: 500; letter-spacing: 2px; text-transform: none;
  color: var(--dc-muted); text-align: left; height: 24px; padding: 0 5px;
  white-space: nowrap; overflow: hidden;
}
.dc-tab td {
  height: 32px; padding: 0 5px;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  vertical-align: middle;
}
.dc-tab .r { text-align: right; }
.dc-tab .m, .dc-m {
  font-family: 'Roboto Mono', 'Courier New', monospace;
  font-weight: 400; font-size: 22px;
}
.dc-tab .nm { font-size: 23px; font-weight: 700; }
.dc-tab tbody tr:nth-child(even) td { background: var(--dc-alt); }
.dc-bbt { padding: 4px 12px 8px 12px; }

/* Équipages */
.dc-crew td { height: 31px; }
.dc-crew .nm { font-size: 24px; }

/* Navigation */
.dc-nav td { height: 32px; }
.dc-nav .nm { font-size: 24px; }
.dc-nav .nt { font-size: 19px; font-weight: 500; }
.dc-nav .ix { font-size: 22px; }

/* Radio */
.dc-rname {
  font-family: 'Roboto Mono', 'Courier New', monospace;
  font-weight: 400; font-size: 17px; letter-spacing: 1px;
  color: var(--dc-acc); height: 28px; line-height: 34px; padding: 0 5px;
}
.dc-radio .dc-tab tbody tr:nth-child(even) td { background: transparent; }
.dc-radio .dc-tab tbody tr:nth-child(odd) td { background: var(--dc-alt); }
.dc-radio td { height: 35px; }
.dc-radio .us { font-size: 21px; font-weight: 700; text-transform: uppercase; }
.dc-radio .fq { font-size: 24px; }
.dc-radio .md { font-size: 15px; color: var(--dc-muted); text-align: right; letter-spacing: 1px; }

/* Terrains */
.dc-fields td { height: 32px; padding: 0 4px; }
.dc-fields .ro {
  font-size: 25px; font-weight: 700; color: var(--dc-acc);
  text-transform: uppercase;
}
.dc-fields .nm { font-size: 18px; }
.dc-fields .m { font-size: 21px; }

/* Météo */
.dc-metar {
  background: var(--dc-metar);
  font-family: 'Roboto Mono', 'Courier New', monospace;
  font-weight: 400; font-size: 16px; line-height: 20px;
  padding: 5px 10px; margin-bottom: 6px;
  overflow-wrap: anywhere;
}
.dc-wtab { width: 100%; border-collapse: collapse; }
.dc-wtab td { height: 28px; padding: 0 3px; white-space: nowrap; vertical-align: middle; }
.dc-wtab .wl {
  font-size: 13px; letter-spacing: 2px; text-transform: uppercase; color: var(--dc-ink);
}
.dc-wtab .wv {
  font-family: 'Roboto Mono', 'Courier New', monospace;
  font-weight: 400; font-size: 21px; text-align: right;
}

/* Carburant · Emport */
.dc-fuelwrap { display: flex; gap: 18px; }
.dc-fuel { flex: 0 0 150px; }
.dc-frow {
  display: flex; justify-content: space-between; align-items: baseline;
  border-bottom: 1px dotted var(--dc-dot); height: 36px; line-height: 36px;
}
.dc-frow:last-child { border-bottom: 0; }
.dc-frow .fl { font-size: 15px; letter-spacing: 2.5px; text-transform: uppercase; }
.dc-frow .fv { font-family: 'Roboto Mono', 'Courier New', monospace; font-weight: 400; font-size: 24px; white-space: nowrap; }
.dc-load { list-style: none; flex: 1 1 auto; min-width: 0; }
.dc-load li {
  font-family: 'Roboto Mono', 'Courier New', monospace; font-weight: 400;
  font-size: 20px; line-height: 28px; display: flex;
}
.dc-load .bl { flex: 0 0 22px; color: var(--dc-acc); font-size: 17px; }
.dc-load .lx { flex: 1 1 auto; min-width: 0; overflow-wrap: anywhere; }

/* Menaces · Notes */
.dc-chips { display: flex; flex-wrap: wrap; gap: 6px 8px; margin-bottom: 8px; }
.dc-chip {
  display: block;
  border: 2px solid var(--dc-hi); color: var(--dc-hi);
  font-size: 21px; font-weight: 700; line-height: 28px;
  padding: 0 10px; text-transform: uppercase; white-space: nowrap;
}
.dc-notes { font-size: 20px; line-height: 26px; font-weight: 700; white-space: pre-line; overflow-wrap: anywhere; }

/* ============ ADAPTATION < 1800 px : libellés courts ============ */
@media (max-width: 1800px) {
  .tb-btn .tb-long { display: none; }
  .tb-btn .tb-short { display: inline; }
  .tb-btn .tb-btn-label.solo { display: none; }
  .tb-btn { padding: 0 10px; }
}
@media (max-width: 1350px) {
  .tb-brand { font-size: 13px; }
  .tb-version { display: none; }
}

/* ============ TABLETTE ≤ 1100 px ============ */
@media (max-width: 1100px) {
  .tb-btn .tb-btn-label { display: none; }
  .tb-btn { padding: 0 8px; }
  .tb-brand { display: none; }
  .tb-select { max-width: 120px; padding: 0 26px 0 8px; text-overflow: ellipsis; overflow: hidden; }
  .tb-version { display: none; }
  .tb-seg .seg-btn { padding: 0 10px; }

  .app { grid-template-columns: 1fr; bottom: 68px; }
  .app .editor, .app .preview-wrap { display: none; }
  body[data-active-tab="preview"] .preview-wrap { display: block; }
  body:not([data-active-tab="preview"]) .editor { display: block; }
  body:not([data-active-tab="preview"]) .ed-section { display: none; }
__TAB_SECTION_RULES__
  body[data-active-tab] .ed-section > summary { display: none; }
  body[data-active-tab] .ed-section > .ed-content {
    display: flex !important;
    padding: 0;
    padding-top: 8px;
  }
  .panel-mobile-header {
    display: flex !important;
    background: linear-gradient(90deg, var(--olive) 0%, var(--olive-dark) 100%);
    padding: 12px 14px;
    font-family: var(--f-stencil);
    font-weight: 700;
    font-size: 14px;
    letter-spacing: 2px;
    color: var(--amber);
    border-bottom: 1px solid var(--amber-dark);
    margin: -2px 0 6px 0;
  }
  .tab-bar { display: flex; }
  .preview-wrap { padding: 16px 8px 30px 8px; }
}
@media (max-width: 600px) {
  .tb-btn { padding: 0 6px; min-width: 38px; height: 38px; }
  .ed-field-row, .ed-field-row.three, .li-grid.g2, .li-grid.g3, .li-grid.g4, .li-grid.g5 { grid-template-columns: 1fr 1fr; }
  .export-modal-choices { grid-template-columns: 1fr; }
  .export-modal-panel { padding: 18px 20px; }
  .editor { padding: 12px 12px 24px 12px; }
}

/* ============ IMPRESSION : une feuille A4 portrait par page de datacard ============ */
#print-root { display: none; }
#measure-root {
  position: fixed;
  left: -12000px;
  top: 0;
  width: 1000px;
  visibility: hidden;
  pointer-events: none;
  z-index: -1;
}
@page { size: A4 portrait; margin: 0; }
@media print {
  html, body { height: auto; overflow: visible; background: #ffffff; }
  .toolbar, .app, .tab-bar, .toast, .export-modal, #measure-root { display: none !important; }
  #print-root { display: block; }
  .dc-psheet {
    width: 210mm;
    height: 297mm;
    overflow: hidden;
    position: relative;
    break-after: page;
    page-break-after: always;
    background: var(--dc-pg);
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }
  .dc-psheet:last-child { break-after: auto; page-break-after: auto; }
  .dc-psheet[data-mode="day"] { --dc-pg: #f1ecdf; }
  .dc-psheet[data-mode="night"] { --dc-pg: #121310; }
  .dc-psheet > .dc-page {
    transform: scale(0.793701, 0.793853);
    transform-origin: 0 0;
  }
}
"""

# Règles « un onglet = une section » sous 1 100 px, générées pour les onze sections.
SECTION_IDS = ['meta', 'flight', 'mission', 'times', 'crew', 'nav', 'radio', 'fields', 'weather', 'fuel', 'threats']
_tab_rules = ',\n'.join(
    f'  body[data-active-tab="{s}"] .ed-section[data-section="{s}"]' for s in SECTION_IDS
) + ' {\n    display: block;\n    border: none;\n  }'
CSS = CSS.replace('__TAB_SECTION_RULES__', _tab_rules)
CSS = CSS.replace('__STARDOS_700__', A['STARDOS_700'])
CSS = CSS.replace('__OSWALD_500__', A['OSWALD_500'])
CSS = CSS.replace('__ROBOTO_MONO_400__', A['ROBOTO_MONO_400'])

HTML = r"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0, viewport-fit=cover">
<meta name="theme-color" content="#1a1e10">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<title>Datacard Generator</title>
<style>
__CSS__
</style>
<!-- html2canvas v1.4.1 — embarqué pour l'export PNG -->
<script>__LIB_HTML2CANVAS__</script>
<!-- JSZip v3.10.1 — embarqué pour l'export ZIP multi-pages -->
<script>__LIB_JSZIP__</script>
</head>
<body data-theme="cw-nato">

<!-- ===== TOOLBAR ===== -->
<header class="toolbar" role="toolbar" aria-label="Datacard Generator" data-i18n-aria-label="app.title">
  <div class="tb-brand"><span class="tb-brand-main" data-i18n="app.title">Datacard Generator</span></div>
  <div class="tb-seg" id="mode-seg" role="group" data-i18n-title="tb.mode.tip" title="Version de jour ou de nuit de la datacard" data-i18n-aria-label="tb.mode.tip" aria-label="Version de jour ou de nuit de la datacard">
    <button type="button" class="seg-btn" id="mode-day" data-mode="day" aria-pressed="true" data-i18n="tb.mode.day">Day</button>
    <button type="button" class="seg-btn" id="mode-night" data-mode="night" aria-pressed="false" data-i18n="tb.mode.night">Night</button>
  </div>
  <button class="tb-btn" id="btn-briefing" data-i18n-title="tb.briefing" title="Depuis le briefing">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><polyline points="9 15 12 18 15 15"/><line x1="12" y1="11" x2="12" y2="18"/></svg>
    <span class="tb-btn-label"><span class="tb-long" data-i18n="tb.briefing">Depuis le briefing</span><span class="tb-short" data-i18n="tb.briefing.short">Briefing</span></span>
  </button>
  <button class="tb-btn" id="btn-json-import" data-i18n-title="tb.json.import" title="Importer JSON">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
    <span class="tb-btn-label solo" data-i18n="tb.json.import">Importer JSON</span>
  </button>
  <input type="file" id="file-load" accept=".json,application/json" hidden>
  <button class="tb-btn" id="btn-json-export" data-i18n-title="tb.json.export" title="Exporter JSON">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/></svg>
    <span class="tb-btn-label solo" data-i18n="tb.json.export">Exporter JSON</span>
  </button>
  <button class="tb-btn" id="btn-print" data-i18n-title="tb.export" title="Exporter">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 6 2 18 2 18 9"/><path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/><rect x="6" y="14" width="12" height="8"/></svg>
    <span class="tb-btn-label solo" data-i18n="tb.export">Exporter</span>
  </button>
  <button class="tb-btn" id="btn-example" data-i18n-title="tb.example.tip" title="Charger la datacard d'exemple (remplace le document en cours)">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="8" y1="13" x2="16" y2="13"/><line x1="8" y1="17" x2="16" y2="17"/></svg>
    <span class="tb-btn-label solo" data-i18n="tb.example">Exemple</span>
  </button>
  <button class="tb-btn danger" id="btn-reset" data-i18n-title="tb.reset.tip" title="Vider le document (repartir d'une carte blanche)">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
    <span class="tb-btn-label solo" data-i18n="tb.reset">Reset</span>
  </button>
  <select class="tb-select" id="theme-select" data-i18n-title="tb.theme.tip" title="Thème graphique" data-i18n-aria-label="tb.theme.tip" aria-label="Thème graphique">
    <option value="cw-nato"     data-i18n="theme.cw-nato">Cold War OTAN</option>
    <option value="cw-soviet"   data-i18n="theme.cw-soviet">Cold War Soviétique</option>
    <option value="modern-nato" data-i18n="theme.modern-nato">OTAN moderne</option>
    <option value="modern-east" data-i18n="theme.modern-east">Bloc Est moderne</option>
  </select>
  <div class="tb-spacer"></div>
  <span class="tb-version">v__APP_VERSION__</span>
  <button class="tb-lang-btn" id="btn-lang" data-i18n-title="tb.lang.tip" title="Switch language / Changer de langue">🇬🇧</button>
</header>

<!-- ===== FENÊTRE D'EXPORT ===== -->
<div class="export-modal" id="export-modal" hidden role="dialog" aria-labelledby="export-modal-title" aria-modal="true">
  <div class="export-modal-backdrop" id="export-modal-backdrop"></div>
  <div class="export-modal-panel" role="document">
    <button class="export-modal-close" id="export-modal-close" data-i18n-aria-label="modal.close" aria-label="Fermer">×</button>
    <h2 id="export-modal-title" data-i18n="tb.export">Exporter</h2>
    <div class="export-modal-choices">
      <button class="export-choice" id="export-choice-pdf" type="button">
        <div class="export-choice-icon">🖨</div>
        <div class="export-choice-label">PDF</div>
        <div class="export-choice-desc" data-i18n="ex.pdf">PDF (impression)</div>
      </button>
      <button class="export-choice" id="export-choice-png" type="button">
        <div class="export-choice-icon">🖼</div>
        <div class="export-choice-label">PNG</div>
        <div class="export-choice-desc" data-i18n="ex.png">PNG (kneeboard)</div>
      </button>
    </div>
    <div class="export-png-config" id="export-png-config" hidden>
      <h3 data-i18n="ex.pages">Pages à exporter</h3>
      <div class="export-png-actions-top">
        <button type="button" class="export-png-toggle" id="export-png-all" data-i18n="ex.all">Tout cocher</button>
        <button type="button" class="export-png-toggle" id="export-png-none" data-i18n="ex.none">Tout décocher</button>
      </div>
      <div class="export-png-list" id="export-png-list"></div>
      <div class="export-png-actions-bottom">
        <button type="button" class="export-png-back" id="export-png-back" data-i18n="ex.back">← Retour</button>
        <button type="button" class="export-png-go" id="export-png-go"><span data-i18n="tb.export">Exporter</span> <span id="export-png-count"></span></button>
      </div>
    </div>
  </div>
</div>

<!-- ===== FENÊTRE D'IMPORT DEPUIS UN BRIEFING ===== -->
<div class="export-modal" id="import-modal" hidden role="dialog" aria-labelledby="import-modal-title" aria-modal="true">
  <div class="export-modal-backdrop" id="import-modal-backdrop"></div>
  <div class="export-modal-panel" role="document">
    <button class="export-modal-close" id="import-modal-close" data-i18n-aria-label="modal.close" aria-label="Fermer">×</button>
    <h2 id="import-modal-title" data-i18n="imp.title">Importer depuis le Briefing Generator</h2>
    <div class="imp-block">
      <label class="imp-src" id="imp-src-current-row"><input type="radio" name="imp-src" id="imp-src-current" value="current"><span data-i18n="imp.src.current">Briefing en cours</span></label>
      <div class="imp-note" id="imp-current-note" hidden></div>
      <label class="imp-src" id="imp-src-file-row"><input type="radio" name="imp-src" id="imp-src-file" value="file"><span data-i18n="imp.src.file">Fichier JSON du briefing</span></label>
      <div class="imp-file" id="imp-file-zone" hidden>
        <button type="button" class="imp-filebtn" id="imp-file-btn" data-i18n="imp.choose">Choisir un fichier…</button>
        <span class="imp-filename" id="imp-file-name"></span>
        <input type="file" id="file-briefing" accept=".json,application/json" hidden>
      </div>
    </div>
    <div class="imp-block">
      <h3 data-i18n="imp.flights">Vols à importer</h3>
      <div class="export-png-list" id="imp-list"></div>
    </div>
    <div class="export-png-actions-bottom">
      <button type="button" class="export-png-back" id="imp-cancel" data-i18n="imp.cancel">Annuler</button>
      <button type="button" class="export-png-go" id="imp-go" data-i18n="imp.go">Importer</button>
    </div>
  </div>
</div>

<!-- ===== APP ===== -->
<div class="app" id="app">
  <aside class="editor" id="editor">
    <div class="pack-bar" id="pack-bar"></div>
    <div id="ed-sections"></div>
  </aside>
  <main class="preview-wrap" id="preview-wrap">
    <div class="dc-warn" id="dc-warn" role="alert" hidden></div>
    <div id="preview"></div>
  </main>
</div>

<!-- ===== ONGLETS (tablette) ===== -->
<nav class="tab-bar" id="tab-bar" role="tablist" aria-label="Datacard Generator" data-i18n-aria-label="app.title">
  <button type="button" data-tab="meta" role="tab" data-i18n="sec.meta">Méta</button>
  <button type="button" data-tab="flight" role="tab" data-i18n="sec.flight">Vol</button>
  <button type="button" data-tab="mission" role="tab" data-i18n="sec.mission">Mission</button>
  <button type="button" data-tab="times" role="tab" data-i18n="sec.times">Horaires</button>
  <button type="button" data-tab="crew" role="tab" data-i18n="sec.crew">Équipages</button>
  <button type="button" data-tab="nav" role="tab" data-i18n="sec.nav">Navigation</button>
  <button type="button" data-tab="radio" role="tab" data-i18n="sec.radio">Radio</button>
  <button type="button" data-tab="fields" role="tab" data-i18n="sec.fields">Terrains</button>
  <button type="button" data-tab="weather" role="tab" data-i18n="sec.weather">Météo</button>
  <button type="button" data-tab="fuel" role="tab" data-i18n="sec.fuel">Carburant et emport</button>
  <button type="button" data-tab="threats" role="tab" data-i18n="sec.threats">Menaces et notes</button>
  <button type="button" data-tab="preview" role="tab" data-i18n="sec.preview">Aperçu</button>
</nav>

<div class="toast" id="toast" role="status" aria-live="polite"></div>
<div id="print-root" aria-hidden="true"></div>
<div id="measure-root" aria-hidden="true"></div>

<script>
__APP_JS__
</script>

</body>
</html>
"""

JS = r"""
'use strict';

/* =====================================================
   DATACARD GENERATOR v1.0.0
   Une datacard d'une page par vol, pour le kneeboard.
   Monofichier, hors ligne : aucune dépendance externe.
   ===================================================== */

const KEY_STATE = 'datacard_state_v1';
const KEY_THEME = 'theme_v1';
const KEY_LANG = 'lang_v1';
const KEY_BRIEFING = ['kh', 'r26_briefing_state_v2'].join('');   // clé du Briefing Generator, lecture seule : le briefing en cours
const KEY_WING = 'wing_config_v1';                // lecture seule : indicatifs des escadrons
const FORMAT_ID = 'dcs-datacard-v1';
const THEME_IDS = ['cw-nato', 'cw-soviet', 'modern-nato', 'modern-east'];
const MOBILE_BREAKPOINT = 1100;
const PAGE_W = 1000;
const PAGE_H = 1414;

const LIMITS = { steps: 8, times: 8, crew: 6, nav: 30, radios: 4, channels: 12, fields: 5, loadout: 8, threats: 12 };

const CLASSIF_KEYS = ['confidential', 'secret', 'top-secret', 'unclassified', 'nato-restricted', 'nato-secret'];
const CLASSIF_LEGACY_MAP = {
  'CONFIDENTIEL DÉFENSE': 'confidential',
  'SECRET DÉFENSE':       'secret',
  'TRÈS SECRET':          'top-secret',
  'NON CLASSIFIÉ':        'unclassified',
  'NATO RESTRICTED':      'nato-restricted',
  'NATO SECRET':          'nato-secret'
};
const THREAT_LEGACY_MAP = {
  'Faible':    'low',
  'Modéré':    'moderate',
  'Élevé':     'high',
  'eleve':     'high',
  'Danger':    'high',
  'Important': 'high',
  'Critique':  'high'
};
const THREAT_KEYS = ['', 'low', 'moderate', 'high'];
const UNIT_CHOICES = { mass: ['kg', 'lb'], distance: ['km', 'nm'], altitude: ['m', 'ft'] };
const SECTION_IDS = ['meta', 'flight', 'mission', 'times', 'crew', 'nav', 'radio', 'fields', 'weather', 'fuel', 'threats'];
const TAB_IDS = SECTION_IDS.concat(['preview']);

/* Contenu du bouton « Exemple » (document dcs-datacard-v1) */
const EXAMPLE_DOC = __EXAMPLE_DOC__;

/* ============= i18n FR / EN ============= */
const I18N = {
  fr: {
    'app.title': 'Datacard Generator',
    'tb.mode.day': 'Day',
    'tb.mode.night': 'Night',
    'tb.mode.tip': 'Version de jour ou de nuit de la datacard',
    'tb.briefing': 'Depuis le briefing',
    'tb.briefing.short': 'Briefing',
    'tb.json.import': 'Importer JSON',
    'tb.json.export': 'Exporter JSON',
    'tb.export': 'Exporter',
    'tb.example': 'Exemple',
    'tb.example.tip': 'Charger la datacard d\'exemple (remplace le document en cours)',
    'tb.reset': 'Reset',
    'tb.reset.tip': 'Vider le document (repartir d\'une carte blanche)',
    'tb.theme.tip': 'Thème graphique',
    'tb.lang.tip': 'Switch language / Changer de langue',
    'theme.cw-nato': 'Cold War OTAN',
    'theme.cw-soviet': 'Cold War Soviétique',
    'theme.modern-nato': 'OTAN moderne',
    'theme.modern-east': 'Bloc Est moderne',
    'modal.close': 'Fermer',
    'ex.pdf': 'PDF (impression)',
    'ex.png': 'PNG (kneeboard)',
    'ex.pages': 'Pages à exporter',
    'ex.all': 'Tout cocher',
    'ex.none': 'Tout décocher',
    'ex.back': '← Retour',
    'ex.page': 'Page',
    'ex.progress': 'Génération {i}/{n}…',
    'ex.error': 'Erreur d\'export : ',
    'toast.pngOne': 'PNG exporté ✓',
    'toast.pngMany': '{n} PNG exportés ✓',
    'imp.title': 'Importer depuis le Briefing Generator',
    'imp.src.current': 'Briefing en cours',
    'imp.src.currentOff': 'Aucun briefing enregistré dans ce navigateur.',
    'imp.src.file': 'Fichier JSON du briefing',
    'imp.choose': 'Choisir un fichier…',
    'imp.flights': 'Vols à importer',
    'imp.empty': 'Ce briefing ne contient aucun vol.',
    'imp.go': 'Importer',
    'imp.cancel': 'Annuler',
    'toast.imported': '{n} datacard(s) importée(s) ✓',
    'toast.jsonSaved': 'Datacards enregistrées ✓',
    'toast.jsonLoaded': 'Datacards chargées ✓',
    'err.json': 'Fichier non reconnu.',
    'confirm.json': 'Remplacer les datacards en cours ?',
    'confirm.example': 'Remplacer le document en cours par l\'exemple ?',
    'toast.example': 'Exemple chargé ✓',
    'confirm.reset': 'Vider toutes les datacards ?',
    'toast.reset': 'Document vidé ✓',
    'confirm.delete': 'Supprimer cette datacard ?',
    'pack.title': 'Datacard {n} / {N}',
    'pack.add': 'Ajouter',
    'pack.dup': 'Dupliquer',
    'pack.del': 'Supprimer',
    'pack.prev': 'Datacard précédente',
    'pack.next': 'Datacard suivante',
    'pack.up': 'Monter la datacard',
    'pack.down': 'Descendre la datacard',
    'li.up': 'Monter',
    'li.down': 'Descendre',
    'li.del': 'Supprimer',
    'warn.overflow': 'Contenu tronqué : la page 1 déborde même sans la navigation.',
    'sec.meta': 'Méta',
    'sec.flight': 'Vol',
    'sec.mission': 'Mission',
    'sec.times': 'Horaires',
    'sec.crew': 'Équipages',
    'sec.nav': 'Navigation',
    'sec.radio': 'Radio',
    'sec.fields': 'Terrains',
    'sec.weather': 'Météo',
    'sec.fuel': 'Carburant et emport',
    'sec.threats': 'Menaces et notes',
    'sec.preview': 'Aperçu',
    'f.classification': 'Classification',
    'f.docRef': 'Référence',
    'f.operation': 'Opération',
    'f.mission': 'Mission',
    'f.date': 'Date',
    'f.time': 'Heure',
    'f.callsign': 'Indicatif',
    'f.aircraft': 'Appareil',
    'f.count': 'Nombre',
    'f.task': 'Tâche',
    'f.threat': 'Menace',
    'f.mass': 'Masse',
    'f.distance': 'Distance',
    'f.altitude': 'Altitude',
    'thr.none': '—',
    'thr.low': 'Faible',
    'thr.moderate': 'Modérée',
    'thr.high': 'Élevée',
    'f.objective': 'Objectif',
    'f.steps': 'Étapes',
    'f.crew.callsign': 'Indicatif',
    'f.crew.pilot': 'Pilote',
    'f.crew.crew': 'Équipier',
    'f.crew.board': 'N° de bord',
    'f.nav.name': 'Point',
    'f.nav.course': 'Cap',
    'f.nav.distance': 'Distance',
    'f.nav.altitude': 'Altitude',
    'f.nav.tos': 'Heure',
    'f.nav.note': 'Note',
    'f.radio.name': 'Poste',
    'f.radio.channel': 'Canal',
    'f.radio.label': 'Usage',
    'f.radio.frequency': 'Fréquence',
    'f.radio.modulation': 'Modulation',
    'f.field.role': 'Rôle',
    'f.field.icao': 'OACI',
    'f.field.name': 'Nom',
    'f.field.runway': 'Piste',
    'f.field.frequency': 'Fréquence',
    'role.none': '—',
    'f.metar': 'METAR',
    'f.wind': 'Vent',
    'f.visibility': 'Visibilité',
    'f.qnh': 'QNH',
    'f.clouds': 'Nuages',
    'f.joker': 'Joker',
    'f.bingo': 'Bingo',
    'f.loadout': 'Emport',
    'f.threats': 'Menaces',
    'f.notes': 'Notes',
    'add.step': '+ Ajouter une étape',
    'add.time': '+ Ajouter un horaire',
    'add.crew': '+ Ajouter un équipage',
    'add.point': '+ Ajouter un point',
    'add.radio': '+ Ajouter un poste',
    'add.channel': '+ Ajouter un canal',
    'add.field': '+ Ajouter un terrain',
    'add.line': '+ Ajouter une ligne',
    'add.threat': '+ Ajouter une menace',
    'times.d1': 'Mise en route',
    'times.d2': 'Décollage',
    'times.d3': 'IP',
    'times.d4': 'TOT',
    'times.d5': 'RTB',
    'radio.default': 'Fréquences',
    'classif.confidential': 'CONFIDENTIEL DÉFENSE',
    'classif.secret': 'SECRET DÉFENSE',
    'classif.top-secret': 'TRÈS SECRET',
    'classif.unclassified': 'NON CLASSIFIÉ',
    'classif.nato-restricted': 'NATO RESTRICTED',
    'classif.nato-secret': 'NATO SECRET',
    'u.kg': 'kg',
    'u.lb': 'lb',
    'u.km': 'km',
    'u.nm': 'NM',
    'u.m': 'm',
    'u.ft': 'ft',
    'dc.title': 'DATACARD',
    'dc.b.mission': 'MISSION',
    'dc.b.times': 'HORAIRES',
    'dc.b.crew': 'ÉQUIPAGES',
    'dc.b.nav': 'NAVIGATION',
    'dc.b.radio': 'RADIO',
    'dc.b.fields': 'TERRAINS',
    'dc.b.weather': 'MÉTÉO',
    'dc.b.fuel': 'CARBURANT',
    'dc.b.loadout': 'EMPORT',
    'dc.b.threats': 'MENACES',
    'dc.b.notes': 'NOTES',
    'dc.page2': 'DATACARD · NAVIGATION',
    'dc.flightOf': 'VOL DE {n}',
    'dc.operation': 'OPÉRATION {op}',
    'dc.thr.low': 'MENACE FAIBLE',
    'dc.thr.moderate': 'MENACE MODÉRÉE',
    'dc.thr.high': 'MENACE ÉLEVÉE',
    'dc.h.callsign': 'INDICATIF',
    'dc.h.pilot': 'PILOTE',
    'dc.h.crew': 'ÉQUIPIER',
    'dc.h.board': 'N°',
    'dc.h.point': 'POINT',
    'dc.h.course': 'CAP °',
    'dc.h.dist': 'DIST {u}',
    'dc.h.alt': 'ALT {u}',
    'dc.h.tos': 'TOS',
    'dc.h.note': 'NOTE',
    'dc.h.ch': 'CH',
    'dc.h.use': 'USAGE',
    'dc.h.freq': 'FRÉQ',
    'dc.h.icao': 'OACI',
    'dc.h.name': 'NOM',
    'dc.h.rwy': 'PISTE',
    'dc.role.dep': 'DEP',
    'dc.role.arr': 'ARR',
    'dc.role.alt': 'ALT',
    'dc.w.wind': 'VENT',
    'dc.w.vis': 'VIS',
    'dc.w.qnh': 'QNH',
    'dc.w.clouds': 'NUAGES',
    'dc.w.calm': 'CALME',
    'dc.joker': 'JOKER',
    'dc.bingo': 'BINGO',
    'm01': 'JAN', 'm02': 'FÉV', 'm03': 'MAR', 'm04': 'AVR', 'm05': 'MAI', 'm06': 'JUN',
    'm07': 'JUL', 'm08': 'AOÛ', 'm09': 'SEP', 'm10': 'OCT', 'm11': 'NOV', 'm12': 'DÉC'
  },
  en: {
    'app.title': 'Datacard Generator',
    'tb.mode.day': 'Day',
    'tb.mode.night': 'Night',
    'tb.mode.tip': 'Day or night version of the datacard',
    'tb.briefing': 'From briefing',
    'tb.briefing.short': 'Briefing',
    'tb.json.import': 'Import JSON',
    'tb.json.export': 'Export JSON',
    'tb.export': 'Export',
    'tb.example': 'Example',
    'tb.example.tip': 'Load the example datacard (replaces the current document)',
    'tb.reset': 'Reset',
    'tb.reset.tip': 'Clear the document (start from a blank card)',
    'tb.theme.tip': 'Graphic theme',
    'tb.lang.tip': 'Switch language / Changer de langue',
    'theme.cw-nato': 'Cold War NATO',
    'theme.cw-soviet': 'Cold War Soviet',
    'theme.modern-nato': 'Modern NATO',
    'theme.modern-east': 'Modern East Bloc',
    'modal.close': 'Close',
    'ex.pdf': 'PDF (print)',
    'ex.png': 'PNG (kneeboard)',
    'ex.pages': 'Pages to export',
    'ex.all': 'Check all',
    'ex.none': 'Uncheck all',
    'ex.back': '← Back',
    'ex.page': 'Page',
    'ex.progress': 'Generating {i}/{n}…',
    'ex.error': 'Export error: ',
    'toast.pngOne': 'PNG exported ✓',
    'toast.pngMany': '{n} PNGs exported ✓',
    'imp.title': 'Import from the Briefing Generator',
    'imp.src.current': 'Current briefing',
    'imp.src.currentOff': 'No briefing saved in this browser.',
    'imp.src.file': 'Briefing JSON file',
    'imp.choose': 'Choose a file…',
    'imp.flights': 'Flights to import',
    'imp.empty': 'This briefing has no flights.',
    'imp.go': 'Import',
    'imp.cancel': 'Cancel',
    'toast.imported': '{n} datacard(s) imported ✓',
    'toast.jsonSaved': 'Datacards saved ✓',
    'toast.jsonLoaded': 'Datacards loaded ✓',
    'err.json': 'Unrecognised file.',
    'confirm.json': 'Replace the current datacards?',
    'confirm.example': 'Replace the current document with the example?',
    'toast.example': 'Example loaded ✓',
    'confirm.reset': 'Clear all datacards?',
    'toast.reset': 'Document cleared ✓',
    'confirm.delete': 'Delete this datacard?',
    'pack.title': 'Datacard {n} / {N}',
    'pack.add': 'Add',
    'pack.dup': 'Duplicate',
    'pack.del': 'Delete',
    'pack.prev': 'Previous datacard',
    'pack.next': 'Next datacard',
    'pack.up': 'Move datacard up',
    'pack.down': 'Move datacard down',
    'li.up': 'Move up',
    'li.down': 'Move down',
    'li.del': 'Delete',
    'warn.overflow': 'Content truncated: page 1 overflows even without navigation.',
    'sec.meta': 'Meta',
    'sec.flight': 'Flight',
    'sec.mission': 'Mission',
    'sec.times': 'Times',
    'sec.crew': 'Crew',
    'sec.nav': 'Navigation',
    'sec.radio': 'Radio',
    'sec.fields': 'Airfields',
    'sec.weather': 'Weather',
    'sec.fuel': 'Fuel and loadout',
    'sec.threats': 'Threats and notes',
    'sec.preview': 'Preview',
    'f.classification': 'Classification',
    'f.docRef': 'Reference',
    'f.operation': 'Operation',
    'f.mission': 'Mission',
    'f.date': 'Date',
    'f.time': 'Time',
    'f.callsign': 'Callsign',
    'f.aircraft': 'Aircraft',
    'f.count': 'Count',
    'f.task': 'Task',
    'f.threat': 'Threat',
    'f.mass': 'Mass',
    'f.distance': 'Distance',
    'f.altitude': 'Altitude',
    'thr.none': '—',
    'thr.low': 'Low',
    'thr.moderate': 'Moderate',
    'thr.high': 'High',
    'f.objective': 'Objective',
    'f.steps': 'Steps',
    'f.crew.callsign': 'Callsign',
    'f.crew.pilot': 'Pilot',
    'f.crew.crew': 'Crew',
    'f.crew.board': 'Board no.',
    'f.nav.name': 'Point',
    'f.nav.course': 'Heading',
    'f.nav.distance': 'Distance',
    'f.nav.altitude': 'Altitude',
    'f.nav.tos': 'Time',
    'f.nav.note': 'Note',
    'f.radio.name': 'Radio',
    'f.radio.channel': 'Channel',
    'f.radio.label': 'Use',
    'f.radio.frequency': 'Frequency',
    'f.radio.modulation': 'Modulation',
    'f.field.role': 'Role',
    'f.field.icao': 'ICAO',
    'f.field.name': 'Name',
    'f.field.runway': 'Runway',
    'f.field.frequency': 'Frequency',
    'role.none': '—',
    'f.metar': 'METAR',
    'f.wind': 'Wind',
    'f.visibility': 'Visibility',
    'f.qnh': 'QNH',
    'f.clouds': 'Clouds',
    'f.joker': 'Joker',
    'f.bingo': 'Bingo',
    'f.loadout': 'Loadout',
    'f.threats': 'Threats',
    'f.notes': 'Notes',
    'add.step': '+ Add step',
    'add.time': '+ Add time',
    'add.crew': '+ Add crew member',
    'add.point': '+ Add point',
    'add.radio': '+ Add radio',
    'add.channel': '+ Add channel',
    'add.field': '+ Add airfield',
    'add.line': '+ Add line',
    'add.threat': '+ Add threat',
    'times.d1': 'Start-up',
    'times.d2': 'Take-off',
    'times.d3': 'IP',
    'times.d4': 'TOT',
    'times.d5': 'RTB',
    'radio.default': 'Frequencies',
    'classif.confidential': 'CONFIDENTIAL',
    'classif.secret': 'SECRET',
    'classif.top-secret': 'TOP SECRET',
    'classif.unclassified': 'UNCLASSIFIED',
    'classif.nato-restricted': 'NATO RESTRICTED',
    'classif.nato-secret': 'NATO SECRET',
    'u.kg': 'kg',
    'u.lb': 'lb',
    'u.km': 'km',
    'u.nm': 'NM',
    'u.m': 'm',
    'u.ft': 'ft',
    'dc.title': 'DATACARD',
    'dc.b.mission': 'MISSION',
    'dc.b.times': 'TIMES',
    'dc.b.crew': 'CREW',
    'dc.b.nav': 'NAVIGATION',
    'dc.b.radio': 'RADIO',
    'dc.b.fields': 'AIRFIELDS',
    'dc.b.weather': 'WEATHER',
    'dc.b.fuel': 'FUEL',
    'dc.b.loadout': 'LOADOUT',
    'dc.b.threats': 'THREATS',
    'dc.b.notes': 'NOTES',
    'dc.page2': 'DATACARD · NAVIGATION',
    'dc.flightOf': 'FLIGHT OF {n}',
    'dc.operation': 'OPERATION {op}',
    'dc.thr.low': 'THREAT LOW',
    'dc.thr.moderate': 'THREAT MODERATE',
    'dc.thr.high': 'THREAT HIGH',
    'dc.h.callsign': 'CALLSIGN',
    'dc.h.pilot': 'PILOT',
    'dc.h.crew': 'CREW',
    'dc.h.board': 'NO.',
    'dc.h.point': 'POINT',
    'dc.h.course': 'HDG °',
    'dc.h.dist': 'DIST {u}',
    'dc.h.alt': 'ALT {u}',
    'dc.h.tos': 'TOS',
    'dc.h.note': 'NOTE',
    'dc.h.ch': 'CH',
    'dc.h.use': 'USE',
    'dc.h.freq': 'FREQ',
    'dc.h.icao': 'ICAO',
    'dc.h.name': 'NAME',
    'dc.h.rwy': 'RWY',
    'dc.role.dep': 'DEP',
    'dc.role.arr': 'ARR',
    'dc.role.alt': 'ALT',
    'dc.w.wind': 'WIND',
    'dc.w.vis': 'VIS',
    'dc.w.qnh': 'QNH',
    'dc.w.clouds': 'CLOUDS',
    'dc.w.calm': 'CALM',
    'dc.joker': 'JOKER',
    'dc.bingo': 'BINGO',
    'm01': 'JAN', 'm02': 'FEB', 'm03': 'MAR', 'm04': 'APR', 'm05': 'MAY', 'm06': 'JUN',
    'm07': 'JUL', 'm08': 'AUG', 'm09': 'SEP', 'm10': 'OCT', 'm11': 'NOV', 'm12': 'DEC'
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
  document.querySelectorAll('[data-i18n-aria-label]').forEach(el => { el.setAttribute('aria-label', t(el.dataset.i18nAriaLabel)); });
  document.title = t('app.title');
}

function updateFlagButton() {
  const btn = document.getElementById('btn-lang');
  if (!btn) return;
  btn.textContent = CURRENT_LANG === 'fr' ? '🇬🇧' : '🇫🇷';
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
function clone(o) { return JSON.parse(JSON.stringify(o)); }
function pad2(n) { return String(n).padStart(2, '0'); }

function showToast(msg) {
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.classList.add('show');
  clearTimeout(showToast._h);
  showToast._h = setTimeout(() => el.classList.remove('show'), 2200);
}

/* ============= MODÈLE ============= */
function defaultTimes() {
  return ['d1', 'd2', 'd3', 'd4', 'd5'].map(k => ({ label: t('times.' + k), value: '' }));
}

function newCard() {
  return {
    meta: { classification: 'confidential', docRef: '', operation: '', mission: '', date: '', time: '' },
    flight: { callsign: '', aircraft: '', count: null, task: '', threat: '' },
    units: { mass: 'kg', distance: 'km', altitude: 'm' },
    mission: { objective: '', execution: [] },
    times: defaultTimes(),
    crew: [],
    nav: [],
    radios: [],
    fields: [],
    weather: { metar: '', wind: '', visibility: '', qnh: '', clouds: '' },
    fuel: { joker: '', bingo: '' },
    loadout: [],
    threats: [],
    notes: ''
  };
}

function newDoc() { return { format: FORMAT_ID, mode: 'day', cards: [newCard()] }; }

function normClassif(v, fallback) {
  const s = str(v);
  if (CLASSIF_KEYS.indexOf(s) !== -1) return s;
  const m = CLASSIF_LEGACY_MAP[s];
  return m || fallback;
}

function normCount(v) {
  if (typeof v === 'number' || typeof v === 'string') {
    const n = parseInt(v, 10);
    if (Number.isInteger(n) && n >= 1) return n;
  }
  return null;
}

function normStrList(arr, max) {
  return arr.slice(0, max).map(str);
}

/* Fusion d'une carte lue sur une carte neuve : champ absent → valeur neuve ; champ inconnu → ignoré. */
function normalizeCard(src) {
  const c = newCard();
  if (!src || typeof src !== 'object') return c;
  const meta = src.meta;
  if (meta && typeof meta === 'object') {
    ['docRef', 'operation', 'mission', 'date', 'time'].forEach(k => { if (k in meta) c.meta[k] = str(meta[k]); });
    if ('classification' in meta) c.meta.classification = normClassif(meta.classification, c.meta.classification);
  }
  const fl = src.flight;
  if (fl && typeof fl === 'object') {
    ['callsign', 'aircraft', 'task'].forEach(k => { if (k in fl) c.flight[k] = str(fl[k]); });
    if ('count' in fl) c.flight.count = normCount(fl.count);
    if ('threat' in fl) c.flight.threat = THREAT_KEYS.indexOf(fl.threat) !== -1 ? fl.threat : '';
  }
  const un = src.units;
  if (un && typeof un === 'object') {
    Object.keys(UNIT_CHOICES).forEach(k => { if (k in un && UNIT_CHOICES[k].indexOf(un[k]) !== -1) c.units[k] = un[k]; });
  }
  const mi = src.mission;
  if (mi && typeof mi === 'object') {
    if ('objective' in mi) c.mission.objective = str(mi.objective);
    if (Array.isArray(mi.execution)) c.mission.execution = normStrList(mi.execution, LIMITS.steps);
  }
  if (Array.isArray(src.times)) {
    c.times = src.times.slice(0, LIMITS.times).map(o => ({ label: str(o && o.label), value: str(o && o.value) }));
  }
  if (Array.isArray(src.crew)) {
    c.crew = src.crew.slice(0, LIMITS.crew).map(o => ({ callsign: str(o && o.callsign), pilot: str(o && o.pilot), crew: str(o && o.crew), board: str(o && o.board) }));
  }
  if (Array.isArray(src.nav)) {
    c.nav = src.nav.slice(0, LIMITS.nav).map(o => ({
      name: str(o && o.name), course: str(o && o.course), distance: str(o && o.distance),
      altitude: str(o && o.altitude), tos: str(o && o.tos), note: str(o && o.note)
    }));
  }
  if (Array.isArray(src.radios)) {
    c.radios = src.radios.slice(0, LIMITS.radios).map(r => ({
      name: str(r && r.name),
      channels: Array.isArray(r && r.channels)
        ? r.channels.slice(0, LIMITS.channels).map(ch => ({
            channel: str(ch && ch.channel), label: str(ch && ch.label),
            frequency: str(ch && ch.frequency), modulation: str(ch && ch.modulation)
          }))
        : []
    }));
  }
  if (Array.isArray(src.fields)) {
    c.fields = src.fields.slice(0, LIMITS.fields).map(f => ({
      role: (f && ['', 'dep', 'arr', 'alt'].indexOf(f.role) !== -1) ? f.role : '',
      icao: str(f && f.icao), name: str(f && f.name), runway: str(f && f.runway), frequency: str(f && f.frequency)
    }));
  }
  const we = src.weather;
  if (we && typeof we === 'object') {
    ['metar', 'wind', 'visibility', 'qnh', 'clouds'].forEach(k => { if (k in we) c.weather[k] = str(we[k]); });
  }
  const fu = src.fuel;
  if (fu && typeof fu === 'object') {
    ['joker', 'bingo'].forEach(k => { if (k in fu) c.fuel[k] = str(fu[k]); });
  }
  if (Array.isArray(src.loadout)) c.loadout = normStrList(src.loadout, LIMITS.loadout);
  if (Array.isArray(src.threats)) c.threats = normStrList(src.threats, LIMITS.threats);
  if ('notes' in src) c.notes = str(src.notes);
  return c;
}

function normalizeDoc(src) {
  const d = { format: FORMAT_ID, mode: 'day', cards: [] };
  if (src && typeof src === 'object') {
    if (src.mode === 'night') d.mode = 'night';
    if (Array.isArray(src.cards)) d.cards = src.cards.map(normalizeCard);
  }
  if (!d.cards.length) d.cards = [newCard()];
  return d;
}

/* Une carte « neuve et intacte » : aucune valeur saisie (les libellés d'horaires par défaut ne comptent pas). */
function isBlankCard(c) {
  const n = newCard();
  const a = clone(c), b = clone(n);
  a.times = a.times.map(x => ({ label: '', value: x.value }));
  b.times = b.times.map(x => ({ label: '', value: x.value }));
  return JSON.stringify(a) === JSON.stringify(b);
}
function isBlankDoc(d) { return d.cards.length === 1 && isBlankCard(d.cards[0]); }

/* ============= ÉTAT ============= */
let doc = newDoc();
let curIdx = 0;

function curCard() { return doc.cards[curIdx]; }

function persistState() {
  try { localStorage.setItem(KEY_STATE, JSON.stringify(doc)); } catch (e) { /* quota ou stockage indisponible */ }
}

function loadState() {
  try {
    const raw = localStorage.getItem(KEY_STATE);
    if (raw) { doc = normalizeDoc(JSON.parse(raw)); curIdx = 0; return; }
  } catch (e) { /* état illisible : document neuf */ }
  doc = newDoc();
  curIdx = 0;
}

function setDoc(next) {
  doc = next;
  curIdx = 0;
  persistState();
  renderAll();
}

/* ============= DATE, METAR ============= */
/* « AAAA-MM-JJ » → « JJ MMM AAAA » ; toute autre forme s'affiche telle quelle. */
function fmtDate(s) {
  const v = str(s);
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(v.trim());
  if (!m) return v;
  const mo = parseInt(m[2], 10), d = parseInt(m[3], 10);
  if (mo < 1 || mo > 12 || d < 1 || d > 31) return v;
  return m[3] + ' ' + t('m' + m[2]) + ' ' + m[1];
}

/* Décodage d'un METAR : vent, visibilité, QNH, première couche de nuages. */
function decodeMetar(raw) {
  const out = { wind: '', visibility: '', qnh: '', clouds: '', any: false };
  const parts = str(raw).trim().toUpperCase().split(/\s+/).filter(Boolean);
  let sawVis = false;
  for (let i = 0; i < parts.length; i++) {
    const p = parts[i];
    let m;
    if (!out.wind && (m = /^(\d{3}|VRB)(\d{2,3})(?:G(\d{2,3}))?KT$/.exec(p))) {
      if (parseInt(m[2], 10) === 0) out.wind = t('dc.w.calm');
      else out.wind = m[1] === 'VRB' ? 'VRB/' + m[2] : m[1] + '/' + m[2] + (m[3] ? 'G' + m[3] : '');
    } else if (p === 'CAVOK') {
      if (!out.visibility) out.visibility = 'CAVOK';
      if (!out.clouds) out.clouds = 'CAVOK';
      sawVis = true;
    } else if (!sawVis && /^\d{4}$/.test(p)) {
      const n = parseInt(p, 10);
      out.visibility = n >= 9999 ? '≥ 10 km' : (n < 5000 ? n + ' m' : (n / 1000) + ' km');
      sawVis = true;
    } else if (!out.clouds && (m = /^(FEW|SCT|BKN|OVC)(\d{3})/.exec(p))) {
      out.clouds = m[1] + ' ' + (parseInt(m[2], 10) * 100) + ' ft';
    } else if (!out.qnh && (m = /^Q(\d{4})$/.exec(p))) {
      out.qnh = m[1] + ' hPa';
    } else if (!out.qnh && (m = /^A(\d{2})(\d{2})$/.exec(p))) {
      out.qnh = m[1] + '.' + m[2] + ' inHg';
    }
  }
  out.any = !!(out.wind || out.visibility || out.qnh || out.clouds);
  return out;
}

/* ============= IMPORT DEPUIS UN BRIEFING ============= */
function normalizeThreatLevel(lvl) {
  if (!lvl) return '';
  if (lvl === 'low' || lvl === 'moderate' || lvl === 'high') return lvl;
  if (THREAT_LEGACY_MAP[lvl]) return THREAT_LEGACY_MAP[lvl];
  const k = String(lvl).toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '');
  if (k.includes('elev') || k.includes('danger') || k.includes('important') || k.includes('critiqu')) return 'high';
  if (k.includes('moder')) return 'moderate';
  return 'low';
}

function readJsonKey(key) {
  try {
    const raw = localStorage.getItem(key);
    if (!raw) return null;
    const v = JSON.parse(raw);
    return (v && typeof v === 'object') ? v : null;
  } catch (e) { return null; }
}

/* Le briefing enregistré par le Briefing Generator, en lecture seule. */
function readCurrentBriefing() {
  const b = readJsonKey(KEY_BRIEFING);
  return (b && Array.isArray(b.phases)) ? b : null;
}

function isBriefingObject(o) {
  return !!(o && typeof o === 'object' && !Array.isArray(o) && o.meta && typeof o.meta === 'object' && Array.isArray(o.phases) && !('format' in o));
}

function wingSquadron(id) {
  const w = readJsonKey(KEY_WING);
  if (!w || !Array.isArray(w.squadrons)) return null;
  return w.squadrons.find(s => s && s.id === id) || null;
}

function sameText(a, b) {
  return str(a).replace(/\s+/g, '').toLowerCase() === str(b).replace(/\s+/g, '').toLowerCase();
}

/* Indicatif, appareil et clé de groupe d'équipage d'un vol du briefing. */
function phaseIdentity(ph) {
  const guest = ph.squadron === '__guest__';
  const g = (guest && ph.guestSquadron && typeof ph.guestSquadron === 'object') ? ph.guestSquadron : {};
  const sq = (!guest && ph.squadron) ? wingSquadron(ph.squadron) : null;
  let callsign = '';
  if (hasText(ph.subgroup)) callsign = ph.subgroup.trim();
  else if (guest && hasText(g.subgroup)) callsign = g.subgroup.trim();
  else if (guest && hasText(g.name)) callsign = g.name.trim();
  else if (sq && hasText(sq.callsign)) callsign = sq.callsign.trim();
  else callsign = str(ph.squadron).trim();
  const aircraft = guest ? str(g.aircraft).trim() : str(ph.aircraft).trim();
  /* Clé de groupe : escadron || sous-groupe || appareil, comme les groupes de mission du briefing */
  let id, sub, ac;
  if (guest) {
    id = hasText(g.name) ? g.name : '?';
    sub = hasText(ph.subgroup) ? ph.subgroup : str(g.subgroup);
    ac = hasText(g.aircraft) ? g.aircraft : '?';
  } else {
    id = str(ph.squadron);
    sub = str(ph.subgroup);
    ac = hasText(ph.aircraft) ? ph.aircraft : ((sq && Array.isArray(sq.aircraft) && sq.aircraft.length) ? str(sq.aircraft[0]) : '');
  }
  return { callsign, aircraft, key: id + '||' + sub + '||' + ac };
}

function crewGroupFor(b, key) {
  const groups = (b.roster && Array.isArray(b.roster.groups)) ? b.roster.groups : [];
  const g = groups.find(x => x && x.missionKey === key);
  return (g && Array.isArray(g.pilots)) ? g.pilots : [];
}

function radiosFromBriefing(b, aircraft) {
  const rp = (b.radioPlan && typeof b.radioPlan === 'object') ? b.radioPlan : {};
  const items = Array.isArray(rp.items) ? rp.items.filter(x => x && typeof x === 'object') : [];
  const plans = Array.isArray(rp.aircraftPlans) ? rp.aircraftPlans : [];
  const plan = hasText(aircraft) ? plans.find(p => p && sameText(p.aircraft, aircraft)) : null;
  if (plan) {
    const byId = {};
    items.forEach(it => { byId[it.id] = it; });
    const radios = [];
    (Array.isArray(plan.radios) ? plan.radios : []).forEach(r => {
      if (!r || typeof r !== 'object') return;
      const channels = [];
      (Array.isArray(r.channels) ? r.channels : []).forEach(ch => {
        if (!ch || typeof ch !== 'object') return;
        if (ch.channel === '' || ch.channel == null) return;
        if (ch.mode === 'custom') {
          if (!(hasText(ch.frequency) || hasText(ch.label))) return;
          channels.push({ channel: str(ch.channel), label: str(ch.label), frequency: str(ch.frequency), modulation: str(ch.modulation) });
        } else {
          const it = byId[ch.itemId];
          if (!it) return;
          channels.push({ channel: str(ch.channel), label: str(it.label), frequency: str(it.frequency), modulation: str(it.modulation) });
        }
      });
      if (hasText(r.name) || channels.length) radios.push({ name: str(r.name), channels: channels.slice(0, LIMITS.channels) });
    });
    return radios.slice(0, LIMITS.radios);
  }
  const all = items.filter(it => hasText(it.label) || hasText(it.frequency))
    .map(it => ({ channel: '', label: str(it.label), frequency: str(it.frequency), modulation: str(it.modulation) }));
  return all.length ? [{ name: t('radio.default'), channels: all.slice(0, LIMITS.channels) }] : [];
}

function splitThreats(s) {
  return str(s).split(/[,;]/).map(x => x.trim()).filter(Boolean);
}

/* La datacard d'un vol (phase) d'un briefing. Elle vit ensuite seule : aucun lien avec le briefing. */
function cardFromPhase(b, ph) {
  const c = newCard();
  const meta = (b.meta && typeof b.meta === 'object') ? b.meta : {};
  c.meta.classification = normClassif(meta.classification, 'confidential');
  ['docRef', 'operation', 'mission', 'date', 'time'].forEach(k => { c.meta[k] = str(meta[k]); });

  const idn = phaseIdentity(ph);
  c.flight.callsign = idn.callsign;
  c.flight.aircraft = idn.aircraft;
  let count = normCount(ph.count);
  const pilots = crewGroupFor(b, idn.key);
  if (count == null && pilots.length) count = pilots.length;
  c.flight.count = count;
  c.flight.task = str(ph.title);
  c.flight.threat = ph.threatLevel ? normalizeThreatLevel(ph.threatLevel) : '';

  c.mission.objective = str(ph.objective);
  c.mission.execution = (Array.isArray(ph.execution) ? ph.execution : []).map(s => {
    if (typeof s === 'string') return s;
    const text = str(s && s.text);
    const subs = (s && Array.isArray(s.subtasks)) ? s.subtasks.map(str).filter(x => x !== '') : [];
    return subs.length ? text + ' — ' + subs.join(' · ') : text;
  }).filter(hasText).slice(0, LIMITS.steps);

  c.crew = pilots.slice(0, LIMITS.crew).map(p => ({ callsign: str(p && p.callsign), pilot: str(p && p.name), crew: '', board: '' }));
  c.radios = radiosFromBriefing(b, idn.aircraft);

  const mi = (b.mission && typeof b.mission === 'object') ? b.mission : {};
  const farp = Array.isArray(mi.farp) ? mi.farp : [];
  const dep = str(ph.departure).trim();
  let depFound = false;
  let fields = farp.filter(f => f && typeof f === 'object').map(f => {
    let role = '';
    if (dep && !depFound && (sameText(f.icao, dep) || sameText(f.name, dep))) { role = 'dep'; depFound = true; }
    return { role, icao: str(f.icao), name: str(f.name), runway: str(f.rwy), frequency: '' };
  });
  if (dep && !depFound) fields.unshift({ role: 'dep', icao: dep, name: '', runway: '', frequency: '' });
  c.fields = fields.slice(0, LIMITS.fields);

  const si = (b.sitac && typeof b.sitac === 'object') ? b.sitac : {};
  c.weather.metar = str(si.metar);
  const dm = decodeMetar(c.weather.metar);
  c.weather.wind = dm.wind; c.weather.visibility = dm.visibility; c.weather.qnh = dm.qnh; c.weather.clouds = dm.clouds;

  const th = (mi.threats && typeof mi.threats === 'object') ? mi.threats : {};
  c.threats = splitThreats(th.sam).concat(splitThreats(th.aaa)).slice(0, LIMITS.threats);
  c.notes = str(ph.notes);
  return c;
}

/* Libellé d'un vol dans la liste d'import : « indicatif · appareil · tâche » */
function phaseLabel(ph) {
  const idn = phaseIdentity(ph);
  return [idn.callsign, idn.aircraft, str(ph.title).trim()].filter(hasText).join(' · ');
}

/* ============= RENDU DE LA DATACARD ============= */
function dash(v) { return hasText(v) ? esc(v) : '—'; }
function classifLabel(c) { return t('classif.' + c.meta.classification); }
function unitLabel(c, kind) { return t('u.' + c.units[kind]); }

function anyText(o, keys) { return keys.some(k => hasText(o[k])); }
function navRows(c) { return c.nav.filter(r => anyText(r, ['name', 'course', 'distance', 'altitude', 'tos', 'note'])); }

function blockHtml(name, title, bodyHtml, bodyClass) {
  return '<section class="dc-block" data-block="' + name + '"><h3 class="dc-bh">' + esc(title) + '</h3>' +
    '<div class="' + (bodyClass || 'dc-bb') + '">' + bodyHtml + '</div></section>';
}

function blkMission(c) {
  const obj = c.mission.objective.trim();
  const steps = c.mission.execution.filter(hasText);
  if (!obj && !steps.length) return '';
  let b = '';
  if (obj) b += '<p class="dc-obj">' + esc(obj) + '</p>';
  if (steps.length) {
    b += '<ol class="dc-steps">' + steps.map((s, i) =>
      '<li><span class="n">' + (i + 1) + '.</span><span class="x">' + esc(s) + '</span></li>').join('') + '</ol>';
  }
  return blockHtml('mission', t('dc.b.mission'), b);
}

function blkTimes(c) {
  const rows = c.times.filter(x => hasText(x.value));
  if (!rows.length) return '';
  const b = '<div class="dc-times">' + rows.map(x =>
    '<div class="dc-trow"><span class="dc-tl">' + esc(x.label) + '</span><span class="dc-tv">' + esc(x.value) + '</span></div>').join('') + '</div>';
  return blockHtml('times', t('dc.b.times'), b);
}

function blkCrew(c) {
  const rows = c.crew.filter(r => anyText(r, ['callsign', 'pilot', 'crew', 'board']));
  if (!rows.length) return '';
  const withCrew = rows.some(r => hasText(r.crew));
  const cols = withCrew
    ? '<col style="width:36%"><col style="width:26%"><col style="width:26%"><col>'
    : '<col style="width:42%"><col style="width:42%"><col>';
  let h = '<th>' + esc(t('dc.h.callsign')) + '</th><th>' + esc(t('dc.h.pilot')) + '</th>';
  if (withCrew) h += '<th>' + esc(t('dc.h.crew')) + '</th>';
  h += '<th>' + esc(t('dc.h.board')) + '</th>';
  const body = rows.map(r =>
    '<tr><td class="nm">' + esc(r.callsign) + '</td><td class="m">' + esc(r.pilot) + '</td>' +
    (withCrew ? '<td class="m">' + esc(r.crew) + '</td>' : '') +
    '<td class="m">' + esc(r.board) + '</td></tr>').join('');
  return blockHtml('crew', t('dc.b.crew'),
    '<table class="dc-tab dc-crew"><colgroup>' + cols + '</colgroup><thead><tr>' + h + '</tr></thead><tbody>' + body + '</tbody></table>', 'dc-bbt');
}

function blkNav(c) {
  const rows = navRows(c);
  if (!rows.length) return '';
  const du = unitLabel(c, 'distance'), au = unitLabel(c, 'altitude');
  const head = '<th>#</th><th>' + esc(t('dc.h.point')) + '</th>' +
    '<th class="r">' + esc(t('dc.h.course')) + '</th>' +
    '<th class="r">' + esc(t('dc.h.dist', { u: du })) + '</th>' +
    '<th class="r">' + esc(t('dc.h.alt', { u: au })) + '</th>' +
    '<th class="r">' + esc(t('dc.h.tos')) + '</th>' +
    '<th>' + esc(t('dc.h.note')) + '</th>';
  const body = rows.map((r, i) =>
    '<tr><td class="m ix">' + i + '</td><td class="nm">' + esc(r.name) + '</td>' +
    '<td class="m r">' + dash(r.course) + '</td><td class="m r">' + dash(r.distance) + '</td>' +
    '<td class="m r">' + dash(r.altitude) + '</td><td class="m r">' + dash(r.tos) + '</td>' +
    '<td class="nt">' + esc(r.note) + '</td></tr>').join('');
  return blockHtml('nav', t('dc.b.nav'),
    '<table class="dc-tab dc-nav"><colgroup><col style="width:50px"><col style="width:288px"><col style="width:90px"><col style="width:108px"><col style="width:89px"><col style="width:136px"><col></colgroup>' +
    '<thead><tr>' + head + '</tr></thead><tbody>' + body + '</tbody></table>', 'dc-bbt');
}

function blkRadio(c) {
  const radios = c.radios.map(r => ({
    name: r.name,
    ch: r.channels.filter(x => anyText(x, ['channel', 'label', 'frequency', 'modulation']))
  })).filter(r => hasText(r.name) || r.ch.length);
  if (!radios.length) return '';
  let b = '<div class="dc-rhead"><span class="h1">' + esc(t('dc.h.ch')) + '</span><span class="h2">' + esc(t('dc.h.use')) +
    '</span><span class="h3">' + esc(t('dc.h.freq')) + '</span></div>';
  b += radios.map(r => {
    let s = '<div class="dc-radio">';
    if (hasText(r.name)) s += '<div class="dc-rname">' + esc(r.name) + '</div>';
    if (r.ch.length) {
      s += '<table class="dc-tab"><colgroup><col style="width:58px"><col style="width:196px"><col style="width:160px"><col></colgroup><tbody>' +
        r.ch.map(x =>
          '<tr><td class="m">' + dash(x.channel) + '</td><td class="us">' + esc(x.label) + '</td>' +
          '<td class="m fq">' + dash(x.frequency) + '</td><td class="md">' + esc(x.modulation) + '</td></tr>').join('') +
        '</tbody></table>';
    }
    return s + '</div>';
  }).join('');
  return blockHtml('radio', t('dc.b.radio'), b, 'dc-bbt');
}

function blkFields(c) {
  const rows = c.fields.filter(f => anyText(f, ['icao', 'name', 'runway', 'frequency']));
  if (!rows.length) return '';
  const body = rows.map(f =>
    '<tr><td class="ro">' + (f.role ? esc(t('dc.role.' + f.role)) : '') + '</td><td class="m">' + dash(f.icao) + '</td>' +
    '<td class="nm">' + esc(f.name) + '</td><td class="m">' + dash(f.runway) + '</td><td class="m">' + dash(f.frequency) + '</td></tr>').join('');
  return blockHtml('fields', t('dc.b.fields'),
    '<table class="dc-tab dc-fields"><colgroup><col style="width:56px"><col style="width:76px"><col><col style="width:54px"><col style="width:104px"></colgroup>' +
    '<thead><tr><th></th><th>' + esc(t('dc.h.icao')) + '</th><th>' + esc(t('dc.h.name')) + '</th><th>' + esc(t('dc.h.rwy')) + '</th><th>' + esc(t('dc.h.freq')) + '</th></tr></thead>' +
    '<tbody>' + body + '</tbody></table>', 'dc-bbt');
}

function blkWeather(c) {
  const w = c.weather;
  const vals = [['dc.w.wind', w.wind], ['dc.w.vis', w.visibility], ['dc.w.qnh', w.qnh], ['dc.w.clouds', w.clouds]];
  const hasV = vals.some(v => hasText(v[1]));
  if (!hasText(w.metar) && !hasV) return '';
  const cell = v => hasText(v[1])
    ? '<td class="wl">' + esc(t(v[0])) + '</td><td class="wv">' + esc(v[1]) + '</td>'
    : '<td class="wl"></td><td class="wv"></td>';
  let b = '';
  if (hasText(w.metar)) b += '<div class="dc-metar">' + esc(w.metar) + '</div>';
  if (hasV) {
    let rows = '';
    if (hasText(w.wind) || hasText(w.visibility)) rows += '<tr>' + cell(vals[0]) + cell(vals[1]) + '</tr>';
    if (hasText(w.qnh) || hasText(w.clouds)) rows += '<tr>' + cell(vals[2]) + cell(vals[3]) + '</tr>';
    b += '<table class="dc-wtab"><tbody>' + rows + '</tbody></table>';
  }
  return blockHtml('weather', t('dc.b.weather'), b);
}

function blkFuel(c) {
  const fuelRows = [['dc.joker', c.fuel.joker], ['dc.bingo', c.fuel.bingo]].filter(r => hasText(r[1]));
  const load = c.loadout.filter(hasText);
  if (!fuelRows.length && !load.length) return '';
  const mu = unitLabel(c, 'mass');
  let b = '<div class="dc-fuelwrap">';
  if (fuelRows.length) {
    b += '<div class="dc-fuel">' + fuelRows.map(r =>
      '<div class="dc-frow"><span class="fl">' + esc(t(r[0])) + '</span><span class="fv">' + esc(r[1].trim() + ' ' + mu) + '</span></div>').join('') + '</div>';
  }
  if (load.length) {
    b += '<ul class="dc-load">' + load.map(l => '<li><span class="bl">▪</span><span class="lx">' + esc(l) + '</span></li>').join('') + '</ul>';
  }
  b += '</div>';
  const title = [fuelRows.length ? t('dc.b.fuel') : '', load.length ? t('dc.b.loadout') : ''].filter(Boolean).join(' · ');
  return blockHtml('fuel', title, b);
}

function blkThreats(c) {
  const th = c.threats.filter(hasText);
  const notes = c.notes.trim();
  if (!th.length && !notes) return '';
  let b = '';
  if (th.length) b += '<div class="dc-chips">' + th.map(x => '<span class="dc-chip">' + esc(x) + '</span>').join('') + '</div>';
  if (notes) b += '<div class="dc-notes">' + esc(notes) + '</div>';
  const title = [th.length ? t('dc.b.threats') : '', notes ? t('dc.b.notes') : ''].filter(Boolean).join(' · ');
  return blockHtml('threats', title, b);
}

function rowHtml(cls, cells) {
  const live = cells.filter(Boolean);
  if (!live.length) return '';
  return '<div class="dc-row ' + cls + (live.length > 1 ? ' dc-two' : '') + '">' + live.join('') + '</div>';
}

function headMain(c) {
  const f = c.flight, m = c.meta;
  const n = f.count;
  const sub = [
    f.aircraft.trim(),
    n != null ? t('dc.flightOf', { n: n }) : '',
    f.task.trim().toUpperCase()
  ].filter(hasText).join(' · ');
  const op = [hasText(m.operation) ? t('dc.operation', { op: m.operation.trim() }) : '', m.mission.trim()].filter(hasText).join(' · ');
  const dt = [fmtDate(m.date).trim(), m.time.trim()].filter(hasText).join(' · ');
  let r = '<div class="dc-ttl">' + esc(t('dc.title')) + '</div>';
  if (op) r += '<div class="dc-op">' + esc(op) + '</div>';
  if (dt) r += '<div class="dc-dt">' + esc(dt) + '</div>';
  if (f.threat) r += '<div class="dc-pill thr-' + f.threat + '">' + esc(t('dc.thr.' + f.threat)) + '</div>';
  return '<div class="dc-head"><div class="dc-hl"><div class="dc-cs">' + esc(f.callsign.trim()) + '</div><div class="dc-sub">' + esc(sub) +
    '</div></div><div class="dc-hr">' + r + '</div></div>';
}

function headNav(c) {
  return '<div class="dc-head dc-head2"><div class="dc-hl"><div class="dc-cs">' + esc(c.flight.callsign.trim()) + '</div></div>' +
    '<div class="dc-hr"><div class="dc-ttl">' + esc(t('dc.page2')) + '</div></div></div>';
}

/* Une page de datacard. kind : 'main' (page 1) ou 'nav' (page de navigation). */
function pageHtml(c, mode, p, N, kind, withNav) {
  const cls = esc(classifLabel(c));
  const pg = p + ' / ' + N;
  const top = '<div class="dc-top"><span>' + cls + '</span><span>' + esc(c.meta.docRef.trim()) + '</span><span>' + pg + '</span></div>';
  const opm = [c.meta.operation.trim(), c.meta.mission.trim()].filter(hasText).join(' ');
  const footL = [t('dc.title'), c.flight.callsign.trim(), opm].filter(hasText).join(' · ');
  const foot = '<div class="dc-foot"><span>' + esc(footL) + '</span><span>' + cls + '</span><span>' + pg + '</span></div>';
  let head, body;
  if (kind === 'nav') {
    head = headNav(c);
    body = rowHtml('dc-r3', [blkNav(c)]);
  } else {
    head = headMain(c);
    const fields = blkFields(c), weather = blkWeather(c);
    const col = (fields || weather) ? '<div class="dc-col">' + fields + weather + '</div>' : '';
    body = rowHtml('dc-r1', [blkMission(c), blkTimes(c)]) +
      rowHtml('dc-r2', [blkCrew(c)]) +
      (withNav ? rowHtml('dc-r3', [blkNav(c)]) : '') +
      rowHtml('dc-r4', [blkRadio(c), col]) +
      rowHtml('dc-r5', [blkFuel(c), blkThreats(c)]);
  }
  return '<article class="dc-page" data-mode="' + mode + '">' + top + head + '<div class="dc-body">' + body + '</div>' + foot + '</article>';
}

/* ----- Découpage en pages : décidé à la mesure du rendu, jamais à un compte de lignes ----- */
const layoutCache = new Map();

function overflowsHtml(html) {
  const m = document.getElementById('measure-root');
  m.innerHTML = html;
  let over = false;
  const b = m.querySelector('.dc-body');
  if (b) {
    const rows = b.querySelectorAll(':scope > .dc-row');
    const last = rows.length ? rows[rows.length - 1] : null;
    if (b.scrollHeight > b.clientHeight + 1) over = true;
    if (last && last.getBoundingClientRect().bottom > b.getBoundingClientRect().bottom - 8) over = true;
  }
  m.innerHTML = '';
  return over;
}

function planCard(c) {
  const key = CURRENT_LANG + '|' + JSON.stringify(c);
  if (layoutCache.has(key)) return layoutCache.get(key);
  const plan = { split: false, overflow: false };
  if (navRows(c).length) {
    if (overflowsHtml(pageHtml(c, 'day', 1, 1, 'main', true))) {
      plan.split = true;
      plan.overflow = overflowsHtml(pageHtml(c, 'day', 1, 2, 'main', false));
    }
  } else {
    plan.overflow = overflowsHtml(pageHtml(c, 'day', 1, 1, 'main', false));
  }
  if (layoutCache.size > 80) layoutCache.clear();
  layoutCache.set(key, plan);
  return plan;
}

/* Les pages d'une carte, dans un mode donné */
function cardPages(c, mode) {
  const plan = planCard(c);
  const pages = plan.split
    ? [pageHtml(c, mode, 1, 2, 'main', false), pageHtml(c, mode, 2, 2, 'nav', false)]
    : [pageHtml(c, mode, 1, 1, 'main', true)];
  return { plan, pages };
}

/* ============= APERÇU ============= */
function renderPreview() {
  const c = curCard();
  const res = cardPages(c, doc.mode);
  document.getElementById('preview').innerHTML = res.pages.map(h => '<div class="dc-sheet">' + h + '</div>').join('');
  const warn = document.getElementById('dc-warn');
  if (res.plan.overflow) { warn.textContent = t('warn.overflow'); warn.hidden = false; }
  else { warn.textContent = ''; warn.hidden = true; }
  applyPreviewScale();
}

function applyPreviewScale() {
  const wrap = document.getElementById('preview-wrap');
  const prev = document.getElementById('preview');
  const cs = getComputedStyle(wrap);
  const avail = wrap.clientWidth - parseFloat(cs.paddingLeft) - parseFloat(cs.paddingRight);
  if (!(avail > 0)) return;
  const s = Math.max(0.2, Math.min(1, avail / PAGE_W));
  prev.style.setProperty('--s', s.toFixed(4));
}

/* ============= ÉDITEUR ============= */
function getPath(obj, path) {
  return path.split('.').reduce((o, k) => (o == null ? undefined : o[k]), obj);
}
function setPath(obj, path, val) {
  const keys = path.split('.');
  let o = obj;
  for (let i = 0; i < keys.length - 1; i++) o = o[keys[i]];
  o[keys[keys.length - 1]] = val;
}

const LIST_SPECS = {
  'mission.execution': { max: LIMITS.steps, make: () => '' },
  'times': { max: LIMITS.times, make: () => ({ label: '', value: '' }) },
  'crew': { max: LIMITS.crew, make: () => ({ callsign: '', pilot: '', crew: '', board: '' }) },
  'nav': { max: LIMITS.nav, make: () => ({ name: '', course: '', distance: '', altitude: '', tos: '', note: '' }) },
  'radios': { max: LIMITS.radios, make: () => ({ name: '', channels: [] }) },
  'radios.*.channels': { max: LIMITS.channels, make: () => ({ channel: '', label: '', frequency: '', modulation: '' }) },
  'fields': { max: LIMITS.fields, make: () => ({ role: '', icao: '', name: '', runway: '', frequency: '' }) },
  'loadout': { max: LIMITS.loadout, make: () => '' },
  'threats': { max: LIMITS.threats, make: () => '' }
};
function listSpec(path) { return LIST_SPECS[path.replace(/\.\d+\./g, '.*.')]; }

function fInput(labelKey, path, value, extra) {
  return '<div class="ed-field"><label>' + esc(t(labelKey)) + '</label><input type="text" data-path="' + path + '" value="' + esc(value) + '"' + (extra || '') + '></div>';
}
function fInputBare(path, value, extra) {
  return '<div class="ed-field"><input type="text" data-path="' + path + '" value="' + esc(value) + '"' + (extra || '') + '></div>';
}
function fArea(labelKey, path, value) {
  return '<div class="ed-field"><label>' + esc(t(labelKey)) + '</label><textarea data-path="' + path + '">' + esc(value) + '</textarea></div>';
}
function fSelect(labelKey, path, value, options) {
  return '<div class="ed-field"><label>' + esc(t(labelKey)) + '</label><select data-path="' + path + '">' +
    options.map(o => '<option value="' + esc(o[0]) + '"' + (o[0] === value ? ' selected' : '') + '>' + esc(o[1]) + '</option>').join('') +
    '</select></div>';
}

function listHtml(path, items, renderItem, addKey) {
  const spec = listSpec(path);
  const rows = items.map((it, i) =>
    '<div class="li" data-list="' + path + '" data-i="' + i + '"><div class="li-main">' + renderItem(it, i) + '</div><div class="li-ctl">' +
    '<button type="button" class="ed-btn-icon neutral" data-act="up" data-list="' + path + '" data-i="' + i + '"' + (i === 0 ? ' disabled' : '') + ' title="' + esc(t('li.up')) + '" aria-label="' + esc(t('li.up')) + '">▲</button>' +
    '<button type="button" class="ed-btn-icon neutral" data-act="down" data-list="' + path + '" data-i="' + i + '"' + (i === items.length - 1 ? ' disabled' : '') + ' title="' + esc(t('li.down')) + '" aria-label="' + esc(t('li.down')) + '">▼</button>' +
    '<button type="button" class="ed-btn-icon" data-act="remove" data-list="' + path + '" data-i="' + i + '" title="' + esc(t('li.del')) + '" aria-label="' + esc(t('li.del')) + '">✕</button>' +
    '</div></div>').join('');
  return '<div class="ed-list">' + rows + '</div>' +
    '<button type="button" class="ed-btn-add" data-act="add" data-list="' + path + '"' + (items.length >= spec.max ? ' disabled' : '') + '>' + esc(t(addKey)) + '</button>';
}

function unitOptions(kind) { return UNIT_CHOICES[kind].map(k => [k, t('u.' + k)]); }

const SECTION_BUILDERS = {
  meta: c =>
    fSelect('f.classification', 'meta.classification', c.meta.classification, CLASSIF_KEYS.map(k => [k, t('classif.' + k)])) +
    fInput('f.docRef', 'meta.docRef', c.meta.docRef) +
    '<div class="ed-field-row">' + fInput('f.operation', 'meta.operation', c.meta.operation) + fInput('f.mission', 'meta.mission', c.meta.mission) + '</div>' +
    '<div class="ed-field-row">' + fInput('f.date', 'meta.date', c.meta.date) + fInput('f.time', 'meta.time', c.meta.time) + '</div>',

  flight: c =>
    '<div class="ed-field-row">' + fInput('f.callsign', 'flight.callsign', c.flight.callsign) + fInput('f.aircraft', 'flight.aircraft', c.flight.aircraft) + '</div>' +
    '<div class="ed-field-row">' + fInput('f.count', 'flight.count', c.flight.count == null ? '' : String(c.flight.count), ' inputmode="numeric"') +
    fSelect('f.threat', 'flight.threat', c.flight.threat, [['', t('thr.none')], ['low', t('thr.low')], ['moderate', t('thr.moderate')], ['high', t('thr.high')]]) + '</div>' +
    fInput('f.task', 'flight.task', c.flight.task) +
    '<div class="ed-field-row three">' +
    fSelect('f.mass', 'units.mass', c.units.mass, unitOptions('mass')) +
    fSelect('f.distance', 'units.distance', c.units.distance, unitOptions('distance')) +
    fSelect('f.altitude', 'units.altitude', c.units.altitude, unitOptions('altitude')) + '</div>',

  mission: c =>
    fArea('f.objective', 'mission.objective', c.mission.objective) +
    '<div class="ed-field"><label>' + esc(t('f.steps')) + '</label></div>' +
    listHtml('mission.execution', c.mission.execution, (s, i) => fInputBare('mission.execution.' + i, s), 'add.step'),

  times: c => listHtml('times', c.times, (x, i) =>
    '<div class="li-grid g2">' + fInputBare('times.' + i + '.label', x.label) + fInputBare('times.' + i + '.value', x.value) + '</div>', 'add.time'),

  crew: c => listHtml('crew', c.crew, (x, i) =>
    '<div class="li-grid g2">' + fInput('f.crew.callsign', 'crew.' + i + '.callsign', x.callsign) + fInput('f.crew.pilot', 'crew.' + i + '.pilot', x.pilot) + '</div>' +
    '<div class="li-grid g2">' + fInput('f.crew.crew', 'crew.' + i + '.crew', x.crew) + fInput('f.crew.board', 'crew.' + i + '.board', x.board) + '</div>', 'add.crew'),

  nav: c => listHtml('nav', c.nav, (x, i) =>
    '<div class="li-grid gs">' + fInput('f.nav.name', 'nav.' + i + '.name', x.name) + '</div>' +
    '<div class="li-grid g3">' + fInput('f.nav.course', 'nav.' + i + '.course', x.course) + fInput('f.nav.distance', 'nav.' + i + '.distance', x.distance) +
    fInput('f.nav.altitude', 'nav.' + i + '.altitude', x.altitude) + '</div>' +
    '<div class="li-grid g2">' + fInput('f.nav.tos', 'nav.' + i + '.tos', x.tos) + fInput('f.nav.note', 'nav.' + i + '.note', x.note) + '</div>', 'add.point'),

  radio: c => listHtml('radios', c.radios, (r, i) =>
    '<div class="li-grid gs">' + fInput('f.radio.name', 'radios.' + i + '.name', r.name) + '</div>' +
    '<div class="li-sub">' + listHtml('radios.' + i + '.channels', r.channels, (ch, j) => {
      const p = 'radios.' + i + '.channels.' + j;
      return '<div class="li-grid g2">' + fInput('f.radio.channel', p + '.channel', ch.channel) + fInput('f.radio.label', p + '.label', ch.label) + '</div>' +
        '<div class="li-grid g2">' + fInput('f.radio.frequency', p + '.frequency', ch.frequency) + fInput('f.radio.modulation', p + '.modulation', ch.modulation) + '</div>';
    }, 'add.channel') + '</div>', 'add.radio'),

  fields: c => listHtml('fields', c.fields, (f, i) =>
    '<div class="li-grid g2">' +
    fSelect('f.field.role', 'fields.' + i + '.role', f.role, [['', t('role.none')], ['dep', t('dc.role.dep')], ['arr', t('dc.role.arr')], ['alt', t('dc.role.alt')]]) +
    fInput('f.field.icao', 'fields.' + i + '.icao', f.icao) + '</div>' +
    '<div class="li-grid gs">' + fInput('f.field.name', 'fields.' + i + '.name', f.name) + '</div>' +
    '<div class="li-grid g2">' + fInput('f.field.runway', 'fields.' + i + '.runway', f.runway) + fInput('f.field.frequency', 'fields.' + i + '.frequency', f.frequency) + '</div>', 'add.field'),

  weather: c =>
    fInput('f.metar', 'weather.metar', c.weather.metar) +
    '<div class="ed-field-row">' + fInput('f.wind', 'weather.wind', c.weather.wind) + fInput('f.visibility', 'weather.visibility', c.weather.visibility) + '</div>' +
    '<div class="ed-field-row">' + fInput('f.qnh', 'weather.qnh', c.weather.qnh) + fInput('f.clouds', 'weather.clouds', c.weather.clouds) + '</div>',

  fuel: c =>
    '<div class="ed-field-row">' + fInput('f.joker', 'fuel.joker', c.fuel.joker) + fInput('f.bingo', 'fuel.bingo', c.fuel.bingo) + '</div>' +
    '<div class="ed-field"><label>' + esc(t('f.loadout')) + '</label></div>' +
    listHtml('loadout', c.loadout, (s, i) => fInputBare('loadout.' + i, s), 'add.line'),

  threats: c =>
    '<div class="ed-field"><label>' + esc(t('f.threats')) + '</label></div>' +
    listHtml('threats', c.threats, (s, i) => fInputBare('threats.' + i, s), 'add.threat') +
    fArea('f.notes', 'notes', c.notes)
};

const openState = {};

function sectionHtml(id, idx, c) {
  const title = pad2(idx + 1) + ' ░ ' + t('sec.' + id);
  return '<details class="ed-section" data-section="' + id + '"' + (openState[id] === false ? '' : ' open') + '>' +
    '<summary>' + esc(title) + '</summary><div class="ed-content"><div class="panel-mobile-header">' + esc(title) + '</div>' +
    SECTION_BUILDERS[id](c) + '</div></details>';
}

function renderEditor() {
  const ed = document.getElementById('editor');
  const top = ed.scrollTop;
  const c = curCard();
  document.getElementById('ed-sections').innerHTML = SECTION_IDS.map((id, i) => sectionHtml(id, i, c)).join('');
  ed.scrollTop = top;
}

function packTitle() {
  const cs = curCard().flight.callsign.trim();
  return t('pack.title', { n: curIdx + 1, N: doc.cards.length }) + (cs ? ' — ' + cs : '');
}
function updatePackTitle() {
  const el = document.getElementById('pack-title');
  if (el) el.textContent = packTitle();
}

function renderPack() {
  const N = doc.cards.length;
  const b = (act, label, extra, disabled) =>
    '<button type="button" class="pack-btn' + (extra || '') + '" data-pack="' + act + '"' + (disabled ? ' disabled' : '') + '>' + esc(label) + '</button>';
  const ico = (act, glyph, key, disabled) =>
    '<button type="button" class="pack-btn" data-pack="' + act + '"' + (disabled ? ' disabled' : '') + ' title="' + esc(t(key)) + '" aria-label="' + esc(t(key)) + '">' + glyph + '</button>';
  document.getElementById('pack-bar').innerHTML =
    '<div class="pack-title" id="pack-title">' + esc(packTitle()) + '</div>' +
    '<div class="pack-btns">' +
    ico('prev', '◄', 'pack.prev', curIdx === 0) + ico('next', '►', 'pack.next', curIdx === N - 1) +
    b('add', t('pack.add')) + b('dup', t('pack.dup')) + b('del', t('pack.del'), ' danger') +
    ico('up', '▲', 'pack.up', curIdx === 0) + ico('down', '▼', 'pack.down', curIdx === N - 1) +
    '</div>';
}

function updateModeSeg() {
  document.querySelectorAll('#mode-seg .seg-btn').forEach(b => {
    const on = b.dataset.mode === doc.mode;
    b.classList.toggle('active', on);
    b.setAttribute('aria-pressed', on ? 'true' : 'false');
  });
}

function renderAll() {
  renderPack();
  renderEditor();
  renderPreview();
  updateModeSeg();
}

/* Toute modification : enregistrement puis aperçu */
function touch() {
  persistState();
  renderPreview();
}

function syncMetar(c) {
  const d = decodeMetar(c.weather.metar);
  if (!d.any) return;
  c.weather.wind = d.wind; c.weather.visibility = d.visibility; c.weather.qnh = d.qnh; c.weather.clouds = d.clouds;
  [['wind', d.wind], ['visibility', d.visibility], ['qnh', d.qnh], ['clouds', d.clouds]].forEach(p => {
    const el = document.querySelector('#editor [data-path="weather.' + p[0] + '"]');
    if (el) el.value = p[1];
  });
}

function onEditorInput(e) {
  const el = e.target;
  const path = el && el.dataset ? el.dataset.path : '';
  if (!path) return;
  if (e.type === 'change' && el.tagName !== 'SELECT') return;
  const c = curCard();
  if (path === 'flight.count') setPath(c, path, normCount(el.value));
  else setPath(c, path, el.value);
  if (path === 'weather.metar') syncMetar(c);
  if (path === 'flight.callsign') updatePackTitle();
  touch();
}

function onEditorClick(e) {
  const btn = e.target.closest('[data-act]');
  if (!btn || btn.disabled) return;
  const act = btn.dataset.act, path = btn.dataset.list, i = parseInt(btn.dataset.i, 10);
  const c = curCard();
  const arr = getPath(c, path);
  const spec = listSpec(path);
  if (!Array.isArray(arr) || !spec) return;
  let focusIdx = -1;
  if (act === 'add') {
    if (arr.length >= spec.max) return;
    arr.push(spec.make());
    focusIdx = arr.length - 1;
  } else if (act === 'remove') {
    arr.splice(i, 1);
  } else if (act === 'up' && i > 0) {
    const tmp = arr[i - 1]; arr[i - 1] = arr[i]; arr[i] = tmp;
  } else if (act === 'down' && i < arr.length - 1) {
    const tmp = arr[i + 1]; arr[i + 1] = arr[i]; arr[i] = tmp;
  } else return;
  renderEditor();
  touch();
  if (focusIdx >= 0) {
    const f = document.querySelector('#editor .li[data-list="' + path + '"][data-i="' + focusIdx + '"] input, #editor .li[data-list="' + path + '"][data-i="' + focusIdx + '"] textarea');
    if (f) f.focus();
  }
}

/* ----- Paquet de datacards ----- */
function onPackClick(e) {
  const btn = e.target.closest('[data-pack]');
  if (!btn || btn.disabled) return;
  const act = btn.dataset.pack;
  const N = doc.cards.length;
  if (act === 'prev' && curIdx > 0) curIdx--;
  else if (act === 'next' && curIdx < N - 1) curIdx++;
  else if (act === 'add') { doc.cards.push(newCard()); curIdx = doc.cards.length - 1; }
  else if (act === 'dup') { doc.cards.splice(curIdx + 1, 0, clone(curCard())); curIdx++; }
  else if (act === 'del') {
    if (!confirm(t('confirm.delete'))) return;
    if (N > 1) { doc.cards.splice(curIdx, 1); if (curIdx >= doc.cards.length) curIdx = doc.cards.length - 1; }
    else doc.cards[0] = newCard();
  } else if (act === 'up' && curIdx > 0) {
    const tmp = doc.cards[curIdx - 1]; doc.cards[curIdx - 1] = doc.cards[curIdx]; doc.cards[curIdx] = tmp; curIdx--;
  } else if (act === 'down' && curIdx < N - 1) {
    const tmp = doc.cards[curIdx + 1]; doc.cards[curIdx + 1] = doc.cards[curIdx]; doc.cards[curIdx] = tmp; curIdx++;
  } else return;
  persistState();
  renderAll();
}

/* ----- Onglets (tablette) ----- */
function setActiveTab(id) {
  if (TAB_IDS.indexOf(id) === -1) id = 'meta';
  document.body.dataset.activeTab = id;
  document.querySelectorAll('#tab-bar button').forEach(b => b.classList.toggle('current', b.dataset.tab === id));
  if (id === 'preview') applyPreviewScale();
  const ed = document.getElementById('editor');
  if (ed) ed.scrollTop = 0;
}

/* ----- Thème de la chrome : n'écrit la clé partagée que sur un choix explicite ----- */
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
  const sel = document.getElementById('theme-select');
  if (sel) sel.value = id;
  if (persist) { try { localStorage.setItem(KEY_THEME, id); } catch (e) { /* ignore */ } }
}

function setLang(lang) {
  if (lang !== 'fr' && lang !== 'en') return;
  if (lang === CURRENT_LANG) return;
  CURRENT_LANG = lang;
  try { localStorage.setItem(KEY_LANG, lang); } catch (e) { /* ignore */ }
  document.documentElement.lang = lang;
  layoutCache.clear();
  applyI18nStatic();
  updateFlagButton();
  renderAll();
  if (!document.getElementById('import-modal').hidden) impRefresh();
}

function setMode(m) {
  if (m !== 'day' && m !== 'night') return;
  doc.mode = m;
  persistState();
  updateModeSeg();
  renderPreview();
}

/* ============= TÉLÉCHARGEMENT ============= */
function stamp() {
  const d = new Date();
  return d.getFullYear() + pad2(d.getMonth() + 1) + pad2(d.getDate()) + '_' + pad2(d.getHours()) + pad2(d.getMinutes()) + pad2(d.getSeconds());
}
function slug(s) {
  const k = str(s).trim().toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/[^a-z0-9]+/g, '_').replace(/^_+|_+$/g, '');
  return k;
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
  const blob = new Blob([JSON.stringify(doc, null, 2)], { type: 'application/json' });
  const cs = slug(curCard().flight.callsign) || 'doc';
  const fname = 'datacard_' + cs + '_' + stamp() + '.json';
  if (navigator.share && navigator.canShare) {
    try {
      const file = new File([blob], fname, { type: 'application/json' });
      if (navigator.canShare({ files: [file] })) {
        navigator.share({ files: [file], title: t('app.title'), text: fname }).catch(() => {
          fallbackDownload(blob, fname, t('toast.jsonSaved'));
        });
        return;
      }
    } catch (e) { /* repli ci-dessous */ }
  }
  fallbackDownload(blob, fname, t('toast.jsonSaved'));
}

/* ============= IMPORT JSON ============= */
function loadJsonFile(file) {
  const reader = new FileReader();
  reader.onload = () => {
    let parsed;
    try { parsed = JSON.parse(reader.result); } catch (e) { showToast(t('err.json')); return; }
    if (isBriefingObject(parsed)) { openImportModal(parsed, file.name); return; }
    if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed) || parsed.format !== FORMAT_ID) { showToast(t('err.json')); return; }
    if (!isBlankDoc(doc) && !confirm(t('confirm.json'))) return;
    setDoc(normalizeDoc(parsed));
    showToast(t('toast.jsonLoaded'));
  };
  reader.onerror = () => showToast(t('err.json'));
  reader.readAsText(file);
}

/* ============= IMPORT DEPUIS UN BRIEFING ============= */
const imp = { src: 'current', fileBriefing: null, fileName: '', current: null };

function impBriefing() {
  return imp.src === 'file' ? imp.fileBriefing : imp.current;
}

function impRefresh() {
  const curRow = document.getElementById('imp-src-current-row');
  const curRadio = document.getElementById('imp-src-current');
  const note = document.getElementById('imp-current-note');
  const off = !imp.current;
  curRow.classList.toggle('off', off);
  curRadio.disabled = off;
  note.hidden = !off;
  note.textContent = off ? t('imp.src.currentOff') : '';
  document.getElementById('imp-src-current').checked = imp.src === 'current';
  document.getElementById('imp-src-file').checked = imp.src === 'file';
  document.getElementById('imp-file-zone').hidden = imp.src !== 'file';
  document.getElementById('imp-file-name').textContent = imp.fileName;
  const b = impBriefing();
  const list = document.getElementById('imp-list');
  const phases = b ? b.phases.filter(p => p && typeof p === 'object') : [];
  if (!phases.length) {
    list.innerHTML = '<div class="imp-empty">' + esc(b ? t('imp.empty') : '') + '</div>';
  } else {
    list.innerHTML = phases.map((ph, i) =>
      '<label class="export-png-page-row"><input type="checkbox" class="export-png-page-cb imp-cb" data-i="' + i + '" checked>' +
      '<span class="export-png-page-num">' + pad2(i + 1) + '</span><span>' + esc(phaseLabel(ph) || '—') + '</span></label>').join('');
  }
  document.getElementById('imp-go').disabled = !phases.length;
}

function openImportModal(fileBriefing, fileName) {
  imp.current = readCurrentBriefing();
  if (fileBriefing) { imp.fileBriefing = fileBriefing; imp.fileName = fileName || ''; imp.src = 'file'; }
  else { imp.src = imp.current ? 'current' : 'file'; if (imp.src === 'file') { imp.fileBriefing = null; imp.fileName = ''; } }
  impRefresh();
  document.getElementById('import-modal').hidden = false;
}
function closeImportModal() { document.getElementById('import-modal').hidden = true; }

function runImport() {
  const b = impBriefing();
  if (!b) return;
  const phases = b.phases.filter(p => p && typeof p === 'object');
  const picked = Array.from(document.querySelectorAll('#imp-list .imp-cb:checked')).map(cb => phases[parseInt(cb.dataset.i, 10)]).filter(Boolean);
  if (!picked.length) return;
  const cards = picked.map(ph => cardFromPhase(b, ph));
  if (isBlankDoc(doc)) { doc.cards = cards; curIdx = 0; }
  else { const first = doc.cards.length; doc.cards = doc.cards.concat(cards); curIdx = first; }
  persistState();
  renderAll();
  closeImportModal();
  showToast(t('toast.imported', { n: cards.length }));
}

function loadBriefingFile(file) {
  const reader = new FileReader();
  reader.onload = () => {
    let parsed;
    try { parsed = JSON.parse(reader.result); } catch (e) { showToast(t('err.json')); return; }
    if (!isBriefingObject(parsed)) { showToast(t('err.json')); return; }
    imp.fileBriefing = parsed; imp.fileName = file.name; imp.src = 'file';
    impRefresh();
  };
  reader.onerror = () => showToast(t('err.json'));
  reader.readAsText(file);
}

/* ============= EXPORT : fenêtre ============= */
function allExportPages() {
  /* Toutes les pages de toutes les cartes, dans le mode affiché. */
  const out = [];
  doc.cards.forEach((c, ci) => {
    const res = cardPages(c, doc.mode);
    const cs = slug(c.flight.callsign) || ('carte' + (ci + 1));
    res.pages.forEach((html, pi) => out.push({ html, card: ci, page: pi + 1, pages: res.pages.length, cs }));
  });
  return out;
}

function openExportModal() {
  document.querySelector('#export-modal .export-modal-choices').hidden = false;
  document.getElementById('export-png-config').hidden = true;
  document.getElementById('export-modal-title').textContent = t('tb.export');
  document.getElementById('export-modal').hidden = false;
}
function closeExportModal() { document.getElementById('export-modal').hidden = true; }

function updatePngCount() {
  const n = document.querySelectorAll('.export-png-page-cb.exp-cb:checked').length;
  document.getElementById('export-png-count').textContent = '(' + n + ')';
  document.getElementById('export-png-go').disabled = n === 0;
}

function showPngConfig() {
  const pages = allExportPages();
  document.getElementById('export-png-list').innerHTML = pages.map((p, i) =>
    '<label class="export-png-page-row"><input type="checkbox" class="export-png-page-cb exp-cb" data-idx="' + i + '" checked>' +
    '<span class="export-png-page-num">' + pad2(i + 1) + '</span><span>' + esc((p.cs.toUpperCase()) + ' — ' + t('ex.page') + ' ' + p.page + '/' + p.pages) + '</span></label>').join('');
  document.querySelector('#export-modal .export-modal-choices').hidden = true;
  document.getElementById('export-png-config').hidden = false;
  updatePngCount();
}

/* ============= EXPORT PNG : 1 000 × 1 414 px ============= */
async function renderPageToPng(html) {
  if (document.fonts && document.fonts.ready) await document.fonts.ready;
  const holder = document.createElement('div');
  holder.style.cssText = 'position:fixed;left:-12000px;top:0;width:1000px;height:1414px;z-index:-1;pointer-events:none;';
  holder.innerHTML = html;
  document.body.appendChild(holder);
  try {
    const el = holder.firstElementChild;
    const canvas = await html2canvas(el, {
      backgroundColor: null,
      logging: false,
      useCORS: true,
      allowTaint: false,
      scale: 1,
      width: PAGE_W,
      height: PAGE_H,
      windowWidth: PAGE_W,
      windowHeight: PAGE_H
    });
    return await new Promise((resolve, reject) => {
      canvas.toBlob(b => (b ? resolve(b) : reject(new Error('canvas'))), 'image/png');
    });
  } finally {
    if (holder.parentNode) holder.parentNode.removeChild(holder);
  }
}

async function executePngExport() {
  const all = allExportPages();
  const idx = Array.from(document.querySelectorAll('.export-png-page-cb.exp-cb:checked')).map(cb => parseInt(cb.dataset.idx, 10));
  const sel = idx.map(i => all[i]).filter(Boolean);
  if (!sel.length) return;
  const goBtn = document.getElementById('export-png-go');
  const original = goBtn.innerHTML;
  goBtn.disabled = true;
  goBtn.setAttribute('aria-busy', 'true');
  /* Deux cartes de même indicatif ne doivent pas écraser leurs noms de fichier */
  const used = {};
  const names = sel.map(p => {
    let base = 'dc_' + p.cs + '_p' + p.page;
    if (used[base]) { used[base]++; base = 'dc_' + p.cs + '_' + used[base] + '_p' + p.page; } else used[base] = 1;
    return base + '.png';
  });
  try {
    if (sel.length === 1) {
      goBtn.textContent = t('ex.progress', { i: 1, n: 1 });
      const blob = await renderPageToPng(sel[0].html);
      closeExportModal();
      fallbackDownload(blob, names[0], t('toast.pngOne'));
    } else {
      const zip = new JSZip();
      for (let i = 0; i < sel.length; i++) {
        const msg = t('ex.progress', { i: i + 1, n: sel.length });
        goBtn.textContent = msg;
        showToast(msg);
        zip.file(names[i], await renderPageToPng(sel[i].html));
      }
      const zipBlob = await zip.generateAsync({ type: 'blob' });
      closeExportModal();
      fallbackDownload(zipBlob, 'datacards_' + stamp() + '.zip', t('toast.pngMany', { n: sel.length }));
    }
  } catch (err) {
    showToast(t('ex.error') + (err && err.message ? err.message : ''));
    console.error('[Export PNG]', err);
  } finally {
    goBtn.innerHTML = original;
    goBtn.removeAttribute('aria-busy');
    updatePngCount();
  }
}

/* ============= EXPORT PDF : impression, une feuille A4 par page ============= */
function fillPrintRoot() {
  const root = document.getElementById('print-root');
  root.innerHTML = allExportPages().map(p => '<div class="dc-psheet" data-mode="' + doc.mode + '">' + p.html + '</div>').join('');
}
function clearPrintRoot() { document.getElementById('print-root').innerHTML = ''; }

function doPrint() {
  closeExportModal();
  setTimeout(() => window.print(), 50);
}

/* ============= EXEMPLE ET RESET ============= */
function loadExample() {
  if (!confirm(t('confirm.example'))) return;
  setDoc(normalizeDoc(clone(EXAMPLE_DOC)));
  showToast(t('toast.example'));
}
function resetDoc() {
  if (!confirm(t('confirm.reset'))) return;
  setDoc(newDoc());
  showToast(t('toast.reset'));
}

/* ============= CÂBLAGE ============= */
function bindEvents() {
  const ed = document.getElementById('editor');
  ed.addEventListener('input', onEditorInput);
  ed.addEventListener('change', onEditorInput);
  ed.addEventListener('click', onEditorClick);
  ed.addEventListener('toggle', e => {
    const d = e.target;
    if (d && d.matches && d.matches('details.ed-section')) openState[d.dataset.section] = d.open;
  }, true);
  document.getElementById('pack-bar').addEventListener('click', onPackClick);

  document.getElementById('mode-seg').addEventListener('click', e => {
    const b = e.target.closest('[data-mode]');
    if (b) setMode(b.dataset.mode);
  });
  document.getElementById('btn-briefing').addEventListener('click', () => openImportModal(null));
  const fileLoad = document.getElementById('file-load');
  document.getElementById('btn-json-import').addEventListener('click', () => { fileLoad.value = ''; fileLoad.click(); });
  fileLoad.addEventListener('change', () => { if (fileLoad.files && fileLoad.files[0]) loadJsonFile(fileLoad.files[0]); });
  document.getElementById('btn-json-export').addEventListener('click', downloadJson);
  document.getElementById('btn-print').addEventListener('click', openExportModal);
  document.getElementById('btn-example').addEventListener('click', loadExample);
  document.getElementById('btn-reset').addEventListener('click', resetDoc);
  document.getElementById('theme-select').addEventListener('change', e => applyTheme(e.target.value, true));
  document.getElementById('btn-lang').addEventListener('click', () => setLang(CURRENT_LANG === 'fr' ? 'en' : 'fr'));

  /* Export */
  document.getElementById('export-modal-backdrop').addEventListener('click', closeExportModal);
  document.getElementById('export-modal-close').addEventListener('click', closeExportModal);
  document.getElementById('export-choice-pdf').addEventListener('click', doPrint);
  document.getElementById('export-choice-png').addEventListener('click', showPngConfig);
  document.getElementById('export-png-back').addEventListener('click', openExportModal);
  document.getElementById('export-png-all').addEventListener('click', () => { document.querySelectorAll('.exp-cb').forEach(cb => { cb.checked = true; }); updatePngCount(); });
  document.getElementById('export-png-none').addEventListener('click', () => { document.querySelectorAll('.exp-cb').forEach(cb => { cb.checked = false; }); updatePngCount(); });
  document.getElementById('export-png-list').addEventListener('change', updatePngCount);
  document.getElementById('export-png-go').addEventListener('click', executePngExport);

  /* Import depuis un briefing */
  document.getElementById('import-modal-backdrop').addEventListener('click', closeImportModal);
  document.getElementById('import-modal-close').addEventListener('click', closeImportModal);
  document.getElementById('imp-cancel').addEventListener('click', closeImportModal);
  document.getElementById('imp-go').addEventListener('click', runImport);
  document.getElementById('imp-src-current').addEventListener('change', () => { imp.src = 'current'; impRefresh(); });
  document.getElementById('imp-src-file').addEventListener('change', () => { imp.src = 'file'; impRefresh(); });
  const fb = document.getElementById('file-briefing');
  document.getElementById('imp-file-btn').addEventListener('click', () => { fb.value = ''; fb.click(); });
  fb.addEventListener('change', () => { if (fb.files && fb.files[0]) loadBriefingFile(fb.files[0]); });

  document.addEventListener('keydown', e => {
    if (e.key !== 'Escape') return;
    if (!document.getElementById('export-modal').hidden) closeExportModal();
    if (!document.getElementById('import-modal').hidden) closeImportModal();
  });

  document.querySelectorAll('#tab-bar button').forEach(b => b.addEventListener('click', () => setActiveTab(b.dataset.tab)));

  window.addEventListener('beforeprint', fillPrintRoot);
  window.addEventListener('afterprint', clearPrintRoot);
  let rz = null;
  window.addEventListener('resize', () => { clearTimeout(rz); rz = setTimeout(applyPreviewScale, 60); });

  /* Le shell règle le thème en posant body[data-theme] : suivre sans réécrire la clé */
  new MutationObserver(() => {
    const sel = document.getElementById('theme-select');
    const cur = document.body.dataset.theme;
    if (sel && cur && sel.value !== cur && THEME_IDS.indexOf(cur) !== -1) sel.value = cur;
  }).observe(document.body, { attributes: true, attributeFilter: ['data-theme'] });
}

/* ============= DÉMARRAGE ============= */
function init() {
  initLang();
  applyTheme(loadTheme(), false);
  applyI18nStatic();
  updateFlagButton();
  loadState();
  bindEvents();
  setActiveTab('meta');
  renderAll();
  /* Les polices embarquées mesurent autrement que les polices de repli : refaire le découpage une fois chargées. */
  if (document.fonts && document.fonts.load) {
    Promise.all([
      document.fonts.load("500 20px 'Oswald'"),
      document.fonts.load("700 20px 'Stardos Stencil'"),
      document.fonts.load("400 20px 'Roboto Mono'")
    ]).then(() => document.fonts.ready).then(() => { layoutCache.clear(); renderPreview(); }).catch(() => {});
  }
}

if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
else init();

"""


# ============================================================
# ASSEMBLAGE
# ============================================================
def build():
    try:
        example = json.loads(EXAMPLE_DOC_JSON)
    except ValueError as e:
        raise SystemExit(f"[ERREUR] Document d'exemple illisible : {e}")
    if example.get('format') != 'dcs-datacard-v1':
        raise SystemExit("[ERREUR] Le document d'exemple n'est pas au format dcs-datacard-v1")
    example_js = json.dumps(example, ensure_ascii=False, indent=2).replace('</', '<\\/')

    js = JS.replace('__EXAMPLE_DOC__', example_js)
    html = HTML
    html = html.replace('__CSS__', CSS)
    html = html.replace('__LIB_HTML2CANVAS__', A['lib_html2canvas'])
    html = html.replace('__LIB_JSZIP__', A['lib_jszip'])
    html = html.replace('__APP_VERSION__', APP_VERSION)
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
