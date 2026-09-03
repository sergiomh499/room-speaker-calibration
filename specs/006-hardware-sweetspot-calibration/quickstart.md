# Quickstart Guide: Tight Sweet-Spot & Hardware Profile Calibration

**Feature**: `006-hardware-sweetspot-calibration`
**Date**: 2026-09-04

---

## Prerequisites

1. Python 3.10+ with numpy, scipy, reportlab.
2. Web calibration server running on port `53317` (`python3 scripts/web_calibration_server.py`).
3. Empirical impulse responses in `data/`.

---

## Scenario 1: Switch Hardware Profile via REST API

Verify that changing hardware profile persists to `config/hardware.json` and updates optimizer limits without touching AVR registers.

```bash
# 1. Query current configuration
curl -s http://127.0.0.1:53317/api/hardware/config | jq .active

# Expected output:
# {
#   "microphone": "pixel_9_pro_calibrated",
#   "amplifier": "yamaha_rx_v673",
#   "speakers": "q_acoustics_3020i"
# }

# 2. Select miniDSP UMIK-1 microphone
curl -s -X POST http://127.0.0.1:53317/api/hardware/select \
  -H "Content-Type: application/json" \
  -d '{"microphone": "minidsp_umik1", "amplifier": "yamaha_rx_v673", "speakers": "q_acoustics_3020i"}' | jq .ok

# Expected output: true
```

---

## Scenario 2: Validate Front L / Front R Modal Balance with Broadband Normalization

Run the optimization engine using the new broadband 300 Hz – 3 kHz normalization and Variable Smoothing. Verify Front L receives active corrective filters in the modal band instead of collapsing to 0 dB.

```bash
python3 -c '
from scripts.auto_calibrate import run_calibration
res = run_calibration(target_key="harman_wide_room", push_yamaha=False)
l_notches = [b for b in res["left_filters"] if b["gain_db"] < 0]
r_notches = [b for b in res["right_filters"] if b["gain_db"] < 0]
print(f"Front L active modal notches: {len(l_notches)}")
print(f"Front R active modal notches: {len(r_notches)}")
assert len(l_notches) >= 2, "Front L must have at least 2 active modal notch filters!"
assert len(r_notches) >= 2, "Front R must have at least 2 active modal notch filters!"
print("SUCCESS: Balanced modal correction verified across both channels!")
'
```

---

## Scenario 3: Verify PDF Report Displays Active Hardware Profile

Generate the technical PDF report and check that Table 1 contains the exact selected hardware:

```bash
python3 scripts/generate_pdf_report.py
# Check stdout for active hardware components:
# [v] Hardware Components documented:
#     - Microphone: Google Pixel 9 Pro (Tethered Acoustic) / miniDSP UMIK-1
#     - Amplifier:  Yamaha RX-V673 (Burr-Brown DAC)
#     - Speakers:   Q Acoustics 3020i (5.0" Bookshelf)
```
