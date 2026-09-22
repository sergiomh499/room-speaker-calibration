import React, { createContext, useContext, useState, useEffect, ReactNode, useCallback } from 'react';
import { get, set } from 'idb-keyval';
import { AVRStatus, Topology, TargetProfile, MeasurementPoint, SubwooferConfig } from '../types';
import { api } from '../services/api';
export type AppView = 'home' | 'calibrate' | 'history' | 'settings';

interface CalibrationContextType {
  view: AppView;
  setView: (v: AppView) => void;
  topology: Topology;
  setTopology: (t: Topology) => void;
  wizardStep: number;
  setWizardStep: (s: number) => void;
  totalSteps: number;
  avrStatus: AVRStatus;
  refreshStatus: () => Promise<void>;
  points: MeasurementPoint[];
  setPoints: React.Dispatch<React.SetStateAction<MeasurementPoint[]>>;
  profiles: TargetProfile[];
  activeProfileId: string;
  setActiveProfileId: (id: string) => void;
  subwooferConfig: SubwooferConfig;
  setSubwooferConfig: React.Dispatch<React.SetStateAction<SubwooferConfig>>;
  toast: (message: string, type?: 'info' | 'success' | 'warn' | 'error') => void;
  toasts: Array<{ id: string; message: string; type: string }>;
}

const defaultAVR: AVRStatus = {
  ok: true,
  avr_power: 'On',
  avr_input: 'AV4',
  avr_volume_db: -25.0,
  avr_peq_mode: 'Manual PEQ',
  avr_drc: 'Off',
  points_measured: 5,
  points_total: 5,
  calibration_ready: true,
  online: true,
};

const initialPoints: MeasurementPoint[] = [
  { id: 1, label: 'Punto 1', sublabel: 'Sweet Spot Central', measured: true, active: true },
  { id: 2, label: 'Punto 2', sublabel: 'Oído Izquierdo (+40cm)', measured: true },
  { id: 3, label: 'Punto 3', sublabel: 'Oído Derecho (+40cm)', measured: true },
  { id: 4, label: 'Punto 4', sublabel: 'Frente (+30cm)', measured: true },
  { id: 5, label: 'Punto 5', sublabel: 'Detrás (+30cm)', measured: true },
];

const CalibrationContext = createContext<CalibrationContextType | null>(null);

export const CalibrationProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [view, setView] = useState<AppView>('home');
  const [topology, setTopology] = useState<Topology>('2.1');
  const [wizardStep, setWizardStep] = useState<number>(1);
  const [avrStatus, setAvrStatus] = useState<AVRStatus>(defaultAVR);
  const [points, setPoints] = useState<MeasurementPoint[]>(initialPoints);
  const [profiles, setProfiles] = useState<TargetProfile[]>([]);
  const [activeProfileId, setActiveProfileId] = useState<string>('harman_wide_room');
  const [subwooferConfig, setSubwooferConfig] = useState<SubwooferConfig>({
    crossover_hz: 80,
    phase_degrees: 0,
    trim_db: 0,
    peq_bands: [
      { band: 1, freq_hz: 78.7, q: 5.04, gain_db: -3.5, type: 'PEQ Notch' },
      { band: 2, freq_hz: 45.2, q: 3.20, gain_db: -2.0, type: 'PEQ Notch' },
    ],
  });
  const [toasts, setToasts] = useState<Array<{ id: string; message: string; type: string }>>([]);

  // Dynamic step count: 4 steps for 2.0 (skipping Subwoofer), 5 steps for 2.1
  const totalSteps = topology === '2.0' ? 4 : 5;

  const toast = useCallback((message: string, type: 'info' | 'success' | 'warn' | 'error' = 'info') => {
    const id = Math.random().toString(36).substring(2, 9);
    setToasts(prev => [...prev, { id, message, type }]);
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id));
    }, 4000);
  }, []);

  const refreshStatus = useCallback(async () => {
    const st = await api.getStatus();
    setAvrStatus(st);
  }, []);

  // Poll status periodically
  useEffect(() => {
    refreshStatus();
    const interval = setInterval(refreshStatus, 4000);
    return () => clearInterval(interval);
  }, [refreshStatus]);

  // Load profiles on mount
  useEffect(() => {
    api.getTargets().then(data => {
      if (data && data.length > 0) {
        setProfiles(data);
      }
    }).catch(err => {
      console.error('Error loading target profiles:', err);
    });
  }, []);
  // Load physical measurement points on mount
  useEffect(() => {
    api.getMeasurementAnalysis().then(data => {
      if (data && data.points && data.points.length > 0) {
        const loadedPoints: MeasurementPoint[] = data.points.map((p: any) => ({
          id: p.point_id,
          label: p.name,
          sublabel: p.sublabel,
          measured: p.measured,
          channels: p.channels,
          active: p.point_id === 1,
        }));
        setPoints(loadedPoints);
      }
    }).catch(err => {
      console.error('Error loading measurement points analysis:', err);
    });
  }, []);
  // Restore saved state from IndexedDB
  useEffect(() => {
    get<Topology>('calibration_topology').then(saved => {
      if (saved) setTopology(saved);
    }).catch(() => {});
    get<string>('calibration_active_profile').then(saved => {
      if (saved) setActiveProfileId(saved);
    }).catch(() => {});
  }, []);

  // Persist state to IndexedDB
  useEffect(() => {
    set('calibration_topology', topology).catch(() => {});
  }, [topology]);

  useEffect(() => {
    set('calibration_active_profile', activeProfileId).catch(() => {});
  }, [activeProfileId]);


  return (
    <CalibrationContext.Provider
      value={{
        view,
        setView,
        topology,
        setTopology,
        wizardStep,
        setWizardStep,
        totalSteps,
        avrStatus,
        refreshStatus,
        points,
        setPoints,
        profiles,
        activeProfileId,
        setActiveProfileId,
        subwooferConfig,
        setSubwooferConfig,
        toast,
        toasts,
      }}
    >
      {children}
    </CalibrationContext.Provider>
  );
};

export const useCalibration = (): CalibrationContextType => {
  const ctx = useContext(CalibrationContext);
  if (!ctx) {
    throw new Error('useCalibration must be used within a CalibrationProvider');
  }
  return ctx;
};
