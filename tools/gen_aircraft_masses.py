#!/usr/bin/env python3
"""Rend data/aircraft_masses.json : pour chaque type volable de data/aircraft_types.json (75 types), les masses que l'éditeur de
mission de DCS World compte pour le poids au décollage, lues dans le relevé de l'éditeur (me_db_api, env gui) :
  empty  EmptyWeight        — masse à vide, options d'équipement par défaut comprises (kg)
  max    MaxTakeOffWeight   — masse maximale au décollage (kg)
  ammo   AmmoWeight         — masse du plein d'obus des canons de l'appareil (kg) ; 0 sans canon
  options  (seulement pour un type qui en a) — les options d'appareil de l'éditeur qui pèsent, dans l'ordre du jeu :
           { id, kind: "check" | "list", def, label, weight?, weightWhenOn?, values? }
           values (liste) : { id, label, weightWhenOn?, weightDependentOfFuel? }
Les deux fichiers du relevé se passent en argument : ils ne sont pas dans ce dépôt. Un nombre écrit en texte par le jeu devient
un nombre ; un entier s'écrit sans décimale, les autres comme le jeu ; clés triées, une ligne par type : le fichier est stable
(deux passages, même fichier à l'octet). La sortie s'arrête, sans rien écrire, si un type de la suite manque au relevé, si une
valeur n'est pas un nombre ou si une option sort de la forme ci-dessus.

Usage : python3 tools/gen_aircraft_masses.py <masses_jeu.json> <options_jeu.json> [data/aircraft_masses.json]
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
KINDS = {'checkbox': 'check', 'comboList': 'list'}
# Les clés du relevé que la table garde ; toute autre clé de poids, ou de forme, arrête la sortie. `playerOnly` est connue et n'est pas écrite.
OPT_KEYS = {'control', 'defValue', 'id', 'label', 'playerOnly', 'values', 'weight', 'weightWhenOn'}
PROP_KEYS = {'control', 'defValue', 'id', 'playerOnly', 'values', 'weight', 'weightWhenOn'}
OPT_VAL_KEYS = {'dispName', 'id', 'weightWhenOn', 'wdf'}
PROP_VAL_KEYS = {'id', 'weightWhenOn', 'wdf'}


def fail(msg):
    raise SystemExit('[ERREUR] ' + msg)


def num(v, what):
    """Un nombre du jeu : un nombre, ou un texte qui se lit comme un nombre (le jeu les lit tels). Un entier sans décimale."""
    if isinstance(v, bool):
        fail(what + ' : un booléen n\'est pas un nombre')
    if isinstance(v, str):
        try:
            v = float(v.strip())
        except ValueError:
            fail('%s : « %s » ne se lit pas comme un nombre' % (what, v))
    if not isinstance(v, (int, float)) or v != v or v in (float('inf'), float('-inf')):
        fail(what + ' : pas un nombre')
    return int(v) if float(v).is_integer() else v


def ordered(d, what):
    """Les entrées d'une table Lua exportée ({"1": …, "2": …}) dans l'ordre numérique de leurs clés."""
    if not isinstance(d, dict) or not all(k.isdigit() for k in d):
        fail(what + ' : table numérotée attendue')
    return [d[k] for k in sorted(d, key=int)]


def build(masses, opts, types):
    out, texts = {}, []
    for ty in types:
        if ty not in masses or not isinstance(masses[ty], dict):
            fail('type absent du relevé des masses : ' + ty)
        m = masses[ty]
        for k in ('EmptyWeight', 'MaxTakeOffWeight', 'AmmoWeight'):
            if k not in m:
                fail('%s : %s absent du relevé' % (ty, k))
            if isinstance(m[k], str):
                texts.append((ty, k, m[k]))
        e = {'empty': num(m['EmptyWeight'], ty + ' EmptyWeight'), 'max': num(m['MaxTakeOffWeight'], ty + ' MaxTakeOffWeight'),
             'ammo': num(m['AmmoWeight'], ty + ' AmmoWeight')}
        props = ordered(m.get('props', {}), ty + ' props')
        olist = ordered(opts.get(ty, {}), ty + ' options')
        if len(props) != len(olist):
            fail('%s : %d options avec masse au relevé des masses, %d au relevé des libellés' % (ty, len(props), len(olist)))
        res = []
        for p, o in zip(props, olist):
            where = '%s option %s' % (ty, p.get('id'))
            if p.get('id') != o.get('id'):
                fail('%s : id différent entre les deux relevés (%r, %r)' % (where, p.get('id'), o.get('id')))
            if p.get('control') != o.get('control') or p.get('control') not in KINDS:
                fail('%s : contrôle %r hors de P1 (check, list)' % (where, p.get('control')))
            if set(p) - PROP_KEYS or set(o) - OPT_KEYS:
                fail('%s : clé hors de P1 : %s' % (where, sorted((set(p) - PROP_KEYS) | (set(o) - OPT_KEYS))))
            if not isinstance(o.get('label'), str) or o['label'] == '':
                fail(where + ' : libellé absent')
            kind = KINDS[p['control']]
            d = p.get('defValue')
            if kind == 'check':
                if not isinstance(d, bool) or d != o.get('defValue'):
                    fail(where + ' : défaut d\'une case non booléen ou différent entre les relevés')
                if 'values' in p or 'values' in o:
                    fail(where + ' : une case avec des valeurs')
            else:
                d = num(d, where + ' defValue')
            r = {'id': p['id'], 'kind': kind, 'def': d, 'label': o['label']}
            for k in ('weight', 'weightWhenOn'):
                if k in p:
                    r[k] = num(p[k], where + ' ' + k)
                    if k in o and num(o[k], where) != r[k]:
                        fail(where + ' : ' + k + ' différent entre les relevés')
            if kind == 'list':
                pv, ov = ordered(p.get('values'), where + ' values'), ordered(o.get('values'), where + ' values')
                if len(pv) != len(ov) or not pv:
                    fail(where + ' : valeurs de liste différentes entre les relevés')
                vals = []
                for a, b in zip(pv, ov):
                    if set(a) - PROP_VAL_KEYS or set(b) - OPT_VAL_KEYS:
                        fail('%s : clé de valeur hors de P1 : %s' % (where, sorted((set(a) - PROP_VAL_KEYS) | (set(b) - OPT_VAL_KEYS))))
                    if a.get('id') != b.get('id') or not isinstance(b.get('dispName'), str):
                        fail(where + ' : valeur de liste sans libellé ou d\'id différent')
                    v = {'id': num(a['id'], where + ' value id'), 'label': b['dispName']}
                    if 'weightWhenOn' in a:
                        v['weightWhenOn'] = num(a['weightWhenOn'], where)
                    if 'wdf' in a:
                        v['weightDependentOfFuel'] = num(a['wdf'], where)
                    vals.append(v)
                if d not in [v['id'] for v in vals]:
                    fail(where + ' : le défaut n\'est pas une valeur de la liste')
                r['values'] = vals
            elif 'weight' not in r and 'weightWhenOn' not in r:
                fail(where + ' : une case sans masse')
            res.append(r)
        if res:
            e['options'] = res
        out[ty] = e
    unused = [t for t in opts if t in types and t not in out]
    if unused:
        fail('options sans type : %s' % unused)
    return out, texts


def dumps(table):
    lines = ['%s: %s' % (json.dumps(t, ensure_ascii=False), json.dumps(table[t], ensure_ascii=False, sort_keys=True, separators=(', ', ': ')))
             for t in sorted(table)]
    return '{\n ' + ',\n '.join(lines) + '\n}\n'


def main(masses_path, opts_path, out_path=None):
    out_path = out_path or os.path.join(ROOT, 'data', 'aircraft_masses.json')
    with open(os.path.join(ROOT, 'data', 'aircraft_types.json'), encoding='utf-8') as f:
        t = json.load(f)
    types = t['helicopters'] + t['planes']
    if len(types) != 75 or len(set(types)) != 75:
        fail('data/aircraft_types.json : 75 types attendus')
    with open(masses_path, encoding='utf-8') as f:
        masses = json.load(f)
    with open(opts_path, encoding='utf-8') as f:
        opts = json.load(f)
    table, texts = build(masses, opts, types)
    with open(out_path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(dumps(table))
    for ty, k, v in texts:
        print('texte lu comme nombre : %s %s « %s »' % (ty, k, v))
    n = sum(1 for e in table.values() if 'options' in e)
    print('%d types, %d avec des options, %d avec un canon' % (len(table), n, sum(1 for e in table.values() if e['ammo'] > 0)))


if __name__ == '__main__':
    if len(sys.argv) not in (3, 4):
        raise SystemExit(__doc__)
    main(*sys.argv[1:])
