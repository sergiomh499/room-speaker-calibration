# Research: Multi-Format Filter Export (REW, EqualizerAPO, CSV)

## 1. REW (.req) Filter File Syntax

### Decision
Generate REW filter files following the official Room EQ Wizard equalizer export specification:
```text
Filter Settings file

Room EQ V5.20 or later
Dated: {YYYY-MM-DD HH:MM:SS}
Notes: Room Speaker Calibration - Profile: {profile} - Channel: {channel}

Equaliser: Generic
Filter  1: ON  PK       Fc   {freq:7.1f} Hz  Gain {gain:+6.1f} dB  Q {q:5.3f}
Filter  2: ON  PK       Fc   {freq:7.1f} Hz  Gain {gain:+6.1f} dB  Q {q:5.3f}
...
Filter  7: ON  PK       Fc   {freq:7.1f} Hz  Gain {gain:+6.1f} dB  Q {q:5.3f}
```

### Rationale
- REW's EQ window imports `.req` files seamlessly when `Equaliser: Generic` or `Equaliser: Configurable` is used.
- Per-channel files (`filters_harman_wide_room_L.req` and `filters_harman_wide_room_R.req`) allow individual import into Left and Right channel measurement slots.

### Alternatives Considered
- Single combined REW file: REW does not natively support multi-channel in a single `.req` file; it expects one file per channel.

---

## 2. EqualizerAPO Syntax

### Decision
Generate EqualizerAPO configuration files using standard channel switching and parametric filter commands:
```text
# EqualizerAPO Configuration
# Generated: {timestamp}
# Profile: {profile}
# Hardware: {mic} / {amp} / {speakers}

# Preamp to prevent digital clipping from positive boosts
Preamp: {preamp:+5.1f} dB

Channel: L
Filter 1: ON PK Fc {freq_l1} Hz Gain {gain_l1} dB Q {q_l1}
...
Filter 7: ON PK Fc {freq_l7} Hz Gain {gain_l7} dB Q {q_l7}

Channel: R
Filter 1: ON PK Fc {freq_r1} Hz Gain {gain_r1} dB Q {q_r1}
...
Filter 7: ON PK Fc {freq_r7} Hz Gain {gain_r7} dB Q {q_r7}
```

### Rationale
- EqualizerAPO applies `Channel: L` and `Channel: R` directives sequentially to the Windows audio pipeline.
- Automatic calculation of `Preamp: -{max_boost} dB` ensures zero digital clipping when positive EQ boosts are present (e.g. +1.5 dB or +2.0 dB).

---

## 3. Structured Tabular CSV Format

### Decision
Use standard comma-separated values with clear headers:
```csv
channel,band,frequency_hz,gain_db,q,filter_type,profile,hardware_mic,hardware_amp,hardware_speakers
L,1,2520.0,1.5,1.260,PK,harman_wide_room,pixel_9_pro_calibrated,yamaha_rx_v673,q_acoustics_3020i
...
R,7,12700.0,0.0,1.000,PK,harman_wide_room,pixel_9_pro_calibrated,yamaha_rx_v673,q_acoustics_3020i
```

### Rationale
- Easily importable by pandas, Excel, Google Sheets, or MATLAB.
- Contains full hardware provenance and profile tags on every row.

---

## 4. Web Dashboard & CLI Packaging

### Decision
- Endpoint: `GET /api/export_filters?format={rew|equalizerapo|csv|all}&profile={profile}`
- `format=rew`: downloads a ZIP containing `filters_L.req` and `filters_R.req`.
- `format=equalizerapo`: downloads `equalizer_apo_config.txt`.
- `format=csv`: downloads `peq_filters.csv`.
- `format=all`: downloads a combined ZIP containing all above artifacts.
- CLI: `python3 scripts/export_filters.py --profile harman_wide_room --format all --out-dir exports/`
