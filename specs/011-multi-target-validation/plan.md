# Implementation Plan: Multi-Target Validation & Comparative Acoustic Benchmarking

**Branch**: `011-multi-target-validation` | **Date**: 2026-09-04 | **Spec**: [specs/011-multi-target-validation/spec.md](spec.md)

**Input**: Feature specification from `specs/011-multi-target-validation/spec.md`

## Summary

1. Unify target curve calculation across the calibration suite, enforcing 4th-order high-pass roll-off for Q Acoustics 3020i ($f_c = 64\text{ Hz}$).
2. Build a professional 1-to-1 calibration and testing workflow per profile (deploy PEQ $\rightarrow$ sweep verification $\rightarrow$ single-preset Antes vs Después vs Target plot) with 3 key metrics (modal reduction, stereo symmetry, target deviation).
3. Modernize the web dashboard to a "Dark Studio Pro" aesthetic (Dirac Live / Logic Pro inspired): `#0f172a` slate palette, ergonomic touch targets ($\ge 48\text{px}$) for mobile and desktop, responsive layout, smooth state transitions, and historic session explorer with preset pre-loading directly to AVR.
4. Expose secondary multi-target benchmarks via `/api/targets` and `/api/calibration/multi_target_eval` in collapsible panels.

## Technical Context

**Language/Version**: Python 3.14  
**Primary Dependencies**: NumPy, SciPy, Matplotlib, ReportLab (PDF)  
**Storage**: NumPy archive binaries (`.npz`), JSON configuration (`config/targets.json`), session historical directories (`data/sessions/`)  
**Frontend/UI**: Pure HTML5 / Modern CSS (Vanilla Responsive Grid/Flex, CSS Variables, GPU micro-animations), Vanilla ES6 JavaScript (Zero external bulky frameworks)  
**Testing**: Python `unittest` (`python3 -m unittest discover -s tests -p "test_*.py"`)  
**Target Platform**: Linux (Arch/CachyOS x86_64), local calibration server at `http://127.0.0.1:53317`, responsive mobile browsers (>=360px)  
**Project Type**: Acoustic DSP Optimization, Hardware AV Controller, Dark Studio Pro Web Dashboard  
**Performance Goals**: Multi-target evaluations computed in $< 50\text{ ms}$; UI transitions $< 250\text{ ms}$; zero horizontal overflow on mobile; zero page reloads  
**Constraints**: Constitution Principle I (hardware truth), Principle II (non-destructive telemetry), Principle III (profile-scoped sweeps), Principle IV (measurement immutability)  
**Scale/Scope**: 9 community target profiles, cross-comparison across hardware measurement modes, historical session browser with AVR preset preloading  
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
## Implementation Phases

### Phase 1: Core Mathematical Unification (Complete)
- Unify target curve calculation in `scripts/peq_optimizer.py` and import in `scripts/verify_calibration.py`.
- Guarantee that all target curves enforce $f_c=64\text{ Hz}$ Butterworth high-pass filtering in 2.0 bookshelf mode.

### Phase 2: Multi-Target Benchmarking Engine (Complete)
- Implement `evaluate_multi_target_alignment()` in `scripts/verify_calibration.py`.
- Generate cross-target comparison tables (RMS error, peak deviation, S-TIER score).

### Phase 3: Professional 1-to-1 Workflow & Preset Preload Endpoints
- Implement `POST /api/calibration/preload_preset` in `scripts/web_calibration_server.py` to deploy stored profiles directly to the AVR hardware.
- Implement `GET /api/sessions/history` to provide historical calibration and verification sessions.

### Phase 4: Dark Studio Pro Responsive Dashboard Redesign
- Restructure web calibration interface to Dark Studio Pro aesthetic (`#0f172a` deep slate, studio emerald accents, crisp typography).
- Enlarge all touch controls to $\ge 48\text{px}$ for mobile sweet-spot usage.
- Implement single-preset 1-to-1 card (Antes vs Después vs Target con 3 métricas de ingeniería: reducción modal, simetría estéreo y adherencia al target).
- Add interactive preset pre-load selector and historical session explorer.
- Ensure collapsible secondary multi-target benchmark accordion.

### Phase 5: Verification & Full Regression
- Add tests for preset preloading and historical session querying.
- Run full regression suite (`python3 -m unittest discover -s tests -p "test_*.py"`).

## Constitution Post-Design Re-Evaluation

- [x] **Principle I (Hardware Truth)**: Preset pre-loading pushes actual YNC XML commands to `192.168.1.43` without simulation.
- [x] **Principle II (Non-Destructive Telemetry)**: History browsing and telemetry are strictly GET read-only requests.
- [x] **Principle III (Profile-Scoped Verification)**: 1-to-1 workflow maintains strict scoping of measured sweeps to their specific profile.
- [x] **Principle IV (Measurement Immutability)**: Historical sessions and sweeps remain read-only; new calibrations create new timestamped sessions.

## Artifacts Generated

- `specs/011-multi-target-validation/plan.md`
- `specs/011-multi-target-validation/research.md`
- `specs/011-multi-target-validation/data-model.md`
- `specs/011-multi-target-validation/quickstart.md`
- `specs/011-multi-target-validation/contracts/api_contracts.md`

## Next Steps

Run `/speckit.tasks` to generate the updated task decomposition covering the Dark Studio Pro dashboard redesign and preset preloading.

### Generated Artifacts
- `specs/011-multi-target-validation/plan.md`
- `specs/011-multi-target-validation/research.md`
- `specs/011-multi-target-validation/data-model.md`
- `specs/011-multi-target-validation/contracts/api_contracts.md`
- `specs/011-multi-target-validation/quickstart.md`

Ready for `/speckit.tasks`.
