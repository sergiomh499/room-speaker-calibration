import { yamahaDirect } from './yamahaDirect';

export interface MusicTrackInfo {
  title: string;
  artist: string;
  album: string;
  albumArtUrl?: string;
  isPlaying: boolean;
  source: 'spotify' | 'dlna' | 'net_radio' | 'airplay';
}

export class MusicCasterService {
  private currentTrack: MusicTrackInfo = {
    title: 'Ninguna reproducción activa',
    artist: 'Yamaha RX-V673',
    album: 'En espera',
    isPlaying: false,
    source: 'spotify'
  };

  /**
   * Lanza la aplicación Spotify directamente en Android mediante deep-linking
   * y configura automáticamente el receptor Yamaha en la entrada eARC/TV o SERVER con perfil acústico óptimo.
   */
  async launchSpotify(spotifyUri: string = 'spotify:playlist:37i9dQZF1DXcBWIGoYBM5M'): Promise<boolean> {
    try {
      // 1. Conmutar el receptor Yamaha a AV4 (Audio TV / eARC) o SERVER
      await yamahaDirect.setInput('AV4');
      // 2. Activar perfil acústico Harman Music (Escena 1)
      await yamahaDirect.selectScene(1);

      // 3. Abrir la app de Spotify nativa en Android
      if (typeof window !== 'undefined') {
        const intentUrl = `intent://#Intent;package=com.spotify.music;action=android.intent.action.VIEW;data=${encodeURIComponent(spotifyUri)};end`;
        const fallbackUrl = `https://open.spotify.com/`;

        // Intentar abrir el Intent de Spotify o la app
        window.location.href = intentUrl;
        setTimeout(() => {
          window.open(fallbackUrl, '_blank');
        }, 1500);
      }
      return true;
    } catch (e) {
      console.error('Error lanzando Spotify:', e);
      return false;
    }
  }

  /**
   * Envía un flujo de audio DLNA DMR directo al puerto 8080 del receptor Yamaha.
   * Soporta cualquier URL pública o local (MP3, FLAC, WAV, stream de radio por internet).
   */
  async castAudioStream(url: string, title: string = 'Transmisión Móvil'): Promise<boolean> {
    const success = await yamahaDirect.playDlnaStream(url, title);
    if (success) {
      this.currentTrack = {
        title,
        artist: 'Flujo Digital Directo',
        album: 'DLNA Lossless Cast',
        isPlaying: true,
        source: 'dlna'
      };
    }
    return success;
  }

  /**
   * Conmuta el receptor Yamaha a entrada NET_RADIO y sintoniza una emisora preestablecida.
   */
  async setNetRadio(): Promise<boolean> {
    return await yamahaDirect.setInput('NET_RADIO');
  }

  /**
   * Pausa o detiene la reproducción activa en el receptor.
   */
  async stopPlayback(): Promise<boolean> {
    try {
      const xml = `<YAMAHA_AV cmd="PUT"><Main_Zone><Play_Control><Playback>Stop</Playback></Play_Control></Main_Zone></YAMAHA_AV>`;
      await yamahaDirect.sendYncXml(xml);
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
