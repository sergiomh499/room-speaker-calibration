# Feature Specification: Professional Standalone Android Acoustic Calibration Suite

**Feature Branch**: `012-pro-android-calibration`

**Created**: 2026-10-09

**Status**: Draft

**Input**: User description: "profesionaliza el proyecto de cara a que sea realmente usable y utilizable, y util al fin y al cabo, quiero maxima eficiencia y una experiencia profesional donde se vea exactamente como afecta la calibracion, curvas reales, no inventada, quiero profesionalidad y uso, finalmente quiero que sea unicamente una aplicacion movil android"

## Clarifications

### Session 2026-10-09

- Q: How should the standalone Android mobile application route the acoustic measurement sweep signals to the Yamaha audio/video receiver? → A: Dual-mode: Support direct physical cable (USB-C/3.5mm to AVR V-AUX) as the high-precision standard, plus wireless UPnP/DLNA casting over Wi-Fi as a convenience option.
- Q: How should the mobile application manage frequency calibration curves for the device's built-in microphone versus external USB measurement microphones? → A: Bundled device profile + Custom .cal import: Provide a tested baseline profile for the primary internal microphone, plus full support to import standard .cal calibration files for USB measurement microphones.
- Q: Should auxiliary non-calibration features (such as internet radio streaming) be removed from the mobile application? → A: Dedicated Calibration Suite: Purge auxiliary streaming player modules; keep only acoustic calibration, receiver hardware control, and acoustic analysis tools.
- Q: How should the AVR hardware control surface be integrated into the mobile app alongside the calibration suite? → A: Dedicated AVR Control Tab: A primary navigation tab offering full receiver hardware control (Power, 0.5 dB Volume dial, Inputs, PEQ Mode A/B toggle, Pure Direct, Channel Trims, and Scene selection).
- Q: How should the Android mobile application store and persist calibration sessions, impulse responses, and historical measurement data? → A: Structured Hybrid Storage: Store session metadata, discrete PEQ biquads, and frequency response vectors in local structured database storage for instantaneous retrieval, keep raw impulse responses in app-private storage, and provide a one-tap "Export Calibration Archive" (ZIP/PDF) to device storage.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Standalone Mobile Acoustic Sweep & Real Response Analysis (Priority: P1)

An audio enthusiast or sound engineer performs an acoustic room calibration directly from their Android mobile device without requiring any external PC, terminal session, or background server running. The mobile application coordinates the playback of synchronized logarithmic sine sweeps through the receiver, captures uncompressed raw audio through the calibrated microphone, performs on-device digital deconvolution against the inverse sweep filter, and extracts genuine impulse responses and frequency spectra. The user inspects real, physically measured acoustic curves—with zero simulated or synthesized placeholders.

**Why this priority**: Core value and foundation of the product. The user's primary mandate is a truly standalone Android app that delivers genuine acoustic physics and un-faked curves with maximum computational efficiency.

**Independent Test**: Can be tested independently by launching the Android application, connecting to the local receiver over Wi-Fi, capturing an acoustic sweep via the phone's microphone, and observing the rendered frequency response curve and physical room metrics (SPL, signal-to-noise ratio, time-of-flight delay, speaker distance) derived directly from recorded audio samples.

**Acceptance Scenarios**:

1. **Given** the mobile app is connected to the local network with the receiver accessible, **When** the user triggers an acoustic sweep for the Left or Right channel, **Then** the app plays the synchronized excitation sweep, records uncompressed audio, executes on-device deconvolution, and presents a genuine measured frequency response curve within 3 seconds.
2. **Given** an acoustic measurement has been captured, **When** the user reviews the acoustic diagnostic card, **Then** all displayed metrics (peak SPL in dB, signal-to-noise ratio in dB, arrival time in milliseconds, and speaker distance in meters) are calculated deterministically from the recorded impulse response without arbitrary hardcoded offsets.
3. **Given** an ambient noise event occurs during measurement (e.g., sudden noise floor spike), **When** the signal-to-noise ratio falls below acceptable acoustic limits (< 14 dB), **Then** the application flags the measurement as invalid, provides clear guidance on room conditions, and prompts for a clean re-take.

