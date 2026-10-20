/*
  PVA — panel firmware
  Draft 6 · Oct 2026 · untested
  Boards: ELEGOO ESP32 30-pin (original ESP32, 4 MB flash) — the current build;
          ESP32-S3 with 16 MB flash also supported (set the pins below).

  Build stages (set the switches below)
  - Stage 1, bench:   USB power, probe only.              BENCH 1, PANEL_SENSE 0, USE_RTC 0, SUN_SENSE 0
  - Stage 1, panel:   panel + buck + supercap, probe.     BENCH 0, PANEL_SENSE 0, USE_RTC 0, SUN_SENSE 0
  - Stage 2, full:    + voltage divider, DS3231 clock.    BENCH 0, PANEL_SENSE 1, USE_RTC 1, SUN_SENSE 0
  - Stage 2, sun:     + sun sensor (MOSFET, shunt, INA180) BENCH 0, PANEL_SENSE 1, USE_RTC 1, SUN_SENSE 1
  - Desk test, any board, no sensors:                     BENCH 1, BENCH_FAKE 1 (invented temperature and sun)

  The rhythm
  - The panel wakes with the light, records all day, and goes dark at dusk.
  - During the exhibition, each day's artwork data is written to /art/ and SEALED at
    Bosa's sunset: after that moment nothing more is added to that day.
  - After sunset the panel enters twilight mode (slower CPU, quieter radio) so it can
    stay awake a little longer on the last light; the finished image is still served.
  - Visitors see only the exhibition days. Everything else is raw data for the admin.

  The dial's data (rules v1), all in solar time counted from Bosa's solar noon
  - Sun: every 10 s the sun sensor shorts the panel for about a millisecond and reads
    the short-circuit current. Each 15-minute solar section is sun (1) if more than
    half its readings are above a third of this panel's clear-noon current (set once
    with "Calibrate" on the admin page), shade (0) otherwise, unknown (-1) if the
    sensor is not fitted or not calibrated. The readings themselves are always kept.
  - Heat: panel temperature every 5 minutes.
  - Presence: distinct phones on the panel's Wi-Fi in each solar hour. Phones are
    told apart only by a salted hash held in memory for that hour; nothing that
    identifies a phone is ever stored.

  No battery, no clean on/off
  - Dawn gate: at boot the radio stays off (the biggest draw) and the board idles in
    light sleep until the panel holds GATE_V for GATE_MS. Only then does Wi-Fi start.
  - Session merging: a reboot within MERGE_S on the same day continues the session.
  - The ESP32's own brownout detector holds the chip in reset when the supply sags.

  Files
  - Raw (private, admin only):
      /log/current.csv   5-minute records         -> /archive/sess-NNNNN.csv
      /log/sun.csv       1-minute sun current     -> /archive/sun-NNNNN.csv
      /log/vis.csv       visitors per solar hour  -> /archive/vis-NNNNN.csv
      /archive/summary.csv  one line per session
  - Art (public, exhibition days only, sealed at sunset):
      /art/YYYY-MM-DD.csv      epoch, volts, temp_c, isc       (every 5 minutes)
      /art/YYYY-MM-DD.sun.csv  section, sun, readings, above, isc_mean
      /art/YYYY-MM-DD.vis.csv  hour, visitors

  Time
  - DS3231 clock module with coin cell (USE_RTC 1): set once by the admin page.
  - Without it, the first visitor's phone sets the time each day (sealing may then be late).

  Admin (on the panel's own Wi-Fi, http://192.168.4.1/admin.html)
  - status, set clock, set exhibition dates, calibrate the sun sensor, download all raw
    data. Every call needs ADMIN_KEY. The key travels as plain HTTP on an open network.

  Wiring (ELEGOO 30-pin on the screw-terminal breakout)
  - Panel -> fuse -> reverse-polarity diode -> buck converter (8–60 V in), set to 5.0 V
    BEFORE anything else is connected -> 5V/VIN and GND terminals.
  - 5.5 V 4 F supercapacitor across the 5 V output (in the shaded box). It also carries
    the board through each sun-sensor pulse, while the diode keeps the converter's
    input capacitor from being shorted.
  - TVS diode SMAJ5.0A across the 5 V output (stage 2).
  - DS18B20 on the panel back: red 3.3 V, black GND, yellow GPIO 4, 4.7k GPIO 4 to 3.3 V.
  - Panel voltage (stage 2): Panel + -> 100k -> GPIO 34 -> 4.7k -> GND (+ 100 nF). 48 V -> 2.15 V, 60 V -> 2.7 V.
    Must be GPIO 32–39 on the original ESP32 (ADC1): the others stop working with Wi-Fi.
  - DS3231 (stage 2): 3.3 V, GND, SDA GPIO 21, SCL GPIO 22.
  - Sun sensor (stage 2): logic-level N-MOSFET (>=60 V, >=20 A) across the panel,
    after an input Schottky (>=100 V, >=15 A) and BEFORE the fuse and the 1N5408 (the short-circuit current must not run through
    the fuse), drain to panel +, source through the shunt to panel −; gate on GPIO 25 with a 100 Ω series
    resistor and a 10k pull-down. Shunt SHUNT_OHM in the MOSFET's source leg; INA180A3
    (gain 100) across the shunt, powered from 3.3 V, output to GPIO 35. Check SHUNT_OHM
    and SENSE_GAIN against the parts fitted.

  Build (Arduino IDE, ESP32 core 3.x)
  - Libraries: OneWire, DallasTemperature, RTClib
  - ELEGOO: board "ESP32 Dev Module" · Flash 4MB · Partition Scheme: Custom
    (partitions.csv, ~2 MB LittleFS). For a 16 MB S3, use partitions_16mb.csv instead
    (rename it to partitions.csv) and board "ESP32S3 Dev Module", PSRAM OPI.
  - data/ folder: index.html, admin.html, media/   (upload with the LittleFS uploader)
  - panel_config.h: copy from panel_config.example.h; panel name and admin key per panel
*/

