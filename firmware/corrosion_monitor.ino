/*
 * Corrosion Monitor — ESP32 + HX711 + DS18B20
 * Prototype maintenance prédictive — M2 Maintenance Industrielle — ESTL Douala
 *
 * Cycle : wake → mesure (Rx + T) → POST Supabase → deep sleep 10 min
 *
 * Brochage :
 *   HX711 DOUT  → GPIO 21
 *   HX711 SCK   → GPIO 22
 *   DS18B20 DQ  → GPIO 4  (pull-up 4.7 kΩ vers 3.3V obligatoire)
 *   R_série 100Ω → entre 3.3V et E+ du pont
 *
 * Bibliothèques requises (Arduino Library Manager) :
 *   - HX711 by Bogdan Necula
 *   - DallasTemperature by Miles Burton
 *   - OneWire by Jim Studt
 *   - ArduinoJson by Benoit Blanchon (v6.x)
 */

#include "HX711.h"
#include <OneWire.h>
#include <DallasTemperature.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include "secrets.h"   // credentials Wi-Fi + Supabase (non commité)

// ── Identifiant de la sonde ───────────────────────────────────────────────────
#define ASSET_ID    "sonde-01"
#define TABLE_NAME  "cr_measurements"

// ── Brochage ─────────────────────────────────────────────────────────────────
#define HX711_DOUT_PIN   21
#define HX711_SCK_PIN    22
#define ONE_WIRE_BUS      4

// ── Paramètres pont de Wheatstone ───────────────────────────────────────────
const float R_SERIE  = 100.0;
const float R1       = 10.0;
const float R2       = 10.0;
const float R_REF    = 0.5;
const float V_ALIM   = 3.3;
const float R_PONT_EQUIV = (R1 + R_REF);
const float V_EXC_EFF    = V_ALIM * R_PONT_EQUIV / (R_SERIE + R_PONT_EQUIV);

// ── Timing ───────────────────────────────────────────────────────────────────
#define SLEEP_INTERVAL_US  600000000ULL   // 10 minutes
#define MESURES_PAR_CYCLE  10             // moyenne HX711
#define WIFI_TIMEOUT_MS    15000

// ── Persistance RTC (survit au deep sleep) ───────────────────────────────────
RTC_DATA_ATTR static unsigned long mesure_index = 0;
RTC_DATA_ATTR static double        last_Rx      = 0.0;

// ── Objets ───────────────────────────────────────────────────────────────────
HX711 scale;
OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature sensors(&oneWire);

// ── Prototypes ───────────────────────────────────────────────────────────────
double lire_resistance();
float  lire_temperature();
bool   connecter_wifi();
bool   envoyer_supabase(unsigned long ts, double rx, float temp, double delta_r);

// ─────────────────────────────────────────────────────────────────────────────
void setup() {
  Serial.begin(115200);
  delay(150);

  mesure_index++;
  unsigned long timestamp_s = mesure_index * 600UL;

  Serial.printf("\n=== Cycle %lu — t=%lus ===\n", mesure_index, timestamp_s);

  // Mesures
  double Rx          = lire_resistance();
  float  temperature = lire_temperature();

  // ΔR/Δt (Ω/h)
  double delta_R_per_h = 0.0;
  if (last_Rx > 1e-6 && mesure_index > 1)
    delta_R_per_h = (Rx - last_Rx) * 6.0;
  last_Rx = Rx;

  Serial.printf("  Rx=%.6f Ω  T=%.2f°C  ΔR=%.8f Ω/h\n", Rx, temperature, delta_R_per_h);

  // Power down HX711 avant Wi-Fi (réduit le bruit EMI)
  pinMode(HX711_SCK_PIN, OUTPUT);
  digitalWrite(HX711_SCK_PIN, HIGH);
  delayMicroseconds(80);

  // Envoi Supabase
  if (connecter_wifi()) {
    bool ok = envoyer_supabase(timestamp_s, Rx, temperature, delta_R_per_h);
    Serial.println(ok ? "  Supabase OK ✓" : "  Supabase ECHEC ✗");
    WiFi.disconnect(true);
    WiFi.mode(WIFI_OFF);
  } else {
    Serial.println("  Wi-Fi ECHEC — donnée perdue");
  }

  Serial.println("  → deep sleep 600s\n");
  Serial.flush();
  esp_sleep_enable_timer_wakeup(SLEEP_INTERVAL_US);
  esp_deep_sleep_start();
}

void loop() {}

// ─────────────────────────────────────────────────────────────────────────────
double lire_resistance() {
  scale.begin(HX711_DOUT_PIN, HX711_SCK_PIN);
  scale.set_gain(128);

  unsigned long t0 = millis();
  while (!scale.is_ready() && millis() - t0 < 3000) delay(10);
  if (!scale.is_ready()) return last_Rx;

  long reading = scale.read_average(MESURES_PAR_CYCLE);

  double v_diff_raw = (double)reading / 8388608.0 / 128.0 * V_EXC_EFF;
  double ratio_ref  = R_REF / (R1 + R_REF);
  double ratio_rx   = (v_diff_raw / V_EXC_EFF) + ratio_ref;

  if (ratio_rx <= 0.0 || ratio_rx >= 1.0) return last_Rx;
  return R2 * ratio_rx / (1.0 - ratio_rx);
}

// ─────────────────────────────────────────────────────────────────────────────
float lire_temperature() {
  sensors.begin();
  sensors.setResolution(12);
  sensors.requestTemperatures();
  delay(760);

  float t = sensors.getTempCByIndex(0);
  if (t == -127.0f || t == 85.0f) return -999.0f;
  return t;
}

// ─────────────────────────────────────────────────────────────────────────────
bool connecter_wifi() {
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print("  Wi-Fi");

  unsigned long t0 = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - t0 < WIFI_TIMEOUT_MS) {
    delay(300);
    Serial.print(".");
  }
  Serial.println();

  if (WiFi.status() == WL_CONNECTED) {
    Serial.printf("  IP: %s\n", WiFi.localIP().toString().c_str());
    return true;
  }
  return false;
}

// ─────────────────────────────────────────────────────────────────────────────
bool envoyer_supabase(unsigned long ts, double rx, float temp, double delta_r) {
  double ratio_rx = rx  / (R2 + rx);
  double ratio_ref = R_REF / (R1 + R_REF);
  double v_diff   = V_EXC_EFF * (ratio_rx - ratio_ref);

  StaticJsonDocument<256> doc;
  doc["asset_id"]      = ASSET_ID;
  doc["timestamp_s"]   = (long)ts;
  doc["vdiff_v"]       = v_diff;
  doc["rx_ohm"]        = rx;
  doc["temp_c"]        = temp;
  doc["delta_r_per_h"] = delta_r;

  String payload;
  serializeJson(doc, payload);

  String url = String(SUPABASE_URL) + "/rest/v1/" + TABLE_NAME;

  HTTPClient http;
  http.begin(url);
  http.addHeader("Content-Type",  "application/json");
  http.addHeader("apikey",        SUPABASE_KEY);
  http.addHeader("Authorization", String("Bearer ") + SUPABASE_KEY);
  http.addHeader("Prefer",        "return=minimal");

  int code = http.POST(payload);
  http.end();
  return (code == 201);
}
