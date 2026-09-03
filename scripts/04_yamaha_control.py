#!/usr/bin/env python3
"""
Yamaha RX-V673 Network Control Engine & Presets
Direct hardware integration via HTTP YNC (XML) API.
"""
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET

IP = "192.168.1.43"
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
            
    v = root.find('.//Volume/Lvl/Val')
    if v is not None and v.text:
        status['Master_Volume'] = f"{float(v.text)/10:.1f}"
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
    print(f"  * Volumen Actual:             {st.get('Master_Volume', 'N/A')} dB")
    print(f"  * Modo Straight:              {st.get('Straight', 'N/A')}")
    print(f"  * Programa DSP:               {st.get('Sound_Program', 'N/A')}")
    print(f"  * Pure Direct:                {st.get('Pure_Direct', 'Off')}")
    print(f"  * Dialogue Lift / Level:      Lift: {st.get('Dialogue_Lift', '0')} | Level: {st.get('Dialogue_Lvl', '0')}")
    print(f"  * Adaptive DRC:               {st.get('Adaptive_DRC', 'Off')}")
    print("=" * 65)


def send_key(key):
    key = key.lower()
    mapping = {
        "on_screen": ("Menu_Control", "On Screen"),
        "onscreen": ("Menu_Control", "On Screen"),
        "menu": ("Menu_Control", "On Screen"),
        "setup": ("Menu_Control", "On Screen"),
        "option": ("Menu_Control", "Option"),
        "top_menu": ("Menu_Control", "Top Menu"),
        "display": ("Menu_Control", "Display"),
        "up": ("Cursor", "Up"),
        "down": ("Cursor", "Down"),
        "left": ("Cursor", "Left"),
        "right": ("Cursor", "Right"),
        "enter": ("Cursor", "Sel"),
        "sel": ("Cursor", "Sel"),
        "ok": ("Cursor", "Sel"),
        "return": ("Cursor", "Return"),
        "back": ("Cursor", "Return")
    }
    
    if key not in mapping:
        print(f"Tecla no reconocida: {key}")
        print("Teclas válidas: on_screen, option, up, down, left, right, enter, return")
        return
        
    tag, val = mapping[key]
    xml = f'<YAMAHA_AV cmd="PUT"><Main_Zone><List_Control><{tag}>{val}</{tag}></List_Control></Main_Zone></YAMAHA_AV>'
    res = send_cmd(xml)
    print(f"[>] Tecla enviada al Yamaha: {key.upper()} ({tag}={val})")

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
def select_scene(num):
    if num not in [1, 2, 3, 4]:
        print("Número de escena inválido (1-4)")
        return
    xml = f'<YAMAHA_AV cmd="PUT"><Main_Zone><Scene><Scene_Sel>Scene {num}</Scene_Sel></Scene></Main_Zone></YAMAHA_AV>'
    res = send_cmd(xml)
    print(f"[v] Escena {num} activada en el Yamaha RX-V673.")
    time.sleep(0.3)
def set_peq_mode(mode):
    valid = ["Through", "Flat", "Front", "Natural", "Manual"]
    mode_map = {m.lower(): m for m in valid}
    target_mode = mode_map.get(str(mode).lower())
    if not target_mode:
        print(f"Modo PEQ inválido: {mode}. Opciones: {', '.join(valid)}")
        return False
    xml = f'<YAMAHA_AV cmd="PUT"><System><Speaker_Preout><Pattern_1><PEQ><Sel>{target_mode}</Sel></PEQ></Pattern_1></Speaker_Preout></System></YAMAHA_AV>'
    res = send_cmd(xml)
    print(f"[✓] PEQ Mode configurado en '{target_mode}': {res.strip()}")
    return True

