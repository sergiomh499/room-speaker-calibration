import React, { useState, useMemo } from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
} from 'recharts';

export interface CurveDataPoint {
  freq: number;
  measured?: number;
  target?: number;
  corrected?: number;
}

interface FrequencyGraphProps {
  data: CurveDataPoint[];
  title?: string;
  height?: number;
  showSchroeder?: boolean;
}

export const FrequencyGraph: React.FC<FrequencyGraphProps> = ({
  data,
  title,
  height = 320,
  showSchroeder = true,
}) => {
  const [showMeasured, setShowMeasured] = useState<boolean>(true);
  const [showTarget, setShowTarget] = useState<boolean>(true);
  const [showCorrected, setShowCorrected] = useState<boolean>(true);

  // Format frequency ticks (20, 50, 100, 200, 500, 1k, 2k, 5k, 10k, 20k)
  const formatFreq = (val: number): string => {
    if (val >= 1000) {
      return `${(val / 1000).toFixed(val % 1000 === 0 ? 0 : 1)}k`;
    }
    return `${val}`;
  };
  const domainTicks = useMemo(() => [20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000], []);

  const yDomain = useMemo<[number, number]>(() => {
    if (!data || data.length === 0) return [-36, 12];
    let minVal = 0;
    let maxVal = 0;
    data.forEach(d => {
      [d.measured, d.target, d.corrected].forEach(v => {
        if (typeof v === 'number' && !isNaN(v)) {
          if (v < minVal) minVal = v;
          if (v > maxVal) maxVal = v;
        }
      });
    });
    const floorMin = Math.max(-48, Math.floor((minVal - 3) / 6) * 6);
    const ceilMax = Math.min(18, Math.ceil((maxVal + 3) / 6) * 6);
    return [floorMin, ceilMax];
  }, [data]);

  const yTicks = useMemo(() => {
    const [min, max] = yDomain;
    const ticks: number[] = [];
    for (let t = min; t <= max; t += 6) {
      ticks.push(t);
    }
    return ticks;
  }, [yDomain]);

  return (
    <div className="w-full bg-surface-1/90 border border-border-subtle rounded-xl p-4 sm:p-5 flex flex-col gap-3">
      {/* Header and Layer Toggles */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-border-subtle">
        <div>
          {title && <h4 className="text-sm font-semibold text-slate-200 tracking-tight">{title}</h4>}
          <div className="text-[11px] text-slate-400 font-mono">
            Respuesta Acústica en Frecuencia (20 Hz — 20 kHz, dB SPL)
          </div>
        </div>

        {/* Legend toggles */}
        <div className="flex items-center gap-2 text-xs font-mono select-none">
          <button
            type="button"
            onClick={() => setShowMeasured(!showMeasured)}
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full border transition-all ${
              showMeasured
                ? 'bg-slate-700/50 border-slate-500 text-slate-200 shadow-sm'
                : 'bg-surface-2/30 border-transparent text-slate-500'
            }`}
          >
            <span className="w-2.5 h-2.5 rounded-full bg-slate-400"></span>
            <span>Medido</span>
          </button>

          <button
            type="button"
            onClick={() => setShowTarget(!showTarget)}
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full border transition-all ${
              showTarget
                ? 'bg-amber-500/10 border-amber-500/40 text-amber-300 shadow-sm'
                : 'bg-surface-2/30 border-transparent text-slate-500'
            }`}
          >
            <span className="w-2.5 h-2.5 rounded-full bg-amber-400"></span>
            <span>Objetivo</span>
          </button>

          <button
            type="button"
            onClick={() => setShowCorrected(!showCorrected)}
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full border transition-all ${
              showCorrected
                ? 'bg-emerald-500/10 border-emerald-500/40 text-emerald-300 shadow-sm'
                : 'bg-surface-2/30 border-transparent text-slate-500'
            }`}
          >
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400"></span>
            <span>Corregido PEQ</span>
          </button>
        </div>
      </div>

      {/* Recharts Container */}
      <div className="w-full relative" style={{ height: `${height}px` }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 10, right: 12, left: -2, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
            <XAxis
              dataKey="freq"
              scale="log"
              domain={[20, 20000]}
              type="number"
              ticks={domainTicks}
              tickFormatter={formatFreq}
              stroke="#64748b"
              fontSize={11}
              fontFamily="JetBrains Mono"
            />
            <YAxis
              domain={yDomain}
              ticks={yTicks}
              stroke="#64748b"
              fontSize={11}
              fontFamily="JetBrains Mono"
              width={46}
              tickFormatter={(val: number) => `${val > 0 ? `+${val}` : val} dB`}
            />
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const pData = payload[0].payload as CurveDataPoint;
                  return (
                    <div className="bg-surface-2/95 border border-border-strong p-3 rounded-lg shadow-xl backdrop-blur font-mono text-xs z-50">
                      <div className="text-slate-400 border-b border-border-subtle pb-1 mb-1.5 font-semibold">
                        Frecuencia: <span className="text-indigo-300">{formatFreq(pData.freq)} Hz</span>
                      </div>
                      {pData.measured !== undefined && showMeasured && (
                        <div className="text-slate-300 flex justify-between gap-4">
                          <span>Medido:</span>
                          <span className="font-semibold">{pData.measured.toFixed(1)} dB</span>
                        </div>
                      )}
                      {pData.target !== undefined && showTarget && (
                        <div className="text-amber-400 flex justify-between gap-4">
                          <span>Objetivo:</span>
                          <span className="font-semibold">{pData.target.toFixed(1)} dB</span>
                        </div>
                      )}
                      {pData.corrected !== undefined && showCorrected && (
                        <div className="text-emerald-400 flex justify-between gap-4">
                          <span>Corregido:</span>
                          <span className="font-semibold">{pData.corrected.toFixed(1)} dB</span>
                        </div>
                      )}
                    </div>
                  );
                }
                return null;
              }}
            />

            {/* Zero dB Reference Line */}
            <ReferenceLine y={0} stroke="rgba(255,255,255,0.2)" strokeDasharray="4 4" />

            {/* Schroeder frequency boundary (240 Hz) */}
            {showSchroeder && (
              <ReferenceLine
                x={240}
                stroke="#6366f1"
                strokeDasharray="2 2"
                label={{
                  value: 'Schroeder ~240Hz',
                  fill: '#818cf8',
                  fontSize: 10,
                  position: 'insideTopLeft',
                  fontFamily: 'JetBrains Mono',
                }}
              />
            )}

            {showMeasured && (
              <Line
                type="monotone"
                dataKey="measured"
                stroke="#94a3b8"
                strokeWidth={1.5}
                dot={false}
                isAnimationActive={false}
                connectNulls={true}
              />
            )}

            {showTarget && (
              <Line
                type="monotone"
                dataKey="target"
                stroke="#f59e0b"
                strokeWidth={2}
                strokeDasharray="5 5"
                dot={false}
                isAnimationActive={false}
                connectNulls={true}
              />
            )}

            {showCorrected && (
              <Line
                type="monotone"
                dataKey="corrected"
                stroke="#10b981"
                strokeWidth={2.5}
                dot={false}
                isAnimationActive={false}
                connectNulls={true}
              />
            )}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