#include <WiFi.h>
#include <WebServer.h>
#include <DNSServer.h>
#include <LittleFS.h>
#include <Preferences.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include <Wire.h>
#include <RTClib.h>
#include <esp_wifi.h>
#include <esp_random.h>
#include <sys/time.h>
#include <time.h>
#include <math.h>
#include <limits.h>
#include <esp_sleep.h>
#include <vector>
#include <algorithm>

// ---------------- build stage ----------------
#define BENCH          1       // 1 = USB power at the desk: no dawn gate, no dusk close
#define PANEL_SENSE    0       // 1 = voltage divider fitted (needed for dawn gate and dusk)
#define USE_RTC        0       // 1 = DS3231 clock module fitted
#define SUN_SENSE      0       // 1 = sun sensor fitted (MOSFET, shunt, INA180)
#define BENCH_FAKE     0       // 1 = desk test with no sensors: invents temperature and sun current
                               //     so the dial shows every layer. Never on a real panel.

// ---------------- pins ----------------
#if CONFIG_IDF_TARGET_ESP32
  #define PIN_TEMP       4     // ELEGOO 30-pin: DS18B20 data
  #define PIN_PANEL_ADC  34    // ADC1 only (GPIO 32–39); input-only pin, fine for a divider
  #define PIN_SUN_ADC    35    // ADC1, input-only: INA180 output
  #define PIN_SUN_GATE   25    // MOSFET gate
  #define PIN_SDA        21
  #define PIN_SCL        22
#else
  #define PIN_TEMP       -1    // S3: a free GPIO from the board pinout; -1 = no probe fitted
  #define PIN_PANEL_ADC  -1    // S3: ADC1 is GPIO 1–10
  #define PIN_SUN_ADC    -1
  #define PIN_SUN_GATE   -1
  #define PIN_SDA        -1    // -1 = the board's default I2C pins
  #define PIN_SCL        -1
  #if (PANEL_SENSE && PIN_PANEL_ADC < 0) || (SUN_SENSE && (PIN_SUN_ADC < 0 || PIN_SUN_GATE < 0))
  #error "Set the pins for this board"
  #endif
#endif
#define DAWN_GATE      (PANEL_SENSE && !BENCH)   // gate and dusk logic need a real panel reading
#define SUN_DATA       (SUN_SENSE || BENCH_FAKE) // sun sections are recorded
#if BENCH_FAKE && !BENCH
#error "BENCH_FAKE is for the desk only: set BENCH 1"
#endif

// ---------------- identity ----------------
// Per-panel settings live in panel_config.h (not in the repo): copy
// panel_config.example.h to panel_config.h and set the values for each panel.
#include "panel_config.h"
const char* PANEL_ID      = PVA_PANEL_ID;           // also the Wi-Fi name
const char* AP_PASS       = PVA_AP_PASS;            // "" = open network
const char* ADMIN_KEY     = PVA_ADMIN_KEY;          // a different key per panel
const char* FW_VERSION    = "pva-fw-6.1.1";
const char* RULES_VERSION = "rules-1";              // keep in step with index.html

// ---------------- place ----------------
const char*  TZ_INFO = "CET-1CEST,M3.5.0,M10.5.0/3"; // Italy
const double LAT = 40.2986, LNG = 8.4970;            // Bosa: the dial runs on the town's sun

// ---------------- behaviour ----------------
const float    DIVIDER        = (100.0 + 4.7) / 4.7;   // R1 100k, R2 4k7 (carrier v1)
const float    SHUNT_OHM      = 0.005;              // sun sensor shunt
const float    SENSE_GAIN     = 100.0;              // INA180A3 (gain 100: a vertical panel gives only ~1/3 of Isc)
const float    SUN_FRACTION   = 1.0 / 3;            // sun = above this share of clear-noon current
const uint32_t SAMPLE_MS      = 10UL * 1000;
const uint32_t RECORD_MS      = 5UL * 60 * 1000;
const uint32_t SUNLOG_MS      = 60UL * 1000;
const float    DUSK_V         = 7.0;
const float    DAWN_V         = 8.0;
const uint8_t  DUSK_SAMPLES   = 3;
const float    GATE_V         = 12.0;               // panel volts that must hold before the radio starts
const uint32_t GATE_MS        = 60UL * 1000;        // ...for this long
const uint32_t MERGE_S        = 45UL * 60;          // a reboot within this gap continues the session
const uint16_t KEEP_SESSIONS  = 2000;               // raw data is kept; prune only if storage fills
const uint8_t  FS_MAX_PCT     = 90;
const int      SEC_S          = 15 * 60;            // dial section
const int      HOUR_S         = 60 * 60;            // presence hour
const int      MAX_PHONES     = 64;

