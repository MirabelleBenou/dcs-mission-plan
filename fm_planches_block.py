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
import json
import os
import re

from fm_schemas_block import sv_text, sv_box, sv_defs, _n, _esc, fr_typo

HERE = os.path.dirname(os.path.abspath(__file__))

# L'erreur d'une planche ne s'élève pas : elle s'inscrit ici, et le build du FM sort en 1 une fois tous ses contrôles écrits.
PLANCHE_ERRORS = []
PLATES = []          # les planches construites, pour le compte rendu du build

TOOL_SOURCES = {'hq': 'build_hq.py', 'fc': 'build_flight_configurator.py', 'dg': 'build_datacard_generator.py',
                'rp': 'build_route_planner.py', 'bg': 'build_briefing_generator.py', 'rs': 'build_recon_station.py', 'mp': 'build_mission_plan.py'}
TOOL_NAMES = {'hq': 'HQ', 'fc': 'Flight Configurator', 'dg': 'Datacard Generator',
              'rp': 'Route Planner', 'bg': 'Briefing Generator', 'rs': 'Recon Station', 'mp': 'Mission Plan'}


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


_DECL = re.compile(r'(?:const|var) I18N = \{\s*(?:fr|en)\s*:\s*\{')
_EXPR0, _EXPR1 = '\ue000', '\ue001'      # entourent le rang d'une expression d'une f-string qui n'est pas une chaîne littérale du premier niveau


def _bound_once_strings(tree):
    """Les noms liés une seule fois dans tout le module, à n'importe quelle portée, et à un littéral de chaîne : {nom: texte}.
    Lient un nom : une affectation (simple, augmentée, annotée, morse), global, nonlocal, une cible de for, with, import, except, un paramètre, un def ou une class."""
    count, val = {}, {}

    def bind(name):
        count[name] = count.get(name, 0) + 1
    for n in ast.walk(tree):
        if isinstance(n, ast.Name) and isinstance(n.ctx, (ast.Store, ast.Del)):
            bind(n.id)
        elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            bind(n.name)
        elif isinstance(n, ast.arg):
            bind(n.arg)
        elif isinstance(n, (ast.Import, ast.ImportFrom)):
            for al in n.names:
                bind((al.asname or al.name).split('.')[0])
        elif isinstance(n, (ast.Global, ast.Nonlocal)):
            for nm in n.names:
                bind(nm)
        elif isinstance(n, ast.ExceptHandler) and n.name:
            bind(n.name)
        elif isinstance(n, ast.AugAssign) and isinstance(n.target, ast.Name):
            bind(n.target.id)            # une affectation augmentée lie le nom une fois de plus
    for n in ast.walk(tree):
        if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name) \
                and isinstance(n.value, ast.Constant) and isinstance(n.value.value, str):
            val[n.targets[0].id] = n.value.value
    return {k: v for k, v in val.items() if count.get(k) == 1}


def _retouches(tree, fstr, dict_text):
    """Les retouches, après la f-string, de la variable qui la reçoit. Seule est permise X = X.replace(a, b[, n]) (ou une chaîne de .replace sur X) où a est une chaîne littérale
    absente du texte lu du dictionnaire. Renvoie les messages d'erreur."""
    scope = tree
    recv = None
    for n in ast.walk(tree):
        if isinstance(n, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef)):
            for st in ast.walk(n):
                if isinstance(st, ast.Assign) and st.value is fstr and len(st.targets) == 1 and isinstance(st.targets[0], ast.Name):
                    recv, scope = st.targets[0].id, n
    if recv is None:
        return []
    errs = []

    def root(e):
        while True:
            if isinstance(e, ast.Call):
                e = e.func
            elif isinstance(e, ast.Attribute):
                e = e.value
            else:
                return e

    def chain_ok(e, line):
        """e : X ou X.replace(a, b[, n])[.replace(…)] ; renvoie True si la chaîne est permise (messages ajoutés sinon)."""
        ok = True
        while isinstance(e, ast.Call):
            f = e.func
            if not (isinstance(f, ast.Attribute) and f.attr == 'replace' and 2 <= len(e.args) <= 3 and not e.keywords):
                errs.append('ligne %d : %s est retouché autrement que par .replace(a, b[, n])' % (line, recv))
                return False
            a = e.args[0]
            if not (isinstance(a, ast.Constant) and isinstance(a.value, str)):
                errs.append('ligne %d : %s.replace(…) dont le premier argument n’est pas une chaîne littérale : %s' % (line, recv, ast.unparse(a)[:60]))
                ok = False
            elif a.value in dict_text:
                errs.append('ligne %d : %s.replace(%r, …) : ce texte est dans le dictionnaire' % (line, recv, a.value[:60]))
                ok = False
            e = f.value
        return ok and isinstance(e, ast.Name) and e.id == recv
    inner = set()
    for n in ast.walk(scope):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and isinstance(n.func.value, ast.Call):
            inner.add(id(n.func.value))
    for n in ast.walk(scope):
        if getattr(n, 'lineno', 0) <= fstr.lineno:
            continue
        if isinstance(n, ast.Assign) and n.value is not fstr and any(isinstance(t, ast.Name) and t.id == recv for t in n.targets):
            r = root(n.value)
            if len(n.targets) != 1 or not (isinstance(n.value, ast.Call) and isinstance(r, ast.Name) and r.id == recv):
                errs.append('ligne %d : %s est ré-affecté autrement que par %s = %s.replace(a, b)' % (n.lineno, recv, recv, recv))
        elif isinstance(n, ast.AugAssign) and isinstance(n.target, ast.Name) and n.target.id == recv:
            errs.append('ligne %d : %s est retouché par une affectation augmentée' % (n.lineno, recv))
        elif isinstance(n, ast.Call) and id(n) not in inner and isinstance(n.func, ast.Attribute):
            r = root(n.func)
            if isinstance(r, ast.Name) and r.id == recv:
                chain_ok(n, n.lineno)
    return errs


def _js_texts(tree):
    """Les textes JS que le source Python écrit : chaque littéral de chaîne (la valeur que Python lui donne) et chaque f-string (ses parties constantes, « {{ » déjà « { » ;
    ses valeurs {NOM} remplacées par la chaîne littérale du premier niveau de ce nom). Toute autre expression est remplacée par un repère, avec son texte. Renvoie [(texte, [expressions], nœud)]."""
    top = _bound_once_strings(tree)
    inner = {id(v) for n in ast.walk(tree) if isinstance(n, ast.JoinedStr) for v in n.values}
    out = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in inner:
            out.append((n.value, [], n))
        elif isinstance(n, ast.JoinedStr):
            parts, exprs = [], []
            for v in n.values:
                if isinstance(v, ast.Constant):
                    parts.append(v.value)
                elif isinstance(v.value, ast.Name) and v.value.id in top and v.conversion == -1 and v.format_spec is None:
                    parts.append(top[v.value.id])
                else:
                    parts.append(_EXPR0 + str(len(exprs)) + _EXPR1)
                    exprs.append('{' + ast.unparse(v.value) + '}')
            out.append((''.join(parts), exprs, n))
    return out


def _read_js_dicts(src):
    """Le dictionnaire « const I18N = { fr: {…}, en: {…} } » (ou « var ») d'un outil dont le source Python porte le JS dans une chaîne ou une f-string.
    Le texte JS est celui que Python écrit : les chaînes constantes (littéral brut, ou parties constantes d'une f-string, où « {{ » est déjà « { » ; une valeur {NOM} y est le littéral du premier
    niveau de ce nom). Une autre expression dans le dictionnaire est une erreur. L'objet se lit clé par clé (fr ou en, « : », « { », le bloc, puis « , » ou « } ») :
    exactement les deux clés, une fois chacune, dans n'importe quel ordre."""
    tree = ast.parse(src)
    hits = [(js, ex, nd) for js, ex, nd in _js_texts(tree) if _DECL.search(js)]
    if len(hits) != 1:
        raise ValueError('const I18N : %d occurrence(s) dans le source, une attendue' % len(hits))
    js, exprs, node = hits[0]

    def show(t):
        return re.sub(_EXPR0 + r'(\d+)' + _EXPR1, lambda m: exprs[int(m.group(1))], t)
    try:
        fr, en, span = _read_i18n_object(js, show)
    except ValueError as e:
        raise ValueError(show(str(e))) from None
    if isinstance(node, ast.JoinedStr):
        dict_text = span + '\n' + '\n'.join(list(fr) + list(fr.values()) + list(en) + list(en.values()))
        errs = _retouches(tree, node, dict_text)
        if errs:
            raise ValueError('const I18N : la f-string est retouchée après coup : ' + ' ; '.join(errs))
    return fr, en


def _read_i18n_object(js, show):
    start = _DECL.search(js)
    i = re.compile(r'(?:const|var) I18N = \{').match(js, start.start()).end()
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
    span = js[start.start():i + 1]
    k = re.search(_EXPR0 + r'(\d+)' + _EXPR1, span)
    if k:
        raise ValueError('const I18N : une expression qui n’est pas une chaîne littérale du premier niveau dans le dictionnaire : ' + show(k.group(0)))
    return found['fr'], found['en'], span


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


_EXTRA = re.compile(r'^(?:\s+[A-Za-z_:][\w:.-]*="[^"<>]*")+$')
_WORDS = re.compile(r'[\s░·]+')
_NORM = re.compile(r'[\W_]+')


def _norm(t):
    return _NORM.sub('', t.casefold())


