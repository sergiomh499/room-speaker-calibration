# Implementation Plan: Ground-Truth Empirical PEQ Calibration & Multichannel Architecture

**Branch**: `010-ground-truth-peq-math` | **Date**: 2026-09-04 | **Spec**: [specs/010-ground-truth-peq-math/spec.md](spec.md)

**Input**: Feature specification from `/specs/010-ground-truth-peq-math/spec.md`

## Summary
Re-derive the entire PEQ filter calculation engine from foundational transfer function physics (second-order IIR biquad equations, Robert Bristow-Johnson Audio EQ Cookbook) to replace heuristic approximations and eliminate static offsets. Audit all 9 loaded target curves for 2.0 bookshelf acoustic limits (Q Acoustics 3020i with 64 Hz port tuning), incorporating low-frequency protection and human in-room high-frequency roll-off. Architect the channel routing and optimization structures to seamlessly support future multichannel expansions (2.1, 5.1, 7.1) via modular channel parameterization.

## Technical Context

**Language/Version**: Python 3.10+ (NumPy, SciPy), Vanilla JavaScript (ES6 Modules)
**Primary Dependencies**: `scipy.signal`, `numpy.fft`, `urllib.request`
**Storage**: JSON (`config/targets.json`, `config/hardware.json`), NPZ (`data/medicion_promedio_espacial.npz`)
**Testing**: Python `unittest` suite (`tests/test_peq_optimizer.py`, `tests/test_targets_config.py`, `tests/test_modal_notch_diagnostic.py`)
**Target Platform**: Linux / Yamaha RX-V673 YNC XML API / Chrome/Firefox Mobile & Desktop
**Project Type**: Acoustic DSP Engine & Web Dashboard
**Performance Goals**: < 100ms full stereo biquad optimization, zero UI blocking
**Constraints**: 7 hardware PEQ bands per channel, discrete Yamaha frequency and Q registers, strict anti-boosting of cancellation nulls

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Principle I: Hardware-First (No Simulated State)**: PASS. All biquad evaluations match empirical measurement datasets and snap to exact Yamaha register tables.
- **Principle II: Non-Destructive Telemetry**: PASS. Calibration sweeps and parameter reads maintain receiver integrity.
- **Principle III: Profile-Scoped Verification**: PASS. Biquad optimization derives parameters strictly scoped to the active profile.
- **Principle IV: Measurement Immutability**: PASS. Spatial averages and sweet spot sweeps remain immutable references during solver execution.

## Project Structure

### Documentation (this feature)

```text
specs/010-ground-truth-peq-math/
├── plan.md              # Implementation plan
├── research.md          # RBJ biquad transfer functions, 2.0 target curves, commercial paradigms
├── data-model.md        # Entities: BiquadCoefficients, ChannelCalibrationProfile, SystemAcousticSession
├── quickstart.md        # Validation commands and quick run guide
├── contracts/
│   └── api_contracts.md # REST and hardware synchronization contracts
└── checklists/
    └── requirements.md  # Quality validation checklist
```

### Source Code

```text
scripts/
├── peq_optimizer.py          # Ground-truth biquad solver, modal peak priority, channel parameterization
├── web_calibration_server.py # REST endpoints, multichannel session state, dynamic targets.json sync
└── yamaha_controller.py      # Multi-channel YNC XML command builder (L, R, C, SW, SL, SR, SBL, SBR)
tests/
├── test_peq_biquad_math.py   # Mathematical verification of complex transfer functions
└── test_multichannel_peq.py  # Validation of modular channel allocations and subwoofer crossover routing
```

## Architecture Decisions

| Decision | Rationale | Alternatives Considered |
| :--- | :--- | :--- |
| **Exact RBJ Biquad Equations** | Models complex frequency response and skirt overlap with 100% mathematical fidelity. | Gaussian bell approximation (lacks Nyquist wrapping and phase fidelity). |
| **2.0 Bookshelf Target Curve Protection** | Enforces Butterworth roll-off below 60 Hz to protect 5-inch woofers from excessive excursion. | Full-range flat bass extension (causes mechanical driver distortion). |
| **Peak-Priority Attenuation ($Q \ge 2.0$)** | Attenuates standing wave resonances without boosting destructive room cancellations. | Symmetrical boost/cut equalization. |
| **Modular Channel Parameterization** | Allows instant scaling to 2.1, 5.1, or 7.1 topologies without refactoring core DSP logic. | Hardcoding Left and Right channel indices into the solver. |
