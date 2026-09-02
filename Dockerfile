# ==============================================================================
# Dockerfile: Room Speaker Calibration & Yamaha REST Bridge
# ==============================================================================
FROM python:3.12-slim

# Install ALSA utilities for optional direct host audio hardware passthrough
RUN apt-get update && apt-get install -y --no-install-recommends     alsa-utils     libasound2     curl     && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code and configuration
COPY . .

# Environment Defaults
ENV YAMAHA_IP="192.168.1.39"
ENV BRIDGE_PORT=8899
ENV PYTHONUNBUFFERED=1

EXPOSE 8899

# Healthcheck probe
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3   CMD curl -f http://localhost:8899/api/status || exit 1

ENTRYPOINT ["python3", "scripts/ha_bridge.py", "--serve"]
