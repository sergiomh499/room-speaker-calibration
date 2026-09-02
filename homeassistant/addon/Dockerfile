FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends     alsa-utils     curl     && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1
EXPOSE 8899

CMD ["python3", "scripts/ha_bridge.py", "--serve"]
