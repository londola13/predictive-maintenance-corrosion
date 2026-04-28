/*
 * Corrosion Monitor — ESP32 + HX711 + DS18B20
 * Prototype maintenance prédictive de la corrosion (Detar Plus)
 * M2 Maintenance Industrielle — ENSPD Douala
 *
 * Cycle : wake → mesure (Vdiff + R + T) → CSV série → deep sleep 10 min
 * Persistance entre cycles : RTC_DATA_ATTR (mémoire RTC = survit au deep sleep)
 *
 * Brochage :
 *   HX711 DOUT  → GPIO 21
 *   HX711 SCK   → GPIO 22
 *   HX711 VCC   → 3.3V
 *   HX711 GND   → GND
 *   DS18B20 DQ  → GPIO 4  (résistance pull-up 4.7 kΩ vers 3.3V obligatoire)
 *   82Ω série   → entre 3.3V et E+ du pont (limite courant, supprime effet Joule)
 *
 * Format CSV sortie série (115200 baud) :
 *   Timestamp_s;Vdiff_V;Rx_Ohm;Temp_C;DeltaR_Ohm_per_h
 */

#include "HX711.h"
#include <OneWire.h>
#include <DallasTemperature.h>

// ── Brochage ─────────────────────────────────────────────────────────────────
#define HX711_DOUT_PIN   21
#define HX711_SCK_PIN    22
#define ONE_WIRE_BUS      4

// ── Paramètres pont de Wheatstone ───────────────────────────────────────────
// V_EXC_EFFECTIVE = 3.3 × R_pont / (R_serie + R_pont)
// R_pont (bras R1+R_REF) ≈ 10.5 Ω → V_eff ≈ 3.3 × 10.5/92.5 ≈ 0.374 V
// On utilise V_EXC_EFFECTIVE dans la formule pour obtenir Rx absolu correct.
const float R_SERIE  = 100.0;  // résistance série de protection (Ω)
const float R1       = 10.0;   // bras 1 du pont (Ω)
const float R2       = 10.0;   // bras 2 du pont (Ω)
const float R_REF    = 0.5;    // résistance de référence (bras avec fil) (Ω)
const float V_ALIM   = 3.3;    // tension alimentation ESP32 (V)

// Tension effective aux bornes du pont (diviseur résistif série)
// Le bras R1+R_REF ≈ 10.5Ω est en parallèle avec R2+Rx_initial ≈ 10.13Ω → ~5.15Ω
// Pour simplifier : on estime R_pont_equiv ≈ (R1+R_REF) = 10.5Ω (approximation valide
// car Rx << R2, donc les deux bras tirent des courants proches).
const float R_PONT_EQUIV = (R1 + R_REF);  // ≈ 10.5 Ω
const float V_EXC_EFF    = V_ALIM * R_PONT_EQUIV / (R_SERIE + R_PONT_EQUIV);

// ── Timing ───────────────────────────────────────────────────────────────────
#define SLEEP_INTERVAL_US  600000000ULL  // 10 minutes en microsecondes
#define MESURES_PAR_CYCLE  10            // moyenne sur N lectures HX711

// ── Persistance RTC (survit au deep sleep) ───────────────────────────────────
RTC_DATA_ATTR static unsigned long mesure_index  = 0;  // compteur de cycles
RTC_DATA_ATTR static double        last_Rx        = 0.0; // Rx du cycle précédent
RTC_DATA_ATTR static bool          header_envoye  = false;

// ── Objets ───────────────────────────────────────────────────────────────────
HX711 scale;
OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature sensors(&oneWire);

// ── Prototypes ───────────────────────────────────────────────────────────────
double lire_resistance();
float  lire_temperature();

