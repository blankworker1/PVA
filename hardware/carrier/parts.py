# PVA carrier board v1 — parts and nets, transcribed from hardware/CARRIER.md
# Each part: ref, (library, symbol), value, footprint, {pin number: net}, notes
# Pins not listed are no-connect. Nets in CAPS are signals; +5V, +3V3, GND are rails.

R0603 = "Resistor_SMD:R_0603_1608Metric"
R0805 = "Resistor_SMD:R_0805_2012Metric"
C0603 = "Capacitor_SMD:C_0603_1608Metric"
C0805 = "Capacitor_SMD:C_0805_2012Metric"
T2_508 = "TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-2-5.08_1x02_P5.08mm_Horizontal"
T3_35 = "TerminalBlock_Phoenix:TerminalBlock_Phoenix_PT-1,5-3-3.5-H_1x03_P3.50mm_Horizontal"
T4_35 = "TerminalBlock_Phoenix:TerminalBlock_Phoenix_PT-1,5-4-3.5-H_1x04_P3.50mm_Horizontal"
T2_HC = "TerminalBlock_MetzConnect:TerminalBlock_MetzConnect_Type067_RT01902HDWC_1x02_P10.00mm_Horizontal"
TP = "TestPoint:TestPoint_Loop_D2.50mm_Drill1.0mm"

def R(ref, val, fp, a, b, note=""):  return (ref, ("Device", "R"), val, fp, {"1": a, "2": b}, note)
def C(ref, val, fp, a, b, note=""):  return (ref, ("Device", "C"), val, fp, {"1": a, "2": b}, note)

SECTIONS = []

# 1. Panel input and sun sensor
SECTIONS.append(("1. Panel input and sun sensor", [
    ("J1", ("Connector", "Screw_Terminal_01x02"), "PANEL+ / PANEL- (>=15 A, 4-6 mm2)", T2_HC,
        {"1": "PANEL+", "2": "GND"}, "Board edge; GND here is PANEL-"),
    ("D0", ("Device", "D_Schottky_Dual_CommonCathode_AKA_Parallel"), ">=100 V >=15 A dual Schottky (e.g. 20 A 100 V)",
        "Package_TO_SOT_SMD:TO-263-2", {"1": "PANEL+", "2": "PV+", "3": "PANEL+"},
        "Input protection; cooling area; carries AUX current too"),
    ("Q1", ("Device", "Q_NMOS_GDS"), "N-MOSFET >=60 V (>=100 V if D6 fitted) >=20 A Rds(on)<=20 mOhm @4.5 V", "Package_TO_SOT_SMD:TO-252-2",
        {"1": "GATE", "2": "PV+", "3": "SHUNT_TOP"}, "Sun sensor: shorts the panel ~1 ms every 10 s"),
    R("RSH1", "5m 1% 2512 >=2 W", "Resistor_SMD:R_2512_6332Metric", "SHUNT_TOP", "GND",
        "Spec ref R_SH. Kelvin connections to U2; star ground at the GND end"),
    R("RSH2", "DNP (option: 2x 10m)", "Resistor_SMD:R_2512_6332Metric", "SHUNT_TOP", "GND", "Spec ref R_SH2. Footprint only"),
    ("U2", ("Amplifier_Current", "INA180A3"), "INA180A3 (gain 100)", "Package_TO_SOT_SMD:SOT-23-5",
        {"1": "ISENSE_RAW", "2": "GND", "3": "SHUNT_TOP", "4": "GND", "5": "+3V3"},
        "IN+ and IN- by Kelvin traces from the inner ends of RSH1's pads"),
    C("C6", "100n", C0603, "+3V3", "GND", "U2 decoupling"),
    R("R6", "1k", R0603, "ISENSE_RAW", "ISENSE"),
    C("C7", "10n", C0603, "ISENSE", "GND"),
    ("U3", ("Driver_FET", "MCP1416"), "MCP1416 (or TC4427A class)", "Package_TO_SOT_SMD:SOT-23-5",
        {"2": "+5V", "3": "GATE_IN", "4": "GND", "5": "GATE_DRV"}, "Non-inverting, 5 V gate drive"),
    C("C11", "1u", C0603, "+5V", "GND", "ADDED, not in spec v1: U3 supply decoupling (datasheet requirement)"),
    R("R4", "10R", R0603, "GATE_DRV", "GATE"),
    R("R5", "10k", R0603, "GATE_IN", "GND", "Q1 stays off while the ESP32 boots"),
    R("R21", "100k", R0603, "GATE", "SHUNT_TOP", "ADDED, review 2: Q1 gate-source pull-down; holds Q1 off while U3 is unpowered at dawn"),
    ("D6", ("Device", "D_Zener"), "DNP: SMCJ58A TVS (fit after bench test if needed)", "Diode_SMD:D_SMC", {"1": "PV+", "2": "GND"},
        "ADDED, review 2: footprint only. If fitted, Q1 must be >= 100 V (clamp ~90 V)"),
    ("JP1", ("Jumper", "Jumper_2_Open"), "Jumper: remove = sun sensor off", "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical",
        {"1": "GPIO25_GATE", "2": "GATE_IN"}, ""),
]))

