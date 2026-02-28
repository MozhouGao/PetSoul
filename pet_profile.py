"""
Pet Profile Data Model
Represents structured pet attributes extracted from images
"""

from dataclasses import dataclass
from typing import List, Optional, Dict


@dataclass
class PetProfile:
    """Structured pet profile with extracted attributes"""
    species: str  # "dog", "cat", etc.
    breed: Optional[str] = None
    breed_confidence: float = 0.0
    coat_colors: List[str] = None
    markings: List[str] = None
    fur_length: Optional[str] = None
    # Physical attributes for procedural 3D generation
    body_type: Optional[str] = None       # compact, athletic, stocky, slender, large
    ear_shape: Optional[str] = None       # floppy, erect, semi_erect, rose, button
    tail_type: Optional[str] = None       # long_curved, long_straight, curled, short, docked
    snout_length: Optional[str] = None    # flat, short, medium, long
    size_class: Optional[str] = None      # toy, small, medium, large, giant
    leg_length: Optional[str] = None      # short, medium, long

    def __post_init__(self):
        if self.coat_colors is None:
            self.coat_colors = []
        if self.markings is None:
            self.markings = []

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "species": self.species,
            "breed": self.breed,
            "breed_confidence": self.breed_confidence,
            "coat_colors": self.coat_colors,
            "markings": self.markings,
            "fur_length": self.fur_length,
            "body_type": self.body_type,
            "ear_shape": self.ear_shape,
            "tail_type": self.tail_type,
            "snout_length": self.snout_length,
            "size_class": self.size_class,
            "leg_length": self.leg_length,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'PetProfile':
        """Create from dictionary"""
        return cls(**data)
