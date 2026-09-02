# Guía Técnica de Equipamiento y Extensibilidad del Sistema

Este documento recopila las especificaciones de ingeniería de los componentes actuales, el mapeo de las 4 escenas programadas en el receptor y las instrucciones para dar de alta nuevos equipos en la arquitectura de calibración.

---

## 1. Mapeo y Programación de las 4 Escenas (Yamaha RX-V673)

Todas las escenas están enlazadas a la entrada **`AV4` (HDMI ARC desde la LG C5 OLED)**, manteniendo el ecualizador paramétrico manual (`PEQ Manual`) activo y optimizado para cada tipo de contenido:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       YAMAHA RX-V673 - MAPA DE ESCENAS                      │
├─────────┬──────────────────────┬──────────────┬──────────────┬──────────────┤
│ ESCENA  │ NOMBRE               │ MODO DSP     │ ADAPTIVE DRC │ DIALOGUE     │
├─────────┼──────────────────────┼──────────────┼──────────────┼──────────────┤
│ SCENE 1 │ Música Hi-Fi         │ Straight     │ Off          │ Inactivo (0) │
│ SCENE 2 │ Cine Estándar        │ Standard DSP │ Off / MAX    │ +1 (Realce)  │
│ SCENE 3 │ Noche y Voces        │ Drama DSP    │ Auto         │ +2 (Máximo)  │
│ SCENE 4 │ Conciertos / Live    │ Music Video  │ Off / MAX    │ 0 (Inmersión)│
└─────────┴──────────────────────┴──────────────┴──────────────┴──────────────┘
```

---

### Detalle Acústico de Cada Escena:

#### 🎵 SCENE 1: Música Hi-Fi (Audición Estéreo Pura / Lossless)
* **Entrada**: `AV4` (HDMI ARC).
* **Modo de Sonido**: **`Straight`**.
* **Comportamiento**: Apaga todo el motor de simulación espacial Cinema DSP. El audio se reproduce canal por canal con máxima pureza tímbrica y fidelidad a la mezcla de estudio.
* **Dinámica**: `Adaptive DRC: Off` (entrega el 100% de la dinámica original sin comprimir).
* **Uso**: Spotify, Amazon Music HD, YouTube Music, vinilos, sesiones acústicas.

---

#### 🎬 SCENE 2: Cine Estándar (Blockbusters / Series / Inmersión)
* **Entrada**: `AV4` (HDMI ARC).
* **Modo de Sonido**: **`Standard` (Cinema DSP)**.
* **Comportamiento**: Activa el procesamiento espacial optimizado para bandas sonoras cinematográficas (Dolby Digital / DTS) con `3D Cinema DSP: Auto`.
* **Diálogos**: **`Dialogue Level: +1`** (adelanta las voces del canal central virtual para que no queden tapadas por la música y efectos de fondo).
* **Dinámica**: `Dynamic Range: MAX` (explosiones con pegada y graves contundentes).
* **Uso**: Películas en Stremio, Prime Video, Netflix, Disney+, cine de acción y ciencia ficción.

---

#### 🌙 SCENE 3: Noche y Voces (Podcasts / YouTube Hablado / Audición Nocturna)
* **Entrada**: `AV4` (HDMI ARC).
* **Modo de Sonido**: **`Drama` (Cinema DSP)**.
* **Comportamiento**: El algoritmo `Drama` enfoca la energía acústica en el espectro de la voz humana (300 Hz a 4 kHz).
* **Nivelación Dinámica**: **`Adaptive DRC: Auto`** (comprime inteligentemente los picos repentinos de anuncios o explosiones para no despertar a nadie por la noche).
* **Diálogos**: **`Dialogue Level: +2`** (máxima inteligibilidad vocal a volumen bajo: -40 dB a -30 dB).
* **Uso**: Podcasts, vídeos hablados de YouTube, documentales, noticias y películas de madrugada.

---

#### 🏟️ SCENE 4: Conciertos / Live & Deportes (Atmósfera de Estadio / Acústica de Recinto)
* **Entrada**: `AV4` (HDMI ARC).
* **Modo de Sonido**: **`Music Video` (Cinema DSP)**.
* **Comportamiento**: Simula la reverberación temprana y el campo sonoro envolvente de un auditorio / estadio en directo, expandiendo la escena estéreo más allá de los altavoces físicos.
* **Dinámica**: `Adaptive DRC: Off` (rango dinámico libre).
* **Uso**: Festivales en directo (Tomorrowland, Glastonbury), videoclips de directos, retransmisiones deportivas y partidos de fútbol/baloncesto.

---

## 2. Análisis Técnico del Yamaha RX-V673

* **Conversores Digital/Analógico (DAC)**: **Burr-Brown PCM5101 / DSD1791 (192 kHz / 24-bit)** con SNR > 105 dB.
* **Arquitectura PEQ**: 7 filtros paramétricos IIR Biquad por canal con pasos de 0.5 dB y factores Q `1.000`, `1.260`, `1.587`.
* **Impedancia (`ADVANCED SETUP > SP IMP.`)**: Mantener en **`8 Ω MIN`** para que los transistores entreguen el voltaje completo (~45V) a los 6 $\Omega$ de los Q Acoustics 3020i.
* **ECO Mode**: Mantener en **`Off`** para preservar la entrega instantánea de corriente en bombos y transitorios.

---

## 3. Análisis Electroacústico de los Q Acoustics 3020i

* **Recinto**: MDF con refuerzos internos *Point-to-Point (P2P) Bracing* que eliminan coloraciones en los 400–800 Hz.
* **Woofer**: 125 mm (5") con fibras de aramida. Corte natural anecoico $F_3$ en **64 Hz**.
* **Tweeter**: 22 mm desacoplado mecánicamente del bafle frontal mediante junta viscoelástica para evitar modulación cruzada.
* **Crossover**: Cruce en **2.400 Hz** compensado digitalmente por nuestro filtro `2520 Hz (+1.5 dB, Q=1.260)`.

---

## 4. Cómo Dar de Alta Nuevos Equipos en `config/equipment.json`

Para incorporar nuevos altavoces o receptores, basta con añadir una nueva entrada en `config/equipment.json`:

```json
"speakers": {
    "kef_q350": {
        "brand": "KEF",
        "model": "Q350",
        "type": "2-way Uni-Q Coaxial",
        "woofer_size_inch": 6.5,
        "crossover_frequency_hz": 2500.0,
        "spinorama_notch_compensation": null,
        "f3_extension_hz": 51.0,
        "nominal_impedance_ohm": 8.0,
        "minimum_impedance_ohm": 3.7
    }
}
```