# 2. Board side of the panel
SECTIONS.append(("2. Fuse, diode, divider", [
    ("F1", ("Device", "Fuse"), "2 A slow-blow", "Fuse:Fuse_1812_4532Metric", {"1": "PV+", "2": "PV_F"}, "After the Q1 node"),
    ("D1", ("Device", "D"), "S3M (1000 V 3 A)", "Diode_SMD:D_SMC", {"1": "BUCK_IN+", "2": "PV_F"}, "Reverse polarity; blocks Q1 pulses"),
    ("J2", ("Connector", "Screw_Terminal_01x02"), "BUCK IN + / -", T2_508, {"1": "BUCK_IN+", "2": "GND"}, "To ANGEEK buck input"),
    R("R1", "100k 1%", R0805, "PV_F", "VDIV"),
    R("R2", "4k7 1%", R0603, "VDIV", "GND", "Was 5k6; changed after review (48 V -> 2.15 V)"),
    C("C5", "100n", C0603, "VDIV", "GND"),
]))

# 3. 5 V rail
SECTIONS.append(("3. 5 V rail", [
    ("J3", ("Connector", "Screw_Terminal_01x02"), "BUCK OUT + / - (set 5.0 V)", T2_508, {"1": "+5V", "2": "GND"}, ""),
    ("J6", ("Connector", "Screw_Terminal_01x02"), "Supercap 2.7 V 10 F (upper)", T2_508, {"1": "+5V", "2": "MID"}, "Silkscreen - side (stripe)"),
    ("J7", ("Connector", "Screw_Terminal_01x02"), "Supercap 2.7 V 10 F (lower)", T2_508, {"1": "MID", "2": "GND"}, "Silkscreen - side (stripe)"),
    R("R7", "10k", R0805, "+5V", "MID", "Balancing"),
    R("R8", "10k", R0805, "MID", "GND", "Balancing"),
    ("D2", ("Device", "D_Zener"), "SMAJ5.0A (TVS, unidirectional)", "Diode_SMD:D_SMA", {"1": "+5V", "2": "GND"}, ""),
    ("C3", ("Device", "C_Polarized"), "470u 10 V low ESR", "Capacitor_SMD:CP_Elec_8x10.5", {"1": "+5V", "2": "GND"}, "Close to ESP32 VIN"),
    C("C4", "100n", C0603, "+5V", "GND"),
    R("R9", "10k", R0603, "+5V", "LED_A"),
    ("LED1", ("Device", "LED"), "Green, ~0.3 mA", "LED_SMD:LED_0603_1608Metric", {"1": "GND", "2": "LED_A"}, "5 V present; dim on purpose"),
]))

# 4. ESP32 socket — ELEGOO 30-pin (DOIT DevKit V1 layout). PROVISIONAL: confirm pin order on a delivered board.
LEFT = ["EN", "36", "39", "34", "35", "32", "33", "25", "26", "27", "14", "12", "13", "GND", "VIN"]
RIGHT = ["23", "22", "1", "3", "21", "19", "18", "5", "17", "16", "4", "2", "15", "GND", "3V3"]
GPIO_NET = {"VIN": "+5V", "GND": "GND", "3V3": "+3V3",
            "4": "DQ", "21": "SDA", "22": "SCL", "25": "GPIO25_GATE", "34": "VDIV", "35": "ISENSE",
            "5": "SD_CS", "18": "SD_SCK", "19": "SD_MISO", "23": "SD_MOSI", "39": "SD_CD",
            "26": "GPIO26", "27": "GPIO27", "32": "GPIO32", "33": "GPIO33", "36": "GPIO36", "13": "GPIO13", "14": "GPIO14",
            "16": "UART_RX", "17": "UART_TX"}
