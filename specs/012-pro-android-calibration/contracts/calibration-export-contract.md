# Contract: Calibration Archive & Export Schema

**Module**: `services/exportService.ts`
**Version**: 1.0.0

## 1. Archive Structure
When a user initiates an export from the mobile application, a self-contained `.zip` bundle is generated in the device's public `Documents/OctaveCalibrations/` directory:

```text
Octave_Calibration_{SessionId}_{Timestamp}.zip
├── session.json               # Full session metadata, metrics, and parameters
├── curves.csv                 # Raw & smoothed frequency spectra across all points
├── yamaha_peq_matrix.xml      # Exported YNC XML payload deployed to receiver
├── impulse_responses/
│   ├── point_1_Front_L.bin    # 32-bit Float raw impulse response
│   ├── point_1_Front_R.bin
│   └── point_1_Subwoofer.bin
└── report.pdf                 # Formatted summary report with before/after curves
```

---

## 2. Session JSON Schema (`session.json`)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "OctaveCalibrationSession",
  "type": "object",
  "required": ["sessionId", "createdAt", "topology", "targetProfile", "peqMatrix", "verification"],
  "properties": {
    "sessionId": { "type": "string", "format": "uuid" },
    "createdAt": { "type": "string", "format": "date-time" },
    "appVersion": { "type": "string" },
    "topology": { "type": "string", "enum": ["2.0", "2.1"] },
    "microphone": {
      "type": "object",
      "properties": {
        "id": { "type": "string" },
        "name": { "type": "string" },
        "isUsb": { "type": "boolean" },
        "calibrationFile": { "type": "string" }
      }
    },
    "targetProfile": {
      "type": "object",
      "properties": {
        "id": { "type": "string" },
        "name": { "type": "string" },
        "bassBoostDb": { "type": "number" },
        "hfRollOffDb": { "type": "number" }
      }
    },
    "peqMatrix": {
      "type": "object",
      "properties": {
        "Front_L": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "band": { "type": "integer" },
              "freqHz": { "type": "number" },
              "q": { "type": "number" },
              "gainDb": { "type": "number" },
              "role": { "type": "string" }
            }
          }
        },
        "Front_R": { "type": "array" }
      }
    },
    "crossover": {
      "type": "object",
      "properties": {
        "crossoverHz": { "type": "number" },
        "subwooferTrimDb": { "type": "number" },
        "subwooferDelayMs": { "type": "number" }
      }
    },
    "verification": {
      "type": "object",
      "properties": {
        "verified": { "type": "boolean" },
        "modalReductionDb": { "type": "number" },
        "rmsImprovementDb": { "type": "number" }
      }
    }
  }
}
```

---

## 3. Curves CSV Schema (`curves.csv`)
Comma-separated value table containing all calibrated response points:
```csv
frequency_hz,target_db,pre_cal_left_db,pre_cal_right_db,filter_left_db,filter_right_db,verified_left_db,verified_right_db
31.3,2.5,74.2,75.1,0.0,0.0,74.5,75.0
39.4,2.5,76.8,77.4,-2.5,-3.0,74.1,74.5
...
```
