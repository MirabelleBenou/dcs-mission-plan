#!/usr/bin/env python3
"""Build the Flight Configurator HTML module : un vol (identité, radios, emport, livrée, route portée) et son paquet `dcs-flight-package-v1`.

Produit dist/dcs_flight_configurator.html (fichier autonome, hors-ligne, aucune requête réseau).
Usage : python3 -B build_flight_configurator.py

Blocs partagés insérés tels quels (identiques à l'octet dans les modules qui les utilisent) :
  radio_block.py    — noms des postes radio et numéros de canal du cockpit
  payload_block.py  — presets d'emport (UnitPayloads), pylônes et armes permis, `payload` d'un .miz ; il lit les constantes WEAPON_NAMES,
                      AIRCRAFT_PYLONS et AIRCRAFT_LIMITS, qui sont celles du Loadout Editor de Mission Tools

Tables (data/, copiées à l'octet de Mission Tools ; pydcs 1.0.0, LGPL-3.0 ; les dessins de views/ sont de Goldwolf, hors licence du dépôt) :
elles sont recopiées dans la page entre des marqueurs `/* NOM:BEGIN */` et `/* NOM:END */`, et le build s'arrête si une copie diffère de son fichier.
"""

import json
import os
import re
import subprocess
import sys

from payload_block import build_block as build_payload_block
from radio_block import build_block as build_radio_block

HERE = os.path.dirname(os.path.abspath(__file__))
APP_VERSION = "0.1.0"

with open(os.path.join(HERE, 'assets.json')) as _f:
    A = json.load(_f)

# Les quatre tables : (nom de la constante, fichier de data/)
TABLES = [('WEAPON_NAMES', 'weapon_names.json'), ('AIRCRAFT_LIMITS', 'aircraft_limits.json'),
          ('AIRCRAFT_PYLONS', 'aircraft_pylons.json'), ('AIRCRAFT_VIEWS', 'aircraft_views.json')]

# ---------- CSS : socle commun à la suite (copié de HQ : thèmes, barre, sections, boutons, listes du thème, toast) ----------
CSS_COMMON = """
:root {
  --f-stencil:    'Stardos Stencil', 'Impact', 'Arial Narrow Bold', sans-serif;
  --f-typewriter: 'Roboto Mono', 'Courier New', monospace;
  --f-ui:         'Oswald', 'Arial Narrow', sans-serif;
  --amber:        #c0892a;
  --amber-dark:   #8a5e15;
  --green-radar:  #4f6b3a;
}

/* THÈMES — 4 identiques à Mission Plan */
body[data-theme="cw-nato"] {
  --paper: #d8c9a5; --paper-light: #e3d6b5; --paper-dark: #b8a77c;
  --ink: #1f1c16; --ink-faded: #463f30;
  --olive: #4a5230; --olive-dark: #2c321e; --olive-deep: #1a1e10;
  --khaki: #807454; --khaki-light: #a89a72;
  --rust: #7a3a20;
  --red-stamp: #a83524; --red-faded: #c4574a;
}
body[data-theme="cw-soviet"] {
  --paper: #d8c479; --paper-light: #e8d690; --paper-dark: #b8a64a;
  --ink: #1f1c16; --ink-faded: #463f30;
  --olive: #2a3a5a; --olive-dark: #1a2540; --olive-deep: #0e1830;
  --khaki: #3a4a2e; --khaki-light: #5a6a48;
  --rust: #6a1a1a;
  --red-stamp: #841e1e; --red-faded: #a04040;
}
body[data-theme="modern-nato"] {
  --paper: #e8e3d8; --paper-light: #f0ece2; --paper-dark: #c8c0b0;
  --ink: #15181c; --ink-faded: #3a4048;
  --olive: #2a3038; --olive-dark: #1c2026; --olive-deep: #0e1014;
  --khaki: #5c6b7a; --khaki-light: #7a8a98;
  --rust: #4a3020;
  --red-stamp: #1a1a1a; --red-faded: #4a4a4a;
}
body[data-theme="modern-east"] {
  --paper: #cdc6b8; --paper-light: #ddd6c8; --paper-dark: #ada69a;
  --ink: #1a1610; --ink-faded: #3d3024;
  --olive: #3d3024; --olive-dark: #2a2018; --olive-deep: #1a140e;
  --khaki: #4a5238; --khaki-light: #6a7256;
  --rust: #6a3010;
  --red-stamp: #7a2424; --red-faded: #a04040;
}

* { box-sizing: border-box; margin: 0; padding: 0; }
html, body { height: 100%; overscroll-behavior: none; }
button, input, select, textarea { font: inherit; cursor: pointer; }

body {
  font-family: var(--f-typewriter);
  background: var(--olive-deep);
  color: var(--paper);
  font-size: 14px;
  line-height: 1.5;
  -webkit-tap-highlight-color: transparent;
  -webkit-text-size-adjust: 100%;
}

/* ======== TOOLBAR ======== */
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
  color: var(--amber);
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
.tb-select {
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
}
.tb-select:hover, .tb-select:focus-visible {
  background-color: var(--olive);
  border-color: var(--amber);
  outline: none;
}
.tb-select option { background-color: var(--olive-dark); color: var(--paper); }

/* ---------- Listes de la barre au thème de l'interface (lot mp-ui-listes) ----------
   Le <select> reste dans la page, masqué ; un bouton de mêmes classes prend sa place (voir initToolbarMenus). */
select[data-tbm-src] { display: none !important; }
.tbm-trigger { display: inline-block; text-align: left; white-space: nowrap; }
.tbm-lbl { display: block; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; text-align: left; padding: 4px 0; margin: -3.25px 0 -2.75px; pointer-events: none; }
.tbm-lbl::after { content: attr(data-w); display: block; height: 0; overflow: hidden; visibility: hidden; white-space: pre; }
@supports (width: calc-size(max-content, round(up, size, 1px))) { .tbm-lbl::after { width: calc-size(max-content, round(up, size, 1px)); } }
.tbm-trigger-open { border-color: var(--amber) !important; }
.tbm-panel {
  position: fixed; z-index: 5000; min-width: 180px; max-width: min(340px, calc(100vw - 16px));
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
.tbm-opt[aria-selected="true"] { color: var(--amber); }
.tbm-opt[aria-selected="true"]::before { content: ''; position: absolute; left: 0; top: 6px; bottom: 6px; width: 3px; background: var(--amber); }
.tbm-opt[aria-selected="true"] .tbm-mark { background: var(--amber); border-color: var(--amber); }
.tbm-opt[aria-disabled="true"] { color: var(--khaki); cursor: not-allowed; background: none; }
.tbm-opt[aria-disabled="true"] .tbm-mark { border-style: dashed; border-color: var(--khaki); background: none; }
.tbm-opt[aria-disabled="true"] .tbm-note { color: var(--khaki); font-size: 10px; letter-spacing: 1px; margin-left: auto; padding-left: 14px; }
@media (prefers-reduced-motion: reduce) { .tbm-panel { animation: none; } }
@media print { .tbm-panel { display: none; } }

/* ---------- Filtres de la liste des vols au thème de l'interface (lot mp-listes-filtres-themees) ----------
   Le bouton fermé garde la boîte et le texte du <select> du filtre ; seul le chevron est dessiné (12 × 8, trait 1,6 px, couleur du texte,
   à 12 px du bord droit, 8 px sur un champ de moins de 120 px). La liste ouverte garde la police du champ. */
.tbm-panel.tbm-p-field { max-width: calc(100vw - 16px); }
.tbm-panel.tbm-p-field .tbm-opt {
  font-family: var(--f-typewriter); font-weight: 400; font-size: 14px; letter-spacing: .2px; text-transform: none;
}
.tbm-panel.tbm-p-field .tbm-opt[aria-selected="true"] { font-weight: 400; }
.tbm-panel.tbm-up { border-top: 1px solid var(--amber-dark); border-bottom: 3px solid var(--amber); transform-origin: bottom left; }
.tb-lang-btn {
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
}
.tb-lang-btn:hover, .tb-lang-btn:focus-visible {
  background: var(--olive);
  border-color: var(--amber);
  outline: none;
}
/* Exemple (lot mp-exemples-demarrer) : bouton à icône seule, comme dans les autres outils */
.tb-btn {
  background: transparent;
  border: 1px solid var(--khaki);
  color: var(--paper);
  height: 36px;
  width: 40px;
  padding: 0;
  cursor: pointer;
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: all .15s;
}
.tb-btn:hover, .tb-btn:focus-visible {
  background: var(--olive);
  border-color: var(--amber);
  color: var(--amber);
  outline: none;
}
.tb-btn:active { transform: translateY(1px); }
.tb-btn svg { width: 16px; height: 16px; flex-shrink: 0; }
.tb-spacer { flex: 1; }
.tb-version {
  font-size: 11px;
  opacity: .45;
  color: var(--amber);
  letter-spacing: .5px;
  user-select: none;
  white-space: nowrap;
}
/* La barre ne déborde pas sur un téléphone étroit (lot mp-exemples-demarrer) */
@media (max-width: 539px) {
  .tb-version { display: none; }
}
@media (max-width: 479px) {
  .toolbar { gap: 6px; padding-left: max(8px, env(safe-area-inset-left)); padding-right: max(8px, env(safe-area-inset-right)); }
  .tb-brand { min-width: 0; }
  .tb-brand-sub, .tb-sep { display: none; }
  .tb-brand-main { font-size: 14px; letter-spacing: 2px; }
  .tb-btn { width: 36px; }
  .tb-select { font-size: 11px; letter-spacing: .5px; padding: 0 22px 0 8px; background-position: right 6px center; }
  .tb-select.tbm-trigger { min-width: 0; flex: 0 1 auto; }
  .tb-lang-btn { min-width: 36px; padding: 0 4px; }
}

/* ======== MAIN LAYOUT ======== */
.app {
  position: fixed;
  top: 56px; bottom: 0; left: 0; right: 0;
  overflow-y: auto;
  overscroll-behavior: contain;
  background: var(--olive-deep);
}

/* ======== EDITOR ======== */
.editor {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px 16px 80px 16px;
  color: var(--paper);
}
.editor::-webkit-scrollbar { width: 8px; }
.editor::-webkit-scrollbar-track { background: var(--olive-deep); }
.editor::-webkit-scrollbar-thumb { background: var(--khaki); border: 2px solid var(--olive-deep); }

/* ======== ED SECTION ======== */
.ed-section {
  contain: layout;
  margin-bottom: 14px;
  border: 1px solid var(--khaki);
  background: rgba(20,24,12,.5);
}
.ed-section > summary {
  cursor: pointer;
  padding: 12px 14px;
  background: linear-gradient(90deg, var(--olive) 0%, var(--olive-dark) 100%);
  font-family: var(--f-stencil);
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
  content: '\u25c4';
  font-size: 10px;
  color: var(--paper);
  transition: transform .2s;
}
.ed-section[open] > summary::after { transform: rotate(-90deg); }
.ed-section > summary:hover { color: var(--paper-light); }
.ed-content {
  padding: 14px;
  display: flex; flex-direction: column; gap: 14px;
}

/* FIELDS */
.ed-field { display: flex; flex-direction: column; gap: 5px; }
.ed-field label {
  font-family: var(--f-ui);
  font-weight: 700;
  font-size: 11px;
  letter-spacing: 1.8px;
  text-transform: uppercase;
  color: var(--amber);
  display: flex; align-items: center; gap: 6px;
}
.ed-field label::before { content: '\u25ba'; color: var(--rust); font-size: 8px; }
.ed-field input[type=text] {
  background: rgba(216,201,165,.92);
  border: 1px solid var(--khaki);
  border-left: 3px solid var(--amber-dark);
  font-family: var(--f-typewriter);
  font-size: 13px;
  color: var(--ink);
  padding: 10px 11px;
  min-height: 44px;
  transition: all .15s;
  width: 100%;
}
.ed-field input:focus {
  outline: none;
  border-left-color: var(--red-stamp);
  background: var(--paper-light);
  box-shadow: 0 0 0 1px var(--amber);
}
.ed-field-row { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }

/* BUTTONS */
.ed-btn-icon {
  background: var(--rust);
  border: 1px solid var(--red-faded);
  color: var(--paper-light);
  font-family: var(--f-ui);
  font-weight: 700;
  cursor: pointer;
  padding: 0 12px;
  transition: background .15s;
  font-size: 18px;
  line-height: 1;
  min-width: 44px;
  min-height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.ed-btn-icon:hover { background: var(--red-stamp); }
.ed-btn-icon.danger { background: var(--rust); }
.ed-btn-add {
  background: transparent;
  border: 1px dashed var(--amber);
  color: var(--amber);
  font-family: var(--f-ui);
  font-weight: 700;
  letter-spacing: 1.5px;
  padding: 12px;
  min-height: 44px;
  cursor: pointer;
  font-size: 12px;
  text-transform: uppercase;
  transition: all .15s;
}
.ed-btn-add:hover { background: var(--olive); color: var(--paper-light); }
.ed-btn-add-sm { padding: 6px 10px; min-height: 36px; font-size: 10px; }

.miz-btn {
  display: inline-flex; align-items: center; gap: 6px;
  font-family: var(--f-stencil); font-size: 12px;
  letter-spacing: .05em; padding: 9px 14px;
  border: 1px solid var(--khaki); border-radius: 3px;
  background: rgba(0,0,0,.2); color: var(--paper-light);
  cursor: pointer; transition: background .15s;
  text-transform: uppercase;
}
.miz-btn:hover { background: var(--olive); border-color: var(--amber); color: var(--amber); }
.miz-btn.primary { border-color: var(--amber); color: var(--amber); }
.miz-btn.primary:hover { background: var(--amber-dark); color: var(--paper-light); }
.miz-btn-row { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 10px; }
.miz-btn:disabled { opacity: .4; cursor: default; }
.miz-btn:disabled:hover { background: rgba(0,0,0,.2); border-color: var(--khaki); color: var(--paper-light); }
.miz-btn.primary:disabled:hover { border-color: var(--amber); color: var(--amber); }
/* ======== TOAST ======== */
.toast {
  position: fixed;
  bottom: 20px; left: 50%;
  transform: translateX(-50%) translateY(100px);
  background: var(--olive-dark);
  border: 1px solid var(--amber);
  color: var(--paper);
  font-family: var(--f-ui);
  font-weight: 500;
  letter-spacing: 2px;
  text-transform: uppercase;
  font-size: 12px;
  padding: 10px 20px;
  z-index: 2000;
  opacity: 0;
  transition: all .3s ease;
  pointer-events: none;
  box-shadow: 0 4px 16px rgba(0,0,0,.6);
  width: max-content; max-width: calc(100vw - 24px); text-align: center;
}
.toast.show {
  opacity: 1;
  transform: translateX(-50%) translateY(0);
}
.toast.act { pointer-events: auto; width: max-content; max-width: calc(100vw - 24px); text-align: center; }
.toast-action {
  background: none; border: 0; padding: 6px 4px; margin: -6px 0; cursor: pointer;
  font: inherit; letter-spacing: inherit; text-transform: inherit; color: var(--amber);
  text-decoration: underline; text-underline-offset: 3px;
}
.toast-action:hover, .toast-action:focus-visible { color: var(--paper-light); outline: none; }

.pk-chk {
  display: inline-flex; align-items: center; gap: 8px;
  font-family: var(--f-ui); font-size: 12px; letter-spacing: 1px; text-transform: uppercase;
  color: var(--paper); min-height: 34px; cursor: pointer;
}
.pk-chk input { accent-color: var(--amber); width: 18px; height: 18px; margin: 0; flex: none; }
.pk-chk.off { opacity: .4; cursor: default; }
.pk-chk.off input { cursor: default; }"""

