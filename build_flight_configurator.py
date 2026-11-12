#!/usr/bin/env python3
"""Build the Flight Configurator HTML module : un vol (identité, radios, emport, livrée, route choisie au Route Planner ; un type par unité) exporté en paquet `dcs-flight-package-v2`.

Produit dist/dcs_flight_configurator.html (fichier autonome, hors-ligne, aucune requête réseau).
Usage : python3 -B build_flight_configurator.py

Blocs partagés insérés tels quels (identiques à l'octet dans les modules qui les utilisent) :
  radio_block.py    — noms des postes radio et numéros de canal du cockpit
  radio_bands_block.py — la bande de chaque poste (règle de Mission Tools) et les postes que la mission ne pré-règle pas (le poste HF des deux hélicoptères) ; le Datacard Generator, HQ et le Route Planner l'emploient aussi
  payload_block.py  — lecture d'un .lua de presets, pylônes et armes permis, `payload` d'un .miz ; il lit les constantes WEAPON_NAMES,
                      AIRCRAFT_PYLONS et AIRCRAFT_LIMITS, qui sont celles du Loadout Editor de Mission Tools
  group_store_block.py — la fiche des groupes partagée avec le Route Planner (flight_set_v1) : lecture, écriture groupe par groupe, migration
  import_block.py   — la fenêtre d'import commune au Route Planner (HQ, briefing en cours, fichier) : lit les sources et écrit dans la fiche ; le module en reçoit un rappel
  magvar_block.py, projection_block.py, route_pack_block.py — la déclinaison magnétique, les projections des théâtres de DCS (llToDcs, dcsToLl) et
                      packPoint (le point d'un paquet, le même texte qu'au Route Planner) : le bloc Route en tire les caps magnétiques, le croquis et les points
  bloc de coordonnées de navigation (COORD_BLOCK ci-dessous) — recopié octet pour octet du Route Planner et du Datacard Generator (empreinte COORD_SHA16) : legCalc, fmtHdg, parseDecl

Tables (data/, copiées à l'octet de Mission Tools ; pydcs 1.0.0, LGPL-3.0 ; les dessins de views/ sont de Goldwolf, hors licence du dépôt) :
elles sont recopiées dans la page entre des marqueurs `/* NOM:BEGIN */` et `/* NOM:END */`, et le build s'arrête si une copie diffère de son fichier.
"""

import hashlib
import json
import os
import re
import subprocess
import sys

from group_store_block import build_block as build_group_store_block
from import_block import build_block as build_import_block, build_css as build_import_css, build_html as build_import_html
from messages_block import build_block as build_messages_block, build_css as build_messages_css
from ui_block import build_block as build_ui_block, build_css as build_ui_css, verify as ui_verify, fingerprint as ui_fingerprint

CONTRAST_CSS = r"""
/* MP-20 begin */
/* Contrastes (texte sous 18 px, 4,5 : 1 au moins) : couleur du texte seule, la palette commune ne bouge pas. */
:where(body[data-theme="cw-nato"]) .tb-brand-short { color: #d5865c; }
:where(body[data-theme="cw-nato"]) .tb-sel { color: #c49037; }
:where(body[data-theme="cw-nato"]) #btn-open { color: #c49037; }
:where(body[data-theme="cw-nato"]) .fc-bh { color: #dcbe8a; }
:where(body[data-theme="cw-nato"]) .pk-x { color: #ab9e78; }
:where(body[data-theme="cw-nato"]) .ed-field label { color: #c79641; }
:where(body[data-theme="cw-nato"]) .fc-sub > summary { color: #c79641; }
:where(body[data-theme="cw-nato"]) .fc-sub .fc-sum { color: #ab9e78; }
:where(body[data-theme="cw-nato"]) .fc-lo-k { color: #c79641; }
:where(body[data-theme="cw-soviet"]) .fc-bh { color: #cc9f52; }
:where(body[data-theme="cw-soviet"]) .pk-x { color: #95a08a; }
:where(body[data-theme="cw-soviet"]) .ed-field label { color: #c6943d; }
:where(body[data-theme="cw-soviet"]) .fc-sub > summary { color: #c6943d; }
:where(body[data-theme="cw-soviet"]) .fc-sub .fc-sum { color: #95a08a; }
:where(body[data-theme="cw-soviet"]) .fc-lo-k { color: #c6943d; }
:where(body[data-theme="cw-soviet"]) .tb-label { color: #879279; }
:where(body[data-theme="cw-soviet"]) .fc-route.none { color: #788569; }
:where(body[data-theme="cw-soviet"]) .fc-post .fc-sum { color: #8f9a83; }
:where(body[data-theme="cw-soviet"]) .fc-band { color: #8f9a83; }
:where(body[data-theme="cw-soviet"]) .fc-ch > label { color: #8f9a83; }
:where(body[data-theme="cw-soviet"]) .cmp-credit { color: #808c72; }
:where(body[data-theme="cw-soviet"]) .cmp-st .n { color: #808c72; }
:where(body[data-theme="cw-soviet"]) .cmp-row > .sn { color: #79866b; }
:where(body[data-theme="cw-soviet"]) .cmp-sub { color: #79866b; }
:where(body[data-theme="cw-soviet"]) .cmp-tot { color: #79866b; }
:where(body[data-theme="modern-nato"]) .fc-bh { color: #c38f35; }
:where(body[data-theme="modern-nato"]) .pk-x { color: #8e9ca7; }
:where(body[data-theme="modern-nato"]) .ed-field label { color: #c49037; }
:where(body[data-theme="modern-nato"]) .fc-sub > summary { color: #c49037; }
:where(body[data-theme="modern-nato"]) .fc-sub .fc-sum { color: #8e9ca7; }
:where(body[data-theme="modern-nato"]) .fc-lo-k { color: #c49037; }
:where(body[data-theme="modern-nato"]) .fc-post .fc-sum { color: #8695a1; }
:where(body[data-theme="modern-nato"]) .fc-band { color: #8695a1; }
:where(body[data-theme="modern-nato"]) .fc-ch > label { color: #8695a1; }
:where(body[data-theme="modern-east"]) .fc-bh { color: #c6943d; }
:where(body[data-theme="modern-east"]) .pk-x { color: #989e8a; }
:where(body[data-theme="modern-east"]) .ed-field label { color: #c6943d; }
:where(body[data-theme="modern-east"]) .fc-sub > summary { color: #c6943d; }
:where(body[data-theme="modern-east"]) .fc-sub .fc-sum { color: #989e8a; }
:where(body[data-theme="modern-east"]) .fc-lo-k { color: #c6943d; }
:where(body[data-theme="modern-east"]) .tb-label { color: #888e78; }
:where(body[data-theme="modern-east"]) .fc-route.none { color: #7a8269; }
:where(body[data-theme="modern-east"]) .fc-post .fc-sum { color: #929884; }
:where(body[data-theme="modern-east"]) .fc-band { color: #929884; }
:where(body[data-theme="modern-east"]) .fc-ch > label { color: #929884; }
:where(body[data-theme="modern-east"]) .cmp-credit { color: #858b74; }
:where(body[data-theme="modern-east"]) .cmp-st .n { color: #858b74; }
:where(body[data-theme="modern-east"]) .cmp-row > .sn { color: #7d846c; }
:where(body[data-theme="modern-east"]) .cmp-sub { color: #7d846c; }
:where(body[data-theme="modern-east"]) .cmp-tot { color: #7d846c; }
:where(body[data-theme="cw-soviet"]) .rt-cm { color: #768367; }
:where(body[data-theme="modern-east"]) .rt-cm { color: #7a8269; }
/* lignes des menus de la barre (lot mp-ui-disposition-b) : le texte neutre des lignes « .dsp-opt » (Ouvrir) atteint 4,5 : 1 dans les quatre thèmes ; les thèmes cw-nato et modern-nato le tenaient déjà */
:where(body[data-theme="cw-soviet"]) .dsp-opt:not([aria-checked="true"]):not(:hover):not(:focus-visible):not([aria-selected="true"]):not([aria-disabled="true"]) { color: #879279; }
:where(body[data-theme="modern-east"]) .dsp-opt:not([aria-checked="true"]):not(:hover):not(:focus-visible):not([aria-selected="true"]):not([aria-disabled="true"]) { color: #888e78; }
/* MP-20 end */
"""
from magvar_block import build_block as build_magvar_block
from payload_block import build_block as build_payload_block
from projection_block import build_block as build_projection_block
from radio_bands_block import build_block as build_radio_bands_block
from radio_block import build_block as build_radio_block
from route_pack_block import build_block as build_route_pack_block
from route_theatre_block import build_block as build_route_theatre_block

HERE = os.path.dirname(os.path.abspath(__file__))
APP_VERSION = "0.1.2"

with open(os.path.join(HERE, 'assets.json')) as _f:
    A = json.load(_f)

# Le bloc de coordonnées de navigation, recopié OCTET POUR OCTET du Route Planner (qui le tient du Datacard Generator) : de « const NAV_R_KM » à « /* Nombre lisible d'un champ Cap » exclu,
# puis la fonction readNum. Le module n'en emploie que legCalc, fmtHdg et parseDecl ; l'empreinte (sha256, 16) est celle des trois pages, vérifiée par check().
# Il lit pad2, qui n'est pas dans le bloc : la page la pose avant lui, au même texte que le Route Planner et le Datacard Generator.
COORD_SHA16 = 'd7a32324179cee24'
PAD2_JS = "function pad2(n) { return String(n).padStart(2, '0'); }\n"
COORD_BLOCK = r"""const NAV_R_KM = 6371.0088;
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

# Les quatre tables : (nom de la constante, fichier de data/)
TABLES = [('WEAPON_NAMES', 'weapon_names.json'), ('AIRCRAFT_LIMITS', 'aircraft_limits.json'),
          ('AIRCRAFT_PYLONS', 'aircraft_pylons.json'), ('AIRCRAFT_VIEWS', 'aircraft_views.json'), ('LIVERIES_DEFAULT', 'liveries_default.json')]

# ---------- Textes (FR et EN : le build vérifie la parité et que chaque clé sert) ----------
I18N_FR = {
    'ui.cancel': 'Annuler',
    'ui.close': 'Fermer',
    'ui.restore': 'Restaurer',
    'ui.foldall': 'Tout replier',
    'ui.unfoldall': 'Tout déplier',
    'ui.fmt': 'Format',
    'ui.pages': 'Pages',
    'ui.fname': 'Nom du fichier',
    'ui.export': 'Exporter',
    'toolbar.subtitle': '░ PAQUET DE VOL',
    'toolbar.theme.tooltip': 'Thème graphique',
    'toolbar.lang.tooltip': 'Passer en anglais',

    'theme.cw-nato': 'Cold War OTAN',
    'theme.cw-soviet': 'Cold War Soviétique',
    'theme.modern-nato': 'OTAN moderne',
    'theme.modern-east': 'Bloc Est moderne',

    'tb.open': 'Ouvrir',
    'tb.open.tip': 'Ouvrir une configuration ou importer des groupes',
    'tb.save': 'Sauvegarder',
    'tb.save.tip': 'Sauvegarder le travail en cours (JSON : le paquet et les réglages du module)',
    'op.file': 'Ouvrir une configuration…',
    'op.file.h': '.json',
    'op.file.tip': 'Ouvrir un fichier de travail (JSON) : remplace le contenu du module',
    'op.import': 'Importer des groupes…',
    'op.import.h': 'briefing, HQ, paquet',
    'op.import.tip': 'Importer des groupes, des routes, des radios, des emports depuis la mission chargée dans HQ ou un paquet de vol',
    'tb.export': 'Exporter',
    'tb.export.tip': 'Exporter le paquet de vol pour le Mission Commander',
    'tb.clear': 'Effacer',
    'tb.clear.tip': 'Effacer',
    'tb.example': 'Exemple',
    'tb.example.tip': 'Ouvrir l\u2019exemple : deux groupes (deux Mi-24P, deux Mi-8MT) ; le travail en cours se restaure en un geste',
    'toast.example': 'Exemple chargé',
    'ex.group': 'EXEMPLE',

    'bar.ok': 'Prêt à exporter : {0}',
    'bar.clamped': '{0} réglage(s) d’emport ramené(s) à la limite de l’appareil.',
    'bar.bad.freq': 'Export impossible : {0} fréquence(s) à corriger dans les radios.',
    'bar.theatre.conflict': "Export impossible : les groupes sont sur {0}, Mission Plan sur {1} (voir le bandeau).",
    'bar.route.theatre': "Export impossible : la route du groupe {0} est sur {1}, Mission Plan sur {2}.",
    'bar.no.flight': 'Export impossible : ajoutez au moins un groupe.',
    'bar.no.name': 'Export impossible : le groupe {0} n’a pas de nom.',
    'bar.dup': 'Noms en double : {0}',

    'tb.theatre': 'Théâtre',
    'tc.banner': "Les groupes sont sur {0} ; le théâtre de Mission Plan est {1}.",
    'tc.back': "Repasser sur {0}",
    'tc.keep': "Garder {0}, retirer les routes des groupes",

    'sec.flights': 'GROUPES',
    'sec.cmp': 'EMPORT',
    'sec.presets': 'MES PRESETS',

    'fl.title': 'Groupe {0}',
    'fl.add': '+ Ajouter un groupe',
    'fl.fold': 'Replier le groupe',
    'fl.unfold': 'Déplier le groupe',
    'fl.foldall': 'Tout replier',
    'fl.unfoldall': 'Tout déplier',
    'fl.remove': 'Retirer ce groupe',
    'fl.empty': 'Aucun groupe. Ajoutez-en un, ou importez-en depuis la barre du haut.',
    'fl.nounit': 'Aucune unité',
    'cmp.nounit': 'Ajoutez une unité à ce groupe : ses radios, son emport et sa route se règlent ici.',
    'fl.name': 'Nom du groupe',
    'fl.name.ph': 'Hind 1',
    'u.type': 'Type',
    'fl.coalition': 'Coalition',
    'fl.coalition.any': '— non renseignée —',
    'fl.coalition.blue': 'Bleue (OTAN)',
    'fl.coalition.red': 'Rouge',
    'fl.units.one': '{0} unité',
    'fl.units.many': '{0} unités',

    'sec.route': 'ROUTE',
    'route.none': 'Aucune route.',
    'route.line': 'Route : {0} — {1}, {2}',
    'route.line.nod': 'Route : {0} — {1}',
    'route.pts.one': '{0} point',
    'route.pts.many': '{0} points',
    'route.imported': 'Route importée',
    'route.unnamed': 'Route sans nom',
    'route.from.rp': 'du Route Planner',
    'route.from.pkg': 'importée avec le groupe',
    'route.change': 'Changer de route',
    'route.remove': 'Retirer',
    'route.see': 'Voir la route ↓',
    'route.pick': 'Choisir la route ↓',
    'route.choose.none': 'Aucune route pour ce groupe. Touche une route du Route Planner pour la donner au groupe.',
    'route.choose.other': 'Choisir une autre route pour ce groupe.',
    'route.keep': 'Garder la route actuelle',
    'route.list.linked': 'Liées à ce groupe',
    'route.list.other': 'Autres routes',
    'route.tag.linked': 'liée à {0}',
    'route.tag.free': 'sans groupe',
    'route.empty': 'Le Route Planner n’a aucune route : trace-la d’abord là-bas.',
    'route.th.nosupport': 'Les routes du Route Planner sont sur {0}, un théâtre que ce module ne gère pas.',
    'route.nosketch': 'Choisissez un théâtre pour voir la route.',
    'route.sketch': 'Croquis de la route {0}',
    'route.col.leg': 'Branche',
    'route.col.hdg': 'Cap M',
    'route.col.dist': 'Distance',
    'route.total': 'Total',
    'route.note': 'Cap magnétique : déclinaison {0} ({1}) — le même calcul que le Route Planner et le Datacard Generator. Le croquis n’est qu’un rappel : la route se trace au Route Planner.',
    'route.decl.to': ' à ',
    'route.src.mission': 'date de la mission',
    'route.src.route': 'date du paquet',
    'route.src.rp': 'année du Route Planner',
    'route.src.default': 'année par défaut',
    'route.src.manual': 'saisie au Route Planner',
    'route.gone': 'Cette route n’est plus au Route Planner : la dernière copie est gardée.',
    'route.few': 'Cette route n’a plus de points au Route Planner : la dernière copie est gardée.',
    'route.theatre.other': 'La route liée est sur {0}, Mission Plan sur {1} : la route n’est pas reprise.',
    'route.norp': 'Le Route Planner n’a pas encore été ouvert ici : la route n’est pas reprise.',
    'route.noid': 'Ouvre le Route Planner une fois pour pouvoir choisir ces routes (il leur donne un identifiant).',
    'route.toast.one': 'Route « {0} » reprise du Route Planner pour {1}.',
    'toast.saveFail': '⚠ Enregistrement local impossible (espace plein)',
    'toast.gsFull': '⚠ Stockage du navigateur plein : vos groupes ne sont pas enregistrés. Sauvegardez un fichier de travail.',
    'route.toast.many': 'Routes reprises du Route Planner : {0}.',

    'u.title': 'Unité {0}',
    'u.fold': 'Replier l’unité',
    'u.unfold': 'Déplier l’unité',
    'u.add': '+ Ajouter une unité ({0}/4)',
    'u.type.confirm.title': 'Changer le type de {0} ?',
    'u.type.confirm.text': 'Ses radios et son emport seront effacés.',
    'u.remove': 'Retirer cette unité',
    'u.name': 'Nom',
    'u.callsign': 'Indicatif',
    'u.onboard': 'N° de bord',
    'u.livery': 'Livrée',
    'u.livery.keep': 'Inchangée (celle de la mission)',
    'u.opt': 'facultatif',
    'u.radios': 'Radios',
    'u.radios.sum': '{0} postes',
    'u.radios.set': '{0} canaux réglés',
    'u.loadout': 'Emport',
    'u.loadout.none': 'non renseigné — HQ n’y touchera pas',
    'u.see': 'Voir l’emport ↓',

    'rad.chans': '{0} canaux',
    'rad.ch': 'CH {0}',
    'rad.hint': 'Fréquences en MHz, dans la bande de chaque poste (virgule ou point). Les modulations ne sont pas écrites. Un canal vide n’est pas écrit.',
    'rad.err.nan': 'Canal {0} : « {1} » n’est pas une fréquence.',
    'rad.err.range': 'Canal {0} : {1} MHz hors de la bande du poste ({2}).',
    'rad.freq': 'Fréquence {0}',
    'rad.err.nan.f': 'Fréquence {0} : « {1} » n’est pas une fréquence.',
    'rad.err.range.f': 'Fréquence {0} : {1} MHz hors de la bande du poste ({2}).',
    'rad.bad.n': '{0} hors bande',
    'rad.err.more': ' (+ {0} autre(s))',
    'rad.copy': 'Recopier sur les autres unités du groupe',

    'cmp.for': '{0} · {1}',
    'cmp.from': 'Partir de',
    'cmp.from.none': '— non renseigné —',
    'cmp.from.empty': 'Vide (poser des armes)',
    'cmp.from.imp': 'Emport importé',
    'cmp.from.units': 'Unités du module',
    'cmp.from.copy': 'Copier : {0} · {1}',
    'cmp.copied': 'copié de {0}',
    'cmp.emptyNote': 'Emport vide créé : HQ posera ces réglages sans arme',
    'cmp.none': '— vide —',
    'cmp.offTable': '(hors table)',
    'cmp.sym': 'Symétrique',
    'cmp.mass': 'Masse des emports :',

    'lo.pylon': 'Station {0}',

    'cmp.credit': 'Illustration : Goldwolf, DCS Reference Guide — avec son accord',
    'cmp.mirror': '↔ station jumelle : {0}',
    'cmp.noMirror': '↔ pas d\'équivalent sur la station jumelle {0}',
    'cmp.back': '↑ Retour à l’unité',
    'cmp.note': 'Un réglage d’arme (code laser, fusée…) suit sa station tant que l’arme n’est pas changée. Une valeur hors limites est ramenée à la limite de l’appareil (0 ou son maximum).',
    'cmp.noview': 'Pas de vue de face pour ce type : la liste des stations.',
    'cmp.pick': 'Choisissez un groupe et une unité : l’emport se compose ici.',
    'cmp.mod': 'modifié',
    'cmp.custom': 'Emport composé',
    'cmp.settings': 'réglages',
    'cmp.save': 'Garder dans mes presets…',
    'cmp.save.name': 'Nom du preset',
    'cmp.save.go': 'Enregistrer',
    'cmp.save.cancel': 'Annuler',
    'cmp.save.ph': 'Patrouille AT',
    'cmp.save.err.name': 'Donnez un nom au preset.',
    'cmp.save.err.dup': 'Un preset de ce nom existe déjà pour le {0}.',
    'cmp.save.err.none': 'Aucune arme posée : rien à enregistrer.',
    'cmp.save.ok': 'Preset « {0} » gardé dans « mes presets ».',
    'cmp.clear': 'Vider l’emport',

    'lo.fuel': 'Carburant (kg)',
    'lo.flare': 'Leurres',
    'lo.chaff': 'Paillettes',
    'lo.gun': 'Canon (%)',
    'lo.max': 'max {0}',
    'lo.pct': '{0} %',
    'lo.fuelbar': 'Carburant (%)',
    'lo.imported': 'emport importé',
    'lo.src.mine': 'mes presets',
    'lo.src.imp': 'import',
    'lo.src.copy': 'copie',

    'w.left': '(gauche)',
    'w.right': '(droite)',

    'pr.err': '{0} : illisible — ligne {1} ({2})',
    'pr.mine': 'Mes presets ({0})',
    'pr.load': 'Charger des presets (.lua)',
    'pr.none': 'Aucun preset. Composez un emport et gardez-le sous un nom, ou chargez un fichier .lua.',
    'pr.unsup': '{0} : appareil « {1} » non géré.',
    'pr.added': '{0} preset(s) ajouté(s) à mes presets.',
    'pr.report': '{0} preset(s) ajouté(s)',
    'pr.skipped': '{0} ignoré(s) : nom déjà pris',
    'pr.delete': 'Retirer',

    'err.code.unterminated-comment': 'commentaire non fermé',
    'err.code.unterminated-string': 'chaîne non fermée',
    'err.code.unexpected-character': 'caractère inattendu',
    'err.code.unexpected-eof': 'fin de fichier inattendue',
    'err.code.unexpected-token': 'élément inattendu',
    'err.code.bad-structure': 'structure inattendue',

    'sum.route': 'route {0} pts',
    'sum.radios': 'radios {0} canaux',
    'sum.radios.var': 'radios variées',
    'sum.loadout': 'emport {0}',
    'sum.loadout.custom': 'emport composé',
    'sum.loadout.var': 'emports variés',
    'sum.livery': 'livrée {0}',
    'sum.livery.var': 'livrées variées',
    'sum.type.pick': 'type à choisir',
    'u.type.pick': '— à choisir —',
    'u.notype': 'Choisissez le type de l’appareil pour régler ses radios, son emport et sa livrée.',
    'bar.no.type': 'Export impossible : choisissez le type de chaque appareil ({0}, unité {1}).',

    'msg.jsonUnreadable': '⚠ Fichier illisible : ce n’est pas du JSON.',
    'msg.formatUnsupported': '⚠ Format « {0} » non pris en charge ici (attendu : {1}).',
    'fmt.work': 'fichier de travail',
    'fmt.pkg': 'paquet de vol',
    'rej.unknown': 'inconnu',
    'bar.start': 'Pour commencer : ajoutez un groupe.',
    'open.theatre.set': 'Théâtre de Mission Plan : {0}',
    'open.theatre.unknown': "Ce fichier est sur un théâtre que Mission Plan ne connaît pas ({0}) : il n’est pas ouvert.",
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
    'open.done': 'Fichier ouvert : {0} groupe(s).',
    'open.ignored': '{0} groupe(s) non géré(s) ignoré(s).',

    'clear.confirm.title': 'Effacer le module ?',
    'clear.confirm.text': 'Les groupes, la route et l’emport en cours seront effacés ; vos presets restent. Cela ne se défait pas.',
    'fl.remove.confirm.title': 'Retirer le groupe « {0} » ?',
    'fl.remove.confirm.text': 'Ce groupe est partagé avec le Route Planner et le Datacard Generator : il sera retiré de tous les modules.',
    'ui.verb.clear': 'Effacer',
    'ui.verb.change': 'Changer',
    'ui.verb.remove': 'Retirer',

    'save.done': 'Travail sauvegardé : {0}',
    'fn.label': 'Nom du fichier',
    'fn.cancel': 'Annuler',
    'fn.close': 'Fermer',
    'fn.save.title': 'Sauvegarder le travail',
    'fn.save.go': 'Sauvegarder',
    'fn.export.title': 'Exporter le paquet',
    'fn.export.go': 'Exporter',

    'export.done': 'Paquet exporté : {0}',
}

I18N_EN = {
    'ui.cancel': 'Cancel',
    'ui.close': 'Close',
    'ui.restore': 'Restore',
    'ui.foldall': 'Fold all',
    'ui.unfoldall': 'Unfold all',
    'ui.fmt': 'Format',
    'ui.pages': 'Pages',
    'ui.fname': 'File name',
    'ui.export': 'Export',
    'toolbar.subtitle': '░ FLIGHT PACKAGE',
    'toolbar.theme.tooltip': 'Graphic theme',
    'toolbar.lang.tooltip': 'Switch to French',

    'theme.cw-nato': 'Cold War NATO',
    'theme.cw-soviet': 'Cold War Soviet',
    'theme.modern-nato': 'Modern NATO',
    'theme.modern-east': 'Modern Eastern Bloc',

    'tb.open': 'Open',
    'tb.open.tip': 'Open a configuration or import groups',
    'tb.save': 'Save',
    'tb.save.tip': 'Save the work in progress (JSON: the package and the module settings)',
    'op.file': 'Open a configuration…',
    'op.file.h': '.json',
    'op.file.tip': 'Open a working file (JSON): replaces the module content',
    'op.import': 'Import groups…',
    'op.import.h': 'briefing, HQ, package',
    'op.import.tip': 'Import groups, routes, radios, loadouts from the mission loaded in HQ or a flight package',
    'tb.export': 'Export',
    'tb.export.tip': 'Export the flight package for the Mission Commander',
    'tb.clear': 'Clear',
    'tb.clear.tip': 'Clear',
    'tb.example': 'Example',
    'tb.example.tip': 'Open the example: two groups (two Mi-24P, two Mi-8MT); the work in progress comes back in one tap',
    'toast.example': 'Example loaded',
    'ex.group': 'EXAMPLE',

    'bar.ok': 'Ready to export: {0}',
    'bar.clamped': '{0} loadout setting(s) brought back to the aircraft limit.',
    'bar.bad.freq': 'Cannot export: {0} frequency(ies) to fix in the radios.',
    'bar.theatre.conflict': "Cannot export: the groups are on {0}, Mission Plan on {1} (see the banner).",
    'bar.route.theatre': "Cannot export: group {0}'s route is on {1}, Mission Plan on {2}.",
    'bar.no.flight': 'Cannot export: add at least one group.',
    'bar.no.name': 'Cannot export: group {0} has no name.',
    'bar.dup': 'Duplicate names: {0}',

    'tb.theatre': 'Theatre',
    'tc.banner': "The groups are on {0}; Mission Plan's theatre is {1}.",
    'tc.back': "Back to {0}",
    'tc.keep': "Keep {0}, remove the groups' routes",

    'sec.flights': 'GROUPS',
    'sec.cmp': 'LOADOUT',
    'sec.presets': 'MY PRESETS',

    'fl.title': 'Group {0}',
    'fl.add': '+ Add a group',
    'fl.fold': 'Fold the group',
    'fl.unfold': 'Unfold the group',
    'fl.foldall': 'Fold all',
    'fl.unfoldall': 'Unfold all',
    'fl.remove': 'Remove this group',
    'fl.empty': 'No group. Add one, or import some from the top bar.',
    'fl.nounit': 'No unit',
    'cmp.nounit': 'Add a unit to this group: its radios, loadout and route are set here.',
    'fl.name': 'Group name',
    'fl.name.ph': 'Hind 1',
    'u.type': 'Type',
    'fl.coalition': 'Coalition',
    'fl.coalition.any': '— not set —',
    'fl.coalition.blue': 'Blue (NATO)',
    'fl.coalition.red': 'Red',
    'fl.units.one': '{0} unit',
    'fl.units.many': '{0} units',

    'sec.route': 'ROUTE',
    'route.none': 'No route.',
    'route.line': 'Route: {0} — {1}, {2}',
    'route.line.nod': 'Route: {0} — {1}',
    'route.pts.one': '{0} point',
    'route.pts.many': '{0} points',
    'route.imported': 'Imported route',
    'route.unnamed': 'Unnamed route',
    'route.from.rp': 'from the Route Planner',
    'route.from.pkg': 'imported with the group',
    'route.change': 'Change route',
    'route.remove': 'Remove',
    'route.see': 'See the route ↓',
    'route.pick': 'Choose the route ↓',
    'route.choose.none': 'No route for this group. Tap a Route Planner route to give it to the group.',
    'route.choose.other': 'Choose another route for this group.',
    'route.keep': 'Keep the current route',
    'route.list.linked': 'Linked to this group',
    'route.list.other': 'Other routes',
    'route.tag.linked': 'linked to {0}',
    'route.tag.free': 'no group',
    'route.empty': 'The Route Planner has no route: draw it there first.',
    'route.th.nosupport': 'The Route Planner routes are on {0}, a theatre this module does not handle.',
    'route.nosketch': 'Choose a theatre to see the route.',
    'route.sketch': 'Sketch of route {0}',
    'route.col.leg': 'Leg',
    'route.col.hdg': 'Mag hdg',
    'route.col.dist': 'Distance',
    'route.total': 'Total',
    'route.note': 'Magnetic heading: variation {0} ({1}) — the same calculation as the Route Planner and the Datacard Generator. The sketch is only a reminder: the route is drawn in the Route Planner.',
    'route.decl.to': ' to ',
    'route.src.mission': 'mission date',
    'route.src.route': 'package date',
    'route.src.rp': 'Route Planner year',
    'route.src.default': 'default year',
    'route.src.manual': 'typed in the Route Planner',
    'route.gone': 'This route is no longer in the Route Planner: the last copy is kept.',
    'route.few': 'This route no longer has points in the Route Planner: the last copy is kept.',
    'route.theatre.other': 'The linked route is on {0}, Mission Plan on {1}: the route is not followed.',
    'route.norp': 'The Route Planner has not been opened here yet: the route is not followed.',
    'route.noid': 'Open the Route Planner once to be able to pick these routes (it gives them an identifier).',
    'route.toast.one': 'Route “{0}” updated from the Route Planner for {1}.',
    'toast.saveFail': '⚠ Cannot save locally (storage full)',
    'toast.gsFull': '⚠ Browser storage full: your groups are not saved. Save a work file.',
    'route.toast.many': 'Routes updated from the Route Planner: {0}.',

    'u.title': 'Unit {0}',
    'u.fold': 'Fold the unit',
    'u.unfold': 'Unfold the unit',
    'u.add': '+ Add a unit ({0}/4)',
    'u.type.confirm.title': 'Change the type of {0}?',
    'u.type.confirm.text': 'Its radios and loadout will be erased.',
    'u.remove': 'Remove this unit',
    'u.name': 'Name',
    'u.callsign': 'Callsign',
    'u.onboard': 'Onboard no.',
    'u.livery': 'Livery',
    'u.livery.keep': 'Unchanged (the mission’s)',
    'u.opt': 'optional',
    'u.radios': 'Radios',
    'u.radios.sum': '{0} radios',
    'u.radios.set': '{0} channels set',
    'u.loadout': 'Loadout',
    'u.loadout.none': 'not set — HQ will not touch it',
    'u.see': 'See the loadout ↓',

    'rad.chans': '{0} channels',
    'rad.ch': 'CH {0}',
    'rad.hint': 'Frequencies in MHz, within each radio’s band (comma or dot). Modulations are not written. An empty channel is not written.',
    'rad.err.nan': 'Channel {0}: “{1}” is not a frequency.',
    'rad.err.range': 'Channel {0}: {1} MHz is outside the radio’s band ({2}).',
    'rad.freq': 'Frequency {0}',
    'rad.err.nan.f': 'Frequency {0}: “{1}” is not a frequency.',
    'rad.err.range.f': 'Frequency {0}: {1} MHz is outside the radio’s band ({2}).',
    'rad.bad.n': '{0} out of band',
    'rad.err.more': ' (+ {0} more)',
    'rad.copy': 'Copy to the other units of the group',

    'cmp.for': '{0} · {1}',
    'cmp.from': 'Start from',
    'cmp.from.none': '— not set —',
    'cmp.from.empty': 'Empty (place weapons)',
    'cmp.from.imp': 'Imported loadout',
    'cmp.from.units': 'Module units',
    'cmp.from.copy': 'Copy: {0} · {1}',
    'cmp.copied': 'copied from {0}',
    'cmp.emptyNote': 'Empty loadout created: HQ will set these values with no weapon',
    'cmp.none': '— empty —',
    'cmp.offTable': '(not in table)',
    'cmp.sym': 'Symmetric',
    'cmp.mass': 'Loadout weight:',

    'lo.pylon': 'Station {0}',

    'cmp.credit': 'Illustration: Goldwolf, DCS Reference Guide — used with permission',
    'cmp.mirror': '↔ twin station: {0}',
    'cmp.noMirror': '↔ no equivalent on twin station {0}',
    'cmp.back': '↑ Back to the unit',
    'cmp.note': 'A weapon setting (laser code, fuze…) follows its station as long as the weapon is not changed. A loadout setting out of range is brought back to the aircraft limit (0 or its maximum).',
    'cmp.noview': 'No front view for this type: the station list.',
    'cmp.pick': 'Pick a group and a unit: the loadout is composed here.',
    'cmp.mod': 'modified',
    'cmp.custom': 'Composed loadout',
    'cmp.settings': 'settings',
    'cmp.save': 'Keep in my presets…',
    'cmp.save.name': 'Preset name',
    'cmp.save.go': 'Save',
    'cmp.save.cancel': 'Cancel',
    'cmp.save.ph': 'AT patrol',
    'cmp.save.err.name': 'Give the preset a name.',
    'cmp.save.err.dup': 'A preset with this name already exists for the {0}.',
    'cmp.save.err.none': 'No weapon placed: nothing to save.',
    'cmp.save.ok': 'Preset “{0}” kept in “my presets”.',
    'cmp.clear': 'Empty the loadout',

    'lo.fuel': 'Fuel (kg)',
    'lo.flare': 'Flares',
    'lo.chaff': 'Chaff',
    'lo.gun': 'Gun (%)',
    'lo.max': 'max {0}',
    'lo.pct': '{0}%',
    'lo.fuelbar': 'Fuel (%)',
    'lo.imported': 'imported loadout',
    'lo.src.mine': 'my presets',
    'lo.src.imp': 'import',
    'lo.src.copy': 'copy',

    'w.left': '(left)',
    'w.right': '(right)',

    'pr.err': '{0}: unreadable — line {1} ({2})',
    'pr.mine': 'My presets ({0})',
    'pr.load': 'Load presets (.lua)',
    'pr.none': 'No preset. Compose a loadout and keep it under a name, or load a .lua file.',
    'pr.unsup': '{0}: aircraft “{1}” not handled.',
    'pr.added': '{0} preset(s) added to my presets.',
    'pr.report': '{0} preset(s) added',
    'pr.skipped': '{0} skipped: name already taken',
    'pr.delete': 'Remove',

    'err.code.unterminated-comment': 'unclosed comment',
    'err.code.unterminated-string': 'unclosed string',
    'err.code.unexpected-character': 'unexpected character',
    'err.code.unexpected-eof': 'unexpected end of file',
    'err.code.unexpected-token': 'unexpected token',
    'err.code.bad-structure': 'unexpected structure',

    'sum.route': 'route {0} pts',
    'sum.radios': 'radios {0} channels',
    'sum.radios.var': 'radios vary',
    'sum.loadout': 'loadout {0}',
    'sum.loadout.custom': 'composed loadout',
    'sum.loadout.var': 'loadouts vary',
    'sum.livery': 'livery {0}',
    'sum.livery.var': 'liveries vary',
    'sum.type.pick': 'type to pick',
    'u.type.pick': '— to pick —',
    'u.notype': 'Pick the aircraft type to set its radios, loadout and livery.',
    'bar.no.type': 'Cannot export: pick each aircraft’s type ({0}, unit {1}).',

    'msg.jsonUnreadable': '⚠ Unreadable file: this is not JSON.',
    'msg.formatUnsupported': '⚠ Format “{0}” is not supported here (expected: {1}).',
    'fmt.work': 'work file',
    'fmt.pkg': 'flight package',
    'rej.unknown': 'unknown',
    'bar.start': 'To start: add a group.',
    'open.theatre.set': 'Mission Plan theatre: {0}',
    'open.theatre.unknown': "This file is on a theatre Mission Plan does not know ({0}): it is not opened.",
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
    'open.done': 'File opened: {0} group(s).',
    'open.ignored': '{0} unhandled group(s) ignored.',

    'clear.confirm.title': 'Clear the module?',
    'clear.confirm.text': 'The groups, route and loadouts in progress will be erased; your presets stay. This cannot be undone.',
    'fl.remove.confirm.title': 'Remove the group “{0}”?',
    'fl.remove.confirm.text': 'This group is shared with the Route Planner and the Datacard Generator: it will be removed from all modules.',
    'ui.verb.clear': 'Clear',
    'ui.verb.change': 'Change',
    'ui.verb.remove': 'Remove',

    'save.done': 'Work saved: {0}',
    'fn.label': 'File name',
    'fn.cancel': 'Cancel',
    'fn.close': 'Close',
    'fn.save.title': 'Save the work',
    'fn.save.go': 'Save',
    'fn.export.title': 'Export the package',
    'fn.export.go': 'Export',

    'export.done': 'Package exported: {0}',
}

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
  --rust: #5e1414;
  --red-stamp: #841e1e; --red-faded: #a04040;
}
body[data-theme="modern-nato"] {
  --paper: #e8e3d8; --paper-light: #f0ece2; --paper-dark: #c8c0b0;
  --ink: #15181c; --ink-faded: #3a4048;
  --olive: #2a3038; --olive-dark: #1c2026; --olive-deep: #0e1014;
  --khaki: #5c6b7a; --khaki-light: #7a8a98;
  --rust: #2a2a2a;
  --red-stamp: #1a1a1a; --red-faded: #4a4a4a;
}
body[data-theme="modern-east"] {
  --paper: #cdc6b8; --paper-light: #ddd6c8; --paper-dark: #ada69a;
  --ink: #1a1610; --ink-faded: #3d3024;
  --olive: #3d3024; --olive-dark: #2a2018; --olive-deep: #1a140e;
  --khaki: #4a5238; --khaki-light: #6a7256;
  --rust: #5a1a1a;
  --red-stamp: #7a2424; --red-faded: #a04040;
}

* { box-sizing: border-box; margin: 0; padding: 0; }
html, body { height: 100%; overscroll-behavior: none; }
button, input, select, textarea { font: inherit; cursor: pointer; }

body {
  font-family: var(--f-typewriter);
  background: var(--olive-deep);
  color: var(--paper);
  font-size: 13px;
  line-height: 1.5;
  -webkit-tap-highlight-color: transparent;
  -webkit-text-size-adjust: 100%;
}

/* ======== TOOLBAR ======== */
.toolbar {
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
}
.tb-select option { background-color: var(--olive-dark); color: var(--paper); }
/* Le théâtre dans la barre : le libellé et la liste, mêmes règles qu'au Route Planner et au Datacard Generator (.tb-label, .tb-sel) */
.tb-label { font-family: var(--f-ui); font-size: 10px; font-weight: 500; letter-spacing: 1.5px; color: var(--khaki-light); text-transform: uppercase; flex: none; margin-left: 4px; white-space: nowrap; }
.tb-sel {
  font-family: var(--f-ui); font-weight: 700; letter-spacing: 1.5px; font-size: 12px; text-transform: uppercase;
  color: var(--amber); border: 1px solid var(--amber-dark); height: 40px; min-width: 44px;
  padding: 0 30px 0 12px; cursor: pointer; display: inline-flex; align-items: center; justify-content: center; gap: 6px; flex: none; appearance: none; -webkit-appearance: none;
  background: var(--olive-dark) url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='6'%3E%3Cpath d='M1 1l4 4 4-4' fill='none' stroke='%23c0892a' stroke-width='1.5'/%3E%3C/svg%3E") no-repeat right 11px center;
}
.tb-sel:hover, .tb-sel:focus-visible { border-color: var(--amber); }
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
  position: fixed; z-index: 5000; min-width: 180px; max-width: min(340px, calc(100vw - 16px));
  max-height: min(62vh, 440px); overflow-y: auto; overscroll-behavior: contain;
  background: linear-gradient(180deg, var(--olive-dark) 0%, var(--olive-deep) 100%);
  border: 1px solid var(--amber-dark); border-top: 3px solid var(--amber);
  box-shadow: 0 12px 28px rgba(0,0,0,.55), 0 2px 0 rgba(0,0,0,.35);
  padding: 4px 0; margin: 0; list-style: none; scrollbar-width: thin; scrollbar-color: var(--amber-dark) transparent;
  transform-origin: top left; animation: tbm-in .12s ease-out;
}
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
  font-family: var(--f-typewriter); font-weight: 400; font-size: 13px; letter-spacing: .2px; text-transform: none;
}
.tbm-panel.tbm-p-field .tbm-opt[aria-selected="true"] { font-weight: 400; }
.tbm-panel .tbm-group { margin-top: 2px; border-top: 1px solid rgba(168,154,114,.25); }
.fc-lo-line:empty { display: none; }
.tbm-panel.tbm-up { border-top: 1px solid var(--amber-dark); border-bottom: 3px solid var(--amber); transform-origin: bottom left; }

/* ---------- le menu « Ouvrir » (lot mp-ui-disposition-b) : le bouton de la barre et son panneau, au style des listes de la barre (tbm-*) ---------- */
#btn-open { position: relative; color: var(--amber); border-color: var(--amber-dark); padding-right: 12px; }
#btn-open:hover, #btn-open:focus-visible, #btn-open.dsp-open { border-color: var(--amber); }
#btn-open .dsp-chev { width: 10px; height: 6px; }
#btn-open.dsp-open .dsp-chev { transform: rotate(180deg); }
.dsp-panel { max-height: min(80vh, 600px); min-width: 260px; padding-bottom: 6px; }
.mn-hint { margin-left: auto; padding-left: 14px; flex: 0 1 auto; min-width: 0; text-align: right; }
/* rien de coupé : le menu s'élargit à son contenu, dans la largeur de la vue ; au-delà, l'indice passe à la ligne */
.tbm-panel.mn-panel { max-width: min(560px, calc(100vw - 16px)); }
.mn-panel .tbm-opt .tbm-txt { flex: 0 0 auto; overflow: visible; text-overflow: clip; }
.mn-opt[aria-disabled="true"] { color: var(--khaki-light); cursor: not-allowed; opacity: .7; }
.mn-opt[aria-disabled="true"]:hover { background: none; color: var(--khaki-light); }
.dsp-opt { outline: none; color: var(--khaki-light); }
.dsp-opt:focus-visible { background: var(--olive); color: var(--amber); }
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
}
/* bouton de la barre : icône seule (le module y ajoute le libellé) */
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
@media (max-width: 479px) {
  .toolbar { gap: 6px; padding-left: max(8px, env(safe-area-inset-left)); padding-right: max(8px, env(safe-area-inset-right)); }
  .tb-brand { min-width: 0; }
  .tb-brand-sub, .tb-sep { display: none; }
  .tb-brand-main { font-size: 13px; letter-spacing: 2px; }
  .tb-btn { width: 36px; }
  .tb-select { font-size: 11px; letter-spacing: .5px; padding: 0 22px 0 8px; background-position: right 6px center; }
  .tb-select.tbm-trigger { min-width: 0; flex: 0 1 auto; }
  .tb-lang-btn { min-width: 36px; padding: 0 4px; }
}

/* ======== MAIN LAYOUT ======== */
.app {
  position: fixed;
  top: 60px; bottom: 0; left: 0; right: 0;
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

/* FIELDS */
.ed-field { display: flex; flex-direction: column; gap: 5px; }
.ed-field label {
  font-family: var(--f-ui);
  font-weight: 500;
  font-size: 11px;
  letter-spacing: 1.8px;
  text-transform: uppercase;
  color: var(--amber);
  display: flex; align-items: center; gap: 6px;
}
.ed-field label::before { content: ''; flex: none; width: 6px; height: 2px; background: var(--rust); }
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
  border-left-color: var(--red-stamp);
  background: var(--paper-light);
  box-shadow: 0 0 0 1px var(--amber);
}
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
"""

