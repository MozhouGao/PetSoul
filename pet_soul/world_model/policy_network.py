"""
Policy Network — action selection via the world model.

Given the current latent state, selects the best action by:
1. Imagining outcomes for each possible action (via LatentDynamicsModel)
2. Scoring each imagined outcome with a learned reward predictor
3. Choosing the action with the highest predicted reward

This replaces the FSM's random transition logic with *planning-based*
decision-making. The pet appears to act intentionally because it is
actually reasoning about consequences.

For MVP the reward predictor is a simple MLP. It can later be upgraded
to a full RL value function trained online.
"""

import logging
from typing import Optional

import numpy as np
import torch
import torch.nn as nn

from pet_soul.config import CONFIG
from pet_soul.world_model.latent_dynamics import LatentDynamicsModel

logger = logging.getLogger(__name__)

# Actions the pet can take (maps to animation states / FSM transitions)
ACTION_NAMES = ["stay", "approach", "retreat", "play", "rest"]
NUM_ACTIONS = len(ACTION_NAMES)


class RewardPredictor(nn.Module):
    """Predicts a scalar reward from a latent state.

    Trained to maximise:
        - Proximity to user (positive reward when close)
        - Motion naturalness (penalty for unrealistic transitions)
        - Personality coherence (reward for staying in-character)
    """

    def __init__(self, latent_dim: int = CONFIG.world_model_latent_dim):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(latent_dim, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
        )

    def forward(self, z: torch.Tensor) -> torch.Tensor:
        """
        Args:
            z: (batch, latent_dim)
        Returns:
            reward: (batch, 1)
        """
        return self.net(z)


class PolicyNetwork:
    """Selects actions by imagining outcomes via the world model.

    Usage::

        policy = PolicyNetwork(dynamics, reward_predictor)
        action_id = policy.select_action(current_z)
        action_name = ACTION_NAMES[action_id]
    """

    def __init__(
        self,
        dynamics: LatentDynamicsModel,
        reward: Optional[RewardPredictor] = None,
        temperature: float = 1.0,
    ):
        self.dynamics = dynamics
        self.reward = reward or RewardPredictor()
        self.temperature = temperature

        self.dynamics.eval()
        self.reward.eval()

    def select_action(
        self,
        z: np.ndarray,
        lookahead: int = 1,
    ) -> int:
        """Select the best action from the current latent state.

        Args:
            z: (latent_dim,) current state.
            lookahead: How many steps to simulate per action (default 1).

        Returns:
            action_id: index into ACTION_NAMES.
        """
        scores = np.zeros(NUM_ACTIONS)

        for a in range(NUM_ACTIONS):
            z_sim = z.copy()
            total_reward = 0.0
            for _ in range(lookahead):
                z_sim = self.dynamics.predict(z_sim, a)
                r = self._score(z_sim)
                total_reward += r
            scores[a] = total_reward

        # Softmax selection with temperature
        if self.temperature > 0:
            exp_scores = np.exp((scores - scores.max()) / self.temperature)
            probs = exp_scores / (exp_scores.sum() + 1e-9)
            return int(np.random.choice(NUM_ACTIONS, p=probs))
        else:
            return int(np.argmax(scores))

    def _score(self, z: np.ndarray) -> float:
        z_t = torch.from_numpy(z).float().unsqueeze(0)
        with torch.no_grad():
            r = self.reward(z_t)
        return float(r.item())

    def select_action_name(self, z: np.ndarray, lookahead: int = 1) -> str:
        """Like select_action but returns the action name string."""
        return ACTION_NAMES[self.select_action(z, lookahead)]
