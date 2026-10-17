# PVA — Photovoltaic Art

Nine end-of-life solar panels placed around Bosa, each powering only itself. Each panel records its day of sun and turns it into an image, drawn by fixed rules, created and viewed live, then sealed at sunset. The image is seen only on a visitor's phone, through the panel's own Wi-Fi, for the run of the exhibition. Same sun, different data.

First exhibition: **SUNDIAL · La Meridiana**, Bosa, summer 2027.

This is a proof of concept: a bare-bones trial of the technology and the dial. There is no story or media layer; site-specific layers will come later.

> Status: drafts, not yet tested on hardware. The drawing rules on the panel page are still a placeholder; the agreed rules (v1) are in `tools/pva_rules.py`.

## How it fits together

| Part | What it is | Where it runs |
| --- | --- | --- |
| The panel | PV panel + ESP32 + temperature probe + clock module, no battery, no internet | On a wall in Bosa |
| The dial | Each day's image, drawn on the visitor's phone from the panel's data | The panel's own Wi-Fi |
| The map | Route, pins, which panels are likely awake, the visitor's position | The PVA website (this repo's `docs/`) |
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
    admin.html                admin page: status, clock, exhibition dates, raw data download
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
2. **Build stage.** Set the three switches at the top of the firmware (see the table below). Pins are preset for the ELEGOO 30-pin board; on an ESP32-S3, set them by hand.
3. **Media.** Edit `data/media/title.txt` (panel name) and `data/media/map.txt` (map address).
4. **Build.** Arduino IDE, ESP32 core 3.x; libraries OneWire, DallasTemperature, RTClib. ELEGOO: board *ESP32 Dev Module*, Flash 4 MB, Partition Scheme *Custom* (uses `partitions.csv` in the sketch folder). ESP32-S3: board *ESP32S3 Dev Module*, Flash 16 MB, PSRAM OPI, and rename `partitions_16mb.csv` to `partitions.csv`.
5. **Flash.** Erase all flash first (essential on any board that ever held keys), upload the firmware, then upload `data/` with the LittleFS uploader.
6. **Set up on site.** Join the panel's Wi-Fi, open `http://192.168.4.1/admin.html`, enter the key, set the clock from your phone and set the exhibition's first and last day.

| Stage | Hardware | `BENCH` | `PANEL_SENSE` | `USE_RTC` |
| --- | --- | --- | --- | --- |
| 1, bench | ESP32 on USB, temperature probe | 1 | 0 | 0 |
| 1, panel | + panel, buck converter, supercapacitor | 0 | 0 | 0 |
| 2, full | + voltage divider, DS3231 clock, protection | 0 | 1 | 1 |
| 2+ | + sun sensor (MOSFET, shunt, INA180) | firmware support still to come | | |

Without the divider (`PANEL_SENSE 0`) there is no dawn gate or dusk close: the supercapacitor smooths the start, and the board simply runs until the light fails. Without the clock (`USE_RTC 0`), the first visitor's phone sets the time each day.

## Hardware per panel

Each panel is also a vertical sundial, mounted vertical and facing due south: see [hardware/SUNDIAL.md](hardware/SUNDIAL.md) for the gnomon, the drilling template, the installation and the noon-shadow wall test.

**Stage 1:** 36 V 180 W PV panel · DC-DC buck converter (8–60 V in), set to exactly 5.0 V with a multimeter **before** connecting anything · 5.5 V 4 F supercapacitor across the 5 V output (in the shaded box: it ages fast in heat) · ELEGOO ESP32 30-pin on a screw-terminal breakout · DS18B20 waterproof probe on the panel back, data on GPIO 4, 4.7 kΩ from GPIO 4 to 3.3 V.

**Stage 2 adds:** fuse and reverse-polarity diode on the panel side · SMAJ5.0A TVS diode across 5 V · panel-voltage divider 100 kΩ / 5.6 kΩ + 100 nF into GPIO 34 (must be GPIO 32–39: the other analog pins stop working with Wi-Fi on) · DS3231 clock module on GPIO 21/22.

**For the sun rule:** logic-level MOSFET (≥60 V, ≥20 A), shunt resistor, INA180 current-sense amplifier.

## The dial (rules v1, draft)

- **Time:** solar noon at the top; 12° per hour; Bosa's solstice day (15 h 03 m) spans 180°, shorter days proportionally less.
- **Sun:** a ring of 15-minute solar sections, ochre for direct sun, blue for shade, from a short-circuit current reading (above a third of the panel's clear-noon current = sun).
- **Heat:** a red line rising from the axis, the panel's warming since sunrise; +40 °C reaches the ring, with no upper limit.
- **Presence:** one black dot per solar hour, for visitors in that hour: small 1–5, medium 6–10, large 11+.
- **Seal:** the black horizon line; nothing after sunset enters the dial.
- **A panel that did not wake:** the ring outline and the axis only, in black.
- **Inks:** ochre, red, blue, black, translucent, printed in that order.

*Horas non numero nisi serenas* — I count only the sunny hours.

## Data and privacy

Visitors are counted, never identified. Raw data stays on each panel and is downloaded only through the admin page; visitors see the exhibition days' images, nothing else.
