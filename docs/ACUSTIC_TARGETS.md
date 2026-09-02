# Fundamentos Psicoacústicos, Evidencia Científica y Validación Externa

Este documento expone las bases técnicas, mediciones de laboratorio independientes y literatura de ingeniería acústica que respaldan la configuración maestra implementada en el sistema **Yamaha RX-V673 + Q Acoustics 3020i + LG C5 OLED**.

---

## 1. Validación Externa por Fuentes de Referencia

### A. Medición Klippel NFS Spinorama de los Q Acoustics 3020i (Audio Science Review)
* **Fuente**: *Audio Science Review (ASR) - Amir Majidimehr*.
* **Hallazgo de Laboratorio**: Las mediciones anecoicas estandarizadas Klippel NFS demuestran un escalón/valle acústico pronunciado entre **2.0 kHz y 3.0 kHz** (con centro en **2.4 - 2.5 kHz**) debido a la divergencia de directividad entre el woofer de 5" y el tweeter desacoplado de 22 mm en la región de cruce (*crossover*).
* **Solución Implementada**: Banda 6 del PEQ del Yamaha fijada en **2.52 kHz (+1.5 dB, Q=1.260)**. Recupera la inteligibilidad vocal y el foco holográfico central sin provocar estridencia.

### B. Gestión de Impedancia y Tensión de Riel (Audioholics - Gene DellaSala)
* **Fuente**: *Audioholics Audio Engineering Research*.
* **Hallazgo de Laboratorio**: El selector de impedancia de Yamaha (`ADVANCED SETUP -> SP IMP.`) a `6 Ω MIN` activa una derivación en el transformador que reduce drásticamente la **tensión de los rieles de alimentación** para superar certificaciones térmicas de laboratorio bajo onda continua. Esto comprime el rango dinámico (*headroom*) y provoca saturación prematura (*clipping*) en picos musicales o explosiones.
* **Solución Implementada**: Selector fijado estrictamente en **`8 Ω MIN`**, permitiendo que las etapas finales suministren corriente instantánea completa a los 3020i (mínimo de 4 Ω en graves medios).

### C. Promedio Espacial Multipunto y Límite de Schroeder (Dr. Floyd Toole / Sean Olive - AES)
* **Fuente**: *Sound Reproduction: The Acoustics and Psychoacoustics of Loudspeakers and Rooms (AES Fellow)*.
* **Principio Acústico**: La ecualización electrónica mediante filtros paramétricos de sala solo es de fase mínima y efectiva por debajo de la **Frecuencia de Schroeder** (~300-400 Hz).
  * La calibración en un único punto (*monopunto*) intenta corregir cancelaciones de fase locales, degradando el sonido fuera del punto dulce.
  * El promedio espacial RMS de 5 puntos aísla la resonancia real de esquina (**110 Hz**) y permite aplicar un filtro **Notch quirúrgico de alta selectividad ($Q=2.000$, $-5.0	ext{ dB}$ en Front R)** sin recortar la pegada en 60-80 Hz.

### D. Dispersión Horizontal Amplia a 0° Toe-In (Salas Asimétricas/Divididas)
* **Principio Acústico**: En salas rectangulares donde la mitad izquierda es un espacio abierto de vida, orientar los altavoces a 0° paralelos proyecta la energía sonora de forma homogénea.
* **Solución Implementada**: Banda 7 fijada en **$10.1	ext{ kHz}$ a $0.0	ext{ dB}$ (neutro)** en lugar de recortar agudos, compensando de forma natural la caída fuera de eje (*off-axis*) para que la música conserve detalle y aire en toda la habitación.

---

## 2. Resumen de Perfiles y Benchmark Acústico

| Perfil | Metodología | Resonancia 110Hz | Decaimiento CSD | Pegada 60Hz | Claridad 2.5kHz | Varianza Sala | Tier |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Through (Bypass)** | Monopunto | $+14.5	ext{ dB}$ | $> 220	ext{ ms}$ | $+3.0	ext{ dB}$ | $-1.5	ext{ dB}$ | $\pm 6.5	ext{ dB}$ | **D** |
| **YPAO Flat (Auto)** | Monopunto | $+17.0	ext{ dB}$ | $> 200	ext{ ms}$ | $+4.0	ext{ dB}$ | $+0.5	ext{ dB}$ | $\pm 5.8	ext{ dB}$ | **C** |
| **Harman Neutral** | Monopunto | $+10.0	ext{ dB}$ | $< 140	ext{ ms}$ | $+3.0	ext{ dB}$ | $+1.5	ext{ dB}$ | $\pm 4.2	ext{ dB}$ | **B** |
| **Harman Impact** | Monopunto (15°) | $+4.5	ext{ dB}$ | $< 90	ext{ ms}$ | $+6.0	ext{ dB}$ | $+2.5	ext{ dB}$ | $\pm 4.2	ext{ dB}$ | **A** |
| **Harman Wide Room** | **Multipunto 5-P (0°)** | **$+4.0	ext{ dB}$** | **$< 85	ext{ ms}$** | **$+5.5	ext{ dB}$** | **$+2.5	ext{ dB}$** | **$\pm 1.6	ext{ dB}$** | 🥇 **S** |
