"""
Frozen dog skeleton used by every generated pet and every animation clip.

Bone names are part of the contract. Do not rename them: preset clips, owner
video retargets, the Blender rig, and the Unity player all share this list.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import numpy as np

# name, parent, local translation in a canonical standing dog (Y up, Z forward).
# Legs are separated, tail is extended, four feet are below the body.
TEMPLATE_BONES: Tuple[Tuple[str, Optional[str], Tuple[float, float, float]], ...] = (
    ("root", None, (0.0, 0.0, 0.0)),
    ("pelvis", "root", (0.0, 0.42, -0.08)),
    ("spine_01", "pelvis", (0.0, 0.02, 0.12)),
    ("spine_02", "spine_01", (0.0, 0.03, 0.14)),
    ("neck", "spine_02", (0.0, 0.05, 0.10)),
    ("head", "neck", (0.0, 0.04, 0.10)),
    ("ear_l", "head", (-0.05, 0.06, 0.0)),
    ("ear_r", "head", (0.05, 0.06, 0.0)),
    ("tail_01", "pelvis", (0.0, 0.02, -0.12)),
    ("tail_02", "tail_01", (0.0, 0.03, -0.10)),
    ("tail_03", "tail_02", (0.0, 0.02, -0.09)),
    ("thigh_fl", "spine_02", (-0.07, -0.02, 0.08)),
    ("knee_fl", "thigh_fl", (0.0, -0.14, 0.03)),
    ("paw_fl", "knee_fl", (0.0, -0.12, 0.02)),
    ("thigh_fr", "spine_02", (0.07, -0.02, 0.08)),
    ("knee_fr", "thigh_fr", (0.0, -0.14, 0.03)),
    ("paw_fr", "knee_fr", (0.0, -0.12, 0.02)),
    ("thigh_bl", "pelvis", (-0.07, -0.02, -0.02)),
    ("knee_bl", "thigh_bl", (0.0, -0.14, -0.02)),
    ("paw_bl", "knee_bl", (0.0, -0.12, 0.01)),
    ("thigh_br", "pelvis", (0.07, -0.02, -0.02)),
    ("knee_br", "thigh_br", (0.0, -0.14, -0.02)),
    ("paw_br", "knee_br", (0.0, -0.12, 0.01)),
)

BONE_NAMES: Tuple[str, ...] = tuple(b[0] for b in TEMPLATE_BONES)
PARENT_OF: Dict[str, Optional[str]] = {name: parent for name, parent, _ in TEMPLATE_BONES}
CLIP_NAMES: Tuple[str, ...] = ("idle", "walk", "run", "sit", "stand", "stretch")


def template_local_translations() -> Dict[str, np.ndarray]:
    return {name: np.array(local, dtype=np.float64) for name, _, local in TEMPLATE_BONES}


def template_world_positions() -> Dict[str, np.ndarray]:
    local = template_local_translations()
    world: Dict[str, np.ndarray] = {}
    for name, parent, _ in TEMPLATE_BONES:
        world[name] = local[name].copy() if parent is None else world[parent] + local[name]
    return world


def _bounds(points: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    return points.min(axis=0), points.max(axis=0)


def place_on_mesh(vertices: np.ndarray) -> Dict[str, np.ndarray]:
    """Scale the canonical skeleton so it fills a mesh bounding box.

    Returns local translations (identity rest rotation) in mesh POSITION space.
    The longer horizontal axis of the mesh is treated as the dog's length.
    """
    if len(vertices) == 0:
        raise ValueError("mesh has no vertices")

    verts = np.asarray(vertices, dtype=np.float64)
    vmin, vmax = _bounds(verts)
    ext = np.maximum(vmax - vmin, 1e-4)

    template_world = template_world_positions()
    stacked = np.stack([template_world[n] for n in BONE_NAMES], axis=0)
    tmin, tmax = _bounds(stacked)
    text = np.maximum(tmax - tmin, 1e-4)

    length_axis = 0 if ext[0] >= ext[2] else 2
    placed_world: Dict[str, np.ndarray] = {}
    for name in BONE_NAMES:
        tn = (template_world[name] - tmin) / text
        if length_axis == 2:
            mapped = vmin + tn * ext
        else:
            mapped = np.array([
                vmin[0] + tn[2] * ext[0],
                vmin[1] + tn[1] * ext[1],
                vmin[2] + tn[0] * ext[2],
            ])
        placed_world[name] = mapped

    local: Dict[str, np.ndarray] = {}
    for name, parent, _ in TEMPLATE_BONES:
        if parent is None:
            local[name] = placed_world[name]
        else:
            local[name] = placed_world[name] - placed_world[parent]
    return local


def height_scale(vertices: np.ndarray) -> float:
    """How much taller the mesh is than the canonical skeleton, for pose offsets."""
    verts = np.asarray(vertices, dtype=np.float64)
    mesh_h = max(float(verts[:, 1].max() - verts[:, 1].min()), 1e-4)
    worlds = np.stack(list(template_world_positions().values()), axis=0)
    template_h = max(float(worlds[:, 1].max() - worlds[:, 1].min()), 1e-4)
    return mesh_h / template_h
