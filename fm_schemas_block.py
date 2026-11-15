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

# La légende : une ligne par lettre, ce qui passe, de quel outil à quel outil, et ce que cela apporte ; jamais le geste, le menu ni le détail
# (ils sont dans le panneau Reçoit · Donne du chapitre et dans ses gestes). Chaque ligne finit par un renvoi : (FR, EN, [pages]).
S0_LEGEND = {
    'dcs_in': ("DCS → HQ : le .miz, dont HQ lit les groupes, la date, l’heure et la météo.",
               "DCS → HQ: the .miz, whose groups, date, time and weather HQ reads.", ['hq']),
    'dcs_out': ("HQ → DCS : le .miz final, avec les paquets appliqués.",
                "HQ → DCS: the final .miz, with the packages applied.", ['hq']),
    'print': ("BG → imprimé : le briefing, en PDF ou en PNG par page.",
              "BG → printout: the briefing, as a PDF or one PNG per page.", ['bg']),
    'example': ("Exemple ▾ : un exemple complet par groupe d’outils.",
                "Example ▾: a complete example per tool group.", ['gestes']),
    'wing': ("HQ → BG, RS, DG, FC : l’escadre, pour les en-têtes, logos, indicatifs et livrées.",
             "HQ → BG, RS, DG, FC: the wing, for headers, logos, call signs and liveries.", ['hq']),
    'brief_rs': ("BG → RS : le bloc d’informations de la photo, pour le préremplir.",
                 "BG → RS: the photo’s info block, to pre-fill it.", ['rs']),
    'mission': ("HQ → BG, RP, DG, FC : la mission ouverte, pour la météo, la date et l’heure du briefing et pour créer les groupes.",
                "HQ → BG, RP, DG, FC: the open mission, for the briefing’s weather, date and time and to create the groups.", ['bg', 'rp', 'dg', 'fc']),
    'photo': ("RS → BG : la photo composée, ajoutée à la main au briefing.",
              "RS → BG: the composed photo, added by hand to the briefing.", ['rs', 'bg']),
    'work': ("Fichier de travail : tout le travail sauf HQ, à reprendre ou à passer à un autre pilote.",
             "Work file: all the work except HQ, to resume or to pass to another pilot.", ['gestes']),
    'pack': ("HQ → RP, DG, FC : les groupes cochés en paquet, pour travailler sans le .miz.",
             "HQ → RP, DG, FC: the ticked groups as a package, to work without the .miz.", ['hq', 'fc']),
    'fpack': ("FC → HQ : le paquet de vol, appliqué au .miz ; c’est le seul retour qui se fusionne.",
              "FC → HQ: the flight package, applied to the .miz; it is the only return that merges.", ['fc', 'hq']),
    'brief_fl': ("BG → RP, DG, FC : le briefing en cours, pour créer les groupes, régler les radios et préremplir les datacards.",
                 "BG → RP, DG, FC: the current briefing, to create the groups, set the radios and pre-fill the datacards.", ['bg', 'rp', 'dg', 'fc']),
    'map': ("RP → BG : l’image de la carte, pour le briefing.",
            "RP → BG: the map image, for the briefing.", ['rp', 'bg']),
    'routes': ("RP → FC, RP ↔ DG : les routes, pour les groupes et les datacards ; le DG réécrit les points qu’il modifie.",
               "RP → FC, RP ↔ DG: the routes, for the groups and the datacards; the DG rewrites the points it edits.", ['rp', 'dg', 'fc']),
    'active': ("RP → DG : la route active et les points de référence, pour la carte.",
               "RP → DG: the active route and the reference points, for the card.", ['rp', 'dg']),
    'groups': ("RP, DG, FC : la fiche des groupes, partagée en direct dans les deux sens.",
               "RP, DG, FC: the group sheet, shared live both ways.", ['rp', 'dg', 'fc']),
    'remove': ("DG, FC : retirer un groupe retire aussi sa datacard.",
               "DG, FC: removing a group also removes its datacard.", ['dg', 'fc']),
    'cf': ("CombatFlite → RP : les calques d’un fichier .cf, en lecture seule sur la carte.",
           "CombatFlite → RP: the layers of a .cf file, read-only on the map.", ['rp']),
    'lua': ("RP ↔ DCS : les routes du Route Tool, à reprendre ou à lui donner.",
            "RP ↔ DCS: the Route Tool routes, to take back or to give it.", ['rp']),
    'knee': ("DG → kneeboard, imprimé : les datacards, en PNG ou en PDF.",
             "DG → kneeboard, printout: the datacards, as PNG or PDF.", ['dg']),
}

# Le renvoi de fin de ligne : page → (ancre, FR, EN). « gestes » = la table des gestes de « Par où commencer ».
LINKS = {
    'hq': ('hq', 'HQ', 'HQ'), 'bg': ('bg', 'BG', 'BG'), 'rs': ('rs', 'RS', 'RS'), 'fc': ('fc', 'FC', 'FC'), 'rp': ('rp', 'RP', 'RP'),
    'dg': ('dg', 'DG', 'DG'), 'gestes': ('start:gestes', 'Les gestes', 'Gestures'),
}

# Les réglages ne s'échangent pas : une phrase sous la légende
S0_SETTINGS = (
    "Les réglages ne sont pas des échanges : le théâtre et les unités se règlent dans la barre de l’un des trois outils du Flight Leader et valent pour les trois ; le cap vaut pour le RP et le DG.",
    "Settings are not exchanges: the theatre and the units are set in the bar of any one of the three Flight Leader tools and apply to all three; the heading applies to the RP and the DG.")

