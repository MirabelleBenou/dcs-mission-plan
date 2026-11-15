#!/usr/bin/env python3
"""Bloc « SCHÉMAS DU FIELD MANUAL » : les outils de dessin des schémas (boîtes, flèches, textes FR/EN), le schéma d'ensemble des échanges
(S0, une variante large et une variante en hauteur pour le téléphone), sa légende, les six panneaux « Reçoit · Donne », puis les schémas
redessinés du Briefing Generator, du Route Planner et de la datacard.

Règle de lisibilité : la couleur d'un module marque son cadre, l'encre écrit ; aucun texte de schéma sous le corps 8.

Chaque flèche, chaque ligne de carte et chaque ligne de panneau porte data-ex="<ids de la table des échanges>" : le build compare les
ids des deux variantes de S0 et vérifie que chaque id de la table est dessiné et qu'il figure dans un panneau.

Usage (par build_field_manual.py) : from fm_schemas_block import *
"""
import collections
import html as _html
import re

NF = ' '      # espace fine insécable (typographie française)


def fr_typo(t):
    """Typographie française : espace fine insécable avant « : ; ! ? »."""
    return re.sub(r' ([:;!?])', NF + r'\1', t)


def _n(v):
    return f'{v:g}'


def _esc(s):
    return _html.escape(s, quote=False)


# ── Outils de dessin ─────────────────────────────────────────────────────────────

def sv_text(x, y, size, fr, en=None, anchor='middle', op=None, ls=None, cls=None, dx=None, extra=''):
    """<text> FR puis EN (lang-block) ; un seul <text> si les deux langues sont identiques."""
    def one(txt, lang):
        a = f' x="{_n(x)}" y="{_n(y)}" font-size="{_n(size)}"'
        if anchor != 'start':
            a += f' text-anchor="{anchor}"'
        if cls:
            a += f' class="{cls}{" lang-block" if lang else ""}"'
        else:
            a += ' fill="currentColor"'
            if lang:
                a += ' class="lang-block"'
        if lang:
            a += f' data-lang="{lang}"'
        if op is not None:
            a += f' opacity="{op}"'
        if ls is not None:
            a += f' letter-spacing="{_n(ls)}"'
        if dx is not None:
            a += f' dx="{_n(dx)}"'
        a += extra
        return f'<text{a}>{_esc(fr_typo(txt) if lang in ("fr", None) else txt)}</text>'
    if en is None or en == fr:
        return one(fr, None)
    return one(fr, 'fr') + '\n          ' + one(en, 'en')


def sv_box(x, y, w, h, mod=None, dashed=False):
    """Boîte : fond opaque clair (paper-light) ; boîte de module = aplat 20 % + trait 2 px du module."""
    cls = 'sv-box' + (f' sv-m-{mod}' if mod else '')
    a = f'<rect class="{cls}" x="{_n(x)}" y="{_n(y)}" width="{_n(w)}" height="{_n(h)}" rx="3"'
    a += ' stroke-width="2"' if mod else ' stroke="currentColor" stroke-width="1.4"'
    if dashed:
        a += ' stroke-dasharray="4 3"'
    return a + '/>'


def sv_pill(x, y, w, h, fr, en):
    """Pastille sombre (étiquette de format) et son texte clair."""
    r = f'<rect class="sv-pill" x="{_n(x)}" y="{_n(y)}" width="{_n(w)}" height="{_n(h)}" rx="2"/>'
    t = sv_text(x + w / 2, y + 9.6, 8.5, fr, en, cls='sv-pill-t', ls=1, dx=0.5)
    return r + '\n          ' + t


def sv_tag(bx, by, bw, fr, en):
    """Étiquette S / A / S·A (Standard / Avancé) à cheval sur le bord haut d'une boîte, près de son coin droit."""
    w = 26 if len(fr) > 1 else 13
    return sv_pill(bx + bw - w - 3, by - 6.5, w, 13, fr, en)


def sv_line(x1, y1, x2, y2, marker, dashed=False, sw=1.2, op=.8):
    d = ' stroke-dasharray="4 3"' if dashed else ''
    return (f'<line x1="{_n(x1)}" y1="{_n(y1)}" x2="{_n(x2)}" y2="{_n(y2)}" stroke="currentColor" '
            f'stroke-width="{_n(sw)}" opacity="{_n(op)}"{d} marker-end="url(#{marker})"/>')


def sv_path(dd, marker, dashed=False, sw=1.2, op=.8):
    d = ' stroke-dasharray="4 3"' if dashed else ''
    return (f'<path d="{dd}" fill="none" stroke="currentColor" stroke-width="{_n(sw)}" '
            f'opacity="{_n(op)}"{d} marker-end="url(#{marker})"/>')


def sv_defs(marker):
    return (f'<defs><marker id="{marker}" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto-start-reverse">'
            f'<path d="M0,0 L7,3.5 L0,7 Z" fill="currentColor" opacity=".8"/></marker></defs>')


def sv_title(fr, en, y, y_rule):
    return (sv_text(360, y, 13, fr, en, op=.9, ls=3) + '\n          '
            f'<line x1="120" y1="{_n(y_rule)}" x2="600" y2="{_n(y_rule)}" stroke="currentColor" stroke-width=".6" opacity=".3"/>')


# ═════════════════════════════════════════════════════════════════════════════════
# LA TABLE DES ÉCHANGES : les seuls ids qui se dessinent
# ═════════════════════════════════════════════════════════════════════════════════
# Retirés de la table dessinée : S11 (théâtre), S12 (unités de mesure), S13 (réglages de cap), qui sont des
# réglages et non des données échangées ; F2 (le BG ne lit plus un .miz : il prend la météo, la date et l'heure de la mission d'HQ, S2).
# F7 (configuration Wing, de HQ à un autre HQ) et F13 (anciens fichiers) n'ont pas de flèche : ils sont dans les panneaux.

TABLE_IDS = ['S1', 'S2', 'S3', 'S4', 'S5', 'S6', 'S8', 'S9', 'S10',
             'C1', 'C2', 'C3',
             'F1', 'F3', 'F4', 'F5', 'F6', 'F7', 'F8', 'F9', 'F10', 'F11', 'F12', 'F13']
NOT_DRAWN = ('F7', 'F13')

# Les flèches de S0 : clé → ids de la table. La lettre d'une clé se déduit de la place de son premier badge dans la variante large
# (de haut en bas, de gauche à droite) : voir letters().
AK = {
    'dcs_in': ['F1'], 'dcs_out': ['F3'], 'print': ['F11'], 'example': ['C3'],
    'wing': ['S1'], 'brief_rs': ['S3'], 'mission': ['S2'], 'photo': ['F8'], 'work': ['C2'],
    'pack': ['F5', 'F6'], 'fpack': ['F4'], 'brief_fl': ['S4', 'S5'], 'map': ['C1'],
    'routes': ['S8'], 'active': ['S9'], 'groups': ['S6'], 'remove': ['S10'],
    'cf': ['F10'], 'lua': ['F9'], 'knee': ['F12'],
}

