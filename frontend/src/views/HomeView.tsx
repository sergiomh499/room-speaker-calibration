import React, { useState, useEffect } from 'react';
import { Sliders, CheckCircle2, Speaker, Cpu, Volume2, ShieldCheck, ArrowRight, Music } from 'lucide-react';
import { useCalibration } from '../context/CalibrationContext';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Pill } from '../components/ui/Pill';
import { FrequencyGraph, CurveDataPoint } from '../components/charts/FrequencyGraph';
import { api } from '../services/api';

export const HomeView: React.FC = () => {
  const { setView, setWizardStep, avrStatus, topology } = useCalibration();
  const [curveData, setCurveData] = useState<CurveDataPoint[]>([]);

  // Generate synthetic realistic response curve fallback
  const fallbackCurve = (): CurveDataPoint[] => {
    const freqs = [
      20, 25, 31.5, 40, 50, 63, 80, 100, 125, 160, 200, 250, 315, 400, 500,
      630, 800, 1000, 1250, 1600, 2000, 2500, 3150, 4000, 5000, 6300, 8000,
      10000, 12500, 16000, 20000
    ];
    return freqs.map(f => {
      // Room modes in bass: peak at 78 Hz, dip at 110 Hz
      let raw = 0;
      if (f < 100) raw = Math.sin((f - 20) * 0.1) * 6 + 2;
      else if (f < 300) raw = Math.cos((f - 100) * 0.05) * 4 - 2;
      else raw = (Math.random() - 0.5) * 2 - (f > 8000 ? (f - 8000) / 4000 : 0);

      // Harman target curve: bass boost +5dB tapering down to -1dB at 20kHz
      let target = 0;
      if (f <= 60) target = 5.0;
      else if (f <= 150) target = 5.0 - ((f - 60) / 90) * 4.5;
      else target = 0.5 - (Math.log10(f / 150) / Math.log10(20000 / 150)) * 2.5;

      // Corrected curve: raw pulled towards target via 7-band PEQ
      const corrected = raw + (target - raw) * 0.85;

      return {
        freq: f,
        measured: Math.round(raw * 10) / 10,
        target: Math.round(target * 10) / 10,
        corrected: Math.round(corrected * 10) / 10,
      };
    });
  };

  useEffect(() => {
    let isMounted = true;
    api.getMeasuredCurve('harman_2_1')
      .then(res => {
        if (!isMounted) return;
        if (res && res.freqs && res.freqs.length > 0) {
          const points: CurveDataPoint[] = [];
          for (let i = 0; i < res.freqs.length; i += 2) {
            points.push({
              freq: Math.round(res.freqs[i]),
              measured: Math.round(res.measured_l[i] * 10) / 10,
              target: Math.round(res.target[i] * 10) / 10,
              corrected: Math.round(res.corrected_l[i] * 10) / 10,
            });
          }
          setCurveData(points);
        } else {
          setCurveData(fallbackCurve());
        }
      })
      .catch(() => {
        if (isMounted) setCurveData(fallbackCurve());
      });

    return () => { isMounted = false; };
  }, []);

  return (
    <div className="space-y-6 pb-20 md:pb-8">
      {/* Hero Section */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-surface-1 via-surface-1 to-indigo-950/40 border border-border-subtle p-6 sm:p-8">
        <div className="absolute top-0 right-0 -mt-12 -mr-12 w-64 h-64 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />
        
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2 max-w-2xl">
            <div className="flex items-center gap-2">
              <Pill variant="emerald" icon={<CheckCircle2 className="w-3.5 h-3.5" />}>
                Calibración Activa: Harman 2.1
              </Pill>
              <Pill variant="neutral">
                ITU-R BS.1116 (5 Puntos)
              </Pill>
            </div>
            <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-white">
              Tu sala, ajustada con precisión de estudio.
            </h1>
            <p className="text-sm text-slate-300 leading-relaxed">
              Respuesta en frecuencia optimizada mediante filtros biquad paramétricos en NVRAM, con gestión activa de graves y crossover a 80 Hz para Focal Cub Evo y Q Acoustics 3020i.
            </p>
          </div>

          <div className="flex flex-col sm:flex-row gap-3 shrink-0">
            <Button
              variant="primary"
              size="lg"
              icon={<Sliders className="w-4 h-4" />}
              onClick={() => {
                setWizardStep(1);
                setView('calibrate');
              }}
            >
              Iniciar Calibración
            </Button>
            <Button
              variant="outline"
              size="lg"
              icon={<Music className="w-4 h-4" />}
              onClick={() => {
                setWizardStep(topology === '2.0' ? 3 : 4);
                setView('calibrate');
              }}
            >
              Cambiar Perfil PEQ
            </Button>
          </div>
        </div>
      </div>

      {/* 4 Quick Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card
          title="Receptor AV"
          subtitle="Yamaha RX-V673"
          icon={<Cpu className="w-4 h-4" />}
          badge={<Pill variant={avrStatus.online ? 'emerald' : 'rose'}>{avrStatus.avr_power}</Pill>}
        >
          <div className="space-y-1 text-xs">
            <div className="flex justify-between text-slate-400 font-mono">
              <span>Entrada:</span>
              <span className="text-slate-200">{avrStatus.avr_input}</span>
            </div>
            <div className="flex justify-between text-slate-400 font-mono">
              <span>DRC Dinámico:</span>
              <span className="text-slate-200">{avrStatus.avr_drc}</span>
            </div>
          </div>
        </Card>

        <Card
          title="Topología Acústica"
          subtitle="2.1 Satélites + Subwoofer"
          icon={<Speaker className="w-4 h-4" />}
          badge={<Pill variant="indigo">80 Hz XO</Pill>}
        >
          <div className="space-y-1 text-xs">
            <div className="flex justify-between text-slate-400 font-mono">
              <span>Frontales:</span>
              <span className="text-slate-200">Q Acoustics 3020i (Small)</span>
            </div>
            <div className="flex justify-between text-slate-400 font-mono">
              <span>Subwoofer:</span>
              <span className="text-slate-200">Focal Cub Evo (Fase 0°)</span>
            </div>
          </div>
        </Card>

        <Card
          title="Modo DSP Activo"
          subtitle="Yamaha YNC Protocol"
          icon={<ShieldCheck className="w-4 h-4" />}
          badge={<Pill variant="cyan">{avrStatus.avr_peq_mode}</Pill>}
        >
          <div className="space-y-1 text-xs">
            <div className="flex justify-between text-slate-400 font-mono">
              <span>Bypass de Fábrica:</span>
              <span className="text-slate-200">Desactivado</span>
            </div>
            <div className="flex justify-between text-slate-400 font-mono">
              <span>Filtros en NVRAM:</span>
              <span className="text-slate-200">7 bandas / canal</span>
            </div>
          </div>
        </Card>

        <Card
          title="Volumen & Nivel"
          subtitle="Sensibilidad 75 dB SPL"
          icon={<Volume2 className="w-4 h-4" />}
          badge={<Pill variant="amber">{avrStatus.avr_volume_db} dB</Pill>}
        >
          <div className="space-y-1 text-xs">
            <div className="flex justify-between text-slate-400 font-mono">
              <span>Sub Trim:</span>
              <span className="text-slate-200">+10.0 dB</span>
            </div>
            <div className="flex justify-between text-slate-400 font-mono">
              <span>Headroom PEQ:</span>
              <span className="text-slate-200">-3.5 dB</span>
            </div>
          </div>
        </Card>
      </div>

      {/* Main Acoustic Frequency Response Graph */}
      <FrequencyGraph
        title="Medición Acústica Espacial & Corrección Activa"
        data={curveData}
        height={340}
      />

      {/* Room Acoustic Foundation & Insights */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card
          title="Fundamento Acústico de Sala"
          subtitle="Norma Internacional ITU-R BS.1116"
          icon={<ShieldCheck className="w-4 h-4 text-emerald-400" />}
        >
          <div className="space-y-3 text-xs text-slate-300 leading-relaxed">
            <p>
              • <strong className="text-indigo-300">Frecuencia de Schroeder (fs ≈ 240 Hz):</strong> Por debajo de esta frecuencia predominan las ondas estacionarias (modos propios axiales, tangenciales y oblicuos). El ecualizador paramétrico actúa quirúrgicamente con filtros Notch.
            </p>
            <p>
              • <strong className="text-amber-300">Banda de Transición y Directividad (&gt; 500 Hz):</strong> En altas frecuencias predomina la directividad del altavoz y las reflexiones tempranas de pared; solo se aplican suaves curvas de balance tonal (Tilt).
            </p>
          </div>
        </Card>

        <Card
          title="Puntos de Calibración & Variación Espacial"
          subtitle="Clúster de 5 posiciones con radio de 40 cm"
          icon={<CheckCircle2 className="w-4 h-4 text-indigo-400" />}
          action={
            <Button
              variant="ghost"
              size="sm"
              icon={<ArrowRight className="w-3.5 h-3.5" />}
              onClick={() => {
                setWizardStep(2);
                setView('calibrate');
              }}
            >
              Ver Puntos
            </Button>
          }
        >
          <div className="space-y-2 text-xs">
            <div className="flex items-center justify-between p-2 rounded-lg bg-surface-2/60 border border-border-subtle font-mono">
              <span className="text-slate-300">P1: Sweet Spot Principal</span>
              <Pill variant="emerald" size="sm">100% Ponderación</Pill>
            </div>
            <div className="flex items-center justify-between p-2 rounded-lg bg-surface-2/60 border border-border-subtle font-mono">
              <span className="text-slate-300">P2-P5: Perímetro de Escucha</span>
              <Pill variant="indigo" size="sm">40 cm Offset</Pill>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
};
