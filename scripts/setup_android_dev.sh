#!/usr/bin/env bash
# ==============================================================================
# Setup del Entorno de Desarrollo Android y Bucle Rápido en Linux (CachyOS/Arch)
# ==============================================================================
set -euo pipefail

echo "=== Configurando Herramientas Android en Linux ==="

# 1. Instalar JDK 17, ADB y Scrcpy
if ! command -v adb &> /dev/null || ! command -v javac &> /dev/null || ! command -v scrcpy &> /dev/null; then
  echo "[+] Instalando JDK 17, android-tools y scrcpy mediante pacman..."
  sudo pacman -S --needed --noconfirm jdk17-openjdk android-tools scrcpy
else
  echo "[✓] JDK 17, ADB y Scrcpy ya están instalados."
fi

# 2. Configurar variables de entorno si existen Android SDK
export ANDROID_HOME="${ANDROID_HOME:-$HOME/Android/Sdk}"
if [ -d "$ANDROID_HOME" ]; then
  export PATH="$PATH:$ANDROID_HOME/platform-tools:$ANDROID_HOME/cmdline-tools/latest/bin"
  echo "[✓] ANDROID_HOME configurado en: $ANDROID_HOME"
fi

# 3. Comprobar dispositivos conectados
echo ""
echo "=== Dispositivos Android Conectados ==="
adb devices -l || true

echo ""
echo "=== Comandos para el Bucle de Desarrollo ==="
echo "1. Bucle en Vivo (Live Reload):"
echo "   cd frontend && bun run dev"
echo ""
echo "2. Pantalla de tu móvil en el PC:"
echo "   scrcpy --stay-awake --turn-screen-off"
echo ""
echo "3. Compilar APK localmente:"
echo "   cd frontend/android && ./gradlew assembleDebug"
echo ""
