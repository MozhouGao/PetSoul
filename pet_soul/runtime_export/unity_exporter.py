"""
Unity Exporter — packages mesh, animation, and personality for Unity.

Produces a self-contained export bundle (directory or ZIP) that a Unity
project can import directly:

    <export_dir>/
        model.glb                    # 3D mesh from Meshy
        personality.json             # PersonalityProfile
        motion_latent.npy            # Motion autoencoder latent vector
        motion_stats.json            # Raw motion statistics
        audio_stats.json             # Audio feature summary
        animation_curves.json        # Baked keyframe animation data
        manifest.json                # Bundle metadata
"""

import json
import logging
import shutil
import zipfile
from pathlib import Path
from typing import Dict, Optional

import numpy as np

logger = logging.getLogger(__name__)


def export_to_unity(
    output_dir: str,
    mesh_path: Optional[str] = None,
    personality: Optional[Dict] = None,
    motion_latent: Optional[np.ndarray] = None,
    motion_stats: Optional[Dict] = None,
    audio_stats: Optional[Dict] = None,
    animation_curves: Optional[Dict] = None,
    metadata: Optional[Dict] = None,
) -> str:
    """Create a Unity-ready export bundle.

    Args:
        output_dir: Destination directory for the bundle.
        mesh_path: Path to the generated GLB/FBX mesh file.
        personality: PersonalityProfile.to_dict() output.
        motion_latent: Encoded motion latent vector.
        motion_stats: Raw motion feature statistics.
        audio_stats: Audio feature summary.
        animation_curves: Baked animation keyframe data.
        metadata: Extra metadata (pet name, species, breed, etc.).

    Returns:
        Path to the export directory.
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    # 1. Copy mesh file
    if mesh_path and Path(mesh_path).exists():
        ext = Path(mesh_path).suffix
        shutil.copy2(mesh_path, out / f"model{ext}")
        logger.info("Exported mesh → %s", out / f"model{ext}")

    # 2. Personality profile
    if personality:
        _write_json(out / "personality.json", personality)

    # 3. Motion latent vector
    if motion_latent is not None:
        np.save(str(out / "motion_latent.npy"), motion_latent)
        logger.info("Exported motion latent → motion_latent.npy")

    # 4. Motion statistics
    if motion_stats:
        _write_json(out / "motion_stats.json", motion_stats)

    # 5. Audio statistics
    if audio_stats:
        _write_json(out / "audio_stats.json", audio_stats)

    # 6. Animation curves (keyframe data for Unity Animator)
    if animation_curves:
        _write_json(out / "animation_curves.json", animation_curves)

    # 7. Manifest
    manifest = {
        "format_version": "1.0",
        "has_mesh": mesh_path is not None,
        "has_personality": personality is not None,
        "has_motion": motion_latent is not None,
        "has_audio": audio_stats is not None,
        "has_animation": animation_curves is not None,
    }
    if metadata:
        manifest["metadata"] = metadata
    _write_json(out / "manifest.json", manifest)

    logger.info("Unity export bundle created at %s", out)
    return str(out)


def export_to_zip(
    output_dir: str,
    zip_path: str,
) -> str:
    """Compress an export bundle directory into a ZIP file.

    Args:
        output_dir: Path to the export bundle directory.
        zip_path: Destination ZIP file path.

    Returns:
        Path to the created ZIP file.
    """
    out = Path(output_dir)
    zp = Path(zip_path)
    zp.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as zf:
        for file in out.rglob("*"):
            if file.is_file():
                arcname = file.relative_to(out)
                zf.write(file, arcname)

    logger.info("Export bundle zipped → %s", zp)
    return str(zp)


def keypoints_to_animation_curves(
    keypoints_3d: np.ndarray,
    fps: float = 30.0,
    keypoint_names: Optional[list] = None,
) -> Dict:
    """Convert 3D keypoint sequences into Unity-compatible animation curves.

    Args:
        keypoints_3d: (T, J, 3) array.
        fps: Frame rate.
        keypoint_names: Optional names for each joint.

    Returns:
        Dictionary with ``fps``, ``duration``, and per-joint ``curves``.
    """
    T, J, _ = keypoints_3d.shape
    duration = T / fps

    if keypoint_names is None:
        keypoint_names = [f"joint_{i}" for i in range(J)]

    curves = {}
    for j in range(J):
        name = keypoint_names[j] if j < len(keypoint_names) else f"joint_{j}"
        curves[name] = {
            "x": keypoints_3d[:, j, 0].tolist(),
            "y": keypoints_3d[:, j, 1].tolist(),
            "z": keypoints_3d[:, j, 2].tolist(),
        }

    return {
        "fps": fps,
        "duration": round(duration, 4),
        "num_frames": T,
        "num_joints": J,
        "curves": curves,
    }


def _write_json(path: Path, data: dict):
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)
    logger.info("Exported %s", path.name)
