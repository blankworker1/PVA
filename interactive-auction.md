# Interactive nodes and the street auction — specified against carrier v1

The PVA carrier board v1 ([hardware/CARRIER.md](hardware/CARRIER.md)) was designed for a SUNDIAL wall panel: no battery, awake from dawn to dusk. This document specifies a second way of using **the same board, unchanged**: an **interactive node** on a battery, and the first interactive node, **the street auction**.

The interactive nodes belong to **SUNSET** (PVA no. 2, formerly GO TO BED), a network of panels that carry messages and stamps between walls. Where SUNDIAL is about time, SUNSET is about one moment in it: every day's business closes at sunset. They are specified here because they are a use of carrier v1, like the three layers in [USES.md](USES.md).

> Status: draft 2, 22 Oct 2026 (three lockers; business in daylight only; evening lights on the battery). Concept and rules settled in discussion; nothing built. Nothing here changes the carrier board.

---

## 1. Two power tiers, one board

**The rule: the power tier follows the load, not the role.** A node that only serves pages and keeps records is a wall node. A node that moves, flips, lights or releases something is an interactive node.

| | Wall node | Interactive node |
| --- | --- | --- |
| Examples | SUNDIAL panels; SUNSET message walls; a data-only auction | The street auction (lockers); the robot arm; the flip-dot wall |
| Panel connects to | Carrier J1 directly | Victron SmartSolar MPPT 75/15 → 12 V LiFePO₄ battery → MPPT load output → carrier J1 |
| JP1 (sun-sensor jumper) | **On** | **Off**, and the sun sensor compiled out of the firmware |
| Sun reading | The carrier's own short-circuit current: true light level | Victron PV voltage and power over VE.Direct: energy harvested |
| GPIO 34 divider reads | Panel voltage (dawn and dusk gates) | Battery voltage (a cross-check of the Victron's figure) |
| Battery data | None | Victron: battery voltage and current, charge state, yield today |
| Awake | Dawn to dusk, off at night | Business sunrise to sunset; lights after sunset (about four hours, set in the pilot), then asleep until sunrise (1.2) |
| Temperature probe, clock, Wi-Fi, storage | Same | Same |
| Firmware | Wall build | Interactive build |

### 1.1 Why JP1 must be off

Every 10 seconds the sun sensor's MOSFET (Q1) shorts `PV+` to ground through the 5 mΩ shunt, before the fuse. A panel is a current source and gives at most about 6 A into that short, which is the whole point of the sensor. **A battery is not a current source:** the same pulse would be a dead short of a 12 V LiFePO₄ pack.

- **JP1 is a physical jumper** (a 2-pin header between GPIO 25 and the gate driver U3). With the jumper removed, Q1 cannot be switched on, whatever the firmware does.
- **The interactive build also compiles the sun sensor out** (`SUN_SENSOR 0`), so GPIO 25 is never driven high, even if someone refits the jumper.
- The Victron's own load-output protection is a third line, not a substitute for the first two.

The carrier cannot keep its own sun measurement on this tier: the panel now feeds the Victron, and shorting the Victron's input every 10 seconds would discharge its input capacitors through Q1 and upset its tracking.

### 1.2 Sunset is the moment

SUNDIAL seals each day's dial at Bosa's sunset. SUNSET keeps the same moment: **the day's business closes at sunset.** The auction's hammer falls, the day's records seal, and the whole network keeps one rhythm.

- **Sunset comes from the clock,** computed for Bosa as SUNDIAL's seal already is (`sunTimes`), not from the panel or battery voltage. A cloudy afternoon must not end the auction early.
- **All business is in daylight.** Listing, bidding, collecting and returning happen between sunrise and sunset, and nowhere else. At sunset the Wi-Fi closes.
- **The battery keeps the lights on after sunset,** about four hours as the starting point. In Sardinia the street is busiest in the evening, so the lockers stay lit: the result of the day's hammer, and tomorrow's lot waiting in the wings, readable from the pavement. Nothing can be done until sunrise.
- **Then the node sleeps.** The lights go out and the ESP32 deep-sleeps until sunrise.
- **The lighting routine is not fixed here.** Which lockers are lit, in which colours, how bright, by day or only in the evening, and for how long, is a firmware setting, tuned on the built hardware during the pilot (6).
- The battery smooths cloudy days and motor or solenoid surges, and lights the evening. It does not move the close of the day.

**The sun is the coin slot.** Actions that cost energy (a grab, a flip, a door) are offered only when the battery's charge state allows. A dull week means fewer actions, and the page says so.

### 1.3 What the Victron data means

The VE.Direct text protocol sends a block of values about once a second (19200 baud): battery voltage and current, PV voltage and power, charge state, yield today, load-output state.

- **PV power is energy harvested, not light.** When the battery is full the Victron backs off the panel, so on full-battery days an interactive node's dial understates the sun. Interactive-node dials are labelled accordingly. Only wall nodes measure the sun.
- **Check the 75/15's VE.Direct signal level before wiring.** If its TX is 5 V, put a resistor divider on the ESP32's RX pin.

---

## 2. Carrier v1 on the battery tier

### 2.1 Wiring

```
 PV panel ──► Victron MPPT 75/15 (PV in)        battery ◄──► MPPT (battery terminals)
                     │
                     ├── LOAD out (low-voltage disconnect) ──► fuse ──► carrier J1 (PANEL +/−)
                     │                                           └──► fuse ──► 12 V line to the off-board driver
                     └── VE.Direct ──► carrier J10 (GPIO 16 RX, 17 TX, GND)
```

- **Panel to MPPT:** a recycled panel's open-circuit voltage (44.5 V on the TSM-185DC01 label, about 48 V on a cold morning) is well inside the 75 V limit.
- **Carrier power:** J1 takes the MPPT load output. The buck converter turns about 13 V into the usual 5 V rail. The low-voltage disconnect protects the battery.
- **Supercapacitors:** harmless with a battery; fit them or leave them out.
- **Heavy loads stay off the carrier.** Solenoids and lights run from their own fused 12 V line through a small off-board driver (2.3). The carrier's take-offs (F2 0.5 A at 5 V, F3 0.2 A at 3.3 V) are for small sensors, not locks.
- **AUX (J12)** is not used on this tier: the battery and load output replace it.

### 2.2 Pins for the auction node

All from the spare-pins header J9 and the UART header J10. Nothing on the ESP32 strapping pins.

| Use | GPIO | Header | Notes |
| --- | --- | --- | --- |
| Lock, locker A | 26 | J9 | To the driver's MOSFET gate; pull-down on the driver board |
| Lock, locker B | 13 | J9 | Same |
| Lock, locker C | 27 | J9 | Same. **Remove R19** on the carrier: this gives up the switched 5 V output (U4), which nothing on the battery tier uses |
| Door switch, locker A | 32 | J9 | Reed switch to GND, pull-up to the header's 3V3 |
| Door switch, locker B | 33 | J9 | Same |
| Door switch, locker C | 36 | J9 | Same; input only, and has no internal pull-up, so the external pull-up is required |
| Interior lights (LED data) | 14 | J9 | One data line for all three lockers (addressable strips chain). Through a 3.3 → 5 V level shifter on the driver board. GPIO 14 toggles briefly at boot: the lights may flicker on reset, the locks never do |
| VE.Direct | 16 RX, 17 TX | J10 | Divider on RX if the Victron sends 5 V |
| Clock | 21 / 22 | on board | DS3231, already fitted |
| Temperature probe | 4 | J4 | Inside the locker housing: the heat check (3.6) |

Every J9 pin is now in use. More lockers, or a switch for the light supply, would come from an I2C port expander (MCP23017 class, 16 pins) on the I2C header J13, with no other change.

### 2.3 The off-board driver

A small board beside the carrier, on the 12 V line:

- 3 logic-level N-MOSFETs with flyback diodes and gate pull-downs, one per lock;
- a 12 V → 5 V buck for the interior lights (addressable RGB, a short strip per locker);
- a 74AHCT125-class level shifter for the LED data line;
- screw terminals for the locks, lights and door switches.

**Locks are fail-secure:** solenoid latches that stay locked without power and open on a short pulse (about 1 s). Doors stay shut through any fault, reboot or flat battery.

### 2.4 Power, roughly

| Load | Draw | Per day |
| --- | --- | --- |
| ESP32, Wi-Fi on, sunrise to sunset | ~0.5 W | ~6 Wh over 12 h |
| ESP32, Wi-Fi off, evening lights | ~0.1–0.2 W | < 1 Wh |
| Interior lights, three lockers, dimmed | ~1–2 W per locker | the largest item: ~12–24 Wh for four evening hours, plus any daytime lighting. An estimate until the pilot sets the routine |
| Light strips switched to black overnight | standby of the LED chips | ~1–3 Wh; removable later with a supply switch on an expander pin |
| Locks | ~0.5–1 A at 12 V for ~1 s, a few times a day | negligible |

Roughly 30–40 Wh a day. A 12 V 20–40 Ah LiFePO₄ pack (about 250–500 Wh) and a recycled panel cover this with several dull days in reserve. Size the battery to the lights. If the charge state falls low, the evening lights are the first thing to shorten.

---

## 3. The street auction

A fully automated street auction: three lockers with lit interiors and transparent perspex doors, one lot a day, settled in SUNSET stamps. Nobody attends it. **The catalogue is the street itself:** everything for sale is visible from the pavement all day.

### 3.1 Stage and wings

Three lockers, each with one job a day. The roles rotate at every sunrise:

| Locker | Today's job | At next sunrise becomes |
| --- | --- | --- |
| **Wings in** | Takes tomorrow's lot, any time from sunrise to sunset (1 stamp to list) | Stage |
| **Stage** | Today's lot on auction; the hammer falls at sunset | Wings out |
| **Wings out** | Yesterday's lot: the winner collects until midday, then the seller takes it back until sunset | Wings in (empty) |

One lot is auctioned per day. If nobody lists a lot, tomorrow's stage is empty and it is a rest day.

Each door has one job a day, so a seller can list at any hour of daylight, and the winner and the seller never compete with a new listing for the same door.

### 3.2 A lot's life

| When | What happens |
| --- | --- |
| Day N, sunrise to sunset | The lot is on the **stage**. Anyone at the node can bid in stamps |
| Day N, sunset | **The hammer.** Bidding ends; no further bids. The highest bid wins |
| Day N, sunset to four hours after | Business is closed. The stage locker shows *sold* or *unsold* in its light |
| Day N+1, sunrise to midday | The locker is now **wings out**. The winner collects with their winning-bid token |
| Day N+1, from sunrise | The seller can redeem the winning stamps at any time in daylight (no locker needed; the node holds them) |
| Day N+1, midday to sunset | If not collected, the winner forfeits: the seller keeps the stamps **and** can take the goods back with their seller token. The node posts an automatic **shout** ("Locker A uncollected"), which couriers carry to every wall |
| Day N+1, still full at sunset | The lot is abandoned. At the next sunrise it **goes back on stage**, relisted automatically; its proceeds are burned |

A lot with no bids at the hammer goes to wings out for the seller to take back, under the same timings, and is relisted the same way if still there at sunset.

**When an abandoned lot is relisted,** two lots want tomorrow's stage: the relisted one and the new one waiting in wings in. **The relisted lot goes on stage first; the new lot waits one more day in wings in,** and no new listings are taken until it moves. It is rare, and the rotation stays intact.

### 3.3 Locker states

| State | Light colour | Who can open the door |
| --- | --- | --- |
| Empty (wings in) | (dim or off) | A seller, for 1 stamp |
| On stage | for sale | Nobody |
| Sold, awaiting collection | sold | The winner's token, until midday |
| Uncollected or unsold | return to seller | The seller's token, until sunset |
| Listed, waiting in wings in | coming tomorrow | Nobody |
| Relisted | for sale (next day) | Nobody |

**The light is the message.** Without accounts or contact details, the node cannot tell anyone anything directly; the colour of each locker, readable from the street, is the status. The seller token also shows the lot's status on the node's page, and uncollected lots are announced by shout.

After sunset the lights can show the day's result to the evening street (1.2); the colours and routine are set in the pilot (6).

A door switch on each locker confirms that the door was opened and closed again, so each locker resets itself.

### 3.4 Stamps and settlement

- **Listing costs 1 stamp.** It is the auction's only sink, apart from burned relist proceeds. Everything else is a transfer from buyer to seller.
- **A bid needs the stamps in hand.** Bidding spends them into the node (marked spent on the public list) and gives the bidder a bid receipt.
- **Outbid:** the node at once issues fresh stamps of the same value back to the bidder.
- **Won:** the stamps stay with the node until the seller redeems them, as fresh stamps.
- **Why spent, not "locked":** SUNSET nodes learn of each other's spends only when couriers carry blocks between walls. A stamp merely marked as locked at the auction could be spent at another wall before the news arrived. Spending into the node means the only valid copies are the ones it holds, so nothing can be spent twice. To the user it behaves exactly like "locked until paid or returned".

No separate escrow is needed: **the firmware is the escrow.** Every lot ends with the seller holding either the stamps or the goods (or, if the winner never comes, both).

### 3.5 Tokens on an open network

The node's Wi-Fi is open and plain HTTP: anything sent can be read by anyone in range (USES.md 4.3). A token sent in clear could be copied by a bystander, who would reach the locker first. So tokens are **commit and reveal**:

1. **At bid time** (or at listing, for the seller), the phone makes its own random secret and sends only its hash. The node records the hash against the bid or lot and signs the receipt (HMAC-SHA256 with a key only the node holds).
2. **At collection,** the phone reveals the secret. The node checks it against the hash, opens the door at once and marks the token used.

Anyone listening sees the secret only at the moment it stops being worth anything. Tokens are bearer: whoever holds the phone's secret holds the claim. Tokens are saved in the visitor's passport page beside their stamps.

**On the node:** flash encryption on, so a stolen board does not give up the signing key. Every state change (bids, tokens issued and used, locker states) is written to flash before it is acted on, so a reboot or brown-out resumes exactly where it was and no door ever opens twice.

### 3.6 Practical rules

- **No food, liquids or batteries.** A lit perspex box in the Sardinian sun is an oven. Choose a shaded or north-facing site; the temperature probe sits inside the housing and the page shows the reading.
- **Size limit:** whatever fits the locker and closes the door.
- **Visibility is the moderation.** Nothing can be hidden behind perspex, and listing costs a stamp, so dumping has a price.
- **Client limit:** up to 10 phones at once; pages keep connections short (bid, then go).

---

## 4. Firmware: the interactive build

Same firmware family as the wall nodes, built with:

| Setting | Wall build | Interactive build |
| --- | --- | --- |
| `SUN_SENSOR` | 1 | 0 (GPIO 25 never driven) |
| `PANEL_SENSE` | panel voltage, dawn and dusk gates | battery voltage, cross-check only |
| `VE_DIRECT` | 0 | 1, on UART2 (GPIO 16/17) |
| Close of the day | dusk from panel voltage | Bosa's sunset from the clock: Wi-Fi closes, the evening lighting routine runs, then deep sleep until sunrise |
| Node role | wall | auction (locks, door switches, lights) |

New for the auction: the three-locker rotation (3.1) and locker states (3.3), bid handling and stamp issue (3.4), commit-and-reveal tokens (3.5), the automatic shout, and the colour code on the lights.

---

## 5. Open questions

| Question | Notes |
| --- | --- |
| A maintenance path for a dead controller | BOX's rule is "no override, ever", but a dead board would trap a lot. Decide between that purity and a sealed, tamper-screwed manual release |
| Exact cut-off times | Midday for collection, sunset for seller returns: confirm against how people actually use the street |
| Bid steps and opening bid | Minimum increment; whether the seller can set a reserve |
| Comune permission | An unattended street exchange is the piece most likely to need a word with the comune before Bosa 2027 |
| Stamp format | Depends on SUNSET's bearer-stamp spec (public unspent list, node logos, passport page) |
| Prior art | Check "world's first fully automated street auction" before using it publicly |

---

## 6. Pilot tasks

Settled on the built hardware, not on paper. The firmware is written so each of these is a setting, not a rebuild.

| Task | What to settle |
| --- | --- |
| **Lighting routine** | Which lockers are lit and when (day, evening, both), colours for each state, brightness, how long after sunset (about four hours to start), and how the routine shortens when the battery is low |
| Cut-off times | Midday for collection and sunset for seller returns, against how people actually use the street |
| Heat | Temperature inside the housing on a summer afternoon, with and without daytime lighting |
| Power budget | The real daily draw against the estimate in 2.4, and the battery size it calls for |
