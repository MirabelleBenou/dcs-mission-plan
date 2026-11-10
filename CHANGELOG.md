# Changelog

All notable changes to the **DCS Mission Plan** suite.

The suite bundles several **independently-versioned tools**, so entries are grouped per tool. Versions map to GitHub tags/releases. Format loosely follows [Keep a Changelog](https://keepachangelog.com).

---

## Unreleased

Changes merged since the last release, grouped per tool.

### All tools
#### Changed
- File buttons use the same words everywhere: **Open** and **Save** for the tool's own file, **Import** and **Export** to exchange with another tool or produce the final document, **Clear** to empty the tool. The Datacard Generator's four file buttons become Open, Import, Save and Export.
- Every file you save or export asks for its name first, with the usual name filled in; names use one date format everywhere. On tablets, HQ's flight packages and modified .miz now open the share menu, like the other files.
- Every tool's top bar follows one layout: the tool's name and what it is for (only its initials on narrow screens) in the tool's colour, the file buttons in one order (Open, Save, Import, Export, Example, Clear) with one icon per action, then the version and a drawn language flag (it no longer shows as letters on Windows). The back button uses the same type in every tool, and the dot of the wing stamp takes the tool's colour.
- On wide screens, each tool shows its own decorative stamp in the top bar, as the Briefing Generator did; it never makes the bar scroll.
- Flight packages and the mission HQ shares with the other tools now give each aircraft its own type instead of one type per group (formats `dcs-flight-package-v2` and `dcs-mission-snapshot-v2`); files in the previous format still open, their group type applying to every aircraft. The Datacard Generator and the Route Planner show a mixed flight with all its types.
- A DCS group is now called a group, not a flight, in HQ, the Route Planner, the Datacard Generator, the Flight Configurator, the Briefing Generator's quick brief and the Field Manual (“Link to a group…”, “Check shown groups”…). Format names do not change: a flight package is still a flight package.
- In HQ and the Datacard Generator, radios are named and ordered as DCS does (A-10C II, C-130J, M-2000C, OH-58D, Gazelles, F-15E, AV-8B), as in Mission Tools; for the Gazelles, only the FM radio, the one missions preset.
- One message style across the suite: a single toast at the bottom of the screen, with a coloured edge for success (green) and errors (red); errors stay on screen at least five seconds. Errors are told in plain words (“Unreadable file: this is not a .miz.”) instead of the browser's technical message. Switching language no longer shows a message; the flag's tooltip says what it does (“Switch to French”). Labels read by screen readers follow the tool's language.
- One way to confirm, export and fold across the suite: questions open in the suite's own window and their button says what will happen (“Delete”, “Clear”); loading the example or opening a file over your work no longer asks, it offers “Restore” for twelve seconds instead. Collapsible sections all use the same arrow, in the tool's colour, on the left; the whole header is clickable, a folded section shows a one-line summary, and each tool remembers what you folded. Warnings use one colour in every theme.
- One toolbar across the suite: 44-pixel buttons, the same fonts, built in (the landing page no longer loads web fonts), six text sizes, readable contrast in every theme, and a visible focus outline for the keyboard. Inside Mission Plan, each tool keeps its language flag and leaves the theme to the landing page; switching language in one tool now carries over to the others. “Side” is now “Coalition” wherever it names the coalition of a group, blue first, in the Field Manual too (the Route Planner’s symbol field keeps “Side”).
- The empty Recon Station reads at 4.5:1 in the four themes, the heading buttons of the Datacard Generator sit side by side, and its preview area shows the same focus outline as the rest.

#### Removed
- The repository no longer ships one particular wing's configuration file, nor six squadron logos that no tool used; the README and the code comments no longer name that wing. Each wing still makes or imports its own configuration in HQ.

### Mission Plan — landing
#### Added
- A card for the Flight Configurator, right after HQ.
#### Changed
- On phones (below 760 px wide), the back button shrinks to an arrow and the wing stamp is hidden, so each tool's top bar fits; a bar that is still too wide scrolls sideways, with a fade on its right edge.
#### Fixed
- On phones and tablets, the on-screen keyboard no longer hides the bottom of the open tool.

### HQ
#### Added
- **Example** button: loads a demonstration wing (Task Force Kestrel, three squadrons); your own wing configuration is kept and can be restored in one tap.
- **Flight packages**: export one or more flights of the loaded .miz (route, radios, loadout, livery) to a package file, and apply flight packages to a mission — each flight is found by its group name (spaces at either end ignored) and side, you choose what to apply per flight, and a report lists what was written. A flight may mix aircraft types: radios, loadout and livery go to an aircraft only when its type in the mission matches the package, and two groups with the same name are reported rather than guessed.
- **Dynamic Spawn**, read from the mission: templates are marked in the flight list with the airfields and FARPs they serve, and a panel lists each airfield and FARP offering Dynamic Spawn, with its template per aircraft type.
- **Delete flights** from the loaded mission: check them in the flight list, review what still points to them, and save the mission without them. Dynamic Spawn links to a deleted flight are reset; triggers, tasks and scripts that name it are listed, not changed.
- **Dynamic Spawn**, written to the mission: a flight can be made a template and linked, per aircraft type, to the airfields and FARPs that already have Dynamic Spawn enabled in the mission editor.
#### Changed
- Radios are named and numbered as in the cockpit in the mission summary and in the package messages (the Mi-24P's R-863 and R-828 start at channel 0). The .miz keeps its own numbering.
- Flight packages are recognised by their content, not their file name; unreadable flights are skipped and counted, an empty package or one without theatre is refused, with the same messages as the Route Planner and the Datacard Generator. *Load another .miz* also clears the mission offered to the Route Planner and the Datacard Generator.
- The Side and Type filters of the flight list open in the suite's own list, like every other list, instead of the system menu.
- **Wing configuration**: a squadron's aircraft are now picked from the game's flyable types (75, by their name in a .miz, from pydcs 1.0.0), grouped into helicopters and airplanes, with “Other type (mod)…” for a community mod. A name that is not a game type is marked “not in the base game”, with a “Replace with…” list of close types; nothing is blocked. The example uses the game's names (Mi-8MT, MiG-21Bis).
- Flight packages: the frequencies of a radio that missions do not preset (the Mi-24P's and Mi-8MT's HF radio) are skipped; the mission is not changed for them.
#### Fixed
- The interface language is shared with the other tools (HQ kept its own); the language already chosen in HQ is kept.

### Flight Configurator
#### Added
- **Flight Configurator**, a new module: a Flight Lead prepares a flight (identity, radios, loadout built on the aircraft's front view or started from the squadron's presets, livery) and exports it as a flight package that HQ applies to the Mission Commander's mission. Each aircraft of a flight has its own type, so a flight can mix types; flight names must be unique per side before export.
- A **Route** block above the loadout: pick one of the Route Planner's routes for the group (one route per group), then see it as a paper sketch — waypoints, names, numbered legs — with each leg's magnetic heading and distance in NM. When the route changes in the Route Planner, the group follows it; if it is deleted there, the last copy is kept.
- The Mi-24P's and Mi-8MT's HF radio (Jadro-1I, Jadro-1A), which missions do not preset: up to five frequencies, carried in the flight package and shown on the datacard, never written to the mission by HQ.
- An Example button that loads two groups (Mi-24P, Mi-8MT), with “Restore” for twelve seconds.
#### Changed
- Groups are now shared with the Route Planner: create, rename or re-route a group in either tool and the other follows at once. A group may have no unit yet. A group with no unit is exported route only.
- **Import** now also reads the Briefing Generator — its groups, their number of aircraft and the radio plan of each aircraft type, cockpit channel numbers converted — with Side, Type and Name filters. A group is completed when its name, case included, and side match; a flight of an aircraft the suite does not handle comes in as a group with its route only. An aircraft the suite does not know by the briefing's name is left for you to pick; the package exports once every type is picked. An imported route now shows in the Route Planner as the group's route.
- Radio bands follow the Mission Tools rule, keeping only what both DCS and the reference guide accept: the Mi-24P's R-863 now ends at 399.9 MHz and its R-828 at 59.9 MHz. An out-of-band frequency already in a group (imported, or typed before a band changed) is flagged but no longer blocks the export.
- Theatres are listed by their name (“Cold War Germany”), as in the Route Planner. The status bar no longer opens in red: it says what to do first, and turns red only when you try to export something incomplete.
- The theatre is picked in the toolbar, like the Route Planner and the Datacard Generator, and shared with them (all fourteen theatres). When the groups are on another theatre, a banner offers to go back to it or to keep the shared theatre and remove the groups' routes; export waits for that choice. An opened package, mission or working file sets the shared theatre.
- Route lengths follow the distance unit shared by the Route Planner and the Datacard Generator.
- Removing a group shared with the Route Planner and the Datacard Generator now asks first. “Empty the module” is now “Clear”.

### Recon Station
#### Added
- **Example** button: loads a demonstration reconnaissance photo with its markers, shapes, magnifier and info block (USDA NAIP aerial image, public domain).
#### Changed
- The top bar no longer overflows on narrow phones.
- Importing a wing configuration checks the file like HQ and the Briefing Generator, with the same messages.
- Messages no longer cover the drawing bar, and choosing a file that is not an image now says so.
- Classification uses the Briefing Generator's six levels, translated; “Import config” no longer points to the Briefing Generator.

### Briefing Generator
#### Changed
- The example loads in the interface language (French or English).
- **Load** only accepts a briefing: any other file (flight package, route, datacard) is refused with a message and the current briefing is kept.
- Export in one window: format, pages and file name together. Metadata is now the last section, folded.
#### Fixed
- In the export window, the page list no longer shows the PDF and PNG choices above it, so it fits on phones.
- A .miz the METAR assistant cannot read shows a message in the interface language instead of a French-only alert.

### Datacard Generator
#### Added
- **Mission loaded in HQ** and **Flight package** in the import window: one datacard per flight (navigation, callsign, type, radios; mission date, time and weather from HQ), filtered by side, type and name; from the Route Planner, **all routes** at once, one datacard per route. You pick the radio channels to import. A radio now holds up to 20 channels.
- The HF radio of the Mi-24P and Mi-8MT, with the frequencies chosen in the Flight Configurator or typed here: pick the ones shown on the card, with their name, as for the other radios; no channel number is printed for them.
- Airfields: pick the airfield from the theatre's list (the eleven theatres with game data; the other three offer a free name); the Datacard Generator has a theatre list like the Route Planner's, and the two modules share the theatre, which the datacard file keeps; the runway and the tower frequency in the band of the group's radio fill in, and DEP and ARR are taken from the route's first and last points, filling only empty boxes.
- Airfields: the ICAO code fills in with the runway and tower frequency when the airfield is picked from the list (today's codes, known for 292 of the 745 airfields; from OurAirports, via DCS Airfield Charts).
#### Changed
- **One datacard per group**: the Datacard Generator now shares the groups of the Flight Configurator and the Route Planner. Each group has its datacard, listed in the new card list; a group's name, side, aircraft (callsign, type, board number) and radio frequencies are edited on either side and follow at once. Radios are shown in one box per aircraft type (“RADIO — MI-24P”), a channel that differs between two aircraft of a type is marked “varies by unit”, and you pick the channels shown on the card, with their name and modulation. The loadout can be taken from the Flight Configurator as a table. Pilots, times, weather, fuel, navigation and notes stay with the datacard. **New datacard** creates a group; **Free card** keeps a datacard outside the groups, and earlier datacards open as free cards.
- The example loads in the interface language (French or English).
- Radios imported from HQ or a flight package are named and numbered as in the cockpit (the Mi-24P's R-863 and R-828 start at channel 0); an aircraft type the suite does not know keeps "Radio n" and the mission's channel numbers. With several aircraft types, the channels are chosen per type.
- **Import JSON** and the import window's **JSON file** both recognise a briefing, a route, a route set (all routes at once) and a flight package; a refused file says why.
- Day / Night reads Jour / Nuit in French.
- The crew has one line per aircraft (callsign, pilot, type, board number), filled from HQ or a flight package. When every line has a type, the group's aircraft and count follow the lines; the card's header reads “2 × Mi-24P · CAS” (or “1 × Mi-24P + 1 × Mi-8MT”) instead of “Mi-24P · FLIGHT OF 2”. A crew member saved in an older datacard is kept after the pilot's name.
- The editor has one **Group and crew** box, as in the Flight Configurator: the group (name, coalition for a group's datacard, aircraft, count, task, threat), then one card per aircraft (callsign, type, board number, pilot). A group's datacard and a free card now show the same boxes in the same order — the order of the printed datacard — on desktop and in the phone's tabs; the units move to **Meta**. A mixed group's aircraft read "Mi-24P + Mi-8MT" on both.
- The datacard always keeps all its blocks, even empty ones, so it can be printed and filled in by hand: an empty block shows its headings and a few blank lines (three mission steps, four crew rows, five navigation points, two reference points, four radio channels, the departure, arrival and alternate airfields, the weather labels, Joker and Bingo, two lines for the loadout and two for notes). A block with data is unchanged; a full datacard may now take two pages.
- Units (mass, distance, altitude) apply to every card and are shared with the Route Planner.
- Airfields box: airier columns with light separators and one text size. Picking an airfield from the list replaces its ICAO code, runway and tower frequency, even typed ones ("Other…" clears them); the runway is a single end, picked from the airfield's list, the one facing the Weather wind first.
- Weather box: a light separator between its two columns, and a slightly smaller METAR, which now fits on one line in most cases.
- A datacard's navigation is now a Route Planner route, edited from both sides: a waypoint entered (coordinates, or course and distance), moved or removed in one tool changes in the other; time and note stay with the datacard, attached to each waypoint. A card without a route gets one at its first position. Course settings (true or magnetic, variation, year) are shared with the Route Planner. Reference points are the Route Planner's, shared by the whole mission; each datacard chooses which ones it shows.
- Export in one window: format, pages and file name together. Rarely used sections (meta, airfields, fuel, threats) start folded.
- True or magnetic heading is now two buttons, as in the Route Planner.
- A lighter top bar: Day | Night and the units move into **Display ▾**, and **Open ▾** opens a datacard or imports. Datacards are chosen on one line — the card's name with its tag, “+” for a new datacard, “…” for a free card, attach, import groups, duplicate and delete; the list groups linked and free cards, and two cards of the same name read “CAESAR” and “CAESAR · 2”.
#### Removed
- The Datacard Generator's own HQ and flight package imports, replaced by the common import window of the Flight Configurator and the Route Planner.
#### Fixed
- In the export window, the page list no longer shows the PDF and PNG choices above it, so it fits on phones.
- Computed magnetic variation now follows DCS for every mission date: years up to 1985 use the IGRF model DCS ships (up to 1.2° closer), later years the previous five-year WMM file, as DCS does (0.2° closer in 1990, 1995 … 2025).
- Changing the language with the briefing import window open keeps the phases you picked; opening the window again starts from the card's own group.
- A frequency field you had only clicked into now shows a frequency changed meanwhile in the Flight Configurator.
- A group name, callsign or board number field you had only clicked into now shows a change made meanwhile in the Flight Configurator, instead of writing the old value back.
- Airfield search on phones and tablets: the list stays above the on-screen keyboard.

### Route Planner
#### Added
- **Ruler** mode on the map: tap to measure, segment by segment, each with its heading (true or magnetic, like the navigation) and distance in the chosen unit, and the total; taps snap to waypoints, reference points and airfields; nothing is saved.
- **Several routes**, one per flight: a route list in the Route section, the other routes drawn faintly on the map; **Import** (the mission loaded in HQ, or a flight package sent by the mission commander) turns groups into routes, filtered by side, type and name, and **Flight package** exports linked routes to a package that HQ applies to the mission (untouched waypoints keep their original data). **Save** is now a menu (selected route, all routes), and every save asks for the file name first. **Clear** lets you pick what to clear (selected route, all routes, reference points, drawings, NATO symbols, imported layers) or clear everything.
#### Changed
- Units (distance km or NM, altitude m or ft) are chosen with the base map in the **Display** menu; the Theatre list is as wide as the option chosen.
- The example loads in the interface language (French or English).
- **Open** and **Flight package** also read a flight package in a .zip; a flight without route says *no route*; a refused file says why.
- Each route now has a stable identifier in the route set (saved files included), so other tools can follow it.
- **Groups…** replaces “Link to a group”: tick the groups that follow the route, or create one. Imports from HQ or a flight package attach each route to its group, creating it if needed; the flight package exports one flight per group.
- **Import** replaces “From HQ” and “Flight package”: the same window as the Flight Configurator (mission loaded in HQ, current briefing, flight package .json or .zip, briefing file), bringing the group's aircraft, radios, loadouts and liveries along with its route. A route imported in the Flight Configurator is added here as its group's route.
- The theatre is shared with the Datacard Generator: changing it in one module changes it in the other.
- Units are shared with the Datacard Generator.
- Each route keeps its theatre: switching theatre hides the routes of the other theatres (kept, back when you return), and the Flight Configurator only offers the routes of the shared theatre.
- A saved route set keeps every route's theatre, across all theatres; opening it puts each route back on its own theatre and replaces the whole set.
- Routes can be edited from the Datacard Generator; each waypoint keeps a stable identifier; course settings are shared with the Datacard Generator.
- A lighter top bar: the base map and the units move into **Display ▾**, above what the map shows (that menu's former “Base map” group is now “Overlays”); **Open ▾** opens a route or imports routes, and the Import button leaves the panel. Routes are chosen on one line — the route's name, “+” for a new route, “…” to duplicate or delete — and the next steps (to the datacard, to the briefing, flight package, save, Route Tool) now follow the points instead of closing the Navigation section.
#### Fixed
- Computed magnetic variation now follows DCS for every mission date: years up to 1985 use the IGRF model DCS ships (up to 1.2° closer), later years the previous five-year WMM file, as DCS does (0.2° closer in 1990, 1995 … 2025).

### Field Manual
#### Added
- A **Flight Configurator** chapter.
- **Getting started** on the index page: every tool's Example button.
#### Changed
- HQ and Recon Station chapters: the Example button.
- The Route Planner chapter names the magnetic models DCS uses: IGRF up to 1985, then WMM.
- The Datacard Generator chapter lists the editor's boxes in their new order, with **Group and crew**.
- The Flight Configurator chapter: the helicopters' HF radio and the bands.
- The Datacard Generator chapter: empty blocks are kept.
- The Datacard Generator chapter: the airfield list.
- The Flight Configurator, Datacard Generator and Route Planner chapters: shared theatre and units.
- The Datacard Generator and Route Planner chapters: navigation shared with the route, shared course settings.
- The Route Planner and Datacard Generator pages follow their new Display and Open menus and their one-line route and datacard selection.

---

## Mission Plan — landing

- Operational **"situation board" landing page** that embeds the live tools (HQ, Briefing Generator, Recon Station) in isolated frames and stages the upcoming ones as *Coming soon*.
- **4 themes** (Cold War NATO / Soviet, Modern NATO / Eastern Bloc) and **FR/EN** carried across the whole suite from the board.
- **Online and offline** — published as a hosted page and as a single offline HTML file.
- **Tablet & mobile** first-class target (touch, drag, rotation-safe).
- Wing configuration shared automatically across embedded tools.

### `v1.24.0`
#### Added
- Embeds **Field Manual v1.3.0** — a Route Planner chapter (see below).
#### Changed
- Embeds **Route Planner v1.13.1** — airfield chart sheets say they are loading and fetch their other pages in the background (see below).

### `v1.23.0`
#### Added
- Embeds **Route Planner v1.13.0** — tap an airfield or heliport in Read mode to open its chart sheet (see below).

### `v1.22.0`
#### Added
- Embeds **Briefing Generator v2.6.0** — an optional radio name and channel on each frequency of the quick brief (see below).
#### Changed
- The board shows its tools in a new order: HQ, Route Planner, Briefing Generator, Datacard Generator, Recon Station, Field Manual.

### `v1.21.1`
#### Changed
- Embeds **Route Planner v1.12.1** — a *Display* menu, and the map stays fixed below 1,100 px wide in every orientation (see below).

### `v1.21.0`
#### Added
- Embeds **Route Planner v1.12.0**, **Briefing Generator v2.5.0** and **Field Manual v1.2.4** — send the framed map view from the Route Planner to the briefing (see below).
- The board relays the map image from the Route Planner to the Briefing Generator, in memory only.

### `v1.20.0`
#### Added
- Embeds **Route Planner v1.11.0** — NATO military symbols (APP-6) in drawn layers (see below).

### `v1.19.1`
#### Fixed
- Embeds **Briefing Generator v2.4.7** — neutral example reference, and remove buttons that stay inside editor rows (see below).

### `v1.19.0`
#### Added
- Embeds **Route Planner v1.10.0** — Flappie's navigation chart as a background on the Caucasus, and DCS map tiles served from a public host before DCS Olympus (see below).

### `v1.18.1`
#### Changed
- Embeds **Route Planner v1.9.1** — the map/panel divider also in short landscape windows (see below).

### `v1.18.0`
#### Added
- Embeds **Route Planner v1.9.0** — the DCS map can come from a tile mirror on the hosting server, with DCS Olympus as fallback (see below).

### `v1.17.1`
#### Fixed
- Embeds **Route Planner v1.8.1** and **Datacard Generator v1.5.1** — magnetic variation before 1985 like DCS (see below).

### `v1.17.0`
#### Added
- Embeds **Route Planner v1.8.0** and **Datacard Generator v1.5.0** — magnetic headings computed like DCS (see below).

### `v1.16.1`
#### Changed
- Drop-down lists in the tools' forms follow the UI theme too — no more white system menus on tablets (see below).
- Embeds **Briefing Generator v2.4.6**, **Datacard Generator v1.4.2**, **Recon Station v1.1.1** and **Route Planner v1.7.1**.

### `v1.16.0`
#### Added
- Embeds **Recon Station v1.1.0** — annotations drawn by touch (see below).

### `v1.15.0`
#### Added
- Embeds **Route Planner v1.7.0** — orbits, kill boxes, curves, FLOT and corridors by touch (see below).

### `v1.14.0`
#### Added
- Embeds **Route Planner v1.6.0** — touch drawing in layers, resizable map in portrait (see below).

### `v1.13.0`
#### Added
- Embeds **Route Planner v1.5.0** — DCS towns and map search (see below).

### `v1.12.0`
#### Added
- Embeds **Route Planner v1.4.0** — CombatFlite layers (see below).

### `v1.11.0`
#### Added
- Embeds **Route Planner v1.3.0** — leg boxes, ground speed and minute marks (see below).

### `v1.10.0`
#### Added
- Embeds **Route Planner v1.2.0** — DCS Route Tool import and export (see below).

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

### `v2.6.0`
#### Added
- **Radio name and channel on each frequency of the quick brief**, both optional: under each frequency line of the editor, then in a column between the label and the frequency on the mission page (`R-863 · CH 3`; a channel made of digits only is shown as `CH 3`). The column appears only when at least one line has a radio or a channel — otherwise the page is unchanged. The full brief keeps both fields without showing them.

### `v2.5.0`
#### Added
- **Receive a map from the Route Planner**: a window asks where to place it — in the quick brief, the map · threats · targets page or a photo page; in the full brief, the SITAC map, the cover map, a mission's documents or a new annex page. A map already in place is replaced only after confirmation.
#### Fixed
- A full browser storage is now reported (a toast) instead of failing silently to save the briefing.

### `v2.4.7`
#### Fixed
- The example placeholder of the document reference field and the reference of the loaded example are now neutral (`FH-M3-1989`); the example's phases no longer carry a squadron that the default wing config does not have.
- The × remove button no longer overflows the right edge of airfield and radio-item rows in the editor — airfields on tablets and desktops, radio items on phones — in both the full and the quick format; the button keeps its 44 px touch size.

### `v2.4.6`
#### Changed
- Form drop-down lists (classification, threat, units, radio items, airfield role, imagery, altitude reference…) open as a themed list instead of the system menu, in the field's own font — touch and keyboard; a list near the bottom of the screen opens upwards.

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

### `v1.1.1`
#### Changed
- Form drop-down lists (classification, threat, units, radio items, airfield role, imagery, altitude reference…) open as a themed list instead of the system menu, in the field's own font — touch and keyboard; a list near the bottom of the screen opens upwards.

## Recon Station

### `v1.1.0`
#### Added
- **Annotate by touch** — a drawing bar sits on the image: *Select · Frame · Ellipse · Polyline · Arrow · Bracket · Text · Loupe*. One tap places, large handles adjust: frames and magnifiers resize by their four edges and their four corners (the opposite side or corner stays put), frames rotate by their own handle, the magnifier's inset keeps the proportions of its source and stays inside the image. *Settings*, *Copy*, *Delete* and *OK* on the bar, as in the Route Planner; settings can be changed while you create.
- The image is never hidden under the drawing bar, on a computer as on a tablet.

#### Changed
- *Add a magnifier* moves from the *Legend* section to *Shapes*.
- The export is unchanged: the same annotations give the same PNG.

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

### `v1.5.1`
#### Fixed
- Before 1985, the magnetic variation extends the 1985 model back in time with its secular variation, like DCS, instead of staying at its 1985 values (Cold War Germany, 1961: about −4° instead of −1°). From 1985 on, nothing changes.

### `v1.5.0`
#### Added
- **Magnetic variation computed like DCS**: with the magnetic heading, a new *Variation* setting — *Computed* or *Entered*. Computed uses the World Magnetic Models DCS World ships (epochs 1985–2025), leg by leg at each leg's start point, for the year of the card's *Date* field (1985 when empty).
- The printed navigation header shows the year and the range: *NAVIGATION · MAGNETIC HEADING · VAR 1989 (−1.6 to −0.2°)*.
- A route sent from the Route Planner brings its variation mode, and its year when the card's *Date* is empty.
#### Changed
- A card saved with a typed variation opens in *Entered* mode, unchanged.

### `v1.4.2`
#### Changed
- Form drop-down lists (classification, threat, units, radio items, airfield role, imagery, altitude reference…) open as a themed list instead of the system menu, in the field's own font — touch and keyboard; a list near the bottom of the screen opens upwards.

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

### `v1.13.1`
#### Changed
- Airfield chart sheets: a loading message while the sheet and its page arrive; the other pages are fetched in the background once the first one is shown, so switching tabs is immediate.

### `v1.13.0`
#### Added
- **Airfield and heliport sheets**: in Read mode, tapping an airfield or a heliport opens its chart from **DCS Airfield Charts**, served by the wing's server — one tab per page (10-9, 10-9A…), pinch to zoom, double-tap to reframe; a heliport opens on its box of the heliport directory. When a field has no sheet, the viewer says so; when the server does not answer, it says the sheets are unavailable. Point and Ref. modes are unchanged.

### `v1.12.1`
#### Added
- **Display menu** in the top bar: show or hide the route, reference points, drawings, NATO symbols, imported layers, MGRS grid, towns, airfields and places — it replaces the four toggle buttons; a dot marks the button when something is hidden. A hidden element comes back when you switch to the mode that edits it, and the choices are remembered.
#### Changed
- Below 1,100 px wide, **the map stays fixed in every orientation** (short landscape windows included — e.g. unfolded phones) and only the panel scrolls; the divider sets the map height (140 px minimum in short landscape). While typing in the panel with the on-screen keyboard up, the map shrinks to its minimum and comes back afterwards.

### `v1.12.0`
#### Added
- **→ To the briefing**: frame the map (3:2 landscape or 2:3 portrait, pan and zoom under the frame) and export what the screen shows — background, grid, route, leg boxes, minute ticks, layers and NATO symbols — as a 1,600 px JPEG with a caption band (route name, theatre, scale bar in the route's distance unit), a north arrow and the background's attribution. In the suite it goes straight to the Briefing Generator; standalone, the image is downloaded.

### `v1.11.0`
#### Added
- **NATO military symbols (APP-6)** in drawn layers — a ninth drawing tool, *Symbol*: tap the map to place it, then set it in its sheet: side (friend, hostile, neutral, unknown), style (filled in APP-6 colours, or outlined in the side's colour), size (S, M, L, fixed on screen), the symbol itself from a catalogue — units (infantry, mechanised infantry, armour, recon, artillery, air defence, helicopters, engineers, logistics) with their echelon (platoon to division) and higher formation, equipment (tank, IFV, SAM, AAA, radar), aircraft (fixed-wing, fighter, attack, bomber, transport, helicopter, attack helicopter) and the FARP — and its designation.
- A new symbol starts from the settings of the last one; symbols are copied, moved and deleted like the other objects, open their card in *Read* mode (with *→ Reference point*), add a route point when tapped in *Point* mode, and are saved and exported with the layers.
- Symbols are drawn with [milsymbol](https://github.com/spatialillusions/milsymbol) (MIT), embedded in a reduced build.

### `v1.10.0`
#### Added
- **Flappie's navigation chart on the Caucasus** — a new *Background* choice, *Navigation chart (Flappie)*, offered on the Caucasus only: roads, railways, rivers, towns, forests, airfields and navaids drawn like an aeronautical chart, sharp up to zoom 12 and enlarged beyond. Credit *Map © Flappie* at the bottom of the map — many thanks to him. The chart already prints town names, so the *Towns* button is greyed out under it; your setting comes back on any other background.

#### Changed
- **DCS map tiles from a public host first** — opened outside a hosting page (the hosted page on GitHub, or the offline file), the *DCS map* now asks a public copy of the DCS Olympus tiles first (with their agreement), then DCS Olympus tile by tile; Germany Cold War gains zoom 16 there too. Inside a hosting page that provides its own tile mirror, nothing changes.

### `v1.9.1`
#### Changed
- **The map/panel divider in short landscape windows too** (under 1,100 px wide and under 600 px high — a foldable phone unfolded and turned, for instance): the page still scrolls, and the divider sets the map height between 220 px and 85% of the window below the top bar. Its height is remembered apart from the portrait one (`rp_split_land_v1`), so turning the device keeps both; a double tap restores the original height. Portrait and wide layouts are unchanged.

### `v1.9.0`
#### Added
- **DCS map tiles from a mirror on the hosting server.** When the page that hosts the suite provides a same-site tile mirror (`localStorage` key `map_layers_v1`, `{"configSchemaVersion":1,"dcs":{"url":"/…/{key}/{z}/{x}/{y}.png"}}`), the *DCS map* layer asks the mirror for each tile and falls back to DCS Olympus tile by tile when the mirror does not have it. If the mirror fails repeatedly without a single success (an expired session, say), the page goes straight to Olympus until it is reloaded. Without that key — the hosted page, or the file opened locally — tiles come from DCS Olympus as before.
- **Cold War Germany at level 16** through the mirror only: one more layer, sharper from zoom 16; where a level-16 tile is missing, level 15 shows underneath.

### `v1.8.1`
#### Fixed
- Before 1985, the magnetic variation extends the 1985 model back in time with its secular variation, like DCS, instead of staying at its 1985 values (Bitburg, June 1965: −4.9° instead of −2.2°). From 1985 on, nothing changes.

### `v1.8.0`
#### Added
- **Magnetic variation computed like DCS**: in the Navigation panel, *Variation — Computed · Entered*. Computed uses the World Magnetic Models DCS World ships (epochs 1985–2025), leg by leg at each leg's start point — matching the mission editor's readings to 0.1°.
- The year comes from the mission loaded in HQ when it is on the same theatre, otherwise from the *Year* field; *Override* puts the typed year first; 1985 by default. The panel says where the year comes from.
- Each point of the navigation table shows its variation; the title shows the year and the range: *NAVIGATION — MAGNETIC HEADING · VAR 1985 (−2.1 to −0.7°)*.
#### Changed
- A route saved with a typed variation opens in *Entered* mode, unchanged. Headings typed for *+ Point* by heading & distance use the variation of the point you start from.

### `v1.7.1`
#### Changed
- Form drop-down lists (classification, threat, units, radio items, airfield role, imagery, altitude reference…) open as a themed list instead of the system menu, in the field's own font — touch and keyboard; a list near the bottom of the screen opens upwards.

## Route Planner

### `v1.7.0`
#### Added
- **Orbits** and **kill boxes** in *Draw* mode. An orbit is set by its two ends and its width; drag the width handle to the side you want to turn to. A kill box shows its grid (3 × 3 by default, set in *Settings*), resizes by its four edges and its four corners — the opposite side or corner stays put, live size in NM — and rotates by its own handle.
- **Curves, FLOT and corridors** — a zone can be drawn straight or curved, a line can be a plain line, a FLOT or a corridor; chosen in *Settings*, the corridor's width is dragged on the map.
- **Settings while you create** — choosing a tool opens the settings of the shape to come, placed above the message so the map stays visible.

## Route Planner

### `v1.6.0`
#### Added
- **Draw mode** — a fourth button next to *Waypoint · Ref. · Read*: draw your own layers by touch — circles, zones, lines, typed points (target, DMPI, exit point, LZ…) and text. One tap places, a handle adjusts: drag a circle's radius (shown live in NM), move vertices, tap a "+" to insert one, move the whole shape. *Settings* for name, colour, line style and fill; *Copy* and *Delete*. The route fades while you draw and stays untouched.
- **Your own layers** — create and name layers, choose the one you draw in; CombatFlite layers stay read-only, and *Copy to draw* turns one into an editable copy. Drawn layers are saved in the browser and travel in the exported file.
- **Resizable map in portrait** — drag the bar between the map and the panel to give the map more or less room; double-tap it to restore the default. The size is remembered.

#### Changed
- The "map unavailable" banner no longer slides under the tap-mode control on phones.

### `v1.5.0`
#### Added
- **DCS towns** — the names of the towns of the DCS maps (Caucasus, Germany Cold War, Syria) appear from zoom 10, without overlapping each other or your route: towns close to the route first, major towns in bold. They work offline. A **Towns** button turns them on or off. Tap a town to make it a waypoint or a reference point, like an airfield.
- **Map search** — a magnifier under the zoom buttons: type two letters to find a town, an airfield or helipad, a waypoint, a reference point or a layer item (accents ignored); pick a result to centre the map on it, marked by a pulsing ring.

#### Changed
- In *Read* mode the leg insertion "+" handles are hidden; a CombatFlite ring without altitude no longer shows "0".

### `v1.4.0`
#### Added
- **CombatFlite layers** — *Open* now also reads a CombatFlite mission file (`.cf`): pick the layers you want and they are drawn on the map, read-only — threat rings, zones (lines, curves, FLOT, corridors), orbits, kill boxes with their grid, targets and other points, text boxes — with CombatFlite's colours (fills softened so the route stays readable). The theatre follows the file.
- A **Layers** section lists them: show or hide each one, remove one or all. Layers are kept in your browser, apart from the route.
- **Read** mode on the map switch (*Waypoint · Ref. · Read*): tap a layer item to read its card; a point's card can turn it into a reference point. In *Waypoint* or *Ref.* mode, layers let taps through, and a tapped target becomes a waypoint or a reference point named after it — like an airfield.
- **Export** lets you choose what the route file carries: the route, and any of the layers. A file with layers and no route adds its layers without touching your route.

### `v1.3.0`
#### Added
- **Leg boxes** — a house-shaped box on each leg: the name of the waypoint it leads to, heading, distance, ground speed, altitude and ETE (*Full*), or heading and distance only (*Minimal*). Each box lies along its leg with its roof pointing the way you fly, text always upright; drag it out of the way and it keeps its place, even when the leg moves. *None* brings back the plain heading · distance label.
- **Ground speed** — one default speed for the route and an optional speed per leg, in km/h or knots following the distance unit.
- **Minute marks** — a tick at every minute of each leg, longer every five minutes, and the **elapsed time** under each waypoint (`00+21+05`); ETE per leg and total time on the navigation sheet.
- **Route line** and **minute marks** in the route colour or in black — your choice, kept in your browser.
#### Changed
- The route file (`dcs-route-v1`) also keeps the ground speeds, the box style and where each box was dragged; older files open with the defaults.

### `v1.2.0`
#### Added
- **DCS Route Tool** — *Open* now also reads a Route Tool file (`Saved Games\DCS\Config\RouteToolPresets\<map>.lua`): pick the theatre (guessed from the file name) and one of its routes. **Export to the Route Tool** adds the route to your existing `<map>.lua` — every other route kept byte for byte — or writes a new file; no timing is written, DCS computes it. Coordinates use each map's DCS projection (11 theatres, from [pydcs](https://github.com/pydcs/dcs)); reference points are not exported.
#### Changed
- **Portrait tablets and phones**: the map stays in place and only the panel below it scrolls, the on-screen keyboard included.
- *Open* accepts any file and recognises it by its content.

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

### `v1.3.0`
#### Added
- **Route Planner chapter** — theatre and base maps, tap modes, building the route, reference points, leg boxes, navigation and magnetic variation (with the DCS editor ruler caveat), airfield chart sheets, drawing layers and NATO symbols, CombatFlite layers, hand-off to the Datacard and Briefing Generators, DCS Route Tool, tablet layout; two new diagrams.
#### Changed
- Datacard Generator chapter: importing navigation from the Route Planner.

### `v1.2.4`
#### Changed
- Briefing Generator chapter: the map can come from the Route Planner.

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