# ---------- CSS propre au module ----------
CSS_FC = r"""
/* ======== FLIGHT CONFIGURATOR ======== */
/* L'accent du module : UNE variable (--fc, #D0784A, provisoire ; au shell, --a-fc). Il colore le bandeau, le bouton principal, le focus, les puces actives et le logo F·C. */
:root { --fc: #D0784A; }
body[data-theme] { --fc-dark: color-mix(in srgb, var(--fc) 62%, #000); --fc-dim: color-mix(in srgb, var(--fc) 26%, transparent); --pk-warn: var(--red-faded); --pk-ok: #7fa062; --cmp-frame: #1f1f1f; --cmp-strip: #151a1f; --amber-dim: rgba(192,137,42,.28); }
body[data-theme="cw-soviet"], body[data-theme="modern-nato"], body[data-theme="modern-east"] { --pk-warn: #e8b840; }  /* --red-faded y est trop sombre sur le fond de la page */

/* barre du haut : même méthode que HQ et le Datacard Generator (.tb-btn : icône, libellé long, libellé court, icône seule) */
.tb-btn { width: auto; height: 38px; min-width: 38px; padding: 0 12px; gap: 6px; font-family: var(--f-ui); font-weight: 500; letter-spacing: 1.5px; font-size: 12px; text-transform: uppercase; white-space: nowrap; }
.tb-btn .tb-short { display: none; }
.tb-btn:disabled { opacity: .4; cursor: default; }
.tb-btn:disabled:hover { background: transparent; border-color: var(--khaki); color: var(--paper); }
.tb-btn.danger:hover { background: var(--rust); border-color: var(--red-faded); color: var(--paper-light); }
.tb-brand-short { display: none; font-family: var(--f-stencil); font-size: 16px; font-weight: 700; letter-spacing: 3px; color: var(--amber); }
/* Seuils mesurés dans le shell (qui ajoute à la barre un bouton de retour de 40 ou 119 px) : libellé long dès 1040 px (le français est le plus large),
   libellé court de 900 à 1039 px, icône seule en dessous ; le titre complet seulement dès 1360 px */
@media (max-width: 1359px) { .tb-brand-main, .tb-brand-sub, .tb-sep { display: none; } .tb-brand-short { display: inline; } .tb-version { display: none; } }
@media (max-width: 1039px) { .tb-btn .tb-long { display: none; } .tb-btn .tb-short { display: inline; } .tb-btn { padding: 0 9px; letter-spacing: 1px; } .tb-select { max-width: 130px; } }
@media (max-width: 899px) { .tb-btn .tb-btn-label { display: none; } .tb-btn { padding: 0; width: 38px; } .tb-select { max-width: 110px; } }
@media (max-width: 539px) { .tb-brand-short { display: none; } .tb-select { max-width: 96px; } }
@media (max-width: 479px) { .toolbar { gap: 3px; } .tb-btn { width: 34px; min-width: 34px; } .tb-select { max-width: 64px; padding: 0 18px 0 6px; } .tb-lang-btn { min-width: 34px; padding: 0 2px; } }

/* l'état de l'export */
.fc-status { position: sticky; top: 0; z-index: 5; margin: 0 0 12px; padding: 7px 12px; font-family: var(--f-typewriter); font-size: 12px; line-height: 1.4; color: var(--paper-light); background: var(--olive-dark); border: 1px solid var(--khaki); border-left: 3px solid var(--pk-warn); word-break: break-word; }
.fc-status.ok { border-left-color: var(--pk-ok); color: var(--paper); }

.editor { max-width: 1840px; }
.ed-field input[type=text] { min-width: 0; }
.ed-field input[type=text].bad { border-color: var(--pk-warn); border-left-color: var(--pk-warn); }
.fc-cols { display: grid; grid-template-columns: minmax(0, 1fr); gap: 16px; align-items: start; }
@media (min-width: 1100px) { .fc-cols { grid-template-columns: minmax(0, 1fr) minmax(0, 1.12fr); } }
.fc-cols > * { min-width: 0; }
.fc-block { border: 1px solid var(--khaki); background: rgba(20,24,12,.5); }
#col-presets > .fc-block, #col-right > .fc-block + .fc-block { margin-top: 16px; }
.fc-bh { padding: 11px 14px; background: linear-gradient(90deg, var(--olive) 0%, var(--olive-dark) 100%); font-family: var(--f-stencil); font-size: 13px; letter-spacing: 2px; color: var(--amber); border-bottom: 1px solid var(--amber-dark); min-height: 44px; display: flex; align-items: center; gap: 6px; }
.fc-bh .fc-count { font-family: var(--f-typewriter); font-size: 12px; letter-spacing: 0; color: var(--paper); }
.fc-bc { padding: 14px; display: flex; flex-direction: column; gap: 12px; }
.fc-row { display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 10px; align-items: end; }
.fc-row > * { min-width: 0; }
.fc-row3 { display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 10px; }
.fc-row3 > * { min-width: 0; }
.fc-fname { font-family: var(--f-typewriter); font-size: 12px; color: var(--paper); min-height: 44px; display: flex; align-items: center; word-break: break-all; padding: 0 2px; }
.pk-note { font-family: var(--f-typewriter); font-size: 11px; color: var(--khaki-light); margin: 0; }
.pk-warn { font-family: var(--f-typewriter); font-size: 11px; color: var(--pk-warn); margin-top: 6px; word-break: break-word; }
.snap-flight-tag { font-family: var(--f-ui); font-size: 10px; padding: 2px 6px; border-radius: 2px; background: var(--olive); color: var(--paper-light); text-transform: uppercase; letter-spacing: 1px; white-space: nowrap; }
.pk-x { flex: none; min-width: 36px; min-height: 36px; background: none; border: 0; color: var(--khaki-light); font-size: 16px; cursor: pointer; }
.pk-x:hover, .pk-x:focus-visible { color: var(--amber); outline: none; }

/* listes des formulaires au thème de l'interface (même composant que la barre) */
.fc-sel.tbm-trigger.tbm-field {
  display: block; position: relative; contain: inline-size; text-align: left; letter-spacing: normal; text-transform: none; font-weight: 400;
  box-sizing: border-box; width: 100%; min-width: 0; min-height: 44px; padding: 0 34px 0 11px; margin: 0; cursor: pointer;
  font-family: var(--f-typewriter); font-size: 13px; line-height: 42px;
  background: rgba(216,201,165,.92); color: var(--ink);
  border: 1px solid var(--khaki); border-left: 3px solid var(--amber-dark); border-radius: 0;
}
.fc-sel.tbm-trigger.tbm-field::after {
  content: ''; position: absolute; right: 12px; top: 50%; width: 12px; height: 8px; margin-top: -4px; pointer-events: none;
  background: currentColor; -webkit-mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='8' viewBox='0 0 12 8'%3E%3Cpath d='M1 1.5l5 5 5-5' fill='none' stroke='%23000' stroke-width='1.6'/%3E%3C/svg%3E") center / 12px 8px no-repeat; mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='8' viewBox='0 0 12 8'%3E%3Cpath d='M1 1.5l5 5 5-5' fill='none' stroke='%23000' stroke-width='1.6'/%3E%3C/svg%3E") center / 12px 8px no-repeat;
}
.fc-sel.tbm-trigger.tbm-field .tbm-lbl { margin: 0; padding: 0; line-height: 42px; }
.fc-sel.tbm-trigger.tbm-field .tbm-lbl::after { display: none; }
/* une arme au nom long passe sur deux lignes au lieu d'être coupée ; dans la liste ouverte, elle passe à la ligne */
.cmp-row .fc-sel.tbm-trigger.tbm-field { display: flex; align-items: center; line-height: 1.25; padding-top: 5px; padding-bottom: 5px; min-height: 40px; }
.cmp-row .fc-sel.tbm-trigger.tbm-field .tbm-lbl { line-height: 1.25; white-space: normal; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; text-overflow: clip; }
.tbm-panel.tbm-p-field .tbm-opt { white-space: normal; line-height: 1.3; padding-top: 8px; padding-bottom: 8px; word-break: break-word; }
.fc-sel.tbm-trigger.tbm-field:focus { outline: none; border-left-color: var(--red-stamp); box-shadow: 0 0 0 1px var(--amber); }
.fc-sel.tbm-trigger.tbm-field:disabled { opacity: .5; cursor: default; }

/* un vol */
.fc-list { display: flex; flex-direction: column; gap: 12px; }
.fc-flight { border: 1px solid var(--khaki); border-radius: 3px; padding: 10px 12px 12px; background: rgba(0,0,0,.15); }
.fc-fhead, .fc-uhead { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin-bottom: 8px; }
.fc-fhead .pk-x, .fc-uhead .pk-x { margin-left: auto; margin-right: -8px; }
.fc-ftitle { font-family: var(--f-stencil); font-size: 13px; letter-spacing: 1.5px; color: var(--amber); text-transform: uppercase; word-break: break-word; min-width: 0; }
.fc-route { display: flex; align-items: center; gap: 8px 12px; flex-wrap: wrap; margin-top: 10px; padding: 6px 10px; border: 1px dashed rgba(128,116,84,.6); font-family: var(--f-typewriter); font-size: 12px; color: var(--paper); }
.fc-route.none { color: var(--khaki-light); border-color: rgba(128,116,84,.35); }
.fc-route-t { min-width: 0; word-break: break-word; flex: 1 1 200px; }
.fc-small { min-height: 36px; padding: 6px 12px; font-size: 11px; }
.fc-units { display: grid; grid-template-columns: minmax(0, 1fr); gap: 10px; margin-top: 12px; }
.fc-unit { border: 1px solid rgba(128,116,84,.55); border-left: 3px solid var(--amber-dark); padding: 8px 10px 10px; background: rgba(0,0,0,.12); }
.fc-unit.sel { border-left-color: var(--amber); background: rgba(192,137,42,.1); box-shadow: 0 0 0 1px rgba(192,137,42,.5); }
.fc-uhead { margin-bottom: 6px; }
.fc-utitle { font-family: var(--f-stencil); font-size: 12px; letter-spacing: 1px; color: var(--paper); text-transform: uppercase; }
.fc-row4 { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; }
.fc-row4 > * { min-width: 0; }
.fc-sub { margin-top: 10px; border-top: 1px solid rgba(128,116,84,.45); }
.fc-sub > summary { cursor: pointer; list-style: none; display: flex; align-items: center; gap: 8px; min-height: 40px; user-select: none; font-family: var(--f-stencil); font-size: 12px; letter-spacing: 1.5px; color: var(--amber); text-transform: uppercase; }
.fc-sub > summary::-webkit-details-marker { display: none; }
.fc-sub > summary::before { content: '\25ba'; font-size: 8px; color: var(--rust); transition: transform .2s; }
.fc-sub[open] > summary::before { transform: rotate(90deg); }
.fc-sub > summary .fc-sum { font-family: var(--f-typewriter); font-size: 11px; letter-spacing: 0; text-transform: none; color: var(--khaki-light); min-width: 0; word-break: break-word; }
.fc-sub > .fc-subc { padding: 2px 0 6px; display: flex; flex-direction: column; gap: 10px; }
.fc-posts { display: grid; grid-template-columns: minmax(0, 1fr); gap: 8px; }
.fc-post { border: 1px solid rgba(128,116,84,.4); background: rgba(0,0,0,.12); }
.fc-post > summary { cursor: pointer; list-style: none; display: flex; align-items: center; gap: 8px; min-height: 40px; padding: 0 10px; user-select: none; font-family: var(--f-ui); font-weight: 500; font-size: 12px; letter-spacing: 1px; color: var(--paper); text-transform: uppercase; }
.fc-post > summary::-webkit-details-marker { display: none; }
.fc-post > summary::after { content: '\25c4'; margin-left: auto; font-size: 10px; color: var(--paper); transition: transform .2s; }
.fc-post[open] > summary::after { transform: rotate(-90deg); }
.fc-post > summary .fc-sum { font-family: var(--f-typewriter); font-size: 11px; letter-spacing: 0; text-transform: none; color: var(--khaki-light); }
.fc-post > .fc-postc { padding: 4px 10px 10px; }
.fc-chans { display: grid; grid-template-columns: repeat(auto-fill, minmax(104px, 1fr)); gap: 6px 8px; }
.fc-ch { display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.fc-ch > label { font-family: var(--f-ui); font-size: 10px; letter-spacing: 1.2px; text-transform: uppercase; color: var(--khaki-light); }
.fc-ch input { background: rgba(216,201,165,.92); border: 1px solid var(--khaki); border-left: 3px solid var(--amber-dark); font-family: var(--f-typewriter); font-size: 13px; color: var(--ink); padding: 6px 8px; min-height: 40px; width: 100%; min-width: 0; border-radius: 0; }
.fc-ch input:focus { outline: none; border-left-color: var(--red-stamp); background: var(--paper-light); box-shadow: 0 0 0 1px var(--amber); }
.fc-ch input.bad { border-color: var(--pk-warn); border-left-color: var(--pk-warn); }
.fc-msg { font-family: var(--f-typewriter); font-size: 11px; color: var(--pk-warn); margin-top: 6px; word-break: break-word; }
.fc-msg:empty { display: none; }
.fc-lo-sum { display: flex; align-items: center; gap: 8px 12px; flex-wrap: wrap; margin-top: 10px; padding-top: 8px; border-top: 1px solid rgba(128,116,84,.45); }
.fc-lo-k { font-family: var(--f-stencil); font-size: 12px; letter-spacing: 1.5px; color: var(--amber); text-transform: uppercase; }
.fc-lo-v { font-family: var(--f-typewriter); font-size: 12px; color: var(--paper); flex: 1 1 160px; min-width: 0; word-break: break-word; }

/* l'emport : la vue de face de Mission Tools (Loadout Editor), reprise */
.cmp-top { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 10px; align-items: end; }
.cmp-top > * { min-width: 0; }
.cmp-for { font-family: var(--f-typewriter); font-size: 13px; color: var(--paper-light); word-break: break-word; display: flex; flex-wrap: wrap; gap: 4px 8px; align-items: center; }
.fc-lo-line { display: flex; flex-wrap: wrap; gap: 6px 10px; align-items: center; font-family: var(--f-typewriter); font-size: 11px; color: var(--khaki-light); }
#cmp-wrap { position: relative; }
.cmp-view { position: relative; background: var(--cmp-frame); padding: 14px 14px 34px; border-radius: 4px; }
.cmp-wrap-strip .cmp-view { border-radius: 4px 4px 0 0; }
.cmp-svgbox { position: relative; margin: 0 auto; width: min(100%, calc(52vh * var(--r))); }
.cmp-svgbox > svg { display: block; width: 100%; height: auto; }
.cmp-svgbox svg [stroke]:not([stroke="none"]) { stroke: var(--paper); }
.cmp-svgbox svg [fill="#ffffff"] { fill: var(--cmp-frame); }
.cmp-credit { position: absolute; right: 10px; bottom: 8px; max-width: 70%; font-family: var(--f-typewriter); font-size: 10px; line-height: 1.3; color: var(--khaki-light); background: var(--cmp-frame); padding: 0 4px; text-align: right; }
.cmp-num { position: absolute; transform: translate(-50%, 8px); min-width: 20px; text-align: center; font-family: var(--f-typewriter); font-size: 12px; line-height: 18px; color: var(--amber); background: var(--cmp-strip); border: 1px solid var(--amber); border-radius: 3px; padding: 0 3px; }
.cmp-num.sel { background: var(--amber); color: var(--olive-deep); }
#cmp-leads { position: absolute; inset: 0; width: 100%; height: 100%; pointer-events: none; z-index: 2; overflow: visible; }
#cmp-leads path { fill: none; stroke: var(--amber); stroke-width: 1.4; stroke-dasharray: 5 4; opacity: .9; }
#cmp-leads path.on { stroke-width: 2.4; opacity: 1; }
#cmp-leads circle { fill: #1b2228; stroke: var(--amber); stroke-width: 2; }
.cmp-strip { position: relative; height: 58px; background: var(--cmp-strip); border-top: 1px solid var(--khaki); border-radius: 0 0 4px 4px; }
.cmp-st { position: absolute; top: 6px; transform: translateX(-50%); width: calc(100% / var(--n) - 6px); min-width: 0; text-align: center; padding: 3px 2px; background: var(--cmp-frame); border: 1px solid var(--khaki); border-radius: 3px; cursor: pointer; z-index: 3; }
.cmp-st .n { display: block; font-family: var(--f-typewriter); font-size: 11px; color: var(--khaki-light); }
.cmp-st .w { display: block; font-family: var(--f-typewriter); font-size: 11px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; color: var(--paper-light); }
.cmp-st.sel { border-color: var(--amber); box-shadow: 0 0 0 2px var(--amber-dim); }
.cmp-st.sel .n { color: var(--amber); }
.cmp-st:focus-visible { outline: 2px solid var(--amber); outline-offset: 1px; }
.cmp-wrap-flat .cmp-view { padding-bottom: 8px; }
.cmp-wrap-flat .cmp-svgbox { margin-bottom: 46px; }
.cmp-wrap-flat .cmp-credit { position: static; max-width: none; padding: 0; margin-top: 6px; }
.cmp-list { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 4px 20px; }
.cmp-row { display: grid; grid-template-columns: 24px minmax(0, 1fr) auto 62px; align-items: center; gap: 8px; padding: 3px 6px; border-radius: 4px; }
.cmp-row.sel { background: var(--amber-dim); }
.cmp-row .sn { font-family: var(--f-typewriter); font-size: 13px; color: var(--khaki-light); }
.cmp-row.sel .sn { color: var(--amber); }
.cmp-row .pair { font-family: var(--f-typewriter); font-size: 12px; color: var(--khaki-light); white-space: nowrap; }
.cmp-row .cmp-kg { text-align: right; font-family: var(--f-typewriter); font-size: 12px; color: var(--paper); white-space: nowrap; }
.cmp-foot { display: flex; align-items: center; flex-wrap: wrap; gap: 8px 18px; padding-top: 4px; }
.cmp-tot { font-family: var(--f-typewriter); font-size: 12px; color: var(--khaki-light); }
.cmp-tot b { color: var(--paper-light); white-space: nowrap; }
.pk-chk { display: inline-flex; align-items: center; gap: 8px; min-height: 36px; cursor: pointer; font-family: var(--f-typewriter); font-size: 12px; }
.fc-chip { font-family: var(--f-ui); font-size: 10px; letter-spacing: 1px; text-transform: uppercase; padding: 1px 6px; border: 1px solid var(--khaki); color: var(--khaki-light); white-space: nowrap; }
.fc-set { display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 8px; }
.fc-set > * { min-width: 0; }
.fc-set .ed-field label { font-size: 10px; letter-spacing: 1.2px; }
.fc-actions .miz-btn { min-height: 44px; width: 100%; justify-content: center; }
.fc-editor { border: 1px solid var(--amber); border-top: 3px solid var(--amber); background: var(--olive-dark); padding: 12px; display: flex; flex-direction: column; gap: 10px; }
.fc-pvfile { font-family: var(--f-typewriter); font-size: 12px; color: var(--khaki-light); word-break: break-all; }
.fc-pvfile #pv-file { color: var(--paper); }
.fc-pre { margin: 0; max-height: 380px; overflow: auto; padding: 10px 12px; background: var(--cmp-strip); border: 1px solid rgba(128,116,84,.5); font-family: var(--f-typewriter); font-size: 11px; line-height: 1.45; color: var(--paper); white-space: pre; tab-size: 2; }

/* les presets */
.fc-lib { display: flex; flex-direction: column; gap: 6px; }
.fc-file { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; border: 1px solid rgba(128,116,84,.45); padding: 4px 4px 4px 10px; background: rgba(0,0,0,.12); min-height: 44px; }
.fc-file-n { font-family: var(--f-typewriter); font-size: 12px; color: var(--paper); word-break: break-all; min-width: 0; }
.fc-file .pk-x { margin-left: auto; }
.fc-h { font-family: var(--f-stencil); font-size: 11px; letter-spacing: 2px; text-transform: uppercase; color: var(--amber); padding: 8px 0 2px; border-bottom: 1px solid var(--khaki); margin-bottom: 4px; }
.miz-btn { min-height: 44px; }
.miz-btn.fc-small { min-height: 36px; }

/* la fenêtre d'import (même gabarit que celle du Datacard Generator, aux couleurs de l'interface) */
.export-modal[hidden] { display: none !important; }
.export-modal { position: fixed; inset: 0; z-index: 10000; display: flex; align-items: center; justify-content: center; padding: 16px; }
.export-modal-backdrop { position: absolute; inset: 0; background: rgba(0,0,0,.6); }
.export-modal-panel { position: relative; background: var(--olive-dark); color: var(--paper); border: 2px solid var(--khaki); border-top: 3px solid var(--amber); border-radius: 3px; padding: 22px 26px; max-width: 640px; width: 100%; max-height: 92vh; overflow-y: auto; box-shadow: 0 8px 40px rgba(0,0,0,.6); font-family: var(--f-typewriter); }
.export-modal-close { position: absolute; top: 6px; right: 10px; min-width: 40px; min-height: 40px; background: none; border: none; color: var(--paper); font-size: 24px; line-height: 1; cursor: pointer; }
.export-modal-close:hover { color: var(--amber); }
.export-modal h2 { font-family: var(--f-stencil); font-weight: 700; font-size: 18px; letter-spacing: 2px; margin: 0 36px 14px 0; text-transform: uppercase; color: var(--amber); }
.imp-block { margin-bottom: 14px; }
.imp-block h3 { font-family: var(--f-stencil); font-weight: 700; font-size: 13px; letter-spacing: 2px; margin: 0 0 8px; color: var(--paper-light); text-transform: uppercase; }
.imp-src { display: flex; align-items: center; gap: 10px; min-height: 40px; font-size: 13px; cursor: pointer; }
.imp-src.off { opacity: .5; cursor: not-allowed; }
.imp-src input { accent-color: var(--amber); width: 18px; height: 18px; flex: none; }
.imp-note { font-size: 11px; color: var(--khaki-light); margin: 0 0 6px 28px; line-height: 1.35; word-break: break-word; }
.imp-file { display: flex; align-items: center; gap: 10px; margin: 2px 0 4px 28px; font-size: 11px; flex-wrap: wrap; }
.imp-filebtn { background: transparent; border: 1px solid var(--khaki); padding: 6px 12px; min-height: 36px; font-family: inherit; font-size: 11px; cursor: pointer; color: var(--paper); border-radius: 2px; }
.imp-filebtn:hover, .imp-filebtn:focus-visible { background: var(--olive); border-color: var(--amber); outline: none; }
.imp-filename { color: var(--khaki-light); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 100%; }
.imp-list { max-height: 300px; overflow-y: auto; border: 1px solid rgba(128,116,84,.5); padding: 4px 10px; background: rgba(0,0,0,.18); }
.imp-flight { padding: 6px 0; }
.imp-flight + .imp-flight { border-top: 1px dashed rgba(128,116,84,.5); }
.imp-flight.off { opacity: .55; }
.imp-fh { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; min-height: 36px; font-size: 13px; cursor: pointer; }
.imp-fh input { accent-color: var(--amber); width: 18px; height: 18px; flex: none; }
.imp-nm { font-family: var(--f-stencil); letter-spacing: 1px; min-width: 0; overflow-wrap: anywhere; }
.imp-n { font-size: 11px; color: var(--khaki-light); margin-left: auto; text-align: right; }
.pk-parts { display: flex; flex-wrap: wrap; gap: 4px 14px; margin: 0 0 2px 26px; }
.pk-chk input { accent-color: var(--amber); width: 18px; height: 18px; margin: 0; flex: none; }
.pk-chk.off { opacity: .4; cursor: default; }
.imp-actions { display: flex; justify-content: space-between; gap: 10px; margin-top: 8px; }
.imp-btn { background: transparent; border: 2px solid var(--khaki); padding: 8px 18px; min-height: 44px; font-family: var(--f-stencil); font-weight: 700; letter-spacing: 2px; font-size: 13px; cursor: pointer; color: var(--paper); border-radius: 2px; text-transform: uppercase; }
.imp-btn:hover { background: var(--olive); }
.imp-btn.go { background: var(--amber-dark); border-color: var(--amber); color: var(--paper-light); }
.imp-btn:disabled { opacity: .4; cursor: not-allowed; pointer-events: none; }

@media (max-width: 539px) {
  .editor { padding: 10px 8px 80px 8px; }
  .fc-bc { padding: 10px; }
  .fc-flight { padding: 8px 8px 10px; }
  .fc-unit { padding: 6px 8px 8px; }
  .fc-chans { grid-template-columns: repeat(auto-fill, minmax(92px, 1fr)); }
  .cmp-list { grid-template-columns: minmax(0, 1fr); }
  .cmp-row { grid-template-columns: 22px minmax(0, 1fr) auto 56px; gap: 6px; padding: 3px 0; }
  .miz-btn-row .miz-btn { flex: 1 1 100%; justify-content: center; }
  .export-modal-panel { padding: 16px 14px; }
  .imp-n { margin-left: 0; text-align: left; width: 100%; }
  .imp-actions .imp-btn { flex: 1; padding: 8px 10px; }
}

/* L'accent (--fc) : bordure du bandeau, bouton principal, focus, puces actives, logo F·C */
.toolbar { border-bottom-color: var(--fc); }
.tb-brand-main, .tb-brand-short { color: var(--fc); }
.tb-btn:hover, .tb-btn:focus-visible, .tb-lang-btn:hover, .tb-lang-btn:focus-visible { border-color: var(--fc); }
.tb-btn:hover, .tb-btn:focus-visible { color: var(--fc); }
.miz-btn.primary { border-color: var(--fc); color: var(--fc); }
.miz-btn.primary:hover { background: var(--fc-dark); color: var(--paper-light); }
.miz-btn.primary:disabled:hover { background: rgba(0,0,0,.2); border-color: var(--fc); color: var(--fc); }
.fc-sel.tbm-trigger.tbm-field:focus, .fc-ch input:focus { box-shadow: 0 0 0 1px var(--fc); }
.cmp-st:focus-visible { outline-color: var(--fc); }
.fc-bh { border-bottom-color: var(--fc); }
.fc-unit.sel { border-left-color: var(--fc); background: var(--fc-dim); box-shadow: 0 0 0 1px var(--fc); }
.cmp-num { color: var(--fc); border-color: var(--fc); }
.cmp-num.sel { background: var(--fc); color: var(--olive-deep); }
#cmp-leads path, #cmp-leads circle { stroke: var(--fc); }
.cmp-st.sel { border-color: var(--fc); box-shadow: 0 0 0 2px var(--fc-dim); }
.cmp-st.sel .n, .cmp-row.sel .sn { color: var(--fc); }
.cmp-row.sel { background: var(--fc-dim); }
.fc-editor, .export-modal-panel { border-color: var(--fc); }
.pk-chk input, .imp-src input, .imp-fh input { accent-color: var(--fc); }
.imp-filebtn:hover, .imp-filebtn:focus-visible { border-color: var(--fc); }
.imp-btn.go { background: var(--fc-dark); border-color: var(--fc); }
.fc-status.ok { border-left-color: var(--fc); }

/* R295 : une seule graisse par police embarquée (Oswald 500, Roboto Mono 400, Stardos Stencil 700) */
.ed-field label, .ed-btn-icon, .ed-btn-add { font-weight: 500; }
b, strong { font-weight: 400; }
"""

