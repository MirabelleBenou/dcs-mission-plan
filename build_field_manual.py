#!/usr/bin/env python3
"""Build the DCS Field Manual HTML module — monofichier, offline, Mission Plan suite."""

import json
import os
import base64
import re
import subprocess
import sys
import tempfile

CONTRAST_CSS = r"""
/* MP-20 begin */
/* Contrastes (texte sous 18 px, 4,5 : 1 au moins) : couleur du texte seule, la palette commune ne bouge pas. */
:where(body[data-theme="cw-nato"]) .tb-brand-short { color: #8b9aaf; }
:where(body[data-theme="cw-nato"]) .tb-classif { color: #d4847b; }
:where(body[data-theme="cw-soviet"]) .tb-classif { color: #be7d7d; }
:where(body[data-theme="modern-nato"]) .tb-classif { color: #898989; }
:where(body[data-theme="modern-east"]) .tb-classif { color: #bd7979; }
/* MP-20 end */
"""

HERE = os.path.dirname(os.path.abspath(__file__))

APP_VERSION = '1.3.0'
MODULE_ID   = 'fm'

# ── Assets ──────────────────────────────────────────────────────────────────────

ASSETS_PATH = os.path.join(HERE, 'assets.json')
if not os.path.isfile(ASSETS_PATH):
    raise SystemExit(f"[ERREUR] Entrée manquante : {ASSETS_PATH} (assets.json attendu à la racine du dépôt)")
with open(ASSETS_PATH) as f:
    A = json.load(f)
print(f'✓ assets.json chargé depuis {ASSETS_PATH}')

def b64_font(key):
    return A.get(key, '')

# ── Images ──────────────────────────────────────────────────────────────────────

TILES_DIR = os.path.join(HERE, 'tiles')

def encode_image(filename):
    """Encode une image en data URI base64. Ne jamais redimensionner (règle REX)."""
    path = os.path.join(TILES_DIR, filename)
    if not os.path.isfile(path):
        raise SystemExit(f"[ERREUR] Entrée manquante : {path} (tuile {filename} attendue dans tiles/)")
    with open(path, 'rb') as f:
        b64 = base64.b64encode(f.read()).decode('ascii')
    ext = filename.rsplit('.', 1)[-1].lower()
    mime = 'image/webp' if ext == 'webp' else f'image/{ext}'
    return f'data:{mime};base64,{b64}'

RS_TILE    = encode_image('rs.webp')
FM_COVER   = encode_image('fm_cover.webp')
HQ_TILE    = encode_image('hq.webp')
BG_TILE    = encode_image('bg.webp')
DG_TILE    = encode_image('kg.webp')
RP_TILE    = encode_image('rp.webp')
FC_TILE    = encode_image('fc.webp')

if RS_TILE:
    print(f'✓ rs.webp embarqué ({len(RS_TILE)//1024} Ko base64)')
else:
    print('⚠ rs.webp introuvable', file=sys.stderr)

if HQ_TILE:
    print(f'✓ hq.webp embarqué ({len(HQ_TILE)//1024} Ko base64)')
else:
    print('⚠ hq.webp introuvable', file=sys.stderr)

if BG_TILE:
    print(f'✓ bg.webp embarqué ({len(BG_TILE)//1024} Ko base64)')
else:
    print('⚠ bg.webp introuvable', file=sys.stderr)

if DG_TILE:
    print(f'✓ kg.webp embarqué ({len(DG_TILE)//1024} Ko base64)')
else:
    print('⚠ kg.webp introuvable', file=sys.stderr)

if RP_TILE:
    print(f'✓ rp.webp embarqué ({len(RP_TILE)//1024} Ko base64)')
else:
    print('⚠ rp.webp introuvable', file=sys.stderr)

if FM_COVER:
    print(f'✓ fm_cover.webp embarqué ({len(FM_COVER)//1024} Ko base64)')
else:
    print('⚠ fm_cover.webp absent — fallback couverture SVG/typo activé', file=sys.stderr)

# ── Kraft SVG variants (identique à Recon Station) ──────────────────────────────

def _kraft_variant(b64svg, bg_color, grain_color):
    if not b64svg:
        return ''
    svg_bytes = base64.b64decode(b64svg)
    svg_str   = svg_bytes.decode('utf-8')
    svg_str   = svg_str.replace('#d6c7a3', bg_color).replace('#ccbe99', grain_color)
    return base64.b64encode(svg_str.encode('utf-8')).decode('ascii')

KRAFT_RAW   = A.get('KRAFT_SVG', '')
KRAFT_NATO  = _kraft_variant(KRAFT_RAW, '#d6c7a3', '#ccbe99')
KRAFT_SOV   = _kraft_variant(KRAFT_RAW, '#d4c075', '#c8b060')
KRAFT_MNATO = _kraft_variant(KRAFT_RAW, '#e4dfd2', '#d8d4c8')
KRAFT_MEAST = _kraft_variant(KRAFT_RAW, '#c8c1b2', '#bcb5a6')

# ── Polices ──────────────────────────────────────────────────────────────────────

SPECIAL_ELITE_B64 = b64_font('SPECIAL_ELITE')
STARDOS_400_B64   = b64_font('STARDOS_400')
STARDOS_700_B64   = b64_font('STARDOS_700')
OSWALD_500_B64    = b64_font('OSWALD_500')
OSWALD_700_B64    = b64_font('OSWALD_700')
ROBOTO_MONO_400_B64 = b64_font('ROBOTO_MONO_400')

def font_face_css():
    """Génère les @font-face. Fallback CDN si base64 absent."""
    parts = []
    if SPECIAL_ELITE_B64:
        parts.append(f"""@font-face {{
  font-family: 'Special Elite';
  font-weight: 400;
  font-display: swap;
  src: url('data:font/woff2;base64,{SPECIAL_ELITE_B64}') format('woff2');
}}""")
    else:
        parts.append("/* Special Elite : fallback CDN */")

    # Stardos Stencil 400 : le tampon de décor de la barre
    if STARDOS_400_B64:
        parts.append(f"""@font-face {{
  font-family: 'Stardos Stencil';
  font-weight: 400;
  font-display: swap;
  src: url('data:font/woff2;base64,{STARDOS_400_B64}') format('woff2');
}}""")

    if STARDOS_700_B64:
        parts.append(f"""@font-face {{
  font-family: 'Stardos Stencil';
  font-weight: 700;
  font-display: swap;
  src: url('data:font/woff2;base64,{STARDOS_700_B64}') format('woff2');
}}""")
    else:
        parts.append("/* Stardos Stencil : fallback CDN */")

    if OSWALD_500_B64:
        parts.append(f"""@font-face {{
  font-family: 'Oswald';
  font-weight: 500;
  font-display: swap;
  src: url('data:font/woff2;base64,{OSWALD_500_B64}') format('woff2');
}}""")
    if OSWALD_700_B64:
        parts.append(f"""@font-face {{
  font-family: 'Oswald';
  font-weight: 700;
  font-display: swap;
  src: url('data:font/woff2;base64,{OSWALD_700_B64}') format('woff2');
}}""")

    # Roboto Mono 400 : le bouton retour que le shell ajoute à la barre l'emploie ; une police n'apparaît jamais sans sa face embarquée (R295)
    if ROBOTO_MONO_400_B64:
        parts.append(f"""@font-face {{
  font-family: 'Roboto Mono';
  font-weight: 400;
  font-display: swap;
  src: url('data:font/woff2;base64,{ROBOTO_MONO_400_B64}') format('woff2');
}}""")
    return '\n'.join(parts)

FONT_CDN = ''   # aucune police distante : toutes sont embarquées (R295)

# ── Couverture HTML ──────────────────────────────────────────────────────────────

if FM_COVER:
    COVER_HTML = f"""<div class="cover-wrap">
        <div class="cover-img-box" style="background-image:url('{FM_COVER}')">
          <div class="cover-overlay">
            <span class="cover-suite">DCS · MISSION PLAN</span>
            <span class="cover-ref">FM-MP-01</span>
          </div>
        </div>
      </div>"""
else:
    COVER_HTML = """<div class="cover-wrap cover-svg">
        <div class="cover-svg-inner">
          <div class="cover-classif-top">DECLASSIFIED — UNCLASSIFIED</div>
          <div class="cover-title-main">FIELD MANUAL</div>
          <div class="cover-title-sub">DCS · MISSION PLAN</div>
          <div class="cover-ref-box">FM-MP-01</div>
          <div class="cover-stamp">APPROVED FOR PUBLIC RELEASE</div>
        </div>
      </div>"""

# ── RS tile src (fallback placeholder) ──────────────────────────────────────────

RS_TILE_SRC = RS_TILE if RS_TILE else "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"
HQ_TILE_SRC = HQ_TILE if HQ_TILE else "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"
BG_TILE_SRC = BG_TILE if BG_TILE else "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"
DG_TILE_SRC = DG_TILE if DG_TILE else "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"
RP_TILE_SRC = RP_TILE if RP_TILE else "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"
FC_TILE_SRC = FC_TILE

# ── Schémas générés (BG « Ce qui alimente quoi » ; DG figure 2) ──────────────────
# Règle de lisibilité : la couleur d'un module marque (trait, aplat à 20 %), l'encre écrit.

import html as _html

_NBSP_FINE = ' '   # espace fine insécable (typographie française)

def _n(v):
    return f'{v:g}'

def _esc(s):
    return _html.escape(s, quote=False)

def sv_text(x, y, size, fr, en=None, anchor='middle', op=None, ls=None, cls=None, dx=None):
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
        return f'<text{a}>{_esc(txt)}</text>'
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
    return (f'<defs><marker id="{marker}" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto">'
            f'<path d="M0,0 L7,3.5 L0,7 Z" fill="currentColor" opacity=".8"/></marker></defs>')

def sv_title(fr, en, y, y_rule):
    return (sv_text(360, y, 13, fr, en, op=.9, ls=3) + '\n          '
            f'<line x1="120" y1="{_n(y_rule)}" x2="600" y2="{_n(y_rule)}" stroke="currentColor" stroke-width=".6" opacity=".3"/>')

def _build_bg_svg():
    """Briefing Generator — « Ce qui alimente quoi » (viewBox 720 × 425), complété de la Datacard
    et des étiquettes S / A (Standard / Avancé)."""
    M = 'bm'
    T = sv_text
    o = []
    o.append('<svg viewBox="0 0 720 425" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Ce qui alimente quoi" data-aria-fr="Ce qui alimente quoi" data-aria-en="What feeds what">')
    o.append('          ' + sv_defs(M))
    o.append('          ' + sv_title('CE QUI ALIMENTE QUOI', 'WHAT FEEDS WHAT', 24, 32))
    # rangée du haut
    o.append('          ' + sv_box(16, 66, 96, 42, 'hq'))
    o.append('          ' + T(64, 84, 12, 'HQ'))
    o.append('          ' + T(64, 98, 8, 'wing_config', op=.9))
    o.append('          ' + sv_box(156, 66, 96, 42))
    o.append('          ' + T(204, 91, 11, 'Escadrons', 'Squadrons'))
    o.append('          ' + sv_tag(156, 66, 96, 'S·A', 'S·A'))
    o.append('          ' + sv_box(296, 66, 96, 42, 'bg'))
    o.append('          ' + T(344, 84, 11, 'Missions'))
    o.append('          ' + T(344, 98, 8, 'groupes', 'groups', op=.9))
    o.append('          ' + sv_tag(296, 66, 96, 'S·A', 'S·A'))
    o.append('          ' + sv_box(436, 66, 96, 42))
    o.append('          ' + T(484, 84, 10, 'Appareil', 'Aircraft'))
    o.append('          ' + T(484, 98, 8, 'sélectionné', 'selected', op=.9))
    o.append('          ' + sv_tag(436, 66, 96, 'S·A', 'S·A'))
    o.append('          ' + sv_box(576, 66, 100, 42))
    o.append('          ' + T(626, 91, 10.5, 'Plan radio', 'Radio plan'))
    o.append('          ' + sv_tag(576, 66, 100, 'S·A', 'S·A'))
    # flèches de la rangée du haut
    o.append('          ' + sv_line(112, 87, 154, 87, M))
    o.append('          ' + T(133, 80, 8, 'identité', 'identity', op=.9))
    o.append('          ' + sv_line(252, 87, 294, 87, M))
    o.append('          ' + T(273, 80, 8, 'escadron', 'squadron', op=.9))
    o.append('          ' + sv_line(392, 87, 434, 87, M))
    o.append('          ' + T(413, 80, 8, 'type', op=.9))
    o.append('          ' + sv_line(532, 87, 574, 87, M))
    o.append('          ' + T(553, 80, 8, 'réf radio', 'radio ref', op=.9))
    # équipage
    o.append('          ' + sv_box(250, 190, 140, 42))
    o.append('          ' + T(320, 215, 11, 'Équipage', 'Crew'))
    o.append('          ' + sv_tag(250, 190, 140, 'A', 'A'))
    o.append('          ' + sv_path('M204,108 C204,160 270,165 280,189', M, op=.8))
    o.append('          ' + T(196, 150, 8, 'callsign → indicatifs', 'callsign → call signs', anchor='end', op=.9))
    o.append('          ' + sv_path('M344,108 C344,150 350,160 350,189', M, op=.8))
    o.append('          ' + T(356, 150, 8, 'groupes liés', 'linked groups', anchor='start', op=.9))
    # aérodromes, METAR
    o.append('          ' + sv_box(40, 296, 150, 42))
    o.append('          ' + T(115, 315, 10.5, 'Aérodromes / FARP', 'Airfields / FARPs'))
    o.append('          ' + T(115, 329, 8, 'ICAO', op=.9))
    o.append('          ' + sv_tag(40, 296, 150, 'S·A', 'S·A'))
    o.append('          ' + sv_box(250, 296, 120, 42))
    o.append('          ' + T(310, 321, 11, 'METAR'))
    o.append('          ' + sv_tag(250, 296, 120, 'S·A', 'S·A'))
    o.append('          ' + sv_line(190, 317, 248, 317, M))
    o.append('          ' + T(219, 310, 8, 'pré-rempli', 'pre-filled', op=.9))
    # métadonnées (trait plein)
    o.append('          ' + sv_box(470, 296, 160, 42))
    o.append('          ' + T(550, 315, 10.5, 'Métadonnées', 'Metadata'))
    o.append('          ' + T(550, 329, 8, 'en-têtes & pieds de page', 'page headers & footers', op=.9))
    o.append('          ' + sv_tag(470, 296, 160, 'S·A', 'S·A'))
    # carte, menaces, cibles (Standard et Avancé)
    o.append('          ' + sv_box(20, 190, 170, 42))
    o.append('          ' + T(105, 215, 10.5, 'Carte · menaces · cibles', 'Map · threats · targets'))
    o.append('          ' + sv_tag(20, 190, 170, 'S·A', 'S·A'))
    # boîtes neuves
    o.append('          ' + sv_box(40, 360, 190, 36))
    o.append('          ' + T(135, 382, 10, 'Couverture · charts · annexes', 'Cover · charts · annexes'))
    o.append('          ' + sv_tag(40, 360, 190, 'A', 'A'))
    o.append('          ' + sv_box(250, 360, 120, 36))
    o.append('          ' + T(310, 382, 11, 'Photos'))
    o.append('          ' + sv_tag(250, 360, 120, 'S', 'S'))
    # Datacard Generator et les quatre flèches tiretées
    o.append('          ' + sv_box(470, 190, 170, 42, 'dg'))
    o.append('          ' + T(555, 208, 11, 'Datacard Generator'))
    o.append('          ' + T(555, 222, 8, 'une datacard par groupe', 'one datacard per group', op=.9))
    o.append('          ' + sv_path('M392,100 C432,108 488,140 500,188', M, dashed=True))
    o.append('          ' + T(458, 140, 8, 'groupes', 'groups', anchor='end', op=.9))
    o.append('          ' + sv_line(626, 108, 620, 188, M, dashed=True))
    o.append('          ' + T(628, 152, 8, 'fréquences', 'frequencies', anchor='start', op=.9))
    o.append('          ' + sv_line(390, 211, 468, 211, M, dashed=True))
    o.append('          ' + T(429, 204, 8, 'équipage', 'crew', op=.9))
    o.append('          ' + sv_path('M370,306 C440,300 500,268 520,234', M, dashed=True))
    o.append('          ' + T(536, 266, 8, 'METAR décodé', 'decoded METAR', anchor='start', op=.9))
    # la clé
    o.append('          ' + sv_pill(470, 364, 13, 13, 'S', 'S'))
    o.append('          ' + T(489, 374, 9, 'Standard', 'Standard', anchor='start'))
    o.append('          ' + sv_pill(470, 384, 13, 13, 'A', 'A'))
    o.append('          ' + T(489, 394, 9, 'Avancé', 'Advanced', anchor='start'))
    o.append('          ' + T(470, 414, 8, f'Tireté{_NBSP_FINE}: lu par le Datacard Generator',
                              'Dashed: read by the Datacard Generator', anchor='start', op=.9))
    o.append('        </svg>')
    return '\n'.join(o)

def _build_dg_feed_svg():
    """Datacard Generator — figure 2 « Ce qui alimente la datacard » (viewBox 720 × 380)."""
    M = 'dgf'
    T = sv_text
    o = []
    o.append('<svg viewBox="0 0 720 380" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Ce qui alimente la datacard" data-aria-fr="Ce qui alimente la datacard" data-aria-en="What feeds the datacard">')
    o.append('          ' + sv_defs(M))
    o.append('          ' + sv_title('CE QUI ALIMENTE LA DATACARD', 'WHAT FEEDS THE DATACARD', 26, 34))
    # Briefing Generator et ses huit lignes
    o.append('          ' + sv_box(24, 60, 220, 200, 'bg'))
    o.append('          ' + T(134, 80, 11, 'Briefing Generator'))
    lines = [
        ('méta (opération, mission, date)', 'meta (operation, mission, date)'),
        (f'groupes{_NBSP_FINE}: indicatif, appareil, tâche', 'groups: callsign, aircraft, task'),
        ('objectif et étapes', 'objective and steps'),
        ('équipage', 'crew'),
        ('radio', 'radio'),
        ('terrains, départ marqué DEP', 'airfields, departure marked DEP'),
        ('METAR, décodé', 'METAR, decoded'),
        ('menaces · notes', 'threats · notes'),
    ]
    for i, (fr, en) in enumerate(lines):
        o.append('          ' + T(40, 102 + 20 * i, 9, fr, en, anchor='start', op=.95))
    # saisie à la main
    o.append('          ' + sv_box(24, 282, 220, 56))
    o.append('          ' + T(134, 306, 11, 'Saisie à la main', 'Typed in by hand'))
    o.append('          ' + T(134, 322, 8, 'horaires · navigation · carburant · emport',
                              'times · navigation · fuel · loadout', op=.9))
    # HQ (.miz), tireté
    o.append('          ' + sv_box(320, 56, 150, 48, dashed=True))
    o.append('          ' + T(395, 76, 11, 'HQ (.miz)'))
    o.append('          ' + T(395, 92, 8, 'navigation · emport — à venir', 'navigation · loadout — coming', op=.9))
    # Datacard Generator
    o.append('          ' + sv_box(320, 168, 150, 60, 'dg'))
    o.append('          ' + T(395, 195, 11, 'Datacard Generator'))
    o.append('          ' + T(395, 212, 8, 'une datacard par groupe', 'one datacard per group', op=.9))
    # flèches vers la Datacard
    o.append('          ' + sv_line(244, 170, 318, 192, M))
    o.append('          ' + T(282, 150, 8, 'un groupe =', 'one group =', op=.9))
    o.append('          ' + T(282, 160, 8, 'une datacard', 'one datacard', op=.9))
    o.append('          ' + sv_path('M244,306 C300,306 330,262 350,230', M))
    o.append('          ' + sv_line(395, 104, 395, 166, M, dashed=True))
    o.append('          ' + T(401, 140, 8, 'à venir', 'coming', anchor='start', op=.9))
    # Route Planner (trait plein), sous le Datacard Generator
    o.append('          ' + sv_box(380, 282, 140, 44, 'rp'))
    o.append('          ' + T(450, 300, 11, 'Route Planner'))
    o.append('          ' + T(450, 315, 8, 'navigation · points de réf.', 'navigation · reference points', op=.9))
    o.append('          ' + sv_line(450, 282, 450, 230, M))
    # sorties
    outs = [
        (112, 'PNG · kneeboard DCS', 'PNG · DCS kneeboard', '2 000 × 2 828 px', '2,000 × 2,828 px'),
        (178, 'PDF · impression', 'PDF · printing', 'une page A4 par page', 'one A4 sheet per page'),
        (244, 'JSON · archive, partage', 'JSON · archive, share', None, None),
    ]
    for (y, tfr, ten, sfr, sen) in outs:
        o.append('          ' + sv_box(540, y, 160, 40))
        if sfr:
            o.append('          ' + T(620, y + 17, 11, tfr, ten))
            o.append('          ' + T(620, y + 31, 8, sfr, sen, op=.9))
        else:
            o.append('          ' + T(620, y + 24, 11, tfr, ten))
    o.append('          ' + sv_path('M470,188 C505,188 505,132 538,132', M))
    o.append('          ' + sv_line(470, 198, 538, 198, M))
    o.append('          ' + sv_path('M470,208 C505,208 505,264 538,264', M))
    # note
    o.append('          ' + T(360, 360, 9, f'Le Briefing Generator ne connaît pas la datacard{_NBSP_FINE}: la lecture va dans un seul sens.',
                              'The Briefing Generator knows nothing of the datacard: reading goes one way only.', op=.9))
    o.append('        </svg>')
    return '\n'.join(o)

def _build_rp_screen_svg():
    """Route Planner — figure 1 « L’écran du Route Planner » (viewBox 720 × 352) : un schéma, pas une capture."""
    M = 'rps'
    T = sv_text
    A = '#7ac97a'
    o = []
    o.append('<svg viewBox="0 0 720 352" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="L’écran du Route Planner" data-aria-fr="L’écran du Route Planner" data-aria-en="The Route Planner screen">')
    o.append('          ' + sv_defs(M))
    o.append('          ' + sv_title('L’ÉCRAN DU ROUTE PLANNER', 'THE ROUTE PLANNER SCREEN', 24, 32))
    # la barre du haut
    o.append('          ' + sv_box(110, 48, 500, 26))
    o.append('          ' + T(118, 64.5, 8.5, 'R·P', anchor='start', ls=1))
    o.append('          ' + T(146, 64.5, 8, 'Affichage ▾', 'Display ▾', anchor='start'))
    o.append('          ' + T(208, 64.5, 8, 'Théâtre ▾', 'Theatre ▾', anchor='start'))
    o.append('          ' + T(262, 64.5, 8, 'Ouvrir ▾ · Sauvegarder ▾ · Exporter ▾ · Exemple · Effacer',
                              'Open ▾ · Save ▾ · Export ▾ · Example · Clear', anchor='start'))
    # le panneau et ses sections
    o.append('          ' + sv_box(110, 80, 160, 260))
    secs = [
        (86, 112, 'ROUTE', 'ROUTE', 3, 18),
        (204, 26, 'POINTS DE RÉFÉRENCE', 'REFERENCE POINTS', 1, 0),
        (234, 20, 'CALQUES', 'LAYERS', 0, 0),
        (258, 76, 'NAVIGATION', 'NAVIGATION', 3, 0),
    ]
    for (y, h, fr, en, rows, dy) in secs:
        o.append('          ' + f'<rect x="116" y="{y}" width="148" height="{h}" fill="none" stroke="currentColor" stroke-width="1" opacity=".75"/>')
        o.append('          ' + T(121, y + 10, 7, fr, en, anchor='start', ls=1, op=.95))
        for k in range(rows):
            o.append('          ' + f'<line x1="122" y1="{y + 20 + dy + 9 * k}" x2="258" y2="{y + 20 + dy + 9 * k}" stroke="currentColor" stroke-width="1" opacity=".3"/>')
    # la ligne de sélection des routes : « 1 · FOOTHOLD ▾ », « + », « … »
    o.append('          ' + sv_box(122, 98, 100, 13))
    o.append('          ' + T(128, 107, 6.5, '1 · FOOTHOLD ▾', anchor='start'))
    o.append('          ' + sv_box(226, 98, 14, 13))
    o.append('          ' + T(233, 107, 7, '+'))
    o.append('          ' + sv_box(244, 98, 14, 13))
    o.append('          ' + T(251, 107, 7, '…'))
    # la carte, sa grille
    o.append('          ' + sv_box(276, 80, 334, 260))
    for x in (336, 396, 456, 516, 576):
        o.append('          ' + f'<line x1="{x}" y1="81" x2="{x}" y2="339" stroke="currentColor" stroke-width=".8" opacity=".18"/>')
    for y in (130, 180, 230, 280, 330):
        o.append('          ' + f'<line x1="277" y1="{y}" x2="609" y2="{y}" stroke="currentColor" stroke-width=".8" opacity=".18"/>')
    # la loupe de la recherche
    o.append('          ' + '<rect class="sv-box" x="284" y="88" width="16" height="16" rx="2" stroke="currentColor" stroke-width="1"/>')
    o.append('          ' + '<circle cx="291" cy="95" r="3.6" fill="none" stroke="currentColor" stroke-width="1.3"/>')
    o.append('          ' + '<line x1="293.6" y1="97.6" x2="297" y2="101" stroke="currentColor" stroke-width="1.3"/>')
    # les quatre modes de toucher, en haut à droite de la carte
    modes = [('Point', 'Waypoint'), ('Réf.', 'Ref.'), ('Lire', 'Read'), ('Dessin', 'Draw')]
    for i, (fr, en) in enumerate(modes):
        x = 444 + 40 * i
        o.append('          ' + sv_box(x, 88, 40, 16, 'rp' if i == 0 else None))
        o.append('          ' + T(x + 20, 99, 7, fr, en))
    # la route : quatre points, une référence, une boîte de branche
    pts = [(322, 296), (380, 196), (496, 222), (566, 146)]
    o.append('          ' + '<polyline points="' + ' '.join(f'{x},{y}' for x, y in pts) +
             f'" fill="none" stroke="{A}" stroke-width="3" stroke-linejoin="round"/>')
    for i, (x, y) in enumerate(pts):
        o.append('          ' + f'<circle cx="{x}" cy="{y}" r="7" class="sv-box" stroke="currentColor" stroke-width="1.6"/>')
        o.append('          ' + T(x, y + 2.8, 7.5, str(i)))
    o.append('          ' + '<rect x="514.5" y="284.5" width="11" height="11" transform="rotate(45 520 290)" fill="currentColor"/>')
    o.append('          ' + sv_text(520, 292.8, 7, 'A', cls='sv-pill-t'))
    # la boîte de branche, en maison, sous la branche 1 → 2
    o.append('          ' + '<path class="sv-box" d="M416,240 L438,230 L460,240 L460,266 L416,266 Z" stroke="currentColor" stroke-width="1.2"/>')
    o.append('          ' + T(438, 250, 6.5, '094°V', '094°T'))
    o.append('          ' + T(438, 260, 6.5, '12,4 km', '12.4 km'))
    # libellés, à gauche
    o.append('          ' + T(102, 124, 10, 'Panneau', 'Panel', anchor='end'))
    o.append('          ' + sv_line(105, 121, 128, 121, M))
    o.append('          ' + T(102, 178, 10, 'Sorties', 'Hand-offs', anchor='end'))
    o.append('          ' + sv_line(105, 175, 120, 175, M))
    # libellés, à droite
    o.append('          ' + T(622, 64, 10, 'Barre du haut', 'Top bar', anchor='start'))
    o.append('          ' + sv_line(618, 61, 596, 61, M))
    o.append('          ' + T(622, 99, 10, 'Modes de toucher', 'Tap modes', anchor='start'))
    o.append('          ' + sv_line(620, 96, 606, 96, M))
    o.append('          ' + T(622, 152, 10, 'Route', anchor='start'))
    o.append('          ' + sv_line(618, 149, 576, 147, M))
    o.append('          ' + T(622, 255, 10, 'Boîte', 'Leg box', anchor='start'))
    o.append('          ' + T(622, 267, 10, 'de branche', 'per leg', anchor='start'))
    o.append('          ' + sv_line(618, 258, 463, 258, M))
    o.append('          ' + T(622, 312, 10, 'Carte', 'Map', anchor='start'))
    o.append('          ' + sv_line(618, 309, 600, 309, M))
    o.append('        </svg>')
    return '\n'.join(o)


def _build_rp_feed_svg():
    """Route Planner — figure 2 « Ce qui entre dans le Route Planner, et ce qui en sort » (viewBox 720 × 360)."""
    M = 'rpf'
    T = sv_text
    o = []
    o.append('<svg viewBox="0 0 720 360" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Ce qui entre dans le Route Planner, et ce qui en sort" data-aria-fr="Ce qui entre dans le Route Planner, et ce qui en sort" data-aria-en="What goes into the Route Planner, and what comes out">')
    o.append('          ' + sv_defs(M))
    o.append('          ' + sv_title('CE QUI ENTRE, CE QUI SORT', 'WHAT GOES IN, WHAT COMES OUT', 24, 32))
    o.append('          ' + T(116, 52, 9, 'ENTRE', 'IN', op=.8, ls=2))
    o.append('          ' + T(604, 52, 9, 'SORT', 'OUT', op=.8, ls=2))
    ins = [
        (62, None, 'Route JSON', 'Route JSON', 'route · réf. · calques', 'route · ref. · layers'),
        (116, None, 'Route Tool de DCS', 'DCS Route Tool', '<théâtre>.lua', '<theatre>.lua'),
        (170, None, 'CombatFlite (.cf)', 'CombatFlite (.cf)', 'calques', 'layers'),
        (224, 'hq', 'HQ', 'HQ', 'année de la mission → déclinaison', 'mission year → variation'),
        (278, None, 'Airfield Charts', 'Airfield Charts', 'fiches des terrains', 'airfield chart sheets'),
    ]
    for (y, mod, tfr, ten, sfr, sen) in ins:
        o.append('          ' + sv_box(16, y, 200, 42, mod))
        o.append('          ' + T(116, y + 18, 11, tfr, ten))
        o.append('          ' + T(116, y + 32, 8, sfr, sen, op=.9))
    # le Route Planner
    o.append('          ' + sv_box(300, 140, 120, 108, 'rp'))
    o.append('          ' + T(360, 188, 12, 'Route'))
    o.append('          ' + T(360, 204, 12, 'Planner'))
    # flèches d’entrée
    for (y, ty) in ((83, 158), (137, 176), (191, 194), (245, 212), (299, 230)):
        o.append('          ' + sv_path(f'M216,{y} C258,{y} 258,{ty} 298,{ty}', M))
    outs = [
        (74, 'dg', 'Datacard Generator', 'Datacard Generator', 'navigation · points de réf.', 'navigation · reference points'),
        (138, 'bg', 'Briefing Generator', 'Briefing Generator', 'image de la carte', 'map image'),
        (202, None, 'Route Tool de DCS', 'DCS Route Tool', '<théâtre>.lua', '<theatre>.lua'),
        (266, None, 'JSON', 'JSON', 'route · réf. · calques', 'route · ref. · layers'),
    ]
    for (y, mod, tfr, ten, sfr, sen) in outs:
        o.append('          ' + sv_box(504, y, 200, 42, mod))
        o.append('          ' + T(604, y + 18, 11, tfr, ten))
        o.append('          ' + T(604, y + 32, 8, sfr, sen, op=.9))
    for (y, fy) in ((95, 164), (159, 184), (223, 204), (287, 224)):
        o.append('          ' + sv_path(f'M420,{fy} C462,{fy} 462,{y} 502,{y}', M))
    # note
    o.append('          ' + T(360, 346, 9, f'Hors de la suite{_NBSP_FINE}: la route reste dans le navigateur, la carte s’enregistre en image.',
                              'Outside the suite: the route stays in the browser, the map is saved as an image.', op=.9))
    o.append('        </svg>')
    return '\n'.join(o)


BG_SVG = _build_bg_svg()
DG_FEED_SVG = _build_dg_feed_svg()
RP_SCREEN_SVG = _build_rp_screen_svg()
RP_FEED_SVG = _build_rp_feed_svg()

BG_LEGEND_FR = (f'Fig. 1 — Comment les saisies d’une section alimentent les autres — et la datacard. '
                f'S{_NBSP_FINE}: saisi en Standard{_NBSP_FINE}; A{_NBSP_FINE}: en Avancé{_NBSP_FINE}; S·A{_NBSP_FINE}: dans les deux.')
BG_LEGEND_EN = ('Fig. 1 — How entries in one section feed the others — and the datacard. '
                'S: entered in Standard; A: in Advanced; S·A: in both.')

# ── CSS additionnel : boîtes de schéma, zoom ─────────────────────────────────────

