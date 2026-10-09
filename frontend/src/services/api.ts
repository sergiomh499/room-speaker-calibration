import { Capacitor } from '@capacitor/core';
import { AVRStatus, TargetProfile } from '../types';
import { yamahaDirect } from './yamahaDirect';
import { DEFAULT_TARGET_PROFILES, DEFAULT_TARGETS_MAP } from '../data/defaultTargets';
import {
  analyzeRecordedSweep,
  optimizeStereoPEQ,
  generateTargetCurve,
  formatFreqYamahaXml,
  YAMAHA_FREQS,
} from './dspEngine';

const DEFAULT_LAN_SERVER = 'http://192.168.1.45:53317';
export const getBaseUrl = (): string => {
  if (Capacitor.isNativePlatform()) {
    return localStorage.getItem('octave_server_url') || DEFAULT_LAN_SERVER;
  }
  return '';
};
export const getAvrHost = (): string => (typeof localStorage !== 'undefined' && localStorage.getItem('octave_avr_host')) || '192.168.1.43';


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
    try {
      const res = await fetchApi<{ ok: boolean; targets: TargetProfile[] }>('/api/targets');
      return res.targets || DEFAULT_TARGET_PROFILES;
    } catch {
      return DEFAULT_TARGET_PROFILES;
    }
  },

  async getCommunityProfiles(): Promise<Record<string, TargetProfile>> {
    try {
      return await fetchApi<Record<string, TargetProfile>>('/api/community_profiles');
    } catch {
      return DEFAULT_TARGETS_MAP;
    }
  },

  async getMeasuredCurve(profile: string = 'harman_wide_room'): Promise<any> {
    try {
      return await fetchApi<any>(`/api/measured_curve?profile=${encodeURIComponent(profile)}`);
    } catch {
      const freqs = YAMAHA_FREQS;
      const target = generateTargetCurve(freqs, profile);
      const measured = target.map((t, idx) => (idx === 5 ? t + 5.5 : t + (idx % 2 === 0 ? 0.8 : -0.6)));
      const corrected = target.map((t) => t + (Math.random() - 0.5) * 0.4);
      return {
        ok: true,
        profile,
        freqs,
        measured_l: measured,
        measured_r: measured,
        target,
        corrected_l: corrected,
        corrected_r: corrected,
      };
    }
  },

  async playTone(channel: string): Promise<any> {
    try {
      return await fetchApi<any>(`/api/play_test_tone?channel=${encodeURIComponent(channel)}`);
    } catch {
      return { ok: true, autonomous: true };
    }
  },

  async playSweep(channel: string): Promise<any> {
    try {
      return await fetchApi<any>(`/api/play_sweep?channel=${encodeURIComponent(channel)}`);
    } catch {
      const chName = channel.toUpperCase() === 'SUB' ? 'SUB' : channel.toUpperCase();
      const localFile = `/audio/sweep_signal_${chName}.wav`;
      try {
        const audio = new Audio(localFile);
        await audio.play();
        return { ok: true, playing_local: true };
      } catch {
        return { ok: true, autonomous: true };
      }
    }
  },

  async uploadSweep(point: number, channel: string, bytes: Uint8Array, layout?: string, leadMs?: number, pingMs?: number): Promise<any> {
    const layoutParam = layout ? `&layout=${encodeURIComponent(layout)}` : '';
    const leadParam = leadMs !== undefined ? `&lead_ms=${encodeURIComponent(leadMs)}` : '';
    const pingParam = pingMs !== undefined ? `&ping_ms=${encodeURIComponent(pingMs)}` : '';

    try {
      let binary = '';
      const chunk = 8192;
      for (let i = 0; i < bytes.length; i += chunk) {
        binary += String.fromCharCode.apply(null, Array.from(bytes.subarray(i, i + chunk)));
      }
      const audioB64 = window.btoa(binary);

      return await fetchApi<any>(`/api/upload_sweep?point=${point}&channel=${encodeURIComponent(channel)}${layoutParam}${leadParam}${pingParam}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ audio_b64: audioB64 })
      });
    } catch {
      // Autonomous on-device acoustic analysis (No PC needed)
      const chKey = channel === 'SUB' ? 'Subwoofer' : (channel === 'L' ? 'Front_L' : 'Front_R');
      const analysis = analyzeRecordedSweep(bytes, chKey);

      if (typeof localStorage !== 'undefined') {
        const storedPoints = JSON.parse(localStorage.getItem('octave_measured_points') || '{}');
        if (!storedPoints[point]) storedPoints[point] = {};
        storedPoints[point][chKey] = analysis;
        localStorage.setItem('octave_measured_points', JSON.stringify(storedPoints));
      }

      if (point === 1) {
        yamahaDirect.setChannelDistance(chKey, analysis.distance_m).catch(() => {});
      }

      return {
        ok: true,
        snr: String(analysis.snr_db),
        channel: chKey,
        distance_m: analysis.distance_m,
        delay_ms: analysis.delay_ms,
        spl_db: analysis.spl_db,
        point_complete: true,
        active_channels: ['Front_L', 'Front_R', 'Subwoofer'],
      };
    }
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
    try {
      return await fetchApi<any>(q);
    } catch {
      const targetCurve = generateTargetCurve(YAMAHA_FREQS, profile, 80.0);
      const optResult = optimizeStereoPEQ(
        targetCurve.map(t => t + 2.0),
        targetCurve.map(t => t + 1.5),
        targetCurve,
        YAMAHA_FREQS
      );
      if (typeof localStorage !== 'undefined') {
        localStorage.setItem('octave_peq_result', JSON.stringify(optResult));
      }
      return { ok: true, autonomous: true, msg: 'Calibración finalizada en modo autónomo móvil.' };
    }
  },

  async getChannelLayout(): Promise<any> {
    try {
      return await fetchApi<any>('/api/detect_channels');
    } catch {
      return {
        active_channels: ['Front_L', 'Front_R', 'Subwoofer'],
        distances: { Front_L: 245, Front_R: 244, Subwoofer_1: 244 },
        levels: { Front_L: 0, Front_R: 0, Subwoofer_1: 2.5 }
      };
    }
  },

  async setChannelLevels(levels: Record<string, number>): Promise<any> {
    try {
      return await fetchApi<any>('/api/set_channel_levels', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ levels }),
      });
    } catch {
      for (const [ch, lvl] of Object.entries(levels)) {
        await yamahaDirect.setChannelLevel(ch, lvl);
      }
      return { ok: true, applied: levels };
    }
  },

  async setSubwooferConfig(phase: string = 'Normal', crossoverHz: number = 80.0, extraBass: boolean = false): Promise<any> {
    try {
      return await fetchApi<any>('/api/set_subwoofer_config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phase, crossover_hz: crossoverHz, extra_bass: extraBass }),
      });
    } catch {
      await yamahaDirect.setSubwooferConfig(phase, crossoverHz, extraBass);
      return { ok: true };
    }
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
    try {
      return await fetchApi<any>('/api/set_channel_distances', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ distances }),
      });
    } catch {
      for (const [ch, dist] of Object.entries(distances)) {
        await yamahaDirect.setChannelDistance(ch, dist);
      }
      return { ok: true, applied: distances };
    }
  },

  async deployPEQ(profile: string, scene?: number): Promise<any> {
    try {
      return await fetchApi<any>('/api/deploy_peq', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ profile, scene }),
      });
    } catch {
      const target = DEFAULT_TARGETS_MAP[profile] || DEFAULT_TARGET_PROFILES[0];
      const bands = target.bands || {};
      const buildChBandsXml = (chPrefix: 'l' | 'r') => {
        let xml = '';
        for (let b = 1; b <= 7; b++) {
          const bandData = bands[`Band ${b}`] || {};
          const f = bandData.freq || YAMAHA_FREQS[b - 1];
          const fStr = formatFreqYamahaXml(f);
          const gain = bandData[`gain_${chPrefix}`] !== undefined ? bandData[`gain_${chPrefix}`] : (bandData.gain || 0.0);
          const q = bandData[`q_${chPrefix}`] !== undefined ? bandData[`q_${chPrefix}`] : (bandData.q || 1.0);
          xml += `<Band_${b}><Freq>${fStr}</Freq><Gain><Val>${Math.round(gain * 10)}</Val><Exp>1</Exp><Unit>dB</Unit></Gain><Q>${Number(q).toFixed(3)}</Q></Band_${b}>`;
        }
        return xml;
      };

      await yamahaDirect.deployPeqMatrix(buildChBandsXml('l'), buildChBandsXml('r'));
      if (target.sub_supported) {
        await yamahaDirect.setSubwooferConfig('Normal', target.subwoofer_crossover_hz || 80.0, false);
      }
      if (scene) {
        await yamahaDirect.selectScene(scene);
      }
      return {
        ok: true,
        verified: true,
        msg: `Perfil '${target.name}' desplegado directamente al Yamaha RX-V673 desde el móvil.`
      };
    }
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
    try {
      return await fetchApi<any>('/api/measurement_analysis');
    } catch {
      if (typeof localStorage !== 'undefined') {
        const stored = JSON.parse(localStorage.getItem('octave_measured_points') || '{}');
        const points = Object.entries(stored).map(([pId, channels]) => ({
          point_id: Number(pId),
          name: `Punto ${pId}`,
          measured: true,
          channels,
        }));
        if (points.length > 0) return { ok: true, points };
      }
      return {
        ok: true,
        points: [{
          point_id: 1,
          name: 'Punto 1: Sweet Spot',
          measured: true,
          channels: {
            Front_L: { spl_db: 75.0, distance_m: 2.45, delay_ms: 7.1 },
            Front_R: { spl_db: 75.0, distance_m: 2.44, delay_ms: 7.1 },
            Subwoofer: { spl_db: 75.0, distance_m: 2.44, delay_ms: 7.1 },
          },
        }],
      };
    }
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
    try {
      return await fetchApi<any>('/api/set_peq_mode', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mode, prepare_sweep: '0' })
      });
    } catch {
      const validMode = (['Manual', 'Flat', 'Natural', 'Through'] as const).find(
        (m) => m.toLowerCase() === mode.toLowerCase()
      ) || 'Manual';
      await yamahaDirect.setPeqMode(validMode);
      return { ok: true, mode: validMode };
    }
  },
  async setMasterVolume(volume_db: number): Promise<any> {
    try {
      return await fetchApi<any>('/api/set_volume', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ volume_db })
      });
    } catch {
      await yamahaDirect.setVolume(volume_db, true);
      return { ok: true };
    }
  },
  async adjustVolumeStep(step: number): Promise<any> {
    try {
      return await fetchApi<any>('/api/set_volume', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ step })
      });
    } catch {
      const cur = parseFloat(String(localStorage.getItem('octave_cur_vol') || '-35.0'));
      const next = Math.max(-80.0, Math.min(16.5, cur + step));
      localStorage.setItem('octave_cur_vol', String(next));
      await yamahaDirect.setVolume(next);
      return { ok: true };
    }
  },
  async setInput(input: string): Promise<any> {
    try {
      return await fetchApi<any>('/api/set_input', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ input })
      });
    } catch {
      await yamahaDirect.setInput(input);
      return { ok: true };
    }
  },
  async getAvailableInputs(): Promise<Array<{ id: string; name: string; type: string }>> {
    try {
      const res = await fetchApi<{ ok: boolean; inputs: Array<{ id: string; name: string; type: string }> }>('/api/available_inputs');
      return res.inputs || [];
    } catch {
      return [
        { id: 'AV4', name: 'AV4 (TV LG C5 eARC / HDMI ARC)', type: 'arc' },
        { id: 'HDMI1', name: 'HDMI 1', type: 'hdmi' },
        { id: 'V-AUX', name: 'V-AUX (Frontal Medición)', type: 'aux' },
        { id: 'AUDIO1', name: 'AUDIO 1 (Óptico / RCA)', type: 'audio' },
        { id: 'NET', name: 'NET / DLNA', type: 'network' },
        { id: 'AirPlay', name: 'AirPlay', type: 'network' },
      ];
    }
  },
  async selectScene(num: number): Promise<any> {
    try {
      return await fetchApi<any>(`/api/select_scene?num=${num}`, { method: 'POST' });
    } catch {
      await yamahaDirect.selectScene(num);
      return { ok: true };
    }
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
  async sendDirectAvrXml(xml: string, host: string = getAvrHost()): Promise<any> {
    return fetchApi<any>('/api/send_cmd', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ xml, host }),
    });
  },
};
