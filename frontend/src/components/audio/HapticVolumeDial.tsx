import React, { useRef, useState, useEffect, useCallback } from 'react';
import { Volume2, VolumeX } from 'lucide-react';

export interface HapticVolumeDialProps {
  volumeDb: number;
  isMuted: boolean;
  minDb?: number;
  maxDb?: number;
  step?: number;
  onChange: (newVol: number) => void;
  onToggleMute: () => void;
}

/**
 * Braun Minimalist Rotary Volume Dial (Dieter Rams "Weniger, aber besser" aesthetic).
 * Precision matte graphite casing, knurled indicator index, iconic Braun orange accent,
 * hairline radial tick graduation, and native 120 Hz haptic micro-feedback.
 */
export const HapticVolumeDial: React.FC<HapticVolumeDialProps> = ({
  volumeDb,
  isMuted,
  minDb = -80.0,
  maxDb = 16.5,
  step = 0.5,
  onChange,
  onToggleMute,
}) => {
  const dialRef = useRef<SVGSVGElement | null>(null);
  const isDragging = useRef<boolean>(false);
  const startY = useRef<number>(0);
  const startVol = useRef<number>(volumeDb);
  const lastHapticVol = useRef<number>(volumeDb);
  const [isHovered, setIsHovered] = useState<boolean>(false);

  // Normalize volume: 0.0 to 1.0
  const normalized = Math.max(0.0, Math.min(1.0, (volumeDb - minDb) / (maxDb - minDb)));

  // Rotary geometry: 270 degree arc from 135° (bottom-left) to 405° (bottom-right)
  const cx = 110;
  const cy = 110;
  const dialRadius = 66; // physical knob radius
  const trackRadius = 84; // graduated scale radius
  const circumference = 2 * Math.PI * trackRadius;
  const arcSpanFraction = 270 / 360;
  const totalArcLength = circumference * arcSpanFraction;
  const dashOffset = totalArcLength - totalArcLength * normalized;

  // Angular position of needle / indicator dot (135° to 405°)
  const currentAngleDeg = 135 + normalized * 270;
  const needleRad = (currentAngleDeg * Math.PI) / 180;
  const indicatorDotX = cx + (dialRadius - 10) * Math.cos(needleRad);
  const indicatorDotY = cy + (dialRadius - 10) * Math.sin(needleRad);

  // Haptic pulse on step crossing
  const triggerHaptic = useCallback((val: number) => {
    if (Math.abs(val - lastHapticVol.current) >= step) {
      lastHapticVol.current = val;
      if (typeof navigator !== 'undefined' && navigator.vibrate) {
        navigator.vibrate(10);
      }
    }
  }, [step]);

  const updateVolume = useCallback((newVol: number) => {
    const clamped = Math.max(minDb, Math.min(maxDb, Math.round(newVol / step) * step));
    triggerHaptic(clamped);
    onChange(clamped);
  }, [minDb, maxDb, step, onChange, triggerHaptic]);

  const handlePointerDown = (e: React.PointerEvent<SVGSVGElement>) => {
    e.preventDefault();
    isDragging.current = true;
    startY.current = e.clientY;
    startVol.current = volumeDb;
    (e.target as Element).setPointerCapture?.(e.pointerId);
  };

  const handlePointerMove = (e: React.PointerEvent<SVGSVGElement>) => {
    if (!isDragging.current) return;
    e.preventDefault();

    if (dialRef.current) {
      const rect = dialRef.current.getBoundingClientRect();
      const centerX = rect.left + rect.width / 2;
      const centerY = rect.top + rect.height / 2;
      const dx = e.clientX - centerX;
      const dy = e.clientY - centerY;
      const dist = Math.sqrt(dx * dx + dy * dy);

      // Circular angular drag around knob
      if (dist > 30) {
        let angleDeg = (Math.atan2(dy, dx) * 180) / Math.PI;
        if (angleDeg < 0) angleDeg += 360;

        let relativeAngle = angleDeg - 135;
        if (relativeAngle < 0) relativeAngle += 360;

        if (relativeAngle <= 270) {
          const ratio = relativeAngle / 270;
          updateVolume(minDb + ratio * (maxDb - minDb));
          return;
        }
      }
    }

    // Vertical precision drag fallback
    const deltaY = startY.current - e.clientY;
    updateVolume(startVol.current + deltaY * 0.25);
  };

  const handlePointerUp = (e: React.PointerEvent<SVGSVGElement>) => {
    if (isDragging.current) {
      isDragging.current = false;
      try {
        (e.target as Element).releasePointerCapture?.(e.pointerId);
      } catch {}
    }
  };

  useEffect(() => {
    lastHapticVol.current = volumeDb;
  }, [volumeDb]);

  // Braun iconic accent color: Braun Orange (#ff6600 / #f97316) for active level, Coral Red for Mute
  const braunAccent = isMuted ? '#ef4444' : '#ff6600';

  // Major and minor tick graduations around the mechanical scale
  const ticks = [
    { db: -80, label: '-80' },
    { db: -60, label: '' },
    { db: -50, label: '-50' },
    { db: -40, label: '' },
    { db: -30, label: '-30' },
    { db: -20, label: '-20' },
    { db: -10, label: '-10' },
    { db: 0, label: '0' },
    { db: 16.5, label: '+16' },
  ];

  return (
    <div className="relative flex flex-col items-center justify-center select-none py-1">
      {/* Industrial Rotary Housing */}
      <div
        className="relative w-64 h-64 flex items-center justify-center"
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
      >
        <svg
          ref={dialRef}
          className="w-full h-full cursor-grab active:cursor-grabbing touch-none select-none"
          viewBox="0 0 220 220"
          onPointerDown={handlePointerDown}
          onPointerMove={handlePointerMove}
          onPointerUp={handlePointerUp}
          onPointerCancel={handlePointerUp}
        >
          {/* Outer Housing Ring (Matte Braun Dark Polycarbonate) */}
          <circle
            cx={cx}
            cy={cy}
            r="104"
            fill="#121214"
            stroke="#27272a"
            strokeWidth="1"
          />

          {/* Scale Inset Bezel */}
          <circle
            cx={cx}
            cy={cy}
            r="94"
            fill="#18181b"
            stroke="#27272a"
            strokeWidth="1"
          />

          {/* Background Arc Track */}
          <circle
            cx={cx}
            cy={cy}
            r={trackRadius}
            fill="none"
            stroke="#27272a"
            strokeWidth="4"
            strokeLinecap="round"
            strokeDasharray={`${totalArcLength} ${circumference}`}
            transform={`rotate(135 ${cx} ${cy})`}
          />

          {/* Active Level Arc Track (Braun Orange / Red) */}
          <circle
            cx={cx}
            cy={cy}
            r={trackRadius}
            fill="none"
            stroke={braunAccent}
            strokeWidth="4"
            strokeLinecap="round"
            strokeDasharray={`${totalArcLength} ${circumference}`}
            strokeDashoffset={dashOffset}
            transform={`rotate(135 ${cx} ${cy})`}
            className="transition-all duration-75"
          />

          {/* Milled Mechanical Tick Marks */}
          {ticks.map((t, idx) => {
            const frac = (t.db - minDb) / (maxDb - minDb);
            const ang = (135 + frac * 270) * (Math.PI / 180);
            const isMajor = t.label.length > 0;
            const rInner = isMajor ? trackRadius + 6 : trackRadius + 8;
            const rOuter = isMajor ? trackRadius + 15 : trackRadius + 12;

            const x1 = cx + rInner * Math.cos(ang);
            const y1 = cy + rInner * Math.sin(ang);
            const x2 = cx + rOuter * Math.cos(ang);
            const y2 = cy + rOuter * Math.sin(ang);

            const isPassed = !isMuted && frac <= normalized;

            return (
              <g key={idx}>
                <line
                  x1={x1}
                  y1={y1}
                  x2={x2}
                  y2={y2}
                  stroke={isPassed ? '#f4f4f5' : '#52525b'}
                  strokeWidth={isMajor ? 1.5 : 1}
                  strokeLinecap="square"
                />
                {isMajor && (
                  <text
                    x={cx + (rOuter + 6) * Math.cos(ang)}
                    y={cy + (rOuter + 6) * Math.sin(ang) + 3}
                    textAnchor="middle"
                    fill={isPassed ? '#a1a1aa' : '#52525b'}
                    fontSize="7"
                    fontFamily="monospace"
                    fontWeight="600"
                  >
                    {t.label}
                  </text>
                )}
              </g>
            );
          })}

          {/* Central Physical Knob (Brushed Matte Anthracite) */}
          <circle
            cx={cx}
            cy={cy}
            r={dialRadius}
            fill="#18181b"
            stroke={isHovered ? '#3f3f46' : '#27272a'}
            strokeWidth="1.5"
          />

          {/* Recessed Inner Grip Ring */}
          <circle
            cx={cx}
            cy={cy}
            r={dialRadius - 6}
            fill="#141416"
            stroke="#27272a"
            strokeWidth="1"
          />

          {/* Center Matte Display Capsule */}
          <circle
            cx={cx}
            cy={cy}
            r={dialRadius - 16}
            fill="#09090b"
            stroke="#27272a"
            strokeWidth="1"
          />

          {/* Iconic Braun Orange Indicator Dot on Knob Edge */}
          <circle
            cx={indicatorDotX}
            cy={indicatorDotY}
            r="3.5"
            fill={braunAccent}
            stroke="#09090b"
            strokeWidth="1"
          />
        </svg>

        {/* Precision Numerical Display in Knob Center */}
        <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
          <span className="text-[9px] font-mono tracking-widest uppercase text-zinc-500 font-semibold mb-0.5">
            {isMuted ? 'MUTE' : 'GAIN'}
          </span>

          <div className="flex items-baseline justify-center">
            <span
              className={`text-2xl font-mono font-bold tracking-tighter ${
                isMuted ? 'text-red-400 line-through' : 'text-zinc-100'
              }`}
            >
              {volumeDb > 0 ? '+' : ''}
              {volumeDb.toFixed(1)}
            </span>
            <span className="text-[10px] font-mono text-zinc-500 ml-0.5 font-medium">dB</span>
          </div>

          {/* Mechanical Mute Switch */}
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              onToggleMute();
            }}
            className={`mt-1.5 pointer-events-auto px-2 py-0.5 rounded text-[10px] font-mono font-semibold uppercase tracking-wider flex items-center gap-1 transition-all active:scale-95 border ${
              isMuted
                ? 'bg-red-500/20 text-red-400 border-red-500/60'
                : 'bg-zinc-800/80 text-zinc-400 border-zinc-700/80 hover:text-zinc-200 hover:border-zinc-500'
            }`}
          >
            {isMuted ? <VolumeX className="w-2.5 h-2.5" /> : <Volume2 className="w-2.5 h-2.5 text-zinc-500" />}
            <span>{isMuted ? 'UNMUTE' : 'MUTE'}</span>
          </button>
        </div>
      </div>

      {/* Tactile Rocker Stepper Controls (Braun ET66 calculator aesthetic) */}
      <div className="grid grid-cols-4 gap-1.5 mt-3 w-full max-w-xs px-2">
        <button
          type="button"
          onClick={() => updateVolume(volumeDb - 2.0)}
          className="py-2 rounded-lg border border-zinc-800 bg-zinc-900/90 text-zinc-400 hover:text-zinc-100 hover:border-zinc-700 active:bg-zinc-800 font-mono text-xs transition-colors"
          title="-2.0 dB"
        >
          -2
        </button>

        <button
          type="button"
          onClick={() => updateVolume(volumeDb - 0.5)}
          className="py-2 rounded-lg border border-zinc-800 bg-zinc-900/90 text-zinc-300 hover:text-white hover:border-zinc-700 active:bg-zinc-800 font-mono text-xs font-semibold transition-colors"
          title="-0.5 dB"
        >
          -0.5
        </button>

        <button
          type="button"
          onClick={() => updateVolume(volumeDb + 0.5)}
          className="py-2 rounded-lg border border-zinc-800 bg-zinc-900/90 text-zinc-300 hover:text-white hover:border-zinc-700 active:bg-zinc-800 font-mono text-xs font-semibold transition-colors"
          title="+0.5 dB"
        >
          +0.5
        </button>

        <button
          type="button"
          onClick={() => updateVolume(volumeDb + 2.0)}
          className="py-2 rounded-lg border border-zinc-800 bg-zinc-900/90 text-zinc-400 hover:text-zinc-100 hover:border-zinc-700 active:bg-zinc-800 font-mono text-xs transition-colors"
          title="+2.0 dB"
        >
          +2
        </button>
      </div>

      <div className="flex items-center gap-1.5 mt-2 text-[9px] font-mono tracking-wider text-zinc-500 uppercase">
        <span className="w-1.5 h-1.5 rounded-full bg-orange-500/80" />
        <span>Paso de 0.5 dB · Tacto Háptico Directo</span>
      </div>
    </div>
  );
};
