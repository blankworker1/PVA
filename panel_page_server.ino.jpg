/*
  PVA — panel firmware
  Draft 4 · Oct 2026 · untested
  Board: ESP32-S3 with 16 MB flash (N16R8); prototype on Waveshare ESP32-S3-Touch-LCD-1.47

  The rhythm
  - The panel wakes with the light, records all day, and goes dark at dusk.
  - During the exhibition, each day's artwork data is written to /art/YYYY-MM-DD.csv
    and SEALED at Bosa's sunset: after that moment nothing more is added to that day.
  - After sunset the panel enters twilight mode (slower CPU, quieter radio) so it can
    stay awake a little longer on the last light; the finished image is still served.
  - Visitors see only the exhibition days. Everything else is raw data for the admin.

  No battery, no clean on/off
  - Dawn gate: at boot the radio stays off (the biggest draw) and the board idles in
    light sleep until the panel holds GATE_V for GATE_MS. Only then does Wi-Fi start.
    This stops the dawn stutter: boot, radio on, voltage collapses, brownout, repeat.
  - Session merging: if the last raw record is from the same day and less than
    MERGE_S ago, a reboot (dawn stutter, passing cloud) continues the same session
    instead of starting a new one. No archive step and no settings write on those boots.
  - The ESP32's own brownout detector (on by default) holds the chip in reset when
    the supply sags, so it never runs erratically on a falling voltage.

  Data
  - Raw log: /log/current.csv, archived per power-on to /archive/sess-NNNNN.csv
    plus /archive/summary.csv. Private: only reachable with the admin key.
  - Art log: /art/YYYY-MM-DD.csv (epoch, volts, temp) — public, exhibition days only.

  Time
  - DS3231 clock module with coin cell (USE_RTC 1): set once by the admin page, kept overnight.
  - Without it, the first visitor's phone sets the time each day (sealing may then be late).

  Admin (on the panel's own Wi-Fi, http://192.168.4.1/admin.html)
  - status, set clock, set exhibition dates, download all raw data. Every call needs ADMIN_KEY.
  - The key travels as plain HTTP on an open network: fine for this data, not a secret vault.

  Wiring
  - Panel +  -> 100k -> ADC pin -> 5.6k -> GND (+ 100 nF ADC to GND). Calibrate DIVIDER.
  - DS18B20: 3.3 V, GND, data -> TEMP pin with 4.7k pull-up to 3.3 V.
  - DS3231: 3.3 V, GND, SDA, SCL.
  - Panel -> reverse-polarity diode -> buck converter (LM2596HV, 60 V in; check its
    catch diode is 60 V, e.g. SS56) -> board 5 V.
  - TVS diode SMAJ5.0A across the 5 V output: clamps a spike, and if the converter
    ever fails short it sacrifices itself instead of the board.
  - Optional: extra 470 µF / 63 V across the converter input if dawn stutter persists.

  Build (Arduino IDE, core 3.x)
  - Libraries: OneWire, DallasTemperature, RTClib
  - Board: ESP32S3 Dev Module · Flash 16MB · PSRAM: OPI PSRAM · partitions.csv in sketch folder
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
#include <sys/time.h>
#include <time.h>
#include <math.h>
#include <esp_sleep.h>
#include <vector>
#include <algorithm>

// ---------------- pins: set from the board pinout ----------------
#define PIN_PANEL_ADC  -1      // ADC1 pin (GPIO1–10 on the S3), free of display/touch/SD
#define PIN_TEMP       -1      // any free GPIO
#define USE_RTC        1       // 1 = DS3231 fitted
#define PIN_SDA        -1      // -1 = board default I2C pins
#define PIN_SCL        -1
#define BENCH          0       // 1 = on USB power at the desk: skip the dawn gate
#if (PIN_PANEL_ADC < 0) || (PIN_TEMP < 0)
#error "Set PIN_PANEL_ADC and PIN_TEMP to free GPIOs from the board pinout"
#endif

// ---------------- identity ----------------
// Per-panel settings live in panel_config.h (not in the repo): copy
// panel_config.example.h to panel_config.h and set the values for each panel.
#include "panel_config.h"
const char* PANEL_ID      = PVA_PANEL_ID;           // also the Wi-Fi name
const char* AP_PASS       = PVA_AP_PASS;            // "" = open network
const char* ADMIN_KEY     = PVA_ADMIN_KEY;          // a different key per panel
const char* FW_VERSION    = "pva-fw-4";
const char* RULES_VERSION = "rules-0-placeholder";  // keep in step with index.html

// ---------------- place ----------------
const char*  TZ_INFO = "CET-1CEST,M3.5.0,M10.5.0/3"; // Italy
const double LAT = 40.2986, LNG = 8.4970;            // Bosa: sunset is the town's, not the panel's

// ---------------- behaviour ----------------
const float    DIVIDER        = (100.0 + 5.6) / 5.6;
const uint32_t SAMPLE_MS      = 10UL * 1000;
const uint32_t RECORD_MS      = 5UL * 60 * 1000;
const float    DUSK_V         = 7.0;
const float    DAWN_V         = 8.0;
const uint8_t  DUSK_SAMPLES   = 3;
const float    GATE_V         = 12.0;               // panel volts that must hold before the radio starts
const uint32_t GATE_MS        = 60UL * 1000;        // ...for this long
const uint32_t MERGE_S        = 45UL * 60;          // a reboot within this gap continues the session
const uint16_t KEEP_SESSIONS  = 2000;   // raw data is kept; prune only if storage fills
const uint8_t  FS_MAX_PCT     = 90;
const bool     COUNT_VISITORS = true;

struct Band { const char* name; float lo; };
const Band  BANDS[] = { {"cold", -100}, {"mild", 10}, {"warm", 30}, {"hot", 50} };
const int   NB      = sizeof(BANDS) / sizeof(BANDS[0]);
const float HYST    = 2.0;

// ---------------- files ----------------
const char* CUR     = "/log/current.csv";
const char* SUM     = "/archive/summary.csv";
const char* CUR_HDR = "uptime_s,epoch,volts,volts_peak,temp_c,temp_peak,visitors\n";
const char* SUM_HDR = "session,records,duration_s,start_epoch,end_epoch,volts_peak,temp_min,temp_max,max_visitors\n";
const char* ART_HDR = "epoch,volts,temp_c\n";

// ---------------- state ----------------
IPAddress         apIP(192, 168, 4, 1);
DNSServer         dns;
WebServer         server(80);
Preferences       prefs;
OneWire           ow(PIN_TEMP);
DallasTemperature ds(&ow);
RTC_DS3231        rtc;

uint32_t session = 0;
bool     timeKnown = false, rtcOk = false, tempOk = false;
bool     closed = false, twilight = false;
int64_t  exStart = 0, exEnd = 0;   // epochs: local midnight of first day, local midnight after last day
uint8_t  lowCount = 0;
int      band = -1;
uint32_t lastSample = 0, lastRecord = 0;
float    nowV = 0, nowT = NAN;
float    sumV = 0, peakV = 0, sumT = 0, peakT = -1000;
uint16_t nV = 0, nT = 0;

// ================= time =================
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

// Sunset for the local day containing t (after SunCalc, Agafonkin). Returns UTC epoch seconds.
time_t sunsetFor(time_t t) {
  const double rad = M_PI / 180.0, J1970 = 2440588.0, J2000 = 2451545.0;
  struct tm lt; localtime_r(&t, &lt);
  lt.tm_hour = 12; lt.tm_min = 0; lt.tm_sec = 0;
  time_t noon = mktime(&lt);
  double d   = noon / 86400.0 - 0.5 + J1970 - J2000;
  double lw  = -LNG * rad, phi = LAT * rad;
  double n   = round(d - 0.0009 - lw / (2 * M_PI));
  double ds_ = 0.0009 + lw / (2 * M_PI) + n;
  double M   = rad * (357.5291 + 0.98560028 * ds_);
  double C   = rad * (1.9148 * sin(M) + 0.02 * sin(2 * M) + 0.0003 * sin(3 * M));
  double L   = M + C + rad * 102.9372 + M_PI;
  double dec = asin(sin(L) * sin(rad * 23.4397));
  double w   = acos((sin(-0.833 * rad) - sin(phi) * sin(dec)) / (cos(phi) * cos(dec)));
  double Jset = J2000 + 0.0009 + (w + lw) / (2 * M_PI) + n + 0.0053 * sin(M) - 0.0069 * sin(2 * L);
  return (time_t)((Jset + 0.5 - J1970) * 86400.0);
}

bool inExhibition(time_t t) { return exStart && t >= exStart && t < exEnd; }

// ================= sensors =================
float readPanelV() {
  uint32_t mv = 0;
  for (int k = 0; k < 8; k++) mv += analogReadMilliVolts(PIN_PANEL_ADC);
  return (mv / 8.0f) / 1000.0f * DIVIDER;
}

float readTempC() {               // non-blocking: read last conversion, request the next
  if (!tempOk) return NAN;
  float t = ds.getTempCByIndex(0);
  ds.requestTemperatures();
  return (t > -100 && t < 125) ? t : NAN;
}

void updateBand(float t) {
  if (isnan(t)) return;
  if (band < 0) { band = 0; for (int b = 0; b < NB; b++) if (t >= BANDS[b].lo) band = b; return; }
  while (band + 1 < NB && t >= BANDS[band + 1].lo + HYST) band++;
  while (band > 0 && t < BANDS[band].lo - HYST) band--;
}

// ================= logging =================
void appendLine(const String& path, const char* hdr, const char* line) {
  bool isNew = !LittleFS.exists(path);
  File f = LittleFS.open(path, FILE_APPEND);
  if (!f) return;
  if (isNew) f.print(hdr);
  f.print(line);
  f.close();
}

void writeRecord() {
  if (!nV) return;
  float vAvg = sumV / nV, tAvg = nT ? sumT / nT : NAN;
  time_t now = nowEpoch();
  char buf[128];

  // raw: always
  snprintf(buf, sizeof buf, "%lu,%lld,%.2f,%.2f,%.1f,%.1f,%u\n",
           (unsigned long)(millis() / 1000), (long long)now, vAvg, peakV,
           tAvg, nT ? peakT : NAN,
           COUNT_VISITORS ? (unsigned)WiFi.softAPgetStationNum() : 0u);
  appendLine(CUR, CUR_HDR, buf);

  // art: only exhibition days, only before Bosa's sunset (the seal)
  if (now && inExhibition(now) && now < sunsetFor(now)) {
    snprintf(buf, sizeof buf, "%lld,%.2f,%.1f\n", (long long)now, vAvg, tAvg);
    appendLine("/art/" + dateStr(now) + ".csv", ART_HDR, buf);
  }

  sumV = peakV = sumT = 0; peakT = -1000; nV = nT = 0;
}

void enterTwilight() {
  twilight = true;
  writeRecord();                       // last record before the seal took effect
  setCpuFrequencyMhz(80);              // lowest speed Wi-Fi allows
  WiFi.setTxPower(WIFI_POWER_2dBm);    // quieter radio: the network shrinks with the light
}

void sample() {
  lastSample = millis();
  nowV = readPanelV();
  nowT = readTempC();
  updateBand(nowT);

  if (!closed) {
    sumV += nowV; if (nowV > peakV) peakV = nowV; nV++;
    if (!isnan(nowT)) { sumT += nowT; if (nowT > peakT) peakT = nowT; nT++; }
  }

  time_t now = nowEpoch();
  if (now && !twilight && now >= sunsetFor(now)) enterTwilight();

  if (!closed && nowV < DUSK_V) {
    if (++lowCount >= DUSK_SAMPLES) { writeRecord(); closed = true; }
  } else if (nowV >= DUSK_V) {
    lowCount = 0;
  }
  if (closed && nowV > DAWN_V) { closed = false; lowCount = 0; lastRecord = millis(); }
}

// ================= raw archive (once, at boot) =================
void archivePrevious(uint32_t prev) {
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
  // merged sessions restart the uptime counter, so prefer the clock for duration
  unsigned long dur = (firstE && lastE) ? (unsigned long)(lastE - firstE)
                    : (lastUp >= firstUp ? lastUp - firstUp : 0);
  char buf[160];
  snprintf(buf, sizeof buf, "%lu,%lu,%lu,%lld,%lld,%.2f,%.1f,%.1f,%lu\n",
           (unsigned long)prev, (unsigned long)rows, dur,
           firstE, lastE, vPeak, tMin < 999 ? tMin : NAN, tMax > -999 ? tMax : NAN, (unsigned long)maxVis);
  appendLine(SUM, SUM_HDR, buf);
  char dst[40];
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

void prune() {   // raw detail only, oldest first, only past the limits
  auto files = listDir("/archive", "sess-");
  size_t k = 0;
  while (k < files.size() && (files.size() - k > KEEP_SESSIONS || fsFullPct() > FS_MAX_PCT)) {
    LittleFS.remove("/archive/" + files[k]);
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

void handleNow() {
  time_t now = nowEpoch();
  char buf[360];
  snprintf(buf, sizeof buf,
           "{\"panel\":\"%s\",\"epoch\":%lld,\"sunset\":%lld,\"twilight\":%s,\"closed\":%s,"
           "\"v\":%.2f,\"t\":%s,\"band\":\"%s\",\"uptime\":%lu,\"visitors\":%u,\"exhibition\":%s}",
           PANEL_ID, (long long)now, (long long)(now ? sunsetFor(now) : 0),
           twilight ? "true" : "false", closed ? "true" : "false",
           nowV, isnan(nowT) ? "null" : String(nowT, 1).c_str(),
           band >= 0 ? BANDS[band].name : "unknown",
           (unsigned long)(millis() / 1000), (unsigned)WiFi.softAPgetStationNum(),
           now && inExhibition(now) ? "true" : "false");
  server.send(200, "application/json", buf);
}

void handleArtList() {
  time_t now = nowEpoch();
  String j = "{\"panel\":\"" + String(PANEL_ID) + "\",\"rules\":\"" + RULES_VERSION + "\"";
  j += ",\"lat\":" + String(LAT, 4) + ",\"lng\":" + String(LNG, 4);
  j += ",\"start\":\"" + (exStart ? dateStr(exStart) : String("")) + "\"";
  j += ",\"end\":\"" + (exEnd ? dateStr(exEnd - 1) : String("")) + "\"";
  j += ",\"today\":\"" + (now ? dateStr(now) : String("")) + "\"";
  j += ",\"epoch\":" + String((long long)now) + ",\"sunset\":" + String((long long)(now ? sunsetFor(now) : 0));
  j += ",\"days\":[";
  auto files = listDir("/art", "2");
  for (size_t i = 0; i < files.size(); i++) {
    if (i) j += ',';
    j += "\"" + files[i].substring(0, files[i].length() - 4) + "\"";
  }
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
  j += ",\"rtc\":" + String(rtcOk ? "true" : "false");
  j += ",\"start\":\"" + (exStart ? dateStr(exStart) : String("")) + "\"";
  j += ",\"end\":\"" + (exEnd ? dateStr(exEnd - 1) : String("")) + "\"";
  j += ",\"sunset\":" + String((long long)(now ? sunsetFor(now) : 0));
  j += ",\"session\":" + String(session) + ",\"uptime\":" + String(millis() / 1000);
  j += ",\"volts\":" + String(nowV, 2) + ",\"temp\":" + (isnan(nowT) ? String("null") : String(nowT, 1));
  j += ",\"temp_sensor\":" + String(tempOk ? "true" : "false");
  j += ",\"art_days\":" + String(listDir("/art", "2").size());
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

void handleAdminExport() {
  if (!checkKey()) return;
  time_t now = nowEpoch();
  String name = String(PANEL_ID) + "_" + (now ? dateStr(now) : String("undated")) + ".csv";
  server.sendHeader("Content-Disposition", "attachment; filename=\"" + name + "\"");
  server.setContentLength(CONTENT_LENGTH_UNKNOWN);
  server.send(200, "text/csv", "");
  String buf;
  buf += "# panel=" + String(PANEL_ID) + " firmware=" + FW_VERSION + " rules=" + RULES_VERSION;
  buf += " lat=" + String(LAT, 4) + " lng=" + String(LNG, 4);
  buf += " exhibition=" + (exStart ? dateStr(exStart) : String("-")) + ".." + (exEnd ? dateStr(exEnd - 1) : String("-"));
  buf += " exported=" + String((long long)now) + "\n";
  buf += "session,uptime_s,epoch,volts,volts_peak,temp_c,temp_peak,visitors\n";
  for (auto& n : listDir("/archive", "sess-"))
    streamRaw("/archive/" + n, (uint32_t)n.substring(5, 10).toInt(), buf);
  streamRaw(CUR, session, buf);
  if (buf.length()) server.sendContent(buf);
  server.sendContent("");   // end of chunked response
}

// ================= setup / loop =================
void setup() {
  Serial.begin(115200);
  setenv("TZ", TZ_INFO, 1);
  tzset();

  LittleFS.begin(true);
  LittleFS.mkdir("/log");
  LittleFS.mkdir("/archive");
  LittleFS.mkdir("/art");
  LittleFS.mkdir("/media");

  prefs.begin("panel", false);
  exStart = prefs.getLong64("exStart", 0);
  exEnd   = prefs.getLong64("exEnd", 0);

#if USE_RTC
  if (PIN_SDA >= 0) Wire.begin(PIN_SDA, PIN_SCL); else Wire.begin();
  rtcOk = rtc.begin();
  if (rtcOk && !rtc.lostPower()) {
    time_t t = (time_t)rtc.now().unixtime();
    if (t > 1700000000) setClock(t, false);
  }
#endif

  analogSetPinAttenuation(PIN_PANEL_ADC, ADC_11db);
#if !BENCH
  dawnGate();                          // radio stays off until the panel can carry it
#endif

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

  ds.begin();
  tempOk = ds.getDeviceCount() > 0;
  if (tempOk) { ds.setWaitForConversion(false); ds.requestTemperatures(); }

  WiFi.mode(WIFI_AP);
  WiFi.softAPConfig(apIP, apIP, IPAddress(255, 255, 255, 0));
  WiFi.softAP(PANEL_ID, strlen(AP_PASS) ? AP_PASS : nullptr);
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
  server.on("/admin/export", handleAdminExport);
  server.onNotFound(handleCaptive);
  server.begin();

  lastSample = lastRecord = millis();
}

void loop() {
  dns.processNextRequest();
  server.handleClient();
  uint32_t now = millis();
  if (now - lastSample >= SAMPLE_MS) sample();
  if (!closed && now - lastRecord >= RECORD_MS) { writeRecord(); lastRecord = now; }
}
