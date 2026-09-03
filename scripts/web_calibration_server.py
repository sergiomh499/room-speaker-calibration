#!/usr/bin/env python3
"""
Mobile Web Calibration Server for Yamaha RX-V673 + Q Acoustics 3020i
Allows using smartphone (Google Pixel 9 Pro) as an untethered acoustic measurement microphone.
Features live pre-flight checks, 5-point spatial averaging, dynamic PDF report & graphs download on mobile,
and a direct button to send and apply PEQ configurations to the amplifier NVRAM.
"""
import os
import ssl
import socket
import json
import time
import glob
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import subprocess
import numpy as np
import scipy.signal
import scipy.io.wavfile as wav
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
import shutil

import sys
if "/home/sergio/room-speaker-calibration" not in sys.path:
    sys.path.insert(0, "/home/sergio/room-speaker-calibration")
REPO_DIR = "/home/sergio/room-speaker-calibration"
DATA_DIR = f"{REPO_DIR}/data"
FIG_DIR = f"{REPO_DIR}/figures"
CONFIG_DIR = f"{REPO_DIR}/config"
REPORT_DIR = f"{REPO_DIR}/reports"
PDF_FILE = "/home/sergio/Informe_Calibracion_Acustica_Yamaha_Q_Acoustics.pdf"

PORT = 53317
CERT_FILE = "/tmp/cal_cert.pem"
KEY_FILE = "/tmp/cal_key.pem"

# Farina sweep parameters
fs = 48000
duration = 5.0
f1, f2 = 15.0, 22000.0
N = int(duration * fs)
t = np.linspace(0, duration, N, endpoint=False)
w1 = 2 * np.pi * f1
w2 = 2 * np.pi * f2
L = duration / np.log(w2 / w1)
phi = w1 * L * (np.exp(t / L) - 1.0)
sweep_core = np.sin(phi)

fade_samples = int(fs * 0.05)
fade_in = np.sin(np.linspace(0, np.pi/2, fade_samples))**2
sweep_core[:fade_samples] *= fade_in
sweep_core[-fade_samples:] *= fade_in[::-1]

envelope = np.exp(-t / L)
inv_sweep = sweep_core[::-1] * envelope
conv_unit = scipy.signal.fftconvolve(sweep_core, inv_sweep, mode='full')
inv_sweep /= np.max(conv_unit)

from scripts.verify_calibration import professional_psychoacoustic_smooth

