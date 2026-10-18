# PVA carrier board — specification v1

One small board per panel. It carries everything except the ESP32 and the buck converter, which plug in or wire on.
Every part on the board is fitted by the board maker; the builder only plugs in, screws down and fits a coin cell.

> Status: specification for the board designer, not yet drawn. v1 is also the bench test of the sun sensor,
> so it carries test points and options. Order 5 for v1; fix, then order 10 of v2.

## Decisions

| Decision | Choice |
| --- | --- |
| Board drawn by | A freelancer in KiCad, from this document |
| ESP32 | ELEGOO ESP32 30-pin (USB-C) dev board, **plugged into two 1 × 15 female header sockets** (removable) |
| Buck converter | ANGEEK 8–60 V module, **beside the board**, joined by 4 short wires (screw terminal to screw terminal) |
| Clock | DS3231 chip **on the board**, CR2032 holder, **no charging circuit** |
| Supercapacitors | Two 2.7 V 10 F radial cells (10 × 25 mm, 5 mm lead pitch), **in screw terminals**, fitted by the builder |
| Enclosure | Standard IP65 junction box, about 150 × 110 × 70 mm, cable glands for panel and probe |
| Board | 2 layers, **2 oz copper**, about 100 × 80 mm, 4 × M3 mounting holes, black solder mask, white silkscreen |
| Maker | JLCPCB or PCBWay, standard assembly (SMD) + through-hole assembly for the terminals |

## Block diagram

```
 panel + ──┬────────────── F1 1 A ──┬── D1 ──► J2 BUCK IN +      J3 BUCK OUT + ──► 5V rail ──► ESP32 VIN
           │                         │                                              │
           Q1 sun MOSFET             R1/R2 divider ─► GPIO 34               C1+C2 supercaps (series)
           │                         │                                       TVS, 470 µF, LED
           R_SH 5 mΩ ─► INA180 ─► GPIO 35
           │
 panel − ──┴──────────── GND ──────────────────────► J2 BUCK IN −      J3 BUCK OUT − ──► GND

 ESP32 3V3 ──► 3V3 rail ──► DS3231 + CR2032, DS18B20 terminals (GPIO 4), INA180 supply, I2C header
 GPIO 25 ──► jumper JP1 ──► gate driver U3 (from 5 V) ──► Q1 gate
```

**Important: the sun MOSFET sits directly across the panel terminals, before the fuse.** The panel is a current source:
its short-circuit current (about 5–6 A, check the label) is safe to short for a millisecond, but it must not flow
through a small fuse every 10 seconds. The fuse protects only the board side, so it can be small.

## Circuit, section by section

### 1. Panel input and sun sensor

| Ref | Part | Value / rating | Notes |
| --- | --- | --- | --- |
| J1 | Screw terminal, 2-way, high current | ≥ 15 A, accepts 4–6 mm² (or ferrules), 7.62–10 mm pitch | Board edge; labelled `PANEL +` `PANEL −` |
| Q1 | N-MOSFET | V_DS ≥ 60 V, I_D ≥ 20 A, R_DS(on) ≤ 20 mΩ at V_GS 4.5 V, DPAK/D2PAK or PowerPAK | Drain on `PANEL +`, source on R_SH top |
| R_SH | Shunt resistor | 5 mΩ, 1 %, 2512, ≥ 2 W | Between Q1 source and GND |
| R_SH2 | Footprint only | 2512, parallel to R_SH | Option: two 10 mΩ in parallel instead of one 5 mΩ |
| U2 | Current-sense amplifier INA180A1 | Gain 20 V/V, SOT-23-5 | Supply 3V3 (output then can never exceed 3.3 V); IN+ to R_SH top, IN− to R_SH bottom by **Kelvin traces** |
| C6 | Capacitor | 100 nF, 0603 | U2 supply decoupling |
| R6, C7 | RC on U2 output | 1 kΩ + 10 nF | Light filter into GPIO 35; time constant 10 µs, well inside the 400 µs settle |
| U3 | Low-side gate driver, non-inverting | Supply 4.5–18 V, input threshold works from 3.3 V (TC4427A / MCP1416 class), SOT-23-5 or SOIC-8 | Powered from 5V rail, so Q1 gets 5 V gate drive |
| R4 | Gate resistor | 10 Ω, 0603 | U3 output to Q1 gate |
| R5 | Pull-down | 10 kΩ, 0603 | U3 input to GND: Q1 stays off while the ESP32 boots |
| JP1 | 2-pin header + jumper | | GPIO 25 to U3 input. **Remove the jumper to disable the sun sensor** |