// ---------------- files ----------------
const char* CUR      = "/log/current.csv";
const char* SUNLOG   = "/log/sun.csv";
const char* VISLOG   = "/log/vis.csv";
const char* SUM      = "/archive/summary.csv";
const char* CUR_HDR  = "uptime_s,epoch,volts,volts_peak,temp_c,temp_peak,visitors,isc\n";
const char* SUN_HDR  = "uptime_s,epoch,isc_avg,isc_max\n";
const char* VIS_HDR  = "epoch,hour,visitors\n";
const char* SUM_HDR  = "session,records,duration_s,start_epoch,end_epoch,volts_peak,temp_min,temp_max,max_visitors\n";
const char* ART_HDR  = "epoch,volts,temp_c,isc\n";
const char* ARTS_HDR = "section,sun,readings,above,isc_mean\n";
const char* ARTV_HDR = "hour,visitors\n";

// ---------------- state ----------------
IPAddress         apIP(192, 168, 4, 1);
DNSServer         dns;
WebServer         server(80);
Preferences       prefs;
#if PIN_TEMP >= 0
OneWire           ow(PIN_TEMP);
DallasTemperature ds(&ow);
#endif
RTC_DS3231        rtc;

uint32_t session = 0;
bool     timeKnown = false, rtcOk = false, tempOk = false;
bool     closed = false, twilight = false;
int64_t  exStart = 0, exEnd = 0;   // epochs: local midnight of first day, local midnight after last day
uint8_t  lowCount = 0;
uint32_t lastSample = 0, lastRecord = 0, lastSunLog = 0;
float    nowV = 0, nowT = NAN, nowI = NAN;
float    sumV = 0, peakV = 0, sumT = 0, peakT = -1000, sumI = 0;
uint16_t nV = 0, nT = 0, nI = 0;
float    iref = 0;                                  // clear-noon short-circuit current (A)
float    recentI[6] = { 0 };                        // last minute of readings, for calibration
uint8_t  recentIdx = 0;
float    minSum = 0, minMax = 0; uint16_t minN = 0; // 1-minute sun log

// dial section (15 min) and presence hour, in solar time
int      secK = INT_MIN; uint16_t secN = 0, secAbove = 0; float secSum = 0; String secDay;
int      hourK = INT_MIN; String hourDay;
uint32_t phones[MAX_PHONES]; uint8_t nPhones = 0;
uint32_t salt = 0;

// ================= time and the sun =================
time_t nowEpoch() { return timeKnown ? time(nullptr) : 0; }

void setClock(time_t t, bool writeRtc) {
  struct timeval tv = { t, 0 };
  settimeofday(&tv, nullptr);
  timeKnown = true;
  if (writeRtc && rtcOk) rtc.adjust(DateTime((uint32_t)t));
}

String dateStr(time_t t) {
  struct tm lt; localtime_r(&t, &lt);
  char b[12]; strftime(b, sizeof b, "%Y-%m-%d", &lt);
  return String(b);
}

// Sunrise, solar noon and sunset (UTC epoch s) for the local day containing t.
// After SunCalc (Agafonkin); the same formula as the panel page and tools/pva_rules.py.
void sunTimes(time_t t, time_t* rise, time_t* noon, time_t* set) {
  const double rad = M_PI / 180.0, J1970 = 2440588.0, J2000 = 2451545.0;
  struct tm lt; localtime_r(&t, &lt);
  lt.tm_hour = 12; lt.tm_min = 0; lt.tm_sec = 0;
  time_t mid = mktime(&lt);
  double d   = mid / 86400.0 - 0.5 + J1970 - J2000;
  double lw  = -LNG * rad, phi = LAT * rad;
  double n   = round(d - 0.0009 - lw / (2 * M_PI));
  double ds_ = 0.0009 + lw / (2 * M_PI) + n;
  double M   = rad * (357.5291 + 0.98560028 * ds_);
  double C   = rad * (1.9148 * sin(M) + 0.02 * sin(2 * M) + 0.0003 * sin(3 * M));
  double L   = M + C + rad * 102.9372 + M_PI;
  double dec = asin(sin(L) * sin(rad * 23.4397));
  double Jnoon = J2000 + ds_ + 0.0053 * sin(M) - 0.0069 * sin(2 * L);
  double w   = acos((sin(-0.833 * rad) - sin(phi) * sin(dec)) / (cos(phi) * cos(dec)));
  double Jset = J2000 + 0.0009 + (w + lw) / (2 * M_PI) + n + 0.0053 * sin(M) - 0.0069 * sin(2 * L);
  auto toT = [&](double j) { return (time_t)((j + 0.5 - J1970) * 86400.0); };
  if (rise) *rise = toT(2 * Jnoon - Jset);
  if (noon) *noon = toT(Jnoon);
  if (set)  *set  = toT(Jset);
}
time_t sunsetFor(time_t t) { time_t s; sunTimes(t, nullptr, nullptr, &s); return s; }

bool inExhibition(time_t t) { return exStart && t >= exStart && t < exEnd; }
bool artMoment(time_t t, time_t rise, time_t set) { return t && inExhibition(t) && t >= rise && t < set; }

// floor / ceil division that behave for negative offsets (morning)
int floorDiv(long long a, int b) { return (int)(a >= 0 ? a / b : -((-a + b - 1) / b)); }
int ceilDiv(long long a, int b)  { return -floorDiv(-a, b); }

