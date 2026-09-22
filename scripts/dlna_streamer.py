#!/usr/bin/env python3
"""
DLNA DMR / UPnP Network Audio Streamer for Yamaha RX-V673.
Allows streaming lossless sweeps, test signals, and music directly over Wi-Fi / Ethernet
without needing an HDMI cable or physical connection.
"""
from __future__ import annotations

import argparse
import html
import socket
import sys
import time
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from typing import Optional, Tuple

DEFAULT_AVR_IP = "192.168.1.43"
DEFAULT_UPNP_PORT = 8080

def get_local_lan_ip(target_ip: str = DEFAULT_AVR_IP) -> str:
    """Finds the local IP address routable to the AVR."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect((target_ip, 80))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()

def send_soap_command(action: str, body_xml: str, host: str = DEFAULT_AVR_IP, port: int = DEFAULT_UPNP_PORT, timeout: float = 3.0) -> Tuple[int, str]:
    """Sends a SOAP request to the Yamaha AVTransport service."""
    ctrl_url = f"http://{host}:{port}/AVTransport/ctrl"
    soap = f"""<?xml version="1.0" encoding="utf-8"?>
<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
  <s:Body>
    <u:{action} xmlns:u="urn:schemas-upnp-org:service:AVTransport:1">
      {body_xml}
    </u:{action}>
  </s:Body>
</s:Envelope>"""
    headers = {
        "Content-Type": 'text/xml; charset="utf-8"',
        "SOAPAction": f'"urn:schemas-upnp-org:service:AVTransport:1#{action}"',
        "User-Agent": "RoomCalibration-DLNA/1.0",
    }
    req = urllib.request.Request(ctrl_url, data=soap.encode("utf-8"), headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8")
    except Exception as e:
        return 0, str(e)

def get_current_avr_input(host: str = DEFAULT_AVR_IP) -> str:
    """Queries active input from Yamaha via YNC XML."""
    ync_url = f"http://{host}/YamahaRemoteControl/ctrl"
    req = urllib.request.Request(
        ync_url,
        data=b'<YAMAHA_AV cmd="GET"><Main_Zone><Input><Input_Sel>GetParam</Input_Sel></Input></Main_Zone></YAMAHA_AV>',
        headers={"Content-Type": "text/xml; charset=utf-8"},
    )
    try:
        with urllib.request.urlopen(req, timeout=2.0) as resp:
            xml = resp.read().decode("utf-8")
            root = ET.fromstring(xml)
            el = root.find(".//Input_Sel")
            return el.text.strip() if el is not None and el.text else "AV4"
    except Exception:
        return "AV4"

def set_avr_input(input_name: str, host: str = DEFAULT_AVR_IP) -> bool:
    """Switches Yamaha input (e.g. SERVER, AV4, V-AUX)."""
    ync_url = f"http://{host}/YamahaRemoteControl/ctrl"
    payload = f'<YAMAHA_AV cmd="PUT"><Main_Zone><Input><Input_Sel>{input_name}</Input_Sel></Input></Main_Zone></YAMAHA_AV>'
    req = urllib.request.Request(
        ync_url,
        data=payload.encode("utf-8"),
        headers={"Content-Type": "text/xml; charset=utf-8"},
    )
    try:
        with urllib.request.urlopen(req, timeout=2.0) as resp:
            return resp.status == 200
    except Exception:
        return False

def stream_audio_to_avr(
    audio_url: str,
    title: str = "Acoustic Calibration Signal",
    host: str = DEFAULT_AVR_IP,
    port: int = DEFAULT_UPNP_PORT,
    auto_switch_input: bool = True,
) -> Tuple[bool, str]:
    """
    Directly streams an audio URL to the Yamaha RX-V673 over Wi-Fi / Ethernet via DLNA.
    Switches input to SERVER, loads AVTransport URI with DIDL-Lite metadata, and executes Play.
    """
    if auto_switch_input:
        curr_in = get_current_avr_input(host)
        if curr_in != "SERVER":
            set_avr_input("SERVER", host=host)
            time.sleep(0.4)

    # Build DIDL-Lite metadata
    didl = f"""<DIDL-Lite xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/">
