import React from 'react';
import { CalibrationProvider, useCalibration } from './context/CalibrationContext';
import { Topbar } from './components/layout/Topbar';
import { HomeView } from './views/HomeView';
import { CalibrateView } from './views/CalibrateView';
import { HistoryView } from './views/HistoryView';
import { SettingsView } from './views/SettingsView';
import { CheckCircle2, AlertCircle, Info, AlertTriangle } from 'lucide-react';

const AppContent: React.FC = () => {
  const { view, toasts } = useCalibration();

  return (
    <div className="min-h-screen flex flex-col bg-surface-0 text-slate-100 selection:bg-indigo-500/30">
      <Topbar />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 pt-6 pb-24 md:pb-12">
        {view === 'home' && <HomeView />}
        {view === 'calibrate' && <CalibrateView />}
        {view === 'history' && <HistoryView />}
        {view === 'settings' && <SettingsView />}
      </main>

      {/* Floating Toast Container */}
      <div className="fixed bottom-16 md:bottom-6 right-4 z-50 flex flex-col gap-2 max-w-sm w-full pointer-events-none">
        {toasts.map(t => (
          <div
            key={t.id}
            className={`pointer-events-auto flex items-center gap-2.5 p-3 rounded-xl border shadow-2xl backdrop-blur text-xs font-mono transition-all animate-in fade-in slide-in-from-bottom-2 ${
              t.type === 'success'
                ? 'bg-emerald-950/90 border-emerald-500/40 text-emerald-200'
                : t.type === 'error'
                ? 'bg-rose-950/90 border-rose-500/40 text-rose-200'
                : t.type === 'warn'
                ? 'bg-amber-950/90 border-amber-500/40 text-amber-200'
                : 'bg-surface-2/95 border-border-strong text-slate-200'
            }`}
          >
            {t.type === 'success' && <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />}
            {t.type === 'error' && <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />}
            {t.type === 'warn' && <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />}
            {t.type === 'info' && <Info className="w-4 h-4 text-indigo-400 shrink-0" />}
            <span className="flex-1">{t.message}</span>
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