// ================= sensors =================
float readPanelV() {
#if !PANEL_SENSE
  return 0;                        // no divider fitted: volts are logged as 0
#endif
  uint32_t mv = 0;
  for (int k = 0; k < 8; k++) mv += analogReadMilliVolts(PIN_PANEL_ADC);
  return (mv / 8.0f) / 1000.0f * DIVIDER;
}

// Short the panel for about a millisecond and read the current: proportional to sunlight.
// desk test: a clear day with a few passing clouds, from the clock (or uptime if no clock yet)
float fakeHour() {
  time_t t = nowEpoch();
  if (!t) return 8 + (millis() / 1000.0f) / 60.0f;          // no clock: one "hour" per real minute
  struct tm lt; localtime_r(&t, &lt);
  return lt.tm_hour + lt.tm_min / 60.0f + lt.tm_sec / 3600.0f;
}

float readSunI() {
#if BENCH_FAKE
  float h = fakeHour(), s = sinf(M_PI * (h - 6.0f) / 15.0f);
  bool cloud = sinf(h * 7.3f) + sinf(h * 2.1f) > 1.3f;
  return s > 0 ? 3.0f * s * (cloud ? 0.15f : 1.0f) : 0;
#elif !SUN_SENSE
  return NAN;
#else
  digitalWrite(PIN_SUN_GATE, HIGH);
  delayMicroseconds(400);          // let the current settle
  uint32_t mv = 0;
  for (int k = 0; k < 4; k++) mv += analogReadMilliVolts(PIN_SUN_ADC);
  digitalWrite(PIN_SUN_GATE, LOW);
  float i = (mv / 4.0f) / 1000.0f / (SHUNT_OHM * SENSE_GAIN);
  return i < 0 ? 0 : i;
#endif
}

float readTempC() {               // non-blocking: read last conversion, request the next
#if BENCH_FAKE
  float h = fakeHour(), s = sinf(M_PI * (h - 7.0f) / 14.0f);
  return 21.0f + (s > 0 ? 26.0f * s : 0) + (esp_random() % 100) / 100.0f;
#endif
#if PIN_TEMP < 0
  return NAN;
#else
  if (!tempOk) return NAN;
  float t = ds.getTempCByIndex(0);
  ds.requestTemperatures();
  return (t > -100 && t < 125) ? t : NAN;
#endif
}

// ================= files =================
void appendLine(const String& path, const char* hdr, const char* line) {
  bool isNew = !LittleFS.exists(path);
  File f = LittleFS.open(path, FILE_APPEND);
  if (!f) return;
  if (isNew) f.print(hdr);
  f.print(line);
  f.close();
}

// ================= presence: distinct phones per solar hour =================
uint32_t phoneHash(const uint8_t* mac) {          // salted FNV-1a; the salt never leaves RAM
  uint32_t h = 2166136261u ^ salt;
  for (int i = 0; i < 6; i++) { h ^= mac[i]; h *= 16777619u; }
  return h;
}

void notePhones() {
  wifi_sta_list_t list;
  if (esp_wifi_ap_get_sta_list(&list) != ESP_OK) return;
  for (int i = 0; i < list.num; i++) {
    uint32_t h = phoneHash(list.sta[i].mac);
    bool seen = false;
    for (uint8_t j = 0; j < nPhones; j++) if (phones[j] == h) { seen = true; break; }
    if (!seen && nPhones < MAX_PHONES) phones[nPhones++] = h;
  }
}

void flushHour(time_t now) {
  if (hourK == INT_MIN) return;
  char buf[48];
  snprintf(buf, sizeof buf, "%lld,%d,%u\n", (long long)now, hourK, nPhones);
  appendLine(VISLOG, VIS_HDR, buf);                                  // raw: always
  if (nPhones && hourDay.length()) {                                // art: only if flagged
    snprintf(buf, sizeof buf, "%d,%u\n", hourK, nPhones);
    appendLine("/art/" + hourDay + ".vis.csv", ARTV_HDR, buf);
  }
  hourK = INT_MIN; nPhones = 0; hourDay = "";
}

// ================= sun: 15-minute solar sections =================
void flushSection() {
  if (secK == INT_MIN) return;
  if (secDay.length() && secN) {
    int verdict = (SUN_DATA && iref > 0) ? (secAbove * 2 > secN ? 1 : 0) : -1;
    char buf[64];
    snprintf(buf, sizeof buf, "%d,%d,%u,%u,%.3f\n", secK, verdict, secN, secAbove, secSum / secN);
    appendLine("/art/" + secDay + ".sun.csv", ARTS_HDR, buf);
  }
  secK = INT_MIN; secN = secAbove = 0; secSum = 0; secDay = "";
}

void trackDial(time_t now) {
  if (!now) return;
  time_t rise, noon, set;
  sunTimes(now, &rise, &noon, &set);
  bool art = artMoment(now, rise, set);
  String day = art ? dateStr(now) : String("");

  // presence hour k covers (noon + (k-1) h, noon + k h]; its dot sits at noon + k h
  int hk = ceilDiv((long long)(now - noon), HOUR_S);
  if (hk != hourK) { flushHour(now); hourK = hk; hourDay = day; }
  else if (art && !hourDay.length()) hourDay = day;   // the hour that sunrise falls in
  notePhones();

#if SUN_DATA
  if (now < rise || now >= set || isnan(nowI)) return;
  int k = floorDiv((long long)(now - noon), SEC_S);
  if (k != secK) { flushSection(); secK = k; secDay = day; }
  secN++; secSum += nowI;
  if (iref > 0 && nowI > iref * SUN_FRACTION) secAbove++;
#endif
}

