# Proof of print — a mint interactive node on carrier v1

A SUNSET interactive node that **turns digital stamps into paper stamps, and back.** The visitor spends stamps from their phone and the node prints a small paper stamp: a bearer note that can be handed to anyone in the street, with no phone involved. Brought back to the node, the paper turns into digital stamps again.

It runs on carrier v1 on the battery tier: the panel feeds a Victron SmartSolar MPPT 75/15 and a 12 V LiFePO₄ battery, with JP1 off and the sun sensor compiled out. The tier is specified in [interactive-auction.md](interactive-auction.md), sections 1 and 2; this document covers only what is different.

> Status: draft 3, 22 Oct 2026 (each mint issues two parts, the stamp as artwork and a redeem sticker; the artwork stamp alone is also sold as a souvenir). Artwork to be designed; nothing built. **Nothing here changes the carrier board.**

---

## 1. The idea

- **A mint and a shop.** The print node does two things: it **converts** digital stamps to paper and back, and it **sells** the artwork stamp alone as a souvenir, for digital stamps.
- **Proof of print.** The paper is printed and cut by the machine, signed by it, and recorded by it. It is the same stamp in a different body.
- **Paper circulates by hand.** Once printed, a paper stamp can pass from person to person, like cash, with no phone and no network. It goes back to the printing node only to be turned digital again.
- **Daylight only,** like all SUNSET business: minting and redeeming run from sunrise to sunset.

### Where it sits in SUNSET

| Node | Proof | Direction |
| --- | --- | --- |
| Wall (message nodes) | walk | earn |
| Arm game ([interactive-arm-game.md](interactive-arm-game.md)) | skill | earn |
| Street auction ([interactive-auction.md](interactive-auction.md)) | bid | transfer; listing fee is a sink |
| **Print node** | **print** | **convert** (digital ⇄ paper) and **spend** (souvenir stamp); fees are a sink |
| Flip-dot wall ([interactive-flipdot.md](interactive-flipdot.md)) | mark | spend, paper only |

---

## 2. The paper stamp

### 2.1 The object

- **Round thermal labels on a roll.** Each label is round and self-adhesive, printed by the node.
- **Cut square.** The printer's cutter cuts the backing between labels, so each label comes out on a **square of backing paper**, like a postage stamp on its sheet.
- **Every mint issues two parts:**

| Part | What it is | Carries |
| --- | --- | --- |
| **The stamp** (artwork) | A gift. It has **no value** and can be kept, given, shown, photographed or stuck anywhere | The artwork (to be decided, 5); the node's 5 × 5 logo; date and serial. *(Possible:* the day's sundial dial, dithered, so every stamp shows the sun of the day it was minted*)* |
| **The redeem sticker** | The value. A plain round sticker that turns back into digital stamps (3.2) | Value; the same serial; the QR code with the signed one-time code; a short typed code as fallback |

- **Separating art and value.** The artwork can travel freely as promotion for SUNSET, because copying it costs nothing: there is nothing to steal. All the value, and all the security, sits on the plain sticker. The QR also gets a whole label to itself, so it can be printed larger and read more reliably.
- **The shared serial** links the pair, so a stamp and its sticker can always be matched (provenance), but only the sticker can be redeemed.
- **Stuck to things.** The redeem sticker is adhesive: stuck on an object, it attaches a value to it. A postcard, a bottle or a lot at the auction can carry its price on its back.
- **Printed together.** The two labels are printed one after the other. The cutter can cut after each label (two separate squares) or after the pair (one strip of two, like a *se-tenant* pair of postage stamps). Chosen with the artwork (5).

### 2.2 Denominations

Redeem stickers are printed in **denominations** (for example 1, 5 and 10), so paper behaves like cash: a handful of notes rather than a sheet of ones. The values are set in the pilot.

### 2.3 Its weaknesses, stated

- **Thermal paper is fragile.** It fades with time and light, and darkens with heat (thermal coatings react at roughly 60–70 °C). Stored in the shade it lasts years; left on a dashboard it does not. The project can accept this as a feature: paper money that slowly disappears.
- **Copies are possible.** A photocopy of a redeem sticker's QR is as good as the original until one of them is redeemed. Section 3.3 limits the damage to "first to redeem wins". It is the old question of every printed note, run as a street experiment: what makes a piece of paper trustworthy when anyone can copy it?