FM_EXTRA_CSS = r'''
/* ── SCHÉMAS : la couleur du module marque, l'encre écrit ── */
.sv-box {
  fill: var(--paper-light);
}
.sv-m-hq { fill: color-mix(in srgb, #4FB286 20%, var(--paper-light)); stroke: #4FB286; }
.sv-m-bg { fill: color-mix(in srgb, #c0892a 20%, var(--paper-light)); stroke: #c0892a; }
.sv-m-rs { fill: color-mix(in srgb, #C95A9C 20%, var(--paper-light)); stroke: #C95A9C; }
.sv-m-dg { fill: color-mix(in srgb, #4f7a8e 20%, var(--paper-light)); stroke: #4f7a8e; }
.sv-m-rp { fill: color-mix(in srgb, #7ac97a 20%, var(--paper-light)); stroke: #7ac97a; }
.sv-pill { fill: var(--olive-dark); }
.sv-pill-t { fill: var(--paper-light); }
.fm-schema.tall svg { max-height: 425px; }

/* ── ZOOM : image ou schéma ouvert plein écran ── */
.fm-zoom-host { position: relative; }
[data-zoomable] { cursor: zoom-in; }
[data-zoomable]:focus-visible {
  outline: 2px solid var(--amber);
  outline-offset: 2px;
}
.fm-hero-img[data-zoomable]:focus-visible,
.cover-img-box[data-zoomable]:focus-visible { outline-offset: -3px; }
.fm-zoom-badge {
  position: absolute;
  top: 8px; right: 8px;
  z-index: 3;
  width: 26px; height: 26px;
  border-radius: 3px;
  background: rgba(26, 30, 16, .66);
  color: #f0e8d0;
  font-family: system-ui, 'Segoe UI Symbol', 'DejaVu Sans', sans-serif;
  font-size: 15px;
  line-height: 26px;
  text-align: center;
  opacity: .72;
  pointer-events: none;
  transition: opacity .12s;
}
.fm-zoom-badge::after { content: "\2922"; }
.fm-hero > .fm-zoom-badge { right: 38px; }
.fm-zoom-host:hover > .fm-zoom-badge,
.fm-zoom-host:focus-within > .fm-zoom-badge { opacity: 1; }

body.zm-open #fm-root { overflow: hidden; }
.zm {
  position: fixed;
  inset: 0;
  z-index: 5000;
  background: rgba(0, 0, 0, .94);
  color: var(--paper);
  font-family: var(--f-ui);
}
.zm[hidden] { display: none !important; }
.zm-stage {
  position: absolute;
  inset: 0;
  overflow: hidden;
  touch-action: none;
  overscroll-behavior: none;
  -webkit-user-select: none;
  user-select: none;
  cursor: default;
}
.zm.zoomed .zm-stage { cursor: grab; }
.zm.zoomed .zm-stage:active { cursor: grabbing; }
.zm-box {
  position: absolute;
  left: 0; top: 0;
  color: var(--ink);
  font-family: var(--f-typewriter);
  will-change: transform;
}
.zm-box img {
  display: block;
  width: 100%;
  height: auto;
  -webkit-user-drag: none;
  box-shadow: 0 0 0 1px var(--khaki), 0 10px 40px rgba(0, 0, 0, .6);
}
.zm-box .fm-schema {
  margin: 0;
  border: 0;
  padding: calc(20px * var(--zs, 1));
  background-color: var(--paper);
  background-image: linear-gradient(rgba(0, 0, 0, .10), rgba(0, 0, 0, .10)), var(--kraft-bg);
  background-size: auto, 400px 566px;
  box-shadow: 0 0 0 1px var(--khaki), 0 10px 40px rgba(0, 0, 0, .6);
}
.zm-box .fm-schema svg { max-height: none; width: 100%; height: auto; }
.zm-box .fm-schema-legend {
  margin-top: calc(10px * var(--zs, 1));
  font-size: calc(10px * var(--zs, 1));
  letter-spacing: calc(1.5px * var(--zs, 1));
}
.zm-bar {
  position: absolute;
  left: 50%;
  bottom: max(14px, env(safe-area-inset-bottom));
  transform: translateX(-50%);
  display: flex;
  gap: 8px;
  z-index: 2;
}
.zm-btn {
  min-width: 44px;
  height: 44px;
  padding: 0 14px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-family: var(--f-ui);
  font-size: 13px;
  letter-spacing: 2px;
  text-transform: uppercase;
  line-height: 1;
  color: var(--paper);
  background: linear-gradient(180deg, var(--olive-dark) 0%, var(--olive-deep) 100%);
  border: 1px solid var(--khaki);
  border-radius: 0;
  cursor: pointer;
  box-shadow: 0 2px 10px rgba(0, 0, 0, .5);
}
.zm-btn:hover { background: var(--olive); border-color: var(--fm-accent); }
.zm-btn:focus-visible { background: var(--olive); }
.zm-sym { width: 44px; padding: 0; font-size: 24px; letter-spacing: 0; text-transform: none; }
.zm-close {
  position: absolute;
  top: max(10px, env(safe-area-inset-top));
  right: max(10px, env(safe-area-inset-right));
  z-index: 2;
  font-size: 28px;
}
'''

ZOOM_HTML = '''<!-- ======== ZOOM (images et schémas) ======== -->
<div id="fm-zoom" class="zm" role="dialog" aria-modal="true" hidden>
  <div class="zm-stage"><div class="zm-box"></div></div>
  <div class="zm-bar" role="toolbar">
    <button type="button" class="zm-btn zm-sym" data-zm="out">&minus;</button>
    <button type="button" class="zm-btn" data-zm="fit"></button>
    <button type="button" class="zm-btn zm-sym" data-zm="in">+</button>
  </div>
  <button type="button" class="zm-btn zm-sym zm-close" data-zm="close">&times;</button>
</div>'''

# ── JS : zoom (vectoriel : on agrandit la largeur du SVG, jamais une capture) ────

ZOOM_JS = r'''
// ── Zoom des images et des schémas ────────────────────────────
var ZM_MAX = 4;          // zoom maximal, relatif à l'ajustement
var ZM_STEP = 1.5;       // pas des boutons + et −
var ZM_REF = 812;        // largeur de référence d'un panneau de schéma (échelle --zs)
var ZM_SIDE = 16, ZM_TOP = 60, ZM_BOTTOM = 72;   // marges réservées autour de l'ajustement

var zm = {
  dlg: null, stage: null, box: null, opener: null, schema: false,
  natW: 1, natH: 1, fitW: 1, s: 1, x: 0, y: 0,
  ptrs: {}, drag: null, pinch: null, moved: false, lastTap: null, ghost: null
};

function zmBtnLabels() {
  return [
    ['out', 'zoom.out'], ['in', 'zoom.in'], ['close', 'zoom.close']
  ];
}

function fmZoomRefresh() {
  document.querySelectorAll('[data-zoomable]').forEach(function(el) {
    el.setAttribute('aria-label', t('zoom.open'));
    el.setAttribute('title', t('zoom.open'));
  });
  if (!zm.dlg) return;
  zmBtnLabels().forEach(function(p) {
    var b = zm.dlg.querySelector('[data-zm="' + p[0] + '"]');
    if (b) { b.setAttribute('aria-label', t(p[1])); b.setAttribute('title', t(p[1])); }
  });
  var fit = zm.dlg.querySelector('[data-zm="fit"]');
  if (fit) { fit.textContent = t('zoom.fit'); fit.setAttribute('aria-label', t('zoom.fit')); fit.setAttribute('title', t('zoom.fit')); }
}

function zmView() {
  return { w: zm.stage.clientWidth, h: zm.stage.clientHeight };
}

function zmFitRect() {
  var v = zmView();
  return {
    x: ZM_SIDE, y: ZM_TOP,
    w: Math.max(80, v.w - 2 * ZM_SIDE),
    h: Math.max(80, v.h - ZM_TOP - ZM_BOTTOM)
  };
}

function zmSetWidth(w) {
  zm.box.style.width = w + 'px';
  if (zm.schema) zm.box.style.setProperty('--zs', String(w / ZM_REF));
}

function zmComputeFit() {
  var f = zmFitRect(), aspect;
  if (zm.schema) {
    zmSetWidth(1000);
    aspect = zm.box.offsetHeight / 1000;
  } else {
    aspect = zm.natH / zm.natW;
  }
  zm.fitW = Math.min(f.w, f.h / aspect);
}

function zmClamp(v, lo, hi) { return Math.max(lo, Math.min(hi, v)); }

function zmApply() {
  zm.s = zmClamp(zm.s, 1, ZM_MAX);
  var w = zm.fitW * zm.s;
  zmSetWidth(w);
  var h = zm.box.offsetHeight;
  var v = zmView(), f = zmFitRect();
  if (zm.s <= 1.0001) {
    zm.s = 1;
    zm.x = f.x + (f.w - w) / 2;
    zm.y = f.y + (f.h - h) / 2;
  } else {
    // plus grand que l'écran : pas de bord vide ; plus petit : entièrement visible
    zm.x = (w >= v.w) ? zmClamp(zm.x, v.w - w, 0) : zmClamp(zm.x, 0, v.w - w);
    zm.y = (h >= v.h) ? zmClamp(zm.y, v.h - h, 0) : zmClamp(zm.y, 0, v.h - h);
  }
  zm.box.style.transform = 'translate3d(' + zm.x + 'px,' + zm.y + 'px,0)';
  zm.dlg.classList.toggle('zoomed', zm.s > 1.0001);
}

function zmZoomAt(ns, ax, ay) {
  ns = zmClamp(ns, 1, ZM_MAX);
  if (ns === zm.s) return;
  var r = ns / zm.s;
  zm.x = ax - (ax - zm.x) * r;
  zm.y = ay - (ay - zm.y) * r;
  zm.s = ns;
  zmApply();
}

function zmZoomCenter(ns) {
  var v = zmView();
  zmZoomAt(ns, v.w / 2, v.h / 2);
}

function zmFit() {
  zm.s = 1;
  zmApply();
}

// Cloner un schéma : identifiants uniques (marqueurs, motifs) pour que les pointes de flèche s'y affichent
function zmCloneSchema(el) {
  var c = el.cloneNode(true);
  var badge = c.querySelector('.fm-zoom-badge');
  if (badge) badge.remove();
  ['role', 'tabindex', 'aria-label', 'title', 'data-zoomable'].forEach(function(a) { c.removeAttribute(a); });
  c.classList.remove('fm-zoom-host');
  var ids = [];
  c.querySelectorAll('[id]').forEach(function(n) { ids.push(n.id); });
  if (ids.length) {
    var all = c.querySelectorAll('*');
    for (var i = 0; i < all.length; i++) {
      var n = all[i];
      if (n.id) n.id = 'zm-' + n.id;
      var attrs = n.attributes;
      for (var j = 0; j < attrs.length; j++) {
        var v = attrs[j].value;
        if (v.indexOf('url(#') === -1) continue;
        ids.forEach(function(id) { v = v.split('url(#' + id + ')').join('url(#zm-' + id + ')'); });
        n.setAttribute(attrs[j].name, v);
      }
    }
  }
  return c;
}

function zmOpen(el) {
  zm.opener = el;
  zm.schema = el.classList.contains('fm-schema');
  zm.box.innerHTML = '';
  zm.box.style.width = '';
  zm.box.style.removeProperty('--zs');
  var label = '';
  var nat = null, img = null;
  if (zm.schema) {
    var svg = el.querySelector('svg');
    label = svg ? (svg.getAttribute('aria-label') || '') : '';
    zm.box.appendChild(zmCloneSchema(el));
  } else {
    var src = el.currentSrc || el.src || '';
    if (!src) {
      var m = /url\(["']?([^"')]+)["']?\)/.exec(getComputedStyle(el).backgroundImage || '');
      src = m ? m[1] : '';
    }
    label = el.getAttribute('alt') || 'Field Manual';
    nat = el.naturalWidth ? [el.naturalWidth, el.naturalHeight] : (el._fmNat || null);
    img = new Image();
    img.alt = '';
    img.draggable = false;
    zm.box.appendChild(img);
    img.src = src;
  }
  zm.dlg.setAttribute('aria-label', label);
  zm.dlg.hidden = false;
  document.body.classList.add('zm-open');
  var root = document.getElementById('fm-root'), bar = document.querySelector('.toolbar');
  if (root) root.inert = true;
  if (bar) bar.inert = true;
  zm.ptrs = {}; zm.drag = null; zm.pinch = null; zm.lastTap = null;
  fmZoomRefresh();
  var ready = function() {
    zmComputeFit();
    zm.s = 1;
    zmApply();
  };
  if (zm.schema) {
    ready();
  } else if (nat) {
    zm.natW = nat[0]; zm.natH = nat[1];
    ready();
  } else {
    img.onload = function() {
      zm.natW = img.naturalWidth || 1;
      zm.natH = img.naturalHeight || 1;
      if (!zm.dlg.hidden && zm.box.firstChild === img) ready();
    };
    if (img.complete && img.naturalWidth) img.onload();
  }
  var cb = zm.dlg.querySelector('[data-zm="close"]');
  if (cb) cb.focus({ preventScroll: true });
}

function zmClose() {
  if (zm.dlg.hidden) return;
  zm.dlg.hidden = true;
  zm.box.innerHTML = '';
  zm.ptrs = {}; zm.drag = null; zm.pinch = null;
  document.body.classList.remove('zm-open');
  var root = document.getElementById('fm-root'), bar = document.querySelector('.toolbar');
  if (root) root.inert = false;
  if (bar) bar.inert = false;
  var o = zm.opener;
  zm.opener = null;
  if (o && o.focus) o.focus({ preventScroll: true });
}

function zmDist(a, b) { return Math.sqrt((a.x - b.x) * (a.x - b.x) + (a.y - b.y) * (a.y - b.y)); }

function zmTwo() {
  var ids = Object.keys(zm.ptrs);
  return [zm.ptrs[ids[0]], zm.ptrs[ids[1]]];
}

function zmStartDrag() {
  var ids = Object.keys(zm.ptrs);
  if (ids.length !== 1) { zm.drag = null; return; }
  var p = zm.ptrs[ids[0]];
  zm.drag = { px: p.x, py: p.y, x: zm.x, y: zm.y };
}

function zmStartPinch() {
  var pp = zmTwo();
  zm.drag = null;
  zm.pinch = {
    d: Math.max(1, zmDist(pp[0], pp[1])),
    mx: (pp[0].x + pp[1].x) / 2, my: (pp[0].y + pp[1].y) / 2,
    s: zm.s, x: zm.x, y: zm.y
  };
}

function zmTap(x, y, ptype) {
  var now = Date.now(), lt = zm.lastTap;
  var r = zm.box.getBoundingClientRect();
  var inside = x >= r.left && x <= r.right && y >= r.top && y <= r.bottom;
  if (lt && now - lt.t < 400 && Math.abs(x - lt.x) < 30 && Math.abs(y - lt.y) < 30) {
    zm.lastTap = null;
    zmZoomAt(zm.s > 1.0001 ? 1 : 2, x, y);
    return;
  }
  zm.lastTap = { t: now, x: x, y: y };
  if (!inside && zm.s <= 1.0001) {
    if (ptype === 'touch') zm.ghost = { t: now, x: x, y: y };
    zmClose();
  }
}

function zmOnDown(e) {
  if (e.pointerType === 'mouse' && e.button !== 0) return;
  try { zm.stage.setPointerCapture(e.pointerId); } catch (err) {}
  zm.ptrs[e.pointerId] = { x: e.clientX, y: e.clientY };
  var n = Object.keys(zm.ptrs).length;
  if (n === 1) { zm.moved = false; zmStartDrag(); }
  else if (n === 2) { zm.moved = true; zmStartPinch(); }
}

function zmOnMove(e) {
  var p = zm.ptrs[e.pointerId];
  if (!p) return;
  p.x = e.clientX; p.y = e.clientY;
  var n = Object.keys(zm.ptrs).length;
  if (n >= 2 && zm.pinch) {
    var pp = zmTwo();
    var d = zmDist(pp[0], pp[1]);
    var mx = (pp[0].x + pp[1].x) / 2, my = (pp[0].y + pp[1].y) / 2;
    var ns = zmClamp(zm.pinch.s * d / zm.pinch.d, 1, ZM_MAX);
    var r = ns / zm.pinch.s;
    zm.s = ns;
    zm.x = mx - (zm.pinch.mx - zm.pinch.x) * r;
    zm.y = my - (zm.pinch.my - zm.pinch.y) * r;
    zmApply();
  } else if (zm.drag) {
    var dx = p.x - zm.drag.px, dy = p.y - zm.drag.py;
    if (Math.sqrt(dx * dx + dy * dy) > 6) zm.moved = true;
    if (zm.moved && zm.s > 1.0001) {
      zm.x = zm.drag.x + dx;
      zm.y = zm.drag.y + dy;
      zmApply();
    }
  }
}

function zmOnUp(e) {
  var p = zm.ptrs[e.pointerId];
  if (!p) return;
  delete zm.ptrs[e.pointerId];
  var n = Object.keys(zm.ptrs).length;
  if (n === 1) { zm.pinch = null; zmStartDrag(); }
  else if (n === 0) {
    zm.pinch = null; zm.drag = null;
    if (!zm.moved && e.type === 'pointerup') zmTap(e.clientX, e.clientY, e.pointerType);
  }
}

function zmOnWheel(e) {
  e.preventDefault();
  var dy = e.deltaY;
  if (e.deltaMode === 1) dy *= 16; else if (e.deltaMode === 2) dy *= 400;
  var k = e.ctrlKey ? 0.01 : 0.0015;
  zmZoomAt(zm.s * Math.exp(-dy * k), e.clientX, e.clientY);
}

function zmOnKey(e) {
  if (!zm.dlg || zm.dlg.hidden) return;
  if (e.key === 'Escape') { e.preventDefault(); zmClose(); return; }
  if (e.key === 'Tab') {
    var f = [].slice.call(zm.dlg.querySelectorAll('button'));
    if (!f.length) return;
    var i = f.indexOf(document.activeElement);
    e.preventDefault();
    f[(i + (e.shiftKey ? f.length - 1 : 1)) % f.length].focus();
    return;
  }
  if (e.key === '+' || e.key === '=') { e.preventDefault(); zmZoomCenter(zm.s * ZM_STEP); }
  else if (e.key === '-') { e.preventDefault(); zmZoomCenter(zm.s / ZM_STEP); }
  else if (e.key === '0') { e.preventDefault(); zmFit(); }
  else if (zm.s > 1.0001 && e.key.indexOf('Arrow') === 0) {
    e.preventDefault();
    var step = 80;
    if (e.key === 'ArrowLeft') zm.x += step;
    else if (e.key === 'ArrowRight') zm.x -= step;
    else if (e.key === 'ArrowUp') zm.y += step;
    else zm.y -= step;
    zmApply();
  }
}

function initZoom() {
  zm.dlg = document.getElementById('fm-zoom');
  if (!zm.dlg) return;
  zm.stage = zm.dlg.querySelector('.zm-stage');
  zm.box = zm.dlg.querySelector('.zm-box');

  document.querySelectorAll('.fm-schema, .fm-hero-img, .cover-img-box').forEach(function(el) {
    el.setAttribute('role', 'button');
    el.setAttribute('tabindex', '0');
    el.setAttribute('data-zoomable', '1');
    var host = el.classList.contains('fm-hero-img') ? el.parentNode : el;
    host.classList.add('fm-zoom-host');
    var b = document.createElement('span');
    b.className = 'fm-zoom-badge';
    b.setAttribute('aria-hidden', 'true');
    host.appendChild(b);
    el.addEventListener('click', function(e) {
      // le toucher sur le fond qui ferme la fenêtre ne doit pas rouvrir ce qui se trouve dessous
      var g = zm.ghost;
      if (g && Date.now() - g.t < 400 &&
          Math.abs(e.clientX - g.x) < 14 && Math.abs(e.clientY - g.y) < 14) { zm.ghost = null; return; }
      zmOpen(el);
    });
    el.addEventListener('keydown', function(e) {
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); zmOpen(el); }
    });
    if (el.classList.contains('cover-img-box')) {
      var m = /url\(["']?([^"')]+)["']?\)/.exec(getComputedStyle(el).backgroundImage || '');
      if (m) {
        var pre = new Image();
        pre.onload = function() { el._fmNat = [pre.naturalWidth, pre.naturalHeight]; };
        pre.src = m[1];
      }
    }
  });

  zm.dlg.querySelectorAll('[data-zm]').forEach(function(b) {
    b.addEventListener('click', function() {
      var a = b.getAttribute('data-zm');
      if (a === 'close') zmClose();
      else if (a === 'fit') zmFit();
      else if (a === 'in') zmZoomCenter(zm.s * ZM_STEP);
      else if (a === 'out') zmZoomCenter(zm.s / ZM_STEP);
    });
  });

  zm.stage.addEventListener('pointerdown', zmOnDown);
  zm.stage.addEventListener('pointermove', zmOnMove);
  zm.stage.addEventListener('pointerup', zmOnUp);
  zm.stage.addEventListener('pointercancel', zmOnUp);
  zm.stage.addEventListener('wheel', zmOnWheel, { passive: false });
  document.addEventListener('keydown', zmOnKey);
  window.addEventListener('resize', function() {
    if (zm.dlg.hidden) return;
    zmComputeFit();
    zmApply();
  });
  fmZoomRefresh();
}
'''

# ── HTML principal ───────────────────────────────────────────────────────────────

HTML = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0, viewport-fit=cover">
<title>Field Manual — Mission Plan</title>
{FONT_CDN}
<style>
/* =============================================
   DCS FIELD MANUAL v{APP_VERSION}
   Documentation module — Mission Plan suite
   ============================================= */

{font_face_css()}

:root {{
  --f-stencil:    'Stardos Stencil', 'Impact', 'Arial Narrow Bold', sans-serif;
  --f-typewriter: 'Special Elite', 'Courier New', monospace;
  --f-ui:         'Oswald', 'Arial Narrow', sans-serif;
  --amber:        #c0892a;
  --amber-dark:   #8a5e15;
  --green-radar:  #4f6b3a;
  /* Accent du module Field Manual */
  --fm-accent:    #7E8FA6;
  --fm-accent-dark: #5a6a7a;
}}

/* ── THÈMES (clonés verbatim depuis build_recon_station.py) ── */
body[data-theme="cw-nato"] {{
  --paper: #d8c9a5; --paper-light: #e3d6b5; --paper-dark: #b8a77c;
  --ink: #1f1c16; --ink-faded: #463f30;
  --olive: #4a5230; --olive-dark: #2c321e; --olive-deep: #1a1e10;
  --khaki: #807454; --khaki-light: #a89a72;
  --red-stamp: #a83524; --red-faded: #c4574a;
  --rust: #7a3a20;
  --kraft-bg: url('data:image/svg+xml;base64,{KRAFT_NATO}');
}}
body[data-theme="cw-soviet"] {{
  --paper: #d8c479; --paper-light: #e8d690; --paper-dark: #b8a64a;
  --ink: #1f1c16; --ink-faded: #463f30;
  --olive: #2a3a5a; --olive-dark: #1a2540; --olive-deep: #0e1830;
  --khaki: #3a4a2e; --khaki-light: #5a6a48;
  --red-stamp: #841e1e; --red-faded: #a04040;
  --rust: #5e1414;
  --kraft-bg: url('data:image/svg+xml;base64,{KRAFT_SOV}');
}}
body[data-theme="modern-nato"] {{
  --paper: #e8e3d8; --paper-light: #f0ece2; --paper-dark: #c8c0b0;
  --ink: #15181c; --ink-faded: #3a4048;
  --olive: #2a3038; --olive-dark: #1c2026; --olive-deep: #0e1014;
  --khaki: #5c6b7a; --khaki-light: #7a8a98;
  --red-stamp: #1a1a1a; --red-faded: #4a4a4a;
  --rust: #2a2a2a;
  --kraft-bg: url('data:image/svg+xml;base64,{KRAFT_MNATO}');
}}
body[data-theme="modern-east"] {{
  --paper: #cdc6b8; --paper-light: #ddd6c8; --paper-dark: #ada69a;
  --ink: #1a1610; --ink-faded: #3d3024;
  --olive: #3d3024; --olive-dark: #2a2018; --olive-deep: #1a140e;
  --khaki: #4a5238; --khaki-light: #6a7256;
  --red-stamp: #7a2424; --red-faded: #a04040;
  --rust: #5a1a1a;
  --kraft-bg: url('data:image/svg+xml;base64,{KRAFT_MEAST}');
}}

/* ── Reset & base ── */
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
html, body {{ height: 100%; overscroll-behavior: none; }}
button, input, select, textarea {{ font: inherit; cursor: pointer; }}
/* le focus visible : la même règle que le bloc d'interface commun des autres modules */
button:focus-visible, select:focus-visible, input:focus-visible, textarea:focus-visible, summary:focus-visible,
a[href]:focus-visible, [tabindex]:focus-visible, [role="button"]:focus-visible {{
  outline: 2px solid var(--amber); outline-offset: 2px;
}}

body {{
  font-family: var(--f-typewriter);
  background: var(--olive-deep);
  color: var(--paper);
  font-size: 14px;
  line-height: 1.6;
  overflow: hidden;
  -webkit-tap-highlight-color: transparent;
  -webkit-text-size-adjust: 100%;
  display: flex;
  flex-direction: column;
  height: 100vh;
}}

/* ── TOOLBAR ── */
.toolbar {{
  position: relative;
  flex-shrink: 0;
  height: 60px;
  background: linear-gradient(180deg, var(--olive-dark) 0%, var(--olive-deep) 100%);
  border-bottom: 2px solid var(--fm-accent-dark);
  display: flex;
  align-items: center;
  padding: 0 14px;
  gap: 8px;
  z-index: 1000;
  box-shadow: 0 4px 12px rgba(0,0,0,.4);
  padding-left: max(14px, env(safe-area-inset-left));
  padding-right: max(14px, env(safe-area-inset-right));
}}

.tb-brand {{ display: flex; flex-direction: column; line-height: 1.1; gap: 1px; flex-shrink: 0; }}
.tb-brand-main {{
  font-family: var(--f-stencil);
  font-size: 16px;
  font-weight: 700;
  letter-spacing: 3px;
  color: var(--fm-accent);
  text-transform: uppercase;
  white-space: nowrap;
}}
.tb-brand-sub {{
  font-family: var(--f-ui);
  font-size: 10px;
  letter-spacing: 2px;
  color: var(--khaki-light);
  text-transform: uppercase;
  white-space: nowrap;
}}

.tb-sep {{ width: 1px; height: 28px; background: var(--khaki); opacity: .4; flex-shrink: 0; }}
.tb-spacer {{ flex: 1; }}
.tb-version {{
  font-family: var(--f-typewriter);
  font-size: 11px;
  opacity: .45;
  color: var(--amber);
  letter-spacing: .5px;
  user-select: none;
  white-space: nowrap;
}}

#btn-lang {{
  background: transparent;
  border: 1px solid var(--khaki);
  color: var(--paper);
  box-sizing: border-box;
  height: 44px;
  min-width: 44px;
  min-height: 44px;
  padding: 0 8px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-family: 'Roboto Mono', 'Courier New', monospace;
  font-weight: 400;
  font-size: 16px;
  transition: all .15s;
  flex-shrink: 0;
}}
#btn-lang:hover, #btn-lang:focus-visible {{
  background: var(--olive);
  border-color: var(--fm-accent);
}}


/* ---------- Barre du haut commune aux sept modules (lot mp-imports-suite) ----------
   La marque du Flight Configurator : le titre et son sous-titre à l'accent du module dès 1360 px, le sigle seul en dessous (à toutes les largeurs) ;
   la version avec le titre ; le tampon de décor dès 1101 px. Seuils mesurés dans le shell avec un tampon d'escadre « TEST WING », en français et en anglais. */
.tb-brand-main, .tb-brand-short {{ color: #7E8FA6; }}
.tb-brand-short {{ display: none; font-family: var(--f-stencil); font-size: 16px; font-weight: 700; letter-spacing: 3px; white-space: nowrap; }}
.tb-classif {{ font-family: var(--f-stencil); font-weight: 400; font-size: 11px; letter-spacing: 3px; color: var(--red-faded); border: 1px solid var(--red-faded); padding: 4px 10px; white-space: nowrap; flex-shrink: 0; }}
#btn-lang svg {{ display: block; }}
.tb-brand-sub {{ font-weight: 500; }}
.tb-version {{ font-family: 'Roboto Mono', monospace; }}
@media (max-width: 1359px) {{ .tb-brand-main, .tb-brand-sub, .tb-brand + .tb-sep, .tb-version {{ display: none; }} .tb-brand-short {{ display: inline; }} }}
@media (max-width: 1100px) {{ .tb-classif {{ display: none; }} }}

/* ── ROOT SCROLL ── */
#fm-root {{
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  color: var(--ink);
  background: var(--kraft-bg), var(--paper);
  background-repeat: repeat;
  background-size: 400px 566px, auto;
}}

/* ── PAGE SYSTEM ── */
.fm-page {{ display: block; }}
.fm-page.hidden {{ display: none; }}

/* ── INDEX PAGE ── */
#page-index {{
  max-width: 900px;
  margin: 0 auto;
  padding: 32px 24px 64px;
}}

/* ── COUVERTURE ── */
.cover-wrap {{
  margin-bottom: 32px;
  border: 1px solid var(--khaki);
  box-shadow: 0 6px 24px rgba(0,0,0,.5), inset 0 0 60px rgba(0,0,0,.2);
  position: relative;
  overflow: hidden;
}}
.cover-img-box {{
  width: 100%;
  height: 260px;
  background-size: cover;
  background-position: center 25%;
  position: relative;
}}
.cover-img-box::after {{
  content: "";
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 1;
  background: linear-gradient(to top, rgba(0,0,0,.72) 0%, rgba(0,0,0,.32) 30%, transparent 58%);
}}
.cover-overlay {{
  position: absolute;
  bottom: 0; left: 0;
  padding: 16px 20px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  z-index: 2;
}}
.cover-suite {{
  font-weight: 500;   /* Oswald 500, la face que le navigateur dessinait déjà pour 400 */
  font-weight: 500;   /* Oswald 500, la face que le navigateur dessinait déjà pour 400 */
  font-family: var(--f-ui);
  font-size: 12px;
  letter-spacing: 3px;
  color: rgba(255,255,255,.75);
  text-transform: uppercase;
}}
.cover-ref {{
  font-family: var(--f-stencil);
  font-size: 18px;
  color: var(--fm-accent);
  letter-spacing: 2px;
}}

/* Fallback couverture SVG */
.cover-svg {{ background: var(--olive-dark); }}
.cover-svg-inner {{
  padding: 40px 32px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  text-align: center;
  border: 2px solid var(--khaki);
  margin: 8px;
}}
.cover-classif-top {{
  font-family: var(--f-ui);
  font-size: 10px;
  letter-spacing: 3px;
  color: var(--red-stamp);
  text-transform: uppercase;
  border: 1px solid var(--red-stamp);
  padding: 3px 10px;
}}
.cover-title-main {{
  font-family: var(--f-stencil);
  font-size: 42px;
  color: var(--fm-accent);
  letter-spacing: 6px;
  line-height: 1;
}}
.cover-title-sub {{
  font-family: var(--f-ui);
  font-size: 14px;
  letter-spacing: 4px;
  color: var(--khaki-light);
  text-transform: uppercase;
}}
.cover-ref-box {{
  font-family: var(--f-typewriter);
  font-size: 16px;
  color: var(--paper);
  border: 1px solid var(--fm-accent);
  padding: 4px 14px;
  letter-spacing: 2px;
}}
.cover-stamp {{
  font-family: var(--f-stencil);
  font-size: 11px;
  color: var(--red-stamp);
  letter-spacing: 2px;
  opacity: .7;
  margin-top: 8px;
}}

/* ── INTRO ── */
.fm-intro {{
  border-top: 1px solid var(--khaki);
  border-bottom: 1px solid var(--khaki);
  padding: 20px 0;
  margin-bottom: 36px;
}}
.fm-intro p {{
  color: var(--ink);
  font-size: 13px;
  line-height: 1.7;
  margin-bottom: 10px;
  opacity: .9;
}}
.fm-intro p:last-child {{ margin-bottom: 0; }}

/* ── SECTION TITLE ── */
.fm-section-title {{
  font-family: var(--f-stencil);
  font-size: 13px;
  letter-spacing: 4px;
  color: var(--fm-accent);
  text-transform: uppercase;
  margin-bottom: 20px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--fm-accent);
  opacity: .8;
}}

/* ── PLAQUES INDEX ── */
.fm-plaque-grid {{
  display: flex;
  flex-direction: column;
  gap: 16px;
}}
@media (min-width: 900px) {{
  .fm-plaque-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
  }}
  .fm-plaque-grid .fm-plaque:first-child {{
    grid-column: 1 / -1;
  }}
}}

.fm-plaque {{
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 20px;
  background: linear-gradient(135deg, rgba(255,255,255,.04), rgba(0,0,0,.15));
  border: 1px solid var(--khaki);
  position: relative;
  overflow: hidden;
  transition: translate .12s ease, box-shadow .12s ease;
  text-decoration: none;
  color: inherit;
}}
.fm-plaque::before {{
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, rgba(var(--chapter-accent-rgb),.08) 0%, transparent 50%);
  pointer-events: none;
}}
.fm-plaque.active {{
  cursor: pointer;
  border-color: color-mix(in srgb, var(--chapter-accent, var(--fm-accent)) 40%, var(--khaki));
}}
.fm-plaque.active:hover {{
  translate: 0 -2px;
  box-shadow: 0 6px 20px rgba(0,0,0,.35);
  border-color: var(--chapter-accent, var(--fm-accent));
}}
.fm-plaque.active:focus-visible {{
  outline: 2px solid var(--amber);
  outline-offset: 2px;
}}
.fm-plaque.soon {{
  opacity: .5;
  cursor: default;
  pointer-events: none;
}}

.fm-plaque-monogram {{
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: var(--chapter-accent, var(--fm-accent));
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: var(--f-stencil);
  font-size: 16px;
  font-weight: 700;
  color: #fff;
  flex-shrink: 0;
  letter-spacing: 1px;
}}
.fm-plaque-info {{
  flex: 1;
  min-width: 0;
}}
.fm-plaque-name {{
  font-family: var(--f-stencil);
  font-size: 15px;
  letter-spacing: 2px;
  color: var(--ink);
  margin-bottom: 3px;
}}
.fm-plaque-desc {{
  font-weight: 500;   /* idem */
  font-weight: 500;   /* idem */
  font-family: var(--f-ui);
  font-size: 11px;
  letter-spacing: 1px;
  color: var(--khaki);
  text-transform: uppercase;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}}
.fm-plaque-badge {{
  font-family: var(--f-stencil);
  font-size: 9px;
  letter-spacing: 2px;
  padding: 3px 8px;
  text-transform: uppercase;
  flex-shrink: 0;
}}
.fm-plaque.active .fm-plaque-badge {{
  color: var(--accent-ink);
  border: 1px solid var(--chapter-accent, var(--fm-accent));
}}
.fm-plaque.soon .fm-plaque-badge {{
  color: var(--khaki);
  border: 1px solid var(--khaki);
  position: absolute;
  top: 12px; right: 14px;
}}
/* Tampon SOON en diagonal */
.fm-plaque.soon .fm-soon-stamp {{
  position: absolute;
  top: 50%; right: 16px;
  transform: rotate(-8deg) translateY(-50%);
  font-family: var(--f-stencil);
  font-size: 22px;
  letter-spacing: 3px;
  color: var(--red-stamp);
  border: 2px solid var(--red-stamp);
  padding: 2px 8px;
  opacity: .45;
  pointer-events: none;
}}

/* ── CHAPITRE PAGE ── */
/* La couleur d'un module marque, l'encre écrit : l'encre d'accent (50 % accent, 50 % encre) porte le texte. */
.fm-chapter, .fm-plaque, .fm-stub-placeholder {{
  --accent-ink: color-mix(in srgb, var(--chapter-accent, var(--fm-accent)) 40%, var(--ink));
}}
.fm-chapter {{
  max-width: 860px;
  margin: 0 auto;
  padding: 32px 24px 80px;
}}

/* Bouton retour index */
.fm-back-btn {{
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-family: var(--f-ui);
  font-size: 11px;
  letter-spacing: 2px;
  text-transform: uppercase;
  color: var(--fm-accent);
  background: transparent;
  border: 1px solid var(--fm-accent);
  padding: 6px 14px;
  cursor: pointer;
  margin-bottom: 28px;
  transition: all .12s;
}}
.fm-back-btn:hover {{ background: rgba(126,143,166,.12); }}

