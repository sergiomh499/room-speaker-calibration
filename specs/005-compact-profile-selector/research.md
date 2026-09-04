# Research & Technical Decisions: Compact Acoustic Profile Selector

**Feature**: `005-compact-profile-selector`
**Date**: 2026-09-03
**Status**: Complete

---

## 1. Profile Grid Layout & Density Optimization

### Context
The previous community profile selector rendered 9 vertically stacked `.profile-card` divs, each containing 6 separate text blocks (badge, category, title, community research backing, full description, pros tags, cons tags, and a 42px button). This consumed over 1,400px of vertical space, pushing the calculated PEQ table (Section 3) and verification charts (Section 4) far off-screen.

### Decision
Implement a responsive CSS Grid container (`#profiles-container`) configured with:
```css
display: grid;
grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
gap: 10px;
margin-top: 10px;
```
Each compact profile card (`.compact-profile-chip`):
- Displays: Rank badge + Category (top row), Profile Title (middle row), and a subtle 1-line acoustic summary / signature tag.
- Padding: 8px 12px (reduced from 16px).
- Min-height: ~72px (reduced from ~260px).
- Cursor: pointer, with active state highlighting (`border-color: #38bdf8; background: rgba(14, 116, 144, 0.18)`).
- Eliminates the individual "Seleccionar" button; clicking anywhere on the card directly selects the profile.

### Alternatives Considered
- **Horizontal scrollable carousel**: Rejected because items on the right are hidden off-screen, reducing discoverability and requiring extra lateral navigation.
- **HTML `<select>` dropdown menu**: Rejected because it completely obscures acoustic categories, badges, and rankings until opened, degrading visual feedback.
- **Collapsible accordion per card**: Rejected because expanding cards causes layout shifting and reintroduces vertical clutter.

---

## 2. Shared Active Profile Inspector

### Context
Users still need access to the rich acoustic context (Dr. Floyd Toole AES research, Harman curve targets, Sean Olive papers, room-mode compatibility, pros, and cons) without cluttering the 9-item selection matrix.

### Decision
Introduce a single shared inspector card (`#profile-inspector-panel`) positioned immediately below the compact grid:
- Header: Active profile badge, full title, category, and an optional collapse toggle.
- Body:
  - Respaldo Científico / Comunitario (formatted with `#38bdf8` accent).
  - Descripción Acústica y Recomendación de Aplicación.
  - Side-by-side or dual-column Pros (`#86efac`) and Cons (`#fca5a5`).
- Dynamically re-rendered by JavaScript whenever `selectProfile(key)` is invoked.
- Default state: Open with concise padding, collapsible via click.

### Alternatives Considered
- **Modal dialog**: Rejected because modals occlude the underlying PEQ table and require dismiss clicks, breaking workflow continuity.
- **Hover tooltips**: Rejected because tooltips do not work reliably on mobile touchscreens and vanish upon cursor movement.

---

## 3. Local Preview Isolation vs Hardware Deployment

### Context
Clarification session 2026-09-03 ratified that clicking a profile card MUST preview the filters locally without automatically issuing PUT/POST commands to the physical Yamaha RX-V673.

### Decision
- `selectProfile(key)`:
  1. Updates `currentSelectedProfile = key`.
  2. Updates UI active border on the clicked card.
  3. Updates `#profile-inspector-panel` with the selected profile's metadata.
  4. Populates Section 3 (`#selected-peq-panel`) with the calculated 7-band filter table.
  5. Updates download link for the technical PDF report.
  6. Checks verification status for that profile key via `/api/verification_status?profile=${key}`.
- Writing to the amplifier hardware remains strictly bound to `#btn-apply-selected-peq` (which invokes `/api/apply_profile?profile=${key}`).

### Compliance with Project Constitution
- **Principle II (Non-Destructive Telemetry)**: Read/preview operations have zero side effects on AVR input or DSP state.
- **Principle III (Profile-Scoped Verification)**: Verification status and PDF download URLs are strictly scoped to the active profile key.
- **Principle V (Minimum Viable Command Surface)**: Hardware writes occur only via atomic, explicit user invocation.

---

## 4. Responsive Viewport Breakpoints

### Specifications
- **Desktop (>= 1024px)**: 3 columns $\times$ 3 rows. Total grid height: ~240px. Total section height with inspector: ~360px.
- **Tablet (640px - 1023px)**: 2 columns $\times$ 5 rows. Total grid height: ~360px.
- **Mobile (< 640px)**: 1 column $\times$ 9 rows or 2 columns with reduced font sizes (0.75rem). Minimum touch target height: 44px. Zero horizontal overflow.