# La légende : (clé, phrase d'en-tête, [(outil, phrase)]) en FR puis en EN. {clé} = la lettre de cette flèche. Une ligne par outil récepteur.
S0_LEGEND = {
    'dcs_in': (
        "DCS → HQ : le .miz d’origine entre dans HQ par Ouvrir .miz (ou déposé sur la page). HQ y lit les groupes Client (nom, coalition, unités avec type, indicatif, livrée, radios et emport, route), la date et l’heure de départ et la météo, pour les montrer, les modifier et les offrir aux autres outils.", [],
        "DCS → HQ: the original .miz enters HQ through Open .miz (or dropped on the page). HQ reads its Client groups (name, coalition, units with type, call sign, livery, radios and loadout, route), the start date and time and the weather, to show them, edit them and offer them to the other tools.", []),
    'dcs_out': (
        "HQ → DCS : HQ écrit le .miz final par Sauvegarder .miz (après Paquets de vol, Supprimer ou Dynamic Spawn) : c’est le fichier que DCS ouvre, avec les groupes modifiés.", [],
        "HQ → DCS: HQ writes the final .miz through Save .miz (after Flight packages, Delete or Dynamic Spawn): it is the file DCS opens, with the edited groups.", []),
    'print': (
        "BG → imprimé : le BG imprime son briefing par Exporter, en PDF (impression du navigateur) ou en PNG par page, pour le distribuer.", [],
        "BG → printout: the BG prints its briefing through Export, as a PDF (browser print) or one PNG per page, to hand it out.", []),
    'example': (
        "Exemple ▾ charge l’exemple STEPPE WIND par groupe d’outils, Mission Commander (briefing du BG et composition de RS) ou Flight Leader (groupes, routes, calques, datacards), et remplace le travail de ce groupe.", [],
        "Example ▾ loads the STEPPE WIND example by tool group, Mission Commander (BG briefing and RS composition) or Flight Leader (groups, routes, layers, datacards), and replaces the work of that group.", []),
    'wing': (
        "HQ → BG, RS, FC, DG : le Wing saisi dans HQ (fenêtre Wing) passe sans geste ; chaque outil en prend ceci.",
        [('BG', "le logo wing principal et le nom court (en-tête de chaque page, tampon de la barre) ; le tampon HQ (cachet de réception de la couverture) ; les escadrons : identifiant, indicatif et appareils pour la liste Escadron de chaque vol, logo escadron en haut à droite de la page du vol, avertissement si un escadron du briefing manque ; en lecture seule, le nom complet et l’identifiant."),
         ('RS', "le logo wing principal (nommé d’après le nom court) et le logo de chaque escadron (nommé d’après son identifiant), proposés dans la grille Logo de la photo avec la marque Wing ; les logos ajoutés à la main restent."),
         ('FC', "les livrées ajoutées (nom, appareils) et la livrée par défaut de chaque appareil, pour la liste Livrée."),
         ('DG', "l’indicatif et le premier appareil de l’escadron d’un vol importé du briefing."),
         ('Import FC · RP · DG', "l’indicatif et l’appareil des escadrons, pour nommer les groupes pris au briefing."),
         ('Barre de chaque outil', "le nom court.")],
        "HQ → BG, RS, FC, DG: the Wing entered in HQ (Wing window) passes with no gesture; each tool takes the following from it.",
        [('BG', "the main wing logo and the short name (header of every page, bar stamp); the HQ stamp (receipt stamp of the cover); the squadrons: identifier, call sign and aircraft for each flight’s Squadron list, squadron logo at the top right of the flight page, a warning if a squadron of the briefing is missing; read-only, the full name and the identifier."),
         ('RS', "the main wing logo (named after the short name) and each squadron’s logo (named after its identifier), offered in the photo’s Logo grid with the Wing mark; the logos added by hand stay."),
         ('FC', "the added liveries (name, aircraft) and each aircraft’s default livery, for the Livery list."),
         ('DG', "the call sign and first aircraft of the squadron of a flight imported from the briefing."),
         ('FC · RP · DG import', "the call sign and aircraft of the squadrons, to name the groups taken from the briefing."),
         ('Each tool bar', "the short name.")]),
    'brief_rs': (
        "BG → RS : à l’ouverture de RS, le BG remplit les champs vides Msn (opération et mission), DTG (date du briefing) et Class (classification) du bloc d’informations de la photo, pour ne pas les ressaisir ; un champ déjà rempli n’est jamais écrasé et Crew reste à saisir.", [],
        "BG → RS: when RS opens, the BG fills the empty fields Msn (operation and mission), DTG (briefing date) and Class (classification) of the photo’s info block, so they need not be typed again; a field already filled is never overwritten and Crew stays to be typed.", []),
    'mission': (
        "HQ → BG, FC, RP, DG : la mission ouverte dans HQ est lue par ces quatre outils, qui la prennent chacun par leur geste ; la ligne sous la barre de chacun dit quel .miz est chargé, sa date et son heure.",
        [('BG', "assistant METAR › Reprendre de la mission d’HQ (grisé tant qu’HQ n’a pas de mission) : la météo (vent au sol, QNH, visibilité, température, nuages, brouillard, poussière) remplit l’assistant, puis Insérer dans METAR place le METAR dans le briefing ; la date et l’heure vont dans l’en-tête du briefing."),
         ('FC · RP · DG', "leur fenêtre d’import (source Mission chargée dans HQ) lit, pour chaque groupe Client, le nom, la coalition, les unités (type, indicatif, numéro de bord) et, à cocher, Route, Radios, Emport et Livrée, qu’elle écrit dans la fiche des groupes."),
         ('FC', "la livrée de chaque unité dans la mission, pour présélectionner la liste Livrée tant qu’on n’en choisit pas."),
         ('DG', "la date, l’heure de départ et la météo (METAR décodé : vent, visibilité, QNH, nuages), pour les cartes des groupes importés.")],
        "HQ → BG, FC, RP, DG: the mission open in HQ is read by these four tools, which each take it through their own gesture; the line under each bar says which .miz is loaded, its date and its time.",
        [('BG', "METAR assistant › Take from HQ mission (greyed out while HQ has no mission): the weather (ground wind, QNH, visibility, temperature, clouds, fog, dust) fills the assistant, then Insert into METAR puts the METAR in the briefing; the date and time go into the briefing header."),
         ('FC · RP · DG', "their import window (source Mission loaded in HQ) reads for each Client group the name, the coalition, the units (type, call sign, tail number) and, to tick, Route, Radios, Loadout and Livery, which it writes into the group sheet."),
         ('FC', "the livery of each unit in the mission, to preselect the Livery list until you choose one."),
         ('DG', "the date, the start time and the weather (decoded METAR: wind, visibility, QNH, clouds), for the cards of the imported groups.")]),
    'photo': (
        "RS → BG : la photo ne passe pas toute seule : RS › Exporter écrit un PNG, puis dans le BG la section Photos › ajouter l’image le place dans les pages de photos du briefing.", [],
        "RS → BG: the photo does not pass by itself: RS › Export writes a PNG, then in the BG the Photos section › add the image puts it in the photo pages of the briefing.", []),
    'work': (
        "Le fichier de travail : Sauvegarder (accueil, ou chaque outil sauf HQ) écrit en un JSON le briefing, la composition de RS sans son image source, la fiche des groupes, les routes et leurs calques et les datacards ; Ouvrir le relit et remplace tout le travail. Il ne porte ni la mission d’HQ, ni la configuration Wing (RS n’en garde que le logo posé sur la photo), ni l’image source de RS, ni les presets d’emport du FC, ni les préférences d’écran.", [],
        "The work file: Save (home page, or each tool except HQ) writes in one JSON the briefing, the RS composition without its source image, the group sheet, the routes and their layers and the datacards; Open reads it back and replaces all the work. It carries neither the HQ mission, nor the Wing configuration (RS keeps only the logo placed on the photo), nor the RS source image, nor the FC loadout presets, nor the screen preferences.", []),
    'pack': (
        "HQ → FC, RP, DG : HQ exporte les groupes cochés en paquet (Paquets de vol › Exporter) que le FC, le RP et le DG ouvrent par leur fenêtre d’import (source Fichier). C’est la voie du Flight Leader qui n’a pas le .miz : pour chaque groupe, Route, Radios, Emport et Livrée à cocher, sans le .miz ouvert dans son HQ.", [],
        "HQ → FC, RP, DG: HQ exports the ticked groups as a package (Flight packages › Export) which the FC, the RP and the DG open through their import window (source File). It is the way for a Flight Leader who does not have the .miz: for each group, Route, Radios, Loadout and Livery to tick, without the .miz open in their HQ.", []),
    'fpack': (
        "FC → HQ : le FC exporte le paquet de vol (Exporter) que HQ lit par Paquets de vol › Importer des paquets puis Appliquer à la mission : HQ écrit, dans les groupes du .miz de même nom, les parties cochées (Route, Radios, Emport, Livrée) de chaque unité. C’est le seul retour d’un Flight Leader qui se fusionne.", [],
        "FC → HQ: the FC exports the flight package (Export) which HQ reads through Flight packages › Import packages then Apply to the mission: HQ writes, into the .miz groups of the same name, the ticked parts (Route, Radios, Loadout, Livery) of each unit. It is the only return from a Flight Leader that merges.", []),
    'brief_fl': (
        "BG → FC, RP, DG : le briefing en cours du BG (même navigateur) est lu par la fenêtre d’import du FC, du RP et du DG (source Briefing en cours).",
        [('FC · RP · DG', "une ligne par indicatif de vol avec son appareil et son nombre d’unités (le nombre saisi, sinon l’effectif de l’équipage, sinon un)."),
         ('FC', "les radios : au Standard les fréquences de la liste (radio, canal, fréquence), à l’Avancé le plan radio de l’appareil (radios, canaux, fréquences), posées sur le poste de même nom au canal du cockpit indiqué, les autres étant comptées ignorées."),
         ('DG', "tout le briefing (Ouvrir ▾ › Importer… › Briefing en cours) : opération, mission, date, heure, classification, tâche et menace du vol, objectif, étapes, équipage, radios, terrains avec leur piste, METAR décodé, menaces SAM et AAA, notes, pour préremplir ses cartes.")],
        "BG → FC, RP, DG: the BG’s current briefing (same browser) is read by the import window of the FC, the RP and the DG (source Current briefing).",
        [('FC · RP · DG', "one line per flight call sign with its aircraft and its number of units (the typed number, else the crew size, else one)."),
         ('FC', "the radios: in Standard the frequencies of the list (radio, channel, frequency), in Advanced the aircraft’s radio plan (radios, channels, frequencies), put on the same-name post at the cockpit channel given, the others being counted as ignored."),
         ('DG', "the whole briefing (Open ▾ › Import… › Current briefing): operation, mission, date, time, classification, flight task and threat, objective, steps, crew, radios, airfields with their runway, decoded METAR, SAM and AAA threats, notes, to pre-fill its cards.")]),
    'map': (
        "RP → BG : le RP envoie l’image de la carte (cadrée, avec échelle, nord et cartouche) au BG par Exporter ▾ › Image pour le briefing… › Exporter, sans fichier et seulement dans la même session ; la fenêtre Placer la carte du Route Planner du BG la pose, au Standard dans la page Carte ou les pages de photos, à l’Avancé en carte de SITAC, de couverture, dans les documents d’une mission ou en annexe.", [],
        "RP → BG: the RP sends the map image (framed, with scale, north and cartouche) to the BG through Export ▾ › Image for the briefing… › Export, with no file and only in the same session; the BG’s Place the Route Planner map window puts it, in Standard on the Map page or the photo pages, in Advanced as SITAC map, cover map, in a mission’s documents or as an annex.", []),
    'routes': (
        "Le RP donne ses routes (leurs points) sans geste : au FC, qui les propose dans Changer de route et en copie les points dans le groupe ; au DG, qui en fait le tableau Navigation de la carte et renvoie au RP les points qu’on y modifie ou retire.", [],
        "The RP gives its routes (their points) with no gesture: to the FC, which offers them in Change route and copies the points into the group; to the DG, which makes the card’s Navigation table from them and sends back to the RP the points edited or removed there.", []),
    'active': (
        "Le RP donne aussi au DG, sans geste, la route active et les points de référence, pour la route active de la carte et ses références.", [],
        "The RP also gives the DG, with no gesture, the active route and the reference points, for the card’s active route and its references.", []),
    'groups': (
        "FC, RP et DG partagent en direct, dans les deux sens, la fiche des groupes : nom, coalition, unités (type, indicatif, numéro de bord, livrée), radios (fréquences et canaux à imprimer), emport et route copiée ; le DG en tire une carte par groupe (indicatif, appareil, nombre, équipage, radios choisies, départ et arrivée), le RP y rattache ses routes par Groupes de la route, le FC la règle unité par unité.", [],
        "FC, RP and DG share live, both ways, the group sheet: name, coalition, units (type, call sign, tail number, livery), radios (frequencies and channels to print), loadout and copied route; the DG makes one card per group from it (call sign, aircraft, number, crew, chosen radios, departure and arrival), the RP attaches its routes to it through Route groups, the FC sets it up unit by unit.", []),
    'remove': (
        "Les datacards du DG (une carte par groupe, et des cartes libres) sont rangées à part ; Retirer ce groupe au FC retire aussi sa carte du DG, et Supprimer la datacard et le groupe au DG retire le groupe de tous les outils, pour qu’aucune carte ne reste sans groupe.", [],
        "The DG datacards (one card per group, and free cards) are stored apart; Remove this group in the FC also removes its card from the DG, and Delete the datacard and the group in the DG removes the group from all tools, so no card is left without a group.", []),
    'lua': (
        "RP ↔ DCS : le RP lit et écrit le fichier <théâtre>.lua du Route Tool de DCS (Ouvrir ▾ › Ouvrir une route…, Exporter ▾ › Route Tool…) : les points d’une route, 30 au plus, sans les points de référence, pour reprendre une route faite en jeu ou la donner au Route Tool.", [],
        "RP ↔ DCS: the RP reads and writes the <theatre>.lua file of the DCS Route Tool (Open ▾ › Open a route…, Export ▾ › Route Tool…): the points of a route, 30 at most, without the reference points, to take back a route made in game or give one to the Route Tool.", []),
    'cf': (
        "CombatFlite → RP : le RP ouvre un fichier .cf de CombatFlite par Ouvrir ▾ › Ouvrir une route… : ses calques (zones, cercles, points, orbites, boîtes, textes, symboles), à cocher puis Afficher, en lecture seule sur la carte.", [],
        "CombatFlite → RP: the RP opens a CombatFlite .cf file through Open ▾ › Open a route…: its layers (zones, circles, points, orbits, boxes, texts, symbols), to tick then Show, read-only on the map.", []),
    'knee': (
        "DG → kneeboard, imprimé : le DG exporte ses datacards par Exporter, en PNG par page (un ZIP s’il y en a plusieurs) pour le kneeboard de DCS, ou en PDF pour imprimer.", [],
        "DG → kneeboard, printout: the DG exports its datacards through Export, as one PNG per page (a ZIP if there are several) for the DCS kneeboard, or as a PDF to print.", []),
}

# Les réglages ne s'échangent pas : une phrase sous la légende
S0_SETTINGS = (
    "Les réglages ne sont pas des échanges de données : le théâtre et les unités de mesure se règlent dans la barre de l’un des trois outils du Flight Leader (FC, RP, DG) et valent pour les trois ; les réglages de cap valent pour le RP et le DG.",
    "Settings are not data exchanges: the theatre and the measurement units are set in the bar of any one of the three Flight Leader tools (FC, RP, DG) and apply to all three; the heading settings apply to the RP and the DG.")

# Les six étapes du travail type ; {clé} = la lettre de la flèche
S0_STEPS = [
    (1, "Mission Commander, HQ : saisir le Wing une seule fois (noms, escadrons, indicatifs, appareils, logos, tampon, livrées), que le BG, RS, le FC et le DG reprennent ({wing}) ; puis Ouvrir .miz ({dcs_in}), pour que HQ lise les groupes, la date, l’heure et la météo de la mission et les offre au BG, au FC, au RP et au DG ({mission}).",
        "Mission Commander, HQ: enter the Wing once (names, squadrons, call signs, aircraft, logos, stamp, liveries), which the BG, RS, the FC and the DG take up ({wing}); then Open .miz ({dcs_in}), so HQ reads the groups, the date, the time and the weather of the mission and offers them to the BG, the FC, the RP and the DG ({mission})."),
    (2, "Mission Commander, BG puis RS : écrire le briefing (en-tête et escadrons tirés du Wing ; météo, date et heure reprises de la mission d’HQ par l’assistant METAR › Reprendre de la mission d’HQ), puis composer la photo dans RS (logos du Wing proposés ; Msn, DTG et Class préremplis du briefing), l’exporter en PNG et l’ajouter à la main aux Photos du BG ({photo}), pour qu’elle figure dans le briefing imprimé.",
        "Mission Commander, BG then RS: write the briefing (header and squadrons taken from the Wing; weather, date and time taken from the HQ mission through the METAR assistant › Take from HQ mission), then compose the photo in RS (Wing logos offered; Msn, DTG and Class pre-filled from the briefing), export it as a PNG and add it by hand to the BG Photos ({photo}), so it appears in the printed briefing."),
    (3, "Mission Commander : Sauvegarder le fichier de travail ({work}) et le donner aux Flight Leaders, pour qu’ils importent dans le FC, le RP et le DG le briefing (groupes, appareils, nombre d’unités, fréquences du plan radio ; {brief_fl}). Il ne porte ni la mission d’HQ ni le Wing. Le .miz est facultatif pour un Flight Leader : lui donner soit le .miz, qu’il ouvre dans son HQ, soit le paquet exporté d’HQ par Paquets de vol › Exporter ({pack}), qui porte la route, les radios, l’emport et la livrée des groupes cochés. Pour avoir les escadrons du Wing dans son HQ, lui donner aussi le fichier d’Exporter config : sans lui, un vol d’escadron s’importe sous l’identifiant de l’escadron, sans appareil.",
        "Mission Commander: Save the work file ({work}) and give it to the Flight Leaders, so they import into the FC, the RP and the DG the briefing (groups, aircraft, number of units, radio plan frequencies; {brief_fl}). It carries neither the HQ mission nor the Wing. The .miz is optional for a Flight Leader: give them either the .miz, which they open in their HQ, or the package exported from HQ through Flight packages › Export ({pack}), which carries the route, radios, loadout and livery of the ticked groups. For the Wing squadrons in their HQ, also give them the Export config file: without it, a squadron flight is imported under the squadron identifier, without aircraft."),
    (4, "Flight Leader : Ouvrir le fichier de travail (il remplace tout le travail du navigateur) ; le .miz étant facultatif, soit ouvrir dans HQ le .miz fourni par le Mission Commander ({mission}), soit importer son paquet ({pack}) ; puis tracer la route au RP, régler groupes, radios, emport et livrées au FC et composer les datacards au DG : les trois partagent les groupes en direct, de sorte qu’un changement fait dans l’un apparaît dans les autres ({groups}).",
        "Flight Leader: Open the work file (it replaces all the work in the browser); the .miz being optional, either open in HQ the .miz supplied by the Mission Commander ({mission}), or import its package ({pack}); then draw the route in the RP, set up groups, radios, loadout and liveries in the FC and compose the datacards in the DG: the three share the groups live, so a change made in one appears in the others ({groups})."),
    (5, "Flight Leader : au FC, Exporter le paquet de vol (par unité route, radios, emport, livrée) et le rendre au Mission Commander ({fpack}), car rouvrir le fichier de travail d’un Flight Leader remplacerait le travail du Mission Commander au lieu de s’y ajouter.",
        "Flight Leader: in the FC, Export the flight package (per unit route, radios, loadout, livery) and hand it back to the Mission Commander ({fpack}), because reopening a Flight Leader’s work file would replace the Mission Commander’s work instead of adding to it."),
    (6, "Mission Commander : dans HQ, Paquets de vol › Importer des paquets puis Appliquer à la mission (route, radios, emport et livrée de chaque unité dans les groupes de même nom), puis Sauvegarder .miz ({dcs_out}), pour obtenir le .miz final que DCS ouvre.",
        "Mission Commander: in HQ, Flight packages › Import packages then Apply to the mission (route, radios, loadout and livery of each unit in the groups of the same name), then Save .miz ({dcs_out}), to get the final .miz that DCS opens."),
]