def header(pins): return {str(i + 1): GPIO_NET[p] for i, p in enumerate(pins) if p in GPIO_NET}
SECTIONS.append(("4. ESP32 socket (ELEGOO 30-pin, plugged in; antenna keep-out)", [
    ("J14", ("Connector_Generic", "Conn_01x15"), "ESP32 left row: EN,36,39,34,35,32,33,25,26,27,14,12,13,GND,VIN",
        "Connector_PinSocket_2.54mm:PinSocket_1x15_P2.54mm_Vertical", header(LEFT), "Row spacing 25.4 mm, provisional"),
    ("J15", ("Connector_Generic", "Conn_01x15"), "ESP32 right row: 23,22,1,3,21,19,18,5,17,16,4,2,15,GND,3V3",
        "Connector_PinSocket_2.54mm:PinSocket_1x15_P2.54mm_Vertical", header(RIGHT), "EN, 1, 3, 2, 12, 15 not brought out"),
]))

# 5. Clock
SECTIONS.append(("5. Clock", [
    ("U1", ("Timer_RTC", "DS3231M"), "DS3231SN (or RV-3028-C7, firmware change)", "Package_SO:SOIC-16W_7.5x10.3mm_P1.27mm",
        dict({"1": "RTC_32K", "2": "+3V3", "3": "RTC_INT", "13": "GND", "14": "VBAT", "15": "SDA", "16": "SCL"},
             **{str(n): "GND" for n in range(5, 13)}),
        "Symbol DS3231M has the same pinout as DS3231SN (pins 5-12 to GND); RST not connected"),
    ("BT1", ("Device", "Battery_Cell"), "CR2032 holder (no charging)", "Battery:BatteryHolder_Keystone_3034_1x20mm",
        {"1": "VBAT", "2": "GND"}, ""),
    C("C10", "100n", C0603, "+3V3", "GND", "U1 decoupling"),
    R("R10", "4k7", R0603, "SDA", "+3V3"),
    R("R11", "4k7", R0603, "SCL", "+3V3"),
]))

# 6. Temperature probes
SECTIONS.append(("6. Temperature probes", [
    ("J4", ("Connector", "Screw_Terminal_01x03"), "DS18B20: 3V3 / DATA / GND", T3_35, {"1": "+3V3", "2": "DQ_T", "3": "GND"}, "red / yellow / black"),
    ("J5", ("Connector", "Screw_Terminal_01x03"), "Optional 2nd probe", T3_35, {"1": "+3V3", "2": "DQ_T", "3": "GND"}, "In parallel with J4"),
    R("R12", "4k7", R0603, "DQ_T", "+3V3"),
    R("R20", "DNP", R0603, "DQ_T", "+3V3", "Spec ref R12b. Footprint only: stronger pull-up for long cable"),
    R("R13", "100R", R0603, "DQ_T", "DQ"),
    ("D3", ("Device", "D_TVS"), "ESD 3.3 V (e.g. PESD3V3L1BA)", "Diode_SMD:D_SOD-323", {"1": "DQ_T", "2": "GND"}, "At the terminal"),
]))

# 7. microSD
SECTIONS.append(("7. microSD (future-proofing)", [
    ("J8", ("Connector", "Micro_SD_Card_Det_Hirose_DM3AT"), "microSD push-push with detect (Hirose DM3AT)",
        "Connector_Card:microSD_HC_Hirose_DM3AT-SF-PEJM5",
        {"2": "SD_CS", "3": "SD_MOSI", "4": "+3V3", "5": "SD_SCK", "6": "GND", "7": "SD_MISO",
         "10": "SD_CD", "9": "GND", "11": "GND"}, "At a board edge; DAT1, DAT2 not used in SPI mode"),
    R("R14", "10k", R0603, "SD_CS", "+3V3", "Also keeps GPIO 5 high at boot"),
    R("R15", "10k", R0603, "SD_MOSI", "+3V3"),
    R("R16", "10k", R0603, "SD_MISO", "+3V3"),
    R("R17", "10k", R0603, "SD_CD", "+3V3"),
    C("C8", "10u", C0805, "+3V3", "GND"),
    C("C9", "100n", C0603, "+3V3", "GND"),
]))

# 8. Expansion and test
tps = [("TP1", "PV+"), ("TP2", "BUCK_IN+"), ("TP3", "+5V"), ("TP4", "MID"), ("TP5", "+3V3"), ("TP6", "GND"),
       ("TP7", "VDIV"), ("TP8", "ISENSE"), ("TP9", "GATE"), ("TP10", "RTC_INT"), ("TP11", "RTC_32K")]
