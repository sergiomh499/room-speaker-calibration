import { Capacitor, CapacitorHttp } from '@capacitor/core';

export const YAMAHA_DEFAULT_IP = '192.168.1.43';

export class YamahaDirectController {
  private ip: string;
  private volumeDebounceTimer: any = null;
  private pendingTargetVolume: number | null = null;
  private isSendingVolume = false;

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
   * Envía un comando XML al endpoint YNC del receptor Yamaha RX-V673.
   * Utiliza CapacitorHttp nativo en Android (sin CORS) o fetch directo.
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
        },
        connectTimeout: 4000,
        readTimeout: 5000,
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
   * Cambia el volumen maestro de forma reactiva con debounce de 60ms.
   * Si el usuario pulsa [+] o [-] repetidas veces rápido, no satura el puerto HTTP
   * del Yamaha con 10 conexiones encoladas, sino que envía el valor acumulado final al instante.
   */
  async setVolume(volumeDb: number, immediate = false): Promise<boolean> {
    this.pendingTargetVolume = volumeDb;
    if (immediate) {
      clearTimeout(this.volumeDebounceTimer);
      return this._flushVolume();
    }

    clearTimeout(this.volumeDebounceTimer);
    this.volumeDebounceTimer = setTimeout(() => {
      this._flushVolume();
    }, 60);
    return true;
  }

  private async _flushVolume(): Promise<boolean> {
    if (this.pendingTargetVolume === null || this.isSendingVolume) return false;
    const target = this.pendingTargetVolume;
    this.pendingTargetVolume = null;
    this.isSendingVolume = true;

    try {
      const val = Math.round(target * 10);
      const xml = `<YAMAHA_AV cmd="PUT"><Main_Zone><Volume><Lvl><Val>${val}</Val><Exp>1</Exp><Unit>dB</Unit></Lvl></Volume></Main_Zone></YAMAHA_AV>`;
      await this.sendYncXml(xml);
      return true;
    } catch (e) {
      console.warn('Error enviando volumen a Yamaha:', e);
      return false;
    } finally {
      this.isSendingVolume = false;
      // Si mientras se enviaba se acumuló otra pulsación, despacharla
      if (this.pendingTargetVolume !== null) {
        this._flushVolume();
      }
    }
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
  async playDlnaStream(audioUrl: string, title: string = 'Calibración Acústica', contentType: string = 'audio/wav'): Promise<boolean> {
    // Map MIME → DLNA PN
    const dlnaPn: Record<string, string> = {
      'audio/wav': 'LPCM', 'audio/x-wav': 'LPCM',
      'audio/mpeg': 'MP3', 'audio/mp3': 'MP3',
      'audio/flac': 'FLAC', 'audio/x-flac': 'FLAC',
      'audio/ogg': 'OGG', 'audio/aac': 'AAC_ISO',
    };
    const pn = dlnaPn[contentType] ?? 'MP3';
    const protocolInfo = `http-get:*:${contentType}:DLNA.ORG_PN=${pn}`;

    // Automatically route any non-local URL through local proxy to avoid Yamaha HTTPS/Access error
    let targetUrl = audioUrl;
    if (!audioUrl.startsWith('http://192.168.') && !audioUrl.startsWith('http://127.0.0.1')) {
      const serverUrl = localStorage.getItem('octave_server_url') || 'http://192.168.1.45:53317';
      targetUrl = `${serverUrl}/api/stream_proxy?url=${encodeURIComponent(audioUrl)}`;
    }

    const didl = `<DIDL-Lite xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/">
<item id="1" parentID="0" restricted="1">
<dc:title>${title}</dc:title>
<upnp:class>object.item.audioItem.musicTrack</upnp:class>
<res protocolInfo="${protocolInfo}">${targetUrl}</res>
</item>
</DIDL-Lite>`;

    await this.setInput('SERVER');

    const urlCtrl = `http://${this.ip}:8080/AVTransport/ctrl`;

    // 1. Send Stop first to flush buffer and avoid playing residual sweep audio
    const bodyStop = `<?xml version="1.0" encoding="utf-8"?>
<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
  <s:Body><u:Stop xmlns:u="urn:schemas-upnp-org:service:AVTransport:1"><InstanceID>0</InstanceID></u:Stop></s:Body>
</s:Envelope>`;

    const bodySetUri = `<?xml version="1.0" encoding="utf-8"?>
<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
  <s:Body>
    <u:SetAVTransportURI xmlns:u="urn:schemas-upnp-org:service:AVTransport:1">
      <InstanceID>0</InstanceID>
      <CurrentURI>${targetUrl}</CurrentURI>
      <CurrentURIMetaData><![CDATA[${didl}]]></CurrentURIMetaData>
  </s:Body>
</s:Envelope>`;

    const bodyPlay = `<?xml version="1.0" encoding="utf-8"?>
<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
  <s:Body>
    <u:Play xmlns:u="urn:schemas-upnp-org:service:AVTransport:1">
      <InstanceID>0</InstanceID>
      <Speed>1</Speed>
    </u:Play>
  </s:Body>
</s:Envelope>`;

    if (Capacitor.isNativePlatform()) {
      try {
        await CapacitorHttp.post({
          url: urlCtrl,
          data: bodyStop,
          headers: { 'Content-Type': 'text/xml; charset="utf-8"', 'SOAPAction': '"urn:schemas-upnp-org:service:AVTransport:1#Stop"' }
        });
      } catch {}
      await CapacitorHttp.post({
        url: urlCtrl,
        data: bodySetUri,
        headers: { 'Content-Type': 'text/xml; charset="utf-8"', 'SOAPAction': '"urn:schemas-upnp-org:service:AVTransport:1#SetAVTransportURI"' }
      });
      await new Promise(r => setTimeout(r, 400));
      await CapacitorHttp.post({
        url: urlCtrl,
        data: bodyPlay,
        headers: { 'Content-Type': 'text/xml; charset="utf-8"', 'SOAPAction': '"urn:schemas-upnp-org:service:AVTransport:1#Play"' }
      });
      return true;
    }
    // Browser: delegate to backend
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