# Les données d'exemple qui tombent, par hasard, sur une valeur du dictionnaire de l'outil : (planche, texte français) → raison. Rien d'autre.
D_EXCEPTIONS = {
    # la pastille de coalition de l'instantané affiche la valeur brute du groupe (fl.coalition), pas le libellé traduit de pk.flt.red
    ('hq', 'Red'): 'valeur brute de coalition affichée par l’outil, pas le libellé du filtre',
    ('hq', 'red'): 'le même, par mot (K1) : valeur brute de coalition affichée par l’outil',
    # le nom de la mission d'exemple, STEPPE WIND, est une donnée ; « wind » est aussi un libellé de météo du dictionnaire du DG
    ('dg', 'wind'): 'mot du nom de la mission d’exemple STEPPE WIND, pas le libellé de la météo',
    # le sigle court de la barre téléphone est écrit en dur dans l'outil (build_hq.py, tb-brand-short), hors dictionnaire ; sa norme tombe sur « HQ »
    ('hq', 'H·Q'): 'sigle écrit en dur dans l’outil, non traduit',
    # valeur d'exemple de la ligne Paillettes : le reste du gabarit « {0} % » une fois l'argument retiré
    ('fc', '0'): 'nombre d’exemple, égal au résidu du gabarit lo.pct',
    # le titre du bandeau de l'accueil est écrit en dur dans le shell ; sa norme tombe sur le bouton de retour « ◄ Mission Plan » (clé back)
    ('start', 'MISSION PLAN'): 'titre du bandeau écrit en dur dans l’accueil, distinct du bouton de retour',
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
        if isinstance(v, (list, tuple)) and v and all(isinstance(x, _Part) for x in v):
            return ''.join(self._slot(x, li) for x in v)
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
            for w in _WORDS.split(txt):
                nw = _norm(w)
                if len(nw) >= 2 and nw in self._dvals and (self.pid, nw) not in D_EXCEPTIONS and (self.pid, p.fr, nw) not in self._dseen:
                    self._dseen.add((self.pid, p.fr, nw))
                    PLANCHE_ERRORS.append('FAIL planche %s : la donnée d’exemple « %s » porte le mot « %s », une valeur du dictionnaire de l’outil : écrivez le libellé par L, accolé à la donnée (ou ajoutez une exception motivée, une par planche et par mot)' % (self.pid, p.fr, w))

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

    def text(self, x, y, size, *parts, **kw):
        if '_m' in kw:
            kw.pop('_m')
            PLANCHE_ERRORS.append('FAIL planche %s : _m n’est pas un argument de text() : un titre du manuel s’écrit par les titres de planche' % self.pid)
        return self._text(x, y, size, parts, False, kw)

    def _title_text(self, x, y, size, *parts, **kw):
        """Le seul chemin d'un titre du manuel dans un <text> : les titres de planche."""
        return self._text(x, y, size, parts, True, kw)

    def _text(self, x, y, size, parts, _m, kw):
        """Un <text> (FR puis EN) de la planche, écrit par le genre de ses parties. Le genre M (titre du manuel) n'y entre que par les titres de planche (_m)."""
        fr, en, kind = self.resolve(parts)
        ex = kw.get('extra', '')
        if ex and not _EXTRA.match(ex):
            PLANCHE_ERRORS.append('FAIL planche %s : extra= n’accepte que des attributs (nom="valeur", sans < ni >) : %r' % (self.pid, ex))
            kw = {k: v for k, v in kw.items() if k != 'extra'}
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
        return (self._title_text(360, y, 13, M(fr, en), op=.9, ls=3) + '\n          '
                f'<line x1="120" y1="{_n(y_rule)}" x2="600" y2="{_n(y_rule)}" stroke="currentColor" stroke-width=".6" opacity=".3"/>')

    def title_tall(self, fr, en, sub_fr, sub_en, w=360):
        """Le titre de la variante haute et son sous-titre."""
        return (self._title_text(w / 2, 22, 12, M(fr, en), op=.9, ls=2.5) + '\n          '
                + self._title_text(w / 2, 38, 8.5, M(sub_fr, sub_en), op=.7))

    def svg_open(self, cls, w, h, aria_fr, aria_en, marker):
        return (f'<svg class="{cls}" viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{_q(aria_fr)}" '
                f'data-aria-fr="{_q(aria_fr)}" data-aria-en="{_q(aria_en)}">\n          ' + sv_defs(marker))

    # ── la légende numérotée ─────────────────────────────────────────────────────
    def _bodies(self, n, tf, te):
        """Les corps FR et EN d'une ligne de légende : un texte, ou une suite de textes et de libellés de l'outil (L), écrits tels que l'écran les affiche.
        Les deux langues portent la même suite de libellés (mêmes clés, même ordre) ; chaque libellé est lu et compté une fois."""
        if isinstance(tf, str) and isinstance(te, str):
            return tf, te
        lf = [x for x in ([tf] if isinstance(tf, str) else tf) if not isinstance(x, str)]
        le = [x for x in ([te] if isinstance(te, str) else te) if not isinstance(x, str)]
        for x in lf + le:
            if x.kind != 'L':
                PLANCHE_ERRORS.append('FAIL planche %s : le corps d’une légende n’admet que du texte et des libellés de l’outil (ligne %s)' % (self.pid, n))
                return '?', '?'
        kf, ke = [(x.tool, x.key) for x in lf], [(x.tool, x.key) for x in le]
        if kf != ke:
            PLANCHE_ERRORS.append('FAIL planche %s : légende ligne %s : le corps FR et le corps EN ne citent pas les mêmes libellés de l’outil, dans le même ordre (FR %s, EN %s)'
                                  % (self.pid, n, [k for _t, k in kf], [k for _t, k in ke]))
            return '?', '?'
        res = [self._label(x) for x in lf]
        self.counts['L'] += len(lf)

        def build(t, li):
            out, k = '', 0
            for x in ([t] if isinstance(t, str) else t):
                if isinstance(x, str):
                    out += x
                else:
                    out += res[k][li]
                    k += 1
            return out
        return build(tf, 0), build(te, 1)

    def legend_html(self, rows):
        """rows : (n, parties du titre, texte FR, texte EN). Le titre en gras est un libellé de l'outil ou un titre du manuel."""
        li = []
        for n, title, tf, te in rows:
            fr, en, kind = self.resolve(title)
            if kind not in ('L', 'M'):
                PLANCHE_ERRORS.append('FAIL planche %s : le titre en gras de la légende (ligne %s) doit être un libellé de l’outil ou un titre du manuel : « %s »' % (self.pid, n, fr))
            self.counts[kind] += 1
            tf, te = self._bodies(n, tf, te)
            li.append(f'<li><span class="pl-n">{n}</span><span class="lang-block" data-lang="fr"><b>{_esc(fr_typo(fr))}</b> — {_esc(fr_typo(tf))}</span>'
                      f'<span class="lang-block" data-lang="en"><b>{_esc(en)}</b> — {_esc(te)}</span></li>')
        return '<ol class="pl-legend">' + ''.join(li) + '</ol>'

    def figure_html(self, wide, tall, cap_fr, cap_en, legend, anchor=None):
        """La planche : le cadre, la figure zoomable (variante large, variante haute, « Fig. 1 — … »), puis la légende numérotée ; anchor : l'ancre de la planche."""
        return (f'<div class="fm-plate"' + (f' id="{anchor}"' if anchor else '') + f'>\n        <div class="fm-schema fm-plate-fig">\n          {wide}\n          {tall}\n'
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

def aircraft_name(ty):
    """Le nom sous lequel la suite montre un type d'appareil (data/aircraft_names.json, la même table que toutes les listes) : une planche qui montre un type le montre sous son nom, jamais sous son nom de .miz."""
    with open(os.path.join(HERE, 'data', 'aircraft_names.json'), encoding='utf-8') as fh:
        return json.load(fh)['names'][ty]


def _hq_cards(P, x, w, y, gap):
    """Les trois groupes d'exemple : (SVG, [(y, h)])."""
    o, cards = [], []
    for name, typ, coal, units in (('Caesar 1', 'Mi-24P', 'Red', ['Caesar 1-1', 'Caesar 1-2']),
                                   ('Anton 2', 'Mi-8MT', 'Red', ['Anton 2-1', 'Anton 2-2']),
                                   ('Viper 1', 'F-16C_50', 'Blue', ['Viper 1-1', 'Viper 1-2'])):
        s, h = P.group_card(x, y, w, name, aircraft_name(typ), coal, units, [D('2 '), L('hq', 'snap.units')])
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
         ['le fichier, le théâtre, la date, l’heure de départ, la météo et son METAR, l’empreinte du .miz. L’icône à droite d’un en-tête, « ', L('hq', 'ui.foldall'), ' » ou « ', L('hq', 'ui.unfoldall'), ' », replie toutes les sections ou les déplie toutes.'],
         ['the file, theatre, date, start time, the weather and its METAR, the .miz fingerprint. The icon at the right of a header, “', L('hq', 'ui.foldall'), '” or “', L('hq', 'ui.unfoldall'), '”, folds all the sections or unfolds them all.']),
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


def _head(P, x, y, w, parts, fold=True, chevron=True):
    """L'en-tête d'un bloc : chevron, titre, icône de repli ; y est le haut du bloc. Au téléphone, ni chevron ni icône : le titre seul."""
    o = [chev(x + 8, y + 10), P.text(x + 20, y + 15, 8.5, *parts, anchor='start')] if chevron else [P.text(x + 8, y + 15, 8.5, *parts, anchor='start')]
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
    """Ligne titre d'un groupe : repli, nom, pastilles (type, unités), l'icône « Tout replier » (dès un groupe), retrait."""
    o = [chev(gx + 8, gy + 8), P.text(gx + 20, gy + 13, 8.5, D('CAESAR'), anchor='start')]
    px = gx + 20 + 6.2 * 6
    s, w1 = P.pill(px, gy + 4, [D('Mi-24P')])
    o.append(s)
    s, w2 = P.pill(px + w1 + 4, gy + 4, [L('fc', 'fl.units.many', args=('2',))])
    o.append(s)
    o.append(fold_icon(gx + gw - 32, gy + 5))
    o.append(P.text(gx + gw - 12, gy + 13, 8.5, D('✕'), op=.7))
    return o


def _fc_route_line(P, x, y):
    return P.text(x, y, 8, L('fc', 'route.line', args=(D('STEPPE WIND M3'), L('fc', 'route.pts.many', args=('6',)), [D('153,7 ', '153.7 '), L('fc', 'u.km')])), anchor='start', op=.8)


def _fc_departure(P, x, y, w):
    """Les deux champs de départ d'un groupe (lot vol-parking) : la base, puis le départ sur la place ; chacun sur sa ligne. Renvoie (SVG, y de la fin)."""
    o = [P.lfield(x, y, w, [L('fc', 'fp.base')], [L('fc', 'fp.base.opt', args=('Akrotiri', D('0,0', '0.0')))]),
         P.lfield(x, y + 29, w, [L('fc', 'fp.start')], [L('fc', 'fp.start.parking')])]
    return o, y + 29 + 26


def _fc_stand(P, x, y, w):
    """La place d'une unité : la liste (l'identifiant, le genre, la longueur) et le bouton Plan."""
    return (P.lfield(x, y, w - 48, [L('fc', 'fp.place')], [L('fc', 'fp.place.opt', args=('H1', L('fc', 'fp.kind.heli'), '30'))])
            + P.btn(x + w - 42, y + 11, 42, 15, [L('fc', 'fp.plan')], size=8))


def _fc_unit_head(P, ux, uy, uw, n):
    return [chev(ux + 7, uy + 7), P.text(ux + 19, uy + 12, 8.5, L('fc', 'u.title', args=(n,)), anchor='start'), fold_icon(ux + uw - 30, uy + 4), P.text(ux + uw - 10, uy + 12, 8.5, D('✕'), op=.7)]


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
    for k, (n, arme, kg) in enumerate((('1', '2 x 9M114 Shturm', '104'), ('2', 'B-8V20A - 20 x S-8KOM', '348'))):
        yy = sy + k * 18
        o.append(P.text(x + 8, yy + 11, 8, D(n), anchor='start', op=.8))
        o.append(P.field(x + 18, yy, fw, 15, [D(arme)], size=8))
        o.append(P.text(x + w - 8, yy + 11, 8, D(kg + ' '), L('fc', 'u.kg'), anchor='end', op=.75))
    sym = y + 138 + dy
    o.append(P.tick(x + 8, sym, True))
    o.append(P.text(x + 20, sym + 7, 8, L('fc', 'cmp.sym'), anchor='start'))
    # la masse des emports, la masse au décollage, puis la ligne de détail (l'écran la replie sur la largeur du bloc)
    ml = sym + 24
    o.append(P.text(x + 8, ml, 8, L('fc', 'cmp.mass'), D(' 1 599,6 ', ' 1,599.6 '), L('fc', 'u.kg'), anchor='start', op=.8))
    o.append(P.text(x + 8, ml + 11, 8, L('fc', 'cmp.takeoff', args={'y': [D('12 399,1 ', '12,399.1 '), L('fc', 'u.kg')], 'max': D('11 500', '11,500'), 'u': L('fc', 'u.kg')}), anchor='start', op=.8))
    o.append(P.text(x + 8, ml + 22, 7, L('fc', 'cmp.d.empty'), D(' 8 891', ' 8,891'), L('fc', 'cmp.d.eq'), D(' + '), L('fc', 'cmp.d.fuel'), D(' 1 701', ' 1,701'), anchor='start', op=.6))
    o.append(P.text(x + 8, ml + 31, 7, D('+ '), L('fc', 'cmp.d.stores'), D(' 1 599,6', ' 1,599.6'), D(' + '), L('fc', 'cmp.d.rounds'), D(' 207,5', ' 207.5'), anchor='start', op=.6))
    o.append(P.text(x + 8, ml + 40, 7, L('fc', 'cmp.d.tail'), anchor='start', op=.6))
    # carburant, leurres, paillettes sur une rangée ; le canon, son libellé dit la masse des obus au plein, sur la sienne
    fy = ml + 50
    fw3 = (w - 16 - 12) / 3
    for k, (lab, val) in enumerate(((L('fc', 'lo.fuel', args={'u': 'kg'}), '1701'), (L('fc', 'lo.flare'), '192'), (L('fc', 'lo.chaff'), '0'))):
        o.append(P.lfield(x + 8 + k * (fw3 + 6), fy, fw3, [lab], [D(val)], size=8))
    gy2 = fy + 29
    o.append(P.lfield(x + 8, gy2, w - 16, [L('fc', 'lo.gunfull', args={'0': D('207,5', '207.5'), 'u': L('fc', 'u.kg')})], [D('100')], size=8))
    last = (x + w - 8, gy2 + 18)
    # l'équipement : le titre, puis la case de l'option du Mi-24P
    ey = gy2 + 36
    o.append(P.text(x + 8, ey + 7, 8, L('fc', 'eq.title'), anchor='start', op=.75))
    o.append(P.tick(x + 8, ey + 14, True))
    o.append(P.text(x + 20, ey + 21, 8, D('Écran IR des tuyères · 160 ', 'IR exhaust screen · 160 '), L('fc', 'u.kg'), anchor='start', op=.85))
    eqa = (x + w - 8, ey + 4)
    # Partir de, Garder dans mes presets…
    py = ey + 36
    sel = 96 if not narrow else 84
    o.append(P.lfield(x + 8, py, sel, [L('fc', 'cmp.from')], [L('fc', 'cmp.custom')], size=8))
    gw_ = 128 if not narrow else 118
    o.append(P.btn(x + 8 + sel + 6, py + 11, gw_, 15, [L('fc', 'cmp.save')], size=8))
    h = py + 34 - y
    o[0] = sv_box(x, y, w, h)
    anc = {'head': y + 12, 'sym': (x + 20 + 4.6 * 10 + 4, sym + 4), 'fuel': last, 'eq': eqa, 'save': (x + 8 + sel + 6 + gw_, py + 18)}
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
    dep, dep_end = _fc_departure(P, gx + 8, gy + 68, gw - 16)
    ux, uw, uy = gx + 6, gw - 12, dep_end + 8
    fy, fy2 = uy + 18, uy + 47
    fy3 = fy2 + 29
    ry = fy3 + 48
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
    o += dep
    o.append(f'<rect x="{_n(ux)}" y="{_n(uy)}" width="{_n(uw)}" height="{_n(UH)}" rx="2" fill="none" stroke="currentColor" stroke-width="1" opacity=".55"/>')
    o += _fc_unit_head(P, ux, uy, uw, '1')
    o.append(P.lfield(ux + 8, fy, 62, [L('fc', 'u.type')], [D('Mi-24P')]))
    o.append(P.lfield(ux + 74, fy, 62, [L('fc', 'u.name')], [D('CAESAR-1')]))
    o.append(P.lfield(ux + 140, fy, 62, [L('fc', 'u.callsign')], [D('CAESAR 1-1')]))
    o.append(P.lfield(ux + 8, fy2, 62, [L('fc', 'u.onboard')], [D('41')]))
    o.append(P.lfield(ux + 74, fy2, 128, [L('fc', 'u.livery')], [D('262nd_SHQ_USSR')]))
    o.append(_fc_stand(P, ux + 8, fy3, 194))
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
    o.append(P.text(R0 + 8, CT + 52, 8, L('fc', 'route.from.rp'), D(' · '), L('fc', 'route.pts.many', args=('6',)), D(' · 153,7 ', ' · 153.7 '), L('fc', 'u.km'), anchor='start', op=.75))
    o.append(P.btn(R1 - 8 - 44, CT + 29, 44, 15, [L('fc', 'route.remove')], size=8))
    o.append(P.btn(R1 - 8 - 44 - 4 - 88, CT + 29, 88, 15, [L('fc', 'route.change')], size=8))
    o.append(P.text(R0 + 8, CT + 71, 8, L('fc', 'route.col.leg'), anchor='start', op=.6))
    o.append(P.text(R0 + 160, CT + 71, 8, L('fc', 'route.col.hdg'), anchor='end', op=.6))
    o.append(P.text(R1 - 8, CT + 71, 8, L('fc', 'route.col.dist'), anchor='end', op=.6))
    o.append(P.text(R0 + 8, CT + 84, 8, D('1   AKROTIRI → WP1'), anchor='start', op=.8))
    o.append(P.text(R0 + 160, CT + 84, 8, D('282°'), anchor='end', op=.8))
    o.append(P.text(R1 - 8, CT + 84, 8, D('30,1 ', '30.1 '), L('fc', 'u.km'), anchor='end', op=.8))
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
    o.append(P.bubble(5, 80, gy + 68 + 18, gx + 8, gy + 68 + 18))
    o.append(P.bubble(6, 80, uy + 8, ux, uy + 8))
    o.append(P.bubble(7, ux + uw + 5, fy2 + 18, ux + 202, fy2 + 18))      # à droite de la livrée : dessous, la place
    o.append(P.bubble(8, 80, fy3 + 18, ux + 8, fy3 + 18))
    o.append(P.bubble(9, 80, ry - 3, ux, ry - 3))
    o.append(P.bubble(10, 80, ry2 + 7, ux + 8, ry2 + 7))
    o.append(P.bubble(11, 80, addg + 8, gx, addg + 8))
    o.append(P.bubble(12, 640, CT + 12, R1, CT + 12))
    o.append(P.bubble(13, 640, anc['head'], R1, anc['head']))
    o.append(P.bubble(14, 640, anc['sym'][1], anc['sym'][0], anc['sym'][1]))
    o.append(P.bubble(15, 640, anc['fuel'][1], anc['fuel'][0], anc['fuel'][1]))
    o.append(P.bubble(16, 640, anc['eq'][1], anc['eq'][0], anc['eq'][1]))
    o.append(P.bubble(17, 640, anc['save'][1], anc['save'][0], anc['save'][1]))
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
    dep, dep_end = _fc_departure(P, gx + 8, gy + 68, gw - 16)
    ux, uw, uy = gx + 6, gw - 12, dep_end + 8
    fy, fy2, fy3 = uy + 18, uy + 47, uy + 76
    fy4 = fy3 + 29
    ry = fy4 + 26 + 14
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
    o += dep
    o.append(f'<rect x="{_n(ux)}" y="{_n(uy)}" width="{_n(uw)}" height="{_n(UH)}" rx="2" fill="none" stroke="currentColor" stroke-width="1" opacity=".55"/>')
    o += _fc_unit_head(P, ux, uy, uw, '1')
    o.append(P.lfield(ux + 8, fy, 92, [L('fc', 'u.type')], [D('Mi-24P')]))
    o.append(P.lfield(ux + 108, fy, 92, [L('fc', 'u.name')], [D('CAESAR-1')]))
    o.append(P.lfield(ux + 8, fy2, 92, [L('fc', 'u.callsign')], [D('CAESAR 1-1')]))
    o.append(P.lfield(ux + 108, fy2, 92, [L('fc', 'u.onboard')], [D('41')]))
    o.append(P.lfield(ux + 8, fy3, 192, [L('fc', 'u.livery')], [D('262nd_SHQ_USSR')]))
    o.append(_fc_stand(P, ux + 8, fy4, 192))
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
    o.append(P.text(X0 + 8, RT + 49, 8, L('fc', 'route.from.rp'), D(' · '), L('fc', 'route.pts.many', args=('6',)), D(' · 153,7 ', ' · 153.7 '), L('fc', 'u.km'), anchor='start', op=.75))
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
    o.append(P.bubble(5, 30, gy + 68 + 18, gx + 8, gy + 68 + 18))
    o.append(P.bubble(6, 30, uy + 8, ux, uy + 8))
    o.append(P.bubble(7, 30, fy3 + 16, ux + 8, fy3 + 16))
    o.append(P.bubble(8, 30, fy4 + 18, ux + 8, fy4 + 18))
    o.append(P.bubble(9, 30, ry - 3, ux, ry - 3))
    o.append(P.bubble(11, 30, addg + 8, gx, addg + 8))
    o.append(P.bubble(12, 30, RT + 12, X0, RT + 12))
    o.append(P.bubble(13, 30, anc['head'], X0, anc['head']))
    o.append(P.bubble(14, 30, anc['sym'][1], anc['sym'][0], anc['sym'][1]))
    o.append(P.bubble(15, 30, anc['fuel'][1], X0 + 8, anc['fuel'][1]))
    o.append(P.bubble(16, 330, anc['eq'][1], anc['eq'][0], anc['eq'][1]))
    o.append(P.bubble(17, 330, anc['save'][1], anc['save'][0], anc['save'][1]))
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
         ['sa carte se replie par la flèche à gauche de son nom ; ✕ le retire de tous les outils. L’icône à droite de l’en-tête, « ', L('fc', 'fl.foldall'), ' » ou « ', L('fc', 'fl.unfoldall'), ' », replie ou déplie tous les groupes, même un seul.'],
         ['its card folds by the arrow at the left of its name; ✕ removes it from all tools. The icon at the right of the header, “', L('fc', 'fl.foldall'), '” or “', L('fc', 'fl.unfoldall'), '”, folds or unfolds all the groups, even a single one.']),
        (4, [L('fc', 'fl.name')],
         'et la coalition identifient le groupe. Deux groupes d’une même coalition ne portent pas le même nom : l’export est refusé.',
         'and the coalition identify the group. Two groups of the same coalition do not share a name: the export is refused.'),
        (5, [L('fc', 'fp.base')],
         ['la base d’où part le groupe, rangée par distance du point 1 de la route ; « Aucune » le laisse partir du point 1. « ', L('fc', 'fp.start'), ' » dit comment : sur la place, à froid ou moteurs en route, quand il y a une base ; en vol ou au sol au point 1 sinon. Le paquet porte la base, le départ et les places qui prennent l’appareil du groupe.'],
         ['the base the group starts from, listed by distance from waypoint 1 of the route; “None” lets it start at waypoint 1. “', L('fc', 'fp.start'), '” tells how: on the stand, cold or with engines running, when there is a base; in the air or on the ground at waypoint 1 otherwise. The package carries the base, the start and the stands that fit the group’s aircraft.']),
        (6, [L('fc', 'u.title', args=('1',))],
         ['son type, son nom, son indicatif, son numéro de bord et sa livrée. Changer le type d’une unité efface ses radios et son emport, avec confirmation. Dans un groupe de deux unités ou plus, l’icône à droite de l’en-tête, « ', L('fc', 'u.foldall'), ' » ou « ', L('fc', 'u.unfoldall'), ' », replie ou déplie toutes les unités du groupe.'],
         ['its type, its name, its call sign, its tail number and its livery. Changing a unit’s type clears its radios and loadout, with confirmation. In a group of two units or more, the icon at the right of the header, “', L('fc', 'u.foldall'), '” or “', L('fc', 'u.unfoldall'), '”, folds or unfolds all the units of the group.']),
        (7, [L('fc', 'u.livery')],
         'une liste, celle du type de l’unité. Ce qu’elle affiche tant que vous n’avez rien choisi est dit plus bas, dans La livrée.',
         'a list, the unit type’s. What it shows until you choose is told below, in The livery.'),
        (8, [L('fc', 'fp.place')],
         ['la place de l’unité sur la base : une liste des places qui prennent son appareil, ou « ', L('fc', 'fp.plan'), ' », le plan de l’aérodrome de DCS Airfield Charts avec les places dessus. Une place prise par une autre unité du Flight Configurator n’est plus offerte ; si elle est prise dans la mission, HQ propose une place libre.'],
         ['the unit’s stand on the base: a list of the stands that take its aircraft, or “', L('fc', 'fp.plan'), '”, the airfield map from DCS Airfield Charts with the stands on it. A stand taken by another unit of the Flight Configurator is no longer offered; if it is taken in the mission, HQ offers a free one.']),
        (9, [L('fc', 'u.radios')],
         'pour chaque poste de l’appareil, un champ par canal, numéroté comme au cockpit. La case devant un canal l’imprime sur la datacard du groupe : le Datacard Generator montre le même choix, mais le paquet de vol ne le porte pas.',
         'for each radio of the aircraft, one field per channel, numbered as in the cockpit. The box in front of a channel prints it on the group’s datacard: the Datacard Generator shows the same choice, but the flight package does not carry it.'),
        (10, [L('fc', 'rad.copy')],
         'écrit les mêmes canaux sur les unités du même type.',
         'writes the same channels on the units of the same type.'),
        (11, [L('fc', 'fl.add')],
         'ajoute un groupe, avec son nom, sa coalition et ses unités.',
         'adds a group, with its name, its coalition and its units.'),
        (12, [L('fc', 'sec.route')],
         'le bloc parle du groupe de l’unité choisie. Changer de route rouvre le choix, Retirer la vide.',
         'the block is about the chosen unit’s group. Change route reopens the choice, Remove empties it.'),
        (13, [L('fc', 'sec.cmp')],
         'l’unité choisie, que l’on touche sur sa carte, a son emport affiché ici : la vue de face de l’appareil, avec une case par station et la liste des armes permises. La masse des emports et la masse au décollage s’affichent, en orange au-delà du maximum recommandé ; dessous, une ligne dit chaque terme de la somme, calculée comme l’éditeur de DCS : l’appareil à vide avec ses options d’équipement, le carburant, les emports, les obus du canon au pourcentage choisi, et la cuve de certains avions. Les leurres et les paillettes ne pèsent rien.',
         'the chosen unit, which you tap on its card, has its loadout shown here: the aircraft’s front view, with one box per station and the list of permitted weapons. The loadout mass and the take-off mass are shown, in orange beyond the recommended maximum; below, a line gives each term of the sum, worked out like the DCS editor: the empty aircraft with its equipment options, the fuel, the stores, the gun rounds at the chosen percentage, and the tank of some aircraft. Flares and chaff weigh nothing.'),
        (14, [L('fc', 'cmp.sym')],
         'pose sur la station jumelle l’arme miroir. Une arme qui ne peut pas aller avec le reste est grisée, avec les stations qui la gênent ; le Kord du Mi-24P n’a qu’une porte.',
         'places the mirror weapon on the twin station. A weapon that cannot go with the rest is greyed out, with the stations that obstruct it; the Mi-24P’s Kord has only one door.'),
        (15, [L('fc', 'lo.fuel', args={'u': 'kg'}), D(', '), L('fc', 'lo.flare'), D(', '), L('fc', 'lo.chaff'), D(', '), L('fc', 'lo.gun')],
         'une valeur tapée hors limite est refusée. Le champ du canon n’existe que pour un appareil qui en a un ; son libellé dit la masse des obus au plein, et le pourcentage choisi la fait compter dans la masse au décollage.',
         'a typed value out of range is refused. The gun field only exists for an aircraft that has a gun; its label gives the rounds’ mass when full, and the percentage you choose makes it count in the take-off mass.'),
        (16, [L('fc', 'eq.title')],
         ['une case par option que l’éditeur de DCS donne à l’appareil (écran IR des tuyères, blindage, demi-porte cargo…), avec sa masse ; une liste pour les options à plusieurs valeurs, comme le réservoir du Bf 109. Un geste recalcule la masse au même instant. Le paquet de vol porte ces options pour chaque unité (AddPropAircraft) et HQ les écrit dans la mission ; un appareil sans option n’a pas ce bloc.'],
         ['one box per option that the DCS editor gives the aircraft (IR exhaust screen, extra armour, cargo half-door…), with its mass; a list for the options with several values, like the Bf 109’s tank. A gesture recomputes the mass at once. The flight package carries these options for each unit (AddPropAircraft) and HQ writes them to the mission; an aircraft without options does not have this block.']),
        (17, [L('fc', 'cmp.save')],
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
         ['suivent la page. L’icône à droite d’un en-tête, « ', L('dg', 'ui.foldall'), ' » ou « ', L('dg', 'ui.unfoldall'), ' », replie toutes les sections ou les déplie toutes.'],
         ['follow the page. The icon at the right of a header, “', L('dg', 'ui.foldall'), '” or “', L('dg', 'ui.unfoldall'), '”, folds all the sections or unfolds them all.']),
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
         'le nom d’un terrain se choisit dans la liste des aérodromes du théâtre, qui remplit le reste ; DEP et ARR viennent de la route. La liste des pistes marque la piste face au vent et celles à vent arrière, d’après la Météo ; une piste choisie vent arrière est signalée sous sa rangée.',
         'an airfield’s name is chosen from the theatre’s airfield list, which fills in the rest; DEP and ARR come from the route. The runway list marks the runway into the wind and those with a tailwind, from the Weather box; a runway chosen with a tailwind is flagged under its row.'),
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


