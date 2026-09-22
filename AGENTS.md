<!-- SPECKIT START -->
For additional context about technologies to be used, project structure,
shell commands, and other important information, read the current plan
at specs/011-multi-target-validation/plan.md
<!-- SPECKIT END -->

# Repository Guidelines

## Project Overview
Automated electroacoustic room correction and multi-point calibration suite engineered for domestic listening environments. The system optimizes a 2.1 setup (Yamaha RX-V673 AVR + Q Acoustics 3020i + Focal Cub Evo subwoofer) using smartphone (Google Pixel 9 Pro tethered/untethered) or calibrated USB microphones (miniDSP UMIK-1, Dayton UMM-6).

The engine executes Farina logarithmic sine sweeps, records multi-point acoustic impulse responses, computes spatial vector averaging and psychoacoustic smoothing, calculates 7-band parametric EQ (PEQ) filter biquads snapped to discrete Yamaha DSP hardware constraints, computes subwoofer crossover/delay/trims, directly programs AVR NVRAM via Yamaha Network Control (YNC XML/HTTP), and validates acoustic response against target curves (Harman In-Room, B&K 1974, Dirac Live).

---

## Architecture & Data Flow

### System Components
```
[ Microphone (Pixel 9 Pro / UMIK-1) ]
                  │
          Farina Audio Sweeps
                  ▼
[ Web Calibration Server ] (Python 3.10+ / HTTP+ThreadingMixIn :53317)
  ├── Static Host ───────────────► [ React 18 SPA (Vite / Tailwind / Three.js) ]
  ├── Spatial Averaging ─────────► [ scripts/spatial_average.py ]
  ├── PEQ & Filter Optimizer ────► [ scripts/peq_optimizer.py ]
  │                                   ├── Discrete Yamaha Frequency/Q/Gain Snapping
  │                                   ├── Modal Resonance Notch Identification
  │                                   └── Subwoofer Crossover & Phase Alignment
  └── Hardware Controller ───────► [ scripts/04_yamaha_control.py ]
                                      └── YNC XML over HTTP (192.168.1.43:80)
                                            ├── Volume & Channel Trims (±0.5 dB)
                                            ├── Speaker Distances (0.05 m steps)
                                            └── 7-Band PEQ Matrix per Channel
```

### End-to-End Calibration Pipeline
1. **Pre-Flight & State Snapshot**: `scripts/web_calibration_server.py` verifies AVR connectivity and captures a pre-calibration snapshot of current NVRAM settings into `data/pre_measurement_avr_state.json` for rollback safety.
2. **Excitation & Measurement**: Synchronized Farina sweeps (full-range 15–22,000 Hz or subwoofer 15–180 Hz) play through the AVR while the microphone captures 1 to 5 spatial positions (`data/medicion_punto_*.npz`).
3. **Deconvolution & Spatial Averaging**: `scripts/spatial_average.py` deconvolves recorded sweeps with the inverse filter, performs time-of-flight alignment, and computes complex vector spatial averages.
4. **Constrained PEQ Optimization**: `scripts/peq_optimizer.py` identifies standing room modes, evaluates transfer error against selected target curves (`config/targets.json`), and optimizes 7 PEQ biquads per channel with discrete parameter quantization.
5. **Hardware Deployment**: Parameters are converted to YNC XML payloads and deployed via HTTP POST to `http://<AVR_IP>/YamahaRemoteControl/ctrl`.
6. **Closed-Loop Verification & Reporting**: A post-calibration sweep validates correction accuracy, generating multi-panel comparison plots (`figures/`) and automated PDF reports (`reports/`).

---

## Key Directories

- `scripts/`: Core electroacoustic engine, mathematical optimizers, hardware communication, and web server.
- `frontend/`: Single-page application frontend.
  - `frontend/src/views/`: Primary views (`HomeView`, `CalibrateView`, `SettingsView`, `HistoryView`).
  - `frontend/src/components/`: Modular UI, 3D visualization (`charts/SpatialRoom3D.tsx`), frequency plots (`FrequencyGraph.tsx`, `PEQFilterGraph.tsx`), and dialogs.
  - `frontend/src/context/`: Central state store (`CalibrationContext.tsx`).
  - `frontend/src/services/`: REST API client (`api.ts`).
  - `frontend/src/types/`: Domain TypeScript types and interfaces.
