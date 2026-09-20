import React, { useState, useEffect } from 'react';
import {
  X,
  Sliders,
  BarChart3,
  Layers,
  Info,
  Volume2,
  RefreshCw,
} from 'lucide-react';
import { Button } from './ui/Button';
import { Card } from './ui/Card';
import { api } from '../services/api';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts';

interface MeasurementAnalysisModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const POINT_COLORS = {
  1: '#6366f1', // Indigo (P1 Sweet Spot)
  2: '#10b981', // Emerald (P2 Sofá Izq)
  3: '#f59e0b', // Amber (P3 Sofá Der)
  4: '#06b6d4', // Cyan (P4 Mesa Frente)
  5: '#ec4899', // Rose (P5 Fondo)
};

export const MeasurementAnalysisModal: React.FC<MeasurementAnalysisModalProps> = ({
  isOpen,
  onClose,
}) => {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<any>(null);
  const [selectedPoint, setSelectedPoint] = useState<number | 'all'>('all');
  const [selectedChannel, setSelectedChannel] = useState<'all' | 'l' | 'r' | 'sub'>('all');
  const [activeTab, setActiveTab] = useState<'metrics' | 'curves' | 'diagnostic'>('metrics');

  const loadData = async () => {
    setLoading(true);
    try {
      const res = await api.getMeasurementAnalysis();
      if (res && res.ok) {
        setData(res);
      }
    } catch (err) {
      console.error('Error loading measurement analysis:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      loadData();
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const points = data?.points || [];
  const curves = data?.curves || [];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-black/80 backdrop-blur-md animate-fade-in">
      <div className="relative w-full max-w-5xl max-h-[92vh] flex flex-col bg-surface-1 border border-border-strong rounded-2xl shadow-2xl overflow-hidden text-slate-200">
        {/* Modal Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-border-subtle bg-surface-0/60">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-indigo-500/15 text-indigo-400 border border-indigo-500/30">
              <BarChart3 className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base sm:text-lg font-bold text-white flex items-center gap-2">
                Análisis Acústico Multicanal y Comparativa Espacial
                <span className="text-xs px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 font-mono border border-indigo-500/30">
                  5 Puntos
                </span>
              </h2>
              <p className="text-xs text-slate-400">
                Visualización física, telemetría de retardo temporal y curvas de respuesta en frecuencia
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="sm" icon={<RefreshCw className="w-4 h-4" />} onClick={loadData}>
              Actualizar
            </Button>
            <button
              onClick={onClose}
              className="p-2 text-slate-400 hover:text-white rounded-lg hover:bg-surface-2 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Filter Toolbar & Tab navigation */}
        <div className="px-5 py-3 border-b border-border-subtle bg-surface-2/30 flex flex-wrap items-center justify-between gap-3 text-xs">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-slate-400 font-semibold">Punto:</span>
            <button
              onClick={() => setSelectedPoint('all')}
              className={`px-2.5 py-1 rounded-md font-mono transition-all ${
                selectedPoint === 'all'
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'bg-surface-2 text-slate-400 hover:text-white'
              }`}
            >
              Todos (1-5)
            </button>
            {[1, 2, 3, 4, 5].map(pId => (
              <button
                key={pId}
                onClick={() => setSelectedPoint(pId)}
                className={`px-2 py-1 rounded-md font-mono transition-all flex items-center gap-1.5 ${
                  selectedPoint === pId
                    ? 'bg-indigo-600 text-white shadow-sm'
                    : 'bg-surface-2 text-slate-400 hover:text-white'
                }`}
              >
                <span
                  className="w-2 h-2 rounded-full inline-block"
                  style={{ backgroundColor: POINT_COLORS[pId as keyof typeof POINT_COLORS] }}
                />
                P{pId}
              </button>
            ))}
          </div>

          <div className="flex items-center gap-2">
            <span className="text-slate-400 font-semibold">Canal:</span>
            {(['all', 'l', 'r', 'sub'] as const).map(ch => (
              <button
                key={ch}
                onClick={() => setSelectedChannel(ch)}
                className={`px-2 py-1 rounded-md font-mono uppercase transition-all ${
                  selectedChannel === ch
                    ? 'bg-emerald-600 text-white shadow-sm'
                    : 'bg-surface-2 text-slate-400 hover:text-white'
                }`}
              >
                {ch === 'all' ? 'Todos' : ch === 'sub' ? 'Subwoofer' : `Front ${ch}`}
              </button>
            ))}
          </div>

          {/* View Mode Buttons */}
          <div className="flex items-center gap-1 bg-surface-1 p-1 rounded-lg border border-border-subtle">
            <button
              onClick={() => setActiveTab('metrics')}
              className={`px-3 py-1 rounded-md font-medium transition-all ${
                activeTab === 'metrics' ? 'bg-indigo-500/20 text-indigo-300 font-semibold' : 'text-slate-400 hover:text-white'
              }`}
            >
              Telemetría
            </button>
            <button
              onClick={() => setActiveTab('curves')}
              className={`px-3 py-1 rounded-md font-medium transition-all ${
                activeTab === 'curves' ? 'bg-indigo-500/20 text-indigo-300 font-semibold' : 'text-slate-400 hover:text-white'
              }`}
            >
              Gráficas
            </button>
            <button
              onClick={() => setActiveTab('diagnostic')}
              className={`px-3 py-1 rounded-md font-medium transition-all ${
                activeTab === 'diagnostic' ? 'bg-indigo-500/20 text-indigo-300 font-semibold' : 'text-slate-400 hover:text-white'
              }`}
            >
              Diagnóstico
            </button>
          </div>
        </div>

        {/* Modal Body */}
        <div className="p-5 overflow-y-auto flex-1 space-y-4">
          {loading ? (
            <div className="flex flex-col items-center justify-center p-12 text-slate-400">
              <RefreshCw className="w-8 h-8 animate-spin text-indigo-400 mb-3" />
              <p className="text-sm font-medium">Cargando análisis acústico espacial de 5 puntos...</p>
            </div>
          ) : (
            <>
              {/* TAB 1: METRICS & TELEMETRY TABLE */}
              {activeTab === 'metrics' && (
                <div className="space-y-4">
                  <div className="overflow-x-auto rounded-xl border border-border-subtle shadow-sm bg-surface-0">
                    <table className="w-full text-left text-xs font-mono">
                      <thead className="bg-surface-2/60 text-slate-300 border-b border-border-subtle uppercase tracking-wider text-[11px]">
                        <tr>
                          <th className="py-3 px-4">Punto</th>
                          <th className="py-3 px-3">Ubicación Física</th>
                          <th className="py-3 px-3">Canal</th>
                          <th className="py-3 px-3 text-right">Distancia</th>
                          <th className="py-3 px-3 text-right">Retardo</th>
                          <th className="py-3 px-3 text-right">Nivel SPL</th>
                          <th className="py-3 px-4">Diagnóstico Físico</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-border-subtle/50 text-slate-300">
                        {points
                          .filter((p: any) => selectedPoint === 'all' || p.point_id === selectedPoint)
                          .flatMap((p: any) => {
                            const chKeys =
                              selectedChannel === 'all'
                                ? ['Front_L', 'Front_R', 'Subwoofer']
                                : selectedChannel === 'l'
                                ? ['Front_L']
                                : selectedChannel === 'r'
                                ? ['Front_R']
                                : ['Subwoofer'];

                            return chKeys.map((chKey, idx) => {
                              const chData = p.channels[chKey] || {};
                              const isSub = chKey === 'Subwoofer';
                              const p1Dist = points[0]?.channels[chKey]?.distance_m || chData.distance_m;
                              const deltaP1 = chData.distance_m - p1Dist;

                              return (
                                <tr
                                  key={`${p.point_id}-${chKey}`}
                                  className={`hover:bg-surface-2/30 transition-colors ${
                                    idx === 0 && selectedChannel === 'all' ? 'border-t border-border-subtle/80' : ''
                                  }`}
                                >
                                  {idx === 0 && selectedChannel === 'all' ? (
                                    <td rowSpan={chKeys.length} className="py-3 px-4 font-semibold text-white align-top border-r border-border-subtle/40 bg-surface-1/40">
                                      <div className="flex items-center gap-2">
                                        <span
                                          className="w-2.5 h-2.5 rounded-full"
                                          style={{
                                            backgroundColor:
                                              POINT_COLORS[p.point_id as keyof typeof POINT_COLORS] || '#6366f1',
                                          }}
                                        />
                                        <span>P{p.point_id}</span>
                                      </div>
                                    </td>
                                  ) : selectedChannel !== 'all' ? (
                                    <td className="py-3 px-4 font-semibold text-white">
                                      <div className="flex items-center gap-2">
                                        <span
                                          className="w-2.5 h-2.5 rounded-full"
                                          style={{
                                            backgroundColor:
                                              POINT_COLORS[p.point_id as keyof typeof POINT_COLORS] || '#6366f1',
                                          }}
                                        />
                                        <span>P{p.point_id}</span>
                                      </div>
                                    </td>
                                  ) : null}

                                  {(idx === 0 && selectedChannel === 'all') || selectedChannel !== 'all' ? (
                                    <td
                                      rowSpan={selectedChannel === 'all' ? chKeys.length : 1}
                                      className="py-3 px-3 text-slate-400 text-[11px] align-top border-r border-border-subtle/40"
                                    >
                                      {p.sublabel || p.name}
                                    </td>
                                  ) : null}

                                  <td className="py-3 px-3 font-semibold">
                                    <span
                                      className={`px-1.5 py-0.5 rounded text-[10px] ${
                                        isSub
                                          ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                                          : chKey === 'Front_L'
                                          ? 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/30'
                                          : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                                      }`}
                                    >
                                      {isSub ? 'SUB (Focal)' : chKey.replace('Front_', '')}
                                    </span>
                                  </td>

                                  <td className="py-3 px-3 text-right font-medium">
                                    <span className="text-white">{chData.distance_m ? `${chData.distance_m} m` : '—'}</span>
                                    {p.point_id !== 1 && deltaP1 !== 0 && (
                                      <span
                                        className={`ml-1 text-[10px] ${
                                          deltaP1 < 0 ? 'text-emerald-400 font-bold' : 'text-amber-400'
                                        }`}
                                      >
                                        ({deltaP1 > 0 ? `+${deltaP1.toFixed(2)}` : deltaP1.toFixed(2)}m)
                                      </span>
                                    )}
                                  </td>

                                  <td className="py-3 px-3 text-right text-slate-400">
                                    {chData.delay_ms ? `${chData.delay_ms} ms` : '—'}
                                  </td>

                                  <td className="py-3 px-3 text-right">
                                    <span
                                      className={`font-semibold ${
                                        isSub && chData.spl_db > 60
                                          ? 'text-cyan-400'
                                          : chData.spl_db >= 64
                                          ? 'text-emerald-400'
                                          : 'text-slate-300'
                                      }`}
                                    >
                                      {chData.spl_db ? `${chData.spl_db} dB` : '—'}
                                    </span>
                                  </td>

                                  <td className="py-3 px-4 text-xs text-slate-400">
                                    {chData.diagnostic}
                                  </td>
                                </tr>
                              );
                            });
                          })}
                      </tbody>
                    </table>
                  </div>

                  {/* Clarification Callout for Point 4 */}
                  <div className="p-4 rounded-xl bg-cyan-500/10 border border-cyan-500/30 text-xs flex items-start gap-3">
                    <Info className="w-5 h-5 text-cyan-400 shrink-0 mt-0.5" />
                    <div>
                      <span className="font-bold text-cyan-200">
                        Análisis Físico del Punto 4 (Frente / Zona Mesa):
                      </span>
                      <p className="text-slate-300 mt-1 leading-relaxed">
                        Al avanzar físicamente del sofá central hacia la mesa de centro (Punto 4), el micrófono se sitúa más cerca de la pantalla y de los altavoces: la distancia a <strong>Front_L se reduce a 2.12 m</strong> (vs 2.45 m), a <strong>Front_R a 2.02 m</strong> (vs 2.35 m), y al <strong>Subwoofer Focal Cub Evo se reduce a 3.30 m</strong> (vs 3.65 m). Simultáneamente, la presión acústica en graves en la mesa aumenta a <strong>65.7 dB SPL</strong> (+12.6 dB) debido al refuerzo de ondas estacionarias en la zona central de la sala.
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* TAB 2: OVERLAID RECHARTS CURVES */}
              {activeTab === 'curves' && (
                <div className="space-y-4">
                  <div className="p-4 rounded-xl bg-surface-0 border border-border-subtle">
                    <div className="flex items-center justify-between mb-3">
                      <span className="text-sm font-semibold text-white flex items-center gap-2">
                        <Layers className="w-4 h-4 text-indigo-400" />
                        Curvas de Respuesta en Frecuencia Comparadas (20 Hz - 20 kHz)
                      </span>
                      <span className="text-xs text-slate-400 font-mono">
                        Escala Logarítmica · dB SPL
                      </span>
                    </div>

                    <div className="h-80 w-full">
                      <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={curves} margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
                          <CartesianGrid strokeDasharray="3 3" stroke="#2a303c" vertical={false} />
                          <XAxis
                            dataKey="freq"
                            stroke="#64748b"
                            tick={{ fontSize: 10, fill: '#94a3b8' }}
                            tickFormatter={v => (v >= 1000 ? `${v / 1000}k` : v)}
                          />
                          <YAxis
                            stroke="#64748b"
                            tick={{ fontSize: 10, fill: '#94a3b8' }}
                            domain={[-55, 10]}
                            unit="dB"
                          />
                          <Tooltip
                            contentStyle={{
                              backgroundColor: '#0d1117',
                              border: '1px solid #30363d',
                              borderRadius: '8px',
                              fontSize: '11px',
                              fontFamily: 'monospace',
                            }}
                            formatter={(value: any, name: any) => [`${value} dB`, name]}
                            labelFormatter={v => `${v} Hz`}
                          />
                          <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />

                          {/* Render lines for active points */}
                          {[1, 2, 3, 4, 5]
                            .filter(pId => selectedPoint === 'all' || selectedPoint === pId)
                            .map(pId => {
                              const color = POINT_COLORS[pId as keyof typeof POINT_COLORS];
                              return (
                                <React.Fragment key={pId}>
                                  {(selectedChannel === 'all' || selectedChannel === 'l') && (
                                    <Line
                                      type="monotone"
                                      dataKey={`p${pId}_l`}
                                      name={`P${pId} Front L`}
                                      stroke={color}
                                      strokeWidth={2}
                                      dot={false}
                                      strokeDasharray={selectedChannel === 'all' ? undefined : undefined}
                                    />
                                  )}
                                  {(selectedChannel === 'all' || selectedChannel === 'r') && (
                                    <Line
                                      type="monotone"
                                      dataKey={`p${pId}_r`}
                                      name={`P${pId} Front R`}
                                      stroke={color}
                                      strokeWidth={1.5}
                                      dot={false}
                                      strokeDasharray="4 2"
                                    />
                                  )}
                                  {(selectedChannel === 'all' || selectedChannel === 'sub') && (
                                    <Line
                                      type="monotone"
                                      dataKey={`p${pId}_sub`}
                                      name={`P${pId} Subwoofer`}
                                      stroke={pId === 4 ? '#06b6d4' : color}
                                      strokeWidth={pId === 4 ? 2.5 : 1.5}
                                      dot={false}
                                      strokeDasharray="2 2"
                                    />
                                  )}
                                </React.Fragment>
                              );
                            })}
                        </LineChart>
                      </ResponsiveContainer>
                    </div>

                    <div className="mt-3 flex flex-wrap items-center justify-between text-xs text-slate-400 border-t border-border-subtle pt-3">
                      <div className="flex items-center gap-4">
                        <span className="flex items-center gap-1.5">
                          <span className="w-4 h-0.5 bg-white inline-block" /> Frontal L (Sólida)
                        </span>
                        <span className="flex items-center gap-1.5">
                          <span className="w-4 h-0.5 border-t border-dashed border-white inline-block" /> Frontal R (Guiones)
                        </span>
                        <span className="flex items-center gap-1.5">
                          <span className="w-4 h-0.5 border-t border-dotted border-white inline-block" /> Subwoofer (Punteada)
                        </span>
                      </div>
                      <span className="text-[11px] text-indigo-300">
                        * Observa cómo P4 (Cyan) presenta mayor amplitud en graves al estar más cerca del Subwoofer.
                      </span>
                    </div>
                  </div>
                </div>
              )}

              {/* TAB 3: DIAGNOSTIC & ROOM ACOUSTICS */}
              {activeTab === 'diagnostic' && (
                <div className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <Card
                      title="Geometría Espacial de la Sala"
                      subtitle="Posicionamiento relativo a los monitores y subwoofer"
                      icon={<Sliders className="w-4 h-4 text-indigo-400" />}
                    >
                      <div className="space-y-3 text-xs">
                        <div className="p-3 rounded-lg bg-surface-0 border border-border-subtle">
                          <span className="font-bold text-white block">Posición Subwoofer Focal Cub Evo:</span>
                          <span className="text-slate-400">
                            Ubicado en la esquina frontal derecha (x: +1.20m, y: +3.44m).
                          </span>
                        </div>
                        <div className="p-3 rounded-lg bg-surface-0 border border-border-subtle">
                          <span className="font-bold text-white block">Punto 1 (Centro / Sweet Spot):</span>
                          <span className="text-slate-400">
                            Distancias calibradas: L = 2.45 m, R = 2.35 m, Sub = 3.65 m.
                          </span>
                        </div>
                        <div className="p-3 rounded-lg bg-cyan-500/10 border border-cyan-500/30">
                          <span className="font-bold text-cyan-200 block">Punto 4 (Frente / Mesa):</span>
                          <span className="text-slate-300">
                            El usuario avanza hacia la mesa: L = 2.12 m, R = 2.02 m, Sub = 3.30 m. 
                            <strong> Se acerca 35 cm a los tres altavoces</strong>.
                          </span>
                        </div>
                      </div>
                    </Card>

                    <Card
                      title="Comportamiento Modal en Graves"
                      subtitle="Por qué varía la presión sonora del Subwoofer"
                      icon={<Volume2 className="w-4 h-4 text-emerald-400" />}
                    >
                      <div className="space-y-3 text-xs leading-relaxed text-slate-300">
                        <p>
                          1. <strong>Interacción con Modos Axiales</strong>: En recintos cerrados de 5.2m x 3.8m, las frecuencias entre 35 Hz y 80 Hz presentan nodos (valles de silencio) y antinodos (máximos de presión).
                        </p>
                        <p>
                          2. <strong>Punto 2 (Izquierda) vs Punto 3 (Derecha)</strong>: Al desplazarse a la derecha (P3), el micrófono se aproxima a la esquina del subwoofer, aumentando el nivel medido a 59.8 dB SPL. A la izquierda (P2), se sitúa en una zona de cancelación parcial (46.8 dB SPL).
                        </p>
                        <p>
                          3. <strong>Punto 4 (Mesa)</strong>: Al acercarse físicamente al frente, la distancia disminuye a 3.30 m y la presión acústica alcanza 65.7 dB SPL, activando la resonancia de sala en 50 Hz.
                        </p>
                      </div>
                    </Card>
                  </div>
                </div>
              )}
            </>
          )}
        </div>

        {/* Modal Footer */}
        <div className="px-5 py-3 border-t border-border-subtle bg-surface-0/60 flex items-center justify-between text-xs">
          <span className="text-slate-400">
            5/5 Puntos de medición procesados con sincronización acústica sin retardo Wi-Fi.
          </span>
          <Button variant="primary" size="sm" onClick={onClose}>
            Entendido / Cerrar
          </Button>
        </div>
      </div>
    </div>
  );
};
