# Quickstart Validation Guide: Acoustic PEQ Optimization Engine

**Feature**: `004-fix-peq-calculation`
**Date**: 2026-09-03
**Status**: Complete

This guide details the step-by-step procedures to validate the acoustic PEQ optimizer and score reporting.

## Prerequisites
- Working directory: `/home/sergio/room-speaker-calibration`
- Python 3.14 with `numpy`, `scipy`, `matplotlib`, `reportlab` installed.
- Measured acoustic files available in `data/`:
  - `data/medicion_punto_1.npz` (Sweet Spot)
  - `data/medicion_promedio_espacial.npz` (5-Point Spatial Average)

---

## Validation Scenarios

### Scenario 1: Verify Peak Detection & Error Gating
Validate that the optimizer only assigns cuts to genuine resonant peaks above target ($\Delta \text{SPL} \ge +1.5\text{ dB}$) and leaves dips at $0.0\text{ dB}$.

```bash
python3 -c "
import numpy as np
from scripts.peq_optimizer import detect_modal_resonances

d = np.load('data/medicion_punto_1.npz')
freqs = d['freqs']
resp_l = d['smooth_l'] - d['smooth_l'][np.argmin(np.abs(freqs - 1000.0))]

# Construct dummy flat target (0 dB)
target = np.zeros_like(freqs)

peaks = detect_modal_resonances(freqs, resp_l, target, min_elevation_db=1.5, max_peaks=7)
print('Detected true peaks:')
for p in peaks:
    print(f\"  {p['freq_hz']:.1f} Hz | Elev: {p['elevation_db']:+.1f} dB | Q: {p['q']:.3f} | BW: {p['bandwidth_hz']:.1f} Hz\")
    assert p['elevation_db'] >= 1.5, 'Error: detected peak with elevation < 1.5 dB'
print('Scenario 1 Passed!')
"
```
**Expected Outcome**: All detected peaks have `elevation_db >= +1.5 dB`. Frequencies in dips (e.g. 62.5 Hz, 80 Hz) are omitted.

---

### Scenario 2: Test Coordinated Stereo PEQ Calculation
Run `scripts/auto_calibrate.py` for `harman_wide_room` in dry-run mode:

```bash
python3 scripts/auto_calibrate.py --profile harman_wide_room --dry-run
```
**Expected Outcome**:
- Clean execution with exit code `0`.
- Peak resonance at ~115–125 Hz is addressed on both Front L and Front R without excessive high-Q notch stacking.
- High-frequency voicing (2520 Hz) is preserved on both channels.
- Cumulative negative cut is bounded ($\ge -12.0\text{ dB}$).

---

### Scenario 3: Verify Metric Consistency & Non-Zero Score
Verify that `scripts/verify_calibration.py` outputs both `target_alignment_pct` and `fidelity_score_pct` as identical non-zero numbers:

```bash
python3 -c "
import scripts.verify_calibration as vc

m = vc.run_verification('harman_wide_room', save_fig=False)
for c in m['comparative_curves']:
    score1 = c.get('target_alignment_pct')
    score2 = c.get('fidelity_score_pct')
    print(f\"{c['name']}: target_alignment={score1}%, fidelity_score={score2}%\")
    assert score1 is not None and score1 > 0.0, f'Error: invalid score for {c[\"name\"]}'
    assert score1 == score2, f'Error: metric discrepancy {score1} != {score2}'
print('Scenario 3 Passed!')
"
```
**Expected Outcome**: All curves report positive alignment percentages (> 50.0%) and `target_alignment_pct == fidelity_score_pct`.

---

### Scenario 4: Test Web Dashboard API Endpoint
Query the live web calibration server on port `53317` for verification comparison data:

```bash
curl -s "http://127.0.0.1:53317/api/verification_comparison" | python3 -c "
import sys, json
data = json.load(sys.stdin)
assert data['ok'] is True
for c in data['comparative_curves']:
    score = c.get('fidelity_score_pct', 0)
    print(f\"API Score for {c['name']}: {score}%\")
    assert score > 0.0, f'Error: API returned 0% score for {c[\"name\"]}'
print('Scenario 4 Passed!')
"
```
**Expected Outcome**: API returns JSON with `ok: true` and all curves displaying their true mathematical scores (e.g. 90%+ for PEQ Manual).

---

### Scenario 5: Full Automated Regression Test Suite
Execute project test suites:

```bash
python3 -m unittest tests/test_peq_optimizer_coordinated.py
python3 -m unittest tests/test_report_graphs_sync.py
```
**Expected Outcome**: 100% test pass rate.
