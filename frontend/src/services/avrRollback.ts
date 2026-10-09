import { yamahaDirect } from './yamahaDirect';

export interface AvrSnapshot {
  timestamp: number;
  power: string;
  input: string;
  volumeDb: number;
  peqMode: string;
  pattern1Xml?: string;
}

const SNAPSHOT_KEY = 'octave_pre_flight_snapshot';

export class AvrRollbackService {
  /**
   * Captures the full receiver operational and PEQ NVRAM state before calibration begins.
   */
  async captureSnapshot(): Promise<AvrSnapshot | null> {
    try {
      // 1. Basic Status query
      const statusXml = `<YAMAHA_AV cmd="GET"><Main_Zone><Basic_Status>GetParam</Basic_Status></Main_Zone></YAMAHA_AV>`;
      const statusResp = await yamahaDirect.sendYncXml(statusXml);

      const pMatch = statusResp.match(/<Power>(.*?)<\/Power>/);
      const inMatch = statusResp.match(/<Input_Sel>(.*?)<\/Input_Sel>/);
      const volMatch = statusResp.match(/<Val>(-?\d+)<\/Val>/);

      // 2. Full Pattern_1 PEQ & Speaker Preout query
      let pattern1Xml = '';
      try {
        const peqQuery = `<YAMAHA_AV cmd="GET"><System><Speaker_Preout><Pattern_1>GetParam</Pattern_1></Speaker_Preout></System></YAMAHA_AV>`;
        pattern1Xml = await yamahaDirect.sendYncXml(peqQuery);
      } catch {}

      // 3. Active PEQ Mode query
      let peqMode = 'Through';
      try {
        const peqSelQuery = `<YAMAHA_AV cmd="GET"><System><Speaker_Preout><Pattern_1><PEQ><Sel>GetParam</Sel></PEQ></Pattern_1></Speaker_Preout></System></YAMAHA_AV>`;
        const peqSelResp = await yamahaDirect.sendYncXml(peqSelQuery);
        const peqMatch = peqSelResp.match(/<Sel>(.*?)<\/Sel>/);
        if (peqMatch) peqMode = peqMatch[1];
      } catch {}

      const snapshot: AvrSnapshot = {
        timestamp: Date.now(),
        power: pMatch ? pMatch[1] : 'On',
        input: inMatch ? inMatch[1] : 'AV4',
        volumeDb: volMatch ? parseInt(volMatch[1], 10) / 10 : -40.0,
        peqMode,
        pattern1Xml,
      };

      if (typeof localStorage !== 'undefined') {
        localStorage.setItem(SNAPSHOT_KEY, JSON.stringify(snapshot));
      }

      return snapshot;
    } catch (e) {
      console.warn('Fallo al capturar snapshot de seguridad de Yamaha:', e);
      return null;
    }
  }

  /**
   * Restores the receiver to the pre-calibration state saved in the snapshot.
   */
  async restoreSnapshot(): Promise<boolean> {
    try {
      if (typeof localStorage === 'undefined') return false;
      const raw = localStorage.getItem(SNAPSHOT_KEY);
      if (!raw) return false;

      const snapshot: AvrSnapshot = JSON.parse(raw);

      // 1. Restore PEQ Matrix if saved
      if (snapshot.pattern1Xml && snapshot.pattern1Xml.includes('<Pattern_1>')) {
        const putPatternXml = `<YAMAHA_AV cmd="PUT"><System><Speaker_Preout>${snapshot.pattern1Xml}</Speaker_Preout></System></YAMAHA_AV>`;
        await yamahaDirect.sendYncXml(putPatternXml).catch(() => {});
      }

      // 2. Restore PEQ Mode
      const validMode = (['Manual', 'Flat', 'Natural', 'Through'] as const).find(m => m.toLowerCase() === snapshot.peqMode.toLowerCase()) || 'Through';
      await yamahaDirect.setPeqMode(validMode).catch(() => {});

      // 3. Restore Input and Volume
      await yamahaDirect.setInput(snapshot.input).catch(() => {});
      await yamahaDirect.setVolume(snapshot.volumeDb, true).catch(() => {});

      return true;
    } catch (e) {
      console.error('Error restaurando snapshot en Yamaha:', e);
      return false;
    }
  }

  isSnapshotAvailable(): boolean {
    return typeof localStorage !== 'undefined' && localStorage.getItem(SNAPSHOT_KEY) !== null;
  }
}

export const avrRollback = new AvrRollbackService();
