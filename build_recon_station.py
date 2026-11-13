#!/usr/bin/env python3
"""Build the DCS Recon Station HTML module — monofichier, canvas-native."""

import json
import os
import base64
import re

from messages_block import build_block as build_messages_block, build_css as build_messages_css
from ui_block import build_tbm_css, build_tbm_block, build_block as build_ui_block, build_css as build_ui_css, verify as ui_verify, verify_bar as ui_verify_bar
from shell_only_block import build_block as build_shell_only_block
# La garde du module seul : premier élément du <body> (build_mission_plan.py la vérifie dans le dist/)
SHELL_ONLY_TAG = '<script data-lang-key="lang_v1">\n' + build_shell_only_block() + '</script>\n'

CONTRAST_CSS = r"""
/* MP-20 begin */
/* Contrastes (texte sous 18 px, 4,5 : 1 au moins) : couleur du texte seule, la palette commune ne bouge pas. */
:where(body[data-theme="cw-nato"]) .tb-brand-short { color: #d47db1; }
:where(body[data-theme="cw-nato"]) #btn-open { color: #c49037; }
:where(body[data-theme="cw-nato"]) .tb-classif { color: #d4847b; }
:where(body[data-theme="cw-nato"]) .ed-section > summary { color: #dcbe8a; }
:where(body[data-theme="cw-nato"]) .drop-zone.has-image { color: #7f936f; }
:where(body[data-theme="cw-nato"]) .img-credit { color: #a69e87; }
:where(body[data-theme="cw-nato"]) .logo-mode button.active { color: #dcbe8a; }
:where(body[data-theme="cw-nato"]) .logo-thumb-none { color: #a69e87; }
:where(body[data-theme="cw-nato"]) .cartouche-point-toggle input:checked + .point-marker { color: #f36262; }
:where(body[data-theme="cw-nato"]) .btn-remove-row { color: #d4847b; }
:where(body[data-theme="cw-nato"]) .amorce-toggle input:checked + .amorce-marker { color: #c28d30; }
:where(body[data-theme="cw-nato"]) .btn-add-row { color: #c49037; }
:where(body[data-theme="cw-nato"]) .shapes-toolbox button { color: #c49037; }
:where(body[data-theme="cw-nato"]) .btn-add-inset { color: #8d9f7f; }
:where(body[data-theme="cw-nato"]) .inset-num { color: #849775; }
:where(body[data-theme="cw-nato"]) .inset-color-group button.active { color: #c79641; }
:where(body[data-theme="cw-nato"]) .dr-tool.on { color: #efe8d5; }
:where(body[data-theme="cw-soviet"]) .tb-brand-short { color: #cf6ea8; }
:where(body[data-theme="cw-soviet"]) .tb-classif { color: #be7d7d; }
:where(body[data-theme="cw-soviet"]) .ed-section > summary { color: #cc9f52; }
:where(body[data-theme="cw-soviet"]) .drop-zone.has-image { color: #798f69; }
:where(body[data-theme="cw-soviet"]) .img-credit { color: #959d8e; }
:where(body[data-theme="cw-soviet"]) .logo-mode button.active { color: #cc9f52; }
:where(body[data-theme="cw-soviet"]) .logo-thumb-none { color: #919a8a; }
:where(body[data-theme="cw-soviet"]) .cartouche-point-toggle input:checked + .point-marker { color: #f25757; }
:where(body[data-theme="cw-soviet"]) .btn-remove-row { color: #be7d7d; }
:where(body[data-theme="cw-soviet"]) .btn-add-inset { color: #809471; }
:where(body[data-theme="cw-soviet"]) .inset-num { color: #7f936f; }
:where(body[data-theme="cw-soviet"]) .inset-color-group button.active { color: #c49037; }
:where(body[data-theme="cw-soviet"]) .dr-tool.on { color: #f2e8c0; }
:where(body[data-theme="cw-soviet"]) .btn-replace { color: #879279; }
:where(body[data-theme="cw-soviet"]) .ed-label { color: #859178; }
:where(body[data-theme="cw-soviet"]) .logo-mode button { color: #879279; }
:where(body[data-theme="cw-soviet"]) .btn-upload-logo { color: #879279; }
:where(body[data-theme="cw-soviet"]) .logo-mode-label { color: #7e8b70; }
:where(body[data-theme="cw-soviet"]) .amorce-marker { color: #879279; }
:where(body[data-theme="cw-soviet"]) .shape-color-group button { color: #879279; }
:where(body[data-theme="cw-soviet"]) .inset-color-group button { color: #879279; }
:where(body[data-theme="modern-nato"]) .tb-brand-short { color: #cd66a3; }
:where(body[data-theme="modern-nato"]) .tb-classif { color: #898989; }
:where(body[data-theme="modern-nato"]) .ed-section > summary { color: #c38f35; }
:where(body[data-theme="modern-nato"]) .drop-zone.has-image { color: #768c65; }
:where(body[data-theme="modern-nato"]) .img-credit { color: #8f99a3; }
:where(body[data-theme="modern-nato"]) .logo-mode button.active { color: #c38f35; }
:where(body[data-theme="modern-nato"]) .logo-thumb-none { color: #8d97a2; }
:where(body[data-theme="modern-nato"]) .cartouche-point-toggle input:checked + .point-marker { color: #f25353; }
:where(body[data-theme="modern-nato"]) .btn-remove-row { color: #898989; }
:where(body[data-theme="modern-nato"]) .btn-add-inset { color: #798f69; }
:where(body[data-theme="modern-nato"]) .inset-num { color: #7b906b; }
:where(body[data-theme="modern-nato"]) .inset-color-group button.active { color: #c28d30; }
:where(body[data-theme="modern-east"]) .tb-brand-short { color: #ce69a5; }
:where(body[data-theme="modern-east"]) .tb-classif { color: #bd7979; }
:where(body[data-theme="modern-east"]) .ed-section > summary { color: #c6943d; }
:where(body[data-theme="modern-east"]) .drop-zone.has-image { color: #768c65; }
:where(body[data-theme="modern-east"]) .img-credit { color: #969b8c; }
:where(body[data-theme="modern-east"]) .logo-mode button.active { color: #c6943d; }
:where(body[data-theme="modern-east"]) .logo-thumb-none { color: #94998a; }
:where(body[data-theme="modern-east"]) .cartouche-point-toggle input:checked + .point-marker { color: #f25757; }
:where(body[data-theme="modern-east"]) .btn-remove-row { color: #bd7979; }
:where(body[data-theme="modern-east"]) .btn-add-inset { color: #7d916d; }
:where(body[data-theme="modern-east"]) .inset-num { color: #7d916d; }
:where(body[data-theme="modern-east"]) .inset-color-group button.active { color: #c38f35; }
:where(body[data-theme="modern-east"]) .dr-tool.on { color: #ece8e0; }
:where(body[data-theme="modern-east"]) .btn-replace { color: #888e78; }
:where(body[data-theme="modern-east"]) .ed-label { color: #868d76; }
:where(body[data-theme="modern-east"]) .logo-mode button { color: #888e78; }
:where(body[data-theme="modern-east"]) .btn-upload-logo { color: #888e78; }
:where(body[data-theme="modern-east"]) .logo-mode-label { color: #828971; }
:where(body[data-theme="modern-east"]) .amorce-marker { color: #888e78; }
:where(body[data-theme="modern-east"]) .shape-color-group button { color: #888e78; }
:where(body[data-theme="modern-east"]) .inset-color-group button { color: #888e78; }
:where(body[data-theme="cw-nato"]) .preview-placeholder { color: #897e60; }
:where(body[data-theme="cw-soviet"]) .drop-zone { color: #7e8b70; }
:where(body[data-theme="cw-soviet"]) .preview-placeholder { color: #77826f; }
:where(body[data-theme="modern-nato"]) .preview-placeholder { color: #73808d; }
:where(body[data-theme="modern-east"]) .drop-zone { color: #828971; }
:where(body[data-theme="modern-east"]) .preview-placeholder { color: #7b816e; }
/* MP-20 end */
"""

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS_PATH = os.path.join(HERE, 'assets.json')
if not os.path.isfile(ASSETS_PATH):
    raise SystemExit(f"[ERREUR] Entrée manquante : {ASSETS_PATH} (assets.json attendu à la racine du dépôt)")

APP_VERSION = "1.1.1"

with open(ASSETS_PATH) as f:
    A = json.load(f)

# ---------- Photo de l'exemple (lot mp-exemples-demarrer) ----------
# Photo aérienne libre : USDA NAIP, domaine public (recadrage 3:2, 1 200 × 800, niveaux de gris). Le build vérifie
# son sha256 comme celui des assets, et l'embarque en data URL.
import hashlib
RS_EXAMPLE_IMG_PATH = os.path.join(HERE, 'samples', 'rs_example_naip.jpg')
RS_EXAMPLE_IMG_SHA256 = 'c617233144c7092aa6f1b4063b594bc4d938fdd7a7fc16d3b89f292da933225b'
if not os.path.isfile(RS_EXAMPLE_IMG_PATH):
    raise SystemExit(f"[ERREUR] Entrée manquante : {RS_EXAMPLE_IMG_PATH} (samples/rs_example_naip.jpg attendu)")
with open(RS_EXAMPLE_IMG_PATH, 'rb') as f:
    _rs_example_bytes = f.read()
if hashlib.sha256(_rs_example_bytes).hexdigest() != RS_EXAMPLE_IMG_SHA256:
    raise SystemExit("[ERREUR] samples/rs_example_naip.jpg : le sha256 ne correspond pas à la photo attendue")
RS_EXAMPLE_IMG_B64 = base64.b64encode(_rs_example_bytes).decode('ascii')

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

# ---------- Annoter au doigt (lot mp-rs-v1.1.0) ----------
# Icônes de la barre : celles de la maquette du CdP (SVG 24×24, trait currentColor).
RSD_ICONS = {
 "select": "<svg viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linejoin=\"round\" stroke-linecap=\"round\"><path d=\"M6 3l12 9-5.2 1.1L15.6 20l-2.6 1.1-2.8-6.9L6 18z\"/></svg>",
 "rect": "<svg viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linejoin=\"round\" stroke-linecap=\"round\"><rect x=\"3.5\" y=\"6\" width=\"17\" height=\"12\"/></svg>",
 "ellipse": "<svg viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linejoin=\"round\" stroke-linecap=\"round\"><ellipse cx=\"12\" cy=\"12\" rx=\"9\" ry=\"6\"/></svg>",
 "poly": "<svg viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linejoin=\"round\" stroke-linecap=\"round\"><path d=\"M3 18l6-9 6 5 6-9\"/><rect x=\"7.5\" y=\"7.5\" width=\"3\" height=\"3\" fill=\"currentColor\"/><rect x=\"13.5\" y=\"12.5\" width=\"3\" height=\"3\" fill=\"currentColor\"/></svg>",
 "arrow": "<svg viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linejoin=\"round\" stroke-linecap=\"round\"><path d=\"M4 20L18.5 5.5\"/><path d=\"M11 5h8v8\"/></svg>",
 "bracket": "<svg viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linejoin=\"round\" stroke-linecap=\"round\"><path d=\"M4 9v6M20 9v6M4 12h16\"/></svg>",
 "label": "<svg viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linejoin=\"round\" stroke-linecap=\"round\"><path d=\"M5 6V4h14v2M12 4v16M9 20h6\"/></svg>",
 "inset": "<svg viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linejoin=\"round\" stroke-linecap=\"round\"><circle cx=\"10\" cy=\"10\" r=\"6\"/><path d=\"M14.5 14.5L20.5 20.5\"/><path d=\"M7.5 10h5M10 7.5v5\"/></svg>",
 "props": "<svg viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linejoin=\"round\" stroke-linecap=\"round\"><path d=\"M4 7h10M18 7h2M4 17h4M12 17h8\"/><circle cx=\"16\" cy=\"7\" r=\"2\"/><circle cx=\"10\" cy=\"17\" r=\"2\"/></svg>",
 "dup": "<svg viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linejoin=\"round\" stroke-linecap=\"round\"><rect x=\"8\" y=\"8\" width=\"12\" height=\"12\"/><path d=\"M4 16V4h12\"/></svg>",
 "del": "<svg viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linejoin=\"round\" stroke-linecap=\"round\"><path d=\"M4 7h16M9 7V4h6v3M6 7l1 13h10l1-13M10 11v6M14 11v6\"/></svg>",
 "ok": "<svg viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2.6\"><path d=\"M4 12.5l5 5L20 6.5\"/></svg>",
 "move": "<svg viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linejoin=\"round\" stroke-linecap=\"round\"><path d=\"M12 2v20M2 12h20M12 2l-3 3M12 2l3 3M12 22l-3-3M12 22l3-3M2 12l3-3M2 12l3 3M22 12l-3-3M22 12l-3 3\"/></svg>",
 "vtx": "<svg viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linejoin=\"round\" stroke-linecap=\"round\"><rect x=\"8\" y=\"8\" width=\"8\" height=\"8\"/><path d=\"M3 3l18 18\"/></svg>"
}

RSD_CSS = r'''/* ======== ANNOTER AU DOIGT (lot mp-rs-v1.1.0) — la barre, le message, la fiche et les poignées du Route Planner sur l'aperçu ========
   Valeurs de la maquette du CdP (R297), reprises telles quelles ; les règles des calques, des pas à pas et de la grille n'ont pas d'élément ici. */
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
.dr-hint .dr-acts[hidden] { display: none; }

.dr-bar { display: flex; align-items: stretch; gap: 8px; background: var(--olive-deep); border: 2px solid var(--amber-dark);
  box-shadow: 0 2px 8px rgba(0,0,0,.45); padding: 6px; box-sizing: border-box; }
.dr-tools { display: flex; flex: 1 1 auto; justify-content: flex-end; gap: 0; min-width: 0; }
.dr-tool { display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 3px; flex: 1 1 0; min-width: 44px; max-width: 72px;
  min-height: 52px; background: transparent; color: var(--paper); border: 1px solid var(--khaki); border-left: none; cursor: pointer; padding: 4px 2px; }
.dr-tool:first-child { border-left: 1px solid var(--khaki); }
.dr-tool svg { width: 22px; height: 22px; display: block; }
.dr-tool i { font-style: normal; font-weight: 700; font-size: 10px; letter-spacing: 1px; text-transform: uppercase; line-height: 1; }
.dr-tool.on { background: var(--amber-dark); color: var(--paper-light); border-color: var(--amber); box-shadow: inset 0 -3px 0 var(--amber); }
.dr-tool.danger { color: #f0a090; }
.dr-sel { flex: 1 1 auto; min-width: 0; display: flex; flex-direction: column; justify-content: center; padding: 0 6px; color: var(--paper-light); }
.dr-sel small { font-weight: 700; font-size: 10px; letter-spacing: 1.5px; color: var(--amber); text-transform: uppercase; }
.dr-sel span { font-family: var(--f-mono); font-size: 13px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.dr-bar.selmode .dr-tools { flex: 0 0 auto; }
.dr-bar.selmode .dr-tool { width: 60px; flex: none; }

/* la fiche de propriétés (feuille du bas) */
.dr-sheet { position: absolute; right: 10px; bottom: 100px; width: 340px; max-width: calc(100% - 20px); box-sizing: border-box; z-index: 1001;
  background: var(--olive-deep); border: 2px solid var(--amber-dark); box-shadow: 0 4px 14px rgba(0,0,0,.5); color: var(--paper-light);
  padding: 10px 12px 12px; font-family: var(--f-ui); max-height: calc(100% - 130px); overflow: auto; }
.dr-sheet[hidden] { display: none; }
.dr-sheet .sh-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px; }
.dr-sheet .sh-head b { font-weight: 700; font-size: 11px; letter-spacing: 1.5px; color: var(--amber); text-transform: uppercase; }
.dr-sheet .sh-x { width: 40px; height: 40px; background: transparent; border: 1px solid var(--khaki); color: var(--paper); font-size: 16px; cursor: pointer; }
.dr-f { margin-top: 8px; }
.dr-f > label { display: block; font-weight: 700; font-size: 10px; letter-spacing: 1.5px; color: var(--amber); text-transform: uppercase; margin-bottom: 4px; }
.dr-f input[type=text], .dr-f input[type=number], .dr-f select { width: 100%; height: 40px; box-sizing: border-box; font-family: var(--f-mono); font-size: 13px;
  padding: 0 8px; background: var(--paper-light); color: var(--ink); border: 1px solid var(--khaki); border-left: 3px solid var(--amber-dark); }
.dr-sw { display: flex; gap: 6px; flex-wrap: wrap; }
.dr-sw button { width: 36px; height: 36px; border: 2px solid var(--khaki); cursor: pointer; padding: 0; position: relative; }
.dr-sw button.on { border-color: var(--amber); box-shadow: 0 0 0 2px var(--olive-deep), 0 0 0 4px var(--amber); }
.dr-seg { display: flex; } .dr-seg .tb-btn { flex: 1; height: 40px; min-width: 0; padding: 0 6px; }

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

@media (max-width: 600px) {
  .dr-ui { left: 6px; right: 6px; }
  .dr-bar { flex-wrap: wrap; gap: 6px; }
  .dr-tool { min-height: 50px; }
  .dr-bar.selmode .dr-tool { width: 52px; }
  .dr-sheet { left: 6px; right: 6px; width: auto; max-width: none; bottom: 94px; }
  .dr-hint .dr-msg { font-size: 12px; }
  .dr-sheet { padding: 8px 10px 10px; bottom: 90px; max-height: calc(100% - 100px); }
  .dr-f { margin-top: 6px; }
  .dr-sw { gap: 5px; } .dr-sw button { width: 34px; height: 34px; }
  .dr-sheet .sh-x { width: 36px; height: 36px; }
}

/* 1.7.0 : barrettes de bord, rotation, réglages de l'objet à venir */
@media (max-width: 600px) {
  .dr-tool { min-width: 0; padding: 4px 0; }
  .dr-tool i { font-size: 10px; letter-spacing: .4px; }
  .dr-tool svg { width: 21px; height: 21px; }
}
.dr-h.v.edge i { width: 22px; height: 10px; margin: -5px 0 0 -11px; border-radius: 2px; background: var(--paper-light); }
.dr-h.v.corner i { width: 14px; height: 14px; margin: -7px 0 0 -7px; border-radius: 2px; background: var(--paper-light); border: 2px solid var(--amber-dark); }
.dr-h.r.rot i { width: 22px; height: 22px; margin: -11px 0 0 -11px; }
.dr-h.r.rot i::after { content: '⟳'; position: absolute; inset: 0; font: 700 16px/18px var(--f-ui); color: var(--ink); text-align: center; }
.dr-hint .tb-btn.mq-props svg { width: 18px; height: 18px; }
.dr-hint .tb-btn.mq-props.on { background: var(--amber-dark); border-color: var(--amber); }

/* Recon Station : la couche des poignées, au-dessus du canevas */
.rsd-ov { position: absolute; inset: 0; pointer-events: none; z-index: 5; }
.rsd-svg, .rsd-prev { position: absolute; left: 0; top: 0; pointer-events: none; overflow: visible; }
.rsd-h { position: absolute; width: 44px; height: 44px; margin: -22px 0 0 -22px; pointer-events: auto; touch-action: none; cursor: grab; }
.rsd-h.mv.src i { background: var(--paper-light); color: var(--amber-dark); border-color: var(--amber-dark); }
.rsd-h.r.corner i { border-radius: 2px; width: 14px; height: 14px; margin: -7px 0 0 -7px; }
.rsd-ui { z-index: 20; bottom: 14px; }
.rsd-sheet { z-index: 21; bottom: 92px; }
.rsd-sheet.mq-draft { bottom: 150px; }
.rsd-ui .dr-bar { justify-content: center; }
.rsd-ui .dr-tools { justify-content: center; flex: 1 1 auto; }
.rsd-ui .dr-tool { max-width: 78px; }
.dr-sw.rsd-sw button { width: auto; min-width: 86px; height: 40px; padding: 0 10px; display: flex; align-items: center; justify-content: center; }
.dr-sw.rsd-sw button span { font-family: var(--f-ui); font-weight: 700; font-size: 11px; letter-spacing: 1.2px; text-transform: uppercase; color: #fff; }
.dr-sw.rsd-sw button[data-v=white] span { color: #111; }
@media (max-width: 600px) {
  .rsd-ui .dr-tool { min-width: 0; padding: 4px 0; }
  .rsd-ui .dr-tool i { font-size: 10px; letter-spacing: .4px; }
  .rsd-ui .dr-tool svg { width: 21px; height: 21px; }
  .rsd-sheet { bottom: 86px; }
}
/* sous 1 101 px, la barre d'onglets (48 px, fixe) occupe le bas : la barre de dessin et la fiche se posent au-dessus */
@media (max-width: 1100px) {
  .rsd-ui { position: fixed; left: 10px; right: 10px; bottom: 60px; }
  .rsd-sheet { position: fixed; bottom: 140px; }
  .rsd-sheet.mq-draft { bottom: 196px; }
}
@media (max-width: 600px) { .rsd-ui { left: 6px; right: 6px; } .rsd-sheet { bottom: 134px; } .rsd-sheet.mq-draft { bottom: 190px; } }
/* la bande réservée en bas de l'aperçu : l'image ne passe pas sous la barre ni sous le message (--rsd-band, mesurée en JS) */
.preview-inner { padding-bottom: var(--rsd-band, 16px); }
/* les boutons de la barre, du message et de la fiche : ceux du Route Planner (RS a son propre .tb-btn clair) */
.rsd-ui .tb-btn, .rsd-sheet .tb-btn {
  font-family: var(--f-ui); font-weight: 700; letter-spacing: 1.5px; font-size: 12px; text-transform: uppercase;
  background: transparent; color: var(--paper); border: 1px solid var(--khaki); height: 40px; min-width: 44px;
  padding: 0 12px; cursor: pointer; display: inline-flex; align-items: center; justify-content: center; gap: 6px; border-radius: 0; box-shadow: none; }
.rsd-ui .tb-btn.on, .rsd-sheet .tb-btn.on, .rsd-ui .tb-btn.go { background: var(--amber-dark); color: var(--paper-light); border-color: var(--amber); box-shadow: inset 0 -3px 0 var(--amber); }
.rsd-sheet .dr-seg .tb-btn + .tb-btn { border-left: none; }
.rsd-ui .dr-hint .tb-btn { height: 36px; font-size: 11px; padding: 0 10px; }
.rsd-sheet .sh-x { background: transparent; color: var(--paper); border: 1px solid var(--khaki); }
.rsd-sheet input[type=text] { width: 100%; height: 40px; box-sizing: border-box; font-family: 'Roboto Mono', monospace; font-size: 13px; padding: 0 8px;
  background: var(--paper-light); color: var(--ink); border: 1px solid var(--khaki); border-left: 3px solid var(--amber-dark); }
'''

