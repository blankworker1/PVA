# The arm game — a dexterity interactive node on carrier v1

A SUNSET interactive node with a robot arm in a transparent enclosure, played from visitors' phones. The game is **pegs in holes**: drop a peg cleanly into a hole and the machine pays a stamp. It is SUNSET's first **earning node by skill**, beside the walls, which pay for walking.

It runs on carrier v1 on the battery tier: the panel feeds a Victron SmartSolar MPPT 75/15 and a 12 V LiFePO₄ battery, with JP1 off and the sun sensor compiled out. The tier is specified in [interactive-auction.md](interactive-auction.md), sections 1 and 2; this document covers only what is different.

> Status: draft 1, 22 Oct 2026. Brings together the decisions made so far; nothing built. **Nothing here changes the carrier board.**

---

## 1. The idea

- **An arcade claw, turned into a test of skill.** A robot arm behind perspex, steered from the visitor's phone. Nothing is won and nothing leaves the box; the prize is a stamp.
- **Proof of skill.** SUNSET pays stamps for real acts: walking a message between walls is *proof of walk*, getting a peg into a hole is *proof of skill*. Both earn the same stamp.
- **The machine is the witness.** A sensor under each hole confirms the drop, so the stamp is issued by the hardware, not claimed by the player.
- **The sun sets the issuance.** Every move costs energy. The node can only pay out as many stamps as its battery allows: a dull week mints fewer stamps.
- **Daylight only,** like all SUNSET business: play runs from sunrise to sunset.

### Where it sits in SUNSET

| Node | Proof | Direction |
| --- | --- | --- |
| Wall (message nodes) | walk | earn |
| **Arm game** | **skill** | **earn** |
| Street auction ([interactive-auction.md](interactive-auction.md)) | bid | transfer buyer → seller; listing fee is a sink |
| Spending nodes (e.g. a flip-dot pixel wall, to be specified) | mark | spend |

**One stamp type** everywhere. Each stamp carries the 5 × 5 logo of the node that issued it, so its origin is visible, but every stamp spends the same.

---

## 2. Hardware

### 2.1 The arm: Joy-IT Grab-it (Robot02)

Chosen over the Arduino TinkerKit Braccio, which reads as a school or hobby kit rather than an object; the Grab-it's black anodised aluminium reads as an artwork behind perspex.

| | Joy-IT Grab-it (Robot02) |
| --- | --- |
| Frame | Black anodised aluminium profiles, ball-bearing joints and turntable |
| Servos | 6 × 21.5 kg·cm at 7.4 V, metal gears, standard PWM; 5–7.4 V, up to about 2 A each |
| Reach / height | About 30 cm from the turntable centre; up to 42 cm tall |
| Weight | 1540 g |
| Controller | None in the base kit; driven here by the carrier (2.3) |
| Availability | Current product (about €160 for the arm alone, about €250 bundled with a controller) |

- **Difficulty is a design choice, not a defect.** The arm is stiff and precise, so the game is made hard by the peg tolerances and the controls (3.2), not by jitter.
- **Its strength cuts both ways.** It can crack a peg board or push on the perspex if a move goes wrong. The firmware sets **soft angle limits and speed limits** on every joint, so the arm cannot reach the walls.

### 2.2 The board: pegs, holes and the gravity loop

Nothing needs resetting:

- The holes are **through-holes.** A peg dropped in falls through the board onto a **sloped ramp** below and rolls back to a **hopper**, where the arm picks it up again. The pegs circulate like a marble run, and the board is always empty and ready.
- **A sensor under each hole** (IR break-beam or a small microswitch flap) gives the ESP32 a trustworthy "success" for that hole.
- **Holes from loose to tight,** or round, square and triangular pegs, so some drops are easy and some very hard.
- **Jams:** if a peg sticks on the ramp or lands outside the hopper, the arm runs a **self-clearing routine** after sunset, when play has closed. It can double as a small evening performance.

### 2.3 Driving the arm from the carrier

Six servos and the hole sensors need more pins than J9 has, so the servos go on a **PCA9685-class 16-channel PWM board** on the carrier's I2C header (J13). J9 is left for the sensors.

| Use | GPIO / bus | Header | Notes |
| --- | --- | --- | --- |
| Servo PWM, 6 channels (16 available) | I2C SDA 21 / SCL 22 | J13 | PCA9685 board, shared I2C with the DS3231 (different address) |
| Servo power enable | 26 | J9 | MOSFET or relay on the servo supply; off at boot (pull-down), off outside play |
| Hole sensors 1–5 | 32, 33, 36, 13, 14 | J9 | 36 is input only and needs an external pull-up; GPIO 14 toggles at boot, harmless on an input |
| Hopper / jam sensor (optional) | one of the pins above | J9 | Or an I2C port expander (MCP23017 class) on J13 if more inputs are needed; the PCA9685 is outputs only |
| Switched 5 V | 27 | via R19 to U4 | Unchanged; free for a light or fan |
| VE.Direct | 16 RX, 17 TX | J10 | As on every interactive node |
| Enclosure temperature probe | 4 | J4 / J5 | Heat check (3.5) |

