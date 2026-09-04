# API Contracts: Tight Sweet-Spot & Hardware Profile Calibration

**Feature**: `006-hardware-sweetspot-calibration`
**Date**: 2026-09-04

---

## 1. GET `/api/hardware/config`

Retrieves the full hardware configuration including active selections and available models.

### Response (200 OK)
```json
{
  "ok": true,
  "active": {
    "microphone": "pixel_9_pro_calibrated",
    "amplifier": "yamaha_rx_v673",
    "speakers": "q_acoustics_3020i"
  },
  "microphones": {
    "pixel_9_pro_calibrated": { "id": "pixel_9_pro_calibrated", "name": "Google Pixel 9 Pro (Tethered Acoustic)", "type": "mems_dual_capsule", "cal_file": "config/calibrations/pixel_9_pro_90deg.cal" },
    "minidsp_umik1": { "id": "minidsp_umik1", "name": "miniDSP UMIK-1 (USB Calibrated)", "type": "electret_condenser", "cal_file": "config/calibrations/umik1_90deg.cal" },
    "dayton_umm6": { "id": "dayton_umm6", "name": "Dayton Audio UMM-6", "type": "electret_condenser", "cal_file": "config/calibrations/dayton_umm6_90deg.cal" },
    "generic_flat": { "id": "generic_flat", "name": "Generic Flat Microphone", "type": "uncalibrated", "cal_file": null }
  },
  "amplifiers": {
    "yamaha_rx_v673": { "id": "yamaha_rx_v673", "brand": "Yamaha", "model": "RX-V673", "protocol": "ync_xml", "peq_bands": 7 },
    "generic_avr": { "id": "generic_avr", "brand": "Generic", "model": "Standard AVR / DSP", "protocol": "manual_export", "peq_bands": 7 }
  },
  "speakers": {
    "q_acoustics_3020i": { "id": "q_acoustics_3020i", "brand": "Q Acoustics", "model": "3020i", "f3_cutoff_hz": 64.0, "crossover_hz": 2400.0 },
    "generic_bookshelf": { "id": "generic_bookshelf", "brand": "Generic", "model": "Standard Bookshelf", "f3_cutoff_hz": 80.0, "crossover_hz": 2500.0 },
    "generic_tower": { "id": "generic_tower", "brand": "Generic", "model": "Floorstanding Tower", "f3_cutoff_hz": 40.0, "crossover_hz": 2800.0 }
  }
}
```

---

## 2. POST `/api/hardware/select`

Updates the active microphone, amplifier, or speaker model. Non-destructive: does not modify AVR hardware registers.

### Request Body
```json
{
  "microphone": "minidsp_umik1",
  "amplifier": "yamaha_rx_v673",
  "speakers": "q_acoustics_3020i"
}
```

### Response (200 OK)
```json
{
  "ok": true,
  "msg": "Hardware configuration updated successfully.",
  "active": {
    "microphone": "minidsp_umik1",
    "amplifier": "yamaha_rx_v673",
    "speakers": "q_acoustics_3020i"
  }
}
```

---

## 3. POST `/api/hardware/upload_mic_cal`

Uploads an individual `.cal` or `.txt` calibration file (e.g. from miniDSP serial lookup).

### Request
Multipart form data with file field `cal_file` and string `mic_id`.

### Response (200 OK)
```json
{
  "ok": true,
  "msg": "Calibration file saved and bound to microphone profile.",
  "cal_file_path": "config/calibrations/custom_user_mic.cal",
  "points_parsed": 512
}
```

---

## 4. GET `/api/calibration/modal_diagnostics`

Returns detailed side-by-side modal peak detection and filter allocation metrics for Front L and Front R.

### Response (200 OK)
```json
{
  "ok": true,
  "smoothing": "variable",
  "normalization": "broadband_300_3000_hz",
  "channels": {
    "L": {
      "baseline_spl_db": 74.2,
      "detected_peaks": [
        { "freq_hz": 119.0, "elevation_db": 4.8, "q": 2.52, "assigned_gain_db": -4.0 },
        { "freq_hz": 198.4, "elevation_db": 2.6, "q": 2.00, "assigned_gain_db": -2.0 }
      ],
      "active_notches_count": 4,
      "rms_error_before": 3.84,
      "rms_error_after": 1.42
    },
    "R": {
      "baseline_spl_db": 74.5,
      "detected_peaks": [
        { "freq_hz": 125.0, "elevation_db": 5.1, "q": 3.175, "assigned_gain_db": -4.5 },
        { "freq_hz": 198.4, "elevation_db": 3.2, "q": 2.00, "assigned_gain_db": -2.5 }
      ],
      "active_notches_count": 5,
      "rms_error_before": 4.12,
      "rms_error_after": 1.38
    }
  }
}
```
