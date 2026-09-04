# Specification: Multi-Target Validation & Comparative Acoustic Benchmarking

**Feature Branch**: `011-multi-target-validation`  
**Specification File**: `specs/011-multi-target-validation/spec.md`  
**Domain**: Acoustic Room Correction, DSP Verification, Interactive Web Visualization  

---

## 1. Executive Summary & Problem Statement

### 1.1 Context
In the room acoustic correction workflow for the Yamaha RX-V673 and Q Acoustics 3020i system, calibration quality is evaluated against target acoustic curves. Currently, validation routines evaluate the measured post-correction sweep (`medicion_verificacion_manual_{profile}.npz`) against a single target curve tied to the active profile. Users and acoustic evaluators cannot dynamically switch or compare multiple target curves against individual frequency response graphs (through bypass, YPAO Flat, YPAO Natural, and manual PEQ presets) to observe how well each hardware/DSP setting aligns with different target philosophies (e.g. Harman/Floyd Toole, B&K 1974, Dirac Live, Cinema/Blockbuster, Pure Audiophile Flat).

### 1.2 Objective
Enable multi-target validation and interactive comparative overlays across all generated response curves:
1. Verify and audit the mathematical accuracy of existing target curves (verifying that they properly reflect high-pass bookshelf rolloff at 64 Hz, bass boundary tilt, and treble rolloff).
2. Expand the target validation engine so that any verification measurement or comparison plot can dynamically evaluate and display deviation metrics (RMS error, maximum deviation, S-TIER score) against multiple selectable target curves.
3. Allow users in the web calibration dashboard and verification reports to toggle or overlay alternative target curves to see how closely each acoustic preset resembles both its native target and alternative acoustic references.


## Clarifications

