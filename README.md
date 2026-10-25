# DCS Mission Plan

<!-- Replace with a screenshot of the landing "situation board" (e.g. docs/screenshots/landing.png) -->
![Intro-image](docs/screenshots/landing.jpg)
> Prepare your DCS World missions end to end — a suite of tools behind one operational landing page. **Use it online, or download a single offline file.**

![License](https://img.shields.io/badge/license-MIT-blue)
![Platform](https://img.shields.io/badge/platform-Web-green)
![Offline](https://img.shields.io/badge/offline-yes-success)
![Tablet & mobile](https://img.shields.io/badge/tablet%20%26%20mobile-ready-orange)
![Tools](https://img.shields.io/badge/tools-6%20live-brown)

🌐 **[Use it online »](https://mirabellebenou.github.io/dcs-mission-plan/)** &nbsp;·&nbsp; 💾 **[Download the offline file »](../../releases)**

> 🗺️ **Thanks to the [DCS Olympus](https://github.com/Pax1601/DCSOlympus) team!** The Route Planner's **DCS map** layer uses the DCS map tiles they kindly share with the community — come and say hi on their **[Discord](https://discord.gg/kNAQkhUHnQ)**.

A single-page **"situation board"** that brings together a suite of mission-prep tools for DCS World virtual pilots and wings — staged like a Cold War operations table. Open the board, pick a tool, prepare your mission. It runs entirely in your browser: **online for those who don't want to download**, or as **one offline HTML file** you can keep, share, and use without internet.

Developped with the help of Claude AI (I'm not a dev !)

---

## 📱 Built for the tablet (and your phone)

Mission Plan is designed to be used **where you actually fly** — on a tablet next to your stick, or on your phone.

- **Touch-first UI** — large tap targets, drag-and-drop, no tiny desktop-only controls
- **Responsive layout** — split view on tablet/desktop, tabbed view on phone
- **Rotation-safe** — keeps working when you flip the tablet between landscape and portrait
- **No install** — open a link or a single file in the mobile browser; works offline once loaded
- **Export on the go** — generate PDF/PNG straight from the device

## 🧰 The suite

The landing page presents each tool as a **pinned print** on the board. Active tools open in place; upcoming ones are stamped *Coming soon*.

| Tool | What it does | Status |
|------|--------------|--------|
| **HQ** | Command post — configure your wing once (branding, squadrons), shared with the other tools; experimental `.miz` mission reader/patcher | 🧪 Beta `v0.1.1` |
| **Briefing Generator** | Mission briefings, full or quick — SITAC, radio plan, airfields, charts, recon photos — PDF & PNG export | ✅ `v2.4.5` |
| **Recon Station** | Turn a screenshot into a reconnaissance analysis photo — sensor looks, annotations, lossless PNG | ✅ `v1.0.1` |
| **Field Manual** | In-app documentation for the suite — one illustrated chapter per tool, diagrams, FR/EN, offline | ✅ `v1.2.3` |
| **Route Planner** | Lay a route on a map — DCS map (by DCS Olympus), topographic or satellite, MGRS grid, place names, DCS airfields — type coordinates or heading & distance, reference points, headings, distances, MGRS & DMS, sent to the datacard | ✅ `v1.1.1` |
| **Datacard Generator** | One-page flight datacards for the kneeboard — from scratch, from a briefing or from a route — reference points, day & night, PNG & PDF export | ✅ `v1.4.1` |

> Each tool is a standalone HTML file with its own build; the landing page embeds the live tools and stages them all on one board.

### 🛡️ HQ — your wing, configured once

HQ is the suite's **command post**. Its main job today is the **wing hub**: set your wing name, logo, squadrons and callsigns **once**, and Briefing Generator + Recon Station pick it up automatically. HQ also ships an **experimental `.miz` engine** (read a mission, export a mission snapshot, apply surgical patches) — the advanced flight-package UI is still in development and in-game validation is pending, so HQ is published as **beta**.

### 🚀 Briefing Generator — in detail

Briefing Generator builds a **complete, shareable mission briefing** as a multi-section document, with **PDF and per-page PNG export** straight from the browser.

- **Sections** — cover, situation map (SITAC), charts, annexes, and mission phases
- **Radio & weather** — radio plan, METAR assistant, and **METAR import from a `.miz`**
- **Airfields** — structured airfield information
- **Wing branding** — pulled automatically from HQ (name, logo, squadrons)
- **Images** — drop in your own maps/charts; oversized images are auto-recompressed
- **4 themes, FR/EN**, multi-wing

### 🛰️ Recon Station — in detail

Recon Station turns any screenshot into a convincing **reconnaissance analysis photo**, fully in the browser, with **lossless full-resolution PNG export** (native Canvas 2D — what you preview is exactly what you export).

- **Sensor looks** — EO (default), IR white-hot, IR black-hot, SAR (stylizations, not radiometric data)
- **Image effects** — greyscale, contrast, vignette, grain, scanlines (sliders, off by default)
- **Annotations** — numbered movable markers, a magnifier/loupe (crops after effects), shapes (ellipse, rectangle, polygon, arrow, bracket), and labels (stamp, cursive grease-pencil, plain)
- **Editable info block** — 9 fields, bold text, black/white
- **Classification banner** — top/bottom bars, 4 levels, off by default
- **Wing logos** — upload manually or pull the shared wing branding from HQ; colour / grey / white modes

### 📖 Field Manual — in detail

The Field Manual is the suite's **built-in documentation**, opened from the board like any other tool — **no internet, no separate guide to download**.

- **One chapter per tool** — Recon Station, HQ, Briefing Generator, Datacard Generator (upcoming tools are stubbed)
- **Diagrams, not screenshots** — each chapter has a hand-drawn-style **SVG schematic** (e.g. *what feeds what* in the Briefing Generator) that adapts to the active theme
- **"What it's for" first** — plain explanations of each tool's purpose and workflow
- **4 themes, FR/EN**, fully offline

## ✨ Features

- **Online or fully offline** — use the hosted version, or one HTML file with no install, no server, no internet
- **One landing page** — embeds the live tools; open it, use it, share it
- **Tablet & mobile first** — see above 📱
- **4 graphical themes** — Cold War NATO (default), Cold War Soviet, Modern NATO, Modern Eastern Bloc — chosen on the board, carried across the tools
- **Bilingual** — full FR/EN toggle, shared across the suite
- **Configure your wing once** (HQ) — branding/squadrons shared with the other tools
- **PDF & PNG export** — straight from your browser
- **Auto-save** — your work is preserved in your browser's local storage

## 📸 Screenshots

<!-- Drop your screenshots in docs/screenshots/ and update the paths below -->
![board](docs/screenshots/board.png)

![briefing-generator](docs/screenshots/briefing_generator.png)

![recon-station](docs/screenshots/recon_station.png)

## 🚀 Quick Start

**Option A — online (nothing to download)**
1. Open **[the hosted version](https://mirabellebenou.github.io/dcs-mission-plan/)** in your browser (works on phone/tablet too)
2. Pick a tool on the board and go

**Option B — offline file**
1. Download the latest `dcs_mission_plan.html` from the [Releases](../../releases) page
2. Open it in any modern browser (Chrome recommended) — on PC or tablet
3. It keeps working offline; bookmark or "Add to Home Screen" on mobile

No account, no internet required after the first load.

## 🛡️ For wing administrators

Customize the branding for your virtual wing — done once, in **HQ**, and shared with every tool:

1. Open **HQ** from the board
2. Set the wing name, logo, squadrons, callsigns
3. The configuration is shared automatically with Briefing Generator and Recon Station (and exportable to hand to your pilots)

The default `MY WING` configuration is generic — replace it with your own.

## 📓 Changelog

See [CHANGELOG.md](./CHANGELOG.md) for the per-tool version history.

## 🏗️ Building from source

If you want to modify the code yourself.

### Prerequisites
- Python 3.8+ (standard library only)

### Build
Each tool builds to a standalone HTML, then the landing page embeds the live tools:

```bash
# 1) Build the tools
python3 build_briefing_generator.py             # → dist/dcs_briefing_generator.html
python3 build_recon_station.py                  # → dist/dcs_recon_station.html
python3 build_hq.py                             # → dist/dcs_hq.html
python3 build_field_manual.py                   # → dist/dcs_field_manual.html
python3 build_datacard_generator.py            # → dist/dcs_datacard_generator.html
python3 build_route_planner.py                 # → dist/dcs_route_planner.html

# 2) Assemble the landing page (embeds the tools + board tiles)
python3 build_mission_plan.py                   # → dist/dcs_mission_plan.html
```

Run the six tool builds first, then the landing-page build: the latter reads the six modules from `dist/` and the tiles from `tiles/`. Inputs (`assets.json`, `tiles/`) are read from the repository, and a build stops with a non-zero exit code if one is missing.

The output `dist/dcs_mission_plan.html` is the distributable (and the file published online). `docs/index.html` is a byte-for-byte copy of `dist/dcs_mission_plan.html`, made at each milestone.

### Project structure
```
.
├── build_mission_plan.py          # Landing/shell builder — embeds tools + tiles
├── build_briefing_generator.py    # Briefing Generator builder (single script)
├── build_recon_station.py         # Recon Station builder
├── build_hq.py                    # HQ builder
├── build_field_manual.py          # Field Manual builder
├── build_datacard_generator.py    # Datacard Generator builder
├── build_route_planner.py         # Route Planner builder
├── assets.json                    # Embedded fonts, libraries, kraft texture (base64)
├── airfields.json                 # DCS airfield & helipad positions (from pydcs)
├── tiles/                         # Board tiles (512² WebP): hq, bg, rs, fm, rp, kg
├── docs/screenshots/              # README images
├── CHANGELOG.md
├── README.md
└── LICENSE
```

## 🗺️ Roadmap

### ⏳ Work in Progress
- ⏳ **HQ** — flight-package / Commander UI, and in-game `.miz` validation (out of beta)
- ⏳ **Route Planner** — DCS Route Tool import & export, NATO symbols and drawing, read routes from a `.miz`, automatic magnetic variation, kneeboard export
- ⏳ **Datacard Generator** — import waypoints and loadouts from HQ (`.miz`)
- ⏳ **UI polish** and more themes

### 📋 Planned (Briefing Generator)
- Auto-save indicator, briefing templates (CAS / CAP / SEAD), URL-based sharing
- Full-screen presentation mode, recurring-charts library
- Briefing versioning + diff, auto checklist validation

## 🤝 Contributing

Bug reports and feature suggestions are welcome via the [Issues](../../issues) page.

For code contributions: fork, branch, study the build scripts to understand the architecture, test by rebuilding and opening the result in a browser, then open a pull request.

## ⚠️ Compatibility

- **Chrome / Edge** (recommended): all features, including print-to-PDF
- **Firefox**: works; PDF rendering may differ slightly
- **Safari** (macOS & iOS): works, minor visual variations
- **Mobile browsers** (Android/iOS): supported and a first-class target — touch, drag, rotation

## 📄 License

[MIT License](./LICENSE) — free to use, modify, and distribute, including commercially.

## 🙏 Acknowledgments

- Built for the DCS World virtual aviation community
- DCS map tiles by the **[DCS Olympus](https://github.com/Pax1601/DCSOlympus)** team — [Discord](https://discord.gg/kNAQkhUHnQ)
- Map engine [Leaflet](https://leafletjs.com) (BSD-2-Clause); topographic tiles © OpenStreetMap contributors, SRTM, style © OpenTopoMap (CC-BY-SA); satellite imagery © Esri, Maxar, Earthstar Geographics
- DCS airfield & helipad names and positions from **[pydcs](https://github.com/pydcs/dcs)** (LGPL-3.0); place-name overlay © Esri, HERE, Garmin, OpenStreetMap contributors
- Initial version developed for the **4th VEAW** virtual wing — distributed as a generic wing config example
- Cold War kraft SVG file provided by Flappie, thanks to him !

---

*This project is not affiliated with or endorsed by Eagle Dynamics, the developers of DCS World.*
