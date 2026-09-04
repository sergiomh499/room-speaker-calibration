# Quickstart & Validation Guide: Compact Acoustic Profile Selector

**Feature**: `005-compact-profile-selector`
**Date**: 2026-09-03
**Status**: Complete

---

## 1. Prerequisites

- Python 3.10+ with `scripts/web_calibration_server.py` operational.
- Yamaha RX-V673 and Q Acoustics 3020i calibration environment.
- Background server running on port `53317`.

---

## 2. Validation Scenarios

### Scenario 1: Verify Compact Grid Layout & 9 Profile Chips
Run a curl query to ensure all 9 community profiles are delivered by the server:

```bash
curl -s http://127.0.0.1:53317/api/community_profiles | python3 -c "
import sys, json
data = json.load(sys.stdin)
assert len(data) == 9, f'Expected 9 profiles, got {len(data)}'
print('Verified 9 community profiles available for compact selector.')
"
```

### Scenario 2: UI Visual Density & Height Verification
Inspect the web calibration dashboard at `http://127.0.0.1:53317`:

1. Open the browser and navigate to the dashboard.
2. Locate the "📚 Selector de Curvas y Perfiles Comunitarios" section.
3. Verify that all 9 profiles appear in a balanced 3-column grid (on desktop viewports >= 1024px).
4. Verify that total vertical height of the grid is under 300px.
5. Verify that Section 3 (`Filtros PEQ Calculados`) is immediately visible without deep scrolling.

### Scenario 3: Profile Switching & Inspector Panel Responsiveness
1. Click on `#profile-chip-bk_1974` (Brüel & Kjær 1974).
2. Confirm that:
   - The card border immediately lights up with cyan highlight (`#38bdf8`).
   - The shared inspector panel below the grid updates to show B&K 1974 research backing, description, and pros/cons.
   - Section 3 PEQ table updates in < 150ms to display B&K 1974 filters.
   - No command is sent to the physical AVR until the user explicitly presses "Aplicar Perfil al Receptor".
3. Click on `#profile-chip-dirac_live`. Confirm identical instant local update.

### Scenario 4: Viewport Reflow (Mobile & Tablet)
1. Open browser Developer Tools and toggle Device Mode.
2. Set viewport width to `768px` (Tablet): verify grid reflows to 2 columns with zero horizontal scroll.
3. Set viewport width to `375px` (Mobile): verify grid reflows cleanly to 1 column with touch-friendly tap targets.
