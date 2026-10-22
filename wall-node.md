# Wall nodes — the message walls of SUNSET

The four **wall nodes** are the backbone of [SUNSET](SUNSET.md). Each is a recycled panel on a wall, serving its own Wi-Fi with no internet. On it, anyone can read and leave short messages. Visitors' phones carry messages from wall to wall as they walk, and the first to deliver new messages to a wall earns a **stamp**: *proof of walk*. The walls are where most visitors meet SUNSET, where its news travels, and where most new stamps come from.

A wall node is a **wall-tier** panel: the panel straight into the carrier board, no battery, awake from dawn to dusk, the same hardware as a SUNDIAL panel ([SUNDIAL.md](SUNDIAL.md), [hardware/CARRIER.md](hardware/CARRIER.md)).

> Status: draft 2, 22 Oct 2026 (shouts are paid for). Brings together the decisions made so far; nothing built. The shared stamp format is outlined here (5) and will get its own specification.

---

## 1. The visitor's experience

### 1.1 Finding a wall

A panel on a wall, with a small plate: the panel's number and its 5 × 5 logo. The visitor joins the panel's Wi-Fi (the network name is on the plate) and the wall's page opens.

### 1.2 The first screen: the dial tone

Every wall opens on its **dial tone:** a simple picture that says the network is alive.

- **Who is here:** how many phones are connected to this wall right now.
- **The network:** the other nodes, each with the **time of its last update** from this wall's point of view. A wall that hasn't heard from another for a long time shows it, so the network's gaps are visible, and so is where to walk.
- **The three shouts:** the town's current news (2.2).
- **Service notices,** on their own line: the installation asking for upkeep, in public (SUNSET.md 7.1).
- **The rules on one screen** (SUNSET.md 5): earn by walking messages or by skill; spend at the auction, the print node or the flip-dot wall; paper works without a phone; everything closes at sunset.

### 1.3 Reading and writing

- **Read** the wall's messages: whispers left here, and shouts from around the town.
- **Write** a short message. No account, no login. A name is only what someone types into the message.
- **Reply** to a message with one tap.
- **Shout:** pay to promote any whisper to a shout (2.2).

### 1.4 Carrying, without trying

The visitor's phone is a **courier by default**. On connecting to a wall, the page quietly picks up that wall's latest messages; on connecting to the next wall, it delivers them. A **ticker** on the page shows it happening: *picked up 14 messages from Wall 2… delivered to Wall 3.* The visitor only has to walk.

### 1.5 The first stamp

If the visitor is **the first to deliver** a wall's new messages to another wall, that wall pays a stamp. A newcomer's first stamp is a few minutes' walk from their first wall. It lands in their **passport page** (5.3), stamped with the 5 × 5 logo of the wall that paid it.

### 1.6 What it feels like

A town where the walls talk to each other only through the people walking between them. Messages travel at walking pace; the news is hours old by the time it crosses town, and that is the point. The visitors are the network: **the participants are the internet.**

---

## 2. Messages

### 2.1 Whisper

- A message left at one wall, **readable at that wall.**
- Short, with a fixed length limit (set in the pilot).
- Time-stamped by the panel's own clock, never by the phone.

### 2.2 Shout

- A message **carried to the whole town:** couriers take shouts from wall to wall, so every wall shows them as they arrive.
- **The dashboard shows three shouts** at a time: the town's current headlines.
- **Shouts are paid for.** Anyone can promote any whisper to a shout, their own or someone else's, by spending stamps (the price is set in the pilot). A shout is **community advertising:** whoever wants the town to hear something pays for it, whether it's a party, a lost dog or a café selling coffee for stamps. The stamps spent leave circulation: a sink.
- **Node notices are free.** Interactive nodes shout too: the auction's "Locker A uncollected", the SUNSET set's "the set plays tonight". They enter the network the same way and couriers carry them.

### 2.3 Rules

| Rule | Detail |
| --- | --- |
| **Open posting** | Anyone in range can write; constrained length |
| **No identity** | Anonymous, or a name typed into the message. "Don't trust anything that is written" |
| **No moderation** | Nothing is checked or removed by hand |
| **Seven days** | Every message is gone within 7 days. This is a feature, not a bug |
| **Nothing attributable** | No user data is held; no phone identifiers are stored with messages |
| **Text only** | Shown as text, never as HTML, on every page (as SUNDIAL's visitors' book, SUNDIAL.md 4.2) |

---

## 3. Couriers and blocks

### 3.1 Blocks

