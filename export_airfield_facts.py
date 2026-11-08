#!/usr/bin/env python3
"""Écrit airfield_facts.json : les faits du jeu sur les aérodromes de chaque théâtre (nom, position, pistes, radio de tour).

Source : pydcs au commit 84f6335d2b10207ff556dae35ef9c1fea3eee964 (LGPL-3.0), importé comme bibliothèque, aucun code recopié ;
c'est le commit de airdromes.json et d'Airfield Charts. Les builds n'ont jamais besoin de pydcs : ils lisent airfield_facts.json.

Format « dcs-airfield-facts-v1 » :
  { format, source, theatres: { <théâtre>: [ [nom, lat, lon, pistes, radios], … ] } }
  pistes : liste de "<principale>/<opposée>" dans l'ordre de pydcs (ex. "22/04"), [] s'il n'y en a pas ;
  radios : [vhf_haute, uhf, vhf_basse, hf] en Hz entiers, ou null si pydcs n'a pas de radio de tour ;
  lat, lon : degrés à 6 décimales (position.latlng() de pydcs). Triés par nom ; une ligne par aérodrome ; sortie déterministe.

Usage :  python3.12 export_airfield_facts.py            (écrit airfield_facts.json à côté du script)
         python3.12 export_airfield_facts.py <fichier>  (écrit ailleurs)
"""
import json
import os
import sys

PYDCS_COMMIT = '84f6335d2b10207ff556dae35ef9c1fea3eee964'
FORMAT = 'dcs-airfield-facts-v1'
SOURCE = 'pydcs 84f6335 (LGPL-3.0): airfield names, positions, runways and tower radios of the DCS mission editor'

# théâtre de la suite → classe de dcs.terrain (la carte Germany de pydcs est « GermanyCW », la Sinai « SinaiMap »)
THEATRES = [
    ('Caucasus', 'Caucasus'), ('Falklands', 'Falklands'), ('GermanyCW', 'Germany'), ('Kola', 'Kola'),
    ('MarianaIslands', 'MarianaIslands'), ('Nevada', 'Nevada'), ('Normandy', 'Normandy'), ('PersianGulf', 'PersianGulf'),
    ('SinaiMap', 'Sinai'), ('Syria', 'Syria'), ('TheChannel', 'TheChannel'),
]

HERE = os.path.dirname(os.path.abspath(__file__))


def facts():
    import dcs.terrain as terrain
    out = []
    for theatre, cls in THEATRES:
        t = getattr(terrain, cls)()
        rows = []
        for name in sorted(t.airports):
            a = t.airports[name]
            ll = a.position.latlng()
            pistes = ['%s/%s' % (r.main.name, r.opposite.name) for r in a.runways]
            r = a.atc_radio
            radios = None if r is None else [int(r.vhf_high_hz), int(r.uhf_hz), int(r.vhf_low_hz), int(r.hf_hz)]
            rows.append([a.name, round(ll.lat, 6), round(ll.lng, 6), pistes, radios])
        rows.sort(key=lambda x: x[0])
        out.append((theatre, rows))
    return out


def render(data):
    lines = ['{', '  "format": %s,' % json.dumps(FORMAT), '  "source": %s,' % json.dumps(SOURCE, ensure_ascii=False), '  "theatres": {']
    for i, (theatre, rows) in enumerate(data):
        lines.append('    %s: [' % json.dumps(theatre))
        for j, row in enumerate(rows):
            lines.append('      ' + json.dumps(row, ensure_ascii=False) + (',' if j < len(rows) - 1 else ''))
        lines.append('    ]' + (',' if i < len(data) - 1 else ''))
    lines += ['  }', '}']
    return '\n'.join(lines) + '\n'


def main():
    dest = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'airfield_facts.json')
    data = facts()
    with open(dest, 'w', encoding='utf-8', newline='\n') as f:
        f.write(render(data))
    n = sum(len(r) for _, r in data)
    print('[OK] %s : %d aérodromes, %d avec pistes, %d avec radio de tour' % (
        dest, n, sum(1 for _, r in data for x in r if x[3]), sum(1 for _, r in data for x in r if x[4] is not None)))


if __name__ == '__main__':
    main()
