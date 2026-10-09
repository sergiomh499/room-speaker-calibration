import React, { useState, useEffect } from 'react';
import { Activity, RefreshCw, Layers, Table } from 'lucide-react';
import { useCalibration } from '../context/CalibrationContext';
import { FrequencyGraph, CurveDataPoint } from '../components/charts/FrequencyGraph';
import { identifyRoomModes } from '../services/dspEngine';
import { Button } from '../components/ui/Button';
import { Pill } from '../components/ui/Pill';
import { api } from '../services/api';

export const AcousticCurvesView: React.FC = () => {
  const { activeProfileId, toast } = useCalibration();
  const [curveData, setCurveData] = useState<CurveDataPoint[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [showTarget, setShowTarget] = useState<boolean>(true);
  const [showMeasured, setShowMeasured] = useState<boolean>(true);
  const [showCorrected, setShowCorrected] = useState<boolean>(true);

  const fetchCurves = async () => {
    setLoading(true);
    try {
      const profile = activeProfileId || 'harman_wide_room';
      const res = await api.getMeasuredCurve(profile);
      if (res && res.freqs && res.freqs.length > 0) {
        const points: CurveDataPoint[] = [];
        for (let i = 0; i < res.freqs.length; i++) {
          const meas = res.measured_l?.[i] ?? res.measured_avg?.[i];
          const tgt = res.target?.[i];
          const corr = res.corrected_l?.[i] ?? res.verified_l?.[i];
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
    } catch {
      toast('Aviso al cargar curvas acústicas reales', 'warn');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCurves();
  }, [activeProfileId]);

  return (
    <div className="space-y-6 max-w-5xl mx-auto pb-12">
      {/* Cabecera */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-5 rounded-2xl bg-zinc-900 border border-zinc-800">
        <div>
          <div className="flex items-center gap-2">
            <Activity className="w-5 h-5 text-orange-400" />
            <h1 className="text-lg font-bold text-white font-mono">Curvas Acústicas Reales</h1>
          </div>
          <p className="text-xs text-zinc-400 font-mono mt-1">
            Datos derivados exclusivamente de la física de la sala (sin aproximaciones sintéticas)
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Pill variant="neutral" size="sm">Perfil: {activeProfileId}</Pill>
          <Button
            size="sm"
            variant="ghost"
            onClick={fetchCurves}
            disabled={loading}
            icon={<RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />}
          >
            Actualizar
          </Button>
        </div>
      </div>

      {/* Controles de Capas de Curvas */}
      <div className="flex flex-wrap items-center gap-2 p-3 rounded-xl bg-zinc-900/60 border border-zinc-800/80 font-mono text-xs">
        <span className="text-zinc-500 mr-2 flex items-center gap-1.5">
          <Layers className="w-3.5 h-3.5 text-zinc-400" />
          <span>Capas Visibles:</span>
        </span>
        <button
          type="button"
          onClick={() => setShowMeasured(!showMeasured)}
          className={`px-3 py-1.5 rounded-lg border transition-all ${
            showMeasured
              ? 'border-orange-500/80 bg-orange-500/15 text-orange-300'
              : 'border-zinc-800 bg-zinc-950 text-zinc-600'
          }`}
        >
          ● Medición Base (Sin Corregir)
        </button>
        <button
          type="button"
          onClick={() => setShowTarget(!showTarget)}
          className={`px-3 py-1.5 rounded-lg border transition-all ${
            showTarget
              ? 'border-indigo-500/80 bg-indigo-500/15 text-indigo-300'
              : 'border-zinc-800 bg-zinc-950 text-zinc-600'
          }`}
        >
          ● Curva Objetivo ({activeProfileId})
        </button>
        <button
          type="button"
          onClick={() => setShowCorrected(!showCorrected)}
          className={`px-3 py-1.5 rounded-lg border transition-all ${
            showCorrected
              ? 'border-emerald-500/80 bg-emerald-500/15 text-emerald-300'
              : 'border-zinc-800 bg-zinc-950 text-zinc-600'
          }`}
        >
          ● Verificación Post-Calibración
        </button>
      </div>

      {/* Gráfico Principal */}
      <div className="p-6 rounded-2xl bg-zinc-900 border border-zinc-800">
        <FrequencyGraph
          data={curveData.map(p => ({
            freq: p.freq,
            measured: showMeasured ? p.measured : undefined,
            target: showTarget ? p.target : undefined,
            corrected: showCorrected ? p.corrected : undefined,
          }))}
          height={380}
        />
      </div>

      {/* Tabla de Modos de Sala Detectados */}
      <div className="p-5 rounded-2xl bg-zinc-900 border border-zinc-800 space-y-3 font-mono text-xs">
        <div className="flex items-center gap-2 text-white font-semibold">
          <Table className="w-4 h-4 text-orange-400" />
          <span>Resonancias Modales Atenuadas (&lt; 500 Hz)</span>
        </div>
        <p className="text-zinc-400 text-[11px]">
          Filtros notch de factor Q alto aplicados a ondas estacionarias dominantes de la sala.
        </p>
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-zinc-800 text-zinc-500 text-[11px]">
                <th className="py-2 px-3">Frecuencia</th>
                <th className="py-2 px-3">Tipo de Modo</th>
                <th className="py-2 px-3">Elevación Base</th>
                <th className="py-2 px-3">Ganancia Filtro</th>
                <th className="py-2 px-3">Delta Residual</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800/60 text-zinc-300">
              {curveData.length > 0 && identifyRoomModes(
                curveData.map(c => c.measured ?? 0),
                curveData.map(c => c.target ?? 0),
                curveData.map(c => c.freq)
              ).map((m) => (
                <tr key={m.frequencyHz}>
                  <td className="py-2.5 px-3 text-orange-400 font-semibold">{m.frequencyHz} Hz</td>
                  <td className="py-2.5 px-3 text-zinc-400">{m.modeType}</td>
                  <td className="py-2.5 px-3">+{m.elevationDb.toFixed(1)} dB</td>
                  <td className="py-2.5 px-3 text-rose-400 font-semibold">{m.filterGainDb.toFixed(1)} dB</td>
                  <td className="py-2.5 px-3 text-emerald-400 font-semibold">
                    {m.residualDeltaDb > 0 ? `+${m.residualDeltaDb.toFixed(1)} dB` : `${m.residualDeltaDb.toFixed(1)} dB`} (Atenuado)
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
