# Feature Specification: Comprehensive Acoustic Engine Audit, Real Optimization Refactor, and Honest Verification Pipeline

**Feature Branch**: `001-audit-refactor-measurements`

**Created**: 2026-09-03

**Status**: Draft

**Input**: User description: "tengo sospechas de que actualmente el repositorio esta falseando muchas medidas, calculos estan mal y hay que hacer un gran refactor del repositorio, se intensivo y ponte con todo, cueste lo que cueste"

## Clarifications

### Session 2026-09-03

- Q: Should the 7-band PEQ optimization engine calculate independent center frequencies for each channel (Front L vs Front R) or enforce identical center frequencies with channel-independent Q and gain? → A: Option A - Independent center frequencies, Q factors, and gains per channel to precisely address room acoustic asymmetry (e.g. corner-loaded right speaker vs open-space left speaker).
- Q: When multi-point measurements exist, how should the optimization objective weigh the primary listening position (Sweet Spot) versus the spatial average of all surrounding points? → A: Option C - Strict Sweet Spot priority (80% Sweet Spot / 20% spatial average): Optimizes primarily for the main listening seat to maximize central stereo imaging and tonal accuracy, using secondary positions to prevent equalizing narrow localized phase cancellations.
- Q: What objective physical criteria must a live post-calibration sweep meet to be awarded the official "S-TIER (Certified)" rating? → A: Option A - Strict Multi-Metric: Peak modal resonance reduction >= 6.0 dB, modal RMS deviation from target < 2.5 dB (60-500 Hz), and inter-channel stereo level delta < 2.0 dB.
- Q: How should the iterative calibration workflow track, version, and compare sequential adjustment passes (e.g. Baseline Through → Initial PEQ → Refined Notch) in datasets and technical audit reports? → A: Option A - Structured Calibration Epochs (Iteration N): Numbered, immutable iteration snapshots (`iter_0_baseline`, `iter_1_peq`, `iter_2_refined`, etc.) with comparative convergence curves and delta tables in technical reports to validate adjustments a posteriori.
- Q: What specific acoustic visualizations and numerical audit sections must the technical post-calibration report include to formally certify that adjustments were executed correctly? → A: Option A - Comprehensive Technical Audit Suite: Magnitude frequency curves (1/24-octave & psychoacoustic), 3D Waterfall CSD temporal decay, exact Yamaha NVRAM register/biquad dump, and iterative epoch convergence table.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Honest & Verifiable Acoustic Measurement Audit (Priority: P1)

As an audio engineer or high-fidelity enthusiast calibrating speakers in a domestic room,
I want the calibration system to compute every filter, curve, and metric strictly from authentic, measured physical impulse response data,
So that I have 100% confidence that the audio correction reflects real physical acoustics without hidden simulations, hardcoded tables, or fabricated numbers.

**Why this priority**: The foundational credibility of the entire project depends on mathematical and acoustic integrity. Faked data or pre-calculated static values masquerading as dynamic room optimizations completely defeat the purpose of an acoustic calibration tool.

**Independent Test**: Can be fully tested by running the calibration pipeline on raw measurement data with altered acoustic peaks; the system must dynamically generate different, mathematically optimal filters targeting those exact peaks, proving zero hardcoded filter values are emitted.

**Acceptance Scenarios**:

1. **Given** a raw room impulse response with a prominent resonant room mode at 112 Hz, **When** the calibration analysis runs, **Then** the system calculates filter parameters derived mathematically from that specific resonance, and zero static fallback values from configuration files are injected.
2. **Given** any reported acoustic metric or chart, **When** the user inspects its provenance, **Then** the system explicitly displays the source file path, timestamp, signal-to-noise ratio, and verification status.

---

### User Story 2 - True Electroacoustic Parametric EQ Optimization (Priority: P2)

As a listener optimizing a Yamaha RX-V673 receiver with Q Acoustics 3020i speakers,
I want an algorithmic optimization engine that fits the receiver's 7 parametric biquad bands to compensate for measured room boundary reflections and modal resonances below 500 Hz,
So that the acoustic output matches psychoacoustic target curves (such as Harman In-Room Target) while strictly obeying Yamaha hardware limits.

