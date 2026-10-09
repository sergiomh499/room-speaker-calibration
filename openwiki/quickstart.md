---
type: guide
title: Acoustic Calibration Quickstart & Operational Guide
description: End-to-end operational guide for standalone Android mobile room calibration, on-device Farina sweep execution, discrete Yamaha PEQ programming, and verification.
tags: [quickstart, calibration, android, yamaha, peq, farina-sweep]
verified:
  - by: openwiki/0.7.1
    at: 2026-10-09T22:03:18.374Z
sources:
  - id: openwiki-source-2dce44551be719e25e08ba51
    resource: repo://frontend/src/services/avrRollback.ts
  - id: openwiki-source-aee57788baec6f022d15f90f
    resource: repo://frontend/src/views/CalibrateView.tsx
  - id: openwiki-source-a9f48595f5e17d7c358ba2df
    resource: repo://specs/012-pro-android-calibration/quickstart.md
generated: { by: "omp", at: "2026-10-09T22:03:18.374Z" }
---

# Acoustic Calibration Quickstart & Operational Guide

## Hardware Prerequisites & Environment

* **Audio/Video Receiver (AVR)**: Yamaha RX-V673 connected to local Wi-Fi (`192.168.1.43`).
* **Loudspeakers**: Q Acoustics 3020i (Left & Right bookshelf pair) + Focal Cub Evo (active subwoofer).
* **Measurement Microphone**:
  * Built-in: Google Pixel 9 Pro (using `MediaRecorder.AudioSource.UNPROCESSED` with factory MEMS compensation).
  * External USB: miniDSP UMIK-1 or Dayton UMM-6 with custom 90-degree diffuse `.cal` calibration file.
* **Mobile Runtime**: Standalone Android application (APK packaged via Capacitor 6) running locally on Android 10+. Zero external server or PC required.

---

## End-to-End Calibration Workflow

### 1. Pre-Flight Check & Microphone Profile
1. Launch the **Octave** app on the Android device connected to the home Wi-Fi network.
2. The app detects the Yamaha receiver via SSDP/subnet probing. Confirm the top status bar displays the receiver as **Online** with current volume and input selector.
3. In **Step 1 (Setup & Canales)**, choose your speaker topology:
   * **2.0 Estéreo**: Bookshelf speakers only.
   * **2.1 Subwoofer**: Bookshelf speakers + Focal Cub Evo active subwoofer.
4. Select the microphone profile or tap **Importar Archivo .cal** to upload an official laboratory calibration file.

### 2. Multi-Point Sweep Measurement
1. In **Step 2 (Medición Móvil)**, place the phone at listening height in the primary sweet spot (Punto 1).
2. Choose audio excitation delivery:
   * **Physical Line-Out (Recommended)**: Connect USB-C/3.5mm cable from phone to receiver front panel `V-AUX` for sub-millisecond DAC synchronization.
   * **Wireless DLNA**: Stream sweeps over local Wi-Fi to Yamaha's media renderer.
3. Tap **Iniciar Medición**. The app plays a 5-second 48 kHz Farina logarithmic sine sweep, captures uncompressed 16-bit PCM audio, runs on-device FFT deconvolution, and computes:
   * Direct arrival delay (ms) and calculated speaker distance (m).
   * Peak signal level (dBFS) and Signal-to-Noise Ratio (SNR $\ge 14\text{ dB}$).
   * Calibrated frequency response with 1/12-octave psychoacoustic smoothing.
4. (Optional) Repeat for peripheral points (2 to 5) to compute a complex vector spatial average.

### 3. Subwoofer Alignment (2.1 Topology Only)
1. In **Step 3 (Graves & Focal)**, review the crossover recommendation (80 Hz default for Q Acoustics 3020i).
2. The engine evaluates the acoustic time-of-flight difference between mains and subwoofer to recommend phase ($0^\circ$ or $180^\circ$).
3. Fine-tune subwoofer trim level in discrete $0.5\text{ dB}$ steps.

### 4. Target Voicing & Discrete PEQ Optimization
1. In **Step 4 (Perfil & PEQ)**, choose an acoustic target curve:
   * **Harman In-Room**: Controlled warm bass shelf (+2.5 dB) with gradual high-frequency roll-off (-0.8 dB/oct).
   * **B&K 1974**: Classic linear downward acoustic tilt.
   * **Linear Flat**: Studio reference response.
2. The optimizer identifies dominant standing wave resonances below 500 Hz and calculates 7 discrete peaking filter biquads per channel strictly mapped to Yamaha discrete hardware frequencies and Q factors.

### 5. Atomic Hardware Deployment & Verification
1. In **Step 5 (Yamaha & Verif)**, tap **Desplegar a Yamaha**. The discrete filter matrix is transmitted via YNC XML over HTTP directly to the receiver's NVRAM, and PEQ mode is set to `Manual`.
2. Tap **Medición de Verificación** to record a post-calibration verification sweep.
3. Review the interactive comparison overlay:
   * **Layer 1 (Medición Base)**: Raw uncalibrated room response.
   * **Layer 2 (Curva Objetivo)**: Selected acoustic target.
   * **Layer 3 (Filtros PEQ)**: Combined biquad transfer function.
   * **Layer 4 (Verificación)**: Actual post-calibration measured response proving modal peak attenuation.

---

## Live Hardware Remote & Auditioning (`AvrRemoteView.tsx`)

Navigate to the **AVR Remote** tab for day-to-day operation and instant A/B subjective auditing:
* **Haptic Master Volume Dial**: Rotate the precision dial to adjust receiver master volume in exact $\pm 0.5\text{ dB}$ steps with 60 ms reactive debounce.
* **Instant A/B DSP Toggle**: Switch between `Manual PEQ` (calibrated sound) and `Through` (unprocessed bypass) to hear the acoustic improvement in real time.
* **Disaster Recovery Rollback**: Tap **Rollback NVRAM** at any time to restore the pre-calibration receiver configuration saved during session pre-flight.

---

## Build, Test & Development Commands

```bash
# Run unit tests validating on-device Farina deconvolution and FFT math
cd frontend
bun test

# Run offline mathematical DSP regression tests
pytest tests/test_peq_biquad_math.py tests/test_fft_parity.py tests/test_audit_zero_hardcode.py

# Build production TypeScript web bundle
bun run build

# Synchronize web assets to native Android container
bun x cap sync android

# Compile standalone debug APK
cd android
./gradlew assembleDebug
# Generated APK: frontend/android/app/build/outputs/apk/debug/app-debug.apk (8.4 MB)
```