# La note du .miz facultatif, dans S0 (large et haute) : {mission} et {pack} = les lettres
NOTE_MIZ_FR = ['Le .miz est facultatif pour un', 'Flight Leader : soit le .miz ({mission}),', 'à ouvrir dans son HQ, soit le', 'paquet exporté d’HQ ({pack}).']
NOTE_MIZ_EN = ['The .miz is optional for a', 'Flight Leader: either the .miz ({mission}),', 'to open in their HQ, or the', 'package exported from HQ ({pack}).']


# ═════════════════════════════════════════════════════════════════════════════════
# S0 · le schéma d'ensemble
# ═════════════════════════════════════════════════════════════════════════════════

# Les noms des modules (monogramme, nom) — les mêmes dans les deux variantes
MODS = {
    'hq': ('HQ', 'Wing Command Center', 'Wing Command Center'),
    'bg': ('BG', 'Briefing Generator', 'Briefing Generator'),
    'rs': ('RS', 'Recon Station', 'Recon Station'),
    'fc': ('FC', 'Flight Configurator', 'Flight Configurator'),
    'rp': ('RP', 'Route Planner', 'Route Planner'),
    'dg': ('DG', 'Datacard Generator', 'Datacard Generator'),
}

# Ce que chaque Flight Leader prend, dans sa case : (ids, [lignes FR], [lignes EN]). Le .miz d'HQ ou le paquet : l'un ou l'autre.
CARDS = {
    'fc': [
        (['S2', 'F5', 'F6'], ['.miz d’HQ ou paquet :', 'groupes, route, radios,', 'emport, livrée'], ['HQ .miz or package:', 'groups, route, radios,', 'loadout, livery']),
        (['S1'], ['Wing : livrées'], ['Wing: liveries']),
        (['S5'], ['briefing : groupes,', 'fréquences radio'], ['briefing: groups,', 'radio frequencies']),
    ],
    'rp': [
        (['S2', 'F5', 'F6'], ['.miz d’HQ ou paquet :', 'groupes, route'], ['HQ .miz or package:', 'groups, route']),
        (['S5'], ['briefing : groupes'], ['briefing: groups']),
    ],
    'dg': [
        (['S2'], ['.miz d’HQ : groupes,', 'date, heure, météo'], ['HQ .miz: groups,', 'date, time, weather']),
        (['F5', 'F6'], ['ou paquet : groupes'], ['or package: groups']),
        (['S1'], ['Wing : indicatifs'], ['Wing: call signs']),
        (['S4', 'S5'], ['briefing : objectif,', 'étapes, équipage,', 'radios, terrains,', 'météo, menaces'], ['briefing: objective,', 'steps, crew, radios,', 'airfields, weather,', 'threats']),
    ],
}

# Ce que les modules du Mission Commander lisent, sous leur nom (le détail est dans la légende)
SUBS = {
    'hq': [('lit : .miz de DCS,', 'reads: DCS .miz,'), ('paquets de vol du FC', 'FC flight packages')],
    'bg': [('lit : Wing, météo, date', 'reads: Wing, weather, date'), ('et heure d’HQ, carte RP,', 'and time from HQ, RP map,'), ('photo RS', 'RS photo')],
    'rs': [('lit : Msn, DTG, Class', 'reads: Msn, DTG, Class'), ('du BG, logos du Wing', 'of the BG, Wing logos')],
}


class _S:
    """Un schéma en construction : les éléments, le marqueur, les ids dessinés, la place du premier badge de chaque flèche."""
    def __init__(self, w, h, marker, aria_fr, aria_en, cls, L):
        self.o = []
        self.w, self.h, self.m, self.cls = w, h, marker, cls
        self.aria = (aria_fr, aria_en)
        self.ids = set()
        self.L = L
        self.pos = {}

    def add(self, s):
        self.o.append('          ' + s)

    def box(self, x, y, w, h, mod=None, dashed=False):
        self.add(sv_box(x, y, w, h, mod, dashed))

    def T(self, x, y, size, fr, en=None, **kw):
        self.add(sv_text(x, y, size, fr, en, **kw))

    def frame(self, x, y, w, h):
        self.add(f'<rect class="sv-frame" x="{_n(x)}" y="{_n(y)}" width="{_n(w)}" height="{_n(h)}" rx="4"/>')

    def ext(self, x, y, w, h, lines, size=10.5):
        """Une boîte hors de la suite (tiretée) ; lines : [(fr, en)] centrées."""
        self.box(x, y, w, h, dashed=True)
        n = len(lines)
        for i, (fr, en) in enumerate(lines):
            self.T(x + w / 2, y + h / 2 + (i - (n - 1) / 2) * (size + 2) + size * .35, size, fr, en)

    def note(self, x, y, w, h, fr_lines, en_lines, size=9.5, step=12):
        """La note du .miz facultatif : une boîte tiretée et ses lignes, FR puis EN."""
        self.box(x, y, w, h, dashed=True)
        for i, (a, b) in enumerate(zip(fr_lines, en_lines)):
            self.T(x + 9, y + 16 + i * step, size, a, b, anchor='start')

    def _at(self, key, x, y):
        p = (y, x)
        if key not in self.pos or p < self.pos[key]:
            self.pos[key] = p

    def arrow(self, key, d, dashed=False, both=False, bd=None):
        """Une flèche : le chemin d, la clé de ses ids, sa lettre (badge) posée en bd=(x, y)."""
        ex = AK[key]
        self.ids.update(ex)
        p = (f'<path d="{d}" fill="none" stroke="currentColor" stroke-width="1.4" opacity=".85"'
             + (' stroke-dasharray="4 3"' if dashed else '') + f' marker-end="url(#{self.m})"'
             + (f' marker-start="url(#{self.m})"' if both else '') + '/>')
        g = f'<g class="sv-ar" data-ex="{" ".join(ex)}">{p}'
        if bd:
            g += self._badge(bd[0], bd[1], key)
        self.add(g + '</g>')

    def badge_only(self, key, x, y):
        ex = AK[key]
        self.ids.update(ex)
        self.add(f'<g class="sv-ar" data-ex="{" ".join(ex)}">{self._badge(x, y, key)}</g>')

    def _badge(self, x, y, key):
        self._at(key, x, y)
        return (f'<rect class="sv-bd" x="{_n(x - 7)}" y="{_n(y - 7)}" width="14" height="14" rx="3"/>'
                + sv_text(x, y + 3.6, 10, self.L.get(key, '?'), extra=' font-weight="700"'))

    def chip(self, x, y, w, fr, en, key):
        """Le jeton « Exemple ▾ » : son texte au centre, sa lettre à droite."""
        self.ids.update(AK[key])
        self.add(f'<g data-ex="{" ".join(AK[key])}"><rect class="sv-chip" x="{_n(x)}" y="{_n(y)}" width="{_n(w)}" height="16" rx="8"/>')
        self.add(self._badge(x + w - 14, y + 8, key) + sv_text(x + w / 2 - 8, y + 11.5, 9.5, fr, en) + '</g>')

    def step(self, x, y, n):
        self.add(f'<circle class="sv-pill" cx="{_n(x)}" cy="{_n(y)}" r="8.5"/>')
        self.T(x, y + 3.6, 10.5, str(n), cls='sv-pill-t', extra=' font-weight="700"')

    def module(self, key, x, y, w, h, card=False, sub=None):
        mono, fr, en = MODS[key]
        self.box(x, y, w, h, key)
        cx = x + w / 2
        self.T(cx, y + 22, 16, mono)
        self.T(cx, y + 38, 10, fr, en)
        if sub:
            for k, (a, b) in enumerate(sub):
                self.T(cx, y + 53 + 11 * k, 9, a, b)
        if card:
            ly = y + 46
            self.add(f'<line x1="{_n(x + 10)}" y1="{_n(ly)}" x2="{_n(x + w - 10)}" y2="{_n(ly)}" stroke="currentColor" stroke-width=".6" opacity=".35"/>')
            yy = ly + 13
            for ex, frs, ens in CARDS[key]:
                self.ids.update(ex)
                g = [f'<g data-ex="{" ".join(ex)}">']
                for a, b in zip(frs, ens):
                    g.append(sv_text(x + 9, yy, 9.5, a, b, anchor='start'))
                    yy += 11.5
                g.append('</g>')
                self.add('\n          '.join(g))
                yy += 3

    def svg(self):
        a_fr, a_en = self.aria
        head = (f'<svg class="{self.cls}" viewBox="0 0 {_n(self.w)} {_n(self.h)}" xmlns="http://www.w3.org/2000/svg" role="img" '
                f'aria-label="{_esc(a_fr)}" data-aria-fr="{_esc(a_fr)}" data-aria-en="{_esc(a_en)}">')
        return '\n'.join([head, '          ' + sv_defs(self.m)] + self.o + ['        </svg>'])


_ARIA = ('Le schéma d’ensemble de la suite : qui reçoit quoi, de qui', 'The suite map: who receives what, from whom')


def build_s0_wide(L):
    s = _S(720, 704, 's0w', _ARIA[0], _ARIA[1], 's0-wide', L)
    A = s.arrow
    cols = (34, 224, 414)
    MW = 156
    MCy, FLy, FLh = 104, 362, 164
    note_fr = [t.format_map(L) for t in NOTE_MIZ_FR]
    note_en = [t.format_map(L) for t in NOTE_MIZ_EN]
    # les cadres, leurs titres (en bas à droite : le haut et la gauche portent des flèches)
    s.frame(8, 62, 588, 184)
    s.T(588, 238, 10.5, 'MISSION COMMANDER', anchor='end', ls=1.5)
    s.frame(8, 340, 588, 284)
    s.T(588, 616, 10.5, 'FLIGHT LEADER', anchor='end', ls=1.5)
    # « Exemple ▾ » : un jeton par cadre
    s.chip(396, 66, 192, 'Exemple ▾ → BG · RS', 'Example ▾ → BG · RS', 'example')
    s.chip(396, 344, 192, 'Exemple ▾ → RP · FC · DG', 'Example ▾ → RP · FC · DG', 'example')
    # les six modules
    s.module('hq', cols[0], MCy, MW, 88, sub=SUBS['hq'])
    s.module('bg', cols[1], MCy, MW, 88, sub=SUBS['bg'])
    s.module('rs', cols[2], MCy, MW, 88, sub=SUBS['rs'])
    s.module('fc', cols[0], FLy, MW, FLh, card=True)
    s.module('rp', cols[1], FLy, MW, FLh, card=True)
    s.module('dg', cols[2], FLy, MW, FLh, card=True)
    # hors de la suite
    s.ext(34, 8, 156, 30, [('DCS', 'DCS')])
    s.ext(252, 8, 160, 30, [('Imprimés · PDF, PNG', 'Printouts · PDF, PNG')], 10)
    s.ext(187, 654, 100, 34, [('CombatFlite', 'CombatFlite'), ('.cf', '.cf')], 10)
    s.ext(307, 654, 100, 34, [('Route Tool', 'Route Tool'), ('.lua', '.lua')], 10)
    s.ext(413, 654, 150, 34, [('Kneeboard · imprimé', 'Kneeboard · printout')], 10)
    # Mission Commander : entrées, sorties
    A('dcs_in', 'M80,38 L80,104', True, bd=(80, 56))
    A('dcs_out', 'M116,104 L116,38', True, bd=(116, 56))
    A('print', 'M330,104 L330,38', True, bd=(330, 56))
    A('wing', 'M160,104 L160,91 L492,91 L492,104', bd=(420, 91))
    A('wing', 'M190,128 L224,128', bd=(207, 128))
    A('brief_rs', 'M380,128 L414,128', bd=(397, 128))
    A('mission', 'M190,158 L224,158', bd=(207, 158))
    A('photo', 'M414,158 L380,158', True, bd=(397, 158))
    # le fichier de travail
    s.ids.add('C2')
    s.add('<g data-ex="C2">')
    s.box(606, 266, 106, 62)
    s.T(659, 286, 10.5, 'Fichier de', 'Work')
    s.T(659, 299, 10.5, 'travail', 'file')
    s.T(659, 318, 9.5, 'hors HQ', 'not HQ')
    s.add('</g>')
    A('work', 'M659,266 L659,205 L598,205', False, both=True, bd=(659, 236))
    A('work', 'M659,328 L659,445 L598,445', False, both=True, bd=(659, 390))
    # du Mission Commander au Flight Leader : le .miz (ou) le paquet
    A('mission', 'M82,192 L82,340', bd=(82, 292))
    A('pack', 'M134,192 L134,340', True, bd=(134, 292))
    A('fpack', 'M180,362 L180,192', True, bd=(180, 292))
    A('brief_fl', 'M262,192 L262,340', bd=(262, 292))
    A('map', 'M342,362 L342,192', bd=(342, 292))
    s.T(0, 0, 9, 'le .miz', 'the .miz', extra=' transform="translate(69 293) rotate(-90)"')
    s.T(0, 0, 9, '(facultatif)', '(optional)', extra=' transform="translate(58 293) rotate(-90)"')
    s.T(0, 0, 9, 'ou le paquet', 'or the package', extra=' transform="translate(121 293) rotate(-90)"')
    s.note(366, 262, 226, 64, note_fr, note_en)
    # le Flight Leader : hors de la suite (les flèches passent derrière la barre)
    A('cf', 'M250,654 L250,526', True, bd=(250, 632))
    A('lua', 'M330,654 L330,526', True, both=True, bd=(330, 632))
    A('knee', 'M450,526 L450,654', True, bd=(450, 632))
    # le Flight Leader : ce qui est partagé, dans les deux sens
    s.ids.update(['S6', 'S10'])
    s.add('<g data-ex="S6 S10">')
    s.box(34, 546, 536, 44)
    s.T(302, 564, 10, 'groupes · unités · radios (fréquences, canaux à imprimer) · emport', 'groups · units · radios (frequencies, channels to print) · loadout')
    s.T(302, 580, 10, 'route copiée · retrait d’un groupe avec sa datacard', 'copied route · removal of a group with its datacard')
    s.add('</g>')
    for cx in (112, 302, 492):
        A('groups', f'M{cx},526 L{cx},546', False, both=True)
    s.badge_only('groups', 70, 546)
    s.badge_only('remove', 160, 546)
    A('routes', 'M224,428 L190,428', bd=(207, 428))
    A('routes', 'M380,428 L414,428', False, both=True, bd=(397, 428))
    A('active', 'M380,456 L414,456', bd=(397, 456))
    # les étapes du travail type
    for (x, y, n) in ((34, 104, 1), (224, 104, 2), (414, 104, 2), (606, 266, 3), (34, 362, 4), (224, 362, 4), (414, 362, 4), (180, 228, 5), (116, 80, 6)):
        s.step(x, y, n)
    return s


