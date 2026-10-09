import React, { useState, useEffect } from 'react';
import {
  Sliders,
  Volume2,
  VolumeX,
  ShieldCheck,
  RotateCcw,
  Zap,
  Power,
  Tv,
} from 'lucide-react';
import { useCalibration } from '../context/CalibrationContext';
import { useAvrControls } from '../services/avrControls';
import { HapticVolumeDial } from '../components/audio/HapticVolumeDial';
import { Button } from '../components/ui/Button';
import { Pill } from '../components/ui/Pill';
import { FrequencyGraph, CurveDataPoint } from '../components/charts/FrequencyGraph';
import { api } from '../services/api';

export const HomeView: React.FC = () => {
  const {
    setView,
    avrStatus,
    refreshStatus,
    profiles,
    activeProfileId,
    setActiveProfileId,
    toast,
  } = useCalibration();

  const {
    currentVol,
    isMuted,
    handleVolumeChange,
    handleToggleMute,
    handleSelectInput,
    handleSceneSelect,
    handleSetPeqMode,
  } = useAvrControls({ avrStatus, refreshStatus, toast });

  const [curveData, setCurveData] = useState<CurveDataPoint[]>([]);
  const [deploying, setDeploying] = useState<boolean>(false);
  const [restoringAvr, setRestoringAvr] = useState<boolean>(false);
  const [checkingPreflight, setCheckingPreflight] = useState<boolean>(false);
  const [togglingDrc, setTogglingDrc] = useState<boolean>(false);

  useEffect(() => {
    let isMounted = true;
    const profileToFetch = activeProfileId || 'harman_wide_room';
    api
      .getMeasuredCurve(profileToFetch)
      .then((res) => {
        if (!isMounted) return;
        if (res && res.freqs && res.freqs.length > 0) {
          const points: CurveDataPoint[] = [];
          for (let i = 0; i < res.freqs.length; i += 2) {
            const corr = res.corrected_l?.[i] ?? res.simulated_l?.[i] ?? res.simulated_avg?.[i];
            const meas = res.measured_l?.[i] ?? res.measured_avg?.[i];
            const tgt = res.target?.[i];
            points.push({
              freq: Math.round(res.freqs[i]),
              measured: meas !== undefined && !isNaN(meas) ? Math.round(meas * 10) / 10 : undefined,
              target: tgt !== undefined && !isNaN(tgt) ? Math.round(tgt * 10) / 10 : undefined,
              corrected: corr !== undefined && !isNaN(corr) ? Math.round(corr * 10) / 10 : undefined,
            });
          }
          setCurveData(points);
        } else {
          setCurveData([]);
        }
      })
      .catch(() => {
        if (isMounted) setCurveData([]);
      });

    return () => {
      isMounted = false;
    };
  }, [activeProfileId]);

  const handleDeployProfile = async () => {
    setDeploying(true);
    try {
      await api.deployPEQ(activeProfileId);
      toast(
        `✓ Perfil '${profiles.find((p) => p.id === activeProfileId)?.name || activeProfileId}' aplicado al Yamaha RX-V673`,
        'success'
      );
    } catch (err: any) {
      toast(`Error al aplicar perfil: ${err.message || 'Error de red'}`, 'warn');
    } finally {
      setDeploying(false);
    }
  };

  // Quick Action handlers (Step 5)
  const handleRestoreAvr = async () => {
    setRestoringAvr(true);
    try {
      await api.restoreAvrMode();
      toast('Estado previo del Yamaha restaurado con éxito', 'success');
      await refreshStatus();
    } catch (err: any) {
      toast(`Error al restaurar AVR: ${err.message || 'Error de red'}`, 'warn');
    } finally {
      setRestoringAvr(false);
    }
  };

  const handlePreflight = async () => {
    setCheckingPreflight(true);
    try {
      const res = await api.preflightCheck(false);
      if (res && res.ok) {
        toast('AVR verificado correctamente y en línea', 'success');
      } else {
        toast(`Verificación AVR: ${res?.message || 'Advertencia de estado'}`, 'warn');
      }
      await refreshStatus();
    } catch (err: any) {
      toast(`Error de verificación: ${err.message || 'AVR inalcanzable'}`, 'error');
    } finally {
      setCheckingPreflight(false);
    }
  };

  const handleToggleDrc = async () => {
    setTogglingDrc(true);
    try {
      const isDrcOn = avrStatus.avr_drc === 'On' || avrStatus.avr_drc === 'Auto';
      const nextDrcVal = isDrcOn ? 'Off' : 'Auto';
      const xml = `<YAMAHA_AV cmd="PUT"><Main_Zone><Sound_Video><Adaptive_DRC>${nextDrcVal}</Adaptive_DRC></Sound_Video></Main_Zone></YAMAHA_AV>`;
      await api.sendDirectAvrXml(xml);
      toast(`Adaptive DRC: ${nextDrcVal === 'Auto' ? 'Activado (Auto)' : 'Desactivado'}`, 'info');
      await refreshStatus();
    } catch (err: any) {
      toast(`Error al conmutar DRC: ${err.message || 'Fallo de red'}`, 'warn');
    } finally {
      setTogglingDrc(false);
    }
  };

  const isDrcActive = avrStatus.avr_drc === 'On' || avrStatus.avr_drc === 'Auto';

  return (
    <div className="space-y-6 pb-28 md:pb-12">
      {/* 1. AVR Status Bar */}
      <div className="p-4 rounded-lg bg-zinc-950 border border-zinc-800 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <span
              className={`w-2.5 h-2.5 rounded-full ${
                avrStatus.online ? 'bg-emerald-400 animate-pulse' : 'bg-rose-500'
              }`}
            />
            <span className="text-sm font-bold text-white font-mono tracking-tight">
              Yamaha RX-V673
            </span>
          </div>
          <div className="flex items-center gap-1.5 text-xs font-mono">
            <Pill variant={avrStatus.avr_power === 'On' ? 'emerald' : 'neutral'} size="sm">
              <Power className="w-3 h-3 mr-1 inline" />
              {avrStatus.avr_power}
            </Pill>
            <Pill variant="cyan" size="sm">
              <Tv className="w-3 h-3 mr-1 inline" />
              {avrStatus.avr_input || 'AV4'}
            </Pill>
            <Pill variant="neutral" size="sm" className="border-orange-500/60 text-orange-300">
              {avrStatus.avr_peq_mode}
            </Pill>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Pill
            variant={isMuted ? 'rose' : 'neutral'}
            size="md"
            icon={isMuted ? <VolumeX className="w-4 h-4" /> : <Volume2 className="w-4 h-4" />}
          >
            <span className="font-bold text-sm">
              {currentVol > 0 ? '+' : ''}
              {currentVol.toFixed(1)} dB
            </span>
            {isMuted && <span className="ml-1 text-[10px] text-rose-300 uppercase font-mono">(Mute)</span>}
          </Pill>
        </div>
      </div>

      {/* 2. AVR Controls: Braun Minimalist Deck */}
      <div className="p-4 sm:p-6 rounded-2xl bg-zinc-950/90 border border-zinc-800 space-y-6 shadow-sm">
        {/* Central Rotary Haptic Volume Dial */}
        <HapticVolumeDial
          volumeDb={currentVol}
          isMuted={isMuted}
          onChange={(newVol) => {
            const delta = newVol - currentVol;
            handleVolumeChange(delta);
          }}
          onToggleMute={handleToggleMute}
        />

        {/* Inputs Grid (Braun Mechanical Push-Buttons) */}
        <div className="space-y-2 pt-2 border-t border-zinc-800/80">
          <div className="flex justify-between items-center text-[10px] font-mono uppercase tracking-wider text-zinc-400">
            <span>Entrada de Audio</span>
            <span className="text-orange-400 font-semibold">{avrStatus.avr_input || 'AV4'}</span>
          </div>
          <div className="grid grid-cols-3 sm:grid-cols-6 gap-2">
            {[
              { id: 'AV4', label: 'AV4 (TV eARC)' },
              { id: 'HDMI1', label: 'HDMI 1' },
              { id: 'V-AUX', label: 'V-AUX' },
              { id: 'AUDIO1', label: 'AUDIO 1' },
              { id: 'NET', label: 'NET / DLNA' },
              { id: 'AirPlay', label: 'AirPlay' },
            ].map((inp) => {
              const active = (avrStatus.avr_input || '').toUpperCase() === inp.id.toUpperCase();
              return (
                <button
                  key={inp.id}
                  type="button"
                  onClick={() => handleSelectInput(inp.id)}
                  className={`py-2 px-2 rounded-lg border text-[11px] font-mono text-center transition-all truncate flex items-center justify-center gap-1.5 active:scale-95 ${
                    active
                      ? 'border-orange-500/80 bg-zinc-900 text-zinc-100 font-bold shadow-sm'
                      : 'border-zinc-800 bg-zinc-900/60 text-zinc-400 hover:text-zinc-200 hover:border-zinc-700'
                  }`}
                >
                  <span
                    className={`w-1.5 h-1.5 rounded-full ${
                      active ? 'bg-orange-500' : 'bg-transparent'
                    }`}
                  />
                  <span>{inp.label}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Listening Modes / Scenes (Braun Industrial Tactile Switches) */}
        <div className="space-y-2 pt-1 border-t border-zinc-800/80">
          <div className="flex justify-between items-center text-[10px] font-mono uppercase tracking-wider text-zinc-400">
            <span>Escenas de Hardware</span>
            <span className="text-zinc-500 text-[9px]">Ajusta Escena + Modo PEQ</span>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
            {[
              { num: 1, label: '1 Música', desc: 'Manual PEQ' },
              { num: 2, label: '2 Cine', desc: 'Manual PEQ' },
              { num: 3, label: '3 Gaming', desc: 'Manual PEQ' },
              { num: 4, label: '4 Pure Direct', desc: 'Through PEQ' },
            ].map((s) => (
              <button
                key={s.num}
                type="button"
                onClick={() => handleSceneSelect(s.num)}
                className="py-2.5 px-3 rounded-lg border border-zinc-800 bg-zinc-900/60 hover:border-zinc-700 hover:bg-zinc-900 text-left transition-all active:scale-[0.98]"
              >
                <div className="font-mono text-xs font-semibold text-zinc-200 flex items-center justify-between">
                  <span>{s.label}</span>
                  <span className="text-[9px] text-zinc-500 font-normal">CH 1-4</span>
                </div>
                <div className="text-[10px] font-mono text-orange-400/90 mt-0.5">{s.desc}</div>
              </button>
            ))}
          </div>
        </div>

        {/* PEQ Modes Grid */}
        <div className="space-y-2 pt-1 border-t border-zinc-800/80">
          <div className="flex justify-between items-center text-[10px] font-mono uppercase tracking-wider text-zinc-400">
            <span>Modo PEQ Hardware</span>
            <span className="text-orange-400 font-bold">{avrStatus.avr_peq_mode}</span>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
            {(['Manual', 'Natural', 'Flat', 'Through'] as const).map((mId) => {
              const isActive = (avrStatus.avr_peq_mode || '').toLowerCase().includes(mId.toLowerCase());
              return (
                <button
                  key={mId}
                  type="button"
                  onClick={() => handleSetPeqMode(mId)}
                  className={`py-2 px-2 rounded-lg text-xs font-mono font-semibold border transition-all text-center active:scale-95 ${
                    isActive
                      ? 'border-orange-500/80 bg-zinc-900 text-zinc-100 shadow-sm'
                      : 'border-zinc-800 bg-zinc-900/60 text-zinc-400 hover:text-zinc-200 hover:border-zinc-700'
                  }`}
                >
                  {mId}
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* 3. Quick Actions (Braun tactile matrix) */}
      <div className="space-y-2">
        <span className="text-[10px] font-mono text-zinc-500 uppercase tracking-widest px-1">
          Funciones del Sistema
        </span>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
          <button
            type="button"
            onClick={() => setView('calibrate')}
            className="p-3 rounded-lg border border-zinc-800 bg-zinc-950/80 hover:border-zinc-700 text-xs font-mono flex flex-col items-center gap-1.5 text-zinc-300 hover:text-white transition-all active:scale-[0.98]"
          >
            <Sliders className="w-4 h-4 text-orange-400" />
            <span>Calibrar Sala</span>
          </button>

          <button
            type="button"
            disabled={restoringAvr}
            onClick={handleRestoreAvr}
            className="p-3 rounded-lg border border-zinc-800 bg-zinc-950/80 hover:border-zinc-700 text-xs font-mono flex flex-col items-center gap-1.5 text-zinc-300 hover:text-white transition-all active:scale-[0.98] disabled:opacity-50"
          >
            <RotateCcw className={`w-4 h-4 ${restoringAvr ? 'animate-spin text-orange-400' : 'text-zinc-400'}`} />
            <span>{restoringAvr ? 'Restaurando...' : 'Restaurar Estado'}</span>
          </button>

          <button
            type="button"
            disabled={checkingPreflight}
            onClick={handlePreflight}
            className="p-3 rounded-lg border border-zinc-800 bg-zinc-950/80 hover:border-zinc-700 text-xs font-mono flex flex-col items-center gap-1.5 text-zinc-300 hover:text-white transition-all active:scale-[0.98] disabled:opacity-50"
          >
            <ShieldCheck className={`w-4 h-4 text-emerald-400 ${checkingPreflight ? 'animate-pulse' : ''}`} />
            <span>{checkingPreflight ? 'Verificando...' : 'Verificar AVR'}</span>
          </button>

          <button
            type="button"
            disabled={togglingDrc}
            onClick={handleToggleDrc}
            className={`p-3 rounded-lg border text-xs font-mono flex flex-col items-center gap-1.5 transition-all active:scale-[0.98] disabled:opacity-50 ${
              isDrcActive
                ? 'border-orange-500/80 bg-orange-500/10 text-orange-300'
                : 'border-zinc-800 bg-zinc-950/80 hover:border-zinc-700 text-zinc-300 hover:text-white'
            }`}
          >
            <Zap className={`w-4 h-4 ${isDrcActive ? 'text-orange-400 fill-orange-400' : 'text-zinc-500'}`} />
            <span>DRC: {isDrcActive ? 'On (Auto)' : 'Off'}</span>
          </button>
        </div>
      </div>

      {/* 4. Profile Selector & Deploy */}
      <div id="perfiles-peq-section" className="space-y-3 pt-2">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <span className="text-[10px] font-mono text-zinc-500 uppercase tracking-widest block">
              Curvas Acústicas Objetivo
            </span>
            <span className="text-sm font-semibold text-zinc-100 font-mono">
              {profiles.find((p) => p.id === activeProfileId)?.name?.split('(')[0]?.trim() || activeProfileId}
            </span>
          </div>
          <Button
            variant="primary"
            size="sm"
            loading={deploying}
            onClick={handleDeployProfile}
            className="self-start sm:self-auto bg-orange-600 hover:bg-orange-500 text-white font-mono border-none"
          >
            Aplicar en Yamaha
          </Button>
        </div>

        {/* Profile Chips */}
        <div className="flex gap-2 overflow-x-auto pb-2 pt-1 scrollbar-none -mx-4 px-4 sm:mx-0 sm:px-0">
          {profiles.map((p) => {
            const isSelected = p.id === activeProfileId;
            return (
              <button
                key={p.id}
                type="button"
                onClick={() => setActiveProfileId(p.id)}
                className={`shrink-0 flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-mono whitespace-nowrap border transition-all active:scale-95 ${
                  isSelected
                    ? 'bg-zinc-900 border-orange-500 text-white font-bold'
                    : 'bg-zinc-950/80 border-zinc-800 text-zinc-400 hover:text-zinc-200 hover:border-zinc-700'
                }`}
              >
                <div className={`w-1.5 h-1.5 rounded-full ${isSelected ? 'bg-orange-500' : 'bg-zinc-600'}`} />
                <span className="text-zinc-200">{p.name.split('(')[0].trim()}</span>
              </button>
            );
          })}
        </div>

        {/* Active Profile Info */}
        {profiles.find((p) => p.id === activeProfileId) && (
          <div className="p-3 rounded-lg bg-zinc-950 border border-zinc-800 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs">
            <p className="text-zinc-300 leading-relaxed max-w-2xl font-mono text-[11px]">
              <strong className="text-zinc-100">
                {profiles.find((p) => p.id === activeProfileId)?.name}:{' '}
              </strong>
              {profiles.find((p) => p.id === activeProfileId)?.description}
            </p>
            <span className="shrink-0 text-zinc-500 font-mono text-[10px] self-start sm:self-auto">
              Categoría:{' '}
              <strong className="text-orange-400">
                {profiles.find((p) => p.id === activeProfileId)?.category}
              </strong>
            </span>
          </div>
        )}
      </div>

      {/* 5. Main Acoustic Frequency Response Graph */}
      <FrequencyGraph
        title={`Respuesta Acústica & Curva: ${
          profiles.find((p) => p.id === activeProfileId)?.name?.split('(')[0]?.trim() || activeProfileId
        }`}
        data={curveData}
        height={260}
      />
    </div>
  );
};
