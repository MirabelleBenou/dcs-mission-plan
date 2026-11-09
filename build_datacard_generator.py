#!/usr/bin/env python3
"""Build — DCS Datacard Generator v1.5.1.

Produit dist/dcs_datacard_generator.html : un fichier unique, hors ligne, sans
serveur et sans ressource externe. Les polices et les bibliothèques (html2canvas,
JSZip) viennent d'assets.json, à la racine du dépôt ; la déclinaison magnétique (coefficients IGRF 1900–1985 et WMM 1985–2025, comme DCS)
vient des dossiers igrf/ et wmm/ via magvar_block.py ; les projections des théâtres de DCS viennent de projection_block.py ; les faits du jeu sur les aérodromes
(pistes, radios de tour ; pydcs, LGPL-3.0) viennent d'airfield_facts.json, que export_airfield_facts.py écrit (le build n'a jamais besoin de pydcs).

Usage : python3 build_datacard_generator.py
"""

import json
import os
import re
import shutil
import subprocess
import sys

from magvar_block import build_block as build_magvar_block
from radio_bands_block import build_block as build_radio_bands_block
from radio_block import build_block as build_radio_block
from projection_block import build_block as build_projection_block
from group_store_block import build_block as build_group_store_block
from route_pack_block import build_block as build_route_pack_block
from route_theatre_block import build_block as build_route_theatre_block
from payload_block import build_block as build_payload_block
from import_block import build_block as build_import_block, build_css as build_import_css, build_html as build_import_html
from messages_block import build_block as build_messages_block, build_css as build_messages_css

HERE = os.path.dirname(os.path.abspath(__file__))
APP_VERSION = "1.5.1"
OUT_PATH = os.path.join(HERE, 'dist', 'dcs_datacard_generator.html')
ASSETS_PATH = os.path.join(HERE, 'assets.json')
FACTS_PATH = os.path.join(HERE, 'airfield_facts.json')
ICAO_PATH = os.path.join(HERE, 'airfield_icao.json')


def airfield_facts():
    """Les faits du jeu sur les aérodromes (airfield_facts.json, format dcs-airfield-facts-v1) : { théâtre: [ [nom, lat, lon, pistes, radios], … ] }, vérifiés."""
    if not os.path.isfile(FACTS_PATH):
        raise SystemExit(f"[ERREUR] Entrée manquante : {FACTS_PATH} (airfield_facts.json attendu à la racine du dépôt)")
    with open(FACTS_PATH, encoding='utf-8') as f:
        d = json.load(f)
    if not isinstance(d, dict) or d.get('format') != 'dcs-airfield-facts-v1' or not isinstance(d.get('theatres'), dict):
        raise SystemExit("[ERREUR] airfield_facts.json : le format doit être « dcs-airfield-facts-v1 » avec une table « theatres »")

    def num(v):
        return isinstance(v, (int, float)) and not isinstance(v, bool)
    for th, rows in d['theatres'].items():
        if not isinstance(rows, list):
            raise SystemExit(f"[ERREUR] airfield_facts.json : la liste de {th} est illisible")
        for a in rows:
            ok = (isinstance(a, list) and len(a) == 5 and isinstance(a[0], str) and a[0] != '' and num(a[1]) and num(a[2])
                  and isinstance(a[3], list) and all(isinstance(x, str) and x != '' for x in a[3])
                  and (a[4] is None or (isinstance(a[4], list) and len(a[4]) == 4 and all(isinstance(x, int) and not isinstance(x, bool) and x > 0 for x in a[4]))))
            if not ok:
                raise SystemExit(f"[ERREUR] airfield_facts.json : entrée illisible dans {th} : {a!r}")
    return d['theatres']


def airfield_icao(facts):
    """Les codes OACI d'aujourd'hui des aérodromes (airfield_icao.json, format dcs-airfield-icao-v1) : { théâtre: { nom: OACI } }, vérifiés contre les faits du jeu (facts = airfield_facts()) :
    chaque théâtre et chaque nom sont dans airfield_facts.json, chaque code est de quatre caractères A-Z ou 0-9."""
    if not os.path.isfile(ICAO_PATH):
        raise SystemExit(f"[ERREUR] Entrée manquante : {ICAO_PATH} (airfield_icao.json attendu à la racine du dépôt)")
    with open(ICAO_PATH, encoding='utf-8') as f:
        d = json.load(f)
    if not isinstance(d, dict) or d.get('format') != 'dcs-airfield-icao-v1' or not isinstance(d.get('theatres'), dict):
        raise SystemExit("[ERREUR] airfield_icao.json : le format doit être « dcs-airfield-icao-v1 » avec une table « theatres »")
    for th, codes in d['theatres'].items():
        if th not in facts:
            raise SystemExit(f"[ERREUR] airfield_icao.json : le théâtre « {th} » n'est pas dans airfield_facts.json")
        if not isinstance(codes, dict):
            raise SystemExit(f"[ERREUR] airfield_icao.json : la table de {th} est illisible")
        names = {a[0] for a in facts[th]}
        for name, code in codes.items():
            if name not in names:
                raise SystemExit(f"[ERREUR] airfield_icao.json : {th} : « {name} » n'est pas un aérodrome de ce théâtre dans airfield_facts.json")
            if not isinstance(code, str) or not re.fullmatch(r'[A-Z0-9]{4}', code):
                raise SystemExit(f"[ERREUR] airfield_icao.json : {th} : « {name} » : le code {code!r} n'est pas de quatre caractères A-Z ou 0-9")
    return d['theatres']


def dg_tables():
    """Les trois tables que payload_block.py lit (WEAPON_NAMES, AIRCRAFT_PYLONS, AIRCRAFT_LIMITS), tirées de data/*.json, les mêmes fichiers que ceux du
    Flight Configurator, et réduites aux types du Flight Configurator (PAYLOAD_TYPES de payload_block.py) : rien n'est recopié à la main. Les index de
    pylônes sont renumérotés sur les seuls CLSID gardés ; le nom d'une arme est celui du fichier. Le build s'arrête si un CLSID d'un type du
    Flight Configurator, ou d'un emport (clé « CLSID ») d'un exemple du DG, n'a pas de nom."""
    types = json.loads(re.search(r"const PAYLOAD_TYPES = (\[.*?\]);", build_payload_block()).group(1).replace("'", '"'))
    with open(os.path.join(HERE, 'data', 'aircraft_pylons.json'), encoding='utf-8') as f:
        pyl = json.load(f)
    with open(os.path.join(HERE, 'data', 'weapon_names.json'), encoding='utf-8') as f:
        names = json.load(f)
    with open(os.path.join(HERE, 'data', 'aircraft_limits.json'), encoding='utf-8') as f:
        lim = json.load(f)
    orig = {c: i for i, c in enumerate(pyl['clsids'])}
    idx = {}
    kept_types = {}
    for ty in types:
        if ty not in pyl['types'] or ty not in lim:
            raise SystemExit("[ERREUR] Type du Flight Configurator absent des tables de data/ : " + ty)
        kept_types[ty] = {}
        for n, lst in pyl['types'][ty].items():
            kept_types[ty][n] = [idx.setdefault(pyl['clsids'][i], len(idx)) for i in lst]
    clsids = [c for c, _ in sorted(idx.items(), key=lambda kv: kv[1])]
    nameless = [c for c in clsids if c not in names]
    for ex in (EXAMPLE_DOC_JSON, EXAMPLE_DOC_JSON_EN):
        nameless += [c for c in re.findall(r'"CLSID"\s*:\s*"([^"]*)"', ex) if c not in names and c != '<CLEAN>']
    if nameless:
        raise SystemExit("[ERREUR] CLSID sans nom dans data/weapon_names.json : " + ", ".join(sorted(set(nameless))[:10]))
    pylons = {'clsids': clsids, 'weights': [pyl['weights'][orig[c]] for c in clsids], 'types': kept_types}
    dump = lambda o: json.dumps(o, ensure_ascii=False, separators=(',', ':'))
    out = (dump({c: names[c] for c in sorted(clsids)}), dump(pylons), dump({ty: lim[ty] for ty in types}))
    assert all('</script' not in x.lower() for x in out)
    return out

REQUIRED_ASSETS = ['STARDOS_400', 'STARDOS_700', 'OSWALD_500', 'OSWALD_700', 'ROBOTO_MONO_400', 'lib_html2canvas', 'lib_jszip']

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
          "type": "Mi-24P",
          "board": "41"
        },
        {
          "callsign": "CAESAR 1-2",
          "pilot": "FALCON",
          "type": "Mi-24P",
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

# Même document, en anglais : structure et valeurs numériques identiques à EXAMPLE_DOC_JSON (lot mp-exemples-demarrer).
# Le bouton « Exemple » charge l'un ou l'autre selon la langue de l'interface au moment du clic.
EXAMPLE_DOC_JSON_EN = r'''{
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
        "task": "CAS / Area defence",
        "threat": "high"
      },
      "units": {
        "mass": "kg",
        "distance": "km",
        "altitude": "m"
      },
      "mission": {
        "objective": "An armoured convoy is leaving KARAVOSTASI to retake POLIS: intercept it before it reaches the FARP.",
        "execution": [
          "Take-off POLIS",
          "Coastal route to the IP",
          "Priority SAM / AAA, then APC / MBT",
          "RTB POLIS as per SITAC"
        ]
      },
      "times": [
        {
          "label": "Start-up",
          "value": "09:30"
        },
        {
          "label": "Take-off",
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
          "type": "Mi-24P",
          "board": "41"
        },
        {
          "callsign": "CAESAR 1-2",
          "pilot": "FALCON",
          "type": "Mi-24P",
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
          "note": "Departure"
        },
        {
          "name": "COAST 1",
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
          "note": "Island + river"
        },
        {
          "name": "TGT KARAVOSTASI",
          "course": "118",
          "distance": "9",
          "altitude": "30",
          "tos": "10:12",
          "note": "Coastal axis"
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
              "label": "Group 1",
              "frequency": "127.50",
              "modulation": "AM"
            },
            {
              "channel": "1",
              "label": "Group 2",
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
              "label": "Tactical",
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
        "GSh-30-2 · 250 rounds"
      ],
      "threats": [
        "SA-13",
        "SA-9",
        "MANPADS",
        "ZSU-23-4",
        "BMP-2"
      ],
      "notes": "Landmark: small island + river 8 km from the objective."
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
  font-weight: 400;
  font-display: swap;
  src: url('data:font/woff2;base64,__STARDOS_400__') format('woff2');
}
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
.tb-brand { display: flex; flex-direction: column; line-height: 1.1; gap: 1px; flex-shrink: 0; }
.tb-brand-main {
  font-family: var(--f-stencil);
  font-size: 16px;
  font-weight: 700;
  letter-spacing: 3px;
  text-transform: uppercase;
  white-space: nowrap;
}
.tb-brand-sub {
  font-family: var(--f-ui);
  font-size: 10px;
  letter-spacing: 2px;
  color: var(--khaki-light);
  text-transform: uppercase;
  white-space: nowrap;
}
.tb-sep { width: 1px; height: 28px; background: var(--khaki); opacity: .4; flex-shrink: 0; }
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

/* Le théâtre dans la barre : le libellé et la liste, mêmes règles qu'au Route Planner (.tb-label, .tb-sel) */
.tb-label { font-size: 10px; font-weight: 500; letter-spacing: 1.5px; color: var(--khaki-light); text-transform: uppercase; flex: none; margin-left: 4px; white-space: nowrap; }
.tb-sel {
  font-family: var(--f-ui); font-weight: 700; letter-spacing: 1.5px; font-size: 12px; text-transform: uppercase;
  color: var(--amber); border: 1px solid var(--amber-dark); height: 40px; min-width: 44px;
  padding: 0 30px 0 12px; cursor: pointer; display: inline-flex; align-items: center; justify-content: center; gap: 6px; flex: none; appearance: none; -webkit-appearance: none;
  background: var(--olive-dark) url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='6'%3E%3Cpath d='M1 1l4 4 4-4' fill='none' stroke='%23c0892a' stroke-width='1.5'/%3E%3C/svg%3E") no-repeat right 11px center;
}
.tb-sel:hover, .tb-sel:focus-visible { border-color: var(--amber); outline: none; }
.tb-sel option { background: var(--olive-dark); color: var(--paper); font-weight: 500; }

/* ---------- le menu « Unités » (recopié du Route Planner, lot mp-theatre-unique) : le bouton de la barre et son panneau, au style des listes de la barre (tbm-*) ---------- */
#btn-units { position: relative; color: var(--amber); border-color: var(--amber-dark); padding-right: 12px; }
#btn-units:hover, #btn-units:focus-visible, #btn-units.dsp-open { border-color: var(--amber); }
#btn-units .dsp-chev { width: 10px; height: 6px; }
#btn-units.dsp-open .dsp-chev { transform: rotate(180deg); }
.dsp-panel { max-height: min(80vh, 600px); min-width: 240px; padding-bottom: 6px; }
.dsp-sub { font-family: var(--f-ui); font-weight: 500; font-size: 10px; letter-spacing: 1.8px; text-transform: uppercase; color: var(--khaki); padding: 10px 18px 4px; }
.dsp-sub:not(:first-of-type) { border-top: 1px solid rgba(168,154,114,.25); margin-top: 4px; }
.dsp-opt { outline: none; color: var(--khaki-light); }
.dsp-opt[aria-checked="true"] { color: var(--paper); }
.dsp-opt:focus-visible { background: var(--olive); color: var(--amber); }
.dsp-box { position: relative; width: 15px; height: 15px; flex: none; box-sizing: border-box; border: 1.5px solid var(--khaki); }
.dsp-opt[aria-checked="true"] .dsp-box { background: var(--amber); border-color: var(--amber); }
.dsp-opt[aria-checked="true"] .dsp-box::after { content: ''; position: absolute; left: 3.5px; top: 0.5px; width: 4px; height: 8px; box-sizing: border-box;
  border-right: 2px solid var(--olive-deep); border-bottom: 2px solid var(--olive-deep); transform: rotate(45deg); }
.dsp-opt:hover .dsp-box { border-color: var(--amber); }
.dsp-opt[role="menuitemradio"] .dsp-box { border-radius: 50%; }

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
.tbm-off { display: none !important; }
/* La recherche en tête d'une liste (option data-search du <select>) : collée en haut du panneau qui défile */
.tbm-list { margin: 0; padding: 0; list-style: none; outline: none; }
.tbm-list:focus, .tbm-list:focus-visible { outline: none; }
.tbm-search { position: sticky; top: 0; z-index: 2; padding: 6px 10px; background: var(--olive-dark); border-bottom: 1px solid rgba(168,154,114,.25); }
.tbm-q { display: block; width: 100%; min-height: 36px; box-sizing: border-box; padding: 6px 10px; font-family: var(--f-typewriter); font-size: 14px; letter-spacing: .2px; color: #1f1c16; background: rgba(216, 201, 165, .92); border: 1px solid var(--khaki); border-left: 3px solid var(--amber-dark); border-radius: 0; outline: none; }
.tbm-q:focus { border-left-color: var(--red-stamp); box-shadow: 0 0 0 1px var(--amber); }
.tbm-q::placeholder { color: #6b6450; opacity: 1; }
.tbm-none { margin: 0; padding: 0; list-style: none; cursor: default; }
.tbm-msg { font-family: var(--f-typewriter); font-size: 14px; color: var(--khaki-light); }
.tbm-msg:not(:empty) { padding: 12px 18px; }
@media (prefers-reduced-motion: reduce) { .tbm-panel { animation: none; } }
@media print { .tbm-panel { display: none; } }

/* ---------- Listes des formulaires au thème de l'interface (lot mp-ui-listes-formulaires) ----------
   Le bouton fermé garde la boîte et le texte du <select> du champ ; seul le chevron est dessiné (12 × 8, trait 1,6 px, couleur du texte,
   à 12 px du bord droit, 8 px sur un champ de moins de 120 px). La liste ouverte garde la police, la casse et la graisse du champ. */
.ed-field .tbm-trigger.tbm-field {
  display: block; width: 100%; min-width: 0; min-height: 44px; text-align: left; cursor: pointer; contain: inline-size;
  background: rgba(216, 201, 165, .92) url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='8' viewBox='0 0 12 8'%3E%3Cpath d='M1 1.5l5 5 5-5' fill='none' stroke='%231f1c16' stroke-width='1.6'/%3E%3C/svg%3E") no-repeat right 12px center;
  border: 1px solid var(--khaki); border-left: 3px solid var(--amber-dark);
  font-family: var(--f-typewriter); font-weight: 400; font-size: 13px; color: #1f1c16; padding: 10px 34px 10px 11px;
  transition: all .15s; letter-spacing: normal; text-transform: none; border-radius: 0;
}
.ed-field .tbm-trigger.tbm-field.tbm-narrow { padding-right: 26px; background-position: right 8px center; transition: none; }
.ed-field .tbm-trigger.tbm-field .tbm-lbl { margin: 0; padding: 0; line-height: 22px; }
.ed-field .tbm-trigger.tbm-field .tbm-lbl::after { display: none; }
.ed-field .tbm-trigger.tbm-field:focus-visible,
.ed-field .tbm-trigger.tbm-field.tbm-trigger-open {
  outline: none; border-left-color: var(--red-stamp); background-color: #ece0c2; box-shadow: 0 0 0 1px var(--amber);
  border-top-color: var(--khaki) !important; border-right-color: var(--khaki) !important; border-bottom-color: var(--khaki) !important;
}

.tbm-panel.tbm-p-field { max-width: calc(100vw - 16px); }
.tbm-panel.tbm-p-field .tbm-opt {
  font-family: var(--f-typewriter); font-weight: 400; font-size: 14px; letter-spacing: .2px; text-transform: none;
}
.tbm-panel.tbm-p-field .tbm-opt[aria-selected="true"] { font-weight: 400; }
.tbm-panel.tbm-up { border-top: 1px solid var(--amber-dark); border-bottom: 3px solid var(--amber); transform-origin: bottom left; }
.tb-spacer { flex: 1; min-width: 0; }
.tb-version {
  font-family: var(--f-typewriter);
  font-size: 11px;
  opacity: .45;
  color: var(--amber);
  letter-spacing: .5px;
  user-select: none;
  white-space: nowrap;
  flex-shrink: 0;
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
  min-height: 44px;
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
.ed-navset { margin-bottom: 6px; }
.ed-warn {
  font-family: var(--f-ui);
  font-size: 11px;
  letter-spacing: 1px;
  color: var(--amber);
  border-left: 3px solid var(--red-stamp);
  background: rgba(0, 0, 0, .18);
  padding: 5px 8px;
  margin: 6px 0 8px;
}
.ed-warn[hidden] { display: none; }
.ed-coord { font-family: var(--f-typewriter); font-size: 11px; line-height: 1.35; overflow-wrap: anywhere; }
.ed-coord:empty { display: none; }
.ed-coord.ok { color: var(--khaki-light); }
.ed-coord.bad { color: #e8806a; }
.ed-field input[readonly] { background: rgba(216, 201, 165, .5); color: #4a4636; cursor: not-allowed; }
.ed-field .af-free { margin-top: 6px; }

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
.ed-btn-icon.unit-x { min-width: 44px; min-height: 44px; }
#grp-modal .export-png-back, #grp-modal .export-png-go { min-height: 44px; }
.rc-msg { font-family: var(--f-ui); font-size: 11px; letter-spacing: .6px; color: #ff9d8a; margin-left: 56px; }
.rc-freq input.bad { border-color: #ff9d8a; }
.rc-row.nc .rc-msg { margin-left: 0; }
.rc-row.frz .rc-top { gap: 4px 12px; }
.frz-v { font-family: var(--f-typewriter); font-size: 13px; color: var(--paper); }
.frz-on { font-family: var(--f-ui); font-size: 11px; font-weight: 700; letter-spacing: 1.2px; text-transform: uppercase; color: var(--amber); overflow-wrap: anywhere; }
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
.ed-btn-add.sm { min-height: 44px; padding: 6px 10px; font-size: 11px; }

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
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  text-align: center;
  overflow: hidden;
  white-space: nowrap;
  transition: all .15s;
}
.tab-bar button .tab-ico {
  font-size: 16px;
  line-height: 1;
  font-family: var(--f-stencil);
  font-weight: 700;
}
.tab-bar button.current {
  background: var(--olive);
  color: var(--amber);
  border-color: var(--amber-dark);
}
.tab-bar button:active { transform: translateY(1px); }

@@MESSAGES_CSS@@

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
/* Nom du fichier : le champ (fenêtre « Enregistrer » et panneau PNG) */
.fn-field { margin: 0 0 14px; }
.fn-field .lbl {
  display: block;
  margin-bottom: 4px;
  font-size: 11px;
  letter-spacing: 1px;
  text-transform: uppercase;
  opacity: 0.7;
}
.fn-row { display: flex; align-items: center; gap: 8px; }
.fn-row .in {
  flex: 1 1 auto;
  min-width: 0;
  box-sizing: border-box;
  background: rgba(255, 255, 255, 0.25);
  border: 1px solid #1f1c16;
  border-radius: 2px;
  padding: 8px 10px;
  font-family: inherit;
  font-size: 13px;
  color: inherit;
}
.fn-row .in:focus { outline: 2px solid var(--amber, #c8901f); outline-offset: 1px; }
.fn-ext { flex: none; font-size: 13px; opacity: 0.7; }
.export-modal-choices[hidden] { display: none; }
.bi-block { margin-bottom: 14px; }
.bi-src {
  display: flex; align-items: center; gap: 10px;
  padding: 6px 0;
  font-size: 13px;
  cursor: pointer;
}
.bi-src.off { opacity: .5; cursor: not-allowed; }
.bi-src input { accent-color: var(--amber, #c8901f); }
.bi-note { font-size: 11px; opacity: .75; margin: 0 0 6px 26px; line-height: 1.35; }
.bi-file { display: flex; align-items: center; gap: 10px; margin: 2px 0 6px 26px; font-size: 11px; }
.bi-file[hidden] { display: none; }
.bi-filebtn {
  background: transparent;
  border: 1px solid #1f1c16;
  padding: 4px 10px;
  min-height: 44px;
  font-family: inherit;
  font-size: 11px;
  cursor: pointer;
  color: inherit;
  border-radius: 2px;
}
.bi-filebtn:hover { background: rgba(0, 0, 0, 0.06); border-color: var(--amber, #c8901f); }
.bi-filename { opacity: .75; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.bi-src[hidden] { display: none; }
.bi-groups { border-top: 1px dashed rgba(0, 0, 0, 0.25); padding-top: 10px; }
.bi-groups-note { margin-left: 0; margin-bottom: 8px; }

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
  --dc-sep: rgba(20,19,15,.16);
}
.dc-page[data-mode="night"] {
  --dc-pg: #121310;  --dc-ink: #d6cfb8;  --dc-blk: #1a1b16;  --dc-bd: #3e3f33;
  --dc-bh-bg: #2a2b22;  --dc-bh-fg: #e2d9bf;
  --dc-band-bg: #26271f;  --dc-band-fg: #c9a45a;
  --dc-alt: #202119;  --dc-acc: #c9a45a;
  --dc-hi: #d0604c;  --dc-mod: #c08a2a;  --dc-lo: #7d8f52;
  --dc-dot: #4a4a3e;  --dc-metar: #24251d;  --dc-muted: #9a9378;
  --dc-pill-fg: #f1ecdf;  --dc-rule: #d6cfb8;
  --dc-sep: rgba(214,207,184,.18);
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
  font-synthesis: none;
}
.dc-page * { box-sizing: border-box; margin: 0; padding: 0; }
.dc-page { --dc-fo: 'Oswald', 'Arial Narrow', sans-serif; --dc-fm: 'Roboto Mono', 'Courier New', monospace; --dc-fs: 'Stardos Stencil', 'Impact', sans-serif; }

/* Échelle typographique, graisses, interlettrages, marges et filets : ceux de la maquette validée (lot mp-dg-v1.0.2). */

/* Bandeaux haut et bas */
.dc-top, .dc-foot {
  flex: 0 0 32px;
  height: 32px;
  background: var(--dc-band-bg);
  color: var(--dc-band-fg);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 26px;
  font: 500 15px/32px var(--dc-fo);
  letter-spacing: .14em;
  text-transform: uppercase;
  white-space: nowrap;
}
.dc-top span, .dc-foot span { color: var(--dc-band-fg); }

/* En-tête de la page 1 : 136 px, rangée de tête calée sur le filet */
.dc-head {
  flex: 0 0 136px;
  height: 136px;
  margin-top: 10px;
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  padding: 0 30px 8px 30px;
  border-bottom: 4px solid var(--dc-rule);
  overflow: hidden;
}
.dc-hl { display: flex; flex-direction: column; min-width: 0; flex: 1 1 auto; }
.dc-cs {
  font: 700 76px/.9 var(--dc-fs);
  letter-spacing: .04em;
  color: var(--dc-ink);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  padding: 6px 0 10px 0;
  margin: -6px 0 -10px 0;
}
.dc-sub {
  margin-top: 4px;
  font: 500 20px/1.2 var(--dc-fo);
  letter-spacing: .1em;
  color: var(--dc-ink);
  white-space: nowrap;
  overflow: hidden;
}
.dc-hr {
  display: flex; flex-direction: column; align-items: flex-end; align-self: flex-start;
  flex: 0 0 auto;
  max-width: 470px;
}
.dc-ttl {
  font: 700 34px/1 var(--dc-fs);
  letter-spacing: .16em;
  color: var(--dc-acc);
}
.dc-op {
  margin-top: 4px;
  font: 500 20px/1.25 var(--dc-fo);
  letter-spacing: .08em;
  color: var(--dc-ink);
  white-space: nowrap; overflow: hidden; max-width: 470px;
}
.dc-dt {
  font: 400 22px/1.3 var(--dc-fm);
  color: var(--dc-ink);
  white-space: nowrap; overflow: hidden; max-width: 470px;
}
.dc-pill {
  margin-top: 6px;
  padding: 3px 10px;
  font: 500 17px/1.2 var(--dc-fo);
  letter-spacing: .12em;
  color: var(--dc-pill-fg);
  white-space: nowrap;
}
.dc-pill.thr-high { background: var(--dc-hi); }
.dc-pill.thr-moderate { background: var(--dc-mod); }
.dc-pill.thr-low { background: var(--dc-lo); }
/* En-tête réduit de la page 2 : règles de l'addendum 1 de mp-dg-v1.0.0 (C17), inchangées */
.dc-head.dc-head2 { flex: 0 0 62px; height: 62px; padding: 4px 30px 0 30px; align-items: center; }
.dc-head2 .dc-hl { flex: 1 1 0; min-width: 0; margin-right: 24px; }
.dc-head2 .dc-hr { flex: 0 0 auto; align-self: center; max-width: none; }
.dc-head2 .dc-cs { font-size: 44px; line-height: 54px; height: 54px; letter-spacing: 1px; padding: 0; margin: 0; text-overflow: ellipsis; }
.dc-head2 .dc-ttl { font-size: 32px; line-height: 40px; letter-spacing: 6px; margin-right: -6px; white-space: nowrap; }

/* Grille des rangées */
.dc-body {
  flex: 1 1 auto;
  min-height: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 10px 0 0 0;
}
.dc-row { flex: 0 0 auto; padding: 0 30px; }
.dc-row.dc-two { display: grid; gap: 12px; }
.dc-r1.dc-two { grid-template-columns: minmax(0, 1.55fr) minmax(0, 1fr); }
.dc-r4.dc-two { grid-template-columns: minmax(0, 1.25fr) minmax(0, 1fr); }
.dc-r5.dc-two { grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); }
.dc-row > .dc-block, .dc-row > .dc-col { min-width: 0; }
.dc-col { display: flex; flex-direction: column; gap: 12px; }
.dc-col > .dc-block:last-child { flex: 1 1 auto; }

/* Blocs */
.dc-block {
  border: 2px solid var(--dc-bd);
  background: var(--dc-blk);
  padding: 0 12px 10px 12px;
  min-width: 0;
}
.dc-bh {
  display: block;
  background: var(--dc-bh-bg);
  color: var(--dc-bh-fg);
  margin: 0 -12px 8px -12px;
  padding: 6px 12px;
  font: 500 16px/1 var(--dc-fo);
  letter-spacing: .16em;
  text-transform: uppercase;
  white-space: nowrap;
  overflow: hidden;
}
.dc-bb, .dc-bbt { min-width: 0; }

/* Mission */
.dc-obj { font: 500 19px/1.35 var(--dc-fo); letter-spacing: .02em; margin-bottom: 6px; white-space: pre-line; overflow-wrap: anywhere; }
.dc-steps { list-style: none; }
.dc-steps li { display: flex; font: 500 19px/1.4 var(--dc-fo); letter-spacing: .03em; }
.dc-steps .n { flex: 0 0 26px; text-align: right; padding-right: 4px; }
.dc-steps .x { flex: 1 1 auto; min-width: 0; overflow-wrap: anywhere; }

/* Horaires */
.dc-times { display: grid; gap: 4px; }
.dc-trow {
  display: flex; justify-content: space-between; align-items: baseline; gap: 8px;
  border-bottom: 1px dotted var(--dc-dot);
  padding: 2px;
}
.dc-tl {
  font: 500 15px/1 var(--dc-fo); letter-spacing: .12em; text-transform: uppercase;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis; flex: 1 1 auto; min-width: 0;
}
.dc-tv { font: 400 28px/1.05 var(--dc-fm); white-space: nowrap; flex: 0 0 auto; }

/* Tableaux */
.dc-tab { width: 100%; border-collapse: collapse; table-layout: fixed; }
.dc-tab th {
  font: 500 13px/1 var(--dc-fo); letter-spacing: .1em;
  text-align: left; padding: 4px 6px; opacity: .75;
  white-space: nowrap; overflow: hidden;
}
.dc-tab td {
  font: 400 22px/1.2 var(--dc-fm); padding: 3px 6px;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.dc-tab .r { text-align: right; }
.dc-tab tbody tr:nth-child(even) td { background: var(--dc-alt); }

/* Équipages */
.dc-crew td.nm { font-family: var(--dc-fo); font-weight: 500; letter-spacing: .05em; }

/* Navigation */
.dc-navc td.cc { font-size: 20px; letter-spacing: .02em; text-align: left; text-overflow: clip; }
.dc-navc th.cc { text-align: left; }
.dc-navc th:nth-child(5), .dc-navc td:nth-child(5) { padding-left: 18px; }
.dc-navc th:nth-child(6), .dc-navc td:nth-child(6) { padding-left: 14px; }
.dc-nav td.nm { font-family: var(--dc-fo); font-weight: 500; font-size: 21px; letter-spacing: .04em; }
.dc-nav td.nt { font-family: var(--dc-fo); font-weight: 500; font-size: 17px; opacity: .85; }

/* Radio : rangées alternées recommencées à chaque poste, filet plein entre deux postes */
.dc-radio td.us { font-family: var(--dc-fo); font-weight: 500; font-size: 18px; letter-spacing: .05em; text-transform: uppercase; }
.dc-radio td.fq { font-size: 24px; }
.dc-radio td.md { font-size: 14px; opacity: .7; }
.dc-radio tr.rsep td { font: 500 15px/1 var(--dc-fo); letter-spacing: .12em; color: var(--dc-acc); padding-top: 8px; background: none !important; }
.dc-radio tbody tr:nth-child(even) td { background: none; }
.dc-radio tbody tr.z td { background: var(--dc-alt); }
.dc-radio tr.rsep-n td, .dc-radio tr.pn td { border-top: 1px solid var(--dc-dot); padding-top: 10px; }

/* Page Radios : chaque poste, ses canaux sur 3 colonnes */
.dc-rposte-n { margin-top: 12px; padding-top: 4px; border-top: 1px solid var(--dc-dot); }
.dc-rname { font: 500 15px/1 var(--dc-fo); letter-spacing: .12em; color: var(--dc-acc); padding: 8px 0 4px 0; }
.dc-rcols { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 0 14px; align-items: start; }
.dc-rcols > div { min-width: 0; }
.dc-radio3 th, .dc-radio3 td { padding-left: 4px; padding-right: 4px; }
.dc-radio3 td { padding-top: 2px; padding-bottom: 2px; }
.dc-rheads { margin-bottom: 2px; }
.dc-radio3 td.fq { text-overflow: clip; }

/* Terrains : aucun texte coupé (lot mp-dg-terrains-liste). Les colonnes suivent leur contenu (tableau en largeur automatique, aucune largeur fixée : les largeurs de <col> du balisage sont des repères, celles-ci priment) :
   le rôle ne se coupe jamais ; le nom passe à la ligne aux espaces et aux tirets et, en dernier recours seulement, se coupe entre deux lettres ; l'OACI prend sa largeur minimale (quatre caractères au moins) et se coupe entre deux lettres quand la place manque ; la piste se coupe après les virgules seulement
   (« 23L/05R » reste sur une ligne) ; la fréquence se coupe aux espaces seulement, jamais dans un nombre ; la rangée grandit. Le tableau des lignes à remplir (classe dc-blank, posée au rendu) garde ses colonnes fixes et ses marges. */
.dc-fields td.ro { font-family: var(--dc-fo); font-weight: 500; color: var(--dc-acc); text-transform: uppercase; }
.dc-fields td.nm { font-family: var(--dc-fo); font-weight: 500; font-size: 18px; }
.dc-tab.dc-fields:not(.dc-blank) { table-layout: auto; }
.dc-fields:not(.dc-blank) col { width: auto !important; }
.dc-fields:not(.dc-blank) col:nth-child(1), .dc-fields:not(.dc-blank) col:nth-child(2), .dc-fields:not(.dc-blank) col:nth-child(4), .dc-fields:not(.dc-blank) col:nth-child(5) { width: 1px !important; }       /* la largeur de leur plus long élément insécable (l'OACI : au moins quatre caractères) ; le nom prend le reste */
.dc-fields:not(.dc-blank) th, .dc-fields:not(.dc-blank) td { padding-left: 6px; padding-right: 6px; padding-top: 2px; padding-bottom: 2px; }       /* trois pistes sur trois lignes ne font pas déborder la page */
.dc-fields:not(.dc-blank) td { white-space: normal; overflow: visible; text-overflow: clip; overflow-wrap: anywhere; }
.dc-fields:not(.dc-blank) td.ro { white-space: nowrap; overflow-wrap: normal; }
.dc-fields:not(.dc-blank) td:nth-child(4), .dc-fields:not(.dc-blank) td:last-child { overflow-wrap: normal; word-break: normal; }
.dc-fields:not(.dc-blank) td:nth-child(4) { line-height: 1; }
.dc-fields:not(.dc-blank) td:nth-child(2) { min-width: calc(4ch + 14px); }       /* un code OACI de quatre lettres ne se coupe jamais */
.dc-fields:not(.dc-blank) td { font-size: 18px; }       /* une seule taille pour toutes les cellules, l'étiquette comprise */
.dc-fields:not(.dc-blank) th:nth-child(n+3), .dc-fields:not(.dc-blank) td:nth-child(n+3) { border-left: 1px solid var(--dc-sep); }       /* un filet léger entre le nom, la piste et la fréquence ; aucun entre l'étiquette et l'OACI */

/* Météo : quatre paires sur deux colonnes, valeur calée à droite, filet pointillé dessous */
.dc-metar {
  background: var(--dc-metar);
  font: 400 15px/1.3 var(--dc-fm);
  padding: 4px 6px; margin-bottom: 4px;
  overflow-wrap: anywhere;
}
.dc-wgrid { display: grid; grid-template-columns: 1fr 1fr; column-gap: 14px; }
.dc-wgrid .wp {
  display: flex; justify-content: space-between; align-items: baseline;
  border-bottom: 1px dotted var(--dc-dot); padding: 2px; min-width: 0;
}
.dc-wgrid .wp.wp0 { border-bottom: 0; }
.dc-wgrid .wl { font: 500 13px/1 var(--dc-fo); letter-spacing: .12em; text-transform: uppercase; white-space: nowrap; margin-right: calc(8px - .12em); }
.dc-wgrid .wv { font: 400 19px/1.1 var(--dc-fm); white-space: nowrap; }

/* Carburant · Emport */
.dc-fuelwrap { display: grid; grid-template-columns: minmax(0, .8fr) minmax(0, 1.2fr); gap: 14px; align-items: start; }
.dc-fuelwrap.dc-solo { display: block; }
.dc-fp {
  display: flex; justify-content: space-between; align-items: baseline;
  border-bottom: 1px dotted var(--dc-dot); padding: 2px;
}
.dc-fp .fl { font: 500 15px/1 var(--dc-fo); letter-spacing: .12em; text-transform: uppercase; }
.dc-fp .fv { font: 400 21px/1.1 var(--dc-fm); white-space: nowrap; }
.dc-load { list-style: none; min-width: 0; }
.dc-load li { font: 400 19px/1.4 var(--dc-fm); display: flex; }
.dc-load .bl { flex: 0 0 2ch; color: var(--dc-acc); }
.dc-load .lx { flex: 1 1 auto; min-width: 0; overflow-wrap: anywhere; }

/* Menaces · Notes */
.dc-chips { display: flex; flex-wrap: wrap; gap: 6px; }
.dc-chip {
  display: block;
  border: 2px solid var(--dc-hi); color: var(--dc-hi);
  font: 500 18px/1 var(--dc-fo); letter-spacing: .06em;
  padding: 5px 8px; text-transform: uppercase; white-space: nowrap;
}
.dc-notes { margin-top: 9px; font: 500 17px/1.35 var(--dc-fo); letter-spacing: .02em; white-space: pre-line; overflow-wrap: anywhere; }

/* Boîtes vides : titres et lignes à compléter à la main. Toute ligne ou rangée vide mesure 24 px de haut, filet pointillé de 1 px compris ; le filet
   est de l'encre de la page, en mode jour comme en mode nuit ; les rangées alternées des tableaux gardent leur fond. */
tr.dc-bl td.nt, tr.dc-bl td.md { opacity: 1; }
tr.dc-bl td { height: 24px; padding-top: 0; padding-bottom: 0; line-height: 22px; border-bottom: 1px dotted var(--dc-ink); }
div.dc-bl, li.dc-bl, p.dc-bl { height: 24px; border-bottom: 1px dotted var(--dc-ink); margin: 0; overflow: hidden; }
.dc-wgrid .wp.dc-bl { border-bottom-color: var(--dc-ink); }
.dc-fblank > .dc-load { grid-column: 1; grid-row: 2; margin-top: 8px; }


/* ---------- Barre du haut commune aux sept modules (lot mp-imports-suite) ----------
   La marque du Flight Configurator : le titre et son sous-titre à l'accent du module dès 1601 px, le sigle seul en dessous (à toutes les largeurs) ;
   la version avec le titre ; le tampon de décor dès 2307 px. Seuils mesurés dans le shell avec un tampon d'escadre « TEST WING », en français et en anglais,
   la liste du théâtre comprise (lot mp-dg-terrains-liste : +142 px au titre, +171 px aux textes des boutons, +183 px au tampon de décor, au pire des deux langues) et le bouton « Unités »
   (lot mp-theatre-unique : +97 px au titre, +103 px aux textes des boutons, +103 px au tampon de décor, mesurés avant et après). */
.tb-brand-main, .tb-brand-short { color: #8fb0c0; }
.tb-brand-short { display: none; font-family: var(--f-stencil); font-size: 16px; font-weight: 700; letter-spacing: 3px; white-space: nowrap; }
.tb-classif { font-family: var(--f-stencil); font-weight: 400; font-size: 11px; letter-spacing: 3px; color: var(--red-faded); border: 1px solid var(--red-faded); padding: 4px 10px; white-space: nowrap; flex-shrink: 0; }
.tb-lang-btn svg { display: block; }
.tb-brand-sub { font-weight: 500; }
.tb-version { font-family: 'Roboto Mono', monospace; }
@media (max-width: 1600px) { .tb-brand-main, .tb-brand-sub, .tb-brand + .tb-sep, .tb-version { display: none; } .tb-brand-short { display: inline; } }
@media (max-width: 2306px) { .tb-classif { display: none; } }
/* Les boutons portent leur texte au-dessus de 2015 px ; en dessous, l'icône seule (seuil mesuré : avec le tampon d'escadre, la barre défilerait sinon) */
@media (max-width: 2014px) { .tb-btn .tb-btn-label { display: none; } .tb-btn { padding: 0 10px; } }
@media (max-width: 1250px) {
  /* le sélecteur de thème se resserre */
  .tb-select { max-width: 124px; padding: 0 26px 0 8px; text-overflow: ellipsis; overflow: hidden; }
}

/* ============ GROUPES PARTAGÉS (maquette) : liste des cartes, groupe, équipage, radios par type, emport ============ */
.pack-btn.main { background: var(--olive); border-color: var(--amber); color: var(--amber); }
.pack-btn.main:hover:not(:disabled), .pack-btn.main:focus-visible { background: var(--olive-dark); color: var(--paper-light); }
.pack-sub { font-family: var(--f-ui); font-size: 10px; letter-spacing: 1.5px; text-transform: uppercase; color: var(--khaki-light); }
.cards-list { list-style: none; display: flex; flex-direction: column; gap: 6px; }
.card-row {
  display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 2px 8px; align-items: center;
  width: 100%; min-height: 48px; padding: 7px 10px; text-align: left;
  background: rgba(0, 0, 0, .18); border: 1px solid var(--khaki); border-left: 3px solid var(--khaki); color: var(--paper);
  font-family: var(--f-ui);
}
.card-row:hover, .card-row:focus-visible { border-color: var(--amber); outline: none; }
.card-row.cur { background: var(--olive); border-color: var(--amber); border-left-color: var(--amber); }
.card-row.free { border-left-style: dashed; }
.cr-name { font-family: var(--f-stencil); font-weight: 700; font-size: 14px; letter-spacing: 2px; color: var(--amber); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; min-width: 0; }
.cr-tag { font-size: 10px; font-weight: 700; letter-spacing: 1.5px; text-transform: uppercase; padding: 2px 7px; border: 1px solid; white-space: nowrap; }
.cr-tag.linked { color: var(--amber); border-color: var(--amber-dark); }
.cr-tag.free { color: var(--khaki-light); border-color: var(--khaki); border-style: dashed; }
.cr-tag.gone { color: #e8806a; border-color: var(--red-faded); }
.cr-sum { grid-column: 1 / -1; font-size: 11px; letter-spacing: .6px; color: var(--khaki-light); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.card-row.cur .cr-sum { color: var(--paper); opacity: .85; }

/* La boîte « Groupe et équipage » : champs partagés avec le Flight Configurator (pastille FC) sur une carte liée */
.sh {
  display: inline-block; padding: 0 4px; margin-left: 2px; font-size: 9px; line-height: 14px; letter-spacing: 1px;
  color: var(--olive-deep); background: var(--amber); border-radius: 2px;
}
.ed-field label .sh { align-self: center; }
.li-u { padding: 6px 8px; grid-template-columns: minmax(0, 1fr) 44px; }
.li-u .ed-btn-icon { min-width: 44px; min-height: 44px; }
.li-u .li-main { gap: 6px; }
.li-u .li-grid { gap: 6px; }
.li-u .ed-field { gap: 3px; }
.li-uh { display: flex; align-items: center; gap: 8px; }
.li-ut { font-family: var(--f-stencil); font-weight: 700; font-size: 12px; letter-spacing: 2px; color: var(--amber); }
.snap-tag { font-family: var(--f-ui); font-size: 10px; letter-spacing: 1.2px; text-transform: uppercase; padding: 1px 6px; border: 1px solid var(--khaki); color: var(--khaki-light); }

/* Radios : un encadré par type */
.rt-box { border: 1px solid var(--khaki); background: rgba(0, 0, 0, .14); padding: 10px; display: flex; flex-direction: column; gap: 10px; min-width: 0; }
.rt-h { display: flex; flex-direction: column; gap: 2px; font-weight: 400; }
.rt-t { font-family: var(--f-stencil); font-weight: 700; font-size: 14px; letter-spacing: 2px; color: var(--amber); }
.rt-u { font-family: var(--f-ui); font-size: 11px; letter-spacing: .8px; color: var(--khaki-light); }
.rt-post { display: flex; flex-direction: column; gap: 6px; padding-top: 8px; border-top: 1px dashed var(--khaki); }
.rt-ph { font-family: var(--f-ui); font-weight: 700; font-size: 11px; letter-spacing: 1.8px; text-transform: uppercase; color: var(--paper); }
.rc-row { display: flex; flex-direction: column; gap: 4px; padding: 6px 8px; border: 1px solid transparent; border-left: 3px solid var(--khaki); background: rgba(0, 0, 0, .12); min-width: 0; }
.rc-row.on { border-color: var(--amber-dark); border-left-color: var(--amber); background: rgba(192, 137, 42, .10); }
.rc-top { display: flex; flex-wrap: wrap; align-items: center; gap: 4px 10px; }
.rc-ch { flex: 0 0 auto; min-width: 46px; font-family: var(--f-stencil); font-weight: 700; font-size: 13px; letter-spacing: 1.5px; color: var(--amber); }
.rc-freq { flex: 1 1 110px; min-width: 96px; }
.rc-freq input[type=text] { min-height: 44px; }
.rc-on { flex: 0 0 auto; display: inline-flex; align-items: center; gap: 8px; min-height: 44px; padding: 0 4px; cursor: pointer; font-family: var(--f-ui); font-size: 11px; font-weight: 700; letter-spacing: 1.4px; text-transform: uppercase; color: var(--paper); }
.rc-on input { width: 22px; height: 22px; accent-color: var(--amber); margin: 0; }
.rc-var { font-family: var(--f-ui); font-size: 11px; letter-spacing: 1px; color: var(--amber); margin-left: 56px; }
.rc-var::before { content: '⚠ '; }
.rc-extra { display: none; grid-template-columns: 1fr 1fr; gap: 8px; }
.rc-row.on .rc-extra { display: grid; }

/* Emport du Flight Configurator : tableaux sans dessin */
.ed-chk { display: flex; align-items: center; gap: 10px; min-height: 44px; cursor: pointer; font-family: var(--f-ui); font-weight: 700; font-size: 12px; letter-spacing: 1.5px; text-transform: uppercase; color: var(--amber); }
.ed-chk input { width: 22px; height: 22px; accent-color: var(--amber); margin: 0; flex: 0 0 auto; }
.lo-grp { border: 1px solid var(--khaki); background: rgba(0, 0, 0, .14); padding: 8px 10px; min-width: 0; }
.lo-t { font-family: var(--f-stencil); font-weight: 700; font-size: 13px; letter-spacing: 2px; color: var(--amber); margin-bottom: 6px; overflow-wrap: anywhere; }
.lo-tab { width: 100%; border-collapse: collapse; table-layout: fixed; font-family: var(--f-typewriter); font-size: 12px; color: var(--paper); }
.lo-tab th { font-family: var(--f-ui); font-size: 10px; letter-spacing: 1.5px; text-align: left; color: var(--khaki-light); padding: 3px 6px; border-bottom: 1px solid var(--khaki); }
.lo-tab td { padding: 4px 6px; vertical-align: top; overflow-wrap: anywhere; border-bottom: 1px dotted rgba(168, 154, 114, .35); }
.lo-tab td.n, .lo-tab th:first-child { text-align: center; }

/* Fenêtres (nouvelle datacard, rattacher, supprimer) */
.grp-p { font-size: 13px; line-height: 1.45; margin: 0 0 12px; }
.grp-p.grp-empty { font-weight: 700; }
.grp-opt { display: flex; align-items: center; gap: 10px; min-height: 44px; padding: 6px 8px; border: 1px solid #8a7a52; margin-bottom: 6px; cursor: pointer; font-size: 13px; }
.grp-opt input { width: 20px; height: 20px; accent-color: #3d4a22; }
.grp-nm { font-weight: 700; overflow-wrap: anywhere; min-width: 0; }
.grp-sub { margin-left: auto; font-size: 11px; opacity: .75; }
#grp-actions { flex-wrap: wrap; margin-top: 14px; }
.grp-danger { background: #a83524; border-color: #a83524; }

/* La carte : emport en tableaux */
.dc-lo { min-width: 0; }
.dc-lo + .dc-lo { margin-top: 10px; }
.dc-lo-t { font: 500 15px/1 var(--dc-fo); letter-spacing: .12em; color: var(--dc-acc); padding: 2px 0 6px 0; overflow-wrap: anywhere; }
.dc-lot td { font: 400 17px/1.25 var(--dc-fm); white-space: normal; overflow-wrap: anywhere; vertical-align: top; text-overflow: clip; }
.dc-lot td.n, .dc-lot th:first-child { text-align: center; }
.dc-lo-n { font: 400 15px/1.3 var(--dc-fm); color: var(--dc-hi); margin-top: 6px; }

/* ============ TABLETTE ≤ 1100 px ============ */
@media (max-width: 1100px) {
  .tb-btn { padding: 0 8px; }
  .tb-select { max-width: 120px; padding: 0 26px 0 8px; text-overflow: ellipsis; overflow: hidden; }
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

  /* Barre du haut et barre d'onglets : une seule ligne, qui défile au doigt ; un fondu signale le bord qui déborde */
  .toolbar, .tab-bar {
    --fade-w: 22px;
    overflow-x: auto;
    overflow-y: hidden;
    flex-wrap: nowrap;
    scrollbar-width: none;
    -webkit-overflow-scrolling: touch;
    overscroll-behavior-x: contain;
    touch-action: pan-x;
  }
  .toolbar { --fade-gap: 8px; }
  .tab-bar { --fade-gap: 2px; }
  .toolbar::-webkit-scrollbar, .tab-bar::-webkit-scrollbar { display: none; }
  .toolbar > * { flex-shrink: 0; }
  .toolbar::before, .toolbar::after, .tab-bar::before, .tab-bar::after {
    content: '';
    position: sticky;
    flex: 0 0 var(--fade-w);
    width: var(--fade-w);
    align-self: stretch;
    pointer-events: none;
    opacity: 0;
    transition: opacity .15s;
    z-index: 2;
  }
  .toolbar::before, .tab-bar::before {
    left: 0;
    margin-right: calc(-1 * (var(--fade-w) + var(--fade-gap)));
    background: inherit;
    mask-image: linear-gradient(90deg, #000, transparent);
    -webkit-mask-image: linear-gradient(90deg, #000, transparent);
  }
  .toolbar::after, .tab-bar::after {
    right: 0;
    margin-left: calc(-1 * (var(--fade-w) + var(--fade-gap)));
    background: inherit;
    mask-image: linear-gradient(270deg, #000, transparent);
    -webkit-mask-image: linear-gradient(270deg, #000, transparent);
  }
  .toolbar.fade-l::before, .tab-bar.fade-l::before,
  .toolbar.fade-r::after, .tab-bar.fade-r::after { opacity: 1; }
  .tab-bar button { flex: 1 0 auto; min-width: 56px; padding: 6px 8px; }
}
@media (max-width: 600px) {
  .tb-btn { padding: 0 6px; min-width: 38px; height: 38px; }
  .ed-field-row, .ed-field-row.three, .li-grid.g2, .li-grid.g3, .li-grid.g4, .li-grid.g5 { grid-template-columns: 1fr 1fr; }
  .export-modal-choices { grid-template-columns: 1fr; }
  .export-modal-panel { padding: 18px 20px; }
  .editor { padding: 12px 12px 24px 12px; }
  .rc-extra { grid-template-columns: 1fr; }
  .card-row { min-height: 52px; }
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
  .toolbar, .app, .tab-bar, .export-modal, #measure-root { display: none !important; }
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

# Règles « un onglet = une section » sous 1 100 px, générées pour les onze sections (l'ordre de l'aperçu imprimé : méta, mission, horaires, groupe et équipage, navigation, références, radio, terrains, météo, carburant et emport, menaces et notes).
SECTION_IDS = ['meta', 'mission', 'times', 'group', 'nav', 'refs', 'radio', 'fields', 'weather', 'fuel', 'threats']
_tab_rules = ',\n'.join(
    f'  body[data-active-tab="{s}"] .ed-section[data-section="{s}"]' for s in SECTION_IDS
) + ' {\n    display: block;\n    border: none;\n  }'
CSS = CSS.replace('__TAB_SECTION_RULES__', _tab_rules)
CSS = CSS.replace('__STARDOS_400__', A['STARDOS_400'])
CSS = CSS.replace('__STARDOS_700__', A['STARDOS_700'])
CSS = CSS.replace('__OSWALD_500__', A['OSWALD_500'])
CSS = CSS.replace('__OSWALD_700__', A['OSWALD_700'])
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
  <div class="tb-brand">
    <span class="tb-brand-main">DATACARD GENERATOR</span>
    <span class="tb-brand-short" data-i18n="app.short">D·G</span>
    <span class="tb-brand-sub" data-i18n="tb.subtitle">░ CARTES DE BORD</span>
  </div>
  <div class="tb-sep"></div>
  <div class="tb-seg" id="mode-seg" role="group" data-i18n-title="tb.mode.tip" title="Version de jour ou de nuit de la datacard" data-i18n-aria-label="tb.mode.tip" aria-label="Version de jour ou de nuit de la datacard">
    <button type="button" class="seg-btn" id="mode-day" data-mode="day" aria-pressed="true" data-i18n="tb.mode.day">Day</button>
    <button type="button" class="seg-btn" id="mode-night" data-mode="night" aria-pressed="false" data-i18n="tb.mode.night">Night</button>
  </div>
  <div class="tb-sep"></div>
  <span class="tb-label" data-i18n="tb.theatre">Théâtre</span>
  <select class="tb-sel" id="theatre" data-i18n-aria-label="tb.theatre" aria-label="Théâtre"></select>
  <div class="tb-sep"></div>
  <button type="button" class="tb-btn" id="btn-units" aria-haspopup="menu" aria-expanded="false" data-i18n-title="tb.units" title="Unités" data-i18n-aria-label="tb.units" aria-label="Unités"><span id="units-txt"></span><svg class="dsp-chev" viewBox="0 0 10 6" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M1 1l4 4 4-4"/></svg></button>
  <div class="tb-sep"></div>
  <button class="tb-btn" id="btn-json-import" data-i18n-title="tb.json.import.tip" title="Ouvrir une datacard (JSON)">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v1H3z"/><path d="M3 10h19l-2 8a2 2 0 0 1-2 1.5H5a2 2 0 0 1-2-2z"/></svg>
    <span class="tb-btn-label" data-i18n="tb.json.import">Ouvrir</span>
  </button>
  <input type="file" id="file-load" accept=".json,.zip,application/json,application/zip" hidden>
  <button class="tb-btn" id="btn-json-export" data-i18n-title="tb.json.export.tip" title="Enregistrer la datacard (JSON)">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 3h11l4 4v13a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1z"/><path d="M8 3v5h7V3"/><rect x="7" y="13" width="10" height="8"/></svg>
    <span class="tb-btn-label" data-i18n="tb.json.export">Enregistrer</span>
  </button>
  <button class="tb-btn" id="btn-briefing" data-i18n-title="tb.briefing.tip" title="Importer un briefing, une route, la mission d'HQ ou un paquet de vol" data-i18n-aria-label="tb.briefing.tip" aria-label="Importer un briefing, une route, la mission d'HQ ou un paquet de vol">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
    <span class="tb-btn-label" data-i18n="tb.briefing">Importer</span>
  </button>
  <button class="tb-btn" id="btn-print" data-i18n-title="tb.export.tip" title="Exporter en PDF ou PNG">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
    <span class="tb-btn-label" data-i18n="tb.export">Exporter</span>
  </button>
  <button class="tb-btn" id="btn-example" data-i18n-title="tb.example.tip" title="Ouvrir la datacard d'exemple (remplace le document en cours)">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="8" y1="13" x2="16" y2="13"/><line x1="8" y1="17" x2="16" y2="17"/></svg>
    <span class="tb-btn-label" data-i18n="tb.example">Exemple</span>
  </button>
  <button class="tb-btn danger" id="btn-reset" data-i18n-title="tb.reset.tip" title="Vider le document (repartir d'une carte blanche)">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/><path d="M10 11v6M14 11v6"/><path d="M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/></svg>
    <span class="tb-btn-label" data-i18n="tb.reset">Effacer</span>
  </button>
  <select class="tb-select" id="theme-select" data-i18n-title="tb.theme.tip" title="Thème graphique" data-i18n-aria-label="tb.theme.tip" aria-label="Thème graphique">
    <option value="cw-nato"     data-i18n="theme.cw-nato">Cold War OTAN</option>
    <option value="cw-soviet"   data-i18n="theme.cw-soviet">Cold War Soviétique</option>
    <option value="modern-nato" data-i18n="theme.modern-nato">OTAN moderne</option>
    <option value="modern-east" data-i18n="theme.modern-east">Bloc Est moderne</option>
  </select>
  <div class="tb-spacer"></div>
  <div class="tb-classif">COCKPIT COPY // DO NOT REMOVE</div>
  <span class="tb-version">v__APP_VERSION__</span>
  <button class="tb-lang-btn" id="btn-lang" data-i18n-title="tb.lang.tip" title="Passer en anglais" data-i18n-aria-label="tb.lang.tip" aria-label="Passer en anglais"><svg viewBox="0 0 20 14" width="22" height="15" xmlns="http://www.w3.org/2000/svg"><rect width="20" height="14" fill="#012169"/><path d="M0,0 L20,14 M20,0 L0,14" stroke="#fff" stroke-width="2.8"/><path d="M0,0 L20,14 M20,0 L0,14" stroke="#C8102E" stroke-width="1.6"/><rect x="8" width="4" height="14" fill="#fff"/><rect y="5" width="20" height="4" fill="#fff"/><rect x="9" width="2" height="14" fill="#C8102E"/><rect y="6" width="20" height="2" fill="#C8102E"/></svg></button>
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
      <div class="fn-field"><label class="lbl" for="export-png-fname" data-i18n="fn.label">Nom du fichier</label><div class="fn-row"><input class="in" id="export-png-fname" type="text" autocomplete="off" autocapitalize="off" spellcheck="false" maxlength="100"><span class="fn-ext" id="export-png-ext">.png</span></div></div>
      <div class="export-png-actions-bottom">
        <button type="button" class="export-png-back" id="export-png-back" data-i18n="ex.back">← Retour</button>
        <button type="button" class="export-png-go" id="export-png-go"><span data-i18n="tb.export">Exporter</span> <span id="export-png-count"></span></button>
      </div>
    </div>
  </div>
</div>

<!-- ===== FENÊTRE : ENREGISTRER LA DATACARD — CHOISIR LE NOM DU FICHIER ===== -->
<div class="export-modal" id="save-modal" hidden role="dialog" aria-labelledby="save-title" aria-modal="true">
  <div class="export-modal-backdrop" id="save-backdrop"></div>
  <div class="export-modal-panel" role="document">
    <button type="button" class="export-modal-close" id="save-close" data-i18n-aria-label="modal.close" aria-label="Fermer">×</button>
    <h2 id="save-title" data-i18n="save.title">Enregistrer la datacard</h2>
    <div class="fn-field"><label class="lbl" for="save-fname" data-i18n="fn.label">Nom du fichier</label><div class="fn-row"><input class="in" id="save-fname" type="text" autocomplete="off" autocapitalize="off" spellcheck="false" maxlength="100"><span class="fn-ext">.json</span></div></div>
    <div class="export-png-actions-bottom">
      <button type="button" class="export-png-back" id="save-cancel" data-i18n="fn.cancel">Annuler</button>
      <button type="button" class="export-png-go" id="save-go" data-i18n="tb.json.export">Enregistrer</button>
    </div>
  </div>
</div>

<!-- ===== FENÊTRE D'IMPORT (briefing ou route) ===== -->
<div class="export-modal" id="import-modal" hidden role="dialog" aria-labelledby="import-modal-title" aria-modal="true">
  <div class="export-modal-backdrop" id="import-modal-backdrop"></div>
  <div class="export-modal-panel" role="document">
    <button class="export-modal-close" id="import-modal-close" data-i18n-aria-label="modal.close" aria-label="Fermer">×</button>
    <h2 id="import-modal-title" data-i18n="imp.title">Importer dans la datacard</h2>
    <div class="bi-block">
      <label class="bi-src" id="bi-src-current-row"><input type="radio" name="bi-src" id="bi-src-current" value="current"><span data-i18n="imp.src.current">Briefing en cours</span></label>
      <div class="bi-note" id="bi-current-note" hidden></div>
      <label class="bi-src" id="bi-src-route-row"><input type="radio" name="bi-src" id="bi-src-route" value="route"><span data-i18n="imp.src.route">Route en cours</span></label>
      <div class="bi-note" id="bi-route-note" hidden></div>
      <label class="bi-src" id="bi-src-file-row"><input type="radio" name="bi-src" id="bi-src-file" value="file"><span data-i18n="imp.src.file">Fichier JSON (briefing ou route)</span></label>
      <div class="bi-file" id="bi-file-zone" hidden>
        <button type="button" class="bi-filebtn" id="bi-file-btn" data-i18n="imp.choose">Choisir un fichier…</button>
        <span class="bi-filename" id="bi-file-name"></span>
        <input type="file" id="file-briefing" accept=".json,.zip,application/json,application/zip" hidden>
      </div>
    </div>
    <div class="bi-block" id="bi-flights-block">
      <h3 data-i18n="imp.flights">Groupes à importer</h3>
      <div class="export-png-list" id="bi-list"></div>
    </div>
    <div class="bi-block" id="bi-route-block" hidden>
      <h3 data-i18n="imp.route.title">Route à importer</h3>
      <div class="bi-note bi-route-line" id="bi-route-line"></div>
      <label class="bi-src"><input type="radio" name="bi-route-mode" id="bi-route-fill" value="fill" checked><span data-i18n="imp.route.fill">Remplir la navigation de la datacard affichée</span></label>
      <div class="bi-note" data-i18n="imp.route.fillNote">Sa navigation et ses points de référence sont remplacés.</div>
      <label class="bi-src"><input type="radio" name="bi-route-mode" id="bi-route-new" value="new"><span data-i18n="imp.route.new">Nouvelle datacard</span></label>
      <label class="bi-src" id="bi-route-all-row" hidden><input type="radio" name="bi-route-mode" id="bi-route-all" value="all"><span id="bi-route-all-lbl"></span></label>
    </div>
    <div class="bi-block bi-groups">
      <div class="bi-note bi-groups-note" data-i18n="bi.groups.note">Les groupes (mission d'HQ, briefing, paquet de vol) s'importent par la fenêtre d'import commune : ils entrent dans la fiche des groupes, chacun avec sa datacard.</div>
      <button type="button" class="bi-filebtn" id="bi-groups" data-i18n="pack.impgroups">Importer des groupes</button>
    </div>
    <div class="export-png-actions-bottom">
      <button type="button" class="export-png-back" id="bi-cancel" data-i18n="imp.cancel">Annuler</button>
      <button type="button" class="export-png-go" id="bi-go" data-i18n="imp.go">Importer</button>
    </div>
  </div>
</div>

<!-- ===== FENÊTRE D'IMPORT COMMUNE (groupes) ===== -->
@@IMPORT_HTML@@

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
  <button type="button" data-tab="meta" role="tab"><span class="tab-ico">⚙</span><span data-i18n="sec.meta">Méta</span></button>
  <button type="button" data-tab="mission" role="tab"><span class="tab-ico">▣</span><span data-i18n="sec.mission">Mission</span></button>
  <button type="button" data-tab="times" role="tab"><span class="tab-ico">⏱</span><span data-i18n="sec.times">Horaires</span></button>
  <button type="button" data-tab="group" role="tab"><span class="tab-ico">✈</span><span data-i18n="tab.group">Groupe</span></button>
  <button type="button" data-tab="nav" role="tab"><span class="tab-ico">🧭</span><span data-i18n="sec.nav">Navigation</span></button>
  <button type="button" data-tab="refs" role="tab"><span class="tab-ico">◆</span><span data-i18n="sec.refs">Points de référence</span></button>
  <button type="button" data-tab="radio" role="tab"><span class="tab-ico">📻</span><span data-i18n="sec.radio">Radio</span></button>
  <button type="button" data-tab="fields" role="tab"><span class="tab-ico">🛬</span><span data-i18n="sec.fields">Terrains</span></button>
  <button type="button" data-tab="weather" role="tab"><span class="tab-ico">☁</span><span data-i18n="sec.weather">Météo</span></button>
  <button type="button" data-tab="fuel" role="tab"><span class="tab-ico">⛽</span><span data-i18n="tab.fuel">Carburant</span></button>
  <button type="button" data-tab="threats" role="tab"><span class="tab-ico">⚠</span><span data-i18n="tab.threats">Menaces</span></button>
  <button type="button" data-tab="preview" role="tab"><span class="tab-ico">◈</span><span data-i18n="sec.preview">Aperçu</span></button>
</nav>

<!-- ===== FENÊTRE : GROUPES (nouvelle datacard, rattacher, supprimer) ===== -->
<div class="export-modal" id="grp-modal" hidden role="dialog" aria-labelledby="grp-title" aria-modal="true">
  <div class="export-modal-backdrop" id="grp-backdrop"></div>
  <div class="export-modal-panel" role="document">
    <h2 id="grp-title"></h2>
    <div id="grp-body"></div>
    <div class="export-png-actions-bottom" id="grp-actions"></div>
  </div>
</div>

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
/* Clé de stockage écrite par le Briefing Generator (identifiant déjà public) ; ici en lecture seule. */
const KEY_BRIEFING = 'khr26_briefing_state_v2';
const KEY_WING = 'wing_config_v1';                // lecture seule : indicatifs des escadrons
const FORMAT_ID = 'dcs-datacard-v1';
/* Route Planner : clé de l'état de la route (lecture seule), clé du passage vers la datacard, format du fichier */
const KEY_ROUTE = 'route_state_v1';
const KEY_HANDOFF = 'route_handoff_v1';
const ROUTE_FORMAT = 'dcs-route-v1';
const FT_M = 0.3048;
const THEME_IDS = ['cw-nato', 'cw-soviet', 'modern-nato', 'modern-east'];
const MOBILE_BREAKPOINT = 1100;
const PAGE_W = 1000;
const PAGE_H = 1414;

const LIMITS = { steps: 8, times: 8, crew: 6, nav: 30, refs: 12, radios: 4, channels: 20, fields: 5, loadout: 8, threats: 12 };

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
const SECTION_IDS = ['meta', 'mission', 'times', 'group', 'nav', 'refs', 'radio', 'fields', 'weather', 'fuel', 'threats'];
const TAB_IDS = SECTION_IDS.concat(['preview']);

/* Contenu du bouton « Exemple » (document dcs-datacard-v1) */
const EXAMPLE_DOC = __EXAMPLE_DOC__;
const EXAMPLE_DOC_EN = __EXAMPLE_DOC_EN__;

/* ============= i18n FR / EN ============= */
const I18N = {
  fr: {
    'app.title': 'Datacard Generator',
    'tb.subtitle': '░ CARTES DE BORD',
    'tb.mode.day': 'Jour',
    'tb.mode.night': 'Nuit',
    'tb.mode.tip': 'Version de jour ou de nuit de la datacard',
    'tb.briefing': 'Importer',
    'tb.briefing.tip': 'Importer un briefing ou une route dans une datacard',
    'app.short': 'D·G',
    'tb.briefing.short': 'Importer',
    'tb.json.import': 'Ouvrir',
    'tb.json.import.tip': 'Ouvrir une datacard (JSON)',
    'tb.json.export': 'Enregistrer',
    'tb.json.export.tip': 'Enregistrer la datacard (JSON)',
    'tb.export': 'Exporter',
    'tb.export.tip': 'Exporter en PDF ou PNG',
    'tb.example': 'Exemple',
    'tb.example.tip': 'Ouvrir la datacard d\'exemple (remplace le document en cours)',
    'tb.reset': 'Effacer',
    'tb.reset.tip': 'Vider le document (repartir d\'une carte blanche)',
    'tb.theme.tip': 'Thème graphique',
    'tb.theatre': 'Théâtre',
    'tb.units': 'Unités',
    'f.search': 'Rechercher…',
    'f.noaf': 'Aucun aérodrome',
    'f.norwy': 'Aucun sens',
    'tb.lang.tip': 'Passer en anglais',
    'theme.cw-nato': 'Cold War OTAN',
    'theme.cw-soviet': 'Cold War Soviétique',
    'theme.modern-nato': 'OTAN moderne',
    'theme.modern-east': 'Bloc Est moderne',
    'modal.close': 'Fermer',
    'fn.label': 'Nom du fichier',
    'fn.cancel': 'Annuler',
    'save.title': 'Enregistrer la datacard',
    'ex.pdf': 'PDF (impression)',
    'ex.png': 'PNG (kneeboard)',
    'ex.pages': 'Pages à exporter',
    'ex.all': 'Tout cocher',
    'ex.none': 'Tout décocher',
    'ex.back': '← Retour',
    'ex.page': 'Page',
    'ex.progress': 'Génération {i}/{n}…',
    'msg.exportFailed': '⚠ Export impossible.',
    'toast.noMeasure': '⚠ Mise en page non mesurée (le module n\'est pas affiché) : rien n\'est exporté.',
    'toast.pngOne': 'PNG exporté ✓',
    'toast.pngMany': '{n} PNG exportés ✓',
    'imp.title': 'Importer dans la datacard',
    'imp.src.current': 'Briefing en cours',
    'imp.src.currentOff': 'Aucun briefing enregistré dans ce navigateur.',
    'imp.src.route': 'Route en cours',
    'imp.src.routeOff': 'Aucune route sur {th} dans ce navigateur.',
    'imp.src.file': 'Fichier JSON (briefing ou route)',
    'imp.route.title': 'Route à importer',
    'imp.route.line': '« {name} » — {n} points',
    'imp.route.noname': 'Route sans nom',
    'imp.route.fill': 'Remplir la navigation de la datacard affichée',
    'imp.route.fillNote': 'Sa navigation et ses points de référence sont remplacés.',
    'imp.route.refs': ' · {k} réf.',
    'imp.route.new': 'Nouvelle datacard',
    'toast.routeImported': 'Route importée\u202f: {n} points ✓',
    'imp.choose': 'Choisir un fichier…',
    'imp.flights': 'Groupes à importer',
    'imp.route.all': 'Toutes les routes ({n}), une datacard par route',
    'rej.json': '⚠ Fichier illisible : ce n’est pas du JSON.',
    'rej.zip': '⚠ Archive illisible : pas de package.json à la racine.',
    'rej.format': '⚠ Format « {x} » non pris en charge ici (attendu : {list}).',
    'rej.unknown': 'inconnu',
    'rej.incomplete': '⚠ Fichier « {x} » incomplet : aucune route à points.',
    'rej.isDatacard': '⚠ C\'est une datacard : ouvrez-la par « Ouvrir ».',
    'fmt.briefing': 'briefing',
    'fmt.route': 'route',
    'fmt.set': 'jeu de routes',
    'fmt.pkg': 'paquet de vol',
    'fmt.datacard': 'datacard',
    'imp.general': 'Données générales (sans groupe)',
    'imp.go': 'Importer',
    'imp.cancel': 'Annuler',
    'toast.imported': '{n} datacard(s) importée(s) ✓',
    'toast.jsonSaved': 'Datacards enregistrées ✓',
    'toast.jsonLoaded': 'Datacards chargées ✓',
    'confirm.json': 'Remplacer les datacards en cours ?',
    'confirm.json.groups': 'Remplacer vos cartes libres par celles du fichier ? Les cartes des groupes sont gardées ; la carte du fichier qui porte un groupe de la fiche remplace la sienne.',
    'frz.note': 'Copie de ce que le groupe donnait à cette carte avant qu\'elle devienne libre : lecture seule.',
    'u.type.pick': '— à choisir —',
    'sum.type.pick': 'type à choisir',
    'rad.err.nan': 'Canal {0} : « {1} » n’est pas une fréquence.',
    'rad.err.range': 'Canal {0} : {1} MHz hors de la bande du poste ({2}).',
    'rad.err.nan.f': 'Fréquence {0} : « {1} » n’est pas une fréquence.',
    'rad.err.range.f': 'Fréquence {0} : {1} MHz hors de la bande du poste ({2}).',
    'toast.briefFilled': 'Carte « {n} » remplie depuis le briefing (mission, date et heure, terrains, météo)',
    'confirm.example': 'Remplacer le document en cours par l\'exemple ?',
    'toast.example': 'Exemple chargé ✓',
    'confirm.reset': 'Vider toutes les datacards ?',
    'toast.reset': 'Document vidé ✓',
    'confirm.delete': 'Supprimer cette datacard ?',
    'pack.dup': 'Dupliquer',
    'pack.del': 'Supprimer',
    'pack.list': 'Datacards ({n})',
    'pack.newlinked': 'Nouvelle datacard',
    'pack.newfree': 'Carte libre',
    'pack.attach': 'Rattacher à un groupe',
    'pack.impgroups': 'Importer des groupes',
    'bi.groups.note': 'Les groupes (mission d\'HQ, briefing, paquet de vol) s\'importent par la fenêtre d\'import commune : ils entrent dans la fiche des groupes, chacun avec sa datacard.',
    'pack.dup.linked': 'Une carte liée ne se duplique pas',
    'pack.tag.linked': 'liée',
    'pack.tag.free': 'libre',
    'pack.tag.gone': 'groupe supprimé',
    'pack.unnamed': 'Datacard {n}',
    'sum.unit': '{n} unités',
    'sum.unit.1': '{n} unité',
    'sum.free': 'Carte libre, hors des groupes',
    'sum.gone': 'Le groupe n\'existe plus : carte libre',
    'fl.untitled': 'Groupe {n}',
    'fl.name.ph': 'Hind 1',
    'grp.gone': 'Le groupe de cette carte n\'existe plus ailleurs : la carte est libre et garde la dernière copie de ses champs de groupe.',
    'sh.tip': 'Champ partagé avec le Flight Configurator et le Route Planner',
    'f.group.name': 'Nom du groupe',
    'f.coalition': 'Coalition',
    'coal.none': '— non renseignée —',
    'coal.blue': 'Bleue (OTAN)',
    'coal.red': 'Rouge',
    'f.crew.type': 'Type',
    'cr.unit': 'Unité {n}',
    'cr.legend': 'Indicatif, type et n° de bord sont ceux du groupe (partagés). Le pilote est propre à cette carte.',
    'cr.add': '+ Ajouter une unité ({n}/{max})',
    'cr.remove': 'Retirer cette unité',
    'cr.rm.confirm': 'Retirer {n} supprime ses fréquences et son emport du groupe. Continuer ?',
    'u.type.confirm': 'Changer le type de {n} efface ses radios et son emport. Continuer ?',
    'rt.title': 'RADIO — {type}',
    'rt.units': '{n} unités : {names}',
    'rt.units.1': '{n} unité : {names}',
    'rt.ch': 'CH {n}',
    'rt.on': 'sur la carte',
    'rt.varies': 'varie selon l\'unité',
    'rt.name': 'Nom du canal',
    'rt.mod': 'Modulation',
    'rt.free': 'Canaux libres ({n})',
    'rt.free.hide': 'Masquer les canaux libres',
    'rt.free.f': 'Fréquences libres ({n})',
    'rt.free.f.hide': 'Masquer les fréquences libres',
    'rt.freq': 'Fréquence {n}',
    'rt.nofreq': 'Aucune fréquence dans la fiche pour ce poste.',
    'rt.align.confirm': 'Ce canal diffère selon l\'unité : {list}.\nÉcrire « {freq} » dans les {n} unités {type} ?',
    'rt.align.confirm.f': 'Cette fréquence diffère selon l\'unité : {list}.\nÉcrire « {freq} » dans les {n} unités {type} ?',
    'rt.none': 'Ce groupe n\'a pas d\'unité : aucune radio à montrer.',
    'rt.legend': 'Les fréquences sont celles de la fiche. Cochez les canaux à porter sur la carte ; leur nom et leur modulation sont propres à cette carte.',
    'lo.fc': 'Emport du Flight Configurator',
    'lo.fc.hint': 'Lecture seule : l\'emport se modifie au Flight Configurator.',
    'lo.h.n': 'N°',
    'lo.h.load': 'CHARGE',
    'lo.none': 'Sans emport : {names}',
    'lo.empty': 'Aucun emport dans ce groupe.',
    'lo.raw': '{names} : emport à ouvrir au Flight Configurator',
    'w.left': '(gauche)',
    'w.right': '(droite)',
    'cmp.offTable': '(hors table)',
    'cmp.mod': 'modifié',
    'cmp.copied': 'copié de {n}',
    'toast.gsFull': '⚠ Stockage du navigateur plein : vos groupes ne sont pas enregistrés. Enregistrez un fichier de travail.',
    'm.cancel': 'Annuler',
    'm.new.title': 'Nouvelle datacard',
    'm.new.go': 'Créer',
    'm.att.title': 'Rattacher à un groupe',
    'm.att.text': 'Les champs de groupe de cette carte (indicatif, unités, types, n° de bord) seront remplacés par ceux du groupe choisi ; ses pilotes sont gardés, par rang d\'unité. La carte que ce groupe avait devient libre.',
    'm.att.empty': 'Aucun groupe dans la fiche. Créez-en un avec « Nouvelle datacard ».',
    'm.att.go': 'Rattacher',
    'm.att.hascard': 'carte « {n} » : elle deviendra libre',
    'm.del.title': 'Supprimer la datacard « {n} »',
    'm.del.text': 'Cette datacard est celle du groupe « {n} », partagé avec le Flight Configurator et le Route Planner. La supprimer supprime le groupe pour tous les modules.',
    'm.del.both': 'Supprimer la datacard et le groupe',
    'li.up': 'Monter',
    'li.down': 'Descendre',
    'li.del': 'Supprimer',
    'warn.overflow': 'Contenu tronqué : la page 1 déborde même sans la navigation.',
    'warn.overflow2': 'Contenu tronqué\u202f: la page 2 déborde.',
    'warn.overflowR': 'Contenu tronqué\u202f: la page Radios déborde.',
    'sec.meta': 'Méta',
    'sec.group': 'Groupe et équipage',
    'sec.mission': 'Mission',
    'sec.times': 'Horaires',
    'sec.nav': 'Navigation',
    'sec.refs': 'Points de référence',
    'sec.radio': 'Radio',
    'sec.fields': 'Terrains',
    'sec.weather': 'Météo',
    'sec.fuel': 'Carburant et emport',
    'sec.threats': 'Menaces et notes',
    'sec.preview': 'Aperçu',
    'tab.fuel': 'Carburant',
    'tab.group': 'Groupe',
    'tab.threats': 'Menaces',
    'ph.meta.docRef': 'OPS-M3-1989',
    'ph.meta.operation': 'FOOTHOLD',
    'ph.meta.mission': 'M3',
    'ph.meta.date': '1989-03-22',
    'ph.meta.time': '10:00 L',
    'ph.flight.callsign': 'CAESAR',
    'ph.flight.aircraft': 'Mi-24P',
    'ph.flight.count': '2',
    'ph.flight.task': 'CAS / Défense de zone',
    'ph.mission.objective': 'Intercepter le convoi avant la FARP',
    'ph.mission.execution.*': 'Chemin côtier jusqu\'à l\'IP',
    'ph.times.*.label': 'Décollage',
    'ph.times.*.value': '09:45',
    'ph.crew.*.callsign': 'CAESAR 1-1',
    'ph.crew.*.pilot': 'VIPER',
    'ph.crew.*.type': 'Mi-24P',
    'ph.crew.*.board': '41',
    'ph.nav.*.name': 'IP',
    'ph.nav.*.course': '059',
    'ph.nav.*.distance': '32',
    'ph.nav.*.altitude': '50',
    'ph.nav.*.tos': '10:05',
    'ph.nav.*.note': 'Île + rivière',
    'ph.refs.*.name': 'ÎLE PETRA',
    'ph.refs.*.coord': '36S VD 85842 93459',
    'ph.refs.*.altitude': '0',
    'ph.refs.*.note': 'Repère côtier',
    'ph.radios.*.name': 'R-863',
    'ph.radios.*.channels.*.channel': '0',
    'ph.radios.*.channels.*.label': 'Groupe 1',
    'ph.radios.*.channels.*.frequency': '127.50',
    'ph.radios.*.channels.*.modulation': 'AM',
    'ph.fields.*.icao': 'LCRA',
    'ph.fields.*.name': 'Akrotiri',
    'ph.fields.*.runway': '10',
    'ph.fields.*.frequency': '270.00',
    'ph.weather.metar': 'LCRA 221000Z 18002KT 9999 SCT082 20/15 Q1013',
    'ph.weather.wind': '180/02',
    'ph.weather.visibility': '≥ 10 km',
    'ph.weather.qnh': '1013 hPa',
    'ph.weather.clouds': 'SCT 8200 ft',
    'ph.fuel.joker': '600',
    'ph.fuel.bingo': '450',
    'ph.loadout.*': '4 × 9M114 Shturm',
    'ph.threats.*': 'SA-13',
    'ph.notes': 'Repère : petite île + rivière',
    'f.classification': 'Classification',
    'f.docRef': 'Référence',
    'f.operation': 'Opération',
    'f.mission': 'Mission',
    'f.date': 'Date',
    'f.time': 'Heure',
    'f.aircraft': 'Appareil',
    'f.group.deduced': 'Déduit des équipages',
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
    'f.crew.board': 'N° de bord',
    'f.nav.name': 'Point',
    'f.nav.course': 'Cap',
    'f.nav.distance': 'Distance',
    'f.nav.altitude': 'Altitude',
    'f.nav.tos': 'Heure',
    'f.nav.note': 'Note',
    'f.nav.display': 'Affichage',
    'nav.mode.course': 'Cap / distance',
    'nav.mode.mgrs': 'MGRS',
    'nav.mode.dms': 'DMS',
    'f.nav.ref': 'Cap',
    'nav.ref.true': 'Vrai',
    'nav.ref.mag': 'Magnétique',
    'f.nav.decl': 'Déclinaison (°)',
    'ph.navDisplay.decl': '3,5',
    'nav.decl.help': 'en degrés, + vers l\'Est ; lue au CDU de l\'A-10C (POSINFO), au DED du F-16 (MVAR) ou à l\'HSI du F/A-18',
    'nav.decl.warn': 'Déclinaison manquante : cap vrai affiché',
    'f.nav.vmode': 'Déclinaison',
    'nav.vmode.calc': 'Calculée',
    'nav.vmode.manual': 'Saisie',
    'nav.vy.date': 'Année {a} · champ Date',
    'nav.vy.def': 'Année 1985 par défaut · champ Date vide',
    'nav.vy.model': 'Modèle de DCS ({e}), par branche au point de départ',
    'f.nav.coord': 'Coordonnées',
    'ph.nav.*.coord': '36S VD 47535 77241',
    'nav.coord.bad': '✗ Format non reconnu',
    'nav.calc.tip': 'Calculé depuis les coordonnées',
    'nav.coord.help': 'MGRS, ou N35°02\'11" E032°25\'29", ou N35°02.183\' E032°25.483\', ou 35.0365, 32.4248, ou 36.49.30N/34.44.29E',
    'nav.est.prev': 'Estimé depuis le point précédent (cap, distance) :',
    'nav.est.next': 'Estimé depuis le point suivant (cap, distance) :',
    'dc.h.course.t': 'CAP V °',
    'dc.h.course.m': 'CAP M °',
    'dc.h.mgrs': 'MGRS',
    'dc.h.coord': 'COORDONNÉES',
    'dc.b.nav.true': 'NAVIGATION · CAP VRAI',
    'dc.b.nav.mag': 'NAVIGATION · CAP MAGNÉTIQUE · DÉCL. {d}° {h}',
    'dc.b.nav.calc': 'NAVIGATION · CAP MAGNÉTIQUE · VAR {a} ({min} à {max}°)',
    'dc.b.nav.calc1': 'NAVIGATION · CAP MAGNÉTIQUE · VAR {a} ({v}°)',
    'f.radio.name': 'Poste',
    'f.radio.channel': 'Canal',
    'f.radio.label': 'Usage',
    'f.radio.frequency': 'Fréquence',
    'f.radio.modulation': 'Modulation',
    'f.field.role': 'Rôle',
    'f.field.icao': 'OACI',
    'f.field.name': 'Nom',
    'f.field.pick': 'Choisir…',
    'f.field.other': 'Autre…',
    'th.Afghanistan': 'Afghanistan',
    'th.Caucasus': 'Caucase',
    'th.Falklands': 'Atlantique Sud',
    'th.GermanyCW': 'Allemagne (guerre froide)',
    'th.Iraq': 'Irak',
    'th.Kola': 'Kola',
    'th.MarianaIslands': 'Mariannes',
    'th.MarianaIslandsWWII': 'Mariannes 1944',
    'th.Nevada': 'Nevada',
    'th.Normandy': 'Normandie',
    'th.PersianGulf': 'Golfe Persique',
    'th.SinaiMap': 'Sinaï',
    'th.Syria': 'Syrie',
    'th.TheChannel': 'Manche',
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
    'add.point': '+ Ajouter un point',
    'add.ref': '+ Point de référence',
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
    'dc.b.refs': 'POINTS DE RÉFÉRENCE',
    'dc.b.radio': 'RADIO',
    'dc.b.fields': 'TERRAINS',
    'dc.b.weather': 'MÉTÉO',
    'dc.b.fuel': 'CARBURANT',
    'dc.b.loadout': 'EMPORT',
    'dc.b.threats': 'MENACES',
    'dc.b.notes': 'NOTES',
    'dc.page2': 'DATACARD · NAVIGATION',
    'dc.pageR': 'DATACARD · RADIOS',
    'dc.flightOf': 'GROUPE DE {n}',
    'dc.operation': 'OPÉRATION {op}',
    'dc.thr.low': 'MENACE FAIBLE',
    'dc.thr.moderate': 'MENACE MODÉRÉE',
    'dc.thr.high': 'MENACE ÉLEVÉE',
    'dc.h.callsign': 'INDICATIF',
    'dc.h.pilot': 'PILOTE',
    'dc.h.crew': 'APPAREIL',
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
    'tb.subtitle': '░ DATACARDS',
    'tb.mode.day': 'Day',
    'tb.mode.night': 'Night',
    'tb.mode.tip': 'Day or night version of the datacard',
    'tb.briefing': 'Import',
    'tb.briefing.tip': 'Import a briefing or a route into a datacard',
    'app.short': 'D·G',
    'tb.briefing.short': 'Import',
    'tb.json.import': 'Open',
    'tb.json.import.tip': 'Open a datacard (JSON)',
    'tb.json.export': 'Save',
    'tb.json.export.tip': 'Save the datacard (JSON)',
    'tb.export': 'Export',
    'tb.export.tip': 'Export to PDF or PNG',
    'tb.example': 'Example',
    'tb.example.tip': 'Open the example datacard (replaces the current document)',
    'tb.reset': 'Clear',
    'tb.reset.tip': 'Clear the document (start from a blank card)',
    'tb.theme.tip': 'Graphic theme',
    'tb.theatre': 'Theatre',
    'tb.units': 'Units',
    'f.search': 'Search…',
    'f.noaf': 'No airfield',
    'f.norwy': 'No runway end',
    'tb.lang.tip': 'Switch to French',
    'theme.cw-nato': 'Cold War NATO',
    'theme.cw-soviet': 'Cold War Soviet',
    'theme.modern-nato': 'Modern NATO',
    'theme.modern-east': 'Modern East Bloc',
    'modal.close': 'Close',
    'fn.label': 'File name',
    'fn.cancel': 'Cancel',
    'save.title': 'Save the datacard',
    'ex.pdf': 'PDF (print)',
    'ex.png': 'PNG (kneeboard)',
    'ex.pages': 'Pages to export',
    'ex.all': 'Check all',
    'ex.none': 'Uncheck all',
    'ex.back': '← Back',
    'ex.page': 'Page',
    'ex.progress': 'Generating {i}/{n}…',
    'msg.exportFailed': '⚠ Export failed.',
    'toast.noMeasure': '⚠ Layout not measured (the module is not displayed): nothing was exported.',
    'toast.pngOne': 'PNG exported ✓',
    'toast.pngMany': '{n} PNGs exported ✓',
    'imp.title': 'Import into the datacard',
    'imp.src.current': 'Current briefing',
    'imp.src.currentOff': 'No briefing saved in this browser.',
    'imp.src.route': 'Current route',
    'imp.src.routeOff': 'No route on {th} in this browser.',
    'imp.src.file': 'JSON file (briefing or route)',
    'imp.route.title': 'Route to import',
    'imp.route.line': '“{name}” — {n} waypoints',
    'imp.route.noname': 'Untitled route',
    'imp.route.fill': 'Fill the navigation of the datacard shown',
    'imp.route.fillNote': 'Its navigation and reference points are replaced.',
    'imp.route.refs': ' · {k} ref.',
    'imp.route.new': 'New datacard',
    'toast.routeImported': 'Route imported: {n} waypoints ✓',
    'imp.choose': 'Choose a file…',
    'imp.flights': 'Groups to import',
    'imp.route.all': 'All routes ({n}), one datacard per route',
    'rej.json': '⚠ Unreadable file: this is not JSON.',
    'rej.zip': '⚠ Unreadable archive: no package.json at the root.',
    'rej.format': '⚠ Format “{x}” is not supported here (expected: {list}).',
    'rej.unknown': 'unknown',
    'rej.incomplete': '⚠ Incomplete "{x}" file: no route with points.',
    'rej.isDatacard': '⚠ This is a datacard: open it with "Open".',
    'fmt.briefing': 'briefing',
    'fmt.route': 'route',
    'fmt.set': 'route set',
    'fmt.pkg': 'flight package',
    'fmt.datacard': 'datacard',
    'imp.general': 'General data (no group)',
    'imp.go': 'Import',
    'imp.cancel': 'Cancel',
    'toast.imported': '{n} datacard(s) imported ✓',
    'toast.jsonSaved': 'Datacards saved ✓',
    'toast.jsonLoaded': 'Datacards loaded ✓',
    'confirm.json': 'Replace the current datacards?',
    'confirm.json.groups': 'Replace your free cards with the file\'s? The groups\' cards are kept; the file\'s card that carries a group of the shared set replaces that group\'s card.',
    'frz.note': 'A copy of what the group gave this card before it became free: read only.',
    'u.type.pick': '— to pick —',
    'sum.type.pick': 'type to pick',
    'rad.err.nan': 'Channel {0}: “{1}” is not a frequency.',
    'rad.err.range': 'Channel {0}: {1} MHz is outside the radio’s band ({2}).',
    'rad.err.nan.f': 'Frequency {0}: “{1}” is not a frequency.',
    'rad.err.range.f': 'Frequency {0}: {1} MHz is outside the radio’s band ({2}).',
    'toast.briefFilled': 'Card “{n}” filled from the briefing (mission, date and time, airfields, weather)',
    'confirm.example': 'Replace the current document with the example?',
    'toast.example': 'Example loaded ✓',
    'confirm.reset': 'Clear all datacards?',
    'toast.reset': 'Document cleared ✓',
    'confirm.delete': 'Delete this datacard?',
    'pack.dup': 'Duplicate',
    'pack.del': 'Delete',
    'pack.list': 'Datacards ({n})',
    'pack.newlinked': 'New datacard',
    'pack.newfree': 'Free card',
    'pack.attach': 'Attach to a group',
    'pack.impgroups': 'Import groups',
    'bi.groups.note': 'Groups (HQ mission, briefing, flight package) are imported through the common import window: they enter the group sheet, each with its datacard.',
    'pack.dup.linked': 'A linked card cannot be duplicated',
    'pack.tag.linked': 'linked',
    'pack.tag.free': 'free',
    'pack.tag.gone': 'group deleted',
    'pack.unnamed': 'Datacard {n}',
    'sum.unit': '{n} units',
    'sum.unit.1': '{n} unit',
    'sum.free': 'Free card, outside the groups',
    'sum.gone': 'The group no longer exists: free card',
    'fl.untitled': 'Group {n}',
    'fl.name.ph': 'Hind 1',
    'grp.gone': 'This card\'s group no longer exists elsewhere: the card is free and keeps the last copy of its group fields.',
    'sh.tip': 'Field shared with the Flight Configurator and the Route Planner',
    'f.group.name': 'Group name',
    'f.coalition': 'Coalition',
    'coal.none': '— not set —',
    'coal.blue': 'Blue (NATO)',
    'coal.red': 'Red',
    'f.crew.type': 'Type',
    'cr.unit': 'Unit {n}',
    'cr.legend': 'Callsign, type and onboard no. belong to the group (shared). The pilot belongs to this card only.',
    'cr.add': '+ Add a unit ({n}/{max})',
    'cr.remove': 'Remove this unit',
    'cr.rm.confirm': 'Removing {n} deletes its frequencies and loadout from the group. Continue?',
    'u.type.confirm': 'Changing {n}’s type clears its radios and loadout. Continue?',
    'rt.title': 'RADIO — {type}',
    'rt.units': '{n} units: {names}',
    'rt.units.1': '{n} unit: {names}',
    'rt.ch': 'CH {n}',
    'rt.on': 'on the card',
    'rt.varies': 'varies by unit',
    'rt.name': 'Channel name',
    'rt.mod': 'Modulation',
    'rt.free': 'Empty channels ({n})',
    'rt.free.hide': 'Hide empty channels',
    'rt.free.f': 'Empty frequencies ({n})',
    'rt.free.f.hide': 'Hide empty frequencies',
    'rt.freq': 'Frequency {n}',
    'rt.nofreq': 'No frequency in the group sheet for this radio.',
    'rt.align.confirm': 'This channel differs between units: {list}.\nWrite “{freq}” to all {n} {type} units?',
    'rt.align.confirm.f': 'This frequency differs between units: {list}.\nWrite “{freq}” to all {n} {type} units?',
    'rt.none': 'This group has no unit: no radio to show.',
    'rt.legend': 'Frequencies are those of the group sheet. Tick the channels to print on the card; their name and modulation belong to this card only.',
    'lo.fc': 'Loadout from the Flight Configurator',
    'lo.fc.hint': 'Read only: the loadout is edited in the Flight Configurator.',
    'lo.h.n': 'NO.',
    'lo.h.load': 'STORE',
    'lo.none': 'No loadout: {names}',
    'lo.empty': 'No loadout in this group.',
    'lo.raw': '{names}: loadout to open in the Flight Configurator',
    'w.left': '(left)',
    'w.right': '(right)',
    'cmp.offTable': '(not in table)',
    'cmp.mod': 'modified',
    'cmp.copied': 'copied from {n}',
    'toast.gsFull': '⚠ Browser storage full: your groups are not saved. Save a work file.',
    'm.cancel': 'Cancel',
    'm.new.title': 'New datacard',
    'm.new.go': 'Create',
    'm.att.title': 'Attach to a group',
    'm.att.text': 'This card\'s group fields (callsign, units, types, board numbers) will be replaced by those of the chosen group; its pilots are kept, by unit rank. The card this group had becomes free.',
    'm.att.empty': 'No group in the sheet. Create one with “New datacard”.',
    'm.att.go': 'Attach',
    'm.att.hascard': 'card “{n}”: it will become free',
    'm.del.title': 'Delete the datacard "{n}"',
    'm.del.text': 'This datacard is the one of the group “{n}”, shared with the Flight Configurator and the Route Planner. Deleting it deletes the group for all modules.',
    'm.del.both': 'Delete the datacard and the group',
    'li.up': 'Move up',
    'li.down': 'Move down',
    'li.del': 'Delete',
    'warn.overflow': 'Content truncated: page 1 overflows even without navigation.',
    'warn.overflow2': 'Content truncated: page 2 overflows.',
    'warn.overflowR': 'Content truncated: the Radios page overflows.',
    'sec.meta': 'Meta',
    'sec.group': 'Group and crew',
    'sec.mission': 'Mission',
    'sec.times': 'Times',
    'sec.nav': 'Navigation',
    'sec.refs': 'Reference points',
    'sec.radio': 'Radio',
    'sec.fields': 'Airfields',
    'sec.weather': 'Weather',
    'sec.fuel': 'Fuel and loadout',
    'sec.threats': 'Threats and notes',
    'sec.preview': 'Preview',
    'tab.fuel': 'Fuel',
    'tab.group': 'Group',
    'tab.threats': 'Threats',
    'ph.meta.docRef': 'OPS-M3-1989',
    'ph.meta.operation': 'FOOTHOLD',
    'ph.meta.mission': 'M3',
    'ph.meta.date': '1989-03-22',
    'ph.meta.time': '10:00 L',
    'ph.flight.callsign': 'CAESAR',
    'ph.flight.aircraft': 'Mi-24P',
    'ph.flight.count': '2',
    'ph.flight.task': 'CAS / Area defence',
    'ph.mission.objective': 'Intercept the convoy before the FARP',
    'ph.mission.execution.*': 'Coastal route to the IP',
    'ph.times.*.label': 'Take-off',
    'ph.times.*.value': '09:45',
    'ph.crew.*.callsign': 'CAESAR 1-1',
    'ph.crew.*.pilot': 'VIPER',
    'ph.crew.*.type': 'Mi-24P',
    'ph.crew.*.board': '41',
    'ph.nav.*.name': 'IP',
    'ph.nav.*.course': '059',
    'ph.nav.*.distance': '32',
    'ph.nav.*.altitude': '50',
    'ph.nav.*.tos': '10:05',
    'ph.nav.*.note': 'Island + river',
    'ph.refs.*.name': 'PETRA ISLAND',
    'ph.refs.*.coord': '36S VD 85842 93459',
    'ph.refs.*.altitude': '0',
    'ph.refs.*.note': 'Coastal landmark',
    'ph.radios.*.name': 'R-863',
    'ph.radios.*.channels.*.channel': '0',
    'ph.radios.*.channels.*.label': 'Group 1',
    'ph.radios.*.channels.*.frequency': '127.50',
    'ph.radios.*.channels.*.modulation': 'AM',
    'ph.fields.*.icao': 'LCRA',
    'ph.fields.*.name': 'Akrotiri',
    'ph.fields.*.runway': '10',
    'ph.fields.*.frequency': '270.00',
    'ph.weather.metar': 'LCRA 221000Z 18002KT 9999 SCT082 20/15 Q1013',
    'ph.weather.wind': '180/02',
    'ph.weather.visibility': '≥ 10 km',
    'ph.weather.qnh': '1013 hPa',
    'ph.weather.clouds': 'SCT 8200 ft',
    'ph.fuel.joker': '600',
    'ph.fuel.bingo': '450',
    'ph.loadout.*': '4 × 9M114 Shturm',
    'ph.threats.*': 'SA-13',
    'ph.notes': 'Landmark: small island + river',
    'f.classification': 'Classification',
    'f.docRef': 'Reference',
    'f.operation': 'Operation',
    'f.mission': 'Mission',
    'f.date': 'Date',
    'f.time': 'Time',
    'f.aircraft': 'Aircraft',
    'f.group.deduced': 'Deduced from the crew list',
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
    'f.crew.board': 'Board no.',
    'f.nav.name': 'Point',
    'f.nav.course': 'Heading',
    'f.nav.distance': 'Distance',
    'f.nav.altitude': 'Altitude',
    'f.nav.tos': 'Time',
    'f.nav.note': 'Note',
    'f.nav.display': 'Display',
    'nav.mode.course': 'Heading / distance',
    'nav.mode.mgrs': 'MGRS',
    'nav.mode.dms': 'DMS',
    'f.nav.ref': 'Heading',
    'nav.ref.true': 'True',
    'nav.ref.mag': 'Magnetic',
    'f.nav.decl': 'Variation (°)',
    'ph.navDisplay.decl': '3,5',
    'nav.decl.help': 'in degrees, + East; read on the A-10C CDU (POSINFO), the F-16 DED (MVAR) or the F/A-18 HSI',
    'nav.decl.warn': 'Variation missing: true heading shown',
    'f.nav.vmode': 'Variation',
    'nav.vmode.calc': 'Computed',
    'nav.vmode.manual': 'Entered',
    'nav.vy.date': 'Year {a} · Date field',
    'nav.vy.def': 'Year 1985 by default · Date field empty',
    'nav.vy.model': 'DCS model ({e}), per leg at its start point',
    'f.nav.coord': 'Coordinates',
    'ph.nav.*.coord': '36S VD 47535 77241',
    'nav.coord.bad': '✗ Format not recognized',
    'nav.calc.tip': 'Computed from coordinates',
    'nav.coord.help': 'MGRS, or N35°02\'11" E032°25\'29", or N35°02.183\' E032°25.483\', or 35.0365, 32.4248, or 36.49.30N/34.44.29E',
    'nav.est.prev': 'Estimated from the previous point (heading, distance):',
    'nav.est.next': 'Estimated from the next point (heading, distance):',
    'dc.h.course.t': 'HDG T °',
    'dc.h.course.m': 'HDG M °',
    'dc.h.mgrs': 'MGRS',
    'dc.h.coord': 'COORDINATES',
    'dc.b.nav.true': 'NAVIGATION · TRUE HEADING',
    'dc.b.nav.mag': 'NAVIGATION · MAGNETIC HEADING · VAR {d}° {h}',
    'dc.b.nav.calc': 'NAVIGATION · MAGNETIC HEADING · VAR {a} ({min} to {max}°)',
    'dc.b.nav.calc1': 'NAVIGATION · MAGNETIC HEADING · VAR {a} ({v}°)',
    'f.radio.name': 'Radio',
    'f.radio.channel': 'Channel',
    'f.radio.label': 'Use',
    'f.radio.frequency': 'Frequency',
    'f.radio.modulation': 'Modulation',
    'f.field.role': 'Role',
    'f.field.icao': 'ICAO',
    'f.field.name': 'Name',
    'f.field.pick': 'Pick…',
    'f.field.other': 'Other…',
    'th.Afghanistan': 'Afghanistan',
    'th.Caucasus': 'Caucasus',
    'th.Falklands': 'South Atlantic',
    'th.GermanyCW': 'Cold War Germany',
    'th.Iraq': 'Iraq',
    'th.Kola': 'Kola',
    'th.MarianaIslands': 'Mariana Islands',
    'th.MarianaIslandsWWII': 'Mariana Islands WWII',
    'th.Nevada': 'Nevada',
    'th.Normandy': 'Normandy',
    'th.PersianGulf': 'Persian Gulf',
    'th.SinaiMap': 'Sinai',
    'th.Syria': 'Syria',
    'th.TheChannel': 'The Channel',
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
    'add.point': '+ Add point',
    'add.ref': '+ Reference point',
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
    'dc.b.refs': 'REFERENCE POINTS',
    'dc.b.radio': 'RADIO',
    'dc.b.fields': 'AIRFIELDS',
    'dc.b.weather': 'WEATHER',
    'dc.b.fuel': 'FUEL',
    'dc.b.loadout': 'LOADOUT',
    'dc.b.threats': 'THREATS',
    'dc.b.notes': 'NOTES',
    'dc.page2': 'DATACARD · NAVIGATION',
    'dc.pageR': 'DATACARD · RADIOS',
    'dc.flightOf': 'GROUP OF {n}',
    'dc.operation': 'OPERATION {op}',
    'dc.thr.low': 'THREAT LOW',
    'dc.thr.moderate': 'THREAT MODERATE',
    'dc.thr.high': 'THREAT HIGH',
    'dc.h.callsign': 'CALLSIGN',
    'dc.h.pilot': 'PILOT',
    'dc.h.crew': 'AIRCRAFT',
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

/* Drapeaux dessinés (ils ne s'affichent pas en lettres sous Windows) ; le bouton montre la langue vers laquelle il bascule */
const FLAG_FR = '<svg viewBox="0 0 20 14" width="22" height="15" xmlns="http://www.w3.org/2000/svg"><rect width="7" height="14" fill="#002395"/><rect x="7" width="6" height="14" fill="#fff"/><rect x="13" width="7" height="14" fill="#ED2939"/></svg>';
const FLAG_EN = '<svg viewBox="0 0 20 14" width="22" height="15" xmlns="http://www.w3.org/2000/svg"><rect width="20" height="14" fill="#012169"/><path d="M0,0 L20,14 M20,0 L0,14" stroke="#fff" stroke-width="2.8"/><path d="M0,0 L20,14 M20,0 L0,14" stroke="#C8102E" stroke-width="1.6"/><rect x="8" width="4" height="14" fill="#fff"/><rect y="5" width="20" height="4" fill="#fff"/><rect x="9" width="2" height="14" fill="#C8102E"/><rect y="6" width="20" height="2" fill="#C8102E"/></svg>';

function updateFlagButton() {
  const btn = document.getElementById('btn-lang');
  if (!btn) return;
  btn.innerHTML = CURRENT_LANG === 'fr' ? FLAG_EN : FLAG_FR;
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

@@MESSAGES_BLOCK@@

/* ============= COORDONNÉES DE NAVIGATION ============= */
/* Datum WGS84. Lecture : MGRS, degrés-minutes-secondes, degrés-minutes décimales, degrés décimaux.
   Conversions : série de Krüger (ordre 4) ; cap initial du grand cercle et distance haversine (R = 6 371,0088 km). */
const NAV_MODES = ['course', 'mgrs', 'dms'];
const NAV_REFS = ['true', 'mag'];
const NAV_R_KM = 6371.0088;
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

/* Nombre lisible d'un champ Cap / Distance (virgule ou point décimal), sinon null */
function readNum(s) {
  if (typeof s !== 'string') return null;
  const m = /^\s*(\d+(?:[.,]\d+)?)\s*$/.exec(s);
  return m ? parseFloat(m[1].replace(',', '.')) : null;
}

@@MAGVAR_BLOCK@@
@@RADIO_BLOCK@@
@@RADIO_BANDS_BLOCK@@
@@PROJECTION_BLOCK@@
/* La déclinaison des caps d'une datacard : null (cap vrai, ou saisie illisible) ; { decl } saisie ; { calc: true, y } calculée,
   y étant l'année décimale du champ Date (1985, le 1er juillet, s'il est vide ou illisible) */
function navVar(c) {
  const nd = c.navDisplay;
  if (nd.ref !== 'mag') return null;
  if (nd.vmode === 'manual') { const d = parseDecl(nd.decl); return d == null ? null : { decl: d }; }
  const y = magDecYear(c.meta.date);
  return { calc: true, y: y == null ? magDecYear('1985') : y, dated: y != null };
}
/* La déclinaison (°, + vers l'Est) au point pt */
function varAt(nv, pt) { return nv.calc ? magVar(pt.lat, pt.lon, nv.y) : nv.decl; }
/* Une déclinaison au dixième : signe − (U+2212) ou +, virgule en FR, aucun signe pour 0,0 */
function fmtVar(v) {
  const r = Math.round(v * 10) / 10;
  const x = Math.abs(r).toFixed(1);
  const d = CURRENT_LANG === 'fr' ? x.replace('.', ',') : x;
  return r === 0 ? d : (r < 0 ? '\u2212' : '+') + d;
}

/* Pour chaque point de c.nav (même indice) : { pt, est, estDir, calc, blank } — pt : coordonnée saisie lue (ou null) ;
   est : coordonnées estimées par le cap et la distance saisis (ou null), estDir 'prev' (vers l'avant) ou 'next' (à rebours) ;
   calc : { cap, dist } (chaînes) quand la branche (point précédent non vide → ce point) est calculable, sinon null. */
function navLegs(c) {
  const nv = navVar(c);
  const nm = dgU.distance === 'nm';
  const out = [];
  let prev = null;
  c.nav.forEach(r => {
    const blank = !NAV_KEYS.some(k => hasText(r[k]));
    const pt = parseCoord(r.coord);
    let calc = null;
    if (!blank) {
      if (prev && prev.pt && pt) {
        const L = legCalc(prev.pt, pt);
        let brg = L.brg, dv = null;
        if (nv) { dv = varAt(nv, prev.pt); brg = ((brg - dv) % 360 + 360) % 360; }    /* la déclinaison du point de départ de la branche */
        const d = nm ? L.km / NAV_NM_KM : L.km;
        calc = { cap: fmtHdg(brg), dist: String(Math.round(d)), v: dv };
      }
    }
    const o = { pt: pt, est: null, estDir: '', calc: calc, blank: blank };
    out.push(o);
    if (!blank) prev = o;
  });
  /* Cap et distance saisis d'un point, lus : { brg (vrai), km } ou null ; le cap saisi est magnétique : cap vrai = cap + la déclinaison
     de base, le point connu dont on part (le précédent, ou à rebours le suivant) */
  const leg = (i, base) => {
    const r = c.nav[i];
    const cap = readNum(r.course), dist = readNum(r.distance);
    if (cap == null || dist == null || cap > 360 || !(dist > 0)) return null;
    let brg = cap;
    if (nv) brg = (cap + varAt(nv, base)) % 360;
    return { brg: brg, km: nm ? dist * NAV_NM_KM : dist };
  };
  const live = out.map((o, i) => i).filter(i => !out[i].blank);
  /* vers l'avant : le point précédent est placé (saisi ou estimé) */
  live.forEach((i, k) => {
    const o = out[i];
    if (o.pt || k === 0) return;
    const p = out[live[k - 1]], base = p.pt || p.est, L = base ? leg(i, base) : null;
    if (base && L) { o.est = legDest(base, L.brg, L.km); o.estDir = 'prev'; }
  });
  /* à rebours : le point suivant est placé et la branche saisie sur lui est lisible */
  for (let k = live.length - 2; k >= 0; k--) {
    const o = out[live[k]], n = out[live[k + 1]];
    if (o.pt || o.est) continue;
    const base = n.pt || n.est, L = base ? leg(live[k + 1], base) : null;
    if (base && L) {
      const x = legOrigin(base, L.brg, L.km);
      if (x) { o.est = x; o.estDir = 'next'; }
    }
  }
  return out;
}

/* ============= MODÈLE ============= */
function defaultTimes() {
  return ['d1', 'd2', 'd3', 'd4', 'd5'].map(k => ({ label: t('times.' + k), value: '' }));
}

function newCard() {
  return {
    meta: { classification: 'confidential', docRef: '', operation: '', mission: '', date: '', time: '' },
    flight: { callsign: '', aircraft: '', count: null, task: '', threat: '' },
    units: { mass: dgU.mass, distance: dgU.distance, altitude: dgU.altitude },       /* toujours égal à la clé mp_units_v1 (dgUnitsSet) */
    mission: { objective: '', execution: [] },
    times: defaultTimes(),
    crew: [],
    nav: [],
    navDisplay: { mode: 'course', ref: 'true', decl: '', vmode: 'calc' },
    refs: [],
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

/* Le mode de la déclinaison lu : gardé s'il est connu ; sinon « Saisie » quand une valeur saisie se lit (une carte d'avant ce mode
   ne change pas), « Calculée » sinon */
function readVMode(v, decl) {
  return (v === 'calc' || v === 'manual') ? v : (parseDecl(decl) != null ? 'manual' : 'calc');
}

/* La copie figée (c.frz) lue : radios [{ type, posts: [{ r, name, rows: [[canal, canal du cockpit, fréquence]] }] }], emports [{ names, type, lo, rows: [[point, CLSID]] }], bruts [noms] ; ce qui n'a pas la forme est écarté */
function normFrz(o) {
  const arr = v => Array.isArray(v) ? v : [];
  const radios = arr(o.radios).filter(m => gsIsObj(m) && typeof m.type === 'string' && Array.isArray(m.posts)).map(m => ({ type: m.type, posts: m.posts.filter(p => gsIsObj(p) && Array.isArray(p.rows)).map(p => ({ r: Number(p.r) || 0, name: str(p.name), rows: p.rows.filter(r => Array.isArray(r)).map(r => [Number(r[0]) || 0, str(r[1]), str(r[2])]) })) }));
  const loads = arr(o.loads).filter(x => gsIsObj(x) && typeof x.type === 'string' && gsIsObj(x.lo) && Array.isArray(x.rows)).map(x => ({ names: arr(x.names).map(str), type: x.type, lo: { key: str(x.lo.key), label: str(x.lo.label), from: str(x.lo.from), modified: x.lo.modified === true }, rows: x.rows.filter(r => Array.isArray(r)).map(r => [str(r[0]), str(r[1])]) }));
  return { radios: radios, loads: loads, raw: arr(o.raw).map(str) };
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
    /* une ligne d'une carte ancienne porte « crew » (l'équipier) : il est gardé après le pilote, « VIPER / HUSKER », et la clé disparaît */
    c.crew = src.crew.slice(0, LIMITS.crew).map(o => {
      let pilot = str(o && o.pilot);
      const old = str(o && o.crew).trim();
      if (old !== '') { pilot = pilot.trim(); pilot = pilot !== '' ? pilot + ' / ' + old : old; }
      const row = { callsign: str(o && o.callsign), pilot: pilot, type: str(o && o.type), board: str(o && o.board) };
      if (o && typeof o.dflt === 'string' && o.dflt !== '') row.dflt = o.dflt;       /* l'étiquette par défaut d'une unité d'une carte liée (le FC : groupe-rang) */
      return row;
    });
  }
  if (Array.isArray(src.nav)) {
    c.nav = src.nav.slice(0, LIMITS.nav).map(o => ({
      name: str(o && o.name), course: str(o && o.course), distance: str(o && o.distance),
      altitude: str(o && o.altitude), tos: str(o && o.tos), note: str(o && o.note), coord: str(o && o.coord)
    }));
  }
  const nd = src.navDisplay;
  if (nd && typeof nd === 'object') {
    if (NAV_MODES.indexOf(nd.mode) !== -1) c.navDisplay.mode = nd.mode;
    if (NAV_REFS.indexOf(nd.ref) !== -1) c.navDisplay.ref = nd.ref;
    if ('decl' in nd) c.navDisplay.decl = str(nd.decl);
    c.navDisplay.vmode = readVMode(nd.vmode, c.navDisplay.decl);
  }
  if (Array.isArray(src.refs)) {
    c.refs = src.refs.slice(0, LIMITS.refs).map(o => ({
      name: str(o && o.name), coord: str(o && o.coord), altitude: str(o && o.altitude), note: str(o && o.note)
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
  if (typeof src.gsId === 'string' && src.gsId !== '') {       /* carte liée à un groupe de la fiche (flight_set_v1) : son fcId, les canaux affichés, le choix de l'emport */
    c.gsId = src.gsId;
    c.gsSide = gsSide(src.gsSide);
    c.radioSel = {};
  }
  if ('loadoutFc' in src) c.loadoutFc = src.loadoutFc === true;       /* une carte devenue libre garde ses canaux affichés et le choix de l'emport (rien ne se perd) */
  if (src.radioSel && typeof src.radioSel === 'object' && !Array.isArray(src.radioSel)) {
    c.radioSel = {};
    Object.keys(src.radioSel).forEach(k => {
      const o = src.radioSel[k];
      if (o && typeof o === 'object') c.radioSel[k] = { on: o.on === true, label: str(o.label), mod: str(o.mod) };
    });
  }
  if (src.gsGone === true) c.gsGone = true;
  const fz = src.frz;
  if (gsIsObj(fz)) c.frz = normFrz(fz);
  if (!c.gsId) syncGroup(c);
  return c;
}

function normalizeDoc(src) {
  const d = { format: FORMAT_ID, mode: 'day', cards: [] };
  if (src && typeof src === 'object') {
    if (src.mode === 'night') d.mode = 'night';
    if (Array.isArray(src.cards)) d.cards = src.cards.map(normalizeCard);
    if (dgTheatreOk(src.theatre)) d.theatre = src.theatre;       /* le théâtre du document ; absent tant qu'aucun n'a été choisi ou pris */
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

/* ============= LE THÉÂTRE DU DOCUMENT (lot mp-dg-terrains-liste) =============
   Une clé de plus dans datacard_state_v1 : theatre, un des quatorze théâtres de DG_THEATRES (la liste de la barre, comme au Route Planner) ; absente tant qu'aucun théâtre n'a été choisi ou pris :
   le document est alors au théâtre par défaut du Route Planner. Le théâtre est partagé avec le Route Planner par la clé mp_theatre_v1 = { theatre } (sans horodatage : réécrire la même valeur ne déclenche aucun
   évènement « storage »), dans les deux sens : le dernier changement gagne. À vide, le document prend celui de la fiche des groupes, puis celui de la route enregistrée. */
const DG_THEATRES = ['Caucasus', 'GermanyCW', 'Syria', 'PersianGulf', 'Normandy', 'TheChannel', 'Nevada', 'MarianaIslands', 'MarianaIslandsWWII', 'Kola', 'SinaiMap', 'Iraq', 'Afghanistan', 'Falklands'];       /* les quatorze théâtres du Route Planner, dans son ordre ; les faits du jeu n'existent que pour onze d'entre eux */
const DG_THEATRE_DEFAULT = 'Caucasus';       /* le théâtre d'un profil neuf au Route Planner */
const KEY_THEATRE = 'mp_theatre_v1';
function dgTheatreOk(id) { return typeof id === 'string' && DG_THEATRES.indexOf(id) !== -1; }
function dgTheatre() { return dgTheatreOk(doc.theatre) ? doc.theatre : DG_THEATRE_DEFAULT; }
function dgReadTheatreKey() {
  try {
    const o = JSON.parse(localStorage.getItem(KEY_THEATRE));
    return o && typeof o === 'object' && dgTheatreOk(o.theatre) ? o.theatre : '';
  } catch (e) { return ''; }
}
function dgWriteTheatreKey(id) {
  if (dgReadTheatreKey() === id) return;       /* déjà là : aucune écriture */
  try { localStorage.setItem(KEY_THEATRE, JSON.stringify({ theatre: id })); } catch (e) { /* stockage indisponible : comme les autres écritures du module */ }
}
/* La liste de la barre : les quatorze théâtres, dans la langue de l'interface, au théâtre du document */
function dgFillTheatre() {
  const s = document.getElementById('theatre');
  if (!s) return;
  s.innerHTML = DG_THEATRES.map(id => '<option value="' + id + '">' + esc(t('th.' + id)) + '</option>').join('');
  s.value = dgTheatre();
}
/* Un théâtre choisi dans la liste de la barre, ou venu de l'autre module (fromKey) : le document le prend, la liste des terrains suit ; un choix de l'utilisateur est écrit dans mp_theatre_v1 */
function dgSetTheatre(id, fromKey) {
  if (!dgTheatreOk(id)) return;
  doc.theatre = id;
  if (!fromKey) dgWriteTheatreKey(id);
  const s = document.getElementById('theatre');
  if (s && s.value !== id) s.value = id;
  doc.cards.forEach(c => { const f = dgFlightOf(c); if (f) afRouteFill(c, f); });       /* DEP et ARR de la route, si la fiche est de ce théâtre */
  persistState();
  renderEditor(true);
  renderPreview();
}
/* L'autre module a écrit mp_theatre_v1 */
function dgFollowTheatre() {
  const k = dgReadTheatreKey();
  if (k && k !== doc.theatre) dgSetTheatre(k, true);
}
/* À vide, le théâtre du document est celui de la fiche des groupes, sinon celui de la route enregistrée ; rend vrai s'il en a pris un */
function dgAdoptTheatre() {
  if (doc.theatre) return false;
  let th = dgTheatreOk(DGG.theatre) ? DGG.theatre : '';
  if (!th) { const r = readJsonKey(KEY_ROUTE), rt = r && !Array.isArray(r) ? str(r.theatre) : ''; if (dgTheatreOk(rt)) th = rt; }
  if (!th) return false;
  doc.theatre = th;
  const s = document.getElementById('theatre');
  if (s && s.value !== th) s.value = th;
  return true;
}

/* ============= LES UNITÉS PARTAGÉES (lot mp-theatre-unique) =============
   Une clé de stockage, mp_units_v1 = { mass, distance, altitude } (kg|lb, km|nm, m|ft), que le Route Planner (distance, altitude) et ce module lisent et écrivent ; sans horodatage,
   écrite seulement si un champ diffère de ce qu'elle porte (réécrire la même valeur ne déclenche aucun évènement « storage » : c'est ce qui coupe la boucle), et jamais réécrite quand elle
   vient de l'autre module. Un champ absent ou invalide vaut kg, km, m. dgU est la valeur en cours : toute carte porte la même dans c.units (datacard_state_v1 et les fichiers écrits
   gardent leur format), et tout rendu lit dgU. Un document ouvert, importé ou lu d'une route donne sa première carte à la clé (dgUnitsAdopt) ; l'exemple suit la clé. */
const KEY_UNITS = 'mp_units_v1';
const UNITS_DEFAULT = { mass: 'kg', distance: 'km', altitude: 'm' };
const dgU = { mass: 'kg', distance: 'km', altitude: 'm' };
function dgUnitsNorm(o) {
  const r = {};
  Object.keys(UNITS_DEFAULT).forEach(k => { r[k] = o && typeof o === 'object' && UNIT_CHOICES[k].indexOf(o[k]) !== -1 ? o[k] : UNITS_DEFAULT[k]; });
  return r;
}
/* La clé lue et normalisée ; null si elle est absente ou n'est pas un objet */
function dgReadUnitsKey() {
  try {
    const o = JSON.parse(localStorage.getItem(KEY_UNITS));
    return o && typeof o === 'object' && !Array.isArray(o) ? dgUnitsNorm(o) : null;
  } catch (e) { return null; }
}
function dgWriteUnitsKey(u) {
  let raw = null;
  try { raw = JSON.parse(localStorage.getItem(KEY_UNITS)); } catch (e) { raw = null; }
  if (raw && typeof raw === 'object' && Object.keys(UNITS_DEFAULT).every(k => raw[k] === u[k])) return;       /* déjà là : aucune écriture */
  try { localStorage.setItem(KEY_UNITS, JSON.stringify({ mass: u.mass, distance: u.distance, altitude: u.altitude })); } catch (e) { /* stockage indisponible : comme les autres écritures du module */ }
}
/* Poser les unités : dgU, chaque carte, le menu ; la clé s'écrit sauf si elles viennent de la clé (fromKey). Rend vrai si elles ont changé. */
function dgUnitsSet(u, fromKey) {
  const n = dgUnitsNorm(u);
  const changed = Object.keys(UNITS_DEFAULT).some(k => dgU[k] !== n[k]);
  Object.assign(dgU, n);
  const stale = doc.cards.some(c => !c.units || Object.keys(UNITS_DEFAULT).some(k => c.units[k] !== n[k]));       /* une carte stockée qui diffère de la clé : elle est remise à la clé et la persistance a lieu */
  doc.cards.forEach(c => { c.units = { mass: n.mass, distance: n.distance, altitude: n.altitude }; });
  if (!fromKey) dgWriteUnitsKey(n);
  dgUnitsSync();
  if (changed || stale) { persistState(); renderEditor(true); renderPreview(); }
  return changed;
}
/* Un document ouvert, importé ou lu d'une route : les unités valides de sa première carte deviennent la clé */
function dgUnitsAdopt(units) { return dgUnitsSet(units); }
/* L'autre module a écrit mp_units_v1 */
function dgFollowUnits() {
  const k = dgReadUnitsKey();
  if (k && Object.keys(UNITS_DEFAULT).some(f => dgU[f] !== k[f])) dgUnitsSet(k, true);
}

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
  if (doc.theatre) next.theatre = doc.theatre;       /* ouvrir un fichier, l'exemple ou une carte blanche ne change pas le théâtre choisi ; un fichier n'en pose un que si le document n'en a pas */
  doc = next;
  doc.cards.forEach(c => { c.units = { mass: dgU.mass, distance: dgU.distance, altitude: dgU.altitude }; });       /* « Exemple », une carte blanche, un fichier : les cartes suivent la clé */
  curIdx = 0;
  const ts = document.getElementById('theatre');
  if (ts && ts.value !== dgTheatre()) ts.value = dgTheatre();       /* un fichier a pu poser le théâtre d'un document qui n'en avait pas */
  gsApplyAll(true);
  persistState();
  renderAll();
}

@@ROUTE_PACK_BLOCK@@
@@ROUTE_THEATRE_BLOCK@@
@@GROUP_STORE_BLOCK@@
@@IMPORT_BLOCK@@
const WEAPON_NAMES = @@WEAPON_NAMES@@;
const AIRCRAFT_PYLONS = @@AIRCRAFT_PYLONS@@;
const AIRCRAFT_LIMITS = @@AIRCRAFT_LIMITS@@;
@@PAYLOAD_BLOCK@@
/* ============= GROUPES PARTAGÉS (lot mp-dg-groupes) =============
   La fiche des groupes (flight_set_v1, bloc partagé) : une carte liée porte gsId (le fcId de son groupe). Ses champs de groupe (nom, camp, unités : indicatif,
   type, n° de bord ; fréquences ; emport) sont ceux de la fiche : ils se lisent à l'ouverture et à chaque évènement « storage », et chaque modification d'un
   de ces champs s'écrit dans la fiche par dgPut (gsPutFlight : le seul groupe touché, les clés inconnues gardées). Restent à la carte : le pilote (rangé par
   le rang de l'unité dans le groupe, la fiche n'ayant pas d'identifiant d'unité), les temps, la météo, le carburant, les notes, la navigation, les canaux
   affichés (radioSel : « type|poste|canal » → { on, label, mod }) et le choix de l'emport (loadoutFc). */
const DG_UNIT_TYPES = PAYLOAD_TYPES;
const DG_TYPE_LABEL = IMP_TYPE_LABEL;
const DG_MAX_UNITS = IMP_MAX_UNITS;
const DG_UI = { free: {} };       /* état d'écran : les canaux libres montrés, par « type|poste » */
let DGG = { flights: [], theatre: '', stable: '', shown: '', pend: false };       /* stable : la fiche lue ; shown : la fiche que l'écran montre ; pend : un évènement « storage » attend sa relecture */

function dgStr(v) { return typeof v === 'string' ? v : (typeof v === 'number' ? String(v) : ''); }
function dgCs(v) { return csText(v); }
function dgFlightLabel(f, fi) { return dgStr(f.name).trim() || t('fl.untitled', { n: fi + 1 }); }
function dgUnits(f) { return (Array.isArray(f.units) ? f.units : []).filter(gsIsObj); }
function dgUnitDefault(f, fi, ui) { return dgFlightLabel(f, fi) + '-' + (ui + 1); }
function dgUnitLabel(f, fi, ui) { const u = dgUnits(f)[ui]; return dgCs(u.callsign).trim() || dgStr(u.name).trim() || dgUnitDefault(f, fi, ui); }
function dgTypeLabel(ty) { return ty === '' ? t('sum.type.pick') : (Object.prototype.hasOwnProperty.call(DG_TYPE_LABEL, ty) ? DG_TYPE_LABEL[ty] : ty); }
function dgFlightPos(id) { return DGG.flights.findIndex(f => f.fcId === id); }
function dgFlightOf(c) { return c && c.gsId ? (DGG.flights.find(f => f.fcId === c.gsId) || null) : null; }
/* Le nom d'une carte dans la liste : l'indicatif ; sans lui, une carte liée prend le nom que le groupe a dans la fiche (« Groupe 4 », comme au Flight Configurator) */
function dgCardName(x, i) {
  const f = dgFlightOf(x);
  return x.flight.callsign.trim() || (f ? dgFlightLabel(f, dgFlightPos(f.fcId)) : t('pack.unnamed', { n: i + 1 }));
}
function dgPackFn(r, th) {
  let gs = 220;
  try { const st = JSON.parse(localStorage.getItem(KEY_ROUTE)); if (gsIsObj(st) && typeof st.groundSpeed === 'number' && st.groundSpeed > 0) gs = st.groundSpeed; } catch (e) { /* vitesse par défaut */ }
  return gsPackRoute(r, th, gs);
}
/* Un échec d'écriture de la fiche (stockage plein), dit une fois par série d'échecs */
function gsOnSaveFail() { showToast(t('toast.gsFull'), { type: 'err', ms: 6000 }); }

/* Les champs de groupe d'une carte liée, lus dans le groupe de la fiche ; le pilote reste à la carte (rang de l'unité) */
function dgApplyGroup(c, f, fi) {
  const units = dgUnits(f), old = Array.isArray(c.crew) ? c.crew : [];
  c.gsId = f.fcId;
  delete c.gsGone;
  c.gsSide = gsSide(f.coalition);
  c.flight.callsign = dgStr(f.name);
  c.crew = units.map((u, i) => ({ callsign: dgCs(u.callsign).trim(), dflt: dgUnitLabel(f, fi, i), pilot: old[i] ? str(old[i].pilot) : '', type: dgStr(u.type), board: dgStr(u.onboard) }));
  const types = [];
  units.forEach(u => { const ty = dgStr(u.type); if (ty && types.indexOf(ty) < 0) types.push(ty); });
  c.flight.count = units.length || null;
  c.flight.aircraft = types.join(' + ');
  if (!gsIsObj(c.radioSel)) c.radioSel = {};
  if (typeof c.loadoutFc !== 'boolean') c.loadoutFc = false;
  const z = dgFreeze(f, c);
  if (z) c.frz = z; else delete c.frz;
  afRouteFill(c, f);       /* DEP et ARR pris de la route du groupe */
}

/* La liste des cartes suit la fiche : les cartes liées dans l'ordre de la fiche, puis les cartes libres ; un groupe sans carte reçoit la sienne ;
   une carte dont le groupe a disparu devient libre (elle garde sa dernière copie des champs de groupe et le dit) */
function gsApplyAll(first) {
  const g = gsRead();
  if (g === null) return false;
  DGG.flights = g.flights; DGG.theatre = g.theatre; DGG.stable = gsStable(g);
  dgAdoptTheatre();
  const cur = doc.cards[curIdx] || null;
  const pos = new Map(g.flights.map((f, i) => [f.fcId, i]));
  const linked = [], free = [], seen = new Set();
  doc.cards.forEach(c => {
    if (c.gsId && pos.has(c.gsId) && !seen.has(c.gsId)) { seen.add(c.gsId); dgApplyGroup(c, g.flights[pos.get(c.gsId)], pos.get(c.gsId)); linked.push(c); }
    else if (c.gsId) { delete c.gsId; c.gsGone = true; free.push(c); }
    else free.push(c);
  });
  g.flights.forEach((f, i) => { if (!seen.has(f.fcId)) { const c = newCard(); dgApplyGroup(c, f, i); linked.push(c); } });
  linked.sort((a, b) => pos.get(a.gsId) - pos.get(b.gsId));
  doc.cards = linked.concat(linked.length && first ? free.filter(c => !isBlankCard(c)) : free);       /* une carte vierge intacte n'est écartée qu'au premier passage de la fiche (chargement, « Ouvrir ») : jamais sur un évènement « storage » ni après une écriture */
  if (!doc.cards.length) doc.cards = [newCard()];
  const k = cur ? doc.cards.indexOf(cur) : -1;
  curIdx = k >= 0 ? k : 0;
  return true;
}
/* Un autre onglet écrit la fiche en plusieurs temps : on relit après 300 ms de calme ; l'écran ne change que si la fiche a changé par rapport à ce qu'il montre
   (DGG.shown, pas DGG.stable : une écriture du DG dans ces 300 ms relit aussi ce que l'autre a écrit, l'écran n'en saurait rien) */
function dgStorage(e) {
  if (e.key !== null && e.key !== KEY_FLIGHT_SET) return;
  DGG.pend = true;
  clearTimeout(dgStorage._h);
  dgStorage._h = setTimeout(() => {
    DGG.pend = false;
    const g = gsRead();
    if (g === null || gsStable(g) === DGG.shown) return;
    if (gsApplyAll()) { persistState(); renderAll(true); }
  }, 300);
}
/* L'écran n'est plus à jour de la fiche (un autre module a écrit pendant une saisie) : il se redessine, la saisie en cours gardée */
function dgRefreshIfStale() {
  if (DGG.pend || DGG.shown === DGG.stable) return;
  renderAll(true);
}

/* ----- Écriture dans la fiche : relire, changer le seul groupe touché (une copie), gsPutFlight ; la carte suit la fiche ----- */
/* mut(copie du groupe) peut rendre faux pour ne rien écrire. Rend vrai si la fiche porte le groupe changé. */
function dgPut(id, mut) {
  const g = gsRead(), f = g && g.flights.find(x => x.fcId === id);
  if (!f) return false;
  const nf = clone(f);
  if (mut(nf) === false) return false;
  const ok = gsPutFlight(nf);
  gsApplyAll();
  persistState();
  if (!DGG.pend) DGG.shown = DGG.stable;       /* sans évènement en attente, l'écran (mis à jour champ par champ) suit la fiche ; sinon la relecture prévue le redessinera */
  return ok;
}
function dgUnitsOf(nf) { return (Array.isArray(nf.units) ? nf.units : []).filter(gsIsObj); }
/* Une unité qui porte des fréquences ou un emport (règle du Flight Configurator : changer son type ou la retirer les perd, avec confirmation) */
function dgUnitHasData(u) { return impRadioCount(u) > 0 || gsIsObj(u.loadout) || gsIsObj(u.payloadIn); }

/* Les champs Appareil et Nombre du groupe et les indicatifs par défaut suivent la fiche, sans refaire l'éditeur (le curseur reste en place) */
function dgSyncFields(c) {
  [['aircraft', c.flight.aircraft], ['count', c.flight.count == null ? '' : String(c.flight.count)]].forEach(p => {
    const el = document.querySelector('#editor [data-path="flight.' + p[0] + '"]');
    if (el && el.value !== p[1]) el.value = p[1];
  });
  const f = dgFlightOf(c), fi = f ? dgFlightPos(f.fcId) : -1;
  if (f) document.querySelectorAll('#editor [data-gs$=".callsign"]').forEach((el, i) => { el.placeholder = dgUnitDefault(f, fi, i); });
}
function dgAfterEdit(c) { dgSyncFields(c); renderPack(); renderPreview(); }

/* Un champ de groupe de l'éditeur : name, coalition, u.<rang>.callsign|type|onboard, f.<type|poste|canal> (fréquence) */
function onGsField(el, e) {
  const c = curCard();
  if (!c.gsId || !dgFlightOf(c)) return;
  const key = el.dataset.gs, isSel = el.tagName === 'SELECT';
  if (isSel && e.type !== 'change') return;
  if (key.indexOf('f.') === 0) {
    if (e.type === 'change') { el._dgPend = false; dgSetFreq(c, key.slice(2), el); }
    else { el._dgPend = true; dgFreqMsg(el, ''); }       /* saisie non validée : si un redessin fait perdre au navigateur son « change », la sortie du champ l'écrit (focusout) */
    return;
  }
  let m;
  if (key === 'name') { dgPut(c.gsId, nf => { nf.name = el.value; }); dgAfterEdit(c); return; }
  if (key === 'coalition') { dgPut(c.gsId, nf => { nf.coalition = gsSide(el.value); }); dgAfterEdit(c); return; }
  if ((m = /^u\.(\d+)\.(callsign|onboard)$/.exec(key))) {
    const i = parseInt(m[1], 10), k = m[2];
    dgPut(c.gsId, nf => { const u = dgUnitsOf(nf)[i]; if (!u) return false; u[k] = el.value; });
    dgAfterEdit(c);
    return;
  }
  if ((m = /^u\.(\d+)\.type$/.exec(key))) dgChangeType(c, parseInt(m[1], 10), el);
}
/* Le type d'une unité change : ses radios et son emport ne valent plus (ils suivent le type) ; s'il y en a à perdre, une confirmation, refusée la liste revient à l'ancien type */
function dgChangeType(c, i, el) {
  const f = dgFlightOf(c), u = f ? dgUnits(f)[i] : null, nt = el.value;
  if (!u || nt === u.type || DG_UNIT_TYPES.indexOf(nt) < 0) return;
  if (dgUnitHasData(u) && !confirm(t('u.type.confirm', { n: dgUnitLabel(f, dgFlightPos(f.fcId), i) }))) { renderEditor(); return; }
  dgPut(c.gsId, nf => { const x = dgUnitsOf(nf)[i]; if (!x) return false; x.type = nt; x.radios = {}; x.loadout = null; delete x.payloadIn; });
  renderEditor(); renderPack(); renderPreview();
}
/* Une unité de plus (du type de la dernière, comme au Flight Configurator) */
function dgAddUnit(c) {
  const f = dgFlightOf(c);
  if (!f || dgUnits(f).length >= DG_MAX_UNITS) return;
  dgPut(c.gsId, nf => { const us = dgUnitsOf(nf); nf.units.push(newUnit(us.length ? us[us.length - 1].type : IMP_DEFAULT_TYPE)); });
  renderEditor(); renderPack(); renderPreview();
  const el = document.querySelector('#editor [data-gs="u.' + (dgUnits(dgFlightOf(c) || { units: [] }).length - 1) + '.callsign"]');
  if (el) el.focus();
}
/* Une unité de moins (jamais la dernière) ; avec confirmation si elle porte des fréquences ou un emport (D3.1) ; son pilote part avec elle, les suivants remontent d'un rang */
function dgRemoveUnit(c, i) {
  const g = gsRead(), f = g ? g.flights.find(x => x.fcId === c.gsId) : null;
  if (!f) return;
  if (gsStable(g) !== DGG.shown) { if (gsApplyAll()) { persistState(); renderAll(true); } return; }       /* l'écran n'était plus à jour de la fiche : il l'est maintenant, rien n'est retiré sur une rangée périmée */
  const us = dgUnits(f);
  if (us.length < 2 || !us[i]) return;
  if (dgUnitHasData(us[i]) && !confirm(t('cr.rm.confirm', { n: dgUnitLabel(f, dgFlightPos(f.fcId), i) }))) return;
  const pilots = c.crew.map(x => x.pilot);
  c.crew.splice(i, 1);
  const ok = dgPut(c.gsId, nf => { const u = dgUnitsOf(nf)[i], k = u ? nf.units.indexOf(u) : -1; if (k < 0) return false; nf.units.splice(k, 1); });
  if (!ok) c.crew.forEach((x, k) => { x.pilot = pilots[k] !== undefined ? pilots[k] : x.pilot; });
  renderEditor(); renderPack(); renderPreview();
}
/* La bande de chaque poste, en MHz, [bas, haut] bornes comprises, sans contrôle de pas : celle de radio_bands_block.py (RADIO_BANDS, radioBand, radioInBand), le bloc que le Flight Configurator
   partage : c'est la règle des fréquences du groupe. Un poste que la mission ne pré-règle pas (RADIO_FREE : le poste HF des deux hélicoptères) n'a pas de numéro de canal. */
function dgPostFree(ty, r) { return radioFreeCount(ty, Number(r)) > 0; }
function dgFmtMHz(v) { return String(v).replace('.', CURRENT_LANG === 'fr' ? ',' : '.'); }
function dgBandText(ty, r) { return radioBand(ty, Number(r)).map(b => dgFmtMHz(b[0]) + '–' + dgFmtMHz(b[1])).join(' · ') + ' MHz'; }
/* Le message d'une fréquence déjà dans la fiche qui n'est pas dans la bande de son poste (ou n'est pas un nombre) ; '' si elle est bonne ou vide. Elle reste dans la fiche : le champ la signale seulement. */
function dgFreqIssue(ty, r, c, raw) {
  const p = dgParseFreq(raw), free = dgPostFree(ty, r), n = free ? c : radioCockpitChannel(ty, Number(r), c);
  if (p.nan) return t(free ? 'rad.err.nan.f' : 'rad.err.nan', { 0: n, 1: String(raw).trim() });
  if (p.v !== undefined && !radioInBand(radioBand(ty, Number(r)), p.v)) return t(free ? 'rad.err.range.f' : 'rad.err.range', { 0: n, 1: dgFmtMHz(p.v), 2: dgBandText(ty, r) });
  return '';
}
/* parseFreq du Flight Configurator : la virgule devient un point ; vide, nombre, ou pas une fréquence */
function dgParseFreq(s) {
  const x = String(s).trim().replace(',', '.');
  if (x === '') return { empty: true };
  return /^\d+(\.\d+)?$/.test(x) ? { v: Number(x), x: x } : { nan: true };
}
/* Une fréquence (MHz) écrite dans une case : trois décimales, comme la boîte Radio et la liste des terrains */
function dgFreqStr(v) { return v.toFixed(3); }
/* ============= TERRAINS : LISTE DES AÉRODROMES (lot mp-dg-terrains-liste) =============
   Les faits du jeu (airfield_facts.json, pydcs, LGPL-3.0) : { théâtre: [ [nom, lat, lon, pistes, radios], … ] } ; radios = [VHF haute, UHF, VHF basse, HF] en Hz, ou null.
   La liste des noms est celle du théâtre du document (la liste de la barre, comme au Route Planner).
   Rien n'est ajouté à l'état de la carte. Choisir un aérodrome dans la liste remplace toujours l'OACI, la piste et la fréquence (même saisies à la main) ; « Autre… » les vide ;
   DEP et ARR pris de la route et les rangées remplies après l'import d'un briefing ne remplissent que des cases vides.
   La piste est un seul sens (lot mp-dg-terrains-lisibilite) : les sens de l'aérodrome sont ses pistes du jeu éclatées (« 04R/22L » → 04R, 22L), sans doublon ; le sens proposé est celui face au vent de la Météo.
   AF_UI (état d'écran, jamais écrit) : other = les rangées dont le champ libre du nom est ouvert ; otherR = celles dont le champ libre de la piste est ouvert ; sig = les aérodromes de la route déjà posés, par carte. */
const AIRFIELD_FACTS = __AIRFIELD_FACTS__;
/* Les codes OACI d'aujourd'hui (airfield_icao.json, OurAirports, domaine public) : { théâtre: { nom: OACI } } ; un aérodrome absent a un code inconnu */
const AIRFIELD_ICAO = __AIRFIELD_ICAO__;
const AF_UI = { other: new WeakSet(), otherR: new WeakSet(), sig: new WeakMap() };
const AF_ROUTE_M = 5000;       /* l'aérodrome pris de la route : à 5 km au plus du premier (DEP) ou du dernier (ARR) point */

function afRows(th) { return Object.prototype.hasOwnProperty.call(AIRFIELD_FACTS, th) ? AIRFIELD_FACTS[th] : []; }
/* L'aérodrome de ce nom (rogné, casse exacte) dans le théâtre du document : la rangée des faits, ou null */
function afFind(name) {
  const n = str(name).trim();
  if (n === '') return null;
  return afRows(dgTheatre()).find(r => r[0] === n) || null;
}
/* Le type du groupe d'une carte liée (celui de sa première unité) ; '' pour une carte libre */
function afCardType(c) { const f = dgFlightOf(c), us = f ? dgUnits(f) : []; return us.length ? dgStr(us[0].type) : ''; }
/* La fréquence de tour (Hz) qui tombe dans la radio du groupe : postes du type dans l'ordre, dans chacun la première de VHF haute, UHF, VHF basse, HF qui est dans sa bande ;
   à défaut (carte libre, type ou bande inconnus, aucune fréquence dans aucune bande) la VHF haute */
function afTowerHz(radios, c) {
  const ty = afCardType(c);
  if (ty) {
    const posts = radioPostsOf(ty);
    for (let i = 0; i < posts.length; i++) {
      const band = radioBand(ty, posts[i]);
      if (!band.length) continue;
      for (let k = 0; k < radios.length; k++) if (radioInBand(band, radios[k] / 1e6)) return radios[k];
    }
  }
  return radios[0];
}
/* Le code OACI connu de l'aérodrome de ce nom dans ce théâtre, ou '' */
function afIcao(th, name) {
  const t = Object.prototype.hasOwnProperty.call(AIRFIELD_ICAO, th) ? AIRFIELD_ICAO[th] : null;
  return t && Object.prototype.hasOwnProperty.call(t, name) ? t[name] : '';
}
/* Les sens d'un aérodrome : ses pistes du jeu, dans l'ordre, éclatées en sens (« 04R/22L » → 04R, 22L), sans doublon ; aucun pour un aérodrome sans piste */
function afEnds(row) {
  const out = [];
  row[3].forEach(p => String(p).split('/').forEach(x => { x = x.trim(); if (x !== '' && out.indexOf(x) === -1) out.push(x); }));
  return out;
}
/* La direction du vent (degrés) de la boîte Météo, ou -1 : trois chiffres, une barre et une vitesse non nulle (« 180/10 », « 250/12G20 ») ; vitesse nulle, VRB/…, calme, vide ou autre : pas de vent lisible */
function afWindDir(w) {
  const m = /^(\d{3})\/(\d+)/.exec(str(w).trim());
  return m && parseInt(m[2], 10) > 0 ? parseInt(m[1], 10) : -1;
}
/* Le sens proposé : celui dont le cap (son numéro × 10°) fait le plus petit écart d'angle avec le vent, le premier à égalité ; sans vent lisible, le premier ; '' sans sens */
function afPickEnd(ends, wind) {
  if (!ends.length) return '';
  const dir = afWindDir(wind);
  if (dir < 0) return ends[0];
  let best = ends[0], bd = Infinity;
  ends.forEach(e => {
    const n = /^\d+/.exec(e);
    if (!n) return;
    const d = Math.abs(parseInt(n[0], 10) * 10 - dir) % 360, g = Math.min(d, 360 - d);
    if (g < bd) { bd = g; best = e; }
  });
  return best;
}
/* Ce que le jeu donne pour un aérodrome (rangée des faits du théâtre du document) : l'OACI, la piste (le sens proposé face au vent de la carte) et la fréquence (MHz, comme la boîte Radio) ; '' quand le jeu n'a rien */
function afGame(row, c) { return { icao: afIcao(dgTheatre(), row[0]), rwy: afPickEnd(afEnds(row), c.weather.wind), freq: row[4] ? dgFreqStr(afTowerHz(row[4], c) / 1e6) : '' }; }
/* Le nom se vide ou passe en champ libre : l'OACI, la piste et la fréquence se vident, saisies à la main comprises */
function afClearGame(f) { f.icao = ''; f.runway = ''; f.frequency = ''; }
/* Pose le nom de la rangée. Par défaut (un choix dans la liste) l'OACI, la piste et la fréquence prennent les valeurs du jeu et remplacent les précédentes, saisies à la main comprises ;
   avec only, seules les cases vides se remplissent (DEP et ARR de la route). Rend vrai si le nom est dans la liste. */
function afSetName(c, f, name, only) {
  f.name = name;
  const row = afFind(name);
  if (!row) return false;
  const g = afGame(row, c);
  if (!only || !hasText(f.icao)) f.icao = g.icao;
  if (!only || !hasText(f.runway)) f.runway = g.rwy;
  if (!only || !hasText(f.frequency)) f.frequency = g.freq;
  return true;
}
/* Distance (m) entre deux points lat/lon (haversine, rayon moyen de la Terre) */
function afDist(a, b, c, d) {
  const r = Math.PI / 180, p = (c - a) * r, q = (d - b) * r;
  const x = Math.sin(p / 2) * Math.sin(p / 2) + Math.cos(a * r) * Math.cos(c * r) * Math.sin(q / 2) * Math.sin(q / 2);
  return 12742000 * Math.asin(Math.min(1, Math.sqrt(x)));
}
/* L'aérodrome le plus proche d'un point dans un théâtre, à AF_ROUTE_M au plus : sa rangée des faits, ou null */
function afNearest(th, lat, lon) {
  let best = null, bd = Infinity;
  afRows(th).forEach(r => { const d = afDist(lat, lon, r[1], r[2]); if (d < bd) { bd = d; best = r; } });
  return best && bd <= AF_ROUTE_M ? best : null;
}
/* DEP et ARR pris de la route du groupe (les points en coordonnées DCS dans la fiche partagée). Appelée à chaque lecture de la fiche (gsApplyAll, par dgApplyGroup) : elle ne change que la carte,
   jamais la fiche, donc l'écriture d'une carte ne relance rien. Elle agit à l'ouverture et quand les aérodromes de la route changent (la signature, par carte), pas à chaque lecture :
   une rangée que l'utilisateur retire pendant la séance ne revient pas à la lecture suivante. Elle n'agit que si la fiche est du théâtre du document (les points sont dans ses coordonnées). */
function afRouteFill(c, f) {
  const th = DGG.theatre;
  if (th !== dgTheatre() || !afRows(th).length || !Object.prototype.hasOwnProperty.call(TM_PARAMS, th) || !gsIsObj(f.route)) return;
  const src = f.route.points, list = Array.isArray(src) ? src : (gsIsObj(src) ? Object.keys(src).filter(k => /^\d+$/.test(k)).sort((a, b) => a - b).map(k => src[k]) : []);
  const pts = list.filter(p => gsIsObj(p) && typeof p.x === 'number' && typeof p.y === 'number' && isFinite(p.x) && isFinite(p.y));
  if (!pts.length) return;
  const ends = [pts[0], pts[pts.length - 1]].map(p => { const ll = dcsToLl(th, p.x, p.y); return afNearest(th, ll.lat, ll.lon); });
  const sig = th + '|' + ends.map(r => r ? r[0] : '').join('|');
  if (AF_UI.sig.get(c) === sig) return;
  AF_UI.sig.set(c, sig);
  [['dep', ends[0]], ['arr', ends[1]]].forEach(e => {
    const role = e[0], r = e[1];
    if (!r) return;
    let row = c.fields.find(x => x.role === role);
    if (row) { if (hasText(row.name)) return; }
    else {
      if (c.fields.length >= LIMITS.fields) return;
      row = { role: role, icao: '', name: '', runway: '', frequency: '' };
      c.fields.splice(role === 'arr' ? c.fields.map(x => x.role).lastIndexOf('dep') + 1 : 0, 0, row);       /* DEP en tête, ARR juste après DEP */
    }
    afSetName(c, row, r[0], true);
  });
}

/* Après l'import d'un briefing : les rangées dont le nom est dans la liste du théâtre prennent l'OACI, la piste (le sens proposé) et la fréquence du jeu si leur case est vide ; une piste venue du briefing reste */
function afFillRows(c) {
  c.fields.forEach(f => {
    const row = afFind(f.name);
    if (!row) return;
    const g = afGame(row, c);
    if (!hasText(f.icao)) f.icao = g.icao;
    if (!hasText(f.runway)) f.runway = g.rwy;
    if (!hasText(f.frequency)) f.frequency = g.freq;
  });
}

/* Le champ Nom d'une rangée : la liste du thème (les aérodromes du théâtre du document, avec une recherche) et « Autre… » qui ouvre un champ libre ; un nom hors liste s'affiche dans le champ libre */
function afFreeInput(i, f) {
  return '<input type="text" class="af-free" data-path="fields.' + i + '.name" value="' + esc(f.name) + '"' + phAttr('fields.' + i + '.name') + ' autocomplete="off">';
}
function afNameHtml(f, i) {
  const hit = afFind(f.name);
  const other = AF_UI.other.has(f) || (hasText(f.name) && !hit);
  const cur = other ? '@other' : (hit ? hit[0] : '');
  const opt = (v, l, x) => '<option value="' + esc(v) + '"' + (v === cur ? ' selected' : '') + (x || '') + '>' + esc(l) + '</option>';
  let o = opt('', t('f.field.pick'));
  afRows(dgTheatre()).forEach(r => { o += opt(r[0], r[0]); });
  o += opt('@other', t('f.field.other'), ' data-keep');
  return '<div class="ed-field"><label>' + esc(t('f.field.name')) + '</label><select data-af="' + i + '" data-search data-search-empty="' + esc(t('f.noaf')) + '">' + o + '</select>' + (other ? afFreeInput(i, f) : '') + '</div>';
}
/* La case Piste d'une rangée : quand le nom est un aérodrome de la liste (champ libre du nom fermé) qui a au moins un sens, une liste (la liste du thème, comme le nom) de ses sens puis « Autre… » qui ouvre un champ libre ;
   une valeur qui n'est pas un sens de l'aérodrome (ancien document, saisie) s'affiche, intacte, dans le champ libre. Nom libre ou aérodrome sans piste : un champ texte. La valeur reste du texte dans fields[i].runway. */
function afRwyFreeInput(i, f) {
  return '<input type="text" class="af-free" data-path="fields.' + i + '.runway" value="' + esc(f.runway) + '"' + phAttr('fields.' + i + '.runway') + ' autocomplete="off">';
}
function afRwyHtml(f, i) {
  const hit = AF_UI.other.has(f) ? null : afFind(f.name), ends = hit ? afEnds(hit) : [];
  if (!ends.length) return fInput('f.field.runway', 'fields.' + i + '.runway', f.runway).replace('class="ed-field"', 'class="ed-field" data-rwcell');
  const cur = AF_UI.otherR.has(f) ? '@other' : (ends.indexOf(f.runway) !== -1 ? f.runway : (hasText(f.runway) ? '@other' : ''));       /* le champ libre ouvert le reste au redessin, comme pour le nom */
  const other = cur === '@other';
  const opt = (v, l, x) => '<option value="' + esc(v) + '"' + (v === cur ? ' selected' : '') + (x || '') + '>' + esc(l) + '</option>';
  let o = cur === '' ? opt('', t('f.field.pick')) : '';
  ends.forEach(e => { o += opt(e, e); });
  o += opt('@other', t('f.field.other'), ' data-keep');
  return '<div class="ed-field" data-rwcell><label>' + esc(t('f.field.runway')) + '</label><select data-afr="' + i + '" data-search data-search-empty="' + esc(t('f.norwy')) + '">' + o + '</select>' + (other ? afRwyFreeInput(i, f) : '') + '</div>';
}
/* Redessine la case Piste de la rangée (le nom ou la liste des sens a changé) */
function afRwyRefresh(li, f, i) {
  const cell = li && li.querySelector('[data-rwcell]');
  if (cell) cell.outerHTML = afRwyHtml(f, i);
}
/* Un choix dans la liste (le <select> reçoit input puis change : le second ne change plus rien) */
function onAfName(el) {
  const c = curCard(), i = parseInt(el.dataset.af, 10), f = c.fields[i];
  if (!f) return;
  const li = el.closest('.li'), v = el.value;
  const sync = () => { if (li) ['icao', 'frequency'].forEach(key => { const x = li.querySelector('[data-path="fields.' + i + '.' + key + '"]'); if (x && x.value !== f[key]) x.value = f[key]; }); };
  AF_UI.otherR.delete(f);
  if (v === '@other') {
    AF_UI.other.add(f);
    afClearGame(f);       /* « Autre… » vide l'OACI, la piste et la fréquence, saisies à la main comprises */
    afRwyRefresh(li, f, i);
    sync();
    if (li && !li.querySelector('.af-free[data-path$=".name"]')) {
      el.parentNode.insertAdjacentHTML('beforeend', afFreeInput(i, f));
      const fr = li.querySelector('.af-free[data-path$=".name"]');
      if (fr) fr.focus();
    }
    touch();
    return;
  }
  AF_UI.other.delete(f);
  if (v === '') { afClearGame(f); f.name = ''; }
  else afSetName(c, f, v);
  if (li) {
    const fr = li.querySelector('.af-free[data-path$=".name"]');
    if (fr) fr.remove();
    afRwyRefresh(li, f, i);
    sync();
  }
  touch();
}
/* Un choix dans la liste des sens : un sens remplace la piste ; « Autre… » ouvre le champ libre, la valeur présente y reste */
function onAfRwy(el) {
  const c = curCard(), i = parseInt(el.dataset.afr, 10), f = c.fields[i];
  if (!f) return;
  const li = el.closest('.li'), v = el.value;
  if (v === '@other') {
    AF_UI.otherR.add(f);
    if (li && !li.querySelector('.af-free[data-path$=".runway"]')) {
      el.parentNode.insertAdjacentHTML('beforeend', afRwyFreeInput(i, f));
      const fr = li.querySelector('.af-free[data-path$=".runway"]');
      if (fr) fr.focus();
    }
    touch();
    return;
  }
  AF_UI.otherR.delete(f);
  f.runway = v;
  if (li) { const fr = li.querySelector('.af-free[data-path$=".runway"]'); if (fr) fr.remove(); }
  touch();
}

/* Le message d'une fréquence refusée, sous la ligne du canal (et le champ marqué) ; '' l'efface */
function dgFreqMsg(el, msg) {
  const row = el.closest('.rc-row');
  el.classList.toggle('bad', !!msg);
  if (!row) return;
  let m = row.querySelector('.rc-msg');
  if (!msg) { if (m) m.remove(); return; }
  if (!m) { m = document.createElement('div'); m.className = 'rc-msg'; m.setAttribute('role', 'alert'); row.querySelector('.rc-top').after(m); }
  m.textContent = msg;
}
/* Une fréquence saisie s'écrit dans toutes les unités de ce type, selon la règle du Flight Configurator : la virgule vaut un point, une valeur non numérique ou hors de la bande
   du poste n'est pas écrite (le champ le dit et revient à la fiche), un champ vidé efface la fréquence. Si elle efface une différence entre les unités, une confirmation le dit avant (D9).
   La fiche est relue ici : ni les unités ni les valeurs comparées ne viennent d'un état périmé. */
function dgSameFreq(a, b) {
  const x = dgParseFreq(a), y = dgParseFreq(b);
  if (x.empty || y.empty) return !!x.empty && !!y.empty;
  return x.v !== undefined && y.v !== undefined && Math.abs(x.v - y.v) < 1e-9;
}
function dgSetFreq(c, key, el) {
  const g = gsRead(), f = g ? g.flights.find(x => x.fcId === c.gsId) : null, parts = key.split('|');
  if (!f || parts.length !== 3) return;
  const ty = parts[0], r = parts[1], ch = parts[2], us = dgUnits(f), idx = [];
  us.forEach((u, i) => { if (u.type === ty) idx.push(i); });
  if (!idx.length) return;
  const olds = idx.map(i => dgFreq(us[i], r, ch)), free = dgPostFree(ty, r), cock = free ? Number(ch) : radioCockpitChannel(ty, Number(r), Number(ch));
  /* la valeur est revenue à celle qu'avait le champ à l'entrée : rien ne s'écrit, aucune confirmation (que le canal diffère ou non) ; le champ montre ce que la fiche porte à cet instant (changée entre-temps ailleurs comprise) et sa base suit */
  if (el._dgBase !== undefined && dgSameFreq(el.value, el._dgBase)) { el.value = olds[0]; el._dgBase = olds[0]; dgFreqMsg(el, ''); return; }
  const p = dgParseFreq(el.value);
  let msg = '';
  if (p.nan) msg = t(free ? 'rad.err.nan.f' : 'rad.err.nan', { 0: cock, 1: el.value.trim() });
  else if (p.v !== undefined && !radioInBand(radioBand(ty, Number(r)), p.v)) msg = t(free ? 'rad.err.range.f' : 'rad.err.range', { 0: cock, 1: dgFmtMHz(p.v), 2: dgBandText(ty, r) });
  if (msg) { el.value = olds[0]; el._dgBase = olds[0]; dgFreqMsg(el, msg); return; }       /* refusée : rien n'est écrit, le champ revient à la fiche */
  const val = p.empty ? '' : (/\.\d{4,}$/.test(p.x) ? p.x : dgFreqStr(p.v));
  dgFreqMsg(el, '');
  if (olds.some(v => v !== olds[0])) {
    const fi = dgFlightPos(f.fcId);
    const list = idx.map((i, k) => dgUnitLabel(f, fi, i) + ' : ' + (olds[k] || '—')).join(' · ');
    if (!confirm(t(free ? 'rt.align.confirm.f' : 'rt.align.confirm', { list: list, freq: val || '—', n: idx.length, type: dgTypeLabel(ty) }))) { el.value = olds[0]; el._dgBase = olds[0]; return; }       /* refusé : le champ revient à ce que la fiche porte, rien n'est écrit */
  }
  el.value = val; el._dgBase = val;
  dgPut(c.gsId, nf => { const nus = dgUnitsOf(nf); idx.forEach(i => { const u = nus[i]; if (!u) return; if (!gsIsObj(u.radios)) u.radios = {}; if (!gsIsObj(u.radios[r])) u.radios[r] = {}; u.radios[r][ch] = val; }); });
  const row = document.querySelector('#editor [data-rc="' + key.replace(/"/g, '') + '"]'), v = row ? row.querySelector('.rc-var') : null;
  if (v) v.remove();
  renderPreview();
  dgRefreshIfStale();
}

/* ----- Radios : un encadré par type d'appareil du groupe ----- */
function dgFreq(u, r, c) { return gsIsObj(u.radios) && gsIsObj(u.radios[r]) && u.radios[r][c] !== undefined ? dgStr(u.radios[r][c]).trim() : ''; }
/* [{ type, units: [rang], posts: [{ r, name, rows: [{ c, cock, freq, varies, vals }] }] }] ; la fréquence d'un canal est celle de la première unité du type ; un poste non pré-réglé (le poste HF des
   hélicoptères) a des fréquences, sans numéro de canal : cock vaut '' */
function dgRadioModel(f) {
  const us = dgUnits(f), types = [];
  us.forEach(u => { const ty = dgStr(u.type); if (ty && types.indexOf(ty) < 0) types.push(ty); });
  return types.map(ty => {
    const idx = [];
    us.forEach((u, i) => { if (u.type === ty) idx.push(i); });
    const posts = radioPostsOf(ty).map(r => {
      const rows = [], free = dgPostFree(ty, r);
      for (let c = 1; c <= radioSlotsOf(ty, r); c++) {
        const vals = idx.map(i => dgFreq(us[i], r, c)), first = vals[0] || '';
        rows.push({ c: c, cock: free ? '' : radioCockpitChannel(ty, r, c), freq: first, varies: vals.some(v => v !== first), vals: vals });
      }
      return { r: r, name: radioPosteName(ty, r) || 'R' + r, rows: rows };
    });
    return { type: ty, units: idx, posts: posts };
  });
}
function dgRsKey(ty, r, c) { return ty + '|' + r + '|' + c; }
function dgRs(c, key) { const o = gsIsObj(c.radioSel) && gsIsObj(c.radioSel[key]) ? c.radioSel[key] : null; return { on: !!(o && o.on), label: o ? str(o.label) : '', mod: o ? str(o.mod) : '' }; }
function dgRowShown(row) { return row.vals.some(v => v !== ''); }
/* Les encadrés de la carte : les types qui ont au moins un canal coché ; [{ title, posts: [{ name, ch: [{ channel, label, frequency, modulation }] }] }] */
function dgRadioBoxes(c) {
  const f = dgFlightOf(c);
  return dgBoxesOf(c, f ? dgRadioModel(f) : dgFrozenModel(c));
}
function dgBoxesOf(c, model) {
  const out = [];
  model.forEach(m => {
    const posts = [];
    m.posts.forEach(p => {
      const ch = [];
      p.rows.forEach(row => {
        const s = dgRs(c, dgRsKey(m.type, p.r, row.c));
        if (s.on) ch.push(dgPostFree(m.type, p.r) ? { channel: '', nochan: true, label: s.label, frequency: row.freq, modulation: s.mod } : { channel: row.cock, label: s.label, frequency: row.freq, modulation: s.mod });
      });
      if (ch.length) posts.push({ name: p.name, ch: ch });
    });
    if (posts.length) out.push({ title: t('rt.title', { type: dgTypeLabel(m.type).toUpperCase() }), posts: posts });
  });
  return out;
}

/* ----- Emport : un tableau par emport distinct, sans dessin ; les intitulés sont ceux du Flight Configurator ----- */
/* L'intitulé d'un point comme le Flight Configurator l'affiche (weaponLabel, puis « (hors table) » si l'arme n'est pas permise à ce pylône) : payload_block.py est le même bloc */
function dgPylonLabel(type, n, clsid) {
  const nm = payloadWeaponName(clsid), side = nm ? payloadWeaponSide(type, clsid) : '';
  const lab = (nm ? (side ? nm + ' ' + t(side === 'L' ? 'w.left' : 'w.right') : nm) : '') || clsid;
  const p = (payloadPylons(type) || []).find(x => String(x.n) === String(n));
  return (p && p.allowed.indexOf(clsid) >= 0) ? lab : lab + ' ' + t('cmp.offTable');
}
/* Le nom de l'emport comme le Flight Configurator le donne (loadoutName) : l'étiquette (preset, « copié de … »), puis « · modifié » */
function dgLoadName(lo) {
  const lab = lo.key === 'copy' && typeof lo.from === 'string' ? t('cmp.copied', { n: lo.from }) : dgStr(lo.label);
  return lab + (lo.modified ? ' · ' + t('cmp.mod') : '');
}
function dgLoadRows(type, lo) {
  const py = gsIsObj(lo.pylons) ? lo.pylons : {};
  return Object.keys(py).filter(k => /^\d+$/.test(k) && gsIsObj(py[k]) && typeof py[k].CLSID === 'string' && py[k].CLSID !== '').sort((a, b) => Number(a) - Number(b)).map(k => ({ n: k, name: dgPylonLabel(type, k, py[k].CLSID), clsid: py[k].CLSID }));
}
/* { groups: [{ names, rows, name, type, lo }], none: [noms], raw: [noms] } : les unités au même emport (mêmes points chargés, même nom) partagent un tableau */
function dgLoadGroups(f) {
  const us = dgUnits(f), groups = [], none = [], raw = [];
  us.forEach((u, i) => {
    const lo = gsIsObj(u.loadout) && gsIsObj(u.loadout.pylons) ? u.loadout : null;
    const rows = lo ? dgLoadRows(dgStr(u.type), lo) : [];
    if (!rows.length) { (gsIsObj(u.payloadIn) && !lo ? raw : none).push(i); return; }
    const name = dgLoadName(lo), key = dgStr(u.type) + '\u0001' + name + '\u0001' + JSON.stringify(rows.map(r => [r.n, r.name]));
    const g = groups.find(x => x.key === key);
    if (g) g.idx.push(i); else groups.push({ key: key, idx: [i], rows: rows, name: name, type: dgStr(u.type), lo: lo });
  });
  groups.forEach(g => { g.names = dgNames(f, g.idx); });
  return { groups: groups, none: dgNames(f, none), raw: dgNames(f, raw) };
}
function dgNames(f, idx) { const fi = dgFlightPos(f.fcId); return idx.map(i => dgUnitLabel(f, fi, i)); }
/* Ce que l'aperçu tire de la fiche pour les radios et l'emport, gardé dans la carte (c.frz) à chaque lecture de la fiche : quand le groupe disparaît ou que la carte
   est détachée, la carte libre qui en naît montre la même chose, en lecture seule. Rien qui dépende de la langue n'y est écrit : les libellés se refont à l'affichage. */
function dgFreeze(f, c) {
  /* un poste non pré-réglé (le poste HF des hélicoptères) n'entre dans la copie que s'il porte une fréquence ou un canal coché : une carte qui n'en a pas garde la même copie qu'avant */
  const radios = dgRadioModel(f).map(m => ({ type: m.type, posts: m.posts.filter(p => !dgPostFree(m.type, p.r) || p.rows.some(r => r.freq !== '' || dgRs(c, dgRsKey(m.type, p.r, r.c)).on)).map(p => ({ r: p.r, name: p.name, rows: p.rows.map(r => [r.c, r.cock, r.freq]) })) }));
  const g = dgLoadGroups(f);
  const loads = g.groups.map(x => ({ names: x.names, type: x.type, lo: { key: dgStr(x.lo.key), label: dgStr(x.lo.label), from: dgStr(x.lo.from), modified: !!x.lo.modified }, rows: x.rows.map(r => [r.n, r.clsid]) }));
  const hasFreq = radios.some(m => m.posts.some(p => p.rows.some(r => r[2] !== '')));
  return (hasFreq || loads.length || g.raw.length) ? { radios: hasFreq ? radios : [], loads: loads, raw: g.raw } : null;
}
/* c.frz relu (carte libre née d'une carte liée) : les encadrés radio, comme dgRadioModel les donne */
function dgFrozenModel(c) {
  const z = !c.gsId && gsIsObj(c.frz) ? c.frz : null;
  if (!z) return [];
  return (Array.isArray(z.radios) ? z.radios : []).map(m => ({ type: m.type, posts: m.posts.map(p => ({ r: p.r, name: p.name, rows: p.rows.map(r => ({ c: r[0], cock: r[1], freq: r[2], vals: [r[2]], varies: false })) })) }));
}
/* La vue de l'emport d'une carte : celle de la fiche (carte liée) ou la copie figée (carte libre née d'une carte liée) */
function dgLoadView(c) {
  const f = dgFlightOf(c);
  if (f) return dgLoadGroups(f);
  const z = !c.gsId && gsIsObj(c.frz) ? c.frz : null;
  if (!z) return { groups: [], none: [], raw: [] };
  return {
    groups: (Array.isArray(z.loads) ? z.loads : []).map(x => ({ names: x.names, rows: x.rows.map(r => ({ n: r[0], name: dgPylonLabel(x.type, r[0], r[1]) })), name: dgLoadName(x.lo), type: x.type })),
    none: [], raw: Array.isArray(z.raw) ? z.raw : []
  };
}
/* Une carte libre née d'une carte liée porte-t-elle une copie figée à montrer ? */
function dgFrozen(c) { return !c.gsId && gsIsObj(c.frz) && ((Array.isArray(c.frz.radios) && c.frz.radios.length) || (Array.isArray(c.frz.loads) && c.frz.loads.length) || (Array.isArray(c.frz.raw) && c.frz.raw.length)); }
function dgLoadTable(rows, cls, head) {
  return '<table class="' + cls + '"><colgroup><col style="width:' + (head ? '40px' : '12%') + '"><col></colgroup><thead><tr><th>' + esc(t('lo.h.n')) + '</th><th>' + esc(t('lo.h.load')) + '</th></tr></thead><tbody>' +
    rows.map(r => '<tr><td class="n">' + esc(r.n) + '</td><td class="w">' + esc(r.name) + '</td></tr>').join('') + '</tbody></table>';
}
function dgLoadEditorHtml(c) {
  const g = dgLoadView(c);
  let h = '';
  g.groups.forEach(x => { h += '<div class="lo-grp"><div class="lo-t">' + esc(x.names.join(' · ') + (x.name ? ' — ' + x.name : '')) + '</div>' + dgLoadTable(x.rows, 'lo-tab', true) + '</div>'; });
  if (!g.groups.length) h += '<div class="ed-help">' + esc(t('lo.empty')) + '</div>';
  if (g.groups.length && g.none.length) h += '<div class="ed-help">' + esc(t('lo.none', { names: g.none.join(', ') })) + '</div>';
  if (g.raw.length) h += '<div class="ed-warn">' + esc(t('lo.raw', { names: g.raw.join(', ') })) + '</div>';
  return (c.gsId ? '' : '<div class="ed-help">' + esc(t('frz.note')) + '</div>') + h + (c.gsId ? '<div class="ed-help">' + esc(t('lo.fc.hint')) + '</div>' : '');
}
function dgLoadCardHtml(c) {
  const g = dgLoadView(c);
  let h = g.groups.map(x => '<div class="dc-lo"><div class="dc-lo-t">' + esc(x.names.join(' · ').toUpperCase() + (x.name ? ' — ' + x.name : '')) + '</div>' + dgLoadTable(x.rows, 'dc-tab dc-lot', false) + '</div>').join('');
  if (g.raw.length) h += '<div class="dc-lo-n">' + esc(t('lo.raw', { names: g.raw.join(', ') })) + '</div>';
  return h;
}

/* ----- Éditeur d'une carte liée ----- */
function shLabel(key) { return esc(t(key)) + ' <span class="sh" title="' + esc(t('sh.tip')) + '">FC</span>'; }
function fShared(labelKey, inner) { return '<div class="ed-field"><label>' + shLabel(labelKey) + '</label>' + inner + '</div>'; }
function selShared(gsKey, value, options) {
  return '<select data-gs="' + gsKey + '">' + options.map(o => '<option value="' + esc(o[0]) + '"' + (o[0] === value ? ' selected' : '') + '>' + esc(o[1]) + '</option>').join('') + '</select>';
}
/* La boîte « Groupe et équipage », la même pour une carte liée et une carte libre : le groupe (nom, coalition, appareil, nombre, tâche, menace), puis une ligne par unité
   (indicatif, type, n° de bord, pilote). Carte liée : nom, coalition, indicatif, type et n° de bord sont écrits dans le groupe de la fiche (pastille FC), appareil et nombre sont déduits ;
   carte libre : tout est saisi sur la carte, et la coalition n'existe pas (l'état d'une carte libre n'en porte pas). */
function groupBoxHtml(c) {
  const lk = !!c.gsId, f = lk ? dgFlightOf(c) : null;
  if (lk && !f) return '';
  const ro = (lk || deduceGroup(c)) ? ' readonly title="' + esc(t('f.group.deduced')) + '"' : '';
  const coal = [['', t('coal.none')], ['blue', t('coal.blue')], ['red', t('coal.red')]];
  const thr = fSelect('f.threat', 'flight.threat', c.flight.threat, [['', t('thr.none')], ['low', t('thr.low')], ['moderate', t('thr.moderate')], ['high', t('thr.high')]]);
  const head = (!lk && c.gsGone ? '<div class="ed-warn">' + esc(t('grp.gone')) + '</div>' : '') +
    '<div class="ed-field-row">' +
    (lk ? fShared('f.group.name', '<input type="text" data-gs="name" value="' + esc(dgStr(f.name)) + '" placeholder="' + esc(t('fl.name.ph')) + '" autocomplete="off" spellcheck="false">') + fShared('f.coalition', selShared('coalition', gsSide(f.coalition), coal))
      : fInput('f.group.name', 'flight.callsign', c.flight.callsign) + (c.gsGone && c.gsSide ? '<div class="ed-field"><label>' + esc(t('f.coalition')) + '</label><input type="text" value="' + esc(t('coal.' + c.gsSide)) + '" readonly tabindex="-1"></div>' : '<div class="ed-field"></div>')) + '</div>' +
    '<div class="ed-field-row">' + fInput('f.aircraft', 'flight.aircraft', c.flight.aircraft, ro) +
    fInput('f.count', 'flight.count', c.flight.count == null ? '' : String(c.flight.count), ' inputmode="numeric"' + ro) + '</div>' +
    '<div class="ed-field-row">' + fInput('f.task', 'flight.task', c.flight.task) + thr + '</div>';
  if (!lk) {
    /* même ligne que celle d'une carte liée : le ✕ en tête de ses boutons (même place, même taille, même infobulle), ▲ et ▼ en dessous */
    const frows = c.crew.map((x, i) =>
      '<div class="li li-u" data-list="crew" data-i="' + i + '"><div class="li-main">' +
      '<div class="li-uh"><span class="li-ut">' + esc(t('cr.unit', { n: i + 1 })) + '</span></div>' +
      '<div class="li-grid g2">' + fInput('f.crew.callsign', 'crew.' + i + '.callsign', x.callsign) + fInput('f.crew.type', 'crew.' + i + '.type', x.type) + '</div>' +
      '<div class="li-grid g2">' + fInput('f.crew.board', 'crew.' + i + '.board', x.board) + fInput('f.crew.pilot', 'crew.' + i + '.pilot', x.pilot) + '</div></div>' +
      '<div class="li-ctl"><button type="button" class="ed-btn-icon unit-x" data-act="remove" data-list="crew" data-i="' + i + '" title="' + esc(t('cr.remove')) + '" aria-label="' + esc(t('cr.remove')) + '">✕</button>' +
      '<button type="button" class="ed-btn-icon neutral" data-act="up" data-list="crew" data-i="' + i + '"' + (i === 0 ? ' disabled' : '') + ' title="' + esc(t('li.up')) + '" aria-label="' + esc(t('li.up')) + '">▲</button>' +
      '<button type="button" class="ed-btn-icon neutral" data-act="down" data-list="crew" data-i="' + i + '"' + (i === c.crew.length - 1 ? ' disabled' : '') + ' title="' + esc(t('li.down')) + '" aria-label="' + esc(t('li.down')) + '">▼</button></div></div>').join('');
    return head + '<div class="ed-list">' + frows + '</div>' +
      '<button type="button" class="ed-btn-add" data-act="add" data-list="crew"' + (c.crew.length >= LIMITS.crew ? ' disabled' : '') + '>' + esc(t('cr.add', { n: c.crew.length, max: LIMITS.crew })) + '</button>';
  }
  const units = dgUnits(f), fi = dgFlightPos(f.fcId);
  const opts = DG_UNIT_TYPES.map(ty => [ty, dgTypeLabel(ty)]);
  const rows = c.crew.map((x, i) => {
    const u = units[i] || {};
    const uo = dgStr(u.type) === '' ? [['', t('u.type.pick')]].concat(opts) : opts;       /* une unité sans type (que l'import commun produit pour un type inconnu) : « à choisir », comme au Flight Configurator */
    return '<div class="li li-u" data-unit="' + i + '"><div class="li-main">' +
      '<div class="li-uh"><span class="li-ut">' + esc(t('cr.unit', { n: i + 1 })) + '</span><span class="snap-tag">' + esc(dgTypeLabel(dgStr(u.type))) + '</span></div>' +
      '<div class="li-grid g2">' +
      fShared('f.crew.callsign', '<input type="text" data-gs="u.' + i + '.callsign" value="' + esc(dgCs(u.callsign)) + '" placeholder="' + esc(dgUnitDefault(f, fi, i)) + '" autocomplete="off" spellcheck="false">') +
      fShared('f.crew.type', selShared('u.' + i + '.type', dgStr(u.type), uo)) + '</div>' +
      '<div class="li-grid g2">' +
      fShared('f.crew.board', '<input type="text" data-gs="u.' + i + '.onboard" value="' + esc(dgStr(u.onboard)) + '" autocomplete="off" spellcheck="false">') +
      fInput('f.crew.pilot', 'crew.' + i + '.pilot', x.pilot) + '</div></div>' +
      '<div class="li-ctl"><button type="button" class="ed-btn-icon unit-x" data-gs-act="rm-unit" data-i="' + i + '"' + (units.length > 1 ? '' : ' disabled') + ' title="' + esc(t('cr.remove')) + '" aria-label="' + esc(t('cr.remove')) + '">✕</button></div></div>';
  }).join('');
  return head + '<div class="ed-list">' + rows + '</div>' +
    '<button type="button" class="ed-btn-add" data-gs-act="add-unit"' + (units.length >= DG_MAX_UNITS ? ' disabled' : '') + '>' + esc(t('cr.add', { n: units.length, max: DG_MAX_UNITS })) + '</button>' +
    '<div class="ed-help">' + esc(t('cr.legend')) + '</div>';
}
function radioLinkedHtml(c) {
  const f = dgFlightOf(c);
  if (!f) return '';
  const model = dgRadioModel(f), fi = dgFlightPos(f.fcId);
  if (!model.length) return '<div class="ed-help">' + esc(t('rt.none')) + '</div>';
  return '<div class="ed-help">' + esc(t('rt.legend')) + '</div>' + model.map(m => {
    const names = m.units.map(i => dgUnitLabel(f, fi, i)).join(', ');
    const posts = m.posts.map(p => {
      const fk = m.type + '|' + p.r, all = !!DG_UI.free[fk];
      const nFree = p.rows.filter(r => !dgRowShown(r)).length;
      const rows = p.rows.filter(r => all || dgRowShown(r)).map(row => {
        const key = dgRsKey(m.type, p.r, row.c), s = dgRs(c, key);
        const tip = row.varies ? row.vals.map((v, k) => dgUnitLabel(f, fi, m.units[k]) + ' : ' + (v || '—')).join(' · ') : '';
        const nc = dgPostFree(m.type, p.r), bad = dgFreqIssue(m.type, p.r, row.c, row.freq);       /* une fréquence hors bande déjà dans la fiche est gardée et signalée */
        return '<div class="rc-row' + (nc ? ' nc' : '') + (s.on ? ' on' : '') + '" data-rc="' + esc(key) + '"><div class="rc-top">' + (nc ? '' : '<span class="rc-ch">' + esc(t('rt.ch', { n: row.cock })) + '</span>') +
          '<div class="ed-field rc-freq"><input type="text" inputmode="decimal" data-gs="f.' + esc(key) + '" value="' + esc(row.freq) + '"' + (bad ? ' class="bad"' : '') + ' placeholder="—" autocomplete="off" spellcheck="false" aria-label="' + esc(nc ? t('rt.freq', { n: row.c }) : t('f.radio.frequency') + ' — ' + t('rt.ch', { n: row.cock })) + '"></div>' +
          '<label class="rc-on"><input type="checkbox" data-rs="' + esc(key) + '" data-rk="on"' + (s.on ? ' checked' : '') + '><span>' + esc(t('rt.on')) + '</span></label></div>' +
          (bad ? '<div class="rc-msg" role="alert">' + esc(bad) + '</div>' : '') +
          (row.varies ? '<div class="rc-var" title="' + esc(tip) + '">' + esc(t('rt.varies')) + '</div>' : '') +
          '<div class="rc-extra">' +
          '<div class="ed-field"><label>' + esc(t('rt.name')) + '</label><input type="text" data-rs="' + esc(key) + '" data-rk="label" value="' + esc(s.label) + '" placeholder="' + esc(t('ph.radios.*.channels.*.label')) + '" autocomplete="off"></div>' +
          '<div class="ed-field"><label>' + esc(t('rt.mod')) + '</label><input type="text" data-rs="' + esc(key) + '" data-rk="mod" value="' + esc(s.mod) + '" placeholder="' + esc(t('ph.radios.*.channels.*.modulation')) + '" autocomplete="off"></div></div></div>';
      }).join('');
      const fr = dgPostFree(m.type, p.r), more = nFree ? '<button type="button" class="ed-btn-add sm" data-rsfree="' + esc(fk) + '">' + esc(all ? t(fr ? 'rt.free.f.hide' : 'rt.free.hide') : t(fr ? 'rt.free.f' : 'rt.free', { n: nFree })) + '</button>' : '';
      return '<div class="rt-post"><div class="rt-ph">' + esc(p.name) + '</div>' + (rows || '<div class="ed-help">' + esc(t('rt.nofreq')) + '</div>') + more + '</div>';
    }).join('');
    return '<section class="rt-box" data-rtype="' + esc(m.type) + '"><h4 class="rt-h"><span class="rt-t">' + esc(t('rt.title', { type: dgTypeLabel(m.type).toUpperCase() })) + '</span>' +
      '<span class="rt-u">' + esc(t(m.units.length < 2 ? 'rt.units.1' : 'rt.units', { n: m.units.length, names: names })) + '</span></h4>' + posts + '</section>';
  }).join('');
}
function cardSummary(x) {
  if (x.gsId) {
    const types = [];
    x.crew.forEach(r => { if (r.type && types.indexOf(r.type) < 0) types.push(r.type); });
    return [t(x.crew.length < 2 ? 'sum.unit.1' : 'sum.unit', { n: x.crew.length }), types.map(dgTypeLabel).join(', '), x.gsSide ? t('coal.' + x.gsSide) : ''].filter(hasText).join(' · ');
  }
  return x.gsGone ? t('sum.gone') : (x.meta.operation.trim() || x.meta.mission.trim() || t('sum.free'));
}

/* ----- Fenêtres : nouvelle datacard, rattacher, supprimer ----- */
function grpModal(title, bodyHtml, buttons, kind) {
  const m = document.getElementById('grp-modal');
  DG_UI.grpKind = kind || '';
  m.querySelector('#grp-title').textContent = title;
  m.querySelector('#grp-body').innerHTML = bodyHtml;
  m.querySelector('#grp-actions').innerHTML = buttons.map(b => '<button type="button" class="' + b.cls + '" data-grp-act="' + b.act + '">' + esc(b.label) + '</button>').join('');
  m.hidden = false;
  const first = m.querySelector('input:not([disabled]), button');
  if (first) first.focus();
}
function grpClose() { document.getElementById('grp-modal').hidden = true; DG_UI.grpKind = ''; }
/* La langue change pendant que la fenêtre des groupes est ouverte : elle se refait dans la nouvelle langue, le nom saisi ou le groupe choisi gardés */
function grpRetranslate() {
  const m = document.getElementById('grp-modal'), k = DG_UI.grpKind;
  if (m.hidden || !k) return;
  const nm = document.getElementById('grp-name'), pick = m.querySelector('input[name="grp-pick"]:checked');
  const v = nm ? nm.value : '', pv = pick ? pick.value : '';
  if (k === 'new') { grpAskNew(); document.getElementById('grp-name').value = v; }
  else if (k === 'attach') {
    grpAskAttach();
    const r = pv ? Array.prototype.find.call(m.querySelectorAll('input[name="grp-pick"]'), x => x.value === pv) : null;
    if (r) { r.checked = true; document.querySelector('#grp-actions [data-grp-act="attach"]').disabled = false; }
  } else if (k === 'del') grpAskDelete();
}
function grpAskNew() {
  grpModal(t('m.new.title'), '<div class="fn-field"><label class="lbl" for="grp-name">' + esc(t('f.group.name')) + '</label><div class="fn-row"><input class="in" id="grp-name" type="text" autocomplete="off" spellcheck="false" placeholder="' + esc(t('fl.name.ph')) + '"></div></div>',
    [{ cls: 'export-png-back', act: 'cancel', label: t('m.cancel') }, { cls: 'export-png-go', act: 'new', label: t('m.new.go') }], 'new');
}
/* « Rattacher à un groupe » (carte libre) : tous les groupes de la fiche ; la carte que le groupe avait devient libre (intacte) */
function grpAskAttach() {
  const cardOf = new Map();
  doc.cards.forEach(x => { if (x.gsId) cardOf.set(x.gsId, x); });
  const rows = DGG.flights.map((f, i) => {
    const k = cardOf.get(f.fcId), sub = t(dgUnits(f).length < 2 ? 'sum.unit.1' : 'sum.unit', { n: dgUnits(f).length }) + (k ? ' · ' + t('m.att.hascard', { n: dgCardName(k, doc.cards.indexOf(k)) }) : '');
    return '<label class="grp-opt"><input type="radio" name="grp-pick" value="' + esc(f.fcId) + '"><span class="grp-nm">' + esc(dgFlightLabel(f, i)) + '</span><span class="grp-sub">' + esc(sub) + '</span></label>';
  }).join('');
  grpModal(t('m.att.title'), '<p class="grp-p">' + esc(t('m.att.text')) + '</p>' + rows + (DGG.flights.length ? '' : '<p class="grp-p grp-empty">' + esc(t('m.att.empty')) + '</p>'),
    [{ cls: 'export-png-back', act: 'cancel', label: t('m.cancel') }, { cls: 'export-png-go', act: 'attach', label: t('m.att.go') }], 'attach');
  document.querySelector('#grp-actions [data-grp-act="attach"]').disabled = true;
}
/* Supprimer une carte liée supprime le groupe pour tous les modules : une seule voie, après confirmation */
function grpAskDelete() {
  const c = curCard();
  const nm = dgCardName(c, curIdx);
  grpModal(t('m.del.title', { n: nm }), '<p class="grp-p">' + esc(t('m.del.text', { n: nm })) + '</p>',
    [{ cls: 'export-png-back', act: 'cancel', label: t('m.cancel') }, { cls: 'export-png-go grp-danger', act: 'del-both', label: t('m.del.both') }], 'del');
}
function grpAct(act) {
  const c = curCard();
  if (act === 'cancel') { grpClose(); return; }
  if (act === 'new') {
    const name = (document.getElementById('grp-name').value || '').trim(), before = new Set(DGG.flights.map(f => f.fcId));
    grpClose();
    if (!gsPutFlight({ fcId: gsNewId(), name: name, coalition: '', route: null, units: [newUnit()] })) return;
    gsApplyAll();
    curIdx = Math.max(0, doc.cards.findIndex(x => x.gsId && !before.has(x.gsId)));
  } else if (act === 'attach') {
    const pick = document.querySelector('#grp-body input[name="grp-pick"]:checked');
    grpClose();
    const f = pick ? DGG.flights.find(x => x.fcId === pick.value) : null;
    if (!f || c.gsId) return;
    const prev = doc.cards.find(x => x.gsId === f.fcId);
    if (prev) delete prev.gsId;       /* la carte qu'avait ce groupe devient libre, intacte : rien ne se perd */
    c.gsId = f.fcId;
    gsApplyAll();
  } else if (act === 'del-both') {
    const id = c.gsId;
    grpClose();
    if (!id || !gsRemoveFlight(id)) return;
    doc.cards.splice(curIdx, 1);
    if (!doc.cards.length) doc.cards = [newCard()];
    gsApplyAll();
    curIdx = Math.min(curIdx, doc.cards.length - 1);
  }
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

  c.crew = pilots.slice(0, LIMITS.crew).map(p => ({ callsign: str(p && p.callsign), pilot: str(p && p.name), type: '', board: '' }));
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

/* La datacard des données générales d'un briefing (celles qui ne dépendent d'aucun vol). */
function cardFromGeneral(b) {
  const c = newCard();
  const meta = (b.meta && typeof b.meta === 'object') ? b.meta : {};
  c.meta.classification = normClassif(meta.classification, 'confidential');
  ['docRef', 'operation', 'mission', 'date', 'time'].forEach(k => { c.meta[k] = str(meta[k]); });
  const mi = (b.mission && typeof b.mission === 'object') ? b.mission : {};
  c.mission.execution = (Array.isArray(mi.objectives) ? mi.objectives : []).map(str).filter(hasText).slice(0, LIMITS.steps);
  c.radios = radiosFromBriefing(b, '');
  c.fields = (Array.isArray(mi.farp) ? mi.farp : []).filter(f => f && typeof f === 'object').slice(0, LIMITS.fields)
    .map(f => ({ role: '', icao: str(f.icao), name: str(f.name), runway: str(f.rwy), frequency: '' }));
  const si = (b.sitac && typeof b.sitac === 'object') ? b.sitac : {};
  c.weather.metar = str(si.metar);
  const dm = decodeMetar(c.weather.metar);
  c.weather.wind = dm.wind; c.weather.visibility = dm.visibility; c.weather.qnh = dm.qnh; c.weather.clouds = dm.clouds;
  const th = (mi.threats && typeof mi.threats === 'object') ? mi.threats : {};
  c.threats = splitThreats(th.sam).concat(splitThreats(th.aaa)).slice(0, LIMITS.threats);
  c.notes = str(th.note);
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
function unitLabel(c, kind) { return t('u.' + dgU[kind]); }       /* tout rendu lit la clé partagée */

function anyText(o, keys) { return keys.some(k => hasText(o[k])); }
const CREW_KEYS = ['callsign', 'pilot', 'type', 'board'];
/* Le groupe déduit des lignes d'équipage : au moins une ligne non vide et un type sur chacune ; sinon null.
   types : [[type, nombre]] dans l'ordre des lignes ; aircraft : les types joints par « + » ; count : le nombre de lignes */
function deduceGroup(c) {
  const rows = c.crew.filter(r => anyText(r, CREW_KEYS));
  if (!rows.length || rows.some(r => !hasText(r.type))) return null;
  const types = [];
  rows.forEach(r => {
    const ty = r.type.trim();
    const e = types.find(x => x[0] === ty);
    if (e) e[1]++; else types.push([ty, 1]);
  });
  return { types: types, aircraft: types.map(x => x[0]).join(' + '), count: rows.length };
}
/* Quand le groupe se déduit, la carte enregistre l'appareil et le nombre déduits */
function syncGroup(c) {
  const d = deduceGroup(c);
  if (d) { c.flight.aircraft = d.aircraft; c.flight.count = d.count; }
  return !!d;
}
function navRows(c) { return c.nav.filter(r => anyText(r, NAV_KEYS)); }
/* Points de référence : une rangée dont aucun champ n'est rempli n'existe pas pour le bloc. */
const REF_KEYS = ['name', 'coord', 'altitude', 'note'];
function refRows(c) { return c.refs.filter(r => anyText(r, REF_KEYS)); }

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

function crewHead(withCrew) {
  const cols = withCrew
    ? '<col style="width:36%"><col style="width:26%"><col style="width:26%"><col>'
    : '<col style="width:42%"><col style="width:42%"><col>';
  let h = '<th>' + esc(t('dc.h.callsign')) + '</th><th>' + esc(t('dc.h.pilot')) + '</th>';
  if (withCrew) h += '<th>' + esc(t('dc.h.crew')) + '</th>';
  h += '<th>' + esc(t('dc.h.board')) + '</th>';
  return { cols: cols, h: h };
}
function blkCrew(c) {
  const rows = c.crew.filter(r => anyText(r, CREW_KEYS));
  if (!rows.length) return '';
  const withCrew = rows.some(r => hasText(r.type));
  const hd = crewHead(withCrew), cols = hd.cols, h = hd.h;
  const body = rows.map(r =>
    '<tr><td class="nm">' + esc(r.callsign || r.dflt || '') + '</td><td class="m">' + esc(r.pilot) + '</td>' +
    (withCrew ? '<td class="m">' + esc(r.type) + '</td>' : '') +
    '<td class="m">' + esc(r.board) + '</td></tr>').join('');
  return blockHtml('crew', t('dc.b.crew'),
    '<table class="dc-tab dc-crew"><colgroup>' + cols + '</colgroup><thead><tr>' + h + '</tr></thead><tbody>' + body + '</tbody></table>', 'dc-bbt');
}

/* Décimale de la déclinaison pour le titre : 3 → « 3 », 2.5 → « 2,5 » en français, « 2.5 » en anglais */
function fmtDecl(v) {
  const x = String(+Math.abs(v).toFixed(2));
  return CURRENT_LANG === 'fr' ? x.replace('.', ',') : x;
}

/* Colonnes du bloc Navigation selon l'affichage (largeurs en px ; la dernière colonne, la note, prend le reste) */
const NAV_COLS = {
  course: [50, 288, 90, 108, 89, 136],
  mgrs:   [50, 262, 236, 84, 100],
  dms:    [50, 224, 290, 84, 100]
};

/* L'en-tête du tableau de navigation selon l'affichage ; hc : l'intitulé de la colonne du cap (mode « course ») */
function navHead(c, mode, hc) {
  const du = unitLabel(c, 'distance'), au = unitLabel(c, 'altitude');
  if (mode === 'course') {
    return '<th>#</th><th>' + esc(t('dc.h.point')) + '</th>' +
      '<th class="r">' + esc(hc) + '</th>' +
      '<th class="r">' + esc(t('dc.h.dist', { u: du })) + '</th>' +
      '<th class="r">' + esc(t('dc.h.alt', { u: au })) + '</th>' +
      '<th class="r">' + esc(t('dc.h.tos')) + '</th>' +
      '<th>' + esc(t('dc.h.note')) + '</th>';
  }
  return '<th>#</th><th>' + esc(t('dc.h.point')) + '</th>' +
    '<th class="cc">' + esc(t(mode === 'mgrs' ? 'dc.h.mgrs' : 'dc.h.coord')) + '</th>' +
    '<th class="r">' + esc(t('dc.h.alt', { u: au })) + '</th>' +
    '<th class="r">' + esc(t('dc.h.tos')) + '</th>' +
    '<th>' + esc(t('dc.h.note')) + '</th>';
}
function navTable(mode, head, body) {
  const cols = '<colgroup>' + NAV_COLS[mode].map(w => '<col style="width:' + w + 'px">').join('') + '<col></colgroup>';
  return '<table class="dc-tab dc-nav' + (mode === 'course' ? '' : ' dc-navc') + '">' + cols +
    '<thead><tr>' + head + '</tr></thead><tbody>' + body + '</tbody></table>';
}

function blkNav(c) {
  const rows = navRows(c);
  if (!rows.length) return '';
  const nd = c.navDisplay, mode = nd.mode;
  const legs = navLegs(c);
  const shown = [];
  c.nav.forEach((r, i) => { if (anyText(r, NAV_KEYS)) shown.push({ r: r, g: legs[i] }); });
  let title = t('dc.b.nav'), head, body;
  if (mode === 'course') {
    const calcAny = shown.some(x => x.g.calc);
    const nv = navVar(c);
    if (calcAny) {
      if (!nv) title = t('dc.b.nav.true');
      else if (!nv.calc) title = t('dc.b.nav.mag', { d: fmtDecl(nv.decl), h: nv.decl >= 0 ? 'E' : 'W' });
      else {
        const vs = shown.filter(x => x.g.calc).map(x => x.g.calc.v);
        const a = fmtVar(Math.min.apply(null, vs)), b = fmtVar(Math.max.apply(null, vs)), yr = String(Math.floor(nv.y));
        title = a === b ? t('dc.b.nav.calc1', { a: yr, v: a }) : t('dc.b.nav.calc', { a: yr, min: a, max: b });
      }
    }
    const hc = calcAny ? t(nv ? 'dc.h.course.m' : 'dc.h.course.t') : t('dc.h.course');
    head = navHead(c, mode, hc);
    body = shown.map((x, i) => {
      const r = x.r, k = x.g.calc;
      return '<tr><td class="m ix">' + i + '</td><td class="nm">' + esc(r.name) + '</td>' +
        '<td class="m r">' + (k ? esc(k.cap) : dash(r.course)) + '</td><td class="m r">' + (k ? esc(k.dist) : dash(r.distance)) + '</td>' +
        '<td class="m r">' + dash(r.altitude) + '</td><td class="m r">' + dash(r.tos) + '</td>' +
        '<td class="nt">' + esc(r.note) + '</td></tr>';
    }).join('');
  } else {
    head = navHead(c, mode, '');
    body = shown.map((x, i) => {
      const r = x.r, p = x.g.pt || x.g.est;
      const cc = p ? esc(mode === 'mgrs' ? (toMGRS(p.lat, p.lon) || '—') : toDMS(p.lat, p.lon)) : esc('—');
      return '<tr><td class="m ix">' + i + '</td><td class="nm">' + esc(r.name) + '</td>' +
        '<td class="m cc">' + cc + '</td>' +
        '<td class="m r">' + dash(r.altitude) + '</td><td class="m r">' + dash(r.tos) + '</td>' +
        '<td class="nt">' + esc(r.note) + '</td></tr>';
    }).join('');
  }
  return blockHtml('nav', title, navTable(mode, head, body), 'dc-bbt');
}

/* Largeurs du bloc Points de référence (px ; la note, dernière colonne, prend le reste) */
const REF_COLS = {
  mgrs: [50, 262, 236, 84],
  dms:  [50, 224, 290, 84]
};

/* Bloc « Points de référence » : le tableau de la navigation en mode coordonnées (mêmes classes), sans heure */
function refsHead(c, mode) {
  const au = unitLabel(c, 'altitude');
  return '<th>#</th><th>' + esc(t('dc.h.point')) + '</th>' +
    '<th class="cc">' + esc(t(mode === 'mgrs' ? 'dc.h.mgrs' : 'dc.h.coord')) + '</th>' +
    '<th class="r">' + esc(t('dc.h.alt', { u: au })) + '</th>' +
    '<th>' + esc(t('dc.h.note')) + '</th>';
}
function refsTable(mode, head, body) {
  const cols = '<colgroup>' + REF_COLS[mode].map(w => '<col style="width:' + w + 'px">').join('') + '<col></colgroup>';
  return '<table class="dc-tab dc-nav dc-navc dc-refs">' + cols +
    '<thead><tr>' + head + '</tr></thead><tbody>' + body + '</tbody></table>';
}
function blkRefs(c) {
  const rows = refRows(c);
  if (!rows.length) return '';
  const mode = c.navDisplay.mode === 'dms' ? 'dms' : 'mgrs';
  const head = refsHead(c, mode);
  const body = rows.map((r, i) => {
    const p = parseCoord(r.coord);
    const cc = p ? esc(mode === 'mgrs' ? (toMGRS(p.lat, p.lon) || '—') : toDMS(p.lat, p.lon)) : esc('—');
    return '<tr><td class="m ix">' + String.fromCharCode(65 + i) + '</td><td class="nm">' + esc(r.name) + '</td>' +
      '<td class="m cc">' + cc + '</td>' +
      '<td class="m r">' + dash(r.altitude) + '</td>' +
      '<td class="nt">' + esc(r.note) + '</td></tr>';
  }).join('');
  return blockHtml('refs', t('dc.b.refs'), refsTable(mode, head, body), 'dc-bbt');
}

/* Le tableau d'un encadré Radio : une ligne de nom par poste ; rangées alternées recommencées à chaque poste (la 1re surlignée) ;
   filet plein au-dessus du nom de chaque poste sauf le premier (ou de sa 1re rangée s'il n'a pas de nom). */
function radioTable(radios) {
  const rows = radios.map((r, ri) => {
    let s = '';
    if (hasText(r.name)) s += '<tr class="rsep' + (ri ? ' rsep-n' : '') + '"><td class="dc-rname" colspan="4">' + esc(r.name) + '</td></tr>';
    s += r.ch.map((x, k) => {
      const cl = [k % 2 === 0 ? 'z' : '', (k === 0 && ri && !hasText(r.name)) ? 'pn' : '', x.blank ? 'dc-bl' : ''].filter(Boolean).join(' ');
      return '<tr' + (cl ? ' class="' + cl + '"' : '') + '><td>' + (x.nochan || x.blank ? '' : dash(x.channel)) + '</td><td class="us">' + esc(x.label) + '</td>' +
        '<td class="fq">' + (x.blank ? '' : dash(x.frequency)) + '</td><td class="md">' + esc(x.modulation) + '</td></tr>';
    }).join('');
    return s;
  }).join('');
  return '<table class="dc-tab dc-radio"><colgroup><col style="width:58px"><col style="width:178px"><col style="width:195px"><col></colgroup>' +
    '<thead><tr><th>' + esc(t('dc.h.ch')) + '</th><th>' + esc(t('dc.h.use')) + '</th><th>' + esc(t('dc.h.freq')) + '</th><th></th></tr></thead>' +
    '<tbody>' + rows + '</tbody></table>';
}
function blkRadio(c) {
  /* carte liée (ou carte libre née d'une carte liée : sa copie figée) : un encadré « RADIO — <TYPE> » par type qui a au moins un canal coché */
  const boxes = dgRadioBoxes(c).map(b => blockHtml('radio', b.title, radioTable(b.posts), 'dc-bbt'));
  const boxHtml = boxes.length > 1 ? '<div class="dc-col">' + boxes.join('') + '</div>' : (boxes[0] || '');
  if (c.gsId) return boxHtml;
  const radios = c.radios.map(r => ({
    name: r.name,
    ch: r.channels.filter(x => anyText(x, ['channel', 'label', 'frequency', 'modulation']))
  })).filter(r => hasText(r.name) || r.ch.length);
  if (!radios.length) return boxHtml;
  return boxHtml + blockHtml('radio', t('dc.b.radio'), radioTable(radios), 'dc-bbt');
}

/* Les postes de la page Radios : chacun avec son en-tête, ses canaux sur 3 colonnes (lecture colonne par colonne : 1-7, 8-14, 15-20) */
function blkRadioPage(c) {
  const own = c.gsId ? [] : c.radios.map(r => ({
    name: r.name,
    ch: r.channels.filter(x => anyText(x, ['channel', 'label', 'frequency', 'modulation']))
  }));
  const radios = dgRadioBoxes(c).reduce((a, b) => a.concat(b.posts.map(p => ({ name: b.title + ' · ' + p.name, ch: p.ch }))), []).concat(own).filter(r => hasText(r.name) || r.ch.length);
  if (!radios.length) return '';
  const head = '<thead><tr><th>' + esc(t('dc.h.ch')) + '</th><th>' + esc(t('dc.h.use')) + '</th><th>' + esc(t('dc.h.freq')) + '</th><th></th></tr></thead>';
  const colg = '<colgroup><col style="width:46px"><col><col style="width:118px"><col style="width:40px"></colgroup>';
  const body = radios.map((r, ri) => {
    const per = Math.max(1, Math.ceil(r.ch.length / 3));
    let cols = '';
    for (let k = 0; k < 3; k++) {
      const part = r.ch.slice(k * per, (k + 1) * per);
      if (!part.length) { cols += '<div></div>'; continue; }
      cols += '<table class="dc-tab dc-radio dc-radio3">' + colg + '<tbody>' + part.map((x, j) =>
        '<tr' + (j % 2 === 0 ? ' class="z"' : '') + '><td>' + (x.nochan ? '' : dash(x.channel)) + '</td><td class="us">' + esc(x.label) + '</td>' +
        '<td class="fq">' + dash(x.frequency) + '</td><td class="md">' + esc(x.modulation) + '</td></tr>').join('') + '</tbody></table>';
    }
    return '<div class="dc-rposte' + (ri ? ' dc-rposte-n' : '') + '">' + (hasText(r.name) ? '<div class="dc-rname">' + esc(r.name) + '</div>' : '') +
      '<div class="dc-rcols">' + cols + '</div></div>';
  }).join('');
  /* une seule ligne d'en-têtes pour toute la page, au-dessus des trois colonnes */
  const heads = '<div class="dc-rcols dc-rheads">' + [0, 1, 2].map(() => '<table class="dc-tab dc-radio dc-radio3">' + colg + head + '</table>').join('') + '</div>';
  return blockHtml('radio', t('dc.b.radio'), heads + body, 'dc-bbt');
}

/* La piste au rendu : une coupure possible après chaque virgule (<wbr>, jamais dans la valeur gardée), jamais dans « 23L/05R » */
function rwyHtml(v) { return hasText(v) ? esc(v).replace(/,/g, ',<wbr>') : '\u2014'; }
/* La fréquence au rendu : l'espace qui précède un « / » est insécable (jamais dans la valeur gardée), la barre reste au bout de la première fréquence */
function freqHtml(v) { return hasText(v) ? esc(v).replace(/ +\//g, '&nbsp;/') : '\u2014'; }
function blkFields(c) {
  const rows = c.fields.filter(f => anyText(f, ['icao', 'name', 'runway', 'frequency']));
  if (!rows.length) return '';
  const body = rows.map(f =>
    '<tr><td class="ro">' + (f.role ? esc(t('dc.role.' + f.role)) : '') + '</td><td class="m">' + dash(f.icao) + '</td>' +
    '<td class="nm">' + esc(f.name) + '</td><td class="m">' + rwyHtml(f.runway) + '</td><td class="m">' + freqHtml(f.frequency) + '</td></tr>').join('');
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
  const pair = v => hasText(v[1])
    ? '<div class="wp"><span class="wl">' + esc(t(v[0])) + '</span><span class="wv">' + esc(v[1]) + '</span></div>'
    : '<div class="wp wp0"></div>';
  let b = '';
  if (hasText(w.metar)) b += '<div class="dc-metar">' + esc(w.metar) + '</div>';
  if (hasV) {
    let cells = '';
    if (hasText(w.wind) || hasText(w.visibility)) cells += pair(vals[0]) + pair(vals[1]);
    if (hasText(w.qnh) || hasText(w.clouds)) cells += pair(vals[2]) + pair(vals[3]);
    b += '<div class="dc-wgrid">' + cells + '</div>';
  }
  return blockHtml('weather', t('dc.b.weather'), b);
}

function blkFuel(c) {
  const fuelRows = [['dc.joker', c.fuel.joker], ['dc.bingo', c.fuel.bingo]].filter(r => hasText(r[1]));
  const fcLoad = (c.gsId || dgFrozen(c)) && c.loadoutFc ? dgLoadCardHtml(c) : '';
  const load = fcLoad ? [''] : c.loadout.filter(hasText);
  if (!fuelRows.length && !load.length) return '';
  const mu = unitLabel(c, 'mass');
  let b = '<div class="dc-fuelwrap' + (fuelRows.length && load.length ? '' : ' dc-solo') + '">';
  if (fuelRows.length) {
    b += '<div class="dc-fuel">' + fuelRows.map(r =>
      '<div class="dc-fp"><span class="fl">' + esc(t(r[0])) + '</span><span class="fv">' + esc(r[1].trim() + ' ' + mu) + '</span></div>').join('') + '</div>';
  }
  if (load.length) {
    b += fcLoad || '<ul class="dc-load">' + load.map(l => '<li><span class="bl">▪</span><span class="lx">' + esc(l) + '</span></li>').join('') + '</ul>';
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

/* ----- Boîtes vides (lot mp-dg-cases-vides) : une boîte que le rendu ci-dessus ne montre pas (aucune donnée) garde ses titres et quelques
   lignes vides, à compléter à la main ; elle n'est jamais retirée. Une boîte qui a une donnée garde le rendu ci-dessus. ----- */
const BLANK_ROWS = { steps: 3, crew: 4, nav: 5, refs: 2, radio: 4, loadout: 2, notes: 2 };
function blankRows(n, cells) {
  let s = '';
  for (let i = 0; i < n; i++) s += '<tr class="dc-bl">' + cells.map(cl => '<td' + (cl ? ' class="' + cl + '"' : '') + '></td>').join('') + '</tr>';
  return s;
}

function blkMissionBlank(c) {
  let b = '<p class="dc-obj dc-bl"></p><ol class="dc-steps">';
  for (let i = 1; i <= BLANK_ROWS.steps; i++) b += '<li class="dc-bl"><span class="n">' + i + '.</span><span class="x"></span></li>';
  return blockHtml('mission', t('dc.b.mission'), b + '</ol>');
}

function blkTimesBlank(c) {
  const rows = c.times.filter(x => hasText(x.label));
  const b = '<div class="dc-times">' + rows.map(x =>
    '<div class="dc-trow dc-bl"><span class="dc-tl">' + esc(x.label) + '</span><span class="dc-tv"></span></div>').join('') + '</div>';
  return blockHtml('times', t('dc.b.times'), b);
}

function blkCrewBlank(c) {
  const hd = crewHead(true);
  return blockHtml('crew', t('dc.b.crew'),
    '<table class="dc-tab dc-crew"><colgroup>' + hd.cols + '</colgroup><thead><tr>' + hd.h + '</tr></thead><tbody>' +
    blankRows(BLANK_ROWS.crew, ['nm', 'm', 'm', 'm']) + '</tbody></table>', 'dc-bbt');
}

function blkNavBlank(c) {
  const mode = c.navDisplay.mode;
  const head = navHead(c, mode, t('dc.h.course'));
  const cells = mode === 'course' ? ['m ix', 'nm', 'm r', 'm r', 'm r', 'm r', 'nt'] : ['m ix', 'nm', 'm cc', 'm r', 'm r', 'nt'];
  return blockHtml('nav', t('dc.b.nav'), navTable(mode, head, blankRows(BLANK_ROWS.nav, cells)), 'dc-bbt');
}

function blkRefsBlank(c) {
  const mode = c.navDisplay.mode === 'dms' ? 'dms' : 'mgrs';
  return blockHtml('refs', t('dc.b.refs'), refsTable(mode, refsHead(c, mode), blankRows(BLANK_ROWS.refs, ['m ix', 'nm', 'm cc', 'm r', 'nt'])), 'dc-bbt');
}

function blkRadioBlank(c) {
  const ch = [];
  for (let i = 0; i < BLANK_ROWS.radio; i++) ch.push({ blank: true, channel: '', label: '', frequency: '', modulation: '' });
  return blockHtml('radio', t('dc.b.radio'), radioTable([{ name: '', ch: ch }]), 'dc-bbt');
}

function blkFieldsBlank(c) {
  const body = ['dep', 'arr', 'alt'].map(r =>
    '<tr class="dc-bl"><td class="ro">' + esc(t('dc.role.' + r)) + '</td><td class="m"></td><td class="nm"></td><td class="m"></td><td class="m"></td></tr>').join('');
  return blockHtml('fields', t('dc.b.fields'),
    '<table class="dc-tab dc-fields dc-blank"><colgroup><col style="width:56px"><col style="width:76px"><col><col style="width:54px"><col style="width:104px"></colgroup>' +
    '<thead><tr><th></th><th>' + esc(t('dc.h.icao')) + '</th><th>' + esc(t('dc.h.name')) + '</th><th>' + esc(t('dc.h.rwy')) + '</th><th>' + esc(t('dc.h.freq')) + '</th></tr></thead>' +
    '<tbody>' + body + '</tbody></table>', 'dc-bbt');
}

function blkWeatherBlank(c) {
  const b = '<div class="dc-wgrid">' + ['dc.w.wind', 'dc.w.vis', 'dc.w.qnh', 'dc.w.clouds'].map(k =>
    '<div class="wp dc-bl"><span class="wl">' + esc(t(k)) + '</span><span class="wv"></span></div>').join('') + '</div>';
  return blockHtml('weather', t('dc.b.weather'), b);
}

function blkFuelBlank(c) {
  let b = '<div class="dc-fuelwrap dc-fblank"><div class="dc-fuel">' + ['dc.joker', 'dc.bingo'].map(k =>
    '<div class="dc-fp dc-bl"><span class="fl">' + esc(t(k)) + '</span><span class="fv"></span></div>').join('') + '</div><ul class="dc-load">';
  for (let i = 0; i < BLANK_ROWS.loadout; i++) b += '<li class="dc-bl"><span class="lx"></span></li>';
  return blockHtml('fuel', t('dc.b.fuel') + ' · ' + t('dc.b.loadout'), b + '</ul></div>');
}

function blkThreatsBlank(c) {
  let b = '';
  for (let i = 0; i < BLANK_ROWS.notes; i++) b += '<div class="dc-notes dc-bl"></div>';
  return blockHtml('threats', t('dc.b.threats') + ' · ' + t('dc.b.notes'), b);
}

function rowHtml(cls, cells) {
  const live = cells.filter(Boolean);
  if (!live.length) return '';
  return '<div class="dc-row ' + cls + (live.length > 1 ? ' dc-two' : '') + '">' + live.join('') + '</div>';
}

/* Le groupe de l'en-tête : déduit des lignes, chaque type avec son nombre (« 1 × Mi-24P + 1 × Mi-8MT ») ; sinon « n × A », « A » seul, « GROUPE DE n », ou rien */
function groupText(c) {
  const d = deduceGroup(c);
  if (d) return d.types.map(x => x[1] + ' \u00d7 ' + x[0]).join(' + ');
  const a = c.flight.aircraft.trim(), n = c.flight.count;
  if (hasText(a)) return (n != null && a.indexOf('+') < 0) ? n + ' \u00d7 ' + a : a;
  return n != null ? t('dc.flightOf', { n: n }) : '';
}

function headMain(c) {
  const f = c.flight, m = c.meta;
  const sub = [
    groupText(c),
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

function headRadios(c) {
  return '<div class="dc-head dc-head2"><div class="dc-hl"><div class="dc-cs">' + esc(c.flight.callsign.trim()) + '</div></div>' +
    '<div class="dc-hr"><div class="dc-ttl">' + esc(t('dc.pageR')) + '</div></div></div>';
}

/* Une page de datacard. kind : 'main' (page 1), 'nav' (page de navigation) ou 'radios' (page Radios, la dernière) ; noRadio : la page 1 sans le bloc Radio.
   withNav : la navigation est sur cette page ; withRefs : les points de référence aussi (après la navigation). */
function pageHtml(c, mode, p, N, kind, withNav, withRefs, noRadio) {
  const cls = esc(classifLabel(c));
  const pg = p + ' / ' + N;
  const top = '<div class="dc-top"><span>' + cls + '</span><span>' + esc(c.meta.docRef.trim()) + '</span><span>' + pg + '</span></div>';
  const opm = [c.meta.operation.trim(), c.meta.mission.trim()].filter(hasText).join(' ');
  const footL = [t('dc.title'), c.flight.callsign.trim(), opm].filter(hasText).join(' · ');
  const foot = '<div class="dc-foot"><span>' + esc(footL) + '</span><span>' + cls + '</span><span>' + pg + '</span></div>';
  let head, body;
  if (kind === 'radios') {
    head = headRadios(c);
    body = rowHtml('dc-r3', [blkRadioPage(c)]);
  } else if (kind === 'nav') {
    head = headNav(c);
    body = (withNav ? rowHtml('dc-r3', [blkNav(c) || blkNavBlank(c)]) : '') + (withRefs ? rowHtml('dc-r3', [blkRefs(c) || blkRefsBlank(c)]) : '');
  } else {
    head = headMain(c);
    const fields = blkFields(c) || blkFieldsBlank(c), weather = blkWeather(c) || blkWeatherBlank(c);
    const col = '<div class="dc-col">' + fields + weather + '</div>';
    body = rowHtml('dc-r1', [blkMission(c) || blkMissionBlank(c), blkTimes(c) || blkTimesBlank(c)]) +
      rowHtml('dc-r2', [blkCrew(c) || blkCrewBlank(c)]) +
      (withNav ? rowHtml('dc-r3', [blkNav(c) || blkNavBlank(c)]) : '') +
      (withRefs ? rowHtml('dc-r3', [blkRefs(c) || blkRefsBlank(c)]) : '') +
      rowHtml('dc-r4', [noRadio ? '' : (blkRadio(c) || blkRadioBlank(c)), col]) +
      rowHtml('dc-r5', [blkFuel(c) || blkFuelBlank(c), blkThreats(c) || blkThreatsBlank(c)]);
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

/* Découpage d'une carte, toujours décidé à la mesure du rendu. plan.split : deux pages ; plan.p2 : ce que porte la page 2
   (« refs » : les seules références ; « navrefs » : la navigation puis les références, ou la navigation seule sans référence).
   nr : la page 1 sans le bloc Radio. */
function planBase(c, nr) {
  const plan = { split: false, overflow: false, overflow2: false, p2: 'navrefs' };
  /* La navigation et les points de référence sont toujours présents (vides : leurs titres et leurs lignes à remplir). Une navigation qui a une donnée
     ne part jamais en page 2 à cause de références : le cas 2 d'avant vaut même si les références sont vides. */
  const dataNav = navRows(c).length > 0;
  /* 1 · tout tient en page 1 (navigation puis références) ; 2 · (navigation avec une donnée) la page 1 avec la navigation seule tient : les références,
     vides ou non, passent seules en page 2 ; 3 · page 1 sans navigation ni références, page 2 avec la navigation puis les références */
  if (overflowsHtml(pageHtml(c, 'day', 1, 1, 'main', true, true, nr))) {
    plan.split = true;
    if (dataNav && !overflowsHtml(pageHtml(c, 'day', 1, 2, 'main', true, false, nr))) plan.p2 = 'refs';
    else {
      plan.overflow = overflowsHtml(pageHtml(c, 'day', 1, 2, 'main', false, false, nr));
      plan.overflow2 = overflowsHtml(pageHtml(c, 'day', 2, 2, 'nav', true, true));   /* page 2 : la navigation puis les références */
    }
  }
  return plan;
}

/* Tant que le bloc Radio tient en page 1, rien ne change. Sinon (la page 1 déborde même sans la navigation, et elle ne déborde plus sans le bloc Radio),
   le bloc Radio forme une page à lui, la dernière : plan.radioPage ; plan.overflowR : cette page déborde. */
/* La zone de mesure a-t-elle une taille ? Dans un cadre caché (module du shell passé au second plan) elle n'en a pas : rien n'y est mesuré, rien n'est mis en cache */
function dgMeasurable() { return document.getElementById('measure-root').getBoundingClientRect().width > 0; }
function planCard(c) {
  if (!dgMeasurable()) return { split: false, overflow: false, overflow2: false, p2: 'navrefs', radioPage: false, overflowR: false, unmeasured: true };       /* plan provisoire : ni alerte ni cache ; l'aperçu se refait quand le cadre redevient visible */
  const key = CURRENT_LANG + '|' + JSON.stringify(c);
  if (layoutCache.has(key)) return layoutCache.get(key);
  let plan = planBase(c, false);
  plan.radioPage = false; plan.overflowR = false;
  if (plan.overflow && blkRadio(c) !== '') {
    const alt = planBase(c, true);
    if (!alt.overflow) {
      plan = alt;
      plan.radioPage = true;
      plan.overflowR = overflowsHtml(pageHtml(c, 'day', plan.split ? 3 : 2, plan.split ? 3 : 2, 'radios', false, false));
    }
  }
  if (layoutCache.size > 80) layoutCache.clear();
  layoutCache.set(key, plan);
  return plan;
}

/* Les pages d'une carte, dans un mode donné */
function cardPages(c, mode) {
  const plan = planCard(c);
  const rp = plan.radioPage, nr = rp;
  const N = (plan.split ? 2 : 1) + (rp ? 1 : 0);
  const pages = plan.split
    ? (plan.p2 === 'refs'
      ? [pageHtml(c, mode, 1, N, 'main', true, false, nr), pageHtml(c, mode, 2, N, 'nav', false, true)]
      : [pageHtml(c, mode, 1, N, 'main', false, false, nr), pageHtml(c, mode, 2, N, 'nav', true, true)])
    : [pageHtml(c, mode, 1, N, 'main', true, true, nr)];
  if (rp) pages.push(pageHtml(c, mode, N, N, 'radios', false, false));
  return { plan, pages };
}

/* ============= APERÇU ============= */
function renderPreview() {
  const c = curCard();
  const res = cardPages(c, doc.mode);
  DG_UI.needLayout = !!res.plan.unmeasured;
  document.getElementById('preview').innerHTML = res.pages.map(h => '<div class="dc-sheet">' + h + '</div>').join('');
  const warn = document.getElementById('dc-warn');
  if (res.plan.overflow) { warn.textContent = t('warn.overflow'); warn.hidden = false; }
  else if (res.plan.overflow2) { warn.textContent = t('warn.overflow2'); warn.hidden = false; }
  else if (res.plan.overflowR) { warn.textContent = t('warn.overflowR'); warn.hidden = false; }
  else { warn.textContent = ''; warn.hidden = true; }
  applyPreviewScale();
}

function dgRelayout() { if (DG_UI.needLayout && dgMeasurable()) renderPreview(); }

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
  'crew': { max: LIMITS.crew, make: () => ({ callsign: '', pilot: '', type: '', board: '' }) },
  'nav': { max: LIMITS.nav, make: () => ({ name: '', course: '', distance: '', altitude: '', tos: '', note: '', coord: '' }) },
  'refs': { max: LIMITS.refs, make: () => ({ name: '', coord: '', altitude: '', note: '' }) },
  'radios': { max: LIMITS.radios, make: () => ({ name: '', channels: [] }) },
  'radios.*.channels': { max: LIMITS.channels, make: () => ({ channel: '', label: '', frequency: '', modulation: '' }) },
  'fields': { max: LIMITS.fields, make: () => ({ role: '', icao: '', name: '', runway: '', frequency: '' }) },
  'loadout': { max: LIMITS.loadout, make: () => '' },
  'threats': { max: LIMITS.threats, make: () => '' }
};
function listSpec(path) { return LIST_SPECS[path.replace(/\.\d+\./g, '.*.')]; }

/* Exemple grisé d'un champ : clé ph.<chemin> (indices de liste → *) ; jamais écrit dans l'état */
function phAttr(path) {
  const key = 'ph.' + path.replace(/\.\d+(?=\.|$)/g, '.*');
  return ' placeholder="' + esc(t(key)) + '"';
}
function fInput(labelKey, path, value, extra) {
  return '<div class="ed-field"><label>' + esc(t(labelKey)) + '</label><input type="text" data-path="' + path + '" value="' + esc(value) + '"' + phAttr(path) + (extra || '') + '></div>';
}
function fInputBare(path, value, extra) {
  return '<div class="ed-field"><input type="text" data-path="' + path + '" value="' + esc(value) + '"' + phAttr(path) + (extra || '') + '></div>';
}
function fArea(labelKey, path, value) {
  return '<div class="ed-field"><label>' + esc(t(labelKey)) + '</label><textarea data-path="' + path + '"' + phAttr(path) + '>' + esc(value) + '</textarea></div>';
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
    '<button type="button" class="ed-btn-add" data-act="add" data-list="' + path + '"' + (items.length >= spec.max ? ' disabled' : '') + '>' + esc(Array.isArray(addKey) ? t(addKey[0], addKey[1]) : t(addKey)) + '</button>';
}


/* Réglages d'affichage de la navigation (en tête de la section) et état d'une coordonnée saisie */
function navDeclMissing(c) { return c.navDisplay.ref === 'mag' && c.navDisplay.vmode === 'manual' && parseDecl(c.navDisplay.decl) == null; }

/* Les deux lignes d'aide de la déclinaison calculée : l'année (le champ Date) et le modèle de DCS */
function navVarHelp(c) {
  const nv = navVar(c) || { calc: true, y: magDecYear('1985'), dated: false };
  const y = nv.y;
  let l1 = nv.dated ? t('nav.vy.date', { a: Math.floor(y) }) : t('nav.vy.def');
  return esc(l1) + '<br>' + esc(t('nav.vy.model', { e: magModel(y) }));
}

function navSettingsHtml(c) {
  const nd = c.navDisplay, mag = nd.ref === 'mag', calc = nd.vmode === 'calc';
  return '<div class="ed-field-row three ed-navset">' +
    fSelect('f.nav.display', 'navDisplay.mode', nd.mode, [['course', t('nav.mode.course')], ['mgrs', t('nav.mode.mgrs')], ['dms', t('nav.mode.dms')]]) +
    fSelect('f.nav.ref', 'navDisplay.ref', nd.ref, [['true', t('nav.ref.true')], ['mag', t('nav.ref.mag')]]) +
    (mag ? fSelect('f.nav.vmode', 'navDisplay.vmode', nd.vmode, [['calc', t('nav.vmode.calc')], ['manual', t('nav.vmode.manual')]]) : '<div class="ed-field"></div>') + '</div>' +
    (mag && !calc ? '<div class="ed-field-row">' + fInput('f.nav.decl', 'navDisplay.decl', nd.decl, ' inputmode="decimal" autocomplete="off"') + '</div>' +
      '<div class="ed-help">' + esc(t('nav.decl.help')) + '</div>' : '') +
    (mag && calc ? '<div class="ed-help" data-nav-vhelp>' + navVarHelp(c) + '</div>' : '') +
    '<div class="ed-help">' + esc(t('f.nav.coord')) + (CURRENT_LANG === 'fr' ? ' : ' : ': ') + esc(t('nav.coord.help')) + '</div>' +
    '<div class="ed-warn" data-nav-warn' + (navDeclMissing(c) ? '' : ' hidden') + '>' + esc(t('nav.decl.warn')) + '</div>';
}

function coordState(raw, pt, g) {
  if (!pt && g && g.est && !hasText(raw)) return { cls: 'ok', text: t(g.estDir === 'next' ? 'nav.est.next' : 'nav.est.prev') + ' ' + (toMGRS(g.est.lat, g.est.lon) || '—') + ' · ' + toDMS(g.est.lat, g.est.lon) };
  if (!hasText(raw)) return { cls: '', text: '' };
  if (!pt) return { cls: 'bad', text: t('nav.coord.bad') };
  return { cls: 'ok', text: '✓ ' + (toMGRS(pt.lat, pt.lon) || '—') + ' · ' + toDMS(pt.lat, pt.lon) };
}

/* Remet à jour, sans refaire l'éditeur (le curseur reste en place) : lignes d'état, Cap et Distance calculés, avertissement */
function syncNavEditor() {
  const c = curCard();
  const legs = navLegs(c);
  const cm = c.navDisplay.mode === 'course';
  document.querySelectorAll('#editor .li[data-list="nav"]').forEach(li => {
    const i = parseInt(li.dataset.i, 10);
    const x = c.nav[i], g = legs[i];
    if (!x || !g) return;
    const st = li.querySelector('[data-coord-state]');
    if (st) { const o = coordState(x.coord, g.pt, g); st.textContent = o.text; st.className = 'ed-coord ' + o.cls; }
    const lock = cm && !!g.calc;
    [['course', lock ? g.calc.cap : x.course], ['distance', lock ? g.calc.dist : x.distance]].forEach(p => {
      const el = li.querySelector('[data-path="nav.' + i + '.' + p[0] + '"]');
      if (!el) return;
      if (el.value !== p[1]) el.value = p[1];
      el.readOnly = lock;
      if (lock) el.title = t('nav.calc.tip'); else el.removeAttribute('title');
    });
  });
  const w = document.querySelector('#editor [data-nav-warn]');
  if (w) w.hidden = !navDeclMissing(c);
  const vh = document.querySelector('#editor [data-nav-vhelp]');
  if (vh) vh.innerHTML = navVarHelp(c);
}

/* Points de référence : la ligne d'état de chaque coordonnée, sans refaire l'éditeur */
function syncRefsEditor() {
  const c = curCard();
  document.querySelectorAll('#editor .li[data-list="refs"]').forEach(li => {
    const x = c.refs[parseInt(li.dataset.i, 10)];
    const st = li.querySelector('[data-coord-state]');
    if (!x || !st) return;
    const o = coordState(x.coord, parseCoord(x.coord), null);
    st.textContent = o.text; st.className = 'ed-coord ' + o.cls;
  });
}

const SECTION_BUILDERS = {
  meta: c =>
    fSelect('f.classification', 'meta.classification', c.meta.classification, CLASSIF_KEYS.map(k => [k, t('classif.' + k)])) +
    fInput('f.docRef', 'meta.docRef', c.meta.docRef) +
    '<div class="ed-field-row">' + fInput('f.operation', 'meta.operation', c.meta.operation) + fInput('f.mission', 'meta.mission', c.meta.mission) + '</div>' +
    '<div class="ed-field-row">' + fInput('f.date', 'meta.date', c.meta.date) + fInput('f.time', 'meta.time', c.meta.time) + '</div>',

  mission: c =>
    fArea('f.objective', 'mission.objective', c.mission.objective) +
    '<div class="ed-field"><label>' + esc(t('f.steps')) + '</label></div>' +
    listHtml('mission.execution', c.mission.execution, (s, i) => fInputBare('mission.execution.' + i, s), 'add.step'),

  times: c => listHtml('times', c.times, (x, i) =>
    '<div class="li-grid g2">' + fInputBare('times.' + i + '.label', x.label) + fInputBare('times.' + i + '.value', x.value) + '</div>', 'add.time'),

  group: c => groupBoxHtml(c),

  nav: c => navSettingsHtml(c) + (() => {
    const legs = navLegs(c), cm = c.navDisplay.mode === 'course';
    return listHtml('nav', c.nav, (x, i) => {
      const g = legs[i], lock = cm && !!g.calc;
      const ro = lock ? ' readonly title="' + esc(t('nav.calc.tip')) + '"' : '';
      const st = coordState(x.coord, g.pt, g);
      return '<div class="li-grid gs">' + fInput('f.nav.name', 'nav.' + i + '.name', x.name) + '</div>' +
        '<div class="li-grid gs"><div class="ed-field"><label>' + esc(t('f.nav.coord')) + '</label>' +
        '<input type="text" data-path="nav.' + i + '.coord" value="' + esc(x.coord) + '"' + phAttr('nav.' + i + '.coord') + ' autocomplete="off" spellcheck="false">' +
        '<div class="ed-coord ' + st.cls + '" data-coord-state>' + esc(st.text) + '</div></div></div>' +
        '<div class="li-grid g3">' + fInput('f.nav.course', 'nav.' + i + '.course', lock ? g.calc.cap : x.course, ro) +
        fInput('f.nav.distance', 'nav.' + i + '.distance', lock ? g.calc.dist : x.distance, ro) +
        fInput('f.nav.altitude', 'nav.' + i + '.altitude', x.altitude) + '</div>' +
        '<div class="li-grid g2">' + fInput('f.nav.tos', 'nav.' + i + '.tos', x.tos) + fInput('f.nav.note', 'nav.' + i + '.note', x.note) + '</div>';
    }, 'add.point');
  })(),

  refs: c =>
    '<div class="ed-help">' + esc(t('f.nav.coord')) + (CURRENT_LANG === 'fr' ? ' : ' : ': ') + esc(t('nav.coord.help')) + '</div>' +
    listHtml('refs', c.refs, (x, i) => {
      const st = coordState(x.coord, parseCoord(x.coord), null);
      return '<div class="li-grid gs">' + fInput('f.nav.name', 'refs.' + i + '.name', x.name) + '</div>' +
        '<div class="li-grid gs"><div class="ed-field"><label>' + esc(t('f.nav.coord')) + '</label>' +
        '<input type="text" data-path="refs.' + i + '.coord" value="' + esc(x.coord) + '"' + phAttr('refs.' + i + '.coord') + ' autocomplete="off" spellcheck="false">' +
        '<div class="ed-coord ' + st.cls + '" data-coord-state>' + esc(st.text) + '</div></div></div>' +
        '<div class="li-grid g2">' + fInput('f.nav.altitude', 'refs.' + i + '.altitude', x.altitude) + fInput('f.nav.note', 'refs.' + i + '.note', x.note) + '</div>';
    }, 'add.ref'),

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
    '<div class="li-grid gs">' + afNameHtml(f, i) + '</div>' +
    '<div class="li-grid g2">' + afRwyHtml(f, i) + fInput('f.field.frequency', 'fields.' + i + '.frequency', f.frequency) + '</div>', 'add.field'),

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

/* Une carte liée : le groupe, l'équipage = les unités, les radios par type, l'emport du FC */
const LINKED_BUILDERS = {
  radio: radioLinkedHtml,
  fuel: c =>
    '<div class="ed-field-row">' + fInput('f.joker', 'fuel.joker', c.fuel.joker) + fInput('f.bingo', 'fuel.bingo', c.fuel.bingo) + '</div>' +
    '<label class="ed-chk"><input type="checkbox" data-lofc="1"' + (c.loadoutFc ? ' checked' : '') + '><span>' + esc(t('lo.fc')) + '</span></label>' +
    (c.loadoutFc ? dgLoadEditorHtml(c) :
      '<div class="ed-field"><label>' + esc(t('f.loadout')) + '</label></div>' + listHtml('loadout', c.loadout, (s, i) => fInputBare('loadout.' + i, s), 'add.line'))
};
/* Une carte libre née d'une carte liée montre, en lecture seule, ce que le groupe lui donnait : les canaux affichés (radios) et les tableaux d'emport (carburant et emport) */
function dgFrozenRadioHtml(c) {
  let h = '';
  dgFrozenModel(c).forEach(m => {
    const posts = m.posts.map(p => {
      const rows = p.rows.filter(r => r.freq !== '' || dgRs(c, dgRsKey(m.type, p.r, r.c)).on);
      if (!rows.length) return '';
      return '<div class="rt-post"><div class="rt-ph">' + esc(p.name) + '</div>' + rows.map(r => {
        const s = dgRs(c, dgRsKey(m.type, p.r, r.c)), extra = [s.label, s.mod].filter(hasText).join(' · ');
        return '<div class="rc-row frz' + (s.on ? ' on' : '') + '"><div class="rc-top">' + (dgPostFree(m.type, p.r) ? '' : '<span class="rc-ch">' + esc(t('rt.ch', { n: r.cock })) + '</span>') + '<span class="frz-v">' + esc(r.freq || '—') + '</span>' +
          (s.on ? '<span class="frz-on">' + esc(t('rt.on') + (extra ? ' · ' + extra : '')) + '</span>' : '') + '</div></div>';
      }).join('') + '</div>';
    }).join('');
    if (posts) h += '<section class="rt-box" data-rtype="' + esc(m.type) + '"><h4 class="rt-h"><span class="rt-t">' + esc(t('rt.title', { type: dgTypeLabel(m.type).toUpperCase() })) + '</span></h4>' + posts + '</section>';
  });
  return h ? '<div class="ed-help">' + esc(t('frz.note')) + '</div>' + h : '';
}
function dgFrozenSection(id, c) {
  if (!dgFrozen(c)) return '';
  if (id === 'radio') return dgFrozenRadioHtml(c);
  return '';
}
/* Une carte libre née d'une carte liée qui portait un emport du FC : la section Carburant et emport garde la case « Emport du Flight Configurator » : cochée, le tableau figé (la liste manuelle est masquée) ; décochée, la saisie à la main, qui s'imprime */
function dgFrozenLoad(c) { return !c.gsId && gsIsObj(c.frz) && ((Array.isArray(c.frz.loads) && c.frz.loads.length) || (Array.isArray(c.frz.raw) && c.frz.raw.length)); }
Object.keys(LINKED_BUILDERS).forEach(id => {
  const base = SECTION_BUILDERS[id];
  SECTION_BUILDERS[id] = c => c.gsId ? LINKED_BUILDERS[id](c) : (id === 'fuel' && dgFrozenLoad(c) ? LINKED_BUILDERS.fuel(c) : dgFrozenSection(id, c) + base(c));
});

/* L'éditeur suit l'ordre des blocs de l'aperçu imprimé, pour une carte liée comme pour une carte libre (SECTION_IDS) */
const openState = {};

function sectionHtml(id, idx, c) {
  const title = pad2(idx + 1) + ' ░ ' + t('sec.' + id);
  return '<details class="ed-section" data-section="' + id + '"' + (openState[id] === false ? '' : ' open') + '>' +
    '<summary>' + esc(title) + '</summary><div class="ed-content"><div class="panel-mobile-header">' + esc(title) + '</div>' +
    SECTION_BUILDERS[id](c) + '</div></details>';
}

/* Le champ en cours de saisie, retrouvé dans l'éditeur refait */
function dgFocusSel(el) {
  const d = el.dataset || {}, q = v => String(v).replace(/\\/g, '\\\\').replace(/"/g, '\\"');
  if (d.gs) return '[data-gs="' + q(d.gs) + '"]';
  if (d.rs) return '[data-rs="' + q(d.rs) + '"][data-rk="' + q(d.rk) + '"]';
  if (d.path) return '[data-path="' + q(d.path) + '"]';
  return '';
}
/* keep : le redessin vient d'un autre module ; le champ qu'on est en train de saisir est gardé tel quel (même nœud : sa valeur, son focus, son curseur et sa saisie
   non validée), le reste est refait. Le « change » que le retrait du champ peut déclencher est ignoré (DG_UI.rendering). */
function renderEditor(keep) {
  const ed = document.getElementById('editor');
  const top = ed.scrollTop;
  const c = curCard();
  const act = document.activeElement;
  const cand = keep && act && ed.contains(act) && (act.tagName === 'TEXTAREA' || (act.tagName === 'INPUT' && /^(text|search|tel|url|number)$/.test(act.type))) ? act : null;
  /* Un champ de fréquence n'est gardé que si une saisie y est en cours (non validée, ou une valeur différente de celle de l'entrée) ; sinon le champ neuf prend sa place, avec la valeur à jour, et reçoit le focus */
  const isFreq = !!(cand && cand.dataset && cand.dataset.gs && cand.dataset.gs.indexOf('f.') === 0);
  const isGs = !!(cand && cand.dataset && cand.dataset.gs);
  const pending = !isGs || !!cand._dgPend || (cand._dgBase !== undefined && !(isFreq ? dgSameFreq(cand.value, cand._dgBase) : cand.value === cand._dgBase));
  const kept = cand && pending ? cand : null;
  const refocus = cand && !pending ? cand : null;
  const sel = cand ? dgFocusSel(cand) : '';
  const caret = cand ? [cand.selectionStart, cand.selectionEnd, cand.selectionDirection] : null;
  DG_UI.rendering = true;
  try {
    document.getElementById('ed-sections').innerHTML = SECTION_IDS.map((id, i) => sectionHtml(id, i, c)).join('');
    const nw = kept && sel ? ed.querySelector(sel) : null;
    if (nw && nw !== kept && nw.tagName === kept.tagName) {
      nw.replaceWith(kept);
      kept.focus({ preventScroll: true });
      try { kept.setSelectionRange(caret[0], caret[1], caret[2] || 'none'); } catch (err) { /* un champ sans curseur */ }
    } else if (refocus && sel) {
      const fresh = ed.querySelector(sel);
      if (fresh) {
        fresh._dgBase = fresh.value;
        fresh.focus({ preventScroll: true });
        try { fresh.setSelectionRange(caret[0], caret[1], caret[2] || 'none'); } catch (err) { /* un champ sans curseur */ }
      }
    }
  } finally { DG_UI.rendering = false; }
  ed.scrollTop = top;
}

function packTitle() {
  return t('pack.list', { n: doc.cards.length });
}
function updatePackTitle() { renderPack(); }

/* La liste des cartes : les cartes liées (dans l'ordre de la fiche), puis les cartes libres */
function renderPack() {
  const c = curCard(), linked = !!c.gsId;
  const b = (act, label, extra, disabled, tip) =>
    '<button type="button" class="pack-btn' + (extra || '') + '" data-pack="' + act + '"' + (disabled ? ' disabled' : '') + (tip ? ' title="' + esc(tip) + '"' : '') + '>' + esc(label) + '</button>';
  const rows = doc.cards.map((x, i) => {
    const name = dgCardName(x, i);
    const tag = x.gsId ? ['linked', 'pack.tag.linked'] : (x.gsGone ? ['gone', 'pack.tag.gone'] : ['free', 'pack.tag.free']);
    return '<li><button type="button" class="card-row' + (x.gsId ? '' : ' free') + (i === curIdx ? ' cur' : '') + '" data-card="' + i + '"' + (i === curIdx ? ' aria-current="true"' : '') + '>' +
      '<span class="cr-name">' + esc(name) + '</span><span class="cr-tag ' + tag[0] + '">' + esc(t(tag[1])) + '</span><span class="cr-sum">' + esc(cardSummary(x)) + '</span></button></li>';
  }).join('');
  document.getElementById('pack-bar').innerHTML =
    '<div class="pack-title" id="pack-title">' + esc(packTitle()) + '</div>' +
    '<ul class="cards-list">' + rows + '</ul>' +
    '<div class="pack-btns">' +
    b('newlinked', t('pack.newlinked'), ' main') + b('newfree', t('pack.newfree')) +
    (linked ? '' : b('attach', t('pack.attach'))) + b('impgroups', t('pack.impgroups')) +
    b('dup', t('pack.dup'), '', linked, linked ? t('pack.dup.linked') : '') + b('del', t('pack.del'), ' danger') +
    '</div>';
}

function updateModeSeg() {
  document.querySelectorAll('#mode-seg .seg-btn').forEach(b => {
    const on = b.dataset.mode === doc.mode;
    b.classList.toggle('active', on);
    b.setAttribute('aria-pressed', on ? 'true' : 'false');
  });
}

function renderAll(keep) {
  renderPack();
  renderEditor(keep);
  renderPreview();
  updateModeSeg();
  DGG.shown = DGG.stable;
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

/* Les champs Appareil et Nombre du groupe suivent les lignes d'équipage, sans refaire l'éditeur (le curseur reste en place) */
function syncGroupEditor(c) {
  const lock = !!deduceGroup(c);
  [['aircraft', c.flight.aircraft], ['count', c.flight.count == null ? '' : String(c.flight.count)]].forEach(p => {
    const el = document.querySelector('#editor [data-path="flight.' + p[0] + '"]');
    if (!el) return;
    if (lock && el.value !== p[1]) el.value = p[1];
    el.readOnly = lock;
    if (lock) el.title = t('f.group.deduced'); else el.removeAttribute('title');
  });
}

function onEditorInput(e) {
  if (DG_UI.rendering) return;        /* un redessin peut faire partir un « change » sur le champ qu'il retire : il n'ouvre ni confirmation ni écriture */
  const el = e.target;
  if (el && el.dataset && el.dataset.rs) {        /* un canal affiché : la case, le nom, la modulation (propres à la carte) */
    const c = curCard(), key = el.dataset.rs, k = el.dataset.rk;
    if (k !== 'on' && e.type === 'change') return;
    if (!gsIsObj(c.radioSel)) c.radioSel = {};
    const cur = gsIsObj(c.radioSel[key]) ? c.radioSel[key] : { on: false, label: '', mod: '' };
    if (k === 'on') { cur.on = el.checked; const row = el.closest('.rc-row'); if (row) row.classList.toggle('on', el.checked); }
    else cur[k] = el.value;
    c.radioSel[key] = cur;
    touch();
    return;
  }
  if (el && el.dataset && el.dataset.afr !== undefined) { onAfRwy(el); return; }        /* la liste des sens d'une rangée de la boîte Terrains */
  if (el && el.dataset && el.dataset.af !== undefined) { onAfName(el); return; }        /* la liste des aérodromes d'une rangée de la boîte Terrains */
  if (el && el.dataset && el.dataset.lofc) { curCard().loadoutFc = el.checked; renderEditor(); touch(); return; }
  if (el && el.dataset && el.dataset.gs) { onGsField(el, e); return; }        /* champ partagé avec la fiche : écrit dans le groupe */
  const path = el && el.dataset ? el.dataset.path : '';
  if (!path) return;
  if (e.type === 'change' && el.tagName !== 'SELECT') return;
  const c = curCard();
  if (path === 'flight.count') setPath(c, path, normCount(el.value));
  else setPath(c, path, el.value);
  if (path === 'weather.metar') syncMetar(c);
  if (path === 'flight.callsign') updatePackTitle();
  if (/^crew\./.test(path) && !c.gsId) { syncGroup(c); syncGroupEditor(c); }
  if (path === 'navDisplay.ref' || path === 'navDisplay.vmode') renderEditor();        /* la troisième liste et la rangée de la saisie changent */
  else if (/^nav(Display)?\./.test(path) || path === 'meta.date') syncNavEditor();
  if (/^refs\./.test(path)) syncRefsEditor();
  touch();
}

/* La sortie d'un champ de fréquence dont la saisie n'a pas été validée par un « change » (le champ a été gardé à travers un redessin) l'écrit maintenant */
function onEditorFocusIn(e) {
  const el = e.target;
  if (DG_UI.rendering) return;       /* le focus rendu par un redessin ne change pas la référence */
  if (el && el.dataset && el.dataset.gs && (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA')) el._dgBase = el.value;       /* la valeur du champ à l'entrée : la référence de « rien n'a changé » */
}
function onEditorFocusOut(e) {
  const el = e.target;
  if (DG_UI.rendering || !el || !el._dgPend || !el.dataset || !el.dataset.gs) return;
  el._dgPend = false;
  const c = curCard();
  if (c.gsId && dgFlightOf(c) && el.dataset.gs.indexOf('f.') === 0) dgSetFreq(c, el.dataset.gs.slice(2), el);
}
function onEditorClick(e) {
  const ga = e.target.closest('[data-gs-act]');
  if (ga) {
    if (!ga.disabled) { const c = curCard(); if (ga.dataset.gsAct === 'add-unit') dgAddUnit(c); else if (ga.dataset.gsAct === 'rm-unit') dgRemoveUnit(c, parseInt(ga.dataset.i, 10)); }
    return;
  }
  const fr = e.target.closest('[data-rsfree]');
  if (fr) { DG_UI.free[fr.dataset.rsfree] = !DG_UI.free[fr.dataset.rsfree]; renderEditor(); return; }
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
  if (path === 'crew') syncGroup(c);
  renderEditor();
  touch();
  if (focusIdx >= 0) {
    const f = document.querySelector('#editor .li[data-list="' + path + '"][data-i="' + focusIdx + '"] input, #editor .li[data-list="' + path + '"][data-i="' + focusIdx + '"] textarea');
    if (f) f.focus();
  }
}

/* ----- Liste des cartes ----- */
function onPackClick(e) {
  const row = e.target.closest('[data-card]');
  if (row) { curIdx = parseInt(row.dataset.card, 10); renderAll(); return; }
  const btn = e.target.closest('[data-pack]');
  if (!btn || btn.disabled) return;
  const act = btn.dataset.pack;
  if (act === 'newlinked') { grpAskNew(); return; }
  if (act === 'attach') { grpAskAttach(); return; }
  if (act === 'impgroups') { impOpen({ opener: btn }); return; }
  if (act === 'newfree') { doc.cards.push(newCard()); curIdx = doc.cards.length - 1; }
  else if (act === 'dup') { doc.cards.splice(curIdx + 1, 0, clone(curCard())); curIdx++; }
  else if (act === 'del') {
    if (curCard().gsId) { grpAskDelete(); return; }
    if (!confirm(t('confirm.delete'))) return;
    doc.cards.splice(curIdx, 1);
    if (!doc.cards.length) doc.cards = [newCard()];
    if (curIdx >= doc.cards.length) curIdx = doc.cards.length - 1;
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
  const cur = document.querySelector('#tab-bar button.current');
  if (cur) revealInScroller(document.getElementById('tab-bar'), cur);
  const ed = document.getElementById('editor');
  if (ed) ed.scrollTop = 0;
}

/* ----- Barres défilantes (barre du haut et onglets, sous 1 100 px) ----- */
function revealInScroller(bar, el) {
  if (!bar || !el || bar.scrollWidth <= bar.clientWidth) return;
  const b = bar.getBoundingClientRect();
  const r = el.getBoundingClientRect();
  if (r.left < b.left) bar.scrollLeft += r.left - b.left - 8;
  else if (r.right > b.right) bar.scrollLeft += r.right - b.right + 8;
}

function initScrollBar(bar) {
  if (!bar) return;
  const mq = window.matchMedia('(max-width: 1100px)');
  const update = () => {
    const max = bar.scrollWidth - bar.clientWidth;
    bar.classList.toggle('fade-l', mq.matches && bar.scrollLeft > 1);
    bar.classList.toggle('fade-r', mq.matches && bar.scrollLeft < max - 1);
  };
  const child = t => { while (t && t.parentNode !== bar) t = t.parentNode; return t; };
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
  /* Le shell ajoute son bouton de retour et son tampon après le chargement */
  new MutationObserver(update).observe(bar, { childList: true, subtree: true, characterData: true });
  update();
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
  dgFillTheatre();
  dgUnitsSync();
  updateFlagButton();
  renderAll();
  if (!document.getElementById('import-modal').hidden) biRefresh(true);
  if (impIsOpen()) impRender();       /* la fenêtre d'import commune ouverte se traduit, comme au Flight Configurator et au Route Planner */
  grpRetranslate();
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
  return d.getFullYear() + pad2(d.getMonth() + 1) + pad2(d.getDate()) + '-' + pad2(d.getHours()) + pad2(d.getMinutes()) + pad2(d.getSeconds());
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
  if (toastMsg) showToast(toastMsg, { type: 'ok' });
}

/* Le nom d'un fichier choisi : sans « .json », accents ôtés, tout ce qui n'est pas lettre, chiffre, _ + - devient « _ » ; vide si rien ne reste */
function cleanFname(v) {
  return str(v).trim().replace(/\.json$/i, '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/[^A-Za-z0-9_+-]+/g, '_').replace(/_{2,}/g, '_').replace(/^_+|_+$/g, '').slice(0, 100);
}

/* Un nom par défaut : la partie variable est nettoyée et coupée à 40 caractères, puis l'horodatage s'ajoute en fin de nom (jamais coupé) */
function fnPart(v, fallback) { return cleanFname(v).slice(0, 40) || fallback; }
function fnDefault(base, stamp) {
  const b = cleanFname(base).slice(0, 84).replace(/_+$/, '');
  return (b ? b + '_' : '') + stamp;
}

/* « Enregistrer » : la fenêtre du nom du fichier, pré-remplie du nom d'avant */
const SAVEN = { name: '', opener: null, at: 0 };
function saveModalOpen() { return !document.getElementById('save-modal').hidden; }
function saveSync() { document.getElementById('save-go').disabled = cleanFname(SAVEN.name) === ''; }
function openSaveModal(opener) {
  const cs = fnPart(slug(curCard().flight.callsign), 'doc');
  SAVEN.name = fnDefault('datacard_' + cs, stamp());
  SAVEN.opener = opener || document.activeElement;
  SAVEN.at = performance.now();
  const f = document.getElementById('save-fname');
  f.value = SAVEN.name;
  saveSync();
  document.getElementById('save-modal').hidden = false;
  f.focus({ preventScroll: true });
  f.select();
}
function closeSaveModal() {
  document.getElementById('save-modal').hidden = true;
  const o = SAVEN.opener;
  SAVEN.opener = null;
  if (o && o.focus && !o.disabled) { try { o.focus({ preventScroll: true }); } catch (e) { /* ignore */ } }
}
function saveGo() {
  const name = cleanFname(SAVEN.name);
  if (name === '') return;
  closeSaveModal();
  downloadJson(name);
}

/* L'écriture de la datacard sous le nom choisi (sans extension) */
function downloadJson(name) {
  const blob = new Blob([JSON.stringify(doc, null, 2)], { type: 'application/json' });
  const fname = name + '.json';
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

/* « Ouvrir » une datacard : les cartes des groupes de la fiche sont gardées, comme à « Exemple » ; une carte du fichier qui porte un groupe de la fiche (son gsId) remplace la carte de ce
   groupe (ses champs propres viennent du fichier, ses champs de groupe de la fiche) ; les autres cartes du fichier (libres, ou liées à un groupe que la fiche n'a pas) entrent comme cartes libres,
   et remplacent les cartes libres d'avant. Le mode est celui du fichier. */
function openDatacards(next) {
  const u0 = next.cards.length ? next.cards[0].units : null;       /* les unités de la première carte du fichier */
  const g = gsRead(), ids = new Set(g ? g.flights.map(f => f.fcId) : []);
  const mine = new Map(next.cards.filter(c => c.gsId && ids.has(c.gsId)).map(c => [c.gsId, c]));
  const kept = doc.cards.filter(x => x.gsId).map(x => mine.get(x.gsId) || x);
  mine.forEach((c, id) => { if (!doc.cards.some(x => x.gsId === id)) kept.push(c); });       /* un groupe qui n'avait pas de carte reçoit celle du fichier */
  const fresh = next.cards.filter(c => !(c.gsId && ids.has(c.gsId))).map(c => {
    if (c.gsId) { delete c.gsId; delete c.gsSide; }
    return c;
  });
  next.cards = kept.concat(fresh);
  if (!next.cards.length) next.cards = [newCard()];
  if (u0) dgUnitsAdopt(u0);
  setDoc(next);
  curIdx = Math.min(kept.length, next.cards.length - 1);
  renderAll();
}

/* ============= IMPORT JSON ============= */
/* « Ouvrir » : une datacard remplace le document (avec confirmation s'il n'est pas vide) ; un briefing, une route ou un jeu de routes ouvrent la fenêtre d'import
   (briefing ou route) sur la bonne source ; un paquet de vol ouvre la fenêtre d'import commune (import_block.py), qui écrit dans la fiche des groupes ;
   le reste est refusé avec sa raison, sans rien ouvrir. */
function loadJsonFile(file) {
  readImportFile(file, r => {
    if (r.reject) { rejectMsg(r.reject); return; }
    const k = biRecognise(r.parsed, file.name, true, r.zip);
    if (!k) return;
    if (k.kind === 'datacard') {
      const hasGroups = doc.cards.some(x => x.gsId);
      if (!isBlankDoc(doc) && !confirm(t(hasGroups ? 'confirm.json.groups' : 'confirm.json'))) return;
      openDatacards(normalizeDoc(r.parsed));
      showToast(t('toast.jsonLoaded'), { type: 'ok' });
      return;
    }
    if (k.kind === 'pkg') { impOpen({ opener: document.getElementById('btn-json-import'), parsed: r.parsed, name: file.name }); return; }
    openImportModal(null);
    biUseFile(k, file.name);
  });
}

/* ============= IMPORT DEPUIS UN BRIEFING OU UNE ROUTE ============= */
/* Les groupes (mission d'HQ, briefing, paquet de vol) passent par la fenêtre d'import commune (import_block.py) : ils s'écrivent dans la fiche et chaque groupe a sa carte.
   Cette fenêtre-ci ne garde que ce qui n'est pas un groupe : le briefing (mission, temps, terrains, météo) et la route (navigation), dans des cartes libres ou la carte affichée. */
const bi = { src: 'current', fileBriefing: null, fileRoute: null, fileSet: [], fileName: '', current: null, currentRoute: null, routeSet: [] };

function biBriefing() {
  if (bi.src === 'file') return bi.fileBriefing;
  return bi.src === 'current' ? bi.current : null;
}
function biRoute() {
  if (bi.src === 'file') return bi.fileRoute;
  return bi.src === 'route' ? bi.currentRoute : null;
}
/* Les routes que « Toutes les routes » importerait : celles du Route Planner (« Route en cours ») ou celles du jeu de routes d'un fichier */
function biSetList() {
  return bi.src === 'route' ? bi.routeSet : (bi.src === 'file' ? bi.fileSet : []);
}

/* ----- Route du Route Planner ----- */
function isRouteObject(o) {
  return !!(o && typeof o === 'object' && !Array.isArray(o) && o.format === ROUTE_FORMAT && Array.isArray(o.points));
}

/* Route lue : { name, theatre, units, navDisplay { ref, decl, mode, year, force }, points, refs } (points valides, 30 au plus ; références valides, 12 au plus),
   ou null si ce n'est pas une route */
function routeFromObject(o) {
  if (!isRouteObject(o)) return null;
  const un = (o.units && typeof o.units === 'object') ? o.units : {};
  const nd = (o.navDisplay && typeof o.navDisplay === 'object') ? o.navDisplay : {};
  const readPts = list => {
    const out = [];
    list.forEach(p => {
      if (!p || typeof p !== 'object') return;
      if (typeof p.lat !== 'number' || typeof p.lon !== 'number' || !isFinite(p.lat) || !isFinite(p.lon)) return;
      if (Math.abs(p.lat) > 90 || Math.abs(p.lon) > 180) return;
      out.push({
        name: str(p.name), lat: p.lat, lon: p.lon,
        alt: (typeof p.alt === 'number' && isFinite(p.alt)) ? p.alt : 0,
        altRef: p.altRef === 'MSL' ? 'MSL' : 'AGL'
      });
    });
    return out;
  };
  const points = readPts(o.points);
  const refs = Array.isArray(o.refs) ? readPts(o.refs) : [];
  return {
    name: str(o.name),
    units: { distance: un.distance === 'nm' ? 'nm' : 'km', altitude: un.altitude === 'ft' ? 'ft' : 'm' },
    theatre: str(o.theatre),
    navDisplay: {
      ref: nd.ref === 'mag' ? 'mag' : 'true', decl: str(nd.decl), mode: readVMode(nd.mode, str(nd.decl)),
      year: (typeof nd.year === 'string' && /^\d{1,4}$/.test(nd.year)) ? nd.year : '', force: nd.force === true
    },
    points: points.slice(0, LIMITS.nav),
    refs: refs.slice(0, LIMITS.refs)
  };
}

/* La route enregistrée par le Route Planner, en lecture seule ; null s'il n'y a aucun point. */
function dgCommonTheatre() { return dgReadTheatreKey() || dgTheatre(); }       /* le théâtre commun C : mp_theatre_v1 s'il est valide, sinon celui du document */
/* Le théâtre de référence des routes d'avant le lot : celui de route_state_v1 s'il est valide, sinon mp_theatre_v1, sinon Caucasus (la même règle que le Route Planner et le Flight Configurator) */
function dgStateTheatre(st) { return isPlainObject(st) && dgTheatreOk(st.theatre) ? st.theatre : (dgReadTheatreKey() || DG_THEATRE_DEFAULT); }
/* La route en cours : route_state_v1 s'il est de C (un theatre absent ou invalide vaut dgStateTheatre) ; sinon la première route de C de route_set_v1 ; sinon aucune. Les réglages de la route viennent de route_state_v1 seulement s'il est de C ; sinon de la clé partagée et des défauts. */
function readCurrentRoute() {
  const o = readJsonKey(KEY_ROUTE), C = dgCommonTheatre();
  if (isPlainObject(o) && dgStateTheatre(o) === C) {
    const r = routeFromObject(Object.assign({}, o, { theatre: C }));
    if (r && r.points.length) return r;
  }
  const l = biReadRouteSet();
  return l.length ? l[0].route : null;
}

/* Altitude d'un point (mètres) → chaîne entière dans l'unité de la route */
function routeAltStr(m, unit) {
  return String(Math.round(unit === 'ft' ? m / FT_M : m));
}

/* Remplace la navigation et les points de référence d'une datacard par ceux de la route ; unités et cap de la route ;
   le mode d'affichage ne change pas. Une route sans référence vide les références de la carte. */
function applyRouteToCard(c, r) {
  c.nav = r.points.slice(0, LIMITS.nav).map(p => ({
    name: p.name, course: '', distance: '', altitude: routeAltStr(p.alt, r.units.altitude), tos: '',
    note: p.altRef === 'AGL' ? 'AGL' : '', coord: toMGRS(p.lat, p.lon)
  }));
  c.refs = r.refs.slice(0, LIMITS.refs).map(p => ({
    name: p.name, coord: toMGRS(p.lat, p.lon), altitude: routeAltStr(p.alt, r.units.altitude), note: p.altRef === 'AGL' ? 'AGL' : ''
  }));
  c.units.distance = r.units.distance;
  c.units.altitude = r.units.altitude;
  c.navDisplay.ref = r.navDisplay.ref;
  c.navDisplay.decl = r.navDisplay.decl;
  c.navDisplay.vmode = r.navDisplay.mode;
  /* Route en cap magnétique calculé et champ Date vide : il prend l'année de la route (la mission, la saisie ou l'année forcée) ;
     un champ Date déjà rempli ne change jamais */
  if (r.navDisplay.ref === 'mag' && r.navDisplay.mode === 'calc' && !hasText(c.meta.date)) {
    const ys = magYearSource(r.theatre, r.navDisplay.year, r.navDisplay.force);
    if (ys.src === 'mission') c.meta.date = ys.date;
    else if (ys.src === 'forced' || ys.src === 'typed') c.meta.date = ys.year;
  }
}

const KEY_ROUTESET = 'route_set_v1';                  /* écrit par le Route Planner ; ici en lecture seule */
const SET_FORMAT = 'dcs-route-set-v1';
const PACKAGE_FORMATS = ['dcs-flight-package-v1', 'dcs-flight-package-v2'];     /* la suite écrit la v2 ; la v1 ne reste qu'en lecture : un paquet passe à la fenêtre commune */

function isPlainObject(o) { return !!o && typeof o === 'object' && !Array.isArray(o); }

/* Les refus d'un fichier, communs à la suite (mêmes textes au Route Planner, au Datacard Generator, à HQ et au Briefing Generator) :
   la valeur de « format » du fichier (« inconnu » sans format), puis la liste de ce que l'entrée lit */
function rejectFormat(parsed, kinds) {
  const f = isPlainObject(parsed) ? parsed.format : undefined;
  const x = ((typeof f === 'string' && f !== '') || typeof f === 'number') ? String(f) : t('rej.unknown');
  showToast(t('rej.format', { x: x, list: kinds.map(k => t('fmt.' + k)).join(', ') }), { type: 'err' });
}
function rejectMsg(key) { showToast(t(key), { type: 'err' }); }
/* un format reconnu dont le contenu est inutilisable : une route sans liste de points, un jeu sans liste de routes ou sans aucune route à points */
function rejectIncomplete(fmt) { showToast(t('rej.incomplete', { x: fmt }), { type: 'err' }); }

/* Un fichier d'import lu : { parsed, zip } (le JSON d'un .json, ou le package.json à la racine d'un .zip, « PK » en tête ; zip dit d'où il vient) ou { reject } (la clé du message).
   Le texte se décode comme readAsText : une marque UTF-16 (LE ou BE) en tête, UTF-16 ; sinon UTF-8 (la marque UTF-8 est ôtée). */
function readImportFile(file, done) {
  const reader = new FileReader();
  reader.onload = () => {
    const bytes = new Uint8Array(reader.result);
    const parse = (text, zip) => {
      if (text.charCodeAt(0) === 0xFEFF) text = text.slice(1);
      let parsed;
      try { parsed = JSON.parse(text); } catch (e) { console.warn('[DG] import : JSON illisible', e); done({ reject: 'rej.json' }); return; }
      done({ parsed: parsed, zip: zip });
    };
    if (!(bytes.length >= 2 && bytes[0] === 0x50 && bytes[1] === 0x4B)) {
      const enc = (bytes[0] === 0xFF && bytes[1] === 0xFE) ? 'utf-16le' : ((bytes[0] === 0xFE && bytes[1] === 0xFF) ? 'utf-16be' : 'utf-8');
      parse(new TextDecoder(enc).decode(bytes), false);
      return;
    }
    if (typeof JSZip === 'undefined') { done({ reject: 'rej.zip' }); return; }
    JSZip.loadAsync(bytes).then(z => { const e = z.file('package.json'); return e ? e.async('string') : null; })
      .then(txt => { if (txt === null) done({ reject: 'rej.zip' }); else parse(txt, true); }, () => done({ reject: 'rej.zip' }));
  };
  reader.onerror = () => done({ reject: 'rej.json' });
  reader.readAsArrayBuffer(file);
}

/* Un jeu de routes (dcs-route-set-v1) lu d'un fichier → { routes, route } : routes, celles qui portent au moins un point, dans l'ordre, chacune lue comme « Route en cours »
   avec les réglages que porte le fichier ; route, la route active (à défaut la première qui a des points) ; null s'il n'y a pas de liste de routes */
function biSetFromFile(o) {
  if (!Array.isArray(o.routes)) return null;
  const list = o.routes.filter(r => isPlainObject(r) && Array.isArray(r.points));
  if (!list.length) return null;
  /* seulement les routes de C, chacune classée par son theatre, sinon par le theatre de tête du fichier, sinon par la règle H2 (comme le stockage et l'ouverture au Route Planner) */
  const C = dgCommonTheatre(), ref = dgTheatreOk(o.theatre) ? o.theatre : dgStateTheatre(readJsonKey(KEY_ROUTE));
  const active = (Number.isInteger(o.active) && o.active >= 0 && o.active < o.routes.length) ? o.routes[o.active] : null;
  const shared = Object.assign({}, o, { format: ROUTE_FORMAT, theatre: C });
  const all = list.filter(r => routeTheatre(r, ref) === C).map(r => {
    const f = r.flight;
    return { src: r, route: routeFromObject(Object.assign({}, shared, { name: r.name, points: r.points })),
      flight: (isPlainObject(f) && typeof f.groupName === 'string') ? f : null };
  });
  const routes = all.filter(e => e.route && e.route.points.length);
  if (!routes.length) return null;      /* aucune route à points sur C */
  const chosen = routes.filter(e => e.src === active)[0] || routes[0];
  return { routes: routes.map(e => ({ route: e.route, flight: e.flight })), route: chosen.route };
}

/* Un fichier lu → ce qu'il est : { kind: 'datacard' | 'briefing' | 'route' | 'set' | 'pkg', … } ; null après avoir dit pourquoi il est refusé.
   withDatacard : l'entrée lit aussi la datacard (« Ouvrir » de la barre) ; la fenêtre d'import renvoie vers la barre. Un paquet de vol (« pkg ») n'est pas lu ici : il va à la fenêtre commune. */
function biRecognise(parsed, fname, withDatacard, fromZip) {
  const fmt = isPlainObject(parsed) ? parsed.format : undefined;
  if (fromZip && PACKAGE_FORMATS.indexOf(fmt) < 0) { rejectFormat(parsed, ['pkg']); return null; }      /* un .zip ne porte qu'un paquet de vol */
  if (fmt === FORMAT_ID) {
    if (!withDatacard) { rejectMsg('rej.isDatacard'); return null; }
    return { kind: 'datacard' };
  }
  if (isBriefingObject(parsed)) return { kind: 'briefing', briefing: parsed };
  if (fmt === ROUTE_FORMAT) {
    if (!isRouteObject(parsed)) { rejectIncomplete(ROUTE_FORMAT); return null; }
    return { kind: 'route', route: routeFromObject(parsed) };
  }
  if (fmt === SET_FORMAT) {
    const set = biSetFromFile(parsed);
    if (!set) { rejectIncomplete(SET_FORMAT); return null; }
    return { kind: 'set', routes: set.routes, route: set.route };
  }
  if (PACKAGE_FORMATS.indexOf(fmt) >= 0) return { kind: 'pkg' };
  rejectFormat(parsed, ['briefing', 'route', 'set', 'pkg'].concat(withDatacard ? ['datacard'] : []));
  return null;
}

/* Un fichier reconnu, mis dans la fenêtre d'import ouverte */
function biUseFile(k, fname) {
  bi.fileBriefing = null; bi.fileRoute = null; bi.fileSet = []; bi.fileName = '';
  if (k.kind === 'briefing') bi.fileBriefing = k.briefing;
  else { bi.fileRoute = k.route; if (k.kind === 'set') bi.fileSet = k.routes; }
  bi.fileName = fname; bi.src = 'file';
  biRefresh();
}

/* Les cartes neuves s'ajoutent à la suite (ou prennent la place d'un document vide) et la première est affichée */
function biAddCards(cards) {
  if (isBlankDoc(doc)) { doc.cards = cards; curIdx = 0; }
  else { const first = doc.cards.length; doc.cards = doc.cards.concat(cards); curIdx = first; }
}

/* Les routes du Route Planner qui portent au moins un point : [{ route (lue comme « Route en cours », avec les réglages partagés), flight }],
   dans l'ordre des routes ; la route active est celle de route_state_v1 (qui fait foi pour elle, comme au Route Planner) */
function biReadRouteSet() {
  const st = readJsonKey(KEY_ROUTE), set = readJsonKey(KEY_ROUTESET), C = dgCommonTheatre();
  if (!isPlainObject(set) || set.format !== SET_FORMAT || !Array.isArray(set.routes)) return [];
  const stOk = isPlainObject(st) && dgStateTheatre(st) === C;       /* route_state_v1 d'un autre théâtre que C : ignoré (ni la route active, ni ses réglages) */
  const ref = dgStateTheatre(st);       /* le théâtre des routes d'avant le lot (H2) */
  const base = stOk ? Object.assign({}, st, { theatre: C }) : { format: ROUTE_FORMAT, theatre: C };
  const out = [];
  set.routes.forEach((r, i) => {
    if (!isPlainObject(r) || !Array.isArray(r.points) || routeTheatre(r, ref) !== C) return;       /* seulement les routes de C (bloc partagé : une route sans theatre est lue comme le Route Planner l'écrira) */
    const o = (stOk && i === set.active) ? { name: st.name, points: st.points } : { name: r.name, points: r.points };
    const route = routeFromObject(Object.assign({}, base, o));
    if (!route || !route.points.length) return;
    const f = r.flight;
    out.push({ route: route, flight: (isPlainObject(f) && typeof f.groupName === 'string') ? f : null });
  });
  return out;
}

function runAllRoutesImport() {
  const list = biSetList();
  if (list.length < 2) return;
  const cards = list.map(e => {
    const c = newCard();
    applyRouteToCard(c, e.route);
    c.flight.callsign = e.flight ? e.flight.groupName : e.route.name;
    c.flight.aircraft = (e.flight && typeof e.flight.aircraftType === 'string') ? e.flight.aircraftType : '';      /* un lien sans type laisse l'appareil vide ; un lien ancien garde le sien */
    return c;
  });
  biAddCards(cards);
  dgUnitsAdopt(cards[0].units);       /* la première carte donne ses unités à la clé, toutes les cartes les prennent */
  persistState();
  renderAll();
  closeImportModal();
  showToast(t('toast.imported', { n: cards.length }), { type: 'ok' });
}


/* lang : la liste se refait pour un changement de langue : les choix de l'utilisateur sont relevés avant et remis ; à toute autre appel (ouverture, source, fichier) elle repart de la présélection */
function biRefresh(lang) {
  const curRow = document.getElementById('bi-src-current-row');
  const curRadio = document.getElementById('bi-src-current');
  const note = document.getElementById('bi-current-note');
  const off = !bi.current;
  curRow.classList.toggle('off', off);
  curRadio.disabled = off;
  note.hidden = !off;
  note.textContent = off ? t('imp.src.currentOff') : '';
  const rtRow = document.getElementById('bi-src-route-row');
  const rtRadio = document.getElementById('bi-src-route');
  const rtNote = document.getElementById('bi-route-note');
  const rtOff = !bi.currentRoute;
  rtRow.classList.toggle('off', rtOff);
  rtRadio.disabled = rtOff;
  rtNote.hidden = !rtOff;
  rtNote.textContent = rtOff ? t('imp.src.routeOff', { th: t('th.' + dgCommonTheatre()) }) : '';
  document.getElementById('bi-src-current').checked = bi.src === 'current';
  document.getElementById('bi-src-route').checked = bi.src === 'route';
  document.getElementById('bi-src-file').checked = bi.src === 'file';
  document.getElementById('bi-file-zone').hidden = bi.src !== 'file';
  document.getElementById('bi-file-name').textContent = bi.fileName;
  const r = biRoute();
  document.getElementById('bi-flights-block').hidden = !!r;
  document.getElementById('bi-route-block').hidden = !r;
  if (r) {
    const nm = hasText(r.name) ? r.name.trim() : t('imp.route.noname');
    document.getElementById('bi-route-line').textContent = t('imp.route.line', { name: nm, n: r.points.length }) +
      (r.refs.length ? t('imp.route.refs', { k: r.refs.length }) : '');
    /* « Toutes les routes » : sur la route en cours quand le Route Planner en garde au moins deux, ou sur un jeu de routes d'un fichier qui en porte au moins deux */
    const nAll = biSetList().length;
    const allRow = document.getElementById('bi-route-all-row');
    allRow.hidden = nAll < 2;
    document.getElementById('bi-route-all-lbl').textContent = t('imp.route.all', { n: nAll });
    if (nAll < 2 && document.getElementById('bi-route-all').checked) document.getElementById('bi-route-fill').checked = true;
  }
  const b = biBriefing();
  const list = document.getElementById('bi-list');
  const phases = b ? b.phases.filter(p => p && typeof p === 'object') : [];
  if (!b) {
    list.innerHTML = '';
  } else {
    /* Après les vols, toujours la ligne des données générales : cochée d'office quand le briefing n'a aucun vol. */
    const cur = curCard(), one = !!(cur.gsId && dgFlightOf(cur));
    if (one) {
      /* Une carte liée est affichée : un seul choix (une phase, ou les données générales) ; la phase dont l'indicatif est le nom du groupe est présélectionnée, sinon aucune */
      const gn = dgStr(dgFlightOf(cur).name).trim().toLowerCase();
      /* La phase déjà choisie (la fenêtre est ouverte, la langue change) est relevée avant de refaire la liste ; la présélection ne joue que s'il n'y en avait pas */
      const picked = lang ? list.querySelector('input[name="bi-pick"]:checked') : null, pv = picked ? picked.dataset.i : '';
      const keepIdx = pv === 'general' ? -2 : (pv !== '' && phases[parseInt(pv, 10)] ? parseInt(pv, 10) : -1);
      const pre0 = gn === '' ? -1 : phases.findIndex(ph => phaseIdentity(ph).callsign.trim().toLowerCase() === gn);
      const pre = keepIdx === -1 ? pre0 : keepIdx;
      list.innerHTML = phases.map((ph, i) =>
        '<label class="export-png-page-row"><input type="radio" name="bi-pick" class="export-png-page-cb bi-cb" data-i="' + i + '"' + (i === pre ? ' checked' : '') + '>' +
        '<span class="export-png-page-num">' + pad2(i + 1) + '</span><span>' + esc(phaseLabel(ph) || '—') + '</span></label>').join('') +
        '<label class="export-png-page-row"><input type="radio" name="bi-pick" class="export-png-page-cb bi-cb" data-i="general"' + (pre === -2 ? ' checked' : '') + '>' +
        '<span class="export-png-page-num"></span><span>' + esc(t('imp.general')) + '</span></label>';
    } else {
      /* changement de langue : les phases cochées et décochées restent comme l'utilisateur les a laissées */
      const old = lang ? Array.prototype.slice.call(list.querySelectorAll('input[type="checkbox"].bi-cb')) : [];
      const was = old.length ? new Set(old.filter(x => x.checked).map(x => x.dataset.i)) : null;
      const on = k => was ? was.has(String(k)) : (k === 'general' ? !phases.length : true);
      list.innerHTML = phases.map((ph, i) =>
      '<label class="export-png-page-row"><input type="checkbox" class="export-png-page-cb bi-cb" data-i="' + i + '"' + (on(i) ? ' checked' : '') + '>' +
      '<span class="export-png-page-num">' + pad2(i + 1) + '</span><span>' + esc(phaseLabel(ph) || '—') + '</span></label>').join('') +
      '<label class="export-png-page-row"><input type="checkbox" class="export-png-page-cb bi-cb" data-i="general"' + (on('general') ? ' checked' : '') + '>' +
      '<span class="export-png-page-num"></span><span>' + esc(t('imp.general')) + '</span></label>';
    }
  }
  biUpdateGo();
}

function biUpdateGo() {
  const r = biRoute(), go = document.getElementById('bi-go');
  go.textContent = t('imp.go');
  go.disabled = r ? !r.points.length : !document.querySelector('#bi-list .bi-cb:checked');
}

/* fileBriefing / fileRoute : un fichier déjà lu ; forceSrc 'route' : ouvrir sur « Route en cours » (passage depuis le Route Planner) */
function openImportModal(fileBriefing, fileName, fileRoute, forceSrc) {
  bi.current = readCurrentBriefing();
  bi.currentRoute = readCurrentRoute();
  bi.routeSet = biReadRouteSet();
  bi.fileBriefing = null; bi.fileRoute = null; bi.fileSet = []; bi.fileName = '';      /* rouvrir la fenêtre oublie le fichier */
  if (fileBriefing) { bi.fileBriefing = fileBriefing; bi.fileName = fileName || ''; bi.src = 'file'; }
  else if (fileRoute) { bi.fileRoute = fileRoute; bi.fileName = fileName || ''; bi.src = 'file'; }
  else if (forceSrc === 'route' && bi.currentRoute) { bi.src = 'route'; }
  else bi.src = bi.current ? 'current' : (bi.currentRoute ? 'route' : 'file');
  document.getElementById('bi-route-fill').checked = true;
  biRefresh();
  document.getElementById('import-modal').hidden = false;
}
/* Le théâtre commun ou les routes du Route Planner ont changé (autre onglet) pendant que la fenêtre d'import est ouverte : les routes proposées se relisent, sans recharger */
function dgRoutesRefresh() {
  const m = document.getElementById('import-modal');
  if (!m || m.hidden) return;
  bi.currentRoute = readCurrentRoute();
  bi.routeSet = biReadRouteSet();
  if (bi.src === 'route' && !bi.currentRoute) bi.src = bi.current ? 'current' : 'file';
  biRefresh();
}
function closeImportModal() {
  if (TBM.cur) tbmClose(false);      /* la liste ouverte se ferme avec la fenêtre */
  document.getElementById('import-modal').hidden = true;
}

/* Passage depuis le Route Planner : la clé est lue puis supprimée, la fenêtre s'ouvre sur « Route en cours ». */
function checkRouteHandoff() {
  let v = null;
  try { v = localStorage.getItem(KEY_HANDOFF); } catch (e) { return; }
  if (v === null) return;
  try { localStorage.removeItem(KEY_HANDOFF); } catch (e) { /* ignore */ }
  openImportModal(null, '', null, 'route');
}

function runRouteImport() {
  const r = biRoute();
  if (!r || !r.points.length) return;
  if (biSetList().length >= 2 && document.getElementById('bi-route-all').checked) { runAllRoutesImport(); return; }
  if (document.getElementById('bi-route-new').checked) {
    const c = newCard();
    applyRouteToCard(c, r);
    if (isBlankDoc(doc)) { doc.cards = [c]; curIdx = 0; }
    else { doc.cards.push(c); curIdx = doc.cards.length - 1; }
  } else {
    applyRouteToCard(curCard(), r);
  }
  dgUnitsAdopt(curCard().units);       /* la route lue donne ses unités à la clé */
  persistState();
  renderAll();
  closeImportModal();
  showToast(t('toast.routeImported', { n: r.points.length }), { type: 'ok' });
}

function runImport() {
  if (biRoute()) { runRouteImport(); return; }
  const b = biBriefing();
  if (!b) return;
  const phases = b.phases.filter(p => p && typeof p === 'object');
  const boxes = Array.from(document.querySelectorAll('#bi-list .bi-cb:checked'));
  const cur = curCard();
  if (cur.gsId && boxes.length) {
    /* Une carte liée est affichée : le briefing la remplit pour ce qui n'est pas un groupe (mission, date et heure, terrains, météo), jamais l'indicatif, l'équipage ni les radios */
    const cb = boxes[0], src = cb.dataset.i === 'general' ? cardFromGeneral(b) : (phases[parseInt(cb.dataset.i, 10)] ? cardFromPhase(b, phases[parseInt(cb.dataset.i, 10)]) : null);
    if (!src) return;
    ['classification', 'docRef', 'operation', 'mission', 'date', 'time'].forEach(k => { cur.meta[k] = src.meta[k]; });
    cur.mission = clone(src.mission);
    cur.fields = clone(src.fields);
    cur.weather = clone(src.weather);       /* avant les rangées : le sens proposé suit le vent du briefing */
    afFillRows(cur);
    persistState();
    renderAll();
    closeImportModal();
    showToast(t('toast.briefFilled', { n: dgCardName(cur, curIdx) }), { type: 'ok' });
    return;
  }
  const cards = [];
  boxes.forEach(cb => {
    if (cb.dataset.i === 'general') return;
    const ph = phases[parseInt(cb.dataset.i, 10)];
    if (ph) cards.push(cardFromPhase(b, ph));
  });
  if (boxes.some(cb => cb.dataset.i === 'general')) cards.push(cardFromGeneral(b));
  if (!cards.length) return;
  cards.forEach(afFillRows);
  biAddCards(cards);
  persistState();
  renderAll();
  closeImportModal();
  showToast(t('toast.imported', { n: cards.length }), { type: 'ok' });
}

/* « Choisir un fichier… » de la source « Fichier JSON » : un briefing, une route ou un jeu de routes ; un paquet de vol passe à la fenêtre d'import commune ; une datacard renvoie vers « Ouvrir » */
function loadBriefingFile(file) {
  readImportFile(file, r => {
    if (r.reject) { rejectMsg(r.reject); return; }
    const k = biRecognise(r.parsed, file.name, false, r.zip);
    if (!k) return;
    if (k.kind === 'pkg') { closeImportModal(); impOpen({ opener: document.getElementById('btn-briefing'), parsed: r.parsed, name: file.name }); return; }
    biUseFile(k, file.name);
  });
}

/* La fenêtre d'import commune (import_block.py) écrit dans la fiche des groupes ; la liste des cartes la suit : chaque groupe importé a sa carte, la première est affichée */
function dgImported(res) {
  gsApplyAll();
  const k = doc.cards.findIndex(x => x.gsId && res.fcIds.indexOf(x.gsId) >= 0);
  if (k >= 0) curIdx = k;
  persistState();
  renderAll();
  showToast(res.failed ? '⚠ ' + res.text + ' · ' + t('toast.gsFull').replace(/^⚠\s*/, '') : res.text, { type: res.failed ? 'err' : 'ok', ms: res.failed ? 6000 : res.ms });
}

/* ============= EXPORT : fenêtre ============= */
function allExportPages() {
  /* Toutes les pages de toutes les cartes, dans le mode affiché. Rien ne part d'un plan non mesuré : cadre caché, aucune page. */
  const out = [];
  if (!dgMeasurable()) return out;
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

/* Le nom du PNG (une page) ou du zip (plusieurs) : il suit les pages cochées tant qu'on ne l'a pas changé */
const PNGN = { name: '', edited: false, stamp: '' };
function pngDefaultName(idx) {
  if (idx.length === 1) {
    const p = allExportPages()[idx[0]];
    return fnDefault('dc_' + fnPart(p.cs, 'carte') + '_p' + p.page, PNGN.stamp);
  }
  return 'datacards_' + PNGN.stamp;
}
function updatePngCount() {
  const idx = Array.from(document.querySelectorAll('.export-png-page-cb.exp-cb:checked')).map(cb => parseInt(cb.dataset.idx, 10));
  const n = idx.length;
  const span = document.getElementById('export-png-count');
  if (!span) return;      /* pendant le rendu, le bouton porte « Génération i/n » : le compteur n'existe pas */
  span.textContent = '(' + n + ')';
  document.getElementById('export-png-ext').textContent = n > 1 ? '.zip' : '.png';
  const fld = document.getElementById('export-png-fname');
  if (!PNGN.edited && n) { PNGN.name = cleanFname(pngDefaultName(idx)); fld.value = PNGN.name; }
  document.getElementById('export-png-go').disabled = n === 0 || cleanFname(PNGN.name) === '';
}

function showPngConfig() {
  PNGN.edited = false;
  PNGN.stamp = stamp();
  const pages = allExportPages();
  document.getElementById('export-png-list').innerHTML = pages.map((p, i) =>
    '<label class="export-png-page-row"><input type="checkbox" class="export-png-page-cb exp-cb" data-idx="' + i + '" checked>' +
    '<span class="export-png-page-num">' + pad2(i + 1) + '</span><span>' + esc((p.cs.toUpperCase()) + ' — ' + t('ex.page') + ' ' + p.page + '/' + p.pages) + '</span></label>').join('');
  document.querySelector('#export-modal .export-modal-choices').hidden = true;
  document.getElementById('export-png-config').hidden = false;
  updatePngCount();
}

/* ============= EXPORT PNG : 2 000 × 2 828 px (×2) ============= */
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
      scale: 2,   // échelle fixe (ignore devicePixelRatio) → 2 000 × 2 828 px
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
  if (!dgMeasurable()) { showToast(t('toast.noMeasure'), { type: 'err' }); return; }       /* jamais d'image d'un plan non mesuré */
  const all = allExportPages();
  const idx = Array.from(document.querySelectorAll('.export-png-page-cb.exp-cb:checked')).map(cb => parseInt(cb.dataset.idx, 10));
  const sel = idx.map(i => all[i]).filter(Boolean);
  if (!sel.length) return;
  const fileName = cleanFname(PNGN.name);
  if (fileName === '') return;
  const goBtn = document.getElementById('export-png-go');
  const original = goBtn.innerHTML;
  goBtn.disabled = true;
  goBtn.setAttribute('aria-busy', 'true');
  /* Deux cartes de même indicatif ne doivent pas écraser leurs noms de fichier (les pages d'un zip) */
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
      fallbackDownload(blob, fileName + '.png', t('toast.pngOne'));
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
      fallbackDownload(zipBlob, fileName + '.zip', t('toast.pngMany', { n: sel.length }));
    }
  } catch (err) {
    console.error('[Export PNG]', err);
    showToast(t('msg.exportFailed'), { type: 'err' });
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
  const linked = doc.cards.filter(c => c.gsId);       /* les groupes de la fiche gardent leurs cartes ; la fiche n'est pas touchée */
  const ex = normalizeDoc(clone(CURRENT_LANG === 'en' ? EXAMPLE_DOC_EN : EXAMPLE_DOC));   // la langue de l'interface au moment du clic
  ex.cards = linked.concat(ex.cards);
  setDoc(ex);
  curIdx = linked.length;
  renderAll();
  showToast(t('toast.example'), { type: 'ok' });
}
function resetDoc() {
  if (!confirm(t('confirm.reset'))) return;
  setDoc(newDoc());
  showToast(t('toast.reset'), { type: 'ok' });
}

/* ============= CÂBLAGE ============= */
function bindEvents() {
  const ed = document.getElementById('editor');
  ed.addEventListener('input', onEditorInput);
  ed.addEventListener('change', onEditorInput);
  ed.addEventListener('focusin', onEditorFocusIn);
  ed.addEventListener('focusout', onEditorFocusOut);
  ed.addEventListener('click', onEditorClick);
  ed.addEventListener('toggle', e => {
    const d = e.target;
    if (d && d.matches && d.matches('details.ed-section')) openState[d.dataset.section] = d.open;
  }, true);
  document.getElementById('pack-bar').addEventListener('click', onPackClick);
  document.getElementById('grp-backdrop').addEventListener('click', grpClose);
  document.getElementById('grp-modal').addEventListener('click', e => { const b = e.target.closest('[data-grp-act]'); if (b && !b.disabled) grpAct(b.dataset.grpAct); });
  document.getElementById('grp-modal').addEventListener('change', e => { const b = document.querySelector('#grp-actions [data-grp-act="attach"]'); if (b && e.target.name === 'grp-pick') b.disabled = false; });

  document.getElementById('mode-seg').addEventListener('click', e => {
    const b = e.target.closest('[data-mode]');
    if (b) setMode(b.dataset.mode);
  });
  document.getElementById('btn-briefing').addEventListener('click', () => openImportModal(null));
  const fileLoad = document.getElementById('file-load');
  document.getElementById('btn-json-import').addEventListener('click', () => { fileLoad.value = ''; fileLoad.click(); });
  fileLoad.addEventListener('change', () => { if (fileLoad.files && fileLoad.files[0]) loadJsonFile(fileLoad.files[0]); });
  document.getElementById('btn-json-export').addEventListener('click', e => openSaveModal(e.currentTarget));
  ['save-close', 'save-cancel'].forEach(id => document.getElementById(id).addEventListener('click', closeSaveModal));
  /* le fond ignore les clics des 400 ms qui suivent l'ouverture : le 2e clic d'un double-clic sur « Enregistrer » ne ferme pas la fenêtre */
  document.getElementById('save-backdrop').addEventListener('click', () => { if (performance.now() - SAVEN.at > 400) closeSaveModal(); });
  document.getElementById('save-go').addEventListener('click', saveGo);
  document.getElementById('save-fname').addEventListener('input', e => { SAVEN.name = e.target.value; saveSync(); });
  document.getElementById('save-fname').addEventListener('keydown', e => { if (e.key === 'Enter') { e.preventDefault(); if (!e.repeat) saveGo(); } });
  document.getElementById('btn-print').addEventListener('click', openExportModal);
  document.getElementById('btn-example').addEventListener('click', loadExample);
  document.getElementById('btn-reset').addEventListener('click', resetDoc);
  document.getElementById('theme-select').addEventListener('change', e => applyTheme(e.target.value, true));
  document.getElementById('theatre').addEventListener('change', e => dgSetTheatre(e.target.value));
  unBind();
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
  document.getElementById('export-png-fname').addEventListener('input', e => { PNGN.name = e.target.value; PNGN.edited = true; updatePngCount(); });
  document.getElementById('export-png-fname').addEventListener('keydown', e => { if (e.key === 'Enter') { e.preventDefault(); const g = document.getElementById('export-png-go'); if (!g.disabled && !e.repeat) executePngExport(); } });

  /* Import depuis un briefing ou une route ; les groupes passent par la fenêtre d'import commune */
  document.getElementById('import-modal-backdrop').addEventListener('click', closeImportModal);
  document.getElementById('import-modal-close').addEventListener('click', closeImportModal);
  document.getElementById('bi-cancel').addEventListener('click', closeImportModal);
  document.getElementById('bi-go').addEventListener('click', runImport);
  document.getElementById('bi-list').addEventListener('change', biUpdateGo);
  document.getElementById('bi-src-current').addEventListener('change', () => { bi.src = 'current'; biRefresh(); });
  document.getElementById('bi-src-route').addEventListener('change', () => { bi.src = 'route'; biRefresh(); });
  document.getElementById('bi-src-file').addEventListener('change', () => { bi.src = 'file'; biRefresh(); });
  const fb = document.getElementById('file-briefing');
  document.getElementById('bi-file-btn').addEventListener('click', () => { fb.value = ''; fb.click(); });
  fb.addEventListener('change', () => { if (fb.files && fb.files[0]) loadBriefingFile(fb.files[0]); });
  document.getElementById('bi-groups').addEventListener('click', () => { closeImportModal(); impOpen({ opener: document.getElementById('btn-briefing') }); });

  /* Tab et Maj+Tab bouclent sur les contrôles de la fenêtre « Enregistrer » */
  document.addEventListener('keydown', e => {
    if (e.key !== 'Tab' || !saveModalOpen()) return;
    const m = document.getElementById('save-modal');
    const els = Array.prototype.filter.call(m.querySelectorAll('button, input'), x => !x.disabled && x.offsetParent !== null);
    if (!els.length) return;
    const first = els[0], last = els[els.length - 1];
    if (e.shiftKey && (document.activeElement === first || !m.contains(document.activeElement))) { e.preventDefault(); last.focus(); }
    else if (!e.shiftKey && (document.activeElement === last || !m.contains(document.activeElement))) { e.preventDefault(); first.focus(); }
  });

  document.addEventListener('keydown', e => {
    if (e.key !== 'Escape') return;
    if (saveModalOpen()) { e.preventDefault(); closeSaveModal(); return; }
    if (!document.getElementById('grp-modal').hidden) { grpClose(); return; }
    if (!document.getElementById('export-modal').hidden) closeExportModal();
    if (!document.getElementById('import-modal').hidden) closeImportModal();
  });

  document.querySelectorAll('#tab-bar button').forEach(b => b.addEventListener('click', () => setActiveTab(b.dataset.tab)));
  initScrollBar(document.querySelector('.toolbar'));
  initScrollBar(document.getElementById('tab-bar'));

  /* Passage depuis le Route Planner (même origine : l'évènement vient d'un autre document) */
  window.addEventListener('storage', e => { if (e.key === KEY_HANDOFF) checkRouteHandoff(); if (e.key === KEY_THEATRE) dgFollowTheatre(); if (e.key === KEY_UNITS) dgFollowUnits(); if (e.key === KEY_THEATRE || e.key === KEY_ROUTE || e.key === KEY_ROUTESET) dgRoutesRefresh(); dgStorage(e); });

  window.addEventListener('beforeprint', fillPrintRoot);
  window.addEventListener('afterprint', clearPrintRoot);
  let rz = null;
  window.addEventListener('resize', () => { clearTimeout(rz); rz = setTimeout(applyPreviewScale, 60); dgRelayout(); });
  if (window.ResizeObserver) new ResizeObserver(dgRelayout).observe(document.getElementById('measure-root'));       /* le cadre redevient visible dans le shell : l'aperçu se refait avec un plan mesuré */

  /* Le shell règle le thème en posant body[data-theme] : suivre sans réécrire la clé */
  new MutationObserver(() => {
    const sel = document.getElementById('theme-select');
    const cur = document.body.dataset.theme;
    if (sel && cur && sel.value !== cur && THEME_IDS.indexOf(cur) !== -1) sel.value = cur;
  }).observe(document.body, { attributes: true, attributeFilter: ['data-theme'] });
}

/* ============= LE MENU « UNITÉS » (recopié du Route Planner, lot mp-theatre-unique) =============
   Même composant et même aspect que le menu du Route Planner (tbm-panel dsp-panel, dsp-opt, dsp-box), des lignes « radio » : une seule unité par groupe, celle de dgU ;
   trois groupes ici (Masse, Distance, Altitude) ; les titres des groupes sont ceux des anciens réglages par carte. Un choix règle l'unité et la clé ; le panneau reste ouvert. */
const UN = { open: false, panel: null, x0: 0, y0: 0 };
const UN_ROWS = [
  { g: 'mass', k: 'kg' }, { g: 'mass', k: 'lb' },
  { g: 'distance', k: 'km' }, { g: 'distance', k: 'nm' },
  { g: 'altitude', k: 'm' }, { g: 'altitude', k: 'ft' }
];
function unOn(r) { return dgU[r.g] === r.k; }
/* Le bouton dit le réglage en cours (distance · altitude, comme au Route Planner) ; les cases du panneau ouvert le suivent */
function dgUnitsSync() {
  const tx = document.getElementById('units-txt');
  if (tx) tx.textContent = t('u.' + dgU.distance) + ' · ' + t('u.' + dgU.altitude);
  if (!UN.open || !UN.panel) return;
  UN_ROWS.forEach(r => {
    const row = UN.panel.querySelector('[data-g="' + r.g + '"][data-k="' + r.k + '"]');
    if (row) row.setAttribute('aria-checked', unOn(r) ? 'true' : 'false');
  });
}
function unBuild() {
  const ul = UN.panel;
  ul.textContent = '';
  ul.setAttribute('aria-label', t('tb.units'));
  const head = document.createElement('div');
  head.className = 'tbm-head';
  head.setAttribute('role', 'presentation');
  head.textContent = t('tb.units');
  ul.appendChild(head);
  let g = '';
  UN_ROWS.forEach(r => {
    if (r.g !== g) {
      g = r.g;
      const sub = document.createElement('div');
      sub.className = 'dsp-sub';
      sub.setAttribute('role', 'presentation');
      sub.textContent = t('f.' + g);
      ul.appendChild(sub);
    }
    const row = document.createElement('div');
    row.className = 'tbm-opt dsp-opt';
    row.setAttribute('role', 'menuitemradio');
    row.setAttribute('aria-checked', 'false');
    row.tabIndex = -1;
    row.setAttribute('data-g', r.g);
    row.setAttribute('data-k', r.k);
    const box = document.createElement('span');
    box.className = 'dsp-box';
    box.setAttribute('aria-hidden', 'true');
    const txt = document.createElement('span');
    txt.className = 'tbm-txt';
    txt.textContent = t('u.' + r.k);
    row.appendChild(box);
    row.appendChild(txt);
    ul.appendChild(row);
  });
  dgUnitsSync();
}
function unPlace() {
  const btn = document.getElementById('btn-units'), p = UN.panel;
  const r = btn.getBoundingClientRect();
  const vw = document.documentElement.clientWidth, vh = window.innerHeight;
  const top = r.bottom + 4;
  UN.x0 = r.left; UN.y0 = r.top;
  p.style.minWidth = Math.max(240, r.width) + 'px';
  p.style.top = top + 'px';
  p.style.maxHeight = Math.max(60, Math.min(0.8 * vh, 600, vh - top - 8)) + 'px';
  const w = p.getBoundingClientRect().width;
  let left = r.left;
  if (left + w > vw - 8) left = vw - 8 - w;
  if (left < 8) left = 8;
  p.style.left = left + 'px';
}
function unOpen() {
  if (UN.open) return;
  if (TBM.cur) tbmClose(false);
  const ul = document.createElement('div');
  ul.className = 'tbm-panel dsp-panel';
  ul.id = 'un-panel';
  ul.setAttribute('role', 'menu');
  ul.tabIndex = -1;
  document.body.appendChild(ul);
  UN.panel = ul;
  UN.open = true;
  unBuild();
  ul.addEventListener('click', e => {
    const row = e.target.closest ? e.target.closest('.dsp-opt') : null;
    if (row) unChoose(row.getAttribute('data-g'), row.getAttribute('data-k'));
  });
  ul.addEventListener('keydown', unKey);
  const b = document.getElementById('btn-units');
  b.classList.add('dsp-open');
  b.setAttribute('aria-expanded', 'true');
  b.setAttribute('aria-controls', 'un-panel');
  unPlace();
  ul.focus({ preventScroll: true });
}
function unClose(refocus) {
  if (!UN.open) return;
  UN.open = false;
  if (UN.panel) UN.panel.remove();
  UN.panel = null;
  const b = document.getElementById('btn-units');
  b.classList.remove('dsp-open');
  b.setAttribute('aria-expanded', 'false');
  if (refocus) b.focus({ preventScroll: true });
}
function unKey(e) {
  const rows = Array.prototype.slice.call(UN.panel.querySelectorAll('.dsp-opt'));
  const cur = rows.indexOf(document.activeElement);
  const go = k => { if (rows[k]) { rows[k].focus({ preventScroll: true }); rows[k].scrollIntoView({ block: 'nearest' }); } };
  const k = e.key;
  if (k === 'ArrowDown') { e.preventDefault(); go(cur < 0 ? 0 : Math.min(rows.length - 1, cur + 1)); }
  else if (k === 'ArrowUp') { e.preventDefault(); go(cur < 0 ? rows.length - 1 : Math.max(0, cur - 1)); }
  else if (k === 'Home') { e.preventDefault(); go(0); }
  else if (k === 'End') { e.preventDefault(); go(rows.length - 1); }
  else if ((k === 'Enter' || k === ' ') && cur >= 0) { e.preventDefault(); unChoose(rows[cur].getAttribute('data-g'), rows[cur].getAttribute('data-k')); }
  else if (k === 'Escape') { e.preventDefault(); e.stopPropagation(); unClose(true); }
  else if (k === 'Tab') unClose(true);
}
/* Un toucher ou un clic hors du panneau et du bouton le ferme, sans agir ailleurs (le clic qui suit est avalé) */
function unOutside(e) {
  if (!UN.open) return;
  const t = e.target;
  if (UN.panel.contains(t) || document.getElementById('btn-units').contains(t)) return;
  const other = t && t.closest ? t.closest('.tbm-trigger') : null;
  unClose(false);
  if (other) return;
  tbmSwallowNext();
}
/* Une ligne règle l'unité de son groupe (le menu reste ouvert) */
function unChoose(g, k) {
  const u = { mass: dgU.mass, distance: dgU.distance, altitude: dgU.altitude };
  if (!(g in u)) return;
  u[g] = k;
  dgUnitsSet(u);
}
function unBind() {
  const b = document.getElementById('btn-units');
  b.addEventListener('click', () => { if (UN.open) unClose(false); else unOpen(); });
  b.addEventListener('keydown', e => {
    if (e.key === 'ArrowDown' && !UN.open) { e.preventDefault(); unOpen(); }
  });
  document.addEventListener('pointerdown', unOutside, true);
  document.addEventListener('keydown', e => { if (e.key === 'Escape' && UN.open) { e.preventDefault(); unClose(true); } });
  window.addEventListener('resize', () => unClose(false));
  window.addEventListener('blur', () => unClose(false));
  window.addEventListener('scroll', e => {
    if (!UN.open || (e.target && e.target.nodeType && UN.panel.contains(e.target))) return;
    const r = b.getBoundingClientRect();
    if (Math.abs(r.left - UN.x0) > 0.5 || Math.abs(r.top - UN.y0) > 0.5) unClose(false);
  }, true);
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
  specs.forEach(sp => tbmAttach(document.getElementById(sp[0]), sp[1], sp[2], sp[3]));
  if (TBM.bound) return;
  TBM.bound = true;
  document.addEventListener('pointerdown', tbmOutside, true);
  window.addEventListener('click', tbmSwallowClick, true);
  window.addEventListener('resize', tbmResized);
  window.addEventListener('blur', () => tbmClose(false));
  window.addEventListener('scroll', tbmScrolled, true);
  if (window.visualViewport) { window.visualViewport.addEventListener('resize', tbmVvChanged); window.visualViewport.addEventListener('scroll', tbmVvChanged); }
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
   bouton fermé déjà habillé par le module) ; fit : le bouton prend la largeur de l'option choisie (comme au Route Planner) ;
   un <select data-search> reçoit une recherche en tête de sa liste (lot mp-dg-terrains-liste : seule la liste des aérodromes) */
function tbmAttach(sel, labelFn, mode, fit) {
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
  const m = { sel: sel, btn: btn, lbl: lbl, labelFn: labelFn, panel: null, active: -1, type: '', typeTimer: 0, x0: 0, y0: 0, uid: uid, form: !!mode, fit: !!fit, search: sel.hasAttribute('data-search'), q: null, lis: [], list: null, none: null, noneLi: null, bar: null, empty: '', up: undefined, mo: null };
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
  const w = m.fit ? txt : all.join(String.fromCharCode(10));       /* fit : le bouton prend la largeur de l'option choisie */
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
  const panel = document.createElement('div');
  panel.className = 'tbm-panel' + (m.form ? ' tbm-p-field' : '');
  panel.id = 'tbm-panel-' + m.uid;
  const head = document.createElement('div');
  head.className = 'tbm-head';
  head.setAttribute('aria-hidden', 'true');
  head.textContent = name;
  panel.appendChild(head);
  const ul = document.createElement('ul');
  ul.className = 'tbm-list';
  ul.id = 'tbm-list-' + m.uid;
  ul.setAttribute('role', 'listbox');
  ul.setAttribute('aria-label', name);
  ul.tabIndex = -1;
  let real = 0;
  for (let k = 0; k < opts.length; k++) if (opts[k].value !== '' && !opts[k].hasAttribute('data-keep')) real++;
  m.q = null; m.none = null; m.noneLi = null; m.bar = null; m.list = ul; m.lis = [];
  if (m.search) {
    /* le champ de recherche est un combobox hors de la listbox (modèle ARIA) ; sans aucune option à chercher, pas de champ : seule la ligne neutre le dit */
    if (real > 0) {
      const bar = document.createElement('div');
      bar.className = 'tbm-search';
      const q = document.createElement('input');
      q.type = 'text';
      q.className = 'tbm-q';
      q.setAttribute('role', 'combobox');
      q.setAttribute('aria-controls', ul.id);
      q.setAttribute('aria-expanded', 'true');
      q.setAttribute('aria-autocomplete', 'list');
      q.setAttribute('placeholder', t('f.search'));
      q.setAttribute('aria-label', t('f.search'));
      q.setAttribute('autocomplete', 'off');
      q.setAttribute('autocapitalize', 'off');
      q.setAttribute('spellcheck', 'false');
      q.setAttribute('enterkeyhint', 'search');
      q.addEventListener('input', () => tbmFilter(m));
      bar.appendChild(q);
      panel.appendChild(bar);
      m.q = q; m.bar = bar;
    }
    /* la ligne neutre (L4) : dans la liste, entre « Choisir… » ou les aérodromes et « Autre… » ; elle est transparente pour la listbox (role presentation) et son texte est dans une zone aria-live qui existe toujours, vide tant qu'il y a des résultats */
    const none = document.createElement('li');
    none.className = 'tbm-none';
    none.setAttribute('role', 'presentation');
    const msg = document.createElement('div');
    msg.className = 'tbm-msg';
    msg.setAttribute('aria-live', 'polite');
    m.empty = sel.getAttribute('data-search-empty') || '';
    if (real === 0) msg.textContent = m.empty;
    none.appendChild(msg);
    m.none = msg;
    m.noneLi = none;
  }
  for (let k = 0; k < opts.length; k++) {
    const o = opts[k], li = document.createElement('li');
    li.className = 'tbm-opt';
    if (o.hasAttribute('data-keep')) li.setAttribute('data-keep', '');
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
    m.lis.push(li);
  }
  if (m.noneLi) ul.insertBefore(m.noneLi, m.lis.find(x => x.hasAttribute('data-keep')) || null);
  panel.appendChild(ul);
  panel.addEventListener('keydown', e => tbmKey(m, e));
  panel.addEventListener('click', e => {
    const li = e.target.closest ? e.target.closest('.tbm-opt') : null;
    if (!li || li.getAttribute('aria-disabled') === 'true') return;
    tbmChoose(m, Number(li.getAttribute('data-i')));
  });
  panel.addEventListener('mousemove', e => {
    const li = e.target.closest ? e.target.closest('.tbm-opt') : null;
    if (!li || li.getAttribute('aria-disabled') === 'true') return;
    const k = Number(li.getAttribute('data-i'));
    if (k !== m.active) tbmSetActive(m, k, false);
  });
  document.body.appendChild(panel);
  m.panel = panel;
  TBM.cur = m;
  m.btn.classList.add('tbm-trigger-open');
  m.btn.setAttribute('aria-expanded', 'true');
  m.up = undefined;
  tbmPlace(m);
  let k0 = sel.selectedIndex;
  if (k0 < 0 || (opts[k0] && opts[k0].disabled)) k0 = tbmFirst(m, 1);
  tbmSetActive(m, k0, 'center');
  if (m.q && window.matchMedia && window.matchMedia('(hover: hover) and (pointer: fine)').matches) m.q.focus({ preventScroll: true });       /* la recherche a le focus sur ordinateur, pas au toucher (le clavier de l'écran ne s'ouvre pas seul) */
  else ul.focus({ preventScroll: true });
}

/* Sans casse ni accents */
function tbmNorm(x) { return String(x).normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase(); }
/* La recherche : au fil de la frappe, une partie du nom ; « Autre… » (data-keep) reste ; sans résultat, une ligne neutre ; l'option active devient la première trouvée */
function tbmFilter(m) {
  const q = tbmNorm(m.q.value.trim()), o = m.sel.options;
  let n = 0, first = -1;
  m.lis.forEach((li, k) => {
    const keep = li.hasAttribute('data-keep');
    const show = q === '' || keep || (o[k].value !== '' && tbmNorm(o[k].label).indexOf(q) >= 0);
    li.classList.toggle('tbm-off', !show);
    if (q !== '' && !keep && show) { n++; if (first < 0) first = k; }
  });
  const none = q !== '' && n === 0;
  m.none.textContent = none ? m.empty : '';       /* la ligne sans résultat est annoncée (aria-live) quand son texte apparaît */
  if (m.form) tbmPlace(m, true);       /* la liste a changé de hauteur : ouverte vers le haut, elle reste accrochée au bouton */
  if (q === '') { m.panel.scrollTop = 0; tbmSetActive(m, m.sel.selectedIndex >= 0 ? m.sel.selectedIndex : tbmFirst(m, 1), true); return; }
  if (first < 0) first = m.lis.findIndex(li => li.hasAttribute('data-keep'));
  m.panel.scrollTop = 0;
  tbmSetActive(m, first, true);
}
function tbmOff(m, k) { return !!(m.lis[k] && m.lis[k].classList.contains('tbm-off')); }

/* Sous le bouton (4 px), bord gauche aligné, au moins aussi large, à 8 px au moins des bords de la fenêtre.
   Liste de formulaire : la place utile va du bas de la barre du haut au haut de la barre d'onglets fixée en bas (portrait),
   sinon au bas de la fenêtre ; dessous si elle y tient entière, sinon dessus si la place y est plus grande (classe tbm-up). Appelée à l'ouverture, après chaque filtrage (sens gardé : keepDir)
   et quand la fenêtre est redimensionnée ou défilée pendant que la recherche a le focus (le clavier de l'écran). */
/* La zone visible, en coordonnées de la fenêtre : le visualViewport quand il existe (sur Chrome Android et iOS, le clavier de l'écran ne réduit que lui), sinon la fenêtre ;
   dans un cadre (le shell), la fenêtre du cadre : le shell la fait suivre le clavier, et le visualViewport d'un cadre n'est pas fiable */
function tbmVis() {
  const v = window.visualViewport;
  if (v && v.height > 0 && v.width > 0 && window.parent === window) return { top: v.offsetTop, bottom: v.offsetTop + v.height, left: v.offsetLeft, right: v.offsetLeft + v.width };
  return { top: 0, bottom: window.innerHeight, left: 0, right: document.documentElement.clientWidth };
}
function tbmScroller(el) {
  for (let e = el.parentElement; e && e !== document.documentElement; e = e.parentElement) {
    const o = getComputedStyle(e).overflowY;
    if ((o === 'auto' || o === 'scroll') && e.scrollHeight > e.clientHeight + 1) return e;
  }
  return null;
}
/* Pendant la recherche : le bouton sorti de la zone visible (clavier, défilement) est ramené au centre de celle-ci, puis la liste se replace */
function tbmReveal(m) {
  const r = m.btn.getBoundingClientRect(), vis = tbmVis(), tb = document.querySelector('header.toolbar');
  const lo = Math.max(vis.top, tb ? tb.getBoundingClientRect().bottom : 0);
  if (r.bottom <= vis.bottom - 8 && r.top >= lo) return;
  const d = (r.top + r.height / 2) - (lo + (vis.bottom - lo) / 2), sc = tbmScroller(m.btn);
  if (sc) sc.scrollTop += d; else window.scrollBy(0, d);
}
function tbmPlace(m, keepDir) {
  const r = m.btn.getBoundingClientRect(), p = m.panel;
  const vis = tbmVis(), vw = vis.right, vh = vis.bottom;       /* la zone visible (visualViewport) : le clavier de l'écran ne réduit parfois que celle-ci */
  let top = r.bottom + 4;
  m.x0 = r.left; m.y0 = r.top;
  if (m.form) {
    const tb = document.querySelector('header.toolbar'), bar = document.querySelector('.tab-bar');
    const lo = Math.max(vis.top, tb ? tb.getBoundingClientRect().bottom : 0);
    let hi = vh;
    if (bar) {
      const bs = getComputedStyle(bar), br = bar.getBoundingClientRect();
      if (bs.position === 'fixed' && bs.display !== 'none' && br.height > 0 && br.top > lo) hi = Math.min(hi, br.top);
    }
    const cap = tbmKb(m) ? Math.max(60, vh - lo - 8) : Math.min(0.62 * (vh - vis.top), 440);       /* pendant la recherche au toucher (clavier de l'écran) : plus de plafond, toute la hauteur visible */
    const below = hi - (r.bottom + 4) - 12, above = (r.top - 4) - lo - 12;
    p.style.minWidth = Math.min(Math.max(180, r.width), vw - 16) + 'px';
    p.style.maxHeight = 'none';
    const up = keepDir && m.up !== undefined ? m.up : Math.min(p.offsetHeight, cap) > below && above > below;       /* keepDir : le sens choisi à l'ouverture ne change pas pendant la frappe */
    m.up = up;
    p.style.maxHeight = Math.max(60, Math.min(cap, up ? above : below, vh - lo - 8)) + 'px';
    p.classList.toggle('tbm-up', up);
    let ty = up ? r.top - 4 - p.offsetHeight : r.bottom + 4;
    ty = Math.max(lo, Math.min(ty, vh - 4 - p.offsetHeight));       /* le bouton hors de la zone visible et sans rien à défiler : la liste reste dans la zone visible */
    p.style.top = ty + 'px';
    p.style.left = r.left + 'px';
    const fw = p.getBoundingClientRect().width;
    let fl = r.left;
    if (fl + fw > vw - 8) fl = vw - 8 - fw;
    if (fl < vis.left + 8) fl = vis.left + 8;
    p.style.left = fl + 'px';
    return;
  }
  p.style.minWidth = Math.max(180, r.width) + 'px';
  p.style.top = top + 'px';
  p.style.left = r.left + 'px';
  p.style.maxHeight = Math.max(60, Math.min(0.62 * (vh - vis.top), 440, vh - top - 12)) + 'px';
  const w = p.getBoundingClientRect().width;
  let left = r.left;
  if (left + w > vw - 8) left = vw - 8 - w;
  if (left < vis.left + 8) left = vis.left + 8;
  p.style.left = left + 'px';
}

function tbmFirst(m, d) {
  const o = m.sel.options;
  let k = d > 0 ? 0 : o.length - 1;
  for (; k >= 0 && k < o.length; k += d) if (!o[k].disabled && !tbmOff(m, k)) return k;
  return -1;
}

function tbmSetActive(m, k, reveal) {
  const p = m.panel;
  if (!p) return;
  const prev = p.querySelector('.tbm-opt.active');
  if (prev) prev.classList.remove('active');
  m.active = k;
  const li = k >= 0 ? p.querySelector('.tbm-opt[data-i="' + k + '"]') : null;
  const holders = [m.list, m.q].filter(Boolean);       /* la listbox, et le champ de recherche quand il y en a un */
  if (!li) { holders.forEach(h => h.removeAttribute('aria-activedescendant')); return; }
  li.classList.add('active');
  holders.forEach(h => h.setAttribute('aria-activedescendant', li.id));
  if (!reveal) return;
  const t = li.offsetTop, h = li.offsetHeight, sh = m.bar ? m.bar.offsetHeight : 0;       /* la recherche collée en haut cache les sh premiers pixels */
  if (k === tbmFirst(m, 1)) p.scrollTop = 0;
  else if (t - sh < p.scrollTop) p.scrollTop = Math.max(0, t - sh);
  else if (t + h > p.scrollTop + p.clientHeight) p.scrollTop = reveal === 'center' ? Math.max(0, t - sh - (p.clientHeight - sh - h) / 2) : t + h - p.clientHeight;
}

function tbmStep(m, d) {
  const o = m.sel.options;
  for (let k = m.active + d; k >= 0 && k < o.length; k += d) {
    if (!o[k].disabled && !tbmOff(m, k)) { tbmSetActive(m, k, true); return; }
  }
}

/* Saisie de lettres : première option qui commence par elles, remise à zéro après 0,7 s */
function tbmType(m, ch) {
  clearTimeout(m.typeTimer);
  m.type += ch.toLowerCase();
  m.typeTimer = setTimeout(() => { m.type = ''; }, 700);
  const o = m.sel.options;
  for (let k = 0; k < o.length; k++) {
    if (!o[k].disabled && !tbmOff(m, k) && o[k].label.toLowerCase().indexOf(m.type) === 0) { tbmSetActive(m, k, true); return; }
  }
}

/* Les touches dans le champ de recherche : ↓ passe à la première option, Entrée choisit l'option active, Échap ferme ; le reste est de la frappe */
function tbmQKey(m, e) {
  const k = e.key;
  if (k === 'ArrowDown') { e.preventDefault(); tbmSetActive(m, tbmFirst(m, 1), true); m.list.focus({ preventScroll: true }); }
  else if (k === 'ArrowUp') e.preventDefault();
  else if (k === 'Enter') { e.preventDefault(); if (m.active >= 0 && !tbmOff(m, m.active)) tbmChoose(m, m.active); }
  else if (k === 'Escape') { e.preventDefault(); e.stopPropagation(); tbmClose(true); }
  else if (k === 'Tab') tbmClose(true);
}

function tbmKey(m, e) {
  const k = e.key;
  if (m.q && e.target === m.q) { tbmQKey(m, e); return; }
  if (m.q && k === 'ArrowUp' && m.active === tbmFirst(m, 1) && e.target !== m.q) { e.preventDefault(); m.q.focus({ preventScroll: true }); return; }       /* ↑ sur la première option : le focus revient au champ */
  if (m.q && k.length === 1 && k !== ' ' && !e.ctrlKey && !e.metaKey && !e.altKey) {       /* une lettre tapée sur la liste va à la recherche ; Espace, non : il choisit l'option active (dans le champ, il se tape) */
    e.preventDefault();
    m.q.focus({ preventScroll: true });
    m.q.value += k;
    tbmFilter(m);
    return;
  }
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
  m.q = null; m.bar = null; m.none = null; m.noneLi = null; m.list = null; m.lis = [];
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
  const other = t && t.closest ? t.closest('.tbm-trigger, #btn-units') : null;
  tbmClose(false);
  if (other) return;
  tbmSwallowNext();
}

/* Le clic qui suit le toucher hors de la liste est avalé (aussi pour le menu « Unités ») */
function tbmSwallowNext() {
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

/* Le champ de recherche a le focus : le clavier de l'écran redimensionne la fenêtre ou fait défiler la page ; la liste ne se ferme pas, elle se replace */
function tbmSearching(m) { return !!(m && m.panel && m.q && document.activeElement === m.q); }

/* La recherche au toucher : le clavier de l'écran est ouvert (pas de souris : sur ordinateur la recherche a le focus dès l'ouverture, sans clavier) */
function tbmKb(m) { return tbmSearching(m) && !(window.matchMedia && window.matchMedia('(hover: hover) and (pointer: fine)').matches); }
/* La hauteur qu'il faut pour le champ et quatre options entières (ou toutes, s'il y en a moins) */
function tbmNeed(m) {
  const p = m.panel, h0 = p.style.maxHeight, sy = p.scrollTop;
  p.style.maxHeight = 'none';
  p.scrollTop = 0;
  const pr = p.getBoundingClientRect();
  const opts = m.lis.filter(li => !li.classList.contains('tbm-off'));
  let need = p.offsetHeight;
  if (opts.length) {
    const last = opts[Math.min(4, opts.length) - 1].getBoundingClientRect();
    need = Math.min(need, last.bottom - pr.top + 4);
  }
  p.style.maxHeight = h0;
  p.scrollTop = sy;
  return need;
}
/* Si la place sous le bouton ne suffit pas, le bouton remonte en haut de la zone visible (sous la barre, 8 px) : vrai quand la place sous lui suffit ensuite */
function tbmFit(m) {
  const vis = tbmVis(), tb = document.querySelector('header.toolbar'), bar = document.querySelector('.tab-bar');
  const lo = Math.max(vis.top, tb ? tb.getBoundingClientRect().bottom : 0);
  let hi = vis.bottom;
  if (bar) {
    const bs = getComputedStyle(bar), br = bar.getBoundingClientRect();
    if (bs.position === 'fixed' && bs.display !== 'none' && br.height > 0 && br.top > lo) hi = Math.min(hi, br.top);
  }
  const below = () => hi - (m.btn.getBoundingClientRect().bottom + 4) - 12;
  const need = tbmNeed(m);
  if (below() >= need) return false;
  const d = m.btn.getBoundingClientRect().top - (lo + 8);
  if (Math.abs(d) > 0.5) {
    const sc = tbmScroller(m.btn);
    if (sc) sc.scrollTop += d; else window.scrollBy(0, d);
    const rest = m.btn.getBoundingClientRect().top - (lo + 8);
    if (sc && Math.abs(rest) > 0.5) window.scrollBy(0, rest);
  }
  return below() >= need;
}

/* Le redimensionnement de la fenêtre ferme la liste, sauf pendant la recherche (elle se replace, le bouton ramené à l'écran) */
function tbmResized() {
  const m = TBM.cur;
  if (tbmSearching(m)) { tbmFollow(m); return; }
  tbmClose(false);
}
function tbmFollow(m) {
  if (!m.form) return;
  tbmReveal(m);
  if (tbmKb(m) && tbmFit(m)) { m.up = false; tbmPlace(m, true); return; }
  tbmPlace(m);
}
/* Le visualViewport (zone visible) change — clavier de l'écran, zoom : sans effet hors recherche ; pendant la recherche la liste se replace dans la zone visible */
function tbmVvChanged() {
  const m = TBM.cur;
  if (tbmSearching(m)) tbmFollow(m);
}

/* Le défilement de la barre (ou de la page) déplace le bouton : la liste se ferme, sauf pendant la recherche (le bouton sorti de la zone visible est ramené, la liste se replace) */
function tbmScrolled(e) {
  const m = TBM.cur;
  if (!m || !m.panel) return;
  if (e.target === m.panel || (e.target.nodeType && m.panel.contains(e.target))) return;
  const r = m.btn.getBoundingClientRect();
  if (Math.abs(r.left - m.x0) > 0.5 || Math.abs(r.top - m.y0) > 0.5) {
    if (tbmSearching(m)) { tbmFollow(m); return; }
    tbmClose(false);
  }
}

function init() {
  initLang();
  applyTheme(loadTheme(), false);
  applyI18nStatic();
  updateFlagButton();
  initToolbarMenus([['theme-select', () => t('tb.theme.tip')]]);   /* les listes de la barre au thème de l'interface */
  initFormMenus(sel => { const f = sel.closest('.ed-field'), l = f && f.querySelector('label'); return l ? l.textContent.trim() : (sel.getAttribute('aria-label') || ''); });   /* les listes des formulaires */
  impSetup({ lang: () => CURRENT_LANG, onImported: dgImported, toast: msg => showToast('\u26a0 ' + msg, { type: 'err' }) });      /* la fenêtre d'import commune : elle écrit dans la fiche, les cartes suivent */
  gsMigrate(dgPackFn);
  loadState();
  { const k = dgReadUnitsKey(); dgUnitsSet(k || doc.cards[0].units, !!k); }       /* la clé fait foi ; absente, la première carte du document la pose */
  const th0 = doc.theatre;
  { const k = dgReadTheatreKey(); if (k) doc.theatre = k; }       /* le théâtre que le Route Planner a écrit : le dernier changement gagne */
  dgFillTheatre();
  initToolbarMenus([['theatre', () => t('tb.theatre'), undefined, true]]);       /* la liste du théâtre, comme au Route Planner */
  gsApplyAll(true);
  if (doc.theatre !== th0) persistState();       /* un théâtre pris (clé partagée, fiche ou route) est gardé */
  bindEvents();
  setActiveTab('meta');
  renderAll();
  checkRouteHandoff();
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
    try:
        example_en = json.loads(EXAMPLE_DOC_JSON_EN)
    except ValueError as e:
        raise SystemExit(f"[ERREUR] Document d'exemple anglais illisible : {e}")
    if example_en.get('format') != 'dcs-datacard-v1':
        raise SystemExit("[ERREUR] Le document d'exemple anglais n'est pas au format dcs-datacard-v1")
    example_en_js = json.dumps(example_en, ensure_ascii=False, indent=2).replace('</', '<\\/')

    _wn, _pyl, _lim = dg_tables()
    js = JS.replace('@@WEAPON_NAMES@@', _wn).replace('@@AIRCRAFT_PYLONS@@', _pyl).replace('@@AIRCRAFT_LIMITS@@', _lim)
    js = js.replace('@@PAYLOAD_BLOCK@@\n', build_payload_block()).replace('@@IMPORT_BLOCK@@\n', build_import_block()).replace('@@MESSAGES_BLOCK@@\n', build_messages_block())
    _facts = airfield_facts()
    facts_js = json.dumps(_facts, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
    js = js.replace('__AIRFIELD_FACTS__', facts_js)
    icao_js = json.dumps(airfield_icao(_facts), ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
    js = js.replace('__AIRFIELD_ICAO__', icao_js)
    js = js.replace('@@ROUTE_PACK_BLOCK@@\n', build_route_pack_block()).replace('@@ROUTE_THEATRE_BLOCK@@\n', build_route_theatre_block()).replace('@@GROUP_STORE_BLOCK@@\n', build_group_store_block())
    js = js.replace('__EXAMPLE_DOC__', example_js).replace('__EXAMPLE_DOC_EN__', example_en_js).replace('@@MAGVAR_BLOCK@@\n', build_magvar_block()).replace('@@RADIO_BLOCK@@\n', build_radio_block()).replace('@@RADIO_BANDS_BLOCK@@\n', build_radio_bands_block()).replace('@@PROJECTION_BLOCK@@\n', build_projection_block())
    html = HTML
    html = html.replace('__CSS__', CSS.replace('@@MESSAGES_CSS@@\n', build_messages_css()) + build_import_css())
    html = html.replace('@@IMPORT_HTML@@\n', build_import_html())
    html = html.replace('__LIB_HTML2CANVAS__', A['lib_html2canvas'])
    html = html.replace('__LIB_JSZIP__', A['lib_jszip'])
    html = html.replace('__APP_VERSION__', APP_VERSION)
    html = html.replace('__APP_JS__', js)

    # Contrôles de construction
    pt, it = re.search(r"const PAYLOAD_TYPES = \[(.*?)\];", build_payload_block()), re.search(r"const IMP_TYPES = \[(.*?)\];", build_import_block())
    if not (pt and it and pt.group(1) == it.group(1)):
        raise SystemExit("[ERREUR] Les types du bloc d'import ne sont pas ceux de PAYLOAD_TYPES")
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