---

### User Story 2 - Empirical Before-and-After Calibration Comparison with Closed-Loop Verification (Priority: P2)

The user wants to see exactly how the calibration alters their room acoustics in the real world. After calculating discrete parametric equalization filters and deploying them into the receiver's DSP memory, the application guides the user through an empirical post-calibration verification sweep. The app renders an overlay displaying:
1. The baseline pre-calibration measured curve,
2. The selected target curve (e.g., Harman In-Room, B&K 1974),
3. The calculated parametric filter transfer function, and
4. The actual post-calibration measured curve.
The user clearly sees the authentic physical correction delta—showing standing wave room modes attenuated and the real frequency balance achieved.

**Why this priority**: Directly satisfies the user's requirement for "una experiencia profesional donde se vea exactamente como afecta la calibracion, curvas reales, no inventada". Real verification closes the loop and proves that calibration actually improved the room's sound.

**Independent Test**: Can be tested independently by taking a baseline measurement, deploying a calculated filter set to the receiver, executing a verification sweep in the same position, and confirming that the application graphs both curves simultaneously and calculates the real acoustic variance delta across bass, midrange, and treble bands.

**Acceptance Scenarios**:

1. **Given** an active calibration filter set is deployed to the receiver, **When** the user initiates the verification step, **Then** the app records a verification sweep with the receiver's manual PEQ engaged and plots the actual post-calibration acoustic curve.
2. **Given** both baseline and verification measurements exist for the same profile, **When** viewing the comparison screen, **Then** the app displays an authentic visual overlay showing pre-calibration response, post-calibration response, target response, and PEQ transfer function, clearly indicating the dB reduction of modal peaks.
3. **Given** the comparison view is displayed, **When** the user toggles individual curves (e.g., hide target, show delta), **Then** the chart updates immediately without reloading or re-estimating data.

---

### User Story 3 - Guided Professional Calibration Wizard & Zero-Touch Deployment (Priority: P3)

The user follows a streamlined, ergonomic mobile wizard specifically designed for touch interaction that handles the entire calibration lifecycle: receiver discovery and health check, microphone profile selection (with optional calibration file support), topology selection (2.0 stereo or 2.1 with active subwoofer), single- or multi-point spatial measurement sequence with audio-visual countdown cues, automated subwoofer crossover and level balance, and one-tap atomic hardware deployment with automatic pre-flight state backup and instant rollback.

**Why this priority**: Ensures the system is "realmente usable y utilizable, y util al fin y al cabo" by removing friction, technical jargon, and manual configuration hurdles while preserving professional acoustic rigor.

**Independent Test**: Can be tested independently by stepping through the wizard from step 1 to final deployment, checking that every step validates prerequisites before allowing progression, and verifying that the receiver's pre-flight state is backed up and restorable on demand.

**Acceptance Scenarios**:

1. **Given** the user launches the calibration flow, **When** selecting a 2.1 topology, **Then** the wizard guides the user through main speaker sweeps, subwoofer integration, crossover recommendation, and relative channel level matching.
2. **Given** the user triggers deployment of calculated filters, **When** the deployment completes, **Then** the receiver's DSP parameters are atomically programmed, the active mode is confirmed via read-back, and a success confirmation is displayed.
3. **Given** the user cancels or aborts the session at any point, **When** requesting a rollback, **Then** the receiver's pre-calibration settings are restored within 2 seconds.

---

### User Story 4 - Historical Calibration Management & Multi-Profile Auditing (Priority: P4)

The user maintains multiple calibration sessions and profiles over time (e.g., evaluating different target curves like Harman vs. B&K, or testing speaker repositioning and room acoustic treatment). The mobile app stores historical measurement archives locally, allows side-by-side metric comparison, and lets the user re-deploy previously validated filter sets directly to the receiver without repeating the physical sweep process.

