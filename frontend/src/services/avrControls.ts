import { useState, useEffect, useRef } from 'react';
import { AVRStatus } from '../types';
import { api } from './api';
import { yamahaDirect } from './yamahaDirect';

export interface UseAvrControlsOptions {
  avrStatus: AVRStatus;
  refreshStatus: () => Promise<void>;
  toast: (msg: string, type?: 'info' | 'success' | 'warn' | 'error') => void;
}

export function useAvrControls({ avrStatus, refreshStatus, toast }: UseAvrControlsOptions) {
  const [localVol, setLocalVol] = useState<number | null>(null);
  const isAdjustingRef = useRef<boolean>(false);
  const timeoutRef = useRef<any>(null);

  const serverVol = typeof avrStatus.avr_volume_db === 'number'
    ? avrStatus.avr_volume_db
    : parseFloat(String(avrStatus.avr_volume_db)) || -35.0;

  const serverMuted = avrStatus.avr_mute === 'On' || (typeof avrStatus.avr_volume_db === 'number'
    ? avrStatus.avr_volume_db <= -70
    : parseFloat(String(avrStatus.avr_volume_db)) <= -70);

  const [isMuted, setIsMuted] = useState<boolean>(serverMuted);

  useEffect(() => {
    if (!isAdjustingRef.current) {
      setLocalVol(serverVol);
    }
  }, [serverVol]);

  useEffect(() => {
    setIsMuted(serverMuted);
  }, [serverMuted]);

  useEffect(() => {
    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
    };
  }, []);

  const currentVol = localVol !== null ? localVol : serverVol;

  const handleVolumeChange = async (delta: number) => {
    if (typeof navigator !== 'undefined' && navigator.vibrate) {
      navigator.vibrate(12);
    }
    isAdjustingRef.current = true;
    clearTimeout(timeoutRef.current);
    const nextVol = Math.max(-80.0, Math.min(16.5, Math.round((currentVol + delta) * 2) / 2));
    setLocalVol(nextVol);

    try {
      await api.adjustVolumeStep(delta);
    } catch {
      yamahaDirect.setVolume(nextVol);
    }

    timeoutRef.current = setTimeout(async () => {
      isAdjustingRef.current = false;
      await refreshStatus();
    }, 600);
  };

  const handleToggleMute = () => {
    if (typeof navigator !== 'undefined' && navigator.vibrate) {
      navigator.vibrate(20);
    }
    const nextMute = !isMuted;
    setIsMuted(nextMute);
    const xml = `<YAMAHA_AV cmd="PUT"><Main_Zone><Volume><Mute>${nextMute ? 'On' : 'Off'}</Mute></Volume></Main_Zone></YAMAHA_AV>`;
    yamahaDirect.sendYncXml(xml);
    toast(nextMute ? 'Silenciado (Mute)' : 'Sonido activado', 'info');
    setTimeout(refreshStatus, 400);
  };

  const handleSceneSelect = async (sceneNum: number) => {
    if (typeof navigator !== 'undefined' && navigator.vibrate) {
      navigator.vibrate([15, 30, 15]);
    }
    yamahaDirect.selectScene(sceneNum);
    const sceneLabels: Record<number, string> = { 1: 'Música', 2: 'Cine', 3: 'Gaming', 4: 'Pure Direct' };
    const label = sceneLabels[sceneNum] || `Escena ${sceneNum}`;

    try {
      if (sceneNum === 4) {
        await api.setPeqMode('Through');
      } else {
        await api.setPeqMode('Manual');
      }
    } catch {
      const mode = sceneNum === 4 ? 'Through' : 'Manual';
      yamahaDirect.setPeqMode(mode);
    }

    toast(`${label} activada`, 'success');
    setTimeout(refreshStatus, 800);
  };

  const handleSelectInput = async (newInput: string) => {
    if (typeof navigator !== 'undefined' && navigator.vibrate) {
      navigator.vibrate(15);
    }
    try {
      await api.setInput(newInput);
      toast(`Entrada AVR: ${newInput}`, 'info');
      await refreshStatus();
    } catch (err: any) {
      toast(`Error al cambiar entrada: ${err?.message || 'Fallo de red'}`, 'warn');
    }
  };

  const handleSetPeqMode = async (mode: 'Manual' | 'Natural' | 'Flat' | 'Through') => {
    if (typeof navigator !== 'undefined' && navigator.vibrate) {
      navigator.vibrate(15);
    }
    try {
      await api.setPeqMode(mode);
      toast(`Modo PEQ: ${mode}`, 'info');
      await refreshStatus();
    } catch {
      yamahaDirect.setPeqMode(mode);
      toast(`Modo PEQ: ${mode}`, 'info');
      setTimeout(refreshStatus, 500);
    }
  };

  return {
    currentVol,
    isMuted,
    handleVolumeChange,
    handleToggleMute,
    handleSelectInput,
    handleSceneSelect,
    handleSetPeqMode,
  };
}
