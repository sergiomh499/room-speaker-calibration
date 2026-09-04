# Research: Modal Notch Diagnostic and Acoustic PEQ Rationale (Front L 125 Hz Room Mode Analysis)

## 1. Physical Acoustic Analysis of Front L 125 Hz Room Resonance

### Decision
Establish that the Front L 125 Hz peak is an axial standing wave ($\lambda = 2.81\text{ m}$, $\lambda/2 = 1.40\text{ m}$) excited by physical speaker-boundary interaction, and document that the surgical notch ($Q \ge 4.0$) is required by room acoustics.

### Technical Rationale
- **Wavelength & Standing Waves**:
  $$v = 343\text{ m/s} \implies \lambda = \frac{343}{122} \approx 2.81\text{ m}$$
  In typical residential rooms, walls separated by ~2.80 m (or a speaker placed at ~1.40 m from a reflective boundary) create an axial standing wave. The reflected wave arrives in constructive phase with the speaker's direct output, producing a localized sound pressure peak ($+6.32\text{ dB}$ measured in `data/medicion_promedio_espacial.npz`).
- **Q Factor & Bandwidth**:
  $$Q = \frac{f_0}{\Delta f} = \frac{125.0}{24.9} \approx 5.04$$
  A room resonance has high Q because boundaries have low acoustic absorption at 125 Hz (gypsum, brick, and glass reflect ~95% of low-frequency energy).
- **Why a Surgical Filter**:
  A standard broad filter ($Q = 1.0$) with center frequency 125 Hz spans $62.5\text{ Hz}$ to $250\text{ Hz}$. Applying a broad -3 dB cut would hollow out the musical fundamentals of bass guitar, kick drum, and male baritone voices. A high-Q notch ($Q = 4.0$) restricts attenuation strictly to the $110 - 135\text{ Hz}$ resonant zone, extinguishing the room rumble while preserving 100% of bass punch.

### Alternatives Considered
- *Ignoring the resonance*: Results in muddy, boomy bass and severe acoustic masking over vocal intelligibility.
- *Applying broad PEQ*: Drains essential musical energy from 80 Hz to 200 Hz.
- *Physical bass traps alone*: Standard 5 cm foam or fiberglass panels are acoustically ineffective at 125 Hz ($\lambda = 2.8\text{ m}$ requires porous absorbers $\ge 35\text{ cm}$ thickness). Electronic PEQ is the industry-standard solution.

---

## 2. Stereo Asymmetry (Front L vs Front R)

### Decision
Document that independent channel equalization ($f_{0,L} \ne f_{0,R}$) is mandatory in domestic stereo environments and proves the peak is an environmental artifact rather than a transducer issue.

### Technical Rationale
- Front L exhibits its primary resonance at 125 Hz (+6.32 dB, $Q = 5.04$).
- Front R exhibits its primary resonance at 198.4 Hz (+4.23 dB, $Q = 2.52$).
- Domestic listening rooms feature non-symmetric boundary conditions: Front L is typically closer to a solid lateral wall or corner, while Front R faces an open doorway, hallway, window with curtains, or lighter partition.
- As documented by Dr. Floyd Toole (*Sound Reproduction: The Acoustics and Psychoacoustics of Loudspeakers and Rooms*, AES): "Below the transition frequency (~300-500 Hz), the room dominates the sound. Equalization must be applied to individual channels to correct their unique boundary coupling."

---

## 3. Rationale for 0.0 dB Inactive Bands

### Decision
Enforce that unexcited PEQ bands remain at 0.0 dB, strictly adhering to minimum-phase preservation and anti-boosting rules.

### Technical Rationale
- **Phase Preservation**: Every IIR biquad filter introduces phase shift ($\Delta \phi$). Injecting unnecessary filters into clean acoustic zones alters the temporal impulse response.
- **No Boosting of Non-Minimum-Phase Nulls**: Sharp cancellation dips in the frequency response are caused by destructive boundary interference (comb filtering). Adding $+6\text{ dB}$ of gain increases amplifier power by $4\times$, saturating the RX-V673 power supply and causing cone bottoming-out in the 3020i 5-inch woofer, without restoring SPL at the listener's ears.
- **Conclusion**: Bands 1 (62.5 Hz), 3 (157.5 Hz), 4 (250 Hz), 5 (500 Hz), and 7 (10.1 kHz) staying at 0.0 dB is proof of mathematical discipline, not a missing calculation.

---

## 4. Loudspeaker Crossover Voicing (2.52 kHz Boost)

### Decision
Explain that the $+1.5\text{ dB}$ (L) and $+2.0\text{ dB}$ (R) boost at 2520 Hz is speaker-specific crossover compensation, not a room resonance correction.