- `config/`: System configuration and target curves.
  - `config/hardware.json`: Hardware profiles (microphones, amplifier specs, discrete frequency/Q tables, speakers, subwoofer).
  - `config/targets.json`: Acoustic target curves (Harman In-Room, B&K 1974, Dirac Live, Linear Flat).
  - `config/calibrations/`: 90-degree microphone calibration files (`.cal`).
- `tests/`: Pytest suite for DSP math, biquad stability, optimizer ground-truth, and zero-hardcode audits.
- `data/`: Stored measurement archives (`.npz`), generated Farina sweep WAVs, and AVR state backups.
- `figures/`: Diagnostic plots (RT60 decay, impulse responses, waterfall/CSD, spatial averages).
- `reports/`: Generated PDF calibration reports (ReportLab).
- `specs/`: Specification documents, API contracts, and implementation plans.
- `homeassistant/`: Home Assistant integration (packages, Lovelace UI, REST bridge service).

---

## Development Commands

### Backend & Acoustic Engine
```bash
# Start calibration web server daemon (port 53317)
python3 scripts/web_calibration_server.py

# Run standalone multi-point auto-calibration CLI
python3 scripts/auto_calibrate.py --target harman_wide_room --use-spatial-avg

# Push calculated PEQ matrix to Yamaha AVR hardware
python3 scripts/auto_calibrate.py --target harman_wide_room --push-yamaha

# Query Yamaha AVR hardware status via YNC XML
python3 scripts/04_yamaha_control.py status

# Switch AVR scenes over network
python3 scripts/04_yamaha_control.py scene 1

# Generate post-calibration verification and benchmark plots
python3 scripts/verify_calibration.py

# Generate cumulative spectral decay (CSD / waterfall) plots
python3 scripts/csd_waterfall.py
```

### Frontend (React + Vite)
```bash
cd frontend

# Install dependencies (preferred: Bun)
bun install

# Start Vite development server (proxies API calls to backend)
bun run dev

# Type check and build production bundle into frontend/dist/
bun run build

# Preview production build locally
bun run preview
```

### Testing & Verification
```bash
# Run all offline mathematical, DSP, and zero-hardcode tests
pytest tests/ -k "not test_multi_target_endpoints and not test_preset_preloader"

# Run specific DSP unit test suites
pytest tests/test_peq_biquad_math.py
pytest tests/test_peq_optimizer_ground_truth.py
pytest tests/test_audit_zero_hardcode.py

# Run full test suite (requires backend running on localhost:53317)
pytest tests/ -vv
```

---

## Code Conventions & Common Patterns

### 1. Strict Zero-Hardcode Invariant
- **Rule**: Never hardcode acoustic parameters (speaker distances, dB trims, PEQ frequencies, Q factors, room modes, or crossover points).
- **Implementation**: Every value must derive deterministically from measured signal physics (`.npz` impulse responses) or explicit hardware capabilities defined in `config/hardware.json`.
- **Validation**: Enforced via `tests/test_audit_zero_hardcode.py`.

### 2. Hardware Parameter Quantization
- Yamaha RX-V673 DSP accepts only discrete parameter steps. Never emit arbitrary floating-point values to the hardware.
- Always use optimizer quantization helpers:
  - Frequencies: `snap_frequency(f)` against `YAMAHA_FREQS` (28 bands: 31.3 Hz to 16.0 kHz).
  - Q factors: `snap_q(q)` against `YAMAHA_QS` (14 values: 0.500 to 10.080).
  - Gains: `snap_gain(g)` clamped to `[-12.0, +3.0] dB` in discrete 0.5 dB steps (`GAIN_STEP_DB = 0.5`).
- Trims: Speaker trim levels clamped to `[-10.0, +10.0] dB` in 0.5 dB steps.

### 3. Asymmetric Acoustic Gain Limits
- Maximum boost: `MAX_BOOST_DB = +3.0 dB` (prevent amplifier clipping and distortion).
- Maximum cut: `MAX_CUT_DB = -12.0 dB` (effective modal standing wave attenuation).
- Schroeder transition threshold: Above `SCHROEDER_FREQ_HZ = 500.0 Hz`, maximum boost is strictly `0.0 dB` to prevent comb-filter overcompensation in non-minimum phase zones.

