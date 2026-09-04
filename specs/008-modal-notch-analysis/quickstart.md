# Quickstart: Modal Notch Diagnostic and Acoustic PEQ Rationale

## Prerequisites
- Python 3.10+ with `numpy`, `scipy`, and `requests`.
- Measured acoustic spatial average present in `data/medicion_promedio_espacial.npz`.
- Web calibration server running or test environment available.

## 1. Verify Empirical Modal Peaks and Physical Wavelength
Run the diagnostic script to compute exact resonance frequencies, Q factors, and room mode wavelengths:

```bash
python3 -c "
import numpy as np
from scripts.peq_optimizer import broadband_normalize, detect_modal_resonances

data = np.load('data/medicion_promedio_espacial.npz')
freqs = data['freqs']
norm_l = broadband_normalize(freqs, data['smooth_l'])
norm_r = broadband_normalize(freqs, data['smooth_r'])

peaks_l = detect_modal_resonances(freqs, norm_l, np.zeros_like(freqs))
peaks_r = detect_modal_resonances(freqs, norm_r, np.zeros_like(freqs))

print('=== MODOS DE SALA DETECTADOS ===')
print(f'Front L: {peaks_l[0][\"freq_hz\"]} Hz | +{peaks_l[0][\"elevation_db\"]:.1f} dB | Q={peaks_l[0][\"q\"]} | Lambda={343/peaks_l[0][\"freq_hz\"]:.2f}m')
print(f'Front R: {peaks_r[0][\"freq_hz\"]} Hz | +{peaks_r[0][\"elevation_db\"]:.1f} dB | Q={peaks_r[0][\"q\"]} | Lambda={343/peaks_r[0][\"freq_hz\"]:.2f}m')
"
```

Expected output:
- Front L: ~125 Hz | +6.3 dB | Q ~ 5.0 | Lambda ~ 2.74 m (axial mode)
- Front R: ~198 Hz | +4.2 dB | Q ~ 2.5 | Lambda ~ 1.73 m

## 2. Verify Speaker Transducer Health Above Schroeder Frequency (> 400 Hz)
Verify that L and R track with high precision above 400 Hz:

```bash
python3 -c "
import numpy as np
data = np.load('data/medicion_promedio_espacial.npz')
freqs = data['freqs']
mask = (freqs >= 400) & (freqs <= 8000)
diff = np.abs(data['smooth_l'][mask] - data['smooth_r'][mask])
print(f'Mean L/R delta (> 400 Hz): {np.mean(diff):.2f} dB')
print(f'Delta @ 1 kHz: {np.abs(data[\"smooth_l\"][np.argmin(np.abs(freqs - 1000))] - data[\"smooth_r\"][np.argmin(np.abs(freqs - 1000))]):.2f} dB')
assert np.mean(diff) < 1.0, 'Discrepancy above Schroeder indicates transducer issue!'
print('[✓] Transductores 100% íntegros y sanos.')
"
```

## 3. Verify Modal Diagnostics REST Endpoint
Test the live API endpoint for modal diagnostics:

```bash
curl -s http://127.0.0.1:53317/api/calibration/modal_diagnostics | jq .
```
