# Quickstart Validation Guide: Dynamic Reports, Acoustic Figures, and PEQ Deployment

**Feature**: `003-fix-report-graphs`
**Date**: 2026-09-03
**Status**: Ready for Verification

## Validation Scenarios

### Scenario 1: CLI Parameter Compatibility (`--target` vs `--profile`)
**Objective**: Prove that `auto_calibrate.py` accepts both `--target` and `--profile` without crashing with exit code 2.

```bash
# Test alias --target
python3 scripts/auto_calibrate.py --target harman_wide_room

# Test original --profile
python3 scripts/auto_calibrate.py --profile bk_1974
```
**Expected Outcome**: Both commands complete with exit code 0 and output calculated PEQ biquads.

---

### Scenario 2: 3D Waterfall CSD Non-Zero Acoustic Decay
**Objective**: Confirm that the 3D Waterfall plot is computed from Punto 1 physical impulse response and contains valid non-zero decay slices.

```bash
# Execute waterfall generator
python3 scripts/csd_waterfall.py

# Verify generated plot exists and is non-empty
stat figures/waterfall_csd_comparison.png
```
**Expected Outcome**: The plot reflects physical room modal ringing (< 300 Hz) with non-zero dynamic range, eliminating flat zeroed planes.

---

### Scenario 3: Profile-Aware PDF Report Generation
**Objective**: Generate PDF technical reports for two distinct profiles and verify that the target curves and profile titles differ accordingly.

```bash
# Generate for Harman Target
python3 scripts/03_generate_pdf_report.py --profile harman_wide_room --output reports/test_harman.pdf

# Generate for B&K 1974 Target
python3 scripts/03_generate_pdf_report.py --profile bk_1974 --output reports/test_bk1974.pdf

# Verify both exist
ls -lh reports/test_harman.pdf reports/test_bk1974.pdf
```
**Expected Outcome**: Both PDF files compile cleanly, have non-zero size (> 1 MB), and reflect the respective profile's target curves.

---

### Scenario 4: Web Server Cache-Busting and PEQ Application
**Objective**: Test the live web API endpoints for cache-control headers and robust error reporting.

```bash
# Check PDF download headers (must include no-cache)
curl -I -s http://127.0.0.1:53317/api/download_pdf | grep -i "cache-control"

# Apply profile via API
curl -X POST "http://127.0.0.1:53317/api/apply_profile?profile=harman_wide_room"
```
**Expected Outcome**:
- `Cache-Control: no-cache, no-store, must-revalidate` is present in response headers.
- API returns `{"ok": true, ...}` with zero subprocess exit status 2 errors.
