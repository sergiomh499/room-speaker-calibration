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

---

## 3. POST `/api/calibration/preload_preset`

Deploys a stored profile or historical session PEQ filter set directly to the Yamaha RX-V673 hardware without repeating the multi-point spatial measurement.

### Request
```json
{
  "profile_id": "bk_1974",
  "session_id": "sesion_20260904_180309"
}
```

### Response
```json
{
  "ok": true,
  "deployed_profile": "bk_1974",
  "bands_fl": 7,
  "bands_fr": 7,
  "peq_select": "Manual",
  "verification_curve_available": true,
  "msg": "Filtros PEQ B&K 1974 cargados en el Yamaha RX-V673 con éxito."
}
```

---

## 4. GET `/api/sessions/history`

Lists all historical calibration sessions and available verification sweeps.

### Response
```json
{
  "ok": true,
  "sessions": [
    {
      "session_id": "sesion_20260904_180309",
      "profile_id": "harman_wide_room",
      "timestamp": "2026-09-04 18:03:09",
      "certified": true,
      "has_verification": true
    }
  ]
}
```

