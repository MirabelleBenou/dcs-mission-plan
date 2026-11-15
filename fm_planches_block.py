#!/usr/bin/env python3
"""Bloc « PLANCHES D'ÉCRAN DU FIELD MANUAL » : les aides de dessin communes aux planches (bulle et amorce, bouton, champ, icône de repli,
chevron, carte de groupe, titre, légende numérotée, figure), le CSS générique d'une planche, et le contrôle des libellés.

Une planche est l'écran d'un outil redessiné au trait : une variante large (viewBox 720 de large) et une variante haute (360 de large, sous 700 px),
des bulles numérotées, une légende numérotée.

Règle des libellés : tout texte dessiné (chaque <text> du SVG) est écrit par une fonction qui dit son genre.
  - L(outil, clé, …)  un libellé de l'outil : le texte vient du dictionnaire FR et EN de l'outil, lu au build dans son source
                      (sans l'exécuter, sans lire dist/). Transformations permises, et elles seules : la casse (up), un gabarit {0} {1} {n} {x}
                      rempli d'une valeur d'exemple (args), un pictogramme de tête retiré (icon), « ▾ » ou « … » ajouté (add).
  - D(fr, en)         une donnée d'exemple (nom de groupe, type d'appareil, date, heure, fréquence, METAR, compte, nom de fichier, empreinte, sigle,
                      pictogramme), écrite en clair.
  - M(fr, en)         un titre du manuel (titre de planche, titre d'une ligne de légende), écrit en clair.
Le build du FM s'arrête (comme ses autres contrôles) si une clé manque en FR ou en EN, et si un <text> d'une planche n'est passé par aucune de ces fonctions.

Usage (par build_field_manual.py) : from fm_planches_block import *
"""
import ast
import html
import os
import re

from fm_schemas_block import sv_text, sv_box, sv_defs, _n, _esc, fr_typo

HERE = os.path.dirname(os.path.abspath(__file__))

# L'erreur d'une planche ne s'élève pas : elle s'inscrit ici, et le build du FM sort en 1 une fois tous ses contrôles écrits.
PLANCHE_ERRORS = []
PLATES = []          # les planches construites, pour le compte rendu du build

TOOL_SOURCES = {'hq': 'build_hq.py', 'fc': 'build_flight_configurator.py', 'dg': 'build_datacard_generator.py'}
TOOL_NAMES = {'hq': 'HQ', 'fc': 'Flight Configurator', 'dg': 'Datacard Generator'}


# ═════════════════════════════════════════════════════════════════════════════════
# Les dictionnaires des outils, lus dans leur source (jamais exécuté, jamais dist/)
# ═════════════════════════════════════════════════════════════════════════════════

def _js_str_at(s, i):
    """Le littéral de chaîne JS qui commence en s[i] (' ou ") : (texte, indice après le guillemet fermant)."""
    q = s[i]
    out = []
    i += 1
    while True:
        c = s[i]
        if c == '\\':
            n = s[i + 1]
            if n == 'u':
                out.append(chr(int(s[i + 2:i + 6], 16)))
                i += 6
                continue
            if n in 'xU':
                raise ValueError('échappement JS non lu : \\' + n)
            out.append({'n': '\n', 't': '\t'}.get(n, n))
            i += 2
            continue
        if c == q:
            return ''.join(out), i + 1
        out.append(c)
        i += 1


_SKIP = re.compile(r'(?:\s|,|//[^\n]*|/\*.*?\*/)*', re.S)
_IDENT = re.compile(r'[A-Za-z_$][\w$]*')
_COLON = re.compile(r'\s*:\s*')
_PLUS = re.compile(r'\s*\+')


def _parse_js_block(txt):
    """Les entrées « clé: 'valeur' » d'un bloc d'objet JS, jusqu'à son « } » fermant ; tout autre contenu est une erreur."""
    d = {}
    i = 0
    n = len(txt)
    while True:
        i = _SKIP.match(txt, i).end()
        if i >= n:
            raise ValueError('bloc non refermé')
        if txt[i] == '}':
            return d
        if txt[i] in '\'"':
            k, i = _js_str_at(txt, i)
        else:
            m = _IDENT.match(txt, i)
            if not m:
                raise ValueError('clé illisible : ' + txt[i:i + 40])
            k, i = m.group(0), m.end()
        m = _COLON.match(txt, i)
        if not m:
            raise ValueError('« : » attendu après ' + k)
        i = m.end()
        if txt[i] not in '\'"':
            raise ValueError('valeur non littérale pour ' + k)
        v, i = _js_str_at(txt, i)
        if _PLUS.match(txt, i):
            raise ValueError('concaténation pour ' + k)
        if k in d:
            raise ValueError('clé en double : ' + k)
        d[k] = v


