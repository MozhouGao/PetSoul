"""
Rig a static Meshy GLB onto the frozen dog skeleton and embed clips.

Blender's automatic weights are used when the `blender` executable is on PATH.
Otherwise the Python skin in glb_rig binds the same skeleton and the same clips.
"""

from __future__ import annotations

import json
import logging
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Optional

from dog_skeleton import BONE_NAMES, PARENT_OF, place_on_mesh
from glb_rig import _largest_mesh, read_glb, rig_glb
from preset_clips import merge_clips, preset_library

logger = logging.getLogger(__name__)

BLENDER_SCRIPT = Path(__file__).parent / "tools" / "rig_dog.py"


def rigged_path_for(static_glb: Path) -> Path:
    static_glb = Path(static_glb)
    return static_glb.with_name(f"{static_glb.stem}_rigged.glb")


def build_clip_set(owner: Optional[Dict[str, dict]] = None) -> Dict[str, dict]:
    if not owner:
        return preset_library()
    return merge_clips(preset_library(), owner)


def rig_static_model(static_glb: Path, owner_clips: Optional[Dict[str, dict]] = None) -> Optional[Path]:
    """Write `{stem}_rigged.glb` beside the static file. Returns None if rigging fails."""
    static_glb = Path(static_glb)
    if not static_glb.exists():
        logger.error("cannot rig missing mesh %s", static_glb)
        return None
    destination = rigged_path_for(static_glb)
    clips = build_clip_set(owner_clips)
    try:
        if shutil.which("blender") and BLENDER_SCRIPT.exists():
            if _rig_with_blender(static_glb, destination, clips):
                return destination
            logger.warning("Blender rig failed for %s; using the Python skin", static_glb.name)
        rig_glb(static_glb, destination, clips)
        return destination
    except Exception:
        logger.exception("rigging failed for %s", static_glb)
        return None


def _rig_with_blender(src: Path, dst: Path, clips: Dict[str, dict]) -> bool:
    gltf, blob = read_glb(src)
    _, _, vertices = _largest_mesh(gltf, blob)
    local = place_on_mesh(vertices)
    spec = {
        "bones": [
            {"name": name, "parent": PARENT_OF[name], "local": [float(v) for v in local[name]]}
            for name in BONE_NAMES
        ],
        "clips": _clips_for_blender(clips, local),
    }
    with tempfile.TemporaryDirectory() as tmp:
        spec_path = Path(tmp) / "spec.json"
        spec_path.write_text(json.dumps(spec))
        result = subprocess.run(
            [
                "blender", "--background", "--python", str(BLENDER_SCRIPT),
                "--", str(src), str(dst), str(spec_path),
            ],
            capture_output=True,
            text=True,
            timeout=180,
        )
    if result.returncode != 0 or not dst.exists():
        logger.warning("blender stderr: %s", result.stderr[-500:] if result.stderr else "")
        return False
    return True


def _clips_for_blender(clips: Dict[str, dict], rest_local: Dict[str, "object"]) -> dict:
    encoded = {}
    for name, clip in clips.items():
        rotations = {
            bone: np_list(values) for bone, values in clip["rotations"].items()
        }
        translations = {}
        for bone, offsets in clip.get("translations", {}).items():
            rest = rest_local[bone]
            full = [[float(rest[i] + row[i]) for i in range(3)] for row in offsets]
            translations[bone] = full
        encoded[name] = {
            "times": [float(t) for t in clip["times"]],
            "rotations": rotations,
            "translations": translations,
        }
    return encoded


def np_list(values) -> list:
    return [[float(x) for x in row] for row in values]
