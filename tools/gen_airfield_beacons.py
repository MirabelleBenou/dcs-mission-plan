#!/usr/bin/env python3
"""Génère airfield_beacons.json : les balises radio des aérodromes de DCS, pour le bloc « Balises — terrains » du Datacard Generator.

Usage : python3 -B tools/gen_airfield_beacons.py <dossier downloads/navaids de DCS Airfield Charts> --commit <sha> [--out <fichier>]

Le dossier est celui de `downloads/navaids/` de dcs-airfield-charts : un fichier par théâtre (`Syria.json`…, format `dcs-navaids-v1`), dont chaque aérodrome porte
`beacons` : la liste des balises que le jeu lui rattache (fichiers du jeu, `beacons.lua`), ou null quand elles ne sont pas connues. Rien n'est importé de pydcs.
Seuls les théâtres dont un aérodrome au moins a une liste `beacons` (non nulle) sont gardés, et dans chacun seuls les aérodromes qui ont au moins une balise ;
les balises sont gardées brutes, dans l'ordre du fichier. Le commit (`--commit`, obligatoire : 40 caractères hexadécimaux) est celui du dépôt de Charts lu.

Le fichier rendu est compact et stable (clés triées, aucun espace, une fin de ligne) : deux fabrications de suite donnent le même fichier, à l'octet.
  { "format": "dcs-airfield-beacons-v1",
    "source": { "commit": "<sha>", "repo": "MirabelleBenou/dcs-airfield-charts" },
    "theatres": { "<théâtre>": { "<nom>": [ [type, indicatif, fréquence Hz | null, canal | null, piste | null], … ], … }, … } }
Sortie par défaut : airfield_beacons.json, à la racine du dépôt.
"""
import glob
import json
import os
import re
import sys

FORMAT_IN = 'dcs-navaids-v1'
FORMAT_OUT = 'dcs-airfield-beacons-v1'
REPO = 'MirabelleBenou/dcs-airfield-charts'
# Les types que le Datacard Generator sait écrire (son ordre d'affichage, puis les deux moitiés des ILS et des PRMG) : un autre type arrête la fabrication
TYPES = ['HOMER', 'AIRPORT_HOMER', 'AIRPORT_HOMER_WITH_MARKER', 'ILS_FAR_HOMER', 'ILS_NEAR_HOMER', 'RSBN', 'PRMG_LOCALIZER', 'PRMG_GLIDESLOPE',
         'TACAN', 'AIRPORT_TACAN', 'VOR', 'VOR_DME', 'DME', 'VORTAC', 'ILS_LOCALIZER', 'ILS_GLIDESLOPE']
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def die(msg):
    sys.stderr.write('[ERREUR] ' + msg + '\n')
    sys.exit(1)


def is_int(v):
    return isinstance(v, int) and not isinstance(v, bool)


def beacon(where, b):
    """Une balise du fichier de Charts, vérifiée, en rangée [type, indicatif, fréquence, canal, piste]"""
    if not isinstance(b, dict):
        die(where + ' : balise illisible : %r' % (b,))
    ty, cs, fq, ch, rw = b.get('type'), b.get('callsign'), b.get('frequency'), b.get('channel'), b.get('runway')
    if ty not in TYPES:
        die(where + ' : type de balise inconnu : %r' % (ty,))
    if not isinstance(cs, str):
        die(where + ' : indicatif illisible : %r' % (cs,))
    if not (fq is None or (is_int(fq) and fq > 0)):
        die(where + ' : fréquence illisible : %r' % (fq,))
    if not (ch is None or (is_int(ch) and ch >= 0)):
        die(where + ' : canal illisible : %r' % (ch,))
    if not (rw is None or isinstance(rw, str)):
        die(where + ' : piste illisible : %r' % (rw,))
    return [ty, cs, fq, ch, rw]


def build(folder, commit):
    files = sorted(glob.glob(os.path.join(folder, '*.json')))
    if not files:
        die('aucun fichier de théâtre dans ' + folder)
    theatres = {}
    for p in files:
        with open(p, encoding='utf-8') as f:
            d = json.load(f)
        name = os.path.basename(p)
        if not isinstance(d, dict) or d.get('format') != FORMAT_IN or not isinstance(d.get('theatre'), str) or not isinstance(d.get('airdromes'), list):
            die('%s : format %r inattendu' % (name, d.get('format') if isinstance(d, dict) else None))
        th = d['theatre']
        if th in theatres:
            die('théâtre en double : ' + th)
        known = False
        table = {}
        for a in d['airdromes']:
            if not isinstance(a, dict) or not isinstance(a.get('name'), str) or a['name'] == '':
                die('%s : aérodrome illisible : %r' % (name, a))
            bs = a.get('beacons')
            if bs is None:
                continue
            if not isinstance(bs, list):
                die('%s : %s : balises illisibles' % (name, a['name']))
            known = True
            if not bs:
                continue
            if a['name'] in table:
                die('%s : aérodrome en double : %s' % (name, a['name']))
            table[a['name']] = [beacon('%s : %s' % (name, a['name']), b) for b in bs]
        if known:
            theatres[th] = table
    return {'format': FORMAT_OUT, 'source': {'repo': REPO, 'commit': commit}, 'theatres': theatres}


def main(argv):
    args, commit, out = [], None, os.path.join(HERE, 'airfield_beacons.json')
    i = 0
    while i < len(argv):
        if argv[i] in ('--commit', '--out'):
            if i + 1 >= len(argv):
                die(argv[i] + ' : valeur attendue')
            if argv[i] == '--commit':
                commit = argv[i + 1]
            else:
                out = argv[i + 1]
            i += 2
            continue
        args.append(argv[i])
        i += 1
    if len(args) != 1:
        die('usage : gen_airfield_beacons.py <dossier downloads/navaids> --commit <sha> [--out <fichier>]')
    if not commit or not re.fullmatch(r'[0-9a-f]{40}', commit):
        die('--commit : le commit complet de dcs-airfield-charts (40 caractères hexadécimaux) est attendu')
    if not os.path.isdir(args[0]):
        die('dossier introuvable : ' + args[0])
    d = build(args[0], commit)
    text = json.dumps(d, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n'
    with open(out, 'w', encoding='utf-8', newline='\n') as f:
        f.write(text)
    n = sum(len(v) for th in d['theatres'].values() for v in th.values())
    print('[OK] %s — %d théâtre(s), %d aérodrome(s), %d balise(s), %d octets' % (os.path.relpath(out), len(d['theatres']), sum(len(th) for th in d['theatres'].values()), n, len(text.encode('utf-8'))))


if __name__ == '__main__':
    main(sys.argv[1:])
