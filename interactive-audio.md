# The SUNSET set — an audio interactive node on carrier v1

A SUNSET interactive node that plays **the SUNSET set** at sunset. It doesn't play every night, only **when the sun has fully charged the battery that day.** The night's set is announced by a shout.

**The panel is only the transmitter.** The carrier's ESP32 reads the music from its microSD card and streams it over Bluetooth to a registered Bluetooth speaker. Nothing is added inside the enclosure.

It runs on carrier v1 on the battery tier: the panel feeds a Victron SmartSolar MPPT 75/15 and a 12 V LiFePO₄ battery, with JP1 off and the sun sensor compiled out. The tier is specified in [interactive-auction.md](interactive-auction.md), sections 1 and 2; this document covers only what is different.

> Status: draft 3, 22 Oct 2026 (the panel as Bluetooth transmitter to a registered speaker; option of a speaker locker that charges it). Concept only; nothing built. **Nothing here changes the carrier board.**

---

## 1. The idea

- **The sun pays for the music.** The set plays only on a day when the battery reached full charge. A dull day means silence, and the page says why.
- **It starts at sunset,** the moment every SUNSET node keeps. The set is a performance, not business, so it plays after the day's business has closed, on stored sun.
- **The shout comes first.** The node knows it can play as soon as the battery is full, usually early in the afternoon. It posts a shout then ("The SUNSET set plays tonight at [node]"), and couriers have hours to carry it to the walls before sunset.
- **The panel holds the music; the speaker makes the sound.** No amplifier, wiring or sockets on the panel.

---

## 2. Hardware

### 2.1 The panel as transmitter

The carrier's ESP32 is the **original ESP32** (ELEGOO 30-pin, WROOM-32), which can act as a **Classic Bluetooth audio source** (A2DP), as a phone does. It reads MP3 files from the microSD card in the carrier's own socket J8 (already wired, unused by SUNDIAL), decodes them and streams them to the speaker. (The newer ESP32-S3 cannot do this; carrier v1 does not use it.)

- **Nothing added inside the enclosure.** No DAC, no amplifier, no relay, no sockets.
- **No radio clash.** Wi-Fi and Bluetooth share the ESP32's one radio, but the set plays after sunset, when Wi-Fi has closed (3.4). They never run together.
- **Range:** Bluetooth Classic reaches about 10 m in the open, less through the enclosure and the panel. The speaker stays close to the wall, which is where people gather anyway.

### 2.2 Pairing: the registered speaker

A Bluetooth speaker cannot be given a password: speakers pair with "Just Works" (no code) or a fixed PIN such as 0000, because they have no way to type one. The protection is on the ESP32's side:

- **An allowlist.** The ESP32 stores the Bluetooth address of the project's own speaker (or speakers), paired once by the admin. At sunset it connects only to those and ignores every other device.
- **During the set,** a speaker connected to the ESP32 normally refuses a second source, so a stranger's phone cannot take over mid-set.
- **What remains:** someone could clone a registered speaker's address to receive the stream. That is a lot of effort for a free set, and accepted.

### 2.3 Option: the speaker locker

The registered speaker can live **in a transparent locker under the panel**, the same perspex-doored locker as the street auction's, which keeps it safe and **charged**.

| Part | Notes |
| --- | --- |
| **Locker** | Perspex door, locked fail-secure (as in interactive-auction.md 2.3). Opened only for maintenance |
| **Acoustic door** | The speaker plays from inside the locker, so the door needs a grille or perforated panel: plain perspex muffles the sound |
| **Charger** | A 12 V → 5 V USB buck (2–3 A) from the battery, switched on and off by the ESP32 through a MOSFET. Not from the carrier's own 5 V outputs, which are fused at 0.5 A |
| **Temperature probe** | Inside the locker. The speaker's own lithium battery must not charge in heat |

- **The sun charges the speaker.** The charger runs only once the battery has reached float: the day's surplus fills the speaker, and the speaker plays it back at sunset. This restores "the sun pays for the music" literally.
- **The speaker never leaves.** It plays in place, so there is nothing to carry, lend or lose.
- **Heat is the main risk.** A lithium battery in a sun-heated perspex box should not charge above about 45 °C and should not sit for long above about 60 °C. The locker needs shade or a north-facing site, ventilation, and a firmware rule: no charging above the limit (the threshold is set in the pilot).

### 2.4 Pins

| Use | GPIO | Header | Notes |
| --- | --- | --- | --- |
| Speaker charger (locker option) | 32 | J9 | To the charger's MOSFET or enable pin; pull-down so it is off at boot |
| Locker lock (locker option) | 26 | J9 | Through the lock driver, as on the auction node |
| Locker door switch (locker option) | 33 | J9 | Reed switch to GND, pull-up to 3V3 |
| microSD | 5, 18, 19, 23; card-detect 39 | on board (J8) | Already wired on carrier v1 |
| VE.Direct | 16 RX, 17 TX | J10 | As on every interactive node |
| Clock | 21 / 22 | on board | Sunset time and the end-of-set time |
| Locker temperature probe | 4 | J5 | Second probe terminal, already on the carrier |
| Spare | 13, 14, 27, 36 | J9 | 36 is input only |