**Why this priority**: Adds long-term utility and professional workflow flexibility, enabling iterative room tuning and comparative listening sessions.

**Independent Test**: Can be tested independently by saving two distinct calibration runs under different profiles, switching between them in the history view, comparing their real frequency responses, and deploying a saved historical filter set directly to the receiver.

**Acceptance Scenarios**:

1. **Given** multiple calibration sessions have been completed, **When** the user opens the history view, **Then** the app lists all sessions with timestamps, active target profiles, average SPL, and verification status.
2. **Given** a historical session is selected, **When** the user taps "Deploy to Receiver", **Then** that session's filter matrix is pushed to the hardware and verified via status read-back.


### User Story 5 - Real-Time Receiver Hardware Control & Acoustic Monitoring (Priority: P3)

The user adjusts and monitors their receiver's physical acoustic state directly from the mobile app without having to locate the physical remote control. Through a dedicated "AVR Control" navigation tab, the user smoothly adjusts master volume with a precise 0.5 dB dial, switches audio inputs, toggles between Manual PEQ, YPAO, and Through bypass modes for instant A/B acoustic verification, toggles Straight or Pure Direct listening, and fine-tunes individual channel trim levels in real time.

**Why this priority**: Essential companion to acoustic calibration that enables instant A/B subjective evaluation and everyday receiver operation without switching applications.

**Independent Test**: Can be tested independently by opening the AVR Control tab, rotating the volume dial to verify immediate 0.5 dB receiver response, and toggling PEQ Mode to confirm the receiver switches between Manual and Through modes over the local network.

**Acceptance Scenarios**:

1. **Given** the app is connected to the receiver on the local network, **When** the user accesses the AVR Control tab, **Then** live status (power, active input, volume in dB, PEQ mode, and DRC state) is displayed within 1 second.
2. **Given** the user rotates or taps the volume control, **When** adjusting volume, **Then** commands are debounced to prevent network flooding and the receiver's volume updates in exact 0.5 dB increments.
3. **Given** the user wants to evaluate calibration impact during music playback, **When** toggling the PEQ mode button between "Manual" (calibrated) and "Through" (unprocessed), **Then** the receiver immediately switches DSP mode without changing input or volume.
---

### Edge Cases

