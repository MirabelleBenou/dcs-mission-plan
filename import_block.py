#!/usr/bin/env python3
"""Bloc « IMPORT COMMUN » : la fenêtre d'import (HQ, briefing en cours, fichier) écrite une fois, injectée telle quelle dans le Flight Configurator et le Route Planner.

Trois textes, identiques à l'octet dans les deux dist/ :
  build_css()   — la feuille de la fenêtre (thème de l'interface : mêmes variables que les deux modules ; l'accent est --imp-accent, à défaut --fc, à défaut --amber)
  build_html()  — la fenêtre (vide : le bloc la remplit) et le sélecteur de fichier caché
  build_block() — le script : lecture des sources, liste, filtres, fusion, écriture dans la fiche partagée flight_set_v1

Le bloc écrit dans la fiche (group_store_block.py : relire, changer le seul groupe touché, gsPutFlight), jamais dans l'état d'un module. L'emport importé s'écrit en une fois : si le module donne un rappel loadoutFrom(type, payload) (le Flight Configurator), l'emport est écrit déjà converti ;
sinon (le Route Planner) il est écrit brut, unité.payloadIn, avec loadout: null, et le Flight Configurator le convertit à la lecture de la fiche en ne changeant que ces champs.
Il lit group_store_block.py (gsRead, gsPutFlight, gsNewId, gsNameKey, gsSide, gsEnsure, gsSetTheatre, gsJson, gsIsObj) et radio_block.py (RADIO_POSTES, RADIO_FIRST_CHANNEL).
Le module lui donne sa langue et ses rappels par impSetup({ lang, before, onImported, toast, noteLiveries, loadoutFrom }) ; il ouvre la fenêtre par impOpen().

Usage (par les builds) : from import_block import build_block, build_css, build_html
"""

BLOCK_BEGIN = '/* ===== IMPORT COMMUN (HQ, briefing, fichier) ===== */'
BLOCK_END = '/* ===== FIN DE L\'IMPORT COMMUN ===== */'
CSS_BEGIN = '/* ===== IMPORT COMMUN : feuille ===== */'
CSS_END = '/* ===== FIN DE LA FEUILLE D\'IMPORT ===== */'
HTML_BEGIN = '<!-- ===== IMPORT COMMUN : fenêtre ===== -->'
HTML_END = '<!-- ===== FIN DE LA FENÊTRE D\'IMPORT ===== -->'

_CSS = r"""
.imp-modal { --imp-acc: var(--imp-accent, var(--fc, var(--amber))); }
.imp-modal[hidden] { display: none !important; }
.imp-modal { position: fixed; inset: 0; z-index: 10000; display: flex; align-items: center; justify-content: center; padding: 16px; }
.imp-backdrop { position: absolute; inset: 0; background: rgba(0,0,0,.6); }
.imp-panel { position: relative; background: var(--olive-dark); color: var(--paper); border: 2px solid var(--imp-acc); border-top: 3px solid var(--imp-acc); border-radius: 3px; padding: 22px 26px; max-width: 640px; width: 100%; max-height: calc(100vh - 32px); max-height: calc(100dvh - 32px); display: flex; flex-direction: column; overflow: hidden; box-shadow: 0 8px 40px rgba(0,0,0,.6); font-family: var(--f-typewriter); }
.imp-x { position: absolute; top: 2px; right: 6px; min-width: 44px; min-height: 44px; background: none; border: none; color: var(--paper); font-size: 24px; line-height: 1; cursor: pointer; }
.imp-x:hover, .imp-x:focus-visible { color: var(--amber); outline: none; }
.imp-panel h2 { flex: none; font-family: var(--f-stencil); font-weight: 700; font-size: 18px; letter-spacing: 2px; margin: 0 44px 14px 0; text-transform: uppercase; color: var(--amber); }
#imp-body { flex: 1 1 auto; min-height: 0; display: flex; flex-direction: column; overflow-y: auto; }
.imp-block { margin-bottom: 14px; }
.imp-block h3 { font-family: var(--f-stencil); font-weight: 700; font-size: 13px; letter-spacing: 2px; margin: 0 0 8px; color: var(--paper-light); text-transform: uppercase; }
.imp-srcs { flex: none; }
.imp-srcline { flex: none; margin-bottom: 8px; font-size: 12px; display: flex; flex-wrap: wrap; align-items: center; gap: 4px 12px; }
.imp-link { background: none; border: 0; padding: 0 2px; min-height: 44px; font: inherit; color: var(--imp-acc); text-decoration: underline; cursor: pointer; }
.imp-link:focus-visible { outline: 2px solid var(--imp-acc); outline-offset: 2px; }
.imp-src { display: flex; align-items: center; gap: 10px; min-height: 44px; font-size: 13px; cursor: pointer; }
.imp-src.off { opacity: .5; cursor: not-allowed; }
.imp-src input, .imp-fh input { accent-color: var(--imp-acc); width: 20px; height: 20px; flex: none; margin: 0; }
.imp-note { font-size: 11px; color: var(--khaki-light); margin: 0 0 6px 30px; line-height: 1.35; word-break: break-word; }
.imp-note.top { margin-left: 0; }
.imp-warn { color: var(--paper-light); border-left: 3px solid var(--imp-acc); padding: 4px 0 4px 10px; background: rgba(0,0,0,.18); }
.imp-file { display: flex; align-items: center; gap: 10px; margin: 2px 0 4px 30px; font-size: 11px; flex-wrap: wrap; }
.imp-filebtn { background: transparent; border: 1px solid var(--khaki); padding: 6px 12px; min-height: 44px; font-family: inherit; font-size: 11px; cursor: pointer; color: var(--paper); border-radius: 2px; }
.imp-filebtn:hover, .imp-filebtn:focus-visible { background: var(--olive); border-color: var(--imp-acc); outline: none; }
.imp-filename { color: var(--khaki-light); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 100%; }
.imp-bgside { display: flex; align-items: center; gap: 8px; margin: 0 0 6px 30px; font-size: 11px; }
.imp-srcline .imp-bgside { margin: 0; }
.imp-lbl { display: block; font-family: var(--f-stencil); font-weight: 700; font-size: 11px; letter-spacing: 1.8px; text-transform: uppercase; color: var(--amber); margin: 0 0 4px; }
.imp-bgside .imp-lbl { margin: 0; }
.imp-bgsel { display: block; flex: 0 1 auto; max-width: 100%; min-width: 0; }
.imp-fls { flex: 1 1 auto; min-height: 150px; display: flex; flex-direction: column; margin-bottom: 8px; }
.imp-filters { display: flex; gap: 8px; margin: 0 0 8px; flex-wrap: wrap; }
.imp-filters > div { flex: 1 1 110px; min-width: 0; }
.imp-filters > div.nm { flex: 2 1 150px; }
.imp-sel.tbm-trigger.tbm-field {
  display: block; position: relative; contain: inline-size; text-align: left; letter-spacing: normal; text-transform: none; font-weight: 400;
  box-sizing: border-box; width: 100%; min-width: 0; min-height: 44px; padding: 0 34px 0 11px; margin: 0; cursor: pointer;
  font-family: var(--f-typewriter); font-size: 13px; line-height: 42px;
  background: rgba(216,201,165,.92); color: var(--ink);
  border: 1px solid var(--khaki); border-left: 3px solid var(--amber-dark); border-radius: 0;
}
.imp-sel.tbm-trigger.tbm-field::after {
  content: ''; position: absolute; right: 12px; top: 50%; width: 12px; height: 8px; margin-top: -4px; pointer-events: none;
  background: currentColor;
  -webkit-mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='8' viewBox='0 0 12 8'%3E%3Cpath d='M1 1.5l5 5 5-5' fill='none' stroke='%23000' stroke-width='1.6'/%3E%3C/svg%3E") center / 12px 8px no-repeat;
  mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='8' viewBox='0 0 12 8'%3E%3Cpath d='M1 1.5l5 5 5-5' fill='none' stroke='%23000' stroke-width='1.6'/%3E%3C/svg%3E") center / 12px 8px no-repeat;
}
.imp-sel.tbm-trigger.tbm-field .tbm-lbl { margin: 0; padding: 0; line-height: 42px; }
.imp-sel.tbm-trigger.tbm-field .tbm-lbl::after { display: none; }
.imp-sel.tbm-trigger.tbm-field:focus { outline: none; border-left-color: var(--red-stamp); box-shadow: 0 0 0 1px var(--imp-acc); }
.imp-sel.tbm-trigger.tbm-field:disabled { opacity: .5; cursor: default; }
.tbm-panel.tbm-imp { z-index: 10500; }
.imp-in { display: block; box-sizing: border-box; width: 100%; min-width: 0; min-height: 44px; padding: 0 10px; background: rgba(216,201,165,.92); color: var(--ink); border: 1px solid var(--khaki); border-left: 3px solid var(--amber-dark); border-radius: 0; font-family: var(--f-typewriter); font-size: 13px; cursor: text; }
.imp-in:focus { outline: none; border-left-color: var(--red-stamp); box-shadow: 0 0 0 1px var(--imp-acc); }
.imp-bulk { display: flex; flex-wrap: wrap; align-items: center; gap: 6px; margin-bottom: 4px; }
.imp-cnt { margin-left: auto; font-size: 11px; color: var(--khaki-light); }
.imp-list { flex: 1 1 auto; min-height: 90px; overflow-y: auto; border: 1px solid rgba(128,116,84,.5); padding: 4px 10px; background: rgba(0,0,0,.18); }
.imp-flight { padding: 4px 0; }
.imp-flight + .imp-flight { border-top: 1px dashed rgba(128,116,84,.5); }
.imp-flight.off { opacity: .55; }
.imp-fh { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; min-height: 44px; font-size: 13px; cursor: pointer; }
.imp-flight.off .imp-fh { cursor: not-allowed; }
.imp-nm { font-family: var(--f-stencil); letter-spacing: 1px; min-width: 0; overflow-wrap: anywhere; }
.imp-tag { font-family: var(--f-ui); font-size: 10px; padding: 2px 6px; border-radius: 2px; background: var(--olive); color: var(--paper-light); text-transform: uppercase; letter-spacing: 1px; white-space: nowrap; }
.imp-n { font-size: 11px; color: var(--khaki-light); margin-left: auto; text-align: right; }
.imp-parts { display: flex; flex-wrap: wrap; gap: 0 14px; padding-left: 28px; }
.imp-chk { display: inline-flex; align-items: center; gap: 8px; min-height: 44px; cursor: pointer; font-family: var(--f-typewriter); font-size: 12px; }
.imp-chk input { accent-color: var(--imp-acc); width: 18px; height: 18px; margin: 0; flex: none; }
.imp-chk.off { opacity: .4; cursor: default; }
.imp-empty { font-size: 12px; color: var(--khaki-light); margin: 6px 0; }
.imp-actions { flex: none; display: flex; justify-content: space-between; gap: 10px; padding-top: 10px; border-top: 1px solid rgba(128,116,84,.5); }
.imp-btn { background: transparent; border: 2px solid var(--khaki); padding: 8px 18px; min-height: 44px; font-family: var(--f-stencil); font-weight: 700; letter-spacing: 2px; font-size: 13px; cursor: pointer; color: var(--paper); border-radius: 2px; }
.imp-btn:hover { background: var(--olive); }
.imp-btn:focus-visible { outline: 2px solid var(--imp-acc); outline-offset: 2px; }
.imp-btn.go { background: var(--olive-deep); border-color: var(--imp-acc); color: var(--paper-light); }
.imp-btn:disabled { opacity: .4; cursor: not-allowed; pointer-events: none; }
@media (max-height: 800px) { .imp-file + .imp-note { display: none; } }
@media (max-width: 539px) {
  .imp-modal { padding: 8px; }
  .imp-panel { padding: 12px 12px 10px; }
  .imp-panel h2 { margin-bottom: 8px; font-size: 16px; }
  .imp-block { margin-bottom: 8px; }
  .imp-fls { margin-bottom: 4px; }
  .imp-srcline { margin-bottom: 2px; }
  .imp-n { margin-left: 0; text-align: left; width: 100%; }
  .imp-parts { padding-left: 0; gap: 0 10px; }
  .imp-actions .imp-btn { flex: 1; padding: 8px 10px; }
}
@media print { .imp-modal { display: none; } }
"""

