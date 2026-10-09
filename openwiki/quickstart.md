---
type: guide
title: Guía de Calibración Acústica y Uso Rápido
description: Flujo de medición acústica desacoplada, optimización PEQ cuantizada para Yamaha RX-V673 y verificación post-calibración.
tags: [quickstart, acoustic, peq, yamaha, dsp, calibration]
---

# Guía de Calibración Acústica y Uso Rápido

## Requisitos de Hardware y Entorno

* **Amplificador / AVR**: Yamaha RX-V673 (control por red YNC / HTTP XML).
* **Altavoces**: Q Acoustics 3020i en estéreo.
* **Micrófono de medición**: Smartphone desacoplado (Google Pixel 9 Pro) o micrófono calibrado USB.
* **Servidor de calibración**: Python 3 con `numpy`, `scipy`, `soundfile`.
* **Frontend**: React + TypeScript (`frontend/`).

## Flujo Rápido de Calibración

### 1. Iniciar el Servidor Web de Calibración
```bash
python3 scripts/web_calibration_server.py
```
El servidor levanta en `https://0.0.0.0:53317` con certificado autofirmado para permitir acceso desde el navegador móvil en la red local.

### 2. Protocolo de Medición Acústica
1. Conectar el smartphone a la misma red Wi-Fi y abrir `https://<IP_LOCAL>:53317`.
2. Realizar las comprobaciones de ruido de fondo (*pre-flight check*).
3. Reproducir el barrido acústico logarítmico (chirp FFT) desde el AVR en cada uno de los puntos designados (promedio espacial de 1 a 5 puntos, ponderando el Sweet Spot al 80%).

### 3. Optimización PEQ Matemática
Ejecutar el motor de optimización matemática sin plantillas sintéticas:
```bash
python3 scripts/peq_optimizer.py
```
El algoritmo calcula los filtros biquad cuantizados ajustándose a las 28 frecuencias y 14 factores Q exactos del DSP de Yamaha.

### 4. Aplicación al AVR
Los filtros pueden inyectarse directamente a la memoria NVRAM del receptor Yamaha a través del botón en la interfaz web o mediante la API de control HTTP.