---

## 3. The flows

### 3.1 Digital to paper (minting)

1. At the print node, the visitor opens the mint page and chooses the value to print.
2. The stamps are **spent into the node** from the passport page (marked spent on the public list), plus the printing fee (3.4). This is the same step as placing a bid at the auction (interactive-auction.md 3.4).
3. The node writes the new paper stamp to flash (serial, value, code, unspent), signs it, then prints and cuts **the stamp and the redeem sticker**.
4. The visitor takes both from the output slot.

### 3.2 Paper to digital (redeeming)

1. The holder joins the **printing node's** Wi-Fi and scans the redeem sticker's QR with the phone's ordinary camera app, which opens the node's redeem page. (A web page served by the node cannot use the camera itself, because the node's pages are plain HTTP; the phone's own camera app can read the QR and open the link.) The short code can be typed instead.
2. The node checks the signature and that the paper stamp is unspent.
3. It marks the paper stamp spent and issues fresh digital stamps of the same value to the phone (commit and reveal, as in interactive-auction.md 3.5).
4. **The redemption slot:** the redeemed sticker can be dropped into a perspex box beside the node, a growing, visible pile of spent money. Dropping it in is not enforced; the node's spent list is what counts.

### 3.3 Why redemption is at the printing node only

SUNSET nodes learn of each other's spends only when couriers carry blocks between walls. If a paper stamp could be redeemed anywhere, a photocopy could be redeemed at two nodes before either heard of the other. **Redeemed only where it was printed,** the printing node's own spent list is always up to date, and a copy can never be redeemed twice.

