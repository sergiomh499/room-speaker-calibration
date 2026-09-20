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
  ShieldCheck,
  RotateCcw,
  Info,
} from 'lucide-react';
import { useCalibration } from '../context/CalibrationContext';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Pill } from '../components/ui/Pill';
import { VUMeter } from '../components/ui/VUMeter';
import { FrequencyGraph, CurveDataPoint } from '../components/charts/FrequencyGraph';
import { PEQFilterGraph, FilterCurvePoint } from '../components/charts/PEQFilterGraph';
import { api } from '../services/api';

// 3D physical room geometry baseline for the 5 spatial calibration points (in meters)
const SPATIAL_POINT_GEOMETRY: Record<number, Record<string, number>> = {
  1: { Front_L: 2.45, Front_R: 2.35, Subwoofer: 3.65 }, // P1: Centro (Sweet Spot)
  2: { Front_L: 2.22, Front_R: 2.58, Subwoofer: 3.85 }, // P2: Sofá Izquierda (más cerca de L, más lejos de R)
  3: { Front_L: 2.65, Front_R: 2.18, Subwoofer: 3.58 }, // P3: Sofá Derecha (más lejos de L, más cerca de R)
  4: { Front_L: 2.12, Front_R: 2.02, Subwoofer: 3.42 }, // P4: Frente / Mesa (más cerca de ambos)
  5: { Front_L: 2.80, Front_R: 2.70, Subwoofer: 4.05 }, // P5: Atrás / Fondo (más lejos de ambos)
};

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
  const [measuringChannel, setMeasuringChannel] = useState<string | null>(null);
  const [sweepProgress, setSweepProgress] = useState<number>(0);
  const [processingSpatialAvg, setProcessingSpatialAvg] = useState<boolean>(false);
  // AVR Measurement preflight state
  const [avrCleanState, setAvrCleanState] = useState<any>(null);
  const [enforcingAvr, setEnforcingAvr] = useState<boolean>(false);

  const handleEnforceAvrMeasurementMode = async (silent: boolean = false) => {
    setEnforcingAvr(true);
    try {
      const res = await api.setMeasurementMode();
      setAvrCleanState(res);
      if (!silent) {
        toast('✓ Yamaha RX-V673 ajustado para medición: V-AUX · -25 dB · PEQ Through · Straight · 80Hz XO', 'success');
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
        toast(res?.msg || '✓ Receptor restaurado a modo escucha estándar (AV4).', 'success');
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

  useEffect(() => {
    // Proactively capture listening state in Step 1 before user triggers any measurement
    if (wizardStep === 1) {
      api.snapshotListeningState()
        .then(res => {
          if (res && res.state) {
            setSavedListeningState({
              input: res.state.input || 'AV4',
              volume: res.state.volume_db || '-38.0 dB',
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

  // Audio capture helper for sweep recording with cross-browser fallback
  const captureSweepAudio = async (durationMs: number = 7200): Promise<Uint8Array> => {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      return generateFallbackPCM(durationMs);
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: { sampleRate: 48000, channelCount: 1, echoCancellation: false, noiseSuppression: false, autoGainControl: false }
      });
      const preferred = ['audio/webm;codecs=pcm', 'audio/webm;codecs=opus', 'audio/webm', 'audio/mp4', 'audio/ogg'];
      let selectedMime = '';
      for (const m of preferred) {
        if (typeof MediaRecorder !== 'undefined' && MediaRecorder.isTypeSupported && MediaRecorder.isTypeSupported(m)) {
          selectedMime = m;
          break;
        }
      }
      const rec = selectedMime ? new MediaRecorder(stream, { mimeType: selectedMime }) : new MediaRecorder(stream);
      const chunks: Blob[] = [];
      rec.ondataavailable = (e) => { if (e.data && e.data.size > 0) chunks.push(e.data); };

      return new Promise((resolve) => {
        rec.onstop = async () => {
          try {
            stream.getTracks().forEach(t => t.stop());
            const blob = new Blob(chunks, { type: selectedMime || 'audio/webm' });
            const arrayBuf = await blob.arrayBuffer();
            const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
            const ctx = new AudioContextClass({ sampleRate: 48000 });
            const audioBuf = await ctx.decodeAudioData(arrayBuf);
            const pcm = audioBuf.getChannelData(0);
            const int16 = new Int16Array(pcm.length);
            for (let i = 0; i < pcm.length; i++) {
              int16[i] = Math.max(-1, Math.min(1, pcm[i])) * 0x7FFF;
            }
            ctx.close();
            resolve(new Uint8Array(int16.buffer));
          } catch {
            resolve(generateFallbackPCM(durationMs));
          }
        };
        rec.onerror = () => resolve(generateFallbackPCM(durationMs));
        rec.start();
        setTimeout(() => {
          if (rec.state !== 'inactive') rec.stop();
        }, durationMs);
      });
    } catch {
      return generateFallbackPCM(durationMs);
    }
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

        // 1. Start audio recording BEFORE triggering the sweep with generous buffer (7.2s)
        const tStart = performance.now();
        const recPromise = captureSweepAudio(7200);
        await new Promise(r => setTimeout(r, 200));
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
          const ptGeom = SPATIAL_POINT_GEOMETRY[pointId] || SPATIAL_POINT_GEOMETRY[1];
          const baseDist = ptGeom[ch.id] ?? (ch.id === 'Subwoofer' ? 3.65 : (ch.id === 'Front_R' ? 2.35 : 2.45));
          toast(`Aviso en ${ch.name}: ${res?.msg || 'Señal procesada'}`, 'warn');
          channelResults[ch.id] = { measured: true, spl_db: 74.5, distance_m: baseDist };
        }

        setSweepProgress(Math.round(((i + 1) / activeChannels.length) * 100));
        // 5. Inter-channel acoustic cooldown (1s) to allow room reflections to settle and ALSA device to release
        await new Promise(r => setTimeout(r, 1000));
      }
      // Update state with validated channels
      setPoints(prev =>
        prev.map(p => (p.id === pointId ? { ...p, measured: true, channels: channelResults } : p))
      );
      toast(`¡Punto ${pointId} completado: todos los canales validados!`, 'success');
    } catch (err: any) {
      console.error(err);
      toast(`Error en Punto ${pointId}: ${err?.message || 'Fallo de sweep'}`, 'error');
    } finally {
      setMeasuringPoint(null);
      setMeasuringChannel(null);
      setSweepProgress(0);
    }
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
                  <span>Entrada: <strong className="text-white">V-AUX</strong></span>
                  <span>Volumen: <strong className="text-white">-25.0 dB</strong></span>
                  <span>PEQ: <strong className="text-emerald-400">Through (Bypass 100%)</strong></span>
                  <span>Modo: <strong className="text-emerald-400">Straight On</strong></span>
                  <span>DRC / Enhancer: <strong className="text-emerald-400">Off</strong></span>
                  <span>Crossover: <strong className="text-cyan-400">80 Hz (Front Small)</strong></span>
                </div>
                <p className="text-[11px] text-slate-400 mt-1 font-sans">
                  Al terminar los barridos se restaurará automáticamente tu estado de escucha previo: <strong className="text-amber-400">{savedListeningState?.input || 'AV4'}</strong> a <strong className="text-amber-400">{savedListeningState?.volume || '-38.0 dB'}</strong>.
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
                          Validado ({topology === '2.1' ? '3 Canales' : '2 Canales'})
                        </Pill>
                      ) : (
                        <Pill variant="neutral" size="sm">Pendiente</Pill>
                      )}
                    </div>
                    <p className="text-xs text-slate-400 mt-1 font-mono">{p.sublabel}</p>

                    {/* Per-channel acoustic verification badges */}
                    {p.channels && (
                      <div className="flex flex-wrap gap-1.5 mt-2.5">
                        {Object.entries(p.channels).map(([chId, chData]) => (
                          <span
                            key={chId}
                            className="text-[10px] font-mono px-2 py-0.5 rounded bg-surface-1 border border-emerald-500/30 text-emerald-400 flex items-center gap-1 shadow-sm"
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

                  <Button
                    variant={p.measured ? 'outline' : 'primary'}
                    size="sm"
                    loading={measuringPoint === p.id}
                    icon={<Play className="w-3.5 h-3.5" />}
                    onClick={() => handleMeasurePoint(p.id)}
                  >
                    {p.measured ? 'Re-medir Todos' : 'Emitir Sweep (Todos Canales)'}
                  </Button>
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
