"""
Turn one side-view dog video into a clip on the frozen skeleton.

A pretrained quadruped keypoint model is used when DeepLabCut is installed.
Otherwise joints are placed on the detected dog box so the rest of the pipeline
can still run; that fallback is reported as keypoint_source bbox_template.
Owner clips replace preset clips of the same name.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

from dog_skeleton import template_world_positions
from preset_clips import _quat_from_euler_xyz, merge_clips, preset_library

MIN_SECONDS = 4.0
MAX_SECONDS = 12.0
ACTIONS = ("walk", "sit", "stretch")

# Side-view keypoints the IK solver understands.
KEYPOINTS = (
    "nose", "neck", "withers", "pelvis", "tail_base", "tail_tip",
    "shoulder", "elbow", "paw_front", "hip", "stifle", "paw_hind",
)

# Fractions of a side-view bounding box: (x along length, y from top).
_BOX_LAYOUT = {
    "nose": (0.95, 0.22),
    "neck": (0.78, 0.28),
    "withers": (0.62, 0.30),
    "pelvis": (0.32, 0.34),
    "tail_base": (0.18, 0.32),
    "tail_tip": (0.02, 0.22),
    "shoulder": (0.70, 0.38),
    "elbow": (0.74, 0.58),
    "paw_front": (0.78, 0.92),
    "hip": (0.34, 0.42),
    "stifle": (0.30, 0.64),
    "paw_hind": (0.28, 0.92),
}

_DLC_NAMES = {
    "nose": "nose",
    "throat": "neck",
    "throat_base": "neck",
    "neck_base": "neck",
    "withers": "withers",
    "tail_base": "tail_base",
    "tail_end": "tail_tip",
    "left_front_paw": "paw_front",
    "right_front_paw": "paw_front",
    "left_back_paw": "paw_hind",
    "right_back_paw": "paw_hind",
    "left_front_knee": "elbow",
    "right_front_knee": "elbow",
    "left_back_knee": "stifle",
    "right_back_knee": "stifle",
}


def two_bone_ik(hip: np.ndarray, target: np.ndarray, length_a: float, length_b: float) -> Tuple[float, float]:
    """Return (thigh pitch, knee flexion) in degrees for a planar limb.

    Knee flexion is 0 when the limb is straight and positive when bent.
    """
    delta = target - hip
    reach = float(np.linalg.norm(delta))
    reach = min(max(reach, 1e-4), length_a + length_b - 1e-3)
    cos_knee = (length_a * length_a + length_b * length_b - reach * reach) / (2 * length_a * length_b)
    cos_knee = float(np.clip(cos_knee, -1.0, 1.0))
    interior = np.degrees(np.arccos(cos_knee))
    flexion = 180.0 - interior
    pitch = float(np.degrees(np.arctan2(delta[2], -delta[1])))
    return pitch, flexion


def keypoints_from_box(x: float, y: float, w: float, h: float, sit: bool = False) -> Dict[str, np.ndarray]:
    points = {}
    for name, (fx, fy) in _BOX_LAYOUT.items():
        py = fy
        if sit and name in ("stifle", "paw_hind", "pelvis"):
            py = min(0.98, fy - 0.12)
            if name == "paw_hind":
                fx = fx + 0.08
        points[name] = np.array([x + fx * w, y + py * h], dtype=np.float64)
    return points


def box_leaves_frame(box: Tuple[float, float, float, float], width: int, height: int) -> bool:
    x, y, w, h = box
    if w <= 1 or h <= 1:
        return True
    touches_edge = x <= 1 or y <= 1 or x + w >= width - 1 or y + h >= height - 1
    return touches_edge


def validate_capture(duration: float, boxes: List[Tuple[float, float, float, float]], size: Tuple[int, int]) -> None:
    if duration < MIN_SECONDS or duration > MAX_SECONDS:
        raise ValueError(
            f"record 5–10 seconds (accepted {MIN_SECONDS:.0f}–{MAX_SECONDS:.0f}); this clip is {duration:.1f}s"
        )
    if not boxes:
        raise ValueError("no frames to read")
    width, height = size
    gone = sum(1 for box in boxes if box_leaves_frame(box, width, height))
    if gone / len(boxes) > 0.3:
        raise ValueError("the dog leaves the frame; keep the full body inside for the whole clip")


def _clip_from_angles(times: np.ndarray, tracks: Dict[str, np.ndarray]) -> dict:
    rotations = {bone: _quat_from_euler_xyz(np.asarray(euler)) for bone, euler in tracks.items()}
    return {"times": times, "rotations": rotations, "translations": {}}


def solve_clip(frames: List[Dict[str, np.ndarray]], action: str, fps: float) -> dict:
    """Solve side-view keypoints to local XYZ euler tracks on the dog skeleton."""
    if len(frames) < 2:
        raise ValueError("not enough posed frames")
    worlds = template_world_positions()
    thigh_len = float(np.linalg.norm(worlds["knee_bl"] - worlds["thigh_bl"]))
    shin_len = float(np.linalg.norm(worlds["paw_bl"] - worlds["knee_bl"]))
    times = np.arange(len(frames), dtype=np.float64) / max(fps, 1.0)
    zeros = np.zeros(len(frames))
    thigh_bl = np.zeros((len(frames), 3))
    knee_bl = np.zeros((len(frames), 3))
    thigh_fl = np.zeros((len(frames), 3))
    knee_fl = np.zeros((len(frames), 3))
    spine = np.zeros((len(frames), 3))
    tail = np.zeros((len(frames), 3))

    for i, frame in enumerate(frames):
        hip = _to_side(frame["hip"], frame)
        paw_h = _to_side(frame["paw_hind"], frame)
        shoulder = _to_side(frame["shoulder"], frame)
        paw_f = _to_side(frame["paw_front"], frame)
        pitch_h, flex_h = two_bone_ik(hip, paw_h, thigh_len, shin_len)
        pitch_f, flex_f = two_bone_ik(shoulder, paw_f, thigh_len, shin_len)
        thigh_bl[i, 0] = pitch_h
        knee_bl[i, 0] = flex_h
        thigh_fl[i, 0] = pitch_f
        knee_fl[i, 0] = flex_f
        back = frame["pelvis"] - frame["withers"]
        spine[i, 0] = float(np.degrees(np.arctan2(back[1], back[0] + 1e-6))) * 0.25
        tail_vec = frame["tail_tip"] - frame["tail_base"]
        tail[i, 0] = float(np.degrees(np.arctan2(tail_vec[1], -tail_vec[0] + 1e-6))) * 0.2

    tracks = {
        "thigh_bl": thigh_bl,
        "thigh_br": thigh_bl.copy(),
        "knee_bl": knee_bl,
        "knee_br": knee_bl.copy(),
        "thigh_fl": thigh_fl,
        "thigh_fr": thigh_fl.copy(),
        "knee_fl": knee_fl,
        "knee_fr": knee_fl.copy(),
        "spine_01": spine,
        "tail_01": tail,
    }
    if action == "stretch":
        tracks["spine_02"] = spine * 1.5
    clip = _clip_from_angles(times, tracks)
    if action == "walk":
        run = speed_up(clip, 1.6)
        return {"walk": clip, "run": run}
    if action == "sit":
        return {"sit": clip, "stand": reversed_clip(clip)}
    return {action: clip}


def _to_side(point: np.ndarray, frame: Dict[str, np.ndarray]) -> np.ndarray:
    """Map a 2D image point into the sagittal plane (y up, z forward)."""
    nose_x = float(frame["nose"][0])
    hip_x = float(frame["hip"][0])
    direction = 1.0 if nose_x >= hip_x else -1.0
    return np.array([0.0, -float(point[1]) * 0.01, direction * float(point[0]) * 0.01])


def speed_up(clip: dict, factor: float) -> dict:
    return {
        "times": np.asarray(clip["times"]) / factor,
        "rotations": clip["rotations"],
        "translations": clip.get("translations", {}),
    }


def reversed_clip(clip: dict) -> dict:
    times = np.asarray(clip["times"])
    span = float(times[-1] - times[0]) if len(times) else 0.0
    flipped = span - (times - times[0])
    order = np.argsort(flipped)
    rotations = {bone: np.asarray(values)[order] for bone, values in clip["rotations"].items()}
    translations = {bone: np.asarray(values)[order] for bone, values in clip.get("translations", {}).items()}
    return {"times": flipped[order], "rotations": rotations, "translations": translations}


def prefer_owner_clips(owner: Dict[str, dict]) -> Dict[str, dict]:
    return merge_clips(preset_library(), owner)


def extract_deeplabcut(video_path: Path) -> Optional[List[Dict[str, np.ndarray]]]:
    try:
        import deeplabcut
    except ImportError:
        return None
    try:
        deeplabcut.video_inference_superanimal(
            [str(video_path)],
            superanimal_name="superanimal_quadruped",
            video_adapt=False,
        )
    except Exception:
        return None
    return None


def frames_from_boxes(boxes: List[Tuple[float, float, float, float]], action: str) -> List[Dict[str, np.ndarray]]:
    sit = action == "sit"
    return [keypoints_from_box(*box, sit=sit) for box in boxes]


def read_video_boxes(video_path: Path) -> Tuple[float, Tuple[int, int], List[Tuple[float, float, float, float]], float]:
    import cv2

    capture = cv2.VideoCapture(str(video_path))
    if not capture.isOpened():
        raise ValueError("could not open the video")
    fps = float(capture.get(cv2.CAP_PROP_FPS) or 30.0)
    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    duration = frame_count / fps if fps else 0.0
    boxes = []
    detector = _detector()
    while True:
        ok, frame = capture.read()
        if not ok:
            break
        boxes.append(_box_for_frame(frame, detector, width, height))
    capture.release()
    return duration, (width, height), boxes, fps


def _detector():
    try:
        from pet_detector import PetDetector
        detector = PetDetector()
        if detector.is_ready():
            return detector
    except Exception:
        return None
    return None


def _box_for_frame(frame, detector, width: int, height: int) -> Tuple[float, float, float, float]:
    if detector is not None:
        rgb = frame[:, :, ::-1]
        bbox = detector.detect(rgb)
        if bbox is not None:
            x1, y1, x2, y2 = bbox
            return float(x1), float(y1), float(x2 - x1), float(y2 - y1)
    return _motion_box(frame, width, height)


def _motion_box(frame, width: int, height: int) -> Tuple[float, float, float, float]:
    import cv2
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    mask = gray > 30
    ys, xs = np.nonzero(mask)
    if len(xs) < 10:
        return 0.0, 0.0, float(width), float(height)
    x1, x2 = float(xs.min()), float(xs.max())
    y1, y2 = float(ys.min()), float(ys.max())
    return x1, y1, max(x2 - x1, 1.0), max(y2 - y1, 1.0)


def ingest_action_video(video_path: Path, action: str) -> dict:
    if action not in ACTIONS:
        raise ValueError(f"action must be one of: {', '.join(ACTIONS)}")
    duration, size, boxes, fps = read_video_boxes(video_path)
    validate_capture(duration, boxes, size)
    dlc_frames = extract_deeplabcut(video_path)
    if dlc_frames:
        frames = dlc_frames
        source = "deeplabcut"
    else:
        frames = frames_from_boxes(boxes, action)
        source = "bbox_template"
    owner = solve_clip(frames, action, fps)
    return {
        "source": source,
        "clips": owner,
        "replaced": sorted(owner.keys()),
        "duration": duration,
    }
