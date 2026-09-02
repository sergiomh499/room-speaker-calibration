#!/usr/bin/env python3
"""
Yamaha RX-V673 Network Control Engine & Presets
Direct hardware integration via HTTP YNC (XML) API.
"""
import sys
import time
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

def get_parsed_status():
    xml = '<YAMAHA_AV cmd="GET"><Main_Zone><Basic_Status>GetParam</Basic_Status></Main_Zone></YAMAHA_AV>'
    res = send_cmd(xml)
    root = ET.fromstring(res)
    
    status = {}
    for elem in root.iter():
        if elem.text and elem.text.strip():
            status[elem.tag] = elem.text.strip()
            
    # Pure direct
    for elem in root.iter('Pure_Direct'):
        for child in elem:
            if child.tag == 'Mode':
                status['Pure_Direct'] = child.text.strip()
                
    return status

def print_status():
    st = get_parsed_status()
    print("=" * 65)
    print("       ESTADO REAL DEL RECEPTOR YAMAHA RX-V673 (ONLINE)")
    print("=" * 65)
    print(f"  * Alimentación (Power):       {st.get('Power', 'N/A')}")
    print(f"  * Entrada Seleccionada:       {st.get('Input_Sel', 'N/A')} (LG C5 HDMI ARC)")
    print(f"  * Volumen Actual:             {st.get('Val', 'N/A')} dB")
    print(f"  * Modo Straight:              {st.get('Straight', 'N/A')}")
    print(f"  * Programa DSP:               {st.get('Sound_Program', 'N/A')}")
    print(f"  * Pure Direct:                {st.get('Pure_Direct', 'Off')}")
    print(f"  * Dialogue Lift / Level:      Lift: {st.get('Dialogue_Lift', '0')} | Level: {st.get('Dialogue_Lvl', '0')}")
    print(f"  * Adaptive DRC:               {st.get('Adaptive_DRC', 'Off')}")
    print("=" * 65)

def apply_preset(num):
    if num not in [1, 2, 3, 4]:
        print("Número de preset inválido. Usa 1, 2, 3 o 4.")
        return

    # 1. Asegurar Power On y entrada AV4
    send_cmd('<YAMAHA_AV cmd="PUT"><Main_Zone><Power_Control><Power>On</Power></Power_Control></Main_Zone></YAMAHA_AV>')
    send_cmd('<YAMAHA_AV cmd="PUT"><Main_Zone><Input><Input_Sel>AV4</Input_Sel></Input></Main_Zone></YAMAHA_AV>')

    if num == 1:
        # SCENE 1: Música Hi-Fi
        print("\n[+] Aplicando PRESET 1: MÚSICA HI-FI (Straight / PEQ Manual Activo)...")
        send_cmd('<YAMAHA_AV cmd="PUT"><Main_Zone><Sound_Video><Pure_Direct><Mode>Off</Mode></Pure_Direct></Sound_Video></Main_Zone></YAMAHA_AV>')
        send_cmd('<YAMAHA_AV cmd="PUT"><Main_Zone><Surround><Program_Sel><Current><Straight>On</Straight></Current></Program_Sel></Surround></Main_Zone></YAMAHA_AV>')
        send_cmd('<YAMAHA_AV cmd="PUT"><Main_Zone><Surround><Program_Sel><Current><Enhancer>Off</Enhancer></Current></Program_Sel></Surround></Main_Zone></YAMAHA_AV>')
        send_cmd('<YAMAHA_AV cmd="PUT"><Main_Zone><Sound_Video><Adaptive_DRC>Off</Adaptive_DRC></Sound_Video></Main_Zone></YAMAHA_AV>')

    elif num == 2:
        # SCENE 2: Cine & Películas
        print("\n[+] Aplicando PRESET 2: CINE & PELÍCULAS (Standard DSP / Dialogue Lift +1)...")
        send_cmd('<YAMAHA_AV cmd="PUT"><Main_Zone><Sound_Video><Pure_Direct><Mode>Off</Mode></Pure_Direct></Sound_Video></Main_Zone></YAMAHA_AV>')
        send_cmd('<YAMAHA_AV cmd="PUT"><Main_Zone><Surround><Program_Sel><Current><Straight>Off</Straight></Current></Program_Sel></Surround></Main_Zone></YAMAHA_AV>')
        send_cmd('<YAMAHA_AV cmd="PUT"><Main_Zone><Surround><Program_Sel><Current><Sound_Program>Standard</Sound_Program></Current></Program_Sel></Surround></Main_Zone></YAMAHA_AV>')
        send_cmd('<YAMAHA_AV cmd="PUT"><Main_Zone><Sound_Video><Dialogue_Adjust><Dialogue_Lift>1</Dialogue_Lift><Dialogue_Lvl>1</Dialogue_Lvl></Dialogue_Adjust></Sound_Video></Main_Zone></YAMAHA_AV>')
        send_cmd('<YAMAHA_AV cmd="PUT"><Main_Zone><Sound_Video><Adaptive_DRC>Off</Adaptive_DRC></Sound_Video></Main_Zone></YAMAHA_AV>')

    elif num == 3:
        # SCENE 3: TV & Series
        print("\n[+] Aplicando PRESET 3: TV & SERIES (Drama DSP / Diálogos Optimizados)...")
        send_cmd('<YAMAHA_AV cmd="PUT"><Main_Zone><Sound_Video><Pure_Direct><Mode>Off</Mode></Pure_Direct></Sound_Video></Main_Zone></YAMAHA_AV>')
        send_cmd('<YAMAHA_AV cmd="PUT"><Main_Zone><Surround><Program_Sel><Current><Straight>Off</Straight></Current></Program_Sel></Surround></Main_Zone></YAMAHA_AV>')
        send_cmd('<YAMAHA_AV cmd="PUT"><Main_Zone><Surround><Program_Sel><Current><Sound_Program>Drama</Sound_Program></Current></Program_Sel></Surround></Main_Zone></YAMAHA_AV>')
        send_cmd('<YAMAHA_AV cmd="PUT"><Main_Zone><Sound_Video><Dialogue_Adjust><Dialogue_Lift>1</Dialogue_Lift><Dialogue_Lvl>1</Dialogue_Lvl></Dialogue_Adjust></Sound_Video></Main_Zone></YAMAHA_AV>')
        send_cmd('<YAMAHA_AV cmd="PUT"><Main_Zone><Sound_Video><Adaptive_DRC>Off</Adaptive_DRC></Sound_Video></Main_Zone></YAMAHA_AV>')

    elif num == 4:
        # SCENE 4: Pure Direct
        print("\n[+] Aplicando PRESET 4: PURE DIRECT (Bypass Digital)...")
        send_cmd('<YAMAHA_AV cmd="PUT"><Main_Zone><Sound_Video><Pure_Direct><Mode>On</Mode></Pure_Direct></Sound_Video></Main_Zone></YAMAHA_AV>')

    time.sleep(0.2)
    print_status()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg in ["status", "estado", "-s"]:
            print_status()
        elif arg.isdigit() and int(arg) in [1, 2, 3, 4]:
            apply_preset(int(arg))
        elif arg in ["musica", "music", "hifi", "1"]:
            apply_preset(1)
        elif arg in ["cine", "pelis", "movies", "2"]:
            apply_preset(2)
        elif arg in ["tv", "series", "drama", "3"]:
            apply_preset(3)
        elif arg in ["direct", "puredirect", "pure", "4"]:
            apply_preset(4)
        else:
            print("Uso: python3 04_yamaha_control.py [status | 1 | 2 | 3 | 4 | musica | cine | tv | direct]")
    else:
        print_status()
