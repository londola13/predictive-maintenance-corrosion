/*
 * Corrosion Monitor — ESP32 + HX711 + DS18B20
 * Mode : loop labo (secteur, pas de deep sleep)
 * Periode : 30 s
 *
 * Run actif : Run #18 RTF — HCl brut, PHASE CONTROLEE 30C, 3e run VITRINE (protocole acide corrige)
 * run_id    : e80a5a55-8d5f-4a40-9deb-546542b1bcf4
 *
 * MAJ Wi-Fi (OTA) ACTIVEE : apres ce 1er flash USB, les mises a jour suivantes
 *   se font SANS cable. Arduino IDE > Outils > Port > Ports reseau > corrosion-esp32.
 *   Mot de passe OTA : voir #define OTA_PASSWORD ci-dessous.
 *
 * MONTAGE : 2 fils + shunt + R_lift (version v3)
 *   Topologie : VCC -> R_shunt -> fil ER -> R_lift -> GND
 *   R_lift remonte le common mode HX711 a ~1.7V (necessaire pour le PGA)
 *   I = (VCC - V_wire) / (R_shunt + R_lift) ~ 1.75 mA
 *   R_fil = V_sense / I (loi d'Ohm)
 *
 * Brochage :
 *   HX711 DOUT -> GPIO 21
 *   HX711 SCK  -> GPIO 22
 *   DS18B20 DQ -> GPIO 19  (pull-up 4.7 kOhm vers 3.3V obligatoire)
 *   HX711 A+   -> entre R_shunt et le fil
 *   HX711 A-   -> entre le fil et R_lift
 *   ESP32 3V3  -> R_shunt 970 -> [fil] -> R_lift 970 -> GND
 */

#include "HX711.h"
#include <OneWire.h>
#include <DallasTemperature.h>
#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <ArduinoOTA.h>   // mise a jour du firmware par Wi-Fi (OTA)
#include <time.h>
#include "secrets.h"

#define ASSET_ID   "sonde-01"
#define TABLE_NAME "cr_measurements"
#define RUN_ID     "e80a5a55-8d5f-4a40-9deb-546542b1bcf4"

// ── OTA (televersement Wi-Fi) ─────────────────────────────────────────────────
// Apres ce 1er flash USB, l'ESP32 apparait dans Arduino IDE :
//   Outils > Port > Ports reseau  ->  corrosion-esp32 (a.b.c.d)
// Selectionner ce port reseau et televerser SANS cable. Mot de passe demande ci-dessous.
#define OTA_HOSTNAME  "corrosion-esp32"
#define OTA_PASSWORD  "corrosion2026"

#define HX711_DOUT_PIN   21
#define HX711_SCK_PIN    22
#define ONE_WIRE_BUS     19

// ========== MONTAGE 2 FILS + SHUNT + R_LIFT ==========
const double VCC_VOLTS    = 3.45;      // tension ESP32 3V3 mesuree au multimetre
const double R_SHUNT_OHM  = 10000.0;   // R_shunt 10k : repousse le plafond ADC de 12.9 -> ~127 ohm affiches
const double R_LIFT_OHM   = 10000.0;   // R_lift 10k (courant /10 ; common mode inchange car ratio 0.5)
const int    HX711_GAIN   = 64;        // gain 64 -> plage +/-40 mV
const double V_REF_HX711  = 4.2987;    // AVDD du HX711 (mesurer au multimetre)

// Calibration empirique du HX711 (compense l'ecart systematique du module + V_REF).
// NOUVEAU module HX711 (remplace apres panne ESP32) : echelle differente de l'ancien.
//   Calibre sur R_test=8.2 Ohm reel -> Rx_brut=25.8 -> 8.2/25.8 = 0.32
//   (l'ancien module donnait 33.7 ; ne plus utiliser cette valeur avec ce module)
const double HX711_CAL_FACTOR = 0.32;

// Longueur immergee / longueur totale entre B et A
const double L_IMMERGE_FRAC = 180.0 / 200.0;  // 180 cm immerges sur 200 cm totaux (Run #11)

