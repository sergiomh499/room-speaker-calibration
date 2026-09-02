# Optimización Acústica y Calibración de Sala
## Sistema: LG C5 OLED · Yamaha RX-V673 · Q Acoustics 3020i

Este repositorio contiene la totalidad de los datos de medición real, scripts de procesamiento acústico, figuras de alta resolución, informes de ingeniería y utilidades de control en red desarrollados para la calibración electroacústica del sistema estéreo 2.0.

---

## 📁 Estructura del Repositorio

```
yamaha-qacoustics-calibration/
├── data/
│   ├── medicion_real_calibracion.npz  # Datos reales medidos (FFT 65k, suavizado 1/24, IR)
│   ├── sweep_signal_L.wav             # Señal de excitación (Barrido Logarítmico Farina L)
│   └── sweep_signal_R.wav             # Señal de excitación (Barrido Logarítmico Farina R)
├── figures/
│   ├── respuesta_acustica_real.png    # Gráficas reales de respuesta y simetría estéreo
│   └── respuesta_impulso_real.png     # Respuesta temporal al impulso (deconvolución)
├── reports/
│   └── Informe_Calibracion_Acustica_Real.pdf # Informe técnico completo en PDF
├── scripts/
│   ├── 01_measure_sweep.py            # Motor de medición y captura por barrido Farina
│   ├── 02_plot_responses.py          # Generador de gráficas acústicas reales
│   ├── 03_generate_pdf_report.py      # Compilador del informe PDF de ingeniería
│   └── 04_yamaha_control.py          # Utilidad de control y consulta en red del receptor
└── README.md                          # Documentación técnica maestra
```

---

## 🛠️ Especificaciones de la Cadena de Audio y Entorno

| Componente | Modelo / Tecnología | Parámetros Eléctricos y Operativos |
| :--- | :--- | :--- |
| **Fuente / Pantalla** | **LG C5 OLED (webOS)** | Salida HDMI ARC · Formato Bitstream · Salida Digital: **Transferencia (Pass Through)** · **eARC: Off** · Latencia: Bypass |
| **Receptor AV** | **Yamaha RX-V673** | HDMI 1.4a ARC · DAC Burr-Brown 192 kHz / 24-bit · **Impedancia: 8 Ω MIN** · **ECO Mode: Off** · **Dynamic Range: MAX** |
| **Altavoces** | **Q Acoustics 3020i** | 2 vías Bass-Reflex · Cono de 125 mm (5") · Tweeter de 22 mm desacoplado · Imp: 6 Ω (mín 4 Ω) · Sens: 88 dB/W/m |
| **Entorno Físico** | Sala Asimétrica | **Canal L (Front L)**: Espacio abierto (>50 cm) · **Canal R (Front R)**: Esquina (<20 cm, Corner loading) |

---

## 📊 Coeficientes del Ecualizador Paramétrico (PEQ Manual)

Configuración definitiva introducida en la memoria `PEQ Manual` del procesador DSP de Yamaha:

### Front L (Canal Izquierdo — Abierto a Sala)
* **Band 1 (62.5 Hz)**: Ganancia **`-1.0 dB`** | $Q = 1.260$ *(Control de ganancia en subgrave)*
* **Band 2 (99.2 Hz)**: Ganancia **`-1.5 dB`** | $Q = 1.587$ *(Atenuación del modo axial principal)*
* **Band 3 (157.5 Hz)**: Ganancia **`-1.0 dB`** | $Q = 1.260$ *(Limpieza de medios-graves)*
* **Band 4 (250.0 Hz)**: Ganancia **`0.0 dB`** | $Q = 1.000$ *(Paso neutro)*
* **Band 5 (500.0 Hz)**: Ganancia **`0.0 dB`** | $Q = 1.000$ *(Paso neutro)*
* **Band 6 (2.52 kHz)**: Ganancia **`+1.5 dB`** | $Q = 1.260$ *(Compensación del escalón del filtro divisor de 3020i)*
* **Band 7 (10.1 kHz)**: Ganancia **`-1.0 dB`** | $Q = 1.000$ *(Caída suave Harman House Curve contra fatiga auditiva)*

### Front R (Canal Derecho — Esquina)
* **Band 1 (62.5 Hz)**: Ganancia **`-1.5 dB`** | $Q = 1.260$ *(Atenuación de sobrepresión de esquina)*
* **Band 2 (99.2 Hz)**: Ganancia **`-1.5 dB`** | $Q = 1.260$ *(Equilibrio simétrico tonal)*
* **Band 3 (157.5 Hz)**: Ganancia **`0.0 dB`** | $Q = 1.000$ *(Paso neutro)*
* **Band 4 (250.0 Hz)**: Ganancia **`0.0 dB`** | $Q = 1.000$ *(Paso neutro)*
* **Band 5 (500.0 Hz)**: Ganancia **`0.0 dB`** | $Q = 1.000$ *(Paso neutro)*
* **Band 6 (2.52 kHz)**: Ganancia **`+1.5 dB`** | $Q = 1.260$ *(Compensación del escalón del filtro divisor de 3020i)*
* **Band 7 (10.1 kHz)**: Ganancia **`-1.0 dB`** | $Q = 1.000$ *(Caída suave Harman House Curve)*

---

## 🎬 Mapeo Operativo de Escenas en Yamaha RX-V673

1. **SCENE 1 (Música / Audición Pura)**:
   * **Entrada**: `AV4` (HDMI ARC desde LG C5).
   * **Modo**: `Straight` (procesamiento espacial Cinema DSP apagado).
   * **Adaptive DRC**: `Off` (rango dinámico 100% íntegro).
   * **Dialogue Level**: Inactivo automáticamente por modo Straight.
2. **SCENE 2 (Cine / Series / YouTube Hablado)**:
   * **Entrada**: `AV4` (HDMI ARC desde LG C5).
   * **Modo**: `Standard` (Cinema DSP activo).
   * **Adaptive DRC**: `Auto` (nivelación de volumen en diálogos nocturnos y anuncios).
   * **Dialogue Level**: **`+1`** (adelanto de presencia vocal en mezcla estéreo).

---

## 🚀 Instrucciones de Ejecución de los Scripts

Para repetir mediciones o regenerar informes en cualquier momento:

```bash
cd /home/sergio/yamaha-qacoustics-calibration

# 1. Ejecutar una nueva medición acústica en tiempo real:
python3 scripts/01_measure_sweep.py

# 2. Regenerar las figuras y métricas de simetría:
python3 scripts/02_plot_responses.py

# 3. Compilar el informe de ingeniería en PDF:
python3 scripts/03_generate_pdf_report.py

# 4. Consultar el estado en red del receptor Yamaha:
python3 scripts/04_yamaha_control.py status
```
