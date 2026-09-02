# Fundamentos Acústicos y Perfiles de Calibración (*Target Curves*)

Este documento detalla los principios psicoacústicos, investigaciones académicas de referencia y las directrices para seleccionar la curva objetivo adecuada según el tipo de contenido y preferencias de audición.

---

## 1. Fundamentos Psicoacústicos: ¿Por qué una sala NO debe ser plana?

Uno de los errores más comunes en la corrección de sala es intentar forzar una respuesta en frecuencia 100% plana en el punto de escucha mediante ecualización. Las investigaciones del **Dr. Floyd Toole** (*Sound Reproduction: The Acoustics and Psychoacoustics of Loudspeakers and Rooms*) y el equipo de investigación de **Harman International (Sean Olive et al.)** demuestran lo siguiente:

1. **Directividad y Campo Difuso**: Un altavoz anecoicamente neutro (como los Q Acoustics 3020i) irradia sonido de manera uniforme. Sin embargo, las altas frecuencias son absorbidas por cortinas, alfombras y aire mucho más rápido que las bajas frecuencias.
2. **Respuesta en Sala Natural (*In-Room Target*)**: Cuando un altavoz de calidad reproduce en una sala doméstica, la energía acumulada resultante en la posición de escucha debe presentar una **pendiente descendente suave** de entre **$-0.8	ext{ dB}$ y $-1.2	ext{ dB}$ por octava** desde los 1 kHz hasta los 20 kHz.
3. **El Mito de la Respuesta Plana en Agudos**: Forzar agudos planos por ecualización (como intentan algunos modos automáticos) provoca un sonido estridente, metálico y con fatiga auditiva severa a los 20 minutos de escucha.

---

## 2. La Frecuencia de Transición de Schroeder ($f_s$)

En cualquier sala doméstica existe una frontera acústica denominada **Frecuencia de Schroeder**:

$$f_s pprox 2000 \sqrt{rac{T_{60}}{V}}$$

* **Por debajo de $f_s$ (~250 - 300 Hz)**: El comportamiento acústico está dominado por las dimensiones de la sala y los **modos estacionarios (ondas estacionarias/resonancias axiales)**. En esta región, la ecualización paramétrica (PEQ) es **imprescindible y altamente efectiva** para recortar picos de presión.
* **Por encima de $f_s$ (>300 Hz)**: El oído humano discrimina el sonido directo del altavoz frente a las reflexiones tardías. Por encima de 500 Hz solo se debe ecualizar para corregir anomalías intrínsecas del altavoz (como el escalón de cruce del crossover) o aplicar una curva de caída suave general (*House Curve*).

---

## 3. Catálogo de Perfiles Objetivo y Guía de Elección

El sistema incluye **5 perfiles objetivo precalculados** seleccionables mediante el parámetro `--target`:

| Perfil (`--target`) | Filosofía Acústica | Características Típicas | Contenido Ideal / Uso Recomendado |
| :--- | :--- | :--- | :--- |
| **`harman_neutral`** *(Por Defecto)* | **Harman Reference Target** | Realce de graves $+2.0	ext{ dB}$ (<120 Hz) + Caída suave de $-0.8	ext{ dB}$/oct (>6 kHz). | **Todo uso (Hi-Fi, Pop, Rock, Cine estándar, Series)**. El perfil más polivalente y equilibrado. |
| **`audiophile_flat`** | **Diffuse-Field Linear** | Graves neutros $+0.0	ext{ dB}$ + Respuesta lineal estricta hasta 10 kHz. | **Música Clásica Orquestal, Jazz acústico, Mastering, Salas tratadas**. Máxima pureza timbral. |
| **`cinema_impact`** | **Blockbuster Home Cinema** | Realce de subgraves $+3.5	ext{ dB}$ (<100 Hz) + Atenuación de agudos $-1.2	ext{ dB}$/oct (>5 kHz). | **Cine de Acción, Ciencia Ficción, Videojuegos, Pistas DTS/Atmos**. Graves profundos y cero aspereza a alto SPL. |
| **`vocal_clarity`** | **Speech & Dialogue Focus** | Graves secos recortados + Realce de inteligibilidad $+1.5	ext{ dB}$ en 2.8 kHz. | **Podcasts, YouTube hablado, Vlogs, Documentales, Cine nocturno**. Diálogos nítidos a bajo volumen. |
| **`warm_music`** | **British Warmth / Analogue** | Graves redondos $+2.5	ext{ dB}$ (<150 Hz) + Caída relajada $-1.5	ext{ dB}$/oct (>4 kHz). | **Vinilos, Rock de los 70/80, Soul, Jazz de club, Sesiones de fondo prolongadas**. |

---

## 4. Fuentes y Bibliografía Técnica

1. **Toole, Floyd E.** (2017). *Sound Reproduction: The Acoustics and Psychoacoustics of Loudspeakers and Rooms (3rd Edition)*. Routledge.
2. **Olive, Sean E., Welti, Todd, & McMullin, Elisabeth** (2013). *Listener Preferences for In-Room Loudspeaker and Headphone Target Responses*. Audio Engineering Society (AES) Convention Paper 8994.
3. **Klippel, Wolfgang** (2006). *Tutorial: Loudspeaker Nonlinearities—Causes, Characteristics, Symptoms*. Journal of the Audio Engineering Society.
4. **Farina, Angelo** (2000). *Simultaneous Measurement of Impulse Response and Distortion with a Swept-Sine Technique*. Audio Engineering Society (AES) Convention 108.
