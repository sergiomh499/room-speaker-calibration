# Protocolo y Guía de Procedimiento de Medición Acústica

Esta guía documenta paso a paso el procedimiento formal para realizar mediciones acústicas, procesar los datos de sala y aplicar corrección paramétrica (PEQ) en el sistema **LG C5 + Yamaha RX-V673 + Q Acoustics 3020i**.

---

## 1. Preparación del Entorno Físico y Acústico

1. **Aislamiento de Ruido de Fondo**:
   * Apaga climatizadores, aires acondicionados, ventiladores o cualquier electrodoméstico que genere zumbido continuo.
   * Cierra puertas y ventanas. El ruido ambiental de la sala debe situarse preferentemente por debajo de **30–35 dB SPL**.
2. **Posicionamiento del Micrófono (YPAO o UMIK-1)**:
   * **Soporte Rígido**: Monta el micrófono en un trípode fotográfico desacoplado. **Nunca** lo sostengas con la mano ni lo apoyes directamente en cojines o en el respaldo del sofá.
   * **Orientación de la Cápsula**: Apuntando verticalmente a **90° hacia el techo**.
   * **Altura**: Exactamente a la altura media de los oídos de una persona sentada en la posición principal de escucha (MLP), típicamente entre **90 cm y 105 cm** respecto al suelo.
3. **Despeje de la Trayectoria Directa**:
   * Asegúrate de que no haya obstáculos (mesas de centro altas, portátiles bloqueando la línea de visión acústica directa) entre los altavoces y el micrófono.

---

## 2. Conexión y Flujo de Señal

```
[ Laptop / PC ] ──(HDMI)──> [ Yamaha RX-V673 (Entrada V-AUX Frontal o HDMI Posterior) ]
      ▲                                   │
      │                                   ▼
[ Micrófono (Jack / USB) ]     [ Q Acoustics 3020i (L / R) ]
```

1. Conecta el cable HDMI del portátil a la entrada frontal **`V-AUX`** del Yamaha RX-V673.
2. Conecta el micrófono a la entrada de micro frontal o al puerto de captura del sistema.
3. Ajusta el volumen del receptor Yamaha a tu nivel de audición habitual (**entre -28 dB y -20 dB**).

---

## 3. Ejecución Automatizada del Barrido de Medición

El script genera una señal de excitación de **barrido senoidal logarítmico de Farina (15 Hz a 22.000 Hz, 5 segundos)** con silencios de seguridad antes y después:

```bash
cd /home/sergio/yamaha-qacoustics-calibration

# Ejecutar el barrido de medición en ambos canales:
python3 scripts/01_measure_sweep.py
```

### Proceso Interno del Algoritmo:
1. Conmuta el receptor automáticamente a **`V-AUX`** y modo **`Straight On`** vía comandos HTTP YNC XML.
2. Reproduce el barrido en el canal izquierdo mientras graba la respuesta en tiempo real.
3. Repite el proceso para el canal derecho.
4. Aplica **deconvolución por filtro inverso**, aislando la respuesta al impulso lineal pura de las reflexiones tardías y armónicos de distorsión.
5. Calcula la transformada rápida de Fourier (**FFT de 65.536 puntos**) y aplica suavizado fraccional psicoacústico de **1/24 de octava**.
6. Restaura el receptor a la entrada **`AV4` (HDMI ARC TV)**.
7. Guarda los datos limpios en `data/medicion_real_calibracion.npz`.

---

## 4. Cálculo y Optimización de Filtros PEQ

Ejecuta el motor de calibración seleccionando la curva de destino deseada:

```bash
# Para audición equilibrada y música/cine general (Recomendado):
python3 scripts/auto_calibrate.py --target harman_neutral --export-pdf

# Para cine con graves contundentes e impacto:
python3 scripts/auto_calibrate.py --target cinema_impact --export-pdf

# Para máxima claridad en diálogos y podcasts:
python3 scripts/auto_calibrate.py --target vocal_clarity --export-pdf
```

---

## 5. Introducción de Valores en el Yamaha RX-V673

1. Enciende la televisión y pulsa **`ON SCREEN`** (o `SETUP`) en el mando del Yamaha.
2. Navega a **`Speaker`** $ightarrow$ **`Manual Setup`** $ightarrow$ **`Equalizer`**.
3. Cambia **`PEQ Select`** a **`Manual`**.
4. Entra en **`Front L`** e introduce las 7 frecuencias, factores Q y ganancias generadas por el script.
5. Entra en **`Front R`** e introduce las 7 bandas correspondientes al canal derecho.
6. Pulsa **`RETURN`** para asegurar que el ajuste quede guardado.
