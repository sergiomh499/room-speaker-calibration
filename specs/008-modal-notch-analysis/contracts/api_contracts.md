# API & Interface Contracts: Modal Notch Diagnostic & Acoustic Rationale

## 1. REST Endpoint: Modal Diagnostics with Acoustic Rationale

`GET /api/calibration/modal_diagnostics`

Returns empirical modal peak detection enriched with physical wavelength calculations, speaker integrity verification, and band-by-band rationales.

### Response JSON Schema

```json
{
  "ok": true,
  "smoothing": "Variable Smoothing (Var)",
  "normalization": "Broadband Energy Average (300 Hz - 3 kHz)",
  "channels": {
    "L": {
      "active_notches_count": 1,
      "peaks": [
        {
          "freq_hz": 125.0,
          "elevation_db": 6.32,
          "q": 5.04,
          "bandwidth_hz": 24.9,
          "wavelength_m": 2.74,
          "boundary_dim_m": 1.37,
          "classification": "AXIAL_ROOM_MODE",
          "rationale": "Onda estacionaria axial de sala excitada por proximidad a esquina/pared lateral."
        }
      ]
    },
    "R": {
      "active_notches_count": 1,
      "peaks": [
        {
          "freq_hz": 198.4,
          "elevation_db": 4.23,
          "q": 2.52,
          "bandwidth_hz": 90.9,
          "wavelength_m": 1.73,
          "boundary_dim_m": 0.86,
          "classification": "AXIAL_ROOM_MODE",
          "rationale": "Modo de sala en canal derecho con mayor amortiguación acústica."
        }
      ]
    }
  },
  "transducer_health": {
    "model": "Q Acoustics 3020i",
    "verdict": "PRISTINE_HEALTH",
    "mean_stereo_delta_db": 0.35,
    "notes": "Simetría anecoica excelente (Δ < 0.5 dB a 1 kHz). Cero defectos mecánicos o eléctricos."
  }
}
```

## 2. Web UI Contract: Modal Diagnostics & Tooltip Cards

### Element: `#modal-symmetry-card`
Renders:
1. Two-column grid comparing Front L and Front R detected modes.
2. For each detected mode:
   - Center frequency + snapped Yamaha frequency.
   - Peak elevation in dB.
   - Quality factor Q and physical bandwidth $\Delta f$.
   - Associated physical wavelength $\lambda$ and half-wave boundary distance.
3. Transducer health badge (`INTEGRIDAD: ÓPTIMA` in `#4ade80`).
4. Explanatory tooltip detailing why high-Q notch is required to preserve musical bass punch.
