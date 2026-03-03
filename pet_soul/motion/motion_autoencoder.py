"""
Motion Autoencoder — LSTM-based encoder/decoder for pet motion style.

Learns a compressed latent representation of motion sequences that can
be sampled to generate novel, non-repetitive animation variations that
preserve the individual pet's movement style.

Architecture (cheap-stack, M2-compatible):
    Encoder:  LSTM(input=J*3, hidden=128) → Linear → z (64-dim)
    Decoder:  Linear → LSTM(input=64, hidden=128) → Linear → J*3
"""

import logging
from pathlib import Path
from typing import Optional, Tuple

import numpy as np
import torch
import torch.nn as nn

from pet_soul.config import CONFIG
from pet_soul.motion.pose_extractor import NUM_KEYPOINTS

logger = logging.getLogger(__name__)


class MotionEncoder(nn.Module):
    """LSTM encoder that maps a motion sequence to a latent vector."""

    def __init__(
        self,
        input_dim: int = NUM_KEYPOINTS * 3,
        hidden_dim: int = CONFIG.motion_hidden_dim,
        latent_dim: int = CONFIG.motion_latent_dim,
    ):
        super().__init__()
        self.lstm = nn.LSTM(input_dim, hidden_dim, batch_first=True)
        self.fc_mu = nn.Linear(hidden_dim, latent_dim)
        self.fc_logvar = nn.Linear(hidden_dim, latent_dim)

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Args:
            x: (batch, seq_len, input_dim)
        Returns:
            mu, logvar — each (batch, latent_dim)
        """
        _, (h_n, _) = self.lstm(x)
        h = h_n.squeeze(0)  # (batch, hidden)
        return self.fc_mu(h), self.fc_logvar(h)


class MotionDecoder(nn.Module):
    """LSTM decoder that reconstructs a motion sequence from a latent vector."""

    def __init__(
        self,
        output_dim: int = NUM_KEYPOINTS * 3,
        hidden_dim: int = CONFIG.motion_hidden_dim,
        latent_dim: int = CONFIG.motion_latent_dim,
        seq_length: int = CONFIG.motion_seq_length,
    ):
        super().__init__()
        self.seq_length = seq_length
        self.fc = nn.Linear(latent_dim, hidden_dim)
        self.lstm = nn.LSTM(hidden_dim, hidden_dim, batch_first=True)
        self.out = nn.Linear(hidden_dim, output_dim)

    def forward(self, z: torch.Tensor) -> torch.Tensor:
        """
        Args:
            z: (batch, latent_dim)
        Returns:
            reconstructed: (batch, seq_length, output_dim)
        """
        h = self.fc(z).unsqueeze(1).repeat(1, self.seq_length, 1)
        out, _ = self.lstm(h)
        return self.out(out)


class MotionAutoencoder(nn.Module):
    """VAE-style motion autoencoder combining encoder and decoder."""

    def __init__(
        self,
        input_dim: int = NUM_KEYPOINTS * 3,
        hidden_dim: int = CONFIG.motion_hidden_dim,
        latent_dim: int = CONFIG.motion_latent_dim,
        seq_length: int = CONFIG.motion_seq_length,
    ):
        super().__init__()
        self.encoder = MotionEncoder(input_dim, hidden_dim, latent_dim)
        self.decoder = MotionDecoder(input_dim, hidden_dim, latent_dim, seq_length)

    def reparameterize(self, mu: torch.Tensor, logvar: torch.Tensor) -> torch.Tensor:
        std = torch.exp(0.5 * logvar)
        eps = torch.randn_like(std)
        return mu + eps * std

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        mu, logvar = self.encoder(x)
        z = self.reparameterize(mu, logvar)
        recon = self.decoder(z)
        return recon, mu, logvar

    def encode(self, motion_seq: np.ndarray) -> np.ndarray:
        """Encode a numpy motion sequence to a latent vector.

        Args:
            motion_seq: (T, J, 3) or (T, J*3)

        Returns:
            z: (latent_dim,)
        """
        self.eval()
        if motion_seq.ndim == 3:
            motion_seq = motion_seq.reshape(motion_seq.shape[0], -1)
        x = torch.from_numpy(motion_seq).float().unsqueeze(0)
        with torch.no_grad():
            mu, _ = self.encoder(x)
        return mu.squeeze(0).numpy()

    def decode(self, z: np.ndarray) -> np.ndarray:
        """Decode a latent vector back to a motion sequence.

        Args:
            z: (latent_dim,)

        Returns:
            motion_seq: (seq_length, J*3)
        """
        self.eval()
        z_t = torch.from_numpy(z).float().unsqueeze(0)
        with torch.no_grad():
            recon = self.decoder(z_t)
        return recon.squeeze(0).numpy()

    def sample(self, n: int = 1) -> np.ndarray:
        """Sample random motion sequences from the latent prior.

        Returns:
            (n, seq_length, J*3)
        """
        self.eval()
        z = torch.randn(n, self.encoder.fc_mu.out_features)
        with torch.no_grad():
            return self.decoder(z).numpy()


def vae_loss(
    recon: torch.Tensor,
    target: torch.Tensor,
    mu: torch.Tensor,
    logvar: torch.Tensor,
    kl_weight: float = 0.001,
) -> torch.Tensor:
    """Combined reconstruction + KL divergence loss."""
    recon_loss = nn.functional.mse_loss(recon, target, reduction="mean")
    kl_loss = -0.5 * torch.mean(1 + logvar - mu.pow(2) - logvar.exp())
    return recon_loss + kl_weight * kl_loss


def save_model(model: MotionAutoencoder, path: str):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), path)
    logger.info("Motion autoencoder saved to %s", path)


def load_model(path: str) -> MotionAutoencoder:
    model = MotionAutoencoder()
    model.load_state_dict(torch.load(path, map_location="cpu"))
    model.eval()
    logger.info("Motion autoencoder loaded from %s", path)
    return model
