# Guía Técnica de Equipamiento y Procesamiento

Este documento recopila las especificaciones de ingeniería de los componentes actuales del sistema, el análisis del hardware de audio y la justificación de los ajustes configurados.

---

## 1. Receptor Audiovisual: Yamaha RX-V673

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           YAMAHA RX-V673 (ARQUITECTURA)                     │
│  • Etapa de Potencia: Discreta de alta corriente (90 W/canal @ 8 Ω, 0.09%)  │
│  • DAC Interno: Burr-Brown PCM1681 (192 kHz / 24-bit, 105 dB SNR)           │
│  • Motor DSP: Cinema DSP 3D con Virtual Presence Speaker (VPS)              │
│  • Ecualizador: PEQ Paramétrico 7 bandas IIR Biquad por canal               │
│  • Interfaz de Red: Protocolo YNC (XML over HTTP en puerto 80)              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### A. Gestión de Impedancia: ¿Por qué 8 $\Omega$ MIN y no 6 $\Omega$?
En el menú avanzado (`ADVANCED SETUP` $\rightarrow$ `SP IMP.`), Yamaha permite seleccionar entre `8 \Omega MIN` y `6 \Omega MIN`.
* **Explicación Técnica**: El ajuste de 6 $\Omega$ no añade capacidad de corriente; activa un limitador de tensión en el secundario del transformador para superar homologaciones térmicas en laboratorio.
* **Impacto en el Audio**: Limitar la tensión recorta el *headroom* dinámico en los picos transitorios de música y cine.
* **Configuración Aplicada**: Se mantiene en **`8 \Omega MIN`** para que los transistores entreguen toda la dinámica a los altavoces de 6 $\Omega$, asegurando al menos 10 cm de ventilación sobre el chasis.

### B. Motor Cinema DSP 3D y Virtual Presence Speaker (VPS)
* El procesador Yamaha RX-V673 incluye algoritmos propietarios de función de transferencia relacionada con la cabeza (HRTF).
* Con `Cinema DSP 3D Mode: Auto` activo, al detectar que no hay altavoces de presencia físicos conectados en la pared, el receptor **habilita automáticamente el Virtual Presence Speaker (VPS)**, proyectando las fuentes sonoras hacia la altura del panel LG C5 OLED.

---

## 2. Altavoces de Estantería: Q Acoustics 3020i

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Q ACOUSTICS 3020i (ESPECIFICACIONES)                │
│  • Configuración: 2 vías Bass-Reflex con puerto trasero afinado             │
│  • Woofer: 125 mm (5 pulgadas) de papel recubierto con suspensión de goma   │
│  • Tweeter: 22 mm cúpula suave desacoplada del deflector frontal            │
│  • Frecuencia de Cruce (Crossover): 2.4 kHz (Filtro divisor orden acústico)  │
│  • Respuesta Anecoica: 64 Hz – 30 kHz (-3 dB)                               │
│  • Sensibilidad / Impedancia: 88 dB/W/m · 6 Ω nominal (mínimo 4.0 Ω)        │
│  • Construcción: Refuerzos internos punto a punto (P2P Bracing)             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Compensación de Cruce en PEQ:
* En la zona de cruce anecoico (~2.4 kHz – 2.5 kHz), existe una ligera pérdida de energía por la directividad fuera de eje del cono de 5 pulgadas.
* El filtro de **`Band 6: 2.52 kHz (+1.5 dB, Q=1.260)`** en el ecualizador compensa este escalón, solidificando la presencia vocal.

---

## 3. Pantalla: LG C5 OLED

* **Conexión**: HDMI 2 (eARC/ARC) $\rightarrow$ HDMI OUT (ARC) del Yamaha.
* **Ajustes Óptimos en webOS**:
  * *Salida de sonido*: **Dispositivo HDMI(ARC)**.
  * *Salida de sonido digital*: **Paso a través (Pass Through)** (evita remuestreos y latencia).
  * *Formato de entrada HDMI*: **Bitstream**.
  * *Compatibilidad eARC*: Desactivar si se experimentan cortes con HDMI 1.4 legado.
