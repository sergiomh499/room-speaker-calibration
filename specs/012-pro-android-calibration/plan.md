# Implementation Plan: Professional Standalone Android Acoustic Calibration Suite

**Branch**: `012-pro-android-calibration` | **Date**: 2026-10-09 | **Spec**: [specs/012-pro-android-calibration/spec.md](spec.md)

**Input**: Feature specification from `/specs/012-pro-android-calibration/spec.md`

## Summary

Deliver a dedicated, professional-grade, standalone Android mobile calibration suite for domestic listening environments (Yamaha RX-V673 AVR + Q Acoustics 3020i + Focal Cub Evo subwoofer) that runs entirely on-device without any PC or background server dependency. The application performs real on-device digital deconvolution of Farina logarithmic sine sweeps using Fast Fourier Transforms and fractional-octave psychoacoustic smoothing, completely eliminating synthetic or randomized placeholder curves. It provides dual-mode sweep excitation (physical AUX line-out and wireless UPnP/DLNA casting), enforces discrete Yamaha hardware DSP parameter quantization (28 bands, 14 Qs, 0.5 dB gain steps, +3 dB max boost, 0 dB boost above 500 Hz), provides an interactive closed-loop before-and-after comparison overlay, adds a dedicated AVR hardware remote control tab, and purges auxiliary internet radio streaming bloat.

## Technical Context

**Language/Version**: TypeScript 5.3+, Java 17 (Android Native Plugins), Python 3.10+ (offline reference DSP math & ground-truth validation).

**Primary Dependencies**:
- Frontend / Mobile UI: React 18, Vite 6, TailwindCSS, Lucide React, Three.js (spatial room visualization), canvas-confetti.
- Native Android Bridge: Capacitor 6 (`@capacitor/core`, `@capacitor/android`, `@capacitor/http`, `@capacitor/filesystem`).
- Native Plugins: `RawAudioRecorderPlugin.java` (uncompressed 48 kHz PCM audio recording via `AudioRecord`), `AvrDiscoveryPlugin.java` (UDP SSDP/subnet discovery).

**Storage**:
- Structured Database (IndexedDB / LocalStorage): Session metadata, discrete 7-band PEQ biquads, calibrated response vectors (100–300 frequency bins), and acoustic metrics.
- App-Private Sandboxed Storage: Raw PCM/WAV sweeps and windowed Room Impulse Response (RIR) Float32 buffers.
- Public Device Storage (`Documents/OctaveCalibrations/`): Exported self-contained ZIP archives (JSON, CSV curves, PDF report).

**Testing**:
- DSP Math & Offline Verification: Pytest suite (`tests/test_peq_biquad_math.py`, `tests/test_peq_optimizer_ground_truth.py`, `tests/test_audit_zero_hardcode.py`).
- Mobile Frontend Unit / Contract Tests: Vitest / Bun test (`frontend/src/services/__tests__/dspEngine.test.ts`).
- End-to-End Validation: Manual & emulated mobile execution covering live YNC XML commands, audio deconvolution, and closed-loop verification.

**Target Platform**: Android 10+ (API Level 29+, optimized for Android 14+ on Google Pixel 9 Pro).

**Project Type**: Standalone Mobile Application (Hybrid Capacitor Android container packaging React SPA).

**Performance Goals**:
- On-device Farina deconvolution and 65,536-point real FFT: $< 2.5\text{ s}$ per sweep on mobile hardware (benchmarked at ~120–160 ms on ARM64).
- Master volume adjustment latency: $< 60\text{ ms}$ debounce with instant reactive UI feedback.
- Interactive acoustic chart rendering: $< 100\text{ ms}$ response on touch pan/zoom and curve toggles.
- End-to-end full 2.1 calibration completion: $< 5\text{ minutes}$.

**Constraints**:
- Strict Zero-Synthetic Invariant: 100% of displayed acoustic curves must derive deterministically from measured audio samples; zero `Math.random()` or hardcoded offsets.
- Discrete Hardware DSP Quantization: All filter frequencies snapped to `YAMAHA_FREQS` (28 values), Q factors to `YAMAHA_QS` (14 values), gains to $[-12.0, +3.0]\text{ dB}$ ($0.5\text{ dB}$ steps), and maximum boost $\le 0.0\text{ dB}$ above $500\text{ Hz}$.
- Zero Server Dependency: Fully functional offline on the local Wi-Fi subnet without requiring an external PC, Python daemon, or cloud service.

