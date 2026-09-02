# Guía Técnica de Equipamiento y Extensibilidad del Sistema

Este documento recopila las especificaciones de ingeniería de los componentes actuales y detalla el procedimiento para dar de alta nuevos altavoces y receptores en la arquitectura de calibración.

---

## 1. Análisis Técnico del Yamaha RX-V673

### A. Procesamiento Digital de Señal (DSP) y DAC
* **Conversores Digital/Analógico (DAC)**: Utiliza convertidores **Burr-Brown PCM5101 / DSD1791 (192 kHz / 24-bit)** en todos los canales principales, con una relación señal-ruido (SNR) de más de 105 dB.
* **Arquitectura PEQ**:
  * 7 filtros paramétricos IIR de 2º orden (*Biquad*) por canal.
  * Pasos de frecuencia discretos (18 frecuencias disponibles entre 62.5 Hz y 16 kHz).
  * Factores Q seleccionables: `1.000`, `1.260`, `1.587`.
  * Ganancia: de `-12.0 dB` a `+3.0 dB` en pasos de `0.5 dB`.
* **Motor CINEMA DSP**:
  * Funciones de realce como `Dialogue Level` y `Dialogue Lift` operan sobre el canal central virtual calculando desfases y sumas vectoriales en los transistores frontales.
  * En modo `Straight`, el procesador DSP espacial se apaga por completo, entregando una señal pura canal por canal.

### B. Gestión Eléctrica e Impedancia
* **Conmutador de Impedancia (`ADVANCED SETUP > SP IMP.`)**:
  * **Ajuste 8 Ω MIN (Recomendado)**: Mantiene los raíles de tensión del transformador a plena capacidad (~45V), garantizando el rango dinámico completo y transitorios rápidos para altavoces de 6 Ω como los 3020i.
  * **Ajuste 6 Ω MIN**: Limita la tensión de alimentación mediante derivación de bobinado para superar pruebas térmicas continuas de laboratorio, pero comprime el *headroom* en picos musicales.

---

## 2. Análisis Electroacústico de los Q Acoustics 3020i

* **Estructura del Recinto (*Point-to-Point P2P Bracing*)**:
  * Paneles de MDF de 20 mm con refuerzos internos dirigidos por interferometría láser para eliminar resonancias de caja en los 400–800 Hz.
* **Transductor de Graves/Medios (Woofer)**:
  * Cono de 125 mm (5") de papel tratado con fibras de aramida.
  * Frecuencia de corte anecoico natural ($F_3$): **64 Hz** (pendiente de 24 dB/octava en modo Bass-Reflex).
* **Transductor de Agudos (Tweeter)**:
  * Cúpula suave de microfibra de 22 mm (0.9").
  * **Desacoplo Mecánico**: La placa frontal del tweeter está aislada físicamente del chasis del bafle mediante una junta viscoelástica, evitando que las vibraciones del woofer se transmitan a los agudos.
* **Comportamiento del Crossover**:
  * Cruce de 2º orden en **2.400 Hz**.
  * En mediciones anecoicas (Spinorama), presenta un ligero escalón/valle de $-2.0	ext{ dB}$ en la zona de transición que nuestro ecualizador compensa mediante el filtro `2520 Hz (+1.5 dB, Q=1.260)`.

---

## 3. Cómo Dar de Alta Nuevos Equipos en `config/equipment.json`

El motor de calibración `auto_calibrate.py` es **100% modular**. Para incorporar nuevos altavoces o receptores, basta con añadir una nueva entrada en `config/equipment.json`:

### Ejemplo 1: Añadir un Nuevo Altavoz (ej. KEF Q350)
```json
"speakers": {
    "kef_q350": {
        "brand": "KEF",
        "model": "Q350",
        "type": "2-way Uni-Q Coaxial",
        "woofer_size_inch": 6.5,
        "tweeter_size_mm": 25.0,
        "tweeter_decoupled": false,
        "crossover_frequency_hz": 2500.0,
        "spinorama_notch_compensation": null,
        "f3_extension_hz": 51.0,
        "nominal_impedance_ohm": 8.0,
        "minimum_impedance_ohm": 3.7,
        "sensitivity_db": 87.0,
        "recommended_crossover_subwoofer_hz": 70.0
    }
}
```

### Ejemplo 2: Añadir un Nuevo Receptor o DSP (ej. Denon con Audyssey / MiniDSP)
```json
"av_receivers": {
    "minidsp_2x4hd": {
        "brand": "MiniDSP",
        "model": "2x4 HD",
        "dac": "AKM AK4456 192kHz/32-bit",
        "peq_bands": 10,
        "discrete_frequencies_hz": null,
        "allowed_q_values": null,
        "gain_step_db": 0.1,
        "max_boost_db": 6.0,
        "max_cut_db": -20.0,
        "ip_control_available": false
    }
}
```

Al ejecutar `python3 scripts/auto_calibrate.py --speaker kef_q350 --avr minidsp_2x4hd`, el motor optimizará automáticamente los filtros adaptándose a los límites de resolución del nuevo hardware.