def _read_js_dicts(src):
    """Le dictionnaire « const I18N = { fr: {…}, en: {…} } » d'un outil dont le source Python porte le JS dans une chaîne.
    Le texte JS est celui que Python écrit : les chaînes constantes (littéral brut, ou parties constantes d'une f-string, où « {{ » est déjà « { »)."""
    hits = [n.value for n in ast.walk(ast.parse(src))
            if isinstance(n, ast.Constant) and isinstance(n.value, str) and 'const I18N = {' in n.value and 'en: {' in n.value]
    if len(hits) != 1:
        raise ValueError('const I18N : %d occurrence(s) dans le source, une attendue' % len(hits))
    js = hits[0]
    i = js.index('const I18N = {')
    j = js.index('fr: {', i)
    k = js.index('en: {', j)
    return _parse_js_block(js[j + 5:k]), _parse_js_block(js[k + 5:])


def _read_py_dicts(src):
    """Les dicts littéraux I18N_FR et I18N_EN d'un outil écrits en Python."""
    found = {}
    for n in ast.parse(src).body:
        if isinstance(n, ast.Assign) and len(n.targets) == 1 and getattr(n.targets[0], 'id', None) in ('I18N_FR', 'I18N_EN'):
            found[n.targets[0].id] = ast.literal_eval(n.value)
    if set(found) != {'I18N_FR', 'I18N_EN'}:
        raise ValueError('I18N_FR et I18N_EN attendus au premier niveau du source')
    return found['I18N_FR'], found['I18N_EN']


_DICTS = {}


def tool_dicts(tool, root=None):
    """(FR, EN) du dictionnaire de l'outil, ou None si son source ne se lit pas (l'erreur est inscrite une fois)."""
    if tool in _DICTS:
        return _DICTS[tool]
    path = os.path.join(root or HERE, TOOL_SOURCES[tool])
    try:
        with open(path, encoding='utf-8') as f:
            src = f.read()
        fr, en = (_read_py_dicts if tool == 'fc' else _read_js_dicts)(src)
        _DICTS[tool] = (fr, en)
    except Exception as e:     # noqa: BLE001 — toute erreur de lecture arrête le build, avec son texte
        PLANCHE_ERRORS.append('FAIL planche : dictionnaire de %s illisible dans %s (%s)' % (TOOL_NAMES[tool], TOOL_SOURCES[tool], e))
        _DICTS[tool] = None
    return _DICTS[tool]


# ═════════════════════════════════════════════════════════════════════════════════
# Les trois genres de texte
# ═════════════════════════════════════════════════════════════════════════════════

class _Part:
    def __init__(self, kind, **kw):
        self.kind = kind
        self.__dict__.update(kw)


def L(tool, key, up=False, args=None, icon=False, add=''):
    """Un libellé de l'outil, par sa référence (outil, clé). up : en capitales ; args : les valeurs d'un gabarit {0} {1} {n} {x} (tuple ou dict) ;
    icon : retire le pictogramme de tête (« 📦 Exporter » → « Exporter ») ; add : « ▾ » ou « … » ajouté quand l'écran l'affiche."""
    return _Part('L', tool=tool, key=key, up=up, args=args, icon=icon, add=add)


def D(fr, en=None):
    """Une donnée d'exemple, écrite en clair (la même dans les deux langues si en est omis)."""
    return _Part('D', fr=fr, en=fr if en is None else en)


def M(fr, en):
    """Un titre du manuel, écrit en clair."""
    return _Part('M', fr=fr, en=en)


_ICON = re.compile(r'^[^\w\s…]+\s+')
_SLOT = re.compile(r'\{(\w+)\}')