### Session 2026-09-04
- Q: ¿Cómo prefieres estructurar el flujo de calibración y validación simplificado para cada curva? → A: Opción A enriquecida con C: Flujo profesional 1 a 1 donde cada preset tiene su calibración, testeo directo y visualización de 3 métricas útiles (reducción modal en graves, simetría estéreo |L-R| y adherencia al target), permitiendo además consultar verificaciones históricas y precargar presets ya guardados en el receptor o en disco.
- Q: ¿Qué estilo visual y de interacción prefieres como estándar de diseño para modernizar la interfaz hacia software de estudio profesional? → A: Opción A (Dark Studio Pro / Dirac & Logic Pro inspired): paleta grafito/slate oscuro (#0f172a / #1e293b), botones táctiles de gran formato (>=48px de altura), diseño totalmente adaptable y responsive (móvil y PC), microanimaciones fluidas de feedback visual y estética de herramienta de audio profesional sin apariencia de prototipo genérico.

---

## 2. User Scenarios & Testing Flows

### Scenario 1: Auditing the Primary Target Curve Against Real Acoustic Ground Truth
- **Given** an empirical measurement set (`medicion_punto_1.npz` and `medicion_promedio_espacial.npz`),
- **When** the calibration system loads the active preset (e.g., `harman_wide_room`),
- **Then** the validation engine computes the target curve incorporating:
  - 4th-order high-pass Butterworth roll-off ($f_c = 64\text{ Hz}$ for 2.0 bookshelf speakers).
  - Psychoacoustic target tilt (+2.5 dB below 120 Hz, smooth transition to -0.8 dB/octave above 200 Hz).
  - Verifies that the primary target does not penalize physical low-frequency physical roll-off below 50 Hz.

### Scenario 2: Cross-Comparing Measured Presets Against Multiple Alternative Targets
- **Given** verification measurement sweeps for different modes (Through, YPAO Flat, YPAO Natural, PEQ Manual),
- **When** the user inspects the validation interface or requests a multi-target audit,
- **Then** the system calculates cross-comparison fidelity scores:
  - RMS deviation of YPAO Flat vs Harman Target, vs B&K 1974, vs Audiophile Flat.
  - RMS deviation of PEQ Manual vs its intended preset target and vs generic flat reference.
- **And** outputs a comparative matrix showing which preset best satisfies each target curve standard.

### Scenario 3: Interactive Multi-Target Curve Overlay in Web UI

### Scenario 4: Professional 1-to-1 Calibration & Dedicated Verification Workflow
- **Given** an acoustic profile selected by the user (e.g. `bk_1974`),
- **When** the user clicks "Calibrar y Testear",
- **Then** the system deploys the preset PEQ filters to the Yamaha AVR, executes a dedicated verification log-sweep, and displays:
  - A clean 1-to-1 acoustic plot: **Antes (Through)** vs **Después (PEQ Medido)** vs **Target Nativo del Preset** (línea dorada).
  - Exactly 3 actionable engineering metrics:
    1. **Reducción del Pico Modal en Graves (dB y % energía)** ($< 400\text{ Hz}$).
    2. **Simetría Estéreo \|L - R\| (dB)** (corrección de desbalance por paredes laterales).
    3. **Adherencia al Target (%)** en el rango vocal y modal ($60\text{ Hz} - 5\text{ kHz}$).

### Scenario 5: Historical Verification Explorer & Preset Preload
- **Given** historical calibration sessions and sweeps stored in `data/sessions/`,
- **When** the user explores past verifications,
- **Then** the interface allows pre-loading any saved preset directly into the active PEQ slots of the AVR and reloading its corresponding verification curve without requiring a new measurement.

- **Given** the web calibration graph interface (`/api/calibration_status` and `/` dashboard),
- **When** the user views the post-calibration verification frequency response curve,
- **Then** the user can select from a dropdown or checkbox list of available reference targets (Harman, B&K 1974, Dirac Live, Cinema Blockbuster, Audiophile Flat),
- **And** the interface renders the chosen target curves overlaid directly against the measured Left/Right acoustic response, updating deviation badges and alignment metrics in real time.

### Scenario 6: Responsive Mobile Studio Workflow at Listening Position
- **Given** a user holding a smartphone or tablet at the main listening position (Sweet Spot),
- **When** the user accesses the calibration web interface via local Wi-Fi,
- **Then** the interface presents large, ergonomic touch controls ($\ge 48\text{px}$) with instant tactile visual feedback,
- **And** graphs, status badges, and sweep triggers scale smoothly without horizontal scrolling or tiny illegible text.


---

## 3. Functional Requirements

### 3.1 Target Curve Correctness & Acoustic Integrity
- **FR-001**: The system MUST verify that all validation target curves include the physical roll-off model for the Q Acoustics 3020i ($f_c \approx 64\text{ Hz}$, $24\text{ dB/octave}$) to prevent artificial penalty in sub-bass regions where small bookshelf speakers cannot physically output sound.
- **FR-002**: Validation targets MUST be unified between `scripts/verify_calibration.py`, `scripts/peq_optimizer.py`, and `scripts/web_calibration_server.py` to eliminate discrepancy between optimization targets and verification scoring targets.
- **FR-003**: The target generator MUST support both 2.0 bookshelf setups ($f_c = 64\text{ Hz}$) and bass-managed subwoofer setups ($f_{\text{crossover}} = 80\text{ Hz}$).

### 3.2 Multi-Target Benchmarking Engine
- **FR-004**: The verification engine MUST calculate alignment metrics (RMS error in dB, maximum peak deviation in dB, and S-TIER score percentage) for any measured curve against all defined target curves in `config/targets.json`.
- **FR-005**: The system MUST generate a comparative cross-target table (e.g. Preset vs Target Matrix) showing the fit of each mode (`through`, `ypao_flat`, `ypao_natural`, `ypao_front`, `manual`) against the 5 primary community target categories.
- **FR-006**: When evaluating a preset against its native target, the system MUST report whether the preset achieves target alignment within $\le 2.0\text{ dB}$ RMS across the core modal and midrange band ($60\text{ Hz} - 5\text{ kHz}$).

### 3.3 Dashboard and Report Visualization
- **FR-007**: The web server API MUST provide an endpoint (`/api/targets` or `/api/validation_targets`) returning the mathematical target vectors across the active frequency grid for all available profiles.
- **FR-008**: The web dashboard graph canvas MUST support toggling secondary target curves as reference dashed lines to allow immediate visual comparison of measured responses against alternative standards.
- **FR-009**: PDF and image report generators (`scripts/verify_calibration.py`) MUST support an optional multi-target comparison plot displaying the measured response alongside the native target and secondary reference curves.

### 3.4 Professional 1-to-1 Calibration & Historic Preset Explorer
- **FR-010**: The web dashboard MUST provide a direct 1-to-1 workflow per preset: deploy PEQ $\rightarrow$ sweep verification $\rightarrow$ render single-preset plot (Through vs PEQ vs Native Target) with the 3 primary engineering metrics.
- **FR-011**: The system MUST support browsing and reloading historical verification runs (`/api/sessions`) with full preset parameter pre-loading directly to the AVR hardware.
- **FR-012**: Complex multi-target comparative matrices MUST remain collapsible or secondary so they do not clutter the default professional 1-to-1 view.



### 3.5 Dark Studio Pro Responsive UX & Ergonomics
- **FR-013**: The web interface MUST follow the "Dark Studio Pro" design system inspired by professional audio suites (Dirac Live, Logic Pro): dark slate palette (`#0f172a`, `#1e293b`), crisp typography, border glows on active states, and zero generic placeholder AI styling.
- **FR-014**: All primary touch/click controls (Start Sweep, Calibrate, Test Profile, Save Preset) MUST have a minimum height of 48px with clear tactile visual feedback (hover/active states, active border highlight) for effortless one-handed smartphone operation at the listening position.
- **FR-015**: The interface MUST be fully responsive across mobile (>=360px), tablet, and desktop (up to 4K displays) using CSS flex/grid layouts, scalable font sizing, and collapsible auxiliary telemetry panels.
- **FR-016**: Visual state transitions (measurement progression, sweeps, preset loading, graph updates) MUST utilize GPU-accelerated CSS micro-animations (fade, slide, progress pulse) that convey meaningful operational state without causing layout shifts.

---

## 4. Key Entities & Data Contracts

### 4.1 Target Profile Schema (`TargetProfile`)
- `id`: Unique identifier string (`harman_wide_room`, `bk_1974`, `dirac_live`, `cinema_blockbuster`, `audiophile_flat`).
- `name`: Display name and community pedigree.
- `house_curve_params`: Low-frequency shelf boost, transition frequency, high-frequency slope.
- `cutoff_hz`: High-pass corner frequency (default 64.0 Hz for 2.0 bookshelf).

### 4.2 Cross-Target Validation Matrix (`ValidationMatrix`)
- `measurement_mode`: Measurement identifier (`through`, `ypao_flat`, `ypao_natural`, `manual`).
- `scores`: Mapping of `target_id` to:
  - `rms_error_db`: Root mean square deviation from 60 Hz to 5 kHz.
  - `max_peak_error_db`: Maximum single-frequency deviation.
  - `fidelity_score_pct`: Normalized fidelity score (0 - 100%).
  - `target_fit_rating`: Qualitative grade (S-TIER, A, B, C).

---

## 5. Success Criteria & Verification Metrics

- **SC-001**: **Target Consistency**: 100% of mathematical target curves generated across all scripts (`verify_calibration`, `peq_optimizer`, `web_calibration_server`) yield identical frequency vectors within $< 0.05\text{ dB}$ tolerance.
- **SC-002**: **No False Bass Penalty**: In 2.0 bookshelf mode, evaluating an uncorrected speaker against the target curve below 60 Hz does not degrade the score due to natural speaker roll-off.
- **SC-003**: **Multi-Target Comparability**: The system can evaluate and render any measured curve against any of the 9 defined presets within $< 50\text{ ms}$ compute time.
- **SC-004**: **Interactive Overlay**: Users can toggle between at least 5 distinct reference targets in the web interface and observe updated delta metrics without page reloads.
- **SC-005**: **Studio Pro Mobile & Desktop Ergonomics**: 100% of interactive calibration buttons conform to $\ge 48\text{px}$ touch targets and render seamlessly with zero horizontal overflow on mobile screens down to $360\text{px}$ width.
- **SC-006**: **Responsive Interaction Latency**: Visual state transitions and animations complete in $< 250\text{ ms}$ with zero frame drops on standard mobile and desktop browsers.

---

## 6. Assumptions & Non-Goals

### Assumptions
- The physical speakers remain Q Acoustics 3020i with a nominal -3 dB point around 64 Hz in free space.
- The AVR is the Yamaha RX-V673 operating in 2.0 (Large) mode without active subwoofer for primary baseline calibration.

### Non-Goals
- Modifying the physical Yamaha PEQ hardware parameters on the receiver during read-only target comparisons (conforms to Constitution Principle II).
- Forcing a single universal target curve on users who prefer alternative acoustic voicings (e.g. B&K 1974 analog warmth vs Harman neutrality).