Without the locker option, only the microSD card, VE.Direct and the clock are used.

### 2.5 Power

| Load | Draw | Per day |
| --- | --- | --- |
| ESP32 streaming, Wi-Fi off | about 0.5 W | under 1 Wh for an hour's set |
| Speaker charging (locker option) | about 5–10 W while charging | the speaker's own battery capacity, typically 20–40 Wh, only on full-battery days |

The node's own cost is small; with the locker, charging the speaker is the main load, and it only ever draws on surplus.

---

## 3. The rules

### 3.1 When it plays

| Condition | Source |
| --- | --- |
| The battery reached **float** (full) at some point today | The Victron's charge state, over VE.Direct |
| The battery is still above a set level at sunset | The Victron's battery voltage and charge state |
| Inside the season and the permitted hours | Settings, from the comune's rules (3.3) |
| The registered speaker is in range | The ESP32's Bluetooth connection |

If the first three are met, the shout goes out when the battery first reaches float. At sunset the ESP32 connects to the registered speaker and the set starts. If the speaker cannot be found by the latest end time, the night passes in silence.

**How long it plays** is a setting, tuned in the pilot: **fixed** (for example 45–60 minutes), or **earned**, following the day's surplus from the Victron's daily yield.

### 3.2 What it plays

- **The SUNSET set:** music on the microSD card, loaded at the yearly visit or by the admin.
- Each night can play the next set in a list, so the town doesn't hear the same hour every time.
- **Rights:** public performance in Italy normally needs an SIAE licence. The simplest course is music the project owns or that is openly licensed (Creative Commons with commercial use allowed). To be settled before the first set (5).

### 3.3 Volume and neighbours

- **A volume cap,** set through the Bluetooth stream's volume and fixed in firmware, below the speaker's maximum.
- **A fixed latest end time,** whatever the set length, inside the comune's quiet hours.
- Choose sites where the sound carries along the street, not into bedrooms.

### 3.4 Wi-Fi

The day's business closes at sunset on every SUNSET node, and the audio node keeps the rule: its Wi-Fi serves pages in daylight (whether tonight's set is on, past sets) and closes at sunset. The music plays with Wi-Fi off, which is also what lets Bluetooth have the radio.

---

## 4. Phones and the sound

**Streaming the set to visitors' phones over the node's Wi-Fi was considered, and not chosen.**

- **Bandwidth is not the problem.** Ten phones at 64–128 kbit/s is under 1.5 Mbit/s, within what the ESP32 can serve.
- **Sync is.** Every phone buffers differently, so phones drift hundreds of milliseconds behind the speaker and behind each other. Together that sounds like an echo, not a bigger sound system.
- **Captive-portal browsers** often block or stop background audio, and the access point serves at most 10 phones.

The speaker stays the one source. Two alternatives suit the project better:

| Option | What it is | When |
| --- | --- | --- |
| **Take-home excerpt** | After a set, a short excerpt of that night's set can be downloaded from the node, from sunrise the next day (daylight only, like all business). Each night's excerpt is different, like a sealed dial | Possible from the first version |
| **Distributed sound** | Each phone plays a different *layer* of the music (drums, bass, voice) instead of the same mix. Drift matters far less when the parts differ | A later experiment; it would need Wi-Fi open during the set, an exception to 3.4, and would compete with Bluetooth for the radio |

---

## 5. Alternatives considered

| Alternative | Why not first |
| --- | --- |
| **Amplifier inside the enclosure, with two weatherproof speaker jacks;** speakers plugged in for the set | More parts in the box (amplifier, relay, jacks), a bigger enclosure, and the amplifier's own pairing or wiring. Kept as a fallback if the Bluetooth speaker proves unreliable |
| **Wired I2S DAC** (PCM5102 class) into an amplifier, on GPIO 26, 13 and 14 | Only needed with an amplifier and if Bluetooth fails |
| **Phones as the sound system** | See 4 |

---

## 6. Open questions

| Question | Notes |
| --- | --- |
| Docked or brought | The speaker locker (2.3), or a registered speaker brought to the wall by a host for each set |
| Acoustic door | Grille, perforated perspex or mesh: enough sound out, nothing in |
| Music rights | Own music, openly licensed music, or an SIAE licence. Settle before the first public set |
| Comune permission | Amplified sound in a public street: hours, volume, season |
| Set length | Fixed, or earned from the day's surplus (3.1) |
| Where the set comes from | Who makes the SUNSET set, and how many sets are in the list |
| Daylight trigger in winter | Short days may rarely reach float; whether the set is a summer-only event |

## 7. Pilot tasks

| Task | What to settle |
| --- | --- |
| **Bluetooth link** | Connection to the registered speaker at sunset, reconnection after dropouts, refusal of strangers, range through the enclosure and the panel |
| Test firmware build | Wi-Fi, Bluetooth, MP3 decoding and the pages inside the 1.9 MB app slot |
| Speaker locker (if used) | Heat inside the locker in summer; the charging temperature limit; sound through the door |
| Volume cap | On site, with the neighbours in mind |
| Real power draw | Streaming and speaker charging, against the estimate in 2.5 |
| Trigger thresholds | Float reached, and the battery level required at sunset |
