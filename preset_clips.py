"""
Six preset clips on the frozen dog skeleton: idle, walk, run, sit, stand, stretch.

Rotations are degrees, XYZ, local to each bone. Translation offsets are in
canonical skeleton units and must be multiplied by the mesh height scale
before they are written into a GLB.
"""

from __future__ import annotations

from typing import Dict

import numpy as np

from dog_skeleton import CLIP_NAMES

FPS = 30


def _quat_from_euler_xyz(deg: np.ndarray) -> np.ndarray:
    rad = np.radians(deg)
    rx, ry, rz = rad[..., 0], rad[..., 1], rad[..., 2]
    cx, sx = np.cos(rx * 0.5), np.sin(rx * 0.5)
    cy, sy = np.cos(ry * 0.5), np.sin(ry * 0.5)
    cz, sz = np.cos(rz * 0.5), np.sin(rz * 0.5)
    qw = cx * cy * cz + sx * sy * sz
    qx = sx * cy * cz - cx * sy * sz
    qy = cx * sy * cz + sx * cy * sz
    qz = cx * cy * sz - sx * sy * cz
    quat = np.stack([qx, qy, qz, qw], axis=-1)
    norm = np.linalg.norm(quat, axis=-1, keepdims=True)
    return quat / np.maximum(norm, 1e-8)


def _empty_tracks(times: np.ndarray) -> Dict[str, Dict[str, np.ndarray]]:
    return {"times": times, "rotations": {}, "translations": {}}


def _put_euler(clip: dict, bone: str, euler_deg: np.ndarray) -> None:
    clip["rotations"][bone] = _quat_from_euler_xyz(np.asarray(euler_deg, dtype=np.float64))


def _leg_cycle(times: np.ndarray, phase: float, lift: float, knee: float) -> np.ndarray:
    w = 2.0 * np.pi * times / times[-1]
    thigh = np.stack([
        lift * np.sin(w + phase),
        np.zeros_like(times),
        np.zeros_like(times),
    ], axis=1)
    shin = np.stack([
        -knee + 0.45 * knee * np.sin(w + phase + 0.6),
        np.zeros_like(times),
        np.zeros_like(times),
    ], axis=1)
    return thigh, shin


def build_idle() -> dict:
    times = np.arange(0, 2.0, 1.0 / FPS)
    if times[-1] < 2.0 - 1e-6:
        times = np.append(times, 2.0)
    clip = _empty_tracks(times)
    bob = 4.0 * np.sin(2 * np.pi * times / 2.0)
    _put_euler(clip, "spine_01", np.stack([bob, np.zeros_like(times), np.zeros_like(times)], axis=1))
    wag = 18.0 * np.sin(2 * np.pi * times / 0.6)
    _put_euler(clip, "tail_01", np.stack([np.zeros_like(times), wag, np.zeros_like(times)], axis=1))
    _put_euler(clip, "tail_02", np.stack([np.zeros_like(times), wag * 0.6, np.zeros_like(times)], axis=1))
    return clip


def build_walk() -> dict:
    times = np.linspace(0.0, 1.0, FPS + 1)
    clip = _empty_tracks(times)
    for bone, phase, lift, knee in (
        ("fl", 0.0, 22.0, 28.0),
        ("br", 0.0, 22.0, 28.0),
        ("fr", np.pi, 22.0, 28.0),
        ("bl", np.pi, 22.0, 28.0),
    ):
        thigh, shin = _leg_cycle(times, phase, lift, knee)
        _put_euler(clip, f"thigh_{bone}", thigh)
        _put_euler(clip, f"knee_{bone}", shin)
    _put_euler(clip, "spine_01", np.stack([6 * np.sin(2 * np.pi * times), np.zeros_like(times), np.zeros_like(times)], axis=1))
    _put_euler(clip, "tail_01", np.stack([np.zeros_like(times), 12 * np.sin(2 * np.pi * times), np.zeros_like(times)], axis=1))
    return clip


