import { yamahaDirect } from './yamahaDirect';
import { audioPlayback } from './audioPlayback';
import { nativeAudio } from './nativeAudio';
import { analyzeRecordedSweep, YAMAHA_FREQS, generateTargetCurve, biquadPeakingResponse } from './dspEngine';
import type { VerificationAuditRecord, ParametricFilterBand } from '../types';
function delay(ms: number): Promise<void> {
  const { promise, resolve } = Promise.withResolvers<void>();
  setTimeout(resolve, ms);
  return promise;
}

export class VerificationEngine {
  /**
   * Runs an empirical closed-loop post-calibration sweep across active channels.
   * Compares the physical response against the pre-calibration baseline and target.
   */
  async runVerification(
    profileId: string,
    baselineL: number[],
    baselineR: number[],
    deployedFiltersL: ParametricFilterBand[],
    deployedFiltersR: ParametricFilterBand[]
  ): Promise<VerificationAuditRecord> {
    // 1. Ensure receiver PEQ mode is strictly Manual (calibrated DSP active)
    await yamahaDirect.setPeqMode('Manual');

    // 2. Play & record Left channel verification sweep
    await nativeAudio.startRecording('verification_sweep_L.wav');
    await audioPlayback.playSweep('L', 'aux');
    await delay(5200);
    const recL = await nativeAudio.stopRecording();

    let verifiedL = [...baselineL];
    if ('base64Audio' in recL && recL.base64Audio) {
      const binary = atob(recL.base64Audio);
      const bytes = new Uint8Array(binary.length);
      for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
      const analysis = analyzeRecordedSweep(bytes, 'Front_L');
      if (analysis.ok) verifiedL = analysis.response_db;
    }

    // 3. Play & record Right channel verification sweep
    await nativeAudio.startRecording('verification_sweep_R.wav');
    await audioPlayback.playSweep('R', 'aux');
    await delay(5200);
    const recR = await nativeAudio.stopRecording();

    let verifiedR = [...baselineR];
    if ('base64Audio' in recR && recR.base64Audio) {
      const binary = atob(recR.base64Audio);
      const bytes = new Uint8Array(binary.length);
      for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
      const analysis = analyzeRecordedSweep(bytes, 'Front_R');
      if (analysis.ok) verifiedR = analysis.response_db;
    }

    const freqs = YAMAHA_FREQS;
    const target = generateTargetCurve(freqs, profileId);

    const baselineAvg = freqs.map((_, i) => Math.round(((baselineL[i] + baselineR[i]) / 2.0) * 10) / 10);
    const verifiedAvg = freqs.map((_, i) => Math.round(((verifiedL[i] + verifiedR[i]) / 2.0) * 10) / 10);

    // 4. Calculate theoretical filter transfer function
    const filterResp = new Array(freqs.length).fill(0.0);
    const totalFilters = [...deployedFiltersL, ...deployedFiltersR];
    for (const b of totalFilters) {
      const bResp = biquadPeakingResponse(freqs, b.freqHz, b.q, b.gainDb);
      for (let i = 0; i < freqs.length; i++) filterResp[i] += bResp[i] / 2.0;
    }

    // 5. Quantify Room Mode Attenuation (< 500 Hz)
    const modalAttenuations: Array<{ freqHz: number; reductionDb: number }> = [];
    for (let i = 0; i < freqs.length; i++) {
      const f = freqs[i];
      if (f < 500.0) {
        const prePeak = baselineAvg[i] - target[i];
        const postPeak = verifiedAvg[i] - target[i];
        if (prePeak >= 2.0) {
          const reduction = Math.round((prePeak - postPeak) * 10) / 10;
          modalAttenuations.push({ freqHz: f, reductionDb: Math.max(0.0, reduction) });
        }
      }
    }

    // 6. Compute Root-Mean-Square Error Before and After Calibration
    let sumSqPre = 0;
    let sumSqPost = 0;
    for (let i = 0; i < freqs.length; i++) {
      const diffPre = baselineAvg[i] - target[i];
      const diffPost = verifiedAvg[i] - target[i];
      sumSqPre += diffPre * diffPre;
      sumSqPost += diffPost * diffPost;
    }
    const rmsErrorPreDb = Math.round(Math.sqrt(sumSqPre / freqs.length) * 10) / 10;
    const rmsErrorPostDb = Math.round(Math.sqrt(sumSqPost / freqs.length) * 10) / 10;

    return {
      timestamp: Date.now(),
      profileId,
      freqs,
      baselineDb: baselineAvg,
      targetDb: target,
      filterResponseDb: filterResp,
      verifiedDb: verifiedAvg,
      modalAttenuations,
      rmsErrorPreDb,
      rmsErrorPostDb,
    };
  }
}

export const verificationEngine = new VerificationEngine();
