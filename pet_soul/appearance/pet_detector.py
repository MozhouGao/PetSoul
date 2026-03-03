"""
Pet Detection Module
Uses YOLOv8 for detecting and cropping pets from images
"""

import logging
import cv2
import numpy as np
from typing import Optional, Tuple
from ultralytics import YOLO
from pathlib import Path

from pet_soul.config import CONFIG, PROJECT_ROOT

logger = logging.getLogger(__name__)


class PetDetector:
    """Detects pets in images using YOLOv8"""

    # YOLO classes for pets (COCO dataset)
    PET_CLASSES = {
        15: "dog",  # COCO class 15
        16: "cat",  # COCO class 16
        # Add more if needed: bird, horse, etc.
    }

    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize pet detector

        Args:
            model_path: Path to YOLOv8 model file. If None, uses default yolov8n.pt
        """
        self.model = None
        self.model_ready = False

        if model_path is None:
            # Look for yolov8n.pt at the project root
            default_path = PROJECT_ROOT / CONFIG.yolo_model
            if default_path.exists():
                model_path = str(default_path)
            else:
                model_path = CONFIG.yolo_model  # Will download automatically

        self._load_model(model_path)

    def _load_model(self, model_path: str):
        """Load YOLOv8 model"""
        try:
            logger.info("Loading YOLOv8 model from %s...", model_path)
            self.model = YOLO(model_path)
            self.model_ready = True
            logger.info("YOLOv8 model loaded successfully")
        except Exception as e:
            logger.error("Error loading YOLOv8 model: %s", e)
            self.model_ready = False

    def detect(self, image: np.ndarray, conf_threshold: float = CONFIG.yolo_conf_threshold) -> Optional[Tuple[int, int, int, int]]:
        """
        Detect pet in image

        Args:
            image: Input image as numpy array (RGB format)
            conf_threshold: Confidence threshold for detection

        Returns:
            Bounding box as (x1, y1, x2, y2) or None if no pet detected
        """
        if not self.model_ready or self.model is None:
            return None

        try:
            # Run detection
            results = self.model(image, conf=conf_threshold, verbose=False)

            # Find best pet detection
            best_box = None
            best_conf = 0.0

            for result in results:
                boxes = result.boxes
                if boxes is None or len(boxes) == 0:
                    continue

                for box in boxes:
                    # Check if detected class is a pet
                    cls_id = int(box.cls[0])
                    if cls_id in self.PET_CLASSES:
                        conf = float(box.conf[0])
                        if conf > best_conf:
                            best_conf = conf
                            # Get bounding box coordinates
                            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                            best_box = (int(x1), int(y1), int(x2), int(y2))

            return best_box

        except Exception as e:
            logger.error("Error during pet detection: %s", e)
            return None

    def crop_pet(self, image: np.ndarray, bbox: Optional[Tuple[int, int, int, int]] = None) -> Optional[np.ndarray]:
        """
        Crop pet from image

        Args:
            image: Input image
            bbox: Bounding box. If None, detects first

        Returns:
            Cropped pet image or None
        """
        if bbox is None:
            bbox = self.detect(image)

        if bbox is None:
            return None

        x1, y1, x2, y2 = bbox
        h, w = image.shape[:2]

        # Ensure coordinates are within image bounds
        x1 = max(0, x1)
        y1 = max(0, y1)
        x2 = min(w, x2)
        y2 = min(h, y2)

        if x2 <= x1 or y2 <= y1:
            return None

        # Crop with some padding
        padding = CONFIG.crop_padding_px
        x1 = max(0, x1 - padding)
        y1 = max(0, y1 - padding)
        x2 = min(w, x2 + padding)
        y2 = min(h, y2 + padding)

        cropped = image[y1:y2, x1:x2]
        return cropped

    def is_ready(self) -> bool:
        """Check if model is loaded and ready"""
        return self.model_ready
