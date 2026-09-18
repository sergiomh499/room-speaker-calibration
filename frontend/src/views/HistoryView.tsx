import React, { useState, useEffect } from 'react';
import { History, RotateCcw, FileText, Calendar } from 'lucide-react';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Pill } from '../components/ui/Pill';
import { api } from '../services/api';
import { useCalibration } from '../context/CalibrationContext';

interface SessionItem {
  id: string;
  name: string;
  date: string;
  profile: string;
  points_count: number;
}

export const HistoryView: React.FC = () => {
  const { toast } = useCalibration();
  const [sessions, setSessions] = useState<SessionItem[]>([]);
  const [restoringId, setRestoringId] = useState<string | null>(null);

  const fallbackSessions: SessionItem[] = [
    {
      id: 'session_20260918_1700',
      name: 'Calibración 2.1 Focal Cub Evo + Harman',
      date: '18 Sep 2026, 17:00',
      profile: 'harman_2_1',
      points_count: 5,
    },
    {
      id: 'session_20260917_2030',
      name: 'Sesión Estéreo Floyd Toole Studio',
      date: '17 Sep 2026, 20:30',
      profile: 'floyd_toole_inroom',
      points_count: 5,
    },
  ];

  useEffect(() => {
    let active = true;
    api.getHistory()
      .then(res => {
        if (!active) return;
        if (res && res.sessions && res.sessions.length > 0) {
          setSessions(res.sessions);
        } else {
          setSessions(fallbackSessions);
        }
      })
      .catch(() => {
        if (active) setSessions(fallbackSessions);
      });

    return () => { active = false; };
  }, []);

  const handleRestore = async (id: string) => {
    setRestoringId(id);
    try {
      await api.restoreSession(id);
      toast(`Sesión '${id}' restaurada en el receptor AV y estado local.`, 'success');
    } catch {
      toast(`No se pudo restaurar la sesión '${id}'.`, 'error');
    } finally {
      setRestoringId(null);
    }
  };

  return (
    <div className="space-y-6 pb-20 md:pb-8">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-white tracking-tight">Historial de Calibraciones</h2>
          <p className="text-sm text-slate-400 mt-1 font-mono">
            Registros acústicos guardados y copias de seguridad de NVRAM en disco.
          </p>
        </div>

        <Button
          variant="outline"
          icon={<FileText className="w-4 h-4" />}
          onClick={() => window.open('/api/download_pdf', '_blank')}
        >
          Exportar Informe Acústico (PDF)
        </Button>
      </div>

      <Card
        title="Sesiones Acústicas en Disco"
        subtitle="Restaura cualquier medición previa de forma instantánea"
        icon={<History className="w-5 h-5 text-indigo-400" />}
      >
        <div className="divide-y divide-border-subtle">
          {sessions.map(s => (
            <div
              key={s.id}
              className="py-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4 hover:bg-surface-2/30 px-2 rounded-xl transition-colors"
            >
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-semibold text-white">{s.name}</span>
                  <Pill variant="indigo" size="sm">{s.profile}</Pill>
                </div>
                <div className="flex items-center gap-3 text-xs text-slate-400 font-mono">
                  <span className="flex items-center gap-1">
                    <Calendar className="w-3 h-3 text-slate-500" />
                    {s.date}
                  </span>
                  <span>•</span>
                  <span>{s.points_count} posiciones medidas</span>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  loading={restoringId === s.id}
                  icon={<RotateCcw className="w-3.5 h-3.5" />}
                  onClick={() => handleRestore(s.id)}
                >
                  Restaurar
                </Button>
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
};
