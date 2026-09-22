import React, { useState } from 'react';
import { Volume2, VolumeX, Plus, Minus, Sliders, ChevronUp, ChevronDown } from 'lucide-react';
import { yamahaDirect } from '../../services/yamahaDirect';
import { useCalibration } from '../../context/CalibrationContext';

export const MobileAvrRemote: React.FC = () => {
  const { avrStatus, toast } = useCalibration();
  const [isOpen, setIsOpen] = useState(false);
  const [isMuted, setIsMuted] = useState(false);

  // Parsear volumen actual
  const currentVol = typeof avrStatus.avr_volume_db === 'number'
    ? avrStatus.avr_volume_db
    : parseFloat(String(avrStatus.avr_volume_db)) || -35.0;
  const handleVolumeChange = async (delta: number) => {
    const nextVol = Math.round((currentVol + delta) * 2) / 2;
    await yamahaDirect.setVolume(nextVol);
    toast(`Volumen: ${nextVol > 0 ? '+' : ''}${nextVol.toFixed(1)} dB`, 'info');
  };

  const handleToggleMute = async () => {
    const nextMute = !isMuted;
    setIsMuted(nextMute);
    const xml = `<YAMAHA_AV cmd="PUT"><Main_Zone><Volume><Mute>${nextMute ? 'On' : 'Off'}</Mute></Volume></Main_Zone></YAMAHA_AV>`;
    await yamahaDirect.sendYncXml(xml);
    toast(nextMute ? 'Receptor silenciado (Mute)' : 'Sonido restaurado', 'info');
  };

  const handleSceneSelect = async (sceneNum: number) => {
    await yamahaDirect.selectScene(sceneNum);
    toast(`Escena ${sceneNum} activada`, 'success');
  };

  const handleTogglePeq = async () => {
    const nextMode = avrStatus.avr_peq_mode === 'Manual' ? 'Through' : 'Manual';
    await yamahaDirect.setPeqMode(nextMode);
    toast(`Modo PEQ: ${nextMode}`, 'info');
  };

  return (
    <div className="fixed bottom-[calc(4.5rem+max(env(safe-area-inset-bottom,0px),12px))] sm:bottom-6 left-4 z-40">
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
              <span className="text-white font-bold text-sm">{avrStatus.avr_volume_db} dB</span>
            </div>
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => handleVolumeChange(-1.0)}
                className="flex-1 py-2.5 rounded-xl border border-border-subtle bg-surface-2 hover:bg-surface-2/80 active:scale-95 text-white flex items-center justify-center font-bold text-sm shadow-sm transition-all"
              >
                <Minus className="w-4 h-4" />
              </button>
              <button
                type="button"
                onClick={handleToggleMute}
                className={`px-3 py-2.5 rounded-xl border transition-all ${
                  isMuted
                    ? 'border-rose-500/50 bg-rose-500/20 text-rose-300'
                    : 'border-border-subtle bg-surface-2 text-slate-300 hover:text-white'
                }`}
              >
                {isMuted ? <VolumeX className="w-4 h-4" /> : <Volume2 className="w-4 h-4" />}
              </button>
              <button
                type="button"
                onClick={() => handleVolumeChange(1.0)}
                className="flex-1 py-2.5 rounded-xl border border-border-subtle bg-surface-2 hover:bg-surface-2/80 active:scale-95 text-white flex items-center justify-center font-bold text-sm shadow-sm transition-all"
              >
                <Plus className="w-4 h-4" />
              </button>
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

          {/* PEQ Bypass / Active Switch */}
          <div className="flex items-center justify-between pt-1">
            <span className="text-xs font-mono text-slate-400">Modo PEQ</span>
            <button
              type="button"
              onClick={handleTogglePeq}
              className={`px-3 py-1 rounded-lg text-xs font-mono font-semibold border transition-all ${
                avrStatus.avr_peq_mode === 'Manual'
                  ? 'border-indigo-500/50 bg-indigo-600/20 text-indigo-300'
                  : 'border-border-subtle bg-surface-2 text-slate-400'
              }`}
            >
              {avrStatus.avr_peq_mode}
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
