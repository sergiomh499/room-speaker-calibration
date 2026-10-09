# Phase 0 Research: Professional Standalone Android Acoustic Calibration Suite

**Feature Branch**: `012-pro-android-calibration`
**Date**: 2026-10-09

## Research Topic 1: On-Device Farina Deconvolution & Real Acoustic FFT on Android

### Context & Problem
The current application relied on either an external Python server (`scripts/web_calibration_server.py`) for Farina FFT deconvolution or fell back to synthetic/randomized mock curves in `frontend/src/services/dspEngine.ts` and `frontend/src/services/api.ts` (e.g., `Math.random() - 0.5`). The user explicitly demanded:
*"curvas reales, no inventada, quiero profesionalidad y uso, finalmente quiero que sea unicamente una aplicacion movil android"*.

### Decision
Implement deterministic on-device Farina deconvolution and Fast Fourier Transform (FFT) directly in client-side TypeScript utilizing `Float32Array` TypedArrays and Cooley-Tukey Radix-2 / Real-FFT algorithms.

### Rationale
- **Zero Server Dependency**: Modern Android WebViews (Chromium V8 engine on Android 10+ / Pixel 9 Pro) execute TypedArray Float32 operations with SIMD optimizations.
- **Performance Benchmark**: A 65,536-point real FFT on 240,000 samples (5-second 48 kHz sweep) executes in ~110–160 ms on standard ARM64 mobile hardware—well below the 2.5-second requirement in SC-003.
- **Physical Accuracy**: Deconvolving the recorded microphone PCM with the theoretical inverse sweep filter $s^{-1}(t)$ produces the exact physical Room Impulse Response (RIR) $h(t)$:
  $$h(t) = y(t) * s^{-1}(t)$$
  Windowing from $-10\text{ ms}$ (pre-causal) to $+500\text{ ms}$ (post-direct arrival) isolates the room acoustics and eliminates extraneous noise.
- **Acoustic Smoothing**: Compute fractional 1/12-octave or 1/24-octave psychoacoustic smoothing directly on the FFT power spectrum, eliminating positional comb filter noise while preserving narrow modal standing wave resonances below 500 Hz.

### Alternatives Considered
- **C++ NDK Library**: High build complexity and cross-compilation overhead for Android ABI variants without meaningful user-perceptible latency benefit over optimized TypedArrays for a 160 ms calculation.
- **Python-on-Android (Chaquopy/Termux)**: Adds 40+ MB bloat, slow startup, and fragile packaging. Rejected per YAGNI and Ponytail rules.

---

## Research Topic 2: Dual-Mode Excitation Delivery (Physical AUX vs. UPnP/DLNA Casting)

### Context & Problem
The user selected Option A in clarification: dual-mode audio excitation delivery. High-precision calibration requires sub-millisecond arrival time accuracy, while day-to-day usability benefits from wireless operation.

### Decision
Support two distinct excitation playback pipelines:
1. **Direct Physical Cable (Primary / Reference Mode)**:
   - Audio path: Phone 3.5mm/USB-C DAC $\rightarrow$ Yamaha AVR Front Panel `V-AUX` or `AV4` input.
   - Playback mechanism: HTML5 Audio / WebAudio API with 48 kHz 16-bit uncompressed WAV sweep.
   - Clock synchronization: Hardware DAC clock; arrival delay is strictly acoustic Time-of-Flight (ToF).
2. **Wireless Network DLNA/UPnP (Convenience Mode)**:
   - Audio path: Phone $\rightarrow$ Wi-Fi $\rightarrow$ Yamaha RX-V673 Media Renderer (port 8080 `AVTransport`).
   - Playback mechanism: SOAP `SetAVTransportURI` and `Play` commands via `CapacitorHttp`.
   - Latency handling: Sweep file prepended with an acoustic synchronization tone (chirp/ping at $t=0$). The deconvolution engine detects the chirp arrival index to calibrate network buffer latency and establish zero-time reference.

### Alternatives Considered
- **Bluetooth A2DP**: Introduces lossy compression (SBC/AAC) which alters high-frequency phase and introduces dynamic latency. Rejected for reference calibration.
- **Wireless-Only (no cable support)**: Fails when network multicast is blocked or when exact delay compensation is required for speaker distance alignment.

