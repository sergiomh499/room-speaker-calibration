---
description: "Task list for Multi-Target Validation & Comparative Acoustic Benchmarking"
---

# Tasks: Multi-Target Validation & Comparative Acoustic Benchmarking

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

## Phase 4: User Story 3 (P3) - Server Endpoints & Interactive Dashboard Overlay

**Goal**: Expose target vectors and evaluation metrics via HTTP endpoints and render interactive target overlays on the web dashboard.
**Independent Test**: Query `GET /api/targets` and `POST /api/calibration/multi_target_eval` verifying correct JSON structures and live overlay.

- [x] T009 [P] [US3] Unit test API endpoints for targets and multi-target evaluation in `tests/test_multi_target_endpoints.py`
- [x] T010 [US3] Implement `GET /api/targets` endpoint in `scripts/web_calibration_server.py`
- [x] T011 [US3] Implement `POST /api/calibration/multi_target_eval` endpoint in `scripts/web_calibration_server.py`
- [x] T012 [US3] Add interactive multi-target toggles in web dashboard

## Phase 5: Polish & Regression Verification

- [x] T013 Run full project regression test suite (`python3 -m unittest discover -s tests -p "test_*.py"`)
- [x] T014 Execute quickstart scenarios in `specs/011-multi-target-validation/quickstart.md`
