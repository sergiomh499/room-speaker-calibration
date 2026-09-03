"""
tests/conftest.py
Pytest fixtures for honest acoustic engine tests, benchmark impulse responses, and discrete hardware tables.
"""

import os
import sys
from pathlib import Path
import pytest
import numpy as np

# Ensure project root is in sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

@pytest.fixture
def sample_freq_grid():
    """Standard logarithmic frequency grid from 20 Hz to 20 kHz (1200 points)."""
    return np.logspace(np.log10(20.0), np.log10(20000.0), 1200)

@pytest.fixture
def synthetic_room_impulse():
    """
    Generates a realistic physical-like domestic room impulse response:
    - 48 kHz sampling rate, 1.0 second duration (48000 samples).
    - Prominent room modal ringing at 63.5 Hz (Q ~ 8) and 112.5 Hz (Q ~ 10).
    - Reverberation time RT60 ~ 0.4s.
    """
    fs = 48000
    duration = 0.5
    t = np.linspace(0, duration, int(fs * duration), endpoint=False)
    
    # Direct sound impulse
    ir = np.zeros_like(t)
    ir[480] = 1.0  # 10ms arrival
    
    # Room modes (decaying sinusoids)
    mode1 = 0.4 * np.exp(-t * 8.0) * np.sin(2 * np.pi * 63.5 * t)
    mode2 = 0.6 * np.exp(-t * 12.0) * np.sin(2 * np.pi * 112.5 * t)
    mode3 = 0.3 * np.exp(-t * 18.0) * np.sin(2 * np.pi * 238.0 * t)
    
    # Early reflections
    ir[580] = 0.3
    ir[720] = -0.25
    ir[950] = 0.18
    
    # Diffuse tail
    np.random.seed(42)
    tail = 0.05 * np.exp(-t * 15.0) * np.random.randn(len(t))
    
    ir = ir + mode1 + mode2 + mode3 + tail
    ir = ir / np.max(np.abs(ir)) * 0.5  # Normalize to safe -6 dBFS peak
    return ir, fs

@pytest.fixture
def harman_target_curve(sample_freq_grid):
    """
    Harman In-Room Target Curve:
    +4.5 dB bass shelf below 100 Hz, flat 200 Hz - 1 kHz, -0.8 dB/octave tilt above 1 kHz.
    """
    target = np.zeros_like(sample_freq_grid)
    for i, f in enumerate(sample_freq_grid):
        if f < 100.0:
            target[i] = 4.5
        elif f < 200.0:
            target[i] = 4.5 * (1.0 - (f - 100.0) / 100.0)
        elif f <= 1000.0:
            target[i] = 0.0
        else:
            target[i] = -0.8 * np.log2(f / 1000.0)
    return sample_freq_grid, target

@pytest.fixture
def temp_epoch_dir(tmp_path):
    """Isolated temporary directory for calibration epochs."""
    epoch_dir = tmp_path / "epochs"
    epoch_dir.mkdir(parents=True, exist_ok=True)
    return epoch_dir
