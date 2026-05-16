/*
 * Corrosion Monitor — ESP32 + HX711 + DS18B20
 * Mode : loop labo (secteur, pas de deep sleep)
 * Période : 30 s
 *
 * Run actif : Run #1 RTF — baseline sans inhibiteur
 * run_id    : 0621172f-c502-4fa3-8954-f2921f644c19
 *
 * Brochage :
 *   HX711 DOUT  → GPIO 21
 *   HX711 SCK   → GPIO 22
 *   DS18B20 DQ  → GPIO 19  (pull-up 4.7 kΩ vers 3.3V obligatoire)
 *   R_série 100Ω → entre 3.3V et E+ du pont
 *
 * Bibliothèques requises (Arduino Library Manager) :
 *   - HX711 by Bogdan Necula
 *   - DallasTemperature by Miles Burton
 *   - OneWire by Jim Studt
 *   - ArduinoJson by Benoit Blanchon (v6.x)
 *   - WiFiClientSecure (inclus dans ESP32 Arduino core)
 *
 * Calibration V_REF_HX711 :
 *   Mesurer la tension AVDD du module HX711 au multimètre (pin VCC).
 *   Remplacer V_REF_HX711 avec votre mesure avant de flasher.
 */

#include "HX711.h"
#include <OneWire.h>
#include <DallasTemperature.h>
#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <time.h>
#include "secrets.h"   // WIFI_SSID, WIFI_PASSWORD, SUPABASE_URL, SUPABASE_KEY

// ── Identifiant run et sonde ──────────────────────────────────────────────────
#define ASSET_ID   "sonde-01"
#define TABLE_NAME "cr_measurements"
#define RUN_ID     "0621172f-c502-4fa3-8954-f2921f644c19"

// ── Brochage ─────────────────────────────────────────────────────────────────
#define HX711_DOUT_PIN   21
#define HX711_SCK_PIN    22
#define ONE_WIRE_BUS     19

// ── Paramètres pont de Wheatstone ────────────────────────────────────────────
const double R_SERIE  = 100.0;
const double R1       = 10.0;
const double R2       = 10.0;
const double R_REF    = 0.5;
const double V_ALIM   = 3.3;

// Référence ADC = AVDD du HX711 — mesurer au multimètre sur pin VCC du module
const double V_REF_HX711 = 4.2987;  // à ajuster avec votre mesure

const double R_PONT_EQUIV = (R1 + R_REF);
const double V_EXC_EFF    = V_ALIM * R_PONT_EQUIV / (R_SERIE + R_PONT_EQUIV);

// ── Timing ───────────────────────────────────────────────────────────────────
#define MEASURE_INTERVAL_MS  30000UL
#define MESURES_PAR_CYCLE    10
#define WIFI_TIMEOUT_MS      15000
#define NTP_TIMEOUT_MS       10000
#define POST_RETRY_MAX       3

const double DT_HOURS = (MEASURE_INTERVAL_MS / 1000.0) / 3600.0;

// ── Objets ───────────────────────────────────────────────────────────────────
HX711 scale;
OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature sensors(&oneWire);

// ── État global ───────────────────────────────────────────────────────────────
static double last_Rx       = 0.0;
static bool   first_measure = true;

// ── Prototypes ───────────────────────────────────────────────────────────────
bool   init_wifi();
bool   init_ntp();
time_t get_epoch();
double lire_resistance();
float  lire_temperature();
bool   envoyer_supabase(time_t ts, double rx, float temp, double delta_r_h);

// =============================================================================
void setup() {
  Serial.begin(115200);
  delay(200);
  Serial.println("\n=== Corrosion Monitor — Mode Loop Labo ===");
  Serial.printf("Periode : %lu s | run_id : %s\n", MEASURE_INTERVAL_MS / 1000UL, RUN_ID);

  if (!init_wifi()) {
    Serial.println("FATAL : Wi-Fi indisponible. Reboot dans 10s.");
    delay(10000);
    ESP.restart();
  }

  if (!init_ntp()) {
    Serial.println("FATAL : NTP indisponible. Reboot dans 10s.");
    delay(10000);
    ESP.restart();
  }

  Serial.println("Setup OK — demarrage boucle de mesure...\n");

  scale.begin(HX711_DOUT_PIN, HX711_SCK_PIN);
  scale.set_gain(128);
  sensors.begin();
  sensors.setResolution(12);
}