# ---------- Corps de la page ----------
def _icon(d):
    return '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + d + '</svg>'


def _btn(bid, key, icon, extra=''):
    return ('<button type="button" class="tb-btn%s" id="btn-%s" data-i18n-title="tb.%s.tip" title="">%s'
            '<span class="tb-btn-label"><span class="tb-long" data-i18n="tb.%s">.</span><span class="tb-short" data-i18n="tb.%s.s">.</span></span></button>'
            % (extra, bid, key, _icon(icon), key, key))


BODY = r"""
<body data-theme="cw-nato">

<!-- TOOLBAR -->
<header class="toolbar" role="toolbar" aria-label="Flight Configurator">
  <div class="tb-brand">
    <span class="tb-brand-main">FLIGHT CONFIGURATOR</span>
    <span class="tb-brand-short">F·C</span>
    <span class="tb-brand-sub" data-i18n="toolbar.subtitle">░ PAQUET DE VOL</span>
  </div>
  <div class="tb-sep"></div>
  @@BUTTONS@@
  <div class="tb-sep"></div>
  <select class="tb-select" id="theme-select" data-i18n-title="toolbar.theme.tooltip" title="Thème graphique">
    <option value="cw-nato"     data-i18n="theme.cw-nato">Cold War OTAN</option>
    <option value="cw-soviet"   data-i18n="theme.cw-soviet">Cold War Soviétique</option>
    <option value="modern-nato" data-i18n="theme.modern-nato">OTAN moderne</option>
    <option value="modern-east" data-i18n="theme.modern-east">Bloc Est moderne</option>
  </select>
  <button class="tb-lang-btn" id="btn-lang" title="Switch language / Changer de langue">🇬🇧</button>
  <div class="tb-spacer"></div>
  <span class="tb-version">v@@VERSION@@</span>
</header>

<!-- MAIN APP -->
<div class="app" id="app">
  <div class="editor" id="editor-panel">
    <div class="fc-status" id="fc-status" role="status" aria-live="polite"></div>
    <div class="fc-cols">
      <div id="col-left"><div id="col-flights"></div><div id="col-presets"></div></div>
      <div id="col-right"></div>
    </div>
  </div>
</div>

<!-- FENÊTRE D'IMPORT -->
<div class="export-modal" id="imp-modal" hidden role="dialog" aria-modal="true" aria-labelledby="imp-modal-title">
  <div class="export-modal-backdrop" id="imp-modal-backdrop"></div>
  <div class="export-modal-panel">
    <button type="button" class="export-modal-close" id="imp-modal-close" data-i18n-title="imp.close" title="Fermer" aria-label="Fermer">×</button>
    <h2 id="imp-modal-title" data-i18n="imp.title">Importer dans le module</h2>
    <div id="imp-body"></div>
    <div class="imp-actions">
      <button type="button" class="imp-btn" id="imp-cancel" data-i18n="imp.cancel">Annuler</button>
      <button type="button" class="imp-btn go" id="imp-go" data-i18n="imp.go" disabled>Importer</button>
    </div>
  </div>
</div>

<input type="file" id="fc-in-lua" accept=".lua,text/plain" multiple hidden>
<input type="file" id="fc-in-open" accept=".json,application/json" hidden>
<input type="file" id="fc-in-pkg" accept=".json,.zip,application/json,application/zip" hidden>
<input type="file" id="fc-in-snap" accept=".json,application/json" hidden>
<div class="toast" id="toast" role="status" aria-live="polite"></div>
"""

BUTTONS = '\n  '.join([
    _btn('open', 'open', '<path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v1H3z"/><path d="M3 10h19l-2 8a2 2 0 0 1-2 1.5H5a2 2 0 0 1-2-2z"/>'),
    _btn('save', 'save', '<path d="M5 3h11l4 4v13a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1z"/><path d="M8 3v5h7V3"/><rect x="7" y="13" width="10" height="8"/>'),
    _btn('import', 'import', '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>'),
    _btn('export', 'export', '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>'),
    _btn('clear', 'clear', '<polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/><path d="M10 11v6M14 11v6"/><path d="M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/>', ' danger'),
])
BODY = BODY.replace('@@BUTTONS@@', BUTTONS)

# ---------- Listes au thème de l'interface (copie du composant de HQ) ----------
JS_TBM = """
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
"""

