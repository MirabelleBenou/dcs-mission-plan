#!/usr/bin/env python3
"""Rend data/aircraft_templates.json : pour chaque type volable de data/aircraft_types.json, le gabarit dont HQ a besoin pour
créer un vol absent d'une mission, lu dans pydcs 1.0.0 (dcs/planes.py, dcs/helicopters.py et dcs/task.py). pydcs se lit en texte
(analyse syntaxique du fichier), jamais importé ni exécuté.

Pour chaque type :
  heli               vrai si la classe est dans dcs/helicopters.py
  task_default       le nom de la tâche par défaut, tel que DCS l'écrit (« CAS », « CAP », « Ground Attack »…)
  fuel_max           le carburant maximal (kg)
  chaff, flare       les paillettes et les leurres
  radio_frequency    la fréquence du groupe par défaut (MHz) ; une classe qui n'en dit rien prend celle de la classe mère de pydcs (251)
  length, width      la longueur et l'envergure (m)
  property_defaults  les réglages par défaut du type (AddPropAircraft), valeurs telles quelles ; une valeur None de pydcs (écrite « nil »,
                     c'est-à-dire pas de clé pour DCS) n'est pas reprise
  panel_radio        par poste, les fréquences par défaut de ses canaux : {"1": {"1": 127.5, ...}, ...}
Un attribut que la classe ne donne pas : la clé est absente (jamais null), sauf radio_frequency (voir plus haut).
Un type sans panel_radio n'a aucun poste programmable : pas de clé panel_radio.

Usage : python3 tools/gen_aircraft_templates.py <dossier racine de pydcs 1.0.0> data/aircraft_types.json data/aircraft_templates.json
"""
import ast
import json
import sys

SOURCE = ("pydcs 1.0.0 (LGPL-3.0-or-later) — dcs/planes.py, dcs/helicopters.py and dcs/task.py, the classes with flyable = True: "
          "the template HQ uses to create a flight the mission lacks (task, fuel, countermeasures, group frequency, size, "
          "default unit properties, default radio channels)")

# La valeur que pydcs donne à toute classe qui ne dit rien (dcs/unittype.py, FlyingType).
BASE_RADIO_FREQUENCY = 251


def class_attrs(path):
    """Les classes d'un fichier de pydcs : {nom de classe: {attribut: noeud de sa valeur}}."""
    with open(path, encoding='utf-8') as f:
        tree = ast.parse(f.read())
    out = {}
    for c in tree.body:
        if not isinstance(c, ast.ClassDef):
            continue
        d = {}
        for s in c.body:
            if isinstance(s, ast.Assign) and len(s.targets) == 1 and isinstance(s.targets[0], ast.Name):
                d[s.targets[0].id] = s.value
            elif isinstance(s, ast.AnnAssign) and isinstance(s.target, ast.Name) and s.value is not None:
                d[s.target.id] = s.value
        out[c.name] = d
    return out


def task_names(root):
    """{nom de la classe de tâche: nom écrit par DCS} lu dans dcs/task.py (« GroundAttack » : « Ground Attack »)."""
    names = {}
    for cname, d in class_attrs(root + '/dcs/task.py').items():
        v = d.get('name')
        if isinstance(v, ast.Constant) and isinstance(v.value, str):
            names[cname] = v.value
    return names


def literal(node, what):
    try:
        return ast.literal_eval(node)
    except Exception:
        raise SystemExit('[ERREUR] %s : forme non lue par la règle' % what)


def number(node, what):
    v = literal(node, what)
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        raise SystemExit('[ERREUR] %s : un nombre attendu' % what)
    return v


def panel_radio(node, what):
    """{poste: {canal: fréquence}} avec postes et canaux dans l'ordre numérique, clés en texte."""
    pr = literal(node, what)
    if not isinstance(pr, dict):
        raise SystemExit('[ERREUR] %s : forme non lue par la règle' % what)
    out = {}
    for post in sorted(pr):
        body = pr[post]
        if not isinstance(post, int) or not isinstance(body, dict) or set(body) != {'channels'} or not isinstance(body['channels'], dict):
            raise SystemExit('[ERREUR] %s : poste %r de forme non lue par la règle' % (what, post))
        ch = body['channels']
        for k, v in ch.items():
            if not isinstance(k, int) or isinstance(v, bool) or not isinstance(v, (int, float)):
                raise SystemExit('[ERREUR] %s : canal %r du poste %r de forme non lue par la règle' % (what, k, post))
        out[str(post)] = {str(k): ch[k] for k in sorted(ch)}
    return out


def main(root, types_path, out_path):
    with open(types_path, encoding='utf-8') as f:
        t = json.load(f)
    ids = t['helicopters'] + t['planes']
    tasks = task_names(root)
    found = {}
    for fname, heli in (('planes', False), ('helicopters', True)):
        for cname, d in class_attrs(root + '/dcs/' + fname + '.py').items():
            idn = d.get('id')
            if not (isinstance(idn, ast.Constant) and idn.value in ids):
                continue
            tid = idn.value
            tpl = {'heli': heli}
            td = d.get('task_default')
            if td is not None:
                if not (isinstance(td, ast.Attribute) and isinstance(td.value, ast.Name) and td.value.id == 'task'
                        and td.attr in tasks):
                    raise SystemExit('[ERREUR] %s : task_default non lu' % tid)
                tpl['task_default'] = tasks[td.attr]
            for key in ('fuel_max', 'chaff', 'flare', 'radio_frequency', 'length', 'width'):
                if key in d:
                    tpl[key] = number(d[key], '%s.%s' % (tid, key))
            if 'radio_frequency' not in tpl:
                tpl['radio_frequency'] = BASE_RADIO_FREQUENCY
            if 'property_defaults' in d:
                pd = literal(d['property_defaults'], tid + '.property_defaults')
                if not isinstance(pd, dict):
                    raise SystemExit('[ERREUR] %s.property_defaults : un dictionnaire attendu' % tid)
                # pydcs écrit une valeur None en « nil » : pour DCS, la clé n'existe pas ; elle est donc omise (jamais null).
                tpl['property_defaults'] = {k: v for k, v in pd.items() if v is not None}
            if 'panel_radio' in d:
                tpl['panel_radio'] = panel_radio(d['panel_radio'], tid + '.panel_radio')
            if tid in found:
                raise SystemExit('[ERREUR] type %s présent deux fois dans pydcs' % tid)
            found[tid] = tpl
    missing = [i for i in ids if i not in found]
    if missing:
        raise SystemExit('[ERREUR] types introuvables dans pydcs : %s' % missing)
    out = {'source': SOURCE, 'types': {i: found[i] for i in ids}}
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
        f.write('\n')
    print('%d types, %d avec des postes programmables' % (len(ids), sum(1 for i in ids if 'panel_radio' in found[i])))


if __name__ == '__main__':
    main(*sys.argv[1:4])