# ---------- CSS propre au module ----------
CSS_FC = r"""
/* ======== FENÊTRE « NOM DU FICHIER » ======== */

/* ======== FLIGHT CONFIGURATOR ======== */
/* L'accent du module : UNE variable, --fc (au shell, --a-fc). Il colore le bandeau, le bouton principal, le focus, les puces actives et le logo F·C. */
:root { --fc: #D0784A; --mp-accent: #D0784A; }
body[data-theme] {
  --fc-dark: color-mix(in srgb, var(--fc) 62%, #000);
  --fc-dim: color-mix(in srgb, var(--fc) 26%, transparent);
  --pk-ok: var(--fc);
  --cmp-frame: #1f1f1f; --cmp-strip: #151a1f;
}

/* ---------- Barre du haut : même méthode que HQ et le Datacard Generator ---------- */
.toolbar { border-bottom-color: var(--fc); }
.tb-brand-main, .tb-brand-short { color: var(--fc); }
.tb-brand-short { display: none; font-family: var(--f-stencil); font-size: 16px; font-weight: 700; letter-spacing: 3px; }
.tb-btn { width: auto; height: 38px; min-width: 38px; padding: 0 12px; gap: 6px; font-family: var(--f-ui); font-weight: 500; letter-spacing: 1.5px; font-size: 12px; text-transform: uppercase; white-space: nowrap; }
.tb-btn:hover, .tb-btn:focus-visible, .tb-lang-btn:hover, .tb-lang-btn:focus-visible { border-color: var(--fc); }
.tb-btn:hover, .tb-btn:focus-visible { color: var(--fc); }
.tb-btn:disabled { opacity: .4; cursor: default; }
.tb-btn:disabled:hover { background: transparent; border-color: var(--khaki); color: var(--paper); }
.tb-btn.danger:hover { background: var(--rust); border-color: var(--red-faded); color: var(--paper-light); }
/* Seuils mesurés dans le shell (il ajoute à la barre un bouton de retour de 40 ou 119 px, et le tampon de l'escadre « TEST WING »), en français et en anglais, en paysage et en portrait (lot mp-ui-disposition-b : « Ouvrir ▾ » remplace « Ouvrir » et « Importer » ;
   la barre tient sans défiler dès 553 px, sauf de 760 à 792 px où le tampon du shell s'ajoute ; chaque seuil est la plus petite largeur où elle tient avec ce qui précède) : libellés entiers dès 1179 px (le français est le plus large),
   les mêmes libellés aux marges resserrées de 1133 à 1178 px (plus de libellé court), icône seule en dessous ; le titre et la version dès 1468 px, le tampon de décor dès 1677 px ; le sigle reste visible à toutes les largeurs.
   La liste du théâtre (lot mp-theatre-unique) a déplacé de 179 px les seuils du titre et du tampon de décor, de 290 px ceux des libellés entiers et resserrés (théâtre « Caucase », mesuré dans le shell, en français et en anglais, sans dépassement de 900 à 1900 px). */
@media (max-width: 1467px) { .tb-brand-main, .tb-brand-sub, .tb-sep, .tb-version { display: none; } .tb-brand-short { display: inline; } }
@media (max-width: 1178px) { .tb-btn { padding: 0 9px; letter-spacing: 1px; } }
@media (max-width: 1132px) { .tb-btn .tb-btn-label { display: none; } .tb-btn { padding: 0; width: 44px; } }
@media (max-width: 539px) { .tb-select { max-width: 96px; } }
@media (max-width: 479px) { .toolbar { gap: 3px; } .tb-btn { width: 34px; min-width: 34px; } .tb-select { max-width: 64px; padding: 0 18px 0 6px; } .tb-lang-btn { min-width: 34px; padding: 0 2px; } }
/* Le bouton « Ouvrir » reste un bouton de menu (icône + chevron) : à la taille de celui du Route Planner, jamais réduit à la forme d'un bouton à icône seule (mêmes marges intérieures : 12 px, 8 px à gauche sous 521 px) */
@media (max-width: 1132px) { #btn-open { width: auto; min-width: 44px; padding-left: 12px; padding-right: 12px; } }
@media (max-width: 520px) { #btn-open { padding-left: 8px; } }
/* La liste du théâtre (lot mp-theatre-unique) : jusqu'à 980 px le libellé « Théâtre » cède la place (la liste garde son nom accessible) ; sous 480 px la liste se resserre (texte entier jusqu'à 96 px, puis coupé)
   et la liste du thème de l'interface quitte la barre (le thème se règle au tableau du shell, qui le propage) : sans cela la barre défile de 21 à 28 px à 412 px */
@media (max-width: 849px) { .tb-label { display: none; } }
@media (max-width: 479px) { .tb-sel { padding: 0 20px 0 6px; font-size: 11px; letter-spacing: .5px; background-position: right 6px center; flex: none; max-width: 79px; } .tb-select.tbm-trigger { display: none; } }

/* Tampon de décor : le style de celui du Briefing Generator, en anglais dans les deux langues ; il ne s'affiche que quand la barre a la place. */
.tb-brand-sub { font-weight: 500; }
.tb-version { font-family: 'Roboto Mono', monospace; }
.tb-classif { font-family: var(--f-stencil); font-weight: 400; font-size: 11px; letter-spacing: 3px; color: var(--red-faded); border: 1px solid var(--red-faded); padding: 4px 10px; white-space: nowrap; flex-shrink: 0; }
@media (max-width: 1676px) { .tb-classif { display: none; } }

/* ---------- Page : état de l'export, deux colonnes, blocs ---------- */
.editor { max-width: 1840px; }
#fc-status { position: sticky; top: 0; z-index: 5; }       /* le bandeau est .ui-bandeau (neutre, .ok, .err) ; ici seulement sa place */
/* Le bandeau « les groupes sont sur un autre théâtre » (lot mp-theatre-unique) : le style des avertissements de la fiche (.rt-warn), deux boutons de la suite */
.fc-tc { margin: 0 0 12px; padding: 10px 12px; background: var(--olive-dark); border: 1px solid var(--khaki); border-left: 3px solid var(--amber); }
.fc-tc[hidden] { display: none; }
.fc-tc .rt-note { margin: 0; }
.fc-tc .miz-btn-row { margin-top: 10px; }
.fc-cols { display: grid; grid-template-columns: minmax(0, 1fr); gap: 16px; align-items: start; }
.fc-cols > * { min-width: 0; }
@media (min-width: 1100px) { .fc-cols { grid-template-columns: minmax(0, 1fr) minmax(0, 1.12fr); } }
.fc-block { border: 1px solid var(--khaki); background: rgba(20,24,12,.5); }
#col-presets > .fc-block { margin-top: 16px; }
.fc-bh { padding: 11px 14px; background: linear-gradient(90deg, var(--olive) 0%, var(--olive-dark) 100%); font-family: var(--f-stencil); font-size: 13px; letter-spacing: 2px; color: var(--amber); border-bottom: 1px solid var(--fc); min-height: 44px; display: flex; align-items: center; gap: 6px; }
.fc-bh .fc-count { font-family: var(--f-typewriter); font-size: 12px; letter-spacing: 0; color: var(--paper); }
.fc-bc { padding: 14px; display: flex; flex-direction: column; gap: 12px; }
.fc-row { display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 10px; align-items: end; }
.fc-row3 { display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 10px; }
.fc-row4 { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; }
.fc-row > *, .fc-row3 > *, .fc-row4 > *, .fc-set > * { min-width: 0; }
.snap-flight-tag { font-family: var(--f-ui); font-weight: 500; font-size: 10px; padding: 2px 6px; border-radius: 2px; background: var(--olive); color: var(--paper-light); text-transform: uppercase; letter-spacing: 1px; white-space: nowrap; }
.pk-x { flex: none; min-width: 36px; min-height: 36px; background: none; border: 0; color: var(--khaki-light); font-size: 16px; cursor: pointer; }
.pk-x:hover, .pk-x:focus-visible { color: var(--amber); }
.pk-chk { display: inline-flex; align-items: center; gap: 8px; min-height: 36px; cursor: pointer; font-family: var(--f-typewriter); font-size: 12px; }
.pk-chk input { accent-color: var(--fc); width: 18px; height: 18px; margin: 0; flex: none; }
.pk-chk.off { opacity: .4; cursor: default; }
.miz-btn { min-height: 44px; }
.miz-btn.primary { border-color: var(--fc); color: var(--fc); }
.miz-btn.primary:hover { background: var(--fc-dark); color: var(--paper-light); }
.miz-btn.primary:disabled:hover { background: rgba(0,0,0,.2); border-color: var(--fc); color: var(--fc); }
.miz-btn.fc-small { min-height: 36px; }
.fc-small { padding: 6px 12px; font-size: 11px; }
.fc-msg { font-family: var(--f-typewriter); font-size: 11px; color: var(--mp-warn); margin-top: 6px; word-break: break-word; }
.fc-msg:empty { display: none; }

/* ---------- Champs : listes au thème de l'interface (même composant que la barre), nombres ---------- */
.fc-sel.tbm-trigger.tbm-field {
  display: block; position: relative; contain: inline-size; text-align: left; letter-spacing: normal; text-transform: none; font-weight: 400;
  box-sizing: border-box; width: 100%; min-width: 0; min-height: 44px; padding: 0 34px 0 11px; margin: 0; cursor: pointer;
  font-family: var(--f-typewriter); font-size: 13px; line-height: 42px;
  background: rgba(216,201,165,.92); color: var(--ink);
  border: 1px solid var(--khaki); border-left: 3px solid var(--amber-dark); border-radius: 0;
}
.fc-sel.tbm-trigger.tbm-field::after {
  content: ''; position: absolute; right: 12px; top: 50%; width: 12px; height: 8px; margin-top: -4px; pointer-events: none;
  background: currentColor;
  -webkit-mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='8' viewBox='0 0 12 8'%3E%3Cpath d='M1 1.5l5 5 5-5' fill='none' stroke='%23000' stroke-width='1.6'/%3E%3C/svg%3E") center / 12px 8px no-repeat;
  mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='8' viewBox='0 0 12 8'%3E%3Cpath d='M1 1.5l5 5 5-5' fill='none' stroke='%23000' stroke-width='1.6'/%3E%3C/svg%3E") center / 12px 8px no-repeat;
}
.fc-sel.tbm-trigger.tbm-field .tbm-lbl { margin: 0; padding: 0; line-height: 42px; }
.fc-sel.tbm-trigger.tbm-field .tbm-lbl::after { display: none; }
.fc-sel.tbm-trigger.tbm-field:focus { border-left-color: var(--red-stamp); box-shadow: 0 0 0 1px var(--fc); }
.fc-sel.tbm-trigger.tbm-field:disabled { opacity: .5; cursor: default; }
.tbm-panel.tbm-p-field .tbm-opt { white-space: normal; line-height: 1.3; padding-top: 8px; padding-bottom: 8px; word-break: break-word; }
.ed-field input[type=text] { min-width: 0; }
.ed-field input.bad, .fc-ch input.bad { border-color: var(--mp-warn); border-left-color: var(--mp-warn); }
.fc-ch input, .fc-set input[type=number] {
  background: rgba(216,201,165,.92); border: 1px solid var(--khaki); border-left: 3px solid var(--amber-dark);
  font-family: var(--f-typewriter); font-size: 13px; color: var(--ink); padding: 6px 8px; width: 100%; min-width: 0; border-radius: 0;
  -moz-appearance: textfield; appearance: textfield;
}
.fc-ch input { min-height: 44px; }
.fc-set input[type=number] { min-height: 44px; }
.fc-ch input:focus, .fc-set input[type=number]:focus { border-left-color: var(--red-stamp); background: var(--paper-light); box-shadow: 0 0 0 1px var(--fc); }
.fc-ch input::-webkit-outer-spin-button, .fc-ch input::-webkit-inner-spin-button, .fc-set input::-webkit-outer-spin-button, .fc-set input::-webkit-inner-spin-button { -webkit-appearance: none; margin: 0; }
.fc-set input:disabled { opacity: .5; }
/* la barre du carburant : piste et curseur aux couleurs du thème (--khaki, --paper-light), la part pleine à l'accent du module (--fc) ; l'élément fait 34 px de haut pour se prendre au doigt */
.fc-bar { display: flex; align-items: center; gap: 8px; margin-top: 4px; }
.fc-pct { flex: none; min-width: 3.6em; text-align: right; font-family: var(--f-typewriter); font-size: 12px; color: var(--paper-light); font-variant-numeric: tabular-nums; }
.fc-range { -webkit-appearance: none; appearance: none; flex: 1 1 auto; min-width: 0; width: 100%; height: 34px; margin: 0; padding: 0; background: transparent; cursor: pointer; touch-action: pan-y; }
.fc-range:focus-visible { outline: 2px solid var(--amber); outline-offset: 2px; }
.fc-range::-webkit-slider-runnable-track { height: 8px; border: 1px solid var(--khaki); border-radius: 0; background: linear-gradient(to right, var(--fc) 0, var(--fc) var(--p, 100%), var(--olive-dark) var(--p, 100%), var(--olive-dark) 100%); }
.fc-range::-webkit-slider-thumb { -webkit-appearance: none; appearance: none; width: 24px; height: 24px; margin-top: -9px; border-radius: 50%; background: var(--paper-light); border: 3px solid var(--fc); box-shadow: 0 1px 3px rgba(0,0,0,.6); }
.fc-range::-moz-range-track { height: 8px; border: 1px solid var(--khaki); border-radius: 0; background: var(--olive-dark); }
.fc-range::-moz-range-progress { height: 8px; background: var(--fc); }
.fc-range::-moz-range-thumb { width: 18px; height: 18px; border-radius: 50%; background: var(--paper-light); border: 3px solid var(--fc); box-shadow: 0 1px 3px rgba(0,0,0,.6); }
.fc-range:disabled { opacity: .4; }

/* ---------- Un vol ---------- */
.fc-list { display: flex; flex-direction: column; gap: 12px; }
.fc-flight { border: 1px solid var(--khaki); border-radius: 3px; padding: 10px 12px 12px; background: rgba(0,0,0,.15); }
.fc-fhead, .fc-uhead { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin-bottom: 8px; }
.fc-fhead .pk-x, .fc-uhead .pk-x { margin-left: auto; margin-right: -8px; }
.fc-fhead .pk-x { min-width: 44px; min-height: 44px; }
.fc-flight.folded .fc-fhead { margin-bottom: 0; }
.fc-fold { display: flex; align-items: center; gap: 8px; min-height: 44px; min-width: 0; flex: 0 1 auto; padding: 0 4px 0 0; background: none; border: 0; cursor: pointer; text-align: left; color: inherit; }
.fc-fold:focus-visible { outline: 2px solid var(--amber); outline-offset: 2px; }
.fc-chev { flex: none; width: 0; height: 0; border-left: 7px solid var(--mp-accent); border-top: 5px solid transparent; border-bottom: 5px solid transparent; transition: transform .2s; margin: 0 4px; }
.fc-fold[aria-expanded="true"] .fc-chev { transform: rotate(90deg); }
.fc-ftitle { font-family: var(--f-stencil); font-size: 13px; letter-spacing: 1.5px; color: var(--amber); text-transform: uppercase; word-break: break-word; min-width: 0; }
.fc-foldall { margin-left: auto; }
/* replié, l'en-tête garde le titre et le résumé du vol sur une ligne (les pastilles de l'appareil et du nombre d'unités passent dans le résumé) */
.fc-fsum { display: none; flex: 1 1 calc(100% - 24px); min-width: 0; order: 9; margin: -2px 0 2px 24px; font-family: var(--f-typewriter); font-size: 12px; line-height: 1.4; color: var(--khaki-light); overflow-wrap: anywhere; }
.fc-flight.folded .fc-fsum { display: block; }
.fc-flight.folded .fc-fhead .snap-flight-tag { display: none; }
.fc-fbody[hidden] { display: none; }
.fc-route { display: flex; align-items: center; gap: 8px 12px; flex-wrap: wrap; margin-top: 10px; padding: 6px 10px; border: 1px dashed rgba(128,116,84,.6); font-family: var(--f-typewriter); font-size: 12px; color: var(--paper); }
.fc-route.none { color: var(--khaki-light); border-color: rgba(128,116,84,.35); }
.fc-route-t { min-width: 0; word-break: break-word; flex: 1 1 200px; }
.fc-units { display: grid; grid-template-columns: minmax(0, 1fr); gap: 10px; margin-top: 12px; }
.fc-unit { border: 1px solid rgba(128,116,84,.55); border-left: 3px solid var(--amber-dark); padding: 8px 10px 10px; background: rgba(0,0,0,.12); }
.fc-unit.sel { border-left-color: var(--fc); background: var(--fc-dim); box-shadow: 0 0 0 1px var(--fc); }
.fc-nounit { display: flex; align-items: center; min-height: 44px; box-sizing: border-box; border: 1px dashed rgba(128,116,84,.6); border-left: 3px solid var(--amber-dark); padding: 6px 10px; font-family: var(--f-typewriter); font-size: 12px; color: var(--khaki-light); cursor: pointer; }
.fc-nounit.sel { border-left-color: var(--fc); background: var(--fc-dim); box-shadow: 0 0 0 1px var(--fc); color: var(--paper); }
.fc-uhead { margin-bottom: 6px; }
/* la flèche de l'unité : le dessin de celle du groupe (.fc-chev), une cible de 44 px ; repliée, la carte garde son en-tête et une ligne de résumé */
.fc-ufold { display: flex; align-items: center; justify-content: center; flex: none; min-width: 44px; min-height: 44px; margin: -8px 0 -8px -12px; padding: 0; background: none; border: 0; cursor: pointer; color: inherit; }
.fc-ufold:focus-visible { outline: 2px solid var(--amber); outline-offset: 2px; }
.fc-ufold[aria-expanded="true"] .fc-chev { transform: rotate(90deg); }
.fc-usum { display: none; margin: 0 0 2px 26px; font-family: var(--f-typewriter); font-size: 12px; line-height: 1.4; color: var(--khaki-light); overflow-wrap: anywhere; min-width: 0; }
.fc-unit.folded .fc-usum { display: block; }
.fc-unit.folded .fc-uhead { margin-bottom: 2px; }
.fc-ubody[hidden] { display: none; }
.fc-utitle { font-family: var(--f-stencil); font-size: 12px; letter-spacing: 1px; color: var(--paper); text-transform: uppercase; }
.fc-sub { margin-top: 10px; border-top: 1px solid rgba(128,116,84,.45); }
.fc-sub > summary { cursor: pointer; list-style: none; display: flex; align-items: center; gap: 8px; min-height: 44px; user-select: none; font-family: var(--f-stencil); font-size: 12px; letter-spacing: 1.5px; color: var(--amber); text-transform: uppercase; }
.fc-sub > summary::-webkit-details-marker, .fc-post > summary::-webkit-details-marker { display: none; }
.fc-sub > summary.ui-fold-head::before, .fc-post > summary.ui-fold-head::before { margin: 0 4px; }
.fc-sub .fc-sum, .fc-post .fc-sum { font-family: var(--f-typewriter); font-weight: 400; font-size: 11px; letter-spacing: 0; text-transform: none; color: var(--khaki-light); min-width: 0; word-break: break-word; }
.fc-sub > .fc-subc { padding: 2px 0 6px; display: flex; flex-direction: column; gap: 10px; }
.fc-posts { display: grid; grid-template-columns: minmax(0, 1fr); gap: 8px; }
.fc-post { border: 1px solid rgba(128,116,84,.4); background: rgba(0,0,0,.12); }
.fc-post > summary { cursor: pointer; list-style: none; display: grid; grid-template-columns: auto minmax(0, 1fr); align-items: center; column-gap: 8px; min-height: 44px; padding: 3px 10px; user-select: none; font-family: var(--f-ui); font-weight: 500; font-size: 12px; letter-spacing: 1px; color: var(--paper); text-transform: uppercase; }
.fc-post > summary.ui-fold-head::before { grid-column: 1; grid-row: 1 / span 2; }
.fc-ptop { grid-column: 2; display: flex; flex-wrap: wrap; align-items: baseline; gap: 0 8px; min-width: 0; word-break: break-word; }
.fc-band { grid-column: 2; font-family: var(--f-typewriter); font-weight: 400; font-size: 11px; letter-spacing: 0; text-transform: none; color: var(--khaki-light); min-width: 0; word-break: break-word; }
.fc-flag { color: var(--mp-warn) !important; }
.fc-flag:empty { display: none; }
.fc-post > .fc-postc { padding: 4px 10px 10px; }
.fc-chans { display: grid; grid-template-columns: repeat(auto-fill, minmax(104px, 1fr)); gap: 6px 8px; }
.fc-ch { display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.fc-ch > label { font-family: var(--f-ui); font-weight: 500; font-size: 10px; letter-spacing: 1.2px; text-transform: uppercase; color: var(--khaki-light); }
.fc-lo-sum { display: flex; align-items: center; gap: 8px 12px; flex-wrap: wrap; margin-top: 10px; padding-top: 8px; border-top: 1px solid rgba(128,116,84,.45); }
.fc-see { background: none; border: 0; padding: 6px 2px; min-height: 34px; font-family: var(--f-typewriter); font-size: 12px; color: var(--fc); text-decoration: underline; cursor: pointer; }
@media (min-width: 1100px) { .fc-see { display: none; } }
.fc-lo-k { font-family: var(--f-stencil); font-size: 12px; letter-spacing: 1.5px; color: var(--amber); text-transform: uppercase; }
.fc-lo-v { font-family: var(--f-typewriter); font-size: 12px; color: var(--paper); flex: 1 1 160px; min-width: 0; word-break: break-word; }

/* ---------- Le bloc ROUTE : choisir une route du Route Planner, la voir en croquis sur papier, caps magnétiques et distances ----------
   La feuille garde ses variables de thème (--paper-light, --ink, --red-stamp…) ; rien en dur hors des rgba du quadrillage et de l'ombre. */
#blk-route { margin-bottom: 16px; }
#blk-route[hidden] { display: none; }
#blk-route .miz-btn.fc-small { min-height: 44px; }
.rt-note { margin: 0; font-family: var(--f-typewriter); font-size: 13px; line-height: 1.5; color: var(--paper); }
.rt-note.rt-warn { color: var(--amber); }
.rt-h { margin: 4px 0 -2px; font-family: var(--f-ui); font-weight: 500; font-size: 12px; letter-spacing: 2px; text-transform: uppercase; color: var(--amber); }
.rt-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(170px, 1fr)); gap: 12px; }
.rt-grid > * { min-width: 0; }
.rt-card { display: flex; flex-direction: column; align-items: stretch; gap: 6px; min-height: 44px; padding: 6px; text-align: left; background: rgba(0,0,0,.25); border: 1px solid var(--khaki); border-radius: 0; color: var(--paper); cursor: pointer; }
.rt-card:hover, .rt-card:focus-visible { border-color: var(--amber); }
.rt-card.on { border-color: var(--fc); box-shadow: 0 0 0 1px var(--fc); }
.rt-card:disabled { opacity: .5; cursor: default; }
.rt-card:disabled:hover { border-color: var(--khaki); }
.rt-cn { font-family: var(--f-ui); font-weight: 500; font-size: 16px; letter-spacing: 1px; line-height: 1.25; text-transform: uppercase; color: var(--paper-light); overflow-wrap: anywhere; }
.rt-cm { font-family: var(--f-typewriter); font-size: 12px; color: var(--khaki-light); }
.rt-card .rt-tag { align-self: flex-start; max-width: 100%; overflow-wrap: anywhere; white-space: normal; }
.rt-tag.full { background: var(--olive); border-color: var(--olive); color: var(--paper-light); }
.rt-head { display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 8px 14px; }
.rt-hl { display: flex; flex-wrap: wrap; align-items: baseline; gap: 2px 12px; min-width: 0; flex: 1 1 240px; }
.rt-name { font-family: var(--f-ui); font-weight: 500; font-size: 22px; letter-spacing: 1px; line-height: 1.2; text-transform: uppercase; color: var(--paper-light); overflow-wrap: anywhere; }
.rt-sub { font-family: var(--f-typewriter); font-size: 12px; color: var(--khaki-light); }
.rt-hb { display: flex; flex-wrap: wrap; gap: 8px; }
.rt-mini, .rt-thumb { display: block; background-color: var(--paper-light); background-image: linear-gradient(rgba(70,63,48,.09) 1px, transparent 1px), linear-gradient(90deg, rgba(70,63,48,.09) 1px, transparent 1px); background-size: 12px 12px; border: 1px solid var(--paper-dark); }
.rt-mini > svg, .rt-thumb > svg { display: block; width: 100%; height: auto; }
.rt-thumb { flex: none; width: 64px; height: 40px; background-size: 8px 8px; overflow: hidden; }
.fc-route .fc-see { min-height: 44px; }
.rt-paper { position: relative; background-color: var(--paper-light); background-image: linear-gradient(rgba(70,63,48,.09) 1px, transparent 1px), linear-gradient(90deg, rgba(70,63,48,.09) 1px, transparent 1px); background-size: 22px 22px; border: 1px solid var(--paper-dark); box-shadow: 2px 3px 0 rgba(0,0,0,.45); transform: rotate(-0.4deg); margin: 4px 0 6px; }
.rt-paper > svg { display: block; max-width: 100%; }
.rt-svg text { font-family: var(--f-typewriter); }
.rt-leg { fill: none; stroke: var(--ink); stroke-width: 2; stroke-linecap: round; stroke-linejoin: round; }
.rt-leg2 { fill: none; stroke: var(--ink-faded); stroke-width: 1; stroke-linecap: round; opacity: .45; }
.rt-arr { fill: none; stroke: var(--ink); stroke-width: 2; stroke-linecap: round; stroke-linejoin: round; }
.rt-pt { fill: none; stroke: var(--ink); stroke-width: 1.8; }
.rt-start { fill: var(--red-stamp); }
.rt-m .rt-leg { stroke-width: 1.5; }
.rt-m .rt-leg2 { stroke-width: .8; }
.rt-m .rt-arr { stroke-width: 1.2; }
.rt-m .rt-pt { stroke-width: 1.2; }
.rt-lbl { font-size: 12px; fill: var(--ink); stroke: var(--paper-light); stroke-width: 4px; stroke-linejoin: round; paint-order: stroke; }
.rt-con { fill: none; stroke: var(--ink-faded); stroke-width: 1; }
.rt-hd { font-size: 11px; fill: var(--red-stamp); stroke: var(--paper-light); stroke-width: 3px; stroke-linejoin: round; paint-order: stroke; text-anchor: middle; }
.rt-num circle { fill: var(--paper-light); stroke: var(--red-stamp); stroke-width: 1.2; }
.rt-num text { font-size: 10px; fill: var(--red-stamp); text-anchor: middle; }
.rt-svg .rt-gn { font-family: var(--f-stencil); font-weight: 400; font-size: 13px; letter-spacing: 2px; text-transform: uppercase; fill: var(--ink-faded); }
.rt-north line, .rt-north path, .rt-scale path { fill: none; stroke: var(--ink); stroke-width: 1.6; stroke-linecap: round; stroke-linejoin: round; }
.rt-svg .rt-nn { font-family: var(--f-stencil); font-weight: 400; font-size: 16px; fill: var(--ink); text-anchor: middle; }
.rt-scale text { font-size: 12px; fill: var(--ink); }
.rt-tab { width: 100%; border-collapse: collapse; font-family: var(--f-typewriter); font-size: 13px; color: var(--paper); }
.rt-tab th { padding: 8px 6px; text-align: left; font-family: var(--f-ui); font-weight: 500; font-size: 12px; letter-spacing: 2px; text-transform: uppercase; color: var(--amber); border-bottom: 1px solid var(--khaki-light); }
.rt-tab td { padding: 7px 6px; border-bottom: 1px dashed rgba(128,116,84,.55); overflow-wrap: anywhere; }
.rt-tab .rt-n { width: 2.2em; color: var(--khaki-light); }
.rt-tab .rt-r { text-align: right; white-space: nowrap; }
.rt-tab .rt-tot td { border-bottom: 0; }
@media (max-width: 539px) { .rt-name { font-size: 22px; } .rt-tab { font-size: 12px; } }

/* ---------- L'emport : la vue de face de Mission Tools (Loadout Editor), reprise ---------- */
.fc-back { display: none; align-self: flex-start; min-height: 40px; padding: 0 4px; background: none; border: 0; font-family: var(--f-typewriter); font-size: 13px; color: var(--fc); text-decoration: underline; cursor: pointer; }
.fc-back:focus-visible { outline: 2px solid var(--amber); outline-offset: 2px; }
@media (max-width: 1099px) { .fc-back { display: inline-flex; align-items: center; } }
.cmp-top { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 10px; align-items: end; }
.cmp-top > * { min-width: 0; }
.cmp-for { font-family: var(--f-typewriter); font-size: 13px; color: var(--paper-light); word-break: break-word; display: flex; flex-wrap: wrap; gap: 4px 8px; align-items: center; }
.fc-lo-line { display: flex; flex-wrap: wrap; gap: 6px 10px; align-items: center; font-family: var(--f-typewriter); font-size: 11px; color: var(--khaki-light); }
#cmp-wrap { position: relative; }
.cmp-view { position: relative; background: var(--cmp-frame); padding: 26px 14px 30px; border-radius: 4px; }
.cmp-wrap-strip .cmp-view { border-radius: 4px 4px 0 0; }
.cmp-svgbox { position: relative; margin: 0 auto; width: min(100%, calc(52vh * var(--r))); }
.cmp-svgbox > svg { display: block; width: 100%; height: auto; }
.cmp-svgbox svg [stroke]:not([stroke="none"]) { stroke: var(--paper); }
.cmp-svgbox svg [fill="#ffffff"] { fill: var(--cmp-frame); }
/* le crédit est en haut à droite de la vue, comme au Loadout Editor de Mission Tools : la vue lui laisse sa marge haute, aucun trait ne le traverse */
.cmp-credit { position: absolute; right: 10px; top: 6px; z-index: 4; max-width: calc(100% - 20px); font-family: var(--f-typewriter); font-size: 10px; line-height: 1.3; color: var(--khaki-light); background: var(--cmp-frame); padding: 0 4px; text-align: right; }
#cmp-leads { position: absolute; inset: 0; width: 100%; height: 100%; pointer-events: none; z-index: 2; overflow: visible; }
#cmp-leads path { fill: none; stroke: var(--fc); stroke-width: 1.4; stroke-dasharray: 5 4; opacity: .9; }
#cmp-leads path.on { stroke-width: 2.4; opacity: 1; }
#cmp-leads circle { fill: #1b2228; stroke: var(--fc); stroke-width: 2; }
.cmp-strip { position: relative; height: 58px; background: var(--cmp-strip); border-top: 1px solid var(--khaki); border-radius: 0 0 4px 4px; }
.cmp-st { position: absolute; top: 6px; transform: translateX(-50%); width: calc(100% / var(--n) - 6px); min-width: 0; text-align: center; padding: 3px 2px; background: var(--cmp-frame); border: 1px solid var(--khaki); border-radius: 3px; cursor: pointer; z-index: 3; }
.cmp-st .n { display: block; font-family: var(--f-typewriter); font-size: 11px; color: var(--khaki-light); }
.cmp-st .w { display: block; font-family: var(--f-typewriter); font-size: 11px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; color: var(--paper-light); }
.cmp-st.has { border-color: var(--khaki-light); }
.cmp-st.sel, .cmp-st.sel.has { border-color: var(--fc); box-shadow: 0 0 0 2px var(--fc-dim); }
.cmp-st.sel .n { color: var(--fc); }
.cmp-st:focus-visible { outline: 2px solid var(--amber); outline-offset: 2px; }
/* étroit : la rangée ne porte que les numéros (les armes sont dans la liste), régulièrement espacés */
.cmp-wrap-flat .cmp-view { padding: 34px 10px 12px; border-radius: 4px 4px 0 0; }      /* étroit : le crédit tient sur deux lignes, en haut */
.cmp-wrap-flat .cmp-strip { height: 34px; }
.cmp-wrap-flat .cmp-st { top: 6px; width: calc(100% / var(--n) - 2px); max-width: 30px; padding: 1px 0; cursor: default; }
.cmp-wrap-flat .cmp-st .w { display: none; }
.cmp-wrap-flat .cmp-st .n { font-size: 12px; line-height: 20px; }
.cmp-wrap-flat .cmp-st.has .n { color: var(--paper-light); }
.cmp-list { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 4px 20px; }
.cmp-row { display: grid; grid-template-columns: 26px minmax(0, 1fr) 74px; align-items: center; gap: 2px 8px; padding: 3px 6px; border-radius: 4px; }
.cmp-row.sel { background: var(--fc-dim); }
.cmp-row > .sn { grid-column: 1; grid-row: 1; font-family: var(--f-typewriter); font-size: 13px; color: var(--khaki-light); }
.cmp-row.sel > .sn { color: var(--fc); }
.cmp-row > .fc-sel { grid-column: 2; grid-row: 1; min-width: 0; width: 100%; }
.cmp-row > .cmp-kg { grid-column: 3; grid-row: 1; text-align: right; font-family: var(--f-typewriter); font-size: 12px; color: var(--paper); white-space: nowrap; font-variant-numeric: tabular-nums; }
.cmp-row > .cmp-sub { grid-column: 2 / 4; grid-row: 2; }
.cmp-sub { display: flex; align-items: center; flex-wrap: wrap; gap: 2px 10px; font-family: var(--f-typewriter); font-size: 11px; color: var(--khaki-light); }
.cmp-sub[hidden], .cmp-mirror[hidden], .cmp-nomirror[hidden] { display: none; }
/* une arme au nom long passe sur deux lignes au lieu d'être coupée */
.cmp-row .fc-sel.tbm-trigger.tbm-field { display: flex; align-items: center; line-height: 1.25; padding-top: 5px; padding-bottom: 5px; min-height: 40px; }
.cmp-row .fc-sel.tbm-trigger.tbm-field .tbm-lbl { line-height: 1.25; white-space: normal; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; text-overflow: clip; }
.cmp-foot { display: flex; align-items: center; flex-wrap: wrap; gap: 8px 18px; padding-top: 4px; }
.cmp-tot { font-family: var(--f-typewriter); font-size: 12px; color: var(--khaki-light); }
.cmp-tot b { color: var(--paper-light); white-space: nowrap; }
.fc-chip { font-family: var(--f-ui); font-size: 10px; letter-spacing: 1px; text-transform: uppercase; padding: 1px 6px; border: 1px solid var(--khaki); color: var(--khaki-light); white-space: nowrap; }
.fc-set { display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 8px; }
.fc-set .ed-field label { font-size: 10px; letter-spacing: 1.2px; }
.fc-actions .miz-btn { min-height: 44px; width: 100%; justify-content: center; }
.fc-editor { border: 1px solid var(--fc); border-top: 3px solid var(--fc); background: var(--olive-dark); padding: 12px; display: flex; flex-direction: column; gap: 10px; }

/* ---------- Mes presets ---------- */
.fc-lib { display: flex; flex-direction: column; gap: 6px; }
.fc-file { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; border: 1px solid rgba(128,116,84,.45); padding: 4px 4px 4px 10px; background: rgba(0,0,0,.12); min-height: 44px; }
.fc-file-n { font-family: var(--f-typewriter); font-size: 12px; color: var(--paper); word-break: break-all; min-width: 0; }
.fc-file .pk-x { margin-left: auto; }
.fc-h { font-family: var(--f-stencil); font-size: 11px; letter-spacing: 2px; text-transform: uppercase; color: var(--amber); padding: 8px 0 2px; border-bottom: 1px solid var(--khaki); margin-bottom: 4px; }

/* ---------- Téléphone ---------- */
@media (max-width: 539px) {
  .editor { padding: 10px 8px 80px 8px; }
  .fc-bc { padding: 10px; }
  .fc-flight { padding: 8px 8px 10px; }
  .fc-unit { padding: 6px 8px 8px; }
  .fc-chans { grid-template-columns: repeat(auto-fill, minmax(92px, 1fr)); }
  .cmp-list { grid-template-columns: minmax(0, 1fr); }
  .cmp-row { grid-template-columns: 24px minmax(0, 1fr) 70px; gap: 2px 6px; padding: 3px 0; }
  .miz-btn-row .miz-btn { flex: 1 1 100%; justify-content: center; }
}

/* R295 : une seule graisse par police embarquée (Oswald 500, Roboto Mono 400, Stardos Stencil 700) */
b, strong { font-weight: 400; }
"""

