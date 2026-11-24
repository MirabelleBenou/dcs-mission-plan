#!/usr/bin/env python3
"""Rend data/threats.json : les systèmes de défense aérienne du jeu, rangés par tools/threat_systems.json (la table tenue à la main),
avec pour chacun la portée de tir et de détection la plus grande de ses pièces, lues dans pydcs 1.0.0 (dcs/vehicles.py, classe AirDefence :
detection_range et threat_range de chaque type, en mètres), et la portée et le plafond de la fiche du DCS Threats Guide de Goldwolf.
pydcs se lit en texte, jamais importé ni exécuté.

Usage : python3 tools/gen_threats.py <dossier racine de pydcs 1.0.0> tools/threat_systems.json data/threats.json
"""
import ast
import json
import sys

SOURCE = ("pydcs 1.0.0 (LGPL-3.0-or-later) — dcs/vehicles.py, AirDefence: detection_range and threat_range of each unit type, "
          "grouped into systems; Goldwolf, DCS Threats Guide (beta v1, 17 August 2026), range and ceiling of each system's fiche, "
          "credited to its author.")
SENSOR_HEIGHT_M = {"search": 10, "fire-control": 5, "shooter": 2}
GAP_THRESHOLD = 0.1
KINDS = ('sam', 'aaa', 'radar')
BASE_CLASS = 'unittype.VehicleType'


def _dotted(node):
    """Le nom pointé d'une base de classe (« unittype.VehicleType »), ou None si ce n'est ni un nom ni un attribut de noms."""
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if not isinstance(node, ast.Name):
        return None
    parts.append(node.id)
    return '.'.join(reversed(parts))


def _int_literal(node):
    return isinstance(node, ast.Constant) and type(node.value) is int


def read_air_defence(root):
    """Lit dcs/vehicles.py par ast.parse (jamais exécuté) : la classe de tête AirDefence et ses classes imbriquées ; refuse ce qu'il ne sait pas lire."""
    with open(root + '/dcs/vehicles.py', encoding='utf-8') as f:
        text = f.read()
    try:
        tree = ast.parse(text)
    except SyntaxError as e:
        raise SystemExit('[ERREUR] dcs/vehicles.py illisible : %s' % e)
    head = next((n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'AirDefence'), None)
    if head is None:
        raise SystemExit('[ERREUR] classe AirDefence introuvable dans dcs/vehicles.py')
    types = {}
    owner = {}
    for cls in head.body:
        if not isinstance(cls, ast.ClassDef):
            continue
        bases = [_dotted(b) for b in cls.bases]
        if bases != [BASE_CLASS]:
            raise SystemExit('[ERREUR] type %s : sa base (%s) n\'est pas %s, un héritage qu\'on ne sait pas lire' % (cls.name, ', '.join(str(b) for b in bases) or 'aucune', BASE_CLASS))
        seen = {}
        for st in cls.body:
            if isinstance(st, ast.Assign) and len(st.targets) == 1 and isinstance(st.targets[0], ast.Name):
                key, val = st.targets[0].id, st.value
            elif isinstance(st, ast.AnnAssign) and isinstance(st.target, ast.Name) and st.value is not None:
                key, val = st.target.id, st.value
            else:
                continue
            if key in seen:
                raise SystemExit('[ERREUR] type %s : la clé %s est affectée deux fois' % (cls.name, key))
            seen[key] = val
        if 'id' not in seen or not (isinstance(seen['id'], ast.Constant) and isinstance(seen['id'].value, str)):
            raise SystemExit('[ERREUR] type %s : id absent ou qui n\'est pas une chaîne littérale' % cls.name)
        tid = seen['id'].value
        vals = {}
        for key in ('detection_range', 'threat_range'):
            if key in seen and not _int_literal(seen[key]):
                raise SystemExit('[ERREUR] type %s : %s n\'est pas un entier littéral (flottant, expression ou nom)' % (tid, key))
            vals[key] = seen[key].value if key in seen else 0
        if tid in types:
            raise SystemExit('[ERREUR] type %s : deux classes portent cet id (%s et %s)' % (tid, owner[tid], cls.name))
        types[tid] = vals
        owner[tid] = cls.name
    if not types:
        raise SystemExit('[ERREUR] aucune classe lue dans AirDefence de dcs/vehicles.py')
    return types


def main(root, table_path, out_path):
    types = read_air_defence(root)
    with open(table_path, encoding='utf-8') as f:
        table = json.load(f)
    excluded = table.get('excluded', [])
    systems = table['systems']
    seen = set()
    used = set(excluded)
    out_systems = []
    for s in systems:
        sid = s['id']
        if sid in seen:
            raise SystemExit('[ERREUR] id de système en double : %s' % sid)
        seen.add(sid)
        if s['kind'] not in KINDS:
            raise SystemExit('[ERREUR] nature inconnue (%r) pour le système %s' % (s['kind'], sid))
        if s['sensor'] not in SENSOR_HEIGHT_M:
            raise SystemExit('[ERREUR] capteur inconnu (%r) pour le système %s' % (s['sensor'], sid))
        if not s['pieces']:
            raise SystemExit('[ERREUR] le système %s n\'a aucune pièce' % sid)
        missing = [p for p in s['pieces'] if p not in types]
        if missing:
            raise SystemExit('[ERREUR] pièces absentes de pydcs pour le système %s : %s' % (sid, missing))
        used.update(s['pieces'])
        fire_m = max(types[p]['threat_range'] for p in s['pieces'])
        detect_m = max(types[p]['detection_range'] for p in s['pieces'])
        g = s.get('goldwolf')
        goldwolf = None
        ceiling_m = None
        gap = False
        if g:
            goldwolf = {'range_m': round(g['range_km'] * 1000), 'ceiling_m': round(g['ceiling_km'] * 1000), 'page': g['page']}
            ceiling_m = goldwolf['ceiling_m']
            ref = detect_m if s['kind'] == 'radar' else fire_m
            if ref <= 0:
                raise SystemExit('[ERREUR] portée de référence nulle pour le système %s : écart non calculable' % sid)
            gap = abs(goldwolf['range_m'] - ref) / ref > GAP_THRESHOLD
        out_systems.append({
            'id': sid, 'name_en': s['name_en'], 'name_fr': s['name_fr'], 'kind': s['kind'], 'sensor': s['sensor'],
            'pieces': list(s['pieces']), 'fire_m': fire_m, 'detect_m': detect_m, 'ceiling_m': ceiling_m,
            'goldwolf': goldwolf, 'gap': gap,
        })
    orphans = sorted(t for t, v in types.items() if (v['detection_range'] or v['threat_range']) and t not in used)
    if orphans:
        raise SystemExit('[ERREUR] types AirDefence à portée non nulle rangés dans aucun système ni dans excluded : %s' % orphans)
    out = {'format': 'dcs-threats-v1', 'source': SOURCE, 'sensor_height_m': SENSOR_HEIGHT_M,
           'gap_threshold': GAP_THRESHOLD, 'systems': out_systems}
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
        f.write('\n')
    print('%d systèmes, %d en écart avec Goldwolf' % (len(out_systems), sum(1 for s in out_systems if s['gap'])))


if __name__ == '__main__':
    main(*sys.argv[1:4])