def build_run() -> dict:
    times = np.linspace(0.0, 0.55, int(0.55 * FPS) + 1)
    clip = _empty_tracks(times)
    for bone, phase in (("fl", 0.0), ("br", 0.0), ("fr", np.pi), ("bl", np.pi)):
        thigh, shin = _leg_cycle(times, phase, 38.0, 42.0)
        _put_euler(clip, f"thigh_{bone}", thigh)
        _put_euler(clip, f"knee_{bone}", shin)
    _put_euler(clip, "spine_01", np.stack([-12 + 10 * np.sin(4 * np.pi * times / times[-1]), np.zeros_like(times), np.zeros_like(times)], axis=1))
    _put_euler(clip, "tail_01", np.stack([-20 * np.ones_like(times), np.zeros_like(times), np.zeros_like(times)], axis=1))
    return clip


def _sit_pose(amount: np.ndarray) -> dict:
    times_len = len(amount)
    clip_rots = {}
    zeros = np.zeros(times_len)
    def euler(x, y, z):
        return np.stack([x, y, z], axis=1)

    clip_rots["thigh_bl"] = _quat_from_euler_xyz(euler(-70 * amount, zeros, zeros))
    clip_rots["thigh_br"] = _quat_from_euler_xyz(euler(-70 * amount, zeros, zeros))
    clip_rots["knee_bl"] = _quat_from_euler_xyz(euler(80 * amount, zeros, zeros))
    clip_rots["knee_br"] = _quat_from_euler_xyz(euler(80 * amount, zeros, zeros))
    clip_rots["spine_01"] = _quat_from_euler_xyz(euler(-18 * amount, zeros, zeros))
    clip_rots["tail_01"] = _quat_from_euler_xyz(euler(10 * amount, zeros, zeros))
    drop = -0.12 * amount
    trans = np.stack([zeros, drop, 0.04 * amount], axis=1)
    return clip_rots, {"pelvis": trans}


def build_sit() -> dict:
    times = np.linspace(0.0, 1.2, int(1.2 * FPS) + 1)
    amount = np.clip(times / 1.0, 0.0, 1.0)
    rots, trans = _sit_pose(amount)
    return {"times": times, "rotations": rots, "translations": trans}


def build_stand() -> dict:
    times = np.linspace(0.0, 1.2, int(1.2 * FPS) + 1)
    amount = 1.0 - np.clip(times / 1.0, 0.0, 1.0)
    rots, trans = _sit_pose(amount)
    return {"times": times, "rotations": rots, "translations": trans}


def build_stretch() -> dict:
    times = np.linspace(0.0, 1.6, int(1.6 * FPS) + 1)
    amount = np.sin(np.pi * np.clip(times / 1.4, 0.0, 1.0))
    zeros = np.zeros_like(times)
    clip = _empty_tracks(times)
    _put_euler(clip, "thigh_fl", np.stack([35 * amount, zeros, zeros], axis=1))
    _put_euler(clip, "thigh_fr", np.stack([35 * amount, zeros, zeros], axis=1))
    _put_euler(clip, "knee_fl", np.stack([15 * amount, zeros, zeros], axis=1))
    _put_euler(clip, "knee_fr", np.stack([15 * amount, zeros, zeros], axis=1))
    _put_euler(clip, "spine_02", np.stack([-25 * amount, zeros, zeros], axis=1))
    _put_euler(clip, "thigh_bl", np.stack([-15 * amount, zeros, zeros], axis=1))
    _put_euler(clip, "thigh_br", np.stack([-15 * amount, zeros, zeros], axis=1))
    _put_euler(clip, "tail_01", np.stack([20 * amount, zeros, zeros], axis=1))
    return clip


_BUILDERS = {
    "idle": build_idle,
    "walk": build_walk,
    "run": build_run,
    "sit": build_sit,
    "stand": build_stand,
    "stretch": build_stretch,
}


def preset_library() -> Dict[str, dict]:
    clips = {name: fn() for name, fn in _BUILDERS.items()}
    missing = [name for name in CLIP_NAMES if name not in clips]
    if missing:
        raise RuntimeError(f"missing preset clips: {missing}")
    return clips


def merge_clips(presets: Dict[str, dict], owner: Dict[str, dict]) -> Dict[str, dict]:
    """Owner clips replace presets of the same name. Missing owner actions stay preset."""
    merged = dict(presets)
    for name, clip in owner.items():
        if clip is not None:
            merged[name] = clip
    return merged
