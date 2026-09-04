# Phase 0 Research: Multi-Target Validation & Comparative Acoustic Benchmarking

**Feature**: `011-multi-target-validation`  
**Date**: 2026-09-04  

---

## 1. Unified Mathematical Target Curve Generation

### Problem
Previously, mathematical target curve calculations were scattered across `scripts/verify_calibration.py`, `scripts/peq_optimizer.py`, and `scripts/web_calibration_server.py`, causing subtle differences in transition knee formulations and roll-offs.

### Decision
Standardize all target generation in `scripts/peq_optimizer.py:generate_bookshelf_target_curve()` as the single source of truth:
1. **Low-Frequency High-Pass Model**:
   $$HPF(f) = 20 \log_{10}\left(\frac{1}{\sqrt{1 + (f_c / f)^4}}\right)$$
   Where $f_c = 64.0\text{ Hz}$ for 2.0 bookshelf speakers (Q Acoustics 3020i), or $f_{\text{crossover}} = 80.0\text{ Hz}$ when an active subwoofer is present.
2. **Psychoacoustic Reference Curves**:
   - **Harman / Floyd Toole**: +2.5 dB below 120 Hz, cosine knee transition to 200 Hz, -0.8 dB/octave treble slope.
   - **B&K 1974**: +3.0 dB below 100 Hz, linear descent to 400 Hz, -0.9 dB/octave analog treble rolloff.
   - **Dirac Live**: +2.0 dB shelf below 120 Hz, transition to 250 Hz, -0.6 dB/octave tilt above 1 kHz.
   - **Cinema / Blockbuster**: +3.5 dB sub-bass shelf below 120 Hz, transition to 200 Hz, -1.0 dB/octave above 2 kHz.
   - **Pure Audiophile Flat (Diffuse-Field)**: Flat 0.0 dB reference through audio band with 64 Hz speaker protection HPF.

### Rationale
Eliminates code duplication and guarantees that verification metrics reflect the exact mathematical target used during PEQ filter optimization.

---

## 2. Multi-Target Scoring & Alignment Metrics

### Problem
When a measurement is captured, it is only scored against its active profile. The user cannot see whether a curve like YPAO Flat actually scores better against Audiophile Flat or Harman, or how PEQ Manual performs against alternative house curves.

### Decision
Implement `evaluate_multi_target_alignment(freqs, resp_l, resp_r, target_keys=None)`:
- Computes for each target profile:
  - RMS Error across modal & midrange evaluation band (60 Hz – 5000 Hz):
    $$RMS = \sqrt{\frac{1}{N} \sum_{i} (Response_i - Target_i)^2}$$
  - Peak error in modal region: $\max |Response_i - Target_i|$ (60 – 400 Hz).
  - Fidelity Score (0 – 100%):
    $$Score = \max\left(0, 100 - (RMS \times 15.0)\right)$$
  - Classification: `S-TIER` ($\le 1.2\text{ dB}$ RMS), `A` ($\le 2.0\text{ dB}$), `B` ($\le 3.0\text{ dB}$), `C` ($> 3.0\text{ dB}$).

### Alternatives Considered
- *Full-band scoring (20 Hz - 20 kHz)*: Rejected because measurement mic noise floor > 16 kHz and room boundary interference below 30 Hz pollute fidelity scores without acoustic perceptual relevance.

---

## 3. Web Dashboard Target Overlay Integration

### Problem
The web calibration server UI renders the target curve as a single static green line corresponding to the current active profile.

### Decision
1. Expose `GET /api/targets` returning the vector points $(f, dB)$ for all defined profiles.
2. In the browser dashboard canvas, add a selector/toggle allowing users to overlay secondary target curves as dashed lines alongside the measured response.
3. Expose `POST /api/calibration/multi_target_eval` to return on-the-fly cross-target matrix for the current session measurements.

---

## 4. Professional 1-to-1 Calibration & Dedicated Verification Workflow

### Problem
Displaying massive tables comparing 9 targets simultaneously creates cognitive overload ("circle of confusion") and looks like a generic AI prototype rather than professional audio engineering software (like Dirac Live or REW). Furthermore, testing against multiple curves simultaneously misses the fundamental acoustic fact: each calibration preset was optimized for one specific target.

### Decision
1. Adopt the industry-standard 1-to-1 workflow: Select profile -> Deploy PEQ to AVR -> Execute Verification Sweep -> Render Dedicated Comparison:
   - **Before (Through/Uncorrected)**: Baseline room response.
   - **After (Measured Post-PEQ)**: Empirical response under active filters.
   - **Target**: The native target curve designed for this specific preset.
2. Focus telemetry on 3 essential engineering metrics:
   - **Modal Peak Reduction**: $\Delta\text{dB}$ attenuation of primary room modes ($< 300\text{ Hz}$).
   - **Stereo Symmetry ($|L - R|$)**: Average deviation between left and right channels ($< 1.5\text{ dB}$ target).
   - **Target Adherence**: Mid-band RMS deviation ($60\text{ Hz} - 3\text{ kHz}$) and qualitative grade (S-TIER / A / B).
3. Keep secondary multi-target benchmarking tables collapsed inside an optional "Acoustic Benchmark Matrix" accordion.

---

## 5. Dark Studio Pro Responsive UX Architecture

### Problem
Previous web UI had smaller buttons, fixed desktop dimensions, and standard web styles that felt like an amateur dashboard or prototype when operated from a smartphone at the listening sweet spot.

### Decision
1. Implement **Dark Studio Pro** design tokens:
   - Background: Deep slate/graphite (`#090d16` / `#0f172a` / `#1e293b`).
   - Accents: Studio Emerald (`#10b981`), Amber Warning (`#f59e0b`), Slate Border (`#334155`), Cyan Highlight (`#06b6d4`).
   - Typography: Clean sans-serif with tabular numerals for audio telemetry.
2. Ergonomic Touch Targets:
   - All primary action buttons (Start Sweep, Calibrate, Preload Preset) have minimum height of $48\text{px}$ with $12\text{px}-16\text{px}$ padding.
   - Tap states with `:active { transform: scale(0.98); }` and subtle glowing focus borders.
3. Mobile & Desktop Adaptability:
   - CSS Grid and Flexbox with media queries breakpoints: Mobile ($< 640\text{px}$), Tablet ($640\text{px} - 1024\text{px}$), Desktop ($> 1024\text{px}$).
   - Full-width charts on mobile, side-by-side telemetry panels on desktop.
4. Historic Session & Preset Preload:
   - Load saved sessions from `data/sessions/` and presets from `config/targets.json`.
   - One-click "Deploy Preset to Yamaha" button sending PEQ parameters directly via YNC XML without requiring re-computation or re-sweeping.

