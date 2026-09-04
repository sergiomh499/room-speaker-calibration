# Feature Specification: Modal Notch Diagnostic and Acoustic PEQ Rationale (Front L 125 Hz Room Mode Analysis)

**Feature Branch**: `008-modal-notch-analysis`
**Created**: 2026-09-04
**Status**: Ready for Review
**Input**: User description: "realizadas mediciones pero carecen de sentido los valores de filtros peq calculados, el notch modal quirurjico en L a que se debe?"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Physical Acoustic Analysis of Front L 125 Hz Room Mode vs Front R Asymmetry (Priority: P1 MVP)

As an audio user who performed empirical acoustic measurements in the listening room, I want an authoritative physical and mathematical explanation of why a sharp surgical notch (-2.5 dB, Q=4.0-5.0 at 125 Hz) was computed exclusively for Front L while Front R has its primary mode at 198 Hz, so that I understand the physical boundary conditions of my room and trust the acoustic correction without doubting the measurement validity.

**Why this priority**: Without understanding the underlying wave physics (standing waves, boundary gain, wall reflections, and room dimensions), asymmetric filters appear "erroneous" or "senseless" to users expecting symmetrical stereo settings. Providing the exact physical mechanism gives confidence that the DSP is correctly solving a real room acoustic defect rather than misfiring.

**Independent Test**: Evaluate measured impulse and frequency responses in `data/medicion_promedio_espacial.npz`; demonstrate that Front L exhibits an empirical resonance peak of +6.32 dB at 118.7-125.0 Hz with an ultra-narrow 24.9 Hz bandwidth (Q=5.04), whereas Front R exhibits its dominant resonance at 198.4 Hz (+4.23 dB, Q=2.52), proving physical stereo boundary asymmetry.

**Acceptance Scenarios**:

1. **Given** real acoustic measurement data (`medicion_promedio_espacial.npz`), **When** analyzing the Front L response, **Then** the system demonstrates that 125 Hz corresponds to an axial room standing wave ($\lambda \approx 2.81\text{ m}$, half-wave $\approx 1.40\text{ m}$) caused by the left speaker's physical proximity to a room boundary or corner.
2. **Given** the detected peak at 125 Hz with Q=5.04, **When** explaining why the notch filter is "surgical" (high Q), **Then** the analysis proves that a wide filter (e.g. Q=1.0) would indiscriminately hollow out musical energy from 80 Hz to 200 Hz, while a high-Q notch strictly drains the resonant standing wave without gutting bass punch.
3. **Given** the comparison between Front L and Front R, **When** evaluating stereo symmetry, **Then** the analysis details why domestic listening rooms are acoustically asymmetric (doors, openings, furniture, asymmetrical wall distances), making independent L/R PEQ correction mandatory for precise stereo imaging.

---

### User Story 2 - Rationale for Inactive Bands (0.0 dB) and High-Frequency Voicing Boosts (Priority: P2)

As a home theater and Hi-Fi enthusiast, I want to understand why several PEQ bands (bands 1, 3, 4, 5, and 7) remain set to 0.0 dB and why band 6 applies a positive boost (+1.5 dB / +2.0 dB) at 2.52 kHz, so that I comprehend why modern professional DSP does not apply arbitrary equalization across all 7 available bands.

**Why this priority**: Traditional analog equalizers encouraged "smiley face" curves across all bands. Modern electroacoustics (Dr. Floyd Toole, Sean Olive, Earl Geddes) mandates that equalizers must never attempt to fill narrow acoustic cancellation dips (comb filtering) with positive boost, and must leave clean acoustic regions untouched (0.0 dB) to preserve minimum phase response.

**Independent Test**: Cross-reference the optimizer's acoustic rules (`SCHROEDER_FREQ_HZ = 500 Hz`, zero boost above Schroeder, and strictly selective modal cuts); show that keeping unaffected bands at 0.0 dB preserves amplifier headroom and avoids thermal strain, while the 2.52 kHz boost corresponds to loudspeaker design compensation (Q Acoustics 3020i crossover dip).

**Acceptance Scenarios**:

