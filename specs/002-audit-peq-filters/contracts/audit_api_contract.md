# Interface Contract: PEQ Filter Audit & Verification

## 1. CLI Interface: `scripts/audit_peq_filters.py`

### Invocation
```bash
python3 scripts/audit_peq_filters.py [--profile <key>] [--peq-file <path>] [--reoptimize] [--json]
```

### Options
- `--profile <key>`: Target profile key (default: `harman_wide_room`).
- `--peq-file <path>`: Path to custom PEQ matrix JSON to audit (default: active NVRAM or current calibration).
- `--reoptimize`: If audit fails or is suboptimal, compute and output the mathematically optimal replacement.
- `--json`: Output full audit diagnosis in machine-readable JSON format.

### Exit Codes
- `0`: Audit completed; filters verified as `ACCURATE`.
- `1`: Error reading measurements or parsing PEQ matrix.
- `2`: Audit completed; filters diagnosed as `SUBOPTIMAL` or `ERRONEOUS`.

---

## 2. HTTP REST API Endpoint: `/api/audit_peq`

### Request
`POST /api/audit_peq?profile=harman_wide_room`

**Headers**: `Content-Type: application/json`

**Body (Optional)**:
```json
{
  "profile": "harman_wide_room",
  "peq_matrix": {
    "left": [
      { "band": 1, "freq_hz": 113.0, "q": 4.0, "gain_db": -6.0 }
    ],
    "right": [
      { "band": 1, "freq_hz": 113.0, "q": 4.0, "gain_db": -6.0 }
    ]
  }
}
```

### Response (200 OK)
```json
{
  "ok": true,
  "verdict": "ACCURATE",
  "verdict_summary": "14 filtros verificados. Todos los filtros modales atacan picos reales con atenuación negativa y parámetros discretos válidos.",
  "metrics": {
    "residual_rms_error_db": 2.09,
    "modal_peak_attenuation_db": 6.2,
    "stereo_imbalance_db": 1.76,
    "improvement_pct": 29.8
  },
  "diagnostics": {
    "left_channel": {
      "detected_modes": [
        { "freq_hz": 112.8, "prominence_db": 7.4, "estimated_q": 4.5 }
      ],
      "filter_evaluations": [
        { "band": 1, "freq_hz": 112.8, "q": 4.0, "gain_db": -6.0, "status": "ALIGNED", "discrepancy_hz": 0.0 }
      ]
    },
    "right_channel": { ... }
  },
  "recommended_peq": null
}
```
