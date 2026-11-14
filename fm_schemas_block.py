#!/usr/bin/env python3
"""Bloc « SCHÉMAS DU FIELD MANUAL » : les outils de dessin des schémas (boîtes, flèches, textes FR/EN), le schéma d'ensemble des échanges
(S0, une variante large et une variante en hauteur pour le téléphone), sa légende, les six panneaux « Reçoit · Donne », puis les schémas
redessinés du Briefing Generator, du Route Planner et de la datacard.

Règle de lisibilité (R291) : la couleur d'un module marque son cadre, l'encre écrit ; aucun texte de schéma sous le corps 8.

Chaque flèche, chaque ligne de carte et chaque ligne de panneau porte data-ex="<ids de la table des échanges>" : le build compare les
ids des deux variantes de S0 et vérifie que chaque id de la table est dessiné et qu'il figure dans un panneau.

Usage (par build_field_manual.py) : from fm_schemas_block import *
"""
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

TABLE_IDS = ['S1', 'S2', 'S3', 'S4', 'S5', 'S6', 'S8', 'S9', 'S10', 'S11', 'S12', 'S13',
             'C1', 'C2', 'C3',
             'F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7', 'F8', 'F9', 'F10', 'F11', 'F12', 'F13']

# La légende lettrée de S0 : (lettre, ids, FR, EN). Une lettre = une flèche (ou un groupe de flèches) du schéma.
S0_LEGEND = [
    ('a', ['F1'], f'Le .miz d’origine entre dans HQ : Ouvrir .miz, ou le déposer sur la page.',
                  'The original .miz enters HQ: Open .miz, or drop it on the page.'),
    ('b', ['F3'], f'HQ écrit le .miz final : Sauvegarder .miz.',
                  'HQ writes the final .miz: Save .miz.'),
    ('c', ['F2'], f'Le BG prend la météo d’un .miz : l’assistant METAR.',
                  'The BG takes the weather of a .miz: the METAR assistant.'),
    ('d', ['S1'], f'Le Wing, tout seul : HQ → BG, et aussi FC (livrées) et DG (indicatifs).',
                  'The Wing, by itself: HQ → BG, and also FC (liveries) and DG (call signs).'),
    ('e', ['F7'], f'La configuration Wing en fichier, de HQ vers RS : Exporter config, puis Importer config.',
                  'The Wing configuration as a file, from HQ to RS: Export config, then Import config.'),
    ('f', ['S3'], f'Le BG préremplit RS : opération, date, classification (champs vides seulement).',
                  'The BG pre-fills RS: operation, date, classification (empty fields only).'),
    ('g', ['F8'], f'La photo va de RS au BG à la main : exporter le PNG, l’ajouter aux Photos.',
                  'The photo goes from RS to the BG by hand: export the PNG, add it to Photos.'),
    ('h', ['F11'], f'Le BG imprime : PDF, ou PNG par page.',
                   'The BG prints: PDF, or one PNG per page.'),
    ('i', ['S2'], f'La mission ouverte dans HQ passe au FC, au RP et au DG, tout seule : ce que chacun en prend est dans sa case.',
                  'The mission open in HQ reaches the FC, the RP and the DG by itself: what each takes is in its box.'),
    ('j', ['F5', 'F6'], f'HQ exporte les groupes cochés en paquet, que le FC, le RP et le DG lisent par leur fenêtre d’import.',
                        'HQ exports the ticked groups as a package, which the FC, the RP and the DG read in their import window.'),
    ('k', ['F4'], f'Le FC exporte le paquet de vol ; HQ l’applique au .miz : le seul retour d’un Flight Leader qui se fusionne.',
                  'The FC exports the flight package; HQ applies it to the .miz: the only return from a Flight Leader that merges.'),
    ('l', ['S4', 'S5'], f'Le briefing en cours alimente la fenêtre d’import du FC, du RP et du DG (groupes, plan radio) ; le DG le lit aussi en entier.',
                        'The current briefing feeds the import window of the FC, the RP and the DG (groups, radio plan); the DG also reads all of it.'),
    ('m', ['C1'], f'Le RP envoie l’image de la carte au BG : Exporter ▾ › Image pour le briefing, dans la même session.',
                  'The RP sends the map image to the BG: Export ▾ › Image for the briefing, in the same session.'),
    ('n', ['S6', 'S10', 'S11', 'S12', 'S13'],
     f'FC, RP et DG partagent en direct, dans les deux sens : groupes et leurs unités, radios (fréquences, canaux à imprimer), théâtre, unités de mesure, cap (RP, DG). Retirer un groupe retire sa datacard.',
     'FC, RP and DG share live, both ways: groups and their units, radios (frequencies, channels to print), theatre, measurement units, heading (RP, DG). Removing a group removes its datacard.'),
    ('o', ['S8', 'S9'], f'Le RP donne ses routes au FC et au DG, et au DG la route active et les points de référence.',
                        'The RP gives its routes to the FC and the DG, and to the DG the active route and the reference points.'),
    ('p', ['F9'], f'Le RP lit et écrit le fichier .lua du Route Tool de DCS.',
                  'The RP reads and writes the .lua file of the DCS Route Tool.'),
    ('q', ['F10'], f'Le RP ouvre un fichier .cf de CombatFlite (calques).',
                   'The RP opens a CombatFlite .cf file (layers).'),
    ('r', ['F12'], f'Le DG exporte la datacard : PNG pour le kneeboard, PDF pour imprimer.',
                   'The DG exports the datacard: PNG for the kneeboard, PDF for printing.'),
    ('s', ['C2'], f'Le fichier de travail : Sauvegarder (chaque outil sauf HQ), Ouvrir (remplace tout). Il ne porte ni la mission d’HQ ni le Wing.',
                  'The work file: Save (every tool except HQ), Open (replaces everything). It carries neither the HQ mission nor the Wing.'),
    ('t', ['C3'], f'Exemple ▾ charge l’exemple par groupe d’outils.',
                  'Example ▾ loads the example by group of tools.'),
]