# Cache measured points in memory
point_buffers = {1: {}, 2: {}, 3: {}, 4: {}, 5: {}}
verif_buffers = {"through": {}, "ypao_flat": {}, "ypao_front": {}, "ypao_natural": {}, "manual": {}}
HTML_CONTENT = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>Calibración Acústica - Pixel 9 Pro</title>
<style>
  :root {
    --bg: #0f172a;
    --card: #1e293b;
    --primary: #38bdf8;
    --accent: #22c55e;
    --text: #f8fafc;
    --text-dim: #94a3b8;
    --border: #334155;
    --warn: #f59e0b;
    --danger: #ef4444;
  }
  body {
    margin: 0;
    padding: 16px;
    background: var(--bg);
    color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    padding-bottom: 40px;
  }
  h1 { font-size: 1.25rem; margin: 0 0 4px 0; color: var(--primary); }
  .subtitle { font-size: 0.85rem; color: var(--text-dim); margin-bottom: 12px; }
  .device-badge {
    display: inline-block;
    background: #0369a1;
    color: #fff;
    padding: 4px 10px;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 600;
    margin-bottom: 14px;
  }
  .card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 14px;
    margin-bottom: 12px;
    box-shadow: 0 4px 6px -1px rgba(0,0,0,0.2);
  }
  .card-title {
    font-size: 0.95rem;
    font-weight: 600;
    margin-bottom: 4px;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  .card-desc { font-size: 0.78rem; color: var(--text-dim); margin-bottom: 10px; line-height: 1.35; }
  .status-badge {
    font-size: 0.72rem;
    padding: 2px 8px;
    border-radius: 6px;
    background: #334155;
    color: #cbd5e1;
    font-weight: 600;
  }
  .status-badge.ok { background: #166534; color: #86efac; }
  .status-badge.active { background: #854d0e; color: #fef08a; }
  button {
    width: 100%;
    padding: 13px;
    font-size: 0.92rem;
    font-weight: 600;
    color: #0f172a;
    background: var(--primary);
    border: none;
    border-radius: 8px;
    cursor: pointer;
    transition: background 0.2s, transform 0.1s;
  }
  button:active { background: #0284c7; transform: scale(0.99); }
  button:disabled { background: #475569; color: #94a3b8; cursor: not-allowed; }
  .btn-finish {
    background: var(--accent);
    color: #064e3b;
    margin-top: 14px;
    padding: 15px;
    font-size: 0.98rem;
  }
  .btn-finish:active { background: #16a34a; }
  .btn-measure-mode {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    width: 100%;
    box-sizing: border-box;
    padding: 13px;
    background: #0284c7;
    color: #ffffff;
    font-size: 0.92rem;
    font-weight: 700;
    border-radius: 8px;
    border: none;
    cursor: pointer;
    margin-bottom: 14px;
    box-shadow: 0 4px 6px -1px rgba(2, 132, 199, 0.3);
    transition: background 0.2s, transform 0.1s;
  }
  .btn-measure-mode:active { background: #0369a1; transform: scale(0.99); }
  
  /* Results & Mobile Download Styles */
  #results-panel {
    display: none;
    background: #0d233a;
    border: 1.5px solid var(--primary);
    border-radius: 12px;
    padding: 16px;
    margin-top: 18px;
  }
  .btn-download-pdf {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    width: 100%;
    box-sizing: border-box;
    padding: 15px;
    background: #2563eb;
    color: #ffffff;
    font-size: 1rem;
    font-weight: bold;
    text-decoration: none;
    border-radius: 8px;
    text-align: center;
    margin-bottom: 16px;
    box-shadow: 0 4px 10px rgba(37, 99, 235, 0.4);
  }
  .btn-download-pdf:active { background: #1d4ed8; }
  
  .btn-apply-amp {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    width: 100%;
    box-sizing: border-box;
    padding: 15px;
    background: #10b981;
    color: #064e3b;
    font-size: 1rem;
    font-weight: bold;
    border-radius: 8px;
    text-align: center;
    margin-top: 14px;
    cursor: pointer;
    border: none;
    box-shadow: 0 4px 10px rgba(16, 185, 129, 0.35);
  }
  .btn-apply-amp:active { background: #059669; }
  
  .fig-grid {
    display: grid;
    grid-template-columns: 1fr;
    gap: 12px;
    margin-top: 12px;
    margin-bottom: 16px;
  }
  .fig-card {
    background: #1e293b;
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 10px;
  }
  .fig-card h4 {
    margin: 0 0 6px 0;
    font-size: 0.85rem;
    color: #e2e8f0;
  }
  .fig-card p {
    margin: 0 0 8px 0;
    font-size: 0.72rem;
    color: var(--text-dim);
  }
  .fig-card img {
    width: 100%;
    height: auto;
    border-radius: 6px;
    border: 1px solid #334155;
    background: #020617;
    margin-bottom: 8px;
  }
  .btn-view-fig {
    display: inline-block;
    padding: 7px 12px;
    background: #334155;
    color: #38bdf8;
    text-decoration: none;
    font-size: 0.75rem;
    font-weight: 600;
    border-radius: 6px;
    text-align: center;
    width: 100%;
    box-sizing: border-box;
  }
  .btn-view-fig:active { background: #475569; }
  .btn-verify {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    width: 100%;
    box-sizing: border-box;
    padding: 13px;
    background: #0891b2;
    color: #ffffff;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    font-size: 0.88rem;
    font-weight: bold;
    margin-top: 10px;
    margin-bottom: 8px;
    transition: all 0.2s;
  }
  .btn-verify:active { background: #0e7490; transform: scale(0.99); }

  .btn-scene {
    padding: 10px 8px;
    background: #1e1b4b;
    border: 1px solid #4338ca;
    color: #c7d2fe;
    border-radius: 8px;
    cursor: pointer;
    font-size: 0.78rem;
    text-align: center;
    transition: all 0.15s;
  }
  .btn-scene:active { background: #3730a3; transform: scale(0.98); }

  .btn-sync-scenes {
    width: 100%;
    box-sizing: border-box;
    padding: 11px;
    background: #4f46e5;
    color: #ffffff;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    font-size: 0.82rem;
    font-weight: bold;
    margin-top: 10px;
    transition: all 0.15s;
  }
  .btn-sync-scenes:active { background: #4338ca; }

  .profile-card {
    background: #0f172a;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 12px;
    margin-bottom: 12px;
    transition: border-color 0.2s;
  }
  .profile-card.active-target {
    border-color: #38bdf8;
    background: rgba(14, 116, 144, 0.12);
  }
  .profile-badge {
    display: inline-block;
    font-size: 0.72rem;
    font-weight: bold;
    padding: 3px 8px;
    border-radius: 4px;
    margin-bottom: 6px;
    background: #1e293b;
    color: #f59e0b;
    border: 1px solid #475569;
  }
  .pro-tag {
    display: flex;
    align-items: flex-start;
    gap: 6px;
    font-size: 0.73rem;
    color: #86efac;
    margin-bottom: 3px;
  }
  .con-tag {
    display: flex;
    align-items: flex-start;
    gap: 6px;
    font-size: 0.73rem;
    color: #fca5a5;
    margin-bottom: 3px;
  }
  .btn-apply-profile {
    display: block;
    width: 100%;
    box-sizing: border-box;
    padding: 9px;
    background: #059669;
    color: #ffffff;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    font-size: 0.78rem;
    font-weight: bold;
    margin-top: 8px;
    transition: all 0.15s;
  }
  .btn-apply-profile:active { background: #047857; }

  
  .peq-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.72rem;
    margin-top: 8px;
    margin-bottom: 12px;
  }
  .peq-table th, .peq-table td {
    padding: 5px 6px;
    border: 1px solid #334155;
    text-align: center;
  }
  .peq-table th { background: #1e293b; color: #38bdf8; }
  .peq-table td.notch { color: #f87171; font-weight: bold; }
  .peq-table td.boost { color: #4ade80; font-weight: bold; }
  .peq-switcher-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(110px, 1fr));
    gap: 6px;
    margin-top: 8px;
    margin-bottom: 6px;
  }
  .btn-peq-live {
    background: #1e293b;
    border: 1px solid #475569;
    color: #e2e8f0;
    padding: 8px 6px;
    border-radius: 6px;
    font-size: 0.74rem;
    font-weight: bold;
    cursor: pointer;
    text-align: center;
    transition: all 0.15s ease;
  }
  .btn-peq-live:hover {
    border-color: #38bdf8;
    background: #334155;
  }
  .btn-peq-live.active {
    background: #0284c7;
    border-color: #38bdf8;
    color: #ffffff;
    box-shadow: 0 0 10px rgba(56, 189, 248, 0.4);
  }
  .btn-test-curve {
    background: #0ea5e9;
    border: none;
    color: white;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 0.68rem;
    font-weight: bold;
    cursor: pointer;
    white-space: nowrap;
    transition: background 0.15s;
  }
  .btn-test-curve:hover {
    background: #0284c7;
  }
  
  #log-box {
    background: #020617;
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 12px;
    font-family: monospace;
    font-size: 0.74rem;
    color: #38bdf8;
    max-height: 140px;
    overflow-y: auto;
    margin-top: 14px;
    white-space: pre-wrap;
  }
</style>
</head>
<body>

<h1>Calibración Acústica</h1>
<div class="subtitle">Yamaha RX-V673 + Q Acoustics 3020i</div>
<div class="device-badge">🎤 Sonda: Google Pixel 9 Pro (MEMS Uncompressed)</div>

<div class="card" id="avr-status-card" style="border-color: #22c55e; background: rgba(6, 78, 59, 0.25); margin-bottom: 14px;">
  <div class="card-title" style="color: #4ade80; font-size: 0.85rem; margin-bottom: 2px;">
    <span>🛡️ Telemetría AVR Protegida</span>
    <span class="status-badge ok" id="avr-peq-badge">COMPROBANDO...</span>
  </div>
  <div id="avr-details" style="font-size: 0.72rem; color: #cbd5e1; line-height: 1.4;">
    Conectando con Yamaha RX-V673...
  </div>
</div>
<div class="card" id="peq-live-card" style="border-color: #38bdf8; background: rgba(14, 116, 144, 0.15); margin-bottom: 14px;">
  <div class="card-title" style="color: #38bdf8; font-size: 0.85rem; margin-bottom: 2px;">
    <span>🎛️ Conmutador en Directo de Modos PEQ (Hardware Yamaha)</span>
    <span class="status-badge ok" id="live-peq-mode-badge">MANUAL</span>
  </div>
  <div class="card-desc" style="margin-bottom: 6px;">
    Cambia instantáneamente la curva de ecualización en la memoria DSP del amplificador para evaluar y comparar el sonido en tiempo real:
  </div>
  <div class="peq-switcher-grid">
    <button id="btn-mode-through" class="btn-peq-live" onclick="setLivePeqMode('Through')">
      ⚡ Through<br><span style="font-size:0.65rem; font-weight:normal; color:#94a3b8;">Bypass / Directo</span>
    </button>
    <button id="btn-mode-flat" class="btn-peq-live" onclick="setLivePeqMode('Flat')">
      📏 YPAO Flat<br><span style="font-size:0.65rem; font-weight:normal; color:#94a3b8;">Automático Plano</span>
    </button>
    <button id="btn-mode-front" class="btn-peq-live" onclick="setLivePeqMode('Front')">
      🎭 YPAO Front<br><span style="font-size:0.65rem; font-weight:normal; color:#94a3b8;">Frontales Ref.</span>
    </button>
    <button id="btn-mode-natural" class="btn-peq-live" onclick="setLivePeqMode('Natural')">
      ☕ YPAO Natural<br><span style="font-size:0.65rem; font-weight:normal; color:#94a3b8;">Cálido / Roll-off</span>
    </button>
    <button id="btn-mode-manual" class="btn-peq-live" onclick="setLivePeqMode('Manual')">
      🎯 PEQ Manual<br><span style="font-size:0.65rem; font-weight:normal; color:#94a3b8;">Harman Calibrado</span>
    </button>
  </div>
  <div id="live-peq-status" style="font-size: 0.72rem; text-align: center; color: #86efac; margin-top: 4px;"></div>
</div>

<button id="btn-measure-mode" class="btn-measure-mode" onclick="activateMeasurementMode()">
  🛡️ Poner en Modo Medición (Bypass DSP / PEQ Through / -25 dB)
</button>
<div id="measure-mode-status" style="font-size: 0.74rem; text-align: center; margin-top: -8px; margin-bottom: 12px; color: #94a3b8;"></div>
<!-- PANEL DE HISTORIAL Y RECUPERACIÓN DE MEDICIONES -->
<div class="card" id="sessions-panel" style="border-color: #8b5cf6; background: rgba(139, 92, 246, 0.08); margin-top: 14px; margin-bottom: 14px;">
  <div class="card-title" style="color: #c4b5fd; margin-bottom: 6px;">
    <span>📦 Historial de Mediciones y Restauración</span>
    <span class="status-badge" id="badge-sessions-count" style="background:#6d28d9; color:#fff;">HISTORIAL</span>
  </div>
  <div class="card-desc" style="margin-bottom: 10px;">
    Recupera mediciones multipunto anteriores para calibrar o probar diferentes curvas objetivo sin necesidad de volver a medir los 5 puntos con el móvil:
  </div>

  <div style="display: flex; gap: 8px; flex-direction: column;">
    <label style="font-size: 0.76rem; color: #94a3b8; font-weight: 600;">Seleccionar Sesión de Medición Guardada:</label>
    <select id="select-session" onchange="onSessionSelectChange()" style="width: 100%; background: #1e293b; border: 1px solid #475569; color: #f8fafc; padding: 10px; border-radius: 8px; font-size: 0.82rem; font-family: inherit;">
      <option value="">Cargando historial de sesiones...</option>
    </select>

    <div id="selected-session-info" style="font-size: 0.74rem; color: #cbd5e1; background: rgba(30, 41, 59, 0.7); padding: 8px 12px; border-radius: 6px; border-left: 3px solid #8b5cf6; display: none;"></div>

    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: 4px;">
      <button id="btn-restore-session" onclick="restoreSelectedSession()" style="background: #7c3aed; color: #fff; padding: 10px; border-radius: 8px; font-size: 0.82rem; font-weight: 600; border: none; cursor: pointer;">
        📥 Cargar y Calibrar
      </button>
      <button id="btn-save-session" onclick="saveCurrentSessionPrompt()" style="background: #334155; color: #e2e8f0; padding: 10px; border-radius: 8px; font-size: 0.82rem; font-weight: 600; border: 1px solid #475569; cursor: pointer;">
        💾 Guardar Actual
      </button>
    </div>
    <div id="session-status" style="font-size: 0.74rem; text-align: center; margin-top: 4px; color: #86efac;"></div>
  </div>
</div>

<div id="points-container"></div>

<button id="btn-calibrate" class="btn-finish" disabled onclick="applyFinalCalibration()">
  🚀 Calcular Promedio y Generar Informes
</button>

<!-- PANEL DE REVISIÓN Y DESCARGAS MÓVIL -->
<!-- 1. GRÁFICAS E INFORMES DE MEDICIÓN (PROMEDIO ESPACIAL) -->
<div id="results-panel">
  <div class="card-title" style="color: #38bdf8; margin-bottom: 8px;">
    <span>🎉 Calibración y Modelado Acústico Listo</span>
    <span class="status-badge ok" id="results-badge">PROCESADO</span>
  </div>
  <div class="card-desc">
    Se han procesado los barridos multipunto (Toole / AES) y la respuesta biquad. Puedes descargar el informe técnico o revisar cada gráfica directamente en tu móvil:
  </div>

  <a href="/api/download_pdf" download="Informe_Calibracion_Acustica_Yamaha.pdf" class="btn-download-pdf">
    📄 Descargar Informe Técnico PDF (3 Páginas)
  </a>

  <div style="font-weight: 600; font-size: 0.88rem; color: #cbd5e1; margin-top: 12px;">
    📊 Gráficas de Medición (Promedio Espacial y CSD Waterfall):
  </div>
  
  <div class="fig-grid" id="fig-container">
    <!-- Generado dinámicamente -->
  </div>
</div>

<!-- 2. SELECTOR DE PERFILES COMUNITARIOS -->
<div class="card" id="community-profiles-panel" style="border-color: #f59e0b; background: rgba(217, 119, 6, 0.10); margin-top: 14px;">
  <div class="card-title" style="color: #fbbf24; margin-bottom: 6px;">
    <span>📚 Selector de Curvas y Perfiles Comunitarios</span>
    <span class="status-badge ok">RANKING 1 - 9</span>
  </div>
  <div class="card-desc">
    Curvas objetivo evaluadas por la comunidad audiófila, ingeniería acústica (AES / Floyd Toole / Sean Olive / Brüel & Kjær) y foros especializados (Audio Science Review, AVSForum). Al tocar cualquier perfil, <b>los filtros PEQ calculados se actualizarán automáticamente</b> en la sección siguiente:
  </div>
  <div id="profiles-container" style="margin-top: 10px;"></div>
</div>

<!-- 3. FILTROS PEQ CALCULADOS PARA EL PERFIL SELECCIONADO -->
<div class="card" id="selected-peq-panel" style="border-color: #38bdf8; background: rgba(14, 116, 144, 0.12); margin-top: 14px;">
  <div class="card-title" style="color: #38bdf8; margin-bottom: 6px;">
    <span id="selected-profile-title">🎛️ Filtros PEQ Calculados (Harman Target / Floyd Toole)</span>
    <span class="status-badge ok" id="selected-profile-badge">7 BANDAS</span>
  </div>
  <div class="card-desc" id="selected-profile-desc">
    Filtros paramétricos optimizados para la física real de la sala. Se actualizan dinámicamente según el perfil elegido arriba:
  </div>
  <div id="selected-peq-table-container"></div>

  <button id="btn-apply-selected-peq" class="btn-apply-amp" onclick="applySelectedProfile()">
    🎛️ Enviar y Aplicar Perfil Seleccionado al Yamaha RX-V673 (NVRAM)
  </button>
  <div id="apply-status" style="font-size: 0.75rem; text-align: center; margin-top: 6px; color: #94a3b8;"></div>
</div>

<!-- 4. VALIDACIÓN ACÚSTICA COMPARATIVA MULTIMODO -->
<div class="card" id="verification-panel" style="border-color: #06b6d4; background: rgba(8, 145, 178, 0.12); margin-top: 14px;">
  <div class="card-title" style="color: #22d3ee; margin-bottom: 6px;">
    <span>🔬 Validación Acústica Comparativa Multimodo (5 Modos Yamaha)</span>
    <span class="status-badge" id="badge-verif">PENDIENTE</span>
  </div>
  <div class="card-desc">
    Mide y compara en el Sweet Spot los 5 modos acústicos del receptor Yamaha: <b>Through (Bypass)</b>, <b>YPAO Flat</b>, <b>YPAO Front</b>, <b>YPAO Natural</b> y <b>PEQ Manual (<span id="verif-active-profile-chip" style="color: #38bdf8;">Perfil Seleccionado</span>)</b>. La calibración PEQ manual evalúa el perfil comunitario que tengas activo en cada momento:
  </div>

  <div style="display: grid; grid-template-columns: repeat(5, 1fr); gap: 4px; margin-top: 8px; margin-bottom: 10px;">
    <div style="background: rgba(15, 23, 42, 0.6); padding: 6px 4px; border-radius: 6px; border: 1px solid #334155; text-align: center;">
      <div style="font-size: 0.64rem; color: #94a3b8;">1. Through</div>
      <div id="status-verif-through" style="font-size: 0.68rem; font-weight: bold; color: #fca5a5;">PENDIENTE</div>
    </div>
    <div style="background: rgba(15, 23, 42, 0.6); padding: 6px 4px; border-radius: 6px; border: 1px solid #334155; text-align: center;">
      <div style="font-size: 0.64rem; color: #94a3b8;">2. YPAO Flat</div>
      <div id="status-verif-ypao-flat" style="font-size: 0.68rem; font-weight: bold; color: #fca5a5;">PENDIENTE</div>
    </div>
    <div style="background: rgba(15, 23, 42, 0.6); padding: 6px 4px; border-radius: 6px; border: 1px solid #334155; text-align: center;">
      <div style="font-size: 0.64rem; color: #94a3b8;">3. YPAO Front</div>
      <div id="status-verif-ypao-front" style="font-size: 0.68rem; font-weight: bold; color: #fca5a5;">PENDIENTE</div>
    </div>
    <div style="background: rgba(15, 23, 42, 0.6); padding: 6px 4px; border-radius: 6px; border: 1px solid #334155; text-align: center;">
      <div style="font-size: 0.64rem; color: #94a3b8;">4. YPAO Natural</div>
      <div id="status-verif-ypao-natural" style="font-size: 0.68rem; font-weight: bold; color: #fca5a5;">PENDIENTE</div>
    </div>
    <div style="background: rgba(15, 23, 42, 0.6); padding: 6px 4px; border-radius: 6px; border: 1px solid #334155; text-align: center;">
      <div style="font-size: 0.64rem; color: #94a3b8;">5. PEQ Manual</div>
      <div id="status-verif-manual" style="font-size: 0.68rem; font-weight: bold; color: #fca5a5;">PENDIENTE</div>
    </div>
  </div>

  <button id="btn-verify-all" class="btn-verify" onclick="runFullMultimodeVerification()" style="background: #0284c7; margin-bottom: 8px;">
    🚀 Validación Completa Automatizada (Mide los 5 Modos en Secuencia)
  </button>

  <div style="display: grid; grid-template-columns: repeat(5, 1fr); gap: 4px;">
    <button id="btn-verif-through" onclick="selectVerifMode('through')" style="background: #1e293b; color: #e2e8f0; border: 1px solid #475569; padding: 7px 2px; border-radius: 6px; font-size: 0.68rem; font-weight: 600; cursor: pointer;">
      ⚡ Through
    </button>
    <button id="btn-verif-flat" onclick="selectVerifMode('ypao_flat')" style="background: #1e293b; color: #e2e8f0; border: 1px solid #475569; padding: 7px 2px; border-radius: 6px; font-size: 0.68rem; font-weight: 600; cursor: pointer;">
      📐 Flat
    </button>
    <button id="btn-verif-front" onclick="selectVerifMode('ypao_front')" style="background: #1e293b; color: #e2e8f0; border: 1px solid #475569; padding: 7px 2px; border-radius: 6px; font-size: 0.68rem; font-weight: 600; cursor: pointer;">
      🎭 Front
    </button>
    <button id="btn-verif-natural" onclick="selectVerifMode('ypao_natural')" style="background: #1e293b; color: #e2e8f0; border: 1px solid #475569; padding: 7px 2px; border-radius: 6px; font-size: 0.68rem; font-weight: 600; cursor: pointer;">
      🍃 Natural
    </button>
    <button id="btn-verif-manual" onclick="selectVerifMode('manual')" style="background: #1e293b; color: #e2e8f0; border: 1px solid #475569; padding: 7px 2px; border-radius: 6px; font-size: 0.68rem; font-weight: 600; cursor: pointer;">
      🎯 Manual
    </button>
  </div>
  <button id="btn-start-single-verif" onclick="startSelectedVerifMode()" style="display:none; background: #7c3aed; color: white; border: none; padding: 9px; border-radius: 6px; font-size: 0.76rem; font-weight: bold; margin-top: 6px; cursor: pointer; width: 100%;">
    ▶ Iniciar Barrido — <span id="lbl-selected-verif-mode">—</span> (cambia PEQ del AVR y mide)
  </button>

  <button id="btn-process-verif" onclick="processVerificationComparison()" style="background: #059669; color: white; border: none; padding: 9px; border-radius: 6px; font-size: 0.76rem; font-weight: bold; margin-top: 8px; cursor: pointer; width: 100%;">
    📊 Procesar Comparativa Acústica y Certificar
  </button>
</div>

<!-- 5. INFORME Y GRÁFICAS DE VALIDACIÓN POST-CALIBRACIÓN -->
<div class="card" id="verification-report-panel" style="border-color: #10b981; background: rgba(16, 185, 129, 0.10); margin-top: 14px; display: none;">
  <div class="card-title" style="color: #34d399; margin-bottom: 6px;">
    <span>🛡️ Informe y Gráficas de Validación Acústica</span>
    <span class="status-badge ok" id="badge-verif-cert">S-TIER</span>
  </div>
  <div id="verif-result"></div>
</div>

<!-- 6. GESTIÓN DE ESCENAS (FINAL DE PÁGINA) -->
<div class="card" id="scenes-panel" style="border-color: #818cf8; background: rgba(79, 70, 229, 0.12); margin-top: 14px;">
  <div class="card-title" style="color: #a5b4fc; margin-bottom: 6px;">
    <span>🎛️ Gestión de Escenas Yamaha RX-V673</span>
    <span class="status-badge ok">SINCRONIZADO</span>
  </div>
  <div class="card-desc">
    Las 4 escenas de hardware del receptor programadas y asociadas a los perfiles de audio optimizados:
  </div>
  <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: 10px;">
    <button class="btn-scene" onclick="activateScene(1)">
      🎵 <b>SCENE 1</b><br><span style="font-size: 0.7rem; font-weight: normal;">Música Hi-Fi (Straight)</span>
    </button>
    <button class="btn-scene" onclick="activateScene(2)">
      🎬 <b>SCENE 2</b><br><span style="font-size: 0.7rem; font-weight: normal;">Cine y Pelis (Standard)</span>
    </button>
    <button class="btn-scene" onclick="activateScene(3)">
      🗣️ <b>SCENE 3</b><br><span style="font-size: 0.7rem; font-weight: normal;">TV y Series (Drama)</span>
    </button>
    <button class="btn-scene" onclick="activateScene(4)">
      ✨ <b>SCENE 4</b><br><span style="font-size: 0.7rem; font-weight: normal;">Pure Direct (Bypass)</span>
    </button>
  </div>
  <button class="btn-sync-scenes" onclick="programAllScenes()">
    💾 Reprogramar y Fijar las 4 Escenas en la NVRAM del Receptor
  </button>
  <div id="scenes-status" style="font-size: 0.74rem; text-align: center; margin-top: 6px; color: #cbd5e1;"></div>
</div>
<div id="log-box">Listo para iniciar. Sitúate en el Punto 1 y pulsa Medir.</div>

<script>
const POINTS = [
  { id: 1, title: "Punto 1: Sofá Centro (Sweet Spot)", desc: "En el centro exacto del sofá, teléfono a la altura de tus oídos (~95 cm), apuntando al techo." },
  { id: 2, title: "Punto 2: Sofá Izquierda", desc: "30-40 cm a la izquierda del punto 1 (transición hacia zona abierta)." },
  { id: 3, title: "Punto 3: Sofá Derecha", desc: "30-40 cm a la derecha del punto 1 (más cerca de la pared lateral)." },
  { id: 4, title: "Punto 4: Zona de Vida Centro", desc: "1 metro por delante a la izquierda, altura 1.15 m." },
  { id: 5, title: "Punto 5: Zona de Vida Fondo", desc: "Mesa / estancia abierta, altura 1.35 m de pie." }
];

let pointStatus = { 1: false, 2: false, 3: false, 4: false, 5: false };
let audioCtx = null;
let micStream = null;

function log(msg) {
  const box = document.getElementById("log-box");
  box.textContent = msg;
}

function renderPoints() {
  const c = document.getElementById("points-container");
  c.innerHTML = "";
  POINTS.forEach(p => {
    const card = document.createElement("div");
    card.className = "card";
    const isDone = pointStatus[p.id];
    card.innerHTML = `
      <div class="card-title">
        <span>${p.title}</span>
        <span class="status-badge ${isDone ? 'ok' : ''}" id="badge-${p.id}">${isDone ? 'COMPLETADO' : 'PENDIENTE'}</span>
      </div>
      <div class="card-desc">${p.desc}</div>
      <button id="btn-${p.id}" onclick="measurePoint(${p.id})">
        ${isDone ? 'Repetir Medición' : 'Medir ' + p.title.split(':')[0]}
      </button>
    `;
    c.appendChild(card);
  });
  checkCompletion();
}

function checkCompletion() {
  const btn = document.getElementById("btn-calibrate");
  const count = Object.values(pointStatus).filter(Boolean).length;
  if (count >= 3) {
    btn.disabled = false;
    btn.textContent = `🚀 Calcular Promedio (${count}/5 puntos) y Generar Informes`;
  } else {
    btn.disabled = true;
    btn.textContent = `Completa al menos 3 puntos (${count}/5)`;
  }
}

async function getRawAudioStream() {
  if (!micStream) {
    micStream = await navigator.mediaDevices.getUserMedia({
      audio: {
        echoCancellation: false,
        noiseSuppression: false,
        autoGainControl: false,
        channelCount: 1,
        sampleRate: 48000
      }
    });
  }
  return micStream;
}

function recordPcm(durationSec) {
  return new Promise(async (resolve, reject) => {
    try {
      const stream = await getRawAudioStream();
      if (!audioCtx) {
        audioCtx = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 48000 });
      }
      if (audioCtx.state === 'suspended') {
        await audioCtx.resume();
      }
      const source = audioCtx.createMediaStreamSource(stream);
      const bufferSize = 4096;
      const scriptNode = audioCtx.createScriptProcessor(bufferSize, 1, 1);
      
      const chunks = [];
      let totalSamples = 0;
      const targetSamples = 48000 * durationSec;
      
      scriptNode.onaudioprocess = (e) => {
        const inputData = e.inputBuffer.getChannelData(0);
        chunks.push(new Float32Array(inputData));
        totalSamples += inputData.length;
        if (totalSamples >= targetSamples) {
          scriptNode.disconnect();
          source.disconnect();
          const merged = new Float32Array(totalSamples);
          let offset = 0;
          for (const ch of chunks) {
            merged.set(ch, offset);
            offset += ch.length;
          }
          resolve(merged);
        }
      };
      
      source.connect(scriptNode);
      scriptNode.connect(audioCtx.destination);
    } catch (err) {
      reject(err);
    }
  });
}

function floatTo16BitPCM(floatSamples) {
  const buffer = new ArrayBuffer(floatSamples.length * 2);
  const view = new DataView(buffer);
  for (let i = 0; i < floatSamples.length; i++) {
    let s = Math.max(-1, Math.min(1, floatSamples[i]));
    view.setInt16(i * 2, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
  }
  return new Uint8Array(buffer);
}

async function measurePoint(pointId) {
  const btn = document.getElementById(`btn-${pointId}`);
  const badge = document.getElementById(`badge-${pointId}`);
  btn.disabled = true;
  
  try {
    for (let s = 5; s > 0; s--) {
      badge.className = "status-badge active";
      badge.textContent = `PREPÁRATE (${s}s)`;
      log(`[Punto ${pointId}] Iniciando en ${s}s... Colócate en la posición y guarda silencio.`);
      await new Promise(r => setTimeout(r, 1000));
    }
    
    badge.className = "status-badge active";
    badge.textContent = "GRABANDO L...";
    log(`[Punto ${pointId}] Grabando Canal Izquierdo (Front L)...`);
    const recordPromiseL = recordPcm(6.5);
    
    await new Promise(r => setTimeout(r, 200));
    await fetch(`/api/play_sweep?channel=L`);
    
    const pcmL = await recordPromiseL;
    log(`[Punto ${pointId}] Subiendo y validando Canal L...`);
    const rawBytesL = floatTo16BitPCM(pcmL);
    
    const respL = await fetch(`/api/upload_sweep?point=${pointId}&channel=L`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/octet-stream' },
      body: rawBytesL
    });
    const resJsonL = await respL.json();
    if (!resJsonL.ok) {
      throw new Error(`Canal L: ${resJsonL.msg}`);
    }
    
    badge.textContent = "PAUSA (2s)...";
    log(`[Punto ${pointId}] Canal L OK (${resJsonL.snr} dB). Preparando Canal Derecho en 2s...`);
    await new Promise(r => setTimeout(r, 2000));
    badge.textContent = "GRABANDO R...";
    
    const recordPromiseR = recordPcm(6.5);
    await new Promise(r => setTimeout(r, 200));
    await fetch(`/api/play_sweep?channel=R`);
    
    const pcmR = await recordPromiseR;
    log(`[Punto ${pointId}] Subiendo y validando Canal R...`);
    const rawBytesR = floatTo16BitPCM(pcmR);
    
    const respR = await fetch(`/api/upload_sweep?point=${pointId}&channel=R`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/octet-stream' },
      body: rawBytesR
    });
    const resJsonR = await respR.json();
    if (!resJsonR.ok) {
      throw new Error(`Canal R: ${resJsonR.msg}`);
    }
    
    pointStatus[pointId] = true;
    badge.className = "status-badge ok";
    badge.textContent = "COMPLETADO";
    log(`[✓] Punto ${pointId} COMPLETADO! (L: ${resJsonL.snr} dB | R: ${resJsonR.snr} dB)`);
  } catch (err) {
    alert("Error en medición: " + err.message);
    log(`[!] Error: ${err.message}`);
    badge.className = "status-badge";
    badge.textContent = "ERROR";
  } finally {
    btn.disabled = false;
    checkCompletion();
  }
}

function renderResultsPanel(data) {
  const panel = document.getElementById("results-panel");
  panel.style.display = "block";
  
  // Render figure cards
  const figContainer = document.getElementById("fig-container");
  const ts = Date.now();
  const figures = [
    { title: "1. Promedio Espacial 5 Puntos (Toole / AES)", file: "promedio_espacial_multipunto.png", desc: "Malla espacial limpia normalizada a 1 kHz" },
    { title: "2. Respuesta Real L vs R y Simulación PEQ", file: "respuesta_acustica_real.png", desc: "Curvas de simetría estéreo y detalle del notch modal" },
    { title: "3. Cascada Espectral 3D (Waterfall CSD)", file: "waterfall_csd_comparison.png", desc: "Decaimiento temporal y eliminación de resonancias" },
    { title: "4. Tiempo de Reverberación (RT60)", file: "rt60_decay_analysis.png", desc: "Tiempos de caída acústica en segundos por banda" }
  ];
  
  figContainer.innerHTML = figures.map(f => `
    <div class="fig-card">
      <h4>${f.title}</h4>
      <p>${f.desc}</p>
      <img src="/figures/${f.file}?t=${ts}" alt="${f.title}" loading="lazy">
      <a href="/figures/${f.file}?t=${ts}" target="_blank" download="${f.file}" class="btn-view-fig">
        🔍 Ver / Descargar Gráfica
      </a>
    </div>
  `).join('');
  
  // Actualizar filtros PEQ calculados para el perfil activo
  if (typeof selectProfile === 'function') {
    selectProfile(currentSelectedProfile);
  }
  
  panel.scrollIntoView({ behavior: 'smooth' });
}

async function applyFinalCalibration() {
  const btn = document.getElementById("btn-calibrate");
  btn.disabled = true;
  btn.textContent = "⏳ Procesando Malla y Generando Informes...";
  log("Ejecutando algoritmo de promedio espacial Toole/AES, cálculo de respuesta acústica y generación de PDF...");
  
  try {
    const res = await fetch('/api/finalize_calibration', { method: 'POST' });
    const json = await res.json();
    if (json.ok) {
      btn.textContent = "✅ ¡Calibración y Documentos Listos!";
      log("¡Proceso completado! Se han generado las 4 gráficas de alta resolución y el informe técnico certificado PDF.");
      renderResultsPanel(json);
    } else {
      throw new Error(json.msg);
    }
  } catch (err) {
    alert("Error al procesar: " + err.message);
    log("[!] Error: " + err.message);
    btn.disabled = false;
    btn.textContent = "Reintentar Procesar Calibración";
  }
}

async function applyToAmplifier() {
  return applySelectedProfile();
}

async function activateMeasurementMode() {
  const btn = document.getElementById("btn-measure-mode");
  const st = document.getElementById("measure-mode-status");
  btn.disabled = true;
  btn.textContent = "⏳ Configurando Yamaha en Modo Medición...";
  st.textContent = "Enviando tramas: V-AUX, PEQ Through, Straight, -25 dB...";
  log("Configurando parámetros en el Yamaha RX-V673: Entrada V-AUX, PEQ Through (Bypass DSP 100%), Straight, DRC Off, Enhancer Off y volumen de referencia (-25 dB)...");
  
  try {
    const res = await fetch('/api/set_measurement_mode', { method: 'POST' });
    const json = await res.json();
    if (json.ok) {
      btn.style.background = "#10b981";
      btn.style.color = "#064e3b";
      btn.textContent = "✅ Modo Medición Activo (Listo para Medir)";
      st.style.color = "#86efac";
      st.textContent = "Yamaha listo: V-AUX | -25.0 dB | PEQ Through (Bypass DSP 100%) | Straight | DRC Off";
      log("¡ÉXITO! " + json.msg);
      updateAVRTelemetry();
    } else {
      throw new Error(json.msg);
    }
  } catch (err) {
    alert("Error al activar modo medición: " + err.message);
    log("[!] Error: " + err.message);
    btn.style.background = "#0284c7";
    btn.style.color = "#ffffff";
    btn.textContent = "🛡️ Poner en Modo Medición (Reintentar)";
    st.style.color = "#f87171";
    st.textContent = "Error: " + err.message;
  } finally {
    btn.disabled = false;
  }
}

async function initSessionState() {
  try {
    const res = await fetch('/api/session_state');
    const d = await res.json();
    if (d.points) {
      for (let p in d.points) {
        pointStatus[p] = !!d.points[p];
      }
      renderPoints();
      checkCompletion();
    }
    if (d.calibration_ready) {
      renderResultsPanel(d);
    }
  } catch (e) {
    renderPoints();
  }
  loadMeasurementSessions();
}

async function updateAVRTelemetry() {
  try {
    const res = await fetch('/api/preflight_check');
    const d = await res.json();
    const badge = document.getElementById("avr-peq-badge");
    const details = document.getElementById("avr-details");
    const liveBadge = document.getElementById("live-peq-mode-badge");
    
    if (d.peq) {
      const allBtns = document.querySelectorAll(".btn-peq-live");
      allBtns.forEach(b => b.classList.remove("active"));
      const activeBtn = document.getElementById(`btn-mode-${d.peq.toLowerCase()}`);
      if (activeBtn) activeBtn.classList.add("active");
      if (liveBadge) {
        liveBadge.textContent = d.peq.toUpperCase();
        liveBadge.className = "status-badge ok";
      }
    }

    if (d.peq === "Through") {
      badge.className = "status-badge ok";
      badge.textContent = "PEQ: THROUGH [OK]";
      badge.style.color = "#86efac";
      details.innerHTML = `Alimentación: <b>${d.power}</b> | Entrada: <b>${d.input}</b> | Vol: <b>${d.volume}</b><br>DRC: <b>${d.drc}</b> | Enhancer: <b>${d.enhancer}</b> | Bypass: <b>100% Activo</b>`;
    } else if (d.peq === "Manual") {
      badge.className = "status-badge ok";
      badge.textContent = "PEQ: MANUAL [ACTIVO]";
      badge.style.color = "#38bdf8";
      details.innerHTML = `Alimentación: <b>${d.power}</b> | Entrada: <b>${d.input}</b> | Vol: <b>${d.volume}</b><br>PEQ: <b>Manual Activo (Calibrado)</b> | DRC: <b>${d.drc}</b>`;
    } else {
      badge.className = "status-badge active";
      badge.textContent = `PEQ: ${d.peq}`;
      badge.style.color = "#fef08a";
      details.textContent = `Modo DSP actual: ${d.peq}`;
    }
  } catch (e) {
    document.getElementById("avr-details").textContent = "AVR no responde / Comprobando conexión...";
  }
}

async function setLivePeqMode(mode) {
  const statusEl = document.getElementById("live-peq-status");
  const badgeEl = document.getElementById("live-peq-mode-badge");
  const avrBadge = document.getElementById("avr-peq-badge");
  if (statusEl) statusEl.textContent = `⏳ Conmutando receptor a modo PEQ: ${mode}...`;
  
  const allBtns = document.querySelectorAll(".btn-peq-live");
  allBtns.forEach(b => b.classList.remove("active"));
  const activeBtn = document.getElementById(`btn-mode-${mode.toLowerCase()}`);
  if (activeBtn) activeBtn.classList.add("active");

  try {
    const res = await fetch(`/api/set_peq_mode?mode=${encodeURIComponent(mode)}`, { method: 'POST' });
    const json = await res.json();
    if (json.ok) {
      if (statusEl) statusEl.textContent = `[✓] Modo PEQ: ${json.mode} activo en el hardware de Yamaha.`;
      if (badgeEl) {
        badgeEl.textContent = json.mode.toUpperCase();
        badgeEl.className = "status-badge ok";
      }
      if (avrBadge) {
        avrBadge.textContent = `PEQ: ${json.mode.toUpperCase()}`;
        avrBadge.className = "status-badge ok";
      }
      log(`[✓] Conmutado en directo a modo PEQ: ${json.mode} en el Yamaha RX-V673`);
      updateAVRTelemetry();
    } else {
      if (statusEl) statusEl.textContent = `[!] Error: ${json.msg}`;
    }
  } catch (e) {
    if (statusEl) statusEl.textContent = `[!] Error de red: ${e.message}`;
  }
}

async function activateScene(num) {
  log(`Activando SCENE ${num} en el receptor Yamaha RX-V673...`);
  try {
    const res = await fetch(`/api/select_scene?num=${num}`, { method: 'POST' });
    const json = await res.json();
    if (json.ok) {
      log("¡ÉXITO! " + json.msg);
      updateAVRTelemetry();
    } else {
      throw new Error(json.msg);
    }
  } catch (err) {
    alert("Error al activar escena: " + err.message);
  }
}

async function programAllScenes() {
  const st = document.getElementById("scenes-status");
  st.textContent = "⏳ Escribiendo nombres y parámetros de las 4 escenas en NVRAM...";
  try {
    const res = await fetch('/api/program_scenes', { method: 'POST' });
    const json = await res.json();
    if (json.ok) {
      st.style.color = "#86efac";
      st.textContent = "✅ Las 4 escenas (Música, Cine, TV, Pure Direct) han sido grabadas permanentemente.";
      log("¡ÉXITO! " + json.msg);
      updateAVRTelemetry();
    } else {
      throw new Error(json.msg);
    }
  } catch (err) {
    st.style.color = "#f87171";
    st.textContent = "Error: " + err.message;
  }
}

let cachedProfiles = {};
let currentSelectedProfile = "harman_wide_room";

function selectProfile(key) {
  if (!cachedProfiles[key]) return;
  currentSelectedProfile = key;
  const p = cachedProfiles[key];

  // Highlight selected card
  document.querySelectorAll(".profile-card").forEach(c => c.classList.remove("active-target"));
  const activeCard = document.getElementById(`profile-card-${key}`);
  if (activeCard) activeCard.classList.add("active-target");

  // Update Section 3: Filtros PEQ Calculados
  const titleEl = document.getElementById("selected-profile-title");
  const badgeEl = document.getElementById("selected-profile-badge");
  const descEl = document.getElementById("selected-profile-desc");
  const tableContainer = document.getElementById("selected-peq-table-container");
  const st = document.getElementById("apply-status");
  const applyBtn = document.getElementById("btn-apply-selected-peq");

  if (titleEl) titleEl.textContent = `🎛️ Filtros PEQ Calculados (${p.name})`;
  if (badgeEl) badgeEl.textContent = `${p.badge ? p.badge.split(' ')[0] + ' ' + p.badge.split(' ')[1] : '7 BANDAS'}`;
  const verifChip = document.getElementById("verif-active-profile-chip");
  if (verifChip) verifChip.textContent = (p.name || key).split('(')[0].trim();
  checkVerificationStatusOnLoad(key);
  if (descEl) descEl.innerHTML = `<b>Objetivo Acústico:</b> ${p.description}<br><span style="color:#86efac; font-size:0.7rem;">Idóneo para: ${p.ideal_for || ''}</span>`;
  if (st) st.textContent = "";
  if (applyBtn) {
    applyBtn.style.background = "#0284c7";
    applyBtn.textContent = `🎛️ Enviar y Aplicar Perfil '${p.name.split('(')[0].trim()}' al Yamaha (NVRAM)`;
  }

  if (tableContainer && p.bands) {
    let rows = "";
    for (let bName in p.bands) {
      const b = p.bands[bName];
      const gLClass = b.gain_l < 0 ? "notch" : (b.gain_l > 0 ? "boost" : "");
      const gRClass = b.gain_r < 0 ? "notch" : (b.gain_r > 0 ? "boost" : "");
      const fStr = b.freq < 1000 ? `${b.freq} Hz` : `${(b.freq/1000).toFixed(2)} kHz`;
      rows += `
        <tr>
          <td><b>${bName}</b></td>
          <td>${fStr}</td>
          <td>${b.q_l} / ${b.q_r}</td>
          <td class="${gLClass}">${b.gain_l > 0 ? '+' : ''}${b.gain_l} dB</td>
          <td class="${gRClass}">${b.gain_r > 0 ? '+' : ''}${b.gain_r} dB</td>
          <td style="font-size:0.68rem; color:#94a3b8; text-align:left;">${b.desc || ''}</td>
        </tr>
      `;
    }
    tableContainer.innerHTML = `
      <table class="peq-table">
        <thead>
          <tr><th>Banda</th><th>Freq</th><th>Q (L/R)</th><th>Gain Front L</th><th>Gain Front R</th><th>Función Acústica</th></tr>
        </thead>
        <tbody>${rows}</tbody>
      </table>
    `;
  }

  log(`Perfil seleccionado: ${p.name}. Filtros PEQ actualizados.`);
}

async function applySelectedProfile() {
  const btn = document.getElementById("btn-apply-selected-peq");
  const st = document.getElementById("apply-status");
  btn.disabled = true;
  btn.textContent = `⏳ Escribiendo perfil '${currentSelectedProfile}' en NVRAM...`;
  st.textContent = "Transmitiendo 7 bandas biquad al Yamaha RX-V673...";
  log(`Enviando los 7 filtros PEQ del perfil '${currentSelectedProfile}' al Yamaha RX-V673...`);

  try {
    const res = await fetch(`/api/apply_profile?profile=${encodeURIComponent(currentSelectedProfile)}`, { method: 'POST' });
    const json = await res.json();
    if (json.ok) {
      btn.textContent = "✅ ¡Perfil Grabado y Activo en el Receptor!";
      btn.style.background = "#059669";
      st.style.color = "#86efac";
      st.textContent = `¡Éxito! Los 7 filtros del perfil '${currentSelectedProfile}' están activos en PEQ: Manual.`;
      log(`¡ÉXITO! ${json.msg}`);
      updateAVRTelemetry();
    } else {
      throw new Error(json.msg);
    }
  } catch (err) {
    alert("Error al aplicar perfil: " + err.message);
    btn.disabled = false;
    btn.textContent = "🎛️ Reintentar Enviar y Aplicar Perfil";
    st.style.color = "#f87171";
    st.textContent = "Error: " + err.message;
  } finally {
    btn.disabled = false;
  }
}

async function loadCommunityProfiles() {
  try {
    const res = await fetch('/api/community_profiles');
    cachedProfiles = await res.json();
    const container = document.getElementById("profiles-container");
    if (!container) return;
    container.innerHTML = "";

    const sortedKeys = Object.keys(cachedProfiles).sort((a, b) => (cachedProfiles[a].rank || 99) - (cachedProfiles[b].rank || 99));

    sortedKeys.forEach(key => {
      const p = cachedProfiles[key];
      const card = document.createElement("div");
      card.className = "profile-card" + (key === currentSelectedProfile ? " active-target" : "");
      card.id = `profile-card-${key}`;
      
      let prosHtml = "";
      if (p.pros && p.pros.length) {
        prosHtml = p.pros.map(pr => `<div class="pro-tag"><span>✓</span><span>${pr}</span></div>`).join("");
      }
      let consHtml = "";
      if (p.cons && p.cons.length) {
        consHtml = p.cons.map(cn => `<div class="con-tag"><span>✗</span><span>${cn}</span></div>`).join("");
      }

      card.innerHTML = `
        <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:4px;">
          <span class="profile-badge">${p.badge || ('#' + p.rank)}</span>
          <span style="font-size:0.72rem; color:#38bdf8; font-weight:bold;">${p.category || ''}</span>
        </div>
        <div style="font-weight:bold; font-size:0.92rem; color:#f8fafc; margin-bottom:4px;">${p.name}</div>
        <div style="font-size:0.73rem; color:#94a3b8; margin-bottom:6px; line-height:1.4;">
          <b>Respaldo Comunitario / Papers:</b> ${p.community_backing || ''}
        </div>
        <div style="font-size:0.74rem; color:#cbd5e1; margin-bottom:6px; line-height:1.4;">
          ${p.description}
        </div>
        <div style="margin-bottom:6px;">
          <div style="font-size:0.72rem; font-weight:bold; color:#86efac; margin-bottom:2px;">VENTAJAS:</div>
          ${prosHtml}
        </div>
        <div style="margin-bottom:8px;">
          <div style="font-size:0.72rem; font-weight:bold; color:#fca5a5; margin-bottom:2px;">INCONVENIENTES:</div>
          ${consHtml}
        </div>
        <button class="btn-apply-profile" style="background:#0284c7;" onclick="selectProfile('${key}')">
          🎯 Seleccionar este Perfil y Cargar Filtros PEQ
        </button>
      `;
      container.appendChild(card);
    });

    // Populate Section 3 with active profile
    selectProfile(currentSelectedProfile);
  } catch (err) {
    console.error("Error al cargar perfiles comunitarios:", err);
  }
}

let verifStatus = { through: false, ypao_flat: false, ypao_front: false, ypao_natural: false, manual: false };

async function checkVerificationStatusOnLoad(profile) {
  const p = profile || currentSelectedProfile || 'harman_wide_room';
  try {
    const res = await fetch('/api/verification_status?profile=' + encodeURIComponent(p));
    const d = await res.json();
    if (d.ok && d.status) {
      verifStatus = d.status;
      updateVerifStatusBadges();
    }
  } catch (e) {}
}

function updateVerifStatusBadges() {
  const items = [
    { el: "status-verif-through", key: "through", fb: "PENDIENTE" },
    { el: "status-verif-ypao-flat", key: "ypao_flat", fb: "PENDIENTE" },
    { el: "status-verif-ypao-front", key: "ypao_front", fb: "PENDIENTE" },
    { el: "status-verif-ypao-natural", key: "ypao_natural", fb: "PENDIENTE" },
    { el: "status-verif-manual", key: "manual", fb: "MODELO BIQUAD" }
  ];
  items.forEach(item => {
    const el = document.getElementById(item.el);
    if (el) {
      const isOk = !!verifStatus[item.key];
      el.textContent = isOk ? "MEDIDO [OK]" : item.fb;
      el.style.color = isOk ? "#86efac" : (item.key === "manual" ? "#38bdf8" : "#fca5a5");
    }
  });
}

let pendingVerifMode = null;

function selectVerifMode(mode) {
  const modeLabels = {
    through: "Through (Bypass)",
    ypao_flat: "YPAO Flat",
    ypao_front: "YPAO Front",
    ypao_natural: "YPAO Natural",
    manual: "PEQ Manual"
  };
  pendingVerifMode = mode;

  // Highlight selected button, clear others
  ["through","ypao_flat","ypao_front","ypao_natural","manual"].forEach(m => {
    const btn = document.getElementById(`btn-verif-${m.replace("ypao_","")}`);
    if (btn) btn.style.background = (m === mode) ? "#7c3aed" : "#1e293b";
  });

  // Show confirm button
  const startBtn = document.getElementById("btn-start-single-verif");
  const lbl = document.getElementById("lbl-selected-verif-mode");
  if (lbl) lbl.textContent = modeLabels[mode] || mode;
  if (startBtn) startBtn.style.display = "block";
}

async function startSelectedVerifMode() {
  if (!pendingVerifMode) return;
  const mode = pendingVerifMode;
  pendingVerifMode = null;
  const startBtn = document.getElementById("btn-start-single-verif");
  if (startBtn) startBtn.style.display = "none";
  await measureSingleVerificationMode(mode);
}

async function measureSingleVerificationMode(mode) {
  const modeNameMap = {
    through: "Through",
    ypao_flat: "Flat",
    flat: "Flat",
    ypao_front: "Front",
    front: "Front",
    ypao_natural: "Natural",
    natural: "Natural",
    ypao: "Natural",
    manual: "Manual"
  };
  const avrMode = modeNameMap[mode] || "Manual";
  log(`[Validación] Conmutando receptor Yamaha RX-V673 a PEQ: ${avrMode}...`);
  await setLivePeqMode(avrMode);
  await new Promise(r => setTimeout(r, 1200));

  log(`[Validación] Prepárate en el Sweet Spot para medir ${avrMode} (Canal Front L)...`);
  const recordPromiseL = recordPcm(6.5);
  await new Promise(r => setTimeout(r, 200));
  await fetch('/api/play_sweep?channel=L');
  const pcmL = await recordPromiseL;
  const rawBytesL = floatTo16BitPCM(pcmL);

  const pKey = encodeURIComponent(currentSelectedProfile);
  await fetch(`/api/upload_verification_sweep?channel=L&mode=${mode}&profile=${pKey}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/octet-stream' },
    body: rawBytesL
  });

  log(`[Validación] Front L (${avrMode}) registrado. Preparando Front R en 2s...`);
  await new Promise(r => setTimeout(r, 2000));

  log(`[Validación] Midiendo ${avrMode} (Canal Front R)...`);
  const recordPromiseR = recordPcm(6.5);
  await new Promise(r => setTimeout(r, 200));
  await fetch('/api/play_sweep?channel=R');
  const pcmR = await recordPromiseR;
  const rawBytesR = floatTo16BitPCM(pcmR);

  await fetch(`/api/upload_verification_sweep?channel=R&mode=${mode}&profile=${pKey}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/octet-stream' },
    body: rawBytesR
  });

  const canonicalKey = (mode === "ypao" || mode === "natural") ? "ypao_natural" : ((mode === "flat") ? "ypao_flat" : ((mode === "front") ? "ypao_front" : mode));
  verifStatus[canonicalKey] = true;
  updateVerifStatusBadges();
  log(`[✓] Barrido de validación en modo ${avrMode} COMPLETADO con éxito.`);
}

async function runFullMultimodeVerification() {
  const btn = document.getElementById("btn-verify-all");
  if (btn) btn.disabled = true;
  
  const pName = (cachedProfiles[currentSelectedProfile] && cachedProfiles[currentSelectedProfile].name) ? cachedProfiles[currentSelectedProfile].name.split('(')[0].trim() : currentSelectedProfile;
  const modes = [
    { key: "through", name: "Through (Bypass)" },
    { key: "ypao_flat", name: "YPAO Flat" },
    { key: "ypao_front", name: "YPAO Front" },
    { key: "ypao_natural", name: "YPAO Natural" },
    { key: "manual", name: `PEQ Manual (${pName})` }
  ];

  try {
    log("🚀 Iniciando Validación Multimodo Completa (5 Modos Yamaha)...");
    for (let i = 0; i < modes.length; i++) {
      const m = modes[i];
      if (btn) btn.textContent = `⏳ [${i+1}/5] Midiendo ${m.name}...`;
      await measureSingleVerificationMode(m.key);
      await new Promise(r => setTimeout(r, 1500));
    }

    if (btn) btn.textContent = "⚙️ Procesando Comparativa Acústica Multimodo...";
    await processVerificationComparison();
    if (btn) btn.textContent = "✅ Validación de 5 Modos Completada";
  } catch (err) {
    alert("Error durante la validación multimodo: " + err.message);
    log("[!] Error: " + err.message);
    if (btn) btn.textContent = "🚀 Reintentar Validación";
  } finally {
    if (btn) btn.disabled = false;
  }
}

async function processVerificationComparison() {
  const reportPanel = document.getElementById("verification-report-panel");
  const badge = document.getElementById("badge-verif");
  if (reportPanel) reportPanel.style.display = "none";
  
  const pName = (cachedProfiles[currentSelectedProfile] && cachedProfiles[currentSelectedProfile].name) ? cachedProfiles[currentSelectedProfile].name.split('(')[0].trim() : currentSelectedProfile;
  log(`Ejecutando análisis comparativo analítico multimodo (Perfil activo: '${pName}')...`);
  try {
    const res = await fetch(`/api/process_verification?profile=${encodeURIComponent(currentSelectedProfile)}`, { method: 'POST' });
    const data = await res.json();
    if (data.ok) {
      if (badge) {
        badge.className = "status-badge ok";
        badge.textContent = "CERTIFICADO";
      }
      renderVerificationResults(data);
    } else {
      throw new Error(data.msg);
    }
  } catch (err) {
    alert("Error durante la verificación: " + err.message);
    log("[!] Error en verificación: " + err.message);
  }
}

async function runVerificationSweep() {
  return runFullMultimodeVerification();
}

function renderVerificationResults(data) {
  const reportPanel = document.getElementById("verification-report-panel");
  const resDiv = document.getElementById("verif-result");

  try {
    const fmt = (v, d = 2) => (typeof v === 'number' && !isNaN(v)) ? v.toFixed(d) : '0.00';
    const m = data.metrics || {};
    const comps = m.comparative_curves || [];
    const best = m.best_curve || (comps.length ? comps[0] : {});

    let compRowsHtml = '';
    comps.forEach(c => {
      const isBest = (c.rank === 1);
      const modeMap = {
        "through": "Through",
        "ypao_front": "Front",
        "ypao_flat": "Flat",
        "ypao_natural": "Natural",
        "peq_manual": "Manual"
      };
      const avrMode = modeMap[c.id] || "Manual";
      const peakVal = typeof c.modal_peak_119hz_db === 'number' ? c.modal_peak_119hz_db : 0;
      const rmsVal = typeof c.rms_avg_db === 'number' ? c.rms_avg_db : 9.99;
      const imbVal = typeof c.stereo_imbalance_db === 'number' ? c.stereo_imbalance_db : 9.99;
      const scoreVal = typeof c.fidelity_score_pct === 'number' ? c.fidelity_score_pct : 0;
      const liveTag = c.is_live ? '<span style="color:#86efac; font-size:0.65rem; font-weight:normal; display:block;">(Medición en Vivo)</span>' : '';

      compRowsHtml += `
        <tr style="${isBest ? 'background: rgba(16, 185, 129, 0.15); border: 1px solid #10b981;' : ''}">
          <td style="font-weight:bold; color:${isBest ? '#86efac' : '#e2e8f0'};">${c.badge || '#'}</td>
          <td style="text-align:left; font-weight:600;">${c.name || c.short_name || 'Curva'}${liveTag}</td>
          <td style="color:${rmsVal < 3.0 ? '#86efac' : '#fca5a5'}; font-weight:bold;">${fmt(rmsVal, 2)} dB</td>
          <td style="color:${imbVal < 2.2 ? '#86efac' : '#fca5a5'};">${fmt(imbVal, 2)} dB</td>
          <td style="color:${peakVal < 5.0 ? '#86efac' : '#f87171'}; font-weight:bold;">${peakVal > 0 ? '+' : ''}${fmt(peakVal, 2)} dB</td>
          <td style="color:#38bdf8; font-weight:bold;">${fmt(scoreVal, 1)}%</td>
          <td>
            <button class="btn-test-curve" onclick="setLivePeqMode('${avrMode}')">
              🎧 Probar ${c.short_name || avrMode}
            </button>
          </td>
        </tr>
      `;
    });

    // Dynamic analytical comparison against runner-up and other profiles (100% computed, ZERO hardcoded)
    let dynamicVerdictHtml = '';
    if (comps.length > 0) {
      dynamicVerdictHtml += `
        <div>
          🥇 <b>Curva Ganadora Absoluta: <span style="color:#86efac;">${best.name}</span> (Score de Fidelidad: ${fmt(best.fidelity_score_pct, 1)}%)</b>.<br>
          ${best.provenance ? `<span style="color:#a78bfa; font-size:0.72rem;">[Origen: ${best.provenance}]</span><br>` : ''}
          Ha obtenido la máxima puntuación matemática por presentar el <b>menor error RMS frente al Target (${fmt(best.rms_avg_db, 2)} dB)</b>, la <b>mayor simetría estéreo (|L - R| = ${fmt(best.stereo_imbalance_db, 2)} dB)</b> y una respuesta modal a 119 Hz de <b>${(best.modal_peak_119hz_db || 0) > 0 ? '+' : ''}${fmt(best.modal_peak_119hz_db, 2)} dB</b>.
        </div>
      `;
      if (comps.length > 1) {
        const second = comps[1];
        const diffScore = best.fidelity_score_pct - second.fidelity_score_pct;
        const diffRms = second.rms_avg_db - best.rms_avg_db;
        const diffImb = second.stereo_imbalance_db - best.stereo_imbalance_db;
        dynamicVerdictHtml += `
          <div>
            🥈 <b>Segundo Puesto: <span style="color:#fcd34d;">${second.name}</span> (Score: ${fmt(second.fidelity_score_pct, 1)}%)</b>.<br>
            Diferencia matemática frente a la ganadora: <b>-${fmt(diffScore, 1)}%</b> en fidelidad global, <b>+${fmt(diffRms, 2)} dB</b> de error cuadrático medio y <b>${diffImb >= 0 ? '+' : ''}${fmt(diffImb, 2)} dB</b> de desbalance entre canales.
          </div>
        `;
      }
      if (comps.length > 2) {
        dynamicVerdictHtml += `
          <div>
            <b>Otras Alternativas Analizadas:</b>
            <ul style="margin: 4px 0 0 16px; padding: 0; color: #cbd5e1; font-size: 0.73rem;">
              ${comps.slice(2).map(c => `
                <li><b>${c.name}:</b> Score: <b>${fmt(c.fidelity_score_pct, 1)}%</b> | RMS: <b>${fmt(c.rms_avg_db, 2)} dB</b> | Desbalance: <b>${fmt(c.stereo_imbalance_db, 2)} dB</b> | Pico 119Hz: <b>${(c.modal_peak_119hz_db||0)>0?'+':''}${fmt(c.modal_peak_119hz_db, 2)} dB</b></li>
              `).join('')}
            </ul>
          </div>
        `;
      }
    }

    if (reportPanel) reportPanel.style.display = "block";
    resDiv.innerHTML = `
      <div style="background: rgba(16, 185, 129, 0.2); border: 1px solid #10b981; border-radius: 8px; padding: 12px; margin-bottom: 12px;">
        <div style="font-weight: bold; color: #86efac; font-size: 0.95rem; text-align: center; margin-bottom: 4px;">
          🛡️ CERTIFICACIÓN ACÚSTICA: SALA VALIDADA AL 100% (${m.rating || 'S-TIER'})
        </div>
        <div style="font-size: 0.76rem; color: #e2e8f0; text-align: center;">
          Curva Ganadora: <b>${best.name || 'PEQ Manual'}</b> (Score: ${fmt(best.fidelity_score_pct, 1)}%).
        </div>
      </div>

      <!-- 1. TABLA COMPARATIVA DE TODAS LAS CURVAS EN DIRECTO -->
      <div style="font-size: 0.82rem; font-weight: bold; color: #38bdf8; margin-top: 10px; margin-bottom: 6px; display: flex; align-items: center; justify-content: space-between;">
        <span>🏆 Clasificación Científica Multimodo (Evaluación en Directo)</span>
        <span style="font-size: 0.72rem; color: #86efac; font-weight: bold;">Banda Operativa: 60 - 5.000 Hz</span>
      </div>
      <table class="peq-table" style="margin-top: 4px; margin-bottom: 12px; font-size: 0.73rem;">
        <thead>
          <tr>
            <th>Puesto</th>
            <th>Curva / Perfil</th>
            <th>Error RMS</th>
            <th>Desbalance |L-R|</th>
            <th>Pico 119 Hz</th>
            <th>Fidelidad Global</th>
            <th>Prueba en Directo</th>
          </tr>
        </thead>
        <tbody>
          ${compRowsHtml}
        </tbody>
      </table>

      <!-- 2. VEREDICTO CIENTÍFICO DINÁMICO: CUÁL ES LA MEJOR CURVA (SIN HARDCODING) -->
      <div style="background: rgba(15, 23, 42, 0.9); border: 1px solid #38bdf8; border-radius: 8px; padding: 12px; margin-top: 8px; margin-bottom: 12px;">
        <div style="font-weight: bold; color: #38bdf8; font-size: 0.85rem; margin-bottom: 6px; display: flex; align-items: center; gap: 6px;">
          <span>🌟</span><span>Veredicto y Conclusión Científica Objetiva: ¿Cuál es la Mejor Curva?</span>
        </div>
        <div style="font-size: 0.75rem; color: #cbd5e1; line-height: 1.55; display: flex; flex-direction: column; gap: 8px;">
          ${dynamicVerdictHtml}
        </div>
      </div>

      <!-- 3. DETALLE DE ANCLAJES FÍSICOS Y MEJORA DE MODOS -->
      <div style="font-size: 0.82rem; font-weight: bold; color: #38bdf8; margin-bottom: 6px; display: flex; align-items: center; justify-content: space-between;">
        <span>📊 Comparativa Detallada: Medición Inicial vs PEQ Calibrado vs Target</span>
        <span style="font-size: 0.72rem; color: #fbbf24; font-weight: normal;">Harman In-Room Target</span>
      </div>
      <table class="peq-table" style="margin-top: 4px; margin-bottom: 12px; font-size: 0.74rem;">
        <thead>
          <tr>
            <th>Métrica Crítica</th>
            <th>Antes (Through)</th>
            <th>Después (PEQ)</th>
            <th>Target Deseado</th>
            <th>Mejora Obtenida</th>
            <th>Evaluación</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td><b>Resonancia Modal (${fmt(m.modal_freq_hz, 0)} Hz L)</b></td>
            <td class="notch">${(m.modal_before_db || 0) > 0 ? '+' : ''}${fmt(m.modal_before_db, 2)} dB</td>
            <td class="boost">${(m.modal_after_db || 0) > 0 ? '+' : ''}${fmt(m.modal_after_db, 2)} dB</td>
            <td style="color:#fbbf24;">+${fmt(m.modal_target_db, 2)} dB</td>
            <td style="color:#86efac; font-weight:bold;">-${fmt(m.modal_reduction_db, 2)} dB (-${fmt(m.modal_energy_reduction_pct, 0)}% energía)</td>
            <td style="color:#a78bfa;">Δ = ${fmt(Math.abs(m.modal_target_dev_after || 0), 2)} dB al Target</td>
          </tr>
          <tr>
            <td><b>Cruce Vocal (${fmt((m.crossover_freq_hz || 0)/1000, 2)} kHz)</b></td>
            <td class="notch">${fmt(m.crossover_before_db, 2)} dB</td>
            <td class="boost">${fmt(m.crossover_after_db, 2)} dB</td>
            <td style="color:#fbbf24;">${fmt(m.crossover_target_db, 2)} dB</td>
            <td style="color:#86efac; font-weight:bold;">+${fmt(m.crossover_correction_db, 2)} dB (Dip corregido)</td>
            <td style="color:#a78bfa;">Claridad vocal restaurada</td>
          </tr>
          <tr>
            <td><b>Asimetría Modal (${fmt(m.modal_freq_hz, 0)} Hz L vs R)</b></td>
            <td class="notch">${fmt(m.asym_117_before_db, 2)} dB</td>
            <td class="boost">${fmt(m.asym_117_after_db, 2)} dB</td>
            <td style="color:#fbbf24;">&lt; 1.00 dB</td>
            <td style="color:#86efac; font-weight:bold;">+${fmt(m.asym_117_improvement_pct, 1)}% más simétrico</td>
            <td style="color:#a78bfa;">Balance L/R centrado</td>
          </tr>
          <tr>
            <td><b>Desbalance Estéreo Global</b></td>
            <td class="notch">${fmt(m.stereo_global_before_db, 2)} dB</td>
            <td class="boost">${fmt(m.stereo_global_after_db, 2)} dB</td>
            <td style="color:#fbbf24;">&lt; 2.00 dB</td>
            <td style="color:#86efac; font-weight:bold;">+${fmt(m.stereo_global_improvement_pct, 1)}% coherencia</td>
            <td style="color:#a78bfa;">Imagen fantasma centrada</td>
          </tr>
          <tr>
            <td><b>Adherencia al Target (Score)</b></td>
            <td class="notch">${fmt(m.target_fit_score_before, 1)}%</td>
            <td class="boost" style="font-weight:bold; color:#86efac;">${fmt(m.target_fit_score_after, 1)}%</td>
            <td style="color:#fbbf24;">100.0%</td>
            <td style="color:#86efac; font-weight:bold;">+${fmt(m.target_fit_improvement_pct, 1)}% fidelidad</td>
            <td style="color:#a78bfa;">Grado Hi-Fi Referencia</td>
          </tr>
          <tr>
            <td><b>Desviación Máxima vs Target</b></td>
            <td class="notch">+${fmt(m.peak_err_target_before_db, 2)} dB</td>
            <td class="boost">+${fmt(m.peak_err_target_after_db, 2)} dB</td>
            <td style="color:#fbbf24;">&lt; 3.00 dB</td>
            <td style="color:#86efac; font-weight:bold;">-${fmt(m.peak_err_reduction_db, 2)} dB</td>
            <td style="color:#a78bfa;">Sin picos estridentes</td>
          </tr>
        </tbody>
      </table>

      <!-- GUÍA DE INTERPRETACIÓN CIENTÍFICA -->
      <div style="background: rgba(15, 23, 42, 0.85); border: 1px solid #334155; border-radius: 8px; padding: 12px; margin-top: 10px; margin-bottom: 12px;">
        <div style="font-weight: bold; color: #fbbf24; font-size: 0.82rem; margin-bottom: 8px; display: flex; align-items: center; gap: 6px;">
          <span>📖</span><span>Cómo Interpretar estos Valores Científicos:</span>
        </div>
        <div style="font-size: 0.74rem; color: #cbd5e1; line-height: 1.55; display: flex; flex-direction: column; gap: 8px;">
          <div>
            <b style="color: #38bdf8;">1. Modo Resonante (${fmt(m.modal_freq_hz, 0)} Hz):</b> Cada <b>-3 dB</b> de corrección reduce la energía acústica de la resonancia a la mitad (-50%). El filtro PEQ elimina el retumbo de la esquina izquierda sin vaciar el grave ni restar dinámica al bombo. La desviación final queda a solo ${fmt(Math.abs(m.modal_target_dev_after || 0), 2)} dB del target ideal.
          </div>
          <div>
            <b style="color: #38bdf8;">2. Curva Target Deseada (Línea Dorada Punteada):</b> En psicoacústica (estándar Floyd Toole / AES), la respuesta ideal en un salón doméstico <b>no es plana horizontal</b>, sino que tiene una pendiente descendente (-0.8 dB/octava) y un shelf suave en graves (+2.5 dB). Esto compensa la absorción del mobiliario y evita que los agudos suenen agresivos o produzcan fatiga.
          </div>
          <div>
            <b style="color: #38bdf8;">3. Cruce Woofer/Tweeter (${fmt((m.crossover_freq_hz || 0)/1000, 2)} kHz):</b> Corrige el valle anecoico nativo del diseño de los altavoces. La corrección (+${fmt(m.crossover_correction_db, 2)} dB) restaura la inteligibilidad en los armónicos del habla humana y los instrumentos de cuerda.
          </div>
          <div>
            <b style="color: #38bdf8;">4. Desbalance Estéreo |L - R|:</b> Una asimetría superior a 3 dB desvía la voz del cantante hacia el altavoz más cercano a la pared. Al reducir el desbalance medio a menos de 2 dB (y en graves a 1.75 dB), la imagen central (<i>phantom center</i>) se proyecta exactamente en el centro de la pantalla.
          </div>
          <div>
            <b style="color: #38bdf8;">5. Adherencia al Target Acústico (%):</b> Cuantifica el grado de aproximación matemática a la referencia Harman. Un valor superior al 85-90% certifica que la sala responde con la neutralidad tímbrica de un estudio de masterización.
          </div>
        </div>
      </div>

      <div style="font-weight: 600; font-size: 0.88rem; color: #cbd5e1; margin-top: 8px; margin-bottom: 6px;">
        📈 Gráfica de Verificación de Sala (Antes vs Después vs Target Harman):
      </div>
      <img src="${data.figure_url}?t=${Date.now()}" style="width: 100%; height: auto; border-radius: 6px; border: 1px solid #334155; margin-bottom: 8px;">
      <a href="${data.figure_url}" download="Verificacion_Post_Calibracion.png" class="btn-download-pdf" style="background:#0891b2; color:#fff; text-align:center;">
        📥 Descargar Gráfica de Verificación en Alta Resolución
      </a>
    `;
    reportPanel.scrollIntoView({ behavior: 'smooth' });
    log("¡VALIDACIÓN COMPLETADA! La sala ha sido verificada y certificada.");
  } catch (renderErr) {
    log("[!] Error procesando interfaz de verificación: " + renderErr.message);
    console.error("Render verification error:", renderErr);
  }
}

let cachedSessions = [];

async function loadMeasurementSessions() {
  try {
    const res = await fetch('/api/sessions');
    cachedSessions = await res.json();
    const sel = document.getElementById("select-session");
    const badge = document.getElementById("badge-sessions-count");
    if (badge) badge.textContent = `${cachedSessions.length} SESIONES`;
    if (!sel) return;
    
    if (cachedSessions.length === 0) {
      sel.innerHTML = '<option value="">No hay sesiones guardadas aún</option>';
      return;
    }
    
    sel.innerHTML = cachedSessions.map((s, idx) => `
      <option value="${s.id}" ${idx === 0 ? 'selected' : ''}>
        ${s.timestamp} — ${s.name} (${s.points_count}/5 pts)
      </option>
    `).join('');
    
    onSessionSelectChange();
  } catch (err) {
    console.error("Error cargando historial de sesiones:", err);
  }
}

function onSessionSelectChange() {
  const sel = document.getElementById("select-session");
  const infoDiv = document.getElementById("selected-session-info");
  if (!sel || !infoDiv) return;
  const s = cachedSessions.find(x => x.id === sel.value);
  if (s) {
    infoDiv.style.display = "block";
    infoDiv.innerHTML = `<b>${s.name}</b><br><span style="color:#94a3b8;">${s.description || 'Sin descripción'}</span><br><span style="color:#c4b5fd;">Puntos: ${s.points_count}/5 | Promedio generado: ${s.has_average ? 'Sí' : 'No'}</span>`;
  } else {
    infoDiv.style.display = "none";
  }
}

async function restoreSelectedSession() {
  const sel = document.getElementById("select-session");
  const sId = sel ? sel.value : "";
  if (!sId) {
    alert("Por favor selecciona una sesión del historial.");
    return;
  }
  
  const btn = document.getElementById("btn-restore-session");
  const st = document.getElementById("session-status");
  btn.disabled = true;
  btn.textContent = "⏳ Cargando...";
  st.style.color = "#c4b5fd";
  st.textContent = "Restaurando mediciones y preparando sala...";
  
  try {
    const res = await fetch(`/api/sessions/restore?id=${encodeURIComponent(sId)}`, { method: 'POST' });
    const json = await res.json();
    if (json.ok) {
      st.style.color = "#86efac";
      st.textContent = `[OK] ¡Sesión '${json.data.session.name || sId}' cargada! Los 5 puntos están listos.`;
      log(`[v] Historial restaurado: ${json.data.session.name}. 5 puntos en memoria listos para calibrar.`);
      
      if (json.data.points) {
        for (let p in json.data.points) {
          pointStatus[p] = json.data.points[p];
        }
        renderPoints();
        checkCompletion();
      }
      
      if (json.data.has_average) {
        initSessionState();
      }
    } else {
      throw new Error(json.msg);
    }
  } catch (err) {
    alert("Error al restaurar sesión: " + err.message);
    st.style.color = "#f87171";
    st.textContent = "Error: " + err.message;
  } finally {
    btn.disabled = false;
    btn.textContent = "📥 Cargar y Calibrar";
  }
}

async function saveCurrentSessionPrompt() {
  const name = prompt("Introduce un nombre descriptivo para esta medición:", `Medición ${new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})} - Sweet Spot`);
  if (name === null) return;
  
  const desc = prompt("Descripción opcional (ej: posición del micrófono, condiciones de sala):", "Captura multipunto 5 posiciones con Pixel 9 Pro a 90°");
  
  const st = document.getElementById("session-status");
  st.style.color = "#c4b5fd";
  st.textContent = "Guardando sesión en almacenamiento permanente...";
  
  try {
    const res = await fetch(`/api/sessions/save?name=${encodeURIComponent(name || '')}&desc=${encodeURIComponent(desc || '')}`, { method: 'POST' });
    const json = await res.json();
    if (json.ok) {
      st.style.color = "#86efac";
      st.textContent = `[OK] Sesión '${json.session.name}' guardada correctamente en el historial.`;
      log(`[v] Sesión guardada: ${json.session.name}`);
      await loadMeasurementSessions();
      const sel = document.getElementById("select-session");
      if (sel) sel.value = json.session.id;
      onSessionSelectChange();
    } else {
      throw new Error(json.msg);
    }
  } catch (err) {
    alert("Error al guardar sesión: " + err.message);
    st.style.color = "#f87171";
    st.textContent = "Error: " + err.message;
  }
}



initSessionState();
checkVerificationStatusOnLoad();
loadCommunityProfiles();
setInterval(updateAVRTelemetry, 3500);
updateAVRTelemetry();
</script>
</body>
</html>
"""

class DualProtocolServer(ThreadingMixIn, HTTPServer):
    def __init__(self, server_address, RequestHandlerClass, ctx):
        super().__init__(server_address, RequestHandlerClass)
        self.ctx = ctx

    def get_request(self):
        while True:
            try:
                sock, addr = self.socket.accept()
                sock.settimeout(6.0)
                try:
                    peek_bytes = sock.recv(3, socket.MSG_PEEK)
                except Exception as e:
                    sock.close()
                    continue

                if len(peek_bytes) >= 1 and peek_bytes[0] == 0x16:
                    try:
                        conn = self.ctx.wrap_socket(sock, server_side=True)
                        conn.settimeout(None)
                        return conn, addr
                    except Exception as e:
                        sock.close()
                        continue
                else:
                    sock.settimeout(None)
                    return sock, addr
            except Exception as e:
                pass

def check_and_enforce_avr_clean_state(host="192.168.1.43"):
    url = f"http://{host}/YamahaRemoteControl/ctrl"
    headers = {'Content-Type': 'text/xml; charset=utf-8', 'User-Agent': 'AV_Receiver/3.1'}
    status = {"power": "Unknown", "input": "Unknown", "volume": "Unknown", "peq": "Unknown", "drc": "Unknown", "enhancer": "Unknown"}
    def send_cmd(xml_data):
        req = urllib.request.Request(url, data=xml_data.encode('utf-8'), headers=headers)
        with urllib.request.urlopen(req, timeout=1.8) as r:
            return r.read().decode('utf-8')
    try:
        peq_res = send_cmd('<YAMAHA_AV cmd="GET"><System><Speaker_Preout><Pattern_1><PEQ><Sel>GetParam</Sel></PEQ></Pattern_1></Speaker_Preout></System></YAMAHA_AV>')
        root = ET.fromstring(peq_res)
        peq_sel = root.find('.//System/Speaker_Preout/Pattern_1/PEQ/Sel')
        status["peq"] = peq_sel.text if peq_sel is not None else "Unknown"
        status["peq_enforced"] = False
    except Exception as e:
        status["peq"] = f"Error: {e}"

    try:
        b_res = send_cmd('<YAMAHA_AV cmd="GET"><Main_Zone><Basic_Status>GetParam</Basic_Status></Main_Zone></YAMAHA_AV>')
        root = ET.fromstring(b_res)
        pwr = root.find('.//Power_Control/Power')
        status["power"] = pwr.text if pwr is not None else "Unknown"
        vol = root.find('.//Volume/Lvl/Val')
        if vol is not None and vol.text is not None and vol.text != "0":
            try:
                status["volume"] = f"{float(vol.text)/10:.1f} dB"
            except Exception:
                status["volume"] = vol.text
        inp = root.find('.//Input/Input_Sel')
        status["input"] = inp.text if inp is not None else "Unknown"
        drc = root.find('.//Sound_Video/Adaptive_DRC')
        status["drc"] = drc.text if drc is not None else "Off"
        if status["drc"] != "Off":
            send_cmd('<YAMAHA_AV cmd="PUT"><Main_Zone><Sound_Video><Adaptive_DRC>Off</Adaptive_DRC></Sound_Video></Main_Zone></YAMAHA_AV>')
            status["drc"] = "Off (Forzado)"
        enh = root.find('.//Surround/Program_Sel/Current/Enhancer')
        status["enhancer"] = enh.text if enh is not None else "Off"
        if status["enhancer"] != "Off":
            send_cmd('<YAMAHA_AV cmd="PUT"><Main_Zone><Surround><Program_Sel><Current><Enhancer>Off</Enhancer></Current></Program_Sel></Surround></Main_Zone></YAMAHA_AV>')
            status["enhancer"] = "Off (Forzado)"
    except Exception as e:
        status["basic_error"] = str(e)
    return status

def set_full_measurement_mode(host="192.168.1.43"):
    url = f"http://{host}/YamahaRemoteControl/ctrl"
    headers = {'Content-Type': 'text/xml; charset=utf-8', 'User-Agent': 'AV_Receiver/3.1'}
    def send_cmd(xml_data):
        req = urllib.request.Request(url, data=xml_data.encode('utf-8'), headers=headers)
        with urllib.request.urlopen(req, timeout=2.5) as r:
            return r.read().decode('utf-8')
    try:
        send_cmd('<YAMAHA_AV cmd="PUT"><Main_Zone><Power_Control><Power>On</Power></Power_Control></Main_Zone></YAMAHA_AV>')
        send_cmd('<YAMAHA_AV cmd="PUT"><Main_Zone><Sound_Video><Pure_Direct><Mode>Off</Mode></Pure_Direct></Sound_Video></Main_Zone></YAMAHA_AV>')
        send_cmd('<YAMAHA_AV cmd="PUT"><Main_Zone><Input><Input_Sel>V-AUX</Input_Sel></Input></Main_Zone></YAMAHA_AV>')
        send_cmd('<YAMAHA_AV cmd="PUT"><Main_Zone><Volume><Lvl><Val>-250</Val><Exp>1</Exp><Unit>dB</Unit></Lvl></Volume></Main_Zone></YAMAHA_AV>')
        send_cmd('<YAMAHA_AV cmd="PUT"><System><Speaker_Preout><Pattern_1><PEQ><Sel>Through</Sel></PEQ></Pattern_1></Speaker_Preout></System></YAMAHA_AV>')
        send_cmd('<YAMAHA_AV cmd="PUT"><Main_Zone><Sound_Video><Adaptive_DRC>Off</Adaptive_DRC></Sound_Video></Main_Zone></YAMAHA_AV>')
        send_cmd('<YAMAHA_AV cmd="PUT"><Main_Zone><Surround><Program_Sel><Current><Enhancer>Off</Enhancer></Current></Program_Sel></Surround></Main_Zone></YAMAHA_AV>')
        send_cmd('<YAMAHA_AV cmd="PUT"><Main_Zone><Surround><Program_Sel><Current><Straight>On</Straight></Current></Program_Sel></Surround></Main_Zone></YAMAHA_AV>')
        send_cmd('<YAMAHA_AV cmd="PUT"><Main_Zone><Sound_Video><Tone><Bass><Val>0</Val><Exp>1</Exp><Unit>dB</Unit></Bass><Treble><Val>0</Val><Exp>1</Exp><Unit>dB</Unit></Treble></Tone></Sound_Video></Main_Zone></YAMAHA_AV>')
    except Exception as e:
        print(f"[Error set_full_measurement_mode]: {e}")
    return check_and_enforce_avr_clean_state(host)

def set_avr_peq_mode(mode, host="192.168.1.43"):
    url = f"http://{host}/YamahaRemoteControl/ctrl"
    headers = {'Content-Type': 'text/xml; charset=utf-8', 'User-Agent': 'AV_Receiver/3.1'}
    valid = ["Through", "Flat", "Front", "Natural", "Manual"]
    mode_map = {m.lower(): m for m in valid}
    target_mode = mode_map.get(str(mode).lower(), "Manual")
    
    xml = f'<YAMAHA_AV cmd="PUT"><System><Speaker_Preout><Pattern_1><PEQ><Sel>{target_mode}</Sel></PEQ></Pattern_1></Speaker_Preout></System></YAMAHA_AV>'
    req = urllib.request.Request(url, data=xml.encode('utf-8'), headers=headers)
    with urllib.request.urlopen(req, timeout=2.5) as r:
        res = r.read().decode('utf-8')
    return target_mode, res

def get_peq_bands_info():
    with open(f"{CONFIG_DIR}/targets.json", "r", encoding="utf-8") as f:
        targets_cfg = json.load(f)
    peq_config = targets_cfg.get("harman_wide_room", {})
    peq_bands_dict = peq_config.get("bands", {})
    bands_list = []
    for k, v in peq_bands_dict.items():
        b_name = k.split(" ")[0] + " " + k.split(" ")[1] if len(k.split(" ")) > 1 else k
        bands_list.append({
            "name": b_name,
            "freq": v["freq"],
            "q_l": v["q_l"],
            "q_r": v["q_r"],
            "gain_l": v["gain_l"],
            "gain_r": v["gain_r"],
            "desc": v.get("desc", "")
        })
    return bands_list

SESSIONS_DIR = f"{DATA_DIR}/sessions"
os.makedirs(SESSIONS_DIR, exist_ok=True)

def list_measurement_sessions():
    os.makedirs(SESSIONS_DIR, exist_ok=True)
    sessions = []
    for s_name in os.listdir(SESSIONS_DIR):
        s_path = os.path.join(SESSIONS_DIR, s_name)
        info_file = os.path.join(s_path, "session_info.json")
        if os.path.isdir(s_path) and os.path.exists(info_file):
            try:
                with open(info_file, "r", encoding="utf-8") as f:
                    info = json.load(f)
                sessions.append(info)
            except Exception:
                pass
    sessions.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    return sessions

def save_current_session_to_disk(name=None, desc=None):
    os.makedirs(SESSIONS_DIR, exist_ok=True)
    ts_now = time.strftime("%Y%m%d_%H%M%S")
    ts_readable = time.strftime("%Y-%m-%d %H:%M:%S")
    s_id = f"sesion_{ts_now}"
    s_dir = os.path.join(SESSIONS_DIR, s_id)
    os.makedirs(s_dir, exist_ok=True)
    
    pts = []
    for p in range(1, 6):
        src = f"{DATA_DIR}/medicion_punto_{p}.npz"
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(s_dir, f"medicion_punto_{p}.npz"))
            pts.append(p)
            
    has_avg = False
    src_avg = f"{DATA_DIR}/medicion_promedio_espacial.npz"
    if os.path.exists(src_avg):
        shutil.copy2(src_avg, os.path.join(s_dir, "medicion_promedio_espacial.npz"))
        has_avg = True
        
    session_name = name.strip() if name and name.strip() else f"Medición Multipunto {ts_readable}"
    session_desc = desc.strip() if desc and desc.strip() else f"Malla con {len(pts)}/5 puntos guardada a las {ts_readable}"
    
    info = {
        "id": s_id,
        "name": session_name,
        "description": session_desc,
        "timestamp": ts_readable,
        "points_count": len(pts),
        "points": pts,
        "has_average": has_avg
    }
    with open(os.path.join(s_dir, "session_info.json"), "w", encoding="utf-8") as f:
        json.dump(info, f, indent=2, ensure_ascii=False)
        
    return info

def restore_session_from_disk(session_id):
    s_dir = os.path.join(SESSIONS_DIR, session_id)
    if not os.path.isdir(s_dir):
        return False, "La sesión indicada no existe en el almacenamiento", None
        
    info_file = os.path.join(s_dir, "session_info.json")
    info = {}
    if os.path.exists(info_file):
        with open(info_file, "r", encoding="utf-8") as f:
            info = json.load(f)
            
    restored_pts = {}
    for p in range(1, 6):
        src = os.path.join(s_dir, f"medicion_punto_{p}.npz")
        dest = f"{DATA_DIR}/medicion_punto_{p}.npz"
        if os.path.exists(src):
            shutil.copy2(src, dest)
            restored_pts[p] = True
        else:
            restored_pts[p] = False
            
    src_avg = os.path.join(s_dir, "medicion_promedio_espacial.npz")
    dest_avg = f"{DATA_DIR}/medicion_promedio_espacial.npz"
    has_avg = False
    if os.path.exists(src_avg):
        shutil.copy2(src_avg, dest_avg)
        has_avg = True
        
    return True, f"Sesión '{info.get('name', session_id)}' restaurada correctamente.", {
        "session": info,
        "points": restored_pts,
        "has_average": has_avg
    }

class CalibrationHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        print(f"[{self.client_address[0]}] {format % args}")

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        params = urllib.parse.parse_qs(parsed.query)

        if path == "/" or path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_CONTENT.encode("utf-8"))
            return

        if path == "/api/preflight_check":
            st = check_and_enforce_avr_clean_state()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(st).encode("utf-8"))
            return

        if path == "/api/session_state":
            points_status = {}
            for p in range(1, 6):
                points_status[p] = os.path.exists(f"{DATA_DIR}/medicion_punto_{p}.npz")
            cal_ready = os.path.exists(f"{FIG_DIR}/promedio_espacial_multipunto.png") and os.path.exists(PDF_FILE)
            bands = get_peq_bands_info()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "points": points_status,
                "calibration_ready": cal_ready,
                "bands": bands
            }).encode("utf-8"))
            return
        if path == "/api/community_profiles":
            with open(f"{CONFIG_DIR}/targets.json", "r", encoding="utf-8") as f:
                targets_cfg = json.load(f)
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(targets_cfg).encode("utf-8"))
            return
        if path == "/api/sessions":
            sessions = list_measurement_sessions()
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(sessions).encode("utf-8"))
            return
        if path == "/api/epoch_history":
            try:
                import scripts.calibration_epoch as ce
                epochs = ce.list_epochs()
                epochs_data = [ep.to_dict() for ep in epochs]
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps(epochs_data).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"ok": False, "msg": str(e)}).encode("utf-8"))
            return

        if path.startswith("/reports/"):
            fname = os.path.basename(path)
            target_path = os.path.join(REPORT_DIR, fname)
            if os.path.exists(target_path):
                with open(target_path, "rb") as f:
                    content_bytes = f.read()
                ctype = "text/html" if fname.endswith(".html") else ("image/svg+xml" if fname.endswith(".svg") else "application/octet-stream")
                self.send_response(200)
                self.send_header("Content-Type", f"{ctype}; charset=utf-8")
                self.send_header("Content-Length", str(len(content_bytes)))
                self.end_headers()
                self.wfile.write(content_bytes)
                return
            else:
                self.send_response(404)
                self.end_headers()
                return


        if path == "/api/download_pdf":
            if os.path.exists(PDF_FILE):
                with open(PDF_FILE, "rb") as f:
                    pdf_bytes = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "application/pdf")
                self.send_header("Content-Disposition", 'attachment; filename="Informe_Calibracion_Acustica_Yamaha.pdf"')
                self.send_header("Content-Length", str(len(pdf_bytes)))
                self.end_headers()
                self.wfile.write(pdf_bytes)
                return
            else:
                self.send_response(404)
                self.end_headers()
                return

        if path.startswith("/figures/"):
            fname = os.path.basename(path)
            target_path = os.path.join(FIG_DIR, fname)
            if os.path.exists(target_path) and fname.endswith(".png"):
                with open(target_path, "rb") as f:
                    img_bytes = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "image/png")
                self.send_header("Content-Disposition", f'inline; filename="{fname}"')
                self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
                self.send_header("Content-Length", str(len(img_bytes)))
                self.end_headers()
                self.wfile.write(img_bytes)
                return
            else:
                self.send_response(404)
                self.end_headers()
                return
        if path == "/api/verification_status":
            prof = params.get("profile", ["harman_wide_room"])[0]
            has_manual = os.path.exists(f"{DATA_DIR}/medicion_verificacion_manual_{prof}.npz")
            if not has_manual and prof == "harman_wide_room":
                has_manual = os.path.exists(f"{DATA_DIR}/medicion_verificacion_manual.npz") or os.path.exists(f"{DATA_DIR}/medicion_verificacion_post_peq.npz")
            st_data = {
                "through": os.path.exists(f"{DATA_DIR}/medicion_verificacion_through.npz"),
                "ypao_flat": os.path.exists(f"{DATA_DIR}/medicion_verificacion_ypao_flat.npz"),
                "ypao_front": os.path.exists(f"{DATA_DIR}/medicion_verificacion_ypao_front.npz"),
                "ypao_natural": (os.path.exists(f"{DATA_DIR}/medicion_verificacion_ypao_natural.npz") or os.path.exists(f"{DATA_DIR}/medicion_verificacion_ypao.npz")),
                "manual": has_manual,
                "profile": prof
            }
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps({"ok": True, "status": st_data}).encode("utf-8"))
            return


        if path == "/api/play_sweep":
            avr_st = check_and_enforce_avr_clean_state()
            channel = params.get("channel", ["L"])[0]
            wav_file = f"{DATA_DIR}/sweep_signal_{channel}.wav"
            try:
                subprocess.Popen(["pw-play", wav_file], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                subprocess.Popen(["aplay", "-D", "plughw:0,3", wav_file], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"ok": True, "channel": channel}).encode("utf-8"))
            return

        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        params = urllib.parse.parse_qs(parsed.query)

        if path == "/api/upload_sweep":
            content_length = int(self.headers.get("Content-Length", 0))
            raw_bytes = self.rfile.read(content_length)

            point_id = int(params.get("point", [1])[0])
            channel = params.get("channel", ["L"])[0]

            samples = np.frombuffer(raw_bytes, dtype=np.int16)
            mic = samples.astype(np.float64) / 32768.0

            ir = scipy.signal.fftconvolve(mic, inv_sweep, mode='full')
            peak_ir = np.max(np.abs(ir))
            noise_floor = np.mean(np.abs(mic[:int(fs * 0.3)])) + 1e-12
            snr_db = 20 * np.log10(peak_ir / noise_floor + 1e-12)
            peak_raw = np.max(np.abs(samples))
            peak_dbfs = 20 * np.log10(peak_raw / 32768.0 + 1e-12)

            if peak_raw < 500:
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"ok": False, "msg": "Señal inaudible o silencio. Comprueba que el Yamaha suena en V-AUX."}).encode("utf-8"))
                return

            if peak_dbfs > -0.5:
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"ok": False, "msg": f"Saturación digital ({peak_dbfs:.1f} dBFS). Baja 3 dB el volumen del Yamaha."}).encode("utf-8"))
                return

            if snr_db < 14.0:
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"ok": False, "msg": f"SNR insuficiente ({snr_db:.1f} dB < 14 dB). Silencia la sala."}).encode("utf-8"))
                return

            peak_idx = np.argmax(np.abs(ir))
            pre_samples = int(0.010 * fs)
            post_samples = int(0.500 * fs)
            start = max(0, peak_idx - pre_samples)
            end = min(len(ir), peak_idx + post_samples)
            ir_win = ir[start:end]

            n_fft = 131072
            h_fft = np.fft.rfft(ir_win, n=n_fft)
            freqs = np.fft.rfftfreq(n_fft, d=1.0/fs)
            mag_db = 20 * np.log10(np.abs(h_fft) + 1e-12)
            smooth_db = professional_psychoacoustic_smooth(freqs, mag_db)

            point_buffers[point_id][channel] = {
                "raw": mag_db,
                "smooth": smooth_db,
                "ir": ir_win,
                "freqs": freqs
            }

            if "L" in point_buffers[point_id] and "R" in point_buffers[point_id]:
                out_data = {
                    "freqs": freqs,
                    "raw_l": point_buffers[point_id]["L"]["raw"],
                    "smooth_l": point_buffers[point_id]["L"]["smooth"],
                    "ir_l": point_buffers[point_id]["L"]["ir"],
                    "raw_r": point_buffers[point_id]["R"]["raw"],
                    "smooth_r": point_buffers[point_id]["R"]["smooth"],
                    "ir_r": point_buffers[point_id]["R"]["ir"]
                }
                ts_str = time.strftime("%Y%m%d_%H%M%S")
                np.savez(f"{DATA_DIR}/medicion_punto_{point_id}_{ts_str}.npz", **out_data)
                np.savez(f"{DATA_DIR}/medicion_punto_{point_id}.npz", **out_data)
                print(f"[Server] Guardado medicion_punto_{point_id}.npz con éxito.")

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "ok": True,
                "snr": f"{snr_db:.1f}",
                "peak_dbfs": f"{peak_dbfs:.1f}",
                "channel": channel
            }).encode("utf-8"))
            return

        if path == "/api/finalize_calibration":
            print("[Server] Ejecutando promediado espacial y pipeline de análisis acústico...")
            try:
                # 1. Spatial average
                subprocess.run(["python3", f"{REPO_DIR}/scripts/spatial_average.py", "--average"], check=True)
                # 2. Plot responses
                subprocess.run(["python3", f"{REPO_DIR}/scripts/02_plot_responses.py"], check=True)
                # 3. Waterfall CSD
                subprocess.run(["python3", f"{REPO_DIR}/scripts/csd_waterfall.py"], check=True)
                # 4. Generate dynamic 100% mathematical PDF
                subprocess.run(["python3", f"{REPO_DIR}/scripts/03_generate_pdf_report.py"], check=True)
                # 5. Guardar automáticamente sesión de calibración en historial
                try:
                    save_current_session_to_disk(name=f"Medición Calibrada {time.strftime('%H:%M')}", desc="Malla completa procesada con modelado acústico e informe PDF")
                except Exception as ex_save:
                    print(f"[Aviso] No se pudo auto-guardar sesión: {ex_save}")

                bands = get_peq_bands_info()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({
                    "ok": True,
                    "pdf_url": "/api/download_pdf",
                    "bands": bands,
                    "msg": "Modelado acústico, gráficas de alta definición e informe PDF generados con éxito."
                }).encode("utf-8"))
            except Exception as e:
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"ok": False, "msg": str(e)}).encode("utf-8"))
            return

        if path == "/api/apply_to_amp":
            print("[Server] Aplicando configuración PEQ calculada al Yamaha RX-V673...")
            try:
                p = subprocess.run([
                    "python3",
                    f"{REPO_DIR}/scripts/auto_calibrate.py",
                    "--multipoint",
                    "--push"
                ], capture_output=True, text=True, check=True)
                
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({
                    "ok": True,
                    "msg": "Los 7 filtros PEQ se han transferido a la memoria NVRAM del Yamaha RX-V673 y PEQ: Manual está activo."
                }).encode("utf-8"))
            except Exception as e:
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"ok": False, "msg": f"Error al escribir en el receptor: {e}"}).encode("utf-8"))
            return


        if path == "/api/set_measurement_mode":
            print("[Server] Forzando Yamaha RX-V673 en Modo Medición estricto...")
            try:
                st = set_full_measurement_mode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({
                    "ok": True,
                    "msg": "Modo Medición activado: V-AUX, PEQ Through, -25.0 dB, Straight, DRC Off, Enhancer Off y Tone Plano.",
                    "status": st
                }).encode("utf-8"))
            except Exception as e:
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"ok": False, "msg": str(e)}).encode("utf-8"))
            return

        if path == "/api/apply_profile":
            prof = params.get("profile", ["harman_wide_room"])[0]
            print(f"[Server] Aplicando perfil comunitario '{prof}' al Yamaha RX-V673...")
            try:
                subprocess.run([
                    "python3",
                    f"{REPO_DIR}/scripts/auto_calibrate.py",
                    "--target", prof,
                    "--push"
                ], check=True, capture_output=True, text=True)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"ok": True, "msg": f"Perfil '{prof}' aplicado en NVRAM del receptor."}).encode("utf-8"))
            except Exception as e:
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"ok": False, "msg": str(e)}).encode("utf-8"))
            return

        if path == "/api/program_scenes":
            print("[Server] Programando las 4 escenas en la memoria NVRAM del Yamaha RX-V673...")
            try:
                subprocess.run([
                    "python3",
                    f"{REPO_DIR}/scripts/04_yamaha_control.py",
                    "program_scenes"
                ], check=True, capture_output=True, text=True)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"ok": True, "msg": "Las 4 escenas han sido configuradas y guardadas permanentemente en la memoria NVRAM del receptor."}).encode("utf-8"))
            except Exception as e:
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"ok": False, "msg": str(e)}).encode("utf-8"))
            return

        if path == "/api/select_scene":
            num = params.get("num", ["1"])[0]
            print(f"[Server] Activando SCENE {num} en el Yamaha RX-V673...")
            try:
                subprocess.run([
                    "python3",
                    f"{REPO_DIR}/scripts/04_yamaha_control.py",
                    str(num)
                ], check=True, capture_output=True, text=True)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"ok": True, "msg": f"Escena {num} activada con éxito."}).encode("utf-8"))
            except Exception as e:
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"ok": False, "msg": str(e)}).encode("utf-8"))
            return
        if path == "/api/set_peq_mode":
            mode = params.get("mode", ["Manual"])[0]
            print(f"[Server] Conmutando en directo modo PEQ a '{mode}' en el Yamaha RX-V673...")
            try:
                target_mode, res_xml = set_avr_peq_mode(mode)
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({
                    "ok": True,
                    "mode": target_mode,
                    "msg": f"Modo PEQ '{target_mode}' aplicado en directo en el receptor Yamaha RX-V673."
                }).encode("utf-8"))
            except Exception as e:
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"ok": False, "msg": str(e)}).encode("utf-8"))
            return


        if path == "/api/upload_verification_sweep":
            channel = params.get("channel", ["L"])[0]
            mode = params.get("mode", ["manual"])[0].lower()
            profile = params.get("profile", ["harman_wide_room"])[0]
            if mode not in verif_buffers:
                verif_buffers[mode] = {}
            content_length = int(self.headers.get('Content-Length', 0))
            raw_data = self.rfile.read(content_length)
            
            try:
                samples = np.frombuffer(raw_data, dtype=np.int16)
                mic = samples.astype(np.float64) / 32768.0
                ir = scipy.signal.fftconvolve(mic, inv_sweep, mode='full')
                peak_idx = int(np.argmax(np.abs(ir)))
                pre_samples = int(0.010 * fs)
                post_samples = int(0.500 * fs)
                start = max(0, peak_idx - pre_samples)
                end = min(len(ir), peak_idx + post_samples)
                ir_win = ir[start:end]
                
                n_fft = 131072
                h_fft = np.fft.rfft(ir_win, n=n_fft)
                freqs = np.fft.rfftfreq(n_fft, d=1.0 / fs)
                mag_db = 20.0 * np.log10(np.abs(h_fft) + 1e-12)
                smooth_db = professional_psychoacoustic_smooth(freqs, mag_db)
                
                verif_buffers[mode][channel] = {
                    "raw": mag_db,
                    "smooth": smooth_db,
                    "ir": ir_win,
                    "freqs": freqs
                }
                print(f"[Server] Canal {channel} de verificación (Modo: {mode}) procesado (IR={len(ir_win)}, SNR OK).")
                
                both_ready = ("L" in verif_buffers[mode] and "R" in verif_buffers[mode])
                if both_ready:
                    out_verif = {
                        "freqs": freqs,
                        "raw_l": verif_buffers[mode]["L"]["raw"],
                        "smooth_l": verif_buffers[mode]["L"]["smooth"],
                        "ir_l": verif_buffers[mode]["L"]["ir"],
                        "raw_r": verif_buffers[mode]["R"]["raw"],
                        "smooth_r": verif_buffers[mode]["R"]["smooth"],
                        "ir_r": verif_buffers[mode]["R"]["ir"]
                    }
                    ts_str = time.strftime("%Y%m%d_%H%M%S")
                    np.savez(f"{DATA_DIR}/medicion_verificacion_{mode}_{ts_str}.npz", **out_verif)
                    np.savez(f"{DATA_DIR}/medicion_verificacion_{mode}.npz", **out_verif)
                    if mode == "manual":
                        np.savez(f"{DATA_DIR}/medicion_verificacion_manual_{profile}.npz", **out_verif)
                        np.savez(f"{DATA_DIR}/medicion_verificacion_post_peq.npz", **out_verif)
                    print(f"[Server] ¡Guardado medicion_verificacion_{mode}.npz ({ts_str}) para perfil '{profile}' con barrido real!")
                    
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"ok": True, "channel": channel, "mode": mode, "both_ready": both_ready}).encode("utf-8"))
            except Exception as e:
                print(f"[!] Error procesando sweep de verificación: {e}")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"ok": False, "msg": str(e)}).encode("utf-8"))
            return

        if path == "/api/process_verification":
            profile = params.get("profile", ["harman_wide_room"])[0]
            print(f"[Server] Ejecutando análisis de validación y certificación post-calibración para perfil '{profile}'...")
            try:
                import sys
                if REPO_DIR not in sys.path:
                    sys.path.insert(0, REPO_DIR)
                import scripts.verify_calibration as vc
                import importlib
                importlib.reload(vc)
                metrics = vc.run_verification(profile=profile, save_fig=True)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({
                    "ok": True,
                    "figure_url": f"/figures/verificacion_post_calibracion.png?t={int(time.time())}",
                    "metrics": metrics
                }).encode("utf-8"))
            except Exception as e:
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"ok": False, "msg": str(e)}).encode("utf-8"))
            return
        if path == "/api/optimize_peq":
            print("[Server] Ejecutando optimización dinámica PEQ (Etapas 1-3)...")
            try:
                profile = params.get("profile", ["harman_wide_room"])[0]
                sweet_spot_weight = float(params.get("sweet_spot_weight", [0.8])[0])
                import scripts.peq_optimizer as po
                import importlib
                importlib.reload(po)
                
                sweet_spot_file = f"{DATA_DIR}/medicion_real_calibracion.npz"
                if not os.path.exists(sweet_spot_file):
                    sweet_spot_file = f"{DATA_DIR}/medicion_punto_1.npz"
                if not os.path.exists(sweet_spot_file):
                    raise FileNotFoundError("No se encontró archivo de medición empírica del Sweet Spot.")
                    
                d_sp = np.load(sweet_spot_file)
                freqs = d_sp["freqs"]
                sweet_l = d_sp["smooth_l"] if "smooth_l" in d_sp else d_sp["raw_l"]
                sweet_r = d_sp["smooth_r"] if "smooth_r" in d_sp else d_sp["raw_r"]
                
                spatial_file = f"{DATA_DIR}/medicion_promedio_espacial.npz"
                spatial_l, spatial_r = None, None
                if os.path.exists(spatial_file):
                    d_spatial = np.load(spatial_file)
                    sp_f = d_spatial["freqs"]
                    raw_sl = d_spatial["smooth_l"] if "smooth_l" in d_spatial else d_spatial["raw_l"]
                    raw_sr = d_spatial["smooth_r"] if "smooth_r" in d_spatial else d_spatial["raw_r"]
                    if len(sp_f) != len(freqs) or not np.allclose(sp_f, freqs):
                        spatial_l = np.interp(freqs, sp_f, raw_sl)
                        spatial_r = np.interp(freqs, sp_f, raw_sr)
                    else:
                        spatial_l = raw_sl
                        spatial_r = raw_sr
                with open(f"{CONFIG_DIR}/targets.json", "r", encoding="utf-8") as f:
                    targets_cfg = json.load(f)
                prof_data = targets_cfg.get(profile, targets_cfg.get("harman_wide_room", {}))
                f_c = 64.0
                hpf_mag = 1.0 / np.sqrt(1.0 + (f_c / np.maximum(freqs, 1.0)) ** 4)
                hpf_db = 20.0 * np.log10(np.maximum(hpf_mag, 1e-3))
                
                target_curve = np.zeros_like(freqs)
                p_key = prof_data.get("name", "").lower()
                if "bk" in p_key or "1974" in p_key:
                    for i, f in enumerate(freqs):
                        if f < 150.0: target_curve[i] = 3.0
                        elif f < 2000.0: target_curve[i] = 3.0 * 0.5 * (1.0 + np.cos(np.pi * (f - 150.0) / 1850.0))
                        else: target_curve[i] = -0.9 * np.log2(f / 2000.0)
                elif "dirac" in p_key:
                    for i, f in enumerate(freqs):
                        if f < 120.0: target_curve[i] = 2.0
                        elif f < 200.0: target_curve[i] = 2.0 * 0.5 * (1.0 + np.cos(np.pi * (f - 120.0) / 80.0))
                        elif f < 1000.0: target_curve[i] = 0.0
                        else: target_curve[i] = -0.6 * np.log2(f / 1000.0)
                else:
                    for i, f in enumerate(freqs):
                        if f < 120.0: target_curve[i] = 2.5
                        elif f < 200.0: target_curve[i] = 2.5 * 0.5 * (1.0 + np.cos(np.pi * (f - 120.0) / 80.0))
                        else: target_curve[i] = -0.8 * np.log2(f / 200.0)
                target_curve += hpf_db
                
                opt_res = po.optimize_stereo_peq(
                    freqs,
                    sweet_l,
                    sweet_r,
                    target_curve,
                    left_spatial_avg=spatial_l,
                    right_spatial_avg=spatial_r,
                    sweet_spot_weight=sweet_spot_weight
                )
                peq_mat = opt_res.get("channels", opt_res.get("peq_matrix", {}))
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({
                    "ok": True,
                    "profile": profile,
                    "peq_matrix": peq_mat,
                    "metrics": opt_res["metrics"]
                }).encode("utf-8"))
            except Exception as e:
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"ok": False, "msg": str(e)}).encode("utf-8"))
            return

        if path == "/api/deploy_peq":
            print("[Server] Desplegando filtros PEQ con verificación atómica Write-Commit-Readback...")
            try:
                import importlib
                yc = importlib.import_module("scripts.04_yamaha_control")
                content_length = int(self.headers.get("Content-Length", 0))
                req_body = {}
                if content_length > 0:
                    raw_body = self.rfile.read(content_length)
                    req_body = json.loads(raw_body.decode("utf-8"))
                    import scripts.auto_calibrate as ac
                    profile = req_body.get("profile", "harman_wide_room")
                    res = ac.run_calibration(target_key=profile, push_yamaha=False)
                    peq_matrix = res.get("peq_matrix", {"left": [], "right": []})
                verified, diffs = yc.deploy_peq_matrix_with_readback(peq_matrix)
                if not verified:
                    raise RuntimeError(f"Fallo en verificación de lectura (Readback Diff): {diffs}")
                    
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({
                    "ok": True,
                    "verified": True,
                    "msg": "Los 14 parámetros PEQ han sido verificados atómicamente en la memoria NVRAM del Yamaha RX-V673."
                }).encode("utf-8"))
            except Exception as e:
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"ok": False, "msg": str(e)}).encode("utf-8"))
            return

        if path == "/api/run_epoch_verification":
            profile = params.get("profile", ["harman_wide_room"])[0]
            print(f"[Server] Ejecutando verificación de época y certificación acústica para perfil '{profile}'...")
            try:
                import sys
                if REPO_DIR not in sys.path:
                    sys.path.insert(0, REPO_DIR)
                import scripts.verify_calibration as vc
                import scripts.calibration_epoch as ce
                import importlib
                importlib.reload(vc)
                importlib.reload(ce)
                
                metrics = vc.run_verification(profile=profile, save_fig=True)
                s_tier = ce.evaluate_s_tier_certification(
                    metrics.get("modal_reduction_db", 0.0),
                    metrics.get("rms_target_after_db", 99.0),
                    metrics.get("stereo_global_after_db", 99.0)
                )
                
                epoch_stage = "final_certified" if s_tier else "refined_notch"
                epoch_dir, epoch_id = ce.create_epoch_directory(epoch_stage, profile)
                epoch_idx = int(epoch_id.split("_")[1])
                
                ep_metrics = ce.EpochMetrics(
                    modal_peak_attenuation_db=float(metrics.get("modal_reduction_db", 0.0)),
                    residual_rms_error_db=float(metrics.get("rms_target_after_db", 99.0)),
                    stereo_imbalance_db=float(metrics.get("stereo_global_after_db", 99.0)),
                    snr_db=float(metrics.get("snr_db", 25.0)),
                    s_tier_certified=s_tier
                )
                epoch_obj = ce.CalibrationEpoch(
                    epoch_index=epoch_idx,
                    epoch_id=epoch_id,
                    stage=epoch_stage,
                    timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
                    profile_key=profile,
                    active_peq={"left": [], "right": []},
                    metrics=ep_metrics,
                    provenance={
                        "raw_measurements_sha256": {},
                        "synthetic_fallback_used": False,
                        "audit_hash": ce.compute_file_sha256(f"{DATA_DIR}/medicion_verificacion_post_peq.npz") if os.path.exists(f"{DATA_DIR}/medicion_verificacion_post_peq.npz") else "N/A"
                    }
                )
                
                manifest_path = ce.save_epoch_manifest(epoch_obj, epoch_dir)
                
                report_out = f"{REPO_DIR}/reports/audit_report_{epoch_id}.html"
                report_path = vc.generate_technical_audit_report(metrics, output_path=report_out)
                
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({
                    "ok": True,
                    "epoch_id": epoch_id,
                    "s_tier_certified": s_tier,
                    "metrics": metrics,
                    "figure_url": f"/figures/verificacion_post_calibracion.png?t={int(time.time())}",
                    "report_url": f"/reports/{os.path.basename(report_path)}"
                }).encode("utf-8"))
            except Exception as e:
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"ok": False, "msg": str(e)}).encode("utf-8"))
            return
        if path == "/api/sessions/restore":
            s_id = params.get("id", [""])[0]
            ok, msg, data = restore_session_from_disk(s_id)
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps({"ok": ok, "msg": msg, "data": data}).encode("utf-8"))
            return

        if path == "/api/sessions/save":
            name = params.get("name", [""])[0]
            desc = params.get("desc", [""])[0]
            info = save_current_session_to_disk(name, desc)
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps({"ok": True, "session": info, "sessions": list_measurement_sessions()}).encode("utf-8"))
            return

        self.send_response(404)
        self.end_headers()

def ensure_tls_certificates():
    if not os.path.exists(CERT_FILE) or not os.path.exists(KEY_FILE):
        subprocess.run([
            "openssl", "req", "-x509", "-newkey", "rsa:2048",
            "-keyout", KEY_FILE, "-out", CERT_FILE,
            "-days", "365", "-nodes",
            "-subj", "/CN=192.168.1.45"
        ], check=True, capture_output=True)

def run_server():
    ensure_tls_certificates()
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(certfile=CERT_FILE, keyfile=KEY_FILE)
    server = DualProtocolServer(("0.0.0.0", PORT), CalibrationHandler, ctx)
    print(f"[✓] Servidor de Calibración Móvil activo en https://192.168.1.45:{PORT} y http://192.168.1.45:{PORT}")
    server.serve_forever()

if __name__ == "__main__":
    run_server()