class Plate:
    """Une planche : ses textes, passés par L, D ou M, sont inscrits ici ; verify() contrôle que le SVG n'en porte pas d'autre."""

    def __init__(self, pid, tools):
        self.pid = pid
        self.tools = tools
        self.emitted = []       # les sorties de sv_text, telles que posées dans le SVG
        self.refs = set()       # (outil, clé) lus
        self.counts = {'L': 0, 'D': 0, 'M': 0}
        PLATES.append(self)

    def _err(self, tool, key, msg):
        PLANCHE_ERRORS.append('FAIL planche %s : outil %s, clé « %s » : %s' % (self.pid, TOOL_NAMES.get(tool, tool), key, msg))

    # ── un libellé de l'outil, dans les deux langues ─────────────────────────────
    def _label(self, p):
        out = []
        self.refs.add((p.tool, p.key))
        dd = tool_dicts(p.tool)
        for li, lang in ((0, 'FR'), (1, 'EN')):
            if dd is None:
                out.append('?')
                continue
            if p.key not in dd[li]:
                self._err(p.tool, p.key, 'absente du dictionnaire %s' % lang)
                out.append('?')
                continue
            t = dd[li][p.key]
            slots = _SLOT.findall(t)
            if p.args is None:
                if slots:
                    self._err(p.tool, p.key, 'gabarit %s sans valeur d’exemple (%s)' % ('{' + slots[0] + '}', lang))
            else:
                vals = p.args if isinstance(p.args, dict) else {str(i): v for i, v in enumerate(p.args)}
                miss = [s for s in slots if s not in vals]
                if miss or not slots:
                    self._err(p.tool, p.key, 'les valeurs d’exemple ne vont pas au gabarit (%s)' % lang)
                else:
                    t = _SLOT.sub(lambda m: str(vals[m.group(1)]), t)
            if p.icon:
                t2 = _ICON.sub('', t)
                if t2 == t:
                    self._err(p.tool, p.key, 'aucun pictogramme de tête à retirer (%s)' % lang)
                t = t2
            if p.up:
                t = t.upper()
            if p.add:
                if p.add not in ('▾', '…'):
                    self._err(p.tool, p.key, 'ajout non permis « %s »' % p.add)
                t = t + (' ' + p.add if p.add == '▾' else p.add)
            out.append(t)
        return out[0], out[1]

    def resolve(self, parts):
        """(FR, EN, genre) d'une suite de parties ; le genre est L s'il y a un libellé de l'outil, M pour un titre du manuel, D sinon."""
        fr, en, kinds = '', '', set()
        for p in parts:
            if p.kind == 'L':
                a, b = self._label(p)
            else:
                a, b = p.fr, p.en
            fr += a
            en += b
            kinds.add(p.kind)
        if 'M' in kinds and kinds != {'M'}:
            raise ValueError('un titre du manuel ne se mêle à rien d’autre')
        kind = 'L' if 'L' in kinds else ('M' if 'M' in kinds else 'D')
        return fr, en, kind

    def text(self, x, y, size, *parts, **kw):
        """Un <text> (FR puis EN) de la planche, écrit par le genre de ses parties."""
        fr, en, kind = self.resolve(parts)
        s = sv_text(x, y, size, fr, None if en == fr else en, **kw)
        self.emitted.append(s)
        self.counts[kind] += 1
        return s

    # ── contrôle ─────────────────────────────────────────────────────────────────
    def verify(self, *svgs):
        """Chaque <text> des SVG de la planche a été écrit par L, D ou M ; sinon l'erreur le cite. Chaque texte écrit se retire une fois : un doublon écrit à la main reste."""
        rest = '\n'.join(svgs)
        for s in self.emitted:
            rest = rest.replace(s, '', 1)
        for t in re.findall(r'<text\b[^>]*>(.*?)</text>', rest, flags=re.S):
            PLANCHE_ERRORS.append('FAIL planche %s : un <text> n’est passé par aucune des deux fonctions (libellé de l’outil, donnée d’exemple) : « %s »'
                                  % (self.pid, html.unescape(t)))

    # ── les aides de dessin ──────────────────────────────────────────────────────
    def bubble(self, n, cx, cy, tx, ty):
        """Bulle numérotée et son amorce vers le point visé (tx, ty), point plein au bout."""
        return (f'<line x1="{_n(cx)}" y1="{_n(cy)}" x2="{_n(tx)}" y2="{_n(ty)}" stroke="currentColor" stroke-width="1" opacity=".8"/>'
                f'<circle cx="{_n(tx)}" cy="{_n(ty)}" r="1.8" fill="currentColor"/>'
                f'<circle class="sv-box" cx="{_n(cx)}" cy="{_n(cy)}" r="8.5" stroke="currentColor" stroke-width="1.4"/>'
                + self.text(cx, cy + 3.2, 9, D(str(n)), extra=' font-weight="700"'))

    def btn(self, x, y, w, h, parts=None, op=.65, size=8):
        """Bouton : cadre au trait, libellé centré."""
        return (f'<rect x="{_n(x)}" y="{_n(y)}" width="{_n(w)}" height="{_n(h)}" rx="2" fill="none" stroke="currentColor" stroke-width="1" opacity="{op}"/>'
                + (self.text(x + w / 2, y + h / 2 + 3, size, *parts) if parts else ''))

    def field(self, x, y, w, h, parts=None):
        """Champ ou liste : trait plein, valeur à gauche."""
        return (f'<rect x="{_n(x)}" y="{_n(y)}" width="{_n(w)}" height="{_n(h)}" rx="1.5" fill="none" stroke="currentColor" stroke-width="1" opacity=".55"/>'
                + (self.text(x + 5, y + h / 2 + 3, 8, *parts, anchor='start', op=.85) if parts else ''))

    def group_card(self, x, y, w, name, typ, coal, units, count):
        """Carte de groupe : case, nom, trois pastilles (type, coalition, nombre d'unités), une ligne par unité. count : les parties du texte de la pastille du nombre."""
        o = []
        h = 24 + 12 * len(units)
        o.append(f'<rect x="{_n(x)}" y="{_n(y)}" width="{_n(w)}" height="{_n(h)}" rx="2" fill="none" stroke="currentColor" stroke-width="1" opacity=".7"/>')
        o.append(f'<rect x="{_n(x + 6)}" y="{_n(y + 6)}" width="9" height="9" fill="none" stroke="currentColor" stroke-width="1"/>')
        o.append(self.text(x + 21, y + 14, 8.5, D(name), anchor='start'))
        tx = x + 21 + 6.2 * len(name)
        for parts in ([D(typ)], [D(coal)], count):
            tw = 8 + 5.4 * len(self.resolve(parts)[0])
            o.append(f'<rect class="sv-pill" x="{_n(tx)}" y="{_n(y + 6)}" width="{_n(tw)}" height="11" rx="1.5"/>')
            o.append(self.text(tx + tw / 2, y + 14.5, 8, *parts, cls='sv-pill-t'))
            tx += tw + 4
        for k, u in enumerate(units):
            yy = y + 30 + 12 * k
            o.append(self.text(x + 8, yy, 8, D(u), anchor='start'))
            o.append(f'<line x1="{_n(x + 52)}" y1="{_n(yy - 3)}" x2="{_n(x + w - 10)}" y2="{_n(yy - 3)}" stroke="currentColor" stroke-width="5" opacity=".12"/>')
        return '\n          '.join(o), h

    def title_wide(self, fr, en, y, y_rule):
        """Le titre de la variante large (viewBox 720) et son filet."""
        return (self.text(360, y, 13, M(fr, en), op=.9, ls=3) + '\n          '
                f'<line x1="120" y1="{_n(y_rule)}" x2="600" y2="{_n(y_rule)}" stroke="currentColor" stroke-width=".6" opacity=".3"/>')

    def title_tall(self, fr, en, sub_fr, sub_en, w=360):
        """Le titre de la variante haute et son sous-titre."""
        return (self.text(w / 2, 22, 12, M(fr, en), op=.9, ls=2.5) + '\n          '
                + self.text(w / 2, 38, 8.5, M(sub_fr, sub_en), op=.7))

    def svg_open(self, cls, w, h, aria_fr, aria_en, marker):
        return (f'<svg class="{cls}" viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{_esc(aria_fr)}" '
                f'data-aria-fr="{_esc(aria_fr)}" data-aria-en="{_esc(aria_en)}">\n          ' + sv_defs(marker))

    # ── la légende numérotée ─────────────────────────────────────────────────────
    def legend_html(self, rows):
        """rows : (n, parties du titre, texte FR, texte EN). Le titre en gras est un libellé de l'outil ou un titre du manuel."""
        li = []
        for n, title, tf, te in rows:
            fr, en, kind = self.resolve(title)
            self.counts[kind] += 1
            li.append(f'<li><span class="pl-n">{n}</span><span class="lang-block" data-lang="fr"><b>{_esc(fr_typo(fr))}</b> — {_esc(fr_typo(tf))}</span>'
                      f'<span class="lang-block" data-lang="en"><b>{_esc(en)}</b> — {_esc(te)}</span></li>')
        return '<ol class="pl-legend">' + ''.join(li) + '</ol>'

    def figure_html(self, wide, tall, cap_fr, cap_en, legend):
        """La planche : le cadre, la figure zoomable (variante large, variante haute, « Fig. 1 — … »), puis la légende numérotée."""
        return (f'<div class="fm-plate">\n        <div class="fm-schema fm-plate-fig">\n          {wide}\n          {tall}\n'
                f'          <div class="fm-schema-legend">'
                f'<span class="lang-block" data-lang="fr">{_esc(cap_fr)}</span>'
                f'<span class="lang-block" data-lang="en">{_esc(cap_en)}</span></div>\n        </div>\n'
                f'        {legend}\n      </div>')