# ═════════════════════════════════════════════════════════════════════════════════
# La planche du Route Planner : l'écran, une route ouverte
# ═════════════════════════════════════════════════════════════════════════════════

# La route de l'exemple, en coordonnées réduites (0..1) du cadre de la carte : n, nom, u, v
_RP_PTS = [(0, 'AKROTIRI', .86, .87), (1, 'WP1', .50, .83), (2, 'POLIS', .25, .49), (3, 'IP', .46, .39),
       (4, 'KARAVOSTASI', .80, .30), (5, 'POLIS', .25, .49)]
_RP_ROWS = [('AKROTIRI', '0', '—', 'ref.MSL'), ('WP1', '30', '220', 'ref.AGL'), ('POLIS', '30', '220', 'ref.AGL'),
        ('IP', '50', '220', 'ref.AGL'), ('KARAVOSTASI', '50', '220', 'ref.AGL'), ('POLIS', '0', '220', 'ref.AGL')]
_RP_MODES = (('tap.wp', 30), ('tap.ref', 26), ('tap.read', 26), ('tap.draw', 34), ('tap.ruler', 32))
_RP_MODE_ON = 2          # le mode actif à l'ouverture : Lire


def _rp_rect(x, y, w, h, op=.7, sw=1, dash=False):
    d = ' stroke-dasharray="3 2"' if dash else ''
    return f'<rect x="{_n(x)}" y="{_n(y)}" width="{_n(w)}" height="{_n(h)}" rx="2" fill="none" stroke="currentColor" stroke-width="{sw}" opacity="{op}"{d}/>'


def _rp_chev_closed(x, y):
    return f'<path d="M{_n(x)},{_n(y)} l5,3 l-5,3 z" fill="currentColor" opacity=".8"/>'


def _rp_active(P, x, y, w, h, parts, size=8):
    """Bouton actif (mode Point, onglet Coordonnées) : l'aplat des pastilles."""
    return (f'<rect class="sv-pill" x="{_n(x)}" y="{_n(y)}" width="{_n(w)}" height="{_n(h)}" rx="1.5"/>'
            + P.text(x + w / 2, y + h / 2 + 3, size, *parts, cls='sv-pill-t'))


def _rp_magnifier(cx, cy, r=3.2):
    return (f'<circle cx="{_n(cx - 1)}" cy="{_n(cy - 1)}" r="{_n(r)}" fill="none" stroke="currentColor" stroke-width="1.1"/>'
            f'<line x1="{_n(cx + 1.4)}" y1="{_n(cy + 1.4)}" x2="{_n(cx + 4)}" y2="{_n(cy + 4)}" stroke="currentColor" stroke-width="1.3"/>')