RSD_JS = r'''// =============================================================
//  ANNOTER AU DOIGT — lot mp-rs-v1.1.0
//  Un toucher pose, une poignée ajuste. La méthode du mode Dessin du Route Planner, sur un canevas :
//  la barre, le message et la fiche sont du DOM posé sur l'aperçu ; les poignées (cible 44 px) vivent dans une
//  couche DOM au-dessus du canevas ; rien de cela n'entre dans composeRecon ni dans l'export.
//  Le modèle des annotations (STATE.annotations) et son enregistrement ne changent pas : aucun champ neuf,
//  aucune clé de travail (l'outil, la sélection, le brouillon, la couleur ne s'enregistrent jamais).
// =============================================================
const RSD_TOOLS = ['select', 'rect', 'ellipse', 'poly', 'arrow', 'bracket', 'label', 'inset'];
const RSD_TYPES = ['rect', 'ellipse', 'poly', 'arrow', 'bracket', 'label', 'inset'];
const RSD_COLORS = { red: '#E22', black: '#000', white: '#fff' };
const RSD_HIT = { path: 22, label: 44, inset: 8, ellipseQ: 1.3 };   /* rayons de toucher, en pixels (l'ellipse : valeur normalisée) */
const RSD_COPY_PX = 24;        /* une copie : 24 px à droite, 24 px en bas, à l'écran */
const RSD_MOVE_TOL = 4;        /* un glisser de poignée (ou de repère) commence au-delà de 4 px */
const RSD_TAP_TOL = 8;         /* au-delà de 8 px, un toucher sur l'image n'est plus un toucher */
const RSD_ROT_PX = 40;         /* la poignée de rotation du cadre : 40 px au-delà du milieu du bord haut */
const RSD_MIN_PX = 8;          /* le côté d'un cadre : 8 px au moins */
const RSD_SHEET_GAP = 6, RSD_SHEET_TOP = 10, RSD_SHEET_MIN = 160;
const RSD_ICONS = __RSD_ICONS__;

/* L'état : en mémoire seulement */
const RSD = {
  tool: 'select',       /* select · rect · ellipse · poly · arrow · bracket · label · inset */
  sel: null,            /* l'id de l'annotation choisie */
  vtx: -1,              /* le point choisi d'un tracé choisi */
  sheet: false,         /* la fiche « Réglages » est ouverte */
  build: null,          /* un tracé, une flèche ou un crochet en cours : { kind, pts: [{x, y}] } (fractions de l'image) */
  draft: null,          /* le brouillon des réglages de l'objet à venir : { n, tool, it, vals } (jamais enregistré) */
  draftN: 0,
  color: 'red',         /* la dernière couleur choisie dans une fiche */
  hs: [],               /* les poignées : { el, pos, upd, tap, start, move, end } */
  raf: 0, sheetKey: '', busy: false, sig: '', ro: null
};

const rsd$ = id => document.getElementById(id);
const rsdEsc = s => escapeAttr(String(s == null ? '' : s));
const rsdCl = (v, lo, hi) => Math.min(hi, Math.max(lo, v));
const rsdSub = (s, o) => Object.keys(o).reduce((r, k) => r.split('{' + k + '}').join(o[k]), s);

function rsdSel() {
  if (!RSD.sel) return null;
  return (STATE.annotations || []).find(a => a.id === RSD.sel && RSD_TYPES.indexOf(a.type) !== -1) || null;
}
function rsdColorOf(a) { return a.color || (a.type === 'inset' ? 'white' : 'red'); }

/* La vue : le canevas tel qu'il est posé, en pixels de l'écran (ov = la couche des poignées) */
function rsdView() {
  const cv = rsd$('preview-canvas'), ov = rsd$('rsd-ov');
  const c = cv.getBoundingClientRect(), o = ov.getBoundingClientRect();
  return { cl: c.left, ct: c.top, w: c.width, h: c.height, l: c.left - o.left, t: c.top - o.top, ow: o.width, oh: o.height,
    ok: !cv.hidden && c.width > 0 && c.height > 0 };
}
const rsdAtN = (v, nx, ny) => ({ x: v.l + nx * v.w, y: v.t + ny * v.h });      /* fractions de l'image → couche */
const rsdAtP = (v, px, py) => ({ x: v.l + px, y: v.t + py });                   /* pixels du canevas → couche */

/* ---------- la géométrie, en pixels du canevas à l'écran ---------- */
function rsdRectG(a, v) {
  const th = (a.angle || 0) * Math.PI / 180;
  return { cx: (a.x + a.w / 2) * v.w, cy: (a.y + a.h / 2) * v.h, hw: a.w * v.w / 2, hh: a.h * v.h / 2,
    ux: Math.cos(th), uy: Math.sin(th), vx: -Math.sin(th), vy: Math.cos(th) };
}
function rsdRectCorners(g) {
  return [[-1, -1], [1, -1], [1, 1], [-1, 1]].map(k => ({ x: g.cx + k[0] * g.hw * g.ux + k[1] * g.hh * g.vx, y: g.cy + k[0] * g.hw * g.uy + k[1] * g.hh * g.vy }));
}
function rsdBracketG(a, v) {
  const x1 = a.x1 * v.w, y1 = a.y1 * v.h, x2 = a.x2 * v.w, y2 = a.y2 * v.h;
  const dx = x2 - x1, dy = y2 - y1, len = Math.hypot(dx, dy) || 1, ux = dx / len, uy = dy / len;
  const m = Math.min(v.w, v.h), dep = (a.depth || 0.04) * m;
  return { x1: x1, y1: y1, x2: x2, y2: y2, px: -uy, py: ux, m: m, dep: dep, ox: -uy * dep, oy: ux * dep };
}
let RSD_MEAS = null;
function rsdLabelBox(a, v) {      /* le rectangle qu'occupe un texte à l'écran (mesuré avec les polices de composeRecon) */
  const W = SOURCE_IMG ? SOURCE_IMG.naturalWidth : 1920, k = v.w / W, sc = W / 1920, s = n => Math.round(n * sc);
  if (!RSD_MEAS) RSD_MEAS = document.createElement('canvas').getContext('2d');
  let fs, font, bw, bh;
  if (a.style === 'stamp') { fs = s(22); font = '400 ' + fs + 'px "Roboto Mono",monospace'; }
  else if (a.style === 'cursive') { fs = s(36); font = '400 ' + fs + 'px "Caveat",cursive'; }
  else { fs = s(22); font = '400 ' + fs + 'px "Roboto Mono",monospace'; }
  RSD_MEAS.font = font;
  const tw = RSD_MEAS.measureText(a.text || '').width;
  if (a.style === 'stamp') { bw = tw + s(8) * 2; bh = fs + s(8) * 1.4; } else { bw = tw + s(6); bh = fs * 1.15; }
  bw = Math.max(bw * k, 24); bh = Math.max(bh * k, 18);
  return { x: a.x * v.w - bw / 2, y: a.y * v.h - bh / 2, w: bw, h: bh };
}

/* ---------- la couche : contour de la sélection, tracé en cours ---------- */
function rsdPts(list) { return list.map(p => p.x.toFixed(2) + ',' + p.y.toFixed(2)).join(' '); }
function rsdContourShape(a, v) {
  if (a.type === 'rect') return '<polygon points="' + rsdPts(rsdRectCorners(rsdRectG(a, v))) + '"/>';
  if (a.type === 'ellipse') return '<ellipse cx="' + (a.cx * v.w) + '" cy="' + (a.cy * v.h) + '" rx="' + (a.rx * v.w) + '" ry="' + (a.ry * v.h) + '"/>';
  if (a.type === 'poly') {
    const q = (a.pts || []).map(p => ({ x: p.x * v.w, y: p.y * v.h }));
    return '<' + (a.closed ? 'polygon' : 'polyline') + ' points="' + rsdPts(q) + '"/>';
  }
  if (a.type === 'arrow') return '<line x1="' + (a.x1 * v.w) + '" y1="' + (a.y1 * v.h) + '" x2="' + (a.x2 * v.w) + '" y2="' + (a.y2 * v.h) + '"/>';
  if (a.type === 'bracket') {
    const g = rsdBracketG(a, v);
    return '<polyline points="' + rsdPts([{ x: g.x1 + g.ox, y: g.y1 + g.oy }, { x: g.x1, y: g.y1 }, { x: g.x2, y: g.y2 }, { x: g.x2 + g.ox, y: g.y2 + g.oy }]) + '"/>';
  }
  if (a.type === 'label') { const b = rsdLabelBox(a, v); return '<rect x="' + b.x + '" y="' + b.y + '" width="' + b.w + '" height="' + b.h + '"/>'; }
  if (a.type === 'inset') {
    const r = o => '<rect x="' + (o.x * v.w) + '" y="' + (o.y * v.h) + '" width="' + (o.w * v.w) + '" height="' + (o.h * v.h) + '"/>';
    return r(a.src) + r(a.box);
  }
  return '';
}
function rsdContour(v) {
  const svg = rsd$('rsd-svg'), a = rsdSel();
  svg.setAttribute('width', v.ow); svg.setAttribute('height', v.oh);
  const sh = (a && !RSD.build && v.ok) ? rsdContourShape(a, v) : '';
  svg.innerHTML = sh ? '<g class="rsd-contour" transform="translate(' + v.l + ' ' + v.t + ')" fill="none" stroke="#c0892a" stroke-width="7" stroke-opacity="0.45" stroke-linecap="round" stroke-linejoin="round">' + sh + '</g>' : '';
}
/* le tracé en cours (tracé, flèche, crochet) : dessiné à la couleur du brouillon */
function rsdPreviewDraw(v) {
  v = v || rsdView();
  const svg = rsd$('rsd-prev'), b = RSD.build;
  svg.setAttribute('width', v.ow); svg.setAttribute('height', v.oh);
  if (!b || !b.pts.length || !v.ok) { svg.innerHTML = ''; return; }
  const col = RSD_COLORS[RSD.draft ? rsdColorOf(RSD.draft.it) : RSD.color] || RSD_COLORS.red;
  const q = b.pts.map(p => ({ x: p.x * v.w, y: p.y * v.h }));
  const closed = b.kind === 'poly' && RSD.draft && RSD.draft.it.closed;
  const line = (pts, extra) => (pts.length >= 2 ? '<polyline points="' + rsdPts(pts) + '" ' + extra + '/>' : '');
  let h = '<g transform="translate(' + v.l + ' ' + v.t + ')" fill="none" stroke-linecap="round" stroke-linejoin="round">';
  const pts = closed && q.length >= 3 ? q.concat([q[0]]) : q;
  h += line(pts, 'stroke="rgba(0,0,0,.45)" stroke-width="6"') + line(pts, 'stroke="' + col + '" stroke-width="3"');
  if (b.kind === 'poly' && !closed && q.length >= 3) h += line([q[q.length - 1], q[0]], 'stroke="' + col + '" stroke-width="2" stroke-opacity="0.7" stroke-dasharray="6 6"');
  svg.innerHTML = h + '</g>';
}

/* ---------- les poignées : 44 px de cible, 16 px visibles ---------- */
function rsdMk(cls, pos, cb, keepEl) {
  const mid = cls.indexOf('mid') !== -1, mv = cls.indexOf('mv') !== -1;
  const el = document.createElement('div');
  el.className = 'rsd-h dr-h ' + cls;
  el.innerHTML = '<i>' + (mid ? '+' : (mv ? RSD_ICONS.move : '')) + '</i>';
  rsd$('rsd-ov').appendChild(el);
  const h = Object.assign({ el: el, pos: pos }, cb || {});
  rsdBind(h);
  RSD.hs.push(h);
  return h;
}

/* Un toucher (sans glisser) appelle h.tap ; un glisser appelle h.start, h.move(delta en px, évènement) puis h.end */
function rsdBind(h) {
  const el = h.el;
  let st = null;
  el.addEventListener('pointerdown', e => {
    if (e.pointerType === 'mouse' && e.button !== 0) return;
    st = { id: e.pointerId, x0: e.clientX, y0: e.clientY, moved: false };
    try { el.setPointerCapture(e.pointerId); } catch (x) { /* ignore */ }
  });
  el.addEventListener('pointermove', e => {
    if (!st || e.pointerId !== st.id) return;
    const d = { x: e.clientX - st.x0, y: e.clientY - st.y0 };
    if (!st.moved) {
      if (Math.hypot(d.x, d.y) < RSD_MOVE_TOL) return;
      st.moved = true;
      RSD.busy = true;
      if (h.start) h.start(e);
    }
    if (h.move) h.move(d, e);
  });
  const stop = e => {
    if (!st || e.pointerId !== st.id) return;
    const was = st;
    st = null;
    try { el.releasePointerCapture(e.pointerId); } catch (x) { /* ignore */ }
    if (was.moved) { RSD.busy = false; if (h.end) h.end(); }
    else if (e.type === 'pointerup' && h.tap) h.tap();
  };
  el.addEventListener('pointerup', stop);
  el.addEventListener('pointercancel', stop);
}

function rsdPlaceOne(h, v) {
  const p = h.pos(v);
  h.el.style.left = p.x + 'px';
  h.el.style.top = p.y + 'px';
  if (h.upd) h.upd(v);
}
/* Tout se replace : les poignées, le contour, le tracé en cours */
function rsdPlace() {
  const v = rsdView();
  RSD.hs.forEach(h => { h.el.style.display = v.ok ? '' : 'none'; if (v.ok) rsdPlaceOne(h, v); });
  rsdContour(v);
  rsdPreviewDraw(v);
}

/* Déplacer des couples (x, y) en fractions, ensemble, sans quitter l'image : bb(base) donne l'étendue [x0, y0, x1, y1] de ce qui bouge */
function rsdMoveCb(refs, bb, build) {
  let base = null, v = null;
  return {
    start: () => { v = rsdView(); base = refs.map(r => ({ x: r[0][r[1]], y: r[0][r[2]] })); },
    move: d => {
      let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
      if (bb) { const b = bb(base); x0 = b[0]; y0 = b[1]; x1 = b[2]; y1 = b[3]; }
      else base.forEach(p => { x0 = Math.min(x0, p.x); y0 = Math.min(y0, p.y); x1 = Math.max(x1, p.x); y1 = Math.max(y1, p.y); });
      const dx = rsdCl(d.x / v.w, -x0, 1 - x1), dy = rsdCl(d.y / v.h, -y0, 1 - y1);
      refs.forEach((r, i) => { r[0][r[1]] = base[i].x + dx; r[0][r[2]] = base[i].y + dy; });
      rsdLive();
    },
    end: build ? rsdBuildEnd : rsdCommit
  };
}
function rsdMeanPts(pts) { return { x: pts.reduce((s, p) => s + p.x, 0) / pts.length, y: pts.reduce((s, p) => s + p.y, 0) / pts.length }; }
function rsdMoveHandle(a, pts) {   /* ✥ : tout bouge ensemble */
  return rsdMoveCb(pts.map(p => [p, 'x', 'y']));
}
function rsdEdgeIcon(h, deg) { const i = h.el.firstChild; if (i) i.style.transform = deg ? 'rotate(' + deg + 'deg)' : ''; }

/* Une poignée d'angle : au-dessus des bords ; sous 88 px de plus petit côté à l'écran, le bord l'emporte (règle du Route Planner) */
const RSD_CORNERS = [[-1, -1], [1, -1], [1, 1], [-1, 1]];
function rsdCornerZ(h, size) { h.upd = v => { h.el.style.zIndex = size(v) > 88 ? '' : '-1'; }; }

/* ----- le cadre : quatre barrettes de bord, quatre angles, la rotation, ✥ ----- */
function rsdRectHandles(a) {
  ['l', 'r', 't', 'b'].forEach(side => {
    const horiz = side === 'l' || side === 'r';
    const nrm = g => side === 'r' ? [g.ux, g.uy] : side === 'l' ? [-g.ux, -g.uy] : side === 't' ? [-g.vx, -g.vy] : [g.vx, g.vy];
    const h = rsdMk('v edge', v => { const g = rsdRectG(a, v), n = nrm(g), e = horiz ? g.hw : g.hh; return rsdAtP(v, g.cx + n[0] * e, g.cy + n[1] * e); }, {});
    h.upd = () => rsdEdgeIcon(h, (a.angle || 0) + (horiz ? 90 : 0));      /* la barrette suit le sens de son bord, et le garde pendant une rotation */
    let B = null;
    /* un bord se tire seul, le long de sa normale ; le bord opposé reste en place (mesuré en pixels, contre l'état du début du glisser) */
    h.start = () => { const v = rsdView(), g = rsdRectG(a, v); B = { v: v, g: g, n: nrm(g), s0: horiz ? 2 * g.hw : 2 * g.hh }; };
    h.move = d => {
      const s = Math.max(RSD_MIN_PX, B.s0 + d.x * B.n[0] + d.y * B.n[1]), dd = s - B.s0;
      const cx = B.g.cx + B.n[0] * dd / 2, cy = B.g.cy + B.n[1] * dd / 2;
      if (horiz) a.w = s / B.v.w; else a.h = s / B.v.h;
      a.x = cx / B.v.w - a.w / 2; a.y = cy / B.v.h - a.h / 2;
      rsdLive();
    };
    h.end = rsdCommit;
  });
  RSD_CORNERS.forEach(k => {
    const sx = k[0], sy = k[1];
    const h = rsdMk('v corner', v => { const g = rsdRectG(a, v); return rsdAtP(v, g.cx + sx * g.hw * g.ux + sy * g.hh * g.vx, g.cy + sx * g.hw * g.uy + sy * g.hh * g.vy); }, {});
    rsdCornerZ(h, v => { const g = rsdRectG(a, v); return Math.min(2 * g.hw, 2 * g.hh); });
    let B = null;
    /* un angle se tire seul ; le coin opposé reste en place, l'angle ne change pas (pixels de l'écran, repère tourné du cadre, contre l'état du début du glisser) */
    h.start = () => {
      const v = rsdView(), g = rsdRectG(a, v);
      B = { v: v, g: g, p: { x: g.cx + sx * g.hw * g.ux + sy * g.hh * g.vx, y: g.cy + sx * g.hw * g.uy + sy * g.hh * g.vy },
            o: { x: g.cx - sx * g.hw * g.ux - sy * g.hh * g.vx, y: g.cy - sx * g.hw * g.uy - sy * g.hh * g.vy } };
    };
    h.move = d => {
      const g = B.g, qx = B.p.x + d.x - B.o.x, qy = B.p.y + d.y - B.o.y;
      const w = Math.max(RSD_MIN_PX, sx * (qx * g.ux + qy * g.uy)), hh = Math.max(RSD_MIN_PX, sy * (qx * g.vx + qy * g.vy));
      const cx = B.o.x + (sx * w * g.ux + sy * hh * g.vx) / 2, cy = B.o.y + (sx * w * g.uy + sy * hh * g.vy) / 2;
      a.w = w / B.v.w; a.h = hh / B.v.h;
      a.x = cx / B.v.w - a.w / 2; a.y = cy / B.v.h - a.h / 2;
      rsdLive();
    };
    h.end = rsdCommit;
  });
  let c = null;
  const rot = rsdMk('r rot', v => { const g = rsdRectG(a, v), d = g.hh + RSD_ROT_PX; return rsdAtP(v, g.cx - g.vx * d, g.cy - g.vy * d); }, {});
  rot.start = () => { const v = rsdView(), g = rsdRectG(a, v); c = { x: v.cl + g.cx, y: v.ct + g.cy }; };
  rot.move = (d, e) => {                    /* même convention que la base : atan2(dx, −dy), au dixième de degré */
    a.angle = Math.round(Math.atan2(e.clientX - c.x, -(e.clientY - c.y)) * 1800 / Math.PI) / 10;
    rsdLive();
  };
  rot.end = rsdCommit;
  rsdMk('mv', v => rsdAtN(v, a.x + a.w / 2, a.y + a.h / 2), rsdMoveCb([[a, 'x', 'y']], b => [b[0].x + a.w / 2, b[0].y + a.h / 2, b[0].x + a.w / 2, b[0].y + a.h / 2]));
}

/* ----- l'ellipse : quatre barrettes (gauche, droite → rx ; haut, bas → ry), le bord opposé en place ----- */
function rsdEllipseHandles(a) {
  [['l', -1, 0], ['r', 1, 0], ['t', 0, -1], ['b', 0, 1]].forEach(k => {
    const sx = k[1], sy = k[2];
    const h = rsdMk('v edge', v => rsdAtN(v, a.cx + sx * a.rx, a.cy + sy * a.ry), {});
    h.upd = () => rsdEdgeIcon(h, sx ? 90 : 0);
    let B = null;
    h.start = () => { B = { v: rsdView(), cx: a.cx, cy: a.cy, rx: a.rx, ry: a.ry }; };
    h.move = d => {
      if (sx) {
        const r = Math.max(0.005, B.rx + sx * (d.x / B.v.w) / 2), fixed = B.cx - sx * B.rx;
        a.rx = r; a.cx = fixed + sx * r;
      } else {
        const r = Math.max(0.005, B.ry + sy * (d.y / B.v.h) / 2), fixed = B.cy - sy * B.ry;
        a.ry = r; a.cy = fixed + sy * r;
      }
      rsdLive();
    };
    h.end = rsdCommit;
  });
  rsdMk('mv', v => rsdAtN(v, a.cx, a.cy), rsdMoveCb([[a, 'cx', 'cy']], b => [b[0].x - a.rx, b[0].y - a.ry, b[0].x + a.rx, b[0].y + a.ry]));
}

/* ----- le tracé : un carré par point, un « + » au milieu de chaque segment, ✥ ----- */
function rsdPolyHandles(a, keep, keepIdx) {
  const n = a.pts.length, area = a.closed === true;
  for (let k = 0; k < n; k++) {
    if (keep && k === keepIdx) continue;
    const h = rsdMk('v' + (RSD.vtx === k ? ' on' : ''), v => rsdAtN(v, a.pts[k].x, a.pts[k].y), rsdMoveCb([[a.pts[k], 'x', 'y']]));
    h.tap = () => { RSD.vtx = RSD.vtx === k ? -1 : k; rsdBuildHandles(); rsdSyncUi(); };
  }
  const segs = area ? (n > 2 ? n : 1) : n - 1;
  const mvH = () => rsdMk('mv', v => { const m = rsdMeanPts(a.pts); return rsdAtN(v, m.x, m.y); }, rsdMoveHandle(a, a.pts));
  if (n < 3) mvH();                       /* deux points : le « + » est au même endroit que ✥ ; il reste au-dessus */
  for (let k = 0; k < segs; k++) {
    const ia = k, ib = (k + 1) % n, at = k + 1;
    const midPt = () => ({ x: (a.pts[ia].x + a.pts[ib].x) / 2, y: (a.pts[ia].y + a.pts[ib].y) / 2 });
    const h = rsdMk('mid', v => { const m = midPt(); return rsdAtN(v, m.x, m.y); }, {});
    h.tap = () => {
      const m = midPt();
      a.pts.splice(at, 0, { x: m.x, y: m.y });
      RSD.vtx = at;
      rsdChanged();
    };
    h.start = () => {                   /* glisser un « + » : le point s'insère, et se déplace */
      const m = midPt();
      a.pts.splice(at, 0, { x: m.x, y: m.y });
      if (RSD.vtx >= at) RSD.vtx++;
      h.el.classList.remove('mid');
      h.el.classList.add('v');
      h.el.firstChild.textContent = '';
      h.pos = v => rsdAtN(v, a.pts[at].x, a.pts[at].y);
      h.tap = null;
      const cb = rsdMoveCb([[a.pts[at], 'x', 'y']]);
      h.start = cb.start; h.move = cb.move; h.end = () => { cb.end(); rsdBuildHandles(); rsdSyncUi(); };
      cb.start();
      rsdBuildHandles(h, at);
    };
  }
  if (n >= 3) mvH();
}

/* ----- la flèche et le crochet ----- */
function rsdSegHandles(a) {
  rsdMk('v', v => rsdAtN(v, a.x1, a.y1), rsdMoveCb([[a, 'x1', 'y1']]));
  rsdMk('mv', v => rsdAtN(v, (a.x1 + a.x2) / 2, (a.y1 + a.y2) / 2), rsdMoveCb([[a, 'x1', 'y1'], [a, 'x2', 'y2']]));
  if (a.type === 'arrow') { rsdMk('r', v => rsdAtN(v, a.x2, a.y2), rsdMoveCb([[a, 'x2', 'y2']])); return; }
  rsdMk('v', v => rsdAtN(v, a.x2, a.y2), rsdMoveCb([[a, 'x2', 'y2']]));
  /* la profondeur : décalée de depth × min(largeur, hauteur) du côté du crochet ; glissée, depth = la distance signée à la droite des extrémités */
  const dh = rsdMk('r', v => { const g = rsdBracketG(a, v); return rsdAtP(v, (g.x1 + g.x2) / 2 + g.px * g.dep, (g.y1 + g.y2) / 2 + g.py * g.dep); }, {});
  let B = null;
  dh.start = () => { const v = rsdView(); B = { v: v, g: rsdBracketG(a, v) }; };
  dh.move = (d, e) => {
    const g = B.g, fx = e.clientX - B.v.cl, fy = e.clientY - B.v.ct;
    const sd = (fx - g.x1) * g.px + (fy - g.y1) * g.py;
    let dep = Math.round(rsdCl(sd / g.m, -0.2, 0.2) * 10000) / 10000;
    if (dep === 0) dep = sd < 0 ? -0.0001 : 0.0001;       /* 0 se lit 0,04 à l'export : jamais 0 */
    a.depth = dep;
    rsdLive();
  };
  dh.end = rsdCommit;
}

/* ----- la loupe : la zone source et l'encart, chacun quatre barrettes et ✥ ; l'encart garde les proportions de la source ----- */
function rsdInsetFit(a, anchor) {     /* l'encart reste dans l'image : s'il déborde, il se réduit en gardant les proportions */
  const b = a.box, r = a.src.h / a.src.w;
  b.h = b.w * r;
  const k = Math.min(1, (1 - b.x) / b.w, (1 - b.y) / b.h);
  if (k < 1) { b.w *= k; b.h = b.w * r; }
}
function rsdInsetHandles(a) {
  const src = a.src, box = a.box;
  [['l', -1, 0], ['r', 1, 0], ['t', 0, -1], ['b', 0, 1]].forEach(k => {
    const sx = k[1], sy = k[2];
    /* la zone source : un bord bouge, l'opposé reste ; l'encart suit (hauteur = largeur × h / w) */
    const hs = rsdMk('v edge', v => rsdAtN(v, src.x + (sx > 0 ? src.w : sx < 0 ? 0 : src.w / 2), src.y + (sy > 0 ? src.h : sy < 0 ? 0 : src.h / 2)), {});
    hs.upd = () => rsdEdgeIcon(hs, sx ? 90 : 0);
    let B = null;
    hs.start = () => { B = { v: rsdView(), s: Object.assign({}, src), b: Object.assign({}, box) }; };
    hs.move = d => {
      const s0 = B.s, MIN = 0.03;
      let x = s0.x, y = s0.y, w = s0.w, h = s0.h;
      if (sx < 0) { x = rsdCl(s0.x + d.x / B.v.w, 0, s0.x + s0.w - MIN); w = s0.x + s0.w - x; }
      else if (sx > 0) { w = rsdCl(s0.w + d.x / B.v.w, MIN, 1 - s0.x); }
      else if (sy < 0) { y = rsdCl(s0.y + d.y / B.v.h, 0, s0.y + s0.h - MIN); h = s0.y + s0.h - y; }
      else { h = rsdCl(s0.h + d.y / B.v.h, MIN, 1 - s0.y); }
      const keep = { x: src.x, y: src.y, w: src.w, h: src.h }, kb = { x: box.x, y: box.y, w: box.w, h: box.h };
      src.x = x; src.y = y; src.w = w; src.h = h;
      box.x = B.b.x; box.y = B.b.y; box.w = B.b.w;
      rsdInsetFit(a);
      if (Math.min(box.w, box.h) < 0.05) { Object.assign(src, keep); Object.assign(box, kb); return; }   /* l'encart : 0,05 au moins */
      rsdLive();
    };
    hs.end = rsdCommit;
  });
  [['l', -1, 0], ['r', 1, 0], ['t', 0, -1], ['b', 0, 1]].forEach(k => {
    const sx = k[1], sy = k[2];
    /* l'encart : un bord gauche ou droit → sa largeur, la hauteur suit, son bord haut reste ; un bord haut ou bas → sa hauteur, la largeur suit, son bord gauche reste */
    const hb = rsdMk('v edge', v => rsdAtN(v, box.x + (sx > 0 ? box.w : sx < 0 ? 0 : box.w / 2), box.y + (sy > 0 ? box.h : sy < 0 ? 0 : box.h / 2)), {});
    hb.upd = () => rsdEdgeIcon(hb, sx ? 90 : 0);
    let B = null;
    hb.start = () => { B = { v: rsdView(), b: Object.assign({}, box), r: src.h / src.w }; };
    hb.move = d => {
      const b0 = B.b, r = B.r, MIN = 0.05;
      if (sx) {
        const R = b0.x + b0.w;
        const req = sx > 0 ? b0.w + d.x / B.v.w : b0.w - d.x / B.v.w;
        const max = Math.min(sx > 0 ? 1 - b0.x : R, (1 - b0.y) / r), min = Math.max(MIN, MIN / r);
        const w = Math.min(max, Math.max(min, req));
        box.w = w; box.h = w * r; box.x = sx > 0 ? b0.x : R - w; box.y = b0.y;
      } else {
        const Bm = b0.y + b0.h;
        const req = sy > 0 ? b0.h + d.y / B.v.h : b0.h - d.y / B.v.h;
        const max = Math.min(sy > 0 ? 1 - b0.y : Bm, (1 - b0.x) * r), min = Math.max(MIN, MIN * r);
        const h = Math.min(max, Math.max(min, req));
        box.h = h; box.w = h / r; box.y = sy > 0 ? b0.y : Bm - h; box.x = b0.x;
      }
      rsdLive();
    };
    hb.end = rsdCommit;
  });
  /* les angles de la zone source : le coin opposé reste, l'encart suit les proportions et reste dans l'image */
  RSD_CORNERS.forEach(k => {
    const sx = k[0], sy = k[1];
    const h = rsdMk('v corner', v => rsdAtN(v, src.x + (sx > 0 ? src.w : 0), src.y + (sy > 0 ? src.h : 0)), {});
    rsdCornerZ(h, v => Math.min(src.w * v.w, src.h * v.h));
    let B = null;
    h.start = () => { B = { v: rsdView(), s: Object.assign({}, src), b: Object.assign({}, box) }; };
    h.move = d => {
      const s0 = B.s, MIN = 0.03;
      let x = s0.x, y = s0.y, w = s0.w, hh = s0.h;
      if (sx < 0) { x = rsdCl(s0.x + d.x / B.v.w, 0, s0.x + s0.w - MIN); w = s0.x + s0.w - x; } else { w = rsdCl(s0.w + d.x / B.v.w, MIN, 1 - s0.x); }
      if (sy < 0) { y = rsdCl(s0.y + d.y / B.v.h, 0, s0.y + s0.h - MIN); hh = s0.y + s0.h - y; } else { hh = rsdCl(s0.h + d.y / B.v.h, MIN, 1 - s0.y); }
      const keep = { x: src.x, y: src.y, w: src.w, h: src.h }, kb = { x: box.x, y: box.y, w: box.w, h: box.h };
      src.x = x; src.y = y; src.w = w; src.h = hh;
      box.x = B.b.x; box.y = B.b.y; box.w = B.b.w;
      rsdInsetFit(a);
      if (Math.min(box.w, box.h) < 0.05) { Object.assign(src, keep); Object.assign(box, kb); return; }
      rsdLive();
    };
    h.end = rsdCommit;
  });
  /* les angles de l'encart : le coin opposé reste ; l'encart garde les proportions de la source, sa taille suit le déplacement projeté sur la diagonale ; il reste dans l'image */
  RSD_CORNERS.forEach(k => {
    const sx = k[0], sy = k[1];
    const h = rsdMk('v corner', v => rsdAtN(v, box.x + (sx > 0 ? box.w : 0), box.y + (sy > 0 ? box.h : 0)), {});
    rsdCornerZ(h, v => Math.min(box.w * v.w, box.h * v.h));
    let B = null;
    h.start = () => { B = { v: rsdView(), b: Object.assign({}, box), r: src.h / src.w }; };
    h.move = d => {
      const b0 = B.b, r = B.r, MIN = 0.05, V = B.v;
      const Fx = sx > 0 ? b0.x : b0.x + b0.w, Fy = sy > 0 ? b0.y : b0.y + b0.h;       /* le coin opposé, en fractions */
      const dx = sx * b0.w * V.w, dy = sy * b0.h * V.h, len = Math.hypot(dx, dy) || 1;     /* la diagonale, en pixels */
      const t = (d.x * dx + d.y * dy) / len;                                              /* le déplacement projeté sur elle */
      const req = b0.w * (len + t) / len;
      const max = Math.min(sx > 0 ? 1 - Fx : Fx, (sy > 0 ? 1 - Fy : Fy) / r), min = Math.max(MIN, MIN / r);
      const w = Math.min(max, Math.max(min, req));
      box.w = w; box.h = w * r; box.x = sx > 0 ? Fx : Fx - w; box.y = sy > 0 ? Fy : Fy - box.h;
      rsdLive();
    };
    h.end = rsdCommit;
  });
  rsdMk('mv src', v => rsdAtN(v, src.x + src.w / 2, src.y + src.h / 2), rsdMoveCb([[src, 'x', 'y']], b => [b[0].x, b[0].y, b[0].x + src.w, b[0].y + src.h]));
  rsdMk('mv', v => rsdAtN(v, box.x + box.w / 2, box.y + box.h / 2), rsdMoveCb([[box, 'x', 'y']], b => [b[0].x, b[0].y, b[0].x + box.w, b[0].y + box.h]));
}

function rsdHandlesFor(a) {
  if (a.type === 'rect') rsdRectHandles(a);
  else if (a.type === 'ellipse') rsdEllipseHandles(a);
  else if (a.type === 'poly') rsdPolyHandles(a);
  else if (a.type === 'arrow' || a.type === 'bracket') rsdSegHandles(a);
  else if (a.type === 'label') rsdMk('mv', v => rsdAtN(v, a.x, a.y), rsdMoveCb([[a, 'x', 'y']]));
  else if (a.type === 'inset') rsdInsetHandles(a);
}

/* Refaire les poignées de ce qu'on édite : le tracé en cours, ou l'objet choisi ; keep : la poignée en cours de glisser, qui devient le point keepIdx */
function rsdBuildHandles(keep, keepIdx) {
  RSD.hs.forEach(h => { if (h !== keep) h.el.remove(); });
  RSD.hs = keep ? [keep] : [];
  if (SOURCE_READY) {
    const b = RSD.build;
    if (b) {
      b.pts.forEach((p, k) => {
        const first = b.kind === 'poly' && k === 0 && b.pts.length >= 3;
        const h = rsdMk('v' + (first ? ' first' : ''), v => rsdAtN(v, p.x, p.y), rsdMoveCb([[p, 'x', 'y']], null, true));
        if (first) h.tap = () => rsdClosePoly();
      });
    } else {
      const a = rsdSel();
      if (a) {
        if (a.type === 'poly') rsdPolyHandles(a, keep, keepIdx); else rsdHandlesFor(a);
      }
    }
  }
  RSD.sig = rsdSig();
  rsdPlace();
}
function rsdSig() {
  if (RSD.build) return 'b/' + RSD.build.kind + '/' + RSD.build.pts.length;
  const a = rsdSel();
  if (!a) return '';
  return a.type + '/' + a.id + (a.type === 'poly' ? '/' + a.pts.length + '/' + (a.closed ? 1 : 0) + '/' + RSD.vtx : '');
}

/* Pendant un glisser : l'objet, le contour et les poignées suivent (une fois par image) ; rien ne s'enregistre */
function rsdLive() {
  if (RSD.raf) return;
  RSD.raf = requestAnimationFrame(() => { RSD.raf = 0; rsdLiveNow(); });
}
function rsdLiveNow() {
  if (RSD.raf) { cancelAnimationFrame(RSD.raf); RSD.raf = 0; }
  rsdPlace();
  rsdUpdateDesc();
  if (!RSD.build) renderPreview();
}
/* La fin d'un glisser : la seule écriture de recon_state_v1 */
function rsdCommit() {
  RSD.busy = false;
  if (RSD.raf) { cancelAnimationFrame(RSD.raf); RSD.raf = 0; }
  saveState();
  rsdEditors();
  renderPreview();
  if (RSD.sig !== rsdSig()) rsdBuildHandles(); else rsdPlace();
  rsdUpdateDesc();
  if (RSD.sheet) rsdRenderSheet(true);
}
/* La fin d'un glisser sur le tracé en cours : rien ne s'enregistre */
function rsdBuildEnd() {
  RSD.busy = false;
  if (RSD.raf) { cancelAnimationFrame(RSD.raf); RSD.raf = 0; }
  rsdPlace();
}
/* Un changement discret (insertion d'un point, retrait, réglage) : écrire, redessiner, refaire les poignées */
function rsdChanged() {
  saveState();
  rsdEditors();
  schedulePreview();
  rsdBuildHandles();
  rsdSyncUi();
}
function rsdEditors() { renderShapesEditor(); renderLabelEditor(); renderInsetEditor(); }

/* L'aperçu vient d'être redessiné : l'objet choisi existe-t-il encore, ses poignées sont-elles les bonnes ? */
function rsdRefresh() {
  if (RSD.sel && !rsdSel()) { RSD.sel = null; RSD.vtx = -1; RSD.sheet = false; rsdBuildHandles(); rsdSyncUi(); return; }
  if (!RSD.busy && RSD.sig !== rsdSig()) { rsdBuildHandles(); rsdSyncUi(); return; }
  rsdPlace();
}

/* ---------- la barre, le message, la fiche ---------- */
function rsdColorName(c) { return t('rsd.c.' + c); }
function rsdDesc(a) {
  if (a.type === 'poly') return rsdSub(t(a.pts.length === 1 ? 'rsd.n.1' : 'rsd.n.n'), { n: a.pts.length }) + (a.closed ? ' · ' + t('rsd.sh.closed') : '');
  if (a.type === 'label') return a.text || '';
  if (a.type === 'inset') return a.label || t('rsd.g.inset');
  return rsdColorName(rsdColorOf(a));
}
function rsdUpdateDesc() {
  const a = rsdSel(), el = document.querySelector('#rsd-bar .dr-sel span');
  if (a && el) el.textContent = rsdDesc(a);
}
function rsdToolBtn(attrs, icon, label, cls) {
  return '<button type="button" class="dr-tool' + (cls ? ' ' + cls : '') + '" ' + attrs + ' title="' + rsdEsc(label) + '" aria-label="' + rsdEsc(label) + '">' +
    RSD_ICONS[icon] + '<i>' + rsdEsc(label) + '</i></button>';
}
function rsdRenderBar() {
  const bar = rsd$('rsd-bar'), a = rsdSel();
  bar.className = 'dr-bar' + (a ? ' selmode' : '');
  bar.setAttribute('aria-label', t('rsd.bar.aria'));
  let h = '';
  if (!a) {
    h += '<div class="dr-tools" role="group">' + RSD_TOOLS.map(k =>
      rsdToolBtn('data-dr="tool" data-tool="' + k + '" aria-pressed="' + (RSD.tool === k ? 'true' : 'false') + '"', k, t('rsd.tool.' + k), RSD.tool === k ? 'on' : '')).join('') + '</div>';
  } else {
    h += '<div class="dr-sel"><small>' + rsdEsc(t('rsd.g.' + a.type) + (RSD.vtx >= 0 ? ' · ' + rsdSub(t('rsd.vtx.n'), { n: RSD.vtx + 1 }) : '')) + '</small><span>' + rsdEsc(rsdDesc(a)) + '</span></div>';
    h += '<div class="dr-tools" role="group">' +
      (RSD.vtx >= 0 ? rsdToolBtn('data-dr="vtx"', 'vtx', t('rsd.b.vtx')) : '') +
      rsdToolBtn('data-dr="props" aria-pressed="' + (RSD.sheet ? 'true' : 'false') + '"', 'props', t('rsd.b.props'), RSD.sheet ? 'on' : '') +
      rsdToolBtn('data-dr="dup"', 'dup', t('rsd.b.copy')) +
      rsdToolBtn('data-dr="del"', 'del', t('rsd.b.del'), 'danger') +
      rsdToolBtn('data-dr="ok"', 'ok', t('rsd.b.ok')) + '</div>';
  }
  bar.innerHTML = h;
}
function rsdRenderHint() {
  const hint = rsd$('rsd-hint'), msg = rsd$('rsd-msg'), acts = rsd$('rsd-acts');
  if (rsdSel()) { hint.hidden = true; return; }
  hint.hidden = false;
  const tool = RSD.tool, b = RSD.build;
  let m = '', a = '';
  if (tool === 'select') m = rsdEsc(t('rsd.msg.select'));
  else if (tool === 'poly') {
    const n = b ? b.pts.length : 0;
    if (!n) m = rsdEsc(t('rsd.msg.poly'));
    else m = '<b>' + rsdEsc(rsdSub(t(n === 1 ? 'rsd.n.1' : 'rsd.n.n'), { n: n })) + '</b> ' + rsdEsc(t('rsd.build.add')) + (n >= 3 ? rsdEsc(t('rsd.build.close')) : '');
    a += '<button type="button" class="tb-btn" data-dr="undo" title="' + rsdEsc(t('rsd.undo')) + '" aria-label="' + rsdEsc(t('rsd.undo')) + '">↶</button>' +
      '<button type="button" class="tb-btn go" data-dr="finish">' + rsdEsc(t('rsd.finish')) + '</button>';
  } else m = rsdEsc(t('rsd.msg.' + tool + ((tool === 'arrow' || tool === 'bracket') && b && b.pts.length ? '2' : '')));
  if (tool !== 'select') {
    /* les réglages de l'objet à venir : le bouton avant ↶ / Terminer / ✕ */
    a = '<button type="button" class="tb-btn mq-props' + (RSD.sheet ? ' on' : '') + '" data-dr="props" aria-pressed="' + (RSD.sheet ? 'true' : 'false') + '" title="' + rsdEsc(t('rsd.b.props')) +
      '" aria-label="' + rsdEsc(t('rsd.b.props')) + '">' + RSD_ICONS.props + '</button>' + a;
    a += '<button type="button" class="tb-btn" data-dr="cancel" title="' + rsdEsc(t('rsd.cancel')) + '" aria-label="' + rsdEsc(t('rsd.cancel')) + '">✕</button>';
  }
  msg.innerHTML = m;
  acts.innerHTML = a;
  acts.hidden = !a;
}

/* ----- la fiche « Réglages » : celle de l'objet choisi, ou (draft) celle de l'objet à venir, aux mêmes champs ----- */
function rsdSheetHtml(a, draft) {
  const g = a.type;
  const f = (label, id, body) => '<div class="dr-f"><label' + (id ? ' for="' + id + '"' : '') + '>' + rsdEsc(label) + '</label>' + body + '</div>';
  const seg = (field, items) => '<div class="dr-seg" role="group">' + items.map(x =>
    '<button type="button" class="tb-btn' + (x.on ? ' on' : '') + '" data-f="' + field + '" data-v="' + x.v + '" aria-pressed="' + (x.on ? 'true' : 'false') + '">' + rsdEsc(x.label) + '</button>').join('') + '</div>';
  const col = rsdColorOf(a);
  const sw = '<div class="dr-sw rsd-sw" role="group">' + (g === 'inset' ? ['white', 'black', 'red'] : ['red', 'black', 'white']).map(c =>
    '<button type="button" data-f="color" data-v="' + c + '" style="background:' + RSD_COLORS[c] + '" aria-pressed="' + (col === c ? 'true' : 'false') + '"' + (col === c ? ' class="on"' : '') + '><span>' + rsdEsc(rsdColorName(c)) + '</span></button>').join('') + '</div>';
  let h = '<div class="sh-head"><b>' + rsdEsc(rsdSub(t(draft ? 'rsd.sheet.draft' : 'rsd.sheet'), { g: t('rsd.g.' + g) })) + '</b><button type="button" class="sh-x" data-dr="props" title="' + rsdEsc(t('rsd.f.close')) +
    '" aria-label="' + rsdEsc(t('rsd.f.close')) + '">×</button></div>';
  if (g === 'label') {
    h += f(t('rsd.f.text'), 'rsd-f-text', '<input type="text" id="rsd-f-text" data-f="text" autocomplete="off" spellcheck="false" value="' + rsdEsc(a.text) + '">');
    h += f(t('rsd.f.color'), '', sw);
    h += f(t('rsd.f.style'), '', seg('style', ['stamp', 'cursive', 'plain'].map(s => ({ v: s, on: a.style === s, label: t('rsd.st.' + s) }))));
  } else if (g === 'poly') {
    h += f(t('rsd.f.color'), '', sw);
    h += f(t('rsd.f.shape'), '', seg('closed', [{ v: '0', on: a.closed !== true, label: t('rsd.sh.open') }, { v: '1', on: a.closed === true, label: t('rsd.sh.closed') }]));
  } else if (g === 'inset') {
    h += f(t('rsd.f.caption'), 'rsd-f-caption', '<input type="text" id="rsd-f-caption" data-f="legend" autocomplete="off" spellcheck="false" placeholder="' + rsdEsc(t('rsd.f.caption.ph')) + '" value="' + rsdEsc(a.label || '') + '">');
    h += f(t('rsd.f.color'), '', sw);
  } else h += f(t('rsd.f.color'), '', sw);
  return h;
}
/* La fiche s'ouvre sur l'objet choisi (outil Choisir), ou, avec un outil de création, sur le brouillon de l'objet à venir : { a, draft } ou null */
function rsdSheetTarget() {
  const a = rsdSel();
  if (RSD.tool === 'select') return a ? { a: a, draft: false } : null;
  return RSD.draft ? { a: RSD.draft.it, draft: true } : null;
}
/* La fiche « à venir » se pose d'après le message, mesuré : son bas à 6 px au-dessus du message, sa hauteur bornée à la place qui reste (aperçu + 10 px),
   160 px au moins (elle couvre alors le haut de l'aperçu, jamais le message). La fiche d'un objet choisi garde sa place de feuille du bas. */
function rsdPlaceSheet() {
  const sh = rsd$('rsd-sheet'), hint = rsd$('rsd-hint'), pv = rsd$('preview-panel');
  if (!sh || !hint) return;
  if (sh.hidden || !sh.classList.contains('mq-draft') || hint.hidden) { sh.style.bottom = ''; sh.style.maxHeight = ''; return; }
  const fixed = getComputedStyle(sh).position === 'fixed';
  const p = pv.getBoundingClientRect(), h = hint.getBoundingClientRect();
  const top = p.top + (fixed ? 0 : pv.clientTop), bottom = fixed ? document.documentElement.clientHeight : top + pv.clientHeight, base = h.top - RSD_SHEET_GAP;
  sh.style.bottom = Math.round(bottom - base) + 'px';
  sh.style.maxHeight = Math.max(RSD_SHEET_MIN, Math.floor(base - (top + RSD_SHEET_TOP))) + 'px';
}
/* La bande du bas : l'image ne passe jamais sous la barre ni sous le message.
   Hauteur = marge basse de la barre + barre + 6 px + message (44 px, son minimum) + 8 px, mesurée sur la barre affichée ;
   elle ne dépend pas de la présence du message (l'image ne saute pas). Sans image, rien n'est réservé. */
const RSD_BAND_GAP = 6, RSD_BAND_MSG = 44, RSD_BAND_AIR = 8;
function rsdBand() {
  const pv = rsd$('preview-panel'), ui = rsd$('rsd-ui'), bar = rsd$('rsd-bar'), inner = pv && pv.querySelector('.preview-inner');
  if (!pv || !inner || !ui || !bar) return;
  let px = '';
  if (SOURCE_READY && !ui.hidden && ui.getClientRects().length && bar.getClientRects().length) {
    const ir = inner.getBoundingClientRect(), br = bar.getBoundingClientRect();
    const band = Math.ceil(ir.bottom - (br.top - RSD_BAND_GAP - RSD_BAND_MSG - RSD_BAND_AIR));
    if (band > 0) px = band + 'px';
  }
  if (pv.style.getPropertyValue('--rsd-band') !== px) {
    if (px) pv.style.setProperty('--rsd-band', px); else pv.style.removeProperty('--rsd-band');
  }
}
function rsdRenderSheet(force) {
  const sh = rsd$('rsd-sheet'), tg = rsdSheetTarget();
  if (!RSD.sheet || !tg || !SOURCE_READY) { sh.hidden = true; sh.classList.remove('mq-draft'); RSD.sheetKey = ''; rsdPlaceSheet(); return; }
  const key = (tg.draft ? 'draft/' + RSD.draft.n : RSD.sel) + '/' + CURRENT_LANG;
  sh.hidden = false;
  sh.classList.toggle('mq-draft', tg.draft);
  if (key !== RSD.sheetKey || force) {
    if (tg.draft && tg.a.type === 'label' && !('text' in RSD.draft.vals)) tg.a.text = t('rsd.new.text');
    RSD.sheetKey = key;
    sh.innerHTML = rsdSheetHtml(tg.a, tg.draft);
  }
  rsdPlaceSheet();
}

/* Tout ce que montre le mode, remis d'aplomb */
/* Le toast commun (messages_block.py) se pose à 12 px au-dessus de la plus haute des deux commandes du bas, le message de dessin ou la barre de dessin :
   il ne recouvre jamais une commande. Sans l'une ni l'autre (pas d'image), la variable est ôtée et le toast reste à 20 px du bas. */
const RSD_TOAST_GAP = 12;
function rsdToastPlace() {
  const root = document.documentElement;
  const tops = ['rsd-hint', 'rsd-bar'].map(rsd$).filter(el => el && el.getClientRects().length).map(el => el.getBoundingClientRect().top);
  if (!tops.length) { root.style.removeProperty('--mp-toast-bottom'); return; }
  const px = Math.round(root.clientHeight - Math.min.apply(null, tops) + RSD_TOAST_GAP) + 'px';
  if (root.style.getPropertyValue('--mp-toast-bottom') !== px) root.style.setProperty('--mp-toast-bottom', px);
}
function rsdSyncUi() {
  const ui = rsd$('rsd-ui');
  if (!ui) return;
  ui.hidden = !SOURCE_READY;
  if (!SOURCE_READY) { rsd$('rsd-sheet').hidden = true; rsdToastPlace(); return; }
  const a = rsdSel();
  if (RSD.sel && !a) { RSD.sel = null; RSD.vtx = -1; RSD.sheet = false; }
  if (RSD.sheet && !rsdSheetTarget()) RSD.sheet = false;
  if (RSD.vtx >= 0 && (!a || a.type !== 'poly' || RSD.vtx >= a.pts.length)) RSD.vtx = -1;
  rsdRenderBar();
  rsdRenderHint();
  rsdRenderSheet(false);
  rsdBand();
  rsdPlaceSheet();
  rsdToastPlace();
}

/* ---------- le choix, la création ---------- */
function rsdSelect(id) {
  RSD.sel = id; RSD.vtx = -1;
  rsdBuildHandles();
  rsdSyncUi();
}
function rsdDeselect() {
  RSD.sel = null; RSD.vtx = -1; RSD.sheet = false;
  rsdBuildHandles();
  rsdSyncUi();
}
/* Abandonner la création en cours, ou quitter un outil de pose : retour à Choisir, rien n'est écrit */
function rsdCancel() {
  RSD.build = null; RSD.tool = 'select'; RSD.draft = null; RSD.sheet = false;
  rsdBuildHandles();
  rsdSyncUi();
}
function rsdSetTool(x) {
  if (RSD_TOOLS.indexOf(x) === -1 || x === RSD.tool) return;
  const sheet = RSD.sheet;
  if (RSD.build) {
    if (rsdFinish(true)) { RSD.sel = null; RSD.vtx = -1; RSD.sheet = false; }     /* assez de points : le tracé se termine, rien n'est choisi */
    RSD.build = null;
  }
  RSD.tool = x;
  RSD.draft = x === 'select' ? null : rsdNewDraft(x);
  RSD.sheet = x === 'select' ? false : sheet;                                      /* changer d'outil, fiche ouverte : elle se rouvre sur le brouillon du nouvel outil */
  RSD.sheetKey = '';
  RSD.build = (x === 'poly' || x === 'arrow' || x === 'bracket') ? { kind: x, pts: [] } : null;
  rsdBuildHandles();
  rsdSyncUi();
}

/* Le brouillon des réglages de l'objet à venir : la géométrie vient des touchers, les réglages de la fiche */
function rsdNewDraft(tool) {
  const c = tool === 'inset' ? 'white' : RSD.color;
  let it;
  if (tool === 'rect') it = { type: 'rect', x: 0, y: 0, w: 0.18, h: 0.12, angle: 0, color: c };
  else if (tool === 'ellipse') it = { type: 'ellipse', cx: 0, cy: 0, rx: 0.08, ry: 0.05, color: c };
  else if (tool === 'poly') it = { type: 'poly', pts: [], closed: false, color: c };
  else if (tool === 'arrow') it = { type: 'arrow', x1: 0, y1: 0, x2: 0, y2: 0, color: c };
  else if (tool === 'bracket') it = { type: 'bracket', x1: 0, y1: 0, x2: 0, y2: 0, depth: 0.04, color: c };
  else if (tool === 'label') it = { type: 'label', x: 0, y: 0, text: t('rsd.new.text'), style: 'stamp', color: c };
  else it = { type: 'inset', src: { x: 0, y: 0, w: 0.12, h: 0.12 }, box: { x: 0, y: 0, w: 0.22, h: 0.22 }, color: 'white', label: '' };
  return { n: ++RSD.draftN, tool: tool, it: it, vals: {} };
}
/* Un réglage posé sur un objet (le choisi, un neuf, ou le brouillon) ; false s'il ne le concerne pas ou s'il est illisible */
function rsdSetField(a, f, v) {
  const ty = a.type;
  if (f === 'color') { if (!RSD_COLORS[v]) return false; a.color = v; RSD.color = v; }
  else if (f === 'text') { if (ty !== 'label') return false; a.text = v; }
  else if (f === 'style') { if (ty !== 'label' || ['stamp', 'cursive', 'plain'].indexOf(v) === -1) return false; a.style = v; }
  else if (f === 'closed') { if (ty !== 'poly') return false; a.closed = v === '1'; }
  else if (f === 'legend') { if (ty !== 'inset') return false; a.label = v; }
  else return false;
  return true;
}
/* Un réglage de la fiche : sur un objet il s'applique et s'enregistre aussitôt ; sur le brouillon il se retient (rien ne s'enregistre) */
function rsdApply(tg, f, v) {
  if (!rsdSetField(tg.a, f, v)) return;
  if (tg.draft) { RSD.draft.vals[f] = v; rsdPreviewDraw(); rsdRenderBar(); return; }
  saveState();
  rsdEditors();
  schedulePreview();
  if (f === 'closed') rsdBuildHandles(); else rsdPlace();
  rsdRenderBar();
}
/* À la création : seuls les réglages changés dans la fiche « à venir » passent à l'objet */
function rsdApplyDraft(a, skip) {
  const d = RSD.draft;
  if (!d) return;
  Object.keys(d.vals).forEach(f => { if (!skip || skip.indexOf(f) === -1) rsdSetField(a, f, d.vals[f]); });
}
function rsdAdd(a, skip) {
  rsdApplyDraft(a, skip);
  STATE.annotations = STATE.annotations || [];
  STATE.annotations.push(a);
  RSD.tool = 'select'; RSD.build = null; RSD.draft = null;       /* la fiche, si elle est ouverte, reste ouverte sur l'objet créé */
  RSD.sel = a.id; RSD.vtx = -1;
  saveState();
  rsdEditors();
  schedulePreview();
  rsdBuildHandles();
  rsdSyncUi();
}
function rsdFinish(quiet) {
  const b = RSD.build;
  if (!b || b.kind !== 'poly') return false;
  if (b.pts.length < 2) { if (!quiet) showToast(t('rsd.t.min'), { type: 'err' }); return false; }
  rsdAdd({ id: uid(), type: 'poly', pts: b.pts.map(p => ({ x: p.x, y: p.y })), closed: false, color: RSD.color });
  return true;
}
function rsdClosePoly() {
  const b = RSD.build;
  if (!b || b.kind !== 'poly' || b.pts.length < 3) return;
  rsdAdd({ id: uid(), type: 'poly', pts: b.pts.map(p => ({ x: p.x, y: p.y })), closed: true, color: RSD.color }, ['closed']);
}

/* Un toucher sur l'image avec un outil de création : n = le point, en fractions de l'image */
function rsdCreate(tool, n) {
  const c = RSD.color;
  if (tool === 'rect') {
    rsdAdd({ id: uid(), type: 'rect', x: rsdCl(n.x - 0.09, 0, 1 - 0.18), y: rsdCl(n.y - 0.06, 0, 1 - 0.12), w: 0.18, h: 0.12, angle: 0, color: c });
  } else if (tool === 'ellipse') {
    rsdAdd({ id: uid(), type: 'ellipse', cx: rsdCl(n.x, 0.08, 1 - 0.08), cy: rsdCl(n.y, 0.05, 1 - 0.05), rx: 0.08, ry: 0.05, color: c });
  } else if (tool === 'label') {
    RSD.sheet = true;
    rsdAdd({ id: uid(), type: 'label', x: n.x, y: n.y, text: t('rsd.new.text'), style: 'stamp', color: c });
    const f = rsd$('rsd-f-text');
    if (f) { f.focus(); f.select(); }
  } else if (tool === 'inset') {
    const sw = 0.12, sh = 0.12, bw = 0.22, bh = bw * (sh / sw), m = 0.02;
    const bx = n.x < 0.5 ? 1 - m - bw : m, by = n.y < 0.5 ? 1 - m - bh : m;      /* l'encart : dans le coin opposé au toucher */
    rsdAdd({ id: uid(), type: 'inset', src: { x: rsdCl(n.x - sw / 2, 0, 1 - sw), y: rsdCl(n.y - sh / 2, 0, 1 - sh), w: sw, h: sh }, box: { x: bx, y: by, w: bw, h: bh }, color: 'white', label: '' });
  } else if (RSD.build) {
    const b = RSD.build;
    b.pts.push({ x: n.x, y: n.y });
    if (tool === 'arrow' && b.pts.length === 2) { rsdAdd({ id: uid(), type: 'arrow', x1: b.pts[0].x, y1: b.pts[0].y, x2: b.pts[1].x, y2: b.pts[1].y, color: c }); return; }
    if (tool === 'bracket' && b.pts.length === 2) { rsdAdd({ id: uid(), type: 'bracket', x1: b.pts[0].x, y1: b.pts[0].y, x2: b.pts[1].x, y2: b.pts[1].y, depth: 0.04, color: c }); return; }
    rsdBuildHandles();
    rsdSyncUi();
  }
}

/* ----- toucher : l'annotation la plus proche, la dernière dessinée à égalité ----- */
function rsdSegDist(p, a, b) {
  const dx = b.x - a.x, dy = b.y - a.y, l2 = dx * dx + dy * dy;
  let u = l2 ? ((p.x - a.x) * dx + (p.y - a.y) * dy) / l2 : 0;
  u = Math.max(0, Math.min(1, u));
  return Math.hypot(p.x - (a.x + u * dx), p.y - (a.y + u * dy));
}
function rsdInside(p, q) {
  let on = false;
  for (let i = 0, j = q.length - 1; i < q.length; j = i++) {
    if ((q[i].y > p.y) !== (q[j].y > p.y) && p.x < (q[j].x - q[i].x) * (p.y - q[i].y) / (q[j].y - q[i].y) + q[i].x) on = !on;
  }
  return on;
}
function rsdBoxDist(p, x, y, w, h, tol) {         /* un rectangle droit : la distance à son bord, ou -1 s'il n'est pas touché (dedans, ou à tol près) */
  const ax = Math.max(x - p.x, p.x - (x + w)), ay = Math.max(y - p.y, p.y - (y + h));
  if (ax > 0 || ay > 0) { const d = Math.hypot(Math.max(ax, 0), Math.max(ay, 0)); return d <= tol ? d : -1; }
  return -Math.max(ax, ay);
}
/* La distance (px) de p (pixels du canevas) à l'annotation si elle est touchée, sinon -1 */
function rsdHit(a, p, v) {
  if (a.type === 'rect') {
    const g = rsdRectG(a, v), dx = p.x - g.cx, dy = p.y - g.cy;
    const lx = dx * g.ux + dy * g.uy, ly = dx * g.vx + dy * g.vy;
    const ax = Math.abs(lx) - g.hw, ay = Math.abs(ly) - g.hh;
    if (ax > 0 || ay > 0) { const d = Math.hypot(Math.max(ax, 0), Math.max(ay, 0)); return d <= RSD_HIT.path ? d : -1; }
    return -Math.max(ax, ay);
  }
  if (a.type === 'ellipse') {
    const rx = a.rx * v.w || 0.01, ry = a.ry * v.h || 0.01;
    const q = Math.pow((p.x - a.cx * v.w) / rx, 2) + Math.pow((p.y - a.cy * v.h) / ry, 2);
    return q <= RSD_HIT.ellipseQ ? Math.abs(Math.sqrt(q) - 1) * Math.min(rx, ry) : -1;
  }
  if (a.type === 'poly') {
    const q = (a.pts || []).map(x => ({ x: x.x * v.w, y: x.y * v.h })), n = q.length;
    if (!n) return -1;
    let d = Infinity;
    for (let i = 0; i + 1 < n; i++) d = Math.min(d, rsdSegDist(p, q[i], q[i + 1]));
    if (a.closed && n > 2) d = Math.min(d, rsdSegDist(p, q[n - 1], q[0]));
    if (n === 1) d = Math.hypot(p.x - q[0].x, p.y - q[0].y);
    return (d <= RSD_HIT.path || (a.closed && n > 2 && rsdInside(p, q))) ? d : -1;
  }
  if (a.type === 'arrow' || a.type === 'bracket') {
    const d = rsdSegDist(p, { x: a.x1 * v.w, y: a.y1 * v.h }, { x: a.x2 * v.w, y: a.y2 * v.h });
    return d <= RSD_HIT.path ? d : -1;
  }
  if (a.type === 'label') {
    const d = Math.hypot(p.x - a.x * v.w, p.y - a.y * v.h);
    return d <= RSD_HIT.label ? d : -1;
  }
  if (a.type === 'inset') {
    const d1 = rsdBoxDist(p, a.src.x * v.w, a.src.y * v.h, a.src.w * v.w, a.src.h * v.h, RSD_HIT.inset);
    const d2 = rsdBoxDist(p, a.box.x * v.w, a.box.y * v.h, a.box.w * v.w, a.box.h * v.h, RSD_HIT.inset);
    if (d1 < 0) return d2;
    return d2 < 0 ? d1 : Math.min(d1, d2);
  }
  return -1;
}
function rsdPickAt(p, v) {
  let best = null, bd = Infinity;
  (STATE.annotations || []).forEach(a => {
    if (RSD_TYPES.indexOf(a.type) === -1) return;
    const d = rsdHit(a, p, v);
    if (d >= 0 && d <= bd) { best = a; bd = d; }                   /* à égalité, le dernier */
  });
  if (best) rsdSelect(best.id); else rsdDeselect();
}

/* ----- les actions de la barre ----- */
function rsdCopy() {
  const a = rsdSel(), v = rsdView();
  if (!a || !v.ok) return;
  const dx = RSD_COPY_PX / v.w, dy = RSD_COPY_PX / v.h;
  const c = JSON.parse(JSON.stringify(a));
  c.id = uid();
  /* l'étendue de ce qui bouge, en fractions : 24 px à droite et en bas ; sans place de ce côté, de l'autre */
  let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
  const ext = (x, y, w, h) => { x0 = Math.min(x0, x); y0 = Math.min(y0, y); x1 = Math.max(x1, x + (w || 0)); y1 = Math.max(y1, y + (h || 0)); };
  if (c.type === 'rect') ext(c.x, c.y, c.w, c.h);
  else if (c.type === 'ellipse') ext(c.cx - c.rx, c.cy - c.ry, 2 * c.rx, 2 * c.ry);
  else if (c.type === 'poly') c.pts.forEach(p => ext(p.x, p.y));
  else if (c.type === 'arrow' || c.type === 'bracket') { ext(c.x1, c.y1); ext(c.x2, c.y2); }
  else if (c.type === 'label') ext(c.x, c.y);
  else if (c.type === 'inset') { ext(c.src.x, c.src.y, c.src.w, c.src.h); ext(c.box.x, c.box.y, c.box.w, c.box.h); }
  const sx = x1 + dx <= 1 ? dx : (x0 - dx >= 0 ? -dx : 0), sy = y1 + dy <= 1 ? dy : (y0 - dy >= 0 ? -dy : 0);
  if (c.type === 'rect') { c.x += sx; c.y += sy; }
  else if (c.type === 'ellipse') { c.cx += sx; c.cy += sy; }
  else if (c.type === 'poly') c.pts.forEach(p => { p.x += sx; p.y += sy; });
  else if (c.type === 'arrow' || c.type === 'bracket') { c.x1 += sx; c.y1 += sy; c.x2 += sx; c.y2 += sy; }
  else if (c.type === 'label') { c.x += sx; c.y += sy; }
  else if (c.type === 'inset') { c.src.x += sx; c.src.y += sy; c.box.x += sx; c.box.y += sy; }
  STATE.annotations.push(c);
  RSD.sel = c.id; RSD.vtx = -1;
  saveState();
  rsdEditors();
  schedulePreview();
  rsdBuildHandles();
  rsdSyncUi();
}
function rsdDelete() {
  const a = rsdSel();
  if (!a) return;
  STATE.annotations = STATE.annotations.filter(x => x !== a);
  saveState();
  rsdEditors();
  schedulePreview();
  rsdDeselect();
}
/* « Point » : retire le point choisi, sauf sous deux points */
function rsdRemoveVertex() {
  const a = rsdSel();
  if (!a || a.type !== 'poly' || RSD.vtx < 0) return;
  if (a.pts.length <= 2) { showToast(t('rsd.t.min'), { type: 'err' }); return; }
  a.pts.splice(RSD.vtx, 1);
  RSD.vtx = -1;
  rsdChanged();
}

function rsdOnClick(ev) {
  const b = ev.target.closest ? ev.target.closest('[data-dr]') : null;
  if (!b) return;
  const a = b.dataset.dr;
  if (a === 'tool') rsdSetTool(b.dataset.tool);
  else if (a === 'undo') { if (RSD.build) { RSD.build.pts.pop(); rsdBuildHandles(); rsdSyncUi(); } }
  else if (a === 'finish') rsdFinish(false);
  else if (a === 'cancel') rsdCancel();
  else if (a === 'vtx') rsdRemoveVertex();
  else if (a === 'props') { if (rsdSheetTarget()) { RSD.sheet = !RSD.sheet; RSD.sheetKey = ''; rsdSyncUi(); } }
  else if (a === 'dup') rsdCopy();
  else if (a === 'del') rsdDelete();
  else if (a === 'ok') rsdDeselect();
}
function rsdOnSheet(ev) {
  const tg = rsdSheetTarget();
  if (!tg) return;
  if (ev.type === 'click') {
    const b = ev.target.closest ? ev.target.closest('button[data-f]') : null;
    if (!b) return;
    rsdApply(tg, b.dataset.f, b.dataset.v);
    rsdRenderSheet(true);
  } else if (ev.type === 'input') {
    const el = ev.target;
    if (!el || !el.dataset || !el.dataset.f) return;
    rsdApply(tg, el.dataset.f, el.value);
  }
}

/* ---------- l'image : un toucher crée ou choisit ; un repère numéroté ou une cible se glisse directement ---------- */
const RSD_SLOP = 0.04;
function rsdHitMarker(p) {            /* p en fractions : une cible, puis un repère (comme à la base) */
  for (let i = 0; i < STATE.cartouche.length; i++) {
    const e = STATE.cartouche[i];
    if (e.point && e.target && Math.hypot(e.target.x - p.x, e.target.y - p.y) < RSD_SLOP) return { type: 'target', idx: i };
  }
  for (let i = 0; i < STATE.cartouche.length; i++) {
    const e = STATE.cartouche[i];
    if (e.point && Math.hypot(e.x - p.x, e.y - p.y) < RSD_SLOP) return { type: 'marker', idx: i };
  }
  return null;
}
function rsdInitCanvas() {
  const cv = rsd$('preview-canvas');
  cv.style.touchAction = 'none';
  let st = null;
  const norm = ev => { const v = rsdView(); return { v: v, x: (ev.clientX - v.cl) / v.w, y: (ev.clientY - v.ct) / v.h }; };
  cv.addEventListener('pointerdown', ev => {
    if (ev.pointerType === 'mouse' && ev.button !== 0) return;
    const n = norm(ev);
    st = { id: ev.pointerId, x0: ev.clientX, y0: ev.clientY, moved: false, far: false, hit: RSD.tool === 'select' ? rsdHitMarker(n) : null };
    try { cv.setPointerCapture(ev.pointerId); } catch (x) { /* ignore */ }
  });
  cv.addEventListener('pointermove', ev => {
    if (!st || ev.pointerId !== st.id) return;
    const dist = Math.hypot(ev.clientX - st.x0, ev.clientY - st.y0);
    if (dist > RSD_TAP_TOL) st.far = true;
    if (!st.hit) return;
    if (!st.moved) { if (dist < RSD_MOVE_TOL) return; st.moved = true; }
    ev.preventDefault();
    const p = norm(ev), e = STATE.cartouche[st.hit.idx];
    if (!e) return;
    const q = { x: rsdCl(p.x, 0, 1), y: rsdCl(p.y, 0, 1) };
    if (st.hit.type === 'marker') { e.x = q.x; e.y = q.y; }
    else if (e.target) { e.target.x = q.x; e.target.y = q.y; }
    rsdLive();
  });
  const up = ev => {
    if (!st || ev.pointerId !== st.id) return;
    const was = st;
    st = null;
    try { cv.releasePointerCapture(ev.pointerId); } catch (x) { /* ignore */ }
    if (was.moved) { saveState(); renderPreview(); return; }             /* un repère ou une cible glissé : une seule écriture, à la fin */
    if (ev.type !== 'pointerup' || was.far) return;
    const n = norm(ev);
    if (!n.v.ok) return;
    if (RSD.tool === 'select') rsdPickAt({ x: ev.clientX - n.v.cl, y: ev.clientY - n.v.ct }, n.v);
    else rsdCreate(RSD.tool, { x: rsdCl(n.x, 0, 1), y: rsdCl(n.y, 0, 1) });
  };
  cv.addEventListener('pointerup', up);
  cv.addEventListener('pointercancel', up);
}

function rsdInit() {
  const ui = rsd$('rsd-ui'), sh = rsd$('rsd-sheet');
  ui.addEventListener('click', rsdOnClick);
  sh.addEventListener('click', ev => { if (ev.target.closest && ev.target.closest('[data-dr]')) rsdOnClick(ev); else rsdOnSheet(ev); });
  sh.addEventListener('input', rsdOnSheet);
  rsdInitCanvas();
  document.addEventListener('keydown', ev => {
    if (ev.key !== 'Escape' || !SOURCE_READY || (typeof TBM !== 'undefined' && TBM.cur)) return;
    if (RSD.build || RSD.tool !== 'select') rsdCancel();
    else if (RSD.sheet && rsdSel()) { RSD.sheet = false; rsdSyncUi(); }
    else if (rsdSel()) rsdDeselect();
  });
  if (window.ResizeObserver) {
    RSD.ro = new ResizeObserver(() => { rsdBand(); rsdPlace(); rsdPlaceSheet(); rsdToastPlace(); });
    [rsd$('preview-panel'), rsd$('preview-canvas'), rsd$('rsd-hint'), rsd$('rsd-bar'), sh].forEach(el => RSD.ro.observe(el));
  }
  window.addEventListener('resize', () => { rsdBand(); rsdPlace(); rsdPlaceSheet(); rsdToastPlace(); });
  rsdSyncUi();
}
'''.replace('__RSD_ICONS__', json.dumps(RSD_ICONS, ensure_ascii=False))