S0_STEPS = [
    (1, f'Mission Commander, HQ : le Wing une fois pour toutes, puis Ouvrir .miz.',
        'Mission Commander, HQ: the Wing once and for all, then Open .miz.'),
    (2, f'Mission Commander : le briefing au BG, la photo à RS (puis à la main au BG).',
        'Mission Commander: the briefing in the BG, the photo in RS (then by hand into the BG).'),
    (3, f'Sauvegarder le fichier de travail et l’envoyer aux Flight Leaders (avec le .miz s’ils veulent ses groupes).',
        'Save the work file and send it to the Flight Leaders (with the .miz if they want its groups).'),
    (4, f'Flight Leader : Ouvrir le fichier, puis le RP, le FC et le DG, qui partagent tout en direct.',
        'Flight Leader: Open the file, then the RP, the FC and the DG, which share everything live.'),
    (5, f'Flight Leader : le FC exporte le paquet de vol et le rend au Mission Commander.',
        'Flight Leader: the FC exports the flight package and hands it back to the Mission Commander.'),
    (6, f'Mission Commander : dans HQ, Paquets de vol › Appliquer, puis Sauvegarder .miz : le .miz final.',
        'Mission Commander: in HQ, Flight packages › Apply, then Save .miz: the final .miz.'),
]


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

# Ce que chaque Flight Leader prend, dans sa case : (ids, [lignes FR], [lignes EN])
CARDS = {
    'fc': [
        (['S2'], [f'.miz d’HQ{NF}: groupes,', 'livrées, déclinaison'], ['HQ .miz: groups,', 'liveries, declination']),
        (['S1'], [f'Wing{NF}: livrées'], ['Wing: liveries']),
        (['S5'], [f'briefing{NF}: groupes,', 'fréquences'], ['briefing: groups,', 'frequencies']),
    ],
    'rp': [
        (['S2'], [f'.miz d’HQ{NF}: groupes,', 'déclinaison'], ['HQ .miz: groups,', 'declination']),
        (['S5'], [f'briefing{NF}: groupes'], ['briefing: groups']),
    ],
    'dg': [
        (['S2'], [f'.miz d’HQ{NF}: groupes,', 'date, heure, météo,', 'déclinaison'], ['HQ .miz: groups,', 'date, time, weather,', 'declination']),
        (['S1'], [f'Wing{NF}: indicatifs'], ['Wing: call signs']),
        (['S4', 'S5'], [f'briefing{NF}: tout'], ['briefing: all']),
    ],
}


class _S:
    """Un schéma en construction : les éléments, le marqueur, les ids dessinés."""
    def __init__(self, w, h, marker, aria_fr, aria_en, cls):
        self.o = []
        self.w, self.h, self.m, self.cls = w, h, marker, cls
        self.aria = (aria_fr, aria_en)
        self.ids = set()

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

    def arrow(self, ex, d, dashed=False, both=False, badge=None, bd=None):
        """Une flèche : le chemin d, ses ids, sa lettre (badge) posée en bd=(x, y)."""
        self.ids.update(ex)
        p = (f'<path d="{d}" fill="none" stroke="currentColor" stroke-width="1.4" opacity=".85"'
             + (' stroke-dasharray="4 3"' if dashed else '') + f' marker-end="url(#{self.m})"'
             + (f' marker-start="url(#{self.m})"' if both else '') + '/>')
        g = f'<g class="sv-ar" data-ex="{" ".join(ex)}">{p}'
        if badge and bd:
            g += self._badge(bd[0], bd[1], badge)
        self.add(g + '</g>')

    def badge_only(self, ex, x, y, letter):
        self.ids.update(ex)
        self.add(f'<g class="sv-ar" data-ex="{" ".join(ex)}">{self._badge(x, y, letter)}</g>')

    def _badge(self, x, y, letter):
        return (f'<rect class="sv-bd" x="{_n(x - 7)}" y="{_n(y - 7)}" width="14" height="14" rx="3"/>'
                + sv_text(x, y + 3.6, 10, letter, extra=' font-weight="700"'))

    def step(self, x, y, n):
        self.add(f'<circle class="sv-pill" cx="{_n(x)}" cy="{_n(y)}" r="8.5"/>')
        self.T(x, y + 3.6, 10.5, str(n), cls='sv-pill-t', extra=' font-weight="700"')

    def module(self, key, x, y, w, h, card=False):
        mono, fr, en = MODS[key]
        self.box(x, y, w, h, key)
        cx = x + w / 2
        self.T(cx, y + 22, 16, mono)
        self.T(cx, y + 38, 10, fr, en)
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


