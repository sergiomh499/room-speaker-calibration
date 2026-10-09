import { fetchApi } from './api';

export interface DlnaPlaybackStatus {
  isPlaying: boolean;
  activeUri?: string;
}

export class DlnaStreamerService {
  private status: DlnaPlaybackStatus = {
    isPlaying: false,
  };

  /**
   * Casts a direct audio sweep or tone to the Yamaha RX-V673 media renderer over DLNA.
   */
  async castAudioUrl(url: string, title = 'Octave Sweep Signal'): Promise<boolean> {
    try {
      const res = await fetchApi<{ ok: boolean; msg?: string }>('/api/cast_radio', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url, title, content_type: 'audio/wav' })
      });

      if (res && res.ok) {
        this.status = { isPlaying: true, activeUri: url };
        return true;
      }
      return false;
    } catch {
      return false;
    }
  }

  /**
   * Stops active network playback on the receiver.
   */
  async stopPlayback(): Promise<boolean> {
    try {
      await fetchApi('/api/stop_avr_stream', { method: 'POST' });
      this.status.isPlaying = false;
      return true;
    } catch {
      return false;
    }
  }

  getStatus(): DlnaPlaybackStatus {
    return this.status;
  }
}

export const musicCaster = new DlnaStreamerService();
