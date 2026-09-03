# API & Interface Contracts: Acoustic PEQ Optimization Engine

**Feature**: `004-fix-peq-calculation`
**Date**: 2026-09-03
**Status**: Complete

## 1. Python Module Interface (`scripts/peq_optimizer.py`)

### 1.1 `detect_modal_resonances`
```python
def detect_modal_resonances(
    freqs_hz: np.ndarray,
    response_db: np.ndarray,
    target_db: np.ndarray,
    min_elevation_db: float = 1.5,
    max_peaks: int = 7,
    max_freq: float = 500.0,
) -> List[Dict[str, float]]:
    """
    Detects true room resonance peaks strictly where measured SPL exceeds target SPL
    by at least min_elevation_db (+1.5 dB). Computes physical bandwidth in Hz and
    snaps Q factor to Yamaha discrete steps.

    Returns:
        List of dicts: [
            {"freq_hz": float, "elevation_db": float, "bandwidth_hz": float, "q": float}
        ]
    """
```

### 1.2 `optimize_stereo_peq`
```python
def optimize_stereo_peq(
    freqs_hz: np.ndarray,
    left_sweet_spot: np.ndarray,
    right_sweet_spot: np.ndarray,
    target_db: np.ndarray,
    left_spatial_avg: Optional[np.ndarray] = None,
    right_spatial_avg: Optional[np.ndarray] = None,
    sweet_spot_weight: float = 0.8,
    target_key: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Coordinated stereo parametric equalizer optimization for Yamaha RX-V673.
    - Pairs common modes within +-5% frequency and assigns symmetrical center freqs and Q.
    - Applies independent trim only if asymmetric boundary gain is confirmed (<= 3.0 dB diff).
    - Strictly clamps gain to 0.0 dB on dips and nulls.
    - Preserves high-frequency voicing (> 500 Hz) defined in targets.json.
    - Enforces cumulative cut limit (<= -12.0 dB composite response).

    Returns:
        {
            "channels": {
                "left": List[Dict[str, Any]],   # 7 PEQFilterBand dicts
                "right": List[Dict[str, Any]],  # 7 PEQFilterBand dicts
            },
            "metrics": {
                "predicted_rms_reduction_db": float,
                "predicted_modal_attenuation_db": float,
                "execution_time_ms": float,
            }
        }
    """
```

---

## 2. CLI Interface Contract (`scripts/auto_calibrate.py`)

```bash
python3 scripts/auto_calibrate.py [--profile|--target <name>] [--multipoint|--no-spatial] [--push] [--dry-run]
```

### Arguments:
- `--profile` / `--target`: Target curve profile (`harman_wide_room`, `bk_1974`, `dirac_live`, `cinema_blockbuster`, `pure_vocal_clarity`, `audiophile_flat`). Defaults to `harman_wide_room`.
- `--multipoint` (default: True): Ingests 5-point spatial average weighted with Sweet Spot. `--no-spatial` forces 100% Sweet Spot.
- `--push`: Sends optimized PEQ parameters directly to Yamaha RX-V673 via HTTP YNC XML API with readback verification.
- `--dry-run`: Runs optimization and prints parameter tables without modifying hardware.

### Exit Codes:
- `0`: Success, parameters generated and verified.
- `1`: Invalid profile or missing empirical measurement file.
- `2`: Hardware communication / readback verification failure.

---

## 3. Web Service API Contracts (`scripts/web_calibration_server.py`)

### 3.1 `GET /api/verification_comparison`
Returns comparative acoustic metrics for all calibration curves (Through, YPAO Flat, YPAO Natural, PEQ Manual).

#### Response Schema (JSON):
```json
{
  "ok": true,
  "profile": "harman_wide_room",
  "comparative_curves": [
    {
      "id": "peq_manual",
      "name": "PEQ Manual (Harman Target)",
      "short_name": "PEQ Manual",
      "rms_avg_db": 1.74,
      "rms_l_db": 1.71,
      "rms_r_db": 1.77,
      "stereo_imbalance_db": 1.15,
      "modal_peak_119hz_db": 1.25,
      "target_alignment_pct": 97.3,
      "fidelity_score_pct": 97.3,
      "rank": 1,
      "badge": "🥇 #1 RECOMENDADA",
      "is_live": true,
      "provenance": "Medición en Vivo (Sweet Spot)",
      "color": "#00e676"
    }
  ],
  "best_curve": {
    "id": "peq_manual",
    "name": "PEQ Manual (Harman Target)",
    "target_alignment_pct": 97.3,
    "fidelity_score_pct": 97.3,
    "rms_avg_db": 1.74
  }
}
```

*Contract Invariant*: Both `target_alignment_pct` and `fidelity_score_pct` MUST be present, non-null, and equal.

### 3.2 `POST /api/apply_profile?profile=<key>`
Deploys the optimized PEQ profile to the Yamaha receiver NVRAM.

#### Response Schema (JSON):
```json
{
  "ok": true,
  "msg": "Perfil 'harman_wide_room' aplicado y verificado en la memoria NVRAM del receptor.",
  "profile": "harman_wide_room",
  "verified": true
}
```