def build_s0_wide():
    s = _S(720, 650, 's0w', 'Le schéma d’ensemble de la suite : qui reçoit quoi, de qui', 'The suite map: who receives what, from whom', 's0-wide')
    A = s.arrow
    # les cadres, leurs titres (en bas à droite : le haut et la gauche portent des flèches)
    s.frame(8, 62, 588, 184)
    s.T(588, 238, 10.5, 'MISSION COMMANDER', anchor='end', ls=1.5)
    s.frame(8, 340, 588, 226)
    s.T(588, 558, 10.5, 'FLIGHT LEADER', anchor='end', ls=1.5)
    # « Exemple ▾ » : un jeton par cadre
    for fy, fr, en, ex in ((66, f'Exemple ▾ → BG · RS', 'Example ▾ → BG · RS', ['C3']), (344, 'Exemple ▾ → RP · FC · DG', 'Example ▾ → RP · FC · DG', ['C3'])):
        s.ids.update(ex)
        s.add(f'<g data-ex="C3"><rect class="sv-chip" x="396" y="{fy}" width="192" height="16" rx="8"/>')
        s.add(sv_text(492, fy + 11.5, 9.5, fr, en) + '</g>')
    # les six modules
    cols = (41, 227, 413)
    MCy, FLy = 104, 362
    s.module('hq', cols[0], MCy, 150, 62)
    s.module('bg', cols[1], MCy, 150, 62)
    s.module('rs', cols[2], MCy, 150, 62)
    s.module('fc', cols[0], FLy, 150, 116, card=True)
    s.module('rp', cols[1], FLy, 150, 116, card=True)
    s.module('dg', cols[2], FLy, 150, 116, card=True)
    # hors de la suite
    s.ext(41, 8, 150, 30, [('Éditeur de DCS', 'DCS editor')])
    s.ext(282, 8, 150, 30, [('Imprimés · PDF, PNG', 'Printouts · PDF, PNG')], 10)
    s.ext(187, 596, 100, 34, [('CombatFlite', 'CombatFlite'), ('.cf', '.cf')], 10)
    s.ext(307, 596, 100, 34, [('Route Tool', 'Route Tool'), ('.lua', '.lua')], 10)
    s.ext(413, 596, 150, 34, [('Kneeboard · imprimé', 'Kneeboard · printout')], 10)
    # Mission Commander : entrées, sorties
    A(['F1'], 'M80,38 L80,104', True, badge='a', bd=(80, 52))
    A(['F3'], 'M116,104 L116,38', True, badge='b', bd=(116, 52))
    A(['F2'], 'M191,23 L252,23 L252,104', True, badge='c', bd=(222, 23))
    A(['F11'], 'M330,104 L330,38', True, badge='h', bd=(330, 52))
    A(['F7'], 'M160,104 L160,91 L470,91 L470,104', True, badge='e', bd=(400, 91))
    A(['S1'], 'M191,136 L227,136', badge='d', bd=(209, 122))
    A(['S3'], 'M377,126 L413,126', badge='f', bd=(395, 112))
    A(['F8'], 'M413,148 L377,148', True, badge='g', bd=(395, 162))
    # du Mission Commander au Flight Leader
    A(['S2'], 'M88,166 L88,340', badge='i', bd=(88, 292))
    A(['F5', 'F6'], 'M128,166 L128,340', True, badge='j', bd=(128, 292))
    A(['F4'], 'M168,362 L168,166', True, badge='k', bd=(168, 292))
    A(['S4', 'S5'], 'M262,166 L262,340', badge='l', bd=(262, 292))
    A(['C1'], 'M342,362 L342,166', badge='m', bd=(342, 292))
    # le fichier de travail
    s.ids.add('C2')
    s.add('<g data-ex="C2">')
    s.box(606, 266, 106, 62)
    s.T(659, 286, 10.5, 'Fichier de', 'Work')
    s.T(659, 299, 10.5, 'travail', 'file')
    s.T(659, 318, 9.5, 'hors HQ', 'not HQ')
    s.add('</g>')
    A(['C2'], 'M659,266 L659,205 L598,205', False, both=True, badge='s', bd=(659, 236))
    A(['C2'], 'M659,328 L659,445 L598,445', False, both=True, badge='s', bd=(659, 390))
    # le Flight Leader : hors de la suite (les flèches passent derrière la barre)
    A(['F10'], 'M237,596 L237,478', True, badge='q', bd=(237, 574))
    A(['F9'], 'M357,596 L357,478', True, both=True, badge='p', bd=(357, 574))
    A(['F12'], 'M450,478 L450,596', True, badge='r', bd=(450, 574))
    # le Flight Leader : ce qui est partagé, dans les deux sens
    s.ids.update(['S6', 'S10', 'S11', 'S12', 'S13'])
    s.add('<g data-ex="S6 S10 S11 S12 S13">')
    s.box(41, 498, 522, 40)
    s.T(302, 514, 10, f'groupes · unités · radios (fréquences, canaux à imprimer)', 'groups · units · radios (frequencies, channels to print)')
    s.T(302, 529, 10, f'théâtre · unités de mesure · cap (RP, DG)', 'theatre · measurement units · heading (RP, DG)')
    s.add('</g>')
    for cx in (116, 302, 488):
        A(['S6', 'S11', 'S12'], f'M{cx},478 L{cx},498', False, both=True)
    s.badge_only(['S6', 'S10', 'S11', 'S12', 'S13'], 302 - 150, 498, 'n')
    A(['S8', 'S9'], 'M227,440 L191,440', badge='o', bd=(209, 426))
    A(['S8', 'S9'], 'M377,440 L413,440', badge='o', bd=(395, 426))
    # les étapes du travail type
    for (x, y, n) in ((41, 104, 1), (227, 104, 2), (413, 104, 2), (606, 266, 3), (41, 362, 4), (227, 362, 4), (413, 362, 4), (168, 214, 5), (116, 80, 6)):
        s.step(x, y, n)
    return s


