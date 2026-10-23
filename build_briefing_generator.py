#!/usr/bin/env python3
"""Build unifié — DCS Briefing Generator v2.2.0.
Produit dist/dcs_briefing_generator.html (fusion build_css.py + build_html.py).
Usage : python3 build_briefing_generator.py
"""
"""Build the v2 KHR-26 Cold War briefing generator with tablet support."""

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))

ASSETS_PATH = os.path.join(HERE, 'assets.json')
if not os.path.isfile(ASSETS_PATH):
    raise SystemExit(f"[ERREUR] Entrée manquante : {ASSETS_PATH} (assets.json attendu à la racine du dépôt)")
with open(ASSETS_PATH) as f:
    A = json.load(f)

CSS = r"""
/* ============================================
   COLD WAR BRIEFING GENERATOR v2 — KHR-26
   Tablet-ready, fonts embedded, offline-first
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
  font-family: 'Special Elite';
  font-weight: 400;
  font-display: swap;
  src: url('data:font/woff2;base64,__SPECIAL_ELITE__') format('woff2');
}
@font-face {
  /* Phase X — étape C : Roboto Mono Regular pour les 2 thèmes modernes
     (subset latin, ~12 KB). Glyphes manquants du subset (░ ▮ ★ etc.)
     resolvent via fallback sur 'Courier New' / 'Courier' / monospace. */
  font-family: 'Roboto Mono';
  font-weight: 400;
  font-display: swap;
  src: url('data:font/woff2;base64,__ROBOTO_MONO_400__') format('woff2');
}
@font-face {
  /* Partie B (2c) — Chrome éditeur : Oswald Medium latin subset (~13 Ko woff2).
     Rendu homogène PC ↔ tablette. Depuis v2.4.1, Oswald 600 et 700 sont embarquées
     aussi : le chrome éditeur et les pages (--f-condensed) n'ont plus de faux gras. */
  font-family: 'Oswald';
  font-weight: 500;
  font-display: swap;
  src: url('data:font/woff2;base64,__OSWALD_500__') format('woff2');
}
@font-face {
  font-family: 'Oswald';
  font-weight: 600;
  font-display: swap;
  src: url('data:font/woff2;base64,__OSWALD_600__') format('woff2');
}
@font-face {
  font-family: 'Oswald';
  font-weight: 700;
  font-display: swap;
  src: url('data:font/woff2;base64,__OSWALD_700__') format('woff2');
}

:root {
  /* Typography stack — partagée par tous les thèmes (la phase X — étape C
     redéfinira --f-typewriter sur les thèmes modernes). */
  --f-stencil: 'Stardos Stencil', 'Impact', 'Arial Narrow Bold', sans-serif;
  --f-typewriter: 'Special Elite', 'Courier New', 'Courier', monospace;
  --f-condensed: 'Oswald', 'Arial Narrow', sans-serif;
  --f-ui: 'Oswald', 'Arial Narrow', sans-serif; /* Chrome éditeur — 2c */
  --f-mono: ui-monospace, 'SF Mono', 'Menlo', 'Consolas', monospace;

  /* Variables sémantiques constantes sur tous les thèmes
     (cf. phase X § 1.5 et Q1/Q2 de validation utilisateur). */
  --amber:        #c0892a;  /* accent UI : onglets actifs, branding, warn */
  --amber-dark:   #8a5e15;
  --green-radar:  #4f6b3a;  /* threat chips et accents tactiques sémantiques */
}

/* ============================================
   THÈMES — phase X
   Bascule via <body data-theme="..."> :
     cw-nato (défaut) | cw-soviet | modern-nato | modern-east
   Le JS de l'étape E posera l'attribut au démarrage via loadTheme().
   ============================================ */

/* --- Thème : Cold War OTAN (défaut, valeurs originales préservées) --- */
body[data-theme="cw-nato"] {
  --paper:        #d8c9a5;
  --paper-light:  #e3d6b5;
  --paper-dark:   #b8a77c;
  --paper-edge:   #8a7a52;
  --page-bg:      #d6c7a3;  /* fond .page sous la texture kraft */
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
  --kraft-bg: url('data:image/svg+xml;base64,__KRAFT_SVG_NATO__');
}

/* --- Thème : Cold War Soviétique --- */
body[data-theme="cw-soviet"] {
  --paper:        #d8c479;  /* ocre chaud */
  --paper-light:  #e8d690;
  --paper-dark:   #b8a64a;
  --paper-edge:   #8a7a30;
  --page-bg:      #d4c075;
  --ink:          #1f1c16;
  --ink-faded:    #463f30;
  --olive:        #2a3a5a;  /* bleu nuit (accent secondaire) */
  --olive-dark:   #1a2540;
  --olive-deep:   #0e1830;
  --khaki:        #3a4a2e;  /* vert armée russe (accent principal) */
  --khaki-light:  #5a6a48;
  --rust:         #5e1414;
  --red-stamp:    #841e1e;  /* rouge bordeaux */
  --red-faded:    #a04040;
  --kraft-bg: url('data:image/svg+xml;base64,__KRAFT_SVG_SOVIET__');
}

/* --- Thème : OTAN moderne --- */
body[data-theme="modern-nato"] {
  --paper:        #e8e3d8;  /* blanc cassé */
  --paper-light:  #f0ece2;
  --paper-dark:   #c8c0b0;
  --paper-edge:   #948c7c;
  --page-bg:      #e4dfd2;
  --ink:          #15181c;  /* gris-bleu froid */
  --ink-faded:    #3a4048;
  --olive:        #2a3038;  /* anthracite (accent secondaire) */
  --olive-dark:   #1c2026;
  --olive-deep:   #0e1014;
  --khaki:        #5c6b7a;  /* gris-bleu militaire (accent principal) */
  --khaki-light:  #7a8a98;
  --rust:         #2a2a2a;  /* moderne : pas de rouge, neutre */
  --red-stamp:    #1a1a1a;  /* tampons noirs */
  --red-faded:    #4a4a4a;
  --kraft-bg: url('data:image/svg+xml;base64,__KRAFT_SVG_MODERN_NATO__');
}

/* --- Thème : Bloc Est moderne --- */
body[data-theme="modern-east"] {
  --paper:        #cdc6b8;  /* papier grisé */
  --paper-light:  #ddd6c8;
  --paper-dark:   #ada69a;
  --paper-edge:   #7a7466;
  --page-bg:      #c8c1b2;
  --ink:          #1a1610;  /* brun chaud */
  --ink-faded:    #3d3024;
  --olive:        #3d3024;  /* brun terre (accent secondaire) */
  --olive-dark:   #2a2018;
  --olive-deep:   #1a140e;
  --khaki:        #4a5238;  /* vert digital (accent principal) */
  --khaki-light:  #6a7256;
  --rust:         #5a1a1a;
  --red-stamp:    #7a2424;  /* rouge sombre */
  --red-faded:    #a04040;
  --kraft-bg: url('data:image/svg+xml;base64,__KRAFT_SVG_MODERN_EAST__');
}

/* Phase X — étape C : police de corps des thèmes modernes
   Roboto Mono remplace Special Elite (typewriter) sur les 2 thèmes modernes
   pour un rendu technique/digital. La stack de fallback couvre les glyphes
   absents du subset latin (░ ▮ ★ etc. → fallback sur Courier/monospace). */
body[data-theme="modern-nato"],
body[data-theme="modern-east"] {
  --f-typewriter: 'Roboto Mono', 'Courier New', 'Courier', monospace;
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

/* v2.3.1 — barre du haut défilante : elle défile dès qu'elle déborde, un fondu signale le bord qui cache du contenu */
.toolbar {
  --fade-w: 22px;
  --fade-gap: 8px;
  overflow-x: auto;
  overflow-y: hidden;
  flex-wrap: nowrap;
  scrollbar-width: none;
  -webkit-overflow-scrolling: touch;
  overscroll-behavior-x: contain;
  touch-action: pan-x;
}
.toolbar::-webkit-scrollbar { display: none; }
.toolbar::before, .toolbar::after {
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
.toolbar::before {
  left: 0;
  margin-right: calc(-1 * (var(--fade-w) + var(--fade-gap)));
  background: linear-gradient(90deg, rgba(0,0,0,.55), transparent);
}
.toolbar::after {
  right: 0;
  margin-left: calc(-1 * (var(--fade-w) + var(--fade-gap)));
  background: linear-gradient(270deg, rgba(0,0,0,.55), transparent);
}
.toolbar.fade-l::before, .toolbar.fade-r::after { opacity: 1; }

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
}
.tb-btn:hover, .tb-btn:focus-visible {
  background: var(--olive);
  border-color: var(--amber);
  color: var(--amber);
  outline: none;
}
.tb-btn:active { transform: translateY(1px); }
.tb-btn.active {
  background: var(--amber-dark);
  border-color: var(--amber);
  color: var(--paper-light);
}
.tb-btn.danger:hover {
  background: var(--rust);
  border-color: var(--red-faded);
  color: var(--paper-light);
}
.tb-btn svg { width: 16px; height: 16px; flex-shrink: 0; }

/* Phase X — étape E : sélecteur de thème graphique
   Utilise --olive-dark (thématisé) en background pour suivre l'identité
   visuelle de chaque thème, et --amber/--amber-dark (constants) en accent UI.
   Caret custom SVG inline (couleur amber #c0892a, hard-coded car les data:url
   ne supportent pas les variables CSS — mais l'amber étant constant, c'est
   cohérent avec tous les thèmes). */
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
.tb-select:active { transform: translateY(1px); }
/* Le menu déroulant natif est rendu par l'OS — on force au moins un fond
   lisible et une couleur de texte exploitable sur tous les systèmes. */
.tb-select option {
  background-color: var(--olive-dark);
  color: var(--paper);
}

.tb-spacer { flex: 1; }

.tb-classif {
  font-family: var(--f-stencil);
  font-size: 11px;
  letter-spacing: 3px;
  color: var(--red-faded);
  border: 1px solid var(--red-faded);
  padding: 4px 10px;
  white-space: nowrap;
}

.tb-version {
  font-size: 11px;
  opacity: 0.5;
  color: var(--amber);
  letter-spacing: 0.5px;
  align-self: center;
  margin-left: 8px;
  user-select: none;
}

/* i18n — bouton drapeau langue (Phase 9 — v2.2.0)
   Bouton bascule FR↔EN, positionné entre le sélecteur de thème et le spacer.
   Affiche le drapeau de la langue CIBLE (celle vers laquelle on bascule). */
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
}
.tb-lang-btn:hover, .tb-lang-btn:focus-visible {
  background: var(--olive);
  border-color: var(--amber);
  outline: none;
}
.tb-lang-btn:active { transform: translateY(1px); }

/* Brief complet / simplifié — sélecteur à deux positions (v2.3.0) */
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
  padding: 0 12px;
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
  color: var(--paper-light);
  box-shadow: inset 0 -3px 0 var(--amber);
}
.tb-seg .seg-short { display: none; }
@media (max-width: 1500px) {
  .tb-seg .seg-long { display: none; }
  .tb-seg .seg-short { display: inline; }
}

/* ============ MAIN APP ============ */
.app {
  position: fixed;
  top: 56px; bottom: 0; left: 0; right: 0;
  display: grid;
  grid-template-columns: 460px 1fr;
  background: var(--olive-deep);
}

/* ============ EDITOR ============ */
.editor {
  background:
    repeating-linear-gradient(
      0deg,
      transparent 0,
      transparent 2px,
      rgba(0,0,0,.04) 2px,
      rgba(0,0,0,.04) 3px
    ),
    linear-gradient(180deg, var(--olive-dark) 0%, var(--olive-deep) 100%);
  border-right: 2px solid var(--amber-dark);
  overflow-y: auto;
  overscroll-behavior: contain;   /* AJOUT chatG : isolation du scroll, prévention reflows en cascade */
  padding: 16px 16px 80px 16px;
  color: var(--paper);
}

.editor::-webkit-scrollbar { width: 10px; }
.editor::-webkit-scrollbar-track { background: var(--olive-deep); }
.editor::-webkit-scrollbar-thumb { background: var(--khaki); border: 2px solid var(--olive-deep); }

/* SECTIONS */
.ed-section {
  contain: layout;   /* AJOUT chatG : isolation layout, prévention reflows globaux sur input */
  margin-bottom: 14px;
  border: 1px solid var(--khaki);
  background: rgba(20, 24, 12, .5);
}

.ed-section > summary, .ed-section > .panel-header {
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
  content: '◄';
  font-size: 10px;
  color: var(--paper);
  transition: transform .2s;
}
.ed-section[open] > summary::after {
  transform: rotate(-90deg);
}
.ed-section > summary:hover { color: var(--paper-light); }

/* Panneau assistant METAR — découplé du tab-system (correctif 2) */
.metar-panel {
  contain: layout;
  margin-bottom: 14px;
  border: 1px solid var(--khaki);
  background: rgba(20, 24, 12, .5);
}
.metar-panel > summary {
  cursor: pointer;
  padding: 12px 14px;
  background: linear-gradient(90deg, var(--olive) 0%, var(--olive-dark) 100%);
  font-family: var(--f-stencil);
  font-size: 13px;
  letter-spacing: 2px;
  color: var(--amber);
  list-style: none;
  display: flex; align-items: center;
  border-bottom: 1px solid var(--amber-dark);
  user-select: none;
  min-height: 48px;
}
.metar-panel > summary::-webkit-details-marker { display: none; }
.metar-panel > summary:hover { color: var(--paper-light); }
.metar-panel > .ed-content { padding: 14px; }

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
.ed-field label::before {
  content: '►';
  color: var(--rust);
  font-size: 8px;
}

.ed-field input[type=text],
.ed-field input[type=date],
.ed-field input[type=number],
.ed-field textarea,
.ed-field select {
  background: rgba(216, 201, 165, .92);
  border: 1px solid var(--khaki);
  border-left: 3px solid var(--amber-dark);
  font-family: var(--f-typewriter);
  font-size: 13px;
  color: var(--ink);
  padding: 10px 11px;
  min-height: 44px;
  transition: all .15s;
  resize: vertical;
  width: 100%;
}
.ed-field input:focus,
.ed-field textarea:focus,
.ed-field select:focus {
  outline: none;
  border-left-color: var(--red-stamp);
  background: var(--paper-light);
  box-shadow: 0 0 0 1px var(--amber);
}
.ed-field textarea { min-height: 70px; line-height: 1.4; }

.ed-field-row { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }

/* DYNAMIC LISTS */
.ed-list { display: flex; flex-direction: column; gap: 8px; }
.ed-list-item { display: flex; gap: 8px; }
.ed-list-item input,
.ed-list-item textarea { flex: 1; }

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
.ed-btn-icon:active { transform: translateY(1px); }

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
.ed-btn-add:active { transform: translateY(1px); }

/* IMAGE UPLOAD */
.ed-img-zone {
  border: 1px dashed var(--khaki);
  background: rgba(0,0,0,.2);
  padding: 14px;
  text-align: center;
  cursor: pointer;
  font-family: var(--f-ui);
  font-weight: 600;
  font-size: 11px;
  color: var(--khaki-light);
  text-transform: uppercase;
  letter-spacing: 1.5px;
  transition: all .15s;
  position: relative;
  min-height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.ed-img-zone:hover, .ed-img-zone:focus-within {
  border-color: var(--amber);
  color: var(--amber);
}
.ed-img-zone.has-img {
  border-style: solid;
  border-color: var(--green-radar);
  color: var(--paper);
  padding: 0;
  min-height: 0;
}
.ed-img-zone.has-img img {
  width: 100%;
  height: auto;
  display: block;
  max-height: 280px;
  object-fit: contain;
  background: rgba(0,0,0,.15);
}
.ed-img-zone .img-rm {
  position: absolute;
  top: 6px; right: 6px;
  background: var(--rust);
  color: var(--paper-light);
  border: 1px solid var(--red-faded);
  width: 32px; height: 32px;
  cursor: pointer;
  font-weight: 700;
  display: flex; align-items: center; justify-content: center;
  font-family: var(--f-ui);
  font-size: 18px;
  line-height: 1;
  padding: 0;
}
.ed-img-zone .img-info {
  position: absolute;
  bottom: 6px; left: 6px;
  background: rgba(0,0,0,.7);
  color: var(--paper);
  font-family: var(--f-mono);
  font-size: 9px;
  letter-spacing: 1px;
  padding: 2px 6px;
}
.ed-img-zone input[type=file] { display: none; }

/* PHASE SELECTOR */
.phase-bar {
  display: grid;
  grid-template-columns: 44px 1fr 44px 44px 44px 44px;
  gap: 6px;
  padding: 10px;
  background: rgba(192, 137, 42, .12);
  border: 1px solid var(--amber-dark);
  margin-bottom: 14px;
  align-items: center;
}
.phase-bar button {
  height: 44px;
  background: var(--olive);
  border: 1px solid var(--khaki);
  color: var(--paper);
  font-family: var(--f-ui);
  font-weight: 700;
  font-size: 16px;
  cursor: pointer;
  transition: all .15s;
  display: flex;
  align-items: center;
  justify-content: center;
}
.phase-bar button:hover:not(:disabled) {
  background: var(--amber-dark);
  border-color: var(--amber);
}
.phase-bar button:active:not(:disabled) { transform: translateY(1px); }
.phase-bar button:disabled {
  opacity: .35;
  cursor: not-allowed;
}
.phase-bar button.danger { color: var(--red-faded); }
.phase-bar button.danger:hover:not(:disabled) {
  background: var(--rust);
  color: var(--paper-light);
  border-color: var(--red-faded);
}
.phase-indicator {
  text-align: center;
  font-family: var(--f-stencil);
  letter-spacing: 2px;
  color: var(--amber);
  font-size: 13px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.phase-indicator strong {
  color: var(--paper-light);
  font-size: 16px;
  font-weight: 700;
}

.phase-empty {
  padding: 30px 14px;
  text-align: center;
  color: var(--khaki-light);
  font-family: var(--f-typewriter);
  font-style: italic;
  border: 1px dashed var(--khaki);
}

/* Phase / comm-plan editor card (used inside list editors) */
.ed-phase-card {
  border: 1px solid var(--khaki);
  background: rgba(0,0,0,.2);
  padding: 14px 12px 12px 12px;
  margin-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  position: relative;
}
.ed-phase-card .phase-num {
  position: absolute;
  top: -10px; left: 12px;
  background: var(--amber-dark);
  color: var(--paper);
  font-family: var(--f-stencil);
  font-size: 11px;
  letter-spacing: 1px;
  padding: 2px 8px;
  border: 1px solid var(--amber);
}
.ed-phase-card .phase-rm {
  position: absolute;
  top: -10px; right: 8px;
  background: var(--rust);
  color: var(--paper-light);
  border: 1px solid var(--red-faded);
  cursor: pointer;
  padding: 2px 10px;
  font-family: var(--f-ui);
  font-weight: 700;
  font-size: 11px;
  letter-spacing: 1px;
  text-transform: uppercase;
  height: 22px;
  min-width: 60px;
}
.ed-phase-card .phase-rm:hover { background: var(--red-stamp); }

.ed-help {
  font-family: var(--f-typewriter);
  font-size: 11px;
  color: var(--khaki-light);
  font-style: italic;
  padding: 6px 0;
  border-top: 1px dotted var(--khaki);
  margin-top: 4px;
}

/* ============ WING EDITOR (Phase 4) ============ */
.wing-fieldset {
  border: 1px solid var(--khaki);
  border-radius: 4px;
  padding: 12px;
  margin: 0 0 14px 0;
}
.wing-legend {
  font-family: var(--f-stencil);
  font-size: 11px;
  letter-spacing: .08em;
  color: var(--khaki-light);
  padding: 0 6px;
  text-transform: uppercase;
}
.wing-hint {
  font-family: var(--f-typewriter);
  font-size: 10px;
  color: var(--khaki);
  font-weight: normal;
  font-style: italic;
}
.wing-logo-zone {
  min-height: 80px;
}
/* Squadron cards */
.wing-sq-card {
  border: 1px solid var(--khaki);
  border-radius: 4px;
  padding: 10px;
  margin-bottom: 10px;
  background: rgba(0,0,0,.15);
}
.wing-sq-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  font-family: var(--f-stencil);
  font-size: 12px;
  color: var(--khaki-light);
  letter-spacing: .06em;
}
.wing-sq-toggle {
  flex: 1;
  cursor: pointer;
  user-select: none;
}
.wing-sq-toggle::before {
  content: '▶ ';
  font-size: 9px;
  opacity: .7;
}
.wing-sq-card.open .wing-sq-toggle::before {
  content: '▼ ';
}
.wing-sq-body {
  display: none;
}
.wing-sq-card.open .wing-sq-body {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
/* Aircraft tags */
.wing-aircraft-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
  align-items: center;
}
.wing-ac-tag {
  background: var(--olive);
  color: var(--paper-light);
  font-family: var(--f-typewriter);
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 3px;
  display: flex;
  align-items: center;
  gap: 4px;
}
.wing-ac-tag button {
  background: none;
  border: none;
  color: var(--paper-light);
  cursor: pointer;
  padding: 0;
  font-size: 12px;
  line-height: 1;
  opacity: .7;
}
.wing-ac-tag button:hover { opacity: 1; }
.wing-ac-add-row {
  display: flex;
  gap: 6px;
  margin-top: 4px;
}
.wing-ac-add-row input {
  flex: 1;
}
.wing-ac-add-row button {
  white-space: nowrap;
}
/* Action buttons */
.wing-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 4px 0 10px 0;
}
.wing-action-btn {
  flex: 1;
  min-width: 120px;
  font-family: var(--f-stencil);
  font-size: 12px;
  letter-spacing: .05em;
  padding: 9px 10px;
  border-radius: 3px;
  border: 1px solid var(--khaki);
  background: rgba(0,0,0,.2);
  color: var(--paper-light);
  cursor: pointer;
  text-align: center;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
  transition: background .15s;
}
.wing-action-btn:hover { background: var(--olive); }
.wing-action-import input[type=file] { display: none; }
.wing-action-reset { border-color: var(--red-stamp); color: var(--red-stamp); }
.wing-action-reset:hover { background: var(--red-stamp); color: var(--paper-light); }
/* Size counter */
.wing-size-counter {
  font-family: var(--f-typewriter);
  font-size: 11px;
  color: var(--khaki);
  text-align: right;
  padding: 4px 2px 0;
  opacity: .75;
}
.wing-size-counter.warn { color: #e8b840; opacity: 1; }

/* id field invalid: spaces or slashes detected */
.wing-id-warning {
  border-color: #e8b840 !important;
  box-shadow: 0 0 0 2px rgba(232,184,64,.25) !important;
}
/* Logo zone busy during async compression */
.wing-logo-loading {
  opacity: .45;
  cursor: wait !important;
  pointer-events: none;
}

/* ── Wing read-only panel (P1.B) ── */
.wing-ro-info {
  margin-bottom: 12px;
}
.wing-ro-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  background: rgba(0,0,0,.2);
  border: 1px solid var(--khaki);
  border-radius: 4px;
}
.wing-ro-logo {
  width: 56px; height: 56px;
  object-fit: contain;
  flex-shrink: 0;
  background: rgba(0,0,0,.1);
  border-radius: 3px;
}
.wing-ro-text {
  flex: 1;
  min-width: 0;
}
.wing-ro-name {
  font-family: var(--f-stencil);
  font-size: 14px;
  letter-spacing: 2px;
  color: var(--amber);
  text-transform: uppercase;
}
.wing-ro-full {
  font-family: var(--f-typewriter);
  font-size: 11px;
  color: var(--paper-dark);
  margin-top: 2px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.wing-ro-meta {
  font-family: var(--f-ui);
  font-size: 10px;
  font-weight: 500;
  letter-spacing: 1px;
  color: var(--khaki-light);
  margin-top: 3px;
  text-transform: uppercase;
}
.wing-hq-hint {
  font-family: var(--f-ui);
  font-size: 10px;
  font-weight: 500;
  letter-spacing: 1.5px;
  color: var(--khaki-light);
  text-align: center;
  padding: 6px 0;
  border-top: 1px dotted var(--khaki);
  margin-top: 8px;
  text-transform: uppercase;
  opacity: .7;
}

/* ============ PREVIEW ============ */
.preview-wrap {
  overflow: auto;
  overscroll-behavior: contain;   /* AJOUT chatG : isolation du scroll, prévention reflows en cascade */
  background: var(--olive-deep);
  padding: 30px 20px 60px 20px;
}
.preview-wrap::-webkit-scrollbar { width: 12px; }
.preview-wrap::-webkit-scrollbar-track { background: var(--olive-deep); }
.preview-wrap::-webkit-scrollbar-thumb { background: var(--khaki); border: 2px solid var(--olive-deep); }

/* PAGES */
.page {
  width: 794px;
  height: 1123px;           /* A4 figée — plus de min-height (chatE étape A) */
  max-height: 1123px;
  margin: 0 auto 30px auto;
  background: var(--page-bg);
  background-image: var(--kraft-bg);
  background-size: 100% 100%;
  background-repeat: no-repeat;
  background-position: top left;
  color: var(--ink);
  position: relative;
  box-shadow: 0 8px 24px rgba(0,0,0,.5), 0 2px 4px rgba(0,0,0,.3);
  padding: 28px 36px 50px 36px;  /* bottom 60→50px pour mieux placer le footer (chatE étape A) */
  overflow: hidden;
  -webkit-print-color-adjust: exact;
  print-color-adjust: exact;
}

.page::before, .page::after {
  content: '';
  position: absolute;
  width: 22px; height: 22px;
  border: 2px solid var(--ink-faded);
  pointer-events: none;
}
.page::before { top: 8px; left: 8px; border-right: none; border-bottom: none; }
.page::after { bottom: 8px; right: 8px; border-left: none; border-top: none; }

/* PAGE HEADER */
.p-header {
  display: grid;
  grid-template-columns: 70px 1fr 70px;
  align-items: center;
  gap: 16px;
  padding-bottom: 12px;
  border-bottom: 3px double var(--ink-faded);
  margin-bottom: 18px;
}
.p-header .p-header-logo {
  width: 64px; height: 64px;
  /* FIX Bug B (complément) : background-image au lieu d'object-fit pour
     compatibilité html2canvas */
  background-size: contain;
  background-repeat: no-repeat;
  background-position: center;
  filter: contrast(1.05);
}
.p-header .p-title { text-align: center; }
.p-header .p-title .p-classif {
  font-family: var(--f-stencil);
  letter-spacing: 6px;
  font-size: 11px;
  color: var(--red-stamp);
  border: 2px solid var(--red-stamp);
  padding: 2px 10px;
  display: inline-block;
  margin-bottom: 6px;
}
.p-header .p-title h1 {
  font-family: var(--f-stencil);
  font-size: 28px;
  letter-spacing: 4px;
  color: var(--ink);
  font-weight: 700;
}
.p-header .p-title .p-sub {
  font-family: var(--f-condensed);
  font-weight: 600;
  font-size: 11px;
  letter-spacing: 3px;
  color: var(--ink-faded);
  margin-top: 2px;
  text-transform: uppercase;
}

/* SECTION BANNER */
.p-section {
  background: var(--olive-dark);
  color: var(--paper-light);
  font-family: var(--f-stencil);
  font-size: 16px;
  letter-spacing: 5px;
  text-align: center;
  padding: 8px 12px;
  border-top: 2px solid var(--amber-dark);
  border-bottom: 2px solid var(--amber-dark);
  margin-bottom: 14px;
}
.p-section::before, .p-section::after {
  content: '◆';
  color: var(--amber);
  margin: 0 12px;
  font-size: 10px;
  vertical-align: middle;
}

.p-subsection {
  background: var(--khaki);
  color: var(--paper-light);
  font-family: var(--f-condensed);
  font-weight: 700;
  font-size: 13px;
  letter-spacing: 3px;
  text-align: center;
  padding: 5px 10px;
  margin: 14px 0 8px 0;
  border-left: 4px solid var(--amber-dark);
  border-right: 4px solid var(--amber-dark);
  text-transform: uppercase;
}

.p-body {
  font-family: var(--f-typewriter);
  font-size: 13px;
  line-height: 1.65;
  color: var(--ink);
}
.p-body p { margin-bottom: 10px; text-align: justify; }

/* BULLETS */
.p-bullets { list-style: none; padding-left: 4px; }
.p-bullets li {
  padding: 4px 0 4px 24px;
  position: relative;
  border-bottom: 1px dotted var(--paper-edge);
}
.p-bullets li:last-child { border-bottom: none; }
.p-bullets li::before {
  content: '✓';
  position: absolute;
  left: 4px; top: 4px;
  color: var(--olive);
  font-weight: 700;
  font-size: 14px;
}

.p-bullets-num { list-style: none; padding: 0; counter-reset: stepcount; }
.p-bullets-num li {
  padding: 3px 0 3px 32px;
  position: relative;
  counter-increment: stepcount;
}
.p-bullets-num li::before {
  content: counter(stepcount, decimal-leading-zero);
  position: absolute;
  left: 4px; top: 3px;
  font-family: var(--f-condensed);
  font-weight: 700;
  font-size: 11px;
  color: var(--rust);
  background: var(--paper-light);
  border: 1px solid var(--khaki);
  padding: 0 4px;
  letter-spacing: 1px;
}

/* IMAGE FRAME */
.p-imgframe {
  border: 2px solid var(--ink-faded);
  padding: 5px;
  background: rgba(0,0,0,.05);
  margin: 10px 0;
  position: relative;
}
.p-imgframe::before {
  content: attr(data-label);
  position: absolute;
  top: -10px; left: 10px;
  background: var(--paper);
  padding: 0 6px;
  font-family: var(--f-condensed);
  font-weight: 600;
  font-size: 10px;
  letter-spacing: 2px;
  color: var(--ink-faded);
  text-transform: uppercase;
}
.p-imgframe img {
  display: block;
  max-width: 100%;
  width: auto;
  height: auto;
  max-height: 200mm;   /* élargi vs original 190mm, marge de sécurité vs débordement A4 */
  margin: 0 auto;   /* centrage horizontal */
}
.p-imgframe.empty {
  background:
    linear-gradient(135deg, transparent 49%, var(--khaki) 49%, var(--khaki) 51%, transparent 51%),
    linear-gradient(45deg, transparent 49%, var(--khaki) 49%, var(--khaki) 51%, transparent 51%);
  background-size: 40px 40px;
  background-color: rgba(0,0,0,.04);
  min-height: 280px;
  display: flex; align-items: center; justify-content: center;
}
.p-imgframe.empty::after {
  content: attr(data-empty-label);
  font-family: var(--f-stencil);
  letter-spacing: 4px;
  color: var(--khaki);
  font-size: 14px;
  background: var(--paper);
  padding: 8px 16px;
}

/* FOOTER */
.p-footer {
  position: absolute;
  bottom: 16px; left: 36px; right: 36px;
  display: flex; justify-content: space-between;
  align-items: center;
  border-top: 1px solid var(--ink-faded);
  padding-top: 6px;
  font-family: var(--f-condensed);
  font-weight: 600;
  font-size: 10px;
  letter-spacing: 2px;
  color: var(--ink-faded);
  text-transform: uppercase;
}
.p-footer .p-classif-foot {
  color: var(--red-stamp);
  letter-spacing: 4px;
  font-family: var(--f-stencil);
  font-weight: 700;
}

/* THREAT CHIPS */
.threat-chip {
  display: inline-block;
  font-family: var(--f-stencil);
  font-size: 11px;
  letter-spacing: 3px;
  padding: 4px 12px;
  border: 2px solid;
  text-transform: uppercase;
  vertical-align: middle;
}
/* Faible — vert */
.threat-chip.t-faible  { color: #1a4d1a; border-color: #2d6e2d; background: #c8e6c9; }
/* Modéré — orange vif */
.threat-chip.t-modere  { color: #7a3a00; border-color: #d06000; background: #ffe0b2; }
/* Élevé  — rouge */
.threat-chip.t-eleve   { color: #fff;    border-color: #7b0000; background: #b71c1c; }

/* PHASE TITLE BLOCK */
.phase-title {
  font-family: var(--f-stencil);
  font-size: 17px;
  letter-spacing: 3px;
  color: var(--olive-dark);
  border-bottom: 1px solid var(--ink-faded);
  padding-bottom: 4px;
  margin-bottom: 8px;
  display: flex; align-items: center; flex-wrap: wrap; gap: 10px;
}
.phase-num-tag {
  background: var(--olive-dark);
  color: var(--amber);
  padding: 2px 8px;
  font-size: 12px;
  letter-spacing: 2px;
}

.phase-block {
  margin-bottom: 14px;
  padding: 8px 10px;
  background: rgba(255,255,255,.18);
  border-left: 3px solid var(--olive);
}
.phase-block-label {
  font-family: var(--f-condensed);
  font-weight: 700;
  font-size: 11px;
  letter-spacing: 2px;
  color: var(--rust);
  text-transform: uppercase;
  margin-bottom: 4px;
}

.p-2col { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
.p-2col > div { min-width: 0; }

/* METAR */
.metar-line {
  font-family: var(--f-mono);
  font-size: 14px;
  letter-spacing: 1px;
  background: var(--olive-deep);
  color: #b3d99b;
  padding: 10px 14px;
  border-left: 4px solid var(--green-radar);
  border-right: 4px solid var(--green-radar);
  margin: 4px 0;
  word-break: break-all;
}
.metar-line::before { content: '> '; color: var(--amber); }

/* RADIO */

.txt-small { font-size: 11px; color: var(--ink-faded); }

/* ============ SUB-TASKS in preview ============ */
.p-subtasks {
  list-style: none;
  padding-left: 20px;
  margin-top: 4px;
  counter-reset: subtask;
}
.p-subtasks li {
  padding: 2px 0 2px 22px;
  position: relative;
  border-bottom: none;
  font-size: 12px;
  color: var(--ink-faded);
  counter-increment: subtask;
}
.p-subtasks li::before {
  content: counter(subtask, lower-alpha) ')';
  position: absolute;
  left: 0;
  font-family: var(--f-condensed);
  font-weight: 700;
  font-size: 11px;
  color: var(--olive);
  letter-spacing: 1px;
}

/* ============ REORDER buttons in editor lists ============ */
.ed-list-item { align-items: flex-start; }
.ed-list-move {
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex-shrink: 0;
}
.ed-btn-move {
  background: var(--olive-dark);
  border: 1px solid var(--khaki);
  color: var(--khaki-light);
  font-size: 12px;
  line-height: 1;
  cursor: pointer;
  padding: 0;
  width: 32px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all .12s;
}
.ed-btn-move:hover:not(:disabled) {
  background: var(--amber-dark);
  color: var(--paper);
  border-color: var(--amber);
}
.ed-btn-move:disabled { opacity: .3; cursor: not-allowed; }
.ed-btn-move:active:not(:disabled) { transform: translateY(1px); }

/* Sub-task items in editor */
.ed-subtask-wrap {
  margin-top: 6px;
  padding-left: 12px;
  border-left: 2px solid var(--olive-dark);
  display: flex;
  flex-direction: column;
  gap: 5px;
}
.ed-subtask-row {
  display: flex;
  gap: 6px;
}
.ed-subtask-row input { flex: 1; font-size: 12px; }
.ed-btn-subtask-add {
  font-family: var(--f-ui);
  font-weight: 600;
  font-size: 10px;
  letter-spacing: 1px;
  text-transform: uppercase;
  background: transparent;
  border: 1px dashed var(--olive);
  color: var(--olive);
  cursor: pointer;
  padding: 5px 10px;
  margin-top: 4px;
  transition: all .12s;
}
.ed-btn-subtask-add:hover { background: var(--olive-dark); color: var(--paper); }

/* Phase bar with reorder buttons */
.phase-bar {
  display: grid;
  grid-template-columns: 44px 1fr 44px 44px 44px 44px 44px 44px;
  gap: 6px;
}

.empty-placeholder {
  font-family: var(--f-typewriter);
  font-style: italic;
  color: var(--khaki);
  padding: 10px 0;
  border: 1px dashed var(--khaki);
  text-align: center;
  margin: 6px 0;
  font-size: 12px;
}

/* ============ RADIO SUMMARY (page 3) ============ */
.radio-summary {
  width: 100%;
  border-collapse: collapse;
  font-family: var(--f-typewriter);
  font-size: 12px;
  margin: 4px 0;
}
.radio-summary tr { border-bottom: 1px dotted var(--paper-edge); }
.radio-summary tr:last-child { border-bottom: none; }
.radio-summary th {
  text-align: left;
  font-family: var(--f-condensed);
  font-weight: 700;
  font-size: 11px;
  letter-spacing: 1.5px;
  color: var(--rust);
  text-transform: uppercase;
  padding: 4px 8px 4px 4px;
  white-space: nowrap;
  width: 1%;
}
.radio-summary td {
  padding: 4px 4px;
  text-align: right;
}
.radio-summary .radio-freq {
  font-family: var(--f-mono);
  font-weight: 700;
  letter-spacing: 1px;
  color: var(--ink);
}
.radio-summary .radio-mod {
  font-family: var(--f-condensed);
  font-weight: 700;
  font-size: 10px;
  letter-spacing: 1.5px;
  color: var(--olive);
  margin-left: 6px;
  display: inline-block;
  padding: 1px 5px;
  background: rgba(74, 82, 48, .15);
  border: 1px solid var(--paper-edge);
}

/* ============ RADIO TABLE (annexe per aircraft) ============ */
.radio-block {
  margin-bottom: 12px;
}
.radio-block-name {
  font-family: var(--f-stencil);
  font-size: 14px;
  letter-spacing: 3px;
  color: var(--olive-dark);
  background: var(--paper-light);
  padding: 4px 10px;
  border-left: 3px solid var(--rust);
  border-bottom: 1px solid var(--paper-edge);
}
.radio-channel-table {
  width: 100%;
  border-collapse: collapse;
  font-family: var(--f-mono);
  font-size: 11px;
  margin-top: 2px;
}
.radio-channel-table tr { border-bottom: 1px dotted var(--paper-edge); }
.radio-channel-table tr:last-child { border-bottom: none; }
.radio-channel-table td {
  padding: 3px 6px;
  vertical-align: middle;
}
.radio-channel-table .ch-num {
  font-family: var(--f-condensed);
  font-weight: 700;
  font-size: 10px;
  letter-spacing: 2px;
  color: var(--rust);
  background: var(--paper-light);
  width: 1%;
  white-space: nowrap;
  text-align: center;
}
.radio-channel-table .ch-freq {
  font-weight: 700;
  letter-spacing: 1px;
  color: var(--ink);
  width: 1%;
  white-space: nowrap;
}
.radio-channel-table .ch-mod {
  width: 1%;
  white-space: nowrap;
  font-family: var(--f-condensed);
  font-weight: 600;
  font-size: 10px;
  color: var(--olive);
  letter-spacing: 1px;
}
.radio-channel-table .ch-label {
  font-family: var(--f-typewriter);
  font-size: 11px;
  color: var(--ink-faded);
  letter-spacing: 0.5px;
}

/* ============ GUEST SQUADRON badge (no logo) ============ */
.squadron-logo-guest {
  width: 38px; height: 38px;
  flex-shrink: 0;
  background: var(--olive-dark);
  border: 2px solid var(--khaki);
  display: flex; align-items: center; justify-content: center;
  font-family: var(--f-stencil);
  font-size: 10px;
  letter-spacing: 1px;
  color: var(--amber);
}
.squadron-grid .squadron-logo-guest {
  width: 32px; height: 32px;
  font-size: 8px;
}

/* Extended squadron chip with sub-group */
.squadron-chip .sq-sub {
  padding: 5px 10px;
  color: var(--olive-dark);
  font-style: italic;
  border-right: 1px solid var(--paper-edge);
  font-family: var(--f-typewriter);
  font-weight: 400;
  font-size: 11px;
  letter-spacing: 0.5px;
  text-transform: none;
}

/* ============ EDITOR — canal custom toggle ============ */
.ed-channel-row {
  display: grid;
  grid-template-columns: 44px 56px 1fr 44px;
  gap: 5px;
  align-items: start;
  margin-bottom: 4px;
}
.ed-channel-row.custom-mode {
  grid-template-columns: 44px 56px 1fr 1fr 58px 44px;
}
.ed-ch-toggle {
  font-family: var(--f-ui);
  font-weight: 700;
  font-size: 10px;
  letter-spacing: 1px;
  text-transform: uppercase;
  background: var(--olive);
  color: var(--paper-light);
  border: 1px solid var(--khaki);
  cursor: pointer;
  min-height: 44px;
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all .15s;
  line-height: 1.1;
  text-align: center;
  padding: 2px 3px;
}
.ed-ch-toggle:hover { background: var(--amber-dark); border-color: var(--amber); }
.ed-ch-toggle:active { transform: translateY(1px); }
.ed-ch-toggle.is-custom {
  background: var(--rust);
  color: var(--paper-light);
  border-color: var(--red-faded);
}
.ed-ch-toggle.is-custom:hover { background: var(--red-stamp); }

/* Radio table rows for custom freqs (dim the ch-label) */
.radio-channel-table .ch-custom-label {
  font-family: var(--f-typewriter);
  font-size: 11px;
  color: var(--ink-faded);
  font-style: italic;
}

/* Guest squadron fields in phase editor */
.ed-guest-fields {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 10px;
  background: rgba(122, 58, 32, .08);
  border: 1px dashed var(--rust);
  margin-top: 2px;
}
.ed-guest-fields label::before { color: var(--red-stamp); }

/* ── Assistant METAR (10A + 10C) ─────────────────────────────────── */
.metar-form { padding: 10px 0; }
.metar-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 8px;
  align-items: center;
}
.metar-field { display: flex; flex-direction: column; gap: 3px; }
.metar-field label {
  font-family: var(--f-ui);
  font-size: 10px;
  text-transform: uppercase;
  color: var(--amber);
  letter-spacing: 1px;
}
.metar-field input, .metar-field select {
  font-family: var(--f-ui);
  font-size: 13px;
  width: 80px;
  padding: 3px 6px;
  background: var(--input-bg);
  border: 1px solid var(--border);
  color: var(--text);
}
.metar-field input[type="text"] { width: 90px; }
.metar-field input[type="number"] { width: 60px; }
#ma-wspd, #ma-gust { width: 52px; }
.metar-check-label {
  display: flex;
  align-items: center;
  gap: 5px;
  font-family: var(--f-ui);
  font-size: 11px;
  text-transform: uppercase;
  color: var(--amber);
  cursor: pointer;
}
.metar-check-label input[type="checkbox"] {
  accent-color: var(--amber);
  width: 15px; height: 15px;
}
.metar-preview-line {
  margin: 10px 0;
  padding: 8px 12px;
  background: rgba(0,0,0,.25);
  border-left: 3px solid var(--amber);
  font-family: var(--f-mono);
  font-size: 13px;
  color: var(--text);
  letter-spacing: 1.5px;
  word-break: break-all;
}
.metar-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: 8px;
}
.metar-more > summary {
  font-family: var(--f-ui);
  font-size: 11px;
  color: var(--text-dim);
  cursor: pointer;
  margin-bottom: 6px;
}


@media (max-width: 600px) {
  .ed-channel-row.custom-mode {
    grid-template-columns: 44px 52px 1fr 50px 44px;
  }
}
/* Ligne aérodrome structuré (Partie 1 — 10B-lite) */
.ed-airfield-row {
  display: grid;
  grid-template-columns: 56px auto 1fr 52px auto 36px;
  gap: 6px;
  margin-bottom: 6px;
  align-items: center;
}
/* Tablette portrait et + (>600px) : on NE surcharge PAS .ed-airfield-row
   → la grille desktop "56px auto 1fr 52px auto 36px" s'applique = tout sur UNE ligne. */
@media (max-width: 600px) {
  .ed-airfield-row {
    grid-template-columns: 56px auto 1fr auto;
    grid-template-areas:
      "icao farp name rm"
      "rwy  atc  atc  atc";
    gap: 6px 8px;
  }
  .ed-airfield-row .af-icao       { grid-area: icao; }
  .ed-airfield-row .af-farp-check { grid-area: farp; }
  .ed-airfield-row .af-name       { grid-area: name; }
  .ed-airfield-row .af-rm         { grid-area: rm;  justify-self: end; }
  .ed-airfield-row .af-rwy        { grid-area: rwy; }
  .ed-airfield-row .af-atc-check  { grid-area: atc; justify-self: start; }
  .ed-airfield-row .af-icao,
  .ed-airfield-row .af-name,
  .ed-airfield-row .af-rwy        { min-width: 0; }
}
.af-farp-check, .af-atc-check {
  display: flex;
  align-items: center;
  gap: 4px;
  font-family: var(--f-ui);
  font-size: 11px;
  text-transform: uppercase;
  color: var(--amber);
  cursor: pointer;
  white-space: nowrap;
}
.af-farp-check input[type="checkbox"],
.af-atc-check  input[type="checkbox"] {
  accent-color: var(--amber);
  width: 15px; height: 15px;
  cursor: pointer;
}

.ed-radio-item-row {
  display: grid;
  grid-template-columns: 28px 1.5fr 1fr 70px 44px; /* 2b : colonne checkbox overview */
  gap: 6px;
  margin-bottom: 6px;
  align-items: center;
}
.ed-radio-item-row input,
.ed-radio-item-row select {
  min-width: 0;
}
/* Case à cocher overview (2b) */
.ri-overview-check {
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}
.ri-overview-check input[type="checkbox"] {
  width: 16px;
  height: 16px;
  accent-color: var(--amber);
  cursor: pointer;
}
.ri-overview-check input[type="checkbox"]:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}

.ed-radio-block {
  border: 1px dashed var(--khaki);
  padding: 8px;
  margin-bottom: 8px;
  background: rgba(0,0,0,.12);
}
.ed-radio-block-head {
  display: flex;
  gap: 6px;
  margin-bottom: 6px;
}
.ed-radio-block-head input {
  flex: 1;
  background: rgba(216, 201, 165, .92) !important;
  border-left-color: var(--amber) !important;
  font-weight: 400;
  letter-spacing: 1px;
}
.ed-channels-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: 6px;
}
.ed-channel-row input,
.ed-channel-row select { min-width: 0; }

.ed-btn-add-sm {
  padding: 6px 10px;
  min-height: 36px;
  font-size: 10px;
}

/* Mobile: tighter rows */
@media (max-width: 600px) {
  .ed-radio-item-row {
    grid-template-columns: 1fr 80px 60px 40px;
  }
}
.menace-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 6px;
  margin: 6px 0;
}
.menace-cell {
  background: rgba(122, 58, 32, .08);
  border: 1px solid var(--paper-edge);
  border-left: 3px solid var(--rust);
  padding: 5px 10px;
  font-size: 12px;
  /* v2.4.0 — une ligne par catégorie : le nom (colonne fixe) puis les menaces */
  display: flex;
  align-items: flex-start;
  gap: 8px;
}
.menace-cell strong {
  font-family: var(--f-condensed);
  font-weight: 700;
  font-size: 11px;
  letter-spacing: 2px;
  color: var(--rust);
  text-transform: uppercase;
  flex: 0 0 var(--menace-name-w, 124px);
  white-space: nowrap;
}
.menace-cell .menace-val {
  flex: 1 1 0;
  min-width: 0;
  overflow-wrap: anywhere;
}

/* SQUADRON CHIP (on phase pages, just under section title) */
.squadron-chip {
  /* FIX Bug C : display flex + width fit-content au lieu de inline-flex
     pour contourner un bug html2canvas qui peint la bordure mais pas le contenu
     quand inline-flex + overflow:hidden sont combinés */
  display: flex;
  width: fit-content;
  align-items: center;
  gap: 0;
  border: 2px solid var(--olive-dark);
  background: var(--paper-light);
  font-family: var(--f-condensed);
  font-weight: 700;
  font-size: 11px;
  letter-spacing: 2px;
  text-transform: uppercase;
  margin: 0 0 8px 0;
  overflow: hidden;
}
.squadron-chip .sq-id {
  background: var(--olive-dark);
  color: var(--amber);
  padding: 5px 10px;
  letter-spacing: 3px;
}
.squadron-chip .sq-cs {
  padding: 5px 10px;
  color: var(--rust);
  border-right: 1px solid var(--paper-edge);
}
.squadron-chip .sq-ac {
  padding: 5px 10px;
  color: var(--ink-faded);
  font-family: var(--f-mono);
  font-weight: 500;
  font-size: 11px;
  letter-spacing: 1px;
  text-transform: none;
}

/* SQUADRON GRID on Mission Overview page */
.squadron-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 6px 0;
}
/* All cells always the same width — 3 per row, regardless of total count.
   Formula: (100% - 2 gaps) / 3  →  (100% - 16px) / 3 */
.squadron-cell {
  flex: 0 0 calc(33.333% - 5.334px);
  min-width: 0;
}
.squadron-cell {
  display: flex;
  align-items: center;
  gap: 10px;
  background: rgba(74, 82, 48, .12);
  border: 1px solid var(--paper-edge);
  border-left: 3px solid var(--olive);
  padding: 6px 10px;
  font-size: 12px;
  min-width: 0;
}
.squadron-cell .squadron-logo-sm {
  width: 38px;
  height: 38px;
  /* FIX Bug B : background-image au lieu d'object-fit pour compatibilité html2canvas */
  background-size: contain;
  background-repeat: no-repeat;
  background-position: center;
  flex-shrink: 0;
}
.squadron-cell .squadron-info { flex: 1; min-width: 0; overflow: hidden; }
.squadron-cell .squadron-info strong {
  font-family: var(--f-condensed);
  font-weight: 700;
  font-size: 11px;
  letter-spacing: 1.5px;
  color: var(--olive-dark);
  text-transform: uppercase;
  display: block;
  margin-bottom: 1px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.squadron-cell .squadron-aircraft {
  font-family: var(--f-mono);
  font-size: 10px;
  color: var(--ink-faded);
  letter-spacing: 0.5px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.squadron-cell .squadron-phases {
  font-family: var(--f-condensed);
  font-weight: 600;
  font-size: 10px;
  letter-spacing: 1.5px;
  color: var(--rust);
  text-transform: uppercase;
  margin-top: 1px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
/* All cells are compact (always 3-col) */
.squadron-grid .squadron-cell {
  padding: 6px 8px;
  gap: 8px;
}
.squadron-grid .squadron-cell .squadron-logo-sm {
  width: 32px;
  height: 32px;
}

/* ============ IMAGE PAGES (dedicated) ============ */
.p-img-page-grid {
  display: flex;
  flex-direction: column;
  gap: 20px;
}
/* 2 images empilées — hauteur réduite pour tenir sur la page */
.p-img-page-grid.stacked-two .p-img-block img {
  max-height: 88mm;
}
.p-img-block {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.p-img-block-title {
  font-family: var(--f-condensed);
  font-weight: 700;
  font-size: 12px;
  letter-spacing: 2px;
  text-transform: uppercase;
  color: var(--rust);
  border-bottom: 1px solid var(--paper-edge);
  padding-bottom: 4px;
}
.p-img-block img {
  /* Le cadre s'adapte à l'image (pas l'inverse) — centré horizontalement */
  display: block;
  max-width: 100%;
  width: auto;
  height: auto;
  max-height: 190mm;
  margin: 0 auto;
  border: 1px solid var(--paper-edge);
}
.p-img-block-caption {
  font-family: var(--f-typewriter);
  font-size: 11px;
  color: var(--ink-faded);
  font-style: italic;
  line-height: 1.3;
  border-top: 1px dotted var(--paper-edge);
  padding-top: 4px;
}
.p-annexe-caption {
  font-family: var(--f-typewriter);
  font-size: 12px;
  color: var(--ink);
  margin-top: 8px;
  padding: 0 4mm;
  line-height: 1.4;
}

/* ============ EDITOR — phase images list ============ */
.ed-img-list { display: flex; flex-direction: column; gap: 14px; }
.ed-img-card {
  border: 1px solid var(--khaki);
  background: rgba(0,0,0,.15);
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  position: relative;
}
.ed-img-card-num {
  position: absolute;
  top: -10px; left: 10px;
  background: var(--olive);
  color: var(--paper);
  font-family: var(--f-stencil);
  font-size: 10px;
  letter-spacing: 1px;
  padding: 2px 8px;
  border: 1px solid var(--khaki);
}
.ed-img-card-rm {
  position: absolute;
  top: -10px; right: 8px;
  background: var(--rust);
  color: var(--paper-light);
  border: 1px solid var(--red-faded);
  cursor: pointer;
  padding: 2px 10px;
  font-family: var(--f-condensed);
  font-weight: 700;
  font-size: 11px;
  text-transform: uppercase;
}
.ed-img-card-rm:hover { background: var(--red-stamp); }

/* STAMPS */
.stamp-classif {
  transform: rotate(-9deg);
  border: 4px solid var(--red-stamp);
  color: var(--red-stamp);
  font-family: var(--f-stencil);
  font-size: 18px;
  letter-spacing: 4px;
  padding: 6px 16px;
  opacity: .55;
  text-align: center;
  background: rgba(255,255,255,.05);
  order: 2;
}
.stamp-classif::before, .stamp-classif::after {
  content: '';
  display: block;
  height: 2px;
  background: var(--red-stamp);
  margin: 4px 0;
}

.stamp-receipt {
  transform: rotate(-4deg);
  border: 2px solid var(--ink-faded);
  color: var(--ink-faded);
  font-family: var(--f-typewriter);
  font-size: 10px;
  letter-spacing: 1.5px;
  padding: 6px 12px;
  opacity: .65;
  text-transform: uppercase;
  text-align: center;
  background: rgba(255,255,255,.18);
  line-height: 1.3;
  order: 1;
}

/* ============================================
   STAMPS — Phase X étape D : variantes thématiques
   Overrides CSS uniquement, le DOM .stamp-classif reste inchangé.
   Le texte (state.meta.classification) demeure dynamique.
   ============================================ */

/* --- cw-soviet : étoile à 5 branches en arrière-plan, texte ocre crème
       Plan B3 — sceau quasi-carré (width 180px) pour préserver l'aspect-ratio
       de l'étoile (1:1) et garantir les 5 pointes visibles quel que soit
       le texte. white-space normal autorise le wrap sur 2 lignes pour les
       classifications longues. paint-order + text-stroke pour la lisibilité
       quand le texte déborde marginalement de la zone rouge centrale.
       Variante A — sceau centré horizontalement (display: block + margin auto)
       pour une composition équilibrée au lieu d'aligné à gauche en flow normal. --- */
body[data-theme="cw-soviet"] .stamp-classif {
  display: block;
  margin: 24px auto 8px auto;
  border: 3px solid var(--red-stamp);
  width: 180px;
  color: #e8d690;
  -webkit-text-stroke: 1.5px #1a1610;
  paint-order: stroke fill;
  font-weight: 400;
  letter-spacing: 1px;
  font-size: 14px;
  line-height: 1.2;
  opacity: .9;
  transform: rotate(-6deg);
  padding: 70px 24px;
  white-space: normal;
  text-align: center;
  background-color: transparent;
  background-image: url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAxMDAgMTAwIj48cG9seWdvbiBwb2ludHM9IjUwLDIgNjEuNzYsMzMuODIgOTUuNjUsMzUuMTcgNjkuMDIsNTYuMTggNzguMjEsODguODMgNTAsNzAgMjEuNzksODguODMgMzAuOTgsNTYuMTggNC4zNSwzNS4xNyAzOC4yNCwzMy44MiIgZmlsbD0iIzg0MWUxZSIvPjwvc3ZnPg==');
  background-size: contain;
  background-position: center;
  background-repeat: no-repeat;
}
body[data-theme="cw-soviet"] .stamp-classif::before,
body[data-theme="cw-soviet"] .stamp-classif::after {
  display: none;
}

/* --- modern-nato + modern-east : carré digital plat, sans rotation, pas vintage --- */
body[data-theme="modern-nato"] .stamp-classif,
body[data-theme="modern-east"] .stamp-classif {
  border: 1.5px solid var(--red-stamp);
  border-radius: 4px;
  transform: rotate(0deg);
  opacity: 1;
  font-family: var(--f-typewriter);
  font-weight: 400;
  font-size: 13px;
  letter-spacing: 2px;
  padding: 8px 16px 8px 30px;
  background: rgba(255,255,255,.45);
  position: relative;
}
/* Pastille indicatrice ronde — réutilise le pseudo-élément ::before
   (qui faisait la barre horizontale en cw-nato). */
body[data-theme="modern-nato"] .stamp-classif::before,
body[data-theme="modern-east"] .stamp-classif::before {
  content: '';
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  display: block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--red-stamp);
  margin: 0;
}
/* Cacher la barre horizontale du bas en modern-nato. */
body[data-theme="modern-nato"] .stamp-classif::after {
  display: none;
}

/* --- modern-east : étiquette ID mini bleu-noir au coin inférieur droit
       Réutilise ::after (qui faisait la barre du bas en cw-nato). --- */
body[data-theme="modern-east"] .stamp-classif {
  padding-bottom: 14px;
}
body[data-theme="modern-east"] .stamp-classif::after {
  content: 'MZ-7';
  display: block;
  position: absolute;
  bottom: 1px;
  right: 6px;
  background: transparent;
  color: #1a2030;  /* bleu-noir hors palette de thème (accent dédié) */
  font-family: var(--f-typewriter);
  font-weight: 400;
  font-size: 7px;
  letter-spacing: 1px;
  margin: 0;
  height: auto;
}

.doc-meta {
  position: absolute;
  top: 12px; left: 50%;
  transform: translateX(-50%);
  font-family: var(--f-mono);
  font-size: 9px;
  letter-spacing: 2px;
  color: var(--ink-faded);
  text-transform: uppercase;
}

/* ============ ROSTER — single unified <table> per pair of groups ============
   Architecture: ONE <table> = ONE rendering pipeline = stable in both screen & PDF.
   Identical CSS for screen and print (no @media print overrides for roster). */
.roster-tables {
  margin-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 18px;
}
.roster-mega {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
  table-layout: fixed;
}
/* Column widths: always 4 columns, each pair gets 50% */
.rmt-col-name { width: 32%; }
.rmt-col-cs   { width: 18%; }

/* Group header row (colspan="2" for each group) */
.rmt-row-group .rmt-group-head {
  text-align: left;
  padding: 6px 10px 5px 12px;
  border-left: 4px solid var(--rust);
  border-bottom: 1px solid var(--paper-edge);
  vertical-align: top;
  /* No background — uses border-left + page kraft for distinction */
}
.rmt-row-group .rmt-group-head + .rmt-group-head {
  /* Visual gap between left and right group in the same row */
  padding-left: 22px;
}
.rmt-group-name {
  display: block;
  font-family: var(--f-stencil);
  font-weight: 400;
  font-size: 13px;
  letter-spacing: 2px;
  text-transform: uppercase;
  color: var(--olive-dark);
  margin-bottom: 4px;
}
.rmt-group-aircraft {
  display: inline-block;
  font-family: var(--f-mono);
  font-size: 10px;
  letter-spacing: 1.5px;
  color: var(--rust);
  font-weight: normal;
  padding: 1px 5px;
  border: 1px solid var(--rust);
}

/* Column header row */
.rmt-row-cols th {
  font-family: var(--f-condensed);
  font-weight: 700;
  font-size: 10px;
  letter-spacing: 2px;
  text-transform: uppercase;
  color: var(--olive-dark);
  padding: 5px 10px;
  text-align: left;
  border-bottom: 2px solid var(--olive);
}

/* Data cells */
.roster-mega tbody td {
  font-family: var(--f-typewriter);
  font-size: 12px;
  padding: 5px 10px;
  border-bottom: 1px dotted var(--paper-edge);
  vertical-align: middle;
  overflow: hidden;
  text-overflow: ellipsis;
}
.roster-mega tbody tr:last-child td { border-bottom: none; }
.roster-mega .rmt-callsign {
  font-family: var(--f-condensed);
  font-weight: 700;
  font-size: 11px;
  letter-spacing: 1.5px;
  color: var(--rust);
}

/* Vertical separator between left and right groups */
.rmt-sep {
  border-left: 1px dashed var(--paper-edge);
  padding-left: 22px;
}

.ed-label-hint {
  font-weight: 500;
  font-size: 10px;
  letter-spacing: 0.5px;
  color: var(--khaki);
  text-transform: none;
  opacity: 0.8;
}
.roster-aircraft-hint {
  font-family: var(--f-mono);
  font-size: 11px;
  color: var(--amber);
  letter-spacing: 1px;
}

.roster-pilot-row {
  display: grid;
  grid-template-columns: 2fr 1.5fr 44px;
  gap: 6px;
  margin-bottom: 5px;
}
.roster-pilot-row input { min-width: 0; }

/* ============ TAB BAR — active tab roster ============ */
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
  flex: 1;
  background: transparent;
  border: 1px solid transparent;
  color: var(--khaki-light);
  font-family: var(--f-condensed);
  font-weight: 700;
  font-size: 9px;
  letter-spacing: 1px;
  text-transform: uppercase;
  padding: 6px 2px;
  min-height: 54px;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
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

/* ============ TOAST ============ */
.toast {
  position: fixed;
  bottom: 20px; left: 50%;
  transform: translateX(-50%) translateY(100px);
  background: var(--olive-dark);
  border: 1px solid var(--amber);
  color: var(--paper);
  font-family: var(--f-condensed);
  font-weight: 600;
  letter-spacing: 2px;
  text-transform: uppercase;
  font-size: 12px;
  padding: 10px 20px;
  z-index: 2000;
  opacity: 0;
  transition: all .3s ease;
  pointer-events: none;
  box-shadow: 0 4px 16px rgba(0,0,0,.6);
}
.toast.show {
  opacity: 1;
  transform: translateX(-50%) translateY(0);
  pointer-events: auto;
}

/* ============ BRIEF COMPLET / SIMPLIFIÉ (v2.3.0) ============ */
/* Un élément marqué data-fmt n'existe que dans le mode indiqué. */
body[data-format="simple"] [data-fmt="full"] { display: none !important; }
body[data-format="full"] [data-fmt="simple"] { display: none !important; }

.ed-card-bar { display: flex; justify-content: flex-end; gap: 6px; }
.ed-card-bar .ed-btn-icon { min-width: 40px; min-height: 36px; font-size: 16px; }
.ed-btn-icon.neutral { background: var(--olive); border-color: var(--khaki); }
.ed-btn-icon.neutral:hover { background: var(--olive-dark); }
.ed-btn-icon:disabled { opacity: .35; cursor: not-allowed; }
.ed-radio-item-row.s-row { grid-template-columns: 1.5fr 1fr 70px 44px; }
@media (max-width: 600px) {
  .ed-radio-item-row.s-row { grid-template-columns: 1fr 80px 60px 40px; }
}

/* Pages du brief simplifié : tableau des vols, photos */
.p-flights {
  width: 100%;
  border-collapse: collapse;
  margin: 12px 0 6px 0;
  font-family: var(--f-typewriter);
  font-size: 12px;
}
.p-flights th {
  text-align: left;
  font-family: var(--f-condensed);
  font-weight: 700;
  font-size: 11px;
  letter-spacing: 2px;
  color: var(--rust);
  text-transform: uppercase;
  padding: 4px 6px;
  border-bottom: 2px solid var(--ink);
}
.p-flights th.c-vol { width: 105px; }
.p-flights th.c-ac  { width: 100px; }
.p-flights th.c-dep { width: 90px; }   /* v2.4.0 : 80 → 90, « FARP DELTA » tient sur une ligne ; plus long, il passe à la ligne */
.p-flights td {
  padding: 6px 6px;
  vertical-align: top;
  border-bottom: 1px dotted var(--paper-edge);
}
.p-flights .fl-vol {
  font-family: var(--f-condensed);
  font-weight: 700;
  font-size: 14px;
  letter-spacing: 1px;
  text-transform: uppercase;
  white-space: nowrap;
}
.p-flights .fl-ac,
.p-flights .fl-dep { font-family: var(--f-mono); white-space: normal; overflow-wrap: anywhere; }  /* v2.4.0 : passe à la ligne au lieu de sortir de la page */
.p-photo .p-imgframe img { max-height: 330px; }

/* v2.4.0 — page « carte, menaces, cibles » : carte plafonnée en hauteur */
.p-imgframe.p-map-cap img  { max-height: 430px; }
.p-imgframe.p-map-full img { max-height: 800px; }   /* carte seule : la page tient (≈ 820 px utiles sous le bandeau) */

/* v2.4.0 — tableau des cibles (au modèle du tableau des vols), brief simplifié et brief complet */
.p-targets {
  width: 100%;
  table-layout: fixed;
  border-collapse: collapse;
  margin: 12px 0 6px 0;
  font-family: var(--f-typewriter);
  font-size: 12px;
}
.p-targets th {
  text-align: left;
  font-family: var(--f-condensed);
  font-weight: 700;
  font-size: 11px;
  letter-spacing: 2px;
  color: var(--rust);
  text-transform: uppercase;
  padding: 4px 6px;
  border-bottom: 2px solid var(--ink);
}
.p-targets th.c-num { width: 46px; }
.p-targets th.c-nat { width: 170px; }
.p-targets th.c-pos { width: 170px; }
.p-targets td {
  padding: 6px 6px;
  vertical-align: top;
  border-bottom: 1px dotted var(--paper-edge);
  white-space: normal;
  overflow-wrap: anywhere;
}
.p-targets .tg-num {
  font-family: var(--f-condensed);
  font-weight: 700;
  font-size: 14px;
  letter-spacing: 1px;
  text-transform: uppercase;
}
.p-targets .tg-nature { font-weight: 400; }
.p-targets .tg-pos { font-family: var(--f-mono); }

/* v2.4.0 — éditeur : liste des cibles (une rangée : N°, Nature, Position, Remarque, ×) */
.ed-targets { container-type: inline-size; }
.ed-target-row {
  display: grid;
  grid-template-columns: 56px minmax(0, 1fr) minmax(0, 1fr) minmax(0, 1.4fr) 44px;
  grid-template-areas: "num nature pos remark rm";
  gap: 6px;
  margin-bottom: 6px;
  align-items: center;
}
.ed-target-row input { min-width: 0; }
.ed-target-row [data-tg="num"]    { grid-area: num; }
.ed-target-row [data-tg="nature"] { grid-area: nature; }
.ed-target-row [data-tg="position"] { grid-area: pos; }
.ed-target-row [data-tg="remark"] { grid-area: remark; }
.ed-target-row [data-tg-rm]       { grid-area: rm; align-self: stretch; }
@container (max-width: 520px) {
  .ed-target-row {
    grid-template-columns: minmax(0, 1fr) minmax(0, 1fr) 44px;
    grid-template-areas: "num nature rm" "pos remark rm";
  }
}
@media (max-width: 600px) {
  .ed-target-row {
    grid-template-columns: minmax(0, 1fr) minmax(0, 1fr) 44px;
    grid-template-areas: "num nature rm" "pos remark rm";
  }
}
.p-photo-caption {
  font-family: var(--f-typewriter);
  font-style: italic;
  font-size: 12px;
  color: var(--ink);
  margin: 2px 0 10px 0;
  line-height: 1.4;
}

/* ============ RESPONSIVE — TABLET / MOBILE ============ */
@media (max-width: 1100px) {
  /* Hide some toolbar buttons text */
  .tb-btn .tb-btn-label { display: none; }
  .tb-btn { padding: 0 10px; }
  .tb-classif { display: none; }
  .tb-brand { font-size: 13px; padding-right: 10px; }
  .tb-brand-sub { display: none; }

  .app {
    grid-template-columns: 1fr;
    bottom: 68px;
  }
  .app .editor, .app .preview-wrap {
    display: none;
  }
  /* Show only the active panel zone */
  body[data-active-tab="preview"] .preview-wrap { display: block; }
  body:not([data-active-tab="preview"]) .editor { display: block; }

  /* Hide non-active editor sections */
  body:not([data-active-tab="preview"]) .ed-section { display: none; }
  body[data-active-tab="s-situation"] .ed-section[data-section="s-situation"],
  body[data-active-tab="s-mission"] .ed-section[data-section="s-mission"],
  body[data-active-tab="s-coord"] .ed-section[data-section="s-coord"],
  body[data-active-tab="s-photos"] .ed-section[data-section="s-photos"],
  body[data-active-tab="meta"] .ed-section[data-section="meta"],
  body[data-active-tab="cover"] .ed-section[data-section="cover"],
  body[data-active-tab="sitac"] .ed-section[data-section="sitac"],
  body[data-active-tab="mission"] .ed-section[data-section="mission"],
  body[data-active-tab="radio"] .ed-section[data-section="radio"],
  body[data-active-tab="phases"] .ed-section[data-section="phases"],
  body[data-active-tab="roster"] .ed-section[data-section="roster"],
  body[data-active-tab="charts"] .ed-section[data-section="charts"],
  body[data-active-tab="annexes"] .ed-section[data-section="annexes"],
  body[data-active-tab="wing"] .ed-section[data-section="wing"] {
    display: block;
    border: none;
  }

  /* Active section: hide summary, force content visible */
  body[data-active-tab] .ed-section > summary { display: none; }
  body[data-active-tab] .ed-section > .ed-content {
    display: flex !important;
    padding: 0;
    padding-top: 8px;
  }

  /* Show panel header instead */
  .panel-mobile-header {
    display: flex !important;
    background: linear-gradient(90deg, var(--olive) 0%, var(--olive-dark) 100%);
    padding: 12px 14px;
    font-family: var(--f-stencil);
    font-size: 14px;
    letter-spacing: 2px;
    color: var(--amber);
    border-bottom: 1px solid var(--amber-dark);
    margin: -16px -16px 12px -16px;
  }

  .tab-bar { display: flex; }

  /* Preview adapts: scale to fit width */
  .preview-wrap { padding: 16px 8px 30px 8px; }
  .page {
    width: 794px; /* FIX kraft tablette : largeur fixe pour que applyPreviewScale() puisse scaler correctement */
    transform-origin: top center;
    /* JS will apply scale */
    padding: 22px 24px 50px 24px;
    min-height: auto;
  }
}
.panel-mobile-header { display: none; }

/* Mode desktop sur tablette paysage / petits écrans (Xiaomi Pad 6, iPad Pro, etc.)
   Comprime la toolbar pour qu'elle tienne sur les viewports 1100-1366px
   sans changer la bascule UX desktop ↔ tablette.
   Reproduit le mode icon-only des boutons (déjà actif sous 1100px) et
   conserve le badge .tb-classif pour préserver le flavor visuel. */
@media (min-width: 1101px) and (max-width: 1366px) {
  /* Boutons en mode icon-only — comme sous 1100px */
  .tb-btn .tb-btn-label { display: none; }
  .tb-btn { padding: 0 10px; }

  /* Sélecteur de thème compressé (la liste déroulante reste lisible au clic) */
  .tb-select {
    max-width: 130px;
    padding: 0 28px 0 10px;
    text-overflow: ellipsis;
    overflow: hidden;
  }
}

/* PHONE */
@media (max-width: 600px) {
  .tb-brand { font-size: 11px; letter-spacing: 1px; padding-right: 8px; margin-right: 2px; }
  .tb-brand::before { width: 6px; height: 6px; }
  .tb-btn { padding: 0 8px; min-width: 40px; height: 38px; }
  .tb-btn svg { width: 14px; height: 14px; }
  .tab-bar button { font-size: 9px; min-height: 50px; }
  .tab-bar button .tab-ico { font-size: 14px; }
  .editor { padding: 12px 12px 24px 12px; }
  .ed-field-row { grid-template-columns: 1fr; }
  .phase-bar { grid-template-columns: 40px 1fr 40px 40px 40px 40px; }
  .tb-version { display: none; }
}

/* ============= EXPORT MODAL ============= */
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
  color: var(--ink, #2a2a2a);
  border: 2px solid var(--ink, #2a2a2a);
  border-radius: 4px;
  padding: 24px 28px;
  max-width: 520px;
  width: 100%;
  box-shadow: 0 8px 40px rgba(0, 0, 0, 0.5);
  font-family: 'Roboto Mono', monospace;
}
.export-modal-close {
  position: absolute;
  top: 8px;
  right: 12px;
  background: none;
  border: none;
  color: var(--ink, #2a2a2a);
  font-size: 24px;
  line-height: 1;
  cursor: pointer;
  padding: 4px 8px;
  font-family: inherit;
}
.export-modal-close:hover { color: var(--amber, #c8901f); }
.export-modal h2 {
  font-family: 'Stardos Stencil', sans-serif;
  font-size: 22px;
  letter-spacing: 2px;
  margin: 0 0 4px;
  text-transform: uppercase;
}
.export-modal-subtitle {
  font-size: 12px;
  opacity: 0.7;
  margin: 0 0 20px;
  letter-spacing: 1px;
}
.export-modal-choices {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}
.export-choice {
  background: transparent;
  border: 2px solid var(--ink, #2a2a2a);
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
.export-choice:focus-visible {
  outline: 2px solid var(--amber, #c8901f);
  outline-offset: 2px;
}
.export-choice-icon { font-size: 32px; margin-bottom: 8px; }
.export-choice-label {
  font-family: 'Stardos Stencil', sans-serif;
  font-size: 18px;
  letter-spacing: 2px;
  margin-bottom: 6px;
}
.export-choice-desc {
  font-size: 11px;
  opacity: 0.75;
  letter-spacing: 0.5px;
  line-height: 1.35;
}
/* Panneau PNG (step 2) */
.export-png-config h3 {
  font-family: 'Stardos Stencil', sans-serif;
  font-size: 14px;
  letter-spacing: 2px;
  margin: 0 0 10px;
  text-transform: uppercase;
}
.export-png-actions-top {
  display: flex;
  gap: 8px;
  margin-bottom: 10px;
}
.export-png-toggle {
  background: transparent;
  border: 1px solid var(--ink, #2a2a2a);
  padding: 4px 10px;
  font-family: inherit;
  font-size: 11px;
  letter-spacing: 0.5px;
  cursor: pointer;
  color: inherit;
  border-radius: 2px;
}
.export-png-toggle:hover {
  background: rgba(0, 0, 0, 0.06);
  border-color: var(--amber, #c8901f);
}
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
  font-family: 'Stardos Stencil', sans-serif;
  letter-spacing: 1px;
  min-width: 60px;
}
.export-png-page-hint {
  opacity: 0.7;
  font-size: 11px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.export-png-actions-bottom {
  display: flex;
  justify-content: space-between;
  gap: 10px;
}
.export-png-back, .export-png-go {
  background: transparent;
  border: 2px solid var(--ink, #2a2a2a);
  padding: 8px 18px;
  font-family: 'Stardos Stencil', sans-serif;
  letter-spacing: 2px;
  font-size: 13px;
  cursor: pointer;
  color: inherit;
  border-radius: 2px;
  text-transform: uppercase;
}
.export-png-back:hover {
  background: rgba(0, 0, 0, 0.05);
}
.export-png-go {
  background: var(--amber, #c8901f);
  color: var(--paper, #f4ead5);
  border-color: var(--amber, #c8901f);
}
.export-png-go:hover {
  background: var(--ink, #2a2a2a);
  border-color: var(--ink, #2a2a2a);
}
.export-png-go:disabled {
  opacity: 0.4;
  cursor: not-allowed;
  pointer-events: none;
}

/* Mobile : grille 2 colonnes → 1 colonne */
@media (max-width: 600px) {
  .export-modal-choices { grid-template-columns: 1fr; }
  .export-modal-panel { padding: 18px 20px; }
}

/* ===========================================================
   WARNING débordement — aperçu UNIQUEMENT (chatE étape A)
   Bandeau rouge transparent en bas des pages tronquées.
   Masqué en print (CSS only, jamais via JS conditionnel).
   =========================================================== */
.p-overflow-warning {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background: rgba(180, 30, 30, 0.78);
  color: #fff;
  font-family: var(--f-condensed, 'Roboto Condensed', sans-serif);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 2px;
  text-transform: uppercase;
  padding: 5px 12px;
  text-align: center;
  z-index: 50;
  pointer-events: none;
  backdrop-filter: blur(1px);
}

/* Hide warning in print — CSS only, jamais conditionnel JS */
@media print {
  .p-overflow-warning { display: none !important; }
}

/* ===========================================================
   .page--for-png — (chatE étape B)
   Réplique textuellement les règles @media print de .page,
   en CSS standard (sans @media print), pour application
   sur le clone hors-écran lors de l'export PNG.
   À MAINTENIR SYNCHRONISÉ avec @media print .page { ... }.
   =========================================================== */
.page--for-png {
  width: 794px !important;
  height: 1123px !important;
  min-height: 0 !important;
  max-height: 1123px !important;
  overflow: hidden !important;
  margin: 0 !important;
  padding: 28px 36px 50px 36px !important;
  box-shadow: none !important;
  transform: none !important;
}
/* Le bandeau warning est masqué sur le clone PNG — CSS only, jamais via JS */
.page--for-png .p-overflow-warning {
  display: none !important;
}

/* ============ PRINT ============ */
@media print {
  body { background: white; overflow: visible; }
  .toolbar, .editor, .tab-bar, .export-modal { display: none !important; }
  .app { position: static; display: block; bottom: auto; }
  .preview-wrap {
    position: static; padding: 0; overflow: visible;
    background: white; display: block !important;
  }
  .page {
    /* Exact A4 — no overflow onto next page */
    width: 210mm;
    height: 297mm;
    min-height: 0 !important;
    max-height: 297mm;
    overflow: hidden;
    margin: 0;
    padding: 7.4mm 9.5mm 13mm 9.5mm;  /* miroir mm du padding écran 28/36/50/36px (chatE étape A) */
    box-shadow: none;
    page-break-after: always;
    break-after: page;
    transform: none !important;
    /* SVG kraft texture — couvre exactement la page A4 (par thème via --kraft-bg) */
    background-color: var(--page-bg);
    background-image: var(--kraft-bg);
    background-size: 100% 100%;
    background-repeat: no-repeat;
    background-position: top left;
    background-attachment: scroll;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
    color-adjust: exact;
    position: relative;
    z-index: auto;
  }
  /* Contenu toujours au-dessus du fond raster */
  .page > * {
    position: relative;
    z-index: 1;
  }
  .page:last-child { page-break-after: auto; break-after: auto; }

  /* Roster: identical layout in screen and print (same single <table>),
     so no print-specific overrides needed for roster anymore. */

  /* Keep footer anchored to bottom in print */
  .p-footer {
    position: absolute;
    bottom: 8mm; left: 14mm; right: 14mm;
    padding-top: 4px;
  }
  /* Simplify other CSS backgrounds that can cause artifacts */
  .p-bullets li::before,
  .p-bullets-num li::before { background: var(--paper); }
  .radio-block-name { background: var(--paper-light); }

  @page {
    size: A4 portrait;
    margin: 0;
  }
}
"""

CSS = CSS.replace('__STARDOS_400__', A['STARDOS_400'])
CSS = CSS.replace('__STARDOS_700__', A['STARDOS_700'])
CSS = CSS.replace('__SPECIAL_ELITE__', A['SPECIAL_ELITE'])
CSS = CSS.replace('__ROBOTO_MONO_400__', A['ROBOTO_MONO_400'])
CSS = CSS.replace('__OSWALD_500__', A['OSWALD_500'])  # 2c
CSS = CSS.replace('__OSWALD_600__', A['OSWALD_600'])
CSS = CSS.replace('__OSWALD_700__', A['OSWALD_700'])

# ════════════════════════════════════════════════════════════════════
# Bloc HTML (ex-build_html.py) — CSS déjà en mémoire, pas de lecture fichier
# ════════════════════════════════════════════════════════════════════

import base64
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))

APP_VERSION = "2.4.1"

ASSETS_PATH = os.path.join(HERE, 'assets.json')
if not os.path.isfile(ASSETS_PATH):
    raise SystemExit(f"[ERREUR] Entrée manquante : {ASSETS_PATH} (assets.json attendu à la racine du dépôt)")
with open(ASSETS_PATH) as f:
    A = json.load(f)

# CSS déjà en mémoire depuis le bloc CSS

HTML = r"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0, viewport-fit=cover">
<meta name="theme-color" content="#1a1e10">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<title>MY WING // GÉNÉRATEUR DE BRIEFING</title>
<style>
__CSS__
</style>
<!-- html2canvas v1.4.1 — embarqué pour export PNG kneeboard (étape B) -->
<script>__LIB_HTML2CANVAS__</script>
<!-- JSZip v3.10.1 — embarqué pour export ZIP multi-pages (étape B) -->
<script>__LIB_JSZIP__</script>
</head>
<body data-theme="cw-nato" data-format="simple">

<!-- ===== TOOLBAR ===== -->
<header class="toolbar" role="toolbar" aria-label="Actions principales">
  <div class="tb-brand"><span class="tb-brand-main">MY WING</span> <span class="tb-brand-sub">░ BRIEFING</span></div>
  <div class="tb-seg" id="format-seg" role="group" data-i18n-title="toolbar.format.tooltip" title="Choisir le format du briefing" data-i18n-aria-label="toolbar.format.tooltip" aria-label="Choisir le format du briefing">
    <button type="button" class="seg-btn" data-format="full" aria-pressed="false"><span class="seg-long" data-i18n="toolbar.format.full">Brief complet</span><span class="seg-short" data-i18n="toolbar.format.fullShort">Complet</span></button>
    <button type="button" class="seg-btn" data-format="simple" aria-pressed="true"><span class="seg-long" data-i18n="toolbar.format.simple">Brief simplifié</span><span class="seg-short" data-i18n="toolbar.format.simpleShort">Simplifié</span></button>
  </div>
  <button class="tb-btn" id="btn-save" data-i18n-title="toolbar.save.tooltip" title="Exporter le briefing en JSON">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/></svg>
    <span class="tb-btn-label" data-i18n="toolbar.save">Sauver</span>
  </button>
  <button class="tb-btn" id="btn-load" data-i18n-title="toolbar.load.tooltip" title="Charger un briefing JSON">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
    <span class="tb-btn-label" data-i18n="toolbar.load">Charger</span>
  </button>
  <input type="file" id="file-load" accept=".json,application/json" hidden>
  <button class="tb-btn" id="btn-print" data-i18n-title="toolbar.export.tooltip" title="Exporter en PDF ou PNG (kneeboard DCS)">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 6 2 18 2 18 9"/><path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/><rect x="6" y="14" width="12" height="8"/></svg>
    <span class="tb-btn-label" data-i18n="toolbar.export">Exporter</span>
  </button>
  <button class="tb-btn danger" id="btn-reset" data-i18n-title="toolbar.reset.tooltip" title="Vider le briefing (repartir d'une page blanche)">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
    <span class="tb-btn-label" data-i18n="toolbar.reset">Reset</span>
  </button>
  <button class="tb-btn" id="btn-example" data-i18n-title="toolbar.example.tooltip" title="Charger le briefing d'exemple (remplace le briefing en cours)">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="8" y1="13" x2="16" y2="13"/><line x1="8" y1="17" x2="16" y2="17"/></svg>
    <span class="tb-btn-label" data-i18n="toolbar.example">Exemple</span>
  </button>
  <select class="tb-select" id="theme-select" data-i18n-title="toolbar.theme.tooltip" title="Thème graphique">
    <option value="cw-nato"     data-i18n="theme.cw-nato">Cold War OTAN</option>
    <option value="cw-soviet"   data-i18n="theme.cw-soviet">Cold War Soviétique</option>
    <option value="modern-nato" data-i18n="theme.modern-nato">OTAN moderne</option>
    <option value="modern-east" data-i18n="theme.modern-east">Bloc Est moderne</option>
  </select>
  <button class="tb-lang-btn" id="btn-lang" data-i18n-title="toolbar.lang.tooltip" title="Switch language / Changer de langue">🇬🇧</button>
  <div class="tb-spacer"></div>
  <div class="tb-classif">CLASSIFIED // FOR EYES ONLY</div>
  <span class="tb-version">v__APP_VERSION__</span>
</header>

<!-- ===== EXPORT MODAL ===== -->
<div class="export-modal" id="export-modal" hidden role="dialog" aria-labelledby="export-modal-title" aria-modal="true">
  <div class="export-modal-backdrop" id="export-modal-backdrop"></div>
  <div class="export-modal-panel" role="document">
    <button class="export-modal-close" id="export-modal-close" data-i18n-aria-label="modal.export.close" aria-label="Fermer">×</button>
    <h2 id="export-modal-title" data-i18n="modal.export.title">Exporter le briefing</h2>
    <p class="export-modal-subtitle" data-i18n="modal.export.subtitle">Choisissez le format de sortie</p>
    <div class="export-modal-choices">
      <button class="export-choice" id="export-choice-pdf" type="button">
        <div class="export-choice-icon">🖨</div>
        <div class="export-choice-label">PDF</div>
        <div class="export-choice-desc" data-i18n="modal.export.pdf.desc">Impression système · Toutes les pages</div>
      </button>
      <button class="export-choice" id="export-choice-png" type="button">
        <div class="export-choice-icon">🖼</div>
        <div class="export-choice-label">PNG</div>
        <div class="export-choice-desc" data-i18n="modal.export.png.desc">Kneeboard DCS · 1588×2246, A4</div>
      </button>
    </div>
    <!-- Le panneau PNG (sélecteur de pages) apparaît ici en step 2 — implémenté étape B -->
    <div class="export-png-config" id="export-png-config" hidden>
      <h3 data-i18n="modal.export.png.pages">Pages à exporter</h3>
      <div class="export-png-actions-top">
        <button type="button" class="export-png-toggle" id="export-png-all" data-i18n="modal.export.png.checkAll">Tout cocher</button>
        <button type="button" class="export-png-toggle" id="export-png-none" data-i18n="modal.export.png.uncheckAll">Tout décocher</button>
      </div>
      <div class="export-png-list" id="export-png-list">
        <!-- checkboxes par page injectées dynamiquement -->
      </div>
      <div class="export-png-actions-bottom">
        <button type="button" class="export-png-back" id="export-png-back" data-i18n="modal.export.png.back">← Retour</button>
        <button type="button" class="export-png-go" id="export-png-go"><span data-i18n="modal.export.png.go">Exporter</span> <span id="export-png-count"></span></button>
      </div>
    </div>
  </div>
</div>

<!-- ===== APP ===== -->
<div class="app" id="app">

  <!-- ============ EDITOR ============ -->
  <aside class="editor" id="editor">

    <!-- 00 META -->
    <details class="ed-section" data-section="meta" open>
      <summary data-i18n="editor.meta.summary">00 ░ MÉTADONNÉES</summary>
      <div class="ed-content">
        <div class="panel-mobile-header" data-i18n="editor.meta.summary">00 ░ MÉTADONNÉES</div>
        <div class="ed-field-row">
          <div class="ed-field"><label data-i18n="editor.meta.operation">Opération</label><input data-bind="meta.operation" type="text" placeholder="FOOTHOLD"></div>
          <div class="ed-field"><label data-i18n="editor.meta.missionCode">Mission code</label><input data-bind="meta.mission" type="text" placeholder="M3"></div>
        </div>
        <div class="ed-field-row">
          <div class="ed-field"><label data-i18n="editor.meta.date">Date mission</label><input data-bind="meta.date" type="date"></div>
          <div class="ed-field"><label data-i18n="editor.meta.classification">Classification</label>
            <select data-bind="meta.classification">
              <option value="confidential"    data-i18n="classif.confidential">CONFIDENTIEL DÉFENSE</option>
              <option value="secret"          data-i18n="classif.secret">SECRET DÉFENSE</option>
              <option value="top-secret"      data-i18n="classif.top-secret">TRÈS SECRET</option>
              <option value="unclassified"    data-i18n="classif.unclassified">NON CLASSIFIÉ</option>
              <option value="nato-restricted" data-i18n="classif.nato-restricted">NATO RESTRICTED</option>
              <option value="nato-secret"     data-i18n="classif.nato-secret">NATO SECRET</option>
            </select>
          </div>
        </div>
        <div class="ed-field" data-fmt="simple"><label data-i18n="editor.meta.time">Heure (Z)</label><input data-bind="meta.time" type="text" placeholder="1000Z"></div>
        <div class="ed-field"><label data-i18n="editor.meta.docRef">Référence document</label><input data-bind="meta.docRef" type="text" placeholder="KHR26-FH-M3-1989"></div>
        <div class="ed-help" data-i18n="editor.meta.help">Métadonnées présentes dans tous les pieds de page.</div>
      </div>
    </details>

    <!-- S1 SITUATION (brief simplifié) -->
    <details class="ed-section" data-section="s-situation" data-fmt="simple" open>
      <summary data-i18n="editor.simple.situation.summary">01 ░ SITUATION</summary>
      <div class="ed-content">
        <div class="panel-mobile-header" data-i18n="editor.simple.situation.summary">01 ░ SITUATION</div>
        <div class="ed-field">
          <label data-i18n="editor.sitac.points">Points de situation</label>
          <div class="ed-list" data-list="sitac.points"></div>
          <button type="button" class="ed-btn-add" data-add="sitac.points" data-i18n="editor.sitac.addPoint">+ Ajouter un point</button>
        </div>
        <div class="ed-field">
          <label data-i18n="editor.simple.map">Carte (image)</label>
          <label class="ed-img-zone" data-img-bind="sitac.mapImage">
            <input type="file" accept="image/*">
            <span class="img-text" data-i18n="editor.imgZone.tap">▲ TOUCHER POUR CHARGER UNE CARTE ▲</span>
          </label>
        </div>
        <div class="ed-field-row">
          <div class="ed-field"><label data-i18n="editor.mission.tanks">Menaces — Chars</label><input data-bind="mission.threats.tanks" type="text"></div>
          <div class="ed-field"><label data-i18n="editor.mission.apc">Menaces — APC</label><input data-bind="mission.threats.apc" type="text"></div>
        </div>
        <div class="ed-field-row">
          <div class="ed-field"><label data-i18n="editor.mission.aaa">Menaces — AAA</label><input data-bind="mission.threats.aaa" type="text"></div>
          <div class="ed-field"><label data-i18n="editor.mission.sam">Menaces — SAM</label><input data-bind="mission.threats.sam" type="text"></div>
        </div>
        <div class="ed-field"><label data-i18n="editor.mission.threatsNote">Note menaces (libre)</label><textarea data-bind="mission.threats.note" rows="2"></textarea></div>
      </div>
    </details>

    <!-- S2 MISSION (brief simplifié) : objectifs + vols -->
    <details class="ed-section" data-section="s-mission" data-fmt="simple" open>
      <summary data-i18n="editor.simple.mission.summary">02 ░ MISSION</summary>
      <div class="ed-content">
        <div class="panel-mobile-header" data-i18n="editor.simple.mission.summary">02 ░ MISSION</div>
        <div class="ed-field">
          <label data-i18n="editor.mission.objectives">Objectifs principaux</label>
          <div class="ed-list" data-list="mission.objectives"></div>
          <button type="button" class="ed-btn-add" data-add="mission.objectives" data-i18n="editor.mission.addObjective">+ Ajouter un objectif</button>
        </div>
        <div class="ed-field">
          <label data-i18n="editor.simple.flights">Vols</label>
          <div class="ed-img-list" id="s-flights-list"></div>
          <button type="button" class="ed-btn-add" id="s-flight-add" data-i18n="editor.simple.addFlight">+ Ajouter un vol</button>
        </div>
        <div class="ed-field">
          <label data-i18n="editor.targets.label">Cibles</label>
          <div class="ed-targets" id="s-targets-list"></div>
          <button type="button" class="ed-btn-add" id="s-target-add" data-i18n="editor.targets.add">+ Ajouter une cible</button>
        </div>
      </div>
    </details>

    <!-- S3 COORDINATION (brief simplifié) : fréquences, terrains, METAR -->
    <details class="ed-section" data-section="s-coord" data-fmt="simple" open>
      <summary data-i18n="editor.simple.coord.summary">03 ░ COORDINATION</summary>
      <div class="ed-content">
        <div class="panel-mobile-header" data-i18n="editor.simple.coord.summary">03 ░ COORDINATION</div>
        <div class="ed-field">
          <label data-i18n="simple.freq">Fréquences</label>
          <div id="s-radio-items-list"></div>
          <button type="button" class="ed-btn-add" id="s-radio-item-add" data-i18n="editor.radio.addItem">+ Ajouter un item</button>
        </div>
        <div class="ed-field">
          <label data-i18n="simple.airfields">Terrains</label>
          <div id="s-airfields-list"></div>
          <button type="button" class="ed-btn-add" id="s-airfield-add" data-i18n="editor.mission.addFarp">+ Ajouter une base</button>
        </div>
        <div class="ed-field">
          <label data-i18n="editor.sitac.metar">METAR</label>
          <div style="display:flex;gap:8px;align-items:center;">
            <input data-bind="sitac.metar" type="text" placeholder="LCRA 221000Z 18002KT 9999 SCT082 20/15 Q1013" style="flex:1;">
            <button type="button" class="ed-btn-add" id="s-metar-assistant-btn" data-i18n="editor.sitac.metarAssistant">🛠 Assistant METAR</button>
          </div>
          <div id="s-metar-slot"></div>
        </div>
      </div>
    </details>

    <!-- S4 PHOTOS (brief simplifié) -->
    <details class="ed-section" data-section="s-photos" data-fmt="simple" open>
      <summary data-i18n="editor.simple.photos.summary">04 ░ PHOTOS</summary>
      <div class="ed-content">
        <div class="panel-mobile-header" data-i18n="editor.simple.photos.summary">04 ░ PHOTOS</div>
        <div class="ed-img-list" id="s-photos-list"></div>
        <button type="button" class="ed-btn-add" id="s-photo-add" data-i18n="editor.simple.addPhoto">+ Ajouter une photo</button>
      </div>
    </details>

    <!-- 01 COVER -->
    <details class="ed-section" data-section="cover" data-fmt="full">
      <summary data-i18n="editor.cover.summary">01 ░ OPÉRATION (COUVERTURE)</summary>
      <div class="ed-content">
        <div class="panel-mobile-header" data-i18n="editor.cover.summaryShort">01 ░ OPÉRATION</div>
        <div class="ed-field"><label data-i18n="editor.cover.title">Titre opération</label><input data-bind="cover.title" type="text" placeholder="OPERATION FOOTHOLD"></div>
        <div class="ed-field"><label data-i18n="editor.cover.narrative">Récit / Contexte</label><textarea data-bind="cover.narrative" rows="6"></textarea></div>
        <div class="ed-field">
          <label data-i18n="editor.cover.map">Carte d'opération (image)</label>
          <label class="ed-img-zone" data-img-bind="cover.mapImage">
            <input type="file" accept="image/*">
            <span class="img-text" data-i18n="editor.imgZone.tap">▲ TOUCHER POUR CHARGER UNE CARTE ▲</span>
          </label>
        </div>
      </div>
    </details>

    <!-- 02 SITAC -->
    <details class="ed-section" data-section="sitac" data-fmt="full">
      <summary data-i18n="editor.sitac.summary">02 ░ SITAC</summary>
      <div class="ed-content">
        <div class="panel-mobile-header" data-i18n="editor.sitac.summary">02 ░ SITAC</div>
        <div class="ed-field"><label data-i18n="editor.sitac.date">Date SITAC (affichée)</label><input data-bind="sitac.date" type="text" placeholder="22-03-1989"></div>
        <div class="ed-field">
          <label data-i18n="editor.sitac.points">Points de situation</label>
          <div class="ed-list" data-list="sitac.points"></div>
          <button type="button" class="ed-btn-add" data-add="sitac.points" data-i18n="editor.sitac.addPoint">+ Ajouter un point</button>
        </div>
        <div class="ed-field">
          <label data-i18n="editor.sitac.metar">METAR</label>
          <div style="display:flex;gap:8px;align-items:center;">
            <input data-bind="sitac.metar" type="text" placeholder="LCRA 221000Z 18002KT 9999 SCT082 20/15 Q1013" style="flex:1;">
            <button type="button" class="ed-btn-add" id="metar-assistant-btn" data-i18n="editor.sitac.metarAssistant">🛠 Assistant METAR</button>
          </div>
        </div>
        <!-- Panneau Assistant METAR (10A + 10C) -->
        <details class="metar-panel" id="metar-assistant-panel" style="display:none;">
          <summary data-i18n="editor.sitac.metarAssistant">🛠 Assistant METAR</summary>
          <div class="ed-content" id="metar-assistant-content">
            <!-- Rendu dynamique par renderMetarAssistant() -->
          </div>
        </details>
        <div class="ed-field">
          <label data-i18n="editor.sitac.map">Carte SITAC (image)</label>
          <label class="ed-img-zone" data-img-bind="sitac.mapImage">
            <input type="file" accept="image/*">
            <span class="img-text" data-i18n="editor.imgZone.tap">▲ TOUCHER POUR CHARGER UNE CARTE ▲</span>
          </label>
        </div>
      </div>
    </details>

    <!-- 03 MISSION -->
    <details class="ed-section" data-section="mission" data-fmt="full">
      <summary data-i18n="editor.mission.summary">03 ░ APERÇU MISSION</summary>
      <div class="ed-content">
        <div class="panel-mobile-header" data-i18n="editor.mission.summary">03 ░ APERÇU MISSION</div>
        <div class="ed-field">
          <label data-i18n="editor.mission.objectives">Objectifs principaux</label>
          <div class="ed-list" data-list="mission.objectives"></div>
          <button type="button" class="ed-btn-add" data-add="mission.objectives" data-i18n="editor.mission.addObjective">+ Ajouter un objectif</button>
        </div>
        <div class="ed-field">
          <label data-i18n="editor.targets.label">Cibles</label>
          <div class="ed-targets" id="targets-list"></div>
          <button type="button" class="ed-btn-add" id="target-add" data-i18n="editor.targets.add">+ Ajouter une cible</button>
        </div>
        <div class="ed-field">
          <label data-i18n="editor.mission.farp">FARP &amp; Aéroports</label>
          <div id="airfields-list"></div>
          <button type="button" class="ed-btn-add" id="airfield-add" data-i18n="editor.mission.addFarp">+ Ajouter une base</button>
        </div>
        <div class="ed-field-row">
          <div class="ed-field"><label data-i18n="editor.mission.tanks">Menaces — Chars</label><input data-bind="mission.threats.tanks" type="text"></div>
          <div class="ed-field"><label data-i18n="editor.mission.apc">Menaces — APC</label><input data-bind="mission.threats.apc" type="text"></div>
        </div>
        <div class="ed-field-row">
          <div class="ed-field"><label data-i18n="editor.mission.aaa">Menaces — AAA</label><input data-bind="mission.threats.aaa" type="text"></div>
          <div class="ed-field"><label data-i18n="editor.mission.sam">Menaces — SAM</label><input data-bind="mission.threats.sam" type="text"></div>
        </div>
        <div class="ed-field"><label data-i18n="editor.mission.threatsNote">Note menaces (libre)</label><textarea data-bind="mission.threats.note" rows="2"></textarea></div>
      </div>
    </details>

    <!-- 04 RADIO PLAN -->
    <details class="ed-section" data-section="radio" data-fmt="full" open>
      <summary data-i18n="editor.radio.summary">04 ░ PLAN RADIO</summary>
      <div class="ed-content">
        <div class="panel-mobile-header" data-i18n="editor.radio.summary">04 ░ PLAN RADIO</div>
        <div class="ed-field">
          <label data-i18n="editor.radio.items">Items radio (max 6) — affichés sur la page 3</label>
          <div id="radio-items-list"></div>
          <button type="button" class="ed-btn-add" id="radio-item-add" data-i18n="editor.radio.addItem">+ Ajouter un item</button>
        </div>
        <div class="ed-help" data-i18n="editor.radio.help">Définissez ici les fréquences communes (ATC, MISSION, Groupes...). Vous les assignerez ensuite aux canaux radio par appareil ci-dessous.</div>
        <div class="ed-field" style="margin-top:8px;">
          <label data-i18n="editor.radio.aircraft">Plans radio par appareil</label>
          <div id="radio-aircraft-list"></div>
          <button type="button" class="ed-btn-add" id="radio-aircraft-add" data-i18n="editor.radio.addAircraft">+ Ajouter un appareil</button>
        </div>
        <div class="ed-help" data-i18n="editor.radio.helpAircraft">Pour chaque appareil, configurez les radios et leurs canaux. Si une image est fournie, elle remplace la table générée.</div>
      </div>
    </details>

    <!-- 05 PHASES -->
    <details class="ed-section" data-section="phases" data-fmt="full" open>
      <summary data-i18n="editor.phases.summary">05 ░ MISSIONS</summary>
      <div class="ed-content">
        <div class="panel-mobile-header" data-i18n="editor.phases.summary">05 ░ MISSIONS</div>
        <div class="phase-bar">
          <button type="button" id="phase-prev" data-i18n-title="editor.phases.prev" title="Mission précédente">◄</button>
          <div class="phase-indicator" id="phase-indicator">—</div>
          <button type="button" id="phase-next" data-i18n-title="editor.phases.next" title="Mission suivante">►</button>
          <button type="button" id="phase-add" data-i18n-title="editor.phases.add" title="Ajouter une mission">+</button>
          <button type="button" id="phase-dup" data-i18n-title="editor.phases.dup" title="Dupliquer cette mission">⎘</button>
          <button type="button" id="phase-up" data-i18n-title="editor.phases.up" title="Monter la mission">↑</button>
          <button type="button" id="phase-down" data-i18n-title="editor.phases.down" title="Descendre la mission">↓</button>
          <button type="button" class="danger" id="phase-rm" data-i18n-title="editor.phases.remove" title="Supprimer cette mission">×</button>
        </div>
        <div id="phase-editor"></div>
      </div>
    </details>

    <!-- 07 ÉQUIPAGE -->
    <details class="ed-section" data-section="roster" data-fmt="full">
      <summary data-i18n="editor.roster.summary">07 ░ ÉQUIPAGE</summary>
      <div class="ed-content">
        <div class="panel-mobile-header" data-i18n="editor.roster.summary">07 ░ ÉQUIPAGE</div>
        <div class="ed-help" style="margin-bottom:10px;" data-i18n="editor.roster.help">
          Définissez les pilotes par groupe ou sous-groupe. Une page d'ordre de bataille sera générée après l'aperçu mission si au moins un pilote est renseigné.
        </div>
        <div id="roster-groups-list"></div>
        <button type="button" class="ed-btn-add" id="roster-group-add" data-i18n="editor.roster.addGroup">+ Ajouter un groupe</button>
      </div>
    </details>

    <!-- 08 CHARTS -->
    <details class="ed-section" data-section="charts" data-fmt="full">
      <summary data-i18n="editor.charts.summary">08 ░ CHARTS</summary>
      <div class="ed-content">
        <div class="panel-mobile-header" data-i18n="editor.charts.summary">08 ░ CHARTS</div>
        <div id="charts-list"></div>
        <button type="button" class="ed-btn-add" id="chart-add" data-i18n="editor.charts.add">+ Ajouter une chart</button>
      </div>
    </details>

    <!-- 09 ANNEXES -->
    <details class="ed-section" data-section="annexes" data-fmt="full">
      <summary data-i18n="editor.annexes.summary">09 ░ ANNEXES</summary>
      <div class="ed-content">
        <div class="panel-mobile-header" data-i18n="editor.annexes.summary">09 ░ ANNEXES</div>
        <div id="annexes-list"></div>
        <button type="button" class="ed-btn-add" id="annexe-add" data-i18n="editor.annexes.add">+ Ajouter une annexe</button>
      </div>
    </details>

    <!-- 10 WING — read-only consumer (édition dans HQ) -->
    <details class="ed-section" data-section="wing" data-fmt="full">
      <summary data-i18n="editor.wing.summary">10 ░ CONFIGURATION WING</summary>
      <div class="ed-content">
        <div class="panel-mobile-header" data-i18n="editor.wing.summaryShort">10 ░ CONFIG WING</div>

        <!-- Informations wing courantes (read-only) -->
        <div id="wing-ro-info" class="wing-ro-info"></div>

        <!-- Filet d'import standalone / fallback -->
        <div class="wing-actions">
          <label class="wing-action-btn wing-action-import" data-i18n-title="editor.wing.importTooltip" title="Importer un fichier wing_config.json">
            <input type="file" accept=".json" id="wing-import-input">
            <span data-i18n="editor.wing.import">📥 Importer config</span>
          </label>
          <button type="button" class="wing-action-btn wing-action-reset" id="wing-reset-btn" data-i18n="editor.wing.reset">
            ♻ Réinitialiser
          </button>
        </div>

        <p class="wing-hq-hint" data-i18n="editor.wing.hqHint">✦ Édition complète disponible dans HQ</p>

      </div>
    </details>

    <div class="ed-help" data-wing-label style="text-align:center; padding:12px 4px;">
      ◆ MY WING ◆<br>
      <span data-i18n="editor.autoSave">Sauvegarde locale automatique</span><br>
      <span data-i18n="editor.exportTip">Export JSON pour conserver vos templates</span>
    </div>
  </aside>

  <!-- ============ PREVIEW ============ -->
  <main class="preview-wrap" id="preview-wrap">
    <div id="preview"></div>
  </main>

</div>

<!-- ============ MOBILE TAB BAR ============ -->
<nav class="tab-bar" id="tab-bar" role="tablist" aria-label="Sections du briefing">
  <button type="button" data-tab="meta" role="tab"><span class="tab-ico">⚙</span><span data-i18n="tab.meta">Méta</span></button>
  <button type="button" data-tab="s-situation" data-fmt="simple" role="tab"><span class="tab-ico">▣</span><span data-i18n="tab.simple.situation">Situation</span></button>
  <button type="button" data-tab="s-mission" data-fmt="simple" role="tab"><span class="tab-ico">✈</span><span data-i18n="tab.mission">Mission</span></button>
  <button type="button" data-tab="s-coord" data-fmt="simple" role="tab"><span class="tab-ico">📻</span><span data-i18n="tab.simple.coord">Coordination</span></button>
  <button type="button" data-tab="s-photos" data-fmt="simple" role="tab"><span class="tab-ico">🖼</span><span data-i18n="tab.simple.photos">Photos</span></button>
  <button type="button" data-tab="cover" data-fmt="full" role="tab"><span class="tab-ico">◉</span><span data-i18n="tab.cover">Couv.</span></button>
  <button type="button" data-tab="sitac" data-fmt="full" role="tab"><span class="tab-ico">▣</span><span data-i18n="tab.sitac">SITAC</span></button>
  <button type="button" data-tab="mission" data-fmt="full" role="tab"><span class="tab-ico">✈</span><span data-i18n="tab.mission">Mission</span></button>
  <button type="button" data-tab="radio" data-fmt="full" role="tab"><span class="tab-ico">📻</span><span data-i18n="tab.radio">Radio</span></button>
  <button type="button" data-tab="phases" data-fmt="full" role="tab"><span class="tab-ico">⊕</span><span data-i18n="tab.phases">Missions</span></button>
  <button type="button" data-tab="roster" data-fmt="full" role="tab"><span class="tab-ico">👤</span><span data-i18n="tab.roster">Équipage</span></button>
  <button type="button" data-tab="charts" data-fmt="full" role="tab"><span class="tab-ico">🗺</span><span data-i18n="tab.charts">Charts</span></button>
  <button type="button" data-tab="annexes" data-fmt="full" role="tab"><span class="tab-ico">📎</span><span data-i18n="tab.annexes">Annexes</span></button>
  <button type="button" data-tab="wing" data-fmt="full" role="tab"><span class="tab-ico">🛡</span><span data-i18n="tab.wing">Wing</span></button>
  <button type="button" data-tab="preview" role="tab"><span class="tab-ico">◈</span><span data-i18n="tab.preview">Aperçu</span></button>
</nav>

<div class="toast" id="toast" role="status" aria-live="polite"></div>

<!-- ============ EMBEDDED WING CONFIG (generic default) ============ -->
<script>
/* DEFAULT_WING_CONFIG is generated by build_html.py.
   It contains the wing branding + squadrons + base64-encoded logos.
   The 4th VEAW config is distributed separately as wing_config_4th-veaw.json.
   See `wing_config.json` schema in DOCS for the full format. */
const DEFAULT_WING_CONFIG = JSON.parse(__DEFAULT_WING_CONFIG__);
</script>

<!-- ============ APPLICATION ============ -->
<script>
'use strict';

/* =====================================================
   DCS WORLD BRIEFING GENERATOR v2
   Tablet-ready, offline-first
   ===================================================== */

const STORAGE_KEY = 'khr26_briefing_state_v2';
const KEY_WING     = 'wing_config_v1';
const KEY_THEME    = 'theme_v1';
const KEY_LANG     = 'lang_v1';  // Phase 9 — i18n FR/EN
const MOBILE_BREAKPOINT = 1100;
const IMG_MAX_WIDTH = 1600;
const IMG_JPEG_QUALITY = 0.82;
const IMG_RECOMPRESS_THRESHOLD = 800 * 1024;  // 800 Ko base64 : seuil de déclenchement recompression auto

/* ============= i18n FR/EN (Phase 9 — v2.2.0) =============
   Architecture :
   - I18N : dictionnaires clés-valeurs par langue (notation pointée par domaine)
   - CURRENT_LANG : état courant ('fr' | 'en')
   - t(key) : résolution d'une clé avec fallback FR
   - initLang() : lecture localStorage + détection navigator.language
   - setLang(lang) : bascule + persistance + mise à jour DOM
   - applyI18nStatic() : peuple les éléments data-i18n* dans le DOM

   CLASSIF_LEGACY_MAP : migration des anciennes valeurs textuelles de
   meta.classification vers les clés canoniques. Les labels affichés
   sont désormais gérés par I18N (classif.*), pas stockés dans le state. */

const I18N = {
  fr: {
    // ── Toolbar ──
    'toolbar.save':           'Sauver',
    'toolbar.load':           'Charger',
    'toolbar.export':         'Exporter',
    'toolbar.reset':          'Reset',
    'toolbar.save.tooltip':   'Exporter le briefing en JSON',
    'toolbar.load.tooltip':   'Charger un briefing JSON',
    'toolbar.export.tooltip': 'Exporter en PDF ou PNG (kneeboard DCS)',
    'toolbar.reset.tooltip':  'Vider le briefing (repartir d\'une page blanche)',
    'toolbar.theme.tooltip':  'Thème graphique',
    'toolbar.lang.tooltip':   'Switch language / Changer de langue',
    // ── Document ──
    'doc.title.suffix': 'GÉNÉRATEUR DE BRIEFING',
    // ── Tab bar ──
    'tab.meta':    'Méta',
    'tab.cover':   'Couv.',
    'tab.sitac':   'SITAC',
    'tab.mission': 'Mission',
    'tab.radio':   'Radio',
    'tab.phases':  'Missions',
    'tab.roster':  'Équipage',
    'tab.charts':  'Charts',
    'tab.annexes': 'Annexes',
    'tab.wing':    'Wing',
    'tab.preview': 'Aperçu',
    // ── Modale export ──
    'modal.export.close':          'Fermer',
    'modal.export.title':          'Exporter le briefing',
    'modal.export.subtitle':       'Choisissez le format de sortie',
    'modal.export.pdf.desc':       'Impression système · Toutes les pages',
    'modal.export.png.desc':       'Kneeboard DCS · 1588×2246, A4',
    'modal.export.png.pages':      'Pages à exporter',
    'modal.export.png.checkAll':   'Tout cocher',
    'modal.export.png.uncheckAll': 'Tout décocher',
    'modal.export.png.back':       '← Retour',
    'modal.export.png.go':         'Exporter',
    'modal.export.titlePng':       'Export PNG kneeboard',
    // ── Section 00 META ──
    'editor.meta.summary':        '00 ░ MÉTADONNÉES',
    'editor.meta.operation':      'Opération',
    'editor.meta.missionCode':    'Mission code',
    'editor.meta.date':           'Date mission',
    'editor.meta.classification': 'Classification',
    'editor.meta.docRef':         'Référence document',
    'editor.meta.help':           'Métadonnées présentes dans tous les pieds de page.',
    // ── Section 01 COVER ──
    'editor.cover.summary':      '01 ░ OPÉRATION (COUVERTURE)',
    'editor.cover.summaryShort': '01 ░ OPÉRATION',
    'editor.cover.title':        'Titre opération',
    'editor.cover.narrative':    'Récit / Contexte',
    'editor.cover.map':          'Carte d\'opération (image)',
    // ── Section 02 SITAC ──
    'editor.sitac.summary':  '02 ░ SITAC',
    'editor.sitac.date':     'Date SITAC (affichée)',
    'editor.sitac.points':   'Points de situation',
    'editor.sitac.addPoint': '+ Ajouter un point',
    'editor.sitac.metar':           'METAR',
    'editor.sitac.metarAssistant':  '🛠 Assistant METAR',
    'editor.sitac.metarOverwrite':   'Remplacer le METAR existant ?',
    'editor.sitac.metarMizOverwrite':'Écraser les champs avec les données du .miz ?',
    'editor.sitac.map':      'Carte SITAC (image)',
    // ── Section 03 MISSION ──
    'editor.mission.summary':      '03 ░ APERÇU MISSION',
    'editor.mission.objectives':   'Objectifs principaux',
    'editor.mission.addObjective': '+ Ajouter un objectif',
    'editor.mission.farp':         'FARP & Aéroports',
    'editor.mission.addFarp':      '+ Ajouter une base',
    'editor.mission.icao':         'ICAO',
    'editor.mission.name':         'Nom',
    'editor.mission.farpCheck':    'FARP',
    'editor.mission.rwyAirport':   'Piste en service',
    'editor.mission.rwyFarp':      'Cap D/A',
    'editor.mission.atc':          'ATC',
    'editor.mission.tanks':        'Menaces — Chars',
    'editor.mission.apc':          'Menaces — APC',
    'editor.mission.aaa':          'Menaces — AAA',
    'editor.mission.sam':          'Menaces — SAM',
    'editor.mission.threatsNote':  'Note menaces (libre)',
    // ── Section 04 RADIO ──
    'editor.radio.summary':      '04 ░ PLAN RADIO',
    'editor.radio.items':        'Items radio — cochez jusqu\'à 6 pour l\'aperçu',
    'editor.radio.addItem':      '+ Ajouter un item',
    'editor.radio.help':         'Définissez ici les fréquences communes (ATC, MISSION, Groupes...). Vous les assignerez ensuite aux canaux radio par appareil ci-dessous.',
    'editor.radio.aircraft':     'Plans radio par appareil',
    'editor.radio.addAircraft':  '+ Ajouter un appareil',
    'editor.radio.helpAircraft': 'Pour chaque appareil, configurez les radios et leurs canaux. Si une image est fournie, elle remplace la table générée.',
    'editor.radio.customName':   'Nom personnalisé',
    'editor.radio.radioName':    'Nom radio (R-863, UHF, ...)',
    'editor.radio.labelEx':      'Libellé (ex: ATC)',
    'editor.radio.freqLabel':    'Fréq.',
    'editor.radio.chLabel':      'Ch.',
    'editor.radio.chanLabel':    'Libellé',
    'editor.radio.chanFreq':     'Fréq.',
    'editor.radio.imgNote':      '⚠ Image fournie : la table sera remplacée par l\'image dans le briefing.',
    'editor.radio.delAircraftConfirm': 'Supprimer la configuration radio de l\'appareil',
    'editor.radio.delChanAriaLabel':   'Supprimer canal',
    'editor.radio.delAircraftAriaLabel': 'Supprimer appareil',
    'editor.radio.freeFreqTooltip':   'Fréquence libre — tap pour passer en Item global',
    'editor.radio.globalItemTooltip': 'Item global — tap pour passer en Fréquence libre',
    // ── Section 05 PHASES ──
    'editor.phases.summary': '05 ░ MISSIONS',
    'editor.phases.prev':    'Mission précédente',
    'editor.phases.next':    'Mission suivante',
    'editor.phases.add':     'Ajouter une mission',
    'editor.phases.dup':     'Dupliquer cette mission',
    'editor.phases.up':      'Monter la mission',
    'editor.phases.down':    'Descendre la mission',
    'editor.phases.remove':  'Supprimer cette mission',
    'editor.phases.dupSuffix':     ' (copie)',
    'editor.phases.deleteConfirm': 'Supprimer la mission',
    'editor.phases.objective':     'Objectif',
    'editor.phases.title':         'Titre de la mission',
    'editor.phases.flightPlan':    'Plan de vol',
    'editor.phases.threatLevel':   'Niveau de menace',
    'editor.phases.notes':         'Notes / repères tactiques',
    'editor.phases.images':        'Images de mission (pages dédiées, 2 par page)',
    'editor.phases.execSteps':     'Étapes d\'exécution',
    'editor.phases.addStep':       '+ Ajouter une étape',
    'editor.phases.addImage':      '+ Ajouter une image',
    'editor.phases.squadron':      'Escadron affecté',
    'editor.phases.subgroup':      'Sous-groupe',
    'editor.phases.subgroupHint':  '(optionnel)',
    'editor.phases.aircraft':      'Appareil utilisé',
    'editor.phases.guestName':     'Nom de l\'escadron',
    'editor.phases.guestSub':      'Nom du groupe',
    'editor.phases.guestAircraft': 'Appareil',
    'editor.phases.guestOption':   '— Escadron invité... —',
    'editor.phases.addSubtask':    '+ Sous-tâche',
    'editor.phases.noImage':          'Aucune image. Toucher « + Ajouter une image ».',
    'editor.phases.imgTitle':          'Titre / tâche associée',
    'editor.phases.imgCaption':        'Commentaire / légende',
    'editor.phases.imgCaptionPlaceholder': 'Commentaire optionnel affiché sous l\'image',
    'editor.phases.noMission':     'Aucune mission définie.',
    'editor.phases.addFirst':      'Touchez + pour ajouter une mission.',
    'editor.phases.indicatorLabel':'Mission',
    // ── Section 07 ROSTER ──
    'editor.roster.summary':  '07 ░ ÉQUIPAGE',
    'editor.roster.help':     'Définissez les pilotes par groupe ou sous-groupe. Une page d\'ordre de bataille sera générée après l\'aperçu mission si au moins un pilote est renseigné.',
    'editor.roster.addGroup': '+ Ajouter un groupe',
    'editor.roster.noGroup':  'Aucun groupe. Toucher « + Ajouter un groupe ».',
    'editor.roster.noPilot':  'Aucun pilote.',
    'editor.roster.delGroupConfirm': 'Supprimer ce groupe ?',
    'editor.roster.pilotPlaceholder':    'Nom / indicatif pilote',
    'editor.roster.callsignPlaceholder': 'Callsign',
    'editor.roster.pilotsLabel': 'Pilotes',
    // ── Section 08 CHARTS ──
    'editor.charts.summary':       '08 ░ CHARTS',
    'editor.charts.add':           '+ Ajouter une chart',
    'editor.charts.noChart':       'Aucune chart. Toucher « + Ajouter une chart ».',
    'editor.charts.airportLabel':  'Nom de l\'aéroport / chart',
    // ── Section 09 ANNEXES ──
    'editor.annexes.summary':  '09 ░ ANNEXES',
    'editor.annexes.add':      '+ Ajouter une annexe',
    'editor.annexes.noAnnex':      'Aucune annexe. Toucher « + Ajouter une annexe ».',
    'editor.annexes.titleLabel':    'Titre',
    'editor.annexes.captionLabel':  'Commentaire / légende',
    'editor.annexes.captionPlaceholder': 'Commentaire optionnel affiché sous l\'image',
    // ── Section 10 WING ──
    'editor.wing.summary':      '10 ░ CONFIGURATION WING',
    'editor.wing.summaryShort': '10 ░ CONFIG WING',
    'editor.wing.import':       '📥 Importer config',
    'editor.wing.hqHint':        '✦ Édition complète disponible dans HQ',
    'editor.wing.resetConfirm.ro':'Réinitialiser le wing au défaut ?\nToutes les modifications seront perdues.',
    'editor.wing.roWing':        'Wing actif',
    'editor.wing.roSquadrons':   'Escadrons enregistrés',
    'toast.wingLoaded':          'Config wing chargée ✓',
    'toast.wingReset':           'Wing réinitialisé ✓',
    'toast.wingInvalid':         '⚠ Config invalide : ',
    'toast.wingJsonInvalid':     '⚠ JSON invalide : ',
    'toast.wingFileError':       '⚠ Lecture du fichier impossible',
    'editor.wing.importTooltip':'Importer un fichier wing_config.json',
    'editor.wing.reset':        '♻ Réinitialiser',
    // ── Shared editor strings ──
    'editor.imgZone.tap':     '▲ TOUCHER POUR CHARGER UNE CARTE ▲',
    'editor.imgZone.tapLogo': '▲ TOUCHER POUR CHARGER UN LOGO ▲',
    'editor.autoSave':        'Sauvegarde locale automatique',
    'editor.exportTip':       'Export JSON pour conserver vos templates',
    // ── Strings résiduelles externalisées (Étape C) ──
    'select.noSquadron':           '— Aucun escadron —',
    'select.noGroup':              '— Sélectionner un groupe —',
    'select.customAircraft':       '— Autre (libre) —',
    'select.noItem':               '— Item —',
    'phase.newTitle':              'Nouvelle mission',
    'placeholder.guestName':       'Ex : WOLF',
    'placeholder.guestSub':        'Ex : WOLF 1 (optionnel)',
    'placeholder.guestAircraft':   'Ex : F-16CM',
    'placeholder.subgroup':        'Ex : ANTON, CAESAR, WOLF 2…',
    'placeholder.imgTitle':        'Ex : Route d\'approche — Attaque ERCAN',
    'placeholder.chartName':       'Ex : AKROTIRI (LCRA) — Piste 10',
    'placeholder.annexeTitle':     'Ex : Notes additionnelles',
    'editor.image.label':         'Image',
    'editor.imgZone.tapShort':    '▲ TOUCHER POUR CHARGER ▲',
    'editor.imgCard.remove':      'Suppr.',
    'editor.phases.moveUp':       'Monter',
    'editor.phases.moveDown':     'Descendre',
    'phase.defaultMapTitle':      'Carte phase',
    'placeholder.optional':       '(optionnel)',
    'preview.objectives':             'Objectifs',
    'preview.sitrepPoints':           'Points de Situation',
    'preview.metar':                  'METAR',
    'preview.sitacImgCaption':        'SITUATION TACTIQUE',
    'preview.noPoints':               'Aucun point renseigné',
    'preview.metarMissing':           '— METAR NON RENSEIGNÉ —',
    'preview.threatTanks':            '◣ Chars / MBT',
    'preview.threatApc':              '◣ APC / VBL',
    'preview.threatAaa':              '◣ AAA',
    'preview.threatSam':              '◣ SAM',
    'editor.phases.aircraftSigle':    'APPAREIL',
    'editor.roster.groupSigle':       'GROUPE',
    'editor.roster.groupSelectLabel': 'Groupe / sous-groupe (depuis les missions)',
    'editor.roster.addPilot':         '+ Ajouter un pilote',
    // Éditeur radio — strings oubliées
    'editor.radio.radiosChannelsLabel':  'Radios & canaux',
    'editor.radio.addRadio':             '+ Ajouter une radio',
    'editor.radio.addChannel':           '+ Canal',
    // Preview — strings oubliées
    'preview.theaterMap':                'CARTE THÉÂTRE',
    'preview.radioAnnexHeader':          'ANNEXE ░ PLAN RADIO',
    'preview.airportFallback':           'AÉROPORT',
    'preview.noMapProvided':             '◯ AUCUNE CARTE FOURNIE ◯',
    'preview.receivedOn':                'REÇU LE',
    'preview.atc':                       'ATC',
    'preview.autoinfo':                  'Auto-info',
    'preview.capLabel':                  'Cap D/A',
    'preview.noRadioItems':              'Aucun item radio défini',
    'preview.noRadioConfig':             'Aucune radio configurée pour cet appareil',
    'preview.guestFallback':             'INVITÉ',
    // Misc strings dynamiques
    'editor.phases.subtaskPlaceholder':  'Sous-tâche',
    'toast.fileMustBeImage':             'Le fichier doit être une image.',
    'toast.exportSingle':                '1 page exportée ✓',
    'toast.exportMulti':                 'pages exportées ✓',
    'error.canvasToBlob':                'Conversion canvas → blob PNG échouée',
    'editor.imgZone.removeImageAria': 'Retirer l\'image',
    'editor.annexes.numSigle':        'ANNEXE',
    // ── Toasts ──
    'toast.langSwitched':      'Interface en français',
    'toast.briefingSaved':     'Briefing exporté ✓',
    'toast.briefingLoaded':    'Briefing chargé ✓',
    'toast.briefingReset':     'Briefing vidé ✓',
    'toast.briefingOptimized': 'Briefing optimisé — {n} image(s) recompressée(s) ✓',
    'toast.briefingOptimizedOnLoad': 'Briefing optimisé au chargement — {n} image(s) ✓',
    'toast.imageCompressing':  'Compression image...',
    'toast.imageLoaded':       'Image chargée ✓',
    'toast.logoInvalid':       '⚠ Logo invalide : ',
    'toast.imageError':        'Erreur : ',
    'toast.jsonInvalid':       '⚠ Fichier JSON invalide : ',
    'toast.fileUnreadable':    '⚠ Lecture impossible',
    'toast.exportError':       '⚠ Erreur export PNG : ',
    'toast.exportGenProgress': 'Génération ',
    // ── Confirmations ──
    'confirm.resetBriefing': 'Vider tout le briefing ?',
    'confirm.deletePhase':   'Supprimer la mission',
    'confirm.deleteRadioAc': 'Supprimer la configuration radio de l\'appareil',
    'confirm.deleteGroup':   'Supprimer ce groupe ?',
    // ── Aperçu rendu (preview) ──
    'preview.missionOverview':   'APERÇU MISSION',
    'preview.squadronsEngaged':  'Escadrons Engagés',
    'preview.farpAirports':      'FARP & Aéroports',
    'preview.radioPlan':         'Plan Radio',
    'preview.threatsIdentified': 'Menaces Identifiées',
    'preview.rosterPage':        'ÉQUIPAGE ░ ORDRE DE BATAILLE',
    'preview.radioAnnex':        'ANNEXE ░ PLAN RADIO',
    'preview.chartPage':         'CHART ░ AÉROPORT',
    'preview.objective':         '◆ Objectif',
    'preview.execution':         '◆ Exécution',
    'preview.flightPlan':        '◆ Plan de Vol',
    'preview.tacticalNotes':     '◆ Notes Tactiques',
    'preview.noSteps':           'Aucune étape',
    'preview.missionSingular':   'Mission',
    'preview.missionPlural':     'Missions',
    'preview.rosterName':        'NOM / INDICATIF',
    'preview.rosterCallsign':    'CALLSIGN',
    // ── Niveaux de menace ──
    'threatLevel.low':      'Faible',
    'threatLevel.moderate': 'Modéré',
    'threatLevel.high':     'Élevé',
    // ── Classifications ──
    'classif.confidential':    'CONFIDENTIEL DÉFENSE',
    'classif.secret':          'SECRET DÉFENSE',
    'classif.top-secret':      'TRÈS SECRET',
    'classif.unclassified':    'NON CLASSIFIÉ',
    'classif.nato-restricted': 'NATO RESTRICTED',
    'classif.nato-secret':     'NATO SECRET',
    // ── Thèmes graphiques ──
    'theme.cw-nato':      'Cold War OTAN',
    'theme.cw-soviet':    'Cold War Soviétique',
    'theme.modern-nato':  'OTAN moderne',
    'theme.modern-east':  'Bloc Est moderne',
    // ── Brief complet / simplifié (v2.3.0) ──
    'toolbar.format.full':        'Brief complet',
    'toolbar.format.simple':      'Brief simplifié',
    'toolbar.format.fullShort':   'Complet',
    'toolbar.format.simpleShort': 'Simplifié',
    'toolbar.format.tooltip':     'Choisir le format du briefing',
    'toolbar.example':            'Exemple',
    'toolbar.example.tooltip':    'Charger le briefing d\'exemple (remplace le briefing en cours)',
    'confirm.loadExample':        'Remplacer le briefing en cours par l\'exemple ?',
    'toast.exampleLoaded':        'Exemple chargé ✓',
    'tab.simple.situation':       'Situation',
    'tab.simple.coord':           'Coordination',
    'tab.simple.photos':          'Photos',
    'editor.meta.time':           'Heure (Z)',
    'editor.simple.situation.summary': '01 ░ SITUATION',
    'editor.simple.mission.summary':   '02 ░ MISSION',
    'editor.simple.coord.summary':     '03 ░ COORDINATION',
    'editor.simple.photos.summary':    '04 ░ PHOTOS',
    'editor.simple.flights':      'Vols',
    'editor.simple.flightNum':    'VOL',
    'editor.simple.photoNum':     'PHOTO',
    'editor.simple.count':        'Nombre',
    'editor.simple.addFlight':    '+ Ajouter un vol',
    'editor.simple.addPhoto':     '+ Ajouter une photo',
    'editor.simple.noFlights':    'Aucun vol. Toucher « + Ajouter un vol ».',
    'editor.simple.noPhotos':     'Aucune photo. Toucher « + Ajouter une photo ».',
    'editor.simple.up':           'Monter',
    'editor.simple.down':         'Descendre',
    'editor.simple.map':          'Carte (image)',
    'editor.targets.label':       'Cibles',
    'editor.targets.add':         '+ Ajouter une cible',
    'editor.targets.num':         'N°',
    'editor.targets.nature':      'Nature',
    'editor.targets.position':    'Position',
    'editor.targets.remark':      'Remarque',
    'editor.targets.empty':       'Aucune cible. Toucher « + Ajouter une cible ».',
    'editor.radio.overviewCheckTooltip': 'Afficher dans l’aperçu (6 au plus)',
    'preview.targets':            'Cibles',
    'preview.targetNum':          'N°',
    'preview.targetNature':       'Nature',
    'preview.targetPosition':     'Position',
    'preview.targetRemark':       'Remarque',
    'simple.threats':             'Menaces',
    'simple.hdr.map':             'CARTE',
    'simple.hdr.threats':         'MENACES',
    'simple.hdr.targets':         'CIBLES',
    'simple.hdr.cont':            'SUITE',
    'simple.subtitle':            'BRIEF SIMPLIFIÉ',
    'simple.hdr.operation':       'OPÉRATION',
    'simple.hdr.mission':         'MISSION',
    'simple.situation':           'Situation',
    'simple.mission':             'Mission',
    'simple.th.flight':           'Vol',
    'simple.th.aircraft':         'Appareil',
    'simple.task':                'Tâche',
    'simple.departure':           'Départ',
    'simple.freq':                'Fréquences',
    'simple.airfields':           'Terrains',
    'simple.weather':             'Météo',
    'simple.photosBanner':        'PHOTOS ░ RECONNAISSANCE',
    'simple.photoLabel':          'PHOTO',
    'simple.noPhoto':             '◯ PHOTO MANQUANTE ◯',
  },
  en: {
    // ── Toolbar ──
    'toolbar.save':           'Save',
    'toolbar.load':           'Load',
    'toolbar.export':         'Export',
    'toolbar.reset':          'Reset',
    'toolbar.save.tooltip':   'Export briefing as JSON',
    'toolbar.load.tooltip':   'Load a JSON briefing',
    'toolbar.export.tooltip': 'Export to PDF or PNG (DCS kneeboard)',
    'toolbar.reset.tooltip':  'Clear the briefing (start from a blank page)',
    'toolbar.theme.tooltip':  'Graphic theme',
    'toolbar.lang.tooltip':   'Switch language / Changer de langue',
    // ── Document ──
    'doc.title.suffix': 'BRIEFING GENERATOR',
    // ── Tab bar ──
    'tab.meta':    'Meta',
    'tab.cover':   'Cover',
    'tab.sitac':   'SITAC',
    'tab.mission': 'Mission',
    'tab.radio':   'Radio',
    'tab.phases':  'Missions',
    'tab.roster':  'Crew',
    'tab.charts':  'Charts',
    'tab.annexes': 'Annexes',
    'tab.wing':    'Wing',
    'tab.preview': 'Preview',
    // ── Export modal ──
    'modal.export.close':          'Close',
    'modal.export.title':          'Export briefing',
    'modal.export.subtitle':       'Choose output format',
    'modal.export.pdf.desc':       'System print · All pages',
    'modal.export.png.desc':       'DCS Kneeboard · 1588×2246, A4',
    'modal.export.png.pages':      'Pages to export',
    'modal.export.png.checkAll':   'Check all',
    'modal.export.png.uncheckAll': 'Uncheck all',
    'modal.export.png.back':       '← Back',
    'modal.export.png.go':         'Export',
    'modal.export.titlePng':       'PNG kneeboard export',
    // ── Section 00 META ──
    'editor.meta.summary':        '00 ░ METADATA',
    'editor.meta.operation':      'Operation',
    'editor.meta.missionCode':    'Mission code',
    'editor.meta.date':           'Mission date',
    'editor.meta.classification': 'Classification',
    'editor.meta.docRef':         'Document reference',
    'editor.meta.help':           'Metadata shown in all page footers.',
    // ── Section 01 COVER ──
    'editor.cover.summary':      '01 ░ OPERATION (COVER)',
    'editor.cover.summaryShort': '01 ░ OPERATION',
    'editor.cover.title':        'Operation title',
    'editor.cover.narrative':    'Narrative / Context',
    'editor.cover.map':          'Operation map (image)',
    // ── Section 02 SITAC ──
    'editor.sitac.summary':  '02 ░ SITAC',
    'editor.sitac.date':     'SITREP date (displayed)',
    'editor.sitac.points':   'SITREP points',
    'editor.sitac.addPoint': '+ Add point',
    'editor.sitac.metar':           'METAR',
    'editor.sitac.metarAssistant':  '🛠 METAR Assistant',
    'editor.sitac.metarOverwrite':   'Replace existing METAR?',
    'editor.sitac.metarMizOverwrite':'Overwrite assistant fields with .miz data?',
    'editor.sitac.map':      'SITAC map (image)',
    // ── Section 03 MISSION ──
    'editor.mission.summary':      '03 ░ MISSION OVERVIEW',
    'editor.mission.objectives':   'Main objectives',
    'editor.mission.addObjective': '+ Add objective',
    'editor.mission.farp':         'FARP & Airfields',
    'editor.mission.addFarp':      '+ Add airfield',
    'editor.mission.icao':         'ICAO',
    'editor.mission.name':         'Name',
    'editor.mission.farpCheck':    'FARP',
    'editor.mission.rwyAirport':   'Active runway',
    'editor.mission.rwyFarp':      'In/Out',
    'editor.mission.atc':          'ATC',
    'editor.mission.tanks':        'Threats — Armor (MBT)',
    'editor.mission.apc':          'Threats — APC',
    'editor.mission.aaa':          'Threats — AAA',
    'editor.mission.sam':          'Threats — SAM',
    'editor.mission.threatsNote':  'Threats note (free text)',
    // ── Section 04 RADIO ──
    'editor.radio.summary':      '04 ░ RADIO PLAN',
    'editor.radio.items':        'Radio items — check up to 6 for the overview',
    'editor.radio.addItem':      '+ Add item',
    'editor.radio.help':         'Define shared frequencies here (ATC, MISSION, Groups...). Assign them to aircraft radio channels below.',
    'editor.radio.aircraft':     'Radio plans by aircraft',
    'editor.radio.addAircraft':  '+ Add aircraft',
    'editor.radio.helpAircraft': 'For each aircraft, configure radios and their channels. If an image is provided, it replaces the generated table.',
    'editor.radio.customName':   'Custom name',
    'editor.radio.radioName':    'Radio name (R-863, UHF, ...)',
    'editor.radio.labelEx':      'Label (e.g. ATC)',
    'editor.radio.freqLabel':    'Freq.',
    'editor.radio.chLabel':      'Ch.',
    'editor.radio.chanLabel':    'Label',
    'editor.radio.chanFreq':     'Freq.',
    'editor.radio.imgNote':      '⚠ Image provided: the table will be replaced by the image in the briefing.',
    'editor.radio.delAircraftConfirm':   'Delete radio config for aircraft',
    'editor.radio.delChanAriaLabel':     'Delete channel',
    'editor.radio.delAircraftAriaLabel': 'Delete aircraft',
    'editor.radio.freeFreqTooltip':   'Custom frequency — tap to switch to global item',
    'editor.radio.globalItemTooltip': 'Global item — tap to switch to custom frequency',
    // ── Section 05 PHASES ──
    'editor.phases.summary': '05 ░ MISSIONS',
    'editor.phases.prev':    'Previous mission',
    'editor.phases.next':    'Next mission',
    'editor.phases.add':     'Add mission',
    'editor.phases.dup':     'Duplicate this mission',
    'editor.phases.up':      'Move mission up',
    'editor.phases.down':    'Move mission down',
    'editor.phases.remove':  'Delete this mission',
    'editor.phases.dupSuffix':     ' (copy)',
    'editor.phases.deleteConfirm': 'Delete mission',
    'editor.phases.objective':     'Objective',
    'editor.phases.title':         'Mission title',
    'editor.phases.flightPlan':    'Flight Plan',
    'editor.phases.threatLevel':   'Threat Level',
    'editor.phases.notes':         'Tactical Notes / Cues',
    'editor.phases.images':        'Mission Images (dedicated pages, 2 per page)',
    'editor.phases.execSteps':     'Execution Steps',
    'editor.phases.addStep':       '+ Add step',
    'editor.phases.addImage':      '+ Add image',
    'editor.phases.squadron':      'Assigned squadron',
    'editor.phases.subgroup':      'Sub-group',
    'editor.phases.subgroupHint':  '(optional)',
    'editor.phases.aircraft':      'Aircraft type',
    'editor.phases.guestName':     'Squadron name',
    'editor.phases.guestSub':      'Group name',
    'editor.phases.guestAircraft': 'Aircraft',
    'editor.phases.guestOption':   '— Guest squadron... —',
    'editor.phases.addSubtask':    '+ Sub-task',
    'editor.phases.noImage':          'No image. Tap « + Add image ».',
    'editor.phases.imgTitle':          'Title / associated task',
    'editor.phases.imgCaption':        'Caption / legend',
    'editor.phases.imgCaptionPlaceholder': 'Optional caption shown below the image',
    'editor.phases.noMission':     'No mission defined.',
    'editor.phases.addFirst':      'Tap + to add a mission.',
    'editor.phases.indicatorLabel':'Mission',
    // ── Section 07 ROSTER ──
    'editor.roster.summary':  '07 ░ CREW / ROSTER',
    'editor.roster.help':     'Define pilots by group or sub-group. A battle order page will be generated after the mission overview if at least one pilot is listed.',
    'editor.roster.addGroup': '+ Add group',
    'editor.roster.noGroup':  'No groups. Tap « + Add group ».',
    'editor.roster.noPilot':  'No pilots.',
    'editor.roster.delGroupConfirm': 'Delete this group?',
    'editor.roster.pilotPlaceholder':    'Name / pilot callsign',
    'editor.roster.callsignPlaceholder': 'Callsign',
    'editor.roster.pilotsLabel': 'Pilots',
    // ── Section 08 CHARTS ──
    'editor.charts.summary':      '08 ░ CHARTS',
    'editor.charts.add':          '+ Add chart',
    'editor.charts.noChart':      'No charts. Tap « + Add chart ».',
    'editor.charts.airportLabel': 'Airfield / chart name',
    // ── Section 09 ANNEXES ──
    'editor.annexes.summary':  '09 ░ ANNEXES',
    'editor.annexes.add':      '+ Add annex',
    'editor.annexes.noAnnex':          'No annexes. Tap « + Add annex ».',
    'editor.annexes.titleLabel':        'Title',
    'editor.annexes.captionLabel':      'Caption / legend',
    'editor.annexes.captionPlaceholder': 'Optional caption shown below the image',
    // ── Section 10 WING ──
    'editor.wing.summary':      '10 ░ WING CONFIGURATION',
    'editor.wing.summaryShort': '10 ░ WING CONFIG',
    'editor.wing.import':       '📥 Import config',
    'editor.wing.hqHint':        '✦ Full editing available in HQ',
    'editor.wing.resetConfirm.ro':'Reset wing to default?\nAll changes will be lost.',
    'editor.wing.roWing':        'Active wing',
    'editor.wing.roSquadrons':   'Registered squadrons',
    'toast.wingLoaded':          'Wing config loaded ✓',
    'toast.wingReset':           'Wing reset ✓',
    'toast.wingInvalid':         '⚠ Invalid config: ',
    'toast.wingJsonInvalid':     '⚠ Invalid JSON: ',
    'toast.wingFileError':       '⚠ Cannot read file',
    'editor.wing.importTooltip':'Import a wing_config.json file',
    'editor.wing.reset':        '♻ Reset',
    // ── Shared editor strings ──
    'editor.imgZone.tap':     '▲ TAP TO LOAD A MAP ▲',
    'editor.imgZone.tapLogo': '▲ TAP TO LOAD A LOGO ▲',
    'editor.autoSave':        'Automatic local save',
    'editor.exportTip':       'Export JSON to keep your templates',
    // ── Residual strings externalized (Step C) ──
    'select.noSquadron':           '— No squadron —',
    'select.noGroup':              '— Select a group —',
    'select.customAircraft':       '— Other (custom) —',
    'select.noItem':               '— Item —',
    'phase.newTitle':              'New mission',
    'placeholder.guestName':       'e.g. WOLF',
    'placeholder.guestSub':        'e.g. WOLF 1 (optional)',
    'placeholder.guestAircraft':   'e.g. F-16CM',
    'placeholder.subgroup':        'e.g. ANTON, CAESAR, WOLF 2…',
    'placeholder.imgTitle':        'e.g. Approach route — ERCAN Strike',
    'placeholder.chartName':       'e.g. AKROTIRI (LCRA) — RWY 10',
    'placeholder.annexeTitle':     'e.g. Additional notes',
    'editor.image.label':         'Image',
    'editor.imgZone.tapShort':    '▲ TAP TO LOAD ▲',
    'editor.imgCard.remove':      'Remove',
    'editor.phases.moveUp':       'Move up',
    'editor.phases.moveDown':     'Move down',
    'phase.defaultMapTitle':      'Phase map',
    'placeholder.optional':       '(optional)',
    'preview.objectives':             'Objectives',
    'preview.sitrepPoints':           'Situation Points',
    'preview.metar':                  'METAR',
    'preview.sitacImgCaption':        'TACTICAL SITUATION',
    'preview.noPoints':               'No points provided',
    'preview.metarMissing':           '— METAR NOT PROVIDED —',
    'preview.threatTanks':            '◣ Tanks / MBT',
    'preview.threatApc':              '◣ APC / IFV',
    'preview.threatAaa':              '◣ AAA',
    'preview.threatSam':              '◣ SAM',
    'editor.phases.aircraftSigle':    'AIRCRAFT',
    'editor.roster.groupSigle':       'GROUP',
    'editor.roster.groupSelectLabel': 'Group / subgroup (from missions)',
    'editor.roster.addPilot':         '+ Add a pilot',
    // Editor radio
    'editor.radio.radiosChannelsLabel':  'Radios & channels',
    'editor.radio.addRadio':             '+ Add radio',
    'editor.radio.addChannel':           '+ Channel',
    // Preview
    'preview.theaterMap':                'THEATER MAP',
    'preview.radioAnnexHeader':          'ANNEX ░ RADIO PLAN',
    'preview.airportFallback':           'AIRFIELD',
    'preview.noMapProvided':             '◯ NO MAP PROVIDED ◯',
    'preview.receivedOn':                'RECEIVED ON',
    'preview.atc':           'ATC',
    'preview.autoinfo':      'Auto-info',
    'preview.capLabel':      'In/Out',
    'preview.noRadioItems':              'No radio items defined',
    'preview.noRadioConfig':             'No radio configured for this aircraft',
    'preview.guestFallback':             'GUEST',
    // Misc
    'editor.phases.subtaskPlaceholder':  'Subtask',
    'toast.fileMustBeImage':             'File must be an image.',
    'toast.exportSingle':                '1 page exported ✓',
    'toast.exportMulti':                 'pages exported ✓',
    'error.canvasToBlob':                'Canvas → PNG blob conversion failed',
    'editor.imgZone.removeImageAria': 'Remove image',
    'editor.annexes.numSigle':        'ANNEX',
    // ── Toasts ──
    'toast.langSwitched':      'Interface in English',
    'toast.briefingSaved':     'Briefing exported ✓',
    'toast.briefingLoaded':    'Briefing loaded ✓',
    'toast.briefingReset':     'Briefing cleared ✓',
    'toast.briefingOptimized': 'Briefing optimized — {n} image(s) recompressed ✓',
    'toast.briefingOptimizedOnLoad': 'Briefing optimized on load — {n} image(s) ✓',
    'toast.imageCompressing':  'Compressing image…',
    'toast.imageLoaded':       'Image loaded ✓',
    'toast.logoInvalid':       '⚠ Invalid logo: ',
    'toast.imageError':        'Error: ',
    'toast.jsonInvalid':       '⚠ Invalid JSON file: ',
    'toast.fileUnreadable':    '⚠ Cannot read file',
    'toast.exportError':       '⚠ PNG export error: ',
    'toast.exportGenProgress': 'Generating ',
    // ── Confirmations ──
    'confirm.resetBriefing': 'Clear the entire briefing?',
    'confirm.deletePhase':   'Delete mission',
    'confirm.deleteRadioAc': 'Delete radio config for aircraft',
    'confirm.deleteGroup':   'Delete this group?',
    // ── Preview (aperçu rendu) ──
    'preview.missionOverview':   'MISSION OVERVIEW',
    'preview.squadronsEngaged':  'Squadrons Engaged',
    'preview.farpAirports':      'FARP & Airfields',
    'preview.radioPlan':         'Radio Plan',
    'preview.threatsIdentified': 'Identified Threats',
    'preview.rosterPage':        'CREW ░ ORDER OF BATTLE',
    'preview.radioAnnex':        'ANNEX ░ RADIO PLAN',
    'preview.chartPage':         'CHART ░ AIRFIELD',
    'preview.objective':         '◆ OBJECTIVE',
    'preview.execution':         '◆ EXECUTION',
    'preview.flightPlan':        '◆ FLIGHT PLAN',
    'preview.tacticalNotes':     '◆ TACTICAL NOTES',
    'preview.noSteps':           'No steps',
    'preview.missionSingular':   'Mission',
    'preview.missionPlural':     'Missions',
    'preview.rosterName':        'NAME / CALLSIGN',
    'preview.rosterCallsign':    'CALLSIGN',
    // ── Threat levels ──
    'threatLevel.low':      'Low',
    'threatLevel.moderate': 'Moderate',
    'threatLevel.high':     'High',
    // ── Classifications ──
    'classif.confidential':    'CONFIDENTIAL',
    'classif.secret':          'SECRET',
    'classif.top-secret':      'TOP SECRET',
    'classif.unclassified':    'UNCLASSIFIED',
    'classif.nato-restricted': 'NATO RESTRICTED',
    'classif.nato-secret':     'NATO SECRET',
    // ── Graphic themes ──
    'theme.cw-nato':      'Cold War NATO',
    'theme.cw-soviet':    'Cold War Soviet',
    'theme.modern-nato':  'Modern NATO',
    'theme.modern-east':  'Modern Eastern Bloc',
    // ── Full / quick brief (v2.3.0) ──
    'toolbar.format.full':        'Full brief',
    'toolbar.format.simple':      'Quick brief',
    'toolbar.format.fullShort':   'Full',
    'toolbar.format.simpleShort': 'Quick',
    'toolbar.format.tooltip':     'Choose the briefing format',
    'toolbar.example':            'Example',
    'toolbar.example.tooltip':    'Load the example briefing (replaces the current one)',
    'confirm.loadExample':        'Replace the current briefing with the example?',
    'toast.exampleLoaded':        'Example loaded ✓',
    'tab.simple.situation':       'Situation',
    'tab.simple.coord':           'Coordination',
    'tab.simple.photos':          'Photos',
    'editor.meta.time':           'Time (Z)',
    'editor.simple.situation.summary': '01 ░ SITUATION',
    'editor.simple.mission.summary':   '02 ░ MISSION',
    'editor.simple.coord.summary':     '03 ░ COORDINATION',
    'editor.simple.photos.summary':    '04 ░ PHOTOS',
    'editor.simple.flights':      'Flights',
    'editor.simple.flightNum':    'FLIGHT',
    'editor.simple.photoNum':     'PHOTO',
    'editor.simple.count':        'Count',
    'editor.simple.addFlight':    '+ Add flight',
    'editor.simple.addPhoto':     '+ Add photo',
    'editor.simple.noFlights':    'No flights. Tap « + Add flight ».',
    'editor.simple.noPhotos':     'No photos. Tap « + Add photo ».',
    'editor.simple.up':           'Move up',
    'editor.simple.down':         'Move down',
    'editor.simple.map':          'Map (image)',
    'editor.targets.label':       'Targets',
    'editor.targets.add':         '+ Add target',
    'editor.targets.num':         'No.',
    'editor.targets.nature':      'Type',
    'editor.targets.position':    'Position',
    'editor.targets.remark':      'Remarks',
    'editor.targets.empty':       'No target. Tap “+ Add target”.',
    'editor.radio.overviewCheckTooltip': 'Show in the overview (6 at most)',
    'preview.targets':            'Targets',
    'preview.targetNum':          'No.',
    'preview.targetNature':       'Type',
    'preview.targetPosition':     'Position',
    'preview.targetRemark':       'Remarks',
    'simple.threats':             'Threats',
    'simple.hdr.map':             'MAP',
    'simple.hdr.threats':         'THREATS',
    'simple.hdr.targets':         'TARGETS',
    'simple.hdr.cont':            'CONT.',
    'simple.subtitle':            'QUICK BRIEF',
    'simple.hdr.operation':       'OPERATION',
    'simple.hdr.mission':         'MISSION',
    'simple.situation':           'Situation',
    'simple.mission':             'Mission',
    'simple.th.flight':           'Flight',
    'simple.th.aircraft':         'Aircraft',
    'simple.task':                'Task',
    'simple.departure':           'Departure',
    'simple.freq':                'Frequencies',
    'simple.airfields':           'Airfields',
    'simple.weather':             'Weather',
    'simple.photosBanner':        'PHOTOS ░ RECONNAISSANCE',
    'simple.photoLabel':          'PHOTO',
    'simple.noPhoto':             '◯ NO PHOTO ◯',
  }
};

// Migration des anciennes valeurs textuelles de classification vers clés canoniques
const CLASSIF_LEGACY_MAP = {
  'CONFIDENTIEL DÉFENSE': 'confidential',
  'SECRET DÉFENSE':       'secret',
  'TRÈS SECRET':          'top-secret',
  'NON CLASSIFIÉ':        'unclassified',
  'NATO RESTRICTED':      'nato-restricted',
  'NATO SECRET':          'nato-secret'
};

// Migration des anciennes valeurs textuelles de threatLevel vers clés canoniques
// Couvre : FR (Faible/Modéré/Élevé), legacy (Danger/Important/Critique)
const THREAT_LEGACY_MAP = {
  'Faible':    'low',
  'Modéré':    'moderate',
  'Élevé':     'high',
  'eleve':     'high',
  'Danger':    'high',
  'Important': 'high',
  'Critique':  'high'
};

let CURRENT_LANG = 'fr'; // initialisé par initLang()

function t(key, fallback) {
  const dict = I18N[CURRENT_LANG] || I18N.fr;
  if (key in dict) return dict[key];
  if (fallback !== undefined) return fallback;
  if (key in I18N.fr) return I18N.fr[key]; // fallback FR si clé absente en EN
  console.warn('[i18n] missing key:', key);
  return key;
}

function initLang() {
  try {
    const stored = localStorage.getItem(KEY_LANG);
    if (stored === 'fr' || stored === 'en') {
      CURRENT_LANG = stored;
      document.documentElement.lang = CURRENT_LANG;
      return;
    }
  } catch(e) { /* localStorage indisponible */ }
  const nav = (navigator.language || 'fr').toLowerCase();
  CURRENT_LANG = nav.startsWith('fr') ? 'fr' : 'en';
  try { localStorage.setItem(KEY_LANG, CURRENT_LANG); } catch(e) { /* ignore */ }
  document.documentElement.lang = CURRENT_LANG;
}

// applyI18nStatic : peuple les attributs data-i18n* dans le DOM
// Appelée à l'init et à chaque bascule de langue.
// Support : elements classiques + <option data-i18n> (textContent seul, value= inchangée)
// Étape B ajoutera les attributs dans le HTML — dès maintenant la fonction
// est fonctionnelle, elle ne fait juste rien si aucun attribut n'est présent.
function applyI18nStatic() {
  // textContent (éléments courants + <option>)
  document.querySelectorAll('[data-i18n]').forEach(el => {
    el.textContent = t(el.dataset.i18n);
  });
  // title attribute
  document.querySelectorAll('[data-i18n-title]').forEach(el => {
    el.title = t(el.dataset.i18nTitle);
  });
  // placeholder attribute
  document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
    el.placeholder = t(el.dataset.i18nPlaceholder);
  });
  // aria-label attribute
  document.querySelectorAll('[data-i18n-aria-label]').forEach(el => {
    el.setAttribute('aria-label', t(el.dataset.i18nAriaLabel));
  });
}

function updateFlagButton() {
  const btn = document.getElementById('btn-lang');
  if (!btn) return;
  // Afficher le drapeau de la langue CIBLE (vers laquelle on basculerait)
  btn.textContent = CURRENT_LANG === 'fr' ? '\uD83C\uDDEC\uD83C\uDDE7' : '\uD83C\uDDEB\uD83C\uDDF7';
}

function updateDocTitle() {
  const w = wingConfig ? wingConfig.wing : null;
  const base = w ? w.shortName : 'MY WING';
  document.title = base + ' // ' + t('doc.title.suffix');
}

function setLang(lang) {
  if (lang !== 'fr' && lang !== 'en') return;
  if (lang === CURRENT_LANG) return;
  CURRENT_LANG = lang;
  try { localStorage.setItem(KEY_LANG, CURRENT_LANG); } catch(e) { /* ignore */ }
  document.documentElement.lang = CURRENT_LANG;
  applyI18nStatic();
  rerenderAllDynamic();     // rejoue les sections construites en JS
  updateFlagButton();
  updateDocTitle();
  schedulePreview();
  showToast(t('toast.langSwitched'), 'success');
}

/* rerenderAllDynamic — Phase 9 : rejoue toutes les fonctions de rendu dynamique
   qui utilisent t() à la construction. Appelée par setLang() pour que la bascule
   de langue mette à jour l'éditeur (les éléments avec data-i18n* sont déjà gérés
   par applyI18nStatic, mais le contenu construit en JS via innerHTML ne l'est pas). */
function rerenderAllDynamic() {
  // Éditeur — chaque fonction est idempotente (vide son conteneur et reconstruit)
  try { renderPhaseEditor(); }      catch(e) { console.warn('rerender phase failed:', e); }
  try { renderCharts(); }           catch(e) { console.warn('rerender charts failed:', e); }
  try { renderAnnexes(); }          catch(e) { console.warn('rerender annexes failed:', e); }
  try { renderAirfields(); }        catch(e) { console.warn('rerender airfields failed:', e); }
  try { renderRoster(); }           catch(e) { console.warn('rerender roster failed:', e); }
  try { renderRadioItems(); }       catch(e) { console.warn('rerender radio items failed:', e); }
  try { renderRadioAircrafts(); }   catch(e) { console.warn('rerender radio ac failed:', e); }
  // Brief simplifié (v2.3.2) : vols, fréquences et photos construisent leurs libellés par t()
  try { renderSimpleFlights(); }    catch(e) { console.warn('rerender simple flights failed:', e); }
  try { renderSimpleRadioItems(); } catch(e) { console.warn('rerender simple radio failed:', e); }
  try { renderPhotosEditor(); }     catch(e) { console.warn('rerender photos failed:', e); }
  // v2.4.0 : listes de cibles (les deux formats) et zones d'image liées à l'état (leur texte vient de t())
  try { renderTargets(); }          catch(e) { console.warn('rerender targets failed:', e); }
  try { document.querySelectorAll('[data-img-bind]').forEach(refreshImgZone); } catch(e) { console.warn('rerender img zones failed:', e); }
  // P1.B: wing read-only panel re-rendered via renderWingReadOnly() depuis storage listener
}

/* ============= WING CONFIG (runtime, mutable) =============
   wingConfig is the single source of truth for wing branding and
   squadron data. At startup it points to DEFAULT_WING_CONFIG (generic);
   the user can load any wing via JSON import or localStorage persistence.
   Helpers (getSquadron, getAllAircraft) ALWAYS read wingConfig.squadrons
   dynamically — never capture a frozen copy. */
let wingConfig = DEFAULT_WING_CONFIG;

function getSquadron(id) { return wingConfig.squadrons.find(s => s.id === id) || null; }

/* All distinct aircraft types across the current wing.
   Function (not constant) so it reflects wingConfig changes at runtime. */
function getAllAircraft() {
  const set = new Set();
  wingConfig.squadrons.forEach(s => s.aircraft.forEach(a => set.add(a)));
  return Array.from(set);
}

/* DEFAULTS = briefing VIDE (v2.3.0). Le contenu de démonstration est EXAMPLE_BRIEFING
   (bouton « Exemple »). meta.format : 'simple' (brief simplifié) | 'full' (brief complet). */
const DEFAULTS = {
  meta: {
    operation: '',
    mission: '',
    date: '',
    time: '',
    format: 'simple',
    classification: 'confidential',
    docRef: ''
  },
  cover: { title: '', narrative: '', mapImage: '' },
  sitac: { date: '', points: [], metar: '', mapImage: '' },
  mission: {
    objectives: [],
    farp: [],
    threats: { tanks: '', apc: '', aaa: '', sam: '', note: '' },
    targets: []   // v2.4.0 : { num, nature, position, remark } — partagée par les deux formats
  },
  radioPlan: { items: [], aircraftPlans: [] },
  phases: [],
  charts: [],
  annexes: [],
  roster: { groups: [] },
  photos: []   // brief simplifié : { title, img, caption }
};

/* Briefing d'exemple (ancienne démonstration). Toujours en brief complet. */
const EXAMPLE_BRIEFING = {
  meta: {
    operation: 'FOOTHOLD',
    mission: 'M3',
    date: '1989-03-22',
    format: 'full',
    classification: 'confidential',
    docRef: 'VEAW-FH-M3-1989'
  },
  cover: {
    title: 'OPERATION FOOTHOLD',
    narrative: "Les forces soviétiques sont à l'origine du déclenchement d'une guerre civile en Syrie et ont assisté les troupes rebelles pour réussir un coup d'État. Une fois le gouvernement tombé, les forces dissidentes ont envahi l'île de Chypre et capturé la quasi-totalité de l'île, sauf la base OTAN d'AKROTIRI.\n\nLes forces de l'OTAN opèrent un déploiement majeur afin d'assister le gouvernement légitime chypriote à reprendre le contrôle total de l'île. Il n'est pas exclu une opération aéro-navale majeure pour « libérer » la Syrie.",
    mapImage: ''
  },
  sitac: {
    date: '22-03-1989',
    points: [
      "La majorité de l'île reste aux mains de l'ennemi",
      "L'aéroport de PAPHOS a été capturé et ses défenses renforcées",
      "La FARP POLIS a été capturée mais ses défenses sont fragiles",
      "L'adversaire utilise l'aéroport d'ERKAN pour ses contre-offensives (CAP/CAS/SEAD)",
      "Un site de missiles SILKWORM empêche la flotte OTAN de se rapprocher",
      "Le HQ a renforcé POLIS et AKROTIRI avec une unité SAM ROLAND chacune"
    ],
    metar: 'LCRA 221000Z 18002KT 9999 SCT082 20/15 Q1013',
    mapImage: ''
  },
  mission: {
    objectives: [
      "Apporter du ravitaillement à POLIS",
      "Renforcer les défenses de POLIS — Défendre la FARP",
      "Reconnaître et capturer la zone de KARAVOSTASI",
      "Missions secondaires possibles (CSAR, S&D)"
    ],
    farp: [
      { icao:'LCRA', name:'Akrotiri', isFarp:false, rwy:'10', atc:true  },
      { icao:'LCPH', name:'Paphos',   isFarp:false, rwy:'11', atc:true  }
    ],
    threats: {
      tanks: 'T-55 à T-80',
      apc: 'BRDM-2, BMP-1, BMP-2, BTR-80',
      aaa: 'ZU-57, ZU-23, ZSU-24, S-60, KS-19',
      sam: 'Manpads, SA-8, SA-9, SA-13, Avenger',
      note: 'Pas de SAM longue portée sur Chypre'
    }
  },
  radioPlan: {
    items: [
      { id: 'atc',     label: 'ATC',     frequency: '270.00', modulation: 'AM' },
      { id: 'mission', label: 'MISSION', frequency: '265.00', modulation: 'AM' },
      { id: 'grp1',    label: 'Groupe 1', frequency: '127.50', modulation: 'AM' },
      { id: 'grp2',    label: 'Groupe 2', frequency: '135.00', modulation: 'AM' },
      { id: 'fm1',     label: 'Tactique FM', frequency: '21.50', modulation: 'FM' }
    ],
    aircraftPlans: [
      {
        aircraft: 'Mi-24P',
        radios: [
          {
            name: 'R-863',
            channels: [
              { channel: 0, mode: 'item', itemId: 'grp1' },
              { channel: 1, mode: 'item', itemId: 'grp2' },
              { channel: 3, mode: 'item', itemId: 'mission' },
              { channel: 7, mode: 'item', itemId: 'atc' }
            ]
          },
          {
            name: 'R-828',
            channels: [
              { channel: 0, mode: 'item', itemId: 'fm1' }
            ]
          }
        ],
        image: ''
      },
      {
        aircraft: 'Mi-8',
        radios: [
          {
            name: 'R-863',
            channels: [
              { channel: 4, mode: 'item', itemId: 'mission' },
              { channel: 8, mode: 'item', itemId: 'atc' }
            ]
          },
          {
            name: 'R-828',
            channels: [
              { channel: 1, mode: 'item', itemId: 'fm1' }
            ]
          }
        ],
        image: ''
      }
    ]
  },
  phases: [
    {
      title: 'Ravitaillement POLIS',
      objective: "Ravitailler POLIS en armement pour les Mi-24P",
      execution: [
        {text: "TO PAPHOS — Ravitaillement à POLIS pour Mission #2", subtasks: []},
        {text: "Caisses ATAKA + Roquettes", subtasks: []}
      ],
      flightPlan: 'CAP 352° / Distance 34 Km',
      threatLevel: 'low', notes: '', images: [],
      squadron: 'KHR-26', aircraft: 'Mi-8', subgroup: 'ANTON'
    },
    {
      title: 'Défense POLIS — Mi-24P',
      objective: "Les renseignements font état d'un convoi blindé au départ de KARAVOSTASI pour reprendre POLIS",
      execution: [
        {text: "TO POLIS", subtasks: []},
        {text: "Suivre le chemin côtier de POLIS jusque KARAVOSTASI", subtasks: []}
      ],
      flightPlan: "Chemin côtier jusqu'à l'IP Mission #3",
      threatLevel: 'high', notes: 'Route estimée du convoi : voir carte phase 2', images: [],
      squadron: 'KHR-26', aircraft: 'Mi-24P', subgroup: 'CAESAR'
    },
    {
      title: 'RECO + ASSAUT KARAVOSTASI',
      objective: "Préparer la capture de la zone par les troupes aéroportées. Destruction des défenses SAM/AAA et des éléments blindés",
      execution: [
        {text: "TO POLIS — Retour selon SITAC", subtasks: []},
        {text: "Rassemblement à l'IP", subtasks: []},
        {text: "Cibles prioritaires : SAM / AAA", subtasks: ["SA-13", "SA-9", "Manpads"]},
        {text: "Cibles secondaires : APC / MBT", subtasks: []}
      ],
      flightPlan: 'IP : 59° / 32 Km — TGT : 118° / 9 Km',
      threatLevel: 'high', notes: "Repère : petite île + rivière à 8/9 Km de KARAVOSTASI. Axe d'assaut le long de la côte.",
      images: [], squadron: 'KHR-26', aircraft: 'Mi-24P', subgroup: ''
    }
  ],
  charts: [
    { name: 'AKROTIRI (LCRA) — Piste en service : 10', img: '' },
    { name: 'PAPHOS (LCPH) — Piste en service : 11', img: '' }
  ],
  annexes: [],
  roster: {
    groups: []   // { missionKey: 'KHR-26||CAESAR||Mi-24P', pilots: [{name,aircraft,callsign}] }
  }
};

let state;
let currentPhaseIdx = 0;
let activeTab = 'meta';

/* ============= STATE / PERSISTENCE ============= */
function loadState() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) {
      const parsed = JSON.parse(raw);
      state = mergeDeep(structuredClone(DEFAULTS), parsed);
      // Migration classification : legacy texte → clé canonique (v2.2.0)
      if (state.meta && state.meta.classification) {
        const migrated = CLASSIF_LEGACY_MAP[state.meta.classification];
        if (migrated) state.meta.classification = migrated;
      }
      if (Array.isArray(state.phases)) {
        state.phases.forEach(ph => {
          ph.execution = normalizeExecution(ph.execution);
          normalizePhaseImages(ph);
          ph.threatLevel = normalizeThreatLevel(ph.threatLevel);
        });
      }
      normalizeCharts(state);
      normalizeAnnexes(state);
      applyLoadedFormat(parsed);
      normalizePhotos(state);
      normalizeTargets(state);
      return;
    }
  } catch(e) { console.warn('Storage load failed:', e); }
  state = structuredClone(DEFAULTS);
}

/* v2.3.0 — le format se lit sur ce que CONTIENT le fichier / le stockage (pas sur le résultat
   de la fusion avec DEFAULTS, qui porte 'simple') : sans champ meta.format, c'est un brief complet. */
function applyLoadedFormat(parsed) {
  const fmt = parsed && parsed.meta ? parsed.meta.format : undefined;
  state.meta.format = (fmt === 'simple' || fmt === 'full') ? fmt : 'full';
}

/* v2.4.0 — cibles : toujours une liste d'objets à quatre chaînes { num, nature, position, remark } */
function normalizeTargets(s) {
  if (!s.mission || typeof s.mission !== 'object') s.mission = {};
  const str = v => (v == null ? '' : String(v));
  const list = Array.isArray(s.mission.targets) ? s.mission.targets : [];
  s.mission.targets = list.map(tg => ({
    num: str(tg && tg.num),
    nature: str(tg && tg.nature),
    position: str(tg && tg.position),
    remark: str(tg && tg.remark)
  }));
}

/* photos du brief simplifié : toujours une liste de { title, img, caption } */
function normalizePhotos(s) {
  if (!Array.isArray(s.photos)) s.photos = [];
  s.photos = s.photos.map(p => ({
    title: (p && p.title) || '',
    img: (p && p.img) || '',
    caption: (p && p.caption) || ''
  }));
}

function persistState() {
  try { localStorage.setItem(STORAGE_KEY, JSON.stringify(state)); }
  catch(e) { /* localStorage may be unavailable or full */ }
}

/* ============= WING CONFIG PERSISTENCE ============= */

/* Validates a candidate wing config object.
   Returns { ok: true } or { ok: false, errors: string[] }.
   Called both at import and at localStorage load to guard against corruption. */
function validateWingConfig(obj) {
  const errors = [];
  if (!obj || typeof obj !== 'object') return { ok: false, errors: [t('validate.schemaMissing')] };
  if (obj.configSchemaVersion !== 1)
    errors.push(t('validate.schemaMissing'));
  if (!obj.wing || typeof obj.wing !== 'object') {
    errors.push(t('validate.wingMissing'));
  } else {
    if (!obj.wing.shortName)
      errors.push(t('validate.shortNameMissing'));
    if (!obj.wing.logo || !String(obj.wing.logo).startsWith('data:image/'))
      errors.push(t('validate.logoInvalid'));
  }
  if (!Array.isArray(obj.squadrons)) {
    errors.push(t('validate.squadronsNotArray'));
  } else {
    obj.squadrons.forEach((sq, i) => {
      if (!sq.id)                      errors.push('squadrons[' + i + ']' + t('validate.sqIdMissing'));
      if (!sq.callsign)                errors.push('squadrons[' + i + ']' + t('validate.sqCallsignMissing'));
      if (!Array.isArray(sq.aircraft)) errors.push('squadrons[' + i + ']' + t('validate.sqAircraftNotArray'));
    });
  }
  return errors.length === 0 ? { ok: true } : { ok: false, errors };
}

/* Reads wing config from localStorage.
   Returns DEFAULT_WING_CONFIG (deep-cloned) if absent or invalid. */
function loadWingConfig() {
  try {
    const raw = localStorage.getItem(KEY_WING);
    if (raw) {
      const parsed = JSON.parse(raw);
      const check = validateWingConfig(parsed);
      if (check.ok) return parsed;
      console.warn('[Wing] Config localStorage invalide — utilisation du défaut :', check.errors);
    }
  } catch(e) { console.warn('[Wing] Lecture localStorage échouée :', e); }
  return structuredClone(DEFAULT_WING_CONFIG);
}

/* Debounced write of wingConfig to localStorage (200 ms).
   Called by importWingConfig/resetWingConfig (P1.B: wing editor moved to HQ). */
let _wingPersistTimer = null;
function persistWingConfig() {
  if (_wingPersistTimer) clearTimeout(_wingPersistTimer);
  _wingPersistTimer = setTimeout(() => {
    try {
      localStorage.setItem(KEY_WING, JSON.stringify(wingConfig));
    } catch(e) {
      if (e.name === 'QuotaExceededError') {
        showToast(t('toast.wingStorageFull'));
      } else {
        console.warn('[Wing] Erreur persistance :', e);
      }
    }
  }, 200);
}

function mergeDeep(target, source) {
  for (const k of Object.keys(source || {})) {
    if (source[k] && typeof source[k] === 'object' && !Array.isArray(source[k])) {
      target[k] = mergeDeep(target[k] || {}, source[k]);
    } else {
      target[k] = source[k];
    }
  }
  return target;
}

function getByPath(obj, path) {
  return path.split('.').reduce((o, k) => o == null ? undefined : o[k], obj);
}
function setByPath(obj, path, val) {
  const keys = path.split('.');
  let o = obj;
  for (let i = 0; i < keys.length - 1; i++) {
    if (o[keys[i]] == null) o[keys[i]] = {};
    o = o[keys[i]];
  }
  o[keys[keys.length - 1]] = val;
}

/* ============= IMAGE COMPRESSION ============= */
function compressImageFile(file) {
  return new Promise((resolve, reject) => {
    if (!file.type.startsWith('image/')) {
      reject(new Error(t('toast.fileMustBeImage')));
      return;
    }
    const reader = new FileReader();
    reader.onload = () => {
      const img = new Image();
      img.onload = () => {
        try {
          let { width, height } = img;
          if (width > IMG_MAX_WIDTH) {
            height = Math.round(height * IMG_MAX_WIDTH / width);
            width = IMG_MAX_WIDTH;
          }
          const canvas = document.createElement('canvas');
          canvas.width = width;
          canvas.height = height;
          const ctx = canvas.getContext('2d');
          ctx.fillStyle = '#ffffff';
          ctx.fillRect(0, 0, width, height);
          ctx.drawImage(img, 0, 0, width, height);
          const dataUrl = canvas.toDataURL('image/jpeg', IMG_JPEG_QUALITY);
          resolve({ dataUrl, width, height });
        } catch (e) { reject(e); }
      };
      img.onerror = () => reject(new Error('Image illisible.'));
      img.src = reader.result;
    };
    reader.onerror = () => reject(new Error('Lecture du fichier impossible.'));
    reader.readAsDataURL(file);
  });
}

/* ============= AUTO-RECOMPRESSION (briefings importés / hérités) =============
   Parcourt toutes les images du state et recompresse silencieusement celles
   qui dépassent IMG_RECOMPRESS_THRESHOLD via un canvas (JPEG q82, max 1600 px).
   Retourne le nombre d'images recompressées. */
function recompressDataUrl(dataUrl) {
  return new Promise((resolve, reject) => {
    if (typeof dataUrl !== 'string' || !dataUrl.startsWith('data:image/')) {
      resolve(null);  // pas une image valide, on saute
      return;
    }
    if (dataUrl.length < IMG_RECOMPRESS_THRESHOLD) {
      resolve(null);  // déjà sous le seuil
      return;
    }
    const img = new Image();
    img.onload = () => {
      try {
        let { width, height } = img;
        if (width > IMG_MAX_WIDTH) {
          height = Math.round(height * IMG_MAX_WIDTH / width);
          width = IMG_MAX_WIDTH;
        }
        const canvas = document.createElement('canvas');
        canvas.width = width;
        canvas.height = height;
        const ctx = canvas.getContext('2d');
        ctx.fillStyle = '#ffffff';
        ctx.fillRect(0, 0, width, height);
        ctx.drawImage(img, 0, 0, width, height);
        resolve(canvas.toDataURL('image/jpeg', IMG_JPEG_QUALITY));
      } catch (e) { reject(e); }
    };
    img.onerror = () => resolve(null);  // image illisible : on laisse intacte
    img.src = dataUrl;
  });
}

async function recompressOversizedImagesInState(s) {
  if (!s || typeof s !== 'object') return 0;
  let count = 0;
  const tasks = [];

  // Cover map
  if (s.cover && typeof s.cover.mapImage === 'string') {
    tasks.push(['cover.mapImage', s.cover, 'mapImage']);
  }
  // SITAC map
  if (s.sitac && typeof s.sitac.mapImage === 'string') {
    tasks.push(['sitac.mapImage', s.sitac, 'mapImage']);
  }
  // Phases
  if (Array.isArray(s.phases)) {
    s.phases.forEach((ph, pi) => {
      if (typeof ph.mapImage === 'string') {
        tasks.push(['phases[' + pi + '].mapImage', ph, 'mapImage']);
      }
      if (Array.isArray(ph.images)) {
        ph.images.forEach((im, ii) => {
          if (im && typeof im.data === 'string') {
            tasks.push(['phases[' + pi + '].images[' + ii + '].data', im, 'data']);
          }
        });
      }
    });
  }
  // Charts
  if (Array.isArray(s.charts)) {
    s.charts.forEach((ch, ci) => {
      if (ch && typeof ch.img === 'string') {
        tasks.push(['charts[' + ci + '].img', ch, 'img']);
      }
    });
  }
  // Annexes
  if (Array.isArray(s.annexes)) {
    s.annexes.forEach((an, ai) => {
      if (an && typeof an.img === 'string') {
        tasks.push(['annexes[' + ai + '].img', an, 'img']);
      }
    });
  }
  // Photos (brief simplifié)
  if (Array.isArray(s.photos)) {
    s.photos.forEach((ph, pi) => {
      if (ph && typeof ph.img === 'string') {
        tasks.push(['photos[' + pi + '].img', ph, 'img']);
      }
    });
  }
  // Plan radio
  if (s.radioPlan && Array.isArray(s.radioPlan.aircraftPlans)) {
    s.radioPlan.aircraftPlans.forEach((ap, api) => {
      if (ap && typeof ap.image === 'string') {
        tasks.push(['radioPlan.aircraftPlans[' + api + '].image', ap, 'image']);
      }
    });
  }

  // Traitement séquentiel pour éviter de saturer la mémoire
  for (const [path, parent, key] of tasks) {
    try {
      const newUrl = await recompressDataUrl(parent[key]);
      if (newUrl) {
        parent[key] = newUrl;
        count++;
      }
    } catch (e) {
      // silencieux : on ne casse pas le chargement d'un briefing pour une image bizarre
      console.warn('Recompression échouée pour ' + path + ':', e);
    }
  }
  return count;
}

/* ============= EDITOR RENDERING ============= */
function renderEditorBindings() {
  document.querySelectorAll('[data-bind]').forEach(input => {
    const v = getByPath(state, input.dataset.bind);
    if (v != null) input.value = v;
  });

  document.querySelectorAll('[data-img-bind]').forEach(zone => {
    refreshImgZone(zone);
  });

  document.querySelectorAll('[data-list]').forEach(container => {
    renderList(container);
  });

  renderPhaseEditor();
  renderRadioPlan();
  renderRoster();
  renderCharts();
  renderAnnexes();   // nouveau
  renderAirfields(); // aérodromes structurés (Partie 1)
  migrateAirfieldStrings(); // migration silencieuse strings→objets
  renderWingReadOnly();  // P1.B : afficher wing courant en read-only
  renderTargets();       // v2.4.0 : liste des cibles (éditeur simplifié et éditeur complet)
  renderSimpleEditor();  // v2.3.0 : éditeur du brief simplifié + mode courant
}

/* Returns all unique squadron+subgroup+aircraft combos from missions */
function getMissionGroups() {
  const seen = new Map();
  (state.phases || []).forEach(ph => {
    const info = getPhaseSquadronInfo(ph);
    if (!info) return;
    const key = `${info.id}||${info.subgroup}||${info.aircraft}`;
    if (!seen.has(key)) {
      seen.set(key, {
        key,
        id: info.id,
        callsign: info.callsign,
        aircraft: info.aircraft,
        subgroup: info.subgroup,
        isGuest: info.isGuest
      });
    }
  });
  return Array.from(seen.values());
}

/* Compute human-readable label from a missionGroup object or missionKey string.
   - shortLabel : for callsign prefix   (e.g. "Anton", "Duff", "Wolf")
   - label      : group name            (e.g. "KHR-26 ░ ANTON", "WOLF ░ WOLF 1")
   - fullLabel  : with aircraft         (e.g. "KHR-26 ░ ANTON — Mi-8")
   
   Both standard and guest use the same logic:
     label = id [░ subgroup_or_callsign]
   For guests, id = guest squadron name (e.g. "WOLF"), callsign = same.
   Subgroup optional for both types.
*/
function getRosterLabelParts(keyOrGroup) {
  const g = (typeof keyOrGroup === 'string')
    ? getMissionGroups().find(x => x.key === keyOrGroup)
    : keyOrGroup;
  if (!g) return { shortLabel: keyOrGroup || '—', label: keyOrGroup || '—', fullLabel: keyOrGroup || '—' };

  // Unified logic: id + optional (subgroup or callsign)
  // For guests:   id = guest_name, callsign = guest_name → show subgroup if distinct
  // For standard: id = squadron_id, callsign = group_name (FRANKEN), subgroup replaces callsign
  let identifier;
  if (g.isGuest) {
    // Guest: subgroup if different from id (e.g. "WOLF 1" when id = "WOLF")
    identifier = (g.subgroup && g.subgroup !== g.id) ? g.subgroup : null;
  } else {
    // Standard: subgroup replaces callsign
    identifier = g.subgroup || (g.callsign !== g.id ? g.callsign : null);
  }
  const label = g.id + (identifier ? ' ░ ' + identifier : '');

  // Short label for auto-callsign: subgroup if defined, else id
  const shortLabel = identifier || g.id;
  const fullLabel = label + (g.aircraft ? ' — ' + g.aircraft : '');

  return { shortLabel, label, fullLabel };
}

function getRosterLabel(keyOrGroup) {
  return getRosterLabelParts(keyOrGroup).label;
}
function getRosterFullLabel(keyOrGroup) {
  return getRosterLabelParts(keyOrGroup).fullLabel;
}
function getRosterShortLabel(keyOrGroup) {
  return getRosterLabelParts(keyOrGroup).shortLabel;
}

/* ============= ROSTER (ÉQUIPAGE) EDITOR ============= */
function renderRoster() {
  const list = document.getElementById('roster-groups-list');
  const addBtn = document.getElementById('roster-group-add');
  if (!list) return;
  if (!state.roster) state.roster = { groups: [] };

  const missionGroups = getMissionGroups();
  const usedKeys = new Set(state.roster.groups.map(g => g.missionKey));
  const available = missionGroups.filter(g => !usedKeys.has(g.key));
  if (addBtn) addBtn.disabled = available.length === 0;

  list.innerHTML = '';

  if (missionGroups.length === 0) {
    const warn = document.createElement('div');
    warn.className = 'phase-empty';
    warn.textContent = '⚠ ' + t('editor.roster.help');
    list.appendChild(warn);
    return;
  }

  if (state.roster.groups.length === 0) {
    const empty = document.createElement('div');
    empty.className = 'phase-empty';
    empty.textContent = t('editor.roster.noGroup');
    list.appendChild(empty);
    return;
  }

  state.roster.groups.forEach((grp, gi) => {
    const parts = getRosterLabelParts(grp.missionKey);

    const card = document.createElement('div');
    card.className = 'ed-phase-card';

    // SELECT options — all mission groups, disable already-used ones (except self)
    const opts = getMissionGroups().map(g => {
      const isUsedElsewhere = usedKeys.has(g.key) && g.key !== grp.missionKey;
      const p = getRosterLabelParts(g);
      return `<option value="${escapeAttr(g.key)}" ${isUsedElsewhere ? 'disabled' : ''} ${g.key === grp.missionKey ? 'selected' : ''}>
        ${escapeHtml(p.fullLabel)}
      </option>`;
    }).join('');

    card.innerHTML = `
      <div class="phase-num">${t('editor.roster.groupSigle')} ${gi + 1}</div>
      <button type="button" class="phase-rm" data-grp-rm="${gi}">${t('editor.imgCard.remove')}</button>
      <div class="ed-field" style="margin-top:8px;">
        <label>${t('editor.roster.groupSelectLabel')}</label>
        <select class="roster-grp-select">
          <option value="">${t('select.noGroup')}</option>
          ${opts}
        </select>
      </div>
      <div class="ed-field">
        <label>${t('editor.roster.pilotsLabel')}</label>
        <div class="roster-pilots-list"></div>
        <button type="button" class="ed-btn-add" data-pilot-add="${gi}">${t('editor.roster.addPilot')}</button>
      </div>
    `;
    list.appendChild(card);

    card.querySelector('.roster-grp-select').addEventListener('change', e => {
      state.roster.groups[gi].missionKey = e.target.value;
      renderRoster(); schedulePreview();
    });

    card.querySelector(`[data-grp-rm="${gi}"]`).addEventListener('click', () => {
      if (!confirm(t('confirm.deleteGroup'))) return;
      state.roster.groups.splice(gi, 1);
      renderRoster(); schedulePreview();
    });

    renderPilots(card.querySelector('.roster-pilots-list'), gi);

    card.querySelector(`[data-pilot-add="${gi}"]`).addEventListener('click', () => {
      // Auto-generate callsign: shortLabel + " 1-" + (n+1)
      const n = state.roster.groups[gi].pilots.length;
      const prefix = parts.shortLabel;
      const autoCallsign = `${prefix} 1-${n + 1}`;
      state.roster.groups[gi].pilots.push({ name: '', callsign: autoCallsign });
      renderPilots(card.querySelector('.roster-pilots-list'), gi);
      schedulePreview();
    });
  });
}

function renderPilots(container, gi) {
  if (!container) return;
  const pilots = state.roster.groups[gi].pilots;
  container.innerHTML = '';

  if (pilots.length === 0) {
    const empty = document.createElement('div');
    empty.className = 'phase-empty';
    empty.style.fontSize = '11px';
    empty.textContent = t('editor.roster.noPilot');
    container.appendChild(empty);
    return;
  }

  pilots.forEach((pilot, pi) => {
    const row = document.createElement('div');
    row.className = 'roster-pilot-row';
    row.innerHTML = `
      <input type="text" class="rp-name"    placeholder="${t('editor.roster.pilotPlaceholder')}" value="${escapeAttr(pilot.name || '')}">
      <input type="text" class="rp-callsign" placeholder="${t('editor.roster.callsignPlaceholder')}" value="${escapeAttr(pilot.callsign || '')}">
      <button type="button" class="ed-btn-icon" data-pilot-rm="${pi}">×</button>
    `;
    container.appendChild(row);

    row.querySelector('.rp-name').addEventListener('input', e => {
      state.roster.groups[gi].pilots[pi].name = e.target.value; schedulePreview();
    });
    row.querySelector('.rp-callsign').addEventListener('input', e => {
      state.roster.groups[gi].pilots[pi].callsign = e.target.value; schedulePreview();
    });
    row.querySelector(`[data-pilot-rm="${pi}"]`).addEventListener('click', () => {
      state.roster.groups[gi].pilots.splice(pi, 1);
      renderPilots(container, gi); schedulePreview();
    });
  });
}

/* ============= RADIO PLAN EDITOR ============= */
const RADIO_ITEMS_MAX = 6;
const RADIO_AIRCRAFT_MAX = 6;
const RADIO_RADIOS_MAX = 3;
const RADIO_CHANNELS_MAX = 12;

/* ============= BASE RADIO PAR APPAREIL (copie depuis Comm Plan Editor) =============
   Synchroniser si CPE fait évoluer sa ACFT_RADIO_MAP.
   Clé = type DCS, valeur = {slot: "Nom radio (bande)"}. */
const ACFT_RADIO_MAP = {
  // ─── Soviétiques / Russes ─────────────────────────────────────────────
  "Mi-24P":      { 1: "R-863 (VHF/UHF)",   2: "R-828 (VHF FM)",      3: "Jadro-1I (HF)" },
  "Mi-8MT":      { 1: "R-863 (VHF/UHF)",   2: "R-828 (VHF FM)",      3: "Jadro-1A (HF)" },
  "Ka-50_3":     { 1: "R-800L1 (VHF/UHF)", 2: "R-828 (VHF FM)" },
  "MiG-29A":     { 1: "R-862 (VHF/UHF)" },
  "MiG-29S":     { 1: "R-862 (VHF/UHF)" },
  "MiG-29G":     { 1: "R-862 (VHF/UHF)" },
  "MiG-29 Fulcrum": { 1: "R-862 (VHF/UHF)" },
  "MiG-21Bis":   { 1: "R-832M (VHF/UHF)" },
  "MiG-15bis":   { 1: "RSI-6K (HF)" },
  "Su-25T":      { 1: "R-862 (VHF/UHF)" },
  "Su-27":       { 1: "R-862 (VHF/UHF)" },
  "Su-33":       { 1: "R-862 (VHF/UHF)" },
  // ─── OTAN — chasseurs ─────────────────────────────────────────────────
  "F-5E-3":      { 1: "AN/ARC-164 (UHF)" },
  "F-4E-45MC":   { 1: "AN/ARC-164(V) (UHF COMM)",     2: "AN/ARC-164 (UHF AUX)" },
  "F-14B":       { 1: "AN/ARC-159 (UHF - COMM 1)",    2: "AN/ARC-182 (V/UHF - COMM 2)" },
  "F-14A-135-GR":{ 1: "AN/ARC-159 (UHF - COMM 1)",    2: "AN/ARC-182 (V/UHF - COMM 2)" },
  "F-14A-135-GR-Early": { 1: "AN/ARC-159 (UHF - COMM 1)", 2: "AN/ARC-182 (V/UHF - COMM 2)" },
  "F-15C":       { 1: "AN/ARC-164 (UHF)" },
  "F-15ESE":     { 1: "AN/ARC-164 (UHF - COMM 1)",    2: "AN/ARC-186 (V/UHF - COMM 2)" },
  "F-16C_50":    { 1: "AN/ARC-164 (UHF - COMM 1)",    2: "AN/ARC-222 (V/UHF - COMM 2)" },
  "FA-18C_hornet":{ 1: "AN/ARC-210 (V/UHF - COMM 1)", 2: "AN/ARC-210 (V/UHF - COMM 2)" },
  "JF-17":       { 1: "R&S M3AR (V/UHF - COMM 1)",    2: "R&S M3AR (V/UHF - COMM 2)" },
  // ─── OTAN — Mirage F1 ─────────────────────────────────────────────────
  "Mirage-F1CE": { 1: "TRAP 138 (UHF - Principale)",  2: "TRAP 139 (V/UHF - Auxiliaire)" },
  "Mirage-F1BE": { 1: "TRAP 138 (UHF - Principale)",  2: "TRAP 139 (V/UHF - Auxiliaire)" },
  "Mirage-F1CR": { 1: "TRAP 138 (UHF - Principale)",  2: "TRAP 139 (V/UHF - Auxiliaire)" },
  "Mirage-F1EE": { 1: "TRAP 136 (V/UHF - Verte)",     2: "TRAP 137B (UHF - Rouge)" },
  "Mirage-F1M":  { 1: "TRAP 136 (V/UHF - Verte)",     2: "TRAP 137B (UHF - Rouge)" },
  "M-2000C":     { 1: "TRT ERA 7000 (V/UHF)",          2: "TRT ERA 7200 (UHF Auxiliaire)" },
  // ─── Attaque / CAS ────────────────────────────────────────────────────
  "A-10C":       { 1: "AN/ARC-186 (VHF AM)", 2: "AN/ARC-164 (UHF)",  3: "AN/ARC-186 (VHF FM)" },
  "A-10C_2":     { 1: "AN/ARC-186 (VHF AM)", 2: "AN/ARC-164 (UHF)",  3: "AN/ARC-186 (VHF FM)" },
  "AV8BNA":      { 1: "AN/ARC-210 (V/UHF - COMM 1)", 2: "AN/ARC-210 (V/UHF - COMM 2)" },
  // ─── Hélicoptères OTAN ────────────────────────────────────────────────
  "AH-64D_BLK_II": {
    1: "AN/ARC-186 (VHF - COMM 1)", 2: "AN/ARC-164 (UHF - COMM 2)",
    3: "AN/ARC-201D (FM1 - COMM 3)", 4: "AN/ARC-201D (FM2 - COMM 4)",
    5: "AN/ARC-220 (HF - COMM 5)"
  },
  "CH-47Fbl1": {
    1: "AN/ARC-186 (VHF AM/FM)", 2: "AN/ARC-164 (UHF AM)",
    3: "AN/ARC-201D (VHF FM1)", 4: "AN/ARC-201D (VHF FM2)", 5: "AN/ARC-220 (HF)"
  },
  "UH-1H":       { 1: "AN/ARC-134 (VHF AM)", 2: "AN/ARC-131 (VHF FM)", 3: "AN/ARC-51BX (UHF)" },
  "OH58D":       { 1: "AN/ARC-186 (VHF AM/FM)", 2: "AN/ARC-164 (UHF)", 3: "AN/ARC-201 (VHF FM)" },
  // ─── Hélicoptères français — Gazelles ─────────────────────────────────
  "SA342L":      { 1: "Manta TRAP 138 (V/UHF)", 2: "Manta TRAP 139 (V/UHF)" },
  "SA342M":      { 1: "Manta TRAP 138 (V/UHF)", 2: "Manta TRAP 139 (V/UHF)" },
  "SA342Minigun":{ 1: "Manta TRAP 138 (V/UHF)", 2: "Manta TRAP 139 (V/UHF)" },
  "SA342Mistral":{ 1: "Manta TRAP 138 (V/UHF)", 2: "Manta TRAP 139 (V/UHF)" },
  // ─── Transport ────────────────────────────────────────────────────────
  "C-130J-30":   { 1: "AN/ARC-210 (V/UHF - COMM 1)", 2: "AN/ARC-210 (V/UHF - COMM 2)" },
  "Hercules":    { 1: "AN/ARC-164 (UHF)", 2: "AN/ARC-186 (VHF)" },
};

/* Alias libellé BG (libre) → clé DCS de ACFT_RADIO_MAP.
   Normalisation : toLowerCase().trim(), espaces/tirets condensés en espace simple.
   Priorité : exact → alias → sous-chaîne → null. */
const AIRCRAFT_RADIO_ALIAS = {
  // Mi-24
  "mi 24p": "Mi-24P", "mi24p": "Mi-24P", "mi-24p": "Mi-24P",
  "mi 24": "Mi-24P",  "mi24":  "Mi-24P",  "hind":  "Mi-24P",
  // Mi-8
  "mi 8mt": "Mi-8MT", "mi8mt": "Mi-8MT", "mi-8mt": "Mi-8MT",
  "mi 8": "Mi-8MT",   "mi8":   "Mi-8MT",  "hip":   "Mi-8MT",
  // Ka-50
  "ka 50": "Ka-50_3", "ka50": "Ka-50_3", "ka-50": "Ka-50_3", "hokum": "Ka-50_3",
  // F-16
  "f 16": "F-16C_50", "f16": "F-16C_50", "f-16": "F-16C_50", "viper": "F-16C_50",
  "f 16c": "F-16C_50", "f16c": "F-16C_50",
  // F-4
  "f 4": "F-4E-45MC", "f4": "F-4E-45MC", "f-4": "F-4E-45MC",
  "phantom": "F-4E-45MC", "f 4e": "F-4E-45MC", "f4e": "F-4E-45MC",
  "f 4e phantom ii": "F-4E-45MC", "f-4e phantom ii": "F-4E-45MC",
  // F-5
  "f 5": "F-5E-3", "f5": "F-5E-3", "f-5": "F-5E-3",
  "f 5e": "F-5E-3", "f5e": "F-5E-3", "tiger ii": "F-5E-3",
  // F-15
  "f 15e": "F-15ESE", "f15e": "F-15ESE", "f-15e": "F-15ESE",
  "strike eagle": "F-15ESE", "f 15e strike eagle": "F-15ESE",
  "f 15": "F-15C",  "f15":  "F-15C",  "f-15": "F-15C", "eagle": "F-15C",
  // F-14
  "f 14": "F-14B", "f14": "F-14B", "f-14": "F-14B", "tomcat": "F-14B",
  "f 14b": "F-14B", "f14b": "F-14B",
  // FA-18
  "fa 18": "FA-18C_hornet", "fa18": "FA-18C_hornet", "fa-18": "FA-18C_hornet",
  "f 18": "FA-18C_hornet",  "f18":  "FA-18C_hornet",  "hornet": "FA-18C_hornet",
  "f/a 18": "FA-18C_hornet", "f/a18": "FA-18C_hornet",
  // Mirage F1
  "mirage f1": "Mirage-F1CE", "miragem f1": "Mirage-F1CE",
  "f1": "Mirage-F1CE", "mirage f1ce": "Mirage-F1CE",
  // M-2000
  "m 2000": "M-2000C", "m2000": "M-2000C", "m-2000": "M-2000C",
  "mirage 2000": "M-2000C", "mirage2000": "M-2000C",
  // A-10
  "a 10": "A-10C_2", "a10": "A-10C_2", "a-10": "A-10C_2",
  "warthog": "A-10C_2", "hog": "A-10C_2",
  // AH-64
  "ah 64": "AH-64D_BLK_II", "ah64": "AH-64D_BLK_II", "ah-64": "AH-64D_BLK_II",
  "apache": "AH-64D_BLK_II", "apache ah 64d": "AH-64D_BLK_II",
  "ah 64d": "AH-64D_BLK_II", "ah-64d": "AH-64D_BLK_II",
  // UH-1
  "uh 1": "UH-1H", "uh1": "UH-1H", "uh-1": "UH-1H",
  "huey": "UH-1H", "iroquois": "UH-1H",
  // Gazelle
  "gazelle": "SA342M", "sa342": "SA342M", "sa 342": "SA342M",
  "sa342m": "SA342M", "sa 342m": "SA342M",
  // MiG-29
  "mig 29": "MiG-29S", "mig29": "MiG-29S", "mig-29": "MiG-29S", "fulcrum": "MiG-29S",
  // MiG-21
  "mig 21": "MiG-21Bis", "mig21": "MiG-21Bis", "mig-21": "MiG-21Bis", "fishbed": "MiG-21Bis",
  // Su-25
  "su 25": "Su-25T", "su25": "Su-25T", "su-25": "Su-25T", "frogfoot": "Su-25T",
  // Su-27
  "su 27": "Su-27", "su27": "Su-27", "su-27": "Su-27", "flanker": "Su-27",
};

function _normalizeAcft(name) {
  return (name || '').toLowerCase().trim().replace(/[\s\-]+/g, ' ');
}

function resolveAircraftRadioKey(name) {
  if (!name) return null;
  // 1. Match exact
  if (ACFT_RADIO_MAP[name]) return name;
  const norm = _normalizeAcft(name);
  // 2. Alias
  if (AIRCRAFT_RADIO_ALIAS[norm]) return AIRCRAFT_RADIO_ALIAS[norm];
  // 3. Sous-chaîne heuristique (clé contient le nom ou inversement)
  const normLow = norm;
  for (const key of Object.keys(ACFT_RADIO_MAP)) {
    const keyNorm = _normalizeAcft(key);
    if (keyNorm.includes(normLow) || normLow.includes(keyNorm)) return key;
  }
  return null;
}

// Catalogue complet dédupliqué + trié (repli appareil non reconnu)
function getRadioCatalogue() {
  const set = new Set();
  for (const slots of Object.values(ACFT_RADIO_MAP)) {
    for (const name of Object.values(slots)) set.add(name);
  }
  return Array.from(set).sort();
}

// Radios pour un appareil donné, ou null si non résolu
function getRadiosForAircraft(name) {
  const key = resolveAircraftRadioKey(name);
  if (!key) return null;
  return Object.values(ACFT_RADIO_MAP[key]);
}

function genId(prefix) {
  return prefix + '_' + Math.random().toString(36).slice(2, 8);
}

function ensureRadioPlanShape() {
  if (!state.radioPlan) state.radioPlan = { items: [], aircraftPlans: [] };
  if (!Array.isArray(state.radioPlan.items)) state.radioPlan.items = [];
  if (!Array.isArray(state.radioPlan.aircraftPlans)) state.radioPlan.aircraftPlans = [];
  // Migration silencieuse (2b) : items sans showOnOverview → cocher les ≤6 premiers
  state.radioPlan.items.forEach((it, idx) => {
    if (!it.id) it.id = genId('it');
    if (it.showOnOverview === undefined) it.showOnOverview = idx < 6;
  });
}

function renderRadioPlan() {
  ensureRadioPlanShape();
  renderRadioItems();
  renderRadioAircrafts();
}

function renderRadioItems() {
  const list = document.getElementById('radio-items-list');
  if (!list) return;
  list.innerHTML = '';
  const items = state.radioPlan.items;
  const addBtn = document.getElementById('radio-item-add');
  if (addBtn) addBtn.disabled = false; // illimité — RADIO_ITEMS_MAX retiré (2b)

  // Compteur showOnOverview (2b)
  const checkedCount = items.filter(it => it.showOnOverview).length;

  // Mise à jour du compteur dans le label de section (2b)
  const sectionLabel = document.querySelector('[data-i18n="editor.radio.items"]');
  if (sectionLabel) {
    sectionLabel.textContent = t('editor.radio.items') + '  ' + checkedCount + '/6';
  }

  items.forEach((it, i) => {
    const row = document.createElement('div');
    row.className = 'ed-radio-item-row';
    const isChecked = it.showOnOverview;
    // Désactiver si déjà 6 cochés et celui-ci n'est pas coché (2b)
    const checkDisabled = !isChecked && checkedCount >= 6;
    row.innerHTML = `
      <label class="ri-overview-check" title="${t('editor.radio.overviewCheckTooltip') || 'Afficher dans l\'aperçu (max 6)'}">
        <input type="checkbox" data-ri-overview ${isChecked ? 'checked' : ''} ${checkDisabled ? 'disabled' : ''}>
      </label>
      <input type="text" data-ri-label placeholder="${t('editor.radio.labelEx')}">
      <input type="text" data-ri-freq placeholder="${t('editor.radio.freqLabel')}">
      <select data-ri-mod>
        <option value="AM">AM</option>
        <option value="FM">FM</option>
      </select>
      <button type="button" class="ed-btn-icon" data-ri-rm aria-label="${t('editor.phases.remove')}">×</button>
    `;
    row.querySelector('[data-ri-label]').value = it.label || '';
    row.querySelector('[data-ri-freq]').value = it.frequency || '';
    row.querySelector('[data-ri-mod]').value = it.modulation || 'AM';

    row.querySelector('[data-ri-overview]').addEventListener('change', e => {
      items[i].showOnOverview = e.target.checked;
      renderRadioItems(); // re-render pour recalculer le compteur et les disabled (2b)
      schedulePreview();
    });
    // Debounce pour éviter le jank avec beaucoup d'appareils/canaux (2a)
    let _riDebounce = null;
    const scheduleAircraftRefresh = () => {
      clearTimeout(_riDebounce);
      _riDebounce = setTimeout(() => renderRadioAircrafts(), 150);
    };
    row.querySelector('[data-ri-label]').addEventListener('input', e => {
      items[i].label = e.target.value;
      scheduleAircraftRefresh(); // met à jour les dropdowns en temps réel (2a)
      schedulePreview();
    });
    row.querySelector('[data-ri-freq]').addEventListener('input', e => {
      items[i].frequency = e.target.value;
      scheduleAircraftRefresh(); // met à jour les dropdowns en temps réel (2a)
      schedulePreview();
    });
    row.querySelector('[data-ri-mod]').addEventListener('change', e => {
      items[i].modulation = e.target.value;
      schedulePreview();
    });
    row.querySelector('[data-ri-rm]').addEventListener('click', () => {
      const removedId = items[i].id;
      items.splice(i, 1);
      // Clean up references in aircraftPlans
      state.radioPlan.aircraftPlans.forEach(ap => {
        (ap.radios || []).forEach(r => {
          (r.channels || []).forEach(ch => {
            if (ch.itemId === removedId) ch.itemId = '';
          });
        });
      });
      renderRadioPlan();
      schedulePreview();
    });
    list.appendChild(row);
  });

  if (items.length === 0) {
    const empty = document.createElement('div');
    empty.className = 'phase-empty';
    empty.textContent = t('editor.radio.addItem');
    list.appendChild(empty);
  }
}

function renderRadioAircrafts() {
  const list = document.getElementById('radio-aircraft-list');
  if (!list) return;
  list.innerHTML = '';
  const plans = state.radioPlan.aircraftPlans;
  const addBtn = document.getElementById('radio-aircraft-add');
  if (addBtn) addBtn.disabled = false; // illimité — RADIO_AIRCRAFT_MAX retiré (2a)

  if (plans.length === 0) {
    const empty = document.createElement('div');
    empty.className = 'phase-empty';
    empty.textContent = t('editor.radio.addAircraft');
    list.appendChild(empty);
    return;
  }

  plans.forEach((ap, ai) => {
    const card = document.createElement('div');
    card.className = 'ed-phase-card';
    card.innerHTML = `
      <div class="phase-num">${t('editor.phases.aircraftSigle')} ${ai + 1}</div>
      <button type="button" class="phase-rm" data-ap-rm="${ai}">${t('editor.imgCard.remove')}</button>
      <div class="ed-field"><label>${t('editor.phases.aircraft')}</label>
        <select data-ap-aircraft="${ai}">
          ${getAllAircraft().map(a => `<option value="${escapeAttr(a)}">${escapeHtml(a)}</option>`).join('')}
          <option value="__custom__">${t('select.customAircraft')}</option>
        </select>
      </div>
      <div class="ed-field" data-ap-custom-wrap="${ai}" style="display:none;">
        <label>${t('editor.radio.customName')}</label>
        <input type="text" data-ap-custom="${ai}">
      </div>
      <div class="ed-field">
        <label>${t('editor.radio.helpAircraft').substring(0, 35)}...</label>
        <label class="ed-img-zone" data-img-bind="radioPlan.aircraftPlans.${ai}.image">
          <input type="file" accept="image/*">
          <span class="img-text" data-i18n="editor.imgZone.tap">▲ CHARGER IMAGE ▲</span>
        </label>
      </div>
      <div class="ed-field" data-radios-wrap="${ai}">
        <label>${t('editor.radio.radiosChannelsLabel')}</label>
        <div data-radios-list="${ai}"></div>
        <button type="button" class="ed-btn-add" data-radio-add="${ai}">${t('editor.radio.addRadio')}</button>
      </div>
    `;
    list.appendChild(card);

    // Set aircraft selector
    const acSel = card.querySelector(`[data-ap-aircraft="${ai}"]`);
    const isCustom = !getAllAircraft().includes(ap.aircraft) && ap.aircraft;
    if (isCustom) {
      acSel.value = '__custom__';
      const wrap = card.querySelector(`[data-ap-custom-wrap="${ai}"]`);
      const cust = card.querySelector(`[data-ap-custom="${ai}"]`);
      wrap.style.display = '';
      cust.value = ap.aircraft;
    } else if (ap.aircraft) {
      acSel.value = ap.aircraft;
    }

    acSel.addEventListener('change', () => {
      const wrap = card.querySelector(`[data-ap-custom-wrap="${ai}"]`);
      if (acSel.value === '__custom__') {
        wrap.style.display = '';
        const cust = card.querySelector(`[data-ap-custom="${ai}"]`);
        plans[ai].aircraft = cust.value || '';
      } else {
        wrap.style.display = 'none';
        plans[ai].aircraft = acSel.value;
      }
      schedulePreview();
    });
    card.querySelector(`[data-ap-custom="${ai}"]`).addEventListener('input', e => {
      plans[ai].aircraft = e.target.value;
      schedulePreview();
    });

    card.querySelector(`[data-ap-rm="${ai}"]`).addEventListener('click', () => {
      if (!confirm(t('confirm.deleteRadioAc') + ' ' + (ai + 1) + ' ?')) return;
      plans.splice(ai, 1);
      renderRadioAircrafts();
      schedulePreview();
    });

    // If image set, dim radios area and add note
    const radiosWrap = card.querySelector(`[data-radios-wrap="${ai}"]`);
    if (ap.image) {
      radiosWrap.style.opacity = '0.5';
      const note = document.createElement('div');
      note.className = 'ed-help';
      note.style.color = 'var(--amber)';
      note.textContent = t('editor.radio.imgNote');
      radiosWrap.insertBefore(note, radiosWrap.firstChild);
    }

    // Render radios
    renderAircraftRadios(card.querySelector(`[data-radios-list="${ai}"]`), ai);

    card.querySelector(`[data-radio-add="${ai}"]`).addEventListener('click', () => {
      if (!plans[ai].radios) plans[ai].radios = [];
      if (plans[ai].radios.length >= RADIO_RADIOS_MAX) return;
      plans[ai].radios.push({ name: '', channels: [] }); // champ vide → combobox datalist (P0)
      renderRadioAircrafts();
      schedulePreview();
    });

    refreshImgZone(card.querySelector(`[data-img-bind="radioPlan.aircraftPlans.${ai}.image"]`));
  });
}

function renderAircraftRadios(container, ai) {
  const ap = state.radioPlan.aircraftPlans[ai];
  container.innerHTML = '';
  (ap.radios || []).forEach((r, ri) => {
    const block = document.createElement('div');
    block.className = 'ed-radio-block';
    // Combobox nom radio : filtré par appareil ou catalogue complet (B.4)
    const dlId = `dl-radio-${ai}-${ri}`;
    const radioOptions = getRadiosForAircraft(ap.aircraft) || getRadioCatalogue();
    const datalistHtml = `<datalist id="${dlId}">${radioOptions.map(n => `<option value="${escapeAttr(n)}">`).join('')}</datalist>`;
    block.innerHTML = `
      <div class="ed-radio-block-head">
        ${datalistHtml}
        <input type="text" list="${dlId}" data-r-name placeholder="${t('editor.radio.radioName')}">
        <button type="button" class="ed-btn-icon" data-r-rm aria-label="${t('editor.radio.delChanAriaLabel')}">×</button>
      </div>
      <div data-channels-list class="ed-channels-list"></div>
      <button type="button" class="ed-btn-add ed-btn-add-sm" data-channel-add>${t('editor.radio.addChannel')}</button>
    `;
    block.querySelector('[data-r-name]').value = r.name || '';
    block.querySelector('[data-r-name]').addEventListener('input', e => {
      r.name = e.target.value;
      schedulePreview();
    });
    block.querySelector('[data-r-rm]').addEventListener('click', () => {
      ap.radios.splice(ri, 1);
      renderRadioAircrafts();
      schedulePreview();
    });

    const chList = block.querySelector('[data-channels-list]');
    renderChannels(chList, ai, ri);

    block.querySelector('[data-channel-add]').addEventListener('click', () => {
      if (!r.channels) r.channels = [];
      if (r.channels.length >= RADIO_CHANNELS_MAX) return;
      r.channels.push({ channel: r.channels.length, itemId: '' });
      renderChannels(chList, ai, ri);
      schedulePreview();
    });
    container.appendChild(block);
  });
}

function renderChannels(container, ai, ri) {
  const r = state.radioPlan.aircraftPlans[ai].radios[ri];
  container.innerHTML = '';
  const items = state.radioPlan.items;

  (r.channels || []).forEach((ch, ci) => {
    // Normalize legacy channels without mode field
    if (!ch.mode) ch.mode = 'item';
    const isCustom = ch.mode === 'custom';

    const row = document.createElement('div');
    row.className = 'ed-channel-row' + (isCustom ? ' custom-mode' : '');

    // Toggle button (tablet-friendly, always first cell)
    const toggleBtn = document.createElement('button');
    toggleBtn.type = 'button';
    toggleBtn.className = 'ed-ch-toggle' + (isCustom ? ' is-custom' : '');
    toggleBtn.textContent = isCustom ? 'FR' : 'IT';
    toggleBtn.title = isCustom ? t('editor.radio.freeFreqTooltip') : t('editor.radio.globalItemTooltip');
    toggleBtn.addEventListener('click', () => {
      if (ch.mode === 'custom') {
        ch.mode = 'item';
        delete ch.label; delete ch.frequency; delete ch.modulation;
        if (!ch.itemId) ch.itemId = '';
      } else {
        ch.mode = 'custom';
        ch.label = ''; ch.frequency = ''; ch.modulation = 'AM';
        ch.itemId = '';
      }
      renderChannels(container, ai, ri);
      schedulePreview();
    });
    row.appendChild(toggleBtn);

    // Channel number input
    const chNumInput = document.createElement('input');
    chNumInput.type = 'number';
    chNumInput.placeholder = t('editor.radio.chLabel');
    chNumInput.min = '0';
    chNumInput.value = ch.channel ?? '';
    chNumInput.addEventListener('input', e => {
      const v = e.target.value;
      ch.channel = v === '' ? '' : parseInt(v, 10);
      schedulePreview();
    });
    row.appendChild(chNumInput);

    if (isCustom) {
      // Label input
      const labelInput = document.createElement('input');
      labelInput.type = 'text';
      labelInput.placeholder = t('editor.radio.chanLabel');
      labelInput.value = ch.label || '';
      labelInput.addEventListener('input', e => { ch.label = e.target.value; schedulePreview(); });
      row.appendChild(labelInput);

      // Frequency input
      const freqInput = document.createElement('input');
      freqInput.type = 'text';
      freqInput.placeholder = t('editor.radio.chanFreq');
      freqInput.value = ch.frequency || '';
      freqInput.addEventListener('input', e => { ch.frequency = e.target.value; schedulePreview(); });
      row.appendChild(freqInput);

      // Modulation select
      const modSel = document.createElement('select');
      modSel.innerHTML = '<option value="AM">AM</option><option value="FM">FM</option>';
      modSel.value = ch.modulation || 'AM';
      modSel.addEventListener('change', e => { ch.modulation = e.target.value; schedulePreview(); });
      row.appendChild(modSel);
    } else {
      // Item select
      const opts = [`<option value="">${t('select.noItem')}</option>`]
        .concat(items.map(it => `<option value="${escapeAttr(it.id)}">${escapeHtml(it.label || it.frequency || '\u2014')}</option>`))
        .join('');
      const itemSel = document.createElement('select');
      itemSel.innerHTML = opts;
      itemSel.value = ch.itemId || '';
      itemSel.addEventListener('change', e => { ch.itemId = e.target.value; schedulePreview(); });
      row.appendChild(itemSel);
    }

    // Delete button
    const rmBtn = document.createElement('button');
    rmBtn.type = 'button';
    rmBtn.className = 'ed-btn-icon';
    rmBtn.setAttribute('aria-label', t('editor.radio.delChanAriaLabel'));
    rmBtn.textContent = '×';
    rmBtn.addEventListener('click', () => {
      r.channels.splice(ci, 1);
      renderChannels(container, ai, ri);
      schedulePreview();
    });
    row.appendChild(rmBtn);

    container.appendChild(row);
  });
}

function renderList(container) {
  const path = container.dataset.list;
  const items = getByPath(state, path) || [];
  container.innerHTML = '';
  items.forEach((val, i) => {
    const row = document.createElement('div');
    row.className = 'ed-list-item';
    const isLong = (val || '').length > 60;
    if (isLong) {
      row.innerHTML = `<textarea rows="2"></textarea><button type="button" class="ed-btn-icon" aria-label="Supprimer">×</button>`;
      row.querySelector('textarea').value = val;
    } else {
      row.innerHTML = `<input type="text"><button type="button" class="ed-btn-icon" aria-label="Supprimer">×</button>`;
      row.querySelector('input').value = val;
    }
    const inp = row.querySelector('input,textarea');
    inp.addEventListener('input', () => {
      const arr = getByPath(state, path);
      arr[i] = inp.value;
      schedulePreview();
    });
    row.querySelector('button').addEventListener('click', () => {
      const arr = getByPath(state, path);
      arr.splice(i, 1);
      renderList(container);
      schedulePreview();
    });
    container.appendChild(row);
  });
}

/* PHASE EDITOR (single-phase view with selector) */
function renderPhaseEditor() {
  const container = document.getElementById('phase-editor');
  const indicator = document.getElementById('phase-indicator');
  const total = state.phases.length;

  // clamp index
  if (currentPhaseIdx >= total) currentPhaseIdx = Math.max(0, total - 1);
  if (currentPhaseIdx < 0) currentPhaseIdx = 0;

  // disable nav buttons when applicable
  document.getElementById('phase-prev').disabled = currentPhaseIdx === 0 || total === 0;
  document.getElementById('phase-next').disabled = currentPhaseIdx >= total - 1 || total === 0;
  document.getElementById('phase-rm').disabled = total === 0;
  document.getElementById('phase-dup').disabled = total === 0;
  document.getElementById('phase-up').disabled = currentPhaseIdx === 0 || total === 0;
  document.getElementById('phase-down').disabled = currentPhaseIdx >= total - 1 || total === 0;

  if (total === 0) {
    indicator.innerHTML = `<strong>0</strong> / 0`;
    container.innerHTML = `<div class="phase-empty">${t('editor.phases.noMission')}<br>${t('editor.phases.addFirst')}</div>`;
    return;
  }

  indicator.innerHTML = `${t('editor.phases.indicatorLabel')} <strong>${currentPhaseIdx + 1}</strong> / ${total}`;

  const ph = state.phases[currentPhaseIdx];
  const i = currentPhaseIdx;

  // Build squadron options — known + guest option
  const sqOptions = [`<option value="">${t('select.noSquadron')}</option>`]
    .concat(wingConfig.squadrons.map(s => {
      const aircraftLabel = s.aircraft.length === 1 ? s.aircraft[0] : s.aircraft.join(' / ');
      return `<option value="${s.id}">${escapeHtml(s.id)} ${escapeHtml(s.callsign)} — ${escapeHtml(aircraftLabel)}</option>`;
    }))
    .concat([`<option value="__guest__">${t('editor.phases.guestOption')}</option>`])
    .join('');

  const isGuest = ph.squadron === '__guest__';
  const selectedSq = isGuest ? null : getSquadron(ph.squadron);
  const showAircraftSelector = !isGuest && selectedSq && selectedSq.aircraft.length > 1;

  let aircraftSelectorHtml = '';
  if (showAircraftSelector) {
    const acOpts = selectedSq.aircraft.map(a => `<option value="${escapeAttr(a)}">${escapeHtml(a)}</option>`).join('');
    aircraftSelectorHtml = `
      <div class="ed-field"><label>${t('editor.phases.aircraft')}</label>
        <select id="pf-aircraft">${acOpts}</select>
      </div>`;
  }

  // Guest fields
  const guestData = ph.guestSquadron || { name: '', subgroup: '', aircraft: '' };
  const guestFieldsHtml = isGuest ? `
    <div class="ed-guest-fields">
      <div class="ed-field"><label>${t('editor.phases.guestName')}</label>
        <input id="pf-guest-name" type="text" value="${escapeAttr(guestData.name)}" placeholder="${t('placeholder.guestName')}">
      </div>
      <div class="ed-field"><label>${t('editor.phases.guestSub')}</label>
        <input id="pf-guest-sub" type="text" value="${escapeAttr(guestData.subgroup)}" placeholder="${t('placeholder.guestName')} 1 ${t('placeholder.optional')}">
      </div>
      <div class="ed-field"><label>${t('editor.phases.guestAircraft')}</label>
        <input id="pf-guest-aircraft" type="text" value="${escapeAttr(guestData.aircraft)}" placeholder="${t('placeholder.guestAircraft')}">
      </div>
    </div>` : '';

  container.innerHTML = `
    <div class="ed-field"><label>${t('editor.phases.title')}</label><input id="pf-title" type="text" value="${escapeAttr(ph.title || '')}"></div>
    <div class="ed-field"><label>${t('editor.phases.squadron')}</label>
      <select id="pf-squadron">${sqOptions}</select>
    </div>
    ${guestFieldsHtml}
    ${aircraftSelectorHtml}
    <div class="ed-field"><label>${t('editor.phases.subgroup')} <span class="ed-label-hint">${t('editor.phases.subgroupHint')}</span></label>
      <input id="pf-subgroup" type="text" value="${escapeAttr(ph.subgroup || '')}" placeholder="${t('placeholder.subgroup')}">
    </div>
    <div class="ed-field"><label>${t('editor.phases.objective')}</label><textarea id="pf-objective" rows="3">${escapeHtml(ph.objective || '')}</textarea></div>
    <div class="ed-field">
      <label>${t('editor.phases.execSteps')}</label>
      <div class="ed-list" id="phase-exec-list"></div>
      <button type="button" class="ed-btn-add" id="phase-exec-add">${t('editor.phases.addStep')}</button>
    </div>
    <div class="ed-field-row">
      <div class="ed-field"><label>${t('editor.phases.flightPlan')}</label><input id="pf-flightPlan" type="text" value="${escapeAttr(ph.flightPlan || '')}"></div>
      <div class="ed-field"><label>${t('editor.phases.threatLevel')}</label>
        <select id="pf-threatLevel">
          <option value="low" data-i18n="threatLevel.low">Faible</option>
          <option value="moderate" data-i18n="threatLevel.moderate">Modéré</option>
          <option value="high" data-i18n="threatLevel.high">Élevé</option>
        </select>
      </div>
    </div>
    <div class="ed-field"><label>${t('editor.phases.notes')}</label><textarea id="pf-notes" rows="3">${escapeHtml(ph.notes || '')}</textarea></div>
    <div class="ed-field">
      <label>${t('editor.phases.images')}</label>
      <div class="ed-img-list" id="phase-images-list"></div>
      <button type="button" class="ed-btn-add" id="phase-img-add">${t('editor.phases.addImage')}</button>
    </div>
  `;

  // Set select values
  container.querySelector('#pf-threatLevel').value = ph.threatLevel || 'low';
  container.querySelector('#pf-squadron').value = ph.squadron || '';
  if (showAircraftSelector) {
    container.querySelector('#pf-aircraft').value = ph.aircraft || selectedSq.aircraft[0];
  }

  // Bind text/textarea fields
  ['title', 'objective', 'flightPlan', 'threatLevel', 'notes'].forEach(field => {
    const el = container.querySelector(`#pf-${field}`);
    if (!el) return;
    el.addEventListener('input', () => { state.phases[i][field] = el.value; schedulePreview(); });
    if (el.tagName === 'SELECT') {
      el.addEventListener('change', () => { state.phases[i][field] = el.value; schedulePreview(); });
    }
  });

  // Subgroup
  const subgroupEl = container.querySelector('#pf-subgroup');
  subgroupEl.addEventListener('input', () => { state.phases[i].subgroup = subgroupEl.value; schedulePreview(); renderRoster(); });

  // Guest fields
  if (isGuest) {
    if (!state.phases[i].guestSquadron) state.phases[i].guestSquadron = { name: '', subgroup: '', aircraft: '' };
    container.querySelector('#pf-guest-name').addEventListener('input', e => {
      state.phases[i].guestSquadron.name = e.target.value; schedulePreview(); renderRoster();
    });
    container.querySelector('#pf-guest-sub').addEventListener('input', e => {
      state.phases[i].guestSquadron.subgroup = e.target.value; schedulePreview(); renderRoster();
    });
    container.querySelector('#pf-guest-aircraft').addEventListener('input', e => {
      state.phases[i].guestSquadron.aircraft = e.target.value; schedulePreview(); renderRoster();
    });
  }

  // Squadron selector re-render on change
  container.querySelector('#pf-squadron').addEventListener('change', e => {
    const newSqId = e.target.value;
    state.phases[i].squadron = newSqId;
    if (newSqId === '__guest__') {
      if (!state.phases[i].guestSquadron) state.phases[i].guestSquadron = { name: '', subgroup: '', aircraft: '' };
      state.phases[i].aircraft = '';
    } else {
      const newSq = getSquadron(newSqId);
      if (!newSq) state.phases[i].aircraft = '';
      else if (newSq.aircraft.length === 1) state.phases[i].aircraft = newSq.aircraft[0];
      else if (!newSq.aircraft.includes(state.phases[i].aircraft)) state.phases[i].aircraft = newSq.aircraft[0];
    }
    renderPhaseEditor(); schedulePreview(); renderRoster();
  });

  // Aircraft selector (multi-aircraft squadrons only)
  const acSel = container.querySelector('#pf-aircraft');
  if (acSel) {
    acSel.addEventListener('change', e => { state.phases[i].aircraft = e.target.value; schedulePreview(); renderRoster(); });
  }

  // Exec list
  const execList = container.querySelector('#phase-exec-list');
  renderPhaseExec(execList, i);
  container.querySelector('#phase-exec-add').addEventListener('click', () => {
    state.phases[i].execution = normalizeExecution(state.phases[i].execution);
    state.phases[i].execution.push({ text: '', subtasks: [] });
    renderPhaseExec(execList, i); schedulePreview();
  });

  // Images list
  normalizePhaseImages(state.phases[i]);
  renderPhaseImages(container.querySelector('#phase-images-list'), i);
  container.querySelector('#phase-img-add').addEventListener('click', () => {
    state.phases[i].images.push({ title: '', data: '', caption: '' });
    renderPhaseImages(container.querySelector('#phase-images-list'), i);
    schedulePreview();
  });

  // Traduire les options data-i18n injectées dynamiquement (threatLevel)
  applyI18nStatic();
}

/* ============= PHASE IMAGES EDITOR ============= */
function renderPhaseImages(listEl, phaseIdx) {
  if (!listEl) return;
  // Always read directly from state — never capture a reference that could be invalidated
  // by normalizePhaseImages or any other array replacement elsewhere
  const imgs = state.phases[phaseIdx].images;
  listEl.innerHTML = '';

  if (imgs.length === 0) {
    const empty = document.createElement('div');
    empty.className = 'phase-empty';
    empty.textContent = t('editor.phases.noImage');
    listEl.appendChild(empty);
    return;
  }

  imgs.forEach((img, k) => {
    const card = document.createElement('div');
    card.className = 'ed-img-card';
    // Use distinct class names instead of shared data-k attribute to avoid querySelector ambiguity
    card.innerHTML = `
      <div class="ed-img-card-num">IMAGE ${k + 1}</div>
      <button type="button" class="ed-img-card-rm" data-card-rm="${k}">${t('editor.imgCard.remove')}</button>
      <div class="ed-field" style="margin-top:8px;">
        <label>${t('editor.phases.imgTitle')}</label>
        <input type="text" class="img-title-inp" value="${escapeAttr(img.title)}" placeholder="${t('placeholder.imgTitle')}">
      </div>
      <div class="ed-field">
        <label>${t('editor.image.label')}</label>
        <label class="ed-img-zone ${img.data ? 'has-img' : ''}" data-phase-img-zone="${phaseIdx}-${k}">
          <input type="file" accept="image/*">
          ${img.data
            ? `<img src="${img.data}" alt="Image ${k + 1}">`
            : `<span class="img-text">${t('editor.imgZone.tapShort')}</span>`}
          ${img.data ? `<button type="button" class="img-rm">×</button>` : ''}
        </label>
      </div>
      <div class="ed-field">
        <label>${t('editor.phases.imgCaption')}</label>
        <textarea class="img-caption-inp" rows="2" placeholder="${t('editor.phases.imgCaptionPlaceholder')}">${escapeHtml(img.caption)}</textarea>
      </div>
    `;
    listEl.appendChild(card);

    // ALL event handlers reference state.phases[phaseIdx].images[k] directly.
    // Closing over `phaseIdx` and `k` (primitives) is safe — they don't get invalidated.
    // Closing over `imgs[k]` (object reference) would be unsafe.

    // Title — direct state access
    const titleInp = card.querySelector('.img-title-inp');
    titleInp.addEventListener('input', () => {
      state.phases[phaseIdx].images[k].title = titleInp.value;
      schedulePreview();
    });

    // Caption — direct state access
    const captionInp = card.querySelector('.img-caption-inp');
    captionInp.addEventListener('input', () => {
      state.phases[phaseIdx].images[k].caption = captionInp.value;
      schedulePreview();
    });

    // Remove entire card (Suppr. button)
    card.querySelector(`[data-card-rm="${k}"]`).addEventListener('click', () => {
      state.phases[phaseIdx].images.splice(k, 1);
      renderPhaseImages(listEl, phaseIdx);
      schedulePreview();
    });

    // Image upload
    const zone = card.querySelector(`[data-phase-img-zone="${phaseIdx}-${k}"]`);
    const fileInput = zone.querySelector('input[type=file]');
    fileInput.addEventListener('change', async e => {
      const f = e.target.files[0];
      if (!f) return;
      try {
        const { dataUrl } = await compressImageFile(f);
        state.phases[phaseIdx].images[k].data = dataUrl;
        renderPhaseImages(listEl, phaseIdx);
        schedulePreview();
      } catch (err) {
        showToast(t('toast.imageError') + err.message);
      }
      e.target.value = '';
    });

    // Remove image data only (× button — keeps card)
    const rmImg = zone.querySelector('.img-rm');
    if (rmImg) {
      rmImg.addEventListener('click', e => {
        e.preventDefault();
        e.stopPropagation();
        state.phases[phaseIdx].images[k].data = '';
        renderPhaseImages(listEl, phaseIdx);
        schedulePreview();
      });
    }
  });
}

/* Normalize threatLevel to canonical keys: 'low' | 'moderate' | 'high'
   Migre les anciennes valeurs textuelles FR (Faible/Modéré/Élevé) et legacy
   (Danger, Important) vers les clés canoniques. */
function normalizeThreatLevel(lvl) {
  if (!lvl) return 'low';
  // Déjà canonique
  if (lvl === 'low' || lvl === 'moderate' || lvl === 'high') return lvl;
  // Migration exacte depuis la table
  if (THREAT_LEGACY_MAP[lvl]) return THREAT_LEGACY_MAP[lvl];
  // Correspondance floue (anciens briefings) — normalisation accentuée
  const k = lvl.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
  if (k.includes('elev') || k.includes('danger') || k.includes('important') || k.includes('critiqu')) return 'high';
  if (k.includes('moder')) return 'moderate';
  return 'low';
}

/* Normalize phase images: migrate legacy mapImage → images[] */
function normalizePhaseImages(ph) {
  if (!Array.isArray(ph.images)) ph.images = [];
  // Migrate legacy single mapImage field
  if (ph.mapImage && ph.images.length === 0) {
    ph.images = [{ title: t('phase.defaultMapTitle'), data: ph.mapImage, caption: '' }];
  }
  // Ensure each entry has all fields
  ph.images = ph.images.map(img => ({
    title: img.title || '',
    data: img.data || img.mapImage || '',
    caption: img.caption || ''
  }));
  delete ph.mapImage; // clean up legacy field
}
/* Normalize charts: migrate legacy annexes.chart1Name/chart1Img/chart2Name/chart2Img to charts[] */
function normalizeCharts(state) {
  if (!Array.isArray(state.charts)) state.charts = [];
  // Migration legacy : ancien objet annexes avec chart1Name/chart1Img/chart2Name/chart2Img
  if (state.annexes && !Array.isArray(state.annexes)) {
    const legacy = state.annexes;
    if (legacy.chart1Name || legacy.chart1Img) {
      state.charts.push({ name: legacy.chart1Name || '', img: legacy.chart1Img || '' });
    }
    if (legacy.chart2Name || legacy.chart2Img) {
      state.charts.push({ name: legacy.chart2Name || '', img: legacy.chart2Img || '' });
    }
    state.annexes = []; // tableau vide pour Chat H2 à venir
  }
  // Si annexes n'existait pas du tout
  if (!Array.isArray(state.annexes)) state.annexes = [];
  // Normalisation des entrées
  state.charts = state.charts.map(c => ({ name: c.name || '', img: c.img || '' }));
}
// Normalize annexes: ensure shape {title, img, caption} for each entry
function normalizeAnnexes(state) {
  if (!Array.isArray(state.annexes)) state.annexes = [];
  state.annexes = state.annexes.map(a => ({
    title: a.title || '',
    img: a.img || '',
    caption: a.caption || ''
  }));
}
function normalizeExecution(exec) {
  if (!Array.isArray(exec)) return [];
  return exec.map(s => {
    if (typeof s === 'string') return { text: s, subtasks: [] };
    return { text: s.text || '', subtasks: Array.isArray(s.subtasks) ? s.subtasks : [] };
  });
}

function renderCharts() {
  const listEl = document.getElementById('charts-list');
  if (!listEl) return;
  const charts = state.charts;
  listEl.innerHTML = '';

  if (charts.length === 0) {
    const empty = document.createElement('div');
    empty.className = 'phase-empty';
    empty.textContent = t('editor.charts.noChart');
    listEl.appendChild(empty);
    return;
  }

  charts.forEach((chart, k) => {
    const card = document.createElement('div');
    card.className = 'ed-img-card';
    card.innerHTML = `
      <div class="ed-img-card-num">CHART ${k + 1}</div>
      <button type="button" class="ed-img-card-rm" data-chart-rm="${k}">${t('editor.imgCard.remove')}</button>
      <div class="ed-field" style="margin-top:8px;">
        <label>${t('editor.charts.airportLabel')}</label>
        <input type="text" class="chart-name-inp" value="${escapeAttr(chart.name)}" placeholder="${t('placeholder.chartName')}">
      </div>
      <div class="ed-field">
        <label>${t('editor.image.label')}</label>
        <label class="ed-img-zone ${chart.img ? 'has-img' : ''}" data-chart-img-zone="${k}">
          <input type="file" accept="image/*">
          ${chart.img
            ? `<img src="${chart.img}" alt="Chart ${k + 1}">`
            : `<span class="img-text">${t('editor.imgZone.tapShort')}</span>`}
          ${chart.img ? `<button type="button" class="img-rm">\u00d7</button>` : ''}
        </label>
      </div>
    `;
    listEl.appendChild(card);
  });

  // Bindings — calque sur renderPhaseImages
  listEl.querySelectorAll('.chart-name-inp').forEach((inp, k) => {
    inp.addEventListener('input', () => {
      state.charts[k].name = inp.value;
      schedulePreview();
    });
  });

  listEl.querySelectorAll('[data-chart-rm]').forEach(btn => {
    btn.addEventListener('click', () => {
      const k = parseInt(btn.dataset.chartRm, 10);
      state.charts.splice(k, 1);
      renderCharts();
      schedulePreview();
    });
  });

  listEl.querySelectorAll('[data-chart-img-zone]').forEach(zone => {
    const k = parseInt(zone.dataset.chartImgZone, 10);
    const fileInp = zone.querySelector('input[type="file"]');
    fileInp.addEventListener('change', async e => {
      const f = e.target.files[0];
      if (!f) return;
      showToast(t('toast.imageCompressing'));
      try {
        const { dataUrl } = await compressImageFile(f);
        state.charts[k].img = dataUrl;
        renderCharts();
        schedulePreview();
        showToast(t('toast.imageLoaded'));
      } catch (err) {
        showToast(t('toast.imageError') + err.message);
      }
      e.target.value = '';
    });
    const rmImg = zone.querySelector('.img-rm');
    if (rmImg) {
      rmImg.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        state.charts[k].img = '';
        renderCharts();
        schedulePreview();
      });
    }
  });
}

function renderAnnexes() {
  const listEl = document.getElementById('annexes-list');
  if (!listEl) return;
  const annexes = state.annexes;
  listEl.innerHTML = '';

  if (annexes.length === 0) {
    const empty = document.createElement('div');
    empty.className = 'phase-empty';
    empty.textContent = t('editor.annexes.noAnnex');
    listEl.appendChild(empty);
    return;
  }

  annexes.forEach((annexe, k) => {
    const card = document.createElement('div');
    card.className = 'ed-img-card';
    card.innerHTML = `
      <div class="ed-img-card-num">${t('editor.annexes.numSigle')} ${k + 1}</div>
      <button type="button" class="ed-img-card-rm" data-annexe-rm="${k}">${t('editor.imgCard.remove')}</button>
      <div class="ed-field" style="margin-top:8px;">
        <label>${t('editor.annexes.titleLabel')}</label>
        <input type="text" class="annexe-title-inp" value="${escapeAttr(annexe.title)}" placeholder="${t('placeholder.annexeTitle')}">
      </div>
      <div class="ed-field">
        <label>${t('editor.image.label')}</label>
        <label class="ed-img-zone ${annexe.img ? 'has-img' : ''}" data-annexe-img-zone="${k}">
          <input type="file" accept="image/*">
          ${annexe.img
            ? `<img src="${annexe.img}" alt="Annexe ${k + 1}">`
            : `<span class="img-text">${t('editor.imgZone.tapShort')}</span>`}
          ${annexe.img ? `<button type="button" class="img-rm">\u00d7</button>` : ''}
        </label>
      </div>
      <div class="ed-field">
        <label>${t('editor.annexes.captionLabel')}</label>
        <textarea class="annexe-caption-inp" rows="2" placeholder="${t('editor.annexes.captionPlaceholder')}">${escapeHtml(annexe.caption)}</textarea>
      </div>
    `;
    listEl.appendChild(card);
  });

  // Bindings — calque strict sur renderCharts avec ajout du caption
  listEl.querySelectorAll('.annexe-title-inp').forEach((inp, k) => {
    inp.addEventListener('input', () => {
      state.annexes[k].title = inp.value;
      schedulePreview();
    });
  });

  listEl.querySelectorAll('.annexe-caption-inp').forEach((ta, k) => {
    ta.addEventListener('input', () => {
      state.annexes[k].caption = ta.value;
      schedulePreview();
    });
  });

  listEl.querySelectorAll('[data-annexe-rm]').forEach(btn => {
    btn.addEventListener('click', () => {
      const k = parseInt(btn.dataset.annexeRm, 10);
      state.annexes.splice(k, 1);
      renderAnnexes();
      schedulePreview();
    });
  });

  listEl.querySelectorAll('[data-annexe-img-zone]').forEach(zone => {
    const k = parseInt(zone.dataset.annexeImgZone, 10);
    const fileInp = zone.querySelector('input[type="file"]');
    fileInp.addEventListener('change', async e => {
      const f = e.target.files[0];
      if (!f) return;
      showToast(t('toast.imageCompressing'));
      try {
        const { dataUrl } = await compressImageFile(f);
        state.annexes[k].img = dataUrl;
        renderAnnexes();
        schedulePreview();
        showToast(t('toast.imageLoaded'));
      } catch (err) {
        showToast(t('toast.imageError') + err.message);
      }
      e.target.value = '';
    });
    const rmImg = zone.querySelector('.img-rm');
    if (rmImg) {
      rmImg.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        state.annexes[k].img = '';
        renderAnnexes();
        schedulePreview();
      });
    }
  });
}


/* ============= CLOUD PRESETS TABLE (copie depuis Weather Editor — re-sync si WX évolue) ============= */
const CLOUD_PRESETS_BG = {
  'Preset1':'FEW',  'Preset2':'FEW',
  'Preset3':'SCT',  'Preset4':'SCT',  'Preset5':'SCT',  'Preset6':'SCT',
  'Preset7':'SCT',  'Preset8':'SCT',  'Preset9':'SCT',  'Preset10':'SCT',
  'Preset11':'SCT', 'Preset12':'SCT',
  'Preset13':'BKN', 'Preset14':'BKN', 'Preset15':'BKN', 'Preset16':'BKN',
  'Preset17':'BKN', 'Preset18':'BKN', 'Preset19':'BKN', 'Preset20':'BKN',
  'Preset21':'OVC', 'Preset22':'OVC', 'Preset23':'OVC', 'Preset24':'OVC',
  'Preset25':'OVC', 'Preset26':'OVC', 'Preset27':'OVC',
  'RainyPreset4':'SCT',  'NEWRAINPRESET4':'SCT',
  'RainyPreset5':'BKN',
  'RainyPreset1':'OVC',  'RainyPreset2':'OVC',  'RainyPreset3':'OVC', 'RainyPreset6':'OVC',
};

/* ============= ASSISTANT METAR — 10A (formulaire) + 10C (import .miz) ============= */

function _randomAirportIcao() {
  const airports = (state.mission.farp || []).filter(a => typeof a === 'object' && !a.isFarp && a.icao);
  if (!airports.length) return '';
  return airports[Math.floor(Math.random() * airports.length)].icao;
}

function buildMetarString(p) {
  let s = '';
  if (p.icao)  s += p.icao.toUpperCase() + ' ';
  if (p.ddhhmm) s += p.ddhhmm + 'Z ';
  // Vent
  if (p.calm)       s += '00000KT ';
  else if (p.vrb)   s += 'VRB' + String(p.windSpd||0).padStart(2,'0') + 'KT ';
  else {
    const dir = String(p.windDir||0).padStart(3,'0');
    const spd = String(p.windSpd||0).padStart(2,'0');
    const gust = p.windGust ? 'G' + String(p.windGust).padStart(2,'0') : '';
    s += dir + spd + gust + 'KT ';
  }
  // Visibilité
  if (p.cavok) s += 'CAVOK ';
  else {
    const vis = p.visibility;
    if (!vis || vis >= 10000) s += '9999 ';
    else s += String(vis) + ' ';
    // Phénomènes
    if (p.phenomena && p.phenomena.length) s += p.phenomena.join('') + ' ';
    // Nuages
    if (p.cloudCover && p.cloudCover !== 'NSC') {
      const base = String(Math.round((p.cloudBase||1500)/30.48)).padStart(3,'0');
      s += p.cloudCover + base + ' ';
    } else if (p.cloudCover === 'NSC') s += 'NSC ';
  }
  // Temp/rosée
  const temp = p.temp != null ? (p.temp < 0 ? 'M' + String(Math.abs(p.temp)).padStart(2,'0') : String(p.temp).padStart(2,'0')) : 'XX';
  const dew  = p.dew  != null ? (p.dew  < 0 ? 'M' + String(Math.abs(p.dew)).padStart(2,'0')  : String(p.dew).padStart(2,'0'))  : 'XX';
  s += temp + '/' + dew + ' ';
  // QNH
  if (p.qnh) {
    if (p.qnhInHg) s += 'A' + Math.round(p.qnh * 100) + ' ';
    else           s += 'Q' + Math.round(p.qnh) + ' ';
  }
  return s.trim();
}

function parseMetarString(str) {
  if (!str) return null;
  try {
    const p = { icao:'', ddhhmm:'', calm:false, vrb:false, windDir:0, windSpd:0, windGust:null,
                cavok:false, visibility:9999, phenomena:[], cloudCover:'SCT', cloudBase:1500,
                temp:20, dew:15, qnh:1013, qnhInHg:false };
    const parts = str.trim().split(/\s+/);
    let i = 0;
    // ICAO
    if (/^[A-Z]{4}$/.test(parts[i])) { p.icao = parts[i++]; }
    // DDhhmmZ
    if (/^\d{6}Z$/.test(parts[i])) { p.ddhhmm = parts[i++].replace('Z',''); }
    // Vent
    if (parts[i]) {
      const wm = parts[i].match(/^(\d{3}|VRB)(\d{2,3})(?:G(\d{2,3}))?KT$/);
      if (wm) {
        if (wm[1]==='VRB') p.vrb=true;
        else { p.windDir=parseInt(wm[1]); if(p.windDir===0 && parseInt(wm[2])===0) p.calm=true; }
        p.windSpd=parseInt(wm[2]);
        if(wm[3]) p.windGust=parseInt(wm[3]);
        i++;
      }
    }
    // CAVOK/visibilité
    if (parts[i]==='CAVOK') { p.cavok=true; i++; }
    else if (/^\d{4}$/.test(parts[i])) { p.visibility=parseInt(parts[i++]); }
    // Phénomènes (RA SN BR FG TS DU SA avec intensité)
    const phRe = /^[-+]?(RA|SN|BR|FG|TS|DU|SA)$/;
    while (parts[i] && phRe.test(parts[i])) { p.phenomena.push(parts[i++]); }
    // Nuages
    const cloudRe = /^(FEW|SCT|BKN|OVC|NSC)(\d{3})?$/;
    if (parts[i] && cloudRe.test(parts[i])) {
      const cm = parts[i].match(cloudRe);
      p.cloudCover = cm[1];
      if(cm[2]) p.cloudBase = parseInt(cm[2])*30.48;
      i++;
    }
    // Temp/dew
    if (parts[i] && /^M?\d+\/M?\d+$/.test(parts[i])) {
      const td = parts[i].split('/');
      p.temp = parseInt(td[0].replace('M','-').replace(/^-/,v=>v));
      if(td[0].startsWith('M')) p.temp = -parseInt(td[0].slice(1));
      p.dew  = parseInt(td[1].replace('M','-'));
      if(td[1].startsWith('M')) p.dew = -parseInt(td[1].slice(1));
      i++;
    }
    // QNH
    if (parts[i] && /^Q\d{4}$/.test(parts[i])) { p.qnh=parseInt(parts[i++].slice(1)); }
    else if (parts[i] && /^A\d{4}$/.test(parts[i])) { p.qnh=parseInt(parts[i++].slice(1))/100; p.qnhInHg=true; }
    return p;
  } catch(e) { return null; }
}

function _missionDateToDDhhmm(mdate) {
  // mdate = { Year, Day, Month } + state.missionDate.startTime (secondes depuis minuit)
  // On extrait DD et hhmm depuis la date mission si disponible
  try {
    if (mdate && mdate.Day) {
      const dd = String(mdate.Day).padStart(2,'0');
      const sec = mdate.startTime || 0;
      const hh = String(Math.floor(sec/3600)).padStart(2,'0');
      const mm = String(Math.floor((sec%3600)/60)).padStart(2,'0');
      return dd + hh + mm;
    }
  } catch(e) {}
  return '';
}

let _metarParams = null;

function openMetarAssistant() {
  const panel = document.getElementById('metar-assistant-panel');
  if (!panel) return;
  panel.style.display = '';
  panel.open = true;
  // Initialiser les params depuis le champ METAR existant ou defaults
  const existing = state.sitac && state.sitac.metar;
  let params = existing ? parseMetarString(existing) : null;
  if (!params) {
    params = {
      icao: _randomAirportIcao(), ddhhmm:'', calm:false, vrb:false,
      windDir:270, windSpd:8, windGust:null,
      cavok:true, visibility:9999, phenomena:[], cloudCover:'SCT', cloudBase:1500,
      temp:20, dew:15, qnh:1013, qnhInHg:false
    };
    if (existing) {
      // Avertir parsing échoué mais ne pas écraser le champ
      console.warn('METAR Assistant: parse failed, starting fresh');
    }
  }
  if (!params.icao) params.icao = _randomAirportIcao();
  _metarParams = params;
  renderMetarAssistant(params);
}

function renderMetarAssistant(p) {
  const cont = document.getElementById('metar-assistant-content');
  if (!cont) return;
  const preview = buildMetarString(p);
  cont.innerHTML = `
    <div class="metar-form">
      <div class="metar-row">
        <div class="metar-field"><label>ICAO</label>
          <input id="ma-icao" type="text" value="${escapeAttr(p.icao||'')}" placeholder="LCRA" maxlength="4"></div>
        <div class="metar-field"><label>DDhhmmZ</label>
          <input id="ma-ddhhmm" type="text" value="${escapeAttr(p.ddhhmm||'')}" placeholder="250700" maxlength="6"></div>
      </div>
      <div class="metar-row">
        <label class="metar-check-label"><input id="ma-calm" type="checkbox" ${p.calm?'checked':''}> Calme (00000KT)</label>
        <label class="metar-check-label"><input id="ma-vrb" type="checkbox" ${p.vrb?'checked':''}> VRB</label>
        <div class="metar-field"><label>Dir °</label>
          <input id="ma-wdir" type="number" min="0" max="360" value="${p.windDir||0}" ${p.calm||p.vrb?'disabled':''}></div>
        <div class="metar-field"><label>Vit kt</label>
          <input id="ma-wspd" type="number" min="0" max="99" value="${p.windSpd||0}" ${p.calm?'disabled':''}></div>
        <div class="metar-field" id="ma-gust-wrap">
          <label>Rafales kt</label>
          <input id="ma-gust" type="number" min="0" max="99" value="${p.windGust||''}" placeholder="—"></div>
      </div>
      <div class="metar-row">
        <label class="metar-check-label"><input id="ma-cavok" type="checkbox" ${p.cavok?'checked':''}> CAVOK</label>
        <div class="metar-field" ${p.cavok?'style="display:none"':''} id="ma-vis-wrap">
          <label>Visibilité m</label>
          <input id="ma-vis" type="number" min="0" max="9999" value="${p.cavok?9999:p.visibility}"></div>
      </div>
      <div class="metar-row" id="ma-clouds-wrap" ${p.cavok?'style="display:none"':''}>
        <div class="metar-field"><label>Nuages</label>
          <select id="ma-cloud">
            ${['NSC','FEW','SCT','BKN','OVC'].map(c=>`<option value="${c}" ${p.cloudCover===c?'selected':''}>${c}</option>`).join('')}
          </select></div>
        <div class="metar-field" id="ma-base-wrap" ${p.cloudCover==='NSC'?'style="display:none"':''}>
          <label>Base ft</label>
          <input id="ma-base" type="number" min="0" step="100" value="${Math.round(p.cloudBase/0.3048/100)*100||1500}"></div>
      </div>
      <div class="metar-row">
        <div class="metar-field"><label>Temp °C</label>
          <input id="ma-temp" type="number" min="-50" max="50" value="${p.temp!=null?p.temp:20}"></div>
        <div class="metar-field"><label>Rosée °C</label>
          <input id="ma-dew" type="number" min="-50" max="50" value="${p.dew!=null?p.dew:15}"></div>
        <div class="metar-field"><label>QNH hPa</label>
          <input id="ma-qnh" type="number" min="900" max="1100" value="${p.qnhInHg?Math.round(p.qnh*33.864):p.qnh||1013}"></div>
      </div>
      <details class="metar-more">
        <summary>▸ Plus</summary>
        <div class="metar-row" style="flex-wrap:wrap;gap:6px;">
          ${['RA','SN','BR','FG','TS','DU','SA'].map(ph=>`<label class="metar-check-label"><input type="checkbox" class="ma-phenom" value="${ph}" ${(p.phenomena||[]).includes(ph)?'checked':''}> ${ph}</label>`).join('')}
        </div>
      </details>
      <div class="metar-preview-line">${escapeHtml(preview)}</div>
      <div class="metar-actions">
        <button type="button" class="ed-btn-add" id="ma-import-miz">📥 Importer .miz</button>
        <input type="file" id="ma-miz-input" accept=".miz" style="display:none">
        <button type="button" class="ed-btn-add" id="ma-insert">✔ Insérer dans METAR</button>
      </div>
    </div>
  `;

  // Wirer les événements
  const update = () => {
    _metarParams = _readMetarForm();
    const prev = document.querySelector('.metar-preview-line');
    if (prev) prev.textContent = buildMetarString(_metarParams);
  };

  const fields = ['ma-icao','ma-ddhhmm','ma-wdir','ma-wspd','ma-gust','ma-vis','ma-base','ma-temp','ma-dew','ma-qnh'];
  fields.forEach(id => { const el=document.getElementById(id); if(el) el.addEventListener('input', update); });
  ['ma-calm','ma-vrb','ma-cavok','ma-cloud'].forEach(id => {
    const el=document.getElementById(id); if(el) el.addEventListener('change', () => { _metarParams=_readMetarForm(); renderMetarAssistant(_metarParams); });
  });
  document.querySelectorAll('.ma-phenom').forEach(cb => cb.addEventListener('change', update));

  document.getElementById('ma-insert').addEventListener('click', () => {
    const newMetar = buildMetarString(_metarParams);
    if (state.sitac && state.sitac.metar && state.sitac.metar.trim() && state.sitac.metar.trim() !== newMetar) {
      if (!confirm(t('editor.sitac.metarOverwrite'))) return;
    }
    state.sitac.metar = newMetar;
    // Mettre à jour le champ data-bind
    document.querySelectorAll('[data-bind="sitac.metar"]').forEach(inp => { inp.value = newMetar; });
    schedulePreview();
    document.getElementById('metar-assistant-panel').open = false;
  });

  // Import .miz (10C)
  document.getElementById('ma-import-miz').addEventListener('click', () => {
    document.getElementById('ma-miz-input').click();
  });
  document.getElementById('ma-miz-input').addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    try {
      await _importMizToMetar(file);
    } catch(err) {
      alert('Erreur lecture .miz : ' + err.message);
    }
    e.target.value = '';
  });
}

function _readMetarForm() {
  const g = id => document.getElementById(id);
  const v = id => { const el=g(id); return el?el.value:''; };
  const c = id => { const el=g(id); return el?el.checked:false; };
  const n = id => { const el=g(id); const val=parseFloat(el&&el.value); return isNaN(val)?0:val; };
  const calm = c('ma-calm'), vrb = c('ma-vrb'), cavok = c('ma-cavok');
  const cloud = v('ma-cloud');
  const phenom = [...document.querySelectorAll('.ma-phenom:checked')].map(cb=>cb.value);
  return {
    icao:     v('ma-icao').toUpperCase().slice(0,4),
    ddhhmm:   v('ma-ddhhmm').slice(0,6),
    calm, vrb,
    windDir:  n('ma-wdir'), windSpd:  n('ma-wspd'),
    windGust: v('ma-gust') ? n('ma-gust') : null,
    cavok, visibility: n('ma-vis'),
    phenomena: phenom,
    cloudCover: cloud,
    cloudBase:  n('ma-base') * 0.3048,
    temp:  n('ma-temp'), dew: n('ma-dew'),
    qnh:   n('ma-qnh'), qnhInHg: false
  };
}

async function _importMizToMetar(file) {
  // Confirmation si des champs sont déjà remplis
  if (_metarParams && (_metarParams.windSpd > 0 || _metarParams.cavok === false)) {
    if (!confirm(t('editor.sitac.metarMizOverwrite'))) return;
  }
  // Lecture JSZip (déjà embarqué)
  const buf = await file.arrayBuffer();
  const zip  = await JSZip.loadAsync(buf);
  const missionFile = zip.file('mission');
  if (!missionFile) throw new Error('Fichier "mission" absent du .miz');
  const lua = await missionFile.async('string');

  // --- Parsing par regex tolérantes ---
  function extractNum(re, def) {
    const m = lua.match(re);
    return m ? parseFloat(m[1]) : def;
  }
  function extractStr(re, def) {
    const m = lua.match(re);
    return m ? m[1] : def;
  }

  // Vent : direction (dir au sol → vient de = (dir+180)%360), vitesse m/s → kt
  const windDirMiz = extractNum(/\["atGround"\][\s\S]*?\["dir"\]\s*=\s*([\d.]+)/, 0);
  const windSpdMs  = extractNum(/\["atGround"\][\s\S]*?\["speed"\]\s*=\s*([\d.]+)/, 0);
  const windDir = Math.round((windDirMiz + 180) % 360);
  const windSpd = Math.round(windSpdMs * 1.944);

  // QNH : mmHg → hPa
  const qnhMmhg = extractNum(/\["qnh"\]\s*=\s*([\d.]+)/, 760);
  const qnh = Math.round(qnhMmhg * 1.333);

  // Visibilité : m ; ≥10000 → CAVOK
  const visM = extractNum(/\["distance"\]\s*=\s*([\d.]+)/, 9999);
  const cavok = visM >= 10000;

  // Température °C
  const temp = Math.round(extractNum(/\["temperature"\]\s*=\s*(-?[\d.]+)/, 15));

  // Nuages : preset → FEW/SCT/BKN/OVC
  const presetId = extractStr(/\["preset"\]\s*=\s*"([^"]+)"/, '');
  let cloudCover = 'SCT';
  let cloudBase  = 1500; // ft par défaut
  if (presetId && CLOUD_PRESETS_BG[presetId]) {
    const fam = CLOUD_PRESETS_BG[presetId];
    cloudCover = fam.replace(/\+RA$/,'').replace(/\+R$/,''); // enlever +RA pour code METAR
  } else if (!presetId) {
    // Pas de preset : density → couverture approximative
    const density = extractNum(/\["density"\]\s*=\s*([\d]+)/, 0);
    if      (density === 0) cloudCover = 'NSC';
    else if (density <= 3)  cloudCover = 'FEW';
    else if (density <= 6)  cloudCover = 'SCT';
    else if (density <= 8)  cloudCover = 'BKN';
    else                    cloudCover = 'OVC';
  }
  // Base nuages : m → ft
  const baseM = extractNum(/\["base"\]\s*=\s*([\d.]+)/, 457.2); // ~1500ft
  cloudBase = Math.round(baseM / 0.3048);

  // Brouillard/brume → phénomènes
  const phenomena = [];
  const fogEnabled = /\["enable_fog"\]\s*=\s*true/.test(lua);
  if (fogEnabled) {
    const fogVis = extractNum(/\["fog"\][\s\S]*?\["visibility"\]\s*=\s*([\d]+)/, 9999);
    if (fogVis < 1000) phenomena.push('FG');
    else if (fogVis < 5000) phenomena.push('BR');
  }
  // Dust/Sand
  if (/\["dust_density"\]\s*=\s*(?!0)/.test(lua)) phenomena.push('DU');

  // Date/heure mission → DDhhmmZ
  const mDay    = extractNum(/\["Day"\]\s*=\s*([\d]+)/, 1);
  const startSec = extractNum(/\["start_time"\]\s*=\s*([\d]+)/, 0);
  const hh = String(Math.floor(startSec/3600)).padStart(2,'0');
  const mm = String(Math.floor((startSec%3600)/60)).padStart(2,'0');
  const ddhhmm = String(Math.round(mDay)).padStart(2,'0') + hh + mm;

  // ICAO = aléatoire parmi aérodromes non-FARP du briefing (pas dans le .miz)
  const icao = _randomAirportIcao() || '';

  const params = {
    icao, ddhhmm,
    calm: windSpd === 0, vrb: false,
    windDir, windSpd, windGust: null,
    cavok, visibility: Math.min(visM, 9999),
    phenomena, cloudCover, cloudBase,
    temp, dew: Math.max(temp - 5, -30),
    qnh, qnhInHg: false
  };
  _metarParams = params;
  renderMetarAssistant(params);
}

/* ============= AÉRODROMES STRUCTURÉS (Partie 1 — 10B-lite) =============
   Copie de re-sync : si le modèle évolue, mettre à jour ici aussi.
   migration : string → objet (pattern annexes→charts). */

function migrateAirfieldStrings() {
  if (!state.mission) return;
  if (!Array.isArray(state.mission.farp)) return;
  state.mission.farp = state.mission.farp.map(f => {
    if (typeof f === 'object' && f !== null) return f; // déjà objet
    // Migration string → objet
    const str = String(f).trim();
    const obj = { icao: '', name: '', isFarp: /^(FARP|FOB)\b/i.test(str), rwy: '', atc: false };
    // Séparer sur ' – ' / ' - ' / ':'
    const sepMatch = str.match(/^(.+?)(?:\s*[–\-:]\s*(?:Piste en service\s*[:\-]?\s*|Cap D\/A\s*[:\-]?\s*)?)?(\d+)?(.*)$/i);
    if (sepMatch) {
      obj.name = (sepMatch[1] || str).trim();
      if (sepMatch[2]) obj.rwy = sepMatch[2].trim();
    } else {
      obj.name = str;
    }
    return obj;
  });
}

function renderAirfields() {
  migrateAirfieldStrings();
  // deux éditeurs : mode complet (#airfields-list) et brief simplifié (#s-airfields-list)
  ['airfields-list', 's-airfields-list'].forEach(id => renderAirfieldsInto(document.getElementById(id)));
}

function renderAirfieldsInto(list) {
  if (!list) return;
  list.innerHTML = '';
  const items = state.mission.farp || [];

  items.forEach((af, i) => {
    const row = document.createElement('div');
    row.className = 'ed-airfield-row';
    const isFarp = !!af.isFarp;
    const rwyLabel = isFarp ? t('editor.mission.rwyFarp') : t('editor.mission.rwyAirport');
    row.innerHTML = `
      <input type="text" class="af-icao" placeholder="ICAO" value="${escapeAttr(af.icao || '')}" ${isFarp ? 'disabled' : ''}>
      <label class="af-farp-check" title="${t('editor.mission.farpCheck')}">
        <input type="checkbox" class="af-farp" ${isFarp ? 'checked' : ''}> ${t('editor.mission.farpCheck')}
      </label>
      <input type="text" class="af-name" placeholder="${t('editor.mission.name')}" value="${escapeAttr(af.name || '')}">
      <input type="text" class="af-rwy" placeholder="${rwyLabel}" value="${escapeAttr(af.rwy || '')}">
      <label class="af-atc-check" title="${t('editor.mission.atc')}">
        <input type="checkbox" class="af-atc" ${af.atc ? 'checked' : ''}> ${t('editor.mission.atc')}
      </label>
      <button type="button" class="ed-btn-icon af-rm" aria-label="${t('editor.imgCard.remove')}">×</button>
    `;

    const icaoInp = row.querySelector('.af-icao');
    const farpChk = row.querySelector('.af-farp');
    const nameInp = row.querySelector('.af-name');
    const rwyInp  = row.querySelector('.af-rwy');
    const atcChk  = row.querySelector('.af-atc');
    const rmBtn   = row.querySelector('.af-rm');

    farpChk.addEventListener('change', e => {
      items[i].isFarp = e.target.checked;
      if (e.target.checked) { items[i].icao = ''; }
      renderAirfields(); schedulePreview();
    });
    icaoInp.addEventListener('input', e => { items[i].icao = e.target.value; schedulePreview(); });
    nameInp.addEventListener('input', e => { items[i].name = e.target.value; schedulePreview(); });
    rwyInp.addEventListener('input',  e => { items[i].rwy  = e.target.value; schedulePreview(); });
    atcChk.addEventListener('change', e => { items[i].atc  = e.target.checked; schedulePreview(); });
    rmBtn.addEventListener('click', () => { items.splice(i, 1); renderAirfields(); schedulePreview(); });

    list.appendChild(row);
  });

  if (items.length === 0) {
    const empty = document.createElement('div');
    empty.className = 'phase-empty';
    empty.textContent = t('editor.mission.addFarp');
    list.appendChild(empty);
  }
}

function renderAirfieldPreviewItems() {
  const items = (state.mission.farp || []).filter(f => typeof f === 'object' && f !== null);
  if (!items.length) return '';
  return items.map(af => {
    const parts = [];
    if (!af.isFarp && af.icao) parts.push(escapeHtml(af.icao));
    parts.push(escapeHtml(af.name || '—'));
    if (af.rwy) {
      const label = af.isFarp ? t('preview.capLabel') : 'RWY';
      parts.push(label + ' ' + escapeHtml(af.rwy));
    }
    parts.push(af.atc ? t('preview.atc') : t('preview.autoinfo'));
    return '<li>' + parts.join(' — ') + '</li>';
  }).join('');
}

function renderPhaseExec(container, phaseIdx) {
  const ph = state.phases[phaseIdx];
  // Normalize on first encounter
  ph.execution = normalizeExecution(ph.execution);
  const steps = ph.execution;
  container.innerHTML = '';

  steps.forEach((step, j) => {
    const wrap = document.createElement('div');
    wrap.style.marginBottom = '8px';

    // Step row: [move up] [move down] [input] [remove]
    const row = document.createElement('div');
    row.className = 'ed-list-item';
    row.style.alignItems = 'center';

    // Move buttons
    const moveDiv = document.createElement('div');
    moveDiv.className = 'ed-list-move';

    const upBtn = document.createElement('button');
    upBtn.type = 'button'; upBtn.className = 'ed-btn-move';
    upBtn.textContent = '▲'; upBtn.disabled = j === 0;
    upBtn.addEventListener('click', () => {
      if (j === 0) return;
      [steps[j-1], steps[j]] = [steps[j], steps[j-1]];
      renderPhaseExec(container, phaseIdx); schedulePreview();
    });

    const dnBtn = document.createElement('button');
    dnBtn.type = 'button'; dnBtn.className = 'ed-btn-move';
    dnBtn.textContent = '▼'; dnBtn.disabled = j === steps.length - 1;
    dnBtn.addEventListener('click', () => {
      if (j === steps.length - 1) return;
      [steps[j], steps[j+1]] = [steps[j+1], steps[j]];
      renderPhaseExec(container, phaseIdx); schedulePreview();
    });
    moveDiv.append(upBtn, dnBtn);

    const inp = document.createElement('input');
    inp.type = 'text';
    inp.value = step.text || '';
    inp.addEventListener('input', () => { steps[j].text = inp.value; schedulePreview(); });

    const rmBtn = document.createElement('button');
    rmBtn.type = 'button'; rmBtn.className = 'ed-btn-icon';
    rmBtn.textContent = '×';
    rmBtn.addEventListener('click', () => {
      steps.splice(j, 1);
      renderPhaseExec(container, phaseIdx); schedulePreview();
    });

    row.append(moveDiv, inp, rmBtn);
    wrap.appendChild(row);

    // Sub-tasks section
    const subWrap = document.createElement('div');
    subWrap.className = 'ed-subtask-wrap';

    (step.subtasks || []).forEach((sub, k) => {
      const subRow = document.createElement('div');
      subRow.className = 'ed-subtask-row';
      const subInp = document.createElement('input');
      subInp.type = 'text'; subInp.value = sub;
      subInp.placeholder = `${t('editor.phases.subtaskPlaceholder')} ${String.fromCharCode(97 + k)}`;
      subInp.addEventListener('input', () => { steps[j].subtasks[k] = subInp.value; schedulePreview(); });
      const subRm = document.createElement('button');
      subRm.type = 'button'; subRm.className = 'ed-btn-icon'; subRm.textContent = '×';
      subRm.style.minWidth = '32px'; subRm.style.minHeight = '36px';
      subRm.addEventListener('click', () => {
        steps[j].subtasks.splice(k, 1);
        renderPhaseExec(container, phaseIdx); schedulePreview();
      });
      subRow.append(subInp, subRm);
      subWrap.appendChild(subRow);
    });

    const addSubBtn = document.createElement('button');
    addSubBtn.type = 'button'; addSubBtn.className = 'ed-btn-subtask-add';
    addSubBtn.textContent = t('editor.phases.addSubtask');
    addSubBtn.addEventListener('click', () => {
      steps[j].subtasks.push('');
      renderPhaseExec(container, phaseIdx); schedulePreview();
    });
    subWrap.appendChild(addSubBtn);
    wrap.appendChild(subWrap);
    container.appendChild(wrap);
  });
}

function refreshImgZone(zone) {
  if (!zone) return;
  const path = zone.dataset.imgBind;
  const url = getByPath(state, path);
  zone.classList.toggle('has-img', !!url);
  if (url) {
    zone.innerHTML = `<input type="file" accept="image/*"><img src="${url}" alt="Image chargée"><button type="button" class="img-rm" aria-label="${t('editor.imgZone.removeImageAria')}">×</button>`;
  } else {
    zone.innerHTML = `<input type="file" accept="image/*"><span class="img-text">${t('editor.imgZone.tapShort')}</span>`;
  }
  bindImgZoneEvents(zone);
}

function bindImgZoneEvents(zone) {
  const path = zone.dataset.imgBind;
  const fileInput = zone.querySelector('input[type=file]');
  fileInput.addEventListener('change', async e => {
    const f = e.target.files[0];
    if (!f) return;
    showToast(t('toast.imageCompressing'));
    try {
      const { dataUrl } = await compressImageFile(f);
      setByPath(state, path, dataUrl);
      refreshImgZone(zone);
      schedulePreview();
      showToast(t('toast.imageLoaded'));
    } catch (err) {
      showToast(t('toast.imageError') + err.message);
    }
    e.target.value = '';
  });
  const rm = zone.querySelector('.img-rm');
  if (rm) {
    rm.addEventListener('click', e => {
      e.preventDefault();
      e.stopPropagation();
      setByPath(state, path, '');
      refreshImgZone(zone);
      schedulePreview();
    });
  }
}

/* ============= EDITOR EVENTS ============= */
function bindEditorEvents() {
  // Simple bindings
  document.querySelectorAll('[data-bind]').forEach(input => {
    input.addEventListener('input', () => {
      setByPath(state, input.dataset.bind, input.value);
      schedulePreview();
    });
  });

  // List add buttons
  document.querySelectorAll('[data-add]').forEach(btn => {
    btn.addEventListener('click', () => {
      const path = btn.dataset.add;
      getByPath(state, path).push('');
      renderList(btn.parentElement.querySelector(`[data-list="${path}"]`));
      schedulePreview();
    });
  });

  // Phase nav
  document.getElementById('phase-prev').addEventListener('click', () => {
    if (currentPhaseIdx > 0) { currentPhaseIdx--; renderPhaseEditor(); }
  });
  document.getElementById('phase-next').addEventListener('click', () => {
    if (currentPhaseIdx < state.phases.length - 1) { currentPhaseIdx++; renderPhaseEditor(); }
  });
  document.getElementById('phase-add').addEventListener('click', () => {
    state.phases.push({
      title: t('phase.newTitle'), objective: '', execution: [],
      flightPlan: '', threatLevel: 'low', notes: '', images: [],
      squadron: '', aircraft: '', subgroup: '',
      guestSquadron: { name: '', subgroup: '', aircraft: '' }
    });
    currentPhaseIdx = state.phases.length - 1;
    renderPhaseEditor(); renderRoster(); schedulePreview();
  });
  document.getElementById('phase-dup').addEventListener('click', () => {
    if (state.phases.length === 0) return;
    const cloned = JSON.parse(JSON.stringify(state.phases[currentPhaseIdx]));
    cloned.title = cloned.title + t('editor.phases.dupSuffix');
    state.phases.splice(currentPhaseIdx + 1, 0, cloned);
    currentPhaseIdx++;
    renderPhaseEditor(); renderRoster(); schedulePreview();
  });

  document.getElementById('phase-up').addEventListener('click', () => {
    if (currentPhaseIdx === 0 || state.phases.length < 2) return;
    [state.phases[currentPhaseIdx-1], state.phases[currentPhaseIdx]] =
      [state.phases[currentPhaseIdx], state.phases[currentPhaseIdx-1]];
    currentPhaseIdx--;
    renderPhaseEditor(); renderRoster(); schedulePreview();
  });

  document.getElementById('phase-down').addEventListener('click', () => {
    if (currentPhaseIdx >= state.phases.length - 1) return;
    [state.phases[currentPhaseIdx], state.phases[currentPhaseIdx+1]] =
      [state.phases[currentPhaseIdx+1], state.phases[currentPhaseIdx]];
    currentPhaseIdx++;
    renderPhaseEditor(); renderRoster(); schedulePreview();
  });
  document.getElementById('phase-rm').addEventListener('click', () => {
    if (state.phases.length === 0) return;
    if (!confirm(t('confirm.deletePhase') + ' ' + (currentPhaseIdx + 1) + ' ?')) return;
    state.phases.splice(currentPhaseIdx, 1);
    if (currentPhaseIdx >= state.phases.length) currentPhaseIdx = Math.max(0, state.phases.length - 1);
    renderPhaseEditor(); renderRoster();
    schedulePreview();
  });

  // Roster: add group (picks first available mission group)
  document.getElementById('roster-group-add').addEventListener('click', () => {
    if (!state.roster) state.roster = { groups: [] };
    const usedKeys = new Set(state.roster.groups.map(g => g.missionKey));
    const available = getMissionGroups().filter(g => !usedKeys.has(g.key));
    if (available.length === 0) return;
    // Auto-select first available
    state.roster.groups.push({ missionKey: available[0].key, pilots: [] });
    renderRoster(); schedulePreview();
  });
  document.getElementById('radio-item-add').addEventListener('click', () => {
    ensureRadioPlanShape();
    // Plafond RADIO_ITEMS_MAX supprimé — items illimités (2b)
    // Initialiser showOnOverview selon qu'il reste de la place (2b)
    const checkedCount = state.radioPlan.items.filter(it => it.showOnOverview).length;
    state.radioPlan.items.push({
      id: genId('it'),
      label: '',
      frequency: '',
      modulation: 'AM',
      showOnOverview: checkedCount < 6
    });
    renderRadioPlan();
    schedulePreview();
  });

  // Radio plan: add aircraft button
  document.getElementById('radio-aircraft-add').addEventListener('click', () => {
    ensureRadioPlanShape();
    // Plafond RADIO_AIRCRAFT_MAX supprimé — nombre d'appareils illimité (2a)
    state.radioPlan.aircraftPlans.push({
      aircraft: getAllAircraft()[0] || '',
      radios: [],
      image: ''
    });
    renderRadioAircrafts();
    schedulePreview();
  });
  document.getElementById('metar-assistant-btn').addEventListener('click', () => {
    openMetarAssistant();
  });
  document.getElementById('airfield-add').addEventListener('click', () => {
    if (!state.mission.farp) state.mission.farp = [];
    state.mission.farp.push({ icao:'', name:'', isFarp:false, rwy:'', atc:false });
    renderAirfields(); schedulePreview();
  });
  document.getElementById('chart-add').addEventListener('click', () => {
    state.charts.push({ name: '', img: '' });
    renderCharts();
    schedulePreview();
  });
  document.getElementById('annexe-add').addEventListener('click', () => {
    state.annexes.push({ title: '', img: '', caption: '' });
    renderAnnexes();
    schedulePreview();
  });
  // P1.B: wing binding moved to bindWingImportEvent() (called from init)
}

/* ============= PREVIEW ============= */
let previewTimer = null;
function schedulePreview() {
  if (previewTimer) cancelAnimationFrame(previewTimer);
  previewTimer = requestAnimationFrame(() => {
    renderPreview();
    persistState();
  });
}

/* Sous-titre des pages. Mode complet : texte historique, inchangé.
   Brief simplifié : éléments vides omis, se termine par le libellé du format. */
function pageSubtitle() {
  if (state.meta.format === 'simple') {
    const parts = [];
    if (state.meta.operation) parts.push(t('simple.hdr.operation') + ' ' + state.meta.operation);
    if (state.meta.mission) parts.push(t('simple.hdr.mission') + ' ' + state.meta.mission);
    parts.push(t('simple.subtitle'));
    return parts.map(p => escapeHtml(p)).join(' • ');
  }
  return `OPÉRATION ${escapeHtml(state.meta.operation)} • MISSION ${escapeHtml(state.meta.mission)}`;
}

function pageHeader(opts) {
  opts = opts || {};
  // Default right logo to wing logo for consistency on pages without a squadron logo
  const rightLogo = opts.rightLogo || wingConfig.wing.logo;
  const rightAlt = opts.rightAlt || wingConfig.wing.shortName;
  // FIX Bug B (complément) : <img> → <div background-image> pour les logos du header
  // car object-fit:contain est mal géré par html2canvas (issues #1322, #2425).
  // background-size:contain est correctement rendu.
  return `
    <header class="p-header">
      <div class="p-header-logo" role="img" aria-label="${escapeAttr(wingConfig.wing.shortName)}" style="background-image:url('${wingConfig.wing.logo}')"></div>
      <div class="p-title">
        <div class="p-classif">${escapeHtml(t('classif.' + state.meta.classification, state.meta.classification))}</div>
        <h1>${escapeHtml(wingConfig.wing.shortName)} ░ BRIEFING</h1>
        <div class="p-sub">${pageSubtitle()}</div>
      </div>
      <div class="p-header-logo" role="img" aria-label="${escapeAttr(rightAlt)}" style="background-image:url('${rightLogo}')"></div>
    </header>
  `;
}

function pageFooter(pageNum, totalPages) {
  return `
    <footer class="p-footer">
      <span>${escapeHtml(state.meta.docRef)}</span>
      <span class="p-classif-foot">${escapeHtml(t('classif.' + state.meta.classification, state.meta.classification))}</span>
      <span>PAGE ${pageNum.toString().padStart(2, '0')} / ${totalPages.toString().padStart(2, '0')}</span>
    </footer>
  `;
}

function imgFrame(label, url, extraClass) {
  if (url) return `<div class="p-imgframe${extraClass ? ' ' + extraClass : ''}" data-label="${escapeAttr(label)}"><img src="${url}" alt="${escapeAttr(label)}"></div>`;
  return `<div class="p-imgframe empty" data-label="${escapeAttr(label)}" data-empty-label="${escapeAttr(t('preview.noMapProvided'))}"></div>`;
}

function pageMeta() {
  const d = formatMissionDate(state.meta.date);
  // v2.3.0 : un élément vide est omis avec son séparateur (briefing vierge)
  const parts = [state.meta.docRef, d].filter(Boolean).map(p => escapeHtml(p));
  return `<div class="doc-meta">DOC${parts.length ? ' ▸ ' + parts.join(' ▸ ') : ''}</div>`;
}

function formatMissionDate(d) {
  if (!d) return '';
  try {
    const dt = new Date(d);
    if (isNaN(dt)) return d;
    const locale = CURRENT_LANG === 'fr' ? 'fr-FR' : 'en-GB';  // en-GB : DD/MM/YYYY, format OTAN-conforme
    return dt.toLocaleDateString(locale, { day: '2-digit', month: '2-digit', year: 'numeric' });
  } catch { return d; }
}

/* ============= RADIO RENDER HELPERS ============= */
function renderRadioSummary() {
  ensureRadioPlanShape();
  // Aperçu page 3 : uniquement les items showOnOverview (2b)
  const items = (state.radioPlan.items || []).filter(it => it.showOnOverview && (it.label || it.frequency));
  if (items.length === 0) {
    return '<div class="empty-placeholder">' + t('preview.noRadioItems') + '</div>';
  }
  return `<table class="radio-summary">
    ${items.map(it => `
      <tr>
        <th>${escapeHtml(it.label || '—')}</th>
        <td><span class="radio-freq">${escapeHtml(it.frequency || '—')}</span><span class="radio-mod">${escapeHtml(it.modulation || '')}</span></td>
      </tr>
    `).join('')}
  </table>`;
}

function renderRadioTable(ap) {
  ensureRadioPlanShape();
  const itemsById = {};
  state.radioPlan.items.forEach(it => { itemsById[it.id] = it; });
  const radios = (ap.radios || []).filter(r => r.name || (r.channels && r.channels.length));
  if (radios.length === 0) {
    return '<div class="empty-placeholder">' + t('preview.noRadioConfig') + '</div>';
  }
  return radios.map(r => {
    const channels = (r.channels || []).filter(ch =>
      ch.channel !== '' && ch.channel !== null && ch.channel !== undefined &&
      (ch.mode === 'custom' ? (ch.frequency || ch.label) : ch.itemId)
    );
    if (channels.length === 0) {
      return `<div class="radio-block">
        <div class="radio-block-name">${escapeHtml(r.name || '—')}</div>
        <div class="empty-placeholder" style="margin:4px 0;">Aucun canal</div>
      </div>`;
    }
    return `<div class="radio-block">
      <div class="radio-block-name">${escapeHtml(r.name || '—')}</div>
      <table class="radio-channel-table">
        ${channels.map(ch => {
          if (ch.mode === 'custom') {
            return `<tr>
              <td class="ch-num">CH ${escapeHtml(String(ch.channel ?? ''))}</td>
              <td class="ch-freq">${escapeHtml(ch.frequency || '—')}</td>
              <td class="ch-mod">${escapeHtml(ch.modulation || '')}</td>
              <td class="ch-custom-label">${escapeHtml(ch.label || '')}</td>
            </tr>`;
          }
          const it = itemsById[ch.itemId];
          if (it) {
            return `<tr>
              <td class="ch-num">CH ${escapeHtml(String(ch.channel ?? ''))}</td>
              <td class="ch-freq">${escapeHtml(it.frequency || '—')}</td>
              <td class="ch-mod">${escapeHtml(it.modulation || '')}</td>
              <td class="ch-label">${escapeHtml(it.label || '')}</td>
            </tr>`;
          }
          return `<tr>
            <td class="ch-num">CH ${escapeHtml(String(ch.channel ?? ''))}</td>
            <td class="ch-freq" colspan="3" style="font-style:italic; color:var(--khaki);">— non assigné —</td>
          </tr>`;
        }).join('')}
      </table>
    </div>`;
  }).join('');
}

/* Return a unified info object regardless of whether phase uses known or guest squadron */
function getPhaseSquadronInfo(ph) {
  if (!ph.squadron) return null;
  if (ph.squadron === '__guest__') {
    const g = ph.guestSquadron || {};
    if (!g.name && !g.aircraft) return null;
    // The guest squadron name IS the squadron identifier (replaces "INVITÉ")
    const guestName = g.name || t('preview.guestFallback');
    return {
      id: guestName,          // guest name = squadron id (e.g. "WOLF")
      callsign: guestName,    // same — no separate callsign for guests
      aircraft: g.aircraft || '?',
      subgroup: ph.subgroup || g.subgroup || '',
      logo: null,
      isGuest: true
    };
  }
  const sq = getSquadron(ph.squadron);
  if (!sq) return null;
  return {
    id: sq.id,
    callsign: sq.callsign,
    aircraft: ph.aircraft || sq.aircraft[0],
    subgroup: ph.subgroup || '',
    logo: sq.logo,
    isGuest: false
  };
}

/* ============= BRIEF SIMPLIFIÉ — PAGES (v2.3.0) =============
   Une page de mission (Situation, Mission + tableau des vols, Fréquences, Terrains, Météo),
   puis des pages de photos (deux par page) s'il y en a. Un bloc sans contenu n'est pas rendu.
   Pas de bloc Menaces dans ce mode. */
function simpleBannerText() {
  let s = t('simple.hdr.mission');
  if (state.meta.mission) s += ' ' + state.meta.mission;
  const d = formatMissionDate(state.meta.date);
  if (d) s += ' ░ ' + d;
  if (state.meta.time) s += ' ░ ' + state.meta.time;
  return s;
}

/* Une ligne par mission de l'état : [vol, appareil, tâche, départ] */
function simpleFlightRows() {
  return (state.phases || []).map(ph => {
    const info = getPhaseSquadronInfo(ph);
    const vol = info ? getRosterLabelParts(info).shortLabel : '';
    const acft = (info && info.aircraft && info.aircraft !== '?') ? info.aircraft : '';
    const n = parseInt(ph.count, 10);
    const app = (Number.isInteger(n) && n >= 1) ? (acft ? n + '× ' + acft : n + '×') : acft;
    return [vol, app, ph.title || '', ph.departure || ''];
  });
}

/* ============= v2.4.0 — menaces et cibles (partagés par les deux formats) ============= */
const THREAT_CATS = [
  ['tanks', 'preview.threatTanks'],
  ['apc',   'preview.threatApc'],
  ['aaa',   'preview.threatAaa'],
  ['sam',   'preview.threatSam']
];

/* Une cellule du bloc Menaces : le nom de la catégorie et les menaces sur la même ligne. */
function threatCellHtml(nameKey, value) {
  return `<div class="menace-cell"><strong>${t(nameKey)}</strong><span class="menace-val">${escapeHtml(value)}</span></div>`;
}

/* Les cibles qui comptent : une cible dont les quatre champs sont vides est ignorée. */
function nonEmptyTargets() {
  const list = (state.mission && Array.isArray(state.mission.targets)) ? state.mission.targets : [];
  const f = v => String(v == null ? '' : v).trim();
  return list.filter(tg => tg && (f(tg.num) || f(tg.nature) || f(tg.position) || f(tg.remark)));
}

function targetsTableHtml(list) {
  const cell = v => escapeHtml(String(v == null ? '' : v).trim() ? v : '—');
  return `<table class="p-targets">
        <thead><tr>
          <th class="c-num">${t('preview.targetNum')}</th>
          <th class="c-nat">${t('preview.targetNature')}</th>
          <th class="c-pos">${t('preview.targetPosition')}</th>
          <th>${t('preview.targetRemark')}</th>
        </tr></thead>
        <tbody>${list.map(tg => `<tr>
          <td class="tg-num">${cell(tg.num)}</td>
          <td class="tg-nature">${cell(tg.nature)}</td>
          <td class="tg-pos">${cell(tg.position)}</td>
          <td class="tg-remark">${cell(tg.remark)}</td>
        </tr>`).join('')}</tbody>
      </table>`;
}

function simplePhotoBlock(p, n) {
  const label = t('simple.photoLabel') + ' ' + n + (p.title ? ' — ' + p.title : '');
  const frame = p.img
    ? imgFrame(label, p.img)
    : `<div class="p-imgframe empty" data-label="${escapeAttr(label)}" data-empty-label="${escapeAttr(t('simple.noPhoto'))}"></div>`;
  return `<div class="p-photo">${frame}${p.caption ? `<div class="p-photo-caption">${escapeHtml(p.caption)}</div>` : ''}</div>`;
}

function buildSimplePages() {
  const pages = [];
  const points = ((state.sitac && state.sitac.points) || []).filter(Boolean);
  const objectives = ((state.mission && state.mission.objectives) || []).filter(Boolean);
  const rows = simpleFlightRows();
  const radioItems = ((state.radioPlan && state.radioPlan.items) || []).filter(it => it && (it.label || it.frequency));
  const airfields = (state.mission && Array.isArray(state.mission.farp)) ? renderAirfieldPreviewItems() : '';
  const metar = ((state.sitac && state.sitac.metar) || '').trim();
  const dash = v => escapeHtml(v || '—');
  const contLabel = () => ' ░ ' + escapeHtml(t('simple.hdr.cont'));

  // v2.4.0 — la page de mission est faite de blocs (rubrique + contenu) ; un bloc ne se coupe pas :
  // ceux qui ne tiennent plus passent sur une page « suite » (paginateBlocks).
  const blocks = [];

  if (points.length) {
    blocks.push(`<div class="p-subsection">${t('simple.situation')}</div>
      <ul class="p-bullets">${points.map(p => `<li>${escapeHtml(p)}</li>`).join('')}</ul>`);
  }

  if (objectives.length || rows.length) {
    let b = `<div class="p-subsection">${t('simple.mission')}</div>`;
    if (objectives.length) {
      b += `<ul class="p-bullets">${objectives.map(o => `<li>${escapeHtml(o)}</li>`).join('')}</ul>`;
    }
    if (rows.length) {
      b += `<table class="p-flights">
        <thead><tr>
          <th class="c-vol">${t('simple.th.flight')}</th>
          <th class="c-ac">${t('simple.th.aircraft')}</th>
          <th>${t('simple.task')}</th>
          <th class="c-dep">${t('simple.departure')}</th>
        </tr></thead>
        <tbody>${rows.map(r => `<tr>
          <td class="fl-vol">${dash(r[0])}</td>
          <td class="fl-ac">${dash(r[1])}</td>
          <td class="fl-task">${dash(r[2])}</td>
          <td class="fl-dep">${dash(r[3])}</td>
        </tr>`).join('')}</tbody>
      </table>`;
    }
    blocks.push(b);
  }

  if (radioItems.length || airfields) {
    const freqHtml = radioItems.length
      ? `<div class="p-subsection">${t('simple.freq')}</div>
         <table class="radio-summary">${radioItems.map(it => `
           <tr>
             <th>${escapeHtml(it.label || '—')}</th>
             <td><span class="radio-freq">${escapeHtml(it.frequency || '—')}</span><span class="radio-mod">${escapeHtml(it.modulation || '')}</span></td>
           </tr>`).join('')}
         </table>`
      : '';
    const fieldsHtml = airfields
      ? `<div class="p-subsection">${t('simple.airfields')}</div><ul class="p-bullets">${airfields}</ul>`
      : '';
    blocks.push(`<div class="p-2col" style="margin-top:14px;"><div>${freqHtml}</div><div>${fieldsHtml}</div></div>`);
  }

  if (metar) {
    blocks.push(`<div class="p-subsection">${t('simple.weather')}</div>
      <div class="metar-line">${escapeHtml(metar)}</div>`);
  }

  const bannerText = simpleBannerText();
  paginateBlocks(cont => `<div class="p-section">${escapeHtml(bannerText)}${cont ? contLabel() : ''}</div>`, blocks)
    .forEach(body => pages.push({ body }));

  // v2.4.0 — page « carte, menaces, cibles » : seulement si l'un des trois est présent
  const mapUrl = (state.sitac && state.sitac.mapImage) || '';
  const th = (state.mission && state.mission.threats) || {};
  const threatCells = THREAT_CATS
    .filter(([k]) => String(th[k] == null ? '' : th[k]).trim())
    .map(([k, key]) => threatCellHtml(key, th[k]));
  const threatNote = String(th.note == null ? '' : th.note).trim() ? th.note : '';
  const hasThreats = threatCells.length > 0 || !!threatNote;
  const tgList = nonEmptyTargets();
  if (mapUrl || hasThreats || tgList.length) {
    const crowded = hasThreats || tgList.length > 0;
    const tb = [];
    if (mapUrl) tb.push({ tag: 'map', html: imgFrame(t('preview.sitacImgCaption'), mapUrl, crowded ? 'p-map-cap' : 'p-map-full') });
    if (hasThreats) {
      tb.push({ tag: 'threats', html: `<div class="p-subsection">${t('simple.threats')}</div>` +
        (threatCells.length ? `<div class="menace-grid">${threatCells.join('')}</div>` : '') +
        (threatNote ? `<div class="txt-small" style="margin-top:6px;font-style:italic;">▲ ${escapeHtml(threatNote)}</div>` : '') });
    }
    if (tgList.length) {
      tb.push({ tag: 'targets', html: `<div class="p-subsection">${t('preview.targets')}</div>${targetsTableHtml(tgList)}` });
    }
    // chaque page de la série nomme ce qu'elle porte (CARTE, MENACES, CIBLES), sans « SUITE »
    paginateBlocks((cont, tags) => `<div class="p-section">${tags.map(g => escapeHtml(t('simple.hdr.' + g))).join(' ░ ')}</div>`, tb)
      .forEach(body => pages.push({ body }));
  }

  const photos = (state.photos || []).filter(p => p && (p.img || p.title || p.caption));
  for (let k = 0; k < photos.length; k += 2) {
    pages.push({
      body: `<div class="p-section">${t('simple.photosBanner')}</div>` +
        photos.slice(k, k + 2).map((p, j) => simplePhotoBlock(p, k + j + 1)).join('')
    });
  }
  return pages;
}

function buildPages() {
  const pages = [];

  // PAGE 1 — COVER
  pages.push({
    body: `
      <div class="p-section">OPÉRATION ${escapeHtml(state.meta.operation)}</div>
      ${imgFrame(t('preview.theaterMap'), state.cover.mapImage)}
      <div class="p-body" style="margin-top:14px;">
        ${(state.cover.narrative || '').split('\n').map(p => p.trim() ? `<p>${escapeHtml(p)}</p>` : '').join('')}
      </div>
      <div class="stamp-classif">${escapeHtml(t('classif.' + state.meta.classification, state.meta.classification))}</div>
      <div class="stamp-receipt">${t('preview.receivedOn')}<br>${escapeHtml(formatMissionDate(state.meta.date))}<br>${escapeHtml(wingConfig.wing.hqStamp || 'HQ ░ ' + wingConfig.wing.shortName)}</div>
    `
  });

  // PAGE 2 — SITAC
  pages.push({
    body: `
      <div class="p-section">SITAC ░ ${escapeHtml(state.sitac.date || '—')}</div>
      ${imgFrame(t('preview.sitacImgCaption'), state.sitac.mapImage)}
      <div class="p-subsection">${t('preview.sitrepPoints')}</div>
      <ul class="p-bullets">
        ${(state.sitac.points || []).filter(p=>p).map(p => `<li>${escapeHtml(p)}</li>`).join('') || '<li class="empty-placeholder">' + t('preview.noPoints') + '</li>'}
      </ul>
      <div class="p-subsection">${t('preview.metar')}</div>
      <div class="metar-line">${escapeHtml(state.sitac.metar || t('preview.metarMissing'))}</div>
    `
  });

  // PAGE 3 — MISSION OVERVIEW (with engaged squadrons incl. guests)
  const engagedMap = new Map();
  state.phases.forEach((ph, idx) => {
    const info = getPhaseSquadronInfo(ph);
    if (!info) return;
    const key = `${info.id}|${info.aircraft}|${info.subgroup}`;
    if (!engagedMap.has(key)) engagedMap.set(key, { info, phases: [] });
    engagedMap.get(key).phases.push(idx + 1);
  });
  const engagedList = Array.from(engagedMap.values());

  // v2.4.0 — la page est découpée en blocs (Objectifs · Cibles · Escadrons engagés · Terrains et plan radio · Menaces) :
  // si elle déborde, les blocs qui ne tiennent plus passent sur une page « suite » (paginateBlocks).
  // Quand rien ne déborde, la concaténation redonne exactement le corps de page historique.
  const ovTargets = nonEmptyTargets();
  const ovBlocks = [
    `
      <div class="p-subsection">${t('preview.objectives')}</div>
      <ul class="p-bullets">
        ${(state.mission.objectives || []).filter(o=>o).map(o => `<li>${escapeHtml(o)}</li>`).join('')}
      </ul>
`,
    ovTargets.length ? `
      <div class="p-subsection">${t('preview.targets')}</div>
      ${targetsTableHtml(ovTargets)}
` : '',
    `
      ${engagedList.length ? `
        <div class="p-subsection">${t('preview.squadronsEngaged')}</div>
        <div class="squadron-grid">
          ${engagedList.map(e => {
            const info = e.info;
            // FIX Bug B : remplacer <img> par <div> background-image pour contourner
            // le bug html2canvas avec object-fit:contain (issues #1322, #2425).
            // background-size:contain est correctement rendu, contrairement à object-fit.
            const logoHtml = info.logo
              ? `<div class="squadron-logo-sm" role="img" aria-label="${escapeAttr(info.id)}" style="background-image:url('${info.logo}')"></div>`
              : `<div class="squadron-logo-guest">INV.</div>`;
            // If sub-group defined → show it as the primary name (replaces callsign)
            const primaryName = info.subgroup ? info.subgroup : info.callsign;
            return `
              <div class="squadron-cell">
                ${logoHtml}
                <div class="squadron-info">
                  <strong>${escapeHtml(info.id)} ░ ${escapeHtml(primaryName)}</strong>
                  <div class="squadron-aircraft">${escapeHtml(info.aircraft)}</div>
                  <div class="squadron-phases">${e.phases.length > 1 ? t('preview.missionPlural') : t('preview.missionSingular')} ${e.phases.join(', ')}</div>
                </div>
              </div>`;
          }).join('')}
        </div>
      ` : ''}
`,
    `
      <div class="p-2col" style="margin-top:14px;">
        <div>
          <div class="p-subsection">${t('preview.farpAirports')}</div>
          <ul class="p-bullets">
            ${renderAirfieldPreviewItems()}
          </ul>
        </div>
        <div>
          <div class="p-subsection">${t('preview.radioPlan')}</div>
          ${renderRadioSummary()}
        </div>
      </div>
`,
    `
      <div class="p-subsection">${t('preview.threatsIdentified')}</div>
      <div class="menace-grid">
        ${THREAT_CATS.map(([k, key]) => threatCellHtml(key, state.mission.threats[k] || '—')).join('\n        ')}
      </div>
      ${state.mission.threats.note ? `<div class="txt-small" style="margin-top:6px;font-style:italic;">▲ ${escapeHtml(state.mission.threats.note)}</div>` : ''}
    `
  ];
  paginateBlocks(cont => `
      <div class="p-section">${t('preview.missionOverview')}${cont ? ' ░ ' + escapeHtml(t('simple.hdr.cont')) : ''}</div>
`, ovBlocks).forEach(body => pages.push({ body }));

  // PAGE ÉQUIPAGE — optionnelle, UN SEUL <table> par paire de groupes pour stabilité
  // Architecture choisie pour éviter le bug Skia/PDF où plusieurs <table> avec backgrounds
  // sur la même page créent des paint layers qui se réordonnent de façon non-déterministe.
  // Un seul <table> = un seul rendering pipeline = comportement déterministe en print.
  if (state.roster && state.roster.groups && state.roster.groups.length > 0) {
    const activeGroups = state.roster.groups.filter(g => g.pilots && g.pilots.some(p => p.name || p.callsign));
    if (activeGroups.length > 0) {
      // Render the colspan="2" cell for one group's header (name + aircraft badge)
      const renderGroupHead = g => {
        if (!g) return '<th colspan="2" class="rmt-empty"></th>';
        const parts = getRosterLabelParts(g.missionKey);
        const info = getMissionGroups().find(x => x.key === g.missionKey);
        return `<th colspan="2" class="rmt-group-head">
          <span class="rmt-group-name">${escapeHtml(parts.label)}</span>
          ${info && info.aircraft ? `<span class="rmt-group-aircraft">${escapeHtml(info.aircraft)}</span>` : ''}
        </th>`;
      };

      // Render one mega-table for a pair (or single group on left, empty right)
      // ALWAYS 4 columns to keep consistent layout regardless of group count
      const renderPair = (left, right) => {
        const lp = left.pilots.filter(p => p.name || p.callsign);
        const rp = right ? right.pilots.filter(p => p.name || p.callsign) : [];
        const rows = Math.max(lp.length, rp.length);

        const dataRows = [];
        for (let k = 0; k < rows; k++) {
          const a = lp[k];
          const b = rp[k];
          dataRows.push(`<tr>
            <td class="rmt-name">${a ? escapeHtml(a.name || '—') : ''}</td>
            <td class="rmt-callsign">${a ? escapeHtml(a.callsign || '—') : ''}</td>
            <td class="rmt-name rmt-sep">${b ? escapeHtml(b.name || '—') : ''}</td>
            <td class="rmt-callsign">${b ? escapeHtml(b.callsign || '—') : ''}</td>
          </tr>`);
        }

        return `
          <table class="roster-mega">
            <colgroup>
              <col class="rmt-col-name"><col class="rmt-col-cs">
              <col class="rmt-col-name"><col class="rmt-col-cs">
            </colgroup>
            <thead>
              <tr class="rmt-row-group">
                ${renderGroupHead(left)}
                ${renderGroupHead(right)}
              </tr>
              <tr class="rmt-row-cols">
                <th>${t('preview.rosterName')}</th><th>${t('preview.rosterCallsign')}</th>
                <th class="rmt-sep">${t('preview.rosterName')}</th><th>${t('preview.rosterCallsign')}</th>
              </tr>
            </thead>
            <tbody>
              ${dataRows.join('')}
            </tbody>
          </table>
        `;
      };

      // Build all mega-tables (one per pair)
      let body = '<div class="p-section">' + t('preview.rosterPage') + '</div>';
      body += '<div class="roster-tables">';
      for (let i = 0; i < activeGroups.length; i += 2) {
        body += renderPair(activeGroups[i], activeGroups[i + 1]);
      }
      body += '</div>';
      pages.push({ body });
    }
  }

  // PHASES — with squadron logo and sub-group chip
  state.phases.forEach((ph, i) => {
    const tcls = threatClass(ph.threatLevel);
    const info = getPhaseSquadronInfo(ph);

    const phaseRightLogo = (info && info.logo) ? info.logo : wingConfig.wing.logo;
    const phaseRightAlt = (info && info.logo) ? info.id : wingConfig.wing.shortName;

    let squadronChip = '';
    if (info) {
      // If sub-group is defined, show it instead of the callsign (cleaner, less redundant)
      const nameToShow = info.subgroup ? info.subgroup : info.callsign;
      const subHtml = info.subgroup
        ? `<span class="sq-sub">${escapeHtml(info.subgroup)}</span>` : '';
      // Only show callsign in chip when there IS a subgroup (as context) — but per request,
      // when subgroup defined → replace callsign entirely
      squadronChip = `
        <div class="squadron-chip">
          <span class="sq-id">${escapeHtml(info.id)}</span>
          <span class="sq-cs">${escapeHtml(nameToShow)}</span>
          <span class="sq-ac">${escapeHtml(info.aircraft)}</span>
        </div>`;
    }

    pages.push({
      rightLogo: phaseRightLogo,
      rightAlt: phaseRightAlt,
      body: `
        <div class="p-section">MISSION ${i + 1} ░ ${escapeHtml((ph.title || '').toUpperCase())}</div>

        ${squadronChip}

        <div class="phase-title">
          <span class="phase-num-tag">M${i + 1}</span>
          <span style="flex:1;">${escapeHtml(ph.title || '—')}</span>
          <span class="threat-chip ${tcls}">⚠ ${escapeHtml(t('threatLevel.' + (ph.threatLevel || 'low'), ph.threatLevel || '—'))}</span>
        </div>

        <div class="phase-block">
          <div class="phase-block-label">${t('preview.objective')}</div>
          <div>${escapeHtml(ph.objective || '—')}</div>
        </div>

        <div class="phase-block">
          <div class="phase-block-label">${t('preview.execution')}</div>
          ${(() => {
            const steps = normalizeExecution(ph.execution);
            const nonEmpty = steps.filter(s => s.text);
            if (!nonEmpty.length) return '<div class="empty-placeholder">' + t('preview.noSteps') + '</div>';
            return `<ol class="p-bullets-num">${nonEmpty.map(s => {
              const subs = (s.subtasks || []).filter(st => st);
              const subsHtml = subs.length
                ? `<ul class="p-subtasks">${subs.map(st => `<li>${escapeHtml(st)}</li>`).join('')}</ul>`
                : '';
              return `<li>${escapeHtml(s.text)}${subsHtml}</li>`;
            }).join('')}</ol>`;
          })()}
        </div>

        <div class="phase-block">
          <div class="phase-block-label">${t('preview.flightPlan')}</div>
          <div style="font-family:var(--f-mono); letter-spacing:1px;">${escapeHtml(ph.flightPlan || '—')}</div>
        </div>

        ${ph.notes ? `
          <div class="phase-block">
            <div class="phase-block-label">${t('preview.tacticalNotes')}</div>
            <div>${escapeHtml(ph.notes)}</div>
          </div>` : ''}
      `
    });

    // Dedicated image pages for this phase (2 per page)
    // NOTE: do NOT call normalizePhaseImages here — it replaces ph.images with a new
    // array, breaking the closures captured by event listeners in renderPhaseImages.
    // Normalization is done once on load (loadState / loadJsonFile).
    const phImgs = (ph.images || []).filter(img => img.data);
    const phRightLogo = (info && info.logo) ? info.logo : wingConfig.wing.logo;
    const phRightAlt = (info && info.logo) ? info.id : wingConfig.wing.shortName;
    const phaseLabel = `MISSION ${i + 1}`;

    for (let j = 0; j < phImgs.length; j += 2) {
      const img1 = phImgs[j];
      const img2 = phImgs[j + 1];
      const hasTwo = !!img2;
      pages.push({
        rightLogo: phRightLogo,
        rightAlt: phRightAlt,
        body: `
          <div class="p-section">${escapeHtml(phaseLabel)} ░ ${escapeHtml((ph.title || '').toUpperCase())} ░ DOCUMENTS</div>
          <div class="p-img-page-grid ${hasTwo ? 'stacked-two' : 'stacked-one'}">
            <div class="p-img-block">
              ${img1.title ? `<div class="p-img-block-title">${escapeHtml(img1.title)}</div>` : ''}
              <img src="${img1.data}" alt="${escapeAttr(img1.title || 'Image')}">
              ${img1.caption ? `<div class="p-img-block-caption">${escapeHtml(img1.caption)}</div>` : ''}
            </div>
            ${hasTwo ? `
              <div class="p-img-block">
                ${img2.title ? `<div class="p-img-block-title">${escapeHtml(img2.title)}</div>` : ''}
                <img src="${img2.data}" alt="${escapeAttr(img2.title || 'Image')}">
                ${img2.caption ? `<div class="p-img-block-caption">${escapeHtml(img2.caption)}</div>` : ''}
              </div>
            ` : ''}
          </div>
        `
      });
    }
  });

  // ANNEXES — RADIO PLAN grouped by squadron (one page per squadron)
  ensureRadioPlanShape();
  const aircraftPlans = (state.radioPlan.aircraftPlans || []).filter(ap =>
    ap.aircraft && ((ap.radios && ap.radios.length) || ap.image)
  );

  if (aircraftPlans.length > 0) {
    // Helper: find which squadron operates a given aircraft type
    function findSquadronForAircraft(aircraftName) {
      if (!aircraftName) return null;
      const name = aircraftName.toLowerCase();
      return wingConfig.squadrons.find(sq =>
        sq.aircraft.some(a => {
          const al = a.toLowerCase();
          return al.includes(name) || name.includes(al);
        })
      ) || null;
    }

    // --- Priority 1: collect guest squadrons from phases ---
    // Build a map: aircraft (lowercase) → guest info { name, aircraft }
    // Deduplicated by guest name — last one wins per name (shouldn't matter).
    const guestAircraftMap = new Map(); // aircraft.toLowerCase() → { name }
    (state.phases || []).forEach(ph => {
      if (ph.squadron === '__guest__' && ph.guestSquadron && ph.guestSquadron.aircraft) {
        const key = ph.guestSquadron.aircraft.toLowerCase();
        if (!guestAircraftMap.has(key)) {
          guestAircraftMap.set(key, { name: ph.guestSquadron.name || ph.guestSquadron.aircraft });
        }
      }
    });

    // Helper: find if an aircraft name matches a guest squadron
    function findGuestForAircraft(aircraftName) {
      if (!aircraftName || guestAircraftMap.size === 0) return null;
      const name = aircraftName.toLowerCase();
      // Exact match first, then substring (same logic as findSquadronForAircraft)
      for (const [key, guest] of guestAircraftMap) {
        if (key === name || key.includes(name) || name.includes(key)) return guest;
      }
      return null;
    }

    // Group aircraft plans by squadron (preserve order: first appearance)
    const guestGroupMap = new Map(); // guestName → { name, plans[] }
    const sqGroupMap = new Map();    // squadronId → { squadron, plans[] }
    const ungroupedPlans = [];

    aircraftPlans.forEach(ap => {
      // Priority 1 — guest squadron
      const guest = findGuestForAircraft(ap.aircraft);
      if (guest) {
        if (!guestGroupMap.has(guest.name)) guestGroupMap.set(guest.name, { name: guest.name, plans: [] });
        guestGroupMap.get(guest.name).plans.push(ap);
        return;
      }
      // Priority 2 — wing squadron
      const sq = findSquadronForAircraft(ap.aircraft);
      if (sq) {
        if (!sqGroupMap.has(sq.id)) sqGroupMap.set(sq.id, { squadron: sq, plans: [] });
        sqGroupMap.get(sq.id).plans.push(ap);
      } else {
        // Priority 3 — ungrouped
        ungroupedPlans.push(ap);
      }
    });

    // Helper: render one radio annexe page (shared by guest + wing groups)
    function renderRadioAnnexePage(titleLabel, logoSrc, logoAlt, plans) {
      const bodyContent = plans.length === 1
        ? `
          <div class="p-subsection">${escapeHtml(plans[0].aircraft)}</div>
          ${plans[0].image ? imgFrame(plans[0].aircraft + ' — RADIO', plans[0].image) : renderRadioTable(plans[0])}
        `
        : `
          <div class="p-2col">
            ${plans.map(ap => `
              <div>
                <div class="p-subsection">${escapeHtml(ap.aircraft)}</div>
                ${ap.image ? imgFrame(ap.aircraft + ' — RADIO', ap.image) : renderRadioTable(ap)}
              </div>
            `).join('')}
          </div>
        `;
      pages.push({
        rightLogo: logoSrc,
        rightAlt: logoAlt,
        body: `
          <div class="p-section">${t('preview.radioAnnexHeader')} ░ ${escapeHtml(titleLabel)}</div>
          ${bodyContent}
        `
      });
    }

    // One page per guest squadron group (Priority 1)
    guestGroupMap.forEach(({ name, plans }) => {
      // No dedicated logo for guests — fall back to wing logo (consistent with other logo-less pages)
      renderRadioAnnexePage(name, wingConfig.wing.logo, name, plans);
    });

    // One page per wing squadron group (Priority 2)
    sqGroupMap.forEach(({ squadron, plans }) => {
      renderRadioAnnexePage(squadron.id, squadron.logo, squadron.id, plans);
    });

    // Ungrouped plans (custom aircraft not matching any squadron) → one extra page
    if (ungroupedPlans.length > 0) {
      for (let i = 0; i < ungroupedPlans.length; i += 2) {
        const ap1 = ungroupedPlans[i];
        const ap2 = ungroupedPlans[i + 1];
        pages.push({
          body: `
            <div class="p-section">${t('preview.radioAnnex')}</div>
            <div class="p-2col">
              <div>
                <div class="p-subsection">${escapeHtml(ap1.aircraft || t('editor.phases.aircraftSigle'))}</div>
                ${ap1.image ? imgFrame(ap1.aircraft + ' — RADIO', ap1.image) : renderRadioTable(ap1)}
              </div>
              <div>
                ${ap2 ? `
                  <div class="p-subsection">${escapeHtml(ap2.aircraft || t('editor.phases.aircraftSigle'))}</div>
                  ${ap2.image ? imgFrame(ap2.aircraft + ' — RADIO', ap2.image) : renderRadioTable(ap2)}
                ` : ''}
              </div>
            </div>
          `
        });
      }
    }
  }

  // CHARTS — une page par chart non vide
  state.charts.forEach((chart, idx) => {
    if (chart.img || chart.name) {
      pages.push({
        body: `
          <div class="p-section">${t('preview.chartPage')} ${idx + 1}</div>
          <div class="p-subsection">${escapeHtml(chart.name || t('preview.airportFallback'))}</div>
          ${imgFrame('CHART OPS', chart.img)}
        `
      });
    }
  });

  // ANNEXES — une page par annexe non vide
  state.annexes.forEach((annexe, idx) => {
    if (annexe.img || annexe.title || annexe.caption) {
      pages.push({
        body: `
          <div class="p-section">ANNEXE ░ ${escapeHtml(annexe.title || ('DOCUMENT ' + (idx + 1)))}</div>
          ${imgFrame('ANNEXE', annexe.img)}
          ${annexe.caption ? `<div class="p-annexe-caption">${escapeHtml(annexe.caption)}</div>` : ''}
        `
      });
    }
  });

  return pages;
}

function threatClass(lvl) {
  // Opère sur les clés canoniques (low/moderate/high)
  if (lvl === 'high')     return 't-eleve';
  if (lvl === 'moderate') return 't-modere';
  return 't-faible';
}

/* ============= PAGES « SUITE » (v2.4.0) =============
   Quand le contenu d'une page de mission dépasse la hauteur utile de la page A4 figée, les blocs qui ne
   tiennent plus passent sur une page suivante (même bandeau + « ░ SUITE »), tant qu'il le faut. Un bloc ne se
   coupe pas ; un bloc plus haut qu'une page reste seul (la détection « Contenu tronqué » le signale).
   La mesure se fait AVANT l'écriture de #preview, dans un conteneur hors de #preview qui a les styles d'une page
   (.page--for-png : mêmes marges que l'export PNG et l'impression, quelle que soit la largeur de l'écran), une fois
   les polices chargées. Une page « tient » quand elle ne déclencherait pas le bandeau « Contenu tronqué ». */
/* Re-rendu de l'aperçu sans toucher au stockage (une mesure qui change n'est pas une saisie). */
let _reflowTimer = null;
function scheduleReflow() {
  if (_reflowTimer) cancelAnimationFrame(_reflowTimer);
  _reflowTimer = requestAnimationFrame(() => { _reflowTimer = null; renderPreview(); });
}

let _fontsOk = false;
let _fontsPromise = null;
function ensureFonts() {
  if (_fontsOk || _fontsPromise) return;
  if (!document.fonts || !document.fonts.ready) { _fontsOk = true; return; }
  const loads = Array.from(document.fonts).map(f => f.load().catch(() => null));
  _fontsPromise = Promise.all(loads)
    .then(() => document.fonts.ready)
    .catch(() => null)
    .then(() => { _fontsOk = true; scheduleReflow(); });   // la pagination est refaite avec les vraies polices
}

/* Dimensions naturelles des images (lues une fois) : la mesure ne dépend pas du moment où l'image est décodée. */
const _imgDims = new Map();
function noteImgDims(url) {
  if (_imgDims.has(url)) return;
  _imgDims.set(url, null);
  const im = new Image();
  im.onload = () => {
    if (im.naturalWidth > 0 && im.naturalHeight > 0) {
      _imgDims.set(url, { w: im.naturalWidth, h: im.naturalHeight });
      scheduleReflow();   // la pagination est refaite avec les vraies dimensions
    }
  };
  im.src = url;
}
/* Dans le conteneur de mesure, une image n'est jamais une image : c'est un bloc dont la taille est calculée ici,
   de façon synchrone, à partir des dimensions naturelles (_imgDims) et des limites CSS qui s'appliquent à cette
   image à cet endroit (largeur du cadre, max-width, max-height). Rien n'est chargé ni décodé : la hauteur mesurée
   est celle que prendra l'image chargée dans #preview (même règle que « width:auto; max-width; max-height »).
   Dimensions encore inconnues : l'image réelle est mesurée (provisoire) et un re-rendu suit dès qu'elles le sont. */
function withImgPlaceholders(html) {
  return html.replace(/<img src="(data:[^"]+)"[^>]*>/g, (m, url) => {
    const d = _imgDims.get(url);
    if (d === undefined) { noteImgDims(url); return m; }
    if (!d) return m;
    return `<div class="img-ph" data-w="${d.w}" data-h="${d.h}"></div>`;
  });
}
function sizeImgPlaceholders(root) {
  root.querySelectorAll('.img-ph').forEach(ph => {
    const parent = ph.parentNode;
    const probe = document.createElement('img');   // lit les limites CSS qu'aurait l'image à cet endroit
    parent.insertBefore(probe, ph);
    const cs = getComputedStyle(probe);
    const pcs = getComputedStyle(parent);
    const avail = parent.clientWidth - parseFloat(pcs.paddingLeft) - parseFloat(pcs.paddingRight);
    const lim = (v, base) => v === 'none' ? Infinity : v.endsWith('%') ? base * parseFloat(v) / 100 : parseFloat(v);
    const maxW = lim(cs.maxWidth, avail);
    const maxH = cs.maxHeight.endsWith('%') ? Infinity : lim(cs.maxHeight, 0);
    probe.remove();
    const W = parseFloat(ph.dataset.w), H = parseFloat(ph.dataset.h);
    const k = Math.min(1, maxW / W, maxH / H);
    ph.style.cssText = `display:block;margin:0 auto;width:${W * k}px;height:${H * k}px`;
  });
}

let _measureHost = null;
/* Met le corps de page dans le conteneur de mesure (hors de #preview) et rend la page mesurée. */
function layoutForMeasure(body) {
  if (!_measureHost) {
    _measureHost = document.createElement('div');
    _measureHost.id = 'page-measure';
    _measureHost.setAttribute('aria-hidden', 'true');
    _measureHost.style.cssText = 'position:fixed;left:-10000px;top:0;visibility:hidden;pointer-events:none;';
    document.body.appendChild(_measureHost);
  }
  _measureHost.innerHTML = `<article class="page page--for-png">${pageMeta()}${pageHeader({})}<div style="padding-bottom:28px;">${withImgPlaceholders(body)}</div>${pageFooter(1, 1)}</article>`;
  sizeImgPlaceholders(_measureHost);
  return _measureHost.firstElementChild;
}
function pageFits(body) {
  const pg = layoutForMeasure(body);
  const over = pg.scrollHeight - pg.clientHeight;
  _measureHost.innerHTML = '';
  return over <= OVERFLOW_THRESHOLD_PX;
}

/* headFn(cont, tags) → bandeau de la page (cont = vrai pour une page « suite » ; tags = les étiquettes des blocs
   qu'elle porte) ; blocks → blocs en HTML, ou { html, tag } ; tail → fin de page.
   Retourne les corps de page. Rien ne déborde : un seul corps, la concaténation telle quelle. */
function paginateBlocks(headFn, blocks, tail) {
  tail = tail || '';
  const items = blocks.map(b => typeof b === 'string' ? { html: b } : b);
  const make = (cont, list) => headFn(cont, list.map(i => i.tag)) + list.map(i => i.html).join('') + tail;
  const whole = make(false, items);
  if (pageFits(whole)) return [whole];
  const out = [];
  let cur = [];
  items.forEach(b => {
    if (cur.length === 0) { cur.push(b); return; }
    if (pageFits(make(out.length > 0, cur.concat([b])))) cur.push(b);
    else { out.push(make(out.length > 0, cur)); cur = [b]; }
  });
  if (cur.length) out.push(make(out.length > 0, cur));
  return out;
}

function renderPreview() {
  ensureFonts();
  const pages = (state.meta && state.meta.format === 'simple') ? buildSimplePages() : buildPages();
  const total = pages.length;
  const html = pages.map((p, i) => `
    <article class="page">
      ${pageMeta()}
      ${pageHeader({ rightLogo: p.rightLogo, rightAlt: p.rightAlt })}
      <div style="padding-bottom:28px;">${p.body}</div>
      ${pageFooter(i + 1, total)}
    </article>
  `).join('');
  document.getElementById('preview').innerHTML = html;
  applyPreviewScale();
}

/* Auto-scale preview to fit on small screens */
function applyPreviewScale() {
  const wrap = document.getElementById('preview-wrap');
  const pages = document.querySelectorAll('.page');
  if (!pages.length) return;
  if (window.innerWidth > MOBILE_BREAKPOINT) {
    pages.forEach(p => { p.style.transform = ''; p.style.marginBottom = ''; });
    return;
  }
  // mobile: scale to fit width minus padding
  const available = wrap.clientWidth - 16;
  const pageWidth = 794;
  if (available >= pageWidth) {
    pages.forEach(p => { p.style.transform = ''; p.style.marginBottom = ''; });
    return;
  }
  const scale = available / pageWidth;
  pages.forEach(p => {
    p.style.transform = `scale(${scale})`;
    p.style.transformOrigin = 'top left';
    // reserve scaled height
    const naturalH = p.offsetHeight;
    p.style.marginBottom = `${30 - (naturalH * (1 - scale))}px`;
  });
}

/* ============= UTILITY ============= */
function escapeHtml(str) {
  return String(str ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}
function escapeAttr(str) { return escapeHtml(str); }

function showToast(msg) {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.classList.add('show');
  clearTimeout(showToast._h);
  showToast._h = setTimeout(() => t.classList.remove('show'), 2200);
}

/* ============= ACTIONS ============= */
function downloadJson() {
  const blob = new Blob([JSON.stringify(state, null, 2)], { type: 'application/json' });
  const op = (state.meta.operation || 'op').toLowerCase().replace(/\s+/g, '_');
  const ms = (state.meta.mission || 'm').toLowerCase().replace(/\s+/g, '_');
  const fname = `briefing_${op}_${ms}_${Date.now()}.json`;

  // Try Web Share API first (better on Android)
  if (navigator.share && navigator.canShare) {
    try {
      const file = new File([blob], fname, { type: 'application/json' });
      if (navigator.canShare({ files: [file] })) {
        navigator.share({ files: [file], title: 'Briefing ' + wingConfig.wing.id, text: fname }).catch(() => {
          fallbackDownload(blob, fname);
        });
        return;
      }
    } catch (e) {}
  }
  fallbackDownload(blob, fname);
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
  showToast(toastMsg || t('toast.briefingSaved'));
}

function loadJsonFile(file) {
  const reader = new FileReader();
  reader.onload = async () => {
    try {
      const parsed = JSON.parse(reader.result);
      state = mergeDeep(structuredClone(DEFAULTS), parsed);
      // Migration classification : legacy texte → clé canonique (v2.2.0)
      if (state.meta && state.meta.classification) {
        const migrated = CLASSIF_LEGACY_MAP[state.meta.classification];
        if (migrated) state.meta.classification = migrated;
      }
      if (Array.isArray(state.phases)) {
        state.phases.forEach(ph => {
          ph.execution = normalizeExecution(ph.execution);
          normalizePhaseImages(ph);
          ph.threatLevel = normalizeThreatLevel(ph.threatLevel);
        });
      }
      applyLoadedFormat(parsed);
      normalizePhotos(state);
      normalizeTargets(state);
      currentPhaseIdx = 0;

      // v2.1.1 : recompresse silencieusement les images trop lourdes (briefings v2.1.0 et antérieurs)
      const recompressed = await recompressOversizedImagesInState(state);
      if (recompressed > 0) {
        persistState();  // re-sauvegarde immédiate avec les images optimisées
      }

      renderEditorBindings();
      schedulePreview();
      // 5.2 — Warn about squadron IDs referenced by this briefing but absent from current wing
      if (Array.isArray(state.phases)) {
        const knownIds = new Set((wingConfig.squadrons || []).map(sq => sq.id));
        const missingIds = [...new Set(
          state.phases
            .map(ph => ph.squadron)
            .filter(id => id && id !== '__guest__' && !knownIds.has(id))
        )];
        if (missingIds.length > 0) {
          const MAX_SHOWN = 3;
          const shown = missingIds.slice(0, MAX_SHOWN).join(', ');
          const extra = missingIds.length > MAX_SHOWN ? ` (+${missingIds.length - MAX_SHOWN} autres)` : '';
          showToast(
            `⚠ Ce briefing référence ${missingIds.length} escadron(s) absent(s) du wing courant : ${shown}${extra}. ` +
            t('toast.wingIncompatibleHint')
          );
        } else {
          showToast(t('toast.briefingLoaded'));
        }
      } else {
        showToast(t('toast.briefingLoaded'));
      }
      // Toast supplémentaire si recompression effectuée
      if (recompressed > 0) {
        setTimeout(() => {
          showToast(t('toast.briefingOptimized').replace('{n}', recompressed));
        }, 1500);
      }
    } catch (e) {
      showToast(t('toast.jsonInvalid') + e.message);
    }
  };
  reader.onerror = () => showToast(t('toast.fileUnreadable'));
  reader.readAsText(file);
}

function resetAll() {
  if (!confirm(t('confirm.resetBriefing'))) return;
  state = structuredClone(DEFAULTS);
  currentPhaseIdx = 0;
  renderEditorBindings();
  schedulePreview();
  persistState();
  showToast(t('toast.briefingReset'));
}

/* ============= WING EDITOR ============= */

/* --- Logo compression: 256×256 max, JPEG 0.85 ---
   Separate from compressImageFile (1600px/0.82) — logos need smaller footprint. */
const LOGO_MAX_SIZE = 256;

/* compressLogoFile — supprimé P1.B, édition wing déléguée à HQ */

/* updateWingSizeCounter — supprimé P1.B */

/* refreshWingLogoZone — supprimé P1.B */

/* refreshSqLogoZone — supprimé P1.B */

/* renderSqAircraftTags — supprimé P1.B */

/* renderWingSquadronCard — supprimé P1.B */
/* _saveWingOpenState + renderWingSquadrons — supprimé P1.B */
/* renderWingSquadrons (résidu) — supprimé P1.B */

/* renderWingEditor — supprimé P1.B */
/* bindWingEditorEvents — supprimé P1.B */
/* ============= WING ACTIONS ============= */

/* exportWingConfig — supprimé P1.B */

/* Read a JSON file, validate it as a wing config, and apply it.
   On error, shows a toast — never throws / alerts. */
function importWingConfig(file) {
  const reader = new FileReader();
  reader.onload = () => {
    try {
      const parsed = JSON.parse(reader.result);
      const check  = validateWingConfig(parsed);
      if (!check.ok) {
        showToast(t('toast.wingInvalid') + check.errors.slice(0, 2).join(' · ') +
          (check.errors.length > 2 ? ' (+' + (check.errors.length - 2) + ')' : ''));
        return;
      }
      wingConfig = parsed;
      persistWingConfig();
      applyWingBranding();
      renderWingReadOnly();
      schedulePreview();
      showToast(t('toast.wingLoaded'));
    } catch (e) {
      showToast(t('toast.wingJsonInvalid') + e.message);
    }
  };
  reader.onerror = () => showToast(t('toast.wingFileError'));
  reader.readAsText(file);
}

/* Hard reset to the embedded DEFAULT_WING_CONFIG, wiping localStorage entry. */
function resetWingConfig() {
  if (!confirm(t('editor.wing.resetConfirm.ro') || 'Réinitialiser le wing au défaut ?')) return;
  wingConfig = structuredClone(DEFAULT_WING_CONFIG);
  localStorage.removeItem(KEY_WING);
  applyWingBranding();
  renderWingReadOnly();
  schedulePreview();
  showToast(t('toast.wingReset'));
}


function setActiveTab(tab) {
  activeTab = tab;
  document.body.dataset.activeTab = tab;
  document.querySelectorAll('.tab-bar button').forEach(b => {
    b.classList.toggle('current', b.dataset.tab === tab);
  });
  // On mobile, force the matching <details> to be open
  if (window.innerWidth <= MOBILE_BREAKPOINT) {
    document.querySelectorAll('.ed-section').forEach(s => {
      if (s.dataset.section === tab) {
        s.setAttribute('open', '');
      }
    });
  }
  // Reset scroll on tab change
  if (tab === 'preview') {
    document.getElementById('preview-wrap').scrollTop = 0;
    applyPreviewScale();
  } else {
    document.getElementById('editor').scrollTop = 0;
  }
}

function bindTabBar() {
  document.querySelectorAll('.tab-bar button').forEach(b => {
    b.addEventListener('click', () => setActiveTab(b.dataset.tab));
  });
}

/* ============= WING READ-ONLY PANEL (P1.B) ============= */
/* Renders current wingConfig as read-only info in #wing-ro-info.
   Called on init, after import, after reset, and on storage event. */
function renderWingReadOnly() {
  const el = document.getElementById('wing-ro-info');
  if (!el) return;
  const w = wingConfig.wing;
  const sqCount = Array.isArray(wingConfig.squadrons) ? wingConfig.squadrons.length : 0;
  const logoHtml = (w.logo && w.logo.startsWith('data:image/'))
    ? '<img src="' + escapeAttr(w.logo) + '" alt="Logo" class="wing-ro-logo">'
    : '';
  el.innerHTML =
    '<div class="wing-ro-row">' + logoHtml +
    '<div class="wing-ro-text">' +
      '<div class="wing-ro-name">' + escapeHtml(w.shortName || '') + '</div>' +
      '<div class="wing-ro-full">' + escapeHtml(w.fullName || '') + '</div>' +
      '<div class="wing-ro-meta">' + escapeHtml(w.id || '') +
        (sqCount ? ' · ' + sqCount + ' ' + t('editor.wing.roSquadrons') : '') +
      '</div>' +
    '</div></div>';
}

/* Bind the standalone wing import input (P1.B filet standalone). Called once from init(). */
function bindWingImportEvent() {
  const inp = document.getElementById('wing-import-input');
  if (inp) {
    inp.addEventListener('change', e => {
      if (e.target.files[0]) importWingConfig(e.target.files[0]);
      e.target.value = '';
    });
  }
  const btnReset = document.getElementById('wing-reset-btn');
  if (btnReset) btnReset.addEventListener('click', resetWingConfig);
  /* Storage listener: refresh wing when HQ writes wing_config_v1 (sous shell). */
  window.addEventListener('storage', function(e) {
    if (e.key === 'wing_config_v1') {
      wingConfig = loadWingConfig();
      applyWingBranding();
      renderWingReadOnly();
    }
  });
}

/* ============= WING BRANDING ============= */
/* Apply wing identity to all dynamic HTML entry-points.
   Must be called:
     - once in init() after loadWingConfig()
     - again after any change to wingConfig (importWingConfig, resetWingConfig, wing editor)
   XSS safety: all values from wingConfig pass through escapeHtml / escapeAttr.
   The static HTML contains 'MY WING' placeholders; this function overwrites
   them at DOMContentLoaded so they never appear if wingConfig is loaded. */
function applyWingBranding() {
  const w = wingConfig.wing;
  // <title> — délégué à updateDocTitle() pour intégrer l'i18n (Phase 9)
  updateDocTitle();
  // Toolbar brand
  const brandEl = document.querySelector('.tb-brand-main');
  if (brandEl) brandEl.textContent = w.shortName;
  // Lateral help block (◆ MY WING ◆)
  const helpEl = document.querySelector('.ed-help[data-wing-label]');
  if (helpEl) helpEl.firstChild.textContent = '◆ ' + w.shortName + ' ◆';
}

/* ============= THEME (Phase X — étape E) ============= */
/* Le thème graphique est une préférence utilisateur indépendante du wing
   et du briefing. Stocké en localStorage[KEY_THEME] sous forme d'identifiant
   string. 4 valeurs valides : 'cw-nato' (défaut), 'cw-soviet', 'modern-nato',
   'modern-east'. Toute valeur inconnue ou absente → fallback 'cw-nato'. */
const THEME_IDS = ['cw-nato', 'cw-soviet', 'modern-nato', 'modern-east'];

function loadTheme() {
  try {
    const raw = localStorage.getItem(KEY_THEME);
    if (raw && THEME_IDS.indexOf(raw) !== -1) return raw;
  } catch(e) { /* localStorage may be unavailable */ }
  return 'cw-nato';
}

function applyTheme(themeId) {
  if (THEME_IDS.indexOf(themeId) === -1) themeId = 'cw-nato';
  document.body.dataset.theme = themeId;
  try { localStorage.setItem(KEY_THEME, themeId); }
  catch(e) { /* ignore */ }
  const sel = document.getElementById('theme-select');
  if (sel) sel.value = themeId;
}

/* ============= OVERFLOW DETECTION (chatE étape A) =============
   Détecte les pages dont le contenu déborde de la hauteur A4 figée (1123px).
   Un bandeau rouge "⚠ Contenu tronqué" est injecté en aperçu uniquement.
   Il disparaît dynamiquement si l'utilisateur supprime du contenu.
   Le MutationObserver surveille #preview — aucun re-check disséminé ailleurs.
   ================================================================ */
/* Seuil de dépassement toléré (px). Doit rester < 28, le padding-bottom du corps de page (renderPreview) :
   scrollHeight − clientHeight compte ce padding, donc tant que le dépassement reste sous 28 px le contenu ne touche pas le pied.
   Partagé par pageFits (pagination) et par le bandeau « Contenu tronqué ». */
const OVERFLOW_THRESHOLD_PX = 16;
let overflowObserver = null;

function detectPageOverflows() {
  const pages = document.querySelectorAll('#preview .page');
  pages.forEach(function(page) {
    let warn = page.querySelector('.p-overflow-warning');
    // scrollHeight mesure le contenu réel même avec overflow:hidden — c'est volontaire
    const overflowsBy = page.scrollHeight - page.clientHeight;
    if (overflowsBy > OVERFLOW_THRESHOLD_PX) {
      if (!warn) {
        warn = document.createElement('div');
        warn.className = 'p-overflow-warning';
        warn.textContent = '⚠ Contenu tronqué';
        page.appendChild(warn);
      }
    } else {
      if (warn) warn.remove();
    }
  });
}

function initOverflowObserver() {
  const previewEl = document.getElementById('preview');
  if (!previewEl) return;
  if (overflowObserver) overflowObserver.disconnect();
  overflowObserver = new MutationObserver(function() {
    // Debounce 50ms pour éviter le spam sur les mutations en cascade
    clearTimeout(overflowObserver._timer);
    overflowObserver._timer = setTimeout(detectPageOverflows, 50);
  });
  overflowObserver.observe(previewEl, {
    childList: true,
    subtree: true,
    characterData: true,
    attributes: true,
  });
  // Une image qui finit de charger change la hauteur du contenu sans muter le DOM : on re-vérifie
  previewEl.addEventListener('load', function(e) {
    if (!e.target || e.target.tagName !== 'IMG') return;
    clearTimeout(overflowObserver._timer);
    overflowObserver._timer = setTimeout(detectPageOverflows, 50);
  }, true);
  // Première passe immédiate à l'initialisation
  detectPageOverflows();
}

/* ============= BRIEF COMPLET / SIMPLIFIÉ — ÉDITEUR (v2.3.0) ============= */
/* Le mode vit dans l'état (meta.format) ; <body data-format> pilote l'affichage (CSS data-fmt). */
const _metarHome = { parent: null, next: null };

/* Le panneau de l'assistant METAR n'existe qu'une fois (ids fixes) : il est déplacé dans la
   section Coordination en mode simplifié, et remis à sa place d'origine en mode complet. */
function placeMetarPanel(fmt) {
  const panel = document.getElementById('metar-assistant-panel');
  const slot = document.getElementById('s-metar-slot');
  if (!panel || !slot) return;
  if (!_metarHome.parent) { _metarHome.parent = panel.parentNode; _metarHome.next = panel.nextSibling; }
  if (fmt === 'simple') {
    if (panel.parentNode !== slot) slot.appendChild(panel);
  } else if (panel.parentNode !== _metarHome.parent) {
    _metarHome.parent.insertBefore(panel, _metarHome.next);
  }
}

function applyFormatUi() {
  const fmt = (state && state.meta && state.meta.format === 'simple') ? 'simple' : 'full';
  document.body.dataset.format = fmt;
  document.querySelectorAll('#format-seg .seg-btn').forEach(b => {
    const on = b.dataset.format === fmt;
    b.classList.toggle('active', on);
    b.setAttribute('aria-pressed', on ? 'true' : 'false');
  });
  placeMetarPanel(fmt);
  // l'onglet courant doit exister dans ce mode
  const tabBtn = document.querySelector('.tab-bar button[data-tab="' + activeTab + '"]');
  const shared = activeTab === 'meta' || activeTab === 'preview';
  if (!shared && !(tabBtn && tabBtn.dataset.fmt === fmt)) setActiveTab('meta');
}

function renderSimpleEditor() {
  applyFormatUi();
  renderSimpleFlights();
  renderSimpleRadioItems();
  renderPhotosEditor();
}

function setFormat(fmt) {
  if (fmt !== 'full' && fmt !== 'simple') return;
  if (state.meta.format === fmt) return;
  state.meta.format = fmt;   // seul changement d'état : aucune donnée n'est perdue ni modifiée
  applyFormatUi();
  // rafraîchit l'éditeur du mode qui devient visible (les données ont pu changer dans l'autre)
  document.querySelectorAll('[data-bind]').forEach(input => {
    const v = getByPath(state, input.dataset.bind);
    if (v != null) input.value = v;
  });
  document.querySelectorAll('[data-list]').forEach(renderList);
  document.querySelectorAll('[data-img-bind]').forEach(refreshImgZone);   // v2.4.0 : la carte est partagée
  renderTargets();                                                       // v2.4.0 : les cibles aussi
  renderAirfields();
  if (fmt === 'simple') {
    renderSimpleFlights();
    renderSimpleRadioItems();
    renderPhotosEditor();
  } else {
    renderPhaseEditor();
    renderRadioPlan();
    renderRoster();
  }
  schedulePreview();
}

function loadExample() {
  if (!confirm(t('confirm.loadExample'))) return;
  state = mergeDeep(structuredClone(DEFAULTS), structuredClone(EXAMPLE_BRIEFING));
  state.meta.format = 'full';
  currentPhaseIdx = 0;
  renderEditorBindings();
  schedulePreview();
  persistState();
  showToast(t('toast.exampleLoaded'));
}

function newBlankFlight() {
  return {
    title: '', objective: '', execution: [],
    flightPlan: '', threatLevel: 'low', notes: '', images: [],
    squadron: '', aircraft: '', subgroup: '',
    guestSquadron: { name: '', subgroup: '', aircraft: '' },
    count: '', departure: ''
  };
}

/* Vols = missions de l'état (state.phases) ; les champs propres au mode complet sont conservés. */
function renderSimpleFlights() {
  const list = document.getElementById('s-flights-list');
  if (!list) return;
  list.innerHTML = '';
  const phases = Array.isArray(state.phases) ? state.phases : [];
  if (phases.length === 0) {
    const empty = document.createElement('div');
    empty.className = 'phase-empty';
    empty.textContent = t('editor.simple.noFlights');
    list.appendChild(empty);
    return;
  }

  const sqOptions = [`<option value="">${t('select.noSquadron')}</option>`]
    .concat(wingConfig.squadrons.map(s => {
      const aircraftLabel = s.aircraft.length === 1 ? s.aircraft[0] : s.aircraft.join(' / ');
      return `<option value="${escapeAttr(s.id)}">${escapeHtml(s.id)} ${escapeHtml(s.callsign)} — ${escapeHtml(aircraftLabel)}</option>`;
    }))
    .concat([`<option value="__guest__">${t('editor.phases.guestOption')}</option>`])
    .join('');

  phases.forEach((ph, i) => {
    const isGuest = ph.squadron === '__guest__';
    const selectedSq = isGuest ? null : getSquadron(ph.squadron);
    const showAircraft = !isGuest && selectedSq && selectedSq.aircraft.length > 1;
    const g = ph.guestSquadron || { name: '', subgroup: '', aircraft: '' };
    const n = parseInt(ph.count, 10);

    const aircraftHtml = showAircraft ? `
      <div class="ed-field"><label>${t('editor.phases.aircraft')}</label>
        <select class="fl-aircraft">${selectedSq.aircraft.map(a => `<option value="${escapeAttr(a)}">${escapeHtml(a)}</option>`).join('')}</select>
      </div>` : '';
    const guestHtml = isGuest ? `
      <div class="ed-guest-fields">
        <div class="ed-field"><label>${t('editor.phases.guestName')}</label>
          <input class="fl-g-name" type="text" value="${escapeAttr(g.name)}" placeholder="${escapeAttr(t('placeholder.guestName'))}"></div>
        <div class="ed-field"><label>${t('editor.phases.guestSub')}</label>
          <input class="fl-g-sub" type="text" value="${escapeAttr(g.subgroup)}" placeholder="${escapeAttr(t('placeholder.guestName'))} 1 ${escapeAttr(t('placeholder.optional'))}"></div>
        <div class="ed-field"><label>${t('editor.phases.guestAircraft')}</label>
          <input class="fl-g-ac" type="text" value="${escapeAttr(g.aircraft)}" placeholder="${escapeAttr(t('placeholder.guestAircraft'))}"></div>
      </div>` : '';

    const card = document.createElement('div');
    card.className = 'ed-img-card';
    card.innerHTML = `
      <div class="ed-img-card-num">${t('editor.simple.flightNum')} ${i + 1}</div>
      <div class="ed-card-bar">
        <button type="button" class="ed-btn-icon neutral" data-fl="up" title="${escapeAttr(t('editor.simple.up'))}" aria-label="${escapeAttr(t('editor.simple.up'))}" ${i === 0 ? 'disabled' : ''}>↑</button>
        <button type="button" class="ed-btn-icon neutral" data-fl="down" title="${escapeAttr(t('editor.simple.down'))}" aria-label="${escapeAttr(t('editor.simple.down'))}" ${i === phases.length - 1 ? 'disabled' : ''}>↓</button>
        <button type="button" class="ed-btn-icon" data-fl="rm" title="${escapeAttr(t('editor.imgCard.remove'))}" aria-label="${escapeAttr(t('editor.imgCard.remove'))}">×</button>
      </div>
      <div class="ed-field"><label>${t('simple.task')}</label>
        <input class="fl-title" type="text" value="${escapeAttr(ph.title || '')}"></div>
      <div class="ed-field"><label>${t('editor.phases.squadron')}</label>
        <select class="fl-squadron">${sqOptions}</select></div>
      ${guestHtml}
      ${aircraftHtml}
      <div class="ed-field"><label>${t('editor.phases.subgroup')} <span class="ed-label-hint">${t('editor.phases.subgroupHint')}</span></label>
        <input class="fl-subgroup" type="text" value="${escapeAttr(ph.subgroup || '')}" placeholder="${escapeAttr(t('placeholder.subgroup'))}"></div>
      <div class="ed-field-row">
        <div class="ed-field"><label>${t('editor.simple.count')}</label>
          <input class="fl-count" type="number" min="1" step="1" value="${(Number.isInteger(n) && n >= 1) ? n : ''}"></div>
        <div class="ed-field"><label>${t('simple.departure')}</label>
          <input class="fl-departure" type="text" value="${escapeAttr(ph.departure || '')}"></div>
      </div>
    `;
    list.appendChild(card);

    card.querySelector('.fl-squadron').value = ph.squadron || '';
    const acSel = card.querySelector('.fl-aircraft');
    if (acSel) acSel.value = ph.aircraft || selectedSq.aircraft[0];

    const bindText = (sel, fn) => {
      const el = card.querySelector(sel);
      if (el) el.addEventListener('input', () => { fn(el.value); schedulePreview(); });
    };
    bindText('.fl-title', v => { state.phases[i].title = v; });
    bindText('.fl-subgroup', v => { state.phases[i].subgroup = v; });
    bindText('.fl-departure', v => { state.phases[i].departure = v; });
    const guest = () => state.phases[i].guestSquadron ||
      (state.phases[i].guestSquadron = { name: '', subgroup: '', aircraft: '' });
    bindText('.fl-g-name', v => { guest().name = v; });
    bindText('.fl-g-sub', v => { guest().subgroup = v; });
    bindText('.fl-g-ac', v => { guest().aircraft = v; });

    const countEl = card.querySelector('.fl-count');
    countEl.addEventListener('input', () => {
      const c = parseInt(countEl.value, 10);
      state.phases[i].count = (Number.isInteger(c) && c >= 1) ? c : '';
      schedulePreview();
    });
    countEl.addEventListener('change', () => { countEl.value = state.phases[i].count === '' ? '' : state.phases[i].count; });

    card.querySelector('.fl-squadron').addEventListener('change', e => {
      const p = state.phases[i];
      const newSqId = e.target.value;
      p.squadron = newSqId;
      if (newSqId === '__guest__') {
        if (!p.guestSquadron) p.guestSquadron = { name: '', subgroup: '', aircraft: '' };
        p.aircraft = '';
      } else {
        const newSq = getSquadron(newSqId);
        if (!newSq) p.aircraft = '';
        else if (newSq.aircraft.length === 1) p.aircraft = newSq.aircraft[0];
        else if (!newSq.aircraft.includes(p.aircraft)) p.aircraft = newSq.aircraft[0];
      }
      renderSimpleFlights(); schedulePreview();
    });
    if (acSel) acSel.addEventListener('change', e => { state.phases[i].aircraft = e.target.value; schedulePreview(); });

    card.querySelector('[data-fl="up"]').addEventListener('click', () => {
      if (i === 0) return;
      [state.phases[i - 1], state.phases[i]] = [state.phases[i], state.phases[i - 1]];
      renderSimpleFlights(); schedulePreview();
    });
    card.querySelector('[data-fl="down"]').addEventListener('click', () => {
      if (i >= state.phases.length - 1) return;
      [state.phases[i + 1], state.phases[i]] = [state.phases[i], state.phases[i + 1]];
      renderSimpleFlights(); schedulePreview();
    });
    card.querySelector('[data-fl="rm"]').addEventListener('click', () => {
      if (!confirm(t('confirm.deletePhase') + ' ' + (i + 1) + ' ?')) return;
      state.phases.splice(i, 1);
      renderSimpleFlights(); schedulePreview();
    });
  });
}

/* Fréquences globales (radioPlan.items), sans la case « afficher à l'aperçu ». */
function renderSimpleRadioItems() {
  const list = document.getElementById('s-radio-items-list');
  if (!list) return;
  list.innerHTML = '';
  ensureRadioPlanShape();
  const items = state.radioPlan.items;
  items.forEach((it, i) => {
    const row = document.createElement('div');
    row.className = 'ed-radio-item-row s-row';
    row.innerHTML = `
      <input type="text" data-ri-label placeholder="${escapeAttr(t('editor.radio.labelEx'))}">
      <input type="text" data-ri-freq placeholder="${escapeAttr(t('editor.radio.freqLabel'))}">
      <select data-ri-mod>
        <option value="AM">AM</option>
        <option value="FM">FM</option>
      </select>
      <button type="button" class="ed-btn-icon" data-ri-rm aria-label="${escapeAttr(t('editor.imgCard.remove'))}">×</button>
    `;
    row.querySelector('[data-ri-label]').value = it.label || '';
    row.querySelector('[data-ri-freq]').value = it.frequency || '';
    row.querySelector('[data-ri-mod]').value = it.modulation || 'AM';
    row.querySelector('[data-ri-label]').addEventListener('input', e => { items[i].label = e.target.value; schedulePreview(); });
    row.querySelector('[data-ri-freq]').addEventListener('input', e => { items[i].frequency = e.target.value; schedulePreview(); });
    row.querySelector('[data-ri-mod]').addEventListener('change', e => { items[i].modulation = e.target.value; schedulePreview(); });
    row.querySelector('[data-ri-rm]').addEventListener('click', () => {
      const removedId = items[i].id;
      items.splice(i, 1);
      // même nettoyage que l'éditeur du mode complet : plus de référence vers l'item supprimé
      state.radioPlan.aircraftPlans.forEach(ap => {
        (ap.radios || []).forEach(r => {
          (r.channels || []).forEach(ch => { if (ch.itemId === removedId) ch.itemId = ''; });
        });
      });
      renderSimpleRadioItems(); schedulePreview();
    });
    list.appendChild(row);
  });
  if (items.length === 0) {
    const empty = document.createElement('div');
    empty.className = 'phase-empty';
    empty.textContent = t('editor.radio.addItem');
    list.appendChild(empty);
  }
}

/* Photos du brief simplifié : state.photos = [{ title, img, caption }] */
function renderPhotosEditor() {
  const listEl = document.getElementById('s-photos-list');
  if (!listEl) return;
  listEl.innerHTML = '';
  const photos = Array.isArray(state.photos) ? state.photos : [];
  if (photos.length === 0) {
    const empty = document.createElement('div');
    empty.className = 'phase-empty';
    empty.textContent = t('editor.simple.noPhotos');
    listEl.appendChild(empty);
    return;
  }

  photos.forEach((ph, k) => {
    const card = document.createElement('div');
    card.className = 'ed-img-card';
    card.innerHTML = `
      <div class="ed-img-card-num">${t('editor.simple.photoNum')} ${k + 1}</div>
      <div class="ed-card-bar">
        <button type="button" class="ed-btn-icon neutral" data-ph="up" title="${escapeAttr(t('editor.simple.up'))}" aria-label="${escapeAttr(t('editor.simple.up'))}" ${k === 0 ? 'disabled' : ''}>↑</button>
        <button type="button" class="ed-btn-icon neutral" data-ph="down" title="${escapeAttr(t('editor.simple.down'))}" aria-label="${escapeAttr(t('editor.simple.down'))}" ${k === photos.length - 1 ? 'disabled' : ''}>↓</button>
        <button type="button" class="ed-btn-icon" data-ph="rm" title="${escapeAttr(t('editor.imgCard.remove'))}" aria-label="${escapeAttr(t('editor.imgCard.remove'))}">×</button>
      </div>
      <div class="ed-field"><label>${t('editor.annexes.titleLabel')}</label>
        <input type="text" class="ph-title" value="${escapeAttr(ph.title)}"></div>
      <div class="ed-field">
        <label>${t('editor.image.label')}</label>
        <label class="ed-img-zone ${ph.img ? 'has-img' : ''}" data-photo-zone="${k}">
          <input type="file" accept="image/*">
          ${ph.img
            ? `<img src="${ph.img}" alt="Photo ${k + 1}">`
            : `<span class="img-text">${t('editor.imgZone.tapShort')}</span>`}
          ${ph.img ? `<button type="button" class="img-rm">×</button>` : ''}
        </label>
      </div>
      <div class="ed-field"><label>${t('editor.annexes.captionLabel')}</label>
        <textarea class="ph-caption" rows="2">${escapeHtml(ph.caption)}</textarea></div>
    `;
    listEl.appendChild(card);

    card.querySelector('.ph-title').addEventListener('input', e => { state.photos[k].title = e.target.value; schedulePreview(); });
    card.querySelector('.ph-caption').addEventListener('input', e => { state.photos[k].caption = e.target.value; schedulePreview(); });

    card.querySelector('[data-ph="up"]').addEventListener('click', () => {
      if (k === 0) return;
      [state.photos[k - 1], state.photos[k]] = [state.photos[k], state.photos[k - 1]];
      renderPhotosEditor(); schedulePreview();
    });
    card.querySelector('[data-ph="down"]').addEventListener('click', () => {
      if (k >= state.photos.length - 1) return;
      [state.photos[k + 1], state.photos[k]] = [state.photos[k], state.photos[k + 1]];
      renderPhotosEditor(); schedulePreview();
    });
    card.querySelector('[data-ph="rm"]').addEventListener('click', () => {
      state.photos.splice(k, 1);
      renderPhotosEditor(); schedulePreview();
    });

    const zone = card.querySelector('[data-photo-zone]');
    zone.querySelector('input[type="file"]').addEventListener('change', async e => {
      const f = e.target.files[0];
      if (!f) return;
      showToast(t('toast.imageCompressing'));
      try {
        const { dataUrl } = await compressImageFile(f);
        state.photos[k].img = dataUrl;
        renderPhotosEditor();
        schedulePreview();
        showToast(t('toast.imageLoaded'));
      } catch (err) {
        showToast(t('toast.imageError') + err.message);
      }
      e.target.value = '';
    });
    const rmImg = zone.querySelector('.img-rm');
    if (rmImg) {
      rmImg.addEventListener('click', e => {
        e.preventDefault();
        e.stopPropagation();
        state.photos[k].img = '';
        renderPhotosEditor();
        schedulePreview();
      });
    }
  });
}

/* v2.4.0 — Cibles : state.mission.targets = [{ num, nature, position, remark }].
   Un composant, deux conteneurs (#s-targets-list du brief simplifié, #targets-list du brief complet) :
   chacun rejoue le même rendu, et la liste est la même dans les deux formats. */
const TARGET_FIELDS = [
  ['num', 'editor.targets.num'],
  ['nature', 'editor.targets.nature'],
  ['position', 'editor.targets.position'],
  ['remark', 'editor.targets.remark']
];

function renderTargets() {
  const containers = ['s-targets-list', 'targets-list']
    .map(id => document.getElementById(id)).filter(Boolean);
  if (!containers.length) return;
  if (!state.mission) state.mission = {};
  if (!Array.isArray(state.mission.targets)) state.mission.targets = [];
  const targets = state.mission.targets;
  containers.forEach(list => {
    list.innerHTML = '';
    if (targets.length === 0) {
      const empty = document.createElement('div');
      empty.className = 'phase-empty';
      empty.textContent = t('editor.targets.empty');
      list.appendChild(empty);
      return;
    }
    targets.forEach((tg, i) => {
      const row = document.createElement('div');
      row.className = 'ed-target-row';
      row.innerHTML = TARGET_FIELDS.map(([k, key]) =>
        `<input type="text" data-tg="${k}" placeholder="${escapeAttr(t(key))}" aria-label="${escapeAttr(t(key))}">`
      ).join('') +
        `<button type="button" class="ed-btn-icon" data-tg-rm aria-label="${escapeAttr(t('editor.imgCard.remove'))}">×</button>`;
      TARGET_FIELDS.forEach(([k]) => {
        const inp = row.querySelector(`[data-tg="${k}"]`);
        inp.value = tg[k] || '';
        inp.addEventListener('input', () => { targets[i][k] = inp.value; schedulePreview(); });
      });
      row.querySelector('[data-tg-rm]').addEventListener('click', () => {
        targets.splice(i, 1);
        renderTargets(); schedulePreview();
      });
      list.appendChild(row);
    });
  });
}

function addTarget() {
  if (!state.mission) state.mission = {};
  if (!Array.isArray(state.mission.targets)) state.mission.targets = [];
  state.mission.targets.push({
    num: 'T' + (state.mission.targets.length + 1),
    nature: '', position: '', remark: ''
  });
  renderTargets(); schedulePreview();
}

function bindSimpleEvents() {
  document.querySelectorAll('#format-seg .seg-btn').forEach(b => {
    b.addEventListener('click', () => setFormat(b.dataset.format));
  });
  document.getElementById('btn-example').addEventListener('click', loadExample);
  document.getElementById('s-flight-add').addEventListener('click', () => {
    if (!Array.isArray(state.phases)) state.phases = [];
    state.phases.push(newBlankFlight());
    renderSimpleFlights(); schedulePreview();
  });
  document.getElementById('s-photo-add').addEventListener('click', () => {
    if (!Array.isArray(state.photos)) state.photos = [];
    state.photos.push({ title: '', img: '', caption: '' });
    renderPhotosEditor(); schedulePreview();
  });
  document.getElementById('s-radio-item-add').addEventListener('click', () => {
    ensureRadioPlanShape();
    const checkedCount = state.radioPlan.items.filter(it => it.showOnOverview).length;
    state.radioPlan.items.push({
      id: genId('it'), label: '', frequency: '', modulation: 'AM',
      showOnOverview: checkedCount < 6
    });
    renderSimpleRadioItems(); schedulePreview();
  });
  document.getElementById('s-airfield-add').addEventListener('click', () => {
    if (!state.mission.farp) state.mission.farp = [];
    state.mission.farp.push({ icao: '', name: '', isFarp: false, rwy: '', atc: false });
    renderAirfields(); schedulePreview();
  });
  document.getElementById('s-metar-assistant-btn').addEventListener('click', () => { openMetarAssistant(); });
  document.getElementById('s-target-add').addEventListener('click', addTarget);
  document.getElementById('target-add').addEventListener('click', addTarget);
}

/* ============= INIT ============= */
function revealInToolbar(bar, el) {
  if (!bar || !el || bar.scrollWidth <= bar.clientWidth) return;
  const b = bar.getBoundingClientRect();
  const r = el.getBoundingClientRect();
  if (r.left < b.left) bar.scrollLeft += r.left - b.left - 8;
  else if (r.right > b.right) bar.scrollLeft += r.right - b.right + 8;
}

function initToolbarScroll() {
  const bar = document.querySelector('.toolbar');
  if (!bar) return;
  const update = () => {
    const max = bar.scrollWidth - bar.clientWidth;
    bar.classList.toggle('fade-l', bar.scrollLeft > 1);
    bar.classList.toggle('fade-r', bar.scrollLeft < max - 1);
  };
  const child = t => { while (t && t.parentNode !== bar) t = t.parentNode; return t; };
  bar.addEventListener('scroll', update, { passive: true });
  // Un appui sur un contrôle partiellement visible le ramène entier dans la vue, puis l'active
  bar.addEventListener('click', e => revealInToolbar(bar, child(e.target)), true);
  bar.addEventListener('focusin', e => revealInToolbar(bar, child(e.target)));
  // Molette verticale → défilement horizontal
  bar.addEventListener('wheel', e => {
    if (bar.scrollWidth <= bar.clientWidth) return;
    if (Math.abs(e.deltaY) > Math.abs(e.deltaX)) { bar.scrollLeft += e.deltaY; e.preventDefault(); }
  }, { passive: false });
  window.addEventListener('resize', update);
  if (window.ResizeObserver) new ResizeObserver(update).observe(bar);
  // Le shell ajoute son bouton de retour et son tampon après le chargement
  new MutationObserver(update).observe(bar, { childList: true, subtree: true, characterData: true });
  update();
}

function init() {
  initLang();                          // Phase 9 — lire la langue avant tout
  applyTheme(loadTheme());             // poser le thème AVANT le branding (cf. brief E)
  wingConfig = loadWingConfig();
  loadState();
  applyWingBranding();
  renderWingReadOnly();  // P1.B — panneau wing read-only
  applyI18nStatic();                   // Phase 9 — peupler les data-i18n (Étape B)
  updateFlagButton();                  // Phase 9 — afficher le bon drapeau
  renderEditorBindings();
  bindEditorEvents();
  bindSimpleEvents();    // v2.3.0 : sélecteur de mode, Exemple, éditeur simplifié
  bindTabBar();
  initToolbarScroll();
  bindWingImportEvent();  // P1.B — filet import + storage listener
  setActiveTab('meta');
  renderPreview();
  initOverflowObserver();  // chatE étape A : détection débordement via MutationObserver

  // v2.1.1 : recompresse silencieusement les images héritées (briefings localStorage v2.1.0 et antérieurs)
  recompressOversizedImagesInState(state).then(recompressed => {
    if (recompressed > 0) {
      persistState();
      schedulePreview();
      showToast(t('toast.briefingOptimizedOnLoad').replace('{n}', recompressed));
    }
  });
  document.getElementById('btn-save').addEventListener('click', downloadJson);
  document.getElementById('btn-load').addEventListener('click', () => document.getElementById('file-load').click());
  document.getElementById('file-load').addEventListener('change', e => {
    if (e.target.files[0]) loadJsonFile(e.target.files[0]);
    e.target.value = '';
  });
  document.getElementById('btn-print').addEventListener('click', openExportModal);
  document.getElementById('btn-reset').addEventListener('click', resetAll);
  document.getElementById('theme-select').addEventListener('change', e => { applyTheme(e.target.value); scheduleReflow(); });   // v2.4.0 : la pagination suit les polices du thème
  document.getElementById('btn-lang').addEventListener('click', () => {
    setLang(CURRENT_LANG === 'fr' ? 'en' : 'fr');
  });

  window.addEventListener('resize', () => {
    applyPreviewScale();
  });

  // Keyboard shortcuts (desktop)
  document.addEventListener('keydown', e => {
    if (e.ctrlKey && e.key === 's') { e.preventDefault(); downloadJson(); }
    if (e.ctrlKey && e.key === 'p') { /* let browser handle */ }
  });
}

document.addEventListener('DOMContentLoaded', init);

/* ============= EXPORT MODAL ============= */
function openExportModal() {
  const m = document.getElementById('export-modal');
  m.hidden = false;
  // Reset à l'état "choix initial"
  document.getElementById('export-png-config').hidden = true;
  document.querySelector('.export-modal-choices').hidden = false;
  document.getElementById('export-modal-title').textContent = t('modal.export.title');
  // Focus pour accessibilité
  document.getElementById('export-choice-pdf').focus();
}

function closeExportModal() {
  document.getElementById('export-modal').hidden = true;
}

function handleExportPdf() {
  closeExportModal();
  // Léger délai pour laisser la modale se fermer avant la boîte d'impression
  setTimeout(() => window.print(), 100);
}

/* ---- Step 2 : sélecteur de pages PNG ---- */

/* Extrait un hint lisible depuis un élément .page du DOM.
   Lit le premier .p-section trouvé dans la page — c'est le titre de section
   qui figure sur chaque page (OPÉRATION, SITAC, MISSION 1…, etc.).
   escapeHtml obligatoire : le contenu vient de données utilisateur. */
function pngPageHint(pageEl) {
  if (!pageEl) return '—';
  const sec = pageEl.querySelector('.p-section');
  if (sec && sec.textContent.trim()) return escapeHtml(sec.textContent.trim());
  return '—';
}

function updatePngExportCount() {
  const cbs = document.querySelectorAll('.export-png-page-cb:checked');
  const span = document.getElementById('export-png-count');
  if (!span) return;
  span.textContent = cbs.length ? '(' + cbs.length + ')' : '';
  const goBtn = document.getElementById('export-png-go');
  if (goBtn) goBtn.disabled = cbs.length === 0;
}

function handleExportPngChoice() {
  // S'assurer que l'aperçu est rendu (les .page doivent exister dans le DOM)
  // On ne force PAS le mode ici : les pages sont générées par renderPreview()
  // déjà appelé à l'init. On s'assure juste qu'elles sont dans le DOM.
  renderPreview();

  const allPageEls = document.querySelectorAll('#preview .page');
  const list = document.getElementById('export-png-list');
  if (!list) return;

  // Construire une checkbox par page — data-idx = index réel dans #preview
  list.innerHTML = '';
  allPageEls.forEach(function(pageEl, i) {
    const hint = pngPageHint(pageEl);
    const row = document.createElement('label');
    row.className = 'export-png-page-row';
    // Numéro de page padé sur 2 chiffres pour l'affichage
    const numStr = String(i + 1).padStart(2, '0');
    row.innerHTML =
      '<input type="checkbox" class="export-png-page-cb" data-idx="' + i + '" checked>' +
      '<span class="export-png-page-num">Page ' + numStr + '</span>' +
      '<span class="export-png-page-hint">' + hint + '</span>';
    list.appendChild(row);
  });

  // Passer au step 2 dans la modale
  document.querySelector('.export-modal-choices').hidden = true;
  document.getElementById('export-png-config').hidden = false;
  document.getElementById('export-modal-title').textContent = t('modal.export.titlePng');
  updatePngExportCount();
}

/* ---- Rendu d'une page en PNG A4 en double résolution (1588×2246) ---- */

/* renderPageToPng — version chatF (consolidation post-chatE étape B)
   La classe .page--for-png réplique les règles @media print en CSS standard.
   html2canvas capture le clone avec scale: 2 explicite → PNG 1588×2246 px exact,
   indépendamment du devicePixelRatio de l'appareil (FIX Bug A).
   Plus de second canvas, plus de drawImage, plus de scale 900/794, plus de
   fillRect, plus de cssText bricolé. Le bug de footer disparaît par construction
   (le footer est en position absolute dans la zone figée du clone). */
async function renderPageToPng(pageEl) {
  // Attendre que les polices custom soient chargées (Stardos Stencil, Special Elite…)
  // Évite le FOUT (Flash of Unstyled Text) dans les premiers PNG générés juste après
  // l'ouverture de la page.
  if (document.fonts && document.fonts.ready) {
    await document.fonts.ready;
  }

  const clone = pageEl.cloneNode(true);
  clone.classList.add('page--for-png');   // hérite de toutes les règles @media print via CSS
  // Positionné hors-écran — sans bricoler le layout interne du clone
  clone.style.position = 'fixed';
  clone.style.left = '-9999px';
  clone.style.top = '0';
  clone.style.zIndex = '-1';
  clone.style.pointerEvents = 'none';
  document.body.appendChild(clone);

  try {
    const canvas = await html2canvas(clone, {
      backgroundColor: null,   // la couleur de fond vient de la règle .page (--page-bg)
      logging: false,
      useCORS: true,
      allowTaint: false,
      scale: 2,   // FIX Bug A : échelle fixe (ignore devicePixelRatio) → 1588×2246 px exact (A4 794×1123 ×2)
    });

    return new Promise(function(resolve, reject) {
      canvas.toBlob(function(blob) {
        if (blob) resolve(blob);
        else reject(new Error(t('error.canvasToBlob')));
      }, 'image/png');
    });

  } finally {
    // Cleanup systématique même en cas d'erreur
    if (clone.parentNode) clone.parentNode.removeChild(clone);
  }
}

/* ---- Export effectif (lancé par le bouton "Exporter (N)") ---- */
async function executePngExport() {
  // Récupérer les index de pages cochées (index réels dans #preview)
  const checkedInputs = document.querySelectorAll('.export-png-page-cb:checked');
  const checkedIdx = Array.from(checkedInputs).map(function(cb) {
    return parseInt(cb.dataset.idx, 10);
  });
  if (!checkedIdx.length) return;

  // Les .page sont toujours dans le DOM (mode édition ou aperçu),
  // querySelectorAll fonctionne indépendamment de la classe preview-only.
  // Aucun forçage de mode nécessaire.

  const allPageEls = document.querySelectorAll('#preview .page');
  const toExport = checkedIdx.map(function(i) { return allPageEls[i]; }).filter(Boolean);
  const total = toExport.length;

  // FIX R4 : feedback de progression (option 4)
  // La modale reste ouverte, le bouton devient "Génération X/N..." et le toast s'actualise
  const goBtn = document.getElementById('export-png-go');
  const originalBtnHtml = goBtn.innerHTML;
  goBtn.disabled = true;
  goBtn.setAttribute('aria-busy', 'true');

  function updateProgress(current) {
    const msg = t('toast.exportGenProgress') + current + '/' + total + '…';
    goBtn.innerHTML = msg;
    showToast(msg);
  }

  try {
    if (total === 1) {
      // Une seule page : téléchargement PNG direct
      updateProgress(1);
      const realIdx = checkedIdx[0];
      const fname = 'kb_' + String(realIdx + 1).padStart(2, '0') + '.png';
      const blob = await renderPageToPng(toExport[0]);
      closeExportModal();
      fallbackDownload(blob, fname, t('toast.exportSingle'));

    } else {
      // Plusieurs pages : ZIP
      const zip = new JSZip();
      for (let i = 0; i < toExport.length; i++) {
        updateProgress(i + 1);
        const realIdx = checkedIdx[i];
        const fname = 'kb_' + String(realIdx + 1).padStart(2, '0') + '.png';
        const blob = await renderPageToPng(toExport[i]);
        zip.file(fname, blob);
      }
      const zipBlob = await zip.generateAsync({ type: 'blob' });
      closeExportModal();
      fallbackDownload(zipBlob, 'briefing_kneeboard.zip',
        total + ' ' + t('toast.exportMulti'));
    }
  } catch (err) {
    showToast(t('toast.exportError') + err.message);
    console.error('[Export PNG]', err);
  } finally {
    // Restauration systématique du bouton, même en cas d'erreur
    goBtn.innerHTML = originalBtnHtml;
    goBtn.disabled = false;
    goBtn.removeAttribute('aria-busy');
  }
}

// Bindings modale — câblés ici en global (pas dans init) pour rester cohérent
// avec le pattern "fonctions globales, pas de closures" du projet (cf. DOCS §2.4)
document.addEventListener('DOMContentLoaded', function bindExportModal() {
  document.getElementById('export-modal-backdrop').addEventListener('click', closeExportModal);
  document.getElementById('export-modal-close').addEventListener('click', closeExportModal);
  document.getElementById('export-choice-pdf').addEventListener('click', handleExportPdf);
  document.getElementById('export-choice-png').addEventListener('click', handleExportPngChoice);

  // Boutons Tout cocher / Tout décocher
  document.getElementById('export-png-all').addEventListener('click', function() {
    document.querySelectorAll('.export-png-page-cb').forEach(function(cb) { cb.checked = true; });
    updatePngExportCount();
  });
  document.getElementById('export-png-none').addEventListener('click', function() {
    document.querySelectorAll('.export-png-page-cb').forEach(function(cb) { cb.checked = false; });
    updatePngExportCount();
  });

  // Mise à jour compteur au changement d'une checkbox (délégation sur le container)
  document.getElementById('export-png-list').addEventListener('change', function(e) {
    if (e.target.classList.contains('export-png-page-cb')) updatePngExportCount();
  });

  // Bouton Exporter (N) — lance l'export effectif
  document.getElementById('export-png-go').addEventListener('click', executePngExport);

  // Bouton ← Retour — revient au step 1 (choix PDF/PNG)
  document.getElementById('export-png-back').addEventListener('click', function() {
    document.getElementById('export-png-config').hidden = true;
    document.querySelector('.export-modal-choices').hidden = false;
    document.getElementById('export-modal-title').textContent = t('modal.export.title');
  });

  // Échap pour fermer la modale (quelle que soit l'étape)
  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape' && !document.getElementById('export-modal').hidden) {
      closeExportModal();
    }
  });
});

/* ============= CONSOLE API ============= */
/* All functions below are globally accessible from the browser console.
   No IIFE wrapping — window scope is intentional (cf. DOCS §2.4).

   Wing config read/write (P1.B: editing moved to HQ module):
     wingConfig                          // current wing object (mutable)
     loadWingConfig()                    // → parsed localStorage or DEFAULT_WING_CONFIG
     persistWingConfig()                 // debounced save → localStorage[KEY_WING]
     importWingConfig(file)              // file = File object from <input type="file">
     resetWingConfig()                   // → confirm → DEFAULT_WING_CONFIG + localStorage.removeItem

   Branding refresh (always call after mutating wingConfig directly):
     applyWingBranding()
*/
</script>

</body>
</html>
"""

# ── Generic SVG logos (hardcoded, option C) ──────────────────────────────────
# These are the default wing/squadron logos for the generic "MY WING" config.
# They are embedded as base64 data URLs so the app has no external dependencies.
# Colors: #a8945e (kaki accent) · #2a3038 (anthracite) · #d4c598 (kraft beige)

_GENERIC_WING_LOGO_SVG = '''\
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256">
  <circle cx="128" cy="128" r="115" fill="#d4c598"/>
  <circle cx="128" cy="128" r="115" fill="none" stroke="#a8945e" stroke-width="14"/>
  <circle cx="128" cy="128" r="90" fill="none" stroke="#a8945e" stroke-width="5"/>
  <circle cx="128" cy="128" r="70" fill="none" stroke="#a8945e" stroke-width="2"/>
  <text x="128" y="158" text-anchor="middle"
        font-family="Arial Black, Arial, sans-serif"
        font-weight="900" font-size="86" fill="#2a3038" letter-spacing="-3">WG</text>
</svg>'''

_GENERIC_SQN_LOGO_SVG = '''\
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256">
  <circle cx="128" cy="128" r="115" fill="#d4c598"/>
  <circle cx="128" cy="128" r="115" fill="none" stroke="#a8945e" stroke-width="14"/>
  <circle cx="128" cy="128" r="90" fill="none" stroke="#a8945e" stroke-width="5"/>
  <circle cx="128" cy="128" r="70" fill="none" stroke="#a8945e" stroke-width="2"/>
  <text x="128" y="158" text-anchor="middle"
        font-family="Arial Black, Arial, sans-serif"
        font-weight="900" font-size="86" fill="#2a3038" letter-spacing="-3">01</text>
</svg>'''

_GENERIC_WING_LOGO_DATAURL = (
    'data:image/svg+xml;base64,' +
    base64.b64encode(_GENERIC_WING_LOGO_SVG.encode('utf-8')).decode('ascii')
)
_GENERIC_SQN_LOGO_DATAURL = (
    'data:image/svg+xml;base64,' +
    base64.b64encode(_GENERIC_SQN_LOGO_SVG.encode('utf-8')).decode('ascii')
)
# ─────────────────────────────────────────────────────────────────────────────


def build_default_wing_config(A):
    """Build the embedded default wing config (generic placeholder).

    This is the single source of truth for the default wing.  At runtime,
    the JS reads `wingConfig.wing.*` and `wingConfig.squadrons[*].logo`
    instead of hardcoded constants.

    The 4th VEAW config is distributed separately as wing_config_4th-veaw.json
    and can be imported via the wing editor (📥 Importer config).

    Returns a dict matching the wing_config.json schema (configSchemaVersion 1).
    """
    return {
        "configSchemaVersion": 1,
        "wing": {
            "id": "MY-WING",
            "shortName": "MY WING",
            "fullName": "Mon Wing Virtuel",
            "appTitle": "GÉNÉRATEUR DE BRIEFING",
            "logo": _GENERIC_WING_LOGO_DATAURL,
            "hqStamp": "HQ ░ MY WING",
        },
        "squadrons": [
            {
                "id": "SQN-01",
                "name": "1st Squadron",
                "nickname": "Demo",
                "callsign": "ALPHA",
                "aircraft": ["F-16C Viper"],
                "logo": _GENERIC_SQN_LOGO_DATAURL,
            },
        ],
    }


# Serialise the default config as a JS string literal.
# json.dumps(json.dumps(...)) double-encodes:
#   * inner dump  → produces a valid JSON document
#   * outer dump  → wraps it in a valid JS-quoted string with proper escaping
# At runtime, JS unquotes the string then JSON.parse turns it into an object.
# Faster than parsing as a JS object literal and safer w.r.t. embedded quotes.
_default_wing_config = build_default_wing_config(A)
_default_wing_config_js = json.dumps(
    json.dumps(_default_wing_config, ensure_ascii=False)
)

HTML = HTML.replace('__CSS__', CSS)
HTML = HTML.replace('__LIB_HTML2CANVAS__', A['lib_html2canvas'])
HTML = HTML.replace('__LIB_JSZIP__', A['lib_jszip'])

# ── KRAFT TEXTURES — Phase X étape B ─────────────────────────────────────────
# Le SVG kraft d'origine ne contient que 2 couleurs hex : #d6c7a3 (fond, 1×) et
# #ccbe99 (grain, 139×). On génère 4 variantes thématiques par str.replace pur,
# encodées en base64 et embarquées via 4 placeholders distincts dans le CSS
# (un par bloc body[data-theme="..."]).
#
# Le grain est dérivé du fond avec le même décalage que l'original
# (delta R=-10, G=-9, B=-10 décimaux), pour conserver l'effet "papier" sur
# tous les thèmes.

def modulate_kraft(svg_str, fond_hex, grain_hex):
    """Substitue les 2 couleurs principales du SVG kraft.
    Le SVG original utilise #d6c7a3 (fond) et #ccbe99 (grain horizontal)."""
    return svg_str.replace('#d6c7a3', fond_hex).replace('#ccbe99', grain_hex)

_kraft_svg_str = base64.b64decode(A['KRAFT_SVG']).decode('utf-8')

_kraft_themes = {
    'NATO':         ('#d6c7a3', '#ccbe99'),  # cw-nato (original — preservé)
    'SOVIET':       ('#d4c075', '#cab76b'),  # cw-soviet — ocre chaud
    'MODERN_NATO':  ('#e4dfd2', '#dad6c8'),  # modern-nato — blanc cassé
    'MODERN_EAST':  ('#c8c1b2', '#beb8a8'),  # modern-east — papier grisé
}

for _key, (_fond, _grain) in _kraft_themes.items():
    _modulated_svg = modulate_kraft(_kraft_svg_str, _fond, _grain)
    _b64 = base64.b64encode(_modulated_svg.encode('utf-8')).decode('ascii')
    HTML = HTML.replace(f'__KRAFT_SVG_{_key}__', _b64)

HTML = HTML.replace('__DEFAULT_WING_CONFIG__', _default_wing_config_js)
HTML = HTML.replace('__APP_VERSION__', APP_VERSION)

# Write the final file
os.makedirs(os.path.join(HERE, 'dist'), exist_ok=True)
output_path = os.path.join(HERE, 'dist', 'dcs_briefing_generator.html')
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(HTML)

print(f"File written: {len(HTML):,} bytes ({len(HTML)/1024:.1f} KB)")
print(f"Path: {output_path}")
