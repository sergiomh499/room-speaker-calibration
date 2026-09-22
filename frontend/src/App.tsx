import React, { lazy, Suspense } from 'react';
import { CalibrationProvider, useCalibration } from './context/CalibrationContext';
import { Topbar } from './components/layout/Topbar';
import { HomeView } from './views/HomeView';
import { CheckCircle2, AlertCircle, Info, AlertTriangle, Loader2 } from 'lucide-react';
import { MobileAvrRemote } from './components/mobile/MobileAvrRemote';
import { MusicStreamingHub } from './components/music/MusicStreamingHub';

const CalibrateView = lazy(() => import('./views/CalibrateView').then(m => ({ default: m.CalibrateView })));
const HistoryView = lazy(() => import('./views/HistoryView').then(m => ({ default: m.HistoryView })));
const SettingsView = lazy(() => import('./views/SettingsView').then(m => ({ default: m.SettingsView })));

const ViewFallback: React.FC = () => (
  <div className="flex flex-col items-center justify-center min-h-[400px] gap-3 text-slate-400 font-mono text-xs">
    <Loader2 className="w-6 h-6 animate-spin text-indigo-400" />
    <span>Cargando módulo de calibración...</span>
  </div>
);

const AppContent: React.FC = () => {
  const { view, toasts } = useCalibration();

  return (
    <div className="min-h-screen flex flex-col bg-surface-0 text-slate-100 selection:bg-indigo-500/30">
      <Topbar />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 pt-4 pb-[calc(5.5rem+max(env(safe-area-inset-bottom,0px),16px))] md:pb-12 safe-left safe-right">
        <Suspense fallback={<ViewFallback />}>
          {view === 'home' && <HomeView />}
          {view === 'calibrate' && <CalibrateView />}
          {view === 'music' && <MusicStreamingHub />}
          {view === 'history' && <HistoryView />}
          {view === 'settings' && <SettingsView />}
        </Suspense>
      </main>
      {/* Mobile AVR Remote widget */}
      <MobileAvrRemote />
      {/* Minimalist Floating Pill Toast (iOS Dynamic Island Style) */}
      <div className="fixed top-[max(env(safe-area-inset-top,0px),12px)] left-1/2 -translate-x-1/2 z-50 flex flex-col items-center gap-1.5 pointer-events-none max-w-[90vw] sm:max-w-md w-full px-4">
        {toasts.slice(-2).map(t => (
          <div
            key={t.id}
            className={`pointer-events-auto flex items-center gap-2 px-3.5 py-1.5 rounded-full border shadow-xl backdrop-blur-2xl text-[11px] font-sans font-medium transition-all duration-300 animate-in fade-in slide-in-from-top-3 ${
              t.type === 'success'
                ? 'bg-slate-900/85 border-emerald-500/30 text-emerald-300 shadow-emerald-950/20'
                : t.type === 'error'
                ? 'bg-slate-900/85 border-rose-500/30 text-rose-300 shadow-rose-950/20'
                : t.type === 'warn'
                ? 'bg-slate-900/85 border-amber-500/30 text-amber-300 shadow-amber-950/20'
                : 'bg-slate-900/85 border-slate-700/40 text-slate-200 shadow-black/40'
            }`}
          >
            {t.type === 'success' && <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />}
            {t.type === 'error' && <AlertCircle className="w-3.5 h-3.5 text-rose-400 shrink-0" />}
            {t.type === 'warn' && <AlertTriangle className="w-3.5 h-3.5 text-amber-400 shrink-0" />}
            {t.type === 'info' && <Info className="w-3.5 h-3.5 text-sky-400 shrink-0" />}
            <span className="truncate">{t.message}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

export const App: React.FC = () => {
  return (
    <CalibrationProvider>
      <AppContent />
    </CalibrationProvider>
  );
};

export default App;