SECTIONS.append(("8. Expansion headers and test points", [
    ("J13", ("Connector_Generic", "Conn_01x04"), "I2C: 3V3 GND SDA SCL", "Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical",
        {"1": "+3V3_EXT", "2": "GND", "3": "SDA", "4": "SCL"}, ""),
    ("J9", ("Connector_Generic", "Conn_01x09"), "Spare: 3V3 GND 32 33 36 26 27 13 14", "Connector_PinHeader_2.54mm:PinHeader_1x09_P2.54mm_Vertical",
        {"1": "+3V3_EXT", "2": "GND", "3": "GPIO32", "4": "GPIO33", "5": "GPIO36", "6": "GPIO26", "7": "GPIO27", "8": "GPIO13", "9": "GPIO14"},
        "Silkscreen: 32/33/36 analog, 36 input only"),
    ("J10", ("Connector_Generic", "Conn_01x04"), "UART: 3V3 GND RX2(16) TX2(17)", "Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical",
        {"1": "+3V3_EXT", "2": "GND", "3": "UART_RX", "4": "UART_TX"}, ""),
] + [(t, ("Connector", "TestPoint"), n, TP, {"1": n}, "") for t, n in tps]))

# 9. Power take-off
SECTIONS.append(("9. Power take-off for add-ons", [
    ("J11", ("Connector", "Screw_Terminal_01x04"), "5V / 5V SW / 3V3 / GND", T4_35,
        {"1": "+5V_EXT", "2": "5V_SW", "3": "+3V3_EXT", "4": "GND"}, ""),
    ("F2", ("Device", "Polyfuse"), "PTC 0.5 A hold", "Fuse:Fuse_1206_3216Metric", {"1": "+5V", "2": "+5V_EXT"}, ""),
    ("F3", ("Device", "Polyfuse"), "PTC 0.2 A hold", "Fuse:Fuse_0805_2012Metric", {"1": "+3V3", "2": "+3V3_EXT"},
        "Feeds J11 3V3 and the header 3V3 pins"),
    ("U4", ("Power_Management", "AP22804AW5"), "Load switch 5 V >=1 A, active-high EN, soft start (AP22804AW5 / TPS22918 class)",
        "Package_TO_SOT_SMD:SOT-23-5", {"1": "5V_SW", "2": "GND", "4": "SW_EN", "5": "+5V"},
        "Fed from +5V as in the spec; FLG not used"),
    C("C12", "1u", C0603, "+5V", "GND", "ADDED, not in spec v1: U4 input capacitor"),
    C("C13", "1u", C0603, "5V_SW", "GND", "ADDED, not in spec v1: U4 output capacitor"),
    R("R18", "100k", R0603, "SW_EN", "GND", "Switched output off at boot"),
    R("R19", "0R", R0603, "GPIO27", "SW_EN", "Remove to free GPIO 27"),
    ("D4", ("Device", "D_Schottky"), "SS14 (flyback clamp)", "Diode_SMD:D_SMA", {"1": "5V_SW", "2": "GND"}, ""),
]))

# 10. AUX power out
SECTIONS.append(("10. AUX power out", [
    ("J12", ("Connector", "Screw_Terminal_01x02"), "AUX + / - (>=15 A)", T2_HC, {"1": "AUX+", "2": "GND"},
        "AUX- is PANEL-: never through the shunt"),
    ("F4", ("Device", "Fuse"), "ATO blade holder, fuse NOT fitted (<=3 A on v1; 9 A only with D5 heatsink)", "Fuse:FuseHolder_Blade_ATO_Littelfuse_FLR_178.6165",
        {"1": "PV+", "2": "AUX_F"}, "Empty holder = AUX dead"),
    ("D5", ("Device", "D_Schottky"), "Schottky >=100 V >=10 A (MBR10100 class)", "Package_TO_SOT_THT:TO-220-2_Vertical",
        {"1": "AUX+", "2": "AUX_F"}, "Essential: isolates add-on capacitors from Q1 pulses; heatsink if AUX > ~2 A"),
]))

# Mechanical
SECTIONS.append(("Mechanical", [
    (f"H{i}", ("Mechanical", "MountingHole"), "M3", "MountingHole:MountingHole_3.2mm_M3", {}, "3.5 mm from corners, provisional")
    for i in range(1, 5)
]))

# Power flags (ERC: mark rails that are driven from off-board or from the ESP32's own regulator)
PWR_FLAGS = ["GND", "+5V", "+3V3", "VBAT", "PANEL+", "PV+"]
