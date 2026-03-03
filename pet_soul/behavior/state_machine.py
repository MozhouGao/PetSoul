"""
Finite State Machine — the "alive" layer for pet behavior.

Controls high-level behavioral states (Idle → Curious → Playful → Alert)
with weighted probabilistic transitions driven by sensory input, elapsed
time, and randomised micro-movements.

This is the cheap-stack behaviour engine that feels alive without any
reinforcement learning.  A world-model policy can replace ``update()``
later without changing the state/transition API.
"""

import logging
import random
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
# States
# ------------------------------------------------------------------

class PetState(Enum):
    IDLE = auto()
    CURIOUS = auto()
    PLAYFUL = auto()
    ALERT = auto()
    RESTING = auto()


# ------------------------------------------------------------------
# Sensory input (from Unity or backend)
# ------------------------------------------------------------------

@dataclass
class SensoryInput:
    """Snapshot of stimuli the pet receives each tick."""
    user_distance: float = 10.0       # 0 = touching, 10 = far away
    user_moving: bool = False
    sound_level: float = 0.0          # 0–1 normalised audio amplitude
    time_since_interaction: float = 0.0  # seconds since last user action
    random_seed: float = field(default_factory=random.random)


# ------------------------------------------------------------------
# Transition table
# ------------------------------------------------------------------

# Weights are relative probabilities.  ``condition`` is a callable
# (SensoryInput → bool) that gates the transition.

@dataclass
class Transition:
    target: PetState
    weight: float
    condition: Optional[object] = None  # callable(SensoryInput) → bool


# Default transition table — can be overridden per-personality.
_DEFAULT_TRANSITIONS: Dict[PetState, List[Transition]] = {
    PetState.IDLE: [
        Transition(PetState.CURIOUS, 0.3, lambda s: s.user_moving),
        Transition(PetState.ALERT, 0.2, lambda s: s.sound_level > 0.5),
        Transition(PetState.PLAYFUL, 0.1, lambda s: s.user_distance < 3.0),
        Transition(PetState.RESTING, 0.15, lambda s: s.time_since_interaction > 30),
    ],
    PetState.CURIOUS: [
        Transition(PetState.PLAYFUL, 0.4, lambda s: s.user_distance < 2.0),
        Transition(PetState.ALERT, 0.2, lambda s: s.sound_level > 0.6),
        Transition(PetState.IDLE, 0.3, lambda s: s.time_since_interaction > 10),
    ],
    PetState.PLAYFUL: [
        Transition(PetState.IDLE, 0.3, lambda s: s.time_since_interaction > 15),
        Transition(PetState.CURIOUS, 0.2, lambda s: s.user_distance > 5.0),
        Transition(PetState.RESTING, 0.1, lambda s: s.time_since_interaction > 20),
    ],
    PetState.ALERT: [
        Transition(PetState.CURIOUS, 0.4, lambda s: s.sound_level < 0.3),
        Transition(PetState.IDLE, 0.3, lambda s: s.time_since_interaction > 8),
    ],
    PetState.RESTING: [
        Transition(PetState.IDLE, 0.4, lambda s: s.time_since_interaction < 5),
        Transition(PetState.ALERT, 0.3, lambda s: s.sound_level > 0.7),
    ],
}


# ------------------------------------------------------------------
# FSM
# ------------------------------------------------------------------

class PetFSM:
    """Probabilistic finite state machine for pet behaviour.

    Usage::

        fsm = PetFSM()
        while running:
            sensory = SensoryInput(user_distance=..., ...)
            new_state = fsm.update(sensory)
            animation_controller.play(new_state)
    """

    def __init__(
        self,
        initial_state: PetState = PetState.IDLE,
        transitions: Optional[Dict[PetState, List[Transition]]] = None,
        min_state_duration: float = 1.0,
    ):
        self.state = initial_state
        self.transitions = transitions or _DEFAULT_TRANSITIONS
        self.min_state_duration = min_state_duration
        self._state_entered_at = time.monotonic()
        self._history: List[PetState] = [initial_state]

    @property
    def state_duration(self) -> float:
        """How long (seconds) the FSM has been in the current state."""
        return time.monotonic() - self._state_entered_at

    @property
    def history(self) -> List[PetState]:
        return list(self._history)

    def update(self, sensory: SensoryInput) -> PetState:
        """Evaluate transitions and potentially switch state.

        Returns:
            The (possibly new) current state.
        """
        if self.state_duration < self.min_state_duration:
            return self.state

        candidates = self.transitions.get(self.state, [])
        eligible = []
        for t in candidates:
            if t.condition is None or t.condition(sensory):
                eligible.append(t)

        if not eligible:
            return self.state

        # Weighted random selection
        total = sum(t.weight for t in eligible)
        roll = sensory.random_seed * total
        cumulative = 0.0
        chosen = None
        for t in eligible:
            cumulative += t.weight
            if roll <= cumulative:
                chosen = t
                break

        if chosen is None:
            return self.state

        # Apply a randomised "inertia" — 40 % chance to stay put even if
        # a transition is eligible, making behaviour less twitchy.
        if random.random() < 0.4:
            return self.state

        self._transition_to(chosen.target)
        return self.state

    def force_state(self, state: PetState):
        """Force an immediate state change (e.g. from an API command)."""
        self._transition_to(state)

    def _transition_to(self, new_state: PetState):
        if new_state != self.state:
            logger.debug("FSM: %s → %s", self.state.name, new_state.name)
            self.state = new_state
            self._state_entered_at = time.monotonic()
            self._history.append(new_state)

    def to_dict(self) -> dict:
        return {
            "state": self.state.name,
            "duration": round(self.state_duration, 2),
            "history_length": len(self._history),
        }
