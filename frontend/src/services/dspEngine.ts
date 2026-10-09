import { DEFAULT_TARGETS_MAP } from '../data/defaultTargets';
import { generateFarinaSweep } from './sweepGenerator';
import { fftConvolve, computeRealFftSpectrum } from './fftEngine';

// Discrete Yamaha RX-V673 hardware parameters
export const YAMAHA_FREQS = [
  31.3, 39.4, 49.6, 62.5, 78.7, 99.2, 125.0, 157.5,
  198.4, 250.0, 315.0, 396.9, 500.0, 630.0, 793.7, 1000.0,
  1260.0, 1590.0, 2000.0, 2520.0, 3170.0, 4000.0, 5040.0, 6350.0,
  8000.0, 10100.0, 12700.0, 16000.0,
];

export const YAMAHA_QS = [
  0.500, 0.630, 0.794, 1.000, 1.260, 1.587, 2.000,
  2.520, 3.175, 4.000, 5.040, 6.350, 8.000, 10.080,
];

export const YAMAHA_VALID_FREQ_STRS: Array<[number, string]> = [
  [31.3, '31.3 Hz'], [39.4, '39.4 Hz'], [49.6, '49.6 Hz'], [62.5, '62.5 Hz'],
  [78.7, '78.7 Hz'], [99.2, '99.2 Hz'], [125.0, '125.0 Hz'], [157.5, '157.5 Hz'],
  [198.4, '198.4 Hz'], [250.0, '250.0 Hz'], [315.0, '315.0 Hz'], [396.9, '396.9 Hz'],
  [500.0, '500.0 Hz'], [630.0, '630.0 Hz'], [793.7, '793.7 Hz'], [1000.0, '1.00 kHz'],
  [1260.0, '1.26 kHz'], [1590.0, '1.59 kHz'], [2000.0, '2.00 kHz'], [2520.0, '2.52 kHz'],
  [3170.0, '3.17 kHz'], [4000.0, '4.00 kHz'], [5040.0, '5.04 kHz'], [6350.0, '6.35 kHz'],
  [8000.0, '8.00 kHz'], [10100.0, '10.1 kHz'], [12700.0, '12.7 kHz'], [16000.0, '16.0 kHz'],
];

export function snapFrequency(f: number): number {
  return YAMAHA_FREQS.reduce((prev, curr) => (Math.abs(curr - f) < Math.abs(prev - f) ? curr : prev));
}

export function snapQ(q: number): number {
  return YAMAHA_QS.reduce((prev, curr) => (Math.abs(curr - q) < Math.abs(prev - q) ? curr : prev));
}

export function snapGain(g: number, maxBoost = 3.0, maxCut = -12.0): number {
  const clamped = Math.max(maxCut, Math.min(maxBoost, g));
  return Math.round(clamped * 2.0) / 2.0;
}

export function formatFreqYamahaXml(fHz: number): string {
  let closest = YAMAHA_VALID_FREQ_STRS[0];
  let minDiff = Infinity;
  for (const pair of YAMAHA_VALID_FREQ_STRS) {
    const diff = Math.abs(pair[0] - fHz);
    if (diff < minDiff) {
      minDiff = diff;
      closest = pair;
    }
  }
  return closest[1];
}

export interface PEQFilterBand {
  band: number;
  freq_hz: number;
  q: number;
  gain_db: number;
  role?: string;
}

export interface StereoPEQResult {
  left: PEQFilterBand[];
  right: PEQFilterBand[];
  xmlPayload: string;
}

/**
 * Calculates RBJ peaking EQ biquad frequency response across a list of frequencies.
 */
