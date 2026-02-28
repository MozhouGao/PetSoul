"""
Attribute Extraction Module
Uses CLIP to extract breed, coat colors, and markings from pet images
"""

import logging
import numpy as np
from typing import List, Dict, Tuple, Optional
from PIL import Image
import torch

from config import CONFIG

logger = logging.getLogger(__name__)


class AttributeExtractor:
    """Extracts pet attributes using CLIP"""

    # Common dog breeds (MVP: dog-only support)
    DOG_BREEDS = [
        "Golden Retriever", "Labrador Retriever", "German Shepherd", "Bulldog",
        "Beagle", "Rottweiler", "Yorkshire Terrier", "Dachshund", "Siberian Husky",
        "Great Dane", "Poodle", "Shih Tzu", "Boxer", "Border Collie", "Chihuahua",
        "Australian Shepherd", "Cocker Spaniel", "Pomeranian", "French Bulldog",
        "Maltese", "Boston Terrier", "Havanese", "Bichon Frise", "Pug", "Mastiff"
    ]

    # Coat colors
    COAT_COLORS = [
        "black", "white", "brown", "tan", "golden", "gray", "cream", "orange",
        "red", "brindle", "merle", "blue", "chocolate", "fawn", "sable"
    ]

    # Markings
    MARKINGS = [
        "facial mask", "white chest", "white paws", "spots", "stripes",
        "tuxedo", "brindle pattern", "merle pattern", "patches"
    ]

    # Physical attribute labels for procedural generation
    BODY_TYPES = ["compact", "athletic", "stocky", "slender", "large and muscular"]
    EAR_SHAPES = ["floppy ears", "erect pointy ears", "semi-erect ears", "rose ears", "button ears"]
    TAIL_TYPES = ["long curved tail", "long straight tail", "curled tail over back", "short tail", "docked tail"]
    SNOUT_LENGTHS = ["flat face", "short snout", "medium snout", "long snout"]
    SIZE_CLASSES = ["toy sized dog", "small dog", "medium sized dog", "large dog", "giant dog"]
    FUR_LENGTHS = ["short fur", "medium length fur", "long fur", "wire-haired fur"]

    # Maps CLIP labels back to canonical attribute values
    _BODY_TYPE_MAP = {"compact": "compact", "athletic": "athletic", "stocky": "stocky",
                      "slender": "slender", "large and muscular": "large"}
    _EAR_SHAPE_MAP = {"floppy ears": "floppy", "erect pointy ears": "erect",
                      "semi-erect ears": "semi_erect", "rose ears": "rose", "button ears": "button"}
    _TAIL_TYPE_MAP = {"long curved tail": "long_curved", "long straight tail": "long_straight",
                      "curled tail over back": "curled", "short tail": "short", "docked tail": "docked"}
    _SNOUT_MAP = {"flat face": "flat", "short snout": "short", "medium snout": "medium", "long snout": "long"}
    _SIZE_MAP = {"toy sized dog": "toy", "small dog": "small", "medium sized dog": "medium",
                 "large dog": "large", "giant dog": "giant"}
    _FUR_MAP = {"short fur": "short", "medium length fur": "medium", "long fur": "long",
                "wire-haired fur": "wire-haired"}

    def __init__(self, use_clip: bool = True):
        """
        Initialize attribute extractor

        Args:
            use_clip: Whether to use CLIP model (requires transformers)
        """
        self.use_clip = use_clip
        self.clip_model = None
        self.clip_processor = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        if use_clip:
            self._load_clip()

    def _load_clip(self):
        """Load CLIP model"""
        try:
            from transformers import CLIPProcessor, CLIPModel

            logger.info("Loading CLIP model...")
            self.clip_model = CLIPModel.from_pretrained(CONFIG.clip_model_name).to(self.device)
            self.clip_processor = CLIPProcessor.from_pretrained(CONFIG.clip_model_name)
            self.clip_model.eval()
            logger.info("CLIP model loaded successfully")
        except Exception as e:
            logger.error("Error loading CLIP model: %s", e)
            logger.warning("Attribute extraction will use fallback heuristics")
            self.use_clip = False

    def extract_breed(self, image: np.ndarray) -> Tuple[Optional[str], float]:
        """
        Extract breed from pet image

        Args:
            image: Pet image as numpy array (RGB format)

        Returns:
            Tuple of (breed_name, confidence_score)
        """
        if not self.use_clip or self.clip_model is None:
            return None, 0.0

        try:
            # Convert numpy to PIL Image
            if isinstance(image, np.ndarray):
                if image.dtype != np.uint8:
                    image = (image * 255).astype(np.uint8)
                pil_image = Image.fromarray(image)
            else:
                pil_image = image

            # Prepare prompts
            breed_prompts = [f"a photo of a {breed}" for breed in self.DOG_BREEDS]

            # Process with CLIP
            inputs = self.clip_processor(
                text=breed_prompts,
                images=pil_image,
                return_tensors="pt",
                padding=True
            ).to(self.device)

            with torch.no_grad():
                outputs = self.clip_model(**inputs)
                logits_per_image = outputs.logits_per_image
                probs = logits_per_image.softmax(dim=1)

            # Get best match
            best_idx = probs.argmax().item()
            confidence = probs[0][best_idx].item()
            breed = self.DOG_BREEDS[best_idx]

            return breed, confidence

        except Exception as e:
            logger.error("Error extracting breed: %s", e)
            return None, 0.0

    def extract_coat_colors(self, image: np.ndarray) -> List[str]:
        """
        Extract coat colors from pet image

        Args:
            image: Pet image as numpy array (RGB format)

        Returns:
            List of detected coat colors
        """
        if not self.use_clip or self.clip_model is None:
            return self._extract_colors_heuristic(image)

        try:
            # Convert numpy to PIL Image
            if isinstance(image, np.ndarray):
                if image.dtype != np.uint8:
                    image = (image * 255).astype(np.uint8)
                pil_image = Image.fromarray(image)
            else:
                pil_image = image

            # Prepare color prompts
            color_prompts = [f"a {color} colored dog" for color in self.COAT_COLORS]

            # Process with CLIP
            inputs = self.clip_processor(
                text=color_prompts,
                images=pil_image,
                return_tensors="pt",
                padding=True
            ).to(self.device)

            with torch.no_grad():
                outputs = self.clip_model(**inputs)
                logits_per_image = outputs.logits_per_image
                probs = logits_per_image.softmax(dim=1)

            # Return top colors above threshold
            sorted_indices = probs[0].argsort(descending=True)
            top_colors = [self.COAT_COLORS[idx] for idx in sorted_indices[:CONFIG.max_coat_colors] if probs[0][idx] > CONFIG.coat_color_threshold]

            return top_colors if top_colors else ["brown"]  # Default fallback

        except Exception as e:
            logger.error("Error extracting coat colors: %s", e)
            return self._extract_colors_heuristic(image)

    def extract_markings(self, image: np.ndarray) -> List[str]:
        """
        Extract markings from pet image

        Args:
            image: Pet image as numpy array (RGB format)

        Returns:
            List of detected markings
        """
        if not self.use_clip or self.clip_model is None:
            return []

        try:
            # Convert numpy to PIL Image
            if isinstance(image, np.ndarray):
                if image.dtype != np.uint8:
                    image = (image * 255).astype(np.uint8)
                pil_image = Image.fromarray(image)
            else:
                pil_image = image

            # Prepare marking prompts
            marking_prompts = [f"a dog with {marking}" for marking in self.MARKINGS]

            # Process with CLIP
            inputs = self.clip_processor(
                text=marking_prompts,
                images=pil_image,
                return_tensors="pt",
                padding=True
            ).to(self.device)

            with torch.no_grad():
                outputs = self.clip_model(**inputs)
                logits_per_image = outputs.logits_per_image
                probs = logits_per_image.softmax(dim=1)

            # Get markings above threshold
            detected_markings = []
            for i, marking in enumerate(self.MARKINGS):
                prob = probs[0][i].item()
                if prob > CONFIG.marking_threshold:
                    detected_markings.append(marking)

            return detected_markings

        except Exception as e:
            logger.error("Error extracting markings: %s", e)
            return []

    def _classify_attribute(self, image: np.ndarray, labels: List[str],
                             prompt_template: str, label_map: Dict) -> Optional[str]:
        """Generic CLIP zero-shot classification for a single attribute.

        Args:
            image: Pet image as numpy array (RGB)
            labels: List of CLIP text labels
            prompt_template: Template with {} placeholder for label
            label_map: Maps CLIP label -> canonical value

        Returns:
            Canonical attribute value or None
        """
        if not self.use_clip or self.clip_model is None:
            return None
        try:
            if isinstance(image, np.ndarray):
                if image.dtype != np.uint8:
                    image = (image * 255).astype(np.uint8)
                pil_image = Image.fromarray(image)
            else:
                pil_image = image

            prompts = [prompt_template.format(label) for label in labels]
            inputs = self.clip_processor(
                text=prompts, images=pil_image, return_tensors="pt", padding=True
            ).to(self.device)

            with torch.no_grad():
                outputs = self.clip_model(**inputs)
                probs = outputs.logits_per_image.softmax(dim=1)

            best_idx = probs.argmax().item()
            best_label = labels[best_idx]
            return label_map.get(best_label, best_label)
        except Exception as e:
            logger.error("Error classifying attribute: %s", e)
            return None

    def extract_body_type(self, image: np.ndarray) -> Optional[str]:
        return self._classify_attribute(image, self.BODY_TYPES,
                                        "a {} dog", self._BODY_TYPE_MAP)

    def extract_ear_shape(self, image: np.ndarray) -> Optional[str]:
        return self._classify_attribute(image, self.EAR_SHAPES,
                                        "a dog with {}", self._EAR_SHAPE_MAP)

    def extract_tail_type(self, image: np.ndarray) -> Optional[str]:
        return self._classify_attribute(image, self.TAIL_TYPES,
                                        "a dog with a {}", self._TAIL_TYPE_MAP)

    def extract_snout_length(self, image: np.ndarray) -> Optional[str]:
        return self._classify_attribute(image, self.SNOUT_LENGTHS,
                                        "a dog with a {}", self._SNOUT_MAP)

    def extract_size_class(self, image: np.ndarray) -> Optional[str]:
        return self._classify_attribute(image, self.SIZE_CLASSES,
                                        "a {} standing", self._SIZE_MAP)

    def extract_fur_length(self, image: np.ndarray) -> Optional[str]:
        return self._classify_attribute(image, self.FUR_LENGTHS,
                                        "a dog with {}", self._FUR_MAP)

    def extract_physical_attributes(self, image: np.ndarray) -> Dict[str, Optional[str]]:
        """Extract all physical attributes in one call."""
        return {
            "body_type": self.extract_body_type(image),
            "ear_shape": self.extract_ear_shape(image),
            "tail_type": self.extract_tail_type(image),
            "snout_length": self.extract_snout_length(image),
            "size_class": self.extract_size_class(image),
            "fur_length": self.extract_fur_length(image),
        }

    def _extract_colors_heuristic(self, image: np.ndarray) -> List[str]:
        """Fallback color extraction using simple image analysis"""
        import cv2

        # Convert to RGB if needed
        if len(image.shape) == 3 and image.shape[2] == 3:
            rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB) if image.dtype == np.uint8 else image
        else:
            rgb = image

        # Simple dominant color detection
        mean_color = rgb.mean(axis=(0, 1))

        # Map to color names (very simplified)
        colors = []
        if mean_color[0] < 50 and mean_color[1] < 50 and mean_color[2] < 50:
            colors.append("black")
        elif mean_color[0] > 200 and mean_color[1] > 200 and mean_color[2] > 200:
            colors.append("white")
        elif mean_color[0] > mean_color[1] and mean_color[0] > mean_color[2]:
            colors.append("brown")
        else:
            colors.append("brown")  # Default

        return colors
