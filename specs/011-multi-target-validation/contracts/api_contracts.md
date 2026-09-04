# API Contracts: Multi-Target Validation

## 1. GET `/api/targets`

Returns the list and curve vectors for all available reference targets.

### Response
```json
{
  "ok": true,
  "targets": [
    {
      "id": "harman_wide_room",
      "name": "Harman Target / Floyd Toole (Referencia Acústica Universal)",
      "category": "Música Hi-Fi / Audición Diaria",
      "cutoff_hz": 64.0
    },
    {
      "id": "bk_1974",
      "name": "B&K 1974 (Calidez Analógica Británica / Cero Fatiga)",
      "category": "Música Hi-Fi / Melómano Analógico",
      "cutoff_hz": 64.0
    },
    {
      "id": "dirac_live",
      "name": "Dirac Live Modern Stereo (Claridad y Dinámica)",
      "category": "Música Hi-Fi / Producción / Precisión",
      "cutoff_hz": 64.0
    },
    {
      "id": "cinema_blockbuster",
      "name": "Cinema Blockbuster Impact (Graves Potentes y Efectos Dinámicos)",
      "category": "Cine / Series / Películas de Acción",
      "cutoff_hz": 64.0
    },
    {
      "id": "audiophile_flat",
      "name": "Audiophile Diffuse-Field Flat (Respuesta Neutra de Estudio)",
      "category": "Monitoreo de Estudio / Masterización",
      "cutoff_hz": 64.0
    }
  ]
}
```

---

## 2. POST `/api/calibration/multi_target_eval`

Evaluates a specific measurement file or the active session against all defined targets.

### Request
```json
{
  "measurement_file": "medicion_verificacion_manual.npz",
  "targets": ["harman_wide_room", "bk_1974", "dirac_live", "audiophile_flat"]
}
```

### Response
```json
{
  "ok": true,
  "measurement_file": "medicion_verificacion_manual.npz",
  "results": {
    "harman_wide_room": {
      "target_name": "Harman Target / Floyd Toole",
      "rms_error_db": 0.85,
      "max_peak_error_db": 1.40,
      "fidelity_score_pct": 96.5,
      "rating": "S-TIER"
    },
    "bk_1974": {
      "target_name": "B&K 1974",
      "rms_error_db": 1.10,
      "max_peak_error_db": 1.95,
      "fidelity_score_pct": 94.2,
      "rating": "S-TIER"
    },
    "audiophile_flat": {
      "target_name": "Audiophile Diffuse-Field Flat",
      "rms_error_db": 2.15,
      "max_peak_error_db": 3.40,
      "fidelity_score_pct": 82.0,
      "rating": "B"
    }
  },
  "best_fit": "harman_wide_room"
}
```
