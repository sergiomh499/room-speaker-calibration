# Data Model & UI State: Compact Acoustic Profile Selector

**Feature**: `005-compact-profile-selector`
**Date**: 2026-09-03
**Status**: Complete

---

## 1. Entities & Schema

### CommunityProfile
Represents an acoustic target curve configuration loaded from `config/targets.json` via `GET /api/community_profiles`:

| Field | Type | Description | Example |
|---|---|---|---|
| `key` | `string` (unique ID) | Canonical profile identifier | `"harman_wide_room"`, `"bk_1974"` |
| `name` | `string` | Human-readable title | `"Harman Target / Floyd Toole"` |
| `rank` | `number` (1-9) | Community & scientific ranking | `1` |
| `badge` | `string` | Visual accolade tag | `"#1 RECOMENDADA"` |
| `category` | `string` | Acoustic category | `"Referencia Acústica Universal"` |
| `community_backing` | `string` | Literature and scientific backing | `"Basado en pruebas de audición a doble ciego..."` |
| `description` | `string` | Acoustic profile description & rationale | `"Compensa la ganancia acústica de sala..."` |
| `pros` | `string[]` | List of documented advantages | `["Respuesta tonal equilibrada", ...]` |
| `cons` | `string[]` | List of documented trade-offs | `["Requiere altavoces con buena dispersión", ...]` |
| `bands` | `Record<string, PEQBand>` | 7-band parametric EQ filter matrix | `{ "Band 1": { "freq": 62.5, "gain_l": 0.0, ... } }` |

---

## 2. Client-Side Runtime UI State

The calibration web dashboard (`web_calibration_server.py`) maintains the following client-side reactive state:

```javascript
// Global State
let cachedProfiles = {};               // Loaded from GET /api/community_profiles
let currentSelectedProfile = 'harman_wide_room'; // Active profile key
let isInspectorCollapsed = false;      // Toggle state for detail drawer
```

### State Transitions

```
[Page Load] 
    ↓ 
loadCommunityProfiles() 
    ↓ fetch /api/community_profiles
Render 9 .compact-profile-chip items in #profiles-container
    ↓ 
selectProfile(defaultProfile = 'harman_wide_room')
    ↓
┌─────────────────────────────────────────────────────────────┐
│ Event: User Clicks Profile Chip (e.g. 'bk_1974')            │
└─────────────────────────────────────────────────────────────┘
    ↓
1. Update active styling:
   - Remove .active-target from all chips
   - Add .active-target to #profile-chip-bk_1974
2. Update Active Profile Inspector (#profile-inspector-panel):
   - Render title, badge, category, research backing, pros & cons
3. Update Section 3 (#selected-peq-panel):
   - Render 7-band table for 'bk_1974'
   - Update #selected-profile-title and badge
4. Update Technical PDF Download URL:
   - #btn-download-pdf href = "/api/download_pdf?profile=bk_1974"
5. Update Verification Status Badges:
   - checkVerificationStatusOnLoad('bk_1974')
```

---

## 3. DOM Component Structure

```html
<!-- Container: Community Profiles Panel -->
<div class="card" id="community-profiles-panel">
  <div class="card-title">
    <span>📚 Selector de Curvas y Perfiles Comunitarios</span>
    <span class="status-badge ok">9 PERFILES DISPONIBLES</span>
  </div>
  <div class="card-desc">
    Selecciona una curva objetivo acústica. Los filtros PEQ calculados se actualizarán inmediatamente:
  </div>

  <!-- 1. Compact Grid (3x3 on desktop) -->
  <div id="profiles-container" class="compact-profiles-grid">
    <!-- 9x .compact-profile-chip generated dynamically -->
    <div class="compact-profile-chip active-target" onclick="selectProfile('harman_wide_room')">
      <div class="chip-header">
        <span class="profile-badge">#1 RECOMENDADA</span>
        <span class="chip-category">Referencia Universal</span>
      </div>
      <div class="chip-title">Harman Target / Floyd Toole</div>
    </div>
    <!-- ... 8 more chips ... -->
  </div>

  <!-- 2. Shared Active Profile Inspector (Collapsible) -->
  <div id="profile-inspector-panel" class="profile-inspector">
    <!-- Rendered dynamically by updateProfileInspector() -->
  </div>
</div>
```
