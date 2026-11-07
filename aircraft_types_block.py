#!/usr/bin/env python3
"""Bloc « TYPES D'APPAREILS DU JEU » — la liste des types jouables du jeu pour l'éditeur du Wing de HQ.

Lit data/aircraft_types.json (pydcs 1.0.0 : les classes flyable = True, par id, le nom du type écrit dans un .miz) et rend le
texte JavaScript du bloc : la constante GAME_AIRCRAFT_TYPES = { helicopters: [...], planes: [...] } dans l'ordre du fichier,
et les fonctions gameAircraftIsType (un nom exactement dans la table) et gameAircraftClose (les types proches d'un nom hors
table). Aucune dépendance au reste de la page (ni t(), ni DOM).
Le build s'arrête si la table n'a pas 12 hélicoptères et 63 avions, si un nom y est deux fois, ou si un nom est vide.

Usage (par le build de HQ) : from aircraft_types_block import build_block ; texte = build_block()
"""
import json
import os

BLOCK_BEGIN = '/* ===== TYPES D\'APPAREILS DU JEU ===== */'
BLOCK_END = '/* ===== FIN DES TYPES D\'APPAREILS DU JEU ===== */'

N_HELICOPTERS = 12
N_PLANES = 63
TABLE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'aircraft_types.json')

_JS = r"""
// Types jouables du jeu de base (pydcs 1.0.0), par leur nom dans un .miz ; l'ordre est celui de la table.
const GAME_AIRCRAFT_TYPES = @@TABLE@@;

// Nom exactement dans la table (casse comprise).
function gameAircraftIsType(name) {
  return GAME_AIRCRAFT_TYPES.helicopters.indexOf(name) >= 0 || GAME_AIRCRAFT_TYPES.planes.indexOf(name) >= 0;
}

// Nom réduit : minuscules, rien d'autre que les lettres a-z et les chiffres.
function gameAircraftReduce(name) {
  return String(name).toLowerCase().replace(/[^a-z0-9]/g, '');
}

// Types proches d'un nom, dans l'ordre de la table (hélicoptères, puis avions) ; [] si le nom est dans la table.
// 1. même nom réduit ; 2. sinon le plus long début commun des noms réduits, au moins 3 caractères (tous les types qui l'atteignent).
function gameAircraftClose(name) {
  if (gameAircraftIsType(name)) return [];
  const all = GAME_AIRCRAFT_TYPES.helicopters.concat(GAME_AIRCRAFT_TYPES.planes);
  const r = gameAircraftReduce(name);
  const same = all.filter(ty => gameAircraftReduce(ty) === r);
  if (same.length) return same;
  let best = 0;
  const lens = all.map(ty => {
    const q = gameAircraftReduce(ty);
    let n = 0;
    while (n < r.length && n < q.length && r.charAt(n) === q.charAt(n)) n++;
    if (n > best) best = n;
    return n;
  });
  if (best < 3) return [];
  return all.filter((ty, i) => lens[i] === best);
}
"""


def load_table(path=None):
    """La table lue et vérifiée : {'helicopters': [...], 'planes': [...]} ; SystemExit si elle est fausse."""
    path = path or TABLE_PATH
    with open(path, encoding='utf-8') as f:
        data = json.load(f)
    seen = set()
    for key, n in (('helicopters', N_HELICOPTERS), ('planes', N_PLANES)):
        names = data.get(key)
        if not isinstance(names, list) or len(names) != n:
            raise SystemExit("aircraft_types.json : %d %s attendus, %s trouvés" % (
                n, key, len(names) if isinstance(names, list) else 'aucune liste'))
        for name in names:
            if not isinstance(name, str) or not name.strip():
                raise SystemExit("aircraft_types.json : un nom vide dans %s" % key)
            if name in seen:
                raise SystemExit("aircraft_types.json : le nom %r est deux fois dans la table" % name)
            seen.add(name)
    return {'helicopters': data['helicopters'], 'planes': data['planes']}


def build_block(path=None):
    """Le texte du bloc, délimité par ses deux commentaires, avec un saut de ligne final."""
    t = load_table(path)
    table = json.dumps(t, ensure_ascii=False, indent=2)
    return BLOCK_BEGIN + _JS.replace('@@TABLE@@', table) + BLOCK_END + '\n'
