# Feature Specification: Ground-Truth Empirical PEQ Calibration & Target Curve Realignment (2.0 Bookshelf Architecture)

**Feature Branch**: `010-ground-truth-peq-math`

**Created**: 2026-09-04

**Status**: Draft

**Input**: User description: "sigue sin estar bien calculados los peq manuales, tienes que validar uno a uno que los calculos que se realizan para el calculo de los mismos son correctos, empieza haciendolos desde cero y no tengas en cuenta precepciones anteriores, consulta en internet en perplexity cada una de ellas para cercionarte de que son los adecuados y optimos, y no se estan realizando invenciones o erratas y que se corresponden a los calculos adecuados para llegar a la curva deseada partiendo de las mediciones realizadas y fijadas en el workflow establecido. ademas dale una vuelta y revisa que los perfiles que estan cargados efectivamente a agosto de 2026 son los mejores para un consumo de musica y cine, con un sistema 2.0 o similar al que está actualmente montado, valorando el ajuste en funcion de la configuracion de altavoces que hay. estudia como hacen los calculos ypao y audissey y otras empresas para la calibracion y obtencion de los presets y usa esas mismas tecnicas y mejoradas para obtener una experiencia perfecta"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ground-Truth Mathematical Derivation of 7-Band Manual PEQ Filters (Priority: P1 MVP)

As an audio calibrator using a stereo 2.0 bookshelf system (Yamaha RX-V673 + Q Acoustics 3020i), I want the 7 PEQ filters per channel to be derived directly from verified transfer function mathematics (second-order biquad equations, Robert Bristow-Johnson Audio EQ Cookbook) matching the measured room transfer function against the target curve, without arbitrary heuristic offsets, static overrides, or invented band parameters.

**Why this priority**: Correcting room modes and loudspeaker interaction requires strict mathematical fidelity. Inaccurate filter calculation distorts phase, degrades stereo imaging, or wastes valuable DSP bands on spurious corrections. A ground-truth calculation engine guarantees that every single dB and Q value corresponds to the exact physical transfer function required to reach the target curve.

**Independent Test**: Provide an empirical sweep measurement dataset; execute the optimization solver; verify that every calculated band ($F_c$, Gain, $Q$) accurately predicts the post-filter acoustic response via true cascaded biquad complex frequency response ($H(z)$), reducing root-mean-square (RMS) error against the target curve strictly below the Schroeder frequency ($\le 500\text{ Hz}$).

**Acceptance Scenarios**:

1. **Given** spatial acoustic measurements (Punto 1 Sweet Spot 70% / Cluster 30%), **When** the optimizer calculates the 7 PEQ bands for Left and Right channels, **Then** each band represents an exact parametric biquad peak/notch filter whose combined response minimizes error to the target curve using discrete Yamaha hardware frequencies and Q values.
2. **Given** the 7 hardware bands available per channel, **When** allocating filters across the audio spectrum, **Then** all available bands are prioritized for the modal boundary ($\le 500\text{ Hz}$) and verified loudspeaker acoustic crossover anomalies, leaving non-modal high-frequency regions untouched (0.0 dB) to preserve minimum-phase direct sound.
3. **Given** asymmetric room modes (e.g., Left at 125 Hz, Right at 198 Hz), **When** allocating discrete filter slots, **Then** the system guarantees discrete frequency alignment and zero frequency collision, pairing active notches with neutral 0.0 dB transparent pass on the opposing channel to maintain stereo phase balance.

---

### User Story 2 - Target Curve Auditing and Selection for 2.0 Bookshelf Systems (August 2026 Benchmark) (Priority: P2)

As a music and home-cinema listener without a dedicated subwoofer (pure 2.0 channel setup with 5-inch bookshelf drivers), I want the loaded target curves to reflect modern acoustic research (Harman/Toole in-room preference curve, Brüel & Kjær 1974, Dirac Live house curves) adapted specifically to the acoustic limits of small bookshelf speakers, avoiding unnatural high-frequency brightening or forced sub-bass boosting below driver cutoff ($F_3 \approx 64\text{ Hz}$).

