export type Topology = '2.0' | '2.1' | '3.1' | '5.1';

export interface TargetProfile {
  id: string;
  name: string;
  category: string;
  badge?: string;
  description: string;
  cutoff_hz?: number;
  subwoofer_crossover_hz?: number;
  pros?: string[];
  cons?: string[];
  bands?: Record<string, any>;
  sub_bands?: Record<string, any>;
  supported_topologies?: string[];
  sub_supported?: boolean;
}

export interface AVRStatus {
  ok: boolean;
  avr_power: string;
  avr_input: string;
  avr_volume_db: string | number;
  avr_peq_mode: string;
  avr_mute?: string;
  avr_drc: string;
  points_measured: number;
  points_total: number;
  calibration_ready: boolean;
  timestamp?: number;
  online?: boolean;
}

export interface ChannelTelemetry {
  measured: boolean;
  spl_db?: number;
  distance_m?: number;
  delay_ms?: number;
  snr_db?: number;
}

export interface MeasurementPoint {
  id: number;
  label: string;
  sublabel: string;
  measured: boolean;
  active?: boolean;
  channels?: Record<string, ChannelTelemetry>;
}

export interface SubwooferConfig {
  crossover_hz: number;
  phase_degrees: 0 | 180;
  trim_db: number;
  peq_bands: Array<{
    band: number;
    freq_hz: number;
    q: number;
    gain_db: number;
    type?: string;
  }>;
}

export interface PEQBand {
  band: number;
  freq: number;
  q: number;
  gain: number;
}

export interface CurvePoint {
  freq: number;
  measured_l: number;
  measured_r: number;
  target?: number;
  corrected_l?: number;
  corrected_r?: number;
}

export interface ChannelTrimData {
  id: string;
  name: string;
  model: string;
  current_trim_db: number;
  suggested_trim_db: number;
}

/**
 * Domain Models from Phase 1 Data Model (012-pro-android-calibration)
 */

export interface ParametricFilterBand {
  channel: 'Front_L' | 'Front_R';
  band: number;
  freqHz: number;
  q: number;
  gainDb: number;
  role: 'room_mode' | 'voicing' | 'tilt' | 'transparent_pass';
}

export interface AcousticMeasurement {
  id: string;
  pointIndex: number;
  channel: 'Front_L' | 'Front_R' | 'Subwoofer';
  timestamp: number;
  sampleRate: number;
  durationMs: number;
  peakDbfs: number;
  snrDb: number;
  delayMs: number;
  distanceM: number;
  splDb: number;
  freqs: number[];
  rawResponseDb: number[];
  smoothedResponseDb: number[];
  irBufferPath?: string;
}

export interface ReceiverStateSnapshot {
  timestamp: number;
  power: string;
  input: string;
  volumeDb: number;
  peqMode: string;
  straight?: boolean;
  pattern1Xml?: string;
  volumesRawXml?: string;
  distancesRawXml?: string;
}

export interface VerificationAuditRecord {
  timestamp: number;
  profileId: string;
  freqs: number[];
  baselineDb: number[];
  targetDb: number[];
  filterResponseDb: number[];
  verifiedDb: number[];
  modalAttenuations: Array<{ freqHz: number; reductionDb: number }>;
  rmsErrorPreDb: number;
  rmsErrorPostDb: number;
}

export interface CalibrationSession {
  id: string;
  createdAt: string;
  topology: Topology;
  numPoints: 1 | 3 | 5;
  targetProfileId: string;
  micProfileId: string;
  points: MeasurementPoint[];
  spatialAverage?: Record<string, number[]>;
  optimizedFilters?: Record<string, ParametricFilterBand[]>;
  crossoverHz?: number;
  subwooferDelayMs?: number;
  channelTrims?: Record<string, number>;
  preFlightSnapshot?: ReceiverStateSnapshot;
  verification?: VerificationAuditRecord;
  deployed: boolean;
}

export interface MicrophoneCalibrationProfile {
  id: string;
  name: string;
  isUsb: boolean;
  calibrationData?: Array<[number, number]>; // [freq_hz, offset_db]
}
