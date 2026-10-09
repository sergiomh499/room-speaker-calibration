/**
 * High-Performance Radix-2 Fast Fourier Transform and Convolution Engine.
 * Optimized for Float32Array in client-side WebViews.
 */

export class FftEngine {
  private n: number;
  private cosTable: Float32Array;
  private sinTable: Float32Array;
  private bitRev: Uint32Array;

  constructor(n: number) {
    if ((n & (n - 1)) !== 0 || n <= 0) {
      throw new Error(`FFT size must be a positive power of 2, received ${n}`);
    }
    this.n = n;
    this.cosTable = new Float32Array(n / 2);
    this.sinTable = new Float32Array(n / 2);
    for (let i = 0; i < n / 2; i++) {
      const angle = (-2.0 * Math.PI * i) / n;
      this.cosTable[i] = Math.cos(angle);
      this.sinTable[i] = Math.sin(angle);
    }

    this.bitRev = new Uint32Array(n);
    let j = 0;
    for (let i = 0; i < n; i++) {
      this.bitRev[i] = j;
      let bit = n >> 1;
      while (bit <= j && bit > 0) {
        j -= bit;
        bit >>= 1;
      }
      j += bit;
    }
  }

  /**
   * In-place Radix-2 Cooley-Tukey Complex FFT.
   * Transforms real and imaginary Float32Array buffers in-place.
   */
  transform(real: Float32Array, imag: Float32Array, inverse = false): void {
    const n = this.n;

    // Bit-reversal permutation
    for (let i = 0; i < n; i++) {
      const rev = this.bitRev[i];
      if (i < rev) {
        const tr = real[i];
        real[i] = real[rev];
        real[rev] = tr;

        const ti = imag[i];
        imag[i] = imag[rev];
        imag[rev] = ti;
      }
    }

    // Cooley-Tukey butterfly stages
    for (let len = 2; len <= n; len <<= 1) {
      const halfLen = len >> 1;
      const step = n / len;
      for (let i = 0; i < n; i += len) {
        for (let k = 0; k < halfLen; k++) {
          const idx = k * step;
          const c = this.cosTable[idx];
          const s = inverse ? -this.sinTable[idx] : this.sinTable[idx];

          const pos1 = i + k;
          const pos2 = pos1 + halfLen;

          const uR = real[pos1];
          const uI = imag[pos1];
          const vR = real[pos2] * c - imag[pos2] * s;
          const vI = real[pos2] * s + imag[pos2] * c;

          real[pos1] = uR + vR;
          imag[pos1] = uI + vI;
          real[pos2] = uR - vR;
          imag[pos2] = uI - vI;
        }
      }
    }

    if (inverse) {
      const invN = 1.0 / n;
      for (let i = 0; i < n; i++) {
        real[i] *= invN;
        imag[i] *= invN;
      }
    }
  }
}

/**
 * Convolves two real Float32Array signals using FFT.
 * Returns the full convolution signal of length (x.length + y.length - 1).
 */
export function fftConvolve(x: Float32Array, y: Float32Array): Float32Array {
  const resultLen = x.length + y.length - 1;
  let fftSize = 1;
  while (fftSize < resultLen) {
    fftSize <<= 1;
  }

  const engine = new FftEngine(fftSize);

  const realX = new Float32Array(fftSize);
  const imagX = new Float32Array(fftSize);
  realX.set(x);
  engine.transform(realX, imagX, false);

  const realY = new Float32Array(fftSize);
  const imagY = new Float32Array(fftSize);
  realY.set(y);
  engine.transform(realY, imagY, false);

  // Complex multiplication in frequency domain: (Xr + iXi) * (Yr + iYi)
  const realProd = new Float32Array(fftSize);
  const imagProd = new Float32Array(fftSize);
  for (let i = 0; i < fftSize; i++) {
    realProd[i] = realX[i] * realY[i] - imagX[i] * imagY[i];
    imagProd[i] = realX[i] * imagY[i] + imagX[i] * realY[i];
  }

  // Inverse transform back to time domain
  engine.transform(realProd, imagProd, true);

  return realProd.subarray(0, resultLen);
}

/**
 * Computes frequency response magnitude in dB for an impulse response window.
 */
export function computeRealFftSpectrum(
  irWindow: Float32Array,
  fftSize = 65536,
  sampleRate = 48000
): { freqs: Float32Array; magnitudeDb: Float32Array } {
  let size = fftSize;
  if ((size & (size - 1)) !== 0) {
    size = 65536;
  }

  const engine = new FftEngine(size);
  const real = new Float32Array(size);
  const imag = new Float32Array(size);
  const copyLen = Math.min(size, irWindow.length);
  real.set(irWindow.subarray(0, copyLen));

  engine.transform(real, imag, false);

  const numBins = size / 2;
  const freqs = new Float32Array(numBins);
  const magnitudeDb = new Float32Array(numBins);
  const binWidth = sampleRate / size;

  for (let i = 0; i < numBins; i++) {
    freqs[i] = i * binWidth;
    const mag2 = real[i] * real[i] + imag[i] * imag[i];
    magnitudeDb[i] = 10.0 * Math.log10(Math.max(1e-12, mag2));
  }

  return { freqs, magnitudeDb };
}
