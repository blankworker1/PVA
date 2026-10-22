# SUNSET — PVA no. 2

SUNSET is the second work of **PVA (Photovoltaic Art)**, after [SUNDIAL](README.md). Where SUNDIAL is about time, SUNSET is about one moment in it: **every day's business closes at sunset.** (Its working title was GO TO BED.)

SUNSET is **nine recycled solar panels** on the walls of a town, forming a small offline network with its own currency. People earn **stamps** by walking messages between walls and by skill, and spend them at an auction, a mint and a wall of mechanical pixels. Every panel runs on its own sun, on the same carrier board as SUNDIAL, and everything that happens is unattended, anonymous and over by sunset.

> Status: draft 1, 22 Oct 2026. The five interactive nodes are specified in their own documents; the wall nodes and the stamp format are still to be written. Nothing is built.

---

## 1. Nine panels

**A PVA work is always nine panels.** SUNSET has four wall nodes and five interactive nodes.

| Panel | Kind | What it does | Specification |
| --- | --- | --- | --- |
| Wall 1–4 | **Wall node** | Message walls: visitors post and read messages; couriers (visitors) carry messages between walls and earn stamps for it. The network's news, and the main source of new stamps | To be written |
| Street auction | Interactive | One lot a day in three lit perspex lockers; bids in stamps; the hammer falls at sunset | [interactive-auction.md](interactive-auction.md) |
| Arm game | Interactive | A robot arm in a perspex case; drop a peg in a hole, earn a stamp | [interactive-arm-game.md](interactive-arm-game.md) |
| Print node | Interactive | Turns digital stamps into paper stamps and back; sells the artwork stamp as a souvenir | [interactive-print.md](interactive-print.md) |
| Flip-dot wall | Interactive | Mechanical pixels flipped only with paper stamps; a sticker wall for the spent ones | [interactive-flipdot.md](interactive-flipdot.md) |
| The SUNSET set | Interactive | Plays music at sunset to a registered Bluetooth speaker, only on days the sun has filled its battery | [interactive-audio.md](interactive-audio.md) |

### 1.1 Two power tiers, one board

Every panel uses the **PVA carrier board v1** ([hardware/CARRIER.md](hardware/CARRIER.md)), unchanged. **The power tier follows the load, not the role** (interactive-auction.md 1):

| | Wall nodes (4) | Interactive nodes (5) |
| --- | --- | --- |
| Power | The panel straight into the carrier, no battery | Panel → Victron MPPT 75/15 → 12 V LiFePO₄ battery → carrier |
| Awake | Dawn to dusk | Business sunrise to sunset; some keep lights or music after sunset on stored sun |
| Sun reading | The panel's short-circuit current: true light | The Victron's figures: energy harvested |
| Firmware | Wall build | Interactive build, one role per node |

---

## 2. The stamp economy

**One stamp type** everywhere. Each stamp carries the **5 × 5 logo** of the node that issued it, so its origin is visible, but every stamp spends the same. Stamps are **bearer**: no accounts, no names. They live in the visitor's **passport page** on their phone, or on paper.

### 2.1 Every node is a proof

| Node | Proof | Direction | Notes |
| --- | --- | --- | --- |
| Wall nodes | **walk** | earn | Stamps for carrying messages between walls |
| Arm game | **skill** | earn | Stamps for a peg dropped cleanly; harder holes pay more |
| Street auction | **bid** | transfer | Buyer's stamps go to the seller; the listing fee is a sink |
| Print node | **print** | convert, and spend | Digital ⇄ paper; the printing fee and the souvenir are sinks |
| Flip-dot wall | **mark** | spend, **paper only** | Each flip burns a paper stamp |
| The SUNSET set | **sun** | (none) | No stamps: the sun pays for the music |

### 2.2 Stamps in, stamps out

- **In:** walking (walls) and skill (arm game). Both are limited by the sun: the walls are awake only in daylight, and the arm game only plays while its battery allows. **Issuance is energy-backed.**
- **Out (sinks):** the auction's listing fee and burned relists, the print node's fee and souvenirs, and every flip of a dot.
- **Moving:** auctions move stamps between people; paper moves them hand to hand, with no phone.
- **No cash value, ever.** Stamps cannot be bought or redeemed for money. Their value is only in what they can be used for in the town.

### 2.3 Paper money

