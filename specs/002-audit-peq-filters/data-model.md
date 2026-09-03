# Data Model: PEQ Filter Audit & Verification

## Entities

### 1. ParametricFilterBand
Represents an individual biquad filter in the 7-band channel configuration.

- **band**: `int` (1 to 7)
- **channel**: `str` ("L" or "R")
- **freq_hz**: `float` (center frequency snapped to Yamaha discrete grid)
- **q**: `float` (quality factor snapped to Yamaha discrete grid)
- **gain_db**: `float` (gain clamped between -12.0 dB and +3.0 dB)
- **target_mode**: `Optional[float]` (frequency of matched room resonance peak, if modal)
- **discrepancy_hz**: `float` (difference between filter frequency and matched peak frequency)
- **is_valid_discrete**: `bool` (whether frequency, Q, and gain match Yamaha discrete tables)
- **acoustic_role**: `str` ("Room Mode Attenuation", "Boundary Gain Trim", "Speaker Crossover", "Neutral/Inactive")

---

### 2. RoomResonanceMode
Represents a physical room resonance peak identified from empirical acoustic data below 500 Hz.

- **freq_hz**: `float` (center peak frequency in Hz)
- **prominence_db**: `float` (peak height relative to surrounding baseline)
- **bandwidth_hz**: `float` (half-power bandwidth -3 dB down from peak)
- **estimated_q**: `float` ($f_0 / \Delta f$)
- **channel**: `str` ("L" or "R")
- **addressed_by_filter**: `Optional[int]` (index of the filter addressing this mode, or None)

---

### 3. FilterAuditDiagnosis
The comprehensive audit result comparing the active PEQ matrix against empirical room acoustics.

- **channel**: `str` ("L", "R", or "Stereo")
- **verdict**: `str` ("ACCURATE", "SUBOPTIMAL", "ERRONEOUS")
- **verdict_summary**: `str` (plain-language explanation of findings)
- **residual_rms_error_db**: `float` (RMS deviation between simulated filtered response and target curve)
- **modal_peak_attenuation_db**: `float` (attenuation achieved at primary resonance peak)
- **stereo_imbalance_db**: `float` (mean absolute difference between L and R responses)
- **unaddressed_modes**: `List[RoomResonanceMode]` (physical modes left without a filter)
- **misaligned_filters**: `List[ParametricFilterBand]` (filters > 5 Hz off or placed on flat response)
- **recommended_peq**: `Optional[Dict[str, List[ParametricFilterBand]]]` (recalculated optimal matrix if suboptimal)