**Why this priority**: Real room correction requires true mathematical curve fitting (least-squares / constrained non-linear optimization) mapped to discrete hardware center frequencies and Q steps. Static tables cannot adapt to real room variances.

**Independent Test**: Can be tested independently by feeding synthesized or measured acoustic transfer functions with known room modes; the optimization solver must output 7 biquad bands (frequency, Q, gain) within hardware constraints that minimize mean squared error against the target curve.

**Acceptance Scenarios**:

1. **Given** a measured spatial average frequency response, **When** the optimizer executes, **Then** it calculates up to 7 discrete PEQ bands per channel using only Yamaha-supported center frequencies (from 62.5 Hz to 16.0 kHz) and discrete Q factors (0.500 to 10.080).
2. **Given** room modes with severe dips (nulls) caused by destructive wave interference, **When** the optimization algorithm runs, **Then** it applies an asymmetric gain policy that caps positive gain boost at a safe maximum (+3.0 dB) and prioritizes deep resonant peak cuts (down to -12.0 dB).
3. **Given** frequencies above the room Schroeder / transition frequency (>500 Hz), **When** filters are computed, **Then** the optimizer preserves the native speaker directivity and applies 0.0 dB room-mode correction, applying only subtle broad shelf/tilt adjustments if explicitly mandated by the target.

---

### User Story 3 - Transparent & Strict Verification Certification (Priority: P3)

As a user assessing calibration quality,
I want the verification pipeline to demand a real, measured post-calibration sweep before issuing any certification badge or fidelity score,
So that I am never deceived by synthetic arithmetic sums (`baseline + filter`) pretending to be real acoustic proof.

**Why this priority**: A verification stage that simulates results with mathematical addition and stamps "S-TIER" gives a false sense of success while masking physical room distortion, driver nonlinearities, and port turbulence.

**Independent Test**: Can be tested by requesting verification when no post-calibration sweep file exists; the system must report "UNVERIFIED / PENDING LIVE SWEEP" and must refuse to award a passing grade until an actual hardware sweep is recorded.

**Acceptance Scenarios**:

1. **Given** a newly applied PEQ configuration on the receiver without a subsequent physical measurement, **When** the verification report is generated, **Then** the report marks the profile as unverified and does not compute or display a fake passing score.
2. **Given** a real post-calibration sweep recorded through the receiver, **When** comparative analysis runs, **Then** the system compares actual measured SPL before and after calibration against the target curve, reporting true RMS error, peak reduction in dB, and stereo balance delta.

---

### User Story 4 - Physically Accurate Audio Signal Chain & Routing (Priority: P4)

As an operator running frequency sweeps from a measurement PC,
I want the audio playback, capture, and receiver input routing to remain stable, synchronized, and free of conflicting inputs,
So that sweeps play through the intended analog/auxiliary channel without uncommanded input switching or digital clipping.

**Why this priority**: Conflicting input commands (such as switching to HDMI ARC AV4 while playing analog test signals) ruin measurement validity, capture ambient noise instead of test tones, or corrupt receiver settings.

**Independent Test**: Can be tested by initiating a measurement sweep; the system must verify receiver input selection, play the calibrated Farina logarithmic sine sweep, record impulse response with validated SNR (>14 dB), and leave user-selected operational inputs intact.

**Acceptance Scenarios**:

1. **Given** a measurement session, **When** test audio is generated, **Then** the system sends the sweep through the designated measurement channel, verifies receiver volume at a safe reference level (-25 dBFS), and validates that peak microphone input is within -24 dBFS to -3 dBFS without digital clipping.
2. **Given** background noise or an unseated microphone cable, **When** a sweep capture exhibits SNR under 14 dB or silent signal, **Then** the system aborts with a clear descriptive error rather than proceeding to compute corrupt acoustic data.

---

### Edge Cases

