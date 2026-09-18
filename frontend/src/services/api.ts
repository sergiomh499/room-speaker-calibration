import { AVRStatus, TargetProfile } from '../types';

const BASE_URL = '';

export async function fetchApi<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      'Accept': 'application/json',
      ...options?.headers,
    },
  });
  if (!res.ok) {
    throw new Error(`API error ${res.status}: ${res.statusText}`);
  }
  return res.json();
}

export const api = {
  async getStatus(): Promise<AVRStatus> {
    try {
      const data = await fetchApi<AVRStatus>('/api/status');
      return { ...data, online: true };
    } catch {
      return {
        ok: false,
        avr_power: 'Offline',
        avr_input: '—',
        avr_volume_db: '—',
        avr_peq_mode: '—',
        avr_drc: '—',
        points_measured: 0,
        points_total: 5,
        calibration_ready: false,
        online: false,
      };
    }
  },

  async getTargets(): Promise<TargetProfile[]> {
    const res = await fetchApi<{ ok: boolean; targets: TargetProfile[] }>('/api/targets');
    return res.targets || [];
  },

  async getCommunityProfiles(): Promise<Record<string, TargetProfile>> {
    return fetchApi<Record<string, TargetProfile>>('/api/community_profiles');
  },

  async getMeasuredCurve(profile: string = 'harman_2_1'): Promise<any> {
    return fetchApi<any>(`/api/measured_curve?profile=${encodeURIComponent(profile)}`);
  },

  async playTone(channel: string): Promise<any> {
    return fetchApi<any>(`/api/play_test_tone?channel=${encodeURIComponent(channel)}`);
  },

  async playSweep(channel: string): Promise<any> {
    return fetchApi<any>(`/api/play_sweep?channel=${encodeURIComponent(channel)}`);
  },

  async uploadSweep(point: number, channel: string, bytes: Uint8Array, layout?: string): Promise<any> {
    const layoutParam = layout ? `&layout=${encodeURIComponent(layout)}` : '';
    const res = await fetch(`${BASE_URL}/api/upload_sweep?point=${point}&channel=${encodeURIComponent(channel)}${layoutParam}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/octet-stream' },
      body: bytes as unknown as BodyInit
    });
    if (!res.ok) {
      throw new Error(`Error en upload: ${res.status} ${res.statusText}`);
    }
    return res.json();
  },
  async configure2_1(crossoverHz: number, phaseDeg: number = 0, subTrimDb: number = 0): Promise<any> {
    return fetchApi<any>('/api/configure_2_1', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        subwoofer_crossover_hz: crossoverHz,
        phase_degrees: phaseDeg,
        subwoofer_trim_db: subTrimDb,
        auto_deploy_hardware: false,
      }),
    });
  },

  async autoAlignPhase(): Promise<any> {
    return fetchApi<any>('/api/auto_align_subwoofer_phase', { method: 'POST' });
  },

  async autoAlignLevels(): Promise<any> {
    return fetchApi<any>('/api/auto_align_levels', { method: 'POST' });
  },

  async deployPEQ(profile: string, scene?: number): Promise<any> {
    return fetchApi<any>('/api/deploy_peq', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ profile, scene }),
    });
  },

  async getHistory(): Promise<any> {
    return fetchApi<any>('/api/sessions/history');
  },

  async restoreSession(id: string): Promise<any> {
    return fetchApi<any>('/api/sessions/restore', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: id }),
    });
  },

  async preflightCheck(enforce: boolean = true): Promise<any> {
    return fetchApi<any>(`/api/preflight_check?enforce=${enforce}`);
  },

  async getFilterCurves(profile: string): Promise<any> {
    return fetchApi<any>(`/api/peq_filter_curves?profile=${encodeURIComponent(profile)}`);
  }
};
