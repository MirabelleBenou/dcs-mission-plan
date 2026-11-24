# Changelog

All notable changes to the **DCS Mission Plan** suite, newest first.

Each release is a GitHub release tagged `MP-V<major>.<minor>.<patch>`; the whole suite has had one version number since 2.0.0:
- **major**: a redesign, or a file format that breaks;
- **minor**: a new tool, screen or function, or a change visible everywhere;
- **patch**: fixes.

Between two releases, the hosted version shows its build number at the bottom of the home screen — `MP-V2.1.0+3` is the third update since 2.1.0. A released file shows none.

Further down, *Before v2.0.0* keeps the history of each tool up to v1.24.0, when every tool still had its own version. Format loosely follows [Keep a Changelog](https://keepachangelog.com).

## Unreleased

### All tools

**Build number on the hosted version**
- Between two releases, the bottom of the home screen shows the build number, `MP-V2.1.0+13` for this one; a downloaded release shows none.

**Easier-to-read drop-down lists**
- Their header, the chosen line and the line under the pointer have stronger contrast in every theme.

**Aircraft types under their designation**
- Types are shown as F/A-18C rather than FA-18C_hornet; packages, missions and the work file still store the game’s type name.
- Type lists are grouped (helicopters, then planes) and can be searched.

**A toolbar that no longer scrolls on a phone**
- What does not fit moves into a “⋯” menu at its right end, last item first; the back arrow, the abbreviation, the file buttons and Display always stay.

**Back closes one level at a time on a phone**
- The back gesture or button closes an open menu or window first, then the tool, back to the suite's home screen; only from the home screen does it leave Mission Plan.
- The address names the open tool, so reloading reopens it. Pull-to-refresh is off.

**Easier to touch with a finger**
- On a touch screen, every button, list and field is at least 44 px tall and wide; with a mouse nothing changes.
- On a phone, fields use 16 px text, so the page no longer zooms in when you type (between 520 and 760 px wide, the Route Planner’s waypoint rows still use smaller text).

**Greyed-out commands say why**
- In the “⋯” menu, a command that cannot be used shows the reason under it, such as HQ’s Example when the Wing configuration is provided by another tool.

**Switch tools from the toolbar**
- The tool’s name or abbreviation at the start of the toolbar, with ▾, opens the list of tools in the home screen’s order, the open one marked; one more touch opens another tool, which keeps its work.

**Seven tabs at the bottom on a phone**
- In the Briefing Generator and the Datacard Generator, the editor’s tabs all fit at the bottom of the screen, seven of the same width, in both formats of the briefing; a tab that groups several sections shows each of them, foldable, without repeating its title.

**Switching tools: finishing touches**
- With the list of tools or “⋯” open, a touch on another menu of the toolbar opens it; the tool’s name follows a language change at once and screen readers hear the name shown.

**The tab bar steps aside for the keyboard**
- On a phone, while the on-screen keyboard is open, the tab bar at the bottom of the Briefing Generator, the Datacard Generator and the Route Planner hides, so the field you type in stays in view; in the Route Planner, a search on the map gets the whole height.

**The Squadron Ready Room family insignia**
- Every page of the suite carries the family's icon in the browser tab and when pinned to a phone's home screen.
- The default wing logo, in HQ and the Briefing Generator, is now the Squadron Ready Room insignia; a wing still on the former “WG” logo shows the new one and still counts as not set up.

**Fixed: “⋯” on very narrow screens**
- Below 345 px wide, after the toolbar was scrolled, “⋯” could end up off the screen; it now stays in view.

**Menus easier to read from the keyboard**
- In the toolbar's menus, the line reached with the arrow keys now has enough contrast in every theme.

### Home screen

**The top bar fits on a phone**
- What does not fit, theme and language, moves into a “⋯” menu at its right end, as in the tools; the theme name is no longer cut.

**The Mission Plan insignia**
- The home screen shows the Mission Plan insignia beside its title — on a phone, as a seal on the title's corner — and the family's icon in the top bar; when the Squadron Ready Room opens Mission Plan, your wing's emblem takes its place.
- A *Squadron Ready Room family* line sits above the credits.

### HQ

**No more “Application title” field in the Wing window**
- No tool used it; a Wing configuration that has one still opens and keeps it.

**Liveries of every aircraft type in the Wing window**
- The Wing window offers the game liveries of every aircraft type found in DCS (68 types), not only the four of the Flight Configurator.
- Its “Add a type…” list can be searched.

**Create a flight that the mission lacks**
- Tick “Create this flight in the mission”, pick the country (and the coalition if the package has none) and start in the air or on the ground at the route’s first waypoint.
- A flight without a route, or mixing helicopters and airplanes, is not created and HQ says why.

**Created flights start as the Flight Configurator set them**
- On their stands, cold or engines running, or at the route's first waypoint.
- A stand already taken in the mission is replaced by the nearest free one that fits, which you can change.

**Loadouts keep what the Flight Configurator does not set**
- Applying a flight package keeps the gun ammunition belt chosen in the mission editor and the restricted weapons as they were.

**Equipment options written to each aircraft**
- The options set in the Flight Configurator are written to each aircraft, in found and created flights; the mission's own options go to the Flight Configurator with the loadout.

**A warning before leaving with a mission open**
- The browser asks before the page is closed, reloaded or left: the mission is not kept after that.

**The Wing button keeps its place**
- The Wing button now always sits between Flight packages and Example, whether or not the wing is set up; until it is, the button stays highlighted.

**A clearer warning on a created flight**
- When a package creates a flight, a waypoint that pointed to a unit of the package’s mission is reported as removed, no longer as to be checked.

### Flight Configurator

**Every flyable aircraft of the game (75 types)**
- Any of them can be configured, imported and kept as a preset, not only the Mi-24P, Mi-8MTV2, F-4E and Mirage F1EE.
- What a type lacks is said on screen: no radio preset in the mission editor, radio band not checked, no loadout, no front view, no game livery.

**As many radio channels as the mission editor**
- Each radio offers as many channels as the mission editor writes for the type.

**Start from an airfield**
- Pick the departure base, the start (on the stand, cold or engines running; or at the route's first waypoint) and a stand for each aircraft, from a list or on the airfield map drawn by DCS Airfield Charts.

**Take-off mass like the DCS mission editor**
- Gun rounds count at the gun percentage, and so do the aircraft's equipment options (IR exhaust suppressors, extra armour, cargo door, water or MW-50 tanks, solo flight…), which you can now set for each aircraft.
- The gun field only shows on aircraft that have a gun (#6).

**Fold or unfold everything at once**
- In a group of two units or more, the icon at the right of a unit’s header folds or unfolds all the units of the group.
- The icon at the right of a group’s header folds or unfolds all the groups, now even when there is only one.

**A warning when exporting a flight without a route**
- HQ will not be able to create it if the mission lacks it.

**Folded groups stay folded**
- A group you fold, on its own or with Fold all, is still folded when you come back or reload.

**Fixed: countermeasure limits without chaff**
- For an aircraft that carries no chaff, such as the Mi-8MT, the limit now reads “max 128” instead of a formula with “chaff × 0”.

**The Kord on both doors is reported**
- A Mi-24P loadout received with something on both doors — from a file, a preset or a copy — now shows the conflict under both doors, like any other rule.

### Briefing Generator

**Aircraft types under their designation**
- Like in the other tools; the briefing still stores the game’s type name.

**The same radios as in the other tools**
- The radios offered for each aircraft are the same as in the Flight Configurator and the Datacard Generator (ten types had different radio names).
- Changing the aircraft of a radio plan updates the radios offered at once.

**Radio names picked from the suite’s list**
- The name of a radio in a radio plan is picked from the suite’s own list, with search, instead of the browser’s list; “Other radio…” still lets you type any name, and a name typed earlier stays.

**Fixed: a custom aircraft name hid the radio plan editor**
- A name such as “constructor” no longer stops the radio plan editor from showing.

**Restore after opening a briefing**
- Open a briefing… now offers Restore for 12 seconds, like the other tools: it brings back the briefing you had before.

**Fixed: briefing files are read safely**
- A briefing file, or a briefing kept by the browser, can no longer change how the page works through special keys such as __proto__.

### Route Planner

**Opens in Read mode**
- A tap on the map no longer adds a waypoint by mistake; choose Waypoint to lay the route.

**Relief**
- New “Relief” option in the Display menu: the terrain as DCS sees it, shaded in relief over any base map, on Caucasus, Cold War Germany and Syria.
- With it on, the ground elevation is shown next to the mouse pointer (on a phone, tap the map in Read mode), in the altitude unit you chose; in Read mode, tapping or clicking an imported layer shows the elevation instead of the layer's details — untick Relief to read them.

**DISS-15 values for the Mi-24P and Mi-8MTV2**
- The Navigation section can show each waypoint’s DISS-15 values (forward or aft, left or right, in km from the first waypoint, map angle 000), with the north and the KM-2 value to set.

**Map controls for the finger**
- On a touch screen, zoom, search and the Point · Ref. · Read · Draw · Ruler modes are 44 px, and so is the handle between map and panel.

**Tabs at the bottom on a phone**
- On a phone or tablet, the map stays in view above the panel, which now has four tabs at the bottom of the screen — Route, Ref., Layers and Nav. — in the same bar as the Briefing and Datacard Generators; map and panel start at about half the screen each, and the handle still resizes them.
- Below 520 px wide, a waypoint row takes two lines, the name on the first, altitude, speed and reference on the second; with a finger, its text is 16 px.

**“Clear everything”, as in the other tools**
- In English, the button of the Clear window now reads “Clear everything”.

**Fixed: the map height after typing**
- On a phone, moving the handle while the on-screen keyboard is open no longer keeps the map small once the keyboard closes.

**Threats layer**
- A hostile SAM, AAA or radar symbol can be given its system, among the game’s 57 air defence systems; with Threats ticked in Display, the map shows where an aircraft at the checked height above the ground is seen and within firing range, masked by DCS’s relief, with the firing and detection ranges. On a theatre without relief, only the ranges are drawn.
- Where the route is seen at its planned altitude, it is outlined in yellow, and the navigation sheet says by which threat and over what distance.
- The checked height goes up to 20,000 ft (6,000 m) at least, whatever the ceilings; above a system’s ceiling, that system no longer tints.

### Datacard Generator

**DISS-15 values on Mi-24P and Mi-8MTV2 datacards**
- New “Heading / distance + DISS” display: each waypoint’s DISS-15 values next to heading and distance; the block title tells the map angle, the north and the KM-2 value.

**Runways into the wind**
- The airfield's runway list marks the runway into the wind and those with a tailwind, from the Weather box; a runway chosen with a tailwind of 1 kt or more is flagged under its row.

**Take-off mass like the Flight Configurator**
- Gun rounds and equipment options count.

**Any of the 75 types on a crew line**
- From the same grouped list with search, on a free datacard too.

**The folded Radio section shows its channel count**
- Like the other sections, it says how many channels the datacard prints.

**“For the whole mission” marks only Heading and Variation**
- In the Navigation settings, these two are shared with the Route Planner; Display stays per datacard.

**Fixed: a free card kept its last aircraft**
- When every crew line of a free card goes back to “to pick”, the Aircraft and Count fields empty instead of keeping the last aircraft found.

### Field Manual

**Links in the manual’s ink**
- Links in the text take the manual’s ink instead of the browser’s blue; the Route Planner and Flight Configurator drawings show the new behaviour.

**DISS-15 explained**
- The Route Planner and Datacard Generator chapters explain the DISS-15 values; the Flight Configurator drawing shows the fold icon on a single group.

**The HQ screen drawn with the Wing button in its place**
- The two drawings of the HQ screen show the toolbar in its new order.

**The home screen drawn with its insignia**
- The two drawings of the home screen show the insignia and the family's icon.

**The phone drawing of the home screen in the right order**
- The title plate now sits under the toolbar buttons, as on screen.

**Threats**
- The Route Planner page explains the threats layer and lists the game’s air defence systems with their ranges and ceilings.

## MP-V2.1.0 — 2026-11-16
A small release after v2.0.0: the Field Manual now draws every screen of the suite, and a few fixes in HQ and the Route Planner.

#### HQ
- When the Wing configuration is provided by another tool, the Wing window shows it read-only, with a note saying where to edit it; Import, Reset and the Example are then off, Export still works. The custom liveries and default liveries boxes fold like the squadron cards, closed when the page opens.

#### Route Planner
- **Open ▾ › Open a route or layers…** now says that it also reads CombatFlite layers (.cf).
- In Read mode, an airfield inside a CombatFlite zone opens its chart sheet again, instead of the zone's sheet.

#### Field Manual
- Every tool chapter, and the home page in "Where to start", now opens its gestures with a drawing of the screen: numbered bubbles point to each area, and the numbered legend below says what it does; on a phone, a tall version of the drawing. The windows without a drawing (HQ's Wing, flight packages, Dynamic Spawn) keep a short text after the legend. The build checks that every label drawn exists in its tool.
- The manual's top bar now has Index and Contents: Contents opens a panel listing every page and its sections, one touch away; each chapter ends with the previous and next chapters. The in-page Index button is gone, and Mission Plan's back button says, in its tooltip, that it leads to the Mission Plan home.

## MP-V2.0.0 — 2026-11-15
Mission Plan v2 is one suite with one version number. The home page is now the only way in: a tool opened on its own shows a line pointing to it. All your work lives in one work file that **Save** writes and **Open** reads back. The suite follows a circuit: the Mission Commander prepares the mission (HQ, Briefing Generator, Recon Station), the Flight Leader prepares the flights (Route Planner, Datacard Generator and the new Flight Configurator), and the flights go back to the mission in HQ. The suite is now under the GNU AGPL-3.0 licence.

#### All tools
- **One work file** for the whole suite: **Save** in any tool, or on the home page, writes the briefing, recon, groups, routes, layers, datacards, theatre and settings into one `.json`. **Open… › Open a work file…** brings it all back, and **Restore** undoes it for a few seconds. A part of a file that cannot be read is reported. The Wing configuration and the mission open in HQ are not part of it. Old briefing, datacard, route and configuration files still open.
- **One example mission**, STEPPE WIND over Cyprus, loaded from the **Example ▾** menu of the home page, which has two lines: the Mission Commander line fills the Briefing Generator and Recon Station, the Flight Leader line fills the Route Planner, Datacard Generator and Flight Configurator. The tools no longer have this menu. It follows the interface language and keeps your units and heading settings. HQ keeps its own **Example** button, which loads a demonstration wing.
- **Groups are shared** by the Flight Configurator, Route Planner and Datacard Generator: create, rename or re-route a group in one and the others follow. A DCS group is now called a group, not a flight; a flight package is still a flight package. Deleting a route removes it from the groups that follow it, removing a group removes its datacard, and a route you named is never replaced by an imported one.
- **HQ mission line**: when a mission is open in HQ, the Briefing Generator, Flight Configurator, Route Planner and Datacard Generator show a line under the toolbar with its date, start time and file.
- **One top bar** in every tool, the Field Manual included: the tool's name and purpose, the file buttons in one order (Open, Save, Import, Export, Example, Clear) with one icon each, then the settings and a drawn language flag. When space runs short the bar gives up, in this order, the decorative stamp, list labels, the Display label and the button labels. On phones the file buttons come first. Buttons are 44 pixels high, contrast is readable in every theme, and the keyboard focus is visible.
- **The same words everywhere**: **Open** and **Save** for the tool's own file, **Import** and **Export** to exchange with another tool or make the final document, **Clear** to empty a tool. In the Flight Configurator, Route Planner and Datacard Generator, Clear empties groups, routes and datacards after one confirmation.
- **Every file asks for its name** first, with the usual name filled in. A document keeps one name whatever the format, and kneeboard PNG pages have one size, 2000 × 2828, in the Briefing Generator and the Datacard Generator. On tablets, files open the share menu.
- **One message style**: a single toast at the bottom, green for success and red for errors, which stay at least five seconds. Errors are in plain words.
- **One way to confirm and fold**: questions open in the suite's own window and their button says what will happen. Loading the example or a file over your work offers **Restore** instead of asking. Sections fold with the same arrow, a folded section shows a one-line summary, and each tool remembers what you folded. **Fold all** is an icon in each section header.
- Every drop-down list works the same: a search field on long lists, keyboard navigation, placement above the on-screen keyboard. “Side” is now “Coalition”.
- **Radios** are named and ordered as DCS does (A-10C II, C-130J, M-2000C, OH-58D, Gazelles, F-15E, AV-8B); the Mirage F1CE and F1BE have their own radio names and bands (TRAP 136 and 137B), like the F1EE.
- The language you choose in one tool carries over to the others. **Ctrl+S** saves in every tool.
- **Magnetic variation follows DCS** for every date: the IGRF model up to 1984, the WMM 1985 for 1985, then each year uses the previous five-year WMM file.
- An import window says when a file cannot be read. On phones and tablets, the on-screen keyboard no longer hides the bottom of the open tool.

#### Landing page
- Two frames, **Mission Commander** and **Flight Leader**, with smaller cards. **Open**, **Save**, **Example ▾** and the Field Manual are in the top bar. The open tool takes the keyboard focus, so Ctrl+S reaches it.
- The foot of the page shows the suite's version, its name and the licence. On a new browser profile, the page and its example follow the browser's language.
- The credits name the embedded fonts and their licences (SIL OFL 1.1, Apache 2.0), whose texts are in the repository (`fonts/`); html2canvas and JSZip are credited too.

#### HQ
- **Example** loads a demonstration wing (Task Force Kestrel, three squadrons); your own configuration is kept and **Restore** brings it back.
- The mission is shared with the other tools only while it is open in HQ; after a page reload HQ starts empty.
- The page is laid out around the mission: **Open .miz**, **Save .miz**, **Flight packages** and **Wing** in the top bar. Changes add up, with a counter, and **Save .miz** checks the mission and downloads it once. **Discard** takes it back to how it was when opened or last saved. **Clear** removes the open mission, with a warning if changes are not saved.
- **Flight packages**: export groups of the loaded mission (route, radios, loadout, livery) and apply packages to a mission. Each group is found by its name and side; you choose what to apply, and a report lists what was written. A group may mix aircraft types. Packages are recognised by content, not file name. The HF radio of the Mi-24P and Mi-8MT, which missions do not preset, is skipped. Applying a package the mission already carries says there is nothing to change.
- **Dynamic Spawn**: make a single-aircraft group a template and link it, in three steps, to bases of its coalition that already have it enabled; a panel lists each base offering it.
- **Delete groups** from the mission: review what still points to them, then save without them. Triggers, tasks and scripts that name them are listed, not changed.
- **Wing configuration**: pick each squadron's aircraft from the game's 75 flyable types, with “Other type (mod)…”; add custom liveries and a default livery per type. A configuration the browser refuses to store now says so. Radios are named and numbered as in the cockpit.

#### Flight Configurator
- **New tool.** A Flight Leader prepares a group and exports it as a flight package that HQ applies to the mission. Each aircraft has its own type, so a group can mix types.
- **Radios**: every radio of the aircraft, with the bands of the game (the Mi-24P's R-863 goes up to 399.9 MHz), up to five frequencies for the Mi-24P and Mi-8MT HF radio, and a box on each channel to print it on the datacard.
- **Loadout** built on the aircraft's front view, with the rules of Mission Tools' Loadout Editor: a weapon that cannot go with the rest is greyed out. Sliders for fuel and gun, flares and chaff within the aircraft's capacity, and an estimated take-off weight. Keep your presets under **My presets**: Open, Example and Clear never touch them.
- A **Route** block shows the Route Planner's route for the group as a paper sketch, with each leg's magnetic heading and distance.
- **Import** reads the mission in HQ, a briefing or a flight package, with Side, Type and Name filters. A flight package carries the date and theatre of the mission.
- The theatre is picked in the top bar and shared with the Route Planner and Datacard Generator.

#### Briefing Generator
- **Standard** (one mission page plus photo pages, now the default) or **Advanced** (eleven sections) is chosen in **Display ▾**. Empty fields hint at what to type instead of showing sample values.
- The briefing opens on a **Header** (operation, mission, date, time in Zulu); classification and reference move to the last section, folded. The time is printed in Zulu beside the date, on the briefing and on the datacard.
- **Export** is one window: format, pages and file name. **Take from HQ mission** in the METAR assistant takes weather, date and start time from the mission open in HQ; the tool's own `.miz` import is gone. A `.miz` the assistant cannot read shows a message in the interface language.
- **Open** only accepts a briefing; any other file is refused and your briefing is kept. The Wing tab no longer imports the wing configuration: HQ is where it is set.
- In Standard, aircraft are picked from the game's list. The map image can come from the Route Planner. On the printed briefing, the classification stamp no longer covers the reference line.

#### Recon Station
- **Example** loads a demonstration photo with markers, shapes, magnifier and info block (USDA NAIP aerial image, public domain). **Open ▾**, **Save**, **Export** and **Clear** are in the top bar.
- It shows the Wing logos set in HQ by itself, and still lets you add your own. Empty mission, date and classification fields come from the current briefing.
- Classification uses the Briefing Generator's six levels. A value too long for the info block is drawn smaller, then cut with “…”. Messages no longer cover the drawing bar, and the image stays when you switch language.

#### Route Planner
- **Several routes**, one per group, in a route list; the others are drawn faintly. **Import** (the mission in HQ, a briefing, a flight package `.json` or `.zip`) turns groups into routes with Side, Type and Name filters, bringing their aircraft, radios, loadouts and liveries.
- **Ruler** mode: tap to measure segment by segment, with heading, distance and total; taps snap to waypoints, reference points and airfields.
- **Groups…** picks the groups that follow a route, or creates one. **Save** is a menu (selected route, all routes); **Clear** lets you pick what to clear.
- **Display ▾** holds the base map and the units; **Export ▾** exports the image for the briefing or the Route Tool file.
- Each route keeps its theatre; switching theatre hides the routes of the others, and they return with it. Theatre, units and course settings are shared with the Datacard Generator.

#### Datacard Generator
- **One datacard per group**, shared with the Flight Configurator and Route Planner. A group's name, coalition, aircraft and radio frequencies follow on either side. **+** creates a group, “…” offers a free card, and earlier datacards open as free cards.
- One **Group and crew** box: the group, then one card per aircraft (callsign, type, board number, pilot). When every aircraft has a type, the header reads “2 × Mi-24P · CAS”. Rarely used sections start folded.
- The datacard keeps all its blocks, even empty ones, so it can be filled in by hand.
- **Import** reads the mission in HQ, a flight package, a briefing, a route or all routes at once, one datacard each, with filters; you pick the radio channels, and HQ's date, time and weather come with them.
- **Airfields** are picked from the theatre's list, filling the runway, tower frequency and ICAO code.
- The navigation is the route's: a waypoint changed here changes in the Route Planner. Fuel and take-off weight come from the Flight Configurator, and changing the mass unit converts them.
- A group's datacard shows the Flight Configurator loadout as a table, one line per station.
- **Display ▾** holds Day | Night (Jour | Nuit in French) and the units. Export is one window.

#### Field Manual
- **Rewritten as a how-to**: a “Where to start” page with the two roles, the order of the tools, a map of what each tool takes and gives, the work file and the common gestures; then one chapter per tool.
- New **Flight Configurator** chapter, and every chapter updated.

#### For maintainers
- **Releases are published by a workflow.** Pushing a branch `release/MP-V<x.y.z>` with the release text, the files and a manifest runs six checks, then creates the release and its tag. A branch `release/essai-<name>` runs the same checks and creates nothing.
- Finished branches are deleted by a daily scheduled workflow once they are seven days old.
- The tags `v2.0.0`, `v2.1.0` and `v2.1.1` are from the former Briefing Generator.
- The repository no longer ships one wing's configuration file, nor six squadron logos that no tool used.
- **Licence**: from this release, DCS Mission Plan is licensed under the GNU AGPL-3.0-or-later instead of MIT: any use, commercial included, must publish its source under the same licence, hosted services included. An additional term (section 7(b)) requires every interface to keep the credit line *Based on Mission Plan by MirabelleBenou and the 4th VEAW virtual wing*, shown at the bottom of the landing page. Releases up to v1.24.0 remain under MIT. The pydcs tables (LGPL-3.0-or-later) and Goldwolf's drawings keep their own terms.

## Before v2.0.0 — one version per tool

### Mission Plan — landing

- Operational **"situation board" landing page** that embeds the live tools (HQ, Briefing Generator, Recon Station) in isolated frames and stages the upcoming ones as *Coming soon*.
- **4 themes** (Cold War NATO / Soviet, Modern NATO / Eastern Bloc) and **FR/EN** carried across the whole suite from the board.
- **Online and offline** — published as a hosted page and as a single offline HTML file.
- **Tablet & mobile** first-class target (touch, drag, rotation-safe).
- Wing configuration shared automatically across embedded tools.

#### `v1.24.0`
##### Added
- Embeds **Field Manual v1.3.0** — a Route Planner chapter (see below).
##### Changed
- Embeds **Route Planner v1.13.1** — airfield chart sheets say they are loading and fetch their other pages in the background (see below).

#### `v1.23.0`
##### Added
- Embeds **Route Planner v1.13.0** — tap an airfield or heliport in Read mode to open its chart sheet (see below).

#### `v1.22.0`
##### Added
- Embeds **Briefing Generator v2.6.0** — an optional radio name and channel on each frequency of the quick brief (see below).
##### Changed
- The board shows its tools in a new order: HQ, Route Planner, Briefing Generator, Datacard Generator, Recon Station, Field Manual.

#### `v1.21.1`
##### Changed
- Embeds **Route Planner v1.12.1** — a *Display* menu, and the map stays fixed below 1,100 px wide in every orientation (see below).

#### `v1.21.0`
##### Added
- Embeds **Route Planner v1.12.0**, **Briefing Generator v2.5.0** and **Field Manual v1.2.4** — send the framed map view from the Route Planner to the briefing (see below).
- The board relays the map image from the Route Planner to the Briefing Generator, in memory only.

#### `v1.20.0`
##### Added
- Embeds **Route Planner v1.11.0** — NATO military symbols (APP-6) in drawn layers (see below).

#### `v1.19.1`
##### Fixed
- Embeds **Briefing Generator v2.4.7** — neutral example reference, and remove buttons that stay inside editor rows (see below).

#### `v1.19.0`
##### Added
- Embeds **Route Planner v1.10.0** — Flappie's navigation chart as a background on the Caucasus, and DCS map tiles served from a public host before DCS Olympus (see below).

#### `v1.18.1`
##### Changed
- Embeds **Route Planner v1.9.1** — the map/panel divider also in short landscape windows (see below).

#### `v1.18.0`
##### Added
- Embeds **Route Planner v1.9.0** — the DCS map can come from a tile mirror on the hosting server, with DCS Olympus as fallback (see below).

#### `v1.17.1`
##### Fixed
- Embeds **Route Planner v1.8.1** and **Datacard Generator v1.5.1** — magnetic variation before 1985 like DCS (see below).

#### `v1.17.0`
##### Added
- Embeds **Route Planner v1.8.0** and **Datacard Generator v1.5.0** — magnetic headings computed like DCS (see below).

#### `v1.16.1`
##### Changed
- Drop-down lists in the tools' forms follow the UI theme too — no more white system menus on tablets (see below).
- Embeds **Briefing Generator v2.4.6**, **Datacard Generator v1.4.2**, **Recon Station v1.1.1** and **Route Planner v1.7.1**.

#### `v1.16.0`
##### Added
- Embeds **Recon Station v1.1.0** — annotations drawn by touch (see below).

#### `v1.15.0`
##### Added
- Embeds **Route Planner v1.7.0** — orbits, kill boxes, curves, FLOT and corridors by touch (see below).

#### `v1.14.0`
##### Added
- Embeds **Route Planner v1.6.0** — touch drawing in layers, resizable map in portrait (see below).

#### `v1.13.0`
##### Added
- Embeds **Route Planner v1.5.0** — DCS towns and map search (see below).

#### `v1.12.0`
##### Added
- Embeds **Route Planner v1.4.0** — CombatFlite layers (see below).

#### `v1.11.0`
##### Added
- Embeds **Route Planner v1.3.0** — leg boxes, ground speed and minute marks (see below).

#### `v1.10.0`
##### Added
- Embeds **Route Planner v1.2.0** — DCS Route Tool import and export (see below).

#### `v1.9.1`
##### Changed
- Toolbar drop-down lists follow the UI theme on the board and in every tool — no more white system menus on tablets (see below). Released together with v1.9.0.
- Embeds **Briefing Generator v2.4.5**, **Datacard Generator v1.4.1**, **HQ v0.1.1**, **Recon Station v1.0.1** and **Route Planner v1.1.1**.

#### `v1.9.0`
##### Added
- Embeds **Route Planner v1.1.0** — typed waypoints, reference points, place names, DCS airfields (see below).
- Embeds **Datacard Generator v1.4.0** — reference points block (see below).

#### `v1.8.0`
##### Added
- Embeds **Route Planner v1.0.0** — lay a route on a map and send it to the datacard (see below).
- Embeds **Datacard Generator v1.3.0** — imports a route from the Route Planner (see below).
##### Changed
- Six tools on the board: **Route Planner** joins the live tools, before Recon Station; the *Coming soon* row is gone.
- Cards appear in reading order, and each card tilts its own way on hover.
- Embeds **Briefing Generator v2.4.4**.

#### `v1.7.0`
##### Added
- Embeds **Datacard Generator v1.2.0** — waypoints placed by heading and distance (see below). Released together with v1.5.3 and v1.6.0.
##### Changed
- Embeds **Field Manual v1.2.3**.

#### `v1.6.0`
##### Added
- Embeds **Datacard Generator v1.1.0** — navigation coordinates (see below).
##### Changed
- Embeds **Briefing Generator v2.4.3** and **Field Manual v1.2.2**.

#### `v1.5.3`
##### Fixed
- Embeds **Datacard Generator v1.0.2** — back to the validated layout (see below).

#### `v1.5.2`
##### Fixed
- Embeds **Briefing Generator v2.4.2** — sharp logos in PNG export (see below). Released together with v1.5.1.

#### `v1.5.1`
##### Fixed
- Embeds **Briefing Generator v2.4.1**, **Datacard Generator v1.0.1** and **Field Manual v1.2.1** — real bold headings and sharper PNG exports (see below).

#### `v1.5.0`
##### Changed
- Embeds **Briefing Generator v2.4.0** — map, threats and targets in the quick brief, targets in the full brief, overflow pages (see below).
- Embeds **Field Manual v1.2.0** — Briefing Generator chapter updated for v2.4 (see below).

#### `v1.4.0`
##### Changed
- Embeds **Field Manual v1.1.0** — Datacard Generator chapter, zoomable images and diagrams, more readable colours (see below).
- Embeds **Briefing Generator v2.3.2** — the quick-brief editor follows the language switch (see below).

#### `v1.3.0`
##### Added
- **Datacard Generator** is live on the board, right after Briefing Generator (see below). Field Manual stays the last live tool.
##### Changed
- Embeds **Briefing Generator v2.3.1** — scrollable toolbar on tablets and phones (see below).
- The *Kneeboard Generator* placeholder is replaced by the Datacard Generator, on the board and in Field Manual; Route Planner is the only tool still *Coming soon*.

#### `v1.2.0`
##### Changed
- Embeds **Briefing Generator v2.3.0** — full or quick brief, blank start (see below).

#### `v1.1.0`
##### Added
- **Field Manual** — a new in-app documentation tool, staged on the board like the others: one illustrated chapter per module (HQ, Briefing Generator, Recon Station), line-art diagrams, FR/EN, fully offline.
- **Live theme propagation** — changing the theme on the board (or in a tool) now updates every open tool instantly.
- **Wing stamp in toolbars** — each tool's top bar shows the wing short name with a pulsing accent dot, read from the shared wing config.
##### Changed
- The board now stages **4 live tools** (HQ, Briefing Generator, Recon Station, Field Manual) in a 2×2 layout; canonical tile order HQ · BG · RS · FM.
##### Internal
- Briefing Generator build **unified** into a single `build_briefing_generator.py` (output renamed `dcs_briefing_generator.html`); the read-only-wing (P1.B) sources were reconstructed against the published build — **no functional change** (byte-identical output).

---

### HQ

#### `v0.1.1` (beta)
##### Changed
- The theme list opens as a themed drop-down (dark olive panel, amber marks, 44 px rows), by touch or keyboard; its title follows the language.

#### `v0.1.0` (beta)
Initial release. Command post for the suite.
##### Added
- **Wing hub** — single source for wing branding, squadrons and callsigns; consumed automatically by Briefing Generator and Recon Station.
- **Experimental `.miz` engine** — read a mission, export a mission snapshot (JSON), and apply **surgical patches**: scalar deltas (radio, group frequency, livery) and structural replacements (routes & payloads).
- 4 themes, FR/EN.

##### Notes
- Advanced flight-package / Commander UI is **in development** (dev-gated).
- In-game `.miz` validation in DCS is **pending** — hence the **beta** label.

---

### Briefing Generator

#### `v2.6.0`
##### Added
- **Radio name and channel on each frequency of the quick brief**, both optional: under each frequency line of the editor, then in a column between the label and the frequency on the mission page (`R-863 · CH 3`; a channel made of digits only is shown as `CH 3`). The column appears only when at least one line has a radio or a channel — otherwise the page is unchanged. The full brief keeps both fields without showing them.

#### `v2.5.0`
##### Added
- **Receive a map from the Route Planner**: a window asks where to place it — in the quick brief, the map · threats · targets page or a photo page; in the full brief, the SITAC map, the cover map, a mission's documents or a new annex page. A map already in place is replaced only after confirmation.
##### Fixed
- A full browser storage is now reported (a toast) instead of failing silently to save the briefing.

#### `v2.4.7`
##### Fixed
- The example placeholder of the document reference field and the reference of the loaded example are now neutral (`FH-M3-1989`); the example's phases no longer carry a squadron that the default wing config does not have.
- The × remove button no longer overflows the right edge of airfield and radio-item rows in the editor — airfields on tablets and desktops, radio items on phones — in both the full and the quick format; the button keeps its 44 px touch size.

#### `v2.4.6`
##### Changed
- Form drop-down lists (classification, threat, units, radio items, airfield role, imagery, altitude reference…) open as a themed list instead of the system menu, in the field's own font — touch and keyboard; a list near the bottom of the screen opens upwards.

#### `v2.4.5`
##### Changed
- The theme list opens as a themed drop-down instead of the system menu — touch and keyboard (arrows, Home/End, type-ahead, Esc).

#### `v2.4.4`
##### Fixed
- On a scrolling toolbar (tablet, phone), the edge fades now blend into the bar instead of showing as two dark bands.

#### `v2.4.3`
##### Fixed
- In the editor, a card's number tag (“FLIGHT 1”, “PHOTO 1”…) no longer overlaps the label above the list.

#### `v2.4.2`
##### Fixed
- **Sharp logos in PNG export** — the wing and squadron logos were painted as CSS backgrounds at their on-screen size (64 px) and came out blurry in the 2× PNG; they are now real images, drawn at full resolution. On screen and in the PDF, nothing changes.

#### `v2.4.1`
##### Fixed
- **No more faux bold** — page headings, table headers and flight names used *Impact*, a system font with a single weight that the browser thickened artificially (smudgy on Windows, a different font on Android). They now use the embedded **Oswald 600/700**, identical everywhere: preview, PDF and PNG. The editor chrome no longer asks for weights that aren't embedded either.
- **PNG export at 2×** — **1588 × 2246** px per page instead of 794 × 1123, whatever the screen.

#### `v2.4.0`
##### Added
- **Map, threats and targets in the quick brief** — the Situation section takes a map (the full brief's SITAC map) and the threat fields (tanks, APC, AAA, SAM, note); the Mission section takes a **targets** list (number, type, position, remark). They print on a **“MAP ░ THREATS ░ TARGETS”** page right after the mission page, only when there is something to show; its banner names what it holds.
- **Targets in the full brief** — the same list, shared by both formats, prints as a table under the objectives of the Mission overview page.
- **Overflow pages** — when a mission page no longer fits, the blocks that don't fit move to a following page instead of being cut off. Page measurement no longer depends on images loading.
##### Changed
- **Threats on one line per category** — category and threats side by side, in both formats; the quick brief only shows the categories filled in.
##### Fixed
- A long *Departure* or *Aircraft* value no longer runs off the flights table.
- Missing tooltip translation on a frequency's “show in overview” box.

#### `v2.3.2`
##### Fixed
- **Quick brief follows the language** — switching FR ↔ EN now also re-labels the quick-brief editor (flights, radio items, photo cards), not only the full brief.

#### `v2.3.1`
##### Fixed
- **Scrollable toolbar** — on tablets (portrait or landscape) and phones, the top bar now scrolls sideways instead of running off-screen; a soft fade marks the hidden side, and every control (theme, language) stays reachable.

#### `v2.3.0`
##### Added
- **Full or quick brief** — a toolbar switch between the full dossier (unchanged) and a new **quick brief**: one page with the situation, the mission and a flight table (flight, aircraft, task, departure), frequencies, airfields and weather, followed by recon photo pages, two photos per page. Both modes share the same data, so switching never loses anything.
- **Example** button — loads the former demonstration briefing.
- Optional mission time (Z) in the quick-brief banner.
##### Changed
- **Blank start** — the tool now opens on an empty briefing, in quick mode; **Reset** clears to a blank page. Existing briefings open unchanged, in full mode.

#### `v2.2.0`
##### Added
- **Bilingual UI** — full FR/EN internationalization.
- **Radio plan**, **METAR assistant**, **import METAR from a `.miz`**, structured airfields.
- **Per-page PNG export** and PDF size optimization.
##### Changed
- Wing branding is now **consumed from HQ** (the dedicated wing tab became read-only).

#### `v2.0.0`
##### Added
- Initial offline briefing generator: multi-section editor (cover, SITAC, charts, annexes, phases).
- 4 graphic themes, native PDF export, multi-wing management via JSON.

---

### Recon Station

#### `v1.1.1`
##### Changed
- Form drop-down lists (classification, threat, units, radio items, airfield role, imagery, altitude reference…) open as a themed list instead of the system menu, in the field's own font — touch and keyboard; a list near the bottom of the screen opens upwards.

### Recon Station

#### `v1.1.0`
##### Added
- **Annotate by touch** — a drawing bar sits on the image: *Select · Frame · Ellipse · Polyline · Arrow · Bracket · Text · Loupe*. One tap places, large handles adjust: frames and magnifiers resize by their four edges and their four corners (the opposite side or corner stays put), frames rotate by their own handle, the magnifier's inset keeps the proportions of its source and stays inside the image. *Settings*, *Copy*, *Delete* and *OK* on the bar, as in the Route Planner; settings can be changed while you create.
- The image is never hidden under the drawing bar, on a computer as on a tablet.

##### Changed
- *Add a magnifier* moves from the *Legend* section to *Shapes*.
- The export is unchanged: the same annotations give the same PNG.

### Recon Station

#### `v1.0.1`
##### Changed
- The theme list opens as a themed drop-down instead of the system menu — touch and keyboard.

#### `v1.0.0`
##### Added
- Turn a screenshot into a **reconnaissance analysis photo**; native **Canvas 2D** engine (preview = export); **lossless full-resolution PNG**.
- **Sensor looks** — EO, IR white-hot, IR black-hot, SAR (stylizations, not radiometric data).
- **Image effects** — greyscale, contrast, vignette, grain, scanlines.
- **Annotations** — numbered movable markers, magnifier/loupe, shapes (ellipse, rectangle, polygon, arrow, bracket), labels (stamp, cursive, plain).
- **Editable info block** (9 fields) and **classification banner** (4 levels).
- **Wing logos** — manual upload or shared from HQ; colour / grey / white modes.
- 4 themes, FR/EN.

---

### Datacard Generator

#### `v1.5.1`
##### Fixed
- Before 1985, the magnetic variation extends the 1985 model back in time with its secular variation, like DCS, instead of staying at its 1985 values (Cold War Germany, 1961: about −4° instead of −1°). From 1985 on, nothing changes.

#### `v1.5.0`
##### Added
- **Magnetic variation computed like DCS**: with the magnetic heading, a new *Variation* setting — *Computed* or *Entered*. Computed uses the World Magnetic Models DCS World ships (epochs 1985–2025), leg by leg at each leg's start point, for the year of the card's *Date* field (1985 when empty).
- The printed navigation header shows the year and the range: *NAVIGATION · MAGNETIC HEADING · VAR 1989 (−1.6 to −0.2°)*.
- A route sent from the Route Planner brings its variation mode, and its year when the card's *Date* is empty.
##### Changed
- A card saved with a typed variation opens in *Entered* mode, unchanged.

#### `v1.4.2`
##### Changed
- Form drop-down lists (classification, threat, units, radio items, airfield role, imagery, altitude reference…) open as a themed list instead of the system menu, in the field's own font — touch and keyboard; a list near the bottom of the screen opens upwards.

#### `v1.4.1`
##### Changed
- The theme list opens as a themed drop-down instead of the system menu — touch and keyboard.

#### `v1.4.0`
##### Added
- **Reference points** — up to 12 per datacard (name, coordinates in any format, altitude, note), edited in their own section and printed in a **Reference points** block, lettered A, B, C…, in MGRS or DMS like the navigation.
- **Cascading layout** — the navigation keeps its place on page 1 while it fits; the reference points then move to page 2 on their own, and both move there only when the navigation no longer fits. A datacard without reference points lays out exactly as before.
- A route imported from the Route Planner brings its reference points along.

#### `v1.3.0`
##### Added
- **Import a route** from the Route Planner — the current route or a route file — into the navigation of the datacard shown, or into a new datacard: waypoint names, MGRS coordinates, altitudes (AGL noted), units and heading reference; headings and distances are computed from the coordinates.
##### Changed
- The toolbar's **Import** button (formerly *From briefing*) takes a briefing or a route; **Import JSON** recognises route files.
- On a scrolling toolbar, the edge fades blend into the bar.

#### `v1.2.0`
##### Added
- **Waypoints placed by heading and distance** — a waypoint without coordinates, next to a placed one, gets its coordinates from the heading and distance of the leg between them, forwards (from the previous waypoint) or backwards (from the next one), in a chain; shown in MGRS and DMS like typed coordinates, and flagged as estimated in the editor only.
- **Dotted DMS input** — `36.49.30N/34.44.29E` (with `/`, a comma or spaces; hemisphere before or after) is recognised.
##### Changed
- The navigation display list says **DMS**; a one-line hint lists the accepted coordinate formats.

#### `v1.1.0`
##### Added
- **Navigation coordinates** — each waypoint takes coordinates, pasted as shown by the F10 map or an aircraft: MGRS, degrees-minutes-seconds, degrees-decimal minutes or decimal degrees; the editor tells whether they were recognised.
- **Three ways to show the navigation**, chosen per datacard: **heading / distance** (computed between two waypoints that have coordinates, otherwise as typed), **MGRS** (10 digits) or **degrees, minutes, seconds**.
- **True or magnetic heading** — with the variation typed in the datacard (read on the A-10C CDU, the F-16 DED or the F/A-18 HSI); the block title says which, and the variation used.
##### Changed
- The deck's move-up / move-down buttons are gone: one datacard per flight.

#### `v1.0.2`
##### Fixed
- **Back to the validated layout** — text sizes, letter-spacing and line heights follow the design again (body text had grown 2–3 px larger and crowded the values); the weather block gets back its two-column grid (a value no longer runs into the next label), fuel values their dotted rules, threat chips fit on one line.
##### Changed
- **Radio** — alternating rows restart with each radio set (the first channel of each set is highlighted) and a thin rule separates two sets.

#### `v1.0.1`
##### Fixed
- **PNG export at 2×** — **2000 × 2828** px per page instead of 1000 × 1414; the toolbar's bold labels use an embedded Oswald 700.

#### `v1.0.0`

Initial release. One-page flight datacards for the cockpit kneeboard.

##### Added
- **One datacard per flight** — mission, times, crew, navigation, radio, airfields, weather, fuel & loadout, threats & notes; navigation moves to a second page when it does not fit.
- **Day & Night** versions, readable in VR; the suite themes only change the editor.
- **From scratch or from a briefing** — import flights from the Briefing Generator (current briefing or its JSON file), or only its general data (frequencies, airfields, METAR, objectives) when it has no flights.
- **Fully generic** — no built-in aircraft tables: radios, loadouts and units (kg/lb, km/NM, m/ft) are yours.
- **Exports** — PNG at 1000 × 1414 (drop it in DCS's kneeboard folder), ZIP for several pages, PDF (one A4 page per datacard page), and JSON import/export of the whole pack.
- Example values in empty fields, FR/EN, 4 editor themes, tablet and phone layout with scrollable bars, fully offline.

---

### Route Planner

#### `v1.13.1`
##### Changed
- Airfield chart sheets: a loading message while the sheet and its page arrive; the other pages are fetched in the background once the first one is shown, so switching tabs is immediate.

#### `v1.13.0`
##### Added
- **Airfield and heliport sheets**: in Read mode, tapping an airfield or a heliport opens its chart from **DCS Airfield Charts**, served by the wing's server — one tab per page (10-9, 10-9A…), pinch to zoom, double-tap to reframe; a heliport opens on its box of the heliport directory. When a field has no sheet, the viewer says so; when the server does not answer, it says the sheets are unavailable. Point and Ref. modes are unchanged.

#### `v1.12.1`
##### Added
- **Display menu** in the top bar: show or hide the route, reference points, drawings, NATO symbols, imported layers, MGRS grid, towns, airfields and places — it replaces the four toggle buttons; a dot marks the button when something is hidden. A hidden element comes back when you switch to the mode that edits it, and the choices are remembered.
##### Changed
- Below 1,100 px wide, **the map stays fixed in every orientation** (short landscape windows included — e.g. unfolded phones) and only the panel scrolls; the divider sets the map height (140 px minimum in short landscape). While typing in the panel with the on-screen keyboard up, the map shrinks to its minimum and comes back afterwards.

#### `v1.12.0`
##### Added
- **→ To the briefing**: frame the map (3:2 landscape or 2:3 portrait, pan and zoom under the frame) and export what the screen shows — background, grid, route, leg boxes, minute ticks, layers and NATO symbols — as a 1,600 px JPEG with a caption band (route name, theatre, scale bar in the route's distance unit), a north arrow and the background's attribution. In the suite it goes straight to the Briefing Generator; standalone, the image is downloaded.

#### `v1.11.0`
##### Added
- **NATO military symbols (APP-6)** in drawn layers — a ninth drawing tool, *Symbol*: tap the map to place it, then set it in its sheet: side (friend, hostile, neutral, unknown), style (filled in APP-6 colours, or outlined in the side's colour), size (S, M, L, fixed on screen), the symbol itself from a catalogue — units (infantry, mechanised infantry, armour, recon, artillery, air defence, helicopters, engineers, logistics) with their echelon (platoon to division) and higher formation, equipment (tank, IFV, SAM, AAA, radar), aircraft (fixed-wing, fighter, attack, bomber, transport, helicopter, attack helicopter) and the FARP — and its designation.
- A new symbol starts from the settings of the last one; symbols are copied, moved and deleted like the other objects, open their card in *Read* mode (with *→ Reference point*), add a route point when tapped in *Point* mode, and are saved and exported with the layers.
- Symbols are drawn with [milsymbol](https://github.com/spatialillusions/milsymbol) (MIT), embedded in a reduced build.

#### `v1.10.0`
##### Added
- **Flappie's navigation chart on the Caucasus** — a new *Background* choice, *Navigation chart (Flappie)*, offered on the Caucasus only: roads, railways, rivers, towns, forests, airfields and navaids drawn like an aeronautical chart, sharp up to zoom 12 and enlarged beyond. Credit *Map © Flappie* at the bottom of the map — many thanks to him. The chart already prints town names, so the *Towns* button is greyed out under it; your setting comes back on any other background.

##### Changed
- **DCS map tiles from a public host first** — opened outside a hosting page (the hosted page on GitHub, or the offline file), the *DCS map* now asks a public copy of the DCS Olympus tiles first (with their agreement), then DCS Olympus tile by tile; Germany Cold War gains zoom 16 there too. Inside a hosting page that provides its own tile mirror, nothing changes.

#### `v1.9.1`
##### Changed
- **The map/panel divider in short landscape windows too** (under 1,100 px wide and under 600 px high — a foldable phone unfolded and turned, for instance): the page still scrolls, and the divider sets the map height between 220 px and 85% of the window below the top bar. Its height is remembered apart from the portrait one (`rp_split_land_v1`), so turning the device keeps both; a double tap restores the original height. Portrait and wide layouts are unchanged.

#### `v1.9.0`
##### Added
- **DCS map tiles from a mirror on the hosting server.** When the page that hosts the suite provides a same-site tile mirror (`localStorage` key `map_layers_v1`, `{"configSchemaVersion":1,"dcs":{"url":"/…/{key}/{z}/{x}/{y}.png"}}`), the *DCS map* layer asks the mirror for each tile and falls back to DCS Olympus tile by tile when the mirror does not have it. If the mirror fails repeatedly without a single success (an expired session, say), the page goes straight to Olympus until it is reloaded. Without that key — the hosted page, or the file opened locally — tiles come from DCS Olympus as before.
- **Cold War Germany at level 16** through the mirror only: one more layer, sharper from zoom 16; where a level-16 tile is missing, level 15 shows underneath.

#### `v1.8.1`
##### Fixed
- Before 1985, the magnetic variation extends the 1985 model back in time with its secular variation, like DCS, instead of staying at its 1985 values (Bitburg, June 1965: −4.9° instead of −2.2°). From 1985 on, nothing changes.

#### `v1.8.0`
##### Added
- **Magnetic variation computed like DCS**: in the Navigation panel, *Variation — Computed · Entered*. Computed uses the World Magnetic Models DCS World ships (epochs 1985–2025), leg by leg at each leg's start point — matching the mission editor's readings to 0.1°.
- The year comes from the mission loaded in HQ when it is on the same theatre, otherwise from the *Year* field; *Override* puts the typed year first; 1985 by default. The panel says where the year comes from.
- Each point of the navigation table shows its variation; the title shows the year and the range: *NAVIGATION — MAGNETIC HEADING · VAR 1985 (−2.1 to −0.7°)*.
##### Changed
- A route saved with a typed variation opens in *Entered* mode, unchanged. Headings typed for *+ Point* by heading & distance use the variation of the point you start from.

#### `v1.7.1`
##### Changed
- Form drop-down lists (classification, threat, units, radio items, airfield role, imagery, altitude reference…) open as a themed list instead of the system menu, in the field's own font — touch and keyboard; a list near the bottom of the screen opens upwards.

### Route Planner

#### `v1.7.0`
##### Added
- **Orbits** and **kill boxes** in *Draw* mode. An orbit is set by its two ends and its width; drag the width handle to the side you want to turn to. A kill box shows its grid (3 × 3 by default, set in *Settings*), resizes by its four edges and its four corners — the opposite side or corner stays put, live size in NM — and rotates by its own handle.
- **Curves, FLOT and corridors** — a zone can be drawn straight or curved, a line can be a plain line, a FLOT or a corridor; chosen in *Settings*, the corridor's width is dragged on the map.
- **Settings while you create** — choosing a tool opens the settings of the shape to come, placed above the message so the map stays visible.

### Route Planner

#### `v1.6.0`
##### Added
- **Draw mode** — a fourth button next to *Waypoint · Ref. · Read*: draw your own layers by touch — circles, zones, lines, typed points (target, DMPI, exit point, LZ…) and text. One tap places, a handle adjusts: drag a circle's radius (shown live in NM), move vertices, tap a "+" to insert one, move the whole shape. *Settings* for name, colour, line style and fill; *Copy* and *Delete*. The route fades while you draw and stays untouched.
- **Your own layers** — create and name layers, choose the one you draw in; CombatFlite layers stay read-only, and *Copy to draw* turns one into an editable copy. Drawn layers are saved in the browser and travel in the exported file.
- **Resizable map in portrait** — drag the bar between the map and the panel to give the map more or less room; double-tap it to restore the default. The size is remembered.

##### Changed
- The "map unavailable" banner no longer slides under the tap-mode control on phones.

#### `v1.5.0`
##### Added
- **DCS towns** — the names of the towns of the DCS maps (Caucasus, Germany Cold War, Syria) appear from zoom 10, without overlapping each other or your route: towns close to the route first, major towns in bold. They work offline. A **Towns** button turns them on or off. Tap a town to make it a waypoint or a reference point, like an airfield.
- **Map search** — a magnifier under the zoom buttons: type two letters to find a town, an airfield or helipad, a waypoint, a reference point or a layer item (accents ignored); pick a result to centre the map on it, marked by a pulsing ring.

##### Changed
- In *Read* mode the leg insertion "+" handles are hidden; a CombatFlite ring without altitude no longer shows "0".

#### `v1.4.0`
##### Added
- **CombatFlite layers** — *Open* now also reads a CombatFlite mission file (`.cf`): pick the layers you want and they are drawn on the map, read-only — threat rings, zones (lines, curves, FLOT, corridors), orbits, kill boxes with their grid, targets and other points, text boxes — with CombatFlite's colours (fills softened so the route stays readable). The theatre follows the file.
- A **Layers** section lists them: show or hide each one, remove one or all. Layers are kept in your browser, apart from the route.
- **Read** mode on the map switch (*Waypoint · Ref. · Read*): tap a layer item to read its card; a point's card can turn it into a reference point. In *Waypoint* or *Ref.* mode, layers let taps through, and a tapped target becomes a waypoint or a reference point named after it — like an airfield.
- **Export** lets you choose what the route file carries: the route, and any of the layers. A file with layers and no route adds its layers without touching your route.

#### `v1.3.0`
##### Added
- **Leg boxes** — a house-shaped box on each leg: the name of the waypoint it leads to, heading, distance, ground speed, altitude and ETE (*Full*), or heading and distance only (*Minimal*). Each box lies along its leg with its roof pointing the way you fly, text always upright; drag it out of the way and it keeps its place, even when the leg moves. *None* brings back the plain heading · distance label.
- **Ground speed** — one default speed for the route and an optional speed per leg, in km/h or knots following the distance unit.
- **Minute marks** — a tick at every minute of each leg, longer every five minutes, and the **elapsed time** under each waypoint (`00+21+05`); ETE per leg and total time on the navigation sheet.
- **Route line** and **minute marks** in the route colour or in black — your choice, kept in your browser.
##### Changed
- The route file (`dcs-route-v1`) also keeps the ground speeds, the box style and where each box was dragged; older files open with the defaults.

#### `v1.2.0`
##### Added
- **DCS Route Tool** — *Open* now also reads a Route Tool file (`Saved Games\DCS\Config\RouteToolPresets\<map>.lua`): pick the theatre (guessed from the file name) and one of its routes. **Export to the Route Tool** adds the route to your existing `<map>.lua` — every other route kept byte for byte — or writes a new file; no timing is written, DCS computes it. Coordinates use each map's DCS projection (11 theatres, from [pydcs](https://github.com/pydcs/dcs)); reference points are not exported.
##### Changed
- **Portrait tablets and phones**: the map stays in place and only the panel below it scrolls, the on-screen keyboard included.
- *Open* accepts any file and recognises it by its content.

#### `v1.1.1`
##### Changed
- The **Map**, **Theatre** and theme lists open as themed drop-downs instead of the system menu — touch and keyboard; *DCS map* shows greyed out with its reason on theatres it does not cover. Tapping the map while a list is open only closes the list.

#### `v1.1.0`
##### Added
- **Type a waypoint** — by coordinates (MGRS, DMS, DDM or decimal) or by heading and distance from the last waypoint (true or magnetic, km or NM).
- **Reference points** — up to 12 lettered diamonds (A, B, C…) off the route: a *Waypoint · Ref.* switch on the map chooses what a tap adds; listed in their own section and on the navigation sheet, saved in the route file, and sent to the datacard.
- **Place names** overlay (Esri World Boundaries and Places) over any layer.
- **DCS airfields and helipads** for 11 theatres (names and positions from [pydcs](https://github.com/pydcs/dcs), LGPL-3.0) — runways from zoom 7, helipads from zoom 10; tap one to add a waypoint or a reference point named after it.
##### Changed
- The toolbar scrolls at every width when it overflows.

#### `v1.0.0`
Initial release. Lay a route on a map, read it, send it to the datacard.
- **Map layers** — **DCS map** (the DCS map tiles shared by the [DCS Olympus](https://github.com/Pax1601/DCSOlympus) team, on the eight theatres they cover), **topographic** (OpenTopoMap), **satellite** (Esri World Imagery) or **grid only**; the choice is yours, and offline the map falls back to grid only by itself.
- **MGRS grid** over any layer — zones and bands, 100 km squares with their letters, then 10 km and 1 km lines as you zoom in.
- **The route** — tap the map to add a waypoint, drag it to move it, a leg's "+" inserts one; name, altitude and AGL / MSL per waypoint; up to 30 waypoints, numbered from 0 like DCS.
- **Navigation sheet** — per leg, true or magnetic heading (typed variation) and distance; per waypoint, MGRS (10 digits) and DMS; total distance. Distance in km or NM, altitude in m or ft, chosen separately.
- **To the datacard** — one button opens the Datacard Generator on the route import.
- **JSON** save and open, an example route, 14 theatres, 4 themes, FR/EN, tablet and phone layouts.

### Field Manual

#### `v1.3.0`
##### Added
- **Route Planner chapter** — theatre and base maps, tap modes, building the route, reference points, leg boxes, navigation and magnetic variation (with the DCS editor ruler caveat), airfield chart sheets, drawing layers and NATO symbols, CombatFlite layers, hand-off to the Datacard and Briefing Generators, DCS Route Tool, tablet layout; two new diagrams.
##### Changed
- Datacard Generator chapter: importing navigation from the Route Planner.

#### `v1.2.4`
##### Changed
- Briefing Generator chapter: the map can come from the Route Planner.

#### `v1.2.3`
##### Changed
- Datacard Generator chapter: waypoints placed by heading and distance.

#### `v1.2.2`
##### Changed
- Datacard Generator chapter: navigation coordinates and display modes; the deck buttons.

#### `v1.2.1`
##### Changed
- Export sizes updated (Datacard Generator PNG: 2000 × 2828 px); the quick brief's overflow pages described exactly.

#### `v1.2.0`
##### Changed
- **Briefing Generator chapter** updated for v2.4: the quick brief's map, threats and targets, the “map, threats, targets” page, targets in the full brief, overflow pages; the *what feeds what* diagram gains a **Map · threats · targets** box (C·S).

#### `v1.1.0`
##### Added
- **Datacard Generator chapter** — what the tool does, what a briefing import fills in, day and night, units, exports; with an *anatomy of a datacard* diagram and a *what feeds the datacard* diagram.
- **Zoom** — click or tap any image or diagram to open it full screen; zoom up to 4× (wheel, pinch, buttons, double-tap) and pan. Diagrams stay vector-sharp.
##### Changed
- **Briefing Generator chapter** updated for v2.3: full or quick brief, blank start, the editor tabs on narrow screens; its *what feeds what* diagram now tags each section **C** (full brief) and/or **S** (quick brief).
- **Readability** — module colours now mark (bars, borders, tints) while text is written in ink: headings, links and diagram labels reach a 4.5:1 contrast in all four themes; diagram panels are lighter.
- French typography — non-breaking thin spaces before high punctuation and inside quotes.

#### `v1.0.0`
##### Added
- **In-app suite documentation** — opens on the board like the other tools. One illustrated chapter per module (Recon Station, HQ, Briefing Generator); upcoming tools (Route Planner, Kneeboard) stubbed as *coming*.
- **No screenshots** — line-art SVG diagrams (one per chapter) and reused board tiles, on a "paper" surface.
- 4 themes, FR/EN, fully offline.
