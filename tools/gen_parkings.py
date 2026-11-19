#!/usr/bin/env python3
"""Génère data/parkings.json : les places de stationnement des théâtres de DCS, pour le Flight Configurator.

Usage : python3 -B tools/gen_parkings.py <dossier downloads/parkings de DCS Airfield Charts> [data/parkings.json] [--commit <sha>]

Le dossier est celui de `downloads/parkings/` de dcs-airfield-charts : un fichier par théâtre (`Syria.json`…, format `dcs-parkings-v1`) et `aircraft.json` (`dcs-aircraft-sizes-v1`).
Rien n'est importé de pydcs : les fichiers sont lus tels quels. Le commit de Charts est celui du dépôt qui porte le dossier (git rev-parse HEAD), ou `--commit`.

Le fichier rendu est compact et stable (clés triées, aucun espace, nombres écrits comme Charts les donne) : deux fabrications de suite donnent le même fichier, à l'octet.
  { "aircraft": { "<type>": [hélico 0/1, longueur, largeur, hauteur], … },
    "source": "<la ligne source de Charts> ; dcs-airfield-charts <commit>",
    "theatres": { "<théâtre>": [ [airdromeId, nom, x, y, [ [parking, parking_id, x, y, marques, longueur, largeur, hauteur|null], … ] ], … ], … } }
  marques : 1 = place marquée hélicoptère, 2 = place marquée avion, 3 = les deux. Hauteur : null quand Charts ne la donne pas.
La clé d'un théâtre est la valeur `theatre` du fichier de Charts (celle d'un .miz : Caucasus, GermanyCW, Syria…). Les places viennent de pydcs (LGPL-3.0-or-later), comme les autres tables de data/.
"""
import glob
import json
import os
import re
import subprocess
import sys

FORMAT_THEATRE = 'dcs-parkings-v1'
FORMAT_AIRCRAFT = 'dcs-aircraft-sizes-v1'


def die(msg):
    sys.stderr.write('[ERREUR] ' + msg + '\n')
    sys.exit(1)


def git_commit(folder):
    r = subprocess.run(['git', '-C', folder, 'rev-parse', 'HEAD'], capture_output=True, text=True)
    sha = r.stdout.strip()
    return sha if r.returncode == 0 and re.fullmatch(r'[0-9a-f]{40}', sha) else ''


def read_json(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def build(folder, commit):
    air = read_json(os.path.join(folder, 'aircraft.json'))
    if air.get('format') != FORMAT_AIRCRAFT or not isinstance(air.get('aircraft'), dict):
        die('aircraft.json : format %r inattendu' % air.get('format'))
    aircraft = {}
    for ty, a in air['aircraft'].items():
        aircraft[ty] = [1 if a['heli'] else 0, a['length'], a['width'], a.get('height')]
    sources = set()
    theatres = {}
    files = sorted(p for p in glob.glob(os.path.join(folder, '*.json')) if os.path.basename(p) != 'aircraft.json')
    if not files:
        die('aucun fichier de théâtre dans ' + folder)
    for p in files:
        d = read_json(p)
        if d.get('format') != FORMAT_THEATRE or not isinstance(d.get('theatre'), str) or not isinstance(d.get('airdromes'), list):
            die('%s : format %r inattendu' % (os.path.basename(p), d.get('format')))
        if d['theatre'] in theatres:
            die('théâtre en double : ' + d['theatre'])
        sources.add(d.get('source', ''))
        bases = []
        for b in d['airdromes']:
            places = []
            for s in b['parkings']:
                marks = (1 if s['heli'] else 0) + (2 if s['plane'] else 0)
                places.append([s['parking'], s['parking_id'], s['x'], s['y'], marks, s['length'], s['width'], s.get('height')])
            bases.append([b['airdromeId'], b['name'], b['x'], b['y'], places])
        theatres[d['theatre']] = bases
    if len(sources) != 1:
        die('les fichiers de Charts ne portent pas la même ligne source : %s' % sorted(sources))
    src = sources.pop() + ' ; dcs-airfield-charts ' + commit
    return {'source': src, 'aircraft': aircraft, 'theatres': theatres}


def main(argv):
    args = [a for a in argv if not a.startswith('--')]
    commit = ''
    if '--commit' in argv:
        i = argv.index('--commit')
        commit = argv[i + 1] if i + 1 < len(argv) else ''
        args = [a for a in args if a != commit]
    if not args or len(args) > 2:
        die('usage : gen_parkings.py <dossier downloads/parkings> [sortie] [--commit <sha>]')
    folder = args[0]
    out = args[1] if len(args) > 1 else os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'parkings.json')
    commit = commit or git_commit(folder)
    if not commit:
        die('commit de Charts introuvable : le dossier n\'est pas dans un dépôt git, donnez --commit <sha>')
    doc = build(folder, commit)
    text = json.dumps(doc, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n'
    with open(out, 'w', encoding='utf-8', newline='\n') as f:
        f.write(text)
    n = sum(len(b[4]) for bs in doc['theatres'].values() for b in bs)
    print('[OK] %s : %d théâtres, %d places, %d types d\'appareil, %d octets' % (out, len(doc['theatres']), n, len(doc['aircraft']), len(text.encode('utf-8'))))


if __name__ == '__main__':
    main(sys.argv[1:])
