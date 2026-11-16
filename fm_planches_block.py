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
            if n in 'xUrbfv0\n\r':
                raise ValueError('échappement JS non lu : \\' + (n if n.isalnum() else 'fin de ligne'))
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
    """Les entrées « clé: 'valeur' » d'un bloc d'objet JS (txt commence après son « { »), jusqu'à son « } » fermant ; tout autre contenu est une erreur. Renvoie (dict, indice après le « } »)."""
    d = {}
    i = 0
    n = len(txt)
    while True:
        i = _SKIP.match(txt, i).end()
        if i >= n:
            raise ValueError('bloc non refermé')
        if txt[i] == '}':
            return d, i + 1
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
    Le texte JS est celui que Python écrit : les chaînes constantes (littéral brut, ou parties constantes d'une f-string, où « {{ » est déjà « { »).
    L'objet se lit clé par clé (fr ou en, « : », « { », le bloc, puis « , » ou « } ») : exactement les deux clés, une fois chacune, dans n'importe quel ordre."""
    hits = [n.value for n in ast.walk(ast.parse(src)) if isinstance(n, ast.Constant) and isinstance(n.value, str)
            and re.search(r'const I18N = \{\s*(?:fr|en)\s*:\s*\{', n.value)]
    if len(hits) != 1:
        raise ValueError('const I18N : %d occurrence(s) dans le source, une attendue' % len(hits))
    js = hits[0]
    i = re.search(r'const I18N = \{', js).end()
    found = {}
    while True:
        i = _SKIP.match(js, i).end()
        if js[i] == '}':
            break
        m = _IDENT.match(js, i)
        if not m or m.group(0) not in ('fr', 'en'):
            raise ValueError('const I18N : clé « fr » ou « en » attendue, lu : ' + js[i:i + 20])
        if m.group(0) in found:
            raise ValueError('const I18N : clé « %s » en double' % m.group(0))
        c = _COLON.match(js, m.end())
        if not c or js[c.end()] != '{':
            raise ValueError('const I18N : « : { » attendu après ' + m.group(0))
        found[m.group(0)], i = _parse_js_block(js[c.end() + 1:])
        i += c.end() + 1
        t = re.compile(r'\s*').match(js, i).end()
        if js[t] not in ',}':
            raise ValueError('const I18N : « , » ou « } » attendu après le bloc ' + m.group(0))
        i = t
    if set(found) != {'fr', 'en'}:
        raise ValueError('const I18N : les deux clés fr et en sont attendues')
    return found['fr'], found['en']


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
    if tool not in TOOL_SOURCES:
        PLANCHE_ERRORS.append('FAIL planche : outil inconnu « %s »' % tool)
        _DICTS[tool] = None
        return None
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


def _q(t):
    """Un texte pour un attribut : guillemets échappés."""
    return html.escape(t, quote=True)


_NORM = re.compile(r'[\W_]+')


def _norm(t):
    return _NORM.sub('', t.casefold())


# Les données d'exemple qui tombent, par hasard, sur une valeur du dictionnaire de l'outil : (planche, texte français) → raison. Rien d'autre.
D_EXCEPTIONS = {
    # la pastille de coalition de l'instantané affiche la valeur brute du groupe (fl.coalition), pas le libellé traduit de pk.flt.red
    ('hq', 'Red'): 'valeur brute de coalition affichée par l’outil, pas le libellé du filtre',
    # le sigle court de la barre téléphone est écrit en dur dans l'outil (build_hq.py, tb-brand-short), hors dictionnaire ; sa norme tombe sur « HQ »
    ('hq', 'H·Q'): 'sigle écrit en dur dans l’outil, non traduit',
    # valeur d'exemple de la ligne Paillettes : le reste du gabarit « {0} % » une fois l'argument retiré
    ('fc', '0'): 'nombre d’exemple, égal au résidu du gabarit lo.pct',
}


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
        self.mixed = []         # les <text> qui accolent une donnée à un libellé de l'outil (relecture, sans arrêt)
        self._dvals = None
        self._dseen = set()
        PLATES.append(self)

    def _err(self, tool, key, msg):
        PLANCHE_ERRORS.append('FAIL planche %s : outil %s, clé « %s » : %s' % (self.pid, TOOL_NAMES.get(tool, tool), key, msg))

    # ── un libellé de l'outil, dans les deux langues ─────────────────────────────
    def _slot(self, v, li):
        """La valeur d'un gabarit {0} : un texte, ou une partie L / D (un libellé de l'outil, une donnée d'exemple) qui se lit dans la langue demandée."""
        if isinstance(v, _Part):
            if v.kind == 'D':
                self._check_d(v)
            return (self._label(v) if v.kind == 'L' else (v.fr, v.en))[li]
        return str(v)

    def _label(self, p):
        out = []
        self.refs.add((p.tool, p.key))
        if p.tool not in self.tools:
            self._err(p.tool, p.key, 'cet outil n’est pas celui de la planche (%s)' % ', '.join(TOOL_NAMES.get(t, t) for t in self.tools))
            return '?', '?'
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
                    t = _SLOT.sub(lambda m: self._slot(vals[m.group(1)], li), t)
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

    def _check_d(self, p):
        """Une donnée d'exemple qui égale (ponctuation, espaces et casse ignorés) une valeur FR ou EN du dictionnaire de l'outil de la planche est un libellé écrit en clair : erreur, sauf exception écrite dans D_EXCEPTIONS."""
        if self._dvals is None:
            self._dvals = set()
            for t in self.tools:
                dd = tool_dicts(t)
                for d in (dd or ()):
                    self._dvals |= {_norm(v) for v in d.values()}
            self._dvals.discard('')
        for txt in (p.fr, p.en):
            n = _norm(txt)
            if n and n in self._dvals and (self.pid, p.fr) not in D_EXCEPTIONS and (self.pid, p.fr) not in self._dseen:
                self._dseen.add((self.pid, p.fr))
                PLANCHE_ERRORS.append('FAIL planche %s : la donnée d’exemple « %s » est une valeur du dictionnaire de l’outil : écrivez-la par L (ou ajoutez une exception motivée)' % (self.pid, p.fr))
                break

    def resolve(self, parts):
        """(FR, EN, genre) d'une suite de parties ; le genre est L s'il y a un libellé de l'outil, M pour un titre du manuel, D sinon."""
        fr, en, kinds = '', '', set()
        for p in parts:
            if p.kind == 'L':
                a, b = self._label(p)
            else:
                a, b = p.fr, p.en
                if p.kind == 'D':
                    self._check_d(p)
            fr += a
            en += b
            kinds.add(p.kind)
        if 'M' in kinds and kinds != {'M'}:
            PLANCHE_ERRORS.append('FAIL planche %s : un titre du manuel ne se mêle à rien d’autre : « %s »' % (self.pid, fr))
            kinds = {'L'}
        kind = 'L' if 'L' in kinds else ('M' if 'M' in kinds else 'D')
        return fr, en, kind

    def text(self, x, y, size, *parts, _m=False, **kw):
        """Un <text> (FR puis EN) de la planche, écrit par le genre de ses parties. Le genre M (titre du manuel) n'y entre que par les titres de planche (_m)."""
        fr, en, kind = self.resolve(parts)
        if kind == 'M' and not _m:
            PLANCHE_ERRORS.append('FAIL planche %s : un titre du manuel ne s’écrit que comme titre de planche ou titre de légende : « %s »' % (self.pid, fr))
        if {p.kind for p in parts} >= {'L', 'D'} and fr not in self.mixed:
            self.mixed.append(fr)
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
        if re.search(r'<foreignObject\b', '\n'.join(svgs), flags=re.I):
            PLANCHE_ERRORS.append('FAIL planche %s : foreignObject refusé dans une planche' % self.pid)
        n_open = len(re.findall(r'<text\b', '\n'.join(svgs), flags=re.I))
        n_emit = sum(len(re.findall(r'<text\b', e, flags=re.I)) for e in self.emitted)
        if n_open != n_emit:
            PLANCHE_ERRORS.append('FAIL planche %s : %d <text> ouvrants dans les SVG, %d écrits par les deux fonctions' % (self.pid, n_open, n_emit))
        for t in re.findall(r'<text\b[^>]*>(.*?)</text>', rest, flags=re.S | re.I):
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

    def field(self, x, y, w, h, parts=None, size=8):
        """Champ ou liste : trait plein, valeur à gauche."""
        return (f'<rect x="{_n(x)}" y="{_n(y)}" width="{_n(w)}" height="{_n(h)}" rx="1.5" fill="none" stroke="currentColor" stroke-width="1" opacity=".55"/>'
                + (self.text(x + 5, y + h / 2 + size * .375, size, *parts, anchor='start', op=.85) if parts else ''))

    def pill(self, x, y, parts, size=8, h=11):
        """Pastille : (SVG, largeur). La largeur suit le plus long des deux textes, français ou anglais."""
        fr, en, _k = self.resolve(parts)
        tw = 8 + 5.4 * max(len(fr), len(en)) * size / 8
        return (f'<rect class="sv-pill" x="{_n(x)}" y="{_n(y)}" width="{_n(tw)}" height="{_n(h)}" rx="1.5"/>'
                + self.text(x + tw / 2, y + h - 2.6, size, *parts, cls='sv-pill-t')), tw

    def lfield(self, x, y, w, label, value, badge=False, size=8):
        """Champ étiqueté : le libellé de l'outil au-dessus, le champ dessous (hauteur totale 26) ; badge : la pastille « FC » après le libellé."""
        o = self.text(x, y + 8, 8, *label, anchor='start', op=.75)
        if badge:
            bx = x + 4.4 * len(self.resolve(label)[0]) + 6
            o += (f'<rect class="sv-pill" x="{_n(bx)}" y="{_n(y)}" width="17" height="11.5" rx="1.5"/>'
                  + self.text(bx + 8.5, y + 8.7, 8, D('FC'), cls='sv-pill-t'))
        return o + self.field(x, y + 11, w, 15, value, size=size)

    def tick(self, x, y, on=True):
        """Une case (7 × 7), cochée ou non."""
        return (f'<rect x="{_n(x)}" y="{_n(y)}" width="7" height="7" fill="none" stroke="currentColor" stroke-width="1"/>'
                + (f'<path d="M{_n(x + 1.5)},{_n(y + 3.6)} l1.7,1.8 l2.6,-3.6" fill="none" stroke="currentColor" stroke-width="1.1"/>' if on else ''))

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
        return (self.text(360, y, 13, M(fr, en), op=.9, ls=3, _m=True) + '\n          '
                f'<line x1="120" y1="{_n(y_rule)}" x2="600" y2="{_n(y_rule)}" stroke="currentColor" stroke-width=".6" opacity=".3"/>')

    def title_tall(self, fr, en, sub_fr, sub_en, w=360):
        """Le titre de la variante haute et son sous-titre."""
        return (self.text(w / 2, 22, 12, M(fr, en), op=.9, ls=2.5, _m=True) + '\n          '
                + self.text(w / 2, 38, 8.5, M(sub_fr, sub_en), op=.7, _m=True))

    def svg_open(self, cls, w, h, aria_fr, aria_en, marker):
        return (f'<svg class="{cls}" viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{_q(aria_fr)}" '
                f'data-aria-fr="{_q(aria_fr)}" data-aria-en="{_q(aria_en)}">\n          ' + sv_defs(marker))

    # ── la légende numérotée ─────────────────────────────────────────────────────
    def legend_html(self, rows):
        """rows : (n, parties du titre, texte FR, texte EN). Le titre en gras est un libellé de l'outil ou un titre du manuel."""
        li = []
        for n, title, tf, te in rows:
            fr, en, kind = self.resolve(title)
            if kind not in ('L', 'M'):
                PLANCHE_ERRORS.append('FAIL planche %s : le titre en gras de la légende (ligne %s) doit être un libellé de l’outil ou un titre du manuel : « %s »' % (self.pid, n, fr))
            self.counts[kind] += 1
            li.append(f'<li><span class="pl-n">{n}</span><span class="lang-block" data-lang="fr"><b>{_esc(fr_typo(fr))}</b> — {_esc(fr_typo(tf))}</span>'
                      f'<span class="lang-block" data-lang="en"><b>{_esc(en)}</b> — {_esc(te)}</span></li>')
        return '<ol class="pl-legend">' + ''.join(li) + '</ol>'

    def figure_html(self, wide, tall, cap_fr, cap_en, legend):
        """La planche : le cadre, la figure zoomable (variante large, variante haute, « Fig. 1 — … »), puis la légende numérotée."""
        return (f'<div class="fm-plate">\n        <div class="fm-schema fm-plate-fig">\n          {wide}\n          {tall}\n'
                f'          <div class="fm-schema-legend">'
                f'<span class="lang-block" data-lang="fr">{_esc(fr_typo(cap_fr))}</span>'
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
/* la vue de face du Mi-24P (data/aircraft_views.json) : encre de la planche, fond de papier */
.fm-plate-fig svg .pl-view-bg { fill: var(--paper-light); }
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


# ═════════════════════════════════════════════════════════════════════════════════
# Aides communes aux planches du Flight Configurator et du Datacard Generator
# ═════════════════════════════════════════════════════════════════════════════════

def _toolbar_wide(P, X0, X1, tool, sub_key, buttons):
    """La barre du haut de la variante large : cadre, sous-titre de l'outil, boutons. Renvoie (SVG, {clé: (x, largeur)})."""
    o = [sv_box(X0, 44, X1 - X0, 28), P.text(X0 + 8, 62, 8, L(tool, sub_key), anchor='start', op=.7, ls=.6)]
    bx, x = {}, X0 + 104
    for key, w, parts in buttons:
        o.append(P.btn(x, 49, w, 18, parts))
        bx[key] = (x, w)
        x += w + 4
    return o, bx


def _head(P, x, y, w, parts, fold=True):
    """L'en-tête d'un bloc : chevron, titre, icône de repli ; y est le haut du bloc."""
    o = [chev(x + 8, y + 10), P.text(x + 20, y + 15, 8.5, *parts, anchor='start')]
    if fold:
        o.append(fold_icon(x + w - 18, y + 8))
    return o


def _rule(x0, x1, y):
    return f'<line x1="{_n(x0)}" y1="{_n(y)}" x2="{_n(x1)}" y2="{_n(y)}" stroke="currentColor" stroke-width=".6" opacity=".4"/>'


def _bars(x, y, w, n=1, gap=10):
    """Des traits gris pour un contenu qui n'est pas lu (un tableau, une page)."""
    return ''.join(f'<line x1="{_n(x)}" y1="{_n(y + k * gap)}" x2="{_n(x + w)}" y2="{_n(y + k * gap)}" stroke="currentColor" stroke-width="5" opacity=".12"/>'
                   for k in range(n))


# ═════════════════════════════════════════════════════════════════════════════════
# La planche du Flight Configurator : l'écran, un groupe ouvert
# ═════════════════════════════════════════════════════════════════════════════════

def _fc_group_head(P, gx, gy, gw):
    """Ligne titre d'un groupe : repli, nom, pastilles (type, unités), retrait."""
    o = [chev(gx + 8, gy + 8), P.text(gx + 20, gy + 13, 8.5, D('CAESAR'), anchor='start')]
    px = gx + 20 + 6.2 * 6
    s, w1 = P.pill(px, gy + 4, [D('Mi-24P')])
    o.append(s)
    s, w2 = P.pill(px + w1 + 4, gy + 4, [L('fc', 'fl.units.many', args=('2',))])
    o.append(s)
    o.append(P.text(gx + gw - 12, gy + 13, 8.5, D('✕'), op=.7))
    return o


def _fc_route_line(P, x, y):
    return P.text(x, y, 8, L('fc', 'route.line', args=(D('STEPPE WIND M3'), L('fc', 'route.pts.many', args=('6',)), D('153,7 km', '153.7 km'))), anchor='start', op=.8)


def _fc_unit_head(P, ux, uy, uw, n):
    return [chev(ux + 7, uy + 7), P.text(ux + 19, uy + 12, 8.5, L('fc', 'u.title', args=(n,)), anchor='start'), P.text(ux + uw - 10, uy + 12, 8.5, D('✕'), op=.7)]


def _fc_radios(P, ux, uw, ry, recopy):
    """Les radios d'une unité : l'entrée, un poste, une rangée de canaux, et (si recopy) le bouton Recopier. Renvoie (SVG, y du bouton ou de la fin)."""
    o = [chev(ux + 7, ry - 5), P.text(ux + 19, ry, 8, L('fc', 'u.radios'), anchor='start', op=.9),
         P.text(ux + 52, ry, 8, L('fc', 'u.radios.set', args=('5',)), anchor='start', op=.65)]
    if not recopy:
        return o, ry
    py = ry + 14
    o.append(P.text(ux + 16, py, 8, D('R-863 (VHF/UHF)'), anchor='start'))
    o.append(P.text(ux + 88, py, 8, L('fc', 'rad.chans', args=('20',)), anchor='start', op=.6))
    o.append(P.text(ux + 16, py + 11, 8, D('100–149,975 · 220–399,9 MHz', '100–149.975 · 220–399.9 MHz'), anchor='start', op=.55))
    cy0 = py + 17
    for k, v in enumerate(('127.500', '135.000', '—')):
        ix = ux + 16 + k * 60
        o.append(P.tick(ix, cy0, True))
        o.append(P.text(ix + 10, cy0 + 7, 8, L('fc', 'rad.ch', args=(str(k),)), anchor='start', op=.75))
        o.append(P.field(ix, cy0 + 10, 56, 14, [D(v)], size=8))
    ry2 = cy0 + 31
    o.append(P.btn(ux + 8, ry2, uw - 16, 15, [L('fc', 'rad.copy')], size=8))
    return o, ry2


_VIEWS = {}


def aircraft_front_view(ac):
    """La vue de face d'un appareil, telle que le Flight Configurator l'affiche : lue dans data/aircraft_views.json (lecture seule), recolorée à l'encre de la planche.
    Renvoie (groupe SVG sans son cadre, largeur, hauteur) ; une structure inattendue (autres couleurs, autre nombre de tracés) arrête le build."""
    if ac not in _VIEWS:
        try:
            import json
            with open(os.path.join(HERE, 'data', 'aircraft_views.json'), encoding='utf-8') as fh:
                raw = json.load(fh)[ac]['svg']
            m = re.match(r'\s*<svg\b[^>]*viewBox="0 0 ([\d.]+) ([\d.]+)"[^>]*>(.*)</svg>\s*$', raw, flags=re.S)
            body = m.group(3)
            vals = {v.lower() for v in re.findall(r'\b(?:fill|stroke)="([^"]*)"', body)}
            if (len(re.findall(r'<path\b', body)) != 4 or not {'#ffffff', '#241f21'} <= vals or not vals <= {'#ffffff', '#241f21', 'none'}
                    or re.search(r'\bstyle\s*=', body, flags=re.I) or re.search(r'<(?!/?path\b)\w', body)):
                raise ValueError('structure inattendue (tracés, couleurs, style ou éléments)')
            body = re.sub(r'fill="#ffffff"', 'class="pl-view-bg"', body, flags=re.I)
            body = re.sub(r'stroke="#241f21"', 'stroke="currentColor"', body, flags=re.I)
            _VIEWS[ac] = (body, float(m.group(1)), float(m.group(2)))
        except Exception as e:     # noqa: BLE001
            PLANCHE_ERRORS.append('FAIL planche fc : la vue de face de %s ne se lit pas dans data/aircraft_views.json (%s)' % (ac, e))
            _VIEWS[ac] = ('', 344.34, 270.792)
    return _VIEWS[ac]


def _fc_loadout_block(P, x, y, w, narrow):
    """Le bloc EMPORT : l'unité choisie, la vue de face, deux stations, Symétrique, la masse, carburant et le reste, Partir de et Garder. Renvoie (SVG, hauteur, ancres)."""
    o = [sv_box(x, y, w, 0)]          # le cadre est posé en dernier (hauteur connue)
    o += _head(P, x, y, w, [L('fc', 'sec.cmp')])
    o.append(_rule(x, x + w, y + 24))
    o.append(P.text(x + 8, y + 38, 8, D('CAESAR · CAESAR-1'), anchor='start'))
    s, _w = P.pill(x + 8 + 4.9 * 17 + 6, y + 30, [D('Mi-24P')])
    o.append(s)
    # la vue de face du Mi-24P, celle de la production, puis les six stations numérotées de 6 à 1
    body, vw0, vh0 = aircraft_front_view('Mi-24P')
    vw = 150 if not narrow else 128
    k = vw / vw0
    vh = vh0 * k
    vt = y + 44
    o.append(f'<g transform="translate({_n(x + (w - vw) / 2)},{_n(vt)}) scale({_n(k)})" opacity=".85">{body}</g>')
    wl = vt + vh + 6
    for k in range(6):
        px = x + 30 + k * (w - 60) / 5
        o.append(f'<rect x="{_n(px - 6)}" y="{_n(wl)}" width="12" height="9" fill="none" stroke="currentColor" stroke-width="1" opacity=".7"/>')
        o.append(P.text(px, wl + 20, 8, D(str(6 - k)), op=.7))
    dy = wl + 30 - (y + 94)
    # deux stations dans la liste
    sy = y + 94 + dy
    fw = w - 18 - 54
    for k, (n, arme, kg) in enumerate((('1', '2 x 9M114 Shturm', '104 kg'), ('2', 'B-8V20A - 20 x S-8KOM', '348 kg'))):
        yy = sy + k * 18
        o.append(P.text(x + 8, yy + 11, 8, D(n), anchor='start', op=.8))
        o.append(P.field(x + 18, yy, fw, 15, [D(arme)], size=8))
        o.append(P.text(x + w - 8, yy + 11, 8, D(kg), anchor='end', op=.75))
    sym = y + 138 + dy
    o.append(P.tick(x + 8, sym, True))
    o.append(P.text(x + 20, sym + 7, 8, L('fc', 'cmp.sym'), anchor='start'))
    o.append(P.text(x + 8, sym + 24, 8, L('fc', 'cmp.mass'), D(' 1 600 kg'), anchor='start', op=.8))
    # carburant, leurres, paillettes, canon : deux par rangée (un libellé comme « Carburant (kg) » ne tient pas dans le quart de la largeur au corps 8)
    fy = y + 168 + dy
    fwid = (w - 16 - 6) / 2
    last = None
    for k, (lab, val) in enumerate(((L('fc', 'lo.fuel', args={'u': 'kg'}), '1701'), (L('fc', 'lo.flare'), '192'), (L('fc', 'lo.chaff'), '0'), (L('fc', 'lo.gun'), '100'))):
        fx = x + 8 + (k % 2) * (fwid + 6)
        fyy = fy + (k // 2) * 29
        o.append(P.lfield(fx, fyy, fwid, [lab], [D(val)], size=8))
        if k == 3:
            last = (fx + fwid, fyy + 18)
    # Partir de, Garder dans mes presets…
    py = fy + 64
    sel = 96 if not narrow else 84
    o.append(P.lfield(x + 8, py, sel, [L('fc', 'cmp.from')], [L('fc', 'cmp.custom')], size=8))
    gw_ = 128 if not narrow else 118
    o.append(P.btn(x + 8 + sel + 6, py + 11, gw_, 15, [L('fc', 'cmp.save')], size=8))
    h = py + 34 - y
    o[0] = sv_box(x, y, w, h)
    anc = {'head': y + 12, 'sym': (x + 20 + 4.6 * 10 + 4, sym + 4), 'fuel': last, 'save': (x + 8 + sel + 6 + gw_, py + 18)}
    return o, h, anc


def _fc_wide(P):
    o = ['']          # l'ouverture du SVG est posée en dernier : sa hauteur suit les deux colonnes
    o.append(P.title_wide('L’ÉCRAN DU FLIGHT CONFIGURATOR', 'THE FLIGHT CONFIGURATOR SCREEN', 24, 32))
    o.append('<g transform="translate(0,22)">')
    X0, X1 = 110, 610
    tb, bx = _toolbar_wide(P, X0, X1, 'fc', 'toolbar.subtitle',
                           (('open', 56, [L('fc', 'tb.open', add='▾')]), ('save', 68, [L('fc', 'tb.save')]), ('export', 54, [L('fc', 'tb.export')]),
                            ('display', 66, [L('fc', 'tb.display', add='▾')]), ('clear', 48, [L('fc', 'tb.clear')])))
    o += tb
    o.append(f'<rect x="{X0}" y="78" width="{X1 - X0}" height="16" rx="2" fill="none" stroke="currentColor" stroke-width="1" opacity=".5"/>')
    o.append(P.text(X0 + 8, 89, 8, L('fc', 'bar.ok', args=(D('paquet_CAESAR.json'),)), anchor='start', op=.8))
    CT = 100
    # ── colonne de gauche : les groupes ──────────────────────────────────────────
    L0, L1 = X0, 350
    gx, gw, gy = L0 + 8, L1 - L0 - 16, CT + 30
    ux, uw, uy = gx + 6, gw - 12, gy + 68
    fy, fy2 = uy + 18, uy + 47
    ry = fy2 + 48
    rs, ry2 = _fc_radios(P, ux, uw, ry, True)
    ey = ry2 + 26
    UH = ey + 8 - uy
    u2y = uy + UH + 4
    addu = u2y + 22
    GH = addu + 15 + 8 - gy
    addg = gy + GH + 6
    o.append(sv_box(L0, CT, L1 - L0, addg + 16 + 8 - CT))
    o.append(P.text(L0 + 8, CT + 16, 8.5, L('fc', 'sec.flights'), D(' (1)'), anchor='start', ls=1.2))
    o.append(_rule(L0 + 8, L1 - 8, CT + 22))
    o.append(f'<rect x="{_n(gx)}" y="{_n(gy)}" width="{_n(gw)}" height="{_n(GH)}" rx="2" fill="none" stroke="currentColor" stroke-width="1" opacity=".7"/>')
    o += _fc_group_head(P, gx, gy, gw)
    o.append(P.lfield(gx + 8, gy + 22, 104, [L('fc', 'fl.name')], [D('CAESAR')]))
    o.append(P.lfield(gx + 118, gy + 22, 98, [L('fc', 'fl.coalition')], [L('fc', 'fl.coalition.red')]))
    o.append(_fc_route_line(P, gx + 8, gy + 60))
    o.append(f'<rect x="{_n(ux)}" y="{_n(uy)}" width="{_n(uw)}" height="{_n(UH)}" rx="2" fill="none" stroke="currentColor" stroke-width="1" opacity=".55"/>')
    o += _fc_unit_head(P, ux, uy, uw, '1')
    o.append(P.lfield(ux + 8, fy, 62, [L('fc', 'u.type')], [D('Mi-24P')]))
    o.append(P.lfield(ux + 74, fy, 62, [L('fc', 'u.name')], [D('CAESAR-1')]))
    o.append(P.lfield(ux + 140, fy, 62, [L('fc', 'u.callsign')], [D('CAESAR 1-1')]))
    o.append(P.lfield(ux + 8, fy2, 62, [L('fc', 'u.onboard')], [D('41')]))
    o.append(P.lfield(ux + 74, fy2, 128, [L('fc', 'u.livery')], [D('262nd_SHQ_USSR')]))
    o += rs
    o.append(P.text(ux + 8, ey, 8, L('fc', 'u.loadout'), anchor='start', op=.7))
    o.append(P.text(ux + 46, ey, 8, L('fc', 'cmp.custom'), anchor='start'))
    o.append(f'<rect x="{_n(ux)}" y="{_n(u2y)}" width="{_n(uw)}" height="16" rx="2" fill="none" stroke="currentColor" stroke-width="1" opacity=".55"/>')
    o += _fc_unit_head(P, ux, u2y, uw, '2')
    o.append(P.btn(ux, addu, 128, 15, [L('fc', 'u.add', args=('2',))], size=8))
    o.append(P.btn(gx, addg, 124, 16, [L('fc', 'fl.add')], size=8))
    # ── colonne de droite : la route, l'emport, les presets ─────────────────────
    R0, R1 = 358, X1
    rw = R1 - R0
    o.append(sv_box(R0, CT, rw, 96))
    o += _head(P, R0, CT, rw, [L('fc', 'sec.route'), D(' · CAESAR')])
    o.append(_rule(R0, R1, CT + 24))
    o.append(P.text(R0 + 8, CT + 40, 8.5, D('STEPPE WIND M3'), anchor='start'))
    o.append(P.text(R0 + 8, CT + 52, 8, L('fc', 'route.from.rp'), D(' · '), L('fc', 'route.pts.many', args=('6',)), D(' · 153,7 km', ' · 153.7 km'), anchor='start', op=.75))
    o.append(P.btn(R1 - 8 - 44, CT + 29, 44, 15, [L('fc', 'route.remove')], size=8))
    o.append(P.btn(R1 - 8 - 44 - 4 - 88, CT + 29, 88, 15, [L('fc', 'route.change')], size=8))
    o.append(P.text(R0 + 8, CT + 71, 8, L('fc', 'route.col.leg'), anchor='start', op=.6))
    o.append(P.text(R0 + 160, CT + 71, 8, L('fc', 'route.col.hdg'), anchor='end', op=.6))
    o.append(P.text(R1 - 8, CT + 71, 8, L('fc', 'route.col.dist'), anchor='end', op=.6))
    o.append(P.text(R0 + 8, CT + 84, 8, D('1   AKROTIRI → WP1'), anchor='start', op=.8))
    o.append(P.text(R0 + 160, CT + 84, 8, D('282°'), anchor='end', op=.8))
    o.append(P.text(R1 - 8, CT + 84, 8, D('30,1 km', '30.1 km'), anchor='end', op=.8))
    ey0 = CT + 102
    lo, EH, anc = _fc_loadout_block(P, R0, ey0, rw, False)
    o += lo
    py0 = ey0 + EH + 6
    o.append(sv_box(R0, py0, rw, 68))
    o += _head(P, R0, py0, rw, [L('fc', 'sec.presets')])
    o.append(_rule(R0, R1, py0 + 24))
    o.append(P.btn(R0 + 8, py0 + 30, 140, 15, [L('fc', 'pr.load')], size=8))
    o.append(P.text(R0 + 8, py0 + 60, 8, L('fc', 'pr.mine', args=('0',)), anchor='start', op=.7))
    o[0] = P.svg_open('pl-wide', 720, max(py0 + 68, addg + 16 + 8) + 22 + 10, 'L’écran du Flight Configurator, un groupe ouvert', 'The Flight Configurator screen, with a group open', 'fcw')
    # ── les bulles ───────────────────────────────────────────────────────────────
    mid = bx['export'][0] + bx['export'][1] / 2
    o.append(P.bubble(1, mid, 28, mid, 49))
    o.append(P.bubble(2, 80, CT + 12, L0, CT + 12))
    o.append(P.bubble(3, 80, gy + 8, gx, gy + 8))
    o.append(P.bubble(4, 80, gy + 41, gx + 8, gy + 41))
    o.append(P.bubble(5, 80, uy + 8, ux, uy + 8))
    o.append(P.bubble(6, ux + 138, fy2 + 26 + 12, ux + 138, fy2 + 26))
    o.append(P.bubble(7, 80, ry - 3, ux, ry - 3))
    o.append(P.bubble(8, 80, ry2 + 7, ux + 8, ry2 + 7))
    o.append(P.bubble(9, 80, addg + 8, gx, addg + 8))
    o.append(P.bubble(10, 640, CT + 12, R1, CT + 12))
    o.append(P.bubble(11, 640, anc['head'], R1, anc['head']))
    o.append(P.bubble(12, 640, anc['sym'][1], anc['sym'][0], anc['sym'][1]))
    o.append(P.bubble(13, 640, anc['fuel'][1], anc['fuel'][0], anc['fuel'][1]))
    o.append(P.bubble(14, 640, anc['save'][1], anc['save'][0], anc['save'][1]))
    o.append('</g>')
    o.append('</svg>')
    return '\n          '.join(o)


def _fc_tall(P):
    W = 360
    o = ['']          # l'ouverture du SVG est posée en dernier : sa hauteur suit le contenu
    o.append(P.title_tall('L’ÉCRAN DU FLIGHT CONFIGURATOR', 'THE FLIGHT CONFIGURATOR SCREEN', 'au téléphone', 'on a phone'))
    o.append('<g transform="translate(0,12)">')
    X0, X1 = 62, 298
    w = X1 - X0
    o.append(sv_box(X0, 62, w, 30))
    o.append(P.text(X0 + 10, 81, 8.5, D('◄'), anchor='start'))
    ic = {}
    x = X0 + 52
    for key, glyph in (('open', '▭'), ('save', '▣'), ('export', '⇪'), ('display', '◐'), ('clear', '⌫')):
        o.append(P.btn(x, 67, 26, 20))
        o.append(P.text(x + 13, 81, 9, D(glyph)))
        ic[key] = x + 13
        x += 30
    o.append(f'<rect x="{X0}" y="98" width="{w}" height="16" rx="2" fill="none" stroke="currentColor" stroke-width="1" opacity=".5"/>')
    o.append(P.text(X0 + 8, 109, 8, L('fc', 'bar.ok', args=(D('paquet_CAESAR.json'),)), anchor='start', op=.8))
    # le bloc des groupes
    GT = 122
    gx, gw, gy = X0 + 8, w - 16, GT + 30
    ux, uw, uy = gx + 6, gw - 12, gy + 68
    fy, fy2, fy3 = uy + 18, uy + 47, uy + 76
    ry = fy3 + 26 + 14
    ey = ry + 14
    UH = ey + 8 - uy
    u2y = uy + UH + 4
    addu = u2y + 22
    GH = addu + 15 + 8 - gy
    addg = gy + GH + 6
    o.append(sv_box(X0, GT, w, addg + 16 + 8 - GT))
    o.append(P.text(X0 + 8, GT + 16, 8.5, L('fc', 'sec.flights'), D(' (1)'), anchor='start', ls=1.2))
    o.append(_rule(X0 + 8, X1 - 8, GT + 22))
    o.append(f'<rect x="{_n(gx)}" y="{_n(gy)}" width="{_n(gw)}" height="{_n(GH)}" rx="2" fill="none" stroke="currentColor" stroke-width="1" opacity=".7"/>')
    o += _fc_group_head(P, gx, gy, gw)
    o.append(P.lfield(gx + 8, gy + 22, 98, [L('fc', 'fl.name')], [D('CAESAR')]))
    o.append(P.lfield(gx + 112, gy + 22, 100, [L('fc', 'fl.coalition')], [L('fc', 'fl.coalition.red')]))
    o.append(_fc_route_line(P, gx + 8, gy + 60))
    o.append(f'<rect x="{_n(ux)}" y="{_n(uy)}" width="{_n(uw)}" height="{_n(UH)}" rx="2" fill="none" stroke="currentColor" stroke-width="1" opacity=".55"/>')
    o += _fc_unit_head(P, ux, uy, uw, '1')
    o.append(P.lfield(ux + 8, fy, 92, [L('fc', 'u.type')], [D('Mi-24P')]))
    o.append(P.lfield(ux + 108, fy, 92, [L('fc', 'u.name')], [D('CAESAR-1')]))
    o.append(P.lfield(ux + 8, fy2, 92, [L('fc', 'u.callsign')], [D('CAESAR 1-1')]))
    o.append(P.lfield(ux + 108, fy2, 92, [L('fc', 'u.onboard')], [D('41')]))
    o.append(P.lfield(ux + 8, fy3, 192, [L('fc', 'u.livery')], [D('262nd_SHQ_USSR')]))
    rs, _ = _fc_radios(P, ux, uw, ry, False)
    o += rs
    o.append(P.text(ux + 8, ey, 8, L('fc', 'u.loadout'), anchor='start', op=.7))
    o.append(P.text(ux + 46, ey, 8, L('fc', 'cmp.custom'), anchor='start'))
    o.append(f'<rect x="{_n(ux)}" y="{_n(u2y)}" width="{_n(uw)}" height="16" rx="2" fill="none" stroke="currentColor" stroke-width="1" opacity=".55"/>')
    o += _fc_unit_head(P, ux, u2y, uw, '2')
    o.append(P.btn(ux, addu, 128, 15, [L('fc', 'u.add', args=('2',))], size=8))
    o.append(P.btn(gx, addg, 124, 16, [L('fc', 'fl.add')], size=8))
    # la route, l'emport, les presets
    RT = addg + 16 + 8 + 6
    o.append(sv_box(X0, RT, w, 74))
    o += _head(P, X0, RT, w, [L('fc', 'sec.route'), D(' · CAESAR')])
    o.append(_rule(X0, X1, RT + 24))
    o.append(P.text(X0 + 8, RT + 38, 8.5, D('STEPPE WIND M3'), anchor='start'))
    o.append(P.text(X0 + 8, RT + 49, 8, L('fc', 'route.from.rp'), D(' · '), L('fc', 'route.pts.many', args=('6',)), D(' · 153,7 km', ' · 153.7 km'), anchor='start', op=.75))
    o.append(P.btn(X0 + 8, RT + 54, 88, 15, [L('fc', 'route.change')], size=8))
    o.append(P.btn(X0 + 100, RT + 54, 44, 15, [L('fc', 'route.remove')], size=8))
    ET = RT + 80
    lo, EH, anc = _fc_loadout_block(P, X0, ET, w, True)
    o += lo
    PT = ET + EH + 6
    o.append(sv_box(X0, PT, w, 26))
    o += _head(P, X0, PT, w, [L('fc', 'sec.presets')])
    o[0] = P.svg_open('pl-tall', W, PT + 26 + 12 + 10, 'L’écran du Flight Configurator au téléphone, un groupe ouvert', 'The Flight Configurator screen on a phone, with a group open', 'fct')
    # les bulles : la barre au-dessus, le reste dans les marges
    o.append(P.bubble(1, ic['export'], 44, ic['export'], 67))
    o.append(P.bubble(2, 30, GT + 12, X0, GT + 12))
    o.append(P.bubble(3, 30, gy + 8, gx, gy + 8))
    o.append(P.bubble(4, 30, gy + 41, gx + 8, gy + 41))
    o.append(P.bubble(5, 30, uy + 8, ux, uy + 8))
    o.append(P.bubble(6, 30, fy3 + 16, ux + 8, fy3 + 16))
    o.append(P.bubble(7, 30, ry - 3, ux, ry - 3))
    o.append(P.bubble(9, 30, addg + 8, gx, addg + 8))
    o.append(P.bubble(10, 30, RT + 12, X0, RT + 12))
    o.append(P.bubble(11, 30, anc['head'], X0, anc['head']))
    o.append(P.bubble(12, 30, anc['sym'][1], anc['sym'][0], anc['sym'][1]))
    o.append(P.bubble(13, 30, anc['fuel'][1], X0 + 8, anc['fuel'][1]))
    o.append(P.bubble(14, 330, anc['save'][1], anc['save'][0], anc['save'][1]))
    o.append('</g>')
    o.append('</svg>')
    return '\n          '.join(o)


def _fc_legend_rows():
    return [
        (1, [L('fc', 'tb.export')],
         'écrit le paquet de vol : HQ applique ses parties cochées au groupe de même nom.',
         'writes the flight package: HQ applies its ticked parts to the group with the same name.'),
        (2, [L('fc', 'sec.flights')],
         'vos groupes sont partagés avec le Route Planner et le Datacard Generator : un groupe créé ou renommé dans l’un apparaît dans les autres.',
         'your groups are shared with the Route Planner and the Datacard Generator: a group created or renamed in one appears in the others.'),
        (3, [M('Un groupe', 'A group')],
         'sa carte se replie par la flèche à gauche de son nom ; ✕ le retire de tous les outils.',
         'its card folds by the arrow at the left of its name; ✕ removes it from all tools.'),
        (4, [L('fc', 'fl.name')],
         'et la coalition identifient le groupe. Deux groupes d’une même coalition ne portent pas le même nom : l’export est refusé.',
         'and the coalition identify the group. Two groups of the same coalition do not share a name: the export is refused.'),
        (5, [L('fc', 'u.title', args=('1',))],
         'son type, son nom, son indicatif, son numéro de bord et sa livrée. Changer le type d’une unité efface ses radios et son emport, avec confirmation.',
         'its type, its name, its call sign, its tail number and its livery. Changing a unit’s type clears its radios and loadout, with confirmation.'),
        (6, [L('fc', 'u.livery')],
         'une liste, celle du type de l’unité. Ce qu’elle affiche tant que vous n’avez rien choisi est dit plus bas, dans La livrée.',
         'a list, the unit type’s. What it shows until you choose is told below, in The livery.'),
        (7, [L('fc', 'u.radios')],
         'pour chaque poste de l’appareil, un champ par canal, numéroté comme au cockpit. La case devant un canal l’imprime sur la datacard du groupe : le Datacard Generator montre le même choix, mais le paquet de vol ne le porte pas.',
         'for each radio of the aircraft, one field per channel, numbered as in the cockpit. The box in front of a channel prints it on the group’s datacard: the Datacard Generator shows the same choice, but the flight package does not carry it.'),
        (8, [L('fc', 'rad.copy')],
         'écrit les mêmes canaux sur les unités du même type.',
         'writes the same channels on the units of the same type.'),
        (9, [L('fc', 'fl.add')],
         'ajoute un groupe, avec son nom, sa coalition et ses unités.',
         'adds a group, with its name, its coalition and its units.'),
        (10, [L('fc', 'sec.route')],
         'le bloc parle du groupe de l’unité choisie. Changer de route rouvre le choix, Retirer la vide.',
         'the block is about the chosen unit’s group. Change route reopens the choice, Remove empties it.'),
        (11, [L('fc', 'sec.cmp')],
         'l’unité choisie, que l’on touche sur sa carte, a son emport affiché ici : la vue de face de l’appareil, avec une case par station et la liste des armes permises. La masse totale et la masse estimée au décollage s’affichent, en orange au-delà du maximum recommandé.',
         'the chosen unit, which you tap on its card, has its loadout shown here: the aircraft’s front view, with one box per station and the list of permitted weapons. The total mass and the estimated take-off mass are shown, in orange beyond the recommended maximum.'),
        (12, [L('fc', 'cmp.sym')],
         'pose sur la station jumelle l’arme miroir. Une arme qui ne peut pas aller avec le reste est grisée, avec les stations qui la gênent ; le Kord du Mi-24P n’a qu’une porte.',
         'places the mirror weapon on the twin station. A weapon that cannot go with the rest is greyed out, with the stations that obstruct it; the Mi-24P’s Kord has only one door.'),
        (13, [L('fc', 'lo.fuel', args={'u': 'kg'}), D(', '), L('fc', 'lo.flare'), D(', '), L('fc', 'lo.chaff'), D(', '), L('fc', 'lo.gun')],
         'une valeur tapée hors limite est refusée.',
         'a typed value out of range is refused.'),
        (14, [L('fc', 'cmp.save')],
         'enregistre l’emport sous un nom ; « Charger des presets (.lua) » reprend les fichiers de presets de l’escadre ; « Partir de » propose ces presets et une copie de l’emport d’une autre unité du même type.',
         'saves the loadout under a name; “Load presets (.lua)” takes up the wing’s preset files; “Start from” offers those presets and a copy of another unit’s loadout of the same type.'),
    ]


def build_plate_fc():
    """La planche du Flight Configurator : le HTML (cadre, figure zoomable, légende) ; ses libellés viennent du dictionnaire du FC."""
    P = Plate('fc', ['fc'])
    wide, tall = _fc_wide(P), _fc_tall(P)
    legend = P.legend_html(_fc_legend_rows())
    P.verify(wide, tall)
    return P.figure_html(wide, tall,
                         'Fig. 1 — L’écran du Flight Configurator, un groupe ouvert : la liste des groupes, leurs unités, puis la route, l’emport et les presets.',
                         'Fig. 1 — The Flight Configurator screen with a group open: the group list, its units, then the route, the loadout and the presets.', legend)


# ═════════════════════════════════════════════════════════════════════════════════
# La planche du Datacard Generator : l'éditeur et l'aperçu
# ═════════════════════════════════════════════════════════════════════════════════

_DG_SECTIONS = (('header', 'sec.header'), ('group', 'sec.group'), ('mission', 'sec.mission'), ('times', 'sec.times'), ('nav', 'sec.nav'), ('refs', 'sec.refs'),
                ('radio', 'sec.radio'), ('fields', 'sec.fields'), ('weather', 'sec.weather'), ('fuel', 'sec.fuel'), ('threats', 'sec.threats'), ('meta', 'sec.meta'))


def _dg_pack_bar(P, x, y, w):
    """La barre du paquet : la carte choisie et sa pastille, +, …, puis le résumé. y est le haut ; renvoie (SVG, ancres, bas)."""
    o = []
    pw = w - 16 - 2 * 22
    o.append(P.field(x + 8, y + 8, pw, 18))
    o.append(P.text(x + 14, y + 20, 8.5, D('CAESAR'), anchor='start'))
    s, _w = P.pill(x + 14 + 6.2 * 6 + 6, y + 12, [L('dg', 'pack.tag.linked', up=True)], size=8, h=11)
    o.append(s)
    px, mx = x + 8 + pw + 4, x + 8 + pw + 4 + 22
    o.append(P.btn(px, y + 8, 18, 18, [D('+')], size=10))
    o.append(P.btn(mx, y + 8, 18, 18, [D('…')], size=10))
    o.append(P.text(x + 8, y + 41, 8, L('dg', 'sum.unit', args={'n': '2'}), D(' · Mi-24P · '), L('dg', 'coal.red'), D(' — 1 / 1'), anchor='start', op=.65))
    return o, {'pick': (x + 8, y + 17), 'plus': (px + 9, y + 8), 'more': (mx + 9, y + 8)}, y + 48


def _dg_wide(P):
    o = ['']          # l'ouverture du SVG est posée en dernier : sa hauteur suit l'éditeur
    o.append(P.title_wide('L’ÉCRAN DU DATACARD GENERATOR', 'THE DATACARD GENERATOR SCREEN', 24, 32))
    o.append('<g transform="translate(0,22)">')
    X0, X1 = 110, 610
    tb, bx = _toolbar_wide(P, X0, X1, 'dg', 'tb.subtitle',
                           (('open', 56, [L('dg', 'tb.json.import', add='▾')]), ('save', 68, [L('dg', 'tb.json.export')]), ('export', 54, [L('dg', 'tb.export')]),
                            ('display', 66, [L('dg', 'tb.display', add='▾')]), ('clear', 48, [L('dg', 'tb.reset')])))
    o += tb
    E0, E1 = X0, 336
    CT = 100
    pb, anc, y = _dg_pack_bar(P, E0, CT, E1 - E0)
    body = []
    y += 4
    pos = {}
    opened = {'group', 'nav', 'radio', 'weather'}
    for key, dk in _DG_SECTIONS:
        n = [k for k, _d in _DG_SECTIONS].index(key) + 1
        body.append(f'<rect x="{_n(E0 + 8)}" y="{_n(y)}" width="{_n(E1 - E0 - 16)}" height="15" rx="2" fill="none" stroke="currentColor" stroke-width="1" opacity=".6"/>')
        body.append(P.text(E0 + 14, y + 10.5, 8, D('%02d ░ ' % n), L('dg', dk), anchor='start'))
        body.append(fold_icon(E1 - 8 - 18, y + 2))
        pos[key] = y
        y += 15
        if key not in opened:
            y += 3
            continue
        if key == 'group':
            body.append(P.lfield(E0 + 14, y + 4, 98, [L('dg', 'f.group.name')], [D('CAESAR')], badge=True))
            body.append(P.lfield(E0 + 120, y + 4, 98, [L('dg', 'f.coalition')], [L('dg', 'coal.red')], badge=True))
            pos['group_f'] = y + 4 + 11 + 7.5
            y += 4 + 26 + 6
        elif key == 'nav':
            body.append(P.text(E0 + 14, y + 14, 8, L('dg', 'nr.k'), anchor='start', op=.7))
            body.append(P.text(E0 + 44, y + 14, 8, D('STEPPE WIND M3'), anchor='start'))
            s, _w = P.pill(E0 + 44 + 4.7 * 14 + 8, y + 5, [L('dg', 'nr.tag')], size=8, h=11)
            body.append(s)
            y += 24
        elif key == 'radio':
            body.append(P.text(E0 + 14, y + 11, 8, L('dg', 'rt.title', args={'type': 'MI-24P'}), anchor='start', op=.7))
            body.append(P.text(E0 + 14, y + 28, 8, L('dg', 'rt.ch', args={'n': '0'}), anchor='start', op=.8))
            body.append(P.field(E0 + 42, y + 17, 60, 15, [D('127.500')], size=8))
            body.append(P.tick(E0 + 110, y + 20.5, True))
            body.append(P.text(E0 + 121, y + 28, 8, L('dg', 'rt.on'), anchor='start', op=.8))
            y += 38
        elif key == 'weather':
            body.append(P.lfield(E0 + 14, y + 4, 204, [L('dg', 'f.metar')], [D('LCRA 221000Z 18002KT 9999 SCT082')]))
            y += 4 + 26 + 6
    y += 4
    editor_end = y
    o[0] = P.svg_open('pl-wide', 720, editor_end + 22 + 10, 'L’écran du Datacard Generator, une carte ouverte', 'The Datacard Generator screen, with a card open', 'dgw')
    o.append(sv_box(E0, CT, E1 - E0, editor_end - CT))
    o += pb
    o += body
    # l'aperçu : une page, ses blocs, son numéro
    P0, P1 = 344, X1
    o.append(sv_box(P0, CT, P1 - P0, editor_end - CT))
    o.append(f'<rect x="{_n(P0 + 8)}" y="{_n(CT + 8)}" width="{_n(P1 - P0 - 16)}" height="{_n(editor_end - CT - 16)}" rx="1.5" fill="none" stroke="currentColor" stroke-width="1" opacity=".5"/>')
    o.append(P.text(P1 - 14, CT + 22, 8, D('1 / 2'), anchor='end', op=.8))
    o.append(_bars(P0 + 16, CT + 22, 90, 1))
    o.append(_bars(P0 + 16, CT + 33, 130, 1))
    for (bx0, by0, bw, bh) in ((P0 + 16, CT + 50, 150, 80), (P0 + 172, CT + 50, 66, 80), (P0 + 16, CT + 140, 100, 70), (P0 + 122, CT + 140, 116, 70),
                               (P0 + 16, CT + 220, 222, 70), (P0 + 16, CT + 300, 100, 60), (P0 + 122, CT + 300, 116, 60)):
        o.append(f'<rect x="{_n(bx0)}" y="{_n(by0)}" width="{_n(bw)}" height="{_n(bh)}" rx="1.5" fill="none" stroke="currentColor" stroke-width="1" opacity=".35"/>')
        o.append(_bars(bx0 + 6, by0 + 12, bw - 12, max(1, int((bh - 14) // 12)), gap=12))
    # les bulles
    mid = lambda k: bx[k][0] + bx[k][1] / 2
    o.append(P.bubble(1, mid('export'), 28, mid('export'), 49))
    o.append(P.bubble(2, mid('display'), 28, mid('display'), 49))
    o.append(P.bubble(3, 80, anc['pick'][1], anc['pick'][0], anc['pick'][1]))
    o.append(P.bubble(4, anc['plus'][0], 86, anc['plus'][0], anc['plus'][1]))
    o.append(P.bubble(5, anc['more'][0], 86, anc['more'][0], anc['more'][1]))
    o.append(P.bubble(6, 80, pos['header'] + 7.5, E0 + 8, pos['header'] + 7.5))
    o.append(P.bubble(7, 80, pos['group_f'], E0 + 14, pos['group_f']))
    o.append(P.bubble(8, 80, pos['nav'] + 7.5, E0 + 8, pos['nav'] + 7.5))
    o.append(P.bubble(9, 80, pos['radio'] + 7.5, E0 + 8, pos['radio'] + 7.5))
    o.append(P.bubble(10, 80, pos['fields'] + 7.5, E0 + 8, pos['fields'] + 7.5))
    o.append(P.bubble(11, 80, pos['weather'] + 7.5, E0 + 8, pos['weather'] + 7.5))
    o.append(P.bubble(12, 640, CT + 22, P1, CT + 22))
    o.append('</g>')
    o.append('</svg>')
    return '\n          '.join(o)


def _dg_tall(P):
    W = 360
    o = [P.svg_open('pl-tall', W, 395, 'L’écran du Datacard Generator au téléphone, une carte ouverte', 'The Datacard Generator screen on a phone, with a card open', 'dgt')]
    o.append(P.title_tall('L’ÉCRAN DU DATACARD GENERATOR', 'THE DATACARD GENERATOR SCREEN', 'au téléphone', 'on a phone'))
    o.append('<g transform="translate(0,12)">')
    X0, X1 = 62, 298
    w = X1 - X0
    o.append(sv_box(X0, 62, w, 30))
    o.append(P.text(X0 + 10, 81, 8.5, D('◄'), anchor='start'))
    o.append(P.text(X0 + 34, 81, 8.5, L('dg', 'app.short')))
    ic = {}
    x = X0 + 52
    for key, glyph in (('open', '▭'), ('save', '▣'), ('export', '⇪'), ('display', '◐'), ('clear', '⌫')):
        o.append(P.btn(x, 67, 26, 20))
        o.append(P.text(x + 13, 81, 9, D(glyph)))
        ic[key] = x + 13
        x += 30
    # la barre du paquet, puis le panneau ouvert : l'onglet Groupe
    PT = 112
    o.append(sv_box(X0, PT, w, 54))
    pb, anc, _y = _dg_pack_bar(P, X0, PT, w)
    o += pb
    o.append(sv_box(X0, PT + 60, w, 118))
    o.append(P.text(X0 + 10, PT + 76, 8, D('02 ░ '), L('dg', 'sec.group'), anchor='start'))
    fy = PT + 84
    o.append(P.lfield(X0 + 10, fy, 98, [L('dg', 'f.group.name')], [D('CAESAR')], badge=True))
    o.append(P.lfield(X0 + 118, fy, 106, [L('dg', 'f.coalition')], [L('dg', 'coal.red')], badge=True))
    o.append(P.lfield(X0 + 10, fy + 29, 98, [L('dg', 'f.aircraft')], [D('Mi-24P')]))
    o.append(P.lfield(X0 + 118, fy + 29, 106, [L('dg', 'f.count')], [D('2')]))
    o.append(P.lfield(X0 + 10, fy + 58, 98, [L('dg', 'f.task')], [D('CAS')]))
    o.append(P.lfield(X0 + 118, fy + 58, 106, [L('dg', 'f.threat')], [L('dg', 'thr.high')]))
    # la barre d'onglets : la largeur de chaque onglet suit son libellé
    TT = PT + 188
    o.append(sv_box(X0, TT, w, 40))
    tabs = (('▤', 'sec.header', False), ('✈', 'tab.group', True), ('▣', 'sec.mission', False), ('⏱', 'sec.times', False), ('⌖', 'sec.nav', False))
    lens = [len(P.resolve([L('dg', key)])[0]) for _g, key, _c in tabs]
    widths = [12 + 4.6 * n for n in lens]
    k_ = w / sum(widths)
    widths = [x_ * k_ for x_ in widths]
    tx, navx = X0, None
    for (g, key, cur), tw in zip(tabs, widths):
        cx = tx + tw / 2
        if cur:
            o.append(f'<rect x="{_n(tx + 2)}" y="{_n(TT + 3)}" width="{_n(tw - 4)}" height="34" rx="2" fill="none" stroke="currentColor" stroke-width="1.4"/>')
        o.append(P.text(cx, TT + 16, 9, D(g)))
        o.append(P.text(cx, TT + 31, 8, L('dg', key)))
        if key == 'sec.nav':
            navx = cx
        tx += tw
    o.append(P.bubble(1, ic['export'], 44, ic['export'], 67))
    o.append(P.bubble(2, ic['display'], 44, ic['display'], 67))
    o.append(P.bubble(3, 30, anc['pick'][1], anc['pick'][0], anc['pick'][1]))
    o.append(P.bubble(4, anc['plus'][0], 102, anc['plus'][0], anc['plus'][1]))
    o.append(P.bubble(5, anc['more'][0], 102, anc['more'][0], anc['more'][1]))
    o.append(P.bubble(6, 30, TT + 20, X0, TT + 20))
    o.append(P.bubble(7, 30, fy + 16, X0 + 10, fy + 16))
    o.append(P.bubble(8, navx, TT + 58, navx, TT + 40))
    o.append('</g>')
    o.append('</svg>')
    return '\n          '.join(o)


def _dg_legend_rows():
    return [
        (1, [L('dg', 'tb.export')],
         'propose le PDF ou le PNG : le PDF passe par l’impression du navigateur, une feuille par page ; le PNG est une image par page au format d’une page de kneeboard, et plusieurs pages partent dans un ZIP. L’export suit la version jour ou nuit affichée.',
         'offers PDF or PNG: the PDF goes through the browser’s print, one sheet per page; the PNG is one image per page in the format of a kneeboard page, and several pages leave in a ZIP. The export follows the day or night version shown.'),
        (2, [L('dg', 'tb.display', add='▾')],
         'Jour | Nuit donne à tout le paquet sa version de jour ou de nuit ; seule cette bascule compte, les thèmes de l’outil ne changent pas la datacard. Les unités, partagées avec le Route Planner et le Flight Configurator, changent les intitulés de la fiche ; les valeurs saisies ne sont pas converties, sauf celles de la ligne carburant.',
         'Day | Night gives the whole deck its day or night version; only this switch counts, the tool’s themes do not change the datacard. The units, shared with the Route Planner and the Flight Configurator, change the sheet’s labels; entered values are not converted, except those of the fuel line.'),
        (3, [M('Le paquet de cartes', 'The deck of cards')],
         'une ligne choisit la carte, avec sa pastille LIÉE à un groupe, LIBRE ou GROUPE SUPPRIMÉ.',
         'a row chooses the card, with its badge LINKED to a group, FREE or GROUP DELETED.'),
        (4, [M('+', '+')],
         'ajoute une datacard liée à un groupe.',
         'adds a datacard linked to a group.'),
        (5, [M('…', '…')],
         'ouvre les autres actions sur les cartes. La dernière carte ne se supprime pas : elle se vide.',
         'opens the other actions on the cards. The last card cannot be deleted: it is emptied.'),
        (6, [M('Les sections de l’éditeur', 'The editor sections')],
         'suivent la page. Chacune se replie par l’icône à droite de son en-tête.',
         'follow the page. Each folds by the icon at the right of its header.'),
        (7, [M('La pastille FC', 'The FC badge')],
         'marque les champs partagés : la carte d’un groupe reprend de la fiche des groupes ce que le Flight Configurator règle — unités, radios, emport, carburant et poids.',
         'marks the shared fields: a group’s card takes from the group sheet what the Flight Configurator sets — units, radios, loadout, fuel and weight.'),
        (8, [L('dg', 'sec.nav')],
         'la navigation d’une datacard est une route du Route Planner : un point saisi, déplacé ou supprimé ici l’est aussi là-bas, et inversement ; l’heure et la note restent à la datacard.',
         'a datacard’s navigation is a Route Planner route: a point entered, moved or deleted here is so there too, and the other way round; the time and the note stay on the datacard.'),
        (9, [L('dg', 'sec.radio')],
         'les canaux à imprimer se cochent ici, comme au Flight Configurator.',
         'the channels to print are ticked here, as in the Flight Configurator.'),
        (10, [L('dg', 'sec.fields')],
         'le nom d’un terrain se choisit dans la liste des aérodromes du théâtre, qui remplit le reste ; DEP et ARR viennent de la route.',
         'an airfield’s name is chosen from the theatre’s airfield list, which fills in the rest; DEP and ARR come from the route.'),
        (11, [L('dg', 'sec.weather')],
         'le METAR, saisi ou importé, se décode en vent, visibilité, QNH et nuages, modifiables ensuite.',
         'the METAR, entered or imported, decodes into wind, visibility, QNH and clouds, editable afterwards.'),
        (12, [M('L’aperçu', 'The preview')],
         'la datacard page par page, avec « 1 / 2 » en haut à droite. Voir Quand la page déborde.',
         'the datacard page by page, with “1 / 2” at the top right. See When the page overflows.'),
    ]


def build_plate_dg():
    """La planche de l'éditeur du Datacard Generator : le HTML (cadre, figure zoomable, légende) ; ses libellés viennent du dictionnaire du DG."""
    P = Plate('dg', ['dg'])
    wide, tall = _dg_wide(P), _dg_tall(P)
    legend = P.legend_html(_dg_legend_rows())
    P.verify(wide, tall)
    return P.figure_html(wide, tall,
                         'Fig. 2 — L’éditeur du Datacard Generator, une carte ouverte : la barre du paquet, les sections, puis l’aperçu de la page.',
                         'Fig. 2 — The Datacard Generator editor with a card open: the deck bar, the sections, then the page preview.', legend)
