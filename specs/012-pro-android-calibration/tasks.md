# Tasks: Professional Standalone Android Acoustic Calibration Suite

**Input**: Design documents from `/specs/012-pro-android-calibration/` (`spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`)

**Prerequisites**: `plan.md` (required), `spec.md` (required for user stories), `research.md`, `data-model.md`, `contracts/`

**Tests**: DSP mathematical unit tests and zero-synthetic verification audits are included per constitutional requirements.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

---

## Phase 1: Setup (Shared Infrastructure & Bloat Removal)

**Purpose**: Streamline the codebase into a dedicated mobile calibration suite by purging auxiliary streaming bloat and establishing the 4-tab mobile navigation.

- [X] T001 Remove auxiliary internet radio streaming components, scrapers, and external music players in `frontend/src/components/music/MusicStreamingHub.tsx`
- [X] T002 Clean up unused radio and external streaming routes and methods in `frontend/src/services/musicCaster.ts`
- [X] T003 [P] Configure 4-view mobile primary navigation tabs (Calibrate, AVR Remote, Acoustic Curves, History & Settings) in `frontend/src/components/layout/BottomNav.tsx`
- [X] T004 [P] Update central navigation state router and view switcher in `frontend/src/App.tsx`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core mathematical and hardware communication infrastructure that MUST be complete before ANY user story can execute.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T005 Implement pre-computed Farina inverse sweep coefficients and 48 kHz reference signal generators in `frontend/src/services/sweepGenerator.ts`
- [X] T006 Implement high-performance Cooley-Tukey Real-FFT algorithm (65,536-point) and TypedArray convolution in `frontend/src/services/fftEngine.ts`
- [X] T007 [P] Implement discrete Yamaha parameter quantizers (`snapFrequency`, `snapQ`, `snapGain`, `formatFreqYamahaXml`) and RBJ peaking biquad response calculators in `frontend/src/services/dspEngine.ts`
- [X] T008 [P] Implement direct YNC XML HTTP communication over `CapacitorHttp` with 60ms volume debounce and error handling in `frontend/src/services/yamahaDirect.ts`
- [X] T009 Implement pre-flight receiver NVRAM snapshot capture and one-tap atomic rollback driver in `frontend/src/services/avrRollback.ts`
- [X] T010 [P] Define centralized domain TypeScript interfaces matching data-model entities in `frontend/src/types/index.ts`

**Checkpoint**: Foundation ready — user story implementation can now begin.

---

## Phase 3: User Story 1 - Standalone Mobile Acoustic Sweep & Real Response Analysis (Priority: P1) 🎯 MVP

**Goal**: Coordinate excitation sweep playback, record uncompressed 48 kHz audio via native microphone, execute on-device Farina deconvolution, and compute real physical frequency response and acoustic metrics without any server.

**Independent Test**: Connect phone to local receiver, trigger an acoustic sweep, and confirm that on-device deconvolution calculates authentic impulse response arrival time, distance in meters, peak SPL, SNR, and genuine frequency curve with zero synthetic or randomized data.

### Tests for User Story 1

- [X] T011 [P] [US1] Unit test for on-device Farina deconvolution, peak arrival detection, and FFT magnitude extraction in `frontend/src/services/__tests__/dspEngine.test.ts`
- [X] T012 [P] [US1] Python ground-truth parity test verifying TypeScript FFT deconvolution matches scipy.signal reference in `tests/test_fft_parity.py`

### Implementation for User Story 1

- [X] T013 [P] [US1] Implement dual-mode excitation playback (Physical AUX line-out via WebAudio and wireless UPnP/DLNA casting via `CapacitorHttp`) in `frontend/src/services/audioPlayback.ts`
- [X] T014 [US1] Implement native audio capture coordinator interfacing with `RawAudioRecorderPlugin` (48 kHz 16-bit PCM) in `frontend/src/services/nativeAudio.ts`
- [X] T015 [US1] Implement acoustic signal validation gates (clipping rejection at -0.5 dBFS, SNR check at 14 dB) and causal windowing in `frontend/src/services/dspEngine.ts`
- [X] T016 [US1] Implement real 1/12-octave psychoacoustic smoothing algorithm and transducer `.cal` file offset compensation in `frontend/src/services/dspEngine.ts`
- [X] T017 [US1] Implement physical acoustic metric calculators (arrival delay in ms, distance in meters, peak SPL in dB, SNR in dB) in `frontend/src/services/dspEngine.ts`
- [X] T018 [US1] Connect sweep measurement workflow and live VUMeter feedback in `frontend/src/views/CalibrateView.tsx`

