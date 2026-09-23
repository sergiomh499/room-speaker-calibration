import { Capacitor } from '@capacitor/core';
import { AVRStatus, TargetProfile } from '../types';
import { yamahaDirect } from './yamahaDirect';

const DEFAULT_LAN_SERVER = 'http://192.168.1.45:53317';
export const getBaseUrl = (): string => {
  if (Capacitor.isNativePlatform()) {
    return localStorage.getItem('octave_server_url') || DEFAULT_LAN_SERVER;
  }
  return '';
};

export async function fetchApi<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const base = getBaseUrl();
  const url = endpoint.startsWith('http') ? endpoint : `${base}${endpoint}`;
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 3500);
  try {
    const res = await fetch(url, {
      ...options,
      signal: controller.signal,
      headers: {
        'Accept': 'application/json',
        ...options?.headers,
      },
    });
    if (!res.ok) {
      throw new Error(`API error ${res.status}: ${res.statusText}`);
    }
    return res.json();
  } finally {
    clearTimeout(timeoutId);
  }
}

export const api = {
  async getStatus(): Promise<AVRStatus> {
    try {
      const data = await fetchApi<AVRStatus>('/api/status');
      return { ...data, online: true };
    } catch {
      try {
        if (Capacitor.isNativePlatform()) {
          const xml = `<YAMAHA_AV cmd="GET"><Main_Zone><Basic_Status>GetParam</Basic_Status></Main_Zone></YAMAHA_AV>`;
          const resp = await yamahaDirect.sendYncXml(xml);
          const pMatch = resp.match(/<Power>(.*?)<\/Power>/);
          const inMatch = resp.match(/<Input_Sel>(.*?)<\/Input_Sel>/);
          const volMatch = resp.match(/<Val>(-?\d+)<\/Val>/);
          const drcMatch = resp.match(/<Adaptive_DRC>(.*?)<\/Adaptive_DRC>/);

          let peqMode = 'Manual';
          try {
            const peqXml = `<YAMAHA_AV cmd="GET"><System><Speaker_Preout><Pattern_1><PEQ><Sel>GetParam</Sel></PEQ></Pattern_1></Speaker_Preout></System></YAMAHA_AV>`;
            const peqResp = await yamahaDirect.sendYncXml(peqXml);
            const peqMatch = peqResp.match(/<Sel>(.*?)<\/Sel>/);
            if (peqMatch) peqMode = peqMatch[1];
          } catch {}


          return {
            ok: true,
            avr_power: pMatch ? pMatch[1] : 'On',
            avr_input: inMatch ? inMatch[1] : 'AV4',
            avr_volume_db: volMatch ? (parseInt(volMatch[1], 10) / 10).toFixed(1) : '-40.0',
            avr_peq_mode: peqMode,
            avr_drc: drcMatch ? drcMatch[1] : 'Off',
            points_measured: 5,
            points_total: 5,
            calibration_ready: true,
            online: true,
          };
        }
      } catch (err) {
        console.warn('Error en fallback directo a Yamaha:', err);
      }
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

  async getMeasuredCurve(profile: string = 'harman_wide_room'): Promise<any> {
    return fetchApi<any>(`/api/measured_curve?profile=${encodeURIComponent(profile)}`);
  },

  async playTone(channel: string): Promise<any> {
    return fetchApi<any>(`/api/play_test_tone?channel=${encodeURIComponent(channel)}`);
  },

  async playSweep(channel: string): Promise<any> {
    return fetchApi<any>(`/api/play_sweep?channel=${encodeURIComponent(channel)}`);
  },

  async uploadSweep(point: number, channel: string, bytes: Uint8Array, layout?: string, leadMs?: number, pingMs?: number): Promise<any> {
    const layoutParam = layout ? `&layout=${encodeURIComponent(layout)}` : '';
    const leadParam = leadMs !== undefined ? `&lead_ms=${encodeURIComponent(leadMs)}` : '';
    const pingParam = pingMs !== undefined ? `&ping_ms=${encodeURIComponent(pingMs)}` : '';
    
    // Convert binary to Base64 to bypass CapacitorHttp UTF-8 corruption on Android
    let binary = '';
    const chunk = 8192;
    for (let i = 0; i < bytes.length; i += chunk) {
      binary += String.fromCharCode.apply(null, Array.from(bytes.subarray(i, i + chunk)));
    }
    const audioB64 = window.btoa(binary);

    return fetchApi<any>(`/api/upload_sweep?point=${point}&channel=${encodeURIComponent(channel)}${layoutParam}${leadParam}${pingParam}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ audio_b64: audioB64 })
    });
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
  async finalizeCalibration(profile: string = 'harman_wide_room', points?: number[]): Promise<any> {
    const q = `/api/finalize_calibration?profile=${encodeURIComponent(profile)}${points && points.length ? `&points=${points.join(',')}` : ''}`;
    return fetchApi<any>(q);
  },

  async getChannelLayout(): Promise<any> {
    return fetchApi<any>('/api/detect_channels');
  },

  async setChannelLevels(levels: Record<string, number>): Promise<any> {
    return fetchApi<any>('/api/set_channel_levels', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ levels }),
    });
  },

  async setSubwooferConfig(phase: string = 'Normal', crossoverHz: number = 80.0, extraBass: boolean = false): Promise<any> {
    return fetchApi<any>('/api/set_subwoofer_config', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ phase, crossover_hz: crossoverHz, extra_bass: extraBass }),
    });
  },

  async getVerificationCurves(profile: string = 'harman_wide_room'): Promise<any> {
    return fetchApi<any>(`/api/verification_curves?profile=${encodeURIComponent(profile)}`);
  },
  async getVerificationComparison(profile: string = 'harman_wide_room'): Promise<any> {
    return fetchApi<any>(`/api/verification_comparison?profile=${encodeURIComponent(profile)}`);
  },
  async uploadVerificationSweep(
    channel: string,
    mode: string = 'manual',
    profile: string = 'harman_wide_room',
    audioBytes: Uint8Array
  ): Promise<any> {
    let binary = '';
    const chunk = 8192;
    for (let i = 0; i < audioBytes.length; i += chunk) {
      binary += String.fromCharCode.apply(null, Array.from(audioBytes.subarray(i, i + chunk)));
    }
    const audioB64 = window.btoa(binary);

    const url = `/api/upload_verification_sweep?channel=${encodeURIComponent(channel)}&mode=${encodeURIComponent(mode)}&profile=${encodeURIComponent(profile)}`;
    return fetchApi<any>(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ audio_b64: audioB64 })
    });
  },
  async setChannelDistances(distances: Record<string, number>): Promise<any> {
    return fetchApi<any>('/api/set_channel_distances', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ distances }),
    });
  },

  async deployPEQ(profile: string, scene?: number): Promise<any> {
    return fetchApi<any>('/api/deploy_peq', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ profile, scene }),
    });
  },

  async getPointHistory(point: number): Promise<any> {
    return fetchApi<any>(`/api/point_history?point=${point}`);
  },

  async loadPointHistory(point: number, id: string): Promise<any> {
    return fetchApi<any>('/api/point_history/load', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ point, id }),
    });
  },

  async getHistory(): Promise<any> {
    return fetchApi<any>('/api/sessions/history');
  },

  async getRoomAcousticsAdvanced(): Promise<any> {
    return fetchApi<any>('/api/room_acoustics_advanced');
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

  async setMeasurementMode(): Promise<any> {
    return fetchApi<any>('/api/set_measurement_mode', { method: 'POST' });
  },

  async snapshotListeningState(): Promise<any> {
    return fetchApi<any>('/api/snapshot_listening_state', { method: 'POST' });
  },

  async restoreAvrMode(peq?: string): Promise<any> {
    return fetchApi<any>('/api/restore_avr_mode', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ peq }),
    });
  },

  async getFilterCurves(profile: string): Promise<any> {
    return fetchApi<any>(`/api/peq_filter_curves?profile=${encodeURIComponent(profile)}`);
  },

  async getMeasurementAnalysis(): Promise<any> {
    return fetchApi<any>('/api/measurement_analysis');
  },
  async calculateAndSavePEQ(profile: string, layout: string = '2.1', crossoverHz: number = 80.0): Promise<any> {
    return fetchApi<any>('/api/calibration/calculate_and_save_peq', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        profile,
        layout,
        crossover_hz: crossoverHz
      })
    });
  },
  async setPeqMode(mode: string): Promise<any> {
    return fetchApi<any>('/api/set_peq_mode', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mode, prepare_sweep: '0' })
    });
  },
  async setMasterVolume(volume_db: number): Promise<any> {
    return fetchApi<any>('/api/set_volume', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ volume_db })
    });
  },
  async adjustVolumeStep(step: number): Promise<any> {
    return fetchApi<any>('/api/set_volume', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ step })
    });
  },
  async setInput(input: string): Promise<any> {
    return fetchApi<any>('/api/set_input', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ input })
    });
  },
  async getAvailableInputs(): Promise<Array<{ id: string; name: string; type: string }>> {
    const res = await fetchApi<{ ok: boolean; inputs: Array<{ id: string; name: string; type: string }> }>('/api/available_inputs');
    return res.inputs || [];
  },
  async selectScene(num: number): Promise<any> {
    return fetchApi<any>(`/api/select_scene?num=${num}`, { method: 'POST' });
  },
  async streamToAvr(file: string, title: string = 'Sweep Calibración'): Promise<any> {
    return fetchApi<any>('/api/stream_to_avr', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ file, title }),
    });
  },
  async stopAvrStream(): Promise<any> {
    return fetchApi<any>('/api/stop_avr_stream', { method: 'POST' });
  },
  async sendDirectAvrXml(xml: string, host: string = '192.168.1.43'): Promise<any> {
    return fetchApi<any>('/api/send_cmd', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ xml, host }),
    });
  },
};