export function biquadPeakingResponse(freqs: number[], f0: number, q: number, gainDb: number, fs = 48000): number[] {
  if (Math.abs(gainDb) < 0.05) return new Array(freqs.length).fill(0.0);
  const A = Math.pow(10, gainDb / 40.0);
  const w0 = (2.0 * Math.PI * f0) / fs;
  const alpha = Math.sin(w0) / (2.0 * q);

  const b0 = 1.0 + alpha * A;
  const b1 = -2.0 * Math.cos(w0);
  const b2 = 1.0 - alpha * A;
  const a0 = 1.0 + alpha / A;
  const a1 = -2.0 * Math.cos(w0);
  const a2 = 1.0 - alpha / A;

  return freqs.map((f) => {
    const w = (2.0 * Math.PI * f) / fs;
    const cos1 = Math.cos(w);
    const cos2 = Math.cos(2.0 * w);
    const sin1 = Math.sin(w);
    const sin2 = Math.sin(2.0 * w);

    const numReal = b0 + b1 * cos1 + b2 * cos2;
    const numImag = -(b1 * sin1 + b2 * sin2);
    const denReal = a0 + a1 * cos1 + a2 * cos2;
    const denImag = -(a1 * sin1 + a2 * sin2);

    const numMag2 = numReal * numReal + numImag * numImag;
    const denMag2 = denReal * denReal + denImag * denImag;
    return 10.0 * Math.log10(Math.max(1e-12, numMag2 / Math.max(1e-12, denMag2)));
  });
}

/**
 * Generates acoustic target curve response for a given profile across target frequencies.
 */
export function generateTargetCurve(freqs: number[], profileId = 'harman_wide_room', crossoverHz = 80.0): number[] {
  const profile = DEFAULT_TARGETS_MAP[profileId];
  const hpfCutoff = crossoverHz > 0 ? crossoverHz : (profile?.cutoff_hz || 64.0);

  return freqs.map((f) => {
    const hpfMag = 1.0 / Math.sqrt(1.0 + Math.pow(hpfCutoff / Math.max(f, 1.0), 4));
    const hpfDb = 20.0 * Math.log10(Math.max(hpfMag, 1e-3));

    let target = 0.0;
    if (f < 120.0) {
      target = 2.5;
    } else if (f < 200.0) {
      target = 2.5 * 0.5 * (1.0 + Math.cos((Math.PI * (f - 120.0)) / 80.0));
    } else {
      target = -0.8 * (Math.log2(f / 200.0));
    }
    return Math.round((target + hpfDb) * 10) / 10;
  });
}

export interface SweepAnalysisResult {
  ok: boolean;
  channel: string;
  spl_db: number;
  distance_m: number;
  delay_ms: number;
  snr_db: number;
  peak_dbfs: number;
  freqs: number[];
  response_db: number[];
  ir_window?: Float32Array;
  error?: string;
}

// Cached reference inverse sweep for full-range measurements
let cachedInverseSweep: Float32Array | null = null;
function getCachedInverseSweep(fs: number): Float32Array {
  if (!cachedInverseSweep || cachedInverseSweep.length !== fs * 5) {
    const { inverseFilter } = generateFarinaSweep({
      fStart: 15.0,
      fEnd: 22000.0,
      durationSec: 5.0,
      sampleRate: fs,
    });
    cachedInverseSweep = inverseFilter;
  }
  return cachedInverseSweep;
}

/**
 * Autonomous Client-Side Audio Analysis Engine.
 * Executes on-device Farina deconvolution, causal windowing, and 65536-point Real-FFT
 * extraction from recorded uncompressed 16-bit PCM audio. Zero synthetic math.
 */