// ================= logging =================
void writeRecord() {
  if (!nV) return;
  float vAvg = sumV / nV, tAvg = nT ? sumT / nT : NAN, iAvg = nI ? sumI / nI : NAN;
  time_t now = nowEpoch();
  char buf[160];

  snprintf(buf, sizeof buf, "%lu,%lld,%.2f,%.2f,%.1f,%.1f,%u,%.3f\n",
           (unsigned long)(millis() / 1000), (long long)now, vAvg, peakV,
           tAvg, nT ? peakT : NAN, (unsigned)WiFi.softAPgetStationNum(), iAvg);
  appendLine(CUR, CUR_HDR, buf);

  if (now) {
    time_t rise, noon, set;
    sunTimes(now, &rise, &noon, &set);
    if (artMoment(now, rise, set)) {     // the seal: nothing after sunset
      snprintf(buf, sizeof buf, "%lld,%.2f,%.1f,%.3f\n", (long long)now, vAvg, tAvg, iAvg);
      appendLine("/art/" + dateStr(now) + ".csv", ART_HDR, buf);
    }
  }
  sumV = peakV = sumT = sumI = 0; peakT = -1000; nV = nT = nI = 0;
}

void writeSunLog() {
  lastSunLog = millis();
  if (!minN) return;
  char buf[64];
  snprintf(buf, sizeof buf, "%lu,%lld,%.3f,%.3f\n", (unsigned long)(millis() / 1000),
           (long long)nowEpoch(), minSum / minN, minMax);
  appendLine(SUNLOG, SUN_HDR, buf);
  minSum = minMax = 0; minN = 0;
}

void enterTwilight() {
  twilight = true;
  writeRecord();                       // last record before the seal
  flushSection();
  flushHour(nowEpoch());
  setCpuFrequencyMhz(80);              // lowest speed Wi-Fi allows
  WiFi.setTxPower(WIFI_POWER_2dBm);    // quieter radio: the network shrinks with the light
}

void sample() {
  lastSample = millis();
  nowV = readPanelV();
  nowT = readTempC();
  nowI = readSunI();

  if (!isnan(nowI)) {
    recentI[recentIdx++ % 6] = nowI;
    minSum += nowI; if (nowI > minMax) minMax = nowI; minN++;
  }
  if (!closed) {
    sumV += nowV; if (nowV > peakV) peakV = nowV; nV++;
    if (!isnan(nowT)) { sumT += nowT; if (nowT > peakT) peakT = nowT; nT++; }
    if (!isnan(nowI)) { sumI += nowI; nI++; }
  }

  time_t now = nowEpoch();
  if (!twilight) trackDial(now);
  if (now && !twilight && now >= sunsetFor(now)) enterTwilight();

#if DAWN_GATE                        // dusk close needs a real panel reading
  if (!closed && nowV < DUSK_V) {
    if (++lowCount >= DUSK_SAMPLES) { writeRecord(); closed = true; }
  } else if (nowV >= DUSK_V) {
    lowCount = 0;
  }
  if (closed && nowV > DAWN_V) { closed = false; lowCount = 0; lastRecord = millis(); }
#endif
}

// ================= raw archive (once, at boot) =================
void archivePrevious(uint32_t prev) {
  char dst[40];
  snprintf(dst, sizeof dst, "/archive/sun-%05lu.csv", (unsigned long)prev);
  if (LittleFS.exists(SUNLOG)) LittleFS.rename(SUNLOG, dst);
  snprintf(dst, sizeof dst, "/archive/vis-%05lu.csv", (unsigned long)prev);
  if (LittleFS.exists(VISLOG)) LittleFS.rename(VISLOG, dst);

  if (!LittleFS.exists(CUR)) return;
  File f = LittleFS.open(CUR, FILE_READ);
  uint32_t rows = 0, firstUp = 0, lastUp = 0, maxVis = 0;
  long long firstE = 0, lastE = 0;
  float vPeak = 0, tMin = 1000, tMax = -1000;
  f.readStringUntil('\n');
  while (f.available()) {
    String line = f.readStringUntil('\n');
    unsigned long up; long long e; float v, vp, t, tp; unsigned vis;
    if (sscanf(line.c_str(), "%lu,%lld,%f,%f,%f,%f,%u", &up, &e, &v, &vp, &t, &tp, &vis) != 7) continue;
    if (!rows) firstUp = up;
    lastUp = up; rows++;
    if (e) { if (!firstE) firstE = e; lastE = e; }
    if (vp > vPeak) vPeak = vp;
    if (!isnan(t) && t < tMin) tMin = t;
    if (!isnan(tp) && tp > tMax) tMax = tp;
    if (vis > maxVis) maxVis = vis;
  }
  f.close();
  if (!rows) { LittleFS.remove(CUR); return; }
  unsigned long dur = (firstE && lastE) ? (unsigned long)(lastE - firstE)
                    : (lastUp >= firstUp ? lastUp - firstUp : 0);
  char buf[160];
  snprintf(buf, sizeof buf, "%lu,%lu,%lu,%lld,%lld,%.2f,%.1f,%.1f,%lu\n",
           (unsigned long)prev, (unsigned long)rows, dur,
           firstE, lastE, vPeak, tMin < 999 ? tMin : NAN, tMax > -999 ? tMax : NAN, (unsigned long)maxVis);
  appendLine(SUM, SUM_HDR, buf);
  snprintf(dst, sizeof dst, "/archive/sess-%05lu.csv", (unsigned long)prev);
  LittleFS.rename(CUR, dst);
}