RSD_I18N_FR = r'''    // Annoter au doigt (lot mp-rs-v1.1.0)
    'rsd.bar.aria': 'Annoter l\'image',
    'rsd.tool.select': 'Choisir',
    'rsd.tool.rect': 'Cadre',
    'rsd.tool.ellipse': 'Ellipse',
    'rsd.tool.poly': 'Tracé',
    'rsd.tool.arrow': 'Flèche',
    'rsd.tool.bracket': 'Crochet',
    'rsd.tool.label': 'Texte',
    'rsd.tool.inset': 'Loupe',
    'rsd.g.rect': 'Cadre',
    'rsd.g.ellipse': 'Ellipse',
    'rsd.g.poly': 'Tracé',
    'rsd.g.arrow': 'Flèche',
    'rsd.g.bracket': 'Crochet',
    'rsd.g.label': 'Texte',
    'rsd.g.inset': 'Loupe',
    'rsd.msg.select': 'Touchez une annotation pour la modifier.',
    'rsd.msg.rect': 'Touchez l\'image : le centre du cadre.',
    'rsd.msg.ellipse': 'Touchez l\'image : le centre de l\'ellipse.',
    'rsd.msg.poly': 'Touchez l\'image pour poser les points.',
    'rsd.msg.arrow': 'Touchez le départ de la flèche, puis sa pointe.',
    'rsd.msg.arrow2': 'Touchez la pointe.',
    'rsd.msg.bracket': 'Touchez une extrémité du crochet, puis l\'autre.',
    'rsd.msg.bracket2': 'Touchez l\'autre extrémité.',
    'rsd.msg.label': 'Touchez l\'image pour poser le texte.',
    'rsd.msg.inset': 'Touchez la zone à agrandir.',
    'rsd.n.1': '{n} point',
    'rsd.n.n': '{n} points',
    'rsd.build.add': '— touchez pour en ajouter',
    'rsd.build.close': ', ou le premier pour fermer',
    'rsd.finish': 'Terminer',
    'rsd.undo': 'Retirer le dernier point',
    'rsd.cancel': 'Abandonner',
    'rsd.b.vtx': 'Point',
    'rsd.b.props': 'Réglages',
    'rsd.b.copy': 'Copier',
    'rsd.b.del': 'Suppr.',
    'rsd.b.ok': 'OK',
    'rsd.vtx.n': 'point {n}',
    'rsd.sheet': '{g} · réglages',
    'rsd.sheet.draft': '{g} · réglages · à venir',
    'rsd.f.color': 'Couleur',
    'rsd.c.red': 'Rouge',
    'rsd.c.black': 'Noir',
    'rsd.c.white': 'Blanc',
    'rsd.f.text': 'Texte',
    'rsd.f.style': 'Style',
    'rsd.st.stamp': 'Tampon',
    'rsd.st.cursive': 'Manuscrit',
    'rsd.st.plain': 'Simple',
    'rsd.f.shape': 'Tracé',
    'rsd.sh.open': 'Ouvert',
    'rsd.sh.closed': 'Fermé',
    'rsd.f.caption': 'Légende',
    'rsd.f.caption.ph': 'Agrandissement',
    'rsd.f.close': 'Fermer',
    'rsd.new.text': 'CIBLE',
    'rsd.t.min': '⚠ Un tracé a au moins deux points.',
'''

