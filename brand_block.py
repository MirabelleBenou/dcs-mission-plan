#!/usr/bin/env python3
"""Bloc « MARQUE » : l'insigne de la famille Squadron Ready Room, lu une fois dans brand/ et donné aux huit builds.

Les fichiers de brand/ sont des copies, à l'octet, des fichiers maîtres de la famille (à ne pas modifier ici). Les pages restent des fichiers uniques : chaque
image devient une URL data: au build, aucune requête réseau n'est ajoutée.

Ce que le bloc donne :
  data_url(nom)              l'URL data: d'un fichier de brand/ (data:image/svg+xml;base64,… ; data:image/x-icon;base64,… ; data:image/png;base64,…)
  tab_icons_html(touch)      les liens d'icône d'onglet : favicon.ico, favicon.svg, et avec touch=True apple-touch-icon.png (le shell seul)
  add_tab_icons(html, touch) les liens posés juste après </title> (une seule fois, sinon le build s'arrête)
  INSIGNE_MP, INSIGNE_RR, PICTO   les URL data: de l'insigne de Mission Plan, de l'insigne générique (Ready Room) et du pictogramme
  LEGACY_WG_LOGO_DATAURL     l'ancien logo « WG » par défaut du Wing (voir plus bas)

Usage (par les builds) : from brand_block import add_tab_icons, INSIGNE_RR ; html = add_tab_icons(html)
"""

import base64
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
BRAND_DIR = os.path.join(HERE, 'brand')

_MIME = {'.svg': 'image/svg+xml', '.ico': 'image/x-icon', '.png': 'image/png'}


def data_url(name):
    """L'URL data: (base64) du fichier brand/<name>."""
    with open(os.path.join(BRAND_DIR, name), 'rb') as f:
        raw = f.read()
    mime = _MIME[os.path.splitext(name)[1]]
    return 'data:' + mime + ';base64,' + base64.b64encode(raw).decode('ascii')


INSIGNE_MP = data_url('insigne-mission-plan.svg')
INSIGNE_RR = data_url('insigne-ready-room.svg')
PICTO = data_url('pictogramme.svg')

# L'ancien logo « WG » par défaut du Wing (HQ et Briefing Generator) : l'ancien défaut, lu comme le nouveau (insigne-ready-room.svg).
# Un wing_config_v1 qui porte encore ce logo, à l'octet, est lu avec le nouveau ; le stockage n'est réécrit que par un geste de la personne.
LEGACY_WG_LOGO_DATAURL = (
    'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNTYgMjU2Ij4KICA8Y2lyY2xlIGN4PSIxMjgiIGN5PSIxMjgiIHI9IjExNSIgZmlsbD0iI2Q0YzU5OCIvPgogIDxjaXJjbGUgY3g9IjEyOCIgY3k9IjEyOCIgcj0iMTE1IiBmaWxsPSJub25lIiBzdHJva2U9IiNhODk0NWUiIHN0cm9rZS13aWR0aD0iMTQiLz4KICA8Y2lyY2xlIGN4PSIxMjgiIGN5PSIxMjgiIHI9IjkwIiBmaWxsPSJub25lIiBzdHJva2U9IiNhODk0NWUiIHN0cm9rZS13aWR0aD0iNSIvPgogIDxjaXJjbGUgY3g9IjEyOCIgY3k9IjEyOCIgcj0iNzAiIGZpbGw9Im5vbmUiIHN0cm9rZT0iI2E4OTQ1ZSIgc3Ryb2tlLXdpZHRoPSIyIi8+CiAgPHRleHQgeD0iMTI4IiB5PSIxNTgiIHRleHQtYW5jaG9yPSJtaWRkbGUiCiAgICAgICAgZm9udC1mYW1pbHk9IkFyaWFsIEJsYWNrLCBBcmlhbCwgc2Fucy1zZXJpZiIKICAgICAgICBmb250LXdlaWdodD0iOTAwIiBmb250LXNpemU9Ijg2IiBmaWxsPSIjMmEzMDM4IiBsZXR0ZXItc3BhY2luZz0iLTMiPldHPC90ZXh0Pgo8L3N2Zz4='
)


def tab_icons_html(touch=False):
    """Les liens d'icône d'onglet : le .ico (16, 32, 48), puis le .svg ; avec touch=True, l'apple-touch-icon (180) en plus (le shell seul : c'est la page qu'on épingle à l'écran d'accueil)."""
    out = ('<link rel="icon" type="image/x-icon" sizes="16x16 32x32 48x48" href="' + data_url('favicon.ico') + '">\n'
           '<link rel="icon" type="image/svg+xml" href="' + data_url('favicon.svg') + '">\n')
    if touch:
        out += '<link rel="apple-touch-icon" sizes="180x180" href="' + data_url('apple-touch-icon.png') + '">\n'
    return out


_TITLE_RX = re.compile(r'<title>[^<]*</title>\n')


def add_tab_icons(html, touch=False):
    """Pose les liens juste après l'élément <title> de l'en-tête (le premier du fichier) ; le build s'arrête s'il n'y en a pas, ou si les liens y sont déjà."""
    head_end = html.find('</head>')
    if 'rel="icon"' in html[:head_end]:
        raise SystemExit('[ERREUR] les icônes d\'onglet figurent déjà dans l\'en-tête — build arrêté')
    m = _TITLE_RX.search(html)
    if not m or m.start() > head_end:
        raise SystemExit('[ERREUR] <title> introuvable dans l\'en-tête, les icônes d\'onglet ne peuvent pas être posées — build arrêté')
    return html[:m.end()] + tab_icons_html(touch) + html[m.end():]