// epoch of the last complete record in a raw log (0 if none)
long long lastEpochIn(const char* path) {
  File f = LittleFS.open(path, FILE_READ);
  if (!f) return 0;
  size_t sz = f.size();
  f.seek(sz > 512 ? sz - 512 : 0);
  String tail = f.readString();
  f.close();
  long long last = 0;
  int from = 0;
  for (int nl = tail.indexOf('\n'); nl >= 0; from = nl + 1, nl = tail.indexOf('\n', from)) {
    String line = tail.substring(from, nl);   // only lines ending in a newline: complete records
    unsigned long up; long long e; float a, b, c, d; unsigned vis;
    if (sscanf(line.c_str(), "%lu,%lld,%f,%f,%f,%f,%u", &up, &e, &a, &b, &c, &d, &vis) == 7 && e > 0) last = e;
  }
  return last;
}

// ================= dawn gate (radio off until the panel can carry it) =================
void dawnGate() {
  uint32_t okSince = 0;
  esp_sleep_enable_timer_wakeup(1000000ULL);           // check once a second
  while (true) {
    float v = readPanelV();
    if (v >= GATE_V) {
      if (!okSince) okSince = millis();
      if (millis() - okSince >= GATE_MS) break;
    } else {
      okSince = 0;
    }
    esp_light_sleep_start();                           // a few milliamps while waiting
  }
  esp_sleep_disable_wakeup_source(ESP_SLEEP_WAKEUP_TIMER);
}

uint8_t fsFullPct() { return (uint8_t)(100.0 * LittleFS.usedBytes() / LittleFS.totalBytes()); }

std::vector<String> listDir(const char* path, const char* prefix) {
  std::vector<String> out;
  File dir = LittleFS.open(path);
  if (!dir) return out;
  for (File e = dir.openNextFile(); e; e = dir.openNextFile()) {
    String n = e.name();
    if (n.startsWith(prefix) && n.endsWith(".csv")) out.push_back(n);
  }
  dir.close();
  std::sort(out.begin(), out.end());
  return out;
}

// exhibition days with art data: names exactly YYYY-MM-DD.csv
std::vector<String> artDays() {
  std::vector<String> out;
  for (auto& n : listDir("/art", "2")) if (n.length() == 14) out.push_back(n.substring(0, 10));
  return out;
}

void prune() {   // raw detail only, oldest session first, only past the limits
  auto files = listDir("/archive", "sess-");
  size_t k = 0;
  while (k < files.size() && (files.size() - k > KEEP_SESSIONS || fsFullPct() > FS_MAX_PCT)) {
    String num = files[k].substring(5, 10);
    LittleFS.remove("/archive/" + files[k]);
    LittleFS.remove("/archive/sun-" + num + ".csv");
    LittleFS.remove("/archive/vis-" + num + ".csv");
    k++;
  }
}

// ================= public web =================
void handleRoot() {
  File f = LittleFS.open("/index.html", FILE_READ);
  if (!f) { server.send(200, "text/plain", "PVA panel: no index.html uploaded."); return; }
  server.streamFile(f, "text/html");
  f.close();
}

void handleSync() {   // a visitor lends the time only if the panel has none
  if (!timeKnown && server.hasArg("t")) {
    int64_t t = atoll(server.arg("t").c_str());
    if (t > 1700000000000LL) setClock((time_t)(t / 1000), false);
  }
  server.send(204);
}

String numOrNull(float v, int dp) { return isnan(v) ? String("null") : String(v, dp); }

void handleNow() {
  time_t now = nowEpoch();
  String j = "{\"panel\":\"" + String(PANEL_ID) + "\"";
  j += ",\"epoch\":" + String((long long)now);
  j += ",\"sunset\":" + String((long long)(now ? sunsetFor(now) : 0));
  j += ",\"twilight\":"; j += twilight ? "true" : "false";
  j += ",\"closed\":";   j += closed ? "true" : "false";
  j += ",\"v\":" + String(nowV, 2) + ",\"t\":" + numOrNull(nowT, 1) + ",\"isc\":" + numOrNull(nowI, 3);
  j += ",\"uptime\":" + String(millis() / 1000) + ",\"visitors\":" + String(WiFi.softAPgetStationNum());
  j += ",\"exhibition\":"; j += (now && inExhibition(now)) ? "true" : "false";
  j += "}";
  server.send(200, "application/json", j);
}

