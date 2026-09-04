# Implementation Plan: Tight Sweet-Spot Multipoint & Hardware Profile Calibration

**Branch**: `006-hardware-sweetspot-calibration` | **Date**: 2026-09-04 | **Spec**: [specs/006-hardware-sweetspot-calibration/spec.md](spec.md)

---

## Summary

Resolves the acoustic anomaly where Front L collapsed to zero modal filters while Front R received heavy cuts, by replacing wide multipoint room sweeps and single-frequency (1 kHz) anchor normalization with:
1. **Tight Sweet-Spot 5-Point Cluster**: 15–20 cm radius around ear center (MLP) with 70% sweet-spot / 30% satellite spatial averaging, enforcing mandatory 90° vertical microphone orientation.
2. **Broadband 300 Hz – 3 kHz Normalization & Variable Smoothing (Var)**: Immune to localized narrow 1 kHz reflection dips, providing an adaptive +1.0 dB peak detection threshold to accurately treat genuine room modes (60–300 Hz) on both channels symmetrically.
3. **Hardware Profile Selector**: Persistent configuration in `config/hardware.json` enabling dynamic selection of measurement microphones (Pixel 9 Pro, miniDSP UMIK-1, Dayton UMM-6 with optional `.cal` file upload), amplifiers (Yamaha RX-V673 discrete 7-band biquads), and loudspeakers (Q Acoustics 3020i 64 Hz cutoff & 2.52 kHz crossover dip compensation).
4. **Side-by-Side Modal Diagnostics & PDF Reporting**: Real-time transparency in the web dashboard explaining filter allocations, reflected dynamically in technical PDF reports.

---

## Technical Context

**Language/Version**: Python 3.10+ (runtime Python 3.14 on workstation), Vanilla JavaScript (ES6+), HTML5, CSS3.
**Primary Dependencies**: NumPy (array math & FFT), SciPy (signal processing, biquads, optimization), ReportLab (technical PDF generation), standard library (`http.server`, `urllib`, `json`, `xml.etree.ElementTree`).
**Storage**: File-based persistence in `config/hardware.json`, `config/targets.json`, `data/medicion_punto_*.npz`, `reports/*.pdf`.
**Testing**: Python `unittest` (`python3 -m unittest discover -s tests -p "test_*.py"`).
**Target Platform**: Linux (CachyOS x86_64 host), accessible remotely via mobile browser (Pixel 9 Pro) over local Wi-Fi.
**Project Type**: Embedded HTTP calibration dashboard & electroacoustic optimizer with network AVR control.
**Performance Goals**: Hardware profile switch < 200 ms, PEQ optimization computation < 200 ms, PDF generation < 2.0 s.
**Constraints**: Zero AVR writes on selection change (Principle II & V); discrete Yamaha frequency/Q matrix snapping; Schroeder frequency gate (500 Hz).

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Principle I: Hardware-First — No Simulated State**: PASS. Hardware profile configuration targets the real Yamaha RX-V673 at `192.168.1.43`. Mocking is restricted to isolated unit tests.
- **Principle II: Non-Destructive Telemetry**: PASS. Hardware configuration endpoints (`/api/hardware/config`, `/api/hardware/select`) are strictly decoupled from AVR state and execute zero destructive network commands.
- **Principle III: Profile-Scoped Verification**: PASS. Verification and optimizer runs are parameterized per profile without mixing calibration sweeps.
- **Principle IV: Measurement Immutability and Traceability**: PASS. Spatial sweeps and tight cluster data maintain timestamped audit provenance.
- **Principle V: Minimum Viable Command Surface**: PASS. Targeted parameter writes only (`PUT /YamahaExtendedControl/...`); scene recall is strictly avoided.

---

## Project Structure

### Documentation (this feature)

```text
specs/006-hardware-sweetspot-calibration/
├── plan.md              # This implementation plan
├── research.md          # Acoustic research on tight sweet spot, REW Var smoothing & 2026 standards
├── data-model.md        # HardwareConfiguration, TightClusterData, ModalDiagnostics entities
├── quickstart.md        # Step-by-step runnable validation scenarios
├── contracts/
│   ├── api_contracts.md # REST endpoints for hardware selection & modal diagnostics
│   └── ui_contracts.md  # DOM specifications for hardware panel & tight cluster guide
└── tasks.md             # Implementation task breakdown (generated via /speckit.tasks)
```

### Source Code (repository root)

```text
config/
├── hardware.json               # Active hardware selection & equipment definitions
├── targets.json                # Target acoustic curves (Harman, B&K 1974, Dirac Live, etc.)
└── calibrations/               # 90° diffuse-field calibration curves (.cal)
    ├── pixel_9_pro_90deg.cal
    ├── umik1_90deg.cal
    └── dayton_umm6_90deg.cal

scripts/
├── auto_calibrate.py           # Core calibration pipeline: 70/30 spatial averaging & 300Hz-3kHz norm
├── peq_optimizer.py            # Variable Smoothing (Var), adaptive peak detection, hardware limits
├── web_calibration_server.py   # REST endpoints, Hardware Selector panel, Tight Sweet-Spot UI guide
├── generate_pdf_report.py      # Technical PDF generation integrating active hardware specifications
└── 04_yamaha_control.py        # Discrete Yamaha RX-V673 YNC XML LAN control layer

tests/
├── test_hardware_sweetspot_calibration.py # Regression & contract tests for hardware & tight sweet spot
└── test_compact_profile_selector.py       # Existing regression tests
```

---

## Complexity Tracking

*No constitutional violations identified. Design adheres strictly to Principles I through V.*
