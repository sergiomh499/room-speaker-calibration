import { registerPlugin, Capacitor } from '@capacitor/core';

export interface AudioDevice {
  id: number;
  name: string;
  isUsb: boolean;
  type: string;
}

export interface AudioDevicesResult {
  devices: AudioDevice[];
  sampleRate: number;
  unprocessedSupported: boolean;
}

export interface RecordingResult {
  success: boolean;
  filePath: string;
  fileName: string;
  durationMs: number;
  fileSizeBytes: number;
  base64Audio?: string;
}
export interface RawAudioRecorderPluginInterface {
  getAudioDevices(): Promise<AudioDevicesResult>;
  startRecording(options?: { filename?: string }): Promise<{
    recording: boolean;
    filePath: string;
    audioSource: string;
    sampleRate: number;
  }>;
  stopRecording(): Promise<RecordingResult>;
  getRecordingStatus(): Promise<{ isRecording: boolean; elapsedMs: number }>;
}

const RawAudioRecorder = registerPlugin<RawAudioRecorderPluginInterface>('RawAudioRecorder');

class NativeAudioService {
  private isNative: boolean = false;
  private mediaRecorder: MediaRecorder | null = null;
  private audioChunks: Blob[] = [];
  public isBrowserRecording: boolean = false;
  private startTime: number = 0;

  constructor() {
    this.isNative = Capacitor.isNativePlatform() && Capacitor.isPluginAvailable('RawAudioRecorder');
  }

  isNativeRecorder(): boolean {
    return this.isNative;
  }

  async getDevices(): Promise<AudioDevice[]> {
    if (this.isNative) {
      try {
        const res = await RawAudioRecorder.getAudioDevices();
        return res.devices;
      } catch (e) {
        console.warn('Native getAudioDevices failed:', e);
      }
    }

    // Fallback para navegador
    if (navigator.mediaDevices && navigator.mediaDevices.enumerateDevices) {
      const devs = await navigator.mediaDevices.enumerateDevices();
      return devs
        .filter((d) => d.kind === 'audioinput')
        .map((d, idx) => ({
          id: idx,
          name: d.label || `Micrófono ${idx + 1}`,
          isUsb: d.label.toLowerCase().includes('umik') || d.label.toLowerCase().includes('usb'),
          type: d.label.toLowerCase().includes('usb') ? 'USB Audio Device' : 'Micrófono Sistema'
        }));
    }

    return [{ id: 0, name: 'Micrófono por Defecto', isUsb: false, type: 'Default' }];
  }

  async startRecording(filename?: string): Promise<{ success: boolean; source: string }> {
    if (this.isNative) {
      const res = await RawAudioRecorder.startRecording({ filename });
      return { success: res.recording, source: res.audioSource };
    }

    // Modo navegador: desactivar procesamiento acústico no deseado
    const stream = await navigator.mediaDevices.getUserMedia({
      audio: {
        echoCancellation: false,
        noiseSuppression: false,
        autoGainControl: false,
        channelCount: 1,
        sampleRate: 48000
      }
    });

    this.audioChunks = [];
    this.mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
    this.mediaRecorder.ondataavailable = (e) => {
      if (e.data.size > 0) this.audioChunks.push(e.data);
    };

    this.isBrowserRecording = true;
    this.startTime = Date.now();
    this.mediaRecorder.start(100);

    return { success: true, source: 'BROWSER_WEBRTC_RAW' };
  }

  async stopRecording(): Promise<RecordingResult | { blob: Blob; durationMs: number }> {
    if (this.isNative) {
      return await RawAudioRecorder.stopRecording();
    }

    if (!this.mediaRecorder) {
      throw new Error('No hay grabación activa en el navegador');
    }

    let resolvePromise!: (val: { blob: Blob; durationMs: number }) => void;
    const promise = new Promise<{ blob: Blob; durationMs: number }>((res) => {
      resolvePromise = res;
    });
    const recorder = this.mediaRecorder;

    recorder.onstop = () => {
      const durationMs = Date.now() - this.startTime;
      const blob = new Blob(this.audioChunks, { type: 'audio/webm' });
      this.isBrowserRecording = false;
      resolvePromise({ blob, durationMs });
    };

    recorder.stop();
    recorder.stream.getTracks().forEach((track) => track.stop());
    return promise;
  }
}

export const nativeAudio = new NativeAudioService();
