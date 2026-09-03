# Phase 0 Research: Dynamic Synchronization of Reports, Acoustic Figures, and Hardware PEQ Execution

**Feature**: `003-fix-report-graphs`
**Date**: 2026-09-03
**Status**: Completed

## Research Decisions and Architecture

### 1. Cumulative Spectral Decay (CSD / 3D Waterfall) Physical Signal Sourcing

- **Decision**: Source the time-domain impulse response array strictly from the measured physical impulse response of **Punto 1 (Sweet Spot)** (`ir_l` / `ir_r` stored in `data/medicion_punto_1.npz` or `data/medicion_real_calibracion.npz`).
- **Rationale**: 
  - Spatial multipoint averaging (`spatial_average.py`) averages frequency-domain magnitudes across 5 spatial microphone locations to eliminate single-point spatial null artifacts.
  - Averaging magnitude spectra discards phase information; therefore, `data/medicion_promedio_espacial.npz` lacks a coherent time-domain impulse response (`ir_l` is null or zeroed).
  - When `csd_waterfall.py` or `02_plot_responses.py` attempted to load `ir_l` from `medicion_promedio_espacial.npz`, it fell back to `np.zeros(4800)`, rendering a flat 3D waterfall plot with all values at 0 dB.
  - Sourcing from Point 1 (primary listener ear location) preserves real acoustic phase, room resonance decay tails, and physical boundary reflections.
- **Alternatives Considered**:
  - *Minimum-phase reconstruction via Hilbert transform / IFFT*: Mathematically feasible from magnitude curves, but creates a synthetic approximation rather than showing true physical room decay and violates Constitution Principle I (Hardware-First).
  - *Multi-point IR summation*: Introduces destructive phase cancellations (comb filtering) that do not correspond to any physical ear position in the room.

---

### 2. Real-Time Dynamic & Profile-Aware PDF Report Generation

- **Decision**: Refactor `scripts/03_generate_pdf_report.py` to accept `--profile <profile_key>` and export a reusable programmatic generation function `generate_pdf_report(profile="harman_wide_room", output_path=None) -> str`.
- **Rationale**:
  - Currently, `03_generate_pdf_report.py` hardcodes `harman_wide_room` targets, static text blocks, and writes to an unversioned `Informe_Calibracion_Acustica_Yamaha.pdf`.
  - When a user selects a community profile (e.g. B&K 1974, Dirac Live Modern Stereo, Pure Vocal Clarity), the report must render the matching target curve, compare measured vs simulated response for that specific profile, and document the deployed PEQ biquads.
  - Unifying the output path between `scripts/03_generate_pdf_report.py`, the web server download endpoint `/api/download_pdf`, and the report directory ensures 100% path consistency.
- **Alternatives Considered**:
  - *Pre-rendering PDFs for all 6 community targets at calibration end*: Wastes computation and disk space; does not account for runtime PEQ manual tweaks or re-optimizations.
  - *Client-side PDF generation in browser JS*: Fails to provide consistent typography, high-resolution vector figures, and server-side NVRAM verification data.

---

### 3. CLI Argument Aliasing and Process Error Visibility

- **Decision**: Update `scripts/auto_calibrate.py` to accept `--target` as an alias for `--profile`:
  ```python
  parser.add_argument("--profile", "--target", dest="profile", type=str, default="harman_wide_room", help="Target profile key")
  ```
  Additionally, wrap subprocess calls in `scripts/web_calibration_server.py` with `try ... except subprocess.CalledProcessError as e:` and return `e.stderr.strip() or e.stdout.strip()` in the JSON failure response.
- **Rationale**:
  - Standard `argparse` throws `exit status 2` when encountering unrecognized options like `--target`.
  - The web server was catching the general exception and reporting only `Command '...' returned non-zero exit status 2`, hiding the actual error message.
  - Supporting `--target` and `--profile` as aliases guarantees seamless compatibility across CLI invocations, scripts, Home Assistant packages, and web endpoints.
- **Alternatives Considered**:
  - *Only modifying the web server caller*: Fragile; external scripts (Home Assistant YAML, cron jobs, user terminal) calling `--target` would still crash with exit status 2.

---

### 4. Zero-Staleness HTTP Cache Control and Asset Invalidation

- **Decision**: Configure `scripts/web_calibration_server.py` to emit strict anti-caching HTTP headers on `/figures/*`, `/reports/*`, and `/api/download_pdf`:
  - `Cache-Control: no-cache, no-store, must-revalidate, max-age=0`
  - `Pragma: no-cache`
  - `Expires: 0`
  Pair this with client-side timestamp query parameters (`?t=${Date.now()}`) on all `<img>` tags and verification panels.
- **Rationale**:
  - Modern browsers aggressively cache static assets like PNG and PDF files served over HTTP.
  - Without explicit cache-busting headers, users repeatedly see cached plots from earlier calibration runs even after new sweeps have been processed.
- **Alternatives Considered**:
  - *Randomized filenames on each run*: Requires complex database/state tracking of orphaned files and periodic garbage collection.

---

### 5. Dynamic Impulse Response & RT60 Analysis Plotting

- **Decision**: Create/update `scripts/plot_rt60_decay.py` (or integrate into `scripts/02_plot_responses.py`) to dynamically generate `figures/rt60_decay_analysis.png` and `figures/respuesta_impulso_real.png` from Point 1 IR data on every calibration run.
- **Rationale**:
  - Currently, `figures/rt60_decay_analysis.png` was a static plot from a previous run, never recalculated by `finalize_calibration`.
  - Computing octave-band EDT / T20 / T30 reverberation decay dynamically ensures that all 4 figures displayed in the UI are freshly generated from current acoustic measurements.
