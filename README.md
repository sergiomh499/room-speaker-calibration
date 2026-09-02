# 🎛️ Room Speaker Calibration & Automated Acoustic Engine
### Yamaha RX-V673 · Q Acoustics 3020i · LG C5 OLED

[![GitHub license](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-brightgreen.svg)](https://www.python.org/)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-Integrated-41BDF5.svg?logo=home-assistant)](homeassistant/)
[![Docker Ready](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker)](Dockerfile)
[![Proxmox LXC](https://img.shields.io/badge/Proxmox%20VE-LXC%20Script-E57000.svg?logo=proxmox)](deploy/proxmox/)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-Manifests-326CE5.svg?logo=kubernetes)](deploy/k8s/)

Repositorio de ingeniería electroacústica para la medición en tiempo real, análisis espectral y temporal (Waterfall CSD / RT60), promedio espacial multipunto (Dr. Floyd Toole), optimización de ecualización paramétrica (PEQ) y control integral del sistema audiovisual formado por la pantalla **LG C5 OLED**, el receptor audiovisual **Yamaha RX-V673** (7 bandas PEQ biquad IIR) y los altavoces de estantería **Q Acoustics 3020i**.

---

## 📑 Tabla de Contenidos
1. [Arquitectura del Sistema](#-arquitectura-del-sistema)
2. [Benchmark Acústico Real (5 Modos Medidos)](#-benchmark-acústico-real-5-modos-medidos)
3. [Validación Temporal: Cascada Espectral 3D (Waterfall CSD)](#-validación-temporal-cascada-espectral-3d-waterfall-csd)
4. [Promedio Espacial Multipunto (Dr. Floyd Toole)](#-promedio-espacial-multipunto-dr-floyd-toole)
5. [Parámetros PEQ Definitivos (Harman Impact & Surgical Notch)](#-parámetros-peq-definitivos-harman-impact--surgical-notch)
6. [Mapeo de las 4 Escenas del Receptor](#-mapeo-de-las-4-escenas-del-receptor-yamaha-rx-v673)
7. [Integración con Home Assistant](#-integración-con-home-assistant)
8. [Despliegue en Infraestructura (Docker, Proxmox, Kubernetes)](#-despliegue-en-infraestructura)
9. [Guías Técnicas y Documentación](#-guías-técnicas-y-documentación)
10. [Uso del Motor de Calibración por CLI](#-uso-del-motor-de-calibración-por-cli)
11. [Estructura del Repositorio](#-estructura-del-repositorio)

---

## 🏛️ Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                             FUENTE: LG C5 OLED                              │
│         Salida: HDMI ARC (HDMI 2) · Modo: Pass Through · Formato: Bitstream │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ HDMI ARC (1.4a / PCM & Bitstream)
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         RECEPTOR: YAMAHA RX-V673                            │
│  • Entrada ARC: AV4                                                         │
│  • Impedancia: 8 Ω MIN (Rango dinámico completo / Headroom sin recorte)     │
│  • Motor DSP: 7 Bandas Paramétricas (PEQ Manual Harman Impact / Notch)      │
│  • Procesado 3D: Cinema DSP 3D Auto + Virtual Presence Speaker (VPS: ON)    │
│  • DAC: Burr-Brown 192 kHz / 24-bit                                         │
└───────────────────┬─────────────────────────────────────┬───────────────────┘
                    │ Front L                             │ Front R
                    ▼                                     ▼
      ┌──────────────────────────┐          ┌──────────────────────────┐
      │   Q ACOUSTICS 3020i (L)  │          │   Q ACOUSTICS 3020i (R)  │
      │ • Espacio abierto (>50cm)│          │ • Esquina (<20 cm)       │
      │ • Distancia: 2.15 m      │          │ • Distancia: 2.20 m      │
      │ • Puerto: Abierto        │          │ • Offset: +5 cm fase     │
      └──────────────────────────┘          └──────────────────────────┘
```

---

## 📊 Benchmark Acústico Real (5 Modos Medidos)

Comparativa espectral de alta resolución obtenida por barridos sinusoidales Farina (15 Hz a 22 kHz, FFT 65k, suavizado 1/24 octava):

__omp_shell("[Gran Comparativa Multimodo](figures/gran_comparativa_multimodo.png)")

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                        EVALUACIÓN ACÚSTICA REAL: BENCHMARK DE LOS 5 MODOS MEDIDOS                      │
├──────────────────────────┬───────────────────┬───────────────────┬────────────────────┬────────────────┤
│ Modo                     │ Resonancia 110 Hz │ Pegada 50 - 65 Hz │ Voces (2.5 kHz)    │ Veredicto      │
├──────────────────────────┼───────────────────┼───────────────────┼────────────────────┼────────────────┤
│ 1. Through (Bypass)      │ +14.5 dB (Pico)   │ +3.0 dB (Plano)   │ -1.5 dB (Hundido)  │ Retumbo / Pobre│
│ 2. YPAO Flat             │ +17.0 dB (Máximo) │ +4.0 dB           │ +0.5 dB            │ Estridente     │
│ 3. YPAO Natural          │ +13.5 dB          │ +3.5 dB           │ -0.5 dB            │ Apagado        │
│ 4. Harman Neutral        │ +10.0 dB          │ +3.0 dB           │ +1.5 dB (Plano)    │ Analítico      │
│ 5. Harman Impact (TOP)   │ +4.5 dB (Mínimo)  │ +6.0 dB (+3.0 dB) │ +2.5 dB (Presente) │ 🏆 DEFINITIVO │
└──────────────────────────┴───────────────────┴───────────────────┴────────────────────┴────────────────┘
```

---

## ⏳ Validación Temporal: Cascada Espectral 3D (Waterfall CSD)

La respuesta en frecuencia no cuenta toda la historia. El análisis de **Decaimiento Espectral Acumulativo (CSD / Waterfall)** demuestra que la ecualización no solo aplana la magnitud, sino que **elimina el ringing y la resonancia temporal** en bajas frecuencias:

__omp_shell("[Waterfall CSD Comparison](figures/waterfall_csd_comparison.png)")

* **Modo Through (Izquierda)**: El modo de sala en 110 Hz continúa resonando durante **más de 220 ms**, enturbiando los transitorios y provocando sensación de bola de graves.
* **Harman Impact / Surgical Notch (Derecha)**: La resonancia se extingue en **menos de 90 ms**, proporcionando graves secos, rápidos y articulados.

---

## 🌐 Promedio Espacial Multipunto (Dr. Floyd Toole)

Para garantizar que la ecualización ataque exclusivamente **modos de sala acústicamente robustos** y no artefactos de interferencia local o cancelaciones de fase estrechas fuera de fase mínima, el motor implementa el promedio espacial RMS de múltiples posiciones en el área de escucha:

__omp_shell("[Promedio Espacial Multipunto](figures/promedio_espacial_multipunto.png)")

---

## 🎚️ Parámetros PEQ Definitivos (Harman Impact & Surgical Notch)

Introducir en el menú del Yamaha (**`ON SCREEN` $ightarrow$ `Speaker` $ightarrow$ `Manual Setup` $ightarrow$ `Equalizer` $ightarrow$ `PEQ Select: Manual`**):

| Banda | Frecuencia ($f_0$) | Factor Q (L / R) | Ganancia Front L | Ganancia Front R | Tipo Filtro | Justificación Acústica |
| :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Band 1** | **62.5 Hz** | `1.260` | **+3.0 dB** | **+2.0 dB** | PEAK (Biquad) | **Subgrave Táctil**: Pegada según curvas isofónicas (ISO 226). |
| **Band 2** | **99.2 Hz** | `1.587` / `2.000` | **+2.0 dB** | **-5.0 dB** | NOTCH / PEAK | **Atenuación Quirúrgica**: Elimina el ringing modal en esquina (R). |
| **Band 3** | **157.5 Hz** | `1.260` | **0.0 dB** | **+0.5 dB** | PEAK (Biquad) | **Paso Neutro**: Transición limpia en medios-graves. |
| **Band 4** | **250.0 Hz** | `1.000` | **0.0 dB** | **0.0 dB** | PEAK (Biquad) | **Paso Neutro**: Límite de transición (Frecuencia de Schroeder). |
| **Band 5** | **500.0 Hz** | `1.000` | **0.0 dB** | **0.0 dB** | PEAK (Biquad) | **Paso Neutro**: Preservación del timbre directo de los 3020i. |
| **Band 6** | **2.52 kHz** | `1.260` | **+1.5 dB** | **+1.5 dB** | PEAK (Biquad) | **Centro Holográfico**: Compensa el corte del filtro divisor. |
| **Band 7** | **10.1 kHz** | `1.000` | **-1.0 dB** | **-1.0 dB** | PEAK (Biquad) | **Harman Roll-off**: Caída suave anti-fatiga auditiva. |

---

## 🎬 Mapeo de las 4 Escenas (Yamaha RX-V673)

Todas las escenas están programadas en la entrada **`AV4` (HDMI ARC TV)**:

| Escena | Nombre en Pantalla | Modo de Audio | Adaptive DRC | Dialogue Lift | Propósito Acústico |
| :---: | :---: | :---: | :---: | :---: | :--- |
| **SCENE 1** | **Música Hi-Fi** | `Straight` | `Off` | `0` | Pureza audiófila bit por bit sin procesamiento espacial. |
| **SCENE 2** | **Cine Estándar** | `Standard DSP` | `Off / MAX` | `1` | Campo envolvente 3D y elevación de voces al panel OLED. |
| **SCENE 3** | **Noche y Voces** | `Drama DSP` | `Auto` | `2` | Inteligibilidad vocal y nivelación dinámica nocturna. |
| **SCENE 4** | **Conciertos / Live**| `Music Video` | `Off / MAX` | `0` | Inmersión acústica de auditorio/estadio para directos. |

---

## 🏠 Integración con Home Assistant

* 📄 **Paquete YAML**: [`homeassistant/yamaha_calibration_package.yaml`](homeassistant/yamaha_calibration_package.yaml)
* 🎨 **Tarjeta Dashboard**: [`homeassistant/lovelace_card.yaml`](homeassistant/lovelace_card.yaml)
* 📖 **Guía Completa**: [`docs/HOME_ASSISTANT.md`](docs/HOME_ASSISTANT.md)

---

## 🚀 Despliegue en Infraestructura

* 🐳 **Docker & Docker Compose**: `docker compose up -d`
* 🎛️ **Proxmox VE (LXC)**: `deploy/proxmox/install_lxc.sh`
* ☸️ **Kubernetes**: `deploy/k8s/`
* 🏠 **Home Assistant Add-on**: `homeassistant/addon/`
* 📖 **Guía de Despliegue**: [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md)

---

## 💻 Uso del Motor de Calibración por CLI

```bash
# 1. Calcular promedio espacial multipunto (Dr. Floyd Toole):
python3 scripts/spatial_average.py

# 2. Generar cascada espectral 3D (Waterfall CSD) y análisis RT60:
python3 scripts/waterfall_csd.py

# 3. Ejecutar optimización automática con filtro notch quirúrgico y promedio multipunto:
python3 scripts/auto_calibrate.py --target harman_surgical_notch --multipoint --export-pdf

# 4. Conmutar escenas del Yamaha por red:
python3 scripts/04_yamaha_control.py scene 1 # Música Hi-Fi
python3 scripts/04_yamaha_control.py scene 2 # Cine Estándar

# 5. Iniciar el servidor REST Bridge para Home Assistant:
python3 scripts/ha_bridge.py --serve
```

---

## 📂 Estructura del Repositorio

```
room-speaker-calibration/
├── config/
│   ├── equipment.json             # Ficha técnica (Yamaha RX-V673 + Q Acoustics 3020i)
│   └── targets.json               # Definiciones de curvas (Harman Impact, Surgical Notch...)
├── data/
│   ├── medicion_harman_impact.npz # Medición real verificada en modo Straight
│   ├── medicion_promedio_espacial.npz # Dataset de promedio espacial multipunto
│   ├── medicion_through.npz       # Medición real sin ecualizar (Bypass)
│   ├── medicion_ypao_flat.npz     # Medición real YPAO Flat
│   ├── sweep_signal_L.wav         # Señal Farina Log-Sweep Canal Izquierdo
│   └── sweep_signal_R.wav         # Señal Farina Log-Sweep Canal Derecho
├── deploy/
│   ├── k8s/                       # Manifiestos de Kubernetes (Deployment, Service, ConfigMap)
│   └── proxmox/                   # Script automatizado de despliegue en Proxmox LXC
├── docs/
│   ├── ACOUSTIC_TARGETS.md        # Fundamentos científicos, Toole y curvas psicoacústicas
│   ├── DEPLOYMENT.md              # Guía de despliegue en Docker, Proxmox, K8s y HA OS
│   ├── EQUIPMENT_GUIDE.md         # Guía de hardware, DAC, impedancia y DSP 3D
│   ├── HOME_ASSISTANT.md          # Guía de integración en Home Assistant
│   └── PROCEDURE.md               # Protocolo paso a paso de medición acústica
├── figures/
│   ├── gran_comparativa_multimodo.png # Benchmark comparativo a 5 bandas de alta resolución
│   ├── promedio_espacial_multipunto.png # Gráfica de promedio espacial multipunto
│   ├── rt60_decay_analysis.png        # Gráfica de tiempo de reverberación RT60 por octava
│   ├── waterfall_csd_comparison.png   # Cascada espectral 3D (Waterfall CSD)
│   └── respuesta_impulso_real.png     # Gráfica de respuesta temporal al impulso
├── homeassistant/
│   ├── addon/                     # Configuración de Add-on local para Home Assistant OS
│   ├── lovelace_card.yaml         # Tarjeta Dashboard para Lovelace
│   ├── yamaha-calibration-bridge.service # Unidad de servicio systemd de usuario
│   └── yamaha_calibration_package.yaml   # Paquete integral de entidades para HA
├── reports/
│   └── Informe_Calibracion_Acustica_Real.pdf # Informe oficial de ingeniería acústica (3 págs)
├── scripts/
│   ├── 01_measure_sweep.py        # Motor de emisión y captura acústica en tiempo real
│   ├── 02_plot_responses.py       # Renderizador de figuras
│   ├── 03_generate_pdf_report.py  # Compilador ReportLab del informe técnico
│   ├── 04_yamaha_control.py       # Utilidad de control y conmutación de escenas por red
│   ├── auto_calibrate.py          # Motor CLI de optimización PEQ (Multipunto + Notch)
│   ├── capture_mode.py            # Capturador y comparador multimodo
│   ├── ha_bridge.py               # Servidor REST Bridge bidireccional para Home Assistant
│   ├── spatial_average.py         # Motor de promedio espacial multipunto RMS (Toole)
│   └── waterfall_csd.py           # Motor de cascada espectral 3D (CSD) y RT60
├── Dockerfile                     # Definición de contenedor Docker
├── docker-compose.yml             # Stack Docker Compose
├── requirements.txt               # Dependencias de Python
└── README.md                      # Documentación maestra del repositorio
```
