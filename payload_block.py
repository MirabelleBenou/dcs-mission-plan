#!/usr/bin/env python3
"""Bloc « EMPORT » — lecture et écriture des presets d'emport de l'éditeur de DCS (UnitPayloads\\<type>.lua), catalogue des
armes par pylône, et construction du `payload` d'un .miz. Une seule source pour le Flight Configurator et, plus tard, le
Loadout Editor de Mission Tools.

Rend le texte JavaScript du bloc. Aucune dépendance au reste de la page : ni DOM, ni t(), ni réseau ; le bloc s'exécute seul
sous node. Le catalogue (weapons_catalogue.json, produit une fois par generer_catalogue_armes.py d'après pydcs, LGPL-3.0) y est recopié.

Les modules qui l'utilisent insèrent ce texte tel quel : le bloc est identique à l'octet dans chaque fichier de dist/.

Usage (par les builds) : from payload_block import build_block ; texte = build_block()
"""

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
BLOCK_BEGIN = '/* ===== EMPORT (PRESETS ET PAYLOAD) ===== */'
BLOCK_END = '/* ===== FIN DE L\'EMPORT ===== */'

_JS = r"""
// Catalogue des armes (pydcs) : { source, weapons: { CLSID: nom }, types: { type: { fuelMax, flare, chaff, gun, task, pylons: { n: [CLSID…] } } } }
const PAYLOAD_CATALOGUE = @@CATALOGUE@@;

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

// Nom du type dans l'en-tête d'un fichier UnitPayloads (clé « name »), quand aucun fichier chargé ne le donne.
const PAYLOAD_FILE_NAME = { 'Mi-24P': 'Mi-24P', 'Mi-8MT': 'Mi-8MT', 'F-4E-45MC': 'F-4E-45MC', 'Mirage-F1EE': 'Mirage F1EE' };

// Les fichiers d'hélicoptère (Mi-24P) portent une clé « tasks » vide en tête ; celui d'un avion (A-10C_2) n'en a pas. Un fichier neuf suit cet usage.
const PAYLOAD_TOP_TASKS = { 'Mi-24P': true, 'Mi-8MT': true };

// WEAPONS[type][pylône] = [{ clsid, name }] · FUEL_MAX[type] · LURE_DEFAULTS[type] = { flare, chaff } · TASK_DEFAULT[type]
const WEAPONS = {}, FUEL_MAX = {}, LURE_DEFAULTS = {}, TASK_DEFAULT = {};
PAYLOAD_TYPES.forEach(ty => {
  const c = PAYLOAD_CATALOGUE.types[ty];
  WEAPONS[ty] = {};
  Object.keys(c.pylons).forEach(n => {
    WEAPONS[ty][Number(n)] = c.pylons[n].map(id => ({ clsid: id, name: PAYLOAD_CATALOGUE.weapons[id] }));
  });
  FUEL_MAX[ty] = c.fuelMax;
  LURE_DEFAULTS[ty] = { flare: c.flare, chaff: c.chaff };
  TASK_DEFAULT[ty] = c.task;
});

// Numéros de pylône d'un type, dans l'ordre croissant.
function payloadPylonNumbers(type) {
  return WEAPONS[type] ? Object.keys(WEAPONS[type]).map(Number).sort((a, b) => a - b) : [];
}

// Nom lisible d'une arme sur un pylône ; '' si le CLSID est vide, null s'il n'est pas dans le catalogue de ce pylône.
function payloadWeaponName(type, pylon, clsid) {
  if (clsid === '' || clsid === undefined || clsid === null) return '';
  const list = WEAPONS[type] && WEAPONS[type][pylon];
  if (!list) return null;
  for (let i = 0; i < list.length; i++) if (list[i].clsid === clsid) return list[i].name;
  return null;
}

// Réglages par défaut hors pylônes : carburant maximum, leurres et paillettes du catalogue, canon plein.
function payloadDefaults(type) {
  return { fuel: FUEL_MAX[type], flare: LURE_DEFAULTS[type].flare, chaff: LURE_DEFAULTS[type].chaff, gun: 100 };
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

// Lit un fichier UnitPayloads. Rend { unitType, name, supported, tasks (absent si le fichier n'a pas la clé), presets: [{ name, displayName, pylons: { num: { CLSID, settings? } }, order: [num…], tasks }] }.
// `order` garde l'ordre des pylônes du fichier (un objet JS trie ses clés numériques : sans lui, la réécriture à l'octet serait impossible).
// Les clés que ces fichiers n'ont pas aujourd'hui et que le module ne connaît pas sont gardées dans `extra`, à chaque niveau, et réécrites.
function parseUnitPayloads(text) {
  const root = payloadLuaParse(String(text));
  const top = payloadLuaEntries(root);
  const get = (list, key) => { for (let i = 0; i < list.length; i++) if (list[i].key === key) return list[i]; return null; };
  const need = (list, key, kind, parentLine) => {
    const e = get(list, key);
    if (!e || e.val.k !== kind) throw payloadLuaError(e ? e.line : parentLine, 'bad-structure', key);
    return e;
  };
  const known = (list, names) => {
    const x = {};
    list.forEach(e => { if (names.indexOf(e.key) < 0) x[String(e.key)] = payloadLuaToJs(e.val); });
    return Object.keys(x).length ? x : null;
  };
  const unitType = need(top, 'unitType', 'str', root.line).val.v;
  const nameE = get(top, 'name');
  const out = {
    unitType: unitType,
    name: nameE && nameE.val.k === 'str' ? nameE.val.v : unitType,
    supported: PAYLOAD_TYPES.indexOf(unitType) >= 0,
    presets: []
  };
  const tk = get(top, 'tasks');                       // la clé « tasks » du fichier n'existe pas toujours (le Mi-24P l'a, le A-10C_2 non)
  if (tk && tk.val.k === 'tbl') out.tasks = payloadLuaToJs(tk.val);
  const px = known(top, ['unitType', 'name', 'tasks', 'payloads']);
  if (px) out.extra = px;
  const pay = need(top, 'payloads', 'tbl', root.line);
  payloadLuaEntries(pay.val).forEach(pe => {
    if (pe.val.k !== 'tbl') throw payloadLuaError(pe.line, 'bad-structure', 'payloads');
    const pl = payloadLuaEntries(pe.val);
    const preset = {
      name: need(pl, 'name', 'str', pe.line).val.v,
      displayName: need(pl, 'displayName', 'str', pe.line).val.v,
      pylons: {}, order: [], tasks: []
    };
    const t2 = get(pl, 'tasks');
    if (t2 && t2.val.k === 'tbl') preset.tasks = payloadLuaToJs(t2.val);
    const x2 = known(pl, ['name', 'displayName', 'pylons', 'tasks']);
    if (x2) preset.extra = x2;
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
      const x3 = known(yl, ['CLSID', 'num', 'settings']);
      if (x3) py.extra = x3;
      if (Object.prototype.hasOwnProperty.call(preset.pylons, num)) throw payloadLuaError(ye.line, 'bad-structure', 'num ' + num);
      preset.pylons[num] = py;
      preset.order.push(num);
    });
    out.presets.push(preset);
  });
  return out;
}

// ---------------------------------------------------------------------------------------------------------------
//  ÉCRITURE — au format de l'éditeur : LF, tabulations, clés triées (ordre des fichiers d'exemple), un pylône = { CLSID, num, settings? }.
// ---------------------------------------------------------------------------------------------------------------
function payloadLuaString(s) {
  let out = '';
  for (const ch of String(s)) {
    const c = ch.codePointAt(0);
    if (ch === '\\') out += '\\\\';
    else if (ch === '"') out += '\\"';
    else if (ch === '\n') out += '\\n';
    else if (ch === '\r') out += '\\r';
    else if (c < 32) out += '\\' + String(c).padStart(3, '0');
    else out += ch;
  }
  return '"' + out + '"';
}

// valeur JS → texte Lua ; tableau = [1] = …, objet = ["clé"] = … triées ; table vide = « {\n<tabs>} » comme l'éditeur
function payloadLuaEmit(v, depth) {
  if (typeof v === 'string') return payloadLuaString(v);
  if (typeof v === 'boolean') return v ? 'true' : 'false';
  if (typeof v === 'number') return String(v);
  const tabs = '\t'.repeat(depth), tabs1 = '\t'.repeat(depth + 1);
  let body = '';
  if (Array.isArray(v)) {
    v.forEach((x, i) => { body += tabs1 + '[' + (i + 1) + '] = ' + payloadLuaEmit(x, depth + 1) + ',\n'; });
  } else {
    Object.keys(v).sort().forEach(k => {
      if (v[k] === undefined || v[k] === null) return;
      body += tabs1 + (/^\d+$/.test(k) ? '[' + k + ']' : '["' + payloadLuaString(k).slice(1, -1) + '"]') + ' = ' + payloadLuaEmit(v[k], depth + 1) + ',\n';
    });
  }
  return '{\n' + body + tabs + '}';
}

// Réécrit un objet rendu par parseUnitPayloads (ou construit à la main : { unitType, name?, tasks?, presets: [{ name, displayName?, pylons, order?, tasks? }] }).
function serializeUnitPayloads(obj) {
  const top = Object.assign({}, obj.extra || {});
  top.name = obj.name !== undefined && obj.name !== null ? obj.name : (PAYLOAD_FILE_NAME[obj.unitType] || obj.unitType);
  top.unitType = obj.unitType;
  if (obj.tasks) top.tasks = obj.tasks.slice();
  else if (PAYLOAD_TOP_TASKS[obj.unitType]) top.tasks = [];
  top.payloads = (obj.presets || []).map(pr => {
    const nums = pr.order ? pr.order.filter(n => Object.prototype.hasOwnProperty.call(pr.pylons, n))
                          : Object.keys(pr.pylons).map(Number).sort((a, b) => a - b);
    Object.keys(pr.pylons).map(Number).sort((a, b) => a - b).forEach(n => { if (nums.indexOf(n) < 0) nums.push(n); });
    const e = Object.assign({}, pr.extra || {});
    e.name = pr.name;
    e.displayName = pr.displayName !== undefined && pr.displayName !== null ? pr.displayName : pr.name;
    e.tasks = pr.tasks ? pr.tasks.slice() : [];
    e.pylons = nums.map(n => {
      const py = pr.pylons[n];
      const o = Object.assign({}, py.extra || {});
      o.CLSID = py.CLSID;
      o.num = Number(n);
      if (py.settings !== undefined && py.settings !== null) o.settings = py.settings;
      return o;
    });
    return e;
  });
  return 'local unitPayloads = ' + payloadLuaEmit(top, 0) + '\nreturn unitPayloads\n';
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
    with open(os.path.join(HERE, 'weapons_catalogue.json'), encoding='utf-8') as f:
        cat = json.load(f)
    js_cat = json.dumps(cat, ensure_ascii=True, sort_keys=True, separators=(',', ':'))
    assert '</' not in js_cat
    return BLOCK_BEGIN + _JS.replace('@@CATALOGUE@@', js_cat) + BLOCK_END + '\n'


if __name__ == '__main__':
    txt = build_block()
    print(f"[OK] bloc de l'emport : {len(txt)} caractères")