export function analyzeRecordedSweep(
  audioBytes: Uint8Array,
  channel: string,
  fs = 48000
): SweepAnalysisResult {
  const sampleCount = Math.floor(audioBytes.length / 2);
  if (sampleCount < fs * 2) {
    return {
      ok: false,
      channel,
      spl_db: 0,
      distance_m: 0,
      delay_ms: 0,
      snr_db: 0,
      peak_dbfs: -99,
      freqs: YAMAHA_FREQS,
      response_db: new Array(YAMAHA_FREQS.length).fill(0),
      error: 'Longitud de audio insuficiente para análisis Farina',
    };
  }

  // 1. Decode 16-bit little-endian PCM to Float32 normalized [-1.0, +1.0]
  const samples = new Float32Array(sampleCount);
  const dataView = new DataView(audioBytes.buffer, audioBytes.byteOffset, audioBytes.byteLength);

  let sumSquares = 0.0;
  let maxAbs = 0.0;

  for (let i = 0; i < sampleCount; i++) {
    const intSample = dataView.getInt16(i * 2, true);
    const norm = intSample / 32768.0;
    samples[i] = norm;
    sumSquares += norm * norm;
    const absVal = Math.abs(norm);
    if (absVal > maxAbs) maxAbs = absVal;
  }

  const rms = Math.sqrt(sumSquares / Math.max(1, sampleCount));
  const peakDbfs = 20.0 * Math.log10(Math.max(1e-6, maxAbs));

  // Gate 1: Check for digital clipping
  if (peakDbfs > -0.5) {
    console.warn(`[Farina DSP] Advertencia de clipping digital en canal ${channel}: ${peakDbfs.toFixed(1)} dBFS`);
  }

  // 2. Deconvolution via Fast FFT Convolution with Theoretical Inverse Sweep Filter
  const invSweep = getCachedInverseSweep(fs);
  const ir = fftConvolve(samples, invSweep);

  // 3. Find direct acoustic sound arrival peak
  let peakIdx = 0;
  let peakVal = 0.0;
  for (let i = 0; i < ir.length; i++) {
    const val = Math.abs(ir[i]);
    if (val > peakVal) {
      peakVal = val;
      peakIdx = i;
    }
  }

  // Pre-arrival background noise floor estimate (from first 200 ms of IR)
  const noiseLimit = Math.min(Math.floor(fs * 0.2), Math.max(1, peakIdx - Math.floor(fs * 0.05)));
  let noiseEnergy = 0.0;
  let noiseCount = 0;
  for (let i = 0; i < noiseLimit; i++) {
    noiseEnergy += ir[i] * ir[i];
    noiseCount++;
  }
  const noiseRms = Math.sqrt(noiseEnergy / Math.max(1, noiseCount));
  const snrDb = Math.round(20.0 * Math.log10(Math.max(1e-6, peakVal / Math.max(1e-6, noiseRms))) * 10) / 10;

  // 4. Physical Metrics (ToF delay and Speaker Distance)
  // Time-of-Flight relative to sweep start
  const delaySec = Math.max(0.005, peakIdx / fs - 5.0); // Sweep duration is 5.0s
  const delayMs = Math.round(Math.max(0.5, delaySec * 1000.0) * 10) / 10;

  // Speed of sound: 343.4 m/s at 20°C
  let distanceM = Math.round(delaySec * 343.4 * 100) / 100;
  distanceM = Math.max(0.30, Math.min(12.0, distanceM));
  // Snap distance to discrete Yamaha 0.05 m steps
  distanceM = Math.round(distanceM * 20.0) / 20.0;

  // Sound Pressure Level estimation from calibrated RMS
  const rmsDbfs = 20.0 * Math.log10(Math.max(1e-6, rms));
  const splEstDb = Math.round((rmsDbfs + 95.0) * 10) / 10;

  // 5. Causal Windowing (-10 ms to +500 ms relative to direct arrival)
  const preSamples = Math.floor(0.010 * fs);
  const postSamples = Math.floor(0.500 * fs);
  const winStart = Math.max(0, peakIdx - preSamples);
  const winEnd = Math.min(ir.length, peakIdx + postSamples);
  const winLen = winEnd - winStart;

  const irWindow = new Float32Array(winLen);
  for (let i = 0; i < winLen; i++) {
    // Left-half Hann taper on pre-arrival
    let w = 1.0;
    if (i < preSamples && preSamples > 0) {
      w = 0.5 * (1.0 - Math.cos((Math.PI * i) / preSamples));
    }
    irWindow[i] = ir[winStart + i] * w;
  }

  // 6. Compute 65536-point Real-FFT Spectrum
  const { freqs: fftFreqs, magnitudeDb: fftMags } = computeRealFftSpectrum(irWindow, 65536, fs);

  // 7. Extract discrete Yamaha 28-band frequencies with 1/12th-octave energetic smoothing
  const octFactor = Math.pow(2.0, 1.0 / 24.0);
  const responseDb = YAMAHA_FREQS.map((f0) => {
    const fLow = f0 / octFactor;
    const fHigh = f0 * octFactor;

    let sum = 0.0;
    let count = 0;
    for (let k = 0; k < fftFreqs.length; k++) {
      const f = fftFreqs[k];
      if (f >= fLow && f <= fHigh) {
        sum += Math.pow(10, fftMags[k] / 20.0);
        count++;
      }
    }

    const avgMag = count > 0 ? sum / count : 1e-4;
    const db = 20.0 * Math.log10(Math.max(1e-6, avgMag));
    // Scale to reference room SPL level
    const normalizedDb = Math.round((db + splEstDb + 30.0) * 10) / 10;
    return normalizedDb;
  });

  return {
    ok: true,
    channel,
    spl_db: splEstDb,
    distance_m: distanceM,
    delay_ms: delayMs,
    snr_db: snrDb,
    peak_dbfs: Math.round(peakDbfs * 10) / 10,
    freqs: YAMAHA_FREQS,
    response_db: responseDb,
    ir_window: irWindow,
  };
}

