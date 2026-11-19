#!/usr/bin/env python3
"""Bloc « ADRESSE PUBLIQUE » : PUBLIC_TILES, l'adresse publique des tuiles, des fiches et des plans servis par l'hôte de la suite.

Une seule ligne de code, écrite ici : le Route Planner (tuiles, fiches des aérodromes) et le Flight Configurator (plans des aérodromes) l'insèrent telle quelle.

Usage (par les builds) : from public_host_block import build_block ; texte = build_block()
"""

_JS = r"""/* Adresse publique des tuiles servies par l'hôte de la suite : nos couches, et une copie des tuiles de DCS Olympus avec leur accord */
const PUBLIC_TILES = 'https://dcs-tools-4thveaw.tail777510.ts.net/tuiles/';
"""


def build_block():
    return _JS
