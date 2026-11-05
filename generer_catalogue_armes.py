#!/usr/bin/env python3
"""Génère weapons_catalogue.json : les armes permises par pylône, pour les quatre appareils du Flight Configurator.

Source : pydcs (LGPL-3.0), la même que pour airfields.json. Ce script n'est PAS lancé par les builds : on le relance
à la main quand pydcs change, puis on commite le JSON.

    pip install pydcs
    python3 generer_catalogue_armes.py

Sortie (weapons_catalogue.json, clés triées, déterministe) :
  source   : « pydcs <version> (LGPL-3.0) »
  weapons  : { CLSID: nom lisible }                      (une seule fois par CLSID, tous types confondus)
  types    : { type DCS : { fuelMax, flare, chaff, gun, task, pylons: { numéro de pylône : [CLSID, …] } } }
             fuelMax : carburant interne maximum en kg ; flare / chaff : leurres et paillettes par défaut (= maximum) ;
             gun : pourcentage de munitions de canon par défaut ; task : numéro de tâche par défaut du type (31 = CAS).
"""

import json
import os
import warnings
from importlib import metadata

warnings.filterwarnings('ignore')

from dcs.helicopters import Mi_24P, Mi_8MT          # noqa: E402
from dcs.planes import F_4E_45MC, Mirage_F1EE       # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'weapons_catalogue.json')

TYPES = [Mi_24P, Mi_8MT, F_4E_45MC, Mirage_F1EE]


def _pylon_weapons(cls, n):
    """Les armes (dict pydcs : clsid, name) permises sur le pylône n, dans l'ordre de pydcs."""
    pylon = getattr(cls, 'Pylon%d' % n)
    out = []
    for value in pylon.__dict__.values():
        if isinstance(value, tuple) and len(value) == 2 and isinstance(value[1], dict) and 'clsid' in value[1]:
            out.append(value[1])
    return out


def main():
    weapons = {}
    types = {}
    for cls in TYPES:
        pylons = {}
        for n in sorted(cls.pylons):
            ids = []
            for w in _pylon_weapons(cls, n):
                clsid, name = w['clsid'], w['name']
                if weapons.setdefault(clsid, name) != name:
                    raise SystemExit('[ERREUR] CLSID %s : deux noms différents (%r, %r)' % (clsid, weapons[clsid], name))
                if clsid not in ids:
                    ids.append(clsid)
            pylons[str(n)] = ids
        fuel = cls.fuel_max
        types[cls.id] = {
            'fuelMax': int(fuel) if float(fuel).is_integer() else fuel,
            'flare': int(cls.flare),
            'chaff': int(cls.chaff),
            'gun': 100,
            'task': int(cls.task_default.id),
            'pylons': pylons,
        }
    data = {'source': 'pydcs %s (LGPL-3.0)' % metadata.version('pydcs'), 'weapons': weapons, 'types': types}
    with open(OUT, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(data, f, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
        f.write('\n')
    for t, d in types.items():
        print('%-12s pylônes %-2d  armes distinctes %-3d  carburant max %s  leurres %d  paillettes %d' % (
            t, len(d['pylons']), len({c for ids in d['pylons'].values() for c in ids}), d['fuelMax'], d['flare'], d['chaff']))
    print('[OK] %s : %d CLSID, %d Ko' % (os.path.basename(OUT), len(weapons), os.path.getsize(OUT) // 1024))


if __name__ == '__main__':
    main()