def fold_icon(x, y):
    """L'icône de repli à droite d'un en-tête de section."""
    return f'<path d="M{_n(x)},{_n(y - 1)} l4,3.5 l4,-3.5 M{_n(x)},{_n(y + 10)} l4,-3.5 l4,3.5" fill="none" stroke="currentColor" stroke-width="1.2"/>'


def chev(x, y):
    """Le chevron d'une section."""
    return f'<path d="M{_n(x)},{_n(y)} l6,0 l-3,5 z" fill="currentColor" opacity=".8"/>'


def check_report(plate):
    """Les lignes du compte rendu du build pour une planche."""
    c = plate.counts
    return ('planche %s : %d libellé(s) de l’outil lus dans %s (FR et EN, %d clé(s) distincte(s)), %d donnée(s) d’exemple, %d titre(s) du manuel'
            % (plate.pid, c['L'], ', '.join(TOOL_NAMES[t] for t in plate.tools), len(plate.refs), c['D'], c['M']))


# ═════════════════════════════════════════════════════════════════════════════════
# Le CSS générique d'une planche
# ═════════════════════════════════════════════════════════════════════════════════

PLANCHES_CSS = r'''
/* ── Planches d'écran : le cadre, la figure zoomable, ses deux variantes, la légende numérotée ── */
.fm-plate { margin: 28px 0; border: 1px solid var(--khaki); background: rgba(0,0,0,.10); padding: 20px; position: relative; }
.fm-plate > .fm-schema { margin: 0; border: 0; background: none; padding: 0; }
.fm-schema.fm-plate-fig svg { max-height: none; }
.fm-plate-fig .pl-tall { display: none; }
@media (max-width: 700px) { .fm-plate-fig .pl-wide { display: none; } .fm-plate-fig .pl-tall { display: block; } .fm-plate { padding: 10px; } }
.fm-plate-fig svg circle.sv-box { fill: var(--paper-light); }
.pl-legend { list-style: none; margin: 14px 0 10px; padding: 0 0 0 20px; display: grid; grid-template-columns: 1fr 1fr; gap: 6px 22px; color: var(--ink); }
@media (max-width: 700px) { .pl-legend { grid-template-columns: 1fr; } }
.pl-legend li { display: flex; gap: 8px; align-items: baseline; font-size: 13px; line-height: 1.45; opacity: .9; margin-bottom: 4px; }
.pl-n { flex: none; width: 19px; height: 19px; border: 1.4px solid currentColor; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; font-size: 10.5px; font-weight: 700; transform: translateY(3px); }
'''


