#!/usr/bin/env python3
"""
build_mission_plan.py — DCS Mission Plan shell v1.0
Produit dist/dcs_mission_plan.html (fichier autonome, single-file, offline).

Usage : python3 build_mission_plan.py
Sortie : ./dist/dcs_mission_plan.html

Sources modules actifs (produits par les six autres build_*.py, dans ./dist/) :
  dist/dcs_hq.html
  dist/dcs_briefing_generator.html
  dist/dcs_datacard_generator.html
  dist/dcs_recon_station.html
  dist/dcs_route_planner.html
  dist/dcs_field_manual.html

Sources images (à placer dans ./tiles/) :
  tiles/hq.webp  tiles/bg.webp  tiles/rs.webp  tiles/fm.webp  tiles/rp.webp  tiles/kg.webp
"""

import base64
import os
import sys

# ── Configuration ──────────────────────────────────────────────────────────────
OUT_FILE = 'dist/dcs_mission_plan.html'

# status : 'active' = module embarqué ; 'soon' = carte voilée uniquement
# Ordre des modules actifs = ordre des cartes de la landing. RÈGLE : Field Manual reste TOUJOURS le dernier
# module actif ; tout module activé plus tard s'insère avant lui.
MODULES = [
    {'id': 'hq', 'status': 'active', 'src': 'dist/dcs_hq.html',                        'tile': 'tiles/hq.webp'},
    {'id': 'bg', 'status': 'active', 'src': 'dist/dcs_briefing_generator.html',       'tile': 'tiles/bg.webp'},
    {'id': 'dg', 'status': 'active', 'src': 'dist/dcs_datacard_generator.html',        'tile': 'tiles/kg.webp'},
    {'id': 'rp', 'status': 'active', 'src': 'dist/dcs_route_planner.html',             'tile': 'tiles/rp.webp'},
    {'id': 'rs', 'status': 'active', 'src': 'dist/dcs_recon_station.html',             'tile': 'tiles/rs.webp'},
    {'id': 'fm', 'status': 'active', 'src': 'dist/dcs_field_manual.html',              'tile': 'tiles/fm.webp'},
]

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def encode_file_b64(path):
    abs_path = os.path.join(SCRIPT_DIR, path)
    if not os.path.isfile(abs_path):
        raise SystemExit(f"[ERREUR] Entrée manquante : {abs_path}")
    with open(abs_path, 'rb') as f:
        return base64.b64encode(f.read()).decode('ascii')


def encode_module_b64(path):
    abs_path = os.path.join(SCRIPT_DIR, path)
    if not os.path.isfile(abs_path):
        raise SystemExit(f"[ERREUR] Entrée manquante : {abs_path} (lancer d'abord les six builds de modules)")
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
    """Encode les 4 tuiles (active + soon)."""
    uris = {}
    for mod in modules:
        b64 = encode_file_b64(mod['tile'])
        if b64 is None:
            print(f'  [WARN] Image tuile introuvable : {mod["tile"]} — placeholder utilisé', file=sys.stderr)
            uris[mod['id']] = ''
        else:
            uris[mod['id']] = f'data:image/webp;base64,{b64}'
            print(f'  [OK] Tuile {mod["id"]} — {len(b64)//1024} Ko base64')
    return uris


