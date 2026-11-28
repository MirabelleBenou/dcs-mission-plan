#!/usr/bin/env python3
"""Écrit dans assets.json les bibliothèques du fond papier du Route Planner (carte vectorielle sous Leaflet) :
MapLibre GL JS 6.17.0 (BSD-3-Clause), PMTiles 4.5.0 (BSD-3-Clause) et maplibre-gl-leaflet 0.1.4 (ISC), tirées du
registre npm. Une archive dont l'intégrité sha512 n'est pas celle écrite ici est refusée. Le texte de chaque fichier
est rangé à l'octet sous sa clé, après les clés existantes ; assets.json se réécrit par json.dumps(d), rien d'autre
n'y change. Relancé, l'outil redonne assets.json à l'octet. Bibliothèque standard seule.

Usage : python3 -B tools/gen_map_libs.py
"""
import base64
import hashlib
import io
import json
import os
import sys
import tarfile
import urllib.request

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_PATH = os.path.join(HERE, 'assets.json')
REGISTRY = 'https://registry.npmjs.org/'

# (paquet, version, intégrité npm « dist.integrity », [(fichier de l'archive, clé d'assets.json, taille en octets)])
PACKAGES = [
    ('maplibre-gl', '6.17.0',
     'sha512-2chIZwpLGenoUQOcnm9Pk4SLbA8ppNFq8jlpXiq9vcYm3Y1wJ3fc82FL0GLwBaPYJCLzPv/mC46KEupVov75rQ==',
     [('dist/maplibre-gl.mjs', 'lib_maplibre_gl', 1110272),
      ('dist/maplibre-gl-worker.mjs', 'lib_maplibre_gl_worker', 520114),
      ('dist/maplibre-gl.css', 'lib_maplibre_gl_css', 71596)]),
    ('pmtiles', '4.5.0',
     'sha512-CBeD4SoUluFziGdy/8k7FOjQxQy486n+929W/tWophauvMICpkZ26vGBWhDt/6b1FZQWNaf4jFdT/5+q0Wii5w==',
     [('dist/pmtiles.js', 'lib_pmtiles', 20229)]),
    ('@maplibre/maplibre-gl-leaflet', '0.1.4',
     'sha512-k57wcndZIvq3m08g2je4pjUPGr43ffNW3j+gXbymt8Vi2l1lUERUi1UmdTZcTPN8LuDDYOMWRNBaSLwpAu02ew==',
     [('leaflet-maplibre-gl.js', 'lib_maplibre_gl_leaflet', 9296)]),
]


def tarball_url(name, version):
    base = name.split('/')[-1]
    return f'{REGISTRY}{name}/-/{base}-{version}.tgz'


def fetch(url):
    with urllib.request.urlopen(url, timeout=120) as r:
        if r.status != 200:
            raise SystemExit(f'[ERREUR] {url} : HTTP {r.status}')
        return r.read()


def main():
    with open(ASSETS_PATH, encoding='utf-8') as f:
        d = json.load(f)
    for name, version, integrity, files in PACKAGES:
        url = tarball_url(name, version)
        data = fetch(url)
        got = 'sha512-' + base64.b64encode(hashlib.sha512(data).digest()).decode('ascii')
        if got != integrity:
            raise SystemExit(f'[ERREUR] {name} {version} : intégrité {got} au lieu de {integrity} — archive refusée')
        with tarfile.open(fileobj=io.BytesIO(data), mode='r:gz') as tf:
            for member, key, size in files:
                m = tf.getmember('package/' + member)
                raw = tf.extractfile(m).read()
                if len(raw) != size:
                    raise SystemExit(f'[ERREUR] {name} {member} : {len(raw)} octets au lieu de {size}')
                d[key] = raw.decode('utf-8')
                print(f'{key}  {name}@{version}/{member}  {size} o  sha256 {hashlib.sha256(raw).hexdigest()}')
    out = json.dumps(d)
    with open(ASSETS_PATH, 'w', encoding='utf-8', newline='') as f:
        f.write(out)
    print(f'[OK] {os.path.relpath(ASSETS_PATH, HERE)} — {len(out.encode("utf-8"))} octets')


if __name__ == '__main__':
    sys.exit(main())
