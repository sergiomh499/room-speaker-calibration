# Feature Specification: Audit and Verification of PEQ Filter Calculations

**Feature Branch**: `002-audit-peq-filters`

**Created**: 2026-09-03

**Status**: Draft

**Input**: User description: "los filtros peq no parecen bien calculados, comprueba si es cierto"

## Clarifications

### Session 2026-09-03
- Q: Which acoustic measurement baseline should the audit use as the ground-truth reference when evaluating whether the active PEQ filters match your room's physical resonances? → A: Weighted composite: 80% Sweet Spot (Point 1) + 20% 5-point spatial average.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Diagnostic Audit of Active PEQ Filters Against Room Acoustics (Priority: P1)

As a listener and audio enthusiast, I want to verify whether the 7 parametric EQ filters currently generated for my speakers accurately target the real physical acoustic resonances of my room, so that I can know with certainty whether the equalization is effective or flawed.

**Why this priority**: If the filters are miscalculated or placed at incorrect frequencies, the audio quality degrades, boomy bass resonances remain uncorrected, and listener fatigue occurs. Verifying truth versus error is the foundational requirement before any correction can be applied.

**Independent Test**: Can be fully tested by running an audit check that evaluates the current active PEQ filter set against the empirical sweet-spot measurement data and outputs a pass/fail diagnostic report with frequency alignment error margins.

**Acceptance Scenarios**:

1. **Given** an active PEQ filter configuration and baseline room acoustic measurements, **When** the audit verification is requested, **Then** the system compares each filter's center frequency, bandwidth (Q), and gain against actual measured room resonance peaks and identifies any misalignment greater than 5 Hz.
2. **Given** filters assigned to frequencies with no corresponding room resonance or room gain, **When** the diagnostic check runs, **Then** the system flags those specific filter bands as anomalous and explains the acoustic discrepancy.

---

### User Story 2 - Detection of Mathematical and Hardware Constraint Violations (Priority: P2)

As an acoustic engineer or system operator, I want the system to detect invalid parameter values such as positive boost on room modes, excessively narrow Q factors, out-of-grid center frequencies, or filter clipping, so that the amplifier hardware and speakers are never driven into distortion.

**Why this priority**: Applying positive gain to room boundary modes or using Q factors unsupported by the hardware can overload the amplifier channels, distort the speaker drivers, or produce unnatural ringing.

**Independent Test**: Can be tested independently by supplying intentionally invalid filter values (e.g., +6 dB boost on a modal peak, un-snapped frequencies) and verifying that the audit system detects and rejects 100% of the violations.

**Acceptance Scenarios**:

1. **Given** a filter configuration containing positive gain in the room modal region (< 500 Hz), **When** the validation rules execute, **Then** the system flags the positive gain as a violation of room acoustics best practices.
2. **Given** any filter frequency or Q value that does not match the discrete hardware capability of the receiver, **When** parameter checking runs, **Then** the system reports the exact quantization error and indicates the nearest valid hardware step.

---

### User Story 3 - Automated Re-Optimization and Observable Comparison (Priority: P3)

As a listener, I want to see a side-by-side mathematical comparison between the questionable filter set and an optimal newly recalculated filter set, so that I can clearly see the predicted acoustic improvement before applying changes to my receiver.

**Why this priority**: Identifying a problem is only half the solution; providing a verified, provably superior alternative with transparent metrics enables an informed decision.

**Independent Test**: Can be tested independently by taking a flagged suboptimal filter set, generating an optimized alternative, and verifying that the simulated acoustic response shows reduced residual error and improved frequency linearity.

**Acceptance Scenarios**:

1. **Given** a filter set diagnosed as suboptimal, **When** re-optimization is triggered, **Then** the system computes a revised 7-band filter set that demonstrates a measurably lower deviation from the target curve.
2. **Given** the revised filter set, **When** the comparison is displayed, **Then** the user sees before-and-after metrics including modal attenuation depth, stereo balance symmetry, and overall target alignment.

---
### Edge Cases

- How does the system handle an audit request when no physical measurement file exists?
  - The system must abort gracefully with an explicit message indicating that real empirical measurement data is required and refusing to evaluate simulated or fake curves.
- What happens if the room exhibits fewer than 7 resonant peaks below the transition frequency (500 Hz)?
  - Remaining bands must default to neutral (0.0 dB gain) rather than applying speculative or unnecessary filtering in the high-frequency spectrum.
- How does the system handle resonance peaks that fall halfway between two discrete hardware frequencies?
  - The system must evaluate the residual error of snapping to the upper versus lower frequency step and select the one that produces the lowest overall RMS error.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST extract and evaluate all 14 active biquad filters (7 Left channel, 7 Right channel) against the composite acoustic reference baseline weighted as 80% primary listening position (Sweet Spot) and 20% 5-point spatial average mesh.
- **FR-002**: System MUST identify the top physical room resonance peaks below 500 Hz for both Left and Right channels and compare their center frequencies to the deployed filter frequencies.
- **FR-003**: System MUST calculate the frequency alignment discrepancy for each filter band and flag any filter deviating by more than ±5.0 Hz from a measured peak or target adjustment zone.
- **FR-004**: System MUST enforce that all modal filters (< 500 Hz) apply attenuation (negative gain) with maximum boost strictly clamped to 0.0 dB.
- **FR-005**: System MUST verify that every frequency, Q factor, and gain step exactly matches the discrete parameter tables supported by the Yamaha RX-V673 hardware.
- **FR-006**: System MUST compute the simulated composite transfer function with the filter set active and quantify the residual RMS error against the active target curve (e.g., Harman In-Room Target).
- **FR-007**: System MUST output a clear diagnostic audit summary stating definitively whether the current filter calculation is ACCURATE, SUBOPTIMAL, or ERRONEOUS, accompanied by quantitative evidence.
- **FR-008**: System MUST provide the mathematically optimal filter parameters if the active set is determined to be suboptimal or erroneous.

### Key Entities

- **Filter Audit Report**: A structured evaluation containing the verification status of each channel, list of detected room modes, frequency alignment deltas, gain validity flags, and overall verdict.
- **Room Resonance Profile**: The set of empirically detected acoustic room modes below 500 Hz characterized by center frequency, prominence, and estimated Q bandwidth.
- **Parametric Filter Band**: An individual equalization band defined by band index (1-7), channel (Left/Right), center frequency (Hz), quality factor (Q), and gain (dB).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The diagnostic audit evaluation completes and delivers a comprehensive verdict in less than 3 seconds after invocation.
- **SC-002**: Frequency alignment discrepancies between filters and true room resonance peaks are quantified with numerical precision of 0.1 Hz.
- **SC-003**: 100% of mathematical or hardware violations (such as positive modal boost or non-hardware discrete values) are detected and flagged without false negatives.
- **SC-004**: If re-calculation is required, the revised filter set achieves at least a 15% reduction in residual RMS error across the 60 Hz - 500 Hz band compared to the suboptimal filter set.
- **SC-005**: The audit report presents an unambiguous, non-technical verdict understandable by non-specialist users, backed by concrete numerical indicators.

## Assumptions

- Empirical baseline acoustic measurements (`medicion_real_calibracion.npz` or `medicion_punto_1.npz`) exist and represent genuine microphone captures with acceptable signal-to-noise ratio.
- The target equalization curve used for reference is the standard Harman In-Room Target with 64 Hz high-pass boundary modeling matching the Q Acoustics 3020i specifications.
- Room modal behavior is concentrated below the room transition (Schroeder) frequency (~300-500 Hz); high-frequency filtering above 1 kHz is reserved strictly for documented native speaker crossover anomalies.
