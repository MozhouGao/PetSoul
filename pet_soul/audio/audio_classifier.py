"""
Audio Classifier — small 1D CNN for pet vocalisation classification.

Classifies MFCC spectrograms into vocal categories (bark, meow, whine,
growl, silence) and emotion states (calm, excited, anxious, playful).

The model is intentionally tiny (~50K parameters) and trains in minutes
on CPU / M2.
"""

import logging
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np
import torch
import torch.nn as nn

from pet_soul.config import CONFIG

logger = logging.getLogger(__name__)

VOCAL_CLASSES = ["silence", "bark", "meow", "whine", "growl", "purr"]
EMOTION_CLASSES = ["calm", "excited", "anxious", "playful"]


class AudioCNN(nn.Module):
    """Lightweight 1D CNN operating on MFCC features.

    Input shape:  (batch, n_mfcc, time_frames)
    Output shape: (batch, num_classes)
    """

    def __init__(
        self,
        n_mfcc: int = CONFIG.audio_n_mfcc,
        num_classes: int = len(VOCAL_CLASSES),
    ):
        super().__init__()
        self.conv = nn.Sequential(
            nn.Conv1d(n_mfcc, 32, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool1d(2),
            nn.Conv1d(32, 64, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.AdaptiveAvgPool1d(1),
        )
        self.fc = nn.Sequential(
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(32, num_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: (batch, n_mfcc, time_frames)
        Returns:
            logits: (batch, num_classes)
        """
        features = self.conv(x).squeeze(-1)  # (batch, 64)
        return self.fc(features)


class PetAudioClassifier:
    """High-level wrapper combining vocal type and emotion classifiers."""

    def __init__(
        self,
        vocal_weights: Optional[str] = None,
        emotion_weights: Optional[str] = None,
    ):
        self.vocal_model = AudioCNN(num_classes=len(VOCAL_CLASSES))
        self.emotion_model = AudioCNN(num_classes=len(EMOTION_CLASSES))

        if vocal_weights and Path(vocal_weights).exists():
            self.vocal_model.load_state_dict(
                torch.load(vocal_weights, map_location="cpu")
            )
            logger.info("Loaded vocal classifier weights")

        if emotion_weights and Path(emotion_weights).exists():
            self.emotion_model.load_state_dict(
                torch.load(emotion_weights, map_location="cpu")
            )
            logger.info("Loaded emotion classifier weights")

        self.vocal_model.eval()
        self.emotion_model.eval()

    def classify_vocal(self, mfcc: np.ndarray) -> Tuple[str, float]:
        """Classify a vocalisation type from MFCC features.

        Args:
            mfcc: (n_mfcc, T) MFCC array.

        Returns:
            (class_name, confidence)
        """
        return self._predict(self.vocal_model, mfcc, VOCAL_CLASSES)

    def classify_emotion(self, mfcc: np.ndarray) -> Tuple[str, float]:
        """Classify the emotion from MFCC features.

        Args:
            mfcc: (n_mfcc, T) MFCC array.

        Returns:
            (emotion_name, confidence)
        """
        return self._predict(self.emotion_model, mfcc, EMOTION_CLASSES)

    def classify(self, mfcc: np.ndarray) -> dict:
        """Full classification returning both vocal type and emotion."""
        vocal, v_conf = self.classify_vocal(mfcc)
        emotion, e_conf = self.classify_emotion(mfcc)
        return {
            "vocal_type": vocal,
            "vocal_confidence": round(v_conf, 4),
            "emotion": emotion,
            "emotion_confidence": round(e_conf, 4),
        }

    @staticmethod
    def _predict(
        model: AudioCNN,
        mfcc: np.ndarray,
        class_names: List[str],
    ) -> Tuple[str, float]:
        if mfcc.shape[1] < 2:
            return class_names[0], 0.0
        x = torch.from_numpy(mfcc).float().unsqueeze(0)
        with torch.no_grad():
            logits = model(x)
            probs = torch.softmax(logits, dim=1)
        idx = probs.argmax().item()
        return class_names[idx], float(probs[0, idx])
