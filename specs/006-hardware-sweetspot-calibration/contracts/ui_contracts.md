# UI Contracts: Tight Sweet-Spot & Hardware Profile Calibration

**Feature**: `006-hardware-sweetspot-calibration`
**Date**: 2026-09-04

---

## 1. Hardware Configuration Panel (`#hardware-config-panel`)

Compact selector panel positioned at the top of the calibration suite.

```html
<div class="card" id="hardware-config-panel" style="border-color:#38bdf8; background:rgba(56, 189, 248, 0.05); margin-bottom:14px;">
  <div class="card-title" style="color:#38bdf8; display:flex; justify-content:space-between; align-items:center;">
    <span>Configuración de Hardware & Cadena Electroacústica (2026 Pro)</span>
    <span class="status-badge ok" id="hardware-status-badge">ACTIVO</span>
  </div>
  <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(240px, 1fr)); gap:12px; margin-top:10px;">
    <!-- Selector de Micrófono -->
    <div>
      <label style="font-size:0.75rem; color:#94a3b8; font-weight:bold;">MICRÓFONO DE MEDICIÓN (90° VERTICAL)</label>
      <select id="select-mic" class="input-select" onchange="onHardwareChange()">
        <option value="pixel_9_pro_calibrated">Google Pixel 9 Pro (Tethered Acoustic)</option>
        <option value="minidsp_umik1">miniDSP UMIK-1 (USB Calibrado 90°)</option>
        <option value="dayton_umm6">Dayton Audio UMM-6 (USB Calibrado 90°)</option>
        <option value="generic_flat">Micrófono Genérico Plano</option>
      </select>
    </div>
    <!-- Selector de Amplificador -->
    <div>
      <label style="font-size:0.75rem; color:#94a3b8; font-weight:bold;">AMPLIFICADOR / RECEPTOR AV</label>
      <select id="select-amp" class="input-select" onchange="onHardwareChange()">
        <option value="yamaha_rx_v673">Yamaha RX-V673 (7 Bandas PEQ / YNC LAN)</option>
        <option value="generic_avr">Receptor AV Genérico (Exportación Manual)</option>
      </select>
    </div>
    <!-- Selector de Altavoces -->
    <div>
      <label style="font-size:0.75rem; color:#94a3b8; font-weight:bold;">ALTAVOCES PRINCIPALES (FRONT L / R)</label>
      <select id="select-speakers" class="input-select" onchange="onHardwareChange()">
        <option value="q_acoustics_3020i">Q Acoustics 3020i (F3: 64Hz, Dip Crossover: 2.52kHz)</option>
        <option value="generic_bookshelf">Altavoces de Estantería Genéricos (F3: 80Hz)</option>
        <option value="generic_tower">Altavoces de Columna / Torre (F3: 40Hz)</option>
      </select>
    </div>
  </div>
</div>
```

---

## 2. Tight Sweet-Spot Visual Calibration Guide

Rendered in the measurement pre-flight section, instructing the user on the 5-point tight sphere:

```text
       [ Punto 5: +15 cm Arriba (Cenital) ]
                         |
  [ Punto 2: -15 cm Izq ] -- [ Punto 1: SWEET SPOT (MLP) ] -- [ Punto 3: +15 cm Der ]
                         |
      [ Punto 4: +15 cm Delante (Hacia TV) ]

  * Nota: Micrófono OBLIGATORIO orientado a 90° apuntando verticalmente al techo.
  * Ponderación: 70% Punto 1 / 30% Promedio de Puntos 2, 3, 4 y 5.
```

---

## 3. Side-by-Side Modal Symmetry Diagnostics Card (`#modal-symmetry-card`)

Displays Front L vs Front R detected resonance peaks, active notch filters, and diagnostic reasoning for each band.