# ═════════════════════════════════════════════════════════════════════════════════
# La planche d'HQ : l'écran, une mission ouverte
# ═════════════════════════════════════════════════════════════════════════════════

def _hq_cards(P, x, w, y, gap):
    """Les trois groupes d'exemple : (SVG, [(y, h)])."""
    o, cards = [], []
    for name, typ, coal, units in (('Caesar 1', 'Mi-24P', 'Red', ['Caesar 1-1', 'Caesar 1-2']),
                                   ('Anton 2', 'Mi-8MT', 'Red', ['Anton 2-1', 'Anton 2-2']),
                                   ('Viper 1', 'F-16C_50', 'Blue', ['Viper 1-1', 'Viper 1-2'])):
        s, h = P.group_card(x, y, w, name, typ, coal, units, [D('2 '), L('hq', 'snap.units')])
        o.append(s)
        cards.append((y, h))
        y += h + gap
    return o, cards


def _hq_wide(P):
    o = [P.svg_open('pl-wide', 720, 396, 'L’écran d’HQ, une mission ouverte', 'The HQ screen, with a mission open', 'hqw')]
    o.append(P.title_wide('L’ÉCRAN D’HQ', 'THE HQ SCREEN', 24, 32))
    o.append('<g transform="translate(0,22)">')
    X0, X1 = 110, 610
    # la barre du haut, dans l'ordre de l'écran
    o.append(sv_box(X0, 44, X1 - X0, 28))
    o.append(P.text(X0 + 10, 62, 9, L('hq', 'toolbar.title'), ls=1, anchor='start'))
    bx = {}
    x = X0 + 32
    for key, w, parts in (('wing', 40, [L('hq', 'tb.wing')]), ('open', 62, [L('hq', 'tb.open')]), ('save', 82, [L('hq', 'tb.save')]),
                          ('undo', 16, [D('↺')]), ('pk', 70, [L('hq', 'tb.pk')]), ('sep', 0, None),
                          ('ex', 48, [L('hq', 'toolbar.example')]), ('clr', 46, [L('hq', 'tb.clear')])):
        if key == 'sep':
            o.append(f'<line x1="{_n(x + 2)}" y1="50" x2="{_n(x + 2)}" y2="66" stroke="currentColor" stroke-width="1" opacity=".35"/>')
            x += 8
            continue
        o.append(P.btn(x, 49, w, 18, parts))
        bx[key] = (x, w)
        x += w + 4
    # le compteur de Sauvegarder .miz
    sx, sw = bx['save']
    o.append(f'<rect x="{_n(sx + sw - 7.5)}" y="43.5" width="11" height="11" rx="5.5" fill="currentColor"/>')
    o.append(P.text(sx + sw - 2, 52, 8, D('2'), cls='sv-pill-t', extra=' font-weight="700"'))
    # drapeau
    o.append(P.btn(X1 - 24, 49, 18, 18))
    o.append(f'<rect x="{_n(X1 - 21)}" y="54" width="12" height="8" fill="none" stroke="currentColor" stroke-width="1"/>')
    # colonne de gauche : les groupes
    L0, L1 = X0, 400
    o.append(sv_box(L0, 80, L1 - L0, 278))
    o.append(P.text(L0 + 8, 96, 8.5, L('hq', 'snap.flights', up=True), D(' (3)'), anchor='start', ls=1.2))
    o.append(f'<line x1="{_n(L0 + 8)}" y1="102" x2="{_n(L1 - 8)}" y2="102" stroke="currentColor" stroke-width=".6" opacity=".4"/>')
    o.append(P.field(L0 + 8, 108, 78, 15, [L('hq', 'pk.flt.side', add='▾')]))
    o.append(P.field(L0 + 90, 108, 78, 15, [L('hq', 'pk.flt.type', add='▾')]))
    o.append(P.field(L0 + 172, 108, L1 - L0 - 180, 15, [L('hq', 'pk.flt.name')]))
    o.append(P.btn(L0 + 8, 130, 128, 16, [L('hq', 'pk.flt.checkShown')]))
    o.append(P.btn(L0 + 140, 130, 64, 16, [L('hq', 'pk.flt.uncheck')]))
    # le compte des groupes affichés : en FR le texte de l'outil (« 3 / 3 groupes affichés ») ne tient pas à droite des deux boutons ; il se pose sur la ligne de l'en-tête, à droite
    o.append(P.text(L1 - 8, 96, 8, L('hq', 'pk.flt.shown', args=('3', '3')), anchor='end', op=.75))
    o.append(f'<line x1="{_n(L0 + 8)}" y1="152" x2="{_n(L1 - 8)}" y2="152" stroke="currentColor" stroke-width=".6" opacity=".4"/>')
    cs, cards = _hq_cards(P, L0 + 8, L1 - L0 - 16, 158, 6)
    o += cs
    # colonne de droite : les groupes cochés, la mission source
    R0, R1 = 408, X1
    o.append(sv_box(R0, 80, R1 - R0, 118))
    o.append(chev(R0 + 8, 90))
    o.append(P.text(R0 + 20, 95, 8.5, L('hq', 'hq.checked.many', args=('2',)), anchor='start'))
    o.append(fold_icon(R1 - 18, 88))
    o.append(f'<line x1="{_n(R0)}" y1="104" x2="{_n(R1)}" y2="104" stroke="currentColor" stroke-width=".6" opacity=".4"/>')
    for k, key in enumerate(('pk.export', 'pk.delete', 'pk.dyn')):
        o.append(P.btn(R0 + 8, 112 + 27 * k, R1 - R0 - 16, 20, [L('hq', key, icon=(key == 'pk.export'))], size=8.5))
    o.append(sv_box(R0, 206, R1 - R0, 152))
    o.append(chev(R0 + 8, 216))
    o.append(P.text(R0 + 20, 221, 8.5, L('hq', 'snap.sourceMission'), anchor='start'))
    o.append(fold_icon(R1 - 18, 214))
    o.append(f'<line x1="{_n(R0)}" y1="230" x2="{_n(R1)}" y2="230" stroke="currentColor" stroke-width=".6" opacity=".4"/>')
    o.append(P.text(R0 + 8, 244, 8, D('mission.miz · Syrie · 1985-06-01', 'mission.miz · Syria · 1985-06-01'), anchor='start', op=.85))
    o.append(P.text(R0 + 8, 256, 8, L('hq', 'snap.startTime'), D(' : 08h00', ': 08:00'), anchor='start', op=.85))
    o.append(P.text(R0 + 8, 274, 8, L('hq', 'snap.weather', up=True), anchor='start', ls=1))
    o.append(P.field(R0 + 8, 280, R1 - R0 - 16, 18, [D('XXXX 010800Z 18008KT CAVOK')]))
    o.append(P.text(R0 + 8, 316, 8, D('Vent 180° · 8 kt · QNH 1013', 'Wind 180° · 8 kt · QNH 1013'), anchor='start', op=.75))
    o.append(P.text(R0 + 8, 340, 8, L('hq', 'snap.fingerprint'), D(' : sha256…', ': sha256…'), anchor='start', op=.55))

    def mid(k):
        x, w = bx[k]
        return x + w / 2
    for n, k in ((1, 'wing'), (2, 'open'), (3, 'save'), (4, 'undo'), (5, 'pk'), (6, 'ex'), (7, 'clr')):
        o.append(P.bubble(n, mid(k), 28, mid(k), 49))
    o.append(P.bubble(8, 80, 116, L0 + 8, 116))
    o.append(P.bubble(9, 80, 138, L0 + 8, 138))
    o.append(P.bubble(10, 80, cards[0][0] + 12, L0 + 8, cards[0][0] + 12))
    o.append(P.bubble(11, 640, 130, R1, 130))
    o.append(P.bubble(12, 640, 222, R1 - 10, 222))
    o.append('</g>')
    o.append('</svg>')
    return '\n          '.join(o)