def _rp_map(P, x0, y0, x1, y1, scale=1.0, narrow=False):
    """La carte : cadre, grille, zoom, loupe, modes de toucher, référence, aérodrome, route, boîte de branche. Renvoie (SVG, ancres)."""
    o, anc = [], {}
    w, h = x1 - x0, y1 - y0
    o.append(_rp_rect(x0, y0, w, h, op=.8, sw=1.2))
    step = 40 * scale
    gx = x0 + step / 2
    while gx < x1:
        o.append(f'<line x1="{_n(gx)}" y1="{_n(y0)}" x2="{_n(gx)}" y2="{_n(y1)}" stroke="currentColor" stroke-width=".5" opacity=".18"/>')
        gx += step
    gy = y0 + step / 2
    while gy < y1:
        o.append(f'<line x1="{_n(x0)}" y1="{_n(gy)}" x2="{_n(x1)}" y2="{_n(gy)}" stroke="currentColor" stroke-width=".5" opacity=".18"/>')
        gy += step
    # zoom et loupe, en haut à gauche
    o.append(P.btn(x0 + 6, y0 + 6, 16, 30))
    o.append(f'<line x1="{_n(x0 + 8)}" y1="{_n(y0 + 21)}" x2="{_n(x0 + 20)}" y2="{_n(y0 + 21)}" stroke="currentColor" stroke-width=".6" opacity=".5"/>')
    o.append(P.text(x0 + 14, y0 + 17, 9, D('+')))
    o.append(P.text(x0 + 14, y0 + 32, 9, D('−')))
    o.append(P.btn(x0 + 6, y0 + 42, 16, 16))
    o.append(_rp_magnifier(x0 + 14, y0 + 50))
    anc['loupe'] = (x0 + 22, y0 + 50)
    # les cinq modes de toucher, en haut à droite
    widths = []
    for key, _w in _RP_MODES:              # la largeur suit le plus long des deux libellés, FR ou EN
        fr, en, _k = P.resolve([L('rp', key, up=True)])
        widths.append(max(26, 9 + 5.3 * max(len(fr), len(en))))
    mw = sum(widths)
    mx = x1 - 6 - mw
    o.append(f'<rect class="sv-box" x="{_n(mx - 2)}" y="{_n(y0 + 4)}" width="{_n(mw + 4)}" height="20" rx="2" stroke="currentColor" stroke-width="1"/>')
    for i, ((key, _w), mwi) in enumerate(zip(_RP_MODES, widths)):
        if i == _RP_MODE_ON:
            o.append(_rp_active(P, mx, y0 + 6, mwi - 1, 16, [L('rp', key, up=True)]))
        else:
            o.append(P.btn(mx, y0 + 6, mwi - 1, 16, [L('rp', key, up=True)], op=.5))
        mx += mwi
    anc['modes'] = (x1 - 6, y0 + 14)

    def at(u, v):
        return x0 + u * w, y0 + v * h
    # un point de référence et un aérodrome
    rx, ry = at(.30, .20)
    o.append(f'<path d="M{_n(rx)},{_n(ry - 7)} l7,7 l-7,7 l-7,-7 z" class="sv-box" stroke="currentColor" stroke-width="1.2"/>')
    o.append(P.text(rx, ry + 3, 8, D('A'), extra=' font-weight="700"'))
    if not narrow:
        o.append(P.text(rx + 11, ry + 3, 8, D('ÎLE PETRA', 'PETRA ISLAND'), anchor='start', op=.85))
    ax, ay = at(.16, .74)
    o.append(f'<circle cx="{_n(ax)}" cy="{_n(ay)}" r="3.6" fill="none" stroke="currentColor" stroke-width="1"/><circle cx="{_n(ax)}" cy="{_n(ay)}" r="1.1" fill="currentColor"/>')
    o.append(P.text(ax + 7, ay + 3, 8, D('Paphos'), anchor='start', op=.7))
    # la route
    pts = [(n, name) + at(u, v) for n, name, u, v in _RP_PTS]
    path = ' '.join(('M' if i == 0 else 'L') + f'{_n(p[2])},{_n(p[3])}' for i, p in enumerate(pts))
    o.append(f'<path d="{path}" fill="none" stroke="currentColor" stroke-width="2.2" opacity=".75"/>')
    # traits des minutes sur la branche 1 → 2
    (_a, _b, x1p, y1p), (_c, _d, x2p, y2p) = pts[1], pts[2]
    dx, dy = x2p - x1p, y2p - y1p
    ln = (dx * dx + dy * dy) ** .5
    nx, ny = -dy / ln * 4, dx / ln * 4
    k = 1
    while k * 12 * scale < ln - 10:
        t = k * 12 * scale / ln
        cx, cy = x1p + dx * t, y1p + dy * t
        o.append(f'<line x1="{_n(cx - nx)}" y1="{_n(cy - ny)}" x2="{_n(cx + nx)}" y2="{_n(cy + ny)}" stroke="currentColor" stroke-width="1" opacity=".7"/>')
        k += 1
    # le + d'insertion, sur la branche 0 → 1
    ix, iy = (pts[0][2] + pts[1][2]) / 2, (pts[0][3] + pts[1][3]) / 2
    o.append(f'<circle class="sv-box" cx="{_n(ix)}" cy="{_n(iy)}" r="4.2" stroke="currentColor" stroke-width="1"/>')
    o.append(P.text(ix, iy + 2.8, 8, D('+')))
    for n, name, px, py in pts:
        if n == 2:
            continue                       # sous le 5, comme à l'écran
        o.append(f'<circle class="sv-box" cx="{_n(px)}" cy="{_n(py)}" r="7.5" stroke="currentColor" stroke-width="1.6"/>')
        o.append(P.text(px, py + 3, 8, D(str(n)), extra=' font-weight="700"'))
        if narrow:
            continue                       # au téléphone, les numéros seuls
        if n in (0, 4):                    # sous le numéro (le nom de 4 sortait du cadre à droite, à côté)
            o.append(P.text(px, py + 19, 8, D(name), op=.9))
        elif n == 1:
            o.append(P.text(px + 11, py + 3, 8, D(name), anchor='start', op=.9))
    anc['route'] = (pts[0][2] + 7.5, pts[0][3])
    # la boîte de la branche 3 → 4
    mx_, my_ = (pts[3][2] + pts[4][2]) / 2, (pts[3][3] + pts[4][3]) / 2
    bw, bh = (54, 46) if not narrow else (50, 44)
    bx_, by_ = (mx_ - 4, my_ - bh - 26) if not narrow else (mx_ + 6, my_ + 16)
    o.append(f'<line x1="{_n(bx_ + 12)}" y1="{_n(by_ + (0 if narrow else bh))}" x2="{_n(mx_)}" y2="{_n(my_)}" stroke="currentColor" stroke-width=".8" opacity=".6"/>')
    o.append(sv_box(bx_, by_, bw, bh))
    for i, parts in enumerate(([D('083'), L('rp', 'lb.true')], [D('19,9 ', '19.9 '), L('rp', 'u.km')], [D('220 '), L('rp', 'u.kmh')], [L('rp', 'lb.ete'), D(' 05:25')])):
        o.append(P.text(bx_ + bw / 2, by_ + 11 + i * 10, 8, *parts))
    anc['box'] = (bx_ + bw, by_ + 14)
    return o, anc


def _rp_section_closed(P, x, y, w, n, key):
    return [_rp_rect(x, y, w, 22, op=.7), _rp_chev_closed(x + 9, y + 8), P.text(x + 20, y + 14.5, 8.5, D('%02d ░ ' % n), L('rp', key), anchor='start'),
            fold_icon(x + w - 18, y + 6)]


def _rp_route_head(P, x, y, w):
    o = [chev(x + 8, y + 9), P.text(x + 20, y + 14.5, 8.5, D('01 ░ '), L('rp', 'sec.route'), anchor='start'),
         P.text(x + w - 28, y + 14.5, 8, L('rp', 'sec.points', args={'n': '6'}), anchor='end', op=.7), fold_icon(x + w - 18, y + 6),
         f'<line x1="{_n(x)}" y1="{_n(y + 22)}" x2="{_n(x + w)}" y2="{_n(y + 22)}" stroke="currentColor" stroke-width=".6" opacity=".4"/>']
    return o


def _rp_route_select(P, a, y, w):
    """La ligne qui choisit la route : liste, +, …"""
    lw = w - 64
    return [P.field(a, y, lw, 16, [D('1 · STEPPE WIND M3')]), f'<path d="M{_n(a + lw - 11)},{_n(y + 6.5)} l6,0 l-3,4 z" fill="currentColor" opacity=".7"/>',
            P.btn(a + lw + 4, y, 26, 16, [D('+')], size=9), P.btn(a + lw + 34, y, 26, 16, [D('…')], size=9)]


def _rp_wide(P):
    o = ['']
    o.append(P.title_wide('L’ÉCRAN DU ROUTE PLANNER', 'THE ROUTE PLANNER SCREEN', 24, 32))
    o.append('<g transform="translate(0,22)">')
    X0, X1 = 110, 610
    # ── la barre du haut ────────────────────────────────────────────────────────
    o += [sv_box(X0, 44, X1 - X0, 28), P.text(X0 + 8, 62, 8, L('rp', 'tb.subtitle'), anchor='start', op=.7, ls=.6)]
    bx, x = {}, X0 + 74
    for key, w, parts in (('open', 50, [L('rp', 'tb.open', add='▾')]), ('save', 60, [L('rp', 'tb.save')]),
                          ('export', 52, [L('rp', 'tb.export', add='▾')]), ('display', 58, [L('rp', 'tb.display', add='▾')])):
        o.append(P.btn(x, 49, w, 18, parts))
        bx[key] = (x, w)
        x += w + 4
    o.append(P.text(x + 4, 61, 8, L('rp', 'tb.theatre', up=True), anchor='start', op=.6))
    tx = x + 46
    o.append(P.field(tx, 49, 52, 18, [L('rp', 'th.Syria', add='▾')]))
    bx['theatre'] = (tx, 52)
    o.append(P.btn(tx + 58, 49, 46, 18, [L('rp', 'tb.clear')]))
    bx['clear'] = (tx + 58, 46)
    for n, key in ((1, 'open'), (2, 'export'), (3, 'display'), (4, 'theatre'), (5, 'clear')):
        cx = bx[key][0] + bx[key][1] / 2
        o.append(P.bubble(n, cx, 30, cx, 49))
    # ── le panneau ──────────────────────────────────────────────────────────────
    CT = 82
    PX0, PX1 = X0, 330
    a, aw = PX0 + 8, PX1 - PX0 - 16
    o += _rp_route_head(P, PX0, CT, PX1 - PX0)
    y1 = CT + 30
    o += _rp_route_select(P, a, y1, aw)
    o.append(P.text(a, y1 + 28, 8, L('rp', 'rs.count', args={'a': '1', 'n': '1'}), anchor='start', op=.65))
    y2 = y1 + 36
    o.append(P.lfield(a, y2, aw, [L('rp', 'f.name')], [D('STEPPE WIND M3')]))
    y3 = y2 + 38
    o.append(P.text(a, y3, 8, L('rp', 'rs.groups', up=True), anchor='start', op=.75))
    o.append(P.text(a + 48, y3, 8.5, D('CAESAR'), anchor='start'))
    y4 = y3 + 6
    o.append(P.btn(a, y4, aw, 16, [L('rp', 'rs.assign')]))
    y5 = y4 + 30
    cols = ((0, [L('rp', 'th.no')]), (20, [L('rp', 'th.name')]), (84, [L('rp', 'th.alt', args={'u': 'm'})]),
            (122, [L('rp', 'th.spd.kmh')]), (168, [L('rp', 'th.ref')]))
    for dx, parts in cols:
        o.append(P.text(a + dx, y5, 8, *parts, anchor='start', op=.7))
    y6 = y5 + 6
    for i, (name, alt, spd, ref) in enumerate(_RP_ROWS):
        yy = y6 + i * 15
        o.append(P.field(a, yy, 15, 12, [D(str(i))]))
        o.append(P.field(a + 20, yy, 60, 12, [D(name)]))
        o.append(P.field(a + 84, yy, 34, 12, [D(alt)]))
        if spd == '—':
            o.append(_rp_rect(a + 122, yy, 42, 12, op=.45, dash=True))
            o.append(P.text(a + 143, yy + 9, 8, D('—'), op=.6))
        else:
            o.append(P.field(a + 122, yy, 42, 12, [D(spd)]))
        o.append(P.field(a + 168, yy, 26, 12, [L('rp', ref)]))
        o.append(P.text(a + aw - 2, yy + 9, 8, D('✕'), op=.7))
    y7 = y6 + len(_RP_ROWS) * 15 + 14
    o.append(P.text(a, y7, 8, L('rp', 'add.title', up=True), anchor='start', op=.75))
    y8 = y7 + 6
    hw = (aw - 4) / 2
    o.append(_rp_active(P, a, y8, hw, 15, [L('rp', 'add.coord')]))
    o.append(P.btn(a + hw + 4, y8, hw, 15, [L('rp', 'add.hd')]))
    y9 = y8 + 20
    o.append(P.field(a, y9, aw, 15, [L('rp', 'add.coord.ph')]))
    y10 = y9 + 20
    o.append(P.btn(a, y10, hw, 15, [L('rp', 'add.wp')]))
    o.append(P.btn(a + hw + 4, y10, hw, 15, [L('rp', 'add.ref')]))
    rEnd = y10 + 24
    o.append(f'<rect x="{PX0}" y="{CT}" width="{PX1 - PX0}" height="{_n(rEnd - CT)}" rx="2" fill="none" stroke="currentColor" stroke-width="1.2" opacity=".8"/>')
    sy = rEnd + 6
    for k, (n, key) in enumerate(((2, 'sec.refs'), (3, 'sec.layers'), (4, 'sec.nav'))):
        o += _rp_section_closed(P, PX0, sy + k * 27, PX1 - PX0, n, key)
    PE = sy + 3 * 27 - 5
    # ── la carte ────────────────────────────────────────────────────────────────
    MX0, MX1 = PX1 + 6, X1
    mp, anc = _rp_map(P, MX0, CT, MX1, PE)
    o += mp
    # ── les bulles du panneau et de la carte ────────────────────────────────────
    o.append(P.bubble(6, 92, y1 + 8, a, y1 + 8))
    o.append(P.bubble(7, 92, y4 + 8, a, y4 + 8))
    o.append(P.bubble(8, 92, y6 + 6, a, y6 + 6))
    o.append(P.bubble(9, 92, y8 + 7.5, a, y8 + 7.5))
    o.append(P.bubble(10, 92, sy + 11, PX0, sy + 11))
    o.append(P.bubble(11, anc['loupe'][0] + 22, anc['loupe'][1], anc['loupe'][0], anc['loupe'][1]))
    o.append(P.bubble(12, 632, anc['modes'][1], anc['modes'][0], anc['modes'][1]))
    o.append(P.bubble(13, 632, anc['route'][1], anc['route'][0], anc['route'][1]))
    o.append(P.bubble(14, 632, anc['box'][1], anc['box'][0], anc['box'][1]))
    o.append('</g>')
    o.append('</svg>')
    o[0] = P.svg_open('pl-wide', 720, PE + 22 + 12, 'L’écran du Route Planner, une route ouverte', 'The Route Planner screen, with a route open', 'rpw')
    return '\n          '.join(o)


# Les pictogrammes de la barre du téléphone (au trait)
def _rp_ico_folder(cx, cy):
    return f'<path d="M{_n(cx - 6)},{_n(cy - 4)} h4 l1.5,1.5 h6.5 v7 h-12 z" fill="none" stroke="currentColor" stroke-width="1.1"/>'


def _rp_ico_disk(cx, cy):
    return (f'<rect x="{_n(cx - 5)}" y="{_n(cy - 5)}" width="10" height="10" rx="1" fill="none" stroke="currentColor" stroke-width="1.1"/>'
            f'<rect x="{_n(cx - 2.5)}" y="{_n(cy - 5)}" width="5" height="3" fill="none" stroke="currentColor" stroke-width=".9"/>')


def _rp_ico_export(cx, cy):
    return (f'<path d="M{_n(cx)},{_n(cy + 2)} v-8 m-3,3 l3,-3 l3,3 M{_n(cx - 6)},{_n(cy)} v5 h12 v-5" fill="none" stroke="currentColor" stroke-width="1.1"/>')


def _rp_ico_eye(cx, cy):
    return (f'<path d="M{_n(cx - 7)},{_n(cy)} q7,-7 14,0 q-7,7 -14,0 z" fill="none" stroke="currentColor" stroke-width="1.1"/>'
            f'<circle cx="{_n(cx)}" cy="{_n(cy)}" r="2" fill="currentColor"/>')


def _rp_ico_chev(x, y):
    return f'<path d="M{_n(x)},{_n(y)} l3,3 l3,-3" fill="none" stroke="currentColor" stroke-width="1"/>'


