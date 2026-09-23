import React, { useState } from 'react';
import { Play, Square, Radio, Disc3, Volume2, Cast } from 'lucide-react';
import { musicCaster } from '../../services/musicCaster';
import { yamahaDirect } from '../../services/yamahaDirect';
import { useCalibration } from '../../context/CalibrationContext';

export const MusicStreamingHub: React.FC = () => {
  const { toast } = useCalibration();
  const [streamUrl, setStreamUrl] = useState('');
  const [customTitle, setCustomTitle] = useState('');
  const [isCasting, setIsCasting] = useState(false);

  // Emisoras de alta fidelidad preconfiguradas con streaming verificado
  const PRESET_STATIONS = [
    { name: 'Radio Paradise (320k MP3)', url: 'http://stream.radioparadise.com/mp3-320', genre: 'Eclectic Rock / Audiophile' },
    { name: 'Linn Jazz (320k MP3)', url: 'http://radio.linn.co.uk:8000/autodj', genre: 'Acoustic & Vocal Jazz' },
    { name: 'SomaFM Groove Salad (256k)', url: 'http://ice1.somafm.com/groovesalad-256-mp3', genre: 'Ambient / Chillout / Synth' },
    { name: 'KEXP Seattle Live', url: 'https://kexp-mp3-128.streamguys1.com/kexp128.mp3', genre: 'Indie / Live Studio' }
  ];
  const handleCastStream = async (url: string, title: string) => {
    setIsCasting(true);
    toast(`Conectando DLNA con Yamaha: ${title}...`, 'info');
    try {
      const ok = await musicCaster.castAudioStream(url, title);
      if (ok) {
        toast(`Reproduciendo ${title} en el receptor`, 'success');
      } else {
        toast('Error al iniciar flujo DLNA en el receptor', 'error');
      }
    } finally {
      setIsCasting(false);
    }
  };

  const handleStop = async () => {
    await musicCaster.stopPlayback();
    toast('Reproducción detenida', 'info');
  };

  return (
    <div className="space-y-6">
      {/* Banner Superior Hi-Fi Streaming */}
      <div className="relative overflow-hidden rounded-2xl border border-indigo-500/30 bg-gradient-to-br from-indigo-950/60 via-surface-1 to-surface-0 p-6 shadow-xl">
        <div className="relative z-10 flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
          <div className="space-y-2 max-w-xl">
            <div className="inline-flex items-center gap-2 rounded-full border border-indigo-500/40 bg-indigo-500/10 px-3 py-1 text-xs font-medium text-indigo-400">
              <Cast className="h-3.5 w-3.5" />
              <span>Streaming de Audio en Red (DLNA Hi-Fi)</span>
            </div>
            <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-white flex items-center gap-2">
              <span>Audio Streaming de Alta Fidelidad</span>
            </h2>
            <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">
              Transmite música y flujos de audio directamente al receptor <strong>Yamaha RX-V673</strong> en calidad digital nativa sin pérdidas, con la calibración acústica <strong>Harman Target</strong> (Q Acoustics 3020i + Focal Cub Evo) aplicada en tiempo real.
            </p>
          </div>
        </div>
      </div>

      {/* Grid de Secciones */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Emisoras de Alta Fidelidad DLNA */}
        <div className="rounded-2xl border border-border-subtle bg-surface-1 p-5 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Disc3 className="h-5 w-5 text-indigo-400 animate-spin-slow" />
              <h3 className="text-base font-semibold text-white">Emisoras Streaming DLNA (Sin Pérdida)</h3>
            </div>
            <button
              type="button"
              onClick={handleStop}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-rose-500/30 bg-rose-500/10 text-rose-400 hover:bg-rose-500/20 text-xs font-mono transition-colors"
            >
              <Square className="h-3.5 w-3.5 fill-rose-400" />
              <span>Detener</span>
            </button>
          </div>

          <div className="space-y-2.5">
            {PRESET_STATIONS.map((station) => (
              <div
                key={station.name}
                className="flex items-center justify-between p-3.5 rounded-xl border border-border-subtle bg-surface-2/60 hover:border-indigo-500/40 transition-all"
              >
                <div>
                  <div className="text-sm font-medium text-white">{station.name}</div>
                  <div className="text-xs text-slate-400 font-mono mt-0.5">{station.genre}</div>
                </div>
                <button
                  type="button"
                  disabled={isCasting}
                  onClick={() => handleCastStream(station.url, station.name)}
                  className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium shadow-md transition-all active:scale-95 disabled:opacity-50"
                >
                  <Play className="h-3.5 w-3.5 fill-white" />
                  <span>Enviar</span>
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Flujo Personalizado & Entradas AVR */}
        <div className="space-y-6">
          {/* Formulario URL personalizada */}
          <div className="rounded-2xl border border-border-subtle bg-surface-1 p-5 space-y-4">
            <div className="flex items-center gap-2">
              <Radio className="h-5 w-5 text-amber-400" />
              <h3 className="text-base font-semibold text-white">Transmitir URL de Audio / Podcast</h3>
            </div>
            <div className="space-y-3">
              <div>
                <label className="text-xs font-mono text-slate-400 block mb-1">Título del Flujo</label>
                <input
                  type="text"
                  placeholder="Ej. Mi Podcast Favorito"
                  value={customTitle}
                  onChange={(e) => setCustomTitle(e.target.value)}
                  className="w-full bg-surface-2 border border-border-subtle rounded-xl px-3.5 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                />
              </div>
              <div>
                <label className="text-xs font-mono text-slate-400 block mb-1">URL de Flujo de Audio (HTTP FLAC / MP3 / AAC)</label>
                <input
                  type="text"
                  placeholder="http://servidor-audio:8000/stream.flac"
                  value={streamUrl}
                  onChange={(e) => setStreamUrl(e.target.value)}
                  className="w-full bg-surface-2 border border-border-subtle rounded-xl px-3.5 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                />
              </div>
              <button
                type="button"
                disabled={!streamUrl || isCasting}
                onClick={() => handleCastStream(streamUrl, customTitle || 'Flujo de Audio')}
                className="w-full py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white text-xs font-semibold shadow-md transition-all"
              >
                Transmitir Audio al Yamaha RX-V673
              </button>
            </div>
          </div>

          {/* Conmutador de Entradas Yamaha para Música */}
          <div className="rounded-2xl border border-border-subtle bg-surface-1 p-5 space-y-3">
            <div className="flex items-center gap-2">
              <Volume2 className="h-5 w-5 text-sky-400" />
              <h3 className="text-base font-semibold text-white">Entradas Rápidas de Audio</h3>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              {[
                { label: 'TV Audio (HDMI eARC)', input: 'AV4' },
                { label: 'DLNA Server', input: 'SERVER' },
                { label: 'Net Radio', input: 'NET_RADIO' },
                { label: 'Entrada Frontal', input: 'V-AUX' }
              ].map((item) => (
                <button
                  key={item.input}
                  type="button"
                  onClick={async () => {
                    await yamahaDirect.setInput(item.input);
                    toast(`Entrada conmutada a ${item.label}`, 'info');
                  }}
                  className="p-2.5 rounded-xl border border-border-subtle bg-surface-2/80 hover:border-sky-500/50 hover:bg-surface-2 text-xs font-mono text-slate-200 text-center transition-all"
                >
                  {item.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