def _hq_tall(P):
    W = 360
    o = [P.svg_open('pl-tall', W, 676, 'L’écran d’HQ au téléphone, une mission ouverte', 'The HQ screen on a phone, with a mission open', 'hqt')]
    o.append(P.title_tall('L’ÉCRAN D’HQ', 'THE HQ SCREEN', 'au téléphone', 'on a phone'))
    o.append('<g transform="translate(0,12)">')
    X0, X1 = 62, 298
    # la barre : flèche, sigle, six icônes
    o.append(sv_box(X0, 62, X1 - X0, 30))
    o.append(P.text(X0 + 10, 81, 8.5, D('◄'), anchor='start'))
    o.append(P.text(X0 + 34, 81, 8.5, D('H·Q')))
    ic = {}
    x = X0 + 52
    for key, glyph in (('wing', '⛉'), ('open', '▭'), ('save', '▣'), ('pk', '◫'), ('ex', '▤'), ('clr', '⌫')):
        o.append(P.btn(x, 67, 26, 20))
        o.append(P.text(x + 13, 81, 9, D(glyph)))
        ic[key] = x + 13
        x += 30
    # sections empilées
    y = 100
    o.append(sv_box(X0, y, X1 - X0, 104))
    o.append(chev(X0 + 8, y + 10))
    o.append(P.text(X0 + 20, y + 15, 8.5, L('hq', 'hq.checked.many', args=('2',)), anchor='start'))
    o.append(fold_icon(X1 - 18, y + 8))
    for k, key in enumerate(('pk.export', 'pk.delete', 'pk.dyn')):
        o.append(P.btn(X0 + 8, y + 26 + 25 * k, X1 - X0 - 16, 19, [L('hq', key, icon=(key == 'pk.export'))], size=8.5))
    y11 = y + 15
    y = 212
    o.append(sv_box(X0, y, X1 - X0, 132))
    o.append(chev(X0 + 8, y + 10))
    o.append(P.text(X0 + 20, y + 15, 8.5, L('hq', 'snap.sourceMission'), anchor='start'))
    o.append(fold_icon(X1 - 18, y + 8))
    o.append(P.text(X0 + 8, y + 38, 8, D('mission.miz · Syrie · 1985-06-01', 'mission.miz · Syria · 1985-06-01'), anchor='start', op=.85))
    o.append(P.text(X0 + 8, y + 50, 8, L('hq', 'snap.startTime'), D(' : 08h00', ': 08:00'), anchor='start', op=.85))
    o.append(P.text(X0 + 8, y + 68, 8, L('hq', 'snap.weather', up=True), anchor='start', ls=1))
    o.append(P.field(X0 + 8, y + 74, X1 - X0 - 16, 18, [D('XXXX 010800Z 18008KT…')]))
    o.append(P.text(X0 + 8, y + 108, 8, D('Vent 180° · 8 kt · QNH 1013', 'Wind 180° · 8 kt · QNH 1013'), anchor='start', op=.75))
    o.append(P.text(X0 + 8, y + 124, 8, L('hq', 'snap.fingerprint'), D(' : sha256…', ': sha256…'), anchor='start', op=.55))
    y12 = y + 15
    y = 352
    o.append(sv_box(X0, y, X1 - X0, 286))
    o.append(P.text(X0 + 8, y + 16, 8.5, L('hq', 'snap.flights', up=True), D(' (3)'), anchor='start', ls=1.2))
    o.append(P.field(X0 + 8, y + 26, 108, 15, [L('hq', 'pk.flt.side', add='▾')]))
    o.append(P.field(X0 + 120, y + 26, X1 - X0 - 128, 15, [L('hq', 'pk.flt.type', add='▾')]))
    o.append(P.field(X0 + 8, y + 46, X1 - X0 - 16, 15, [L('hq', 'pk.flt.name')]))
    y8 = y + 40
    o.append(P.btn(X0 + 8, y + 68, 128, 16, [L('hq', 'pk.flt.checkShown')]))
    o.append(P.btn(X0 + 140, y + 68, 64, 16, [L('hq', 'pk.flt.uncheck')]))
    o.append(P.text(X1 - 8, y + 98, 8, L('hq', 'pk.flt.shown', args=('3', '3')), anchor='end', op=.75))
    y9 = y + 76
    yy = y + 108
    y10 = yy + 12
    cs, _cards = _hq_cards(P, X0 + 8, X1 - X0 - 16, yy, 8)
    o += cs
    # bulles : la barre au-dessus, le reste dans les marges
    for n, k in ((1, 'wing'), (2, 'open'), (3, 'save'), (5, 'pk'), (6, 'ex'), (7, 'clr')):
        o.append(P.bubble(n, ic[k], 44, ic[k], 67))
    o.append(P.bubble(11, 30, y11, X0, y11))
    o.append(P.bubble(12, 30, y12, X0, y12))
    o.append(P.bubble(8, 30, y8, X0 + 8, y8))
    o.append(P.bubble(9, 30, y9, X0 + 8, y9))
    o.append(P.bubble(10, 30, y10, X0 + 8, y10))
    o.append('</g>')
    o.append('</svg>')
    return '\n          '.join(o)


