# Phase 1 Interface Contracts: REST API and CLI Invocations

**Feature**: `003-fix-report-graphs`
**Date**: 2026-09-03
**Status**: Completed

## 1. HTTP REST Endpoints

### 1.1 `GET /api/download_pdf`
Downloads the official engineering PDF report for the specified or currently active acoustic profile.

- **Query Parameters**:
  - `profile` (optional, string): Target profile key (default: `harman_wide_room` or active session profile).
- **HTTP Response Headers**:
  ```http
  HTTP/1.1 200 OK
  Content-Type: application/pdf
  Content-Disposition: attachment; filename="Informe_Calibracion_Acustica_Yamaha.pdf"
  Cache-Control: no-cache, no-store, must-revalidate, max-age=0
  Pragma: no-cache
  Expires: 0
  ```
- **Error Response (404/500)**:
  ```json
  {
    "ok": false,
    "msg": "El informe técnico PDF aún no ha sido generado. Ejecute primero la finalización de calibración."
  }
  ```

---

### 1.2 `POST /api/apply_profile`
Deploys the optimized PEQ filter matrix for the chosen target profile directly to the Yamaha RX-V673 NVRAM.

- **Query / Form Parameters**:
  - `profile` (required, string): Target profile key (e.g. `harman_wide_room`, `bk_1974`, `dirac_live`).
- **Success Response (200)**:
  ```json
  {
    "ok": true,
    "msg": "Perfil 'harman_wide_room' aplicado y verificado en la memoria NVRAM del receptor.",
    "profile": "harman_wide_room",
    "verified": true
  }
  ```
- **Failure Response (200)**:
  ```json
  {
    "ok": false,
    "msg": "Error de ejecución en auto_calibrate: <detalle_de_error>",
    "stderr": "auto_calibrate.py: error: ...",
    "exit_code": 2
  }
  ```

---

### 1.3 `POST /api/finalize_calibration`
Executes spatial averaging, dynamically generates all 4 acoustic plots (Spatial Average, L/R Response, Waterfall CSD, RT60 Decay), optimizes PEQ filters, compiles the PDF report, and updates the session manifest.

- **Query Parameters**:
  - `profile` (optional, string): Target profile key (default: active profile).
- **Success Response (200)**:
  ```json
  {
    "ok": true,
    "pdf_url": "/api/download_pdf?profile=harman_wide_room&t=1725398400",
    "msg": "Modelado acústico, gráficas de alta definición e informe PDF generados con éxito.",
    "figures": [
      {
        "id": "promedio_espacial",
        "url": "/figures/promedio_espacial_multipunto.png?t=1725398400"
      },
      {
        "id": "respuesta_acustica",
        "url": "/figures/respuesta_acustica_real.png?t=1725398400"
      },
      {
        "id": "waterfall_csd",
        "url": "/figures/waterfall_csd_comparison.png?t=1725398400"
      },
      {
        "id": "rt60_decay",
        "url": "/figures/rt60_decay_analysis.png?t=1725398400"
      }
    ]
  }
  ```

---

## 2. Command Line Interface (CLI) Contracts

### 2.1 `scripts/auto_calibrate.py`
Automated calibration optimizer and hardware publisher.

- **Arguments**:
  - `--profile`, `--target` (string, alias): Target acoustic profile key (e.g. `harman_wide_room`).
  - `--push` (flag): Deploys calculated 14 biquads to Yamaha RX-V673 via HTTP YNC XML API.
  - `--no-spatial` (flag): Disables 5-point spatial averaging and operates solely on Point 1.
- **Exit Codes**:
  - `0`: Success (calibration calculated and pushed if requested).
  - `1`: Acoustic runtime or communication failure.
  - `2`: Invalid command syntax or unparseable argument.
- **Contract Guarantee**: Both `--profile <key>` and `--target <key>` MUST be accepted identically without throwing exit status 2.

---

### 2.2 `scripts/03_generate_pdf_report.py`
Official engineering PDF document compiler.

- **Arguments**:
  - `--profile`, `--target` (string, alias, default: `harman_wide_room`): Acoustic target to evaluate.
  - `--output` (string, optional): Target PDF file destination.
- **Exit Codes**:
  - `0`: PDF compiled successfully.
  - `1`: Missing input measurement files (`.npz`) or ReportLab render exception.
