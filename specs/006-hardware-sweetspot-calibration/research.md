# Research: Tight Sweet-Spot Multipoint & Hardware Profile Calibration

**Feature**: `006-hardware-sweetspot-calibration`
**Date**: 2026-09-04
**Domain**: Acoustic Engineering, Spatial Signal Processing & Hardware Configuration

---

## 1. Tight Sweet-Spot Clustering vs Wide Room Multipoint Sweeps

### Decision
Implement a focused 5-point measurement cluster strictly bounded to a 15–20 cm radius around the primary listening position (Point 1: Center Head / Eardrum level, Point 2: 15 cm Left Ear, Point 3: 15 cm Right Ear, Point 4: 15 cm Forward, Point 5: 15 cm Elevated). The spatial weighting is defined as **70% Center Sweet Spot (Point 1)** and **30% Spatial Average of satellite points (Points 2–5)**.

### Rationale
- Wide-room multipoint measurements (measuring seats 1 meter apart or near back walls) encounter disparate boundary loading and phase cancellations that do not represent the primary listener's direct perception.
- In 2026, state-of-the-art room correction systems (Dirac Live Focused/Tight mode, Trinnov Optimizer) recommend a tight cluster when optimizing for high-fidelity stereo soundstaging and pinpoint imaging.
- The 70/30 weighting guarantees that the primary head position anchors absolute tonal balance and driver alignment, while the 4 satellite points prevent the optimizer from boosting narrow, spatially fragile comb-filtering nulls.

### Alternatives Considered
- **Equal Arithmetic Average (20% each)**: Dilutes the critical central sweet spot and shifts the perceived acoustic center if furniture reflections vary across satellites.
- **Single-Point Sweet Spot Only**: Vulnerable to extreme narrow notches (comb filters) caused by headrest reflections that should not be equalized with PEQ.

---

## 2. Normalization Strategy: Broadband 300 Hz – 3 kHz vs Single 1.0 kHz Anchor

### Decision
Replace single-frequency anchor normalization (`sweet_l - sweet_l[idx_1kHz]`) with **broadband logarithmic energy averaging between 300 Hz and 3000 Hz**. Pair this with an **adaptive modal peak detection threshold (+1.0 dB above target)** in `detect_modal_resonances()`.

### Rationale
- The previous single-point normalization at 1.0 kHz was the primary root cause of the "strange values" on Front L: a localized room reflection at 1 kHz depressed Front L's entire bass curve below the `+1.5 dB` detection gate, causing the optimizer to find 0 modal peaks on Front L while finding 5 on Front R.
- The 300 Hz – 3 kHz octave band represents the speech and core musical band where human hearing is most sensitive to overall loudness and where loudspeaker directivity is predominantly determined by anechoic design rather than room modes.
- Broadband energy averaging integrates acoustic energy across this band, rendering the baseline impervious to single-bin dips or peaks.

### Alternatives Considered
- **Fixed 1.0 kHz Normalization with Lower Threshold (+0.2 dB)**: Still susceptible to narrow comb filters at 1 kHz shifting the overall channel gain by up to 4 dB.
- **Independent SPL Meter Calibration**: Requires external hardware SPL meter calibration hardware and manual user calibration steps.

---

## 3. Smoothing Algorithm: REW-Standard Variable Smoothing (Var)

### Decision
Implement REW-standard **Variable Smoothing (Var)** across frequency vectors:
- Heavy 1/3 octave smoothing below 80 Hz to prevent attempting to equalize narrow acoustic cancellation nulls.
- High-resolution 1/24 to 1/12 octave smoothing in the modal zone (80 Hz – 400 Hz) to clearly resolve genuine room mode standing waves.
- 1/6 to 1/3 octave smoothing above 1 kHz for psychoacoustic tonal balance.

### Rationale
- In small domestic listening rooms below the Schroeder frequency (~250–300 Hz), unsmoothed curves feature steep non-minimum-phase nulls. If the optimizer attempts to fill these nulls with boost, amplifier headroom is exhausted and distortion increases without audible bass improvement.
- Variable smoothing mirrors human auditory filter bandwidths (Equivalent Rectangular Bandwidth - ERB) while maintaining surgical fidelity on modal resonance ridges.

### Alternatives Considered
- **Fixed 1/6th Octave Smoothing**: Blunts narrow modal peaks in the 100–250 Hz range, causing filters to have too low a Q factor.
- **No Smoothing (1/48th or Raw)**: Creates erratic multi-peak fits with excessive filter overlap and amplifier clipping risk.

---

## 4. Hardware Profile Architecture & Schema

### Decision
Create a unified, persistent hardware configuration model in `config/hardware.json` with three core sections:
1. `microphones`: Active microphone selection, sensitivity offset, calibration curve file path, mandatory 90° orientation.
2. `amplifiers`: Active AVR/amp selection, protocol type (`ync_xml`, `manual`), discrete frequency matrix, discrete Q matrix, band limits (7 for RX-V673), gain limits (-12 dB to +3 dB).
3. `speakers`: Active speaker model, low-frequency -3 dB cutoff (e.g. 64 Hz for 3020i), crossover dip compensation frequency (e.g. 2.52 kHz), nominal impedance, recommended high-pass filter frequency.

### Rationale
- Decouples optimization logic from hardcoded physical assumptions.
- Allows seamless switching between standard equipment (Yamaha RX-V673 + Q Acoustics 3020i + Pixel 9 Pro) and upgraded laboratory gear (UMIK-1 + Dayton + generic amplifiers) without touching the core mathematical codebase.
- Adheres to Constitution Principle I (Hardware-First) and Principle V (Minimum Viable Command Surface).

---

## 5. Microphone Orientation and Calibration Loading

### Decision
Mandate **90° vertical orientation (pointing directly at ceiling)** for all room calibration sweeps. Pre-load standard manufacturer diffuse-field calibration curves for:
- Google Pixel 9 Pro (acoustic MEMS dual-mic array compensation)
- miniDSP UMIK-1 (90° diffuse-field curve)
- Dayton Audio UMM-6 (90° diffuse-field curve)
- Generic Flat (0 dB across all bands)
Provide an HTTP API endpoint (`/api/hardware/upload_mic_cal`) to allow users to upload their individual serial-numbered `.cal` or `.txt` file.

### Rationale
- Pointing a measurement microphone horizontally at 0° introduces directional bias: high frequencies from the on-axis speaker are boosted while reflections and opposite-channel signals are attenuated.
- A 90° orientation provides uniform 360° azimuthal sensitivity in the horizontal plane, essential for multipoint spatial averaging and stereo soundfield integration.
