# Feature Specification: Tight Sweet-Spot Multipoint & Hardware Profile Calibration

**Feature Branch**: `006-hardware-sweetspot-calibration`

**Created**: 2026-09-04

**Status**: Draft

**Input**: User description: "sigue teniendo front l unos valores extraños en el peq, hagamos calibracion multipunto alrededor del sweet spot solo , permite ademas que pueda seleccionarse el micro, el amplificador, los altavoces"

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Tight Sweet-Spot Multipoint Calibration Workflow (Priority: P1) 🎯 MVP

As an audio calibrator, I want the multipoint measurement process to focus exclusively within a tight 15–20 cm cluster around the primary listening position (sweet spot), so that the spatial average reflects genuine ear-level listening physics rather than room boundary extremes, resolving artificial anomalies on Front L.

**Why this priority**: Wide multipoint sweeps (measuring far left/right/back) dilute localized modal peaks and introduce boundary-gain variance that causes Front L modal resonances (e.g. 119 Hz) to fall below the activation threshold after normalization, leaving Front L with flat/zero filters while Front R receives heavy cuts. A tight sweet-spot cluster provides high-fidelity modal averaging.

**Independent Test**: Execute a 5-point calibration restricted to a 15–20 cm radius around the ear position; run the optimizer and verify that both Front L and Front R receive proportional modal filters targeting true room resonances (predicted attenuation >= 3.0 dB on both channels).

**Acceptance Scenarios**:

1. **Given** the web calibration interface, **When** the user starts the multipoint measurement guide, **Then** visual placement instructions clearly direct measuring within a tight sphere around the listener's head (Point 1: Center Sweet Spot, Point 2: 15 cm Left Ear, Point 3: 15 cm Right Ear, Point 4: 15 cm Forward, Point 5: 15 cm Elevated).
2. **Given** tight sweet-spot measurement data, **When** the optimization engine runs, **Then** Front L modal peaks above target are actively identified and corrected with appropriate negative notch filters rather than collapsing to 0.0 dB.
3. **Given** the optimized PEQ table, **When** comparing Front L and Front R bass bands (60–300 Hz), **Then** both channels exhibit balanced modal attenuation without extreme discrepancies (max inter-channel bass gain difference <= 3.0 dB for shared modes).

---

### User Story 2 - Hardware Selector: Microphone, Amplifier, and Speakers (Priority: P2)

As a home theater and Hi-Fi enthusiast, I want to explicitly select and configure the active hardware chain (measurement microphone, amplifier/receiver model, and loudspeaker pair) from the dashboard, so that calibration parameters, crossover compensations, and hardware band limits match my exact equipment.

**Why this priority**: Different hardware imposes distinct physical constraints. The Yamaha RX-V673 has a discrete 7-band snapping matrix; Q Acoustics 3020i has a 64 Hz low-end extension and a 2.52 kHz crossover dip; microphones (e.g. Pixel 9 Pro vs UMIK-1) require distinct calibration compensation curves. Explicit hardware selection ensures mathematical optimization respects physical hardware boundaries.

**Independent Test**: Change the speaker selection or amplifier selection in the dashboard; verify that optimizer rules (crossover compensation frequency, allowable frequency bands, and lower cutoff guardrails) dynamically reconfigure according to the selected hardware profile.

**Acceptance Scenarios**:

1. **Given** the dashboard settings, **When** the user opens the Hardware Configuration panel, **Then** three dropdown selectors are presented:
   - **Microphone**: e.g., Smartphone (Pixel 9 Pro Calibrated), miniDSP UMIK-1 (90° Ceiling File), Dayton UMM-6, Generic Flat Mic.
   - **Amplifier / Receiver**: e.g., Yamaha RX-V673 (7 PEQ bands, YNC XML over LAN), Generic AVR (Manual PEQ).
   - **Loudspeakers**: e.g., Q Acoustics 3020i (64 Hz bass extension, 2.52 kHz crossover dip compensation), Generic Bookshelf (80 Hz high-pass), Floorstanding / Tower (40 Hz extension).
2. **Given** a change in hardware selection (e.g. selecting different speakers or mic), **When** the user saves the configuration, **Then** the hardware state is persisted in `config/hardware.json` and active optimizer constraints immediately reflect the chosen profile.
3. **Given** the active hardware selection, **When** generating technical PDF reports and calibration summaries, **Then** the exact selected hardware models are clearly documented in the system specifications table.

---

### User Story 3 - Real-Time Front L vs Front R Modal Symmetry Diagnostics (Priority: P3)