Scale: 6 A × 5 mΩ = 30 mV × 20 = 0.6 V at GPIO 35, i.e. 0.1 V per amp, as the firmware expects (`SHUNT_OHM 0.005`, `SENSE_GAIN 20`).

### 2. Board side of the panel: fuse, diode, divider

| Ref | Part | Value / rating | Notes |
| --- | --- | --- | --- |
| F1 | Fuse | 1 A slow-blow, 1206/1812 SMD or 5 × 20 mm holder | After the Q1 node, before D1 |
| D1 | Rectifier diode | 1000 V 3 A, SMC (S3M class) | Reverse-polarity protection; stops Q1 pulses draining the buck's input capacitor |
| J2 | Screw terminal, 2-way | 5.0 mm pitch, ≥ 5 A | `BUCK IN +` (after D1), `BUCK IN −` (GND) |
| R1 | Resistor | 100 kΩ, 1 %, 0805 | From F1/D1 node |
| R2 | Resistor | 5.6 kΩ, 1 %, 0603 | To GND |
| C5 | Capacitor | 100 nF, 0603 | Across R2; divider to GPIO 34 (45 V → 2.4 V, 60 V → 3.2 V) |

### 3. 5 V rail

| Ref | Part | Value / rating | Notes |
| --- | --- | --- | --- |
| J3 | Screw terminal, 2-way | 5.0 mm pitch | `BUCK OUT +` `BUCK OUT −`, from the buck set to 5.0 V |
| J6, J7 | Screw terminals, 2-way | 5.0 mm pitch | One per supercap cell, in series: J6 from 5V to MID, J7 from MID to GND. Silkscreen the **−** side (stripe) |
| R7, R8 | Balancing resistors | 10 kΩ, 0805 | One across each cell |
| D2 | TVS | 5.0 V standoff (SMAJ5.0A) | Across 5V rail |
| C3 | Electrolytic or polymer | 470 µF, 10 V, low ESR | Across 5V rail, close to ESP32 VIN |
| C4 | Capacitor | 100 nF, 0603 | Across 5V rail |
| LED1, R9 | Green LED + resistor | 10 kΩ (about 0.3 mA) | "5 V present"; dim on purpose |

### 4. ESP32 socket

Two 1 × 15 female headers, 2.54 mm pitch. **Row spacing: measure the actual ELEGOO board** (30-pin boards come in
two widths) and send the measurement to the designer. Pin positions from the ELEGOO 30-pin pinout.

