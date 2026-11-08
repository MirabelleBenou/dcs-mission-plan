#!/usr/bin/env python3
"""Bloc « POSTES RADIO (COMME AU COCKPIT) » — une seule source pour le Datacard Generator et HQ.

Rend le texte JavaScript du bloc : la table des noms de postes du Comm Plan Editor de Mission Tools (RADIO_POSTES,
recopiée telle quelle), le premier numéro de canal du cockpit par type et par poste (RADIO_FIRST_CHANNEL), et les
fonctions radioPosteName et radioCockpitChannel. Aucune dépendance au reste de la page (ni t(), ni DOM).
Seul l'affichage change : le .miz et tous les formats gardent le numéro de canal du .miz.
Les deux builds insèrent ce texte tel quel : le bloc est identique à l'octet dans les deux fichiers de dist/.

Usage (par les builds) : from radio_block import build_block ; texte = build_block()
"""

BLOCK_BEGIN = '/* ===== POSTES RADIO (COMME AU COCKPIT) ===== */'
BLOCK_END = '/* ===== FIN DES POSTES RADIO ===== */'

_JS = r"""
// Noms des postes par type d'appareil : table du Comm Plan Editor de Mission Tools (clé = unit.type, sensible à la casse).
@@TABLE@@

// Premier numéro de canal du cockpit, par type et par poste. Tout type ou poste absent : 1 (le numéro du .miz).
const RADIO_FIRST_CHANNEL = { "Mi-24P": { 1: 0, 2: 0 }, "Mi-8MT": { 1: 1, 2: 1 } };

// Nom du poste pour un type et un numéro de poste ; '' si le type ou le poste est inconnu.
function radioPosteName(type, radioIndex) {
  const map = Object.prototype.hasOwnProperty.call(RADIO_POSTES, type) ? RADIO_POSTES[type] : null;
  return map && Object.prototype.hasOwnProperty.call(map, radioIndex) ? map[radioIndex] : '';
}

// Numéro de canal tel que le cockpit le montre, depuis le numéro du .miz ; une entrée qui n'est pas un entier >= 1 est rendue telle quelle.
function radioCockpitChannel(type, radioIndex, mizChannel) {
  const s = String(mizChannel);
  const n = Number(s);
  if (!/^\s*\d+\s*$/.test(s) || !(n >= 1)) return s;
  const fm = Object.prototype.hasOwnProperty.call(RADIO_FIRST_CHANNEL, type) ? RADIO_FIRST_CHANNEL[type] : null;
  const first = fm && Object.prototype.hasOwnProperty.call(fm, radioIndex) ? fm[radioIndex] : 1;
  return String(n - 1 + first);
}
"""


def build_block():
    """Le texte du bloc, délimité par ses deux commentaires, avec un saut de ligne final."""
    return BLOCK_BEGIN + _JS.replace('@@TABLE@@', TABLE) + BLOCK_END + '\n'


