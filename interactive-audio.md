# The SUNSET set — an audio interactive node on carrier v1

A SUNSET interactive node with a 12 V amplifier, playing **the SUNSET set** at sunset. It doesn't play every night, only **when the sun has fully charged the battery that day.** The night's set is announced by a shout.

**The amplifier lives inside the panel's own enclosure,** and the only things on the outside are two speaker jacks. The set begins when someone plugs in the speakers. Nothing that can be stolen, kicked or rained on stays in the street.

It runs on the same carrier v1, on the battery tier: the panel feeds a Victron SmartSolar MPPT 75/15 and a 12 V LiFePO₄ battery, with JP1 off and the sun sensor compiled out. The tier is specified in [interactive-auction.md](interactive-auction.md), sections 1 and 2; this document covers only what is different.

> Status: draft 2, 22 Oct 2026 (Bluetooth amplifier first, wired DAC as fallback; amplifier inside the enclosure, speakers plugged in for the set). Concept only; nothing built. **Nothing here changes the carrier board:** every addition is an off-board module wired to its existing headers.

---

## 1. The idea

- **The sun pays for the music.** The set plays only on a day when the battery reached full charge. A dull day means silence, and the page says why.
- **It starts at sunset,** the moment every SUNSET node keeps. The set is a performance, not business, so it plays after the day's business has closed, on stored sun.
- **The shout comes first.** The node knows it can play as soon as the battery is full, usually early in the afternoon. It posts a shout then ("The SUNSET set plays tonight at [node]"), and couriers have hours to carry it to the walls before sunset.
- **The speakers arrive with the people.** The panel holds the music and the power; the speakers are brought and plugged in for the set, then taken away. Plugging them in is part of the event.

---

## 2. Hardware

### 2.1 What is added, all inside the panel's enclosure

| Part | Notes |
| --- | --- |
| **Amplifier** | A small 12 V **Bluetooth** stereo amplifier board (class D). Fed straight from the battery through its own fuse, never through the carrier |
| **Amplifier power relay** | Switches the amplifier's 12 V. Its coil runs from the carrier's switched 5 V output (`5V SW`, J11). Carrier v1 already has this: U4 under GPIO 27 (R19 fitted), with D4 to absorb the coil's kick (CARRIER.md section 9). The amplifier is powered only for the set; idle, it draws nothing |
| **Two speaker jacks** | Weatherproof panel-mount sockets in the enclosure wall (IP67 class, locking: Speakon-type or similar), one per channel, with caps for when nothing is plugged in |
| **microSD card** | In the carrier's own socket J8 (already wired, unused by SUNDIAL). Holds the music |
| **Fallback only: I2S DAC** | PCM5102 class, if Bluetooth proves unreliable (2.3) |

**The enclosure.** The standard box in CARRIER.md (about 150 × 110 × 70 mm) was sized for the carrier alone. With the amplifier board, the relay and the jacks, expect the next size up. The amplifier is a heat source only during the set, after sunset, when the box is cooling; it is idle through the hot afternoon.

### 2.2 Audio path, first option: Bluetooth

The carrier's ESP32 is the **original ESP32** (ELEGOO 30-pin, WROOM-32), which can act as a **Classic Bluetooth audio source** (A2DP), as a phone does. It reads MP3 files from the microSD card, decodes them and streams them to the amplifier a few centimetres away. (The newer ESP32-S3 cannot do this; carrier v1 does not use it.)

- **No DAC, no audio wiring** between the carrier and the amplifier. The I2S pins stay free.
- **No radio clash.** Wi-Fi and Bluetooth share the ESP32's one radio, but the set plays after sunset, when Wi-Fi has closed (3.4). They never run together.
- **The existing amplifier** can be used for the pilot.

**Things to check in the pilot:**

| Check | Why |
| --- | --- |
| **Hijacking** | Many cheap Bluetooth amplifiers power up discoverable and accept the first device that connects, so a passer-by's phone could take the speakers. The ESP32 must connect the instant the relay powers the amplifier, and most amplifiers then refuse a second source. Test the amplifier: does it reconnect to the last device, does it accept strangers, can pairing be locked? |
| **Firmware size** | The Bluetooth stack is large. Wi-Fi, Bluetooth, MP3 decoding and the built-in pages must fit the 1.9 MB app slot (USES.md 1). Make a test build early |
| **Memory** | MP3 decoding and Bluetooth encoding together are within the original ESP32's means; with Wi-Fi off during the set there is more RAM to spare |

### 2.3 Audio path, fallback: wired DAC

If Bluetooth proves unreliable, a PCM5102-class I2S DAC (a few euros) feeds the amplifier's line input by wire, and the amplifier's Bluetooth is never used. The DAC sits in the same enclosure and connects to J9:

| Use | GPIO | Header | Notes |
| --- | --- | --- | --- |
| I2S bit clock | 26 | J9 | To the DAC |
| I2S data | 13 | J9 | To the DAC |
| I2S word select | 14 | J9 | GPIO 14 toggles briefly at boot; the amplifier is unpowered then, so nothing is heard |
| DAC power | 3V3, GND | J9 | From the header |

### 2.4 Pins