| ESP32 pin | Net |
| --- | --- |
| VIN (5V) | 5V rail |
| GND (both) | GND |
| 3V3 | 3V3 rail (the dev board's own regulator feeds the board's 3.3 V parts) |
| GPIO 4 | DS18B20 data |
| GPIO 21 / 22 | I2C SDA / SCL (DS3231, expansion header) |
| GPIO 25 | Sun MOSFET gate (via JP1 and U3) |
| GPIO 34 | Panel voltage divider |
| GPIO 35 | Sun current (INA180 output) |
| GPIO 5 / 18 / 19 / 23 | microSD: CS / SCK / MISO / MOSI (VSPI) |
| GPIO 39 | microSD card-detect (input only) |
| GPIO 26 / 27 / 32 / 33 / 36 / 13 / 14 | Spare-pins header J9 (32, 33 and 36 are ADC1, usable with Wi-Fi on; 36 is input only) |
| GPIO 16 / 17 | UART header J10 (RX2 / TX2) |
| Not brought out | GPIO 1 / 3 (USB serial), 2 / 12 / 15 (boot strapping pins; 2 also drives the dev board's LED) |

Keep copper and parts away from under the ESP32's antenna end; place the antenna at the board edge.
The USB-C socket must stay reachable for programming with the board in the box.

### 5. Clock

| Ref | Part | Value / rating | Notes |
| --- | --- | --- | --- |
| U1 | RTC DS3231SN (SOIC-16W) | | V_CC 3V3; INT/SQW and 32K to test pads only |
| BT1 | CR2032 holder, SMD | | V_BAT. **No charging resistor or diode** |
| C1x | Capacitor | 100 nF, 0603 | U1 decoupling |
| R10, R11 | I2C pull-ups | 4.7 kΩ, 0603 | SDA, SCL to 3V3 |

If the DS3231SN is not in stock at the maker, an RV-3028-C7 is a drop-in alternative in function (needs a firmware library change).

### 6. Temperature probes

| Ref | Part | Value / rating | Notes |
| --- | --- | --- | --- |
| J4, J5 | Screw terminals, 3-way | 3.5 mm pitch | Wired in parallel: `3V3` `DATA` `GND` (red, yellow, black). J5 is for an optional second probe |
| R12 | Pull-up | 4.7 kΩ, 0603 | DATA to 3V3, next to J4 |
| R12b | Footprint only | 0603 | Second pull-up value, if a longer cable needs a stronger pull-up |
| R13 | Series resistor | 100 Ω, 0603 | DATA to GPIO 4 |
| D3 | ESD diode | 3.3 V, SOD-323 | DATA to GND, at the terminal |

### 7. microSD card (future-proofing)

Not used by firmware draft 6; fitted now so that raw data and future media layers can outgrow the ESP32's 2 MB.

| Ref | Part | Value / rating | Notes |
| --- | --- | --- | --- |
| J8 | microSD socket, push-push, with card-detect switch | | SPI mode on the VSPI pins |
| R14–R17 | Pull-ups | 10 kΩ, 0603 | On CS (GPIO 5), MOSI, MISO and card-detect (GPIO 39), to 3V3. The CS pull-up also keeps GPIO 5 high at boot, as a strapping pin should be |
| C8, C9 | Capacitors | 10 µF + 100 nF | At the socket's 3V3 pin |

Place J8 at a board edge where a card can be inserted with the board in the box. Any card from 1 to 32 GB, FAT32.

### 8. Expansion and test

- **I2C header:** 4-pin, 2.54 mm: 3V3, GND, SDA, SCL (for future I2C sensors, e.g. a BME280).
- **Spare-pins header J9:** 9-pin, 2.54 mm: 3V3, GND, GPIO 32, 33, 36, 26, 27, 13, 14. Silkscreen each pin; note "32/33/36 analog, 36 input only".
- **UART header J10:** 4-pin, 2.54 mm: 3V3, GND, GPIO 16 (RX), GPIO 17 (TX), for a future serial device.
- **Power take-off J11:** 4-way screw terminal, 3.5 mm pitch: `5V`, `5V SW`, `3V3`, `GND`, for future add-ons (see section 9).
- Every usable ESP32 pin is then either in use or on a header. The ones left off are reserved for programming (1, 3) or decide how the chip starts (2, 12, 15), and connecting things to them can stop the board booting.
- **Test points** (loops or pads, labelled): `PV+`, `BUCK IN`, `5V`, `3V3`, `GND`, `VDIV` (GPIO 34), `ISENSE` (GPIO 35), `GATE` (Q1 gate).
- **Silkscreen:** "PVA carrier v1", the net name at every terminal, the supercap polarity, and "JP1: remove = sun sensor off".

### 9. Power take-off for future add-ons

| Ref | Part | Value / rating | Notes |
| --- | --- | --- | --- |
| F2 | Resettable fuse (PTC) | 0.5 A hold, 1206 | 5V rail to J11 `5V`: a faulty add-on cannot drag down the panel's own board |
| F3 | Resettable fuse (PTC) | 0.2 A hold, 0805 | 3V3 rail to J11 `3V3` and to the header 3V3 pins |
| U4 | Load switch, 5 V, ≥ 1 A, active-high enable, with soft start (TPS22918 / AP22802 class) | | 5V rail to J11 `5V SW` |
| R18 | Pull-down | 100 kΩ, 0603 | U4 enable to GND: switched output off at boot |
| R19 | 0 Ω link | 0603 | GPIO 27 to U4 enable. Fitted by default; remove to free GPIO 27 |
| D4 | Schottky diode, 1 A (SS14 class), SMA | | Cathode to `5V SW`, anode to GND: flyback clamp, so a bare 5 V relay coil can be driven straight from `5V SW` |

- **A 5 V relay:** either wire a bare 5 V relay coil to `5V SW` and `GND` (D4 absorbs the coil's switch-off kick), or use a relay module powered from `5V` with its input on a spare GPIO (choose a module that triggers from a 3.3 V signal). A typical coil draws 70–90 mA while on; a latching relay draws only during its switching pulse.
- `5V SW` lets a future firmware power an add-on only when wanted (after the dawn gate, or only during the day), so it never competes with the board at the weak ends of the day.
- The 3.3 V comes from the ESP32 dev board's own regulator, which has only about 200 mA to spare: keep 3.3 V add-ons to small sensors. Anything bigger runs from `5V` or `5V SW`.
- Every milliamp taken shortens the supercaps' ride-through in the same proportion. A load of more than about 1 A belongs on its own supply, not on this board.

## Layout rules for the designer

1. **The sun loop is the only high-current path:** `PANEL +` → Q1 → R_SH → `PANEL −`. Keep it short and wide (copper pour, ≥ 3 mm on 2 oz), on one side, with J1, Q1 and R_SH close together.
2. **Kelvin connections:** U2's inputs run as two thin, parallel traces from the inner ends of R_SH's pads; U2 sits right next to R_SH.
3. **Star ground** at R_SH's ground end: the sun loop returns there; signal ground joins there, not through the loop.
4. **Gate:** U3 next to Q1, gate trace short.
5. **Edges:** J1 (panel) and J4/J5 (probe) on one edge, towards the cable glands; J2/J3 towards the buck module; ESP32 antenna at the opposite edge, USB-C reachable.
6. **Spacing:** panel voltage up to 60 V; normal 0.5 mm clearances are plenty.
7. **Mounting:** 4 × M3 holes for standoffs in the box; keep 3 mm clear round them.

## Parts the builder fits (no soldering)

| Part | Per board |
| --- | --- |
| ELEGOO ESP32 30-pin | 1, plugged into the sockets |
| ANGEEK buck converter, set to exactly 5.0 V first | 1, wired to J2 and J3 |
| 2.7 V 10 F supercap | 2, into J6 and J7, stripe to **−** |
| CR2032 | 1 |
| DS18B20 probe | 1 (2 optional), into J4 (J5) |
| Jumper on JP1 | 1, once the sun sensor is to be used |
| microSD card | optional, 1–32 GB, FAT32 |

## Firmware

No change needed for v1: the pins and scale match firmware draft 6 (`SHUNT_OHM 0.005`, `SENSE_GAIN 20`, GPIO 4/21/22/25/34/35).
The gate driver is non-inverting, so GPIO 25 high still means "short the panel".
The microSD socket and the spare pins are unused until a later firmware adds them; nothing on them affects boot.

**Expansion is limited by power, not pins:** there is no battery, so any future sensor should draw no more than a few milliamps.

## v1 bench test, before ordering v2

1. Power the board from a bench supply into `BUCK IN` (no panel): check 5V and 3V3, the LED, the clock (set from the admin page, unplug, plug back in) and the probe.
2. Connect a real panel, jumper JP1 off: check `VDIV` against a multimeter on the panel voltage.
3. Jumper on, clear sun near noon: check `ISENSE` on an oscilloscope or by the firmware's `isc` reading against a multimeter's short-circuit current reading of the same panel.
4. Run a full day with `BENCH 0`, then fix anything in v2.
