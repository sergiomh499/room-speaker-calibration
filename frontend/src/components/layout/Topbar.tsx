import React from 'react';
import { Home, Sliders, History, Settings, Activity, Volume2, Radio, Music } from 'lucide-react';
import { useCalibration, AppView } from '../../context/CalibrationContext';
import { Pill } from '../ui/Pill';

export const Topbar: React.FC = () => {
  const { view, setView, avrStatus } = useCalibration();

  const navItems: Array<{ id: AppView; label: string; icon: React.ReactNode }> = [
    { id: 'home', label: 'Sala', icon: <Home className="w-4 h-4" /> },
    { id: 'calibrate', label: 'Calibrar', icon: <Sliders className="w-4 h-4" /> },
    { id: 'music', label: 'Música', icon: <Music className="w-4 h-4" /> },
    { id: 'history', label: 'Historial', icon: <History className="w-4 h-4" /> },
    { id: 'settings', label: 'Ajustes', icon: <Settings className="w-4 h-4" /> },
  ];

  return (
    <>
      {/* Desktop & Tablet Topbar */}
      <header className="sticky top-0 z-40 w-full bg-surface-0/80 backdrop-blur-md border-b border-border-subtle">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between gap-4">
          {/* Brand */}
          <div
            onClick={() => setView('home')}
            className="flex items-center gap-3 cursor-pointer select-none group"
          >
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-500 via-indigo-600 to-indigo-800 flex items-center justify-center shadow-lg shadow-indigo-600/30 group-hover:scale-105 transition-transform">
              <Activity className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <span className="text-base font-bold tracking-tight text-white">OCTAVE</span>
                <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                  Hi-Fi
                </span>
              </div>
              <div className="text-[10px] text-slate-400 font-mono hidden sm:block">
                Acoustic Studio & PEQ Engine
              </div>
            </div>
          </div>

          {/* Nav Items (Desktop) */}
          <nav className="hidden md:flex items-center gap-1 bg-surface-1/80 border border-border-subtle p-1 rounded-xl">
            {navItems.map(item => {
              const active = view === item.id;
              return (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => setView(item.id)}
                  className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all ${
                    active
                      ? 'bg-indigo-600 text-white shadow-sm'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-surface-2'
                  }`}
                >
                  {item.icon}
                  <span>{item.label}</span>
                </button>
              );
            })}
          </nav>

          {/* AVR Status Pill */}
          <div className="flex items-center gap-2">
            <div className="hidden sm:flex items-center gap-2 bg-surface-1 border border-border-subtle px-3 py-1.5 rounded-lg">
              <span className={`w-2 h-2 rounded-full ${avrStatus.online ? 'bg-emerald-400 animate-pulse' : 'bg-rose-500'}`} />
              <div className="text-xs font-mono">
                <span className="text-slate-400">Yamaha RX-V673: </span>
                <span className="text-slate-200 font-semibold">{avrStatus.avr_power}</span>
                <span className="text-slate-500 mx-1">|</span>
                <span className="text-indigo-300">{avrStatus.avr_peq_mode}</span>
              </div>
              {avrStatus.avr_volume_db !== '—' && (
                <Pill variant="neutral" size="sm" icon={<Volume2 className="w-3 h-3" />}>
                  {avrStatus.avr_volume_db} dB
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

      {/* Mobile Bottom Navigation Bar */}
      <nav className="md:hidden fixed bottom-0 left-0 right-0 z-50 bg-surface-1/95 backdrop-blur-lg border-t border-border-strong px-2 py-2 flex justify-around items-center safe-bottom">
        {navItems.map(item => {
          const active = view === item.id;
          return (
            <button
              key={item.id}
              type="button"
              onClick={() => setView(item.id)}
              className={`flex flex-col items-center justify-center w-16 py-1 rounded-xl text-[11px] font-medium transition-colors ${
                active ? 'text-indigo-400 font-semibold' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <div className={`p-1.5 rounded-lg transition-transform ${active ? 'bg-indigo-500/20 scale-110' : ''}`}>
                {item.icon}
              </div>
              <span className="mt-0.5">{item.label}</span>
            </button>
          );
        })}
      </nav>
    </>
  );
};