# ---------- Script du module ----------
JS_FC = r"""
// =============================================================
//  FLIGHT CONFIGURATOR — maquette 2 (lot A) : le module en ébauche jetable ; tout est réel sauf ce que le rapport dit
// =============================================================
const I18N = {
  fr: {
    'toolbar.subtitle': '░ PAQUET DE VOL',
    'toolbar.theme.tooltip': 'Thème graphique',
    'toolbar.lang.tooltip': 'Changer de langue / Switch language',
    'theme.cw-nato': 'Cold War OTAN', 'theme.cw-soviet': 'Cold War Soviétique', 'theme.modern-nato': 'OTAN moderne', 'theme.modern-east': 'Bloc Est moderne',
    'tb.open': 'Ouvrir', 'tb.open.s': 'Ouvrir', 'tb.open.tip': 'Ouvrir un fichier de travail (JSON) : remplace le contenu du module',
    'tb.save': 'Enregistrer', 'tb.save.s': 'Enreg.', 'tb.save.tip': 'Enregistrer le travail en cours (JSON : le paquet et les réglages du module)',
    'tb.import': 'Importer', 'tb.import.s': 'Import.', 'tb.import.tip': 'Importer des vols, des routes, des radios, des emports depuis la mission de HQ, un paquet de vol ou un snapshot',
    'tb.export': 'Exporter', 'tb.export.s': 'Export.', 'tb.export.tip': 'Exporter le paquet de vol pour le Mission Commander',
    'tb.clear': 'Effacer', 'tb.clear.s': 'Effacer', 'tb.clear.tip': 'Vider le module (les presets gardés restent)',
    'bar.ok': 'Prêt à exporter : {0}',
    'bar.no.theatre': 'Export impossible : choisissez un théâtre (liste « Théâtre », ou importez un paquet).',
    'bar.no.flight': 'Export impossible : ajoutez au moins un vol.',
    'bar.no.name': 'Export impossible : le vol {0} n’a pas de nom.',
    'bar.bad.freq': 'Export impossible : {0} fréquence(s) à corriger dans les radios.',
    'bar.bad.set': 'Export impossible : vol {0}, unité {1} — {2}',
    'pkg.theatre': 'Théâtre', 'pkg.theatre.none': '— à choisir —',
    'pkg.fname': 'Fichier exporté',
    'sec.flights': 'VOLS',
    'sec.cmp': 'EMPORT',
    'sec.presets': 'PRESETS D’EMPORT',
    'sec.preview': 'APERÇU DU PAQUET',
    'fl.title': 'Vol {0}',
    'fl.add': '+ Ajouter un vol',
    'fl.remove': 'Retirer ce vol',
    'fl.empty': 'Aucun vol. Ajoutez-en un, ou importez-en depuis la barre du haut.',
    'fl.name': 'Nom du groupe', 'fl.name.ph': 'Hind 1',
    'fl.type': 'Appareil',
    'fl.coalition': 'Coalition', 'fl.coalition.any': '— non renseignée —', 'fl.coalition.blue': 'Bleue (OTAN)', 'fl.coalition.red': 'Rouge',
    'fl.units.one': '{0} unité', 'fl.units.many': '{0} unités',
    'route.none': 'Aucune route.',
    'route.n': 'Route : {0} points, de « {1} » à « {2} »',
    'route.n1': 'Route : 1 point, « {0} »',
    'route.alt': ' (premier point à {0} m)',
    'route.rm': 'Retirer la route',
    'route.note': 'La route vient d’un import ; elle repart telle quelle. Le tracé se fait dans le Route Planner.',
    'u.title': 'Unité {0}', 'u.add': '+ Ajouter une unité ({0}/4)', 'u.remove': 'Retirer cette unité',
    'u.name': 'Nom', 'u.callsign': 'Indicatif', 'u.onboard': 'N° de bord', 'u.livery': 'Livrée', 'u.livery.ph': 'texte libre',
    'u.opt': 'facultatif',
    'u.radios': 'Radios', 'u.radios.sum': '{0} postes', 'u.radios.set': '{0} canaux réglés',
    'u.loadout': 'Emport', 'u.loadout.none': 'non renseigné — HQ n’y touchera pas',
    'u.compose': 'Composer l’emport',
    'rad.chans': '{0} canaux', 'rad.ch': 'CH {0}',
    'rad.hint': 'Fréquences en MHz (virgule ou point). Les modulations ne sont pas écrites. Un canal vide n’est pas écrit.',
    'rad.copy': 'Recopier sur les autres unités du vol',
    'rad.err.nan': 'Canal {0} : « {1} » n’est pas une fréquence.',
    'rad.err.band': 'Canal {0} : {1} MHz hors de la bande du poste ({2} – {3} MHz).',
    'rad.err.more': ' (+ {0} autre(s))',
    'cmp.for': '{0} · {1}',
    'cmp.from': 'Partir de',
    'cmp.from.none': '— non renseigné —',
    'cmp.from.empty': 'Vide (poser des armes)',
    'cmp.from.imp': 'Emport importé',
    'cmp.none': '— vide —',
    'cmp.offTable': '(hors table)',
    'cmp.sym': 'Symétrique',
    'cmp.mass': 'Masse des emports :',
    'lo.pylon': 'Station {0}',
    'cmp.credit': 'Illustration : Goldwolf, DCS Reference Guide — avec son accord',
    'cmp.noview': 'Pas de vue de face pour ce type : la liste des stations.',
    'cmp.pick': 'Choisissez un vol et une unité : l’emport se compose ici.',
    'cmp.mod': 'modifié',
    'cmp.custom': 'Emport composé',
    'cmp.settings': 'réglages',
    'cmp.save': 'Enregistrer comme preset…', 'cmp.save.name': 'Nom du preset', 'cmp.save.go': 'Enregistrer', 'cmp.save.cancel': 'Annuler',
    'cmp.save.ph': 'Patrouille AT',
    'cmp.save.err.name': 'Donnez un nom au preset.',
    'cmp.save.err.dup': 'Un preset de ce nom existe déjà pour le {0}.',
    'cmp.save.err.none': 'Aucune arme posée : rien à enregistrer.',
    'cmp.save.ok': 'Preset « {0} » gardé dans « mes presets ».',
    'cmp.clear': 'Vider l’emport',
    'cmp.note': 'Un réglage d’arme (code laser, fusée…) suit sa station tant que l’arme n’est pas changée. Modifier une station ne demande pas de nommer un preset.',
    'lo.fuel': 'Carburant (kg)', 'lo.flare': 'Leurres', 'lo.chaff': 'Paillettes', 'lo.gun': 'Canon (%)',
    'lo.max': 'max {0}',
    'lo.err.range': '{0} : valeur hors plage (0 – {1}).',
    'lo.err.lure': 'Leurres et paillettes dépassent la capacité des distributeurs ({0}).',
    'lo.imported': 'emport importé',
    'lo.src.file': 'fichier {0}', 'lo.src.mine': 'mes presets', 'lo.src.imp': 'import',
    'pr.load': 'Charger des presets (.lua)',
    'pr.hint': 'Les fichiers UnitPayloads de l’éditeur de DCS (un par appareil) : leurs presets s’offrent dans « Partir de ». Rien n’est modifié ni envoyé.',
    'pr.files': 'Fichiers chargés ({0})',
    'pr.file.ok': '{0} · {1} presets', 'pr.file.unsup': '{0} · type non géré',
    'pr.err': '{0} : illisible — ligne {1} ({2})',
    'pr.mine': 'Mes presets ({0})',
    'pr.none': 'Aucun preset. Chargez un fichier, ou composez un emport et enregistrez-le.',
    'pr.delete': 'Retirer',
    'pr.export': 'Exporter {0}.lua',
    'pr.export.hint': 'Le fichier .lua réunit les presets du fichier chargé et les vôtres, au format de l’éditeur : déposez-le dans UnitPayloads (il remplace le fichier du même nom).',
    'err.code.': 'erreur',
    'err.code.unterminated-comment': 'commentaire non fermé', 'err.code.unterminated-string': 'chaîne non fermée',
    'err.code.unexpected-character': 'caractère inattendu', 'err.code.unexpected-eof': 'fin de fichier inattendue',
    'err.code.unexpected-token': 'élément inattendu', 'err.code.bad-structure': 'structure inattendue',
    'pv.file': 'Fichier exporté :',
    'pv.empty': 'Rien à exporter pour l’instant.',
    'pv.points': '{0} points, repris tels quels',
    'imp.title': 'Importer dans le module',
    'imp.src': 'Source',
    'imp.src.hq': 'Mission chargée dans HQ',
    'imp.src.pkg': 'Paquet de vol',
    'imp.src.snap': 'Fichier snapshot',
    'imp.src.rp': 'Route Planner', 'imp.src.bg': 'Briefing Generator', 'imp.src.dg': 'Datacard Generator',
    'imp.soon': 'Pas encore branché : prochain lot.',
    'imp.hq.none': 'Aucune mission dans HQ : chargez-en une dans HQ (même navigateur).',
    'imp.hq.ok': '{0} · théâtre {1}',
    'imp.choose': 'Choisir un fichier…',
    'imp.pkg.note': 'Un paquet .json ou .zip (exporté par HQ, le Route Planner ou ce module).',
    'imp.snap.note': 'Le _snapshot.json écrit par HQ.',
    'imp.flights': 'Vols à importer',
    'imp.none': 'Choisissez une source.',
    'imp.part.route': 'Route', 'imp.part.radios': 'Radios', 'imp.part.loadout': 'Emport', 'imp.part.livery': 'Livrée',
    'imp.new': 'nouveau vol', 'imp.exists': 'complète le vol du module',
    'imp.unsupported': 'appareil non géré',
    'imp.units': '{0} unité(s)',
    'imp.theatre.keep': 'Le théâtre du module ({0}) est conservé ; celui de la source est {1}.',
    'imp.theatre.set': 'Le théâtre deviendra {0}.',
    'imp.cancel': 'Annuler', 'imp.go': 'Importer', 'imp.close': 'Fermer',
    'imp.done': '{0} vol(s) importé(s).',
    'rej.json': 'Fichier illisible : ce n’est pas du JSON.',
    'rej.zip': 'Archive illisible : pas de package.json à la racine.',
    'rej.noTheatre': 'Le paquet n’a pas de théâtre.',
    'rej.noFlight': 'Aucun vol lisible dans ce fichier.',
    'rej.format': 'Format « {0} » non reconnu ici (attendu : {1}).',
    'rej.unknown': 'inconnu',
    'rej.skip': '{0} vol(s) illisible(s) ignoré(s).',
    'fmt.pkg': 'paquet de vol', 'fmt.snap': 'snapshot de HQ', 'fmt.work': 'fichier de travail',
    'open.bad': 'Ce fichier n’est pas un fichier de travail ni un paquet de vol.',
    'open.done': 'Fichier ouvert : {0} vol(s).',
    'clear.confirm': 'Vider le module ? Les vols, la route et l’emport en cours sont perdus (vos presets gardés restent).',
    'save.done': 'Travail enregistré : {0}',
    'export.done': 'Paquet exporté : {0}',
    'about.credit': 'Dessins des vues de face : Goldwolf (DCS Reference Guide), avec son accord, hors licence du dépôt. Tables d’armes : pydcs, LGPL-3.0.'
  },
  en: {
    'toolbar.subtitle': '░ FLIGHT PACKAGE',
    'toolbar.theme.tooltip': 'Graphic theme',
    'toolbar.lang.tooltip': 'Switch language / Changer de langue',
    'theme.cw-nato': 'Cold War NATO', 'theme.cw-soviet': 'Cold War Soviet', 'theme.modern-nato': 'Modern NATO', 'theme.modern-east': 'Modern Eastern Bloc',
    'tb.open': 'Open', 'tb.open.s': 'Open', 'tb.open.tip': 'Open a working file (JSON): replaces the module content',
    'tb.save': 'Save', 'tb.save.s': 'Save', 'tb.save.tip': 'Save the work in progress (JSON: the package and the module settings)',
    'tb.import': 'Import', 'tb.import.s': 'Import', 'tb.import.tip': 'Import flights, routes, radios, loadouts from the mission loaded in HQ, a flight package or a snapshot',
    'tb.export': 'Export', 'tb.export.s': 'Export', 'tb.export.tip': 'Export the flight package for the Mission Commander',
    'tb.clear': 'Clear', 'tb.clear.s': 'Clear', 'tb.clear.tip': 'Empty the module (kept presets stay)',
    'bar.ok': 'Ready to export: {0}',
    'bar.no.theatre': 'Cannot export: choose a theatre (the “Theatre” list, or import a package).',
    'bar.no.flight': 'Cannot export: add at least one flight.',
    'bar.no.name': 'Cannot export: flight {0} has no name.',
    'bar.bad.freq': 'Cannot export: {0} frequency(ies) to fix in the radios.',
    'bar.bad.set': 'Cannot export: flight {0}, unit {1} — {2}',
    'pkg.theatre': 'Theatre', 'pkg.theatre.none': '— to choose —',
    'pkg.fname': 'Exported file',
    'sec.flights': 'FLIGHTS',
    'sec.cmp': 'LOADOUT',
    'sec.presets': 'LOADOUT PRESETS',
    'sec.preview': 'PACKAGE PREVIEW',
    'fl.title': 'Flight {0}',
    'fl.add': '+ Add a flight',
    'fl.remove': 'Remove this flight',
    'fl.empty': 'No flight. Add one, or import some from the top bar.',
    'fl.name': 'Group name', 'fl.name.ph': 'Hind 1',
    'fl.type': 'Aircraft',
    'fl.coalition': 'Coalition', 'fl.coalition.any': '— not set —', 'fl.coalition.blue': 'Blue (NATO)', 'fl.coalition.red': 'Red',
    'fl.units.one': '{0} unit', 'fl.units.many': '{0} units',
    'route.none': 'No route.',
    'route.n': 'Route: {0} points, from “{1}” to “{2}”',
    'route.n1': 'Route: 1 point, “{0}”',
    'route.alt': ' (first point at {0} m)',
    'route.rm': 'Remove the route',
    'route.note': 'The route comes from an import and is written back as is. Drawing is done in the Route Planner.',
    'u.title': 'Unit {0}', 'u.add': '+ Add a unit ({0}/4)', 'u.remove': 'Remove this unit',
    'u.name': 'Name', 'u.callsign': 'Callsign', 'u.onboard': 'Onboard no.', 'u.livery': 'Livery', 'u.livery.ph': 'free text',
    'u.opt': 'optional',
    'u.radios': 'Radios', 'u.radios.sum': '{0} radios', 'u.radios.set': '{0} channels set',
    'u.loadout': 'Loadout', 'u.loadout.none': 'not set — HQ will not touch it',
    'u.compose': 'Compose the loadout',
    'rad.chans': '{0} channels', 'rad.ch': 'CH {0}',
    'rad.hint': 'Frequencies in MHz (comma or dot). Modulations are not written. An empty channel is not written.',
    'rad.copy': 'Copy to the other units of the flight',
    'rad.err.nan': 'Channel {0}: “{1}” is not a frequency.',
    'rad.err.band': 'Channel {0}: {1} MHz is outside the radio band ({2} – {3} MHz).',
    'rad.err.more': ' (+ {0} more)',
    'cmp.for': '{0} · {1}',
    'cmp.from': 'Start from',
    'cmp.from.none': '— not set —',
    'cmp.from.empty': 'Empty (place weapons)',
    'cmp.from.imp': 'Imported loadout',
    'cmp.none': '— empty —',
    'cmp.offTable': '(not in table)',
    'cmp.sym': 'Symmetric',
    'cmp.mass': 'Loadout weight:',
    'lo.pylon': 'Station {0}',
    'cmp.credit': 'Illustration: Goldwolf, DCS Reference Guide — used with permission',
    'cmp.noview': 'No front view for this type: the station list.',
    'cmp.pick': 'Pick a flight and a unit: the loadout is composed here.',
    'cmp.mod': 'modified',
    'cmp.custom': 'Composed loadout',
    'cmp.settings': 'settings',
    'cmp.save': 'Save as a preset…', 'cmp.save.name': 'Preset name', 'cmp.save.go': 'Save', 'cmp.save.cancel': 'Cancel',
    'cmp.save.ph': 'AT patrol',
    'cmp.save.err.name': 'Give the preset a name.',
    'cmp.save.err.dup': 'A preset with this name already exists for the {0}.',
    'cmp.save.err.none': 'No weapon placed: nothing to save.',
    'cmp.save.ok': 'Preset “{0}” kept in “my presets”.',
    'cmp.clear': 'Empty the loadout',
    'cmp.note': 'A weapon setting (laser code, fuze…) follows its station as long as the weapon is not changed. Changing a station does not require naming a preset.',
    'lo.fuel': 'Fuel (kg)', 'lo.flare': 'Flares', 'lo.chaff': 'Chaff', 'lo.gun': 'Gun (%)',
    'lo.max': 'max {0}',
    'lo.err.range': '{0}: value out of range (0 – {1}).',
    'lo.err.lure': 'Flares and chaff exceed the dispenser capacity ({0}).',
    'lo.imported': 'imported loadout',
    'lo.src.file': 'file {0}', 'lo.src.mine': 'my presets', 'lo.src.imp': 'import',
    'pr.load': 'Load presets (.lua)',
    'pr.hint': 'The UnitPayloads files of the DCS editor (one per aircraft): their presets are offered in “Start from”. Nothing is modified or sent.',
    'pr.files': 'Loaded files ({0})',
    'pr.file.ok': '{0} · {1} presets', 'pr.file.unsup': '{0} · type not handled',
    'pr.err': '{0}: unreadable — line {1} ({2})',
    'pr.mine': 'My presets ({0})',
    'pr.none': 'No preset. Load a file, or compose a loadout and save it.',
    'pr.delete': 'Remove',
    'pr.export': 'Export {0}.lua',
    'pr.export.hint': 'The .lua file merges the presets of the loaded file and yours, in the editor’s format: drop it into UnitPayloads (it replaces the file of the same name).',
    'err.code.': 'error',
    'err.code.unterminated-comment': 'unclosed comment', 'err.code.unterminated-string': 'unclosed string',
    'err.code.unexpected-character': 'unexpected character', 'err.code.unexpected-eof': 'unexpected end of file',
    'err.code.unexpected-token': 'unexpected token', 'err.code.bad-structure': 'unexpected structure',
    'pv.file': 'Exported file:',
    'pv.empty': 'Nothing to export yet.',
    'pv.points': '{0} points, carried as is',
    'imp.title': 'Import into the module',
    'imp.src': 'Source',
    'imp.src.hq': 'Mission loaded in HQ',
    'imp.src.pkg': 'Flight package',
    'imp.src.snap': 'Snapshot file',
    'imp.src.rp': 'Route Planner', 'imp.src.bg': 'Briefing Generator', 'imp.src.dg': 'Datacard Generator',
    'imp.soon': 'Not wired yet: next lot.',
    'imp.hq.none': 'No mission in HQ: load one in HQ (same browser).',
    'imp.hq.ok': '{0} · theatre {1}',
    'imp.choose': 'Choose a file…',
    'imp.pkg.note': 'A .json or .zip package (exported by HQ, the Route Planner or this module).',
    'imp.snap.note': 'The _snapshot.json written by HQ.',
    'imp.flights': 'Flights to import',
    'imp.none': 'Choose a source.',
    'imp.part.route': 'Route', 'imp.part.radios': 'Radios', 'imp.part.loadout': 'Loadout', 'imp.part.livery': 'Livery',
    'imp.new': 'new flight', 'imp.exists': 'completes the module’s flight',
    'imp.unsupported': 'aircraft not handled',
    'imp.units': '{0} unit(s)',
    'imp.theatre.keep': 'The module’s theatre ({0}) is kept; the source’s is {1}.',
    'imp.theatre.set': 'The theatre will become {0}.',
    'imp.cancel': 'Cancel', 'imp.go': 'Import', 'imp.close': 'Close',
    'imp.done': '{0} flight(s) imported.',
    'rej.json': 'Unreadable file: not JSON.',
    'rej.zip': 'Unreadable archive: no package.json at the root.',
    'rej.noTheatre': 'The package has no theatre.',
    'rej.noFlight': 'No readable flight in this file.',
    'rej.format': 'Format “{0}” not recognised here (expected: {1}).',
    'rej.unknown': 'unknown',
    'rej.skip': '{0} unreadable flight(s) skipped.',
    'fmt.pkg': 'flight package', 'fmt.snap': 'HQ snapshot', 'fmt.work': 'working file',
    'open.bad': 'This file is neither a working file nor a flight package.',
    'open.done': 'File opened: {0} flight(s).',
    'clear.confirm': 'Empty the module? The flights, route and loadouts in progress are lost (your kept presets stay).',
    'save.done': 'Work saved: {0}',
    'export.done': 'Package exported: {0}',
    'about.credit': 'Front-view drawings: Goldwolf (DCS Reference Guide), used with permission, outside the repository licence. Weapon tables: pydcs, LGPL-3.0.'
  }
};

let CURRENT_LANG = 'fr';
function t(key) {
  const d = I18N[CURRENT_LANG] || I18N.fr;
  if (key in d) return d[key];
  if (key in I18N.fr) return I18N.fr[key];
  return key;
}
function tf(key) {
  const a = arguments;
  return t(key).replace(/\{(\d+)\}/g, (m, i) => (Number(i) + 1 < a.length ? String(a[Number(i) + 1]) : m));
}
function esc(s) {
  return String(s === undefined || s === null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
const isObj = o => !!o && typeof o === 'object' && !Array.isArray(o);
const str = v => (typeof v === 'string' ? v : '');
const clone = o => JSON.parse(JSON.stringify(o));
const has = (o, k) => Object.prototype.hasOwnProperty.call(o, k);

// ---------- données par type ----------
const TYPE_LABEL = { 'Mi-24P': 'Mi-24P', 'Mi-8MT': 'Mi-8MT', 'F-4E-45MC': 'F-4E-45MC', 'Mirage-F1EE': 'Mirage F1EE' };
// Nombre de canaux par poste (sonde des .miz) ; seuls les postes qui ont des canaux s'offrent.
const RADIO_CHANNELS = { 'Mi-24P': { 1: 20, 2: 10 }, 'Mi-8MT': { 1: 20, 2: 10 }, 'F-4E-45MC': { 1: 18, 2: 20 }, 'Mirage-F1EE': { 1: 20, 2: 20 } };
// Bande plausible par poste, en MHz (valeurs du module, bornées par les fréquences vues dans les .miz d'exemple)
const RADIO_BANDS = {
  'Mi-24P': { 1: [100, 399.975], 2: [20, 59.975] }, 'Mi-8MT': { 1: [100, 399.975], 2: [20, 59.975] },
  'F-4E-45MC': { 1: [225, 399.975], 2: [225, 399.975] }, 'Mirage-F1EE': { 1: [118, 399.975], 2: [225, 399.975] }
};
const THEATRES = ['Caucasus', 'Falklands', 'GermanyCW', 'Kola', 'MarianaIslands', 'Nevada', 'Normandy', 'PersianGulf', 'SinaiMap', 'Syria', 'TheChannel'];
const PARTS = ['route', 'radios', 'loadout', 'livery'];
const KEY_THEME = 'theme_v1', KEY_LANG = 'lang_v1', KEY_STATE = 'fc_state_v1';
const KEY_SNAPSHOT = 'mission_snapshot_v1', SNAPSHOT_SCHEMA = 'dcs-mission-snapshot-v1', PACKAGE_FORMAT = 'dcs-flight-package-v1';

// ---------- état ----------
const S = { theatre: '', flights: [], sel: { f: 0, u: 0 } };
const LIB = { files: [], mine: {}, errors: [] };
const UI = { open: new Set(), cmp: { sym: true, st: null, saving: false, name: '', err: '' }, imp: null };

function newUnit() { return { name: '', callsign: '', csRaw: undefined, onboard: '', livery: '', radios: {}, loadout: null }; }
function newFlight() { return { name: '', type: 'Mi-24P', coalition: '', route: null, units: [newUnit()] }; }
function RADIO_POSTS(type) { return Object.keys(RADIO_CHANNELS[type] || {}).map(Number); }
function flightLabel(f, fi) { return f.name.trim() || tf('fl.title', fi + 1); }
function unitDefaultName(f, fi, ui) { return (f.name.trim() || tf('fl.title', fi + 1)) + '-' + (ui + 1); }
function unitLabel(f, fi, u, ui) { return u.name.trim() || unitDefaultName(f, fi, ui); }

// ---------- stockage (jamais requis : tout accès en try/catch) ----------
function lsGet(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }
function lsSet(k, v) { try { localStorage.setItem(k, v); } catch (e) { /* l'écran marche sans */ } }
// L'état propre du module tient sous une seule clé, fc_state_v1 : { v, state (le travail en cours), mine (mes presets) }
function loadMine(o) {
  if (isObj(o) && isObj(o.mine)) PAYLOAD_TYPES.forEach(ty => { if (Array.isArray(o.mine[ty])) LIB.mine[ty] = o.mine[ty]; });
}
function saveMine() { saveWork(); }

// ---------- presets d'un type ----------
// Rend [{ key, label, preset, src }] : d'abord les fichiers chargés, puis « mes presets »
function presetsFor(type) {
  const out = [];
  LIB.files.forEach((f, fi) => {
    if (f.parsed.unitType !== type) return;
    f.parsed.presets.forEach((p, pi) => out.push({ key: 'f' + fi + ':' + pi, label: p.displayName || p.name, preset: p, src: tf('lo.src.file', f.name) }));
  });
  (LIB.mine[type] || []).forEach((p, pi) => out.push({ key: 'm:' + pi, label: '★ ' + (p.displayName || p.name), preset: p, src: t('lo.src.mine') }));
  return out;
}

// ---------- indicatif : un nombre s'écrit en nombre, un texte en { name } ----------
function csText(v) {
  if (typeof v === 'number') return String(v);
  if (typeof v === 'string') return v;
  if (isObj(v) && typeof v.name === 'string') return v.name;
  return '';
}
function csValue(u) {
  if (u.csRaw !== undefined && u.csRaw !== null && csText(u.csRaw) === u.callsign) return u.csRaw;
  const x = u.callsign.trim();
  if (x === '') return null;
  return /^\d+$/.test(x) ? Number(x) : { name: x };
}

// ---------- fréquences ----------
function parseFreq(s) {
  const x = String(s).trim().replace(',', '.');
  if (x === '') return { empty: true };
  if (!/^\d+(\.\d+)?$/.test(x)) return { nan: true };
  return { v: Number(x) };
}
function fmtMHz(v) { return String(v).replace('.', CURRENT_LANG === 'fr' ? ',' : '.'); }
// Le premier défaut d'un poste : { msg, bad } (bad = nombre de canaux fautifs), et les canaux fautifs
function radioIssues(f, u, r) {
  const n = RADIO_CHANNELS[f.type][r], band = (RADIO_BANDS[f.type] || {})[r];
  const bad = [];
  let first = '';
  for (let c = 1; c <= n; c++) {
    const raw = (u.radios[r] && u.radios[r][c] !== undefined) ? u.radios[r][c] : '';
    const p = parseFreq(raw);
    let msg = '';
    if (p.nan) msg = tf('rad.err.nan', radioCockpitChannel(f.type, r, c), raw);
    else if (p.v !== undefined && band && (p.v < band[0] || p.v > band[1])) msg = tf('rad.err.band', radioCockpitChannel(f.type, r, c), fmtMHz(p.v), fmtMHz(band[0]), fmtMHz(band[1]));
    if (msg) { bad.push(c); if (!first) first = msg; }
  }
  return { first: first, bad: bad };
}
function radioCount(f, u) {
  let n = 0;
  RADIO_POSTS(f.type).forEach(r => {
    for (let c = 1; c <= RADIO_CHANNELS[f.type][r]; c++) if (u.radios[r] && String(u.radios[r][c] === undefined ? '' : u.radios[r][c]).trim() !== '') n++;
  });
  return n;
}

// ---------- réglages d'emport (hors preset) ----------
function loadoutIssue(f, lo) {
  const d = payloadDefaults(f.type), lim = payloadLureLimits(f.type);
  const spec = { fuel: [t('lo.fuel'), d.fuel], flare: [t('lo.flare'), d.flare], chaff: [t('lo.chaff'), d.chaff], gun: [t('lo.gun'), 100] };
  const bad = {};
  let msg = '';
  Object.keys(spec).forEach(k => {
    const p = parseFreq(lo[k]);
    if (p.nan || p.empty || p.v > spec[k][1]) { bad[k] = true; if (!msg) msg = tf('lo.err.range', spec[k][0], fmtMHz(spec[k][1])); }
  });
  if (!msg) {
    const fl = Number(String(lo.flare).replace(',', '.')), ch = Number(String(lo.chaff).replace(',', '.'));
    if (lim.total !== null && lim.total !== undefined && fl * (lim.flareSize || 0) + ch * (lim.chaffSize || 0) > lim.total) { bad.flare = true; bad.chaff = true; msg = tf('lo.err.lure', lim.total); }
  }
  return { msg: msg, bad: bad };
}
function loadoutFromPreset(type, key, label, src, pylons, prev) {
  const d = payloadDefaults(type);
  const py = {};
  Object.keys(pylons).forEach(n => { if (pylons[n] && pylons[n].CLSID) py[n] = clone(pylons[n]); });
  return {
    key: key, label: label, src: src, modified: false, pylons: py,
    fuel: prev ? prev.fuel : String(d.fuel), flare: prev ? prev.flare : String(d.flare), chaff: prev ? prev.chaff : String(d.chaff), gun: prev ? prev.gun : String(d.gun)
  };
}
function loadoutFromPayload(type, p) {
  if (!isObj(p) || !isObj(p.pylons)) return null;
  const pyl = {};
  Object.keys(p.pylons).forEach(k => {
    const e = p.pylons[k];
    if (isObj(e) && typeof e.CLSID === 'string' && e.CLSID !== '' && /^\d+$/.test(k)) {
      pyl[k] = { CLSID: e.CLSID };
      if (e.settings !== undefined && e.settings !== null) pyl[k].settings = clone(e.settings);
    }
  });
  const d = payloadDefaults(type);
  const num = (v, dflt) => ((typeof v === 'number' && isFinite(v)) || (typeof v === 'string' && v.trim() !== '' && isFinite(Number(v)))) ? String(v) : String(dflt);
  return { key: 'imp', label: t('lo.imported'), src: t('lo.src.imp'), modified: false, pylons: pyl,
    fuel: num(p.fuel, d.fuel), flare: num(p.flare, d.flare), chaff: num(p.chaff, d.chaff), gun: num(p.gun, d.gun) };
}
function loadoutName(lo) { return lo ? lo.label + (lo.modified ? ' · ' + t('cmp.mod') : '') : t('u.loadout.none'); }

// ---------- le paquet ----------
function cleanName(s) { return String(s).replace(/[^A-Za-z0-9_-]/g, '_').slice(0, 40); }
function stamp() {
  const d = new Date(), p = n => String(n).padStart(2, '0');
  return d.getFullYear() + p(d.getMonth() + 1) + p(d.getDate()) + '_' + p(d.getHours()) + p(d.getMinutes()) + p(d.getSeconds());
}
function packageFileName(prefix) {
  const first = S.flights.length ? (S.flights[0].name.trim() || 'vol') : 'vol';
  return (prefix || 'paquet') + '_' + cleanName(first) + (S.flights.length > 1 ? '_+' + (S.flights.length - 1) : '') + '_' + stamp() + '.json';
}
// Ce qui empêche l'export : [{ key, args }] ; la liste vide = prêt
function exportIssues() {
  const out = [];
  if (!S.theatre) out.push({ key: 'bar.no.theatre', args: [] });
  if (!S.flights.length) out.push({ key: 'bar.no.flight', args: [] });
  let nf = 0;
  S.flights.forEach((f, fi) => {
    if (!f.name.trim()) out.push({ key: 'bar.no.name', args: [fi + 1] });
    f.units.forEach(u => RADIO_POSTS(f.type).forEach(r => { nf += radioIssues(f, u, r).bad.length; }));
    f.units.forEach((u, ui) => { const li = u.loadout ? loadoutIssue(f, u.loadout) : null; if (li && li.msg) out.push({ key: 'bar.bad.set', args: [fi + 1, ui + 1, li.msg] }); });
  });
  if (nf) out.push({ key: 'bar.bad.freq', args: [nf] });
  return out;
}
function unitRadiosOut(f, u) {
  const out = [];
  RADIO_POSTS(f.type).forEach(r => {
    const ch = {};
    for (let c = 1; c <= RADIO_CHANNELS[f.type][r]; c++) {
      const p = parseFreq(u.radios[r] && u.radios[r][c] !== undefined ? u.radios[r][c] : '');
      if (p.v !== undefined) ch[String(c)] = p.v;
    }
    if (Object.keys(ch).length) out.push({ radioIndex: r, channels: ch });
  });
  return out.length ? out : null;
}
function unitPayloadOut(f, u) {
  const lo = u.loadout;
  if (!lo) return null;
  const num = v => { const p = parseFreq(v); return p.v; };
  return buildPayload(f.type, lo.pylons, { fuel: num(lo.fuel), flare: num(lo.flare), chaff: num(lo.chaff), gun: num(lo.gun) });
}
// Le paquet dcs-flight-package-v1 : une partie non renseignée sort en null (HQ n'y touche pas) ; la fréquence du groupe n'est plus portée.
function buildPackage() {
  return {
    format: PACKAGE_FORMAT, createdAt: new Date().toISOString(), createdBy: 'Flight Configurator', theatre: S.theatre,
    flights: S.flights.map((f, fi) => ({
      groupName: f.name.trim(), aircraftType: f.type, coalition: f.coalition || null, groupFrequency: null,
      route: f.route ? { points: clone(f.route.points) } : null,
      units: f.units.map((u, ui) => {
        const o = { name: unitLabel(f, fi, u, ui), callsign: csValue(u), liveryId: u.livery.trim() || null, radios: unitRadiosOut(f, u), payload: unitPayloadOut(f, u) };
        if (u.onboard.trim()) o.onboardNum = u.onboard.trim();
        return o;
      })
    }))
  };
}
// Le fichier de travail : le paquet tel qu'il se lit, plus la clé « fc » (état de l'écran, presets) que HQ ignore.
function buildWorkFile() {
  const pkg = buildPackage();
  if (!S.theatre) delete pkg.theatre;
  pkg.createdBy = 'Flight Configurator';
  pkg.fc = { v: 1, state: clone(S), mine: clone(LIB.mine) };
  return pkg;
}
function previewJson() {
  return JSON.stringify(buildPackage(), (k, v) => {
    if (k === 'route' && isObj(v) && isObj(v.points)) return { points: tf('pv.points', routePoints(v.points).length) };
    return v;
  }, 2);
}

// ---------- la route : portée telle quelle ----------
function routeKeys(points) { return isObj(points) ? Object.keys(points).filter(k => /^\d+$/.test(k)).sort((a, b) => Number(a) - Number(b)) : []; }
function routePoints(points) { return routeKeys(points).map(k => ({ k: k, name: (isObj(points[k]) && typeof points[k].name === 'string' && points[k].name !== '') ? points[k].name.replace(/\s+/g, ' ') : 'WP' + k, alt: isObj(points[k]) ? points[k].alt : undefined })); }
function routeLine(f) {
  if (!f.route) return t('route.none');
  const pts = routePoints(f.route.points);
  if (!pts.length) return t('route.none');
  let s = pts.length === 1 ? tf('route.n1', pts[0].name) : tf('route.n', pts.length, pts[0].name, pts[pts.length - 1].name);
  if (typeof pts[0].alt === 'number' && isFinite(pts[0].alt)) s += tf('route.alt', Math.round(pts[0].alt));
  return s;
}

// ---------- rendu : éléments ----------
function selectHtml(attrs, label, options, value) {
  let h = '<select class="fc-sel" aria-label="' + esc(label) + '" ' + attrs + '>';
  options.forEach(o => { h += '<option value="' + esc(o.v) + '"' + (String(o.v) === String(value) ? ' selected' : '') + '>' + esc(o.l) + '</option>'; });
  return h + '</select>';
}
function fieldHtml(label, inner) { return '<div class="ed-field"><label>' + esc(label) + '</label>' + inner + '</div>'; }
function inputHtml(attrs, value, ph, cls) {
  return '<input type="text" autocomplete="off" spellcheck="false" ' + attrs + ' value="' + esc(value) + '"' + (ph ? ' placeholder="' + esc(ph) + '"' : '') + (cls ? ' class="' + cls + '"' : '') + '>';
}
function openAttr(key, dflt) { return (UI.open.has(key) || (dflt && !UI.open.has('~' + key))) ? ' open' : ''; }
function unitsLabel(n) { return tf(n < 2 ? 'fl.units.one' : 'fl.units.many', n); }
function selUnit() { const f = S.flights[S.sel.f]; return f && f.units[S.sel.u] ? { f: f, fi: S.sel.f, u: f.units[S.sel.u], ui: S.sel.u } : null; }

// ---------- rendu : colonne de gauche ----------
function renderLeft() {
  const opts = [{ v: '', l: t('pkg.theatre.none') }].concat(THEATRES.concat(S.theatre && THEATRES.indexOf(S.theatre) < 0 ? [S.theatre] : []).map(x => ({ v: x, l: x })));
  let h = '<section class="fc-block"><div class="fc-bh">' + esc(t('sec.flights')) + ' <span class="fc-count">(' + S.flights.length + ')</span></div><div class="fc-bc">';
  h += '<div class="fc-row fc-top">' + fieldHtml(t('pkg.theatre'), selectHtml('id="pkg-theatre" data-k="theatre"', t('pkg.theatre'), opts, S.theatre))
    + fieldHtml(t('pkg.fname'), '<div class="fc-fname" id="pkg-fname"></div>') + '</div>';
  if (!S.flights.length) h += '<p class="pk-note">' + esc(t('fl.empty')) + '</p>';
  h += '<div class="fc-list" id="fc-list">';
  S.flights.forEach((f, fi) => { h += flightHtml(f, fi); });
  h += '</div><div class="miz-btn-row" style="margin-top:0"><button type="button" class="miz-btn primary" data-act="add-flight">' + esc(t('fl.add')) + '</button></div></div></section>';
  document.getElementById('col-flights').innerHTML = h;
  S.flights.forEach((f, fi) => f.units.forEach((u, ui) => { RADIO_POSTS(f.type).forEach(r => paintRadioMsg(fi, ui, r)); }));
  refreshFileName();
}

function flightHtml(f, fi) {
  const typeOpts = PAYLOAD_TYPES.map(x => ({ v: x, l: TYPE_LABEL[x] }));
  const coOpts = [{ v: '', l: t('fl.coalition.any') }, { v: 'blue', l: t('fl.coalition.blue') }, { v: 'red', l: t('fl.coalition.red') }];
  let h = '<div class="fc-flight" data-f="' + fi + '">';
  h += '<div class="fc-fhead"><span class="fc-ftitle">' + esc(flightLabel(f, fi)) + '</span><span class="snap-flight-tag">' + esc(TYPE_LABEL[f.type]) + '</span>'
    + '<span class="snap-flight-tag">' + esc(unitsLabel(f.units.length)) + '</span>'
    + '<button type="button" class="pk-x" data-act="rm-flight" aria-label="' + esc(t('fl.remove')) + '" title="' + esc(t('fl.remove')) + '">✕</button></div>';
  h += '<div class="fc-row3">';
  h += fieldHtml(t('fl.name'), inputHtml('data-k="name"', f.name, t('fl.name.ph')));
  h += fieldHtml(t('fl.type'), selectHtml('data-k="type"', t('fl.type'), typeOpts, f.type));
  h += fieldHtml(t('fl.coalition'), selectHtml('data-k="coalition"', t('fl.coalition'), coOpts, f.coalition));
  h += '</div>';
  h += '<div class="fc-route' + (f.route && routePoints(f.route.points).length ? '' : ' none') + '"><span class="fc-route-t">' + esc(routeLine(f)) + '</span>';
  if (f.route && routePoints(f.route.points).length) h += '<button type="button" class="miz-btn fc-small" data-act="rm-route">' + esc(t('route.rm')) + '</button>';
  h += '</div>';
  h += '<div class="fc-units">';
  f.units.forEach((u, ui) => { h += unitHtml(f, fi, u, ui); });
  h += '</div>';
  if (f.units.length < 4) h += '<div class="miz-btn-row"><button type="button" class="miz-btn" data-act="add-unit">' + esc(tf('u.add', f.units.length)) + '</button></div>';
  return h + '</div>';
}

function unitHtml(f, fi, u, ui) {
  const at = 'data-u="' + ui + '"';
  const sel = S.sel.f === fi && S.sel.u === ui;
  let h = '<div class="fc-unit' + (sel ? ' sel' : '') + '" data-u="' + ui + '">';
  h += '<div class="fc-uhead"><span class="fc-utitle">' + esc(tf('u.title', ui + 1)) + '</span>';
  if (f.units.length > 1) h += '<button type="button" class="pk-x" data-act="rm-unit" aria-label="' + esc(t('u.remove')) + '" title="' + esc(t('u.remove')) + '">✕</button>';
  h += '</div>';
  h += '<div class="fc-row4">';
  h += fieldHtml(t('u.name'), inputHtml(at + ' data-k="uname"', u.name, unitDefaultName(f, fi, ui)));
  h += fieldHtml(t('u.callsign'), inputHtml(at + ' data-k="callsign"', u.callsign, t('u.opt')));
  h += fieldHtml(t('u.onboard'), inputHtml(at + ' data-k="onboard"', u.onboard, t('u.opt')));
  h += fieldHtml(t('u.livery'), inputHtml(at + ' data-k="livery"', u.livery, t('u.livery.ph')));
  h += '</div>';
  const rk = 'f' + fi + 'u' + ui + 'r';
  const n = radioCount(f, u);
  h += '<details class="fc-sub" data-key="' + rk + '"' + openAttr(rk, false) + '><summary>' + esc(t('u.radios')) + ' <span class="fc-sum" data-sum="radios">' + esc(n ? tf('u.radios.set', n) : tf('u.radios.sum', RADIO_POSTS(f.type).length)) + '</span></summary><div class="fc-subc">';
  h += radiosHtml(f, fi, u, ui);
  h += '</div></details>';
  h += '<div class="fc-lo-sum"><span class="fc-lo-k">' + esc(t('u.loadout')) + '</span><span class="fc-lo-v" data-sum="loadout">' + esc(loadoutName(u.loadout)) + '</span>'
    + '<button type="button" class="miz-btn fc-small" ' + at + ' data-act="sel-unit">' + esc(t('u.compose')) + '</button></div>';
  return h + '</div>';
}

function radiosHtml(f, fi, u, ui) {
  let h = '<div class="fc-posts">';
  RADIO_POSTS(f.type).forEach(r => {
    const n = RADIO_CHANNELS[f.type][r];
    const pk = 'f' + fi + 'u' + ui + 'p' + r;
    h += '<details class="fc-post" data-key="' + pk + '"' + openAttr(pk, false) + '><summary>' + esc(radioPosteName(f.type, r) || ('R' + r)) + ' <span class="fc-sum">' + esc(tf('rad.chans', n)) + '</span></summary><div class="fc-postc">';
    h += '<div class="fc-chans">';
    for (let c = 1; c <= n; c++) {
      const v = (u.radios[r] && u.radios[r][c] !== undefined) ? u.radios[r][c] : '';
      h += '<div class="fc-ch"><label>' + esc(tf('rad.ch', radioCockpitChannel(f.type, r, c))) + '</label>'
        + '<input type="text" inputmode="decimal" autocomplete="off" data-u="' + ui + '" data-r="' + r + '" data-c="' + c + '" data-k="chan" value="' + esc(v) + '" placeholder="—"></div>';
    }
    h += '</div><div class="fc-msg" id="rm-' + fi + '-' + ui + '-' + r + '"></div></div></details>';
  });
  h += '</div><p class="pk-note">' + esc(t('rad.hint')) + '</p>';
  if (f.units.length > 1) h += '<div class="miz-btn-row" style="margin-top:0"><button type="button" class="miz-btn" data-u="' + ui + '" data-act="copy-radios">' + esc(t('rad.copy')) + '</button></div>';
  return h;
}

function paintRadioMsg(fi, ui, r) {
  const f = S.flights[fi], u = f && f.units[ui];
  if (!u) return;
  const iss = radioIssues(f, u, r);
  const root = document.querySelector('#col-left .fc-flight[data-f="' + fi + '"] .fc-unit[data-u="' + ui + '"]');
  if (root) root.querySelectorAll('input[data-r="' + r + '"]').forEach(inp => inp.classList.toggle('bad', iss.bad.indexOf(Number(inp.getAttribute('data-c'))) >= 0));
  const el = document.getElementById('rm-' + fi + '-' + ui + '-' + r);
  if (el) el.textContent = iss.first ? iss.first + (iss.bad.length > 1 ? tf('rad.err.more', iss.bad.length - 1) : '') : '';
}

function refreshFileName() { const e = document.getElementById('pkg-fname'); if (e) e.textContent = packageFileName(); }
function refreshUnitSummaries() {
  S.flights.forEach((f, fi) => f.units.forEach((u, ui) => {
    const root = document.querySelector('#col-left .fc-flight[data-f="' + fi + '"] .fc-unit[data-u="' + ui + '"]');
    if (!root) return;
    const lv = root.querySelector('[data-sum="loadout"]'); if (lv) lv.textContent = loadoutName(u.loadout);
    const rv = root.querySelector('[data-sum="radios"]'); if (rv) { const n = radioCount(f, u); rv.textContent = n ? tf('u.radios.set', n) : tf('u.radios.sum', RADIO_POSTS(f.type).length); }
  }));
}

// ---------- barre : état de l'export ----------
function refreshBar() {
  const iss = exportIssues();
  const b = document.getElementById('btn-export');
  if (b) { b.disabled = iss.length > 0; b.setAttribute('aria-disabled', iss.length ? 'true' : 'false'); }
  const st = document.getElementById('fc-status');
  if (st) {
    st.classList.toggle('ok', iss.length === 0);
    st.textContent = iss.length ? iss.map(i => tf.apply(null, [i.key].concat(i.args))).join(' ') : tf('bar.ok', packageFileName());
  }
}
function refreshPreview() {
  const pre = document.getElementById('fc-preview'), nm = document.getElementById('pv-file');
  if (!pre) return;
  pre.textContent = S.flights.length ? previewJson() : t('pv.empty');
  if (nm) nm.textContent = packageFileName();
}
function refreshAll() { refreshBar(); refreshPreview(); refreshFileName(); saveWork(); }

// ---------- le travail en cours (rule 8) ----------
let _saveTimer = 0;
function saveWork() {
  clearTimeout(_saveTimer);
  _saveTimer = setTimeout(() => lsSet(KEY_STATE, JSON.stringify({ v: 1, state: S, mine: LIB.mine })), 400);
}
function restoreState(st) {
  if (!isObj(st) || !Array.isArray(st.flights)) return false;
  const fl = [];
  st.flights.forEach(f => {
    if (!isObj(f) || PAYLOAD_TYPES.indexOf(f.type) < 0) return;
    const nf = newFlight();
    nf.name = str(f.name); nf.type = f.type; nf.coalition = (f.coalition === 'blue' || f.coalition === 'red') ? f.coalition : '';
    nf.route = (isObj(f.route) && isObj(f.route.points)) ? { points: f.route.points } : null;
    nf.units = (Array.isArray(f.units) ? f.units : []).slice(0, 4).filter(isObj).map(u => {
      const nu = newUnit();
      nu.name = str(u.name); nu.callsign = str(u.callsign); nu.csRaw = u.csRaw; nu.onboard = str(u.onboard); nu.livery = str(u.livery);
      nu.radios = isObj(u.radios) ? u.radios : {};
      nu.loadout = (isObj(u.loadout) && isObj(u.loadout.pylons)) ? u.loadout : null;
      return nu;
    });
    if (!nf.units.length) nf.units.push(newUnit());
    fl.push(nf);
  });
  S.theatre = str(st.theatre); S.flights = fl;
  S.sel = (isObj(st.sel) && Number.isInteger(st.sel.f) && Number.isInteger(st.sel.u)) ? st.sel : { f: 0, u: 0 };
  if (!selUnit()) S.sel = { f: 0, u: 0 };
  return true;
}

// =============================================================
//  L'EMPORT — la vue de face de Mission Tools (Loadout Editor), reprise et adaptée : un panneau dans la page, sur l'unité choisie
// =============================================================
const CMP = { view: null, pairs: {}, pyl: [], small: false, ro: null, type: null };

// Paires : deux stations dont les points d'attache sont symétriques par rapport au milieu du viewBox
// (écart ≤ 2 % de la largeur, même hauteur à 2 % près de la hauteur).
function cmpPairs(view) {
  const W = view.viewBox[0], H = view.viewBox[1], ks = Object.keys(view.stations), out = {};
  for (const a of ks) {
    let best = null, bd = Infinity;
    for (const b of ks) {
      if (a === b) continue;
      const A = view.stations[a], B = view.stations[b];
      const dx = Math.abs(W - A.x - B.x), dy = Math.abs(A.y - B.y);
      if (dx <= 0.02 * W && dy <= 0.02 * H && dx < bd) { best = b; bd = dx; }
    }
    if (best !== null) out[a] = best;
  }
  for (const a of Object.keys(out)) if (out[out[a]] !== a) delete out[a];
  return out;
}
// Nom court : jusqu'au premier « - », sans les parenthèses ; « UnGd Rkts » : on ajoute « · » et le mot après « mm ».
function cmpShort(clsid) {
  if (!clsid) return '—';
  const full = payloadWeaponName(clsid) || clsid;
  let head = full.split(' - ')[0].replace(/\s*\([^)]*\)/g, '').replace(/\s+/g, ' ').trim();
  const k = full.indexOf('UnGd Rkts');
  if (k >= 0) { const m = /\bmm\s+(\S+)/.exec(full.slice(k)); if (m) head += ' · ' + m[1]; }
  return head || full;
}
function cmpNum(n) { return String(Math.round(n)).replace(/\B(?=(\d{3})+(?!\d))/g, CURRENT_LANG === 'fr' ? ' ' : ','); }
function cmpClsid(lo, n) { return lo && lo.pylons[n] && lo.pylons[n].CLSID ? String(lo.pylons[n].CLSID) : ''; }

function renderRight() {
  const col = document.getElementById('col-right');
  const su = selUnit();
  CMP.small = col.clientWidth < 900;
  let h = '<section class="fc-block" id="blk-cmp"><div class="fc-bh">' + esc(t('sec.cmp')) + '</div><div class="fc-bc">' + (su ? cmpHtml(su) : '<p class="pk-note">' + esc(t('cmp.pick')) + '</p>') + '</div></section>';
  h += '<section class="fc-block" id="blk-pv"><div class="fc-bh">' + esc(t('sec.preview')) + '</div><div class="fc-bc"><div class="fc-pvfile"><span>' + esc(t('pv.file')) + '</span> <span id="pv-file"></span></div><pre class="fc-pre" id="fc-preview" tabindex="0"></pre></div></section>';
  col.innerHTML = h;
  if (CMP.ro) { CMP.ro.disconnect(); CMP.ro = null; }
  const wrap = document.getElementById('cmp-wrap');
  if (su && wrap && !CMP.small && typeof ResizeObserver === 'function') { CMP.ro = new ResizeObserver(cmpDraw); CMP.ro.observe(wrap); }
  if (su && CMP.small) cmpStaggerNums();
  cmpUpdate();
  refreshPreview();
  renderPresets();
}
function renderPresets() { document.getElementById('col-presets').innerHTML = presetsHtml(); }

function cmpFromOptions(f, lo) {
  const list = presetsFor(f.type);
  const o = [{ v: '', l: t('cmp.from.none') }];
  if (lo && lo.key === 'imp') o.push({ v: 'imp', l: t('cmp.from.imp') });
  list.forEach(p => o.push({ v: p.key, l: p.label }));
  o.push({ v: '~empty', l: t('cmp.from.empty') });
  return o;
}

function cmpHtml(su) {
  const f = su.f, lo = su.u.loadout;
  const pyl = payloadPylons(f.type);
  CMP.type = f.type; CMP.pyl = pyl || [];
  CMP.view = has(AIRCRAFT_VIEWS, f.type) ? AIRCRAFT_VIEWS[f.type] : null;
  CMP.pairs = CMP.view ? cmpPairs(CMP.view) : {};
  const view = CMP.view, small = CMP.small, C = UI.cmp;
  let h = '<div class="cmp-top"><div class="cmp-for">' + esc(tf('cmp.for', flightLabel(f, su.fi), unitLabel(f, su.fi, su.u, su.ui))) + ' <span class="snap-flight-tag">' + esc(TYPE_LABEL[f.type]) + '</span></div>';
  h += fieldHtml(t('cmp.from'), selectHtml('id="cmp-from"', t('cmp.from'), cmpFromOptions(f, lo), lo ? (lo.key || '') : '')) + '</div>';
  if (lo) h += '<div class="fc-lo-line"><span class="snap-flight-tag">' + esc(lo.src || '') + '</span>' + (lo.modified ? '<span class="snap-flight-tag">' + esc(t('cmp.mod')) + '</span>' : '') + '</div>';
  if (view) {
    const W = view.viewBox[0], H = view.viewBox[1];
    const ks = Object.keys(view.stations).sort((a, b) => view.stations[a].x - view.stations[b].x);
    h += '<div id="cmp-wrap" class="' + (small ? 'cmp-wrap-flat' : 'cmp-wrap-strip') + '"><div class="cmp-view"><div class="cmp-svgbox" style="--r:' + (W / H) + '">' + view.svg;
    if (small) ks.forEach(k => {
      const s = view.stations[k];
      h += '<span class="cmp-num" data-st="' + esc(k) + '" style="left:' + (s.x / W * 100).toFixed(2) + '%;top:' + (s.y / H * 100).toFixed(2) + '%">' + esc(k) + '</span>';
    });
    h += '</div><div class="cmp-credit">' + esc(t('cmp.credit')) + '</div></div>';
    if (!small) {
      h += '<svg id="cmp-leads" aria-hidden="true"></svg><div class="cmp-strip" style="--n:' + ks.length + '">';
      ks.forEach((k, i) => { h += '<div class="cmp-st" data-st="' + esc(k) + '" role="button" tabindex="0" style="left:' + ((i + 0.5) / ks.length * 100).toFixed(3) + '%"><span class="n">' + esc(k) + '</span><span class="w"></span></div>'; });
      h += '</div>';
    }
    h += '</div>';
  } else h += '<p class="pk-note">' + esc(t('cmp.noview')) + '</p>';
  h += '<div class="cmp-list" id="cmp-list">';
  CMP.pyl.forEach(({ n, allowed }) => {
    const s0 = cmpClsid(lo, n);
    let opts = '';
    if (s0 !== '' && allowed.indexOf(s0) < 0) opts += '<option value="' + esc(s0) + '">' + esc((payloadWeaponName(s0) || s0) + ' ' + t('cmp.offTable')) + '</option>';
    opts += '<option value="">' + esc(t('cmp.none')) + '</option>';
    allowed.forEach(c => { opts += '<option value="' + esc(c) + '">' + esc(payloadWeaponName(c) || c) + '</option>'; });
    const p = (view && has(CMP.pairs, n)) ? CMP.pairs[n] : null;
    h += '<div class="cmp-row" data-st="' + esc(n) + '"><span class="sn">' + esc(n) + '</span><select class="fc-sel cmp-sel" data-st="' + esc(n) + '" aria-label="' + esc(tf('lo.pylon', n)) + '">' + opts + '</select>'
      + '<span class="pair">' + (p !== null ? '↔ ' + esc(p) : '') + '</span><span class="cmp-kg"></span></div>';
  });
  h += '</div><div class="cmp-foot">' + (view ? '<label class="pk-chk"><input type="checkbox" id="cmp-sym"' + (C.sym ? ' checked' : '') + '> ' + esc(t('cmp.sym')) + '</label>' : '')
    + '<span class="cmp-tot" id="cmp-total"></span></div>';
  if (lo) {
    const d = payloadDefaults(f.type), at = 'data-u="' + su.ui + '"';
    h += '<div class="fc-set">';
    h += fieldHtml(t('lo.fuel') + ' · ' + tf('lo.max', d.fuel), inputHtml(at + ' data-k="fuel" inputmode="decimal"', lo.fuel));
    h += fieldHtml(t('lo.flare') + ' · ' + tf('lo.max', d.flare), inputHtml(at + ' data-k="flare" inputmode="numeric"', lo.flare));
    h += fieldHtml(t('lo.chaff') + ' · ' + tf('lo.max', d.chaff), inputHtml(at + ' data-k="chaff" inputmode="numeric"' + (d.chaff === 0 ? ' disabled' : ''), lo.chaff));
    h += fieldHtml(t('lo.gun') + ' · ' + tf('lo.max', 100), inputHtml(at + ' data-k="gun" inputmode="numeric"', lo.gun));
    h += '</div><div class="fc-msg" id="lm-msg"></div>';
  }
  h += '<div class="miz-btn-row" style="margin-top:0"><button type="button" class="miz-btn primary" data-act="cmp-save"' + (lo ? '' : ' disabled') + '>' + esc(t('cmp.save')) + '</button>'
    + '<button type="button" class="miz-btn" data-act="cmp-clear"' + (lo ? '' : ' disabled') + '>' + esc(t('cmp.clear')) + '</button></div>';
  if (C.saving && lo) {
    h += '<div class="fc-editor"><div class="fc-row">' + fieldHtml(t('cmp.save.name'), inputHtml('data-k="cmp-name"', C.name, t('cmp.save.ph')))
      + '<div class="ed-field fc-actions"><button type="button" class="miz-btn primary" data-act="cmp-save-go">' + esc(t('cmp.save.go')) + '</button></div>'
      + '<div class="ed-field fc-actions"><button type="button" class="miz-btn" data-act="cmp-save-cancel">' + esc(t('cmp.save.cancel')) + '</button></div></div>'
      + '<div class="fc-msg" id="cmp-save-msg">' + esc(C.err) + '</div></div>';
  }
  h += '<p class="pk-note">' + esc(t('cmp.note')) + '</p>';
  return h;
}

// Sous 900 px de colonne, les pastilles qui se chevauchent sont étagées sur deux ou trois niveaux
function cmpStaggerNums() {
  const els = Array.prototype.slice.call(document.querySelectorAll('#blk-cmp .cmp-num'));
  els.forEach(e => { e.style.marginTop = '0'; });
  const rs = els.map(e => ({ e: e, r: e.getBoundingClientRect() })).sort((a, b) => a.r.left - b.r.left);
  const placed = [];
  rs.forEach(({ e, r }) => {
    let l = 0;
    const hit = o => r.left < o.right + 1 && o.left < r.right + 1 && r.top + l * 18 < o.bottom + 1 && o.top < r.bottom + l * 18 + 1;
    while (placed.some(hit)) l++;
    placed.push({ left: r.left, right: r.right, top: r.top + l * 18, bottom: r.bottom + l * 18 });
    e.style.marginTop = (l * 18) + 'px';
  });
  const box = document.querySelector('#blk-cmp .cmp-svgbox');
  if (box && placed.length) {
    box.style.marginBottom = '';
    const need = Math.max.apply(null, placed.map(o => o.bottom)) - box.getBoundingClientRect().bottom + 8;
    if (need > parseFloat(getComputedStyle(box).marginBottom)) box.style.marginBottom = Math.ceil(need) + 'px';
  }
}

// Valeurs affichées : listes, masses, pastilles, total
function cmpUpdate() {
  const su = selUnit(), blk = document.getElementById('blk-cmp');
  if (!su || !blk) return;
  const lo = su.u.loadout, C = UI.cmp;
  let total = 0, unknown = false;
  CMP.pyl.forEach(({ n }) => {
    const c = cmpClsid(lo, n);
    const row = blk.querySelector('.cmp-row[data-st="' + n + '"]');
    if (!row) return;
    const sel = row.querySelector('select');
    if (sel.value !== c) sel.value = c;
    let w = 0;
    if (c !== '') { w = payloadWeaponMass(c); if (w === null) unknown = true; else total += w; }
    row.querySelector('.cmp-kg').textContent = c === '' ? '' : (w === null ? '—' : cmpNum(w) + ' kg');
    row.classList.toggle('sel', C.st === n);
    const hasSet = !!(lo && lo.pylons[n] && lo.pylons[n].settings !== undefined);
    let chip = row.querySelector('.fc-chip');
    if (hasSet && !chip) { chip = document.createElement('span'); chip.className = 'fc-chip'; chip.textContent = t('cmp.settings'); row.insertBefore(chip, row.querySelector('.cmp-kg')); }
    else if (!hasSet && chip) chip.remove();
    const cell = blk.querySelector('.cmp-st[data-st="' + n + '"]');
    if (cell) {
      cell.querySelector('.w').textContent = cmpShort(c);
      cell.title = c ? (payloadWeaponName(c) || c) : '';
      cell.classList.toggle('sel', C.st === n);
      cell.setAttribute('aria-pressed', C.st === n ? 'true' : 'false');
    }
    const num = blk.querySelector('.cmp-num[data-st="' + n + '"]');
    if (num) num.classList.toggle('sel', C.st === n);
  });
  const tot = document.getElementById('cmp-total');
  if (tot) tot.innerHTML = esc(t('cmp.mass')) + ' <b>' + esc(cmpNum(total) + ' kg' + (unknown ? ' + ?' : '')) + '</b>';
  cmpDraw();
  paintLoadoutMsg();
}
function paintLoadoutMsg() {
  const su = selUnit();
  if (!su || !su.u.loadout) return;
  const iss = loadoutIssue(su.f, su.u.loadout);
  ['fuel', 'flare', 'chaff', 'gun'].forEach(k => { const i = document.querySelector('#blk-cmp input[data-k="' + k + '"]'); if (i) i.classList.toggle('bad', !!iss.bad[k]); });
  const m = document.getElementById('lm-msg'); if (m) m.textContent = iss.msg;
}

// Un trait pointillé par station : du point d'attache (petit rond) vers le bas, puis jusqu'à sa case
function cmpDraw() {
  const svg = document.getElementById('cmp-leads');
  if (!svg || !CMP.view) return;
  const wrap = document.getElementById('cmp-wrap');
  const box = wrap.querySelector('.cmp-svgbox'), view = wrap.querySelector('.cmp-view');
  const wr = wrap.getBoundingClientRect(), br = box.getBoundingClientRect(), vr = view.getBoundingClientRect();
  const W = CMP.view.viewBox[0], H = CMP.view.viewBox[1];
  svg.setAttribute('viewBox', '0 0 ' + wr.width + ' ' + wr.height);
  let out = '';
  Object.keys(CMP.view.stations).forEach(k => {
    const s = CMP.view.stations[k];
    const cell = wrap.querySelector('.cmp-st[data-st="' + k + '"]');
    if (!cell) return;
    const cr = cell.getBoundingClientRect();
    const x = br.left - wr.left + s.x / W * br.width, y = br.top - wr.top + s.y / H * br.height;
    const ky = Math.max(vr.bottom - wr.top - 22, y + 4);
    const cx = cr.left - wr.left + cr.width / 2, cy = cr.top - wr.top;
    out += '<path data-st="' + k + '"' + (UI.cmp.st === k ? ' class="on"' : '') + ' d="M' + x.toFixed(1) + ' ' + y.toFixed(1) + ' L' + x.toFixed(1) + ' ' + ky.toFixed(1) + ' L' + cx.toFixed(1) + ' ' + cy.toFixed(1) + '"/><circle cx="' + x.toFixed(1) + '" cy="' + y.toFixed(1) + '" r="5"/>';
  });
  svg.innerHTML = out;
}

// Un choix sur une station ; « Symétrique » le pose aussi sur sa paire quand la paire le permet.
// « Vide » ne se pose sur la paire que si elle portait le même CLSID que la station juste avant ce choix.
// Un `settings` suit sa station tant que l'arme ne change pas.
function cmpChoose(n, c) {
  const su = selUnit();
  if (!su) return;
  if (!su.u.loadout) su.u.loadout = loadoutFromPreset(su.f.type, '~empty', t('cmp.custom'), '', {}, null);
  const lo = su.u.loadout;
  const prev = cmpClsid(lo, n);
  const put = (k, v) => {
    if (v === '') delete lo.pylons[k];
    else if (cmpClsid(lo, k) !== v) lo.pylons[k] = { CLSID: v };
  };
  put(n, c);
  UI.cmp.st = n;
  if (UI.cmp.sym && CMP.view && has(CMP.pairs, n)) {
    const pp = CMP.pyl.filter(x => x.n === CMP.pairs[n])[0];
    if (pp && (c === '' ? (prev !== '' && cmpClsid(lo, pp.n) === prev) : pp.allowed.indexOf(c) >= 0)) put(pp.n, c);
  }
  lo.modified = lo.key !== '~empty';
  cmpUpdate();
  refreshUnitSummaries();
  refreshAll();
}
function cmpBase(key) {
  const su = selUnit();
  if (!su) return;
  const f = su.f, prev = su.u.loadout;
  if (key === '') su.u.loadout = null;
  else if (key === '~empty') su.u.loadout = loadoutFromPreset(f.type, '~empty', t('cmp.custom'), '', {}, prev);
  else if (key === 'imp') { /* déjà l'emport importé */ }
  else {
    const hit = presetsFor(f.type).filter(p => p.key === key)[0];
    if (hit) su.u.loadout = loadoutFromPreset(f.type, key, hit.label, hit.src, hit.preset.pylons, prev);
  }
  UI.cmp.saving = false; UI.cmp.err = '';
  renderRight(); refreshUnitSummaries(); refreshAll();
}
function cmpSaveGo() {
  const su = selUnit(), C = UI.cmp;
  if (!su || !su.u.loadout) return;
  const name = C.name.trim(), type = su.f.type;
  const fail = m => { C.err = m; const e = document.getElementById('cmp-save-msg'); if (e) e.textContent = m; };
  if (!name) return fail(t('cmp.save.err.name'));
  if ((LIB.mine[type] || []).some(p => p.name === name) || presetsFor(type).some(p => p.preset.name === name || p.preset.displayName === name)) return fail(tf('cmp.save.err.dup', TYPE_LABEL[type]));
  const pylons = {};
  Object.keys(su.u.loadout.pylons).forEach(n => { const p = su.u.loadout.pylons[n]; if (p && p.CLSID) pylons[n] = clone(p); });
  if (!Object.keys(pylons).length) return fail(t('cmp.save.err.none'));
  const order = Object.keys(pylons).map(Number).sort((a, b) => a - b);
  (LIB.mine[type] = LIB.mine[type] || []).push({ name: name, displayName: name, pylons: pylons, order: order, tasks: [TASK_DEFAULT[type]] });
  saveMine();
  const lo = su.u.loadout;
  lo.key = 'm:' + (LIB.mine[type].length - 1); lo.label = '★ ' + name; lo.src = t('lo.src.mine'); lo.modified = false;
  C.saving = false; C.err = ''; C.name = '';
  renderRight(); refreshUnitSummaries(); refreshAll();
  showToast(tf('cmp.save.ok', name));
}

// ---------- les presets (.lua) ----------
function presetsHtml() {
  let h = '<section class="fc-block" id="blk-pr"><div class="fc-bh">' + esc(t('sec.presets')) + '</div><div class="fc-bc">';
  h += '<div class="miz-btn-row" style="margin-top:0"><button type="button" class="miz-btn primary" data-act="load-lua">' + esc(t('pr.load')) + '</button></div>';
  h += '<p class="pk-note">' + esc(t('pr.hint')) + '</p>';
  LIB.errors.forEach(e => { h += '<div class="pk-warn">⚠ ' + esc(e) + '</div>'; });
  h += '<div class="fc-h">' + esc(tf('pr.files', LIB.files.length)) + '</div><div class="fc-lib">';
  LIB.files.forEach((fl, i) => {
    h += '<div class="fc-file"><span class="fc-file-n">' + esc(fl.name) + '</span><span class="snap-flight-tag">'
      + esc(fl.parsed.supported ? tf('pr.file.ok', fl.parsed.unitType, fl.parsed.presets.length) : tf('pr.file.unsup', fl.parsed.unitType)) + '</span>'
      + '<button type="button" class="pk-x" data-act="rm-file" data-i="' + i + '" aria-label="' + esc(t('pr.delete')) + '" title="' + esc(t('pr.delete')) + '">✕</button></div>';
  });
  h += '</div>';
  let nMine = 0;
  PAYLOAD_TYPES.forEach(ty => { nMine += (LIB.mine[ty] || []).length; });
  h += '<div class="fc-h">' + esc(tf('pr.mine', nMine)) + '</div><div class="fc-lib">';
  if (!nMine && !LIB.files.length) h += '<p class="pk-note">' + esc(t('pr.none')) + '</p>';
  PAYLOAD_TYPES.forEach(ty => (LIB.mine[ty] || []).forEach((p, i) => {
    h += '<div class="fc-file"><span class="fc-file-n">★ ' + esc(p.displayName || p.name) + '</span><span class="snap-flight-tag">' + esc(TYPE_LABEL[ty]) + '</span>'
      + '<button type="button" class="pk-x" data-act="rm-mine" data-ty="' + esc(ty) + '" data-i="' + i + '" aria-label="' + esc(t('pr.delete')) + '" title="' + esc(t('pr.delete')) + '">✕</button></div>';
  }));
  h += '</div>';
  if (nMine) {
    h += '<p class="pk-note">' + esc(t('pr.export.hint')) + '</p><div class="miz-btn-row" style="margin-top:0">';
    PAYLOAD_TYPES.forEach(ty => { if ((LIB.mine[ty] || []).length) h += '<button type="button" class="miz-btn" data-act="export-lua" data-ty="' + esc(ty) + '">' + esc(tf('pr.export', ty)) + '</button>'; });
    h += '</div>';
  }
  return h + '</div></section>';
}
function exportLua(ty) {
  const obj = { unitType: ty, name: PAYLOAD_FILE_NAME[ty], presets: [] };
  LIB.files.forEach(fl => {
    if (fl.parsed.unitType !== ty) return;
    obj.name = fl.parsed.name;
    if (fl.parsed.tasks) obj.tasks = fl.parsed.tasks;
    fl.parsed.presets.forEach(p => obj.presets.push(p));
  });
  (LIB.mine[ty] || []).forEach(p => obj.presets.push(p));
  download(serializeUnitPayloads(obj), ty + '.lua', 'text/plain');
}
async function loadLuaFiles(files) {
  LIB.errors = [];
  for (const file of files) {
    let txt = '';
    try { txt = await file.text(); } catch (e) { LIB.errors.push(file.name); continue; }
    try { LIB.files.push({ name: file.name, parsed: parseUnitPayloads(txt) }); }
    catch (e) { LIB.errors.push(tf('pr.err', file.name, e.line || '?', t('err.code.' + (e.code || '')))); }
  }
  renderRight();
}

// ---------- fichiers ----------
function download(text, fname, mime) {
  const blob = new Blob([text], { type: mime || 'text/plain' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = fname;
  document.body.appendChild(a); a.click(); document.body.removeChild(a);
  setTimeout(() => URL.revokeObjectURL(url), 2000);
}
// Un fichier JSON : { parsed, zip } ou { reject } (la clé du message). Un .zip porte un package.json à la racine (« PK » en tête).
function readJsonFile(file, done) {
  const reader = new FileReader();
  reader.onload = () => {
    const bytes = new Uint8Array(reader.result);
    const parse = (text, zip) => {
      if (text.charCodeAt(0) === 0xFEFF) text = text.slice(1);
      let parsed;
      try { parsed = JSON.parse(text); } catch (e) { done({ reject: 'rej.json' }); return; }
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
function rejectFormat(parsed, kinds) {
  const f = isObj(parsed) ? (parsed.format || parsed.schema) : undefined;
  const x = ((typeof f === 'string' && f !== '') || typeof f === 'number') ? String(f) : t('rej.unknown');
  showToast(tf('rej.format', x, kinds.map(k => t('fmt.' + k)).join(', ')), 5000);
}

// « Ouvrir » : un fichier de travail (clé fc) ou un paquet de vol ; il remplace le contenu du module
function openFile(file) {
  readJsonFile(file, r => {
    if (r.reject) { showToast(t(r.reject), 5000); return; }
    const o = r.parsed;
    if (isObj(o) && isObj(o.fc) && isObj(o.fc.state) && restoreState(o.fc.state)) {
      if (isObj(o.fc.mine)) PAYLOAD_TYPES.forEach(ty => {
        (Array.isArray(o.fc.mine[ty]) ? o.fc.mine[ty] : []).forEach(p => {
          if (isObj(p) && isObj(p.pylons) && !(LIB.mine[ty] || []).some(q => q.name === p.name)) (LIB.mine[ty] = LIB.mine[ty] || []).push(p);
        });
      });
      saveMine();
    } else if (isObj(o) && o.format === PACKAGE_FORMAT) {
      const res = impReadPackage(o, file.name);
      if (res.reject) { showToast(t(res.reject), 5000); return; }
      S.flights = []; S.theatre = res.src.theatre; S.sel = { f: 0, u: 0 };
      impMerge(res.src.flights.filter(f => f.supported).map(f => ({ f: f, chk: { route: true, radios: true, loadout: true, livery: true } })));
    } else { showToast(t('open.bad'), 5000); return; }
    UI.cmp.saving = false;
    renderAll();
    showToast(tf('open.done', S.flights.length));
  });
}
function saveFile() {
  const name = packageFileName('fc');
  download(JSON.stringify(buildWorkFile(), null, 1), name, 'application/json');
  showToast(tf('save.done', name));
}
function exportFile() {
  if (exportIssues().length) { refreshBar(); return; }
  const name = packageFileName();
  download(JSON.stringify(buildPackage(), null, 1), name, 'application/json');
  showToast(tf('export.done', name));
}
function clearAll() {
  if (!confirm(t('clear.confirm'))) return;
  S.theatre = ''; S.flights = []; S.sel = { f: 0, u: 0 };
  UI.cmp.saving = false;
  renderAll();
}

// =============================================================
//  IMPORT — par source (comme au Datacard Generator) ; par vol, quatre cases comme HQ : Route, Radios, Emport, Livrée
// =============================================================
function impFlight(f) {
  if (!isObj(f) || typeof f.groupName !== 'string' || typeof f.aircraftType !== 'string') return null;
  const points = (isObj(f.route) && isObj(f.route.points) && routeKeys(f.route.points).length) ? f.route.points : null;
  const units = (Array.isArray(f.units) ? f.units : []).filter(isObj);
  const supported = PAYLOAD_TYPES.indexOf(f.aircraftType) >= 0;
  const out = { groupName: f.groupName, aircraftType: f.aircraftType, coalition: (f.coalition === 'blue' || f.coalition === 'red') ? f.coalition : '', supported: supported, points: points, units: units };
  const hasRadios = units.some(u => Array.isArray(u.radios) && u.radios.some(r => isObj(r) && isObj(r.channels) && Object.keys(r.channels).length));
  out.avail = {
    route: !!points && supported,
    radios: hasRadios && supported,
    loadout: supported && units.some(u => isObj(u.payload) && isObj(u.payload.pylons)),
    livery: units.some(u => typeof u.liveryId === 'string' && u.liveryId !== '') && supported
  };
  return out;
}
function impSource(kind, theatre, file, list) {
  const flights = list.map(impFlight).filter(Boolean);
  flights.forEach(f => { f.on = f.supported; f.chk = { route: f.avail.route, radios: f.avail.radios, loadout: f.avail.loadout, livery: f.avail.livery }; });
  return { kind: kind, theatre: theatre, file: file, flights: flights, skipped: list.length - flights.length };
}
function impReadPackage(o, fname) {
  if (typeof o.theatre !== 'string' || o.theatre === '') return { reject: 'rej.noTheatre' };
  const src = impSource('pkg', o.theatre, fname || '', Array.isArray(o.flights) ? o.flights : []);
  if (!src.flights.length) return { reject: 'rej.noFlight' };
  return { src: src };
}
function impReadSnapshot(o, fname) {
  if (!isObj(o) || o.schema !== SNAPSHOT_SCHEMA || !isObj(o.sourceMission) || typeof o.sourceMission.theatre !== 'string' || !Array.isArray(o.flights)) return { reject: 'fmt' };
  const src = impSource('snap', o.sourceMission.theatre, str(o.sourceMission.filename) || fname || '', o.flights);
  if (!src.flights.length) return { reject: 'rej.noFlight' };
  return { src: src };
}
function impReadHq() {
  let o = null;
  try { o = JSON.parse(lsGet(KEY_SNAPSHOT) || 'null'); } catch (e) { o = null; }
  const r = impReadSnapshot(o, '');
  return r.src || null;
}
function impOpen() {
  UI.imp = { src: '', hq: impReadHq(), pkg: null, snap: null };
  UI.imp.src = UI.imp.hq ? 'hq' : '';
  renderImport();
  const m = document.getElementById('imp-modal');
  m.hidden = false;
  const first = m.querySelector('input[type=radio]:not(:disabled)');
  if (first) first.focus();
}
function impClose() { document.getElementById('imp-modal').hidden = true; UI.imp = null; }
function impCur() { const I = UI.imp; return I && I.src ? I[I.src] : null; }

function renderImport() {
  const I = UI.imp;
  if (!I) return;
  const row = (id, label, extra, off) => '<label class="imp-src' + (off ? ' off' : '') + '"><input type="radio" name="imp-src" value="' + id + '"' + (I.src === id ? ' checked' : '') + (off ? ' disabled' : '') + '><span>' + esc(label) + '</span></label>' + (extra || '');
  let h = '<div class="imp-block"><h3>' + esc(t('imp.src')) + '</h3>';
  h += row('hq', t('imp.src.hq'), '<div class="imp-note">' + esc(I.hq ? tf('imp.hq.ok', I.hq.file, I.hq.theatre) : t('imp.hq.none')) + '</div>', !I.hq);
  h += row('pkg', t('imp.src.pkg'), '<div class="imp-file"><button type="button" class="imp-filebtn" data-act="imp-pick-pkg">' + esc(t('imp.choose')) + '</button><span class="imp-filename">' + esc(I.pkg ? I.pkg.file : '') + '</span></div><div class="imp-note">' + esc(t('imp.pkg.note')) + '</div>');
  h += row('snap', t('imp.src.snap'), '<div class="imp-file"><button type="button" class="imp-filebtn" data-act="imp-pick-snap">' + esc(t('imp.choose')) + '</button><span class="imp-filename">' + esc(I.snap ? I.snap.file : '') + '</span></div><div class="imp-note">' + esc(t('imp.snap.note')) + '</div>');
  [['rp', 'imp.src.rp'], ['bg', 'imp.src.bg'], ['dg', 'imp.src.dg']].forEach(s => { h += row(s[0], t(s[1]), '<div class="imp-note">' + esc(t('imp.soon')) + '</div>', true); });
  h += '</div>';
  const cur = impCur();
  h += '<div class="imp-block"><h3>' + esc(t('imp.flights')) + '</h3>';
  if (!cur) h += '<p class="imp-note" style="margin-left:0">' + esc(t('imp.none')) + '</p>';
  else {
    if (cur.skipped) h += '<div class="imp-note" style="margin-left:0">⚠ ' + esc(tf('rej.skip', cur.skipped)) + '</div>';
    h += '<div class="imp-list" id="imp-list">';
    cur.flights.forEach((f, i) => {
      const ex = S.flights.some(x => x.name.trim() === f.groupName && x.type === f.aircraftType && x.coalition === f.coalition);
      h += '<div class="imp-flight' + (f.supported ? '' : ' off') + '"><label class="imp-fh"><input type="checkbox" data-imp-flight="' + i + '"' + (f.on && f.supported ? ' checked' : '') + (f.supported ? '' : ' disabled') + '>'
        + '<span class="imp-nm">' + esc(f.groupName) + '</span><span class="snap-flight-tag">' + esc(f.aircraftType) + '</span>'
        + '<span class="imp-n">' + esc(f.supported ? (ex ? t('imp.exists') : t('imp.new')) : t('imp.unsupported')) + ' · ' + esc(tf('imp.units', f.units.length)) + '</span></label><div class="pk-parts">';
      PARTS.forEach(p => {
        const on = f.supported && f.avail[p];
        h += '<label class="pk-chk' + (on ? '' : ' off') + '"><input type="checkbox" data-imp-part="' + p + '" data-imp-i="' + i + '"' + ((on && f.chk[p]) ? ' checked' : '') + (on ? '' : ' disabled') + '>' + esc(t('imp.part.' + p)) + '</label>';
      });
      h += '</div></div>';
    });
    h += '</div>';
    if (S.flights.length && S.theatre && S.theatre !== cur.theatre) h += '<div class="imp-note" style="margin-left:0">' + esc(tf('imp.theatre.keep', S.theatre, cur.theatre)) + '</div>';
    else if (!S.theatre || !S.flights.length) h += '<div class="imp-note" style="margin-left:0">' + esc(tf('imp.theatre.set', cur.theatre)) + '</div>';
  }
  h += '</div>';
  document.getElementById('imp-body').innerHTML = h;
  const go = document.getElementById('imp-go');
  go.disabled = !(cur && cur.flights.some(f => f.on && f.supported));
}
// Applique les vols choisis : [{ f, chk }] ; un vol du module de même (nom, appareil, coalition) est complété par les parties cochées, sinon il est créé.
function impMerge(list) {
  let n = 0;
  list.forEach(({ f, chk }) => {
    let tg = S.flights.filter(x => x.name.trim() === f.groupName && x.type === f.aircraftType && x.coalition === f.coalition)[0];
    const created = !tg;
    if (created) { tg = newFlight(); tg.name = f.groupName; tg.type = f.aircraftType; tg.coalition = f.coalition; tg.units = []; S.flights.push(tg); }
    if (chk.route && f.points) tg.route = { points: clone(f.points) };
    f.units.slice(0, 4).forEach((iu, k) => {
      let u = tg.units[k];
      if (!u) {
        u = newUnit(); tg.units.push(u);
        u.name = str(iu.name);
        u.csRaw = iu.callsign; u.callsign = csText(iu.callsign);
        u.onboard = (typeof iu.onboardNum === 'string' || typeof iu.onboardNum === 'number') ? String(iu.onboardNum) : '';
      }
      if (chk.livery && typeof iu.liveryId === 'string') u.livery = iu.liveryId;
      if (chk.radios && Array.isArray(iu.radios)) {
        iu.radios.forEach(r => {
          if (!isObj(r) || !isObj(r.channels) || !has(RADIO_CHANNELS[tg.type], r.radioIndex)) return;
          const post = {};
          Object.keys(r.channels).forEach(c => { const v = r.channels[c]; if (/^\d+$/.test(c) && Number(c) >= 1 && Number(c) <= RADIO_CHANNELS[tg.type][r.radioIndex] && typeof v === 'number' && isFinite(v)) post[c] = String(v); });
          if (Object.keys(post).length) u.radios[r.radioIndex] = post;
        });
      }
      if (chk.loadout) { const lo = loadoutFromPayload(tg.type, iu.payload); if (lo) u.loadout = lo; }
    });
    if (!tg.units.length) tg.units.push(newUnit());
    n++;
  });
  return n;
}
function impGo() {
  const cur = impCur();
  if (!cur) return;
  const picked = cur.flights.filter(f => f.on && f.supported).map(f => ({ f: f, chk: f.chk }));
  if (!picked.length) return;
  if (!S.theatre || !S.flights.length) S.theatre = cur.theatre;
  const n = impMerge(picked);
  const firstNew = S.flights.length - 1;
  S.sel = { f: Math.max(0, Math.min(firstNew, S.sel.f)), u: 0 };
  if (!selUnit()) S.sel = { f: 0, u: 0 };
  impClose();
  renderAll();
  showToast(tf('imp.done', n));
}
function impFile(file, kind) {
  readJsonFile(file, r => {
    if (r.reject) { showToast(t(r.reject), 5000); return; }
    const o = r.parsed;
    if (kind === 'pkg') {
      if (!isObj(o) || o.format !== PACKAGE_FORMAT) { rejectFormat(o, ['pkg']); return; }
      const res = impReadPackage(o, file.name);
      if (res.reject) { showToast(t(res.reject), 5000); return; }
      UI.imp.pkg = res.src; UI.imp.src = 'pkg';
    } else {
      const res = impReadSnapshot(o, file.name);
      if (res.reject === 'fmt') { rejectFormat(o, ['snap']); return; }
      if (res.reject) { showToast(t(res.reject), 5000); return; }
      UI.imp.snap = res.src; UI.imp.src = 'snap';
    }
    renderImport();
  });
}

// =============================================================
//  actions et événements
// =============================================================
function showToast(msg, ms) {
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.classList.add('show');
  clearTimeout(showToast._h);
  showToast._h = setTimeout(() => el.classList.remove('show'), ms || 2400);
}
function renderAll() { renderLeft(); renderRight(); refreshBar(); applyI18nStatic(); saveWork(); }
function selectUnit(fi, ui, scroll) {
  if (S.sel.f === fi && S.sel.u === ui && !scroll) return;
  const changed = !(S.sel.f === fi && S.sel.u === ui);
  S.sel = { f: fi, u: ui };
  document.querySelectorAll('#col-left .fc-unit').forEach(e => {
    const fe = e.closest('.fc-flight');
    e.classList.toggle('sel', Number(fe.getAttribute('data-f')) === fi && Number(e.getAttribute('data-u')) === ui);
  });
  if (changed) { UI.cmp.saving = false; UI.cmp.err = ''; UI.cmp.st = null; renderRight(); saveWork(); }
  if (scroll) { const b = document.getElementById('blk-cmp'); if (b && b.scrollIntoView && window.innerWidth < 1100) b.scrollIntoView({ block: 'start', behavior: 'smooth' }); }
}

function onClick(e) {
  const b = e.target.closest ? e.target.closest('[data-act]') : null;
  if (!b || b.disabled) return;
  const act = b.getAttribute('data-act');
  const fEl = b.closest('.fc-flight'), fi = fEl ? Number(fEl.getAttribute('data-f')) : -1;
  const uEl = b.closest('.fc-unit'), ui = uEl ? Number(uEl.getAttribute('data-u')) : (b.hasAttribute('data-u') ? Number(b.getAttribute('data-u')) : -1);
  if (act === 'add-flight') { S.flights.push(newFlight()); S.sel = { f: S.flights.length - 1, u: 0 }; renderAll(); }
  else if (act === 'rm-flight') { S.flights.splice(fi, 1); if (!selUnit()) S.sel = { f: 0, u: 0 }; renderAll(); }
  else if (act === 'add-unit') { S.flights[fi].units.push(newUnit()); renderLeft(); refreshAll(); }
  else if (act === 'rm-unit') { S.flights[fi].units.splice(ui, 1); if (!selUnit()) S.sel = { f: Math.min(S.sel.f, S.flights.length - 1), u: 0 }; renderAll(); }
  else if (act === 'rm-route') { S.flights[fi].route = null; renderLeft(); refreshAll(); }
  else if (act === 'copy-radios') {
    const f = S.flights[fi], src = f.units[ui].radios;
    f.units.forEach((u, k) => { if (k !== ui) u.radios = clone(src); });
    renderLeft(); refreshAll();
  }
  else if (act === 'sel-unit') selectUnit(fi, ui, true);
  else if (act === 'cmp-save') { UI.cmp.saving = true; UI.cmp.err = ''; UI.cmp.name = ''; renderRight(); const i = document.querySelector('#blk-cmp input[data-k="cmp-name"]'); if (i) i.focus(); }
  else if (act === 'cmp-save-cancel') { UI.cmp.saving = false; renderRight(); }
  else if (act === 'cmp-save-go') cmpSaveGo();
  else if (act === 'cmp-clear') { const su = selUnit(); if (su) { su.u.loadout = null; UI.cmp.saving = false; renderRight(); refreshUnitSummaries(); refreshAll(); } }
  else if (act === 'load-lua') document.getElementById('fc-in-lua').click();
  else if (act === 'rm-file') { LIB.files.splice(Number(b.getAttribute('data-i')), 1); renderRight(); }
  else if (act === 'rm-mine') { (LIB.mine[b.getAttribute('data-ty')] || []).splice(Number(b.getAttribute('data-i')), 1); saveMine(); renderRight(); }
  else if (act === 'export-lua') exportLua(b.getAttribute('data-ty'));
  else if (act === 'imp-pick-pkg') document.getElementById('fc-in-pkg').click();
  else if (act === 'imp-pick-snap') document.getElementById('fc-in-snap').click();
}

function onInput(e) {
  const el = e.target, k = el.getAttribute && el.getAttribute('data-k');
  if (!k) return;
  if (k === 'cmp-name') { UI.cmp.name = el.value; return; }
  const fEl = el.closest('.fc-flight'), fi = fEl ? Number(fEl.getAttribute('data-f')) : -1;
  const f = S.flights[fi];
  const ui = el.hasAttribute('data-u') ? Number(el.getAttribute('data-u')) : -1;
  const u = f && ui >= 0 ? f.units[ui] : null;
  if (k === 'name') { f.name = el.value; const ft = fEl.querySelector('.fc-ftitle'); if (ft) ft.textContent = flightLabel(f, fi); }
  else if (k === 'uname') u.name = el.value;
  else if (k === 'callsign') u.callsign = el.value;
  else if (k === 'onboard') u.onboard = el.value;
  else if (k === 'livery') u.livery = el.value;
  else if (k === 'chan') {
    const r = Number(el.getAttribute('data-r')), c = Number(el.getAttribute('data-c'));
    (u.radios[r] = u.radios[r] || {})[c] = el.value;
    paintRadioMsg(fi, ui, r); refreshUnitSummaries();
  }
  else if (k === 'fuel' || k === 'flare' || k === 'chaff' || k === 'gun') {
    const su = selUnit();
    if (su && su.u.loadout) { su.u.loadout[k] = el.value; paintLoadoutMsg(); }
  }
  refreshAll();
}

function onChange(e) {
  const el = e.target, k = el.getAttribute && el.getAttribute('data-k');
  if (el.id === 'cmp-from') { cmpBase(el.value); return; }
  if (el.id === 'cmp-sym') { UI.cmp.sym = el.checked; return; }
  if (el.classList && el.classList.contains('cmp-sel')) { cmpChoose(el.getAttribute('data-st'), el.value); return; }
  if (!k) return;
  if (k === 'theatre') { S.theatre = el.value; refreshAll(); return; }
  const fEl = el.closest('.fc-flight'), fi = fEl ? Number(fEl.getAttribute('data-f')) : -1;
  const f = S.flights[fi];
  if (k === 'type') {
    f.type = el.value;
    f.units.forEach(u => { u.radios = {}; u.loadout = null; });
    renderAll();
  }
  else if (k === 'coalition') { f.coalition = el.value; refreshAll(); }
}

function onToggle(e) {
  const d = e.target;
  if (!d || !d.getAttribute || d.tagName !== 'DETAILS') return;
  const key = d.getAttribute('data-key');
  if (!key) return;
  if (d.open) { UI.open.add(key); UI.open.delete('~' + key); } else { UI.open.delete(key); UI.open.add('~' + key); }
}

function onFocusIn(e) {
  const ue = e.target.closest ? e.target.closest('.fc-unit') : null;
  if (!ue) return;
  const fe = ue.closest('.fc-flight');
  selectUnit(Number(fe.getAttribute('data-f')), Number(ue.getAttribute('data-u')), false);
}
function onRightClick(e) {
  const cell = e.target.closest ? e.target.closest('.cmp-st') : null;
  if (cell) { UI.cmp.st = cell.getAttribute('data-st'); cmpUpdate(); }
}

// ---------- barre, langue, thème ----------
function loadTheme() {
  const saved = lsGet(KEY_THEME) || 'cw-nato';
  document.body.setAttribute('data-theme', saved);
  const sel = document.getElementById('theme-select');
  if (sel) sel.value = saved;
}
function loadLang() {
  const saved = lsGet(KEY_LANG);
  CURRENT_LANG = (saved === 'fr' || saved === 'en') ? saved : ((navigator.language || 'fr').startsWith('fr') ? 'fr' : 'en');
  document.documentElement.lang = CURRENT_LANG;
}
function applyI18nStatic() {
  document.querySelectorAll('[data-i18n]').forEach(el => { el.textContent = t(el.getAttribute('data-i18n')); });
  document.querySelectorAll('[data-i18n-title]').forEach(el => { el.title = t(el.getAttribute('data-i18n-title')); });
  const b = document.getElementById('btn-lang');
  if (b) { b.textContent = CURRENT_LANG === 'fr' ? '🇬🇧' : '🇫🇷'; b.title = t('toolbar.lang.tooltip'); }
  ['open', 'save', 'import', 'export', 'clear'].forEach(k => { const e = document.getElementById('btn-' + k); if (e) e.setAttribute('aria-label', t('tb.' + k)); });
}

function initEvents() {
  const left = document.getElementById('col-left'), right = document.getElementById('col-right');
  [left, right].forEach(root => {
    root.addEventListener('click', onClick);
    root.addEventListener('input', onInput);
    root.addEventListener('change', onChange);
    root.addEventListener('toggle', onToggle, true);
  });
  left.addEventListener('focusin', onFocusIn);
  right.addEventListener('click', onRightClick);
  right.addEventListener('focusin', e => {
    const row = e.target.closest ? e.target.closest('.cmp-row') : null;
    if (row && UI.cmp.st !== row.getAttribute('data-st')) { UI.cmp.st = row.getAttribute('data-st'); cmpUpdate(); }
  });
  document.getElementById('theme-select').addEventListener('change', e => {
    document.body.setAttribute('data-theme', e.target.value);
    lsSet(KEY_THEME, e.target.value);
  });
  document.getElementById('btn-lang').addEventListener('click', () => {
    CURRENT_LANG = CURRENT_LANG === 'fr' ? 'en' : 'fr';
    lsSet(KEY_LANG, CURRENT_LANG);
    document.documentElement.lang = CURRENT_LANG;
    if (UI.imp) renderImport();
    renderAll();
  });
  document.getElementById('btn-open').addEventListener('click', () => document.getElementById('fc-in-open').click());
  document.getElementById('btn-save').addEventListener('click', saveFile);
  document.getElementById('btn-import').addEventListener('click', impOpen);
  document.getElementById('btn-export').addEventListener('click', exportFile);
  document.getElementById('btn-clear').addEventListener('click', clearAll);
  const fileIn = (id, fn) => document.getElementById(id).addEventListener('change', e => { const fl = Array.prototype.slice.call(e.target.files); e.target.value = ''; fn(fl); });
  fileIn('fc-in-lua', loadLuaFiles);
  fileIn('fc-in-open', fl => { if (fl[0]) openFile(fl[0]); });
  fileIn('fc-in-pkg', fl => { if (fl[0]) impFile(fl[0], 'pkg'); });
  fileIn('fc-in-snap', fl => { if (fl[0]) impFile(fl[0], 'snap'); });
  // fenêtre d'import
  const m = document.getElementById('imp-modal');
  document.getElementById('imp-modal-backdrop').addEventListener('click', impClose);
  document.getElementById('imp-modal-close').addEventListener('click', impClose);
  document.getElementById('imp-cancel').addEventListener('click', impClose);
  document.getElementById('imp-go').addEventListener('click', impGo);
  m.addEventListener('click', onClick);
  m.addEventListener('change', e => {
    const el = e.target, I = UI.imp;
    if (!I) return;
    if (el.name === 'imp-src') { I.src = el.value; renderImport(); return; }
    const cur = impCur();
    if (!cur) return;
    if (el.hasAttribute('data-imp-flight')) { cur.flights[Number(el.getAttribute('data-imp-flight'))].on = el.checked; renderImport(); }
    else if (el.hasAttribute('data-imp-part')) { cur.flights[Number(el.getAttribute('data-imp-i'))].chk[el.getAttribute('data-imp-part')] = el.checked; }
  });
  document.addEventListener('keydown', e => { if (e.key === 'Escape' && UI.imp) impClose(); });
}

function init() {
  loadTheme();
  loadLang();
  try { const w = JSON.parse(lsGet(KEY_STATE) || 'null'); if (isObj(w) && w.v === 1) { loadMine(w); restoreState(w.state); } } catch (e) { /* l'écran marche sans */ }
  initToolbarMenus([['theme-select', () => t('toolbar.theme.tooltip')]]);
  initFormMenus(sel => sel.getAttribute('aria-label') || '');
  initEvents();
  renderAll();
}
init();
"""

