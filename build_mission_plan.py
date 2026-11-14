#!/usr/bin/env python3
"""
build_mission_plan.py — DCS Mission Plan shell v1.0
Produit dist/dcs_mission_plan.html (fichier autonome, single-file, offline).

Usage : python3 build_mission_plan.py
Sortie : ./dist/dcs_mission_plan.html

Sources modules actifs (produits par les sept autres build_*.py, dans ./dist/) :
  dist/dcs_hq.html
  dist/dcs_briefing_generator.html
  dist/dcs_datacard_generator.html
  dist/dcs_recon_station.html
  dist/dcs_route_planner.html
  dist/dcs_flight_configurator.html
  dist/dcs_field_manual.html

Sources images (à placer dans ./tiles/) :
  tiles/hq.webp  tiles/bg.webp  tiles/rs.webp  tiles/rp.webp  tiles/kg.webp  tiles/fc.webp
  (le Field Manual n'a plus de carte : tiles/fm.webp reste au dépôt, il n'est pas embarqué)
"""

import base64
import json
import os
import re
import sys

from shell_only_block import build_block as build_shell_only_block, BLOCK_BEGIN as SHELL_ONLY_BEGIN, BLOCK_END as SHELL_ONLY_END
from messages_block import build_block as build_messages_block, build_css as build_messages_css
from ui_block import build_css as build_ui_css, fingerprint as ui_fingerprint
from suite_file_block import build_presets_merge, build_block as build_suite_file_block, build_html as build_suite_file_html, build_css as build_suite_file_css, THEME_VARS as SUITE_THEME_VARS
import group_store_block

CONTRAST_CSS = r"""
/* MP-20 begin */
/* Contrastes (texte sous 18 px, 4,5 : 1 au moins) : couleur du texte seule, la palette commune ne bouge pas. */
:where(body[data-theme="cw-nato"]) .classif { color: #c88075; }
:where(body[data-theme="cw-nato"]) .bigstamp { color: #d7a29a; }
:where(body[data-theme="cw-nato"]) .pver { color: #40392c; }
:where(body[data-theme="cw-nato"]) .pdesc { color: #40392c; }
:where(body[data-theme="cw-nato"]) .pstatus { color: #373d24; }
:where(body[data-theme="cw-nato"]) .foot { color: #f1ece3; }
:where(body[data-theme="cw-soviet"]) .classif { color: #ba8181; }
:where(body[data-theme="cw-soviet"]) .bigstamp { color: #cda3a3; }
:where(body[data-theme="cw-soviet"]) .pver { color: #3c3629; }
:where(body[data-theme="cw-soviet"]) .pdesc { color: #3c3629; }
:where(body[data-theme="cw-soviet"]) .pstatus { color: #273654; }
:where(body[data-theme="cw-soviet"]) .foot { color: #f1ebd5; }
:where(body[data-theme="modern-nato"]) .foot { color: #e8ebed; }
[data-theme="modern-nato"] .bigstamp { color: #e8ebed; }
:where(body[data-theme="modern-east"]) .foot { color: #edebe7; }
[data-theme="modern-east"] .classif { color: #ae847c; }
[data-theme="modern-east"] .bigstamp { color: #f1eae9; }
/* MP-20 end */
"""

LANDING_CSS = r"""
/* ===== Deux cadres selon le rôle : Mission Commander, Flight Leader (sans numéro) ===== */
.mp-grp{position:relative; border:2px dashed color-mix(in srgb, var(--accent) 55%, transparent); border-radius:8px; padding:34px 18px 22px; background:rgba(0,0,0,.18);}
.mp-tab{position:absolute; top:-15px; left:22px; z-index:7; display:flex; gap:10px; align-items:baseline; background:var(--paper); color:var(--ink);
  border:1px solid var(--paper-edge); padding:5px 14px; border-radius:4px; box-shadow:0 6px 14px rgba(0,0,0,.45); transform:rotate(-1deg);}
.mp-tab b{font-family:var(--f-sten); font-size:20px; letter-spacing:.04em;}
.mp-tab small{font-family:var(--f-mono); font-size:10px; letter-spacing:.16em; text-transform:uppercase; color:var(--ink-2);}
/* ===== La barre du haut : Ouvrir…, Sauvegarder, Exemple ▾, Field Manual (icône et texte ; l'icône seule sous 760 px) ===== */
.mp-sep{width:1px; align-self:stretch; background:var(--line); margin:0 2px;}
.mp-railbtn{display:inline-flex; align-items:center; justify-content:center; gap:7px; box-sizing:border-box; min-width:44px; min-height:44px; padding:7px 12px;
  font-family:var(--f-ui); font-weight:500; font-size:12px; letter-spacing:.08em; text-transform:uppercase; color:var(--amber); background:rgba(0,0,0,.3);
  border:1px solid var(--line); border-radius:4px; cursor:pointer;}
.mp-railbtn:hover{border-color:var(--amber);}
.mp-railbtn svg{flex:none;}
#btn-example .mp-chev{width:10px; height:6px;}
#btn-example[aria-expanded="true"]{border-color:var(--amber);}
#btn-example[aria-expanded="true"] .mp-chev{transform:rotate(180deg);}
/* Le menu Exemple ▾ : le composant des listes de la barre (tbm-panel), deux lignes aux libellés entiers (à l'étroit, ils passent à la ligne) */
.tbm-panel.mp-ex-panel{max-width:min(560px, calc(100vw - 16px)); outline:none;}
.mp-ex-panel .tbm-opt{white-space:normal; line-height:1.3; padding-top:8px; padding-bottom:8px;}
.mp-ex-panel .tbm-opt:focus-visible{background:rgba(255,255,255,.06); color:var(--amber);}
.rail .theme-sel{min-height:44px;}
.rail .flag{width:44px; height:44px;}
@media(max-width:760px){
  .rail{padding:11px 12px; gap:10px;}
  .rail .spacer{display:none;}
  .rail .ctrl{flex:1 1 100%; min-width:0;}
  .rail .ctrl .theme-sel{flex:1 1 0; min-width:0; overflow:hidden;}
  .rail .classif{display:none;}
  .mp-railbtn span{display:none;}
  .mp-railbtn{padding:7px 9px;}
}
@media(max-width:900px){
  .mp-tab{flex-direction:column; gap:0; padding:4px 12px;}
  .mp-tab b{font-size:16px; white-space:nowrap;}
  .mp-tab small{font-size:10px;}
}
"""

# ── Configuration ──────────────────────────────────────────────────────────────
OUT_FILE = 'dist/dcs_mission_plan.html'

