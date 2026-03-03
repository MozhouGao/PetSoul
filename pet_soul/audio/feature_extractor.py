"""
Audio Feature Extraction — MFCC-based representation of pet vocalisations.

Extracts Mel-Frequency Cepstral Coefficients and aggregate statistics
from audio clips (barks, meows, whines) to build a vocal personality
fingerprint.
"""

import logging
from typing import Dict, Optional

import numpy as np

from pet_soul.config import CONFIG

logger = logging.getLogger(__name__)


def load_audio(path: str, sr: int = CONFIG.audio_sample_rate) -> np.ndarray:
    """Load an audio file and return a mono waveform.

    Uses librosa if available, falls back to scipy.io.wavfile for WAV files.

    Returns:
        1-D float32 numpy array normalised to [-1, 1].
    """
    try:
        import librosa
        y, _ = librosa.load(path, sr=sr, mono=True)
        return y
    except ImportError:
        pass

    # Fallback for plain WAV files
    from scipy.io import wavfile
    file_sr, data = wavfile.read(path)
    if data.ndim > 1:
        data = data.mean(axis=1)
    data = data.astype(np.float32)
    if data.max() > 1.0:
        data /= 32768.0
    # Resample if needed (simple decimation — crude but zero-dependency)
    if file_sr != sr:
        ratio = sr / file_sr
        indices = np.round(np.arange(0, len(data), 1 / ratio)).astype(int)
        indices = indices[indices < len(data)]
        data = data[indices]
    return data


def extract_mfcc(
    waveform: np.ndarray,
    sr: int = CONFIG.audio_sample_rate,
    n_mfcc: int = CONFIG.audio_n_mfcc,
    hop_length: int = CONFIG.audio_hop_length,
) -> np.ndarray:
    """Extract MFCC features from a waveform.

    Returns:
        Array of shape ``(n_mfcc, T)`` where T = number of frames.
    """
    try:
        import librosa
        mfcc = librosa.feature.mfcc(
            y=waveform, sr=sr, n_mfcc=n_mfcc, hop_length=hop_length
        )
        return mfcc
    except ImportError:
        logger.warning("librosa not installed — returning empty MFCC")
        return np.zeros((n_mfcc, 1), dtype=np.float32)


def extract_audio_stats(waveform: np.ndarray, sr: int = CONFIG.audio_sample_rate) -> Dict[str, float]:
    """Compute aggregate audio statistics for a pet vocalisation clip.

    Returns:
        Dictionary with keys:
            - rms_energy: root-mean-square amplitude
            - zero_crossing_rate: average ZCR (proxy for pitch/noise)
            - spectral_centroid: brightness of the sound
            - duration_sec: clip length in seconds
            - peak_amplitude: loudest sample
    """
    if len(waveform) == 0:
        return _empty_stats()

    rms = float(np.sqrt(np.mean(waveform ** 2)))
    zcr = float(np.mean(np.abs(np.diff(np.sign(waveform))) > 0))
    peak = float(np.max(np.abs(waveform)))
    duration = len(waveform) / sr

    # Spectral centroid (simple FFT-based)
    fft_mag = np.abs(np.fft.rfft(waveform))
    freqs = np.fft.rfftfreq(len(waveform), d=1.0 / sr)
    total_mag = fft_mag.sum() + 1e-9
    spectral_centroid = float(np.sum(freqs * fft_mag) / total_mag)

    return {
        "rms_energy": round(rms, 6),
        "zero_crossing_rate": round(zcr, 6),
        "spectral_centroid": round(spectral_centroid, 2),
        "duration_sec": round(duration, 3),
        "peak_amplitude": round(peak, 6),
    }


def _empty_stats() -> Dict[str, float]:
    return {
        "rms_energy": 0.0,
        "zero_crossing_rate": 0.0,
        "spectral_centroid": 0.0,
        "duration_sec": 0.0,
        "peak_amplitude": 0.0,
    }