// ─────────────────────────────────────────────────────────────────────────────
void setup() {
  Serial.begin(115200);
  delay(150);  // laisse l'USB se stabiliser après wake

  mesure_index++;
  unsigned long timestamp_s = mesure_index * 600UL;  // 1 mesure = 600 s

  // ── En-tête CSV (première mesure seulement) ───────────────────────────────
  if (!header_envoye) {
    Serial.println("Timestamp_s;Vdiff_V;Rx_Ohm;Temp_C;DeltaR_Ohm_per_h");
    header_envoye = true;
  }

  // ── Lecture résistance (HX711 + pont Wheatstone) ─────────────────────────
  double Rx = lire_resistance();

  // ── Lecture température (DS18B20) ────────────────────────────────────────
  float temperature = lire_temperature();

  // ── Calcul vitesse de corrosion ΔR/Δt (Ω/h) ─────────────────────────────
  double delta_R_per_h = 0.0;
  if (last_Rx > 1e-6 && mesure_index > 1) {
    // dt = 600 s = 1/6 heure
    delta_R_per_h = (Rx - last_Rx) * 6.0;  // (Ω / (1/6 h)) = Ω/h
  }
  last_Rx = Rx;

  // ── Tension différentielle pour le CSV ───────────────────────────────────
  // On recalcule v_diff depuis Rx pour cohérence des colonnes
  // v_diff = V_EXC_EFF × (Rx/(R2+Rx) - R_REF/(R1+R_REF))
  double ratio_rx  = Rx  / (R2   + Rx);
  double ratio_ref = R_REF / (R1 + R_REF);
  double v_diff    = V_EXC_EFF * (ratio_rx - ratio_ref);

  // ── Sortie CSV ────────────────────────────────────────────────────────────
  Serial.print(timestamp_s);    Serial.print(";");
  Serial.print(v_diff,   8);    Serial.print(";");
  Serial.print(Rx,       6);    Serial.print(";");
  Serial.print(temperature, 2); Serial.print(";");
  Serial.println(delta_R_per_h, 8);

  // ── Power down HX711 (SCK HIGH > 60 µs) ──────────────────────────────────
  pinMode(HX711_SCK_PIN, OUTPUT);
  digitalWrite(HX711_SCK_PIN, HIGH);
  delayMicroseconds(80);

  // ── Deep Sleep ────────────────────────────────────────────────────────────
  esp_sleep_enable_timer_wakeup(SLEEP_INTERVAL_US);
  esp_deep_sleep_start();
}

void loop() {
  // Ne s'exécute jamais : deep sleep lancé dans setup()
}

// ─────────────────────────────────────────────────────────────────────────────
double lire_resistance() {
  scale.begin(HX711_DOUT_PIN, HX711_SCK_PIN);
  scale.set_gain(128);

  // Attente HX711 prêt (timeout 3 s)
  unsigned long t0 = millis();
  while (!scale.is_ready() && millis() - t0 < 3000) delay(10);

  if (!scale.is_ready()) return last_Rx;  // fallback sur dernière valeur connue

  long reading = scale.read_average(MESURES_PAR_CYCLE);

  // Conversion code ADC → tension différentielle
  // HX711 gain 128 : 1 LSB = V_EXC_EFF / (2^23) / 128 × gain_interne
  // Le HX711 produit un code 24-bit (signé) : Vdiff = code × V_REF / (gain × 2^23)
  // Avec V_REF interne ≈ V_EXC (ponts de jauge), gain = 128 :
  double v_diff_raw = (double)reading / 8388608.0 / 128.0 * V_EXC_EFF;

  // Calcul Rx depuis la formule du pont de Wheatstone
  // Vdiff = V_EXC × (Rx/(R2+Rx) - R_REF/(R1+R_REF))
  // Rx/(R2+Rx) = Vdiff/V_EXC + R_REF/(R1+R_REF)
  double ratio_ref = R_REF / (R1 + R_REF);
  double ratio_rx  = (v_diff_raw / V_EXC_EFF) + ratio_ref;

  // Protection contre division par zéro ou ratio aberrant
  if (ratio_rx <= 0.0 || ratio_rx >= 1.0) return last_Rx;

  double Rx = R2 * ratio_rx / (1.0 - ratio_rx);
  return Rx;
}

// ─────────────────────────────────────────────────────────────────────────────
float lire_temperature() {
  sensors.begin();
  sensors.setResolution(12);         // 12 bits = 0.0625°C résolution
  sensors.requestTemperatures();
  delay(760);                        // 750 ms max pour conversion 12-bit + marge

  float t = sensors.getTempCByIndex(0);

  // Valeurs d'erreur DS18B20 : -127.0 = non connecté, 85.0 = non initialisé
  if (t == -127.0 || t == 85.0) return -999.0;
  return t;
}
