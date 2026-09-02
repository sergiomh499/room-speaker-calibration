# Integración de Calibración Acústica con Home Assistant

Este módulo permite controlar y recalcular los perfiles de corrección de sala (**Harman Impact**, **Cinema Impact**, **Vocal Clarity**, **Warm Music**) directamente desde botones o selectores en tu panel de **Home Assistant**.

---

## 1. Arquitectura de Conexión

```
┌───────────────────────────┐      HTTP REST      ┌───────────────────────────┐      YNC XML      ┌───────────────────────────┐
│       Home Assistant      │ ──────────────────> │   ha_bridge.py (:8899)    │ ────────────────> │      Yamaha RX-V673       │
│  (Botones / Automatismos) │                     │ (Motor de Calibración CLI)│                   │   (Memoria PEQ y Escenas) │
└───────────────────────────┘                     └───────────────────────────┘                   └───────────────────────────┘
```

---

## 2. Puesta en Marcha en 3 Pasos

### Paso 1: Iniciar el Servidor Bridge en Segundo Plano
En el ordenador/servidor donde está este repositorio:
```bash
cd /home/sergio/room-speaker-calibration
python3 scripts/ha_bridge.py --serve
```
*(Opcional: puedes crearlo como servicio systemd con `systemctl --user enable --now yamaha-calibration-bridge`).*

---

### Paso 2: Añadir el Paquete YAML a Home Assistant
1. Copia el archivo `homeassistant/yamaha_calibration_package.yaml` en la carpeta `packages/` de tu configuración de Home Assistant (o incluye su contenido en `configuration.yaml`).
2. Si Home Assistant está en otra máquina en tu red local, cambia `localhost:8899` en el YAML por la IP de tu ordenador (ej. `http://192.168.1.XX:8899`).
3. Reinicia Home Assistant o recarga los archivos YAML en *Herramientas para desarrolladores*.

---

### Paso 3: Añadir la Tarjeta al Dashboard Lovelace
1. Edita tu Dashboard de Home Assistant.
2. Añade una tarjeta de tipo **Manual** (Código YAML).
3. Pega el contenido de `homeassistant/lovelace_card.yaml`.

---

## 3. Entidades Disponibles en Home Assistant

* **Botones de Calibración**:
  * `button.calibrar_harman_impact_definitivo`: Aplica la curva definitiva con pegada y control de resonancia.
  * `button.calibrar_cine_espectacular`: Realce de subgraves para cine de acción.
  * `button.calibrar_noche_voces`: Compresión dinámica e inteligibilidad para madrugadas.
  * `button.calibrar_calidez_analogica_jazz`: Curva dulce británica para vinilos.
* **Selector Desplegable**:
  * `input_select.yamaha_active_profile`: Permite seleccionar la curva deseada y la aplica automáticamente al receptor.
* **Botones de Escenas Yamaha**:
  * `button.escena_1_musica_hi_fi` (`SCENE 1`)
  * `button.escena_2_cine_estandar` (`SCENE 2`)
  * `button.escena_3_noche_y_voces` (`SCENE 3`)
  * `button.escena_4_conciertos_live_deportes` (`SCENE 4`)
