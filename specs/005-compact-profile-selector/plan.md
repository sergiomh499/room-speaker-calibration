# Implementation Plan: Compact Acoustic Profile Selector

**Branch**: `005-compact-profile-selector` | **Date**: 2026-09-03 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/005-compact-profile-selector/spec.md`

---

## Summary

The community profile selector in the web calibration dashboard currently renders 9 large vertical cards containing extensive paragraphs of scientific rationale, advantages, and drawbacks, consuming over 1,400px of vertical height. This implementation redesigns the selector into a high-density, responsive 3-column CSS Grid of compact profile chips (~240px tall on desktop), paired with a single shared active profile inspector panel directly below. Clicking any card instantly updates the local preview (Section 3 PEQ table and inspector) in < 150ms while strictly leaving AVR hardware deployment to an explicit user confirmation button.

---

## Technical Context

**Language/Version**: Python 3.14 (Server runtime), Vanilla ES6+ JavaScript, HTML5, CSS3  
**Primary Dependencies**: Standard Library (`http.server`, `urllib`, `json`), native browser CSS Grid / Flexbox  
**Storage**: File-backed (`config/targets.json`, `data/*.npz`)  
**Testing**: Python `unittest` (`tests/test_report_graphs_sync.py`, `tests/test_peq_optimizer_coordinated.py`), browser-driven DOM validation  
**Target Platform**: Linux (Arch / CachyOS), Web browser clients (Desktop, Tablet, Mobile)  
**Project Type**: Web Application / Embedded Calibration Dashboard  
**Performance Goals**: < 150ms client-side profile switching; < 350px total vertical height footprint (SC-001)  
**Constraints**: Constitution Principles I–V; zero horizontal scrolling across 360px–1920px viewports; 100% backward-compatibility with existing `/api/*` endpoints.  
**Scale/Scope**: 1 UI component refactor, 9 community acoustic target curves.

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Principle I (Hardware-First — No Simulated State)**: PASS. All AVR state queries continue to use real network YNC XML endpoints.
- **Principle II (Non-Destructive Telemetry)**: PASS. The compact profile selector is entirely client-side UI and read-only GET endpoints (`/api/community_profiles`). It issues no background PUT or state-forcing commands.
- **Principle III (Profile-Scoped Verification)**: PASS. Selecting any profile chip updates `currentSelectedProfile` and correctly scopes verification calls to that profile key.
- **Principle IV (Measurement Immutability)**: PASS. No raw `.npz` measurement files are overwritten or modified.
- **Principle V (Minimum Viable Command Surface)**: PASS. Selecting a profile performs local preview only; hardware writes remain isolated to explicit deployment actions.

---

## Project Structure

### Documentation (this feature)

```text
specs/005-compact-profile-selector/
├── plan.md              # This implementation plan
├── research.md          # Layout, inspector, and preview decisions
├── data-model.md        # Entities, DOM hierarchy, and reactive UI state
├── quickstart.md        # Verification and testing guide
├── contracts/
│   └── ui_contracts.md  # DOM IDs, classes, and JS function interfaces
└── checklists/
    └── requirements.md  # Spec quality checklist (16/16 passed)
```

### Source Code (repository root)

```text
scripts/
└── web_calibration_server.py   # Primary target: HTML, CSS, and JS profile selector refactor
config/
└── targets.json                # Authoritative 9 community acoustic profile configurations
tests/
└── test_report_graphs_sync.py  # Validation and regression tests
```

---

## Phases & Deliverables

1. **Phase 0: Research & Architecture (Complete)**
   - Researched CSS Grid density, shared inspector architecture, and preview isolation. Output: `research.md`.
2. **Phase 1: Design & Contracts (Complete)**
   - Modeled UI entities and reactive state transitions in `data-model.md`.
   - Defined DOM, JS, and CSS contracts in `contracts/ui_contracts.md`.
   - Outlined validation scenarios in `quickstart.md`.
3. **Phase 2: Implementation (Pending /speckit.tasks & /speckit.implement)**
   - Refactor CSS rules in `scripts/web_calibration_server.py` (`.compact-profiles-grid`, `.compact-profile-chip`, `.profile-inspector`).
   - Refactor `loadCommunityProfiles()` to generate compact chips.
   - Implement `updateProfileInspector(key)` to populate the shared inspector panel.
   - Refactor `selectProfile(key)` for instant local preview and active chip highlighting.
   - Restart calibration server and perform smoke tests across viewports.