void handleArtList() {
  time_t now = nowEpoch();
  String j = "{\"panel\":\"" + String(PANEL_ID) + "\",\"rules\":\"" + RULES_VERSION + "\"";
  j += ",\"lat\":" + String(LAT, 4) + ",\"lng\":" + String(LNG, 4);
  j += ",\"start\":\"" + (exStart ? dateStr(exStart) : String("")) + "\"";
  j += ",\"end\":\"" + (exEnd ? dateStr(exEnd - 1) : String("")) + "\"";
  j += ",\"today\":\"" + (now ? dateStr(now) : String("")) + "\"";
  j += ",\"epoch\":" + String((long long)now) + ",\"sunset\":" + String((long long)(now ? sunsetFor(now) : 0));
  j += ",\"sun_sensor\":"; j += (SUN_DATA && iref > 0) ? "true" : "false";
  j += ",\"days\":[";
  auto days = artDays();
  for (size_t i = 0; i < days.size(); i++) { if (i) j += ','; j += "\"" + days[i] + "\""; }
  j += "]}";
  server.send(200, "application/json", j);
}

void handleCaptive() {
  server.sendHeader("Location", "http://192.168.4.1/", true);
  server.send(302, "text/plain", "");
}

// ================= admin =================
bool checkKey() {
  if (server.arg("key") == ADMIN_KEY) return true;
  server.send(403, "text/plain", "Forbidden");
  return false;
}

void handleAdminStatus() {
  if (!checkKey()) return;
  time_t now = nowEpoch();
  String j = "{";
  j += "\"panel\":\"" + String(PANEL_ID) + "\",\"firmware\":\"" + FW_VERSION + "\",\"rules\":\"" + RULES_VERSION + "\"";
  j += ",\"epoch\":" + String((long long)now);
  j += ",\"time_known\":"; j += timeKnown ? "true" : "false";
  j += ",\"rtc\":";        j += rtcOk ? "true" : "false";
  j += ",\"start\":\"" + (exStart ? dateStr(exStart) : String("")) + "\"";
  j += ",\"end\":\"" + (exEnd ? dateStr(exEnd - 1) : String("")) + "\"";
  j += ",\"sunset\":" + String((long long)(now ? sunsetFor(now) : 0));
  j += ",\"session\":" + String(session) + ",\"uptime\":" + String(millis() / 1000);
  j += ",\"volts\":" + String(nowV, 2) + ",\"temp\":" + numOrNull(nowT, 1);
  j += ",\"temp_sensor\":"; j += tempOk ? "true" : "false";
  j += ",\"sun_sensor\":";  j += SUN_DATA ? "true" : "false";
  j += ",\"bench_fake\":";  j += BENCH_FAKE ? "true" : "false";
  j += ",\"isc\":" + numOrNull(nowI, 3) + ",\"iref\":" + String(iref, 3);
  j += ",\"visitors_hour\":" + String(nPhones);
  j += ",\"art_days\":" + String(artDays().size());
  j += ",\"raw_sessions\":" + String(listDir("/archive", "sess-").size());
  j += ",\"used\":" + String(LittleFS.usedBytes()) + ",\"total\":" + String(LittleFS.totalBytes());
  j += "}";
  server.send(200, "application/json", j);
}

void handleAdminClock() {   // the admin's phone sets the clock (and the RTC)
  if (!checkKey()) return;
  int64_t t = atoll(server.arg("t").c_str());
  if (t < 1700000000000LL) { server.send(400, "text/plain", "bad time"); return; }
  setClock((time_t)(t / 1000), true);
  server.send(200, "text/plain", "ok");
}

void handleAdminWindow() {  // start / end as epoch seconds computed on the admin phone
  if (!checkKey()) return;
  int64_t s = atoll(server.arg("start").c_str()), e = atoll(server.arg("end").c_str());
  if (s <= 0 || e <= s) { server.send(400, "text/plain", "bad dates"); return; }
  exStart = s; exEnd = e;
  prefs.putLong64("exStart", exStart);
  prefs.putLong64("exEnd", exEnd);
  server.send(200, "text/plain", "ok");
}

// "Calibrate" on a clear day near solar noon: the last minute's highest reading
// becomes this panel's clear-noon current.
void handleAdminCalibrate() {
  if (!checkKey()) return;
  if (!SUN_DATA) { server.send(400, "text/plain", "sun sensor not fitted"); return; }
  float best = 0;
  for (float v : recentI) if (v > best) best = v;
  if (best < 0.05) { server.send(400, "text/plain", "no reading yet, or no light"); return; }
  iref = best;
  prefs.putFloat("iref", iref);
  server.send(200, "text/plain", String(iref, 3));
}

// all raw data as one CSV, streamed in chunks
void streamRaw(const String& path, uint32_t sess, String& buf) {
  File f = LittleFS.open(path, FILE_READ);
  if (!f) return;
  f.readStringUntil('\n');
  String prefix = String(sess) + ",";
  while (f.available()) {
    String line = f.readStringUntil('\n');
    if (!line.length()) continue;
    buf += prefix; buf += line; buf += '\n';
    if (buf.length() > 2048) { server.sendContent(buf); buf = ""; }
  }
  f.close();
}

void streamSection(const char* title, const char* header, const char* prefix, const char* live, String& buf) {
  buf += "\n# "; buf += title; buf += "\nsession,"; buf += header;
  for (auto& n : listDir("/archive", prefix))
    streamRaw("/archive/" + n, (uint32_t)n.substring(strlen(prefix), strlen(prefix) + 5).toInt(), buf);
  streamRaw(live, session, buf);
}

