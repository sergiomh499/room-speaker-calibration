# Interface Contracts: Compact Acoustic Profile Selector

**Feature**: `005-compact-profile-selector`
**Date**: 2026-09-03
**Status**: Complete

---

## 1. Frontend DOM Contract

### Required Element IDs
- `#community-profiles-panel`: The overarching card container.
- `#profiles-container`: The CSS Grid container hosting the 9 compact chips.
- `#profile-inspector-panel`: The shared single inspector card positioned beneath `#profiles-container`.
- `#profile-chip-{key}`: Individual compact chip elements (`key` matching profile key, e.g. `profile-chip-harman_wide_room`).
- `#selected-profile-title`: Section 3 heading updated upon selection.
- `#selected-peq-panel`: Section 3 card containing the 7-band parametric EQ table.

### CSS Class Invariants
- `.compact-profiles-grid`: Must use CSS Grid (`display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 10px;`).
- `.compact-profile-chip`: Must feature cursor: pointer, border-radius >= 6px, and padding <= 10px.
- `.compact-profile-chip.active-target`: Must have distinct active styling (`border-color: #38bdf8; background: rgba(14, 116, 144, 0.20)`).
- `.profile-inspector`: Collapsible panel with subtle background (`rgba(15, 23, 42, 0.6)`) and clear typographic hierarchy.

---

## 2. JavaScript Interface Contracts

### `loadCommunityProfiles(): Promise<void>`
- **Precondition**: Document ready.
- **Action**: Fetches `GET /api/community_profiles`, sorts profiles by `rank`, builds `.compact-profile-chip` DOM elements inside `#profiles-container`, calls `selectProfile(currentSelectedProfile)`.
- **Postcondition**: `#profiles-container` populated with exactly 9 chips.

### `selectProfile(key: string): void`
- **Precondition**: `key` exists in `cachedProfiles`.
- **Behavior**:
  1. Sets `currentSelectedProfile = key`.
  2. Updates `.active-target` class on corresponding `.compact-profile-chip`.
  3. Calls `updateProfileInspector(key)` to refresh `#profile-inspector-panel`.
  4. Calls `renderPEQTable(key)` to update Section 3 table and title.
  5. Updates download links (`/api/download_pdf?profile=${encodeURIComponent(key)}`).
  6. Dispatches `checkVerificationStatusOnLoad(key)`.
- **Constraint**: MUST NOT invoke any network POST commands to the Yamaha AVR.

### `updateProfileInspector(key: string): void`
- **Precondition**: `key` exists in `cachedProfiles`.
- **Behavior**: Populates `#profile-inspector-panel` with:
  - Header: Profile Name + Category + Badge.
  - Literature / Research: `p.community_backing`.
  - Acoustic Description: `p.description`.
  - Pros (`✓` green tag) and Cons (`✗` red tag).

---

## 3. Backend REST Endpoint Contracts (Read-Only)

### `GET /api/community_profiles`
- **Status**: `200 OK`
- **Payload**: JSON dictionary mapping `profile_key` to `CommunityProfile` metadata.
- **Invariants**: Must return all 9 target curves (`harman_wide_room`, `bk_1974`, `dirac_live`, `cinema_blockbuster`, `vocal_clarity`, `x_curve_cinema`, `audiophile_flat`, `ypao_flat`, `through_bypass`).