- **Hardware quantization mismatch**: A detected acoustic room resonance occurs at 114.5 Hz, but the Yamaha RX-V673 only supports discrete frequencies 99.2 Hz and 125.0 Hz in that octave. The optimizer must choose the discrete frequency and Q value that maximizes attenuation of the modal energy without creating adjacent audible notches.
- **Deep acoustic cancellations (nulls)**: A listener position experiences a 15 dB null at 82 Hz due to boundary destructive interference. The optimizer must recognize that room nulls cannot be equalized with positive boost without overloading the amplifier and causing driver excursion distortion; gain must be strictly limited to <= +3.0 dB.
- **Microphone frequency response distortion**: When an omnidirectional microphone lacks an individualized calibration file, the system must apply standard diffuse-field / free-field compensation curves and explicitly document the calibration uncertainty tolerance in the generated report.
- **Receiver network timeout or communication loss**: If the receiver fails to acknowledge a parameter write during filter deployment, the system must detect the transaction failure, display the uncommitted bands, and prohibit declaring the profile active until readback confirmation succeeds.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST calculate all parametric equalization filter parameters dynamically from empirical room acoustic measurements; when multi-point datasets exist, the optimization cost function MUST weight the primary Sweet Spot (Point 1) at 80% and the secondary spatial average at 20%, strictly prohibiting any reliance on static hardcoded filter parameter tables.
- **FR-002**: System MUST constrain all optimized parametric filter center frequencies, Q factors, and gains strictly to the discrete hardware parameter values supported by the Yamaha RX-V673 receiver architecture, computing independent center frequencies ($f_{0,L} \neq f_{0,R}$), Q factors, and gains for Front Left and Front Right channels to resolve room boundary asymmetry.
- **FR-003**: System MUST enforce an asymmetric acoustic gain policy for room-mode correction: maximum positive gain boost MUST NOT exceed +3.0 dB, maximum attenuation MUST reach down to -12.0 dB, and room-correction boosts above 500 Hz MUST be clamped to 0.0 dB.
- **FR-004**: System MUST eliminate all synthetic fallback calculations that construct simulated curves via arithmetic addition (`measurement + filter_curve`) and present them as verified room responses.
- **FR-005**: System MUST distinctly label every displayed frequency response curve with its verifiable provenance: `REAL_MEASUREMENT` (with source file, timestamp, and SNR) or `THEORETICAL_TARGET`.
- **FR-006**: System MUST withhold any "Certified" or "S-Tier" quality rating unless an authentic post-calibration acoustic sweep has been captured through the physical receiver hardware and strictly satisfies all three objective physical criteria: (1) peak modal resonance reduction $\ge 6.0\text{ dB}$, (2) residual RMS deviation from target $< 2.5\text{ dB}$ across the equalized modal band (60 Hz to 500 Hz), and (3) average inter-channel stereo level imbalance $< 2.0\text{ dB}$.
- **FR-007**: System MUST calculate acoustic quality and compliance metrics using standard, reproducible scientific formulations (unweighted and psychoacoustically smoothed RMS deviation in dB from target curve, inter-channel stereo level delta, and modal peak attenuation in dB) without arbitrary marketing multipliers or fixed offset baselines.
- **FR-008**: System MUST store raw impulse response and frequency response datasets in immutable, numbered epoch archive files (`iter_{N}_{stage}_{timestamp}.npz`), prohibiting unversioned overwrites of historical calibration records.
- **FR-009**: System MUST enforce consistent audio routing during measurement sweeps, verifying the active receiver input and output level before playback and validating that recorded signal levels do not exhibit digital clipping or inadequate signal-to-noise ratio.
- **FR-010**: System MUST provide an automated validation suite that executes the optimization and verification algorithms against reference benchmark datasets and asserts mathematical correctness, convergence, and parameter boundary compliance.
- **FR-011**: System MUST implement a structured Calibration Epoch progression model (`iter_0_baseline`, `iter_1_initial`, ..., `iter_N_refined`), recording the complete active PEQ filter matrix, raw impulse datasets, and post-sweep responses for each pass to enable verifiable a posteriori regression and convergence analysis.
- **FR-012**: System MUST generate an automated Technical Audit Report containing: (1) 1/24-octave and psychoacoustically smoothed magnitude response curves with target overlays, (2) cumulative spectral decay (CSD/waterfall) plots verifying time-domain modal ringing reduction below 300 Hz, (3) a complete hardware register dump of active Yamaha PEQ parameters (frequency, Q, gain) verified via YNC readback, and (4) an iterative epoch convergence table documenting step-by-step before/after acoustic deltas.

