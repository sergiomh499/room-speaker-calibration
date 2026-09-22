import React, { useState, useEffect, useRef } from 'react';
import { Mic, MicOff, AlertCircle } from 'lucide-react';
import { Button } from './Button';

interface VUMeterProps {
  onLevelChange?: (levelDb: number) => void;
  className?: string;
  autoStart?: boolean;
}

export const VUMeter: React.FC<VUMeterProps> = ({ onLevelChange, className, autoStart }) => {
  const [isActive, setIsActive] = useState<boolean>(false);
  const [levelDb, setLevelDb] = useState<number>(-60);
  const [peakDb, setPeakDb] = useState<number>(-60);
  const [error, setError] = useState<string | null>(null);

  const audioContextRef = useRef<AudioContext | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const animFrameRef = useRef<number | null>(null);
  const peakDecayRef = useRef<number>(-60);
  useEffect(() => {
    if (autoStart && !isActive) {
      startMonitoring();
    }
  }, [autoStart]);


  const startMonitoring = async () => {
    try {
      setError(null);
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: false,
          noiseSuppression: false,
          autoGainControl: false,
        },
      });
      streamRef.current = stream;

      const audioCtx = new AudioContext();
      audioContextRef.current = audioCtx;

      const source = audioCtx.createMediaStreamSource(stream);
      const analyser = audioCtx.createAnalyser();
      analyser.fftSize = 512;
      analyser.smoothingTimeConstant = 0.4;
      source.connect(analyser);
      analyserRef.current = analyser;

      setIsActive(true);

      const dataArray = new Uint8Array(analyser.frequencyBinCount);

      const updateMeter = () => {
        if (!analyserRef.current) return;
        analyserRef.current.getByteTimeDomainData(dataArray);

        let sumSquares = 0;
        for (let i = 0; i < dataArray.length; i++) {
          const norm = (dataArray[i] - 128) / 128;
          sumSquares += norm * norm;
        }
        const rms = Math.sqrt(sumSquares / dataArray.length);
        const db = rms > 0.0001 ? 20 * Math.log10(rms) : -60;
        const clampedDb = Math.max(-60, Math.min(0, Math.round(db * 10) / 10));

        setLevelDb(clampedDb);
        if (onLevelChange) onLevelChange(clampedDb);

        if (clampedDb > peakDecayRef.current) {
          peakDecayRef.current = clampedDb;
        } else {
          peakDecayRef.current = Math.max(-60, peakDecayRef.current - 0.4);
        }
        setPeakDb(Math.round(peakDecayRef.current * 10) / 10);

        animFrameRef.current = requestAnimationFrame(updateMeter);
      };

      updateMeter();
    } catch (err: unknown) {
      console.error('Microphone error:', err);
      setError('No se pudo acceder al micrófono. Verifica los permisos del navegador.');
      setIsActive(false);
    }
  };

  const stopMonitoring = () => {
    if (animFrameRef.current) {
      cancelAnimationFrame(animFrameRef.current);
      animFrameRef.current = null;
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }
    setIsActive(false);
    setLevelDb(-60);
    setPeakDb(-60);
  };

  useEffect(() => {
    return () => {
      stopMonitoring();
    };
  }, []);

  // Convert -60 dB to 0 dB to percentage 0% to 100%
  const levelPercent = Math.max(0, Math.min(100, ((levelDb + 60) / 60) * 100));
  const peakPercent = Math.max(0, Math.min(100, ((peakDb + 60) / 60) * 100));

  return (
    <div className={`bg-surface-2/60 border border-border-subtle rounded-xl p-4 ${className || ''}`}>
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2.5">
          <div className={`p-2 rounded-lg ${isActive ? 'bg-emerald-500/20 text-emerald-400' : 'bg-surface-3 text-slate-400'}`}>
            {isActive ? <Mic className="w-5 h-5 animate-pulse" /> : <MicOff className="w-5 h-5" />}
          </div>
          <div>
            <div className="text-sm font-semibold text-slate-200">
              {isActive ? 'Micrófono Activo' : 'Comprobador de Micrófono'}
            </div>
            <div className="text-xs text-slate-400 font-mono">
              {isActive ? `Nivel: ${levelDb.toFixed(1)} dBFS (Pico: ${peakDb.toFixed(1)} dBFS)` : 'Verifica captación acústica antes de medir'}
            </div>
          </div>
        </div>
        <Button
          size="sm"
          variant={isActive ? 'danger' : 'primary'}
          onClick={isActive ? stopMonitoring : startMonitoring}
        >
          {isActive ? 'Detener' : 'Activar Mic'}
        </Button>
      </div>

      {error && (
        <div className="flex items-center gap-2 p-2.5 mb-3 text-xs bg-rose-500/10 border border-rose-500/30 text-rose-300 rounded-lg">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Meter Bar */}
      <div className="relative h-4 bg-surface-0 rounded-full overflow-hidden border border-border-subtle p-0.5">
        {/* Fill bar */}
        <div
          className="h-full rounded-full transition-all duration-75"
          style={{
            width: `${levelPercent}%`,
            background: 'linear-gradient(90deg, #10b981 0%, #10b981 65%, #f59e0b 85%, #f43f5e 100%)',
          }}
        />
        {/* Peak indicator */}
        {isActive && (
          <div
            className="absolute top-0 bottom-0 w-1 bg-white shadow-sm transition-all duration-100"
            style={{ left: `${peakPercent}%` }}
          />
        )}
      </div>

      {/* dB scale labels */}
      <div className="flex justify-between text-[10px] text-slate-500 font-mono mt-1 px-1">
        <span>-60</span>
        <span>-40</span>
        <span>-24</span>
        <span>-12</span>
        <span>-6</span>
        <span>0 dBFS</span>
      </div>
    </div>
  );
};
