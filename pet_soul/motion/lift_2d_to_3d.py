"""
2D → 3D Pose Lifting — lightweight MLP model.

Converts 2D keypoint sequences (T, J, 2) into 3D skeleton trajectories
(T, J, 3) by predicting a depth coordinate for each joint.

The model is intentionally small (<1M parameters) so it trains and
runs comfortably on Apple M2 or CPU.
"""

import logging
from pathlib import Path
from typing import Optional

import numpy as np
import torch
import torch.nn as nn

from pet_soul.config import CONFIG
from pet_soul.motion.pose_extractor import NUM_KEYPOINTS

logger = logging.getLogger(__name__)


class PoseLifter(nn.Module):
    """MLP that predicts depth (z) from 2D keypoint positions."""

    def __init__(
        self,
        num_joints: int = NUM_KEYPOINTS,
        hidden_dim: int = 256,
    ):
        super().__init__()
        input_dim = num_joints * 2  # x, y per joint
        output_dim = num_joints     # z per joint

        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim, output_dim),
        )

    def forward(self, xy: torch.Tensor) -> torch.Tensor:
        """
        Args:
            xy: (batch, num_joints * 2) — flattened 2D keypoints.

        Returns:
            z: (batch, num_joints) — predicted depth per joint.
        """
        return self.net(xy)


def lift_sequence(
    keypoints_2d: np.ndarray,
    model: Optional[PoseLifter] = None,
    weights_path: Optional[str] = None,
) -> np.ndarray:
    """Lift a full 2D keypoint sequence to 3D.

    Args:
        keypoints_2d: (T, J, 2) or (T, J, 3) array.  If 3-channel the
            third column (visibility) is stripped before lifting.
        model: Pre-loaded PoseLifter model, or None to create a new one.
        weights_path: Optional path to trained weights file.

    Returns:
        keypoints_3d: (T, J, 3) — x, y, predicted-z.
    """
    T, J = keypoints_2d.shape[0], keypoints_2d.shape[1]
    xy = keypoints_2d[:, :, :2].reshape(T, -1)  # (T, J*2)

    if model is None:
        model = PoseLifter(num_joints=J)
        if weights_path and Path(weights_path).exists():
            model.load_state_dict(torch.load(weights_path, map_location="cpu"))
            logger.info("Loaded lifter weights from %s", weights_path)
        else:
            logger.info("Using untrained lifter — output will be heuristic depth")

    model.eval()
    with torch.no_grad():
        xy_t = torch.from_numpy(xy).float()
        z = model(xy_t).numpy()  # (T, J)

    # Combine x, y, z
    keypoints_3d = np.zeros((T, J, 3), dtype=np.float32)
    keypoints_3d[:, :, :2] = keypoints_2d[:, :, :2]
    keypoints_3d[:, :, 2] = z

    return keypoints_3d


def smooth_trajectory(
    keypoints_3d: np.ndarray,
    window_length: int = 7,
    polyorder: int = 2,
) -> np.ndarray:
    """Apply Savitzky-Golay temporal smoothing to 3D keypoints.

    Args:
        keypoints_3d: (T, J, 3)
        window_length: Filter window (must be odd).
        polyorder: Polynomial order.

    Returns:
        Smoothed (T, J, 3) array.
    """
    from scipy.signal import savgol_filter

    T = keypoints_3d.shape[0]
    if T < window_length:
        return keypoints_3d

    smoothed = np.copy(keypoints_3d)
    for j in range(keypoints_3d.shape[1]):
        for c in range(3):
            smoothed[:, j, c] = savgol_filter(
                keypoints_3d[:, j, c], window_length, polyorder
            )
    return smoothed
