#!/usr/bin/env python3
"""
Home Assistant REST Bridge for Room Speaker Calibration & Yamaha RX-V673 Full System Control
Provides bidirectional control, real-time telemetry, acoustic calibration triggers,
and DSP/audio parameter management over HTTP.
"""

import os
import sys
import json
import subprocess
import urllib.request
import xml.etree.ElementTree as ET
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

BRIDGE_PORT = 8899
REPO_DIR = "/home/sergio/room-speaker-calibration"
YAMAHA_IP = "192.168.1.43"
YAMAHA_URL = f"http://{YAMAHA_IP}/YamahaRemoteControl/ctrl"

def send_yamaha_cmd(xml_payload):
    req = urllib.request.Request(
        YAMAHA_URL,
        data=xml_payload.encode('utf-8'),
        headers={'Content-Type': 'text/xml; charset=utf-8', 'User-Agent': 'AV_Receiver/3.1'}
    )
    try:
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            return resp.read().decode('utf-8', errors='ignore')
    except Exception as e:
        return f"<error>{str(e)}</error>"

def get_yamaha_full_status():
    xml = '<YAMAHA_AV cmd="GET"><Main_Zone><Basic_Status>GetParam</Basic_Status></Main_Zone></YAMAHA_AV>'
    raw = send_yamaha_cmd(xml)
    
    status = {
        "online": True,
        "receiver": "Yamaha RX-V673",
        "power": "On",
        "input": "AV4",
        "volume_db": -30.0,
        "mute": False,
        "straight": True,
        "sound_program": "Straight",
        "dsp_3d_mode": "Auto",
        "dialogue_lift": 1,
        "dialogue_lvl": 1,
        "adaptive_drc": "Off",
        "pure_direct": "Off",
        "bass_db": 0.0,
        "treble_db": 0.0,
        "active_peq": "Harman Impact Reference"
    }
    
    if "<error>" in raw or not raw:
        status["online"] = False
        return status
        
    try:
        root = ET.fromstring(raw)
        bz = root.find('.//Basic_Status')
        if bz is not None:
            # Power
            p = bz.find('.//Power_Control/Power')
            if p is not None: status["power"] = p.text
            
            # Input
            inp = bz.find('.//Input/Input_Sel')
            if inp is not None: status["input"] = inp.text
            
            # Volume
            vol_val = bz.find('.//Volume/Lvl/Val')
            vol_exp = bz.find('.//Volume/Lvl/Exp')
            if vol_val is not None and vol_exp is not None:
                val = float(vol_val.text)
                exp = float(vol_exp.text)
                status["volume_db"] = val / (10.0 ** exp)
                
            # Mute
            m = bz.find('.//Volume/Mute')
            if m is not None: status["mute"] = (m.text == "On")
            
            # Surround / Straight / Program
            st = bz.find('.//Surround/Program_Sel/Current/Straight')
            if st is not None: status["straight"] = (st.text == "On")
            
            sp = bz.find('.//Surround/Program_Sel/Current/Sound_Program')
            if sp is not None: status["sound_program"] = sp.text
            
            d3d = bz.find('.//Surround/_3D_Cinema_DSP')
            if d3d is not None: status["dsp_3d_mode"] = d3d.text
            
            # Sound & Video
            d_lift = bz.find('.//Sound_Video/Dialogue_Adjust/Dialogue_Lift')
            if d_lift is not None and d_lift.text: status["dialogue_lift"] = int(d_lift.text)
            
            d_lvl = bz.find('.//Sound_Video/Dialogue_Adjust/Dialogue_Lvl')
            if d_lvl is not None and d_lvl.text: status["dialogue_lvl"] = int(d_lvl.text)
            
            drc = bz.find('.//Sound_Video/Adaptive_DRC')
            if drc is not None: status["adaptive_drc"] = drc.text
            
            pd = bz.find('.//Sound_Video/Pure_Direct/Mode')
            if pd is not None: status["pure_direct"] = pd.text
            
            bass_v = bz.find('.//Sound_Video/Tone/Bass/Val')
            bass_e = bz.find('.//Sound_Video/Tone/Bass/Exp')
            if bass_v is not None and bass_e is not None:
                status["bass_db"] = float(bass_v.text) / (10.0 ** float(bass_e.text))
                
            treb_v = bz.find('.//Sound_Video/Tone/Treble/Val')
            treb_e = bz.find('.//Sound_Video/Tone/Treble/Exp')
            if treb_v is not None and treb_e is not None:
                status["treble_db"] = float(treb_v.text) / (10.0 ** float(treb_e.text))
    except Exception as e:
        status["parse_error"] = str(e)
        
    return status

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
            st = get_yamaha_full_status()
            st["available_targets"] = ["harman_impact", "harman_neutral", "cinema_impact", "vocal_clarity", "warm_music", "audiophile_flat"]
            st["scenes"] = {
                "1": "Música Hi-Fi (Straight)",
                "2": "Cine Estándar (Cinema DSP)",
                "3": "Noche y Voces (Drama / DRC Auto)",
                "4": "Conciertos / Live (Music Video)"
            }
            self._send_json(st)

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
                self._send_json({"success": False, "error": p.stderr}, status=500)

        elif path == "/api/scene":
            num = query.get("num", ["1"])[0]
            cmd = ["python3", f"{REPO_DIR}/scripts/04_yamaha_control.py", "scene", str(num)]
            p = subprocess.run(cmd, capture_output=True, text=True)
            self._send_json({"success": p.returncode == 0, "scene": num, "output": p.stdout})

        elif path == "/api/control":
            # Direct control parameters
            param = query.get("param", [""])[0]
            val = query.get("val", [""])[0]
            
            xml = ""
            if param == "power":
                xml = f'<YAMAHA_AV cmd="PUT"><Main_Zone><Power_Control><Power>{val}</Power></Power_Control></Main_Zone></YAMAHA_AV>'
            elif param == "straight":
                xml = f'<YAMAHA_AV cmd="PUT"><Main_Zone><Surround><Program_Sel><Current><Straight>{val}</Straight></Current></Program_Sel></Surround></Main_Zone></YAMAHA_AV>'
            elif param == "sound_program":
                xml = f'<YAMAHA_AV cmd="PUT"><Main_Zone><Surround><Program_Sel><Current><Sound_Program>{val}</Sound_Program></Current></Program_Sel></Surround></Main_Zone></YAMAHA_AV>'
            elif param == "input":
                xml = f'<YAMAHA_AV cmd="PUT"><Main_Zone><Input><Input_Sel>{val}</Input_Sel></Input></Main_Zone></YAMAHA_AV>'
            elif param == "adaptive_drc":
                xml = f'<YAMAHA_AV cmd="PUT"><Main_Zone><Sound_Video><Adaptive_DRC>{val}</Adaptive_DRC></Sound_Video></Main_Zone></YAMAHA_AV>'
            elif param == "pure_direct":
                xml = f'<YAMAHA_AV cmd="PUT"><Main_Zone><Sound_Video><Pure_Direct><Mode>{val}</Mode></Pure_Direct></Sound_Video></Main_Zone></YAMAHA_AV>'
            elif param == "dialogue_lift":
                xml = f'<YAMAHA_AV cmd="PUT"><Main_Zone><Sound_Video><Dialogue_Adjust><Dialogue_Lift>{val}</Dialogue_Lift></Dialogue_Adjust></Sound_Video></Main_Zone></YAMAHA_AV>'
            elif param == "dialogue_lvl":
                xml = f'<YAMAHA_AV cmd="PUT"><Main_Zone><Sound_Video><Dialogue_Adjust><Dialogue_Lvl>{val}</Dialogue_Lvl></Dialogue_Adjust></Sound_Video></Main_Zone></YAMAHA_AV>'
            elif param == "volume_db":
                db_val = int(float(val) * 10)
                xml = f'<YAMAHA_AV cmd="PUT"><Main_Zone><Volume><Lvl><Val>{db_val}</Val><Exp>1</Exp><Unit>dB</Unit></Lvl></Volume></Main_Zone></YAMAHA_AV>'
            elif param == "mute":
                xml = f'<YAMAHA_AV cmd="PUT"><Main_Zone><Volume><Mute>{val}</Mute></Volume></Main_Zone></YAMAHA_AV>'
            elif param == "bass":
                db_val = int(float(val) * 10)
                xml = f'<YAMAHA_AV cmd="PUT"><Main_Zone><Sound_Video><Tone><Bass><Val>{db_val}</Val><Exp>1</Exp><Unit>dB</Unit></Bass></Tone></Sound_Video></Main_Zone></YAMAHA_AV>'
            elif param == "treble":
                db_val = int(float(val) * 10)
                xml = f'<YAMAHA_AV cmd="PUT"><Main_Zone><Sound_Video><Tone><Treble><Val>{db_val}</Val><Exp>1</Exp><Unit>dB</Unit></Treble></Tone></Sound_Video></Main_Zone></YAMAHA_AV>'
                
            if xml:
                res = send_yamaha_cmd(xml)
                self._send_json({"success": True, "param": param, "val": val, "raw_response": res})
            else:
                self._send_json({"error": f"Parámetro no reconocido: {param}"}, status=400)

        else:
            self._send_json({"error": "Endpoint no encontrado"}, status=404)

def run_server(port=BRIDGE_PORT):
    server_address = ('', port)
    httpd = HTTPServer(server_address, CalibrationHandler)
    print(f"[v] Home Assistant Calibration & System Bridge escuchando en el puerto {port}...")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("Servidor detenido.")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--serve":
        run_server()
    else:
        print("Uso: python3 ha_bridge.py --serve")