def build_s0_tall(L):
    s = _S(320, 1316, 's0t', _ARIA[0], _ARIA[1], 's0-tall', L)
    A = s.arrow
    mx, mw = 80, 160
    HQy, BGy, RSy = 92, 210, 328
    FCy, RPy, DGy, FLh = 626, 834, 1042, 164
    EXy = 1256
    note_fr = [t.format_map(L) for t in NOTE_MIZ_FR]
    note_en = [t.format_map(L) for t in NOTE_MIZ_EN]
    s.frame(4, 52, 312, 376)
    s.frame(4, 520, 312, 704)
    # les titres et le jeton de l'exemple, en tête de cadre
    s.T(30, 66, 10.5, 'MISSION COMMANDER', anchor='start', ls=1.5)
    s.T(84, 534, 10.5, 'FLIGHT LEADER', anchor='start', ls=1.5)
    s.ids.add('C3')
    s.add('<g data-ex="C3">' + sv_text(30, 80, 9.5, 'Exemple ▾ → BG · RS', 'Example ▾ → BG · RS', anchor='start') + s._badge(160, 77, 'example') + '</g>')
    s.add('<g data-ex="C3">' + sv_text(84, 548, 9.5, 'Exemple ▾ → RP · FC · DG', 'Example ▾ → RP · FC · DG', anchor='start') + s._badge(240, 545, 'example') + '</g>')
    s.note(84, 556, 224, 58, note_fr, note_en)
    s.module('hq', mx, HQy, mw, 88, sub=SUBS['hq'])
    s.module('bg', mx, BGy, mw, 88, sub=SUBS['bg'])
    s.module('rs', mx, RSy, mw, 88, sub=SUBS['rs'])
    s.module('fc', mx, FCy, mw, FLh, card=True)
    s.module('rp', mx, RPy, mw, FLh, card=True)
    s.module('dg', mx, DGy, mw, FLh, card=True)
    s.ext(160, 6, 152, 30, [('DCS', 'DCS')])
    s.ext(8, 6, 124, 30, [('Imprimés', 'Printouts')], 10)
    s.ext(8, EXy, 96, 40, [('CombatFlite', 'CombatFlite'), ('.cf', '.cf')], 10)
    s.ext(112, EXy, 96, 40, [('Route Tool', 'Route Tool'), ('.lua', '.lua')], 10)
    s.ext(216, EXy, 96, 40, [('Kneeboard', 'Kneeboard'), ('imprimé', 'printout')], 10)
    # Mission Commander : entrées et sorties
    A('dcs_in', f'M185,36 L185,{HQy}', True, bd=(185, 60))
    A('dcs_out', f'M213,{HQy} L213,36', True, bd=(213, 60))
    A('print', f'M{mx},{BGy + 20} L20,{BGy + 20} L20,36', True, bd=(20, 120))
    A('wing', f'M{mx + 30},{HQy + 88} L{mx + 30},{BGy}', bd=(mx + 30, 195))
    A('mission', f'M{mx + 75},{HQy + 88} L{mx + 75},{BGy}', bd=(mx + 75, 195))
    A('wing', f'M{mx + mw},{HQy + 36} L286,{HQy + 36} L286,{RSy + 30} L{mx + mw},{RSy + 30}', bd=(286, 250))
    A('brief_rs', f'M{mx + 30},{BGy + 88} L{mx + 30},{RSy}', bd=(mx + 30, 313))
    A('photo', f'M{mx + 110},{RSy} L{mx + 110},{BGy + 88}', True, bd=(mx + 110, 313))
    # du Mission Commander au Flight Leader : le côté gauche (le .miz ou le paquet)
    A('mission', f'M{mx},{HQy + 14} L30,{HQy + 14} L30,520', bd=(30, 470))
    A('pack', f'M{mx},{HQy + 24} L46,{HQy + 24} L46,520', True, bd=(46, 455))
    A('fpack', f'M{mx},{FCy + 40} L62,{FCy + 40} L62,{HQy + 36} L{mx},{HQy + 36}', True, bd=(62, 440))
    A('brief_fl', f'M{mx},{BGy + 46} L76,{BGy + 46} L76,520', bd=(76, 485))
    # l'image de carte : le côté droit
    A('map', f'M{mx + mw},{RPy + 30} L250,{RPy + 30} L250,{BGy + 36} L{mx + mw},{BGy + 36}', bd=(250, 420))
    # le fichier de travail
    s.ids.add('C2')
    s.add('<g data-ex="C2">')
    s.box(mx + 16, 446, mw - 16, 46)
    s.T(mx + 16 + (mw - 16) / 2, 464, 10.5, 'Fichier de travail', 'Work file')
    s.T(mx + 16 + (mw - 16) / 2, 481, 9.5, 'hors HQ', 'not HQ')
    s.add('</g>')
    A('work', f'M{mx + 100},446 L{mx + 100},428', False, both=True, bd=(mx + 124, 437))
    A('work', f'M{mx + 100},492 L{mx + 100},520', False, both=True, bd=(mx + 124, 506))
    # le Flight Leader : hors de la suite (les flèches passent derrière la barre ou les modules, jamais dessus)
    A('cf', f'M56,{EXy} L56,{EXy - 18} L274,{EXy - 18} L274,{RPy + 90} L{mx + mw},{RPy + 90}', True, bd=(110, EXy - 18))
    A('lua', f'M160,{EXy} L160,{EXy - 10} L262,{EXy - 10} L262,{RPy + 60} L{mx + mw},{RPy + 60}', True, both=True, bd=(212, EXy - 10))
    A('knee', f'M{mx + mw},{DGy + 80} L288,{DGy + 80} L288,{EXy}', True, bd=(288, EXy - 40))
    # le Flight Leader : ce qui est partagé, dans les deux sens (la barre à gauche, tournée)
    s.ids.update(['S6', 'S10'])
    s.add('<g data-ex="S6 S10">')
    s.add('<rect class="sv-box" x="14" y="640" width="22" height="544" rx="3" stroke="currentColor" stroke-width="1.4"/>')
    s.add(sv_text(0, 0, 10, 'groupes · unités · radios · emport · route copiée · retrait d’un groupe',
                  'groups · units · radios · loadout · copied route · removal of a group', extra=' transform="translate(29 912) rotate(-90)"'))
    s.add('</g>')
    for ty in (FCy + 80, RPy + 20, DGy + 80):
        A('groups', f'M{mx},{ty} L36,{ty}', False, both=True)
    s.badge_only('groups', 25, 626)
    s.badge_only('remove', 47, 626)
    A('routes', f'M{mx + 110},{RPy} L{mx + 110},{FCy + FLh}', bd=(mx + 110, RPy - 22))
    A('routes', f'M{mx + 110},{RPy + FLh} L{mx + 110},{DGy}', False, both=True, bd=(mx + 110, DGy - 22))
    s.badge_only('active', mx + 127, DGy - 22)
    for (x, y, n) in ((mx, HQy, 1), (mx, BGy, 2), (mx, RSy, 2), (mx + 16, 446, 3), (mx, FCy, 4), (mx, RPy, 4), (mx, DGy, 4), (62, 400, 5), (238, 78, 6)):
        s.step(x, y, n)
    return s


def letters():
    """La lettre de chaque flèche : l'ordre de lecture de la variante large, de haut en bas puis de gauche à droite (la première lettre à
    la place du premier badge). La légende suit l'ordre alphabétique."""
    first = build_s0_wide(collections.defaultdict(lambda: "?"))
    missing = [k for k in AK if k not in first.pos]
    assert not missing, ('S0 : flèches sans badge', missing)
    order = [k for k, _ in sorted(first.pos.items(), key=lambda kv: kv[1])]
    return {k: chr(97 + i) for i, k in enumerate(order)}


def s0_legend_html(L):
    """La légende lettrée de S0 (dans l'ordre alphabétique, une ligne par outil récepteur), les réglages, puis les six étapes."""
    out = {}
    for lang, i_head, i_subs in (('fr', 0, 1), ('en', 2, 3)):
        T = fr_typo if lang == 'fr' else (lambda x: x)
        items = []
        for key in sorted(AK, key=lambda k: L[k]):
            e = S0_LEGEND[key]
            head, subs = e[i_head], e[i_subs]
            ids = ' '.join(AK[key])
            sub = ''
            if subs:
                sub = '<ul class="xsub">' + ''.join(f'<li><strong>{_esc(T(tool))}</strong> {_esc(T(txt))}</li>' for tool, txt in subs) + '</ul>'
            items.append(f'<li data-ex="{ids}"><span class="xb">{L[key]}</span> {_esc(T(head))}{sub}</li>')
        steps = ''.join(f'<li><span class="xs">{n}</span> {_esc(T((fr if lang == "fr" else en).format_map(L)))}</li>' for n, fr, en in S0_STEPS)
        out[lang] = (''.join(items), steps, T(S0_SETTINGS[0 if lang == 'fr' else 1]))
    li_fr, st_fr, se_fr = out['fr']
    li_en, st_en, se_en = out['en']
    return (f'<div class="fm-xlegend">'
            f'<div class="lang-block" data-lang="fr"><h4>Les flèches</h4><p class="fm-xkey">Trait plein{NF}: en direct, dans la suite. Tireté{NF}: par un fichier ou à la main.</p><ul>{li_fr}</ul>'
            f'<p class="fm-xset">{_esc(se_fr)}</p>'
            f'<h4>Le travail, dans l’ordre</h4><ul>{st_fr}</ul></div>'
            f'<div class="lang-block" data-lang="en"><h4>The arrows</h4><p class="fm-xkey">Solid line: live, inside the suite. Dashed: by a file or by hand.</p><ul>{li_en}</ul>'
            f'<p class="fm-xset">{_esc(se_en)}</p>'
            f'<h4>The work, in order</h4><ul>{st_en}</ul></div></div>')


def s0_html():
    L = letters()
    w, t = build_s0_wide(L), build_s0_tall(L)
    assert w.ids == t.ids, ('S0 : les deux variantes ne portent pas les mêmes ids', sorted(w.ids ^ t.ids))
    assert w.pos.keys() == t.pos.keys() == set(AK), ('S0 : les deux variantes ne portent pas les mêmes flèches lettrées', sorted(set(AK) ^ set(t.pos)))
    missing = [i for i in TABLE_IDS if i not in w.ids and i not in NOT_DRAWN]
    assert not missing, ('S0 : ids de la table non dessinés', missing)
    assert set(L.values()) == set(chr(97 + i) for i in range(len(AK))) and len(L) == len(AK) == len(S0_LEGEND), 'S0 : une lettre par flèche, une ligne de légende par lettre'
    cap_fr = 'Fig. 1 — La suite d’un coup d’œil : ce que chaque outil prend et donne, dans son sens, avec le travail sauvegardé et rechargé.'
    cap_en = 'Fig. 1 — The suite at a glance: what each tool takes and gives, in its direction, with the work saved and reloaded.'
    return (f'<div class="fm-schema fm-s0">\n        {w.svg()}\n        {t.svg()}\n'
            f'        <div class="fm-schema-legend">\n'
            f'          <span class="lang-block" data-lang="fr">{cap_fr}</span>\n'
            f'          <span class="lang-block" data-lang="en">{cap_en}</span>\n'
            f'        </div>\n      </div>\n' + s0_legend_html(L)), w.ids


