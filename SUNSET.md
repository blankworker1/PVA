# SUNSET — PVA no. 2

SUNSET is the second work of **PVA (Photovoltaic Art)**, after [SUNDIAL](README.md). Where SUNDIAL is about time, SUNSET is about one moment in it: **every day's business closes at sunset.** (Its working title was GO TO BED.)

SUNSET is **nine recycled solar panels** on the walls of a town, forming a small offline network with its own currency. People earn **stamps** by walking messages between walls and by skill, and spend them at an auction, a mint and a wall of mechanical pixels. Every panel runs on its own sun, on the same carrier board as SUNDIAL, and everything that happens is unattended, anonymous and over by sunset.

> Status: draft 1, 22 Oct 2026. The five interactive nodes are specified in their own documents; the wall nodes in [wall-node.md](wall-node.md); the stamp format is outlined there and still to be specified in full. Nothing is built.

---

## 1. Nine panels

**A PVA work is always nine panels.** SUNSET has four wall nodes and five interactive nodes.

| Panel | Kind | What it does | Specification |
| --- | --- | --- | --- |
| Wall 1–4 | **Wall node** | Message walls: visitors post and read messages; couriers (visitors) carry messages between walls and earn stamps for it. The network's news, and the main source of new stamps | [wall-node.md](wall-node.md) |
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
| Wall nodes | **walk** | earn, and spend | Stamps for carrying messages between walls; **shouts are paid for**, a sink |
| Arm game | **skill** | earn | Stamps for a peg dropped cleanly; harder holes pay more |
| Street auction | **bid** | transfer | Buyer's stamps go to the seller; the listing fee is a sink |
| Print node | **print** | convert, and spend | Digital ⇄ paper; the printing fee and the souvenir are sinks |
| Flip-dot wall | **mark** | spend, **paper only** | Each flip burns a paper stamp |
| The SUNSET set | **sun** | (none) | No stamps: the sun pays for the music |

### 2.2 Stamps in, stamps out

- **In:** walking (walls) and skill (arm game). Both are limited by the sun: the walls are awake only in daylight, and the arm game only plays while its battery allows. **Issuance is energy-backed.**
- **Out (sinks):** paid shouts, the auction's listing fee and burned relists, the print node's fee and souvenirs, and every flip of a dot.
- **Moving:** auctions move stamps between people; paper moves them hand to hand, with no phone.
- **No cash value, ever.** Stamps cannot be bought or redeemed for money. Their value is only in what they can be used for in the town.

### 2.3 Paper money

The print node turns digital stamps into **paper stamps**: an artwork stamp (a gift, no value) and a **redeem sticker** (the value). Paper can pass from hand to hand like cash, so **people without a phone can take part:** someone hands them a sticker, and they spend it at the flip-dot wall, which accepts only paper. The print node and the flip-dot wall share one spent list over ESP-NOW, so a copied sticker can never be spent twice.

---

### 2.4 Stamps in the town: a possible outcome, not a feature

Paper stamps pass from hand to hand, so nothing stops people trading with them outside the nodes. A café owner might shout that today a coffee costs a few stamps, cash only, to bring people in.

- **SUNSET neither invites nor prevents it.** It does not recruit shops, set prices or promise any value. Stamps are never sold or redeemed for money by SUNSET.
- **What a trader can do with stamps taken:** spend paper at the flip-dot wall, hand it on, or redeem it at the print node and bid, list a lot, buy souvenirs or pay for shouts. The auction is the only place stamps buy *things* from other people.
- **What it would mean:** stamps would find a price in the real town, and walking and skill would be worth more. The sun-limited issuance would become the currency's real monetary policy.
- **The trader's risks are the trader's:** a sticker can be checked as **genuine** with the print node's public key, but only the print node and the flip-dot wall know whether it is **unspent**, so prompt redemption is the protection. Any sale for stamps is the trader's own business, receipts and tax included.

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

The positions are chosen on site, framed for the best possible outcomes. The logic:

| Panel | Where | Why |
| --- | --- | --- |
| **Print node + flip-dot wall: the gateway** | **As a pair (a hard requirement),** within ESP-NOW range of each other, at the **entrance** to the route, **near businesses that already have footfall** | The way in to SUNSET (4.1). They share one spent list; the mint, and the wall where its money is spent |
| **Walls 1–4** | Spread to the edges of the route | Distance is what makes proof of walk mean something: the walls set the shape of the walk |
| **Street auction** | Where people already pass | Its catalogue is the street itself |
| **The SUNSET set** | The town's **sunset spot,** a west-facing place where people already gather to watch the sun go down | The set starts at sunset; choose neighbours who can live with an hour of music |
| **Arm game** | In shade | Servos and electronics in a perspex case |

The walls and the interactive nodes interleave along the route, so a walk between walls passes the places to spend.

### 4.1 The gateway

The print node and the flip-dot wall together are **the entrance to the installation.**

- **The first thing people see:** the flip-dot picture, made by the town a paid dot at a time, and the sticker wall beside it. It shows at a glance that something is happening, and that people take part.
- **Where the rules are explained** (5), and where the route and the map start.
- **Where paper meets the town.** Placed near bars, cafés and shops that already have footfall, the gateway draws their customers in, and gives those businesses the infrastructure to take part: paper stamps redeemed or checked at the print node from their own counter (4.2), and paid shouts to advertise on every wall.

### 4.2 Hosts

Every panel needs a wall, and the owner's consent. Hosting is a fair exchange: wall space and consent for the node's presence. **No money and no endorsement;** PVA runs every node.

| Host of | What the host gets |
| --- | --- |
| **The gateway** (print node, flip-dot wall) | The installation's entrance at the door: footfall, and, within the print node's Wi-Fi range (roughly 30–50 m outdoors, less through walls), **live settlement** of paper stamps from the counter: redeem a sticker the moment it is handed over, or check its status by serial (interactive-print.md 3.6) |
| **A wall node** | Couriers arriving all day; the town's shouts on the wall; spends known "as far as this wall has heard" |
| **Any node** | A place on the route, and the shouts that point people to it |

Hosts are chosen because their wall fits the layout, not the other way round: walls stay spread, and the gateway pair stays together.

---

## 5. The first five minutes

A visitor meets five kinds of node in one day. Each needs one obvious first step. **The gateway explains the whole economy on one screen** when people arrive, and every wall repeats it for those who start elsewhere:

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
| Messages on the walls vanish within 7 days; nothing attributable is kept | wall-node.md 2.3 |

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
| **Stamp format** | The bearer-stamp design shared by all nodes: the public unspent list, the 5 × 5 node logos, signatures |
| Onboarding | The one-screen explanation at the first wall; the first stamp |
| Site plan | Where each of the nine panels goes, against section 4 |
| Permissions | Comune, wall owners, amplified sound, an unattended street auction |
| Build order | Which nodes are piloted first, and in which order the nine are built |
| Verify page | A small offline page on the SUNSET website, with the print node's public key, so anyone can check a paper stamp is genuine on their own phone (2.4) |