# Les six étapes du travail type ; {clé} = la lettre de la flèche ; une ou deux phrases, le geste précis est au chapitre
S0_STEPS = [
    (1, "Mission Commander, dans HQ : saisir le Wing une fois ({wing}), puis ouvrir le .miz ({dcs_in}) pour offrir sa mission aux autres outils ({mission}).",
        "Mission Commander, in HQ: enter the Wing once ({wing}), then open the .miz ({dcs_in}) to offer its mission to the other tools ({mission}).", ['hq']),
    (2, "Mission Commander, BG puis RS : écrire le briefing, composer la photo et l’ajouter à la main au briefing ({photo}).",
        "Mission Commander, BG then RS: write the briefing, compose the photo and add it by hand to the briefing ({photo}).", ['bg', 'rs']),
    (3, "Mission Commander : sauvegarder le fichier de travail ({work}) et le donner aux Flight Leaders, qui y prennent le briefing ({brief_fl}). Le .miz ou le paquet d’HQ ({pack}) leur est facultatif.",
        "Mission Commander: save the work file ({work}) and give it to the Flight Leaders, who take the briefing from it ({brief_fl}). The .miz or the HQ package ({pack}) is optional for them.", ['gestes', 'hq']),
    (4, "Flight Leader : ouvrir le fichier de travail, et au besoin le .miz ({mission}) ou le paquet ({pack}) ; tracer la route au RP, composer les datacards au DG, régler groupes, radios et emport au FC ({groups}).",
        "Flight Leader: open the work file, and if needed the .miz ({mission}) or the package ({pack}); draw the route in the RP, compose the datacards in the DG, set up groups, radios and loadout in the FC ({groups}).", ['rp', 'dg', 'fc']),
    (5, "Flight Leader : exporter au FC le paquet de vol et le rendre au Mission Commander ({fpack}).",
        "Flight Leader: export the flight package in the FC and hand it back to the Mission Commander ({fpack}).", ['fc']),
    (6, "Mission Commander : dans HQ, appliquer les paquets, puis sauvegarder le .miz final ({dcs_out}).",
        "Mission Commander: in HQ, apply the packages, then save the final .miz ({dcs_out}).", ['hq']),
]

# La note du .miz facultatif, dans S0 (large et haute) : {mission} et {pack} = les lettres
NOTE_MIZ_FR = ['Le .miz est facultatif pour un', 'Flight Leader : soit le .miz ({mission}),', 'à ouvrir dans son HQ, soit le', 'paquet exporté d’HQ ({pack}).']
NOTE_W_FR = ['Le .miz est facultatif', 'pour un Flight Leader :', 'soit le .miz ({mission}),', 'à ouvrir dans son HQ,', 'soit le paquet d’HQ ({pack}).']
NOTE_W_EN = ['The .miz is optional', 'for a Flight Leader:', 'either the .miz ({mission}),', 'to open in their HQ,', 'or the HQ package ({pack}).']
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
        (['S2', 'F5', 'F6'], ['.miz d’HQ ou paquet :', 'groupes et leurs parties'], ['HQ .miz or package:', 'groups and their parts']),
        (['S5'], ['briefing : groupes'], ['briefing: groups']),
    ],
    'dg': [
        (['S2'], ['.miz d’HQ : groupes,', 'date, heure, météo'], ['HQ .miz: groups,', 'date, time, weather']),
        (['F5', 'F6'], ['ou paquet : groupes', 'et leurs parties'], ['or package: groups', 'and their parts']),
        (['S1'], ['Wing : indicatifs'], ['Wing: call signs']),
        (['S4', 'S5'], ['briefing : un vol', 'par carte'], ['briefing: one flight', 'per card']),
    ],
}