# ---------- Corps de la page ----------
def _icon(d):
    return '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + d + '</svg>'


def _btn(bid, key, icon, extra=''):
    return ('<button type="button" class="tb-btn%s" id="btn-%s" data-i18n-title="tb.%s.tip" title="">%s'
            '<span class="tb-btn-label" data-i18n="tb.%s">.</span></button>'
            % (extra, bid, key, _icon(icon), key))


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
  <span class="tb-label" data-i18n="tb.theatre">Théâtre</span>
  <select class="tb-sel" id="theatre" aria-label="Théâtre"></select>
  <div class="tb-sep"></div>
  @@BUTTONS@@
  <div class="tb-sep"></div>
  <select class="tb-select" id="theme-select" data-i18n-title="toolbar.theme.tooltip" title="Thème graphique">
    <option value="cw-nato"     data-i18n="theme.cw-nato">Cold War OTAN</option>
    <option value="cw-soviet"   data-i18n="theme.cw-soviet">Cold War Soviétique</option>
    <option value="modern-nato" data-i18n="theme.modern-nato">OTAN moderne</option>
    <option value="modern-east" data-i18n="theme.modern-east">Bloc Est moderne</option>
  </select>
  <div class="tb-spacer"></div>
  <div class="tb-classif">FLIGHT LEAD // COPY 1</div>
  <span class="tb-version">v@@VERSION@@</span>
  <button class="tb-lang-btn" id="btn-lang" title="Passer en anglais" aria-label="Passer en anglais"><svg viewBox="0 0 20 14" width="22" height="15" xmlns="http://www.w3.org/2000/svg"><rect width="20" height="14" fill="#012169"/><path d="M0,0 L20,14 M20,0 L0,14" stroke="#fff" stroke-width="2.8"/><path d="M0,0 L20,14 M20,0 L0,14" stroke="#C8102E" stroke-width="1.6"/><rect x="8" width="4" height="14" fill="#fff"/><rect y="5" width="20" height="4" fill="#fff"/><rect x="9" width="2" height="14" fill="#C8102E"/><rect y="6" width="20" height="2" fill="#C8102E"/></svg></button>
</header>

<!-- MAIN APP -->
<div class="app" id="app">
  <div class="editor" id="editor-panel">
    <div class="fc-tc" id="fc-tc" role="alert" hidden></div>
    <div class="ui-bandeau" id="fc-status" role="status" aria-live="polite"></div>
    <div class="fc-cols">
      <div id="col-left"><div id="col-flights"></div></div>
      <div id="col-right"></div>
    </div>
  </div>
</div>

@@IMPORT_HTML@@
<input type="file" id="fc-in-lua" accept=".lua,text/plain" multiple hidden>
<input type="file" id="fc-in-open" accept=".json,application/json" hidden>
<!-- FENÊTRE : NOM DU FICHIER (enregistrement, paquet) -->
<div class="ui-modal" id="fn-modal" hidden role="dialog" aria-modal="true" aria-labelledby="fn-title">
  <div class="ui-backdrop" id="fn-backdrop"></div>
  <div class="ui-panel" role="document">
    <button type="button" class="ui-close" id="fn-close" aria-label="Fermer">&times;</button>
    <h2 id="fn-title" class="ui-title"></h2>
    <div class="ui-field"><label class="ui-lbl" for="fn-name" data-i18n="fn.label">Nom du fichier</label><div class="ui-row"><input class="ui-in" id="fn-name" type="text" autocomplete="off" autocapitalize="off" spellcheck="false" maxlength="100"><span class="ui-ext" id="fn-ext">.json</span></div></div>
    <div class="ui-actions">
      <button type="button" class="ui-btn" id="fn-cancel" data-i18n="fn.cancel">Annuler</button>
      <button type="button" class="ui-btn primary" id="fn-go"></button>
    </div>
  </div>
</div>
"""

OPEN_BTN = '''  <button type="button" class="tb-btn" id="btn-open" aria-haspopup="menu" aria-expanded="false" data-i18n-title="tb.open.tip" title="">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v1H3z"/><path d="M3 10h19l-2 8a2 2 0 0 1-2 1.5H5a2 2 0 0 1-2-2z"/></svg>
    <span class="tb-btn-label" data-i18n="tb.open">.</span>
    <svg class="dsp-chev" viewBox="0 0 10 6" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M1 1l4 4 4-4"/></svg>
  </button>'''.strip()
BUTTONS = '\n  '.join([
    OPEN_BTN,
    _btn('save', 'save', '<path d="M5 3h11l4 4v13a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1z"/><path d="M8 3v5h7V3"/><rect x="7" y="13" width="10" height="8"/>'),
    _btn('export', 'export', '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>'),
    _btn('example', 'example', '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="8" y1="13" x2="16" y2="13"/><line x1="8" y1="17" x2="16" y2="17"/>'),
    _btn('clear', 'clear', '<polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/><path d="M10 11v6M14 11v6"/><path d="M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/>', ' danger'),
])
BODY = BODY.replace('@@BUTTONS@@', BUTTONS).replace('@@IMPORT_HTML@@\n', build_import_html())

# ---------- Listes au thème de l'interface (copie du composant de HQ) ----------
JS_TBM = """
/* ============= LE MENU « OUVRIR » (lot mp-ui-disposition-b) =============
   Même composant et même aspect que les listes de la barre (tbm-panel dsp-panel, dsp-opt) et que les menus du Route Planner et du Datacard Generator :
   un seul menu ouvert à la fois, avec les listes de la barre. Une ligne par geste, son indice à droite. */
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

/* o : { items, choose } : une ligne par geste ; le menu se ferme avant choose.
   items : { k, label, hint?, title?, disabled? } */
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
    if (it.disabled) row.setAttribute('aria-disabled', 'true');
    if (it.title) row.title = it.title;
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
    btn.focus({ preventScroll: true });      /* la fenêtre qui s'ouvre rend le focus au bouton du menu */
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
  const go = k => { if (rows[k]) rows[k].focus({ preventScroll: true }); };
  const k = e.key;
  if (k === 'ArrowDown') { e.preventDefault(); go(cur < 0 ? 0 : Math.min(rows.length - 1, cur + 1)); }
  else if (k === 'ArrowUp') { e.preventDefault(); go(cur < 0 ? rows.length - 1 : Math.max(0, cur - 1)); }
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
  opn.addEventListener('click', () => { if (MN.cur && MN.cur.btn === opn) mnClose(false); else fcOpenMenu(opn); });
  opn.addEventListener('keydown', e => { if (e.key === 'ArrowDown' && !MN.cur) { e.preventDefault(); fcOpenMenu(opn); } });
}

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
  const m = { sel: sel, btn: btn, lbl: lbl, labelFn: labelFn, panel: null, active: -1, type: '', typeTimer: 0, x0: 0, y0: 0, uid: uid, form: !!mode, fit: !!fit, mo: null };
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
  const w = m.fit ? txt : all.join(String.fromCharCode(10));       /* fit : le bouton prend la largeur de l'option choisie (comme au Route Planner et au Datacard Generator) */
  if (m.lbl.getAttribute('data-w') !== w) m.lbl.setAttribute('data-w', w);
  let name = '';
  try { name = m.labelFn(); } catch (e) { name = ''; }
  m.btn.setAttribute('aria-label', name);
  if (sel.hasAttribute('title')) m.btn.title = sel.title; else if (m.fit && txt) m.btn.title = txt; else m.btn.removeAttribute('title');       /* fit : nom entier en infobulle (le bouton peut le tronquer) */
  m.btn.disabled = sel.disabled;
}

