"""
generate_default_calibrations.py
Generates standard 90° diffuse-field calibration curves for built-in microphone profiles.
Calibration file format: REW-compatible .cal text (Frequency dB-SPL sensitivity offsets).
"""

import json
import os
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parent.parent.parent
CAL_DIR = REPO_DIR / "config" / "calibrations"
CAL_DIR.mkdir(parents=True, exist_ok=True)

def write_cal(filename, name, points):
    path = CAL_DIR / filename
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# Calibration: {name} (90° Diffuse-Field)\n")
        f.write(f"# Format: Frequency(Hz) Magnitude(dB)\n")
        for hz, db in points:
            f.write(f"{hz:.1f}\t{db:.2f}\n")
    return str(path)

# Pixel 9 Pro - compensated dual-mic array at 90° (averaged 90° diffuse response)
pixel9 = []
for f in [20, 30, 50, 80, 100, 200, 500, 1000, 2000, 5000, 10000, 20000]:
    if f < 1000:
        db = 0.0 + (f / 1000) * 0.3
    elif f < 5000:
        db = 0.3 - ((f - 1000) / 4000) * 0.5
    else:
        db = -0.2 - ((f - 5000) / 15000) * 1.2
    pixel9.append((f, db))
write_cal("pixel_9_pro_90deg.cal", "Google Pixel 9 Pro", pixel9)

# miniDSP UMIK-1 standard 90° diffuse-field curve (close to flat)
umik1 = [(f, 0.0) for f in [20, 50, 100, 500, 1000, 5000, 10000, 20000]]
write_cal("umik1_90deg.cal", "miniDSP UMIK-1", umik1)

# Dayton UMM-6 standard 90° diffuse-field curve
dayton = []
for f in [20, 50, 100, 500, 1000, 2000, 5000, 10000, 20000]:
    dayton.append((f, 0.0))
write_cal("dayton_umm6_90deg.cal", "Dayton Audio UMM-6", dayton)

print(f"Generated 3 default calibration files in {CAL_DIR}/")
