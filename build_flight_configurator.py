#!/usr/bin/env python3
"""Build the Flight Configurator HTML module : un vol (identité, radios, emport, livrée) et son paquet `dcs-flight-package-v1`.

Produit dist/dcs_flight_configurator.html (fichier autonome, hors-ligne, aucune requête réseau).
Usage : python3 -B build_flight_configurator.py

Blocs partagés insérés tels quels (identiques à l'octet dans les modules qui les utilisent) :
  radio_block.py    — noms des postes radio et numéros de canal du cockpit
  payload_block.py  — presets d'emport (UnitPayloads), catalogue des armes (weapons_catalogue.json), `payload` d'un .miz
"""

import base64
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
body[data-theme] { --pk-warn: var(--red-faded); --pk-ok: #7fa062; }
body[data-theme="cw-soviet"], body[data-theme="modern-nato"], body[data-theme="modern-east"] { --pk-warn: #e8b840; }  /* --red-faded y est trop sombre sur le fond de la page */

.editor { max-width: 980px; }
.ed-field input[type=text] { min-width: 0; }
.ed-field input[type=text].bad { border-color: var(--pk-warn); border-left-color: var(--pk-warn); }
.fc-row { display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 10px; align-items: end; }
.fc-row > * { min-width: 0; }
.fc-fname { font-family: var(--f-typewriter); font-size: 12px; color: var(--paper); min-height: 44px; display: flex; align-items: center; word-break: break-all; padding: 0 2px; }
.pk-note { font-family: var(--f-typewriter); font-size: 11px; color: var(--khaki-light); margin: 0; }
.pk-warn { font-family: var(--f-typewriter); font-size: 11px; color: var(--pk-warn); margin-top: 6px; word-break: break-word; }
.snap-flight-tag {
  font-family: var(--f-ui); font-size: 10px; padding: 2px 6px; border-radius: 2px;
  background: var(--olive); color: var(--paper-light); text-transform: uppercase; letter-spacing: 1px; white-space: nowrap;
}
.pk-x {
  flex: none; min-width: 36px; min-height: 36px; background: none; border: 0; color: var(--khaki-light); font-size: 16px; cursor: pointer;
}
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
.fc-ed-py .fc-sel.tbm-trigger.tbm-field { display: flex; align-items: center; line-height: 1.25; padding-top: 6px; padding-bottom: 6px; }
.fc-ed-py .fc-sel.tbm-trigger.tbm-field .tbm-lbl { line-height: 1.25; white-space: normal; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; text-overflow: clip; }
.tbm-panel.tbm-p-field .tbm-opt { white-space: normal; line-height: 1.3; padding-top: 8px; padding-bottom: 8px; word-break: break-word; }
.fc-sel.tbm-trigger.tbm-field:focus { outline: none; border-left-color: var(--red-stamp); box-shadow: 0 0 0 1px var(--amber); }
.fc-sel.tbm-trigger.tbm-field:disabled { opacity: .5; cursor: default; }

/* un vol */
.fc-list { display: flex; flex-direction: column; gap: 12px; }
.fc-flight { border: 1px solid var(--khaki); border-radius: 3px; padding: 10px 12px 12px; background: rgba(0,0,0,.15); }
.fc-fhead, .fc-uhead { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin-bottom: 8px; }
.fc-fhead .pk-x, .fc-uhead .pk-x { margin-left: auto; margin-right: -8px; }
.fc-ftitle { font-family: var(--f-stencil); font-size: 13px; letter-spacing: 1.5px; color: var(--amber); text-transform: uppercase; }
.fc-units { display: flex; flex-direction: column; gap: 10px; margin-top: 12px; }
.fc-unit { border: 1px solid rgba(128,116,84,.55); border-left: 3px solid var(--amber-dark); padding: 8px 10px 10px; background: rgba(0,0,0,.12); }
.fc-uhead { margin-bottom: 6px; }
.fc-utitle { font-family: var(--f-stencil); font-size: 12px; letter-spacing: 1px; color: var(--paper); text-transform: uppercase; }
.fc-row4 { display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 10px; }
.fc-row4 > * { min-width: 0; }
.fc-sub { margin-top: 10px; border-top: 1px solid rgba(128,116,84,.45); }
.fc-sub > summary {
  cursor: pointer; list-style: none; display: flex; align-items: center; gap: 8px; min-height: 40px; user-select: none;
  font-family: var(--f-stencil); font-size: 12px; letter-spacing: 1.5px; color: var(--amber); text-transform: uppercase;
}
.fc-sub > summary::-webkit-details-marker { display: none; }
.fc-sub > summary::before { content: '\25ba'; font-size: 8px; color: var(--rust); transition: transform .2s; }
.fc-sub[open] > summary::before { transform: rotate(90deg); }
.fc-sub > summary .fc-sum { font-family: var(--f-typewriter); font-size: 11px; letter-spacing: 0; text-transform: none; color: var(--khaki-light); min-width: 0; word-break: break-word; }
.fc-sub > .fc-subc { padding: 2px 0 6px; display: flex; flex-direction: column; gap: 10px; }
.fc-post { border: 1px solid rgba(128,116,84,.4); background: rgba(0,0,0,.12); }
.fc-post > summary {
  cursor: pointer; list-style: none; display: flex; align-items: center; gap: 8px; min-height: 40px; padding: 0 10px; user-select: none;
  font-family: var(--f-ui); font-weight: 500; font-size: 12px; letter-spacing: 1px; color: var(--paper); text-transform: uppercase;
}
.fc-post > summary::-webkit-details-marker { display: none; }
.fc-post > summary::after { content: '\25c4'; margin-left: auto; font-size: 10px; color: var(--paper); transition: transform .2s; }
.fc-post[open] > summary::after { transform: rotate(-90deg); }
.fc-post > summary .fc-sum { font-family: var(--f-typewriter); font-size: 11px; letter-spacing: 0; text-transform: none; color: var(--khaki-light); }
.fc-post > .fc-postc { padding: 4px 10px 10px; }
.fc-chans { display: grid; grid-template-columns: repeat(auto-fill, minmax(112px, 1fr)); gap: 6px 8px; }
.fc-ch { display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.fc-ch > label { font-family: var(--f-ui); font-size: 10px; letter-spacing: 1.2px; text-transform: uppercase; color: var(--khaki-light); }
.fc-ch input {
  background: rgba(216,201,165,.92); border: 1px solid var(--khaki); border-left: 3px solid var(--amber-dark);
  font-family: var(--f-typewriter); font-size: 13px; color: var(--ink); padding: 6px 8px; min-height: 40px; width: 100%; min-width: 0; border-radius: 0;
}
.fc-ch input:focus { outline: none; border-left-color: var(--red-stamp); background: var(--paper-light); box-shadow: 0 0 0 1px var(--amber); }
.fc-ch input.bad { border-color: var(--pk-warn); border-left-color: var(--pk-warn); }
.fc-msg { font-family: var(--f-typewriter); font-size: 11px; color: var(--pk-warn); margin-top: 6px; word-break: break-word; }
.fc-msg:empty { display: none; }

/* l'emport */
.fc-lo-line { display: flex; flex-wrap: wrap; gap: 6px 10px; align-items: center; font-family: var(--f-typewriter); font-size: 11px; color: var(--khaki-light); }
.fc-pylons { display: flex; flex-direction: column; border: 1px solid rgba(128,116,84,.4); }
.fc-py { display: grid; grid-template-columns: 52px minmax(0, 1fr) auto; gap: 8px; align-items: baseline; padding: 6px 10px; }
.fc-py + .fc-py { border-top: 1px solid rgba(128,116,84,.3); }
.fc-py-n { font-family: var(--f-stencil); font-size: 11px; letter-spacing: 1px; color: var(--amber); text-transform: uppercase; }
.fc-py-w { font-family: var(--f-typewriter); font-size: 12px; color: var(--paper); word-break: break-word; min-width: 0; }
.fc-py-w small { display: block; font-size: 10px; color: var(--khaki-light); margin-top: 1px; word-break: break-all; }
.fc-py.empty .fc-py-w { color: var(--khaki-light); opacity: .7; }
.fc-py.unk .fc-py-w { color: var(--pk-warn); }
.fc-chip { font-family: var(--f-ui); font-size: 10px; letter-spacing: 1px; text-transform: uppercase; padding: 1px 6px; border: 1px solid var(--khaki); color: var(--khaki-light); white-space: nowrap; }
.fc-set { display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 8px; }
.fc-set > * { min-width: 0; }
.fc-set .ed-field label { font-size: 10px; letter-spacing: 1.2px; }
.fc-actions .miz-btn { min-height: 44px; width: 100%; justify-content: center; }
.fc-editor { border: 1px solid var(--amber); border-top: 3px solid var(--amber); background: var(--olive-dark); padding: 12px; display: flex; flex-direction: column; gap: 12px; }
.fc-ed-title { font-family: var(--f-stencil); font-size: 13px; letter-spacing: 1.5px; color: var(--amber); text-transform: uppercase; }
.fc-ed-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 8px 14px; }
.fc-ed-py { display: flex; flex-direction: column; gap: 3px; min-width: 0; }
.fc-ed-py > label { font-family: var(--f-ui); font-weight: 500; font-size: 11px; letter-spacing: 1.5px; text-transform: uppercase; color: var(--amber); display: flex; gap: 8px; align-items: baseline; }
.fc-ed-py > small { font-family: var(--f-typewriter); font-size: 10px; color: var(--khaki-light); word-break: break-all; min-height: 14px; }
.fc-ed-py > label .fc-chip { margin-left: auto; }

/* les presets */
.fc-lib { display: flex; flex-direction: column; gap: 6px; }
.fc-file { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; border: 1px solid rgba(128,116,84,.45); padding: 4px 4px 4px 10px; background: rgba(0,0,0,.12); min-height: 44px; }
.fc-file-n { font-family: var(--f-typewriter); font-size: 12px; color: var(--paper); word-break: break-all; min-width: 0; }
.fc-file .pk-x { margin-left: auto; }
.fc-h { font-family: var(--f-stencil); font-size: 11px; letter-spacing: 2px; text-transform: uppercase; color: var(--amber); padding: 8px 0 2px; border-bottom: 1px solid var(--khaki); margin-bottom: 4px; }
.miz-btn { min-height: 44px; }
@media (max-width: 539px) {
  .editor { padding: 14px 10px 80px 10px; }
  .ed-content { padding: 10px; }
  .fc-flight { padding: 8px 8px 10px; }
  .fc-unit { padding: 6px 8px 8px; }
  .fc-py { grid-template-columns: 40px minmax(0, 1fr); }
  .fc-py .fc-chip { grid-column: 2; justify-self: start; }
  .fc-chans { grid-template-columns: repeat(auto-fill, minmax(96px, 1fr)); }
  .fc-ed-grid { grid-template-columns: 1fr; }
  .miz-btn-row .miz-btn { flex: 1 1 100%; justify-content: center; }
}

/* R295 : une seule graisse par police embarquée (Oswald 500, Roboto Mono 400, Stardos Stencil 700) */
.ed-field label, .ed-btn-icon, .ed-btn-add { font-weight: 500; }
b, strong { font-weight: 400; }
"""

# ---------- Corps de la page ----------
BODY = r"""
<body data-theme="cw-nato">

<!-- TOOLBAR -->
<header class="toolbar" role="toolbar" aria-label="Flight Configurator">
  <div class="tb-brand">
    <span class="tb-brand-main">FLIGHT CONFIGURATOR</span>
    <span class="tb-brand-sub" data-i18n="toolbar.subtitle">░ PAQUET DE VOL</span>
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
  <span class="tb-version">v@@VERSION@@</span>
</header>

<!-- MAIN APP -->
<div class="app" id="app">
  <div class="editor" id="editor-panel">

    <details class="ed-section" id="sec-pkg" open>
      <summary data-i18n="sec.pkg">PAQUET</summary>
      <div class="ed-content" id="pkg-body"></div>
    </details>

    <details class="ed-section" id="sec-flights" open>
      <summary><span data-i18n="sec.flights">VOLS</span>&nbsp;<span id="fl-count"></span></summary>
      <div class="ed-content" id="fl-body"></div>
    </details>

    <details class="ed-section" id="sec-presets" open>
      <summary data-i18n="sec.presets">PRESETS D'EMPORT</summary>
      <div class="ed-content" id="pr-body"></div>
    </details>

  </div>
</div>

<input type="file" id="fc-in-lua" accept=".lua,text/plain" multiple hidden>
<input type="file" id="fc-in-ctx" accept=".json,application/json" hidden>
<div class="toast" id="toast" role="status" aria-live="polite"></div>
"""

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
//  FLIGHT CONFIGURATOR — ébauche de maquette (lot A) : aucun paquet n'est encore écrit ni lu
// =============================================================
const KEY_THEME = 'theme_v1';
const KEY_LANG  = 'fc_lang_v1';
const KEY_MINE  = 'fc_presets_v1';

const I18N = {
  fr: {
    'toolbar.subtitle': '░ PAQUET DE VOL',
    'toolbar.theme.tooltip': 'Thème graphique',
    'toolbar.lang.tooltip': 'Changer de langue / Switch language',
    'theme.cw-nato': 'Cold War OTAN', 'theme.cw-soviet': 'Cold War Soviétique', 'theme.modern-nato': 'OTAN moderne', 'theme.modern-east': 'Bloc Est moderne',
    'sec.pkg': 'PAQUET', 'sec.flights': 'VOLS', 'sec.presets': 'PRESETS D’EMPORT',
    'pkg.theatre': 'Théâtre', 'pkg.theatre.none': '— non renseigné —',
    'pkg.fname': 'Fichier exporté',
    'pkg.stamp': 'AAAAMMJJ-HHMMSS',
    'pkg.load': '⇓ Charger un contexte ou un paquet',
    'pkg.new': '↺ Nouveau paquet',
    'pkg.export': '📦 Exporter le paquet',
    'pkg.ctx.none': 'Aucun contexte chargé : tout se saisit ici. Un contexte (le _snapshot.json d’HQ ou un paquet) propose le théâtre, les vols et leurs unités.',
    'pkg.ctx.on': 'Contexte : {0} — {1}, {2}',
    'pkg.confirm.new': 'Vider le paquet en cours ?',
    'toast.mock': 'Maquette : pas encore branché',
    'fl.add': '+ Ajouter un vol',
    'fl.title': 'Vol {0}',
    'fl.name': 'Nom du groupe', 'fl.name.ph': 'ex. Hind 1',
    'fl.type': 'Appareil',
    'fl.coalition': 'Coalition', 'fl.coalition.any': '— non précisée —', 'fl.coalition.blue': 'Bleue (blue)', 'fl.coalition.red': 'Rouge (red)',
    'fl.freq': 'Fréquence du groupe (MHz)', 'fl.freq.ph': 'facultative',
    'fl.remove': 'Retirer le vol',
    'fl.units.one': '{0} unité', 'fl.units.many': '{0} unités',
    'fl.empty': 'Aucun vol. Ajoutez-en un, ou chargez un contexte.',
    'u.title': 'Unité {0}', 'u.remove': 'Retirer l’unité', 'u.add': '+ Ajouter une unité ({0}/4)',
    'u.name': 'Nom de l’unité', 'u.callsign': 'Indicatif', 'u.onboard': 'N° de bord', 'u.livery': 'Livrée',
    'u.livery.ph': 'identifiant DCS, facultatif', 'u.opt': 'facultatif',
    'u.radios': 'Radios', 'u.loadout': 'Emport',
    'u.radios.sum': '{0} postes', 'u.loadout.none': 'non renseigné — HQ n’y touchera pas',
    'rad.post': '{0}', 'rad.chans': '{0} canaux', 'rad.ch': 'Canal {0}',
    'rad.hint': 'Fréquences en MHz. Les canaux portent le numéro du cockpit. Les modulations ne s’écrivent pas.',
    'rad.copy': '⧉ Recopier sur les autres unités du vol',
    'rad.err.nan': 'Canal {0} : « {1} » n’est pas une fréquence.',
    'rad.err.band': 'Canal {0} : {1} MHz hors de la bande du poste ({2} – {3} MHz).',
    'rad.err.more': ' (+ {0} autre(s))',
    'lo.preset': 'Preset', 'lo.preset.none': '— aucun —', 'lo.create': '✎ Créer un preset…',
    'lo.src.file': 'fichier {0}', 'lo.src.mine': 'mes presets',
    'lo.nopreset': 'Aucun preset pour le {0}. Chargez un fichier UnitPayloads ou créez un preset.',
    'lo.pylon': 'Pyl. {0}', 'lo.empty': 'vide', 'lo.unknown': 'arme absente du catalogue', 'lo.settings': 'réglages',
    'lo.fuel': 'Carburant (kg)', 'lo.flare': 'Leurres', 'lo.chaff': 'Paillettes', 'lo.gun': 'Canon (%)',
    'lo.max': 'max {0}', 'lo.err.range': '{0} : de 0 à {1}.',
    'lo.settings.line': 'Carburant, leurres, paillettes et canon se règlent ici ; ils ne font pas partie du preset.',
    'ed.title': 'Nouveau preset — {0}',
    'ed.name': 'Nom du preset', 'ed.name.ph': 'ex. Patrouille AT',
    'ed.empty': '— vide —', 'ed.clear': 'Tout vider', 'ed.save': 'Enregistrer le preset', 'ed.cancel': 'Annuler',
    'ed.kept': 'réglages conservés',
    'ed.err.name': 'Donnez un nom au preset.', 'ed.err.dup': 'Un preset de ce nom existe déjà pour le {0}.', 'ed.err.none': 'Choisissez au moins une arme.',
    'ed.hint': 'Aucune règle d’emport n’est vérifiée ici : le preset est écrit comme celui de l’éditeur de DCS.',
    'pr.load': '⇓ Charger des presets (.lua)',
    'pr.hint': 'Un fichier UnitPayloads par appareil, au format de l’éditeur de DCS.',
    'pr.files': 'Fichiers chargés ({0})',
    'pr.file.ok': '{0} · {1} presets', 'pr.file.unsup': '{0} · type non géré',
    'pr.err': '{0} : illisible — ligne {1} ({2})',
    'pr.mine': 'Mes presets ({0})', 'pr.mine.hint': 'Gardés dans ce navigateur.',
    'pr.export': '⇑ Exporter {0}.lua', 'pr.delete': 'Supprimer',
    'pr.export.hint': 'Le fichier réunit les presets chargés et les vôtres.',
    'pr.none': 'Aucun preset chargé ni créé.',
    'err.code.unterminated-string': 'chaîne non fermée', 'err.code.unexpected-eof': 'fin de fichier inattendue', 'err.code.unexpected-token': 'élément inattendu',
    'err.code.bad-structure': 'structure inattendue', 'err.code.unexpected-character': 'caractère inattendu', 'err.code.unterminated-comment': 'commentaire non fermé'
  },
  en: {
    'toolbar.subtitle': '░ FLIGHT PACKAGE',
    'toolbar.theme.tooltip': 'Visual theme',
    'toolbar.lang.tooltip': 'Switch language / Changer de langue',
    'theme.cw-nato': 'Cold War NATO', 'theme.cw-soviet': 'Cold War Soviet', 'theme.modern-nato': 'Modern NATO', 'theme.modern-east': 'Modern East Bloc',
    'sec.pkg': 'PACKAGE', 'sec.flights': 'FLIGHTS', 'sec.presets': 'LOADOUT PRESETS',
    'pkg.theatre': 'Theatre', 'pkg.theatre.none': '— not set —',
    'pkg.fname': 'Exported file',
    'pkg.stamp': 'YYYYMMDD-HHMMSS',
    'pkg.load': '⇓ Load a context or a package',
    'pkg.new': '↺ New package',
    'pkg.export': '📦 Export the package',
    'pkg.ctx.none': 'No context loaded: everything is entered here. A context (HQ’s _snapshot.json or a package) offers the theatre, the flights and their units.',
    'pkg.ctx.on': 'Context: {0} — {1}, {2}',
    'pkg.confirm.new': 'Clear the current package?',
    'toast.mock': 'Mock-up: not wired yet',
    'fl.add': '+ Add a flight',
    'fl.title': 'Flight {0}',
    'fl.name': 'Group name', 'fl.name.ph': 'e.g. Hind 1',
    'fl.type': 'Aircraft',
    'fl.coalition': 'Coalition', 'fl.coalition.any': '— unspecified —', 'fl.coalition.blue': 'Blue', 'fl.coalition.red': 'Red',
    'fl.freq': 'Group frequency (MHz)', 'fl.freq.ph': 'optional',
    'fl.remove': 'Remove the flight',
    'fl.units.one': '{0} unit', 'fl.units.many': '{0} units',
    'fl.empty': 'No flight. Add one, or load a context.',
    'u.title': 'Unit {0}', 'u.remove': 'Remove the unit', 'u.add': '+ Add a unit ({0}/4)',
    'u.name': 'Unit name', 'u.callsign': 'Callsign', 'u.onboard': 'Onboard no.', 'u.livery': 'Livery',
    'u.livery.ph': 'DCS id, optional', 'u.opt': 'optional',
    'u.radios': 'Radios', 'u.loadout': 'Loadout',
    'u.radios.sum': '{0} radios', 'u.loadout.none': 'not set — HQ will leave it untouched',
    'rad.post': '{0}', 'rad.chans': '{0} channels', 'rad.ch': 'Channel {0}',
    'rad.hint': 'Frequencies in MHz. Channels carry the cockpit numbers. Modulations are not written.',
    'rad.copy': '⧉ Copy to the other units of the flight',
    'rad.err.nan': 'Channel {0}: “{1}” is not a frequency.',
    'rad.err.band': 'Channel {0}: {1} MHz is outside the radio’s band ({2} – {3} MHz).',
    'rad.err.more': ' (+ {0} more)',
    'lo.preset': 'Preset', 'lo.preset.none': '— none —', 'lo.create': '✎ Create a preset…',
    'lo.src.file': 'file {0}', 'lo.src.mine': 'my presets',
    'lo.nopreset': 'No preset for the {0}. Load a UnitPayloads file or create a preset.',
    'lo.pylon': 'Pyl. {0}', 'lo.empty': 'empty', 'lo.unknown': 'weapon not in the catalogue', 'lo.settings': 'settings',
    'lo.fuel': 'Fuel (kg)', 'lo.flare': 'Flares', 'lo.chaff': 'Chaff', 'lo.gun': 'Gun (%)',
    'lo.max': 'max {0}', 'lo.err.range': '{0}: 0 to {1}.',
    'lo.settings.line': 'Fuel, flares, chaff and gun are set here; they are not part of the preset.',
    'ed.title': 'New preset — {0}',
    'ed.name': 'Preset name', 'ed.name.ph': 'e.g. AT patrol',
    'ed.empty': '— empty —', 'ed.clear': 'Clear all', 'ed.save': 'Save the preset', 'ed.cancel': 'Cancel',
    'ed.kept': 'settings kept',
    'ed.err.name': 'Give the preset a name.', 'ed.err.dup': 'A preset with this name already exists for the {0}.', 'ed.err.none': 'Pick at least one weapon.',
    'ed.hint': 'No loadout rule is checked here: the preset is written like the DCS editor writes it.',
    'pr.load': '⇓ Load presets (.lua)',
    'pr.hint': 'One UnitPayloads file per aircraft, in the DCS editor’s format.',
    'pr.files': 'Loaded files ({0})',
    'pr.file.ok': '{0} · {1} presets', 'pr.file.unsup': '{0} · type not handled',
    'pr.err': '{0}: unreadable — line {1} ({2})',
    'pr.mine': 'My presets ({0})', 'pr.mine.hint': 'Kept in this browser.',
    'pr.export': '⇑ Export {0}.lua', 'pr.delete': 'Delete',
    'pr.export.hint': 'The file holds the loaded presets and yours.',
    'pr.none': 'No preset loaded or created.',
    'err.code.unterminated-string': 'unterminated string', 'err.code.unexpected-eof': 'unexpected end of file', 'err.code.unexpected-token': 'unexpected token',
    'err.code.bad-structure': 'unexpected structure', 'err.code.unexpected-character': 'unexpected character', 'err.code.unterminated-comment': 'unterminated comment'
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

// ---------- données par type ----------
const TYPE_LABEL = { 'Mi-24P': 'Mi-24P', 'Mi-8MT': 'Mi-8MT', 'F-4E-45MC': 'F-4E-45MC', 'Mirage-F1EE': 'Mirage F1EE' };
// Nombre de canaux par poste (sonde des .miz) ; seuls les postes qui ont des canaux s'offrent.
const RADIO_CHANNELS = { 'Mi-24P': { 1: 20, 2: 10 }, 'Mi-8MT': { 1: 20, 2: 10 }, 'F-4E-45MC': { 1: 18, 2: 20 }, 'Mirage-F1EE': { 1: 20, 2: 20 } };
// Bande plausible par poste, en MHz (à confirmer : valeurs de DCS d'après la connaissance du jeu, bornées par les fréquences vues dans les .miz d'exemple)
const RADIO_BANDS = {
  'Mi-24P': { 1: [100, 399.975], 2: [20, 59.975] }, 'Mi-8MT': { 1: [100, 399.975], 2: [20, 59.975] },
  'F-4E-45MC': { 1: [225, 399.975], 2: [225, 399.975] }, 'Mirage-F1EE': { 1: [118, 399.975], 2: [225, 399.975] }
};
const THEATRES = ['Caucasus', 'Falklands', 'GermanyCW', 'Kola', 'MarianaIslands', 'Nevada', 'Normandy', 'PersianGulf', 'SinaiMap', 'Syria', 'TheChannel'];

// ---------- état ----------
const S = { theatre: '', flights: [], ctx: null };
const LIB = { files: [], mine: {}, errors: [] };
const UI = { open: new Set(), editor: null };

function newUnit() { return { name: '', callsign: '', onboard: '', livery: '', radios: {}, loadout: null }; }
function newFlight() { return { name: '', type: 'Mi-24P', coalition: '', freq: '', units: [newUnit()] }; }

// ---------- stockage (jamais requis : tout accès en try/catch) ----------
function loadMine() {
  try {
    const raw = localStorage.getItem(KEY_MINE);
    const o = raw ? JSON.parse(raw) : null;
    if (o && typeof o === 'object' && o.mine && typeof o.mine === 'object') {
      PAYLOAD_TYPES.forEach(ty => { if (Array.isArray(o.mine[ty])) LIB.mine[ty] = o.mine[ty]; });
    }
  } catch (e) { /* l'écran marche sans */ }
}
function saveMine() {
  try { localStorage.setItem(KEY_MINE, JSON.stringify({ mine: LIB.mine })); } catch (e) { /* idem */ }
}

// ---------- listes de presets d'un type ----------
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
function clonePylons(p) { return JSON.parse(JSON.stringify(p)); }

// ---------- rendu ----------
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

function cleanName(s) { return String(s).replace(/[^A-Za-z0-9_-]/g, '_').slice(0, 40); }
function packageFileName() {
  const first = S.flights.length ? (S.flights[0].name || 'vol') : 'vol';
  return 'paquet_' + cleanName(first) + (S.flights.length > 1 ? '_+' + (S.flights.length - 1) : '') + '_' + t('pkg.stamp') + '.json';
}

function renderPackage() {
  const opts = [{ v: '', l: t('pkg.theatre.none') }].concat(THEATRES.map(x => ({ v: x, l: x })));
  let h = '<div class="fc-row">';
  h += fieldHtml(t('pkg.theatre'), selectHtml('id="pkg-theatre" data-k="theatre"', t('pkg.theatre'), opts, S.theatre));
  h += fieldHtml(t('pkg.fname'), '<div class="fc-fname" id="pkg-fname">' + esc(packageFileName()) + '</div>');
  h += '</div>';
  h += '<div class="miz-btn-row" style="margin-top:0">';
  h += '<button type="button" class="miz-btn" data-act="load-ctx">' + esc(t('pkg.load')) + '</button>';
  h += '<button type="button" class="miz-btn" data-act="new-pkg">' + esc(t('pkg.new')) + '</button>';
  h += '<button type="button" class="miz-btn primary" data-act="export-pkg"' + (S.flights.length ? '' : ' disabled') + '>' + esc(t('pkg.export')) + '</button>';
  h += '</div>';
  h += '<p class="pk-note">' + esc(S.ctx ? tf('pkg.ctx.on', S.ctx.file, S.ctx.theatre, S.ctx.n) : t('pkg.ctx.none')) + '</p>';
  document.getElementById('pkg-body').innerHTML = h;
}

function unitsLabel(n) { return tf(n < 2 ? 'fl.units.one' : 'fl.units.many', n); }

function renderFlights() {
  document.getElementById('fl-count').textContent = '(' + S.flights.length + ')';
  let h = '';
  if (!S.flights.length) h += '<p class="pk-note">' + esc(t('fl.empty')) + '</p>';
  h += '<div class="fc-list" id="fc-list">';
  S.flights.forEach((f, fi) => { h += flightHtml(f, fi); });
  h += '</div>';
  h += '<div class="miz-btn-row" style="margin-top:0"><button type="button" class="miz-btn primary" data-act="add-flight">' + esc(t('fl.add')) + '</button></div>';
  document.getElementById('fl-body').innerHTML = h;
  S.flights.forEach((f, fi) => f.units.forEach((u, ui) => { RADIO_POSTS(f.type).forEach(r => validateRadios(fi, ui, r)); }));
}

function flightHtml(f, fi) {
  const typeOpts = PAYLOAD_TYPES.map(x => ({ v: x, l: TYPE_LABEL[x] }));
  const coOpts = [{ v: '', l: t('fl.coalition.any') }, { v: 'blue', l: t('fl.coalition.blue') }, { v: 'red', l: t('fl.coalition.red') }];
  let h = '<div class="fc-flight" data-f="' + fi + '">';
  h += '<div class="fc-fhead"><span class="fc-ftitle">' + esc(tf('fl.title', fi + 1)) + '</span><span class="snap-flight-tag">' + esc(TYPE_LABEL[f.type]) + '</span>'
    + '<span class="snap-flight-tag">' + esc(unitsLabel(f.units.length)) + '</span>'
    + '<button type="button" class="pk-x" data-act="rm-flight" aria-label="' + esc(t('fl.remove')) + '" title="' + esc(t('fl.remove')) + '">✕</button></div>';
  h += '<div class="fc-row">';
  h += fieldHtml(t('fl.name'), inputHtml('data-k="name"', f.name, t('fl.name.ph')));
  h += fieldHtml(t('fl.type'), selectHtml('data-k="type"', t('fl.type'), typeOpts, f.type));
  h += fieldHtml(t('fl.coalition'), selectHtml('data-k="coalition"', t('fl.coalition'), coOpts, f.coalition));
  h += fieldHtml(t('fl.freq'), inputHtml('data-k="freq" inputmode="decimal"', f.freq, t('fl.freq.ph')));
  h += '</div>';
  h += '<div class="fc-units">';
  f.units.forEach((u, ui) => { h += unitHtml(f, fi, u, ui); });
  h += '</div>';
  if (f.units.length < 4) h += '<div class="miz-btn-row"><button type="button" class="miz-btn" data-act="add-unit">' + esc(tf('u.add', f.units.length)) + '</button></div>';
  return h + '</div>';
}

function RADIO_POSTS(type) { return Object.keys(RADIO_CHANNELS[type] || {}).map(Number); }

function unitHtml(f, fi, u, ui) {
  const at = 'data-u="' + ui + '"';
  let h = '<div class="fc-unit" data-u="' + ui + '">';
  h += '<div class="fc-uhead"><span class="fc-utitle">' + esc(tf('u.title', ui + 1)) + '</span>';
  if (f.units.length > 1) h += '<button type="button" class="pk-x" data-act="rm-unit" aria-label="' + esc(t('u.remove')) + '" title="' + esc(t('u.remove')) + '">✕</button>';
  h += '</div>';
  h += '<div class="fc-row4">';
  h += fieldHtml(t('u.name'), inputHtml(at + ' data-k="uname"', u.name, (f.name || 'Hind 1') + '-' + (ui + 1)));
  h += fieldHtml(t('u.callsign'), inputHtml(at + ' data-k="callsign"', u.callsign, t('u.opt')));
  h += fieldHtml(t('u.onboard'), inputHtml(at + ' data-k="onboard"', u.onboard, t('u.opt')));
  h += fieldHtml(t('u.livery'), inputHtml(at + ' data-k="livery"', u.livery, t('u.livery.ph')));
  h += '</div>';
  // radios
  const rk = 'f' + fi + 'u' + ui + 'r';
  h += '<details class="fc-sub" data-key="' + rk + '"' + openAttr(rk, false) + '><summary>' + esc(t('u.radios')) + ' <span class="fc-sum">' + esc(tf('u.radios.sum', RADIO_POSTS(f.type).length)) + '</span></summary><div class="fc-subc">';
  h += radiosHtml(f, fi, u, ui);
  h += '</div></details>';
  // emport
  const lk = 'f' + fi + 'u' + ui + 'l';
  const lo = u.loadout;
  h += '<details class="fc-sub" data-key="' + lk + '"' + openAttr(lk, false) + '><summary>' + esc(t('u.loadout')) + ' <span class="fc-sum">' + esc(lo ? lo.presetName : t('u.loadout.none')) + '</span></summary><div class="fc-subc">';
  h += loadoutHtml(f, fi, u, ui);
  h += '</div></details>';
  return h + '</div>';
}

function radiosHtml(f, fi, u, ui) {
  let h = '';
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
  h += '<p class="pk-note">' + esc(t('rad.hint')) + '</p>';
  if (f.units.length > 1) h += '<div class="miz-btn-row" style="margin-top:0"><button type="button" class="miz-btn" data-u="' + ui + '" data-act="copy-radios">' + esc(t('rad.copy')) + '</button></div>';
  return h;
}

function parseFreq(s) {
  const x = String(s).trim().replace(',', '.');
  if (x === '') return { empty: true };
  if (!/^\d+(\.\d+)?$/.test(x)) return { nan: true };
  return { v: Number(x) };
}
function fmtMHz(v) { return String(v).replace('.', CURRENT_LANG === 'fr' ? ',' : '.'); }
function validateRadios(fi, ui, r) {
  const f = S.flights[fi], u = f && f.units[ui];
  if (!u) return;
  const band = (RADIO_BANDS[f.type] || {})[r];
  const n = RADIO_CHANNELS[f.type][r];
  let first = '', bad = 0;
  for (let c = 1; c <= n; c++) {
    const inp = document.querySelector('#fl-body .fc-flight[data-f="' + fi + '"] .fc-unit[data-u="' + ui + '"] input[data-r="' + r + '"][data-c="' + c + '"]');
    const raw = (u.radios[r] && u.radios[r][c] !== undefined) ? u.radios[r][c] : '';
    const p = parseFreq(raw);
    let msg = '';
    if (p.nan) msg = tf('rad.err.nan', radioCockpitChannel(f.type, r, c), raw);
    else if (p.v !== undefined && band && (p.v < band[0] || p.v > band[1])) msg = tf('rad.err.band', radioCockpitChannel(f.type, r, c), fmtMHz(p.v), fmtMHz(band[0]), fmtMHz(band[1]));
    if (inp) inp.classList.toggle('bad', !!msg);
    if (msg) { bad++; if (!first) first = msg; }
  }
  const el = document.getElementById('rm-' + fi + '-' + ui + '-' + r);
  if (el) el.textContent = first ? first + (bad > 1 ? tf('rad.err.more', bad - 1) : '') : '';
}

function loadoutHtml(f, fi, u, ui) {
  const list = presetsFor(f.type);
  const lo = u.loadout;
  const at = 'data-u="' + ui + '"';
  let h = '';
  const opts = [{ v: '', l: t('lo.preset.none') }].concat(list.map(p => ({ v: p.key, l: p.label })));
  h += '<div class="fc-row">';
  h += fieldHtml(t('lo.preset'), selectHtml(at + ' data-k="preset"', t('lo.preset'), opts, lo ? lo.key : ''));
  h += '<div class="ed-field fc-actions"><button type="button" class="miz-btn" ' + at + ' data-act="open-editor">' + esc(t('lo.create')) + '</button></div>';
  h += '</div>';
  if (!list.length && !lo) h += '<p class="pk-note">' + esc(tf('lo.nopreset', TYPE_LABEL[f.type])) + '</p>';
  if (lo) {
    h += '<div class="fc-lo-line"><span class="snap-flight-tag">' + esc(lo.src || '') + '</span></div>';
    h += '<div class="fc-pylons">';
    const nums = payloadPylonNumbers(f.type);
    Object.keys(lo.pylons).map(Number).forEach(n => { if (nums.indexOf(n) < 0) nums.push(n); });
    nums.forEach(n => {
      const py = lo.pylons[n];
      const clsid = py ? py.CLSID : '';
      const name = payloadWeaponName(f.type, n, clsid);
      let cls = 'fc-py', w;
      if (!clsid) { cls += ' empty'; w = esc(t('lo.empty')); }
      else if (name === null) { cls += ' unk'; w = esc(t('lo.unknown')) + '<small>' + esc(clsid) + '</small>'; }
      else w = esc(name) + '<small>' + esc(clsid) + '</small>';
      h += '<div class="' + cls + '"><span class="fc-py-n">' + esc(tf('lo.pylon', n)) + '</span><span class="fc-py-w">' + w + '</span>'
        + (py && py.settings ? '<span class="fc-chip">' + esc(t('lo.settings')) + '</span>' : '') + '</div>';
    });
    h += '</div>';
    const d = payloadDefaults(f.type);
    h += '<div class="fc-set">';
    h += fieldHtml(t('lo.fuel') + ' · ' + tf('lo.max', d.fuel), inputHtml(at + ' data-k="fuel" inputmode="decimal"', lo.fuel));
    h += fieldHtml(t('lo.flare') + ' · ' + tf('lo.max', d.flare), inputHtml(at + ' data-k="flare" inputmode="numeric"', lo.flare));
    h += fieldHtml(t('lo.chaff') + ' · ' + tf('lo.max', d.chaff), inputHtml(at + ' data-k="chaff" inputmode="numeric"' + (d.chaff === 0 ? ' disabled' : ''), lo.chaff));
    h += fieldHtml(t('lo.gun') + ' · ' + tf('lo.max', 100), inputHtml(at + ' data-k="gun" inputmode="numeric"', lo.gun));
    h += '</div><div class="fc-msg" id="lm-' + fi + '-' + ui + '"></div>';
    h += '<p class="pk-note">' + esc(t('lo.settings.line')) + '</p>';
  }
  if (UI.editor && UI.editor.f === fi && UI.editor.u === ui) h += editorHtml(f);
  return h;
}

function editorHtml(f) {
  const E = UI.editor;
  let h = '<div class="fc-editor" id="fc-editor">';
  h += '<div class="fc-ed-title">' + esc(tf('ed.title', TYPE_LABEL[f.type])) + '</div>';
  h += '<div class="fc-row">' + fieldHtml(t('ed.name'), inputHtml('data-k="ed-name"', E.name, t('ed.name.ph')))
    + '<div class="ed-field fc-actions"><button type="button" class="miz-btn" data-act="ed-clear">' + esc(t('ed.clear')) + '</button></div></div>';
  h += '<div class="fc-ed-grid">';
  payloadPylonNumbers(f.type).forEach(n => {
    const cur = E.pylons[n] ? E.pylons[n].CLSID : '';
    const list = WEAPONS[f.type][n];
    const opts = [{ v: '', l: t('ed.empty') }];
    let known = !cur;
    list.forEach(w => { opts.push({ v: w.clsid, l: w.name }); if (w.clsid === cur) known = true; });
    if (!known) opts.push({ v: cur, l: '⚠ ' + cur });
    h += '<div class="fc-ed-py"><label>' + esc(tf('lo.pylon', n)) + (E.pylons[n] && E.pylons[n].settings ? '<span class="fc-chip">' + esc(t('ed.kept')) + '</span>' : '') + '</label>'
      + selectHtml('data-k="ed-py" data-n="' + n + '"', tf('lo.pylon', n), opts, cur) + '<small>' + esc(cur) + '</small></div>';
  });
  h += '</div><div class="fc-msg" id="ed-msg">' + esc(E.error || '') + '</div>';
  h += '<p class="pk-note">' + esc(t('ed.hint')) + '</p>';
  h += '<div class="miz-btn-row" style="margin-top:0"><button type="button" class="miz-btn primary" data-act="ed-save">' + esc(t('ed.save')) + '</button>'
    + '<button type="button" class="miz-btn" data-act="ed-cancel">' + esc(t('ed.cancel')) + '</button></div>';
  return h + '</div>';
}

function renderPresets() {
  let h = '<div class="miz-btn-row" style="margin-top:0"><button type="button" class="miz-btn primary" data-act="load-lua">' + esc(t('pr.load')) + '</button></div>';
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
  PAYLOAD_TYPES.forEach(ty => {
    (LIB.mine[ty] || []).forEach((p, i) => {
      h += '<div class="fc-file"><span class="fc-file-n">★ ' + esc(p.displayName || p.name) + '</span><span class="snap-flight-tag">' + esc(TYPE_LABEL[ty]) + '</span>'
        + '<button type="button" class="pk-x" data-act="rm-mine" data-ty="' + esc(ty) + '" data-i="' + i + '" aria-label="' + esc(t('pr.delete')) + '" title="' + esc(t('pr.delete')) + '">✕</button></div>';
    });
  });
  h += '</div>';
  if (nMine) {
    h += '<p class="pk-note">' + esc(t('pr.mine.hint')) + ' ' + esc(t('pr.export.hint')) + '</p><div class="miz-btn-row" style="margin-top:0">';
    PAYLOAD_TYPES.forEach(ty => { if ((LIB.mine[ty] || []).length) h += '<button type="button" class="miz-btn" data-act="export-lua" data-ty="' + esc(ty) + '">' + esc(tf('pr.export', ty)) + '</button>'; });
    h += '</div>';
  }
  document.getElementById('pr-body').innerHTML = h;
}

function renderAll() { renderPackage(); renderFlights(); renderPresets(); applyI18nStatic(); }

// ---------- actions ----------
function applyPreset(f, u, key) {
  if (!key) { u.loadout = null; return; }
  const hit = presetsFor(f.type).filter(p => p.key === key)[0];
  if (!hit) { u.loadout = null; return; }
  const d = payloadDefaults(f.type);
  u.loadout = {
    key: key, presetName: hit.label, src: hit.src, pylons: clonePylons(hit.preset.pylons),
    fuel: String(d.fuel), flare: String(d.flare), chaff: String(d.chaff), gun: String(d.gun)
  };
}

function openEditor(fi, ui) {
  const f = S.flights[fi], u = f.units[ui];
  const src = u.loadout ? clonePylons(u.loadout.pylons) : {};
  UI.editor = { f: fi, u: ui, name: '', pylons: src, error: '', tasks: [TASK_DEFAULT[f.type]] };
  UI.open.add('f' + fi + 'u' + ui + 'l');
  renderFlights();
  const el = document.getElementById('fc-editor');
  if (el && el.scrollIntoView) el.scrollIntoView({ block: 'nearest' });
}

function saveEditor() {
  const E = UI.editor, f = S.flights[E.f], u = f.units[E.u];
  const name = E.name.trim();
  const fail = key => { E.error = key; const m = document.getElementById('ed-msg'); if (m) m.textContent = key; };
  if (!name) return fail(t('ed.err.name'));
  if ((LIB.mine[f.type] || []).some(p => p.name === name)) return fail(tf('ed.err.dup', TYPE_LABEL[f.type]));
  const pylons = {};
  Object.keys(E.pylons).forEach(n => { if (E.pylons[n] && E.pylons[n].CLSID) pylons[n] = E.pylons[n]; });
  if (!Object.keys(pylons).length) return fail(t('ed.err.none'));
  const order = Object.keys(pylons).map(Number).sort((a, b) => a - b);
  const preset = { name: name, displayName: name, pylons: pylons, order: order, tasks: E.tasks.slice() };
  (LIB.mine[f.type] = LIB.mine[f.type] || []).push(preset);
  saveMine();
  const idx = LIB.mine[f.type].length - 1;
  UI.editor = null;
  applyPreset(f, u, 'm:' + idx);
  renderFlights(); renderPresets();
}

function download(text, fname, mime) {
  const blob = new Blob([text], { type: mime || 'text/plain' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = fname;
  document.body.appendChild(a); a.click(); document.body.removeChild(a);
  setTimeout(() => URL.revokeObjectURL(url), 2000);
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
  renderFlights(); renderPresets();
}

function onClick(e) {
  const b = e.target.closest ? e.target.closest('[data-act]') : null;
  if (!b || b.disabled) return;
  const act = b.getAttribute('data-act');
  const fEl = b.closest('.fc-flight'), fi = fEl ? Number(fEl.getAttribute('data-f')) : -1;
  const uEl = b.closest('.fc-unit'), ui = uEl ? Number(uEl.getAttribute('data-u')) : (b.hasAttribute('data-u') ? Number(b.getAttribute('data-u')) : -1);
  if (act === 'add-flight') { S.flights.push(newFlight()); renderFlights(); renderPackage(); }
  else if (act === 'rm-flight') { S.flights.splice(fi, 1); UI.editor = null; renderFlights(); renderPackage(); }
  else if (act === 'add-unit') { S.flights[fi].units.push(newUnit()); renderFlights(); }
  else if (act === 'rm-unit') { S.flights[fi].units.splice(ui, 1); UI.editor = null; renderFlights(); }
  else if (act === 'copy-radios') {
    const f = S.flights[fi], src = f.units[ui].radios;
    f.units.forEach((u, k) => { if (k !== ui) u.radios = JSON.parse(JSON.stringify(src)); });
    renderFlights();
  }
  else if (act === 'open-editor') openEditor(fi, ui);
  else if (act === 'ed-cancel') { UI.editor = null; renderFlights(); }
  else if (act === 'ed-clear') { UI.editor.pylons = {}; renderFlights(); }
  else if (act === 'ed-save') saveEditor();
  else if (act === 'load-lua') document.getElementById('fc-in-lua').click();
  else if (act === 'load-ctx') document.getElementById('fc-in-ctx').click();
  else if (act === 'new-pkg') { if (confirm(t('pkg.confirm.new'))) { S.flights = []; S.theatre = ''; S.ctx = null; UI.editor = null; renderAll(); } }
  else if (act === 'export-pkg') showToast(t('toast.mock'));
  else if (act === 'rm-file') { LIB.files.splice(Number(b.getAttribute('data-i')), 1); renderFlights(); renderPresets(); }
  else if (act === 'rm-mine') { (LIB.mine[b.getAttribute('data-ty')] || []).splice(Number(b.getAttribute('data-i')), 1); saveMine(); renderFlights(); renderPresets(); }
  else if (act === 'export-lua') exportLua(b.getAttribute('data-ty'));
}

function onInput(e) {
  const el = e.target, k = el.getAttribute && el.getAttribute('data-k');
  if (!k) return;
  const fEl = el.closest('.fc-flight'), fi = fEl ? Number(fEl.getAttribute('data-f')) : -1;
  const f = S.flights[fi];
  const ui = el.hasAttribute('data-u') ? Number(el.getAttribute('data-u')) : -1;
  const u = f && ui >= 0 ? f.units[ui] : null;
  if (k === 'name') { f.name = el.value; const p = document.getElementById('pkg-fname'); if (p) p.textContent = packageFileName(); }
  else if (k === 'freq') f.freq = el.value;
  else if (k === 'uname') u.name = el.value;
  else if (k === 'callsign') u.callsign = el.value;
  else if (k === 'onboard') u.onboard = el.value;
  else if (k === 'livery') u.livery = el.value;
  else if (k === 'chan') {
    const r = Number(el.getAttribute('data-r')), c = Number(el.getAttribute('data-c'));
    (u.radios[r] = u.radios[r] || {})[c] = el.value;
    validateRadios(fi, ui, r);
  }
  else if (u && u.loadout && (k === 'fuel' || k === 'flare' || k === 'chaff' || k === 'gun')) { u.loadout[k] = el.value; validateLoadout(fi, ui); }
  else if (k === 'ed-name' && UI.editor) UI.editor.name = el.value;
}

function validateLoadout(fi, ui) {
  const f = S.flights[fi], lo = f.units[ui].loadout, d = payloadDefaults(f.type);
  const spec = { fuel: [t('lo.fuel'), d.fuel], flare: [t('lo.flare'), d.flare], chaff: [t('lo.chaff'), d.chaff], gun: [t('lo.gun'), 100] };
  let msg = '';
  Object.keys(spec).forEach(k => {
    const inp = document.querySelector('#fl-body .fc-flight[data-f="' + fi + '"] .fc-unit[data-u="' + ui + '"] input[data-k="' + k + '"]');
    const p = parseFreq(lo[k]);
    const bad = p.nan || p.empty || p.v > spec[k][1];
    if (inp) inp.classList.toggle('bad', !!bad);
    if (bad && !msg) msg = tf('lo.err.range', spec[k][0], fmtMHz(spec[k][1]));
  });
  const el = document.getElementById('lm-' + fi + '-' + ui);
  if (el) el.textContent = msg;
}

function onChange(e) {
  const el = e.target, k = el.getAttribute && el.getAttribute('data-k');
  if (!k) return;
  if (k === 'theatre') { S.theatre = el.value; return; }
  const fEl = el.closest('.fc-flight'), fi = fEl ? Number(fEl.getAttribute('data-f')) : -1;
  const f = S.flights[fi];
  if (k === 'type') {
    f.type = el.value;
    f.units.forEach(u => { u.radios = {}; u.loadout = null; });
    UI.editor = null; renderFlights();
  }
  else if (k === 'coalition') f.coalition = el.value;
  else if (k === 'preset') { const ui = Number(el.getAttribute('data-u')); applyPreset(f, f.units[ui], el.value); renderFlights(); }
  else if (k === 'ed-py' && UI.editor) {
    const n = Number(el.getAttribute('data-n')), old = UI.editor.pylons[n];
    if (!el.value) delete UI.editor.pylons[n];
    else UI.editor.pylons[n] = (old && old.CLSID === el.value) ? old : { CLSID: el.value };   // un `settings` suit le pylône tant que l'arme ne change pas
    renderFlights();
  }
}

function onToggle(e) {
  const d = e.target;
  if (!d || !d.getAttribute || d.tagName !== 'DETAILS') return;
  const key = d.getAttribute('data-key');
  if (!key) return;
  if (d.open) { UI.open.add(key); UI.open.delete('~' + key); } else { UI.open.delete(key); UI.open.add('~' + key); }
}

// ---------- barre, langue, thème ----------
function showToast(msg, ms) {
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.classList.add('show');
  clearTimeout(showToast._h);
  showToast._h = setTimeout(() => el.classList.remove('show'), ms || 2200);
}
function loadTheme() {
  let saved = 'cw-nato';
  try { saved = localStorage.getItem(KEY_THEME) || 'cw-nato'; } catch (e) { /* idem */ }
  document.body.setAttribute('data-theme', saved);
  const sel = document.getElementById('theme-select');
  if (sel) sel.value = saved;
}
function loadLang() {
  let saved = null;
  try { saved = localStorage.getItem(KEY_LANG); } catch (e) { /* idem */ }
  CURRENT_LANG = (saved === 'fr' || saved === 'en') ? saved : ((navigator.language || 'fr').startsWith('fr') ? 'fr' : 'en');
  document.documentElement.lang = CURRENT_LANG;
}
function applyI18nStatic() {
  document.querySelectorAll('[data-i18n]').forEach(el => { el.textContent = t(el.getAttribute('data-i18n')); });
  document.querySelectorAll('[data-i18n-title]').forEach(el => { el.title = t(el.getAttribute('data-i18n-title')); });
  const b = document.getElementById('btn-lang');
  if (b) { b.textContent = CURRENT_LANG === 'fr' ? '🇬🇧' : '🇫🇷'; b.title = t('toolbar.lang.tooltip'); }
}

function initEvents() {
  const root = document.getElementById('editor-panel');
  root.addEventListener('click', onClick);
  root.addEventListener('input', onInput);
  root.addEventListener('change', onChange);
  root.addEventListener('toggle', onToggle, true);
  document.getElementById('theme-select').addEventListener('change', e => {
    document.body.setAttribute('data-theme', e.target.value);
    try { localStorage.setItem(KEY_THEME, e.target.value); } catch (x) { /* idem */ }
  });
  document.getElementById('btn-lang').addEventListener('click', () => {
    CURRENT_LANG = CURRENT_LANG === 'fr' ? 'en' : 'fr';
    try { localStorage.setItem(KEY_LANG, CURRENT_LANG); } catch (x) { /* idem */ }
    document.documentElement.lang = CURRENT_LANG;
    renderAll();
  });
  document.getElementById('fc-in-lua').addEventListener('change', e => { const fl = Array.prototype.slice.call(e.target.files); e.target.value = ''; loadLuaFiles(fl); });
  document.getElementById('fc-in-ctx').addEventListener('change', e => { e.target.value = ''; showToast(t('toast.mock')); });
}

function init() {
  loadTheme();
  loadLang();
  loadMine();
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


def build_html():
    fonts = (FONTS.replace('@@ROBOTO_MONO_400@@', A['ROBOTO_MONO_400'])
                  .replace('@@STARDOS_700@@', A['STARDOS_700'])
                  .replace('@@OSWALD_500@@', A['OSWALD_500']))
    js = build_radio_block() + '\n' + build_payload_block() + '\n' + JS_TBM + '\n' + JS_FC
    return ('<!DOCTYPE html>\n<html lang="fr">\n<head>\n<meta charset="UTF-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0, viewport-fit=cover">\n'
            '<meta name="theme-color" content="#1a1e10">\n<title>Flight Configurator</title>\n<style>\n'
            + fonts + CSS_COMMON + CSS_FC + '\n</style>\n</head>\n'
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
    """Vérifications du build : parité FR/EN, clés de texte, syntaxe des scripts, aucune requête réseau, graisses."""
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
        used = {k for k in used if not k.startswith('err.code.')}
        ok(used <= kfr, 'toute clé de texte utilisée existe : manque %s' % sorted(used - kfr))
    scripts = re.findall(r'<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>', html, re.S)
    for i, s in enumerate(scripts):
        tmp = os.path.join(HERE, '.fc_check_%d.js' % i)
        with open(tmp, 'w', encoding='utf-8') as f:
            f.write(s)
        r = subprocess.run(['node', '--check', tmp], capture_output=True, text=True)
        os.remove(tmp)
        ok(r.returncode == 0, 'node --check du script %d%s' % (i + 1, '' if r.returncode == 0 else ' : ' + r.stderr[:300]))
    ok(not re.search(r'fetch\(|XMLHttpRequest|WebSocket|sendBeacon|<script[^>]*\bsrc=|<link[^>]*href=["\']http', html), 'aucune requête réseau')
    ok(not re.search(r'font-weight:\s*(600|800|900|bold)', html), 'aucune graisse sans sa face (R295)')
    ok('/* ===== POSTES RADIO (COMME AU COCKPIT) ===== */' in html and '/* ===== EMPORT (PRESETS ET PAYLOAD) ===== */' in html, 'blocs partagés présents')
    if bad:
        sys.exit(1)


if __name__ == '__main__':
    main()