def build_s0_tall():
    s = _S(320, 1034, 's0t', 'Le schéma d’ensemble de la suite : qui reçoit quoi, de qui', 'The suite map: who receives what, from whom', 's0-tall')
    A = s.arrow
    mx, mw = 85, 150
    HQy, BGy, RSy = 92, 192, 292
    FCy, RPy, DGy = 500, 660, 820
    s.frame(4, 52, 312, 322)
    s.frame(4, 452, 312, 498)
    # les titres et le jeton de l'exemple, en tête de cadre
    s.T(30, 66, 10.5, 'MISSION COMMANDER', anchor='start', ls=1.5)
    s.T(84, 466, 10.5, 'FLIGHT LEADER', anchor='start', ls=1.5)
    s.ids.add('C3')
    s.add('<g data-ex="C3">' + sv_text(30, 80, 9.5, 'Exemple ▾ → BG · RS', 'Example ▾ → BG · RS', anchor='start') + '</g>')
    s.add('<g data-ex="C3">' + sv_text(84, 480, 9.5, 'Exemple ▾ → RP · FC · DG', 'Example ▾ → RP · FC · DG', anchor='start') + '</g>')
    s.module('hq', mx, HQy, mw, 62)
    s.module('bg', mx, BGy, mw, 62)
    s.module('rs', mx, RSy, mw, 62)
    s.module('fc', mx, FCy, mw, 116, card=True)
    s.module('rp', mx, RPy, mw, 116, card=True)
    s.module('dg', mx, DGy, mw, 116, card=True)
    s.ext(160, 6, 152, 30, [('Éditeur de DCS', 'DCS editor')])
    s.ext(8, 6, 124, 30, [('Imprimés', 'Printouts')], 10)
    s.ext(8, 976, 96, 40, [('CombatFlite', 'CombatFlite'), ('.cf', '.cf')], 10)
    s.ext(112, 976, 96, 40, [('Route Tool', 'Route Tool'), ('.lua', '.lua')], 10)
    s.ext(216, 976, 96, 40, [('Kneeboard', 'Kneeboard'), ('imprimé', 'printout')], 10)
    # Mission Commander : entrées et sorties
    A(['F1'], f'M185,36 L185,{HQy}', True, badge='a', bd=(185, 56))
    A(['F3'], f'M213,{HQy} L213,36', True, badge='b', bd=(213, 48))
    A(['F2'], f'M290,36 L290,{BGy + 10} L{mx + mw},{BGy + 10}', True, badge='c', bd=(290, 130))
    A(['F11'], f'M{mx},{BGy + 20} L20,{BGy + 20} L20,36', True, badge='h', bd=(20, 120))
    A(['F7'], f'M{mx + mw},{HQy + 36} L270,{HQy + 36} L270,{RSy + 30} L{mx + mw},{RSy + 30}', True, badge='e', bd=(270, 270))
    A(['S1'], f'M{mx + 40},{HQy + 62} L{mx + 40},{BGy}', badge='d', bd=(mx + 40, 177))
    A(['S3'], f'M{mx + 40},{BGy + 62} L{mx + 40},{RSy}', badge='f', bd=(mx + 40, 277))
    A(['F8'], f'M{mx + 110},{RSy} L{mx + 110},{BGy + 62}', True, badge='g', bd=(mx + 110, 277))
    # du Mission Commander au Flight Leader : le côté gauche
    A(['S2'], f'M{mx},{HQy + 14} L34,{HQy + 14} L34,452', badge='i', bd=(34, 410))
    A(['F5', 'F6'], f'M{mx},{HQy + 24} L50,{HQy + 24} L50,452', True, badge='j', bd=(50, 395))
    A(['F4'], f'M{mx},{FCy + 40} L66,{FCy + 40} L66,{HQy + 36} L{mx},{HQy + 36}', True, badge='k', bd=(66, 380))
    A(['S4', 'S5'], f'M{mx},{BGy + 46} L73,{BGy + 46} L73,452', badge='l', bd=(73, 425))
    # l'image de carte : le côté droit
    A(['C1'], f'M{mx + mw},{RPy + 30} L250,{RPy + 30} L250,{BGy + 36} L{mx + mw},{BGy + 36}', badge='m', bd=(250, 420))
    # le fichier de travail
    s.ids.add('C2')
    s.add('<g data-ex="C2">')
    s.box(mx, 392, mw, 46)
    s.T(mx + mw / 2, 410, 10.5, 'Fichier de travail', 'Work file')
    s.T(mx + mw / 2, 427, 9.5, 'hors HQ', 'not HQ')
    s.add('</g>')
    A(['C2'], f'M{mx + 75},392 L{mx + 75},374', False, both=True, badge='s', bd=(mx + 100, 383))
    A(['C2'], f'M{mx + 75},438 L{mx + 75},452', False, both=True, badge='s', bd=(mx + 100, 445))
    # le Flight Leader : hors de la suite (les flèches passent derrière la barre ou les modules, jamais dessus)
    A(['F10'], f'M56,976 L56,958 L274,958 L274,{RPy + 90} L{mx + mw},{RPy + 90}', True, badge='q', bd=(110, 958))
    A(['F9'], f'M160,976 L160,966 L262,966 L262,{RPy + 60} L{mx + mw},{RPy + 60}', True, both=True, badge='p', bd=(212, 966))
    A(['F12'], f'M{mx + mw},{DGy + 80} L288,{DGy + 80} L288,976', True, badge='r', bd=(288, 940))
    # le Flight Leader : ce qui est partagé, dans les deux sens (la barre à gauche, tournée)
    s.ids.update(['S6', 'S10', 'S11', 'S12', 'S13'])
    s.add('<g data-ex="S6 S10 S11 S12 S13">')
    s.add('<rect class="sv-box" x="14" y="510" width="22" height="420" rx="3" stroke="currentColor" stroke-width="1.4"/>')
    s.add(sv_text(0, 0, 10, 'groupes · unités · radios · théâtre · unités de mesure · cap',
                  'groups · units · radios · theatre · measurement units · heading', extra=' transform="translate(29 720) rotate(-90)"'))
    s.add('</g>')
    for ty in (FCy + 80, RPy + 20, DGy + 80):
        A(['S6', 'S11', 'S12'], f'M{mx},{ty} L36,{ty}', False, both=True)
    s.badge_only(['S6', 'S10', 'S11', 'S12', 'S13'], 25, 498, 'n')
    A(['S8', 'S9'], f'M{mx + 110},{RPy} L{mx + 110},{FCy + 116}', badge='o', bd=(mx + 110, 638))
    A(['S8', 'S9'], f'M{mx + 110},{RPy + 116} L{mx + 110},{DGy}', badge='o', bd=(mx + 110, 798))
    for (x, y, n) in ((mx, HQy, 1), (mx, BGy, 2), (mx, RSy, 2), (mx, 392, 3), (mx, FCy, 4), (mx, RPy, 4), (mx, DGy, 4), (66, 330, 5), (213, 70, 6)):
        s.step(x, y, n)
    return s


