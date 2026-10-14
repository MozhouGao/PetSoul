"""Contract tests for the rig, preset motion, sound bank, and video retarget."""

import wave
from pathlib import Path

import numpy as np

from dog_skeleton import BONE_NAMES, CLIP_NAMES
from glb_rig import animation_names, make_box_glb, read_glb, rig_glb
from pet_profile import PetProfile
from preset_clips import merge_clips, preset_library
from prompt_builder import PromptBuilder
from rigging_service import build_clip_set, rig_static_model
from sound_bank import normalize_peak, split_on_energy, validate_label, write_wav, read_wav
from video_motion import (
    keypoints_from_box,
    prefer_owner_clips,
    solve_clip,
    two_bone_ik,
    validate_capture,
    box_leaves_frame,
)


def test_prompt_asks_for_a_standing_dog():
    prompt = PromptBuilder().build_prompt(PetProfile(species="dog", breed="Beagle"))
    assert "standing on all four legs" in prompt
    assert "legs separated" in prompt
    assert "tail extended" in prompt


def test_preset_names_and_owner_preference():
    presets = preset_library()
    assert tuple(presets) == CLIP_NAMES
    owner = {"sit": presets["idle"]}
    merged = merge_clips(presets, owner)
    assert merged["sit"] is owner["sit"]
    assert merged["walk"] is presets["walk"]
    preferred = prefer_owner_clips({"stretch": presets["stretch"]})
    assert preferred["stretch"] is presets["stretch"]
    assert "run" in preferred


def test_rig_embeds_six_clips(tmp_path: Path):
    src = tmp_path / "box.glb"
    dst = tmp_path / "box_rigged.glb"
    make_box_glb(src)
    names = rig_glb(src, dst, preset_library())
    assert names == list(CLIP_NAMES)
    gltf, _ = read_glb(dst)
    assert gltf["skins"][0]["joints"]
    assert len(gltf["skins"][0]["joints"]) == len(BONE_NAMES)
    assert animation_names(dst) == list(CLIP_NAMES)
    prim = gltf["meshes"][0]["primitives"][0]
    assert "JOINTS_0" in prim["attributes"]
    assert "WEIGHTS_0" in prim["attributes"]


def test_service_writes_rigged_sibling(tmp_path: Path):
    src = tmp_path / "pet_demo.glb"
    make_box_glb(src)
    rigged = rig_static_model(src)
    assert rigged is not None
    assert rigged.name == "pet_demo_rigged.glb"
    assert set(animation_names(rigged)) == set(CLIP_NAMES)
    owner = build_clip_set({"sit": preset_library()["walk"]})
    assert owner["sit"]["times"].shape == preset_library()["walk"]["times"].shape


def test_sound_split_and_label(tmp_path: Path):
    rate = 16000
    silence = np.zeros(rate, dtype=np.float32)
    bark = (0.4 * np.sin(2 * np.pi * 400 * np.arange(rate) / rate)).astype(np.float32)
    gap = np.zeros(rate // 2, dtype=np.float32)
    whine = (0.3 * np.sin(2 * np.pi * 900 * np.arange(rate) / rate)).astype(np.float32)
    samples = np.concatenate([silence, bark, gap, whine, silence])
    takes = split_on_energy(samples, rate)
    assert len(takes) == 2
    assert abs(float(np.max(np.abs(takes[0]))) - 0.9) < 1e-3
    path = tmp_path / "take.wav"
    write_wav(path, takes[0], rate)
    loaded, loaded_rate = read_wav(path)
    assert loaded_rate == rate
    assert loaded.size > 0
    assert validate_label("Bark") == "bark"
    try:
        validate_label("meow")
        assert False
    except ValueError:
        pass
    assert abs(float(np.max(np.abs(normalize_peak(np.array([0.2, -0.1], dtype=np.float32))))) - 0.9) < 1e-5


def test_ik_bends_more_when_the_paw_is_close():
    hip = np.array([0.0, 0.4, 0.0])
    straight = np.array([0.0, 0.05, 0.2])
    bent = np.array([0.0, 0.25, 0.05])
    _, flex_straight = two_bone_ik(hip, straight, 0.2, 0.2)
    _, flex_bent = two_bone_ik(hip, bent, 0.2, 0.2)
    assert flex_bent > flex_straight


def test_side_view_solve_replaces_sit_and_keeps_idle():
    frames = []
    for i in range(8):
        box = keypoints_from_box(10, 10, 200, 120, sit=True)
        frames.append(box)
    solved = solve_clip(frames, "sit", 30)
    merged = prefer_owner_clips(solved)
    assert "sit" in solved and "stand" in solved
    assert merged["sit"] is solved["sit"]
    assert "idle" in merged


def test_capture_rules_reject_a_dog_that_leaves():
    try:
        validate_capture(1.0, [(10, 10, 100, 80)], (200, 200))
        assert False
    except ValueError as exc:
        assert "5" in str(exc)
    boxes = [(0, 80, 30, 40)] * 10
    assert box_leaves_frame(boxes[0], 200, 200)
    try:
        validate_capture(6.0, boxes, (200, 200))
        assert False
    except ValueError as exc:
        assert "leaves the frame" in str(exc)
    validate_capture(6.0, [(40, 40, 120, 100)] * 5, (200, 200))


def test_wav_roundtrip_header(tmp_path: Path):
    path = tmp_path / "a.wav"
    write_wav(path, np.array([0.0, 0.5, -0.5], dtype=np.float32), 8000)
    with wave.open(str(path)) as handle:
        assert handle.getnchannels() == 1
        assert handle.getframerate() == 8000