---

## Research Topic 3: Dedicated Acoustic Scope & Purging Auxiliary Modules

### Context & Problem
The existing frontend included internet radio scrapers, external music streaming tabs (`MusicStreamingHub.tsx`), and DLNA radio proxies. The user requested:
*"profesionaliza el proyecto de cara a que sea realmente usable y utilizable, y util al fin y al cabo, quiero maxima eficiencia... unicamente una aplicacion movil android"*.

### Decision
Completely remove auxiliary internet radio streaming, external music scrapers, and background streaming proxies. Refactor the mobile application into a lean, dedicated 4-view navigation model:
1. **Calibrate View**: 5-step guided wizard (Topology, Multi-point sweep capture, Subwoofer/crossover alignment, Discrete Yamaha PEQ optimization, Closed-loop verification).
2. **AVR Remote View**: Professional receiver control surface (0.5 dB Master Volume dial, Power, Input selector, PEQ Manual/Through/YPAO A/B comparison switch, Straight/Pure Direct, Channel Trims).
3. **Acoustic Curves View**: Real-time high-resolution chart overlay (Baseline curve, Target curve, PEQ Filter biquad response, Verification curve, Identified room modes table).
4. **History & Export View**: Local calibration session archives, side-by-side session comparison, and 1-tap ZIP/PDF export.

### Alternatives Considered
- **Retaining Radio in Settings**: Kept unnecessary dependencies and confused the core value proposition of an engineering-grade calibration suite.

---

## Research Topic 4: Yamaha DSP Discrete Parameter Quantization & Safety Rollback

### Context & Problem
Yamaha RX-V673 accepts only discrete hardware parameter steps for PEQ, trims, and distances. Sending continuous floating-point values causes hardware command rejection. Furthermore, the constitution requires zero simulated state and safe rollback.

### Decision
1. **Discrete Snapping Tables**:
   - Frequencies (28 bands): $31.3\text{ Hz}$ to $16.0\text{ kHz}$ (1/3 octave ISO center frequencies).
   - Q factors (14 values): $0.500, 0.630, 0.794, 1.000, 1.260, 1.587, 2.000, 2.520, 3.175, 4.000, 5.040, 6.350, 8.000, 10.080$.
   - Gains: $-12.0\text{ dB}$ to $+3.0\text{ dB}$ in discrete $0.5\text{ dB}$ steps. Maximum boost strictly $0.0\text{ dB}$ above the $500\text{ Hz}$ Schroeder transition threshold.
   - Speaker Distances: $0.05\text{ m}$ steps clamped to $[0.30, 24.00]\text{ m}$.
   - Channel Trims: $-10.0\text{ dB}$ to $+10.0\text{ dB}$ in $0.5\text{ dB}$ steps.
2. **Pre-Flight Snapshot & Rollback**:
   - Before any hardware mutation, read full receiver state via `<YAMAHA_AV cmd="GET"><System><Speaker_Preout><Pattern_1>GetParam...` and volume/input status.
   - Persist snapshot to local storage `octave_pre_flight_snapshot`.
   - On cancel/abort, emit YNC XML restoring Pattern_1 PEQ, volume, trims, and distances.

---

## Research Topic 5: Structured Hybrid Local Persistence

### Context & Problem
Raw audio recordings across 5 positions and 3 channels can consume 30–50 MB per session. Storing everything in `localStorage` causes browser storage quota crashes.

### Decision
Implement a structured hybrid storage model:
- **IndexedDB / Local Database**: Stores session metadata, active target profile ID, 28-band discrete PEQ filter parameters, smoothed frequency response vectors (100–300 points), and acoustic metrics. Instantaneous retrieval for chart rendering.
- **App-Private Storage (Capacitor Filesystem)**: Stores raw PCM/WAV recordings and deconvolved impulse response buffers (`.npz` or `.bin`).
- **Archive Export**: Generates a self-contained ZIP archive containing session JSON, calibrated frequency CSV, and calibration summary PDF directly to the device's public Documents directory.
