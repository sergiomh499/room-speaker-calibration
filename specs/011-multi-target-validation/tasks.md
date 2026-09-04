---
description: "Task list for Multi-Target Validation, 1-to-1 Professional Calibration & Dark Studio Pro UX"
---

# Tasks: Multi-Target Validation & Dark Studio Pro Calibration Dashboard

**Input**: Design documents from `specs/011-multi-target-validation/`
**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/api_contracts.md`

## Phase 1: Setup & Target Unification (Foundational)

- [x] T001 Verify baseline measurement sweeps and target profile configurations in `config/targets.json`
- [x] T002 Verify 2.0 bookshelf roll-off and subsonic protection across target curves in `scripts/peq_optimizer.py`

## Phase 2: User Story 1 (P1) - Target Curve Correctness & Mathematical Unification

**Goal**: Unify target generation between optimization and verification, ensuring 100% mathematical consistency without false bass penalties.
**Independent Test**: Run `python3 -m unittest tests/test_target_curves_audit.py` confirming identical target curves across modules.

- [x] T003 [P] [US1] Unit test target consistency and bookshelf roll-off in `tests/test_target_curves_audit.py`
- [x] T004 [US1] Refactor `build_profile_target_curve` in `scripts/verify_calibration.py` to import `generate_bookshelf_target_curve` from `scripts/peq_optimizer.py`
- [x] T005 [US1] Update `scripts/web_calibration_server.py` to use `generate_bookshelf_target_curve` for active target generation

## Phase 3: User Story 2 (P2) - Multi-Target Benchmarking Engine

**Goal**: Calculate cross-comparison alignment metrics (RMS error, maximum deviation, S-TIER score) across all presets and targets.
**Independent Test**: Run `tests/test_multi_target_eval.py` asserting accurate evaluation of measured curves against all 5 target categories.

- [x] T006 [P] [US2] Unit test multi-target alignment scoring engine in `tests/test_multi_target_eval.py`
- [x] T007 [US2] Implement `evaluate_multi_target_alignment` in `scripts/verify_calibration.py`
- [x] T008 [US2] Generate cross-target summary matrix in reports (`reports/Informe_Calibracion_Acustica_*.pdf`)

## Phase 4: User Story 3 (P3) - Server Endpoints & Target Overlay

**Goal**: Expose target vectors and evaluation metrics via HTTP endpoints and render interactive target overlays on the web dashboard.
**Independent Test**: Query `GET /api/targets` and `POST /api/calibration/multi_target_eval` verifying correct JSON structures and live overlay.

- [x] T009 [P] [US3] Unit test API endpoints for targets and multi-target evaluation in `tests/test_multi_target_endpoints.py`
- [x] T010 [US3] Implement `GET /api/targets` endpoint in `scripts/web_calibration_server.py`
- [x] T011 [US3] Implement `POST /api/calibration/multi_target_eval` endpoint in `scripts/web_calibration_server.py`

## Phase 5: User Story 4 (P1) - Professional 1-to-1 Calibration & Hardware Preset Preloader

**Goal**: Enable a direct 1-to-1 workflow per preset (deploy PEQ -> sweep verification -> single-preset plot with 3 engineering metrics), plus instant preloading of saved presets to the Yamaha RX-V673.
**Independent Test**: Execute `POST /api/calibration/preload_preset` and `GET /api/sessions/history` verifying live hardware deployment and historical sessions.

- [ ] T012 [P] [US4] Unit test preset pre-loading and historical session querying in `tests/test_preset_preloader.py`
- [ ] T013 [US4] Implement `POST /api/calibration/preload_preset` in `scripts/web_calibration_server.py` to send 7-band PEQ parameters directly to Yamaha AVR
- [ ] T014 [US4] Implement `GET /api/sessions/history` in `scripts/web_calibration_server.py` to index and serve historical sessions from `data/sessions/`
- [ ] T015 [US4] Refactor dashboard graph telemetry to emphasize the 3 key engineering metrics (Modal Peak Reduction, Stereo Symmetry |L-R|, Target Adherence)

## Phase 6: User Story 5 (P1) - Dark Studio Pro Responsive UX Redesign

**Goal**: Redesign the entire web dashboard to a sleek Dark Studio Pro aesthetic (Dirac Live / Logic Pro inspired) with large ergonomic touch targets (>=48px) for mobile/desktop sweet spot operation.
**Independent Test**: Verify layout and touch controls in mobile (360px viewport) and desktop browsers, confirming zero horizontal overflow and GPU-accelerated micro-animations.

- [ ] T016 [US5] Modernize HTML/CSS design tokens in `scripts/web_calibration_server.py` (`#0f172a` deep slate, studio emerald `#10b981`, amber alerts `#f59e0b`, crisp typography)
- [ ] T017 [US5] Enlarge all interactive action buttons to minimum 48px height with tactile `:active` scale and glowing focus states
- [ ] T018 [US5] Implement responsive mobile grid/flex layout with collapsible telemetry drawers and full-width charts on smartphone viewports
- [ ] T019 [US5] Integrate interactive preset preloader UI component and historical session browser in the dashboard

## Phase 7: Polish & Full Regression Verification

- [ ] T020 Run full regression test suite (`python3 -m unittest discover -s tests -p "test_*.py"`)
- [ ] T021 Execute quickstart verification scenarios in `specs/011-multi-target-validation/quickstart.md`
- [ ] T022 Validate end-to-end responsive UI across simulated mobile (360px) and desktop viewports
