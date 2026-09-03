# Control Total del Sistema y Calibración en Home Assistant

Esta integración convierte a **Home Assistant** en el centro de mando integral de tu sistema audiovisual (**LG C5 OLED + Yamaha RX-V673 + Q Acoustics 3020i**), proporcionando telemetría en tiempo real, control total de parámetros de audio/DSP y calibración acústica con un solo toque.

---

## 1. Arquitectura de Conexión

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          PANEL DE HOME ASSISTANT                            │
│  ┌───────────────────────┬──────────────────────────┬────────────────────┐  │
│  │ Media Player Yamaha   │ Telemetría en Tiempo Real│ Calibración 1-Clic │  │
│  │ (Volumen / Entradas)  │ (DSP/Straight/Lift/DRC)  │ (Harman/Cine/Voces)│  │
│  └───────────────────────┴──────────────────────────┴────────────────────┘  │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ HTTP REST & YNC XML
                                       ▼
┌──────────────────────────────────────┴──────────────────────────────────────┐
│                  BRIDGE ACÚSTICO LOCAL (ha_bridge.py :8899)                  │
│       Motor de Calibración CLI + Comunicación Bidireccional con el AVR      │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ YNC Protocol (192.168.1.43:80)
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     RECEPTOR AV YAMAHA RX-V673                              │
│       Memoria PEQ Manual · DAC Burr-Brown · Motor Cinema DSP 3D / VPS       │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Entidades y Visibilidad Total en Home Assistant

### A. Telemetría y Sensores en Tiempo Real (`sensor.*`)
* `sensor.yamaha_perfil_peq_activo`: Muestra el perfil acústico activo (**Harman Impact Reference**, Cinema Impact, etc.).
* `sensor.yamaha_programa_dsp`: Programa de sonido activo (`Straight`, `Standard`, `Drama`, `Music Video`, `7ch Stereo`...).
* `sensor.yamaha_modo_straight`: Indica si el modo de alta fidelidad bit por bit está `Activo` o `Inactivo`.
* `sensor.yamaha_dialogue_lift`: Nivel de elevación de diálogos hacia el panel OLED (0 a 5).
* `sensor.yamaha_dialogue_level`: Nivel de ganancia vocal (0 a 3).
* `sensor.yamaha_adaptive_drc`: Estado de la compresión dinámica inteligente (`Off`, `Auto`).
* `sensor.yamaha_volumen_db`: Nivel exacto de volumen en decibelios (dB).
* `sensor.yamaha_entrada_activa`: Entrada seleccionada (`AV4`, `V-AUX`, `HDMI1`...).

### B. Controles Deslizantes y Selectores (`input_number.*` / `input_select.*`)
* `input_number.yamaha_dialogue_lift_slider`: Control deslizante para subir o bajar la altura de las voces en pantalla en tiempo real.
* `input_number.yamaha_dialogue_lvl_slider`: Control deslizante para adelantar los diálogos.
* `input_select.yamaha_active_profile`: Desplegable de curvas psicoacústicas; al cambiar de opción, calcula y aplica el ecualizador en el Yamaha al instante.
* `input_select.yamaha_dsp_mode_select`: Selector de programas Cinema DSP.
* `input_select.yamaha_input_select`: Selector de entradas de audio/vídeo.

### C. Botones de Acción Rápida (`button.*`)
* **Calibración**: `button.calibrar_harman_impact_definitivo`, `button.calibrar_cine_espectacular`, `button.calibrar_noche_voces`, `button.calibrar_calidez_analogica_jazz`.
* **Escenas Yamaha**: `button.escena_1_musica_hi_fi`, `button.escena_2_cine_estandar`, `button.escena_3_noche_y_voces`, `button.escena_4_conciertos_live_deportes`.

---

## 3. Instalación Rápida (3 Pasos)

### Paso 1: Arrancar el Servicio Bridge en Segundo Plano
En tu ordenador/servidor:
```bash
mkdir -p ~/.config/systemd/user
cp /home/sergio/room-speaker-calibration/homeassistant/yamaha-calibration-bridge.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now yamaha-calibration-bridge
```

### Paso 2: Integrar el Paquete en Home Assistant
1. Copia `homeassistant/yamaha_calibration_package.yaml` en la carpeta `packages/` de tu Home Assistant.
2. *(Si Home Assistant está en otra máquina en tu red local, cambia `localhost:8899` en el YAML por la IP local de este ordenador).*
3. Recarga la configuración YAML en **Herramientas para desarrolladores**.

### Paso 3: Añadir el Panel de Control a Lovelace
1. En tu interfaz de Home Assistant, pulsa **Editar panel**.
2. Añade una tarjeta de tipo **Manual** (código YAML).
3. Pega el contenido de `homeassistant/lovelace_card.yaml`.
