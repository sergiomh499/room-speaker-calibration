import React, { useState, useEffect } from 'react';
import { X, History, Clock, RotateCcw } from 'lucide-react';
import { Button } from './ui/Button';
import { Pill } from './ui/Pill';
import { api } from '../services/api';

interface PointHistoryItem {
  id: string;
  filename: string;
  timestamp: string;
  has_sub?: boolean;
  spl_l?: number;
  spl_r?: number;
  spl_sub?: number;
  source?: string;
}

interface HistoricalPointModalProps {
  isOpen: boolean;
  onClose: () => void;
  pointId: number;
  pointLabel: string;
  onLoadSuccess: (pointId: number, channels: any) => void;
}

export const HistoricalPointModal: React.FC<HistoricalPointModalProps> = ({
  isOpen,
  onClose,
  pointId,
  pointLabel,
  onLoadSuccess,
}) => {
  const [historyItems, setHistoryItems] = useState<PointHistoryItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [loadingId, setLoadingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isOpen) return;
    setLoading(true);
    setError(null);
    api.getPointHistory(pointId)
      .then(res => {
        if (res && res.history) {
          setHistoryItems(res.history);
        } else {
          setHistoryItems([]);
        }
      })
      .catch(err => {
        setError(err?.message || 'Error al obtener historial del punto');
      })
      .finally(() => {
        setLoading(false);
      });
  }, [isOpen, pointId]);

  const handleSelectHistory = async (item: PointHistoryItem) => {
    setLoadingId(item.id);
    try {
      const res = await api.loadPointHistory(pointId, item.id);
      if (res && res.ok) {
        onLoadSuccess(pointId, res.channels);
        onClose();
      } else {
        alert(res?.msg || 'Error al cargar medición');
      }
    } catch (err: any) {
      alert(err?.message || 'Error al cargar medición');
    } finally {
      setLoadingId(null);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-3 sm:p-4 bg-black/80 backdrop-blur-md animate-fade-in">
      <div className="relative w-full max-w-2xl max-h-[88vh] flex flex-col bg-surface-1 border border-border-strong rounded-2xl shadow-2xl overflow-hidden text-slate-200">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-border-subtle bg-surface-0/60">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-indigo-500/10 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
              <History className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-semibold text-white tracking-tight">
                Cargar Medición Histórica — Punto {pointId}
              </h3>
              <p className="text-xs text-slate-400 font-mono">
                {pointLabel} · Recupera capturas previas sin repetir barridos
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-surface-2 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-5 space-y-3">
          {loading ? (
            <div className="py-12 flex flex-col items-center justify-center gap-3 text-slate-400">
              <div className="w-7 h-7 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
              <span className="text-xs font-mono">Buscando mediciones previas para Punto {pointId}...</span>
            </div>
          ) : error ? (
            <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs">
              {error}
            </div>
          ) : historyItems.length === 0 ? (
            <div className="py-12 text-center text-slate-500 text-xs font-mono">
              No se encontraron mediciones históricas guardadas para el Punto {pointId}.
            </div>
          ) : (
            <div className="space-y-2.5">
              <div className="text-[11px] font-mono text-slate-400 px-1 flex justify-between">
                <span>{historyItems.length} capturas encontradas</span>
                <span>Orden: Más reciente primero</span>
              </div>
              {historyItems.map(item => (
                <div
                  key={item.id}
                  className="p-3.5 rounded-xl border border-border-subtle bg-surface-2/40 hover:bg-surface-2 hover:border-indigo-500/40 transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-3"
                >
                  <div className="space-y-1.5">
                    <div className="flex items-center gap-2 flex-wrap">
                      <div className="flex items-center gap-1.5 text-xs font-semibold text-white font-mono">
                        <Clock className="w-3.5 h-3.5 text-indigo-400" />
                        <span>{item.timestamp}</span>
                      </div>
                      <Pill variant="neutral" size="sm">
                        {item.source || 'Backup'}
                      </Pill>
                      {item.has_sub && (
                        <Pill variant="emerald" size="sm">
                          2.1 Focal Cub Evo
                        </Pill>
                      )}
                    </div>

                    {/* Acoustic metrics */}
                    <div className="flex items-center gap-3 text-xs font-mono text-slate-400">
                      {item.spl_l !== null && item.spl_l !== undefined && (
                        <span>L: <strong className="text-slate-200">{item.spl_l} dB</strong></span>
                      )}
                      {item.spl_r !== null && item.spl_r !== undefined && (
                        <span>R: <strong className="text-slate-200">{item.spl_r} dB</strong></span>
                      )}
                      {item.spl_sub !== null && item.spl_sub !== undefined && (
                        <span>SUB: <strong className="text-emerald-300">{item.spl_sub} dB</strong></span>
                      )}
                    </div>
                  </div>

                  <Button
                    variant="outline"
                    size="sm"
                    loading={loadingId === item.id}
                    icon={<RotateCcw className="w-3.5 h-3.5 text-indigo-400" />}
                    onClick={() => handleSelectHistory(item)}
                  >
                    Cargar en Punto {pointId}
                  </Button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-5 py-3 border-t border-border-subtle bg-surface-0/40 flex justify-between items-center text-xs font-mono text-slate-500">
          <span>Al cargar, se actualizan las distancias y niveles SPL del punto seleccionado.</span>
          <Button variant="ghost" size="sm" onClick={onClose}>
            Cerrar
          </Button>
        </div>
      </div>
    </div>
  );
};
