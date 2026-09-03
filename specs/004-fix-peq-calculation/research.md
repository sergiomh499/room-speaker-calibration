# Research & Technical Decisions: Acoustic PEQ Parameter Calculation Engine

**Feature**: `004-fix-peq-calculation`
**Date**: 2026-09-03
**Status**: Completed

## 1. Modal Resonance Peak Detection & Bandwidth Calculation

### Problem Statement
In the legacy implementation, `detect_modal_resonances` ran `scipy.signal.find_peaks` on the raw difference array (`error = response_db - target_db`) using only relative prominence. Consequently, minor local ripples within deep acoustic nulls or boundary dips (e.g. at 62.5 Hz and 78.7 Hz where the Front L response was already −10 dB to −18 dB below the target curve) were classified as "modal resonances" and assigned aggressive notch cuts (up to −10.5 dB). Furthermore, filter bandwidth was estimated using array index offsets (`f_sub[p - w/2]`) rather than physical frequency in Hertz, causing estimated Q factors to falsely peg at the maximum discrete limit ($Q = 10.080$).

### Decision: Absolute Error Gating & Frequency-Domain Bandwidth
1. **Positive Error Gating**:
   A peak is only classified as an actionable room mode if its elevation above the target curve satisfies:
   $$\Delta \text{SPL}(f_0) = \text{SPL}_{\text{measured}}(f_0) - \text{SPL}_{\text{target}}(f_0) \ge +1.5\text{ dB}$$
   If $\Delta \text{SPL}(f_0) < +1.5\text{ dB}$, the gain is strictly clamped to $0.0\text{ dB}$ (no cut, no boost).
2. **Physical Bandwidth Calculation ($\text{Hz}$)**:
   Bandwidth is computed by locating the exact frequencies where the resonant peak drops by 3.0 dB below its maximum on the continuous frequency axis ($f_{\text{high}} - f_{\text{low}}$ in Hz), using linear interpolation across `freqs_hz`.
3. **Q Factor Snapping**:
   $$Q = \frac{f_0}{\Delta f_{-3\text{dB}}}$$
   The continuous Q factor is snapped to the nearest discrete Yamaha RX-V673 Q value:
   $$\{0.500, 0.630, 0.794, 1.000, 1.260, 1.587, 2.000, 2.520, 3.175, 4.000, 5.040, 6.350, 8.000, 10.080\}$$

### Alternatives Considered
- **Unconstrained Polynomial / Spline Fitting**: Rejected because unconstrained high-order polynomial fits produce Runge's phenomenon (spurious oscillations) near frequency boundaries.
- **Machine Learning Auto-Regressive Modeling**: Rejected as an over-engineered abstraction; deterministic peak finding with physical acoustics rules is reproducible, auditable, and fast (< 10 ms).

---

## 2. Coordinated Left/Right Stereo Optimization Strategy

### Problem Statement
Physical room measurements show that both speakers excite common room standing waves (such as the axial room mode at 110–119 Hz where Left is +5.5 dB and Right is +3.2 dB to +5.0 dB). Applying a narrow notch to only one channel (e.g., at 125 Hz on Left only) disrupts the stereo soundstage, creates phase discrepancy, and leaves the right channel uncorrected.

### Decision: Two-Tier Coordinated Strategy
In accordance with Dr. Floyd Toole's psychoacoustic research and AES standards:
1. **Common Mode Detection**:
   If both channels detect a resonance peak within $\pm 5\%$ frequency of each other (e.g., between 110 Hz and 125 Hz), the optimizer links them to the exact same discrete Yamaha frequency and identical Q factor ($Q \le 3.500$).
2. **Symmetrical Base Cut with Asymmetric Gain Offset**:
   The shared frequency receives a common base attenuation matching the shared modal elevation, plus an optional channel-specific trim if one speaker exhibits higher boundary gain (e.g., Left against corner wall). The maximum independent trim difference between channels is constrained to $\le 3.0\text{ dB}$.
3. **Strict High-Frequency Invariant**:
   Above the Schroeder frequency (> 500 Hz), room modes do not exist. Any correction above 500 Hz must be symmetrical and restricted to anechoic loudspeaker voicing (such as the Q Acoustics 3020i 2.52 kHz crossover compensation).

### Alternatives Considered
- **Strictly Identical Global PEQ**: Rejected because real-world room boundaries are physically asymmetrical (living room open on the left, sidewall on the right). Pure global EQ cannot address genuine unilateral boundary loading.
- **Completely Uncoupled Channel Optimization**: Rejected because it produced the problematic single-sided notches and phase incoherence observed by the user.

---

## 3. Multi-Filter Biquad Interaction & Regularization

### Problem Statement
When multiple parametric filters are placed in proximity, their overlapping skirts compound. In the legacy code, 7 separate cuts of −6 dB to −10.5 dB compounded into −47.5 dB of total attenuation, gutting the lower octaves.

### Decision: Full Composite Response Modeling with Regularization
1. **RBJ Audio EQ Peaking Transfer Function**:
   Compute the exact complex transfer function $H_k(z)$ for each active biquad on the digital frequency grid ($f_s = 48\text{ kHz}$) and sum in decibels:
   $$H_{\text{total}}(f) = \sum_{k=1}^{7} 20 \log_{10} |H_k(e^{j 2 \pi f / f_s})|$$
2. **Cumulative Attenuation Guardrail**:
   At every frequency point $f \in [30\text{ Hz}, 500\text{ Hz}]$, the total composite response must not exceed:
   $$H_{\text{total}}(f) \ge -12.0\text{ dB}$$
3. **Acoustic Objective Function with Energy Penalty**:
   $$\text{Loss} = \text{RMS}( \text{SPL}_{\text{eff}}(f) + H_{\text{total}}(f) - \text{SPL}_{\text{target}}(f) ) + \lambda_{\text{suckout}} \cdot \max(0, -H_{\text{total}}(f) - 8.0)^2$$
   This penalizes solutions that create unnatural dips below the target curve.

---

## 4. Metric Naming Alignment Across Verification Engine and Web Server

### Problem Statement
In `scripts/verify_calibration.py`, the curve alignment percentage is stored as `"target_alignment_pct"`, but `scripts/web_calibration_server.py` extracted `c.fidelity_score_pct`. Because `c.fidelity_score_pct` was `undefined`, JavaScript evaluated the ternary fallback `typeof c.fidelity_score_pct === 'number' ? ... : 0`, resulting in 0.0% scores across the entire UI and PDF summaries.

### Decision: Dual-Key Exposure and Resilient Frontend Fallback
1. **Backend (`verify_calibration.py`)**:
   Include both keys in the dictionary output:
   ```python
   "target_alignment_pct": round(alignment_pct, 1),
   "fidelity_score_pct": round(alignment_pct, 1),
   ```
2. **Frontend (`web_calibration_server.py`)**:
   Update JavaScript extraction to check both keys with priority:
   ```javascript
   const scoreVal = (typeof c.target_alignment_pct === 'number') ? c.target_alignment_pct :
                    (typeof c.fidelity_score_pct === 'number') ? c.fidelity_score_pct : 0;
   ```
