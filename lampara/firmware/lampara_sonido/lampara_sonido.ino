/*
  LÁMPARA REACTIVA AL SONIDO — firmware v1
  José · Taller de Interfaces UAI · 2026

  Qué hace
  - Recibe del computador los colores de los 9 LEDs (la página web analiza el audio).
  - Si el computador deja de mandar, sigue sola con sus propios modos.
  - Recibe comandos de texto: avisos de Claude, cambio de modo, brillo, color.
  - Lee 2 botones touch (TTP223) y reconoce: toque, doble toque, toque largo y los dos juntos.
    Cada gesto se avisa al computador ("E1T", "E2L", "EBB"...) y además tiene una acción local.

  Conexiones (Arduino Uno)
    Tira WS2812B (9 LEDs)   5V -> 5V   ·  GND -> GND  ·  DIN -> D6  (opcional 330 Ω en serie)
    Touch 1 (TTP223)        VCC -> 5V (pin 2 del ICSP o en Y)  ·  GND -> GND  ·  I/O -> D7
    Touch 2 (TTP223)        VCC -> 5V                           ·  GND -> GND  ·  I/O -> D8

  Biblioteca: "Adafruit NeoPixel" (Herramientas -> Administrar bibliotecas).

  Protocolo serie (115200 baud)
    Cuadro de colores:  0xFF + 27 bytes (R,G,B x 9, cada uno 0..254) + 1 byte de control (suma % 251)
    Comandos de texto (terminan en '\n'):
      P            -> responde "LAMPARA v1"
      M<n>         -> modo: 0 apagado · 1 arcoíris · 2 respira · 3 fuego · 4 cálida
                              5 aviso Claude · 6 Claude trabajando · 7 listo
      B<0..255>    -> brillo máximo
      C<r>,<g>,<b> -> color base para "respira" y "cálida"
      A / W / K    -> atajos: aviso (A), trabajando (W), listo (K)
      X            -> quita el aviso y vuelve al modo anterior
*/
#include <Adafruit_NeoPixel.h>

#define LED_PIN   6
#define NUM_LEDS  9
#define TOUCH1    7
#define TOUCH2    8
#define BRILLO_MAX 120        // límite de consumo: 9 LEDs por USB sin pasar ~250 mA

Adafruit_NeoPixel tira(NUM_LEDS, LED_PIN, NEO_GRB + NEO_KHZ800);

// (va arriba para que el IDE de Arduino la conozca antes de generar los prototipos)
struct Boton { uint8_t pin; bool abajo; unsigned long tAbajo, tSuelta; uint8_t toques; bool largoEnviado; };
void revisarBoton(Boton &b, uint8_t n);
void gesto(uint8_t n, char g);

enum Modo { APAGADO, ARCOIRIS, RESPIRA, FUEGO, CALIDA, AVISO, TRABAJANDO, LISTO, STREAM };
const uint8_t MODOS_LOCALES[] = { ARCOIRIS, RESPIRA, FUEGO, CALIDA };
const uint8_t N_LOCALES = sizeof(MODOS_LOCALES);

uint8_t modo = ARCOIRIS, modoPrevio = ARCOIRIS, idxLocal = 0;
uint8_t brillos[] = { 25, 60, BRILLO_MAX }, idxBrillo = 1;
uint8_t baseR = 255, baseG = 140, baseB = 40;
bool    encendida = true;
unsigned long ultimoCuadro = 0, inicioModo = 0, ultimoShow = 0;

// ---------------------------------------------------------------- serie
uint8_t cuadro[28]; int8_t posCuadro = -1;
char linea[24]; uint8_t posLinea = 0;

void ponerModo(uint8_t m) {
  if (m != AVISO && m != TRABAJANDO && m != LISTO && m != STREAM && m != APAGADO) modoPrevio = m;
  if ((m == AVISO || m == TRABAJANDO || m == LISTO) && modo < AVISO) modoPrevio = modo;
  modo = m; inicioModo = millis();
  for (uint8_t i = 0; i < N_LOCALES; i++) if (MODOS_LOCALES[i] == m) idxLocal = i;
}