**Scale/Scope**: Single listening room, 2.0 or 2.1 speaker setup, 1 to 5 spatial measurement positions, 4 primary application navigation views.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Requirement | Plan Alignment | Status |
|---|---|---|:---:|
| **I. Hardware-First — No Simulated State** | All AVR reads/writes must target real hardware over network; no mock state | Direct YNC XML over HTTP via CapacitorHttp natively without CORS. All curves derive from real deconvolution; zero synthetic curve generation. | **PASS** |
| **II. Non-Destructive Telemetry** | Polling endpoints must be read-only; no state change side effects | Basic_Status queries are read-only GET commands. Sound program, input, and volume changes occur exclusively on explicit user actions. | **PASS** |
| **III. Profile-Scoped Verification** | Verification sweeps & comparisons scoped to active profile key | Verification records and comparative overlays are indexed by profile key (`harman_wide_room`, `bk_1974`, etc.). | **PASS** |
| **IV. Measurement Immutability & Traceability** | Raw captures immutable; re-runs produce new timestamped records | Every measurement capture generates a unique UUID and timestamped file. Historical records cannot be silently overwritten. | **PASS** |
| **V. Minimum Viable Command Surface** | Targeted single-parameter writes; no scene recall for DSP changes | PEQ mode, volume, trims, and filter biquads use atomic targeted XML writes without touching unrelated inputs or scenes. | **PASS** |

## Project Structure

### Documentation (this feature)

```text
specs/012-pro-android-calibration/
├── spec.md              # Feature specification with clarifications
├── plan.md              # Implementation plan (this file)
├── research.md          # Phase 0 technical research decisions
├── data-model.md        # Phase 1 domain entities, schemas, and state transitions
├── quickstart.md        # Phase 1 runnable verification guide
└── contracts/           # Phase 1 interface contracts
    ├── audio-deconvolution-contract.md
    ├── yamaha-ync-protocol-contract.md
    └── calibration-export-contract.md
```

### Source Code Layout

```text
frontend/
├── src/
│   ├── views/
│   │   ├── CalibrateView.tsx      # 5-step guided calibration wizard
│   │   ├── AvrRemoteView.tsx      # NEW: Dedicated AVR Hardware Control & Diagnostics
│   │   ├── AcousticCurvesView.tsx # NEW: Real before/after comparative acoustic chart overlay
│   │   ├── HistoryView.tsx        # Calibration session archives & 1-tap export
│   │   └── SettingsView.tsx       # Microphone selection, .cal import, network config
│   ├── components/
│   │   ├── charts/
│   │   │   ├── FrequencyGraph.tsx # Interactive real-data frequency response graph
│   │   │   ├── PEQFilterGraph.tsx # Discrete 7-band Yamaha biquad response graph
│   │   │   └── SpatialRoom3D.tsx  # Three.js 3D room listening geometry visualization
│   │   ├── layout/
│   │   │   ├── Topbar.tsx         # AVR connection status, power, quick volume chip
│   │   │   └── BottomNav.tsx      # 4-tab mobile navigation (Calibrate, Remote, Curves, History)
│   │   └── ui/
│   │       ├── VUMeter.tsx        # Real-time microphone input level indicator
│   │       ├── HapticDial.tsx     # 0.5 dB rotary master volume dial
│   │       └── Card.tsx, Button.tsx, Pill.tsx
│   ├── services/
│   │   ├── dspEngine.ts           # On-device Farina deconvolution, real FFT, smoothing, PEQ optimizer
│   │   ├── yamahaDirect.ts       # YNC XML HTTP driver via CapacitorHttp with 60ms debounce
│   │   ├── nativeAudio.ts        # Bridge to RawAudioRecorderPlugin for 48 kHz PCM capture
│   │   ├── exportService.ts       # NEW: ZIP/CSV/PDF session archive exporter
│   │   └── avrDiscovery.ts       # UDP SSDP / subnet receiver auto-detection
│   ├── context/
│   │   └── CalibrationContext.tsx # Central state store for active session, points, and AVR status
│   └── types/
│       └── index.ts               # Domain TypeScript interfaces and types
├── android/
│   └── app/src/main/
│       ├── AndroidManifest.xml   # Audio recording and network permissions
│       └── java/com/octave/roomcalibration/
│           ├── MainActivity.java
│           ├── RawAudioRecorderPlugin.java # 48 kHz uncompressed audio recording
│           └── AvrDiscoveryPlugin.java     # Subnet AVR discovery
└── dist/                          # Production bundle compiled via `bun run build`
```

## Complexity Tracking

> **No Constitution violations exist. All gates passed cleanly.**