# ═════════════════════════════════════════════════════════════════════════════════
# Les six panneaux « Reçoit · Donne »
# ═════════════════════════════════════════════════════════════════════════════════
# Une ligne : (ids, FR, EN) ; FR et EN = (ce qui passe, de / vers quel outil, par quel geste, pour quoi faire)
_SHEET_FR = "Groupes, unités (type, indicatif, numéro de bord, livrée), radios (fréquences, canaux à imprimer), emport, route copiée"
_SHEET_EN = "Groups, units (type, call sign, tail number, livery), radios (frequencies, channels to print), loadout, copied route"

def _share(tool):
    """La ligne commune des trois outils du Flight Leader, vue de l'outil `tool` (les réglages n'en sont pas : ce ne sont pas des échanges)."""
    others = {'fc': ('RP, DG', 'RP, DG'), 'rp': ('FC, DG', 'FC, DG'), 'dg': ('FC, RP', 'FC, RP')}[tool]
    return [
        (['S6'], (_SHEET_FR, others[0], 'sans geste, dans les deux sens', 'pour que ce que l’un règle se voie dans les autres'),
                 (_SHEET_EN, others[1], 'no gesture, both ways', 'so what one sets shows in the others')),
    ]

_WORK_IN_FR = ('Le travail rangé : fichier de travail, exemple', 'la suite', 'Ouvrir ▾ › Ouvrir un travail…, Exemple ▾', 'pour reprendre ou démarrer le travail, qui remplace le précédent')
_WORK_IN_EN = ('Stored work: work file, example', 'the suite', 'Open ▾ › Open a work file…, Example ▾', 'to resume or start the work, which replaces the previous one')

# Le fichier de travail, côté Flight Leader : ce qu'il y met sert à reprendre son travail ou à le passer à un autre Flight Leader (il ne revient pas au Mission Commander)
def _work_out_fl(fr_what, en_what, extra_fr='', extra_en=''):
    return (['C2'], (fr_what, 'le fichier de travail', 'Sauvegarder', 'pour reprendre son travail plus tard, ou le passer à un autre Flight Leader' + extra_fr),
                    (en_what, 'the work file', 'Save', 'to resume your work later, or pass it on to another Flight Leader' + extra_en))

# Le paquet de vol exporté d'HQ : l'autre voie du Flight Leader, sans le .miz
def _pack_in(tool):
    who = {'fc': ('HQ, un autre FC, BG', 'HQ, another FC, BG', 'Importer des groupes… › Fichier', 'Import groups… › File'),
           'rp': ('HQ, FC, BG', 'HQ, FC, BG', 'Importer des routes… › Fichier', 'Import routes… › File'),
           'dg': ('HQ, FC', 'HQ, FC', 'menu … des cartes › Importer des groupes › Fichier', 'cards … menu › Import groups › File')}[tool]
    if tool == 'dg':
        what = ('Ou, sans .miz : un paquet .json ou .zip exporté d’HQ : groupes avec route, radios, emport, livrée', 'Or, without the .miz: a package .json or .zip exported from HQ: groups with route, radios, loadout, livery')
        why = ('pour créer les cartes sans la mission chargée', 'to create the cards without the mission loaded')
    else:
        what = ('Ou, sans .miz : un paquet exporté d’HQ (ou un briefing .json ou .zip) : mêmes données qu’en source HQ ou BG', 'Or, without the .miz: a package exported from HQ (or a briefing .json or .zip): same data as from the HQ or BG source')
        why = ('pour importer sans la mission chargée dans HQ : le .miz est facultatif', 'to import without the mission loaded in HQ: the .miz is optional')
    return (['F5', 'F6'], (what[0], who[0], who[2], why[0]), (what[1], who[1], who[3], why[1]))