def s0_legend_html():
    """La légende lettrée de S0 et les six étapes, sous le schéma."""
    li_fr = ''.join(f'<li data-ex="{" ".join(ids)}"><span class="xb">{l}</span> {fr_typo(fr)}</li>' for l, ids, fr, en in S0_LEGEND)
    li_en = ''.join(f'<li data-ex="{" ".join(ids)}"><span class="xb">{l}</span> {en}</li>' for l, ids, fr, en in S0_LEGEND)
    st_fr = ''.join(f'<li><span class="xs">{n}</span> {fr_typo(fr)}</li>' for n, fr, en in S0_STEPS)
    st_en = ''.join(f'<li><span class="xs">{n}</span> {en}</li>' for n, fr, en in S0_STEPS)
    return (f'<div class="fm-xlegend">'
            f'<div class="lang-block" data-lang="fr"><h4>Les flèches</h4><p class="fm-xkey">Trait plein{NF}: en direct, dans la suite. Tireté{NF}: par un fichier ou à la main.</p><ul>{li_fr}</ul>'
            f'<h4>Le travail, dans l’ordre</h4><ul>{st_fr}</ul></div>'
            f'<div class="lang-block" data-lang="en"><h4>The arrows</h4><p class="fm-xkey">Solid line: live, inside the suite. Dashed: by a file or by hand.</p><ul>{li_en}</ul>'
            f'<h4>The work, in order</h4><ul>{st_en}</ul></div></div>')


