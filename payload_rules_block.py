#!/usr/bin/env python3
"""Bloc « RÈGLES D'EMPORT » — les portes d'un appareil (le Kord du Mi-24P), les incompatibilités entre stations (règles écrites et règles du jeu), les exigences et le plafond de leurres et de paillettes.

Recopié au caractère du Loadout Editor de Mission Tools (dépôt public `dcs-mission-tools`, `modules/dcs_loadout_editor.html`) : de « // Stations dont une seule peut porter une arme à la fois » jusqu'à la fin de `payloadRuleMissing`,
sans la copie en ligne de `PAYLOAD_GAME_RULES` (ici une table injectée par le build, comme les autres), puis `chargeLimit`. Un même emport doit donner le même résultat dans les deux outils : une règle partagée ne se réécrit pas.
Seul le Flight Configurator reçoit ce bloc : le Datacard Generator n'en a pas besoin.

Fonctions pures : ni DOM, ni t(), ni stockage ; le bloc s'exécute seul sous node. Il lit les constantes AIRCRAFT_PYLONS et PAYLOAD_GAME_RULES (tables de data/, posées avant lui) et payloadHas (bloc de l'emport).

Usage (par le build) : from payload_rules_block import build_block, NAMES ; texte = build_block()
"""

import os

HERE = os.path.dirname(os.path.abspath(__file__))
BLOCK_BEGIN = '/* ===== RÈGLES D\'EMPORT (PORTES, INCOMPATIBILITÉS, EXIGENCES, LEURRES) ===== */'
BLOCK_END = '/* ===== FIN DES RÈGLES D\'EMPORT ===== */'

# Les dix déclarations recopiées du Loadout Editor : le build du Flight Configurator s'arrête si l'une manque.
NAMES = ['PAYLOAD_ONE_OF', 'payloadOneOfOthers', 'PAYLOAD_RULES', 'payloadGameCache', 'payloadClsidMap', 'payloadClsidIdx',
         'payloadGameIndex', 'payloadRuleConflicts', 'payloadRuleMissing', 'chargeLimit']

