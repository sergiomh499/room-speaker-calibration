import { Capacitor, CapacitorHttp } from '@capacitor/core';


export const YAMAHA_DEFAULT_IP = '192.168.1.43';

export class YamahaDirectController {
  private ip: string;

  constructor(ip: string = YAMAHA_DEFAULT_IP) {
    this.ip = ip;
  }

  setIp(newIp: string) {
    this.ip = newIp;
  }

  getIp(): string {
    return this.ip;
  }

  /**
   * Envía un comando XML crudo al endpoint YNC del receptor Yamaha RX-V673.
   * Utiliza CapacitorHttp nativo en Android (sin restricciones CORS ni Mixed Content)
   * o el proxy del servidor si se ejecuta en navegador web de escritorio.
   */
  async sendYncXml(xml: string): Promise<string> {
    const url = `http://${this.ip}/YamahaRemoteControl/ctrl`;

    if (Capacitor.isNativePlatform()) {
      const response = await CapacitorHttp.post({
        url,
        data: xml,
        headers: {
          'Content-Type': 'text/xml; charset=utf-8',
          'User-Agent': 'AV_Receiver/3.1'
        }
      });
      return response.data;
    }

    // Modo navegador: enviar a través de proxy local del servidor
    const resp = await fetch('/api/send_cmd', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ xml, host: this.ip })
    });
    const json = await resp.json();
    return json.res || '';
  }

  /**
   * Cambia el volumen maestro en decibelios (ej. -30.0 dB).
   */
  async setVolume(volumeDb: number): Promise<boolean> {
    const val = Math.round(volumeDb * 10);
    const xml = `<YAMAHA_AV cmd="PUT"><Main_Zone><Volume><Lvl><Val>${val}</Val><Exp>1</Exp><Unit>dB</Unit></Lvl></Volume></Main_Zone></YAMAHA_AV>`;
    await this.sendYncXml(xml);
    return true;
  }

  /**
   * Conmuta la entrada activa del receptor (AV4, SERVER, V-AUX, HDMI1..5, etc.).
   */
  async setInput(input: string): Promise<boolean> {
    const xml = `<YAMAHA_AV cmd="PUT"><Main_Zone><Input><Input_Sel>${input}</Input_Sel></Input></Main_Zone></YAMAHA_AV>`;
    await this.sendYncXml(xml);
    return true;
  }

  /**
   * Activa una de las 4 escenas de hardware memorizadas en el receptor (1 a 4).
   */
  async selectScene(num: number): Promise<boolean> {
    const xml = `<YAMAHA_AV cmd="PUT"><Main_Zone><Scene><Scene_Sel>Scene ${num}</Scene_Sel></Main_Zone></YAMAHA_AV>`;
    await this.sendYncXml(xml);
    return true;
  }

  /**
   * Activa o desactiva Pure Direct.
   */
  async setPureDirect(enabled: boolean): Promise<boolean> {
    const mode = enabled ? 'On' : 'Off';
    const xml = `<YAMAHA_AV cmd="PUT"><Main_Zone><Sound_Video><Pure_Direct><Mode>${mode}</Mode></Pure_Direct></Sound_Video></Main_Zone></YAMAHA_AV>`;
    await this.sendYncXml(xml);
    return true;
  }

  /**
   * Configura el modo del ecualizador paramétrico (PEQ): Manual, Flat, Natural, Through.
   */
  async setPeqMode(mode: 'Manual' | 'Flat' | 'Natural' | 'Through'): Promise<boolean> {
    const xml = `<YAMAHA_AV cmd="PUT"><System><Speaker_Preout><Pattern_1><PEQ><Actual><Sel>${mode}</Sel></Actual></PEQ></Pattern_1></Speaker_Preout></System></YAMAHA_AV>`;
    await this.sendYncXml(xml);
    return true;
  }

  /**
   * Envía un flujo de audio DLNA DMR al receptor (puerto 8080).
   */
  async playDlnaStream(audioUrl: string, title: string = 'Calibración Acústica'): Promise<boolean> {
    const didl = `<DIDL-Lite xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/">
<item id="1" parentID="0" restricted="1">
<dc:title>${title}</dc:title>
<upnp:class>object.item.audioItem.musicTrack</upnp:class>
<res protocolInfo="http-get:*:audio/wav:DLNA.ORG_PN=LPCM">${audioUrl}</res>
</item>
</DIDL-Lite>`;

    // 1. Cambiar a SERVER
    await this.setInput('SERVER');

    // 2. SetAVTransportURI
    const bodySetUri = `<?xml version="1.0" encoding="utf-8"?>
<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
  <s:Body>
    <u:SetAVTransportURI xmlns:u="urn:schemas-upnp-org:service:AVTransport:1">
      <InstanceID>0</InstanceID>
      <CurrentURI>${audioUrl}</CurrentURI>
      <CurrentURIMetaData><![CDATA[${didl}]]></CurrentURIMetaData>
    </u:SetAVTransportURI>
  </s:Body>
</s:Envelope>`;

    const urlCtrl = `http://${this.ip}:8080/AVTransport/ctrl`;
    if (Capacitor.isNativePlatform()) {
      await CapacitorHttp.post({
        url: urlCtrl,
        data: bodySetUri,
        headers: {
          'Content-Type': 'text/xml; charset="utf-8"',
          'SOAPAction': '"urn:schemas-upnp-org:service:AVTransport:1#SetAVTransportURI"'
        }
      });

      // 3. Play
      const bodyPlay = `<?xml version="1.0" encoding="utf-8"?>
<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
  <s:Body>
    <u:Play xmlns:u="urn:schemas-upnp-org:service:AVTransport:1">
      <InstanceID>0</InstanceID>
      <Speed>1</Speed>
    </u:Play>
  </s:Body>
</s:Envelope>`;

      await CapacitorHttp.post({
        url: urlCtrl,
        data: bodyPlay,
        headers: {
          'Content-Type': 'text/xml; charset="utf-8"',
          'SOAPAction': '"urn:schemas-upnp-org:service:AVTransport:1#Play"'
        }
      });
      return true;
    }

    // Vía backend
    const resp = await fetch('/api/stream_to_avr', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ file: audioUrl, host: this.ip, title })
    });
    const res = await resp.json();
    return !!res.ok;
  }
}

export const yamahaDirect = new YamahaDirectController();
