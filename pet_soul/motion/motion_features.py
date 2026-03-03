"""
Motion Feature Extraction — handcrafted motion statistics.

Computes a compact, explainable "motion personality" vector from 3D
keypoint sequences. This serves as the cheap-stack personality embedding
(v1) before a learned multimodal transformer is warranted.
"""

import logging
from typing import Dict

import numpy as np

logger = logging.getLogger(__name__)


def compute_motion_stats(keypoints_3d: np.ndarray) -> Dict[str, float]:
    """Compute motion statistics from a 3D keypoint sequence.

    Args:
        keypoints_3d: Array of shape ``(T, J, 3)`` — time, joints, xyz.

    Returns:
        Dictionary of scalar motion features:
            - avg_speed: mean displacement per frame across all joints
            - max_speed: peak joint displacement in any frame
            - movement_entropy: Shannon entropy of speed distribution
            - tail_wag_freq: estimated tail oscillation frequency (Hz at 30fps)
            - head_motion_range: range of nose/head keypoint movement
            - gait_regularity: autocorrelation-based gait periodicity score
    """
    T, J, _ = keypoints_3d.shape

    if T < 2:
        return _empty_stats()

    # Per-frame displacement for each joint
    deltas = np.diff(keypoints_3d, axis=0)              # (T-1, J, 3)
    speeds = np.linalg.norm(deltas, axis=2)              # (T-1, J)

    # --- Aggregate statistics ---
    avg_speed = float(speeds.mean())
    max_speed = float(speeds.max())

    # Movement entropy (how evenly distributed is the motion across time?)
    frame_speeds = speeds.mean(axis=1)                   # (T-1,)
    frame_speeds_norm = frame_speeds / (frame_speeds.sum() + 1e-9)
    movement_entropy = float(-np.sum(
        frame_speeds_norm * np.log(frame_speeds_norm + 1e-9)
    ))

    # Tail wag frequency estimate (tail_base = last keypoint)
    tail_wag_freq = _estimate_oscillation_freq(keypoints_3d[:, -1, 0])

    # Head motion range (nose = first keypoint)
    head_positions = keypoints_3d[:, 0, :]
    head_motion_range = float(
        np.linalg.norm(head_positions.max(axis=0) - head_positions.min(axis=0))
    )

    # Gait regularity via autocorrelation of total speed signal
    gait_regularity = _autocorrelation_peak(frame_speeds)

    return {
        "avg_speed": round(avg_speed, 6),
        "max_speed": round(max_speed, 6),
        "movement_entropy": round(movement_entropy, 4),
        "tail_wag_freq": round(tail_wag_freq, 4),
        "head_motion_range": round(head_motion_range, 6),
        "gait_regularity": round(gait_regularity, 4),
    }


def build_personality_vector(stats: Dict[str, float]) -> np.ndarray:
    """Convert motion stats dict into a fixed-length numpy vector.

    Order matches ``FEATURE_NAMES``.
    """
    return np.array([stats.get(k, 0.0) for k in FEATURE_NAMES], dtype=np.float32)


FEATURE_NAMES = [
    "avg_speed",
    "max_speed",
    "movement_entropy",
    "tail_wag_freq",
    "head_motion_range",
    "gait_regularity",
]


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _empty_stats() -> Dict[str, float]:
    return {k: 0.0 for k in FEATURE_NAMES}


def _estimate_oscillation_freq(signal_1d: np.ndarray, fps: float = 30.0) -> float:
    """Estimate dominant oscillation frequency via FFT."""
    n = len(signal_1d)
    if n < 8:
        return 0.0
    # Remove DC component
    sig = signal_1d - signal_1d.mean()
    fft_mag = np.abs(np.fft.rfft(sig))
    freqs = np.fft.rfftfreq(n, d=1.0 / fps)
    # Ignore DC bin
    if len(fft_mag) > 1:
        peak_idx = np.argmax(fft_mag[1:]) + 1
        return float(freqs[peak_idx])
    return 0.0


def _autocorrelation_peak(signal_1d: np.ndarray) -> float:
    """Compute the height of the first autocorrelation peak (0-1 scale).

    A high value means periodic / regular gait. Low means irregular.
    """
    n = len(signal_1d)
    if n < 4:
        return 0.0
    sig = signal_1d - signal_1d.mean()
    norm = np.dot(sig, sig)
    if norm < 1e-9:
        return 0.0
    autocorr = np.correlate(sig, sig, mode="full")
    autocorr = autocorr[n - 1:] / norm  # normalise, keep positive lags

    # Find first peak after lag 0
    for i in range(2, len(autocorr) - 1):
        if autocorr[i] > autocorr[i - 1] and autocorr[i] > autocorr[i + 1]:
            return float(autocorr[i])
    return 0.0
