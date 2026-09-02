# Protocolo de Medición y Calibración Acústica de Sala

Este documento detalla el procedimiento técnico para capturar mediciones repetibles con rigor de ingeniería utilizando señales de barrido senoidal de Farina y el micrófono de calibración.

---

## 1. Preparación del Entorno Físico

1. **Aislamiento Acústico**:
   * Cerrar puertas y ventanas.
   * Apagar aire acondicionado, ventiladores y electrodomésticos ruidosos (el ruido de fondo debe situarse por debajo de 35 dB SPL).
2. **Ubicación de Altavoces**:
   * Separar los altavoces al menos **20 cm de la pared trasera**.
   * Orientar (*toe-in*) los altavoces **10° a 15° hacia el punto de escucha central** (cruzando los ejes acústicos ligeramente detrás de la cabeza).
3. **Montaje del Micrófono**:
   * Montar el micrófono en un **trípode fotográfico**.
   * Cúpula apuntando estrictamente a **90° hacia el techo**.
   * Altura fijada a la altura media de los oídos sentado (**95 cm a 105 cm del suelo**).
   * **Nunca sostener el micrófono con la mano ni apoyarlo en cojines o respaldo del sofá**.

---

## 2. Protocolo de Barrido Senoidal de Farina

La técnica de Farina emite un barrido logarítmico senoidal continuo de 15 Hz a 22 kHz:
$$x(t) = \sin\left( \frac{2\pi f_1 T}{\ln(f_2/f_1)} \left( \left(\frac{f_2}{f_1}\right)^{t/T} - 1 \right) \right)$$
* Permite separar la **respuesta lineal al impulso** de las distorsiones armónicas no lineales ($H_2, H_3, H_4$).

### Ejecución de Medición:
```bash
cd /home/sergio/room-speaker-calibration
# Ejecutar barrido y generar gráficas:
python3 scripts/01_measure_sweep.py
python3 scripts/02_plot_responses.py
```

---

## 3. Protocolo de Captura Multimodo (`capture_mode.py`)

Para evaluar distintos modos de ecualización de forma sistemática:
1. Poner el receptor en el modo deseado en el menú `Equalizer` (`Through`, `Flat`, `Natural`, `Manual`).
2. Lanzar la captura correspondiente:
```bash
python3 scripts/capture_mode.py --mode through
python3 scripts/capture_mode.py --mode ypao_flat
python3 scripts/capture_mode.py --mode ypao_natural
python3 scripts/capture_mode.py --mode harman_impact
python3 scripts/capture_mode.py --compare
```
