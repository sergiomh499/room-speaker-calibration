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
│   └── EQUIPMENT_GUIDE.md             # Guía técnica de hardware, escenas y extensibilidad
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
│   └── 04_yamaha_control.py          # Control en red y conmutación de escenas
└── README.md                          # Documentación técnica maestra
```

---

## 🎬 Mapeo y Programación de las 4 Escenas (Yamaha RX-V673)

Todas las escenas utilizan la entrada **`AV4` (HDMI ARC desde LG C5)** con el **PEQ Manual activo**:

| Escena (Mando) | Nombre en Pantalla | Modo de Sonido | Adaptive DRC | Dialogue | Uso Óptimo Recomendado |
| :---: | :--- | :---: | :---: | :---: | :--- |
| **SCENE 1** | **`Música Hi-Fi`** | **`Straight`** | **`Off`** | `0` *(Bypass)* | **Música Lossless, Spotify, Amazon Music, Vinilos**. Sonido puro sin procesado espacial. |
| **SCENE 2** | **`Cine Estándar`** | **`Standard DSP`** | **`Off / MAX`** | **`+1`** | **Películas y Series en Stremio, Prime, Netflix**. Máxima dinámica y diálogos claros. |
| **SCENE 3** | **`Noche y Voces`** | **`Drama DSP`** | **`Auto`** | **`+2`** | **YouTube hablado, Podcasts, Cine de noche**. Nivelación de volumen contra sobresaltos. |
| **SCENE 4** | **`Conciertos/Live`**| **`Music Video`** | **`Off / MAX`** | `0` | **Festivales en directo, Deportes, Conciertos**. Inmersión acústica de estadio/recinto. |

---

## 🚀 Uso Rápido: Motor de Calibración Automática (`auto_calibrate.py`)

Calcula al instante las 7 bandas PEQ óptimas según el perfil deseado:

```bash
cd /home/sergio/yamaha-qacoustics-calibration

# 1. Calibración de Referencia Equilibrada (Harman Target):
python3 scripts/auto_calibrate.py --target harman_neutral --export-pdf

# 2. Perfil Cine de Acción e Impacto:
python3 scripts/auto_calibrate.py --target cinema_impact --export-pdf

# 3. Perfil Claridad Vocal (Podcasts / Diálogos):
python3 scripts/auto_calibrate.py --target vocal_clarity --export-pdf

# 4. Conmutar Escenas del Receptor por Red:
python3 scripts/04_yamaha_control.py scene 1   # Activa SCENE 1 (Música Hi-Fi)
python3 scripts/04_yamaha_control.py scene 2   # Activa SCENE 2 (Cine Estándar)
python3 scripts/04_yamaha_control.py scene 3   # Activa SCENE 3 (Noche y Voces)
python3 scripts/04_yamaha_control.py scene 4   # Activa SCENE 4 (Conciertos/Live)
```