**Checking is everywhere; redeeming is at home.** The node signs each stamp with a **public-key signature** (Ed25519 or ECDSA P-256, both within the ESP32's means). Any node, or any phone with the public key, can check that a paper stamp is genuine without being able to redeem it.

### 3.4 The souvenir: the artwork stamp alone

A visitor can also **buy the artwork stamp on its own,** spending digital stamps for a souvenir. No redeem sticker is printed; nothing is converted. The stamps spent leave circulation, so this is a spending node as well as a mint. The price is set in the pilot.

| Mode | The visitor spends | The node prints | Value leaves digital circulation? |
| --- | --- | --- | --- |
| **Convert** | the value + the printing fee | artwork stamp + redeem sticker | The value moves to paper; only the fee leaves |
| **Souvenir** | the souvenir price | artwork stamp only | All of it: a sink |

### 3.5 The printing fee

Minting costs a small fee in stamps (for example 1 per print), set in the pilot. **The fee is what pays for the artwork stamp:** the gift half of every mint. It is a **sink**: those stamps leave circulation. Redeeming is free.

---

### 3.6 Status by serial

Anyone on the print node's Wi-Fi can ask whether a paper stamp is **spent or unspent**, without redeeming it.

- The phone sends **only the sticker's serial,** which is public. It never sends the redeem code, so nothing worth stealing crosses the open Wi-Fi.
- The node answers from its own spent list, which is always up to date (3.3).
- Useful to anyone accepting paper, such as a bar near the print node (SUNSET.md 4.2). A bar can also simply **redeem a sticker on the spot,** from its counter, the moment it is handed over: a sticker redeemed this second cannot have been spent elsewhere.

**The print node is also the gateway** to SUNSET: the entrance to the installation, paired with the flip-dot wall and placed near businesses with footfall (SUNSET.md 4.1).

## 4. Hardware

### 4.1 The printer

| Part | Notes |
| --- | --- |
| **Thermal printer with auto-cutter and label sensing** | A kiosk-type 58 mm (or 80 mm) module with a serial interface, an auto-cutter, and a gap or black-mark sensor so it prints on each round label and cuts the backing between labels. To be confirmed in the pilot: not every receipt module handles die-cut labels |
| **Label roll** | Round die-cut thermal labels on a liner, sized to the printer's paper width. A roll holds a few hundred stamps; refills are a routine task |
| **Printer supply** | From the battery through its own fuse, via a buck converter if the printer needs other than 12 V. Thermal printing and cutting draw roughly 1.5–3 A in short bursts |
| **Output slot** | In the enclosure wall, under cover from rain, with a short chute so the stamp is reachable but the cutter is not |
| **Redemption slot** (optional) | A small perspex box with a letter slot, beside the node |

### 4.2 Pins

The carrier's UART header J10 is taken by the Victron (VE.Direct). The ESP32 has a second hardware UART that can be routed to any spare pins:

| Use | GPIO | Header | Notes |
| --- | --- | --- | --- |
| Printer serial TX | 32 | J9 | UART1, routed to J9 |
| Printer serial RX | 33 | J9 | Printer status: paper out, cutter error, cover open |
| Printer power enable | 26 | J9 | MOSFET or relay on the printer supply; off at boot (pull-down) and between prints |
| Paper-low sensor (optional) | 36 | J9 | If the printer has no serial status for it; input only, external pull-up |
| VE.Direct | 16 RX, 17 TX | J10 | As on every interactive node |
| Clock | 21 / 22 | on board | Dates on the stamps; sunrise and sunset |
| Enclosure temperature probe | 4 | J4 / J5 | Heat check for the paper (4.4) |
| Spare | 13, 14, 27 | J9 | 27 via R19 to the switched 5 V output, unchanged |

### 4.3 Power

| Load | Draw | Notes |
| --- | --- | --- |
| ESP32, Wi-Fi on, sunrise to sunset | about 0.5 W | about 6 Wh a day |
| Printer, per stamp | a few seconds at 1.5–3 A | well under 1 Wh for dozens of stamps |
| Printer idle | none | powered only to print |

The print node is one of the lightest interactive nodes: the battery is there for the printer's bursts, not for its total use.

### 4.4 Heat

The label roll must stay well below the temperature at which thermal paper darkens. Shade or a north-facing site, a ventilated enclosure, and **no printing above a set temperature** read from the probe; the page says why.

---

### 4.5 Counting labels

The node knows how many labels are left:

- **At each refill** the roll's label count is entered (setup on the admin page, or a fixed roll size).
- **Every label printed is counted** and written to flash, so the count survives restarts.
- **Below a threshold** (set in the pilot, for example a day's typical use), the node posts the service notice *labels running low*; at zero, *out of labels*, and minting pauses with a message on its page. The printer's own paper-end sensor is the backstop if the count drifts.
- Minting uses **two labels** (stamp and redeem sticker); a souvenir uses one. The count reflects both.

## 5. Open questions

| Question | Notes |
| --- | --- |
| **Artwork** | The design of the round stamp and the square it is cut from; the plain design of the redeem sticker (2.1) |
| Cut pattern | Each label cut separately, or the pair cut together as a strip of two |
| Souvenir price | How many stamps the artwork stamp costs on its own (3.4) |
| A cash-only node | Specified as the flip-dot wall ([interactive-flipdot.md](interactive-flipdot.md)), which shares the print node's spent list over ESP-NOW |
| Label size and printer | Label diameter, paper width, and a printer that prints and cuts die-cut labels reliably |
| Denominations | Which values, and whether each has its own design |
| Printing fee | How many stamps per print |
| Signature scheme | Ed25519 or ECDSA P-256; how the public key is published so phones can check stamps |
| Redemption slot | Whether to fit it, and what happens to the pile (an artwork in itself, a yearly count) |
| Paper's life | Whether fading is accepted as part of the work, or a longer-life thermal stock is used |

## 6. Pilot tasks

| Task | What to settle |
| --- | --- |
| Printer and labels | Printing on round labels, cutting square, gap sensing, jams |
| QR on the redeem sticker | Smallest label and QR that phone cameras read reliably, with the signature inside it |
| Heat | Temperature inside the enclosure on a summer afternoon; any darkening of the roll |
| Refills | How fast a roll is used, and how refills fit the round of the nodes |
| Copies | Try photocopying a stamp and redeeming both: the second must be refused |
