# PVA — Photovoltaic Art

Nine end-of-life solar panels placed around Bosa, each powering only itself. Each panel records its day of sun and turns it into an image, drawn by fixed rules, created and viewed live, then sealed at sunset. The image is seen only on a visitor's phone, through the panel's own Wi-Fi, for the run of the exhibition. Same sun, different data.

First exhibition: **SUNDIAL · La Meridiana**, Bosa, summer 2027.

This is a proof of concept: a bare-bones trial of the technology and the dial. There is no story or media layer; site-specific layers will come later.

> Status: drafts, not yet compiled or tested on hardware. Firmware draft 6 records everything the dial needs (sun sections, heat, presence); the panel page and `tools/pva_rules.py` both draw rules v1.

## How it fits together

| Part | What it is | Where it runs |
| --- | --- | --- |
| The panel | PV panel + ESP32 + temperature probe + clock module, no battery, no internet | On a wall in Bosa |
| The dial | Each day's image, drawn on the visitor's phone from the panel's data | The panel's own Wi-Fi |
| The map | Route, pins, which panels are likely awake, the visitor's position | The PVA website (this repo's `docs/`) |
| The girasole | A sunflower and a chalkboard: the Heliotropist legend re-enacted, drawn by visitors | First stop of the route, moveable |
| The print | The whole exhibition as one 9 × 9 four-colour screen print | Made after the run from the collected data |

A visit: the flyer's QR code opens the map → at a pin, join that panel's Wi-Fi → the dial opens on its own → leave the Wi-Fi and return to the map.

## Repository

```
docs/
  index.html                  the map — the only part published on the website
firmware/panel_page_server/
  panel_page_server.ino       ESP32 firmware
  partitions.csv              4 MB flash layout for the ELEGOO ESP32 (~2 MB for pages and data)
  partitions_16mb.csv         16 MB layout for an ESP32-S3 (~9.9 MB)
  panel_config.example.h      template for per-panel settings
  data/                       copied into each panel's flash
    index.html                the panel page: today's dial, gallery of past days, live data
    admin.html                admin page: status, clock, exhibition dates, sun-sensor calibration, raw data download
    media/title.txt           this panel's name
    media/map.txt             the map's web address
hardware/
  SUNDIAL.md                  the panel as a sundial: gnomon, drilling template, installation, wall test
tools/
  pva_rules.py                the dial rules as drawing code (canonical print, separations)
  sample_a4.py                A4 sample sheet, invented data
  requirements.txt
```

## Publishing the map

In the repository's GitHub Pages settings, publish from the `docs` folder on the main branch, then point the PVA domain at it. Only `docs/` is published; the panel files stay in the repo but never appear online.

Pins are placed on site: open the map with `?edit` after the address, drag the pins, tap **Copy positions** and paste them into the `PANELS` list at the top of `docs/index.html`.

## Preparing a panel

1. **Settings.** Copy `panel_config.example.h` to `panel_config.h` and set the panel's Wi-Fi name (`panel-01` … `panel-09`) and a long, unique admin key. `panel_config.h` is ignored by git; keep the keys somewhere safe.
2. **Build stage.** Set the four switches at the top of the firmware (see the table below). Pins are preset for the ELEGOO 30-pin board; on an ESP32-S3, set them by hand.
3. **Media.** Edit `data/media/title.txt` (panel name) and `data/media/map.txt` (map address).
4. **Build.** Arduino IDE, ESP32 core 3.x; libraries OneWire, DallasTemperature, RTClib. ELEGOO: board *ESP32 Dev Module*, Flash 4 MB, Partition Scheme *Custom* (uses `partitions.csv` in the sketch folder). ESP32-S3: board *ESP32S3 Dev Module*, Flash 16 MB, PSRAM OPI, and rename `partitions_16mb.csv` to `partitions.csv`.
5. **Flash.** Erase all flash first (essential on any board that ever held keys), upload the firmware, then upload `data/` with the LittleFS uploader.
6. **Set up on site.** Join the panel's Wi-Fi, open `http://192.168.4.1/admin.html`, enter the key, set the clock from your phone and set the exhibition's first and last day.
7. **Calibrate the sun sensor** (once, if fitted): on a clear day near solar noon, tap **Calibrate now**. Until then the panel still logs the raw current, and the dial's sun sections are drawn as outline.

