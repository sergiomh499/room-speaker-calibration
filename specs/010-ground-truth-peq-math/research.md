# Research: Ground-Truth Empirical PEQ Calibration & Multichannel Modular Architecture

## 1. Ground-Truth Biquad Transfer Function Mathematics (Robert Bristow-Johnson Audio EQ Cookbook)

### Decision
Implement the exact mathematical second-order IIR biquad transfer function $H(z)$ for peaking/notch filters, computing continuous complex frequency response and discrete sampling at $F_s = 48\text{ kHz}$ to model acoustic filter cascade:
$$H(z) = \frac{b_0 + b_1 z^{-1} + b_2 z^{-2}}{a_0 + a_1 z^{-1} + a_2 z^{-2}}$$

### Rationale
- Standard parametric equalizers in audio hardware (including Yamaha YPAO DSP and miniDSP engines) implement the standard RBJ peaking EQ equations:
  $$A = 10^{G / 40}$$
  $$\omega_0 = 2 \pi \frac{f_0}{F_s}$$
  $$\alpha = \frac{\sin(\omega_0)}{2 Q}$$
  $$b_0 = 1 + \alpha A, \quad b_1 = -2 \cos(\omega_0), \quad b_2 = 1 - \alpha A$$
  $$a_0 = 1 + \frac{\alpha}{A}, \quad a_1 = -2 \cos(\omega_0), \quad a_2 = 1 - \frac{\alpha}{A}$$
- The complex frequency response $H(e^{j\omega})$ evaluated along the frequency grid yields the exact magnitude in dB:
  $$\text{Gain}_{\text{dB}}(f) = 20 \log_{10} |H(e^{j 2 \pi f / F_s})|$$
- Simulating cascaded filters by summing individual complex transfer functions in the z-domain guarantees zero phase artifacts and accounts for adjacent band interactions (skirt overlap), matching real hardware acoustics.

### Alternatives Considered
- *Gaussian / Simplified Bell Approximation*: Simple $G \cdot \exp(-((f-f_0)/\Delta f)^2)$ fails at high frequencies and wide bandwidths due to lack of Nyquist wrapping and asymmetric skirts. Rejected in favor of exact biquad $H(z)$.
- *Static Lookup Tables*: Rejected because static tables disconnect calculated values from real physical measurement data.

---

## 2. Target Curves for 2.0 Bookshelf Architecture (August 2026 Peer-Reviewed State of the Art)

### Decision
Align the 9 target curves in `config/targets.json` with the acoustic limits of small bookshelf speakers (such as Q Acoustics 3020i with $F_3 = 64\text{ Hz}$):
1. **Low-Frequency Boundary**: High-pass acoustic Butterworth slope ($12\text{ dB/octave}$ to $24\text{ dB/octave}$) starting at $55-60\text{ Hz}$ in 2.0 mode, avoiding forced energy injection into the port cutoff. In 2.1+ mode, the high-pass boundary transitions to the receiver's configured crossover frequency (e.g. 80 Hz).
2. **Room Warmth Region (80 Hz - 200 Hz)**: Smooth $+3.0\text{ dB}$ to $+4.5\text{ dB}$ shelf (matching Harman / Sean Olive in-room preference).
3. **Midrange / Treble Transition**: Linear downward slope of $-0.8\text{ dB}$ to $-1.0\text{ dB}$ per octave from $1\text{ kHz}$ to $20\text{ kHz}$ to mirror natural diffuse-field room absorption.

### Rationale
- **Floyd Toole & Sean Olive Research**: A flat in-room target curve above the Schroeder frequency sounds thin, harsh, and overly bright because microphones capture reflected energy that the human brain naturally processes as spaciousness.
- **Loudspeaker Protection**: Forcing small 5-inch bookshelf woofers to reproduce flat energy down to 20-30 Hz causes mechanical bottoming-out, port turbulence, and high intermodulation distortion (IMD) in the midrange.

### Alternatives Considered
- *Full-range flat target (20 Hz - 20 kHz)*: Causes severe driver distortion and harsh high frequencies.
- *Unfiltered sub-bass boost on 2.0 setups*: Overloads the Yamaha power supply.

---

## 3. Commercial Optimization Paradigms (YPAO R.S.C. vs Audyssey MultEQ XT32 vs Dirac Live)

### Decision
Incorporate the best practices from industry calibration systems:
1. **Spatial Averaging with Variance Weighting (Audyssey MultEQ XT32 paradigm)**:
   - Resonant peaks that appear with low variance across all 5 spatial points are true room modes and are aggressively attenuated.
   - Spatial peaks with high variance (seat-dependent cancellations) are left unboosted to prevent destroying the sweet spot.
2. **Peak-Priority Attenuation (YPAO R.S.C. paradigm)**:
   - Standing wave resonances with high quality factor ($Q \ge 2.0$) are prioritized for surgical notch filters.
   - Non-minimum-phase cancellation dips receive $0.0\text{ dB}$ boost (strict anti-boost cap of $+3.0\text{ dB}$ only for broad speaker crossover dips).
3. **Schroeder Cutoff Boundary ($\le 500\text{ Hz}$)**:
   - Equalization is strictly confined below $500\text{ Hz}$ (plus verified manufacturer crossover correction at $2.52\text{ kHz}$ for Q Acoustics 3020i).

---

## 4. Multichannel Modular Extensibility (2.0 to 7.1 Channel Topologies)

### Decision
Design the solver and data structures to represent audio channels as an extensible map:
- `CHANNELS = ["L", "R", "C", "SW", "SL", "SR", "SBL", "SBR"]`
- In pure 2.0 stereo mode, active channels are strictly `["L", "R"]`.
- The data model and Yamaha communication layer (`send_peq_to_receiver`) parameterize the channel register path (`/Setup/Speaker/ManualSetup/PEQ/{channel}`), allowing seamless 2.1, 5.1, or 7.1 calibration when additional channels and microphones sweeps are supplied.
