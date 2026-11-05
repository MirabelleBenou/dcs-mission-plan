# data/

Tables used by the **Flight Configurator** to compose a loadout station by station. They are copies, byte for byte, of the tables of the Loadout Editor of `dcs-mission-tools` (commit `03834f3ce7858af3aac4e7e0ffbd2f76cceccb3e`), where `data/README.md` describes their shape and how to regenerate them.

- `weapon_names.json`, `aircraft_pylons.json`, `aircraft_limits.json`: generated from [pydcs](https://github.com/pydcs/dcs) **1.0.0**, **LGPL-3.0-or-later** ([`COPYING.LESSER`](COPYING.LESSER)). The tables carry the same licence.
- `aircraft_views.json` and `views/`: the front-view drawings of the Mi-24P, Mi-8MT, F-4E-45MC and Mirage F1EE, by **Goldwolf** (DCS Reference Guide), used with permission. They are **not covered by the repository's MIT licence**: do not reuse them without the author's permission (see [`views/LICENSE.md`](views/LICENSE.md)).

`build_flight_configurator.py` embeds the four tables in the module between `/* NAME:BEGIN */` and `/* NAME:END */` markers, and stops the build if an embedded copy differs from its file.