| Stage | Hardware | `BENCH` | `PANEL_SENSE` | `USE_RTC` | `SUN_SENSE` |
| --- | --- | --- | --- | --- | --- |
| 1, bench | ESP32 on USB, temperature probe | 1 | 0 | 0 | 0 |
| 1, panel | + panel, buck converter, supercapacitor | 0 | 0 | 0 | 0 |
| 2, full | + voltage divider, DS3231 clock, protection | 0 | 1 | 1 | 0 |
| 2, sun | + sun sensor (MOSFET, shunt, INA180) | 0 | 1 | 1 | 1 |

Without the divider (`PANEL_SENSE 0`) there is no dawn gate or dusk close: the supercapacitor smooths the start, and the board simply runs until the light fails. Without the clock (`USE_RTC 0`), the first visitor's phone sets the time each day.

## Installation: the admin checklist (per panel)

**In the workshop**

1. **Settings.** `panel_config.h` from the example: Wi-Fi name (`panel-01` … `panel-09`) and a long, unique admin key, recorded somewhere safe.
2. **Media.** `title.txt` (panel name) and `map.txt` (map address).
3. **Stage switches** to match the hardware fitted. `BENCH` back to `0` before installing.
4. **Flash.** Arduino IDE, ESP32 Dev Module, Custom partitions: erase all flash, upload the firmware, upload `data/` with the LittleFS uploader.
5. **Power chain.** Buck converter set to exactly 5.0 V before anything is connected; then fuse, diode, supercapacitor, TVS.
6. **Sensors.** Probe on GPIO 4 · divider on GPIO 34 · DS3231 on GPIO 21/22 · sun sensor gate on GPIO 25, amplifier on GPIO 35.
7. **Bench test.** On USB: set the clock, set the exhibition dates to today, check status (clock module fitted, probe found, voltage plausible), watch a dial form.
8. **Frame.** Drill from the template; fit the gnomon at 50°, the 13 numbered hour brackets and the stand-off brackets ([hardware/SUNDIAL.md](hardware/SUNDIAL.md)).

**On site**

9. **Permission** from the wall owner or the Comune.
10. **Wall test.** Compass for a first reading, then the noon-shadow test: which edge packs out, and by how much.
11. **Mount.** Cut the stand-offs, hang, spirit level against the glass; box on the deep side, probe on the panel back.
12. **Wall plate** beside the panel: its number and the QR code.
13. **Solar-noon check.** The shadow falls on the 12 bracket; adjust the stand-offs if not.
14. **Admin page.** Join the panel's Wi-Fi, open `http://192.168.4.1/admin.html`, enter the key, set the clock and the exhibition dates.
15. **Calibrate the sun sensor** on a clear day near solar noon, before the run starts. Uncalibrated, every section draws as an outline.
16. **Map pin.** Map with `?edit`, drag the pin, copy the positions into `docs/index.html`, push.

**The girasole (once, for the whole trail)**

- **Sow** two or three dwarf sunflowers in large pots in early to mid May, so one is still in bud, and turning with the sun, in the solstice week. Keep the best.
- **Set up** the pot and a chalkboard, with ochre and blue chalk, in front of a south-facing wall: the first stop of the route. It is moveable; place its pin (the flower) with `?edit` like the panels.

**During the run**

17. **Daily round, at sunset.** Each panel's status and a raw-data download (on an iPhone use Safari, not the Wi-Fi pop-up, which cannot save files). At the girasole: photograph the chalkboard, then wipe it for the next day; water the plant.
18. **Upkeep.** Clean the glass; replace a failed board or panel. A day lost shows in the gallery as the black outline.

**After the run**

19. Final download from every panel, and the seven chalkboard photographs → canonical sheet and separations → print → panels down.

## The visitor's experience

1. A flyer or a wall plate: scan the QR code.
2. The map opens on mobile data: the route, the girasole and nine pins, the visitor's own position, which panels are likely awake now.
3. The first stop, the girasole: the legend re-enacted. A young sunflower turning with the sun, and a chalkboard. The visitor adds a mark, ochre for sun or blue for shade, and writes the time beside it.
4. At a pin: a panel, which is also a sundial telling solar time.
5. Join the open Wi-Fi `panel-0N`; the page opens by itself. No internet is involved.
6. Today's dial forming live, or sealed after sunset: the same rule as the chalkboard, drawn by the panel. Tap it for the day's facts.
7. Below: the gallery of earlier days; a day the panel did not wake is the black outline.
8. A strip at the bottom: panel temperature, time awake, sunset.
9. Leave the Wi-Fi, back to the map, on to the next panel.

