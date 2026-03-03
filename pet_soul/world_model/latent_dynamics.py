"""
Latent Dynamics Model — learned state-transition predictor.

Implements  p(z_{t+1} | z_t, a_t)  in a compact latent space.

Instead of scripting state transitions, this model *predicts* the next
pet state given the current latent state and an action embedding.  This
enables the pet to anticipate outcomes and choose actions that feel
intentional rather than reactive.

Architecture (small, M2-compatible at inference):
    Input:  z_t (latent_dim) + a_t (action_dim)
    Hidden: 2-layer MLP (hidden_dim)
    Output: z_{t+1} (latent_dim) — predicted next state
"""

import logging
from pathlib import Path
from typing import Optional, Tuple

import numpy as np
import torch
import torch.nn as nn

from pet_soul.config import CONFIG

logger = logging.getLogger(__name__)


class LatentDynamicsModel(nn.Module):
    """Predicts the next latent state given current state + action.

    This is the core of the world model: it lets the pet "imagine"
    what will happen next before choosing an action.
    """

    def __init__(
        self,
        latent_dim: int = CONFIG.world_model_latent_dim,
        action_dim: int = 5,  # number of discrete actions encoded as one-hot
        hidden_dim: int = CONFIG.world_model_hidden_dim,
    ):
        super().__init__()
        self.latent_dim = latent_dim
        self.action_dim = action_dim

        self.net = nn.Sequential(
            nn.Linear(latent_dim + action_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, latent_dim),
        )

    def forward(
        self, z: torch.Tensor, action: torch.Tensor
    ) -> torch.Tensor:
        """
        Args:
            z:      (batch, latent_dim) — current latent state.
            action: (batch, action_dim) — one-hot or embedding of action.

        Returns:
            z_next: (batch, latent_dim) — predicted next state.
        """
        x = torch.cat([z, action], dim=-1)
        return self.net(x)

    def predict(self, z: np.ndarray, action_id: int) -> np.ndarray:
        """Convenience method for single-step prediction from numpy.

        Args:
            z: (latent_dim,)
            action_id: integer action index.

        Returns:
            z_next: (latent_dim,)
        """
        self.eval()
        z_t = torch.from_numpy(z).float().unsqueeze(0)
        a_t = torch.zeros(1, self.action_dim)
        if 0 <= action_id < self.action_dim:
            a_t[0, action_id] = 1.0
        with torch.no_grad():
            z_next = self.forward(z_t, a_t)
        return z_next.squeeze(0).numpy()

    def rollout(
        self, z_init: np.ndarray, action_sequence: list, steps: int = 10
    ) -> np.ndarray:
        """Dream rollout — simulate multiple steps into the future.

        Args:
            z_init: (latent_dim,) starting state.
            action_sequence: list of action_ids, cycled if shorter than steps.
            steps: number of future steps to simulate.

        Returns:
            trajectory: (steps+1, latent_dim) including z_init.
        """
        self.eval()
        trajectory = [z_init.copy()]
        z = z_init.copy()
        for i in range(steps):
            action_id = action_sequence[i % len(action_sequence)]
            z = self.predict(z, action_id)
            trajectory.append(z)
        return np.stack(trajectory)


class LatentStateEncoder(nn.Module):
    """Encodes raw observation features into the world model's latent space.

    Combines motion latent, personality vector, and current FSM state
    into a unified latent representation.
    """

    def __init__(
        self,
        motion_dim: int = CONFIG.motion_latent_dim,
        personality_dim: int = 9,  # PersonalityProfile.to_vector() length
        state_dim: int = 5,        # one-hot FSM state
        latent_dim: int = CONFIG.world_model_latent_dim,
    ):
        super().__init__()
        input_dim = motion_dim + personality_dim + state_dim
        self.net = nn.Sequential(
            nn.Linear(input_dim, 64),
            nn.ReLU(),
            nn.Linear(64, latent_dim),
        )

    def forward(self, observation: torch.Tensor) -> torch.Tensor:
        """
        Args:
            observation: (batch, motion_dim + personality_dim + state_dim)
        Returns:
            z: (batch, latent_dim)
        """
        return self.net(observation)

    def encode(
        self,
        motion_latent: np.ndarray,
        personality_vector: np.ndarray,
        state_onehot: np.ndarray,
    ) -> np.ndarray:
        """Convenience encode from numpy arrays.

        Returns:
            z: (latent_dim,)
        """
        self.eval()
        obs = np.concatenate([motion_latent, personality_vector, state_onehot])
        x = torch.from_numpy(obs).float().unsqueeze(0)
        with torch.no_grad():
            z = self.forward(x)
        return z.squeeze(0).numpy()


def save_world_model(model: LatentDynamicsModel, path: str):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), path)
    logger.info("World model saved to %s", path)


def load_world_model(path: str) -> LatentDynamicsModel:
    model = LatentDynamicsModel()
    model.load_state_dict(torch.load(path, map_location="cpu"))
    model.eval()
    logger.info("World model loaded from %s", path)
    return model