**Why this priority**: Standard full-range room target curves assume multi-subwoofer setups capable of flat extension down to 20 Hz. Forcing bookshelf speakers with a 64 Hz port tuning to reproduce heavy sub-bass induces severe mechanical excursion distortion and amplifier clipping. Target curves must adapt their low-frequency roll-off to match the physical boundaries of the installed speakers while maintaining the natural high-frequency decline preferred in human psychoacoustics.

**Independent Test**: Load the active target curves into the system; verify that curves for 2.0 systems incorporate a high-pass acoustic slope below 50-60 Hz, an elevated bass warmth shelf (+3 to +5 dB around 80-150 Hz), and a progressive treble roll-off (-0.8 to -1.0 dB/octave above 1 kHz), matching peer-reviewed blind listening research.

**Acceptance Scenarios**:

1. **Given** a 2.0 speaker profile (Q Acoustics 3020i), **When** generating the target curve, **Then** the curve prevents boost requests below the loudspeaker mechanical cutoff ($F_3 = 64\text{ Hz}$), protecting the amplifier power stage and voice coil excursion.
2. **Given** movie vs. music listening modes, **When** selecting presets, **Then** cinema profiles feature a robust modal bass foundation and gentle high-frequency roll-off (compensating for near-field dialogue clarity), while music profiles maintain linear decay and transparent phase coherence.
3. **Given** community-ranked profiles in `config/targets.json`, **When** auditing curve definitions, **Then** all 9 profiles are verified against authoritative literature (Sean Olive / Floyd Toole AES papers, Dirac Live standard target, Dolby cinema curves) with documented academic citations.

---

### User Story 3 - Implementation of Industry-Standard Multi-Pass Optimization Techniques (YPAO R.S.C. & Audyssey MultEQ XT32 Paradigms) (Priority: P3)

As an audiophile, I want the calibration engine to implement multi-pass optimization techniques similar to advanced commercial systems (YPAO Reflected Sound Control and Audyssey MultEQ XT32), including spatial averaging with variance weighting, peak-priority damping (treating narrow peaks before broad dips), and speaker-boundary interaction filtering.

**Why this priority**: Commercial leaders achieve high fidelity not by running simple moving averages, but by separating minimum-phase modal resonances (which can be inverted via PEQ) from non-minimum-phase boundary cancellations (which must never be boosted). Emulating and improving these techniques ensures professional-grade acoustic correction on consumer AVR hardware.

**Independent Test**: Run synthetic and empirical test sweeps with artificial comb filtering and standing wave peaks; confirm the algorithm identifies and completely attenuates resonant peaks while strictly ignoring non-minimum-phase destructive nulls.

**Acceptance Scenarios**:

1. **Given** a measured frequency response with a deep cancellation dip (-12 dB) caused by quarter-wave boundary reflection, **When** computing filters, **Then** the engine limits positive boost to a maximum of +3.0 dB (or 0.0 dB if dip is narrow), preventing amplifier overload and phase smearing.
2. **Given** multipoint spatial measurements, **When** combining responses, **Then** spatial averaging applies variance-based weighting: peaks that appear consistently across all seats are aggressively cut, while local seat-specific variations receive moderate damping.

---

### Edge Cases

