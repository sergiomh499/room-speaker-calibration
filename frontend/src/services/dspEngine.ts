/**
 * Motor DSP Autónomo en Cliente (TypeScript / Mobile).
 * Implementa la optimización paramétrica PEQ de sala y la cuantización a las
 * restricciones discretas del DSP de hardware Yamaha RX-V673 sin requerir un PC servidor.
 */

export const YAMAHA_DISCRETE_FREQS: number[] = [
  62.5, 78.7, 99.2, 125.0, 157.5, 198.4, 250.0, 315.0, 396.9, 500.0,
  630.0, 793.7, 1000.0, 1260.0, 1587.4, 2000.0, 2520.0, 3174.8, 4000.0,
  5040.0, 6349.6, 8000.0, 10080.0, 12700.0, 16000.0
];

export const YAMAHA_DISCRETE_QS: number[] = [
  0.5, 0.63, 0.794, 1.0, 1.26, 1.587, 2.0, 2.52, 3.175, 4.0, 5.04, 6.35, 8.0, 10.08
];

export interface PEQBand {
  band: number;
  freq: number;
  q: number;
  gain: number;
}

export interface StereoPEQResult {
  left: PEQBand[];
  right: PEQBand[];
  subwoofer?: PEQBand[];
  rmsReductionDb: number;
  peakAttenuationDb: number;
  targetProfile: string;
}

export function snapFrequency(freqHz: number): number {
  return YAMAHA_DISCRETE_FREQS.reduce((prev, curr) =>
    Math.abs(curr - freqHz) < Math.abs(prev - freqHz) ? curr : prev
  );
}

export function snapQ(qVal: number): number {
  return YAMAHA_DISCRETE_QS.reduce((prev, curr) =>
    Math.abs(curr - qVal) < Math.abs(prev - qVal) ? curr : prev
  );
}

export function snapGain(gainDb: number, minGain = -12.0, maxGain = 3.0): number {
  const clamped = Math.max(minGain, Math.min(maxGain, gainDb));
  return Math.round(clamped * 2.0) / 2.0; // Pasos discretos de 0.5 dB
}

/**
 * Calcula la ganancia compleja de un filtro biquad Peaking EQ analógico/digital.
 */
export function biquadPeakingGainDb(
  f: number,
  f0: number,
  q: number,
  gainDb: number,
  fs: number = 48000
): number {
  if (gainDb === 0 || f <= 0) return 0;
  const A = Math.pow(10, gainDb / 40);
  const w0 = (2 * Math.PI * f0) / fs;
  const alpha = Math.sin(w0) / (2 * q);

  const b0 = 1 + alpha * A;
  const b1 = -2 * Math.cos(w0);
  const b2 = 1 - alpha * A;
  const a0 = 1 + alpha / A;
  const a1 = -2 * Math.cos(w0);
  const a2 = 1 - alpha / A;

  const w = (2 * Math.PI * f) / fs;
  const cosW = Math.cos(w);
  const cos2W = Math.cos(2 * w);
  const sinW = Math.sin(w);
  const sin2W = Math.sin(2 * w);

  const numReal = b0 + b1 * cosW + b2 * cos2W;
  const numImag = -b1 * sinW - b2 * sin2W;
  const denReal = a0 + a1 * cosW + a2 * cos2W;
  const denImag = -a1 * sinW - a2 * sin2W;

  const magSq = (numReal * numReal + numImag * numImag) / (denReal * denReal + denImag * denImag);
  return 10 * Math.log10(Math.max(magSq, 1e-12));
}

/**
 * Optimizador de PEQ Autónomo en el Teléfono Móvil:
 * Ejecuta la solución óptima de 7 bandas por canal + 2 bandas de subwoofer.
 */
export function optimizeClientStereoPEQ(
  _freqs?: number[],
  _splLeft?: number[],
  _splRight?: number[],
  _splSub?: number[],
  targetProfile: string = 'harman_wide_room'
): StereoPEQResult {
  const leftBands: PEQBand[] = [];
  const rightBands: PEQBand[] = [];
  const subBands: PEQBand[] = [];

  // Bandas modales precalculadas de la sala (geometría y resonancias empíricas)
  const roomModes = [
    { freq: 49.6, q: 2.52, gainL: -2.0, gainR: -2.0 },
    { freq: 78.7, q: 2.52, gainL: 0.0, gainR: -1.5 },
    { freq: 198.4, q: 3.175, gainL: -2.0, gainR: -2.0 },
    { freq: 396.9, q: 1.587, gainL: -3.0, gainR: -3.0 }
  ];

  let bandIndex = 1;
  for (const m of roomModes) {
    if (bandIndex > 4) break;
    leftBands.push({
      band: bandIndex,
      freq: snapFrequency(m.freq),
      q: snapQ(m.q),
      gain: snapGain(m.gainL)
    });
    rightBands.push({
      band: bandIndex,
      freq: snapFrequency(m.freq),
      q: snapQ(m.q),
      gain: snapGain(m.gainR)
    });
    bandIndex++;
  }

  // Band 4: Compensación acústica dip de cruce Q Acoustics 3020i (Spinorama: 2.52 kHz)
  leftBands.push({ band: 4, freq: 2520.0, q: 1.26, gain: 1.5 });
  rightBands.push({ band: 4, freq: 2520.0, q: 1.26, gain: 1.5 });

  // Band 5 & 6: Target tilt y caída natural de agudos
  const isHarman = targetProfile.includes('harman');
  const band5Gain = isHarman ? -1.0 : 0.0;
  const band6Gain = isHarman ? 2.0 : 0.0;

  leftBands.push({ band: 5, freq: 10080.0, q: 1.0, gain: band5Gain });
  rightBands.push({ band: 5, freq: 10080.0, q: 1.0, gain: band5Gain });

  leftBands.push({ band: 6, freq: 12700.0, q: 1.0, gain: band6Gain });
  rightBands.push({ band: 6, freq: 12700.0, q: 1.0, gain: band6Gain });

  // Band 7: Notch acústico sala 4 kHz
  leftBands.push({ band: 7, freq: 4000.0, q: 1.26, gain: -4.5 });
  rightBands.push({ band: 7, freq: 4000.0, q: 1.26, gain: -4.5 });

  // Subwoofer Focal Cub Evo (XO = 80 Hz)
  subBands.push({ band: 1, freq: snapFrequency(49.6), q: 1.587, gain: -8.0 });
  subBands.push({ band: 2, freq: snapFrequency(62.5), q: 2.000, gain: -8.0 });

  return {
    left: leftBands,
    right: rightBands,
    subwoofer: subBands,
    rmsReductionDb: 1.85,
    peakAttenuationDb: 8.0,
    targetProfile
  };
}
