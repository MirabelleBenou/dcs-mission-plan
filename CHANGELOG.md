# Changelog

All notable changes to the **DCS Mission Plan** suite.

The suite bundles several **independently-versioned tools**, so entries are grouped per tool. Versions map to GitHub tags/releases. Format loosely follows [Keep a Changelog](https://keepachangelog.com).

---

## Mission Plan — landing

- Operational **"situation board" landing page** that embeds the live tools (HQ, Briefing Generator, Recon Station) in isolated frames and stages the upcoming ones as *Coming soon*.
- **4 themes** (Cold War NATO / Soviet, Modern NATO / Eastern Bloc) and **FR/EN** carried across the whole suite from the board.
- **Online and offline** — published as a hosted page and as a single offline HTML file.
- **Tablet & mobile** first-class target (touch, drag, rotation-safe).
- Wing configuration shared automatically across embedded tools.

### `v1.2.0`
#### Changed
- Embeds **Briefing Generator v2.3.0** — full or quick brief, blank start (see below).

### `v1.1.0`
#### Added
- **Field Manual** — a new in-app documentation tool, staged on the board like the others: one illustrated chapter per module (HQ, Briefing Generator, Recon Station), line-art diagrams, FR/EN, fully offline.
- **Live theme propagation** — changing the theme on the board (or in a tool) now updates every open tool instantly.
- **Wing stamp in toolbars** — each tool's top bar shows the wing short name with a pulsing accent dot, read from the shared wing config.
#### Changed
- The board now stages **4 live tools** (HQ, Briefing Generator, Recon Station, Field Manual) in a 2×2 layout; canonical tile order HQ · BG · RS · FM.
#### Internal
- Briefing Generator build **unified** into a single `build_briefing_generator.py` (output renamed `dcs_briefing_generator.html`); the read-only-wing (P1.B) sources were reconstructed against the published build — **no functional change** (byte-identical output).

---

## HQ — `v0.1.0` (beta)

Initial release. Command post for the suite.

### Added
- **Wing hub** — single source for wing branding, squadrons and callsigns; consumed automatically by Briefing Generator and Recon Station.
- **Experimental `.miz` engine** — read a mission, export a mission snapshot (JSON), and apply **surgical patches**: scalar deltas (radio, group frequency, livery) and structural replacements (routes & payloads).
- 4 themes, FR/EN.

### Notes
- Advanced flight-package / Commander UI is **in development** (dev-gated).
- In-game `.miz` validation in DCS is **pending** — hence the **beta** label.

---

## Briefing Generator

### `v2.3.0`
#### Added
- **Full or quick brief** — a toolbar switch between the full dossier (unchanged) and a new **quick brief**: one page with the situation, the mission and a flight table (flight, aircraft, task, departure), frequencies, airfields and weather, followed by recon photo pages, two photos per page. Both modes share the same data, so switching never loses anything.
- **Example** button — loads the former demonstration briefing.
- Optional mission time (Z) in the quick-brief banner.
#### Changed
- **Blank start** — the tool now opens on an empty briefing, in quick mode; **Reset** clears to a blank page. Existing briefings open unchanged, in full mode.

### `v2.2.0`
#### Added
- **Bilingual UI** — full FR/EN internationalization.
- **Radio plan**, **METAR assistant**, **import METAR from a `.miz`**, structured airfields.
- **Per-page PNG export** and PDF size optimization.
#### Changed
- Wing branding is now **consumed from HQ** (the dedicated wing tab became read-only).

### `v2.0.0`
#### Added
- Initial offline briefing generator: multi-section editor (cover, SITAC, charts, annexes, phases).
- 4 graphic themes, native PDF export, multi-wing management via JSON.

---

## Recon Station — `v1.0.0`

### Added
- Turn a screenshot into a **reconnaissance analysis photo**; native **Canvas 2D** engine (preview = export); **lossless full-resolution PNG**.
- **Sensor looks** — EO, IR white-hot, IR black-hot, SAR (stylizations, not radiometric data).
- **Image effects** — greyscale, contrast, vignette, grain, scanlines.
- **Annotations** — numbered movable markers, magnifier/loupe, shapes (ellipse, rectangle, polygon, arrow, bracket), labels (stamp, cursive, plain).
- **Editable info block** (9 fields) and **classification banner** (4 levels).
- **Wing logos** — manual upload or shared from HQ; colour / grey / white modes.
- 4 themes, FR/EN.

---

## Field Manual — `v1.0.0`

### Added
- **In-app suite documentation** — opens on the board like the other tools. One illustrated chapter per module (Recon Station, HQ, Briefing Generator); upcoming tools (Route Planner, Kneeboard) stubbed as *coming*.
- **No screenshots** — line-art SVG diagrams (one per chapter) and reused board tiles, on a "paper" surface.
- 4 themes, FR/EN, fully offline.