def _rp_tall(P):
    W = 360
    o = ['']
    o.append(P.title_tall('L’ÉCRAN DU ROUTE PLANNER', 'THE ROUTE PLANNER SCREEN', 'au téléphone', 'on a phone'))
    o.append('<g transform="translate(0,12)">')
    X0, X1 = 62, 298
    w = X1 - X0
    # ── la barre : pictogrammes seuls, « ⋯ » au bout droit (le théâtre, Effacer et la langue sont dans son menu) ──
    o.append(sv_box(X0, 62, w, 30))
    o.append(P.btn(X0 + 4, 66, 20, 22, [D('◄')]))
    o.append(P.text(X0 + 30, 81, 8.5, L('rp', 'app.short'), anchor='start', extra=' font-weight="700"'))
    bx = {}
    x = X0 + 54
    for key, bw, ico, chv in (('open', 28, _rp_ico_folder, True), ('save', 22, _rp_ico_disk, False), ('export', 28, _rp_ico_export, True), ('display', 22, _rp_ico_eye, False)):
        o.append(P.btn(x, 66, bw, 22))
        o.append(ico(x + (9 if chv else bw / 2), 77))
        if chv:
            o.append(_rp_ico_chev(x + 18, 76))
        bx[key] = (x, bw)
        x += bw + 4
    o.append(P.btn(X1 - 4 - 22, 66, 22, 22, [D('⋯')]))
    bx['more'] = (X1 - 4 - 22, 22)
    for n, key in ((1, 'open'), (2, 'export'), (3, 'display'), (4, 'more')):
        cx = bx[key][0] + bx[key][1] / 2
        o.append(P.bubble(n, cx, 48, cx, 66))
    # ── la carte, fixe en haut ───────────────────────────────────────────────────
    MT, MB = 98, 318
    mp, anc = _rp_map(P, X0, MT, X1, MB, scale=.8, narrow=True)
    o += mp
    # la poignée entre la carte et le panneau
    o.append(f'<rect x="{X0}" y="{MB + 2}" width="{w}" height="12" fill="none" stroke="currentColor" stroke-width=".6" opacity=".35"/>')
    o.append(f'<path d="M{_n(X0 + w / 2 - 14)},{MB + 6} h28 M{_n(X0 + w / 2 - 14)},{MB + 10} h28" stroke="currentColor" stroke-width="1.1" opacity=".7"/>')
    # ── le panneau, qui seul défile ─────────────────────────────────────────────
    PT = MB + 20
    a, aw = X0 + 8, w - 16
    o += _rp_route_head(P, X0, PT, w)
    y1 = PT + 30
    o += _rp_route_select(P, a, y1, aw)
    o.append(P.text(a, y1 + 28, 8, L('rp', 'rs.count', args={'a': '1', 'n': '1'}), anchor='start', op=.65))
    y2 = y1 + 36
    o.append(P.lfield(a, y2, aw, [L('rp', 'f.name')], [D('STEPPE WIND M3')]))
    y3 = y2 + 38
    o.append(P.text(a, y3, 8, L('rp', 'rs.groups', up=True), anchor='start', op=.75))
    o.append(P.text(a + 48, y3, 8.5, D('CAESAR'), anchor='start'))
    y4 = y3 + 6
    o.append(P.btn(a, y4, aw, 16, [L('rp', 'rs.assign')]))
    PE = y4 + 30
    # le panneau continue : bords ouverts en pointillé
    o.append(f'<path d="M{X0},{_n(PE)} V{PT} H{X1} V{_n(PE)}" fill="none" stroke="currentColor" stroke-width="1.2" opacity=".8"/>')
    o.append(f'<line x1="{X0}" y1="{_n(PE)}" x2="{X1}" y2="{_n(PE)}" stroke="currentColor" stroke-width="1" stroke-dasharray="3 3" opacity=".5"/>')
    # ── les bulles ──────────────────────────────────────────────────────────────
    o.append(P.bubble(11, 30, anc['loupe'][1], X0, anc['loupe'][1]))
    o.append(P.bubble(12, 330, anc['modes'][1], anc['modes'][0], anc['modes'][1]))
    o.append(P.bubble(14, 330, anc['box'][1], anc['box'][0], anc['box'][1]))
    o.append(P.bubble(13, 330, anc['route'][1], anc['route'][0], anc['route'][1]))
    o.append(P.bubble(6, 30, y1 + 8, a, y1 + 8))
    o.append(P.bubble(7, 30, y4 + 8, a, y4 + 8))
    o.append('</g>')
    o.append('</svg>')
    o[0] = P.svg_open('pl-tall', W, PE + 12 + 12, 'L’écran du Route Planner au téléphone, une route ouverte', 'The Route Planner screen on a phone, with a route open', 'rpt')
    return '\n          '.join(o)


def _rp_legend_rows():
    return [
        (1, [L('rp', 'tb.open', add='▾')],
         'Ouvrir un travail… lit un fichier de travail de la suite ; Ouvrir une route ou des calques… reconnaît une route JSON, un fichier du Route Tool de DCS ou un fichier CombatFlite ; Importer des routes… ouvre la fenêtre d’import commune.',
         'Open a work file… reads a suite work file; Open a route or layers… recognises a JSON route, a DCS Route Tool file or a CombatFlite file; Import routes… opens the common import window.'),
        (2, [L('rp', 'tb.export', add='▾')],
         'Image pour le briefing… et Route Tool… : voir plus bas. La ligne Route Tool est grisée sur un théâtre sans Route Tool.',
         'Image for the briefing… and Route Tool…: see below. The Route Tool line is greyed out on a theatre without a Route Tool.'),
        (3, [L('rp', 'tb.display', add='▾')],
         'règle le fond, les unités et ce que montre la carte ; un point ambre sur le bouton signale un réglage changé. La Carte DCS est grisée là où DCS n’en a pas, et la carte de navigation de Flappie n’existe que sur le Caucase.',
         'sets the base map, the units and what the map shows; an amber dot on the button flags a changed setting. The DCS map is greyed out where DCS has none, and Flappie’s navigation chart exists only on the Caucasus.'),
        (4, [L('rp', 'tb.theatre')],
         'choisit la carte de DCS (au téléphone, sous « ⋯ », avec Effacer et la langue). Une route garde son théâtre : en changer masque les routes des autres théâtres, qui reviennent quand on y retourne.',
         'chooses the DCS map (on a phone, under “⋯”, with Clear and the language). A route keeps its theatre: changing it hides the other theatres’ routes, which come back when you return.'),
        (5, [L('rp', 'tb.clear')],
         ['efface au choix : ', L('rp', 'clr.one'), ', ', L('rp', 'clr.routes'), ', ', L('rp', 'clr.refs'), ', ', L('rp', 'clr.draw'), ', ', L('rp', 'clr.sym'), ' ou ', L('rp', 'clr.layers'), '.'],
         ['clears, as you choose: ', L('rp', 'clr.one'), ', ', L('rp', 'clr.routes'), ', ', L('rp', 'clr.refs'), ', ', L('rp', 'clr.draw'), ', ', L('rp', 'clr.sym'), ' or ', L('rp', 'clr.layers'), '.']),
        (6, [L('rp', 'sec.route')],
         'en tête, une ligne choisit la route ; + en ajoute une, jusqu’à 12, et … ouvre Dupliquer et Supprimer.',
         'at the top, a row chooses the route; + adds one, up to 12, and … opens Duplicate and Delete.'),
        (7, [L('rp', 'rs.assign')],
         'choisit les groupes qui suivent cette route, ou en crée un ; un groupe ne suit qu’une route, et le Flight Configurator voit le même choix.',
         'chooses the groups that follow this route, or creates one; a group follows only one route, and the Flight Configurator sees the same choice.'),
        (8, [M('Les points', 'The waypoints')],
         'un par ligne : nom, altitude, vitesse et référence de l’altitude, SOL ou MER ; ✕ retire le point.',
         'one per row: name, altitude, speed and altitude reference, AGL or MSL; ✕ removes the waypoint.'),
        (9, [L('rp', 'add.title')],
         'place un point par ses coordonnées (MGRS, DMS, DDM ou décimal) ou par cap et distance depuis le dernier point ; + Réf. en fait un point de référence.',
         'places a waypoint by its coordinates (MGRS, DMS, DDM or decimal) or by heading and distance from the last waypoint; + Ref. makes it a reference point.'),
        (10, [M('Les autres sections', 'The other sections')],
         ['Points de référence, Calques, Navigation. L’icône à droite d’un en-tête, « ', L('rp', 'ui.foldall'), ' » ou « ', L('rp', 'ui.unfoldall'), ' », replie toutes les sections ou les déplie toutes. Voir plus bas.'],
         ['Reference points, Layers, Navigation. The icon at the right of a header, “', L('rp', 'ui.foldall'), '” or “', L('rp', 'ui.unfoldall'), '”, folds all the sections or unfolds them all. See below.']),
        (11, [L('rp', 'sr.title')],
         'la loupe cherche un lieu ou un objet nommé.',
         'the magnifier looks for a named place or object.'),
        (12, [L('rp', 'tap.title')],
         'Le Route Planner s’ouvre en Lire, qui ne pose rien : choisissez Point pour poser la route. Point ajoute un point au bout de la route ; Réf. pose un point de référence ; Lire ne pose rien : un aérodrome ouvre sa fiche, un objet d’un calque montre la sienne ; Dessin ouvre les outils de dessin de vos calques ; Règle mesure cap et distance sans rien poser, et quitter le mode efface la mesure. En Point et en Réf., un aérodrome touché donne un point à son nom.',
         'The Route Planner opens in Read, which places nothing: choose Waypoint to lay the route. Waypoint adds a waypoint at the end of the route; Ref. places a reference point; Read places nothing: an airfield opens its sheet, a layer object shows its own; Draw opens the drawing tools of your layers; Ruler measures heading and distance without placing anything, and leaving the mode clears the measure. In Waypoint and Ref., a tapped airfield gives the waypoint its name.'),
        (13, [M('La route', 'The route')],
         'glissez un point pour le déplacer ; le + posé sur une branche assez longue y insère un point. Les traits des minutes coupent la route toutes les minutes.',
         'drag a waypoint to move it; the + on a long enough leg inserts a waypoint there. The minute ticks cut the route every minute.'),
        (14, [L('rp', 'f.lbx')],
         'écrivent la navigation sur la carte, une par branche : cap, distance, vitesse et ETE.',
         'write the navigation on the map, one per leg: heading, distance, speed and ETE.'),
    ]


def build_plate_rp():
    """La planche du Route Planner : le HTML (cadre, figure zoomable, légende) ; ses libellés viennent du dictionnaire du RP."""
    P = Plate('rp', ['rp'])
    wide, tall = _rp_wide(P), _rp_tall(P)
    legend = P.legend_html(_rp_legend_rows())
    P.verify(wide, tall)
    return P.figure_html(wide, tall,
                         'Fig. 1 — L’écran du Route Planner, la route de l’exemple ouverte : la barre, le panneau de la route, puis la carte et ses modes de toucher.',
                         'Fig. 1 — The Route Planner screen with the example route open: the bar, the route panel, then the map and its tap modes.', legend)


# ═════════════════════════════════════════════════════════════════════════════════
# La planche du Briefing Generator : l'éditeur Standard et l'aperçu de la page de mission
# ═════════════════════════════════════════════════════════════════════════════════

def _sec_closed(P, tool, x, y, w, key):
    """Une section repliée : cadre, chevron fermé, titre, icône de repli."""
    return [_rp_rect(x, y, w, 22, op=.7), _rp_chev_closed(x + 9, y + 8), P.text(x + 20, y + 14.5, 8.5, L(tool, key), anchor='start'), fold_icon(x + w - 18, y + 6)]


def _bg_closed(P, x, y, w, key):
    return _sec_closed(P, 'bg', x, y, w, key)


def _bg_editor(P, x, y, w):
    """L'éditeur de la variante large : « En-tête » et « Situation » ouvertes, les quatre autres repliées. Renvoie (SVG, hauteur, ancres)."""
    o, anc = [], {}
    a, aw, hw = x + 8, w - 16, (w - 16 - 6) / 2
    # 01 En-tête, ouverte
    h1 = 24 + 6 + 26 + 6 + 26 + 8
    o.append(sv_box(x, y, w, h1))
    o += _head(P, x, y, w, [L('bg', 'editor.header.summary')])
    o.append(_rule(x, x + w, y + 24))
    o.append(P.lfield(a, y + 30, hw, [L('bg', 'editor.meta.operation')], [D('STEPPE WIND')]))
    o.append(P.lfield(a + hw + 6, y + 30, hw, [L('bg', 'editor.meta.missionCode')], [D('M3')]))
    o.append(P.lfield(a, y + 62, hw, [L('bg', 'editor.meta.date')], [D('1989-03-22')]))
    o.append(P.lfield(a + hw + 6, y + 62, hw, [L('bg', 'editor.meta.time')], [D('08:00')]))
    anc['head'] = y + 12
    # 02 Situation, ouverte
    y2 = y + h1 + 6
    h2 = 24 + 12 + 2 * 22 + 22 + 8
    o.append(sv_box(x, y2, w, h2))
    o += _head(P, x, y2, w, [L('bg', 'editor.simple.situation.summary')])
    o.append(_rule(x, x + w, y2 + 24))
    o.append(P.text(a, y2 + 38, 8, L('bg', 'editor.sitac.points', up=True), anchor='start', op=.75))
    for k, txt in enumerate((('La majorité de l’île reste…', 'Most of the island remains…'), ('L’aéroport de PAPHOS a été…', 'PAPHOS airport has been…'))):
        yy = y2 + 44 + k * 22
        o.append(P.field(a, yy, aw - 22, 18, [D(*txt)]))
        o.append(P.btn(a + aw - 18, yy, 18, 18, [D('✕')]))
    o.append(P.btn(a, y2 + 44 + 2 * 22, aw, 18, [L('bg', 'editor.sitac.addPoint')]))
    anc['sit'] = y2 + 12
    # 03 à 06, repliées
    y3 = y2 + h2 + 6
    for k, key in enumerate(('editor.simple.mission.summary', 'editor.simple.coord.summary', 'editor.simple.photos.summary', 'editor.meta.summarySimple')):
        o += _bg_closed(P, x, y3 + k * 27, w, key)
    anc['others'] = y3 + 11
    return o, y3 + 4 * 27 - 5 - y, anc