/* ── HERO ── */
.fm-hero {{
  margin-bottom: 32px;
  border: 1px solid var(--chapter-accent, var(--fm-accent));
  box-shadow: 0 4px 20px rgba(0,0,0,.4);
  position: relative;
  overflow: hidden;
}}
.fm-hero-img {{
  width: 100%;
  height: 200px;
  object-fit: cover;
  display: block;
  /* punaise simulée */
  position: relative;
}}
.fm-hero-pin {{
  position: absolute;
  top: 10px; right: 18px;
  width: 12px; height: 12px;
  border-radius: 50%;
  background: var(--chapter-accent, var(--fm-accent));
  box-shadow: 0 2px 6px rgba(0,0,0,.5);
}}
.fm-hero-caption {{
  padding: 12px 16px;
  background: linear-gradient(180deg, var(--olive-dark) 0%, var(--olive-deep) 100%);
  display: flex;
  align-items: center;
  gap: 14px;
  border-top: 2px solid var(--chapter-accent, var(--fm-accent));
}}
.fm-hero-monogram {{
  font-family: var(--f-stencil);
  font-size: 24px;
  color: var(--chapter-accent, var(--fm-accent));
  flex-shrink: 0;
  letter-spacing: 2px;
}}
.fm-hero-title {{
  font-family: var(--f-stencil);
  font-size: 18px;
  letter-spacing: 3px;
  color: var(--paper);
}}
.fm-hero-sub {{
  font-family: var(--f-ui);
  font-size: 10px;
  letter-spacing: 2px;
  color: var(--chapter-accent, var(--fm-accent));
  text-transform: uppercase;
  opacity: .8;
}}

/* ── PROSE ── */
.fm-prose {{
  margin-bottom: 28px;
}}
.fm-prose h3 {{
  font-family: var(--f-stencil);
  font-size: 14px;
  letter-spacing: 3px;
  color: var(--accent-ink);
  text-transform: uppercase;
  margin-bottom: 12px;
  padding-left: 12px;
  border-left: 3px solid var(--chapter-accent, var(--fm-accent));
}}
.fm-prose p {{
  font-size: 13px;
  line-height: 1.75;
  color: var(--ink);
  opacity: .9;
  margin-bottom: 10px;
}}
.fm-prose ol, .fm-prose ul {{
  padding-left: 20px;
  margin-bottom: 10px;
}}
.fm-prose li {{
  font-size: 13px;
  line-height: 1.7;
  color: var(--ink);
  opacity: .9;
  margin-bottom: 4px;
}}

/* Lang blocks */
.lang-block {{ display: block; }}
body[lang="en"] .lang-block[data-lang="fr"] {{ display: none; }}
body[lang="fr"] .lang-block[data-lang="en"] {{ display: none; }}

/* ── CALLOUTS ── */
.fm-callout {{
  margin: 20px 0;
  padding: 14px 16px;
  position: relative;
  font-size: 13px;
  line-height: 1.65;
}}
.fm-callout::before {{
  display: block;
  font-family: var(--f-stencil);
  font-size: 10px;
  letter-spacing: 3px;
  text-transform: uppercase;
  margin-bottom: 8px;
  padding-bottom: 6px;
  border-bottom: 1px solid currentColor;
}}
.fm-callout.note {{
  border: 1px solid var(--fm-accent);
  border-left: 3px solid var(--fm-accent);
  background: rgba(126,143,166,.07);
  color: var(--ink);
}}
.fm-callout.note::before {{
  content: '— NOTE';
  color: var(--fm-accent);
}}
.fm-callout.warn {{
  border: 1px solid var(--red-stamp);
  border-left: 3px solid var(--red-stamp);
  background: rgba(168,53,36,.07);
  color: var(--ink);
}}
.fm-callout.warn::before {{
  content: '▲ ATTENTION';
  color: var(--red-stamp);
}}

.fm-callout a {{
  color: var(--accent-ink);
  text-decoration: underline;
  text-decoration-color: var(--chapter-accent, var(--fm-accent));
}}

kbd {{
  font-family: var(--f-typewriter);
  font-size: 11px;
  background: var(--olive-dark);
  border: 1px solid var(--khaki);
  border-bottom-width: 2px;
  border-radius: 3px;
  padding: 1px 6px;
  color: var(--paper);
  display: inline-block;
  margin: 0 2px;
}}

.fm-callout.key {{
  border: 1px solid var(--khaki);
  background: rgba(128,116,84,.07);
  color: var(--ink);
  display: flex;
  align-items: flex-start;
  gap: 12px;
}}
.fm-callout.key::before {{
  content: none;
}}
.fm-callout-key-icon {{
  font-family: var(--f-stencil);
  font-size: 9px;
  letter-spacing: 2px;
  color: var(--khaki-light);
  white-space: nowrap;
  margin-top: 2px;
  text-transform: uppercase;
}}

/* ── SCHÉMA SVG ── */
.fm-schema {{
  margin: 28px 0;
  border: 1px solid var(--khaki);
  background: rgba(0,0,0,.10);
  padding: 20px;
  position: relative;
}}
.fm-schema svg {{
  display: block;
  width: 100%;
  height: auto;
  max-height: 380px;
}}
.fm-schema-legend {{
  margin-top: 10px;
  font-family: var(--f-ui);
  font-size: 10px;
  letter-spacing: 1.5px;
  color: var(--ink);
  text-transform: uppercase;
  text-align: center;
  opacity: .85;
}}

/* ── STUB ── */
.fm-stub {{
  max-width: 860px;
  margin: 0 auto;
  padding: 32px 24px 80px;
}}
.fm-stub-placeholder {{
  margin-top: 32px;
  padding: 40px;
  border: 1px dashed var(--khaki);
  text-align: center;
  opacity: .45;
}}
.fm-stub-placeholder p {{
  font-family: var(--f-stencil);
  font-size: 18px;
  letter-spacing: 4px;
  color: var(--accent-ink);
  text-transform: uppercase;
}}
.fm-stub-placeholder small {{
  font-family: var(--f-ui);
  font-size: 10px;
  letter-spacing: 2px;
  color: var(--khaki);
  text-transform: uppercase;
  display: block;
  margin-top: 8px;
}}

/* ── CHAPTER ACCENT OVERRIDES ── */
#page-rs  {{ --chapter-accent: #C95A9C; --chapter-accent-rgb: 201,90,156; }}
#page-hq  {{ --chapter-accent: #4FB286; --chapter-accent-rgb: 79,178,134; }}
#page-bg  {{ --chapter-accent: #c0892a; --chapter-accent-rgb: 192,137,42; }}
#page-dg  {{ --chapter-accent: #4f7a8e; --chapter-accent-rgb: 79,122,142; }}
#page-rp  {{ --chapter-accent: #7ac97a; --chapter-accent-rgb: 122,201,122; }}
#page-fc  {{ --chapter-accent: #D0784A; --chapter-accent-rgb: 208,120,74; }}