RSD_I18N_EN = r'''    // Touch annotations (lot mp-rs-v1.1.0)
    'rsd.bar.aria': 'Annotate the image',
    'rsd.tool.select': 'Select',
    'rsd.tool.rect': 'Frame',
    'rsd.tool.ellipse': 'Ellipse',
    'rsd.tool.poly': 'Polyline',
    'rsd.tool.arrow': 'Arrow',
    'rsd.tool.bracket': 'Bracket',
    'rsd.tool.label': 'Text',
    'rsd.tool.inset': 'Loupe',
    'rsd.g.rect': 'Frame',
    'rsd.g.ellipse': 'Ellipse',
    'rsd.g.poly': 'Polyline',
    'rsd.g.arrow': 'Arrow',
    'rsd.g.bracket': 'Bracket',
    'rsd.g.label': 'Text',
    'rsd.g.inset': 'Loupe',
    'rsd.msg.select': 'Tap an annotation to edit it.',
    'rsd.msg.rect': 'Tap the image: the frame\'s centre.',
    'rsd.msg.ellipse': 'Tap the image: the ellipse\'s centre.',
    'rsd.msg.poly': 'Tap the image to place the points.',
    'rsd.msg.arrow': 'Tap the arrow\'s start, then its tip.',
    'rsd.msg.arrow2': 'Tap the tip.',
    'rsd.msg.bracket': 'Tap one end of the bracket, then the other.',
    'rsd.msg.bracket2': 'Tap the other end.',
    'rsd.msg.label': 'Tap the image to place the text.',
    'rsd.msg.inset': 'Tap the area to magnify.',
    'rsd.n.1': '{n} point',
    'rsd.n.n': '{n} points',
    'rsd.build.add': '— tap to add more',
    'rsd.build.close': ', or the first one to close',
    'rsd.finish': 'Finish',
    'rsd.undo': 'Remove the last point',
    'rsd.cancel': 'Cancel',
    'rsd.b.vtx': 'Point',
    'rsd.b.props': 'Settings',
    'rsd.b.copy': 'Copy',
    'rsd.b.del': 'Delete',
    'rsd.b.ok': 'OK',
    'rsd.vtx.n': 'point {n}',
    'rsd.sheet': '{g} · settings',
    'rsd.sheet.draft': '{g} · settings · upcoming',
    'rsd.f.color': 'Colour',
    'rsd.c.red': 'Red',
    'rsd.c.black': 'Black',
    'rsd.c.white': 'White',
    'rsd.f.text': 'Text',
    'rsd.f.style': 'Style',
    'rsd.st.stamp': 'Stamp',
    'rsd.st.cursive': 'Cursive',
    'rsd.st.plain': 'Plain',
    'rsd.f.shape': 'Shape',
    'rsd.sh.open': 'Open',
    'rsd.sh.closed': 'Closed',
    'rsd.f.caption': 'Caption',
    'rsd.f.caption.ph': 'Close-up',
    'rsd.f.close': 'Close',
    'rsd.new.text': 'TARGET',
    'rsd.t.min': '⚠ A polyline needs at least two points.',
'''