PANELS = {
    'hq': {
        'in': [
            (['F1'], ('Le .miz d’origine : groupes Client (nom, coalition, unités, route, radios, emport, livrée), date, heure de départ, météo', 'DCS', 'Ouvrir .miz, ou le déposer sur la page', 'pour les montrer, les modifier et les offrir au BG, au FC, au RP et au DG'),
                     ('The original .miz: Client groups (name, coalition, units, route, radios, loadout, livery), date, start time, weather', 'DCS', 'Open .miz, or drop it on the page', 'to show them, edit them and offer them to the BG, the FC, the RP and the DG')),
            (['F4'], ('Un paquet de vol : par unité, route, radios, emport, livrée', 'le FC', 'Paquets de vol › Importer des paquets, puis Appliquer à la mission', 'pour écrire les parties cochées dans les groupes du .miz de même nom'),
                     ('A flight package: per unit, route, radios, loadout, livery', 'the FC', 'Flight packages › Import packages, then Apply to the mission', 'to write the ticked parts into the .miz groups of the same name')),
            (['F7'], ('Une configuration Wing : identité, tampon, logos, escadrons, livrées', 'un autre HQ', 'Wing › Importer config', 'pour remplir la fenêtre Wing sans la ressaisir'),
                     ('A Wing configuration: identity, stamp, logos, squadrons, liveries', 'another HQ', 'Wing › Import config', 'to fill the Wing window without typing it again')),
        ],
        'out': [
            (['S1'], ('Le Wing : logo et nom court, tampon, escadrons (indicatif, appareils, logo), livrées ajoutées et livrée par défaut', 'BG, RS, DG, FC et la barre de chaque outil', 'sans geste, à chaque saisie de la fenêtre Wing', 'pour l’en-tête et les pages du briefing, les logos de la photo, les indicatifs des cartes, les listes de livrées et le nom court des barres'),
                     ('The Wing: logo and short name, stamp, squadrons (call sign, aircraft, logo), added liveries and default livery', 'BG, RS, DG, FC and each tool bar', 'no gesture, at every Wing window entry', 'for the briefing header and pages, the photo logos, the cards’ call signs, the livery lists and the bars’ short name')),
            (['S2'], ('La mission ouverte : groupes Client (nom, coalition, unités, route, radios, emport, livrée), date, heure de départ, météo', 'BG, FC, RP, DG', 'sans geste, jusqu’à Effacer ou la fermeture de la page', 'pour la météo, la date et l’heure du BG, la fenêtre d’import du FC, du RP et du DG, la livrée par défaut du FC, la date, l’heure et la météo des cartes du DG'),
                     ('The open mission: Client groups (name, coalition, units, route, radios, loadout, livery), date, start time, weather', 'BG, FC, RP, DG', 'no gesture, until Clear or the page is closed', 'for the BG weather, date and time, the import window of the FC, the RP and the DG, the FC default livery, the date, time and weather of the DG cards')),
            (['F5', 'F6'], ('Un paquet des groupes cochés : Route, Radios, Emport, Livrée', 'FC, RP, DG, un autre HQ', 'Paquets de vol › Exporter, puis leur fenêtre d’import › Fichier', 'pour qu’un Flight Leader travaille sans le .miz : il est facultatif'),
                           ('A package of the ticked groups: Route, Radios, Loadout, Livery', 'FC, RP, DG, another HQ', 'Flight packages › Export, then their import window › File', 'so a Flight Leader can work without the .miz: it is optional')),
            (['F7'], ('La configuration Wing', 'un autre HQ', 'Wing › Exporter config', 'pour qu’un autre HQ ait le même Wing : un Flight Leader n’a pas le Wing dans le fichier de travail'),
                     ('The Wing configuration', 'another HQ', 'Wing › Export config', 'so another HQ has the same Wing: a Flight Leader does not get the Wing in the work file')),
            (['F3'], ('Le .miz final', 'DCS', 'Sauvegarder .miz', 'pour que DCS ouvre la mission avec les paquets appliqués'),
                     ('The final .miz', 'DCS', 'Save .miz', 'so DCS opens the mission with the packages applied')),
        ],
    },
    'bg': {
        'in': [
            (['S1'], ('Le Wing : logo wing principal, nom court, tampon HQ, escadrons (identifiant, indicatif, appareils, logo) ; en lecture seule, nom complet et identifiant', 'HQ', 'sans geste', 'pour l’en-tête de chaque page, le cachet de la couverture, la liste Escadron et le logo de la page de chaque vol'),
                     ('The Wing: main wing logo, short name, HQ stamp, squadrons (identifier, call sign, aircraft, logo); read-only, full name and identifier', 'HQ', 'no gesture', 'for every page header, the cover stamp, the Squadron list and the logo of each flight page')),
            (['S2'], ('La météo, la date et l’heure de la mission ouverte dans HQ ; la ligne sous la barre dit quel .miz est chargé', 'HQ', 'assistant METAR › Reprendre de la mission d’HQ (grisé sans mission), puis Insérer dans METAR', 'pour remplir l’assistant et obtenir le METAR du briefing, et pour la date et l’heure de son en-tête'),
                     ('The weather, date and time of the mission open in HQ; the line under the bar says which .miz is loaded', 'HQ', 'METAR assistant › Take from HQ mission (greyed out without a mission), then Insert into METAR', 'to fill the assistant and get the briefing METAR, and for the date and time of its header')),
            (['C1'], ('L’image de la carte : cadrée, avec échelle, nord et cartouche', 'RP, dans la même session', 'RP : Exporter ▾ › Image pour le briefing…, puis BG : Placer', 'pour la carte du briefing : page Carte ou photos au Standard ; SITAC, couverture, documents d’une mission ou annexe à l’Avancé'),
                     ('The map image: framed, with scale, north and cartouche', 'RP, in the same session', 'RP: Export ▾ › Image for the briefing…, then BG: Place', 'for the briefing map: Map or photo pages in Standard; SITAC, cover, a mission’s documents or annex in Advanced')),
            (['F8'], ('La photo composée : un PNG', 'RS', 'RS : Exporter, puis BG : Photos › ajouter l’image, à la main', 'pour les pages de photos du briefing'),
                     ('The composed photo: a PNG', 'RS', 'RS: Export, then BG: Photos › add the image, by hand', 'for the photo pages of the briefing')),
            (['F13'], ('Un ancien briefing .json', 'un fichier', 'Ouvrir ▾ › Ouvrir un briefing…', 'pour reprendre un briefing déjà écrit'),
                      ('An old briefing .json', 'a file', 'Open ▾ › Open a briefing…', 'to resume a briefing already written')),
            (['C2', 'C3'], _WORK_IN_FR, _WORK_IN_EN),
        ],
        'out': [
            (['S3'], ('Opération et mission, date du briefing, classification', 'RS', 'sans geste, à l’ouverture de RS', 'pour préremplir Msn, DTG et Class de la photo, champs vides seulement'),
                     ('Operation and mission, briefing date, classification', 'RS', 'no gesture, when RS opens', 'to pre-fill the photo’s Msn, DTG and Class, empty fields only')),
            (['S4'], ('Le briefing : opération, mission, date, heure, classification, tâche et menace de chaque vol, objectif, étapes, équipage, radios, terrains avec piste, METAR, menaces SAM et AAA, notes', 'DG', 'DG : Ouvrir ▾ › Importer… › Briefing en cours', 'pour préremplir une carte par vol'),
                     ('The briefing: operation, mission, date, time, classification, each flight’s task and threat, objective, steps, crew, radios, airfields with runway, METAR, SAM and AAA threats, notes', 'DG', 'DG: Open ▾ › Import… › Current briefing', 'to pre-fill one card per flight')),
            (['S5'], ('Les vols : indicatif, appareil, nombre d’unités, plan radio (Standard : fréquences de la liste ; Avancé : plan de chaque appareil)', 'FC, RP, DG', 'leur fenêtre d’import › Briefing en cours', 'pour créer les groupes et poser les fréquences sur les postes radio'),
                     ('The flights: call sign, aircraft, number of units, radio plan (Standard: frequencies of the list; Advanced: each aircraft’s plan)', 'FC, RP, DG', 'their import window › Current briefing', 'to create the groups and put the frequencies on the radio posts')),
            (['F11'], ('Le briefing : un PDF, ou un PNG par page', 'l’imprimé', 'Exporter', 'pour le distribuer ou l’imprimer'),
                      ('The briefing: a PDF, or one PNG per page', 'the printout', 'Export', 'to hand it out or print it')),
            (['C2'], ('Le briefing', 'le fichier de travail', 'Sauvegarder', 'pour le reprendre plus tard et le donner aux Flight Leaders, qui en importent les groupes et les fréquences radio'),
                     ('The briefing', 'the work file', 'Save', 'to resume it later and give it to the Flight Leaders, who import its groups and radio frequencies')),
        ],
    },
    'rs': {
        'in': [
            (['S3'], ('Msn (opération et mission), DTG (date), Class (classification)', 'BG', 'sans geste, à l’ouverture de RS, champs vides seulement', 'pour ne pas les ressaisir sur la photo'),
                     ('Msn (operation and mission), DTG (date), Class (classification)', 'BG', 'no gesture, when RS opens, empty fields only', 'so they need not be typed again on the photo')),
            (['S1'], ('Le logo wing principal et le logo de chaque escadron', 'HQ, fenêtre Wing', 'sans geste', 'pour les proposer dans la grille Logo de la photo, marqués Wing ; les logos ajoutés à la main restent'),
                     ('The main wing logo and each squadron’s logo', 'HQ, Wing window', 'no gesture', 'to offer them in the photo’s Logo grid, marked Wing; the logos added by hand stay')),
            (['C2', 'C3'], ('Le travail rangé : fichier de travail, exemple', 'la suite', 'Ouvrir, Exemple', 'pour reprendre ou démarrer le travail, qui remplace le précédent'),
                           ('Stored work: work file, example', 'the suite', 'Open, Example', 'to resume or start the work, which replaces the previous one')),
        ],
        'out': [
            (['F8'], ('La photo composée : un PNG', 'BG', 'Exporter, puis dans le BG Photos › ajouter l’image, à la main', 'pour les pages de photos du briefing'),
                     ('The composed photo: a PNG', 'BG', 'Export, then in the BG Photos › add the image, by hand', 'for the photo pages of the briefing')),
            (['C2'], ('La composition, sans l’image source, avec le logo du Wing posé sur la photo', 'le fichier de travail', 'Sauvegarder', 'pour reprendre la photo plus tard sans le poids de la capture'),
                     ('The composition, without the source image, with the Wing logo placed on the photo', 'the work file', 'Save', 'to resume the photo later without the weight of the capture')),
        ],
    },
    'fc': {
        'in': [
            (['S2'], ('Avec le .miz ouvert dans HQ : les groupes de la mission : nom, coalition, unités (type, indicatif, numéro de bord) et, à cocher, Route, Radios, Emport, Livrée', 'HQ', 'Importer des groupes… › Mission chargée dans HQ', 'pour créer ou compléter les groupes à régler'),
                     ('With the .miz open in HQ: the groups of the mission: name, coalition, units (type, call sign, tail number) and, to tick, Route, Radios, Loadout, Livery', 'HQ', 'Import groups… › Mission loaded in HQ', 'to create or complete the groups to set up')),
            (['S2'], ('Avec le .miz : la livrée de chaque unité dans la mission', 'HQ', 'sans geste', 'pour présélectionner la livrée tant que vous n’en choisissez pas'),
                     ('With the .miz: the livery of each unit in the mission', 'HQ', 'no gesture', 'to preselect the livery until you choose one')),
            _pack_in('fc'),
            (['S1'], ('Les livrées ajoutées (nom, appareils) et la livrée par défaut de chaque appareil', 'HQ, fenêtre Wing', 'sans geste', 'pour la liste Livrée de chaque unité'),
                     ('The added liveries (name, aircraft) and each aircraft’s default livery', 'HQ, Wing window', 'no gesture', 'for each unit’s Livery list')),
            (['S5'], ('Les vols du briefing : indicatif, appareil, nombre d’unités, fréquences du plan radio', 'BG', 'Importer des groupes… › Briefing en cours', 'pour créer les groupes et régler leurs radios'),
                     ('The briefing flights: call sign, aircraft, number of units, radio plan frequencies', 'BG', 'Import groups… › Current briefing', 'to create the groups and set their radios')),
            (['S8'], ('Les routes : points', 'RP', 'sans geste, puis Changer de route', 'pour copier la route dans le groupe'),
                     ('The routes: points', 'RP', 'no gesture, then Change route', 'to copy the route into the group')),
            (['F13'], ('Une ancienne configuration', 'un fichier', 'Ouvrir ▾ › Ouvrir une configuration…', 'pour reprendre une configuration déjà faite'),
                      ('An old configuration', 'a file', 'Open ▾ › Open a configuration…', 'to resume a configuration already made')),
            (['C2', 'C3'], _WORK_IN_FR, _WORK_IN_EN),
        ] + _share('fc'),
        'out': [
            (['F4'], ('Le paquet de vol : groupes avec, par unité, route, radios, emport, livrée', 'HQ', 'Exporter, puis dans HQ Paquets de vol', 'pour écrire ces parties dans le .miz : c’est le seul retour au Mission Commander'),
                     ('The flight package: groups with, per unit, route, radios, loadout, livery', 'HQ', 'Export, then in HQ Flight packages', 'to write these parts into the .miz: it is the only return to the Mission Commander')),
            (['S10'], ('Le retrait d’un groupe', 'RP, DG', 'Retirer ce groupe', 'pour le retirer de tous les outils, avec sa datacard'),
                     ('The removal of a group', 'RP, DG', 'Remove this group', 'to remove it from all tools, with its datacard')),
            _work_out_fl('Les groupes', 'The groups'),
        ] + _share('fc'),
    },
    'rp': {
        'in': [
            (['S2'], ('Avec le .miz ouvert dans HQ : les groupes de la mission avec leur route', 'HQ', 'Importer des routes… › Mission chargée dans HQ', 'pour partir des routes de la mission'),
                     ('With the .miz open in HQ: the mission groups with their route', 'HQ', 'Import routes… › Mission loaded in HQ', 'to start from the mission routes')),
            _pack_in('rp'),
            (['S5'], ('Les vols du briefing : indicatif, appareil, nombre d’unités', 'BG', 'Importer des routes… › Briefing en cours', 'pour créer les groupes auxquels rattacher les routes'),
                     ('The briefing flights: call sign, aircraft, number of units', 'BG', 'Import routes… › Current briefing', 'to create the groups to attach the routes to')),
            (['F9'], ('Les points d’une route, 30 au plus', 'le Route Tool de DCS, fichier <théâtre>.lua', 'Ouvrir ▾ › Ouvrir une route…', 'pour reprendre une route faite en jeu'),
                     ('The points of a route, 30 at most', 'the DCS Route Tool, <theatre>.lua file', 'Open ▾ › Open a route…', 'to take back a route made in game')),
            (['F10'], ('Les calques : zones, cercles, points, orbites, boîtes, textes, symboles', 'CombatFlite, fichier .cf', 'Ouvrir ▾ › Ouvrir une route…, puis Afficher', 'pour les voir en lecture seule sur la carte'),
                      ('The layers: zones, circles, points, orbits, boxes, texts, symbols', 'CombatFlite, .cf file', 'Open ▾ › Open a route…, then Show', 'to see them read-only on the map')),
            (['F13'], ('Une ancienne route', 'un fichier', 'Ouvrir ▾ › Ouvrir une route…', 'pour reprendre une route déjà tracée'),
                      ('An old route', 'a file', 'Open ▾ › Open a route…', 'to resume a route already drawn')),
            (['C2', 'C3'], _WORK_IN_FR, _WORK_IN_EN),
        ] + _share('rp'),
        'out': [
            (['C1'], ('L’image de la carte : cadrée, avec échelle, nord et cartouche', 'BG, dans la même session', 'Exporter ▾ › Image pour le briefing… › Exporter', 'pour la carte du briefing'),
                     ('The map image: framed, with scale, north and cartouche', 'BG, in the same session', 'Export ▾ › Image for the briefing… › Export', 'for the briefing map')),
            (['S8'], ('Les routes : points', 'FC, DG', 'sans geste', 'pour la route copiée du groupe et le tableau Navigation de la carte'),
                     ('The routes: points', 'FC, DG', 'no gesture', 'for the group’s copied route and the card’s Navigation table')),
            (['S9'], ('La route active et les points de référence', 'DG', 'sans geste', 'pour la route active de la carte et ses références'),
                     ('The active route and the reference points', 'DG', 'no gesture', 'for the card’s active route and its references')),
            (['F9'], ('Les points d’une route', 'le Route Tool de DCS', 'Exporter ▾ › Route Tool…', 'pour donner la route au Route Tool, sans les points de référence'),
                     ('The points of a route', 'the DCS Route Tool', 'Export ▾ › Route Tool…', 'to give the route to the Route Tool, without reference points')),
            _work_out_fl('Les routes et leurs calques', 'The routes and their layers'),
        ] + _share('rp'),
    },
    'dg': {
        'in': [
            (['S2'], ('Avec le .miz ouvert dans HQ : les groupes de la mission, la date, l’heure de départ, la météo (METAR décodé)', 'HQ', 'menu … des cartes › Importer des groupes › Mission chargée dans HQ', 'pour créer les cartes et remplir leur date, leur heure et leur météo'),
                     ('With the .miz open in HQ: the mission groups, the date, the start time, the weather (decoded METAR)', 'HQ', 'cards … menu › Import groups › Mission loaded in HQ', 'to create the cards and fill their date, time and weather')),
            _pack_in('dg'),
            (['S1'], ('L’indicatif et le premier appareil de chaque escadron', 'HQ, fenêtre Wing', 'sans geste', 'pour nommer la carte d’un vol du briefing qui porte un escadron'),
                     ('Each squadron’s call sign and first aircraft', 'HQ, Wing window', 'no gesture', 'to name the card of a briefing flight that has a squadron')),
            (['S4', 'S5'], ('Le briefing : opération, mission, date, heure, classification, tâche et menace de chaque vol, objectif, étapes, équipage, radios, terrains avec piste, METAR, menaces SAM et AAA, notes', 'BG', 'Ouvrir ▾ › Importer… › Briefing en cours', 'pour préremplir une carte par vol'),
                           ('The briefing: operation, mission, date, time, classification, each flight’s task and threat, objective, steps, crew, radios, airfields with runway, METAR, SAM and AAA threats, notes', 'BG', 'Open ▾ › Import… › Current briefing', 'to pre-fill one card per flight')),
            (['S8'], ('Les routes : points', 'RP', 'sans geste', 'pour le tableau Navigation de chaque carte'),
                     ('The routes: points', 'RP', 'no gesture', 'for each card’s Navigation table')),
            (['S9'], ('La route active et les points de référence', 'RP', 'sans geste', 'pour la route active de la carte et ses références'),
                     ('The active route and the reference points', 'RP', 'no gesture', 'for the card’s active route and its references')),
            (['F13'], ('Une ancienne datacard', 'un fichier', 'Ouvrir ▾ › Ouvrir une datacard…', 'pour reprendre une carte déjà faite'),
                      ('An old datacard', 'a file', 'Open ▾ › Open a datacard…', 'to resume a card already made')),
            (['S10'], ('Le retrait d’un groupe', 'FC', 'Retirer ce groupe', 'pour retirer aussi sa datacard'),
                      ('The removal of a group', 'FC', 'Remove this group', 'to remove its datacard too')),
            (['C2', 'C3'], _WORK_IN_FR, _WORK_IN_EN),
        ] + _share('dg'),
        'out': [
            (['F12'], ('Les datacards : un PNG par page, un ZIP s’il y en a plusieurs, ou un PDF', 'le kneeboard de DCS, l’imprimé', 'Exporter', 'pour les lire en vol ou les imprimer'),
                      ('The datacards: one PNG per page, a ZIP if there are several, or a PDF', 'the DCS kneeboard, the printout', 'Export', 'to read them in flight or print them')),
            (['S8'], ('Une navigation modifiée : un point déplacé, ajouté ou retiré', 'RP, FC', 'sans geste, dans le tableau Navigation', 'pour que la route du RP et la copie du groupe suivent la carte'),
                     ('A modified navigation: a point moved, added or removed', 'RP, FC', 'no gesture, in the Navigation table', 'so the RP route and the group copy follow the card')),
            (['S10'], ('Le retrait d’une datacard et de son groupe', 'FC, RP', 'Supprimer la datacard et le groupe', 'pour retirer le groupe de tous les outils'),
                      ('The removal of a datacard and its group', 'FC, RP', 'Delete the datacard and the group', 'to remove the group from all tools')),
            _work_out_fl('Les datacards', 'The datacards'),
        ] + _share('dg'),
    },
}


def panel_html(tool):
    p = PANELS[tool]

    out = []
    for lang, h_in, h_out in (('fr', 'Reçoit', 'Donne'), ('en', 'Receives', 'Gives')):
        i = 0 if lang == 'fr' else 1
        T = fr_typo if lang == 'fr' else (lambda x: x)
        cols = []
        for key, head in (('in', h_in), ('out', h_out)):
            li = ''.join(
                f'<li data-ex="{" ".join(r[0])}"><strong>{_esc(T(r[1][i][0]))}</strong> — {_esc(T(r[1][i][1]))} — <span class="rd-g">{_esc(T(r[1][i][2]))}</span> — {_esc(T(r[1][i][3]))}</li>'
                for r in ((row[0], (row[1], row[2])) for row in p[key]))
            cols.append(f'<div class="fm-rd-col"><h4>{head}</h4><ul>{li}</ul></div>')
        out.append(f'<div class="fm-rd lang-block" data-lang="{lang}" data-tool="{tool}">{"".join(cols)}</div>')
    return '\n      '.join(out)


def panel_ids():
    ids = set()
    for p in PANELS.values():
        for k in ('in', 'out'):
            for row in p[k]:
                ids.update(row[0])
    return ids


# Les ids de la table que les panneaux doivent porter : tous ceux de la table (le garde-fou de s0_html ne vérifie que S0)
_PANEL_MISSING = [i for i in TABLE_IDS if i not in panel_ids()]
assert not _PANEL_MISSING, ('panneaux : ids de la table sans ligne', _PANEL_MISSING)