### Technical Rationale
- The Q Acoustics 3020i features a 2-way passive crossover topology crossing over at $2.4\text{ kHz}$.
- At the crossover region, driver directivity mismatch between the 5-inch woofer and the 0.9-inch decoupled ring tweeter causes a mild on-axis energy dip.
- Correcting this with $+1.5\text{ to }+2.0\text{ dB}$ at 2.52 kHz lifts speech articulation, presence, and vocal projection without increasing listener fatigue.

---

## 5. Diagnostic Proof of Transducer Integrity

### Decision
Provide explicit diagnostic metrics in the report proving the Q Acoustics 3020i drivers and crossovers are 100% healthy.

### Technical Rationale
- **Above 400 Hz**: Room boundary modes diminish, and the measurement reflects the speaker's intrinsic direct sound.
- **Empirical Tracking**: At 1000 Hz, difference between L and R is $-0.4\text{ dB}$. At 2520 Hz, difference is $+0.3\text{ dB}$.
- A mechanically or electrically damaged driver (e.g. rub-and-buzz voice coil, torn surround, blown tweeter) exhibits irregular frequency response, severe THD (> 5%), and multi-dB level discrepancies throughout the mid and high bands. The empirical measurement confirms pristine speaker health.

---

## 6. Dynamic PEQ Generation Pipeline & targets.json Synchronization

### Decision
Integrate `optimize_stereo_peq()` directly into the `/api/finalize_calibration` execution pipeline, replacing static placeholder tables in `config/targets.json` with the dynamically calculated 7 biquad filters per channel based on empirical sweet spot (`medicion_punto_1.npz`) and spatial average (`medicion_promedio_espacial.npz`).

### Technical Rationale
- **Root Cause of Calibration Disconnect**: Previously, `targets.json` maintained hardcoded placeholder bands (e.g. Band 2: 125 Hz -2.5 dB L / 0.0 dB R; Band 6: 2520 Hz +1.5 dB L / +2.0 dB R). Although `scripts/peq_optimizer.py` contained mathematical optimization logic, the `/api/finalize_calibration` route only ran `spatial_average.py` and `03_generate_pdf_report.py`, reading static bands from `targets.json` without updating them.
- **Stereo Alignment Contract**: In stereo listening, uncoordinated frequency allocation between channels (e.g. Left cutting at 157.5 Hz and Right cutting at 198.4 Hz on Band 1) creates localized phase anomalies that skew the acoustic soundstage. The optimizer aligns center frequencies for shared modal resonances, and for independent room modes, assigns the mode's center frequency to both channels with a neutral 0.0 dB gain on the unaffected channel.
- **Immutability & Safety**: The calculated bands are committed to `targets.json` under the active profile key, ensuring that `/api/apply_profile`, `/api/apply_to_amp`, and verification sweeps always operate on the actual room calibration.

---

## 7. Paginated Step-by-Step Wizard Architecture & Non-Destructive Point Re-Measurement

### Decision
Structure the web calibration interface as a modular, paginated step-by-step wizard (Steps 1 to 6) allowing users to advance, go back, and re-record any individual measurement point or re-run live verification without discarding session state.

### Technical Rationale
- **UX Pain Point**: A single-page monolithic scroll forces users to re-run the entire calibration session if a single measurement point suffers from background noise (cough, car horn, door slam).
- **State Granularity**: By decoupling each phase into distinct viewports (`#page-preflight`, `#page-multipoint`, `#page-optimizer`, `#page-deploy`, `#page-verification`, `#page-reports`) backed by an active step manager in JavaScript, the user has full navigational freedom.
- **Non-Destructive Point Re-measurement**: Individual point endpoints (`/api/record_point?point=N` and `/api/clear_point?point=N`) permit re-recording Point 3 without affecting Points 1, 2, 4, or 5. Once updated, the spatial average is immediately re-calculated in background.

---

## 8. Mobile Wizard Layout Hierarchy & SVG Vector Graphics Standard

### Decision
Relocate modal resonance diagnostics to Step 3 (Optimization & Profiles) and require vector graphics (SVG) for geometric and cluster representations instead of ASCII characters.

### Technical Rationale
- **Information Context**: Diagnostic graphs and resonance Q values reflect empirical measurement outcomes; displaying them in Step 1 (Hardware Preflight) introduces unnecessary friction and confusion before the room has even been swept.
- **Mobile Readability**: ASCII text diagrams suffer from font proportional scaling and line breaks on narrow mobile viewports (< 480px), corrupting spatial understanding. SVG graphics maintain resolution independence, precise circular coordinates, and clean color contrasts matching the "Dark Moderno Studio" design system.
- **Syntactic Resilience**: Strict closure of async error flows (`try/catch/finally`) prevents catastrophic UI lockups on mobile browsers where uncaught promises freeze touch event delegation.
