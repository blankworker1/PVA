# Carrier board v1 — schematic draft

A KiCad schematic for the carrier board, generated from the specification in [../CARRIER.md](../CARRIER.md).

> **Status: draft-1, 20 Oct 2026. Not reviewed. Do not manufacture from this.**
> It is a faithful drawing of the spec, checked by script, but it must be reviewed by an electronics engineer before anyone lays out or builds the board. The board switches a 45 V panel's full short-circuit current every 10 seconds.

## Files

| File | What |
| --- | --- |
| `carrier.kicad_pro`, `carrier.kicad_sch` | KiCad project and schematic (KiCad 7 format; opens in KiCad 7 and 8) |
| `carrier_schematic.pdf` | The schematic as a PDF (A1), for review |
| `carrier.net` | Netlist exported by KiCad, with footprints: what a layout designer imports |
| `bom.csv` | Bill of materials: references, values and ratings, footprints, fitted or not, notes |
| `checks.py`, `checks.txt` | Calculations: divider and current-sense ranges, supercap ride-through, AUX diode heat |
| `parts.py` | **The source:** every part, footprint and pin-to-net connection, transcribed from CARRIER.md |
| `gen_schematic.py`, `gen_bom.py`, `verify.py`, `build.sh` | Regenerate everything with `./build.sh` |

**Drawing style.** Each pin has a short wire and a net label; parts are joined by net name, not drawn wires. Each section of CARRIER.md has its own block on the sheet. This is a standard KiCad style, and it means the drawing is exactly the netlist.

**To change the board,** edit `parts.py` and run `./build.sh`. Hand edits to `carrier.kicad_sch` are overwritten by the next build.

## How it was checked

- **Connectivity:** `verify.py` reads the netlist KiCad itself exports and checks all **205 pin connections** against `parts.py`. Result: 0 mismatches, no net with fewer than two pins.
- **Footprints:** all exist in KiCad's standard libraries.
- **Coverage:** every reference in CARRIER.md's part tables is present. The extras are parts the spec describes in its text rather than its tables (headers J9, J10, J11, J13; test points; mounting holes; the ESP32 sockets), plus three capacitors I added (below).
- **ERC (electrical rules check):** not yet run. KiCad 7's command line has no ERC; open the project in KiCad and run *Inspect → Electrical Rules Checker*. Power flags are placed on GND, +5V, +3V3, VBAT, PANEL+ and PV+.

## Choices made where the spec left room: please review

1. **ESP32 pin order: provisional.** The sockets follow the common 30-pin DOIT DevKit V1 layout (left: EN, 36, 39, 34, 35, 32, 33, 25, 26, 27, 14, 12, 13, GND, VIN; right: 23, 22, 1, 3, 21, 19, 18, 5, 17, 16, 4, 2, 15, GND, 3V3). **Confirm against a photo of both sides of the ELEGOO board**, together with the 25.4 mm row spacing, before layout.
2. **D0** is drawn as a dual common-cathode Schottky in D2PAK (TO-263) with both anodes on PANEL+, matching the "dual 20 A 100 V" example. A single diode in another package is fine; update the footprint.
3. **Q1** uses a DPAK (TO-252) footprint: gate pad 1, drain on the tab, source pad 3.
4. **Shunt RSH1** (spec R_SH) is a 2-pin 2512 resistor. The Kelvin connection to U2 is a **layout** rule: two thin traces from the inner ends of the pads.
5. **U1** uses KiCad's DS3231M symbol, which has the same 16-pin pinout as the DS3231SN. Pins 5–12 go to GND, as the DS3231SN datasheet requires. RST is left unconnected.
6. **U4 load switch:** AP22804AW5 (current-limited, SOT-23-5), fed from +5V as the spec describes. Confirm the enable polarity of the exact part (the spec needs active-high); its fault flag is not used.
7. **Added, not in spec v1:** C11 (1 µF, U3 gate-driver supply decoupling, required by its datasheet), and C12 and C13 (1 µF, U4 input and output). Remove them if the reviewer disagrees.
8. **D2** (SMAJ5.0A, unidirectional TVS) is drawn with a Zener symbol; **D3** (3.3 V ESD on the probe line) as a bidirectional TVS.
9. **High-current terminals J1 and J12** use a 10 mm-pitch footprint (MetzConnect Type 067) as a placeholder. The designer chooses an equivalent rated ≥ 15 A for 4–6 mm² wire.
10. **microSD J8:** Hirose DM3AT push-push socket. Its detect switch connects SD_CD to GND, and R17 pulls SD_CD up. Whether the switch closes or opens when a card is inserted depends on the socket: check the datasheet, and set the firmware's polarity to match.
11. **Header 3V3 pins** (J9, J10, J13) and J11's 3V3 come through F3 (net +3V3_EXT), as the spec says. The DS3231, probes and microSD use +3V3 directly.
12. **Test points TP10 and TP11** carry the DS3231's INT/SQW and 32K outputs, which the spec sends to test pads only.

## What the calculations show (`checks.txt`)

- **Panel voltage (GPIO 34):** R2 is now 4.7 kΩ (was 5.6 kΩ). The ESP32's analog input reads accurately up to about 2.45 V, which is now about 54 V of panel voltage: the 44.5 V open-circuit voltage gives 2.00 V, a cold-morning 48 V gives 2.15 V, and the board's 60 V rating gives 2.69 V, under the pin's 3.6 V absolute maximum. The 7 V dusk threshold still gives 0.31 V.
- **Sun current (GPIO 35):** 0.5 V per amp, reliable to about 4.9 A. A vertical panel peaks near 1.8 A (0.9 V), with plenty of margin. Only a tilted panel in full sun would exceed the reliable range.
- **Supercaps (5 F at 5 V):** about 45 seconds of ride-through at 0.5 W, as USES.md states.
- **Shunt:** 0.18 W during each 1 ms pulse at 6 A, negligible on average.
- **AUX:** above about 2 A the diodes D0 and D5 need real cooling (6 W in D5 at 9 A).

## Review log

**Review 1 (20 Oct 2026), schematic PDF only.** Three points, all answered:

1. *Current-sense range too low for 15 A.* The sensor only sees the panel's own short-circuit current: 5.40 A on the label, about 6 A at most. 15 A is the terminal and wire rating. Gain 100 is deliberate for a vertical panel (about 1.8 A at noon). Saturation above about 6.6 A is harmless. **Change:** measurement ranges noted on the sheet.
2. *2 A fuse and 3 A diode on a 15 A input?* F1 and D1 are only in the board-supply branch (under 0.3 A), not in the measured current path; F1 sits after the Q1 node so short-circuit pulses never pass through it. **Change:** current-path note on the sheet.
3. *60 V gives 3.17 V at the divider: little margin.* 60 V is the board rating, not an expected voltage (Voc 44.5 V, about 48 V on a cold morning). It was still below the pin's 3.6 V maximum, but above the ADC's accurate range. **Change:** R2 5.6 kΩ → 4.7 kΩ; firmware `DIVIDER` updated (pva-fw-6.1.1).

## Next steps

1. Confirm the ESP32 pin order and spacing, and the box size for the mounting holes.
2. Engineer review of this schematic.
3. Run ERC in KiCad and fix anything it finds.
4. Then layout: in KiCad, *Tools → Update PCB from Schematic*, or send the project or `carrier.net` to the layout service.
