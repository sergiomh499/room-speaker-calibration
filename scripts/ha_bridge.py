#!/usr/bin/env python3
"""
Home Assistant REST Bridge for Room Speaker Calibration
Allows Home Assistant to trigger acoustic sweeps, apply PEQ presets, 
switch Yamaha scenes, and query calibration status via simple HTTP endpoints.
"""

import os
import sys
import json
import subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

BRIDGE_PORT = 8899
REPO_DIR = "/home/sergio/room-speaker-calibration"

class CalibrationHandler(BaseHTTPRequestHandler):
    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode('utf-8'))

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        if path == "/api/status":
            self._send_json({
                "status": "online",
                "receiver": "Yamaha RX-V673",
                "speakers": "Q Acoustics 3020i",
                "active_peq": "Harman Impact Reference",
                "available_targets": ["harman_impact", "harman_neutral", "cinema_impact", "vocal_clarity", "warm_music", "audiophile_flat"],
                "scenes": {
                    "1": "Música Hi-Fi (Straight)",
                    "2": "Cine Estándar (Cinema DSP)",
                    "3": "Noche y Voces (Drama / DRC Auto)",
                    "4": "Conciertos / Live (Music Video)"
                }
            })

        elif path == "/api/calibrate":
            target = query.get("target", ["harman_impact"])[0]
            print(f"[*] Solicitada calibración para el perfil: {target}")
            
            cmd = ["python3", f"{REPO_DIR}/scripts/auto_calibrate.py", "--target", target, "--export-pdf"]
            p = subprocess.run(cmd, capture_output=True, text=True)
            
            if p.returncode == 0:
                self._send_json({
                    "success": True,
                    "target": target,
                    "message": f"Calibración {target} completada y aplicada con éxito.",
                    "output": p.stdout
                })
            else:
                self._send_json({
                    "success": False,
                    "error": p.stderr
                }, status=500)

        elif path == "/api/scene":
            num = query.get("num", ["1"])[0]
            cmd = ["python3", f"{REPO_DIR}/scripts/04_yamaha_control.py", "scene", str(num)]
            p = subprocess.run(cmd, capture_output=True, text=True)
            
            self._send_json({
                "success": p.returncode == 0,
                "scene": num,
                "output": p.stdout
            })

        else:
            self._send_json({"error": "Endpoint no encontrado"}, status=404)

def run_server(port=BRIDGE_PORT):
    server_address = ('', port)
    httpd = HTTPServer(server_address, CalibrationHandler)
    print(f"[v] Home Assistant Calibration Bridge escuchando en el puerto {port}...")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("Servidor detenido.")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--serve":
        run_server()
    elif len(sys.argv) > 2 and sys.argv[1] == "--target":
        target = sys.argv[2]
        cmd = ["python3", f"{REPO_DIR}/scripts/auto_calibrate.py", "--target", target, "--export-pdf"]
        subprocess.run(cmd)
    else:
        print("Uso: python3 ha_bridge.py [--serve | --target <nombre_perfil>]")
