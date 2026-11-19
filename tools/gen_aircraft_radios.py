#!/usr/bin/env python3
"""Rend data/aircraft_radios.json : pour chaque type volable de data/aircraft_types.json, ses postes programmables dans
l'éditeur de mission et le nombre de canaux que l'éditeur écrit par poste, lus dans pydcs 1.0.0 (dcs/planes.py et
dcs/helicopters.py, attribut panel_radio de chaque classe). pydcs se lit en texte, jamais importé ni exécuté.
Un type sans panel_radio n'a aucun poste programmable : {}.

Usage : python3 tools/gen_aircraft_radios.py <dossier racine de pydcs 1.0.0> data/aircraft_types.json data/aircraft_radios.json
"""
import json
import re
import sys

SOURCE = ("pydcs 1.0.0 (LGPL-3.0-or-later) — dcs/planes.py and dcs/helicopters.py, panel_radio of each flyable class: "
          "the radios the mission editor presets, by number, and the number of channels it writes for each")


def main(root, types_path, out_path):
    with open(types_path, encoding='utf-8') as f:
        t = json.load(f)
    ids = t['helicopters'] + t['planes']
    found = {}
    for name in ('planes.py', 'helicopters.py'):
        with open(root + '/dcs/' + name, encoding='utf-8') as f:
            text = f.read()
        for block in text.split('\nclass ')[1:]:
            m = re.search(r'\n    id = "([^"]+)"', block)
            if not m or m.group(1) not in ids:
                continue
            start = block.find('\n    panel_radio = {')
            posts = {}
            if start >= 0:
                body = block[start:block.find('\n    }\n', start + 5)]
                for pm in re.finditer(r'\n        (\d+): \{(.*?)\n        \}', body, re.S):
                    posts[pm.group(1)] = len(re.findall(r'\n                (\d+): ', pm.group(2)))
            found[m.group(1)] = posts
    missing = [i for i in ids if i not in found]
    if missing:
        raise SystemExit('[ERREUR] types introuvables dans pydcs : %s' % missing)
    out = {'source': SOURCE, 'types': {i: found[i] for i in ids}}
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
        f.write('\n')
    print('%d types, %d avec des postes programmables' % (len(ids), sum(1 for i in ids if found[i])))


if __name__ == '__main__':
    main(*sys.argv[1:4])