# Ce que les modules du Mission Commander lisent, sous leur nom (le détail est dans la légende)
SUBS = {
    'hq': [('lit : .miz de DCS,', 'reads: DCS .miz,'), ('paquets de vol du FC', 'FC flight packages')],
    'bg': [('lit : Wing, météo, date', 'reads: Wing, weather, date'), ('et heure d’HQ, carte RP,', 'and time from HQ, RP map,'), ('photo RS', 'RS photo')],
    'rs': [('lit : le bloc d’informations', 'reads: the photo’s info'), ('de la photo (BG), logos', 'block (BG), Wing'), ('du Wing', 'logos')],
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
    note_fr = [t.format_map(L) for t in NOTE_W_FR]
    note_en = [t.format_map(L) for t in NOTE_W_EN]
    # les cadres, leurs titres (en bas à droite : le haut et la gauche portent des flèches)
    s.frame(8, 62, 588, 184)
    s.T(588, 238, 10.5, 'MISSION COMMANDER', anchor='end', ls=1.5)
    s.frame(8, 340, 588, 284)
    s.T(588, 616, 10.5, 'FLIGHT LEADER', anchor='end', ls=1.5)
    # « Exemple ▾ » : une boîte tiretée par cadre, hors du cadre, reliée par une flèche (lettre d)
    s.ext(626, 70, 86, 40, [('Exemple ▾', 'Example ▾'), ('→ BG · RS', '→ BG · RS')], 9.5)
    s.ext(626, 470, 86, 40, [('Exemple ▾', 'Example ▾'), ('→ RP · DG · FC', '→ RP · DG · FC')], 9.5)
    # les six modules
    s.module('hq', cols[0], MCy, MW, 88, sub=SUBS['hq'])
    s.module('bg', cols[1], MCy, MW, 88, sub=SUBS['bg'])
    s.module('rs', cols[2], MCy, MW, 88, sub=SUBS['rs'])
    s.module('rp', cols[0], FLy, MW, FLh, card=True)
    s.module('dg', cols[1], FLy, MW, FLh, card=True)
    s.module('fc', cols[2], FLy, MW, FLh, card=True)
    # hors de la suite
    s.ext(34, 8, 156, 30, [('DCS', 'DCS')])
    s.ext(252, 8, 160, 30, [('Imprimés · PDF, PNG', 'Printouts · PDF, PNG')], 10)
    s.ext(24, 654, 100, 34, [('CombatFlite', 'CombatFlite'), ('.cf', '.cf')], 10)
    s.ext(134, 654, 100, 34, [('Route Tool', 'Route Tool'), ('.lua', '.lua')], 10)
    s.ext(244, 654, 150, 34, [('Kneeboard · imprimé', 'Kneeboard · printout')], 10)
    # Mission Commander : entrées, sorties
    A('example', 'M626,90 L598,90', True, bd=(612, 90))
    A('example', 'M626,490 L598,490', True, bd=(612, 490))
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
    A('fpack', 'M424,362 L424,206 L170,206 L170,192', True, bd=(424, 292))
    A('brief_fl', 'M300,192 L300,340', bd=(300, 292))
    A('map', 'M150,362 L150,226 L240,226 L240,192', bd=(150, 318))
    s.T(0, 0, 9, 'le .miz', 'the .miz', extra=' transform="translate(69 293) rotate(-90)"')
    s.T(0, 0, 9, '(facultatif)', '(optional)', extra=' transform="translate(58 293) rotate(-90)"')
    s.T(0, 0, 9, 'ou le paquet', 'or the package', extra=' transform="translate(121 293) rotate(-90)"')
    s.note(442, 256, 150, 78, note_fr, note_en, size=9)
    # le Flight Leader : hors de la suite (les flèches passent derrière la barre)
    A('cf', 'M70,654 L70,526', True, bd=(70, 632))
    A('lua', 'M176,654 L176,526', True, both=True, bd=(176, 632))
    A('knee', 'M270,526 L270,654', True, bd=(270, 632))
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
    A('routes', 'M190,428 L224,428', False, both=True, bd=(207, 428))
    A('routes', 'M170,362 L170,351 L500,351 L500,362', bd=(335, 351))
    A('active', 'M190,456 L224,456', bd=(207, 456))
    # les étapes du travail type
    for (x, y, n) in ((34, 104, 1), (224, 104, 2), (414, 104, 2), (606, 266, 3), (34, 362, 4), (224, 362, 4), (414, 362, 4), (424, 236, 5), (116, 80, 6)):
        s.step(x, y, n)
    return s


def build_s0_tall(L):
    # Les deux boîtes « Exemple ▾ » sont hors des cadres : l'une dans la rangée du haut, l'autre entre les deux cadres (+72 de hauteur, soit 5,5 %).
    D1, D2 = 24, 48
    s = _S(320, 1316 + D1 + D2, 's0t', _ARIA[0], _ARIA[1], 's0-tall', L)
    A = s.arrow
    mx, mw = 80, 160
    HQy, BGy, RSy = 92 + D1, 210 + D1, 328 + D1
    FLf = 520 + D1 + D2                      # le haut du cadre Flight Leader
    RPy, DGy, FCy, FLh = 626 + D1 + D2, 834 + D1 + D2, 1042 + D1 + D2, 164
    EXy = 1256 + D1 + D2
    note_fr = [t.format_map(L) for t in NOTE_MIZ_FR]
    note_en = [t.format_map(L) for t in NOTE_MIZ_EN]
    s.frame(4, 52 + D1, 312, 376)
    s.frame(4, FLf, 312, 704)
    # les titres en tête de cadre
    s.T(30, 66 + D1, 10.5, 'MISSION COMMANDER', anchor='start', ls=1.5)
    s.T(84, 534 + D1 + D2, 10.5, 'FLIGHT LEADER', anchor='start', ls=1.5)
    s.note(84, 556 + D1 + D2, 224, 58, note_fr, note_en)
    s.module('hq', mx, HQy, mw, 88, sub=SUBS['hq'])
    s.module('bg', mx, BGy, mw, 88, sub=SUBS['bg'])
    s.module('rs', mx, RSy, mw, 88, sub=SUBS['rs'])
    s.module('rp', mx, RPy, mw, FLh, card=True)
    s.module('dg', mx, DGy, mw, FLh, card=True)
    s.module('fc', mx, FCy, mw, FLh, card=True)
    s.ext(172, 6, 140, 30, [('DCS', 'DCS')])
    s.ext(8, 6, 84, 30, [('Imprimés', 'Printouts')], 10)
    s.ext(100, 6, 64, 30, [('Exemple ▾', 'Example ▾'), ('→ BG · RS', '→ BG · RS')], 9)
    s.ext(146, 526, 94, 36, [('Exemple ▾', 'Example ▾'), ('→ RP · DG · FC', '→ RP · DG · FC')], 9)
    s.ext(8, EXy, 96, 40, [('CombatFlite', 'CombatFlite'), ('.cf', '.cf')], 10)
    s.ext(112, EXy, 96, 40, [('Route Tool', 'Route Tool'), ('.lua', '.lua')], 10)
    s.ext(216, EXy, 96, 40, [('Kneeboard', 'Kneeboard'), ('imprimé', 'printout')], 10)
    # les boîtes « Exemple ▾ » : une flèche chacune vers son cadre (lettre d)
    A('example', f'M132,36 L132,{52 + D1}', True, bd=(132, 56))
    A('example', f'M193,562 L193,{FLf}', True, bd=(193, 577))
    # Mission Commander : entrées et sorties
    A('dcs_in', f'M185,36 L185,{HQy}', True, bd=(185, 60))
    A('dcs_out', f'M213,{HQy} L213,36', True, bd=(213, 60))
    A('print', f'M{mx},{BGy + 20} L20,{BGy + 20} L20,36', True, bd=(20, 120 + D1))
    A('wing', f'M{mx + 30},{HQy + 88} L{mx + 30},{BGy}', bd=(mx + 30, 195 + D1))
    A('mission', f'M{mx + 75},{HQy + 88} L{mx + 75},{BGy}', bd=(mx + 75, 195 + D1))
    A('wing', f'M{mx + mw},{HQy + 36} L286,{HQy + 36} L286,{RSy + 30} L{mx + mw},{RSy + 30}', bd=(286, 250 + D1))
    A('brief_rs', f'M{mx + 30},{BGy + 88} L{mx + 30},{RSy}', bd=(mx + 30, 313 + D1))
    A('photo', f'M{mx + 110},{RSy} L{mx + 110},{BGy + 88}', True, bd=(mx + 110, 313 + D1))
    # du Mission Commander au Flight Leader : le côté gauche (le .miz ou le paquet)
    A('mission', f'M{mx},{HQy + 14} L30,{HQy + 14} L30,{FLf}', bd=(30, 470 + D1))
    A('pack', f'M{mx},{HQy + 24} L46,{HQy + 24} L46,{FLf}', True, bd=(46, 455 + D1))
    A('fpack', f'M{mx},{FCy + 40} L62,{FCy + 40} L62,{HQy + 36} L{mx},{HQy + 36}', True, bd=(62, 440 + D1))
    A('brief_fl', f'M{mx},{BGy + 46} L76,{BGy + 46} L76,{FLf}', bd=(76, 485 + D1))
    # l'image de carte : le côté droit
    A('map', f'M{mx + mw},{RPy + 30} L250,{RPy + 30} L250,{BGy + 36} L{mx + mw},{BGy + 36}', bd=(250, 420 + D1))
    # le fichier de travail
    s.ids.add('C2')
    s.add('<g data-ex="C2">')
    s.box(mx + 16, 446 + D1, mw - 16, 46)
    s.T(mx + 16 + (mw - 16) / 2, 464 + D1, 10.5, 'Fichier de travail', 'Work file')
    s.T(mx + 16 + (mw - 16) / 2, 481 + D1, 9.5, 'hors HQ', 'not HQ')
    s.add('</g>')
    A('work', f'M{mx + 100},{446 + D1} L{mx + 100},{52 + D1 + 376}', False, both=True, bd=(mx + 124, 437 + D1))
    A('work', f'M{mx + 40},{492 + D1} L{mx + 40},{FLf}', False, both=True, bd=(mx + 40, 506 + D1 + 22))
    # le Flight Leader : hors de la suite (les flèches passent derrière la barre ou les modules, jamais dessus)
    A('cf', f'M56,{EXy} L56,{EXy - 18} L274,{EXy - 18} L274,{RPy + 90} L{mx + mw},{RPy + 90}', True, bd=(110, EXy - 18))
    A('lua', f'M160,{EXy} L160,{EXy - 10} L262,{EXy - 10} L262,{RPy + 60} L{mx + mw},{RPy + 60}', True, both=True, bd=(212, EXy - 10))
    A('knee', f'M{mx + mw},{DGy + 120} L288,{DGy + 120} L288,{EXy}', True, bd=(288, EXy - 40))
    # le Flight Leader : ce qui est partagé, dans les deux sens (la barre à gauche, tournée)
    s.ids.update(['S6', 'S10'])
    s.add('<g data-ex="S6 S10">')
    s.add(f'<rect class="sv-box" x="14" y="{640 + D1 + D2}" width="22" height="544" rx="3" stroke="currentColor" stroke-width="1.4"/>')
    s.add(sv_text(0, 0, 10, 'groupes · unités · radios · emport · route copiée · retrait d’un groupe',
                  'groups · units · radios · loadout · copied route · removal of a group', extra=f' transform="translate(29 {912 + D1 + D2}) rotate(-90)"'))
    s.add('</g>')
    for ty in (FCy + 80, RPy + 20, DGy + 80):
        A('groups', f'M{mx},{ty} L36,{ty}', False, both=True)
    s.badge_only('groups', 25, RPy)
    s.badge_only('remove', 47, RPy)
    A('routes', f'M{mx + 110},{RPy + FLh} L{mx + 110},{DGy}', False, both=True, bd=(mx + 110, DGy - 22))
    s.badge_only('active', mx + 127, DGy - 22)
    A('routes', f'M{mx + mw},{RPy + 135} L248,{RPy + 135} L248,{FCy + 135} L{mx + mw},{FCy + 135}', bd=(248, DGy + 40))
    for (x, y, n) in ((mx, HQy, 1), (mx, BGy, 2), (mx, RSy, 2), (mx + 16, 446 + D1, 3), (mx, FCy, 4), (mx, RPy, 4), (mx, DGy, 4), (62, 400 + D1, 5), (238, 78 + D1, 6)):
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


def _links(pages, lang):
    """Les renvois de fin de ligne : « → HQ », « → RP · DG · FC » (une ancre vers le chapitre chacun)."""
    parts = []
    for pg in pages:
        anchor, fr, en = LINKS[pg]
        parts.append(f'<a class="fm-xl" href="#{anchor}" onclick="location.hash=\'{anchor}\';return false">{_esc(fr if lang == "fr" else en)}</a>')
    return '<span class="fm-xgo">→ ' + ' · '.join(parts) + '</span>'


def s0_legend_html(L):
    """La légende lettrée de S0 (dans l'ordre alphabétique, une ligne par lettre), la phrase des réglages, puis les six étapes."""
    out = {}
    for lang in ('fr', 'en'):
        T = fr_typo if lang == 'fr' else (lambda x: x)
        i = 0 if lang == 'fr' else 1
        items = []
        for key in sorted(AK, key=lambda k: L[k]):
            e = S0_LEGEND[key]
            ids = ' '.join(AK[key])
            items.append(f'<li data-ex="{ids}"><span class="xb">{L[key]}</span> {_esc(T(e[i]))} {_links(e[2], lang)}</li>')
        steps = ''.join(f'<li><span class="xs">{st[0]}</span> {_esc(T(st[1 + i].format_map(L)))} {_links(st[3], lang)}</li>' for st in S0_STEPS)
        out[lang] = (''.join(items), steps, T(S0_SETTINGS[i]))
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
# Les six panneaux Reçoit · Donne (la passe de corrections : texte plus court, sans les valeurs que l'écran montre)
_SHEET_FR = "Groupes, unités, radios, emport, route copiée"
_SHEET_EN = "Groups, units, radios, loadout, copied route"

def _share(tool):
    """La ligne commune des trois outils du Flight Leader, vue de l'outil `tool` (les réglages n'en sont pas : ce ne sont pas des échanges)."""
    others = {'fc': ('RP, DG', 'RP, DG'), 'rp': ('DG, FC', 'DG, FC'), 'dg': ('RP, FC', 'RP, FC')}[tool]
    return [
        (['S6'], (_SHEET_FR, others[0], 'sans geste, dans les deux sens', 'pour que les trois se suivent'),
                 (_SHEET_EN, others[1], 'no gesture, both ways', 'so the three follow each other')),
    ]

_WORK_IN_FR = ('Le travail rangé : fichier de travail, exemple', 'la suite', 'Ouvrir ▾ › Ouvrir un travail…, Exemple ▾', 'pour reprendre le travail')
_WORK_IN_EN = ('Stored work: work file, example', 'the suite', 'Open ▾ › Open a work file…, Example ▾', 'to resume the work')

# Le fichier de travail, côté Flight Leader : ce qu'il y met sert à reprendre son travail ou à le passer à un autre Flight Leader (il ne revient pas au Mission Commander)
def _work_out_fl(fr_what, en_what, extra_fr='', extra_en=''):
    return (['C2'], (fr_what, 'le fichier de travail', 'Sauvegarder', 'pour le reprendre ou le passer' + extra_fr),
                    (en_what, 'the work file', 'Save', 'to resume it or pass it on' + extra_en))

# Le paquet de vol exporté d'HQ : l'autre voie du Flight Leader, sans le .miz
def _pack_in(tool):
    who = {'fc': ('HQ, un autre FC', 'HQ, another FC', 'Importer des groupes… › Fichier', 'Import groups… › File'),
           'rp': ('HQ, FC', 'HQ, FC', 'Importer des routes… › Fichier', 'Import routes… › File'),
           'dg': ('HQ, FC', 'HQ, FC', 'menu … des cartes › Importer des groupes › Fichier', 'cards … menu › Import groups › File')}[tool]
    if tool == 'dg':
        what = ('Ou, sans .miz : un paquet exporté d’HQ', 'Or, without the .miz: a package exported from HQ')
        why = ('pour créer les cartes sans la mission d’HQ', 'to create the cards without the HQ mission')
    else:
        what = ('Ou, sans .miz : un paquet exporté d’HQ, ou un ancien fichier de briefing (.json)', 'Or, without the .miz: a package exported from HQ, or an old briefing file (.json)')
        why = ('pour importer sans le .miz', 'to import without the .miz')
    return (['F5', 'F6'], (what[0], who[0], who[2], why[0]), (what[1], who[1], who[3], why[1]))

PANELS = {
    'hq': {
        'in': [
            (['F1'], ('Le .miz : les groupes Client, la date, l’heure, la météo', 'DCS', 'Ouvrir .miz, ou le déposer sur la page', 'pour les offrir aux autres outils'),
                     ('The .miz: the Client groups, the date, the time, the weather', 'DCS', 'Open .miz, or drop it on the page', 'to offer them to the other tools')),
            (['F4'], ('Un paquet de vol', 'le FC', 'Paquets de vol › Importer, puis Appliquer à la mission', 'pour les écrire dans les groupes du .miz'),
                     ('A flight package', 'the FC', 'Flight packages › Import, then Apply to the mission', 'to write them into the .miz groups')),
            (['F7'], ('Une configuration Wing', 'un autre HQ', 'Wing › Importer config', 'pour ne pas ressaisir le Wing'),
                     ('A Wing configuration', 'another HQ', 'Wing › Import config', 'so the Wing need not be typed again')),
        ],
        'out': [
            (['S1'], ('Le Wing : identité, escadrons, livrées', 'BG, RS, DG, FC et la barre de chaque outil', 'sans geste, à chaque saisie de la fenêtre Wing', 'pour les en-têtes, logos, indicatifs, livrées'),
                     ('The Wing: identity, squadrons, liveries', 'BG, RS, DG, FC and each tool bar', 'no gesture, at every Wing window entry', 'for headers, logos, call signs, liveries')),
            (['S2'], ('La mission ouverte : groupes Client, date, heure, météo', 'BG, RP, DG, FC', 'sans geste, jusqu’à Effacer ou la fermeture de la page', 'pour la météo, la date et l’heure du briefing, et les imports'),
                     ('The open mission: Client groups, date, time, weather', 'BG, RP, DG, FC', 'no gesture, until Clear or the page is closed', 'for the briefing’s weather, date and time, and the imports')),
            (['F5', 'F6'], ('Un paquet des groupes cochés', 'RP, DG, FC, un autre HQ', 'Exporter, parmi les actions sur les groupes cochés, puis leur fenêtre d’import › Fichier', 'pour travailler sans le .miz, qui est facultatif'),
                           ('A package of the ticked groups', 'RP, DG, FC, another HQ', 'Export, among the actions on the ticked groups, then their import window › File', 'to work without the .miz, which is optional')),
            (['F7'], ('La configuration Wing', 'un autre HQ', 'Wing › Exporter config', 'pour que deux HQ aient le même Wing'),
                     ('The Wing configuration', 'another HQ', 'Wing › Export config', 'so two HQs have the same Wing')),
            (['F3'], ('Le .miz final', 'DCS', 'Sauvegarder .miz', 'pour que DCS l’ouvre'),
                     ('The final .miz', 'DCS', 'Save .miz', 'so DCS opens it')),
        ],
    },
    'bg': {
        'in': [
            (['S1'], ('Le Wing : l’identité de l’escadre et ses escadrons', 'HQ', 'sans geste', 'pour les en-têtes et les pages de vol'),
                     ('The Wing: the wing’s identity and its squadrons', 'HQ', 'no gesture', 'for the headers and the flight pages')),
            (['S2'], ('La météo, la date et l’heure de la mission ouverte dans HQ', 'HQ', 'assistant METAR › Reprendre de la mission d’HQ (grisé sans mission), puis Insérer dans METAR', 'pour le METAR, la date et l’heure du briefing'),
                     ('The weather, date and time of the mission open in HQ', 'HQ', 'METAR assistant › Take from HQ mission (greyed out without a mission), then Insert into METAR', 'for the METAR, date and time of the briefing')),
            (['C1'], ('L’image de la carte', 'RP, dans la même session', 'RP : Exporter ▾ › Image pour le briefing…, puis BG : Placer', 'pour la carte du briefing'),
                     ('The map image', 'RP, in the same session', 'RP: Export ▾ › Image for the briefing…, then BG: Place', 'for the briefing map')),
            (['F8'], ('La photo composée : un PNG', 'RS', 'RS : Exporter, puis BG : Photos › ajouter l’image, à la main', 'pour les pages de photos du briefing'),
                     ('The composed photo: a PNG', 'RS', 'RS: Export, then BG: Photos › add the image, by hand', 'for the briefing’s photo pages')),
            (['F13'], ('Un ancien briefing .json', 'un fichier', 'Ouvrir ▾ › Ouvrir un briefing…', 'pour reprendre un briefing déjà écrit'),
                      ('An old briefing .json', 'a file', 'Open ▾ › Open a briefing…', 'to resume a briefing already written')),
            (['C2', 'C3'], _WORK_IN_FR, _WORK_IN_EN),
        ],
        'out': [
            (['S3'], ('Le bloc d’informations de la photo', 'RS', 'sans geste, à l’ouverture de RS, champs vides seulement', 'pour préremplir la photo'),
                     ('The photo’s info block', 'RS', 'no gesture, when RS opens, empty fields only', 'to pre-fill the photo')),
            (['S4'], ('Le briefing, vol par vol', 'DG', 'DG : Ouvrir ▾ › Importer… › Briefing en cours', 'pour préremplir une carte par vol'),
                     ('The briefing, flight by flight', 'DG', 'DG: Open ▾ › Import… › Current briefing', 'to pre-fill one card per flight')),
            (['S5'], ('Les vols et leur plan radio', 'RP, DG, FC', 'leur fenêtre d’import › Briefing en cours', 'pour créer les groupes et leurs radios'),
                     ('The flights and their radio plan', 'RP, DG, FC', 'their import window › Current briefing', 'to create the groups and their radios')),
            (['F11'], ('Le briefing : PDF ou PNG', 'l’imprimé', 'Exporter', 'pour le distribuer ou l’imprimer'),
                      ('The briefing: PDF or PNG', 'the printout', 'Export', 'to hand it out or print it')),
            (['C2'], ('Le briefing', 'le fichier de travail', 'Sauvegarder', 'pour le donner aux Flight Leaders'),
                     ('The briefing', 'the work file', 'Save', 'to give it to the Flight Leaders')),
        ],
    },
    'rs': {
        'in': [
            (['S3'], ('Le bloc d’informations de la photo', 'BG', 'sans geste, à l’ouverture de RS, champs vides seulement', 'pour ne pas le ressaisir'),
                     ('The photo’s info block', 'BG', 'no gesture, when RS opens, empty fields only', 'so it need not be typed again')),
            (['S1'], ('Les logos du Wing', 'HQ, fenêtre Wing', 'sans geste', 'pour la grille Logo de la photo'),
                     ('The Wing logos', 'HQ, Wing window', 'no gesture', 'for the photo’s Logo grid')),
            (['C2', 'C3'], ('Le travail rangé : fichier de travail, exemple', 'la suite', 'Ouvrir, Exemple', 'pour reprendre le travail'),
                           ('Stored work: work file, example', 'the suite', 'Open, Example', 'to resume the work')),
        ],
        'out': [
            (['F8'], ('La photo composée : un PNG', 'BG', 'Exporter, puis dans le BG Photos › ajouter l’image, à la main', 'pour les pages de photos du briefing'),
                     ('The composed photo: a PNG', 'BG', 'Export, then in the BG Photos › add the image, by hand', 'for the briefing’s photo pages')),
            (['C2'], ('La composition, sans l’image source', 'le fichier de travail', 'Sauvegarder', 'pour reprendre la photo sans la capture'),
                     ('The composition, without the source image', 'the work file', 'Save', 'to resume the photo without the capture')),
        ],
    },
    'rp': {
        'in': [
            (['S2'], ('Avec le .miz ouvert dans HQ : les groupes de la mission avec leur route', 'HQ', 'Importer des routes… › Mission chargée dans HQ', 'pour partir des routes de la mission'),
                     ('With the .miz open in HQ: the mission groups with their route', 'HQ', 'Import routes… › Mission loaded in HQ', 'to start from the mission routes')),
            _pack_in('rp'),
            (['S5'], ('Les vols du briefing', 'BG', 'Importer des routes… › Briefing en cours', 'pour créer les groupes des routes'),
                     ('The briefing flights', 'BG', 'Import routes… › Current briefing', 'to create the route groups')),
            (['F9'], ('Les points d’une route', 'le Route Tool de DCS, fichier <théâtre>.lua', 'Ouvrir ▾ › Ouvrir une route ou des calques…', 'pour reprendre une route de DCS'),
                     ('The points of a route', 'the DCS Route Tool, <theatre>.lua file', 'Open ▾ › Open a route or layers…', 'to take back a route from DCS')),
            (['F10'], ('Les calques d’un fichier CombatFlite', 'CombatFlite, fichier .cf', 'Ouvrir ▾ › Ouvrir une route ou des calques…, puis Afficher', 'pour les voir sur la carte'),
                      ('The layers of a CombatFlite file', 'CombatFlite, .cf file', 'Open ▾ › Open a route or layers…, then Show', 'to see them on the map')),
            (['F13'], ('Une ancienne route', 'un fichier', 'Ouvrir ▾ › Ouvrir une route ou des calques…', 'pour reprendre une route déjà tracée'),
                      ('An old route', 'a file', 'Open ▾ › Open a route or layers…', 'to resume a route already drawn')),
            (['C2', 'C3'], _WORK_IN_FR, _WORK_IN_EN),
        ] + _share('rp'),
        'out': [
            (['C1'], ('L’image de la carte', 'BG, dans la même session', 'Exporter ▾ › Image pour le briefing… › Exporter', 'pour la carte du briefing'),
                     ('The map image', 'BG, in the same session', 'Export ▾ › Image for the briefing… › Export', 'for the briefing map')),
            (['S8'], ('Les routes : points', 'DG, FC', 'sans geste', 'pour le groupe et la carte'),
                     ('The routes: points', 'DG, FC', 'no gesture', 'for the group and the card')),
            (['S9'], ('La route active et les points de référence', 'DG', 'sans geste', 'pour la carte'),
                     ('The active route and the reference points', 'DG', 'no gesture', 'for the card')),
            (['F9'], ('Les points d’une route', 'le Route Tool de DCS', 'Exporter ▾ › Route Tool…', 'pour donner la route au Route Tool'),
                     ('The points of a route', 'the DCS Route Tool', 'Export ▾ › Route Tool…', 'to give the route to the Route Tool')),
            _work_out_fl('Les routes et leurs calques', 'The routes and their layers'),
        ] + _share('rp'),
    },
    'dg': {
        'in': [
            (['S2'], ('Avec le .miz ouvert dans HQ : les groupes, la date, l’heure, la météo', 'HQ', 'menu … des cartes › Importer des groupes › Mission chargée dans HQ', 'pour créer les cartes et leur météo'),
                     ('With the .miz open in HQ: the groups, the date, the time, the weather', 'HQ', 'cards … menu › Import groups › Mission loaded in HQ', 'to create the cards and their weather')),
            _pack_in('dg'),
            (['S1'], ('L’indicatif et le premier appareil de chaque escadron', 'HQ, fenêtre Wing', 'sans geste', 'pour nommer la carte d’un vol'),
                     ('Each squadron’s call sign and first aircraft', 'HQ, Wing window', 'no gesture', 'to name a flight’s card')),
            (['S4', 'S5'], ('Le briefing, vol par vol', 'BG', 'Ouvrir ▾ › Importer… › Briefing en cours', 'pour préremplir une carte par vol'),
                           ('The briefing, flight by flight', 'BG', 'Open ▾ › Import… › Current briefing', 'to pre-fill one card per flight')),
            (['S8'], ('Les routes : points', 'RP', 'sans geste', 'pour chaque carte'),
                     ('The routes: points', 'RP', 'no gesture', 'for each card')),
            (['S9'], ('La route active et les points de référence', 'RP', 'sans geste', 'pour la carte'),
                     ('The active route and the reference points', 'RP', 'no gesture', 'for the card')),
            (['F13'], ('Une ancienne datacard', 'un fichier', 'Ouvrir ▾ › Ouvrir une datacard…', 'pour reprendre une carte déjà faite'),
                      ('An old datacard', 'a file', 'Open ▾ › Open a datacard…', 'to resume a card already made')),
            (['S10'], ('Le retrait d’un groupe', 'FC', 'Retirer ce groupe', 'pour retirer aussi sa datacard'),
                      ('The removal of a group', 'FC', 'Remove this group', 'to remove its datacard too')),
            (['C2', 'C3'], _WORK_IN_FR, _WORK_IN_EN),
        ] + _share('dg'),
        'out': [
            (['F12'], ('Les datacards : PNG, ZIP ou PDF', 'le kneeboard de DCS, l’imprimé', 'Exporter', 'pour les lire en vol ou les imprimer'),
                      ('The datacards: PNG, ZIP or PDF', 'the DCS kneeboard, the printout', 'Export', 'to read them in flight or print them')),
            (['S8'], ('Une navigation modifiée', 'RP, FC', 'sans geste, dans le tableau Navigation', 'pour que le RP et le groupe suivent la carte'),
                     ('A modified navigation', 'RP, FC', 'no gesture, in the Navigation table', 'so the RP and the group follow the card')),
            (['S10'], ('Le retrait d’une datacard et de son groupe', 'FC', 'Supprimer la datacard et le groupe', 'pour le retirer partout'),
                      ('The removal of a datacard and its group', 'FC', 'Delete the datacard and the group', 'to remove it everywhere')),
            _work_out_fl('Les datacards', 'The datacards'),
        ] + _share('dg'),
    },
    'fc': {
        'in': [
            (['S2'], ('Avec le .miz ouvert dans HQ : les groupes de la mission', 'HQ', 'Importer des groupes… › Mission chargée dans HQ', 'pour créer les groupes'),
                     ('With the .miz open in HQ: the mission groups', 'HQ', 'Import groups… › Mission loaded in HQ', 'to create the groups')),
            (['S2'], ('Avec le .miz : la livrée de chaque unité dans la mission', 'HQ', 'sans geste', 'pour présélectionner la livrée'),
                     ('With the .miz: the livery of each unit in the mission', 'HQ', 'no gesture', 'to preselect the livery')),
            _pack_in('fc'),
            (['S1'], ('Les livrées ajoutées et la livrée par défaut de chaque appareil', 'HQ, fenêtre Wing', 'sans geste', 'pour la liste Livrée de chaque unité'),
                     ('The added liveries and each aircraft’s default livery', 'HQ, Wing window', 'no gesture', 'for each unit’s Livery list')),
            (['S5'], ('Les vols du briefing et leur plan radio', 'BG', 'Importer des groupes… › Briefing en cours', 'pour créer les groupes et leurs radios'),
                     ('The briefing flights and their radio plan', 'BG', 'Import groups… › Current briefing', 'to create the groups and their radios')),
            (['S8'], ('Les routes : points', 'RP', 'sans geste, puis Changer de route', 'pour copier la route dans le groupe'),
                     ('The routes: points', 'RP', 'no gesture, then Change route', 'to copy the route into the group')),
            (['F13'], ('Une ancienne configuration', 'un fichier', 'Ouvrir ▾ › Ouvrir une configuration…', 'pour reprendre une configuration déjà faite'),
                      ('An old configuration', 'a file', 'Open ▾ › Open a configuration…', 'to resume a configuration already made')),
            (['C2', 'C3'], _WORK_IN_FR, _WORK_IN_EN),
        ] + _share('fc'),
        'out': [
            (['F4'], ('Le paquet de vol', 'HQ', 'Exporter, puis dans HQ Paquets de vol', 'pour les écrire dans le .miz : le seul retour'),
                     ('The flight package', 'HQ', 'Export, then in HQ Flight packages', 'to write them into the .miz: the only return')),
            (['S10'], ('Le retrait d’un groupe', 'DG', 'Retirer ce groupe', 'pour le retirer partout'),
                      ('The removal of a group', 'DG', 'Remove this group', 'to remove it everywhere')),
            _work_out_fl('Les groupes', 'The groups'),
        ] + _share('fc'),
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
.fm-xgo { white-space: nowrap; font-size: 11.5px; opacity: .85; }
.fm-xl { color: var(--accent-ink, inherit); text-decoration: underline; text-underline-offset: 2px; }
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
    la section Wing d'Avancé, et ce que lit la fenêtre d'import commune (RP, DG, FC) en plus du DG."""
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
    o.append('          ' + sv_box(504, 296, 160, 42))
    o.append('          ' + T(584, 315, 10.5, 'En-tête · métadonnées', 'Header · metadata'))
    o.append('          ' + T(584, 329, 8, 'opération, date, classification', 'operation, date, classification'))
    o.append('          ' + sv_tag(504, 296, 160, 'S·A', 'S·A'))
    # la mission ouverte dans HQ : la météo va au METAR, la date et l'heure à l'en-tête
    o.append('          ' + sv_box(400, 296, 68, 42, 'hq'))
    o.append('          ' + T(434, 314, 11, 'HQ'))
    o.append('          ' + T(434, 328, 8.5, 'mission', 'mission'))
    o.append('          ' + sv_line(400, 317, 372, 317, M))
    o.append('          ' + T(386, 290, 8, 'météo', 'weather'))
    o.append('          ' + sv_line(468, 317, 502, 317, M))
    o.append('          ' + T(485, 290, 8, 'date · heure', 'date · time'))
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
    o.append('          ' + sv_path('M600,338 C560,352 490,354 446,360', M))
    o.append('          ' + T(540, 362, 8, 'préremplit', 'pre-fills', anchor='start'))
    # la fenêtre d'import commune et le Datacard Generator
    o.append('          ' + sv_box(470, 124, 170, 40))
    o.append('          ' + T(555, 142, 11, 'RP · DG · FC'))
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
    o.append('          ' + sv_path('M300,296 C380,262 480,268 520,244', M, dashed=True))
    o.append('          ' + T(440, 277, 8, 'METAR décodé', 'decoded METAR'))
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
    o.append('          ' + ''.join(f'<circle cx="{cx}" cy="123.5" r="1.3" fill="currentColor"/>' for cx in (248.5, 252.5, 256.5)))
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
        x = 378 + 46 * i
        o.append('          ' + sv_box(x, 102, 46, 16, 'rp' if i == 0 else None))
        o.append('          ' + T(x + 23, 113, 8, fr, en))
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