**Checkpoint**: At this point, User Story 1 is fully functional as a standalone acoustic measurement MVP.

---

## Phase 4: User Story 2 - Empirical Before-and-After Calibration Comparison (Priority: P2)

**Goal**: Execute a closed-loop verification sweep with manual PEQ engaged, render an authentic 4-curve visual overlay (Baseline, Target, PEQ filter response, Verification), and compute modal peak attenuation.

**Independent Test**: Run a baseline sweep, deploy a filter set, trigger a verification sweep in the same position, and verify that the interactive chart renders all 4 genuine curves on the same decibel axis with quantified room mode reduction.

### Implementation for User Story 2

- [X] T019 [P] [US2] Implement closed-loop verification sweep execution pipeline (forcing PEQ mode to Manual) in `frontend/src/services/verificationEngine.ts`
- [X] T020 [US2] Implement room mode identification and quantitative attenuation calculator (delta dB reduction below 500 Hz) in `frontend/src/services/dspEngine.ts`
- [X] T021 [P] [US2] Implement interactive high-resolution multi-curve comparison graph (Pre-calibration, Target, Biquad filter transfer, Post-calibration) with interactive curve toggles in `frontend/src/components/charts/FrequencyGraph.tsx`
- [X] T022 [US2] Implement dedicated "Acoustic Curves" view displaying the before-and-after verification overlay and room resonance table in `frontend/src/views/AcousticCurvesView.tsx`

**Checkpoint**: User Stories 1 and 2 deliver end-to-end empirical verification of acoustic calibration.

---

## Phase 5: User Story 3 - Guided Professional Calibration Wizard & Zero-Touch Deployment (Priority: P3)

**Goal**: Deliver a streamlined 5-step touch-optimized calibration wizard handling receiver discovery, speaker topology (2.0/2.1), spatial cluster averaging, discrete Yamaha PEQ filter optimization, and atomic NVRAM programming.

**Independent Test**: Complete a full 2.1 calibration from step 1 to step 5, verify that 7 discrete PEQ bands per channel are programmed into the receiver NVRAM, and confirm that cancelling restores original settings.

### Implementation for User Story 3

- [X] T023 [P] [US3] Implement automated network receiver discovery via SSDP and subnet probe in `frontend/src/services/avrDiscovery.ts`
- [X] T024 [US3] Implement microphone profile selector with bundled reference profiles (Pixel 9 Pro UNPROCESSED) and custom 90-degree `.cal` file importer in `frontend/src/views/SettingsView.tsx`
- [X] T025 [US3] Implement complex vector spatial averaging across 1 to 5 measurement positions to eliminate positional comb filtering in `frontend/src/services/dspEngine.ts`
- [X] T026 [US3] Implement subwoofer crossover integration (phase alignment delay and relative trim calculation) in `frontend/src/services/crossoverAligner.ts`
- [X] T027 [US3] Implement 7-band discrete Yamaha PEQ optimizer enforcing asymmetric gain limits (+3 dB max boost, 0 dB boost above 500 Hz, -12 dB cut) in `frontend/src/services/dspEngine.ts`
- [X] T028 [US3] Implement atomic YNC XML deployment pushing discrete Pattern_1 PEQ matrix, speaker distances, and channel trims to receiver in `frontend/src/services/yamahaDirect.ts`
- [X] T029 [US3] Wire step-by-step wizard navigation, validation gates, and rollback prompt into `frontend/src/views/CalibrateView.tsx`

**Checkpoint**: User Stories 1, 2, and 3 provide a complete, autonomous calibration flow.

---

## Phase 6: User Story 5 - Real-Time Receiver Hardware Control & Acoustic Monitoring (Priority: P3)

**Goal**: Provide a dedicated "AVR Remote & Diagnostics" tab for real-time receiver operation: 0.5 dB rotary volume dial, power toggle, input selector, A/B PEQ mode toggle (Manual vs. Through vs. YPAO), Straight/Pure Direct, and channel trims.

**Independent Test**: Open the AVR Remote tab, rotate the volume dial to verify 0.5 dB receiver updates, and toggle PEQ mode to confirm instant acoustic A/B comparison without interrupting playback.

### Implementation for User Story 5

- [X] T030 [P] [US5] Implement 0.5 dB precision rotary volume dial with haptic feedback and 60ms debounce in `frontend/src/components/audio/HapticVolumeDial.tsx`
- [X] T031 [US5] Implement live status polling driver for power, input, volume, PEQ mode, and sound program in `frontend/src/services/avrControls.ts`
- [X] T032 [US5] Implement instant A/B PEQ mode toggle (`Manual` vs. `Through` vs. `YPAO`) and Straight/Pure Direct switches in `frontend/src/services/yamahaDirect.ts`
- [X] T033 [US5] Implement dedicated "AVR Remote & Diagnostics" view in `frontend/src/views/AvrRemoteView.tsx`

