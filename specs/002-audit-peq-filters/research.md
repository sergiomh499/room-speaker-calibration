# Research: PEQ Filter Audit & Verification Architecture

## Executive Summary
This document investigates and establishes the mathematical and acoustic criteria for evaluating whether the 7-band parametric EQ filters calculated for the Yamaha RX-V673 and Q Acoustics 3020i are physically accurate, suboptimal, or erroneous.

---

## 1. Audit Criteria & Discrepancy Detection

### Decision
The audit analyzer evaluates three distinct tiers of criteria:
1. **Modal Resonance Alignment (< 500 Hz)**:
   - Evaluates detected physical resonance peaks from the empirical 80/20 composite acoustic response (80% Sweet Spot, 20% Spatial Average).
   - Flags any modal filter whose center frequency deviates by more than ±5.0 Hz from a physical peak, or any filter applied to a flat/null region.
2. **Gain & Q Directionality**:
   - Strictly enforces negative gain (attenuation only, max boost = 0.0 dB) for all room modal bands.
   - Verifies that filter Q matches the physical half-power bandwidth ($\Delta f = f_0 / Q$) of the resonance to avoid over-narrow notch ringing or excessive broad attenuation.
3. **Hardware Discrete Quantization**:
   - Validates that $f_0 \in \text{YAMAHA\_FREQS}$ (28 standard 1/3-octave steps), $Q \in \text{YAMAHA\_QS}$ (0.5 to 10.08), and $\text{gain} \in [-12.0, +3.0]\text{ dB}$ (0.5 dB steps).
   - Evaluates whether non-modal bands (> 500 Hz) address documented speaker acoustic crossover traits (e.g. 2.5-3.5 kHz driver transition) or represent arbitrary equalization.

### Rationale
Acoustic room correction below the Schroeder frequency (~300-500 Hz) is minimum-phase; room modes behave as resonant biquad poles. Applying positive gain to room modes drives the amplifier into clipping and exacerbates time-domain ringing. Misaligning a notch filter by even 5-10 Hz misses the resonance peak while creating an artificial dip adjacent to the mode.

### Alternatives Considered
- *Auditing only against the Sweet Spot*: Rejected per user clarification (Option A selected, 80% Sweet Spot + 20% Spatial Average prevents false-positive warnings on seat-localized comb notches).
- *Continuous frequency comparison without quantization*: Rejected because the physical AVR firmware discards non-discrete frequencies, making continuous mathematical evaluation detached from hardware truth.

---

## 2. Quantitative Metric Scoring & Health Classification

### Decision
The audit yields a deterministic classification:
- **ACCURATE (VERIFIED)**: All modal filters align within ±5 Hz of measured room modes, zero positive boost under 500 Hz, hardware parameters 100% discrete, and residual RMS error improved by $\ge 15\%$.
- **SUBOPTIMAL**: Filters target approximately correct regions but use un-snapped values, suboptimal Q, or leave major room modes (> 5 dB prominence) unaddressed.
- **ERRONEOUS**: Filters apply positive boost to room modes, target flat regions with deep notches (> 6 dB cut), or degrade overall target fit compared to Through (bypass).

### Rationale
Provides non-specialist audio enthusiasts with a clear, definitive verdict while providing acoustic engineers with the exact numeric delta per band.

---

## 3. Re-Optimization Integration Pattern

### Decision
Integrate the audit CLI and API directly with `scripts/peq_optimizer.py`. If the audit flags the active filters as SUBOPTIMAL or ERRONEOUS, the tool calculates the optimal filter matrix and outputs a side-by-side delta table comparing the current filters versus the recommended filters.

### Rationale
Users who discover their filters are miscalculated need an immediate, verified correction path without manually re-entering frequencies or guessing parameters.
