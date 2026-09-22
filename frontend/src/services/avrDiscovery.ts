import { registerPlugin, Capacitor } from '@capacitor/core';
import { yamahaDirect } from './yamahaDirect';

export interface DiscoveredAvr {
  ip: string;
  model: string;
  version: string;
}

interface AvrDiscoveryPluginInterface {
  discover(): Promise<{ devices: DiscoveredAvr[] }>;
}

const AvrDiscovery = registerPlugin<AvrDiscoveryPluginInterface>('AvrDiscovery');

class AvrDiscoveryService {
  /**
   * Ejecuta el auto-descubrimiento en la red local:
   * 1. Mediante el plugin nativo SSDP M-SEARCH (UPnP/DLNA) en Android.
   * 2. Si es navegador web o falla SSDP, prueba secuencialmente la IP habitual (192.168.1.43).
   */
  async discover(): Promise<DiscoveredAvr[]> {
    if (Capacitor.isNativePlatform() && Capacitor.isPluginAvailable('AvrDiscovery')) {
      try {
        const res = await AvrDiscovery.discover();
        if (res.devices && res.devices.length > 0) {
          // Asignar automáticamente la IP encontrada a yamahaDirect
          yamahaDirect.setIp(res.devices[0].ip);
          localStorage.setItem('octave_avr_ip', res.devices[0].ip);
          return res.devices;
        }
      } catch (e) {
        console.warn('AvrDiscovery nativo falló:', e);
      }
    }

    // Modo web o fallback: probar IP por defecto
    const defaultIp = localStorage.getItem('octave_avr_ip') || '192.168.1.43';
    try {
      const xml = '<YAMAHA_AV cmd="GET"><System><Config>GetParam</Config></System></YAMAHA_AV>';
      const resp = await yamahaDirect.sendYncXml(xml);
      if (resp && resp.includes('RX-V673')) {
        yamahaDirect.setIp(defaultIp);
        return [{ ip: defaultIp, model: 'RX-V673', version: '1.0' }];
      }
    } catch {}

    return [];
  }
}

export const avrDiscovery = new AvrDiscoveryService();