# ═════════════════════════════════════════════════════════════════════════════════
# CSS des nouveaux éléments
# ═════════════════════════════════════════════════════════════════════════════════

SCHEMAS_CSS = r'''
/* ── S0 : deux variantes, choisies par la largeur ── */
.sv-m-fc { fill: color-mix(in srgb, #D0784A 20%, var(--paper-light)); stroke: #D0784A; }
.sv-frame { fill: none; stroke: currentColor; stroke-width: 1.2; opacity: .5; }
.sv-chip { fill: var(--paper-light); stroke: currentColor; stroke-width: 1; opacity: .95; }
.sv-bd { fill: var(--paper-light); stroke: currentColor; stroke-width: 1.2; }
.fm-schema.fm-s0 svg { max-height: none; }
.fm-s0 .s0-tall { display: none; }
@media (max-width: 700px) {
  .fm-s0 .s0-wide { display: none; }
  .fm-s0 .s0-tall { display: block; }
  .fm-s0 { padding: 10px; }
}

/* ── Légende lettrée de S0 et ses six étapes ── */
.fm-xlegend { margin: -8px 0 28px; }
.fm-xlegend h4, .fm-rd h4 {
  font-family: var(--f-stencil); font-size: 12px; letter-spacing: 3px; text-transform: uppercase;
  color: var(--accent-ink); margin: 14px 0 8px; padding-left: 10px; border-left: 3px solid var(--chapter-accent, var(--fm-accent));
}
.fm-xlegend ul { list-style: none; padding: 0; margin: 0; }
.fm-xlegend li { font-size: 12.5px; line-height: 1.55; color: var(--ink); padding: 3px 0 3px 30px; position: relative; opacity: .92; }
.fm-xkey { font-size: 12px; color: var(--ink); opacity: .85; margin: 0 0 6px; }
.fm-xlegend ul.xsub { margin: 3px 0 2px; }
.fm-xlegend ul.xsub li { padding: 1px 0 1px 12px; font-size: 12px; }
.fm-xlegend ul.xsub li strong { font-weight: 700; }
.fm-xset { font-size: 12.5px; line-height: 1.55; color: var(--ink); margin: 10px 0 0; padding-left: 10px; border-left: 3px solid var(--khaki); }
.xb, .xs {
  position: absolute; left: 0; top: 4px; width: 20px; height: 18px; line-height: 16px; text-align: center; font-weight: 700; font-size: 12px;
  color: var(--ink); background: var(--paper-light); border: 1.2px solid var(--ink); border-radius: 3px;
}
.xs { background: var(--olive-dark); color: var(--paper-light); border-color: var(--olive-dark); border-radius: 50%; width: 20px; height: 20px; line-height: 18px; top: 3px; }

/* ── Panneau « Reçoit · Donne » ── */
.fm-rd { display: grid; grid-template-columns: 1fr 1fr; gap: 0 18px; margin: 0 0 26px; padding: 4px 14px 10px; border: 1px solid var(--chapter-accent, var(--fm-accent)); background: rgba(0,0,0,.06); }
.fm-rd.lang-block[data-lang] { display: grid; }
body[lang="en"] .fm-rd.lang-block[data-lang="fr"], body[lang="fr"] .fm-rd.lang-block[data-lang="en"] { display: none; }
.fm-rd ul { list-style: none; padding: 0; margin: 0; }
.fm-rd li { font-size: 12px; line-height: 1.5; color: var(--ink); padding: 5px 0; border-top: 1px dotted var(--khaki); }
.fm-rd li strong { font-weight: 700; }
.rd-g { opacity: .85; }
@media (max-width: 620px) { .fm-rd { grid-template-columns: 1fr; } }
'''


# ═════════════════════════════════════════════════════════════════════════════════
# Les trois schémas redessinés à l'écran du jour
# ═════════════════════════════════════════════════════════════════════════════════

def build_bg_svg():
    """Briefing Generator — « Ce qui alimente quoi » (viewBox 720 × 425), redessiné : l'image de carte du RP, la photo de RS (à la main),
    la section Wing d'Avancé, et ce que lit la fenêtre d'import commune (FC, RP, DG) en plus du DG."""
    M = 'bm'
    T = sv_text
    o = []
    o.append('<svg viewBox="0 0 720 425" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Ce qui alimente quoi" data-aria-fr="Ce qui alimente quoi" data-aria-en="What feeds what">')
    o.append('          ' + sv_defs(M))
    o.append('          ' + sv_title('CE QUI ALIMENTE QUOI', 'WHAT FEEDS WHAT', 24, 32))
    # rangée du haut
    o.append('          ' + sv_box(16, 66, 96, 42, 'hq'))
    o.append('          ' + T(64, 84, 12, 'HQ'))
    o.append('          ' + T(64, 98, 9, 'Wing'))
    o.append('          ' + sv_box(156, 66, 96, 42))
    o.append('          ' + T(204, 91, 11, 'Escadrons', 'Squadrons'))
    o.append('          ' + sv_tag(156, 66, 96, 'S·A', 'S·A'))
    o.append('          ' + sv_box(296, 66, 96, 42, 'bg'))
    o.append('          ' + T(344, 84, 11, 'Missions'))
    o.append('          ' + T(344, 98, 9, 'groupes', 'groups'))
    o.append('          ' + sv_tag(296, 66, 96, 'S·A', 'S·A'))
    o.append('          ' + sv_box(436, 66, 96, 42))
    o.append('          ' + T(484, 84, 10, 'Appareil', 'Aircraft'))
    o.append('          ' + T(484, 98, 9, 'sélectionné', 'selected'))
    o.append('          ' + sv_tag(436, 66, 96, 'S·A', 'S·A'))
    o.append('          ' + sv_box(576, 66, 100, 42))
    o.append('          ' + T(626, 91, 10.5, 'Plan radio', 'Radio plan'))
    o.append('          ' + sv_tag(576, 66, 100, 'S·A', 'S·A'))
    o.append('          ' + sv_line(112, 87, 154, 87, M))
    o.append('          ' + T(133, 80, 8, 'identité', 'identity'))
    o.append('          ' + sv_line(252, 87, 294, 87, M))
    o.append('          ' + T(273, 80, 8, 'escadron', 'squadron'))
    o.append('          ' + sv_line(392, 87, 434, 87, M))
    o.append('          ' + T(413, 80, 8, 'type'))
    o.append('          ' + sv_line(532, 87, 574, 87, M))
    o.append('          ' + T(553, 80, 8, 'réf radio', 'radio ref'))
    # le Route Planner et la section Wing, à gauche
    o.append('          ' + sv_box(16, 128, 96, 34, 'rp'))
    o.append('          ' + T(64, 143, 10.5, 'RP'))
    o.append('          ' + T(64, 155, 8, 'Route Planner'))
    o.append('          ' + sv_box(130, 128, 106, 34))
    o.append('          ' + T(183, 142, 9.5, 'Configuration Wing', 'Wing configuration'))
    o.append('          ' + T(183, 154, 8, 'lecture seule', 'read-only'))
    o.append('          ' + sv_tag(130, 128, 106, 'A', 'A'))
    o.append('          ' + sv_path('M112,98 C124,110 128,118 136,126', M, op=.8))
    # équipage
    o.append('          ' + sv_box(250, 190, 140, 42))
    o.append('          ' + T(320, 215, 11, 'Équipage', 'Crew'))
    o.append('          ' + sv_tag(250, 190, 140, 'A', 'A'))
    o.append('          ' + sv_path('M240,108 C240,150 270,165 280,189', M, op=.8))
    o.append('          ' + T(262, 178, 8, 'callsign → indicatifs', 'callsign → call signs', anchor='end'))
    o.append('          ' + sv_path('M344,108 C344,150 350,160 350,189', M, op=.8))
    o.append('          ' + T(356, 150, 8, 'groupes liés', 'linked groups', anchor='start'))
    # carte, menaces, cibles (Standard et Avancé), alimentée par le RP
    o.append('          ' + sv_box(20, 190, 170, 42))
    o.append('          ' + T(105, 215, 10.5, 'Carte · menaces · cibles', 'Map · threats · targets'))
    o.append('          ' + sv_tag(20, 190, 170, 'S·A', 'S·A'))
    o.append('          ' + sv_path('M50,162 C50,176 50,182 50,188', M, op=.8))
    o.append('          ' + T(58, 178, 8, 'image de la carte', 'map image', anchor='start'))
    # aérodromes, METAR
    o.append('          ' + sv_box(40, 296, 150, 42))
    o.append('          ' + T(115, 315, 10.5, 'Aérodromes / FARP', 'Airfields / FARPs'))
    o.append('          ' + T(115, 329, 8, 'ICAO'))
    o.append('          ' + sv_tag(40, 296, 150, 'S·A', 'S·A'))
    o.append('          ' + sv_box(250, 296, 120, 42))
    o.append('          ' + T(310, 321, 11, 'METAR'))
    o.append('          ' + sv_tag(250, 296, 120, 'S·A', 'S·A'))
    o.append('          ' + sv_line(190, 317, 248, 317, M))
    o.append('          ' + T(219, 310, 8, 'pré-rempli', 'pre-filled'))
    # en-tête et métadonnées
    o.append('          ' + sv_box(470, 296, 160, 42))
    o.append('          ' + T(550, 315, 10.5, 'En-tête · métadonnées', 'Header · metadata'))
    o.append('          ' + T(550, 329, 8, 'opération, date, classification', 'operation, date, classification'))
    o.append('          ' + sv_tag(470, 296, 160, 'S·A', 'S·A'))
    # boîtes neuves
    o.append('          ' + sv_box(20, 360, 190, 36))
    o.append('          ' + T(115, 382, 10, 'Couverture · charts · annexes', 'Cover · charts · annexes'))
    o.append('          ' + sv_tag(20, 360, 190, 'A', 'A'))
    o.append('          ' + sv_box(226, 360, 100, 36))
    o.append('          ' + T(276, 382, 11, 'Photos'))
    o.append('          ' + sv_tag(226, 360, 100, 'S', 'S'))
    # la photo de Recon Station : à la main
    o.append('          ' + sv_box(384, 360, 60, 36, 'rs'))
    o.append('          ' + T(414, 382, 11, 'RS'))
    o.append('          ' + sv_line(384, 378, 328, 378, M, dashed=True))
    o.append('          ' + T(356, 371, 8, 'à la main', 'by hand'))
    o.append('          ' + sv_path('M520,338 C500,350 470,352 440,358', M))
    o.append('          ' + T(500, 354, 8, 'préremplit', 'pre-fills', anchor='start'))
    # la fenêtre d'import commune et le Datacard Generator
    o.append('          ' + sv_box(470, 124, 170, 40))
    o.append('          ' + T(555, 142, 11, 'FC · RP · DG'))
    o.append('          ' + T(555, 156, 8, 'fenêtre d’import', 'import window'))
    o.append('          ' + sv_path('M392,100 C430,106 450,124 468,138', M, dashed=True))
    o.append('          ' + T(432, 130, 8, 'groupes', 'groups', anchor='end'))
    o.append('          ' + sv_line(626, 108, 626, 122, M, dashed=True))
    o.append('          ' + T(634, 118, 8, 'fréquences', 'frequencies', anchor='start'))
    o.append('          ' + sv_box(470, 200, 170, 42, 'dg'))
    o.append('          ' + T(555, 218, 11, 'Datacard Generator'))
    o.append('          ' + T(555, 232, 8, 'le briefing en entier', 'the whole briefing'))
    o.append('          ' + sv_line(390, 221, 468, 221, M, dashed=True))
    o.append('          ' + T(429, 214, 8, 'équipage', 'crew'))
    o.append('          ' + sv_path('M370,306 C440,300 500,276 520,244', M, dashed=True))
    o.append('          ' + T(536, 270, 8, 'METAR décodé', 'decoded METAR', anchor='start'))
    # la clé
    o.append('          ' + sv_pill(612, 364, 13, 13, 'S', 'S'))
    o.append('          ' + T(630, 374, 9, 'Standard', 'Standard', anchor='start'))
    o.append('          ' + sv_pill(612, 384, 13, 13, 'A', 'A'))
    o.append('          ' + T(630, 394, 9, 'Avancé', 'Advanced', anchor='start'))
    o.append('          ' + T(16, 416, 8.5, f'Tireté{NF}: lu par la fenêtre d’import ou par le Datacard Generator',
                              'Dashed: read by the import window or the Datacard Generator', anchor='start'))
    o.append('        </svg>')
    return '\n'.join(o)


