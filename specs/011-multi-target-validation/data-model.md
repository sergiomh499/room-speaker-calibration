# Data Model: Multi-Target Validation & Comparative Acoustic Benchmarking

**Feature**: `011-multi-target-validation`  
**Date**: 2026-09-04  

---

## 1. Entities

### 1.1 `TargetProfileSpec`
Represents an acoustic reference target curve specification.

```python
@dataclass
class TargetProfileSpec:
    id: str                         # e.g., "harman_wide_room", "bk_1974", "dirac_live"
    name: str                       # Display name e.g., "Harman Target / Floyd Toole"
    category: str                   # e.g., "Música Hi-Fi / Audición Diaria"
    cutoff_hz: float = 64.0         # High-pass cutoff for 2.0 bookshelf protection
    bass_boost_db: float = 2.5      # Low-frequency boundary shelf
    treble_slope_db_oct: float = -0.8 # Treble roll-off slope in dB/octave
```

### 1.2 `TargetAlignmentResult`
Metrics comparing a single channel or stereo response against one target profile.

```python
@dataclass
class TargetAlignmentResult:
    target_id: str                  # Profile identifier
    target_name: str                # Human-readable profile name
    rms_error_db: float             # RMS deviation from 60 Hz to 5000 Hz
    max_peak_error_db: float        # Maximum error peak in modal band (60-400 Hz)
    fidelity_score_pct: float       # Percentage score (0 - 100%)
    rating: str                     # "S-TIER", "A", "B", "C"
```

### 1.3 `MultiTargetBenchmark`
Matrix comparing multiple measurement sweeps against the suite of target curves.

```python
@dataclass
class MultiTargetBenchmark:
    measurement_label: str          # e.g., "PEQ Manual", "YPAO Flat", "Through"
    evaluations: Dict[str, TargetAlignmentResult]
    best_fit_target_id: str         # Target ID with the lowest RMS error
```

---

## 2. Validation Rules & Invariants

1. **Subsonic Protection Invariant**: All target curves evaluated in 2.0 bookshelf mode MUST have $Target(30\text{ Hz}) \le -10.0\text{ dB}$ to match the physical boundary rolloff of the Q Acoustics 3020i.
2. **Frequency Alignment**: All target vectors MUST match the exact logarithmic or FFT frequency bins of the empirical measurement file (`freqs` array in `.npz`).
3. **Score Clamping**: `fidelity_score_pct` MUST be bounded within $[0.0, 100.0]$.