def s0_html():
    w, t = build_s0_wide(), build_s0_tall()
    assert w.ids == t.ids, ('S0 : les deux variantes ne portent pas les mêmes ids', sorted(w.ids ^ t.ids))
    missing = [i for i in TABLE_IDS if i not in w.ids and i not in ('F13',)]
    assert not missing, ('S0 : ids de la table non dessinés', missing)
    cap_fr = 'Fig. 1 — La suite d’un coup d’œil : ce que chaque outil prend et donne, dans son sens, avec le travail sauvegardé et rechargé.'
    cap_en = 'Fig. 1 — The suite at a glance: what each tool takes and gives, in its direction, with the work saved and reloaded.'
    return (f'<div class="fm-schema fm-s0">\n        {w.svg()}\n        {t.svg()}\n'
            f'        <div class="fm-schema-legend">\n'
            f'          <span class="lang-block" data-lang="fr">{cap_fr}</span>\n'
            f'          <span class="lang-block" data-lang="en">{cap_en}</span>\n'
            f'        </div>\n      </div>\n' + s0_legend_html()), w.ids


# ═════════════════════════════════════════════════════════════════════════════════
# Les six panneaux « Reçoit · Donne »
# ═════════════════════════════════════════════════════════════════════════════════
# Une ligne : (ids, ce qui passe, de / vers quel outil, par quel geste) en FR puis en EN.

