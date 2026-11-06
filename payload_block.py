#!/usr/bin/env python3
"""Bloc « EMPORT » — lecture d'un fichier .lua d'exemple (pour en tirer des emports de départ), armes permises par pylône, et
construction du `payload` d'un .miz. Une seule source pour le Flight Configurator et, plus tard, le Loadout Editor de Mission Tools.

Rend le texte JavaScript du bloc. Aucune dépendance au reste de la page : ni DOM, ni t(), ni réseau ; le bloc s'exécute seul
sous node. Les tables d'armes (data/*.json de Mission Tools, d'après pydcs, LGPL-3.0) sont des constantes de la page, lues par le bloc.

Les modules qui l'utilisent insèrent ce texte tel quel : le bloc est identique à l'octet dans chaque fichier de dist/.

Usage (par les builds) : from payload_block import build_block ; texte = build_block()
"""

import os

HERE = os.path.dirname(os.path.abspath(__file__))
BLOCK_BEGIN = '/* ===== EMPORT (PRESETS ET PAYLOAD) ===== */'
BLOCK_END = '/* ===== FIN DE L\'EMPORT ===== */'

_JS = r"""
// Les trois tables de Mission Tools (data/*.json, d'après pydcs 1.0.0, LGPL-3.0) doivent exister avant ce bloc, sous ces noms :
//   WEAPON_NAMES { CLSID: nom } · AIRCRAFT_PYLONS { clsids: [...], weights: [...], types: { type: { pylône: [indices dans clsids] } } }
//   AIRCRAFT_LIMITS { type: { fuel_max, flare, chaff, charge_total, flare_charge_size, chaff_charge_size } }
// Le bloc ne les contient pas : ce sont les mêmes constantes que celles du Loadout Editor, qui peut donc le reprendre tel quel.

// Les quatre types gérés (liste fermée). Tout autre type d'un fichier UnitPayloads se lit mais ne s'offre à aucun vol.
const PAYLOAD_TYPES = ['Mi-24P', 'Mi-8MT', 'F-4E-45MC', 'Mirage-F1EE'];

// Forme du `payload` d'un .miz, par type : clés fixes en plus de chaff, flare, fuel, gun et pylons (mesurées sur des .miz d'exemple).
//   ammo_type : valeur écrite · restricted : table écrite (vide) · fuelAsString : le carburant du .miz est un texte
const PAYLOAD_SHAPE = {
  'Mi-24P':      { ammo_type: 1, restricted: {}, fuelAsString: false },
  'Mi-8MT':      { fuelAsString: true },
  'F-4E-45MC':   { ammo_type: 1 },
  'Mirage-F1EE': {}
};

// Ajouts à la table de pylônes, d'après la mesure des .miz d'exemple : le F-4E porte « <CLEAN> » (dessous d'aile propre) sur ces pylônes,
// valeur que pydcs ne connaît pas. Masse 0.
const PAYLOAD_EXTRA = { 'F-4E-45MC': { clsid: '<CLEAN>', name: '<CLEAN> (clean pylon)', pylons: [2, 3, 4, 10, 11, 12] } };

const payloadHas = (o, k) => Object.prototype.hasOwnProperty.call(o, k);
const payloadIdx = new Map(AIRCRAFT_PYLONS.clsids.map((c, i) => [c, i]));

// Pylônes d'un type : [{ n, allowed: [CLSID…] }] dans l'ordre numérique ; null si la table ne connaît pas le type.
function payloadPylons(type) {
  if (PAYLOAD_TYPES.indexOf(type) < 0 || !payloadHas(AIRCRAFT_PYLONS.types, type)) return null;
  const tp = AIRCRAFT_PYLONS.types[type], ex = PAYLOAD_EXTRA[type];
  return Object.keys(tp).sort((a, b) => Number(a) - Number(b)).map(n => {
    const allowed = tp[n].map(i => AIRCRAFT_PYLONS.clsids[i]);
    if (ex && ex.pylons.indexOf(Number(n)) >= 0) allowed.unshift(ex.clsid);
    return { n: n, allowed: allowed };
  });
}

// Numéros de pylône d'un type, dans l'ordre croissant.
function payloadPylonNumbers(type) {
  const p = payloadPylons(type);
  return p ? p.map(x => Number(x.n)) : [];
}

// Nom lisible d'une arme ; '' si le CLSID est vide, null s'il est inconnu des tables.
function payloadWeaponName(clsid) {
  if (clsid === '' || clsid === undefined || clsid === null) return '';
  if (payloadHas(WEAPON_NAMES, clsid)) return WEAPON_NAMES[clsid];
  for (const ty of Object.keys(PAYLOAD_EXTRA)) if (PAYLOAD_EXTRA[ty].clsid === clsid) return PAYLOAD_EXTRA[ty].name;
  return null;
}

// Masse d'une arme en kg ; null si les tables ne la donnent pas (« <CLEAN> » : 0).
function payloadWeaponMass(clsid) {
  for (const ty of Object.keys(PAYLOAD_EXTRA)) if (PAYLOAD_EXTRA[ty].clsid === clsid) return 0;
  const i = payloadIdx.get(clsid);
  const w = i === undefined ? null : AIRCRAFT_PYLONS.weights[i];
  return (w === null || w === undefined) ? null : w;
}

// Symétrie : le CLSID à poser sur la station jumelle pour le choix `clsid` ; '' s'il n'y a rien à poser. allowedOnTwin : les CLSID permis sur la jumelle.
// Dans l'ordre : le même CLSID, s'il est permis ; sinon celui où Left↔Right (LEFT↔RIGHT, _L↔_R en fin de mot) sont échangés, s'il est permis ;
// sinon l'unique arme permise de même nom (payloadWeaponName) ; sinon ''. Fonction pure : ni DOM, ni t(), ni stockage.
function payloadMirrorClsid(clsid, allowedOnTwin) {
  if (clsid === '' || clsid === undefined || clsid === null) return '';
  const allowed = Array.isArray(allowedOnTwin) ? allowedOnTwin : [];
  if (allowed.indexOf(clsid) >= 0) return clsid;
  const swap = { Left: 'Right', Right: 'Left', LEFT: 'RIGHT', RIGHT: 'LEFT' };
  const swapped = String(clsid).replace(/Left|Right|LEFT|RIGHT/g, m => swap[m]).replace(/_([LR])(?![A-Za-z0-9])/g, (m, c) => '_' + (c === 'L' ? 'R' : 'L'));
  if (swapped !== clsid && allowed.indexOf(swapped) >= 0) return swapped;
  const name = payloadWeaponName(clsid);
  if (name === null || name === '') return '';
  const same = allowed.filter(c => payloadWeaponName(c) === name);
  return same.length === 1 ? same[0] : '';
}

// Réglages par défaut hors pylônes : carburant maximum, leurres et paillettes de AIRCRAFT_LIMITS, canon plein.
function payloadDefaults(type) {
  const l = AIRCRAFT_LIMITS[type];
  return { fuel: l.fuel_max, flare: l.flare, chaff: l.chaff, gun: 100 };
}

// Limites des leurres : flares × flare_charge_size + chaff × chaff_charge_size ≤ charge_total
function payloadLureLimits(type) {
  const l = AIRCRAFT_LIMITS[type];
  return { total: l.charge_total, flareSize: l.flare_charge_size, chaffSize: l.chaff_charge_size };
}

// ---------------------------------------------------------------------------------------------------------------
//  LECTURE — sous-ensemble Lua des fichiers UnitPayloads : tables, chaînes, nombres, booléens, nil, commentaires.
//  Une erreur est une Error avec .line (numéro de ligne, à partir de 1), .code et .detail ; le texte est à traduire par l'appelant.
// ---------------------------------------------------------------------------------------------------------------
function payloadLuaError(line, code, detail) {
  const e = new Error('line ' + line + ': ' + code + (detail ? ' (' + detail + ')' : ''));
  e.line = line; e.code = code; e.detail = detail || '';
  return e;
}

function payloadLuaTokens(src) {
  const toks = [];
  let i = 0, line = 1;
  const n = src.length;
  while (i < n) {
    const c = src[i];
    if (c === '\n') { line++; i++; continue; }
    if (c === ' ' || c === '\t' || c === '\r' || c === '﻿') { i++; continue; }
    if (c === '-' && src[i + 1] === '-') {
      const m = /^--\[(=*)\[/.exec(src.slice(i, i + 40));
      if (m) {
        const close = ']' + m[1] + ']';
        const end = src.indexOf(close, i + m[0].length);
        if (end < 0) throw payloadLuaError(line, 'unterminated-comment');
        for (let k = i; k < end; k++) if (src[k] === '\n') line++;
        i = end + close.length;
      } else {
        while (i < n && src[i] !== '\n') i++;
      }
      continue;
    }
    if ('{}[]=,;'.indexOf(c) >= 0) { toks.push({ t: c, line: line }); i++; continue; }
    if (c === '"' || c === "'") {
      const startLine = line;
      let s = '';
      i++;
      for (;;) {
        if (i >= n || src[i] === '\n') throw payloadLuaError(startLine, 'unterminated-string');
        const d = src[i];
        if (d === c) { i++; break; }
        if (d === '\\') {
          const e = src[i + 1];
          if (e === undefined) throw payloadLuaError(startLine, 'unterminated-string');
          if (e === 'n') { s += '\n'; i += 2; }
          else if (e === 'r') { s += '\r'; i += 2; }
          else if (e === 't') { s += '\t'; i += 2; }
          else if (/[0-9]/.test(e)) {
            let j = i + 1, dg = '';
            while (j < n && dg.length < 3 && /[0-9]/.test(src[j])) { dg += src[j]; j++; }
            s += String.fromCharCode(parseInt(dg, 10)); i = j;
          }
          else if (e === '\n') { s += '\n'; line++; i += 2; }
          else { s += e; i += 2; }
        } else { s += d; i++; }
      }
      toks.push({ t: 'str', v: s, line: startLine });
      continue;
    }
    const num = /^-?(?:0[xX][0-9a-fA-F]+|(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?)/.exec(src.slice(i, i + 64));
    if (num && (c !== '-' || /[0-9.]/.test(src[i + 1] || ''))) {
      toks.push({ t: 'num', v: Number(num[0]), line: line });
      i += num[0].length;
      continue;
    }
    const id = /^[A-Za-z_][A-Za-z_0-9]*/.exec(src.slice(i, i + 64));
    if (id) { toks.push({ t: 'id', v: id[0], line: line }); i += id[0].length; continue; }
    throw payloadLuaError(line, 'unexpected-character', c);
  }
  toks.push({ t: 'eof', line: line });
  return toks;
}

// Arbre : { k: 'tbl', line, entries: [{ key, line, val }] } | { k: 'str'|'num'|'bool'|'nil', v, line } ; key null = entrée positionnelle.
function payloadLuaParse(src) {
  const toks = payloadLuaTokens(src);
  let p = 0;
  const peek = () => toks[p];
  const tokText = tk => tk.t === 'eof' ? 'end of file' : (tk.t === 'str' ? 'string' : (tk.t === 'num' ? 'number' : (tk.t === 'id' ? tk.v : tk.t)));
  const fail = (tk, what) => { throw payloadLuaError(tk.line, tk.t === 'eof' ? 'unexpected-eof' : 'unexpected-token', tk.t === 'eof' ? what : tokText(tk) + ' / ' + what); };
  const expect = (type, what) => { const tk = peek(); if (tk.t !== type) fail(tk, what || type); p++; return tk; };

  function value() {
    const tk = peek();
    if (tk.t === '{') return table();
    if (tk.t === 'str') { p++; return { k: 'str', v: tk.v, line: tk.line }; }
    if (tk.t === 'num') { p++; return { k: 'num', v: tk.v, line: tk.line }; }
    if (tk.t === 'id' && (tk.v === 'true' || tk.v === 'false')) { p++; return { k: 'bool', v: tk.v === 'true', line: tk.line }; }
    if (tk.t === 'id' && tk.v === 'nil') { p++; return { k: 'nil', v: null, line: tk.line }; }
    return fail(tk, 'value');
  }
  function table() {
    const open = expect('{');
    const entries = [];
    for (;;) {
      const tk = peek();
      if (tk.t === '}') { p++; break; }
      let key = null;
      if (tk.t === '[') {
        p++;
        const kt = peek();
        if (kt.t !== 'str' && kt.t !== 'num') fail(kt, 'key');
        p++;
        key = kt.v;
        expect(']', ']');
        expect('=', '=');
      } else if (tk.t === 'id' && toks[p + 1].t === '=' ) {
        key = tk.v; p += 2;
      }
      const v = value();
      entries.push({ key: key, line: tk.line, val: v });
      const sep = peek();
      if (sep.t === ',' || sep.t === ';') { p++; continue; }
      if (sep.t === '}') { p++; break; }
      fail(sep, ', or }');
    }
    return { k: 'tbl', line: open.line, entries: entries };
  }

  let name = null;
  if (peek().t === 'id' && peek().v === 'local') p++;
  const nameTok = expect('id', 'name');
  name = nameTok.v;
  expect('=', '=');
  const root = table();
  if (peek().t === 'id' && peek().v === 'return') {
    p++;
    const rn = expect('id', 'name');
    if (rn.v !== name) throw payloadLuaError(rn.line, 'unexpected-token', rn.v + ' / ' + name);
  }
  expect('eof', 'end of file');
  return root;
}

// Entrées d'une table : clé positionnelle = rang (à partir de 1), comme Lua.
function payloadLuaEntries(tbl) {
  let idx = 0;
  return tbl.entries.map(e => ({ key: e.key === null ? ++idx : e.key, line: e.line, val: e.val }));
}

function payloadLuaToJs(node) {
  if (node.k === 'tbl') {
    const es = payloadLuaEntries(node);
    if (es.every((e, i) => e.key === i + 1)) return es.map(e => payloadLuaToJs(e.val));   // une table vide est un tableau vide
    const o = {};
    es.forEach(e => { o[String(e.key)] = payloadLuaToJs(e.val); });
    return o;
  }
  return node.v;
}

// Lit un fichier .lua d'exemple (un par appareil). Rend { unitType, supported, presets: [{ name, displayName, pylons: { num: { CLSID, settings? } } }] }.
// Seul ce que le module emploie est gardé : le nom, et pour chaque station l'arme et son réglage éventuel.
function parseUnitPayloads(text) {
  const root = payloadLuaParse(String(text));
  const top = payloadLuaEntries(root);
  const get = (list, key) => { for (let i = 0; i < list.length; i++) if (list[i].key === key) return list[i]; return null; };
  const need = (list, key, kind, parentLine) => {
    const e = get(list, key);
    if (!e || e.val.k !== kind) throw payloadLuaError(e ? e.line : parentLine, 'bad-structure', key);
    return e;
  };
  const unitType = need(top, 'unitType', 'str', root.line).val.v;
  const out = { unitType: unitType, supported: PAYLOAD_TYPES.indexOf(unitType) >= 0, presets: [] };
  const pay = need(top, 'payloads', 'tbl', root.line);
  payloadLuaEntries(pay.val).forEach(pe => {
    if (pe.val.k !== 'tbl') throw payloadLuaError(pe.line, 'bad-structure', 'payloads');
    const pl = payloadLuaEntries(pe.val);
    const preset = {
      name: need(pl, 'name', 'str', pe.line).val.v,
      displayName: need(pl, 'displayName', 'str', pe.line).val.v,
      pylons: {}
    };
    payloadLuaEntries(need(pl, 'pylons', 'tbl', pe.line).val).forEach(ye => {
      if (ye.val.k !== 'tbl') throw payloadLuaError(ye.line, 'bad-structure', 'pylons');
      const yl = payloadLuaEntries(ye.val);
      const num = need(yl, 'num', 'num', ye.line).val.v;
      const py = { CLSID: need(yl, 'CLSID', 'str', ye.line).val.v };
      const st = get(yl, 'settings');
      if (st) {
        if (st.val.k !== 'tbl') throw payloadLuaError(st.line, 'bad-structure', 'settings');
        py.settings = payloadLuaToJs(st.val);
      }
      if (Object.prototype.hasOwnProperty.call(preset.pylons, num)) throw payloadLuaError(ye.line, 'bad-structure', 'num ' + num);
      preset.pylons[num] = py;
    });
    out.presets.push(preset);
  });
  return out;
}

// ---------------------------------------------------------------------------------------------------------------
//  LE `payload` D'UN .MIZ
// ---------------------------------------------------------------------------------------------------------------
function payloadClamp(v, lo, hi) {
  v = Number(v);
  if (!isFinite(v)) return lo;
  return Math.min(hi, Math.max(lo, v));
}

// pylons : { numéro: { CLSID, settings? } } (un CLSID vide ou absent = pylône vide, non écrit) · opts : { fuel, flare, chaff, gun } (défauts du catalogue)
// Rend l'objet `payload` du .miz : chaff, flare, fuel, gun, pylons, plus les clés fixes du type (PAYLOAD_SHAPE).
function buildPayload(type, pylons, opts) {
  if (PAYLOAD_TYPES.indexOf(type) < 0) throw new Error('unsupported type: ' + type);
  const d = payloadDefaults(type), o = opts || {};
  const shape = PAYLOAD_SHAPE[type];
  const fuel = payloadClamp(o.fuel === undefined || o.fuel === null || o.fuel === '' ? d.fuel : o.fuel, 0, d.fuel);
  const p = {};
  if (Object.prototype.hasOwnProperty.call(shape, 'ammo_type')) p.ammo_type = shape.ammo_type;
  p.chaff = Math.round(payloadClamp(o.chaff === undefined || o.chaff === null || o.chaff === '' ? d.chaff : o.chaff, 0, d.chaff));
  p.flare = Math.round(payloadClamp(o.flare === undefined || o.flare === null || o.flare === '' ? d.flare : o.flare, 0, d.flare));
  p.fuel = shape.fuelAsString ? String(fuel) : fuel;
  p.gun = Math.round(payloadClamp(o.gun === undefined || o.gun === null || o.gun === '' ? d.gun : o.gun, 0, 100));
  p.pylons = {};
  Object.keys(pylons || {}).map(Number).sort((a, b) => a - b).forEach(n => {
    const py = pylons[n];
    if (!py || py.CLSID === '' || py.CLSID === undefined || py.CLSID === null) return;
    const e = { CLSID: py.CLSID };
    if (py.settings !== undefined && py.settings !== null) e.settings = JSON.parse(JSON.stringify(py.settings));
    p.pylons[n] = e;
  });
  if (Object.prototype.hasOwnProperty.call(shape, 'restricted')) p.restricted = JSON.parse(JSON.stringify(shape.restricted));
  return p;
}
"""


def build_block():
    """Le texte du bloc, délimité par ses deux commentaires, avec un saut de ligne final."""
    return BLOCK_BEGIN + _JS + BLOCK_END + '\n'


if __name__ == '__main__':
    txt = build_block()
    print(f"[OK] bloc de l'emport : {len(txt)} caractères")
