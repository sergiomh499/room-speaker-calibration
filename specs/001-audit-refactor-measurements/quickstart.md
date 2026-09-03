# Quickstart Validation Guide: Acoustic Engine Audit & Honest Calibration

**Feature Branch**: `001-audit-refactor-measurements`  
**Date**: 2026-09-03  
**Status**: Ready

---

## 1. Overview & Prerequisites

This quickstart guides you through validating the refactored, honest acoustic calibration pipeline:
1. **Zero Fake Calculations**: Proof that all filter solutions are computed dynamically from empirical impulse response data.
2. **Discrete Yamaha DSP Compliance**: Ensuring all 7 bands match allowable RX-V673 frequencies, Q factors, and gains.
3. **Structured Calibration Epochs**: Running sequential iterations (Baseline → PEQ → Refined) and observing convergence.
4. **Comprehensive Technical Audit**: Inspecting CSD waterfall decay, hardware register dumps, and S-TIER certification criteria.

### System Requirements
* Python 3.11+ with `numpy`, `scipy`, `matplotlib`.
* Yamaha RX-V673 reachable at `http://192.168.1.43/` via local network.
* Measurement microphone connected via ALSA/USB (for physical sweeps) OR recorded raw `.npz` impulse responses for offline audit mode.

---

## 2. Automated Test Suite (Syntax & Optimization Convergence)

Run the fast automated audit suite to verify mathematical convergence and discrete hardware limits:

```bash
# 1. Compile check all core calibration modules
python3 -m py_compile \
  scripts/peq_optimizer.py \
  scripts/csd_waterfall.py \
  scripts/calibration_epoch.py \
  scripts/verify_calibration.py \
  scripts/web_calibration_server.py

# 2. Run the algorithmic unit & integration test suite (must finish in < 10 seconds)
pytest tests/test_peq_optimizer.py tests/test_calibration_epoch.py tests/test_csd_waterfall.py -v
```

**Expected Outcome**:
* All test cases pass in under 10 seconds.
* 100% of tested filter parameters adhere to discrete Yamaha RX-V673 matrix limits.
* Zero synthetic simulated curves (`measurement + filter`) are produced.

---

## 3. Step-by-Step Iterative Epoch Validation

### Step 3.1: Initialize Epoch 0 (Baseline Through Bypass)
Capture the baseline physical response without any active equalization:

```bash
python3 scripts/calibration_epoch.py init-baseline \
  --profile harman_wide_room \
  --desc "Baseline Through Mode Uncalibrated"
```

**Expected Outcome**:
* An immutable directory is created: `data/calibrations/epochs/epoch_000_baseline_<timestamp>/`.
* `manifest.json` logs `stage: "baseline"`, raw impulse files, and baseline modal resonance peaks.

### Step 3.2: Run Dynamic PEQ Optimization
Calculate the optimal 7-band discrete filter matrix from the baseline sweep:

```bash
python3 scripts/peq_optimizer.py optimize \
  --epoch 0 \
  --profile harman_wide_room \
  --sweet-spot-weight 0.8
```

**Expected Outcome**:
* Discrete filters computed in $< 3.0\text{ s}$ per channel.
* Channel-independent frequencies ($f_{0,L} \neq f_{0,R}$) targeting asymmetric room modes.
* Boost clamped to $\le +3.0\text{ dB}$, and zero boost above $500\text{ Hz}$.

### Step 3.3: Deploy Filters & Verify Hardware Readback
Send the filter matrix to the physical Yamaha RX-V673 and verify commit:

```bash
python3 scripts/calibration_epoch.py deploy --epoch 1
```

**Expected Outcome**:
* HTTP POST sent to `http://192.168.1.43/YamahaRemoteControl/ctrl`.
* Readback XML query verifies that 100% of the 14 biquad bands in receiver NVRAM match the optimizer values.

### Step 3.4: Perform Verification Sweep & Generate Technical Audit Report
Execute the post-calibration verification sweep and build the complete audit suite:

```bash
python3 scripts/verify_calibration.py verify \
  --epoch 1 \
  --profile harman_wide_room
```

**Expected Outcome**:
* Authentic post-calibration physical sweep recorded and saved to Epoch 1.
* Technical report generated (`report_epoch_001.html`) containing:
  - 1/24-octave & psychoacoustic magnitude curves with target overlays.
  - 3D Cumulative Spectral Decay (CSD) waterfall plot demonstrating modal ringing suppression below $300\text{ Hz}$.
  - Verified hardware register dump.
  - S-TIER certification badge awarded **only** if modal reduction $\ge 6.0\text{ dB}$, RMS error $< 2.5\text{ dB}$, and stereo imbalance $< 2.0\text{ dB}$.
