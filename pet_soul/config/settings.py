"""
Central configuration for Pet Digital Twin Platform
"""

import os
from dataclasses import dataclass, field
from pathlib import Path

# Anchor all paths to the project root regardless of where this file lives
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


@dataclass(frozen=True)
class Config:
    # Paths
    static_dir: Path = field(default_factory=lambda: PROJECT_ROOT / "static")
    models_dir: Path = field(default_factory=lambda: PROJECT_ROOT / "models")
    frontend_dist: Path = field(default_factory=lambda: PROJECT_ROOT / "frontend" / "dist")
    yolo_model: str = "yolov8n.pt"

    # Auth0
    auth0_domain: str = field(default_factory=lambda: os.environ.get("AUTH0_DOMAIN", ""))
    auth0_audience: str = field(default_factory=lambda: os.environ.get("AUTH0_AUDIENCE", ""))
    auth0_client_id: str = field(default_factory=lambda: os.environ.get("AUTH0_CLIENT_ID", ""))

    # Supabase
    supabase_url: str = field(default_factory=lambda: os.environ.get("SUPABASE_URL", ""))
    supabase_key: str = field(default_factory=lambda: os.environ.get("SUPABASE_KEY", ""))

    # Model names
    clip_model_name: str = "openai/clip-vit-base-patch32"

    # Detection
    yolo_conf_threshold: float = 0.25
    crop_padding_px: int = 20

    # CLIP thresholds
    coat_color_threshold: float = 0.05
    marking_threshold: float = 0.15
    max_coat_colors: int = 3

    # 3D generation (Meshy.ai API)
    default_output_format: str = "glb"
    meshy_ai_model: str = "meshy-6"
    meshy_target_polycount: int = 15000
    meshy_topology: str = "triangle"
    meshy_enable_pbr: bool = True
    meshy_poll_interval: float = 5.0
    meshy_timeout: float = 600.0

    # Motion module
    motion_latent_dim: int = 64
    motion_hidden_dim: int = 128
    motion_seq_length: int = 60  # frames per clip

    # Behavior engine
    behavior_update_hz: float = 10.0  # FSM update rate
    idle_timeout_sec: float = 5.0

    # Audio
    audio_sample_rate: int = 22050
    audio_n_mfcc: int = 13
    audio_hop_length: int = 512

    # World model (v3.0)
    world_model_latent_dim: int = 32
    world_model_hidden_dim: int = 64

    # Server
    host: str = "0.0.0.0"
    port: int = 8000


CONFIG = Config()