| Use | GPIO | Header | Notes |
| --- | --- | --- | --- |
| Amplifier power (relay) | 27 | via R19 to U4 | Unchanged from the carrier: R19 stays fitted |
| Speaker-plugged sense (optional) | 33 | J9 | A switched jack contact, so the set starts only once speakers are in (3.1) |
| microSD | 5, 18, 19, 23; card-detect 39 | on board (J8) | Already wired on carrier v1 |
| VE.Direct | 16 RX, 17 TX | J10 | As on every interactive node |
| Clock | 21 / 22 | on board | Sunset time and the end-of-set time |
| I2S (fallback only) | 26, 13, 14 | J9 | See 2.3 |
| Spare | 32, 36 | J9 | 36 is input only |

### 2.5 Power

| Load | Draw | Per set |
| --- | --- | --- |
| Amplifier and speakers, moderate volume | about 10–15 W average (music averages well below the rated power) | about 15 Wh an hour |
| ESP32 playing and streaming, Wi-Fi off | about 0.5 W | under 1 Wh an hour |

An hour's set costs about 6 % of a 20 Ah battery (about 250 Wh). The rule that it plays only on a full-battery day means the music never eats into the next day's business.

---

## 3. The rules

### 3.1 When it plays

| Condition | Source |
| --- | --- |
| The battery reached **float** (full) at some point today | The Victron's charge state, over VE.Direct |
| The battery is still above a set level at sunset | The Victron's battery voltage and charge state |
| Inside the season and the permitted hours | Settings, from the comune's rules (3.3) |
| *(optional)* Speakers are plugged in | The jack's switch contact (2.4) |

If the first three are met, the shout goes out when the battery first reaches float. At sunset the relay powers the amplifier, the ESP32 connects to it, and the set starts, or, with the jack sense fitted, starts when the speakers go in. If nobody plugs speakers in by the latest end time, the night passes in silence.

**How long it plays** is a setting, tuned in the pilot. Two options:

- **Fixed:** the same length every time (for example 45–60 minutes).
- **Earned:** the length follows the day's surplus, so a long bright day earns a longer set. The Victron's daily yield gives the figure.

### 3.2 What it plays

- **The SUNSET set:** music on the microSD card, loaded at the yearly visit (the box is opened anyway) or by the admin.
- Each night can play the next set in a list, so the town doesn't hear the same hour every time. The order is a setting.
- **Rights:** public performance in Italy normally needs an SIAE licence. The simplest course is music the project owns or that is openly licensed (Creative Commons with commercial use allowed). To be settled before the first set (5).

### 3.3 Volume and neighbours

- **A volume cap in firmware,** below the amplifier's maximum, set on site in the pilot.
- **A fixed latest end time,** whatever the set length, inside the comune's quiet hours.
- Speakers placed by whoever brings them, but the panel's position decides where the sound starts: choose sites where it carries along the street, not into bedrooms.

### 3.4 Wi-Fi

The day's business closes at sunset on every SUNSET node, and the audio node keeps the rule: its Wi-Fi serves pages in daylight (whether tonight's set is on, past sets) and closes at sunset. The music plays with Wi-Fi off, which is also what lets Bluetooth have the radio.

---

## 4. Phones and the sound

**Streaming the set to visitors' phones over the node's Wi-Fi was considered, and not chosen.**

- **Bandwidth is not the problem.** Ten phones at 64–128 kbit/s is under 1.5 Mbit/s, within what the ESP32 can serve.
- **Sync is.** Every phone buffers differently, so phones drift hundreds of milliseconds behind the speakers and behind each other. Together that sounds like an echo, not a bigger sound system.
- **Captive-portal browsers** often block or stop background audio, and the access point serves at most 10 phones.

The speakers stay the one source. Two alternatives suit the project better:

| Option | What it is | When |
| --- | --- | --- |
| **Take-home excerpt** | After a set, a short excerpt of that night's set can be downloaded from the node, from sunrise the next day (daylight only, like all business). Each night's excerpt is different, like a sealed dial | Possible from the first version |
| **Distributed sound** | Each phone plays a different *layer* of the music (drums, bass, voice) instead of the same mix. Drift matters far less when the parts differ, and the crowd becomes the sound system | A later experiment; it would need Wi-Fi open during the set, an exception to 3.4, and would compete with Bluetooth for the radio |

---

## 5. Open questions

| Question | Notes |
| --- | --- |
| Who brings the speakers | A host, the DJ, or anyone with a pair: whether the jacks are open to any speakers that fit |
| Jack type | Locking and weatherproof, matching the speakers that will be used; and whether to fit the speaker-plugged sense |
| Music rights | Own music, openly licensed music, or an SIAE licence. Settle before the first public set |
| Comune permission | Amplified sound in a public street: hours, volume, season |
| Set length | Fixed, or earned from the day's surplus (3.1) |
| Where the set comes from | Who makes the SUNSET set, and how many sets are in the list |
| Daylight trigger in winter | Short days may rarely reach float; whether the set is a summer-only event |

## 6. Pilot tasks

| Task | What to settle |
| --- | --- |
| **Bluetooth amplifier** | Pairing and reconnection on power-up, refusal of strangers, audio dropouts; switch to the wired DAC (2.3) if any of these fail |
| Test firmware build | Wi-Fi, Bluetooth, MP3 decoding and the pages inside the 1.9 MB app slot |
| Enclosure | Box size for carrier, amplifier, relay and jacks; heat during a set |
| Volume cap | On site, with the neighbours in mind |
| Real power draw | Measured over a full set against the estimate in 2.5 |
| Trigger thresholds | Float reached, and the battery level required at sunset |
| Pops and hum | Power-up and power-down of the amplifier; ground loop between the carrier and the amplifier |