Each node keeps a **block:** everything it currently holds for the network (messages and shouts, and the stamp records that other nodes need: 5.2). A block has a version, so a node can tell new information from old.

### 3.2 The courier's journey

1. **Pick-up.** A phone connected to Wall A receives A's latest block (and anything A holds for other walls).
2. **Carry.** The phone keeps it in the browser while the visitor walks.
3. **Delivery.** At Wall B, the phone hands it over. B merges what is new and gives the phone its own block in return.

Every SUNSET node, wall or interactive, takes part: interactive nodes post their shouts into a block and receive the town's news and stamp records the same way.

### 3.3 Proof of walk

- **The first delivery** of new information from one node to another earns the courier a stamp from the receiving node.
- **Valid between any two nodes:** there is no fixed route and no centre. Two walls are already a network.
- **Permissionless:** anyone walking with a phone can be a courier; no sign-up.
- **Bounded by the sun:** wall nodes are awake only in daylight, so the number of deliveries, and of stamps paid, follows the length of the day.

### 3.4 Why it works on paper and fails gently

- **No backhaul:** nothing reaches the internet. If no one walks, the walls drift apart, and the dial tone shows it.
- **Slow by design:** news is as fast as feet.
- **Lost phones lose nothing:** a courier's block is a copy; every node keeps its own.

---

## 4. Hardware and power

| | Wall node |
| --- | --- |
| Board | PVA carrier v1, wall build, unchanged |
| Power | The panel straight into the carrier; no battery |
| Awake | Dawn to dusk; off at night |
| Wi-Fi | Open access point, up to 10 phones at once, plain HTTP |
| Clock | DS3231 with coin cell: every message and stamp is time-stamped by the panel |
| Storage | LittleFS for messages (7 days), blocks and the stamp records |
| Sun sensor | Available, as on SUNDIAL panels; not needed for the wall's role |

A wall node draws well under 1 W. It needs nothing that a SUNDIAL panel doesn't already have.

---

## 5. Stamps: the shared format (outline)

To be specified in full separately; every SUNSET node depends on it.

### 5.1 What a stamp is

- A **bearer receipt:** whoever holds it can spend it. No accounts, no names.
- Issued by a node, carrying that node's **5 × 5 logo,** a serial and the panel's time.
- **Node logos:** each node's logo is unique within the network, and **never the same as the Photovoltaic Art logo.** The PVA mark belongs to the project as a whole; it never appears as a node's logo or on a stamp as its issuer.
- **No cash value.** Stamps have only uses, never redemption for money.

### 5.2 The public unspent list

- Security is a **public unspent list,** not a private key held by the visitor: each node records which stamps it has issued and which have been spent.
- **Spends travel in blocks:** couriers carry each node's record of spent stamps to the others, so the town's list converges at walking speed.
- **Where a double spend would matter,** nodes don't wait for couriers: stamps are **spent into** the node that receives them (interactive-auction.md 3.4), and the print node and flip-dot wall share their list in real time over ESP-NOW (interactive-flipdot.md 2.1).

### 5.3 The passport page

- A page on the visitor's phone, a grid of boxes **filled by stamps** as they are earned, each showing the logo of the node that paid it.
- **Saved as images,** so the passport survives with nothing installed, plus a **shareable version** to show or send.
- Tokens from the auction and paper-stamp receipts are kept here too.

---

## 6. Open questions

| Question | Notes |
| --- | --- |
| **Phone storage** | Couriers carry blocks in the browser. The captive-portal pop-up browser on some phones keeps no storage between networks; visitors may need to open the page in their normal browser. Test on iPhone and Android first |
| Message length | The limit for whispers and shouts |
| Shout price | How many stamps a shout costs, and whether the price rises when many shouts are waiting |
| Stamps per delivery | One per first delivery, or scaled by how much new information is carried |
| Farming | Two people shuttling between two walls: whether "new information" is enough of a limit, or a per-courier daily cap is needed (without identities) |
| Replies | How a reply shows: threaded under the message, or as a new whisper quoting it |
| Wall plate | Number, logo, network name, and a QR to join |

## 7. Pilot tasks

| Task | What to settle |
| --- | --- |
| Courier storage | Blocks survive from one wall to the next on common phones and browsers |
| Block size | How large a block grows over 7 days of messages, and how long a hand-over takes |
| Dial tone | Readable at a glance by a first-time visitor |
| First stamp | A newcomer earns one within a short walk, without instructions |
| Seven-day expiry | Messages and records drop off cleanly, on every node |