- **Receiver Network Unreachable**: If the receiver's IP address changes or the Wi-Fi connection drops, the app must display an intuitive offline banner with automated subnet scan, manual IP entry, and clear diagnostic status rather than crashing or freezing.
- **Microphone Permission Denied**: If audio recording permission is revoked or not granted, the app must display a clear explanation of why microphone access is required for acoustic measurement and provide a direct link to system settings.
- **Severe Acoustic Clipping / Mic Distortion**: If the sweep playback volume causes the input signal to exceed −0.5 dBFS or saturate the microphone pre-amp, the app must abort the deconvolution, flag digital clipping, and instruct the user to reduce receiver master volume by a specified dB amount.
- **Excessive Ambient Noise**: If background noise (HVAC, street traffic, voices) causes the signal-to-noise ratio to fall below 14 dB, the app must reject the sweep, highlight the problematic frequency band, and recommend re-measuring in quiet conditions.
- **Physical Remote Interference**: If another user changes the receiver's volume or input selector via physical remote during an active calibration session, the app's pre-flight check must detect the state mismatch and prompt the user to re-align receiver state before continuing.
- **Subwoofer Inactive or Unpowered**: If measuring a 2.1 system and the subwoofer produces no measurable acoustic output above the ambient noise floor during its dedicated sweep, the app must notify the user to verify subwoofer power, line-in connection, and gain knob setting.
- **DLNA Buffer Latency / Wireless Network Jitter**: When using wireless UPnP/DLNA casting mode, network buffer variance or packet jitter can shift arrival timing. The system must employ an acoustic synchronization pre-ping or cross-correlation lead-in to accurately align the deconvolution window regardless of network transmission delay.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST operate entirely as a self-contained mobile Android application without requiring any external computer, desktop browser, or companion daemon to execute calibrations.
- **FR-002**: The mobile application MUST execute real on-device digital deconvolution of recorded logarithmic sine sweeps against the theoretical inverse sweep filter to obtain authentic acoustic impulse responses.
- **FR-003**: The system MUST compute frequency response magnitudes strictly from the fast Fourier transform of windowed impulse responses, prohibiting any synthetic, randomized, or mock curve generation.
- **FR-004**: The system MUST apply standard psychoacoustic fractional-octave smoothing (1/12th or 1/24th octave) to real frequency responses for clear, professional visual interpretation while preserving physical standing wave peak and null boundaries.
- **FR-005**: The system MUST calculate physical acoustic metrics deterministically from recorded impulse responses, including direct sound arrival time (time-of-flight delay in ms), physical speaker distance in meters, peak sound pressure level in dB SPL, and signal-to-noise ratio in dB.
- **FR-006**: The system MUST communicate directly with the local network audio/video receiver over local Wi-Fi to read receiver status and transmit parametric equalizer filter matrices, channel trim levels, and speaker distances without routing through third-party cloud services.
- **FR-007**: The system MUST quantize all generated parametric filter parameters strictly to the discrete hardware parameter matrix supported by the receiver's DSP hardware (specific discrete center frequencies, discrete Q factors, and 0.5 dB gain quantization steps).
- **FR-008**: The system MUST enforce asymmetric gain constraints during filter optimization: maximum boost capped at +3.0 dB to prevent amplifier clipping, maximum attenuation clamped at −12.0 dB, and strict 0.0 dB boost limit above the room transition frequency (500 Hz).
- **FR-009**: The system MUST execute an empirical closed-loop verification sweep following filter deployment to capture and plot the real post-calibration acoustic response in the physical room.
- **FR-010**: The system MUST render an interactive before-and-after frequency comparison chart displaying the pre-calibration baseline curve, the selected target curve, the applied parametric filter transfer function, and the post-calibration verification curve on the same calibrated decibel and frequency axis.
- **FR-011**: The system MUST identify dominant room resonance modes below 500 Hz and report the exact center frequency and peak elevation in dB, demonstrating quantitative modal attenuation after calibration.
- **FR-012**: The system MUST support single-point sweet spot calibration as well as multi-point spatial cluster averaging (3 to 5 positions) using complex vector averaging to eliminate positional comb-filtering artifacts.
- **FR-013**: The system MUST automatically capture and persist a snapshot of the receiver's operational settings prior to any hardware modification, enabling one-tap rollback to original settings.
- **FR-014**: The system MUST support microphone frequency response compensation via bundled reference calibration profiles for supported internal smartphone microphones (such as Google Pixel 9 Pro UNPROCESSED) and allow user import of standard 90-degree `.cal` text calibration files for external USB measurement microphones (such as miniDSP UMIK-1 or Dayton UMM-6).
- **FR-015**: The system MUST provide an integrated local network receiver discovery mechanism to detect the receiver's IP address automatically on the local Wi-Fi network.
- **FR-016**: The system MUST support dual-mode audio excitation delivery: direct physical line out (USB-C or 3.5mm analog/optical to receiver V-AUX input) as the high-precision timing reference, and wireless UPnP/DLNA casting over the local network as an alternative convenience mode.
- **FR-017**: The mobile application MUST maintain a strictly dedicated acoustic scope by excluding auxiliary internet radio streaming, external music players, or background media scrapers, maximizing runtime performance and battery efficiency.
- **FR-018**: The system MUST provide a dedicated receiver hardware control view accessible via primary navigation that enables real-time management of power state, master volume in discrete 0.5 dB steps, input selector, DSP PEQ mode (Manual vs. Through vs. YPAO), Straight/Pure Direct modes, and individual channel trim levels directly over local network control.
- **FR-019**: The system MUST employ structured hybrid local persistence: session metadata, target curves, filter matrices, and smoothed frequency spectra stored in indexed local database storage for instantaneous chart rendering and offline comparison, with raw impulse responses saved in app-private sandboxed storage, and provide a one-tap export function to export complete session archives (ZIP/PDF) to device storage.

