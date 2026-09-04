# Quickstart: Multi-Format Filter Export Validation

## Prerequisites
- Working Python 3.10+ environment with numpy and scipy.
- Calibration data generated in `data/medicion_promedio_espacial.npz` or running calibration server.

## 1. CLI Filter Export Validation
```bash
# Export all formats to exports/ directory
python3 scripts/export_filters.py --profile harman_wide_room --format all --out-dir exports/

# Verify exported artifacts exist
ls -la exports/
# Expected:
# - filters_harman_wide_room_L.req
# - filters_harman_wide_room_R.req
# - equalizer_apo_harman_wide_room.txt
# - peq_filters_harman_wide_room.csv
```

## 2. REW Syntax Sanity Check
```bash
head -n 15 exports/filters_harman_wide_room_L.req
# Verify Filter 1..7 lines follow standard REW syntax:
# Filter 1: ON PK Fc 2520.0 Hz Gain +1.5 dB Q 1.260
```

## 3. EqualizerAPO Syntax Sanity Check
```bash
head -n 20 exports/equalizer_apo_harman_wide_room.txt
# Verify Preamp and Channel: L / Channel: R sections
```

## 4. HTTP API Validation
```bash
# Test CSV download
curl -s "http://127.0.0.1:53317/api/export_filters?format=csv&profile=harman_wide_room" | head -n 5

# Test EqualizerAPO download
curl -s "http://127.0.0.1:53317/api/export_filters?format=equalizerapo&profile=harman_wide_room" | head -n 10
```
