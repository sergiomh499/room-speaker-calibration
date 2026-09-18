import React, { useState } from 'react';
import { Mic, Cpu, Sliders } from 'lucide-react';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { useCalibration } from '../context/CalibrationContext';
import { api } from '../services/api';

export const SettingsView: React.FC = () => {
  const { toast } = useCalibration();
  const [micProfile, setMicProfile] = useState<string>('smartphone_cal');
  const [avrHost, setAvrHost] = useState<string>('192.168.1.43');
  const [smoothing, setSmoothing] = useState<string>('var');
  const [testingAvr, setTestingAvr] = useState<boolean>(false);

  const handleTestAvr = async () => {
    setTestingAvr(true);
    try {
      const res = await api.preflightCheck(true);
      if (res && res.power === 'On') {
        toast('Conexión con Yamaha RX-V673 verificada (Estado Acústico Limpio Enforzado).', 'success');
      } else {
        toast('Receptor conectado correctamente.', 'info');
      }
    } catch {
      toast('No se pudo contactar con el receptor Yamaha.', 'error');
    } finally {
      setTestingAvr(false);
    }
  };

  return (
    <div className="space-y-6 pb-20 md:pb-8">
      <div>
        <h2 className="text-2xl font-bold text-white tracking-tight">Ajustes & Parámetros del Sistema</h2>
        <p className="text-sm text-slate-400 mt-1 font-mono">
          Configuración de hardware acústico, compensación de transductor y motor de optimización.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Microphone Settings */}
        <Card
          title="Micrófono de Medición"
          subtitle="Curva de calibración y corrección de cápsula"
          icon={<Mic className="w-5 h-5 text-indigo-400" />}
        >
          <div className="space-y-4">
            <div>
              <label className="text-xs font-semibold text-slate-300 block mb-1.5">
                Perfil de Calibración
              </label>
              <select
                value={micProfile}
                onChange={e => setMicProfile(e.target.value)}
                className="w-full bg-surface-2 border border-border-subtle rounded-lg px-3 py-2 text-xs font-mono text-slate-200 focus:outline-none focus:border-indigo-500"
              >
                <option value="smartphone_cal">Pixel 9 Pro XL (Calibración Óptima Multi-Mic)</option>
                <option value="umik1_90deg">miniDSP UMIK-1 (90 Grados / Difuso)</option>
                <option value="umik1_0deg">miniDSP UMIK-1 (0 Grados / Directo)</option>
                <option value="generic_flat">Respuesta Plana Sin Compensar</option>
              </select>
            </div>

            <div className="p-3 rounded-lg bg-surface-2/40 border border-border-subtle text-xs text-slate-400 leading-relaxed font-mono">
              La curva compensa la atenuación de graves (&lt; 50 Hz) y la resonancia mecánica de alta frecuencia propia de la cápsula MEMS del smartphone.
            </div>
          </div>
        </Card>

        {/* AVR Connection */}
        <Card
          title="Receptor AV Yamaha"
          subtitle="Protocolo YNC (Yamaha Network Control)"
          icon={<Cpu className="w-5 h-5 text-emerald-400" />}
        >
          <div className="space-y-4">
            <div>
              <label className="text-xs font-semibold text-slate-300 block mb-1.5">
                Dirección IP en Red Local
              </label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={avrHost}
                  onChange={e => setAvrHost(e.target.value)}
                  className="flex-1 bg-surface-2 border border-border-subtle rounded-lg px-3 py-2 text-xs font-mono text-slate-200 focus:outline-none focus:border-indigo-500"
                />
                <Button
                  variant="outline"
                  size="sm"
                  loading={testingAvr}
                  onClick={handleTestAvr}
                >
                  Probar
                </Button>
              </div>
            </div>

            <div className="flex items-center justify-between p-3 rounded-lg bg-surface-2/40 border border-border-subtle font-mono text-xs">
              <span className="text-slate-400">Modelo detectado:</span>
              <span className="text-slate-200 font-bold">RX-V673 (Firmware 1.80)</span>
            </div>
          </div>
        </Card>

        {/* Advanced Optimizer Settings */}
        <Card
          title="Motor de Optimización PEQ"
          subtitle="Algoritmo Scipy SLSQP con restricciones NVRAM"
          icon={<Sliders className="w-5 h-5 text-amber-400" />}
          className="md:col-span-2"
        >
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-300 block">
                Suavizado Psicoacústico
              </label>
              <select
                value={smoothing}
                onChange={e => setSmoothing(e.target.value)}
                className="w-full bg-surface-2 border border-border-subtle rounded-lg px-3 py-2 text-xs font-mono text-slate-200 focus:outline-none focus:border-indigo-500"
              >
                <option value="var">Variable (1/48 oct en graves, 1/6 oct en agudos)</option>
                <option value="psychoacoustic">Psicoacústico Estándar (ERB)</option>
                <option value="1/6">1/6 de Octava</option>
                <option value="1/12">1/12 de Octava</option>
              </select>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-300 block">
                Ponderación Sweet Spot (P1)
              </label>
              <input
                type="text"
                disabled
                value="100% P1 (60% clúster + 40% perim)"
                className="w-full bg-surface-2/60 border border-border-subtle rounded-lg px-3 py-2 text-xs font-mono text-slate-400"
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-300 block">
                Límite de Ganancia Positiva
              </label>
              <input
                type="text"
                disabled
                value="+6.0 dB máximo (Anti-clipping)"
                className="w-full bg-surface-2/60 border border-border-subtle rounded-lg px-3 py-2 text-xs font-mono text-slate-400"
              />
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
};
