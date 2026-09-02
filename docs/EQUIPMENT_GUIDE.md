# Guía de Equipamiento, Conectividad y Hoja de Ruta de Hardware

Este documento detalla los componentes del sistema actual, su acoplamiento electroacústico y las opciones de mejora de hardware a futuro.

---

## 1. Cadena de Equipamiento Actual

| Componente | Modelo | Rol en la Cadena | Configuración Activa |
| :--- | :--- | :--- | :--- |
| **Fuente / Pantalla** | **LG C5 OLED (2025)** | Reproductor AV & HDMI ARC | *Pass Through (Paso directo)*, Bitstream, eARC Off (ARC nativo). |
| **Receptor AV** | **Yamaha RX-V673** | Procesador DSP & Amplificador | *8 Ω MIN*, Pure Direct Off, Dynamic Range MAX, PEQ Manual. |
| **Altavoces** | **Q Acoustics 3020i** | Transductores Estéreo 2.0 | Woofer 125 mm, Tweeter 22 mm desacoplado, 0° Toe-In (Paralelo). |
| **Micrófono Actual** | **Yamaha YPAO Stock (3.5mm)** | Captura de Barridos Acústicos | Cápsula omnidireccional a 90° (orientada al techo). |

---

## 2. Análisis del Micrófono YPAO de Serie vs Micrófono Calibrado

### Estado Actual: Micrófono YPAO de Yamaha (Incluido)
* **Precisión en Graves (20 Hz - 400 Hz)**: **Excelente ($\pm 0.5	ext{ dB}$)**. Las cápsulas electret son omnidireccionales y su respuesta en bajas frecuencias es plana y altamente precisa para detectar modos de sala y frecuencias de resonancia de esquina (110 Hz).
* **Limitación en Agudos (>2 kHz)**: No dispone de un archivo de calibración individual de fábrica para compensar tolerancias de manufactura en agudos extremos.
* **Solución Aplicada**: El sistema utiliza la **compensación anecoica Klippel NFS de laboratorio (Audio Science Review)** para corregir los 3020i en agudos/crossover y el micro YPAO para los modos de sala.

---

## 3. Hoja de Ruta de Mejora a Futuro (Micrófonos Calibrados de Precisión)

Para usuarios que deseen llevar la calibración a un estándar de laboratorio de $20	ext{ Hz}$ a $20	ext{ kHz}$ en toda la banda audible:

```
+-----------------------------------------------------------------------------------+
| OPCIONES DE MEJORA DE MICRÓFONO CALIBRADO A FUTURO                               |
+----------------------+--------------------+-----------------+---------------------+
| Modelo               | Tipo de Conexión   | Rango Calibrado | Archivo de Cal (.cal)
+----------------------+--------------------+-----------------+---------------------+
| 1. miniDSP UMIK-1    | USB Directo        | 10 Hz - 20 kHz  | 90° Diffuse Field   |
| 2. Dayton UMM-6      | USB Directo        | 18 Hz - 20 kHz  | Serial-matched 90°  |
| 3. Dayton iMM-6C     | USB-C              | 20 Hz - 20 kHz  | Calibración ind.    |
+----------------------+--------------------+-----------------+---------------------+
```

### Cómo ejecutar una medición con micrófono calibrado a futuro:
```bash
# 1. Conectar el micrófono USB (UMIK-1 / UMM-6)
# 2. Descargar el archivo .cal correspondiente a su número de serie
# 3. Lanzar la calibración acústica con el archivo de compensación:
python3 scripts/01_measure_sweep.py --mic umik1 --cal-file /ruta/a/umik1_90deg.cal
python3 scripts/spatial_average.py --compute-average
python3 scripts/auto_calibrate.py --target harman_wide_room --multipoint --export-pdf
```

---

## 4. Segunda Hoja de Ruta de Mejora: Subwoofer Activo (Corte a 80 Hz)
* **Hardware Recomendado**: *Q Acoustics 3060S* o *SVS SB-1000 Pro* conectado a la salida `SUBWOOFER OUT` del Yamaha.
* **Beneficio**: Alivia a los 3020i de reproducir por debajo de 80 Hz, reduciendo la distorsión por intermodulación en medios y extendiendo la respuesta hasta los 20 Hz reales.