### 4. Idempotency & Safe State Rollback
- All hardware mutations must preserve recovery state.
- Save pre-flight receiver settings to `data/pre_measurement_avr_state.json` prior to deploying filters or running automated sweeps, allowing clean rollback upon abort.

### 5. Frontend Architecture & State Flow
- Central state is maintained in `CalibrationContext.tsx` with functional updates.
- API interactions route through `frontend/src/services/api.ts` using typed contracts (`frontend/src/types/index.ts`).
- Production frontend is compiled to `frontend/dist/` and served directly by `scripts/web_calibration_server.py`.
- Dark Studio Pro UI styling uses TailwindCSS tokens (`bg-zinc-950`, `border-zinc-800`, `text-zinc-100`, `accent-amber-500`).
- Canvas and Three.js components (`SpatialRoom3D.tsx`) must dispose geometries, materials, and requestAnimationFrame loops on unmount.

---

## Important Files

| Path | Purpose |
|------|---------|
| `scripts/web_calibration_server.py` | Multi-threaded calibration server, REST API router, sweep generator, static asset server |
| `scripts/peq_optimizer.py` | DSP optimization engine, RBJ biquad math, Yamaha parameter quantizers, crossover alignment |
| `scripts/04_yamaha_control.py` | Yamaha YNC XML protocol driver over HTTP; handles NVRAM PEQ deployment, volume, scenes |
| `scripts/spatial_average.py` | Multi-point spatial vector averaging, deconvolution, time-of-flight alignment |
| `scripts/auto_calibrate.py` | End-to-end CLI workflow orchestrating measurement, averaging, optimization, and AVR deployment |
| `scripts/verify_calibration.py` | Empirical verification comparing PEQ Manual against Through, YPAO modes, and target curves |
| `frontend/src/context/CalibrationContext.tsx` | Central React state manager for measurement progress, AVR telemetry, and active target |
| `frontend/src/services/api.ts` | Frontend HTTP client wrapping REST endpoints (`/api/*`) |
| `config/hardware.json` | Hardware profiles, discrete DSP frequency/Q tables, speaker/mic specs |
| `config/targets.json` | Standard target frequency response curves (Harman, B&K, Dirac) |
| `tests/conftest.py` | Pytest fixtures: frequency grids, synthetic room impulse responses with modal decay |

---

## Runtime/Tooling Preferences

- **Backend Runtime**: Python 3.10+ (Arch Linux / CachyOS).
- **Core Python Libraries**: `numpy` (>=1.24), `scipy` (>=1.10), `matplotlib` (>=3.7), `reportlab` (>=4.0).
- **Frontend Runtime & Package Manager**: **Bun** (`bun install`, `bun run build`). Fallback to Node 18+ / npm if Bun is absent, but `bun.lock` is the primary lockfile.
- **Frontend Bundler**: Vite 6 with `@vitejs/plugin-react` and TypeScript 5.
- **Microservices & Infrastructure**: Docker (`Dockerfile`, `docker-compose.yml`), Home Assistant OS add-on, Proxmox LXC.

---

## Testing & QA

- **Test Runner**: `pytest` executing tests under `tests/`.
- **Mathematical & DSP Testing**:
  - Validates transfer functions of RBJ peaking biquads against theoretical filter responses (`test_peq_biquad_math.py`).
  - Evaluates optimizer outputs against golden measurement archives (`data/medicion_promedio_espacial.npz`).
  - Tests use `np.testing.assert_allclose` with strict absolute tolerances (`atol=1e-5` to `1e-2`) to avoid floating-point false positives.
- **Hardware Integration Testing**:
  - Verifies that all PEQ parameters generated match valid elements of `YAMAHA_FREQS` and `YAMAHA_QS`.
  - Ensures zero-hardcode compliance across trims, distances, and modal damping.
- **Live Endpoint Tests**:
  - `tests/test_multi_target_endpoints.py` and `tests/test_preset_preloader.py` test HTTP endpoints against `http://127.0.0.1:53317`.
  - Exclude them during offline development using `pytest -k "not test_multi_target_endpoints and not test_preset_preloader"`.
