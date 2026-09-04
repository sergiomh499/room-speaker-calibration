# Implementation Plan: Multi-Target Validation & Comparative Acoustic Benchmarking

**Branch**: `011-multi-target-validation` | **Date**: 2026-09-04 | **Spec**: [specs/011-multi-target-validation/spec.md](spec.md)

**Input**: Feature specification from `specs/011-multi-target-validation/spec.md`

## Summary

Unify target curve calculation across the calibration suite, verify that all validation targets include the 4th-order high-pass roll-off for the Q Acoustics 3020i ($f_c = 64\text{ Hz}$), and build a multi-target comparative benchmarking engine. Expose multi-target metrics and curves via API endpoints and interactive web visualization to allow cross-comparing measured curves against alternative reference standards.

## Technical Context

**Language/Version**: Python 3.14  
**Primary Dependencies**: NumPy, SciPy, Matplotlib, ReportLab (PDF)  
**Storage**: NumPy archive binaries (`.npz`) and JSON configuration (`config/targets.json`)  
**Testing**: Python `unittest` (`python3 -m unittest discover -s tests -p "test_*.py"`)  
**Target Platform**: Linux (Arch/CachyOS x86_64), local calibration server at `http://127.0.0.1:53317`  
**Project Type**: Acoustic DSP Optimization, Hardware AV Controller, Web Calibration Dashboard  
**Performance Goals**: Multi-target evaluations computed in $< 50\text{ ms}$; full web graph overlay updates with zero page reloads  
**Constraints**: Constitution Principle I (hardware truth), Principle II (non-destructive telemetry), Principle III (profile-scoped sweeps)  
**Scale/Scope**: 9 community target profiles, cross-comparison across 4 hardware measurement modes (Through, YPAO Flat, YPAO Natural, PEQ Manual)  

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] **Principle I (Hardware-First)**: Empirical sweeps (`.npz`) sourced from real microphone captures over HDMI ARC; AVR state queries are live via YNC XML.
- [x] **Principle II (Non-Destructive Telemetry)**: Multi-target validation endpoints (`/api/targets`, `/api/calibration/multi_target_eval`) are purely observational read-only computations.
- [x] **Principle III (Profile-Scoped Verification)**: Verification curves are evaluated against distinct profile keys without fallback cross-contamination.
- [x] **Principle IV (Measurement Immutability)**: Multi-target benchmarking consumes immutable `.npz` files and generates side-by-side matrices without modifying raw data.

## Project Structure

### Documentation (this feature)

```text
specs/011-multi-target-validation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── api_contracts.md # Target curves and evaluation API
└── checklists/
    └── requirements.md  # Specification quality checklist
```

### Source Code

```text
scripts/
├── peq_optimizer.py            # Unified target generator (generate_bookshelf_target_curve)
├── verify_calibration.py       # Multi-target scoring engine & comparative table generator
└── web_calibration_server.py   # /api/targets and /api/calibration/multi_target_eval endpoints
config/
└── targets.json                # Verified community target profiles
tests/
├── test_target_curves_audit.py # Unit tests for target curve roll-off & bounds
└── test_multi_target_eval.py   # Unit tests for multi-target benchmarking engine
```

## Implementation Phases

### Phase 1: Core Mathematical Unification
- Unify target curve calculation in `scripts/peq_optimizer.py` and import in `scripts/verify_calibration.py`.
- Guarantee that all target curves enforce $f_c=64\text{ Hz}$ Butterworth high-pass filtering in 2.0 bookshelf mode.

### Phase 2: Multi-Target Benchmarking Engine
- Implement `evaluate_multi_target_alignment()` in `scripts/verify_calibration.py`.
- Generate cross-target comparison tables (RMS error, peak deviation, S-TIER score).

### Phase 3: Web Server & API Integration
- Implement `GET /api/targets` in `scripts/web_calibration_server.py`.
- Implement `POST /api/calibration/multi_target_eval`.
- Integrate multi-target overlay in the calibration web UI.

### Phase 4: Verification & Regression
- Add unit tests in `tests/test_multi_target_eval.py`.
- Run complete test suite and verify quickstart workflows.
