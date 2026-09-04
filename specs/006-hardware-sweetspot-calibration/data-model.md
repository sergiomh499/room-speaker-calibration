# Data Model: Tight Sweet-Spot Multipoint & Hardware Profile Calibration

**Feature**: `006-hardware-sweetspot-calibration`
**Date**: 2026-09-04

---

## 1. Hardware Configuration Entity (`config/hardware.json`)

The central persistent entity managing the user's active electroacoustic signal chain.

```json
{
  "active": {
    "microphone": "pixel_9_pro_calibrated",
    "amplifier": "yamaha_rx_v673",
    "speakers": "q_acoustics_3020i"
  },
  "microphones": {
    "pixel_9_pro_calibrated": {
      "id": "pixel_9_pro_calibrated",
      "name": "Google Pixel 9 Pro (Tethered Acoustic)",
      "type": "mems_dual_capsule",
      "cal_file": "config/calibrations/pixel_9_pro_90deg.cal",
      "orientation": "90_degrees_vertical",
      "sensitivity_offset_db": 0.0,
      "max_sampling_rate_hz": 48000
    },
    "minidsp_umik1": {
      "id": "minidsp_umik1",
      "name": "miniDSP UMIK-1 (USB Calibrated)",
      "type": "electret_condenser",
      "cal_file": "config/calibrations/umik1_90deg.cal",
      "orientation": "90_degrees_vertical",
      "sensitivity_offset_db": 0.0,
      "max_sampling_rate_hz": 48000
    },
    "dayton_umm6": {
      "id": "dayton_umm6",
      "name": "Dayton Audio UMM-6",
      "type": "electret_condenser",
      "cal_file": "config/calibrations/dayton_umm6_90deg.cal",
      "orientation": "90_degrees_vertical",
      "sensitivity_offset_db": 0.0,
      "max_sampling_rate_hz": 48000
    },
    "generic_flat": {
      "id": "generic_flat",
      "name": "Generic Flat Microphone",
      "type": "uncalibrated",
      "cal_file": null,
      "orientation": "90_degrees_vertical",
      "sensitivity_offset_db": 0.0,
      "max_sampling_rate_hz": 48000
    }
  },
  "amplifiers": {
    "yamaha_rx_v673": {
      "id": "yamaha_rx_v673",
      "brand": "Yamaha",
      "model": "RX-V673",
      "protocol": "ync_xml",
      "default_ip": "192.168.1.43",
      "peq_bands": 7,
      "discrete_frequencies_hz": [
        62.5, 78.7, 99.2, 125.0, 157.5, 198.4, 250.0, 315.0, 396.9, 500.0,
        630.0, 793.7, 1000.0, 1260.0, 1587.4, 2000.0, 2520.0, 3174.8, 4000.0,
        5040.0, 6349.6, 8000.0, 10080.0, 12700.0, 16000.0
      ],
      "discrete_qs": [
        0.500, 0.630, 0.794, 1.000, 1.260, 1.587, 2.000, 2.520, 3.175, 4.000, 5.040, 6.350, 8.000, 10.080
      ],
      "gain_step_db": 0.5,
      "max_boost_db": 3.0,
      "max_cut_db": -12.0
    },
    "generic_avr": {
      "id": "generic_avr",
      "brand": "Generic",
      "model": "Standard AVR / DSP",
      "protocol": "manual_export",
      "default_ip": null,
      "peq_bands": 7,
      "discrete_frequencies_hz": null,
      "discrete_qs": null,
      "gain_step_db": 0.1,
      "max_boost_db": 6.0,
      "max_cut_db": -18.0
    }
  },
  "speakers": {
    "q_acoustics_3020i": {
      "id": "q_acoustics_3020i",
      "brand": "Q Acoustics",
      "model": "3020i",
      "type": "2-way Bass-Reflex",
      "woofer_inch": 5.0,
      "f3_cutoff_hz": 64.0,
      "crossover_hz": 2400.0,
      "nominal_impedance_ohm": 6.0,
      "voicing_compensation": {
        "freq_hz": 2520.0,
        "q": 1.26,
        "gain_db": 1.5,
        "reason": "Compensación de dip de cruce 3020i verificado por Spinorama"
      }
    },
    "generic_bookshelf": {
      "id": "generic_bookshelf",
      "brand": "Generic",
      "model": "Standard Bookshelf",
      "type": "2-way Sealed/Reflex",
      "woofer_inch": 5.25,
      "f3_cutoff_hz": 80.0,
      "crossover_hz": 2500.0,
      "nominal_impedance_ohm": 8.0,
      "voicing_compensation": null
    },
    "generic_tower": {
      "id": "generic_tower",
      "brand": "Generic",
      "model": "Floorstanding Tower",
      "type": "3-way Bass-Reflex",
      "woofer_inch": 6.5,
      "f3_cutoff_hz": 40.0,
      "crossover_hz": 2800.0,
      "nominal_impedance_ohm": 6.0,
      "voicing_compensation": null
    }
  }
}
```

---

## 2. Tight Cluster Measurement Model (`TightClusterData`)

Represents the spatial multi-sweep acquisition around the sweet spot.

| Field | Type | Description |
|---|---|---|
| `point_1_sweet_spot` | `np.ndarray` | Master measurement at central ear height (MLP). Weight: 70%. |
| `point_2_left_ear` | `np.ndarray` | 15 cm to the left of Point 1. Satellite weight: 7.5%. |
| `point_3_right_ear` | `np.ndarray` | 15 cm to the right of Point 1. Satellite weight: 7.5%. |
| `point_4_forward` | `np.ndarray` | 15 cm forward towards screen. Satellite weight: 7.5%. |
| `point_5_elevated` | `np.ndarray` | 15 cm vertically above Point 1. Satellite weight: 7.5%. |
| `weighted_response_l` | `np.ndarray` | Computed spatial baseline: $0.70 \times P_1(L) + 0.30 \times \text{mean}(P_{2..5}(L))$. |
| `weighted_response_r` | `np.ndarray` | Computed spatial baseline: $0.70 \times P_1(R) + 0.30 \times \text{mean}(P_{2..5}(R))$. |
| `smoothing_mode` | `str` | `"variable"` (REW Variable Smoothing algorithm). |
| `normalization_anchor` | `str` | `"broadband_300_3000_hz"`. |

---

## 3. Modal Resonance Diagnostics Model (`ModalDiagnostics`)

Provides side-by-side diagnostic transparency for each channel.

| Field | Type | Description |
|---|---|---|
| `channel` | `str` | `"L"` or `"R"`. |
| `baseline_spl_db` | `float` | Integrated SPL in the 300 Hz – 3000 Hz broadband normalization window. |
| `detected_peaks` | `List[Dict]` | List of detected room modes with `center_hz`, `elevation_db`, `f_low_hz`, `f_high_hz`, `q_continuous`. |
| `filter_assignments` | `List[Dict]` | 7-band assigned filters: `band_idx`, `freq_hz`, `q`, `gain_db`, `status` (`"MODAL_NOTCH"`, `"VOICING_BOOST"`, `"FLAT_PRESERVE"`). |
| `predicted_rms_error`| `float` | Estimated error reduction in dB within the 30–500 Hz modal band. |