#define MEASURE_INTERVAL_MS  30000UL
#define MESURES_PAR_CYCLE    10
#define WIFI_TIMEOUT_MS      15000
#define NTP_TIMEOUT_MS       10000
#define POST_RETRY_MAX       3

const double DT_HOURS = (MEASURE_INTERVAL_MS / 1000.0) / 3600.0;

HX711 scale;
OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature sensors(&oneWire);

static double last_Rx       = 0.0;
static bool   first_measure = true;
static double last_v_sense  = 0.0;
static double last_I_A      = 0.0;

bool   init_wifi();
void   ensure_wifi();
void   setup_ota();
void   attendre_avec_ota(unsigned long duree_ms);
bool   init_ntp();
time_t get_epoch();
double lire_resistance();
float  lire_temperature();
bool   envoyer_supabase(time_t ts, double rx, float temp, double delta_r_h, double delta_r_imm_h);

void setup() {
  Serial.begin(115200);
  delay(200);
  Serial.println("\n=== Corrosion Monitor — Mode Loop Labo ===");
  Serial.printf("Periode : %lu s | run_id : %s\n", MEASURE_INTERVAL_MS / 1000UL, RUN_ID);

  if (!init_wifi()) { delay(10000); ESP.restart(); }
  setup_ota();
  if (!init_ntp())  { delay(10000); ESP.restart(); }

  Serial.println("Setup OK — demarrage boucle de mesure...\n");

  scale.begin(HX711_DOUT_PIN, HX711_SCK_PIN);
  scale.set_gain(HX711_GAIN);
  sensors.begin();
  sensors.setResolution(12);
}

void loop() {
  unsigned long t_debut = millis();

  ArduinoOTA.handle();   // ecoute une eventuelle MAJ Wi-Fi

  time_t ts = get_epoch();
  if (ts == 0) { attendre_avec_ota(MEASURE_INTERVAL_MS); return; }

  double Rx          = lire_resistance();
  float  temperature = lire_temperature();

  double delta_R_per_h = 0.0;
  if (!first_measure && last_Rx > 1e-9)
    delta_R_per_h = (Rx - last_Rx) / DT_HOURS;

  double delta_R_imm_per_h = delta_R_per_h / L_IMMERGE_FRAC;

  last_Rx = Rx; first_measure = false;

  Serial.printf("[%ld] Rx=%.6f Ohm  T=%.2f C  dR/h=%.8f  dR_imm/h=%.8f Ohm/h\n",
                (long)ts, Rx, temperature, delta_R_per_h, delta_R_imm_per_h);

  bool ok = false;
  for (int i = 1; i <= POST_RETRY_MAX && !ok; i++) {
    ok = envoyer_supabase(ts, Rx, temperature, delta_R_per_h, delta_R_imm_per_h);
    if (!ok) { Serial.printf("  POST echec (%d/%d)\n", i, POST_RETRY_MAX); delay(2000); }
  }
  Serial.println(ok ? "  Supabase OK" : "  Supabase ECHEC");

  unsigned long elapsed = millis() - t_debut;
  if (elapsed < MEASURE_INTERVAL_MS) attendre_avec_ota(MEASURE_INTERVAL_MS - elapsed);
}

// Attente non bloquante pour l'OTA : appelle ArduinoOTA.handle() toutes les 50 ms
// afin que l'ESP32 reste televersable par Wi-Fi entre deux mesures.
void attendre_avec_ota(unsigned long duree_ms) {
  unsigned long t0 = millis();
  while (millis() - t0 < duree_ms) {
    ArduinoOTA.handle();
    delay(50);
  }
}

void setup_ota() {
  ArduinoOTA.setHostname(OTA_HOSTNAME);
  ArduinoOTA.setPassword(OTA_PASSWORD);
  ArduinoOTA.onStart([]() { Serial.println("\n[OTA] Debut televersement Wi-Fi..."); });
  ArduinoOTA.onEnd([]()   { Serial.println("\n[OTA] Termine. Redemarrage."); });
  ArduinoOTA.onProgress([](unsigned int p, unsigned int t) {
    Serial.printf("[OTA] %u%%\r", (p * 100) / t);
  });
  ArduinoOTA.onError([](ota_error_t e) { Serial.printf("[OTA] Erreur %u\n", e); });
  ArduinoOTA.begin();
  Serial.printf("OTA pret -> hostname '%s' (Arduino IDE : Port > Ports reseau)\n", OTA_HOSTNAME);
}

