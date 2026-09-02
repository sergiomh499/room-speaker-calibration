#!/usr/bin/env python3
"""
Yamaha RX-V673 Network Control Utility
Provides programmatic control, status queries, and SCENE switching via the HTTP YNC (XML) API.
"""
import sys
import urllib.request
import xml.etree.ElementTree as ET

IP = "192.168.1.39"
URL = f"http://{IP}/YamahaRemoteControl/ctrl"

def send_cmd(xml_payload):
    req = urllib.request.Request(
        URL,
        data=xml_payload.encode('utf-8'),
        headers={'Content-Type': 'text/xml; charset=utf-8', 'User-Agent': 'AV_Receiver/3.1'}
    )
    with urllib.request.urlopen(req, timeout=3.0) as resp:
        return resp.read().decode('utf-8', errors='ignore')

def get_status():
    xml = '<YAMAHA_AV cmd="GET"><Main_Zone><Basic_Status>GetParam</Basic_Status></Main_Zone></YAMAHA_AV>'
    res = send_cmd(xml)
    print("=== ESTADO ACTUAL DEL YAMAHA RX-V673 ===")
    for line in res.replace('><', '>\n<').splitlines():
        if any(k in line for k in ['Power', 'Input_Sel>', 'Lvl>', 'Mute', 'Straight', 'Sound_Program', 'Bass', 'Treble', 'Dialogue_Lvl', 'Adaptive_DRC']):
            print(" ", line.strip())

def select_scene(num):
    if num not in [1, 2, 3, 4]:
        print("Número de escena inválido. Usa 1, 2, 3 o 4.")
        return
    scene_names = {
        1: "SCENE 1: Música Hi-Fi (Straight / Bit-perfect)",
        2: "SCENE 2: Cine Estándar (Cinema DSP / Dialogue +1)",
        3: "SCENE 3: Noche y Voces (Drama / Adaptive DRC / Dialogue +2)",
        4: "SCENE 4: Conciertos / Live (Music Video DSP / Inmersión)"
    }
    xml = f'<YAMAHA_AV cmd="PUT"><Main_Zone><Scene><Scene_Sel>Scene {num}</Scene_Sel></Scene></Main_Zone></YAMAHA_AV>'
    send_cmd(xml)
    print(f"[✓] Conmutado a {scene_names[num]}")

def set_input(input_name="AV4"):
    xml = f'<YAMAHA_AV cmd="PUT"><Main_Zone><Input><Input_Sel>{input_name}</Input_Sel></Input></Main_Zone></YAMAHA_AV>'
    send_cmd(xml)
    print(f"Entrada cambiada a {input_name}")

def set_straight(on=True):
    val = "On" if on else "Off"
    xml = f'<YAMAHA_AV cmd="PUT"><Main_Zone><Surround><Program_Sel><Current><Straight>{val}</Straight></Current></Program_Sel></Surround></Main_Zone></YAMAHA_AV>'
    send_cmd(xml)
    print(f"Modo Straight: {val}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()
        if cmd == "status":
            get_status()
        elif cmd == "scene" and len(sys.argv) > 2:
            select_scene(int(sys.argv[2]))
        elif cmd == "input" and len(sys.argv) > 2:
            set_input(sys.argv[2])
        elif cmd == "straight":
            set_straight(True)
        else:
            print("Uso: python3 04_yamaha_control.py [status | scene <1-4> | input <NOMBRE> | straight]")
    else:
        get_status()
