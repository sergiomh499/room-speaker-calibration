# Quickstart & Verification Guide: Professional Standalone Android Calibration Suite

**Feature Branch**: `012-pro-android-calibration`
**Date**: 2026-10-09

## Prerequisites & Environment
- **Node/Bun Environment**: Bun (>=1.1) or Node.js (>=18).
- **Android Toolchain**: Android SDK 33+, JDK 17, ADB.
- **Hardware Targets**:
  - Android Device: Google Pixel 9 Pro (or Android emulator running API 34).
  - Audio Receiver: Yamaha RX-V673 connected to local Wi-Fi (`192.168.1.43`).
  - Speakers: Q Acoustics 3020i (Left/Right) + Focal Cub Evo (Subwoofer).

---

## Scenario 1: Deterministic Real Acoustic Math & Zero-Synthetic Audit
Validates that on-device deconvolution and frequency extraction compute genuine physical acoustics and contain zero `Math.random()` or hardcoded offsets.

```bash
# 1. Run DSP unit tests validating RBJ biquad math and real FFT
pytest tests/test_peq_biquad_math.py
pytest tests/test_peq_optimizer_ground_truth.py
pytest tests/test_audit_zero_hardcode.py

# 2. Verify frontend DSP engine exports deterministic responses
cd frontend
bun test
```
**Expected Outcome**: 100% of mathematical tests pass. Zero synthetic or random curve generators detected.

---

## Scenario 2: Frontend Production Build & Capacitor Android Sync
Compiles the React TypeScript single-page application into production assets and synchronizes native Android assets.

```bash
cd frontend

# Clean build of TypeScript and Vite bundle
bun run build

# Synchronize web assets with Android native project
bun x cap sync android
```
**Expected Outcome**: Production bundle compiled into `frontend/dist/` without TypeScript compiler warnings; native assets copied to `frontend/android/app/src/main/assets/public/`.

---

## Scenario 3: End-to-End Mobile Calibration Run (Live or Emulated)
Tests the complete standalone mobile calibration lifecycle from discovery to verification.

1. **Launch Mobile Application**:
   ```bash
   # Optional: Launch in connected Android device or emulator via ADB
   cd frontend/android
   ./gradlew installDebug
   adb shell am start -n com.octave.roomcalibration/.MainActivity
   ```
2. **Step 1 - Setup & Discovery**:
   - Verify AVR status card shows `192.168.1.43` online, master volume, and current input (`AV4`).
   - Select Microphone: Internal Pixel 9 Pro (Unprocessed) or USB UMIK-1.
3. **Step 2 - Acoustic Sweep Measurement**:
   - Tap "Iniciar Medición" for Point 1 (Sweet Spot).
   - Observe countdown cue and playback of 48 kHz Farina logarithmic sine sweep.
   - Verify diagnostic card: Peak level $\approx -12\text{ dBFS}$, $\text{SNR} \ge 25\text{ dB}$, calculated speaker distance displayed in meters.
   - Confirm rendered frequency response displays true physical room curve with modal resonance peak.
4. **Step 3 - Discrete PEQ Optimization**:
   - Select target profile (e.g., `harman_wide_room`).
   - Observe 7 generated PEQ bands strictly snapped to discrete Yamaha frequencies and Q factors.
   - Verify modal notch filter placed at room mode with gain clamped $\le +3.0\text{ dB}$ (and $\le 0.0\text{ dB}$ above 500 Hz).
5. **Step 4 - Atomic NVRAM Deployment & Verification**:
   - Tap "Desplegar a Yamaha".
   - Confirm AVR receiver receives YNC XML payload and sets PEQ mode to `Manual`.
   - Tap "Medición de Verificación".
   - Review interactive chart: Confirm overlay displays (1) Pre-calibration curve, (2) Target curve, (3) Filter biquad response, and (4) Real post-calibration verification curve showing modal peak reduction.

---

## Scenario 4: Safety Rollback Verification
Tests that user abort restores original AVR state without leaving partial filter configurations.

1. Note original receiver volume and PEQ mode.
2. Start calibration session (which captures pre-flight snapshot).
3. Tap "Cancelar y Restaurar".
4. Confirm receiver status read-back shows exact original settings restored within 2 seconds.