void comando(char *s) {
  switch (s[0]) {
    case 'P': Serial.println(F("LAMPARA v1")); break;
    case 'M': ponerModo(constrain(atoi(s + 1), 0, 7)); encendida = true; break;
    case 'B': tira.setBrightness(min(atoi(s + 1), BRILLO_MAX)); break;
    case 'C': { int r, g, b; if (sscanf(s + 1, "%d,%d,%d", &r, &g, &b) == 3) { baseR = r; baseG = g; baseB = b; } } break;
    case 'A': ponerModo(AVISO); encendida = true; break;
    case 'W': ponerModo(TRABAJANDO); encendida = true; break;
    case 'K': ponerModo(LISTO); encendida = true; break;
    case 'X': ponerModo(modoPrevio); break;
  }
}

void leerSerie() {
  while (Serial.available()) {
    int c = Serial.read();
    if (posCuadro >= 0) {
      cuadro[posCuadro++] = c;
      if (posCuadro == 28) {
        posCuadro = -1;
        unsigned int suma = 0;
        for (uint8_t i = 0; i < 27; i++) suma += cuadro[i];
        if ((suma % 251) == cuadro[27] && modo != AVISO) {   // el aviso de Claude tiene prioridad
          for (uint8_t i = 0; i < NUM_LEDS; i++) tira.setPixelColor(i, cuadro[i*3], cuadro[i*3+1], cuadro[i*3+2]);
          tira.show();                    // se muestra justo al terminar el cuadro: la línea queda libre
          if (modo != STREAM) { if (modo < AVISO) modoPrevio = modo; modo = STREAM; }
          ultimoCuadro = millis();
        }
      }
      continue;
    }
    if (c == 0xFF) { posCuadro = 0; continue; }
    if (c == '\n' || c == '\r') { if (posLinea) { linea[posLinea] = 0; comando(linea); posLinea = 0; } }
    else if (posLinea < sizeof(linea) - 1) linea[posLinea++] = c;
  }
}

// ---------------------------------------------------------------- botones touch
Boton b1 = { TOUCH1 }, b2 = { TOUCH2 };
bool bothActive = false;
const unsigned long LARGO = 650, DOBLE = 280;

void gesto(uint8_t n, char g);   // declarada abajo

void revisarBoton(Boton &b, uint8_t n) {
  bool ahora = digitalRead(b.pin) == HIGH;          // TTP223: HIGH cuando lo tocas
  unsigned long t = millis();
  if (ahora && !b.abajo) { b.abajo = true; b.tAbajo = t; b.largoEnviado = false; }
  if (!ahora && b.abajo) {
    b.abajo = false; b.tSuelta = t;
    if (!b.largoEnviado && !bothActive) b.toques++;
  }
  if (b.abajo && !b.largoEnviado && !bothActive && t - b.tAbajo > LARGO) { b.largoEnviado = true; b.toques = 0; gesto(n, 'L'); }
  if (!b.abajo && b.toques && t - b.tSuelta > DOBLE) { gesto(n, b.toques >= 2 ? 'D' : 'T'); b.toques = 0; }
}

void revisarBotones() {
  if (b1.abajo && b2.abajo && !bothActive && (millis() - max(b1.tAbajo, b2.tAbajo) > 60)) {
    bothActive = true; b1.toques = b2.toques = 0; gesto(0, 'B');
  }
  revisarBoton(b1, 1); revisarBoton(b2, 2);
  if (!b1.abajo && !b2.abajo) bothActive = false;
}

bool computadorActivo() { return modo == STREAM && millis() - ultimoCuadro < 1500; }

void gesto(uint8_t n, char g) {
  // 1) siempre se avisa al computador: E1T, E1D, E1L, E2T, E2D, E2L, EBB
  Serial.print('E'); Serial.print(n == 0 ? 'B' : char('0' + n)); Serial.println(g == 'B' ? 'B' : g);
  // 2) un aviso de Claude se apaga con cualquier toque
  if (modo == AVISO || modo == LISTO) { ponerModo(modoPrevio); return; }
  // 3) si la página está controlando, ella decide qué hace cada gesto
  if (computadorActivo()) return;
  // 4) acciones propias (sin computador)
  if (n == 1 && g == 'T') { encendida = true; idxLocal = (idxLocal + 1) % N_LOCALES; ponerModo(MODOS_LOCALES[idxLocal]); }
  if (n == 1 && g == 'D') { encendida = true; idxLocal = (idxLocal + N_LOCALES - 1) % N_LOCALES; ponerModo(MODOS_LOCALES[idxLocal]); }
  if (n == 1 && g == 'L') { idxBrillo = (idxBrillo + 1) % 3; tira.setBrightness(brillos[idxBrillo]); }
  if (n == 2 && g == 'T') { encendida = !encendida; }
  if (n == 2 && g == 'D') { uint32_t c = tira.ColorHSV(random(65536), 200, 255); baseR = c >> 16; baseG = c >> 8; baseB = c; }
  if (n == 2 && g == 'L') { ponerModo(AVISO); }                 // probar el aviso
  if (n == 0)             { encendida = true; ponerModo(ARCOIRIS); }
}