FONTS = """
@font-face { font-family: 'Roboto Mono'; font-weight: 400; font-display: swap; src: url('data:font/woff2;base64,@@ROBOTO_MONO_400@@') format('woff2'); }
@font-face { font-family: 'Stardos Stencil'; font-weight: 700; font-display: swap; src: url('data:font/woff2;base64,@@STARDOS_700@@') format('woff2'); }
@font-face { font-family: 'Oswald'; font-weight: 500; font-display: swap; src: url('data:font/woff2;base64,@@OSWALD_500@@') format('woff2'); }
"""


def tables_js():
    """Les quatre tables de data/, recopiées telles quelles entre leurs marqueurs : `const NOM = <fichier>;`."""
    out = ''
    for name, fn in TABLES:
        with open(os.path.join(HERE, 'data', fn), encoding='utf-8', newline='') as f:
            txt = f.read()
        assert '</script' not in txt.lower()
        out += '/* %s:BEGIN */\nconst %s = %s;\n/* %s:END */\n' % (name, name, txt.rstrip('\n'), name)
    return out


def build_html():
    fonts = (FONTS.replace('@@ROBOTO_MONO_400@@', A['ROBOTO_MONO_400'])
                  .replace('@@STARDOS_700@@', A['STARDOS_700'])
                  .replace('@@OSWALD_500@@', A['OSWALD_500']))
    js = build_radio_block() + '\n' + tables_js() + '\n' + build_payload_block() + '\n' + JS_TBM + '\n' + JS_FC
    return ('<!DOCTYPE html>\n<html lang="fr">\n<head>\n<meta charset="UTF-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0, viewport-fit=cover">\n'
            '<meta name="theme-color" content="#1a1e10">\n<title>Flight Configurator</title>\n<style>\n'
            + fonts + CSS_COMMON + CSS_FC + '\n</style>\n'
            '<!-- JSZip v3.10.1 — embarqué pour lire un paquet .zip -->\n<script>' + A['lib_jszip'] + '</script>\n</head>\n'
            + BODY.replace('@@VERSION@@', APP_VERSION) + '\n<script>\n' + js + '\n</script>\n</body>\n</html>\n')


