import { fetchApi } from './api';

export interface MusicTrackInfo {
  title: string;
  artist: string;
  album: string;
  albumArtUrl?: string;
  isPlaying: boolean;
  source: 'dlna' | 'net_radio' | 'airplay';
}

const DLNA_CONTENT_TYPE: Record<string, string> = {
  '.mp3': 'audio/mpeg',
  '.flac': 'audio/flac',
  '.ogg': 'audio/ogg',
  '.aac': 'audio/aac',
  '.wav': 'audio/wav',
};

function guessContentType(url: string): string {
  const lower = url.toLowerCase().split('?')[0];
  for (const [ext, mime] of Object.entries(DLNA_CONTENT_TYPE)) {
    if (lower.endsWith(ext)) return mime;
  }
  return 'audio/mpeg';
}

export class MusicCasterService {
  private currentTrack: MusicTrackInfo = {
    title: 'Ninguna reproducción activa',
    artist: 'Yamaha RX-V673',
    album: 'En espera',
    isPlaying: false,
    source: 'dlna'
  };

  /**
   * Envía cualquier flujo de audio (radio online o archivo) al receptor Yamaha RX-V673 vía DLNA.
   * SIEMPRE pasa a través del proxy del servidor local para garantizar compatibilidad total
   * (resuelve HTTPS, transcodifica si es necesario y evita el error "Access Error" del receptor).
   */
  async castAudioStream(url: string, title: string = 'Transmisión'): Promise<boolean> {
    const contentType = guessContentType(url);

    try {
      const res = await fetchApi<{ ok: boolean; msg?: string }>('/api/cast_radio', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url, title, content_type: contentType })
      });

      if (res && res.ok) {
        this.currentTrack = {
          title,
          artist: 'Transmisión Digital Directa',
          album: 'DLNA Local Stream',
          isPlaying: true,
          source: 'dlna'
        };
        return true;
      }
      return false;
    } catch (e) {
      console.error('Error enviando stream a través de API:', e);
      return false;
    }
  }

  /**
   * Detiene la reproducción activa y restaura la entrada a AV4.
   */
  async stopPlayback(): Promise<boolean> {
    try {
      await fetchApi('/api/stop_avr_stream', { method: 'POST' });
      this.currentTrack.isPlaying = false;
      return true;
    } catch {
      return false;
    }
  }

  getCurrentTrack(): MusicTrackInfo {
    return this.currentTrack;
  }
}

export const musicCaster = new MusicCasterService();
