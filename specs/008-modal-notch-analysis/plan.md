# Implementation Plan: Modal Notch Diagnostic and Acoustic PEQ Rationale

**Branch**: `008-modal-notch-analysis` | **Date**: 2026-09-04 | **Spec**: [specs/008-modal-notch-analysis/spec.md](spec.md)

**Input**: Feature specification from `/specs/008-modal-notch-analysis/spec.md`

## Summary
Provide an authoritative physical, mathematical, and electroacoustic diagnostic framework for the Front L 125 Hz room mode standing wave ($\lambda = 2.81\text{ m}$, $Q=5.04$). Formally document why the high-Q surgical notch is required, why Front R is asymmetric, why unexcited bands remain at 0.0 dB (phase preservation / anti-boost), why the 2.52 kHz boost compensates for the Q Acoustics 3020i crossover dip, and why the empirical measurement proves 100% pristine speaker transducer health.

## Technical Context

**Language/Version**: Python 3.10+ (NumPy, SciPy, Matplotlib), Vanilla JS / CSS.
**Primary Dependencies**: `scipy.signal.find_peaks`, `numpy.fft`.
**Storage**: JSON (`config/targets.json`, `config/hardware.json`), NPZ (`data/medicion_promedio_espacial.npz`).
**Testing**: `unittest` test suite in `tests/test_modal_notch_diagnostic.py`.
**Target Platform**: Linux / Yamaha RX-V673 (YNC XML API) / Browser Dashboard.
**Project Type**: Acoustic Signal Processing & Web Dashboard.
**Performance Goals**: Sub-10ms modal detection computation, non-blocking UI rendering.
**Constraints**: Yamaha RX-V673 discrete frequencies & Q values, strictly non-destructive telemetry (zero unauthorized AVR mutations).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Principle I: Hardware-First (No Simulated State)**: PASS. All acoustic metrics originate from real room measurements (`data/medicion_promedio_espacial.npz`) and live Yamaha hardware constraints.
- **Principle II: Non-Destructive Telemetry**: PASS. Diagnostic endpoints are strictly read-only (`GET /api/calibration/modal_diagnostics`).
- **Principle III: Profile-Scoped Verification**: PASS. Visualizations and diagnostics respect active profile scoping.
- **Principle IV: Measurement Immutability**: PASS. Reads existing immutable captures without overwriting.

## Project Structure

### Documentation (this feature)

```text
specs/008-modal-notch-analysis/
├── plan.md              # Implementation plan
├── research.md          # Physical wave equations, Q factor analysis, speaker integrity proofs
├── data-model.md        # Entities: ModalPeakDiagnostic, PEQBandAcousticFunction, TransducerIntegrity
├── quickstart.md        # Validation commands and quick run guide
├── contracts/
│   └── api_contracts.md # REST and UI contracts
└── checklists/
    └── requirements.md  # Quality validation checklist
```

### Source Code

```text
scripts/
├── peq_optimizer.py               # Modal resonance detection with physical wavelength & Q factors
├── web_calibration_server.py      # /api/calibration/modal_diagnostics enriched with physical rationale
tests/
└── test_modal_notch_diagnostic.py # Dedicated test suite verifying modal wavelength and transducer health
```

## Architecture Decisions

| Decision | Rationale | Alternatives Considered |
| :--- | :--- | :--- |
| **High-Q Surgical Notch ($Q \ge 4.0$)** | Drains narrow standing wave without affecting musical fundamentals. | Broad filter ($Q=1.0$) which would ruin bass punch. |
| **0.0 dB Inactive Bands** | Preserves minimum phase and prevents boosting destructive nulls. | Arbitrary equalizer boosting. |
| **L/R Channel Asymmetry** | Domestic room boundaries are non-symmetrical; independent correction is required. | Forcing identical filters, creating an artificial dip in R. |
| **Anechoic Transducer Health Check (> 400 Hz)** | Mean delta $< 0.5\text{ dB}$ proves speakers are mechanically and electrically pristine. | In-depth disassembly or factory bench test. |
