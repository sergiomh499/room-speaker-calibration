# Quickstart: Multi-Target Validation & Comparative Acoustic Benchmarking

## 1. Verify Target Curve Calculation & Consistency

Execute Python snippet to ensure all target curves share the exact 2.0 bookshelf roll-off and correct tilt:

```bash
python3 -c "
import numpy as np
from scripts.peq_optimizer import generate_bookshelf_target_curve

freqs = np.array([30.0, 64.0, 100.0, 1000.0, 10000.0])
for target_key in ['harman_wide_room', 'bk_1974', 'dirac_live', 'cinema_blockbuster', 'audiophile_flat']:
    tc = generate_bookshelf_target_curve(freqs, target_key, fc_hz=64.0)
    print(f'{target_key:<20} | 30Hz: {tc[0]:.1f} dB | 1kHz: {tc[3]:.1f} dB')
    assert tc[0] < -10.0, f'Missing low frequency bookshelf roll-off for {target_key}'
print('[✓] 100% of target curves verified for 2.0 bookshelf acoustic safety.')
"
```

## 2. Evaluate Multi-Target Benchmarking Engine

Run multi-target cross-comparison across empirical sweeps:

```bash
python3 -c "
import numpy as np
from scripts.verify_calibration import evaluate_multi_target_alignment

data = np.load('data/medicion_verificacion_manual.npz')
freqs = data['freqs']
resp_l = data['smooth_l']
resp_r = data['smooth_r']

benchmark = evaluate_multi_target_alignment(freqs, resp_l, resp_r)
for t_id, res in benchmark.items():
    print(f'{res[\"target_name\"]:<30} -> RMS: {res[\"rms_error_db\"]:.2f} dB | Score: {res[\"fidelity_score_pct\"]:.1f}% ({res[\"rating\"]})')
"
```

## 3. Verify Server Multi-Target Endpoints

```bash
curl -s http://127.0.0.1:53317/api/targets | jq .
curl -s -X POST http://127.0.0.1:53317/api/calibration/multi_target_eval -H 'Content-Type: application/json' -d '{}' | jq .
```

## 4. Verify 1-to-1 Professional Calibration & Preset Pre-loading

```bash
# Preload the B&K 1974 preset directly to the Yamaha RX-V673
curl -s -X POST http://127.0.0.1:53317/api/calibration/preload_preset \
  -H 'Content-Type: application/json' \
  -d '{"profile_id": "bk_1974"}' | jq .

# Query historical sessions
curl -s http://127.0.0.1:53317/api/sessions/history | jq .
```

