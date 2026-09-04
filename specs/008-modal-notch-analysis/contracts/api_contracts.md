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

---

## 3. REST Endpoint: Finalize Calibration & Dynamic PEQ Optimization

`POST /api/finalize_calibration?profile={profile_key}`

Executes spatial averaging, runs `optimize_stereo_peq()`, updates `config/targets.json` with the dynamically calculated 7 bands per channel, and generates the figures and technical PDF.

### Response JSON Schema

```json
{
  "ok": true,
  "profile": "harman_wide_room",
  "dynamically_optimized": true,
  "predicted_rms_reduction_db": 1.36,
  "predicted_modal_attenuation_db": 6.00,
  "bands": [
    {
      "name": "Band 1",
      "freq": 157.5,
      "q_l": 1.587,
      "q_r": 1.0,
      "gain_l": -4.0,
      "gain_r": 0.0,
      "desc": "Modo propio axial Front L (157 Hz) con pase neutro en R"
    }
  ],
  "report_url": "/reports/Informe_Calibracion_Acustica_harman_wide_room.pdf"
}
```

---

## 4. REST Endpoints: Non-Destructive Single-Point Re-Measurement

`POST /api/clear_point?point={1..5}`
Clears only the specified measurement point without affecting any other measured points, allowing a clean re-take.

`POST /api/record_point?point={1..5}`
Initiates a sweep measurement for the specified point. Upon completion, automatically recalculates `data/medicion_promedio_espacial.npz` in the background.

---

## 5. Web UI Contract: Paginated Wizard Navigation

### Wizard Pages & Indicators
1. **Navigation Header**: `#wizard-stepper` containing 6 clickable phase chips:
   - `1. Pre-flight Hardware`
   - `2. Medición Multipunto`
   - `3. Optimización PEQ`
   - `4. Grabación en AVR`
   - `5. Verificación en Vivo`
   - `6. Informes y Exportación`
2. **Page Containers**: Active step displayed via `.wizard-page.active`, hiding inactive pages (`display: none`).
3. **Footer Controls**:
   - `#btn-wizard-prev`: Navigate to the preceding phase.
   - `#btn-wizard-next`: Navigate to the next phase (enabled when step criteria pass).
   - `#btn-repeat-point`: Re-arms and measures strictly the active point in Step 2.
