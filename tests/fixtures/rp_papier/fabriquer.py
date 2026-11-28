#!/usr/bin/env python3
"""Fabrique les deux petites archives PMTiles (v3) du banc du fond papier, dans ce dossier, avec la bibliothèque standard seule :
- fond.pmtiles : une tuile vectorielle (MVT) au zoom 9, des entités inventées des couches « mer », « routes » et « grille » ;
- relief.pmtiles : la même tuile en raster (PNG d'une seule couleur).
Les constantes (la tuile, les entités, les couleurs) servent aussi à tests/test_rp_papier.py. Relancé, il redonne les mêmes octets.

Usage : python3 -B tests/fixtures/rp_papier/fabriquer.py
"""
import json
import math
import os
import struct
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
Z, X, Y = 9, 307, 202              # la tuile du banc (Syria, près de la côte)
EXTENT = 8192
SEA_X = 2048                       # la mer : la bande ouest de la tuile, x de 0 à 2048
TRUNK_Y = 4096                     # une route « trunk » horizontale, de x = 2600 à x = 8000
TRUNK_X0, TRUNK_X1 = 2600, 8000
MOTORWAY_X = 5000                  # une route « motorway » verticale, de y = 600 à y = 7600
MOTORWAY_Y0, MOTORWAY_Y1 = 600, 7600
RELIEF_RGB = (150, 90, 160)        # la couleur unie du relief


def tile_ll(px, py, z=Z, x=X, y=Y, extent=EXTENT):
    """Le point (px, py) de la tuile, en unités de tuile : (lat, lon)."""
    n = 2 ** z
    lon = (x + px / extent) / n * 360 - 180
    lat = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * (y + py / extent) / n))))
    return lat, lon


# ---- MVT (protobuf écrit à la main) ----
def varint(v):
    out = bytearray()
    while True:
        b = v & 0x7f
        v >>= 7
        if v:
            out.append(b | 0x80)
        else:
            out.append(b)
            return bytes(out)


def field(num, wire, payload):
    key = varint((num << 3) | wire)
    if wire == 0:
        return key + varint(payload)
    return key + varint(len(payload)) + payload


def zigzag(n):
    return (n << 1) ^ (n >> 31)


def geom(rings, closed):
    out, cx, cy = [], 0, 0
    for ring in rings:
        x0, y0 = ring[0]
        out += [(1 & 7) | (1 << 3), zigzag(x0 - cx), zigzag(y0 - cy)]
        cx, cy = x0, y0
        rest = ring[1:]
        out.append((2 & 7) | (len(rest) << 3))
        for x1, y1 in rest:
            out += [zigzag(x1 - cx), zigzag(y1 - cy)]
            cx, cy = x1, y1
        if closed:
            out.append((7 & 7) | (1 << 3))
    return out


def packed(vals):
    return b''.join(varint(v) for v in vals)


def layer(name, feats):
    """feats : [(type 1 point | 2 ligne | 3 polygone, {clé: texte}, anneaux)]"""
    keys, values, body = [], [], b''
    for i, (gtype, props, rings) in enumerate(feats):
        tags = []
        for k, v in props.items():
            if k not in keys:
                keys.append(k)
            if v not in values:
                values.append(v)
            tags += [keys.index(k), values.index(v)]
        f = field(1, 0, i + 1) + field(2, 2, packed(tags)) + field(3, 0, gtype) + field(4, 2, packed(geom(rings, gtype == 3)))
        body += field(2, 2, f)
    out = field(15, 0, 2) + field(1, 2, name.encode('utf-8')) + body
    out += b''.join(field(3, 2, k.encode('utf-8')) for k in keys)
    out += b''.join(field(4, 2, field(1, 2, v.encode('utf-8'))) for v in values)
    out += field(5, 0, EXTENT)
    return field(3, 2, out)


def mvt():
    sea = [(0, 0), (SEA_X, 0), (SEA_X, EXTENT), (0, EXTENT), (0, 0)]
    return (layer('mer', [(3, {}, [sea])])
            + layer('routes', [(2, {'classe': 'trunk'}, [[(TRUNK_X0, TRUNK_Y), (TRUNK_X1, TRUNK_Y)]]),
                               (2, {'classe': 'motorway'}, [[(MOTORWAY_X, MOTORWAY_Y0), (MOTORWAY_X, MOTORWAY_Y1)]])])
            + layer('grille', [(2, {'type': 'ligne'}, [[(0, 0), (EXTENT, EXTENT)]]),
                               (1, {'type': 'e', 'texte': '12'}, [[(4000, 1000)]])]))


# ---- PNG d'une couleur ----
def png(w, h, rgb):
    rows = b''.join(b'\x00' + bytes(rgb) * w for _ in range(h))

    def chunk(t, d):
        return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(rows, 9)) + chunk(b'IEND', b'')


# ---- PMTiles v3 ----
def tile_id(z, x, y):
    acc = sum(4 ** i for i in range(z))
    n = 2 ** z
    d, s = 0, n // 2
    while s > 0:
        rx = 1 if (x & s) > 0 else 0
        ry = 1 if (y & s) > 0 else 0
        d += s * s * ((3 * rx) ^ ry)
        if ry == 0:                              # rotation dans le carré de côté s
            if rx == 1:
                x, y = s - 1 - x, s - 1 - y
            x, y = y, x
        s //= 2
    return acc + d


def pmtiles(data, tile_type, name):
    tid = tile_id(Z, X, Y)
    root = varint(1) + varint(tid) + varint(1) + varint(len(data)) + varint(0 + 1)
    meta = json.dumps({'name': name, 'attribution': 'test'}, separators=(',', ':')).encode('utf-8')
    (s, w), (n, e) = tile_ll(0, EXTENT), tile_ll(EXTENT, 0)
    root_off = 127
    meta_off = root_off + len(root)
    data_off = meta_off + len(meta)
    clat, clon = tile_ll(EXTENT / 2, EXTENT / 2)
    head = b'PMTiles' + bytes([3]) + struct.pack('<QQQQQQQQQQQ', root_off, len(root), meta_off, len(meta), data_off, 0, data_off, len(data), 1, 1, 1)
    head += bytes([1, 1, 1, tile_type, Z, Z])                # groupée, sans compression interne ni des tuiles, type, zooms
    head += struct.pack('<iiii', round(w * 1e7), round(s * 1e7), round(e * 1e7), round(n * 1e7))
    head += bytes([Z]) + struct.pack('<ii', round(clon * 1e7), round(clat * 1e7))
    assert len(head) == 127
    return head + root + meta + data


def main():
    out = {'fond.pmtiles': pmtiles(mvt(), 1, 'fond'), 'relief.pmtiles': pmtiles(png(256, 256, RELIEF_RGB), 2, 'relief')}
    for k, v in out.items():
        with open(os.path.join(HERE, k), 'wb') as f:
            f.write(v)
        print(k, len(v), 'octets')


if __name__ == '__main__':
    main()
