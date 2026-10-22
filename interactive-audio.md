# The SUNSET set — an audio interactive node on carrier v1

A SUNSET interactive node with a 12 V amplifier and speakers, playing **the SUNSET set** at sunset. It doesn't play every night, only **when the sun has fully charged the battery that day.** The night's set is announced by a shout.

It runs on the same carrier v1, on the battery tier: the panel feeds a Victron SmartSolar MPPT 75/15 and a 12 V LiFePO₄ battery, with JP1 off and the sun sensor compiled out. The tier is specified in [interactive-auction.md](interactive-auction.md), sections 1 and 2; this document covers only what is different.

> Status: draft 1, 22 Oct 2026. Concept only; nothing built. Nothing here changes the carrier board.

---

## 1. The idea

- **The sun pays for the music.** The set plays only on a day when the battery reached full charge. A dull day means silence, and the page says why.
- **It starts at sunset,** the moment every SUNSET node keeps. The set is a performance, not business, so it plays after the day's business has closed, on stored sun.
- **The shout comes first.** The node knows it can play as soon as the battery is full, usually early in the afternoon. It posts a shout then ("The SUNSET set plays tonight at [node]"), and couriers have hours to carry it to the walls before sunset.

---

## 2. Hardware

### 2.1 What is added beside the carrier

| Part | Notes |
| --- | --- |
| **Amplifier** | 12 V class-D stereo board, TPA3116 class, 2 × 30–50 W. Runs straight off the battery through its own fuse, never through the carrier |
| **I2S DAC** | PCM5102 class, powered from the header's 3V3. Turns the ESP32's digital audio into a line signal for the amplifier |
| **Amplifier power relay** | 12 V supply to the amplifier, switched by a relay whose coil runs from the carrier's switched 5 V output (`5V SW`, J11). Carrier v1 already has this: U4 under GPIO 27 (R19 fitted), with D4 to absorb the coil's kick (CARRIER.md section 9) |
| **Speakers** | Weatherproof outdoor speakers (IP65 or marine class), mounted to throw away from the nearest homes |
| **microSD card** | In the carrier's own socket J8 (already wired, unused by SUNDIAL). Holds the music |

The amplifier is powered only for the set. Idle, it draws nothing.

### 2.2 Pins

The audio node has no locks, so J9 has room.

| Use | GPIO | Header | Notes |
| --- | --- | --- | --- |
| I2S bit clock | 26 | J9 | To the DAC |
| I2S data | 13 | J9 | To the DAC |
| I2S word select | 14 | J9 | To the DAC. GPIO 14 toggles briefly at boot; the amplifier is unpowered then, so nothing is heard |
| Amplifier mute | 32 | J9 | Held muted at power-up and power-down, against pops |
| Amplifier power (relay) | 27 | via R19 to U4 | Unchanged from the carrier: R19 stays fitted |
| microSD | 5, 18, 19, 23; card-detect 39 | on board (J8) | Already wired on carrier v1 |
| VE.Direct | 16 RX, 17 TX | J10 | As on every interactive node |
| Clock | 21 / 22 | on board | Sunset time and the end-of-set time |
| Spare | 33, 36 | J9 | 36 is input only |

### 2.3 Power

| Load | Draw | Per set |
| --- | --- | --- |
| Amplifier and speakers, moderate volume | about 10–15 W average (music averages well below the rated power) | about 15 Wh an hour |
| ESP32 playing from the card, Wi-Fi off | about 0.3–0.5 W | under 1 Wh an hour |

An hour's set costs about 6 % of a 20 Ah battery (about 250 Wh). The rule that it plays only on a full-battery day means the music never eats into the next day's business.

---

## 3. The rules

### 3.1 When it plays

| Condition | Source |
| --- | --- |
| The battery reached **float** (full) at some point today | The Victron's charge state, over VE.Direct |
| The battery is still above a set level at sunset | The Victron's battery voltage and charge state |
| Inside the season and the permitted hours | Settings, from the comune's rules (3.3) |

If all three are met, the shout goes out when the battery first reaches float, and the set starts at sunset.

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
- Speakers aimed along the street, away from bedroom windows.

### 3.4 Wi-Fi

The day's business closes at sunset on every SUNSET node, and the audio node keeps the rule: its Wi-Fi serves pages in daylight (today's forecast for the set, past sets) and closes at sunset. The music plays with Wi-Fi off.

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
| **Distributed sound** | Each phone plays a different *layer* of the music (drums, bass, voice) instead of the same mix. Drift matters far less when the parts differ, and the crowd becomes the sound system | A later experiment; it would need Wi-Fi open during the set, an exception to 3.4 |

---

## 5. Open questions

| Question | Notes |
| --- | --- |
| Music rights | Own music, openly licensed music, or an SIAE licence. Settle before the first public set |
| Comune permission | Amplified sound in a public street: hours, volume, season |
| Set length | Fixed, or earned from the day's surplus (3.1) |
| Where the set comes from | Who makes the SUNSET set, and how many sets are in the list |
| Daylight trigger in winter | Short days may rarely reach float; whether the set is a summer-only event |

## 6. Pilot tasks

| Task | What to settle |
| --- | --- |
| Volume cap and speaker aim | On site, with the neighbours in mind |
| Real power draw | Measured over a full set against the estimate in 2.3 |
| Trigger thresholds | Float reached, and the battery level required at sunset |
| Pops and hum | Mute sequencing at power-up and power-down; ground loop between the carrier and the amplifier |
| Heat | Amplifier and speakers in a closed housing on a summer afternoon |
