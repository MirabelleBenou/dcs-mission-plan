#!/usr/bin/env python3
"""Bloc « BANDES ET POSTES NON PRÉ-RÉGLÉS DES RADIOS » — une seule source pour le Flight Configurator, le Datacard Generator, HQ et le Route Planner.

Rend le texte JavaScript du bloc :
  RADIO_BANDS — la bande de chaque poste, par type et par numéro de poste, en MHz, [bas, haut] bornes comprises, sans contrôle de pas.
                Règle de Mission Tools : ce que DCS et le guide de l'appareil acceptent tous les deux quand on a les deux.
  RADIO_FREE  — les postes que la mission ne pré-règle pas, par type : numéro de poste → nombre de fréquences. Ces postes n'ont pas de numéro de canal.
  et les fonctions radioBand, radioInBand et radioFreeCount.
Les noms des postes sont ceux de radio_block.py ; les postes pré-réglés et leurs canaux (RADIO_CHANNELS) sont dans import_block.py.
Aucune dépendance au reste de la page (ni t(), ni DOM). Les builds insèrent ce texte tel quel : le bloc est identique à l'octet dans chaque dist/ qui l'emploie.

Usage (par les builds) : from radio_bands_block import build_block ; texte = build_block()
"""

BLOCK_BEGIN = '/* ===== BANDES ET POSTES NON PRÉ-RÉGLÉS DES RADIOS ===== */'
BLOCK_END = '/* ===== FIN DES BANDES ET DES POSTES NON PRÉ-RÉGLÉS ===== */'

_JS = r"""
// La bande de chaque poste, en MHz, [bas, haut] bornes comprises, sans contrôle de pas (clé = unit.type). Règle de Mission Tools : ce que DCS et le guide de l'appareil acceptent tous les deux quand on a les deux.
//   Mi-24P : R-863 (poste 1) 100 à 149,975 et 220 à 399,9 · R-828 (poste 2) 20 à 59,9 · Jadro-1I (poste 3, HF) 2 à 17,999 · guide du Mi-24P, p. 423 (DCS ne donne pas de bande).
//   Mi-8MT : R-863 100 à 149,975 et 220 à 399,975 · R-828 20 à 59,975 · Jadro-1A (HF) 2 à 17,999 · guide du Mi-8MTV2, p. 169 (pas de fichier DCS).
//   F-4E-45MC : poste 1 COMM (225 à 399,95) et poste 2 AUX, réception seule (265 à 284,9) · manuel du F-4E, chapitre « UHF Radio ».
//   Mirage-F1EE : TRAP 136 (118 à 143,975 et 225 à 399,975) et TRAP 137B (225 à 399,975) · manuel du Mirage F1 (3.13).
const RADIO_BANDS = {
  'Mi-24P': { 1: [[100, 149.975], [220, 399.9]], 2: [[20, 59.9]], 3: [[2, 17.999]] },
  'Mi-8MT': { 1: [[100, 149.975], [220, 399.975]], 2: [[20, 59.975]], 3: [[2, 17.999]] },
  'F-4E-45MC': { 1: [[225, 399.95]], 2: [[265, 284.9]] },
  'Mirage-F1EE': { 1: [[118, 143.975], [225, 399.975]], 2: [[225, 399.975]] }
};

// Les postes que la mission ne pré-règle pas, par type : numéro de poste → nombre de fréquences. Leurs fréquences vivent dans la fiche comme les canaux d'un poste pré-réglé
// (radios[poste][1 à n]) mais sans numéro de canal, et HQ ne les écrit jamais dans la mission.
const RADIO_FREE = { 'Mi-24P': { 3: 5 }, 'Mi-8MT': { 3: 5 } };

// La bande d'un poste : [[bas, haut], …] ; [] si le type ou le poste n'est pas connu.
function radioBand(type, r) {
  return Object.prototype.hasOwnProperty.call(RADIO_BANDS, type) && Object.prototype.hasOwnProperty.call(RADIO_BANDS[type], r) ? RADIO_BANDS[type][r] : [];
}
// Dans la bande = dans l'un de ses intervalles, bornes comprises.
function radioInBand(band, v) { return band.some(b => v >= b[0] - 1e-9 && v <= b[1] + 1e-9); }
// Le nombre de fréquences d'un poste que la mission ne pré-règle pas ; 0 pour tout autre poste (pré-réglé, ou inconnu).
function radioFreeCount(type, r) {
  return Object.prototype.hasOwnProperty.call(RADIO_FREE, type) && Object.prototype.hasOwnProperty.call(RADIO_FREE[type], r) ? RADIO_FREE[type][r] : 0;
}
"""


def build_block():
    """Le texte du bloc, délimité par ses deux commentaires, avec un saut de ligne final."""
    return BLOCK_BEGIN + _JS + BLOCK_END + '\n'


if __name__ == '__main__':
    txt = build_block()
    print(f"[OK] bloc des bandes et des postes non pré-réglés : {len(txt)} caractères")
