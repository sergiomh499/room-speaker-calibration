# Data Model: Multi-Format Filter Export

## Entities

### 1. PEQBandExport
Represents a single parametric equalizer band.

| Field | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `channel` | string | Target channel | `"L"` or `"R"` |
| `band` | integer | Discrete band index | 1 to 7 |
| `frequency_hz` | float | Center frequency in Hz | Discrete Yamaha frequencies (31.3 Hz to 16.0 kHz) |
| `gain_db` | float | Filter gain in decibels | -20.0 to +6.0 dB, 0.5 dB steps |
| `q` | float | Quality factor | 0.500 to 10.080 |
| `filter_type` | string | DSP filter geometry | `"PK"` (Peaking / Parametric) |
| `is_active` | boolean | Whether gain != 0.0 dB | true / false |

### 2. ExportBundle
Represents a formatted multi-format collection.

| Field | Type | Description |
| :--- | :--- | :--- |
| `profile` | string | Community profile identifier (e.g. `harman_wide_room`) |
| `timestamp` | string | Generation ISO timestamp |
| `hardware` | object | Active hardware profile (microphone, amplifier, speakers) |
| `preamp_db` | float | Calculated digital headroom offset (`-max(0, max_gain)`) |
| `bands_l` | list[PEQBandExport] | 7 Front Left bands |
| `bands_r` | list[PEQBandExport] | 7 Front Right bands |
| `artifacts` | map[string, bytes] | Dictionary of format names to formatted byte payloads |
