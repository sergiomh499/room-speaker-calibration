# Contract: Audio Deconvolution & Real Acoustic Analysis Engine

**Module**: `services/dspEngine.ts` / `services/nativeAudio.ts`
**Version**: 1.0.0

## 1. Input Specification

### 1.1 Recorded Audio Buffer
The audio capture engine must deliver uncompressed PCM samples satisfying:
- **Format**: 16-bit signed integer Little-Endian (`S16_LE`) or normalized 32-bit float (`Float32Array`).
- **Sample Rate ($f_s$)**: Strictly $48,000\text{ Hz}$.
- **Channels**: Single-channel mono (`AudioFormat.CHANNEL_IN_MONO`).
- **Source**: `MediaRecorder.AudioSource.UNPROCESSED` (Android 7.0+) or direct USB Audio Class 1/2 driver for external microphones.
- **Duration**: Sweep duration plus acoustic reverberation decay lead-out (typically $5.0\text{ s}$ sweep $+ 1.5\text{ s}$ tail $= 6.5\text{ s}$).

### 1.2 Excitation Inverse Filter ($s^{-1}(t)$)
- **Signal Type**: Farina logarithmic sine sweep.
- **Frequency Span**:
  - Full-Range: $15.0\text{ Hz}$ to $22,000.0\text{ Hz}$.
  - Subwoofer: $15.0\text{ Hz}$ to $180.0\text{ Hz}$.
- **Amplitude Envelope**: Exponential decay envelope $-6.0\text{ dB/octave}$ to compensate for equal-energy-per-octave sweep progression.

---

## 2. Processing Contract

```
[ Raw Audio PCM ] ──► [ Deconvolution via FFT ] ──► [ Direct Arrival Detection ]
                             │                                  │
                             ▼                                  ▼
                    [ Room Impulse Response ]         [ Time-of-Flight Delay ]
                             │                                  │
                             ▼                                  ▼
                    [ Causal Windowing ]              [ Physical Distance (m) ]
                             │
                             ▼
                    [ 65536-Point Real FFT ]
                             │
                             ▼
                    [ Microphone Cal Offset ]
                             │
                             ▼
                    [ 1/12-Octave Smoothing ] ──► [ Real Calibrated Curve ]
```

### 2.1 Quality Validation Gates
Before frequency analysis, the engine must validate signal integrity:
1. **Clipping Gate**: $\text{Peak} > -0.5\text{ dBFS} \implies \text{ERROR: CLIPPING\_DETECTED}$.
2. **Signal-to-Noise Ratio Gate**:
   $$\text{SNR}_{\text{dB}} = 20 \log_{10}\left(\frac{\max |h(t)|}{\text{RMS}_{\text{noise}}}\right) < 14.0\text{ dB} \implies \text{ERROR: LOW\_SNR\_NOISY\_ROOM}$$.

### 2.2 Causal Windowing
- Direct sound arrival sample index: $k_{\text{peak}} = \arg\max |h(t)|$.
- Window start: $\max(0, k_{\text{peak}} - 0.010 \cdot f_s)$ (10 ms pre-arrival lead).
- Window end: $\min(N, k_{\text{peak}} + 0.500 \cdot f_s)$ (500 ms post-arrival tail).
- Tapering: Left-half Hann window on pre-arrival, right-half Tukey window ($\alpha = 0.1$) on tail.

### 2.3 Fractional Octave Smoothing
- Smoothing factor: $2^{1/24}$ (1/12-octave bandwidth) across each frequency bin $f_k \ge 20.0\text{ Hz}$.
- Zero synthesized or randomized data points: every plotted value is the arithmetic mean of FFT energy bins within the fractional filter window.

---

## 3. Output Interface

```typescript
export interface RealAcousticAnalysisResult {
  ok: boolean;
  channel: 'Front_L' | 'Front_R' | 'Subwoofer';
  error?: string;
  metrics: {
    peakDbfs: number;
    snrDb: number;
    delayMs: number;
    distanceM: number;
    splEstDb: number;
  };
  impulseResponse: Float32Array; // Windowed RIR
  frequenciesHz: number[];       // e.g., 28 discrete Yamaha or continuous 1/12-octave grid
  magnitudeDb: number[];         // Calibrated, smoothed decibel response
  dominantModes: Array<{
    frequencyHz: number;
    elevationDb: number;
    qEstimate: number;
  }>;
}
```
