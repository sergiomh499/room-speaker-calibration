# Implementation Plan: Multi-Format Filter Export (REW, EqualizerAPO, CSV)

**Branch**: `007-multi-format-filter-export`
**Spec File**: `specs/007-multi-format-filter-export/spec.md`
**Design Artifacts**:
- Research: `specs/007-multi-format-filter-export/research.md`
- Data Model: `specs/007-multi-format-filter-export/data-model.md`
- Contracts: `specs/007-multi-format-filter-export/contracts/api_contracts.md`
- Quickstart: `specs/007-multi-format-filter-export/quickstart.md`

## 1. Technical Context

- **Source Data**: `scripts/peq_optimizer.py` computes optimized 7-band filters for Front L and Front R matching Yamaha RX-V673 discrete registers.
- **Formats to Support**:
  1. REW (.req): Standard Room EQ Wizard filter definition text files.
  2. EqualizerAPO (.txt): System-wide Windows DSP config with per-channel blocks and negative preamp compensation.
  3. CSV (.csv): Portable tabular format with channel, band, frequency, gain, Q, and active hardware tags.
  4. ZIP bundle: Single-archive package containing all formats.
- **Interfaces**:
  - Standalone script: `scripts/export_filters.py`
  - Web calibration server endpoint: `GET /api/export_filters`
  - Dashboard UI: `#export-filters-card` with dynamic links updating per active profile.

## 2. Constitution Check

- **Principle I (Hardware-First)**: Export operations read calculated mathematical filter values or active NVRAM snapshots; they do not alter AVR state.
- **Principle II (Non-Destructive Telemetry)**: Export endpoints are read-only HTTP GET requests. Zero state mutation occurs on the receiver.
- **Principle III (Profile-Scoped Verification)**: Every export is strictly bound to the requested target profile (`profile` parameter).
- **Principle IV (Single-Source Architecture)**: Reuses `scripts/peq_optimizer.py` filter generation logic and hardware profile from `config/hardware.json`.

## 3. Implementation Steps

1. Create `scripts/export_filters.py` core export module:
   - `format_rew(bands, channel, profile, hardware)`
   - `format_equalizer_apo(bands_l, bands_r, profile, hardware)`
   - `format_csv(bands_l, bands_r, profile, hardware)`
   - `build_export_bundle(profile, out_dir)`
   - CLI entry point with `argparse`.
2. Implement automated tests in `tests/test_filter_export.py`:
   - Verify REW format compliance.
   - Verify EqualizerAPO syntax and preamp offset calculation.
   - Verify CSV header and values match optimizer output.
   - Verify ZIP creation.
3. Integrate REST endpoint `GET /api/export_filters` in `scripts/web_calibration_server.py`.
4. Add `#export-filters-card` to dashboard HTML/JS in `scripts/web_calibration_server.py`.
5. Run full test suite and smoke test export endpoints.
