# Implementation Plan: Modal Notch Diagnostic and Acoustic PEQ Rationale

**Branch**: `008-modal-notch-analysis` | **Date**: 2026-09-04 | **Spec**: [specs/008-modal-notch-analysis/spec.md](spec.md)

**Input**: Feature specification from `/specs/008-modal-notch-analysis/spec.md`

## Summary
Provide an authoritative physical, mathematical, and electroacoustic diagnostic framework for the Front L 125 Hz room mode standing wave ($\lambda = 2.81\text{ m}$, $Q=5.04$). Integrate the dynamic PEQ optimization engine (`optimize_stereo_peq()`) directly into the calibration finalization flow so that all 7 biquad bands per channel are derived from empirical sweet spot and spatial average data, overwriting static placeholder tables in `targets.json` with strict stereo frequency alignment. Transform the web calibration interface into a paginated, step-by-step modular wizard enabling users to navigate between independent phases (Hardware Preflight, Multipoint Measurement, Dynamic Optimization, AVR Deployment, Live Verification, and Reports) and repeat any individual point without losing session state.

## Technical Context

**Language/Version**: Python 3.10+ (NumPy, SciPy, Matplotlib), Vanilla JS (ES6 Modules) / CSS3 Flexbox & Grid.
**Primary Dependencies**: `scipy.signal.find_peaks`, `numpy.fft`, `reportlab`.
**Storage**: JSON (`config/targets.json`, `config/hardware.json`), NPZ (`data/medicion_punto_*.npz`, `data/medicion_promedio_espacial.npz`).
**Testing**: `unittest` test suite in `tests/test_modal_notch_diagnostic.py`, `tests/test_peq_optimizer_coordinated.py`.
**Target Platform**: Linux / Yamaha RX-V673 (YNC XML API) / Browser Dashboard (Mobile & Desktop).
**Project Type**: Acoustic Signal Processing & Web Dashboard.
**Performance Goals**: Sub-10ms modal detection computation, non-blocking UI rendering, instant wizard step transitions.
**Constraints**: Yamaha RX-V673 discrete frequencies & Q values, strictly non-destructive telemetry (zero unauthorized AVR mutations), 7 bands max per channel.
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
| **Stereo Mode Frequency Alignment** | Shared modes share discrete center frequency; asymmetric modes pair with neutral 0.0 dB on opposite channel for stereo invariance. | Independent uncoordinated frequency allocations per channel. |
| **Empirical PEQ Dynamic Sync** | On `/api/finalize_calibration`, derive all 7 bands from actual measurements and write to `targets.json`, eliminating static placeholder tables. | Keeping hardcoded tables in `targets.json` and disconnecting optimizer. |
| **Paginated Wizard Dashboard** | Modular steps with independent state allow repeating any single measurement point or verification sweep without full session restarts. | Single-page monolithic scroll where state errors force starting over. |
| **Anechoic Transducer Health Check (> 400 Hz)** | Mean delta $< 0.5\text{ dB}$ proves speakers are mechanically and electrically pristine. | In-depth disassembly or factory bench test. |
