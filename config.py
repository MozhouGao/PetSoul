"""
Central configuration for Pet 3D Model Generator
"""

import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class Config:
    # Paths
    static_dir: Path = Path(__file__).parent / "static"
    models_dir: Path = Path(__file__).parent / "models"
    frontend_dist: Path = Path(__file__).parent / "frontend" / "dist"
    db_path: Path = Path(__file__).parent / "pet_soul.db"
    yolo_model: str = "yolov8n.pt"

    # Auth
    jwt_secret: str = field(default_factory=lambda: os.environ.get("JWT_SECRET", "dev-secret-change-me"))
    jwt_expiry_days: int = 30

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

    # Server
    host: str = "0.0.0.0"
    port: int = 8000


CONFIG = Config()
