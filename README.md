# 🎛️ Room Speaker Calibration & Automated Acoustic Engine
### Yamaha RX-V673 · Q Acoustics 3020i · LG C5 OLED

[![GitHub license](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-brightgreen.svg)](https://www.python.org/)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-Integrated-41BDF5.svg?logo=home-assistant)](homeassistant/)
[![Docker Ready](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker)](Dockerfile)
[![Proxmox LXC](https://img.shields.io/badge/Proxmox%20VE-LXC%20Script-E57000.svg?logo=proxmox)](deploy/proxmox/)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-Manifests-326CE5.svg?logo=kubernetes)](deploy/k8s/)

Repositorio de ingeniería electroacústica para la medición en tiempo real, análisis espectral de alta resolución, optimización de ecualización paramétrica (PEQ) y control integral del sistema audiovisual formado por la pantalla **LG C5 OLED**, el receptor audiovisual **Yamaha RX-V673** (7 bandas PEQ biquad IIR) y los altavoces de estantería **Q Acoustics 3020i**.

---

## 📑 Tabla de Contenidos
1. [Arquitectura del Sistema](#-arquitectura-del-sistema)
2. [Benchmark Acústico Real (5 Modos Medidos)](#-benchmark-acústico-real-5-modos-medidos)
3. [Parámetros PEQ Definitivos (Harman Impact Reference)](#-parámetros-peq-definitivos-harman-impact-reference)
4. [Mapeo de las 4 Escenas del Receptor](#-mapeo-de-las-4-escenas-del-receptor-yamaha-rx-v673)
5. [Integración con Home Assistant](#-integración-con-home-assistant)
6. [Despliegue en Infraestructura (Docker, Proxmox, Kubernetes)](#-despliegue-en-infraestructura)
7. [Guías Técnicas y Documentación](#-guías-técnicas-y-documentación)
8. [Uso del Motor de Calibración por CLI](#-uso-del-motor-de-calibración-por-cli)
9. [Estructura del Repositorio](#-estructura-del-repositorio)

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
│  • Motor DSP: 7 Bandas Paramétricas (PEQ Manual Harman Impact)              │
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

A continuación se presenta la comparativa acústica de alta resolución capturada con micrófono de medición en la sala real mediante barridos sinusoidales de Farina (15 Hz a 22 kHz, FFT 65k, suavizado 1/24 de octava):

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

## 🎚️ Parámetros PEQ Definitivos (Harman Impact Reference)

Introducir en el menú del Yamaha (**`ON SCREEN` $ightarrow$ `Speaker` $ightarrow$ `Manual Setup` $ightarrow$ `Equalizer` $ightarrow$ `PEQ Select: Manual`**):

| Banda | Frecuencia ($f_0$) | Factor Q (L / R) | Ganancia Front L | Ganancia Front R | Tipo Filtro | Justificación Acústica |
| :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Band 1** | **62.5 Hz** | `1.260` | **+3.0 dB** | **+2.0 dB** | PEAK (Biquad) | **Subgrave Táctil**: Pegada según curvas isofónicas (ISO 226). |
| **Band 2** | **99.2 Hz** | `1.587` / `1.260` | **+2.0 dB** | **-4.0 dB** | PEAK (Biquad) | **Control Asimétrico de Esquina**: Domina la resonancia en R. |
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

El repositorio incluye un paquete YAML completo, tarjeta Lovelace y servidor bridge REST (`ha_bridge.py`) para control integral en Home Assistant:

* 📄 **Paquete YAML**: [`homeassistant/yamaha_calibration_package.yaml`](homeassistant/yamaha_calibration_package.yaml)
* 🎨 **Tarjeta Dashboard**: [`homeassistant/lovelace_card.yaml`](homeassistant/lovelace_card.yaml)
* 📖 **Guía Completa**: [`docs/HOME_ASSISTANT.md`](docs/HOME_ASSISTANT.md)

---

## 🚀 Despliegue en Infraestructura

El sistema está preparado para ejecutarse en cualquier entorno de contenedores o virtualización:
* 🐳 **Docker & Docker Compose**: `docker compose up -d`
* 🎛️ **Proxmox VE (LXC)**: `deploy/proxmox/install_lxc.sh`
* ☸️ **Kubernetes**: `deploy/k8s/` (`ConfigMap`, `Deployment`, `Service`)
* 🏠 **Home Assistant Add-on**: `homeassistant/addon/`
* 📖 **Guía de Despliegue**: [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md)

---

## 📚 Guías Técnicas y Documentación

* **[`docs/PROCEDURE.md`](docs/PROCEDURE.md)**: Protocolo de medición acústica con trípode a 90°, aislamiento de ruido (<35 dB) y deconvolución de Farina.
* **[`docs/ACOUSTIC_TARGETS.md`](docs/ACOUSTIC_TARGETS.md)**: Fundamentos psicoacústicos (Harman Research, Floyd Toole, Sean Olive, curvas isofónicas ISO 226, frecuencia de Schroeder).
* **[`docs/EQUIPMENT_GUIDE.md`](docs/EQUIPMENT_GUIDE.md)**: Análisis del DAC Burr-Brown, conmutador de impedancia a 8 $\Omega$, Cinema DSP 3D/VPS y refuerzos P2P de los altavoces.
* **[`docs/HOME_ASSISTANT.md`](docs/HOME_ASSISTANT.md)**: Integración bidireccional, telemetría y automatismos en Home Assistant.
* **[`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md)**: Manual de despliegue en Docker, Proxmox, Kubernetes y Home Assistant OS.

---

## 💻 Uso del Motor de Calibración por CLI

```bash
# Ejecutar optimización automática para un perfil concreto:
python3 scripts/auto_calibrate.py --target harman_impact --export-pdf
python3 scripts/auto_calibrate.py --target cinema_impact --export-pdf
python3 scripts/auto_calibrate.py --target vocal_clarity --export-pdf

# Conmutar escenas del Yamaha por red:
python3 scripts/04_yamaha_control.py scene 1 # Música Hi-Fi
python3 scripts/04_yamaha_control.py scene 2 # Cine Estándar
python3 scripts/04_yamaha_control.py scene 3 # Noche y Voces
python3 scripts/04_yamaha_control.py scene 4 # Conciertos / Live

# Iniciar el servidor REST Bridge para Home Assistant:
python3 scripts/ha_bridge.py --serve
```

---

## 📂 Estructura del Repositorio

```
room-speaker-calibration/
├── config/
│   ├── equipment.json             # Ficha técnica extensible (Yamaha RX-V673 + Q Acoustics 3020i)
│   └── targets.json               # Definiciones matemáticas de curvas psicoacústicas
├── data/
│   ├── medicion_harman_impact.npz # Medición real verificada en modo Straight
│   ├── medicion_harman_neutral.npz# Medición real Harman Neutral
│   ├── medicion_through.npz       # Medición real sin ecualizar (Bypass)
│   ├── medicion_ypao_flat.npz     # Medición real YPAO Flat
│   ├── medicion_ypao_natural.npz  # Medición real YPAO Natural
│   ├── sweep_signal_L.wav         # Señal Farina Log-Sweep Canal Izquierdo
│   └── sweep_signal_R.wav         # Señal Farina Log-Sweep Canal Derecho
├── deploy/
│   ├── k8s/                       # Manifiestos de Kubernetes (Deployment, Service, ConfigMap)
│   └── proxmox/                   # Script automatizado de despliegue en Proxmox LXC
├── docs/
│   ├── ACOUSTIC_TARGETS.md        # Fundamentos científicos y curvas psicoacústicas
│   ├── DEPLOYMENT.md              # Guía de despliegue en Docker, Proxmox, K8s y HA OS
│   ├── EQUIPMENT_GUIDE.md         # Guía de hardware, DAC, impedancia y DSP 3D
│   ├── HOME_ASSISTANT.md          # Guía de integración en Home Assistant
│   └── PROCEDURE.md               # Protocolo paso a paso de medición acústica
├── figures/
│   ├── gran_comparativa_multimodo.png # Benchmark comparativo a 5 bandas de alta resolución
│   ├── respuesta_acustica_real.png    # Gráfica FFT y suavizado 1/24 octava
│   └── respuesta_impulso_real.png     # Gráfica de respuesta temporal al impulso
├── homeassistant/
│   ├── addon/                     # Configuración de Add-on local para Home Assistant OS
│   ├── lovelace_card.yaml         # Tarjeta Dashboard para Lovelace
│   ├── yamaha-calibration-bridge.service # Unidad de servicio systemd de usuario
│   └── yamaha_calibration_package.yaml   # Paquete integral de entidades para HA
├── reports/
│   └── Informe_Calibracion_Acustica_Real.pdf # Informe oficial de ingeniería acústica
├── scripts/
│   ├── 01_measure_sweep.py        # Motor de emisión y captura acústica en tiempo real
│   ├── 02_plot_responses.py       # Renderizador de gráficas de sala
│   ├── 03_generate_pdf_report.py  # Compilador ReportLab del informe técnico
│   ├── 04_yamaha_control.py       # Utilidad de control y conmutación de escenas por red
│   ├── auto_calibrate.py          # Motor CLI de optimización PEQ
│   ├── capture_mode.py            # Capturador y comparador multimodo
│   └── ha_bridge.py               # Servidor REST Bridge bidireccional para Home Assistant
├── Dockerfile                     # Definición de contenedor Docker
├── docker-compose.yml             # Stack Docker Compose
├── requirements.txt               # Dependencias de Python
└── README.md                      # Documentación maestra del repositorio
```