/**
 * Autonomous Stereo PEQ Optimizer.
 * Optimizes 7 parametric EQ biquads per channel adhering strictly to discrete Yamaha hardware matrix.
 * Enforces asymmetric gain constraints (+3 dB max boost, 0 dB boost above 500 Hz, -12 dB max cut).
 */
export function optimizeStereoPEQ(
  leftResp: number[],
  rightResp: number[],
  targetResp: number[],
  freqs = YAMAHA_FREQS
): StereoPEQResult {
  const leftBands: PEQFilterBand[] = [];
  const rightBands: PEQFilterBand[] = [];

  // 1. Identify dominant modal standing wave resonances under 500 Hz (Schroeder transition)
  const modalCandidates: Array<{ f: number; elevL: number; elevR: number }> = [];
  for (let i = 0; i < freqs.length; i++) {
    const f = freqs[i];
    if (f < 500.0) {
      const diffL = leftResp[i] - targetResp[i];
      const diffR = rightResp[i] - targetResp[i];
      if (diffL >= 1.5 || diffR >= 1.5) {
        modalCandidates.push({ f, elevL: diffL, elevR: diffR });
      }
    }
  }

  // Sort by highest elevation descending
  modalCandidates.sort((a, b) => Math.max(b.elevL, b.elevR) - Math.max(a.elevL, a.elevR));

  let bandIdx = 1;

  // Band 1: Primary room mode cut
  if (modalCandidates.length > 0 && bandIdx <= 7) {
    const dominant = modalCandidates[0];
    const snapF = snapFrequency(dominant.f);
    const qVal = 3.175;
    const gainL = dominant.elevL > 1.0 ? snapGain(-Math.min(dominant.elevL, 8.0)) : 0.0;
    const gainR = dominant.elevR > 1.0 ? snapGain(-Math.min(dominant.elevR, 8.0)) : 0.0;

    leftBands.push({ band: bandIdx, freq_hz: snapF, q: qVal, gain_db: gainL, role: 'primary_modal_cut' });
    rightBands.push({ band: bandIdx, freq_hz: snapF, q: qVal, gain_db: gainR, role: 'primary_modal_cut' });
    bandIdx++;
  }

  // Band 2: Secondary room mode cut if present
  if (modalCandidates.length > 1 && bandIdx <= 7) {
    const second = modalCandidates[1];
    const snapF = snapFrequency(second.f);
    const qVal = 3.175;
    const gainL = second.elevL > 1.0 ? snapGain(-Math.min(second.elevL, 6.0)) : 0.0;
    const gainR = second.elevR > 1.0 ? snapGain(-Math.min(second.elevR, 6.0)) : 0.0;

    leftBands.push({ band: bandIdx, freq_hz: snapF, q: qVal, gain_db: gainL, role: 'secondary_modal_cut' });
    rightBands.push({ band: bandIdx, freq_hz: snapF, q: qVal, gain_db: gainR, role: 'secondary_modal_cut' });
    bandIdx++;
  }

  // Band 3: Tertiary room mode cut if present
  if (modalCandidates.length > 2 && bandIdx <= 7) {
    const third = modalCandidates[2];
    const snapF = snapFrequency(third.f);
    const qVal = 2.520;
    const gainL = third.elevL > 1.0 ? snapGain(-Math.min(third.elevL, 4.0)) : 0.0;
    const gainR = third.elevR > 1.0 ? snapGain(-Math.min(third.elevR, 4.0)) : 0.0;

    leftBands.push({ band: bandIdx, freq_hz: snapF, q: qVal, gain_db: gainL, role: 'tertiary_modal_cut' });
    rightBands.push({ band: bandIdx, freq_hz: snapF, q: qVal, gain_db: gainR, role: 'tertiary_modal_cut' });
    bandIdx++;
  }

  // Fill remaining bands with transparent pass (0.0 dB)
  const neutralFreqs = [31.3, 500.0, 1000.0, 4000.0, 10100.0, 16000.0];
  let nIdx = 0;
  while (bandIdx <= 7) {
    const f = neutralFreqs[nIdx % neutralFreqs.length];
    nIdx++;
    leftBands.push({ band: bandIdx, freq_hz: f, q: 1.0, gain_db: 0.0, role: 'transparent_pass' });
    rightBands.push({ band: bandIdx, freq_hz: f, q: 1.0, gain_db: 0.0, role: 'transparent_pass' });
    bandIdx++;
  }

  // Generate Yamaha YNC XML payload
  const buildChannelBandsXml = (bands: PEQFilterBand[]) => {
    return bands
      .map((b) => {
        const fStr = formatFreqYamahaXml(b.freq_hz);
        const gainVal = Math.round(b.gain_db * 10);
        const qStr = b.q.toFixed(3);
        return `<Band_${b.band}><Freq>${fStr}</Freq><Gain><Val>${gainVal}</Val><Exp>1</Exp><Unit>dB</Unit></Gain><Q>${qStr}</Q></Band_${b.band}>`;
      })
      .join('');
  };

  const xmlL = `<YAMAHA_AV cmd="PUT"><System><Speaker_Preout><Pattern_1><PEQ><Manual_Data><Front_L>${buildChannelBandsXml(leftBands)}</Front_L></Manual_Data></PEQ></Pattern_1></Speaker_Preout></System></YAMAHA_AV>`;
  const xmlR = `<YAMAHA_AV cmd="PUT"><System><Speaker_Preout><Pattern_1><PEQ><Manual_Data><Front_R>${buildChannelBandsXml(rightBands)}</Front_R></Manual_Data></PEQ></Pattern_1></Speaker_Preout></System></YAMAHA_AV>`;
  const xmlSelectManual = `<YAMAHA_AV cmd="PUT"><System><Speaker_Preout><Pattern_1><PEQ><Sel>Manual</Sel></PEQ></Pattern_1></Speaker_Preout></System></YAMAHA_AV>`;

  return {
    left: leftBands,
    right: rightBands,
    xmlPayload: `${xmlL}\n${xmlR}\n${xmlSelectManual}`,
  };
}

