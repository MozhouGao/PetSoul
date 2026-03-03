"""
Pose Extraction — MediaPipe-based 2D keypoint detection for pets.

Uses the MediaPipe Pose model as a starting point. For animal-specific
pose estimation a fine-tuned DeepLabCut model can be swapped in later
via the ``backend`` parameter.
"""

import logging
from pathlib import Path
from typing import Optional

import cv2
import numpy as np

from pet_soul.config import CONFIG

logger = logging.getLogger(__name__)

# Keypoint indices used for pet motion (mapped from MediaPipe human skeleton)
# In production these would come from DeepLabCut animal keypoints.
PET_KEYPOINT_NAMES = [
    "nose", "left_eye", "right_eye", "left_ear", "right_ear",
    "left_shoulder", "right_shoulder", "left_hip", "right_hip",
    "left_front_paw", "right_front_paw", "left_back_paw", "right_back_paw",
    "tail_base",
]

NUM_KEYPOINTS = len(PET_KEYPOINT_NAMES)


class PoseExtractor:
    """Extract 2D pose keypoints from video frames.

    Attributes:
        backend: ``"mediapipe"`` (default) or ``"deeplabcut"``.
    """

    def __init__(self, backend: str = "mediapipe"):
        self.backend = backend
        self._mp_pose = None

        if backend == "mediapipe":
            self._init_mediapipe()

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------

    def _init_mediapipe(self):
        try:
            import mediapipe as mp
            self._mp_pose = mp.solutions.pose.Pose(
                static_image_mode=False,
                model_complexity=1,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5,
            )
            logger.info("MediaPipe Pose initialised")
        except ImportError:
            logger.warning("mediapipe not installed — PoseExtractor will return empty keypoints")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def extract_from_frame(self, frame: np.ndarray) -> np.ndarray:
        """Extract keypoints from a single BGR/RGB frame.

        Returns:
            Array of shape ``(NUM_KEYPOINTS, 3)`` — x, y in normalised coords,
            visibility score. Returns zeros if detection fails.
        """
        if self._mp_pose is None:
            return np.zeros((NUM_KEYPOINTS, 3), dtype=np.float32)

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) if frame.shape[2] == 3 else frame
        results = self._mp_pose.process(rgb)

        if results.pose_landmarks is None:
            return np.zeros((NUM_KEYPOINTS, 3), dtype=np.float32)

        # Map MediaPipe human landmarks to our pet keypoint set.
        # This is approximate — a real animal model (DeepLabCut) is preferred.
        lm = results.pose_landmarks.landmark
        mapping = [0, 2, 5, 7, 8, 11, 12, 23, 24, 15, 16, 27, 28, 23]
        keypoints = np.zeros((NUM_KEYPOINTS, 3), dtype=np.float32)
        for i, idx in enumerate(mapping):
            if idx < len(lm):
                keypoints[i] = [lm[idx].x, lm[idx].y, lm[idx].visibility]

        return keypoints

    def extract_from_video(self, video_path: str, max_frames: int = 0) -> np.ndarray:
        """Extract keypoints from every frame of a video file.

        Args:
            video_path: Path to an MP4/AVI video.
            max_frames: If > 0, stop after this many frames.

        Returns:
            Array of shape ``(T, NUM_KEYPOINTS, 3)``.
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            logger.error("Cannot open video: %s", video_path)
            return np.zeros((0, NUM_KEYPOINTS, 3), dtype=np.float32)

        all_keypoints = []
        frame_count = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break
            kp = self.extract_from_frame(frame)
            all_keypoints.append(kp)
            frame_count += 1
            if max_frames > 0 and frame_count >= max_frames:
                break

        cap.release()
        logger.info("Extracted keypoints from %d frames of %s", frame_count, video_path)

        if not all_keypoints:
            return np.zeros((0, NUM_KEYPOINTS, 3), dtype=np.float32)

        return np.stack(all_keypoints)

    def close(self):
        if self._mp_pose is not None:
            self._mp_pose.close()
            self._mp_pose = None
