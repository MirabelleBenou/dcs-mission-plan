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

### `v1.9.1`
#### Changed
- Toolbar drop-down lists follow the UI theme on the board and in every tool — no more white system menus on tablets (see below). Released together with v1.9.0.
- Embeds **Briefing Generator v2.4.5**, **Datacard Generator v1.4.1**, **HQ v0.1.1**, **Recon Station v1.0.1** and **Route Planner v1.1.1**.

### `v1.9.0`
#### Added
- Embeds **Route Planner v1.1.0** — typed waypoints, reference points, place names, DCS airfields (see below).
- Embeds **Datacard Generator v1.4.0** — reference points block (see below).

### `v1.8.0`
#### Added
- Embeds **Route Planner v1.0.0** — lay a route on a map and send it to the datacard (see below).
- Embeds **Datacard Generator v1.3.0** — imports a route from the Route Planner (see below).
#### Changed
- Six tools on the board: **Route Planner** joins the live tools, before Recon Station; the *Coming soon* row is gone.
- Cards appear in reading order, and each card tilts its own way on hover.
- Embeds **Briefing Generator v2.4.4**.

### `v1.7.0`
#### Added
- Embeds **Datacard Generator v1.2.0** — waypoints placed by heading and distance (see below). Released together with v1.5.3 and v1.6.0.
#### Changed
- Embeds **Field Manual v1.2.3**.

### `v1.6.0`
#### Added
- Embeds **Datacard Generator v1.1.0** — navigation coordinates (see below).
#### Changed
- Embeds **Briefing Generator v2.4.3** and **Field Manual v1.2.2**.

### `v1.5.3`
#### Fixed
- Embeds **Datacard Generator v1.0.2** — back to the validated layout (see below).

### `v1.5.2`
#### Fixed
- Embeds **Briefing Generator v2.4.2** — sharp logos in PNG export (see below). Released together with v1.5.1.

### `v1.5.1`
#### Fixed
- Embeds **Briefing Generator v2.4.1**, **Datacard Generator v1.0.1** and **Field Manual v1.2.1** — real bold headings and sharper PNG exports (see below).

### `v1.5.0`
#### Changed
- Embeds **Briefing Generator v2.4.0** — map, threats and targets in the quick brief, targets in the full brief, overflow pages (see below).
- Embeds **Field Manual v1.2.0** — Briefing Generator chapter updated for v2.4 (see below).

### `v1.4.0`
#### Changed
- Embeds **Field Manual v1.1.0** — Datacard Generator chapter, zoomable images and diagrams, more readable colours (see below).
- Embeds **Briefing Generator v2.3.2** — the quick-brief editor follows the language switch (see below).

### `v1.3.0`
#### Added
- **Datacard Generator** is live on the board, right after Briefing Generator (see below). Field Manual stays the last live tool.
#### Changed
- Embeds **Briefing Generator v2.3.1** — scrollable toolbar on tablets and phones (see below).
- The *Kneeboard Generator* placeholder is replaced by the Datacard Generator, on the board and in Field Manual; Route Planner is the only tool still *Coming soon*.

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

## HQ

### `v0.1.1` (beta)
#### Changed
- The theme list opens as a themed drop-down (dark olive panel, amber marks, 44 px rows), by touch or keyboard; its title follows the language.

### `v0.1.0` (beta)
Initial release. Command post for the suite.
#### Added
- **Wing hub** — single source for wing branding, squadrons and callsigns; consumed automatically by Briefing Generator and Recon Station.
- **Experimental `.miz` engine** — read a mission, export a mission snapshot (JSON), and apply **surgical patches**: scalar deltas (radio, group frequency, livery) and structural replacements (routes & payloads).
- 4 themes, FR/EN.

#### Notes
- Advanced flight-package / Commander UI is **in development** (dev-gated).
- In-game `.miz` validation in DCS is **pending** — hence the **beta** label.

