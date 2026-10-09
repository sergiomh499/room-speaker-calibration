import React, { useState } from 'react';
import {
  Volume2,
  VolumeX,
  ShieldCheck,
  RotateCcw,
  Power,
  Tv,
  Radio,
  Sparkles,
  Sliders,
} from 'lucide-react';
import { useCalibration } from '../context/CalibrationContext';
import { useAvrControls } from '../services/avrControls';
import { HapticVolumeDial } from '../components/audio/HapticVolumeDial';
import { Button } from '../components/ui/Button';
import { Pill } from '../components/ui/Pill';

export const AvrRemoteView: React.FC = () => {
  const {
    avrStatus,
    refreshStatus,
    toast,
  } = useCalibration();

  const {
    currentVol,
    isMuted,
    handleVolumeChange,
    handleToggleMute,
    handleSelectInput,
    handleSetPeqMode,
  } = useAvrControls({ avrStatus, refreshStatus, toast });

  const [restoringAvr, setRestoringAvr] = useState<boolean>(false);
  const [checkingPreflight, setCheckingPreflight] = useState<boolean>(false);

  const handleTogglePower = async () => {
    try {
      const nextPower = avrStatus.avr_power === 'On' ? 'Standby' : 'On';
      const xml = `<YAMAHA_AV cmd="PUT"><Main_Zone><Power_Control><Power>${nextPower}</Power></Power_Control></Main_Zone></YAMAHA_AV>`;
      await fetch('/api/send_cmd', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ xml })
      });
      toast(`Receptor: ${nextPower}`, 'info');
      await refreshStatus();
    } catch {
      toast('Error al cambiar encendido del receptor', 'error');
    }
  };

  const handleRestoreSnapshot = async () => {
    setRestoringAvr(true);
    try {
      const res = await fetch('/api/restore_snapshot', { method: 'POST' });
      const data = await res.json();
      if (data.ok) {
        toast('✓ Estado anterior del receptor restaurado con éxito', 'success');
        await refreshStatus();
      } else {
        toast('Aviso al restaurar snapshot del receptor', 'warn');
      }
    } catch {
      toast('Fallo de red al restaurar snapshot', 'error');
    } finally {
      setRestoringAvr(false);
    }
  };

  const handlePreflightCheck = async () => {
    setCheckingPreflight(true);
    try {
      const res = await fetch('/api/preflight_check');
      const data = await res.json();
      if (data.ok) {
        toast(`✓ Diagnóstico OK: Entrada ${data.input || 'AV4'}, PEQ: ${data.peq_mode || 'Manual'}`, 'success');
        await refreshStatus();
      } else {
        toast('Fallo en verificación previa del receptor', 'error');
      }
    } catch {
      toast('Error de conexión con el receptor', 'error');
    } finally {
      setCheckingPreflight(false);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto pb-12">
      {/* Cabecera Principal */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-5 rounded-2xl bg-zinc-900 border border-zinc-800">
        <div>
          <div className="flex items-center gap-2">
            <span className={`w-2.5 h-2.5 rounded-full ${avrStatus.online ? 'bg-emerald-400 animate-pulse' : 'bg-rose-500'}`} />
            <h1 className="text-lg font-bold text-white font-mono">Yamaha RX-V673 Remote</h1>
          </div>
          <p className="text-xs text-zinc-400 font-mono mt-1">
            Control directo en tiempo real por red local (YNC HTTP / 192.168.1.43)
          </p>
        </div>
        <div className="flex items-center gap-2 w-full sm:w-auto">
          <Button
            size="sm"
            variant={avrStatus.avr_power === 'On' ? 'outline' : 'primary'}
            onClick={handleTogglePower}
            icon={<Power className="w-4 h-4" />}
          >
            {avrStatus.avr_power === 'On' ? 'Apagar' : 'Encender'}
          </Button>
          <Button
            size="sm"
            variant="ghost"
            onClick={handlePreflightCheck}
            disabled={checkingPreflight}
            icon={<ShieldCheck className="w-4 h-4 text-emerald-400" />}
          >
            {checkingPreflight ? 'Verificando...' : 'Diagnóstico'}
          </Button>
        </div>
      </div>

      {/* Control Maestro de Volumen y Silencio */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="p-6 rounded-2xl bg-zinc-900 border border-zinc-800 flex flex-col items-center justify-center space-y-4">
          <span className="text-xs font-mono uppercase tracking-wider text-zinc-400">Volumen Maestro (±0.5 dB)</span>
          <HapticVolumeDial
            volumeDb={currentVol}
            onChange={handleVolumeChange}
            onToggleMute={handleToggleMute}
            isMuted={isMuted}
          />
          <div className="flex items-center gap-3">
            <Button
              size="sm"
              variant={isMuted ? 'outline' : 'ghost'}
              onClick={handleToggleMute}
              icon={isMuted ? <VolumeX className="w-4 h-4 text-rose-400" /> : <Volume2 className="w-4 h-4" />}
            >
              {isMuted ? 'Silenciado (MUTE)' : 'Silenciar'}
            </Button>
          </div>
        </div>

        {/* Comparación Acústica A/B PEQ */}
        <div className="p-6 rounded-2xl bg-zinc-900 border border-zinc-800 flex flex-col justify-between space-y-5">
          <div>
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono uppercase tracking-wider text-zinc-400">Modo DSP Acústico (Audición A/B)</span>
              <Pill variant="neutral" size="sm">{avrStatus.avr_peq_mode}</Pill>
            </div>
            <p className="text-xs text-zinc-400 mt-2 leading-relaxed">
              Alterna instantáneamente entre la calibración activa y el audio sin procesar para evaluar la corrección acústica.
            </p>
          </div>

          <div className="grid grid-cols-3 gap-2">
            {[
              { id: 'Manual', label: 'Manual PEQ', desc: 'Calibrado' },
              { id: 'Through', label: 'Through', desc: 'Bypass puro' },
              { id: 'Flat', label: 'YPAO Flat', desc: 'Hardware' }
            ].map((m) => {
              const active = (avrStatus.avr_peq_mode || '').toLowerCase().includes(m.id.toLowerCase());
              return (
                <button
                  key={m.id}
                  type="button"
                  onClick={() => handleSetPeqMode(m.id as 'Manual' | 'Through' | 'Flat')}
                  className={`p-3 rounded-xl border text-left font-mono transition-all ${
                    active
                      ? 'border-orange-500/80 bg-orange-500/15 text-orange-200'
                      : 'border-zinc-800 bg-zinc-950/60 text-zinc-400 hover:border-zinc-700'
                  }`}
                >
                  <div className="text-xs font-bold">{m.label}</div>
                  <div className="text-[10px] text-zinc-500">{m.desc}</div>
                </button>
              );
            })}
          </div>

          <div className="pt-2 border-t border-zinc-800/80 flex items-center justify-between">
            <span className="text-xs text-zinc-500 font-mono">Restaurar estado previo:</span>
            <Button
              size="sm"
              variant="ghost"
              onClick={handleRestoreSnapshot}
              disabled={restoringAvr}
              icon={<RotateCcw className="w-3.5 h-3.5 text-zinc-400" />}
            >
              {restoringAvr ? 'Restaurando...' : 'Rollback NVRAM'}
            </Button>
          </div>
        </div>
      </div>

      {/* Selector de Entrada y Escenas */}
      <div className="p-6 rounded-2xl bg-zinc-900 border border-zinc-800 space-y-4">
        <span className="text-xs font-mono uppercase tracking-wider text-zinc-400">Selector de Entrada</span>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
          {[
            { id: 'AV4', label: 'AV4 (TV ARC)', icon: <Tv className="w-4 h-4" /> },
            { id: 'V-AUX', label: 'V-AUX (Front)', icon: <Radio className="w-4 h-4" /> },
            { id: 'HDMI1', label: 'HDMI 1', icon: <Sparkles className="w-4 h-4" /> },
            { id: 'AUDIO1', label: 'Audio 1', icon: <Sliders className="w-4 h-4" /> },
          ].map((inp) => {
            const active = avrStatus.avr_input === inp.id;
            return (
              <button
                key={inp.id}
                type="button"
                onClick={() => handleSelectInput(inp.id)}
                className={`flex items-center gap-2 p-3 rounded-xl border font-mono text-xs transition-all ${
                  active
                    ? 'border-orange-500 bg-orange-500/10 text-white font-semibold'
                    : 'border-zinc-800 bg-zinc-950/40 text-zinc-400 hover:border-zinc-700 hover:text-zinc-200'
                }`}
              >
                {inp.icon}
                <span>{inp.label}</span>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
};