TABLE = r"""const RADIO_POSTES = {
  // ─── Soviétiques / Russes ─────────────────────────────────────────────
  "Mi-24P":      { 1: "R-863 (VHF/UHF)",   2: "R-828 (VHF FM)",      3: "Jadro-1I (HF)" },
  "Mi-8MT":      { 1: "R-863 (VHF/UHF)",   2: "R-828 (VHF FM)",      3: "Jadro-1A (HF)" },
  "Ka-50_3":     { 1: "R-800L1 (VHF/UHF)", 2: "R-828 (VHF FM)" },
  "MiG-29A":     { 1: "R-862 (VHF/UHF)" },
  "MiG-29S":     { 1: "R-862 (VHF/UHF)" },
  "MiG-29G":     { 1: "R-862 (VHF/UHF)" },
  "MiG-29 Fulcrum": { 1: "R-862 (VHF/UHF)" },
  "MiG-21Bis":   { 1: "R-832M (VHF/UHF)" },
  "MiG-15bis":   { 1: "RSI-6K (HF)" },
  "Su-25T":      { 1: "R-862 (VHF/UHF)" },
  "Su-27":       { 1: "R-862 (VHF/UHF)" },
  "Su-33":       { 1: "R-862 (VHF/UHF)" },
  // ─── OTAN — chasseurs ─────────────────────────────────────────────────
  "F-5E-3":      { 1: "AN/ARC-164 (UHF)" },
  "F-4E-45MC":   { 1: "AN/ARC-164(V) (UHF COMM)",     2: "AN/ARC-164 (UHF AUX)" },
  "F-14B":       { 1: "AN/ARC-159 (UHF - COMM 1)",    2: "AN/ARC-182 (V/UHF - COMM 2)" },
  "F-14A-135-GR":{ 1: "AN/ARC-159 (UHF - COMM 1)",    2: "AN/ARC-182 (V/UHF - COMM 2)" },
  "F-14A-135-GR-Early": { 1: "AN/ARC-159 (UHF - COMM 1)", 2: "AN/ARC-182 (V/UHF - COMM 2)" },
  "F-15C":       { 1: "AN/ARC-164 (UHF)" },
  "F-15ESE":     { 1: "AN/ARC-164 (UHF - COMM 1)",    2: "V/UHF (COMM 2)" },
  "F-16C_50":    { 1: "AN/ARC-164 (UHF - COMM 1)",    2: "AN/ARC-222 (V/UHF - COMM 2)" },
  "FA-18C_hornet":{ 1: "AN/ARC-210 (V/UHF - COMM 1)", 2: "AN/ARC-210 (V/UHF - COMM 2)" },
  "JF-17":       { 1: "R&S M3AR (V/UHF - COMM 1)",    2: "R&S M3AR (V/UHF - COMM 2)" },
  // ─── OTAN — Mirage F1 ─────────────────────────────────────────────────
  "Mirage-F1CE": { 1: "TRAP 138 (UHF - Principale)",  2: "TRAP 139 (V/UHF - Auxiliaire)" },
  "Mirage-F1BE": { 1: "TRAP 138 (UHF - Principale)",  2: "TRAP 139 (V/UHF - Auxiliaire)" },
  "Mirage-F1CR": { 1: "TRAP 138 (UHF - Principale)",  2: "TRAP 139 (V/UHF - Auxiliaire)" },
  "Mirage-F1EE": { 1: "TRAP 136 (V/UHF - Verte)",     2: "TRAP 137B (UHF - Rouge)" },
  "Mirage-F1M":  { 1: "TRAP 136 (V/UHF - Verte)",     2: "TRAP 137B (UHF - Rouge)" },
  "M-2000C":     { 1: "UHF",                            2: "V/UHF" },
  // ─── Attaque / CAS ────────────────────────────────────────────────────
  "A-10C":       { 1: "AN/ARC-186 (VHF AM)", 2: "AN/ARC-164 (UHF)",  3: "AN/ARC-186 (VHF FM)" },
  "A-10C_2":     { 1: "AN/ARC-210 (V/UHF)",    2: "AN/ARC-164 (UHF)",  3: "AN/ARC-186 (VHF FM)" },
  "AV8BNA":      { 1: "AN/ARC-210 (V/UHF - COMM 1)", 2: "AN/ARC-210 (V/UHF - COMM 2)", 3: "V/UHF (RCS)" },
  // ─── Hélicoptères OTAN ────────────────────────────────────────────────
  "AH-64D_BLK_II": {
    1: "AN/ARC-186 (VHF - COMM 1)", 2: "AN/ARC-164 (UHF - COMM 2)",
    3: "AN/ARC-201D (FM1 - COMM 3)", 4: "AN/ARC-201D (FM2 - COMM 4)",
    5: "AN/ARC-220 (HF - COMM 5)"
  },
  "CH-47Fbl1": {
    1: "AN/ARC-186 (VHF AM/FM)", 2: "AN/ARC-164 (UHF AM)",
    3: "AN/ARC-201D (VHF FM1)", 4: "AN/ARC-201D (VHF FM2)", 5: "AN/ARC-220 (HF)"
  },
  "UH-1H":       { 1: "AN/ARC-134 (VHF AM)", 2: "AN/ARC-131 (VHF FM)", 3: "AN/ARC-51BX (UHF)" },
  "OH58D":       { 1: "AN/ARC-164 (UHF)", 2: "AN/ARC-186 (VHF AM)", 3: "AN/ARC-201 (VHF FM1)", 4: "AN/ARC-201 (VHF FM2)" },
  // ─── Hélicoptères français — Gazelles ─────────────────────────────────
  "SA342L":      { 1: "Radio FM (VHF FM)" },
  "SA342M":      { 1: "Radio FM (VHF FM)" },
  "SA342Minigun":{ 1: "Radio FM (VHF FM)" },
  "SA342Mistral":{ 1: "Radio FM (VHF FM)" },
  // ─── Transport ────────────────────────────────────────────────────────
  "C-130J-30":   { 1: "UHF 1/2 (UHF)", 2: "VHF 1/2 (VHF)" },
  "Hercules":    { 1: "AN/ARC-164 (UHF)", 2: "AN/ARC-186 (VHF)" },
};"""

if __name__ == '__main__':
    txt = build_block()
    print(f"[OK] bloc des postes radio : {len(txt)} caractères")