The visitor's phone counts once per solar hour as a dot on the dial, never identified.

## To do

- [ ] **Import script:** turn an admin download into tile data for `pva_rules.py`, the canonical sheet and the website page.
- [ ] **Separations script:** one file per ink for the screen print.
- [ ] **Website page** for the canonical sheet, filled after each day's round.
- [ ] **Calibration** of every panel before the run; prove the step on the pilot.
- [ ] **"How to read the dial" key** in the panel page's info overlay, as well as on the flyer and website.
- [ ] **Italian and English** on the panel page, info overlay and map.
- [ ] **"Stay connected"** wording on the flyer or wall plate: some phones warn about or drop a network with no internet.
- [ ] **After the last day:** decide whether the panel page closes or changes once the run ends.
- [ ] **First compile and bench test** of firmware draft 6.
- [ ] **The girasole:** sunflower variety and sowing in May; a moveable chalkboard and its stand; where it stands on the route.

## Hardware per panel

Each panel is also a vertical sundial, mounted vertical and facing due south: see [hardware/SUNDIAL.md](hardware/SUNDIAL.md) for the gnomon, the drilling template, the installation and the noon-shadow wall test.

**Stage 1:** 36 V 180 W PV panel · DC-DC buck converter (8–60 V in), set to exactly 5.0 V with a multimeter **before** connecting anything · 5.5 V 4 F supercapacitor across the 5 V output (in the shaded box: it ages fast in heat) · ELEGOO ESP32 30-pin on a screw-terminal breakout · DS18B20 waterproof probe on the panel back, data on GPIO 4, 4.7 kΩ from GPIO 4 to 3.3 V.

**Stage 2 adds:** fuse and reverse-polarity diode on the panel side · SMAJ5.0A TVS diode across 5 V · panel-voltage divider 100 kΩ / 5.6 kΩ + 100 nF into GPIO 34 (must be GPIO 32–39: the other analog pins stop working with Wi-Fi on) · DS3231 clock module on GPIO 21/22.

**Sun sensor:** logic-level N-MOSFET (≥60 V, ≥20 A) across the panel, on the panel side of the diode, gate on GPIO 25 (100 Ω series, 10 kΩ pull-down) · 5 mΩ shunt in its source leg · INA180A1 (gain 20) across the shunt, on 3.3 V, output to GPIO 35. Every 10 s the panel is shorted for about a millisecond and its short-circuit current read; the supercapacitor carries the board through the pulse. If the shunt or gain differ, change `SHUNT_OHM` and `SENSE_GAIN`.

## The dial (rules v1, draft)

- **Time:** solar noon at the top; 12° per hour; Bosa's solstice day (15 h 03 m) spans 180°, shorter days proportionally less.
- **Sun:** a ring of 15-minute solar sections, ochre when this panel is in direct sun, blue when it is not (shade, cloud, or the sun behind the panel), from a short-circuit current reading (above a third of the panel's clear-noon current = sun).
- **Heat:** a red line rising from the axis, the panel's warming since sunrise; +40 °C reaches the ring, with no upper limit.
- **Presence:** one black dot per solar hour, for visitors in that hour: small 1–5, medium 6–10, large 11+.
- **Seal:** the black horizon line; nothing after sunset enters the dial.
- **A panel that did not wake:** the ring outline and the axis only, in black.
- **Inks:** ochre, red, blue, black, translucent, printed in that order.

*Horas non numero nisi serenas* — I count only the sunny hours.

## What a panel records

| File | Contents | Who sees it |
| --- | --- | --- |
| `/art/DATE.csv` | every 5 min: volts, temperature, sun current | visitors (exhibition days, sealed at sunset) |
| `/art/DATE.sun.csv` | each 15-minute solar section: sun 1 / 0 / −1 unknown, readings, readings above, mean current | visitors |
| `/art/DATE.vis.csv` | each solar hour: distinct phones | visitors |
| `/log/…`, `/archive/…` | every 5 min record, sun current every minute, visitors per hour, every day | admin only, as one CSV |

## Data and privacy

Visitors are counted, never identified: a phone is told apart only by a salted hash kept in memory for one hour; the salt changes at every power-on and is never stored. Raw data stays on each panel and is downloaded only through the admin page; visitors see the exhibition days' images, nothing else.