def main():
    html = build_html()
    out = os.path.join(HERE, 'dist', 'dcs_flight_configurator.html')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, 'w', encoding='utf-8', newline='\n') as f:
        f.write(html)
    print('[OK] dcs_flight_configurator.html written (%d KB)' % (os.path.getsize(out) // 1024))
    check(html)


def check(html):
    """Vérifications du build : parité FR/EN, clés de texte, tables égales à leurs fichiers, syntaxe des scripts, aucune requête réseau, graisses."""
    bad = 0

    def ok(cond, label):
        nonlocal bad
        print('  [%s] %s' % ('OK' if cond else 'ÉCHEC', label))
        if not cond:
            bad += 1

    m = re.search(r"const I18N = \{\s*fr: \{(.*?)\n  \},\s*en: \{(.*?)\n  \}\s*\};", html, re.S)
    ok(bool(m), 'dictionnaires FR et EN présents')
    if m:
        keys = lambda s: re.findall(r"^\s*'([^']+)':|, '([^']+)':", s, re.M)
        kfr = {a or b for a, b in keys(m.group(1))}
        ken = {a or b for a, b in keys(m.group(2))}
        ok(kfr == ken, 'parité FR/EN : %d clés, écart %s' % (len(kfr), sorted(kfr ^ ken)))
        used = set(re.findall(r"\bt(?:f)?\('([a-zA-Z0-9_.\-]+)'", html)) | set(re.findall(r'data-i18n(?:-title)?="([^"]+)"', html))
        used |= set(re.findall(r"key: '([a-z]+\.[a-zA-Z0-9_.]+)'", html))
        used = {k for k in used if not k.startswith('err.code.') and not k.endswith('.')}
        used |= {'tb.' + k + s for k in ('open', 'save', 'import', 'export', 'clear') for s in ('', '.s', '.tip')}
        ok(used <= kfr, 'toute clé de texte utilisée existe : manque %s' % sorted(used - kfr))
    # les quatre tables : la copie de la page égale le fichier de data/
    for name, fn in TABLES:
        mm = re.search(r'/\* %s:BEGIN \*/\nconst %s = (.*);\n/\* %s:END \*/' % (name, name, name), html, re.S)
        with open(os.path.join(HERE, 'data', fn), encoding='utf-8', newline='') as f:
            txt = f.read().rstrip('\n')
        ok(bool(mm) and mm.group(1) == txt, 'table %s égale à data/%s' % (name, fn))
    scripts = re.findall(r'<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>', html, re.S)
    for i, s in enumerate(scripts):
        tmp = os.path.join(HERE, '.fc_check_%d.js' % i)
        with open(tmp, 'w', encoding='utf-8') as f:
            f.write(s)
        r = subprocess.run(['node', '--check', tmp], capture_output=True, text=True)
        os.remove(tmp)
        ok(r.returncode == 0, 'node --check du script %d%s' % (i + 1, '' if r.returncode == 0 else ' : ' + r.stderr[:300]))
    own = html.replace(A['lib_jszip'], '')
    ok(not re.search(r'fetch\(|XMLHttpRequest|WebSocket|sendBeacon|<script[^>]*\bsrc=|<link[^>]*href=["\']http', own), 'aucune requête réseau (hors JSZip, qui n\'en fait pas)')
    ok(not re.search(r'font-weight:\s*(600|800|900|bold)|font:\s*(600|800|900|bold)\b', own), 'aucune graisse sans sa face (R295)')
    ok('/* ===== POSTES RADIO (COMME AU COCKPIT) ===== */' in html and '/* ===== EMPORT (PRESETS ET PAYLOAD) ===== */' in html, 'blocs partagés présents')
    if bad:
        sys.exit(1)


if __name__ == '__main__':
    main()
