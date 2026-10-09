import { snapGain } from './dspEngine';
import type { SubwooferConfig } from '../types';

export interface CrossoverAlignmentResult {
  recommendedCrossoverHz: number;
  recommendedPhase: 0 | 180;
  subwooferTrimDb: number;
  delayDeltaMs: number;
  distanceDeltaM: number;
  config: SubwooferConfig;
}

/**
 * Calculates deterministic acoustic crossover, phase, and trim alignment
 * between main satellite speakers and the subwoofer.
 */
export function calculateCrossoverAlignment(
  mainsSplDb: number,
  mainsDistanceM: number,
  subSplDb: number,
  subDistanceM: number,
  crossoverChoiceHz = 80.0
): CrossoverAlignmentResult {
  // Acoustic distance delta in meters
  const distDeltaM = Math.round((subDistanceM - mainsDistanceM) * 100) / 100;

  // Time-of-flight delay delta in milliseconds (speed of sound = 343.4 m/s)
  const delayDeltaMs = Math.round((Math.abs(distDeltaM) / 343.4) * 1000 * 10) / 10;

  // Phase recommendation: at crossover frequency (e.g. 80 Hz, period = 12.5 ms),
  // if delay is closer to half-wavelength (6.25 ms), invert phase to 180°
  const wavelengthMs = 1000.0 / crossoverChoiceHz;
  const halfWaveMs = wavelengthMs / 2.0;
  const phaseDistTo0 = delayDeltaMs % wavelengthMs;
  const phaseDistTo180 = Math.abs(phaseDistTo0 - halfWaveMs);
  const recommendedPhase: 0 | 180 = phaseDistTo180 < phaseDistTo0 ? 180 : 0;

  // Level trim: match subwoofer SPL to mains SPL at crossover (clamped to [-10, +10] in 0.5 dB steps)
  const splDiff = mainsSplDb - subSplDb;
  const rawTrim = Math.max(-10.0, Math.min(10.0, splDiff));
  const subwooferTrimDb = snapGain(rawTrim, 10.0, -10.0);

  const config: SubwooferConfig = {
    crossover_hz: crossoverChoiceHz,
    phase_degrees: recommendedPhase,
    trim_db: subwooferTrimDb,
    peq_bands: [],
  };

  return {
    recommendedCrossoverHz: crossoverChoiceHz,
    recommendedPhase,
    subwooferTrimDb,
    delayDeltaMs,
    distanceDeltaM: distDeltaM,
    config,
  };
}