- **Severe Room Null ($< 60\text{ Hz}$)**: If room geometry creates an acoustic cancellation null below driver cutoff, the system applies zero boost (0.0 dB) to prevent driver bottoming-out.
- **Microphone Measurement Incoherence**: If spatial variance across the 5 points exceeds 15 dB in the high frequencies (> 5 kHz), the system disregards high-frequency variations and restricts PEQ calculations to the reliable modal zone ($\le 500\text{ Hz}$).
- **Hardware Snapping Quantization**: If the optimal mathematical peak frequency falls halfway between two discrete Yamaha PEQ frequencies (e.g. 135 Hz between 125 Hz and 157.5 Hz), the solver evaluates the transfer function at both candidates and selects the one minimizing residual RMS error.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST calculate all 7 PEQ bands per channel using strict second-order biquad transfer function mathematics ($H(z) = \frac{b_0 + b_1 z^{-1} + b_2 z^{-2}}{1 + a_1 z^{-1} + a_2 z^{-2}}$) with zero heuristic or invented parameters.
- **FR-002**: System MUST validate each computed filter against the exact discrete frequency (Hz), gain (dB), and Q factor steps supported by the Yamaha RX-V673 hardware architecture.
- **FR-003**: System MUST restrict room modal correction strictly below the room Schroeder transition frequency ($\le 500\text{ Hz}$), preventing acoustic phase degradation in diffuse high-frequency sound fields.
- **FR-004**: System MUST audit and adapt all target curves in `config/targets.json` to 2.0 bookshelf acoustic specifications, enforcing a natural low-frequency roll-off below speaker $F_3$ (64 Hz for Q Acoustics 3020i) and a psychoacoustic high-frequency slope (-0.8 to -1.0 dB/octave above 1 kHz).
- **FR-005**: System MUST implement peak-priority modal damping (YPAO/Audyssey paradigm), giving highest priority to resonant peaks with $Q \ge 2.0$ while strictly prohibiting positive boosting of non-minimum-phase acoustic cancellation nulls.
- **FR-006**: System MUST ensure stereo band alignment between Left and Right channels, pairing independent asymmetric modes with transparent 0.0 dB settings on the opposing channel to maintain stereo phase coherence.
- **FR-007**: System MUST provide transparent verification metrics for each calculated band, reporting exact center frequency, attenuation depth, filter bandwidth, and predicted residual RMS error reduction.

### Key Entities *(include if feature involves data)*

- **BiquadFilter**: Mathematical representation of an IIR second-order parametric filter, characterized by center frequency ($F_c$), gain ($G$ in dB), quality factor ($Q$), sampling rate ($F_s$), and coefficients ($b_0, b_1, b_2, a_1, a_2$).
- **AcousticTargetProfile**: Electroacoustic target response curve defining desired in-room SPL across 20 Hz - 20 kHz, including speaker-specific high-pass cutoff and high-frequency roll-off parameters.
- **ModalOptimizationResult**: Data structure encapsulating the 7 discrete bands per channel, pre/post predicted RMS error, modal peak reduction, and stereo alignment diagnostics.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Mathematical solver achieves residual RMS error reduction of at least 2.5 dB across the modal band (40 Hz - 300 Hz) compared to uncalibrated Through response.
- **SC-002**: 100% of calculated filter bands match discrete Yamaha RX-V673 register steps without quantization clipping or runtime rounding exceptions.
- **SC-003**: Zero positive boost ($> 0.0\text{ dB}$) is allocated to narrow acoustic dips ($Q \ge 3.0$), eliminating risk of amplifier thermal strain or speaker driver damage.
- **SC-004**: All 9 community target profiles in `config/targets.json` are audited and verified against August 2026 acoustic literature for 2.0 stereo setups, with zero ungrounded heuristic curves.
- **SC-005**: Full stereo optimization and dynamic coefficient calculation completes in under 100 milliseconds.

## Assumptions

- Target listening system is configured in pure 2.0 stereo (Yamaha RX-V673 amplifier with Front speakers set to Large, Subwoofer set to None).
- Q Acoustics 3020i physical specifications ($F_3 \approx 64\text{ Hz}$, 5-inch bass driver, 0.9-inch decoupled tweeter, 6-ohm nominal impedance) represent the physical acoustic constraint for low-frequency extension.
- Speed of sound in room environment is assumed to be $343\text{ m/s}$ ($20^\circ\text{C}$ air temperature).
- Yamaha RX-V673 discrete frequency table spans 28 discrete frequencies per band (31.3 Hz to 16.0 kHz) and discrete Q factors spanning 0.500 to 10.08.