**Servo supply:** a 12 V → 6–7.4 V buck converter rated for about 10 A peaks, from the battery through its own fuse, never through the carrier. Six servos at up to 2 A each could in theory draw over 12 A, but in normal moves only one or two joints work hard at a time.

### 2.4 The enclosure

- **Transparent perspex box,** like an arcade claw cabinet: the arm, the peg board, the ramp and the hopper all visible.
- **Sealed:** nothing for a hand to reach. Thick enough that the arm cannot crack it at its soft limits.
- **Heat:** servos and electronics in a perspex box in the Sardinian sun. Shade or a north-facing site, ventilation, and the temperature probe (3.5).

### 2.5 Power

| Load | Draw | Notes |
| --- | --- | --- |
| ESP32, Wi-Fi on, sunrise to sunset | about 0.5 W | about 6 Wh a day |
| Arm, during a turn | roughly 10–40 W, peaks higher | depends on moves; idle between turns with servo power off |
| Arm, per day | set by play | each turn costs energy; this is what the sun gate meters (3.3) |

A 12 V 20–40 Ah LiFePO₄ pack (about 250–500 Wh) covers a busy day with reserve. The real cost per turn is measured in the pilot.

---

## 3. The rules

### 3.1 A turn

1. **Join the node's Wi-Fi;** the game page opens. If someone is playing, join the queue.
2. **Start a turn.** The phone makes its own secret and sends only its hash (as in interactive-auction.md 3.5), so the stamp it earns can't be copied off the open network.
3. **Steer the arm:** pick a peg from the hopper, carry it to a hole, release.
4. **A sensor confirms the drop:** the node issues the stamp to the player's passport page, signed by the node, revealed only to the phone that holds the secret.
5. **The turn ends** on the timer, or when the player ends it. Next in the queue.

One player at a time; the access point serves up to 10 phones, so the queue is short by design.

### 3.2 Controls and difficulty

- **Coarse moves** (rotate, reach, raise, lower) and a **fine-adjust mode** for the final placement, then **release**.
- **A turn timer,** so the queue keeps moving.
- **Difficulty pays in quantity:** an easy hole earns 1 stamp, the tightest earns 3 (values set in the pilot). One stamp type, varied earning.

### 3.3 The sun gate

- **Each turn costs energy,** so turns are offered only when the battery's charge state allows (from the Victron over VE.Direct). The page shows a charge bar filling: the sun is the coin slot.
- **Issuance is energy-backed.** The node can only mint as many stamps as its battery can pay for in moves. A cloudy week means fewer turns and fewer stamps in circulation.
- **Anti-farming,** with no identities: the sun gate, the turn timer and the queue together cap how many stamps any one person can take in a day. A daily cap per node can be added if the pilot shows it is needed.

### 3.4 Daylight only

Play runs from sunrise to sunset, like all SUNSET business. At sunset the Wi-Fi closes, servo power goes off, and the self-clearing routine (2.2) runs if needed.

### 3.5 Heat and safety

- **Servo power off** whenever no turn is running.
- **No play above a set enclosure temperature,** read from the probe; the page says why.
- **Soft limits and speed limits** on every joint (2.1).

---

## 4. Firmware: the interactive build, arm role

Same interactive build as the other SUNSET nodes (interactive-auction.md 4), with the node role set to **arm game**:

- servo control through the PCA9685 over I2C, with per-joint soft limits and speed limits;
- the turn queue, turn timer and controls page;
- hole sensors, and stamp issue on a confirmed drop (commit-and-reveal, as for auction tokens);
- the sun gate on the Victron's charge state;
- the self-clearing routine after sunset;
- every stamp issued written to flash before it is shown, so a reboot can neither lose nor repeat one.

---

## 5. Open questions

| Question | Notes |
| --- | --- |
| Number of holes and tolerances | How many holes, which shapes, how tight; how many stamps each pays |
| Control scheme | Joint-by-joint buttons, or simpler moves ("left, right, down, grip"); tested with first-time players |
| Daily stamp cap | Only if the sun gate and timer are not enough |
| Peg and board materials | Durable, quiet, and kind to the arm's gripper |
| Jam handling | Whether a hopper sensor is needed, or the nightly clearing routine is enough |
| Site | Shade and ventilation for servos in summer |

## 6. Pilot tasks

| Task | What to settle |
| --- | --- |
| Energy per turn | Measured, to set the sun gate's thresholds |
| Difficulty | Hole tolerances and stamp values that make the game hard but winnable |
| Soft limits | Joint angles and speeds that keep the arm off the perspex and the board |
| Sensor reliability | No missed drops, no false stamps (a peg brushing the sensor without dropping through) |
| Heat | Temperature inside the enclosure on a summer afternoon, servos idle and working |
| Gravity loop | Pegs return to the hopper every time; how often the clearing routine is needed |