void handleAdminExport() {
  if (!checkKey()) return;
  time_t now = nowEpoch();
  String name = String(PANEL_ID) + "_" + (now ? dateStr(now) : String("undated")) + ".csv";
  server.sendHeader("Content-Disposition", "attachment; filename=\"" + name + "\"");
  server.setContentLength(CONTENT_LENGTH_UNKNOWN);
  server.send(200, "text/csv", "");
  String buf;
  buf += "# panel=" + String(PANEL_ID) + " firmware=" + FW_VERSION + " rules=" + RULES_VERSION;
  buf += " lat=" + String(LAT, 4) + " lng=" + String(LNG, 4) + " iref=" + String(iref, 3);
  buf += " exhibition=" + (exStart ? dateStr(exStart) : String("-")) + ".." + (exEnd ? dateStr(exEnd - 1) : String("-"));
  buf += " exported=" + String((long long)now) + "\n";
  buf += "# records (5 minutes)\nsession,"; buf += CUR_HDR;
  for (auto& n : listDir("/archive", "sess-"))
    streamRaw("/archive/" + n, (uint32_t)n.substring(5, 10).toInt(), buf);
  streamRaw(CUR, session, buf);
  streamSection("sun current (1 minute)", SUN_HDR, "sun-", SUNLOG, buf);
  streamSection("visitors per solar hour", VIS_HDR, "vis-", VISLOG, buf);
  if (buf.length()) server.sendContent(buf);
  server.sendContent("");   // end of chunked response
}

// ================= setup / loop =================
void setup() {
  Serial.begin(115200);
  setenv("TZ", TZ_INFO, 1);
  tzset();
  salt = esp_random();

#if SUN_SENSE
  pinMode(PIN_SUN_GATE, OUTPUT);
  digitalWrite(PIN_SUN_GATE, LOW);
  analogSetPinAttenuation(PIN_SUN_ADC, ADC_11db);
#endif

  LittleFS.begin(true);
  LittleFS.mkdir("/log");
  LittleFS.mkdir("/archive");
  LittleFS.mkdir("/art");
  LittleFS.mkdir("/media");

  prefs.begin("panel", false);
  exStart = prefs.getLong64("exStart", 0);
  exEnd   = prefs.getLong64("exEnd", 0);
  iref    = prefs.getFloat("iref", 0);
#if BENCH_FAKE
  if (iref <= 0) iref = 3.0f;      // the invented sun's clear-noon current
#endif

#if USE_RTC
  if (PIN_SDA >= 0) Wire.begin(PIN_SDA, PIN_SCL); else Wire.begin();
  rtcOk = rtc.begin();
  if (rtcOk && !rtc.lostPower()) {
    time_t t = (time_t)rtc.now().unixtime();
    if (t > 1700000000) setClock(t, false);
  }
#endif

#if PANEL_SENSE
  analogSetPinAttenuation(PIN_PANEL_ADC, ADC_11db);
#endif
#if DAWN_GATE
  dawnGate();                          // radio stays off until the panel can carry it
#endif                                 // (without the divider, the supercap smooths the start instead)

  // same day, short gap: a stutter or a cloud, not a new day -> continue the session
  uint32_t prev = prefs.getUInt("session", 0);
  long long lastE = lastEpochIn(CUR);
  time_t now = nowEpoch();
  bool merge = prev && now && lastE && now >= lastE &&
               (now - lastE) < (time_t)MERGE_S && dateStr(now) == dateStr((time_t)lastE);
  if (merge) {
    session = prev;
  } else {
    archivePrevious(prev);
    prune();
    session = prev + 1;
    prefs.putUInt("session", session);
  }

#if PIN_TEMP >= 0
  ds.begin();
  tempOk = ds.getDeviceCount() > 0;
  if (tempOk) { ds.setWaitForConversion(false); ds.requestTemperatures(); }
#endif
#if BENCH_FAKE
  tempOk = true;
#endif

  WiFi.mode(WIFI_AP);
  WiFi.softAPConfig(apIP, apIP, IPAddress(255, 255, 255, 0));
  // channel 1, visible, up to 10 phones at once (the default is only 4)
  WiFi.softAP(PANEL_ID, strlen(AP_PASS) ? AP_PASS : nullptr, 1, 0, 10);
  dns.start(53, "*", apIP);

  // public
  server.on("/", handleRoot);
  server.on("/sync", HTTP_POST, handleSync);
  server.on("/now", handleNow);
  server.on("/art/list", handleArtList);
  server.serveStatic("/art/", LittleFS, "/art/");
  server.serveStatic("/media/", LittleFS, "/media/");
  server.serveStatic("/admin.html", LittleFS, "/admin.html");   // the page is harmless; its calls need the key
  // admin
  server.on("/admin/status", handleAdminStatus);
  server.on("/admin/clock", HTTP_POST, handleAdminClock);
  server.on("/admin/window", HTTP_POST, handleAdminWindow);
  server.on("/admin/calibrate", HTTP_POST, handleAdminCalibrate);
  server.on("/admin/export", handleAdminExport);
  server.onNotFound(handleCaptive);
  server.begin();

  lastSample = lastRecord = lastSunLog = millis();
}

void loop() {
  dns.processNextRequest();
  server.handleClient();
  uint32_t now = millis();
  if (now - lastSample >= SAMPLE_MS) sample();
  if (!closed && now - lastRecord >= RECORD_MS) { writeRecord(); lastRecord = now; }
  if (SUN_DATA && now - lastSunLog >= SUNLOG_MS) writeSunLog();
}