1. **Given** the 7-band constraint of the Yamaha RX-V673 DSP, **When** reviewing bands set to 0.0 dB, **Then** the explanation details that an unexcited frequency band must remain flat to avoid introducing phase distortion, unnecessary digital requantization, or unnatural coloration.
2. **Given** acoustic cancellation dips (nulls) in the measured room response, **When** explaining filter behavior, **Then** the rationale clarifies that pumping energy into a non-minimum-phase boundary cancellation only burns amplifier watts without increasing SPL at the listener's ears.
3. **Given** the +1.5 dB (L) / +2.0 dB (R) boost at 2.52 kHz, **When** examining loudspeaker specifications, **Then** the explanation documents that this is speaker-boundary crossover voicing (2.4 kHz crossover point between the 5-inch woofer and 0.9-inch decoupled tweeter), improving dialogue clarity and speech intelligibility.

---

### User Story 3 - Dashboard Modal Diagnostics & Educational Tooltips (Priority: P3)

As a user navigating the web calibration dashboard, I want the modal symmetry diagnostics and PEQ parameter table to include contextual explanatory tooltips and visual indicators explaining why each filter exists and what physical room dimension it corresponds to.

**Why this priority**: Exposing acoustic reasoning directly in the UI prevents user confusion immediately after measurement without requiring deep technical knowledge of acoustics.

**Independent Test**: Access `/` on the web calibration dashboard; verify that each band row in the PEQ table and the modal symmetry diagnostics card provide concise hover or subtext explanations (e.g. "Modo propio axial", "Compensación de cruce del altavoz", "Banda neutra preservada").

**Acceptance Scenarios**:

1. **Given** the web dashboard PEQ table, **When** inspecting Band 2 (125 Hz), **Then** a badge or tooltip clearly displays "Modo de sala L: $\lambda \approx 2.8\text{ m}$ (Q quirúrgico para evitar retumbo)".
2. **Given** inactive bands (0.0 dB), **When** viewing the interface, **Then** they are labeled "Preservación anecoica / Fase neutra".

---

### Edge Cases

- What happens if the user physically moves the speakers or adds acoustic bass traps? The 125 Hz resonance amplitude and Q factor will decrease, causing subsequent calibration sweeps to reduce the notch attenuation or shift its center frequency.
- What happens if the room has a severe cancellation null at 60 Hz? The system strictly prevents positive boost (> +3.0 dB) to defend the amplifier's power supply and prevent driver bottoming-out.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide an exhaustive physical and mathematical analysis of the Front L 125 Hz room resonance based on measured data in `data/medicion_promedio_espacial.npz`.
- **FR-002**: System MUST calculate the acoustic wavelength ($\lambda = v / f = 343 / 125 \approx 2.74\text{ - }2.86\text{ m}$) and associate it with domestic room axial dimensions and speaker wall boundaries.
- **FR-003**: System MUST document the mathematical definition of the Q factor ($Q = f_0 / \Delta f$) showing that the 125 Hz peak has $\Delta f \approx 25\text{ Hz}$ ($Q \approx 5.0$), requiring an ultra-narrow surgical notch to prevent phase smearing and loss of bass punch.
- **FR-004**: System MUST explain the physical cause of stereo asymmetry between Front L (125 Hz peak) and Front R (198 Hz peak) due to non-symmetric room boundaries.
- **FR-005**: System MUST justify why bands with 0.0 dB gain are optimal and intentional under modern psychoacoustic target curve standards (Dr. Floyd Toole / Sean Olive / AES).
- **FR-006**: System MUST explain the 2.52 kHz loudspeaker crossover dip compensation for the Q Acoustics 3020i 2-way architecture.

### Success Criteria *(measurable & technology-agnostic)*

- **SC-001**: Acoustic explanation explicitly accounts for 100% of the active and inactive PEQ bands in the calculated calibration profile.
- **SC-002**: Theoretical wavelength and room mode standing wave calculations match empirical peak frequencies within $\pm 3\text{ Hz}$.
- **SC-003**: User receives a complete, non-technical and professional synthesis resolving all doubts about the validity of their empirical room measurement.

## Assumptions

- Speed of sound in domestic air at ~20°C is assumed to be $343\text{ m/s}$.
- Q Acoustics 3020i has an acoustic crossover point at 2.4 - 2.5 kHz as published by the manufacturer.
