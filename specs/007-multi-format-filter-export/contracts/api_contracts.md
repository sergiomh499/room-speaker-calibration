# API & UI Contracts: Multi-Format Filter Export

## REST Endpoints

### 1. `GET /api/export_filters`

Export generated PEQ filters in the requested format.

#### Query Parameters
- `profile` (optional, string): Profile identifier (default: `harman_wide_room`).
- `format` (required, string): One of `rew`, `equalizerapo`, `csv`, `all`.
- `channel` (optional, string): For REW single-channel download (`L` or `R`). Defaults to combined ZIP if omitted.

#### Responses

- **200 OK (`format=csv`)**:
  - `Content-Type`: `text/csv; charset=utf-8`
  - `Content-Disposition`: `attachment; filename="peq_filters_{profile}.csv"`
  - Body: Raw CSV text.

- **200 OK (`format=equalizerapo`)**:
  - `Content-Type`: `text/plain; charset=utf-8`
  - `Content-Disposition`: `attachment; filename="equalizer_apo_{profile}.txt"`
  - Body: Raw EqualizerAPO config.

- **200 OK (`format=rew` or `format=all`)**:
  - `Content-Type`: `application/zip`
  - `Content-Disposition`: `attachment; filename="filters_{profile}_{format}.zip"`
  - Body: Binary ZIP payload.

- **400 Bad Request**:
  - `Content-Type`: `application/json`
  - Body: `{"ok": false, "msg": "Descripción del error"}`

---

## UI Contract: Web Calibration Dashboard

### `#export-filters-card` Markup
```html
<div class="card" id="export-filters-card" style="border-color: #38bdf8; background: rgba(56, 189, 248, 0.05); margin-bottom: 14px;">
  <div class="card-title" style="color: #38bdf8; font-size: 0.85rem; margin-bottom: 4px;">
    <span>Exportar Filtros PEQ (Multi-Formato)</span>
    <span class="status-badge ok" id="export-status-badge">DISPONIBLE</span>
  </div>
  <div style="font-size: 0.72rem; color: #94a3b8; margin-bottom: 8px;">
    Descarga la solución paramétrica de 7 bandas optimizada para REW, EqualizerAPO o análisis en CSV.
  </div>
  <div style="display: flex; gap: 8px; flex-wrap: wrap;">
    <a id="btn-export-rew" class="btn-profile" href="/api/export_filters?format=rew&profile=harman_wide_room" style="text-decoration:none; background:#0284c7;">Descargar REW (.req)</a>
    <a id="btn-export-apo" class="btn-profile" href="/api/export_filters?format=equalizerapo&profile=harman_wide_room" style="text-decoration:none; background:#0d9488;">Descargar EqualizerAPO (.txt)</a>
    <a id="btn-export-csv" class="btn-profile" href="/api/export_filters?format=csv&profile=harman_wide_room" style="text-decoration:none; background:#6366f1;">Descargar CSV</a>
    <a id="btn-export-all" class="btn-profile" href="/api/export_filters?format=all&profile=harman_wide_room" style="text-decoration:none; background:#475569;">Descargar Todo (.zip)</a>
  </div>
</div>
```
