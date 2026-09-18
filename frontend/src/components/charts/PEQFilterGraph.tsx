import React from 'react';
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

export interface FilterCurvePoint {
  freq: number;
  total: number;
  b1?: number;
  b2?: number;
  b3?: number;
  b4?: number;
  b5?: number;
  b6?: number;
  b7?: number;
}

interface PEQFilterGraphProps {
  data: FilterCurvePoint[];
  title?: string;
  height?: number;
}

const BAND_COLORS = [
  '#f43f5e', // Band 1: Rose
  '#f97316', // Band 2: Orange
  '#eab308', // Band 3: Yellow
  '#10b981', // Band 4: Emerald
  '#06b6d4', // Band 5: Cyan
  '#6366f1', // Band 6: Indigo
  '#a855f7', // Band 7: Purple
];

export const PEQFilterGraph: React.FC<PEQFilterGraphProps> = ({
  data,
  title = 'Descomposición de Filtros Biquad (7 Bandas PEQ)',
  height = 240,
}) => {
  const formatFreq = (val: number): string => {
    if (val >= 1000) {
      return `${(val / 1000).toFixed(val % 1000 === 0 ? 0 : 1)}k`;
    }
    return `${val}`;
  };

  const domainTicks = [20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000];

  return (
    <div className="w-full bg-surface-1/90 border border-border-subtle rounded-xl p-4 sm:p-5 flex flex-col gap-3">
      <div className="flex flex-wrap items-center justify-between gap-2 pb-2 border-b border-border-subtle">
        <h4 className="text-sm font-semibold text-slate-200 tracking-tight">{title}</h4>
        <div className="flex items-center gap-2 text-[10px] font-mono text-slate-400">
          <span className="flex items-center gap-1">
            <span className="w-2.5 h-1 bg-white rounded"></span> Curva Resultante
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2.5 h-1 bg-indigo-400 rounded"></span> Bandas Individuales
          </span>
        </div>
      </div>

      <div className="w-full relative" style={{ height: `${height}px` }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
            <XAxis
              dataKey="freq"
              scale="log"
              domain={[20, 20000]}
              type="number"
              ticks={domainTicks}
              tickFormatter={formatFreq}
              stroke="#64748b"
              fontSize={10}
              fontFamily="JetBrains Mono"
            />
            <YAxis
              domain={[-12, 12]}
              ticks={[-12, -6, 0, 6, 12]}
              stroke="#64748b"
              fontSize={10}
              fontFamily="JetBrains Mono"
              unit=" dB"
            />
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const pData = payload[0].payload as FilterCurvePoint;
                  return (
                    <div className="bg-surface-2/95 border border-border-strong p-2.5 rounded-lg shadow-xl backdrop-blur font-mono text-xs z-50">
                      <div className="text-slate-300 font-semibold border-b border-border-subtle pb-1 mb-1">
                        {formatFreq(pData.freq)} Hz: Total {pData.total.toFixed(1)} dB
                      </div>
                      <div className="grid grid-cols-2 gap-x-3 gap-y-0.5 text-[11px]">
                        {pData.b1 !== undefined && <span style={{ color: BAND_COLORS[0] }}>B1: {pData.b1.toFixed(1)} dB</span>}
                        {pData.b2 !== undefined && <span style={{ color: BAND_COLORS[1] }}>B2: {pData.b2.toFixed(1)} dB</span>}
                        {pData.b3 !== undefined && <span style={{ color: BAND_COLORS[2] }}>B3: {pData.b3.toFixed(1)} dB</span>}
                        {pData.b4 !== undefined && <span style={{ color: BAND_COLORS[3] }}>B4: {pData.b4.toFixed(1)} dB</span>}
                        {pData.b5 !== undefined && <span style={{ color: BAND_COLORS[4] }}>B5: {pData.b5.toFixed(1)} dB</span>}
                        {pData.b6 !== undefined && <span style={{ color: BAND_COLORS[5] }}>B6: {pData.b6.toFixed(1)} dB</span>}
                        {pData.b7 !== undefined && <span style={{ color: BAND_COLORS[6] }}>B7: {pData.b7.toFixed(1)} dB</span>}
                      </div>
                    </div>
                  );
                }
                return null;
              }}
            />
            <ReferenceLine y={0} stroke="rgba(255,255,255,0.2)" strokeDasharray="4 4" />

            {/* Individual bands */}
            <Line type="monotone" dataKey="b1" stroke={BAND_COLORS[0]} strokeWidth={1} dot={false} isAnimationActive={false} />
            <Line type="monotone" dataKey="b2" stroke={BAND_COLORS[1]} strokeWidth={1} dot={false} isAnimationActive={false} />
            <Line type="monotone" dataKey="b3" stroke={BAND_COLORS[2]} strokeWidth={1} dot={false} isAnimationActive={false} />
            <Line type="monotone" dataKey="b4" stroke={BAND_COLORS[3]} strokeWidth={1} dot={false} isAnimationActive={false} />
            <Line type="monotone" dataKey="b5" stroke={BAND_COLORS[4]} strokeWidth={1} dot={false} isAnimationActive={false} />
            <Line type="monotone" dataKey="b6" stroke={BAND_COLORS[5]} strokeWidth={1} dot={false} isAnimationActive={false} />
            <Line type="monotone" dataKey="b7" stroke={BAND_COLORS[6]} strokeWidth={1} dot={false} isAnimationActive={false} />

            {/* Total combined curve */}
            <Line type="monotone" dataKey="total" stroke="#ffffff" strokeWidth={2} dot={false} isAnimationActive={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
