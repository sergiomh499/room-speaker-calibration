# Implementation Plan: Acoustic PEQ Parameter Calculation Engine & Coordinated Stereo Optimization

**Branch**: `004-fix-peq-calculation` | **Date**: 2026-09-03 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/004-fix-peq-calculation/spec.md`

## Summary

This feature resolves the anomalous parametric equalizer (PEQ) calculations and post-calibration validation failures on the front channels (specifically Front L). The root cause was twofold: (1) peak detection in `peq_optimizer.py` falsely placed deep negative cuts (up to −10.5 dB) on room dips/nulls where measured response was already well below the target curve, while bandwidth calculation operated on array indices rather than physical Hertz, and (2) a metric name mismatch between the Python verification module (`target_alignment_pct`) and web frontend (`fidelity_score_pct`) caused all curves to display 0.0% scores. 

The implementation introduces:
1. Positive error gating ($\Delta \text{SPL} \ge +1.5\text{ dB}$) and continuous frequency bandwidth calculation ($\Delta f_{-3\text{dB}}$ in Hz) for stable Q estimation ($0.5 \le Q \le 5.0$).
2. Coordinated stereo optimization (Opción A) pairing shared room modes (~115 Hz) with symmetrical center frequencies, limiting independent adjustments to verified boundary asymmetry ($Q \le 3.5$, cut $\le -5.0\text{ dB}$).
3. Unified metric naming across Python verification backend, web API, and PDF reporting.

---

## Technical Context

**Language/Version**: Python 3.14 on Linux (x86_64).
**Primary Dependencies**: `numpy`, `scipy` (signal/optimize), `matplotlib` (Agg headless), `reportlab` (PDF generation).
**Storage**: Immutable `.npz` binary arrays in `data/`, JSON profile configuration in `config/targets.json`.
**Testing**: Python `unittest` test suites (`tests/test_peq_optimizer_coordinated.py`, `tests/test_report_graphs_sync.py`, `tests/test_audit_peq.py`).
**Target Platform**: Local Linux workstation and Yamaha RX-V673 AV Receiver (HTTP YNC XML API at `192.168.1.43`).
**Project Type**: Acoustic measurement, numerical optimization, and hardware DSP deployment system.
**Performance Goals**: Dual-channel 7-band optimization execution time $< 500\text{ ms}$; report generation $< 1.5\text{ s}$.
**Constraints**: Yamaha RX-V673 hardware DSP constraints (exactly 7 bands per channel, 28 discrete frequencies, 14 discrete Q factors, gain in 0.5 dB steps from −12.0 dB to +3.0 dB, 0.0 dB boost > 500 Hz).
**Scale/Scope**: Stereo pair (Front L and Front R) calibrated across 6 community target profiles.

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle / Rule | Compliance Status | Analysis & Evidence |
|---|---|---|
| **I. Hardware-First — No Simulated State** | **PASS** | Parameter deployment (`--push` or `/api/apply_profile`) directly addresses Yamaha RX-V673 via HTTP YNC XML API with atomic readback verification. |
| **II. Non-Destructive Telemetry** | **PASS** | Telemetry and status endpoints (`/api/preflight_check`, `/api/verification_comparison`) remain strictly read-only. No side-effecting commands are issued during polling. |
| **III. Profile-Scoped Verification** | **PASS** | All verification metrics, baseline curves, and sweeps are strictly scoped to the active profile key (e.g. `harman_wide_room`, `bk_1974`). |
| **IV. Measurement Immutability & Traceability** | **PASS** | Sourcing is explicitly bound to `medicion_punto_1.npz` (Sweet Spot) and `medicion_promedio_espacial.npz`. No raw captures are silently overwritten. |
| **V. Minimum Viable Command Surface** | **PASS** | Uses targeted atomic parameter writes (`put_param_block`) instead of destructive `Scene_Sel`. |
| **Hardware Constraints (8 Ω MIN, 7 Bands, Schroeder Limit)** | **PASS** | Receiver remains at 8 Ω MIN; exactly 7 discrete bands per channel; strict zero-boost rule enforced above 500 Hz. |

---

## Project Structure

### Documentation (this feature)

```text
specs/004-fix-peq-calculation/
├── plan.md              # Implementation Plan (this document)
├── research.md          # Technical decisions and acoustic research
├── data-model.md        # Schemas for ModalPeak, PEQFilterBand, VerificationResult
├── quickstart.md        # Step-by-step runnable validation guide
├── contracts/           # API and module contracts
│   └── optimizer_contracts.md
└── checklists/
    └── requirements.md  # Spec quality checklist (16/16 pass)
```

### Source Code (repository root)

```text
scripts/
├── peq_optimizer.py             # Core numerical optimization engine (RBJ biquad, peak detection, coordinate descent)
├── auto_calibrate.py            # CLI calibration runner (Sweet Spot + spatial average ingestion, profile dispatch)
├── verify_calibration.py        # Post-calibration acoustic verification engine & metric calculation
├── web_calibration_server.py    # Background calibration server, REST API endpoints, and web dashboard
└── 03_generate_pdf_report.py    # Dynamic profile-aware PDF calibration certificate generator

config/
└── targets.json                 # Community target profiles and acoustic voicing definitions

tests/
├── test_peq_optimizer_coordinated.py  # Unit tests for peak gating, physical Q calculation, and coordinated L/R pairing
├── test_report_graphs_sync.py          # Regression tests for report generation, CSD waterfall, and cache headers
└── test_audit_peq.py                   # Baseline audit test suite
```

**Structure Decision**: Single-project repository with modular scripts in `scripts/`, verified via `tests/`.

---

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

*No violations detected. Design fully complies with Constitution v1.0.0 and Spec Kit standards.*
