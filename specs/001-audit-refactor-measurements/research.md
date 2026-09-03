# Phase 0 Research & Technical Decisions: Comprehensive Acoustic Engine Audit & Refactor

**Feature Branch**: `001-audit-refactor-measurements`  
**Date**: 2026-09-03  
**Status**: Approved / Consolidated

---

## 1. Parametric EQ Optimization Algorithm for Discrete Hardware Constraints

### Decision
Implement a **two-stage modal peak identification and discrete non-linear least squares (NLLS) optimization** with hardware parameter snapping:
1. **Stage 1 (Resonance Detection)**: Identify dominant minimum-phase modal peaks below 500 Hz using smoothed logarithmic frequency derivative analysis and peak prominence detection on the weighted acoustic curve ($80\%$ Sweet Spot, $20\%$ spatial average).
2. **Stage 2 (Biquad Optimization)**: Allocate up to 7 biquad peaking filters per channel ($f_{0,L} \neq f_{0,R}$). Fit continuous $(f_0, Q, \text{gain})$ parameters using constrained Levenberg-Marquardt or Sequential Least Squares Programming (SLSQP) bounded to:
   - $f_0 \in [62.5, 500.0]\text{ Hz}$ (or up to $16.0\text{ kHz}$ if explicitly configured, but gain constrained to $\le 0.0\text{ dB}$ above $500\text{ Hz}$).
   - $\text{gain} \in [-12.0, +3.0]\text{ dB}$.
   - $Q \in [0.500, 10.080]$.
3. **Stage 3 (Discrete Quantization & Fine Retuning)**: Snap each continuous filter parameter to the nearest allowable discrete Yamaha RX-V673 hardware value (from the 28 frequencies, 14 Q factors, and 0.5 dB gain steps). Perform a discrete coordinate descent or greedy 1-step swap to ensure quantization rounding does not induce constructive interference or adjacent dips.

### Rationale
- Pure gradient descent fails because the Yamaha RX-V673 DSP rejects arbitrary float values (it only accepts 28 fixed frequencies and 14 Q factors).
- Pure brute-force combinatorial search over $28^7 \times 14^7 \times 37^7$ possibilities is computationally prohibitive ($\sim 10^{32}$ combinations).
- Stage 1 anchors the filters to physically verified physical room modes (minimum phase peaks).
- Stage 2 converges in $< 500\text{ ms}$ in Python via `scipy.optimize`.
- Stage 3 guarantees $100\%$ hardware compliance in $< 200\text{ ms}$ while minimizing residual RMS target error.

### Alternatives Considered
- **Direct Generic REW Export Simulation**: Rejected because it relies on external manual GUI interaction rather than fully automated reproducible code execution.
- **Genetic Algorithm / Differential Evolution**: Evaluated; rejected due to nondeterministic execution times and potential convergence beyond the 10-second test constraint.
- **Static Pre-calculated Table Lookup**: Strictly rejected per Constitution Principle I and User Story 1 (honest acoustic calibration).

---

## 2. Cumulative Spectral Decay (CSD / Waterfall) Computation

### Decision
Compute the time-domain Cumulative Spectral Decay (CSD) directly from the deconvolved Room Impulse Response (RIR) using a **sliding window short-time Fourier transform (STFT)**:
- **Window Type**: Hann or Blackman-Harris window of length $N = 2048$ samples ($42.7\text{ ms}$ at $48\text{ kHz}$) with zero-padding to $N_{\text{fft}} = 8192$ for smooth spectral interpolation.
- **Temporal Slice Count**: 30 slices covering a decay interval from $t = 0\text{ ms}$ to $t = 300\text{ ms}$ ($10\text{ ms}$ step size per slice).
- **Frequency Range**: Focused on the modal zone: $20\text{ Hz}$ to $500\text{ Hz}$ (with optional full-band display up to $20\text{ kHz}$).
- **Dynamic Range Floor**: $35\text{ dB}$ down from the initial arrival peak.
- **Output Visualization**: Rendered via Matplotlib 3D isometric surface projection and vectorized SVG/PNG for integration into HTML/PDF technical audit reports.

