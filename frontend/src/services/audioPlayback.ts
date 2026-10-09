import { generateFarinaSweep, createWavBlob } from './sweepGenerator';
import { musicCaster } from './musicCaster';

export type ExcitationMode = 'aux' | 'dlna';

class AudioPlaybackService {
  private audioCtx: AudioContext | null = null;
  private currentSource: AudioBufferSourceNode | null = null;
  private cachedBlobs: Record<string, string> = {};
  private getAudioContext(): AudioContext {
    if (!this.audioCtx || this.audioCtx.state === 'closed') {
      if (typeof window.AudioContext === 'undefined') {
        throw new Error('WebAudio no disponible en este dispositivo');
      }
      this.audioCtx = new window.AudioContext({ sampleRate: 48000 });
    }
    if (this.audioCtx.state === 'suspended') {
      this.audioCtx.resume();
    }
    return this.audioCtx;
  }

  /**
   * Pre-generates or retrieves cached WAV object URL for sweep signal.
   */
  getSweepUrl(channel: 'L' | 'R' | 'SUB'): string {
    const key = `sweep_${channel}`;
    if (this.cachedBlobs[key]) {
      return this.cachedBlobs[key];
    }

    const isSub = channel === 'SUB';
    const { sweep } = generateFarinaSweep({
      fStart: 15.0,
      fEnd: isSub ? 180.0 : 22000.0,
      durationSec: 5.0,
      sampleRate: 48000,
    });

    const blob = createWavBlob(sweep, 48000, 1);
    const url = URL.createObjectURL(blob);
    this.cachedBlobs[key] = url;
    return url;
  }

  /**
   * Plays sweep excitation signal either via local WebAudio DAC or via network DLNA.
   */
  async playSweep(
    channel: 'L' | 'R' | 'SUB',
    mode: ExcitationMode = 'aux'
  ): Promise<{ durationMs: number; ok: boolean }> {
    const durationMs = 5000;

    if (mode === 'dlna') {
      const sweepUrl = this.getSweepUrl(channel);
      const castOk = await musicCaster.castAudioUrl(sweepUrl, `Octave Sweep ${channel}`);
      return { durationMs, ok: castOk };
    }

    // Physical AUX / USB-C Direct DAC playback
    try {
      const ctx = this.getAudioContext();
      this.stopPlayback();

      const isSub = channel === 'SUB';
      const { sweep } = generateFarinaSweep({
        fStart: 15.0,
        fEnd: isSub ? 180.0 : 22000.0,
        durationSec: 5.0,
        sampleRate: 48000,
      });

      const audioBuffer = ctx.createBuffer(2, sweep.length, 48000);
      const lChannel = audioBuffer.getChannelData(0);
      const rChannel = audioBuffer.getChannelData(1);

      if (channel === 'L') {
        lChannel.set(sweep);
      } else if (channel === 'R') {
        rChannel.set(sweep);
      } else {
        // Subwoofer: route to both channels
        lChannel.set(sweep);
        rChannel.set(sweep);
      }

      const source = ctx.createBufferSource();
      source.buffer = audioBuffer;
      source.connect(ctx.destination);
      source.start();
      this.currentSource = source;

      return { durationMs, ok: true };
    } catch (e) {
      console.warn('Fallo en reproducción WebAudio directa:', e);
      return { durationMs, ok: false };
    }
  }

  stopPlayback(): void {
    if (this.currentSource) {
      try {
        this.currentSource.stop();
        this.currentSource.disconnect();
      } catch {}
      this.currentSource = null;
    }
  }
}

export const audioPlayback = new AudioPlaybackService();