def build_rp_screen_svg():
    """Route Planner — « L'écran du Route Planner » (viewBox 720 × 372), redessiné à l'écran du jour : barre, ligne de mission d'HQ,
    panneau en sections repliables, cinq modes de toucher, route, boîte de branche. Aucun libellé exact, aucun texte sous le corps 8."""
    M = 'rps'
    T = sv_text
    A = '#7ac97a'
    o = []
    o.append('<svg viewBox="0 0 720 372" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="L’écran du Route Planner" data-aria-fr="L’écran du Route Planner" data-aria-en="The Route Planner screen">')
    o.append('          ' + sv_defs(M))
    o.append('          ' + sv_title('L’ÉCRAN DU ROUTE PLANNER', 'THE ROUTE PLANNER SCREEN', 24, 32))
    # la barre du haut, dans l'ordre de l'écran : Ouvrir, Sauvegarder, Exporter, Affichage, Théâtre, Exemple, Effacer, Thème, langue
    o.append('          ' + sv_box(110, 44, 500, 26))
    o.append('          ' + T(118, 61, 8.5, 'RP', anchor='start', ls=1))
    x = 134
    for w, fr, en in ((50, 'Ouvrir ▾', 'Open ▾'), (64, 'Sauvegarder', 'Save'), (58, 'Exporter ▾', 'Export ▾'), (64, 'Affichage ▾', 'Display ▾'),
                      (46, 'Théâtre', 'Theatre'), (56, 'Exemple ▾', 'Example ▾'), (46, 'Effacer', 'Clear'), (36, 'Thème', 'Theme')):
        o.append('          ' + f'<rect x="{x}" y="49" width="{w}" height="16" rx="2" fill="none" stroke="currentColor" stroke-width="1" opacity=".6"/>')
        o.append('          ' + T(x + w / 2, 60.5, 8, fr, en))
        x += w + 4
    # le drapeau de la langue : un petit cadre, sans libellé
    o.append('          ' + f'<rect x="{x}" y="49" width="16" height="16" rx="2" fill="none" stroke="currentColor" stroke-width="1" opacity=".6"/>')
    o.append('          ' + f'<rect x="{x + 3}" y="54" width="10" height="7" fill="none" stroke="currentColor" stroke-width="1"/>')
    # la ligne de mission d'HQ, sous la barre
    o.append('          ' + sv_box(110, 74, 500, 14))
    o.append('          ' + T(118, 84, 8, 'Mission d’HQ · ce que l’outil en prend', 'HQ mission · what the tool takes from it', anchor='start'))
    # le panneau et ses sections numérotées, repliables
    o.append('          ' + sv_box(110, 94, 160, 262))
    secs = [(100, 118, '01 Route', '01 Route', 3), (222, 28, '02 Points de référence', '02 Reference points', 0),
            (254, 28, '03 Calques', '03 Layers', 0), (286, 64, '04 Navigation', '04 Navigation', 2)]
    for (y, h, fr, en, rows) in secs:
        o.append('          ' + f'<rect x="116" y="{y}" width="148" height="{h}" fill="none" stroke="currentColor" stroke-width="1" opacity=".75"/>')
        o.append('          ' + T(121, y + 11, 8, fr, en, anchor='start'))
        for k in range(rows):
            o.append('          ' + f'<line x1="122" y1="{y + 40 + 14 * k}" x2="258" y2="{y + 40 + 14 * k}" stroke="currentColor" stroke-width="1" opacity=".3"/>')
    # Tout replier : l'icône à droite de l'en-tête
    o.append('          ' + '<path d="M252,103 l4,4 l4,-4 M252,110 l4,-4 l4,4" fill="none" stroke="currentColor" stroke-width="1.2"/>')
    # la ligne de sélection des routes
    o.append('          ' + sv_box(122, 116, 100, 15))
    o.append('          ' + T(128, 127, 8, 'Route ▾', 'Route ▾', anchor='start'))
    o.append('          ' + sv_box(226, 116, 15, 15))
    o.append('          ' + T(233.5, 127, 8.5, '+'))
    o.append('          ' + sv_box(245, 116, 15, 15))
    o.append('          ' + T(252.5, 127, 8.5, '…'))
    # la carte, sa grille
    o.append('          ' + sv_box(276, 94, 334, 262))
    for x in (336, 396, 456, 516, 576):
        o.append('          ' + f'<line x1="{x}" y1="95" x2="{x}" y2="355" stroke="currentColor" stroke-width=".8" opacity=".18"/>')
    for y in (140, 190, 240, 290, 340):
        o.append('          ' + f'<line x1="277" y1="{y}" x2="609" y2="{y}" stroke="currentColor" stroke-width=".8" opacity=".18"/>')
    # zoom et loupe, à gauche de la carte
    o.append('          ' + '<rect class="sv-box" x="284" y="102" width="16" height="30" rx="2" stroke="currentColor" stroke-width="1"/>')
    o.append('          ' + T(292, 113, 9, '+') + T(292, 126, 9, '−'))
    o.append('          ' + '<rect class="sv-box" x="284" y="138" width="16" height="16" rx="2" stroke="currentColor" stroke-width="1"/>')
    o.append('          ' + '<circle cx="291" cy="145" r="3.6" fill="none" stroke="currentColor" stroke-width="1.3"/>')
    o.append('          ' + '<line x1="293.6" y1="147.6" x2="297" y2="151" stroke="currentColor" stroke-width="1.3"/>')
    # les cinq modes de toucher, en haut à droite de la carte
    modes = [('Point', 'Waypoint'), ('Réf.', 'Ref.'), ('Lire', 'Read'), ('Dessin', 'Draw'), ('Règle', 'Ruler')]
    for i, (fr, en) in enumerate(modes):
        x = 402 + 41 * i
        o.append('          ' + sv_box(x, 102, 41, 16, 'rp' if i == 0 else None))
        o.append('          ' + T(x + 20.5, 113, 8, fr, en))
    # la route : quatre points, une référence
    pts = [(322, 306), (380, 206), (496, 232), (566, 160)]
    o.append('          ' + '<polyline points="' + ' '.join(f'{x},{y}' for x, y in pts) +
             f'" fill="none" stroke="{A}" stroke-width="3" stroke-linejoin="round"/>')
    for i, (x, y) in enumerate(pts):
        o.append('          ' + f'<circle cx="{x}" cy="{y}" r="8" class="sv-box" stroke="currentColor" stroke-width="1.6"/>')
        o.append('          ' + T(x, y + 3, 8, str(i)))
    o.append('          ' + '<rect x="514" y="296" width="12" height="12" transform="rotate(45 520 302)" fill="currentColor"/>')
    o.append('          ' + sv_text(520, 305, 8, 'A', cls='sv-pill-t'))
    # la boîte de branche, sous la branche 1 → 2
    o.append('          ' + '<path class="sv-box" d="M410,252 L440,240 L470,252 L470,284 L410,284 Z" stroke="currentColor" stroke-width="1.2"/>')
    o.append('          ' + T(440, 266, 8, 'cap', 'course'))
    o.append('          ' + T(440, 277, 8, 'dist.', 'dist.'))
    # libellés, à gauche
    o.append('          ' + T(102, 150, 10, 'Panneau', 'Panel', anchor='end'))
    o.append('          ' + sv_line(105, 147, 128, 147, M))
    o.append('          ' + T(102, 238, 10, 'Sections', 'Sections', anchor='end'))
    o.append('          ' + T(102, 250, 10, 'repliables', 'foldable', anchor='end'))
    o.append('          ' + sv_line(105, 244, 120, 244, M))
    # libellés, à droite
    o.append('          ' + T(622, 58, 10, 'Barre du haut', 'Top bar', anchor='start'))
    o.append('          ' + sv_line(618, 55, 596, 55, M))
    o.append('          ' + T(622, 84, 10, 'Mission d’HQ', 'HQ mission', anchor='start'))
    o.append('          ' + sv_line(618, 81, 598, 81, M))
    o.append('          ' + T(622, 114, 10, 'Modes de toucher', 'Tap modes', anchor='start'))
    o.append('          ' + sv_line(620, 111, 606, 111, M))
    o.append('          ' + T(622, 166, 10, 'Route', anchor='start'))
    o.append('          ' + sv_line(618, 163, 576, 161, M))
    o.append('          ' + T(622, 270, 10, 'Boîte', 'Leg box', anchor='start'))
    o.append('          ' + T(622, 282, 10, 'de branche', 'per leg', anchor='start'))
    o.append('          ' + sv_line(618, 272, 473, 268, M))
    o.append('          ' + T(622, 330, 10, 'Carte', 'Map', anchor='start'))
    o.append('          ' + sv_line(618, 327, 600, 327, M))
    o.append('        </svg>')
    return '\n'.join(o)


def build_dg_anatomy_svg():
    """Datacard Generator — « Anatomie d'une datacard » (viewBox 720 × 420), redessinée : Carburant · Emport pleine largeur, Menaces · Notes dessous,
    Points de référence avec la navigation."""
    M = 'dga'
    T = sv_text
    o = []
    o.append('<svg viewBox="0 0 720 420" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Anatomie d’une datacard" data-aria-fr="Anatomie d’une datacard" data-aria-en="Anatomy of a datacard">')
    o.append('          ' + sv_defs(M))
    o.append('          ' + sv_title('ANATOMIE D’UNE DATACARD', 'ANATOMY OF A DATACARD', 26, 34))
    # la page, son en-tête et ses bandeaux
    o.append('          ' + '<rect class="sv-box" x="270" y="50" width="180" height="318"/>')
    o.append('          ' + '<rect x="270" y="50" width="180" height="8" fill="currentColor" opacity=".85"/>')
    o.append('          ' + '<rect x="270" y="360" width="180" height="8" fill="currentColor" opacity=".85"/>')
    o.append('          ' + T(276, 80, 17, 'CAESAR', anchor='start'))
    o.append('          ' + '<line x1="276" y1="88" x2="350" y2="88" stroke="currentColor" stroke-width="1.4" opacity=".7"/>')
    o.append('          ' + T(444, 70, 9, 'DATACARD', anchor='end', ls=1))
    o.append('          ' + '<line x1="392" y1="77" x2="444" y2="77" stroke="currentColor" stroke-width="1" opacity=".6"/>')
    o.append('          ' + '<rect x="414" y="83" width="30" height="7" fill="#a83524" opacity=".85"/>')

    def blk(x, y, w, h, fr, en, dashed=False):
        d = ' stroke-dasharray="4 3"' if dashed else ''
        o.append('          ' + f'<rect x="{x}" y="{y}" width="{w}" height="{h}" class="sv-box" stroke="currentColor" stroke-width="1.1"{d}/>')
        o.append('          ' + f'<rect x="{x}" y="{y}" width="{w}" height="6" fill="currentColor" opacity=".75"/>')
        o.append('          ' + T(x + w / 2, y + 6 + (h - 6) / 2 + 3, 8, fr, en))
    blk(274, 96, 106, 44, 'MISSION', 'MISSION')
    blk(384, 96, 62, 44, 'HORAIRES', 'TIMES')
    blk(274, 144, 172, 24, 'ÉQUIPAGES', 'CREW')
    blk(274, 172, 172, 44, 'NAVIGATION', 'NAVIGATION', True)
    blk(274, 220, 172, 22, 'POINTS DE RÉFÉRENCE', 'REFERENCE POINTS')
    blk(274, 246, 90, 50, 'RADIO', 'RADIO')
    blk(368, 246, 78, 23, 'TERRAINS', 'AIRFIELDS')
    blk(368, 273, 78, 23, 'MÉTÉO', 'WEATHER')
    blk(274, 300, 172, 28, 'CARBURANT · EMPORT', 'FUEL · LOADOUT')
    blk(274, 332, 172, 24, 'MENACES · NOTES', 'THREATS · NOTES')
    o.append('          ' + '<path d="M270,50 h180 v318 h-180 z" fill="none" stroke="#4f7a8e" stroke-width="2"/>')
    # libellés à gauche
    left = [(54, 'Classification · référence · page', 'Classification · reference · page'),
            (84, 'Indicatif · appareil · tâche', 'Callsign · aircraft · task'),
            (118, 'Objectif et étapes', 'Objective and steps'),
            (156, 'Indicatif · pilote · appareil · n°', 'Callsign · pilot · aircraft · no.'),
            (271, 'Postes et canaux', 'Radios and channels'),
            (314, 'Carburant · poids · joker · bingo · emport', 'Fuel · weight · joker · bingo · loadout')]
    for y, fr, en in left:
        o.append('          ' + sv_line(232, y, 270, y, M, op=.55, sw=1))
        o.append('          ' + T(226, y + 4, 11, fr, en, anchor='end'))
    right = [(72, 'Opération · date · menace', 'Operation · date · threat'),
             (118, 'Mise en route → RTB', 'Start-up → RTB'),
             (231, 'Points de référence', 'Reference points'),
             (257, 'DEP · ARR · ALT', 'DEP · ARR · ALT'),
             (284, 'METAR décodé', 'Decoded METAR'),
             (344, 'Menaces · notes', 'Threats · notes')]
    for y, fr, en in right:
        o.append('          ' + sv_line(488, y, 450, y, M, op=.55, sw=1))
        o.append('          ' + T(494, y + 4, 11, fr, en, anchor='start'))
    o.append('          ' + sv_line(488, 194, 450, 194, M, op=.55, sw=1))
    o.append('          ' + T(494, 191, 11, 'Points, caps, distances', 'Points, headings, distances', anchor='start'))
    o.append('          ' + T(494, 205, 11, '→ page 2 si elle déborde', '→ page 2 if it overflows', anchor='start'))
    # pied
    o.append('          ' + sv_line(360, 400, 360, 371, M, op=.55, sw=1))
    o.append('          ' + T(360, 414, 11, 'Pied : indicatif · opération · classification · page', 'Footer: callsign · operation · classification · page'))
    o.append('        </svg>')
    return '\n'.join(o)