# La légende d'HQ : (n, titre, texte FR, texte EN). Le titre est un libellé de l'outil, ou un titre du manuel.
def _hq_legend_rows():
    return [
        (1, [L('hq', 'tb.wing')],
         'la fenêtre de l’escadre : escadrons, callsigns, logos, livrées custom et livrée par défaut. Sauvegardée à chaque saisie, lue par tous les outils ; Exporter config et Importer config passent d’un HQ à l’autre. En lecture seule quand un autre outil la fournit.',
         'the wing’s window: squadrons, callsigns, logos, custom liveries and default livery. Saved on every entry, read by every tool; Export config and Import config carry it from one HQ to another. Read-only when another tool provides it.'),
        (2, [L('hq', 'tb.open')],
         'ou déposez le fichier n’importe où sur la page : ses groupes Client, sa date, son heure et sa météo passent aux autres outils, tant que le .miz reste ouvert.',
         'or drop the file anywhere on the page: its Client groups, date, time and weather go to the other tools, as long as the .miz stays open.'),
        (3, [L('hq', 'tb.save')],
         'le compteur dit les modifications en attente (paquets appliqués, groupes supprimés, Dynamic Spawn) ; un seul téléchargement pour toutes. Ctrl+S.',
         'the counter tells the pending changes (packages applied, groups deleted, Dynamic Spawn); one download for all of them. Ctrl+S.'),
        (4, [L('hq', 'tb.revert'), D(' ↺')],
         'abandonne toutes les modifications en attente.',
         'drops all the pending changes.'),
        (5, [L('hq', 'tb.pk')],
         'importe les paquets rendus par les Flight Leaders ; pour chaque groupe, cochez route, radios, emport, livrée, puis Appliquer à la mission. HQ retrouve le groupe par son nom et sa coalition.',
         'imports the packages handed back by the Flight Leaders; for each group, tick route, radios, loadout, livery, then Apply to the mission. HQ finds the group by its name and coalition.'),
        (6, [L('hq', 'toolbar.example')],
         'une escadre de démonstration, sans confirmation ; votre configuration est gardée, Restaurer ma configuration la rend.',
         'a demonstration wing, without a confirmation; your configuration is kept, Restore my configuration brings it back.'),
        (7, [L('hq', 'tb.clear')],
         'retire la mission ouverte, après confirmation ; le Wing ne change pas.',
         'removes the open mission, after a confirmation; the Wing does not change.'),
        (8, [M('Les filtres', 'The filters')],
         'coalition, type et nom : la liste ne montre que les groupes qui y répondent.',
         'coalition, type and name: the list shows only the groups that match.'),
        (9, [L('hq', 'pk.flt.checkShown')],
         'et Tout décocher ; le compte des groupes affichés est à droite.',
         'and Uncheck all; the count of shown groups is on the right.'),
        (10, [M('Un groupe', 'A group')],
         'sa case, son nom, son type, sa coalition, puis chaque unité et ses radios, lus dans le .miz.',
         'its box, name, type and coalition, then each unit and its radios, read from the .miz.'),
        (11, [M('Sur les groupes cochés', 'On the checked groups')],
         'Exporter (un paquet, pour un Flight Leader qui n’a pas le .miz), Supprimer, et Dynamic Spawn… en trois étapes : le template, les lieux d’apparition, le départ moteur tournant.',
         'Export (a package, for a Flight Leader without the .miz), Delete, and Dynamic Spawn… in three steps: the template, the spawn places, the hot start.'),
        (12, [L('hq', 'snap.sourceMission')],
         'le fichier, le théâtre, la date, l’heure de départ, la météo et son METAR, l’empreinte du .miz. Chaque section se replie par l’icône à droite de son en-tête.',
         'the file, theatre, date, start time, the weather and its METAR, the .miz fingerprint. Each section folds by the icon at the right of its header.'),
    ]


def build_plate_hq():
    """La planche d'HQ : le HTML (cadre, figure zoomable, légende) ; ses libellés viennent du dictionnaire d'HQ."""
    P = Plate('hq', ['hq'])
    wide, tall = _hq_wide(P), _hq_tall(P)
    legend = P.legend_html(_hq_legend_rows())
    P.verify(wide, tall)
    return P.figure_html(wide, tall,
                         'Fig. 1 — L’écran d’HQ, une mission ouverte : la barre, les groupes du .miz et leurs actions.',
                         'Fig. 1 — The HQ screen with a mission open: the bar, the .miz groups and their actions.', legend)