<item id="1" parentID="0" restricted="1">
<dc:title>{html.escape(title)}</dc:title>
<upnp:class>object.item.audioItem.musicTrack</upnp:class>
<res protocolInfo="http-get:*:audio/wav:DLNA.ORG_PN=LPCM">{html.escape(audio_url)}</res>
</item>
</DIDL-Lite>"""

    body = f"""<InstanceID>0</InstanceID>
<CurrentURI>{html.escape(audio_url)}</CurrentURI>
<CurrentURIMetaData>{html.escape(didl)}</CurrentURIMetaData>"""

    status, resp = send_soap_command("SetAVTransportURI", body, host=host, port=port)
    if status != 200:
        return False, f"Error SetAVTransportURI (HTTP {status}): {resp}"

    # Send Play
    status, resp = send_soap_command("Play", "<InstanceID>0</InstanceID><Speed>1</Speed>", host=host, port=port)
    if status != 200:
        return False, f"Error Play (HTTP {status}): {resp}"

    return True, "Streaming iniciado correctamente en Yamaha RX-V673."

def stop_avr_stream(host: str = DEFAULT_AVR_IP, port: int = DEFAULT_UPNP_PORT, restore_input: Optional[str] = None) -> Tuple[bool, str]:
    """Stops playback on Yamaha AVR and optionally restores input."""
    status, resp = send_soap_command("Stop", "<InstanceID>0</InstanceID>", host=host, port=port)
    if restore_input:
        set_avr_input(restore_input, host=host)
    return status == 200, resp

def get_avr_transport_status(host: str = DEFAULT_AVR_IP, port: int = DEFAULT_UPNP_PORT) -> dict:
    """Queries current playback state (PLAYING, STOPPED, NO_MEDIA_PRESENT)."""
    status, resp = send_soap_command("GetTransportInfo", "<InstanceID>0</InstanceID>", host=host, port=port)
    state = "UNKNOWN"
    if status == 200:
        if "PLAYING" in resp:
            state = "PLAYING"
        elif "PAUSED_PLAYBACK" in resp:
            state = "PAUSED"
        elif "TRANSITIONING" in resp:
            state = "TRANSITIONING"
        elif "STOPPED" in resp:
            state = "STOPPED"
        elif "NO_MEDIA_PRESENT" in resp:
            state = "NO_MEDIA_PRESENT"
    return {"ok": status == 200, "state": state, "http_status": status}

def main():
    parser = argparse.ArgumentParser(description="Stream audio to Yamaha RX-V673 via DLNA UPnP.")
    parser.add_argument("action", choices=["play", "stop", "status"], help="Action to execute")
    parser.add_argument("--url", help="HTTP URL of the audio file to stream")
    parser.add_argument("--title", default="Calibration Sweep", help="Display title on AVR screen")
    parser.add_argument("--host", default=DEFAULT_AVR_IP, help="Yamaha AVR IP address")
    parser.add_argument("--restore-input", default="AV4", help="Input to restore on stop (e.g. AV4)")
    args = parser.parse_args()

    if args.action == "status":
        st = get_avr_transport_status(host=args.host)
        print(f"Estado de Transporte Yamaha DLNA: {st['state']}")
    elif args.action == "play":
        if not args.url:
            local_ip = get_local_lan_ip(args.host)
            args.url = f"http://{local_ip}:53317/audio/sweep_signal.wav"
            print(f"[*] URL por defecto: {args.url}")
        ok, msg = stream_audio_to_avr(args.url, title=args.title, host=args.host)
        print(f"[{'✓' if ok else '✗'}] {msg}")
    elif args.action == "stop":
        ok, msg = stop_avr_stream(host=args.host, restore_input=args.restore_input)
        print(f"[{'✓' if ok else '✗'}] Detenido. Entrada restaurada a {args.restore_input}.")

if __name__ == "__main__":
    main()