---

## Briefing Generator

### `v2.4.5`
#### Changed
- The theme list opens as a themed drop-down instead of the system menu — touch and keyboard (arrows, Home/End, type-ahead, Esc).

### `v2.4.4`
#### Fixed
- On a scrolling toolbar (tablet, phone), the edge fades now blend into the bar instead of showing as two dark bands.

### `v2.4.3`
#### Fixed
- In the editor, a card's number tag (“FLIGHT 1”, “PHOTO 1”…) no longer overlaps the label above the list.

### `v2.4.2`
#### Fixed
- **Sharp logos in PNG export** — the wing and squadron logos were painted as CSS backgrounds at their on-screen size (64 px) and came out blurry in the 2× PNG; they are now real images, drawn at full resolution. On screen and in the PDF, nothing changes.

### `v2.4.1`
#### Fixed
- **No more faux bold** — page headings, table headers and flight names used *Impact*, a system font with a single weight that the browser thickened artificially (smudgy on Windows, a different font on Android). They now use the embedded **Oswald 600/700**, identical everywhere: preview, PDF and PNG. The editor chrome no longer asks for weights that aren't embedded either.
- **PNG export at 2×** — **1588 × 2246** px per page instead of 794 × 1123, whatever the screen.

### `v2.4.0`
#### Added
- **Map, threats and targets in the quick brief** — the Situation section takes a map (the full brief's SITAC map) and the threat fields (tanks, APC, AAA, SAM, note); the Mission section takes a **targets** list (number, type, position, remark). They print on a **“MAP ░ THREATS ░ TARGETS”** page right after the mission page, only when there is something to show; its banner names what it holds.
- **Targets in the full brief** — the same list, shared by both formats, prints as a table under the objectives of the Mission overview page.
- **Overflow pages** — when a mission page no longer fits, the blocks that don't fit move to a following page instead of being cut off. Page measurement no longer depends on images loading.
#### Changed
- **Threats on one line per category** — category and threats side by side, in both formats; the quick brief only shows the categories filled in.
#### Fixed
- A long *Departure* or *Aircraft* value no longer runs off the flights table.
- Missing tooltip translation on a frequency's “show in overview” box.

### `v2.3.2`
#### Fixed
- **Quick brief follows the language** — switching FR ↔ EN now also re-labels the quick-brief editor (flights, radio items, photo cards), not only the full brief.

### `v2.3.1`
#### Fixed
- **Scrollable toolbar** — on tablets (portrait or landscape) and phones, the top bar now scrolls sideways instead of running off-screen; a soft fade marks the hidden side, and every control (theme, language) stays reachable.

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

## Recon Station

### `v1.0.1`
#### Changed
- The theme list opens as a themed drop-down instead of the system menu — touch and keyboard.

### `v1.0.0`
#### Added
- Turn a screenshot into a **reconnaissance analysis photo**; native **Canvas 2D** engine (preview = export); **lossless full-resolution PNG**.
- **Sensor looks** — EO, IR white-hot, IR black-hot, SAR (stylizations, not radiometric data).
- **Image effects** — greyscale, contrast, vignette, grain, scanlines.
- **Annotations** — numbered movable markers, magnifier/loupe, shapes (ellipse, rectangle, polygon, arrow, bracket), labels (stamp, cursive, plain).
- **Editable info block** (9 fields) and **classification banner** (4 levels).
- **Wing logos** — manual upload or shared from HQ; colour / grey / white modes.
- 4 themes, FR/EN.

---

## Datacard Generator

### `v1.4.1`
#### Changed
- The theme list opens as a themed drop-down instead of the system menu — touch and keyboard.

### `v1.4.0`
#### Added
- **Reference points** — up to 12 per datacard (name, coordinates in any format, altitude, note), edited in their own section and printed in a **Reference points** block, lettered A, B, C…, in MGRS or DMS like the navigation.
- **Cascading layout** — the navigation keeps its place on page 1 while it fits; the reference points then move to page 2 on their own, and both move there only when the navigation no longer fits. A datacard without reference points lays out exactly as before.
- A route imported from the Route Planner brings its reference points along.

### `v1.3.0`
#### Added
- **Import a route** from the Route Planner — the current route or a route file — into the navigation of the datacard shown, or into a new datacard: waypoint names, MGRS coordinates, altitudes (AGL noted), units and heading reference; headings and distances are computed from the coordinates.
#### Changed
- The toolbar's **Import** button (formerly *From briefing*) takes a briefing or a route; **Import JSON** recognises route files.
- On a scrolling toolbar, the edge fades blend into the bar.

### `v1.2.0`
#### Added
- **Waypoints placed by heading and distance** — a waypoint without coordinates, next to a placed one, gets its coordinates from the heading and distance of the leg between them, forwards (from the previous waypoint) or backwards (from the next one), in a chain; shown in MGRS and DMS like typed coordinates, and flagged as estimated in the editor only.
- **Dotted DMS input** — `36.49.30N/34.44.29E` (with `/`, a comma or spaces; hemisphere before or after) is recognised.
#### Changed
- The navigation display list says **DMS**; a one-line hint lists the accepted coordinate formats.

### `v1.1.0`
#### Added
- **Navigation coordinates** — each waypoint takes coordinates, pasted as shown by the F10 map or an aircraft: MGRS, degrees-minutes-seconds, degrees-decimal minutes or decimal degrees; the editor tells whether they were recognised.
- **Three ways to show the navigation**, chosen per datacard: **heading / distance** (computed between two waypoints that have coordinates, otherwise as typed), **MGRS** (10 digits) or **degrees, minutes, seconds**.
- **True or magnetic heading** — with the variation typed in the datacard (read on the A-10C CDU, the F-16 DED or the F/A-18 HSI); the block title says which, and the variation used.
#### Changed
- The deck's move-up / move-down buttons are gone: one datacard per flight.

### `v1.0.2`
#### Fixed
- **Back to the validated layout** — text sizes, letter-spacing and line heights follow the design again (body text had grown 2–3 px larger and crowded the values); the weather block gets back its two-column grid (a value no longer runs into the next label), fuel values their dotted rules, threat chips fit on one line.
#### Changed
- **Radio** — alternating rows restart with each radio set (the first channel of each set is highlighted) and a thin rule separates two sets.

### `v1.0.1`
#### Fixed
- **PNG export at 2×** — **2000 × 2828** px per page instead of 1000 × 1414; the toolbar's bold labels use an embedded Oswald 700.

### `v1.0.0`

Initial release. One-page flight datacards for the cockpit kneeboard.

#### Added
- **One datacard per flight** — mission, times, crew, navigation, radio, airfields, weather, fuel & loadout, threats & notes; navigation moves to a second page when it does not fit.
- **Day & Night** versions, readable in VR; the suite themes only change the editor.
- **From scratch or from a briefing** — import flights from the Briefing Generator (current briefing or its JSON file), or only its general data (frequencies, airfields, METAR, objectives) when it has no flights.
- **Fully generic** — no built-in aircraft tables: radios, loadouts and units (kg/lb, km/NM, m/ft) are yours.
- **Exports** — PNG at 1000 × 1414 (drop it in DCS's kneeboard folder), ZIP for several pages, PDF (one A4 page per datacard page), and JSON import/export of the whole pack.
- Example values in empty fields, FR/EN, 4 editor themes, tablet and phone layout with scrollable bars, fully offline.

---

## Route Planner

### `v1.1.1`
#### Changed
- The **Map**, **Theatre** and theme lists open as themed drop-downs instead of the system menu — touch and keyboard; *DCS map* shows greyed out with its reason on theatres it does not cover. Tapping the map while a list is open only closes the list.

### `v1.1.0`
#### Added
- **Type a waypoint** — by coordinates (MGRS, DMS, DDM or decimal) or by heading and distance from the last waypoint (true or magnetic, km or NM).
- **Reference points** — up to 12 lettered diamonds (A, B, C…) off the route: a *Waypoint · Ref.* switch on the map chooses what a tap adds; listed in their own section and on the navigation sheet, saved in the route file, and sent to the datacard.
- **Place names** overlay (Esri World Boundaries and Places) over any layer.
- **DCS airfields and helipads** for 11 theatres (names and positions from [pydcs](https://github.com/pydcs/dcs), LGPL-3.0) — runways from zoom 7, helipads from zoom 10; tap one to add a waypoint or a reference point named after it.
#### Changed
- The toolbar scrolls at every width when it overflows.

### `v1.0.0`
Initial release. Lay a route on a map, read it, send it to the datacard.
- **Map layers** — **DCS map** (the DCS map tiles shared by the [DCS Olympus](https://github.com/Pax1601/DCSOlympus) team, on the eight theatres they cover), **topographic** (OpenTopoMap), **satellite** (Esri World Imagery) or **grid only**; the choice is yours, and offline the map falls back to grid only by itself.
- **MGRS grid** over any layer — zones and bands, 100 km squares with their letters, then 10 km and 1 km lines as you zoom in.
- **The route** — tap the map to add a waypoint, drag it to move it, a leg's "+" inserts one; name, altitude and AGL / MSL per waypoint; up to 30 waypoints, numbered from 0 like DCS.
- **Navigation sheet** — per leg, true or magnetic heading (typed variation) and distance; per waypoint, MGRS (10 digits) and DMS; total distance. Distance in km or NM, altitude in m or ft, chosen separately.
- **To the datacard** — one button opens the Datacard Generator on the route import.
- **JSON** save and open, an example route, 14 theatres, 4 themes, FR/EN, tablet and phone layouts.

## Field Manual

### `v1.2.3`
#### Changed
- Datacard Generator chapter: waypoints placed by heading and distance.

### `v1.2.2`
#### Changed
- Datacard Generator chapter: navigation coordinates and display modes; the deck buttons.

### `v1.2.1`
#### Changed
- Export sizes updated (Datacard Generator PNG: 2000 × 2828 px); the quick brief's overflow pages described exactly.

### `v1.2.0`
#### Changed
- **Briefing Generator chapter** updated for v2.4: the quick brief's map, threats and targets, the “map, threats, targets” page, targets in the full brief, overflow pages; the *what feeds what* diagram gains a **Map · threats · targets** box (C·S).

### `v1.1.0`
#### Added
- **Datacard Generator chapter** — what the tool does, what a briefing import fills in, day and night, units, exports; with an *anatomy of a datacard* diagram and a *what feeds the datacard* diagram.
- **Zoom** — click or tap any image or diagram to open it full screen; zoom up to 4× (wheel, pinch, buttons, double-tap) and pan. Diagrams stay vector-sharp.
#### Changed
- **Briefing Generator chapter** updated for v2.3: full or quick brief, blank start, the editor tabs on narrow screens; its *what feeds what* diagram now tags each section **C** (full brief) and/or **S** (quick brief).
- **Readability** — module colours now mark (bars, borders, tints) while text is written in ink: headings, links and diagram labels reach a 4.5:1 contrast in all four themes; diagram panels are lighter.
- French typography — non-breaking thin spaces before high punctuation and inside quotes.

### `v1.0.0`
#### Added
- **In-app suite documentation** — opens on the board like the other tools. One illustrated chapter per module (Recon Station, HQ, Briefing Generator); upcoming tools (Route Planner, Kneeboard) stubbed as *coming*.
- **No screenshots** — line-art SVG diagrams (one per chapter) and reused board tiles, on a "paper" surface.
- 4 themes, FR/EN, fully offline.