def _bg_page(P, x, y, w, h):
    """L'aperçu : la page de mission au trait, le contenu en traits gris, les titres de bloc écrits."""
    o = [sv_box(x, y, w, h)]
    px, pw = x + 8, w - 16
    o.append(f'<rect x="{_n(px)}" y="{_n(y + 8)}" width="{_n(pw)}" height="{_n(h - 16)}" rx="1.5" fill="none" stroke="currentColor" stroke-width="1" opacity=".5"/>')
    ix, iw = px + 8, pw - 16
    cy = y + 16
    o.append(_bars(x + w / 2 - 50, cy, 100, 1))                                        # la ligne de référence
    o.append(P.btn(x + w / 2 - 54, cy + 5, 108, 13, [L('bg', 'classif.confidential')], op=.8))
    for cx in (ix + 12, ix + iw - 12):                                                   # les deux logos
        o.append(f'<circle cx="{_n(cx)}" cy="{_n(cy + 24)}" r="11" fill="none" stroke="currentColor" stroke-width="1.1" opacity=".6"/>')
    o.append(_bars(x + w / 2 - 44, cy + 28, 88, 1))
    o.append(_bars(x + w / 2 - 34, cy + 38, 68, 1))
    cy += 50
    o.append(f'<rect class="sv-pill" x="{_n(ix)}" y="{_n(cy)}" width="{_n(iw)}" height="14" rx="1.5"/>')
    o.append(P.text(x + w / 2, cy + 10, 8, L('bg', 'simple.hdr.mission'), D(' M3 ░ 22/03/1989 ░ 08:00Z'), cls='sv-pill-t'))
    cy += 22
    for key, n in (('simple.situation', 3), ('simple.mission', 2)):
        o.append(f'<rect x="{_n(ix)}" y="{_n(cy)}" width="{_n(iw)}" height="13" rx="1.5" fill="none" stroke="currentColor" stroke-width="1" opacity=".55"/>')
        o.append(P.text(x + w / 2, cy + 9.5, 8, L('bg', key, up=True), ls=1.2))
        o.append(_bars(ix + 6, cy + 24, iw - 12, n, gap=9))
        cy += 13 + 8 + n * 9 + 6
    o.append(f'<line x1="{_n(ix)}" y1="{_n(cy)}" x2="{_n(ix + iw)}" y2="{_n(cy)}" stroke="currentColor" stroke-width="1" opacity=".6"/>')   # le tableau des groupes
    o.append(_bars(ix + 4, cy + 10, iw - 8, 3, gap=10))
    cy += 42
    cw = (iw - 8) / 2
    for k, (key, n) in enumerate((('simple.freq', 3), ('simple.airfields', 3))):
        bx = ix + k * (cw + 8)
        o.append(f'<rect x="{_n(bx)}" y="{_n(cy)}" width="{_n(cw)}" height="13" rx="1.5" fill="none" stroke="currentColor" stroke-width="1" opacity=".55"/>')
        o.append(P.text(bx + cw / 2, cy + 9.5, 8, L('bg', key, up=True), ls=1))
        o.append(_bars(bx + 4, cy + 24, cw - 8, n, gap=9))
    cy += 13 + 8 + 3 * 9 + 6
    o.append(f'<rect x="{_n(ix)}" y="{_n(cy)}" width="{_n(iw)}" height="13" rx="1.5" fill="none" stroke="currentColor" stroke-width="1" opacity=".55"/>')
    o.append(P.text(x + w / 2, cy + 9.5, 8, L('bg', 'simple.weather', up=True), ls=1.2))
    o.append(_bars(ix + 6, cy + 24, iw - 12, 1))
    return o


def _bg_wide(P):
    o = ['']
    o.append(P.title_wide('L’ÉCRAN DU BRIEFING GENERATOR', 'THE BRIEFING GENERATOR SCREEN', 24, 32))
    o.append('<g transform="translate(0,22)">')
    X0, X1 = 110, 610
    o += [sv_box(X0, 44, X1 - X0, 28), P.text(X0 + 8, 62, 8, L('bg', 'toolbar.subtitle'), anchor='start', op=.7, ls=.6)]
    bx, x = {}, X0 + 122
    for key, w, parts in (('open', 56, [L('bg', 'toolbar.load', add='▾')]), ('save', 68, [L('bg', 'toolbar.save')]), ('export', 54, [L('bg', 'toolbar.export')]),
                          ('display', 66, [L('bg', 'toolbar.display', add='▾')]), ('clear', 48, [L('bg', 'toolbar.reset')])):
        o.append(P.btn(x, 49, w, 18, parts))
        bx[key] = (x, w)
        x += w + 4
    CT = 82
    E1 = 336
    ed, EH, anc = _bg_editor(P, X0, CT, E1 - X0)
    o += ed
    o += _bg_page(P, E1 + 8, CT, X1 - E1 - 8, EH)
    for n, k in ((1, 'open'), (2, 'save'), (3, 'export'), (4, 'display'), (5, 'clear')):
        cx = bx[k][0] + bx[k][1] / 2
        o.append(P.bubble(n, cx, 28, cx, 49))
    o.append(P.bubble(6, 80, anc['head'], X0, anc['head']))
    o.append(P.bubble(7, 80, anc['sit'], X0, anc['sit']))
    o.append(P.bubble(8, 80, anc['others'], X0, anc['others']))
    o.append(P.bubble(9, 640, CT + 22, X1, CT + 22))
    o.append('</g>')
    o.append('</svg>')
    o[0] = P.svg_open('pl-wide', 720, CT + EH + 22 + 12, 'L’écran du Briefing Generator, en Standard', 'The Briefing Generator screen, in Standard', 'bgw')
    return '\n          '.join(o)


def _ico_trash(cx, cy):
    return (f'<path d="M{_n(cx - 5)},{_n(cy - 3)} h10 M{_n(cx - 2)},{_n(cy - 3)} v-2 h4 v2 M{_n(cx - 4)},{_n(cy - 3)} l.8,8 h6.4 l.8,-8" fill="none" stroke="currentColor" stroke-width="1.1"/>')


def _bg_tall(P):
    W = 360
    o = ['']
    o.append(P.title_tall('L’ÉCRAN DU BRIEFING GENERATOR', 'THE BRIEFING GENERATOR SCREEN', 'au téléphone', 'on a phone'))
    o.append('<g transform="translate(0,12)">')
    X0, X1 = 30, 330
    w = X1 - X0
    o.append(sv_box(X0, 62, w, 30))
    o.append(P.btn(X0 + 4, 66, 20, 22, [D('◄')]))
    o.append(P.text(X0 + 30, 81, 8.5, D('B·G'), anchor='start', extra=' font-weight="700"'))
    bx, x = {}, X0 + 62
    for key, bw, ico, chv in (('open', 30, _rp_ico_folder, True), ('save', 24, _rp_ico_disk, False), ('export', 24, _rp_ico_export, False),
                              ('display', 24, _rp_ico_eye, False), ('clear', 24, _ico_trash, False)):
        o.append(P.btn(x, 66, bw, 22))
        o.append(ico(x + (9 if chv else bw / 2), 77))
        if chv:
            o.append(_rp_ico_chev(x + 19, 76))
        bx[key] = (x, bw)
        x += bw + 6
    # l'onglet En-tête, seul visible : sa section et ses quatre champs
    o.append(sv_box(X0, 100, w, 22))
    o += _head(P, X0, 100, w, [L('bg', 'editor.header.summary')], fold=False, chevron=False)
    a, aw = X0 + 10, w - 20
    for k, (lab, val) in enumerate((('editor.meta.operation', 'STEPPE WIND'), ('editor.meta.missionCode', 'M3'), ('editor.meta.date', '1989-03-22'), ('editor.meta.time', '08:00'))):
        o.append(P.lfield(a, 130 + k * 32, aw, [L('bg', lab)], [D(val)]))
    o.append(P.text(X0 + w / 2, 270, 8, L('bg', 'editor.autoSave'), op=.65))
    # la barre d'onglets : une largeur par libellé, pictogramme au-dessus
    TT = 284
    o.append(sv_box(X0, TT, w, 40))
    tabs = (('▤', 'tab.header', True), ('▣', 'tab.simple.situation', False), ('✈', 'tab.mission', False), ('☎', 'tab.simple.coord', False),
            ('▨', 'tab.simple.photos', False), ('⚙', 'tab.meta', False), ('◈', 'tab.preview', False))
    lens = [max(len(P.resolve([L('bg', key)])[0]), len(P.resolve([L('bg', key)])[1])) for _g, key, _c in tabs]
    widths = [6 + 4.9 * n for n in lens]
    k_ = w / sum(widths)
    widths = [v * k_ for v in widths]
    tx, cxs = X0, {}
    for (g, key, cur), tw in zip(tabs, widths):
        cx = tx + tw / 2
        if cur:
            o.append(f'<rect x="{_n(tx + 1.5)}" y="{_n(TT + 3)}" width="{_n(tw - 3)}" height="34" rx="2" fill="none" stroke="currentColor" stroke-width="1.4"/>')
        o.append(P.text(cx, TT + 16, 9, D(g)))
        o.append(P.text(cx, TT + 31, 8, L('bg', key)))
        cxs[key] = cx
        tx += tw
    for n, k in ((1, 'open'), (2, 'save'), (3, 'export'), (4, 'display'), (5, 'clear')):
        cx = bx[k][0] + bx[k][1] / 2
        o.append(P.bubble(n, cx, 46, cx, 66))
    o.append(P.bubble(6, 14, 111, X0, 111))
    o.append(P.bubble(7, cxs['tab.simple.situation'], TT + 58, cxs['tab.simple.situation'], TT + 40))
    o.append(P.bubble(8, cxs['tab.mission'] + 4, TT + 58, cxs['tab.mission'], TT + 40))
    o.append(P.bubble(9, cxs['tab.preview'], TT + 58, cxs['tab.preview'], TT + 40))
    o.append('</g>')
    o.append('</svg>')
    o[0] = P.svg_open('pl-tall', W, TT + 58 + 8.5 + 12 + 6, 'L’écran du Briefing Generator au téléphone, en Standard', 'The Briefing Generator screen on a phone, in Standard', 'bgt')
    return '\n          '.join(o)


def _bg_legend_rows():
    return [
        (1, [L('bg', 'toolbar.load', add='▾')],
         [L('bg', 'work.open'), ' lit un fichier de travail de la suite ; ', L('bg', 'work.briefing'), ' lit un ancien fichier de briefing, le format choisi voyageant avec lui.'],
         [L('bg', 'work.open'), ' reads a suite work file; ', L('bg', 'work.briefing'), ' reads an old briefing file, the chosen format travelling with it.']),
        (2, [L('bg', 'toolbar.save')],
         ['écrit le fichier de travail de toute la suite (« ', L('bg', 'work.save.tip'), ' », Ctrl+S) ; le briefing est en plus gardé automatiquement dans le navigateur (« ', L('bg', 'editor.autoSave'), ' »).'],
         ['writes the work file of the whole suite (“', L('bg', 'work.save.tip'), '”, Ctrl+S); the briefing is also kept automatically in the browser (“', L('bg', 'editor.autoSave'), '”).']),
        (3, [L('bg', 'toolbar.export')],
         'vérifiez d’abord la mise en page dans l’aperçu. L’export porte les pages du format en cours, en PDF (par l’impression du navigateur, Ctrl+P puis « Enregistrer en PDF », y compris sur Android) ou en PNG par page.',
         'check the layout in the preview first. The export carries the pages of the current format, as a PDF (through the browser’s print, Ctrl+P then “Save as PDF”, on Android too) or as one PNG per page.'),
        (4, [L('bg', 'toolbar.display', add='▾')],
         'choisit le format, Standard ou Avancé ; un point ambre sur le bouton signale Avancé. Changer de format ne perd rien : seules les sections affichées et les pages produites changent, et ce que vous avez saisi pour l’autre format revient quand vous y retournez.',
         'chooses the format, Standard or Advanced; an amber dot on the button marks Advanced. Changing format loses nothing: only the sections shown and the pages produced change, and what you entered for the other format comes back when you return to it.'),
        (5, [L('bg', 'toolbar.reset')],
         'vide tout le briefing, après confirmation.',
         'empties the whole briefing, after a confirmation.'),
        (6, [L('bg', 'editor.header.summary')],
         'l’outil s’ouvre sur une page blanche, en Standard ; les champs vides disent en grisé ce qu’on y met, et cet indice n’est ni dans l’aperçu ni à l’export. Une date qui n’a pas la forme attendue est gardée telle quelle, et le champ prend la couleur d’avertissement.',
         'the tool opens on a blank page, in Standard; empty fields say in grey what goes in them, and that hint is neither in the preview nor in the export. A date that does not have the expected form is kept as it is, and the field takes the warning colour.'),
        (7, [L('bg', 'editor.simple.situation.summary')],
         ['un point de situation par ligne, ✕ le retire, « ', L('bg', 'editor.sitac.addPoint'), ' » en ajoute un, puis le champ ', L('bg', 'editor.simple.map'), ' plus bas dans la section. La carte, les menaces et les cibles sont communes aux deux formats : si une carte est chargée, ou si des menaces ou des cibles sont saisies, une page de carte suit, puis les pages de photos.'],
         ['one situation point per line, ✕ removes it, “', L('bg', 'editor.sitac.addPoint'), '” adds one, then the ', L('bg', 'editor.simple.map'), ' field further down in the section. The map, the threats and the targets are common to both formats: if a map is loaded, or threats or targets are entered, a map page follows, then the photo pages.']),
        (8, [M('Les autres sections', 'The other sections')],
         ['Mission, Coordination, Photos et Métadonnées. L’icône à droite d’un en-tête, « ', L('bg', 'ui.foldall'), ' » ou « ', L('bg', 'ui.unfoldall'), ' », replie toutes les sections ou les déplie toutes. Au téléphone, l’éditeur passe en onglets.'],
         ['Mission, Coordination, Photos and Metadata. The icon at the right of a header, “', L('bg', 'ui.foldall'), '” or “', L('bg', 'ui.unfoldall'), '”, folds all the sections or unfolds them all. On a phone, the editor switches to tabs.']),
        (9, [M('L’aperçu', 'The preview')],
         'la page de mission : situation, mission et groupes, fréquences, terrains et météo. Un bloc vide n’est pas imprimé, et une page qui déborde se poursuit sur la suivante.',
         'the mission page: situation, mission and groups, frequencies, airfields and weather. An empty block is not printed, and a page that overflows continues on the next one.'),
    ]


def build_plate_bg():
    """La planche du Briefing Generator (Standard) : le HTML (cadre, figure zoomable, légende) ; ses libellés viennent du dictionnaire du BG."""
    P = Plate('bg', ['bg'])
    wide, tall = _bg_wide(P), _bg_tall(P)
    legend = P.legend_html(_bg_legend_rows())
    P.verify(wide, tall)
    return P.figure_html(wide, tall,
                         'Fig. 2 — L’écran du Briefing Generator en Standard : la barre, l’éditeur par sections, puis l’aperçu de la page de mission.',
                         'Fig. 2 — The Briefing Generator screen in Standard: the bar, the editor by sections, then the preview of the mission page.', legend)


# ═════════════════════════════════════════════════════════════════════════════════
# La planche de Recon Station : le panneau, la photo annotée, la barre du bas
# ═════════════════════════════════════════════════════════════════════════════════

_RS_FOLDED = ('editor.text.title', 'editor.fx.title', 'editor.info.title', 'editor.logo.title', 'editor.cartouche.title', 'editor.shapes.title',
              'editor.marker.color', 'editor.classif.title')


