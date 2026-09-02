# 🎛️ Sistema de Optimización Acústica y Calibración Modular
## Yamaha RX-V673 · Q Acoustics 3020i · LG C5 OLED

Repositorio modular de ingeniería electroacústica para la medición en tiempo real, análisis espectral, optimización paramétrica automática y documentación técnica de corrección de sala.

---

## 📁 Estructura del Repositorio

```
yamaha-qacoustics-calibration/
├── config/
│   ├── equipment.json                 # Perfiles de hardware (Yamaha, Q Acoustics, extensibles)
│   └── targets.json                   # Curvas psicoacústicas (Harman, Cinema, Vocal, Warm, Flat)
├── data/
│   ├── medicion_real_calibracion.npz  # Datos reales medidos (Raw FFT 65k, Suavizado 1/24, IR)
│   ├── sweep_signal_L.wav             # Señal de excitación (Barrido Farina L)
│   └── sweep_signal_R.wav             # Señal de excitación (Barrido Farina R)
├── docs/
│   ├── PROCEDURE.md                   # Protocolo y guía paso a paso de medición
│   ├── ACOUSTIC_TARGETS.md            # Fundamentos acústicos (Toole, Olive, Schroeder, Curvas)
│   └── EQUIPMENT_GUIDE.md             # Guía técnica de hardware y cómo añadir nuevos equipos
├── figures/
│   ├── respuesta_acustica_real.png    # Gráficas acústicas reales (Front L, Front R, Simetría)
│   └── respuesta_impulso_real.png     # Respuesta al impulso por deconvolución temporal
├── reports/
│   └── Informe_Calibracion_Acustica_Real.pdf # Informe técnico completo de ingeniería en PDF
├── scripts/
│   ├── auto_calibrate.py             # Motor CLI de optimización y cálculo paramétrico automático
│   ├── 01_measure_sweep.py            # Motor de medición y captura por barrido Farina
│   ├── 02_plot_responses.py          # Generador de gráficas acústicas reales
│   ├── 03_generate_pdf_report.py      # Compilador del informe PDF de ingeniería
│   └── 04_yamaha_control.py          # Utilidad de control y consulta en red del receptor
└── README.md                          # Documentación técnica maestra
```

---

## 🚀 Uso Rápido: Motor de Calibración Automática (`auto_calibrate.py`)

El script `auto_calibrate.py` calcula automáticamente las 7 bandas PEQ óptimas para el Yamaha respetando sus restricciones de hardware (frecuencias discretas, factores Q permitidos y pasos de 0.5 dB):

```bash
cd /home/sergio/yamaha-qacoustics-calibration

# 1. Calibración de Referencia Equilibrada (Harman House Curve - Música y Cine):
python3 scripts/auto_calibrate.py --target harman_neutral --export-pdf

# 2. Perfil Cine de Acción e Impacto (Graves contundentes y agudos suaves):
python3 scripts/auto_calibrate.py --target cinema_impact --export-pdf

# 3. Perfil Claridad Vocal (Podcasts, YouTube hablado, Diálogos de noche):
python3 scripts/auto_calibrate.py --target vocal_clarity --export-pdf

# 4. Perfil Calidez Analógica / Vinilo (Graves redondos y agudos relajados):
python3 scripts/auto_calibrate.py --target warm_music --export-pdf

# 5. Perfil Audiófilo Neutro / Difuso (Respuesta estrictamente plana):
python3 scripts/auto_calibrate.py --target audiophile_flat --export-pdf
```

---

## 📚 Documentación Técnica Detallada (`docs/`)

* 📖 **[`docs/PROCEDURE.md`](docs/PROCEDURE.md)**: Guía paso a paso de preparación de sala, colocación del micrófono a 90°, cableado HDMI/ALSA y captura sin ruido.
* 📖 **[`docs/ACOUSTIC_TARGETS.md`](docs/ACOUSTIC_TARGETS.md)**: Fundamentos psicoacústicos (investigaciones de Floyd Toole y Sean Olive / Harman), Frecuencia de Schroeder ($f_s$), y guía completa de curvas según géneros musicales y cine.
* 📖 **[`docs/EQUIPMENT_GUIDE.md`](docs/EQUIPMENT_GUIDE.md)**: Desglose técnico de la arquitectura del Yamaha RX-V673 (Burr-Brown DAC, DSP, impedancia) y Q Acoustics 3020i (crossover, P2P bracing), junto a la guía para añadir nuevos altavoces y receptores a `config/equipment.json`.

---

## 📊 Coeficientes PEQ de Referencia Grabados (Perfil `harman_neutral`)

| Banda | Frecuencia ($f_0$) | Factor Q (L / R) | Ganancia Front L | Ganancia Front R | Función Acústica |
| :---: | :---: | :---: | :---: | :---: | :--- |
| **Band 1** | **62.5 Hz** | `1.260` | **-1.0 dB** | **-1.5 dB** | Atenuación de ganancia de límite en subgrave |
| **Band 2** | **99.2 Hz** | `1.587` / `1.260` | **-1.5 dB** | **-1.5 dB** | Supresión del modo resonante axial de la sala |
| **Band 3** | **157.5 Hz** | `1.260` / `1.000` | **-1.0 dB** | **0.0 dB** | Limpieza de resonancia en la voz masculina |
| **Band 4** | **250.0 Hz** | `1.000` | **0.0 dB** | **0.0 dB** | Paso neutro transparente |
| **Band 5** | **500.0 Hz** | `1.000` | **0.0 dB** | **0.0 dB** | Paso neutro transparente |
| **Band 6** | **2.52 kHz** | `1.260` | **+1.5 dB** | **+1.5 dB** | Compensación del escalón del filtro divisor de los 3020i |
| **Band 7** | **10.1 kHz** | `1.000` | **-1.0 dB** | **-1.0 dB** | Caída suave *Harman House Curve* contra fatiga auditiva |