### Key Entities

- **Acoustic Transfer Function**: The complex frequency response derived from logarithmic sweep deconvolution, comprising frequency grid (Hz), magnitude response (dB SPL normalized), phase, impulse response array, and signal quality metrics (peak level dBFS, SNR dB, timestamp).
- **Hardware Parameter Space**: The discrete matrix of permissible values for the Yamaha RX-V673 DSP engine: 28 discrete center frequencies (62.5 Hz to 16.0 kHz), 14 discrete Q factors (0.500 to 10.080), and discrete gain steps (-12.0 dB to +6.0 dB in 0.5 dB increments) across 7 biquad bands, independently allocatable per channel (Front L and Front R).
- **Acoustic Target Curve**: Mathematical reference curve defining target in-room steady-state sound pressure as a function of frequency (e.g. Harman In-Room Loudspeaker Target Curve with bass rise and high-frequency roll-off).
- **Optimization Result**: The calculated set of 7 discrete biquad filters per channel, including expected residual variance, predicted peak resonance reduction, and mathematical convergence metrics.
- **Verification Audit**: Comparative evaluation comparing measured baseline (Through bypass) against verified post-calibration physical sweep, detailing real modal resonance reduction, residual RMS error, and certification status.
- **Calibration Epoch**: A versioned snapshot of a complete tuning pass containing iteration index ($N$), timestamp, description, applied PEQ matrix (7 bands per channel), raw impulse responses, smoothed magnitude curves, and residual RMS error against the target curve.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of generated PEQ filter configurations are computed algorithmically from acoustic measurement data, with zero reliance on hardcoded filter parameters in the execution path.
- **SC-002**: Measured modal resonance peaks in the sub-200 Hz band are attenuated by at least 6.0 dB in real physical post-calibration sweeps, verified without exceeding +3.0 dB gain boost at any frequency.
- **SC-003**: 0% of unmeasured or simulated curves receive "Certified", "Live Measured", or "S-Tier" designations across all reports, logs, and user interfaces.
- **SC-004**: Residual RMS error between measured acoustic response and the target curve in the equalized modal band (60 Hz to 500 Hz) achieves $< 2.5\text{ dB}$ (improving by at least 20% compared to uncalibrated baseline) and stereo imbalance $< 2.0\text{ dB}$ in physical verification tests.
- **SC-005**: Complete automated audit test suite verifies mathematical optimization convergence and discrete hardware boundary compliance in under 10 seconds.
- **SC-006**: 100% of calibration tuning iterations are traceable through numbered epoch manifests, generating step-by-step convergence graphs and delta tables that document measurable improvement across successive adjustment passes.
- **SC-007**: 100% of generated verification audit reports include cumulative spectral decay (CSD) plots, hardware register dumps, and iterative epoch delta tables alongside frequency magnitude curves.

## Assumptions

- The physical Yamaha RX-V673 receiver is connected to the local network at IP address 192.168.1.43 and responds to standard Yamaha Network Control (YNC) HTTP XML requests.
- The acoustic measurement signal chain utilizes an omnidirectional microphone connected to the host system with an available audio input device.
- Correction is focused on minimum-phase room modal phenomena below the room transition frequency (~300-500 Hz), preserving the native direct sound and crossover voicing of the Q Acoustics 3020i speakers above 500 Hz.
- The user operates in a stereo (2.0) listening configuration with front left and front right channels set to Large (full-range) as established in the project constitution.
