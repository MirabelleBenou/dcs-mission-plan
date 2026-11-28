![Mission Plan — part of the Squadron Ready Room family](brand/banniere-mission-plan.png)

# DCS Mission Plan

**v2.1.0** — one version for the whole suite; see the [CHANGELOG](./CHANGELOG.md).

![Intro-image](docs/screenshots/landing.jpg)
> Prepare your DCS World missions end to end — a suite of tools behind one operational landing page. **Use it online, or download a single offline file.**

![License](https://img.shields.io/badge/license-AGPL--3.0--or--later-blue)
![Platform](https://img.shields.io/badge/platform-Web-green)
![Offline](https://img.shields.io/badge/offline-except%20online%20maps-yellowgreen)
![Tablet & mobile](https://img.shields.io/badge/tablet%20%26%20mobile-ready-orange)
![Tools](https://img.shields.io/badge/tools-7%20live-brown)

> Aircraft, airfield and map data come from **[pydcs](https://github.com/pydcs/dcs)** (LGPL-3.0-or-later) — many thanks to its authors.

🌐 **[Use it online »](https://mirabellebenou.github.io/dcs-mission-plan/)** &nbsp;·&nbsp; 💾 **[Download the offline file »](../../releases)**

> 🗺️ **Thanks to the [DCS Olympus](https://github.com/Pax1601/DCSOlympus) team!** The Route Planner's **DCS map** layer uses the DCS map tiles they kindly share with the community — come and say hi on their **[Discord](https://discord.gg/kNAQkhUHnQ)**.
>
> 🧭 **Thanks to Flappie!** The Route Planner's **navigation chart** on the Caucasus is his accurate DCS map — see it on **[his website](http://dcsmaps.com/caucasus/openlayers)** or get the **[GeoTIFF on DCS User Files](https://digitalcombatsimulator.com/en/files/3305623/)**.

A single-page **"situation board"** that brings together a suite of mission-prep tools for DCS World virtual pilots and wings — staged like a Cold War operations table. Open the board, pick a tool, prepare your mission. It runs entirely in your browser: **online for those who don't want to download**, or as **one offline HTML file** you can keep, share, and use offline — only the Route Planner's online map backgrounds and airfield chart sheets need a connection.

Developed with the help of Claude AI (I'm not a dev!)

---

## 📱 Built for the tablet (and your phone)

Mission Plan is designed to be used **where you actually fly** — on a tablet next to your stick, or on your phone.

- **Touch-first UI** — large tap targets, drag-and-drop, no tiny desktop-only controls
- **Responsive layout** — split view on tablet/desktop, tabbed view on phone
- **Rotation-safe** — keeps working when you flip the tablet between landscape and portrait
- **No install** — open a link or a single file in the mobile browser; works offline once loaded (except the Route Planner's online map backgrounds and airfield chart sheets); needs Safari or iOS 16.4, Chrome or Edge 80, Firefox 113, or later
- **Export on the go** — generate PDF/PNG straight from the device

## 🧰 The suite

The landing page presents each tool as a **pinned print** on the board. Active tools open in place; upcoming ones are stamped *Coming soon*.

| Tool | What it does | Status |
|------|--------------|--------|
| **HQ** | Command post — configure your wing once (branding, squadrons), shared with the other tools; experimental `.miz` mission reader/patcher | 🧪 Beta |
| **Flight Configurator** | Prepare a flight for the Mission Commander — identity, radios, loadout built on the aircraft's front view or started from your presets, livery — and export it as a flight package that HQ applies to a mission; the departure airfield and the stand of each aircraft, on the airfield map; every flyable aircraft of the game (75 types) | 🧪 Beta |
| **Briefing Generator** | Mission briefings, full or quick — SITAC, radio plan, airfields, charts, recon photos, map from the Route Planner — PDF & PNG export | ✅ |
| **Recon Station** | Turn a screenshot into a reconnaissance analysis photo — sensor looks, annotations drawn by touch, lossless PNG | ✅ |
| **Field Manual** | In-app documentation for the suite — one illustrated chapter per tool, diagrams, FR/EN, offline | ✅ |
| **Route Planner** | Lay a route on a map — DCS map (by DCS Olympus), Flappie's navigation chart on the Caucasus, topographic or satellite, MGRS grid, place names, DCS towns and airfields, map search — type coordinates or heading & distance, reference points, headings, distances, MGRS & DMS, sent to the datacard; DCS Route Tool import & export; leg boxes, ground speed and minute marks; CombatFlite layers (.cf); draw your own layers by touch — circles, zones and curves, lines, FLOT and corridors, points, text, orbits, kill boxes with their grid; NATO military symbols (APP-6) — units, equipment, aircraft, FARP — filled or outlined, three sizes; magnetic headings with the variation computed like DCS, leg by leg; tap an airfield or heliport to open its chart from DCS Airfield Charts, served by the wing's server; send the framed map view to the Briefing Generator; a Display menu to show or hide the route, reference points, drawings, NATO symbols, imported layers, grid, towns, airfields and places | ✅ |
| **Datacard Generator** | One-page flight datacards for the kneeboard — from scratch, from a briefing or from a route — reference points, day & night, PNG & PDF export; magnetic headings computed like DCS | ✅ |

> Mission Plan is a single HTML file: every tool opens from its home page, and one **Save** writes all the work of the suite into one `.json` file that **Open…** brings back.

### 🛡️ HQ — your wing, configured once

HQ is the suite's **command post**. Its main job today is the **wing hub**: set your wing name, logo, squadrons and callsigns **once**, and Briefing Generator + Recon Station pick it up automatically. HQ also ships an **experimental `.miz` engine** (read a mission, export a mission snapshot, apply surgical patches) — HQ applies the Flight Configurator's flight packages to the mission, and creates a flight the mission lacks, from its package, on its stands when the package says so; in-game validation is pending, so HQ is published as **beta**. HQ can also write **Dynamic Spawn** into a mission: mark flights as templates and link them to the airfields, FARPs and ships that already have Dynamic Spawn enabled in the mission editor (HQ never enables it). Its **Example** button loads a demonstration wing; your own configuration is kept and can be restored in one tap.

### ✈️ Flight Configurator — in detail

The Flight Configurator is the **Flight Lead's** tool: it prepares one or more flights and exports them as a **flight package** (`dcs-flight-package-v2`; the v1 packages are still read) that the Mission Commander applies to a mission with HQ. It runs for **every flyable aircraft of the game** (75 types). A flight can carry its **departure** (`departure`: the start, the base and the stands that fit the aircraft) and each unit its **stand** (`stand`: parking number, name and position); a package without them is read as before, and HQ writes them into the flight it creates. Each unit of a type that has equipment options also carries `AddPropAircraft` (the options of the mission editor, by id and value); a package without it is read as before.

- **Flights** — group name, aircraft, coalition, up to four units (name, call sign, onboard number, livery); flights fold into a one-line summary
- **Radios** — every radio of the aircraft, one field per channel, frequencies from 0 to 999.999 MHz (the Comm Plan Editor's rule); copy to the other units of the flight
- **Loadout** — built on the aircraft's **front view**: a weapon list per station, twin stations, the loadout mass and the take-off mass, and fuel, flares, chaff and gun brought back to the aircraft's limits; start from **My presets** (loaded from `.lua` preset files, or kept from your own loadouts)
- **Take-off mass** — added up like the DCS mission editor (`me_payload.updateTotalWeight`): the empty aircraft with its equipment options, plus the fuel, the stores, the gun rounds at the gun percentage (the field only shows on aircraft that have a gun) and, for some aircraft, the tank whose mass follows the fuel; flares and chaff weigh nothing. A line under the loadout mass gives each term
- **Equipment** — the options that the mission editor gives each aircraft type (IR exhaust suppressors, extra armour, cargo door, water or MW-50 tanks, solo flight…): a box per option, a list when it has several values, each with its mass. The package carries them for each unit as `AddPropAircraft` (every option of the type with its value, plus any key of the mission that the table does not know); HQ writes them to the aircraft, in found and created flights, and the mission's own options come back to the Flight Configurator with the loadout
- **Livery** — free text, with suggestions from the liveries already seen for that aircraft type
- **Departure** — the base (listed by distance from the route's first waypoint), the start (on the stand, cold or engines running; or in the air or on the ground at the first waypoint) and a stand for each aircraft, from a list of the stands that fit it or on the airfield map drawn by DCS Airfield Charts; a stand taken by another aircraft of the flight is not offered
- **Import** — the mission loaded in HQ, a briefing or a flight package (`.json` or `.zip`), with four boxes per flight: Route, Radios, Loadout, Livery; the route is carried as is, never drawn
- **Open / Save** — **Save** writes all the Mission Plan work, your flights included (your loadout presets stay in your browser), into the suite's work file, and **Open ▾ › Open a work file…** brings it back (an old Flight Configurator file still opens); **Export** writes the package (parts left empty stay untouched in HQ)
- **Reusable loadout engine** — `payload_block.py` reads preset files and builds a `.miz` `payload`, with no DOM and no network; other modules can take it as is
- **4 themes, FR/EN**, touch-first, works offline

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
- **Annotations, by touch** — a drawing bar on the image: frames, ellipses, polylines, arrows, brackets, text labels (stamp, cursive grease-pencil, plain) and magnifiers; one tap places, large handles adjust (frames and magnifiers by their edges and corners, frames rotate); numbered movable markers
- **Editable info block** — 9 fields, bold text, black/white
- **Classification banner** — top/bottom bars, 4 levels, off by default
- **Wing logos** — upload manually or pull the shared wing branding from HQ; colour / grey / white modes
- **Example** — loaded from the **Example ▾** menu of the landing page (Mission Commander line): a demonstration photo with its markers, shapes, magnifier and info block; **Restore** brings back the previous work, image included

### 📖 Field Manual — in detail

The Field Manual is the suite's **built-in documentation**, opened from the board like any other tool — **it works offline, with no separate guide to download**.

- **One chapter per tool** — Recon Station, HQ, Flight Configurator, Briefing Generator, Datacard Generator, Route Planner
- **Diagrams, not screenshots** — each chapter has a hand-drawn-style **SVG schematic** (e.g. *what feeds what* in the Briefing Generator) that adapts to the active theme
- **"What it's for" first** — plain explanations of each tool's purpose and workflow
- **4 themes, FR/EN**, works offline

## ✨ Features

- **Online or offline** — use the hosted version, or one HTML file with no install and no server; everything works offline except the Route Planner's online map backgrounds and airfield chart sheets
- **One landing page** — embeds the live tools; open it, use it, share it
- **Tablet & mobile first** — see above 📱
- **4 graphical themes** — Cold War NATO (default), Cold War Soviet, Modern NATO, Modern Eastern Bloc — chosen on the board, carried across the tools
- **Bilingual** — full FR/EN toggle, shared across the suite
- **Configure your wing once** (HQ) — branding/squadrons shared with the other tools
- **PDF & PNG export** — straight from your browser
- **Auto-save** — your work is preserved in your browser's local storage

## 📸 Screenshots

**The board** — every tool on one page, two roles, 4 themes, FR/EN

![landing](docs/screenshots/landing.jpg)

**HQ** — the wing configuration, with the example wing loaded

![hq](docs/screenshots/hq.jpg)

**Flight Configurator** — a group with its units, route sketch and legs, ready to export as a flight package

![flight-configurator](docs/screenshots/flight_configurator.jpg)

**Flight Configurator, loadout** — each station set on the aircraft's front view, with its weight

![flight-configurator-loadout](docs/screenshots/flight_configurator_loadout.jpg)

**Briefing Generator** — the editor on the left, the printed briefing on the right

![briefing-generator](docs/screenshots/briefing_generator.jpg)

**Recon Station** — numbered targets with their legend, a frame, an ellipse and a magnifier drawn on the image, with the info block

![recon-station](docs/screenshots/recon_station.jpg)

<sub>Recon Station sample image (also the tool's built-in example): USDA National Agriculture Imagery Program (NAIP) aerial photograph, public domain.</sub>

**Route Planner** — a route on the DCS map, with leg boxes, minute marks and reference points

![route-planner](docs/screenshots/route_planner.jpg)

**Datacard Generator** — a one-page kneeboard datacard, built from scratch or from a group, a briefing or a route

![datacard-generator](docs/screenshots/datacard_generator.jpg)

## 🚀 Quick Start

**Option A — online (nothing to download)**
1. Open **[the hosted version](https://mirabellebenou.github.io/dcs-mission-plan/)** in your browser (works on phone/tablet too)
2. Open the **Field Manual** from the top bar of the board and read its **Where to start** page (the two roles, the order of the tools, the work file), then pick a tool and go

**Option B — offline file**
1. Download the latest `dcs_mission_plan.html` from the [Releases](../../releases) page
2. Open it in any modern browser (Chrome recommended) — on PC or tablet
3. It keeps working offline (except the Route Planner's online map backgrounds and airfield chart sheets); bookmark or "Add to Home Screen" on mobile

No account needed. Once the page or the file is loaded, everything works offline, except what the Route Planner loads online: its map backgrounds and its airfield chart sheets.

The **Example ▾** menu is only on the landing page, in its top bar, with two lines (Mission Commander, Flight Leader); the tools have no such menu. There is one example, the fictional STEPPE WIND operation over Cyprus, and it loads by group: the Mission Commander line fills the Briefing Generator and the Recon Station, the Flight Leader line fills the Route Planner, the Datacard Generator and the Flight Configurator; **Restore** brings back the previous work — the quickest way to see what the suite does. HQ has its own **Example** button in its top bar, which loads a demonstration wing (Task Force Kestrel); the Field Manual has no example.

## 🛡️ For wing administrators

Customize the branding for your virtual wing — done once, in **HQ**, and shared with every tool:

1. Open **HQ** from the board
2. Set the wing name, logo, squadrons, callsigns
3. The configuration is shared automatically with Briefing Generator and Recon Station (and exportable to hand to your pilots)

The default `MY WING` configuration is generic — replace it with your own.

## 📓 Changelog

See [CHANGELOG.md](./CHANGELOG.md) for the release notes (one version for the suite since v2.0.0; the history of each tool up to v1.24.0 is kept below them).

## 🏗️ Building from source

If you want to modify the code yourself.

### Prerequisites
- Python 3.8+ (standard library only)

### Build
Each tool builds to an HTML module (a build step, not a file to open on its own), then the landing page embeds them:

```bash
# 1) Build the tools
python3 build_briefing_generator.py             # → dist/dcs_briefing_generator.html
python3 build_recon_station.py                  # → dist/dcs_recon_station.html
python3 build_hq.py                             # → dist/dcs_hq.html
python3 build_flight_configurator.py            # → dist/dcs_flight_configurator.html
python3 build_field_manual.py                   # → dist/dcs_field_manual.html
python3 build_datacard_generator.py            # → dist/dcs_datacard_generator.html
python3 build_route_planner.py                 # → dist/dcs_route_planner.html

# 2) Assemble the landing page (embeds the tools + board tiles)
python3 build_mission_plan.py                   # → dist/dcs_mission_plan.html
```

Opened on its own, a module only shows a line pointing to Mission Plan.

Run the seven tool builds first, then the landing-page build: the latter reads the seven modules from `dist/` and the tiles from `tiles/`. Inputs (`assets.json`, `tiles/`) are read from the repository, and a build stops with a non-zero exit code if one is missing.

The output `dist/dcs_mission_plan.html` is the distributable (and the file published online). `docs/index.html` is a byte-for-byte copy of `dist/dcs_mission_plan.html`, made at each milestone.

### Project structure
```
.
├── build_mission_plan.py          # Landing/shell builder — embeds tools + tiles
├── build_briefing_generator.py    # Briefing Generator builder (single script)
├── build_recon_station.py         # Recon Station builder
├── build_hq.py                    # HQ builder
├── build_flight_configurator.py   # Flight Configurator builder
├── payload_block.py               # Shared loadout block (preset files, .miz payload), no DOM
├── radio_bands_block.py           # Shared radio bands and non-preset radios block (Flight Configurator, Datacard Generator, HQ, Route Planner), no DOM
├── aircraft_types_block.py        # HQ's game aircraft types block (reads data/aircraft_types.json), no DOM
├── build_field_manual.py          # Field Manual builder
├── build_datacard_generator.py    # Datacard Generator builder
├── build_route_planner.py         # Route Planner builder
├── assets.json                    # Embedded fonts, libraries, kraft texture (base64)
├── airfields.json                 # DCS airfield & helipad positions (from pydcs)
├── airdromes.json                 # DCS airfield names and ids per theatre (from pydcs, via DCS Airfield Charts)
├── public_host_block.py           # Shared address of the suite's public files (Route Planner, Flight Configurator), no DOM
├── brand_block.py                 # Shared family insignia block (reads brand/): tab icons, insignia data URLs, no DOM
├── towns.json                     # DCS town names & positions (from the DCS World maps)
├── data/                          # Flight Configurator tables (weapons, pylons, limits, front views from Mission Tools), HQ's aircraft types, and their licences
├── wmm/                          # World Magnetic Model coefficients 1985–2025 (NOAA, public domain)
├── igrf/                         # IGRF-12 coefficients 1900–2015 (IAGA, as shipped by DCS World)
├── tiles/                         # Board tiles (512² WebP): hq, bg, rs, fm, rp, kg, fc
├── docs/screenshots/              # README images
├── brand/                         # Squadron Ready Room family insignia: tab icons, insignia, banner (copies of the family's master files)
├── CHANGELOG.md
├── README.md
└── LICENSE
```

### Shared loadout block (`payload_block.py`)

The module's “loadout” part lives in a **shared JavaScript block**, `payload_block.py`: no DOM, no `t()`, no network, it runs alone under `node`. Another module takes it **as is**: the block's text is byte-identical in every `dist/` file that uses it. It reads three tables set before it, under these names: `WEAPON_NAMES` (CLSID → name), `AIRCRAFT_PYLONS` (permitted weapons and masses per station) and `AIRCRAFT_LIMITS` (fuel, countermeasures), the same ones as Mission Tools' Loadout Editor.

- **`parseUnitPayloads(text)`** reads a preset `.lua` file (the Lua subset of those files: tables, strings, numbers, booleans, comments). It returns `{ unitType, supported, presets: [{ name, displayName, pylons: { number: { CLSID, settings? } } }] }`; `supported` is false for any type other than the four handled (the file reads, but is offered to no group). A read error carries `.line` (the line number), `.code` and `.detail`. A station's `settings` are returned as they are.
- **`buildPayload(type, pylons, { fuel, flare, chaff, gun })`** returns a .miz `payload` object: `pylons` numbered by station (`{ CLSID, settings? }`), `fuel`, `flare`, `chaff`, `gun` brought within the table's limits, and the type's fixed keys (`ammo_type`, `restricted`), as missions write them: the Mi-8MT's fuel is a string, the other three's a number. Helpers read the tables: `payloadPylons(type)`, `payloadWeaponName(clsid)`, `payloadWeaponMass(clsid)`, `payloadDefaults(type)`. `payloadMirrorClsid(clsid, allowedOnTwin)` returns the mirror weapon to put on the twin station (same CLSID, else Left↔Right, else the only weapon with the same name) or an empty string. `payloadWeaponSide(type, clsid)` returns `'L'`, `'R'` or `''`: the side of a weapon whose name is carried by several CLSIDs of the same aircraft, when its CLSID carries one (`Left`/`Right`, `LEFT`/`RIGHT`, `_L`/`_R` at the end); the “left” / “right” text is the caller's. To reuse the block: set the three tables, insert the block's text, call these functions.

## 📦 Publishing a release (maintainers)

Releases are created by the workflow `.github/workflows/release.yml`, not by hand. On `main`, `DEV_BUILD` in `version_block.py` is set to 0, `SUITE_VERSION` takes the new number and the suite is rebuilt, and the changes under `Unreleased` in the CHANGELOG get their heading `## MP-V<x.y.z> — YYYY-MM-DD`. Then a branch `release/MP-V<x.y.z>` is pushed: that `main` commit plus files under `.release/` only — `notes.md` (the release text), the files to download under `assets/` (`dcs_mission_plan.html`; a file over 100 MB, the limit of a git push, goes in parts `.part001`, `.part002`…), and last `manifest.json` (tag, title, `main` commit, and the name, size and SHA-256 of each file). `notes.md` ends with a `## Version numbers` paragraph, the CHANGELOG's `### Version numbers` block word for word: the workflow checks it.

The workflow checks all of it, creates the release with its files, publishes it as the latest release (which creates the tag on the `main` commit) and deletes the branch. If anything fails, nothing stays published and the branch gets `.release/FAILED.md` with the reason. A branch `release/essai-<name>` runs the same checks without publishing anything and writes `.release/CHECK.md`. A file that still carries a build number is refused.

## 🗺️ Roadmap

### ⏳ Work in Progress
- ⏳ **HQ** — in-game `.miz` validation (out of beta)
- ⏳ **Route Planner** — clock times from a TOT, kneeboard export
- ⏳ **The suite** — more aircraft types (the Flight Configurator handles four today), and phone ergonomics
- ⏳ More themes

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

[GNU AGPL-3.0-or-later](https://github.com/MirabelleBenou/dcs-mission-plan/blob/main/LICENSE) — free to use, modify and share, commercial use included (a paid service too), **provided the source code of your version is published under the same licence**, hosted services included (section 13). Every interface must keep the credit line “Based on Mission Plan by MirabelleBenou and the 4th VEAW virtual wing” (an additional term under section 7(b), see `LICENSE`). Releases up to v1.24.0 remain under the MIT licence. Exceptions: the Flight Configurator's front-view drawings (by Goldwolf, `data/views/LICENSE.md`) and the pydcs-derived tables (LGPL-3.0-or-later, `data/COPYING.LESSER`).

## 🙏 Acknowledgments

- Built for the DCS World virtual aviation community
- DCS map tiles by the **[DCS Olympus](https://github.com/Pax1601/DCSOlympus)** team — [Discord](https://discord.gg/kNAQkhUHnQ)
- Caucasus navigation chart by **Flappie** — [his website](http://dcsmaps.com/caucasus/openlayers) and the [GeoTIFF on DCS User Files](https://digitalcombatsimulator.com/en/files/3305623/), many thanks to him!
- Map engine [Leaflet](https://leafletjs.com) (BSD-2-Clause); topographic tiles © OpenStreetMap contributors, SRTM, style © OpenTopoMap (CC-BY-SA); satellite imagery © Esri, Maxar, Earthstar Geographics; paper base map drawn with [MapLibre GL JS](https://maplibre.org) (BSD-3-Clause), [PMTiles](https://github.com/protomaps/PMTiles) (BSD-3-Clause) and [maplibre-gl-leaflet](https://github.com/maplibre/maplibre-gl-leaflet) (ISC), map data © OpenStreetMap contributors (ODbL), relief Copernicus WorldDEM © DLR e.V., © Airbus DS; terrain relief © DCS World, Eagle Dynamics SA, read in the game (non-commercial use)
- NATO military symbols drawn with **[milsymbol](https://github.com/spatialillusions/milsymbol)** by Måns Beckman (MIT)
- DCS airfield & helipad names and positions, and the DCS map projections, from **[pydcs](https://github.com/pydcs/dcs)** (LGPL-3.0-or-later); place-name overlay © Esri, HERE, Garmin, OpenStreetMap contributors
- Airfield names and ids: pydcs, via DCS Airfield Charts
- Flight Configurator: the airfield stands (`data/parkings.json`, from pydcs, LGPL-3.0-or-later) and the airfield maps drawn under them, from **DCS Airfield Charts**
- Datacard Generator: today's ICAO codes of the airfields from **[OurAirports](https://ourairports.com/)** (public domain), matched by position, via DCS Airfield Charts (`airfield_icao.json`); the airfields' radio beacons from the DCS game files, via DCS Airfield Charts (`airfield_beacons.json`, `tools/gen_airfield_beacons.py`), with the airfields from **[pydcs](https://github.com/pydcs/dcs)** (LGPL-3.0-or-later)
- Flight Configurator, Datacard Generator: the aircraft masses (empty, maximum, gun rounds) and the equipment options of each aircraft type (`data/aircraft_masses.json`), read from DCS World and its mission editor (`tools/gen_aircraft_masses.py`)
- Flight Configurator: weapon names, permitted weapons per station, masses and aircraft limits from **[pydcs](https://github.com/pydcs/dcs)** (LGPL-3.0-or-later, `data/COPYING.LESSER`), taken from Mission Tools; the front-view aircraft drawings are by **Goldwolf** (DCS Reference Guide), used with his permission and **not** under this repository's AGPL licence — see `data/views/LICENSE.md`
- HQ: the game's flyable aircraft types offered for a squadron, from **[pydcs](https://github.com/pydcs/dcs)** 1.0.0 (LGPL-3.0-or-later, `data/aircraft_types.json`)
- DCS town names and positions from the DCS World maps, © Eagle Dynamics
- World Magnetic Model coefficients (epochs 1985–2025, the ones DCS World ships) by NOAA NCEI and the British Geological Survey, public domain
- International Geomagnetic Reference Field, 12th generation (IAGA), in the NOAA geomag70 file DCS World ships, used for years up to 1984
- Fonts embedded in every tool: Oswald, Stardos Stencil, Caveat and Roboto Mono (SIL Open Font License 1.1), Special Elite (Apache License 2.0), from Google Fonts — licence texts in [`fonts/LICENSES.md`](fonts/LICENSES.md)
- Squadron Ready Room insignia: original artwork of the project; lettering from Oswald (SIL Open Font License 1.1), converted to outlines.
- PNG and ZIP exports: [html2canvas](https://github.com/niklasvh/html2canvas) by Niklas von Hertzen and [JSZip](https://github.com/Stuk/jszip) by Stuart Knightley (MIT)
- Cold War kraft SVG file provided by Flappie, thanks to him !

---

*This project is not affiliated with or endorsed by Eagle Dynamics, the developers of DCS World.*