// ---------------------------------------------------------------- efectos propios
uint8_t calor[NUM_LEDS];

void dibujar() {
  unsigned long t = millis(), dt = t - inicioModo;
  if (!encendida || modo == APAGADO) { tira.clear(); return; }
  switch (modo) {
    case ARCOIRIS:
      for (uint8_t i = 0; i < NUM_LEDS; i++) tira.setPixelColor(i, tira.gamma32(tira.ColorHSV(t * 12 + i * 7000)));
      break;
    case RESPIRA: {
      float k = 0.15 + 0.85 * (0.5 - 0.5 * cos(t / 900.0));
      for (uint8_t i = 0; i < NUM_LEDS; i++) tira.setPixelColor(i, baseR * k, baseG * k, baseB * k);
    } break;
    case CALIDA:
      for (uint8_t i = 0; i < NUM_LEDS; i++) tira.setPixelColor(i, 255, 120 + i * 4, 30 + i * 2);
      break;
    case FUEGO:
      for (uint8_t i = 0; i < NUM_LEDS; i++) calor[i] = max(0, calor[i] - random(0, 25));
      for (int8_t i = NUM_LEDS - 1; i >= 2; i--) calor[i] = (calor[i - 1] + calor[i - 2] * 2) / 3;
      if (random(255) < 140) calor[random(3)] = min(255, calor[0] + random(120, 255));
      for (uint8_t i = 0; i < NUM_LEDS; i++) {
        uint8_t h = calor[i];
        tira.setPixelColor(i, min(255, h * 2), h > 128 ? (h - 128) * 2 : h / 4, h > 220 ? (h - 220) * 4 : 0);
      }
      break;
    case AVISO: {                     // Claude necesita tu respuesta: ámbar que respira + chispa arriba
      float k = 0.25 + 0.75 * (0.5 - 0.5 * cos(t / 260.0));
      for (uint8_t i = 0; i < NUM_LEDS; i++) tira.setPixelColor(i, 255 * k, 110 * k, 0);
      if ((t / 400) % 2) tira.setPixelColor(NUM_LEDS - 1, 255, 255, 255);
    } break;
    case TRABAJANDO: {                // Claude trabajando: punto azul que sube y baja
      int p = (t / 110) % (2 * NUM_LEDS - 2); if (p >= NUM_LEDS) p = 2 * NUM_LEDS - 2 - p;
      for (uint8_t i = 0; i < NUM_LEDS; i++) { int d = abs(i - p); tira.setPixelColor(i, 0, d == 0 ? 90 : (d == 1 ? 25 : 0), d == 0 ? 255 : (d == 1 ? 70 : 6)); }
    } break;
    case LISTO: {                     // listo: la torre se llena de verde y vuelve al modo anterior
      uint8_t n = min((unsigned long)NUM_LEDS, dt / 90 + 1);
      for (uint8_t i = 0; i < NUM_LEDS; i++) tira.setPixelColor(i, 0, i < n ? 255 : 0, i < n ? 70 : 0);
      if (dt > 2600) ponerModo(modoPrevio);
    } break;
  }
}

// ---------------------------------------------------------------- setup / loop
void setup() {
  Serial.begin(115200);
  pinMode(TOUCH1, INPUT); pinMode(TOUCH2, INPUT);
  tira.begin(); tira.setBrightness(brillos[idxBrillo]);
  for (uint8_t i = 0; i < NUM_LEDS; i++) { tira.setPixelColor(i, 0, 60, 255); tira.show(); delay(40); }   // saludo
  ponerModo(ARCOIRIS);
  Serial.println(F("LAMPARA v1"));
}

void loop() {
  leerSerie();
  revisarBotones();
  if (modo == STREAM) {
    if (millis() - ultimoCuadro > 1500) ponerModo(modoPrevio);   // la página se cerró: sigue sola
    return;
  }
  if (millis() - ultimoShow >= 20 && posCuadro < 0) {           // ~50 cuadros por segundo
    ultimoShow = millis();
    dibujar();
    tira.show();
  }
}
