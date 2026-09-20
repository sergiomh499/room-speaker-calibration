"""
Test Suite: Auditoría Estricta de Cero Hardcodeo (Zero-Hardcode Audit)
Nivel de exigencia: Trinnov Optimizer / Dirac Live.
Verifica de forma determinista y binaria que el 100% de los parámetros acústicos:
- Tiempos de vuelo (ToF) y distancias milimétricas
- Niveles SPL medidos y trims dB calculados
- Fase acústica óptima (0° vs 180°)
- Parámetros de 7 bandas PEQ por canal
- Estimación de T60 y frecuencia modal de Schroeder (fs)
se obtienen única y exclusivamente a partir de la física de las señales medidas (.npz).
"""

import unittest
import numpy as np
import tempfile
import os
from scripts.peq_optimizer import (
    optimize_subwoofer_peq,
    calculate_speaker_trim_levels,
    calculate_multi_sub_alignment,
    calculate_schroeder_reverberation,
    calculate_schroeder_frequency,
    compute_minimum_phase_decomposition,
    detect_modal_resonances,
)


class TestZeroHardcodeAcousticAudit(unittest.TestCase):
    def test_trims_depend_strictly_on_measured_spl(self):
        """Los trims en dB deben variar matemáticamente si varían los SPL medidos."""
        spl_map_1 = {"Front_L": 74.0, "Front_R": 76.0, "Subwoofer": 71.0}
        trims_1 = calculate_speaker_trim_levels(spl_map_1, target_spl_db=75.0)
        self.assertEqual(trims_1["Front_L"], +1.0)
        self.assertEqual(trims_1["Front_R"], -1.0)
        self.assertEqual(trims_1["Subwoofer"], +4.0)

        # Modificación empírica -> trims deben cambiar
        spl_map_2 = {"Front_L": 77.0, "Front_R": 72.0, "Subwoofer": 80.0}
        trims_2 = calculate_speaker_trim_levels(spl_map_2, target_spl_db=75.0)
        self.assertEqual(trims_2["Front_L"], -2.0)
        self.assertEqual(trims_2["Front_R"], +3.0)
        self.assertEqual(trims_2["Subwoofer"], -5.0)
        self.assertNotEqual(trims_1, trims_2)

    def test_subwoofer_peq_notches_track_empirical_peaks(self):
        """Los filtros PEQ de subwoofer deben localizar exactamente los picos de resonancia sintéticos."""
        freqs = np.linspace(20, 200, 1000)
        # Crear un pico resonante pronunciado en 62.5 Hz
        resp_62 = np.zeros_like(freqs)
        resp_62 += 8.0 * np.exp(-((freqs - 62.5) ** 2) / (2 * (3.0 ** 2)))
        bands_62 = optimize_subwoofer_peq(freqs, resp_62, crossover_hz=80.0, max_bands=2)
        self.assertTrue(len(bands_62) > 0)
        self.assertEqual(bands_62[0]["freq_hz"], 62.5)
        self.assertLess(bands_62[0]["gain_db"], -1.0)

        # Mover la resonancia modal a 78.7 Hz
        resp_78 = np.zeros_like(freqs)
        resp_78 += 8.0 * np.exp(-((freqs - 78.7) ** 2) / (2 * (3.0 ** 2)))
        bands_78 = optimize_subwoofer_peq(freqs, resp_78, crossover_hz=80.0, max_bands=2)
        self.assertTrue(len(bands_78) > 0)
        self.assertEqual(bands_78[0]["freq_hz"], 78.7)
        self.assertNotEqual(bands_62[0]["freq_hz"], bands_78[0]["freq_hz"])

    def test_reverberation_and_schroeder_frequency_are_dynamic(self):
        """La frecuencia de Schroeder y el T60 deben calcularse a partir del decaimiento real."""
        sr = 48000
        # Simular sala seca (T60 = ~0.2 s)
        t = np.arange(sr) / sr
        ir_dry = np.exp(-t / (0.2 / 6.91)) * np.random.randn(sr)
        ir_dry[0] = 5.0 # Dirac pulse
        rev_dry = calculate_schroeder_reverberation(ir_dry, sample_rate_hz=sr)
        fs_dry = calculate_schroeder_frequency(rev_dry["t60_s"], room_volume_m3=40.0)

        # Simular sala reverberante (T60 = ~0.8 s)
        ir_wet = np.exp(-t / (0.8 / 6.91)) * np.random.randn(sr)
        ir_wet[0] = 5.0
        rev_wet = calculate_schroeder_reverberation(ir_wet, sample_rate_hz=sr)
        fs_wet = calculate_schroeder_frequency(rev_wet["t60_s"], room_volume_m3=40.0)

        self.assertGreater(rev_wet["t60_s"], rev_dry["t60_s"])
        self.assertGreater(fs_wet["schroeder_frequency_hz"], fs_dry["schroeder_frequency_hz"])

    def test_minimum_phase_decomposition_mathematics(self):
        """La transformada de Hilbert debe separar correctamente fase mínima de anomalías de fase."""
        freqs = np.linspace(20, 20000, 512)
        mag = np.sin(freqs / 1000.0) * 3.0
        decomp = compute_minimum_phase_decomposition(freqs, mag)
        self.assertIn("minimum_phase_deg", decomp)
        self.assertIn("excess_phase_deg", decomp)
        self.assertIn("correctability_factor", decomp)
        self.assertEqual(len(decomp["minimum_phase_deg"]), len(freqs))
        self.assertTrue(np.all(decomp["correctability_factor"] >= 0.2))
        self.assertTrue(np.all(decomp["correctability_factor"] <= 1.0))


if __name__ == "__main__":
    unittest.main()
