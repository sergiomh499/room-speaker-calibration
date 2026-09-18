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
  bands?: Record<string, { f: number; q: number; gain: number }>;
}

export interface AVRStatus {
  ok: boolean;
  avr_power: string;
  avr_input: string;
  avr_volume_db: string | number;
  avr_peq_mode: string;
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