/* Plaques accents individuels */
.fm-plaque[data-module="rs"]  {{ --chapter-accent: #C95A9C; --chapter-accent-rgb: 201,90,156; }}
.fm-plaque[data-module="hq"]  {{ --chapter-accent: #4FB286; --chapter-accent-rgb: 79,178,134; }}
.fm-plaque[data-module="bg"]  {{ --chapter-accent: #c0892a; --chapter-accent-rgb: 192,137,42; }}
.fm-plaque[data-module="rp"]  {{ --chapter-accent: #7ac97a; --chapter-accent-rgb: 122,201,122; }}
.fm-plaque[data-module="dg"]  {{ --chapter-accent: #4f7a8e; --chapter-accent-rgb: 79,122,142; }}
.fm-plaque[data-module="fc"]  {{ --chapter-accent: #D0784A; --chapter-accent-rgb: 208,120,74; }}

/* Exception écrite à R295, pour le contenu des pages du manuel seulement : `strong`, `b` et le reste du contenu gardent le gras du rendu d'origine
   (700 demandé sur Special Elite, qui n'a que sa face 400 : gras synthétisé par le navigateur). La barre et l'interface du manuel restent dans la règle. */
{FM_EXTRA_CSS}
{CONTRAST_CSS}</style>
</head>
<body data-theme="cw-nato">

<!-- ======== TOOLBAR ======== -->
<header class="toolbar">
  <div class="tb-brand">
    <span class="tb-brand-main">FIELD MANUAL</span>
    <span class="tb-brand-short">F·M</span>
    <span class="tb-brand-sub" data-i18n="brand.sub">░ MANUEL OPÉRATIONNEL</span>
  </div>
  <div class="tb-sep" aria-hidden="true"></div>
  <div class="tb-spacer"></div>
  <div class="tb-classif">TRAINING // UNCLASSIFIED</div>
  <span class="tb-version">v{APP_VERSION}</span>
  <button id="btn-lang" aria-label="Passer en anglais" title="Passer en anglais">
    <svg id="flag-svg" viewBox="0 0 20 14" width="22" height="15" xmlns="http://www.w3.org/2000/svg">
      <!-- flag FR par défaut -->
      <rect width="7" height="14" fill="#002395"/>
      <rect x="7" width="6" height="14" fill="#fff"/>
      <rect x="13" width="7" height="14" fill="#ED2939"/>
    </svg>
  </button>
</header>

<!-- ======== MAIN ROOT ======== -->
<main id="fm-root">

  <!-- ===== PAGE INDEX ===== -->
  <section id="page-index" class="fm-page">
    <div style="max-width:900px; margin:0 auto; padding:32px 24px 64px;">

      <!-- Couverture -->
      {COVER_HTML}

      <!-- Intro -->
      <div class="fm-intro">
        <div class="lang-block" data-lang="fr">
          <p>La suite DCS Mission Plan regroupe des outils de préparation de mission entièrement hors-ligne, distribués sous forme de fichiers HTML autonomes. Aucune installation requise, aucune dépendance réseau : chaque outil s'ouvre directement dans votre navigateur.</p>
          <p>Ce manuel documente l'utilisation de chaque module : fonctionnalités, interface, flux de travail, et limites à connaître. Il est conçu pour être parcouru chapitre par chapitre, ou consulté ponctuellement.</p>
        </div>
        <div class="lang-block" data-lang="en">
          <p>The DCS Mission Plan suite brings together fully offline mission preparation tools, distributed as self-contained HTML files. No installation required, no network dependency: each tool opens directly in your browser.</p>
          <p>This manual documents how to use each module: features, interface, workflow, and caveats worth knowing. It is designed to be read chapter by chapter, or consulted as needed.</p>
        </div>
      </div>

      <!-- Démarrer : le bouton Exemple de chaque outil -->
      <div class="fm-prose">
        <h3 class="lang-block" data-lang="fr">Démarrer</h3>
        <h3 class="lang-block" data-lang="en">Getting started</h3>
        <div class="lang-block" data-lang="fr"><p>Chaque outil a un bouton <strong>Exemple</strong> (l’icône de feuille de la barre du haut) qui le remplit d’une démonstration, dans la langue de l’interface au moment du clic : le moyen le plus rapide de voir ce qu’il fait. Les exemples du Briefing Generator, du Datacard Generator, du Route Planner et de Recon Station racontent la même opération fictive, FOOTHOLD ; celui de HQ est une escadre de démonstration. <strong>HQ garde votre configuration d’escadre</strong> et propose de la restaurer en un geste ; dans les autres outils, l’exemple <strong>remplace le travail en cours, après confirmation</strong> (Recon Station ne la demande que s’il y a déjà du travail). Une fois chargé, l’exemple est à vous : changer de langue ensuite ne le retraduit pas. Pour repartir d’une page blanche, <strong>Effacer</strong> (Briefing Generator, Datacard Generator, Route Planner) vide l’outil.</p></div>
        <div class="lang-block" data-lang="en"><p>Every tool has an <strong>Example</strong> button (the sheet icon in the top bar) that fills it with a demonstration, in the interface language at the moment of the click: the quickest way to see what it does. The Briefing Generator, Datacard Generator, Route Planner and Recon Station examples tell the same fictional operation, FOOTHOLD; HQ’s is a demonstration wing. <strong>HQ keeps your wing configuration</strong> and offers to restore it in one tap; in the other tools, the example <strong>replaces the current work, after confirmation</strong> (Recon Station only asks when there is already work in place). Once loaded, the example is yours: switching language afterwards does not translate it again. To start from a blank page, <strong>Clear</strong> (Briefing Generator, Datacard Generator, Route Planner) empties the tool.</p></div>
      </div>

      <!-- Index -->
      <p class="fm-section-title" data-i18n="index.title">Modules documentés</p>

      <div class="fm-plaque-grid">

        <!-- HQ -->
        <div class="fm-plaque active" data-module="hq" tabindex="0" role="button"
             aria-label="HQ — Wing Command Center"
             onclick="navigate('hq')"
             onkeydown="if(event.key==='Enter'||event.key===' '){{event.preventDefault();navigate('hq')}}">
          <div class="fm-plaque-monogram">HQ</div>
          <div class="fm-plaque-info">
            <div class="fm-plaque-name">HQ</div>
            <div class="fm-plaque-desc" data-i18n="index.hq.desc">Wing Command Center — configuration escadre</div>
          </div>
          <div class="fm-plaque-badge" data-i18n="index.badge.active">Manuel</div>
        </div>

        <!-- FC -->
        <div class="fm-plaque active" data-module="fc" tabindex="0" role="button"
             aria-label="FC — Flight Configurator"
             onclick="navigate('fc')"
             onkeydown="if(event.key==='Enter'||event.key===' '){{event.preventDefault();navigate('fc')}}">
          <div class="fm-plaque-monogram">FC</div>
          <div class="fm-plaque-info">
            <div class="fm-plaque-name">Flight Configurator</div>
            <div class="fm-plaque-desc" data-i18n="index.fc.desc">Un groupe prêt à appliquer : radios, emport, livrée</div>
          </div>
          <div class="fm-plaque-badge" data-i18n="index.badge.active">Manuel</div>
        </div>

        <!-- BG -->
        <div class="fm-plaque active" data-module="bg" tabindex="0" role="button"
             aria-label="BG — Briefing Generator"
             onclick="navigate('bg')"
             onkeydown="if(event.key==='Enter'||event.key===' '){{event.preventDefault();navigate('bg')}}">
          <div class="fm-plaque-monogram">BG</div>
          <div class="fm-plaque-info">
            <div class="fm-plaque-name">Briefing Generator</div>
            <div class="fm-plaque-desc" data-i18n="index.bg.desc">Générateur de briefings multi-sections</div>
          </div>
          <div class="fm-plaque-badge" data-i18n="index.badge.active">Manuel</div>
        </div>

        <!-- DG -->
        <div class="fm-plaque active" data-module="dg" tabindex="0" role="button"
             aria-label="DG — Datacard Generator"
             onclick="navigate('dg')"
             onkeydown="if(event.key==='Enter'||event.key===' '){{event.preventDefault();navigate('dg')}}">
          <div class="fm-plaque-monogram">DG</div>
          <div class="fm-plaque-info">
            <div class="fm-plaque-name">Datacard Generator</div>
            <div class="fm-plaque-desc" data-i18n="index.dg.desc">Datacards de vol d’une page</div>
          </div>
          <div class="fm-plaque-badge" data-i18n="index.badge.active">Manuel</div>
        </div>

        <!-- RS -->
        <div class="fm-plaque active" data-module="rs" tabindex="0" role="button"
             aria-label="RS — Recon Station"
             onclick="navigate('rs')"
             onkeydown="if(event.key==='Enter'||event.key===' '){{event.preventDefault();navigate('rs')}}">
          <div class="fm-plaque-monogram">RS</div>
          <div class="fm-plaque-info">
            <div class="fm-plaque-name">Recon Station</div>
            <div class="fm-plaque-desc" data-i18n="index.rs.desc">Compositeur photo-renseignement canvas</div>
          </div>
          <div class="fm-plaque-badge" data-i18n="index.badge.active">Manuel</div>
        </div>

        <!-- RP -->
        <div class="fm-plaque active" data-module="rp" tabindex="0" role="button"
             aria-label="RP — Route Planner"
             onclick="navigate('rp')"
             onkeydown="if(event.key==='Enter'||event.key===' '){{event.preventDefault();navigate('rp')}}">
          <div class="fm-plaque-monogram">RP</div>
          <div class="fm-plaque-info">
            <div class="fm-plaque-name">Route Planner</div>
            <div class="fm-plaque-desc" data-i18n="index.rp.desc">Planification d'itinéraires</div>
          </div>
          <div class="fm-plaque-badge" data-i18n="index.badge.active">Manuel</div>
        </div>

      </div><!-- /fm-plaque-grid -->
    </div>
  </section><!-- /page-index -->


  <!-- ===== PAGE RS — Chapitre-gabarit : Recon Station ===== -->
  <section id="page-rs" class="fm-page hidden">
    <div class="fm-chapter">

      <!-- Retour -->
      <button class="fm-back-btn" onclick="navigate('index')" data-i18n="btn.back">◄ Index</button>

      <!-- Héros -->
      <div class="fm-hero">
        <img class="fm-hero-img" src="{RS_TILE_SRC}" alt="Recon Station" draggable="false">
        <div class="fm-hero-pin" aria-hidden="true"></div>
        <div class="fm-hero-caption">
          <div>
            <div class="fm-hero-monogram">RS</div>
          </div>
          <div>
            <div class="fm-hero-title" data-i18n="rs.hero.title">Recon Station</div>
            <div class="fm-hero-sub" data-i18n="rs.hero.sub">Compositeur photo-renseignement</div>
          </div>
        </div>
      </div>

      <!-- À quoi ça sert -->
      <div class="fm-prose">
        <h3 data-i18n="rs.whatfor.title">À quoi ça sert</h3>
        <div class="lang-block" data-lang="fr">
          <p>Recon Station transforme une capture d'écran DCS — ou n'importe quelle image — en photo d'analyse de reconnaissance, prête à glisser dans un briefing. Le principe : partir d'une vraie image, lui donner l'allure d'un capteur (optique, infrarouge ou radar), puis poser par-dessus une couche d'annotations — cibles, légendes, loupes, bandeau de classification, logos. L'export est un PNG sans perte, à la résolution exacte de la source. Les sections ci-dessous détaillent chaque réglage et son effet.</p>
        </div>
        <div class="lang-block" data-lang="en">
          <p>Recon Station turns a DCS screenshot — or any image — into a reconnaissance analysis photo, ready to drop into a briefing. The idea: start from a real image, give it the look of a sensor (optical, infrared, or radar), then overlay a layer of annotations — targets, legends, loupes, classification banner, logos. Export is a lossless PNG at the source's exact resolution. The sections below detail each control and its effect.</p>
        </div>
      </div>

      <!-- Schéma SVG — anatomie d'une photo recon (où se place chaque élément) -->
      <div class="fm-schema">
        <svg viewBox="0 0 720 380" xmlns="http://www.w3.org/2000/svg" role="img"
             aria-label="Anatomie d'une photo recon" data-aria-fr="Anatomie d'une photo recon" data-aria-en="Anatomy of a recon photo">
          <defs>
            <marker id="lead" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto">
              <path d="M0,0 L7,3.5 L0,7 Z" fill="currentColor" opacity=".55"/>
            </marker>
            <pattern id="hatch" width="6" height="6" patternTransform="rotate(45)" patternUnits="userSpaceOnUse">
              <line x1="0" y1="0" x2="0" y2="6" stroke="#C95A9C" stroke-width="2" opacity=".7"/>
            </pattern>
          </defs>

          <text x="360" y="26" text-anchor="middle" font-size="13" letter-spacing="3" fill="currentColor" opacity=".9" class="lang-block" data-lang="fr">ANATOMIE D'UNE PHOTO RECON</text>
          <text x="360" y="26" text-anchor="middle" font-size="13" letter-spacing="3" fill="currentColor" opacity=".9" class="lang-block" data-lang="en">ANATOMY OF A RECON PHOTO</text>
          <line x1="120" y1="34" x2="600" y2="34" stroke="currentColor" stroke-width=".6" opacity=".3"/>

          <!-- PHOTO (fond sombre, repères clairs) -->
          <rect x="250" y="64" width="220" height="240" fill="#2b2f26" stroke="currentColor" stroke-width="1.2"/>
          <rect x="250" y="64"  width="220" height="18" fill="url(#hatch)"/>
          <rect x="250" y="286" width="220" height="18" fill="url(#hatch)"/>
          <rect x="258" y="248" width="34" height="24" fill="none" stroke="#e8e3d8" stroke-width="1" opacity=".8"/>
          <text x="275" y="263" text-anchor="middle" font-size="9" fill="#e8e3d8" opacity=".8">LOGO</text>
          <rect x="396" y="92" width="66" height="48" fill="none" stroke="#e8e3d8" stroke-width="1" opacity=".85"/>
          <text x="403" y="106" font-size="9" fill="#e8e3d8" opacity=".85">1 ___</text>
          <text x="403" y="120" font-size="9" fill="#e8e3d8" opacity=".85">2 ___</text>
          <text x="403" y="134" font-size="9" fill="#e8e3d8" opacity=".85">3 ___</text>
          <line x1="331" y1="176" x2="356" y2="160" stroke="#C95A9C" stroke-width="1.6"/>
          <circle cx="320" cy="182" r="11" fill="none" stroke="#C95A9C" stroke-width="1.8"/>
          <text x="320" y="186" text-anchor="middle" font-size="11" fill="#C95A9C">1</text>
          <circle cx="356" cy="160" r="2.2" fill="#C95A9C"/>
          <rect x="294" y="206" width="30" height="24" fill="none" stroke="#e8e3d8" stroke-dasharray="3 2" stroke-width="1" opacity=".8"/>
          <rect x="398" y="160" width="64" height="52" fill="none" stroke="#e8e3d8" stroke-width="1.4"/>
          <line x1="324" y1="212" x2="398" y2="186" stroke="#e8e3d8" stroke-dasharray="3 2" stroke-width="1" opacity=".7"/>
          <text x="430" y="190" text-anchor="middle" font-size="11" fill="#e8e3d8" opacity=".7">&#8853;</text>
          <rect x="300" y="250" width="120" height="28" fill="none" stroke="#e8e3d8" stroke-width="1" opacity=".85"/>
          <text x="360" y="268" text-anchor="middle" font-size="8.5" fill="#e8e3d8" opacity=".85">TGT · COORDS · DTG</text>

          <!-- Labels gauche -->
          <line x1="214" y1="73"  x2="250" y2="73"  stroke="currentColor" stroke-width="1" opacity=".55" marker-end="url(#lead)"/>
          <line x1="214" y1="260" x2="258" y2="260" stroke="currentColor" stroke-width="1" opacity=".55" marker-end="url(#lead)"/>
          <line x1="214" y1="182" x2="307" y2="182" stroke="currentColor" stroke-width="1" opacity=".55" marker-end="url(#lead)"/>
          <g font-size="12.5" fill="currentColor" text-anchor="end">
            <text x="208" y="77"  class="lang-block" data-lang="fr">Bandeau de classification</text>
            <text x="208" y="77"  class="lang-block" data-lang="en">Classification banner</text>
            <text x="208" y="264" class="lang-block" data-lang="fr">Logo</text>
            <text x="208" y="264" class="lang-block" data-lang="en">Logo</text>
            <text x="208" y="186" class="lang-block" data-lang="fr">Marqueur + amorce</text>
            <text x="208" y="186" class="lang-block" data-lang="en">Marker + leader line</text>
          </g>

          <!-- Labels droite -->
          <line x1="506" y1="108" x2="464" y2="116" stroke="currentColor" stroke-width="1" opacity=".55" marker-end="url(#lead)"/>
          <line x1="506" y1="186" x2="464" y2="186" stroke="currentColor" stroke-width="1" opacity=".55" marker-end="url(#lead)"/>
          <g font-size="12.5" fill="currentColor" text-anchor="start">
            <text x="512" y="112" class="lang-block" data-lang="fr">Cartouche : N° + légende</text>
            <text x="512" y="112" class="lang-block" data-lang="en">Cartouche: No. + legend</text>
            <text x="512" y="190" class="lang-block" data-lang="fr">Loupe (agrandissement)</text>
            <text x="512" y="190" class="lang-block" data-lang="en">Loupe (magnification)</text>
          </g>

          <!-- Label bas -->
          <line x1="360" y1="326" x2="360" y2="280" stroke="currentColor" stroke-width="1" opacity=".55" marker-end="url(#lead)"/>
          <text x="360" y="336" text-anchor="middle" font-size="12.5" fill="currentColor" class="lang-block" data-lang="fr">Bloc d'informations</text>
          <text x="360" y="336" text-anchor="middle" font-size="12.5" fill="currentColor" class="lang-block" data-lang="en">Information block</text>
        </svg>
        <div class="fm-schema-legend">
          <span class="lang-block" data-lang="fr">Fig. 1 — Où se place chaque élément sur la photo composée.</span>
          <span class="lang-block" data-lang="en">Fig. 1 — Where each element sits on the composed photo.</span>
        </div>
      </div>

      <!-- Référence par fonction -->
      <div class="fm-prose">
        <h3 class="lang-block" data-lang="fr">Préparer la photo</h3>
        <h3 class="lang-block" data-lang="en">Setting up the photo</h3>
        <div class="lang-block" data-lang="fr"><p>L'image est d'abord convertie en niveaux de gris. Le curseur <strong>Contraste</strong> accentue ou adoucit les écarts de luminosité. Le sélecteur <strong>Type d'imagerie</strong> applique ensuite l'allure d'un capteur : <strong>EO visible</strong> garde un rendu photographique net ; <strong>IR blanc chaud</strong> fait ressortir les sources chaudes en clair sur fond sombre ; <strong>IR noir chaud</strong> inverse (chaud = sombre) ; <strong>SAR</strong> donne le grain granuleux et le moucheté d'une image radar. Ce sont des stylisations du signal, pas des mesures réelles. Enfin <strong>Vignette</strong>, <strong>Grain</strong> et <strong>Scanlines</strong> (éteints par défaut) ajoutent l'usure d'un tirage : bords assombris, bruit argentique, lignes de balayage. Chaque effet est un curseur d'intensité appliqué en temps réel.</p></div>
        <div class="lang-block" data-lang="en"><p>The image is first converted to greyscale. The <strong>Contrast</strong> slider sharpens or softens brightness differences. The <strong>Imaging type</strong> selector then applies a sensor look: <strong>EO visible</strong> keeps a crisp photographic render; <strong>IR white-hot</strong> brings hot sources up bright on a dark background; <strong>IR black-hot</strong> inverts it (hot = dark); <strong>SAR</strong> gives the grainy speckle of a radar image. These are signal stylisations, not real measurements. Finally <strong>Vignette</strong>, <strong>Grain</strong>, and <strong>Scanlines</strong> (off by default) add print wear: darkened edges, film noise, scan lines. Each effect is an intensity slider applied in real time.</p></div>
      </div>

      <div class="fm-prose">
        <h3 class="lang-block" data-lang="fr">Le bloc d'informations</h3>
        <h3 class="lang-block" data-lang="en">The information block</h3>
        <div class="lang-block" data-lang="fr"><p>En bas, centré, un bloc renseigne le contexte de la prise : <strong>Cible, Coordonnées, Cap, Altitude, Mission, Capteur, Date-heure (DTG), Équipage, Classification</strong>. Tous les champs sont libres ; laissez vides ceux qui ne s'appliquent pas. Réglez la couleur du texte en <strong>blanc ou noir</strong> selon que le bas de la photo est sombre ou clair.</p></div>
        <div class="lang-block" data-lang="en"><p>At the bottom, centred, a block carries the shot's context: <strong>Target, Coordinates, Course, Altitude, Mission, Sensor, Date-time (DTG), Crew, Classification</strong>. All fields are free text; leave blank those that don't apply. Set the text colour <strong>white or black</strong> depending on whether the bottom of the photo is dark or light.</p></div>
      </div>

      <div class="fm-prose">
        <h3 class="lang-block" data-lang="fr">Cibles : cartouche et marqueurs</h3>
        <h3 class="lang-block" data-lang="en">Targets: cartouche and markers</h3>
        <div class="lang-block" data-lang="fr"><p><strong>« + Ajouter un marquage »</strong> dépose un cercle numéroté que vous faites glisser (souris ou tactile) sur la cible ; le numéro s'inscrit à côté du cercle pour ne pas la masquer. Chaque marqueur est lié à une <strong>ligne de légende</strong> dans le cartouche en haut à droite, et la numérotation se recalcule seule quand vous réordonnez ou supprimez. Couleur <strong>rouge, noir ou blanc</strong>. Activez l'<strong>Amorce</strong> pour tirer un trait du cercle au point exact de la cible (point déplaçable). Pour une ligne de légende sans cercle sur la photo, décochez <strong>« Point visible »</strong>.</p></div>
        <div class="lang-block" data-lang="en"><p><strong>"+ Add a marking"</strong> drops a numbered circle you drag (mouse or touch) onto the target; the number sits beside the circle so it never hides it. Each marker is tied to a <strong>legend line</strong> in the top-right cartouche, and numbering recomputes itself when you reorder or delete. Colour <strong>red, black, or white</strong>. Turn on the <strong>Leader line</strong> to draw from the circle to the exact target point (draggable). For a legend line with no circle on the photo, untick <strong>"Visible point"</strong>.</p></div>
      </div>

      <div class="fm-prose">
        <h3 class="lang-block" data-lang="fr">Loupe</h3>
        <h3 class="lang-block" data-lang="en">Loupe</h3>
        <div class="lang-block" data-lang="fr"><p><strong>« + Ajouter une loupe »</strong> ré-affiche, agrandie, une portion de l'image traitée : une petite zone source sur la photo, reliée en pointillés à une boîte zoomée. Zone et boîte se <strong>déplacent et se redimensionnent</strong> (poignée en bas à droite) ; le ratio reste couplé, donc l'image agrandie <strong>n'est jamais déformée</strong>. Bordure blanche, noire ou rouge, et libellé optionnel.</p></div>
        <div class="lang-block" data-lang="en"><p><strong>"+ Add a loupe"</strong> re-shows a magnified portion of the processed image: a small source area on the photo, linked by a dashed line to a zoomed box. Area and box <strong>move and resize</strong> (bottom-right handle); the ratio stays coupled, so the magnified image is <strong>never distorted</strong>. White, black, or red border, and an optional label.</p></div>
      </div>

      <div class="fm-prose">
        <h3 class="lang-block" data-lang="fr">Formes et étiquettes</h3>
        <h3 class="lang-block" data-lang="en">Shapes and labels</h3>
        <div class="lang-block" data-lang="fr"><p>Cinq <strong>formes</strong> se posent au centre puis se déplacent : ellipse, rectangle (<strong>pivotable</strong>, poignée dédiée), polygone (points éditables, fermeture), flèche (tête pleine) et crochet. Trois styles d'<strong>étiquette</strong> : <strong>tampon</strong> (boîte pleine, texte inversé), <strong>cursif</strong> (police façon crayon gras) et <strong>nu</strong> (texte simple avec halo de lisibilité). Couleur rouge, noir ou blanc pour chaque élément.</p></div>
        <div class="lang-block" data-lang="en"><p>Five <strong>shapes</strong> drop at centre then move: ellipse, rectangle (<strong>rotatable</strong>, dedicated handle), polygon (editable points, closing), arrow (solid head), and bracket. Three <strong>label</strong> styles: <strong>stamp</strong> (filled box, inverted text), <strong>cursive</strong> (grease-pencil font), and <strong>plain</strong> (simple text with a legibility halo). Red, black, or white colour per element.</p></div>
      </div>

      <div class="fm-prose">
        <h3 class="lang-block" data-lang="fr">Bandeau de classification</h3>
        <h3 class="lang-block" data-lang="en">Classification banner</h3>
        <div class="lang-block" data-lang="fr"><p>Deux barres pleine largeur, en <strong>haut et en bas</strong>, éteintes par défaut : <strong>UNCLASSIFIED</strong> (vert), <strong>CONFIDENTIAL</strong> (bleu), <strong>SECRET</strong> (rouge), <strong>TOP SECRET</strong> (orange). Les libellés ne sont <strong>pas traduits</strong> (marquage standard). Ce bandeau est distinct du champ <em>Classification</em> du bloc d'informations ; quand il est actif, la place est réservée pour ne recouvrir ni le cartouche ni le bloc info.</p></div>
        <div class="lang-block" data-lang="en"><p>Two full-width bars, <strong>top and bottom</strong>, off by default: <strong>UNCLASSIFIED</strong> (green), <strong>CONFIDENTIAL</strong> (blue), <strong>SECRET</strong> (red), <strong>TOP SECRET</strong> (orange). The labels are <strong>not translated</strong> (standard marking). This banner is distinct from the <em>Classification</em> field in the information block; when on, space is reserved so it covers neither the cartouche nor the info block.</p></div>
      </div>

      <div class="fm-prose">
        <h3 class="lang-block" data-lang="fr">Logos</h3>
        <h3 class="lang-block" data-lang="en">Logos</h3>
        <div class="lang-block" data-lang="fr"><p>Aucun logo par défaut. Ajoutez-en par <strong>upload d'image</strong>, ou <strong>importez une configuration d'escadre</strong> (fichier .json) exportée depuis HQ ou le Briefing Generator : Recon récupère alors le logo d'escadre et ceux des escadrons. Chaque logo est réduit proportionnellement et se rend en <strong>couleur, niveaux de gris (défaut) ou blanc</strong> (silhouette).</p></div>
        <div class="lang-block" data-lang="en"><p>No logo by default. Add one by <strong>image upload</strong>, or <strong>import a wing configuration</strong> (.json file) exported from HQ or the Briefing Generator: Recon then pulls in the wing logo and the squadron logos. Each logo is scaled down proportionally and renders in <strong>colour, greyscale (default), or white</strong> (silhouette).</p></div>
      </div>

      <div class="fm-prose">
        <h3 class="lang-block" data-lang="fr">Essayer l’exemple</h3>
        <h3 class="lang-block" data-lang="en">Trying the example</h3>
        <div class="lang-block" data-lang="fr"><p>Le bouton <strong>Exemple</strong> de la barre du haut (l’icône de feuille) ouvre une <strong>photo aérienne libre</strong> (USDA NAIP, domaine public) avec sa composition : trois repères de légende et leurs marqueurs, un cadre, une ellipse, une <strong>loupe</strong> et le bloc d’informations rempli (opération FOOTHOLD), dans la langue de l’interface au moment du clic. Sur un outil vide il l’ouvre directement ; s’il y a déjà du travail en place (image, annotations, champs saisis), il demande confirmation avant de le remplacer. Le <strong>crédit de l’image</strong> s’affiche sous la zone de dépôt tant que cette photo est chargée ; il n’entre pas dans l’export PNG et disparaît dès qu’une autre image est importée.</p></div>
        <div class="lang-block" data-lang="en"><p>The <strong>Example</strong> button in the top bar (the sheet icon) opens a <strong>free aerial photograph</strong> (USDA NAIP, public domain) with its composition: three legend entries and their markers, a frame, an ellipse, a <strong>loupe</strong> and the filled-in information block (operation FOOTHOLD), in the interface language at the moment of the click. On an empty tool it opens straight away; if there is already work in place (image, annotations, typed fields), it asks for confirmation before replacing it. The <strong>image credit</strong> shows under the drop zone while that photo is loaded; it never reaches the PNG export and disappears as soon as another image is imported.</p></div>
      </div>

      <div class="fm-prose">
        <h3 class="lang-block" data-lang="fr">Exporter</h3>
        <h3 class="lang-block" data-lang="en">Export</h3>
        <div class="lang-block" data-lang="fr"><p>Le bouton <strong>Exporter</strong> de la barre du haut produit un <strong>PNG sans perte à la résolution native</strong> de la source, nommé automatiquement d'après la cible et l'horodatage. L'aperçu à l'écran est en résolution réduite : seul le fichier exporté reflète la qualité finale.</p></div>
        <div class="lang-block" data-lang="en"><p>The <strong>Export</strong> button in the top bar produces a <strong>lossless PNG at the source's native resolution</strong>, auto-named from the target and timestamp. The on-screen preview is lower resolution: only the exported file reflects final quality.</p></div>
      </div>

            <!-- Callout NOTE -->
      <div class="fm-callout note">
        <div class="lang-block" data-lang="fr">Export PNG lossless — L'export produit un fichier PNG aux dimensions exactes de l'image source, sans aucune recompression. La résolution d'aperçu est inférieure ; seul l'export reflète la qualité finale.</div>
        <div class="lang-block" data-lang="en">Lossless PNG export — The export produces a PNG file at the exact dimensions of the source image, with no recompression. Preview resolution is lower; only the export reflects final quality.</div>
      </div>

      <!-- Callout WARN -->
      <div class="fm-callout warn">
        <div class="lang-block" data-lang="fr">L'image source n'est jamais persistée — Recon Station sauvegarde automatiquement vos paramètres et annotations entre sessions, mais pas l'image elle-même (trop volumineuse pour le stockage local). Après un rechargement de page, vous devrez réimporter votre image source.</div>
        <div class="lang-block" data-lang="en">The source image is never persisted — Recon Station automatically saves your settings and annotations between sessions, but not the image itself (too large for local storage). After the page is refreshed, you will need to import your source image again.</div>
      </div>

      <!-- Callout NOTE — principe effet/annotation -->
      <div class="fm-callout note">
        <div class="lang-block" data-lang="fr">Effet ou annotation — Recon ne peint jamais d'éléments absents de l'image. Les effets transforment les pixels déjà présents ; les annotations se posent par-dessus sans toucher la photo. Même la loupe ne fait que ré-afficher un agrandissement de l'image traitée — elle n'invente rien.</div>
        <div class="lang-block" data-lang="en">Effect or annotation — Recon never paints in elements that aren't in the image. Effects transform the pixels already there; annotations sit on top without touching the photo. Even the loupe only re-shows a magnified crop of the processed image — it invents nothing.</div>
      </div>

    </div><!-- /fm-chapter -->
  </section><!-- /page-rs -->


  <!-- ===== PAGE HQ ===== -->
  <section id="page-hq" class="fm-page hidden">
    <div class="fm-chapter" style="--chapter-accent:#4FB286; --chapter-accent-rgb:79,178,134;">

      <button class="fm-back-btn" onclick="navigate('index')" data-i18n="btn.back">◄ Index</button>

      <div class="fm-hero">
        <img class="fm-hero-img" src="{HQ_TILE_SRC}" alt="HQ" draggable="false">
        <div class="fm-hero-pin" aria-hidden="true"></div>
        <div class="fm-hero-caption">
          <div><div class="fm-hero-monogram">HQ</div></div>
          <div>
            <div class="fm-hero-title" data-i18n="hq.hero.title">HQ — Wing Command Center</div>
            <div class="fm-hero-sub" data-i18n="hq.hero.sub">Configuration escadre centralisée</div>
          </div>
        </div>
      </div>

      <!-- À quoi ça sert -->
      <div class="fm-prose">
        <h3 class="lang-block" data-lang="fr">À quoi ça sert</h3>
        <h3 class="lang-block" data-lang="en">What it's for</h3>
        <div class="lang-block" data-lang="fr"><p>HQ est le <strong>poste de commandement</strong> de la suite : un module de support pour les <strong>Mission Commanders</strong> et les <strong>Flight Leaders</strong>. Il fait deux choses. D'abord, c'est le <strong>seul endroit où définir l'identité de l'escadre</strong> et de ses escadrons ; cette identité est ensuite partagée automatiquement avec les autres modules — le Briefing Generator s'en sert pour son branding et ses escadrons, Recon Station pour ses logos. Ensuite, HQ sait <strong>ouvrir une mission DCS (.miz)</strong> pour en lire les groupes clients, leurs fréquences, leurs livrées et la météo. Réinjecter des modifications dans un .miz (rôle Commander) s'activera avec l'arrivée des modules Flight Lead.</p></div>
        <div class="lang-block" data-lang="en"><p>HQ is the suite's <strong>command post</strong>: a support module for <strong>Mission Commanders</strong> and <strong>Flight Leaders</strong>. It does two things. First, it is the <strong>single place to define the wing's identity</strong> and its squadrons; that identity is then shared automatically with the other modules — the Briefing Generator uses it for branding and squadrons, Recon Station for its logos. Second, HQ can <strong>open a DCS mission (.miz)</strong> to read its client groups, their frequencies, liveries, and weather. Writing changes back into a .miz (Commander role) will activate when the Flight Lead modules arrive.</p></div>
      </div>

      <!-- Schéma SVG — flux du hub -->
      <div class="fm-schema">
        <svg viewBox="0 0 720 380" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="HQ — le hub de la suite" data-aria-fr="HQ — le hub de la suite" data-aria-en="HQ — the suite’s hub">
          <defs>
            <marker id="ha" markerWidth="8" markerHeight="8" refX="6.5" refY="3.5" orient="auto"><path d="M0,0 L8,3.5 L0,7 Z" fill="currentColor" opacity=".6"/></marker>
            <marker id="haf" markerWidth="8" markerHeight="8" refX="6.5" refY="3.5" orient="auto"><path d="M0,0 L8,3.5 L0,7 Z" fill="currentColor" opacity=".35"/></marker>
          </defs>

          <text x="360" y="26" text-anchor="middle" font-size="13" letter-spacing="3" fill="currentColor" opacity=".9" class="lang-block" data-lang="fr">HQ — LE HUB DE LA SUITE</text>
          <text x="360" y="26" text-anchor="middle" font-size="13" letter-spacing="3" fill="currentColor" opacity=".9" class="lang-block" data-lang="en">HQ — THE SUITE'S HUB</text>
          <line x1="120" y1="34" x2="600" y2="34" stroke="currentColor" stroke-width=".6" opacity=".3"/>

          <rect class="sv-box" x="48" y="92" width="86" height="42" rx="3" stroke="currentColor" stroke-width="1.2"/>
          <text x="91" y="112" text-anchor="middle" font-size="12" fill="currentColor">.miz</text>
          <text x="91" y="126" text-anchor="middle" font-size="8" fill="currentColor" opacity=".9">mission</text>
          <line x1="134" y1="113" x2="286" y2="113" stroke="currentColor" stroke-width="1.2" opacity=".6" marker-end="url(#ha)"/>
          <text x="210" y="105" text-anchor="middle" font-size="9" fill="currentColor" opacity=".9" class="lang-block" data-lang="fr">ouvrir</text>
          <text x="210" y="105" text-anchor="middle" font-size="9" fill="currentColor" opacity=".9" class="lang-block" data-lang="en">open</text>

          <rect class="sv-box sv-m-hq" x="288" y="84" width="150" height="64" rx="3" stroke-width="2"/>
          <text x="363" y="116" text-anchor="middle" font-size="22" fill="currentColor" letter-spacing="2">HQ</text>
          <text x="363" y="134" text-anchor="middle" font-size="8.5" fill="currentColor" opacity=".9" class="lang-block" data-lang="fr">poste de commandement</text>
          <text x="363" y="134" text-anchor="middle" font-size="8.5" fill="currentColor" opacity=".9" class="lang-block" data-lang="en">command post</text>

          <line x1="438" y1="113" x2="512" y2="113" stroke="currentColor" stroke-width="1.2" opacity=".35" stroke-dasharray="4 3" marker-end="url(#haf)"/>
          <rect class="sv-box" x="514" y="86" width="172" height="58" rx="3" stroke="currentColor" stroke-width="1" stroke-opacity=".6" stroke-dasharray="4 3"/>
          <text x="600" y="108" text-anchor="middle" font-size="9.5" fill="currentColor" opacity=".9" class="lang-block" data-lang="fr">Snapshot de mission</text>
          <text x="600" y="108" text-anchor="middle" font-size="9.5" fill="currentColor" opacity=".9" class="lang-block" data-lang="en">Mission snapshot</text>
          <text x="600" y="124" text-anchor="middle" font-size="9.5" fill="currentColor" opacity=".9" class="lang-block" data-lang="fr">→ modules Flight Lead</text>
          <text x="600" y="124" text-anchor="middle" font-size="9.5" fill="currentColor" opacity=".9" class="lang-block" data-lang="en">→ Flight Lead modules</text>
          <text x="600" y="137" text-anchor="middle" font-size="8.5" fill="currentColor" opacity=".9" class="lang-block" data-lang="fr">(à venir)</text>
          <text x="600" y="137" text-anchor="middle" font-size="8.5" fill="currentColor" opacity=".9" class="lang-block" data-lang="en">(coming)</text>

          <line x1="363" y1="148" x2="363" y2="196" stroke="currentColor" stroke-width="1.2" opacity=".6" marker-end="url(#ha)"/>
          <rect class="sv-box" x="250" y="198" width="226" height="32" rx="3" stroke="currentColor" stroke-width="1.4"/>
          <text x="363" y="214" text-anchor="middle" font-size="11" fill="currentColor">wing_config</text>
          <text x="363" y="226" text-anchor="middle" font-size="8" fill="currentColor" opacity=".9" class="lang-block" data-lang="fr">identité d'escadre partagée</text>
          <text x="363" y="226" text-anchor="middle" font-size="8" fill="currentColor" opacity=".9" class="lang-block" data-lang="en">shared wing identity</text>

          <line x1="320" y1="230" x2="270" y2="276" stroke="currentColor" stroke-width="1.2" opacity=".6" marker-end="url(#ha)"/>
          <line x1="406" y1="230" x2="456" y2="276" stroke="currentColor" stroke-width="1.2" opacity=".6" marker-end="url(#ha)"/>
          <rect class="sv-box sv-m-bg" x="170" y="278" width="140" height="46" rx="3" stroke-width="2"/>
          <text x="240" y="300" text-anchor="middle" font-size="12" fill="currentColor">Briefing Generator</text>
          <text x="240" y="315" text-anchor="middle" font-size="8" fill="currentColor" opacity=".9" class="lang-block" data-lang="fr">branding + escadrons</text>
          <text x="240" y="315" text-anchor="middle" font-size="8" fill="currentColor" opacity=".9" class="lang-block" data-lang="en">branding + squadrons</text>
          <rect class="sv-box sv-m-rs" x="416" y="278" width="140" height="46" rx="3" stroke-width="2"/>
          <text x="486" y="300" text-anchor="middle" font-size="12" fill="currentColor">Recon Station</text>
          <text x="486" y="315" text-anchor="middle" font-size="8" fill="currentColor" opacity=".9">logos</text>

          <text x="360" y="352" text-anchor="middle" font-size="9" fill="currentColor" opacity=".9" class="lang-block" data-lang="fr">HQ édite — les autres consomment</text>
          <text x="360" y="352" text-anchor="middle" font-size="9" fill="currentColor" opacity=".9" class="lang-block" data-lang="en">HQ edits — the others consume</text>
        </svg>
        <div class="fm-schema-legend">
          <span class="lang-block" data-lang="fr">Fig. 1 — HQ édite l'identité d'escadre ; les autres modules la consomment.</span>
          <span class="lang-block" data-lang="en">Fig. 1 — HQ edits the wing identity; the other modules consume it.</span>
        </div>
      </div>

      <!-- La page : la barre et les deux colonnes -->
      <div class="fm-prose">
        <h3 class="lang-block" data-lang="fr">La page : la barre et les deux colonnes</h3>
        <h3 class="lang-block" data-lang="en">The page: the bar and the two columns</h3>
        <div class="lang-block" data-lang="fr"><p>La barre du haut porte les gestes de la page : <strong>Ouvrir .miz</strong> (ou déposez le fichier n’importe où sur la page), <strong>Sauvegarder .miz</strong>, <strong>Paquets de vol</strong> et <strong>Wing</strong>, puis <strong>Exemple</strong>. Tant que votre wing n’est pas configuré, <strong>Wing</strong> passe en premier, en ambre ; une fois configuré, il reprend sa place. <strong>Paquets de vol</strong> (importer des paquets, les appliquer à la mission) et <strong>Wing</strong> (les escadrons d’abord, puis l’identité du wing) s’ouvrent chacun dans une fenêtre ; <strong>Exemple</strong> ouvre aussi la fenêtre Wing. Une mission ouverte, la page se range sur <strong>deux colonnes dès 1 100 px</strong> : à gauche les <strong>groupes</strong> (filtres et cases à cocher) ; à droite, <strong>collées en haut</strong> de la vue, les actions sur les groupes cochés (<strong>Exporter</strong>, <strong>Supprimer</strong>, <strong>Dynamic Spawn…</strong>), le panneau Dynamic Spawn, puis la mission source et la météo. En dessous de 1 100 px, une seule colonne, la droite d’abord.</p></div>
        <div class="lang-block" data-lang="en"><p>The top bar carries the page’s actions: <strong>Open .miz</strong> (or drop the file anywhere on the page), <strong>Save .miz</strong>, <strong>Flight packages</strong> and <strong>Wing</strong>, then <strong>Example</strong>. Until your wing is set up, <strong>Wing</strong> comes first, in amber; once it is set up, it goes back to its place. <strong>Flight packages</strong> (import packages, apply them to the mission) and <strong>Wing</strong> (the squadrons first, then the wing’s identity) each open in a window; <strong>Example</strong> also opens the Wing window. Once a mission is open, the page lays out in <strong>two columns from 1,100 px</strong>: the <strong>groups</strong> on the left (filters and tick boxes); on the right, <strong>pinned to the top</strong> of the view, the actions on the checked groups (<strong>Export</strong>, <strong>Delete</strong>, <strong>Dynamic Spawn…</strong>), the Dynamic Spawn panel, then the source mission and the weather. Below 1,100 px there is one column, the right-hand one first.</p></div>
      </div>

      <!-- Les modifications s'additionnent -->
      <div class="fm-prose">
        <h3 class="lang-block" data-lang="fr">Les modifications s’additionnent, puis se sauvegardent une fois</h3>
        <h3 class="lang-block" data-lang="en">Changes add up, then are saved once</h3>
        <div class="lang-block" data-lang="fr"><p>Appliquer des paquets, supprimer des groupes et valider un Dynamic Spawn <strong>modifient la mission ouverte</strong> sans rien télécharger : chacun ajoute 1 au <strong>compteur</strong> de <strong>Sauvegarder .miz</strong> (la pastille ambre), et un bandeau le rappelle en haut de la colonne de droite. <strong>Sauvegarder .miz</strong> — ou <strong>Ctrl+S</strong> — vérifie une dernière fois le texte de la mission et télécharge le .miz <strong>une seule fois</strong>. Ouvrir un autre .miz avant de sauvegarder demande confirmation, et quitter la page prévient. <strong>Exporter</strong> des groupes attend que les modifications soient sauvegardées : le paquet porte l’empreinte de la mission sauvegardée. Après un rechargement de la page, HQ affiche encore la mission mais le .miz n’est plus en mémoire : rouvrez-le pour la modifier.</p></div>
        <div class="lang-block" data-lang="en"><p>Applying packages, deleting groups and confirming a Dynamic Spawn <strong>change the open mission</strong> without downloading anything: each adds 1 to the <strong>counter</strong> on <strong>Save .miz</strong> (the amber badge), and a banner says so at the top of the right-hand column. <strong>Save .miz</strong> — or <strong>Ctrl+S</strong> — checks the mission text one last time and downloads the .miz <strong>once</strong>. Opening another .miz before saving asks for confirmation, and leaving the page warns you. <strong>Export</strong> of groups waits until the changes are saved: the package carries the saved mission’s fingerprint. After a page reload, HQ still shows the mission but the .miz is no longer in memory: open it again to change it.</p></div>
      </div>

      <!-- Créateur de Wing : identité -->
      <div class="fm-prose">
        <h3 class="lang-block" data-lang="fr">Le créateur de Wing — l'identité de l'escadre</h3>
        <h3 class="lang-block" data-lang="en">The Wing builder — the wing's identity</h3>
        <div class="lang-block" data-lang="fr"><p>C'est ici que vous décrivez votre escadre, une fois pour toutes : <strong>Nom court</strong> et <strong>Nom complet</strong> ; <strong>Titre d'application</strong> (le titre affiché en tête des briefings) ; <strong>Logo d'escadre</strong> (une image, réduite automatiquement) ; <strong>Tampon HQ</strong> (la mention tamponnée, type « HQ ░ MON ESCADRE »). Chaque champ se répercute sur le branding des autres modules.</p></div>
        <div class="lang-block" data-lang="en"><p>This is where you describe your wing, once and for all: <strong>Short name</strong> and <strong>Full name</strong>; <strong>App title</strong> (the title shown at the top of briefings); <strong>Wing logo</strong> (an image, scaled down automatically); <strong>HQ stamp</strong> (the stamped line, e.g. "HQ ░ MY WING"). Each field flows through to the other modules' branding.</p></div>
      </div>

      <!-- Créateur de Wing : escadrons -->
      <div class="fm-prose">
        <h3 class="lang-block" data-lang="fr">Les escadrons</h3>
        <h3 class="lang-block" data-lang="en">The squadrons</h3>
        <div class="lang-block" data-lang="fr"><p>Ajoutez autant d'escadrons que nécessaire. Pour chacun : <strong>nom</strong>, <strong>surnom</strong> (optionnel), <strong>callsign</strong> (l'identité radio, ex. FRANKEN), <strong>appareils</strong> (ex. Mi-24P, Mi-8) et <strong>logo</strong>. Le callsign sert de base aux indicatifs automatiques des pilotes dans le Briefing Generator (ex. « ANTON 1-1 »), toujours modifiables ensuite.</p></div>
        <div class="lang-block" data-lang="en"><p>Add as many squadrons as needed. For each: <strong>name</strong>, <strong>nickname</strong> (optional), <strong>callsign</strong> (the radio identity, e.g. FRANKEN), <strong>aircraft</strong> (e.g. Mi-24P, Mi-8), and <strong>logo</strong>. The callsign seeds the pilots' automatic call signs in the Briefing Generator (e.g. "ANTON 1-1"), always editable afterwards.</p></div>
      </div>

      <!-- Le bouton Exemple -->
      <div class="fm-prose">
        <h3 class="lang-block" data-lang="fr">Essayer l’exemple</h3>
        <h3 class="lang-block" data-lang="en">Trying the example</h3>
        <div class="lang-block" data-lang="fr"><p>Le bouton <strong>Exemple</strong> de la barre du haut (l’icône de feuille) ouvre une <strong>escadre de démonstration</strong> : la Task Force Kestrel, avec ses trois escadrons et leurs logos, dans la langue de l’interface au moment du clic, sans confirmation. Comme la configuration d’escadre est partagée par toute la suite, <strong>la vôtre est gardée</strong> : le message « Exemple chargé » propose <strong>Restaurer ma configuration</strong> pendant douze secondes, et tant que la sauvegarde existe, le même bouton figure en tête de la fenêtre <strong>Wing</strong>. Restaurer remet votre configuration telle qu’elle était et efface la sauvegarde ; si vous n’en aviez pas encore, la démonstration disparaît. Un nouveau clic sur Exemple ne remplace jamais la sauvegarde, même si vous avez modifié la démonstration entre-temps : seul Restaurer la supprime. L’ouverture d’une mission et le Mission Commander ne bougent pas.</p></div>
        <div class="lang-block" data-lang="en"><p>The <strong>Example</strong> button in the top bar (the sheet icon) opens a <strong>demonstration wing</strong>: Task Force Kestrel, with its three squadrons and their logos, in the interface language at the moment of the click, without confirmation. Because the wing configuration is shared by the whole suite, <strong>yours is kept</strong>: the “Example loaded” message offers <strong>Restore my configuration</strong> for twelve seconds, and as long as the backup exists the same button sits at the top of the <strong>Wing</strong> window. Restoring puts your configuration back exactly as it was and deletes the backup; if you had none yet, the demonstration goes away. Clicking Example again never replaces the backup, even if you edited the demonstration in the meantime: only Restore deletes it. Opening a mission and the Mission Commander are untouched.</p></div>
      </div>

      <!-- Créateur de Wing : partager -->
      <div class="fm-prose">
        <h3 class="lang-block" data-lang="fr">Partager la configuration</h3>
        <h3 class="lang-block" data-lang="en">Sharing the configuration</h3>
        <div class="lang-block" data-lang="fr"><p>Tout est <strong>sauvegardé automatiquement</strong> à chaque modification, et propagé en direct aux autres modules. <strong>Exportez</strong> la configuration en fichier <code>.json</code> pour la distribuer à l'escadre ; chacun l'<strong>importe</strong> pour retrouver exactement le même branding. Un bouton <strong>réinitialise</strong> au wing par défaut.</p></div>
        <div class="lang-block" data-lang="en"><p>Everything is <strong>saved automatically</strong> on every change, and propagated live to the other modules. <strong>Export</strong> the configuration as a <code>.json</code> file to hand it to the wing; everyone <strong>imports</strong> it to get exactly the same branding. A button <strong>resets</strong> to the default wing.</p></div>
      </div>

      <!-- Ouvrir une mission -->
      <div class="fm-prose">
        <h3 class="lang-block" data-lang="fr">Ouvrir une mission</h3>
        <h3 class="lang-block" data-lang="en">Opening a mission</h3>
        <div class="lang-block" data-lang="fr"><p>HQ ouvre un <strong>.miz</strong> et en extrait un <strong>instantané en lecture seule</strong> : les groupes clients (hélicoptères et avions pilotables), présentés par leur <strong>callsign</strong>, avec leurs fréquences radio, la fréquence de groupe, la livrée et la météo de la mission. L'instantané est partagé avec les autres modules et exportable. À cette étape, HQ <strong>lit</strong> — il ne modifie rien.</p></div>
        <div class="lang-block" data-lang="en"><p>HQ opens a <strong>.miz</strong> and extracts a <strong>read-only snapshot</strong>: the client groups (player-flyable helicopters and planes), shown by their <strong>callsign</strong>, with their radio frequencies, group frequency, livery, and the mission weather. The snapshot is shared with the other modules and exportable. At this stage HQ <strong>reads</strong> — it changes nothing.</p></div>
      </div>

      <!-- Dynamic Spawn écrit -->
      <div class="fm-prose">
        <h3 class="lang-block" data-lang="fr">Dynamic Spawn</h3>
        <h3 class="lang-block" data-lang="en">Dynamic Spawn</h3>
        <div class="lang-block" data-lang="fr"><p>HQ peut écrire le Dynamic Spawn dans la mission : cochez des groupes dans la liste, puis <strong>Dynamic Spawn…</strong>. Un groupe devient un <strong>template</strong> (case « Template ») et se lie, pour son type d’appareil, aux aérodromes, FARP et navires de votre choix, avec le départ moteur tournant de chaque lieu. <strong>Prérequis :</strong> seuls les aérodromes, FARP et navires dont le Dynamic Spawn est activé dans l’éditeur de mission, et dont la liste d’appareils contient le type du template, sont proposés pour un template ; la fenêtre dit pourquoi les autres ne sont pas proposés. HQ n’active jamais le Dynamic Spawn et ne crée jamais un type d’appareil : cela se fait dans l’éditeur de mission. Démarquer un template remet à zéro ses liens ; un lieu déjà lié à un autre template pour ce type est signalé, et le lien est remplacé si vous le cochez. HQ ne modifie que les fichiers <code>mission</code> et <code>warehouses</code> du .miz, les relit avant de rendre le fichier, et signale dans le compte rendu un template de plusieurs appareils ou une coalition différente entre le template et le lieu, à vérifier dans DCS.</p></div>
        <div class="lang-block" data-lang="en"><p>HQ can write Dynamic Spawn into the mission: check groups in the list, then <strong>Dynamic Spawn…</strong>. A group becomes a <strong>template</strong> (the “Template” box) and is linked, for its aircraft type, to the airfields, FARPs and ships of your choice, with each place’s hot-start setting. <strong>Prerequisite:</strong> only airfields, FARPs and ships that have Dynamic Spawn enabled in the mission editor, and whose aircraft list contains the template’s type, are offered for a template; the window says why the others are not offered. HQ never enables Dynamic Spawn and never creates an aircraft type: that is done in the mission editor. Unmarking a template resets its links to zero; a place already linked to another template for that type is flagged, and the link is replaced if you check it. HQ only changes the .miz’s <code>mission</code> and <code>warehouses</code> files, reads them back before handing over the file, and reports in the summary a template of more than one aircraft or a different coalition between the template and the place, to be checked in DCS.</p></div>
      </div>

      <!-- Commander à venir -->
      <div class="fm-callout note">
        <div class="lang-block" data-lang="fr">Le rôle Commander arrive — HQ embarque déjà de quoi réinjecter des modifications ciblées (fréquences, livrées, routes…) dans un .miz et produire une mission corrigée. Cette fonction s'activera quand les modules Flight Lead permettront de préparer ces modifications. D'ici là, HQ se concentre sur l'identité d'escadre et la lecture de mission.</div>
        <div class="lang-block" data-lang="en">The Commander role is coming — HQ already carries what it needs to write targeted changes (frequencies, liveries, routes…) back into a .miz and produce a corrected mission. This will activate once the Flight Lead modules let you prepare those changes. Until then, HQ focuses on wing identity and mission reading.</div>
      </div>

    </div><!-- /fm-chapter -->
  </section><!-- /page-hq -->


  <!-- ===== PAGE FC ===== -->
  <section id="page-fc" class="fm-page hidden">
    <div class="fm-chapter" style="--chapter-accent:#D0784A; --chapter-accent-rgb:208,120,74;">

      <button class="fm-back-btn" onclick="navigate('index')" data-i18n="btn.back">◄ Index</button>

      <div class="fm-hero">
        <img class="fm-hero-img" src="{FC_TILE_SRC}" alt="Flight Configurator" draggable="false">
        <div class="fm-hero-pin" aria-hidden="true"></div>
        <div class="fm-hero-caption">
          <div><div class="fm-hero-monogram">F·C</div></div>
          <div>
            <div class="fm-hero-title" data-i18n="fc.hero.title">Flight Configurator</div>
            <div class="fm-hero-sub" data-i18n="fc.hero.sub">Un groupe prêt à appliquer : radios, emport, livrée</div>
          </div>
        </div>
      </div>

      <!-- À quoi ça sert -->
      <div class="fm-prose">
        <h3 class="lang-block" data-lang="fr">À quoi ça sert</h3>
        <h3 class="lang-block" data-lang="en">What it's for</h3>
        <div class="lang-block" data-lang="fr"><p>Le Flight Configurator est l'outil du <strong>Flight Lead</strong> : il prépare <strong>un ou plusieurs groupes</strong> — identité (nom du groupe, coalition, jusqu'à quatre unités dont <strong>chacune a son propre type d'appareil</strong>), <strong>radios</strong>, <strong>emport</strong> composé sur la vue de face de l'appareil ou repris d'un preset, <strong>livrée</strong> — et les exporte en <strong>paquet de vol</strong> que le <strong>Mission Commander</strong> applique à sa mission avec HQ. Quatre appareils : <strong>Mi-24P</strong>, <strong>Mi-8MT</strong>, <strong>F-4E-45MC</strong> et <strong>Mirage F1EE</strong>.</p><p>Le module ne suppose rien de la mission cible : un paquet peut s'appliquer à <strong>n'importe quelle mission</strong> (HQ retrouve chaque groupe par son <strong>nom</strong>, espaces de bord ignorés, et sa <strong>coalition</strong> ; le type n'y entre pas : il sert à ne poser radios, emport et livrée que sur les unités de même type). Un groupe peut donc mélanger des appareils. Chaque partie est facultative ; une partie laissée vide n'est pas touchée par HQ.</p></div>
        <div class="lang-block" data-lang="en"><p>The Flight Configurator is the <strong>Flight Lead</strong>'s tool: it prepares <strong>one or more groups</strong> — identity (group name, coalition, up to four units, <strong>each with its own aircraft type</strong>), <strong>radios</strong>, <strong>loadout</strong> built on the aircraft's front view or started from a preset, <strong>livery</strong> — and exports them as a <strong>flight package</strong> that the <strong>Mission Commander</strong> applies to the mission with HQ. Four aircraft: <strong>Mi-24P</strong>, <strong>Mi-8MT</strong>, <strong>F-4E-45MC</strong> and <strong>Mirage F1EE</strong>.</p><p>The module assumes nothing about the target mission: a package can be applied to <strong>any mission</strong> (HQ finds each group by its <strong>name</strong>, spaces at either end ignored, and its <strong>coalition</strong>; the type does not enter into it: it decides which units receive radios, loadout and livery, those of the same type only). A group can therefore mix aircraft. Every part is optional; a part left empty is not touched by HQ.</p></div>
      </div>

      <!-- Schéma -->
      <div class="fm-schema">
        <svg viewBox="0 0 720 300" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Flight Configurator">
          <defs>
            <marker id="fca" markerWidth="8" markerHeight="8" refX="6.5" refY="3.5" orient="auto"><path d="M0,0 L8,3.5 L0,7 Z" fill="currentColor" opacity=".6"/></marker>
          </defs>
          <text x="360" y="26" text-anchor="middle" font-size="13" letter-spacing="3" fill="currentColor" opacity=".9" class="lang-block" data-lang="fr">DU GROUPE AU PAQUET</text>
          <text x="360" y="26" text-anchor="middle" font-size="13" letter-spacing="3" fill="currentColor" opacity=".9" class="lang-block" data-lang="en">FROM GROUP TO PACKAGE</text>
          <line x1="150" y1="34" x2="570" y2="34" stroke="currentColor" stroke-width=".6" opacity=".3"/>

          <rect class="sv-box" x="30" y="70" width="150" height="44" rx="3" stroke="currentColor" stroke-width="1.2"/>
          <text x="105" y="90" text-anchor="middle" font-size="10.5" fill="currentColor" class="lang-block" data-lang="fr">Mission chargée dans HQ</text>
          <text x="105" y="90" text-anchor="middle" font-size="10.5" fill="currentColor" class="lang-block" data-lang="en">Mission loaded in HQ</text>
          <text x="105" y="105" text-anchor="middle" font-size="8" fill="currentColor" opacity=".9" class="lang-block" data-lang="fr">un modèle possible</text>
          <text x="105" y="105" text-anchor="middle" font-size="8" fill="currentColor" opacity=".9" class="lang-block" data-lang="en">one possible model</text>
          <rect class="sv-box" x="30" y="136" width="150" height="44" rx="3" stroke="currentColor" stroke-width="1.2"/>
          <text x="105" y="156" text-anchor="middle" font-size="10.5" fill="currentColor" class="lang-block" data-lang="fr">Paquet de vol</text>
          <text x="105" y="156" text-anchor="middle" font-size="10.5" fill="currentColor" class="lang-block" data-lang="en">Flight package</text>
          <text x="105" y="171" text-anchor="middle" font-size="8" fill="currentColor" opacity=".9">.json · .zip</text>
          <line x1="180" y1="92" x2="268" y2="124" stroke="currentColor" stroke-width="1.2" opacity=".6" marker-end="url(#fca)"/>
          <line x1="180" y1="158" x2="268" y2="132" stroke="currentColor" stroke-width="1.2" opacity=".6" marker-end="url(#fca)"/>
          <text x="224" y="86" text-anchor="middle" font-size="9" fill="currentColor" opacity=".9" class="lang-block" data-lang="fr">Importer</text>
          <text x="224" y="86" text-anchor="middle" font-size="9" fill="currentColor" opacity=".9" class="lang-block" data-lang="en">Import</text>

          <rect class="sv-box" x="270" y="92" width="180" height="76" rx="3" stroke="#D0784A" stroke-width="2"/>
          <text x="360" y="124" text-anchor="middle" font-size="16" fill="currentColor" letter-spacing="1.5">Flight Configurator</text>
          <text x="360" y="142" text-anchor="middle" font-size="8.5" fill="currentColor" opacity=".9" class="lang-block" data-lang="fr">identité · radios · emport · livrée</text>
          <text x="360" y="142" text-anchor="middle" font-size="8.5" fill="currentColor" opacity=".9" class="lang-block" data-lang="en">identity · radios · loadout · livery</text>
          <text x="360" y="156" text-anchor="middle" font-size="8.5" fill="currentColor" opacity=".9" class="lang-block" data-lang="fr">route du Route Planner, reprise</text>
          <text x="360" y="156" text-anchor="middle" font-size="8.5" fill="currentColor" opacity=".9" class="lang-block" data-lang="en">Route Planner route, kept in step</text>

          <line x1="450" y1="130" x2="538" y2="130" stroke="currentColor" stroke-width="1.2" opacity=".6" marker-end="url(#fca)"/>
          <text x="494" y="122" text-anchor="middle" font-size="9" fill="currentColor" opacity=".9" class="lang-block" data-lang="fr">Exporter</text>
          <text x="494" y="122" text-anchor="middle" font-size="9" fill="currentColor" opacity=".9" class="lang-block" data-lang="en">Export</text>
          <rect class="sv-box sv-m-hq" x="540" y="100" width="150" height="60" rx="3" stroke-width="2"/>
          <text x="615" y="126" text-anchor="middle" font-size="14" fill="currentColor" letter-spacing="2">HQ</text>
          <text x="615" y="144" text-anchor="middle" font-size="8" fill="currentColor" opacity=".9" class="lang-block" data-lang="fr">applique le paquet à la mission</text>
          <text x="615" y="144" text-anchor="middle" font-size="8" fill="currentColor" opacity=".9" class="lang-block" data-lang="en">applies the package to the mission</text>

          <rect class="sv-box" x="270" y="214" width="180" height="40" rx="3" stroke="currentColor" stroke-width="1" stroke-opacity=".6" stroke-dasharray="4 3"/>
          <text x="360" y="231" text-anchor="middle" font-size="10" fill="currentColor" class="lang-block" data-lang="fr">Mes presets</text>
          <text x="360" y="231" text-anchor="middle" font-size="10" fill="currentColor" class="lang-block" data-lang="en">My presets</text>
          <text x="360" y="245" text-anchor="middle" font-size="8" fill="currentColor" opacity=".9" class="lang-block" data-lang="fr">.lua chargés, emports gardés</text>
          <text x="360" y="245" text-anchor="middle" font-size="8" fill="currentColor" opacity=".9" class="lang-block" data-lang="en">loaded .lua, kept loadouts</text>
          <line x1="360" y1="214" x2="360" y2="172" stroke="currentColor" stroke-width="1.2" opacity=".6" stroke-dasharray="4 3" marker-end="url(#fca)"/>
        </svg>
        <div class="fm-schema-legend">
          <span class="lang-block" data-lang="fr">Fig. 1 — On importe, on complète, on exporte un paquet ; HQ l'applique. Les presets ne partent jamais dans le paquet : seul l'emport y est écrit.</span>
          <span class="lang-block" data-lang="en">Fig. 1 — Import, complete, export a package; HQ applies it. Presets never leave in the package: only the loadout is written.</span>
        </div>
      </div>

      <!-- Les groupes -->
      <div class="fm-prose">
        <h3 class="lang-block" data-lang="fr">Les groupes et les unités</h3>
        <h3 class="lang-block" data-lang="en">Groups and units</h3>
        <div class="lang-block" data-lang="fr"><p><strong>Ajoutez un groupe</strong> : nom du groupe, coalition, et pour chaque unité son <strong>type</strong> (en tête de sa carte), son nom, son indicatif, son numéro de bord et sa livrée. Une unité ajoutée prend le type de la dernière du groupe ; changer le type d'une unité efface ses radios et son emport (une confirmation si elle en a). Deux groupes d'une même coalition ne portent pas le même nom : l'export est refusé tant que c'est le cas, et la barre nomme les doublons. Un groupe se <strong>replie</strong> (titre et résumé sur une ligne : « 2 × Mi-24P · route 4 pts · radios 6 canaux · emport … », ou « 1 × Mi-24P + 1 × Mi-8MT » pour un groupe mixte) ; « Tout replier » agit sur tous les groupes, et dès qu'il y a plus de deux groupes, seul celui sur lequel vous travaillez reste déplié. Chaque groupe garde un identifiant interne stable qui n'est jamais écrit dans le paquet. Vos groupes sont partagés avec le Route Planner : un groupe créé ou renommé dans l'un apparaît dans l'autre.</p><p>La <strong>route</strong> d'un groupe vient soit du choix d'une route du Route Planner, dans le bloc ROUTE, soit d'un import (paquet du Route Planner, mission de HQ). La carte du groupe la résume sur une ligne avec un petit croquis ; le détail et le retrait sont au bloc ROUTE (voir « La route »).</p></div>
        <div class="lang-block" data-lang="en"><p><strong>Add a group</strong>: group name, coalition, and for each unit its <strong>type</strong> (at the head of its card), name, call sign, onboard number and livery. A unit you add takes the type of the group's last one; changing a unit's type clears its radios and loadout (with a confirmation if it has any). Two groups of the same coalition do not share a name: the export is refused while they do, and the bar names the duplicates. A group <strong>folds</strong> (title and a one-line summary: “2 × Mi-24P · route 4 pts · radios 6 channels · loadout …”, or “1 × Mi-24P + 1 × Mi-8MT” for a mixed group); “Fold all” acts on every group, and as soon as there are more than two groups only the one you are working on stays open. Each group keeps a stable internal identifier that is never written to the package. Your groups are shared with the Route Planner: a group created or renamed in one appears in the other.</p><p>A group's <strong>route</strong> comes either from picking a Route Planner route in the ROUTE block, or from an import (Route Planner package, HQ mission). The group card sums it up on one line with a small sketch; the detail and the removal are in the ROUTE block (see “The route”).</p></div>
      </div>

      <!-- La route -->
      <div class="fm-prose">
        <h3 class="lang-block" data-lang="fr">La route</h3>
        <h3 class="lang-block" data-lang="en">The route</h3>
        <div class="lang-block" data-lang="fr"><p>Le bloc <strong>ROUTE</strong>, le premier de la colonne de droite (au-dessus d'EMPORT), parle du groupe de l'unité choisie. <strong>Un groupe n'a qu'une seule route</strong> : on la choisit parmi celles du Route Planner (deux points au moins) en touchant une vignette, les routes que le Route Planner lie à ce groupe d'abord, les autres ensuite ; « Changer de route » rouvre le choix, « Retirer » vide la route. Le groupe garde la copie des points : c'est elle que le paquet porte, comme avant. Le lien avec la route du Route Planner (l'identifiant stable que chaque route y reçoit) reste dans le navigateur et dans le fichier de travail, <strong>jamais dans le paquet</strong> ; une route importée par la fenêtre d'import remplace celle du groupe et coupe ce lien.</p><p>La route s'affiche en <strong>croquis sur papier</strong> (points de navigation, leurs noms, sens de la route, nord, échelle) et, dessous, en <strong>table des branches</strong> : le cap <strong>magnétique</strong> et la distance de chaque branche (en NM ou en km, selon l'unité partagée), et le total. Le cap est le cap vrai moins la déclinaison au départ de la branche : la valeur saisie au Route Planner quand elle y est en mode manuel, sinon le calcul à la date de la mission chargée dans HQ, sinon à l'année du Route Planner, sinon à 1985 ; la note sous la table dit laquelle. Le croquis n'est qu'un rappel, sans interaction : <strong>la route se trace au Route Planner</strong>.</p><p><strong>La reprise est automatique</strong> : à l'ouverture du module, quand le Route Planner enregistre et au retour sur l'onglet, chaque groupe lié reprend les points de sa route s'ils ont changé, et son nom (un message le dit). Si la route est supprimée au Route Planner, ou n'a plus deux points, le groupe garde sa dernière copie et son lien, et le bloc le dit ; si elle revient, la reprise reprend. Si le Route Planner est sur un autre théâtre que le module, ou n'a pas encore été ouvert sur cet appareil, rien n'est repris.</p></div>
        <div class="lang-block" data-lang="en"><p>The <strong>ROUTE</strong> block, the first in the right-hand column (above LOADOUT), is about the group of the chosen unit. <strong>A group has just one route</strong>: you pick it from the Route Planner's routes (two points at least) by touching a thumbnail, the routes the Route Planner links to this group first, the others after; “Change route” reopens the choice, “Remove” empties the route. The group keeps its copy of the points: that copy is what the package carries, as before. The link with the Route Planner route (the stable identifier each route gets there) stays in the browser and in the working file, <strong>never in the package</strong>; a route imported through the import window replaces the group's route and cuts that link.</p><p>The route is shown as a <strong>paper sketch</strong> (waypoints, their names, direction of travel, north, scale) and, below it, as a <strong>leg table</strong>: each leg's <strong>magnetic</strong> heading and distance (in NM or km, as per the shared unit), and the total. The heading is the true heading minus the variation at the start of the leg: the value typed in the Route Planner when it is in manual mode there, otherwise the calculation at the date of the mission loaded in HQ, otherwise at the Route Planner's year, otherwise at 1985; the note under the table says which. The sketch is only a reminder, with no interaction: <strong>the route is drawn in the Route Planner</strong>.</p><p><strong>The route follows automatically</strong>: when the module opens, when the Route Planner saves and when you return to the tab, each linked group takes the points of its route if they changed, and its name (a message says so). If the route is deleted in the Route Planner, or no longer has two points, the group keeps its last copy and its link, and the block says so; if the route comes back, it is followed again. If the Route Planner is on a different theatre from the module, or has not been opened on this device yet, nothing is followed.</p></div>
      </div>

      <!-- La barre -->
      <div class="fm-prose">
        <h3 class="lang-block" data-lang="fr">Ouvrir, Sauvegarder, Importer, Exporter, Effacer</h3>
        <h3 class="lang-block" data-lang="en">Open, Save, Import, Export, Clear</h3>
        <div class="lang-block" data-lang="fr"><p><strong>Ouvrir ▾ › Ouvrir une configuration…</strong> et <strong>Sauvegarder</strong> gèrent le <strong>fichier de travail</strong> du module (un <code>.json</code> qui porte vos groupes et « Mes presets »). <kbd>Ctrl</kbd>+<kbd>S</kbd> (<kbd>Cmd</kbd>+<kbd>S</kbd> sur Mac) fait le même geste que <strong>Sauvegarder</strong>. Au Flight Configurator, <strong>Ouvrir ▾ › Importer des groupes…</strong> ouvre la même fenêtre que <strong>Ouvrir ▾ › Importer des routes…</strong> au Route Planner : la mission chargée dans HQ, le briefing en cours du Briefing Generator, ou un fichier (paquet de vol <code>.json</code> ou <code>.zip</code>, briefing). Cochez les groupes et, pour chacun, ce qu'il apporte (route, radios, emport, livrée). Un groupe de même nom (majuscules comprises) et de même coalition est complété, sinon il est créé ; une route importée devient une route du Route Planner. Du briefing viennent les groupes, leur nombre d'appareils et le plan radio de leur type ; un appareil que la suite ne connaît pas sous ce nom arrive sans type, à choisir. Une unité sans type se règle une fois son type choisi ; le paquet ne s'exporte qu'une fois chaque type choisi. <strong>Exporter</strong> écrit le paquet pour le Mission Commander ; <strong>Effacer</strong> vide le module (vos presets restent). Une source chargée se replie en une ligne (« changer » la rouvre) pour laisser la place à la liste. Le théâtre se choisit dans la barre, comme au Route Planner et au Datacard Generator, et les trois le partagent ; si les groupes sont sur un autre théâtre, un bandeau propose d’y revenir ou de retirer leurs routes.</p></div>
        <div class="lang-block" data-lang="en"><p><strong>Open ▾ › Open a configuration…</strong> and <strong>Save</strong> handle the module's <strong>working file</strong> (a <code>.json</code> that carries your groups and “My presets”). <kbd>Ctrl</kbd>+<kbd>S</kbd> (<kbd>Cmd</kbd>+<kbd>S</kbd> on a Mac) does the same as <strong>Save</strong>. In the Flight Configurator, <strong>Open ▾ › Import groups…</strong> opens the same window as <strong>Open ▾ › Import routes…</strong> in the Route Planner: the mission loaded in HQ, the Briefing Generator's current briefing, or a file (flight package <code>.json</code> or <code>.zip</code>, briefing). Tick the groups and, for each, what it brings (route, radios, loadout, livery). A group with the same name (case included) and coalition is completed, otherwise it is created; an imported route becomes a Route Planner route. A briefing brings its groups, their number of aircraft and the radio plan of their type; an aircraft the suite does not know by that name arrives without a type, to be picked. A unit without a type is set up once its type is picked; the package exports only once every type is picked. <strong>Export</strong> writes the package for the Mission Commander; <strong>Clear</strong> empties the module (your presets stay). A loaded source folds into one line (“change” reopens it) to leave room for the list. The theatre is picked in the toolbar, as in the Route Planner and the Datacard Generator, and all three share it; if the groups are on another theatre, a banner offers to go back to it or to remove their routes.</p></div>
      </div>

      <!-- Radios -->
      <div class="fm-prose">
        <h3 class="lang-block" data-lang="fr">Les radios</h3>
        <h3 class="lang-block" data-lang="en">Radios</h3>
        <div class="lang-block" data-lang="fr"><p>Pour chaque poste de l'appareil, un champ par canal, numéroté comme au cockpit (le R-863 et le R-828 pour les deux hélicoptères, deux postes pour le F-4E et le Mirage). Les deux hélicoptères ont aussi leur poste HF, que la mission ne pré-règle pas (Jadro-1I sur le Mi-24P, Jadro-1A sur le Mi-8MT) : jusqu'à cinq fréquences, sans numéro de canal, que la datacard reprend et que HQ n'écrit jamais dans la mission. Une fréquence se saisit en MHz et doit tomber dans <strong>la bande du poste</strong>, que le module écrit <strong>sous le titre de chaque poste</strong> : R-863 de 100 à 149,975 et de 220 à 399,9 MHz, R-828 de 20 à 59,9 MHz, Jadro-1I de 2 à 17,999 MHz (Mi-24P) ; R-863 de 100 à 149,975 et de 220 à 399,975 MHz, R-828 de 20 à 59,975 MHz, Jadro-1A de 2 à 17,999 MHz (Mi-8MT) ; poste COMM de 225 à 399,95 MHz et poste AUX (réception seule) de 265 à 284,9 MHz (F-4E) ; TRAP 136 de 118 à 143,975 et de 225 à 399,975 MHz, TRAP 137B de 225 à 399,975 MHz (Mirage F1). Une valeur hors bande ou qui n'est pas un nombre est <strong>refusée avec un message qui cite la bande</strong> ; une fréquence hors bande déjà présente (importée, ou saisie avant un changement de bande) est gardée et signalée, sans bloquer l'export. « Recopier sur les autres unités du groupe » écrit les mêmes canaux et fréquences sur les autres unités <strong>du même type</strong> (sans autre unité de ce type, le bouton est inactif). Un canal vide n'est pas écrit ; les modulations ne le sont pas non plus.</p></div>
        <div class="lang-block" data-lang="en"><p>For each radio of the aircraft, one field per channel, numbered as in the cockpit (the R-863 and R-828 for the two helicopters, two radios for the F-4E and the Mirage). The two helicopters also have their HF radio, which missions do not preset (Jadro-1I on the Mi-24P, Jadro-1A on the Mi-8MT): up to five frequencies, with no channel number, that the datacard shows and that HQ never writes to the mission. A frequency is typed in MHz and must fall inside <strong>the radio's band</strong>, which the module writes <strong>under each radio's title</strong>: R-863 from 100 to 149.975 and from 220 to 399.9 MHz, R-828 from 20 to 59.9 MHz, Jadro-1I from 2 to 17.999 MHz (Mi-24P); R-863 from 100 to 149.975 and from 220 to 399.975 MHz, R-828 from 20 to 59.975 MHz, Jadro-1A from 2 to 17.999 MHz (Mi-8MT); COMM radio from 225 to 399.95 MHz and AUX radio (receive only) from 265 to 284.9 MHz (F-4E); TRAP 136 from 118 to 143.975 and from 225 to 399.975 MHz, TRAP 137B from 225 to 399.975 MHz (Mirage F1). A value outside the band, or that is not a number, is <strong>refused with a message that quotes the band</strong>; an out-of-band frequency already there (imported, or typed before a band changed) is kept and flagged, without blocking the export. “Copy to the other units of the group” writes the same channels and frequencies on the other units <strong>of the same type</strong> (with no other unit of that type, the button is inactive). An empty channel is not written; modulations are not written either.</p></div>
      </div>

      <!-- Emport -->
      <div class="fm-prose">
        <h3 class="lang-block" data-lang="fr">L'emport</h3>
        <h3 class="lang-block" data-lang="en">The loadout</h3>
        <div class="lang-block" data-lang="fr"><p>L'<strong>unité choisie</strong> (touchez sa carte : elle est marquée ; il y en a toujours une dès qu'il y a un groupe) a son emport affiché à droite, sans bouton : la <strong>vue de face</strong> de l'appareil, avec une case et un trait pointillé par station. Sur écran étroit, « Voir l'emport ↓ » y mène. Voici ce que montre la vue : une case et un trait pointillé par station, une liste d'armes permises par station, la <strong>masse totale</strong>. « Symétrique » pose sur la station jumelle l'arme miroir (la même, sinon sa variante gauche/droite, sinon l'unique arme de même nom) ; la jumelle est dite en clair sous la liste, et la ligne « pas d'équivalent » le dit quand il n'y en a pas ; un <strong>réglage d'arme</strong> (code laser, fusée…) suit sa station tant que l'arme n'est pas changée. Quand une même arme existe en deux versions, gauche et droite (le Kord du Mi-24P, les armes du F-4E), son nom se termine par <strong>« (gauche) »</strong> ou <strong>« (droite) »</strong> ; les tables ne changent pas, seul l'affichage. Dessous, le carburant, les leurres, les paillettes et le canon, <strong>visibles dès qu'une unité est choisie</strong>, avec ou sans arme : aux valeurs de son emport, sinon à celles de la table. Le carburant a, sous son champ en kg, une <strong>barre de 0 à 100 %</strong> : la déplacer écrit les kg (arrondis au kg), taper des kg la déplace ; le paquet ne garde que les kg. Régler une unité « non renseigné » lui donne un <strong>emport vide</strong> qui porte ces réglages (HQ les posera sans arme, et une ligne le dit). Une valeur hors de la table de l'appareil est <strong>ramenée à sa limite</strong> (0 pour une valeur négative), la ligne d'état en donne le nombre. Modifier une station ne demande aucun nom de preset.</p><p><strong>Mes presets</strong> (sous l'emport) : « Garder dans mes presets… » enregistre l'emport composé sous un nom (le bouton, comme « Vider l'emport », n'agit que si une station porte une arme) ; « Charger des presets (.lua) » reprend les fichiers de presets de l'escadre, qui deviennent des points de départ dans « Partir de » (un nom déjà pris est ignoré, et le bloc le dit). « Partir de » propose aussi, après les presets, le groupe <strong>« Unités du module »</strong> : chaque autre unité <strong>du même type</strong>, tous groupes confondus, qui a un emport (« Copier : Groupe · Unité ») ; le choix <strong>recopie</strong> stations, réglages d'armes, carburant, leurres, paillettes et canon, l'emport porte l'étiquette « copié de … » (puis « modifié » s'il change), et <strong>aucun lien ne reste</strong> avec l'unité source. Mes presets vivent dans le navigateur et dans le fichier de travail, <strong>nulle part ailleurs</strong> ; <strong>ce qui part dans le paquet, c'est un emport, jamais un preset</strong>.</p></div>
        <div class="lang-block" data-lang="en"><p>The <strong>chosen unit</strong> (touch its card: it is marked; one is always chosen as soon as there is a group) has its loadout shown on the right, with no button: the aircraft's <strong>front view</strong>. On a narrow screen, “See the loadout ↓” leads there. What the view shows: a cell and a dotted leader per station, a list of permitted weapons per station, the <strong>total mass</strong>. “Symmetric” puts the mirror weapon on the twin station (the same one, else its left/right variant, else the only weapon with the same name); the twin is named in plain words under the list, and the “no equivalent” line says so when there is none; a <strong>weapon setting</strong> (laser code, fuze…) follows its station as long as the weapon is not changed. When the same weapon exists in two versions, left and right (the Mi-24P's Kord, the F-4E's weapons), its name ends with <strong>“(left)”</strong> or <strong>“(right)”</strong>; the tables do not change, only the display. Below, fuel, flares, chaff and gun, <strong>shown as soon as a unit is chosen</strong>, with or without a weapon: at the values of its loadout, otherwise those of the table. Fuel has, under its kg field, a <strong>0 to 100 % bar</strong>: moving it writes the kg (rounded to the kg), typing kg moves it; the package keeps only the kg. Setting a “not set” unit gives it an <strong>empty loadout</strong> that carries those values (HQ will set them with no weapon, and a line says so). A value outside the aircraft's table is <strong>brought back to its limit</strong> (0 for a negative value), the status line gives the count. Changing a station never asks for a preset name.</p><p><strong>My presets</strong> (under the loadout): “Keep in my presets…” saves the composed loadout under a name (the button, like “Empty the loadout”, only acts when a station holds a weapon); “Load presets (.lua)” takes the squadron's preset files, which become starting points in “Start from” (a name already taken is ignored, and the block says so). “Start from” also offers, after the presets, the <strong>“Module units”</strong> group: every other unit <strong>of the same type</strong>, in any group, that has a loadout (“Copy: Group · Unit”); the choice <strong>copies</strong> stations, weapon settings, fuel, flares, chaff and gun, the loadout is labelled “copied from …” (then “modified” if it changes), and <strong>no link remains</strong> with the source unit. My presets live in the browser and in the working file, <strong>nowhere else</strong>; <strong>what leaves in the package is a loadout, never a preset</strong>.</p></div>
      </div>

      <!-- Livrée -->
      <div class="fm-prose">
        <h3 class="lang-block" data-lang="fr">La livrée</h3>
        <h3 class="lang-block" data-lang="en">Livery</h3>
        <div class="lang-block" data-lang="fr"><p>Le champ est un <strong>texte libre</strong> (l'identifiant de livrée de DCS). Il propose en suggestion, dans <strong>un panneau aux couleurs du thème</strong> (flèches, Entrée, Échap, ou un toucher), les livrées <strong>déjà vues pour le type de l'unité</strong> : dans la mission chargée dans HQ, dans les paquets importés et dans les groupes du module ; la liste se filtre par ce qu'on tape (sans casse ni accents), et une livrée écrite de deux façons qui ne diffèrent que par la casse n'y figure qu'une fois, dans la graphie la plus fréquente. Aucune liste n'est écrite d'avance.</p></div>
        <div class="lang-block" data-lang="en"><p>The field is <strong>free text</strong> (DCS's livery identifier). It suggests, in <strong>a panel in the theme's colours</strong> (arrows, Enter, Esc, or a touch), the liveries <strong>already seen for the unit's type</strong>: in the mission loaded in HQ, in imported packages and in the module's groups; the list filters as you type (case and accents ignored), and a livery written two ways that differ only by case appears once, in the most frequent spelling. No list is written in advance.</p></div>
      </div>

      <!-- Paquet -->
      <div class="fm-prose">
        <h3 class="lang-block" data-lang="fr">Le paquet</h3>
        <h3 class="lang-block" data-lang="en">The package</h3>
        <div class="lang-block" data-lang="fr"><p>Un fichier <code>.json</code> de format <code>dcs-flight-package-v2</code>, nommé <code>paquet_&lt;1er groupe&gt;_&lt;horodatage&gt;.json</code> comme celui de HQ. Par groupe : nom du groupe (sans espaces de bord), coalition, route, et par unité nom, <strong>type</strong>, indicatif, livrée, radios, <code>payload</code> ; le groupe n'a pas de type. Un paquet de l'ancien format (<code>v1</code>, un type au groupe) se lit encore : son type vaut pour chacune de ses unités. Une partie non renseignée sort en <strong><code>null</code></strong> : HQ n'y touche pas. Le paquet ne nomme aucune mission source. HQ applique aujourd'hui les radios, l'emport, la livrée et la route ; l'indicatif et le numéro de bord voyagent déjà, mais HQ ne les applique pas encore.</p></div>
        <div class="lang-block" data-lang="en"><p>A <code>.json</code> file of format <code>dcs-flight-package-v2</code>, named <code>paquet_&lt;first group&gt;_&lt;timestamp&gt;.json</code> like HQ's. Per group: group name (trimmed), coalition, route, and per unit name, <strong>type</strong>, call sign, livery, radios, <code>payload</code>; the group has no type. A package in the previous format (<code>v1</code>, one type per group) still opens: its type applies to each of its units. A part left blank is written as <strong><code>null</code></strong>: HQ does not touch it. The package names no source mission. HQ applies radios, loadout, livery and route today; the call sign and onboard number already travel, but HQ does not apply them yet.</p></div>
      </div>

      <!-- Crédits et limites -->
      <div class="fm-callout note">
        <div class="lang-block" data-lang="fr">Crédits : les tables d'armes viennent de <strong>pydcs</strong> (LGPL-3.0), reprises de Mission Tools ; les dessins de la vue de face sont de <strong>Goldwolf</strong> (DCS Reference Guide), utilisés avec son accord et <strong>hors de la licence MIT</strong> du dépôt (voir <code>data/views/LICENSE.md</code>). Limite : le module n'applique aucune règle d'emport — il écrit ce qu'on compose, il ne dit pas que DCS l'acceptera.</div>
        <div class="lang-block" data-lang="en">Credits: the weapon tables come from <strong>pydcs</strong> (LGPL-3.0), taken from Mission Tools; the front-view drawings are by <strong>Goldwolf</strong> (DCS Reference Guide), used with his permission and <strong>outside the repository's MIT licence</strong> (see <code>data/views/LICENSE.md</code>). Limit: the module applies no loadout rule — it writes what you compose, it does not say that DCS will accept it.</div>
      </div>

    </div><!-- /fm-chapter -->
  </section><!-- /page-fc -->


  <!-- ===== PAGE BG ===== -->
  <section id="page-bg" class="fm-page hidden">
    <div class="fm-chapter" style="--chapter-accent:#c0892a; --chapter-accent-rgb:192,137,42;">

      <button class="fm-back-btn" onclick="navigate('index')" data-i18n="btn.back">◄ Index</button>

      <div class="fm-hero">
        <img class="fm-hero-img" src="{BG_TILE_SRC}" alt="Briefing Generator" draggable="false">
        <div class="fm-hero-pin" aria-hidden="true"></div>
        <div class="fm-hero-caption">
          <div><div class="fm-hero-monogram">BG</div></div>
          <div>
            <div class="fm-hero-title" data-i18n="bg.hero.title">Briefing Generator</div>
            <div class="fm-hero-sub" data-i18n="bg.hero.sub">Générateur de briefings multi-sections</div>
          </div>
        </div>
      </div>

      <!-- À quoi ça sert -->
      <div class="fm-prose">
        <h3 class="lang-block" data-lang="fr">À quoi ça sert</h3>
        <h3 class="lang-block" data-lang="en">What it’s for</h3>
        <div class="lang-block" data-lang="fr"><p>Le Briefing Generator prépare le briefing d’une mission, prêt à imprimer ou à emporter en vol, dans l’un de <strong>deux formats</strong>. Le <strong>brief Standard</strong> tient sur <strong>une page</strong> — situation, mission et tableau des groupes, fréquences, terrains, météo —, suivie s’il y a lieu d’une page « carte, menaces, cibles » et de pages de photos. Le <strong>brief Avancé</strong> est un dossier <strong>multi-pages</strong> : couverture, situation tactique, aperçu de mission, plan radio, missions individuelles, équipage, cartes et annexes. On remplit des sections dans l’éditeur, on vérifie la mise en page A4 dans l’aperçu, puis on exporte en <strong>PDF</strong> ou en <strong>PNG par page</strong> (genouillères). L’identité d’escadre (logo, noms, escadrons) est <strong>héritée de HQ</strong>. Quatre thèmes, tout hors-ligne.</p></div>
        <div class="lang-block" data-lang="en"><p>The Briefing Generator prepares a mission briefing, ready to print or take into the cockpit, in one of <strong>two formats</strong>. The <strong>Standard brief</strong> fits on <strong>one page</strong> — situation, mission and groups table, frequencies, airfields, weather —, followed when needed by a “map, threats, targets” page and by photo pages. The <strong>Advanced brief</strong> is a <strong>multi-page</strong> file: cover, tactical situation, mission overview, radio plan, individual missions, crew, charts, and annexes. You fill sections in the editor, check the A4 layout in the preview, then export to <strong>PDF</strong> or <strong>per-page PNG</strong> (kneeboards). The wing identity (logo, names, squadrons) is <strong>inherited from HQ</strong>. Four themes, fully offline.</p></div>
      </div>

      <!-- Deux formats -->
      <div class="fm-prose">
        <h3 class="lang-block" data-lang="fr">Deux formats : Standard ou Avancé</h3>
        <h3 class="lang-block" data-lang="en">Two formats: Standard or Advanced</h3>
        <div class="lang-block" data-lang="fr"><p>Le menu <strong>Affichage ▾</strong> de la barre du haut choisit le format : <strong>Standard</strong> — une page de mission et des pages de photos — ou <strong>Avancé</strong> — dix sections. Un point ambré sur le bouton signale <strong>Avancé</strong>. Le document imprimé ne nomme pas son format. Changer de format <strong>ne perd rien</strong> : seules les sections affichées et les pages produites changent ; ce que vous avez saisi pour l’autre format reste dans le briefing et réapparaît quand vous y revenez. Un briefing sauvegardé avant l’arrivée des deux formats s’ouvre en <strong>Avancé</strong>.</p></div>
        <div class="lang-block" data-lang="en"><p>The <strong>Display ▾</strong> menu in the top bar picks the format: <strong>Standard</strong> — one mission page plus photo pages — or <strong>Advanced</strong> — ten sections. An amber dot on the button flags <strong>Advanced</strong>. The printed document does not name its format. Switching <strong>loses nothing</strong>: only the sections shown and the pages produced change; what you entered for the other format stays in the briefing and comes back when you switch again. A briefing saved before the two formats existed opens as <strong>Advanced</strong>.</p></div>
      </div>

      <!-- Démarrer -->
      <div class="fm-prose">
        <h3 class="lang-block" data-lang="fr">Démarrer : page blanche ou exemple</h3>
        <h3 class="lang-block" data-lang="en">Getting started: blank page or example</h3>
        <div class="lang-block" data-lang="fr"><p>L’outil s’ouvre sur un <strong>briefing vide</strong>, en <strong>Standard</strong>. Le bouton <strong>Exemple</strong> ouvre un briefing de démonstration, lui aussi en Standard (passez en Avancé pour voir toutes les sections), pour voir ce que l’outil sait faire ; il remplace le briefing en cours, après confirmation. Il s’ouvre dans la langue de l’interface au moment du clic : changer de langue ensuite ne le retraduit pas. <strong>Effacer</strong> vide tout le briefing, après confirmation, pour repartir d’une page blanche. Les champs vides disent en grisé <strong>ce qu’on y met</strong> (« Nom de l’opération », « hh:mm »…) ; cet indice n’apparaît ni dans l’aperçu ni à l’export.</p></div>
        <div class="lang-block" data-lang="en"><p>The tool opens on an <strong>empty briefing</strong>, in <strong>Standard</strong>. The <strong>Example</strong> button opens a demonstration briefing, also in Standard (switch to Advanced to see every section), to show what the tool can do; it replaces the current briefing, after confirmation. It opens in the interface language at the moment of the click: switching language afterwards does not translate it again. <strong>Clear</strong> clears the whole briefing, after confirmation, to start from a blank page. Empty fields show in grey <strong>what to type there</strong> (“Operation name”, “hh:mm”…); that hint never appears in the preview or the export.</p></div>
      </div>

      <!-- Schéma SVG -->
      <div class="fm-schema tall">
        {BG_SVG}
        <div class="fm-schema-legend">
          <span class="lang-block" data-lang="fr">{BG_LEGEND_FR}</span>
          <span class="lang-block" data-lang="en">{BG_LEGEND_EN}</span>
        </div>
      </div>

      <!-- Le brief Standard -->
      <div class="fm-prose">
        <h3 class="lang-block" data-lang="fr">Le brief Standard</h3>
        <h3 class="lang-block" data-lang="en">The Standard brief</h3>
        <div class="lang-block" data-lang="fr"><p>Cinq sections. <strong>Méta</strong> : opération, mission, date, <strong>Heure (Z)</strong>, classification, référence. <strong>Situation</strong> : la situation, en points, la <strong>carte</strong> et les <strong>menaces</strong> (chars, APC, AAA, SAM, et une note). <strong>Mission</strong> : les objectifs, puis les <strong>groupes</strong> — pour chacun l’escadron (ou un escadron invité), l’appareil et le sous-groupe, la <strong>Tâche</strong>, le <strong>Nombre</strong> d’appareils et le <strong>Départ</strong> —, puis les <strong>cibles</strong> — pour chacune un numéro, la nature, la position et une remarque. <strong>Coordination</strong> : les fréquences, les terrains et le METAR, avec son assistant. <strong>Photos</strong> : pour chaque photo, un titre, l’image et une légende. La carte et les menaces sont celles du brief Avancé, et les cibles sont partagées par les deux formats : ce qui est saisi d’un côté se retrouve de l’autre.</p></div>
        <div class="lang-block" data-lang="en"><p>Five sections. <strong>Meta</strong>: operation, mission, date, <strong>Time (Z)</strong>, classification, reference. <strong>Situation</strong>: the situation, as bullet points, the <strong>map</strong>, and the <strong>threats</strong> (tanks, APC, AAA, SAM, and a note). <strong>Mission</strong>: the objectives, then the <strong>groups</strong> — for each, the squadron (or a guest squadron), the aircraft and subgroup, the <strong>Task</strong>, the aircraft <strong>Count</strong>, and the <strong>Departure</strong> —, then the <strong>targets</strong> — for each, a number, its type, its position, and a remark. <strong>Coordination</strong>: frequencies, airfields, and the METAR, with its assistant. <strong>Photos</strong>: for each photo, a title, the image, and a caption. The map and the threats are those of the Advanced brief, and the targets are shared by both formats: what you enter on one side shows up on the other.</p></div>
      </div>

      <!-- La page Standard -->
      <div class="fm-prose">
        <h3 class="lang-block" data-lang="fr">La page Standard</h3>
        <h3 class="lang-block" data-lang="en">The Standard page</h3>
        <div class="lang-block" data-lang="fr"><p>Le brief Standard produit <strong>une page de mission</strong> : un bandeau « MISSION » suivi du code de mission, de la date et de l’heure, la <strong>Situation</strong>, la <strong>Mission</strong> avec le <strong>tableau des groupes</strong> (Groupe, Appareil, Tâche, Départ — « 2× F-16C » quand le nombre est renseigné), les <strong>Fréquences</strong> et les <strong>Terrains</strong> côte à côte, puis la <strong>Météo</strong>. Vient ensuite, si une carte est chargée ou si des menaces ou des cibles sont saisies, une page <strong>« CARTE ░ MENACES ░ CIBLES »</strong> : la carte, les menaces — une ligne par catégorie renseignée — et le <strong>tableau des cibles</strong> (N°, Nature, Position, Remarque) ; son bandeau ne nomme que ce qu’elle porte. Un bloc vide ne s’affiche pas, et une page qui déborde se poursuit sur la page suivante : « SUITE » pour la mission, le nom de ce qu’elle porte pour la page carte, menaces, cibles. Suivent, s’il y a des photos, des <strong>pages de photos</strong>, deux par page, sous le bandeau « PHOTOS ░ RECONNAISSANCE ». La carte peut venir du Route Planner : son menu <strong>Exporter ▾ › Image pour le briefing…</strong> l’y envoie, cadrée, avec son échelle et son nord.</p></div>
        <div class="lang-block" data-lang="en"><p>The Standard brief produces <strong>one mission page</strong>: a “MISSION” banner followed by the mission code, date, and time, the <strong>Situation</strong>, the <strong>Mission</strong> with the <strong>groups table</strong> (Group, Aircraft, Task, Departure — “2× F-16C” when the count is filled in), <strong>Frequencies</strong> and <strong>Airfields</strong> side by side, then the <strong>Weather</strong>. Next comes, if a map is loaded or threats or targets are entered, a <strong>“MAP ░ THREATS ░ TARGETS”</strong> page: the map, the threats — one line per category filled in — and the <strong>targets table</strong> (No., Type, Position, Remarks); its banner names only what it holds. An empty block is not shown, and a page that overflows continues on the next page: “CONT.” for the mission, the name of what it holds for the map, threats, targets page. If there are photos, <strong>photo pages</strong> follow, two per page, under the “PHOTOS ░ RECONNAISSANCE” banner. The map can come from the Route Planner: its <strong>Export ▾ › Image for the briefing…</strong> menu sends it there, framed, with its scale and north arrow.</p></div>
      </div>

      <!-- Le brief Avancé, section par section -->
      <div class="fm-prose">
        <h3 class="lang-block" data-lang="fr">Le brief Avancé, section par section</h3>
        <h3 class="lang-block" data-lang="en">The Advanced brief, section by section</h3>
        <div class="lang-block" data-lang="fr"><p>Le brief Avancé garde toutes ses sections, décrites ci-dessous ; elles n’apparaissent qu’en Avancé.</p></div>
        <div class="lang-block" data-lang="en"><p>The Advanced brief keeps all its sections, described below; they only appear in Advanced.</p></div>
      </div>

      <!-- Métadonnées & couverture -->
      <div class="fm-prose">
        <h3 class="lang-block" data-lang="fr">Le squelette : métadonnées &amp; couverture</h3>
        <h3 class="lang-block" data-lang="en">The skeleton: metadata &amp; cover</h3>
        <div class="lang-block" data-lang="fr"><p>Les <strong>Métadonnées</strong> (opération, mission, date, classification, référence du document) alimentent l’en-tête et le pied de toutes les pages. La <strong>Couverture</strong> porte le titre, un narratif d’introduction et une carte du théâtre.</p></div>
        <div class="lang-block" data-lang="en"><p><strong>Metadata</strong> (operation, mission, date, classification, document reference) feed the header and footer of every page. The <strong>Cover</strong> carries the title, an intro narrative, and a theatre map.</p></div>
      </div>

      <!-- SITAC -->
      <div class="fm-prose">
        <h3 class="lang-block" data-lang="fr">Situation tactique (SITAC)</h3>
        <h3 class="lang-block" data-lang="en">Tactical situation (SITAC)</h3>
        <div class="lang-block" data-lang="fr"><p>Décrivez la situation par points, ajoutez une carte tactique, et renseignez le <strong>METAR</strong>. L’<strong>Assistant METAR</strong> vous évite la saisie à la main : soit un formulaire guidé (vent, visibilité, nuages, QNH, température…), soit l’<strong>import d’un .miz</strong> dont il extrait automatiquement la météo de la mission. Le champ METAR reste éditable librement.</p></div>
        <div class="lang-block" data-lang="en"><p>Describe the situation as bullet points, add a tactical map, and fill in the <strong>METAR</strong>. The <strong>METAR Assistant</strong> spares you manual entry: either a guided form (wind, visibility, clouds, QNH, temperature…), or <strong>importing a .miz</strong> from which it extracts the mission weather automatically. The METAR field stays freely editable.</p></div>
      </div>

      <!-- Aperçu mission -->
      <div class="fm-prose">
        <h3 class="lang-block" data-lang="fr">Aperçu de mission</h3>
        <h3 class="lang-block" data-lang="en">Mission overview</h3>
        <div class="lang-block" data-lang="fr"><p>Objectifs, <strong>cibles</strong>, menaces, et une liste structurée d’<strong>aérodromes &amp; FARP</strong> : pour chacun, code <strong>ICAO</strong>, bascule <strong>FARP</strong>, nom, piste en service ou cap, et case <strong>ATC</strong>. Chaque entrée se range proprement dans l’aperçu. Les cibles — numéro, nature, position, remarque — forment un tableau sous les objectifs, s’il y en a ; les menaces tiennent sur une ligne par catégorie.</p></div>
        <div class="lang-block" data-lang="en"><p>Objectives, <strong>targets</strong>, threats, and a structured list of <strong>airfields &amp; FARPs</strong>: for each, <strong>ICAO</strong> code, <strong>FARP</strong> toggle, name, active runway or heading, and an <strong>ATC</strong> box. Each entry lays out cleanly in the preview. The targets — number, type, position, remark — form a table under the objectives, if there are any; the threats take one line per category.</p></div>
      </div>

      <!-- Plan radio -->
      <div class="fm-prose">
        <h3 class="lang-block" data-lang="fr">Plan radio</h3>
        <h3 class="lang-block" data-lang="en">Radio plan</h3>
        <div class="lang-block" data-lang="fr"><p>Un plan <strong>global</strong> (nombre d’entrées illimité ; jusqu’à six retenues à l’aperçu) plus des plans <strong>par appareil</strong>, avec une référence radio propre à chaque type. De quoi cadrer fréquences et canaux pour toute la formation.</p></div>
        <div class="lang-block" data-lang="en"><p>A <strong>global</strong> plan (unlimited entries; up to six shown in the preview) plus <strong>per-aircraft</strong> plans, with a radio reference specific to each type. Everything you need to set frequencies and channels for the whole formation.</p></div>
      </div>

      <!-- Missions individuelles -->
      <div class="fm-prose">
        <h3 class="lang-block" data-lang="fr">Missions individuelles</h3>
        <h3 class="lang-block" data-lang="en">Individual missions</h3>
        <div class="lang-block" data-lang="fr"><p>Autant de missions que nécessaire, parcourues par les flèches (ajouter, dupliquer, réordonner, supprimer). Chacune : titre, escadron, appareil et sous-groupe, objectif, <strong>étapes d’exécution</strong> ordonnables (avec sous-tâches), plan de vol, niveau de menace, notes et images.</p></div>
        <div class="lang-block" data-lang="en"><p>As many missions as needed, browsed with arrows (add, duplicate, reorder, delete). Each one: title, squadron, aircraft and subgroup, objective, orderable <strong>execution steps</strong> (with sub-tasks), flight plan, threat level, notes, and images.</p></div>
      </div>

      <!-- Équipage -->
      <div class="fm-prose">
        <h3 class="lang-block" data-lang="fr">Équipage</h3>
        <h3 class="lang-block" data-lang="en">Crew</h3>
        <div class="lang-block" data-lang="fr"><p>Constituez les groupes de pilotes rattachés aux missions. Les indicatifs sont proposés automatiquement à partir du callsign de l’escadron (ex. « ANTON 1-1 ») et restent modifiables.</p></div>
        <div class="lang-block" data-lang="en"><p>Build the pilot groups attached to the missions. Call signs are suggested automatically from the squadron callsign (e.g. “ANTON 1-1”) and stay editable.</p></div>
      </div>

      <!-- Charts & Annexes -->
      <div class="fm-prose">
        <h3 class="lang-block" data-lang="fr">Charts &amp; annexes</h3>
        <h3 class="lang-block" data-lang="en">Charts &amp; annexes</h3>
        <div class="lang-block" data-lang="fr"><p><strong>Charts</strong> : une liste illimitée de cartes d’aéroport (image + titre). <strong>Annexes</strong> : des pages libres illimitées pour tout ce qui ne rentre pas ailleurs. Les images trop lourdes sont recompressées automatiquement.</p></div>
        <div class="lang-block" data-lang="en"><p><strong>Charts</strong>: an unlimited list of airfield charts (image + title). <strong>Annexes</strong>: unlimited free pages for anything that doesn’t fit elsewhere. Oversized images are recompressed automatically.</p></div>
      </div>

      <!-- Identité d’escadre HQ — CALLOUT -->
      <div class="fm-callout note">
        <div class="lang-block" data-lang="fr">L’escadre se gère dans HQ — la création et la modification de l’escadre (logo, noms, escadrons) se font désormais dans le module HQ. Ici, l’onglet Wing n’affiche plus que le branding hérité, en lecture seule, et se met à jour automatiquement quand HQ change. (En usage autonome, l’import manuel d’une config <code>.json</code> reste un dépannage possible.)</div>
        <div class="lang-block" data-lang="en">The wing lives in HQ — creating and editing the wing (logo, names, squadrons) now happens in the HQ module. Here, the Wing tab only shows the inherited branding, read-only, and updates automatically when HQ changes. (In standalone use, importing a <code>.json</code> config remains a possible fallback.)</div>
      </div>

      <!-- Sauvegarder & reprendre -->
      <div class="fm-prose">
        <h3 class="lang-block" data-lang="fr">Sauvegarder &amp; reprendre</h3>
        <h3 class="lang-block" data-lang="en">Save &amp; resume</h3>
        <div class="lang-block" data-lang="fr"><p>Le briefing est <strong>sauvegardé automatiquement</strong> dans le navigateur. <strong>Sauvegarder</strong> l’écrit en fichier <code>.json</code> pour l’archiver, le partager ou le reprendre sur une autre machine ; <strong>Ouvrir</strong> le relit. Le format choisi voyage avec le fichier. <kbd>Ctrl</kbd>+<kbd>S</kbd> (<kbd>Cmd</kbd>+<kbd>S</kbd> sur Mac) fait le même geste que <strong>Sauvegarder</strong>.</p></div>
        <div class="lang-block" data-lang="en"><p>The briefing is <strong>saved automatically</strong> in the browser. <strong>Save</strong> writes it to a <code>.json</code> file to archive, share, or resume it on another machine; <strong>Open</strong> reads it back. The chosen format travels with the file. <kbd>Ctrl</kbd>+<kbd>S</kbd> (<kbd>Cmd</kbd>+<kbd>S</kbd> on a Mac) does the same as <strong>Save</strong>.</p></div>
      </div>

      <!-- Exporter -->
      <div class="fm-prose">
        <h3 class="lang-block" data-lang="fr">Exporter le briefing</h3>
        <h3 class="lang-block" data-lang="en">Exporting the briefing</h3>
        <div class="lang-block" data-lang="fr"><p>Vérifiez la mise en page dans l’<strong>Aperçu</strong>, puis <strong>Exporter</strong> : l’export porte les pages du format en cours. Le <strong>PDF</strong> passe par l’impression du navigateur (<kbd>Ctrl</kbd>+<kbd>P</kbd> → « Enregistrer en PDF »), y compris sur Android. L’<strong>export PNG</strong> produit une image par page, idéale en genouillère.</p></div>
        <div class="lang-block" data-lang="en"><p>Check the layout in the <strong>Preview</strong>, then <strong>Export</strong>: the export carries the pages of the current format. The <strong>PDF</strong> goes through the browser’s print (<kbd>Ctrl</kbd>+<kbd>P</kbd> → “Save as PDF”), including on Android. The <strong>PNG export</strong> produces one image per page, ideal as a kneeboard.</p></div>
      </div>

      <!-- La barre du haut sur tablette et téléphone -->
      <div class="fm-prose">
        <h3 class="lang-block" data-lang="fr">La barre du haut sur tablette et téléphone</h3>
        <h3 class="lang-block" data-lang="en">The top bar on tablets and phones</h3>
        <div class="lang-block" data-lang="fr"><p>Quand la barre du haut ne tient pas dans la largeur, elle <strong>défile</strong> au doigt, à la molette ou au pavé tactile ; un <strong>fondu</strong> sur un bord signale qu’il reste des boutons de ce côté. Toucher un bouton à moitié visible le ramène en entier avant de l’activer. Jusqu’à 1 100 px de large, l’éditeur passe en <strong>onglets</strong> : un par section, plus <strong>Aperçu</strong>.</p></div>
        <div class="lang-block" data-lang="en"><p>When the top bar doesn’t fit the width, it <strong>scrolls</strong> by finger, mouse wheel, or touchpad; a <strong>fade</strong> on one edge shows there are more buttons that way. Tapping a half-visible button brings it fully into view before activating it. Up to 1,100 px wide, the editor switches to <strong>tabs</strong>: one per section, plus <strong>Preview</strong>.</p></div>
      </div>

      <!-- Et la datacard ? -->
      <div class="fm-callout note">
        <div class="lang-block" data-lang="fr">Et la datacard ? — Le Briefing Generator ne connaît pas la datacard : c’est le <strong>Datacard Generator</strong> qui lit le briefing, en cours ou en fichier, et en tire une datacard par groupe. <a href="#dg">Voir son chapitre</a>.</div>
        <div class="lang-block" data-lang="en">What about the datacard? — The Briefing Generator knows nothing of the datacard: the <strong>Datacard Generator</strong> reads the briefing, current or from a file, and turns each group into a datacard. <a href="#dg">See its chapter</a>.</div>
      </div>

    </div><!-- /fm-chapter -->
  </section><!-- /page-bg -->

  <!-- ===== PAGE DG ===== -->
  <section id="page-dg" class="fm-page hidden">
    <div class="fm-chapter" style="--chapter-accent:#4f7a8e; --chapter-accent-rgb:79,122,142;">

      <button class="fm-back-btn" onclick="navigate('index')" data-i18n="btn.back">◄ Index</button>

      <div class="fm-hero">
        <img class="fm-hero-img" src="{DG_TILE_SRC}" alt="Datacard Generator" draggable="false">
        <div class="fm-hero-pin" aria-hidden="true"></div>
        <div class="fm-hero-caption">
          <div><div class="fm-hero-monogram">DG</div></div>
          <div>
            <div class="fm-hero-title" data-i18n="dg.hero.title">Datacard Generator</div>
            <div class="fm-hero-sub" data-i18n="dg.hero.sub">Datacards de vol pour le kneeboard</div>
          </div>
        </div>
      </div>

      <!-- À quoi ça sert -->
      <div class="fm-prose">
        <h3 class="lang-block" data-lang="fr">À quoi ça sert</h3>
        <h3 class="lang-block" data-lang="en">What it’s for</h3>
        <div class="lang-block" data-lang="fr"><p>Le Datacard Generator produit la <strong>datacard d’un groupe</strong> : une fiche d’une page, au format d’une page de kneeboard, qui réunit ce dont l’équipage a besoin en l’air — indicatif et tâche, horaires, équipages, navigation, radio, terrains, météo, carburant, emport, menaces. On la remplit <strong>à la main</strong> ou <strong>depuis le Briefing Generator</strong> ; on en tient un <strong>paquet</strong>, une par groupe de la mission ; on l’exporte en <strong>PNG</strong> pour le kneeboard de DCS ou en <strong>PDF</strong> pour l’imprimer, en version <strong>jour</strong> ou <strong>nuit</strong>.</p></div>
        <div class="lang-block" data-lang="en"><p>The Datacard Generator produces a <strong>group’s datacard</strong>: a one-page sheet, the size of a kneeboard page, that gathers what the crew needs in the air — callsign and task, times, crew, navigation, radio, airfields, weather, fuel, loadout, threats. You fill it <strong>by hand</strong> or <strong>from the Briefing Generator</strong>; you keep a <strong>deck</strong> of them, one per group in the mission; you export to <strong>PNG</strong> for the DCS kneeboard or to <strong>PDF</strong> for printing, in a <strong>day</strong> or <strong>night</strong> version.</p></div>
      </div>

      <!-- Schéma SVG : anatomie d’une datacard -->
      <div class="fm-schema">
        <svg viewBox="0 0 720 380" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Anatomie d’une datacard" data-aria-fr="Anatomie d’une datacard" data-aria-en="Anatomy of a datacard">
          <defs>
            <marker id="dgl" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto"><path d="M0,0 L7,3.5 L0,7 Z" fill="currentColor" opacity=".55"/></marker>
          </defs>
          <text x="360" y="26" text-anchor="middle" font-size="13" letter-spacing="3" fill="currentColor" opacity=".9" class="lang-block" data-lang="fr">ANATOMIE D’UNE DATACARD</text>
          <text x="360" y="26" text-anchor="middle" font-size="13" letter-spacing="3" fill="currentColor" opacity=".9" class="lang-block" data-lang="en">ANATOMY OF A DATACARD</text>
          <line x1="120" y1="34" x2="600" y2="34" stroke="currentColor" stroke-width=".6" opacity=".3"/>

          <!-- La page, ses bandeaux et son en-tête -->
          <rect class="sv-box" x="270" y="50" width="180" height="255"/>
          <rect x="270" y="50" width="180" height="8" fill="currentColor" opacity=".85"/>
          <rect x="270" y="297" width="180" height="8" fill="currentColor" opacity=".85"/>
          <text x="276" y="80" font-size="17" fill="currentColor">CAESAR</text>
          <line x1="276" y1="88" x2="350" y2="88" stroke="currentColor" stroke-width="1.4" opacity=".7"/>
          <text x="444" y="70" text-anchor="end" font-size="9" letter-spacing="1" fill="currentColor">DATACARD</text>
          <line x1="392" y1="77" x2="444" y2="77" stroke="currentColor" stroke-width="1" opacity=".6"/>
          <rect x="414" y="83" width="30" height="7" fill="#a83524" opacity=".85"/>

          <!-- Les blocs -->
          <rect x="274" y="96" width="106" height="44" class="sv-box" stroke="currentColor" stroke-width="1.1"/>
          <rect x="274" y="96" width="106" height="6" fill="currentColor" opacity=".75"/>
          <text x="327" y="123.5" text-anchor="middle" font-size="8" fill="currentColor" opacity=".9" class="lang-block" data-lang="fr">MISSION</text>
          <text x="327" y="123.5" text-anchor="middle" font-size="8" fill="currentColor" opacity=".9" class="lang-block" data-lang="en">MISSION</text>
          <rect x="384" y="96" width="62" height="44" class="sv-box" stroke="currentColor" stroke-width="1.1"/>
          <rect x="384" y="96" width="62" height="6" fill="currentColor" opacity=".75"/>
          <text x="415" y="123.5" text-anchor="middle" font-size="8" fill="currentColor" opacity=".9" class="lang-block" data-lang="fr">HORAIRES</text>
          <text x="415" y="123.5" text-anchor="middle" font-size="8" fill="currentColor" opacity=".9" class="lang-block" data-lang="en">TIMES</text>
          <rect x="274" y="144" width="172" height="24" class="sv-box" stroke="currentColor" stroke-width="1.1"/>
          <rect x="274" y="144" width="172" height="6" fill="currentColor" opacity=".75"/>
          <text x="360" y="161.5" text-anchor="middle" font-size="8" fill="currentColor" opacity=".9" class="lang-block" data-lang="fr">ÉQUIPAGES</text>
          <text x="360" y="161.5" text-anchor="middle" font-size="8" fill="currentColor" opacity=".9" class="lang-block" data-lang="en">CREW</text>
          <rect x="274" y="172" width="172" height="44" class="sv-box" stroke="currentColor" stroke-width="1.1" stroke-dasharray="4 3"/>
          <rect x="274" y="172" width="172" height="6" fill="currentColor" opacity=".75"/>
          <text x="360" y="199.5" text-anchor="middle" font-size="8" fill="currentColor" opacity=".9" class="lang-block" data-lang="fr">NAVIGATION</text>
          <text x="360" y="199.5" text-anchor="middle" font-size="8" fill="currentColor" opacity=".9" class="lang-block" data-lang="en">NAVIGATION</text>
          <rect x="274" y="220" width="90" height="50" class="sv-box" stroke="currentColor" stroke-width="1.1"/>
          <rect x="274" y="220" width="90" height="6" fill="currentColor" opacity=".75"/>
          <text x="319" y="250.5" text-anchor="middle" font-size="8" fill="currentColor" opacity=".9" class="lang-block" data-lang="fr">RADIO</text>
          <text x="319" y="250.5" text-anchor="middle" font-size="8" fill="currentColor" opacity=".9" class="lang-block" data-lang="en">RADIO</text>
          <rect x="368" y="220" width="78" height="23" class="sv-box" stroke="currentColor" stroke-width="1.1"/>
          <rect x="368" y="220" width="78" height="6" fill="currentColor" opacity=".75"/>
          <text x="407" y="237" text-anchor="middle" font-size="8" fill="currentColor" opacity=".9" class="lang-block" data-lang="fr">TERRAINS</text>
          <text x="407" y="237" text-anchor="middle" font-size="8" fill="currentColor" opacity=".9" class="lang-block" data-lang="en">AIRFIELDS</text>
          <rect x="368" y="247" width="78" height="23" class="sv-box" stroke="currentColor" stroke-width="1.1"/>
          <rect x="368" y="247" width="78" height="6" fill="currentColor" opacity=".75"/>
          <text x="407" y="264" text-anchor="middle" font-size="8" fill="currentColor" opacity=".9" class="lang-block" data-lang="fr">MÉTÉO</text>
          <text x="407" y="264" text-anchor="middle" font-size="8" fill="currentColor" opacity=".9" class="lang-block" data-lang="en">WEATHER</text>
          <rect x="274" y="274" width="84" height="19" class="sv-box" stroke="currentColor" stroke-width="1.1"/>
          <rect x="274" y="274" width="84" height="6" fill="currentColor" opacity=".75"/>
          <text x="316" y="289" text-anchor="middle" font-size="8" fill="currentColor" opacity=".9" class="lang-block" data-lang="fr">CARBURANT · EMPORT</text>
          <text x="316" y="289" text-anchor="middle" font-size="8" fill="currentColor" opacity=".9" class="lang-block" data-lang="en">FUEL · LOADOUT</text>
          <rect x="362" y="274" width="84" height="19" class="sv-box" stroke="currentColor" stroke-width="1.1"/>
          <rect x="362" y="274" width="84" height="6" fill="currentColor" opacity=".75"/>
          <text x="404" y="289" text-anchor="middle" font-size="8" fill="currentColor" opacity=".9" class="lang-block" data-lang="fr">MENACES · NOTES</text>
          <text x="404" y="289" text-anchor="middle" font-size="8" fill="currentColor" opacity=".9" class="lang-block" data-lang="en">THREATS · NOTES</text>
          <path d="M270,50 h180 v255 h-180 z" fill="none" stroke="#4f7a8e" stroke-width="2"/>

          <!-- Libellés à gauche -->
          <line x1="232" y1="54" x2="270" y2="54" stroke="currentColor" stroke-width="1" opacity=".55" marker-end="url(#dgl)"/>
          <line x1="232" y1="84" x2="270" y2="84" stroke="currentColor" stroke-width="1" opacity=".55" marker-end="url(#dgl)"/>
          <line x1="232" y1="118" x2="270" y2="118" stroke="currentColor" stroke-width="1" opacity=".55" marker-end="url(#dgl)"/>
          <line x1="232" y1="156" x2="270" y2="156" stroke="currentColor" stroke-width="1" opacity=".55" marker-end="url(#dgl)"/>
          <line x1="232" y1="245" x2="270" y2="245" stroke="currentColor" stroke-width="1" opacity=".55" marker-end="url(#dgl)"/>
          <line x1="232" y1="284" x2="270" y2="284" stroke="currentColor" stroke-width="1" opacity=".55" marker-end="url(#dgl)"/>
          <g font-size="11" fill="currentColor" text-anchor="end">
            <text x="226" y="58" class="lang-block" data-lang="fr">Classification · référence · page</text>
            <text x="226" y="58" class="lang-block" data-lang="en">Classification · reference · page</text>
            <text x="226" y="88" class="lang-block" data-lang="fr">Indicatif · appareil · tâche</text>
            <text x="226" y="88" class="lang-block" data-lang="en">Callsign · aircraft · task</text>
            <text x="226" y="122" class="lang-block" data-lang="fr">Objectif et étapes</text>
            <text x="226" y="122" class="lang-block" data-lang="en">Objective and steps</text>
            <text x="226" y="160" class="lang-block" data-lang="fr">Indicatif · pilote · appareil · n°</text>
            <text x="226" y="160" class="lang-block" data-lang="en">Callsign · pilot · aircraft · no.</text>
            <text x="226" y="249" class="lang-block" data-lang="fr">Postes et canaux</text>
            <text x="226" y="249" class="lang-block" data-lang="en">Radios and channels</text>
            <text x="226" y="288" class="lang-block" data-lang="fr">Joker · bingo · emport</text>
            <text x="226" y="288" class="lang-block" data-lang="en">Joker · bingo · loadout</text>
          </g>

          <!-- Libellés à droite -->
          <line x1="488" y1="72" x2="450" y2="72" stroke="currentColor" stroke-width="1" opacity=".55" marker-end="url(#dgl)"/>
          <line x1="488" y1="118" x2="450" y2="118" stroke="currentColor" stroke-width="1" opacity=".55" marker-end="url(#dgl)"/>
          <line x1="488" y1="194" x2="450" y2="194" stroke="currentColor" stroke-width="1" opacity=".55" marker-end="url(#dgl)"/>
          <line x1="488" y1="231" x2="450" y2="231" stroke="currentColor" stroke-width="1" opacity=".55" marker-end="url(#dgl)"/>
          <line x1="488" y1="258" x2="450" y2="258" stroke="currentColor" stroke-width="1" opacity=".55" marker-end="url(#dgl)"/>
          <line x1="488" y1="284" x2="450" y2="284" stroke="currentColor" stroke-width="1" opacity=".55" marker-end="url(#dgl)"/>
          <g font-size="11" fill="currentColor" text-anchor="start">
            <text x="494" y="76" class="lang-block" data-lang="fr">Opération · date · menace</text>
            <text x="494" y="76" class="lang-block" data-lang="en">Operation · date · threat</text>
            <text x="494" y="122" class="lang-block" data-lang="fr">Mise en route → RTB</text>
            <text x="494" y="122" class="lang-block" data-lang="en">Start-up → RTB</text>
            <text x="494" class="lang-block" data-lang="fr"><tspan x="494" y="191">Points, caps, distances</tspan> <tspan x="494" y="205">→ page 2 si elle déborde</tspan></text>
            <text x="494" class="lang-block" data-lang="en"><tspan x="494" y="191">Points, headings, distances</tspan> <tspan x="494" y="205">→ page 2 if it overflows</tspan></text>
            <text x="494" y="235" class="lang-block" data-lang="fr">DEP · ARR · ALT</text>
            <text x="494" y="235" class="lang-block" data-lang="en">DEP · ARR · ALT</text>
            <text x="494" y="262" class="lang-block" data-lang="fr">METAR décodé</text>
            <text x="494" y="262" class="lang-block" data-lang="en">Decoded METAR</text>
            <text x="494" y="288" class="lang-block" data-lang="fr">Menaces · notes</text>
            <text x="494" y="288" class="lang-block" data-lang="en">Threats · notes</text>
          </g>

          <!-- Libellé du pied -->
          <line x1="360" y1="336" x2="360" y2="307" stroke="currentColor" stroke-width="1" opacity=".55" marker-end="url(#dgl)"/>
          <text x="360" y="350" text-anchor="middle" font-size="11" fill="currentColor" class="lang-block" data-lang="fr">Pied : indicatif · opération · classification · page</text>
          <text x="360" y="350" text-anchor="middle" font-size="11" fill="currentColor" class="lang-block" data-lang="en">Footer: callsign · operation · classification · page</text>
        </svg>
        <div class="fm-schema-legend">
          <span class="lang-block" data-lang="fr">Fig. 1 — L’anatomie d’une datacard : où se range chaque bloc.</span>
          <span class="lang-block" data-lang="en">Fig. 1 — Anatomy of a datacard: where each block goes.</span>
        </div>
      </div>

      <!-- Le paquet de datacards -->
      <div class="fm-prose">
        <h3 class="lang-block" data-lang="fr">Le paquet de datacards</h3>
        <h3 class="lang-block" data-lang="en">The datacard deck</h3>
        <div class="lang-block" data-lang="fr"><p>Le document est un <strong>paquet</strong> de datacards, une par groupe. En tête du panneau, une ligne choisit la carte : « CAESAR ▾ », avec sa pastille <strong>LIÉE</strong>, <strong>LIBRE</strong> ou <strong>GROUPE SUPPRIMÉ</strong>, ouvre la liste, qui range les cartes sous <strong>Liées aux groupes du FC</strong> et <strong>Libres</strong> ; deux cartes de même nom s’y lisent « CAESAR » et « CAESAR · 2 ». <strong>+</strong> ajoute une datacard liée à un groupe ; <strong>…</strong> ouvre <strong>Carte libre</strong>, <strong>Rattacher à un groupe</strong>, <strong>Importer des groupes</strong>, <strong>Une datacard par route</strong>, <strong>Dupliquer</strong> et <strong>Supprimer</strong> ; dessous, « résumé de la carte — 2 / 3 » donne le rang de la carte choisie et le total. L’aperçu montre la carte courante. La dernière carte ne se supprime pas : elle se vide.</p></div>
        <div class="lang-block" data-lang="en"><p>The document is a <strong>deck</strong> of datacards, one per group. At the top of the panel, one line picks the card: “CAESAR ▾”, with its tag <strong>LINKED</strong>, <strong>FREE</strong> or <strong>GROUP DELETED</strong>, opens the list, which sorts the cards under <strong>Linked to FC groups</strong> and <strong>Free</strong>; two cards of the same name read “CAESAR” and “CAESAR · 2” there. <strong>+</strong> adds a datacard linked to a group; <strong>…</strong> opens <strong>Free card</strong>, <strong>Attach to a group</strong>, <strong>Import groups</strong>, <strong>One datacard per route</strong>, <strong>Duplicate</strong> and <strong>Delete</strong>; below, “card summary — 2 / 3” gives the rank of the chosen card and the total. The preview shows the current card. The last card can’t be deleted: it is cleared instead.</p></div>
      </div>

      <!-- Remplir une datacard -->
      <div class="fm-prose">
        <h3 class="lang-block" data-lang="fr">Remplir une datacard</h3>
        <h3 class="lang-block" data-lang="en">Filling in a datacard</h3>
        <div class="lang-block" data-lang="fr"><p>Onze sections, dans l’ordre de la fiche : <strong>Méta</strong> (classification, référence, opération, mission, date, heure, unités de mesure) ; <strong>Mission</strong> (objectif et étapes) ; <strong>Horaires</strong> (mise en route, décollage, IP, TOT et RTB proposés, modifiables) ; <strong>Groupe et équipage</strong> (nom du groupe, appareil, nombre, tâche, niveau de menace, puis une carte par unité : indicatif, type, numéro de bord, pilote ; l’appareil et le nombre se déduisent des unités dès que chacune a un type, et se lisent alors sans se modifier ; l’en-tête de la fiche en tire le groupe, « 2 × Mi-24P · CAS » ou « 1 × Mi-24P + 1 × Mi-8MT · CAS ») ; <strong>Navigation</strong> (jusqu’à 30 points : coordonnées, cap, distance, altitude, heure, note ; affichage en cap / distance, en MGRS ou en degrés, minutes, secondes, cap vrai ou magnétique ; un point sans coordonnées se place par le cap et la distance qui le relient au point voisin placé, avant ou après lui) ; <strong>Points de référence</strong> ; <strong>Radio</strong> (jusqu’à 4 postes de 20 canaux) ; <strong>Terrains</strong> (départ, arrivée, dégagement) ; <strong>Météo</strong> ; <strong>Carburant et emport</strong> (joker, bingo, lignes d’emport) ; <strong>Menaces et notes</strong>. La datacard d’un groupe a les mêmes sections, dans le même ordre ; la coalition s’y ajoute, et les champs partagés avec le Flight Configurator portent la pastille « FC ». Sur une carte libre, tout est <strong>texte libre</strong>. Chaque champ vide dit en grisé ce qu’on y met ; cet indice n’entre jamais dans la datacard. Le théâtre se choisit dans la barre, comme au Route Planner, et les trois modules le partagent : le changer dans l’un le change dans les autres ; le nom d’un terrain se choisit dans la liste des aérodromes de ce théâtre, avec une recherche : l’OACI (le code d’aujourd’hui, quand il est connu), la piste et la fréquence de tour prennent alors les valeurs de cet aérodrome, en remplaçant les précédentes ; la piste se choisit dans la liste de ses sens, celui face au vent de la Météo étant proposé d’abord ; « Autre… » vide les trois cases pour une saisie libre ; DEP et ARR viennent de la route et ne remplissent que des cases vides. La navigation d’une datacard est une route du Route Planner : un point saisi, déplacé ou supprimé ici l’est aussi là-bas, et inversement ; l’heure et la note restent à la datacard. Le cap et la distance se calculent, ou se saisissent pour placer le point. Les réglages de cap (vrai ou magnétique, déclinaison, année) sont communs à la mission. Les points de référence sont ceux du Route Planner, communs à la mission ; chaque datacard choisit ceux qu’elle affiche.</p></div>
        <div class="lang-block" data-lang="en"><p>Eleven sections, in the order of the sheet: <strong>Meta</strong> (classification, reference, operation, mission, date, time, units); <strong>Mission</strong> (objective and steps); <strong>Times</strong> (start-up, take-off, IP, TOT, and RTB suggested, editable); <strong>Group and crew</strong> (group name, aircraft, count, task, threat level, then one card per aircraft: callsign, type, board number, pilot; the aircraft and the count follow the aircraft as soon as each one has a type, and are then read-only; the sheet’s header draws the group from them, “2 × Mi-24P · CAS” or “1 × Mi-24P + 1 × Mi-8MT · CAS”); <strong>Navigation</strong> (up to 30 points: coordinates, heading, distance, altitude, time, note; shown as heading / distance, MGRS or degrees, minutes, seconds, true or magnetic heading; a waypoint without coordinates is placed by the heading and distance linking it to a placed neighbour, before or after it); <strong>Reference points</strong>; <strong>Radio</strong> (up to 4 radios of 20 channels); <strong>Airfields</strong> (departure, arrival, alternate); <strong>Weather</strong>; <strong>Fuel and loadout</strong> (joker, bingo, loadout lines); <strong>Threats and notes</strong>. A group’s datacard has the same sections, in the same order; the coalition is added, and the fields shared with the Flight Configurator carry the “FC” badge. On a free card, everything is <strong>free text</strong>. Each empty field shows in grey what to put there; that hint never makes it onto the datacard. The theatre is chosen in the bar, as in the Route Planner, and all three modules share it: changing it in one changes it in the others; an airfield’s name is picked from that theatre’s airfield list, with a search: the ICAO code (today’s, when known), runway and tower frequency then take that airfield’s values, replacing the previous ones; the runway is picked from the list of its ends, the one facing the Weather wind first; “Other…” clears the three boxes for free entry; DEP and ARR come from the route and only fill empty boxes. A datacard's navigation is a Route Planner route: a waypoint entered, moved or removed here is also changed there, and the other way round; time and note stay with the datacard. Course and distance are computed, or typed to place the waypoint. Course settings (true or magnetic, variation, year) are shared by the whole mission. Reference points are the Route Planner's, shared by the whole mission; each datacard chooses which ones it shows.</p></div>
      </div>

      <!-- Depuis le briefing -->
      <div class="fm-prose">
        <h3 class="lang-block" data-lang="fr">Depuis le briefing</h3>
        <h3 class="lang-block" data-lang="en">From the briefing</h3>
        <div class="lang-block" data-lang="fr"><p><strong>Ouvrir ▾ › Importer…</strong> ouvre une fenêtre à deux sources : le <strong>Briefing en cours</strong> — celui que le Briefing Generator a enregistré dans ce navigateur, grisé s’il n’y en a pas — ou un <strong>Fichier JSON (briefing ou route)</strong>. La fenêtre liste les <strong>groupes</strong> du briefing, tous cochés, et une ligne <strong>Données générales (sans groupe)</strong>, cochée d’office quand le briefing n’a aucun groupe : c’est le cas d’un brief Standard qui ne porte que des fréquences, des terrains et un METAR. <strong>Importer</strong> ajoute une datacard par ligne cochée, à la fin du paquet ; une datacard vierge laissée seule est remplacée. Un fichier de briefing ouvert par <strong>Ouvrir ▾ › Ouvrir une datacard…</strong> ouvre la même fenêtre.</p></div>
        <div class="lang-block" data-lang="en"><p><strong>Open ▾ › Import…</strong> opens a window with two sources: the <strong>Current briefing</strong> — the one the Briefing Generator saved in this browser, greyed out if there is none — or a <strong>JSON file (briefing or route)</strong>. The window lists the briefing’s <strong>groups</strong>, all ticked, and a <strong>General data (no group)</strong> line, ticked by default when the briefing has no groups: that is the case of a Standard brief that only carries frequencies, airfields, and a METAR. <strong>Import</strong> adds one datacard per ticked line, at the end of the deck; a lone blank datacard is replaced. A briefing file opened with <strong>Open ▾ › Open a datacard…</strong> opens the same window.</p></div>
      </div>

      <!-- Ce que l’import remplit -->
      <div class="fm-prose">
        <h3 class="lang-block" data-lang="fr">Ce que l’import remplit</h3>
        <h3 class="lang-block" data-lang="en">What the import fills in</h3>
        <div class="lang-block" data-lang="fr"><p>Pour chaque groupe : la méta du briefing ; l’<strong>indicatif</strong> (le sous-groupe, sinon l’indicatif de l’escadron), l’appareil, le nombre (celui du groupe, sinon le nombre de pilotes de son équipage), la tâche et la menace ; l’objectif et les étapes, sous-tâches comprises ; l’<strong>équipage</strong> du groupe ; la <strong>radio</strong>, depuis le plan de son appareil, ou à défaut un poste « Fréquences » qui reprend toutes les fréquences du briefing ; les <strong>terrains</strong>, le terrain de départ marqué DEP ; le <strong>METAR</strong>, décodé ; les menaces SAM et AAA ; les notes. Restent à remplir à la main : les <strong>horaires</strong>, la <strong>navigation</strong> (sauf à la prendre au Route Planner), le <strong>carburant</strong> et l’<strong>emport</strong>. La datacard importée vit ensuite seule : modifier le briefing ne la change pas.</p></div>
        <div class="lang-block" data-lang="en"><p>For each group: the briefing’s meta; the <strong>callsign</strong> (the subgroup, otherwise the squadron callsign), the aircraft, the count (the group’s own, otherwise the number of pilots in its crew), the task, and the threat; the objective and the steps, sub-tasks included; the group’s <strong>crew</strong>; the <strong>radio</strong>, from its aircraft’s plan, or failing that a “Frequencies” radio carrying every frequency in the briefing; the <strong>airfields</strong>, with the departure field marked DEP; the <strong>METAR</strong>, decoded; the SAM and AAA threats; the notes. Left to fill in by hand: <strong>times</strong>, <strong>navigation</strong> (unless you take it from the Route Planner), <strong>fuel</strong>, and <strong>loadout</strong>. Once imported, the datacard lives on its own: changing the briefing doesn’t change it.</p></div>
      </div>

      <!-- Depuis le Route Planner -->
      <div class="fm-prose">
        <h3 class="lang-block" data-lang="fr">Depuis le Route Planner</h3>
        <h3 class="lang-block" data-lang="en">From the Route Planner</h3>
        <div class="lang-block" data-lang="fr"><p><strong>Ouvrir ▾ › Importer…</strong> lit aussi une route, ou un jeu de routes, depuis un fichier JSON, par la source <strong>Fichier JSON (briefing ou route)</strong> ou par <strong>Ouvrir ▾ › Ouvrir une datacard…</strong>. La fenêtre montre le nom de la route et son nombre de points, puis deux choix : <strong>Lier la carte à cette route</strong> — la navigation de la datacard affichée devient cette route — ou <strong>Nouvelle datacard</strong>, ajoutée au paquet ; un jeu de routes ajoute <strong>Toutes les routes (n), une datacard par route</strong>. La navigation est la route elle-même, avec les coordonnées MGRS et l’altitude de ses points ; les réglages de cap (vrai ou magnétique, déclinaison, année) sont communs au Route Planner et au Datacard Generator, et l’année vient de la mission ou de l’année saisie, non du champ <strong>Date</strong> de la datacard. Pour suivre une route que le Route Planner garde dans ce navigateur, la datacard a sa propre liste <strong>Lier à une autre route</strong> : choisir une route la lie à la datacard affichée ; <strong>… › Une datacard par route</strong> crée d’un coup une datacard par route du Route Planner (grisé tant qu’il n’y a pas deux routes).</p></div>
        <div class="lang-block" data-lang="en"><p><strong>Open ▾ › Import…</strong> also reads a route, or a route set, from a JSON file, through the <strong>JSON file (briefing or route)</strong> source or through <strong>Open ▾ › Open a datacard…</strong>. The window shows the route’s name and its number of waypoints, then two choices: <strong>Link the card to this route</strong> — the navigation of the datacard shown becomes this route — or <strong>New datacard</strong>, added to the deck; a route set adds <strong>All routes (n), one datacard per route</strong>. Navigation is the route itself, with the MGRS coordinates and altitude of its waypoints; course settings (true or magnetic, variation, year) are shared by the Route Planner and the Datacard Generator, and the year comes from the mission or the typed year, not from the datacard’s <strong>Date</strong> field. To follow a route the Route Planner keeps in this browser, the datacard has its own <strong>Link to another route</strong> list: picking a route links it to the datacard shown; <strong>… › One datacard per route</strong> creates one datacard per Route Planner route in one go (greyed out until there are two routes).</p></div>
      </div>

      <!-- Figure 2 : ce qui alimente la datacard -->
      <div class="fm-schema">
        {DG_FEED_SVG}
        <div class="fm-schema-legend">
          <span class="lang-block" data-lang="fr">Fig. 2 — Ce qui alimente la datacard, et ce qu’elle produit.</span>
          <span class="lang-block" data-lang="en">Fig. 2 — What feeds the datacard, and what it produces.</span>
        </div>
      </div>

      <!-- Day ou Night -->
      <div class="fm-prose">
        <h3 class="lang-block" data-lang="fr">Jour ou Nuit</h3>
        <h3 class="lang-block" data-lang="en">Day or Night</h3>
        <div class="lang-block" data-lang="fr"><p>Le choix <strong>Jour | Nuit</strong>, dans le menu <strong>Affichage ▾</strong>, groupe <strong>Datacard</strong>, donne à tout le paquet sa version de <strong>jour</strong> — encre sombre sur papier clair — ou de <strong>nuit</strong> — tons sourds sur fond sombre, sans aucun blanc pur, pour ne pas éblouir dans un cockpit de nuit. Les thèmes de l’outil ne changent rien à la datacard : seule cette bascule compte.</p></div>
        <div class="lang-block" data-lang="en"><p>The <strong>Day | Night</strong> choice, in the <strong>Display ▾</strong> menu, <strong>Datacard</strong> group, gives the whole deck its <strong>day</strong> version — dark ink on light paper — or its <strong>night</strong> version — muted tones on a dark background, with no pure white, so as not to dazzle in a night cockpit. The tool’s themes change nothing on the datacard: only this switch counts.</p></div>
      </div>

      <!-- Unités, dates et METAR -->
      <div class="fm-prose">
        <h3 class="lang-block" data-lang="fr">Unités, dates et METAR</h3>
        <h3 class="lang-block" data-lang="en">Units, dates, and METAR</h3>
        <div class="lang-block" data-lang="fr"><p>Les unités (masse <strong>kg</strong> ou <strong>lb</strong>, distance <strong>km</strong> ou <strong>NM</strong>, altitude <strong>m</strong> ou <strong>ft</strong>) changent les intitulés et les suffixes de la fiche, <strong>jamais les valeurs saisies</strong> : rien n’est converti. Une date saisie au format AAAA-MM-JJ s’affiche « 22 MAR 1989 » ; toute autre forme s’affiche telle quelle. Le <strong>METAR</strong>, saisi ou importé, se décode tout seul en vent, visibilité, QNH et nuages, qui restent modifiables ensuite ; la météo garde les conventions du METAR, quelles que soient les unités de la carte. Les unités (masse, distance, altitude) se choisissent dans le menu <strong>Affichage ▾</strong>, groupe <strong>Unités</strong>, valent pour toutes les cartes et sont partagées avec le Route Planner.</p></div>
        <div class="lang-block" data-lang="en"><p>Units (mass <strong>kg</strong> or <strong>lb</strong>, distance <strong>km</strong> or <strong>NM</strong>, altitude <strong>m</strong> or <strong>ft</strong>) change the sheet’s headings and suffixes, <strong>never the values you entered</strong>: nothing is converted. A date entered as YYYY-MM-DD shows as “22 MAR 1989”; any other form shows as typed. The <strong>METAR</strong>, typed or imported, decodes itself into wind, visibility, QNH, and clouds, which stay editable afterwards; the weather keeps METAR conventions, whatever the card’s units. Units (mass, distance, altitude) are picked in the <strong>Display ▾</strong> menu, <strong>Units</strong> group, apply to every card and are shared with the Route Planner.</p></div>
      </div>

      <!-- Quand la page déborde -->
      <div class="fm-prose">
        <h3 class="lang-block" data-lang="fr">Quand la page déborde</h3>
        <h3 class="lang-block" data-lang="en">When the page overflows</h3>
        <div class="lang-block" data-lang="fr"><p>La fiche garde toujours toutes ses boîtes, même vides, pour être imprimée et complétée à la main : une boîte vide montre ses titres et quelques lignes à remplir, et une valeur absente d’une rangée remplie s’écrit « — ». Quand tout ne tient pas sur la page, la <strong>navigation passe sur une page 2</strong>, avec un en-tête réduit « DATACARD · NAVIGATION ».</p></div>
        <div class="lang-block" data-lang="en"><p>The sheet always keeps all its blocks, even empty ones, so it can be printed and filled in by hand: an empty block shows its headings and a few lines to fill in, and a missing value in a filled row reads “—”. When everything doesn’t fit on the page, <strong>navigation moves to a page 2</strong>, with a reduced “DATACARD · NAVIGATION” header.</p></div>
      </div>

      <!-- Sauvegarder & reprendre -->
      <div class="fm-prose">
        <h3 class="lang-block" data-lang="fr">Sauvegarder &amp; reprendre</h3>
        <h3 class="lang-block" data-lang="en">Save &amp; resume</h3>
        <div class="lang-block" data-lang="fr"><p>Le paquet est <strong>sauvegardé automatiquement</strong> dans le navigateur. <strong>Sauvegarder</strong> l’écrit en fichier pour l’archiver ou le partager (<kbd>Ctrl</kbd>+<kbd>S</kbd>, <kbd>Cmd</kbd>+<kbd>S</kbd> sur Mac, fait le même geste) ; <strong>Ouvrir ▾ › Ouvrir une datacard…</strong> le rouvre ; il remplace le paquet en cours, après confirmation si celui-ci n’est pas vierge. <strong>Exemple</strong> ouvre une datacard de démonstration ; <strong>Effacer</strong> vide le document. Tous deux demandent confirmation.</p></div>
        <div class="lang-block" data-lang="en"><p>The deck is <strong>saved automatically</strong> in the browser. <strong>Save</strong> writes it to a file to archive or share it (<kbd>Ctrl</kbd>+<kbd>S</kbd>, <kbd>Cmd</kbd>+<kbd>S</kbd> on a Mac, does the same); <strong>Open ▾ › Open a datacard…</strong> reopens it; it replaces the current deck, after confirmation unless that deck is blank. <strong>Example</strong> opens a demonstration datacard; <strong>Clear</strong> clears the document. Both ask for confirmation.</p></div>
      </div>

      <!-- Exporter -->
      <div class="fm-prose">
        <h3 class="lang-block" data-lang="fr">Exporter</h3>
        <h3 class="lang-block" data-lang="en">Export</h3>
        <div class="lang-block" data-lang="fr"><p><strong>Exporter</strong> propose le <strong>PDF</strong> ou le <strong>PNG</strong>. Le PDF passe par l’impression du navigateur : chaque page de chaque datacard occupe une feuille <strong>A4</strong> entière, couleurs de fond comprises. Le PNG produit une image de <strong>2 000 × 2 828 px</strong> par page, au format d’une page de kneeboard ; vous choisissez les pages, et plusieurs pages partent dans un fichier ZIP. L’export suit la version jour ou nuit affichée.</p></div>
        <div class="lang-block" data-lang="en"><p><strong>Export</strong> offers <strong>PDF</strong> or <strong>PNG</strong>. The PDF goes through the browser’s print: each page of each datacard takes up a whole <strong>A4</strong> sheet, background colours included. The PNG produces a <strong>2,000 × 2,828 px</strong> image per page, the size of a kneeboard page; you pick the pages, and several pages go out in a ZIP file. The export follows the day or night version on display.</p></div>
      </div>

      <!-- Sur tablette et téléphone -->
      <div class="fm-prose">
        <h3 class="lang-block" data-lang="fr">Sur tablette et téléphone</h3>
        <h3 class="lang-block" data-lang="en">On tablets and phones</h3>
        <div class="lang-block" data-lang="fr"><p>Jusqu’à 1 100 px de large, l’éditeur passe en <strong>onglets à icône</strong>, un par section, plus <strong>Aperçu</strong>. La barre du haut défile au doigt quand elle ne tient pas ; un fondu sur un bord signale les boutons cachés.</p></div>
        <div class="lang-block" data-lang="en"><p>Up to 1,100 px wide, the editor switches to <strong>icon tabs</strong>, one per section, plus <strong>Preview</strong>. The top bar scrolls by finger when it doesn’t fit; a fade on one edge shows the hidden buttons.</p></div>
      </div>

      <!-- Tout est générique -->
      <div class="fm-callout note">
        <div class="lang-block" data-lang="fr">Tout est générique — Le Datacard Generator ne contient aucune table d’appareils, de radios ou d’emports : ce que vous saisissez s’affiche tel quel. Il sert donc à tout appareil, sans mise à jour quand un module DCS change.</div>
        <div class="lang-block" data-lang="en">Everything is generic — The Datacard Generator holds no table of aircraft, radios, or loadouts: what you type shows as typed. It therefore works for any aircraft, with no update needed when a DCS module changes.</div>
      </div>

      <!-- Contenu tronqué -->
      <div class="fm-callout warn">
        <div class="lang-block" data-lang="fr">Contenu tronqué — Si la page 1 déborde encore une fois la navigation passée en page 2, l’éditeur affiche « Contenu tronqué ». Allégez alors la mission, les notes ou les menaces : la fiche ne se réduit pas d’elle-même.</div>
        <div class="lang-block" data-lang="en">Content truncated — If page 1 still overflows once navigation has moved to page 2, the editor shows “Content truncated”. Trim the mission, notes, or threats: the sheet doesn’t shrink on its own.</div>
      </div>

      <!-- À venir -->
      <div class="fm-callout note">
        <div class="lang-block" data-lang="fr">À venir — L’import des points de navigation et de l’emport depuis HQ (mission <code>.miz</code>) est prévu dans une prochaine version.</div>
        <div class="lang-block" data-lang="en">Coming — Importing navigation points and loadouts from HQ (<code>.miz</code> mission) is planned for a future version.</div>
      </div>

    </div><!-- /fm-chapter -->
  </section><!-- /page-dg -->

  <!-- ===== PAGE RP ===== -->
  <section id="page-rp" class="fm-page hidden">
    <div class="fm-chapter" style="--chapter-accent:#7ac97a; --chapter-accent-rgb:122,201,122;">

      <button class="fm-back-btn" onclick="navigate('index')" data-i18n="btn.back">◄ Index</button>

      <div class="fm-hero">
        <img class="fm-hero-img" src="{RP_TILE_SRC}" alt="Route Planner" draggable="false">
        <div class="fm-hero-pin" aria-hidden="true"></div>
        <div class="fm-hero-caption">
          <div><div class="fm-hero-monogram">RP</div></div>
          <div>
            <div class="fm-hero-title" data-i18n="rp.hero.title">Route Planner</div>
            <div class="fm-hero-sub" data-i18n="rp.hero.sub">Routes, navigation et cartes de mission</div>
          </div>
        </div>
      </div>

      <!-- À quoi ça sert -->
      <div class="fm-prose">
        <h3 class="lang-block" data-lang="fr">À quoi ça sert</h3>
        <h3 class="lang-block" data-lang="en">What it’s for</h3>
        <div class="lang-block" data-lang="fr"><p>Le Route Planner trace la <strong>route d’un groupe</strong> sur la carte d’un théâtre de DCS et en donne la <strong>navigation</strong> : caps, distances, temps. Vous y posez des <strong>points de référence</strong> et des <strong>calques</strong> tactiques, vous consultez la <strong>fiche d’un terrain</strong>, puis vous passez la route au <strong>Datacard Generator</strong>, la carte au <strong>Briefing Generator</strong>, ou la route au <strong>Route Tool</strong> de DCS. Les routes se modifient aussi depuis le Datacard Generator, et les réglages de cap sont partagés avec lui.</p></div>
        <div class="lang-block" data-lang="en"><p>The Route Planner lays a <strong>group’s route</strong> on the map of a DCS theatre and gives you its <strong>navigation</strong>: headings, distances, times. You add <strong>reference points</strong> and tactical <strong>layers</strong>, you look up an <strong>airfield’s chart sheet</strong>, then you pass the route to the <strong>Datacard Generator</strong>, the map to the <strong>Briefing Generator</strong>, or the route to the DCS <strong>Route Tool</strong>. Routes can also be edited from the Datacard Generator, and course settings are shared with it.</p></div>
      </div>

      <!-- Figure 1 : l’écran du Route Planner -->
      <div class="fm-schema">
        {RP_SCREEN_SVG}
        <div class="fm-schema-legend">
          <span class="lang-block" data-lang="fr">Fig. 1 — L’écran du Route Planner : la carte, ses modes de toucher et le panneau.</span>
          <span class="lang-block" data-lang="en">Fig. 1 — The Route Planner screen: the map, its tap modes, and the panel.</span>
        </div>
      </div>

      <!-- Le théâtre et le fond de carte -->
      <div class="fm-prose">
        <h3 class="lang-block" data-lang="fr">Le théâtre et le fond de carte</h3>
        <h3 class="lang-block" data-lang="en">Theatre and base map</h3>
        <div class="lang-block" data-lang="fr"><p>Le sélecteur <strong>Théâtre</strong> choisit la carte de DCS : Caucase, Allemagne (guerre froide), Syrie, Golfe Persique, Normandie, Manche, Nevada, Mariannes, Mariannes 1944, Kola, Sinaï, Irak, Afghanistan, Atlantique Sud. Le groupe <strong>Fond</strong>, en tête du menu <strong>Affichage ▾</strong>, propose <strong>Carte DCS</strong>, <strong>Topo</strong>, <strong>Satellite</strong> et <strong>Grille</strong>, et, sur le Caucase seulement, la <strong>Carte de navigation (Flappie)</strong> : elle n’apparaît pas dans la rangée sur les autres théâtres. Là où DCS n’a pas de carte, le bouton <strong>Carte DCS</strong> se grise, et son info-bulle dit <strong>Carte DCS — absente de ce théâtre</strong>. Les crédits de chaque fond restent affichés au pied de la carte.</p><p>Sous le fond, le groupe <strong>Unités</strong> règle la <strong>Distance</strong> (km ou NM) et l’<strong>Altitude</strong> (m ou ft). Puis, sous <strong>Afficher sur la carte</strong>, le menu dit ce que montre la carte, en trois groupes. <strong>Mission</strong> : <strong>Route</strong>, <strong>Points de réf.</strong> ; <strong>Calques</strong> : <strong>Dessins</strong>, <strong>Symboles OTAN</strong>, <strong>Calques importés</strong> ; <strong>Repères</strong> : <strong>Grille MGRS</strong>, <strong>Villes</strong>, <strong>Aérodromes</strong>, <strong>Lieux (Esri)</strong>. Les villes s’affichent à partir du zoom 10 ; elles sont grisées sur la carte de Flappie, qui les écrit déjà. Les aérodromes et les villes sont grisés sur un théâtre qui n’en a pas. Ce qui est masqué n’est ni dessiné ni touchable ; un point ambre sur le bouton signale un réglage du menu qui n’est plus celui d’origine, un fond autre que Topo ou des unités autres que km et m compris.</p><p>La loupe, en haut à gauche de la carte, ouvre la <strong>recherche</strong> : une ville, un aérodrome ou une hélistation, un point de la route, une référence, ou un objet nommé d’un calque affiché. Choisir un résultat centre la carte dessus.</p></div>
        <div class="lang-block" data-lang="en"><p>The <strong>Theatre</strong> selector picks the DCS map: Caucasus, Cold War Germany, Syria, Persian Gulf, Normandy, The Channel, Nevada, Mariana Islands, Mariana Islands WWII, Kola, Sinai, Iraq, Afghanistan, South Atlantic. The <strong>Base map</strong> group, at the top of the <strong>Display ▾</strong> menu, offers <strong>DCS map</strong>, <strong>Topo</strong>, <strong>Satellite</strong> and <strong>Grid</strong>, and, on the Caucasus only, the <strong>Navigation chart (Flappie)</strong>: it does not appear in the row on other theatres. Where DCS has no map, the <strong>DCS map</strong> button is greyed out, and its tooltip reads <strong>DCS map — not available for this theatre</strong>. Each background’s credits stay shown at the foot of the map.</p><p>Under the base map, the <strong>Units</strong> group sets <strong>Distance</strong> (km or NM) and <strong>Altitude</strong> (m or ft). Then, under <strong>Show on the map</strong>, the menu sets what the map shows, in three groups. <strong>Mission</strong>: <strong>Route</strong>, <strong>Ref. points</strong>; <strong>Layers</strong>: <strong>Drawings</strong>, <strong>NATO symbols</strong>, <strong>Imported layers</strong>; <strong>Overlays</strong>: <strong>MGRS grid</strong>, <strong>Towns</strong>, <strong>Airfields</strong>, <strong>Places (Esri)</strong>. Towns show from zoom 10; they are greyed out on Flappie’s chart, which already prints them. Airfields and towns are greyed out on a theatre that has none. What is hidden is neither drawn nor tappable; an amber dot on the button means a setting of the menu is no longer the original one, a base map other than Topo or units other than km and m included.</p><p>The magnifier, at the top left of the map, opens the <strong>search</strong>: a town, an airfield or a heliport, a waypoint, a reference point, or a named item in a shown layer. Picking a result centres the map on it.</p></div>
      </div>

      <!-- Ce que fait un toucher -->
      <div class="fm-prose">
        <h3 class="lang-block" data-lang="fr">Ce que fait un toucher</h3>
        <h3 class="lang-block" data-lang="en">What a tap does</h3>
        <div class="lang-block" data-lang="fr"><p>En haut à droite de la carte, quatre modes disent ce que fait un toucher :</p><ul><li><strong>Point</strong> — ajoute un point au bout de la route ;</li><li><strong>Réf.</strong> — pose un point de référence ;</li><li><strong>Lire</strong> — ne pose rien : un aérodrome ouvre sa fiche, un objet d’un calque montre la sienne ;</li><li><strong>Dessin</strong> — ouvre les outils de dessin de vos propres calques.</li></ul><p>En <strong>Point</strong> et en <strong>Réf.</strong>, un aérodrome touché donne un point à son nom, en capitales ; une cible d’un calque (un point ou un symbole) devient de même un point de la route ou une référence. Un mode qui modifie quelque chose le rend visible s’il était masqué dans <strong>Affichage</strong>.</p></div>
        <div class="lang-block" data-lang="en"><p>At the top right of the map, four modes set what a tap does:</p><ul><li><strong>Waypoint</strong> — adds a waypoint at the end of the route;</li><li><strong>Ref.</strong> — places a reference point;</li><li><strong>Read</strong> — places nothing: an airfield opens its chart sheet, a layer item shows its own card;</li><li><strong>Draw</strong> — opens the tools for drawing your own layers.</li></ul><p>In <strong>Waypoint</strong> and <strong>Ref.</strong> modes, a tapped airfield gives a point named after it, in capitals; a target in a layer (a point or a symbol) likewise becomes a waypoint or a reference point. A mode that edits something makes it visible if it was hidden under <strong>Display</strong>.</p></div>
      </div>

      <!-- Construire la route -->
      <div class="fm-prose">
        <h3 class="lang-block" data-lang="fr">Construire la route</h3>
        <h3 class="lang-block" data-lang="en">Building the route</h3>
        <div class="lang-block" data-lang="fr"><p>En tête de la section <strong>Route</strong>, une ligne choisit la route : « 1 · FOOTHOLD M3 ▾ » ouvre la liste des routes du théâtre ; <strong>+</strong> ajoute une route ; <strong>…</strong> ouvre <strong>Dupliquer</strong> et <strong>Supprimer</strong> ; dessous, « 1 / 1 routes » donne le rang de la route choisie et le total. Il y a 12 routes au plus : <strong>+</strong> se grise alors, et son info-bulle le dit.</p><p>Touchez la carte pour ajouter un point ; glissez un point pour le déplacer ; le « + » posé sur une branche assez longue insère un point ; il ne paraît qu’en modes <strong>Point</strong> et <strong>Réf.</strong> La route compte <strong>30 points</strong> au plus. Sans toucher la carte, le bloc <strong>Ajouter</strong> place un point par ses <strong>Coordonnées</strong> — MGRS, DMS, DDM ou décimal — ou par <strong>Cap et distance</strong> depuis le dernier point, le cap s’entendant comme celui de la navigation, vrai ou magnétique ; <strong>+ Point</strong> l’ajoute à la route, <strong>+ Réf.</strong> en fait une référence.</p><p>Chaque point a sa ligne dans la section <strong>Route</strong> : un <strong>Nom</strong>, une altitude et sa référence, <strong>SOL</strong> ou <strong>MER</strong>, une vitesse (laissée vide, c’est la vitesse sol de la route ; le point de départ n’en a pas), et × pour le supprimer. Les unités, km ou NM, m ou ft, se choisissent dans le menu <strong>Affichage ▾</strong>, groupe <strong>Unités</strong>. Le champ <strong>Nom de la route</strong> donne son nom à la route. <strong>Groupes…</strong> choisit les groupes qui suivent cette route, ou en crée un ; un groupe ne suit qu'une route. Le Flight Configurator voit le même choix, et ce qu'il change se voit ici. <strong>Exemple</strong> ouvre une route de démonstration et <strong>Effacer</strong> vide la route ; tous deux demandent confirmation. Les unités sont partagées avec le Datacard Generator. Chaque route garde son théâtre : en changer masque les routes des autres théâtres, qui reviennent quand on y retourne. Un fichier de routes garde le théâtre de chacune : à l’ouverture, chaque route retrouve le sien, et ouvrir un jeu de routes remplace toutes les routes, de tous les théâtres.</p></div>
        <div class="lang-block" data-lang="en"><p>At the top of the <strong>Route</strong> section, one line picks the route: “1 · FOOTHOLD M3 ▾” opens the list of the theatre’s routes; <strong>+</strong> adds a route; <strong>…</strong> opens <strong>Duplicate</strong> and <strong>Delete</strong>; below, “1 / 1 routes” gives the rank of the chosen route and the total. There are 12 routes at most: <strong>+</strong> is then greyed out, and its tooltip says so.</p><p>Tap the map to add a waypoint; drag a waypoint to move it; the “+” placed on a long enough leg inserts a waypoint; it only shows in <strong>Waypoint</strong> and <strong>Ref.</strong> modes. The route holds <strong>30 waypoints</strong> at most. Without tapping the map, the <strong>Add</strong> block places a point by its <strong>Coordinates</strong> — MGRS, DMS, DDM or decimal — or by <strong>Heading and distance</strong> from the last waypoint, the heading being read like the navigation’s, true or magnetic; <strong>+ Waypoint</strong> adds it to the route, <strong>+ Ref.</strong> makes it a reference point.</p><p>Each waypoint has its row in the <strong>Route</strong> section: a <strong>Name</strong>, an altitude and its reference, <strong>AGL</strong> or <strong>MSL</strong>, a speed (left empty, it is the route’s ground speed; the starting point has none), and × to delete it. Units, km or NM, m or ft, are chosen in the <strong>Display ▾</strong> menu, <strong>Units</strong> group. The <strong>Route name</strong> field names the route. <strong>Groups…</strong> picks the groups that follow this route, or creates one; a group follows one route. The Flight Configurator sees the same choice, and what it changes shows here. <strong>Example</strong> opens a demonstration route and <strong>Clear</strong> empties the route; both ask for confirmation. Units are shared with the Datacard Generator. Each route keeps its theatre: switching theatre hides the other theatres' routes, which come back when you return. A route file keeps each route's theatre: on opening, every route returns to its own, and opening a route set replaces all routes, on every theatre.</p></div>
      </div>

      <!-- Les points de référence -->
      <div class="fm-prose">
        <h3 class="lang-block" data-lang="fr">Les points de référence</h3>
        <h3 class="lang-block" data-lang="en">Reference points</h3>
        <div class="lang-block" data-lang="fr"><p>Les <strong>Points de référence</strong> marquent ce qui compte hors de la route : une cible, un repère, un terrain. Il y en a <strong>12</strong> au plus. Posez-les en mode <strong>Réf.</strong> ou par <strong>+ Réf.</strong> ; glissez-les pour les déplacer. Sur la carte, chacun est un losange à sa lettre, A, B, C…, sans trait qui les relie. Dans la navigation, ils viennent après le total, sous <strong>POINTS DE RÉFÉRENCE</strong>, avec leurs coordonnées : ils ne comptent ni dans les branches ni dans le total. Ils passent à la datacard, mais pas au Route Tool de DCS.</p></div>
        <div class="lang-block" data-lang="en"><p><strong>Reference points</strong> mark what matters off the route: a target, a landmark, an airfield. There are <strong>12</strong> at most. Place them in <strong>Ref.</strong> mode or with <strong>+ Ref.</strong>; drag them to move them. On the map, each is a diamond with its letter, A, B, C…, with no line joining them. In the navigation, they come after the total, under <strong>REFERENCE POINTS</strong>, with their coordinates: they count neither in the legs nor in the total. They go to the datacard, but not to the DCS Route Tool.</p></div>
      </div>

      <!-- Le tracé et les boîtes de branche -->
      <div class="fm-prose">
        <h3 class="lang-block" data-lang="fr">Le tracé et les boîtes de branche</h3>
        <h3 class="lang-block" data-lang="en">The track and leg boxes</h3>
        <div class="lang-block" data-lang="fr"><p>Les <strong>Boîtes de branche</strong> écrivent la navigation sur la carte, une boîte par branche. <strong>Aucune</strong> : une simple étiquette « cap · distance » sur les branches assez longues. <strong>Minimale</strong> : le cap et la distance. <strong>Complète</strong> : en plus, la vitesse, l’altitude d’arrivée, l’ETE et le nom du point d’arrivée. Glissez une boîte pour la déplacer ; une branche trop courte à l’écran n’en a pas.</p><p>La <strong>Vitesse sol</strong> de la route vaut pour chaque branche dont le point n’a pas sa propre vitesse ; elle fait les temps. Les <strong>Traits des minutes</strong> coupent chaque branche toutes les minutes, ou toutes les cinq minutes quand elle est trop serrée, avec leurs chiffres. <strong>Tracé</strong> et <strong>Traits des minutes</strong> se montrent en <strong>Couleur</strong> ou en <strong>Noir</strong>.</p></div>
        <div class="lang-block" data-lang="en"><p><strong>Leg boxes</strong> write the navigation on the map, one box per leg. <strong>None</strong>: a plain “heading · distance” label on long enough legs. <strong>Minimal</strong>: heading and distance. <strong>Full</strong>: also speed, arrival altitude, ETE, and the name of the arrival waypoint. Drag a box to move it; a leg too short on screen gets none.</p><p>The route’s <strong>Ground speed</strong> applies to every leg whose waypoint has no speed of its own; it sets the times. <strong>Minute marks</strong> cut each leg every minute, or every five minutes when it is too tight, with their numbers. <strong>Route line</strong> and <strong>Minute marks</strong> show in <strong>Colour</strong> or in <strong>Black</strong>.</p></div>
      </div>

      <!-- Navigation : cap vrai ou magnétique -->
      <div class="fm-prose">
        <h3 class="lang-block" data-lang="fr">Navigation : cap vrai ou magnétique</h3>
        <h3 class="lang-block" data-lang="en">Navigation: true or magnetic heading</h3>
        <div class="lang-block" data-lang="fr"><p>Le tableau de la section <strong>Navigation</strong> donne, pour chaque point, son <strong>N°</strong>, son nom et son altitude (<strong>Point · alt.</strong>), ses coordonnées MGRS et DMS, et entre deux points la branche : cap, vitesse, ETE et distance (<strong>MGRS · DMS / cap · distance</strong>). Le <strong>TOTAL</strong> donne la distance et le temps de la route. Le titre du tableau dit le cap employé.</p><p><strong>Cap</strong> : <strong>Vrai</strong> ou <strong>Magnétique</strong>. En magnétique, la <strong>Déclinaison</strong> est <strong>Calculée</strong> ou <strong>Saisie</strong>.</p><ul><li><strong>Calculée</strong> — le modèle magnétique de DCS lui-même, les coefficients que DCS embarque : IGRF pour une année jusqu’à 1985, puis les WMM de 1985 à 2025. Elle s’applique <strong>par branche, au point de départ de la branche</strong> : chaque point montre sa VAR, et le titre en donne l’étendue. L’année est celle de la mission chargée dans HQ pour le même théâtre ; sinon l’<strong>Année</strong> saisie ; sinon 1985. Le bouton <strong>Forcer</strong> n’apparaît que si une mission de HQ du même théâtre est chargée ; tant qu’il n’est pas enfoncé, l’<strong>Année</strong> reste celle de la mission. Enfoncé, il n’agit qu’avec une <strong>Année</strong> valide saisie, de 1900 à 2099 : la mission est alors ignorée. Sous les réglages, une étiquette dit la source de l’année : <strong>MISSION</strong>, <strong>FORCÉE</strong>, <strong>SAISIE</strong> ou <strong>PAR DÉFAUT</strong>.</li><li><strong>Saisie</strong> — une seule valeur, <strong>Déclinaison (°)</strong>, en degrés, + vers l’Est, lue en cabine : au CDU de l’A-10C (POSINFO), au DED du F-16 (MVAR) ou à l’HSI du F/A-18. Sans valeur, le cap reste vrai, et l’avertissement le dit : <strong>Déclinaison manquante : cap vrai affiché</strong>.</li></ul></div>
        <div class="lang-block" data-lang="en"><p>The table in the <strong>Navigation</strong> section gives, for each waypoint, its <strong>No.</strong>, its name and altitude (<strong>Waypoint · alt.</strong>), its MGRS and DMS coordinates, and between two waypoints the leg: heading, speed, ETE, and distance (<strong>MGRS · DMS / heading · distance</strong>). The <strong>TOTAL</strong> gives the route’s distance and time. The table’s title states the heading used.</p><p><strong>Heading</strong>: <strong>True</strong> or <strong>Magnetic</strong>. In magnetic, the <strong>Variation</strong> is <strong>Computed</strong> or <strong>Entered</strong>.</p><ul><li><strong>Computed</strong> — DCS’s own magnetic model, the coefficients DCS ships: IGRF for years up to 1985, then the WMM of 1985 to 2025. It applies <strong>per leg, at the leg’s start point</strong>: each waypoint shows its VAR, and the title gives the range. The year is that of the mission loaded in HQ for the same theatre; otherwise the <strong>Year</strong> you type; otherwise 1985. The <strong>Override</strong> button only appears when an HQ mission for the same theatre is loaded; until it is pressed, the <strong>Year</strong> stays the mission’s. Pressed, it only acts with a valid <strong>Year</strong> typed, from 1900 to 2099: the mission is then ignored. Below the settings, a tag states where the year comes from: <strong>MISSION</strong>, <strong>OVERRIDDEN</strong>, <strong>ENTERED</strong>, or <strong>DEFAULT</strong>.</li><li><strong>Entered</strong> — a single value, <strong>Variation (°)</strong>, in degrees, + East, read in the cockpit: on the A-10C CDU (POSINFO), the F-16 DED (MVAR) or the F/A-18 HSI. With no value, the heading stays true, and a warning says so: <strong>Variation missing: true heading shown</strong>.</li></ul></div>
      </div>

      <!-- La fiche d’un aérodrome -->
      <div class="fm-prose">
        <h3 class="lang-block" data-lang="fr">La fiche d’un aérodrome</h3>
        <h3 class="lang-block" data-lang="en">An airfield’s chart sheet</h3>
        <div class="lang-block" data-lang="fr"><p>En mode <strong>Lire</strong>, avec les <strong>Aérodromes</strong> affichés, touchez un aérodrome ou une hélistation : sa <strong>fiche</strong> s’ouvre. Elle montre les pages d’une chart de DCS Airfield Charts, une par onglet ; pour une <strong>Hélistation</strong>, les pages du répertoire qui la portent. Pincez pour zoomer, touchez deux fois pour recadrer ; à la souris, la molette zoome. L’édition des charts est rappelée en pied. Rien n’est téléchargé avant votre toucher. Trois replis : <strong>Pas de fiche</strong> — le terrain n’en a pas encore ; <strong>Fiches indisponibles</strong> — le serveur des fiches ne répond pas ; <strong>Page indisponible</strong> — une page ne se charge pas.</p></div>
        <div class="lang-block" data-lang="en"><p>In <strong>Read</strong> mode, with <strong>Airfields</strong> shown, tap an airfield or a heliport: its <strong>chart sheet</strong> opens. It shows the pages of a DCS Airfield Charts chart, one per tab; for a <strong>Heliport</strong>, the directory pages that list it. Pinch to zoom, double-tap to reframe; with a mouse, the wheel zooms. The charts’ edition is shown at the foot. Nothing is downloaded before your tap. Three fallbacks: <strong>No sheet</strong> — the airfield has none yet; <strong>Sheets unavailable</strong> — the sheet server does not answer; <strong>Page unavailable</strong> — a page does not load.</p></div>
      </div>

      <!-- Dessiner ses calques -->
      <div class="fm-prose">
        <h3 class="lang-block" data-lang="fr">Dessiner ses calques</h3>
        <h3 class="lang-block" data-lang="en">Drawing your own layers</h3>
        <div class="lang-block" data-lang="fr"><p>Le mode <strong>Dessin</strong> ouvre une barre au pied de la carte. Son bouton <strong>Calque</strong> dit où vous dessinez ; touché, il ouvre <strong>Dessiner dans</strong> : choisir un de vos calques, en créer un par <strong>+ Calque</strong>, ou faire une copie modifiable d’un calque CombatFlite par <strong>Copier pour dessiner</strong>. Sans calque, le premier objet en crée un. Les outils :</p><ul><li><strong>Choisir</strong> — touchez un objet pour le modifier ;</li><li><strong>Cercle</strong> — un toucher pour le centre, le rayon à la poignée ; rayon, altitude max., trait et intérieur ;</li><li><strong>Zone</strong> — un toucher par sommet ; <strong>Tracé</strong> <strong>Droit</strong> ou <strong>Courbe</strong> ;</li><li><strong>Ligne</strong> — un toucher par sommet ; <strong>Type</strong> <strong>Ligne</strong>, <strong>FLOT</strong> (avec son <strong>Côté ennemi</strong>, que l’on inverse) ou <strong>Couloir</strong> (avec sa largeur) ;</li><li><strong>Point</strong> — une cible, un DMPI, un point de sortie, une zone de poser ou un autre point ;</li><li><strong>Texte</strong> — <strong>Sans fond</strong> ou sur <strong>Fond blanc</strong> ;</li><li><strong>Orbite</strong> — l’entrée puis la sortie ; largeur, virage, mission, fréquence, altitudes ;</li><li><strong>Boîte</strong> — le début puis la fin de son axe ; longueur, largeur, grille, altitudes ;</li><li><strong>Symbole</strong> — un symbole militaire OTAN : <strong>Camp</strong>, <strong>Style</strong>, <strong>Taille</strong>, le symbole et sa <strong>Désignation</strong> ; pour une unité, aussi <strong>Échelon</strong> et <strong>Formation</strong>.</li></ul><p>Une zone ou une ligne se termine par <strong>Terminer</strong>. Le bouton <strong>Réglages</strong> règle d’avance l’objet à venir, couleur comprise. Un objet choisi se modifie à ses poignées ; sa barre propose <strong>Sommet</strong> (retirer le sommet choisi), <strong>Réglages</strong>, <strong>Copier</strong>, <strong>Suppr.</strong> (avec confirmation) et <strong>OK</strong>. La section <strong>Calques</strong> du panneau liste les calques, à cocher pour les montrer ; × retire un calque, <strong>Retirer tous les calques</strong> les retire tous. Les calques sont gardés dans le navigateur.</p></div>
        <div class="lang-block" data-lang="en"><p><strong>Draw</strong> mode opens a bar at the foot of the map. Its <strong>Layer</strong> button tells you where you draw; tapped, it opens <strong>Draw in</strong>: pick one of your layers, create one with <strong>+ Layer</strong>, or make an editable copy of a CombatFlite layer with <strong>Copy to draw</strong>. With no layer, the first item creates one. The tools:</p><ul><li><strong>Select</strong> — tap an item to edit it;</li><li><strong>Circle</strong> — one tap for the centre, the radius by the handle; radius, max altitude, line and fill;</li><li><strong>Zone</strong> — one tap per vertex; <strong>Shape</strong> <strong>Straight</strong> or <strong>Curve</strong>;</li><li><strong>Line</strong> — one tap per vertex; <strong>Type</strong> <strong>Line</strong>, <strong>FLOT</strong> (with its <strong>Enemy side</strong>, which you flip) or <strong>Corridor</strong> (with its width);</li><li><strong>Point</strong> — a target, a DMPI, an exit point, an LZ, or another point;</li><li><strong>Text</strong> — <strong>No background</strong> or on a <strong>White background</strong>;</li><li><strong>Orbit</strong> — the entry then the exit; width, turn, mission, frequency, altitudes;</li><li><strong>Box</strong> — the start then the end of its axis; length, width, grid, altitudes;</li><li><strong>Symbol</strong> — a NATO military symbol: <strong>Side</strong>, <strong>Style</strong>, <strong>Size</strong>, the symbol and its <strong>Designation</strong>; for a unit, also <strong>Echelon</strong> and <strong>Higher formation</strong>.</li></ul><p>A zone or a line ends with <strong>Finish</strong>. The <strong>Settings</strong> button sets up the coming item in advance, colour included. A selected item is edited by its handles; its bar offers <strong>Vertex</strong> (remove the selected vertex), <strong>Settings</strong>, <strong>Copy</strong>, <strong>Delete</strong> (with confirmation) and <strong>OK</strong>. The panel’s <strong>Layers</strong> section lists the layers, ticked to show them; × removes a layer, <strong>Remove all layers</strong> removes them all. Layers are kept in the browser.</p></div>
      </div>

      <!-- Les calques CombatFlite -->
      <div class="fm-prose">
        <h3 class="lang-block" data-lang="fr">Les calques CombatFlite</h3>
        <h3 class="lang-block" data-lang="en">CombatFlite layers</h3>
        <div class="lang-block" data-lang="fr"><p><strong>Ouvrir ▾ › Ouvrir une route…</strong> lit aussi un fichier CombatFlite <code>.cf</code>. La fenêtre <strong>Calques CombatFlite</strong> en liste les calques, avec leurs objets : cochez ceux à afficher, puis <strong>Afficher</strong>. Si le fichier nomme un théâtre connu, le Route Planner passe sur ce théâtre. Ces calques s’affichent <strong>en lecture seule</strong>. En mode <strong>Lire</strong>, un objet touché montre sa fiche, selon l’objet : nom, rayon d’un cercle, altitudes, fréquence d’une orbite ; un point ou un symbole montre aussi son MGRS et propose <strong>→ Point de référence</strong>. En <strong>Point</strong> ou en <strong>Réf.</strong>, une cible touchée devient un point ou une référence. Un fichier <code>.cf</code> ne touche jamais la route ; un fichier JSON qui porte des calques sans route ajoute ses calques et laisse la route en place.</p></div>
        <div class="lang-block" data-lang="en"><p><strong>Open ▾ › Open a route…</strong> also reads a CombatFlite <code>.cf</code> file. The <strong>CombatFlite layers</strong> window lists its layers, with their items: tick the ones to show, then <strong>Show</strong>. If the file names a known theatre, the Route Planner switches to it. These layers are <strong>read-only</strong>. In <strong>Read</strong> mode, a tapped item shows its card, depending on the item: name, a circle’s radius, altitudes, an orbit’s frequency; a point or a symbol also shows its MGRS and offers <strong>→ Reference point</strong>. In <strong>Waypoint</strong> or <strong>Ref.</strong> mode, a tapped target becomes a waypoint or a reference point. A <code>.cf</code> file never touches the route; a JSON file that carries layers but no route adds its layers and leaves the route as it is.</p></div>
      </div>

      <!-- Figure 2 : ce qui entre, ce qui sort -->
      <div class="fm-schema">
        {RP_FEED_SVG}
        <div class="fm-schema-legend">
          <span class="lang-block" data-lang="fr">Fig. 2 — Ce qui entre dans le Route Planner, et ce qui en sort.</span>
          <span class="lang-block" data-lang="en">Fig. 2 — What goes into the Route Planner, and what comes out.</span>
        </div>
      </div>

      <!-- Fin du panneau, export vers le briefing -->
      <div class="fm-prose">
        <h3 class="lang-block" data-lang="fr">Exporter vers le briefing</h3>
        <h3 class="lang-block" data-lang="en">Export to the briefing</h3>
        <div class="lang-block" data-lang="fr"><p>La section <strong>Route</strong> finit sur le bloc <strong>Ajouter</strong>. Les datacards suivent leurs routes d’elles-mêmes : au Datacard Generator, la liste <strong>Lier à une autre route</strong> de la carte la lie à une route. Le paquet de vol ne s’exporte plus d’ici : c’est le Flight Configurator qui l’exporte.</p><p><strong>Exporter ▾ › Image pour le briefing…</strong> pose sur la carte un <strong>cadre d’export</strong>, <strong>Paysage</strong> ou <strong>Portrait</strong>. Déplacez et zoomez la carte sous le cadre, puis <strong>Exporter</strong> : l’image de la carte reçoit une échelle, une flèche du nord et un cartouche — le nom de la route et son théâtre, le crédit du fond. Dans la suite, elle part au Briefing Generator ; seule, elle s’enregistre en fichier, à importer dans le Briefing Generator. <strong>Annuler</strong> ferme le cadre. Un fond venu d’un autre site peut manquer dans l’image : un message le signale.</p></div>
        <div class="lang-block" data-lang="en"><p>The <strong>Route</strong> section ends on the <strong>Add</strong> block. Datacards follow their routes by themselves: in the Datacard Generator, the card’s <strong>Link to another route</strong> list links it to a route. The flight package is no longer exported from here: the Flight Configurator exports it.</p><p><strong>Export ▾ › Image for the briefing…</strong> lays an <strong>export frame</strong> on the map, <strong>Landscape</strong> or <strong>Portrait</strong>. Pan and zoom the map under the frame, then <strong>Export</strong>: the map image gets a scale, a north arrow and a title strip — the route’s name and theatre, the background’s credit. Within the suite, it goes to the Briefing Generator; on its own, it is saved as a file, to import into the Briefing Generator. <strong>Cancel</strong> closes the frame. A background from another site may be missing from the image: a message says so.</p></div>
      </div>

      <!-- Ouvrir, sauvegarder, Route Tool de DCS -->
      <div class="fm-prose">
        <h3 class="lang-block" data-lang="fr">Ouvrir, sauvegarder, Route Tool de DCS</h3>
        <h3 class="lang-block" data-lang="en">Open, save, DCS Route Tool</h3>
        <div class="lang-block" data-lang="fr"><p>La route est gardée dans le navigateur : elle vous attend à la prochaine ouverture. <strong>Sauvegarder ▾</strong>, en haut, écrit la route sélectionnée ou toutes les routes en fichier JSON, avec leurs points de référence et leurs réglages ; <kbd>Ctrl</kbd>+<kbd>S</kbd> (<kbd>Cmd</kbd>+<kbd>S</kbd> sur Mac) sauvegarde la route sélectionnée. Quand des calques sont présents, la fenêtre de sauvegarde demande ce que le fichier emporte : <strong>La route</strong> et chacun des calques, à cocher. <strong>Ouvrir ▾ › Ouvrir une route…</strong> reconnaît ce qu’on lui donne : une route JSON, qui remplace la route en cours, après confirmation si une route est en cours ; un fichier du Route Tool de DCS ; un fichier CombatFlite.</p><p>Au Route Planner, <strong>Ouvrir ▾ › Importer des routes…</strong> ouvre la même fenêtre que <strong>Ouvrir ▾ › Importer des groupes…</strong> au Flight Configurator : la mission chargée dans HQ, le briefing en cours du Briefing Generator, ou un fichier (paquet de vol <code>.json</code> ou <code>.zip</code>, briefing). Cochez les groupes et, pour chacun, ce qu'il apporte (route, radios, emport, livrée). Un groupe de même nom (majuscules comprises) et de même coalition est complété, sinon il est créé ; une route importée devient une route du Route Planner. Du briefing viennent les groupes, leur nombre d'appareils et le plan radio de leur type ; un appareil que la suite ne connaît pas sous ce nom arrive sans type, à choisir.</p><p>Le <strong>Route Tool</strong> de DCS range toutes les routes d’une carte dans un seul fichier, <code>&lt;théâtre&gt;.lua</code>, dans <code>Saved Games\\DCS\\Config\\RouteToolPresets</code>. Ouvert, ce fichier donne la fenêtre <strong>Ouvrir une route du Route Tool</strong> : choisissez le théâtre, prérempli d’après le nom du fichier, et la route, puis <strong>Ouvrir la route</strong> : elle remplace la route en cours, vide les points de référence et passe sur le théâtre choisi. <strong>Exporter ▾ › Route Tool…</strong> demande le <strong>Nom de la route dans le Route Tool</strong>, puis propose <strong>Ajouter à mon fichier &lt;théâtre&gt;.lua…</strong>, qui vous fait choisir votre fichier et y ajoute la route, en gardant les vôtres, ou <strong>Créer un fichier neuf</strong>, qui ne contient que cette route. Un nom déjà pris est changé, et le message le dit. Copiez ensuite le fichier dans <code>RouteToolPresets</code> : il remplace l’ancien. Le Route Tool n’existe pas pour tous les théâtres — Irak, Afghanistan et Mariannes 1944 en sont privés — et la ligne est alors grisée.</p></div>
        <div class="lang-block" data-lang="en"><p>The route is kept in the browser: it is waiting for you the next time you open the tool. <strong>Save ▾</strong>, at the top, writes the selected route or all the routes to a JSON file, with their reference points and settings; <kbd>Ctrl</kbd>+<kbd>S</kbd> (<kbd>Cmd</kbd>+<kbd>S</kbd> on a Mac) saves the selected route. When layers are present, the save window asks what the file takes: <strong>The route</strong> and each layer, to tick. <strong>Open ▾ › Open a route…</strong> recognises what you give it: a JSON route, which replaces the current route, after confirmation if a route is in progress; a DCS Route Tool file; a CombatFlite file.</p><p>In the Route Planner, <strong>Open ▾ › Import routes…</strong> opens the same window as <strong>Open ▾ › Import groups…</strong> in the Flight Configurator: the mission loaded in HQ, the Briefing Generator's current briefing, or a file (flight package <code>.json</code> or <code>.zip</code>, briefing). Tick the groups and, for each, what it brings (route, radios, loadout, livery). A group with the same name (case included) and coalition is completed, otherwise it is created; an imported route becomes a Route Planner route. A briefing brings its groups, their number of aircraft and the radio plan of their type; an aircraft the suite does not know by that name arrives without a type, to be picked.</p><p>The DCS <strong>Route Tool</strong> keeps all routes of a map in one file, <code>&lt;theatre&gt;.lua</code>, in <code>Saved Games\\DCS\\Config\\RouteToolPresets</code>. Opened, that file brings up the <strong>Open a Route Tool route</strong> window: pick the theatre, pre-filled from the file name, and the route, then <strong>Open route</strong>: it replaces the current route, clears the reference points, and switches to the chosen theatre. <strong>Export ▾ › Route Tool…</strong> asks for the <strong>Route name in the Route Tool</strong>, then offers <strong>Add to my &lt;theatre&gt;.lua file…</strong>, which has you pick your file and adds the route to it, keeping yours, or <strong>Create a new file</strong>, which holds only this route. A name already taken is changed, and the message says so. Then copy the file into <code>RouteToolPresets</code>: it replaces the old one. The Route Tool does not exist for every theatre — Iraq, Afghanistan and Mariana Islands WWII lack it — and the row is then greyed out.</p></div>
      </div>

      <!-- Sur tablette et téléphone -->
      <div class="fm-prose">
        <h3 class="lang-block" data-lang="fr">Sur tablette et téléphone</h3>
        <h3 class="lang-block" data-lang="en">On tablets and phones</h3>
        <div class="lang-block" data-lang="fr"><p>À partir de 1 100 px de large, le panneau est à gauche et la carte à droite. En dessous, quelle que soit l’orientation, la carte reste fixe au-dessus du panneau, et seul le panneau défile. Entre les deux, une poignée se glisse pour agrandir ou réduire la carte ; deux touchers la remettent à sa taille d’origine. La hauteur choisie est gardée, une pour le portrait, une pour le paysage. Quand le clavier de l’écran s’ouvre sur un champ du panneau, la carte se réduit le temps de la saisie.</p></div>
        <div class="lang-block" data-lang="en"><p>From 1,100 px wide, the panel sits on the left and the map on the right. Below that, whatever the orientation, the map stays fixed above the panel, and only the panel scrolls. Between the two, a handle drags to enlarge or shrink the map; a double-tap restores its original size. The chosen height is kept, one for portrait, one for landscape. When the on-screen keyboard opens on a panel field, the map shrinks while you type.</p></div>
      </div>

      <!-- Le cap de la règle de l’éditeur -->
      <div class="fm-callout warn">
        <div class="lang-block" data-lang="fr">Le cap de la règle de l’éditeur — La règle de l’éditeur de mission de DCS mesure un <strong>cap grille</strong> : il se rapporte au nord de la grille de la carte, et n’est ni vrai ni magnétique. Il diffère donc du cap du Route Planner, jusqu’à une dizaine de degrés sur la carte Allemagne (guerre froide). Pour comparer, prenez le cap <strong>Vrai</strong> du Route Planner. L’écart qui reste est la convergence de la grille : nulle sur le méridien central de la carte, de plus en plus forte à mesure qu’on s’en éloigne.</div>
        <div class="lang-block" data-lang="en">The editor ruler’s heading — The DCS mission editor’s ruler measures a <strong>grid heading</strong>: it refers to the map grid’s north, and is neither true nor magnetic. It therefore differs from the Route Planner’s heading, by up to about ten degrees on the Cold War Germany map. To compare, take the Route Planner’s <strong>True</strong> heading. The gap that remains is the grid convergence: zero on the map’s central meridian, growing as you move away from it.</div>
      </div>

      <!-- Hors ligne -->
      <div class="fm-callout note">
        <div class="lang-block" data-lang="fr">Hors ligne — Sans connexion, les fonds de carte et les fiches ne se chargent pas : la carte n’affiche plus que sa grille, avec le bandeau <strong>Fond indisponible — grille seule</strong> ; le choix du <strong>Fond</strong> ne change pas. La route, les références, la navigation et les calques restent utilisables.</div>
        <div class="lang-block" data-lang="en">Offline — Without a connection, base maps and chart sheets do not load: the map shows only its grid, with the <strong>Map unavailable — grid only</strong> banner; the <strong>Base map</strong> choice does not change. The route, reference points, navigation, and layers stay usable.</div>
      </div>

    </div><!-- /fm-chapter -->
  </section><!-- /page-rp -->


</main><!-- /fm-root -->

{ZOOM_HTML}

<script>
/* =============================================
   DCS FIELD MANUAL — JS
   Routing · i18n · Thème
   ============================================= */

// ── i18n ──────────────────────────────────────
var I18N = {{
  fr: {{
    'brand.name':       'Field Manual',
    'brand.sub':        '░ MANUEL OPÉRATIONNEL',
    'index.title':      'Modules documentés',
    'index.badge.active': 'Manuel',
    'index.hq.desc':    'Wing Command Center — configuration escadre',
    'index.fc.desc':    'Un groupe prêt à appliquer : radios, emport, livrée',
    'index.bg.desc':    'Générateur de briefings multi-sections',
    'index.rs.desc':    'Compositeur photo-renseignement canvas',
    'index.rp.desc':    "Planification d\u2019itin\u00e9raires",
    'index.dg.desc':    'Datacards de vol d’une page',
    'index.soon':       'À VENIR',
    'btn.back':         '◄ Index',
    'rs.hero.title':    'Recon Station',
    'rs.hero.sub':      'Compositeur photo-renseignement',
    'rs.whatfor.title': 'À quoi ça sert',
    'rs.steps.title':   'Prise en main',
    'rs.schema.legend': 'Fig. 1 — Pipeline de composition et ordre de rendu des calques',
    'hq.hero.title':    'HQ — Wing Command Center',
    'hq.hero.sub':      'Configuration escadre centralisée',
    'fc.hero.title':    'Flight Configurator',
    'fc.hero.sub':      'Un groupe prêt à appliquer : radios, emport, livrée',
    'bg.hero.title':    'Briefing Generator',
    'bg.hero.sub':      'Générateur de briefings multi-sections',
    'dg.hero.title':    'Datacard Generator',
    'dg.hero.sub':      'Datacards de vol pour le kneeboard',
    'rp.hero.title':    'Route Planner',
    'rp.hero.sub':      'Routes, navigation et cartes de mission',
    'zoom.open':        'Agrandir',
    'zoom.close':       'Fermer',
    'zoom.in':          'Zoomer',
    'zoom.out':         'Dézoomer',
    'zoom.fit':         'Ajuster',
    'stub.coming':      'Chapitre en préparation'
  }},
  en: {{
    'brand.name':       'Field Manual',
    'brand.sub':        '░ OPERATIONAL MANUAL',
    'index.title':      'Documented Modules',
    'index.badge.active': 'Manual',
    'index.hq.desc':    'Wing Command Center — wing configuration',
    'index.fc.desc':    'A group ready to apply: radios, loadout, livery',
    'index.bg.desc':    'Multi-section briefing generator',
    'index.rs.desc':    'Canvas photo-intelligence composer',
    'index.rp.desc':    'Route planning',
    'index.dg.desc':    'One-page flight datacards',
    'index.soon':       'COMING',
    'btn.back':         '◄ Index',
    'rs.hero.title':    'Recon Station',
    'rs.hero.sub':      'Photo-intelligence composer',
    'rs.whatfor.title': 'What it does',
    'rs.steps.title':   'Getting started',
    'rs.schema.legend': 'Fig. 1 — Composition pipeline and layer render order',
    'hq.hero.title':    'HQ — Wing Command Center',
    'hq.hero.sub':      'Centralised wing configuration',
    'fc.hero.title':    'Flight Configurator',
    'fc.hero.sub':      'A group ready to apply: radios, loadout, livery',
    'bg.hero.title':    'Briefing Generator',
    'bg.hero.sub':      'Multi-section briefing generator',
    'dg.hero.title':    'Datacard Generator',
    'dg.hero.sub':      'Flight datacards for the kneeboard',
    'rp.hero.title':    'Route Planner',
    'rp.hero.sub':      'Routes, navigation and mission maps',
    'zoom.open':        'Enlarge',
    'zoom.close':       'Close',
    'zoom.in':          'Zoom in',
    'zoom.out':         'Zoom out',
    'zoom.fit':         'Fit',
    'stub.coming':      'Chapter in preparation'
  }}
}};

var CURRENT_LANG = 'fr';
var KEY_LANG  = 'lang_v1';
var KEY_THEME = 'theme_v1';
var KEY_STATE = 'fm_state_v1';

function t(key) {{
  var d = I18N[CURRENT_LANG] || I18N['fr'];
  return d[key] !== undefined ? d[key] : (I18N['fr'][key] || key);
}}

function applyI18n() {{
  document.querySelectorAll('[data-i18n]').forEach(function(el) {{
    el.textContent = t(el.getAttribute('data-i18n'));
  }});
  document.querySelectorAll('[data-i18n-title]').forEach(function(el) {{
    el.title = t(el.getAttribute('data-i18n-title'));
  }});
  // Les titres des schémas (aria-label) suivent la langue
  document.querySelectorAll('svg[data-aria-fr]').forEach(function(el) {{
    el.setAttribute('aria-label', el.getAttribute(CURRENT_LANG === 'en' ? 'data-aria-en' : 'data-aria-fr'));
  }});
  // Tampons "À VENIR / COMING" sur les plaques soon
  document.querySelectorAll('.fm-soon-stamp').forEach(function(el) {{
    el.textContent = t('index.soon');
  }});
  // Lang attribute sur body
  document.body.lang = CURRENT_LANG;
  document.documentElement.lang = CURRENT_LANG;
  // Drapeau
  updateFlag();
  // Libellés du zoom (images et schémas)
  fmZoomRefresh();
}}

// ── Drapeaux SVG inline ───────────────────────
var FLAG_FR = '<svg viewBox="0 0 20 14" width="22" height="15" xmlns="http://www.w3.org/2000/svg"><rect width="7" height="14" fill="#002395"/><rect x="7" width="6" height="14" fill="#fff"/><rect x="13" width="7" height="14" fill="#ED2939"/></svg>';
var FLAG_EN = '<svg viewBox="0 0 20 14" width="22" height="15" xmlns="http://www.w3.org/2000/svg"><rect width="20" height="14" fill="#012169"/><path d="M0,0 L20,14 M20,0 L0,14" stroke="#fff" stroke-width="2.8"/><path d="M0,0 L20,14 M20,0 L0,14" stroke="#C8102E" stroke-width="1.6"/><rect x="8" width="4" height="14" fill="#fff"/><rect y="5" width="20" height="4" fill="#fff"/><rect x="9" width="2" height="14" fill="#C8102E"/><rect y="6" width="20" height="2" fill="#C8102E"/></svg>';

function updateFlag() {{
  var btn = document.getElementById('btn-lang');
  if (!btn) return;
  // On montre le drapeau de la langue VERS laquelle on bascule
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

// ── Thème ─────────────────────────────────────
function initTheme() {{
  try {{
    var stored = localStorage.getItem(KEY_THEME);
    if (stored) document.body.setAttribute('data-theme', stored);
  }} catch(e) {{}}
  if (!document.body.getAttribute('data-theme')) {{
    document.body.setAttribute('data-theme', 'cw-nato');
  }}
}}

// ── Routing hash ──────────────────────────────
var PAGES = ['index', 'rs', 'hq', 'fc', 'bg', 'dg', 'rp'];

function showPage(id) {{
  if (PAGES.indexOf(id) === -1) id = 'index';
  PAGES.forEach(function(pid) {{
    var el = document.getElementById('page-' + pid);
    if (!el) return;
    if (pid === id) {{
      el.classList.remove('hidden');
    }} else {{
      el.classList.add('hidden');
    }}
  }});
  var root = document.getElementById('fm-root');
  if (root) root.scrollTop = 0;
  // Persister la dernière page
  try {{ localStorage.setItem(KEY_STATE, JSON.stringify({{page: id}})); }} catch(e) {{}}
}}

function navigate(id) {{
  location.hash = '#' + id;
}}

function onHashChange() {{
  var hash = location.hash.replace('#', '') || 'index';
  showPage(hash);
}}

{ZOOM_JS}

// ── Init ──────────────────────────────────────
function init() {{
  initTheme();
  initLang();
  initZoom();
  applyI18n();

  document.getElementById('btn-lang').addEventListener('click', toggleLang);

  window.addEventListener('hashchange', onHashChange);
  onHashChange();
}}

document.addEventListener('DOMContentLoaded', init);
</script>
</body>
</html>
"""

# ── Écriture ─────────────────────────────────────────────────────────────────────

os.makedirs(os.path.join(HERE, 'dist'), exist_ok=True)
OUTPUT_PATH = os.path.join(HERE, 'dist', 'dcs_field_manual.html')
with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
    f.write(HTML)

size_kb = os.path.getsize(OUTPUT_PATH) // 1024
print(f'\n[OK] dcs_field_manual.html écrit ({size_kb} Ko)')

# ── Vérifications ────────────────────────────────────────────────────────────────

with open(OUTPUT_PATH, 'r', encoding='utf-8') as f:
    src = f.read()

# Un [MISSING] ou un [FAIL] fait sortir le build en 1, une fois tous les contrôles écrits (comme node --check).
CHECK_ERRORS = []

def grep_ok(pattern, label):
    found = pattern in src
    status = 'OK' if found else 'MISSING'
    print(f'  [{status}] {label}')
    if not found:
        CHECK_ERRORS.append('MISSING ' + label)
    return found

def grep_absent(pattern, label):
    found = pattern in src
    status = 'FAIL' if found else 'OK'
    print(f'  [{status}] ABSENT: {label}')
    if found:
        CHECK_ERRORS.append('FAIL ABSENT ' + label)
    return not found

print('\n-- Vérifications --')
grep_ok('body[data-theme="cw-nato"]',     '4 thèmes présents : cw-nato')
grep_ok('body[data-theme="cw-soviet"]',   'cw-soviet')
grep_ok('body[data-theme="modern-nato"]', 'modern-nato')
grep_ok('body[data-theme="modern-east"]', 'modern-east')
grep_ok('id="page-index"',  'page-index présent')
grep_ok('id="page-rs"',     'page-rs présent')
grep_ok('id="page-hq"',     'page-hq présent')
grep_ok('id="page-bg"',     'page-bg présent')
grep_ok('id="page-dg"',     'page-dg présent')
grep_ok('id="page-fc"',     'page-fc présent')
grep_ok('Goldwolf',          'crédit de Goldwolf')
grep_ok('--fm-accent:', '--fm-accent présent')
grep_ok('--chapter-accent: #C95A9C', '--chapter-accent RS')
grep_ok('--chapter-accent: #4FB286', '--chapter-accent HQ')
grep_ok('--chapter-accent: #c0892a', '--chapter-accent BG')
grep_ok('--chapter-accent: #4f7a8e', '--chapter-accent DG')
grep_ok('--chapter-accent: #D0784A', '--chapter-accent FC')
grep_ok('class="toolbar"',  'toolbar présent')
grep_ok('id="fm-zoom"',     'fenêtre de zoom présente')
grep_ok('role="dialog" aria-modal="true"', 'fenêtre de zoom : role=dialog, aria-modal')
grep_ok('--accent-ink:',    '--accent-ink présent')
grep_ok('id="dgf"',         'figure 2 DG : marqueur propre')
grep_ok('viewBox="0 0 720 425"', 'schéma BG refait (720 × 425)')
grep_absent('MT_onModuleSave', 'MT_onModuleSave absent')
grep_absent('app-header',      'app-header absent')
grep_absent('4th VEAW',        '4th VEAW absent')
grep_absent('KHR-26',          'KHR-26 absent')
# Les deux formats du Briefing Generator s'appellent Standard et Avancé, partout dans le manuel
for _old in ('brief simplifié', 'brief complet', 'quick brief', 'full brief', 'simplifiée', 'quick-brief'):
    grep_absent(_old, 'ancien nom de format « ' + _old + ' » absent')

# Vérifier les paires lang-block
fr_count = src.count('data-lang="fr"')
en_count = src.count('data-lang="en"')
status = 'OK' if fr_count == en_count else 'FAIL'
print(f'  [{status}] paires lang-block : fr={fr_count} en={en_count}')
if fr_count != en_count:
    CHECK_ERRORS.append('FAIL paires lang-block')

# ── node --check sur TOUS les scripts inline ──────────────────────────────────────

print('\n-- node --check scripts inline --')
src_nocomments = re.sub(r'<!--.*?-->', '', src, flags=re.S)
scripts = re.findall(r'<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>', src_nocomments, flags=re.S)
print(f'  {len(scripts)} script(s) inline trouvé(s)')
all_ok = True
for i, script in enumerate(scripts):
    with tempfile.NamedTemporaryFile(suffix='.js', mode='w', encoding='utf-8', delete=False) as tmp:
        tmp.write(script)
        tmp_path = tmp.name
    result = subprocess.run(['node', '--check', tmp_path], capture_output=True, text=True)
    os.unlink(tmp_path)
    if result.returncode != 0:
        print(f'  [FAIL] Script #{i+1} : {result.stderr.strip()[:200]}')
        all_ok = False
    else:
        print(f'  [OK] Script #{i+1} ({len(script)//1024} Ko) — node --check PASS')

if not all_ok:
    CHECK_ERRORS.append('node --check')

if not CHECK_ERRORS:
    print('\n[BUILD DONE]')
else:
    print('\n[BUILD ÉCHEC] ' + str(len(CHECK_ERRORS)) + ' contrôle(s) en échec : ' + ' ; '.join(CHECK_ERRORS), file=sys.stderr)
    sys.exit(1)
