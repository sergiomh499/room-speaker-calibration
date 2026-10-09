import type { CalibrationSession } from '../types';

const STORAGE_KEY = 'octave_calibration_sessions';

export class StorageService {
  /**
   * Retrieves all saved calibration sessions ordered by timestamp descending.
   */
  getSessions(): CalibrationSession[] {
    if (typeof localStorage === 'undefined') return [];
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return [];
      const parsed: CalibrationSession[] = JSON.parse(raw);
      return Array.isArray(parsed) ? parsed.sort((a, b) => Date.parse(b.createdAt) - Date.parse(a.createdAt)) : [];
    } catch {
      return [];
    }
  }

  /**
   * Retrieves a specific calibration session by its unique UUID.
   */
  getSessionById(id: string): CalibrationSession | null {
    const sessions = this.getSessions();
    return sessions.find(s => s.id === id) || null;
  }

  /**
   * Saves or updates a calibration session.
   */
  saveSession(session: CalibrationSession): void {
    if (typeof localStorage === 'undefined') return;
    const sessions = this.getSessions();
    const existingIndex = sessions.findIndex(s => s.id === session.id);
    if (existingIndex >= 0) {
      sessions[existingIndex] = session;
    } else {
      sessions.unshift(session);
    }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions));
  }

  /**
   * Deletes a calibration session.
   */
  deleteSession(id: string): boolean {
    if (typeof localStorage === 'undefined') return false;
    const sessions = this.getSessions().filter(s => s.id !== id);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions));
    return true;
  }
}

export const storageService = new StorageService();