# ---------- HTML ----------
RS_MENU_CSS = r"""
/* ---------- le menu « Ouvrir » : le bouton de la barre et son panneau, au style des listes de la barre (tbm-*) ; même composant qu'au Datacard Generator ---------- */
#btn-open { position: relative; color: var(--amber); border-color: var(--amber-dark); padding-right: 12px; }
#btn-open:hover, #btn-open:focus-visible, #btn-open.dsp-open { border-color: var(--amber); }
#btn-open .dsp-chev { width: 10px; height: 6px; }
#btn-open.dsp-open .dsp-chev { transform: rotate(180deg); }
.dsp-panel { max-height: min(80vh, 600px); min-width: 260px; padding-bottom: 6px; }
.mn-hint { margin-left: auto; padding-left: 14px; flex: 0 1 auto; min-width: 0; text-align: right; }
.tbm-panel.mn-panel { max-width: min(560px, calc(100vw - 16px)); }
.mn-panel .tbm-opt .tbm-txt { flex: 0 0 auto; overflow: visible; text-overflow: clip; }
.mn-sep { height: 1px; margin: 4px 0; background: rgba(168,154,114,.35); }
.mn-opt + .mn-sep + .mn-opt { border-top: none; }
.mn-opt[aria-disabled="true"] { color: var(--khaki-light); cursor: not-allowed; opacity: .7; }
.mn-opt[aria-disabled="true"]:hover { background: none; color: var(--khaki-light); }
.dsp-opt { outline: none; color: var(--khaki-light); }
.dsp-opt:focus-visible { background: var(--olive); color: var(--amber); }
"""

RS_MENU_JS = r"""
// ── Le fichier de travail de la suite ─────────────────────────
// Le shell écrit le travail (Sauvegarder), l'ouvre (Ouvrir un travail…) et le restaure ; le module ne fait que le lui demander.
// Aucune écriture n'est différée : saveState écrit recon_state_v1 tout de suite, à chaque saisie : pas de MP_FLUSH.
function workSave() { try { parent.MP_WORK_SAVE(); } catch (e) { console.warn('[RS] sauvegarde du travail indisponible', e); } }
function workOpen() { try { parent.MP_WORK_OPEN(); } catch (e) { console.warn('[RS] ouverture du travail indisponible', e); } }
function workExample() { try { window.parent.MP_WORK_EXAMPLE('mc'); } catch (e) { console.warn('[RS] exemple indisponible', e); } }       // l'exemple se charge dans les outils du groupe, par le shell

// ── Le menu « Ouvrir » : un travail de Mission Plan, ou une image ──
// Même composant et même aspect que les listes de la barre (tbm-panel dsp-panel, dsp-opt) et que le menu « Ouvrir » du Datacard Generator.
const MENU_TRIG = '.tbm-trigger, #btn-open';
const MN = { cur: null, bound: false };

function mnClose(refocus) {
  const m = MN.cur;
  if (!m) return;
  MN.cur = null;
  if (m.panel) m.panel.remove();
  m.btn.classList.remove('dsp-open');
  m.btn.setAttribute('aria-expanded', 'false');
  if (refocus) m.btn.focus({ preventScroll: true });
}

function mnPlace(m) {
  const r = m.btn.getBoundingClientRect(), p = m.panel;
  const vw = document.documentElement.clientWidth, vh = window.innerHeight;
  const top = r.bottom + 4;
  m.x0 = r.left; m.y0 = r.top;
  p.style.minWidth = Math.min(240, vw - 16) + 'px';
  p.style.top = top + 'px';
  p.style.maxHeight = Math.max(60, Math.min(0.8 * vh, 600, vh - top - 8)) + 'px';
  const w = p.getBoundingClientRect().width;
  let left = r.left;
  if (left + w > vw - 8) left = vw - 8 - w;
  if (left < 8) left = 8;
  p.style.left = left + 'px';
}

/* o : { items, choose } (une ligne par geste ; le menu se ferme avant choose) ; items : { k, label, hint? } */
function mnOpen(btn, id, label, o) {
  if (MN.cur) mnClose(false);
  if (TBM.cur) tbmClose(false);
  const ul = document.createElement('div');
  ul.className = 'tbm-panel dsp-panel mn-panel';
  ul.id = id;
  ul.setAttribute('role', 'menu');
  ul.setAttribute('aria-label', label);
  ul.tabIndex = -1;
  o.items.forEach(it => {
    const row = document.createElement('div');
    row.className = 'tbm-opt dsp-opt mn-opt';
    row.setAttribute('role', 'menuitem');
    row.tabIndex = -1;
    row.setAttribute('data-k', it.k);
    const txt = document.createElement('span');
    txt.className = 'tbm-txt';
    txt.textContent = it.label;
    row.appendChild(txt);
    if (it.hint) { const h = document.createElement('span'); h.className = 'ui-note mn-hint'; h.textContent = it.hint; row.appendChild(h); }
    ul.appendChild(row);
  });
  document.body.appendChild(ul);
  const m = { btn: btn, panel: ul, x0: 0, y0: 0, rows: '.mn-opt:not([aria-disabled="true"])' };
  MN.cur = m;
  ul.addEventListener('click', e => {
    const row = e.target.closest ? e.target.closest('.mn-opt') : null;
    if (!row || row.getAttribute('aria-disabled') === 'true') return;
    const k = row.getAttribute('data-k');
    mnClose(false);
    btn.focus({ preventScroll: true });      /* le sélecteur de fichier ou la fenêtre qui s'ouvre rend le focus au bouton du menu */
    o.choose(k, btn);
  });
  ul.addEventListener('keydown', mnKey);
  btn.classList.add('dsp-open');
  btn.setAttribute('aria-expanded', 'true');
  btn.setAttribute('aria-controls', id);
  mnPlace(m);
  ul.focus({ preventScroll: true });
}

function mnKey(e) {
  const m = MN.cur;
  if (!m) return;
  const rows = Array.prototype.slice.call(m.panel.querySelectorAll(m.rows));
  const cur = rows.indexOf(document.activeElement);
  const go = k => { if (rows[k]) { rows[k].focus({ preventScroll: true }); rows[k].scrollIntoView({ block: 'nearest' }); } };
  const k = e.key;
  if (k === 'ArrowDown' || k === 'ArrowRight') { e.preventDefault(); go(cur < 0 ? 0 : Math.min(rows.length - 1, cur + 1)); }
  else if (k === 'ArrowUp' || k === 'ArrowLeft') { e.preventDefault(); go(cur < 0 ? rows.length - 1 : Math.max(0, cur - 1)); }
  else if (k === 'Home') { e.preventDefault(); go(0); }
  else if (k === 'End') { e.preventDefault(); go(rows.length - 1); }
  else if ((k === 'Enter' || k === ' ') && cur >= 0) { e.preventDefault(); rows[cur].click(); }
  else if (k === 'Escape') { e.preventDefault(); e.stopPropagation(); mnClose(true); }
  else if (k === 'Tab') mnClose(true);
}

/* Un toucher ou un clic hors du menu et de son bouton le ferme, sans agir ailleurs (le clic qui suit est avalé) */
function mnOutside(e) {
  const m = MN.cur;
  if (!m) return;
  const t = e.target;
  if (m.panel.contains(t) || m.btn.contains(t)) return;
  const other = t && t.closest ? t.closest(MENU_TRIG) : null;
  mnClose(false);
  if (other) return;
  tbmSwallowNext();
}

function rsOpenMenu(btn) {
  mnOpen(btn, 'op-panel', t('toolbar.open'), {
    items: [
      { k: 'work', label: t('work.open'), hint: t('work.open.hint') },
      { k: 'image', label: t('work.image'), hint: t('work.image.hint') }
    ],
    choose: k => { if (k === 'work') workOpen(); else document.getElementById('file-source').click(); }
  });
}

function mnBind() {
  if (MN.bound) return;
  MN.bound = true;
  document.addEventListener('pointerdown', mnOutside, true);
  document.addEventListener('keydown', e => { if (e.key === 'Escape' && MN.cur) { e.preventDefault(); mnClose(true); } });
  window.addEventListener('resize', () => mnClose(false));
  window.addEventListener('blur', () => mnClose(false));
  window.addEventListener('scroll', e => {
    const m = MN.cur;
    if (!m || (e.target && e.target.nodeType && m.panel.contains(e.target))) return;
    const r = m.btn.getBoundingClientRect();
    if (Math.abs(r.left - m.x0) > 0.5 || Math.abs(r.top - m.y0) > 0.5) mnClose(false);
  }, true);
  const opn = document.getElementById('btn-open');
  opn.addEventListener('click', () => { if (MN.cur && MN.cur.btn === opn) mnClose(false); else rsOpenMenu(opn); });
  opn.addEventListener('keydown', e => { if (e.key === 'ArrowDown' && !MN.cur) { e.preventDefault(); rsOpenMenu(opn); } });
  document.getElementById('btn-save').addEventListener('click', workSave);
  /* Ctrl+S (Cmd+S) : le geste du bouton « Sauvegarder », sauf fenêtre ou menu ouvert */
  document.addEventListener('keydown', e => {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 's') {
      e.preventDefault();
      if (!document.querySelector('.ui-modal:not([hidden])') && !MN.cur && !TBM.cur) workSave();
    }
  });
}
"""

HTML = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0, viewport-fit=cover">
<meta name="theme-color" content="#1a1e10">
<meta name="apple-mobile-web-app-capable" content="yes">
<title>Recon Station — Mission Plan</title>
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
  font-family: 'Stardos Stencil';
  font-weight: 400;
  font-display: swap;
  src: url('data:font/woff2;base64,{A["STARDOS_400"]}') format('woff2');
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
  font-family: 'Oswald';
  font-weight: 700;
  font-display: swap;
  src: url('data:font/woff2;base64,{A["OSWALD_700"]}') format('woff2');
}}
@font-face {{
  font-family: 'Caveat';
  font-weight: 400;
  font-display: swap;
  src: url('data:font/woff2;base64,{A["CAVEAT_400"]}') format('woff2');
}}