**Checkpoint**: The receiver can be fully controlled and subjectively audited A/B from the mobile app.

---

## Phase 7: User Story 4 - Historical Calibration Management & Multi-Profile Auditing (Priority: P4)

**Goal**: Store calibration sessions and impulse responses locally, allow side-by-side historical comparison, enable 1-tap re-deployment of saved filter sets, and export complete self-contained ZIP/PDF calibration archives.

**Independent Test**: Save two calibration sessions, compare them side-by-side in the History view, re-deploy a historical profile to the receiver, and export a complete session ZIP archive to device storage.

### Implementation for User Story 4

- [X] T034 [P] [US4] Implement structured hybrid local storage (IndexedDB for session metadata and curves + app-private file storage for impulse responses) in `frontend/src/services/storageService.ts`
- [X] T035 [US4] Implement self-contained ZIP archive exporter (session JSON, CSV curves, YNC XML payload, and summary PDF) in `frontend/src/services/exportService.ts`
- [X] T036 [US4] Implement historical session list, profile filter, side-by-side curve comparison, and 1-tap re-deployment in `frontend/src/views/HistoryView.tsx`

**Checkpoint**: All 5 user stories are implemented and independently verifiable.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Zero-hardcode and zero-synthetic mathematical audit, production compilation, native Android packaging, and end-to-end verification.

- [X] T037 Perform zero-synthetic audit verifying zero `Math.random()` or hardcoded frequency offsets remain in `frontend/src/services/dspEngine.ts` and `frontend/src/services/api.ts`
- [X] T038 [P] Run offline mathematical DSP regression and biquad transfer function tests via `pytest tests/test_peq_biquad_math.py tests/test_peq_optimizer_ground_truth.py tests/test_audit_zero_hardcode.py`
- [X] T039 Execute production TypeScript bundle compilation and linting via `cd frontend && bun run build`
- [X] T040 Synchronize compiled production web assets to the native Android container via `cd frontend && bun x cap sync android`
- [X] T041 Run quickstart end-to-end verification scenario against local AVR per `specs/012-pro-android-calibration/quickstart.md`

---

## Dependencies & Story Execution Order

```mermaid
graph TD
    Phase1[Phase 1: Setup & Bloat Removal] --> Phase2[Phase 2: Foundational DSP & YNC Engine]
    Phase2 --> US1[Phase 3: US1 - Real Sweep & Deconvolution (P1 MVP)]
    US1 --> US2[Phase 4: US2 - Before/After Verification Overlay (P2)]
    US1 --> US3[Phase 5: US3 - 5-Step Calibration Wizard (P3)]
    Phase2 --> US5[Phase 6: US5 - Dedicated AVR Remote Tab (P3)]
    US2 --> US4[Phase 7: US4 - History & ZIP Archive Export (P4)]
    US3 --> US4
    US4 --> Phase8[Phase 8: Polish & Verification Audit]
    US5 --> Phase8
```

### Parallel Execution Opportunities
- **Phase 1**: T003 (BottomNav) and T004 (App router) can be implemented in parallel.
- **Phase 2**: T007 (PEQ quantizers), T008 (YNC XML driver), and T010 (TypeScript types) can be implemented in parallel.
- **Phase 3**: T011 (Unit tests) and T013 (Audio playback) can run in parallel.
- **Phase 5 & 6**: User Story 5 (AVR Remote Tab) can be developed in parallel with User Story 3 (Calibration Wizard) as both rely only on Foundational Phase 2.

---

## Implementation Strategy: MVP First

1. **MVP Increment (Phases 1, 2, 3)**:
   - Delivers real, on-device acoustic sweep recording, deconvolution, and genuine curve extraction on Android with zero server dependency and zero synthetic math.
2. **Verification Increment (Phase 4)**:
   - Delivers empirical closed-loop before-and-after comparison curves proving acoustic impact.
3. **Hardware Automation Increment (Phases 5 & 6)**:
   - Delivers the guided 5-step wizard, discrete Yamaha NVRAM deployment, safety rollback, and dedicated AVR remote control.
4. **Complete Suite Increment (Phases 7 & 8)**:
   - Delivers session archiving, ZIP/PDF export, zero-hardcode certification, and production APK synchronization.