The print node turns digital stamps into **paper stamps**: an artwork stamp (a gift, no value) and a **redeem sticker** (the value). Paper can pass from hand to hand like cash, so **people without a phone can take part:** someone hands them a sticker, and they spend it at the flip-dot wall, which accepts only paper. The print node and the flip-dot wall share one spent list over ESP-NOW, so a copied sticker can never be spent twice.

---

## 3. A day of SUNSET

| When | What happens |
| --- | --- |
| **Sunrise** | The nodes wake. Business opens. Last night's auction winners can collect their lot (until midday) from **wings out**. The flip-dot panel still shows yesterday's picture |
| **Morning** | A newcomer joins the first wall they meet: a passport page, the rules on one screen, and a message to carry. A few minutes' walk later, at the next wall, their first stamp |
| **Through the day** | Walking wall to wall earns stamps. The arm game is the playful detour: a queue, a peg, a cheer when it drops. The lit lockers show today's lot on stage and tomorrow's in the wings, so people come back to check the bids |
| **Afternoon** | If the SUNSET set's battery is full, its shout goes round the walls: *the set plays tonight*. People spend at the print node, for a souvenir or for paper to take to the flip-dot wall. Spent stickers go up on the sticker wall |
| **Sunset** | **The moment.** The auction's hammer falls. All business stops on every node. If the sun has earned it, the set begins at the wall |
| **Evening** | The lockers glow in their state colours for a few hours; the flip-dot picture holds with no power; the set plays out. Nothing can be bought or sold until sunrise |
| **Night** | Dark and silent. The wall nodes are off; the interactive nodes sleep |

---

## 4. Layout

The positions are chosen on site; the logic is:

| Panel | Where | Why |
| --- | --- | --- |
| **Walls 1–4** | Spread to the edges of the route | Distance is what makes proof of walk mean something: the walls set the shape of the walk |
| **Print node + flip-dot wall** | **As a pair,** within ESP-NOW range (tens of metres along a street) | They share one spent list; the mint, and the wall where its money is spent |
| **Street auction** | Where people already pass | Its catalogue is the street itself |
| **The SUNSET set** | The town's **sunset spot,** a west-facing place where people already gather to watch the sun go down | The set starts at sunset; choose neighbours who can live with an hour of music |
| **Arm game** | In shade | Servos and electronics in a perspex case |

The walls and the interactive nodes interleave along the route, so a walk between walls passes the places to spend.

---

## 5. The first five minutes

A visitor meets five kinds of node in one day. Each needs one obvious first step, and the **first wall explains the whole economy on one screen:**

1. **Earn** by walking messages between walls, or by skill at the arm game.
2. **Spend** at the auction, the print node or the flip-dot wall.
3. **Paper** stamps work without a phone.
4. **Everything closes at sunset.**

---

## 6. Rules shared by every node

| Rule | Where it is specified |
| --- | --- |
| Business only in daylight; sunset from the clock, as SUNDIAL's seal | interactive-auction.md 1.2 |
| No identities: no accounts, no names; bearer stamps and tokens | interactive-auction.md 3.5 |
| Commit and reveal for every token and stamp sent over the open Wi-Fi | interactive-auction.md 3.5 |
| Every state change written to flash before it is acted on | interactive-auction.md 3.5 |
| Interactive nodes: JP1 off, sun sensor compiled out | interactive-auction.md 1.1 |
| Messages on the walls vanish within 7 days; nothing attributable is kept | Wall node specification (to be written) |

---

## 7. Not in the first season

Each of these fits SUNSET's design and is kept for a later season or a fork:

- **A radio node** linking SUNSET to the next village, and **relay panels** in between: a network of villages.
- **A second flip-dot wall,** or a reclaimed bus-sign panel instead of a new one.
- **Distributed sound:** phones playing layers of the set (interactive-audio.md 4).

---

## 8. Open questions

| Question | Notes |
| --- | --- |
| **Wall node specification** | Messages (whisper and shout), couriers and blocks, proof of walk, the passport page, firmware on the wall tier |
| **Stamp format** | The bearer-stamp design shared by all nodes: the public unspent list, the 5 × 5 node logos, signatures |
| Onboarding | The one-screen explanation at the first wall; the first stamp |
| Site plan | Where each of the nine panels goes, against section 4 |
| Permissions | Comune, wall owners, amplified sound, an unattended street auction |
| Build order | Which nodes are piloted first, and in which order the nine are built |
