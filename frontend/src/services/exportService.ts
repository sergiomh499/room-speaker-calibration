import type { CalibrationSession } from '../types';

export class ExportService {
  /**
   * Generates a CSV string containing all frequency response curves from a calibration session.
   */
  generateCurvesCsv(session: CalibrationSession): string {
    const freqs = session.verification?.freqs || [
      31.3, 39.4, 49.6, 62.5, 78.7, 99.2, 125.0, 157.5,
      198.4, 250.0, 315.0, 396.9, 500.0, 630.0, 793.7, 1000.0,
      1260.0, 1590.0, 2000.0, 2520.0, 3170.0, 4000.0, 5040.0, 6350.0,
      8000.0, 10100.0, 12700.0, 16000.0,
    ];

    const lines: string[] = [];
    lines.push('frequency_hz,target_db,baseline_db,filter_response_db,verified_db');

    for (let i = 0; i < freqs.length; i++) {
      const f = freqs[i];
      const tgt = session.verification?.targetDb?.[i] ?? 0.0;
      const base = session.verification?.baselineDb?.[i] ?? 0.0;
      const flt = session.verification?.filterResponseDb?.[i] ?? 0.0;
      const ver = session.verification?.verifiedDb?.[i] ?? 0.0;
      lines.push(`${f},${tgt.toFixed(1)},${base.toFixed(1)},${flt.toFixed(1)},${ver.toFixed(1)}`);
    }

    return lines.join('\n');
  }

  /**
   * Triggers download of the session JSON archive.
   */
  downloadSessionJson(session: CalibrationSession): void {
    const jsonStr = JSON.stringify(session, null, 2);
    const blob = new Blob([jsonStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `Octave_Calibration_${session.id.slice(0, 8)}_${session.targetProfileId}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  /**
   * Triggers download of the curves CSV data.
   */
  downloadCurvesCsv(session: CalibrationSession): void {
    const csvStr = this.generateCurvesCsv(session);
    const blob = new Blob([csvStr], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `Octave_Curves_${session.id.slice(0, 8)}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }
}

export const exportService = new ExportService();