def build_html(module_html_js, tile_uris):
    tile_hq = tile_uris.get('hq', '')
    tile_bg = tile_uris.get('bg', '')
    tile_rs = tile_uris.get('rs', '')
    tile_fm = tile_uris.get('fm', '')
    tile_rp = tile_uris.get('rp', '')
    tile_dg = tile_uris.get('dg', '')

    return f'''<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>DCS Mission Plan</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Saira+Stencil+One&family=Oswald:wght@400;500;600;700&family=Special+Elite&family=Barlow+Condensed:wght@400;500;600&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet">
<style>
/* ============================================================
   DCS MISSION PLAN — DA v4 (shell)
   Landing « Mur de situation » — 4 thèmes
   ============================================================ */
:root{{
  --paper:#d8c9a5; --paper-edge:#8a7a52; --ink:#1f1c16; --ink-2:#463f30;
  --accent:#a98a4e; --olive:#4a5230; --stamp:#a83524; --amber:#c0892a;
  --board:#2a2417; --board-2:#1a1610; --lamp:rgba(255,228,168,.22);
  --line:rgba(192,137,42,.30); --grain:.08; --scan:0; --rot:-2.6deg; --rad:2px;
  --f-disp:'Special Elite','Courier New',monospace;
  --f-sten:'Saira Stencil One','Oswald',sans-serif;
  --f-ui:'Oswald','Arial Narrow',sans-serif;
  --f-body:'Barlow Condensed',sans-serif;
  --f-mono:'JetBrains Mono',monospace;
  --a-hq:#4FB286; --a-bg:#c0892a; --a-rp:#7ac97a; --a-dg:#8fb0c0; --a-rs:#c95a9c; --a-fm:#7E8FA6;
}}
[data-theme="cw-nato"]{{ --paper:#d8c9a5; --paper-edge:#8a7a52; --ink:#1f1c16; --ink-2:#463f30;
  --accent:#a98a4e; --olive:#4a5230; --stamp:#a83524; --amber:#c0892a;
  --board:#2a2417; --board-2:#1a1610; --lamp:rgba(255,228,168,.22);
  --line:rgba(192,137,42,.30); --grain:.08; --scan:0; --rot:-2.6deg; --rad:2px; }}
[data-theme="cw-soviet"]{{ --paper:#d8c479; --paper-edge:#8a7a30; --ink:#1f1c16; --ink-2:#463f30;
  --accent:#c9b35c; --olive:#2a3a5a; --stamp:#841e1e; --amber:#d8b24a;
  --board:#231d12; --board-2:#15110a; --lamp:rgba(255,224,150,.20);
  --line:rgba(232,214,144,.28); --grain:.09; --scan:0; --rot:-4deg; --rad:1px; }}
[data-theme="modern-nato"]{{ --paper:#e8e3d8; --paper-edge:#948c7c; --ink:#15181c; --ink-2:#3a4048;
  --accent:#7a8a98; --olive:#2a3038; --stamp:#1a1a1a; --amber:#5c6b7a;
  --board:#10141a; --board-2:#080b0f; --lamp:rgba(170,200,225,.14);
  --line:rgba(122,138,152,.30); --grain:.03; --scan:.06; --rot:-.8deg; --rad:6px; }}
[data-theme="modern-east"]{{ --paper:#cdc6b8; --paper-edge:#7a7466; --ink:#1a1610; --ink-2:#3d3024;
  --accent:#8a7c5e; --olive:#3d3024; --stamp:#7a2424; --amber:#a98a4e;
  --board:#16110b; --board-2:#0c0805; --lamp:rgba(220,190,150,.14);
  --line:rgba(160,120,80,.26); --grain:.05; --scan:.04; --rot:-1.4deg; --rad:4px; }}

*{{box-sizing:border-box;margin:0;padding:0;}}
html,body{{height:100%;}}
body{{font-family:var(--f-body); background:var(--board-2); color:var(--paper); min-height:100vh; overflow-x:hidden; transition:background .5s ease;}}
.app{{position:relative; z-index:3; min-height:100vh; display:flex; flex-direction:column;}}

/* ===== RAIL ===== */
.rail{{display:flex; align-items:center; gap:14px; flex-wrap:wrap; padding:11px 22px; border-bottom:1px solid var(--line);
  position:relative; z-index:6; background:linear-gradient(180deg, rgba(0,0,0,.6), rgba(0,0,0,.18)); backdrop-filter:blur(2px);}}
.plate{{display:flex; align-items:baseline; gap:9px; padding:5px 11px; border:1px solid var(--line); border-radius:var(--rad);
  background:linear-gradient(180deg, rgba(255,255,255,.06), rgba(0,0,0,.3));}}
.plate .mark{{font-family:var(--f-sten); font-size:16px; letter-spacing:.05em; color:var(--amber);}}
.plate .sub{{font-family:var(--f-mono); font-size:9px; letter-spacing:.24em; color:var(--accent); text-transform:uppercase;}}
.rail .spacer{{flex:1;}}
.ctrl{{display:flex; align-items:center; gap:8px;}}
.seg{{display:inline-flex; border:1px solid var(--line); border-radius:var(--rad); overflow:hidden;}}
.seg button{{font-family:var(--f-ui); font-size:11.5px; letter-spacing:.06em; text-transform:uppercase; background:rgba(0,0,0,.4);
  color:var(--accent); border:none; padding:7px 13px; cursor:pointer;}}
.seg button + button{{border-left:1px solid var(--line);}}
.seg button.on{{background:var(--amber); color:#15120c;}}
.theme-sel{{font-family:var(--f-ui); font-size:12px; letter-spacing:.05em; text-transform:uppercase; background:rgba(0,0,0,.45);
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
  font-family: var(--f-ui); font-size: 10px; letter-spacing: 1.8px; text-transform: uppercase;
  color: var(--accent); padding: 8px 14px 6px; border-bottom: 1px solid var(--line); margin-bottom: 2px;
}}
.tbm-opt {{
  position: relative; display: flex; align-items: center; gap: 10px; min-height: 44px; padding: 0 16px 0 18px;
  font-family: var(--f-ui); font-size: 13px; letter-spacing: 1.3px; text-transform: uppercase;
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

.flag{{font-size:15px; background:rgba(0,0,0,.45); border:1px solid var(--line); width:38px; height:34px; border-radius:var(--rad); cursor:pointer; color:var(--amber);}}
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

.wall-head{{position:relative; z-index:2; max-width:1200px; margin:0 auto 22px; width:100%; display:flex; align-items:flex-end; gap:20px; flex-wrap:wrap;}}
.tab{{position:relative; background:var(--paper); color:var(--ink); padding:13px 22px 15px; border-radius:6px 6px 0 0;
  box-shadow:0 10px 26px rgba(0,0,0,.5); transform:rotate(-1deg); border:1px solid var(--paper-edge); border-bottom:none;}}
.tab .ribbon{{font-family:var(--f-mono); font-size:9px; letter-spacing:.26em; color:var(--ink-2); text-transform:uppercase;}}
.tab h1{{font-family:var(--f-sten); font-size:clamp(28px,4.8vw,48px); line-height:.9; letter-spacing:.02em; color:var(--ink); margin-top:4px;}}
.tab h1 .x{{color:var(--stamp);}}
.note{{display:flex; border:1px solid var(--line); border-radius:var(--rad); overflow:hidden; background:rgba(0,0,0,.32); transform:rotate(.6deg);}}
.note .cell{{padding:8px 13px; border-right:1px solid var(--line);}} .note .cell:last-child{{border-right:none;}}
.note .k{{font-family:var(--f-mono); font-size:9px; letter-spacing:.18em; color:var(--accent); text-transform:uppercase; display:block;}}
.note .v{{font-family:var(--f-ui); font-size:13px; color:var(--amber);}}

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
.shot .tagchip{{position:absolute; top:9px; left:9px; font-family:var(--f-mono); font-size:9px; letter-spacing:.14em; text-transform:uppercase;
  color:#f3ecd9; background:rgba(0,0,0,.6); padding:3px 8px; border:1px solid rgba(255,255,255,.18);}}
.caption{{padding:11px 8px 13px; color:var(--ink);}}
.cap-row{{display:flex; align-items:center; gap:9px;}}
.logo{{font-family:var(--f-mono); font-weight:700; font-size:12px; color:#15120c; padding:4px 7px; border-radius:3px; letter-spacing:.05em;}}
.ptitle{{font-family:var(--f-ui); font-size:18px; font-weight:600; color:var(--ink);}}
.pver{{margin-left:auto; font-family:var(--f-mono); font-size:10px; color:var(--ink-2); border:1px solid var(--paper-edge); padding:1px 6px; border-radius:2px;}}
.pdesc{{font-family:var(--f-body); font-size:14px; color:var(--ink-2); line-height:1.4; margin-top:6px;}}
.pstatus{{display:flex; align-items:center; gap:7px; margin-top:8px; font-family:var(--f-mono); font-size:10px; letter-spacing:.12em; text-transform:uppercase; color:var(--olive);}}
.pstatus .dot{{width:7px; height:7px; border-radius:50%; background:#4f8a3a; box-shadow:0 0 8px #4f8a3a;}}

/* ── Cartes ACTIVES (dossiers ouverts) : BG + Recon, traitement identique ── */
.print.active{{cursor:pointer;}}
.print.active .shot{{height:280px; cursor:pointer;}}
#card-hq .shot{{background-image:url("{tile_hq}");}}
#card-hq::before{{background:radial-gradient(circle at 12% 8%, rgba(96,64,30,.5), transparent 14%);}}
#card-bg .shot{{background-image:url("{tile_bg}");}}
#card-rs .shot{{background-image:url("{tile_rs}");}}
#card-fm .shot{{background-image:url("{tile_fm}");}}
#card-fm::before{{background:radial-gradient(circle at 90% 10%, rgba(96,64,30,.5), transparent 14%);}}
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
.active-row .print[id="card-fm"]{{transform:rotate(-1.4deg); transition:transform .4s cubic-bezier(.2,.75,.2,1), box-shadow .4s;}}
.print.active:hover{{transform:rotate(0) translateY(-7px); cursor:pointer; box-shadow:0 30px 64px rgba(0,0,0,.6), 0 0 0 2px var(--card-accent);}}
.active-row .print[id="card-hq"]:hover{{transform:rotate(-0.7deg) translateY(-7px);}}
.active-row .print[id="card-bg"]:hover{{transform:rotate(0.3deg) translateY(-7px);}}
.active-row .print[id="card-dg"]:hover{{transform:rotate(0.6deg) translateY(-7px);}}
.active-row .print[id="card-rp"]:hover{{transform:rotate(-0.2deg) translateY(-7px);}}
.active-row .print[id="card-rs"]:hover{{transform:rotate(-0.4deg) translateY(-7px);}}
.active-row .print[id="card-fm"]:hover{{transform:rotate(-0.5deg) translateY(-7px);}}
.cta{{margin:2px 8px 12px; display:inline-block; font-family:var(--f-ui); font-size:12.5px; letter-spacing:.08em; text-transform:uppercase;
  color:#15120c; background:var(--card-accent); border:1px solid var(--paper-edge); padding:9px 15px; border-radius:var(--rad);}}
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
  border:3px double var(--stamp); padding:9px 17px; font-size:19px; letter-spacing:.16em; text-transform:uppercase; opacity:.7; background:rgba(0,0,0,.14); border-radius:var(--rad);}}
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
  font-family:var(--f-disp); font-size:14px; letter-spacing:.16em; text-transform:uppercase; color:var(--stamp);
  border:2px double var(--stamp); padding:8px 14px; border-radius:2px;}}
[data-theme="modern-nato"] .props .imprint{{color:#8e9aa6; border-color:#5f6b76;}}
[data-theme="modern-east"] .props .imprint{{color:#a4756c; border-color:#79554e;}}
.props .pin.s1{{position:absolute; top:96px; right:74px;}}
.props .pin.s2{{position:absolute; bottom:62px; left:228px;}}
.props .clip{{position:absolute; right:128px; top:118px; width:13px; height:32px; transform:rotate(26deg);
  border:2px solid #b9bcc0; border-radius:8px; box-shadow:0 2px 4px rgba(0,0,0,.45);}}
.props .clip::before{{content:''; position:absolute; left:2px; right:2px; top:3px; bottom:7px; border:2px solid #a9acb0; border-bottom:none; border-radius:6px 6px 0 0;}}
@media(max-width:1024px){{ .props{{display:none;}} }}

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
</style>
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
      <select class="theme-sel" id="theme-sel" onchange="setTheme(this.value)" data-i18n-title="theme.sel" title="Thème">
        <option value="cw-nato" data-i18n="theme.cwnato">Cold War OTAN</option>
        <option value="cw-soviet" data-i18n="theme.cwsoviet">Cold War Soviétique</option>
        <option value="modern-nato" data-i18n="theme.modernnato">OTAN moderne</option>
        <option value="modern-east" data-i18n="theme.moderneast">Bloc Est moderne</option>
      </select>
      <button class="flag" id="flag-btn" title="Langue / Language">🇬🇧</button>
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

      <!-- Modules actifs : dossiers ouverts, traitement identique.
           Ordre : HQ · Briefing Generator · Datacard Generator · Route Planner · Recon Station · Field Manual.
           RÈGLE : Field Manual reste TOUJOURS la dernière carte active ; un module activé plus tard s'insère avant. -->
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
              <span class="pver">v2.4.5</span>
            </div>
            <div class="pdesc" data-i18n="bg.desc">Briefings complets — SITAC, plan radio, aérodromes, charts, annexes — export PDF prêt à partager.</div>
            <div class="pstatus"><span class="dot"></span> <span data-i18n="status.op">Opérationnel</span></div>
          </div>
          <span class="cta" data-i18n="cta">▶ Ouvrir le dossier</span>
        </div>

        <div class="print active reveal d3" id="card-dg" style="--card-accent:var(--a-dg)" tabindex="0" role="button" aria-label="Datacard Generator">
          <span class="tape"></span><span class="pin tl"></span><span class="pin tr"></span>
          <div class="shot"></div>
          <div class="caption">
            <div class="cap-row">
              <span class="logo" style="background:var(--a-dg)">D·G</span>
              <span class="ptitle">Datacard Generator</span>
              <span class="pver">v1.4.1</span>
            </div>
            <div class="pdesc" data-i18n="dg.desc">Datacards de vol d'une page pour le kneeboard — saisie ou depuis un briefing, day et night, export PNG et PDF.</div>
            <div class="pstatus"><span class="dot"></span> <span data-i18n="status.op">Opérationnel</span></div>
          </div>
          <span class="cta" data-i18n="cta">▶ Ouvrir le dossier</span>
        </div>
        <div class="print active reveal d4" id="card-rp" style="--card-accent:var(--a-rp)" tabindex="0" role="button" aria-label="Route Planner">
          <span class="tape"></span><span class="pin tl"></span><span class="pin tr"></span>
          <div class="shot"></div>
          <div class="caption">
            <div class="cap-row">
              <span class="logo" style="background:var(--a-rp)">R·P</span>
              <span class="ptitle">Route Planner</span>
              <span class="pver">v1.1.1</span>
            </div>
            <div class="pdesc" data-i18n="rp.desc">Tracé de route sur carte — carte DCS, topographique ou satellite, grille MGRS, aérodromes ; points de référence ; caps, distances, MGRS et DMS, envoyés à la datacard.</div>
            <div class="pstatus"><span class="dot"></span> <span data-i18n="status.op">Opérationnel</span></div>
          </div>
          <span class="cta" data-i18n="cta">▶ Ouvrir le dossier</span>
        </div>
        <div class="print active reveal d5" id="card-rs" style="--card-accent:var(--a-rs)" tabindex="0" role="button" aria-label="Recon Station">
          <span class="tape"></span><span class="pin tl"></span><span class="pin tr"></span>
          <div class="shot"></div>
          <div class="caption">
            <div class="cap-row">
              <span class="logo" style="background:var(--a-rs)">R·S</span>
              <span class="ptitle">Recon Station</span>
              <span class="pver">v1.0.1</span>
            </div>
            <div class="pdesc" data-i18n="rs.desc">Transforme une capture en photo d'analyse de reconnaissance — niveaux de gris, annotations, export PNG pleine résolution.</div>
            <div class="pstatus"><span class="dot"></span> <span data-i18n="status.op">Opérationnel</span></div>
          </div>
          <span class="cta" data-i18n="cta">▶ Ouvrir le dossier</span>
        </div>
        <div class="print active reveal d6" id="card-fm" style="--card-accent:var(--a-fm)" tabindex="0" role="button" aria-label="Field Manual">
          <span class="tape"></span><span class="pin tl"></span><span class="pin tr"></span>
          <div class="shot"></div>
          <div class="caption">
            <div class="cap-row">
              <span class="logo" style="background:var(--a-fm)">F·M</span>
              <span class="ptitle">Field Manual</span>
              <span class="pver">v1.2.3</span>
            </div>
            <div class="pdesc" data-i18n="fm.desc">Le manuel d'emploi de la suite — un chapitre par module, schémas et mode d'emploi, entièrement hors-ligne.</div>
            <div class="pstatus"><span class="dot"></span> <span data-i18n="status.op">Opérationnel</span></div>
          </div>
          <span class="cta" data-i18n="cta">▶ Ouvrir le dossier</span>
        </div>
      </div>

    </div>
  </div>

  <div class="foot">
    <span>DCS Mission Suite</span><span class="dot">·</span>
    <span>Open source · MIT</span><span class="dot">·</span>
    <span id="foot-info">Cold War OTAN</span>
    <span class="right" id="foot-right">Mission Plan</span>
  </div>

</div>
</div>

<!-- Module view -->
<div id="module-view"></div>
<div id="module-loading" class="hidden">Chargement…</div>

<script>
  /* ── Données ──────────────────────────────────────────────── */
  {module_html_js}

  var APP_VERSION = '1.9.1';
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
      'hq.desc': 'Poste de commandement — configuration Wing, identité escadrons, logos partagés avec tous les modules.',
      'bg.desc': 'Briefings complets — SITAC, plan radio, aérodromes, charts, annexes — export PDF prêt à partager.',
      'rs.desc': "Transforme une capture en photo d'analyse de reconnaissance — niveaux de gris, annotations, export PNG pleine résolution.",
      'fm.desc': "Le manuel d'emploi de la suite — un chapitre par module, schémas et mode d'emploi, entièrement hors-ligne.",
      'dg.desc': "Datacards de vol d'une page pour le kneeboard — saisie ou depuis un briefing, day et night, export PNG et PDF.",
      'rp.desc': 'Tracé de route sur carte — carte DCS, topographique ou satellite, grille MGRS, aérodromes ; points de référence ; caps, distances, MGRS et DMS, envoyés à la datacard.',
      'status.op': 'Opérationnel',
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
      'hq.desc': 'Command hub — Wing configuration, squadron identity, logos shared across all modules.',
      'bg.desc': 'Complete briefings — SITAC, radio plan, airfields, charts, annexes — PDF export ready to share.',
      'rs.desc': 'Turns a screenshot into a reconnaissance analysis photo — greyscale, annotations, full-resolution PNG export.',
      'fm.desc': "The suite's field manual — one chapter per module, diagrams and how-tos, fully offline.",
      'dg.desc': 'One-page flight datacards for the kneeboard — from scratch or from a briefing, day and night, PNG and PDF export.',
      'rp.desc': 'Lay a route on a map — DCS, topographic or satellite, MGRS grid, airfields; reference points; headings, distances, MGRS and DMS, sent to the datacard.',
      'status.op': 'Operational',
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
    /* Sync bigstamp / classif via thème actuel */
    var cur = document.body.getAttribute('data-theme') || 'cw-nato';
    setTheme(cur);
    /* Bouton chargement */
    var loadEl = document.getElementById('module-loading');
    if (loadEl) loadEl.textContent = t('loading') + '…';
  }}

  function updateFlagBtn() {{
    var btn = document.getElementById('flag-btn');
    if (btn) btn.textContent = CURRENT_LANG === 'fr' ? '🇬🇧' : '🇫🇷';
  }}

  function setLang(lang) {{
    if (lang !== 'fr' && lang !== 'en') return;
    CURRENT_LANG = lang;
    try {{ localStorage.setItem(KEY_LANG, lang); }} catch(e) {{}}
    applyI18n();
    updateFlagBtn();
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

  /* ── Navigation ────────────────────────────────────────────── */
  function openModule(id) {{
    if (!MODULE_HTML[id]) {{
      console.warn('[M·P] Module ' + id + ' : base64 vide');
      return;
    }}
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
        var doc = iframe.contentDocument;
        /* Injection bouton retour dans .toolbar (pas #app-header — cf. vérif grep) */
        var toolbar = doc && doc.querySelector('.toolbar');
        if (toolbar && !toolbar.querySelector('.mp-back-injected')) {{
          var back = doc.createElement('button');
          back.className = 'mp-back-injected';
          back.textContent = t('back');
          back.style.cssText = 'font-family:inherit;font-size:11px;cursor:pointer;color:#c0892a;'
            + 'background:transparent;border:1px solid #c0892a;border-radius:3px;padding:4px 10px;'
            + 'margin-right:12px;letter-spacing:.03em;min-height:36px;flex-shrink:0;';
          back.addEventListener('click', goHub);
          toolbar.insertBefore(back, toolbar.firstChild);
          /* Tampon escadrille — clone du .tb-brand natif de BG (BG exclu : il l'a déjà) */
          var sn = wingShortName();
          if (id !== 'bg' && sn && !toolbar.querySelector('.mp-wing-stamp')) {{
            if (!doc.getElementById('mp-stamp-style')) {{
              var st = doc.createElement('style');
              st.id = 'mp-stamp-style';
              st.textContent =
                '.mp-wing-stamp{{display:inline-flex;align-items:center;gap:10px;'
              + 'margin-right:12px;padding-right:12px;border-right:1px solid #807454;'
              + "font-family:'Stardos Stencil','Impact','Arial Narrow Bold',sans-serif;"
              + 'font-weight:700;letter-spacing:2px;font-size:15px;color:var(--paper,#e8e3d8);'
              + 'white-space:nowrap;flex-shrink:0;}}'
              + '.mp-wing-stamp::before{{content:"";display:inline-block;width:8px;height:8px;'
              + 'border-radius:50%;background:#c0892a;box-shadow:0 0 8px #c0892a;'
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
        console.log('[M·P v' + APP_VERSION + '] Module ' + id + ' chargé');
        try {{ doc.body.setAttribute('data-theme', document.body.getAttribute('data-theme') || 'cw-nato'); }} catch(e) {{}}
      }});

      mv.appendChild(iframe);
      iframes[id] = iframe;
    }} else {{
      iframes[id].style.display = 'block';
      document.getElementById('module-loading').classList.add('hidden');
      try {{ iframes[id].contentDocument.body.setAttribute('data-theme', document.body.getAttribute('data-theme') || 'cw-nato'); }} catch(e) {{}}
    }}

    activeModule = id;
  }}

  /* Point d'entrée pour les modules (le Route Planner ouvre le Datacard Generator) */
  window.MP_OPEN_MODULE = openModule;

  function goHub() {{
    Object.keys(iframes).forEach(function(iid) {{ iframes[iid].style.display = 'none'; }});
    document.getElementById('module-view').style.display = 'none';
    document.getElementById('landing').style.display = '';
    activeModule = null;
    /* Resync thème + langue si changé dans le module */
    try {{
      var storedTheme = localStorage.getItem(KEY_THEME);
      if (storedTheme && THEMES[storedTheme]) setTheme(storedTheme);
      var storedLang = localStorage.getItem(KEY_LANG);
      if (storedLang && storedLang !== CURRENT_LANG) setLang(storedLang);
    }} catch(e) {{}}
  }}

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

/* Un toucher ou un clic hors de la liste et du bouton la ferme, sans agir ailleurs (le clic qui suit est avalé) ;
   le bouton d'une autre liste ferme celle-ci et s'ouvre ensuite par son propre clic. */
function tbmOutside(e) {{
  const m = TBM.cur;
  if (!m) return;
  const t = e.target;
  if (m.panel.contains(t) || m.btn.contains(t)) return;
  const other = t && t.closest ? t.closest('.tbm-trigger') : null;
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
    initToolbarMenus([['theme-sel', function() {{ return t('theme.sel'); }}]]);   /* la liste du thème au thème de la landing */

    /* Clics cartes */
    document.getElementById('card-hq').addEventListener('click', function() {{ openModule('hq'); }});
    document.getElementById('card-hq').addEventListener('keydown', function(e) {{
      if (e.key === 'Enter' || e.key === ' ') {{ e.preventDefault(); openModule('hq'); }}
    }});
    document.getElementById('card-bg').addEventListener('click', function() {{ openModule('bg'); }});
    document.getElementById('card-bg').addEventListener('keydown', function(e) {{
      if (e.key === 'Enter' || e.key === ' ') {{ e.preventDefault(); openModule('bg'); }}
    }});
    document.getElementById('card-rs').addEventListener('click', function() {{ openModule('rs'); }});
    document.getElementById('card-rs').addEventListener('keydown', function(e) {{
      if (e.key === 'Enter' || e.key === ' ') {{ e.preventDefault(); openModule('rs'); }}
    }});
    document.getElementById('card-rp').addEventListener('click', function() {{ openModule('rp'); }});
    document.getElementById('card-rp').addEventListener('keydown', function(e) {{
      if (e.key === 'Enter' || e.key === ' ') {{ e.preventDefault(); openModule('rp'); }}
    }});
    document.getElementById('card-fm').addEventListener('click', function() {{ openModule('fm'); }});
    document.getElementById('card-fm').addEventListener('keydown', function(e) {{
      if (e.key === 'Enter' || e.key === ' ') {{ e.preventDefault(); openModule('fm'); }}
    }});
    document.getElementById('card-dg').addEventListener('click', function() {{ openModule('dg'); }});
    document.getElementById('card-dg').addEventListener('keydown', function(e) {{
      if (e.key === 'Enter' || e.key === ' ') {{ e.preventDefault(); openModule('dg'); }}
    }});

    document.getElementById('flag-btn').addEventListener('click', toggleLang);
    /* Sync inter-contextes : thème + tampon wing (srcdoc même origine) */
    window.addEventListener('storage', function(e) {{
      if (e.key === KEY_THEME && e.newValue && THEMES[e.newValue]) {{ setTheme(e.newValue); }}
      else if (e.key === 'wing_config_v1') {{ refreshWingStamps(); }}
    }});

    console.log('[M·P v' + APP_VERSION + '] Initialisé — langue: ' + CURRENT_LANG);
  }}

  document.addEventListener('DOMContentLoaded', init);
</script>
</body>
</html>'''


def main():
    print('=== build_mission_plan.py — DCS Mission Plan shell ===')

    print('\n[1/3] Encodage modules HTML…')
    module_html_js = build_module_html_js(MODULES)

    print('\n[2/3] Encodage images tuiles…')
    tile_uris = build_tile_uris(MODULES)

    print(f'\n[3/3] Génération {OUT_FILE}…')
    html = build_html(module_html_js, tile_uris)

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