_HTML = r"""
<div class="imp-modal" id="imp-modal" hidden role="dialog" aria-modal="true" aria-labelledby="imp-modal-title">
  <div class="imp-backdrop" id="imp-modal-backdrop"></div>
  <div class="imp-panel">
    <button type="button" class="imp-x" id="imp-modal-close" aria-label="Fermer">×</button>
    <h2 id="imp-modal-title"></h2>
    <div id="imp-body"></div>
    <div class="imp-actions">
      <button type="button" class="imp-btn" id="imp-cancel"></button>
      <button type="button" class="imp-btn go" id="imp-go" disabled></button>
    </div>
  </div>
</div>
<input type="file" id="imp-file-in" accept=".json,.zip,application/json,application/zip" hidden>
"""

_JS = r"""
/* Les types que la suite gère, et les canaux par poste (sonde des .miz) : postes offerts = ceux de radio_block.py, sauf le poste HF des deux hélicoptères. */
const IMP_TYPES = ['Mi-24P', 'Mi-8MT', 'F-4E-45MC', 'Mirage-F1EE'];
const IMP_TYPE_LABEL = { 'Mi-24P': 'Mi-24P', 'Mi-8MT': 'Mi-8MT', 'F-4E-45MC': 'F-4E-45MC', 'Mirage-F1EE': 'Mirage F1EE' };
const IMP_DEFAULT_TYPE = 'Mi-24P';
const RADIO_CHANNELS = { 'Mi-24P': { 1: 20, 2: 10 }, 'Mi-8MT': { 1: 20, 2: 10 }, 'F-4E-45MC': { 1: 18, 2: 20 }, 'Mirage-F1EE': { 1: 20, 2: 20 } };
const IMP_MAX_UNITS = 4;
const IMP_PARTS = ['route', 'radios', 'loadout', 'livery'];
const IMP_KEY_HQ = 'mission_snapshot_v1', IMP_KEY_BRIEFING = 'khr26_briefing_state_v2', IMP_KEY_WING = 'wing_config_v1';
const IMP_HQ_SCHEMAS = ['dcs-mission-snapshot-v1', 'dcs-mission-snapshot-v2'];
const IMP_PACKAGE_FORMATS = ['dcs-flight-package-v1', 'dcs-flight-package-v2'];

/* ----- Textes de la fenêtre, FR et EN : le module donne la langue (impSetup) ----- */
const IMP_I18N = {
  fr: {
    'imp.title': 'Importer',
    'imp.close': 'Fermer',
    'imp.src': 'Source',
    'imp.srcline': 'Source : {0}',
    'imp.change': 'changer',
    'imp.src.hq': 'Mission chargée dans HQ',
    'imp.src.bg': 'Briefing en cours',
    'imp.src.file': 'Fichier',
    'imp.hq.none': 'Aucune mission dans HQ : chargez-en une dans HQ (même navigateur).',
    'imp.hq.ok': '{0} · théâtre {1}',
    'imp.bg.none': 'Aucun briefing en cours : ouvrez le Briefing Generator (même navigateur).',
    'imp.bg.ok': '{0} phase(s)',
    'imp.choose': 'Choisir un fichier…',
    'imp.file.note': 'Un paquet de vol (.json ou .zip) ou un briefing (.json).',
    'imp.side': 'Camp',
    'imp.side.groups': 'Camp des groupes',
    'imp.type': 'Type',
    'imp.name': 'Nom',
    'imp.all': 'Tous',
    'imp.red': 'Rouge',
    'imp.blue': 'Bleu',
    'imp.neutral': 'Neutre',
    'imp.noside': 'Aucun',
    'imp.checkshown': 'Cocher les groupes affichés',
    'imp.uncheckall': 'Tout décocher',
    'imp.count': '{0} / {1} groupes affichés',
    'imp.nomatch': 'Aucun groupe ne correspond.',
    'imp.empty': 'Aucun groupe dans cette source.',
    'imp.flights': 'Groupes à importer',
    'imp.none': 'Choisissez une source.',
    'imp.part.route': 'Route',
    'imp.part.radios': 'Radios',
    'imp.part.loadout': 'Emport',
    'imp.part.livery': 'Livrée',
    'imp.new': 'nouveau groupe',
    'imp.exists': 'complète le groupe du module',
    'imp.unmanaged': 'appareil non géré : groupe sans unité, route seule',
    'imp.nounit': 'aucune unité : route seule',
    'imp.noname': 'sans indicatif',
    'imp.bg.type': 'type à choisir ({0})',
    'imp.bg.type0': 'type à choisir',
    'imp.bg.cap': 'limité à 4 unités ({0} annoncées)',
    'imp.units': '{0} unité(s)',
    'imp.theatre.set': 'Le théâtre deviendra {0}.',
    'imp.theatre.other': 'Le théâtre de la source ({0}) n’est pas celui de vos groupes ({1}) : les routes ne sont pas importées.',
    'imp.cancel': 'Annuler',
    'imp.go': 'Importer',
    'imp.done': '{0} groupe(s) importé(s)',
    'imp.multi': '{0} : plusieurs groupes du module portent ce nom, un nouveau groupe est créé',
    'imp.retype': '{0} : {1} passe de {2} à {3}, ses radios et son emport sont effacés',
    'imp.notype': '{0} unité(s) sans type : à choisir ({1})',
    'imp.skipchan': '{0} canal(aux) ignoré(s)',
    'imp.group': 'Groupe {0}',
    'rej.json': 'Fichier illisible : ce n’est pas du JSON.',
    'rej.zip': 'Archive illisible : pas de package.json à la racine.',
    'rej.noTheatre': 'Le paquet n’a pas de théâtre.',
    'rej.noFlight': 'Aucun groupe lisible dans ce fichier.',
    'rej.noManaged': 'Aucun groupe d’un appareil géré ici (Mi-24P, Mi-8MT, F-4E, Mirage F1) dans ce paquet : rien n’a changé.',
    'rej.format': 'Format « {0} » non reconnu ici (attendu : {1}).',
    'rej.unknown': 'inconnu',
    'rej.skip': '{0} groupe(s) illisible(s) ignoré(s).',
    'fmt.pkg': 'paquet de vol',
    'fmt.briefing': 'briefing'
  },
  en: {
    'imp.title': 'Import',
    'imp.close': 'Close',
    'imp.src': 'Source',
    'imp.srcline': 'Source: {0}',
    'imp.change': 'change',
    'imp.src.hq': 'Mission loaded in HQ',
    'imp.src.bg': 'Current briefing',
    'imp.src.file': 'File',
    'imp.hq.none': 'No mission in HQ: load one in HQ (same browser).',
    'imp.hq.ok': '{0} · theatre {1}',
    'imp.bg.none': 'No current briefing: open the Briefing Generator (same browser).',
    'imp.bg.ok': '{0} phase(s)',
    'imp.choose': 'Choose a file…',
    'imp.file.note': 'A flight package (.json or .zip) or a briefing (.json).',
    'imp.side': 'Side',
    'imp.side.groups': 'Groups’ side',
    'imp.type': 'Type',
    'imp.name': 'Name',
    'imp.all': 'All',
    'imp.red': 'Red',
    'imp.blue': 'Blue',
    'imp.neutral': 'Neutral',
    'imp.noside': 'None',
    'imp.checkshown': 'Check shown groups',
    'imp.uncheckall': 'Uncheck all',
    'imp.count': '{0} / {1} groups shown',
    'imp.nomatch': 'No group matches.',
    'imp.empty': 'No group in this source.',
    'imp.flights': 'Groups to import',
    'imp.none': 'Choose a source.',
    'imp.part.route': 'Route',
    'imp.part.radios': 'Radios',
    'imp.part.loadout': 'Loadout',
    'imp.part.livery': 'Livery',
    'imp.new': 'new group',
    'imp.exists': 'completes the module’s group',
    'imp.unmanaged': 'aircraft not handled: group without unit, route only',
    'imp.nounit': 'no aircraft: route only',
    'imp.noname': 'no callsign',
    'imp.bg.type': 'type to pick ({0})',
    'imp.bg.type0': 'type to pick',
    'imp.bg.cap': 'limited to 4 units ({0} announced)',
    'imp.units': '{0} unit(s)',
    'imp.theatre.set': 'The theatre will become {0}.',
    'imp.theatre.other': 'The source’s theatre ({0}) is not your groups’ ({1}): routes are not imported.',
    'imp.cancel': 'Cancel',
    'imp.go': 'Import',
    'imp.done': '{0} group(s) imported',
    'imp.multi': '{0}: several groups in the module have this name, a new group was created',
    'imp.retype': '{0}: {1} changes from {2} to {3}, its radios and loadout are cleared',
    'imp.notype': '{0} unit(s) without a type: to pick ({1})',
    'imp.skipchan': '{0} channel(s) ignored',
    'imp.group': 'Group {0}',
    'rej.json': 'Unreadable file: not JSON.',
    'rej.zip': 'Unreadable archive: no package.json at the root.',
    'rej.noTheatre': 'The package has no theatre.',
    'rej.noFlight': 'No readable group in this file.',
    'rej.noManaged': 'No group of an aircraft handled here (Mi-24P, Mi-8MT, F-4E, Mirage F1) in this package: nothing has changed.',
    'rej.format': 'Format “{0}” not recognised here (expected: {1}).',
    'rej.unknown': 'unknown',
    'rej.skip': '{0} unreadable group(s) skipped.',
    'fmt.pkg': 'flight package',
    'fmt.briefing': 'briefing'
  }
};
const IMP = { hooks: {}, I: null, bound: false };
function impLang() { try { return IMP.hooks.lang && IMP.hooks.lang() === 'en' ? 'en' : 'fr'; } catch (e) { return 'fr'; } }
function impT(key) { const own = IMP_I18N[impLang()]; return key in own ? own[key] : (key in IMP_I18N.fr ? IMP_I18N.fr[key] : key); }
function impTf(key, ...args) { return impT(key).replace(/\{(\d+)\}/g, (m, i) => (Number(i) < args.length ? String(args[i]) : m)); }

/* ----- Petits utilitaires ----- */
function impEsc(s) { return String(s === undefined || s === null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;'); }
function impNum(v) { return typeof v === 'number' && isFinite(v); }
function impStr(v) { return typeof v === 'string' ? v : ''; }
function impHas(o, k) { return Object.prototype.hasOwnProperty.call(o, k); }
function impClone(o) { return JSON.parse(JSON.stringify(o)); }
function impNorm(x) { return String(x).normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase(); }
function impSame(a, b) { return impStr(a).replace(/\s+/g, '').toLowerCase() === impStr(b).replace(/\s+/g, '').toLowerCase(); }
function impHasText(v) { return typeof v === 'string' && v.trim() !== ''; }
function impRouteKeys(points) { return gsIsObj(points) ? Object.keys(points).filter(k => /^\d+$/.test(k)).sort((a, b) => a - b) : []; }

/* Une unité neuve et son indicatif (le Flight Configurator les emploie aussi) : un type donné est gardé tel quel, '' compris (unité sans type) ; sans type, le type par défaut. */
function newUnit(type) { return { type: typeof type === 'string' ? type : IMP_DEFAULT_TYPE, name: '', callsign: '', csRaw: undefined, onboard: '', livery: '', radios: {}, loadout: null, folded: false }; }
function csText(v) {
  if (typeof v === 'number') return String(v);
  if (typeof v === 'string') return v;
  return (gsIsObj(v) && typeof v.name === 'string') ? v.name : '';
}
function impRadioCount(u) {
  let n = 0;
  Object.keys(RADIO_CHANNELS[u.type] || {}).forEach(r => { for (let c = 1; c <= RADIO_CHANNELS[u.type][r]; c++) if (gsIsObj(u.radios) && gsIsObj(u.radios[r]) && impStr(String(u.radios[r][c] === undefined ? '' : u.radios[r][c])).trim() !== '') n++; });
  return n;
}
function impGroupLabel(f, i) { return gsNameKey(f.name) !== '' ? f.name.trim() : impTf('imp.group', i + 1); }
function impUnitLabel(f, i, u, k) { return impStr(u.name).trim() !== '' ? u.name.trim() : impGroupLabel(f, i) + '-' + (k + 1); }

/* ----- Les types et les unités d'un vol lu (HQ ou paquet, v1 ou v2) ----- */
function impUnitType(f, u) { return gsIsObj(u) && typeof u.type === 'string' && u.type !== '' ? u.type : (gsIsObj(f) && typeof f.aircraftType === 'string' ? f.aircraftType : ''); }
function impFlightTypes(f) {
  const out = [], us = (gsIsObj(f) && Array.isArray(f.units) ? f.units : []).filter(gsIsObj);
  us.forEach(u => { const x = impUnitType(f, u); if (x !== '' && out.indexOf(x) < 0) out.push(x); });
  if (!us.length && gsIsObj(f) && typeof f.aircraftType === 'string' && f.aircraftType !== '') out.push(f.aircraftType);
  return out;
}

/* Un vol lu → une ligne de la liste. En v1 il faut un aircraftType (chaîne) que ses unités sans type prennent ; en v2 chaque unité porte le sien.
   « géré » : au moins une unité (ou son type de vol) et tous les types dans IMP_TYPES. Sinon : un groupe sans unité, sa route seule. */
function impFlightRow(f, v1) {
  if (!gsIsObj(f) || typeof f.groupName !== 'string' || (v1 && typeof f.aircraftType !== 'string')) return null;
  const points = (gsIsObj(f.route) && gsIsObj(f.route.points) && impRouteKeys(f.route.points).length) ? f.route.points : null;
  const units = (Array.isArray(f.units) ? f.units : []).filter(gsIsObj);
  const g = v1 ? f : { units: f.units };      // en v2 le vol n'a pas de type : seules ses unités parlent
  const eff = units.length ? units.map(u => impUnitType(g, u)) : impFlightTypes(g);
  const managed = eff.length > 0 && eff.every(x => IMP_TYPES.indexOf(x) >= 0);
  const hasRadios = units.some(u => Array.isArray(u.radios) && u.radios.some(r => gsIsObj(r) && gsIsObj(r.channels) && Object.keys(r.channels).length));
  const avail = {
    route: !!points, radios: managed && hasRadios,
    loadout: managed && units.some(u => gsIsObj(u.payload) && gsIsObj(u.payload.pylons)),
    livery: managed && units.some(u => typeof u.liveryId === 'string' && u.liveryId !== '')
  };
  const row = {
    kind: 'flight', name: f.groupName, aircraftType: v1 ? f.aircraftType : undefined, types: impFlightTypes(g),
    coalition: (f.coalition === 'blue' || f.coalition === 'red') ? f.coalition : '', coal: typeof f.coalition === 'string' ? f.coalition : '',
    managed: managed, noUnit: eff.length === 0, points: points, units: units, avail: avail, ok: true
  };
  row.count = managed ? Math.min(units.length || 1, IMP_MAX_UNITS) : 0;
  return row;
}
function impNoteLiveries(f, v1) {
  try { if (IMP.hooks.noteLiveries && gsIsObj(f)) IMP.hooks.noteLiveries(v1 ? f : { units: f.units }); } catch (e) { /* facultatif */ }
}
/* Une source : ses lignes lisibles ; la mission de HQ n'a rien de coché à l'ouverture (on y choisit parmi beaucoup), un paquet : tous les vols. */
function impSource(kind, theatre, file, list, v1) {
  list.forEach(f => impNoteLiveries(f, v1));
  const rows = list.map(f => impFlightRow(f, v1)).filter(Boolean);
  rows.forEach(r => { r.on = kind !== 'hq'; r.chk = Object.assign({}, r.avail); });
  return { kind: kind, theatre: theatre, file: file, rows: rows, skipped: list.length - rows.length };
}
function impReadHqObject() {
  const o = gsJson(IMP_KEY_HQ);
  const ok = gsIsObj(o) && IMP_HQ_SCHEMAS.indexOf(o.schema) >= 0 && gsIsObj(o.sourceMission) && typeof o.sourceMission.theatre === 'string' && Array.isArray(o.flights);
  return ok ? o : null;
}
function impReadHq() {
  const o = impReadHqObject();
  if (!o) return null;
  const src = impSource('hq', o.sourceMission.theatre, impStr(o.sourceMission.filename), o.flights, o.schema === 'dcs-mission-snapshot-v1');
  return src.rows.length ? src : null;
}
function impReadPackage(o, fname) {
  if (typeof o.theatre !== 'string' || o.theatre === '') return { reject: 'rej.noTheatre' };
  const src = impSource('file', o.theatre, fname || '', Array.isArray(o.flights) ? o.flights : [], o.format === 'dcs-flight-package-v1');
  src.what = 'pkg';
  if (!src.rows.length) return { reject: 'rej.noFlight' };
  return { src: src };
}

/* ----- Le briefing : une ligne par indicatif, la règle du Datacard Generator (phaseIdentity) ----- */
function impIsBriefing(o) {
  return !!(o && typeof o === 'object' && !Array.isArray(o) && o.meta && typeof o.meta === 'object' && Array.isArray(o.phases) && !('format' in o));
}
function impPhaseIdentity(ph, wing) {
  const guest = ph.squadron === '__guest__';
  const g = (guest && ph.guestSquadron && typeof ph.guestSquadron === 'object') ? ph.guestSquadron : {};
  const sq = (!guest && ph.squadron && wing && Array.isArray(wing.squadrons)) ? (wing.squadrons.find(s => s && s.id === ph.squadron) || null) : null;
  let callsign = '';
  if (impHasText(ph.subgroup)) callsign = ph.subgroup.trim();
  else if (guest && impHasText(g.subgroup)) callsign = g.subgroup.trim();
  else if (guest && impHasText(g.name)) callsign = g.name.trim();
  else if (sq && impHasText(sq.callsign)) callsign = sq.callsign.trim();
  else callsign = impStr(ph.squadron).trim();
  if (guest && callsign === '__guest__') callsign = '';
  const aircraft = guest ? impStr(g.aircraft).trim() : impStr(ph.aircraft).trim();
  let id, sub, ac;
  if (guest) {
    id = impHasText(g.name) ? g.name : '?';
    sub = impHasText(ph.subgroup) ? ph.subgroup : impStr(g.subgroup);
    ac = impHasText(g.aircraft) ? g.aircraft : '?';
  } else {
    id = impStr(ph.squadron);
    sub = impStr(ph.subgroup);
    ac = impHasText(ph.aircraft) ? ph.aircraft : ((sq && Array.isArray(sq.aircraft) && sq.aircraft.length) ? impStr(sq.aircraft[0]) : '');
  }
  return { callsign: callsign, aircraft: aircraft, key: id + '||' + sub + '||' + ac };
}
function impNormCount(v) {
  if (typeof v === 'number' || typeof v === 'string') { const n = parseInt(v, 10); if (Number.isInteger(n) && n >= 1) return n; }
  return null;
}
/* Le nom d'un poste du type, sans ce qui suit « ( » : « R-863 (VHF/UHF) » → « R-863 » */
function impPosteShort(type, idx) {
  const n = typeof radioPosteName === 'function' ? radioPosteName(type, idx) : '';
  return n.split('(')[0];
}
/* Le plan radio du briefing pour un type : { posts: { poste: { canal du .miz: fréquence } }, ignored } ; canal du .miz = canal du briefing − premier canal du cockpit + 1 */
function impBriefingTable(b, type) {
  const out = { posts: {}, ignored: 0 };
  if (IMP_TYPES.indexOf(type) < 0) return out;
  const rp = gsIsObj(b.radioPlan) ? b.radioPlan : {};
  const items = Array.isArray(rp.items) ? rp.items.filter(gsIsObj) : [];
  const byId = {};
  items.forEach(it => { byId[it.id] = it; });
  const plan = (Array.isArray(rp.aircraftPlans) ? rp.aircraftPlans : []).find(p => gsIsObj(p) && impSame(p.aircraft, type));
  if (!plan) return out;
  const posts = Object.keys(RADIO_CHANNELS[type]).map(Number);
  const shortOf = i => impPosteShort(type, i).replace(/\s+/g, '').toLowerCase();
  const used = {};       // nom court → combien de radios du plan l'ont déjà pris
  (Array.isArray(plan.radios) ? plan.radios : []).forEach(r => {
    if (!gsIsObj(r)) return;
    const chans = (Array.isArray(r.channels) ? r.channels : []).filter(gsIsObj).filter(ch => !(ch.channel === '' || ch.channel === null || ch.channel === undefined));
    const nm = impStr(r.name).replace(/\s+/g, '').toLowerCase();
    let poste = 0;
    if (nm !== '') {
      const same = [];       // les postes du type qui portent ce nom court, dans l'ordre de leur numéro
      for (let i = 1; i <= 9; i++) if (shortOf(i) === nm) same.push(i);
      if (same.length > 1) { const k = used[nm] || 0; used[nm] = k + 1; poste = same[k] || 0; }       // plusieurs postes au même nom court : les radios du plan de ce nom les prennent dans l'ordre, la suivante est ignorée
      else poste = same.length ? same[0] : 0;
    }
    const table = {};
    chans.forEach(ch => {
      if (!poste || posts.indexOf(poste) < 0) { out.ignored++; return; }
      const cock = Number(String(ch.channel).trim());
      const fm = impHas(RADIO_FIRST_CHANNEL, type) ? RADIO_FIRST_CHANNEL[type] : null;
      const first = fm && impHas(fm, poste) ? fm[poste] : 1;
      const miz = cock - first + 1;
      if (!Number.isInteger(cock) || String(ch.channel).trim() === '' || !Number.isInteger(miz) || miz < 1 || miz > RADIO_CHANNELS[type][poste]) { out.ignored++; return; }
      let raw = ch.mode === 'custom' ? ch.frequency : (byId[ch.itemId] ? byId[ch.itemId].frequency : undefined);
      const f = Number(String(raw === undefined || raw === null ? '' : raw).trim().replace(',', '.'));
      if (String(raw === undefined || raw === null ? '' : raw).trim() === '' || !isFinite(f) || !(f > 0)) { out.ignored++; return; }
      table[String(miz)] = String(f);
    });
    if (Object.keys(table).length) out.posts[poste] = table;
  });
  return out;
}
function impBriefingSource(b, fname) {
  const wing = gsJson(IMP_KEY_WING);
  const rows = [], seen = {}, tables = {};
  const tableOf = ty => (impHas(tables, ty) ? tables[ty] : (tables[ty] = impBriefingTable(b, ty)));
  b.phases.forEach(ph => {
    if (!gsIsObj(ph)) return;
    const idn = impPhaseIdentity(ph, wing);
    if (idn.callsign === '') {
      rows.push({ kind: 'bg', name: '', title: impStr(ph.title), noName: true, types: [], coalition: '', managed: false, points: null, units: [], avail: { route: false, radios: false, loadout: false, livery: false }, ok: false, on: false, chk: { route: false, radios: false, loadout: false, livery: false }, count: 0 });
      return;
    }
    if (impHas(seen, idn.callsign)) return;       // le nom revient : la première phase décide du type et du nombre
    seen[idn.callsign] = true;
    const type = IMP_TYPES.indexOf(idn.aircraft) >= 0 ? idn.aircraft : '';
    let n = impNormCount(ph.count), capped = 0;
    if (n === null) {
      const groups = (gsIsObj(b.roster) && Array.isArray(b.roster.groups)) ? b.roster.groups : [];
      const grp = groups.find(x => gsIsObj(x) && x.missionKey === idn.key);
      n = (grp && Array.isArray(grp.pilots) && grp.pilots.length) ? grp.pilots.length : 1;
    }
    if (n > IMP_MAX_UNITS) { capped = n; n = IMP_MAX_UNITS; }
    const avail = { route: false, radios: type !== '' && Object.keys(tableOf(type).posts).length > 0, loadout: false, livery: false };
    rows.push({ kind: 'bg', name: idn.callsign, aircraft: idn.aircraft, type: type, types: type ? [type] : [], coalition: '', managed: false, points: null, units: [], avail: avail, ok: true, on: true, chk: Object.assign({}, avail), count: n, capped: capped });
  });
  return { kind: 'bg', what: 'bg', theatre: '', file: fname || '', rows: rows, skipped: 0, brief: b, tables: tables, tableOf: tableOf, phases: b.phases.length };
}
function impReadBg() {
  const b = gsJson(IMP_KEY_BRIEFING);
  if (!gsIsObj(b) || !Array.isArray(b.phases) || !b.phases.length) return null;
  const src = impBriefingSource(b, '');
  return src.rows.length ? src : null;
}
function impReadBriefing(o, fname) {
  if (!o.phases.length) return { reject: 'rej.noFlight' };
  const src = impBriefingSource(o, fname);
  src.kind = 'file';
  if (!src.rows.length) return { reject: 'rej.noFlight' };
  return { src: src };
}
/* Le contenu décide : un paquet (dcs-flight-package-v1 ou v2) ou un briefing (meta, phases, sans clé « format ») ; autre chose : { reject, args } */
function impReadAny(parsed, fname) {
  if (gsIsObj(parsed) && IMP_PACKAGE_FORMATS.indexOf(parsed.format) >= 0) return impReadPackage(parsed, fname);
  if (impIsBriefing(parsed)) return impReadBriefing(parsed, fname);
  const f = gsIsObj(parsed) ? (parsed.format || parsed.schema) : undefined;
  const found = ((typeof f === 'string' && f !== '') || typeof f === 'number') ? String(f) : impT('rej.unknown');
  return { reject: 'rej.format', args: [found, impT('fmt.pkg') + ', ' + impT('fmt.briefing')] };
}

/* ----- Lire un fichier : un .json, ou un .zip qui porte package.json à sa racine ----- */
function impZipEntry(b, want) {
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
    if (name === want) {
      if ((flags & 1) || lho + 30 > n || dv.getUint32(lho, true) !== 0x04034b50) return null;
      const start = lho + 30 + dv.getUint16(lho + 26, true) + dv.getUint16(lho + 28, true);
      if (start + csz > n || usz > 64 * 1048576) return null;
      return { method: method, data: b.subarray(start, start + csz) };
    }
    p += 46 + nl + xl + cl;
  }
  return null;
}
/* Le texte de package.json d'un zip (null s'il n'y en a pas) : JSZip quand la page l'embarque, sinon le lecteur natif (stocké ou deflate) */
function impZipText(bytes) {
  if (typeof JSZip !== 'undefined') return JSZip.loadAsync(bytes).then(z => { const e = z.file('package.json'); return e ? e.async('string') : null; });
  const ent = impZipEntry(bytes, 'package.json');
  if (!ent) return Promise.resolve(null);
  if (ent.method === 0) return Promise.resolve(new TextDecoder('utf-8').decode(ent.data));
  if (ent.method !== 8 || typeof DecompressionStream === 'undefined') return Promise.reject(new Error('zip'));
  return new Response(new Blob([ent.data]).stream().pipeThrough(new DecompressionStream('deflate-raw'))).arrayBuffer().then(buf => new TextDecoder('utf-8').decode(new Uint8Array(buf)));
}
function impReadJsonFile(file, done) {
  const parse = text => {
    try { done({ parsed: JSON.parse(text.charCodeAt(0) === 0xFEFF ? text.slice(1) : text) }); } catch (e) { done({ reject: 'rej.json' }); }
  };
  const reader = new FileReader();
  reader.onerror = () => done({ reject: 'rej.json' });
  reader.onload = () => {
    const bytes = new Uint8Array(reader.result);
    if (!(bytes.length >= 2 && bytes[0] === 0x50 && bytes[1] === 0x4B)) {       // pas de « PK » en tête : un JSON, en UTF-8 ou UTF-16
      const enc = (bytes[0] === 0xFF && bytes[1] === 0xFE) ? 'utf-16le' : ((bytes[0] === 0xFE && bytes[1] === 0xFF) ? 'utf-16be' : 'utf-8');
      parse(new TextDecoder(enc).decode(bytes));
      return;
    }
    impZipText(bytes).then(text => { if (text === null) done({ reject: 'rej.zip' }); else parse(text); }, () => done({ reject: 'rej.zip' }));
  };
  reader.readAsArrayBuffer(file);
}

/* ----- La fiche : retrouver un groupe, le compléter ou le créer ----- */
/* Même nom rogné (la casse compte), même camp (gsSide) : la règle de HQ */
function impFindGroups(flights, name, side) { return flights.filter(f => gsNameKey(f.name) === gsNameKey(name) && gsSide(f.coalition) === gsSide(side)); }
function impBgSideDefault() {
  const g = gsRead();
  if (!g || !g.flights.length) return 'red';
  const sides = [];
  g.flights.forEach(f => { const s = gsSide(f.coalition); if (sides.indexOf(s) < 0) sides.push(s); });
  return sides.length === 1 && sides[0] !== '' ? sides[0] : 'red';
}
/* Le théâtre : une fiche dont les groupes sont d'un autre théâtre que la source garde le sien, et les routes ne s'importent pas */
function impRouteOff(src, g) {
  return !!(src.theatre && g && g.flights.length && g.theatre !== '' && g.theatre !== src.theatre);
}
function impMergeRadios(unit, type, radios) {
  radios.forEach(r => {
    if (!gsIsObj(r) || !gsIsObj(r.channels) || !impHas(RADIO_CHANNELS[type] || {}, r.radioIndex)) return;
    const post = {};
    Object.keys(r.channels).forEach(c => {
      const v = r.channels[c];
      if (/^\d+$/.test(c) && c >= 1 && c <= RADIO_CHANNELS[type][r.radioIndex] && impNum(v)) post[c] = String(v);
    });
    if (Object.keys(post).length) unit.radios[r.radioIndex] = post;
  });
}
/* Un changement de type d'une unité du groupe : ses radios et son emport (qui se lisent selon le type) sont vidés, un avertissement le dit s'il y en avait */
function impRetype(st, target, fi, k, u, ty) {
  if (impRadioCount(u) > 0 || u.loadout || u.payloadIn) st.warn.push(impTf('imp.retype', impGroupLabel(target, fi), impUnitLabel(target, fi, u, k), IMP_TYPE_LABEL[u.type] || u.type, IMP_TYPE_LABEL[ty] || ty));
  u.type = ty; u.radios = {}; u.loadout = null;
  delete u.payloadIn;
}
/* Les unités d'un vol de HQ ou d'un paquet se complètent par rang. Une unité neuve prend l'identité de celle de la source ; une unité du groupe d'un autre type prend toujours le type de la source. */
function impMergeUnit(st, target, fi, k, iu, chk, src) {
  let u = target.units[k];
  const ty = impUnitType(src, iu);
  if (!u) {
    u = newUnit(IMP_TYPES.indexOf(ty) >= 0 ? ty : (target.units.length ? target.units[target.units.length - 1].type : IMP_DEFAULT_TYPE));
    target.units.push(u);
    u.name = impStr(iu.name) === target.name.trim() + '-' + (k + 1) ? '' : impStr(iu.name);      // le nom par défaut reste un nom par défaut
    u.csRaw = iu.callsign; u.callsign = csText(iu.callsign);
    u.onboard = (typeof iu.onboardNum === 'string' || impNum(iu.onboardNum)) ? String(iu.onboardNum) : '';
  } else if (IMP_TYPES.indexOf(ty) >= 0 && ty !== u.type) impRetype(st, target, fi, k, u, ty);
  if (chk.livery && typeof iu.liveryId === 'string') u.livery = iu.liveryId;
  if (chk.radios && Array.isArray(iu.radios)) impMergeRadios(u, u.type, iu.radios);
  if (chk.loadout && gsIsObj(iu.payload) && gsIsObj(iu.payload.pylons)) {
    const conv = st.convert && u.type !== '' ? IMP.hooks.loadoutFrom : null;
    if (conv) { u.loadout = conv(u.type, impClone(iu.payload)) || null; delete u.payloadIn; }       // le module convertit : l'emport s'écrit tel qu'il le garde, jamais d'état intermédiaire
    else { u.payloadIn = impClone(iu.payload); u.loadout = null; }       // brut : le Flight Configurator le convertit à la lecture de la fiche
  }
}
/* Les unités d'une ligne du briefing : le nombre voulu, du type de la ligne ('' : sans type, à choisir) ; le plan radio du type s'applique à chaque unité du groupe de ce type */
function impBriefingUnits(st, target, fi, row, chk, src) {
  const ty = row.type;
  for (let k = 0; k < row.count; k++) {
    let u = target.units[k];
    if (!u) {
      u = newUnit(ty);
      target.units.push(u);
      if (ty === '') { st.noTypeUnits++; if (st.noTypeGroups.indexOf(target.name) < 0) st.noTypeGroups.push(target.name); }
    } else if (ty !== '' && ty !== u.type) impRetype(st, target, fi, k, u, ty);
  }
  if (chk.radios && ty !== '') {
    const tab = src.tableOf(ty);
    if (!impHas(st.counted, ty)) { st.counted[ty] = true; st.ignored += tab.ignored; }
    target.units.forEach(u => {
      if (u.type !== ty) return;
      Object.keys(tab.posts).forEach(p => { u.radios[p] = Object.assign({}, tab.posts[p]); });
    });
  }
}
/* Écrit les lignes cochées dans la fiche, une par une (relire, changer le seul groupe touché, gsPutFlight) ; rend le compte rendu pour le rappel du module */
function impWrite(src, picks, side) {
  const st = { created: new Set(), ids: [], warn: [], noTypeUnits: 0, noTypeGroups: [], ignored: 0, counted: {}, failed: false, convert: true };
  if (!gsEnsure()) { st.failed = true; return impResult(st, 0, src); }
  const g0 = gsRead();
  const routeOff = impRouteOff(src, g0);
  picks = picks.filter(r => r.kind === 'bg' || r.managed || (r.chk.route && r.points && !routeOff));       // un vol sans unité gérée n'importe que sa route : sans elle, rien
  if (src.theatre && (!g0.flights.length || g0.theatre === '') && !gsSetTheatre(src.theatre)) { st.failed = true; return impResult(st, 0, src); }
  for (let n = 0; n < picks.length; n++) {
    const row = picks[n], chk = Object.assign({}, row.chk);
    if (routeOff) chk.route = false;
    const g = gsRead();
    if (!g) { st.failed = true; break; }
    const coalition = row.kind === 'bg' ? gsSide(side) : row.coalition;
    const hits = impFindGroups(g.flights, row.name, coalition);
    let target = (hits.length === 1 && !st.created.has(hits[0].fcId)) ? impClone(hits[0]) : null;
    if (!target && hits.length > 0) st.warn.push(impTf('imp.multi', row.name.trim()));
    const isNew = !target;
    if (isNew) target = { fcId: gsNewId(), name: row.name.trim(), coalition: gsSide(coalition), route: null, units: [] };
    let fi = g.flights.findIndex(x => x.fcId === target.fcId);
    if (fi < 0) fi = g.flights.length;
    if (!Array.isArray(target.units)) target.units = [];
    if (chk.route && row.points) { target.route = { points: impClone(row.points) }; delete target.routeLink; }       // une route importée est un autre plan de vol : le lien avec le Route Planner tombe, le Route Planner la reprend
    if (row.kind === 'bg') impBriefingUnits(st, target, fi, row, chk, src);
    else if (row.managed) {
      row.units.slice(0, IMP_MAX_UNITS).forEach((iu, k) => impMergeUnit(st, target, fi, k, iu, chk, row.aircraftType !== undefined ? row : { units: row.units }));
      if (!target.units.length) target.units.push(newUnit(IMP_TYPES.indexOf(row.types[0]) >= 0 ? row.types[0] : IMP_DEFAULT_TYPE));      // un vol sans unité : une unité, du type du vol
    }
    if (!gsPutFlight(target)) { st.failed = true; break; }
    if (isNew) st.created.add(target.fcId);
    st.ids.push(target.fcId);
  }
  return impResult(st, picks.length, src);
}
function impResult(st, n, src) {
  const parts = [impTf('imp.done', n)].concat(st.warn);
  if (st.noTypeUnits) parts.push(impTf('imp.notype', st.noTypeUnits, st.noTypeGroups.join(', ')));
  if (st.ignored) parts.push(impTf('imp.skipchan', st.ignored));
  return { fcIds: st.ids, created: st.created.size, warnings: st.warn.slice(), noTypeUnits: st.noTypeUnits, ignored: st.ignored, picked: n, failed: st.failed, kind: src ? src.kind : '', text: parts.join(' · '), ms: (st.warn.length || st.noTypeUnits || st.ignored) ? 7000 : undefined };
}
/* « Ouvrir » un paquet au Flight Configurator : ses vols gérés, toutes leurs parties, dans une liste de groupes neuve ; rend { flights, warn } (les groupes au format de la fiche, emport brut) */
function impBuildGroups(rows) {
  const st = { created: new Set(), warn: [], noTypeUnits: 0, noTypeGroups: [], ignored: 0, counted: {} }, flights = [];
  rows.forEach(row => {
    const hits = impFindGroups(flights, row.name, row.coalition);
    let target = (hits.length === 1 && !st.created.has(hits[0].fcId)) ? hits[0] : null;
    if (!target && hits.length > 0) st.warn.push(impTf('imp.multi', row.name.trim()));
    if (!target) { target = { fcId: gsNewId(), name: row.name.trim(), coalition: gsSide(row.coalition), route: null, units: [] }; flights.push(target); st.created.add(target.fcId); }
    const fi = flights.indexOf(target);
    if (row.chk.route && row.points) { target.route = { points: impClone(row.points) }; delete target.routeLink; }
    row.units.slice(0, IMP_MAX_UNITS).forEach((iu, k) => impMergeUnit(st, target, fi, k, iu, row.chk, row.aircraftType !== undefined ? row : { units: row.units }));
    if (!target.units.length) target.units.push(newUnit(IMP_TYPES.indexOf(row.types[0]) >= 0 ? row.types[0] : IMP_DEFAULT_TYPE));
  });
  return { flights: flights, warn: st.warn };
}

/* ----- La fenêtre ----- */
function impCur(I) { I = I || IMP.I; return I && (I.src === 'hq' || I.src === 'bg' || I.src === 'file') ? I[I.src] : null; }
function impIsOpen() { return !!IMP.I && !document.getElementById('imp-modal').hidden; }
function impSetup(hooks) {
  IMP.hooks = hooks || {};
  if (IMP.bound) return;
  IMP.bound = true;
  const m = document.getElementById('imp-modal');
  ['imp-modal-backdrop', 'imp-modal-close', 'imp-cancel'].forEach(id => document.getElementById(id).addEventListener('click', () => impClose()));
  document.getElementById('imp-go').addEventListener('click', impGo);
  m.addEventListener('click', e => {
    const b = e.target.closest ? e.target.closest('[data-act]') : null;
    if (!b || b.disabled || !IMP.I) return;
    const act = b.getAttribute('data-act');
    if (act === 'imp-pick-file') document.getElementById('imp-file-in').click();
    else if (act === 'imp-change-src') { IMP.I.srcOpen = true; impRender(); }
    else if (act === 'imp-check-shown') impSetShown(true);
    else if (act === 'imp-uncheck-all') impSetShown(false);
  });
  m.addEventListener('input', e => { if (e.target.id === 'imp-name' && IMP.I) { IMP.I.name = e.target.value; impRenderList(); } });
  m.addEventListener('change', e => {
    const el = e.target, I = IMP.I, cur = impCur(I);
    if (!I) return;
    if (el.name === 'imp-src') {
      I.src = el.value; I.srcOpen = false; I.msg = '';
      if (I.src === 'bg') { I.bg = impReadBg(); I.bgSide = impBgSideDefault(); }
      if (I.src === 'hq') I.hq = impReadHq();
      I.side = 'all'; I.type = 'all'; I.name = '';
      impRender();
    }
    else if (el.id === 'imp-side') { I.side = el.value; impRenderList(); }
    else if (el.id === 'imp-type') { I.type = el.value; impRenderList(); }
    else if (el.id === 'imp-bg-side') { I.bgSide = el.value; impRenderList(); }
    else if (cur && el.hasAttribute('data-imp-flight')) { cur.rows[Number(el.getAttribute('data-imp-flight'))].on = el.checked; impUpdateGo(); }
    else if (cur && el.hasAttribute('data-imp-part')) { cur.rows[Number(el.getAttribute('data-imp-i'))].chk[el.getAttribute('data-imp-part')] = el.checked; impUpdateGo(); }
  });
  document.getElementById('imp-file-in').addEventListener('change', e => { const f = e.target.files && e.target.files[0]; e.target.value = ''; if (f) impFile(f); });
  document.addEventListener('keydown', e => { if (e.key === 'Escape' && impIsOpen()) impClose(); });
}
/* Ouvre la fenêtre ; opts.parsed (+ name) : un fichier déjà lu (« Ouvrir » au Route Planner), la source « Fichier » est alors celle-là. Rend faux si ce fichier est refusé (le refus est dit). */
function impOpen(opts) {
  opts = opts || {};
  const I = IMP.I = { src: '', hq: impReadHq(), bg: impReadBg(), file: null, side: 'all', type: 'all', name: '', srcOpen: false, msg: '', bgSide: impBgSideDefault(), opener: opts.opener || null };
  if (opts.parsed !== undefined) {
    const res = impReadAny(opts.parsed, opts.name || '');
    if (res.reject) { IMP.I = null; impReject(res.reject, res.args); return false; }
    I.file = res.src; I.src = 'file';
  } else I.src = I.hq ? 'hq' : '';
  impRender();
  const m = document.getElementById('imp-modal');
  m.hidden = false;
  const first = m.querySelector('#imp-body input:not([disabled]), #imp-body button') || document.getElementById('imp-cancel');
  if (first && first.focus) first.focus({ preventScroll: true });
  return true;
}
function impClose() {
  const m = document.getElementById('imp-modal'), o = IMP.I ? IMP.I.opener : null;
  m.hidden = true;
  IMP.I = null;
  if (o && o.focus && !o.disabled) { try { o.focus({ preventScroll: true }); } catch (e) { /* ignore */ } }
}
function impReject(key, args) {
  const msg = impTf.apply(null, [key].concat(args || []));
  if (IMP.I) { IMP.I.msg = msg; IMP.I.srcOpen = true; impRender(); }
  try { if (IMP.hooks.toast) IMP.hooks.toast(msg, 5000); } catch (e) { /* facultatif */ }
}
function impFile(file) {
  impReadJsonFile(file, r => {
    if (!IMP.I) return;
    if (r.reject) { impReject(r.reject); return; }
    const res = impReadAny(r.parsed, file.name);
    if (res.reject) { impReject(res.reject, res.args); return; }
    Object.assign(IMP.I, { file: res.src, src: 'file', srcOpen: false, msg: '', side: 'all', type: 'all', name: '' });
    impRender();
  });
}
/* Dès qu'une source est chargée, elle se replie en une ligne : la liste prend la place. Avant, « Choisir un fichier… » reste visible. */
function impFolded(I) { return !!impCur(I) && !I.srcOpen; }
function impSideText(c) { return c === 'red' ? impT('imp.red') : c === 'blue' ? impT('imp.blue') : c === 'neutrals' ? impT('imp.neutral') : String(c || ''); }
function impSideOptions(sel, withNone) {
  return (withNone ? [['red', impT('imp.red')], ['blue', impT('imp.blue')], ['', impT('imp.noside')]] : [['all', impT('imp.all')], ['red', impT('imp.red')], ['blue', impT('imp.blue')]])
    .map(x => '<option value="' + impEsc(x[0]) + '"' + (x[0] === sel ? ' selected' : '') + '>' + impEsc(x[1]) + '</option>').join('');
}
/* La liste « Camp des groupes » existe dès que la source chargée est un briefing (le briefing en cours, ou un fichier de briefing) */
function impSrcIsBriefing(I) { const c = impCur(I); return !!c && c.what === 'bg'; }
/* La liste se mesure à sa plus longue option (en caractères de sa police à chasse fixe, plus le cadre et la flèche) : le sélecteur remplacé par le module n'a pas de largeur propre */
function impBgSideHtml(I) {
  const n = ['imp.red', 'imp.blue', 'imp.noside'].reduce((m, k) => Math.max(m, impT(k).length), 0) + 2;
  return '<div class="imp-bgside"><label class="imp-lbl" for="imp-bg-side">' + impEsc(impT('imp.side.groups')) + '</label><span class="imp-bgsel" style="width: calc(' + n + 'ch + 52px)"><select class="imp-sel" id="imp-bg-side" aria-label="' + impEsc(impT('imp.side.groups')) + '">' + impSideOptions(I.bgSide, true) + '</select></span></div>';
}
function impSourceLabel(I) {
  if (I.src === 'hq') return impT('imp.src.hq');
  if (I.src === 'bg') return impT('imp.src.bg');
  return impT('imp.src.file') + (I.file && I.file.file ? ' · ' + I.file.file : '');
}
function impSourcesHtml(I) {
  if (impFolded(I)) {
    return '<div class="imp-block imp-srcline"><span>' + impEsc(impTf('imp.srcline', impSourceLabel(I))) + '</span> <button type="button" class="imp-link" data-act="imp-change-src">' + impEsc(impT('imp.change')) + '</button>'
      + (impSrcIsBriefing(I) ? impBgSideHtml(I) : '') + '</div>';
  }
  const row = (id, label, extra, disabled) => '<label class="imp-src' + (disabled ? ' off' : '') + '"><input type="radio" name="imp-src" value="' + id + '"' + (I.src === id ? ' checked' : '') + (disabled ? ' disabled' : '') + '><span>' + impEsc(label) + '</span></label>' + (extra || '');
  const hqNote = '<div class="imp-note">' + impEsc(I.hq ? impTf('imp.hq.ok', I.hq.file, I.hq.theatre) : impT('imp.hq.none')) + '</div>';
  const bgNote = '<div class="imp-note">' + impEsc(I.bg ? impTf('imp.bg.ok', I.bg.phases) : impT('imp.bg.none')) + '</div>' + (I.src === 'bg' && I.bg ? impBgSideHtml(I) : '');
  const filePick = '<div class="imp-file"><button type="button" class="imp-filebtn" data-act="imp-pick-file">' + impEsc(impT('imp.choose')) + '</button><span class="imp-filename">' + impEsc(I.file ? I.file.file : '') + '</span></div><div class="imp-note">' + impEsc(impT('imp.file.note')) + '</div>'
    + (I.msg ? '<div class="imp-note imp-warn" role="alert">⚠ ' + impEsc(I.msg) + '</div>' : '')
    + (I.src === 'file' && impSrcIsBriefing(I) ? impBgSideHtml(I) : '');
  return '<div class="imp-block imp-srcs"><h3>' + impEsc(impT('imp.src')) + '</h3>' + row('hq', impT('imp.src.hq'), hqNote, !I.hq) + row('bg', impT('imp.src.bg'), bgNote, !I.bg) + row('file', impT('imp.src.file'), filePick, false) + '</div>';
}
/* Les lignes affichées : camp, type, nom (casse et accents ignorés) */
function impShown(cur, I) {
  I = I || IMP.I;
  const q = impNorm(I.name.trim()), out = [];
  cur.rows.forEach((r, i) => {
    const coal = r.kind === 'bg' ? gsSide(I.bgSide) : r.coal;
    if ((I.side === 'all' || coal === I.side) && (I.type === 'all' || r.types.indexOf(I.type) >= 0) && (q === '' || impNorm(r.name === '' ? r.title || '' : r.name).indexOf(q) >= 0)) out.push(i);
  });
  return out;
}
/* Une ligne importe-t-elle quelque chose ? Un vol que le module ne gère pas (type hors liste, ou sans unité) n'apporte que sa route : sans route cochée et possible, il n'y a rien à importer */
function impRowGoes(r, routeOff) {
  if (!r.on || !r.ok) return false;
  if (r.kind === 'bg' || r.managed) return true;
  return !!(r.avail.route && r.chk.route && r.points && !routeOff);
}
function impRoutesOff() { const cur = impCur(); return !!(cur && impRouteOff(cur, gsRead())); }
/* L'état d'une ligne : nouveau, complète, ou ce qui la limite */
function impRowState(cur, r, g, I) {
  if (r.kind === 'bg') {
    if (r.noName) return impT('imp.noname');
    const hits = impFindGroups(g.flights, r.name, I.bgSide);
    const bits = [impT(hits.length === 1 ? 'imp.exists' : 'imp.new')];
    if (r.type === '') bits.push(r.aircraft ? impTf('imp.bg.type', r.aircraft) : impT('imp.bg.type0'));
    if (r.capped) bits.push(impTf('imp.bg.cap', r.capped));
    return bits.concat([impTf('imp.units', r.count)]).join(' · ');
  }
  if (!r.managed) return impT(r.noUnit ? 'imp.nounit' : 'imp.unmanaged') + ' · ' + impTf('imp.units', 0);
  return impT(impFindGroups(g.flights, r.name, r.coalition).length === 1 ? 'imp.exists' : 'imp.new') + ' · ' + impTf('imp.units', r.count);
}
function impRowHtml(cur, i, g, I, routeOff) {
  const r = cur.rows[i], state = impRowState(cur, r, g, I);
  const parts = IMP_PARTS.map(p => {
    const on = r.avail[p] && r.ok && !(p === 'route' && routeOff);
    return '<label class="imp-chk' + (on ? '' : ' off') + '"><input type="checkbox" data-imp-part="' + p + '" data-imp-i="' + i + '"' + (on && r.chk[p] ? ' checked' : '') + (on ? '' : ' disabled') + '>' + impEsc(impT('imp.part.' + p)) + '</label>';
  }).join('');
  return '<div class="imp-flight' + (r.ok ? '' : ' off') + '"><label class="imp-fh"><input type="checkbox" data-imp-flight="' + i + '"' + (r.on && r.ok ? ' checked' : '') + (r.ok ? '' : ' disabled') + '>'
    + '<span class="imp-nm">' + impEsc(r.name !== '' ? r.name : (r.title || '—')) + '</span>' + (r.types.length ? '<span class="imp-tag">' + impEsc(r.types.join(' + ')) + '</span>' : '')
    + '<span class="imp-n">' + impEsc(state) + '</span></label><div class="imp-parts">' + parts + '</div></div>';
}
function impListHtml(cur) {
  const I = IMP.I, shown = impShown(cur, I), g = gsRead() || { theatre: '', flights: [] }, routeOff = impRouteOff(cur, g.flights.length ? g : null);
  return shown.length ? shown.map(i => impRowHtml(cur, i, g, I, routeOff)).join('') : '<p class="imp-empty">' + impEsc(impT(cur.rows.length ? 'imp.nomatch' : 'imp.empty')) + '</p>';
}
function impCountText(cur) { return impTf('imp.count', impShown(cur).length, cur.rows.length); }
function impFlightsHtml(I, cur) {
  const g = gsRead() || { theatre: '', flights: [] };
  const other = impRouteOff(cur, g);
  const th = other ? impTf('imp.theatre.other', cur.theatre, g.theatre) : ((cur.theatre && (!g.theatre || !g.flights.length)) ? impTf('imp.theatre.set', cur.theatre) : '');
  const sides = [['all', impT('imp.all')], ['red', impT('imp.red')], ['blue', impT('imp.blue')]];
  if (cur.rows.some(r => r.coal === 'neutrals')) sides.push(['neutrals', impT('imp.neutral')]);
  const types = cur.rows.reduce((acc, r) => acc.concat(r.types), []).filter((v, i, a) => a.indexOf(v) === i).sort();
  const opt = (v, l, sel) => '<option value="' + impEsc(v) + '"' + (v === sel ? ' selected' : '') + '>' + impEsc(l) + '</option>';
  return (cur.skipped ? '<div class="imp-note top">⚠ ' + impEsc(impTf('rej.skip', cur.skipped)) + '</div>' : '')
    + '<div class="imp-filters"><div><label class="imp-lbl" for="imp-side">' + impEsc(impT('imp.side')) + '</label><select class="imp-sel" id="imp-side" aria-label="' + impEsc(impT('imp.side')) + '">' + sides.map(x => opt(x[0], x[1], I.side)).join('') + '</select></div>'
    + '<div><label class="imp-lbl" for="imp-type">' + impEsc(impT('imp.type')) + '</label><select class="imp-sel" id="imp-type" aria-label="' + impEsc(impT('imp.type')) + '">' + opt('all', impT('imp.all'), I.type) + types.map(x => opt(x, x, I.type)).join('') + '</select></div>'
    + '<div class="nm"><label class="imp-lbl" for="imp-name">' + impEsc(impT('imp.name')) + '</label><input class="imp-in" id="imp-name" type="text" autocomplete="off" autocapitalize="off" spellcheck="false" value="' + impEsc(I.name) + '"></div></div>'
    + '<div class="imp-bulk"><button type="button" class="imp-filebtn" data-act="imp-check-shown">' + impEsc(impT('imp.checkshown')) + '</button><button type="button" class="imp-filebtn" data-act="imp-uncheck-all">' + impEsc(impT('imp.uncheckall')) + '</button><span class="imp-cnt" id="imp-count" aria-live="polite">' + impEsc(impCountText(cur)) + '</span></div>'
    + '<div class="imp-list" id="imp-list">' + impListHtml(cur) + '</div>'
    + (th ? '<div class="imp-note top' + (other ? ' imp-warn' : '') + '" id="imp-theatre">' + impEsc(th) + '</div>' : '');
}
function impRender() {
  const I = IMP.I;
  if (!I) return;
  const cur = impCur(I);
  document.getElementById('imp-modal-title').textContent = impT('imp.title');
  document.getElementById('imp-modal-close').setAttribute('aria-label', impT('imp.close'));
  document.getElementById('imp-cancel').textContent = impT('imp.cancel');
  document.getElementById('imp-go').textContent = impT('imp.go');
  document.getElementById('imp-body').innerHTML = impSourcesHtml(I)
    + '<div class="imp-block imp-fls">' + (impFolded(I) ? '' : '<h3>' + impEsc(impT('imp.flights')) + '</h3>') + (cur ? impFlightsHtml(I, cur) : '<p class="imp-note top">' + impEsc(impT('imp.none')) + '</p>') + '</div>';
  impUpdateGo();
}
/* La liste et son compteur seuls : le champ Nom garde le focus, la liste garde sa position */
function impRenderList() {
  const cur = impCur(), list = document.getElementById('imp-list');
  if (!cur || !list) return;
  list.innerHTML = impListHtml(cur);
  document.getElementById('imp-count').textContent = impCountText(cur);
  impUpdateGo();
}
function impUpdateGo() {
  const cur = impCur(), go = document.getElementById('imp-go');
  if (go) { const off = impRoutesOff(); go.disabled = !(cur && cur.rows.some(r => impRowGoes(r, off))); }
}
/* « Cocher les groupes affichés » et « Tout décocher » agissent sur les lignes visibles après filtre ; une ligne grisée ne se coche pas */
function impSetShown(on) {
  const cur = impCur();
  if (!cur) return;
  impShown(cur).forEach(i => { if (cur.rows[i].ok) cur.rows[i].on = on; });
  impRenderList();
}
function impGo() {
  const I = IMP.I, cur = impCur(I);
  if (!I || !cur) return;
  const off = impRoutesOff();
  const picks = cur.rows.filter(r => impRowGoes(r, off));
  if (!picks.length) return;
  try { if (IMP.hooks.before) IMP.hooks.before(); } catch (e) { /* facultatif */ }
  const res = impWrite(cur, picks, I.bgSide);
  impClose();
  try { if (IMP.hooks.onImported) IMP.hooks.onImported(res); } catch (e) { /* le module dit ce qu'il veut */ }
}
"""


def build_block():
    """Le script du bloc, délimité par ses deux commentaires, terminé par un saut de ligne."""
    return BLOCK_BEGIN + _JS + BLOCK_END + '\n'


def build_css():
    """La feuille du bloc, délimitée par ses deux commentaires, terminée par un saut de ligne."""
    return CSS_BEGIN + _CSS + CSS_END + '\n'


def build_html():
    """La fenêtre du bloc et son sélecteur de fichier, délimités par deux commentaires, terminés par un saut de ligne."""
    return HTML_BEGIN + _HTML + HTML_END + '\n'


if __name__ == '__main__':
    print(f"[OK] bloc d'import : script {len(build_block())} caractères, feuille {len(build_css())}, fenêtre {len(build_html())}")
