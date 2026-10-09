import { describe, it, expect } from 'bun:test';
import {
  snapFrequency,
  snapQ,
  snapGain,
  formatFreqYamahaXml,
  biquadPeakingResponse,
  generateTargetCurve,
  optimizeStereoPEQ,
  analyzeRecordedSweep,
  YAMAHA_FREQS,
  YAMAHA_QS,
} from '../dspEngine';
import { generateFarinaSweep } from '../sweepGenerator';
import { FftEngine, fftConvolve } from '../fftEngine';

describe('Discrete Yamaha Hardware Quantizers', () => {
  it('snaps arbitrary frequencies to discrete YAMAHA_FREQS', () => {
    expect(snapFrequency(95.0)).toBe(99.2);
    expect(snapFrequency(1050.0)).toBe(1000.0);
    expect(snapFrequency(2400.0)).toBe(2520.0);
    expect(YAMAHA_FREQS).toContain(snapFrequency(55.0));
  });

  it('snaps quality factor Q to discrete YAMAHA_QS', () => {
    expect(snapQ(1.1)).toBe(1.0);
    expect(snapQ(3.0)).toBe(3.175);
    expect(snapQ(9.5)).toBe(10.08);
    expect(YAMAHA_QS).toContain(snapQ(0.7));
  });

  it('clamps and snaps gains to 0.5 dB increments within [-12.0, +3.0] dB', () => {
    expect(snapGain(4.8)).toBe(3.0);   // Max boost +3.0 dB
    expect(snapGain(-15.2)).toBe(-12.0); // Max cut -12.0 dB
    expect(snapGain(1.23)).toBe(1.0);
    expect(snapGain(-2.67)).toBe(-2.5);
  });

  it('formats frequencies into valid Yamaha XML string representations', () => {
    expect(formatFreqYamahaXml(99.2)).toBe('99.2 Hz');
    expect(formatFreqYamahaXml(1000.0)).toBe('1.00 kHz');
    expect(formatFreqYamahaXml(2520.0)).toBe('2.52 kHz');
  });

  it('calculates peaking biquad transfer response correctly', () => {
    const freqs = [100.0, 1000.0, 10000.0];
    const response = biquadPeakingResponse(freqs, 1000.0, 2.0, 3.0);
    expect(response.length).toBe(3);
    expect(Math.abs(response[1] - 3.0)).toBeLessThan(0.1);
    expect(Math.abs(response[0])).toBeLessThan(0.5);
  });
});

describe('Farina Sweep & FFT Engine', () => {
  it('generates a deterministic 48 kHz logarithmic sine sweep and inverse filter', () => {
    const fs = 48000;
    const { sweep, inverseFilter } = generateFarinaSweep({
      fStart: 20.0,
      fEnd: 20000.0,
      durationSec: 1.0,
      sampleRate: fs,
    });

    expect(sweep.length).toBe(fs);
    expect(inverseFilter.length).toBe(fs);

    // Verify peak amplitude bounded in [-1.0, 1.0]
    let maxSweep = 0;
    for (let i = 0; i < sweep.length; i++) {
      const abs = Math.abs(sweep[i]);
      if (abs > maxSweep) maxSweep = abs;
    }
    expect(maxSweep).toBeGreaterThan(0.9);
    expect(maxSweep).toBeLessThanOrEqual(1.0);
  });

  it('computes FFT and verifies energy conservation on Dirac delta impulse', () => {
    const size = 1024;
    const engine = new FftEngine(size);
    const real = new Float32Array(size);
    const imag = new Float32Array(size);
    real[0] = 1.0; // Delta impulse

    engine.transform(real, imag, false);

    // Flat magnitude spectrum = 1.0 across all frequency bins
    for (let i = 0; i < size; i++) {
      const mag = Math.sqrt(real[i] * real[i] + imag[i] * imag[i]);
      expect(Math.abs(mag - 1.0)).toBeLessThan(1e-4);
    }

    // Inverse transform restores original impulse
    engine.transform(real, imag, true);
    expect(Math.abs(real[0] - 1.0)).toBeLessThan(1e-4);
    for (let i = 1; i < size; i++) {
      expect(Math.abs(real[i])).toBeLessThan(1e-4);
    }
  });

  it('performs FFT convolution matching expected output length', () => {
    const x = new Float32Array([1, 2, 3]);
    const y = new Float32Array([4, 5]);
    const conv = fftConvolve(x, y);

    expect(conv.length).toBe(4);
    // [1*4, 1*5 + 2*4, 2*5 + 3*4, 3*5] = [4, 13, 22, 15]
    expect(Math.abs(conv[0] - 4.0)).toBeLessThan(1e-3);
    expect(Math.abs(conv[1] - 13.0)).toBeLessThan(1e-3);
    expect(Math.abs(conv[2] - 22.0)).toBeLessThan(1e-3);
    expect(Math.abs(conv[3] - 15.0)).toBeLessThan(1e-3);
  });
});

describe('On-Device Sweep Analysis & PEQ Optimizer', () => {
  it('analyzes recorded PCM sweep and returns real metrics without NaN', () => {
    const fs = 48000;
    const numSamples = fs * 3; // 3 seconds
    const pcmBytes = new Uint8Array(numSamples * 2);
    const view = new DataView(pcmBytes.buffer);

    // Synthetic acoustic pulse at sample 48000 (1.0 second delay)
    for (let i = 0; i < numSamples; i++) {
      let val = 0;
      if (i >= 48000 && i < 48200) {
        val = Math.sin((2 * Math.PI * (i - 48000)) / 20) * 16000;
      }
      view.setInt16(i * 2, Math.round(val), true);
    }

    const result = analyzeRecordedSweep(pcmBytes, 'Front_L', fs);
    expect(result.ok).toBe(true);
    expect(result.channel).toBe('Front_L');
    expect(result.freqs.length).toBe(YAMAHA_FREQS.length);
    expect(result.response_db.length).toBe(YAMAHA_FREQS.length);
    for (const val of result.response_db) {
      expect(isNaN(val)).toBe(false);
    }
  });

  it('optimizes exactly 7 PEQ bands per channel with discrete parameter constraints', () => {
    const freqs = YAMAHA_FREQS;
    const target = generateTargetCurve(freqs, 'harman_wide_room');
    // Elevated room mode at 99.2 Hz (+8 dB)
    const measuredL = target.map((t, idx) => (freqs[idx] === 99.2 ? t + 8.0 : t));
    const measuredR = target.map((t, idx) => (freqs[idx] === 99.2 ? t + 7.5 : t));

    const result = optimizeStereoPEQ(measuredL, measuredR, target, freqs);

    expect(result.left.length).toBe(7);
    expect(result.right.length).toBe(7);

    // Band 1 should cut the dominant 99.2 Hz mode
    expect(result.left[0].freq_hz).toBe(99.2);
    expect(result.left[0].gain_db).toBeLessThan(0);
    expect(result.left[0].gain_db).toBeGreaterThanOrEqual(-12.0);

    // Validate discrete Yamaha frequency and Q adherence across all bands
    for (const band of result.left) {
      expect(YAMAHA_FREQS).toContain(band.freq_hz);
      expect(YAMAHA_QS).toContain(band.q);
      expect(band.gain_db).toBeGreaterThanOrEqual(-12.0);
      expect(band.gain_db).toBeLessThanOrEqual(3.0);
    }

    expect(result.xmlPayload).toContain('<Front_L>');
    expect(result.xmlPayload).toContain('<Front_R>');
    expect(result.xmlPayload).toContain('<Sel>Manual</Sel>');
  });
});