_JS = r"""
// Règles d'emport du Loadout Editor de Mission Tools (dépôt dcs-mission-tools, modules/dcs_loadout_editor.html) : le texte des déclarations ci-dessous est celui du Loadout Editor, au caractère
// (garde : un même emport doit donner le même résultat dans les deux outils). Les fonctions sont pures : ni DOM, ni t(), ni stockage.
// Le bloc lit ces constantes, qui doivent exister avant lui : AIRCRAFT_PYLONS (table de pylônes), PAYLOAD_GAME_RULES (data/loadout_rules.json, injectée par le build), et payloadHas (bloc de l'emport).
// Il porte : PAYLOAD_ONE_OF, payloadOneOfOthers (les portes), PAYLOAD_RULES (règles écrites), payloadGameCache, payloadClsidMap, payloadClsidIdx, payloadGameIndex, payloadRuleConflicts, payloadRuleMissing
// (règles du jeu, exclusions et exigences) et chargeLimit (le plafond de leurres et de paillettes).

// Stations dont une seule peut porter une arme à la fois : le Kord du Mi-24P, une porte (décision du 7 novembre).
const PAYLOAD_ONE_OF = { 'Mi-24P': [['7', '8']] };
// Les autres stations du groupe de `n` pour `type` ([] si aucun). Fonction pure : ni DOM, ni t(), ni stockage.
function payloadOneOfOthers(type, n) {
  if (!Object.prototype.hasOwnProperty.call(PAYLOAD_ONE_OF, type)) return [];
  const out = [];
  PAYLOAD_ONE_OF[type].forEach(g => { if (g.indexOf(String(n)) >= 0) g.forEach(m => { if (m !== String(n) && out.indexOf(m) < 0) out.push(m); }); });
  return out;
}

// Incompatibilités d'emport par appareil, d'après les manuels officiels et les guides de la communauté (table du 9 novembre 2026 ; le Mirage F1 en est retiré le 10 novembre : la règle du jeu dit la même chose).
// Trois formes : « mix » (fam : CLSID → famille d'armes ; ok : paires de familles permises, toute autre paire de familles différentes est un conflit)
// « excl » (g : groupes { st, w } ; un CLSID de w posé sur une station de st est incompatible avec un CLSID d'un autre groupe posé sur une station de ce groupe-là)
// et « rack » (le Mi-24P : st station → rack, fam CLSID → famille, sym / asym les paires de familles interdites de chaque matrice, bombs la règle des cases bleues ; matrices du DCS Mi-24P Hind Guide, p. 303–304).
const PAYLOAD_RULES = {
 "AJS37": [
  {
   "id": "ajs37-mix",
   "k": "mix",
   "fam": {
    "{BK90}": "BK90",
    "{BK90MJ1}": "BK90",
    "{BK90MJ2}": "BK90",
    "{AKAN}": "AKAN",
    "{AKAN_NO_TRC}": "AKAN",
    "{ARAKM70BHE}": "ARAK",
    "{ARAKM70BAP}": "ARAK",
    "{ARAKM70BAPPX}": "ARAK",
    "{Rb04_HB}": "RB04",
    "{Rb04AI}": "RB04",
    "{Rb15_HB}": "RB15",
    "{Rb15AI}": "RB15",
    "{LYSBOMB_V7V}": "LYSB",
    "{LYSBOMB_S7V}": "LYSB",
    "{LYSBOMB_S7H}": "LYSB",
    "{LYSBOMB_V7H}": "LYSB",
    "{M71BOMB}": "M71",
    "{M71BOMBD}": "M71",
    "{RB75}": "RB75",
    "{RB75B}": "RB75",
    "{RB75T}": "RB75",
    "{Robot05}": "RB05"
   },
   "ok": [
    [
     "AKAN",
     "RB75"
    ],
    [
     "AKAN",
     "RB05"
    ]
   ]
  }
 ],
 "Mi-24P": [
  {
   "id": "mi24-matrix",
   "k": "rack",
   "st": {
    "2": 1,
    "3": 2,
    "4": 3,
    "5": 4
   },
   "fam": {
    "GUV_YakB_GSHP": "GUV",
    "GUV_VOG": "GUV",
    "{96A7F676-F956-404A-AD04-F33FB2C74884}": "KMGU",
    "{96A7F676-F956-404A-AD04-F33FB2C74881}": "KMGU",
    "{APU_68_S-24}": "S24",
    "B_8V20A_CM": "S8",
    "B_8V20A_OFP2": "S8",
    "B_8V20A_OM": "S8",
    "{6A4B9E69-64FE-439a-9163-3A87FB6A4D81}": "S8",
    "{FC56DF80-9B09-44C5-8976-DCFAFF219062}": "S13",
    "{UB-32A-24}": "S5",
    "{UB32A24_S5KP}": "S5",
    "{UB32A24_S5M}": "S5",
    "{FB3CE165-BF07-4979-887C-92B87F13276B}": "BOMB",
    "{3C612111-C7AD-476E-8A8E-2485812F4E5C}": "BOMB",
    "{FAB_250_M62}": "BOMB",
    "{37DCC01E-9E02-432F-B61D-10C166CA2798}": "BOMB",
    "{4203753F-8198-4E85-9924-6F8FF679F9FF}": "BOMB",
    "{RBK_250_275_AO_1SCH}": "BOMB",
    "{D5435F26-F120-4FA3-9867-34ACE562EF1B}": "BOMB",
    "{7AEC222D-C523-425e-B714-719C0D1EB14D}": "BOMB",
    "{RBK_500U_OAB_2_5RT}": "BOMB",
    "{APU-60-1_R_60M}": "R60",
    "{B0DBC591-0F52-4F7D-AD7B-51E67725FB81}": "R60",
    "{275A2855-4A79-4B2D-B082-91EA2ADF4691}": "R60",
    "{2x9M114_with_adapter}": "ATGM",
    "{2x9M120_Ataka_V_with_adapter}": "ATGM",
    "{2x9M120F_Ataka_V_with_adapter}": "ATGM",
    "{2x9M220_Ataka_V_with_adapter}": "ATGM"
   },
   "bombs": {
    "fam": "BOMB",
    "st": [
     "3",
     "4"
    ],
    "id": "mi24-bombs"
   },
   "sym": {
    "ATGM|BOMB": "mi24-bombs",
    "ATGM|GUV": "mi24-guv",
    "ATGM|S5": "mi24-atgm",
    "BOMB|GUV": "mi24-bombs",
    "BOMB|R60": "mi24-bombs",
    "BOMB|S13": "mi24-bombs",
    "BOMB|S24": "mi24-bombs",
    "BOMB|S8": "mi24-bombs",
    "GUV|KMGU": "mi24-guv",
    "GUV|R60": "mi24-guv",
    "GUV|S13": "mi24-guv",
    "GUV|S24": "mi24-guv",
    "GUV|S5": "mi24-guv",
    "GUV|S8": "mi24-guv",
    "KMGU|S13": "mi24-kmgu",
    "KMGU|S24": "mi24-kmgu",
    "KMGU|S5": "mi24-kmgu",
    "KMGU|S8": "mi24-kmgu",
    "R60|S5": "mi24-r60",
    "S13|S24": "mi24-s24",
    "S13|S5": "mi24-s13",
    "S24|S5": "mi24-s24",
    "S24|S8": "mi24-s24",
    "S5|S8": "mi24-s8"
   },
   "asym": {
    "ATGM|BOMB": "mi24-bombs",
    "ATGM|GUV": "mi24-guv",
    "ATGM|S13": "mi24-atgm",
    "ATGM|S5": "mi24-atgm",
    "ATGM|S8": "mi24-atgm-asym",
    "BOMB|GUV": "mi24-bombs",
    "BOMB|R60": "mi24-bombs",
    "BOMB|S13": "mi24-bombs",
    "BOMB|S24": "mi24-bombs",
    "BOMB|S8": "mi24-bombs",
    "GUV|KMGU": "mi24-guv",
    "GUV|R60": "mi24-guv",
    "GUV|S13": "mi24-guv",
    "GUV|S24": "mi24-guv",
    "GUV|S5": "mi24-guv",
    "GUV|S8": "mi24-guv",
    "KMGU|S13": "mi24-kmgu",
    "KMGU|S24": "mi24-kmgu",
    "KMGU|S5": "mi24-kmgu",
    "KMGU|S8": "mi24-kmgu",
    "R60|S13": "mi24-r60",
    "R60|S5": "mi24-r60",
    "R60|S8": "mi24-r60-asym",
    "S13|S24": "mi24-s24",
    "S13|S5": "mi24-s13",
    "S24|S5": "mi24-s24",
    "S24|S8": "mi24-s24",
    "S5|S8": "mi24-s8"
   }
  }
 ],
 "MiG-21Bis": [
  {
   "id": "mig21-ecm",
   "k": "excl",
   "g": [
    {
     "st": [
      "3"
     ],
     "w": [
      "{SPS-141-100}"
     ]
    },
    {
     "st": [
      "6"
     ],
     "w": [
      "{ASO-2}"
     ]
    }
   ]
  }
 ]
}
;

// Table injectée par le build (data/loadout_rules.json), constante de la page : par type, « x » (exclusions) et « r » (exigences), chaque entrée [sa, [ia…], sb, [ib…]] — sa, sb : stations ; ia, ib : index dans AIRCRAFT_PYLONS.clsids.
// x : un CLSID de ia en sa ne va pas avec un CLSID de ib en sb (ib nul : avec toute charge) ; r : un CLSID de ia en sa exige en sb un CLSID de ib.
// Les règles du jeu d'un type, prêtes à l'emploi (construites au premier appel) : xa[station] / xb[station] = ses exclusions côté sa / côté sb, r[station] = ses exigences ; les index deviennent des ensembles.
const payloadGameCache = {};
let payloadClsidMap = null;
function payloadClsidIdx(c) {
  if (payloadClsidMap === null) payloadClsidMap = new Map(AIRCRAFT_PYLONS.clsids.map((k, i) => [k, i]));
  return payloadClsidMap.get(c);
}
function payloadGameIndex(type) {
  if (payloadHas(payloadGameCache, type)) return payloadGameCache[type];
  const g = PAYLOAD_GAME_RULES[type], out = { xa: {}, xb: {}, r: {} };
  const e = a => ({ sa: a[0], ia: new Set(a[1]), sb: a[2], ib: a[3] === null ? null : new Set(a[3]), need: a[3] });
  const push = (o, k, v) => { if (!payloadHas(o, k)) o[k] = []; o[k].push(v); };
  g.x.forEach(a => { const v = e(a); push(out.xa, v.sa, v); push(out.xb, v.sb, v); });
  g.r.forEach(a => { const v = e(a); push(out.r, v.sa, v); });
  payloadGameCache[type] = out;
  return out;
}
// Les conflits que créerait le CLSID `c` posé à la station `n` de `type` : [{ st, rule }] — les AUTRES stations de l'emport `st` (station → CLSID, '' = vide)
// dont le contenu ne peut pas aller avec `c` en `n`, et l'id de la règle —, triés par numéro de station puis par règle. [] pour un CLSID vide ou un type sans règle.
// Les règles écrites (PAYLOAD_RULES) et celles du jeu (PAYLOAD_GAME_RULES, id « game », dans les deux sens) ; une station déjà en conflit par une règle écrite n'en reçoit pas d'autre.
// La forme « rack » (le Mi-24P) juge l'emport entier, c posé en n : symétrique (rack 1 = rack 4 et rack 2 = rack 3, le vide comptant) il suit la table sym, sinon asym ; une paire de familles différentes de la table est interdite (bombes : seulement si la bombe est en station 3 ou 4) ;
// les conflits sont les stations en paire interdite avec n, et celles dont la paire n'était pas interdite dans l'emport reçu et le devient, c rendant l'emport asymétrique.
// Une règle du jeu entre deux stations d'un même groupe de PAYLOAD_ONE_OF (les portes du Mi-24P) n'est pas rendue : le groupe dit déjà la même contrainte (l'autre station est vidée, avec son message).
// Fonction pure : ni DOM, ni t(), ni stockage.
function payloadRuleConflicts(type, st, n, c) {
  if (typeof c !== 'string' || c === '' || typeof type !== 'string') return [];
  const written = payloadHas(PAYLOAD_RULES, type), game = payloadHas(PAYLOAD_GAME_RULES, type);
  if (!written && !game) return [];
  n = String(n);
  const out = [];
  const put = (m, rule) => { if (!out.some(x => x.st === m && x.rule === rule)) out.push({ st: m, rule }); };
  if (written) PAYLOAD_RULES[type].forEach(r => {
    if (r.k === 'mix') {
      if (!payloadHas(r.fam, c)) return;
      const f = r.fam[c];
      Object.keys(st).forEach(m => {
        const o = st[m];
        if (m === n || typeof o !== 'string' || o === '' || !payloadHas(r.fam, o)) return;
        const g = r.fam[o];
        if (g === f || r.ok.some(p => (p[0] === f && p[1] === g) || (p[0] === g && p[1] === f))) return;
        put(m, r.id);
      });
    } else if (r.k === 'rack') {
      if (!payloadHas(r.st, n)) return;
      const cur = (S, m) => (payloadHas(S, m) && typeof S[m] === 'string') ? S[m] : '';
      const stOf = {};
      Object.keys(r.st).forEach(m => { stOf[r.st[m]] = m; });
      const key = (S, m) => { const o = cur(S, m); return payloadHas(r.fam, o) ? r.fam[o] : o; };
      const isSym = S => key(S, stOf[1]) === key(S, stOf[4]) && key(S, stOf[2]) === key(S, stOf[3]);
      // l'id de la règle qui interdit la paire (a, b) dans l'emport S, ou null
      const banned = (S, a, b) => {
        const oa = cur(S, a), ob = cur(S, b);
        if (!payloadHas(r.fam, oa) || !payloadHas(r.fam, ob)) return null;
        const fa = r.fam[oa], fb = r.fam[ob];
        if (fa === fb) return null;
        const tab = isSym(S) ? r.sym : r.asym, pk = fa < fb ? fa + '|' + fb : fb + '|' + fa;
        if (!payloadHas(tab, pk)) return null;
        const id = tab[pk];
        if (id === r.bombs.id && r.bombs.st.indexOf(fa === r.bombs.fam ? a : fb === r.bombs.fam ? b : '') < 0) return null;
        return id;
      };
      const E = Object.assign({}, st);
      E[n] = c;
      const sts = Object.keys(r.st);
      sts.forEach(m => {
        if (m === n) return;
        const id = banned(E, n, m);
        if (id !== null) put(m, id);
      });
      sts.forEach((a, i) => sts.forEach((b, j) => {
        if (j <= i || a === n || b === n) return;
        const id = banned(E, a, b);
        if (id !== null && banned(st, a, b) === null) { put(a, id); put(b, id); }
      }));
    } else if (r.k === 'excl') {
      r.g.forEach((gi, i) => {
        if (gi.st.indexOf(n) < 0 || gi.w.indexOf(c) < 0) return;
        r.g.forEach((gj, j) => {
          if (j === i) return;
          gj.st.forEach(m => {
            const o = payloadHas(st, m) ? st[m] : '';
            if (m !== n && typeof o === 'string' && gj.w.indexOf(o) >= 0) put(m, r.id);
          });
        });
      });
    }
  });
  if (game) {
    const gi = payloadGameIndex(type), ci = payloadClsidIdx(c);
    const have = new Set(out.map(x => x.st));
    const cur = m => (payloadHas(st, m) && typeof st[m] === 'string') ? st[m] : '';
    const door = payloadOneOfOthers(type, n);
    const hit = m => { if (!have.has(m) && door.indexOf(m) < 0) { have.add(m); out.push({ st: m, rule: 'game' }); } };
    // c en sa : conflit avec sb si elle porte une charge que la règle exclut
    if (payloadHas(gi.xa, n)) gi.xa[n].forEach(e => {
      if (ci === undefined || !e.ia.has(ci)) return;
      const o = cur(e.sb);
      if (o !== '' && (e.ib === null || e.ib.has(payloadClsidIdx(o)))) hit(e.sb);
    });
    // c en sb : conflit avec sa si elle porte une charge qui exclut c
    if (payloadHas(gi.xb, n)) gi.xb[n].forEach(e => {
      if (e.ib !== null && (ci === undefined || !e.ib.has(ci))) return;
      const o = cur(e.sa);
      if (o !== '' && e.ia.has(payloadClsidIdx(o))) hit(e.sa);
    });
  }
  return out.sort((a, b) => (Number(a.st) - Number(b.st)) || (a.rule < b.rule ? -1 : a.rule > b.rule ? 1 : 0));
}

// Les exigences que le contenu `c` de la station `n` (`st[n]`, vide : aucune) laisse sans réponse (PAYLOAD_GAME_RULES, « r ») : [{ st, need }] — la station `sb` qui doit porter un des CLSID de `need`
// (dans l'ordre de la table) —, sans doublon, triées par numéro de station puis par `need`. Elles ne grisent ni ne refusent rien. Fonction pure : ni DOM, ni t(), ni stockage.
function payloadRuleMissing(type, st, n) {
  if (typeof type !== 'string' || !payloadHas(PAYLOAD_GAME_RULES, type)) return [];
  n = String(n);
  const c = (payloadHas(st, n) && typeof st[n] === 'string') ? st[n] : '';
  const ci = c === '' ? undefined : payloadClsidIdx(c);
  if (ci === undefined) return [];
  const gi = payloadGameIndex(type);
  if (!payloadHas(gi.r, n)) return [];
  const out = [], seen = new Set();
  gi.r[n].forEach(e => {
    if (!e.ia.has(ci)) return;
    const o = (payloadHas(st, e.sb) && typeof st[e.sb] === 'string') ? st[e.sb] : '';
    if (o !== '' && e.ib.has(payloadClsidIdx(o))) return;
    const need = e.need.map(i => AIRCRAFT_PYLONS.clsids[i]);
    const key = e.sb + '|' + need.join('|');
    if (seen.has(key)) return;
    seen.add(key);
    out.push({ st: e.sb, need });
  });
  const k = x => x.need.join('|');
  return out.sort((a, b) => (Number(a.st) - Number(b.st)) || (k(a) < k(b) ? -1 : k(a) > k(b) ? 1 : 0));
}

// Plafond de leurres + paillettes : { total, fs, cs } ou null quand la table ne le donne pas
function chargeLimit(lim) {
  if (!lim || typeof lim.charge_total !== 'number' || typeof lim.flare_charge_size !== 'number' || typeof lim.chaff_charge_size !== 'number') return null;
  return { total: lim.charge_total, fs: lim.flare_charge_size, cs: lim.chaff_charge_size };
}
"""


def build_block():
    """Le texte du bloc, délimité par ses deux commentaires, avec un saut de ligne final."""
    return BLOCK_BEGIN + _JS + BLOCK_END + '\n'


if __name__ == '__main__':
    txt = build_block()
    print(f"[OK] bloc des règles d'emport : {len(txt)} caractères")
