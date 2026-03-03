"""
Personality Profile — stores and applies pet personality traits.

Combines motion statistics, optional audio traits, and user-defined
modifiers into a single ``PersonalityProfile`` that conditions the FSM
transition weights and animation blend parameters.

The profile is serialised as JSON and stored in Supabase so it persists
across sessions.
"""

import json
import logging
from dataclasses import dataclass, field, asdict
from typing import Dict, Optional

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class PersonalityProfile:
    """Compact personality representation derived from motion + audio data.

    All values are normalised 0–1 where:
        0 = low expression of the trait
        1 = high expression of the trait
    """

    # Motion-derived traits
    energy_level: float = 0.5        # from avg_speed
    playfulness: float = 0.5         # from movement_entropy
    reactivity: float = 0.5          # from max_speed / reaction latency
    tail_expressiveness: float = 0.5 # from tail_wag_freq
    gait_regularity: float = 0.5     # from autocorrelation score

    # Audio-derived traits (filled by audio module)
    vocal_energy: float = 0.5        # bark/meow intensity
    vocal_frequency: float = 0.5     # how often the pet vocalises

    # Composite scores (computed)
    sociability: float = 0.5
    calmness: float = 0.5

    def compute_composites(self):
        """Derive composite traits from primary traits."""
        self.sociability = np.clip(
            0.3 * self.energy_level + 0.4 * self.playfulness + 0.3 * self.tail_expressiveness,
            0.0, 1.0,
        )
        self.calmness = np.clip(
            1.0 - (0.4 * self.energy_level + 0.3 * self.reactivity + 0.3 * (1 - self.gait_regularity)),
            0.0, 1.0,
        )

    def to_dict(self) -> Dict:
        self.compute_composites()
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: Dict) -> "PersonalityProfile":
        known = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in known}
        return cls(**filtered)

    @classmethod
    def from_json(cls, s: str) -> "PersonalityProfile":
        return cls.from_dict(json.loads(s))

    def to_vector(self) -> np.ndarray:
        """Return the profile as a fixed-length numpy vector."""
        self.compute_composites()
        return np.array([
            self.energy_level,
            self.playfulness,
            self.reactivity,
            self.tail_expressiveness,
            self.gait_regularity,
            self.vocal_energy,
            self.vocal_frequency,
            self.sociability,
            self.calmness,
        ], dtype=np.float32)


def profile_from_motion_stats(stats: Dict[str, float]) -> PersonalityProfile:
    """Build a PersonalityProfile from motion feature statistics.

    Applies simple min-max normalisation heuristics.  In production these
    bounds would be learned from a calibration dataset.
    """
    def _norm(value: float, low: float, high: float) -> float:
        if high <= low:
            return 0.5
        return float(np.clip((value - low) / (high - low), 0.0, 1.0))

    return PersonalityProfile(
        energy_level=_norm(stats.get("avg_speed", 0), 0, 0.05),
        playfulness=_norm(stats.get("movement_entropy", 0), 0, 5.0),
        reactivity=_norm(stats.get("max_speed", 0), 0, 0.1),
        tail_expressiveness=_norm(stats.get("tail_wag_freq", 0), 0, 5.0),
        gait_regularity=_norm(stats.get("gait_regularity", 0), 0, 1.0),
    )
