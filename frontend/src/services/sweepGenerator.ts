/**
 * Farina Logarithmic Sine Sweep Generator and Theoretical Inverse Filter Engine.
 * Implements Angelo Farina's synchronous log-sweep deconvolution method (AES 2000).
 */

export interface SweepParams {
  fStart: number;
  fEnd: number;
  durationSec: number;
  sampleRate: number;
  fadeLeadMs?: number;
  fadeTailMs?: number;
}

export interface FarinaSweepPair {
  sweep: Float32Array;
  inverseFilter: Float32Array;
  sampleRate: number;
  durationSec: number;
}

export function generateFarinaSweep(params: SweepParams): FarinaSweepPair {
  const { fStart, fEnd, durationSec, sampleRate } = params;
  const fadeLeadMs = params.fadeLeadMs ?? 40;
  const fadeTailMs = params.fadeTailMs ?? 20;

  const numSamples = Math.floor(durationSec * sampleRate);
  const w1 = 2 * Math.PI * fStart;
  const w2 = 2 * Math.PI * fEnd;
  const L = durationSec / Math.log(w2 / w1);

  const sweep = new Float32Array(numSamples);
  const inverseFilter = new Float32Array(numSamples);

  const leadSamples = Math.floor((fadeLeadMs / 1000) * sampleRate);
  const tailSamples = Math.floor((fadeTailMs / 1000) * sampleRate);

  for (let i = 0; i < numSamples; i++) {
    const t = i / sampleRate;
    const phase = w1 * L * (Math.exp(t / L) - 1.0);
    let sample = Math.sin(phase);

    // Fade-in envelope (Hann half-window)
    if (i < leadSamples && leadSamples > 0) {
      sample *= 0.5 * (1.0 - Math.cos((Math.PI * i) / leadSamples));
    }
    // Fade-out envelope (Hann half-window)
    if (i >= numSamples - tailSamples && tailSamples > 0) {
      const tailIdx = i - (numSamples - tailSamples);
      sample *= 0.5 * (1.0 + Math.cos((Math.PI * tailIdx) / tailSamples));
    }

    sweep[i] = sample;
  }

  // Generate Inverse Filter: time-reversed and amplitude-modulated by exp(-t / L)
  // (-6 dB / octave attenuation) to compensate for logarithmic energy distribution
  let normEnergy = 0.0;
  for (let i = 0; i < numSamples; i++) {
    const t = i / sampleRate;
    const modulation = Math.exp(-t / L);
    const revSample = sweep[numSamples - 1 - i] * modulation;
    inverseFilter[i] = revSample;
    normEnergy += revSample * revSample;
  }

  // Energy normalization scale factor for unity impulse response height
  const scale = 1.0 / Math.max(1e-9, Math.sqrt(normEnergy * (sampleRate / (2 * Math.PI * L))));
  for (let i = 0; i < numSamples; i++) {
    inverseFilter[i] *= scale;
  }

  return { sweep, inverseFilter, sampleRate, durationSec };
}

export function createWavBlob(samples: Float32Array, sampleRate = 48000, channel = 1): Blob {
  const numChannels = channel;
  const bitsPerSample = 16;
  const byteRate = (sampleRate * numChannels * bitsPerSample) / 8;
  const blockAlign = (numChannels * bitsPerSample) / 8;
  const dataSize = samples.length * blockAlign;
  const headerSize = 44;
  const totalSize = headerSize + dataSize;

  const buffer = new ArrayBuffer(totalSize);
  const view = new DataView(buffer);

  // RIFF Chunk
  view.setUint32(0, 0x52494646, false); // "RIFF"
  view.setUint32(4, totalSize - 8, true);
  view.setUint32(8, 0x57415645, false); // "WAVE"

  // fmt Sub-chunk
  view.setUint32(12, 0x666d7420, false); // "fmt "
  view.setUint32(16, 16, true);          // SubChunk1Size (16 for PCM)
  view.setUint16(20, 1, true);           // AudioFormat (1 for PCM)
  view.setUint16(22, numChannels, true);
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, byteRate, true);
  view.setUint16(32, blockAlign, true);
  view.setUint16(34, bitsPerSample, true);

  // data Sub-chunk
  view.setUint32(36, 0x64617461, false); // "data"
  view.setUint32(40, dataSize, true);

  let offset = 44;
  for (let i = 0; i < samples.length; i++) {
    const s = Math.max(-1.0, Math.min(1.0, samples[i]));
    const pcm = s < 0 ? s * 0x8000 : s * 0x7fff;
    view.setInt16(offset, pcm, true);
    offset += 2;
  }

  return new Blob([buffer], { type: 'audio/wav' });
}