bool init_wifi() {
  WiFi.mode(WIFI_STA);
  WiFi.setAutoReconnect(true);
  WiFi.persistent(true);
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

void ensure_wifi() {
  if (WiFi.status() == WL_CONNECTED) return;
  Serial.print("WiFi perdu, reconnexion");
  unsigned long t0 = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - t0 < WIFI_TIMEOUT_MS) {
    delay(300); Serial.print(".");
  }
  Serial.println(WiFi.status() == WL_CONNECTED ? " OK" : " ECHEC");
}

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
  Serial.println(" TIMEOUT"); return false;
}

time_t get_epoch() {
  struct tm ti;
  if (!getLocalTime(&ti)) return 0;
  return mktime(&ti);
}

double lire_resistance() {
  unsigned long t0 = millis();
  while (!scale.is_ready() && millis() - t0 < 3000) delay(10);
  if (!scale.is_ready()) { Serial.println("  [DEBUG] HX711 NOT READY"); return last_Rx; }

  long reading = scale.read_average(MESURES_PAR_CYCLE);
  // Tension aux bornes du fil (entre HX711 A+ et A-)
  double v_sense = (double)reading * V_REF_HX711 / ((double)HX711_GAIN * 8388608.0);

  // Courant reel : I = (VCC - V_test) / (R_shunt + R_lift)
  double I_A = (VCC_VOLTS - v_sense) / (R_SHUNT_OHM + R_LIFT_OHM);
  if (I_A < 1e-6) I_A = VCC_VOLTS / (R_SHUNT_OHM + R_LIFT_OHM);

  // Resistance du fil = V / I (avec calibration empirique HX711)
  double Rx = (v_sense / I_A) * HX711_CAL_FACTOR;

  last_v_sense = v_sense;
  last_I_A = I_A;

  Serial.printf("  [DEBUG] raw=%ld  v_sense=%.6f V (%.3f mV)  I=%.6f A (%.3f mA)  Rx=%.6f Ohm\n",
                reading, v_sense, v_sense * 1000.0, I_A, I_A * 1000.0, Rx);

  if (Rx < 0.001 || Rx > 100.0) return last_Rx;
  return Rx;
}

float lire_temperature() {
  sensors.requestTemperatures();
  delay(760);
  float t = sensors.getTempCByIndex(0);
  if (t == DEVICE_DISCONNECTED_C || t == 85.0f) return -999.0f;
  return t;
}

bool envoyer_supabase(time_t ts, double rx, float temp, double delta_r_h, double delta_r_imm_h) {
  double v_diff = last_v_sense;

  StaticJsonDocument<384> doc;
  doc["asset_id"]          = ASSET_ID;
  doc["run_id"]            = RUN_ID;
  doc["timestamp_s"]       = (long)ts;
  doc["vdiff_v"]           = v_diff;
  doc["rx_ohm"]            = rx;
  doc["temp_c"]            = temp;
  doc["delta_r_per_h"]     = delta_r_h;
  doc["delta_r_imm_per_h"] = delta_r_imm_h;

  String payload;
  serializeJson(doc, payload);

  ensure_wifi();
  if (WiFi.status() != WL_CONNECTED) return false;

  WiFiClientSecure client;
  client.setInsecure();
  HTTPClient http;
  http.begin(client, String(SUPABASE_URL) + "/rest/v1/" + TABLE_NAME);
  http.addHeader("Content-Type",  "application/json");
  http.addHeader("apikey",        SUPABASE_KEY);
  http.addHeader("Authorization", String("Bearer ") + SUPABASE_KEY);
  http.addHeader("Prefer",        "return=minimal");

  int code = http.POST(payload);
  http.end();
  return (code == 201);
}