def _rs_panel(P, x, y, w):
    """Le panneau : « Image source » et « Rendu » ouverts, les huit autres repliés. Renvoie (SVG, bas, ancres {clé: y de l'en-tête})."""
    o, anc = [], {}
    a, aw = x + 8, w - 16
    h1 = 114
    o.append(sv_box(x, y, w, h1))
    o += _head(P, x, y, w, [L('rs', 'editor.image.title')])
    o.append(_rule(x, x + w, y + 24))
    o.append(_rp_rect(a, y + 30, aw, 42, op=.7, dash=True))
    o.append(P.text(a + aw / 2, y + 48, 8, D('RS_EXAMPLE_NAIP.JPG — 1200×800PX')))
    o.append(P.text(a + aw / 2, y + 62, 8, L('rs', 'editor.image.drop.hint', up=True), op=.65))
    o.append(P.text(a + aw / 2, y + 84, 8, L('rs', 'editor.image.credit'), op=.6))
    o.append(P.btn(a, y + 90, aw, 16, [L('rs', 'editor.image.replace')]))
    anc['image'] = y + 12
    y2 = y + h1 + 6
    o.append(sv_box(x, y2, w, 56))
    o += _head(P, x, y2, w, [L('rs', 'editor.render.title')])
    o.append(_rule(x, x + w, y2 + 24))
    o.append(P.text(a, y2 + 41, 8, L('rs', 'editor.render.contrast'), anchor='start', op=.75))
    sx0, sx1 = a + 52, a + aw - 34
    o.append(f'<line x1="{_n(sx0)}" y1="{_n(y2 + 38)}" x2="{_n(sx1)}" y2="{_n(y2 + 38)}" stroke="currentColor" stroke-width="1.2" opacity=".55"/>')
    o.append(f'<circle class="sv-box" cx="{_n(sx0 + (sx1 - sx0) * .3)}" cy="{_n(y2 + 38)}" r="4" stroke="currentColor" stroke-width="1.2"/>')
    o.append(P.text(a + aw, y2 + 41, 8, D('105%'), anchor='end', op=.75))
    anc['render'] = y2 + 12
    y3 = y2 + 56 + 6
    for k, key in enumerate(_RS_FOLDED):
        o += _sec_closed(P, 'rs', x, y3 + k * 27, w, key)
        anc[key] = y3 + k * 27 + 11
    return o, y3 + len(_RS_FOLDED) * 27 - 5, anc


_RS_TOOLS = ('rsd.tool.select', 'rsd.tool.rect', 'rsd.tool.ellipse', 'rsd.tool.poly', 'rsd.tool.arrow', 'rsd.tool.bracket', 'rsd.tool.label', 'rsd.tool.inset')


def _rs_canvas(P, x, y, w, h):
    """La zone de la photo : la photo en aplat au trait et ses annotations, puis la barre des outils du bas. Renvoie (SVG, ancres)."""
    o, anc = [sv_box(x, y, w, h)], {}
    ph_w = w - 16
    ph_h = ph_w * 2 / 3
    px = x + 8
    py = y + (h - 40 - ph_h) / 2
    o.append(f'<rect x="{_n(px)}" y="{_n(py)}" width="{_n(ph_w)}" height="{_n(ph_h)}" fill="none" stroke="currentColor" stroke-width="1.2" opacity=".8"/>')
    for bx, by, bw, bh in ((10, 14, 50, 30), (70, 10, 40, 24), (118, 14, 46, 28), (14, 60, 36, 34), (62, 66, 30, 26), (100, 112, 44, 26), (14, 110, 40, 30),
                           (196, 70, 30, 30), (236, 66, 36, 40), (150, 140, 20, 30)):
        o.append(f'<rect x="{_n(px + bx)}" y="{_n(py + by)}" width="{_n(bw)}" height="{_n(bh)}" rx="1" fill="currentColor" opacity=".10" stroke="currentColor" stroke-width=".6"/>')
    # annotations : un cadre, une ellipse, trois marquages numérotés, une loupe, le cartouche, le bloc d'informations
    o.append(f'<rect x="{_n(px + 98)}" y="{_n(py + 72)}" width="76" height="28" fill="none" stroke="currentColor" stroke-width="1.6"/>')
    o.append(f'<ellipse cx="{_n(px + 50)}" cy="{_n(py + 132)}" rx="28" ry="13" fill="none" stroke="currentColor" stroke-width="1.6"/>')
    for n, (cx, cy, tx, ty) in enumerate(((px + 206, py + 52, px + 174, py + 80), (px + 118, py + 56, px + 130, py + 72), (px + 28, py + 100, px + 38, py + 120)), 1):
        o.append(f'<line x1="{_n(cx)}" y1="{_n(cy)}" x2="{_n(tx)}" y2="{_n(ty)}" stroke="currentColor" stroke-width="1.2" opacity=".8"/>')
        o.append(f'<circle class="sv-box" cx="{_n(cx)}" cy="{_n(cy)}" r="6.5" stroke="currentColor" stroke-width="1.4"/>')
        o.append(P.text(cx, cy + 2.8, 8, D(str(n)), extra=' font-weight="700"'))
    tw = 108
    tx0, ty0 = px + ph_w - tw - 6, py + 6
    o.append(sv_box(tx0, ty0, tw, 38))
    for k, (n, txt) in enumerate((('1', ('STOCKAGE POL', 'POL STORAGE')), ('2', ('PARC DE RÉSERVOIRS', 'TANK FARM')), ('3', ('PARC DE VÉHICULES', 'VEHICLE PARK')))):
        o.append(P.text(tx0 + 6, ty0 + 12 + k * 11, 8, D(n), anchor='start', op=.8))
        o.append(P.text(tx0 + 16, ty0 + 12 + k * 11, 8, D(*txt), anchor='start', op=.85))
    anc['table'] = (tx0 + tw, ty0 + 19)
    iw, ih = 96, 52
    ix0, iy0 = px + ph_w - iw - 6, py + ph_h - ih - 6
    o.append(f'<rect x="{_n(px + 134)}" y="{_n(py + 112)}" width="14" height="10" fill="none" stroke="currentColor" stroke-width="1" stroke-dasharray="3 2" opacity=".8"/>')
    o.append(f'<line x1="{_n(px + 148)}" y1="{_n(py + 118)}" x2="{_n(ix0)}" y2="{_n(iy0 + 8)}" stroke="currentColor" stroke-width="1" stroke-dasharray="3 2" opacity=".7"/>')
    o.append(sv_box(ix0, iy0, iw, ih))
    o.append(f'<circle cx="{_n(ix0 + 34)}" cy="{_n(iy0 + 28)}" r="11" fill="none" stroke="currentColor" stroke-width="1.4"/>')
    o.append(P.text(ix0 + 34, iy0 + 31, 8, D('2'), extra=' font-weight="700"'))
    o.append(_bars(ix0 + 56, iy0 + 18, 32, 3, gap=9))
    anc['inset'] = (ix0 + iw, iy0 + ih / 2)
    o.append(_bars(px + 8, py + ph_h - 28, 110, 3, gap=9))
    # la barre des outils du bas
    ty = y + h - 40
    o.append(sv_box(x + 3, ty, w - 6, 32))
    lens = [max(len(P.resolve([L('rs', k, up=True)])[0]), len(P.resolve([L('rs', k, up=True)])[1])) for k in _RS_TOOLS]
    widths = [6 + 5.0 * n for n in lens]
    k_ = (w - 12) / sum(widths)
    widths = [v * k_ for v in widths]
    cx0 = x + 6
    for k, (key, bw) in enumerate(zip(_RS_TOOLS, widths)):
        if k == 0:
            o.append(_rp_active(P, cx0 + 1, ty + 4, bw - 2, 24, [L('rs', key, up=True)]))
        else:
            o.append(P.btn(cx0 + 1, ty + 4, bw - 2, 24, [L('rs', key, up=True)], op=.5))
        cx0 += bw
    anc['bar'] = (x + w - 3, ty + 16)
    return o, anc


def _rs_wide(P):
    o = ['']
    o.append(P.title_wide('L’ÉCRAN DE RECON STATION', 'THE RECON STATION SCREEN', 24, 32))
    o.append('<g transform="translate(0,22)">')
    X0, X1 = 110, 610
    o += [sv_box(X0, 44, X1 - X0, 28), P.text(X0 + 8, 62, 8, L('rs', 'toolbar.subtitle'), anchor='start', op=.7, ls=.6)]
    bx, x = {}, X0 + 104
    for key, w, parts in (('open', 56, [L('rs', 'toolbar.open', add='▾')]), ('save', 68, [L('rs', 'toolbar.save')]), ('export', 54, [L('rs', 'toolbar.export')]),
                          ('clear', 48, [L('rs', 'toolbar.reset')])):
        o.append(P.btn(x, 49, w, 18, parts))
        bx[key] = (x, w)
        x += w + 4
    CT = 82
    pn, PE, anc = _rs_panel(P, X0, CT, 190)
    o += pn
    cv, canc = _rs_canvas(P, 308, CT, X1 - 308, PE - CT)
    o += cv
    for n, k in ((1, 'open'), (2, 'save'), (3, 'export')):
        cx = bx[k][0] + bx[k][1] / 2
        o.append(P.bubble(n, cx, 28, cx, 49))
    for n, k in ((4, 'image'), (5, 'render'), (6, 'editor.fx.title'), (7, 'editor.info.title'), (8, 'editor.logo.title'), (9, 'editor.shapes.title'), (10, 'editor.classif.title')):
        o.append(P.bubble(n, 80, anc[k], X0, anc[k]))
    o.append(P.bubble(11, 640, canc['table'][1], canc['table'][0], canc['table'][1]))
    o.append(P.bubble(12, 640, canc['inset'][1], canc['inset'][0], canc['inset'][1]))
    o.append(P.bubble(13, 640, canc['bar'][1], canc['bar'][0], canc['bar'][1]))
    o.append('</g>')
    o.append('</svg>')
    o[0] = P.svg_open('pl-wide', 720, PE + 22 + 12, 'L’écran de Recon Station, une photo annotée', 'The Recon Station screen, with an annotated photo', 'rsw')
    return '\n          '.join(o)


def _rs_tall(P):
    W = 360
    o = ['']
    o.append(P.title_tall('L’ÉCRAN DE RECON STATION', 'THE RECON STATION SCREEN', 'au téléphone', 'on a phone'))
    o.append('<g transform="translate(0,12)">')
    X0, X1 = 30, 330
    w = X1 - X0
    o.append(sv_box(X0, 62, w, 30))
    o.append(P.btn(X0 + 4, 66, 20, 22, [D('◄')]))
    o.append(P.text(X0 + 30, 81, 8.5, D('R·S'), anchor='start', extra=' font-weight="700"'))
    bx, x = {}, X0 + 112
    for key, bw, ico, chv in (('open', 30, _rp_ico_folder, True), ('save', 24, _rp_ico_disk, False), ('export', 24, _rp_ico_export, False), ('clear', 24, _ico_trash, False)):
        o.append(P.btn(x, 66, bw, 22))
        o.append(ico(x + (9 if chv else bw / 2), 77))
        if chv:
            o.append(_rp_ico_chev(x + 19, 76))
        bx[key] = (x, bw)
        x += bw + 8
    pn, PE, anc = _rs_panel(P, X0, 100, w)
    o += pn
    TT = PE + 8
    o.append(sv_box(X0, TT, w, 28))
    o.append(f'<rect x="{_n(X0 + 3)}" y="{_n(TT + 3)}" width="{_n(w / 2 - 4)}" height="22" rx="2" fill="none" stroke="currentColor" stroke-width="1.4"/>')
    o.append(P.text(X0 + w / 4, TT + 18, 8.5, L('rs', 'tab.editor')))
    o.append(P.text(X0 + 3 * w / 4, TT + 18, 8.5, L('rs', 'tab.preview')))
    for n, k in ((1, 'open'), (2, 'save'), (3, 'export')):
        cx = bx[k][0] + bx[k][1] / 2
        o.append(P.bubble(n, cx, 46, cx, 66))
    for n, k in ((4, 'image'), (5, 'render'), (6, 'editor.fx.title'), (7, 'editor.info.title'), (8, 'editor.logo.title'), (9, 'editor.shapes.title'), (10, 'editor.classif.title'),
                 (11, 'editor.cartouche.title')):
        o.append(P.bubble(n, 14, anc[k], X0, anc[k]))
    o.append('</g>')
    o.append('</svg>')
    o[0] = P.svg_open('pl-tall', W, TT + 28 + 12 + 8, 'L’écran de Recon Station au téléphone : le panneau de l’éditeur, onglet Éditeur', 'The Recon Station screen on a phone: the editor panel, Editor tab', 'rst')
    return '\n          '.join(o)


def _rs_legend_rows():
    return [
        (1, [L('rs', 'toolbar.open', add='▾')],
         ['propose ', L('rs', 'work.open'), ' et ', L('rs', 'work.image')],
         ['offers ', L('rs', 'work.open'), ' and ', L('rs', 'work.image')]),
        (2, [L('rs', 'toolbar.save')],
         'Ctrl+S range la composition dans le fichier de travail, sans l’image source : après un rechargement de la page, importez de nouveau l’image.',
         'Ctrl+S stores the composition in the work file, without the source image: after a page reload, import the image again.'),
        (3, [L('rs', 'toolbar.export')],
         'propose un nom (la cible et l’heure), que vous pouvez changer, et écrit un PNG sans perte à la résolution de la source ; l’aperçu à l’écran est réduit.',
         'proposes a name (the target and the time), which you can change, and writes a lossless PNG at the source’s resolution; the on-screen preview is reduced.'),
        (4, [L('rs', 'editor.image.title')],
         'l’image est d’abord convertie en niveaux de gris.',
         'the image is first converted to greyscale.'),
        (5, [L('rs', 'editor.render.title')],
         [L('rs', 'editor.render.contrast'), ' accentue ou adoucit les écarts.'],
         [L('rs', 'editor.render.contrast'), ' sharpens or softens the differences.']),
        (6, [L('rs', 'editor.fx.title')],
         [L('rs', 'editor.fx.sensor'), ' donne l’allure d’un capteur, par stylisation du signal et non par mesure ; ', L('rs', 'editor.fx.vignette'), ', ', L('rs', 'editor.fx.grain'), ' et ', L('rs', 'editor.fx.scanlines'), ', éteints par défaut, ajoutent l’usure d’un tirage. Recon ne peint jamais d’élément absent de l’image.'],
         [L('rs', 'editor.fx.sensor'), ' gives the look of a sensor, by stylising the signal and not by measurement; ', L('rs', 'editor.fx.vignette'), ', ', L('rs', 'editor.fx.grain'), ' and ', L('rs', 'editor.fx.scanlines'), ', off by default, add the wear of a print. Recon never paints an element that is not in the image.']),
        (7, [L('rs', 'editor.info.title')],
         'se pose en bas de la photo : les champs vides ne s’impriment pas. À l’ouverture de RS, le briefing du BG préremplit le bloc ; un champ déjà rempli n’est jamais écrasé.',
         'sits at the bottom of the photo: empty fields are not printed. When RS opens, the BG’s briefing pre-fills the block; a field already filled is never overwritten.'),
        (8, [L('rs', 'editor.logo.title')],
         ['les logos du Wing d’HQ sont proposés dans la grille, marqués ', L('rs', 'editor.logo.wing'), ' ; vous pouvez en ajouter par une image PNG, et chaque logo se rend en couleur, en niveaux de gris ou en blanc.'],
         ['the HQ Wing logos are offered in the grid, marked ', L('rs', 'editor.logo.wing'), '; you can add some from a PNG image, and each logo renders in colour, greyscale or white.']),
        (9, [L('rs', 'editor.shapes.title')],
         'les formes et les étiquettes se posent au centre, puis se déplacent.',
         'shapes and labels are placed at the centre, then moved.'),
        (10, [L('rs', 'editor.classif.title')],
         'le bandeau de classification, éteint par défaut, réserve sa place pour ne recouvrir ni le cartouche ni le bloc d’informations ; il est distinct du champ Classification du bloc.',
         'the classification banner, off by default, reserves its place so as not to cover the cartouche or the information block; it is separate from the block’s Classification field.'),
        (11, [L('rs', 'editor.cartouche.add')],
         ['dépose un cercle numéroté, à glisser sur la cible, lié à une ligne de légende du cartouche ; la numérotation se recalcule toute seule, et ', L('rs', 'editor.cartouche.amorce'), ' tire un trait jusqu’au point exact de la cible.'],
         ['drops a numbered circle, to drag onto the target, tied to a legend line of the cartouche; the numbering recalculates by itself, and ', L('rs', 'editor.cartouche.amorce'), ' draws a line to the exact point of the target.']),
        (12, [L('rs', 'editor.inset.add')],
         'réaffiche, agrandie, une portion de l’image traitée ; la zone et la boîte se déplacent et se redimensionnent sans déformer l’image.',
         'redisplays, enlarged, a portion of the processed image; the zone and the box move and resize without distorting the image.'),
        (13, [M('La barre du bas', 'The bottom bar')],
         ['annote la photo directement, au toucher : ' + ''] + sum([[L('rs', k, up=True), ', '] for k in _RS_TOOLS[:-1]], [])[:-1] + [' et ', L('rs', _RS_TOOLS[-1], up=True), '.'],
         ['annotates the photo directly, by touch: '] + sum([[L('rs', k, up=True), ', '] for k in _RS_TOOLS[:-1]], [])[:-1] + [' and ', L('rs', _RS_TOOLS[-1], up=True), '.']),
    ]


