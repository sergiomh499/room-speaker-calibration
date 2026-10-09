import React from 'react';
import { Sliders, History, Settings, Activity, Volume2, VolumeX, Radio, Music } from 'lucide-react';
import { useCalibration, AppView } from '../../context/CalibrationContext';
import { Pill } from '../ui/Pill';

export const Topbar: React.FC = () => {
  const { view, setView, avrStatus } = useCalibration();
  const isMuted =
    avrStatus.avr_mute === 'On' ||
    (typeof avrStatus.avr_volume_db === 'number'
      ? avrStatus.avr_volume_db <= -70
      : parseFloat(String(avrStatus.avr_volume_db)) <= -70);

  const navItems: Array<{ id: AppView; label: string; icon: React.ReactNode }> = [
    { id: 'control', label: 'Control', icon: <Radio className="w-4 h-4" /> },
    { id: 'calibrate', label: 'Calibrar', icon: <Sliders className="w-4 h-4" /> },
    { id: 'music', label: 'Música', icon: <Music className="w-4 h-4" /> },
    { id: 'history', label: 'Historial', icon: <History className="w-4 h-4" /> },
    { id: 'settings', label: 'Ajustes', icon: <Settings className="w-4 h-4" /> },
  ];

  return (
    <>
      {/* Desktop & Tablet Topbar */}
      <header className="sticky top-0 z-40 w-full bg-zinc-950/95 backdrop-blur-md border-b border-zinc-800 safe-top">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 h-16 sm:h-18 flex items-center justify-between gap-4">
          {/* Brand */}
          <div
            onClick={() => setView('control')}
            className="flex items-center gap-3 cursor-pointer select-none group"
          >
            <div className="w-9 h-9 rounded-lg bg-zinc-900 border border-zinc-700 flex items-center justify-center group-hover:border-orange-500/60 transition-colors">
              <Activity className="w-5 h-5 text-orange-400" />
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <span className="text-base font-bold tracking-tight text-white font-mono">OCTAVE</span>
                <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-orange-500/20 text-orange-300 border border-orange-500/30">
                  Hi-Fi
                </span>
              </div>
              <div className="text-[10px] text-zinc-500 font-mono hidden sm:block">
                Acoustic Studio & PEQ Engine
              </div>
            </div>
          </div>

          {/* Nav Items (Desktop) */}
          <nav className="hidden md:flex items-center gap-1 bg-zinc-900 border border-zinc-800 p-1 rounded-lg">
            {navItems.map(item => {
              const active = view === item.id;
              return (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => setView(item.id)}
                  className={`flex items-center gap-2 px-3.5 py-1.5 rounded-md text-xs font-mono transition-all ${
                    active
                      ? 'bg-orange-600 text-white shadow-sm'
                      : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800'
                  }`}
                >
                  {item.icon}
                  <span>{item.label}</span>
                </button>
              );
            })}
          </nav>

          {/* AVR Status Chip */}
          <div className="flex items-center gap-2">
            <div className="hidden sm:flex items-center gap-2 bg-zinc-900 border border-zinc-800 px-3 py-1.5 rounded-lg">
              <span className={`w-2 h-2 rounded-full ${avrStatus.online ? 'bg-emerald-400 animate-pulse' : 'bg-rose-500'}`} />
              <div className="text-xs font-mono">
                <span className="text-zinc-500">Yamaha RX-V673: </span>
                <span className="text-zinc-200 font-semibold">{avrStatus.avr_power}</span>
                <span className="text-zinc-600 mx-1">|</span>
                <span className="text-orange-400">{avrStatus.avr_peq_mode}</span>
              </div>
              {avrStatus.avr_volume_db !== '—' && (
                <Pill
                  variant={isMuted ? 'rose' : 'neutral'}
                  size="sm"
                  icon={isMuted ? <VolumeX className="w-3 h-3 text-rose-400" /> : <Volume2 className="w-3 h-3" />}
                >
                  {isMuted ? 'MUTE' : `${avrStatus.avr_volume_db} dB`}
                </Pill>
              )}
            </div>

            <div className="sm:hidden flex items-center gap-1.5">
              <Pill variant={avrStatus.online ? 'emerald' : 'rose'} size="sm" icon={<Radio className="w-3 h-3" />}>
                {avrStatus.online ? 'AVR ON' : 'AVR OFF'}
              </Pill>
            </div>
          </div>
        </div>
      </header>

      {/* Mobile Bottom Navigation */}
      <div className="md:hidden fixed bottom-[max(env(safe-area-inset-bottom,0px),12px)] left-0 right-0 z-50 flex justify-center px-4 pointer-events-none">
        <nav className="pointer-events-auto w-full max-w-sm flex items-center justify-around px-2 py-1.5 rounded-2xl bg-zinc-950/90 backdrop-blur-2xl border border-zinc-800 shadow-[0_8px_32px_0_rgba(0,0,0,0.6)]">
          {navItems.map(item => {
            const active = view === item.id;
            return (
              <button
                key={item.id}
                type="button"
                onClick={() => setView(item.id)}
                className={`relative flex flex-col items-center justify-center flex-1 py-1 rounded-xl transition-all duration-200 ${
                  active ? 'text-white' : 'text-zinc-500 hover:text-zinc-300'
                }`}
              >
                {active && (
                  <div className="absolute inset-0 bg-orange-500/10 rounded-xl border border-orange-500/30 -z-10" />
                )}
                <div className={`p-1 transition-transform duration-200 ${active ? 'scale-110 text-orange-400' : ''}`}>
                  {item.icon}
                </div>
                <span className={`text-[10px] tracking-tight mt-0.5 font-mono ${active ? 'font-semibold text-orange-300' : 'font-normal text-zinc-500'}`}>
                  {item.label}
                </span>
              </button>
            );
          })}
        </nav>
      </div>
    </>
  );
};
