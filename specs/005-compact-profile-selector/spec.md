# Feature Specification: Compact Acoustic Profile Selector

**Feature Branch**: `005-compact-profile-selector`

**Created**: 2026-09-03

**Status**: Draft

**Input**: User description: "haz mas compacta la parte de seleccion de perfil"

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Compact Profile Grid and Direct Selection (Priority: P1) 🎯 MVP

As an audio calibrator using the web calibration dashboard, I want the community acoustic profile selection area to be visually compact and organized in a clean responsive grid or list, so that I can see all available target curves at a glance without scrolling through multiple screen heights.

**Why this priority**: The current interface renders 9 large vertical cards with full paragraphs and bullet lists, displacing calculated PEQ filters and verification metrics off-screen. A compact selector delivers immediate usability and spatial efficiency.

**Independent Test**: Load the calibration dashboard in a standard desktop and mobile browser viewport; verify that all 9 profiles fit into a compact grid layout occupying under 350 pixels of vertical height, and clicking any profile immediately activates it.

**Acceptance Scenarios**:

1. **Given** the user navigates to the community profiles section, **When** the page loads, **Then** the profiles are displayed in a compact multi-column grid (or tight badge cards) showing rank, badge, short name, and acoustic category without redundant whitespace.
2. **Given** multiple profiles in the compact grid, **When** the user clicks any profile card or chip, **Then** that profile is visibly highlighted as active and the calculated PEQ filter table immediately updates for that profile.
3. **Given** the compact layout, **When** comparing the vertical screen footprint to the previous full-card design, **Then** the total vertical height consumed by the profile selection section is reduced by at least 65%.

---

### User Story 2 - Expandable Detail & Acoustic Backing on Demand (Priority: P2)

As a technical listener or audio engineer, I want to access the detailed acoustic backing, description, advantages, and drawbacks for any profile on demand, so that I can make informed decisions without cluttering the main calibration interface.

**Why this priority**: Detailed acoustic justification (Dr. Floyd Toole research, Harman target, Sean Olive AES papers, B&K 1974 curve) provides vital context, but should not overwhelm the primary workflow. Collapsible/modal or active-card detail inspection preserves information density without visual bloat.

**Independent Test**: Select a profile and toggle the details view; verify that the description, community backing, pros, and cons become clearly visible, and collapsing it restores the compact view.

**Acceptance Scenarios**:

1. **Given** an active profile in the compact view, **When** the user views the active selection or clicks a "Detalles" toggle, **Then** a concise detail card appears showing the research backing, pros, and cons for only the active profile.
2. **Given** the detail panel is expanded, **When** the user selects a different profile, **Then** the detail panel updates immediately to display the newly selected profile's acoustic characteristics.
3. **Given** the user desires maximum compactness, **When** the detail panel is collapsed or minimized, **Then** the dashboard maintains minimal vertical footprint.

---

### User Story 3 - Responsive Viewport Adaptation (Priority: P3)

As a user calibrating from either a desktop monitor, tablet, or smartphone near the listening sweet spot, I want the compact profile selector to seamlessly adapt to my screen width.

**Why this priority**: Room calibrations often involve holding a laptop, tablet, or phone while seated at the primary listening position. Responsive ergonomics ensure effortless profile switching on any display.

**Independent Test**: Resize the browser viewport across mobile (360px), tablet (768px), and desktop (1200px) widths; verify that the profile selector reflows cleanly without horizontal overflow or clipped text.

**Acceptance Scenarios**:

1. **Given** a wide desktop screen (>= 1024px), **When** rendering the profile selector, **Then** profiles arrange in a balanced 3-column or 4-column compact grid.
2. **Given** a narrow mobile viewport (< 600px), **When** rendering the profile selector, **Then** profiles adapt into a single or dual-column touch-friendly compact list with clear tap targets (minimum 40px height).
3. **Given** any viewport size, **When** selecting a profile, **Then** no horizontal scrolling is introduced to the document.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The community profiles panel MUST render all available target curves in a compact visual layout (such as a 3-column CSS grid or compact selector chips) instead of full-page vertical cards.
- **FR-002**: Each compact profile item MUST prominently display the profile rank/badge (e.g., `#1 RECOMENDADA`, `#2 SEGUNDO PUESTO`), the profile name, and the category tag.
- **FR-003**: Clicking anywhere on a profile item MUST directly select that profile, trigger active highlighting, and reload Section 3 (`Filtros PEQ Calculados`) with that profile's optimized parameters.
- **FR-004**: The compact selector MUST clearly distinguish the currently active profile using high-contrast border and background styling (e.g., cyan `#38bdf8` accent).
- **FR-005**: Detailed information (community backing, description, advantages, drawbacks) MUST be housed in an on-demand collapsible area or dedicated single-card inspector rather than repeated 9 times.
- **FR-006**: Total vertical height consumed by the unexpanded profile selection section MUST NOT exceed 380 pixels on standard desktop viewports (1080p).
- **FR-007**: The compact profile component MUST maintain 100% compatibility with existing backend endpoints (`/api/community_profiles`, `/api/apply_profile`, `/api/verification_status`, and `/api/verification_comparison`).
- **FR-008**: Profile switching MUST preserve the profile-scoping contract mandated by Principle III of the project constitution.

---

### Key Entities

- **Community Profile**: Represents an acoustic target curve (id, name, rank, badge, category, community backing, description, pros, cons, target curve settings).
- **Compact Profile Card / Chip**: Lightweight UI component rendering the essential identification metadata for a single profile.
- **Active Profile Inspector**: Collapsible detail panel presenting deep acoustic context for the selected profile.

---

## Success Criteria *(mandatory)*

- **SC-001**: The profile selection interface vertical height is reduced by at least 65% compared to the prior layout (under 350px vs > 1400px previously).
- **SC-002**: 100% of all 9 community profiles remain accessible and selectable with a single click or tap.
- **SC-003**: Selecting any profile updates the calculated PEQ table in Section 3 in under 150 milliseconds without reloading the page.
- **SC-004**: Full responsiveness verified across viewports from 360px to 1920px width with zero horizontal overflow.
- **SC-005**: Deep technical acoustic rationale and pros/cons remain accessible within 1 click via an on-demand detail drawer or toggle.

---

## Assumptions & Edge Cases

- **Assumptions**:
  - The 9 existing profiles in `config/targets.json` (`harman_wide_room`, `bk_1974`, `dirac_live`, `cinema_blockbuster`, `vocal_clarity`, `x_curve_cinema`, `audiophile_flat`, `ypao_flat`, `through_bypass`) remain the authoritative profiles.
  - Users prioritize immediate access to PEQ filter deployment and verification over reading lengthy static descriptions repeatedly.
- **Edge Cases**:
  - Profile names of varying length (e.g. `Through / Pure Direct (Sin Ecualización / Sala al Desnudo)` vs `B&K 1974`): layout must wrap text gracefully without breaking card alignment.
  - Rapid profile clicking: UI must update active state immediately and debounce/queue filter recalculation cleanly.