function tbmOpen(m) {
  if (TBM.cur) tbmClose(false);
  mnClose(false);
  if (m.sel.disabled) return;
  tbmSync(m);
  const sel = m.sel, opts = sel.options, name = m.labelFn();
  const ul = document.createElement('ul');
  ul.className = 'tbm-panel' + (m.form ? ' tbm-p-field' : '');
  if (sel.closest && sel.closest('#imp-modal')) ul.classList.add('tbm-imp');       // les listes de la fenêtre d'import passent devant elle
  ul.id = 'tbm-list-' + m.uid;
  ul.setAttribute('role', 'listbox');
  ul.setAttribute('aria-label', name);
  ul.tabIndex = -1;
  const head = document.createElement('li');
  head.className = 'tbm-head';
  head.setAttribute('role', 'presentation');
  head.textContent = name;
  ul.appendChild(head);
  let grp = null;
  for (let k = 0; k < opts.length; k++) {
    const o = opts[k], li = document.createElement('li');
    const og = o.parentNode && o.parentNode.tagName === 'OPTGROUP' ? o.parentNode : null;      /* un groupe d'options : son titre, une fois, avant la première */
    if (og !== grp) {
      grp = og;
      if (og) {
        const gh = document.createElement('li');
        gh.className = 'tbm-head tbm-group';
        gh.setAttribute('role', 'presentation');
        gh.textContent = og.label;
        ul.appendChild(gh);
      }
    }
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

/* Choisir : si la valeur change, le <select> la prend et reçoit un évènement change (qui bouillonne) ; un <select data-repick> (le champ Livrée) le reçoit aussi quand on re-choisit sa valeur : le nom affiché devient un choix */
function tbmChoose(m, k) {
  const sel = m.sel, o = sel.options[k];
  if (!o || o.disabled) return;
  const changed = k !== sel.selectedIndex;
  tbmClose(true);
  if (!changed && !sel.hasAttribute('data-repick')) return;
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
  const other = t && t.closest ? t.closest(MENU_TRIG) : null;
  tbmClose(false);
  if (other) return;
  tbmSwallowNext();
}

/* Le clic qui suit le toucher hors de la liste est avalé (aussi pour le menu « Ouvrir ») */
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

# ---------- Script du module ----------
JS_APP = r"""
// =============================================================
//  FLIGHT CONFIGURATOR — un vol (identité, radios, emport, livrée ; un type par unité) exporté en paquet `dcs-flight-package-v2`
//  1. Socle · 2. Modèle · 3. Colonne des vols · 4. Emport et presets · 5. Fenêtre d'import · 6. Fichiers · 7. Événements
// =============================================================

// ---------- 1. Socle : textes, utilitaires, constantes, état ----------
const I18N = @@I18N@@;
let CURRENT_LANG = 'fr';

function t(key) {
  const own = I18N[CURRENT_LANG];
  if (key in own) return own[key];
  return key in I18N.fr ? I18N.fr[key] : key;
}
function tf(key, ...args) {
  return t(key).replace(/\{(\d+)\}/g, (m, i) => (Number(i) < args.length ? String(args[i]) : m));
}
function esc(s) {
  return String(s === undefined || s === null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
const isObj = o => !!o && typeof o === 'object' && !Array.isArray(o);
const isNum = v => typeof v === 'number' && isFinite(v);
const str = v => (typeof v === 'string' ? v : '');
const clone = o => JSON.parse(JSON.stringify(o));
const has = (o, k) => Object.prototype.hasOwnProperty.call(o, k);

const TYPE_LABEL = { 'Mi-24P': 'Mi-24P', 'Mi-8MT': 'Mi-8MT', 'F-4E-45MC': 'F-4E-45MC', 'Mirage-F1EE': 'Mirage F1EE' };
// Canaux par poste (sonde des .miz) : RADIO_CHANNELS est défini par le bloc d'import commun, qui donne aussi radioPostsOf et radioSlotsOf (les postes pré-réglés, puis le poste HF des deux hélicoptères,
// que la mission ne pré-règle pas : cinq fréquences, sans numéro de canal). Les bandes de chaque poste (RADIO_BANDS) et ces postes non pré-réglés (RADIO_FREE) sont ceux de radio_bands_block.py,
// que le Datacard Generator partage ; les noms des postes sont ceux de radio_block.py.
const THEATRES = ['Caucasus', 'GermanyCW', 'Syria', 'PersianGulf', 'Normandy', 'TheChannel', 'Nevada', 'MarianaIslands', 'MarianaIslandsWWII', 'Kola', 'SinaiMap', 'Iraq', 'Afghanistan', 'Falklands'];       // les quatorze théâtres du Route Planner et du Datacard Generator (DG_THEATRES), dans leur ordre
// Le nom lisible d'un théâtre, le même qu'au Route Planner (clés th.*) ; un théâtre hors liste garde son identifiant. La valeur enregistrée reste l'identifiant.
function theatreName(id) { return THEATRES.indexOf(id) >= 0 ? t('th.' + id) : String(id); }
const PARTS = ['route', 'radios', 'loadout', 'livery'];
const LO_FIELDS = ['fuel', 'flare', 'chaff', 'gun'];
const MAX_UNITS = 4;
const SUMMARY_LIVERY_MAX = 24;
const KEY_THEME = 'theme_v1', KEY_LANG = 'lang_v1', KEY_STATE = 'fc_state_v1', KEY_HQ_MISSION = 'mission_snapshot_v1';
const PACKAGE_FORMAT = 'dcs-flight-package-v2', PACKAGE_FORMATS = ['dcs-flight-package-v1', 'dcs-flight-package-v2'];

// L'état. S est le travail en cours : les groupes et le théâtre vivent dans flight_set_v1 (partagée avec le Route Planner, bloc group_store_block.py), le fichier de travail
// les garde en entier ; une clé de plus sur un groupe ou une unité y survit (le bloc « Départ » du lot suivant). fc_state_v1 ne garde que { v: 2, sel, mine }.
// LIB.mine : mes presets par type. UI : ce qui ne se garde pas.
const S = { theatre: 'Caucasus', flights: [], sel: { f: 0, u: 0 } };       // theatre : le théâtre commun de Mission Plan (mp_theatre_v1), toujours un des quatorze ; celui de la fiche des groupes est GS.theatre
const LIB = { mine: {}, report: null };
const UI = {
  open: new Set(),          // volets <details> ouverts ou fermés à la main
  fold: new WeakMap(),      // vol → 'open' | 'closed'
  clamped: 0,               // réglages d'emport ramenés à la limite (ligne d'état)
  exportTried: false,       // un clic sur Exporter avec des manques : le bandeau passe en rouge, jusqu'à ce que les manques soient levés (jamais enregistré)
  cmp: { sym: true, st: null, saving: false, name: '', err: '' },
  rtChoose: null            // le fcId du groupe dont on choisit la route (« Changer de route ») ; un groupe sans route est toujours au choix
};

// ----- Le théâtre commun (lot mp-theatre-unique) -----
// Un seul théâtre pour Mission Plan : celui que le Route Planner, le Datacard Generator et ce module partagent par mp_theatre_v1 = { theatre } (sans horodatage : réécrire la même valeur
// ne déclenche aucun évènement « storage », et un théâtre venu de la clé n'est jamais réécrit : c'est ce qui coupe la boucle). S.theatre est ce théâtre, toujours un des quatorze.
// Le théâtre de la fiche des groupes (flight_set_v1, GS.theatre) reste le sien : la fiche prend le théâtre commun sans rien dire tant que rien n'y est perdu (tcAdopt) ;
// si un groupe porte une route sur un autre théâtre, un bandeau demande (tcConflict, tcPaint) et l'export attend.
const KEY_THEATRE = 'mp_theatre_v1', TH_DEFAULT = 'Caucasus';
function thOk(id) { return typeof id === 'string' && THEATRES.indexOf(id) !== -1; }
function thReadKey() {
  try {
    const o = JSON.parse(localStorage.getItem(KEY_THEATRE));
    return isObj(o) && thOk(o.theatre) ? o.theatre : '';
  } catch (e) { return ''; }
}
function thWriteKey(id) {
  if (thReadKey() === id) return;       // déjà là : aucune écriture
  try { localStorage.setItem(KEY_THEATRE, JSON.stringify({ theatre: id })); } catch (e) { if (!TH_SAVE_FAILED) { TH_SAVE_FAILED = true; try { showToast(t('toast.saveFail'), { type: 'err', ms: 6000 }); } catch (e2) { /* page pas encore prête */ } } }
}
let TH_SAVE_FAILED = false;
// Au chargement : la clé partagée, sinon le théâtre de la fiche des groupes, sinon celui de la route enregistrée, sinon le Caucase (le défaut du Route Planner)
function thInitial() {
  const k = thReadKey();
  if (k) return k;
  const g = gsRead();
  if (g && thOk(g.theatre)) return g.theatre;
  const rt = rpRead().state.theatre;
  return thOk(rt) ? rt : TH_DEFAULT;
}
// La liste de la barre : les quatorze théâtres, dans la langue de l'interface, au théâtre commun
function thFill() {
  const s = document.getElementById('theatre');
  if (!s) return;
  s.setAttribute('aria-label', t('tb.theatre'));
  s.innerHTML = THEATRES.map(id => '<option value="' + id + '">' + esc(t('th.' + id)) + '</option>').join('');
  s.value = S.theatre;
}
// Un théâtre choisi dans la barre, ou venu de l'autre module (fromKey : il n'est pas réécrit) : la fiche le prend ou le bandeau se pose
function thSet(id, fromKey) {
  if (!thOk(id)) return;
  const sel = document.getElementById('theatre');
  if (sel && sel.value !== id) sel.value = id;
  const changed = id !== S.theatre;
  S.theatre = id;
  if (!fromKey) thWriteKey(id);
  if (!changed) return;
  UI.rtChoose = null;
  tcAdopt();
  routeChanged();
}
// L'autre module a écrit mp_theatre_v1
function thFollow() {
  const k = thReadKey();
  if (k && k !== S.theatre) thSet(k, true);
}
// Le bandeau : la fiche (F) est sur un autre théâtre que l'écran (C) et au moins un groupe porte une route (des points lisibles, ou un lien avec le Route Planner). Rend { F, C } ou null.
function tcConflict() {
  const F = GS.live ? GS.theatre : '', C = S.theatre;
  if (F === '' || F === C || !S.flights.length) return null;
  return S.flights.some(f => hasRoute(f)) ? { F: F, C: C } : null;
}
// Rien à perdre : la fiche prend le théâtre commun, sans rien dire
function tcAdopt() {
  if (!GS.live || GS.theatre === S.theatre || tcConflict()) return;
  if (gsSetTheatre(S.theatre)) GS.theatre = S.theatre;
}
function tcPaint() {
  const box = document.getElementById('fc-tc'), tc = tcConflict();
  if (!box) return;
  if (!tc) { if (!box.hidden) { box.hidden = true; box.textContent = ''; box.removeAttribute('data-k'); } return; }
  const html = `<p class="rt-note rt-warn">${esc(tf('tc.banner', theatreName(tc.F), theatreName(tc.C)))}</p>
    <div class="miz-btn-row"><button type="button" class="miz-btn fc-small" data-act="tc-back">${esc(tf('tc.back', theatreName(tc.F)))}</button><button type="button" class="miz-btn fc-small" data-act="tc-keep">${esc(tf('tc.keep', theatreName(tc.C)))}</button></div>`;
  if (box.getAttribute('data-k') !== html) { box.innerHTML = html; box.setAttribute('data-k', html); }
  box.hidden = false;
}
// Bouton 1 : on repasse sur le théâtre de la fiche (le Route Planner et le Datacard Generator suivent)
function tcBack() {
  const tc = tcConflict();
  if (tc) thSet(tc.F);
}
// Bouton 2 : on garde le théâtre commun ; chaque groupe de la fiche perd sa route et son lien (le reste du groupe ne bouge pas), la fiche prend le théâtre commun, en une seule écriture
function tcKeep() {
  const tc = tcConflict(), g = gsRead();
  if (!tc || !g) return;
  g.flights.forEach(raw => { delete raw.route; delete raw.routeLink; });
  if (!gsWrite(S.theatre, g.flights)) return;
  S.flights.forEach(f => { f.route = null; delete f.routeLink; GS.seen[f.fcId] = gsStable(f); });
  GS.theatre = S.theatre;
  UI.rtChoose = null;
  renderAll();
  commitNow();
}

// ---------- Stockage : jamais requis, tout accès en try/catch ----------
function lsGet(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }
function lsSet(k, v) { try { localStorage.setItem(k, v); } catch (e) { /* l'écran marche sans */ } }

// La frappe est regroupée (400 ms) ; mais l'état part aussi sans attendre dès que la page se masque ou se ferme (flushWork, branché dans init).
let _saveTimer = 0;
function writeState() {
  _saveTimer = 0;
  let ok = false;
  try { ok = gsPush(); } catch (e) { ok = false; }
  try { tcAdopt(); } catch (e) { /* l'écran marche sans */ }
  // fc_state_v1 ne perd ses groupes qu'une fois la fiche écrite avec eux : sinon il reste à l'état d'avant (v1, state.flights) et la fiche est retentée à la prochaine écriture
  try { lsSet(KEY_STATE, JSON.stringify(ok ? { v: 2, sel: S.sel, mine: LIB.mine } : fcV1Doc())); } catch (e) { /* l'écran marche sans */ }
}
// L'état d'avant (v1, groupes compris) ; gsMigrateFailed (une migration a déjà échoué) est gardé : la migration retentée ne refait que l'étape 1
function fcV1Doc() {
  const d = { v: 1, state: S, mine: LIB.mine };
  if (GS.mf) d.gsMigrateFailed = true;
  return d;
}
function saveWork() {
  clearTimeout(_saveTimer);
  _saveTimer = setTimeout(writeState, 400);
}
function flushWork() {
  if (!_saveTimer) return;       // rien en attente : un onglet resté inactif n'écrase pas le travail d'un autre
  clearTimeout(_saveTimer);
  writeState();
}
// Un geste qui compte pour l'autre module (route choisie ou retirée, groupe ajouté ou retiré) s'écrit sans attendre.
function commitNow() {
  clearTimeout(_saveTimer);
  writeState();
}

// ----- La fiche partagée (flight_set_v1) -----
// GS.seen : fcId → texte stable (gsStable) du groupe tel qu'on l'a lu ou écrit la dernière fois. writeState n'écrit que les groupes qui diffèrent (gsPutFlight relit la clé, ne remplace que ce groupe),
// retire ceux que le module a supprimés (gsRemoveFlight) et pose le théâtre s'il a changé. Un groupe que le module ne montre pas (une unité d'un type hors de PAYLOAD_TYPES) n'y figure jamais : il n'est jamais touché.
const GS = { seen: {}, theatre: '', live: false, removed: [], mf: false, base: {} };       // base : sans fiche, chaque groupe tel que le module l'a lu sur le disque à son chargement       // live : la fiche existe et le module la suit (sinon fc_state_v1 v1 porte les groupes)
function gsMarkAll() {
  GS.seen = {};
  S.flights.forEach(f => { GS.seen[f.fcId] = gsStable(f); });
  const g = gsRead();
  GS.theatre = g ? g.theatre : '';       // le théâtre de la fiche, tel qu'on vient de la lire : il n'est plus celui de l'écran
  GS.live = true;
}
// Une unité de la fiche qui porte encore un emport brut (payloadIn, écrit par le Route Planner à son import) : restoreFlight l'a converti ; GS.seen garde alors le texte lu tel quel.
// Rend vrai s'il y a un groupe à réécrire : gsFixRaw le fait.
function gsHasRawLoadout(raw) { return isObj(raw) && Array.isArray(raw.units) && raw.units.some(u => isObj(u) && isObj(u.payloadIn)); }
function gsMarkRaw() {
  const g = gsRead();
  let any = false;
  if (g) g.flights.forEach(raw => { if (gsHasRawLoadout(raw) && has(GS.seen, raw.fcId)) { GS.seen[raw.fcId] = gsStable(raw); any = true; } });
  return any;
}
// Écrit la conversion : la fiche est relue à l'instant, et dans chaque groupe qui porte un emport brut seuls les champs loadout et payloadIn des unités concernées changent
// (jamais route, routeLink ni un autre champ, qu'une copie plus ancienne du module aurait périmés). Un groupe que la fiche a changé depuis la lecture est laissé : son événement storage
// ramènera le module. Rend faux si une écriture a échoué (GS.seen garde alors le texte brut : la prochaine écriture du module reprend la conversion).
function gsFixRaw() {
  const g = gsRead();
  let ok = true;
  if (!g) return false;
  g.flights.forEach(raw => {
    if (!gsHasRawLoadout(raw) || GS.seen[raw.fcId] !== gsStable(raw)) return;
    const f = S.flights.filter(x => x.fcId === raw.fcId)[0];
    if (!f) return;
    const out = clone(raw);
    let i = 0;
    out.units.forEach(u => {
      if (!isObj(u)) return;
      const mu = f.units[i++];
      if (!isObj(u.payloadIn)) return;
      u.loadout = mu && mu.loadout ? clone(mu.loadout) : null;
      delete u.payloadIn;
    });
    if (gsPutFlight(out)) GS.seen[raw.fcId] = gsStable(f); else ok = false;
  });
  return ok;
}
// Un groupe de la fiche que le module a changé : fusion à trois. base = ce qu'on a lu ou écrit la dernière fois (GS.seen), mien = la copie du module, leur = la fiche relue ;
// pour chaque clé de premier niveau, mien si elle a changé depuis base, sinon leur ; route et routeLink vont ensemble. Rien n'a changé : on n'écrit pas.
function gsMerge(f) {       // GS.seen[fcId] doit porter la base
  const mine = clone(f), g = gsRead();
  const theirs = g ? g.flights.filter(x => x.fcId === f.fcId)[0] : null;
  if (!theirs || !has(GS.seen, f.fcId)) return gsPutFlight(mine);
  const base = JSON.parse(GS.seen[f.fcId]), out = clone(theirs);
  const changed = k => gsStable(has(mine, k) ? mine[k] : undefined) !== gsStable(has(base, k) ? base[k] : undefined);
  const routeSide = changed('route') || changed('routeLink');
  Object.keys(mine).concat(Object.keys(base)).forEach(k => {
    if (!(k === 'route' || k === 'routeLink' ? routeSide : changed(k))) return;
    if (has(mine, k)) out[k] = mine[k]; else delete out[k];
  });
  return gsPutFlight(out);
}
// La fiche n'existe pas (le stockage l'a refusée, ou le Route Planner ne l'a pas encore créée) : l'état d'avant (v1) est remis à jour, la migration retentée ; si la fiche est là, le module la reprend telle quelle.
// Rend vrai si le module suit la fiche.
function gsAdopt(quiet) {
  if (gsRead() === null) {
    try { lsSet(KEY_STATE, JSON.stringify(fcV1Doc())); } catch (e) { /* l'écran marche sans */ }
    gsMigrate(gsPackFn);
  }
  let gs = gsRead();
  if (!gs) { GS.mf = true; return false; }
  // le module n'adopte une fiche qu'avec ses groupes : ceux de l'état d'avant (v1) qui n'y sont pas y sont versés d'abord ; sinon l'adoption est retentée
  if (!GS.live) {
    let all = true;
    S.flights.forEach(f => {
      if (!gs.flights.some(x => x.fcId === f.fcId)) { if (!gsPutFlight(clone(f))) all = false; return; }
      if (!has(GS.base, f.fcId)) return;       // groupe présent des deux côtés : fusion à trois, ce que le module a changé depuis sa lecture l'emporte
      GS.seen[f.fcId] = GS.base[f.fcId];
      if (!gsMerge(f)) all = false;
    });
    if (!all) return false;
    gs = gsRead();
    if (!gs) return false;
  }
  const folds = {};
  S.flights.forEach(f => { if (UI.fold.has(f)) folds[f.fcId] = UI.fold.get(f); });
  restoreState({ theatre: gs.theatre, flights: gs.flights, sel: S.sel });
  S.flights.forEach(f => { if (has(folds, f.fcId)) UI.fold.set(f, folds[f.fcId]); });
  gsMarkAll();
  if (gsMarkRaw()) gsFixRaw();       // l'emport brut que la fiche portait est converti et écrit dès l'adoption
  GS.base = {};
  try { lsSet(KEY_STATE, JSON.stringify({ v: 2, sel: S.sel, mine: LIB.mine })); } catch (e) { /* l'écran marche sans */ }
  if (!quiet) renderAll();
  return true;
}
// Rend vrai si tout ce que le module a changé est dans la fiche.
function gsPush() {
  if (!GS.live) return gsAdopt();
  let ok = true;
  S.flights.forEach(f => {
    const j = gsStable(f);
    if (GS.seen[f.fcId] === j) return;
    if (gsMerge(f)) GS.seen[f.fcId] = j; else ok = false;
  });
  // seuls les groupes que l'utilisateur a supprimés (removeFlight) sont retirés de la fiche
  GS.removed = GS.removed.filter(id => {
    if (S.flights.some(f => f.fcId === id)) return false;
    if (gsRemoveFlight(id)) { delete GS.seen[id]; return false; }
    ok = false;
    return true;
  });
  return ok;
}
// Ce que les autres ont écrit : les groupes changés sont remplacés, les nouveaux ajoutés (à leur place dans la fiche), ceux qui ont disparu retirés ; la sélection reste sur le même groupe (sinon le premier).
// Un groupe en cours d'écriture locale s'écrit d'abord. Rend vrai si l'écran a changé (il est redessiné).
function gsPull() {
  flushWork();
  if (!GS.live) return gsRead() !== null && gsAdopt();
  const gs = gsRead();
  if (!gs) return false;
  const selId = S.flights[S.sel.f] ? S.flights[S.sel.f].fcId : null, byId = {}, inSet = {}, out = [], taken = [];
  S.flights.forEach(f => { byId[f.fcId] = f; });
  let changed = false, rewrite = false;
  gs.flights.forEach(raw => {
    inSet[raw.fcId] = true;
    const nf = restoreFlight(raw);
    if (!nf) { if (has(GS.seen, raw.fcId)) { delete GS.seen[raw.fcId]; changed = true; } return; }       // un groupe que le module ne sait pas lire : ni montré ni touché
    const cur = byId[raw.fcId], j = gsStable(nf);
    if (cur && (GS.seen[raw.fcId] === j || gsStable(cur) !== GS.seen[raw.fcId])) { out.push(cur); return; }
    if (cur && UI.fold.has(cur)) UI.fold.set(nf, UI.fold.get(cur));
    if (cur) refusedCarry(cur, nf);
    if (cur && cur.routeLink && nf.routeLink && cur.routeLink.rid === nf.routeLink.rid && (cur.routeLink.name !== nf.routeLink.name || JSON.stringify(cur.route ? cur.route.points : null) !== JSON.stringify(nf.route ? nf.route.points : null))) taken.push({ nf: nf, name: nf.routeLink.name });      // le Route Planner a repris la route de ce groupe
    GS.seen[raw.fcId] = j;
    if (gsHasRawLoadout(raw)) { GS.seen[raw.fcId] = gsStable(raw); rewrite = true; }       // l'emport brut est converti : gsFixRaw l'écrit, sans payloadIn
    out.push(nf);
    changed = true;
  });
  S.flights.forEach(f => {
    if (out.indexOf(f) >= 0 || inSet[f.fcId]) return;         // gardé, ou remplacé par sa version de la fiche : son état lu reste
    if (!has(GS.seen, f.fcId)) { out.push(f); return; }       // jamais écrit (le stockage a refusé) : gardé
    delete GS.seen[f.fcId];
    changed = true;
  });
  if (out.some((f, i) => f !== S.flights[i]) || out.length !== S.flights.length) changed = true;
  if (GS.theatre !== gs.theatre) changed = true;       // la fiche a changé de théâtre : le bandeau se réévalue
  GS.theatre = gs.theatre;
  if (!changed) return false;
  S.flights = out;
  const k = selId === null ? -1 : out.findIndex(f => f.fcId === selId);
  S.sel = k >= 0 ? { f: k, u: S.sel.u } : { f: 0, u: 0 };
  if (!S.flights[S.sel.f] || !S.flights[S.sel.f].units[S.sel.u]) S.sel.u = 0;
  if (UI.rtChoose !== null && !S.flights.some(f => f.fcId === UI.rtChoose)) UI.rtChoose = null;
  if (k < 0) Object.assign(UI.cmp, { saving: false, err: '', st: null });       // une saisie en cours (nom de preset) ne se perd que si le groupe choisi a disparu
  renderAll();
  if (rewrite) gsFixRaw();
  tcAdopt();
  if (taken.length && document.visibilityState === 'visible') {
    const lab = taken.map(x => flightLabel(x.nf, S.flights.indexOf(x.nf)));
    showToast(taken.length === 1 ? tf('route.toast.one', taken[0].name.trim() !== '' ? taken[0].name : t('route.unnamed'), lab[0]) : tf('route.toast.many', lab.join(', ')), 4500);
  }
  return true;
}
// Un autre onglet écrit la fiche en plusieurs temps (un groupe, puis le lien de sa route) et le stockage met un instant à arriver d'un onglet à l'autre : le module relit après 300 ms de calme
// (la minuterie repart à chaque événement), pour ne pas convertir ni réécrire sur un état à moitié écrit.
function gsStorage(e) {
  if (e.key !== null && e.key !== KEY_FLIGHT_SET) return;
  clearTimeout(gsStorage._h);
  gsStorage._h = setTimeout(gsPull, 300);
}
// La migration prend les points d'une route lue brute au format du paquet (gsPackRoute du bloc partagé), à la vitesse sol du Route Planner
function gsPackFn(r, th) { return gsPackRoute(r, th, rpRead().state.gs); }
// Un échec d'écriture de la fiche (stockage plein), dit une fois par série d'échecs
function gsOnSaveFail() { showToast(tf('toast.gsFull'), { type: 'err', ms: 6000 }); }
const UNIT_KEYS = ['type', 'name', 'callsign', 'csRaw', 'onboard', 'livery', 'folded', 'radios', 'loadout', 'payloadIn'];       // payloadIn : l'emport brut d'un import, converti ici et jamais gardé
// Un vol de l'état : en v1 (fc_state_v1, fichier de travail d'avant) le type est au vol et chaque unité le prend ; en v2 chaque unité porte le sien.
// Un vol dont une unité a un type non vide hors de PAYLOAD_TYPES est écarté ; une unité sans type ('' : à choisir) et un groupe sans unité (né au Route Planner) sont valides.
function restoreFlight(f) {       // un groupe sans fcId en reçoit un par restoreState (gsLegacyIds) ; ici un identifiant au hasard seulement en dernier recours
  if (!isObj(f)) return null;
  const rawUnits = (Array.isArray(f.units) ? f.units : []).filter(isObj).slice(0, MAX_UNITS);
  const types = rawUnits.map(u => (typeof u.type === 'string' ? u.type : (typeof f.type === 'string' ? f.type : '')));
  if (types.some(x => x !== '' && PAYLOAD_TYPES.indexOf(x) < 0)) return null;
  const nf = newFlight();
  Object.keys(f).forEach(k => { if (['name', 'type', 'coalition', 'route', 'routeLink', 'units'].indexOf(k) < 0) nf[k] = f[k]; });
  if (typeof nf.fcId !== 'string' || nf.fcId === '') nf.fcId = newId();
  nf.name = str(f.name);
  nf.coalition = (f.coalition === 'blue' || f.coalition === 'red') ? f.coalition : '';
  nf.route = (isObj(f.route) && isObj(f.route.points)) ? gsRouteCopy(f.route.points, f.route.missionDate) : null;       // la date reçue avec la route (missionDate) la suit
  if (nf.route && isObj(f.routeLink) && ridOk(f.routeLink.rid)) nf.routeLink = { rid: f.routeLink.rid, name: str(f.routeLink.name) };       // le lien avec le Route Planner ne se garde que s'il y a une route
  nf.units = rawUnits.map((u, i) => {
    const nu = newUnit(types[i]);
    nu.name = str(u.name); nu.callsign = str(u.callsign); nu.csRaw = u.csRaw; nu.onboard = str(u.onboard); nu.livery = str(u.livery);
    nu.folded = u.folded === true;          // carte repliée : un état d'écran, gardé avec le travail, jamais dans le paquet
    nu.radios = isObj(u.radios) ? u.radios : {};
    Object.keys(u).forEach(k => { if (UNIT_KEYS.indexOf(k) < 0) nu[k] = u[k]; });       // une clé inconnue d'une unité est gardée telle quelle
    nu.loadout = (isObj(u.loadout) && isObj(u.loadout.pylons)) ? u.loadout : null;
    if (nu.loadout) LO_FIELDS.forEach(k => { const c = clampNum(nu.loadout[k], 0, loLimit(nu.type, k), k !== 'fuel'); if (c.v !== null) nu.loadout[k] = c.v; });
    if (nu.loadout && !nu.loadout.base && !nu.loadout.modified && nu.loadout.key !== '~empty') nu.loadout.base = loSnap(nu.loadout);      // un emport d'avant le lot, non modifié : son contenu présent est sa source     // un fichier de travail édité : jamais de valeur négative
    if (isObj(u.payloadIn) && nu.type !== '') { const lo = loadoutFromPayload(nu.type, u.payloadIn); if (lo) nu.loadout = lo; }       // l'emport brut d'un import (bloc d'import commun) devient l'emport « importé », limites comprises
    return nu;
  });
  if (!nf.units.length && PAYLOAD_TYPES.indexOf(f.type) >= 0) nf.units.push(newUnit(f.type));       // un vol d'avant (le type au vol, sans unité) reprend une unité ; un groupe sans unité en reste sans
  return nf;
}
function restoreState(st) {
  if (!isObj(st) || !Array.isArray(st.flights)) return false;
  S.flights = gsLegacyIds(st.flights).map(restoreFlight).filter(Boolean);       // un groupe sans fcId, ou au fcId déjà pris, reçoit le même identifiant ('fv1' + rang) qu'à la migration : aucun groupe n'est écarté
  const sel = st.sel;
  S.sel = (isObj(sel) && Number.isInteger(sel.f) && Number.isInteger(sel.u)) ? { f: sel.f, u: sel.u } : { f: 0, u: 0 };
  const sf = S.flights[S.sel.f];
  if (!sf) S.sel = { f: 0, u: 0 }; else if (!sf.units[S.sel.u]) S.sel.u = 0;
  return true;
}

// ---------- 2. Modèle : vols, unités, radios, emport, livrée, résumé ----------
function newId() { return gsNewId(); }       // l'identifiant d'un groupe est celui du bloc partagé
// Chaque vol porte un fcId stable, jamais écrit dans le paquet : un vol renommé reste le même vol pour les liens avec le Route Planner et le Datacard Generator.
const DEFAULT_TYPE = 'Mi-24P';      // la première unité d'un vol neuf ; une unité ajoutée prend le type de la dernière de son vol
// newUnit(type) et csText(v) sont définis par le bloc d'import commun ; sans type donné, le type par défaut (Mi-24P) ; '' : une unité sans type.
function newFlight() { return { fcId: newId(), name: '', coalition: '', route: null, units: [newUnit()] }; }

function flightLabel(f, fi) { return f.name.trim() || tf('fl.title', fi + 1); }
// Le type d'une unité d'un vol lu (paquet ou mission, v1 ou v2) : le sien, sinon, en v1, celui du vol (aircraftType) ; '' si aucun.
function unitTypeOf(f, u) { return isObj(u) && typeof u.type === 'string' && u.type !== '' ? u.type : (isObj(f) && typeof f.aircraftType === 'string' ? f.aircraftType : ''); }
// Les types d'un vol lu, distincts, dans l'ordre de ses unités (un vol v1 sans unité garde son aircraftType) ; leur texte : « Mi-24P + Mi-8MT » (vide si aucune unité n'a de type).
function flightTypes(f) {
  const out = [], us = (isObj(f) && Array.isArray(f.units) ? f.units : []).filter(isObj);
  us.forEach(u => { const x = unitTypeOf(f, u); if (x !== '' && out.indexOf(x) < 0) out.push(x); });
  if (!us.length && isObj(f) && typeof f.aircraftType === 'string' && f.aircraftType !== '') out.push(f.aircraftType);
  return out;
}
function flightTypesLabel(f) { return flightTypes(f).join(' + '); }
// Les types d'un vol du module, dans l'ordre des unités, distincts, avec le nom d'affichage de chacun.
function modTypes(f) { const out = []; f.units.forEach(u => { if (out.indexOf(u.type) < 0) out.push(u.type); }); return out; }
// Le nom d'un type ; '' (une unité sans type, à choisir) se dit « type à choisir ».
function typeLabel(x) { return x === '' ? t('sum.type.pick') : (TYPE_LABEL[x] || x); }
function modTypesLabel(f) { return modTypes(f).map(typeLabel).join(' + '); }
// Un nom de vol se compare rogné des deux côtés ; la casse compte (« Hind 1 » et « HIND 1 » sont deux vols).
function nameKey(s) { return String(s).trim(); }
function unitDefaultName(f, fi, ui) { return flightLabel(f, fi) + '-' + (ui + 1); }
function unitLabel(f, fi, u, ui) { return u.name.trim() || unitDefaultName(f, fi, ui); }
function selUnit() {
  const f = S.flights[S.sel.f], u = f && f.units[S.sel.u];
  return u ? { f: f, fi: S.sel.f, u: u, ui: S.sel.u } : null;
}

// Indicatif (csText est celui du bloc d'import) : un nombre s'écrit en nombre, un texte en { name } ; une table importée est gardée telle quelle tant que le champ ne change pas.
function csValue(u) {
  if (u.csRaw !== undefined && u.csRaw !== null && csText(u.csRaw) === u.callsign) return u.csRaw;
  const x = u.callsign.trim();
  if (x === '') return null;
  return /^\d+$/.test(x) ? Number(x) : { name: x };
}

// ----- Radios -----
function radioPosts(type) { return radioPostsOf(type); }
// Un poste que la mission ne pré-règle pas : ses entrées sont des fréquences, sans numéro de canal.
function radioIsFree(type, r) { return radioFreeCount(type, r) > 0; }
// Une saisie refusée (hors de la bande du poste, ou qui n'est pas un nombre) n'est jamais écrite dans la fiche : la fiche garde la valeur d'avant. Le texte refusé ne vit qu'ici, dans la page ouverte,
// attaché à l'objet de l'unité (jamais à un rang) : « poste|canal » → texte tapé. Le champ le montre, marqué, et l'export reste bloqué tant qu'il en montre un ; il disparaît avec l'unité, au rechargement,
// au changement de type, à « Recopier » (qui copie la fiche) et quand la fiche change ce canal ailleurs (import, Datacard Generator). Une fréquence hors bande déjà dans la fiche n'a rien à voir avec lui.
const REFUSED = new WeakMap();
function refusedGet(u, r, c) { const m = REFUSED.get(u); return m && has(m, r + '|' + c) ? m[r + '|' + c] : undefined; }
function refusedSet(u, r, c, text) { let m = REFUSED.get(u); if (!m) { m = {}; REFUSED.set(u, m); } m[r + '|' + c] = text; }
function refusedClear(u, r, c) { const m = REFUSED.get(u); if (m) { delete m[r + '|' + c]; if (!Object.keys(m).length) REFUSED.delete(u); } }
// Ce que le champ montre : le texte refusé s'il y en a un, sinon la valeur de la fiche.
function chanShown(u, r, c) { const t = refusedGet(u, r, c); return t !== undefined ? t : chanValue(u, r, c); }
// La fiche a été relue (un autre module l'a écrite) : les textes refusés d'une unité ne suivent que si le groupe a les mêmes unités, du même type, et que le canal n'a pas changé dans la fiche.
function refusedCarry(cur, nf) {
  if (cur.units.length !== nf.units.length) return;
  cur.units.forEach((cu, i) => {
    const m = REFUSED.get(cu), nu = nf.units[i];
    if (!m || cu.type !== nu.type) return;
    Object.keys(m).forEach(k => { const p = k.split('|'); if (chanValue(cu, p[0], p[1]) === chanValue(nu, p[0], p[1])) refusedSet(nu, p[0], p[1], m[k]); });
  });
}
function chanValue(u, r, c) { return (u.radios[r] && u.radios[r][c] !== undefined) ? String(u.radios[r][c]) : ''; }
function parseFreq(s) {
  const x = String(s).trim().replace(',', '.');
  if (x === '') return { empty: true };
  return /^\d+(\.\d+)?$/.test(x) ? { v: Number(x) } : { nan: true };
}
function fmtMHz(v) { return String(v).replace('.', CURRENT_LANG === 'fr' ? ',' : '.'); }
// La bande d'un poste : radioBand (radio_bands_block.py), [[bas, haut], …] ; dans la bande = dans l'un de ses intervalles (bornes comprises).
function inBand(band, v) { return radioInBand(band, v); }
// La bande en clair, comme sous le titre du poste, de la forme « bas–haut · bas–haut MHz ».
function bandText(type, r) { return radioBand(type, r).map(b => fmtMHz(b[0]) + '–' + fmtMHz(b[1])).join(' · ') + ' MHz'; }
// Les attributs min et max d'un champ : la bande la plus large du poste.
function bandHull(type, r) {
  const b = radioBand(type, r);
  return [Math.min.apply(null, b.map(x => x[0])), Math.max.apply(null, b.map(x => x[1]))];
}
// Défauts d'un poste : { first (le premier message), bad (les canaux fautifs), block (ceux dont le champ montre un texte refusé : ils bloquent l'export) }. Une fréquence hors de la bande du poste ou non numérique est signalée ;
// celle de la fiche ne bloque pas, le texte refusé (jamais écrit) bloque.
// Un poste non pré-réglé nomme ses entrées « Fréquence n », jamais « Canal n ».
function radioIssues(f, u, r) {
  const ty = u.type, free = radioIsFree(ty, r);
  const bad = [], block = [];
  let first = '';
  for (let c = 1; c <= radioSlotsOf(ty, r); c++) {
    const ref = refusedGet(u, r, c), raw = ref !== undefined ? ref : chanValue(u, r, c), p = parseFreq(raw), ch = free ? c : radioCockpitChannel(ty, r, c);
    let msg = '';
    if (p.nan) msg = tf(free ? 'rad.err.nan.f' : 'rad.err.nan', ch, raw);
    else if (p.v !== undefined && !inBand(radioBand(ty, r), p.v)) msg = tf(free ? 'rad.err.range.f' : 'rad.err.range', ch, fmtMHz(p.v), bandText(ty, r));
    if (msg) {
      bad.push(c); first = first || msg;
      if (ref !== undefined) block.push(c);
    }
  }
  return { first: first, bad: bad, block: block };
}
function radioCount(f, u) {
  let n = 0;
  radioPosts(u.type).forEach(r => { for (let c = 1; c <= radioSlotsOf(u.type, r); c++) if (chanValue(u, r, c).trim() !== '') n++; });
  return n;
}

// ----- Emport : réglages (carburant, leurres, paillettes, canon) bornés par la table de l'appareil -----
function loLimit(type, k) { return payloadDefaults(type)[k]; }     // le maximum est aussi la valeur par défaut
// Ramène une valeur dans [min, max] : { v: texte, n: 1 si elle a bougé } ; { v: null } si ce n'est pas un nombre. Les décimales en trop s'arrondissent sans compter.
function clampNum(raw, min, max, int) {
  const x = String(raw).trim().replace(',', '.');
  if (!/^-?\d+(\.\d+)?$/.test(x)) return { v: null, n: 0 };
  let n = Number(x), moved = 0;
  if (n < min) { n = min; moved = 1; } else if (n > max) { n = max; moved = 1; }
  n = int ? Math.round(n) : Math.round(n * 1000) / 1000;
  return { v: String(n), n: moved };
}
function cleanPylons(pylons) {
  const out = {};
  Object.keys(pylons).forEach(n => { if (isObj(pylons[n]) && typeof pylons[n].CLSID === 'string' && pylons[n].CLSID !== '') out[n] = clone(pylons[n]); });
  return out;
}
// Un emport d'unité : { key, label, src, modified, pylons, fuel, flare, chaff, gun } ; les réglages viennent de `prev` s'il y en a un, sinon des défauts de la table.
function makeLoadout(type, meta, pylons, prev) {
  const lo = { key: meta.key, label: meta.label, src: meta.src, modified: false, pylons: cleanPylons(pylons) };
  LO_FIELDS.forEach(k => { lo[k] = prev ? prev[k] : String(loLimit(type, k)); });
  if (meta.key !== '~empty') lo.base = loSnap(lo);
  return lo;
}
// « (modifié) » par comparaison : l'emport garde la photo de sa source (preset, copie, import) ; la puce dit qu'il en diffère (stations et réglages) et s'efface s'il lui redevient identique.
function loSnap(lo) { const o = { pylons: clone(cleanPylons(lo.pylons)) }; LO_FIELDS.forEach(k => { o[k] = lo[k]; }); return o; }
function stableJson(v) {
  if (Array.isArray(v)) return '[' + v.map(stableJson).join(',') + ']';
  if (isObj(v)) return '{' + Object.keys(v).sort().map(k => JSON.stringify(k) + ':' + stableJson(v[k])).join(',') + '}';
  return JSON.stringify(v);
}
function loSame(a, b) {
  if (stableJson(cleanPylons(a.pylons)) !== stableJson(cleanPylons(b.pylons))) return false;
  return LO_FIELDS.every(k => { const x = loNumber(a[k]), y = loNumber(b[k]); return (x !== undefined && y !== undefined) ? x === y : String(a[k]) === String(b[k]); });
}
// Recalcule la puce ; sans photo de la source (un état d'avant), elle garde ce qu'elle avait.
function loTouch(lo) { if (lo && lo.base) lo.modified = !loSame(lo, lo.base); }
function loadoutFromPayload(type, p) {
  if (!isObj(p) || !isObj(p.pylons)) return null;
  const pylons = {};
  Object.keys(p.pylons).forEach(k => { if (/^\d+$/.test(k)) pylons[k] = p.pylons[k]; });
  const lo = makeLoadout(type, { key: 'imp', label: t('lo.imported'), src: t('lo.src.imp') }, pylons, null);
  LO_FIELDS.forEach(k => {      // hors limites : ramené à la limite de la table, et compté à la ligne d'état
    const c = clampNum(p[k], 0, loLimit(type, k), k !== 'fuel');
    if (c.v !== null) { lo[k] = c.v; UI.clamped += c.n; }
  });
  lo.base = loSnap(lo);
  return lo;
}
// L'étiquette d'un emport copié suit la langue (« copié de Franken 1-1 ») ; les autres gardent celle qu'ils ont reçue.
function loLabel(lo) { return lo.key === 'copy' && typeof lo.from === 'string' ? tf('cmp.copied', lo.from) : lo.label; }
function loSrc(lo) { return lo.key === 'copy' ? t('lo.src.copy') : (lo.src || ''); }
function loadoutName(lo) { return lo ? loLabel(lo) + (lo.modified ? ' · ' + t('cmp.mod') : '') : t('u.loadout.none'); }
// Dans le résumé du vol replié seulement : « emport importé », « emport <nom> », suivis de « (modifié) » s'il l'est (le mot « emport » est déjà dans l'étiquette de l'emport importé).
function loadoutSummary(lo) {
  const name = lo.key === 'imp' ? lo.label : (lo.key === '~empty' ? t('sum.loadout.custom') : tf('sum.loadout', loLabel(lo)));
  return lo.modified ? name + ' (' + t('cmp.mod') + ')' : name;
}

// ----- Mes presets : un nom et des stations -----
function presetName(p) { return str(p.displayName) || str(p.name); }
// La clé d'un preset est son identifiant, donné à sa création (un preset ancien en reçoit un à la lecture) : elle ne dépend plus de son rang.
function newPresetId() { return 'p' + newId().slice(1); }
function presetsFor(type) {
  return (LIB.mine[type] || []).map(p => ({ key: 'm:' + p.id, label: presetName(p), preset: p, src: t('lo.src.mine') }));
}
// Le nom d'une arme tel qu'affiché : celui des tables, suivi de son côté quand payloadWeaponSide en donne un (« Kord 12.7mm HMG (gauche) »).
function weaponLabel(type, clsid) {
  const nm = payloadWeaponName(clsid);
  if (!nm) return nm;
  const side = payloadWeaponSide(type, clsid);
  return side ? nm + ' ' + t(side === 'L' ? 'w.left' : 'w.right') : nm;
}
function mineCount() { return PAYLOAD_TYPES.reduce((n, ty) => n + (LIB.mine[ty] || []).length, 0); }

// ----- Livrée : un <select>, jamais un texte libre -----
// La liste d'un type = les livrées du jeu (LIVERIES_DEFAULT, noms de DCS) et les livrées custom déclarées dans la fenêtre Wing de HQ
// (`liveries` de wing_config_v1) qui portent ce type ; sans doublon à la casse près (le nom du jeu l'emporte), triée sans casse.
const KEY_WING = 'wing_config_v1';
const WL = { stale: true, list: [], defs: {} };      // la lecture de wing_config_v1 (elle peut peser plusieurs Mo : logos) : faite au premier appel, refaite seulement après un évènement storage de sa clé (stale)
function wingRead() {
  if (!WL.stale) return WL;
  WL.stale = false;
  let o = null;
  try { o = JSON.parse(lsGet(KEY_WING) || 'null'); } catch (e) { o = null; }
  WL.list = isObj(o) && Array.isArray(o.liveries) ? o.liveries.filter(x => isObj(x) && typeof x.name === 'string' && Array.isArray(x.aircraft)) : [];
  WL.defs = isObj(o) && isObj(o.defaultLiveries) ? o.defaultLiveries : {};       // { type: nom } : la livrée par défaut de chaque type, déclarée dans la fenêtre Wing de HQ
  return WL;
}
function wingLiveries() { return wingRead().list; }
function liveriesFor(type) {
  const seen = new Set(), out = [];
  const add = n => { const k = n.toLowerCase(); if (n !== '' && !seen.has(k)) { seen.add(k); out.push(n); } };
  (impHas(LIVERIES_DEFAULT, type) ? LIVERIES_DEFAULT[type] : []).forEach(add);
  wingLiveries().forEach(x => { if (x.aircraft.indexOf(type) >= 0) add(x.name.trim()); });
  return out.sort(livCmp);
}
function livCmp(a, b) { const x = a.toLowerCase(), y = b.toLowerCase(); return x < y ? -1 : (x > y ? 1 : (a < b ? -1 : (a > b ? 1 : 0))); }
// Le nom que le champ affiche : toujours un nom (c'est lui que le paquet emporte). Celui que l'utilisateur a choisi (u.livery) ; sinon, tant qu'il n'a rien
// choisi (u.livery reste ''), liveryAuto, qui suit la mission ouverte dans HQ et la configuration Wing.
function liveryValue(u) { return u.livery.trim(); }
const MS = { stale: true, flights: [] };      // la lecture de mission_snapshot_v1 (la mission ouverte dans HQ) : faite au premier appel, refaite seulement après un évènement storage de sa clé (stale)
function missionFlights() {
  if (!MS.stale) return MS.flights;
  MS.stale = false;
  let o = null;
  try { o = JSON.parse(lsGet(KEY_HQ_MISSION) || 'null'); } catch (e) { o = null; }
  MS.flights = isObj(o) && o.schema === 'dcs-mission-snapshot-v2' && Array.isArray(o.flights) ? o.flights.filter(isObj) : [];
  return MS.flights;
}
// La livrée de l'unité dans la mission ouverte dans HQ, comme HQ la retrouve à l'application du paquet : le groupe Client de même nom (rogné, casse exacte) et, si le vol
// a une coalition, de même coalition — un seul, sinon rien ; les unités du groupe d'abord par nom exact (celui que le paquet emporte), puis par rang parmi les restantes.
// Elle ne vaut que si l'unité de la mission a le même type et une livrée non vide.
function missionLivery(f, fi, u, ui) {
  const fname = f.name.trim();
  if (fname === '') return '';
  const groups = missionFlights().filter(g => typeof g.groupName === 'string' && g.groupName.trim() === fname && (f.coalition === '' || g.coalition === f.coalition));
  if (groups.length !== 1) return '';
  const tus = Array.isArray(groups[0].units) ? groups[0].units.filter(isObj) : [], used = new Set(), map = new Array(f.units.length).fill(null);
  f.units.forEach((x, i) => {
    const j = tus.findIndex((tu, k) => !used.has(k) && tu.name === unitLabel(f, fi, x, i));
    if (j >= 0) { used.add(j); map[i] = tus[j]; }
  });
  f.units.forEach((x, i) => {
    if (map[i]) return;
    const j = tus.findIndex((tu, k) => !used.has(k));
    if (j >= 0) { used.add(j); map[i] = tus[j]; }
  });
  const mu = map[ui];
  return mu && mu.type === u.type && typeof mu.liveryId === 'string' && mu.liveryId.trim() !== '' ? mu.liveryId.trim() : '';
}
// La livrée par défaut d'une unité qui a un type, dans l'ordre : celle de la mission d'HQ ; la livrée par défaut du type déclarée dans Wing (si elle est dans la liste du type,
// à la casse près : le nom s'écrit alors comme la liste) ; la première de la liste du type. '' sans type, ou si la liste est vide.
function liveryAuto(f, fi, u, ui) {
  if (u.type === '') return '';
  const m = missionLivery(f, fi, u, ui);
  if (m !== '') return m;
  const names = liveriesFor(u.type), defs = wingRead().defs, w = impHas(defs, u.type) && typeof defs[u.type] === 'string' ? defs[u.type].trim().toLowerCase() : '';
  const hit = w === '' ? undefined : names.find(n => n.toLowerCase() === w);
  return hit !== undefined ? hit : (names.length ? names[0] : '');
}
function liveryShown(f, fi, u, ui) { const v = liveryValue(u); return v !== '' ? v : liveryAuto(f, fi, u, ui); }
// Les options du champ d'une unité : la liste du type, sans « Inchangée » ; la valeur courante est le nom affiché. Le jeu lit les livrées sans tenir compte de la casse : une valeur égale
// à un nom de la liste à la casse près prend la place de ce nom (sa valeur, son libellé, à sa place dans le tri) : un seul nom, et l'export garde l'écriture de l'unité.
// Une valeur qu'aucun nom n'égale à la casse près reste une option hors liste, telle quelle, en tête. Seule une liste vide sans valeur garde « Inchangée » (repli).
function liveryOptions(f, fi, u, ui) {
  let names = liveriesFor(u.type);
  const cur = liveryShown(f, fi, u, ui), opts = [];
  if (cur !== '') {
    const k = names.findIndex(n => n.toLowerCase() === cur.toLowerCase());
    if (k >= 0) { names = names.slice(); names[k] = cur; names.sort(livCmp); }
    else opts.push({ v: cur, l: cur });
  } else opts.push({ v: '', l: t('u.livery.keep') });
  return opts.concat(names.map(n => ({ v: n, l: n })));
}
// La mission d'HQ, wing_config_v1 ou un nom a changé : les listes de livrées se refont sur place (celles de root, sinon de la page), le nom affiché suit ; une liste ouverte sur un champ refait se ferme.
function refreshLiveryLists(root) {
  (root || document.getElementById('col-left')).querySelectorAll('select[data-k="livery"]').forEach(sel => {
    const fe = sel.closest('.fc-flight'), fi = fe ? Number(fe.getAttribute('data-f')) : -1, f = S.flights[fi], ui = Number(sel.getAttribute('data-u')), u = f && f.units[ui];
    if (!u || u.type === '') return;
    if (TBM.cur && TBM.cur.sel === sel) tbmClose(false);
    fillLiverySelect(sel, f, fi, u, ui);
  });
}
// Les options d'un champ Livrée, refaites sur place : le nom affiché y reste choisi.
function fillLiverySelect(sel, f, fi, u, ui) { sel.innerHTML = optionsHtml(liveryOptions(f, fi, u, ui), liveryShown(f, fi, u, ui)); }

// ----- Les points d'une route du groupe (le paquet les porte tels quels) -----
function routeKeys(points) { return isObj(points) ? Object.keys(points).filter(k => /^\d+$/.test(k)).sort((a, b) => a - b) : []; }
function routePoints(points) {
  return routeKeys(points).map(k => {
    const p = isObj(points[k]) ? points[k] : {};
    return { name: (typeof p.name === 'string' && p.name !== '') ? p.name.replace(/\s+/g, ' ') : 'WP' + k, alt: p.alt };
  });
}
// ----- La route : choisie parmi celles du Route Planner, dessinée en croquis, suivie quand elle change là-bas -----
// Un groupe garde sa route (route: { points }, les points d'un paquet, inchangés) et, si elle vient du Route Planner, routeLink: { rid, name } (le nom au dernier passage).
// routeLink vit dans fc_state_v1 et le fichier de travail, jamais dans le paquet. Un groupe n'a qu'une route ; une même route du Route Planner peut servir à plusieurs groupes.
const KEY_RP_SET = 'route_set_v1', KEY_RP_STATE = 'route_state_v1', RP_SET_FORMAT = 'dcs-route-set-v1', RP_GS_DEFAULT = 220;
const ridOk = v => typeof v === 'string' && /^[a-z0-9]{6,32}$/.test(v);
function lsJson(k) { try { return JSON.parse(lsGet(k) || 'null'); } catch (e) { return null; } }
function hasRoute(f) { return !!(f && f.route && isObj(f.route.points) && routeKeys(f.route.points).some(k => { const p = f.route.points[k]; return isObj(p) && isNum(p.x) && isNum(p.y); })); }       // une route : au moins un point aux coordonnées lisibles (le test du Route Planner)
function ptsLabel(n) { return tf(n < 2 ? 'route.pts.one' : 'route.pts.many', n); }
// L'unité de distance partagée : mp_units_v1.distance (« km » ou « nm »), posée par le Route Planner ou le Datacard Generator. Le Flight Configurator la lit à l'ouverture et la suit (évènement « storage ») ; il ne l'écrit jamais. Clé absente ou distance invalide : « km » (le défaut du Route Planner et du Datacard Generator).
const KEY_UNITS = 'mp_units_v1';
let UDIST = 'km';
function udRead() {
  try { const o = JSON.parse(lsGet(KEY_UNITS) || 'null'); return isObj(o) && (o.distance === 'km' || o.distance === 'nm') ? o.distance : 'km'; } catch (e) { return 'km'; }
}
function udLabel() { return UDIST === 'km' ? 'km' : 'NM'; }
function fmtDist(nm) { return fmtNm(UDIST === 'km' ? nm * NAV_NM_KM : nm); }
// Le DG ou le RP a changé l'unité : les longueurs se redessinent, rien ne s'écrit
function udFollow() {
  const d = udRead();
  if (d === UDIST) return;
  UDIST = d;
  renderRouteBlock(); paintRouteLines();
}
function fmtNm(v) { const s = (Math.round(v * 10) / 10).toFixed(1); return CURRENT_LANG === 'fr' ? s.replace('.', ',') : s; }
function routeTitle(f) { return f.routeLink ? (f.routeLink.name.trim() !== '' ? f.routeLink.name : t('route.unnamed')) : t('route.imported'); }

// Ce que le Route Planner a rangé : ses routes (rid vide quand elle n'en a pas encore : le Route Planner en donne un à la prochaine ouverture) et ses réglages (théâtre, vitesse sol, affichage des caps)
function rpRead() {
  const st = lsJson(KEY_RP_STATE), set = lsJson(KEY_RP_SET), nd = isObj(st) && isObj(st.navDisplay) ? st.navDisplay : {};
  const state = {
    theatre: isObj(st) && typeof st.theatre === 'string' ? st.theatre : '',       // aucun théâtre par défaut : '' = le Route Planner n'a pas encore été ouvert ici
    gs: isObj(st) && isNum(st.groundSpeed) && st.groundSpeed > 0 ? st.groundSpeed : RP_GS_DEFAULT,
    nav: { mode: (nd.mode === 'calc' || nd.mode === 'manual') ? nd.mode : (parseDecl(str(nd.decl)) !== null ? 'manual' : 'calc'), decl: str(nd.decl), year: (typeof nd.year === 'string' && /^\d{1,4}$/.test(nd.year)) ? nd.year : '', force: nd.force === true }
  };
  const routes = [];
  if (isObj(set) && (set.format === undefined || set.format === RP_SET_FORMAT) && Array.isArray(set.routes)) {
    set.routes.forEach(r => {
      if (!isObj(r) || !Array.isArray(r.points)) return;
      const pts = r.points.filter(p => isObj(p) && packValidCoord(p.lat, p.lon));
      routes.push({ rid: ridOk(r.rid) ? r.rid : '', theatre: routeTheatre(r, thOk(state.theatre) ? state.theatre : S.theatre), name: str(r.name), points: pts, flight: (isObj(r.flight) && typeof r.flight.groupName === 'string') ? r.flight : null, missionDate: magRouteDate(r.missionDate) });       // une route d'avant le lot (sans theatre) : le théâtre de route_state_v1 s'il est valide, sinon le commun (mp_theatre_v1, Caucasus par défaut), comme le Route Planner l'écrira ; jamais écrite ici
    });
  }
  return { state: state, routes: routes };
}
// Les points d'un paquet pour une route du Route Planner : ceux que son paquet écrirait (même bloc packPoint)
function rpPack(rt, theatre, gs) {
  const o = {};
  rt.points.forEach((p, k) => { o[String(k + 1)] = packPoint(p, k, theatre, gs); });
  return o;
}
function rpUsable(rp) { return routesOfTheatre(rp.routes, S.theatre).filter(r => r.points.length >= 2); }       // seulement les routes du théâtre commun
// Une route du Route Planner est « liée à ce groupe » : même nom (rogné, sans casse) et, si le groupe a un camp, le même
function rtMatches(rt, f) {
  const fl = rt.flight, name = f.name.trim().toLowerCase();
  return !!fl && name !== '' && fl.groupName.trim().toLowerCase() === name && (f.coalition === '' || fl.coalition === f.coalition);
}

// Les points du groupe en latitude / longitude (ils se lisent de la route du groupe, jamais de route_set_v1) ; null sans théâtre lisible
// Le théâtre dans lequel les points d'un groupe sont écrits : celui de la fiche (F) tant que le bandeau est là, sinon le théâtre commun
function rTh() { const tc = tcConflict(); return tc ? tc.F : S.theatre; }
function routeGeo(f) {
  if (!f || !f.route || !has(TM_PARAMS, rTh())) return null;
  const pts = [];
  routeKeys(f.route.points).forEach(k => {
    const p = f.route.points[k];
    if (!isObj(p) || !isNum(p.x) || !isNum(p.y)) return;
    const ll = dcsToLl(rTh(), p.x, p.y);
    pts.push({ name: (typeof p.name === 'string' && p.name.trim() !== '') ? p.name.replace(/\s+/g, ' ').trim() : 'WP' + k, lat: ll.lat, lon: ll.lon });
  });
  return pts.length ? pts : null;
}
function routeNm(pts) { let km = 0; for (let i = 0; i + 1 < pts.length; i++) km += legCalc(pts[i], pts[i + 1]).km; return km / NAV_NM_KM; }
// La déclinaison : la valeur saisie au Route Planner (mode « manual », lisible), sinon le calcul de WMM et d'IGRF à la date de la mission ou à l'année du Route Planner
function declSource(nav, routeDate) {
  if (nav.mode === 'manual') { const v = parseDecl(nav.decl); if (v !== null) return { manual: true, v: v }; }
  return { manual: false, ys: magYearSource(rTh(), nav.year, nav.force, routeDate) };
}
// La date reçue avec la route d'un groupe (paquet ou mission de HQ) : '' sans date lisible
function routeDateOf(f) { return f && f.route ? magRouteDate(f.route.missionDate) : ''; }
function declAt(ds, lat, lon) { if (ds.manual) return ds.v; const d = magVar(lat, lon, ds.ys.y); return d === null ? 0 : d; }
// Les branches : cap initial vrai et distance par legCalc, cap magnétique = cap vrai − déclinaison au départ de la branche (toujours magnétique ici)
function routeLegs(pts, ds) {
  const legs = [];
  let total = 0;
  for (let i = 0; i + 1 < pts.length; i++) {
    const L = legCalc(pts[i], pts[i + 1]), d = declAt(ds, pts[i].lat, pts[i].lon), nm = L.km / NAV_NM_KM;
    total += nm;
    legs.push({ from: pts[i].name, to: pts[i + 1].name, hdg: fmtHdg(((L.brg - d) % 360 + 360) % 360), nm: nm });
  }
  return { legs: legs, total: total };
}
function declText(v) { return fmtNm(Math.abs(v)) + '° ' + (v < 0 ? 'W' : 'E'); }
function declNote(ds, pts) {
  let v;
  if (ds.manual) v = declText(ds.v);
  else {
    const all = pts.map(p => declAt(ds, p.lat, p.lon)), lo = Math.min.apply(null, all), hi = Math.max.apply(null, all);
    if (hi - lo < 0.2) v = declText(all[0]);
    else if ((lo < 0) === (hi < 0)) v = fmtNm(Math.min(Math.abs(lo), Math.abs(hi))) + '°' + t('route.decl.to') + declText(Math.abs(lo) > Math.abs(hi) ? lo : hi);
    else v = declText(lo) + t('route.decl.to') + declText(hi);
  }
  const src = ds.manual ? t('route.src.manual') : ds.ys.year + ', ' + t(ds.ys.src === 'mission' ? 'route.src.mission' : (ds.ys.src === 'route' ? 'route.src.route' : (ds.ys.src === 'default' ? 'route.src.default' : 'route.src.rp')));
  return tf('route.note', v, src);
}

// ----- Le croquis : une feuille de papier, un trait à main levée (graine fixe : le même croquis à chaque rendu) -----
const RT = { w: 0, ro: null, timer: 0 };
const RT_SEED = 20261106, RT_LBL_W = 7.2, RT_LBL_H = 14, RT_HD_W = 6.6, RT_HD_H = 13, RT_NM_PER_DEG = 60.04;
function rtRng(seed) {
  let a = seed >>> 0;
  return () => { a = (a + 0x6D2B79F5) >>> 0; let x = a; x = Math.imul(x ^ (x >>> 15), x | 1); x ^= x + Math.imul(x ^ (x >>> 7), x | 61); return ((x ^ (x >>> 14)) >>> 0) / 4294967296; };
}
const rn = v => String(Math.round(v * 10) / 10);
function rtCircle(x, y, r, rnd) {
  const n = 8, pts = [], ctl = [];
  for (let i = 0; i < n; i++) {
    const a = i * 2 * Math.PI / n, b = (i + 0.5) * 2 * Math.PI / n, ra = r * (1 + (rnd() * 2 - 1) * 0.08), rb = r / Math.cos(Math.PI / n) * (1 + (rnd() * 2 - 1) * 0.08);
    pts.push([x + ra * Math.cos(a), y + ra * Math.sin(a)]);
    ctl.push([x + rb * Math.cos(b), y + rb * Math.sin(b)]);
  }
  let d = 'M' + rn(pts[0][0]) + ' ' + rn(pts[0][1]);
  for (let i = 0; i < n; i++) { const q = pts[(i + 1) % n]; d += 'Q' + rn(ctl[i][0]) + ' ' + rn(ctl[i][1]) + ' ' + rn(q[0]) + ' ' + rn(q[1]); }
  return d + 'Z';
}
// Une branche à main levée : 4 courbes quadratiques, écarts perpendiculaires de ± amp px
function rtHand(a, b, rnd, amp) {
  const dx = b.x - a.x, dy = b.y - a.y, len = Math.hypot(dx, dy) || 1, nx = -dy / len, ny = dx / len;
  const off = () => (rnd() * 2 - 1) * amp, knot = [];
  for (let i = 1; i <= 4; i++) { const e = i === 4 ? 0 : off(); knot.push([a.x + dx * i / 4 + nx * e, a.y + dy * i / 4 + ny * e]); }
  let d = 'M' + rn(a.x) + ' ' + rn(a.y);
  for (let i = 1; i <= 4; i++) { const e = off(), tt = (i - 0.5) / 4; d += 'Q' + rn(a.x + dx * tt + nx * e) + ' ' + rn(a.y + dy * tt + ny * e) + ' ' + rn(knot[i - 1][0]) + ' ' + rn(knot[i - 1][1]); }
  return d;
}
const rtHit = (a, b) => a.x0 < b.x1 && b.x0 < a.x1 && a.y0 < b.y1 && b.y0 < a.y1;
function rtBoxAround(x, y, r) { return { x0: x - r, y0: y - r, x1: x + r, y1: y + r }; }
function rtFree(box, res, W, H) {
  if (box.x0 < 3 || box.y0 < 3 || box.x1 > W - 3 || box.y1 > H - 3) return false;
  const g = { x0: box.x0 - 1, y0: box.y0 - 1, x1: box.x1 + 1, y1: box.y1 + 1 };
  return !res.some(r => rtHit(g, r));
}
// Le croquis d'une route (pts : { name, lat, lon }) en <svg> ; mini : sans texte (vignette, carte du groupe) ; sinon la feuille entière.
// o : W (largeur, 1 unité = 1 px), title, phone, texts (« 044° · 10,9 » par branche) ; en mini aussi H, mx, my.
function rtSketch(pts, o) {
  const mini = !!o.mini, W = o.W, rnd = rtRng(RT_SEED), phone = !!o.phone;
  const mx = mini ? o.mx : (phone ? 60 : 100), my = mini ? o.my : 56, EPS = 1e-7;
  const lm = pts.reduce((a, p) => a + p.lat, 0) / pts.length, ck = Math.cos(lm * Math.PI / 180);
  const xs = pts.map(p => p.lon * ck), ys = pts.map(p => -p.lat);
  const x0 = Math.min.apply(null, xs), x1 = Math.max.apply(null, xs), y0 = Math.min.apply(null, ys), y1 = Math.max.apply(null, ys), dx = x1 - x0, dy = y1 - y0;
  let H, s;
  if (mini) { H = o.H; s = Math.min(dx > EPS ? (W - 2 * mx) / dx : Infinity, dy > EPS ? (H - 2 * my) / dy : Infinity); }
  else {
    const sw = dx > EPS ? (W - 2 * mx) / dx : Infinity, hMin = phone ? 230 : 300, hMax = phone ? 420 : 440;
    H = (dy > EPS && isFinite(sw)) ? Math.max(hMin, Math.min(hMax, dy * sw + 2 * my)) : hMin;
    s = Math.min(sw, dy > EPS ? (H - 2 * my) / dy : Infinity);
  }
  if (!isFinite(s)) s = 0;
  const ox = (W - dx * s) / 2 - x0 * s, oy = (H - dy * s) / 2 - y0 * s;
  const P = pts.map((p, i) => ({ x: xs[i] * s + ox, y: ys[i] * s + oy }));
  const amp = mini ? 0.7 : 1.5, rPt = mini ? 2.6 : 5.5, rStart = mini ? 3.4 : 7;
  // les branches, puis une flèche de sens aux 72 % de chacune
  let legs = '', arrows = '';
  for (let i = 0; i + 1 < P.length; i++) {
    const a = P[i], b = P[i + 1], d = rtHand(a, b, rnd, amp);
    legs += '<path class="rt-leg2" transform="translate(1.2 1)" d="' + d + '"/><path class="rt-leg" d="' + d + '"/>';
    const len = Math.hypot(b.x - a.x, b.y - a.y);
    if (len > (mini ? 6 : 24)) {
      const th = Math.atan2(b.y - a.y, b.x - a.x), tx = a.x + (b.x - a.x) * 0.72, ty = a.y + (b.y - a.y) * 0.72, al = mini ? 3 : 8, k = 25 * Math.PI / 180;
      arrows += '<path class="rt-arr" d="M' + rn(tx - al * Math.cos(th - k)) + ' ' + rn(ty - al * Math.sin(th - k)) + 'L' + rn(tx) + ' ' + rn(ty) + 'L' + rn(tx - al * Math.cos(th + k)) + ' ' + rn(ty - al * Math.sin(th + k)) + '"/>';
    }
  }
  // les points : un point qui retombe à moins de 4 px d'un point déjà dessiné ne se redessine pas, son nom s'ajoute à l'étiquette
  const drawn = [];
  P.forEach((p, i) => {
    const hit = drawn.filter(q => Math.hypot(q.x - p.x, q.y - p.y) < 4)[0];
    if (hit) { if (hit.names.indexOf(pts[i].name) < 0) hit.names.push(pts[i].name); }
    else drawn.push({ x: p.x, y: p.y, start: i === 0, names: [pts[i].name] });
  });
  let dots = '';
  drawn.forEach(q => {
    dots += '<path class="rt-pt" d="' + rtCircle(q.x, q.y, q.start ? rStart : rPt, rnd) + '"/>';
    if (q.start) dots += '<circle class="rt-start" cx="' + rn(q.x) + '" cy="' + rn(q.y) + '" r="' + (mini ? 1.3 : 2.6) + '"/>';
  });
  let extra = '', labels = '', numbers = '', heads = '';
  if (!mini) {
    const res = [];
    // le titre de la feuille, le nord et l'échelle
    const title = o.title || '';
    extra += '<text class="rt-gn" x="16" y="30">' + esc(title) + '</text>';
    res.push({ x0: 8, y0: 12, x1: 22 + title.length * 13, y1: 38 });
    extra += '<g class="rt-north"><line x1="' + (W - 32) + '" y1="64" x2="' + (W - 32) + '" y2="28"/><path d="M' + (W - 38) + ' 36L' + (W - 32) + ' 28L' + (W - 26) + ' 36"/></g><text class="rt-nn" x="' + (W - 32) + '" y="86">N</text>';
    res.push({ x0: W - 48, y0: 18, x1: W - 14, y1: 94 });
    const pxNm = UDIST === 'km' ? s / RT_NM_PER_DEG / NAV_NM_KM : s / RT_NM_PER_DEG, sizes = [1, 2, 5, 10, 20, 50, 100, 200, 500];
    let nm = 0;
    if (pxNm > 0) for (let i = 0; i < sizes.length; i++) if (sizes[i] * pxNm > 50) { nm = sizes[i]; break; }
    if (nm) {
      const L = nm * pxNm, yb = H - 20;
      extra += '<g class="rt-scale"><path d="M16 ' + (yb - 6) + 'V' + yb + 'H' + rn(16 + L) + 'V' + (yb - 6) + '"/><text x="' + rn(16 + L + 8) + '" y="' + (yb + 4) + '">' + nm + ' ' + udLabel() + '</text></g>';
      res.push({ x0: 10, y0: yb - 14, x1: 16 + L + 16 + String(nm).length * 7.2 + 24, y1: yb + 10 });
    }
    drawn.forEach(q => res.push(rtBoxAround(q.x, q.y, (q.start ? rStart : rPt) + 1.5)));
    // les numéros de branche (tablette) : au milieu de chaque branche, avant les étiquettes pour qu'elles les évitent
    const mids = [];
    for (let i = 0; i + 1 < P.length; i++) mids.push({ x: (P[i].x + P[i + 1].x) / 2, y: (P[i].y + P[i + 1].y) / 2 });
    if (!phone) mids.forEach((m, i) => {
      numbers += '<g class="rt-num"><circle cx="' + rn(m.x) + '" cy="' + rn(m.y) + '" r="8"/><text x="' + rn(m.x) + '" y="' + rn(m.y + 3.5) + '">' + (i + 1) + '</text></g>';
      res.push(rtBoxAround(m.x, m.y, 9));
    });
    // les noms : à l'opposé du centre de la route, à 14, 24 puis 36 px, dix directions ; un nom sans place libre se pose quand même
    const cx = drawn.reduce((a, q) => a + q.x, 0) / drawn.length, cy = drawn.reduce((a, q) => a + q.y, 0) / drawn.length;
    const offs = [0, 36, -36, 72, -72, 108, -108, 144, -144, 180].map(d => d * Math.PI / 180);
    const place = (q, ang, dist, w) => {
      const c = Math.cos(ang), sn = Math.sin(ang), ax = q.x + c * dist, ay = q.y + sn * dist;
      const bx = c > 0.35 ? ax : (c < -0.35 ? ax - w : ax - w / 2), by = sn > 0.35 ? ay : (sn < -0.35 ? ay - RT_LBL_H : ay - RT_LBL_H / 2);
      return { box: { x0: bx, y0: by, x1: bx + w, y1: by + RT_LBL_H }, anchor: c > 0.35 ? 'start' : (c < -0.35 ? 'end' : 'middle'), ax: ax, ay: ay };
    };
    const labelBoxes = [];
    drawn.forEach(q => {
      const text = q.names.join(' / ').toUpperCase(), w = text.length * RT_LBL_W + 2;
      const base = Math.hypot(q.x - cx, q.y - cy) < 1 ? -Math.PI / 2 : Math.atan2(q.y - cy, q.x - cx);
      let best = null, bd = 0;
      for (let di = 0; di < 3 && !best; di++) for (let oi = 0; oi < offs.length && !best; oi++) {
        const c = place(q, base + offs[oi], [14, 24, 36][di], w);
        if (rtFree(c.box, res, W, H)) { best = c; bd = [14, 24, 36][di]; }
      }
      if (!best) {
        best = place(q, base, 14, w); bd = 14;
        const b = best.box, shx = Math.max(3 - b.x0, Math.min(0, W - 3 - b.x1)), shy = Math.max(3 - b.y0, Math.min(0, H - 3 - b.y1));
        best.box = { x0: b.x0 + shx, y0: b.y0 + shy, x1: b.x1 + shx, y1: b.y1 + shy };
      }
      const b = best.box, tx = best.anchor === 'start' ? b.x0 : (best.anchor === 'end' ? b.x1 : (b.x0 + b.x1) / 2);
      if (bd >= 24) { const ang = Math.atan2(best.ay - q.y, best.ax - q.x), r = q.start ? rStart : rPt; labels += '<line class="rt-con" x1="' + rn(q.x + Math.cos(ang) * r) + '" y1="' + rn(q.y + Math.sin(ang) * r) + '" x2="' + rn(best.ax) + '" y2="' + rn(best.ay) + '"/>'; }
      labels += '<text class="rt-lbl" text-anchor="' + best.anchor + '" x="' + rn(tx) + '" y="' + rn(b.y0 + 11) + '">' + esc(text) + '</text>';
      res.push(b);
      labelBoxes.push(b);
    });
    // cap et distance au long de la branche (tablette), s'il y a une place libre à 12 ou 20 px ; sinon rien : la table le dit
    if (!phone && o.texts) {
      const samples = [];
      for (let i = 0; i + 1 < P.length; i++) {
        const a = P[i], b = P[i + 1], n = Math.max(1, Math.ceil(Math.hypot(b.x - a.x, b.y - a.y) / 5));
        for (let k = 0; k <= n; k++) samples.push({ x: a.x + (b.x - a.x) * k / n, y: a.y + (b.y - a.y) * k / n });
      }
      mids.forEach((m, i) => {
        const a = P[i], b = P[i + 1], len = Math.hypot(b.x - a.x, b.y - a.y) || 1, text = o.texts[i] || '';
        if (!text) return;
        const w = text.length * RT_HD_W + 4, nx = -(b.y - a.y) / len, ny = (b.x - a.x) / len, out = ((m.x - cx) * nx + (m.y - cy) * ny) >= 0 ? 1 : -1;
        const tries = [[12, out], [12, -out], [20, out], [20, -out]];
        for (let k = 0; k < tries.length; k++) {
          const d = tries[k][0], sd = tries[k][1], px = m.x + nx * sd * d, py = m.y + ny * sd * d;
          const cxx = px + nx * sd * w / 2 * Math.abs(nx), cyy = py + ny * sd * RT_HD_H / 2 * Math.abs(ny) + (Math.abs(ny) < 0.35 ? 0 : 0);
          const box = { x0: cxx - w / 2, y0: cyy - RT_HD_H / 2, x1: cxx + w / 2, y1: cyy + RT_HD_H / 2 };
          if (!rtFree(box, res, W, H)) continue;
          if (samples.some(sp => sp.x > box.x0 - 1 && sp.x < box.x1 + 1 && sp.y > box.y0 - 1 && sp.y < box.y1 + 1)) continue;
          heads += '<text class="rt-hd" x="' + rn(cxx) + '" y="' + rn(cyy + 4) + '">' + esc(text) + '</text>';
          res.push(box);
          break;
        }
      });
    }
  }
  return '<svg class="rt-svg' + (mini ? ' rt-m' : '') + '" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ' + rn(W) + ' ' + rn(H) + '" width="' + rn(W) + '" height="' + rn(H) + '"' + (o.label ? ' role="img" aria-label="' + esc(o.label) + '"' : ' aria-hidden="true"') + '>'
    + extra + legs + arrows + dots + numbers + labels + heads + '</svg>';
}

// ----- Le bloc ROUTE de la colonne droite : le choix, ou la route (en-tête, croquis, table, note) -----
// Le groupe sans route est toujours au choix ; « Changer de route » ouvre le choix pour un groupe (UI.rtChoose = son fcId).
// L'état d'une route liée (copie gardée, théâtre) se calcule au rendu : rien de plus à garder.
function routeStatus(f, rp) {
  if (!f.routeLink) return null;
  if (rp.state.theatre === '') return { k: 'norp' };
  const rt = rp.routes.filter(r => r.rid === f.routeLink.rid)[0];
  if (!rt) return { k: 'gone' };
  if (rt.theatre !== rTh()) return { k: 'theatre', th: rt.theatre };       // la route est d'un autre théâtre (le Route Planner la garde masquée) : aucune reprise
  return rt.points.length < 2 ? { k: 'few' } : null;
}
function rpGeo(rt) { return rt.points.map((p, i) => ({ name: (p.name || '').replace(/\s+/g, ' ').trim() || 'WP' + (i + 1), lat: p.lat, lon: p.lon })); }
function routeCardHtml(rt, f, off) {
  const geo = rpGeo(rt), on = f.routeLink && f.routeLink.rid === rt.rid && ridOk(rt.rid), linked = rtMatches(rt, f);
  off = off || !ridOk(rt.rid);
  const tcb = tcConflict(), tcTip = tcb ? ' title="' + esc(tf('tc.banner', theatreName(tcb.F), theatreName(tcb.C))) + '"' : '';
  const tag = rt.flight ? tf('route.tag.linked', rt.flight.groupName.trim()) : t('route.tag.free');
  const name = rt.name.trim() !== '' ? rt.name.trim() : t('route.unnamed');
  return `<button type="button" class="rt-card${on ? ' on' : ''}" data-act="route-pick" data-rid="${esc(rt.rid)}"${off ? ' disabled' : ''}${tcTip}>
    <span class="rt-mini">${rtSketch(geo, { mini: true, W: 160, H: 100, mx: 10, my: 10 })}</span>
    <span class="rt-cn">${esc(name)}</span>
    <span class="rt-cm">${esc(ptsLabel(geo.length) + ' · ' + fmtDist(routeNm(geo)) + ' ' + udLabel())}</span>
    <span class="snap-flight-tag rt-tag${linked ? ' full' : ''}">${esc(tag)}</span></button>`;
}
function routeChooseHtml(f, rp) {
  const usable = rpUsable(rp), th = rp.state.theatre;
  let msg = '';
  if (th === '') return `<p class="rt-note">${esc(t('route.norp'))}</p>` + (hasRoute(f) ? `<div class="miz-btn-row" style="margin-top:0"><button type="button" class="miz-btn fc-small" data-act="route-keep">${esc(t('route.keep'))}</button></div>` : '');
  if (!has(TM_PARAMS, S.theatre)) msg = tf('route.th.nosupport', theatreName(S.theatre));
  const tcb = tcConflict();
  if (tcb && !msg) msg = tf('tc.banner', theatreName(tcb.F), theatreName(tcb.C));
  const off = msg !== '';
  let h = usable.length ? `<p class="rt-note">${esc(t(hasRoute(f) ? 'route.choose.other' : 'route.choose.none'))}</p>` : `<p class="rt-note">${esc(t('route.empty'))}</p>`;
  if (msg) h += `<p class="rt-note">${esc(msg)}</p>`;
  if (usable.some(r => !ridOk(r.rid))) h += `<p class="rt-note">${esc(t('route.noid'))}</p>`;
  const linked = usable.filter(r => rtMatches(r, f)), other = usable.filter(r => !rtMatches(r, f));
  [['route.list.linked', linked], ['route.list.other', other]].forEach(g => {
    if (g[1].length) h += `<div class="rt-h">${esc(t(g[0]))}</div><div class="rt-grid">${g[1].map(r => routeCardHtml(r, f, off)).join('')}</div>`;
  });
  if (hasRoute(f)) h += `<div class="miz-btn-row" style="margin-top:0"><button type="button" class="miz-btn fc-small" data-act="route-keep">${esc(t('route.keep'))}</button></div>`;
  return h;
}
function routeViewHtml(f, fi, rp) {
  const geo = routeGeo(f), pts = routeKeys(f.route.points).length, st = routeStatus(f, rp);
  let sub = t(f.routeLink ? 'route.from.rp' : 'route.from.pkg') + ' · ' + ptsLabel(pts);
  let table = '';
  if (geo) {
    const ds = declSource(rp.state.nav, routeDateOf(f)), L = routeLegs(geo, ds);
    sub += ' · ' + fmtDist(L.total) + ' ' + udLabel();
    const rows = L.legs.map((l, i) => `<tr><td class="rt-n">${i + 1}</td><td>${esc(l.from)} → ${esc(l.to)}</td><td class="rt-r">${esc(l.hdg)}°</td><td class="rt-r">${esc(fmtDist(l.nm))} ${udLabel()}</td></tr>`).join('');
    table = `<table class="rt-tab"><thead><tr><th class="rt-n"></th><th>${esc(t('route.col.leg'))}</th><th class="rt-r">${esc(t('route.col.hdg'))}</th><th class="rt-r">${esc(t('route.col.dist'))}</th></tr></thead><tbody>${rows}<tr class="rt-tot"><td></td><td>${esc(t('route.total'))}</td><td></td><td class="rt-r">${esc(fmtDist(L.total))} ${udLabel()}</td></tr></tbody></table><p class="rt-note">${esc(declNote(ds, geo))}</p>`;
  }
  let note = '';
  if (st) note = `<p class="rt-note rt-warn">${esc(st.k === 'theatre' ? tf('route.theatre.other', theatreName(st.th), theatreName(rTh())) : t(st.k === 'norp' ? 'route.norp' : (st.k === 'gone' ? 'route.gone' : 'route.few')))}</p>`;
  return `<div class="rt-head"><div class="rt-hl"><span class="rt-name">${esc(routeTitle(f))}</span><span class="rt-sub">${esc(sub)}</span></div>
      <div class="rt-hb"><button type="button" class="miz-btn fc-small" data-act="route-change">${esc(t('route.change'))}</button><button type="button" class="miz-btn fc-small" data-act="route-remove">${esc(t('route.remove'))}</button></div></div>
    ${note}${geo ? '<div class="rt-paper" id="rt-paper"></div>' + table : `<p class="rt-note">${esc(t('route.nosketch'))}</p>`}`;
}
function routeBlockHtml(su) {
  const f = su.f, rp = rpRead(), choosing = !hasRoute(f) || UI.rtChoose === f.fcId;
  return `<section class="fc-block" id="blk-route"><div class="fc-bh">${esc(t('sec.route'))} <span class="fc-count">· ${esc(flightLabel(f, su.fi))}</span></div>
    <div class="fc-bc">${choosing ? routeChooseHtml(f, rp) : routeViewHtml(f, su.fi, rp)}</div></section>`;
}
// Le croquis se dessine à la largeur de la feuille ; la feuille masquée (module caché du shell) a 0 px : le ResizeObserver redessine à son retour.
function rtDraw() {
  const paper = document.getElementById('rt-paper'), su = selUnit();
  if (!paper || !su) return;
  const geo = routeGeo(su.f), w = Math.floor(paper.clientWidth), col = document.getElementById('col-right');
  RT.w = w;
  if (!geo || w < 120) { paper.innerHTML = ''; return; }
  const rp = rpRead(), L = routeLegs(geo, declSource(rp.state.nav, routeDateOf(su.f)));
  paper.innerHTML = rtSketch(geo, { W: w, phone: col.clientWidth <= 520, title: flightLabel(su.f, su.fi), label: tf('route.sketch', routeTitle(su.f)), texts: L.legs.map(l => l.hdg + '° · ' + fmtDist(l.nm)) });
}
function renderRouteBlock() {
  const host = document.getElementById('col-route'), su = selUnit();
  if (!host) return;
  if (RT.ro) { RT.ro.disconnect(); RT.ro = null; }
  host.innerHTML = su ? routeBlockHtml(su) : '';
  const paper = document.getElementById('rt-paper');
  if (!paper) return;
  rtDraw();
  if (typeof ResizeObserver === 'function') {
    RT.ro = new ResizeObserver(() => { if (Math.floor(paper.clientWidth) !== RT.w) rtDraw(); });
    RT.ro.observe(paper);
  }
}
// La ligne de la carte du groupe : sans route « Aucune route. » et un lien ; avec route un mini-croquis, « Route : nom — n points, d NM » et le lien « Voir la route ↓ »
function routeHtml(f) {
  const see = key => f.units.length ? `<button type="button" class="fc-see" data-act="see-route">${esc(t(key))}</button>` : '';       // le bloc Route de la colonne de droite attend une unité
  if (!hasRoute(f)) return `<div class="fc-route none"><span class="fc-route-t">${esc(t('route.none'))}</span>${see('route.pick')}</div>`;
  const geo = routeGeo(f), n = routeKeys(f.route.points).length;
  const text = geo ? tf('route.line', routeTitle(f), ptsLabel(n), fmtDist(routeNm(geo)) + ' ' + udLabel()) : tf('route.line.nod', routeTitle(f), ptsLabel(n));
  const thumb = geo ? `<span class="rt-thumb">${rtSketch(geo, { mini: true, W: 64, H: 40, mx: 7, my: 7 })}</span>` : '';
  return `<div class="fc-route">${thumb}<span class="fc-route-t">${esc(text)}</span>${see('route.see')}</div>`;
}
function paintRouteLines() {
  S.flights.forEach((f, fi) => {
    const el = flightEl(fi), line = el && el.querySelector('.fc-route');
    if (line) line.outerHTML = routeHtml(f);
  });
}
// Un geste sur la route (choisir, retirer, changer…) ou un nom, un camp, un théâtre qui change : le bloc, les lignes des cartes, les résumés et l'état suivent
function routeChanged() { renderRouteBlock(); paintRouteLines(); refreshAll(); commitNow(); }

function routePick(rid) {
  const su = selUnit(), rp = rpRead(), rt = ridOk(rid) ? rp.routes.filter(r => r.rid === rid)[0] : null;
  if (!su || !rt || rt.points.length < 2 || !has(TM_PARAMS, S.theatre)) return;
  const f = su.f;
  if (rt.theatre !== S.theatre || tcConflict()) return;       // seulement une route du théâtre commun, et rien pendant le bandeau
  f.route = gsRouteCopy(rpPack(rt, S.theatre, rp.state.gs), rt.missionDate);       // la date de la route du Route Planner la suit
  f.routeLink = { rid: rt.rid, name: rt.name };
  UI.rtChoose = null;
  routeChanged();
}
// La reprise : chaque groupe lié dont la route du Route Planner existe (deux points au moins, même théâtre) reprend ses points s'ils diffèrent et le nom de la route
// Rend { toast, changed } sans rien dessiner ; une route absente, trop courte ou sur un autre théâtre ne touche pas la copie du groupe.
function routeSync() {
  const out = { toast: '', changed: false };
  if (!S.flights.some(f => f.routeLink)) return out;
  if (tcConflict()) return out;       // le bandeau est là : aucune reprise, aucune écriture de la fiche (elle reste sur son théâtre)
  const rp = rpRead(), done = [];
  S.flights.forEach((f, fi) => {
    if (!f.routeLink || routeStatus(f, rp)) return;
    const rt = rp.routes.filter(r => r.rid === f.routeLink.rid)[0], pts = rpPack(rt, S.theatre, rp.state.gs);
    if (JSON.stringify(pts) === JSON.stringify(f.route ? f.route.points : null) && rt.name === f.routeLink.name && routeDateOf(f) === rt.missionDate) return;
    f.route = gsRouteCopy(pts, rt.missionDate);
    f.routeLink = { rid: rt.rid, name: rt.name };
    done.push({ label: flightLabel(f, fi), name: rt.name.trim() !== '' ? rt.name : t('route.unnamed') });
  });
  if (done.length) {
    out.changed = true;
    out.toast = done.length === 1 ? tf('route.toast.one', done[0].name, done[0].label) : tf('route.toast.many', done.map(d => d.label).join(', '));
  }
  return out;
}
function routeTakeover() {
  if (document.visibilityState !== 'visible') return;       // un onglet resté en arrière-plan n'écrit rien : à son retour (visibilitychange), il reprend
  gsPull();       // la copie que le Route Planner tient à jour dans la fiche d'abord : s'il n'y a plus rien à reprendre, rien ne s'écrit
  const r = routeSync();
  if (r.changed) { clearTimeout(_saveTimer); writeState(); }
  renderRouteBlock();
  paintRouteLines();
  if (r.changed) { refreshSummaries(); showToast(r.toast, 4500); }
}
function routeStorage(e) {
  if (e.key !== null && e.key !== KEY_RP_SET && e.key !== KEY_RP_STATE && e.key !== KEY_HQ_MISSION) return;
  clearTimeout(RT.timer);
  RT.timer = setTimeout(routeTakeover, 80);      // le Route Planner écrit route_set_v1 puis route_state_v1 : un seul passage pour les deux
}

// ----- Le résumé d'un vol, sur une ligne, pour son en-tête replié : une partie absente se tait -----
function commonOrVaried(values, textOne, textVaried) {
  return values.every(x => x === values[0]) ? textOne(values[0]) : textVaried;
}
function clipText(s, max) { return s.length > max ? s.slice(0, max) + '…' : s; }
function flightSummary(f, fi) {
  const counts = [];       // [type, nombre], dans l'ordre des unités
  f.units.forEach(u => { const c = counts.filter(x => x[0] === u.type)[0]; if (c) c[1]++; else counts.push([u.type, 1]); });
  const parts = [counts.length ? counts.map(c => c[1] + ' × ' + typeLabel(c[0])).join(' + ') : t('fl.nounit')];
  const points = f.route ? routePoints(f.route.points).length : 0;
  if (points) parts.push(tf('sum.route', points));
  const radios = f.units.map(u => radioCount(f, u));
  if (radios.some(n => n > 0)) parts.push(commonOrVaried(radios, n => tf('sum.radios', n), t('sum.radios.var')));
  const loadouts = f.units.map(u => (u.loadout ? loadoutSummary(u.loadout) : ''));
  if (loadouts.some(x => x !== '')) parts.push(commonOrVaried(loadouts, x => x, t('sum.loadout.var')));
  const liveries = f.units.map((u, ui) => liveryShown(f, fi, u, ui));
  if (liveries.some(x => x !== '')) parts.push(commonOrVaried(liveries, x => tf('sum.livery', clipText(x, SUMMARY_LIVERY_MAX)), t('sum.livery.var')));
  return parts.join(' · ');
}

// Le résumé d'une unité repliée : nom (ou son défaut), indicatif, livrée (coupée comme au résumé du groupe), emport ; une partie vide se tait.
function unitSummary(f, fi, u, ui) {
  const parts = [unitLabel(f, fi, u, ui), typeLabel(u.type)];
  if (u.callsign.trim() !== '') parts.push(u.callsign.trim());
  const lv = liveryShown(f, fi, u, ui);
  if (lv !== '') parts.push(tf('sum.livery', clipText(lv, SUMMARY_LIVERY_MAX)));
  if (u.loadout) parts.push(loadoutSummary(u.loadout));
  return parts.join(' · ');
}
function unitFoldLabel(f, fi, u, ui) { return `${t(u.folded ? 'u.unfold' : 'u.fold')} : ${unitLabel(f, fi, u, ui)}`; }

// ----- Le paquet -----
function pkStamp(d) {
  d = d || new Date();
  const p = n => String(n).padStart(2, '0');
  return d.getFullYear() + p(d.getMonth() + 1) + p(d.getDate()) + '-' + p(d.getHours()) + p(d.getMinutes()) + p(d.getSeconds());
}
// Le nom par défaut, sans extension : préfixe, premier groupe, « _+n » pour les autres, horodatage
function packageFileName(prefix) {
  const first = S.flights.length ? fnPart(S.flights[0].name, 'groupe') : 'groupe';
  return (prefix || 'paquet') + '_' + first + (S.flights.length > 1 ? '_+' + (S.flights.length - 1) : '') + '_' + pkStamp();
}
// Les noms de vol en double : deux vols de même nom rogné (casse exacte) et de même camp, ou dont l'un n'a pas de camp ; chaque nom une fois.
function duplicateNames() {
  const out = [], seen = new Set();
  S.flights.forEach((f, i) => {
    const k = nameKey(f.name);
    if (k === '' || seen.has(k)) return;
    for (let j = 0; j < i; j++) {
      const g = S.flights[j];
      if (nameKey(g.name) === k && (f.coalition === g.coalition || f.coalition === '' || g.coalition === '')) { seen.add(k); out.push(g.name.trim()); return; }
    }
  });
  return out;
}
// Ce qui empêche l'export : [{ key, args }] ; la liste vide = prêt. Une fréquence qu'on vient de saisir hors bande bloque ; celle qui était déjà dans la fiche (importée, ou saisie avant un changement de bande) est signalée sans bloquer ; un réglage d'emport hors limites est ramené, il ne bloque rien.
function exportIssues() {
  const out = [];
  const tc = tcConflict();
  if (tc) out.push({ key: 'bar.theatre.conflict', args: [theatreName(tc.F), theatreName(tc.C)] });
  else if (S.flights.some(f => f.routeLink)) {       // un groupe lié à une route du Route Planner qui est d'un autre théâtre que le commun : son paquet porterait des points d'une autre carte
    const rp = rpRead();
    S.flights.forEach((f, fi) => {
      const rt = f.routeLink ? rp.routes.filter(r => r.rid === f.routeLink.rid)[0] : null;
      if (rt && rt.theatre !== S.theatre) out.push({ key: 'bar.route.theatre', args: [flightLabel(f, fi), theatreName(rt.theatre), theatreName(S.theatre)] });
    });
  }
  if (!S.flights.length) out.push({ key: 'bar.no.flight', args: [] });
  let badFreq = 0, noType = null;
  S.flights.forEach((f, fi) => {
    if (!f.name.trim()) out.push({ key: 'bar.no.name', args: [fi + 1] });
    f.units.forEach(u => radioPosts(u.type).forEach(r => { badFreq += radioIssues(f, u, r).block.length; }));
    if (!noType) { const k = f.units.findIndex(u => u.type === ''); if (k >= 0) noType = { key: 'bar.no.type', args: [flightLabel(f, fi), k + 1] }; }       // une unité sans type : le paquet ne s'exporte pas
  });
  if (noType) out.push(noType);
  const dups = duplicateNames();
  if (dups.length) out.push({ key: 'bar.dup', args: [dups.join(', ')] });
  if (badFreq) out.push({ key: 'bar.bad.freq', args: [badFreq] });
  return out;
}
function unitRadiosOut(f, u) {
  const out = [];
  radioPosts(u.type).forEach(r => {
    const channels = {};
    for (let c = 1; c <= radioSlotsOf(u.type, r); c++) {
      const p = parseFreq(chanValue(u, r, c));
      if (p.v !== undefined) channels[String(c)] = p.v;
    }
    if (Object.keys(channels).length) out.push({ radioIndex: r, channels: channels });
  });
  return out.length ? out : null;
}
// Un réglage d'emport pour le paquet : un nombre, négatif compris (buildPayload le ramène à 0) ; undefined si ce n'en est pas un (valeur par défaut de la table).
function loNumber(raw) {
  const x = String(raw).trim().replace(',', '.');
  return /^-?\d+(\.\d+)?$/.test(x) ? Number(x) : undefined;
}
function unitPayloadOut(f, u) {
  const lo = u.loadout;
  if (!lo) return null;
  const settings = {};
  LO_FIELDS.forEach(k => { settings[k] = loNumber(lo[k]); });
  return buildPayload(u.type, lo.pylons, settings);     // buildPayload ramène chaque valeur dans la table de l'appareil
}
// Le paquet dcs-flight-package-v2 : une partie non renseignée sort en null (HQ n'y touche pas). Ni fcId, ni sourceMission.
function buildPackage() {
  // missionDate (facultatif, racine) : la date de la mission d'où viennent les routes ; écrite si tous les groupes dont la route porte une date portent la même, sinon absente
  const dates = [];
  S.flights.forEach(f => { const d = routeDateOf(f); if (d !== '' && dates.indexOf(d) < 0) dates.push(d); });
  const pkg = { format: PACKAGE_FORMAT, createdAt: new Date().toISOString(), createdBy: 'Flight Configurator', theatre: S.theatre };
  if (dates.length === 1) pkg.missionDate = dates[0];
  return Object.assign(pkg, {
    flights: S.flights.map((f, fi) => ({
      groupName: f.name.trim(), coalition: f.coalition || null, groupFrequency: null,
      route: f.route ? { points: clone(f.route.points) } : null,
      units: f.units.map((u, ui) => {
        const o = { name: unitLabel(f, fi, u, ui), type: u.type, callsign: csValue(u), liveryId: liveryShown(f, fi, u, ui) || null, radios: unitRadiosOut(f, u), payload: unitPayloadOut(f, u) };
        if (u.onboard.trim()) o.onboardNum = u.onboard.trim();
        return o;
      })
    }))
  });
}
// Le fichier de travail : le paquet tel qu'il se lit, plus la clé « fc » (l'état de l'écran et mes presets) que HQ ignore.
function buildWorkFile() {
  const pkg = buildPackage();
  const tc = tcConflict();
  pkg.fc = { v: 1, state: clone(S), mine: clone(LIB.mine) };
  if (tc) { pkg.theatre = tc.F; pkg.fc.state.theatre = tc.F; }       // le bandeau est là : les routes des groupes sont sur le théâtre de la fiche, le fichier de travail le garde
  return pkg;
}

// ----- Replier les vols -----
// Sans choix de la personne, tout vol est déplié tant qu'il y en a deux ou moins ; au-delà, seul le vol sur lequel on travaille l'est.
// Un choix (plier, déplier) fige l'état de tous les vols affichés à cet instant : rien ne se replie tout seul ensuite.
function flightOpen(f, fi) {
  const m = UI.fold.get(f);
  if (m) return m === 'open';
  return S.flights.length <= 2 || S.sel.f === fi;
}
function foldFreeze() { S.flights.forEach((f, fi) => { if (!UI.fold.has(f)) UI.fold.set(f, flightOpen(f, fi) ? 'open' : 'closed'); }); }
function setFold(f, open) { foldFreeze(); UI.fold.set(f, open ? 'open' : 'closed'); }
function anyFlightOpen() { return S.flights.some((f, fi) => flightOpen(f, fi)); }


// ---------- 3. Colonne des vols ----------
// Une option peut porter `g` (le titre de son groupe) : les options consécutives de même `g` sont rendues dans un <optgroup>.
function optionsHtml(options, value) {
  let out = '', open = null;
  options.forEach(o => {
    const g = o.g || null;
    if (g !== open) { if (open !== null) out += '</optgroup>'; if (g !== null) out += `<optgroup label="${esc(g)}">`; open = g; }
    out += `<option value="${esc(o.v)}"${String(o.v) === String(value) ? ' selected' : ''}>${esc(o.l)}</option>`;
  });
  return out + (open !== null ? '</optgroup>' : '');
}
function selectHtml(attrs, label, options, value) {
  return `<select class="fc-sel" aria-label="${esc(label)}" ${attrs}>${optionsHtml(options, value)}</select>`;
}
function fieldHtml(label, inner) { return `<div class="ed-field"><label>${esc(label)}</label>${inner}</div>`; }
function inputHtml(attrs, value, placeholder) {
  return `<input type="text" autocomplete="off" spellcheck="false" ${attrs} value="${esc(value)}"${placeholder ? ` placeholder="${esc(placeholder)}"` : ''}>`;
}
function numberInputHtml(attrs, value, min, max, step) {
  return `<input type="number" autocomplete="off" inputmode="${step === '1' ? 'numeric' : 'decimal'}" min="${min}" max="${max}" step="${step}" ${attrs} value="${esc(value)}">`;
}
function openAttr(key) { return UI.open.has(key) ? ' open' : ''; }
function unitsLabel(n) { return tf(n < 2 ? 'fl.units.one' : 'fl.units.many', n); }
function flightEl(fi) { return document.querySelector(`#col-left .fc-flight[data-f="${fi}"]`); }
function unitEl(fi, ui) { return document.querySelector(`#col-left .fc-flight[data-f="${fi}"] .fc-unit[data-u="${ui}"]`); }

function renderLeft() {
  const foldAll = S.flights.length > 1 ? `<button type="button" class="miz-btn fc-small fc-foldall" id="fc-foldall" data-act="fold-all">${esc(foldAllLabel())}</button>` : '';
  document.getElementById('col-flights').innerHTML = `<section class="fc-block">
    <div class="fc-bh">${esc(t('sec.flights'))} <span class="fc-count">(${S.flights.length})</span>${foldAll}</div>
    <div class="fc-bc">
      ${S.flights.length ? '' : `<p class="ui-note">${esc(t('fl.empty'))}</p>`}
      <div class="fc-list" id="fc-list">${S.flights.map(flightHtml).join('')}</div>
      <div class="miz-btn-row" style="margin-top:0"><button type="button" class="miz-btn primary" data-act="add-flight">${esc(t('fl.add'))}</button></div>
    </div></section>`;
  S.flights.forEach((f, fi) => f.units.forEach((u, ui) => radioPosts(u.type).forEach(r => paintRadioMsg(fi, ui, r))));
}
function foldAllLabel() { return t(anyFlightOpen() ? 'fl.foldall' : 'fl.unfoldall'); }
function foldLabel(f, fi, open) { return `${t(open ? 'fl.fold' : 'fl.unfold')} : ${flightLabel(f, fi)}`; }

function flightHtml(f, fi) {
  const open = flightOpen(f, fi);
  return `<div class="fc-flight${open ? '' : ' folded'}" data-f="${fi}">
    <div class="fc-fhead">
      <button type="button" class="fc-fold" data-act="fold" aria-expanded="${open}" aria-label="${esc(foldLabel(f, fi, open))}"><span class="fc-chev" aria-hidden="true"></span><span class="fc-ftitle">${esc(flightLabel(f, fi))}</span></button>
      ${f.units.length ? `<span class="snap-flight-tag">${esc(modTypesLabel(f))}</span>` : ''}<span class="snap-flight-tag">${esc(f.units.length ? unitsLabel(f.units.length) : t('fl.nounit'))}</span>
      <button type="button" class="pk-x" data-act="rm-flight" aria-label="${esc(t('fl.remove'))}" title="${esc(t('fl.remove'))}">✕</button>
      <div class="fc-fsum">${esc(flightSummary(f, fi))}</div>
    </div>
    <div class="fc-fbody"${open ? '' : ' hidden'}>
      ${flightFieldsHtml(f)}<div class="fc-depart" hidden></div>${routeHtml(f)}
      <div class="fc-units">${f.units.length ? f.units.map((u, ui) => unitHtml(f, fi, u, ui)).join('') : `<div class="fc-nounit${S.sel.f === fi ? ' sel' : ''}" data-nounit="1">${esc(t('fl.nounit'))}</div>`}</div>
      ${f.units.length < MAX_UNITS ? `<div class="miz-btn-row"><button type="button" class="miz-btn" data-act="add-unit">${esc(tf('u.add', f.units.length))}</button></div>` : ''}
    </div></div>`;
}
function flightFieldsHtml(f) {
  const coalitions = [{ v: '', l: t('fl.coalition.any') }, { v: 'blue', l: t('fl.coalition.blue') }, { v: 'red', l: t('fl.coalition.red') }];
  return `<div class="fc-row3">${fieldHtml(t('fl.name'), inputHtml('data-k="name"', f.name, t('fl.name.ph')))}
    ${fieldHtml(t('fl.coalition'), selectHtml('data-k="coalition"', t('fl.coalition'), coalitions, f.coalition))}</div>`;
}

function unitHtml(f, fi, u, ui) {
  const at = `data-u="${ui}"`, rk = `f${fi}u${ui}r`, n = radioCount(f, u);
  return `<div class="fc-unit${S.sel.f === fi && S.sel.u === ui ? ' sel' : ''}${u.folded ? ' folded' : ''}" data-u="${ui}">
    <div class="fc-uhead"><button type="button" class="fc-ufold" data-act="fold-unit" aria-expanded="${!u.folded}" aria-label="${esc(unitFoldLabel(f, fi, u, ui))}"><span class="fc-chev" aria-hidden="true"></span></button><span class="fc-utitle">${esc(tf('u.title', ui + 1))}</span>
      ${f.units.length > 1 ? `<button type="button" class="pk-x" data-act="rm-unit" aria-label="${esc(t('u.remove'))}" title="${esc(t('u.remove'))}">✕</button>` : ''}</div>
    <div class="fc-usum" data-sum="unit">${esc(unitSummary(f, fi, u, ui))}</div>
    <div class="fc-ubody"${u.folded ? ' hidden' : ''}><div class="fc-row4">
      ${fieldHtml(t('u.type'), selectHtml(`${at} data-k="utype"`, t('u.type'), (u.type === '' ? [{ v: '', l: t('u.type.pick') }] : []).concat(PAYLOAD_TYPES.map(x => ({ v: x, l: TYPE_LABEL[x] || x }))), u.type))}
      ${fieldHtml(t('u.name'), inputHtml(`${at} data-k="uname"`, u.name, unitDefaultName(f, fi, ui)))}
      ${fieldHtml(t('u.callsign'), inputHtml(`${at} data-k="callsign"`, u.callsign, t('u.opt')))}
      ${fieldHtml(t('u.onboard'), inputHtml(`${at} data-k="onboard"`, u.onboard, t('u.opt')))}
      ${u.type === '' ? '' : fieldHtml(t('u.livery'), selectHtml(`${at} data-k="livery" data-repick`, t('u.livery'), liveryOptions(f, fi, u, ui), liveryShown(f, fi, u, ui)))}
    </div>
    ${u.type === '' ? `<p class="ui-note fc-notype">${esc(t('u.notype'))}</p>` : unitSettingsHtml(f, fi, u, ui, rk, at)}
  </div></div>`;
}
function unitSettingsHtml(f, fi, u, ui, rk, at) {
  return `<details class="fc-sub" data-key="${rk}"${openAttr(rk)}><summary class="ui-fold-head" aria-expanded="${UI.open.has(rk)}">${esc(t('u.radios'))} <span class="fc-sum" data-sum="radios">${esc(radiosSummary(f, u))}</span></summary>
      <div class="fc-subc">${radiosHtml(f, fi, u, ui)}</div></details>
    <div class="fc-lo-sum"><span class="fc-lo-k">${esc(t('u.loadout'))}</span><span class="fc-lo-v" data-sum="loadout">${esc(loadoutName(u.loadout))}</span>
      <button type="button" class="fc-see" ${at} data-act="see-cmp">${esc(t('u.see'))}</button></div>`;
}
function radiosSummary(f, u) {
  const n = radioCount(f, u);
  return n ? tf('u.radios.set', n) : tf('u.radios.sum', radioPosts(u.type).length);
}
function radiosHtml(f, fi, u, ui) {
  const ty = u.type;
  const posts = radioPosts(ty).map(r => {
    const pk = `f${fi}u${ui}p${r}`, n = radioSlotsOf(ty, r), hull = bandHull(ty, r), free = radioIsFree(ty, r);
    let chans = '';
    for (let c = 1; c <= n; c++) {
      chans += `<div class="fc-ch"><label>${esc(free ? tf('rad.freq', c) : tf('rad.ch', radioCockpitChannel(ty, r, c)))}</label>`
        + numberInputHtml(`data-u="${ui}" data-r="${r}" data-c="${c}" data-k="chan" placeholder="—"`, chanShown(u, r, c), hull[0], hull[1], '0.001') + '</div>';
    }
    return `<details class="fc-post" data-key="${pk}"${openAttr(pk)}><summary class="ui-fold-head" aria-expanded="${UI.open.has(pk)}"><span class="fc-ptop">${esc(radioPosteName(ty, r) || 'R' + r)} ${free ? '' : `<span class="fc-sum">${esc(tf('rad.chans', n))}</span>`}<span class="fc-sum fc-flag" data-flag="${r}"></span></span><span class="fc-band" data-band="${r}">${esc(bandText(ty, r))}</span></summary>
      <div class="fc-postc"><div class="fc-chans">${chans}</div><div class="fc-msg" id="rm-${fi}-${ui}-${r}"></div></div></details>`;
  }).join('');
  const sameType = f.units.some((x, k) => k !== ui && x.type === ty);       // « Recopier » ne va qu'aux unités du même type : sans elles, le bouton est inactif
  const copy = f.units.length > 1 ? `<div class="miz-btn-row" style="margin-top:0"><button type="button" class="miz-btn" data-u="${ui}" data-act="copy-radios"${sameType ? '' : ' disabled'}>${esc(t('rad.copy'))}</button></div>` : '';
  return `<div class="fc-posts">${posts}</div><p class="ui-note">${esc(t('rad.hint'))}</p>${copy}`;
}

// ----- Mises à jour ciblées (sans redessiner) -----
function paintRadioMsg(fi, ui, r) {
  const f = S.flights[fi], u = f && f.units[ui], root = unitEl(fi, ui);
  if (!u || !root) return;
  const iss = radioIssues(f, u, r);
  root.querySelectorAll(`input[data-r="${r}"]`).forEach(inp => inp.classList.toggle('bad', iss.bad.indexOf(Number(inp.getAttribute('data-c'))) >= 0));
  const el = document.getElementById(`rm-${fi}-${ui}-${r}`);
  if (el) el.textContent = iss.first ? iss.first + (iss.bad.length > 1 ? tf('rad.err.more', iss.bad.length - 1) : '') : '';
  const flag = root.querySelector(`[data-flag="${r}"]`);      // le poste replié le dit aussi : « ⚠ 2 hors bande »
  if (flag) flag.textContent = iss.bad.length ? '⚠ ' + tf('rad.bad.n', iss.bad.length) : '';
}
function paintFold() {
  S.flights.forEach((f, fi) => {
    const el = flightEl(fi);
    if (!el) return;
    const open = flightOpen(f, fi), btn = el.querySelector('.fc-fold');
    el.classList.toggle('folded', !open);
    el.querySelector('.fc-fbody').hidden = !open;
    btn.setAttribute('aria-expanded', String(open));
    btn.setAttribute('aria-label', foldLabel(f, fi, open));
  });
  const all = document.getElementById('fc-foldall');
  if (all) all.textContent = foldAllLabel();
}
// Replier ou déplier une carte d'unité : sans redessiner (la frappe et les volets ouverts restent), l'emport affiché ne change pas.
function paintUnitFold(fi, ui) {
  const f = S.flights[fi], u = f && f.units[ui], el = unitEl(fi, ui);
  if (!u || !el) return;
  el.classList.toggle('folded', u.folded);
  el.querySelector('.fc-ubody').hidden = u.folded;
  const btn = el.querySelector('.fc-ufold');
  btn.setAttribute('aria-expanded', String(!u.folded));
  btn.setAttribute('aria-label', unitFoldLabel(f, fi, u, ui));
}
function refreshSummaries() {
  S.flights.forEach((f, fi) => {
    const head = flightEl(fi);
    if (!head) return;
    head.querySelector('.fc-fsum').textContent = flightSummary(f, fi);
    f.units.forEach((u, ui) => {
      const root = unitEl(fi, ui);
      if (!root) return;
      const lo = root.querySelector('[data-sum="loadout"]'), rd = root.querySelector('[data-sum="radios"]');
      if (lo) lo.textContent = loadoutName(u.loadout);
      root.querySelector('[data-sum="unit"]').textContent = unitSummary(f, fi, u, ui);
      if (rd) rd.textContent = radiosSummary(f, u);
    });
  });
}
function refreshBar() {
  const issues = exportIssues(), btn = document.getElementById('btn-export'), bar = document.getElementById('fc-status');
  if (issues.length === 0) UI.exportTried = false;
  if (btn) { btn.disabled = false; btn.setAttribute('aria-disabled', 'false'); }       // Exporter reste actif : un clic avec des manques n'exporte rien, il dit ce qui manque
  if (!bar) return;
  bar.classList.toggle('ok', issues.length === 0);
  bar.classList.toggle('err', issues.length > 0 && UI.exportTried);
  const empty = !S.flights.length;
  let msg = issues.length ? (empty && !UI.exportTried ? t('bar.start') : issues.map(i => tf(i.key, ...i.args)).join(' ')) : tf('bar.ok', packageFileName() + '.json');
  if (UI.clamped > 0) msg += ' · ' + tf('bar.clamped', UI.clamped);
  bar.textContent = msg;
  tcPaint();
}
function refreshAll() { refreshBar(); refreshSummaries(); saveWork(); }
function renderAll() { renderLeft(); renderRight(); refreshBar(); applyI18nStatic(); saveWork(); }

function selectUnit(fi, ui) {
  const changed = !(S.sel.f === fi && S.sel.u === ui);
  if (!changed) return;
  if (S.sel.f !== fi) UI.rtChoose = null;
  S.sel = { f: fi, u: ui };
  document.querySelectorAll('#col-left .fc-flight').forEach(fe => {
    fe.querySelectorAll('.fc-unit').forEach(ue => ue.classList.toggle('sel', Number(fe.getAttribute('data-f')) === fi && Number(ue.getAttribute('data-u')) === ui));
    fe.querySelectorAll('.fc-nounit').forEach(ue => ue.classList.toggle('sel', Number(fe.getAttribute('data-f')) === fi));
  });
  if (changed) { Object.assign(UI.cmp, { saving: false, err: '', st: null }); renderRight(); saveWork(); }
}


// ---------- 4. Emport (la vue de face de Mission Tools) et mes presets ----------
// Le composeur reprend celui du Loadout Editor : un panneau dans la page, sur l'unité choisie. Large : une case par station (numéro et arme)
// sous le dessin ; étroit (colonne de moins de 900 px) : la même rangée, de numéros seuls. Un trait pointillé relie chaque case à son point d'attache.
const CMP = { type: '', view: null, pairs: {}, pyl: [], small: false, ro: null };

// Deux stations sont jumelles quand leurs points d'attache sont symétriques par rapport au milieu du dessin (à 2 % près).
function cmpPairs(view) {
  const W = view.viewBox[0], H = view.viewBox[1], ids = Object.keys(view.stations), out = {};
  ids.forEach(a => {
    let best = null, bestDx = Infinity;
    ids.forEach(b => {
      if (a === b) return;
      const A = view.stations[a], B = view.stations[b], dx = Math.abs(W - A.x - B.x), dy = Math.abs(A.y - B.y);
      if (dx <= 0.02 * W && dy <= 0.02 * H && dx < bestDx) { best = b; bestDx = dx; }
    });
    if (best !== null) out[a] = best;
  });
  Object.keys(out).forEach(a => { if (out[out[a]] !== a) delete out[a]; });
  return out;
}
// Nom court d'une arme pour sa case : jusqu'au premier « - », sans les parenthèses ; « UnGd Rkts » garde le mot après « mm ».
function cmpShort(clsid) {
  if (!clsid) return '—';
  const full = payloadWeaponName(clsid) || clsid;
  let head = full.split(' - ')[0].replace(/\s*\([^)]*\)/g, '').replace(/\s+/g, ' ').trim();
  const k = full.indexOf('UnGd Rkts'), m = k >= 0 ? /\bmm\s+(\S+)/.exec(full.slice(k)) : null;
  if (m) head += ' · ' + m[1];
  const side = payloadWeaponSide(CMP.type, clsid);       // le côté vient après le nom court, que les parenthèses de la table n'effacent pas
  return (head || full) + (side ? ' ' + t(side === 'L' ? 'w.left' : 'w.right') : '');
}
function cmpNum(n) { return String(Math.round(n)).replace(/\B(?=(\d{3})+(?!\d))/g, CURRENT_LANG === 'fr' ? ' ' : ','); }
// Une station dont l'arme en place n'a pas de miroir sur la jumelle (calculé de l'état : choix, preset ou import) ; la ligne ne paraît que case cochée.
function cmpNoMirror(lo, n, clsid) {
  if (clsid === '' || !CMP.view || !has(CMP.pairs, n)) return false;
  const twin = CMP.pyl.filter(x => x.n === CMP.pairs[n])[0];
  return !!twin && payloadMirrorClsid(clsid, twin.allowed) === '';
}
function cmpClsid(lo, n) { return lo && lo.pylons[n] && lo.pylons[n].CLSID ? String(lo.pylons[n].CLSID) : ''; }

function renderRight() {
  const col = document.getElementById('col-right'), su = selUnit();
  CMP.small = col.clientWidth < 900;
  col.innerHTML = `<div id="col-route"></div><section class="fc-block" id="blk-cmp"><div class="fc-bh">${esc(t('sec.cmp'))}</div>
    <div class="fc-bc">${su && su.u.type === '' ? `<p class="ui-note fc-notype">${esc(t('u.notype'))}</p>` : su ? cmpHtml(su) : `<p class="ui-note">${esc(t(S.flights[S.sel.f] && !S.flights[S.sel.f].units.length ? 'cmp.nounit' : 'cmp.pick'))}</p>`}</div></section><div id="col-presets"></div>`;
  if (CMP.ro) { CMP.ro.disconnect(); CMP.ro = null; }
  const wrap = document.getElementById('cmp-wrap');
  if (su && su.u.type !== '' && wrap && typeof ResizeObserver === 'function') {      // si la colonne passe de part et d'autre de 900 px (rotation d'une tablette), l'emport se redessine dans l'autre mode
    CMP.ro = new ResizeObserver(() => { if ((col.clientWidth < 900) !== CMP.small) renderRight(); else cmpDraw(); });
    CMP.ro.observe(wrap);
  }
  cmpUpdate();
  document.getElementById('col-presets').innerHTML = presetsHtml();
  renderRouteBlock();
}

// Un emport est « armé » dès qu'une station porte une arme : « Garder dans mes presets » et « Vider l'emport » n'agissent qu'alors.
function cmpArmed(lo) { return !!lo && Object.keys(cleanPylons(lo.pylons)).length > 0; }
function cmpLineHtml(lo) {
  if (!lo) return '';
  const src = loSrc(lo);
  return (src ? `<span class="snap-flight-tag">${esc(src)}</span>` : '') + (lo.modified ? `<span class="snap-flight-tag">${esc(t('cmp.mod'))}</span>` : '');
}
function cmpHtml(su) {
  const f = su.f, lo = su.u.loadout, ty = su.u.type;
  CMP.type = ty;
  CMP.pyl = payloadPylons(ty) || [];
  CMP.view = has(AIRCRAFT_VIEWS, ty) ? AIRCRAFT_VIEWS[ty] : null;
  CMP.pairs = CMP.view ? cmpPairs(CMP.view) : {};
  const armed = cmpArmed(lo);
  return `<button type="button" class="fc-back" data-act="back-unit">${esc(t('cmp.back'))}</button>
    <div class="cmp-top"><div class="cmp-for"><span id="cmp-for-t">${esc(tf('cmp.for', flightLabel(f, su.fi), unitLabel(f, su.fi, su.u, su.ui)))}</span> <span class="snap-flight-tag">${esc(TYPE_LABEL[ty] || ty)}</span></div>
      ${fieldHtml(t('cmp.from'), selectHtml('id="cmp-from"', t('cmp.from'), cmpFromOptions(f, lo, su.u), lo ? lo.key : ''))}</div>
    <div class="fc-lo-line" id="cmp-lo-line">${cmpLineHtml(lo)}</div>
    ${CMP.view ? cmpDrawingHtml() : `<p class="ui-note">${esc(t('cmp.noview'))}</p>`}
    <div class="cmp-list" id="cmp-list">${CMP.pyl.map(p => cmpRowHtml(p, lo)).join('')}</div>
    <div class="cmp-foot">${CMP.view ? `<label class="pk-chk"><input type="checkbox" id="cmp-sym"${UI.cmp.sym ? ' checked' : ''}> ${esc(t('cmp.sym'))}</label>` : ''}<span class="cmp-tot" id="cmp-total"></span></div>
    ${cmpSettingsHtml(f, su.ui, lo)}
    <p class="ui-note" id="cmp-empty-note"${lo && lo.key === '~empty' && !armed ? '' : ' hidden'}>${esc(t('cmp.emptyNote'))}</p>
    <div class="miz-btn-row" style="margin-top:0"><button type="button" class="miz-btn primary" data-act="cmp-save"${armed ? '' : ' disabled'}>${esc(t('cmp.save'))}</button>
      <button type="button" class="miz-btn" data-act="cmp-clear"${armed ? '' : ' disabled'}>${esc(t('cmp.clear'))}</button></div>
    ${UI.cmp.saving && lo ? cmpSaveHtml() : ''}
    <p class="ui-note">${esc(t('cmp.note'))}</p>`;
}
// « Partir de » : rien, l'emport importé ou copié en place, mes presets, « Vide », puis le groupe « Unités du module » :
// chaque autre unité du même type, tous vols confondus, qui a un emport (clé « u:groupe:unité »).
function cmpFromOptions(f, lo, unit) {
  const opts = [{ v: '', l: t('cmp.from.none') }];
  if (lo && lo.key === 'imp') opts.push({ v: 'imp', l: t('cmp.from.imp') });
  if (lo && lo.key === 'copy') opts.push({ v: 'copy', l: loLabel(lo) });
  presetsFor(unit.type).forEach(p => opts.push({ v: p.key, l: p.label }));
  opts.push({ v: '~empty', l: t('cmp.from.empty') });
  S.flights.forEach((g, gi) => {
    g.units.forEach((x, xi) => {
      if (x !== unit && x.type === unit.type && x.loadout) opts.push({ g: t('cmp.from.units'), v: 'u:' + gi + ':' + xi, l: tf('cmp.from.copy', flightLabel(g, gi), unitLabel(g, gi, x, xi)) });
    });
  });
  return opts;
}
// Les noms ont changé (frappe dans un nom de groupe ou d'unité) : l'en-tête du panneau et les libellés de « Partir de » les suivent sans autre geste.
function paintCmpNames() {
  const su = selUnit();
  if (!su) return;
  const el = document.getElementById('cmp-for-t');
  if (el) el.textContent = tf('cmp.for', flightLabel(su.f, su.fi), unitLabel(su.f, su.fi, su.u, su.ui));
  const sel = document.getElementById('cmp-from');
  if (sel) sel.innerHTML = optionsHtml(cmpFromOptions(su.f, su.u.loadout, su.u), su.u.loadout ? su.u.loadout.key : '');
}
function cmpDrawingHtml() {
  const view = CMP.view, W = view.viewBox[0], H = view.viewBox[1], small = CMP.small;
  const ids = Object.keys(view.stations).sort((a, b) => view.stations[a].x - view.stations[b].x);
  const credit = `<div class="cmp-credit">${esc(t('cmp.credit'))}</div>`;
  const cells = ids.map((k, i) => `<div class="cmp-st" data-st="${esc(k)}"${small ? '' : ' role="button" tabindex="0"'} style="left:${((i + 0.5) / ids.length * 100).toFixed(3)}%"><span class="n">${esc(k)}</span><span class="w"></span></div>`).join('');
  return `<div id="cmp-wrap" class="${small ? 'cmp-wrap-flat' : 'cmp-wrap-strip'}"><div class="cmp-view"><div class="cmp-svgbox" style="--r:${W / H}">${view.svg}</div>${credit}</div>
    <svg id="cmp-leads" aria-hidden="true"></svg><div class="cmp-strip" style="--n:${ids.length}">${cells}</div></div>`;
}
// Une ligne : numéro de la station, liste d'armes (pleine largeur), masse (colonne fixe, à droite) ; dessous, la station jumelle en clair et les réglages.
function cmpRowHtml(p, lo) {
  const current = cmpClsid(lo, p.n), pair = has(CMP.pairs, p.n) ? CMP.pairs[p.n] : null;
  let opts = '';
  if (current !== '' && p.allowed.indexOf(current) < 0) opts += `<option value="${esc(current)}">${esc((weaponLabel(CMP.type, current) || current) + ' ' + t('cmp.offTable'))}</option>`;
  opts += `<option value="">${esc(t('cmp.none'))}</option>`;
  opts += p.allowed.map(c => `<option value="${esc(c)}">${esc(weaponLabel(CMP.type, c) || c)}</option>`).join('');
  return `<div class="cmp-row" data-st="${esc(p.n)}"><span class="sn">${esc(p.n)}</span>
    <select class="fc-sel cmp-sel" data-st="${esc(p.n)}" aria-label="${esc(tf('lo.pylon', p.n))}">${opts}</select>
    <span class="cmp-kg"></span><div class="cmp-sub">${pair !== null ? `<span class="cmp-mirror">${esc(tf('cmp.mirror', pair))}</span><span class="cmp-nomirror" hidden>${esc(tf('cmp.noMirror', pair))}</span>` : ''}</div></div>`;
}
// Carburant, leurres, paillettes, canon : toujours montrés dès qu'une unité est choisie — aux valeurs de son emport, sinon aux défauts de la table.
// Sous le champ en kg, la barre du carburant (0 à 100 %) et sa valeur.
function fuelPct(raw, max) {
  const x = String(raw).trim().replace(',', '.');
  if (!/^-?\d+(\.\d+)?$/.test(x) || !(max > 0)) return null;
  return Math.max(0, Math.min(100, Math.round(Number(x) / max * 100)));
}
function fuelKg(pct, max) { return pct >= 100 ? String(max) : String(Math.round(max * pct / 100)); }
function cmpSettingsHtml(f, ui, lo) {
  const d = payloadDefaults(f.units[ui].type), at = `data-u="${ui}"`, val = k => (lo ? lo[k] : String(d[k]));
  const pct = fuelPct(val('fuel'), d.fuel);
  const bar = `<div class="fc-bar"><input type="range" class="fc-range" min="0" max="100" step="1" value="${pct === null ? 0 : pct}" style="--p:${pct === null ? 0 : pct}%" data-k="fuel-bar" ${at} aria-label="${esc(t('lo.fuelbar'))}" aria-valuetext="${esc(tf('lo.pct', pct === null ? 0 : pct))}"><span class="fc-pct" id="fuel-pct">${esc(tf('lo.pct', pct === null ? 0 : pct))}</span></div>`;
  const field = (k, step, disabled) => fieldHtml(`${t('lo.' + k)} · ${tf('lo.max', k === 'fuel' ? fmtMHz(d.fuel) : d[k])}`,
    numberInputHtml(`${at} data-k="${k}"${disabled ? ' disabled' : ''}`, val(k), 0, d[k], step) + (k === 'fuel' ? bar : ''));
  return `<div class="fc-set">${field('fuel', 'any')}${field('flare', '1')}${field('chaff', '1', d.chaff === 0)}${field('gun', '1')}</div>`;
}
function cmpSaveHtml() {
  const C = UI.cmp;
  return `<div class="fc-editor"><div class="fc-row">${fieldHtml(t('cmp.save.name'), inputHtml('data-k="cmp-name"', C.name, t('cmp.save.ph')))}
    <div class="ed-field fc-actions"><button type="button" class="miz-btn primary" data-act="cmp-save-go">${esc(t('cmp.save.go'))}</button></div>
    <div class="ed-field fc-actions"><button type="button" class="miz-btn" data-act="cmp-save-cancel">${esc(t('cmp.save.cancel'))}</button></div></div>
    <div class="fc-msg" id="cmp-save-msg">${esc(C.err)}</div></div>`;
}

// ----- Valeurs affichées : listes, masses, cases, total, station jumelle -----
function cmpUpdate() {
  const su = selUnit(), blk = document.getElementById('blk-cmp');
  if (!su || !blk || su.u.type === '') return;
  const lo = su.u.loadout, C = UI.cmp;
  let total = 0, unknown = false;
  CMP.pyl.forEach(({ n }) => {
    const clsid = cmpClsid(lo, n), row = blk.querySelector(`.cmp-row[data-st="${n}"]`);
    if (!row) return;
    const sel = row.querySelector('select');
    if (sel.value !== clsid) sel.value = clsid;
    const mass = clsid === '' ? 0 : payloadWeaponMass(clsid);
    if (mass === null) unknown = true; else total += mass;
    row.querySelector('.cmp-kg').textContent = clsid === '' ? '' : (mass === null ? '—' : cmpNum(mass) + ' kg');
    row.classList.toggle('sel', C.st === n);
    cmpUpdateSub(row, lo && lo.pylons[n] && lo.pylons[n].settings !== undefined, cmpNoMirror(lo, n, clsid));
    cmpUpdateCell(blk.querySelector(`.cmp-st[data-st="${n}"]`), clsid, C.st === n);
  });
  document.getElementById('cmp-total').innerHTML = `${esc(t('cmp.mass'))} <b>${esc(cmpNum(total) + ' kg' + (unknown ? ' + ?' : ''))}</b>`;
  // l'étiquette de l'emport, « Partir de », la ligne « emport vide » et les deux boutons suivent l'état (un emport créé par un réglage, un « modifié » qui paraît)
  const armed = cmpArmed(lo), line = document.getElementById('cmp-lo-line'), from = document.getElementById('cmp-from'), note = document.getElementById('cmp-empty-note');
  const want = lo ? lo.key : '';
  if (line) line.innerHTML = cmpLineHtml(lo);
  if (from && from.value !== want && Array.prototype.some.call(from.options, o => o.value === want)) from.value = want;
  if (note) note.hidden = !(lo && lo.key === '~empty' && !armed);
  blk.querySelectorAll('[data-act="cmp-save"], [data-act="cmp-clear"]').forEach(b => { b.disabled = !armed; });
  cmpDraw();
}
// La ligne sous la liste : la station jumelle n'y figure que si « Symétrique » est cochée ; la puce « réglages » quand l'arme en porte.
function cmpUpdateSub(row, hasSettings, noMirror) {
  const mirror = row.querySelector('.cmp-mirror'), none = row.querySelector('.cmp-nomirror'), sub = row.querySelector('.cmp-sub');
  let chip = row.querySelector('.fc-chip');
  if (mirror) mirror.hidden = !UI.cmp.sym || !!noMirror;
  if (none) none.hidden = !UI.cmp.sym || !noMirror;
  if (hasSettings && !chip) { chip = document.createElement('span'); chip.className = 'fc-chip'; chip.textContent = t('cmp.settings'); sub.appendChild(chip); }
  else if (!hasSettings && chip) chip.remove();
  sub.hidden = !Array.prototype.some.call(sub.children, e => !e.hidden);
}
function cmpUpdateCell(cell, clsid, selected) {
  if (!cell) return;
  cell.querySelector('.w').textContent = cmpShort(clsid);
  cell.title = clsid ? (weaponLabel(CMP.type, clsid) || clsid) : '';
  cell.classList.toggle('sel', selected);
  cell.classList.toggle('has', clsid !== '');
  if (cell.hasAttribute('role')) cell.setAttribute('aria-pressed', String(selected));
}
// Un trait pointillé par station : du point d'attache (petit rond) vers le bas, puis jusqu'à sa case.
function cmpDraw() {
  const svg = document.getElementById('cmp-leads');
  if (!svg || !CMP.view) return;
  const wrap = document.getElementById('cmp-wrap');
  const wr = wrap.getBoundingClientRect(), br = wrap.querySelector('.cmp-svgbox').getBoundingClientRect(), vr = wrap.querySelector('.cmp-view').getBoundingClientRect();
  const W = CMP.view.viewBox[0], H = CMP.view.viewBox[1], knee = vr.bottom - wr.top - (CMP.small ? 10 : 22);
  svg.setAttribute('viewBox', `0 0 ${wr.width} ${wr.height}`);
  svg.innerHTML = Object.keys(CMP.view.stations).map(k => {
    const s = CMP.view.stations[k], cell = wrap.querySelector(`.cmp-st[data-st="${k}"]`);
    if (!cell) return '';
    const cr = cell.getBoundingClientRect();
    const x = br.left - wr.left + s.x / W * br.width, y = br.top - wr.top + s.y / H * br.height;
    const ky = Math.max(knee, y + 4), cx = cr.left - wr.left + cr.width / 2, cy = cr.top - wr.top;
    return `<path data-st="${k}"${UI.cmp.st === k ? ' class="on"' : ''} d="M${x.toFixed(1)} ${y.toFixed(1)} L${x.toFixed(1)} ${ky.toFixed(1)} L${cx.toFixed(1)} ${cy.toFixed(1)}"/><circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="5"/>`;
  }).join('');
}

// ----- Choisir une arme, partir d'un preset, garder un preset -----
// Un choix sur une station ; « Symétrique » pose aussi sur sa jumelle l'arme miroir (payloadMirrorClsid : même CLSID, Left↔Right, même nom), et dit quand il n'y en a pas.
// « Vide » ne se pose sur la jumelle que si elle portait, juste avant ce choix, le miroir de l'arme d'avant. Un `settings` suit sa station tant que l'arme ne change pas.
function cmpChoose(n, clsid) {
  const su = selUnit();
  if (!su) return;
  const created = !su.u.loadout;                 // premier choix sur une unité sans emport : le panneau se redessine (réglages, boutons)
  if (created) su.u.loadout = makeLoadout(su.u.type, { key: '~empty', label: t('cmp.custom'), src: '' }, {}, null);
  const lo = su.u.loadout, before = cmpClsid(lo, n);
  const put = (k, v) => {
    if (v === '') delete lo.pylons[k];
    else if (cmpClsid(lo, k) !== v) lo.pylons[k] = { CLSID: v };
  };
  put(n, clsid);
  UI.cmp.st = n;
  const twin = (UI.cmp.sym && CMP.view && has(CMP.pairs, n)) ? CMP.pyl.filter(x => x.n === CMP.pairs[n])[0] : null;
  if (twin) {
    if (clsid === '') {
      const was = payloadMirrorClsid(before, twin.allowed);
      if (was !== '' && cmpClsid(lo, twin.n) === was) put(twin.n, '');
    } else {
      const m = payloadMirrorClsid(clsid, twin.allowed);
      if (m !== '') put(twin.n, m);
    }
  }
  loTouch(lo);
  if (created) {
    renderRight();
    const trigger = document.querySelector(`#blk-cmp .cmp-row[data-st="${n}"] .tbm-trigger`);
    if (trigger) trigger.focus({ preventScroll: true });
  } else cmpUpdate();
  refreshAll();
}
// Copie l'emport d'une autre unité : stations (avec leurs settings), carburant, leurres, paillettes, canon. `from` : le nom de l'unité source.
function copyLoadout(type, src, from) {
  const lo = { key: 'copy', label: tf('cmp.copied', from), from: from, src: t('lo.src.copy'), modified: false, pylons: cleanPylons(src.pylons) };
  LO_FIELDS.forEach(k => { lo[k] = src[k] !== undefined && src[k] !== null ? String(src[k]) : String(loLimit(type, k)); });
  lo.base = loSnap(lo);
  return lo;
}
function cmpBase(key) {
  const su = selUnit();
  if (!su) return;
  const type = su.u.type, prev = su.u.loadout;
  if (key === '') su.u.loadout = null;
  else if (key === '~empty') su.u.loadout = makeLoadout(type, { key: key, label: t('cmp.custom'), src: '' }, {}, prev);
  else if (key.indexOf('u:') === 0) {            // « Copier : groupe · unité » : une copie, plus aucun lien avec l'unité source
    const a = key.split(':'), gi = Number(a[1]), xi = Number(a[2]), g = S.flights[gi], x = g && g.units[xi];
    if (x && x !== su.u && x.loadout && x.type === type) su.u.loadout = copyLoadout(type, x.loadout, unitLabel(g, gi, x, xi));
  }
  else if (key !== 'imp' && key !== 'copy') {    // 'imp', 'copy' : déjà l'emport importé, déjà la copie
    const hit = presetsFor(type).filter(p => p.key === key)[0];
    if (hit) su.u.loadout = makeLoadout(type, { key: key, label: hit.label, src: hit.src }, hit.preset.pylons, prev);
  }
  Object.assign(UI.cmp, { saving: false, err: '' });
  renderRight();
  refreshAll();
}
function cmpSaveGo() {
  const su = selUnit(), C = UI.cmp;
  if (!su || !su.u.loadout) return;
  const name = C.name.trim(), type = su.u.type, lo = su.u.loadout;
  const fail = msg => { C.err = msg; const e = document.getElementById('cmp-save-msg'); if (e) e.textContent = msg; };
  const pylons = cleanPylons(lo.pylons);
  if (!name) return fail(t('cmp.save.err.name'));
  if ((LIB.mine[type] || []).some(p => presetName(p) === name)) return fail(tf('cmp.save.err.dup', TYPE_LABEL[type]));
  if (!Object.keys(pylons).length) return fail(t('cmp.save.err.none'));
  const preset = { id: newPresetId(), name: name, pylons: pylons };
  (LIB.mine[type] = LIB.mine[type] || []).push(preset);
  Object.assign(lo, { key: 'm:' + preset.id, label: name, src: t('lo.src.mine'), modified: false });
  lo.base = loSnap(lo);
  Object.assign(C, { saving: false, err: '', name: '' });
  renderRight();
  refreshAll();
  showToast(tf('cmp.save.ok', name), { type: 'ok' });
}

// ----- Mes presets : la liste (on en supprime, on ne les renomme pas) et le bouton qui charge des .lua -----
// Un preset est un emport gardé sous un nom (stations seules) ; il sert de point de départ. Ce qui part dans le paquet est l'emport, jamais le preset.
function presetsHtml() {
  const rep = LIB.report, lines = [];
  if (rep) {
    lines.push(`<div class="ui-note">${esc(tf('pr.report', rep.added))}${rep.skipped ? esc(' · ' + tf('pr.skipped', rep.skipped)) : ''}</div>`);
    rep.errors.forEach(e => lines.push(`<div class="ui-avert">⚠ ${esc(e)}</div>`));
  }
  const rows = [];
  PAYLOAD_TYPES.forEach(ty => (LIB.mine[ty] || []).forEach((p, i) => rows.push(`<div class="fc-file"><span class="fc-file-n">${esc(presetName(p))}</span><span class="snap-flight-tag">${esc(TYPE_LABEL[ty])}</span>
    <button type="button" class="pk-x" data-act="rm-mine" data-ty="${esc(ty)}" data-i="${i}" aria-label="${esc(t('pr.delete'))}" title="${esc(t('pr.delete'))}">✕</button></div>`)));
  return `<section class="fc-block" id="blk-pr"><div class="fc-bh">${esc(t('sec.presets'))}</div><div class="fc-bc">
    <div class="miz-btn-row" style="margin-top:0"><button type="button" class="miz-btn" data-act="load-lua">${esc(t('pr.load'))}</button></div>${lines.join('')}
    <div class="fc-h" style="margin-top:0">${esc(tf('pr.mine', mineCount()))}</div>
    <div class="fc-lib">${rows.length ? rows.join('') : `<p class="ui-note">${esc(t('pr.none'))}</p>`}</div></div></section>`;
}
// Des .lua d'exemple : leurs presets rejoignent « Mes presets » sans écran intermédiaire ; un nom déjà pris est ignoré, et le bloc le dit.
async function loadLuaFiles(files) {
  const report = { added: 0, skipped: 0, errors: [] };
  for (const file of files) {
    let parsed;
    try { parsed = parseUnitPayloads(await file.text()); }
    catch (e) { report.errors.push(e.line ? tf('pr.err', file.name, e.line, t('err.code.' + e.code)) : file.name); continue; }
    if (!parsed.supported) { report.errors.push(tf('pr.unsup', file.name, parsed.unitType)); continue; }
    const list = (LIB.mine[parsed.unitType] = LIB.mine[parsed.unitType] || []);
    parsed.presets.forEach(p => {
      const name = presetName(p).trim(), pylons = cleanPylons(p.pylons);
      if (!name || !Object.keys(pylons).length) return;
      if (list.some(q => presetName(q) === name)) { report.skipped++; return; }
      list.push({ id: newPresetId(), name: name, pylons: pylons });
      report.added++;
    });
  }
  LIB.report = report;
  saveWork();
  renderRight();
  showToast(tf('pr.added', report.added), { type: 'ok' });
}


// ---------- 5. Import : la fenêtre est celle du bloc commun (import_block.py) ; ici seulement ses rappels ----------
// Le bloc lit HQ, le briefing en cours ou un fichier et écrit dans la fiche partagée en une fois, l'emport déjà converti (loadoutFrom : loadoutFromPayload). Le module relit la fiche à son rappel,
// puis choisit la première unité du premier groupe importé. Un emport brut (payloadIn) ne vient que du Route Planner : gsFixRaw le convertit sans toucher au reste du groupe.
function fcImportBefore() {
  flushWork();         // ce que l'on a tapé part dans la fiche avant que le bloc la lise
  UI.clamped = 0;      // le compte des réglages ramenés à la limite est celui de cet import
  UI.impRefused = false;
  const cur = (typeof impCur === 'function') ? impCur() : null;
  if (cur && typeof cur.theatre === 'string' && cur.theatre !== '' && !thOk(cur.theatre)) {
    // une source sur un théâtre hors des quatorze : refusée, rien n'est importé (la fenêtre n'a pas d'annulation : les lignes et le théâtre de la source sont vidés avant son écriture)
    UI.impRefused = true;
    const th = cur.theatre;
    cur.theatre = '';
    cur.rows.forEach(r => { r.managed = false; if (r.kind !== 'bg') r.chk = Object.assign({}, r.chk, { route: false }); r.kind = r.kind === 'bg' ? 'x' : r.kind; });
    showToast(tf('open.theatre.unknown', th), { type: 'err' });
  }
  const g = gsRead();
  UI.impPre = !g || !g.theatre || !g.flights.length;      // la fiche était vide ou sans théâtre : l'import peut lui en poser un
}
function fcImported(res) {
  if (UI.impRefused) { UI.impRefused = false; UI.impPre = false; renderAll(); return; }
  if (res.failed && !res.fcIds.length) { renderAll(); return; }
  const gi = gsRead();       // le théâtre que l'import a posé, lu avant gsPull (qui rend la fiche au théâtre commun quand aucun groupe ne porte de route)
  gsPull();
  if (UI.impPre) {       // l'import a posé le théâtre de la fiche : le théâtre commun le prend, sans question (le Route Planner et le Datacard Generator suivent)
    if (gi && thOk(gi.theatre) && gi.theatre !== S.theatre) thSet(gi.theatre);
  }
  UI.impPre = false;
  const k = S.flights.findIndex(f => f.fcId === res.fcIds[0]);
  S.sel = { f: Math.max(0, k), u: 0 };       // la première unité du premier groupe importé
  Object.assign(UI.cmp, { saving: false, err: '', st: null });
  renderAll();
  commitNow();
  showToast(res.failed ? '\u26a0 ' + res.text + ' · ' + t('toast.gsFull').replace(/^\u26a0\s*/, '') : res.text, { type: res.failed ? 'err' : 'ok', ms: res.failed ? 6000 : res.ms });
}


// ---------- 6. Fichiers : Ouvrir, Sauvegarder, Exporter, Effacer ----------
function fcDownload(blob, name) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = name;
  document.body.appendChild(a); a.click(); document.body.removeChild(a);
  setTimeout(() => URL.revokeObjectURL(url), 2000);
}
/* Le nom d'un fichier choisi : sans « .json », accents ôtés, tout ce qui n'est pas lettre, chiffre, _ + - devient « _ » ; vide si rien ne reste */
function cleanFname(v) {
  return str(v).trim().replace(/\.json$/i, '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/[^A-Za-z0-9_+-]+/g, '_').replace(/_{2,}/g, '_').replace(/^_+|_+$/g, '').slice(0, 100);
}
const FN = { name: '', opener: null, run: null, titleKey: '', goKey: '', at: 0, bodyFn: null, bodyEl: null, headFn: null, headEl: null, wide: false, blocked: false };
// Un nom par défaut : la partie variable est nettoyée et coupée à 40 caractères ; l'horodatage s'ajoute ensuite, en fin de nom
function fnPart(v, fallback) { return cleanFname(v).slice(0, 40) || fallback; }
function fnSync() {
  document.getElementById('fn-go').disabled = cleanFname(FN.name) === '' || FN.blocked;
}
function fnRender() {
  document.getElementById('fn-title').textContent = t(FN.titleKey);
  document.getElementById('fn-go').textContent = t(FN.goKey);
  document.getElementById('fn-close').setAttribute('aria-label', t('fn.close'));
  fnBodyMount();
}
/* Un corps facultatif (liste de ce que l'écriture touche) entre le titre et le champ du nom ; absent, le DOM de la fenêtre ne change pas */
function fnBodyMount() {
  if (FN.bodyEl) { FN.bodyEl.remove(); FN.bodyEl = null; }
  if (FN.headEl) { FN.headEl.remove(); FN.headEl = null; }
  if (!FN.bodyFn) return;
  const el = document.createElement('div');
  el.className = 'fn-del';
  el.innerHTML = FN.bodyFn();
  const panel = document.querySelector('#fn-modal .ui-panel');
  if (FN.headFn) {
    const hd = document.createElement('div');   // un texte en tête, hors du corps qui défile
    hd.className = 'snap-meta fn-head';
    hd.textContent = FN.headFn();
    panel.insertBefore(hd, panel.querySelector('.ui-field'));
    FN.headEl = hd;
  }
  panel.insertBefore(el, panel.querySelector('.ui-field'));
  FN.bodyEl = el;
}
/* o : titleKey, goKey, ext, name (le défaut, sans extension), opener, run(nom nettoyé), body (facultatif : () => HTML), blocked (facultatif : le bouton qui écrit reste inactif) */
function fnAsk(o) {
  FN.name = cleanFname(o.name);
  FN.run = o.run;
  FN.opener = o.opener || document.activeElement;
  FN.at = performance.now();
  FN.titleKey = o.titleKey; FN.goKey = o.goKey;
  FN.bodyFn = o.body || null;
  FN.headFn = o.head || null;
  FN.wide = !!o.wide;
  document.querySelector('#fn-modal .ui-panel').classList.toggle('ui-wide', FN.wide);
  FN.blocked = !!o.blocked;
  const inp = document.getElementById('fn-name');
  inp.value = FN.name;
  document.getElementById('fn-ext').textContent = o.ext;
  fnRender();
  fnSync();
  document.getElementById('fn-modal').hidden = false;
  inp.focus({ preventScroll: true });
  inp.select();
}
function fnClose() {
  document.getElementById('fn-modal').hidden = true;
  const o = FN.opener;
  FN.opener = null; FN.run = null; FN.bodyFn = null; FN.headFn = null; FN.blocked = false;
  document.querySelector('#fn-modal .ui-panel').classList.remove('ui-wide');
  if (FN.bodyEl) { FN.bodyEl.remove(); FN.bodyEl = null; }
  if (FN.headEl) { FN.headEl.remove(); FN.headEl = null; }
  if (o && o.focus && !o.disabled) { try { o.focus({ preventScroll: true }); } catch (e) {} }
}
function fnGo() {
  const name = cleanFname(FN.name), run = FN.run;
  if (name === '' || !run || FN.blocked) return;
  fnClose();
  run(name);
}
function fnBind() {
  ['fn-close', 'fn-cancel'].forEach(id => document.getElementById(id).addEventListener('click', fnClose));
  // le fond ignore les clics des 400 ms qui suivent l'ouverture : le 2e clic d'un double-clic sur le bouton qui ouvre ne ferme pas la fenêtre
  document.getElementById('fn-backdrop').addEventListener('click', () => { if (performance.now() - FN.at > 400) fnClose(); });
  document.getElementById('fn-go').addEventListener('click', fnGo);
  const inp = document.getElementById('fn-name');
  inp.addEventListener('input', e => { FN.name = e.target.value; fnSync(); });
  inp.addEventListener('keydown', e => { if (e.key === 'Enter') { e.preventDefault(); if (!e.repeat) fnGo(); } });
  /* Échap, ✕ et le piège du focus : le bloc d'interface commun (la fenêtre est une .ui-modal) */
}

/* Un fichier remis à la personne : le partage du système (un File) quand il le permet, sinon un téléchargement ; un partage rejeté conduit au téléchargement.
   download(blob, nom) est le téléchargement de l'appelant. */
function shareOrDownload(blob, fname, mime, title, download) {
  if (navigator.share && navigator.canShare) {
    try {
      const file = new File([blob], fname, { type: mime });
      if (navigator.canShare({ files: [file] })) {
        navigator.share({ files: [file], title: title, text: fname })
          .catch(() => download(blob, fname));
        return;
      }
    } catch (e) {}
  }
  download(blob, fname);
}

// Mes presets d'un fichier de travail rejoignent les miens ; un nom déjà pris est ignoré. Un preset garde son identifiant, ou en reçoit un.
function mergeMine(mine) {
  if (!isObj(mine)) return;
  PAYLOAD_TYPES.forEach(ty => {
    const list = (LIB.mine[ty] = LIB.mine[ty] || []);
    (Array.isArray(mine[ty]) ? mine[ty] : []).forEach(p => {
      if (isObj(p) && isObj(p.pylons) && presetName(p) !== '' && !list.some(q => presetName(q) === presetName(p))) {
        const id = (typeof p.id === 'string' && p.id !== '' && !list.some(q => q.id === p.id)) ? p.id : newPresetId();
        list.push({ id: id, name: presetName(p), pylons: p.pylons });
      }
    });
  });
  PAYLOAD_TYPES.forEach(ty => (LIB.mine[ty] || []).forEach(p => { if (typeof p.id !== 'string' || p.id === '') p.id = newPresetId(); }));
}
// Un emport d'un état d'avant garde la clé « m:<rang> » de son preset : elle est remplacée par l'identifiant du preset de ce rang dans `mine` (retrouvé par son nom).
function remapPresetKeys(mine) {
  S.flights.forEach(f => f.units.forEach(u => {
    const lo = u.loadout, m = lo && typeof lo.key === 'string' ? /^m:(\d+)$/.exec(lo.key) : null;
    if (!m) return;
    const p = isObj(mine) && Array.isArray(mine[u.type]) ? mine[u.type][Number(m[1])] : null;
    const hit = isObj(p) ? (LIB.mine[u.type] || []).filter(q => presetName(q) === presetName(p))[0] : null;
    if (hit) lo.key = 'm:' + hit.id;
  }));
}
// Le texte d'un refus de la fenêtre d'import commune : la phrase de la suite pour un JSON illisible, sinon la phrase du bloc précédée de « ⚠ »
function fcRejectText(key, args) {
  if (key === 'rej.json') return t('msg.jsonUnreadable');
  return '\u26a0 ' + impTf.apply(null, [key].concat(args || []));
}
// Ouvrir : un fichier de travail (clé fc) ou un paquet de vol ; il remplace le contenu du module. Le fichier impose son théâtre : un théâtre hors des quatorze le refuse, un autre que le théâtre commun
// demande d'abord (s'il y a des groupes à remplacer) ; un fichier de travail sans théâtre laisse le théâtre commun.
function openFile(file) {
  impReadJsonFile(file, r => {
    if (r.reject) { showToast(fcRejectText(r.reject), { type: 'err' }); return; }
    const o = r.parsed;
    let ignored = 0, warn = '', res = null;
    const work = isObj(o) && isObj(o.fc) && isObj(o.fc.state) && Array.isArray(o.fc.state.flights);
    if (!work && isObj(o) && PACKAGE_FORMATS.indexOf(o.format) >= 0) {
      res = impReadPackage(o, file.name);
      if (!res.reject && !res.src.rows.some(f => f.managed)) res.reject = 'rej.noManaged';
      if (res.reject) { showToast(fcRejectText(res.reject, res.args), { type: 'err' }); return; }
    } else if (!work) {
      const f = isObj(o) ? o.format : undefined;
      const x = ((typeof f === 'string' && f !== '') || typeof f === 'number') ? String(f) : t('rej.unknown');
      showToast(tf('msg.formatUnsupported', x, t('fmt.work') + ', ' + t('fmt.pkg')), { type: 'err' });
      return;
    }
    const fth = work ? str(o.fc.state.theatre) : res.src.theatre;
    if (fth !== '' && !thOk(fth)) { showToast(tf('open.theatre.unknown', fth), { type: 'err' }); return; }
    // Le fichier remplace le travail sans question : l'ancien est gardé et « Restaurer » le remet (bloc d'interface commun) ; le toast dit aussi un changement de théâtre.
    const thChanged = fth !== '' && fth !== S.theatre && S.flights.length > 0;
    flushWork();       // la frappe en attente part dans le stockage avant que « Remplacer » en prenne la copie
    replaceWithRestore({
      keys: FC_REPLACE_KEYS, mem: fcMem, back: fcBack,
      run: () => {
        if (work) { restoreState(o.fc.state); UI.clamped = 0; mergeMine(o.fc.mine); remapPresetKeys(o.fc.mine); }
        else {
          UI.clamped = 0;
          ignored = res.src.rows.filter(f => !f.managed).length;
          const built = impBuildGroups(res.src.rows.filter(f => f.managed), res.src);
          restoreState({ flights: built.flights, sel: { f: 0, u: 0 } });       // l'emport brut (payloadIn) est converti par restoreFlight
          warn = built.warn.join(' · ');
        }
        if (fth !== '') { S.theatre = fth; thWriteKey(fth); }
        S.sel = { f: 0, u: 0 };                    // la première unité du premier groupe ouvert
        UI.exportTried = false;
        UI.rtChoose = null;
        Object.assign(UI.cmp, { saving: false, err: '', st: null });
        clearTimeout(_saveTimer);
        if (gsReplaceAll(S.theatre, JSON.parse(JSON.stringify(S.flights)))) gsMarkAll();       // le fichier remplace la fiche entière, théâtre compris
        thFill();
        renderAll();
        writeState();
      },
      msg: () => tf('open.done', S.flights.length) + (ignored ? ' · ' + tf('open.ignored', ignored) : '') + (warn ? ' · ' + warn : '') + (thChanged ? ' · ' + tf('open.theatre.set', theatreName(S.theatre)) : '')
    });
  });
}
// Ce que « Ouvrir » écrit : l'état du module, la fiche des groupes, le théâtre commun (et les clés que la migration de la fiche pourrait toucher).
const FC_REPLACE_KEYS = ['fc_state_v1', 'flight_set_v1', 'flight_set_v1_illisible', 'mp_theatre_v1', 'route_state_v1', 'route_set_v1'];
function fcMem() {
  flushWork();
  return { theatre: S.theatre, flights: clone(S.flights), sel: clone(S.sel), mine: clone(LIB.mine) };
}
// « Restaurer » : le stockage est déjà revenu à l'octet (bloc d'interface commun) ; le module reprend sa copie et se redessine, sans rien réécrire.
function fcBack(m) {
  clearTimeout(_saveTimer); _saveTimer = 0;
  S.theatre = m.theatre; S.flights = clone(m.flights); S.sel = clone(m.sel); LIB.mine = clone(m.mine);
  GS.removed = [];
  gsMarkAll();
  UI.exportTried = false; UI.rtChoose = null; UI.clamped = 0;
  Object.assign(UI.cmp, { saving: false, err: '', st: null });
  thFill();
  renderAll();
  clearTimeout(_saveTimer); _saveTimer = 0;
}
// « Exemple » : deux groupes, au geste « Remplacer » (on fait, on garde l'ancien, « Restaurer » 12 s, aucune question) ; chacun est ce que « + groupe » donne, puis le type posé sur ses deux unités.
function loadExample() {
  flushWork();
  replaceWithRestore({
    keys: FC_REPLACE_KEYS, mem: fcMem, back: fcBack,
    run: () => {
      const mk = (type, n) => { const f = newFlight(); f.name = t('ex.group') + ' ' + n; f.coalition = 'red'; f.units = [newUnit(type), newUnit(type)]; return f; };
      S.flights = [mk('Mi-24P', 1), mk('Mi-8MT', 2)];
      S.sel = { f: 0, u: 0 };
      UI.clamped = 0; UI.exportTried = false; UI.rtChoose = null;
      Object.assign(UI.cmp, { saving: false, err: '', st: null });
      clearTimeout(_saveTimer);
      if (gsReplaceAll(S.theatre, JSON.parse(JSON.stringify(S.flights)))) gsMarkAll();
      renderAll();
      writeState();
    },
    msg: () => t('toast.example')
  });
}
function saveFile() {
  fnAsk({
    titleKey: 'fn.save.title', goKey: 'fn.save.go', ext: '.json',
    name: packageFileName('fc'),
    opener: document.getElementById('btn-save'),
    run: name => {
      const text = JSON.stringify(buildWorkFile(), null, 1);
      shareOrDownload(new Blob([text], { type: 'application/json' }), name + '.json', 'application/json', 'Flight Configurator', fcDownload);
      showToast(tf('save.done', name + '.json'), { type: 'ok' });
    }
  });
}
function exportFile() {
  if (exportIssues().length) {
    UI.exportTried = true;
    refreshBar();
    const bar = document.getElementById('fc-status');
    if (bar && bar.scrollIntoView) bar.scrollIntoView({ block: 'nearest' });
    return;
  }
  fnAsk({
    titleKey: 'fn.export.title', goKey: 'fn.export.go', ext: '.json',
    name: packageFileName(),
    opener: document.getElementById('btn-export'),
    run: name => {
      const text = JSON.stringify(buildPackage(), null, 1);
      shareOrDownload(new Blob([text], { type: 'application/json' }), name + '.json', 'application/json', 'Flight Configurator', fcDownload);
      showToast(tf('export.done', name + '.json'), { type: 'ok' });
    }
  });
}
async function clearAll() {
  if (!await askConfirm({ title: t('clear.confirm.title'), text: t('clear.confirm.text'), verb: t('ui.verb.clear'), danger: true })) return;
  Object.assign(S, { flights: [], sel: { f: 0, u: 0 } });       // le théâtre commun reste
  UI.clamped = 0;
  UI.exportTried = false;
  UI.cmp.saving = false;
  renderAll();
  commitNow();
}
// ---------- 7. Événements ----------
function addFlight() {
  // le vol sur lequel on travaille garde son état, les autres se replient dès qu'il y a plus de deux vols, le nouveau est déplié
  foldFreeze();
  const prev = S.flights[S.sel.f], nf = newFlight();
  S.flights.push(nf);
  if (S.flights.length > 2) S.flights.forEach(x => { if (x !== prev && x !== nf) UI.fold.set(x, 'closed'); });
  UI.fold.set(nf, 'open');
  S.sel = { f: S.flights.length - 1, u: 0 };
  renderAll();
  commitNow();
}
// Un groupe déjà dans la fiche commune des groupes se retire de tous les modules : une question d'abord ; un groupe qui n'y est pas encore se retire sans question.
async function askRemoveFlight(fi) {
  const f = S.flights[fi], g = gsRead();
  if (f && g && g.flights.some(x => x.fcId === f.fcId)) {
    if (!await askConfirm({ title: tf('fl.remove.confirm.title', flightLabel(f, fi)), text: t('fl.remove.confirm.text'), verb: t('ui.verb.remove'), danger: true })) return;
  }
  const i = S.flights.indexOf(f);
  if (i >= 0) removeFlight(i);
}
function removeFlight(fi) {
  if (S.flights[fi] && GS.removed.indexOf(S.flights[fi].fcId) < 0) GS.removed.push(S.flights[fi].fcId);
  const was = S.sel.f === fi;
  S.flights.splice(fi, 1);
  if (was) { S.sel = { f: 0, u: 0 }; Object.assign(UI.cmp, { saving: false, err: '', st: null }); }
  else if (S.sel.f > fi) S.sel.f--;
  renderAll();
  commitNow();
}
function removeUnit(fi, ui) {
  S.flights[fi].units.splice(ui, 1);
  if (S.sel.f === fi && S.sel.u === ui) { S.sel = { f: fi, u: 0 }; Object.assign(UI.cmp, { saving: false, err: '', st: null }); }
  else if (S.sel.f === fi && S.sel.u > ui) S.sel.u--;
  renderAll();
}
function startSavePreset() {
  Object.assign(UI.cmp, { saving: true, err: '', name: '' });
  renderRight();
  const input = document.querySelector('#blk-cmp input[data-k="cmp-name"]');
  if (input) input.focus();
}
function backToUnit() {
  const su = selUnit();
  if (!su) return;
  if (!flightOpen(su.f, su.fi)) { setFold(su.f, true); paintFold(); }
  if (su.u.folded) { su.u.folded = false; paintUnitFold(su.fi, su.ui); saveWork(); }      // une unité repliée se déplie pour y revenir
  const el = unitEl(su.fi, su.ui);
  if (!el) return;
  el.scrollIntoView({ block: 'start', behavior: 'smooth' });
  const btn = el.querySelector('[data-act="see-cmp"]');
  if (btn) btn.focus({ preventScroll: true });
}
// Les actions des boutons, par data-act ; c = { b (le bouton), fi (vol), ui (unité) }.
const ACTIONS = {
  'add-flight': () => addFlight(),
  'rm-flight': c => askRemoveFlight(c.fi),
  'fold': c => { setFold(S.flights[c.fi], !flightOpen(S.flights[c.fi], c.fi)); paintFold(); },
  'fold-all': () => { const open = !anyFlightOpen(); foldFreeze(); S.flights.forEach(f => UI.fold.set(f, open ? 'open' : 'closed')); paintFold(); },
  'add-unit': c => {
    const us = S.flights[c.fi].units, first = !us.length;
    us.push(newUnit(first ? DEFAULT_TYPE : us[us.length - 1].type));
    if (first && S.sel.f === c.fi) { S.sel.u = 0; renderAll(); } else { renderLeft(); refreshAll(); }       // la première unité d'un groupe choisi : la colonne de droite change aussi
  },
  'rm-unit': c => removeUnit(c.fi, c.ui),
  'fold-unit': c => { const u = S.flights[c.fi].units[c.ui]; u.folded = !u.folded; paintUnitFold(c.fi, c.ui); saveWork(); },
  'route-pick': c => routePick(c.b.getAttribute('data-rid')),
  'route-change': () => { const su = selUnit(); if (su) { UI.rtChoose = su.f.fcId; renderRouteBlock(); } },
  'route-keep': () => { UI.rtChoose = null; renderRouteBlock(); },
  'route-remove': () => { const su = selUnit(); if (su) { su.f.route = null; delete su.f.routeLink; UI.rtChoose = null; routeChanged(); } },
  'see-route': c => {
    if (S.sel.f !== c.fi) selectUnit(c.fi, 0);
    const b = document.getElementById('blk-route');
    if (b) b.scrollIntoView({ block: 'start', behavior: 'smooth' });
  },
  'copy-radios': c => {
    const f = S.flights[c.fi], src = f.units[c.ui];
    f.units.forEach((u, k) => { if (k !== c.ui && u.type === src.type) { u.radios = clone(src.radios); REFUSED.delete(u); } });       // « Recopier » copie la fiche : jamais un texte refusé, et celui des autres unités s'efface avec leurs valeurs
    renderLeft(); refreshAll();
  },
  'see-cmp': c => { selectUnit(c.fi, c.ui); const b = document.getElementById('blk-cmp'); if (b && window.innerWidth < 1100) b.scrollIntoView({ block: 'start', behavior: 'smooth' }); },
  'back-unit': () => backToUnit(),
  'cmp-save': () => startSavePreset(),
  'cmp-save-cancel': () => { UI.cmp.saving = false; renderRight(); },
  'cmp-save-go': () => cmpSaveGo(),
  'cmp-clear': () => { const su = selUnit(); if (su) { su.u.loadout = null; UI.cmp.saving = false; renderRight(); refreshAll(); } },
  'load-lua': () => document.getElementById('fc-in-lua').click(),
  'rm-mine': c => { (LIB.mine[c.b.getAttribute('data-ty')] || []).splice(Number(c.b.getAttribute('data-i')), 1); saveWork(); renderRight(); }
};
function onClick(e) {
  const b = e.target.closest ? e.target.closest('[data-act]') : null;
  const card = e.target.closest ? e.target.closest('#col-left .fc-unit') : null;
  const empty = e.target.closest ? e.target.closest('#col-left .fc-nounit') : null;
  if (empty) selectUnit(Number(empty.closest('.fc-flight').getAttribute('data-f')), 0);
  if (card && !(b && ['rm-unit', 'rm-flight', 'fold-unit'].indexOf(b.getAttribute('data-act')) >= 0)) selectUnit(Number(card.closest('.fc-flight').getAttribute('data-f')), Number(card.getAttribute('data-u')));
  if (!b || b.disabled || !has(ACTIONS, b.getAttribute('data-act'))) return;
  const fe = b.closest('.fc-flight'), ue = b.closest('.fc-unit');
  ACTIONS[b.getAttribute('data-act')]({
    b: b,
    fi: fe ? Number(fe.getAttribute('data-f')) : -1,
    ui: ue ? Number(ue.getAttribute('data-u')) : (b.hasAttribute('data-u') ? Number(b.getAttribute('data-u')) : -1)
  });
}

// Saisie : on met l'état à jour à chaque touche ; les bornes s'appliquent à la validation du champ (onChange).
function onInput(e) {
  const el = e.target, k = el.getAttribute && el.getAttribute('data-k');
  if (!k) return;
  if (k === 'cmp-name') { UI.cmp.name = el.value; return; }
  const fe = el.closest('.fc-flight'), fi = fe ? Number(fe.getAttribute('data-f')) : -1, f = S.flights[fi];
  const u = f && el.hasAttribute('data-u') ? f.units[Number(el.getAttribute('data-u'))] : null;
  if (k === 'name') { f.name = el.value; paintFlightName(f, fi, fe); paintCmpNames(); if (fi === S.sel.f) renderRouteBlock(); refreshLiveryLists(fe); }
  else if (k === 'uname') { u.name = el.value; paintCmpNames(); refreshLiveryLists(fe); }
  else if (k === 'callsign') u.callsign = el.value;
  else if (k === 'onboard') u.onboard = el.value;
  else if (k === 'chan') {
    const r = Number(el.getAttribute('data-r'));
    const c = Number(el.getAttribute('data-c')), p = parseFreq(el.value);
    if (p.empty || (p.v !== undefined && inBand(radioBand(u.type, r), p.v))) { (u.radios[r] = u.radios[r] || {})[c] = el.value; refusedClear(u, r, c); }       // une saisie valide (un champ vidé aussi) s'écrit
    else refusedSet(u, r, c, el.value);       // refusée : jamais écrite, la fiche garde la valeur d'avant ; le champ garde le texte tapé, marqué, et l'export est bloqué
    paintRadioMsg(fi, Number(el.getAttribute('data-u')), r);
  } else if (LO_FIELDS.indexOf(k) >= 0) {
    const su = selUnit();
    loSetting(k, el.value);
    if (k === 'fuel' && su) paintFuelBar(fuelPct(el.value, loLimit(su.u.type, 'fuel')), true);
  } else if (k === 'fuel-bar') onFuelBar(el);
  refreshAll();
}
// Le nom d'un groupe change : son titre, l'étiquette de son bouton de repli et les noms par défaut de ses unités (affichés en grisé) suivent la frappe.
function paintFlightName(f, fi, fe) {
  fe.querySelector('.fc-ftitle').textContent = flightLabel(f, fi);
  const btn = fe.querySelector('.fc-fold');
  if (btn) btn.setAttribute('aria-label', foldLabel(f, fi, flightOpen(f, fi)));
  f.units.forEach((x, ui) => {
    const inp = fe.querySelector(`.fc-unit[data-u="${ui}"] input[data-k="uname"]`);
    if (inp) inp.placeholder = unitDefaultName(f, fi, ui);
  });
}
// Un réglage (carburant, leurres, paillettes, canon) de l'unité choisie. Une unité « non renseigné » qu'on règle reçoit un emport « Vide » qui porte ces
// réglages (HQ les posera sans arme) ; tant que la valeur est celle de la table, rien n'est créé. Rend l'emport, ou null.
function loSetting(k, raw) {
  const su = selUnit();
  if (!su) return null;
  if (!su.u.loadout) {
    const c = clampNum(raw, 0, loLimit(su.u.type, k), k !== 'fuel');
    if (c.v === null || Number(c.v) === loLimit(su.u.type, k)) return null;
    su.u.loadout = makeLoadout(su.u.type, { key: '~empty', label: t('cmp.custom'), src: '' }, {}, null);
    cmpUpdate();       // « Partir de », la ligne et les boutons ; le panneau n'est pas redessiné : le champ garde le focus
  }
  su.u.loadout[k] = raw;
  const was = su.u.loadout.modified;
  loTouch(su.u.loadout);
  if (su.u.loadout.modified !== was) { const line = document.getElementById('cmp-lo-line'); if (line) line.innerHTML = cmpLineHtml(su.u.loadout); }      // la puce « modifié » paraît ou s'efface
  return su.u.loadout;
}
// La barre du carburant et sa valeur en % (sans toucher à la position de la barre quand c'est elle qu'on déplace).
function paintFuelBar(pct, moveBar) {
  const bar = document.querySelector('#blk-cmp input[data-k="fuel-bar"]'), out = document.getElementById('fuel-pct');
  if (!bar || pct === null) return;
  if (moveBar) bar.value = String(pct);
  bar.style.setProperty('--p', pct + '%');
  bar.setAttribute('aria-valuetext', tf('lo.pct', pct));
  if (out) out.textContent = tf('lo.pct', pct);
}
// La barre bouge : elle écrit les kg (arrondis au kg, le maximum de la table à 100 %) dans le champ et dans l'emport.
function onFuelBar(el) {
  const su = selUnit();
  if (!su) return;
  const pct = Number(el.value), kg = fuelKg(pct, loLimit(su.u.type, 'fuel'));
  loSetting('fuel', kg);
  const num = document.querySelector('#blk-cmp input[data-k="fuel"]');
  if (num) num.value = kg;
  paintFuelBar(pct, false);
}
// Validation d'un champ : un réglage d'emport hors limites est ramené à la limite de l'appareil (0 pour une valeur négative), et compté à la ligne d'état.
function commitLoadoutField(k, el) {
  const su = selUnit();
  if (!su) return;
  const lim = loLimit(su.u.type, k), q = clampNum(el.value, 0, lim, k !== 'fuel');
  const v = q.v === null ? String(lim) : q.v;
  if (q.v !== null) UI.clamped += q.n;
  loSetting(k, v);
  el.value = v;
  if (k === 'fuel') paintFuelBar(fuelPct(v, lim), true);
  refreshAll();
}
// Le type d'une unité change : ses radios et son emport ne valent plus (ils suivent le type) ; la livrée choisie reste si le nouveau type l'a, sinon l'unité reprend sa livrée par défaut. S'il y en a à perdre, une confirmation ; refusée, la liste revient à l'ancien type.
async function changeUnitType(f, fi, ui, el) {
  const u = f.units[ui], nt = el.value;
  if (!u || nt === u.type || PAYLOAD_TYPES.indexOf(nt) < 0) return;
  if ((radioCount(f, u) > 0 || !!u.loadout) && !await askConfirm({ title: tf('u.type.confirm.title', unitLabel(f, fi, u, ui)), text: t('u.type.confirm.text'), verb: t('ui.verb.change'), danger: true })) { el.value = u.type; return; }
  if (u.type === nt || f.units[ui] !== u) return;
  u.type = nt; u.radios = {}; u.loadout = null; REFUSED.delete(u);
  const lv = u.livery.trim().toLowerCase();
  if (!liveriesFor(nt).some(n => n.toLowerCase() === lv)) u.livery = '';       // une livrée choisie que le nouveau type n'a pas (à la casse et aux espaces de bout près) s'efface : l'unité reprend son défaut
  Object.assign(UI.cmp, { saving: false, err: '', st: null });
  renderAll();
}
function onChange(e) {
  const el = e.target, k = el.getAttribute && el.getAttribute('data-k');
  if (el.id === 'cmp-from') { cmpBase(el.value); return; }
  if (el.id === 'cmp-sym') { UI.cmp.sym = el.checked; cmpUpdate(); return; }
  if (el.classList && el.classList.contains('cmp-sel')) { cmpChoose(el.getAttribute('data-st'), el.value); return; }
  if (!k) return;
  if (k === 'fuel-bar') return;
  if (LO_FIELDS.indexOf(k) >= 0) { commitLoadoutField(k, el); return; }
  const fe = el.closest('.fc-flight'), f = fe && S.flights[Number(fe.getAttribute('data-f'))];
  if (k === 'utype') changeUnitType(f, Number(fe.getAttribute('data-f')), Number(el.getAttribute('data-u')), el);
  else if (k === 'livery') { const u = f.units[Number(el.getAttribute('data-u'))]; if (u) { const ui = Number(el.getAttribute('data-u')); u.livery = el.value; fillLiverySelect(el, f, Number(fe.getAttribute('data-f')), u, ui); refreshAll(); } }
  else if (k === 'coalition') { f.coalition = el.value; if (S.flights.indexOf(f) === S.sel.f) renderRouteBlock(); refreshLiveryLists(fe); refreshAll(); }
}
function onToggle(e) {
  const d = e.target, key = d && d.getAttribute && d.tagName === 'DETAILS' ? d.getAttribute('data-key') : null;
  if (!key) return;
  if (d.open) UI.open.add(key); else UI.open.delete(key);
  const h = d.querySelector(':scope > summary');
  if (h) h.setAttribute('aria-expanded', String(d.open));
}
function onFocusIn(e) {
  const ue = e.target.closest ? e.target.closest('.fc-unit') : null;
  if (ue && !(e.target.matches && e.target.matches('[data-act="rm-unit"], [data-act="fold-unit"]'))) selectUnit(Number(ue.closest('.fc-flight').getAttribute('data-f')), Number(ue.getAttribute('data-u')));
}

// ----- Barre, langue, thème -----
function loadTheme() {
  const saved = lsGet(KEY_THEME) || 'cw-nato';
  document.body.setAttribute('data-theme', saved);
  document.getElementById('theme-select').value = saved;
}
function loadLang() {
  const saved = lsGet(KEY_LANG);
  CURRENT_LANG = (saved === 'fr' || saved === 'en') ? saved : ((navigator.language || 'fr').startsWith('fr') ? 'fr' : 'en');
  document.documentElement.lang = CURRENT_LANG;
}
/* Drapeaux dessinés (ils ne s'affichent pas en lettres sous Windows) ; le bouton montre la langue vers laquelle il bascule */
const FLAG_FR = '<svg viewBox="0 0 20 14" width="22" height="15" xmlns="http://www.w3.org/2000/svg"><rect width="7" height="14" fill="#002395"/><rect x="7" width="6" height="14" fill="#fff"/><rect x="13" width="7" height="14" fill="#ED2939"/></svg>';
const FLAG_EN = '<svg viewBox="0 0 20 14" width="22" height="15" xmlns="http://www.w3.org/2000/svg"><rect width="20" height="14" fill="#012169"/><path d="M0,0 L20,14 M20,0 L0,14" stroke="#fff" stroke-width="2.8"/><path d="M0,0 L20,14 M20,0 L0,14" stroke="#C8102E" stroke-width="1.6"/><rect x="8" width="4" height="14" fill="#fff"/><rect y="5" width="20" height="4" fill="#fff"/><rect x="9" width="2" height="14" fill="#C8102E"/><rect y="6" width="20" height="2" fill="#C8102E"/></svg>';
function applyI18nStatic() {
  thFill();
  document.querySelectorAll('[data-i18n]').forEach(el => { el.textContent = t(el.getAttribute('data-i18n')); });
  document.querySelectorAll('[data-i18n-title]').forEach(el => { el.title = t(el.getAttribute('data-i18n-title')); });
  const lang = document.getElementById('btn-lang');
  lang.innerHTML = CURRENT_LANG === 'fr' ? FLAG_EN : FLAG_FR;
  lang.title = t('toolbar.lang.tooltip');
  lang.setAttribute('aria-label', t('toolbar.lang.tooltip'));
  ['open', 'save', 'export', 'example', 'clear'].forEach(k => document.getElementById('btn-' + k).setAttribute('aria-label', t(k === 'open' ? 'tb.open.tip' : 'tb.' + k)));
}
/* La langue : le drapeau la change ; le shell l'appelle aussi (un module déjà chargé suit la langue de la suite) */
function setLang(lang) {
  if (lang !== 'fr' && lang !== 'en') return;
  CURRENT_LANG = lang;
  lsSet(KEY_LANG, CURRENT_LANG);
  document.documentElement.lang = CURRENT_LANG;
  if (impIsOpen()) impRender();
  renderAll();
}
function bindColumns() {
  const left = document.getElementById('col-left'), right = document.getElementById('col-right');
  [left, right].forEach(root => {
    root.addEventListener('click', onClick);
    root.addEventListener('input', onInput);
    root.addEventListener('change', onChange);
    root.addEventListener('toggle', onToggle, true);
  });
  document.getElementById('fc-tc').addEventListener('click', e => {
    const b = e.target.closest ? e.target.closest('[data-act]') : null, a = b ? b.getAttribute('data-act') : '';
    if (a === 'tc-back') tcBack(); else if (a === 'tc-keep') tcKeep();
  });
  left.addEventListener('focusin', onFocusIn);
  right.addEventListener('click', e => {      // une case du dessin désigne sa station
    const cell = e.target.closest ? e.target.closest('.cmp-st') : null;
    if (cell) { UI.cmp.st = cell.getAttribute('data-st'); cmpUpdate(); }
  });
  right.addEventListener('focusin', e => {
    const row = e.target.closest ? e.target.closest('.cmp-row') : null;
    if (row && UI.cmp.st !== row.getAttribute('data-st')) { UI.cmp.st = row.getAttribute('data-st'); cmpUpdate(); }
  });
}
/* « Ouvrir ▾ » : une configuration (le sélecteur de fichier de l'ancien « Ouvrir »), des groupes à importer (la fenêtre de l'ancien « Importer ») */
function fcOpenMenu(btn) {
  mnOpen(btn, 'op-panel', t('tb.open'), {
    items: [
      { k: 'file', label: t('op.file'), hint: t('op.file.h'), title: t('op.file.tip') },
      { k: 'import', label: t('op.import'), hint: t('op.import.h'), title: t('op.import.tip') }
    ],
    choose: k => {
      if (k === 'file') document.getElementById('fc-in-open').click();
      else impOpen({ opener: btn });
    }
  });
}

function bindToolbar() {
  const on = (id, ev, fn) => document.getElementById(id).addEventListener(ev, fn);
  on('theme-select', 'change', e => { document.body.setAttribute('data-theme', e.target.value); lsSet(KEY_THEME, e.target.value); });
  on('theatre', 'change', e => thSet(e.target.value));
  on('btn-lang', 'click', () => setLang(CURRENT_LANG === 'fr' ? 'en' : 'fr'));
  mnBind();       // « Ouvrir ▾ » : une configuration ou des groupes à importer
  on('btn-save', 'click', saveFile);
  on('btn-export', 'click', exportFile);
  on('btn-example', 'click', loadExample);
  on('btn-clear', 'click', clearAll);
  const fileIn = (id, fn) => on(id, 'change', e => { const files = Array.prototype.slice.call(e.target.files); e.target.value = ''; fn(files); });
  fileIn('fc-in-lua', loadLuaFiles);
  fileIn('fc-in-open', files => { if (files[0]) openFile(files[0]); });
  /* Ctrl+S (Cmd+S) : le geste du bouton « Sauvegarder », sauf fenêtre ou menu ouvert */
  document.addEventListener('keydown', e => {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 's') {
      e.preventDefault();
      if (!uiModalsOpen().length && !MN.cur && !TBM.cur) document.getElementById('btn-save').click();
    }
  });
}
function init() {
  loadTheme();
  loadLang();
  let saved = null, adoptFailed = false;
  try { saved = JSON.parse(lsGet(KEY_STATE) || 'null'); } catch (e) { saved = null; }
  const ok = isObj(saved) && (saved.v === 1 || saved.v === 2);
  const sel0 = ok ? (saved.v === 2 ? saved.sel : (isObj(saved.state) ? saved.state.sel : undefined)) : undefined;
  try {
    if (ok) mergeMine(saved.mine);
    if (ok && saved.gsMigrateFailed === true) GS.mf = true;
    const had = gsRead() !== null;       // la fiche existait avant ce chargement (sinon la migration vient de la bâtir avec les groupes de l'état d'avant)
    gsMigrate(gsPackFn);       // la fiche naît ici si le Route Planner ne l'a pas fait avant : les groupes de l'état d'avant, puis les routes liées par nom
    const gs = gsRead();
    if (gs && had && ok && saved.v === 1 && isObj(saved.state)) {
      // l'état d'avant porte encore ses groupes : la fiche n'est adoptée qu'avec eux
      restoreState(saved.state);
      GS.base = {}; S.flights.forEach(f => { GS.base[f.fcId] = gsStable(f); });
      GS.live = false;
      adoptFailed = !gsAdopt(true);
    } else if (gs) restoreState({ theatre: gs.theatre, flights: gs.flights, sel: sel0 });
    else if (ok && saved.v === 1) { restoreState(saved.state); GS.base = {}; S.flights.forEach(f => { GS.base[f.fcId] = gsStable(f); }); }       // le stockage a refusé la fiche : l'état d'avant, tel qu'il est
    if (ok) remapPresetKeys(saved.mine);
  } catch (e) { /* l'écran marche sans */ }
  if (gsRead() !== null && !adoptFailed) { gsMarkAll(); if (gsMarkRaw()) gsFixRaw(); } else { GS.seen = {}; GS.theatre = ''; GS.live = false; if (gsRead() === null) GS.mf = true; }       // sans fiche (stockage plein), les groupes restent dans fc_state_v1 jusqu'à ce qu'elle puisse être écrite
  S.theatre = thInitial();       // toujours un théâtre : la clé partagée, la fiche, la route enregistrée, le Caucase
  UDIST = udRead();
  thFill();
  tcAdopt();
  initToolbarMenus([['theme-select', () => t('toolbar.theme.tooltip')], ['theatre', () => t('tb.theatre'), undefined, true]]);       // la liste du théâtre : le bouton prend la largeur de l'option choisie, comme au Datacard Generator
  initFormMenus(sel => sel.getAttribute('aria-label') || '');
  bindColumns();
  bindToolbar();
  impSetup({ lang: () => CURRENT_LANG, before: fcImportBefore, onImported: fcImported, toast: msg => showToast('\u26a0 ' + msg, { type: 'err' }), loadoutFrom: loadoutFromPayload });       // la fenêtre d'import du bloc commun
  fnBind();                 // la fenêtre « Nom du fichier »
  const taken = routeSync();      // à l'ouverture : les routes liées reprennent ce que le Route Planner a changé depuis
  if (taken.changed) writeState();
  renderAll();
  if (taken.changed) showToast(taken.toast, 4500);
  window.addEventListener('pagehide', flushWork);
  window.addEventListener('storage', e => {
    if (e.key === KEY_WING || e.key === null) WL.stale = true;       // les sources de livrée ne se relisent qu'après un évènement de leur clé (ou de clé null), avant de refaire les listes
    if (e.key === KEY_HQ_MISSION || e.key === null) MS.stale = true;
    routeStorage(e); gsStorage(e); if (e.key === KEY_THEATRE) thFollow(); if (e.key === KEY_UNITS) udFollow();
    if (e.key === KEY_WING || e.key === KEY_HQ_MISSION || e.key === null) { refreshLiveryLists(); refreshSummaries(); }
  });
  document.addEventListener('visibilitychange', () => { if (document.visibilityState === 'hidden') flushWork(); else { gsPull(); routeTakeover(); } });
}
init();
"""

FONTS = """
@font-face { font-family: 'Roboto Mono'; font-weight: 400; font-display: swap; src: url('data:font/woff2;base64,@@ROBOTO_MONO_400@@') format('woff2'); }
@font-face { font-family: 'Stardos Stencil'; font-weight: 400; font-display: swap; src: url('data:font/woff2;base64,@@STARDOS_400@@') format('woff2'); }
@font-face { font-family: 'Stardos Stencil'; font-weight: 700; font-display: swap; src: url('data:font/woff2;base64,@@STARDOS_700@@') format('woff2'); }
@font-face { font-family: 'Oswald'; font-weight: 500; font-display: swap; src: url('data:font/woff2;base64,@@OSWALD_500@@') format('woff2'); }
@font-face { font-family: 'Oswald'; font-weight: 700; font-display: swap; src: url('data:font/woff2;base64,@@OSWALD_700@@') format('woff2'); }
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


def app_js():
    """Le script du module : les textes (JSON) sont posés dans JS_APP."""
    return JS_APP.replace('@@I18N@@', json.dumps({'fr': I18N_FR, 'en': I18N_EN}, ensure_ascii=False, indent=1))


def build_html():
    fonts = (FONTS.replace('@@ROBOTO_MONO_400@@', A['ROBOTO_MONO_400'])
                  .replace('@@STARDOS_400@@', A['STARDOS_400'])
                  .replace('@@STARDOS_700@@', A['STARDOS_700'])
                  .replace('@@OSWALD_500@@', A['OSWALD_500'])
                  .replace('@@OSWALD_700@@', A['OSWALD_700']))
    js = (build_radio_block() + '\n' + build_radio_bands_block() + '\n' + tables_js() + '\n' + build_payload_block() + '\n' + PAD2_JS + '\n' + COORD_BLOCK + READNUM_BLOCK + build_magvar_block() + '\n' + build_projection_block() + '\n'
          + build_route_pack_block() + '\n' + build_route_theatre_block() + '\n' + build_group_store_block() + '\n' + build_import_block() + '\n' + build_messages_block() + '\n' + build_ui_block() + '\n' + JS_TBM + '\n' + app_js())
    return ('<!DOCTYPE html>\n<html lang="fr">\n<head>\n<meta charset="UTF-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0, viewport-fit=cover">\n'
            '<meta name="theme-color" content="#1a1e10">\n<title>Flight Configurator — Mission Plan</title>\n<style>\n'
            + fonts + CSS_COMMON + CSS_FC + build_messages_css() + build_ui_css() + build_import_css() + CONTRAST_CSS + '\n</style>\n'
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


# Familles de textes choisies par programme : « lo.* », « tb.* », « theme.* », « err.code.* », « th.* » (les théâtres)
DYNAMIC_KEY_PREFIXES = ('lo.', 'tb.', 'theme.', 'err.code.', 'th.')


def check(html):
    """Vérifications du build : parité FR/EN, textes utilisés et sans reste, tables égales à leurs fichiers, syntaxe des scripts, aucune requête réseau, graisses."""
    bad = 0

    def ok(cond, label):
        nonlocal bad
        print('  [%s] %s' % ('OK' if cond else 'ÉCHEC', label))
        if not cond:
            bad += 1

    ok(set(I18N_FR) == set(I18N_EN), 'parité FR/EN : %d clés, écart %s' % (len(I18N_FR), sorted(set(I18N_FR) ^ set(I18N_EN))))
    code = JS_APP + BODY + build_ui_block()      # les textes du bloc commun (ui.*) comptent comme utilisés
    used = set(re.findall(r"\bt(?:f)?\('([a-zA-Z0-9_.\-]+)'", code)) | set(re.findall(r'data-i18n(?:-title)?="([^"]+)"', code))
    used |= set(re.findall(r"key: '([a-z]+\.[a-zA-Z0-9_.]+)'", code))
    prefixed = lambda k: k.startswith(DYNAMIC_KEY_PREFIXES)
    ok({k for k in used if not prefixed(k)} <= set(I18N_FR), 'toute clé de texte utilisée existe : manque %s' % sorted(k for k in used - set(I18N_FR) if not prefixed(k)))
    quoted = lambda k: ("'%s'" % k) in code or ('"%s"' % k) in code
    ok(all(quoted(k) or prefixed(k) for k in I18N_FR), 'aucun texte sans usage : reste %s' % sorted(k for k in I18N_FR if not quoted(k) and not prefixed(k)))
    ok(all(any(k in I18N_FR for k in ['tb.%s%s' % (a, s)]) for a in ('open', 'save', 'export', 'example', 'clear') for s in ('', '.tip')), 'textes de la barre présents')
    # les quatre tables : la copie de la page égale le fichier de data/
    for name, fn in TABLES:
        mm = re.search(r'/\* %s:BEGIN \*/\nconst %s = (.*);\n/\* %s:END \*/' % (name, name, name), html, re.S)
        with open(os.path.join(HERE, 'data', fn), encoding='utf-8', newline='') as f:
            txt = f.read().rstrip('\n')
        ok(bool(mm) and mm.group(1) == txt, 'table %s égale à data/%s' % (name, fn))
    # les livrées par défaut : exactement les types du FC, chaque type avec des noms de texte, sans doublon à la casse près
    with open(os.path.join(HERE, 'data', 'liveries_default.json'), encoding='utf-8') as f:
        liv = json.load(f)
    ptm = re.search(r"const PAYLOAD_TYPES = \[(.*?)\];", html)
    ptypes = re.findall(r"'([^']+)'", ptm.group(1)) if ptm else []
    ok(bool(ptypes) and sorted(liv) == sorted(ptypes), 'livrées par défaut : exactement les types de PAYLOAD_TYPES (%s)' % ', '.join('%s %d' % (k, len(v)) for k, v in sorted(liv.items())))
    ok(all(isinstance(v, list) and v and all(isinstance(n, str) and n.strip() == n and n for n in v) and len({n.lower() for n in v}) == len(v) for v in liv.values()), 'livrées par défaut : des noms non vides, sans espace de bout ni doublon à la casse près')
    ok('input[data-k="livery"]' not in html and 'data-k="livery" role="combobox"' not in html, 'le champ Livrée est une liste, plus un texte libre')
    ok(not re.search(r'\blvOpen\b|\blvItems\b|\blvChoose\b|\blvClose\b|\bisLiveryField\b|\bnoteLiveries\s*:|\bseenLiv\b|u\.livery\.ph', html), 'plus de panneau de suggestions de livrée ni de suggestions tirées des paquets, de la mission d\'HQ ou des autres unités')
    ok('n.toLowerCase() === cur.toLowerCase()' in html and 'names[k] = cur' in html, 'une livrée égale à un nom de la liste à la casse près prend la place de ce nom (un seul nom, son écriture à elle)')
    ok(not re.search(r'\bhqMission\b|\breadHqMission\b|\bHQ_MISSION_SCHEMAS\b|\bUI\.hq\b', html), 'plus de lecteur de la mission d\'HQ sous ses anciens noms (hqMission, readHqMission, UI.hq)')
    fns = re.findall(r'^function (\w+)\(', JS_APP, re.M)
    def fn_body(name):
        mm = re.search(r'^function %s\(.*?^}' % name, JS_APP, re.S | re.M)
        return mm.group(0) if mm else ''
    ok(JS_APP.count('lsGet(KEY_HQ_MISSION)') == 1 and 'lsGet(KEY_HQ_MISSION)' in fn_body('missionFlights'), 'la mission d\'HQ n\'est lue que par missionFlights (le bloc d\'import commun lit la sienne pour l\'import)')
    ok(len(re.findall(r'\bmissionFlights\(', JS_APP)) == 2 and 'missionFlights()' in fn_body('missionLivery'), 'missionFlights n\'est appelée que par missionLivery, que liveryAuto seule appelle : ' + ', '.join(f for f in fns if 'missionLivery(' in fn_body(f)))
    ok([f for f in fns if 'missionLivery(' in fn_body(f) and f != 'missionLivery'] == ['liveryAuto'], 'missionLivery n\'est appelée que par liveryAuto')
    ok("if (!liveriesFor(nt).some(n => n.toLowerCase() === lv)) u.livery = '';" in html, "changer le type d'une unité efface sa livrée choisie si le nouveau type ne l'a pas (l'unité reprend alors son défaut)")
    ok('data-k="livery" data-repick' in html and html.count('data-repick') == 3 and "if (!changed && !sel.hasAttribute('data-repick')) return;" in JS_TBM, 'seul le champ Livrée porte data-repick, et tbmChoose du module re-lance input puis change pour lui seul')
    ok('raw ===' not in fn_body('wingRead') + fn_body('missionFlights') and 'if (!WL.stale) return WL;' in fn_body('wingRead') and 'if (!MS.stale) return MS.flights;' in fn_body('missionFlights'), 'wingRead et missionFlights ne relisent leur clé qu\'une fois marquées à relire (plus de comparaison de la chaîne entière)')
    ok(JS_APP.index('WL.stale = true') < JS_APP.index('refreshLiveryLists(); refreshSummaries();') and 'MS.stale = true' in JS_APP and JS_APP.count('WL.stale = true') == 1 and JS_APP.count('MS.stale = true') == 1, 'l\'écouteur storage marque les sources à relire (clé ou clé null) avant de refaire les listes')
    ok(JS_APP.index('WL.stale = true') < JS_APP.index('routeStorage(e); gsStorage(e);') and JS_APP.index('MS.stale = true') < JS_APP.index('routeStorage(e); gsStorage(e);'), 'l\'écouteur storage marque les sources à relire avant tout autre suivi (route, fiche, théâtre, unités)')
    lo = fn_body('liveryOptions')
    ok("u.livery.keep" in lo and lo.count("t('u.livery.keep')") == 1 and re.search(r"else opts\.push\(\{ v: '', l: t\('u\.livery\.keep'\) \}\)", lo) is not None, "« Inchangée » n'est plus en tête : seul le repli d'une liste vide sans valeur la garde")
    ok("const v = liveryValue(u); return v !== '' ? v : liveryAuto(f, fi, u, ui);" in html, 'liveryShown : le choix de l\'utilisateur, sinon liveryAuto')
    ok("liveryId: liveryShown(f, fi, u, ui) || null" in html and 'liveryId: u.livery' not in html, 'l\'export écrit le nom affiché')
    ok(all(not re.search(r'\bu\.livery(?![.\w])', fn_body(n)) for n in ('flightSummary', 'unitSummary', 'buildPackage', 'liveryOptions', 'liveryAuto', 'missionLivery')), 'les résumés, l\'export et les options ne lisent pas u.livery : ils lisent liveryShown')
    ok(all(k in html for k in ("e.key === KEY_WING || e.key === KEY_HQ_MISSION || e.key === null", "refreshLiveryLists(fe)")), 'les listes de livrées suivent wing_config_v1, la mission d\'HQ, et un nom ou une coalition changés')
    ok("const KEY_WING = 'wing_config_v1';" in html and 'refreshLiveryLists' in html, 'les listes de livrées lisent wing_config_v1 et suivent son changement')
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
    for label, blk in (('bandes et postes non pré-réglés', build_radio_bands_block()), ('déclinaison', build_magvar_block()), ('projections', build_projection_block()), ('points de paquet', build_route_pack_block()), ('théâtre d\'une route', build_route_theatre_block()), ('groupes partagés', build_group_store_block()),
                       ('import commun (script)', build_import_block()), ('import commun (feuille)', build_import_css()), ('import commun (fenêtre)', build_import_html()),
                       ('messages communs (script)', build_messages_block()), ('messages communs (feuille)', build_messages_css()),
                       ('interface commune (script)', build_ui_block()), ('interface commune (feuille)', build_ui_css())):
        ok(blk in html, 'bloc %s inséré tel quel' % label)
    ok(True, "empreinte du bloc d'interface commun : %s" % ui_fingerprint())
    pt, it = re.search(r"const PAYLOAD_TYPES = \[(.*?)\];", build_payload_block()), re.search(r"const IMP_TYPES = \[(.*?)\];", build_import_block())
    ok(bool(pt) and bool(it) and pt.group(1) == it.group(1), 'les types du bloc d\'import sont ceux de PAYLOAD_TYPES')
    ok(COORD_BLOCK + READNUM_BLOCK in html and hashlib.sha256(COORD_BLOCK.encode('utf-8')).hexdigest()[:16] == COORD_SHA16, 'bloc de coordonnées inséré tel quel, empreinte %s' % COORD_SHA16)
    if bad:
        sys.exit(1)


if __name__ == '__main__':
    main()
