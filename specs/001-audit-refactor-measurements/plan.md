# Implementation Plan: Comprehensive Acoustic Engine Audit, Real Optimization Refactor, and Honest Verification Pipeline

**Branch**: `001-audit-refactor-measurements` | **Date**: 2026-09-03 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/001-audit-refactor-measurements/spec.md`

---

## Summary

Eradicate all synthetic fallback curves, hardcoded filter tables, and fabricated acoustic ratings across the calibration codebase. Replace them with:
1. An empirical 7-band discrete PEQ optimizer for the Yamaha RX-V673 constrained strictly to allowable hardware frequencies and Q values, computing channel-independent center frequencies ($f_{0,L} \neq f_{0,R}$) weighted 80% Sweet Spot and 20% spatial average.
2. A structured Calibration Epoch progression model (`epoch_000_baseline`, `epoch_001_peq`, etc.) storing immutable raw impulse responses and manifests to validate adjustments *a posteriori*.
3. A comprehensive technical audit report suite featuring 1/24-octave & psychoacoustic curves, 3D Cumulative Spectral Decay (CSD) waterfall plots below 300 Hz, exact Yamaha NVRAM register dumps, and strict multi-metric S-TIER certification gating ($\ge 6.0\text{ dB}$ modal cut, $< 2.5\text{ dB}$ RMS error, $< 2.0\text{ dB}$ stereo balance).

---

## Technical Context

**Language/Version**: Python 3.11+ (running Python 3.13 on Linux x86_64)  
**Primary Dependencies**: NumPy (numerical arrays), SciPy (signal processing, biquads, deconvolution, optimization), Matplotlib (CSD waterfall, spectral plots), Requests / standard library `urllib` (YNC XML network control)  
**Storage**: Filesystem-based immutable `.npz` archive files for raw impulse/sweeps, JSON for manifests and profile configurations, SVG/PNG/HTML for technical audit reports  
**Testing**: pytest / standard unittest, `python3 -m py_compile` syntax verification, automated synthetic benchmark suite  
**Target Platform**: Linux (Arch/CachyOS x86_64), local audio hardware (ALSA / USB microphone), Yamaha RX-V673 at `192.168.1.43`  
**Project Type**: CLI scientific tool suite + local HTTP daemon/dashboard (`web_calibration_server.py`)  
**Performance Goals**: Complete automated validation test suite runs in under 10 seconds; PEQ numerical optimization converges in under 3 seconds per channel  
**Constraints**: Discrete Yamaha RX-V673 hardware matrix (28 center frequencies, 14 Q factors, 0.5 dB gain steps up to 7 bands per channel), maximum positive boost $+3.0\text{ dB}$, zero boost above $500\text{ Hz}$, strictly non-simulated live measurements, non-destructive telemetry polling  
**Scale/Scope**: Domestic stereo room calibration pipeline for Q Acoustics 3020i + Yamaha RX-V673 + LG C5  

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle / Rule | Requirement Summary | Status | Design Evaluation & Verification |
|---|---|---|---|
| **Principle I: Hardware-First** | No simulated AVR state or synthetic fallback curves (`measurement + filter`). | **PASS** | Synthetic addition formulas eliminated. Every curve is labeled `REAL_MEASUREMENT` or `THEORETICAL_TARGET`. |
| **Principle II: Non-Destructive Telemetry** | Polling endpoints (`/api/preflight_check`, etc.) MUST be strictly read-only; no PUT commands. | **PASS** | State changes restricted to explicit session actions (`set_full_measurement_mode`); polling is pure GET. |
| **Principle III: Profile-Scoped Verification** | Sweeps and PEQ comparison scoped to active profile key. | **PASS** | Epoch manifests and verification routines are strictly scoped to the active `profile_key`. |
| **Principle IV: Measurement Immutability** | Raw `.npz` files are immutable; no unversioned overwrites. | **PASS** | Numbered directory layout (`epoch_{N}_{stage}_{timestamp}/`) enforces historical immutability. |
| **Principle V: Minimum Viable Command Surface** | Single-parameter writes; no destructive `Scene_Sel` for DSP adjustments. | **PASS** | Direct PEQ manual XML biquad addressing prevents input jumps or volume disruption. |
| **Constraint: 8 Ω MIN Impedance** | Yamaha RX-V673 must remain at 8 Ω MIN. | **PASS** | Enforced in equipment documentation and setup guidelines. |
| **Constraint: 7-Band DSP Limit** | Maximum 7 biquads per channel; no boost above 500 Hz. | **PASS** | Hard limits built into `peq_optimizer.py` and JSON schema validator. |

---

## Project Structure

### Documentation (this feature)

```text
specs/001-audit-refactor-measurements/
├── spec.md              # Feature specification with clarifications
├── plan.md              # This implementation plan
├── research.md          # Phase 0 technical research & algorithmic decisions
├── data-model.md        # Phase 1 domain entities, relationships, & lifecycle
├── quickstart.md        # Phase 1 runnable validation scenarios
├── contracts/           # Phase 1 API schemas
│   ├── peq-optimizer-api.json
│   ├── calibration-epoch-manifest.json
│   └── web-api-endpoints.json
└── checklists/
    └── requirements.md  # Quality validation checklist
```

### Source Code (repository root)

```text
config/
├── equipment.json            # Physical hardware parameters (Yamaha RX-V673, Q Acoustics 3020i)
└── targets.json              # Community target curves (Harman, B&K, Dirac, etc.)

scripts/
├── peq_optimizer.py          # [NEW/REFACTOR] Real dynamic discrete PEQ optimization engine
├── csd_waterfall.py          # [NEW] 3D Cumulative Spectral Decay temporal ringing analyzer
├── calibration_epoch.py      # [NEW] Structured Calibration Epoch versioning and manifest manager
├── 01_measure_sweep.py       # Physical ALSA sweep capture (V-AUX routing, level checks)
├── 04_yamaha_control.py      # Yamaha YNC XML transaction layer (readback verification)
├── verify_calibration.py     # [REFACTOR] Honest audit verification (CSD, register dump, S-TIER gate)
└── web_calibration_server.py # [REFACTOR] Dashboard backend (epoch history, dynamic optimization)

tests/
├── test_peq_optimizer.py     # Fast mathematical convergence and discrete hardware limits test
├── test_calibration_epoch.py # Epoch immutability, manifest hashing, and versioning tests
└── test_csd_waterfall.py     # Temporal ringing STFT decay computation tests

data/
└── calibrations/
    └── epochs/               # Numbered immutable calibration epochs
```

**Structure Decision**: Single project layout matching existing repository conventions. New modular components (`peq_optimizer.py`, `csd_waterfall.py`, `calibration_epoch.py`) encapsulate complex scientific computations, keeping `verify_calibration.py` and `web_calibration_server.py` clean, maintainable, and verifiable.

---

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

*Zero violations. All design choices adhere directly to the project constitution.*