:root {{
  --mp-accent: #C95A9C;
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

* {{ box-sizing: border-box; margin: 0; padding: 0; }}
html, body {{ height: 100%; overscroll-behavior: none; }}
button, input, select, textarea {{ font: inherit; cursor: pointer; }}

body {{
  font-family: var(--f-typewriter);
  background: var(--olive-deep);
  color: var(--paper);
  font-size: 13px;
  line-height: 1.5;
  overflow: hidden;
  -webkit-tap-highlight-color: transparent;
  -webkit-text-size-adjust: 100%;
}}

/* l'image et ses canevas sont un document : ils gardent la taille de texte d'origine (14 px), hors de l'échelle de l'interface */
#preview-canvas, #export-canvas {{ font-size: 14px; }}

/* ======== TOOLBAR ======== */
.toolbar {{
  position: fixed;
  top: 0; left: 0; right: 0;
  height: 60px;
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
}}
.tb-select option {{ background-color: var(--olive-dark); color: var(--paper); }}

@@TBM_CSS@@

/* ---------- Listes des formulaires au thème de l'interface (lot mp-ui-listes-formulaires) ----------
   Le bouton fermé garde la boîte et le texte du <select> du champ ; seul le chevron est dessiné (12 × 8, trait 1,6 px, couleur du texte,
   à 12 px du bord droit, 8 px sur un champ de moins de 120 px). La liste ouverte garde la police, la casse et la graisse du champ. */
.ed-select.tbm-trigger.tbm-field {{
  display: block; position: relative; contain: inline-size; text-align: left; letter-spacing: normal; text-transform: none; font-weight: 400; border-radius: 0;
  padding: 5px 34px 5px 8px;
}}
.ed-select.tbm-trigger.tbm-field::after {{
  content: ''; position: absolute; right: 12px; top: 50%; width: 12px; height: 8px; margin-top: -4px; pointer-events: none;
  background: currentColor; -webkit-mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='8' viewBox='0 0 12 8'%3E%3Cpath d='M1 1.5l5 5 5-5' fill='none' stroke='%23000' stroke-width='1.6'/%3E%3C/svg%3E") center / 12px 8px no-repeat; mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='8' viewBox='0 0 12 8'%3E%3Cpath d='M1 1.5l5 5 5-5' fill='none' stroke='%23000' stroke-width='1.6'/%3E%3C/svg%3E") center / 12px 8px no-repeat;
}}
.ed-select.tbm-trigger.tbm-field.tbm-narrow {{ padding-right: 26px; }}
.ed-select.tbm-trigger.tbm-field.tbm-narrow::after {{ right: 8px; }}
.ed-select.tbm-trigger.tbm-field .tbm-lbl {{ margin: 0; padding: 0; line-height: 17px; }}
.ed-select.tbm-trigger.tbm-field .tbm-lbl::after {{ display: none; }}
.ed-select.tbm-trigger.tbm-field:focus-visible {{ border-color: var(--amber); }}

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
}}
/* Exemple (lot mp-exemples-demarrer) : bouton de la barre, avec son texte quand elle a la place (lot mp-imports-suite) ;
   borné à la barre du haut : les .tb-btn de la barre de dessin et de sa fiche ont leurs propres règles (.rsd-ui, .rsd-sheet) */
.toolbar .tb-btn {{
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
}}
.toolbar .tb-btn:hover, .toolbar .tb-btn:focus-visible {{
  background: var(--olive);
  border-color: var(--amber);
  color: var(--amber);
}}
.toolbar .tb-btn.danger:hover {{ background: var(--rust); border-color: var(--red-faded); color: var(--paper-light); }}
.toolbar .tb-btn:active {{ transform: translateY(1px); }}
.toolbar .tb-btn svg {{ width: 16px; height: 16px; flex-shrink: 0; }}
.tb-spacer {{ flex: 1; }}
.tb-version {{
  font-size: 11px;
  opacity: .45;
  color: var(--amber);
  letter-spacing: .5px;
  user-select: none;
  white-space: nowrap;
}}
@media (max-width: 479px) {{
  .toolbar {{ gap: 6px; padding-left: max(8px, env(safe-area-inset-left)); padding-right: max(8px, env(safe-area-inset-right)); }}
  .tb-brand {{ min-width: 0; }}
  .tb-brand-sub, .tb-sep {{ display: none; }}
  .tb-brand-main {{ font-size: 13px; letter-spacing: 2px; }}
  .tb-select {{ font-size: 11px; letter-spacing: .5px; padding: 0 22px 0 8px; background-position: right 6px center; }}
  .tb-select.tbm-trigger {{ min-width: 0; flex: 0 1 auto; }}
  .tb-lang-btn {{ min-width: 36px; padding: 0 4px; }}
}}


/* ---------- Barre du haut commune aux sept modules (lot mp-imports-suite) ----------
   La marque du Flight Configurator : le titre et son sous-titre à l'accent du module dès 1051 px, le sigle seul en dessous (à toutes les largeurs) ;
   la version avec le titre ; le tampon de décor dès 859 px ; les textes des boutons dès 480 px (la barre les porte dès 268 px ; sous 480 px la règle des téléphones garde l'icône seule). Seuils mesurés dans le shell avec un tampon d'escadre « TEST WING », en français et en anglais, en paysage et en portrait
   (lot mp-ui-disposition-b : « Exporter » est dans la barre, qui tient sans défiler à toutes les largeurs mesurées, dès 330 px ; chaque seuil est la plus petite largeur où elle tient avec ce qui précède, le français donnant le seuil). */