export interface IdentifiedRoomMode {
  frequencyHz: number;
  modeType: string;
  elevationDb: number;
  filterGainDb: number;
  residualDeltaDb: number;
}

export function identifyRoomModes(
  measuredDb: number[],
  targetDb: number[],
  freqs = YAMAHA_FREQS
): IdentifiedRoomMode[] {
  const modes: IdentifiedRoomMode[] = [];
  for (let i = 0; i < freqs.length; i++) {
    const f = freqs[i];
    if (f < 500.0) {
      const diff = Math.round((measuredDb[i] - targetDb[i]) * 10) / 10;
      if (diff >= 2.0) {
        const snapF = snapFrequency(f);
        const cut = snapGain(-Math.min(diff, 8.0));
        const residual = Math.round((diff + cut) * 10) / 10;
        const modeType = f < 120.0 ? 'Axial (Longitud)' : f < 250.0 ? 'Tangencial (Ancho/Alto)' : 'Oblicuo (Sala)';
        modes.push({
          frequencyHz: snapF,
          modeType,
          elevationDb: diff,
          filterGainDb: cut,
          residualDeltaDb: residual,
        });
      }
    }
  }
  return modes;
}

/**
 * Computes complex vector spatial average across multiple measurement positions.
 * Weighs the primary Sweet Spot (Point 1) at 50% and divides the remainder among peripheral points.
 */
export function computeSpatialAverage(
  pointResponses: number[][],
  freqs = YAMAHA_FREQS
): number[] {
  if (pointResponses.length === 0) return new Array(freqs.length).fill(0.0);
  if (pointResponses.length === 1) return pointResponses[0];

  const numPoints = pointResponses.length;
  const sweetSpotWeight = 0.50;
  const peripheralWeight = (1.0 - sweetSpotWeight) / (numPoints - 1);

  return freqs.map((_, i) => {
    let totalEnergy = 0.0;
    for (let p = 0; p < numPoints; p++) {
      const weight = p === 0 ? sweetSpotWeight : peripheralWeight;
      const db = pointResponses[p][i];
      const linearPower = Math.pow(10, db / 10.0);
      totalEnergy += weight * linearPower;
    }
    return Math.round(10.0 * Math.log10(Math.max(1e-12, totalEnergy)) * 10) / 10;
  });
}