### Key Entities

- **Acoustic Measurement**: Represents a single spatial audio capture event. Contains channel designation (Left, Right, Subwoofer), raw PCM audio buffer, deconvolved impulse response, arrival peak sample index, time-of-flight delay, physical distance, signal-to-noise ratio, and calibrated frequency response magnitude vector.
- **Spatial Measurement Point**: Represents a designated physical listening position (e.g., primary sweet spot, left seat, right seat). Encapsulates acoustic measurements for all active audio channels at that position.
- **Calibration Session**: Represents a complete calibration run. Includes unique identifier, timestamp, room topology (2.0 or 2.1), selected target profile, microphone profile, collection of spatial measurement points, optimized parametric filter set, receiver pre-flight snapshot, and verification measurement.
- **Target Profile**: Represents the intended acoustic voicing curve across the 20 Hz to 20 kHz spectrum (e.g., Harman In-Room, B&K 1974, Flat). Defines bass shelf gain, high-frequency roll-off slope, and subwoofer crossover target.
- **Parametric Filter Band**: Represents a single discrete biquad filter. Contains channel, band index (1 through 7), center frequency (snapped to hardware frequency table), quality factor Q (snapped to hardware Q table), gain in dB (clamped and snapped to 0.5 dB steps), and acoustic functional role (room mode notch, voicing, or tilt).
- **Receiver State Snapshot**: Encapsulates receiver configuration prior to calibration. Stores power state, input selection, master volume, channel trim levels, speaker distances, and existing PEQ settings for disaster recovery and rollback.
- **Verification Audit Record**: Represents the comparative acoustic result. Contains pre-calibration baseline spectrum, post-calibration verification spectrum, target curve, filter transfer response, and quantitative delta metrics (e.g., peak modal reduction in dB, overall root-mean-square error reduction against target).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user can complete an entire end-to-end acoustic calibration (from initial setup to verified post-calibration playback) directly on their Android phone in under 5 minutes.
- **SC-002**: 100% of frequency response curves displayed to the user (baseline, verification, and comparison) are computed deterministically from real recorded audio data, with zero synthetic, mock, or randomized curves.
- **SC-003**: On-device deconvolution, impulse response windowing, and FFT frequency extraction execute in under 2.5 seconds per sweep on standard Android mobile hardware.
- **SC-004**: The post-calibration verification sweep confirms a measurable reduction of dominant room resonance peaks (below 500 Hz) of at least 3.0 dB to 8.0 dB compared to the pre-calibration baseline.
- **SC-005**: 100% of deployed filter parameters (frequencies, Q factors, gains) conform strictly to the receiver's discrete hardware DSP grid, with zero rejected commands or parameter clamping errors during hardware programming.
- **SC-006**: In the event of a user cancellation or session interruption, full restoration of the receiver's pre-calibration state is achievable in a single tap in under 2.0 seconds.
- **SC-007**: 95% of first-time users can successfully complete a full room calibration without encountering unrecoverable errors or requiring external technical assistance.
- **SC-008**: The mobile application operates autonomously on the local Wi-Fi network without requiring an active internet connection or any external computer running.

## Assumptions

- The Android device is connected to the same local Wi-Fi network (subnet) as the audio/video receiver.
- The audio/video receiver supports network control over standard HTTP XML protocol (Yamaha Network Control / YNC).
- The user's Android device has an operational microphone supporting uncompressed audio capture at 48 kHz (built-in microphone or connected USB measurement microphone such as miniDSP UMIK-1).
- The acoustic environment during measurement is reasonably quiet (ambient noise floor sufficiently below the reference measurement sweep level).
- Room mode acoustic treatment and parametric equalization are physically most effective and minimum-phase below the room Schroeder transition frequency (~500 Hz); frequencies above this threshold represent direct speaker voicing rather than standing wave correction.
- The physical receiver is configured with speakers wired in correct acoustic polarity and placed in standard listening geometry.