.tb-brand-main, .tb-brand-short {{ color: #c95a9c; }}
.tb-brand-short {{ display: none; font-family: var(--f-stencil); font-size: 16px; font-weight: 700; letter-spacing: 3px; white-space: nowrap; }}
.tb-classif {{ font-family: var(--f-stencil); font-weight: 400; font-size: 11px; letter-spacing: 3px; color: var(--red-faded); border: 1px solid var(--red-faded); padding: 4px 10px; white-space: nowrap; flex-shrink: 0; }}
.tb-lang-btn svg {{ display: block; }}
.tb-brand-sub {{ font-weight: 500; }}
.tb-version {{ font-family: 'Roboto Mono', monospace; }}
.toolbar .tb-btn {{ width: auto; height: 38px; min-width: 38px; padding: 0 12px; gap: 6px; font-family: var(--f-ui); font-weight: 500; letter-spacing: 1.5px; font-size: 12px; text-transform: uppercase; white-space: nowrap; }}
@media (max-width: 479px) {{ .toolbar .tb-btn {{ width: 34px; min-width: 34px; }} }}

/* ======== MAIN LAYOUT ======== */
.app {{
  position: fixed;
  top: 60px; bottom: 0; left: 0; right: 0;
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
  display: flex; align-items: center;
  border-bottom: 1px solid var(--amber-dark);
  min-height: 44px;
}}
.ed-section > .ed-body {{ padding: 12px; }}

/* Form fields */
.ed-row {{
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}}
.ed-label {{ font-weight: 500;
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
.ed-input:focus {{ border-color: var(--amber); }}
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
.ed-select:focus {{ border-color: var(--amber); }}
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
.drop-zone {{ font-weight: 500;
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
/* Crédit de l'image de l'exemple : discret, hors de l'export */
.img-credit {{ font-weight: 500;
  margin-top: 6px;
  font-family: var(--f-ui);
  font-size: 10px;
  letter-spacing: 1px;
  text-align: center;
  color: var(--khaki);
  opacity: .85;
}}
.img-credit[hidden] {{ display: none; }}

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
  font-weight: 400;
}}
.btn-remove-row {{
  background: var(--olive-dark);
  border: 1px solid var(--red-faded);
  color: var(--red-faded);
  padding: 4px 6px;
  cursor: pointer;
  font-size: 13px;
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
  font-size: 13px;
  transition: all .15s;
  cursor: pointer;
}}
.cartouche-point-toggle input:checked + .point-marker {{
  border-color: #E22;
  color: #E22;
  background: rgba(238,34,34,.12);
}}
.btn-add-row {{ font-weight: 500;
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
.shapes-toolbox button {{ font-weight: 500;
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
.shape-color-group button {{ font-weight: 500;
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
.amorce-marker {{ font-weight: 500;
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
.inset-color-group button {{ font-weight: 500;
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
.inset-label-input:focus {{ border-color: var(--amber); }}

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
.logo-thumb-none {{ font-weight: 500;
  color: var(--khaki);
  font-family: var(--f-ui);
  font-size: 10px;
  letter-spacing: 1px;
  text-align: center;
}}

/* Le bouton « Exporter » de la barre : grisé tant qu'il n'y a pas d'image */
.tb-btn:disabled {{ opacity: .35; cursor: not-allowed; }}
.tb-btn:disabled:hover {{ background: transparent; border-color: var(--khaki); }}

/* Replace image button */
.btn-replace {{ font-weight: 500;
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
.btn-upload-logo {{ font-weight: 500;
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
.logo-mode-label {{ font-weight: 500;
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
.logo-mode button {{ font-weight: 500;
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
#preview-canvas[hidden] {{ display: none; }}   /* « display: block » ci-dessus l'emportait sur l'attribut hidden : après Effacer, l'ancien dessin restait affiché */
.preview-placeholder {{
  text-align: center;
  color: var(--khaki);
  font-family: var(--f-ui);
  font-size: 13px;
  letter-spacing: 2px;
  text-transform: uppercase;
  user-select: none;
  pointer-events: none;
}}
.preview-placeholder svg {{
  width: 64px; height: 64px;
  margin-bottom: 12px;
  opacity: .15;   /* l'atténuation porte sur le dessin, pas sur le texte (lisible, 4,5 : 1) */
}}

/* ======== FENÊTRE « NOM DU FICHIER » ======== */

@@MESSAGES_CSS@@

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
  .app[data-active-tab="editor"] .editor {{ max-height: calc(100vh - 60px - 48px); order: 1; }}
  .app[data-active-tab="preview"] .editor {{ display: none; }}
  .app[data-active-tab="preview"] .preview {{ min-height: calc(100vh - 60px - 48px); order: 1; }}
}}
@media (min-width: 1101px) {{
  .tab-bar {{ display: none; }}
}}

{RSD_CSS}
{RS_MENU_CSS}
{CONTRAST_CSS}</style>
</head>
<body data-theme="cw-nato">

<!-- TOOLBAR -->
<header class="toolbar" role="toolbar" aria-label="Recon Station">
  <div class="tb-brand">
    <span class="tb-brand-main">RECON STATION</span>
    <span class="tb-brand-short">R·S</span>
    <span class="tb-brand-sub" data-i18n="toolbar.subtitle">░ RENSEIGNEMENT</span>
  </div>
  <button type="button" class="tb-btn tb-file" id="btn-open" aria-haspopup="menu" aria-expanded="false" data-i18n-title="toolbar.open.tooltip" title="Ouvrir un travail ou une image" data-i18n-aria-label="toolbar.open.tooltip" aria-label="Ouvrir un travail ou une image">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v1H3z"/><path d="M3 10h19l-2 8a2 2 0 0 1-2 1.5H5a2 2 0 0 1-2-2z"/></svg>
    <span class="tb-btn-label" data-i18n="toolbar.open">Ouvrir</span>
    <svg class="dsp-chev" viewBox="0 0 10 6" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M1 1l4 4 4-4"/></svg>
  </button>
  <button type="button" class="tb-btn tb-file" id="btn-save" data-i18n-title="work.save.tip" title="Sauvegarder tout le travail de Mission Plan (JSON)" data-i18n-aria-label="work.save.tip" aria-label="Sauvegarder tout le travail de Mission Plan (JSON)">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 3h11l4 4v13a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1z"/><path d="M8 3v5h7V3"/><rect x="7" y="13" width="10" height="8"/></svg>
    <span class="tb-btn-label" data-i18n="toolbar.save">Sauvegarder</span>
  </button>
  <button type="button" class="tb-btn tb-file" id="btn-export" disabled data-i18n-title="toolbar.export.tooltip" title="Exporter l'image (PNG pleine résolution)" data-i18n-aria-label="toolbar.export.tooltip" aria-label="Exporter l'image (PNG pleine résolution)">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
    <span class="tb-btn-label" data-i18n="toolbar.export">Exporter</span>
  </button>
  <div class="tb-sep tb-files-end" aria-hidden="true"></div>
  <button type="button" class="tb-btn" id="btn-example" data-i18n-title="toolbar.example.tooltip" title="Charger l’exemple STEPPE WIND dans les outils du Mission Commander (Briefing Generator, Recon Station) ; le travail en cours du groupe se restaure en un geste" data-i18n-aria-label="toolbar.example.tooltip" aria-label="Charger l’exemple STEPPE WIND dans les outils du Mission Commander (Briefing Generator, Recon Station) ; le travail en cours du groupe se restaure en un geste">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="8" y1="13" x2="16" y2="13"/><line x1="8" y1="17" x2="16" y2="17"/></svg>
    <span class="tb-btn-label" data-i18n="toolbar.example">Exemple</span>
  </button>
  <button type="button" class="tb-btn danger" id="btn-reset" data-i18n-title="toolbar.reset.tooltip" title="Effacer" data-i18n-aria-label="toolbar.reset.tooltip" aria-label="Effacer">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/><path d="M10 11v6M14 11v6"/><path d="M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/></svg>
    <span class="tb-btn-label" data-i18n="toolbar.reset">Effacer</span>
  </button>
  <select class="tb-select" id="theme-select" data-i18n-title="toolbar.theme.tooltip" title="Thème graphique">
    <option value="cw-nato"     data-i18n="theme.cw-nato">Cold War OTAN</option>
    <option value="cw-soviet"   data-i18n="theme.cw-soviet">Cold War Soviétique</option>
    <option value="modern-nato" data-i18n="theme.modern-nato">OTAN moderne</option>
    <option value="modern-east" data-i18n="theme.modern-east">Bloc Est moderne</option>
  </select>
  <div class="tb-spacer"></div>
  <div class="tb-classif">IMINT // CONFIDENTIAL</div>
  <span class="tb-version">v{APP_VERSION}</span>
  <button class="tb-lang-btn" id="btn-lang" title="Passer en anglais" aria-label="Passer en anglais"><svg viewBox="0 0 20 14" width="22" height="15" xmlns="http://www.w3.org/2000/svg"><rect width="20" height="14" fill="#012169"/><path d="M0,0 L20,14 M20,0 L0,14" stroke="#fff" stroke-width="2.8"/><path d="M0,0 L20,14 M20,0 L0,14" stroke="#C8102E" stroke-width="1.6"/><rect x="8" width="4" height="14" fill="#fff"/><rect y="5" width="20" height="4" fill="#fff"/><rect x="9" width="2" height="14" fill="#C8102E"/><rect y="6" width="20" height="2" fill="#C8102E"/></svg></button>
</header>

<!-- MAIN APP -->
<div class="app" id="app" data-active-tab="editor">

  <!-- EDITOR -->
  <div class="editor" id="editor-panel" role="complementary">
    <div class="ui-foldbar"><button type="button" class="ui-btn ui-foldall" id="rs-foldall"></button></div>

    <!-- Section Image -->
    <details class="ed-section" data-section="image">
      <summary class="ui-fold-head"><span data-i18n="editor.image.title">IMAGE SOURCE</span></summary>
      <div class="ed-body">
        <div class="drop-zone" id="drop-zone" tabindex="0"
             data-i18n-aria-label="editor.image.dropzone.aria"
             aria-label="Zone de dépôt d'image">
          <div id="drop-zone-text" data-i18n="editor.image.drop">↓ DÉPOSER UNE IMAGE ICI</div>
          <div class="ui-note" style="margin-top:6px" data-i18n="editor.image.drop.hint">PNG · JPEG — cliquer pour parcourir</div>
        </div>
        <div class="img-credit" id="img-credit" data-i18n="editor.image.credit" hidden>Image : USDA NAIP, domaine public</div>
        <input type="file" id="file-source" accept="image/png,image/jpeg,image/webp" hidden>
        <button class="btn-replace" id="btn-replace" data-i18n="editor.image.replace">↺ REMPLACER L'IMAGE</button>
      </div>
    </details>

    <!-- Section Rendu -->
    <details class="ed-section" data-section="render">
      <summary class="ui-fold-head"><span data-i18n="editor.render.title">RENDU</span></summary>
      <div class="ed-body">
        <div class="ed-row">
          <span class="ed-label" data-i18n="editor.render.contrast">CONTRASTE</span>
          <input type="range" class="ed-slider" id="contrast-slider" min="100" max="130" value="105" step="1">
          <span id="contrast-val" style="min-width:36px;text-align:right;font-family:var(--f-typewriter);font-size:12px;color:var(--amber)">105%</span>
        </div>
      </div>
    </details>

    <!-- Section Couleur texte -->
    <details class="ed-section" data-section="text">
      <summary class="ui-fold-head"><span data-i18n="editor.text.title">COULEUR DU TEXTE</span></summary>
      <div class="ed-body">
        <div class="logo-mode" id="text-color-group" role="group" data-i18n-aria-label="aria.textColor" aria-label="Couleur du texte">
          <button type="button" data-text-color="#fff" data-i18n="editor.text.white">Blanc</button>
          <button type="button" data-text-color="#000" data-i18n="editor.text.black">Noir</button>
        </div>
      </div>
    </details>

    <!-- Section Effets -->
    <details class="ed-section" data-section="fx">
      <summary class="ui-fold-head"><span data-i18n="editor.fx.title">EFFETS</span></summary>
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
    <details class="ed-section" data-section="info">
      <summary class="ui-fold-head"><span data-i18n="editor.info.title">BLOC D'INFORMATIONS</span></summary>
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
    <details class="ed-section" data-section="logo">
      <summary class="ui-fold-head"><span data-i18n="editor.logo.title">LOGO</span></summary>
      <div class="ed-body">
        <div class="logo-grid" id="logo-grid"></div>
        <label class="btn-upload-logo" for="file-logo" data-i18n="editor.logo.upload">↑ IMPORTER UN LOGO PNG</label>
        <input type="file" id="file-logo" accept="image/png,image/webp" hidden>
        <label class="btn-upload-logo" for="file-wing" data-i18n="editor.logo.importWing" style="margin-top:4px">📥 Importer config</label>
        <input type="file" id="file-wing" accept=".json,application/json" hidden>
        <p class="ui-note" data-i18n="editor.logo.importWing.note">✦ Édition complète disponible dans HQ</p>
        <div class="logo-mode-label" data-i18n="editor.logo.mode.title">RENDU DU LOGO</div>
        <div class="logo-mode" id="logo-mode" role="group" data-i18n-aria-label="aria.logoMode" aria-label="Rendu du logo">
          <button type="button" data-logo-mode="color" data-i18n="editor.logo.mode.color">COULEUR</button>
          <button type="button" data-logo-mode="gray"  data-i18n="editor.logo.mode.gray">GRIS</button>
          <button type="button" data-logo-mode="white" data-i18n="editor.logo.mode.white">BLANC</button>
        </div>
      </div>
    </details>

    <!-- Section Cartouche -->
    <details class="ed-section" data-section="cartouche">
      <summary class="ui-fold-head"><span data-i18n="editor.cartouche.title">CARTOUCHE</span></summary>
      <div class="ed-body">
        <div id="cartouche-editor"></div>
        <button class="btn-add-row" id="btn-add-cartouche" data-i18n="editor.cartouche.add">+ AJOUTER UN MARQUAGE</button>
      </div>
    </details>

    <!-- Section Formes (Lot 1) -->
    <details class="ed-section" data-section="shapes">
      <summary class="ui-fold-head"><span data-i18n="editor.shapes.title">FORMES</span></summary>
      <div class="ed-body">
        <div class="shapes-toolbox">
          <button type="button" id="btn-add-ellipse" title="Ellipse" data-i18n-title="editor.shapes.ellipse.tooltip">◯</button>
          <button type="button" id="btn-add-rect"    title="Rectangle" data-i18n-title="editor.shapes.rect.tooltip">▭</button>
          <button type="button" id="btn-add-poly"    title="Polygone" data-i18n-title="editor.shapes.poly.tooltip">⬡</button>
          <button type="button" id="btn-add-arrow"   title="Flèche" data-i18n-title="editor.shapes.arrow.tooltip">→</button>
          <button type="button" id="btn-add-bracket" title="Crochet" data-i18n-title="editor.shapes.bracket.tooltip">⊐</button>
        </div>
        <div id="shapes-editor"></div>
        <button class="btn-add-row btn-add-inset" id="btn-add-inset" data-i18n="editor.inset.add">+ AJOUTER UNE LOUPE</button>
        <div id="inset-editor"></div>
        <button class="btn-add-row btn-add-inset" id="btn-add-label" data-i18n="editor.label.add" data-i18n-title="editor.label.add.tooltip">+ LABEL</button>
        <div id="label-editor"></div>
      </div>
    </details>

    <!-- Section Couleur marquages -->
    <details class="ed-section" data-section="marker">
      <summary class="ui-fold-head"><span data-i18n="editor.marker.color">COULEUR DES MARQUAGES</span></summary>
      <div class="ed-body">
        <div class="logo-mode" id="marker-color-group" role="group" data-i18n-aria-label="aria.markerColor" aria-label="Couleur des marquages">
          <button type="button" data-marker-color="red"   data-i18n="editor.marker.red">Rouge</button>
          <button type="button" data-marker-color="black" data-i18n="editor.marker.black">Noir</button>
          <button type="button" data-marker-color="white" data-i18n="editor.marker.white">Blanc</button>
        </div>
      </div>
    </details>

    <!-- Section Classification (R2-B Lot 2) -->
    <details class="ed-section" data-section="classif">
      <summary class="ui-fold-head"><span data-i18n="editor.classif.title">CLASSIFICATION</span></summary>
      <div class="ed-body">
        <label class="ed-toggle-row">
          <input type="checkbox" id="classif-enable">
          <span data-i18n="editor.classif.enable">Activer le bandeau</span>
        </label>
        <div class="ed-row" style="margin-top:6px">
          <span class="ed-label" data-i18n="editor.classif.level">NIVEAU</span>
          <select id="classif-level" class="ed-select">
            <option value="confidential"    data-i18n="classif.confidential">CONFIDENTIEL DÉFENSE</option>
            <option value="secret"          data-i18n="classif.secret">SECRET DÉFENSE</option>
            <option value="top-secret"      data-i18n="classif.top-secret">TRÈS SECRET</option>
            <option value="unclassified"    data-i18n="classif.unclassified">NON CLASSIFIÉ</option>
            <option value="nato-restricted" data-i18n="classif.nato-restricted">NATO RESTRICTED</option>
            <option value="nato-secret"     data-i18n="classif.nato-secret">NATO SECRET</option>
          </select>
        </div>
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
    <!-- Annoter au doigt : la couche des poignées, la barre, le message et la fiche -->
    <div class="rsd-ov" id="rsd-ov"><svg class="rsd-svg" id="rsd-svg" aria-hidden="true"></svg><svg class="rsd-prev" id="rsd-prev" aria-hidden="true"></svg></div>
    <div class="dr-ui rsd-ui" id="rsd-ui" hidden>
      <div class="dr-hint" id="rsd-hint" role="status" hidden><span class="dr-msg" id="rsd-msg"></span><span class="dr-acts" id="rsd-acts"></span></div>
      <div class="dr-bar" id="rsd-bar" role="toolbar"></div>
    </div>
    <div class="dr-sheet rsd-sheet" id="rsd-sheet" role="group" hidden></div>
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

<!-- FENÊTRE : EXPORTER L'IMAGE — CHOISIR LE NOM DU FICHIER -->
<div class="ui-modal" id="fn-modal" hidden role="dialog" aria-modal="true" aria-labelledby="fn-title">
  <div class="ui-backdrop" id="fn-backdrop"></div>
  <div class="ui-panel" role="document">
    <button type="button" class="ui-close" id="fn-close" data-i18n-aria-label="modal.close" aria-label="Fermer">&times;</button>
    <h2 id="fn-title" class="ui-title" data-i18n="fn.title">Exporter l'image</h2>
    <div class="ui-field"><label class="ui-lbl" for="fn-name" data-i18n="fn.label">Nom du fichier</label><div class="ui-row"><input class="ui-in" id="fn-name" type="text" autocomplete="off" autocapitalize="off" spellcheck="false" maxlength="100"><span class="ui-ext">.png</span></div></div>
    <div class="ui-actions">
      <button type="button" class="ui-btn" id="fn-cancel" data-i18n="fn.cancel">Annuler</button>
      <button type="button" class="ui-btn primary" id="fn-go" data-i18n="fn.go">Exporter</button>
    </div>
  </div>
</div>

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
    'ui.cancel': 'Annuler',
    'f.search': 'Rechercher…',
    'ui.close': 'Fermer',
    'ui.restore': 'Restaurer',
    'ui.restore.refused': 'Restauration impossible : les données ont changé depuis.',
    'ui.foldall': 'Tout replier',
    'ui.unfoldall': 'Tout déplier',
    'ui.fmt': 'Format',
    'ui.pages': 'Pages',
    'ui.fname': 'Nom du fichier',
    'ui.export': 'Exporter',
    'toolbar.theme.tooltip': 'Thème graphique',
    'toolbar.lang.tooltip': 'Passer en anglais',
    'toolbar.subtitle': '░ RENSEIGNEMENT',
    'toolbar.open': 'Ouvrir',
    'toolbar.open.tooltip': 'Ouvrir un travail ou une image',
    'toolbar.save': 'Sauvegarder',
    'work.open': 'Ouvrir un travail…',
    'work.open.hint': '.json',
    'work.image': 'Ouvrir une image…',
    'work.image.hint': 'PNG · JPG · WEBP',
    'work.save.tip': 'Sauvegarder tout le travail de Mission Plan (JSON)',
    'toolbar.export': 'Exporter',
    'toolbar.export.tooltip': "Exporter l'image (PNG pleine résolution)",
    'toolbar.example': 'Exemple',
    'toolbar.example.tooltip': "Charger l’exemple STEPPE WIND dans les outils du Mission Commander (Briefing Generator, Recon Station) ; le travail en cours du groupe se restaure en un geste",
    'toolbar.reset': 'Effacer',
    'toolbar.reset.tooltip': 'Effacer',
    'clear.title': 'Effacer le Recon Station ?',
    'clear.text': 'L\u2019image, ses annotations, la l\u00e9gende et le bloc d\u2019informations seront effac\u00e9s. Le th\u00e8me et la configuration Wing restent.',
    'clear.verb': 'Effacer',
    'clear.toast': 'Recon Station effac\u00e9.',
    'msg.exampleUnavailable': '⚠ Exemple indisponible.',
    'editor.image.credit': 'Image : USDA NAIP, domaine public',
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
    'preview.empty': 'IMPORTER UNE IMAGE POUR COMMENCER',
    'tab.editor': 'ÉDITEUR',
    'tab.preview': 'APERÇU',
    'tab.editor.aria': 'Onglet éditeur',
    'tab.preview.aria': 'Onglet aperçu',
    'toast.theme': 'Thème appliqué',
    'toast.no-image': '⚠ Aucune image source — veuillez en importer une',
    'toast.export.start': 'Export en cours…',
    'toast.export.done': 'Image exportée',
    'fn.label': 'Nom du fichier',
    'fn.title': 'Exporter l’image',
    'fn.cancel': 'Annuler',
    'fn.go': 'Exporter',
    'modal.close': 'Fermer',
    'toast.state-restored': 'Paramètres restaurés — importer une image pour continuer',
    'toast.image-loaded': 'Image chargée',
    'editor.text.title': 'COULEUR DU TEXTE',
    'editor.text.white': 'Blanc',
    'editor.text.black': 'Noir',
    'editor.marker.color': 'COULEUR DES MARQUAGES',
    'editor.marker.red': 'Rouge',
    'editor.marker.black': 'Noir',
    'editor.marker.white': 'Blanc',
    'msg.notImage': '⚠ Le fichier doit être une image.',
    'msg.imageUnreadable': '⚠ Image illisible.',
    'msg.exportFailed': '⚠ Export impossible.',
    'msg.jsonUnreadable': '⚠ Fichier illisible : ce n’est pas du JSON.',
    'msg.notWingConfig': '⚠ Ce fichier n’est pas une configuration wing.',
    'msg.wingIncomplete': '⚠ Configuration wing incomplète : {{0}} champ(s) manquant(s) ou invalide(s).',
    'msg.failed': '⚠ L’opération a échoué.',
    'editor.logo.removeCustom': 'Supprimer le logo importé',
    'editor.logo.none': 'Aucun logo',
    'sum.none': 'Aucun',
    'aria.textColor': 'Couleur du texte',
    'aria.logoMode': 'Rendu du logo',
    'aria.markerColor': 'Couleur des marquages',
    'editor.logo.importWing': '📥 Importer config',
    'editor.logo.importWing.note': '✦ Édition complète disponible dans HQ',
    'toast.noLogoInJson': '⚠ Aucun logo dans ce fichier',
    'validate.schemaMissing': 'configSchemaVersion doit être 1',
    'validate.wingMissing': 'Champ wing manquant',
    'validate.shortNameMissing': 'wing.shortName manquant',
    'validate.logoInvalid': 'wing.logo doit être une data URL image valide (data:image/…)',
    'validate.squadronsNotArray': 'squadrons doit être un tableau',
    'validate.sqIdMissing': '.id manquant',
    'validate.sqCallsignMissing': '.callsign manquant',
    'validate.sqAircraftNotArray': '.aircraft doit être un tableau',
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
    'classif.confidential': 'CONFIDENTIEL DÉFENSE',
    'classif.secret': 'SECRET DÉFENSE',
    'classif.top-secret': 'TRÈS SECRET',
    'classif.unclassified': 'NON CLASSIFIÉ',
    'classif.nato-restricted': 'NATO RESTRICTED',
    'classif.nato-secret': 'NATO SECRET',
{RSD_I18N_FR}  }},
  en: {{
    'ui.cancel': 'Cancel',
    'f.search': 'Search…',
    'ui.close': 'Close',
    'ui.restore': 'Restore',
    'ui.restore.refused': 'Cannot restore: the data has changed since.',
    'ui.foldall': 'Fold all',
    'ui.unfoldall': 'Unfold all',
    'ui.fmt': 'Format',
    'ui.pages': 'Pages',
    'ui.fname': 'File name',
    'ui.export': 'Export',
    'toolbar.theme.tooltip': 'Graphic theme',
    'toolbar.lang.tooltip': 'Switch to French',
    'toolbar.subtitle': '░ INTELLIGENCE',
    'toolbar.open': 'Open',
    'toolbar.open.tooltip': 'Open a work file or an image',
    'toolbar.save': 'Save',
    'work.open': 'Open a work file…',
    'work.open.hint': '.json',
    'work.image': 'Open an image…',
    'work.image.hint': 'PNG · JPG · WEBP',
    'work.save.tip': 'Save all the Mission Plan work (JSON)',
    'toolbar.export': 'Export',
    'toolbar.export.tooltip': 'Export the image (full-resolution PNG)',
    'toolbar.example': 'Example',
    'toolbar.example.tooltip': 'Load the STEPPE WIND example into the Mission Commander tools (Briefing Generator, Recon Station); the group’s work in progress comes back in one tap',
    'toolbar.reset': 'Clear',
    'toolbar.reset.tooltip': 'Clear',
    'clear.title': 'Clear the Recon Station?',
    'clear.text': 'The image, its marks, the legend and the information block will be cleared. The theme and the wing configuration stay.',
    'clear.verb': 'Clear',
    'clear.toast': 'Recon Station cleared.',
    'msg.exampleUnavailable': '⚠ Example unavailable.',
    'editor.image.credit': 'Image: USDA NAIP, public domain',
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
    'preview.empty': 'IMPORT AN IMAGE TO BEGIN',
    'tab.editor': 'EDITOR',
    'tab.preview': 'PREVIEW',
    'tab.editor.aria': 'Editor tab',
    'tab.preview.aria': 'Preview tab',
    'toast.theme': 'Theme applied',
    'toast.no-image': '⚠ No source image — please import one',
    'toast.export.start': 'Exporting…',
    'toast.export.done': 'Image exported',
    'fn.label': 'File name',
    'fn.title': 'Export the image',
    'fn.cancel': 'Cancel',
    'fn.go': 'Export',
    'modal.close': 'Close',
    'toast.state-restored': 'Settings restored — import an image to continue',
    'toast.image-loaded': 'Image loaded',
    'editor.text.title': 'TEXT COLOR',
    'editor.text.white': 'White',
    'editor.text.black': 'Black',
    'editor.marker.color': 'MARKER COLOR',
    'editor.marker.red': 'Red',
    'editor.marker.black': 'Black',
    'editor.marker.white': 'White',
    'msg.notImage': '⚠ The file must be an image.',
    'msg.imageUnreadable': '⚠ Unreadable image.',
    'msg.exportFailed': '⚠ Export failed.',
    'msg.jsonUnreadable': '⚠ Unreadable file: this is not JSON.',
    'msg.notWingConfig': '⚠ This file is not a wing configuration.',
    'msg.wingIncomplete': '⚠ Incomplete wing configuration: {{0}} missing or invalid field(s).',
    'msg.failed': '⚠ The operation failed.',
    'editor.logo.removeCustom': 'Remove imported logo',
    'editor.logo.none': 'No logo',
    'sum.none': 'None',
    'aria.textColor': 'Text color',
    'aria.logoMode': 'Logo rendering',
    'aria.markerColor': 'Marker color',
    'editor.logo.importWing': '📥 Import config',
    'editor.logo.importWing.note': '✦ Full editing available in HQ',
    'toast.noLogoInJson': '⚠ No logo in this file',
    'validate.schemaMissing': 'configSchemaVersion must be 1',
    'validate.wingMissing': 'Missing wing field',
    'validate.shortNameMissing': 'wing.shortName missing',
    'validate.logoInvalid': 'wing.logo must be a valid image data URL (data:image/…)',
    'validate.squadronsNotArray': 'squadrons must be an array',
    'validate.sqIdMissing': '.id missing',
    'validate.sqCallsignMissing': '.callsign missing',
    'validate.sqAircraftNotArray': '.aircraft must be an array',
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
    'classif.confidential': 'CONFIDENTIAL',
    'classif.secret': 'SECRET',
    'classif.top-secret': 'TOP SECRET',
    'classif.unclassified': 'UNCLASSIFIED',
    'classif.nato-restricted': 'NATO RESTRICTED',
    'classif.nato-secret': 'NATO SECRET',
{RSD_I18N_EN}  }}
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

// L'état d'un profil neuf (ses champs vides sont aussi ceux que « Effacer » rend)
function rsFreshState() {{
  return {{
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
    classification: {{ enabled: false, level: 'unclassified' }},  // R2-B Lot 2
  }};
}}
let STATE = rsFreshState();

/* Les six niveaux du Briefing Generator (clés du BG, libellés « classif.* » dans la langue de l'outil) ; une valeur enregistrée avant (UNCLASSIFIED, CONFIDENTIAL, SECRET, TOP SECRET) se relit sur le niveau correspondant */
const RS_CLASS_KEYS = ['confidential', 'secret', 'top-secret', 'unclassified', 'nato-restricted', 'nato-secret'];
const RS_CLASS_OLD = {{ 'UNCLASSIFIED': 'unclassified', 'CONFIDENTIAL': 'confidential', 'SECRET': 'secret', 'TOP SECRET': 'top-secret' }};
function rsClassKey(v) {{ return RS_CLASS_KEYS.indexOf(v) >= 0 ? v : (RS_CLASS_OLD[v] || 'unclassified'); }}

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
    const ffCaveat = new FontFace('Caveat',
      `url(data:font/woff2;base64,${{CAVEAT_B64}})`,
      {{ weight: '400', style: 'normal' }}
    );
    fontsReadyPromise = Promise.all([ff400.load(), ffCaveat.load()]).then(faces => {{
      faces.forEach(f => document.fonts.add(f));
      return document.fonts.ready;
    }}).then(() => {{
      fontsReady = true;
    }});
  }}
  return fontsReadyPromise;
}}

@@MESSAGES_BLOCK@@

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
  showToast(t('toast.theme'));
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
}}

/* Drapeaux dessinés (ils ne s'affichent pas en lettres sous Windows) ; le bouton montre la langue vers laquelle il bascule */
const FLAG_FR = '<svg viewBox="0 0 20 14" width="22" height="15" xmlns="http://www.w3.org/2000/svg"><rect width="7" height="14" fill="#002395"/><rect x="7" width="6" height="14" fill="#fff"/><rect x="13" width="7" height="14" fill="#ED2939"/></svg>';
const FLAG_EN = '<svg viewBox="0 0 20 14" width="22" height="15" xmlns="http://www.w3.org/2000/svg"><rect width="20" height="14" fill="#012169"/><path d="M0,0 L20,14 M20,0 L0,14" stroke="#fff" stroke-width="2.8"/><path d="M0,0 L20,14 M20,0 L0,14" stroke="#C8102E" stroke-width="1.6"/><rect x="8" width="4" height="14" fill="#fff"/><rect y="5" width="20" height="4" fill="#fff"/><rect x="9" width="2" height="14" fill="#C8102E"/><rect y="6" width="20" height="2" fill="#C8102E"/></svg>';

function updateFlagButton() {{
  const btn = document.getElementById('btn-lang');
  if (!btn) return;
  btn.innerHTML = CURRENT_LANG === 'fr' ? FLAG_EN : FLAG_FR;
  btn.title = t('toolbar.lang.tooltip');
  btn.setAttribute('aria-label', t('toolbar.lang.tooltip'));
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
  rsFoldRefresh();
  renderCartoucheEditor();
  renderInsetEditor();
  renderShapesEditor();
  renderLabelEditor();
  renderLogoGrid();      // le titre de la vignette « Aucun logo »
  renderLogoMode();
  renderTextColor();
  renderMarkerColor();
  rsdSyncUi();
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
  if (document.getElementById('rs-foldall')) rsFoldRefresh();
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
      STATE.classification = {{ enabled: !!saved.classification.enabled, level: rsClassKey(saved.classification.level) }};
    }}
    // L'image de l'exemple : l'image source n'est jamais enregistrée ; un état qui porte exampleImage: true la recharge (la même image, la même zone, le même crédit)
    if (saved.exampleImage === true) {{
      STATE.exampleImage = true;
      if (!SOURCE_READY) rsExampleImage();
    }} else delete STATE.exampleImage;
    return true;
  }} catch(e) {{ return false; }}
}}

/* Au démarrage du module, les champs vides Msn, DTG et Class se remplissent du briefing en cours (la clé du Briefing Generator, lue à l'instant, jamais réécrite) :
   Msn = opération et mission, DTG = la date du briefing en JJ.MM.AAAA, Class = le libellé de la classification dans la langue de l'outil. Un champ rempli n'est jamais écrasé ;
   Crew reste à saisir (un briefing porte plusieurs groupes). Sans briefing lisible, rien ne change et rien ne s'écrit. */
const KEY_BRIEFING = 'khr26_briefing_state_v2';
function rsBriefingFill() {{
  let b = null;
  try {{ b = JSON.parse(localStorage.getItem(KEY_BRIEFING)); }} catch (e) {{ b = null; }}
  const m = b && typeof b === 'object' && b.meta && typeof b.meta === 'object' ? b.meta : null;
  if (!m) return false;
  const s = v => (typeof v === 'string' ? v.trim() : '');
  const want = {{}};
  const msn = [s(m.operation), s(m.mission)].filter(x => x !== '').join(' ');
  if (msn) want.msn = msn;
  const d = /^([0-9]{{4}})-([0-9]{{2}})-([0-9]{{2}})$/.exec(s(m.date));
  if (d) want.dtg = d[3] + '.' + d[2] + '.' + d[1];
  const ck = RS_CLASS_KEYS.indexOf(m.classification) >= 0 ? m.classification : (Object.prototype.hasOwnProperty.call(RS_CLASS_OLD, m.classification) ? RS_CLASS_OLD[m.classification] : '');
  if (ck) want.class_ = t('classif.' + ck);
  let changed = false;
  [['msn', 'f-msn'], ['dtg', 'f-dtg'], ['class_', 'f-class']].forEach(([k, id]) => {{
    const el = document.getElementById(id);
    if (!want[k] || !el || el.value.trim() !== '') return;
    el.value = want[k];
    STATE.fields[k] = want[k];
    changed = true;
  }});
  if (changed) saveState();
  return changed;
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
  if (!file) return;
  if (!file.type.startsWith('image/')) {{ showToast(t('msg.notImage'), {{ type: 'err' }}); return; }}
  const reader = new FileReader();
  reader.onload = async e => {{
    const img = new Image();
    img.onload = () => {{
      SOURCE_IMG   = img;
      SOURCE_READY = true;
      document.getElementById('img-credit').hidden = true;     // le crédit n'est que celui de la photo de l'exemple
      document.getElementById('drop-zone').classList.add('has-image');
      document.getElementById('drop-zone-text').textContent =
        file.name + ' — ' + img.naturalWidth + '×' + img.naturalHeight + 'px';
      document.getElementById('btn-export').disabled = false;
      document.getElementById('preview-placeholder').hidden = true;
      document.getElementById('preview-canvas').hidden = false;
      if (STATE.exampleImage) {{ delete STATE.exampleImage; saveState(); }}     // une autre image que celle de l'exemple : l'état ne la porte plus
      showToast(t('toast.image-loaded'), {{ type: 'ok' }});
      rsdSyncUi();
      schedulePreview();
    }};
    img.onerror = () => {{ console.warn('[RS] image illisible'); showToast(t('msg.imageUnreadable'), {{ type: 'err' }}); }};
    img.src = e.target.result;
  }};
  reader.readAsDataURL(file);
}}

// ── Exemple : la photo ──
// L'exemple de la suite se charge par le shell (le fichier d'exemple du groupe Mission Commander) : la composition (repères, formes, loupe, bloc d'informations) est dans recon_state_v1, qui porte exampleImage: true.
// L'image est celle du dépôt (samples/rs_example_naip.jpg, USDA NAIP, domaine public) : elle n'est jamais enregistrée, l'état la nomme ; le schéma de recon_state_v1 ne change pas.
const RS_EXAMPLE_IMG = 'data:image/jpeg;base64,{RS_EXAMPLE_IMG_B64}';
// La photo de l'exemple dans la zone d'image, quand l'état porte exampleImage: true (au démarrage, à la relecture de l'état).
async function rsExampleImage() {{
  const img = new Image();
  try {{
    await new Promise((ok, ko) => {{ img.onload = ok; img.onerror = ko; img.src = RS_EXAMPLE_IMG; }});
  }} catch (e) {{ console.warn('[RS] exemple indisponible', e); showToast(t('msg.exampleUnavailable'), {{ type: 'err' }}); return false; }}
  if (!STATE.exampleImage || SOURCE_READY) return false;     // l'état a changé pendant le chargement : une autre image, ou plus d'image d'exemple
  SOURCE_IMG   = img;
  SOURCE_READY = true;
  document.getElementById('drop-zone').classList.add('has-image');
  document.getElementById('drop-zone-text').textContent = 'rs_example_naip.jpg — ' + img.naturalWidth + '×' + img.naturalHeight + 'px';
  document.getElementById('btn-export').disabled = false;
  document.getElementById('preview-placeholder').hidden = true;
  document.getElementById('preview-canvas').hidden = false;
  document.getElementById('img-credit').hidden = false;
  rsdSyncUi();
  schedulePreview();
  return true;
}}

function rsBack(m) {{
  STATE = structuredClone(m.state);
  SOURCE_IMG = m.img; SOURCE_READY = m.ready;
  const dz = document.getElementById('drop-zone');
  dz.classList.toggle('has-image', m.ready);
  document.getElementById('drop-zone-text').textContent = m.dz;
  document.getElementById('img-credit').hidden = !m.credit;
  document.getElementById('btn-export').disabled = !m.ready;
  document.getElementById('preview-placeholder').hidden = m.ready;
  document.getElementById('preview-canvas').hidden = !m.ready;
  applyStateToForm();
  renderLogoGrid(); renderLogoMode(); renderTextColor(); renderMarkerColor();
  renderCartoucheEditor(); renderInsetEditor(); renderShapesEditor(); renderLabelEditor();
  const ce = document.getElementById('classif-enable'), cl = document.getElementById('classif-level');
  if (ce) ce.checked = !!(STATE.classification && STATE.classification.enabled);
  if (cl) cl.value = (STATE.classification && STATE.classification.level) || 'unclassified';
  rsdSetTool('select');
  rsdDeselect();
  rsdSyncUi();
  saveState();
  schedulePreview();
}}
// Effacer : après confirmation, le contenu seul est vidé (l'image, les annotations, la légende et tous les champs du bloc d'informations) ; les logos importés au module,
// le contraste, les effets, le mode capteur, les couleurs et la classification du bandeau restent. La seule clé écrite est recon_state_v1 ; le thème, la langue et la configuration Wing ne bougent pas.
// Puis, comme au démarrage, les champs Msn, DTG et Class vides se remplissent du briefing en cours.
async function rsReset() {{
  if (!(await askConfirm({{ title: t('clear.title'), text: t('clear.text'), verb: t('clear.verb'), danger: true }}))) return;
  collectState();
  const st = structuredClone(STATE);
  st.fields = rsFreshState().fields;
  st.cartouche = [];
  st.annotations = [];
  delete st.exampleImage;
  rsBack({{ state: st, img: null, ready: false, dz: t('editor.image.drop'), credit: false }});
  rsBriefingFill();
  showToast(t('clear.toast'), {{ type: 'ok' }});
}}
// ── Logo loading ───────────────────────────────────────────────
const LOGO_MAX_SIZE = 512;   // côté long — préserve les exports haute résolution

function loadLogoFile(file) {{
  if (!file) return;
  if (!file.type.startsWith('image/')) {{ showToast(t('msg.notImage'), {{ type: 'err' }}); return; }}
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
    img.onerror = () => {{ console.warn('[RS] logo illisible'); showToast(t('msg.imageUnreadable'), {{ type: 'err' }}); }};
    img.src = e.target.result;
  }};
  reader.readAsDataURL(file);
}}

// ── Validation d'une config d'escadre : celle d'HQ (mêmes règles, mêmes textes) ───────────
function validateWingConfig(obj) {{
  const errors = [];
  if (!obj || typeof obj !== 'object') return {{ ok: false, errors: [t('validate.schemaMissing')] }};
  if (obj.configSchemaVersion !== 1) errors.push(t('validate.schemaMissing'));
  if (!obj.wing || typeof obj.wing !== 'object') {{
    errors.push(t('validate.wingMissing'));
  }} else {{
    if (!obj.wing.shortName) errors.push(t('validate.shortNameMissing'));
    if (!obj.wing.logo || !String(obj.wing.logo).startsWith('data:image/'))
      errors.push(t('validate.logoInvalid'));
  }}
  if (!Array.isArray(obj.squadrons)) {{
    errors.push(t('validate.squadronsNotArray'));
  }} else {{
    obj.squadrons.forEach((sq, i) => {{
      if (!sq.id)                      errors.push('squadrons[' + i + ']' + t('validate.sqIdMissing'));
      if (!sq.callsign)                errors.push('squadrons[' + i + ']' + t('validate.sqCallsignMissing'));
      if (!Array.isArray(sq.aircraft)) errors.push('squadrons[' + i + ']' + t('validate.sqAircraftNotArray'));
    }});
  }}
  return errors.length === 0 ? {{ ok: true }} : {{ ok: false, errors }};
}}

// ── Import config wing BG (G2) ────────────────────────────────
function importWingLogos(file) {{
  const r = new FileReader();
  r.onload = e => {{
    let cfg;
    try {{ cfg = JSON.parse(e.target.result); }}
    catch (err) {{ console.warn('[RS] configuration wing : JSON illisible', err); showToast(t('msg.jsonUnreadable'), {{ type: 'err' }}); return; }}
    if (!cfg || typeof cfg !== 'object' || cfg.configSchemaVersion !== 1) {{ showToast(t('msg.notWingConfig'), {{ type: 'err' }}); return; }}
    let check;
    try {{ check = validateWingConfig(cfg); }}
    catch (err) {{ console.warn('[RS] configuration wing : validation impossible', err); showToast(t('msg.notWingConfig'), {{ type: 'err' }}); return; }}
    if (!check.ok) {{
      console.warn('[RS] configuration wing incomplète :', check.errors);
      showToast(t('msg.wingIncomplete').replace('{{0}}', check.errors.length), {{ type: 'err' }});
      return;
    }}
    try {{
      const added = [];
      const push = (name, b64) => {{
        if (typeof b64 === 'string' && b64.startsWith('data:image/'))
          added.push({{ id: uid(), name: String(name || 'LOGO').slice(0, 24), b64 }});
      }};
      if (cfg.wing) push(cfg.wing.shortName || 'WING', cfg.wing.logo);
      (cfg.squadrons || []).forEach(sq => push(sq.id, sq.logo));
      if (!added.length) {{ showToast(t('toast.noLogoInJson'), {{ type: 'err' }}); return; }}
      STATE.logos.push(...added);
      STATE.logoId = added[0].id;
      saveState(); renderLogoGrid(); schedulePreview();
      showToast(t('toast.logosImported').replace('{{n}}', added.length), {{ type: 'ok' }});
    }} catch (err) {{
      console.warn('[RS] configuration wing : enregistrement ou rendu impossible', err);
      showToast(t('msg.failed'), {{ type: 'err' }});
    }}
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
      return `<div class="logo-thumb ${{active}}" data-logo-id="none" tabindex="0" title="${{t('editor.logo.none')}}">
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

  const valFont = px => `400 ${{px}}px "Gunplay","Roboto Mono",monospace`;
  // Une valeur plus large que la place qui lui reste rétrécit d'abord (jusqu'à 75 % de baseFont), puis se coupe et finit par « … » ;
  // laisse ctx.font à la taille choisie et rend le texte à dessiner, sa largeur et sa taille de police
  function fitValue(value, avail) {{
    ctx.font = valFont(baseFont);
    let val = String(value == null ? '' : value), vw = ctx.measureText(val).width;
    if (vw > avail) {{
      const minFont = baseFont * 0.75;
      let fs = Math.max(minFont, baseFont * avail / vw);
      ctx.font = valFont(fs);
      vw = ctx.measureText(val).width;
      while (vw > avail && fs > minFont) {{ fs = Math.max(minFont, fs - baseFont * 0.01); ctx.font = valFont(fs); vw = ctx.measureText(val).width; }}
      if (vw > avail) {{
        let n = val.length;
        while (n > 0 && ctx.measureText(val.slice(0, n).trimEnd() + '…').width > avail) n--;
        val = val.slice(0, n).trimEnd() + '…';
        vw = ctx.measureText(val).width;
      }}
    }}
    return {{ val: val, w: vw, font: parseFloat(ctx.font.match(/([0-9.]+)px/)[1]) }};
  }}

  // Largeur des champs de valeur (avec filet de soulignement) ; maxX : où commence ce qui suit sur la ligne (libellé suivant, ou bord droit du bloc) :
  // la valeur ne dépasse jamais maxX moins s(10), le filet garde sa longueur fieldW
  function drawField(label, value, x, y, fieldW, maxX, preFit) {{
    // Label gras
    ctx.font = `400 ${{boldFont}}px "Gunplay","Roboto Mono",monospace`;
    ctx.fillStyle = TXT;
    ctx.textBaseline = 'alphabetic';
    const lw = ctx.measureText(label).width;
    ctx.fillText(label, x, y);

    // Valeur gras (E2)
    ctx.fillStyle = TXT;
    const valX = x + lw;
    const avail = Math.max(s(10), (maxX == null ? valX + fieldW + s(10) : maxX) - valX - s(10));
    const fit = preFit || fitValue(value, avail);
    ctx.font = valFont(fit.font);
    ctx.fillText(fit.val, valX, y);

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
  const rightX = blockX + blockW;       // bord droit du bloc : la place du dernier champ d'une ligne
  drawField('Target : ', f.target, lx, y1, s(280), colMid);
  drawField('Coords: ', f.coords, colMid, y1, s(320), rightX);

  // L2 : Crs · Alt · Msn · Sensor
  const y2 = y1 + lineH;
  drawField('Crs: ', f.crs, lx, y2, s(70), lx + s(180));
  drawField('Alt: ', f.alt, lx + s(180), y2, s(90), lx + s(380));
  drawField('Msn: ', f.msn, lx + s(380), y2, s(220), colMid + s(60));
  drawField('Sensor : ', f.sensor, colMid + s(60), y2, s(220), rightX);

  // L3 : DTG · Crew
  const y3 = y2 + lineH;
  drawField('DTG : ', f.dtg, lx, y3, s(320), colMid);
  drawField('Crew: ', f.crew, colMid, y3, s(280), rightX);

  // L4 : Class centré
  const y4 = y3 + lineH;
  const classLabel = 'Class: ';
  ctx.font = `400 ${{boldFont}}px "Gunplay","Roboto Mono",monospace`;
  const classLabelW = ctx.measureText(classLabel).width;
  // la ligne se centre sur la valeur réellement dessinée (après réduction et coupe) et reste dans le bloc : la place de la valeur est celle du bloc moins le libellé et l'écart de s(80)
  const classFit = fitValue(f.class_, Math.max(s(10), blockW - classLabelW - s(80)));
  const totalClassW = classLabelW + classFit.w + s(80);
  const classX = blockX + (blockW - totalClassW) / 2;
  drawField('Class: ', f.class_, classX, y4, s(200), classX + totalClassW, classFit);

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
  ctx.font = `400 ${{hdrFont}}px "Gunplay","Roboto Mono",monospace`;
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
      ctx.font = `400 ${{fsize}}px "Roboto Mono",monospace`;
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
      'unclassified':    '#007a33',
      'confidential':    '#003087',
      'secret':          '#c8102e',
      'top-secret':      '#ff8200',
      'nato-restricted': '#003087',
      'nato-secret':     '#c8102e'
    }};
    const levelKey = rsClassKey(st.classification.level);
    const level = t('classif.' + levelKey);
    const barColor = CLASSIF_COLORS[levelKey] || '#007a33';
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
    ctx.font = `400 ${{cfsize}}px "Roboto Mono",monospace`;
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
    ctx.font = `400 ${{s(30)}}px "Gunplay","Roboto Mono",monospace`;
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
  rsdRefresh();     // les poignées (DOM) suivent ce qui vient d'être dessiné
}}

// ── Overlays d'édition (croix des cibles) ──────────────────────
// Aperçu uniquement — jamais inclus dans composeRecon (non exportés).
// Les poignées des annotations ne sont plus dessinées ici : ce sont des éléments DOM (voir « Annoter au doigt »).
function drawEditOverlays(ctx, W, H) {{
  const scale = W / 1920;
  const s = v => Math.round(v * scale);

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

// ── Nom du fichier : la fenêtre d'« Exporter PNG » ──────────────
function str(v) {{
  if (typeof v === 'string') return v;
  if (typeof v === 'number' && isFinite(v)) return String(v);
  return '';
}}
/* Le nom d'un fichier choisi : sans « .json », accents ôtés, tout ce qui n'est pas lettre, chiffre, _ + - devient « _ » ; vide si rien ne reste */
function cleanFname(v) {{
  return str(v).trim().replace(/\\.json$/i, '').normalize('NFD').replace(/[\\u0300-\\u036f]/g, '').replace(/[^A-Za-z0-9_+-]+/g, '_').replace(/_{{2,}}/g, '_').replace(/^_+|_+$/g, '').slice(0, 100);
}}
/* L'horodatage unique des noms par défaut : AAAAMMJJ-HHMMSS, heure locale */
function fnStamp() {{
  const d = new Date(), p = n => String(n).padStart(2, '0');
  return d.getFullYear() + p(d.getMonth() + 1) + p(d.getDate()) + '-' + p(d.getHours()) + p(d.getMinutes()) + p(d.getSeconds());
}}
const FN = {{ name: '', opener: null, at: 0 }};
function fnOpen() {{ return !document.getElementById('fn-modal').hidden; }}
function fnSync() {{ document.getElementById('fn-go').disabled = cleanFname(FN.name) === ''; }}
function fnAsk(opener) {{
  if (!SOURCE_READY || !SOURCE_IMG) {{
    showToast(t('toast.no-image'), {{ type: 'err' }});
    return;
  }}
  collectState();
  const slug = (STATE.fields.target || '').replace(/[^a-zA-Z0-9-]/g, '_').replace(/_+/g, '_').slice(0, 40);
  FN.name = cleanFname((slug ? 'recon_' + slug : 'recon') + '_' + fnStamp());
  FN.opener = opener || document.activeElement;
  FN.at = performance.now();
  const inp = document.getElementById('fn-name');
  inp.value = FN.name;
  fnSync();
  document.getElementById('fn-modal').hidden = false;
  inp.focus({{ preventScroll: true }});
  inp.select();
}}
function fnClose() {{
  document.getElementById('fn-modal').hidden = true;
  const o = FN.opener;
  FN.opener = null;
  if (o && o.focus && !o.disabled) {{ try {{ o.focus({{ preventScroll: true }}); }} catch (e) {{}} }}
}}
function fnGo() {{
  const name = cleanFname(FN.name);
  if (name === '') return;
  fnClose();
  exportPNG(name);
}}
function fnBind() {{
  ['fn-close', 'fn-cancel'].forEach(id => document.getElementById(id).addEventListener('click', fnClose));
  /* le fond ignore les clics des 400 ms qui suivent l'ouverture : le 2e clic d'un double-clic sur « Exporter PNG » ne ferme pas la fenêtre */
  document.getElementById('fn-backdrop').addEventListener('click', () => {{ if (performance.now() - FN.at > 400) fnClose(); }});
  document.getElementById('fn-go').addEventListener('click', fnGo);
  const inp = document.getElementById('fn-name');
  inp.addEventListener('input', e => {{ FN.name = e.target.value; fnSync(); }});
  inp.addEventListener('keydown', e => {{ if (e.key === 'Enter') {{ e.preventDefault(); if (!e.repeat) fnGo(); }} }});
  /* en phase de capture : l'Échap de la fenêtre ne doit pas aussi défaire une annotation en cours */
  document.addEventListener('keydown', e => {{
    if (!fnOpen()) return;
    if (e.key === 'Escape') {{ e.preventDefault(); e.stopImmediatePropagation(); fnClose(); return; }}
  }}, true);
}}

// ── Export PNG ─────────────────────────────────────────────────
async function exportPNG(name) {{
  if (!SOURCE_READY || !SOURCE_IMG) {{
    showToast(t('toast.no-image'), {{ type: 'err' }});
    return;
  }}
  showToast(t('toast.export.start'), 1500);
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
    if (!blob) {{ showToast(t('msg.exportFailed'), {{ type: 'err' }}); return; }}
    const fname   = name + '.png';
    const url     = URL.createObjectURL(blob);
    const a       = document.createElement('a');
    a.href        = url;
    a.download    = fname;
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 5000);
    showToast(t('toast.export.done'), {{ type: 'ok' }});
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

  // Exemple
  document.getElementById('btn-example').addEventListener('click', workExample);
  document.getElementById('btn-reset').addEventListener('click', rsReset);

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

  document.getElementById('btn-export').addEventListener('click', e => fnAsk(e.currentTarget));
  fnBind();

  // Tabs (mobile)
  document.querySelectorAll('.tab-btn').forEach(btn => {{
    btn.addEventListener('click', () => {{
      const tab = btn.dataset.tab;
      document.getElementById('app').dataset.activeTab = tab;
      requestAnimationFrame(() => {{ rsdPlace(); rsdPlaceSheet(); }});     // au retour sur l'aperçu, les poignées se replacent
      document.querySelectorAll('.tab-btn').forEach(b => {{
        b.classList.toggle('active', b.dataset.tab === tab);
        b.setAttribute('aria-selected', b.dataset.tab === tab ? 'true' : 'false');
      }});
    }});
  }});

  // Le glisser des repères et des cibles, le toucher qui crée ou qui choisit : voir rsdInitCanvas() (« Annoter au doigt »)
}}

{RSD_JS}
{RS_MENU_JS}

@@TBM_JS@@

// ── Init ───────────────────────────────────────────────────────
// ── Repli des sections (rs_folds_v1) ─────────────────────────────
// {{ section: true (ouverte) | false (repliée) }} ; profil neuf : Image source, Rendu, Formes ouvertes, les sept autres repliées ; une clé « export » d'un ancien rs_folds_v1 n'est plus lue.
const RS_FOLDS = 'rs_folds_v1';
const RS_FOLD_DEF = {{ image: true, render: true, text: false, fx: false, info: false, logo: false, cartouche: false, shapes: true, marker: false, classif: false }};
function rsSections() {{ return Array.prototype.slice.call(document.querySelectorAll('#editor-panel > details.ed-section')); }}
/* La ligne de résumé d'une section repliée ; rien si elle est vide (Image source, Rendu et Formes n'en portent pas) */
function rsSectionSum(id) {{
  const v = x => (typeof x === 'string' ? x.trim() : '');
  if (id === 'text') return t(STATE.textColor === '#000' ? 'editor.text.black' : 'editor.text.white');
  if (id === 'marker') return t('editor.marker.' + (['red', 'black', 'white'].indexOf(STATE.markerColor) >= 0 ? STATE.markerColor : 'red'));
  if (id === 'fx') {{
    const sk = {{ 'ir-white': 'irw', 'ir-black': 'irb', sar: 'sar' }}[STATE.sensorMode];
    return uiJoin([sk ? t('editor.fx.sensor.' + sk) : '', STATE.fxVignette > 0 ? t('editor.fx.vignette') + ' ' + STATE.fxVignette : '', STATE.fxGrain > 0 ? t('editor.fx.grain') + ' ' + STATE.fxGrain : '', STATE.fxScanlines > 0 ? t('editor.fx.scanlines') + ' ' + STATE.fxScanlines : '']);
  }}
  if (id === 'info') return v(STATE.fields.target);
  if (id === 'logo') {{ const lg = STATE.logos.find(l => l.id === STATE.logoId); return STATE.logoId !== 'none' && lg ? (v(lg.name) || t('sum.none')) : t('sum.none'); }}
  if (id === 'cartouche') {{ const c = (STATE.cartouche || []).find(x => x && v(x.label)); return c ? v(c.label) : ''; }}
  if (id === 'classif') return STATE.classification && STATE.classification.enabled ? t('classif.' + rsClassKey(STATE.classification.level)) : '';
  return '';
}}
function rsFoldLabel() {{
  const b = document.getElementById('rs-foldall');
  if (b) b.textContent = uiFoldAllLabel(rsSections().some(d => d.open));
}}
function rsFoldRefresh() {{
  rsSections().forEach(d => {{
    const h = d.querySelector(':scope > summary');
    h.setAttribute('aria-expanded', String(d.open));
    uiSum(h, d.open ? '' : rsSectionSum(d.dataset.section));
  }});
  rsFoldLabel();
}}
function rsFoldInit() {{
  rsSections().forEach(d => {{
    const id = d.dataset.section, o = uiFoldOpen(RS_FOLDS, id, RS_FOLD_DEF[id]);
    d.dataset.fold = String(o);
    if (d.open !== o) d.open = o;
  }});
  rsFoldRefresh();
  document.getElementById('editor-panel').addEventListener('toggle', e => {{
    const d = e.target;
    if (!d || !d.matches || !d.matches('details.ed-section')) return;
    if (d.dataset.fold !== String(d.open)) uiFoldSave(RS_FOLDS, d.dataset.section, d.open);
    d.dataset.fold = String(d.open);
    const h = d.querySelector(':scope > summary');
    h.setAttribute('aria-expanded', String(d.open));
    uiSum(h, d.open ? '' : rsSectionSum(d.dataset.section));
    rsFoldLabel();
  }}, true);
  document.getElementById('rs-foldall').addEventListener('click', () => {{
    const ds = rsSections(), open = !ds.some(d => d.open), map = {{}};
    ds.forEach(d => {{ map[d.dataset.section] = open; }});
    uiFoldSaveAll(RS_FOLDS, map);
    ds.forEach(d => {{ if (d.open !== open) d.open = open; }});
    rsFoldLabel();
  }});
}}

async function init() {{
  loadTheme();
  loadLang();
  TBM.cfg = {{ others: () => mnClose(false), trig: MENU_TRIG }};       // ce que ce module ajoute à la liste commune : le menu « Ouvrir » se ferme avec elle
  initToolbarMenus([['theme-select', () => t('toolbar.theme.tooltip')]]);   // les listes de la barre au thème de l'interface
  mnBind();   // le menu « Ouvrir », « Sauvegarder » et Ctrl+S
  initFormMenus(sel => {{ const l = sel.parentElement && sel.parentElement.querySelector('.ed-label'); return l ? l.textContent.trim() : ''; }});   // les listes des formulaires

  const hasState = restoreState();
  applyStateToForm();
  rsBriefingFill();
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
  rsdInit();
  rsFoldInit();

  if (hasState) {{
    showToast(t('toast.state-restored'), 3500);
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

HTML = HTML.replace('<body data-theme="cw-nato">\n', '<body data-theme="cw-nato">\n' + SHELL_ONLY_TAG, 1)
HTML = HTML.replace('@@MESSAGES_CSS@@\n', build_messages_css() + build_ui_css()).replace('@@MESSAGES_BLOCK@@\n', build_messages_block() + build_ui_block()).replace('@@TBM_CSS@@\n', build_tbm_css()).replace('@@TBM_JS@@\n', build_tbm_block())
ui_verify(HTML)
ui_verify_bar(HTML)

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
grep_present("STATE.classification", "STATE.classification présent")
grep_present("classif-enable", "toggle classif présent")
grep_present("classif-level", "select niveau classif présent")
grep_present("UNCLASSIFIED", "niveau UNCLASSIFIED présent")
grep_present("SECRET", "niveau SECRET présent")
grep_present("barH = bannerH", "bandeau réutilise bannerH")
grep_present("bannerH", "bannerH défini (correction A)")
grep_present("blockY = H - blockH - s(12) - bannerH", "blockY réserve bannerH")
grep_present("cartY  = cartMg + bannerH", "cartY réserve bannerH")
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
grep_present("rsdInitCanvas", "annoter au doigt : le canevas (toucher, repères)")
grep_present("rsdRectHandles", "annoter au doigt : poignées du cadre")
grep_present("rsdInsetHandles", "annoter au doigt : poignées de la loupe")
grep_present("rsdPlaceSheet", "annoter au doigt : fiche « à venir » posée d'après le message")
grep_present("font-family: 'Oswald';\n  font-weight: 700;", "Oswald 700 embarquée (face du Route Planner)")
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
# Revue : une valeur du bloc d'informations s'arrête avant ce qui la suit, la ligne Class se centre sur la valeur dessinée
grep_present("function fitValue(value, avail)", "bloc d'informations : la place d'une valeur se mesure (fitValue)")
grep_present("- valX - s(10))", "bloc d'informations : la valeur s'arrête s(10) avant le libellé suivant")
grep_present("const totalClassW = classLabelW + classFit.w + s(80)", "bloc d'informations : Class se centre sur la valeur dessinée")

print("\n[BUILD DONE]")