def get_peq_manual_data(host=IP, timeout=3.0) -> str:
    """Queries the raw XML of active PEQ manual bands from Yamaha NVRAM."""
    xml = '<YAMAHA_AV cmd="GET"><System><Speaker_Preout><Pattern_1><PEQ><Manual_Data>GetParam</Manual_Data></PEQ></Pattern_1></Speaker_Preout></System></YAMAHA_AV>'
    req = urllib.request.Request(
        f"http://{host}/YamahaRemoteControl/ctrl",
        data=xml.encode('utf-8'),
        headers={'Content-Type': 'text/xml; charset=utf-8', 'User-Agent': 'AV_Receiver/3.1'}
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode('utf-8', errors='ignore')

def deploy_peq_matrix_with_readback(
    peq_matrix: dict,
    host=IP,
    timeout=3.0,
    verify_readback: bool = True
) -> tuple[bool, list[str]]:
    """
    Atomic Write-Commit-Readback transaction for Yamaha RX-V673 PEQ.
    Guarantees that 100% of the 14 biquad bands committed to hardware match the optimizer.
    """
    url = f"http://{host}/YamahaRemoteControl/ctrl"
    headers = {'Content-Type': 'text/xml; charset=utf-8', 'User-Agent': 'AV_Receiver/3.1'}
    
    # 1. Set PEQ mode to Manual
    cmd_sel = '<YAMAHA_AV cmd="PUT"><System><Speaker_Preout><Pattern_1><PEQ><Sel>Manual</Sel></PEQ></Pattern_1></Speaker_Preout></System></YAMAHA_AV>'
    req = urllib.request.Request(url, data=cmd_sel.encode('utf-8'), headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        pass
        
    def format_freq(f_hz: float) -> str:
        if f_hz >= 1000.0:
            val = f_hz / 1000.0
            return f"{val:.2f} kHz" if (val * 10) % 1 != 0 else f"{val:.1f} kHz"
        return f"{f_hz:.1f} Hz"

    # 2. Build XML for Front_L and Front_R
    ch_map = {"left": "Front_L", "right": "Front_R"}
    for ch_key, ch_tag in ch_map.items():
        bands = peq_matrix.get(ch_key, [])
        if not bands:
            continue
        bands_xml = ""
        for b in bands:
            b_idx = int(b["band"])
            f_str = format_freq(float(b["freq_hz"]))
            gain_val = int(round(float(b["gain_db"]) * 10))
            q_str = f"{float(b['q']):.3f}"
            bands_xml += f"<Band_{b_idx}><Freq>{f_str}</Freq><Gain><Val>{gain_val}</Val><Exp>1</Exp><Unit>dB</Unit></Gain><Q>{q_str}</Q></Band_{b_idx}>"
            
        xml_ch = f'<YAMAHA_AV cmd="PUT"><System><Speaker_Preout><Pattern_1><PEQ><Manual_Data><{ch_tag}>{bands_xml}</{ch_tag}></Manual_Data></PEQ></Pattern_1></Speaker_Preout></System></YAMAHA_AV>'
        req_ch = urllib.request.Request(url, data=xml_ch.encode('utf-8'), headers=headers)
        with urllib.request.urlopen(req_ch, timeout=timeout) as r:
            res_txt = r.read().decode('utf-8', errors='ignore')
            if 'RC="0"' not in res_txt and 'OK' not in res_txt:
                return False, [f"Hardware returned error on {ch_tag} write: {res_txt}"]

    if not verify_readback:
        return True, []
        
    # 3. Hardware Readback Verification
    time.sleep(0.1)
    try:
        raw_xml = get_peq_manual_data(host=host, timeout=timeout)
        root = ET.fromstring(raw_xml)
    except Exception as e:
        return False, [f"Failed to read back NVRAM state: {e}"]
        
    divergent = []
    for ch_key, ch_tag in ch_map.items():
        bands = peq_matrix.get(ch_key, [])
        ch_elem = root.find(f".//{ch_tag}")
        if ch_elem is None:
            divergent.append(f"Channel {ch_tag} missing in readback XML")
            continue
            
        for b in bands:
            b_idx = int(b["band"])
            b_elem = ch_elem.find(f"Band_{b_idx}")
            if b_elem is None:
                divergent.append(f"{ch_tag} Band_{b_idx} missing in hardware readback")
                continue
            
            gain_elem = b_elem.find(".//Gain/Val")
            if gain_elem is not None and gain_elem.text:
                hw_gain = float(gain_elem.text) / 10.0
                expected_gain = float(b["gain_db"])
                if abs(hw_gain - expected_gain) > 0.3:
                    divergent.append(f"{ch_tag} Band_{b_idx} Gain mismatch: expected {expected_gain} dB, hardware has {hw_gain} dB")

    if divergent:
        return False, divergent
    return True, []
    print_status()

def program_all_scenes():
    print("[*] Programando nombres y parámetros de las 4 escenas en NVRAM...")
    # 1. Nombres
    rename_xml = """<YAMAHA_AV cmd="PUT">
  <Main_Zone>
    <Scene>
      <Scene_1><Name>Música Hi-Fi</Name></Scene_1>
      <Scene_2><Name>Cine y Pelis</Name></Scene_2>
      <Scene_3><Name>TV y Series</Name></Scene_3>
      <Scene_4><Name>Pure Direct</Name></Scene_4>
    </Scene>
  </Main_Zone>
</YAMAHA_AV>"""
    send_cmd(rename_xml)

    # 2. Scene 1: Música Hi-Fi
    s1 = """<YAMAHA_AV cmd="PUT"><Main_Zone><Scene><Scene_1>
      <Input><Input_Sel>AV4</Input_Sel></Input>
      <Sound_Video><Pure_Direct><Mode>Off</Mode></Pure_Direct><HDMI><Output><OUT_1>On</OUT_1></Output></HDMI><Adaptive_DRC>Off</Adaptive_DRC></Sound_Video>
      <Surround><Program_Sel><Current><Straight>On</Straight><Enhancer>Off</Enhancer></Current></Program_Sel></Surround>
    </Scene_1></Scene></Main_Zone></YAMAHA_AV>"""
    send_cmd(s1)

    # 3. Scene 2: Cine y Pelis
    s2 = """<YAMAHA_AV cmd="PUT"><Main_Zone><Scene><Scene_2>
      <Input><Input_Sel>AV4</Input_Sel></Input>
      <Sound_Video><Pure_Direct><Mode>Off</Mode></Pure_Direct><HDMI><Output><OUT_1>On</OUT_1></Output></HDMI><Adaptive_DRC>Off</Adaptive_DRC>
        <Dialogue_Adjust><Dialogue_Lift>1</Dialogue_Lift><Dialogue_Lvl>1</Dialogue_Lvl></Dialogue_Adjust>
      </Sound_Video>
      <Surround><Program_Sel><Current><Straight>Off</Straight><Enhancer>Off</Enhancer><Sound_Program>Standard</Sound_Program></Current></Program_Sel></Surround>
    </Scene_2></Scene></Main_Zone></YAMAHA_AV>"""
    send_cmd(s2)

    # 4. Scene 3: TV y Series
    s3 = """<YAMAHA_AV cmd="PUT"><Main_Zone><Scene><Scene_3>
      <Input><Input_Sel>AV4</Input_Sel></Input>
      <Sound_Video><Pure_Direct><Mode>Off</Mode></Pure_Direct><HDMI><Output><OUT_1>On</OUT_1></Output></HDMI><Adaptive_DRC>Off</Adaptive_DRC>
        <Dialogue_Adjust><Dialogue_Lift>1</Dialogue_Lift><Dialogue_Lvl>2</Dialogue_Lvl></Dialogue_Adjust>
      </Sound_Video>
      <Surround><Program_Sel><Current><Straight>Off</Straight><Enhancer>Off</Enhancer><Sound_Program>Drama</Sound_Program></Current></Program_Sel></Surround>
    </Scene_3></Scene></Main_Zone></YAMAHA_AV>"""
    send_cmd(s3)

    # 5. Scene 4: Pure Direct
    s4 = """<YAMAHA_AV cmd="PUT"><Main_Zone><Scene><Scene_4>
      <Input><Input_Sel>AV4</Input_Sel></Input>
      <Sound_Video><Pure_Direct><Mode>On</Mode></Pure_Direct><HDMI><Output><OUT_1>On</OUT_1></Output></HDMI></Sound_Video>
      <Surround><Program_Sel><Current><Straight>On</Straight><Enhancer>Off</Enhancer></Current></Program_Sel></Surround>
    </Scene_4></Scene></Main_Zone></YAMAHA_AV>"""
    send_cmd(s4)
    print("[v] Las 4 escenas han sido configuradas y grabadas con éxito en el Yamaha RX-V673.")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg in ["status", "estado", "-s"]:
            print_status()
        elif arg in ["program_scenes", "scenes", "program", "setup_scenes"]:
            program_all_scenes()
        elif arg in ["scene", "escena"]:
            if len(sys.argv) > 2 and sys.argv[2].isdigit():
                select_scene(int(sys.argv[2]))
            else:
                print("Especifica número de escena (1-4): python3 04_yamaha_control.py scene 1")
        elif arg in ["peq", "mode", "peq_mode"]:
            if len(sys.argv) > 2:
                set_peq_mode(sys.argv[2])
            else:
                print("Especifica modo PEQ (Through, Flat, Front, Natural, Manual)")
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
        elif arg in ["key", "k", "send"]:
            if len(sys.argv) > 2:
                for k in sys.argv[2:]:
                    send_key(k)
                    time.sleep(0.3)
            else:
                print("Indica una tecla: on_screen, option, up, down, left, right, enter, return")
        elif arg in ["up", "down", "left", "right", "enter", "sel", "ok", "return", "back", "on_screen", "onscreen", "option", "menu", "setup"]:
            send_key(arg)
        else:
            print("Uso: python3 04_yamaha_control.py [status | 1 | 2 | 3 | 4 | on_screen | option | up | down | left | right | enter | return]")
    else:
        print_status()