### Rationale
- Minimum-phase room resonances (standing waves between room boundaries) are characterized by prolonged temporal ringing (high Q decay).
- While magnitude frequency response shows peak height, CSD proves whether parametric notch filters actually suppressed the resonant energy storage in the room over time.
- Verifying ringing decay under $300\text{ Hz}$ provides irrefutable physical proof of correction success.

### Alternatives Considered
- **Wavelet Scalogram (Continuous Wavelet Transform)**: Evaluated; provides excellent time-frequency resolution but is computationally heavier and less standard in electroacoustic literature than CSD.
- **Static 2D Magnitude Overlay Only**: Rejected per user clarification requiring verifiable temporal decay evidence.

---

## 3. Calibration Epoch Versioning and Dataset Schema

### Decision
Structure calibration data into **numbered, immutable epoch directories** under `data/calibrations/epochs/`:
```text
data/calibrations/epochs/
├── epoch_000_baseline_20260903_190000/
│   ├── manifest.json
│   ├── rir_sweep_left.npz
│   ├── rir_sweep_right.npz
│   └── hardware_state_readback.xml
├── epoch_001_peq_harman_20260903_193000/
│   ├── manifest.json
│   ├── peq_matrix.json
│   ├── rir_sweep_left.npz
│   ├── rir_sweep_right.npz
│   ├── hardware_state_readback.xml
│   └── audit_report.html
└── active_manifest.json (symlink / pointer to current verified epoch)
```
- Each `manifest.json` contains:
  - `epoch_id`: Sequential integer (`0, 1, 2, ...`).
  - `stage`: Stage label (`baseline`, `initial_peq`, `refined_notch`, `final_certified`).
  - `timestamp`: ISO-8601 UTC.
  - `profile_key`: Acoustic target curve name.
  - `peq_filters`: 7 bands per channel with $(f_0, Q, \text{gain})$.
  - `metrics`: Peak modal attenuation, residual RMS error ($60-500\text{ Hz}$), inter-channel delta, SNR, and S-TIER certification status.
  - `provenance`: File hashes (SHA-256) of raw impulse sweeps and receiver XML readback.

### Rationale
- Adheres to Constitution Principle IV (Measurement Immutability and Traceability).
- Eliminates any risk of destructive overwriting of baseline captures.
- Allows automated mathematical diffing and step-by-step convergence graphs between Epoch $N$ and Epoch $N-1$.

### Alternatives Considered
- **Single Monolithic SQLite Database**: Over-engineered for a local embedded/desktop acoustic pipeline; `.npz` + `.json` files are natively transparent, git-friendly for config, and directly inspectable by standard scientific Python libraries.
- **Unindexed Overwrite Files**: Strictly prohibited by constitution and specification.

---

## 4. Hardware Transaction Protocol & Readback Verification (Yamaha RX-V673)

### Decision
Enforce a **Write-Commit-Readback Transaction Loop** for all AVR PEQ parameters via Yamaha Network Control (YNC) XML API:
1. **Prepare Payload**: Construct atomic XML command targeting `<System><Speaker_Preout><PEQ><Manual>`.
2. **Execute PUT**: Send HTTP POST to `http://192.168.1.43/YamahaRemoteControl/ctrl` with timeout of $3.0\text{ s}$.
3. **Assert Return Code**: Check `<YAMAHA_AV cmd="PUT" RC="0">`.
4. **Hardware Readback Verification**: Issue a GET request to `http://192.168.1.43/YamahaRemoteControl/ctrl` querying `<System><Speaker_Preout><PEQ><Manual>GetParam</Manual></System>`.
5. **Exact Match Assertion**: Compare returned XML biquad values $(f_0, Q, \text{gain})$ against the intended matrix. If any band diverges or fails to commit, raise a `HardwareCommitError` and abort calibration progression.

### Rationale
- Prevents silent DSP packet drop or partial memory corruption in the receiver's NVRAM.
- Guarantees that acoustic verification sweeps measure the exact filters designed by the optimizer.
- Adheres to Constitution Principle I (Hardware-First).