As an audio calibrator, I want an interactive diagnostic visualizer comparing Front L and Front R raw responses, target curves, and calculated filters side-by-side, so that I can immediately understand why each filter frequency and gain was assigned.

**Why this priority**: Users need transparency into why Front L or Front R received specific values, verifying that room modes are treated symmetrically and no unexpected zero-gain bands occur on active resonance peaks.

**Independent Test**: View the PEQ diagnostic card; verify that a side-by-side comparative table and frequency breakdown clearly displays the detected peaks, bandwidth in Hz, and filter assignments for both channels.

**Acceptance Scenarios**:

1. **Given** calculated PEQ parameters, **When** reviewing the channel diagnostics, **Then** a clear side-by-side table compares Front L and Front R detected peaks, Q factors, and filter gains.
2. **Given** any filter band with 0.0 dB gain, **When** inspecting its status, **Then** a descriptive explanation is provided (e.g. "Preservación anecoica", "Nulo acústico no amplificado", "Sin resonancia modal").

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The calibration measurement workflow MUST provide dedicated guidance for a "Tight Sweet-Spot Cluster" (maximum radius 20 cm around listener ear center), replacing wide-room measurement positioning.
- **FR-002**: The PEQ optimization engine MUST balance Front L and Front R level normalization and peak detection sensitivity to ensure genuine Front L room modes (such as ~115–125 Hz) receive active corrective notch filters.
- **FR-003**: The system MUST implement a persistent hardware configuration schema (`config/hardware.json`) storing selected microphone, amplifier, and speaker profiles.
- **FR-004**: The web calibration dashboard MUST provide an intuitive UI panel allowing users to view and switch the active:
  - Microphone profile (with associated frequency calibration offsets).
  - Amplifier profile (with associated PEQ band counts and discrete parameter matrices).
  - Loudspeaker profile (with low-frequency cutoffs, crossover frequencies, and voicing compensation).
- **FR-005**: The optimization engine MUST ingest the active hardware profile from `config/hardware.json` and dynamically bind optimization limits (such as speaker low-frequency extension and crossover compensation) to the selected hardware.
- **FR-006**: Default hardware configuration MUST be initialized to: Microphone: `Google Pixel 9 Pro (Calibrated Mic)`; Amplifier: `Yamaha RX-V673 (YNC XML Lan)`; Speakers: `Q Acoustics 3020i (Bookshelf)`.
- **FR-007**: Generated technical PDF reports MUST dynamically reflect the selected hardware profile components in Table 1 (System Configuration).
- **FR-008**: Hardware selection changes MUST NOT issue destructive writes to the amplifier until an explicit calibration deployment or test action is triggered.

---

### Key Entities

- **HardwareProfile**: Configuration container defining active hardware components:
  - `microphone`: ID, display name, calibration file/curve, input sensitivity.
  - `amplifier`: ID, display name, protocol (YNC XML), band count (7), discrete frequency matrix, discrete Q matrix, gain step.
  - `speakers`: ID, display name, low-frequency limit (-3 dB point), nominal impedance, crossover frequency, voicing dip compensation.
- **TightClusterMeasurement**: Set of 5 impulse response captures taken within a 20 cm sphere around the primary listening position.

---

## Success Criteria *(mandatory)*

- **SC-001**: Following tight sweet-spot calibration, Front L receives active modal correction (at least 2 active notch filters in the 60–300 Hz region targeting room modes) with RMS error reduction >= 1.5 dB.
- **SC-002**: Switching hardware profiles via the dashboard updates optimizer constraints in under 200 milliseconds.
- **SC-003**: 100% of generated PDF reports and verification summaries display the active hardware configuration.
- **SC-004**: Zero horizontal scrolling across viewports from 360px to 1920px when viewing hardware settings and tight calibration guidance.
- **SC-005**: Compliance with all Constitution principles (Hardware-First, Non-Destructive Telemetry, Profile Scoping, Measurement Immutability, Minimal Command Surface).

---

## Assumptions & Edge Cases

- **Assumptions**:
  - The primary physical hardware remains Yamaha RX-V673 and Q Acoustics 3020i, but the system must accommodate alternative hardware options cleanly without hardcoded strings.
  - Tight sweet-spot spatial averaging (80% sweet spot / 20% spatial average of points 2-5 within 15 cm) yields superior phase coherence for stereo imaging.
- **Edge Cases**:
  - Selection of a speaker profile with low bass capability (e.g. 40 Hz towers): optimizer must avoid cutting naturally extended low bass unless acoustic room resonance is detected.
  - Missing calibration file for a third-party microphone: system falls back gracefully to flat response with an informational warning.
