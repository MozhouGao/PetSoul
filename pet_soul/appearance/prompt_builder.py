"""
Prompt Builder
Constructs prompts for SDXL avatar generation from pet attributes
"""

import logging
from typing import List
from pet_soul.appearance.pet_profile import PetProfile

logger = logging.getLogger(__name__)


class PromptBuilder:
    """Builds prompts for avatar generation"""

    def build_prompt(self, profile: PetProfile, style: str = "realistic") -> str:
        """
        Build prompt from pet profile

        Args:
            profile: PetProfile object with extracted attributes
            style: Style modifier (realistic, cartoon, etc.)

        Returns:
            Complete prompt string
        """
        parts = []

        # Breed
        breed = profile.breed.lower() if profile.breed else profile.species
        parts.append(f"a {breed}")

        # Coat colors
        if profile.coat_colors:
            color_desc = self._format_list(profile.coat_colors)
            parts.append(f"with {color_desc} colored fur")

        # Markings
        if profile.markings:
            marking_desc = self._format_list(profile.markings)
            parts.append(f"with {marking_desc} pattern")

        # Fur length
        if profile.fur_length:
            parts.append(f"{profile.fur_length}-length fur texture")

        # Physical details for better geometry hints
        if profile.ear_shape:
            parts.append(f"{profile.ear_shape} ears")
        if profile.snout_length:
            parts.append(f"{profile.snout_length} snout")

        # Facial detail — this is the key missing piece
        parts.append("detailed face with realistic eyes with pupils and iris")
        parts.append("visible nose and mouth")
        parts.append("natural fur texture with color variation and shading")

        # Quality modifiers
        parts.append("high detail, photorealistic textures, studio lighting")

        prompt = ", ".join(parts)
        return prompt

    def build_negative_prompt(self) -> str:
        """Build negative prompt (things to avoid)"""
        return ", ".join([
            "blurry", "low quality", "distorted", "deformed",
            "extra limbs", "bad anatomy", "watermark", "text",
            "ugly", "duplicate", "photorealistic"
        ])

    def _format_list(self, items: List[str]) -> str:
        """Format list into natural language"""
        if len(items) == 0:
            return ""
        elif len(items) == 1:
            return items[0]
        elif len(items) == 2:
            return f"{items[0]} and {items[1]}"
        else:
            return f"{', '.join(items[:-1])}, and {items[-1]}"
