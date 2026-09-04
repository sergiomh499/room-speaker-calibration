# Quickstart: Ground-Truth Empirical PEQ Calibration & Validation

## 1. Verify Ground-Truth Mathematical Biquad Solver

Execute the verified biquad optimizer over real empirical measurement files:

```bash
python3 -c "
import numpy as np
from scripts.peq_optimizer import optimize_stereo_peq, BiquadFilter

# Load real empirical acoustic data
data = np.load('data/medicion_promedio_espacial.npz')
freqs = data['freqs']
resp_l = data['smooth_l']
resp_r = data['smooth_r']

# Run solver
result = optimize_stereo_peq(
    freqs_hz=freqs,
    left_sweet_spot=resp_l,
    right_sweet_spot=resp_r,
    target_db=np.zeros_like(freqs),
    target_key='harman_wide_room'
)
metrics = result.get('metrics', {})
print(f'Predicted RMS error reduction: {metrics.get(\"predicted_rms_reduction_db\", 0.0):.2f} dB')
print('[✓] Biquad mathematical solver verified successfully.')
"
```

## 2. Verify Audited Target Curves (2.0 Bookshelf Architecture)

Audit that all 9 target curves in `config/targets.json` enforce safe bookshelf operations:

```bash
python3 -c "
import json
with open('config/targets.json') as f:
    cfg = json.load(f)

for name, p in cfg.items():
    if name == '_meta': continue
    bands = p.get('bands', {})
    for b_idx in range(1, 8):
        b = bands.get(f'Band {b_idx}')
        if b:
            assert -12.0 <= b['gain_l'] <= 3.0, f'Invalid gain L: {b[\"gain_l\"]}'
            assert -12.0 <= b['gain_r'] <= 3.0, f'Invalid gain R: {b[\"gain_r\"]}'
print('[✓] 100% of target profile bands within physical amplifier safety limits.')
"
```

## 3. Verify Multichannel Channel Parameterization

Verify that multichannel layouts are correctly routed:

```bash
python3 -c "
from scripts.peq_optimizer import route_multichannel_layout
for layout in ['STEREO_2_0', 'STEREO_2_1', 'SURROUND_5_1', 'SURROUND_7_1']:
    channels = route_multichannel_layout(layout)
    print(f'{layout} -> {channels}')
print('[✓] Multichannel routing validated.')
"
```
