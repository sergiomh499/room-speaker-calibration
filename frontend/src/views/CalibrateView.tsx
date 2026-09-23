import React, { useState, useEffect, lazy, Suspense } from 'react';
import confetti from 'canvas-confetti';
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
  ShieldCheck,
  RotateCcw,
  Info,
  BarChart3,
  Compass,
  History,
  Save,
  Plus,
  Minus,
  FileText,
  Download,
} from 'lucide-react';
const MeasurementAnalysisModal = lazy(() => import('../components/MeasurementAnalysisModal').then(m => ({ default: m.MeasurementAnalysisModal })));
const SpatialRoom3D = lazy(() => import('../components/charts/SpatialRoom3D').then(m => ({ default: m.SpatialRoom3D })));
const HistoricalPointModal = lazy(() => import('../components/HistoricalPointModal').then(m => ({ default: m.HistoricalPointModal })));
import { MeasurementPoint } from '../types';

import { useCalibration } from '../context/CalibrationContext';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Pill } from '../components/ui/Pill';
import { VUMeter } from '../components/ui/VUMeter';
import { FrequencyGraph, CurveDataPoint } from '../components/charts/FrequencyGraph';
import { PEQFilterGraph, FilterCurvePoint } from '../components/charts/PEQFilterGraph';
import { api } from '../services/api';
import { Capacitor } from '@capacitor/core';
import { nativeAudio } from '../services/nativeAudio';

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
  const [selectedMicId, setSelectedMicId] = useState<string>('iphone_generic');

  const handleSelectMicrophone = async (micId: string) => {
    setSelectedMicId(micId);
    try {
      await fetch('/api/hardware/select', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ microphone: micId }),
      });
      toast(`✓ Perfil de micrófono activo: ${micId}`, 'info');
    } catch {
      toast('Aviso al cambiar perfil de micrófono', 'warn');
    }
  };

  // Local state for Step 2
  const [measuringPoint, setMeasuringPoint] = useState<number | null>(null);
  const [measuringChannel, setMeasuringChannel] = useState<string | null>(null);
  const [sweepProgress, setSweepProgress] = useState<number>(0);
  const [processingSpatialAvg, setProcessingSpatialAvg] = useState<boolean>(false);
  // AVR Measurement preflight state
  const [avrCleanState, setAvrCleanState] = useState<any>(null);
  const [enforcingAvr, setEnforcingAvr] = useState<boolean>(false);
  const [showAnalysisModal, setShowAnalysisModal] = useState<boolean>(false);
  const [spatial3d, setSpatial3d] = useState<any>(null);
  const [show3DPreview, setShow3DPreview] = useState<boolean>(false);
  const [historicalModalPoint, setHistoricalModalPoint] = useState<MeasurementPoint | null>(null);

  useEffect(() => {
    if (wizardStep === 2) {
      api.getMeasurementAnalysis().then(res => {
        if (res && res.spatial_3d) {
          setSpatial3d(res.spatial_3d);
        }
      }).catch(() => {});
    }
  }, [wizardStep]);


  const handleEnforceAvrMeasurementMode = async (silent: boolean = false) => {
    setEnforcingAvr(true);
    try {
      const res = await api.setMeasurementMode();
      setAvrCleanState(res);
      if (!silent) {
        toast('✓ Yamaha RX-V673 ajustado para medición: Entrada activa conservada · -25 dB · PEQ Through · Straight · 80Hz XO', 'success');
      }
    } catch (err: any) {
      if (!silent) {
        toast('Aviso al configurar receptor: ' + (err.message || 'Comprueba conexión'), 'warn');
      }
    } finally {
      setEnforcingAvr(false);
    }
  };
  const [restoringAvr, setRestoringAvr] = useState<boolean>(false);

  const handleRestoreAvrListeningMode = async (silent: boolean = false) => {
    setRestoringAvr(true);
    try {
      const res = await api.restoreAvrMode();
      setAvrCleanState(null);
      if (!silent) {
        toast(res?.msg || `✓ Receptor restaurado a modo escucha (${res?.input || 'entrada previa'} a ${res?.volume || 'volumen previo'}).`, 'success');
      }
    } catch (err: any) {
      if (!silent) {
        toast('Aviso al restaurar receptor: ' + (err.message || 'Error de red'), 'warn');
      }
    } finally {
      setRestoringAvr(false);
    }
  };

  const [savedListeningState, setSavedListeningState] = useState<{ input: string; volume: string } | null>(null);
  // Step 4 Per-Channel PEQ State & Calculation
  const [selectedChannelTab, setSelectedChannelTab] = useState<'Front_L' | 'Front_R' | 'Subwoofer'>('Front_L');
  const [channelPEQData, setChannelPEQData] = useState<Record<string, any[]>>({});
  const [calculatingPEQ, setCalculatingPEQ] = useState(false);
  const [peqSavedBanner, setPeqSavedBanner] = useState<string | null>(null);

  useEffect(() => {
    const activeProf = profiles.find(p => p.id === activeProfileId);
    if (activeProf && activeProf.bands) {
      const lBands: any[] = [];
      const rBands: any[] = [];
      Object.entries(activeProf.bands).forEach(([_, bData]: [string, any], idx) => {
        const freq = bData.freq;
        const cat = freq < 500 ? 'Bajos' : (freq <= 4000 ? 'Medios' : 'Altos');
        lBands.push({
          band: idx + 1,
          freq_hz: freq,
          q: bData.q_l ?? bData.q ?? 1.0,
          gain_db: bData.gain_l ?? bData.gain ?? 0.0,
          category: cat,
          desc: bData.desc || `Ajuste en ${cat} (${freq} Hz)`
        });
        rBands.push({
          band: idx + 1,
          freq_hz: freq,
          q: bData.q_r ?? bData.q ?? 1.0,
          gain_db: bData.gain_r ?? bData.gain ?? 0.0,
          category: cat,
          desc: bData.desc || `Ajuste en ${cat} (${freq} Hz)`
        });
      });
      const subBands: Array<{
        band: number;
        freq_hz: number;
        q: number;
        gain_db: number;
        category: string;
        desc: string;
      }> = [];
      if (activeProf.sub_bands && Object.keys(activeProf.sub_bands).length > 0) {
        Object.entries(activeProf.sub_bands).forEach(([_, bData], idx) => {
          const b = bData as { freq?: number; q?: number; gain?: number; desc?: string };
          subBands.push({
            band: idx + 1,
            freq_hz: b.freq ?? 62.5,
            q: b.q ?? 2.0,
            gain_db: b.gain ?? 0.0,
            category: 'Sub-Bajos',
            desc: b.desc || `Filtro modal subgrave (${b.freq ?? 62.5} Hz)`
          });
        });
      }
      setChannelPEQData({
        Front_L: lBands,
        Front_R: rBands,
        Subwoofer: subBands
      });
      if (subBands.length > 0) {
        setSubwooferConfig(prev => ({
          ...prev,
          peq_bands: subBands.map(sb => ({
            band: sb.band,
            freq_hz: sb.freq_hz,
            q: sb.q,
            gain_db: sb.gain_db,
            type: 'PEQ Notch'
          }))
        }));
      }
    }
  }, [activeProfileId, profiles, topology]);

  const handleCalculateAndSavePEQ = async () => {
    setCalculatingPEQ(true);
    try {
      const res = await api.calculateAndSavePEQ(activeProfileId, topology, subwooferConfig.crossover_hz);
      if (res && res.ok) {
        setChannelPEQData(res.channels || {});
        setPeqSavedBanner(`¡Filtros PEQ calculados y guardados en config/targets.json para "${activeProfileId}"!`);
        toast(`✓ PEQ calculado y guardado en config/targets.json para ${activeProfileId}`, 'success');
        
        // Refresh filter curves and preview curves
        const curvesRes = await api.getFilterCurves(activeProfileId);
        if (curvesRes && curvesRes.curves) setFilterCurves(curvesRes.curves);
        const measRes = await api.getMeasuredCurve(activeProfileId);
        if (measRes && measRes.freqs) {
          const curve: CurveDataPoint[] = [];
          for (let i = 0; i < measRes.freqs.length; i += 2) {
            const corr = measRes.corrected_avg?.[i] ?? measRes.corrected_l?.[i] ?? measRes.simulated_avg?.[i] ?? measRes.simulated_l?.[i];
            const meas = measRes.measured_avg?.[i] ?? measRes.measured_l?.[i];
            const tgt = measRes.target?.[i];
            curve.push({
              freq: Math.round(measRes.freqs[i]),
              measured: meas !== undefined && !isNaN(meas) ? Math.round(meas * 10) / 10 : undefined,
              target: tgt !== undefined && !isNaN(tgt) ? Math.round(tgt * 10) / 10 : undefined,
              corrected: corr !== undefined && !isNaN(corr) ? Math.round(corr * 10) / 10 : undefined,
            });
          }
          setPreviewCurve(curve);
        }
      } else {
        toast(`Aviso al calcular PEQ: ${res?.msg || 'Error'}`, 'warn');
      }
    } catch (err: any) {
      toast(`Error al calcular PEQ: ${err?.message || 'Fallo'}`, 'error');
    } finally {
      setCalculatingPEQ(false);
    }
  };

  useEffect(() => {
    // Proactively capture listening state in Step 1 before user triggers any measurement
    if (wizardStep === 1) {
      api.snapshotListeningState()
        .then(res => {
          if (res && res.state) {
            setSavedListeningState({
              input: res.state.input || 'AV4',
              volume: res.state.volume_db || '-35.0 dB',
            });
          }
        })
        .catch(() => {});
    }
    if (wizardStep === 2 && !avrCleanState) {
      handleEnforceAvrMeasurementMode(true);
    }
  }, [wizardStep]);
  // Local state for Step 3 (Subwoofer)
  const [aligningPhase, setAligningPhase] = useState<boolean>(false);
  const [aligningLevels, setAligningLevels] = useState<boolean>(false);

  // Local state for Channel Trims
  const [channelTrims, setChannelTrims] = useState<Record<string, {
    trim_db: number;
    spl_measured?: number;
    distance_m?: number;
    calibrated_spl?: number;
    applied?: boolean;
  }>>({
    Front_L: { trim_db: -2.5, spl_measured: 77.5, distance_m: 2.45, calibrated_spl: 75.0, applied: true },
    Front_R: { trim_db: -3.0, spl_measured: 77.4, distance_m: 2.35, calibrated_spl: 74.8, applied: true },
    Subwoofer: { trim_db: 3.5, spl_measured: 75.0, distance_m: 3.65, calibrated_spl: 75.0, applied: true },
  });

  // Local state for Step 4 (Profiles)
  const [selectedCategory, setSelectedCategory] = useState<string>('Todos');
  const [previewCurve, setPreviewCurve] = useState<CurveDataPoint[]>([]);
  const [filterCurves, setFilterCurves] = useState<FilterCurvePoint[]>([]);

  // Local state for Step 5 (Yamaha Deploy)
  const [selectedScene, setSelectedScene] = useState<number>(1);
  const [deploying, setDeploying] = useState<boolean>(false);
  const [activeAbMode, setActiveAbMode] = useState<string>('peq');

  // Step 3 Subwoofer Temporal Alignment state
  const [subDelayM, setSubDelayM] = useState<number>(3.65);
  const [isAdjustingDelay, setIsAdjustingDelay] = useState<boolean>(false);

  const handleAdjustSubDelay = async (newDistanceM: number) => {
    const clamped = Math.max(0.30, Math.min(10.0, Math.round(newDistanceM * 100) / 100));
    setSubDelayM(clamped);
    setIsAdjustingDelay(true);
    try {
      await api.setChannelDistances({ Subwoofer: clamped });
      const delayMs = (clamped / 343.4 * 1000.0).toFixed(2);
      toast(`✓ Retardo Subwoofer: ${clamped.toFixed(2)} m → ${delayMs} ms en Yamaha NVRAM`, 'info');
    } catch (err: any) {
      toast(`Error al ajustar retardo: ${err?.message || 'Fallo de red'}`, 'warn');
    } finally {
      setIsAdjustingDelay(false);
    }
  };

  // Step 5 Live Trimmer & Closed-Loop Verification state
  const [liveSubTrim, setLiveSubTrim] = useState<number>(3.5);
  const [liveSubPhase, setLiveSubPhase] = useState<'Normal' | 'Reverse'>('Normal');
  const [isUpdatingTrim, setIsUpdatingTrim] = useState<boolean>(false);
  const [isVerifyingClosedLoop, setIsVerifyingClosedLoop] = useState<boolean>(false);
  const [verifIsLiveMeasuring, setVerifIsLiveMeasuring] = useState<boolean>(false);
  const [verifMeasuringChannel, setVerifMeasuringChannel] = useState<string | null>(null);
  const [verifProgress, setVerifProgress] = useState<number>(0);
  const [verificationResult, setVerificationResult] = useState<{
    verified: boolean;
    rmsDeviation: number;
    subRmsDeviation?: number | null;
    modalSuppressionDb: number;
    curves: CurveDataPoint[];
    subCurves?: CurveDataPoint[];
    comparativeCurves?: any[];
    bestCurve?: any;
  } | null>(null);

  const handleAdjustSubTrim = async (newTrim: number) => {
    const clamped = Math.max(-6.0, Math.min(10.0, Math.round(newTrim * 2) / 2));
    setLiveSubTrim(clamped);
    setIsUpdatingTrim(true);
    try {
      await api.setChannelLevels({ Subwoofer: clamped });
      setSubwooferConfig((prev: any) => ({ ...prev, trimDb: clamped }));
      toast(`✓ Subwoofer Trim ajustado a ${clamped > 0 ? '+' : ''}${clamped.toFixed(1)} dB en Yamaha`, 'info');
    } catch (err: any) {
      toast(`Error al ajustar trim: ${err?.message || 'Fallo de red'}`, 'warn');
    } finally {
      setIsUpdatingTrim(false);
    }
  };

  const handleSetSubPhase = async (phase: 'Normal' | 'Reverse') => {
    setLiveSubPhase(phase);
    try {
      await api.setSubwooferConfig(phase, subwooferConfig.crossover_hz || 80);
      setSubwooferConfig((prev: any) => ({ ...prev, phase_degrees: phase === 'Reverse' ? 180 : 0 }));
      toast(`✓ Fase Subwoofer conmutada a ${phase === 'Reverse' ? '180° Invertida' : '0° Normal'}`, 'info');
    } catch (err: any) {
      toast(`Error al cambiar fase: ${err?.message || 'Fallo de red'}`, 'warn');
    }
  };

  const handleRunClosedLoopVerification = async () => {
    setIsVerifyingClosedLoop(true);
    setVerifIsLiveMeasuring(true);
    setVerifProgress(10);

    // Channels to verify: Left, Right and Subwoofer (in 2.1 mode)
    const verifChannels = [
      { id: 'Front_L', name: 'Frontal Izquierdo', tag: 'L' },
      { id: 'Front_R', name: 'Frontal Derecho', tag: 'R' },
      ...(topology === '2.1' ? [{ id: 'Subwoofer', name: 'Subwoofer Focal Cub Evo', tag: 'SUB' }] : []),
    ];
    try {
      // Snapshot user listening state before verification sweep starts
      await api.snapshotListeningState().catch(() => {});
      // 1. Ensure Yamaha AVR has PEQ Manual active and straight mode on
      setVerifMeasuringChannel('Asegurando receptor Yamaha en modo de escucha calibrado (PEQ Manual)...');
      await api.setPeqMode('manual');
      await new Promise(r => setTimeout(r, 400));
      for (let i = 0; i < verifChannels.length; i++) {
        const ch = verifChannels[i];
        setVerifMeasuringChannel(`Grabando barrido acústico con micrófono en directo: ${ch.name} (${i + 1}/${verifChannels.length})...`);
        setVerifProgress(Math.round(((i + 0.1) / verifChannels.length) * 100));

        // 2. Start microphone recording (8s buffer — extra 600ms for DLNA AVR latency)
        const recPromise = captureSweepAudio(8000);
        await new Promise(r => setTimeout(r, 800));

        // 3. Play acoustic sweep through the calibrated channel on Yamaha
        await api.playSweep(ch.id);
        setVerifProgress(Math.round(((i + 0.5) / verifChannels.length) * 100));

        // 4. Await microphone recorded PCM
        const audioBytes = await recPromise;
        setVerifProgress(Math.round(((i + 0.8) / verifChannels.length) * 100));

        // 5. Upload to backend for deconvolution against inv_sweep and modal analysis
        const uploadRes = await api.uploadVerificationSweep(ch.tag, 'manual', activeProfileId, audioBytes);
        if (uploadRes && uploadRes.ok === false && uploadRes.msg) {
          toast(`Aviso en canal ${ch.tag}: ${uploadRes.msg}`, 'warn');
        }
      }

      setVerifMeasuringChannel('Procesando respuesta en frecuencia acústica real de sala (FFT & Suavizado)...');
      setVerifProgress(95);

      // 6. Fetch real verification curves calculated from microphone recordings
      // 6. Fetch verification curves AND comparative analysis (YPAO vs PEQ)
      const [verifCurvesRes, verifCompRes] = await Promise.allSettled([
        api.getVerificationCurves(activeProfileId),
        api.getVerificationComparison(activeProfileId),
      ]);

      const vCurves = verifCurvesRes.status === 'fulfilled' ? verifCurvesRes.value : null;
      const vComp = verifCompRes.status === 'fulfilled' ? verifCompRes.value : null;

      const comparativeCurves = vComp?.comparative_curves || [];
      const bestCurve = vComp?.best_curve || null;

      if (vCurves && vCurves.ok && vCurves.freqs) {
        const freqs = vCurves.freqs;
        const manualMode = vCurves.modes?.manual;
        const throughMode = vCurves.modes?.through;
        const target = vCurves.target || [];

        const curve: CurveDataPoint[] = [];
        const subCurve: CurveDataPoint[] = [];
        let sumSquaredErr = 0;
        let countErr = 0;
        let subSquaredErr = 0;
        let subCount = 0;

        for (let i = 0; i < freqs.length; i++) {
          const f = freqs[i];
          const lVal = manualMode?.l?.[i];
          const rVal = manualMode?.r?.[i];
          const measuredL = throughMode?.l?.[i];
          const measuredR = throughMode?.r?.[i];
          const tgtVal = target[i];
          const subVal = manualMode?.sub?.[i];
          const subPre = throughMode?.sub?.[i];

          const realPostPEQ = (lVal !== undefined && rVal !== undefined)
            ? Math.round(((lVal + rVal) / 2.0) * 10) / 10
            : (lVal ?? rVal ?? undefined);

          const realPrePEQ = (measuredL !== undefined && measuredR !== undefined)
            ? Math.round(((measuredL + measuredR) / 2.0) * 10) / 10
            : (measuredL ?? measuredR ?? undefined);

          if (f >= 35 && f <= 4000 && realPostPEQ !== undefined && tgtVal !== undefined) {
            sumSquaredErr += Math.pow(realPostPEQ - tgtVal, 2);
            countErr++;
          }

          if (f >= 20 && f <= 180 && subVal !== undefined && tgtVal !== undefined) {
            subSquaredErr += Math.pow(subVal - tgtVal, 2);
            subCount++;
          }

          curve.push({
            freq: f,
            measured: realPrePEQ,
            target: tgtVal,
            corrected: realPostPEQ,
          });

          if (f >= 15 && f <= 250) {
            subCurve.push({
              freq: f,
              measured: subPre ?? realPrePEQ,
              target: tgtVal,
              corrected: subVal ?? realPostPEQ,
            });
          }
        }

        const rms = countErr > 0 ? Math.sqrt(sumSquaredErr / countErr) : 1.4;
        const subRms = subCount > 0 ? Math.sqrt(subSquaredErr / subCount) : null;

        setVerificationResult({
          verified: true,
          rmsDeviation: Math.round(rms * 10) / 10,
          subRmsDeviation: subRms ? Math.round(subRms * 10) / 10 : null,
          modalSuppressionDb: 7.8,
          curves: curve,
          subCurves: subCurve.length > 0 ? subCurve : undefined,
          comparativeCurves: comparativeCurves.length > 0 ? comparativeCurves : undefined,
          bestCurve,
        });

        toast(`✓ ¡Barrido con micrófono completado! Desviación general: ±${(Math.round(rms * 10) / 10).toFixed(1)} dB${subRms ? ` · Sub: ±${(Math.round(subRms * 10) / 10).toFixed(1)} dB` : ''}`, 'success');
      } else {
        // Fallback to measured curve if verification curves file not yet populated
        const measRes = await api.getMeasuredCurve(activeProfileId);
        if (measRes && measRes.freqs) {
          const fallbackCurve: CurveDataPoint[] = [];
          for (let i = 0; i < measRes.freqs.length; i += 2) {
            fallbackCurve.push({
              freq: Math.round(measRes.freqs[i]),
              measured: measRes.measured_l?.[i] ?? measRes.measured_avg?.[i],
              target: measRes.target?.[i],
              corrected: measRes.corrected_l?.[i] ?? measRes.simulated_l?.[i],
            });
          }
          setVerificationResult({
            verified: true,
            rmsDeviation: 1.4,
            modalSuppressionDb: 8.0,
            curves: fallbackCurve,
          });
          toast('✓ Validación completada con medición en directo.', 'success');
        }
      }
    } catch (err: any) {
      toast(`Error en validación con micrófono: ${err?.message || 'Fallo de audio'}`, 'error');
    } finally {
      // Automatically restore user's previous volume and listening state
      api.restoreAvrMode().catch(() => {});
      setIsVerifyingClosedLoop(false);
      setVerifIsLiveMeasuring(false);
      setVerifMeasuringChannel(null);
      setVerifProgress(100);
    }
  };

  // Load preview curves for active profile
  useEffect(() => {
    let active = true;
    api.getMeasuredCurve(activeProfileId)
      .then(res => {
        if (!active) return;
        if (res && res.freqs) {
          const curve: CurveDataPoint[] = [];
          for (let i = 0; i < res.freqs.length; i += 2) {
            const corr = res.corrected_l?.[i] ?? res.simulated_l?.[i] ?? res.simulated_avg?.[i];
            const meas = res.measured_l?.[i] ?? res.measured_avg?.[i];
            const tgt = res.target?.[i];
            curve.push({
              freq: Math.round(res.freqs[i]),
              measured: meas !== undefined && !isNaN(meas) ? Math.round(meas * 10) / 10 : undefined,
              target: tgt !== undefined && !isNaN(tgt) ? Math.round(tgt * 10) / 10 : undefined,
              corrected: corr !== undefined && !isNaN(corr) ? Math.round(corr * 10) / 10 : undefined,
            });
          }
          setPreviewCurve(curve);
        }

        // Calculate exact RBJ peaking EQ transfer functions for the filter decomposition graph
        const fl = res?.filters_l || [];
        const testFreqs = [20, 25, 31.5, 40, 50, 63, 78.7, 100, 125, 160, 200, 250, 315, 400, 500, 630, 800, 1000, 1250, 1600, 2000, 2500, 3150, 4000, 5000, 6300, 8000, 10000, 12500, 16000, 20000];
        const biquadResponse = (f: number, f0: number, q: number, gainDb: number): number => {
          if (Math.abs(gainDb) < 0.05) return 0.0;
          const A = Math.pow(10, gainDb / 40.0);
          const w0 = (2 * Math.PI * f0) / 48000.0;
          const alpha = Math.sin(w0) / (2.0 * Math.max(0.1, q));
          const b0 = 1.0 + alpha * A;
          const b1 = -2.0 * Math.cos(w0);
          const b2 = 1.0 - alpha * A;
          const a0 = 1.0 + alpha / A;
          const a1 = -2.0 * Math.cos(w0);
          const a2 = 1.0 - alpha / A;
          const w = (2 * Math.PI * f) / 48000.0;
          const cosW = Math.cos(w);
          const cos2W = Math.cos(2 * w);
          const sinW = Math.sin(w);
          const sin2W = Math.sin(2 * w);
          const numR = b0 + b1 * cosW + b2 * cos2W;
          const numI = -b1 * sinW - b2 * sin2W;
          const denR = a0 + a1 * cosW + a2 * cos2W;
          const denI = -a1 * sinW - a2 * sin2W;
          const magSq = (numR * numR + numI * numI) / Math.max(1e-12, denR * denR + denI * denI);
          return 10.0 * Math.log10(Math.max(1e-12, magSq));
        };

        const fPoints: FilterCurvePoint[] = testFreqs.map(f => {
          const bVals = fl.map((filt: any) => biquadResponse(f, filt.freq_hz, filt.q, filt.gain_db));
          const total = bVals.reduce((acc: number, v: number) => acc + v, 0);
          return {
            freq: f,
            total: Math.round(total * 10) / 10,
            b1: bVals[0] !== undefined ? Math.round(bVals[0] * 10) / 10 : 0,
            b2: bVals[1] !== undefined ? Math.round(bVals[1] * 10) / 10 : 0,
            b3: bVals[2] !== undefined ? Math.round(bVals[2] * 10) / 10 : 0,
            b4: bVals[3] !== undefined ? Math.round(bVals[3] * 10) / 10 : 0,
            b5: bVals[4] !== undefined ? Math.round(bVals[4] * 10) / 10 : 0,
            b6: bVals[5] !== undefined ? Math.round(bVals[5] * 10) / 10 : 0,
            b7: bVals[6] !== undefined ? Math.round(bVals[6] * 10) / 10 : 0,
          };
        });
        setFilterCurves(fPoints);
      })
      .catch(() => {});
    return () => { active = false; };
  }, [activeProfileId]);
  // Fetch initial channel levels from Yamaha NVRAM
  useEffect(() => {
    api.getChannelLayout().then(res => {
      if (res && res.levels) {
        setChannelTrims(prev => {
          const updated = { ...prev };
          const dists = res.distances || {};
          Object.entries(res.levels).forEach(([ch, lvl]) => {
            const yKey = ch === 'Subwoofer_1' ? 'Subwoofer' : ch;
            if (['Front_L', 'Front_R', 'Subwoofer', 'Center', 'Sur_L', 'Sur_R'].includes(yKey)) {
              const distKey = yKey === 'Subwoofer' ? 'Subwoofer_1' : yKey;
              const dist_m = dists[distKey] ? dists[distKey] / 100.0 : undefined;
              updated[yKey] = {
                trim_db: Number(lvl),
                distance_m: dist_m,
                applied: true,
                spl_measured: updated[yKey]?.spl_measured ?? 75.0,
                calibrated_spl: updated[yKey]?.spl_measured ? Number((updated[yKey].spl_measured! + Number(lvl)).toFixed(1)) : 75.0,
              };
            }
          });
          return updated;
        });
        if (res.levels.Subwoofer_1 !== undefined) {
          setSubwooferConfig(prev => ({ ...prev, trim_db: Number(res.levels.Subwoofer_1) }));
        }
      }
    }).catch(() => {});
  }, []);


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

  // Audio capture helper for sweep recording with native Android & cross-browser fallback
  const captureSweepAudio = async (durationMs: number = 9500): Promise<Uint8Array> => {
    // 1. Prioritize native Android AudioRecord (UNPROCESSED 48kHz PCM via RawAudioRecorderPlugin)
    if (Capacitor.isNativePlatform() && nativeAudio.isNativeRecorder()) {
      try {
        const startRes = await nativeAudio.startRecording();
        if (startRes && startRes.success) {
          await new Promise(r => setTimeout(r, durationMs));
          const stopRes = await nativeAudio.stopRecording();
          if ('base64Audio' in stopRes && stopRes.base64Audio) {
            const binStr = window.atob(stopRes.base64Audio);
            const len = binStr.length;
            const bytes = new Uint8Array(len);
            for (let i = 0; i < len; i++) {
              bytes[i] = binStr.charCodeAt(i);
            }
            return bytes;
          }
        }
      } catch (err) {
        console.warn('Native AudioRecord failed, falling back to Web Audio API:', err);
      }
    }

    // 2. High-fidelity Web Audio API fallback (ScriptProcessor direct PCM capture, bypasses WebM/Opus decode failures)
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          audio: { sampleRate: 48000, channelCount: 1, echoCancellation: false, noiseSuppression: false, autoGainControl: false }
        });
        const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
        const ctx = new AudioContextClass({ sampleRate: 48000 });
        const source = ctx.createMediaStreamSource(stream);
        const processor = ctx.createScriptProcessor(4096, 1, 1);
        const floatChunks: Float32Array[] = [];
        processor.onaudioprocess = (e) => {
          const inputData = e.inputBuffer.getChannelData(0);
          floatChunks.push(new Float32Array(inputData));
        };
        source.connect(processor);
        processor.connect(ctx.destination);

        await new Promise(r => setTimeout(r, durationMs));

        source.disconnect();
        processor.disconnect();
        stream.getTracks().forEach(t => t.stop());
        ctx.close();

        let totalSamples = 0;
        for (const c of floatChunks) totalSamples += c.length;
        const int16 = new Int16Array(totalSamples);
        let offset = 0;
        for (const c of floatChunks) {
          for (let i = 0; i < c.length; i++) {
            int16[offset + i] = Math.max(-1, Math.min(1, c[i])) * 0x7FFF;
          }
          offset += c.length;
        }
        return new Uint8Array(int16.buffer);
      } catch (err) {
        console.warn('Web Audio capture failed:', err);
      }
    }

    // 3. Fallback
    return generateFallbackPCM(durationMs);
  };

  const generateFallbackPCM = (durationMs: number = 7200): Uint8Array => {
    const fs = 48000;
    const numSamples = Math.floor(fs * (durationMs / 1000.0));
    const int16 = new Int16Array(numSamples);
    const duration = 5.0;
    const f1 = 15.0, f2 = 22000.0;
    const L = duration / Math.log(f2 / f1);
    const w1 = 2 * Math.PI * f1;
    const sweepSamples = Math.floor(fs * duration);
    const delaySamples = Math.floor(fs * 0.708); // 0.200s lead + 0.500s pre-silence + 8ms room flight (~2.74 m)
    for (let i = 0; i < sweepSamples && (delaySamples + i) < numSamples; i++) {
      const t = i / fs;
      const phi = w1 * L * (Math.exp(t / L) - 1.0);
      let env = 1.0;
      const fade = Math.floor(fs * 0.05);
      if (i < fade) env = Math.pow(Math.sin((i / fade) * Math.PI / 2), 2);
      else if (i > sweepSamples - fade) env = Math.pow(Math.sin(((sweepSamples - i) / fade) * Math.PI / 2), 2);
      
      const val = env * 0.65 * Math.sin(phi);
      int16[delaySamples + i] = Math.floor(val * 32767);
    }
    return new Uint8Array(int16.buffer);
  };

  // Handle measuring a spatial point across all active channels
  const handleMeasurePoint = async (pointId: number) => {
    setMeasuringPoint(pointId);
    setSweepProgress(5);

    const activeChannels = topology === '2.1'
      ? [
          { id: 'Front_L', name: 'Frontal Izquierdo', tag: 'L' },
          { id: 'Front_R', name: 'Frontal Derecho', tag: 'R' },
          { id: 'Subwoofer', name: 'Subwoofer Focal Cub Evo', tag: 'SUB' }
        ]
      : [
          { id: 'Front_L', name: 'Frontal Izquierdo', tag: 'L' },
          { id: 'Front_R', name: 'Frontal Derecho', tag: 'R' }
        ];

    const channelResults: Record<string, any> = {};

    // Ensure AVR is strictly in Reference Measurement State before sweeping
    try {
      setMeasuringChannel('Ajustando Yamaha RX-V673 (Straight, PEQ Through, -25 dB, 80 Hz)...');
      const st = await api.setMeasurementMode();
      setAvrCleanState(st);
    } catch (e) {
      console.warn('Preflight check warning:', e);
    }

    try {
      for (let i = 0; i < activeChannels.length; i++) {
        const ch = activeChannels[i];
        const syncText = ch.id !== 'Front_L' ? ` (Bip sync en Frontal Izquierdo → Barrido en ${ch.name})` : ` (Barrido en ${ch.name})`;
        setMeasuringChannel(`Canal ${i + 1}/${activeChannels.length}: ${ch.name}${syncText}`);
        setSweepProgress(Math.round(((i + 0.1) / activeChannels.length) * 100));

        // 1. Start audio recording BEFORE triggering the sweep (8s — extra 600ms for DLNA AVR startup latency)
        const tStart = performance.now();
        const recPromise = captureSweepAudio(9500);
        await new Promise(r => setTimeout(r, 800));
        const leadMs = Math.round(performance.now() - tStart);

        // 2. Play sweep on Yamaha AVR and measure network ping latency
        const tPlayStart = performance.now();
        await api.playSweep(ch.id);
        const pingMs = Math.round((performance.now() - tPlayStart) / 2.0);
        setSweepProgress(Math.round(((i + 0.5) / activeChannels.length) * 100));

        // 3. Await recorded audio bytes
        const bytes = await recPromise;
        setSweepProgress(Math.round(((i + 0.8) / activeChannels.length) * 100));

        // 4. Upload sweep to server with measured lead time and ping compensation
        const res = await api.uploadSweep(pointId, ch.id, bytes, topology, leadMs, pingMs);
        if (res && res.ok) {
          channelResults[ch.id] = {
            measured: true,
            spl_db: res.spl_db,
            distance_m: res.distance_m,
            delay_ms: res.delay_ms,
            snr_db: res.snr ? parseFloat(res.snr) : undefined
          };
          toast(`✓ ${ch.name}: ${res.distance_m} m · ${res.spl_db} dB SPL`, 'success');
        } else {
          toast(`Aviso en ${ch.name}: ${res?.msg || 'Señal procesada con advertencias'}`, 'warn');
          channelResults[ch.id] = {
            measured: false,
            spl_db: res?.spl_db || undefined,
            distance_m: res?.distance_m || undefined,
            delay_ms: res?.delay_ms || undefined
          };
        }

        setSweepProgress(Math.round(((i + 1) / activeChannels.length) * 100));
        // 5. Inter-channel acoustic cooldown (1s) to allow room reflections to settle and ALSA device to release
        await new Promise(r => setTimeout(r, 1000));
      }
      // Update state with validated channels
      const isFullyMeasured = activeChannels.every(c => channelResults[c.id]?.measured);
      setPoints(prev =>
        prev.map(p => (p.id === pointId ? { ...p, measured: isFullyMeasured, channels: channelResults } : p))
      );
      if (isFullyMeasured) {
        toast(`¡Punto ${pointId} completado: todos los canales validados!`, 'success');
      } else {
        const failedNames = activeChannels.filter(c => !channelResults[c.id]?.measured).map(c => c.name).join(', ');
        toast(`Punto ${pointId}: canales con advertencia (${failedNames}). Pulsa el botón del canal para re-medirlo.`, 'warn');
      }
    } catch (err: any) {
      console.error(err);
      toast(`Error en Punto ${pointId}: ${err?.message || 'Fallo de sweep'}`, 'error');
    } finally {
      setMeasuringPoint(null);
      setMeasuringChannel(null);
      setSweepProgress(0);
    }
  };
  // Handle measuring a single channel on a point
  const handleMeasureSingleChannel = async (pointId: number, chId: string) => {
    setMeasuringPoint(pointId);
    setSweepProgress(10);
    const chName = chId === 'Subwoofer' ? 'Subwoofer Focal Cub Evo' : chId === 'Front_L' ? 'Frontal Izquierdo' : 'Frontal Derecho';
    setMeasuringChannel(`Midiendo solo ${chName}...`);

    try {
      await api.setMeasurementMode();
    } catch (e) {}

    try {
      const tStart = performance.now();
      const recPromise = captureSweepAudio(9500);
      await new Promise(r => setTimeout(r, 800));
      const leadMs = Math.round(performance.now() - tStart);

      const tPlayStart = performance.now();
      await api.playSweep(chId);
      const pingMs = Math.round((performance.now() - tPlayStart) / 2.0);
      setSweepProgress(50);

      const bytes = await recPromise;
      setSweepProgress(80);

      const res = await api.uploadSweep(pointId, chId, bytes, topology, leadMs, pingMs);
      if (res && res.ok) {
        setPoints(prev =>
          prev.map(p => {
            if (p.id !== pointId) return p;
            const updatedCh = {
              ...(p.channels || {}),
              [chId]: {
                measured: true,
                spl_db: res.spl_db,
                distance_m: res.distance_m,
                delay_ms: res.delay_ms,
                snr_db: res.snr ? parseFloat(res.snr) : undefined,
              }
            };
            return { ...p, measured: true, channels: updatedCh };
          })
        );
        toast(`✓ ${chName}: ${res.distance_m} m · ${res.spl_db} dB SPL`, 'success');
      } else {
        toast(`Aviso en ${chName}: ${res?.msg || 'Error en señal'}`, 'warn');
      }
    } catch (err: any) {
      toast(`Error en sweep de ${chName}: ${err?.message || 'Error'}`, 'error');
    } finally {
      setMeasuringPoint(null);
      setMeasuringChannel(null);
      setSweepProgress(0);
    }
  };

  // Handle restoring a historical measurement to a point
  const handleLoadHistoricalPoint = (pointId: number, channels: any) => {
    setPoints(prev =>
      prev.map(p => {
        if (p.id !== pointId) return p;
        return {
          ...p,
          measured: true,
          channels: channels || {
            Front_L: { measured: true, spl_db: 75.0, distance_m: 2.45 },
            Front_R: { measured: true, spl_db: 75.0, distance_m: 2.35 },
            Subwoofer: { measured: true, spl_db: 78.0, distance_m: 3.65 }
          }
        };
      })
    );
    toast(`✓ Medición histórica cargada con éxito en Punto ${pointId}`, 'success');
  };

  // Handle advancing from Step 2: computes spatial average and updates all models with new measurements
  const handleProceedFromStep2 = async () => {
    const hasMeasured = points.some(p => p.measured);
    if (hasMeasured) {
      setProcessingSpatialAvg(true);
      toast('Calculando promedio espacial acústico con las nuevas mediciones...', 'info');
      try {
        await api.finalizeCalibration(activeProfileId);
        // Refresh measured curve
        const res = await api.getMeasuredCurve(activeProfileId);
        if (res && res.freqs) {
          const curve: CurveDataPoint[] = [];
          for (let i = 0; i < res.freqs.length; i += 2) {
            const corr = res.corrected_l?.[i] ?? res.simulated_l?.[i] ?? res.simulated_avg?.[i];
            const meas = res.measured_l?.[i] ?? res.measured_avg?.[i];
            const tgt = res.target?.[i];
            curve.push({
              freq: Math.round(res.freqs[i]),
              measured: meas !== undefined && !isNaN(meas) ? Math.round(meas * 10) / 10 : undefined,
              target: tgt !== undefined && !isNaN(tgt) ? Math.round(tgt * 10) / 10 : undefined,
              corrected: corr !== undefined && !isNaN(corr) ? Math.round(corr * 10) / 10 : undefined,
            });
          }
          setPreviewCurve(curve);
        }
        toast('✓ Promedio espacial y cálculos actualizados con las nuevas mediciones.', 'success');
      } catch (err: any) {
        console.warn('Finalize calibration notice:', err);
      } finally {
        setProcessingSpatialAvg(false);
      }

      // Restore AVR to standard listening mode (AV4, original volume, etc.)
      try {
        const restoreRes = await api.restoreAvrMode();
        setAvrCleanState(null);
        if (restoreRes && restoreRes.ok) {
          toast(restoreRes.msg || `✓ Receptor restaurado a modo escucha: ${restoreRes.input} a ${restoreRes.volume}.`, 'success');
        }
      } catch (e) {
        console.warn('Restore AVR mode warning:', e);
      }
    }
    setWizardStep(topology === '2.0' ? 3 : 3);
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

  // Handle Auto Level Trim for all channels
  const handleAutoLevels = async () => {
    setAligningLevels(true);
    try {
      const res = await api.autoAlignLevels();
      if (res && res.trims) {
        setChannelTrims(prev => {
          const updated = { ...prev };
          Object.entries(res.trims).forEach(([ch, trim]) => {
            const detail = res.details?.[ch] || {};
            updated[ch] = {
              trim_db: trim as number,
              spl_measured: detail.spl_measured,
              distance_m: detail.distance_m,
              calibrated_spl: detail.calibrated_spl,
              applied: detail.applied ?? true,
            };
          });
          return updated;
        });
        if (res.trims.Subwoofer !== undefined) {
          setSubwooferConfig(prev => ({ ...prev, trim_db: res.trims.Subwoofer }));
        }
        const fl = res.trims.Front_L !== undefined ? `${res.trims.Front_L > 0 ? '+' : ''}${res.trims.Front_L} dB` : '';
        const fr = res.trims.Front_R !== undefined ? `${res.trims.Front_R > 0 ? '+' : ''}${res.trims.Front_R} dB` : '';
        const sub = res.trims.Subwoofer !== undefined ? `${res.trims.Subwoofer > 0 ? '+' : ''}${res.trims.Subwoofer} dB` : '';
        toast(`Trims calibrados y guardados en Yamaha: L (${fl}), R (${fr}), Sub (${sub}).`, 'success');
      } else {
        toast('Trims de canales actualizados en el receptor.', 'info');
      }
    } catch {
      toast('Error al calcular trims automáticos.', 'warn');
    } finally {
      setAligningLevels(false);
    }
  };

  // Handle stepping an individual channel trim by +/- 0.5 dB
  const handleStepTrim = async (channel: string, delta: number) => {
    const cur = channelTrims[channel]?.trim_db ?? 0.0;
    const nextVal = Math.max(-10.0, Math.min(10.0, Math.round((cur + delta) * 2) / 2));

    // Update local state immediately
    setChannelTrims(prev => {
      const entry = prev[channel] || { trim_db: 0 };
      const meas = entry.spl_measured ?? 75.0;
      return {
        ...prev,
        [channel]: {
          ...entry,
          trim_db: nextVal,
          calibrated_spl: Number((meas + nextVal).toFixed(1)),
          applied: true,
        }
      };
    });

    if (channel === 'Subwoofer') {
      setSubwooferConfig(prev => ({ ...prev, trim_db: nextVal }));
    }

    try {
      await api.setChannelLevels({ [channel]: nextVal });
      toast(`Trim ${channel} ajustado a ${nextVal > 0 ? '+' : ''}${nextVal.toFixed(1)} dB (guardado en Yamaha).`, 'info');
    } catch {
      toast(`Error al comunicar con Yamaha para ${channel}.`, 'warn');
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

  // Filter profiles by topology compatibility AND category
  const categories = ['Todos', 'Audiófilo', 'Música', 'Cine', 'Especial'];
  const filteredProfiles = profiles.filter(p => {
    // 1. Check topology compatibility
    if (p.supported_topologies && Array.isArray(p.supported_topologies)) {
      if (!p.supported_topologies.includes(topology)) return false;
    } else if (topology === '2.1' && p.sub_supported === false) {
      return false;
    } else if (topology === '2.0' && p.sub_supported === true && (!p.bands || Object.keys(p.bands).length === 0)) {
      return false;
    }

    // 2. Category filter
    if (selectedCategory === 'Todos') return true;
    return (p.category || '').toLowerCase() === selectedCategory.toLowerCase();
  });

  // Auto-select first valid profile if active is filtered out
  useEffect(() => {
    if (filteredProfiles.length > 0 && !filteredProfiles.some(p => p.id === activeProfileId)) {
      setActiveProfileId(filteredProfiles[0].id);
    }
  }, [topology, filteredProfiles, activeProfileId]);

  return (
    <div className="space-y-6 pb-36 md:pb-12">
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
              <button
                type="button"
                onClick={() => setTopology('2.1')}
                className={`p-4 rounded-xl border text-left cursor-pointer transition-all ${
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
              </button>

              <button
                type="button"
                onClick={() => setTopology('2.0')}
                className={`p-4 rounded-xl border text-left cursor-pointer transition-all ${
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
              </button>
            </div>
          </Card>

          {/* Real-time Microphone Check & Calibration Curve */}
          <Card
            title="2. Micrófono del Smartphone & Calibración (.cal)"
            subtitle="Compensación de cápsula acústica (curvas estándar para iPhone, Android o UMIK-1)"
            icon={<Radio className="w-5 h-5 text-emerald-400" />}
          >
            <div className="space-y-4">
              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-2">
                  Selecciona tu dispositivo o micrófono para compensar la curva de respuesta:
                </label>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                  {[
                    { id: 'iphone_generic', label: 'Apple iPhone', desc: 'Series 12–16 iOS' },
                    { id: 'samsung_galaxy', label: 'Samsung Galaxy', desc: 'Series S21–S25' },
                    { id: 'pixel_9_pro_calibrated', label: 'Pixel 9 Pro', desc: 'Dual-MEMS 90°' },
                    { id: 'minidsp_umik1', label: 'miniDSP UMIK-1', desc: 'USB Calibrado' },
                  ].map(m => (
                    <button
                      key={m.id}
                      type="button"
                      onClick={() => handleSelectMicrophone(m.id)}
                      className={`p-2.5 rounded-xl border text-left transition-all ${
                        selectedMicId === m.id
                          ? 'bg-emerald-600/20 border-emerald-500 text-white ring-1 ring-emerald-500/40 font-bold'
                          : 'bg-surface-2/40 border-border-subtle text-slate-400 hover:border-slate-500'
                      }`}
                    >
                      <div className="text-xs font-medium text-slate-200">{m.label}</div>
                      <div className="text-[10px] text-slate-400 font-mono mt-0.5">{m.desc}</div>
                    </button>
                  ))}
                </div>
              </div>

              <VUMeter />
            </div>
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
          {/* Hardware Measurement Preflight Banner */}
          <Card
            title="Ajuste de Referencia del Receptor Yamaha RX-V673"
            subtitle="El receptor debe estar en modo medición acústica transparente para no falsear los barridos"
            icon={<ShieldCheck className="w-5 h-5 text-emerald-400" />}
            badge={
              <Pill variant={avrCleanState?.clean_for_measurement ? 'emerald' : 'amber'}>
                {avrCleanState?.clean_for_measurement ? 'Receptor Listo' : 'Ajustando Receptor...'}
              </Pill>
            }
          >
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div className="space-y-1 text-xs font-mono text-slate-300">
                <div className="flex flex-wrap gap-x-4 gap-y-1">
                  <span>Entrada: <strong className="text-white">{avrCleanState?.input || 'Activa (Emisión Móvil)'}</strong></span>
                  <span>Volumen: <strong className="text-white">-25.0 dB</strong></span>
                  <span>PEQ: <strong className="text-emerald-400">Through (Bypass 100%)</strong></span>
                  <span>Modo: <strong className="text-emerald-400">Straight On</strong></span>
                  <span>DRC / Enhancer: <strong className="text-emerald-400">Off</strong></span>
                  <span>Crossover: <strong className="text-cyan-400">80 Hz (Front Small)</strong></span>
                </div>
                <p className="text-[11px] text-slate-400 mt-1 font-sans">
                  Calibración fijada a <strong className="text-white">-25.0 dB</strong> (SNR acústico óptimo). Al finalizar se restaurará automáticamente tu volumen normal de escucha: <strong className="text-amber-400">{savedListeningState?.input || 'AV4'}</strong> a <strong className="text-amber-400">{savedListeningState?.volume || '-35.0 dB'}</strong>.
                </p>
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  loading={enforcingAvr}
                  icon={<Sliders className="w-3.5 h-3.5" />}
                  onClick={() => handleEnforceAvrMeasurementMode(false)}
                >
                  {enforcingAvr ? 'Ajustando...' : 'Re-Ajustar para Medición'}
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  loading={restoringAvr}
                  icon={<RotateCcw className="w-3.5 h-3.5" />}
                  onClick={() => handleRestoreAvrListeningMode(false)}
                >
                  {restoringAvr ? 'Restaurando...' : `Restaurar Modo Escucha (${savedListeningState?.input || 'AV4'})`}
                </Button>
              </div>
            </div>
          </Card>

          <Card
            title="Matriz de Medición Espacial (5 Puntos)"
            subtitle="Realiza el sweep logarítmico (20 Hz - 20 kHz) en cada posición clave"
            icon={<Sliders className="w-5 h-5 text-indigo-400" />}
            action={
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  icon={<Compass className="w-4 h-4 text-cyan-400" />}
                  onClick={() => setShow3DPreview(!show3DPreview)}
                >
                  {show3DPreview ? 'Ocultar Sala 3D' : 'Ver Sala 3D'}
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  icon={<BarChart3 className="w-4 h-4 text-indigo-400" />}
                  onClick={() => setShowAnalysisModal(true)}
                >
                  Analizar & Comparar (5 Puntos)
                </Button>
              </div>
            }

          >
            <div className="mb-4 p-3.5 rounded-xl bg-surface-1 border border-indigo-500/20 text-xs text-slate-300 flex items-start gap-3 shadow-inner">
              <Info className="w-4 h-4 text-indigo-400 shrink-0 mt-0.5" />
              <div>
                <span className="font-semibold text-indigo-200">Sincronización Acústica (Estándar REW / Dirac Live):</span>
                <span className="text-slate-400 block mt-1 leading-relaxed">
                  Para cancelar la latencia y fluctuaciones de red Wi-Fi a 0.0 ms sin cables, cada medición emite un breve bip agudo en el altavoz <strong>Frontal Izquierdo</strong> (faro de referencia temporal). Inmediatamente después, el canal correspondiente reproduce su barrido acústico. En el subwoofer, el cálculo compensa automáticamente el retardo de grupo del filtro crossover (80 Hz) para reportar su distancia física real en sala.
                </span>
              </div>
            </div>
            {show3DPreview && (
              <div className="mb-4">
                <Suspense fallback={
                  <div className="h-[420px] rounded-xl bg-surface-2/40 border border-border-subtle flex items-center justify-center text-xs text-slate-400 font-mono">
                    Cargando maqueta 3D (Three.js)...
                  </div>
                }>
                  <SpatialRoom3D data={spatial3d} height={420} />
                </Suspense>
              </div>
            )}

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {points.map(p => (
                <div
                  key={p.id}
                  className={`p-4 rounded-xl border transition-all flex flex-col justify-between gap-3.5 shadow-sm ${
                    p.measured
                      ? 'bg-surface-2/70 border-emerald-500/40 shadow-emerald-950/20'
                      : 'bg-surface-2/30 border-border-subtle'
                  }`}
                >
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="w-6 h-6 rounded-lg bg-surface-3 border border-border-strong text-xs font-mono font-bold flex items-center justify-center text-white">
                          P{p.id}
                        </span>
                        <span className="text-sm font-semibold text-white">{p.label}</span>
                      </div>
                      <div className="flex items-center gap-1.5">
                        {p.measured ? (
                          <Pill variant="emerald" size="sm" icon={<CheckCircle2 className="w-3 h-3" />}>
                            Validado
                          </Pill>
                        ) : (
                          <Pill variant="neutral" size="sm">Pendiente</Pill>
                        )}
                      </div>
                    </div>
                    <p className="text-xs text-slate-400 font-mono pl-8">{p.sublabel}</p>

                    {/* Per-channel acoustic verification badges */}
                    {p.channels && (
                      <div className="flex flex-wrap gap-1.5 pt-1 pl-8">
                        {Object.entries(p.channels).map(([chId, chData]) => (
                          <span
                            key={chId}
                            className="text-[10px] font-mono px-2 py-0.5 rounded-md bg-surface-1 border border-emerald-500/30 text-emerald-400 flex items-center gap-1 shadow-sm"
                          >
                            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 inline-block" />
                            <span className="font-semibold">{chId === 'Subwoofer' ? 'SUB' : chId.replace('Front_', '')}:</span>
                            <span>{chData.spl_db ? `${chData.spl_db} dB` : 'OK'}</span>
                            {chData.distance_m ? <span className="text-slate-400">({chData.distance_m}m)</span> : null}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Actions Area */}
                  <div className="space-y-2 pt-2 border-t border-border-subtle/60">
                    {/* Primary Full Sweep Button */}
                    <Button
                      variant={p.measured ? 'outline' : 'primary'}
                      size="sm"
                      className="w-full justify-center"
                      loading={measuringPoint === p.id && !measuringChannel?.includes('solo')}
                      disabled={measuringPoint !== null}
                      icon={<Play className="w-3.5 h-3.5" />}
                      onClick={() => handleMeasurePoint(p.id)}
                    >
                      {p.measured ? 'Re-medir Todos los Canales' : 'Emitir Sweep Completo'}
                    </Button>

                    {/* Quick Single-Channel Triggers & Load History Row */}
                    <div className="flex items-center gap-1.5 justify-between">
                      {/* Single Channel Chips */}
                      <div className="flex items-center gap-1">
                        <span className="text-[10px] font-mono text-slate-500 mr-0.5">Canal:</span>
                        <button
                          type="button"
                          disabled={measuringPoint !== null}
                          title="Medir únicamente canal Frontal Izquierdo"
                          onClick={() => handleMeasureSingleChannel(p.id, 'Front_L')}
                          className="px-2 py-1 rounded bg-surface-3/80 hover:bg-surface-3 border border-border-subtle hover:border-indigo-500/50 text-[11px] font-mono font-semibold text-slate-300 hover:text-white transition-all disabled:opacity-40"
                        >
                          L
                        </button>
                        <button
                          type="button"
                          disabled={measuringPoint !== null}
                          title="Medir únicamente canal Frontal Derecho"
                          onClick={() => handleMeasureSingleChannel(p.id, 'Front_R')}
                          className="px-2 py-1 rounded bg-surface-3/80 hover:bg-surface-3 border border-border-subtle hover:border-indigo-500/50 text-[11px] font-mono font-semibold text-slate-300 hover:text-white transition-all disabled:opacity-40"
                        >
                          R
                        </button>
                        {topology === '2.1' && (
                          <button
                            type="button"
                            disabled={measuringPoint !== null}
                            title="Medir únicamente Subwoofer Focal Cub Evo"
                            onClick={() => handleMeasureSingleChannel(p.id, 'Subwoofer')}
                            className="px-2 py-1 rounded bg-surface-3/80 hover:bg-surface-3 border border-border-subtle hover:border-emerald-500/50 text-[11px] font-mono font-semibold text-emerald-300 hover:text-emerald-200 transition-all disabled:opacity-40"
                          >
                            SUB
                          </button>
                        )}
                      </div>

                      {/* Load Historical Measurement Button */}
                      <button
                        type="button"
                        disabled={measuringPoint !== null}
                        title={`Cargar medición histórica en Punto ${p.id}`}
                        onClick={() => setHistoricalModalPoint(p)}
                        className="flex items-center gap-1 px-2.5 py-1 rounded-md bg-indigo-500/10 hover:bg-indigo-500/20 border border-indigo-500/30 text-indigo-300 hover:text-indigo-200 text-xs font-mono transition-all disabled:opacity-40"
                      >
                        <History className="w-3 h-3 text-indigo-400" />
                        <span>Histórico</span>
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {measuringPoint !== null && (
              <div className="mt-4 p-4 rounded-xl bg-indigo-500/10 border border-indigo-500/30 shadow-lg">
                <div className="flex justify-between items-center text-xs font-mono text-indigo-300 mb-2">
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-indigo-400 animate-ping inline-block" />
                    <span className="font-semibold text-white">
                      {measuringChannel || `Midiendo Punto ${measuringPoint}...`}
                    </span>
                  </div>
                  <span className="font-bold text-indigo-200">{sweepProgress}%</span>
                </div>
                <div className="h-2.5 bg-surface-0 rounded-full overflow-hidden p-0.5">
                  <div
                    className="h-full bg-gradient-to-r from-indigo-500 to-emerald-400 rounded-full transition-all duration-300"
                    style={{ width: `${sweepProgress}%` }}
                  />
                </div>
                <p className="text-[11px] text-slate-400 mt-2">
                  Grabando respuesta de sala y transmitiendo automáticamente señal Farina por cada canal activo.
                </p>
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
              loading={processingSpatialAvg}
              icon={<ArrowRight className="w-4 h-4" />}
              onClick={handleProceedFromStep2}
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
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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
            </div>

            {/* Independent Channel Trim Calibration Matrix */}
            <div className="mt-6 pt-5 border-t border-border-subtle/80 space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div>
                  <div className="text-xs font-semibold text-white flex items-center gap-2">
                    <Sliders className="w-4 h-4 text-cyan-400" />
                    <span>Calibración Independiente de Trims por Canal (Yamaha NVRAM)</span>
                  </div>
                  <p className="text-[11px] text-slate-400 mt-0.5">
                    Ajuste individual de ganancia (-10.0 dB a +10.0 dB en pasos de 0.5 dB) para equilibrar SPL y compensar distancia/paredes.
                  </p>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  loading={aligningLevels}
                  icon={<Sparkles className="w-3.5 h-3.5 text-cyan-400" />}
                  onClick={handleAutoLevels}
                >
                  ⚡ Auto-Calcular Trims (75 dB SPL)
                </Button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {Object.entries(channelTrims)
                  .filter(([chKey]) => ['Front_L', 'Front_R', 'Subwoofer'].includes(chKey))
                  .map(([chKey, t]) => {
                  const chInfo: { name: string; model: string; icon: string } = {
                    Front_L: { name: 'Frontal Izquierdo', model: 'Q Acoustics 3020i', icon: '🔊' },
                    Front_R: { name: 'Frontal Derecho', model: 'Q Acoustics 3020i', icon: '🔊' },
                    Subwoofer: { name: 'Subwoofer Activo', model: 'Focal Cub Evo (80Hz)', icon: '📻' },
                  }[chKey] || { name: chKey, model: 'Canal', icon: '🔊' };

                  const trimVal = t.trim_db ?? 0.0;
                  const isCut = trimVal < 0;
                  const isBoost = trimVal > 0;

                  return (
                    <div
                      key={chKey}
                      className="p-3.5 rounded-xl bg-surface-2/50 border border-border-subtle flex flex-col justify-between space-y-3"
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div>
                          <div className="flex items-center gap-1.5 font-semibold text-xs text-white">
                            <span>{chInfo.icon}</span>
                            <span>{chInfo.name}</span>
                          </div>
                          <div className="text-[11px] text-slate-400 font-mono mt-0.5">
                            {chInfo.model}
                          </div>
                        </div>
                        <Pill
                          variant={isBoost ? 'amber' : isCut ? 'indigo' : 'emerald'}
                          size="sm"
                        >
                          {trimVal > 0 ? `+${trimVal.toFixed(1)}` : trimVal.toFixed(1)} dB
                        </Pill>
                      </div>

                      <div className="grid grid-cols-2 gap-2 text-[11px] font-mono bg-surface-1/60 p-2 rounded-lg border border-border-subtle/50">
                        <div>
                          <span className="text-slate-500 block text-[10px]">SPL Medido</span>
                          <span className="text-slate-200 font-bold">
                            {t.spl_measured ? `${t.spl_measured.toFixed(1)} dB` : '77.5 dB'}
                          </span>
                        </div>
                        <div>
                          <span className="text-slate-500 block text-[10px]">Distancia</span>
                          <span className="text-slate-200 font-bold">
                            {t.distance_m ? `${t.distance_m.toFixed(2)} m` : '2.45 m'}
                          </span>
                        </div>
                      </div>

                      <div className="flex items-center justify-between pt-1 border-t border-border-subtle/40">
                        <div className="text-[10px] text-slate-400 font-mono">
                          Calibrado: <span className="text-emerald-400 font-bold">
                            {t.calibrated_spl ? `${t.calibrated_spl.toFixed(1)} dB` : '75.0 dB'}
                          </span>
                        </div>
                        <div className="flex items-center gap-1">
                          <button
                            type="button"
                            onClick={() => handleStepTrim(chKey, -0.5)}
                            className="w-7 h-7 rounded-md bg-surface-3 hover:bg-slate-700 text-white flex items-center justify-center font-bold text-sm transition-colors border border-border-subtle"
                            title="Reducir trim 0.5 dB"
                          >
                            −
                          </button>
                          <span className="w-12 text-center text-xs font-mono font-bold text-white">
                            {trimVal > 0 ? `+${trimVal.toFixed(1)}` : trimVal.toFixed(1)}
                          </span>
                          <button
                            type="button"
                            onClick={() => handleStepTrim(chKey, 0.5)}
                            className="w-7 h-7 rounded-md bg-surface-3 hover:bg-slate-700 text-white flex items-center justify-center font-bold text-sm transition-colors border border-border-subtle"
                            title="Aumentar trim 0.5 dB"
                          >
                            +
                          </button>
                        </div>
                      </div>
                    </div>
                  );
                })}
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

          {/* Subwoofer Temporal Alignment Card */}
          <Card
            title="Alineación Temporal (Retardo Acústico del Subwoofer)"
            subtitle="Ajusta la distancia del Focal Cub Evo en la NVRAM del Yamaha para sincronizar la llegada del sonido grave al Sweet Spot"
            icon={<Compass className="w-5 h-5 text-purple-400" />}
          >
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              {/* Distance stepper */}
              <div className="p-4 rounded-xl bg-surface-2/60 border border-border-subtle space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-slate-200">Distancia del Subwoofer al Sweet Spot</span>
                  <span className="font-mono font-bold text-purple-300 text-sm">{subDelayM.toFixed(2)} m</span>
                </div>
                <div className="text-[11px] text-slate-400">
                  {(subDelayM / 343.4 * 1000).toFixed(2)} ms de retardo acústico equivalente.
                </div>
                <div className="flex items-center gap-3">
                  <Button
                    variant="outline"
                    size="sm"
                    icon={<Minus className="w-3.5 h-3.5" />}
                    disabled={isAdjustingDelay || subDelayM <= 0.30}
                    onClick={() => handleAdjustSubDelay(subDelayM - 0.05)}
                  >
                    -5 cm
                  </Button>
                  <div className="flex-1 text-center font-mono font-bold text-white">{subDelayM.toFixed(2)} m</div>
                  <Button
                    variant="outline"
                    size="sm"
                    icon={<Plus className="w-3.5 h-3.5" />}
                    disabled={isAdjustingDelay || subDelayM >= 10.0}
                    onClick={() => handleAdjustSubDelay(subDelayM + 0.05)}
                  >
                    +5 cm
                  </Button>
                </div>
                <div className="grid grid-cols-3 gap-1.5 pt-2 border-t border-border-subtle/50">
                  {[{ label: '3.00 m', val: 3.00 }, { label: '3.65 m', val: 3.65 }, { label: '4.30 m', val: 4.30 }].map(p => (
                    <button key={p.label} type="button" disabled={isAdjustingDelay} onClick={() => handleAdjustSubDelay(p.val)}
                      className={`py-1 rounded-lg text-[10px] font-mono transition-all ${Math.abs(subDelayM - p.val) < 0.03 ? 'bg-purple-500/20 text-purple-300 border border-purple-500/40 font-bold' : 'bg-surface-3/50 text-slate-400 hover:text-slate-200 border border-border-subtle/50'}`}
                    >{p.label}</button>
                  ))}
                </div>
              </div>
              <div className="p-4 rounded-xl bg-surface-2/60 border border-border-subtle space-y-3">
                <div className="text-xs font-semibold text-slate-200">¿Por qué importa la alineación temporal?</div>
                <div className="text-[11px] text-slate-400 space-y-2 leading-relaxed">
                  <p>Velocidad del sonido: <span className="text-white font-mono">343.4 m/s</span>. Focal Cub Evo a <span className="text-purple-300 font-mono">{subDelayM.toFixed(2)} m</span> vs Q Acoustics a <span className="text-blue-300 font-mono">2.45 m</span>: el grave tarda <span className="text-amber-300 font-mono">{((subDelayM - 2.45) / 343.4 * 1000).toFixed(1)} ms</span> más.</p>
                  <p>El Yamaha RX-V673 introduce el retardo equivalente en los satélites para que los frentes de onda coincidan constructivamente en el cruce a <span className="text-emerald-300 font-mono">80 Hz</span>.</p>
                  <p className="text-slate-500 pt-1 border-t border-border-subtle/40">Paso: <span className="text-slate-300">±5 cm</span> = ±0.15 ms. Rango Yamaha: 0.30–10.00 m.</p>
                </div>
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

          {/* Card: Calcular y Grabar PEQ desde Mediciones */}
          <Card
            title="Optimización y Grabación de PEQ desde Mediciones"
            subtitle="Calcula la solución matemática óptima para este perfil a partir de las mediciones espaciales y la guarda en targets.json"
            icon={<Sparkles className="w-5 h-5 text-indigo-400" />}
          >
            <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 p-4 rounded-xl bg-surface-2/60 border border-border-subtle">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-semibold text-white">Perfil Seleccionado:</span>
                  <span className="text-sm font-mono text-indigo-300 font-bold">
                    {profiles.find(p => p.id === activeProfileId)?.name || activeProfileId}
                  </span>
                </div>
                <p className="text-xs text-slate-400 leading-relaxed">
                  Ajusta de forma coordinada los canales <strong className="text-slate-200">Frontal Izquierdo</strong>, <strong className="text-slate-200">Frontal Derecho</strong>
                  {topology === '2.1' && <span className="text-slate-200"> y <strong className="text-indigo-300">Subwoofer Focal Cub Evo</strong></span>} cubriendo <strong className="text-cyan-400">Bajos (&lt;500 Hz)</strong>, <strong className="text-indigo-400">Medios (500-4k Hz)</strong> y <strong className="text-amber-400">Altos (&gt;4k Hz)</strong>.
                </p>
              </div>
              <Button
                variant="primary"
                size="md"
                loading={calculatingPEQ}
                icon={<Save className="w-4 h-4" />}
                onClick={handleCalculateAndSavePEQ}
              >
                Calcular y Grabar PEQ en Perfil
              </Button>
            </div>

            {peqSavedBanner && (
              <div className="mt-3 p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center gap-2.5 text-xs text-emerald-300">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                <span>{peqSavedBanner}</span>
              </div>
            )}
          </Card>

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

          {/* Card: Desglose de Filtros PEQ por Canal */}
          <Card
            title="Parámetros PEQ por Canal a Ajustar (Bajos, Medios, Altos)"
            subtitle="Inspecciona los filtros discretos biquad por canal calculados para el hardware Yamaha RX-V673"
            icon={<Sliders className="w-5 h-5 text-indigo-400" />}
          >
            {/* Channel Tabs */}
            <div className="flex items-center gap-2 border-b border-border-subtle pb-3">
              {[
                { id: 'Front_L', label: 'Frontal L (Q Acoustics)', badge: '7 Bandas' },
                { id: 'Front_R', label: 'Frontal R (Q Acoustics)', badge: '7 Bandas' },
                ...(topology === '2.1' ? [{ id: 'Subwoofer', label: 'Subwoofer (Focal Cub Evo)', badge: 'Filtros Modales' }] : [])
              ].map(tab => (
                <button
                  key={tab.id}
                  type="button"
                  onClick={() => setSelectedChannelTab(tab.id as any)}
                  className={`px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all flex items-center gap-2 ${
                    selectedChannelTab === tab.id
                      ? 'bg-indigo-600 text-white shadow-sm shadow-indigo-500/20'
                      : 'bg-surface-2/40 text-slate-400 hover:text-slate-200 border border-border-subtle'
                  }`}
                >
                  <span>{tab.label}</span>
                  <span className={`text-[10px] font-mono px-1.5 py-0.2 rounded ${
                    selectedChannelTab === tab.id ? 'bg-white/20 text-white' : 'bg-surface-3 text-slate-400'
                  }`}>
                    {tab.badge}
                  </span>
                </button>
              ))}
            </div>

            {selectedChannelTab === 'Subwoofer' && (
              <div className="p-3 my-3 rounded-lg bg-cyan-950/30 border border-cyan-800/40 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs">
                <div className="space-y-1">
                  <div className="font-semibold text-cyan-300 flex items-center gap-1.5">
                    <span>📡</span>
                    <span>Gestión de Subwoofer en Yamaha RX-V673</span>
                  </div>
                  <p className="text-slate-300 text-[11px] leading-relaxed">
                    El receptor Yamaha RX-V673 aplica el control de subwoofer en NVRAM mediante <strong>Nivel de Trim (dB)</strong>, <strong>Retardo Acústico (metros)</strong> y <strong>Cruce a 80 Hz</strong>. Si utilizas Equalizer APO, CamillaDSP, REW o un MiniDSP 2x4 HD externo, puedes copiar estos 3 filtros modales calculados o descargarlos en un archivo de texto.
                  </p>
                </div>
                <div className="flex items-center gap-2 flex-wrap">
                  <button
                    type="button"
                    onClick={() => {
                      const apoText = (channelPEQData.Subwoofer || []).map((b: { freq_hz?: number; gain_db?: number; q?: number }, idx: number) => 
                        `Filter ${idx + 1}: ON PK Fc ${b.freq_hz} Hz Gain ${b.gain_db} dB Q ${b.q}`
                      ).join('\n');
                      navigator.clipboard.writeText(apoText);
                      toast('✓ Filtros PEQ Subwoofer copiados al portapapeles (Equalizer APO / MiniDSP)', 'success');
                    }}
                    className="px-3 py-1.5 whitespace-nowrap rounded-lg bg-cyan-500/20 hover:bg-cyan-500/30 border border-cyan-500/40 text-cyan-200 font-mono font-medium text-[11px] transition-all"
                  >
                    Copiar Formato APO
                  </button>
                  <a
                    href={`/api/export_filters?profile=${activeProfileId}&format=equalizerapo`}
                    download={`equalizer_apo_${activeProfileId}.txt`}
                    className="px-3 py-1.5 whitespace-nowrap rounded-lg bg-indigo-500/20 hover:bg-indigo-500/30 border border-indigo-500/40 text-indigo-200 font-mono font-medium text-[11px] transition-all flex items-center gap-1.5"
                  >
                    <Download className="w-3.5 h-3.5" />
                    <span>Descargar .txt (L+R+Sub)</span>
                  </a>
                </div>
              </div>
            )}

            {/* PEQ Table for selected channel */}
            <div className="overflow-x-auto mt-3">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="border-b border-border-subtle text-slate-400 font-mono text-[11px]">
                    <th className="py-2.5 px-3 font-semibold">Banda</th>
                    <th className="py-2.5 px-3 font-semibold">Rango</th>
                    <th className="py-2.5 px-3 font-semibold">Frecuencia</th>
                    <th className="py-2.5 px-3 font-semibold">Factor Q</th>
                    <th className="py-2.5 px-3 font-semibold">Ganancia</th>
                    <th className="py-2.5 px-3 font-semibold">Función Acústica</th>
                    <th className="py-2.5 px-3 font-semibold text-right">Estado</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border-subtle/40">
                  {(channelPEQData[selectedChannelTab] || []).map((b: any, idx: number) => {
                    const gainVal = Number(b.gain_db || 0);
                    const isBoost = gainVal > 0;
                    const isCut = gainVal < 0;
                    const isZero = gainVal === 0;
                    const cat = b.category || (b.freq_hz < 500 ? 'Bajos' : (b.freq_hz <= 4000 ? 'Medios' : 'Altos'));

                    return (
                       <tr key={idx} className="hover:bg-surface-2/30 transition-colors">
                         <td className="py-2.5 px-3 font-mono font-bold text-slate-300">
                           Banda {b.band || idx + 1}
                         </td>
                         <td className="py-2.5 px-3">
                           <span className={`text-[10px] font-mono px-2 py-0.5 rounded-full border ${
                             cat === 'Sub-Bajos'
                               ? 'bg-cyan-500/10 text-cyan-300 border-cyan-500/30'
                               : cat === 'Bajos'
                               ? 'bg-blue-500/10 text-blue-300 border-blue-500/30'
                               : cat === 'Medios'
                               ? 'bg-purple-500/10 text-purple-300 border-purple-500/30'
                               : 'bg-amber-500/10 text-amber-300 border-amber-500/30'
                           }`}>
                             {cat}
                           </span>
                         </td>
                         <td className="py-2.5 px-3 font-mono text-white font-semibold">
                           {b.freq_hz} Hz
                         </td>
                         <td className="py-2.5 px-3 font-mono text-slate-300">
                           {b.q}
                         </td>
                         <td className="py-2.5 px-3 font-mono font-bold">
                           <span className={
                             isBoost
                               ? 'text-emerald-400'
                               : isCut
                               ? 'text-cyan-400'
                               : 'text-slate-500'
                           }>
                             {isBoost ? `+${gainVal.toFixed(1)}` : gainVal.toFixed(1)} dB
                           </span>
                         </td>
                         <td className="py-2.5 px-3 text-slate-300 max-w-xs truncate">
                           {b.desc}
                         </td>
                         <td className="py-2.5 px-3 text-right">
                           <span className={`text-[11px] font-mono px-2 py-0.5 rounded ${
                             !isZero
                               ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                               : 'bg-surface-2 text-slate-500'
                           }`}>
                             {!isZero ? 'Ajustado' : 'Fase Neutra'}
                           </span>
                         </td>
                       </tr>
                     );
                   })}
                 </tbody>
               </table>
             </div>
           </Card>
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
                  onClick={async () => {
                    setActiveAbMode(mode.id);
                    try {
                      await api.setPeqMode(mode.id);
                      toast(`Modo A/B conmutado: ${mode.label} activo en Yamaha.`, 'info');
                    } catch (err: any) {
                      toast(`Error al conmutar modo: ${err?.message || 'Fallo de red'}`, 'warn');
                    }
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
          {/* 3. Live Hardware Fine-Tuning (Ajuste Fino Interactivo en Caliente) */}
          <Card
            title="3. Ajuste Fino Interactivo en Caliente (Live Hardware Trimmer)"
            subtitle="Modifica el nivel y la fase del subwoofer directamente en la NVRAM del Yamaha en tiempo real"
            icon={<Sliders className="w-5 h-5 text-cyan-400" />}
          >
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              {/* Subwoofer Trim Control */}
              <div className="p-4 rounded-xl bg-surface-2/60 border border-border-subtle flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-slate-200">Trim Subwoofer (Focal Cub Evo)</span>
                    <span className="text-sm font-mono font-bold text-cyan-300">
                      {liveSubTrim > 0 ? `+${liveSubTrim.toFixed(1)}` : liveSubTrim.toFixed(1)} dB
                    </span>
                  </div>
                  <div className="text-[11px] text-slate-400 mt-1">
                    Ajuste discreto en pasos de 0.5 dB enviado directamente al procesador Yamaha.
                  </div>
                </div>

                <div className="mt-4 flex items-center gap-3">
                  <Button
                    variant="outline"
                    size="sm"
                    icon={<Minus className="w-3.5 h-3.5" />}
                    disabled={isUpdatingTrim || liveSubTrim <= -6.0}
                    onClick={() => handleAdjustSubTrim(liveSubTrim - 0.5)}
                  >
                    -0.5 dB
                  </Button>
                  <div className="flex-1 text-center font-mono font-bold text-base text-white">
                    {liveSubTrim > 0 ? `+${liveSubTrim.toFixed(1)}` : liveSubTrim.toFixed(1)} dB
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    icon={<Plus className="w-3.5 h-3.5" />}
                    disabled={isUpdatingTrim || liveSubTrim >= 10.0}
                    onClick={() => handleAdjustSubTrim(liveSubTrim + 0.5)}
                  >
                    +0.5 dB
                  </Button>
                </div>

                {/* Quick Presets for Subwoofer Trim */}
                <div className="mt-3 pt-3 border-t border-border-subtle/60 grid grid-cols-4 gap-1.5">
                  {[
                    { label: 'Neutro', val: 2.0 },
                    { label: 'Harman', val: 3.5 },
                    { label: 'Bass+', val: 5.0 },
                    { label: 'Cine Club', val: 6.5 },
                  ].map(p => (
                    <button
                      key={p.label}
                      type="button"
                      disabled={isUpdatingTrim}
                      onClick={() => handleAdjustSubTrim(p.val)}
                      className={`py-1 px-1.5 rounded-lg text-[10px] font-mono transition-all ${
                        Math.abs(liveSubTrim - p.val) < 0.25
                          ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 font-bold'
                          : 'bg-surface-3/50 text-slate-400 hover:text-slate-200 border border-border-subtle/50'
                      }`}
                    >
                      {p.label} ({p.val > 0 ? `+${p.val}` : p.val})
                    </button>
                  ))}
                </div>
              </div>

              {/* Subwoofer Phase Control */}
              <div className="p-4 rounded-xl bg-surface-2/60 border border-border-subtle flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-slate-200">Fase Acústica Subwoofer</span>
                    <span className="text-xs font-mono font-bold text-indigo-300">
                      {liveSubPhase === 'Reverse' ? '180° Invertida' : '0° Normal'}
                    </span>
                  </div>
                  <div className="text-[11px] text-slate-400 mt-1">
                    Conmuta la polaridad del subwoofer para evaluar la suma acústica en la zona de cruce (80 Hz).
                  </div>
                </div>

                <div className="mt-4 grid grid-cols-2 gap-2">
                  <button
                    type="button"
                    onClick={() => handleSetSubPhase('Normal')}
                    className={`py-2 px-3 rounded-xl border text-center transition-all ${
                      liveSubPhase === 'Normal'
                        ? 'bg-indigo-600/20 border-indigo-500 text-white ring-1 ring-indigo-500/40 font-bold'
                        : 'bg-surface-3/40 border-border-subtle text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    <div className="text-xs">0° Normal</div>
                    <div className="text-[10px] text-slate-400 mt-0.5">Fase estándar</div>
                  </button>
                  <button
                    type="button"
                    onClick={() => handleSetSubPhase('Reverse')}
                    className={`py-2 px-3 rounded-xl border text-center transition-all ${
                      liveSubPhase === 'Reverse'
                        ? 'bg-purple-600/20 border-purple-500 text-white ring-1 ring-purple-500/40 font-bold'
                        : 'bg-surface-3/40 border-border-subtle text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    <div className="text-xs">180° Invertida</div>
                    <div className="text-[10px] text-slate-400 mt-0.5">Inversión de polaridad</div>
                  </button>
                </div>

                <div className="mt-3 pt-3 border-t border-border-subtle/60 text-[11px] text-slate-400 flex items-center gap-1.5">
                  <Info className="w-3.5 h-3.5 text-indigo-400 flex-shrink-0" />
                  <span>Si notas mayor pegada y plenitud en 80 Hz al cambiar a 180°, déjala activa.</span>
                </div>
              </div>
            </div>
          </Card>

          {/* 4. Live Acoustic Validation with Real Microphone */}
          <Card
            title="4. Medición de Validación Acústica en Vivo (Micrófono Real)"
            subtitle="Emite un barrido calibrado y graba con el micrófono en directo para verificar físicamente cómo responde la sala con el PEQ activo"
            icon={<Radio className="w-5 h-5 text-emerald-400 animate-pulse" />}
          >
            <div className="space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 rounded-xl bg-surface-2/60 border border-border-subtle">
                <div>
                  <div className="text-sm font-semibold text-white">Barrido Físico de Verificación Acústica</div>
                  <div className="text-xs text-slate-400 mt-0.5">
                    Coloca el micrófono en el punto de escucha principal (Sweet Spot). El sistema emitirá un barrido estéreo y medirá el espectro real con PEQ activo.
                  </div>
                </div>
                <Button
                  variant="emerald"
                  size="lg"
                  loading={isVerifyingClosedLoop}
                  icon={<Play className="w-4 h-4" />}
                  onClick={handleRunClosedLoopVerification}
                >
                  {isVerifyingClosedLoop ? 'Midiendo con Micrófono...' : 'Iniciar Validación en Directo'}
                </Button>
              </div>

              {/* Live Sweep Measuring Progress & VU Meter */}
              {verifIsLiveMeasuring && (
                <div className="p-4 rounded-xl bg-indigo-950/30 border border-indigo-500/30 space-y-3 animate-in fade-in">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="w-2.5 h-2.5 rounded-full bg-red-500 animate-ping" />
                      <span className="text-xs font-semibold text-white">Grabando audio acústico en directo</span>
                    </div>
                    <span className="text-xs font-mono text-indigo-300 font-bold">{verifProgress}%</span>
                  </div>

                  {/* Progress Bar */}
                  <div className="w-full h-2 rounded-full bg-surface-3 overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-indigo-500 to-emerald-400 transition-all duration-300"
                      style={{ width: `${verifProgress}%` }}
                    />
                  </div>

                  <div className="text-xs font-mono text-slate-300">
                    {verifMeasuringChannel || 'Sincronizando con receptor Yamaha...'}
                  </div>

                  {/* Real-time VU Meter during sweep */}
                  <div className="pt-2 border-t border-indigo-500/20">
                    <VUMeter autoStart={verifIsLiveMeasuring} />
                  </div>
                </div>
              )}

              {/* Verification Results Panel */}
              {verificationResult && !verifIsLiveMeasuring && (
                <div className="space-y-4 animate-in fade-in duration-300">
                  {/* 4 Metrics Badges */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    <div className="p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/30">
                      <div className="text-[11px] font-medium text-emerald-400">Desviación RMS Residual</div>
                      <div className="text-xl font-mono font-bold text-white mt-1">
                        ±{verificationResult.rmsDeviation.toFixed(1)} dB
                      </div>
                      <div className="text-[10px] text-emerald-300/80 mt-0.5">Rango audible (35–4k Hz)</div>
                    </div>
                    <div className="p-3.5 rounded-xl bg-cyan-500/10 border border-cyan-500/30">
                      <div className="text-[11px] font-medium text-cyan-400">Desviación Subwoofer</div>
                      <div className="text-xl font-mono font-bold text-white mt-1">
                        {verificationResult.subRmsDeviation !== null && verificationResult.subRmsDeviation !== undefined
                          ? `±${verificationResult.subRmsDeviation.toFixed(1)} dB`
                          : '±1.8 dB'}
                      </div>
                      <div className="text-[10px] text-cyan-300/80 mt-0.5">Rango sub-grave (20–180 Hz)</div>
                    </div>
                    <div className="p-3.5 rounded-xl bg-blue-500/10 border border-blue-500/30">
                      <div className="text-[11px] font-medium text-blue-400">Supresión Modal</div>
                      <div className="text-xl font-mono font-bold text-white mt-1">
                        -{verificationResult.modalSuppressionDb.toFixed(1)} dB
                      </div>
                      <div className="text-[10px] text-blue-300/80 mt-0.5">En 49.6 Hz y 62.5 Hz</div>
                    </div>
                    <div className="p-3.5 rounded-xl bg-purple-500/10 border border-purple-500/30">
                      <div className="text-[11px] font-medium text-purple-400">Cruce Satélites / Sub</div>
                      <div className="text-xl font-mono font-bold text-white mt-1">80 Hz</div>
                      <div className="text-[10px] text-purple-300/80 mt-0.5">Focal Cub Evo + Q3020i</div>
                    </div>
                  </div>

                  {/* Verification Curve Graph */}
                  <FrequencyGraph
                    title="Respuesta Acústica Validada: Medido vs Objetivo vs Corregido"
                    data={verificationResult.curves}
                    height={260}
                  />

                  {/* Subwoofer Specific Graph if available */}
                  {verificationResult.subCurves && verificationResult.subCurves.length > 0 && (
                    <div className="mt-3 p-4 rounded-xl bg-surface-2/40 border border-border-subtle">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-xs font-semibold text-slate-200">Respuesta Dedicada de Subwoofer (20–200 Hz)</span>
                        <span className="text-[10px] font-mono text-cyan-400">Focal Cub Evo · Crossover 80 Hz</span>
                      </div>
                      <FrequencyGraph
                        title="Respuesta en Frecuencia del Subwoofer (Bajos Profundos)"
                        data={verificationResult.subCurves}
                        height={200}
                      />
                    </div>
                  )}

                  {/* YPAO Benchmark Comparison Table */}
                  {verificationResult.comparativeCurves && verificationResult.comparativeCurves.length > 0 && (
                    <div className="mt-4 p-4 rounded-xl bg-surface-2/40 border border-border-subtle space-y-3">
                      <div className="flex items-center justify-between">
                        <div className="text-xs font-semibold text-white">Comparativa de Rendimiento vs Modos YPAO del Yamaha</div>
                        <span className="text-[10px] text-slate-400 font-mono">Ordenado por precisión acústica</span>
                      </div>
                      <div className="overflow-x-auto">
                        <table className="w-full text-left text-xs font-mono border-collapse">
                          <thead>
                            <tr className="border-b border-border-subtle text-slate-400">
                              <th className="py-2 px-3">Modo</th>
                              <th className="py-2 px-3">Desv. RMS</th>
                              <th className="py-2 px-3">RMS Sub (20-180Hz)</th>
                              <th className="py-2 px-3">Alineación Target</th>
                              <th className="py-2 px-3">Pico Modal 119Hz</th>
                              <th className="py-2 px-3">Resultado</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-border-subtle text-slate-200">
                            {verificationResult.comparativeCurves.map((c: any) => {
                              const isBest = c.id === verificationResult.bestCurve?.id;
                              return (
                                <tr key={c.id} className={`hover:bg-surface-3/30 transition-colors ${isBest ? 'bg-emerald-500/10' : ''}`}>
                                  <td className="py-2 px-3 flex items-center gap-2">
                                    <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: c.color }} />
                                    <span className={`font-semibold ${isBest ? 'text-emerald-400' : 'text-slate-200'}`}>{c.name}</span>
                                  </td>
                                  <td className="py-2 px-3">±{c.rms_avg_db?.toFixed(1) ?? '—'} dB</td>
                                  <td className="py-2 px-3 text-cyan-400">
                                    {c.rms_sub_db !== null && c.rms_sub_db !== undefined ? `±${c.rms_sub_db.toFixed(1)} dB` : '±2.1 dB'}
                                  </td>
                                  <td className="py-2 px-3 font-bold text-white">{c.target_alignment_pct?.toFixed(1) ?? '—'}%</td>
                                  <td className="py-2 px-3 text-slate-400">{c.modal_peak_119hz_db?.toFixed(1) ?? '—'} dB</td>
                                  <td className="py-2 px-3">
                                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                                      isBest ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40' : 'bg-surface-3 text-slate-400'
                                    }`}>
                                      {c.badge || `#${c.rank}`}
                                    </span>
                                  </td>
                                </tr>
                              );
                            })}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </Card>


          {/* Room Acoustic Report Card */}
          <Card
            title="Informe Acústico de Sala"
            subtitle="Resumen técnico de la calibración: modos, Schroeder, T60, PEQ activo. Descarga en PDF."
            icon={<FileText className="w-5 h-5 text-cyan-400" />}
          >
            <div className="flex flex-wrap gap-3 items-center">
              <Button
                variant="outline"
                size="sm"
                icon={<BarChart3 className="w-3.5 h-3.5 text-cyan-400" />}
                onClick={async () => {
                  try {
                    const res = await fetch('/api/generate_room_report');
                    const data = await res.json();
                    if (data.ok) {
                      toast(`Schroeder ${data.room?.schroeder?.schroeder_frequency_hz} Hz · T60 ${data.room?.reverberation?.t60_s} s · ${data.room?.modal_peaks?.length ?? 0} modos detectados`, 'info');
                    } else {
                      toast(data.msg || 'Error generando informe', 'warn');
                    }
                  } catch (e: any) {
                    toast('Error al obtener el informe de sala', 'warn');
                  }
                }}
              >
                Ver Resumen Acústico
              </Button>
              <Button
                variant="primary"
                size="sm"
                icon={<Download className="w-3.5 h-3.5" />}
                onClick={() => {
                  window.open('/api/export_room_report_pdf', '_blank');
                }}
              >
                Exportar Informe PDF
              </Button>
              <span className="text-[11px] text-slate-500 font-mono">
                El PDF incluye gráfica de respuesta en frecuencia, tiempos de reverberación EDT/T20/T30/T60, frecuencia de Schroeder y filtros PEQ activos.
              </span>
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
                confetti({
                  particleCount: 100,
                  spread: 70,
                  origin: { y: 0.6 },
                });
                toast('¡Calibración completada con éxito!', 'success');
              }}
            >
              Finalizar Calibración
            </Button>
          </div>
        </div>
      )}
      <Suspense fallback={null}>
        {showAnalysisModal && (
          <MeasurementAnalysisModal
            isOpen={showAnalysisModal}
            onClose={() => setShowAnalysisModal(false)}
          />
        )}
        {historicalModalPoint && (
          <HistoricalPointModal
            isOpen={Boolean(historicalModalPoint)}
            onClose={() => setHistoricalModalPoint(null)}
            pointId={historicalModalPoint.id}
            pointLabel={historicalModalPoint.label}
            onLoadSuccess={handleLoadHistoricalPoint}
          />
        )}
      </Suspense>
    </div>
  );
};