// =============================================================================
void loop() {
  unsigned long t_debut = millis();

  time_t ts = get_epoch();
  if (ts == 0) {
    Serial.println("WARN : epoch=0, mesure ignoree.");
    delay(MEASURE_INTERVAL_MS);
    return;
  }

  double Rx         = lire_resistance();
  float  temperature = lire_temperature();

  double delta_R_per_h = 0.0;
  if (!first_measure && last_Rx > 1e-9)
    delta_R_per_h = (Rx - last_Rx) / DT_HOURS;

  last_Rx       = Rx;
  first_measure = false;

  Serial.printf("[%ld] Rx=%.6f Ohm  T=%.2f C  dR/h=%.8f Ohm/h\n",
                (long)ts, Rx, temperature, delta_R_per_h);

  bool ok = false;
  for (int attempt = 1; attempt <= POST_RETRY_MAX && !ok; attempt++) {
    ok = envoyer_supabase(ts, Rx, temperature, delta_R_per_h);
    if (!ok) {
      Serial.printf("  POST echec (tentative %d/%d)\n", attempt, POST_RETRY_MAX);
      delay(2000);
    }
  }
  Serial.println(ok ? "  Supabase OK" : "  Supabase ECHEC apres 3 tentatives");

  unsigned long elapsed = millis() - t_debut;
  if (elapsed < MEASURE_INTERVAL_MS)
    delay(MEASURE_INTERVAL_MS - elapsed);
}

// =============================================================================
bool init_wifi() {
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print("Wi-Fi");
  unsigned long t0 = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - t0 < WIFI_TIMEOUT_MS) {
    delay(300); Serial.print(".");
  }
  Serial.println();
  if (WiFi.status() == WL_CONNECTED) {
    Serial.printf("IP : %s\n", WiFi.localIP().toString().c_str());
    return true;
  }
  return false;
}

// =============================================================================
bool init_ntp() {
  configTime(0, 0, "pool.ntp.org", "time.nist.gov");
  Serial.print("NTP sync");
  unsigned long t0 = millis();
  struct tm ti;
  while (millis() - t0 < NTP_TIMEOUT_MS) {
    if (getLocalTime(&ti)) {
      Serial.println(" OK");
      Serial.printf("Heure : %04d-%02d-%02d %02d:%02d:%02d UTC\n",
                    ti.tm_year+1900, ti.tm_mon+1, ti.tm_mday,
                    ti.tm_hour, ti.tm_min, ti.tm_sec);
      return true;
    }
    delay(500); Serial.print(".");
  }
  Serial.println(" TIMEOUT");
  return false;
}

// =============================================================================
time_t get_epoch() {
  struct tm ti;
  if (!getLocalTime(&ti)) return 0;
  return mktime(&ti);
}

// =============================================================================
double lire_resistance() {
  unsigned long t0 = millis();
  while (!scale.is_ready() && millis() - t0 < 3000) delay(10);
  if (!scale.is_ready()) {
    Serial.println("WARN : HX711 non pret, renvoi last_Rx");
    return last_Rx;
  }

  long reading = scale.read_average(MESURES_PAR_CYCLE);

  double v_diff_raw = (double)reading * V_REF_HX711 / (128.0 * 8388608.0);
  double ratio_ref  = R_REF / (R1 + R_REF);
  double ratio_rx   = (v_diff_raw / V_EXC_EFF) + ratio_ref;

  if (ratio_rx <= 0.0 || ratio_rx >= 1.0) {
    Serial.printf("WARN : ratio_rx hors domaine (%.4f), renvoi last_Rx\n", ratio_rx);
    return last_Rx;
  }
  return R2 * ratio_rx / (1.0 - ratio_rx);
}

// =============================================================================
float lire_temperature() {
  sensors.requestTemperatures();
  delay(760);
  float t = sensors.getTempCByIndex(0);
  if (t == DEVICE_DISCONNECTED_C || t == 85.0f) {
    Serial.println("WARN : DS18B20 deconnecte ou erreur lecture");
    return -999.0f;
  }
  return t;
}

// =============================================================================
bool envoyer_supabase(time_t ts, double rx, float temp, double delta_r_h) {
  double ratio_rx  = rx / (R2 + rx);
  double ratio_ref = R_REF / (R1 + R_REF);
  double v_diff    = V_EXC_EFF * (ratio_rx - ratio_ref);

  StaticJsonDocument<320> doc;
  doc["asset_id"]      = ASSET_ID;
  doc["run_id"]        = RUN_ID;
  doc["timestamp_s"]   = (long)ts;
  doc["vdiff_v"]       = v_diff;
  doc["rx_ohm"]        = rx;
  doc["temp_c"]        = temp;
  doc["delta_r_per_h"] = delta_r_h;

  String payload;
  serializeJson(doc, payload);

  String url = String(SUPABASE_URL) + "/rest/v1/" + TABLE_NAME;

  WiFiClientSecure client;
  client.setInsecure();

  HTTPClient http;
  http.begin(client, url);
  http.addHeader("Content-Type",  "application/json");
  http.addHeader("apikey",        SUPABASE_KEY);
  http.addHeader("Authorization", String("Bearer ") + SUPABASE_KEY);
  http.addHeader("Prefer",        "return=minimal");

  int code = http.POST(payload);
  http.end();
  return (code == 201);
}
