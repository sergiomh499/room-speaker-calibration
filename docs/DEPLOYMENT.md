# Guía de Despliegue en Infraestructura (Docker, Proxmox, Kubernetes y HA OS)

Este proyecto está diseñado con una arquitectura modular desacoplada para ejecutarse tanto en local como en cualquier entorno de virtualización o contenedores junto a tu infraestructura de Home Assistant.

---

## 1. 🐳 Despliegue con Docker & Docker Compose

### Opción A: Docker Compose (Recomendado)
Para arrancar el stack en 1 comando:
```bash
docker compose up -d --build
```
* **Variables de entorno configurables en `docker-compose.yml`**:
  * `YAMAHA_IP`: IP de tu receptor (por defecto `192.168.1.43`).
  * `BRIDGE_PORT`: Puerto de escucha del servicio (por defecto `8899`).

---

## 2. 🎛️ Despliegue en Proxmox VE (Contenedor LXC)

Puedes ejecutar el bridge en un contenedor LXC ultraligero (Debian 12 o Ubuntu 24.04, <50 MB RAM):

1. Crea un contenedor LXC en Proxmox VE.
2. Dentro de la consola del contenedor, ejecuta el instalador automatizado:
```bash
curl -fsSL https://raw.githubusercontent.com/sergiomh499/room-speaker-calibration/master/deploy/proxmox/install_lxc.sh | bash
```
El script instalará las dependencias en un entorno virtual (`venv`), clonará el código y habilitará el servicio `systemd` persistente.

---

## 3. ☸️ Despliegue en Kubernetes (K3s / MicroK8s / K8s)

Los manifiestos oficiales se encuentran en `deploy/k8s/`:

```bash
# 1. Aplicar ConfigMap, Deployment y Service:
kubectl apply -f deploy/k8s/configmap.yaml
kubectl apply -f deploy/k8s/deployment.yaml
kubectl apply -f deploy/k8s/service.yaml

# 2. Verificar estado de los Pods y Probes:
kubectl get pods -n home-automation -l app=yamaha-calibration-bridge
```

---

## 4. 🏠 Despliegue como Add-on Local en Home Assistant OS

Si utilizas **Home Assistant OS / Supervised**:
1. Copia la carpeta `homeassistant/addon` dentro de la carpeta `/addons/local/yamaha_calibration_bridge` de tu Home Assistant.
2. Ve a **Ajustes $
ightarrow$ Complementos $
ightarrow$ Tienda de complementos $
ightarrow$ Comprobar actualizaciones**.
3. Instala el complemento **Room Speaker Calibration Bridge** y pulsa **Iniciar**.
