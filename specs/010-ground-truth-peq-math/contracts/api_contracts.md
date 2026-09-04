# Interface Contracts: Ground-Truth PEQ Optimization & Multichannel Routing

## 1. REST API Contract: PEQ Optimization Solver

`POST /api/calibration/solve_peq`

Computes ground-truth biquad filter coefficients for active channels based on measured transfer functions.

### Request Payload

```json
{
  "profile_key": "harman_wide_room",
  "layout": "STEREO_2_0",
  "channels": ["L", "R"],
  "speaker_model": "q_acoustics_3020i",
  "crossover_hz": 0
}
```

### Response Payload

```json
{
  "ok": true,
  "profile_key": "harman_wide_room",
  "layout": "STEREO_2_0",
  "computation_time_ms": 12.4,
  "results": {
    "L": {
      "pre_rms_error": 4.82,
      "post_rms_error": 2.15,
      "rms_reduction_db": 2.67,
      "bands": [
        { "band": 1, "freq": 125.0, "gain": -2.5, "q": 5.04, "role": "MODAL_NOTCH" },
        { "band": 2, "freq": 2520.0, "gain": 1.5, "q": 1.26, "role": "CROSSOVER_VOICING" },
        { "band": 3, "freq": 31.3, "gain": 0.0, "q": 1.0, "role": "TRANSPARENT_PASS" },
        { "band": 4, "freq": 39.4, "gain": 0.0, "q": 1.0, "role": "TRANSPARENT_PASS" },
        { "band": 5, "freq": 49.6, "gain": 0.0, "q": 1.0, "role": "TRANSPARENT_PASS" },
        { "band": 6, "freq": 62.5, "gain": 0.0, "q": 1.0, "role": "TRANSPARENT_PASS" },
        { "band": 7, "freq": 78.7, "gain": 0.0, "q": 1.0, "role": "TRANSPARENT_PASS" }
      ]
    },
    "R": {
      "pre_rms_error": 4.12,
      "post_rms_error": 2.08,
      "rms_reduction_db": 2.04,
      "bands": [
        { "band": 1, "freq": 198.4, "gain": -2.0, "q": 2.52, "role": "MODAL_NOTCH" },
        { "band": 2, "freq": 2520.0, "gain": 2.0, "q": 1.26, "role": "CROSSOVER_VOICING" },
        { "band": 3, "freq": 31.3, "gain": 0.0, "q": 1.0, "role": "TRANSPARENT_PASS" },
        { "band": 4, "freq": 39.4, "gain": 0.0, "q": 1.0, "role": "TRANSPARENT_PASS" },
        { "band": 5, "freq": 49.6, "gain": 0.0, "q": 1.0, "role": "TRANSPARENT_PASS" },
        { "band": 6, "freq": 62.5, "gain": 0.0, "q": 1.0, "role": "TRANSPARENT_PASS" },
        { "band": 7, "freq": 78.7, "gain": 0.0, "q": 1.0, "role": "TRANSPARENT_PASS" }
      ]
    }
  }
}
```

## 2. Hardware Synchronization Contract (Yamaha RX-V673 NVRAM)

`POST /api/apply_peq_hardware`

Applies the calculated PEQ bands for any active channel (`L`, `R`, `C`, `SW`, `SL`, `SR`, `SBL`, `SBR`).

```xml
<YAMAHA_AV cmd="PUT">
  <System>
    <Misc>
      <Network_Standby>On</Network_Standby>
    </Misc>
  </System>
  <Main_Zone>
    <PEQ>
      <Manual>
        <{Channel}>
          <Band_{N}>
            <Freq>{Frequency_Hz}</Freq>
            <Gain>{Gain_dB}</Gain>
            <Q>{Q_Factor}</Q>
          </Band_{N}>
        </{Channel}>
      </Manual>
    </PEQ>
  </Main_Zone>
</YAMAHA_AV>
```