PANELS = {
    'hq': {
        'in': [
            (['F1'], ('Le .miz d’origine', 'l’éditeur de DCS', 'Ouvrir .miz, ou le déposer'), ('The original .miz', 'the DCS editor', 'Open .miz, or drop it')),
            (['F4'], ('Les paquets de vol', 'le FC', 'Paquets de vol › Importer'), ('Flight packages', 'the FC', 'Flight packages › Import')),
            (['F7'], ('Une configuration Wing', 'un autre HQ', 'Wing › Importer config'), ('A Wing configuration', 'another HQ', 'Wing › Import config')),
        ],
        'out': [
            (['S1'], ('Le Wing', 'BG, FC, DG', 'tout seul'), ('The Wing', 'BG, FC, DG', 'by itself')),
            (['S2'], ('La mission ouverte', 'FC, RP, DG', 'tout seul'), ('The open mission', 'FC, RP, DG', 'by itself')),
            (['F5', 'F6'], ('Un paquet des groupes cochés', 'FC, RP, DG', '📦 Exporter, puis leur fenêtre d’import'), ('A package of the ticked groups', 'FC, RP, DG', '📦 Export, then their import window')),
            (['F7'], ('La configuration Wing', 'RS, un autre HQ', 'Wing › Exporter config'), ('The Wing configuration', 'RS, another HQ', 'Wing › Export config')),
            (['F3'], ('Le .miz final', 'l’éditeur de DCS', 'Sauvegarder .miz'), ('The final .miz', 'the DCS editor', 'Save .miz')),
        ],
    },
    'bg': {
        'in': [
            (['S1'], ('Le Wing', 'HQ', 'tout seul'), ('The Wing', 'HQ', 'by itself')),
            (['F2'], ('La météo d’un .miz', 'l’éditeur de DCS', 'assistant METAR'), ('The weather of a .miz', 'the DCS editor', 'METAR assistant')),
            (['C1'], ('L’image de la carte', 'RP', 'Exporter ▾ › Image pour le briefing'), ('The map image', 'RP', 'Export ▾ › Image for the briefing')),
            (['F8'], ('La photo', 'RS', 'à la main : Photos'), ('The photo', 'RS', 'by hand: Photos')),
            (['F13'], ('Un ancien briefing', 'un fichier', 'Ouvrir ▾'), ('An old briefing', 'a file', 'Open ▾')),
        ],
        'out': [
            (['S3'], ('Opération, date, classification', 'RS', 'à l’ouverture de RS'), ('Operation, date, classification', 'RS', 'when RS opens')),
            (['S4'], ('Le briefing en entier', 'DG', 'Importer… › Briefing en cours'), ('The whole briefing', 'DG', 'Import… › Current briefing')),
            (['S5'], ('Groupes, nombre, type, plan radio', 'FC, RP, DG', 'leur fenêtre d’import'), ('Groups, count, type, radio plan', 'FC, RP, DG', 'their import window')),
            (['F11'], ('PDF et PNG', 'l’imprimé', 'Exporter'), ('PDF and PNG', 'the printout', 'Export')),
        ],
    },
    'rs': {
        'in': [
            (['S3'], ('Opération, date, classification', 'BG', 'à l’ouverture, champs vides seulement'), ('Operation, date, classification', 'BG', 'when it opens, empty fields only')),
            (['F7'], ('La configuration Wing (logos)', 'HQ', 'Logo › Importer config'), ('The Wing configuration (logos)', 'HQ', 'Logo › Import config')),
            (['C2', 'C3', 'F13'], ('Le fichier de travail, l’exemple', 'la suite', 'Ouvrir ▾, Exemple ▾'), ('The work file, the example', 'the suite', 'Open ▾, Example ▾')),
        ],
        'out': [
            (['F8'], ('La photo en PNG', 'BG', 'Exporter, puis à la main'), ('The photo as PNG', 'BG', 'Export, then by hand')),
            (['C2'], ('Le fichier de travail', 'la suite', 'Sauvegarder'), ('The work file', 'the suite', 'Save')),
        ],
    },
    'fc': {
        'in': [
            (['S2'], ('Groupes : route, radios, emport, livrées', 'HQ', 'Importer des groupes… › mission d’HQ'), ('Groups: route, radios, loadout, liveries', 'HQ', 'Import groups… › HQ mission')),
            (['S1'], ('Les livrées du Wing', 'HQ', 'tout seul'), ('The Wing liveries', 'HQ', 'by itself')),
            (['S5'], ('Groupes, plan radio', 'BG', 'Importer des groupes… › briefing en cours'), ('Groups, radio plan', 'BG', 'Import groups… › current briefing')),
            (['F5', 'F6'], ('Un paquet, un briefing en fichier', 'HQ, un autre FC', 'Importer des groupes… › fichier'), ('A package, a briefing file', 'HQ, another FC', 'Import groups… › file')),
            (['S8'], ('Les routes', 'RP', 'choisir la route du groupe'), ('The routes', 'RP', 'pick the group’s route')),
            (['S6', 'S10', 'S11', 'S12'], ('Groupes, unités, radios (fréquences, canaux à imprimer), théâtre, unités de mesure', 'RP, DG', 'tout seul, dans les deux sens'), ('Groups, units, radios (frequencies, channels to print), theatre, measurement units', 'RP, DG', 'by itself, both ways')),
            (['C2', 'C3', 'F13'], ('Le fichier de travail, l’exemple, un ancien fichier', 'la suite', 'Ouvrir ▾, Exemple ▾'), ('The work file, the example, an old file', 'the suite', 'Open ▾, Example ▾')),
        ],
        'out': [
            (['F4'], ('Le paquet de vol', 'HQ', 'Exporter, puis Paquets de vol'), ('The flight package', 'HQ', 'Export, then Flight packages')),
            (['S6', 'S10', 'S11', 'S12'], ('Groupes, unités, radios (fréquences, canaux à imprimer), théâtre, unités de mesure', 'RP, DG', 'tout seul, dans les deux sens'), ('Groups, units, radios (frequencies, channels to print), theatre, measurement units', 'RP, DG', 'by itself, both ways')),
            (['C2'], ('Le fichier de travail', 'la suite', 'Sauvegarder'), ('The work file', 'the suite', 'Save')),
        ],
    },
    'rp': {
        'in': [
            (['S2'], ('Groupes et routes, la date pour la déclinaison', 'HQ', 'Importer des routes… › mission d’HQ'), ('Groups and routes, the date for the declination', 'HQ', 'Import routes… › HQ mission')),
            (['S5'], ('Groupes et routes', 'BG', 'Importer des routes… › briefing en cours'), ('Groups and routes', 'BG', 'Import routes… › current briefing')),
            (['F5', 'F6'], ('Un paquet', 'HQ, FC', 'Importer des routes… › fichier'), ('A package', 'HQ, FC', 'Import routes… › file')),
            (['F9'], ('Des routes', 'Route Tool de DCS (.lua)', 'Ouvrir ▾ › Ouvrir une route…'), ('Routes', 'DCS Route Tool (.lua)', 'Open ▾ › Open a route…')),
            (['F10'], ('Des calques', 'CombatFlite (.cf)', 'Ouvrir ▾ › Ouvrir une route…'), ('Layers', 'CombatFlite (.cf)', 'Open ▾ › Open a route…')),
            (['S6', 'S10', 'S11', 'S12', 'S13'], ('Groupes, unités, radios, théâtre, unités de mesure, cap', 'FC, DG', 'tout seul, dans les deux sens'), ('Groups, units, radios, theatre, measurement units, heading', 'FC, DG', 'by itself, both ways')),
            (['C2', 'C3', 'F13'], ('Le fichier de travail, l’exemple, un ancien fichier', 'la suite', 'Ouvrir ▾, Exemple ▾'), ('The work file, the example, an old file', 'the suite', 'Open ▾, Example ▾')),
        ],
        'out': [
            (['C1'], ('L’image de la carte', 'BG', 'Exporter ▾ › Image pour le briefing'), ('The map image', 'BG', 'Export ▾ › Image for the briefing')),
            (['S8'], ('Les routes', 'FC, DG', 'tout seul'), ('The routes', 'FC, DG', 'by itself')),
            (['S9'], ('La route active, les points de réf.', 'DG', 'tout seul'), ('The active route, the reference points', 'DG', 'by itself')),
            (['S6', 'S10', 'S11', 'S12', 'S13'], ('Groupes, unités, radios, théâtre, unités de mesure, cap', 'FC, DG', 'tout seul, dans les deux sens'), ('Groups, units, radios, theatre, measurement units, heading', 'FC, DG', 'by itself, both ways')),
            (['F9'], ('Un fichier .lua', 'Route Tool de DCS', 'Exporter ▾ › Route Tool…'), ('A .lua file', 'DCS Route Tool', 'Export ▾ › Route Tool…')),
            (['C2'], ('Le fichier de travail', 'la suite', 'Sauvegarder'), ('The work file', 'the suite', 'Save')),
        ],
    },
    'dg': {
        'in': [
            (['S2'], ('Groupes, date, heure, météo', 'HQ', '… › Importer des groupes'), ('Groups, date, time, weather', 'HQ', '… › Import groups')),
            (['S1'], ('Les indicatifs des escadrons', 'HQ (Wing)', 'tout seul'), ('The squadron call signs', 'HQ (Wing)', 'by itself')),
            (['S4', 'S5'], ('Le briefing', 'BG', 'Importer… › Briefing en cours'), ('The briefing', 'BG', 'Import… › Current briefing')),
            (['F5', 'F6'], ('Un paquet', 'HQ, FC', '… › Importer des groupes › fichier'), ('A package', 'HQ, FC', '… › Import groups › file')),
            (['S8', 'S9'], ('Les routes, la route active, les points de réf.', 'RP', 'tout seul'), ('The routes, the active route, the reference points', 'RP', 'by itself')),
            (['S6', 'S10', 'S11', 'S12', 'S13'], ('Groupes, unités, radios (fréquences, canaux à imprimer), théâtre, unités de mesure, cap', 'FC, RP', 'tout seul, dans les deux sens'), ('Groups, units, radios (frequencies, channels to print), theatre, measurement units, heading', 'FC, RP', 'by itself, both ways')),
            (['C2', 'C3', 'F13'], ('Le fichier de travail, l’exemple, un ancien fichier', 'la suite', 'Ouvrir ▾, Exemple ▾'), ('The work file, the example, an old file', 'the suite', 'Open ▾, Example ▾')),
        ],
        'out': [
            (['S6', 'S10', 'S11', 'S12', 'S13'], ('Groupes, unités, radios (fréquences, canaux à imprimer), théâtre, unités de mesure, cap', 'FC, RP', 'tout seul, dans les deux sens'), ('Groups, units, radios (frequencies, channels to print), theatre, measurement units, heading', 'FC, RP', 'by itself, both ways')),
            (['S8'], ('Une navigation modifiée', 'RP, FC', 'tout seul'), ('A modified navigation', 'RP, FC', 'by itself')),
            (['F12'], ('La datacard en PNG ou PDF', 'kneeboard, imprimé', 'Exporter'), ('The datacard as PNG or PDF', 'kneeboard, printout', 'Export')),
            (['C2'], ('Le fichier de travail', 'la suite', 'Sauvegarder'), ('The work file', 'the suite', 'Save')),
        ],
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
                f'<li data-ex="{" ".join(r[0])}"><strong>{_esc(T(r[1][i][0]))}</strong> — {_esc(T(r[1][i][1]))} — <span class="rd-g">{_esc(T(r[1][i][2]))}</span></li>'
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
    o.append('          ' + sv_line(64, 108, 64, 126, M))
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
    # la barre du haut : des groupes de boutons, sans leurs libellés exacts
    o.append('          ' + sv_box(110, 44, 500, 26))
    o.append('          ' + T(118, 61, 8.5, 'RP', anchor='start', ls=1))
    for x, w, fr, en in ((146, 96, 'Fichiers', 'Files'), (250, 66, 'Affichage', 'Display'), (324, 66, 'Théâtre', 'Theatre'),
                         (398, 66, 'Exemple', 'Example'), (472, 66, 'Effacer', 'Clear')):
        o.append('          ' + f'<rect x="{x}" y="49" width="{w}" height="16" rx="2" fill="none" stroke="currentColor" stroke-width="1" opacity=".6"/>')
        o.append('          ' + T(x + w / 2, 60.5, 8, fr, en))
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
        x = 404 + 40 * i
        o.append('          ' + sv_box(x, 102, 40, 16, 'rp' if i == 0 else None))
        o.append('          ' + T(x + 20, 113, 8, fr, en))
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