def build_plate_rs():
    """La planche de Recon Station : le HTML (cadre, figure zoomable, légende) ; ses libellés viennent du dictionnaire de RS."""
    P = Plate('rs', ['rs'])
    wide, tall = _rs_wide(P), _rs_tall(P)
    legend = P.legend_html(_rs_legend_rows())
    P.verify(wide, tall)
    return P.figure_html(wide, tall,
                         'Fig. 2 — L’écran de Recon Station avec l’exemple : la barre, le panneau, la photo annotée et la barre des outils du bas.',
                         'Fig. 2 — The Recon Station screen with the example: the bar, the panel, the annotated photo and the bottom tool bar.', legend)


# ═════════════════════════════════════════════════════════════════════════════════
# La planche de l'accueil de Mission Plan : la barre, le menu Exemple, les deux groupes d'outils
# ═════════════════════════════════════════════════════════════════════════════════

_ST_CARDS = (('mc', (('H·Q', 'HQ'), ('B·G', 'Briefing Generator'), ('R·S', 'Recon Station'))),
             ('fl', (('R·P', 'Route Planner'), ('D·G', 'Datacard Generator'), ('F·C', 'Flight Configurator'))))


def _ico_doc(cx, cy):
    return (f'<path d="M{_n(cx - 4)},{_n(cy - 5)} h5.5 l2.5,2.5 v7.5 h-8 z M{_n(cx - 2)},{_n(cy)} h4 M{_n(cx - 2)},{_n(cy + 2.5)} h4" fill="none" stroke="currentColor" stroke-width="1.1"/>')


def _ico_book(cx, cy):
    return (f'<path d="M{_n(cx - 6)},{_n(cy - 4)} h5 a1,1 0 0 1 1,1 v7 h-6 z M{_n(cx + 6)},{_n(cy - 4)} h-5 a1,1 0 0 0 -1,1 v7 h6 z" fill="none" stroke="currentColor" stroke-width="1.1"/>')


def _ico_flag(cx, cy):
    return (f'<rect x="{_n(cx - 7)}" y="{_n(cy - 4.5)}" width="14" height="9" fill="none" stroke="currentColor" stroke-width="1.1"/>'
            f'<path d="M{_n(cx - 7)},{_n(cy)} h14 M{_n(cx)},{_n(cy - 4.5)} v9" stroke="currentColor" stroke-width="1.1"/>')


def _st_card(P, x, y, w, sigle, name, tool, h=106):
    o = [sv_box(x, y, w, h)]
    o.append(f'<rect x="{_n(x + 6)}" y="{_n(y + 6)}" width="{_n(w - 12)}" height="44" fill="currentColor" opacity=".10" stroke="currentColor" stroke-width=".6"/>')
    o.append(f'<path d="M{_n(x + 6)},{_n(y + 44)} l{_n((w - 12) * .3)},-20 l{_n((w - 12) * .25)},12 l{_n((w - 12) * .22)},-16 l{_n((w - 12) * .23)},24" fill="none" stroke="currentColor" stroke-width=".8" opacity=".4"/>')
    pl, pw = P.pill(x + 8, y + 56, [D(sigle)])
    o.append(pl)
    o.append(P.text(x + 8 + pw + 6, y + 65, 8.5, D(name), anchor='start', extra=' font-weight="700"'))
    o.append(_bars(x + 8, y + 76, w - 16, 1))
    o.append(P.btn(x + 8, y + 84, w - 16, 16, [L('mp', 'cta', up=True)], op=.7))
    return o


def _start_wide(P):
    o = ['']
    o.append(P.title_wide('L’ACCUEIL DE MISSION PLAN', 'THE MISSION PLAN HOME PAGE', 24, 32))
    o.append('<g transform="translate(0,22)">')
    X0, X1 = 40, 680
    o += [sv_box(X0, 44, X1 - X0, 28), sv_box(X0 + 6, 49, 120, 18), P.text(X0 + 66, 61, 8, D('DCS · MISSION PLAN'))]
    bx, x = {}, 180
    for key, w, parts in (('open', 52, [L('mp', 'work.open.btn')]), ('save', 66, [L('mp', 'work.save.btn')]), ('ex', 64, [L('mp', 'ex.btn', add='▾')])):
        o.append(P.btn(x, 49, w, 18, parts))
        bx[key] = (x, w)
        x += w + 6
    o.append(P.btn(x, 49, 74, 18, [L('mp', 'fm.btn')]))
    x += 80
    o.append(P.field(x, 49, 104, 18, [L('mp', 'theme.cwnato', add='▾')]))
    x += 110
    o.append(_ico_flag(x + 12, 58))
    # le menu Exemple, ouvert
    mx, my, mw = bx['ex'][0], 74, X1 - bx['ex'][0]
    o.append(sv_box(mx, my, mw, 36))
    o.append(P.text(mx + 8, my + 14, 8, L('mp', 'ex.mc'), anchor='start'))
    o.append(P.text(mx + 8, my + 29, 8, L('mp', 'ex.fl'), anchor='start'))
    o.append(f'<line x1="{_n(mx)}" y1="{_n(my + 18)}" x2="{_n(mx + mw)}" y2="{_n(my + 18)}" stroke="currentColor" stroke-width=".6" opacity=".3"/>')
    # le bandeau
    o.append(sv_box(X0 + 10, 84, 190, 40))
    o.append(P.text(X0 + 18, 97, 8, L('mp', 'ribbon'), anchor='start', op=.7))
    o.append(P.text(X0 + 18, 117, 15, D('MISSION PLAN'), anchor='start', extra=' font-weight="700"'))
    # les deux groupes
    y = 138
    for gk, cards in _ST_CARDS:
        o.append(f'<rect x="{X0}" y="{y}" width="{X1 - X0}" height="136" rx="3" fill="none" stroke="currentColor" stroke-width="1" stroke-dasharray="5 3" opacity=".55"/>')
        o.append(sv_box(X0 + 14, y - 9, 224, 18))
        nm = 'Mission Commander' if gk == 'mc' else 'Flight Leader'
        o.append(P.text(X0 + 20, y + 3.5, 8.5, D(nm), anchor='start', extra=' font-weight="700"'))
        o.append(P.text(X0 + 20 + 5.6 * len(nm) + 8, y + 3.5, 8, L('mp', 'grp.%s.sub' % gk, up=True), anchor='start', op=.7))
        cw = (X1 - X0 - 24 - 24) / 3
        for k, (sg, name) in enumerate(cards):
            o += _st_card(P, X0 + 12 + k * (cw + 12), y + 18, cw, sg, name, gk)
        y += 150
    for n, k in ((1, 'open'), (2, 'save'), (3, 'ex')):
        cx = bx[k][0] + bx[k][1] / 2
        o.append(P.bubble(n, cx, 28, cx, 49))
    o.append(P.bubble(4, 704, my + 9, X1, my + 9))
    o.append(P.bubble(5, 704, my + 26, X1, my + 26))
    o.append('</g>')
    o.append('</svg>')
    o[0] = P.svg_open('pl-wide', 720, y + 22 + 6, 'L’accueil de Mission Plan, avec le menu Exemple ouvert', 'The Mission Plan home page, with the Example menu open', 'stw')
    return '\n          '.join(o)


def _start_tall(P):
    W = 360
    o = ['']
    o.append(P.title_tall('L’ACCUEIL DE MISSION PLAN', 'THE MISSION PLAN HOME PAGE', 'au téléphone', 'on a phone'))
    o.append('<g transform="translate(0,12)">')
    X0, X1 = 30, 330
    w = X1 - X0
    o.append(sv_box(X0, 56, w, 22))
    o.append(P.text(X0 + w / 2, 71, 8, D('DCS · MISSION PLAN')))
    IY = 108
    o.append(sv_box(X0, IY, w, 30))
    bx, x = {}, X0 + 6
    for key, bw, ico in (('open', 28, _rp_ico_folder), ('save', 28, _rp_ico_disk), ('ex', 40, _ico_doc), ('fm', 28, _ico_book)):
        o.append(P.btn(x, IY + 4, bw, 22))
        o.append(ico(x + (bw / 2 - (5 if key == 'ex' else 0)), IY + 15))
        if key == 'ex':
            o.append(_rp_ico_chev(x + 29, IY + 14))
        bx[key] = (x, bw)
        x += bw + 6
    # au téléphone, le thème et la langue sont sous « ⋯ », au bout droit de la barre
    o.append(P.btn(X1 - 6 - 28, IY + 4, 28, 22, [D('⋯')]))
    mx, my, mw = X0, IY + 34, w
    o.append(sv_box(mx, my, mw, 36))
    o.append(_bars(mx + 8, my + 11, 250, 1))
    o.append(_bars(mx + 8, my + 26, 270, 1))
    y = my + 46
    for gk, cards in _ST_CARDS:
        o.append(f'<rect x="{X0}" y="{y}" width="{w}" height="104" rx="3" fill="none" stroke="currentColor" stroke-width="1" stroke-dasharray="5 3" opacity=".55"/>')
        o.append(sv_box(X0 + 8, y - 9, 246, 18))
        nm = 'Mission Commander' if gk == 'mc' else 'Flight Leader'
        o.append(P.text(X0 + 14, y + 3.5, 8.5, D(nm), anchor='start', extra=' font-weight="700"'))
        o.append(P.text(X0 + 14 + 5.6 * len(nm) + 8, y + 3.5, 8, L('mp', 'grp.%s.sub' % gk, up=True), anchor='start', op=.7))
        for k, (sg, name) in enumerate(cards):
            ry = y + 14 + k * 29
            o.append(sv_box(X0 + 8, ry, w - 16, 25))
            o.append(f'<rect x="{_n(X0 + 12)}" y="{_n(ry + 4)}" width="30" height="17" fill="currentColor" opacity=".10" stroke="currentColor" stroke-width=".6"/>')
            pl, pw = P.pill(X0 + 48, ry + 7, [D(sg)])
            o.append(pl)
            o.append(P.text(X0 + 48 + pw + 5, ry + 16, 8, D(name), anchor='start', extra=' font-weight="700"'))
            o.append(P.btn(X1 - 8 - 104, ry + 4, 100, 17, [L('mp', 'cta', up=True)], op=.7))
        y += 114
    for n, k in ((1, 'open'), (2, 'save'), (3, 'ex')):
        cx = bx[k][0] + bx[k][1] / 2
        o.append(P.bubble(n, cx, IY - 12, cx, IY + 4))
    o.append(P.bubble(4, 346, my + 11, X1, my + 11))
    o.append(P.bubble(5, 346, my + 26, X1, my + 26))
    o.append('</g>')
    o.append('</svg>')
    o[0] = P.svg_open('pl-tall', W, y + 12 + 8, 'L’accueil de Mission Plan au téléphone', 'The Mission Plan home page on a phone', 'stt')
    return '\n          '.join(o)


def _start_legend_rows():
    return [
        (1, [L('mp', 'work.open.btn')],
         'à l’accueil ; dans les outils, Ouvrir ▾ › Ouvrir un travail… relit un fichier de travail et remplace tout le travail. Il garde : vos presets d’emport, le Wing, la mission d’HQ, la langue et le thème ; vos unités et réglages de cap si le fichier n’en porte pas.',
         'on the home page; in the tools, Open ▾ › Open a work file… reads a work file and replaces all the work. It keeps: your loadout presets, the Wing, the HQ mission, the language and the theme; your units and heading settings if the file carries none.'),
        (2, [L('mp', 'work.save.btn')],
         'à l’accueil et dans chaque outil sauf HQ ; Ctrl+S, Cmd+S sur Mac. Écrit le fichier de travail de toute la suite : briefing, composition de RS, groupes, routes, calques, datacards. HQ écrit le .miz par Sauvegarder .miz. Hors du fichier : le Wing, la mission d’HQ, l’image source de RS, les presets d’emport.',
         'on the home page and in every tool except HQ; Ctrl+S, Cmd+S on Mac. Writes the work file of the whole suite: briefing, RS composition, groups, routes, layers, datacards. HQ writes the .miz with Save .miz. Left out of the file: the Wing, the HQ mission, the RS source image, the loadout presets.'),
        (3, [L('mp', 'ex.btn', add='▾')],
         'dans la barre de l’accueil, seulement : les outils n’ont pas ce menu ; HQ a son bouton Exemple. Deux lignes, qui remplacent le travail de ce groupe d’outils, sans question. Il garde l’autre groupe, vos unités et réglages de cap. Le bouton d’HQ ouvre une escadre de démonstration et garde la vôtre.',
         'in the home page bar only: the tools have no such menu; HQ has its Example button. Two lines, which replace the work of that tool group, without asking. It keeps the other group, your units and heading settings. HQ’s button opens a demonstration wing and keeps yours.'),
        (4, [L('mp', 'ex.mc')],
         'un briefing et une photo.',
         'a briefing and a photo.'),
        (5, [L('mp', 'ex.fl')],
         'une route, un groupe et sa datacard.',
         'a route, a group and its datacard.'),
    ]


def build_plate_start():
    """La planche de l'accueil : le HTML (cadre avec l'ancre « gestes », figure zoomable, légende) ; ses libellés viennent du dictionnaire de Mission Plan."""
    P = Plate('start', ['mp'])
    wide, tall = _start_wide(P), _start_tall(P)
    legend = P.legend_html(_start_legend_rows())
    P.verify(wide, tall)
    return P.figure_html(wide, tall,
                         'Fig. 2 — L’accueil de Mission Plan, le menu Exemple ouvert : la barre, les deux lignes de l’exemple, les deux groupes d’outils.',
                         'Fig. 2 — The Mission Plan home page with the Example menu open: the bar, the two example lines, the two tool groups.', legend, anchor='gestes')
