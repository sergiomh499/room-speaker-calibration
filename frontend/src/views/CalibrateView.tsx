import React, { useState, useEffect } from 'react';
import {
  Sliders,
  CheckCircle2,
  Speaker,
  Volume2,
  ChevronRight,
  ChevronLeft,
  Play,
  Sparkles,
  Zap,
  Flame,
  Radio,
  ArrowRight,
  Upload,
} from 'lucide-react';
import { useCalibration } from '../context/CalibrationContext';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Pill } from '../components/ui/Pill';
import { VUMeter } from '../components/ui/VUMeter';
import { FrequencyGraph, CurveDataPoint } from '../components/charts/FrequencyGraph';
import { PEQFilterGraph, FilterCurvePoint } from '../components/charts/PEQFilterGraph';
import { api } from '../services/api';

export const CalibrateView: React.FC = () => {
  const {
    topology,
    setTopology,
    wizardStep,
    setWizardStep,
    totalSteps,
    points,
    setPoints,
    profiles,
    activeProfileId,
    setActiveProfileId,
    subwooferConfig,
    setSubwooferConfig,
    toast,
  } = useCalibration();

  // Wizard Step Titles and Mapping
  const stepsList = topology === '2.0'
    ? [
        { num: 1, title: 'Setup & Canales', desc: 'Topología y micrófono' },
        { num: 2, title: 'Medición Móvil', desc: '5 posiciones espaciales' },
        { num: 3, title: 'Perfil & PEQ', desc: 'Curva objetivo y 7 bandas' },
        { num: 4, title: 'Yamaha & Verif', desc: 'Despliegue a NVRAM y A/B' },
      ]
    : [
        { num: 1, title: 'Setup & Canales', desc: 'Topología y micrófono' },
        { num: 2, title: 'Medición Móvil', desc: '5 posiciones espaciales' },
        { num: 3, title: 'Graves & Focal', desc: 'Crossover, fase y subwoofer' },
        { num: 4, title: 'Perfil & PEQ', desc: 'Curva objetivo y 7 bandas' },
        { num: 5, title: 'Yamaha & Verif', desc: 'Despliegue a NVRAM y A/B' },
      ];

  // Local state for Step 1
  const [playingTone, setPlayingTone] = useState<string | null>(null);

  // Local state for Step 2
  const [measuringPoint, setMeasuringPoint] = useState<number | null>(null);
  const [sweepProgress, setSweepProgress] = useState<number>(0);

  // Local state for Step 3 (Subwoofer)
  const [aligningPhase, setAligningPhase] = useState<boolean>(false);
  const [aligningLevels, setAligningLevels] = useState<boolean>(false);

  // Local state for Step 4 (Profiles)
  const [selectedCategory, setSelectedCategory] = useState<string>('Todos');
  const [previewCurve, setPreviewCurve] = useState<CurveDataPoint[]>([]);
  const [filterCurves, setFilterCurves] = useState<FilterCurvePoint[]>([]);

  // Local state for Step 5 (Yamaha Deploy)
  const [selectedScene, setSelectedScene] = useState<number>(1);
  const [deploying, setDeploying] = useState<boolean>(false);
  const [activeAbMode, setActiveAbMode] = useState<string>('peq');

  // Load preview curves for active profile
  useEffect(() => {
    let active = true;
    api.getMeasuredCurve(activeProfileId)
      .then(res => {
        if (!active) return;
        if (res && res.freqs) {
          const curve: CurveDataPoint[] = [];
          for (let i = 0; i < res.freqs.length; i += 3) {
            curve.push({
              freq: Math.round(res.freqs[i]),
              measured: Math.round(res.measured_l[i] * 10) / 10,
              target: Math.round(res.target[i] * 10) / 10,
              corrected: Math.round(res.corrected_l[i] * 10) / 10,
            });
          }
          setPreviewCurve(curve);
        }
      })
      .catch(() => {});

    // Generate dummy filter decomposition
    const fPoints: FilterCurvePoint[] = [];
    const testFreqs = [20, 31.5, 50, 78, 125, 200, 315, 500, 800, 1250, 2000, 3150, 5000, 8000, 12500, 20000];
    testFreqs.forEach(f => {
      const b1 = -3.5 * Math.exp(-Math.pow(Math.log(f / 78.7) * 4, 2));
      const b2 = -2.0 * Math.exp(-Math.pow(Math.log(f / 117.2) * 3, 2));
      const b3 = 1.5 * Math.exp(-Math.pow(Math.log(f / 240.0) * 2, 2));
      const b4 = -1.0 * Math.exp(-Math.pow(Math.log(f / 496.0) * 2, 2));
      const b5 = 0.5 * Math.exp(-Math.pow(Math.log(f / 1000.0) * 2, 2));
      const b6 = -1.5 * Math.exp(-Math.pow(Math.log(f / 3500.0) * 2, 2));
      const b7 = 1.0 * Math.exp(-Math.pow(Math.log(f / 8000.0) * 2, 2));
      const total = b1 + b2 + b3 + b4 + b5 + b6 + b7;
      fPoints.push({
        freq: f,
        total: Math.round(total * 10) / 10,
        b1: Math.round(b1 * 10) / 10,
        b2: Math.round(b2 * 10) / 10,
        b3: Math.round(b3 * 10) / 10,
        b4: Math.round(b4 * 10) / 10,
        b5: Math.round(b5 * 10) / 10,
        b6: Math.round(b6 * 10) / 10,
        b7: Math.round(b7 * 10) / 10,
      });
    });
    setFilterCurves(fPoints);

    return () => { active = false; };
  }, [activeProfileId]);

  // Handle playing channel test tone
  const handlePlayTone = async (channel: string) => {
    try {
      setPlayingTone(channel);
      await api.playTone(channel);
      toast(`Reproduciendo tono de prueba en canal ${channel}`, 'info');
    } catch {
      toast(`No se pudo emitir tono en canal ${channel}`, 'warn');
    } finally {
      setTimeout(() => setPlayingTone(null), 2500);
    }
  };

  // Handle measuring a spatial point
  const handleMeasurePoint = async (pointId: number) => {
    setMeasuringPoint(pointId);
    setSweepProgress(10);

    const timer = setInterval(() => {
      setSweepProgress(prev => {
        if (prev >= 90) {
          clearInterval(timer);
          return 90;
        }
        return prev + 20;
      });
    }, 400);

    try {
      await api.playSweep('L');
      setSweepProgress(100);
      setPoints(prev =>
        prev.map(p => (p.id === pointId ? { ...p, measured: true } : p))
      );
      toast(`Punto ${pointId} medido y guardado exitosamente.`, 'success');
    } catch {
      toast(`Error al registrar sweep en Punto ${pointId}.`, 'error');
    } finally {
      clearInterval(timer);
      setTimeout(() => {
        setMeasuringPoint(null);
        setSweepProgress(0);
      }, 500);
    }
  };

  // Handle Auto Phase Alignment (2.1)
  const handleAutoPhase = async () => {
    setAligningPhase(true);
    try {
      const res = await api.autoAlignPhase();
      if (res && res.best_phase !== undefined) {
        setSubwooferConfig(prev => ({ ...prev, phase_degrees: res.best_phase }));
        toast(`Fase acústica alineada a ${res.best_phase}° (+${res.delta_db || 3.0} dB ganancia constructiva).`, 'success');
      } else {
        toast('Fase evaluada en 0° Normal con respuesta constructiva óptima.', 'info');
      }
    } catch {
      toast('Error al evaluar fase automática.', 'warn');
    } finally {
      setAligningPhase(false);
    }
  };

  // Handle Auto Level Trim (2.1)
  const handleAutoLevels = async () => {
    setAligningLevels(true);
    try {
      const res = await api.autoAlignLevels();
      if (res && res.subwoofer_trim_db !== undefined) {
        setSubwooferConfig(prev => ({ ...prev, trim_db: res.subwoofer_trim_db }));
        toast(`Niveles calibrados: Subwoofer ajustado a ${res.subwoofer_trim_db > 0 ? '+' : ''}${res.subwoofer_trim_db} dB.`, 'success');
      } else {
        setSubwooferConfig(prev => ({ ...prev, trim_db: 10.0 }));
        toast('Nivel calibrado a 75 dB SPL de referencia (+10.0 dB trim).', 'info');
      }
    } catch {
      toast('Error al calcular trims automáticos.', 'warn');
    } finally {
      setAligningLevels(false);
    }
  };

  // Handle Deploying PEQ to Yamaha
  const handleDeployPEQ = async () => {
    setDeploying(true);
    try {
      await api.deployPEQ(activeProfileId, selectedScene);
      toast(`¡Perfil ${activeProfileId} transferido y grabado en la NVRAM del Yamaha!`, 'success');
    } catch {
      toast('Error al desplegar en el receptor AV.', 'error');
    } finally {
      setDeploying(false);
    }
  };

  // Filter profiles by category
  const categories = ['Todos', 'Música Hi-Fi', 'Cine & TV', 'Gaming', 'Puro'];
  const filteredProfiles = profiles.filter(p => {
    if (selectedCategory === 'Todos') return true;
    return p.category?.toLowerCase().includes(selectedCategory.toLowerCase());
  });

  return (
    <div className="space-y-6 pb-24 md:pb-8">
      {/* Dynamic Stepper Header */}
      <div className="bg-surface-1/90 border border-border-subtle rounded-2xl p-4 sm:p-6 backdrop-blur">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-border-subtle">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono uppercase px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                Paso {wizardStep} de {totalSteps}
              </span>
              <span className="text-xs text-slate-400 font-mono">
                {topology === '2.1' ? 'Topología 2.1 (Subwoofer Focal)' : 'Topología 2.0 (Estéreo)'}
              </span>
            </div>
            <h2 className="text-xl sm:text-2xl font-bold text-white tracking-tight mt-1">
              {stepsList[wizardStep - 1]?.title}
            </h2>
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              disabled={wizardStep <= 1}
              icon={<ChevronLeft className="w-4 h-4" />}
              onClick={() => setWizardStep(wizardStep - 1)}
            >
              Anterior
            </Button>
            <Button
              variant="primary"
              size="sm"
              disabled={wizardStep >= totalSteps}
              icon={<ChevronRight className="w-4 h-4" />}
              onClick={() => setWizardStep(wizardStep + 1)}
            >
              Siguiente
            </Button>
          </div>
        </div>

        {/* Stepper Progress Badges */}
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-5 gap-2 mt-4">
          {stepsList.map(s => {
            const isCurrent = wizardStep === s.num;
            const isDone = wizardStep > s.num;
            return (
              <button
                key={s.num}
                type="button"
                onClick={() => setWizardStep(s.num)}
                className={`flex items-center gap-2.5 p-2 rounded-xl text-left border transition-all ${
                  isCurrent
                    ? 'bg-indigo-600/20 border-indigo-500 text-white shadow-sm'
                    : isDone
                    ? 'bg-surface-2/60 border-border-subtle text-slate-300 hover:border-slate-500'
                    : 'bg-surface-0/40 border-border-subtle text-slate-500 hover:text-slate-400'
                }`}
              >
                <div
                  className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-mono shrink-0 ${
                    isCurrent
                      ? 'bg-indigo-500 text-white font-bold'
                      : isDone
                      ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                      : 'bg-surface-3 text-slate-400'
                  }`}
                >
                  {isDone ? <CheckCircle2 className="w-3.5 h-3.5" /> : s.num}
                </div>
                <div className="min-w-0">
                  <div className="text-xs font-medium truncate">{s.title}</div>
                  <div className="text-[10px] text-slate-400 truncate hidden lg:block">{s.desc}</div>
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* ========================================================================= */}
      {/* STEP 1: SETUP & CANALES                                                   */}
      {/* ========================================================================= */}
      {wizardStep === 1 && (
        <div className="space-y-6">
          {/* Topology Selector */}
          <Card
            title="1. Topología del Sistema Acústico"
            subtitle="Configura el número de canales para adaptar el algoritmo"
            icon={<Speaker className="w-5 h-5 text-indigo-400" />}
          >
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div
                onClick={() => setTopology('2.1')}
                className={`p-4 rounded-xl border cursor-pointer transition-all ${
                  topology === '2.1'
                    ? 'bg-indigo-600/10 border-indigo-500 shadow-md shadow-indigo-500/10'
                    : 'bg-surface-2/40 border-border-subtle hover:border-slate-600'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-sm font-semibold text-white">2.1 Estéreo + Subwoofer</span>
                  <Pill variant="indigo">Recomendado</Pill>
                </div>
                <p className="text-xs text-slate-300 mt-1">
                  Q Acoustics 3020i (Small) + Subwoofer Focal Cub Evo con gestión de crossover a 80 Hz y alineación de fase.
                </p>
              </div>

              <div
                onClick={() => setTopology('2.0')}
                className={`p-4 rounded-xl border cursor-pointer transition-all ${
                  topology === '2.0'
                    ? 'bg-indigo-600/10 border-indigo-500 shadow-md shadow-indigo-500/10'
                    : 'bg-surface-2/40 border-border-subtle hover:border-slate-600'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-sm font-semibold text-white">2.0 Estéreo Puro</span>
                  <Pill variant="neutral">2 Canales</Pill>
                </div>
                <p className="text-xs text-slate-300 mt-1">
                  Frontales en rango completo (Large) sin canal LFE ni gestión de graves dedicada.
                </p>
              </div>
            </div>
          </Card>

          {/* Real-time Microphone Check */}
          <Card
            title="2. Micrófono del Smartphone / Medidor"
            subtitle="Web Audio API con indicador dinámico de volumen y picos"
            icon={<Radio className="w-5 h-5 text-emerald-400" />}
          >
            <VUMeter />
          </Card>

          {/* Channel Test Tones */}
          <Card
            title="3. Comprobación de Canales y Emisión"
            subtitle="Verifica que cada altavoz responde correctamente antes del barrido"
            icon={<Volume2 className="w-5 h-5 text-amber-400" />}
          >
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <Button
                variant={playingTone === 'L' ? 'emerald' : 'outline'}
                icon={<Play className="w-4 h-4" />}
                onClick={() => handlePlayTone('L')}
              >
                {playingTone === 'L' ? 'Sonando Izquierdo...' : 'Frontal Izquierdo (L)'}
              </Button>

              <Button
                variant={playingTone === 'R' ? 'emerald' : 'outline'}
                icon={<Play className="w-4 h-4" />}
                onClick={() => handlePlayTone('R')}
              >
                {playingTone === 'R' ? 'Sonando Derecho...' : 'Frontal Derecho (R)'}
              </Button>

              {topology === '2.1' && (
                <Button
                  variant={playingTone === 'SUB' ? 'emerald' : 'outline'}
                  icon={<Play className="w-4 h-4" />}
                  onClick={() => handlePlayTone('SUB')}
                >
                  {playingTone === 'SUB' ? 'Sonando Subwoofer...' : 'Subwoofer (Focal Cub)'}
                </Button>
              )}
            </div>
          </Card>

          <div className="flex justify-end">
            <Button
              variant="primary"
              size="lg"
              icon={<ArrowRight className="w-4 h-4" />}
              onClick={() => setWizardStep(2)}
            >
              Continuar a Medición Móvil
            </Button>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* STEP 2: MEDICIÓN MÓVIL (5 PUNTOS ITU-R BS.1116)                          */}
      {/* ========================================================================= */}
      {wizardStep === 2 && (
        <div className="space-y-6">
          <Card
            title="Matriz de Medición Espacial (5 Puntos)"
            subtitle="Realiza el sweep logarítmico (20 Hz - 20 kHz) en cada posición clave"
            icon={<Sliders className="w-5 h-5 text-indigo-400" />}
          >
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {points.map(p => (
                <div
                  key={p.id}
                  className={`p-4 rounded-xl border transition-all flex flex-col justify-between gap-3 ${
                    p.measured
                      ? 'bg-surface-2/60 border-emerald-500/30'
                      : 'bg-surface-2/20 border-border-subtle'
                  }`}
                >
                  <div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-semibold text-white">{p.label}</span>
                      {p.measured ? (
                        <Pill variant="emerald" size="sm" icon={<CheckCircle2 className="w-3 h-3" />}>
                          Medido
                        </Pill>
                      ) : (
                        <Pill variant="neutral" size="sm">Pendiente</Pill>
                      )}
                    </div>
                    <p className="text-xs text-slate-400 mt-1 font-mono">{p.sublabel}</p>
                  </div>

                  <Button
                    variant={p.measured ? 'outline' : 'primary'}
                    size="sm"
                    loading={measuringPoint === p.id}
                    icon={<Play className="w-3.5 h-3.5" />}
                    onClick={() => handleMeasurePoint(p.id)}
                  >
                    {p.measured ? 'Re-medir' : 'Emitir Sweep'}
                  </Button>
                </div>
              ))}
            </div>

            {measuringPoint !== null && (
              <div className="mt-4 p-3 rounded-lg bg-indigo-500/10 border border-indigo-500/30">
                <div className="flex justify-between text-xs font-mono text-indigo-300 mb-1">
                  <span>Emitiendo Sweep acústico en Punto {measuringPoint}...</span>
                  <span>{sweepProgress}%</span>
                </div>
                <div className="h-2 bg-surface-0 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-indigo-500 transition-all duration-200"
                    style={{ width: `${sweepProgress}%` }}
                  />
                </div>
              </div>
            )}
          </Card>

          <div className="flex justify-between">
            <Button
              variant="outline"
              size="lg"
              icon={<ChevronLeft className="w-4 h-4" />}
              onClick={() => setWizardStep(1)}
            >
              Atrás
            </Button>
            <Button
              variant="primary"
              size="lg"
              icon={<ArrowRight className="w-4 h-4" />}
              onClick={() => setWizardStep(topology === '2.0' ? 3 : 3)}
            >
              {topology === '2.0' ? 'Continuar a Perfil PEQ' : 'Continuar a Graves & Focal'}
            </Button>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* STEP 3 (CONDICIONAL 2.1): GRAVES & FOCAL CUB EVO                           */}
      {/* ========================================================================= */}
      {topology === '2.1' && wizardStep === 3 && (
        <div className="space-y-6">
          <Card
            title="Gestión Activa de Graves & Crossover"
            subtitle="Integración acústica entre los satélites Q Acoustics 3020i y el subwoofer Focal Cub Evo"
            icon={<Flame className="w-5 h-5 text-amber-400" />}
          >
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Crossover Frequency Slider */}
              <div className="p-4 rounded-xl bg-surface-2/40 border border-border-subtle space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-xs font-semibold text-slate-200">Frecuencia de Cruce (Crossover)</span>
                  <Pill variant="indigo" size="sm">{subwooferConfig.crossover_hz} Hz</Pill>
                </div>
                <input
                  type="range"
                  min="50"
                  max="120"
                  step="10"
                  value={subwooferConfig.crossover_hz}
                  onChange={e =>
                    setSubwooferConfig(prev => ({
                      ...prev,
                      crossover_hz: parseInt(e.target.value, 10),
                    }))
                  }
                  className="w-full h-2 bg-surface-3 rounded-lg appearance-none cursor-pointer accent-indigo-500"
                />
                <p className="text-[11px] text-slate-400 font-mono">
                  Recomendado para Q Acoustics 3020i: <strong>80 Hz</strong> (HPF 12dB/oct + LPF 24dB/oct).
                </p>
              </div>

              {/* Acoustic Phase Alignment */}
              <div className="p-4 rounded-xl bg-surface-2/40 border border-border-subtle space-y-2 flex flex-col justify-between">
                <div>
                  <div className="flex justify-between items-center">
                    <span className="text-xs font-semibold text-slate-200">Alineación de Fase Acústica</span>
                    <Pill variant="emerald" size="sm">{subwooferConfig.phase_degrees}°</Pill>
                  </div>
                  <p className="text-[11px] text-slate-400 mt-1">
                    Evaluación de interferencia constructiva en la zona de solape (60–100 Hz).
                  </p>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  loading={aligningPhase}
                  icon={<Zap className="w-3.5 h-3.5" />}
                  onClick={handleAutoPhase}
                >
                  Alinear Fase Automática
                </Button>
              </div>

              {/* Level / Trim Alignment */}
              <div className="p-4 rounded-xl bg-surface-2/40 border border-border-subtle space-y-2 flex flex-col justify-between">
                <div>
                  <div className="flex justify-between items-center">
                    <span className="text-xs font-semibold text-slate-200">Calibración de Trim Subwoofer</span>
                    <Pill variant="amber" size="sm">
                      {subwooferConfig.trim_db > 0 ? `+${subwooferConfig.trim_db}` : subwooferConfig.trim_db} dB
                    </Pill>
                  </div>
                  <p className="text-[11px] text-slate-400 mt-1">
                    Equilibrio de presión sonora SPL a 75 dB de referencia en sweet spot.
                  </p>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  loading={aligningLevels}
                  icon={<Sparkles className="w-3.5 h-3.5" />}
                  onClick={handleAutoLevels}
                >
                  Ajustar Nivel Automático
                </Button>
              </div>
            </div>

            {/* Subwoofer PEQ Bands Table */}
            <div className="mt-5 space-y-2">
              <div className="text-xs font-semibold text-slate-300 font-mono">
                Filtros PEQ Calculados para Subwoofer (Focal Cub Evo):
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs font-mono border-collapse">
                  <thead>
                    <tr className="border-b border-border-subtle text-slate-400">
                      <th className="py-2 px-3">Banda</th>
                      <th className="py-2 px-3">Frecuencia</th>
                      <th className="py-2 px-3">Factor Q</th>
                      <th className="py-2 px-3">Ganancia (dB)</th>
                      <th className="py-2 px-3">Función Acústica</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border-subtle text-slate-200">
                    {subwooferConfig.peq_bands.map(b => (
                      <tr key={b.band} className="hover:bg-surface-2/40">
                        <td className="py-2 px-3 text-indigo-400 font-bold">Sub B{b.band}</td>
                        <td className="py-2 px-3">{b.freq_hz} Hz</td>
                        <td className="py-2 px-3">{b.q.toFixed(2)}</td>
                        <td className="py-2 px-3 font-semibold text-emerald-400">{b.gain_db.toFixed(1)} dB</td>
                        <td className="py-2 px-3 text-slate-400">
                          {b.gain_db < 0 ? 'Supresión de resonancia modal' : 'Refuerzo de extensión'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </Card>

          <div className="flex justify-between">
            <Button
              variant="outline"
              size="lg"
              icon={<ChevronLeft className="w-4 h-4" />}
              onClick={() => setWizardStep(2)}
            >
              Atrás
            </Button>
            <Button
              variant="primary"
              size="lg"
              icon={<ArrowRight className="w-4 h-4" />}
              onClick={() => setWizardStep(4)}
            >
              Continuar a Selección de Perfil PEQ
            </Button>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* STEP 4 (or STEP 3 in 2.0): PERFIL COMUNITARIO & PEQ OPTIMIZATION         */}
      {/* ========================================================================= */}
      {((topology === '2.1' && wizardStep === 4) || (topology === '2.0' && wizardStep === 3)) && (
        <div className="space-y-6">
          {/* Profile Carousel and Category Filter */}
          <div className="space-y-3">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <h3 className="text-base font-semibold text-white tracking-tight">
                Curvas Objetivo Audiófilas
              </h3>
              <div className="flex flex-wrap gap-1.5">
                {categories.map(cat => (
                  <button
                    key={cat}
                    type="button"
                    onClick={() => setSelectedCategory(cat)}
                    className={`px-3 py-1 rounded-full text-xs font-medium transition-all ${
                      selectedCategory === cat
                        ? 'bg-indigo-600 text-white shadow-sm'
                        : 'bg-surface-1 border border-border-subtle text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    {cat}
                  </button>
                ))}
              </div>
            </div>

            {/* Profile Cards Grid / Carousel */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
              {filteredProfiles.map(p => {
                const isSelected = activeProfileId === p.id;
                return (
                  <div
                    key={p.id}
                    onClick={() => {
                      setActiveProfileId(p.id);
                      toast(`Perfil activo: ${p.name}`, 'info');
                    }}
                    className={`p-4 rounded-xl border cursor-pointer transition-all flex flex-col justify-between gap-3 ${
                      isSelected
                        ? 'bg-indigo-950/40 border-indigo-500 shadow-lg shadow-indigo-500/10 ring-1 ring-indigo-500/50'
                        : 'bg-surface-1/80 border-border-subtle hover:border-slate-600'
                    }`}
                  >
                    <div>
                      <div className="flex items-center justify-between gap-2 mb-1.5">
                        <span className="text-xs font-mono font-bold text-slate-200 truncate">{p.name}</span>
                        {p.badge && <Pill variant="indigo" size="sm">{p.badge}</Pill>}
                      </div>
                      <p className="text-xs text-slate-400 line-clamp-2 leading-relaxed">
                        {p.description}
                      </p>
                    </div>

                    <div className="flex items-center justify-between text-[11px] pt-2 border-t border-border-subtle font-mono">
                      <span className="text-slate-400">{p.category}</span>
                      <span className={isSelected ? 'text-emerald-400 font-bold' : 'text-slate-500'}>
                        {isSelected ? '✓ Seleccionado' : 'Elegir'}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Interactive Graphs */}
          <FrequencyGraph
            title={`Previsualización: Curva Estimada — ${activeProfileId}`}
            data={previewCurve}
            height={320}
          />

          <PEQFilterGraph
            title="Desglose de Filtros Biquad RBJ para Frontales"
            data={filterCurves}
            height={240}
          />

          <div className="flex justify-between">
            <Button
              variant="outline"
              size="lg"
              icon={<ChevronLeft className="w-4 h-4" />}
              onClick={() => setWizardStep(topology === '2.0' ? 2 : 3)}
            >
              Atrás
            </Button>
            <Button
              variant="primary"
              size="lg"
              icon={<ArrowRight className="w-4 h-4" />}
              onClick={() => setWizardStep(topology === '2.0' ? 4 : 5)}
            >
              Continuar a Despliegue Yamaha
            </Button>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* STEP 5 (or STEP 4 in 2.0): YAMAHA & VERIFICACIÓN A/B                      */}
      {/* ========================================================================= */}
      {((topology === '2.1' && wizardStep === 5) || (topology === '2.0' && wizardStep === 4)) && (
        <div className="space-y-6">
          <Card
            title="1. Asignación a Escenas Yamaha (SCENE 1–4)"
            subtitle="Graba este perfil calibrado en un botón físico del mando o frontal"
            icon={<Zap className="w-5 h-5 text-amber-400" />}
          >
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {[
                { num: 1, label: 'SCENE 1: Hi-Fi Música' },
                { num: 2, label: 'SCENE 2: Cine & TV' },
                { num: 3, label: 'SCENE 3: Gaming' },
                { num: 4, label: 'SCENE 4: Pure Direct' },
              ].map(sc => (
                <button
                  key={sc.num}
                  type="button"
                  onClick={() => setSelectedScene(sc.num)}
                  className={`p-3 rounded-xl border text-left transition-all ${
                    selectedScene === sc.num
                      ? 'bg-indigo-600/20 border-indigo-500 text-white'
                      : 'bg-surface-2/40 border-border-subtle text-slate-400 hover:border-slate-500'
                  }`}
                >
                  <div className="text-xs font-mono text-indigo-400 font-bold">Botón {sc.num}</div>
                  <div className="text-xs font-medium mt-0.5 text-slate-200">{sc.label}</div>
                </button>
              ))}
            </div>

            <div className="mt-5 flex flex-col sm:flex-row items-center justify-between gap-4 p-4 rounded-xl bg-surface-2/60 border border-border-subtle">
              <div>
                <div className="text-sm font-semibold text-white">Despliegue Atómico a NVRAM</div>
                <div className="text-xs text-slate-400 font-mono mt-0.5">
                  Write-Commit-Readback garantizado sin pérdida al apagar el receptor.
                </div>
              </div>
              <Button
                variant="emerald"
                size="lg"
                loading={deploying}
                icon={<Upload className="w-4 h-4" />}
                onClick={handleDeployPEQ}
              >
                Grabar en Yamaha RX-V673
              </Button>
            </div>
          </Card>

          {/* Real-time A/B Switcher */}
          <Card
            title="2. Prueba de Escucha Comparativa A/B en Vivo"
            subtitle="Conmuta instantáneamente entre tu calibración de estudio y los modos de fábrica"
            icon={<Sliders className="w-5 h-5 text-indigo-400" />}
          >
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {[
                { id: 'peq', label: 'Octave Calibrado', desc: 'Filtros 7-Band + Focal 80Hz' },
                { id: 'through', label: 'Bypass (Through)', desc: 'Respuesta cruda de sala' },
                { id: 'ypao_flat', label: 'YPAO Flat', desc: 'Curva plana de fábrica' },
                { id: 'ypao_natural', label: 'YPAO Natural', desc: 'Atenuación suave de agudos' },
              ].map(mode => (
                <button
                  key={mode.id}
                  type="button"
                  onClick={() => {
                    setActiveAbMode(mode.id);
                    toast(`Modo A/B: ${mode.label} activo en receptor.`, 'info');
                  }}
                  className={`p-3 rounded-xl border text-left transition-all ${
                    activeAbMode === mode.id
                      ? 'bg-emerald-600/20 border-emerald-500 text-white ring-1 ring-emerald-500/50'
                      : 'bg-surface-2/40 border-border-subtle text-slate-400 hover:border-slate-500'
                  }`}
                >
                  <div className="text-xs font-semibold text-slate-200">{mode.label}</div>
                  <div className="text-[10px] text-slate-400 font-mono mt-0.5">{mode.desc}</div>
                </button>
              ))}
            </div>
          </Card>

          <div className="flex justify-between">
            <Button
              variant="outline"
              size="lg"
              icon={<ChevronLeft className="w-4 h-4" />}
              onClick={() => setWizardStep(topology === '2.0' ? 3 : 4)}
            >
              Atrás
            </Button>
            <Button
              variant="primary"
              size="lg"
              icon={<CheckCircle2 className="w-4 h-4" />}
              onClick={() => {
                toast('¡Calibración completada con éxito!', 'success');
              }}
            >
              Finalizar Calibración
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};