# status : 'active' = module embarqué ; 'soon' = carte voilée uniquement
# Ordre des modules actifs = ordre des cartes de la landing, en deux cadres : Mission Commander (hq, bg, rs) puis Flight Leader (rp, dg, fc).
# RÈGLE : Field Manual reste TOUJOURS le dernier module actif (il s'ouvre dans le shell, par la barre du haut) et n'a pas de carte :
# 'tile': None. Tout module activé plus tard s'insère avant lui, dans le cadre de son rôle.
MODULES = [
    {'id': 'hq', 'status': 'active', 'src': 'dist/dcs_hq.html',                        'tile': 'tiles/hq.webp'},
    {'id': 'bg', 'status': 'active', 'src': 'dist/dcs_briefing_generator.html',       'tile': 'tiles/bg.webp'},
    {'id': 'rs', 'status': 'active', 'src': 'dist/dcs_recon_station.html',             'tile': 'tiles/rs.webp'},
    {'id': 'rp', 'status': 'active', 'src': 'dist/dcs_route_planner.html',             'tile': 'tiles/rp.webp'},
    {'id': 'dg', 'status': 'active', 'src': 'dist/dcs_datacard_generator.html',        'tile': 'tiles/kg.webp'},
    {'id': 'fc', 'status': 'active', 'src': 'dist/dcs_flight_configurator.html',       'tile': 'tiles/fc.webp'},
    {'id': 'fm', 'status': 'active', 'src': 'dist/dcs_field_manual.html',              'tile': None},
]

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Les polices : celles de la suite, embarquées (octets d'assets.json) ; la page n'appelle aucune police distante
with open(os.path.join(SCRIPT_DIR, 'assets.json')) as _f:
    A = json.load(_f)
for _k in ('OSWALD_500', 'OSWALD_700', 'STARDOS_400', 'STARDOS_700', 'ROBOTO_MONO_400'):
    if not A.get(_k):
        raise SystemExit(f"[ERREUR] Entrée manquante : {_k} dans assets.json")


_KEY_LANG_RE = re.compile(r"\bKEY_LANG\s*=\s*'([0-9A-Za-z_]+)'")
# Les seuls scripts que le <head> d'un module porte : des bibliothèques embarquées (aucun code d'outil), reconnues à leur mention en tête
_HEAD_LIB_BANNERS = ('/*!\n\nJSZip v3.10.1', '/*!\n * html2canvas 1.4.1', '/* @preserve\n * Leaflet 1.9.4', '/*! milsymbol 3.0.5')


def check_shell_only_block():
    """Garde d'identité : la garde du module seul (shell_only_block.build_block()) doit figurer exactement une fois, telle quelle,
    dans chacun des sept modules, dans une balise <script data-lang-key="lang_v1">, premier élément du <body> (la page seule est
    peinte : posée dans le <head>, la garde arrêtait l'analyse avant le <body>, et rien ne se peignait). Le <head> d'un module ne porte
    que des bibliothèques embarquées (JSZip, html2canvas, Leaflet, milsymbol), jamais un script d'outil. Sinon le build s'arrête avant
    toute écriture, en nommant le module."""
    block = build_shell_only_block()
    for mod in MODULES:
        try:
            with open(os.path.join(SCRIPT_DIR, mod['src']), 'r', encoding='utf-8') as fh:
                html = fh.read()
        except OSError as exc:
            raise SystemExit(f"[ERREUR] Module illisible ({exc}) — build arrêté")
        if html.count(block) != 1:
            raise SystemExit(f"[ERREUR] La garde du module seul de {mod['src']} diffère de shell_only_block.py (attendu : une fois, à l'identique) — build arrêté")
        if html.count(SHELL_ONLY_BEGIN) != 1 or html.count(SHELL_ONLY_END) != 1:
            raise SystemExit(f"[ERREUR] Un marqueur de la garde du module seul figure plusieurs fois dans {mod['src']} — build arrêté")
        key = _KEY_LANG_RE.search(html)
        if not key:
            raise SystemExit(f"[ERREUR] KEY_LANG introuvable dans {mod['src']} — build arrêté")
        if key.group(1) != 'lang_v1':
            raise SystemExit(f"[ERREUR] {mod['src']} ne lit pas la langue de la suite (lang_v1) : {key.group(1)} — build arrêté")
        tag = f'<script data-lang-key="{key.group(1)}">\n{block}</script>'
        if html.count(tag) != 1:
            raise SystemExit(f"[ERREUR] {mod['src']} : la garde du module seul n'est pas posée dans une balise <script data-lang-key=\"{key.group(1)}\"> — build arrêté")
        at = html.index(tag)
        head, head_end = html.find('<head>'), html.find('</head>')
        if head < 0 or head_end < head:
            raise SystemExit(f"[ERREUR] {mod['src']} : <head> introuvable — build arrêté")
        for sc in re.finditer(r'<script[^>]*>', html[head:head_end]):
            if not html[head + sc.end():head + sc.end() + 80].startswith(_HEAD_LIB_BANNERS):
                raise SystemExit(f"[ERREUR] {mod['src']} : le <head> porte un script qui n'est pas une bibliothèque embarquée — build arrêté")
        body = re.compile(r'<body[^>]*>\s*').search(html, head_end)
        if not body or html[head_end + len('</head>'):body.start()].strip() or body.end() != at:
            raise SystemExit(f"[ERREUR] {mod['src']} : la garde du module seul n'est pas le premier élément du <body> — build arrêté")
        print(f"  [OK] Garde du module seul identique à shell_only_block.py ({mod['src']})")


def check_suite_colors():
    """Les variables des feuilles de ui_block et de messages_block, posées par le shell sur la fenêtre du nom et sur #toast (suite_file_block.THEME_VARS),
    ont dans chacun des six outils la valeur que le shell leur donne, thème par thème (une variable qui ne change pas d'un thème à l'autre est celle de :root).
    Sinon le build s'arrête, en nommant l'outil, le thème et la variable."""
    for mod in MODULES:
        if mod['id'] in ('fm',):
            continue                                    # le Field Manual n'a ni fenêtre de suite ni toast
        with open(os.path.join(SCRIPT_DIR, mod['src']), 'r', encoding='utf-8') as fh:
            html = fh.read()
        for th, vs in SUITE_THEME_VARS.items():
            for var, val in vs.items():
                if var in ('--f-ui', '--f-stencil'):
                    pat = re.escape(var) + r'\s*:\s*' + re.escape(val)
                elif len({SUITE_THEME_VARS[x][var] for x in SUITE_THEME_VARS}) == 1:
                    pat = r'(?::root|html)\s*\{[^}]*?' + re.escape(var) + r'\s*:\s*' + re.escape(val) + r'\s*[;}]'
                else:
                    pat = r'\[data-theme="' + th + r'"\]\s*\{[^}]*?' + re.escape(var) + r'\s*:\s*' + re.escape(val) + r'\s*[;}]'
                if not re.search(pat, html, re.I):
                    raise SystemExit(f"[ERREUR] {mod['src']} : {var} n'a pas la valeur {val} au thème {th} (la fenêtre du nom et le toast du shell l'ont) — build arrêté")
    print('  [OK] couleurs de la fenêtre du nom et du toast : celles des six outils, aux quatre thèmes')


# Les textes de l'exemple (accueil et cinq outils) : une seule table, la même en FR et en EN ; les modules en portent chacun la leur, le build les compare à celle-ci
EX_BTN_TIP = {'fr': 'Charger l’exemple STEPPE WIND', 'en': 'Load the STEPPE WIND example'}
EX_BTN_LABEL = {'fr': 'Exemple', 'en': 'Example'}
EX_MENU = {'mc': 'Mission Commander — Briefing Generator, Recon Station',
           'fl': 'Flight Leader — Route Planner, Datacard Generator, Flight Configurator'}
EX_TOAST = {'mc': {'fr': 'Exemple STEPPE WIND chargé : Mission Commander', 'en': 'STEPPE WIND example loaded: Mission Commander'},
            'fl': {'fr': 'Exemple STEPPE WIND chargé : Flight Leader', 'en': 'STEPPE WIND example loaded: Flight Leader'}}
EX_TOOLS = {'bg': 'mc', 'rs': 'mc', 'rp': 'fl', 'dg': 'fl', 'fc': 'fl'}
WORK_FORMAT = 'dcs-mission-plan-work-v1'


def read_suite_examples():
    """Les deux fichiers d'exemple (samples/example_work_fr.json, _en.json), lus tels quels. Rend {fr: objet, en: objet}. Les contrôles sont ceux de check_suite_examples()."""
    out = {}
    for lang in ('fr', 'en'):
        path = os.path.join(SCRIPT_DIR, 'samples', 'example_work_%s.json' % lang)
        if not os.path.isfile(path):
            raise SystemExit(f"[ERREUR] Entrée manquante : {path} — build arrêté")
        with open(path, 'r', encoding='utf-8') as fh:
            try:
                out[lang] = json.load(fh)
            except ValueError as exc:
                raise SystemExit(f"[ERREUR] samples/example_work_{lang}.json illisible ({exc}) — build arrêté")
    return out


def check_suite_examples(ex, group_keys):
    """Les fichiers d'exemple : le format du fichier de travail, le théâtre Syria, les mêmes clés en FR et en EN, chaque clé dans un groupe, chaque valeur une chaîne qui se lit en JSON.
    group_keys : {groupe: [clés]}. Sinon le build s'arrête, en nommant le fichier et la clé."""
    in_group = {k for ks in group_keys.values() for k in ks}
    for lang in ('fr', 'en'):
        f, o = 'samples/example_work_%s.json' % lang, ex[lang]
        if not isinstance(o, dict) or o.get('format') != WORK_FORMAT:
            raise SystemExit(f"[ERREUR] {f} : format attendu {WORK_FORMAT} — build arrêté")
        if o.get('theatre') != 'Syria':
            raise SystemExit(f"[ERREUR] {f} : theatre attendu Syria ({o.get('theatre')!r}) — build arrêté")
        if not isinstance(o.get('keys'), dict) or not o['keys']:
            raise SystemExit(f"[ERREUR] {f} : keys absent ou vide — build arrêté")
        for k, v in o['keys'].items():
            if k not in in_group:
                raise SystemExit(f"[ERREUR] {f} : la clé {k} n'est d'aucun groupe — build arrêté")
            if not isinstance(v, str):
                raise SystemExit(f"[ERREUR] {f} : la valeur de {k} n'est pas une chaîne — build arrêté")
            try:
                json.loads(v)
            except ValueError:
                raise SystemExit(f"[ERREUR] {f} : la valeur de {k} ne se lit pas en JSON — build arrêté")
    if sorted(ex['fr']['keys']) != sorted(ex['en']['keys']):
        raise SystemExit("[ERREUR] les fichiers d'exemple FR et EN n'ont pas les mêmes clés — build arrêté")
    # Les presets d'emport sont personnels : le fc_state_v1 d'un exemple ne porte pas de « mine »
    for lang in ('fr', 'en'):
        fc = ex[lang]['keys'].get('fc_state_v1')
        if fc is not None and 'mine' in json.loads(fc):
            raise SystemExit("[ERREUR] samples/example_work_%s.json : fc_state_v1 porte « mine » (les presets ne sont pas dans un exemple) — build arrêté" % lang)


def check_example_tooltips():
    """Le menu Exemple ▾ de chaque outil : le bouton porte, dans chaque langue, l'infobulle de la table (EX_BTN_TIP), son libellé (EX_BTN_LABEL) et ouvre un menu à deux lignes (EX_MENU, dans cet ordre) ;
    chaque ligne appelle MP_WORK_EXAMPLE('mc') et ('fl') ; le build compare au HTML de chaque outil. Les textes sont écrits en \\u2019 / \\u2014 dans l'outil qui les met en échappement."""
    def forms(txt):
        return {txt, txt.replace('’', '\\u2019').replace('—', '\\u2014')}
    for mid in EX_TOOLS:
        src = next(m['src'] for m in MODULES if m['id'] == mid)
        with open(os.path.join(SCRIPT_DIR, src), 'r', encoding='utf-8') as fh:
            html = fh.read()
        for lang in ('fr', 'en'):
            for what, want in (('infobulle', EX_BTN_TIP[lang]), ('libellé', EX_BTN_LABEL[lang])) + tuple(('ligne ' + g, EX_MENU[g]) for g in ('mc', 'fl')):
                n = sum(html.count(w) for w in forms(want))
                if n < 1 or (what.startswith('ligne') and n < 2):
                    raise SystemExit(f"[ERREUR] {src} : {what} du menu Exemple ({lang}) absent ou pas dans les deux langues : « {want} » — build arrêté")
        if 'MP_WORK_EXAMPLE(g)' not in html or 'k => workExample(k)' not in html:
            raise SystemExit(f"[ERREUR] {src} : le menu Exemple n'appelle pas MP_WORK_EXAMPLE par groupe — build arrêté")
        if html.count("{ k: 'mc', label: t(") < 1 or html.count("{ k: 'fl', label: t(") < 1 or html.index("k: 'mc'") > html.index("k: 'fl'"):
            raise SystemExit(f"[ERREUR] {src} : les deux lignes du menu Exemple ne sont pas, dans cet ordre, mc puis fl — build arrêté")
        if 'btn-example' not in html or 'aria-haspopup="menu"' not in html:
            raise SystemExit(f"[ERREUR] {src} : le bouton Exemple n'est pas un menu — build arrêté")


def encode_file_b64(path):
    abs_path = os.path.join(SCRIPT_DIR, path)
    if not os.path.isfile(abs_path):
        raise SystemExit(f"[ERREUR] Entrée manquante : {abs_path}")
    with open(abs_path, 'rb') as f:
        return base64.b64encode(f.read()).decode('ascii')


def encode_module_b64(path):
    abs_path = os.path.join(SCRIPT_DIR, path)
    if not os.path.isfile(abs_path):
        raise SystemExit(f"[ERREUR] Entrée manquante : {abs_path} (lancer d'abord les builds de modules)")
    with open(abs_path, 'r', encoding='utf-8') as fh:
        html = fh.read()
    return base64.b64encode(html.encode('utf-8')).decode('ascii')


def build_module_html_js(modules):
    """N'encode que les modules 'active'."""
    lines = ['const MODULE_HTML = {']
    active = [m for m in modules if m['status'] == 'active']
    for i, mod in enumerate(active):
        b64 = encode_module_b64(mod['src'])
        if b64 is None:
            print(f'  [WARN] Source introuvable : {mod["src"]} — module {mod["id"]} désactivé', file=sys.stderr)
            b64 = ''
        comma = ',' if i < len(active) - 1 else ''
        lines.append(f'  {mod["id"]}: "{b64}"{comma}')
        print(f'  [OK] Module {mod["id"]} — {len(b64)//1024} Ko base64 (UTF-8)')
    lines.append('};')
    return '\n'.join(lines)


def build_tile_uris(modules):
    """Encode les tuiles des modules qui ont une carte (le Field Manual n'en a pas : tile None)."""
    uris = {}
    for mod in modules:
        if not mod['tile']:
            continue
        b64 = encode_file_b64(mod['tile'])
        if b64 is None:
            print(f'  [WARN] Image tuile introuvable : {mod["tile"]} — placeholder utilisé', file=sys.stderr)
            uris[mod['id']] = ''
        else:
            uris[mod['id']] = f'data:image/webp;base64,{b64}'
            print(f'  [OK] Tuile {mod["id"]} — {len(b64)//1024} Ko base64')
    return uris


def build_html(module_html_js, tile_uris, suite_examples_js):
    MESSAGES_CSS = build_messages_css()          # le toast : la feuille de messages_block.py, telle quelle (le shell parle par le même toast que les outils)
    UI_CSS = build_ui_css()                      # la feuille de ui_block.py, telle quelle : la fenêtre du nom est une .ui-modal (le shell ne reçoit pas le script de ui_block)
    SUITE_CSS = build_suite_file_css()           # les couleurs de ces deux feuilles, posées sur la fenêtre du nom et sur #toast
    MESSAGES_JS = build_messages_block()
    SUITE_JS = build_suite_file_block()
    SUITE_HTML = build_suite_file_html()
    tile_hq = tile_uris.get('hq', '')
    tile_bg = tile_uris.get('bg', '')
    tile_rs = tile_uris.get('rs', '')
    tile_rp = tile_uris.get('rp', '')
    tile_dg = tile_uris.get('dg', '')
    tile_fc = tile_uris.get('fc', '')

    return f'''<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, interactive-widget=resizes-content">
<title>DCS Mission Plan</title>
<style>
/* ============================================================
   DCS MISSION PLAN — DA v4 (shell)
   Landing « Mur de situation » — 4 thèmes
   ============================================================ */
@font-face{{ font-family:'Oswald'; font-weight:500; font-display:swap; src:url('data:font/woff2;base64,{A["OSWALD_500"]}') format('woff2'); }}
@font-face{{ font-family:'Oswald'; font-weight:700; font-display:swap; src:url('data:font/woff2;base64,{A["OSWALD_700"]}') format('woff2'); }}
@font-face{{ font-family:'Stardos Stencil'; font-weight:400; font-display:swap; src:url('data:font/woff2;base64,{A["STARDOS_400"]}') format('woff2'); }}
@font-face{{ font-family:'Stardos Stencil'; font-weight:700; font-display:swap; src:url('data:font/woff2;base64,{A["STARDOS_700"]}') format('woff2'); }}
@font-face{{ font-family:'Roboto Mono'; font-weight:400; font-display:swap; src:url('data:font/woff2;base64,{A["ROBOTO_MONO_400"]}') format('woff2'); }}
:root{{
  --paper:#d8c9a5; --paper-edge:#8a7a52; --ink:#1f1c16; --ink-2:#463f30;
  --accent:#a98a4e; --olive:#4a5230; --stamp:#a83524; --amber:#c0892a;
  --board:#2a2417; --board-2:#1a1610; --lamp:rgba(255,228,168,.22);
  --line:rgba(192,137,42,.30); --grain:.08; --scan:0; --rot:-2.6deg; --rad:2px;
  --f-disp:'Roboto Mono','Courier New',monospace;
  --f-sten:'Stardos Stencil','Impact',sans-serif;
  --f-ui:'Oswald','Arial Narrow',sans-serif;
  --f-body:'Oswald','Arial Narrow',sans-serif;
  --f-mono:'Roboto Mono','Courier New',monospace;
  --a-hq:#4FB286; --a-bg:#c0892a; --a-rp:#7ac97a; --a-dg:#8fb0c0; --a-rs:#c95a9c; --a-fc:#d0784a; --a-fm:#7E8FA6;
}}
[data-theme="cw-nato"]{{ --paper:#d8c9a5; --paper-edge:#8a7a52; --ink:#1f1c16; --ink-2:#463f30;
  --accent:#a98a4e; --olive:#4a5230; --stamp:#a83524; --rust:#7a3a20;
  --board:#2a2417; --board-2:#1a1610; --lamp:rgba(255,228,168,.22);
  --line:rgba(192,137,42,.30); --grain:.08; --scan:0; --rot:-2.6deg; --rad:2px; }}
[data-theme="cw-soviet"]{{ --paper:#d8c479; --paper-edge:#8a7a30; --ink:#1f1c16; --ink-2:#463f30;
  --accent:#c9b35c; --olive:#2a3a5a; --stamp:#841e1e; --rust:#5e1414;
  --board:#231d12; --board-2:#15110a; --lamp:rgba(255,224,150,.20);
  --line:rgba(232,214,144,.28); --grain:.09; --scan:0; --rot:-4deg; --rad:1px; }}
[data-theme="modern-nato"]{{ --paper:#e8e3d8; --paper-edge:#948c7c; --ink:#15181c; --ink-2:#3a4048;
  --accent:#7a8a98; --olive:#2a3038; --stamp:#1a1a1a; --rust:#2a2a2a;
  --board:#10141a; --board-2:#080b0f; --lamp:rgba(170,200,225,.14);
  --line:rgba(122,138,152,.30); --grain:.03; --scan:.06; --rot:-.8deg; --rad:6px; }}
[data-theme="modern-east"]{{ --paper:#cdc6b8; --paper-edge:#7a7466; --ink:#1a1610; --ink-2:#3d3024;
  --accent:#8a7c5e; --olive:#3d3024; --stamp:#7a2424; --rust:#5a1a1a;
  --board:#16110b; --board-2:#0c0805; --lamp:rgba(220,190,150,.14);
  --line:rgba(160,120,80,.26); --grain:.05; --scan:.04; --rot:-1.4deg; --rad:4px; }}

*{{box-sizing:border-box;margin:0;padding:0;}}
button:focus-visible, select:focus-visible, input:focus-visible, textarea:focus-visible, summary:focus-visible,
a[href]:focus-visible, [tabindex]:focus-visible, [role="button"]:focus-visible {{
  outline: 2px solid var(--amber); outline-offset: 2px;
}}
html,body{{height:100%;}}
body{{font-family:var(--f-body); background:var(--board-2); color:var(--paper); min-height:100vh; overflow-x:hidden; transition:background .5s ease;}}
.app{{position:relative; z-index:3; min-height:100vh; display:flex; flex-direction:column;}}

/* ===== RAIL ===== */
.rail{{display:flex; align-items:center; gap:14px; flex-wrap:wrap; padding:11px 22px; border-bottom:1px solid var(--line);
  position:relative; z-index:6; background:linear-gradient(180deg, rgba(0,0,0,.6), rgba(0,0,0,.18)); backdrop-filter:blur(2px);}}
.plate{{display:flex; align-items:baseline; gap:9px; padding:5px 11px; border:1px solid var(--line); border-radius:var(--rad);
  background:linear-gradient(180deg, rgba(255,255,255,.06), rgba(0,0,0,.3));}}
.plate .mark{{font-family:var(--f-sten); font-size:16px; letter-spacing:.05em; color:var(--amber);}}
.plate .sub{{font-family:var(--f-mono); font-size:10px; letter-spacing:.24em; color:var(--accent); text-transform:uppercase;}}
.rail .spacer{{flex:1;}}
.ctrl{{display:flex; align-items:center; gap:8px;}}
.seg{{display:inline-flex; border:1px solid var(--line); border-radius:var(--rad); overflow:hidden;}}
.seg button{{font-family:var(--f-ui); font-weight:500; font-size:12px; letter-spacing:.06em; text-transform:uppercase; background:rgba(0,0,0,.4);
  color:var(--accent); border:none; padding:7px 13px; cursor:pointer;}}
.seg button + button{{border-left:1px solid var(--line);}}
.seg button.on{{background:var(--amber); color:#15120c;}}
.theme-sel{{font-family:var(--f-ui); font-weight:500; font-size:12px; letter-spacing:.05em; text-transform:uppercase; background:rgba(0,0,0,.45);
  color:var(--amber); border:1px solid var(--line); padding:7px 11px; border-radius:var(--rad); cursor:pointer; outline:none;}}

/* ---------- Liste du thème au thème de la landing (lot mp-ui-listes) ----------
   Le <select> reste dans la page, masqué ; un bouton de mêmes classes prend sa place (voir initToolbarMenus). */
select[data-tbm-src] {{ display: none !important; }}
.tbm-trigger {{ position: relative; display: inline-block; text-align: left; white-space: nowrap; }}
.tbm-lbl {{ display: block; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; text-align: left; padding: 4px 16px 4px 4px; margin: -3.25px 0 -2.75px; pointer-events: none; }}
.tbm-lbl::after {{ content: attr(data-w); display: block; height: 0; overflow: hidden; visibility: hidden; white-space: pre; }}
@supports (width: calc-size(max-content, round(up, size, 1px))) {{ .tbm-lbl::after {{ width: calc-size(max-content, round(up, size, 1px)); }} }}
.tbm-trigger::after {{ content: ''; position: absolute; right: 3px; top: 50%; width: 10px; height: 6px; margin-top: -3px; pointer-events: none;
  background: currentColor; -webkit-mask: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 10 6'><path d='M1 1l4 4 4-4' fill='none' stroke='black' stroke-width='2'/></svg>") center / 10px 6px no-repeat;
  mask: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 10 6'><path d='M1 1l4 4 4-4' fill='none' stroke='black' stroke-width='2'/></svg>") center / 10px 6px no-repeat; }}
.tbm-trigger-open {{ border-color: var(--amber) !important; }}
.tbm-panel {{
  position: fixed; z-index: 5000; min-width: 180px; max-width: min(340px, calc(100vw - 16px));
  max-height: min(62vh, 440px); overflow-y: auto; overscroll-behavior: contain;
  background: linear-gradient(180deg, var(--board) 0%, var(--board-2) 100%);
  border: 1px solid var(--line); border-top: 3px solid var(--amber); border-radius: var(--rad);
  box-shadow: 0 12px 28px rgba(0,0,0,.55), 0 2px 0 rgba(0,0,0,.35);
  padding: 4px 0; margin: 0; list-style: none; scrollbar-width: thin; scrollbar-color: var(--line) transparent;
  transform-origin: top left; animation: tbm-in .12s ease-out;
}}
@keyframes tbm-in {{ from {{ opacity: 0; transform: translateY(-4px); }} to {{ opacity: 1; transform: none; }} }}
.tbm-head {{
  font-family: var(--f-ui); font-weight: 500; font-size: 10px; letter-spacing: 1.8px; text-transform: uppercase;
  color: var(--accent); padding: 8px 14px 6px; border-bottom: 1px solid var(--line); margin-bottom: 2px;
}}
.tbm-opt {{
  position: relative; display: flex; align-items: center; gap: 10px; min-height: 44px; padding: 0 16px 0 18px;
  font-family: var(--f-ui); font-weight: 500; font-size: 13px; letter-spacing: 1.3px; text-transform: uppercase;
  color: var(--paper); cursor: pointer; white-space: nowrap; user-select: none;
}}
.tbm-opt + .tbm-opt {{ border-top: 1px solid var(--line); }}
.tbm-opt .tbm-mark {{ width: 7px; height: 7px; flex: none; transform: rotate(45deg); border: 1px solid var(--accent); }}
.tbm-opt.active, .tbm-opt:hover {{ background: rgba(255,255,255,.06); color: var(--amber); }}
.tbm-opt.active .tbm-mark, .tbm-opt:hover .tbm-mark {{ border-color: var(--amber); }}
.tbm-opt[aria-selected="true"] {{ color: var(--amber); }}
.tbm-opt[aria-selected="true"]::before {{ content: ''; position: absolute; left: 0; top: 6px; bottom: 6px; width: 3px; background: var(--amber); }}
.tbm-opt[aria-selected="true"] .tbm-mark {{ background: var(--amber); border-color: var(--amber); }}
.tbm-opt[aria-disabled="true"] {{ color: var(--accent); cursor: not-allowed; background: none; }}
.tbm-opt[aria-disabled="true"] .tbm-mark {{ border-style: dashed; border-color: var(--accent); background: none; }}
.tbm-opt[aria-disabled="true"] .tbm-note {{ color: var(--accent); font-size: 10px; letter-spacing: 1px; margin-left: auto; padding-left: 14px; }}
@media (prefers-reduced-motion: reduce) {{ .tbm-panel {{ animation: none; }} }}
@media print {{ .tbm-panel {{ display: none; }} }}

.flag{{font-size:16px; background:rgba(0,0,0,.45); border:1px solid var(--line); width:38px; height:34px; border-radius:var(--rad); cursor:pointer; color:var(--amber); display:inline-flex; align-items:center; justify-content:center; padding:0;}}
.flag svg{{display:block;}}
.classif{{font-family:var(--f-mono); font-size:10px; letter-spacing:.16em; text-transform:uppercase; color:var(--stamp);
  border:1px solid var(--stamp); padding:5px 9px; border-radius:var(--rad); opacity:.85;}}

.atmos{{position:fixed; inset:0; z-index:0; pointer-events:none;}}
.atmos .grain{{position:absolute; inset:0; opacity:var(--grain); mix-blend-mode:overlay;
  background-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='160' height='160'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='2'/></filter><rect width='100%25' height='100%25' filter='url(%23n)'/></svg>");}}
.atmos .scan{{position:absolute; inset:0; opacity:var(--scan); background:repeating-linear-gradient(to bottom, rgba(255,255,255,.5) 0 1px, transparent 1px 3px);}}

/* ============ DIRECTION WALL ============ */
.board{{position:relative; flex:1; padding:24px 26px 56px; overflow:hidden; isolation:isolate;}}
.board::before{{content:''; position:absolute; inset:0; z-index:-1; transition:background .5s ease;
  background:
    url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='400' height='400'><filter id='t'><feTurbulence type='fractalNoise' baseFrequency='0.014' numOctaves='2' seed='4'/></filter><rect width='100%25' height='100%25' filter='url(%23t)' opacity='0.4'/></svg>"),
    radial-gradient(58% 44% at 50% 20%, var(--lamp), transparent 62%),
    radial-gradient(150% 130% at 50% 120%, transparent 30%, rgba(0,0,0,.82)),
    linear-gradient(160deg, var(--board), var(--board-2));
  background-size:420px 420px, auto, auto, auto;
  background-blend-mode:overlay, normal, normal, normal;}}
.board::after{{content:''; position:absolute; inset:0; z-index:-1; opacity:.09; color:var(--accent);
  background-image:linear-gradient(var(--accent) 1px, transparent 1px), linear-gradient(90deg, var(--accent) 1px, transparent 1px);
  background-size:46px 46px; -webkit-mask:radial-gradient(78% 70% at 50% 34%, #000, transparent 88%); mask:radial-gradient(78% 70% at 50% 34%, #000, transparent 88%);}}

.wall-head{{position:relative; z-index:2; max-width:1200px; margin:0 auto 44px; width:100%; display:flex; align-items:flex-end; gap:20px; flex-wrap:wrap;}}
.tab{{position:relative; background:var(--paper); color:var(--ink); padding:13px 22px 15px; border-radius:6px 6px 0 0;
  box-shadow:0 10px 26px rgba(0,0,0,.5); transform:rotate(-1deg); border:1px solid var(--paper-edge); border-bottom:none;}}
.tab .ribbon{{font-family:var(--f-mono); font-size:10px; letter-spacing:.26em; color:var(--ink-2); text-transform:uppercase;}}
.tab h1{{font-family:var(--f-sten); font-size:clamp(28px,4.8vw,48px); line-height:.9; letter-spacing:.02em; color:var(--ink); margin-top:4px;}}
.tab h1 .x{{color:var(--stamp);}}
.note{{display:flex; border:1px solid var(--line); border-radius:var(--rad); overflow:hidden; background:rgba(0,0,0,.32); transform:rotate(.6deg);}}
.note .cell{{padding:8px 13px; border-right:1px solid var(--line);}} .note .cell:last-child{{border-right:none;}}
.note .k{{font-family:var(--f-mono); font-size:10px; letter-spacing:.18em; color:var(--accent); text-transform:uppercase; display:block;}}
.note .v{{font-family:var(--f-ui); font-weight:500; font-size:13px; color:var(--amber);}}

.wall-stage{{position:relative; z-index:1; max-width:1200px; margin:0 auto; width:100%; display:flex; flex-direction:column; gap:36px;}}
.active-row{{display:grid; grid-template-columns:1fr 1fr 1fr; gap:26px;}}
.soon-row{{display:grid; grid-template-columns:1fr 1fr; gap:26px; max-width:760px;}}

.print{{position:relative; border:1px solid var(--paper-edge); border-radius:var(--rad); padding:11px 11px 0;
  background:linear-gradient(158deg, color-mix(in srgb,var(--paper) 96%, #fff 4%), color-mix(in srgb,var(--paper) 80%, #1a1208 20%));
  box-shadow:0 18px 40px rgba(0,0,0,.6), inset 0 1px 0 rgba(255,255,255,.18); transition:transform .4s cubic-bezier(.2,.75,.2,1), box-shadow .4s;}}
.print::after{{content:''; position:absolute; inset:0; z-index:3; pointer-events:none; border-radius:inherit; mix-blend-mode:multiply; opacity:.7;
  box-shadow:inset 0 0 42px rgba(52,34,12,.5), inset 0 0 8px rgba(0,0,0,.34);
  background:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='220' height='220'><filter id='p'><feTurbulence type='fractalNoise' baseFrequency='0.55' numOctaves='3'/></filter><rect width='100%25' height='100%25' filter='url(%23p)' opacity='0.75'/></svg>"); background-size:200px 200px;}}
.print::before{{content:''; position:absolute; inset:0; z-index:3; pointer-events:none; border-radius:inherit; mix-blend-mode:multiply; opacity:.85;
  background:radial-gradient(circle at 88% 92%, rgba(96,64,30,.5), transparent 15%), radial-gradient(circle at 10% 90%, rgba(96,64,30,.4), transparent 13%);}}
#card-bg::before{{background:radial-gradient(circle at 93% 94%, rgba(96,64,30,.5), transparent 14%);}}
#card-rs::before{{background:radial-gradient(circle at 8% 90%, rgba(96,64,30,.5), transparent 15%);}}
.soon-row .print:nth-child(1)::before{{background:
  radial-gradient(circle at 94% 88%, rgba(96,64,30,.54), transparent 18%), radial-gradient(circle at 10% 10%, rgba(80,52,24,.42), transparent 12%);}}
[data-theme^="modern"] .print::after{{opacity:.32;}}
[data-theme^="modern"] .print::before{{opacity:.35;}}
.pin{{position:absolute; width:15px; height:15px; border-radius:50%; z-index:6;
  background:radial-gradient(circle at 35% 30%, #ff8f7e, var(--stamp)); box-shadow:0 4px 7px rgba(0,0,0,.55), inset 0 -2px 3px rgba(0,0,0,.35);}}
.pin.tl{{top:-7px; left:18px;}} .pin.tr{{top:-7px; right:18px;}}
.tape{{position:absolute; top:-12px; left:50%; transform:translateX(-50%) rotate(-3deg); width:118px; height:25px; z-index:5;
  background:linear-gradient(180deg, rgba(230,225,200,.55), rgba(200,195,170,.42)); border:1px solid rgba(255,255,255,.22); box-shadow:0 2px 5px rgba(0,0,0,.3);}}
.shot{{position:relative; border-radius:1px; overflow:hidden; background:var(--board-2) center/cover no-repeat;}}
.shot .tagchip{{position:absolute; top:9px; left:9px; font-family:var(--f-mono); font-size:10px; letter-spacing:.14em; text-transform:uppercase;
  color:#f3ecd9; background:rgba(0,0,0,.6); padding:3px 8px; border:1px solid rgba(255,255,255,.18);}}
.caption{{padding:11px 8px 13px; color:var(--ink);}}
.cap-row{{display:flex; align-items:center; gap:9px;}}
.logo{{font-family:var(--f-mono); font-weight:400; font-size:12px; color:#15120c; padding:4px 7px; border-radius:3px; letter-spacing:.05em;}}
.ptitle{{font-family:var(--f-ui); font-size:16px; font-weight:700; color:var(--ink);}}
.pver{{margin-left:auto; font-family:var(--f-mono); font-size:10px; color:var(--ink-2); border:1px solid var(--paper-edge); padding:1px 6px; border-radius:2px;}}
.pdesc{{font-family:var(--f-body); font-weight:500; font-size:13px; color:var(--ink-2); line-height:1.4; margin-top:6px;
  display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden;}}
.pstatus{{display:flex; align-items:center; gap:7px; margin-top:8px; font-family:var(--f-mono); font-size:10px; letter-spacing:.12em; text-transform:uppercase; color:var(--olive);}}
.pstatus .dot{{width:7px; height:7px; border-radius:50%; background:#4f8a3a; box-shadow:0 0 8px #4f8a3a;}}

/* ── Cartes ACTIVES (dossiers ouverts) : BG + Recon, traitement identique ── */
.print.active{{cursor:pointer;}}
.print.active .shot{{height:130px; cursor:pointer;}}
#card-hq .shot{{background-image:url("{tile_hq}");}}
#card-hq::before{{background:radial-gradient(circle at 12% 8%, rgba(96,64,30,.5), transparent 14%);}}
#card-bg .shot{{background-image:url("{tile_bg}");}}
#card-rs .shot{{background-image:url("{tile_rs}");}}
#card-fc .shot{{background-image:url("{tile_fc}");}}
#card-fc::before{{background:radial-gradient(circle at 92% 90%, rgba(96,64,30,.5), transparent 15%);}}
#card-dg .shot{{background-image:url("{tile_dg}");}}
#card-dg::before{{background:radial-gradient(circle at 10% 92%, rgba(96,64,30,.5), transparent 15%);}}
#card-rp .shot{{background-image:url("{tile_rp}");}}
#card-rp::before{{background:
  radial-gradient(circle at 94% 88%, rgba(96,64,30,.54), transparent 18%), radial-gradient(circle at 10% 10%, rgba(80,52,24,.42), transparent 12%);}}
/* Chaque carte a son angle au repos, son angle au survol et sa durée de bascule, visés par son id (et non par sa position) : l'ordre des cartes peut changer. */
.active-row .print[id="card-hq"]{{transform:rotate(-1.8deg); transition:transform .42s cubic-bezier(.2,.75,.2,1), box-shadow .42s;}}
.active-row .print[id="card-bg"]{{transform:rotate(1.1deg); transition:transform .36s cubic-bezier(.2,.75,.2,1), box-shadow .36s;}}
.active-row .print[id="card-dg"]{{transform:rotate(1.6deg); transition:transform .46s cubic-bezier(.2,.75,.2,1), box-shadow .46s;}}
.active-row .print[id="card-rp"]{{transform:rotate(-0.9deg); transition:transform .38s cubic-bezier(.2,.75,.2,1), box-shadow .38s;}}
.active-row .print[id="card-rs"]{{transform:rotate(0.6deg); transition:transform .44s cubic-bezier(.2,.75,.2,1), box-shadow .44s;}}
.active-row .print[id="card-fc"]{{transform:rotate(-1.2deg); transition:transform .4s cubic-bezier(.2,.75,.2,1), box-shadow .4s;}}
.print.active:hover{{transform:rotate(0) translateY(-7px); cursor:pointer; box-shadow:0 30px 64px rgba(0,0,0,.6), 0 0 0 2px var(--card-accent);}}
.active-row .print[id="card-hq"]:hover{{transform:rotate(-0.7deg) translateY(-7px);}}
.active-row .print[id="card-bg"]:hover{{transform:rotate(0.3deg) translateY(-7px);}}
.active-row .print[id="card-dg"]:hover{{transform:rotate(0.6deg) translateY(-7px);}}
.active-row .print[id="card-rp"]:hover{{transform:rotate(-0.2deg) translateY(-7px);}}
.active-row .print[id="card-rs"]:hover{{transform:rotate(-0.4deg) translateY(-7px);}}
.active-row .print[id="card-fc"]:hover{{transform:rotate(-0.4deg) translateY(-7px);}}
.cta{{margin:0 8px 10px; display:inline-block; font-family:var(--f-ui); font-weight:500; font-size:12px; letter-spacing:.08em; text-transform:uppercase;
  color:#15120c; background:var(--card-accent); border:1px solid var(--paper-edge); padding:6px 12px; border-radius:var(--rad);}}
.print.active:hover .cta{{filter:brightness(1.12);}}

/* sealed (à venir) — plus petites, voilées + tampon */
.soon-row .print:nth-child(1){{transform:rotate(-3deg) translate(2px,0);}}
.print.sealed .shot{{height:150px;}}
.print.sealed .shot::after{{content:''; position:absolute; inset:0; background:rgba(10,8,6,.32);}}
.avenir{{position:absolute; top:10px; right:10px; z-index:4; font-family:var(--f-disp); font-size:11px; letter-spacing:.16em; text-transform:uppercase;
  color:var(--stamp); border:2px solid var(--stamp); padding:3px 8px; background:rgba(0,0,0,.4); transform:rotate(-6deg);}}
[data-theme="modern-nato"] .avenir,[data-theme="modern-east"] .avenir{{border-width:1.5px; font-family:var(--f-mono); font-size:10px;}}
.print.sealed .caption{{padding:9px 8px 11px;}}
.print.sealed .ptitle{{font-size:16px; color:var(--ink-2);}}

.bigstamp{{position:absolute; top:14px; right:30px; z-index:5; transform:rotate(var(--rot)); font-family:var(--f-disp); color:var(--stamp);
  border:3px double var(--stamp); padding:9px 17px; font-size:16px; letter-spacing:.16em; text-transform:uppercase; opacity:.7; background:rgba(0,0,0,.14); border-radius:var(--rad);}}
[data-theme="modern-nato"] .classif,[data-theme="modern-nato"] .bigstamp{{color:#8e9aa6; border-color:#5f6b76;}}
[data-theme="modern-east"] .classif,[data-theme="modern-east"] .bigstamp{{color:#a4756c; border-color:#79554e;}}
[data-theme="modern-nato"] .bigstamp,[data-theme="modern-east"] .bigstamp{{opacity:.5;}}
.soviet-star{{position:absolute; top:18px; left:30px; width:58px; height:58px; z-index:5; opacity:0; transition:opacity .4s;}}
[data-theme="cw-soviet"] .soviet-star{{opacity:.55;}}

/* ── Déco diégétique du panneau (objets posés/épinglés, pas d'abstrait) ── */
.props{{position:absolute; inset:0; z-index:0; pointer-events:none;}}
.props .tape-label{{position:absolute; left:30px; bottom:70px; transform:rotate(-4deg);
  font-family:var(--f-mono); font-size:10px; letter-spacing:.22em; text-transform:uppercase; color:rgba(22,16,10,.74);
  padding:8px 18px; background:linear-gradient(180deg, rgba(228,221,193,.46), rgba(198,191,163,.34)); box-shadow:0 2px 6px rgba(0,0,0,.32);}}
.props .tape-label::before,.props .tape-label::after{{content:''; position:absolute; top:0; bottom:0; width:8px; background:inherit; opacity:.85;}}
.props .tape-label::before{{left:-8px; clip-path:polygon(0 16%,100% 0,100% 100%,0 84%);}}
.props .tape-label::after{{right:-8px; clip-path:polygon(0 0,100% 16%,100% 84%,0 100%);}}
.props .imprint{{position:absolute; right:64px; bottom:118px; transform:rotate(-13deg); opacity:.17;
  font-family:var(--f-disp); font-size:13px; letter-spacing:.16em; text-transform:uppercase; color:var(--stamp);
  border:2px double var(--stamp); padding:8px 14px; border-radius:2px;}}
[data-theme="modern-nato"] .props .imprint{{color:#8e9aa6; border-color:#5f6b76;}}
[data-theme="modern-east"] .props .imprint{{color:#a4756c; border-color:#79554e;}}
.props .pin.s1{{position:absolute; top:96px; right:74px;}}
.props .pin.s2{{position:absolute; bottom:62px; left:228px;}}
.props .clip{{position:absolute; right:128px; top:118px; width:13px; height:32px; transform:rotate(26deg);
  border:2px solid #b9bcc0; border-radius:8px; box-shadow:0 2px 4px rgba(0,0,0,.45);}}
.props .clip::before{{content:''; position:absolute; left:2px; right:2px; top:3px; bottom:7px; border:2px solid #a9acb0; border-bottom:none; border-radius:6px 6px 0 0;}}
@media(max-width:1024px){{ .props{{display:none;}} }}

/* ===== CRÉDIT (l'attribution de la licence, à l'accueil seulement) ===== */
#credits{{margin-top:24px; padding:0 24px 14px; text-align:center; font-family:var(--f-mono); font-size:11px; line-height:1.55; color:var(--accent); position:relative; z-index:6;
  overflow-wrap:anywhere;}}
#credits p + p{{margin-top:3px;}}
#credits a{{color:inherit; text-decoration:underline;}}

/* ===== PIED ===== */
.foot{{padding:13px 24px; border-top:1px solid var(--line); display:flex; gap:14px; align-items:center; flex-wrap:wrap; position:relative; z-index:6;
  font-family:var(--f-mono); font-size:10px; letter-spacing:.16em; color:var(--accent); text-transform:uppercase;}}
.foot .dot{{opacity:.5;}} .foot .right{{margin-left:auto; color:var(--amber);}}

/* Animations — translate, jamais transform (cf. DESIGN §6.1) */
.reveal{{opacity:0; translate:0 12px; animation:rise .65s cubic-bezier(.2,.7,.2,1) forwards;}}
@keyframes rise{{to{{opacity:1; translate:0 0;}}}}
.d1{{animation-delay:.05s}}.d2{{animation-delay:.16s}}.d3{{animation-delay:.3s}}.d4{{animation-delay:.42s}}.d5{{animation-delay:.54s}}.d6{{animation-delay:.66s}}

/* ===== VUE MODULE ===== */
#landing{{display:flex; flex-direction:column; flex:1;}}
#module-view{{display:none; position:fixed; inset:0; z-index:200;}}
#module-view.active{{display:block;}}
#module-view iframe{{width:100%; height:100%; border:none; display:block;}}
#module-loading{{position:fixed; inset:0; z-index:201; background:rgba(10,8,6,.92);
  display:flex; align-items:center; justify-content:center;
  font-family:var(--f-mono); font-size:13px; letter-spacing:.18em; color:var(--amber); text-transform:uppercase;}}
#module-loading.hidden{{display:none;}}

@media(max-width:900px){{ .active-row,.soon-row{{grid-template-columns:1fr;}} }}
@media(max-width:768px){{
  .bigstamp,.soviet-star{{display:none;}}
}}
{MESSAGES_CSS}{UI_CSS}{SUITE_CSS}{LANDING_CSS}{CONTRAST_CSS}</style>
</head>
<body data-theme="cw-nato">

<div class="atmos"><div class="grain"></div><div class="scan"></div></div>

<div id="landing">
<div class="app">

  <!-- RAIL -->
  <div class="rail reveal d1">
    <div class="plate"><span class="mark">DCS · MISSION PLAN</span></div>
    <div class="spacer"></div>
    <div class="ctrl">
      <button type="button" class="mp-railbtn" id="btn-work-open" data-i18n-title="work.open.tip" data-i18n-aria="work.open.tip" title="Ouvrir un travail de Mission Plan (JSON)" aria-label="Ouvrir un travail de Mission Plan (JSON)"><svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M3 7h6l2 2h10v10H3z"/></svg><span data-i18n="work.open.btn">Ouvrir…</span></button>
      <button type="button" class="mp-railbtn" id="btn-work-save" data-i18n-title="work.save.tip" data-i18n-aria="work.save.tip" title="Sauvegarder tout le travail de Mission Plan (JSON)" aria-label="Sauvegarder tout le travail de Mission Plan (JSON)"><svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M5 3h12l3 3v15H5z"/><path d="M8 3v6h8V3M8 21v-7h8v7"/></svg><span data-i18n="work.save.btn">Sauvegarder</span></button>
      <button type="button" class="mp-railbtn" id="btn-example" aria-haspopup="menu" aria-expanded="false" data-i18n-title="ex.tip" data-i18n-aria="ex.tip" title="Charger l’exemple STEPPE WIND" aria-label="Charger l’exemple STEPPE WIND"><svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="8" y1="13" x2="16" y2="13"/><line x1="8" y1="17" x2="16" y2="17"/></svg><span data-i18n="ex.btn">Exemple</span><svg class="mp-chev" viewBox="0 0 10 6" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M1 1l4 4 4-4"/></svg></button>
      <span class="mp-sep" aria-hidden="true"></span>
      <button type="button" class="mp-railbtn" id="btn-fm" data-i18n-title="fm.tip" data-i18n-aria="fm.tip" title="Le manuel de la suite" aria-label="Le manuel de la suite"><svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M4 4h7a3 3 0 0 1 3 3v13a2 2 0 0 0-2-2H4zM20 4h-6M20 4v14h-6"/></svg><span data-i18n="fm.btn">Field Manual</span></button>
      <select class="theme-sel" id="theme-sel" onchange="setTheme(this.value)" data-i18n-title="theme.sel" title="Thème">
        <option value="cw-nato" data-i18n="theme.cwnato">Cold War OTAN</option>
        <option value="cw-soviet" data-i18n="theme.cwsoviet">Cold War Soviétique</option>
        <option value="modern-nato" data-i18n="theme.modernnato">OTAN moderne</option>
        <option value="modern-east" data-i18n="theme.moderneast">Bloc Est moderne</option>
      </select>
      <button class="flag" id="flag-btn" title="Passer en anglais" aria-label="Passer en anglais"><svg viewBox="0 0 20 14" width="22" height="15" xmlns="http://www.w3.org/2000/svg"><rect width="20" height="14" fill="#012169"/><path d="M0,0 L20,14 M20,0 L0,14" stroke="#fff" stroke-width="2.8"/><path d="M0,0 L20,14 M20,0 L0,14" stroke="#C8102E" stroke-width="1.6"/><rect x="8" width="4" height="14" fill="#fff"/><rect y="5" width="20" height="4" fill="#fff"/><rect x="9" width="2" height="14" fill="#C8102E"/><rect y="6" width="20" height="2" fill="#C8102E"/></svg></button>
      <span class="classif" id="classif">Classified // Eyes Only</span>
    </div>
  </div>

  <!-- ============ WALL ============ -->
  <div id="dir-wall" class="board">
    <svg class="soviet-star" viewBox="0 0 100 100"><polygon points="50,4 61,38 97,38 68,60 79,95 50,73 21,95 32,60 3,38 39,38" fill="var(--stamp)" stroke="var(--amber)" stroke-width="1.5"/></svg>

    <div class="props">
      <div class="tape-label">OPS · 06.2026</div>
      <div class="imprint">Nº 047 — 06.26</div>
      <span class="pin s1"></span>
      <span class="pin s2"></span>
      <span class="clip"></span>
    </div>

    <div class="bigstamp" id="bigstamp">Declassified</div>

    <div class="wall-head">
      <div class="tab reveal d2">
        <div class="ribbon" data-i18n="ribbon">// Suite de préparation opérationnelle</div>
        <h1>MISSION <span class="x">PLAN</span></h1>
      </div>
    </div>

    <div class="wall-stage">

      <!-- Modules actifs : dossiers ouverts, traitement identique, en deux cadres selon le rôle (aucun numéro).
           Mission Commander : HQ · Briefing Generator · Recon Station. Flight Leader : Route Planner · Datacard Generator · Flight Configurator.
           Le Field Manual n'a pas de carte : il s'ouvre par la barre du haut.
           RÈGLE : un module activé plus tard s'insère dans le cadre de son rôle (et dans MODULES, avant le Field Manual). -->
      <div class="mp-grp" id="grp-mc">
        <div class="mp-tab"><b>Mission Commander</b><small data-i18n="grp.mc.sub">prépare la mission</small></div>
        <div class="active-row">
          <div class="print active reveal d1" id="card-hq" style="--card-accent:var(--a-hq)" tabindex="0" role="button" aria-label="HQ">
            <span class="tape"></span><span class="pin tl"></span><span class="pin tr"></span>
            <div class="shot"></div>
            <div class="caption">
              <div class="cap-row">
                <span class="logo" style="background:var(--a-hq)">H·Q</span>
                <span class="ptitle">HQ</span>
                <span class="pver">v0.1.1</span>
              </div>
              <div class="pdesc" data-i18n="hq.desc">Poste de commandement — configuration Wing, identité escadrons, logos partagés avec tous les modules.</div>
              <div class="pstatus"><span class="dot"></span> <span data-i18n="status.op">Opérationnel</span></div>
            </div>
            <span class="cta" data-i18n="cta">▶ Ouvrir le dossier</span>
          </div>

          <div class="print active reveal d2" id="card-bg" style="--card-accent:var(--a-bg)" tabindex="0" role="button" aria-label="Briefing Generator">
            <span class="tape"></span><span class="pin tl"></span><span class="pin tr"></span>
            <div class="shot"></div>
            <div class="caption">
              <div class="cap-row">
                <span class="logo" style="background:var(--a-bg)">B·G</span>
                <span class="ptitle">Briefing Generator</span>
                <span class="pver">v2.6.0</span>
              </div>
              <div class="pdesc" data-i18n="bg.desc">Briefings complets — SITAC, plan radio, aérodromes, charts, annexes — export PDF prêt à partager.</div>
              <div class="pstatus"><span class="dot"></span> <span data-i18n="status.op">Opérationnel</span></div>
            </div>
            <span class="cta" data-i18n="cta">▶ Ouvrir le dossier</span>
          </div>

          <div class="print active reveal d3" id="card-rs" style="--card-accent:var(--a-rs)" tabindex="0" role="button" aria-label="Recon Station">
            <span class="tape"></span><span class="pin tl"></span><span class="pin tr"></span>
            <div class="shot"></div>
            <div class="caption">
              <div class="cap-row">
                <span class="logo" style="background:var(--a-rs)">R·S</span>
                <span class="ptitle">Recon Station</span>
                <span class="pver">v1.1.1</span>
              </div>
              <div class="pdesc" data-i18n="rs.desc">Transforme une capture en photo d'analyse de reconnaissance — niveaux de gris, annotations au doigt, export PNG pleine résolution.</div>
              <div class="pstatus"><span class="dot"></span> <span data-i18n="status.op">Opérationnel</span></div>
            </div>
            <span class="cta" data-i18n="cta">▶ Ouvrir le dossier</span>
          </div>
        </div>
      </div>

      <div class="mp-grp" id="grp-fl">
        <div class="mp-tab"><b>Flight Leader</b><small data-i18n="grp.fl.sub">prépare son vol</small></div>
        <div class="active-row">
          <div class="print active reveal d4" id="card-rp" style="--card-accent:var(--a-rp)" tabindex="0" role="button" aria-label="Route Planner">
            <span class="tape"></span><span class="pin tl"></span><span class="pin tr"></span>
            <div class="shot"></div>
            <div class="caption">
              <div class="cap-row">
                <span class="logo" style="background:var(--a-rp)">R·P</span>
                <span class="ptitle">Route Planner</span>
                <span class="pver">v1.13.1</span>
              </div>
              <div class="pdesc" data-i18n="rp.desc">Tracé de route sur carte — carte DCS, topographique ou satellite, grille MGRS, villes et aérodromes, recherche ; points de référence ; caps, distances, vitesse sol et minutage ; calques CombatFlite et dessin au doigt (zones, FLOT, couloirs, orbites, boîtes) ; MGRS et DMS, envoyés à la datacard ; import et export du Route Tool de DCS.</div>
              <div class="pstatus"><span class="dot"></span> <span data-i18n="status.op">Opérationnel</span></div>
            </div>
            <span class="cta" data-i18n="cta">▶ Ouvrir le dossier</span>
          </div>

          <div class="print active reveal d5" id="card-dg" style="--card-accent:var(--a-dg)" tabindex="0" role="button" aria-label="Datacard Generator">
            <span class="tape"></span><span class="pin tl"></span><span class="pin tr"></span>
            <div class="shot"></div>
            <div class="caption">
              <div class="cap-row">
                <span class="logo" style="background:var(--a-dg)">D·G</span>
                <span class="ptitle">Datacard Generator</span>
                <span class="pver">v1.5.1</span>
              </div>
              <div class="pdesc" data-i18n="dg.desc">Datacards de vol d'une page pour le kneeboard — saisie ou depuis un briefing, day et night, export PNG et PDF.</div>
              <div class="pstatus"><span class="dot"></span> <span data-i18n="status.op">Opérationnel</span></div>
            </div>
            <span class="cta" data-i18n="cta">▶ Ouvrir le dossier</span>
          </div>

          <div class="print active reveal d6" id="card-fc" style="--card-accent:var(--a-fc)" tabindex="0" role="button" aria-label="Flight Configurator">
            <span class="tape"></span><span class="pin tl"></span><span class="pin tr"></span>
            <div class="shot"></div>
            <div class="caption">
              <div class="cap-row">
                <span class="logo" style="background:var(--a-fc)">F·C</span>
                <span class="ptitle">Flight Configurator</span>
                <span class="pver">v0.1.2</span>
              </div>
              <div class="pdesc" data-i18n="fc.desc">Assemble un groupe — identité, radios, emport composé sur la vue de face ou tiré de mes presets, livrée — et l'exporte en paquet de vol que HQ applique à une mission.</div>
              <div class="pstatus"><span class="dot"></span> <span data-i18n="status.op">Opérationnel</span></div>
            </div>
            <span class="cta" data-i18n="cta">▶ Ouvrir le dossier</span>
          </div>
        </div>
      </div>

    </div>
  </div>

  <div id="credits">
    <p>Based on Mission Plan by MirabelleBenou and the 4th VEAW virtual wing — <a href="https://github.com/MirabelleBenou/dcs-mission-plan" target="_blank" rel="noopener">github.com/MirabelleBenou/dcs-mission-plan</a> · <a href="https://github.com/MirabelleBenou/dcs-mission-plan/blob/main/LICENSE" target="_blank" rel="noopener">AGPL-3.0-or-later</a></p>
    <p><span data-i18n="credits.data">Données des appareils et des terrains : </span><a href="https://github.com/pydcs/dcs" target="_blank" rel="noopener">pydcs</a><span data-i18n="credits.rest"> (LGPL-3.0-or-later) · vues de face : Goldwolf, DCS Reference Guide, avec son autorisation</span></p>
  </div>

  <div class="foot">
    <span>DCS Mission Plan</span><span class="dot">·</span>
    <span id="foot-info">Cold War OTAN</span>
    <span class="right" id="foot-right">Mission Plan</span>
  </div>

</div>
</div>

<!-- Module view -->
<div id="module-view"></div>
<div id="module-loading" class="hidden">Chargement…</div>

{SUITE_HTML}
<script>
  /* ── Données ──────────────────────────────────────────────── */
  {module_html_js}

  /* Les fichiers d'exemple (samples/example_work_fr.json, samples/example_work_en.json), au format du fichier de travail : l'exemple de chaque groupe, dans la langue du shell */
  const SUITE_EXAMPLES = {suite_examples_js};

  var APP_VERSION = '1.24.0';
  var KEY_LANG  = 'lang_v1';
  var KEY_THEME = 'theme_v1';

  var THEMES = {{
    'cw-nato':    {{label:'Cold War OTAN',       stamp:'Declassified', classif:'Classified // Eyes Only'}},
    'cw-soviet':  {{label:'Cold War Soviétique', stamp:'Секретно',     classif:'Совершенно секретно'}},
    'modern-nato':{{label:'OTAN moderne',        stamp:'Restricted',   classif:'Restricted // NoForn'}},
    'modern-east':{{label:'Bloc Est moderne',    stamp:'MZ-7 // Restr',classif:'MZ-7 // Restricted'}}
  }};

  var I18N = {{
    fr: {{
      ribbon: '// Suite de préparation opérationnelle',
      'grp.mc.sub': 'prépare la mission',
      'grp.fl.sub': 'prépare son vol',
      'ex.btn': 'Exemple',
      'ex.tip': "Charger l’exemple STEPPE WIND",
      'ex.mc': 'Mission Commander — Briefing Generator, Recon Station',
      'ex.fl': 'Flight Leader — Route Planner, Datacard Generator, Flight Configurator',
      'work.example.mc': 'Exemple STEPPE WIND chargé : Mission Commander',
      'work.example.fl': 'Exemple STEPPE WIND chargé : Flight Leader',
      'work.open.btn': 'Ouvrir…',
      'work.open.tip': 'Ouvrir un travail de Mission Plan (JSON)',
      'work.save.btn': 'Sauvegarder',
      'work.save.tip': 'Sauvegarder tout le travail de Mission Plan (JSON)',
      'fm.btn': 'Field Manual',
      'fm.tip': 'Le manuel de la suite',
      'work.name.title': 'Sauvegarder le travail',
      'work.name.label': 'Nom du fichier',
      'work.opened': 'Travail ouvert : {{0}}',
      'work.bad': 'illisible, repris à vide : {{0}}',
      'work.bad.settings': 'réglages',
      'work.err.json': "⚠ Fichier illisible : ce n'est pas du JSON.",
      'work.err.format': "⚠ Ce fichier n'est pas un travail de Mission Plan.",
      'work.err.empty': "⚠ Ce travail est vide : rien n'a changé.",
      'work.err.full': "⚠ Mémoire du navigateur pleine : le travail n'a pas été ouvert.",
      'ui.cancel': 'Annuler',
      'ui.close': 'Fermer',
      'ui.restore': 'Restaurer',
      'ui.restore.refused': 'Restauration impossible\u202f: les données ont changé depuis.',
      'hq.desc': 'Poste de commandement — configuration Wing, identité escadrons, logos partagés avec tous les modules.',
      'bg.desc': 'Briefings complets — SITAC, plan radio, aérodromes, charts, annexes — export PDF prêt à partager.',
      'rs.desc': "Transforme une capture en photo d'analyse de reconnaissance — niveaux de gris, annotations au doigt, export PNG pleine résolution.",
      'dg.desc': "Datacards de vol d'une page pour le kneeboard — saisie ou depuis un briefing, day et night, export PNG et PDF.",
      'fc.desc': "Assemble un groupe — identité, radios, emport composé sur la vue de face ou tiré de mes presets, livrée — et l'exporte en paquet de vol que HQ applique à une mission.",
      'rp.desc': 'Tracé de route sur carte — carte DCS, topographique ou satellite, grille MGRS, villes et aérodromes, recherche ; points de référence ; caps, distances, vitesse sol et minutage ; calques CombatFlite et dessin au doigt (zones, FLOT, couloirs, orbites, boîtes) ; MGRS et DMS, envoyés à la datacard ; import et export du Route Tool de DCS.',
      'status.op': 'Opérationnel',
      'credits.data': 'Données des appareils et des terrains : ',
      'credits.rest': ' (LGPL-3.0-or-later) · vues de face : Goldwolf, DCS Reference Guide, avec son autorisation',
      cta: '▶ Ouvrir le dossier',
      soon: 'À venir',
      loading: 'Chargement',
      back: '◄ Mission Plan',
      'theme.cwnato': 'Cold War OTAN',
      'theme.cwsoviet': 'Cold War Soviétique',
      'theme.modernnato': 'OTAN moderne',
      'theme.moderneast': 'Bloc Est moderne',
      'theme.sel': 'Thème'
    }},
    en: {{
      ribbon: '// Operational planning suite',
      'grp.mc.sub': 'prepares the mission',
      'grp.fl.sub': 'prepares the flight',
      'ex.btn': 'Example',
      'ex.tip': 'Load the STEPPE WIND example',
      'ex.mc': 'Mission Commander — Briefing Generator, Recon Station',
      'ex.fl': 'Flight Leader — Route Planner, Datacard Generator, Flight Configurator',
      'work.example.mc': 'STEPPE WIND example loaded: Mission Commander',
      'work.example.fl': 'STEPPE WIND example loaded: Flight Leader',
      'work.open.btn': 'Open…',
      'work.open.tip': 'Open a Mission Plan work file (JSON)',
      'work.save.btn': 'Save',
      'work.save.tip': 'Save all the Mission Plan work (JSON)',
      'fm.btn': 'Field Manual',
      'fm.tip': "The suite's manual",
      'work.name.title': 'Save the work',
      'work.name.label': 'File name',
      'work.opened': 'Work opened: {{0}}',
      'work.bad': 'unreadable, started empty: {{0}}',
      'work.bad.settings': 'settings',
      'work.err.json': '⚠ Unreadable file: this is not JSON.',
      'work.err.format': '⚠ This file is not a Mission Plan work file.',
      'work.err.empty': '⚠ This work file is empty: nothing has changed.',
      'work.err.full': '⚠ Browser storage is full: the work was not opened.',
      'ui.cancel': 'Cancel',
      'ui.close': 'Close',
      'ui.restore': 'Restore',
      'ui.restore.refused': 'Cannot restore: the data has changed since.',
      'hq.desc': 'Command hub — Wing configuration, squadron identity, logos shared across all modules.',
      'bg.desc': 'Complete briefings — SITAC, radio plan, airfields, charts, annexes — PDF export ready to share.',
      'rs.desc': 'Turns a screenshot into a reconnaissance analysis photo — greyscale, touch annotations, full-resolution PNG export.',
      'dg.desc': 'One-page flight datacards for the kneeboard — from scratch or from a briefing, day and night, PNG and PDF export.',
      'fc.desc': "Assembles a group — identity, radios, loadout built on the front view or started from my presets, livery — and exports it as a flight package that HQ applies to a mission.",
      'rp.desc': 'Lay a route on a map — DCS, topographic or satellite, MGRS grid, towns and airfields, search; reference points; headings, distances, ground speed and minute marks; CombatFlite layers and touch drawing (zones, FLOT, corridors, orbits, boxes); MGRS and DMS, sent to the datacard; DCS Route Tool import and export.',
      'status.op': 'Operational',
      'credits.data': 'Aircraft and airfield data: ',
      'credits.rest': ' (LGPL-3.0-or-later) · front views: Goldwolf, DCS Reference Guide, used with permission',
      cta: '▶ Open the file',
      soon: 'Coming soon',
      loading: 'Loading',
      back: '◄ Mission Plan',
      'theme.cwnato': 'Cold War NATO',
      'theme.cwsoviet': 'Cold War Soviet',
      'theme.modernnato': 'Modern NATO',
      'theme.moderneast': 'Modern East Bloc',
      'theme.sel': 'Theme'
    }}
  }};

  var CURRENT_LANG = 'fr';
  var iframes = {{}};
  var activeModule = null;
  var barSync = {{}};   /* id du module -> fonction qui remet à jour sa barre (bouton retour, dégradé) */

  function t(key) {{
    return (I18N[CURRENT_LANG] && I18N[CURRENT_LANG][key]) || key;
  }}

  /* ── Thème ─────────────────────────────────────────────────── */
  /* ── Tampon escadrille (lecture wing_config_v1) ───────────────── */
  function wingShortName() {{
    try {{
      var c = JSON.parse(localStorage.getItem('wing_config_v1') || 'null');
      return (c && c.wing && c.wing.shortName) ? c.wing.shortName : '';
    }} catch(e) {{ return ''; }}
  }}
  function refreshWingStamps() {{
    var name = wingShortName();
    Object.keys(iframes).forEach(function(iid) {{
      if (iid === 'bg') return;   /* le BG remplit seul son tampon (applyWingBranding) */
      try {{
        var lbl = iframes[iid].contentDocument.querySelector('.mp-wing-stamp-label');
        if (lbl) lbl.textContent = name;
      }} catch(e) {{}}
    }});
  }}
  function setTheme(val) {{
    if (!THEMES[val]) return;
    var d = THEMES[val];
    document.body.setAttribute('data-theme', val);
    document.getElementById('bigstamp').textContent = d.stamp;
    document.getElementById('classif').textContent  = d.classif;
    document.getElementById('theme-sel').value = val;
    document.getElementById('foot-info').textContent = d.label;
    /* i18n soon labels */
    document.querySelectorAll('[data-i18n="soon"]').forEach(function(el) {{
      el.textContent = val.indexOf('modern') === 0 ? (CURRENT_LANG === 'en' ? 'Coming' : 'Bientôt') : t('soon');
    }});
    try {{ localStorage.setItem(KEY_THEME, val); }} catch(e) {{}}
    /* Propagation live : pousser data-theme dans les modules ouverts (CSS body[data-theme]) */
    Object.keys(iframes).forEach(function(iid) {{
      try {{ iframes[iid].contentDocument.body.setAttribute('data-theme', val); }} catch(e) {{}}
    }});
  }}

  /* ── Langue ────────────────────────────────────────────────── */
  function applyI18n() {{
    document.querySelectorAll('[data-i18n]').forEach(function(el) {{
      var key = el.getAttribute('data-i18n');
      /* Les options select : mettre à jour textContent */
      var txt = t(key);
      if (txt !== key) el.textContent = txt;
    }});
    document.querySelectorAll('[data-i18n-title]').forEach(function(el) {{
      el.title = t(el.getAttribute('data-i18n-title'));
    }});
    document.querySelectorAll('[data-i18n-aria]').forEach(function(el) {{
      el.setAttribute('aria-label', t(el.getAttribute('data-i18n-aria')));
    }});
    /* Sync bigstamp / classif via thème actuel */
    var cur = document.body.getAttribute('data-theme') || 'cw-nato';
    setTheme(cur);
    /* Bouton chargement */
    var loadEl = document.getElementById('module-loading');
    if (loadEl) loadEl.textContent = t('loading') + '…';
  }}

  /* Les drapeaux sont dessinés (ils ne s'affichent pas en lettres sous Windows) ; le bouton montre la langue vers laquelle il bascule */
  var FLAG_FR = '<svg viewBox="0 0 20 14" width="22" height="15" xmlns="http://www.w3.org/2000/svg"><rect width="7" height="14" fill="#002395"/><rect x="7" width="6" height="14" fill="#fff"/><rect x="13" width="7" height="14" fill="#ED2939"/></svg>';
  var FLAG_EN = '<svg viewBox="0 0 20 14" width="22" height="15" xmlns="http://www.w3.org/2000/svg"><rect width="20" height="14" fill="#012169"/><path d="M0,0 L20,14 M20,0 L0,14" stroke="#fff" stroke-width="2.8"/><path d="M0,0 L20,14 M20,0 L0,14" stroke="#C8102E" stroke-width="1.6"/><rect x="8" width="4" height="14" fill="#fff"/><rect y="5" width="20" height="4" fill="#fff"/><rect x="9" width="2" height="14" fill="#C8102E"/><rect y="6" width="20" height="2" fill="#C8102E"/></svg>';

  function updateFlagBtn() {{
    var btn = document.getElementById('flag-btn');
    if (!btn) return;
    btn.innerHTML = CURRENT_LANG === 'fr' ? FLAG_EN : FLAG_FR;
    var tip = CURRENT_LANG === 'fr' ? 'Passer en anglais' : 'Switch to French';
    btn.title = tip;
    btn.setAttribute('aria-label', tip);
  }}

  function setLang(lang) {{
    if (lang !== 'fr' && lang !== 'en') return;
    CURRENT_LANG = lang;
    try {{ localStorage.setItem(KEY_LANG, lang); }} catch(e) {{}}
    applyI18n();
    updateFlagBtn();
    Object.keys(barSync).forEach(function(bid) {{ barSync[bid](); }});
  }}

  function toggleLang() {{
    setLang(CURRENT_LANG === 'fr' ? 'en' : 'fr');
  }}

  function initLang() {{
    try {{
      var stored = localStorage.getItem(KEY_LANG);
      if (stored === 'fr' || stored === 'en') CURRENT_LANG = stored;
    }} catch(e) {{}}
  }}

  /* ── Module : decode UTF-8 ─────────────────────────────────── */
  function decodeModule(b64) {{
    var bin = atob(b64);
    var bytes = new Uint8Array(bin.length);
    for (var i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
    return new TextDecoder('utf-8').decode(bytes);
  }}

  /* ── Barre d'un outil dans le shell ────────────────────────── */
  /* Remet à jour, dans le document de l'outil : le bouton retour (flèche seule sous 760 px, avec son nom en aria-label et
     title ; texte entier au-delà) et le fondu du bord droit (barre qui défile et qui n'est pas au bout). Rappelée au
     défilement de la barre, au redimensionnement, aux changements de la barre (langue de l'outil) et au changement de
     langue du shell. */
  function mpBindToolbar(iframe, toolbar, back) {{
    var doc = iframe.contentDocument, win = iframe.contentWindow, queued = false;
    function sync() {{
      queued = false;
      try {{
        var full = t('back');
        var cut = full.indexOf(' ');
        var arrow = cut > 0 ? full.slice(0, cut) : full;
        var name = (cut > 0 ? full.slice(cut) : full).trim();
        var compact = win.matchMedia('(max-width: 759px)').matches;
        var txt = compact ? arrow : full;
        if (back.textContent !== txt) back.textContent = txt;
        if (back.getAttribute('aria-label') !== name) back.setAttribute('aria-label', name);
        if (compact) {{ if (back.title !== name) back.title = name; }}
        else if (back.hasAttribute('title')) back.removeAttribute('title');
        var g = win.getComputedStyle(toolbar).columnGap;
        g = (g && g !== 'normal') ? g : '0px';
        if (toolbar.style.getPropertyValue('--mp-fade-gap') !== g) toolbar.style.setProperty('--mp-fade-gap', g);
        var max = toolbar.scrollWidth - toolbar.clientWidth;
        var on = max > 1 && toolbar.scrollLeft < max - 1;
        if (toolbar.classList.contains('mp-fade-r') !== on) toolbar.classList.toggle('mp-fade-r', on);
      }} catch(e) {{}}
    }}
    function later() {{
      if (queued) return;
      queued = true;
      (win.requestAnimationFrame || win.setTimeout)(sync);
    }}
    toolbar.addEventListener('scroll', later, {{ passive: true }});
    win.addEventListener('resize', later);
    new win.MutationObserver(later).observe(toolbar, {{
      childList: true, subtree: true, characterData: true, attributes: true,
      attributeFilter: ['hidden', 'class', 'style', 'disabled', 'aria-pressed']
    }});
    try {{ if (doc.fonts && doc.fonts.ready) doc.fonts.ready.then(later); }} catch(e) {{}}
    sync();
    return later;
  }}

  /* ── Navigation ────────────────────────────────────────────── */
  /* La langue de la suite est celle de lang_v1 : un outil qui change sa langue par son drapeau l'écrit, mais CURRENT_LANG du shell
     n'est remis à jour qu'au retour à l'accueil. Chemin commun à tout ce qui montre un module (accueil, « Vers la datacard »,
     « Vers le briefing », MP_SEND_MAP) : le shell reprend lang_v1 (drapeau de l'accueil compris), sans rien écrire. */
  function adoptStoredLang() {{
    try {{
      var s = localStorage.getItem(KEY_LANG);
      if ((s === 'fr' || s === 'en') && s !== CURRENT_LANG) {{
        CURRENT_LANG = s;
        applyI18n();
        updateFlagBtn();
        Object.keys(barSync).forEach(function(bid) {{ barSync[bid](); }});
      }}
    }} catch(e) {{}}
  }}

  function openModule(id) {{
    if (!MODULE_HTML[id]) {{
      console.warn('[M·P] Module ' + id + ' : base64 vide');
      return;
    }}
    adoptStoredLang();
    document.getElementById('landing').style.display = 'none';
    var mv = document.getElementById('module-view');
    mv.style.display = 'block';

    Object.keys(iframes).forEach(function(iid) {{ iframes[iid].style.display = 'none'; }});

    if (!iframes[id]) {{
      var loading = document.getElementById('module-loading');
      loading.classList.remove('hidden');
      loading.textContent = t('loading') + '…';

      var iframe = document.createElement('iframe');
      iframe.id = 'iframe-' + id;
      iframe.title = id;
      iframe.srcdoc = decodeModule(MODULE_HTML[id]);

      iframe.addEventListener('load', function() {{
        loading.classList.add('hidden');
        if (typeof suiteOnLoad === 'function') suiteOnLoad(id);
        toastWatch(iframe);
        var doc = iframe.contentDocument;
        /* Injection bouton retour dans .toolbar (pas #app-header — cf. vérif grep) */
        var toolbar = doc && doc.querySelector('.toolbar');
        if (toolbar && !toolbar.querySelector('.mp-back-injected')) {{
          var back = doc.createElement('button');
          back.className = 'mp-back-injected';
          back.textContent = t('back');
          back.style.cssText = 'font-family:"Roboto Mono",monospace;font-weight:400;font-size:11px;cursor:pointer;color:#d9a54a;'
            + 'background:transparent;border:1px solid #c0892a;border-radius:3px;padding:4px 10px;'
            + 'margin-right:12px;letter-spacing:.03em;min-height:44px;box-sizing:border-box;flex-shrink:0;';
          back.addEventListener('click', goHub);
          toolbar.insertBefore(back, toolbar.firstChild);
          /* La barre des outils dans le shell : un seul style pour tous les outils (défilement de la barre, bouton retour
             réduit à la flèche et tampon masqué sous 760 px, fondu sur le bord droit), que le tampon existe ou non */
          if (!doc.getElementById('mp-toolbar-style')) {{
            var tbs = doc.createElement('style');
            tbs.id = 'mp-toolbar-style';
            tbs.textContent =
                '.toolbar{{overflow-x:auto;overflow-y:hidden;scrollbar-width:none;-webkit-overflow-scrolling:touch;}}'
              + '.toolbar::-webkit-scrollbar{{display:none;}}'
              + '.toolbar.mp-fade-r::after{{content:"";position:sticky;right:0;flex:0 0 28px;width:28px;align-self:stretch;'
              + 'margin-left:calc(-28px - var(--mp-fade-gap,0px));pointer-events:none;opacity:1;z-index:2;background:inherit;'
              + '-webkit-mask-image:linear-gradient(270deg,#000,transparent);mask-image:linear-gradient(270deg,#000,transparent);}}'
              + '@media (max-width:759px){{'
              + '.mp-wing-stamp{{display:none !important;}}'
              + '.toolbar .mp-back-injected{{box-sizing:border-box !important;width:44px !important;min-width:44px !important;'
              + 'height:44px !important;min-height:44px !important;padding:0 !important;font-size:13px !important;'
              + 'line-height:1 !important;overflow:hidden;white-space:nowrap;}}'
              + '}}';
            doc.head.appendChild(tbs);
          }}
          barSync[id] = mpBindToolbar(iframe, toolbar, back);
          /* Tampon escadrille — clone du .tb-brand natif de BG (BG exclu : il l'a déjà) */
          var sn = wingShortName();
          var acc = (getComputedStyle(document.documentElement).getPropertyValue('--a-' + id) || '').trim() || '#c0892a';
          if (id !== 'bg' && sn && !toolbar.querySelector('.mp-wing-stamp')) {{
            if (!doc.getElementById('mp-stamp-style')) {{
              var st = doc.createElement('style');
              st.id = 'mp-stamp-style';
              st.textContent =
                '.mp-wing-stamp{{display:inline-flex;align-items:center;gap:10px;'
              + 'margin-right:12px;padding-right:12px;border-right:1px solid #807454;'
              + "font-family:'Stardos Stencil','Impact','Arial Narrow Bold',sans-serif;"
              + 'font-weight:700;letter-spacing:2px;font-size:16px;color:var(--paper,#e8e3d8);'
              + 'white-space:nowrap;flex-shrink:0;}}'
              + '.mp-wing-stamp::before{{content:"";display:inline-block;width:8px;height:8px;'
              + 'border-radius:50%;background:' + acc + ';box-shadow:0 0 8px ' + acc + ';'
              + 'animation:mp-pulse 2s ease-in-out infinite;flex-shrink:0;}}'
              + '@keyframes mp-pulse{{0%,100%{{opacity:1;}}50%{{opacity:.4;}}}}';
              doc.head.appendChild(st);
            }}
            var stamp = doc.createElement('span');
            stamp.className = 'mp-wing-stamp';
            var lbl = doc.createElement('span');
            lbl.className = 'mp-wing-stamp-label';
            lbl.textContent = sn;
            stamp.appendChild(lbl);
            toolbar.insertBefore(stamp, back.nextSibling);
          }}
          /* Déplacer #btn-lang en fin de toolbar */
          var btnLang = doc.getElementById('btn-lang');
          if (btnLang) toolbar.appendChild(btnLang);
        }}
        try {{ doc.body.setAttribute('data-theme', document.body.getAttribute('data-theme') || 'cw-nato'); }} catch(e) {{}}
        try {{ iframe.contentWindow.focus(); }} catch(e) {{}}       /* l'outil ouvert reçoit le clavier : Ctrl+S lui parvient sans clic */
      }});

      mv.appendChild(iframe);
      iframes[id] = iframe;
    }} else {{
      iframes[id].style.display = 'block';
      /* La langue suit comme le thème : un module déjà chargé qui n'est pas dans la langue de la suite passe à celle-ci, sans se recharger, par sa propre fonction de langue (celle de son drapeau) */
      try {{
        var mw = iframes[id].contentWindow;
        if (mw && typeof mw.setLang === 'function' && mw.document.documentElement.lang !== CURRENT_LANG) mw.setLang(CURRENT_LANG);
      }} catch(e) {{ console.warn('[M·P] langue du module ' + id + ' : ' + e); }}
      if (barSync[id]) barSync[id]();
      document.getElementById('module-loading').classList.add('hidden');
      try {{ iframes[id].contentDocument.body.setAttribute('data-theme', document.body.getAttribute('data-theme') || 'cw-nato'); }} catch(e) {{}}
      try {{ iframes[id].contentWindow.focus(); }} catch(e) {{}}
    }}

    activeModule = id;
    toastPlace();
  }}

  /* Le toast du shell au-dessus de la barre basse de l'outil ouvert : il lit --mp-toast-bottom sur le document de l'outil (même origine ; l'outil la pose quand il a une barre basse visible),
     à l'affichage du toast et quand elle change (l'observateur de l'iframe ; un outil qui se recharge est ré-observé à son « load »). Sans valeur, ou à l'accueil, le toast reste à 20 px du bas. */
  function toastPlace() {{
    var root = document.documentElement, v = '';
    try {{
      var f = activeModule && iframes[activeModule], d = f && f.contentDocument;
      if (d && d.documentElement) v = d.documentElement.style.getPropertyValue('--mp-toast-bottom').trim();
    }} catch(e) {{}}
    if (!v) {{ root.style.removeProperty('--mp-toast-bottom'); return; }}
    if (root.style.getPropertyValue('--mp-toast-bottom') !== v) root.style.setProperty('--mp-toast-bottom', v);
  }}
  function toastWatch(iframe) {{
    try {{ new MutationObserver(toastPlace).observe(iframe.contentDocument.documentElement, {{ attributes: true, attributeFilter: ['style'] }}); }}
    catch(e) {{ console.warn('[M·P] toast : ' + e); }}
    toastPlace();
  }}

  /* Point d'entrée pour les modules (le Route Planner ouvre le Datacard Generator) */
  window.MP_OPEN_MODULE = openModule;

  /* Pont de la carte du Route Planner vers le Briefing Generator : le dernier payload reçu reste en mémoire du shell
     (ni postMessage, ni stockage) jusqu'à ce que le BG le prenne — à son démarrage (MP_TAKE_MAP) ou, s'il est déjà
     ouvert, tout de suite (MP_RECEIVE_MAP) */
  var pendingMap = null;
  window.MP_SEND_MAP = function(payload) {{
    pendingMap = payload;
    openModule('bg');
    var f = iframes['bg'];
    try {{
      if (f && f.contentWindow && typeof f.contentWindow.MP_RECEIVE_MAP === 'function') {{
        var p = pendingMap;
        pendingMap = null;
        f.contentWindow.MP_RECEIVE_MAP(p);
      }}
    }} catch(e) {{ console.warn('[M·P] MP_RECEIVE_MAP : ' + e); }}
  }};
  window.MP_TAKE_MAP = function() {{
    var p = pendingMap;
    pendingMap = null;
    return p || null;
  }};

  /* Le clavier de l'écran : sur les navigateurs qui ignorent interactive-widget (iOS), seul le visualViewport de cette page rétrécit ;
     le module (cadre fixe) reçoit alors la hauteur et le haut de la zone visible, et revient à inset: 0 quand le clavier se ferme */
  function fitModuleView() {{
    var mv = document.getElementById('module-view'), vv = window.visualViewport;
    if (!mv) return;
    if (vv && vv.height > 0 && vv.height < window.innerHeight - 1 && Math.abs(vv.scale - 1) < 0.01) {{       /* le clavier ne change pas l'échelle : un zoom à deux doigts, si */
      mv.style.top = vv.offsetTop + 'px';
      mv.style.bottom = 'auto';
      mv.style.height = vv.height + 'px';
    }} else {{
      mv.style.top = '';
      mv.style.bottom = '';
      mv.style.height = '';
    }}
  }}
  if (window.visualViewport) {{
    window.visualViewport.addEventListener('resize', fitModuleView);
    window.visualViewport.addEventListener('scroll', fitModuleView);
  }}

  function goHub() {{
    Object.keys(iframes).forEach(function(iid) {{ iframes[iid].style.display = 'none'; }});
    document.getElementById('module-view').style.display = 'none';
    var landing = document.getElementById('landing');
    landing.style.display = '';
    activeModule = null;
    toastPlace();
    /* Le clavier quitte l'outil qu'on vient de fermer (le clic sur Retour l'y avait laissé) : Ctrl+S au hub est à l'accueil (Sauvegarder), pas à l'outil masqué */
    try {{
      if (document.activeElement && document.activeElement.tagName === 'IFRAME') document.activeElement.blur();
      if (!landing.hasAttribute('tabindex')) landing.setAttribute('tabindex', '-1');
      landing.focus({{ preventScroll: true }});
      window.focus();
    }} catch(e) {{}}
    /* Resync thème + langue si changé dans le module */
    try {{
      var storedTheme = localStorage.getItem(KEY_THEME);
      if (storedTheme && THEMES[storedTheme]) setTheme(storedTheme);
      var storedLang = localStorage.getItem(KEY_LANG);
      if (storedLang && storedLang !== CURRENT_LANG) setLang(storedLang);
    }} catch(e) {{}}
  }}

{MESSAGES_JS}
{SUITE_JS}
/* ============= LISTES DE LA BARRE — thème de l'interface (lot mp-ui-listes) =============
   Le <select> reste dans la page (id, options, écouteurs) : il garde la valeur, mais il est masqué.
   Un <button> de mêmes classes prend sa place et porte le libellé de l'option choisie ; la liste ouverte
   est un <ul role="listbox"> posé en fin de <body> (la barre défile et couperait ce qui déborde).
   Le libellé suit toujours le <select> : mutations du DOM (options reconstruites, traduites, désactivées,
   title) et affectations par le code (value, selectedIndex) interceptées sur l'instance. */
const TBM = {{ cur: null, bound: false, swallow: false }};

function initToolbarMenus(specs) {{
  specs.forEach(sp => tbmAttach(document.getElementById(sp[0]), sp[1]));
  if (TBM.bound) return;
  TBM.bound = true;
  document.addEventListener('pointerdown', tbmOutside, true);
  window.addEventListener('click', tbmSwallowClick, true);
  window.addEventListener('resize', () => tbmClose(false));
  window.addEventListener('blur', () => tbmClose(false));
  window.addEventListener('scroll', tbmScrolled, true);
}}

function tbmAttach(sel, labelFn) {{
  if (!sel || !sel.parentNode || sel.hasAttribute('data-tbm-src')) return;
  const btn = document.createElement('button');
  btn.type = 'button';
  btn.className = sel.className + ' tbm-trigger';
  btn.setAttribute('aria-haspopup', 'listbox');
  btn.setAttribute('aria-expanded', 'false');
  btn.setAttribute('aria-controls', 'tbm-list-' + sel.id);
  const lbl = document.createElement('span');
  lbl.className = 'tbm-lbl';
  btn.appendChild(lbl);
  const m = {{ sel: sel, btn: btn, lbl: lbl, labelFn: labelFn, panel: null, active: -1, type: '', typeTimer: 0, x0: 0, y0: 0 }};
  sel.parentNode.insertBefore(btn, sel);
  sel.setAttribute('data-tbm-src', '');
  ['value', 'selectedIndex'].forEach(k => {{
    const d = Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype, k);
    if (!d || !d.set) return;
    Object.defineProperty(sel, k, {{
      configurable: true, enumerable: true,
      get() {{ return d.get.call(this); }},
      set(v) {{ d.set.call(this, v); tbmSync(m); }}
    }});
  }});
  new MutationObserver(() => tbmSync(m)).observe(sel, {{
    childList: true, subtree: true, characterData: true, attributes: true,
    attributeFilter: ['title', 'aria-label', 'disabled', 'label', 'selected', 'value']
  }});
  sel.addEventListener('change', () => tbmSync(m));
  ['focus', 'mouseover'].forEach(ev => btn.addEventListener(ev, () => tbmSync(m)));   /* filet : option.selected posé par le code */
  btn.addEventListener('click', () => {{ if (m.panel) tbmClose(true); else tbmOpen(m); }});
  btn.addEventListener('keydown', e => {{
    if (e.key === 'Enter' || e.key === ' ' || e.key === 'ArrowDown' || e.key === 'ArrowUp') {{
      e.preventDefault();
      if (!m.panel) tbmOpen(m);
    }}
  }});
  tbmSync(m);
}}

/* Le libellé affiché = l'option choisie ; la largeur = l'option la plus large (comme le <select>) */
function tbmSync(m) {{
  const sel = m.sel, o = sel.options, i = sel.selectedIndex;
  const txt = i >= 0 && o[i] ? o[i].label : '';
  if (m.lbl.textContent !== txt) m.lbl.textContent = txt;
  const all = [];
  for (let k = 0; k < o.length; k++) all.push(o[k].label);
  const w = all.join(String.fromCharCode(10));
  if (m.lbl.getAttribute('data-w') !== w) m.lbl.setAttribute('data-w', w);
  let name = '';
  try {{ name = m.labelFn(); }} catch (e) {{ name = ''; }}
  m.btn.setAttribute('aria-label', name);
  if (sel.hasAttribute('title')) m.btn.title = sel.title; else m.btn.removeAttribute('title');
  m.btn.disabled = sel.disabled;
}}

function tbmOpen(m) {{
  if (TBM.cur) tbmClose(false);
  if (m.sel.disabled) return;
  tbmSync(m);
  const sel = m.sel, opts = sel.options, name = m.labelFn();
  const ul = document.createElement('ul');
  ul.className = 'tbm-panel';
  ul.id = 'tbm-list-' + sel.id;
  ul.setAttribute('role', 'listbox');
  ul.setAttribute('aria-label', name);
  ul.tabIndex = -1;
  const head = document.createElement('li');
  head.className = 'tbm-head';
  head.setAttribute('role', 'presentation');
  head.textContent = name;
  ul.appendChild(head);
  for (let k = 0; k < opts.length; k++) {{
    const o = opts[k], li = document.createElement('li');
    li.className = 'tbm-opt';
    li.id = 'tbm-' + sel.id + '-' + k;
    li.setAttribute('role', 'option');
    li.setAttribute('aria-selected', k === sel.selectedIndex ? 'true' : 'false');
    li.setAttribute('data-i', String(k));
    const mark = document.createElement('span');
    mark.className = 'tbm-mark';
    const txt = document.createElement('span');
    txt.className = 'tbm-txt';
    let label = o.label, note = '';
    if (o.disabled) {{
      li.setAttribute('aria-disabled', 'true');
      const j = label.indexOf(' — ');
      if (j >= 0) {{ note = label.slice(j + 3); label = label.slice(0, j); }}
    }}
    txt.textContent = label;
    li.appendChild(mark);
    li.appendChild(txt);
    if (note) {{
      const n = document.createElement('span');
      n.className = 'tbm-note';
      n.textContent = note;
      li.appendChild(n);
    }}
    ul.appendChild(li);
  }}
  ul.addEventListener('keydown', e => tbmKey(m, e));
  ul.addEventListener('click', e => {{
    const li = e.target.closest ? e.target.closest('.tbm-opt') : null;
    if (!li || li.getAttribute('aria-disabled') === 'true') return;
    tbmChoose(m, Number(li.getAttribute('data-i')));
  }});
  ul.addEventListener('mousemove', e => {{
    const li = e.target.closest ? e.target.closest('.tbm-opt') : null;
    if (!li || li.getAttribute('aria-disabled') === 'true') return;
    const k = Number(li.getAttribute('data-i'));
    if (k !== m.active) tbmSetActive(m, k, false);
  }});
  document.body.appendChild(ul);
  m.panel = ul;
  TBM.cur = m;
  m.btn.classList.add('tbm-trigger-open');
  m.btn.setAttribute('aria-expanded', 'true');
  tbmPlace(m);
  let k0 = sel.selectedIndex;
  if (k0 < 0 || (opts[k0] && opts[k0].disabled)) k0 = tbmFirst(m, 1);
  tbmSetActive(m, k0, 'center');
  ul.focus({{ preventScroll: true }});
}}

/* Sous le bouton (4 px), bord gauche aligné, au moins aussi large, à 8 px au moins des bords de la fenêtre */
function tbmPlace(m) {{
  const r = m.btn.getBoundingClientRect(), p = m.panel;
  const vw = document.documentElement.clientWidth, vh = window.innerHeight;
  const top = r.bottom + 4;
  m.x0 = r.left; m.y0 = r.top;
  p.style.minWidth = Math.max(180, r.width) + 'px';
  p.style.top = top + 'px';
  p.style.left = r.left + 'px';
  p.style.maxHeight = Math.max(60, Math.min(0.62 * vh, 440, vh - top - 12)) + 'px';
  const w = p.getBoundingClientRect().width;
  let left = r.left;
  if (left + w > vw - 8) left = vw - 8 - w;
  if (left < 8) left = 8;
  p.style.left = left + 'px';
}}

function tbmFirst(m, d) {{
  const o = m.sel.options;
  let k = d > 0 ? 0 : o.length - 1;
  for (; k >= 0 && k < o.length; k += d) if (!o[k].disabled) return k;
  return -1;
}}

function tbmSetActive(m, k, reveal) {{
  const p = m.panel;
  if (!p) return;
  const prev = p.querySelector('.tbm-opt.active');
  if (prev) prev.classList.remove('active');
  m.active = k;
  const li = k >= 0 ? p.querySelector('.tbm-opt[data-i="' + k + '"]') : null;
  if (!li) {{ p.removeAttribute('aria-activedescendant'); return; }}
  li.classList.add('active');
  p.setAttribute('aria-activedescendant', li.id);
  if (!reveal) return;
  const t = li.offsetTop, h = li.offsetHeight;
  if (k === tbmFirst(m, 1)) p.scrollTop = 0;
  else if (t < p.scrollTop) p.scrollTop = t;
  else if (t + h > p.scrollTop + p.clientHeight) p.scrollTop = reveal === 'center' ? Math.max(0, t - (p.clientHeight - h) / 2) : t + h - p.clientHeight;
}}

function tbmStep(m, d) {{
  const o = m.sel.options;
  for (let k = m.active + d; k >= 0 && k < o.length; k += d) {{
    if (!o[k].disabled) {{ tbmSetActive(m, k, true); return; }}
  }}
}}

/* Saisie de lettres : première option qui commence par elles, remise à zéro après 0,7 s */
function tbmType(m, ch) {{
  clearTimeout(m.typeTimer);
  m.type += ch.toLowerCase();
  m.typeTimer = setTimeout(() => {{ m.type = ''; }}, 700);
  const o = m.sel.options;
  for (let k = 0; k < o.length; k++) {{
    if (!o[k].disabled && o[k].label.toLowerCase().indexOf(m.type) === 0) {{ tbmSetActive(m, k, true); return; }}
  }}
}}

function tbmKey(m, e) {{
  const k = e.key;
  if (k === 'ArrowDown' || k === 'ArrowUp') {{ e.preventDefault(); tbmStep(m, k === 'ArrowDown' ? 1 : -1); }}
  else if (k === 'Home') {{ e.preventDefault(); tbmSetActive(m, tbmFirst(m, 1), true); }}
  else if (k === 'End') {{ e.preventDefault(); tbmSetActive(m, tbmFirst(m, -1), true); }}
  else if (k === 'Enter' || k === ' ') {{ e.preventDefault(); if (m.active >= 0) tbmChoose(m, m.active); }}
  else if (k === 'Escape') {{ e.preventDefault(); e.stopPropagation(); tbmClose(true); }}
  else if (k === 'Tab') {{ tbmClose(true); }}   /* sans preventDefault : le focus part du bouton vers le contrôle suivant */
  else if (k.length === 1 && !e.ctrlKey && !e.metaKey && !e.altKey) {{ e.preventDefault(); tbmType(m, k); }}
}}

/* Choisir : si la valeur change, le <select> la prend et reçoit un évènement change (qui bouillonne) */
function tbmChoose(m, k) {{
  const sel = m.sel, o = sel.options[k];
  if (!o || o.disabled) return;
  const changed = k !== sel.selectedIndex;
  tbmClose(true);
  if (!changed) return;
  sel.selectedIndex = k;
  sel.dispatchEvent(new Event('change', {{ bubbles: true }}));
}}

function tbmClose(refocus) {{
  const m = TBM.cur;
  if (!m) return;
  TBM.cur = null;
  clearTimeout(m.typeTimer);
  m.type = '';
  if (m.panel) m.panel.remove();
  m.panel = null;
  m.active = -1;
  m.btn.classList.remove('tbm-trigger-open');
  m.btn.setAttribute('aria-expanded', 'false');
  if (refocus) m.btn.focus({{ preventScroll: true }});
}}

/* Exemple ▾ de la barre du haut : le même panneau que les listes (tbm-panel), deux lignes, une par groupe ; il prend la place de TBM.cur (Échap, clic ailleurs, défilement, redimensionnement le ferment comme les listes) */
function exampleMenuOpen(btn) {{
  if (TBM.cur) tbmClose(false);
  const ul = document.createElement('div');
  ul.className = 'tbm-panel mp-ex-panel';
  ul.id = 'ex-panel';
  ul.setAttribute('role', 'menu');
  ul.setAttribute('aria-label', t('ex.btn'));
  ul.tabIndex = -1;
  ['mc', 'fl'].forEach(function(g) {{
    const row = document.createElement('div');
    row.className = 'tbm-opt';
    row.setAttribute('role', 'menuitem');
    row.tabIndex = -1;
    row.setAttribute('data-g', g);
    row.textContent = t('ex.' + g);
    ul.appendChild(row);
  }});
  const m = {{ btn: btn, panel: ul, x0: 0, y0: 0, active: -1 }};
  ul.addEventListener('click', function(e) {{
    const row = e.target.closest ? e.target.closest('.tbm-opt') : null;
    if (!row) return;
    tbmClose(false);
    btn.focus({{ preventScroll: true }});
    if (window.MP_WORK_EXAMPLE) window.MP_WORK_EXAMPLE(row.getAttribute('data-g'));
  }});
  ul.addEventListener('keydown', function(e) {{
    const rows = Array.prototype.slice.call(ul.querySelectorAll('.tbm-opt'));
    const cur = rows.indexOf(document.activeElement);
    const go = function(k) {{ if (rows[k]) rows[k].focus({{ preventScroll: true }}); }};
    const k = e.key;
    if (k === 'ArrowDown' || k === 'ArrowRight') {{ e.preventDefault(); go(cur < 0 ? 0 : Math.min(rows.length - 1, cur + 1)); }}
    else if (k === 'ArrowUp' || k === 'ArrowLeft') {{ e.preventDefault(); go(cur < 0 ? rows.length - 1 : Math.max(0, cur - 1)); }}
    else if (k === 'Home') {{ e.preventDefault(); go(0); }}
    else if (k === 'End') {{ e.preventDefault(); go(rows.length - 1); }}
    else if ((k === 'Enter' || k === ' ') && cur >= 0) {{ e.preventDefault(); rows[cur].click(); }}
    else if (k === 'Escape') {{ e.preventDefault(); e.stopPropagation(); tbmClose(true); }}
    else if (k === 'Tab') tbmClose(true);
  }});
  document.body.appendChild(ul);
  TBM.cur = m;
  btn.setAttribute('aria-expanded', 'true');
  btn.setAttribute('aria-controls', 'ex-panel');
  tbmPlace(m);
  ul.focus({{ preventScroll: true }});
}}

/* Un toucher ou un clic hors de la liste et du bouton la ferme, sans agir ailleurs (le clic qui suit est avalé) ;
   le bouton d'une autre liste ferme celle-ci et s'ouvre ensuite par son propre clic. */
function tbmOutside(e) {{
  const m = TBM.cur;
  if (!m) return;
  const t = e.target;
  if (m.panel.contains(t) || m.btn.contains(t)) return;
  const other = t && t.closest ? t.closest('.tbm-trigger, .mp-railbtn') : null;
  tbmClose(false);
  if (other) return;
  TBM.swallow = true;
  const rel = () => {{ document.removeEventListener('pointerup', rel, true); document.removeEventListener('pointercancel', rel, true); setTimeout(() => {{ TBM.swallow = false; }}, 350); }};
  document.addEventListener('pointerup', rel, true);
  document.addEventListener('pointercancel', rel, true);
}}

function tbmSwallowClick(e) {{
  if (!TBM.swallow) return;
  TBM.swallow = false;
  e.stopPropagation();
  e.preventDefault();
}}

/* Le défilement de la barre (ou de la page) déplace le bouton : la liste se ferme */
function tbmScrolled(e) {{
  const m = TBM.cur;
  if (!m || !m.panel) return;
  if (e.target === m.panel || (e.target.nodeType && m.panel.contains(e.target))) return;
  const r = m.btn.getBoundingClientRect();
  if (Math.abs(r.left - m.x0) > 0.5 || Math.abs(r.top - m.y0) > 0.5) tbmClose(false);
}}

  /* ── Init ───────────────────────────────────────────────────── */
  function init() {{
    /* La mission d'HQ ne vit que tant que son .miz est ouvert : à son démarrage le shell efface la clé, avant toute lecture et avant qu'un module s'ouvre */
    try {{ localStorage.removeItem('mission_snapshot_v1'); }} catch(e) {{}}
    suiteMigrateBriefing();                              /* le briefing sous son nom neutre, avant qu'un outil s'ouvre */
    suiteMigratePresets();                               /* les presets d'emport d'un état d'avant passent à leur bibliothèque, avant qu'un outil s'ouvre */
    initLang();
    /* Thème : lire localStorage */
    try {{
      var storedTheme = localStorage.getItem(KEY_THEME);
      if (storedTheme && THEMES[storedTheme]) {{
        document.body.setAttribute('data-theme', storedTheme);
        document.getElementById('theme-sel').value = storedTheme;
      }}
    }} catch(e) {{}}
    /* Appliquer thème courant (stamp, classif, foot-info) */
    var cur = document.body.getAttribute('data-theme') || 'cw-nato';
    setTheme(cur);
    applyI18n();
    updateFlagBtn();
    suiteBind();                                         /* la fenêtre du nom du fichier de travail */
    initToolbarMenus([['theme-sel', function() {{ return t('theme.sel'); }}]]);   /* la liste du thème au thème de la landing */

    /* Clics cartes : les six cartes des deux cadres (le Field Manual n'a pas de carte : sa touche est dans la barre) */
    ['hq', 'bg', 'rs', 'rp', 'dg', 'fc'].forEach(function(id) {{
      var card = document.getElementById('card-' + id);
      card.addEventListener('click', function() {{ openModule(id); }});
      card.addEventListener('keydown', function(e) {{
        if (e.key === 'Enter' || e.key === ' ') {{ e.preventDefault(); openModule(id); }}
      }});
    }});
    /* La barre du haut : le fichier de travail de la suite (Ouvrir…, Sauvegarder) et le Field Manual */
    document.getElementById('btn-work-open').addEventListener('click', function() {{ if (window.MP_WORK_OPEN) window.MP_WORK_OPEN(); }});
    document.getElementById('btn-work-save').addEventListener('click', function() {{ if (window.MP_WORK_SAVE) window.MP_WORK_SAVE(); }});
    document.getElementById('btn-fm').addEventListener('click', function() {{ openModule('fm'); }});
    /* Exemple ▾ : le menu à deux lignes, une par groupe */
    var exb = document.getElementById('btn-example');
    exb.addEventListener('click', function() {{ if (TBM.cur && TBM.cur.btn === exb) tbmClose(false); else exampleMenuOpen(exb); }});
    exb.addEventListener('keydown', function(e) {{ if (e.key === 'ArrowDown' && !TBM.cur) {{ e.preventDefault(); exampleMenuOpen(exb); }} }});
    /* Ctrl+S / Cmd+S quand le clavier est dans le shell = Sauvegarder (rien sous une fenêtre ou une liste ouverte ; jamais « Enregistrer la page sous ») */
    document.addEventListener('keydown', function(e) {{
      if (!(e.ctrlKey || e.metaKey) || e.altKey || e.shiftKey || (e.key !== 's' && e.key !== 'S')) return;
      e.preventDefault();
      if (document.querySelector('.ui-modal:not([hidden])') || TBM.cur) return;
      if (window.MP_WORK_SAVE) window.MP_WORK_SAVE();
    }});

    document.getElementById('flag-btn').addEventListener('click', toggleLang);
    /* Sync inter-contextes : thème + tampon wing (srcdoc même origine) */
    window.addEventListener('storage', function(e) {{
      if (e.key === KEY_THEME && e.newValue && THEMES[e.newValue]) {{ setTheme(e.newValue); }}
      else if (e.key === 'wing_config_v1') {{ refreshWingStamps(); }}
    }});

    /* Le toast relit la barre basse de l'outil ouvert à son affichage */
    var toastEl = mpToastEl();
    new MutationObserver(function() {{ if (toastEl.classList.contains('show')) toastPlace(); }}).observe(toastEl, {{ attributes: true, attributeFilter: ['class'] }});
  }}

  document.addEventListener('DOMContentLoaded', init);
</script>
</body>
</html>'''


def main():
    print('=== build_mission_plan.py — DCS Mission Plan shell ===')

    print('\n[0/3] Garde du module seul dans les sept modules…')
    check_shell_only_block()

    check_suite_colors()

    print('\n[1/3] Encodage modules HTML…')
    module_html_js = build_module_html_js(MODULES)

    print('\n[2/3] Encodage images tuiles…')
    tile_uris = build_tile_uris(MODULES)

    check_example_tooltips()
    suite_examples = read_suite_examples()
    print("  [OK] le menu Exemple ▾ des cinq outils : infobulle, libellé, deux lignes (mc puis fl), appel de MP_WORK_EXAMPLE par groupe (FR, EN)")

    print(f'\n[3/3] Génération {OUT_FILE}…')
    suite_examples_js = json.dumps(suite_examples, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
    html = build_html(module_html_js, tile_uris, suite_examples_js)
    # La garde du module seul ne figure pas dans le shell lui-même (hors des modules embarqués)
    shell_text = html.replace(module_html_js, '', 1)
    shell_only_body = build_shell_only_block().replace(SHELL_ONLY_BEGIN, '').replace(SHELL_ONLY_END, '').strip()
    for what, found in (('son marqueur de début', SHELL_ONLY_BEGIN in shell_text), ('son marqueur de fin', SHELL_ONLY_END in shell_text),
                        ('le corps du bloc', shell_only_body in shell_text), ('la balise data-lang-key', 'data-lang-key' in shell_text)):
        if found:
            raise SystemExit(f"[ERREUR] La garde du module seul figure dans le shell lui-même ({what}) — build arrêté")
    print('  [OK] Garde du module seul absente du shell lui-même')
    # Le fichier de travail : SUITE_KEYS contient toutes les clés de GS_CONTENT_KEYS (group_store_block.py), dans son ordre, puis celles du briefing et de Recon Station
    gs = re.search(r"const GS_CONTENT_KEYS = \[([^\]]*)\];", group_store_block.build_block())
    sk = re.search(r"const SUITE_KEYS = \[([^\]]*)\];", shell_text)
    if not gs or not sk:
        raise SystemExit("[ERREUR] GS_CONTENT_KEYS ou SUITE_KEYS introuvable — build arrêté")
    gs_keys = re.findall(r"'([^']+)'", gs.group(1))
    suite_keys = re.findall(r"'([^']+)'", sk.group(1))
    missing = [k for k in gs_keys if k not in suite_keys]
    if missing:
        raise SystemExit(f"[ERREUR] SUITE_KEYS ne contient pas toutes les clés de GS_CONTENT_KEYS (manque : {missing}) — build arrêté")
    if suite_keys[:len(gs_keys)] != gs_keys or len(suite_keys) != len(gs_keys) + 2:
        raise SystemExit("[ERREUR] SUITE_KEYS n'est pas GS_CONTENT_KEYS (dans son ordre) suivi des deux clés du briefing et de Recon Station — build arrêté")
    print(f'  [OK] SUITE_KEYS = les {len(gs_keys)} clés de GS_CONTENT_KEYS (dans son ordre) + {len(suite_keys) - len(gs_keys)}')
    # Les groupes de l'exemple : listes de clés disjointes, leur union avec les deux réglages est exactement SUITE_KEYS ; les outils des groupes sont ceux de EX_TOOLS
    sg = re.search(r"const SUITE_GROUPS = \{(.*?)\n\};", shell_text, re.S)
    if not sg:
        raise SystemExit("[ERREUR] SUITE_GROUPS introuvable — build arrêté")
    groups = {}
    for g in ('mc', 'fl'):
        m = re.search(g + r": \{ tools: \[([^\]]*)\], keys: \[([^\]]*)\] \}", sg.group(1))
        if not m:
            raise SystemExit(f"[ERREUR] SUITE_GROUPS : le groupe {g} est illisible — build arrêté")
        groups[g] = {'tools': re.findall(r"'([^']+)'", m.group(1)), 'keys': re.findall(r"'([^']+)'", m.group(2))}
        if sorted(groups[g]['tools']) != sorted(k for k, v in EX_TOOLS.items() if v == g):
            raise SystemExit(f"[ERREUR] SUITE_GROUPS : les outils du groupe {g} ne sont pas ceux des boutons Exemple — build arrêté")
    if set(groups['mc']['keys']) & set(groups['fl']['keys']):
        raise SystemExit("[ERREUR] SUITE_GROUPS : les clés des deux groupes ne sont pas disjointes — build arrêté")
    if len(groups['mc']['keys']) + len(groups['fl']['keys']) + 2 != len(suite_keys) or set(groups['mc']['keys']) | set(groups['fl']['keys']) | {'mp_units_v1', 'mp_nav_v1'} != set(suite_keys):
        raise SystemExit("[ERREUR] SUITE_GROUPS : l'union des deux groupes et de mp_units_v1, mp_nav_v1 n'est pas exactement SUITE_KEYS — build arrêté")
    check_suite_examples(suite_examples, {g: groups[g]['keys'] for g in groups})
    print('  [OK] groupes de l\'exemple : clés disjointes, union avec mp_units_v1 et mp_nav_v1 = SUITE_KEYS ; fichiers d\'exemple : format, Syria, mêmes clés FR et EN, chaque clé dans un groupe, valeurs JSON')
    # Les presets d'emport (fc_presets_v1) sont une bibliothèque personnelle, pas une clé de contenu : ni dans SUITE_KEYS, ni dans GS_CONTENT_KEYS, ni dans un groupe, ni dans un fichier d'exemple
    ex_keys = {k for lang in suite_examples for k in suite_examples[lang]['keys']}
    if 'fc_presets_v1' in suite_keys or 'fc_presets_v1' in gs_keys or 'fc_presets_v1' in groups['mc']['keys'] + groups['fl']['keys'] or 'fc_presets_v1' in ex_keys:
        raise SystemExit("[ERREUR] fc_presets_v1 est dans SUITE_KEYS, GS_CONTENT_KEYS, un groupe de l'exemple ou un fichier d'exemple : c'est une bibliothèque personnelle — build arrêté")
    # Le briefing sous son nom neutre : la clé neuve est dans SUITE_KEYS, l'ancien nom ne figure qu'une fois dans le shell (la constante des deux reprises) et le shell migre avant d'ouvrir un outil
    old_name = re.search(r"const SUITE_OLD_BRIEFING_KEY = '([^']+)'", shell_text)
    if 'briefing_state_v2' not in suite_keys or not old_name or old_name.group(1) in suite_keys or shell_text.count(old_name.group(1)) != 1:
        raise SystemExit("[ERREUR] le briefing n'est pas sous son nom neutre, ou l'ancien nom figure ailleurs que dans sa constante — build arrêté")
    init_head = html.split("function init() {", 1)[1].split("initLang();", 1)[0]
    if "suiteMigrateBriefing();" not in init_head or "suiteMigratePresets();" not in init_head:
        raise SystemExit("[ERREUR] init() ne migre pas le briefing et les presets avant initLang() — build arrêté")
    # La règle de fusion des presets est une seule fonction (suite_file_block.build_presets_merge) : une fois dans le shell, telle quelle ; le Flight Configurator la reprend et le dit à son build
    if shell_text.count(build_presets_merge()) != 1:
        raise SystemExit("[ERREUR] la fusion des presets ne figure pas une fois, telle quelle, dans le shell — build arrêté")
    print("  [OK] fc_presets_v1 hors de SUITE_KEYS, GS_CONTENT_KEYS, des groupes et des exemples ; briefing sous briefing_state_v2, ancien nom dans sa seule constante, migré en tête de init()")
    # Les textes de l'exemple : ceux de la table, dans l'accueil (I18N : menu, infobulle, libellé) et dans le toast
    for g in ('mc', 'fl'):
        for lang in ('fr', 'en'):
            for what, want in (('ex.' + g, EX_MENU[g]), ('work.example.' + g, EX_TOAST[g][lang]), ('ex.tip', EX_BTN_TIP[lang]), ('ex.btn', EX_BTN_LABEL[lang])):
                if shell_text.count(want) < 1:
                    raise SystemExit(f"[ERREUR] le shell ne porte pas le texte {what} ({lang}) de la table — build arrêté")
    # Le toast et les feuilles communes : tels quels dans le shell ; le script de ui_block n'y entre pas
    for what, found in (('le script du toast (messages_block)', shell_text.count(build_messages_block()) == 1),
                        ('la feuille du toast (messages_block)', shell_text.count(build_messages_css()) == 1),
                        ('la feuille de ui_block', shell_text.count(build_ui_css()) == 1),
                        ('le bloc du fichier de travail', shell_text.count(build_suite_file_block()) == 1),
                        ('la fenêtre du nom', shell_text.count(build_suite_file_html()) == 1),
                        ('les couleurs de la fenêtre du nom et du toast', shell_text.count(build_suite_file_css()) == 1)):
        if not found:
            raise SystemExit(f"[ERREUR] {what} ne figure pas une fois, tel quel, dans le shell — build arrêté")
    if 'function askConfirm' in shell_text or 'function uiConfirmEl' in shell_text:
        raise SystemExit("[ERREUR] le script de ui_block figure dans le shell (il n'en prend que la feuille) — build arrêté")
    print(f'  [OK] toast et feuille de ui_block identiques à leurs blocs ; le script de ui_block n\'est pas dans le shell (empreinte {ui_fingerprint()})')
    # Retour au hub : le clavier quitte l'outil fermé (sinon Ctrl+S irait à l'outil masqué et non à Sauvegarder de l'accueil)
    if "landing.focus({ preventScroll: true })" not in html:
        raise SystemExit("[ERREUR] goHub ne rend plus le clavier au hub")
    print('  [OK] goHub rend le clavier au hub')
    # La mission d'HQ ne survit pas au rechargement : la clé s'efface en tête de init(), avant tout autre geste
    if "function init() {\n    /* La mission d'HQ ne vit que tant que son .miz est ouvert" not in html or html.index("localStorage.removeItem('mission_snapshot_v1')") > html.index("initLang();\n    /* Thème"):
        raise SystemExit("[ERREUR] init() n'efface plus mission_snapshot_v1 en tête")
    print('  [OK] init() efface mission_snapshot_v1 en tête, avant toute lecture')

    out_path = os.path.join(SCRIPT_DIR, OUT_FILE)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(html)

    size_kb = os.path.getsize(out_path) // 1024
    print(f'\n✓ Fichier généré : {out_path}')
    print(f'  Taille : {size_kb} Ko')
    print('\n=== Build terminé ===')


if __name__ == '__main__':
    main()
