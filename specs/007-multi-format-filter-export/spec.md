# Feature Specification: Multi-Format Filter Export (REW, EqualizerAPO, CSV)

**Feature Branch**: `007-multi-format-filter-export`
**Created**: 2026-09-04
**Status**: Draft
**Input**: User description: "Export calculated PEQ filters to REW format (.req), EqualizerAPO, and CSV for external usage or archiving."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Export Filters to REW (.req) and EqualizerAPO Configuration (Priority: P1 MVP)

As an audio enthusiast or acoustic calibrator, I want to export the mathematically optimized 7-band parametric EQ filters (frequencies, Q values, gains) for Front L and Front R into Room EQ Wizard (.req) and EqualizerAPO config formats, so that I can apply room correction on PC media players, cross-verify curves in REW, or import them into third-party DSP processors.

**Why this priority**: REW (.req) and EqualizerAPO are the two universal standards for software audio DSP on Windows/Linux/Mac. Providing direct exports allows users to verify our calculated filters against REW's internal acoustic simulator or run system-wide room correction directly on playback sources.

**Independent Test**: Generate filters for any profile (e.g. `harman_wide_room`); invoke export; verify generated `.req` file conforms to REW filter file syntax (Filter 1: ON PK Fc ... Gain ... Q ...) and EqualizerAPO configuration contains valid `Channel: L` / `Channel: R` filter blocks.

**Acceptance Scenarios**:

1. **Given** calculated PEQ filters for Front L and Front R in the calibration engine, **When** the user requests export to REW format, **Then** the system produces a `.req` file with standard REW filter formatting for each channel (or combined dual-channel format) with exact center frequencies, gains, and Q values.
2. **Given** calculated PEQ filters, **When** the user requests export to EqualizerAPO format, **Then** the system produces a `.txt` config file specifying `Channel: L` followed by `Filter 1: ON PK ...` and `Channel: R` followed by its respective filters.
3. **Given** filters generated under hardware snapping (e.g., Yamaha RX-V673 28 discrete frequencies, 0.5-10 Q values), **When** exported, **Then** the export precisely reflects the discrete hardware values and labels them with the active hardware profile.

---

### User Story 2 - Tabular CSV Export and Web Dashboard Download Endpoints (Priority: P2)

As a power user, I want to download all filter parameters and frequency response delta curves as a structured CSV file, and access one-click download buttons on the web calibration dashboard, so that I can archive calibration sessions in spreadsheets or programmatic tooling.

**Why this priority**: CSV provides an open, portable tabular format suitable for analysis in Excel, Python, or MATLAB. Dashboard integration ensures non-technical users can download filters without using the CLI.

**Independent Test**: Trigger `/api/export_filters?format=csv&profile=harman_wide_room`; verify returned HTTP response has `Content-Type: text/csv` with columns `Channel,Band,Frequency_Hz,Gain_dB,Q,Filter_Type`, and verify dashboard contains download links for all three formats.

**Acceptance Scenarios**:

1. **Given** completed calibration for an active profile, **When** accessing the dashboard, **Then** download buttons or an export dropdown menu are visible offering `.req` (REW), `.txt` (EqualizerAPO), and `.csv` downloads.
2. **Given** a request to `/api/export_filters?format=all&profile={profile}`, **When** invoked, **Then** the system can package all export formats into a single zip bundle or provide dedicated individual downloads for REW, EqualizerAPO, and CSV.
3. **Given** missing or uncomputed calibration data, **When** requesting export, **Then** the system returns a clear error message indicating calibration must be computed first.

---

### User Story 3 - Standalone CLI Export Utility (Priority: P3)

As an automation script or command-line user, I want a dedicated CLI command `scripts/export_filters.py` that can export existing PEQ results to a specified output directory without running the web server.

**Why this priority**: Enables headless workflows, batch processing across multiple target curves, and automated archiving in CI or backup scripts.

**Independent Test**: Run `python3 scripts/export_filters.py --profile harman_wide_room --format all --out-dir exports/`; verify three formatted files are created and match the live server export output bit-for-bit.

**Acceptance Scenarios**:

1. **Given** existing calibration data in `data/`, **When** running `scripts/export_filters.py --profile harman_wide_room --format rew`, **Then** it generates valid REW filter files in the specified directory.
2. **Given** the CLI command, **When** `--help` is supplied, **Then** all supported formats (`rew`, `equalizerapo`, `csv`, `all`) and optional output directory arguments are clearly documented.

---

### Edge Cases

- What happens if Front L or Front R has inactive bands (0.0 dB gain)? The export formats must explicitly mark them as either `ON PK ... Gain 0.0` or `OFF`, preserving the 7-band indexing while preventing unintended amplification.
- What happens if the profile has not yet been computed? The endpoint and CLI must raise a friendly `400 Bad Request` or `FileNotFoundError` prompting the user to run `/api/apply_profile` or `scripts/auto_calibrate.py` first.
- What happens if special characters exist in profile names? Output filenames must be sanitized (alphanumeric and underscores only).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST export calculated PEQ filters to REW format (`.req`) following REW's native text representation (`Filter 1: ON PK Fc {freq} Hz Gain {gain} dB Q {q}`).
- **FR-002**: System MUST export calculated PEQ filters to EqualizerAPO configuration syntax (`Channel: L` / `Channel: R` headers with `Filter: ON PK Fc {freq} Hz Gain {gain} dB Q {q}`).
- **FR-003**: System MUST export calculated PEQ filters to structured CSV format with columns: `channel,band,frequency_hz,gain_db,q,filter_type`.
- **FR-004**: System MUST provide a REST endpoint `GET /api/export_filters` accepting query parameters `profile` (default `harman_wide_room`) and `format` (`rew`, `equalizerapo`, `csv`, `zip`/`all`).
- **FR-005**: The web calibration dashboard (`scripts/web_calibration_server.py`) MUST render an "Exportar Filtros" section with direct download triggers for REW, EqualizerAPO, and CSV.
- **FR-006**: System MUST provide a standalone CLI tool `scripts/export_filters.py` supporting `--profile`, `--format`, and `--out-dir`.
- **FR-007**: Exported files MUST include metadata headers documenting: generated timestamp, target profile name, active hardware profile (microphone, amplifier, speakers), and attenuation headroom.
- **FR-008**: Export operations MUST be strictly read-only and MUST NOT mutate the AVR hardware state or active calibration files.

## Success Criteria *(mandatory)*

- **SC-001**: 100% of exported REW files can be imported into REW EQ window without syntax parsing errors.
- **SC-002**: 100% of exported EqualizerAPO files can be loaded into EqualizerAPO configuration editor without syntax errors.
- **SC-003**: Filter values (frequencies, gains, Q) in exported files match the active AVR PEQ register values with zero numeric divergence.
- **SC-004**: All export downloads complete in under 200 ms on local network.
- **SC-005**: All existing 54 automated regression tests continue to pass alongside new export unit tests.

## Key Entities

- **PEQFilterSet**: 7-band parameter collections for Front L and Front R containing frequency (Hz), gain (dB), and Q factor.
- **ExportFormat**: Output representation specification (`rew`, `equalizerapo`, `csv`).
- **FilterExportArtifact**: Generated file with sanitized name, mime type, and embedded acoustic metadata header.

## Assumptions

- REW import expects separate channel filter files or a combined file with channel identifiers. Producing both per-channel files (`filters_L.req`, `filters_R.req`) and combined EqualizerAPO config satisfies both REW and EqualizerAPO conventions.
- Default export directory for CLI tool is `exports/`.
