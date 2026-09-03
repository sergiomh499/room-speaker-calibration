# Feature Specification: Dynamic Synchronization and Verification of Technical Reports and Acoustic Figures

**Feature Branch**: `003-fix-report-graphs`
**Created**: 2026-09-03
**Status**: Ready for Review
**Input**: User description: "el informe tecnico graficas etc parece incorrectas y que no se actualizan, verifica que todo este correcto"

## Clarifications

### Session 2026-09-03
- Q: ¿De qué fuente acústica debe calcularse la Cascada Espectral 3D (Waterfall CSD) para que refleje el decaimiento temporal real sin ceros? → A: Usar la respuesta al impulso medida real del Punto 1 (Sweet Spot / Posición Principal de Escucha) ya que preserva la fase física real y las colas de resonancia acústica sin cancelaciones por promediado.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Real-time Synchronized Technical Report with Active Profile Awareness (Priority: P1)

As a listener calibrating the room audio system, I want the downloaded technical report (PDF) to immediately reflect the currently selected target profile and live measurements, so that I have a 100% accurate, up-to-date record of my room's acoustic performance.

**Why this priority**: When users download the technical report, seeing outdated dates, incorrect profile target curves, or stale figures destroys confidence in the entire calibration process. Real-time synchronization of the core report is essential.

**Independent Test**: Can be fully tested by selecting any profile (e.g. B&K 1974 or Dirac Live), running finalization/verification, and downloading the PDF; the generated document must dynamically state the active profile, current timestamp, and exact measured modal metrics.

**Acceptance Scenarios**:

1. **Given** a calibration session with freshly recorded measurements, **When** the user finalizes calibration or switches profiles, **Then** the technical PDF report is automatically regenerated using the active profile's target curves, deployed PEQ parameters, and current measurement data.
2. **Given** an updated calibration run, **When** the user requests the PDF report via the web interface or direct download, **Then** the served file matches the latest generated version with zero caching delay.

---

### User Story 2 - Fully Dynamic Pipeline Figure Generation and Elimination of Stale Plots (Priority: P2)

As an audio enthusiast reviewing acoustic plots, I want all displayed graphs (spatial average, frequency response, impulse response / RT60, and 3D waterfall) to be dynamically calculated from the latest physical measurement session, so that no static, orphaned, or un-updated figures appear in the interface.

**Why this priority**: The presence of un-updated or orphaned figures (such as static RT60 plots from prior days) confuses users and gives the impression that the calibration pipeline has failed or is returning fake data.

**Independent Test**: Can be tested by executing a new sweep, observing that all figure assets update their file modification timestamps, and verifying that the web UI displays fresh images with cache-busting parameters.

**Acceptance Scenarios**:
1. **Given** a completed 5-point measurement, **When** the analysis pipeline runs, **Then** every displayed figure asset (`promedio_espacial_multipunto.png`, `respuesta_acustica_real.png`, `waterfall_csd_comparison.png`, and impulse/RT60 decay) is generated afresh from the actual recorded audio data, sourcing the 3D Waterfall CSD and impulse decay strictly from the physical Sweet Spot (Punto 1) impulse response.
2. **Given** the web interface results panel, **When** figures are rendered, **Then** all image elements include dynamic cache-busting query strings and strict HTTP cache-control headers preventing browser cache staleness.
---

### User Story 3 - Unification and Instant Delivery of Verification Audits (Priority: P3)

As a system operator validating acoustic correction, I want the multi-mode verification report (comparing Through, YPAO Flat/Front/Natural, and PEQ Manual) to be accessible in both high-definition interactive HTML and downloadable PDF formats, so that I can audit certification decisions across all platforms.

**Why this priority**: Consolidating audit outputs ensures that whether the user reviews the results in a browser, prints a PDF, or inspects the AVR hardware registers, all metrics, badges, and figures tell a single coherent story.

**Independent Test**: Can be tested by running multi-mode verification and verifying that the audit metrics, S-TIER certification status, and comparison curves match identically between the web interface and the generated report.

**Acceptance Scenarios**:

1. **Given** completed verification sweeps across test modes, **When** the verification analysis is processed, **Then** the comparative ranking table and high-resolution multi-curve graph are immediately updated and linked in the interface.
2. **Given** a certified S-TIER calibration, **When** the user downloads the audit report, **Then** the report includes the hardware register dump, acoustic metrics table, and 3D spectral decay graph.

---

### Edge Cases

- **Missing or incomplete sweeps**: If only a subset of measurement points is recorded, the pipeline must clearly indicate which points are missing and prevent generating a misleading 5-point report.
- **Microphone disconnection or clipping during sweep**: If SNR is insufficient, the system must abort figure generation with an informative error rather than overwriting valid previous figures with corrupted artifacts.
- **Offline AVR during hardware readback**: If the Yamaha receiver is powered off or unreachable, the report must display "Hardware unreachable (Offline)" in the register section without failing the acoustic analysis.

### Functional Requirements

- **FR-001**: System MUST accept an active profile parameter when generating the technical PDF report and calculate simulated/measured curves against that specific profile.
- **FR-002**: System MUST dynamically generate all acoustic figures referenced in the report and web UI directly from the current measurement session data (`.npz` files).
- **FR-003**: System MUST compute the 3D Waterfall CSD and impulse decay using the physical impulse response from Punto 1 (Sweet Spot), guaranteeing non-zero time-frequency decay analysis, and replace any static or stale legacy image files.
- **FR-004**: System MUST serve all report and figure endpoints with `Cache-Control: no-cache, no-store, must-revalidate` and appropriate cache-busting tokens.
- **FR-005**: System MUST synchronize the download paths between the web server endpoint (`/api/download_pdf`), the session storage, and the generation script output directory.
- **FR-006**: System MUST ensure narrative text in reports dynamically reflects computed metrics (such as detected modal peak frequencies and attenuation values) rather than fixed hardcoded phrases.
- **FR-007**: System MUST render the verification comparison results immediately upon loading if valid verification data exists on disk for the selected profile.
- **FR-008**: System MUST provide an automated verification script or command to check that all generated figures and reports match the timestamp of the latest acoustic data.

---

### Key Entities

- **TechnicalReportArtifact**: Represents the generated PDF report containing acoustic summary, frequency response curves, PEQ filter table, and modal diagnostics.
- **AcousticFigureAsset**: Represents an image file generated from NumPy data arrays (spatial average, L/R response, impulse response, 3D waterfall CSD, or multi-mode comparative verification).
- **VerificationAuditData**: Data structure encapsulating objective acoustic metrics (modal reduction, target RMS deviation, stereo imbalance, SNR) and S-TIER certification status.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of figures displayed in the web UI and embedded in the PDF report are generated from data timestamped within the current measurement session.
- **SC-002**: Switching target profiles and requesting a report generates an updated PDF reflecting the new profile in under 5.0 seconds.
- **SC-003**: Zero HTTP 304 or stale cached image responses served to clients after a new calibration or verification run.
- **SC-004**: Discrepancy between reported metrics in the web UI and metrics in the downloaded PDF is 0.00 dB across all bands.

---

## Assumptions

- Python runtime has `matplotlib`, `reportlab`, `scipy`, and `numpy` installed and functional.
- The web calibration server runs on port 53317 (dual HTTP/HTTPS) and has write permissions to `reports/`, `figures/`, and `data/`.
- The user operates an LG C5 OLED, Yamaha RX-V673 AVR, and Q Acoustics 3020i speakers connected via HDMI ARC and optical/PCM audio pathways.
