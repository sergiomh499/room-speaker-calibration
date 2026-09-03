# Quickstart Validation Guide: PEQ Filter Audit

## Prerequisites
- Python 3.10+ with `numpy`, `scipy`, and `matplotlib`.
- Baseline physical measurement file at `data/medicion_real_calibracion.npz` or `data/medicion_promedio_espacial.npz`.

---

## Validation Scenario 1: CLI Diagnostic Audit of Active Filters
Runs the audit tool against the current PEQ configuration and prints a diagnostic report:
```bash
python3 scripts/audit_peq_filters.py --profile harman_wide_room
```

**Expected Outcome**:
- Script executes in < 2 seconds.
- Terminal renders a table of detected physical room modes (< 500 Hz).
- Center frequencies and gains of all 14 bands are matched against physical modes.
- Terminal outputs clear status: `ACCURATE`, `SUBOPTIMAL`, or `ERRONEOUS`.

---

## Validation Scenario 2: Detecting Deliberately Flawed Filters
Tests the diagnostic engine against an intentionally flawed filter set (e.g. +6 dB boost at 120 Hz):
```bash
python3 -m unittest tests/test_audit_peq.py
```

**Expected Outcome**:
- Unit tests verify that positive modal gain is rejected.
- Unit tests verify that filters misaligned by > 5 Hz are flagged.
- All tests pass in < 3 seconds.

---

## Validation Scenario 3: Automated Re-Optimization on Flawed Input
Runs the audit with `--reoptimize` flag on an invalid or unaligned filter set:
```bash
python3 scripts/audit_peq_filters.py --profile harman_wide_room --reoptimize
```

**Expected Outcome**:
- Tool outputs diagnostic delta table showing why the original was flawed.
- Tool calculates and displays the mathematically optimal 7-band replacement.
- Simulated residual RMS error is demonstrated to decrease by $\ge 15\%$.
