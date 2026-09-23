import React, { useState, useEffect, useRef } from 'react';
import { Volume2, VolumeX, Plus, Minus, Sliders, ChevronUp, ChevronDown } from 'lucide-react';
import { yamahaDirect } from '../../services/yamahaDirect';
import { api } from '../../services/api';
import { useCalibration } from '../../context/CalibrationContext';

export const MobileAvrRemote: React.FC = () => {
  const { avrStatus, refreshStatus, toast } = useCalibration();
  const [isOpen, setIsOpen] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [localVol, setLocalVol] = useState<number | null>(null);
  const isAdjustingRef = useRef<boolean>(false);
  const timeoutRef = useRef<any>(null);

  // Parsear volumen actual del estado del receptor
  const serverVol = typeof avrStatus.avr_volume_db === 'number'
    ? avrStatus.avr_volume_db
    : parseFloat(String(avrStatus.avr_volume_db)) || -35.0;

  // Sincronizar en tiempo real cuando el receptor cambie externamente
  useEffect(() => {
    if (!isAdjustingRef.current) {
      setLocalVol(serverVol);
    }
  }, [serverVol]);

  const currentVol = localVol !== null ? localVol : serverVol;

  const handleVolumeChange = async (delta: number) => {
    if (typeof navigator !== 'undefined' && navigator.vibrate) {
      navigator.vibrate(12);
    }
    isAdjustingRef.current = true;
    clearTimeout(timeoutRef.current);
    const nextVol = Math.round((currentVol + delta) * 2) / 2;
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
  };

  const handleSceneSelect = (sceneNum: number) => {
    if (typeof navigator !== 'undefined' && navigator.vibrate) {
      navigator.vibrate([15, 30, 15]);
    }
    yamahaDirect.selectScene(sceneNum);
    toast(`Escena ${sceneNum} activada`, 'success');
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
  return (
    <div className="fixed bottom-[calc(4.75rem+max(env(safe-area-inset-bottom,0px),12px))] sm:bottom-6 right-4 sm:left-4 sm:right-auto z-40">
      {/* Botón flotante para abrir el control remoto */}
      {!isOpen && (
        <button
          type="button"
          onClick={() => setIsOpen(true)}
          className="flex items-center gap-2 px-3.5 py-2.5 rounded-full bg-surface-1/95 border border-indigo-500/40 text-white shadow-xl backdrop-blur-md hover:border-indigo-400 active:scale-95 transition-all text-xs font-mono"
        >
          <Sliders className="w-4 h-4 text-indigo-400" />
          <span className="hidden sm:inline font-semibold">AVR Remote:</span>
          <span className="text-indigo-300 font-bold">{avrStatus.avr_volume_db} dB</span>
          <ChevronUp className="w-3.5 h-3.5 text-slate-400" />
        </button>
      )}

      {/* Panel Desplegable del Control Remoto */}
      {isOpen && (
        <div className="w-72 sm:w-80 rounded-2xl border border-indigo-500/40 bg-surface-1/95 p-4 shadow-2xl backdrop-blur-xl space-y-4 animate-in fade-in slide-in-from-bottom-4">
          {/* Header */}
          <div className="flex items-center justify-between pb-2 border-b border-border-subtle">
            <div className="flex items-center gap-2">
              <span className={`w-2 h-2 rounded-full ${avrStatus.online ? 'bg-emerald-400 animate-pulse' : 'bg-rose-500'}`} />
              <span className="text-xs font-bold text-white font-mono">Yamaha RX-V673</span>
            </div>
            <button
              type="button"
              onClick={() => setIsOpen(false)}
              className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-surface-2 transition-colors"
            >
              <ChevronDown className="w-4 h-4" />
            </button>
          </div>

          {/* Control de Volumen */}
          <div className="space-y-1.5">
            <div className="flex justify-between items-center text-xs font-mono">
              <span className="text-slate-400">Volumen Maestro</span>
              <span className="text-indigo-300 font-bold text-base tracking-tight">{currentVol > 0 ? '+' : ''}{currentVol.toFixed(1)} dB</span>
            </div>
            <div className="flex items-center gap-1.5">
              <button
                type="button"
                onClick={() => handleVolumeChange(-2.0)}
                className="px-2.5 py-2 rounded-xl border border-white/5 bg-surface-2 hover:bg-surface-2/80 active:scale-95 text-slate-400 hover:text-white font-mono text-xs shadow-sm transition-all"
                title="-2.0 dB"
              >
                -2
              </button>
              <button
                type="button"
                onClick={() => handleVolumeChange(-0.5)}
                className="flex-1 py-2.5 rounded-xl border border-white/10 bg-surface-2 hover:bg-surface-2/80 active:scale-95 text-white flex items-center justify-center font-bold text-sm shadow-sm transition-all"
              >
                <Minus className="w-4 h-4" />
              </button>
              <button
                type="button"
                onClick={handleToggleMute}
                className={`px-3 py-2.5 rounded-xl border transition-all active:scale-95 ${
                  isMuted
                    ? 'border-rose-500/50 bg-rose-500/20 text-rose-300'
                    : 'border-white/10 bg-surface-2 text-slate-300 hover:text-white'
                }`}
              >
                {isMuted ? <VolumeX className="w-4 h-4" /> : <Volume2 className="w-4 h-4" />}
              </button>
              <button
                type="button"
                onClick={() => handleVolumeChange(0.5)}
                className="flex-1 py-2.5 rounded-xl border border-white/10 bg-surface-2 hover:bg-surface-2/80 active:scale-95 text-white flex items-center justify-center font-bold text-sm shadow-sm transition-all"
              >
                <Plus className="w-4 h-4" />
              </button>
              <button
                type="button"
                onClick={() => handleVolumeChange(2.0)}
                className="px-2.5 py-2 rounded-xl border border-white/5 bg-surface-2 hover:bg-surface-2/80 active:scale-95 text-slate-400 hover:text-white font-mono text-xs shadow-sm transition-all"
                title="+2.0 dB"
              >
                +2
              </button>
            </div>
          </div>

          {/* Selector de Entrada AVR (Input) */}
          <div className="space-y-1.5">
            <div className="flex justify-between items-center text-xs font-mono">
              <span className="text-slate-400">Entrada Activa</span>
              <span className="text-cyan-300 font-semibold">{avrStatus.avr_input || 'AV4'}</span>
            </div>
            <div className="grid grid-cols-3 gap-1.5">
              {[
                { id: 'AV4', label: 'AV4 (TV eARC)' },
                { id: 'HDMI1', label: 'HDMI 1' },
                { id: 'V-AUX', label: 'V-AUX' },
                { id: 'AUDIO1', label: 'AUDIO 1' },
                { id: 'NET', label: 'NET / DLNA' },
                { id: 'AirPlay', label: 'AirPlay' }
              ].map((inp) => (
                <button
                  key={inp.id}
                  type="button"
                  onClick={() => handleSelectInput(inp.id)}
                  className={`py-1.5 px-1 rounded-lg border text-[10px] font-mono text-center transition-all truncate ${
                    (avrStatus.avr_input || '').toUpperCase() === inp.id.toUpperCase()
                      ? 'border-cyan-500/60 bg-cyan-600/20 text-cyan-200 font-bold shadow-sm'
                      : 'border-border-subtle bg-surface-2 text-slate-400 hover:text-white hover:border-border-prominent'
                  }`}
                >
                  {inp.label}
                </button>
              ))}
            </div>
          </div>

          {/* Escenas de Hardware (1 a 4) */}
          <div className="space-y-1.5">
            <span className="text-xs font-mono text-slate-400 block">Escenas Rápidas</span>
            <div className="grid grid-cols-4 gap-1.5">
              {[
                { num: 1, label: 'Música' },
                { num: 2, label: 'Cine' },
                { num: 3, label: 'Gaming' },
                { num: 4, label: 'Pure' }
              ].map((s) => (
                <button
                  key={s.num}
                  type="button"
                  onClick={() => handleSceneSelect(s.num)}
                  className="py-1.5 rounded-lg border border-border-subtle bg-surface-2 hover:border-indigo-500/50 text-[10px] font-mono text-slate-300 hover:text-white text-center transition-all"
                >
                  {s.label}
                </button>
              ))}
            </div>
          </div>

          {/* Selector de Modo PEQ Corregido (Manual, Natural, Flat, Through) */}
          <div className="space-y-1.5 pt-1 border-t border-border-subtle/50">
            <div className="flex justify-between items-center text-xs font-mono">
              <span className="text-slate-400">Modo PEQ Hardware</span>
              <span className="text-indigo-300 font-bold">{avrStatus.avr_peq_mode}</span>
            </div>
            <div className="grid grid-cols-4 gap-1">
              {(['Manual', 'Natural', 'Flat', 'Through'] as const).map((mId) => {
                const isActive = (avrStatus.avr_peq_mode || '').toLowerCase().includes(mId.toLowerCase());
                return (
                  <button
                    key={mId}
                    type="button"
                    onClick={() => handleSetPeqMode(mId)}
                    className={`py-1.5 rounded-lg text-[10px] font-mono font-semibold border transition-all text-center ${
                      isActive
                        ? 'border-indigo-500/60 bg-indigo-600/30 text-indigo-200 shadow-sm'
                        : 'border-border-subtle bg-surface-2 text-slate-400 hover:text-white hover:border-border-prominent'
                    }`}
                  >
                    {mId}
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
