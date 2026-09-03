# Implementation Plan: Dynamic Synchronization of Reports, Acoustic Figures, and Hardware PEQ Execution

**Branch**: `003-fix-report-graphs` | **Date**: 2026-09-03 | **Spec**: [specs/003-fix-report-graphs/spec.md](spec.md)

**Input**: Feature specification from `specs/003-fix-report-graphs/spec.md`

## Summary

This feature resolves user-reported issues where acoustic figures, technical reports, and waterfall plots appeared un-updated or rendered all-zero planes, and fixes an execution crash (`exit status 2`) when applying PEQ filters to the Yamaha RX-V673 receiver. The plan establishes:
1. Physical impulse response sourcing from Punto 1 (Sweet Spot) for non-zero 3D Waterfall CSD and impulse decay analysis.
2. Dynamic, profile-aware PDF report generation adapting to any active community target (Harman, B&K 1974, Dirac Live, etc.).
3. CLI argument aliasing (`--target` and `--profile`) in `auto_calibrate.py` with transparent `stderr` reporting and atomic YNC readback verification.
4. Comprehensive HTTP anti-caching headers and client cache-busting parameters across all figure and report endpoints.

---

## Technical Context

**Language/Version**: Python 3.10+ (standard interpreter on workstation)
**Primary Dependencies**:
- `numpy`: Array manipulation, FFT, spectral convolution
- `scipy`: Digital filtering, biquad synthesis, peak detection
- `matplotlib`: Headless (`Agg`) 2D/3D acoustic figure generation
- `reportlab`: PDF document rendering, platypus flowables, high-resolution tables
- `http.server`: Embedded dual-protocol web server (Workstation port 53317)
**Storage**:
- Raw binary measurement records: `data/medicion_punto_{1..5}.npz`, `data/medicion_promedio_espacial.npz`
- Verification sweeps: `data/medicion_verificacion_manual_{profile}.npz`
- High-resolution visual figures: `figures/*.png`
- Official engineering reports: `reports/*.pdf` and `reports/*.html`
**Testing**: `pytest`, `unittest`, Python `py_compile`
**Target Platform**: Linux x86_64 (workstation / audio calibration hub)
**Project Type**: Acoustic signal processing engine, REST API, and web telemetry interface
**Performance Goals**:
- PDF report generation: < 5.0 seconds
- Web asset delivery latency: < 100 ms
- Discrepancy between UI metrics and PDF metrics: 0.00 dB
**Constraints**:
- Max 7 PEQ bands per channel (Yamaha RX-V673 hardware limitation)
- Correction limited to modal range (< 500 Hz)
- Zero simulation: all hardware state commands must target live receiver via YNC XML API

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Requirement | Status | Verification Note |
|---|---|---|---|
| **I. Hardware-First** | No simulated AVR state or synthetic fallback curves | **PASS** | 3D Waterfall CSD sources true physical impulse response from Punto 1 (`ir_l`/`ir_r`). PEQ push directly targets Yamaha NVRAM. |
| **II. Non-Destructive Telemetry** | Polling endpoints MUST be read-only; no side-effecting PUT commands | **PASS** | Telemetry endpoints (`/api/preflight_check`, `/api/verification_status`) remain purely observational. |
| **III. Profile-Scoped Verification** | Sweeps and PEQ comparison scoped to active profile key | **PASS** | PDF report, verification comparisons, and PEQ deployments are explicitly parameterized by `profile`. |
| **IV. Measurement Immutability** | Raw `.npz` files are immutable; no silent data destruction | **PASS** | Existing baseline files preserved; new verification runs maintain traceable metadata. |
| **V. Minimum Viable Command Surface** | Targeted single-parameter writes; no destructive scene jumps | **PASS** | Direct PEQ manual biquad addressing prevents volume disruption or unintended input switching. |

---

## Project Structure

### Documentation (this feature)

```text
specs/003-fix-report-graphs/
├── spec.md              # Feature specification with integrated clarifications
├── plan.md              # Implementation plan (this document)
├── research.md          # Phase 0 architectural decisions and tradeoffs
├── data-model.md        # Phase 1 data entities and lifecycle relationships
├── quickstart.md        # Phase 1 verification scenarios and run guide
├── contracts/           # Phase 1 interface specifications
│   └── api_contracts.md # REST and CLI endpoint contracts
└── checklists/
    └── requirements.md  # Quality assurance checklist (16/16 pass)
```

### Source Code (repository root)

```text
scripts/
├── 01_measure_sweep.py         # Acoustic sweep engine with calibrated microphone
├── 02_plot_responses.py        # Frequency response & spatial average plotting
├── 03_generate_pdf_report.py   # Dynamic profile-aware PDF report generator
├── 04_yamaha_control.py        # Yamaha RX-V673 YNC XML hardware control
├── auto_calibrate.py           # Optimizer CLI with --profile / --target alias support
├── csd_waterfall.py            # 3D Cumulative Spectral Decay from Punto 1 IR
├── spatial_average.py          # 5-point spatial averaging engine
├── verify_calibration.py       # Multi-mode verification and S-TIER certification
└── web_calibration_server.py   # Web dashboard and REST API with anti-cache headers

config/
└── targets.json                # Target curves (Harman, B&K 1974, Dirac Live, etc.)

data/
├── medicion_punto_{1..5}.npz   # Raw 5-point acoustic captures
└── medicion_promedio_espacial.npz # Averaged frequency response

figures/
├── promedio_espacial_multipunto.png # Dynamic spatial average plot
├── respuesta_acustica_real.png      # Dynamic L/R frequency response plot
├── waterfall_csd_comparison.png     # Dynamic 3D waterfall plot (non-zero decay)
├── rt60_decay_analysis.png          # Dynamic reverberation decay plot
└── verificacion_post_calibracion.png # Dynamic multi-mode verification comparison

reports/
└── Informe_Calibracion_Acustica_Yamaha.pdf # Canonical generated report
```

**Structure Decision**: Monorepo scripts and static asset structure. Code changes localize strictly to `scripts/` with zero disruptive structural migrations.

---

## Complexity Tracking

*No constitutional violations identified. No unjustified architectural complexity.*
