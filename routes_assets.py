"""
Unauthenticated asset routes used by the iOS app.

Sounds and owner videos are keyed by the model id returned from
POST /generate-3d-model (the GLB filename without its extension).
"""

import json
import logging
import shutil
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from config import CONFIG
from database import get_db
from db_models import SoundClip
from rigging_service import rig_static_model, rigged_path_for
from sound_bank import (
    decode_upload,
    extract_wav_from_video,
    read_wav,
    split_on_energy,
    validate_label,
    write_wav,
)
from video_motion import ingest_action_video

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/pet-assets", tags=["pet-assets"])


class LabelBody(BaseModel):
    label: str


def _model_paths(model_id: str) -> tuple[Path, Path]:
    if "/" in model_id or ".." in model_id:
        raise HTTPException(status_code=400, detail="invalid model id")
    static = CONFIG.models_dir / f"{model_id}.glb"
    if not static.exists():
        raise HTTPException(status_code=404, detail="model not found")
    return static, rigged_path_for(static)


def _clip_dict(clip: SoundClip) -> dict:
    return {
        "id": clip.id,
        "model_id": clip.model_id,
        "label": clip.label,
        "duration": clip.duration,
        "url": f"/sounds/{clip.model_id}/{clip.filename}",
    }


@router.get("/{model_id}")
def asset_manifest(model_id: str, db: Session = Depends(get_db)):
    static, rigged = _model_paths(model_id)
    sounds = db.query(SoundClip).filter(SoundClip.model_id == model_id).all()
    return {
        "model_id": model_id,
        "model_url": f"/models/{static.name}",
        "rigged_model_url": f"/models/{rigged.name}" if rigged.exists() else None,
        "sounds": [_clip_dict(clip) for clip in sounds],
    }


@router.get("/{model_id}/sounds")
def list_sounds(model_id: str, db: Session = Depends(get_db)):
    _model_paths(model_id)
    clips = db.query(SoundClip).filter(SoundClip.model_id == model_id).order_by(SoundClip.id).all()
    return [_clip_dict(clip) for clip in clips]


@router.post("/{model_id}/sounds")
async def upload_sound(
    model_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    _model_paths(model_id)
    raw = await file.read()
    suffix = Path(file.filename or "clip.wav").suffix or ".wav"
    work = CONFIG.sounds_dir / model_id / "_incoming"
    try:
        samples, rate = decode_upload(raw, suffix, work)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    finally:
        if work.exists():
            shutil.rmtree(work, ignore_errors=True)

    takes = split_on_energy(samples, rate)
    if not takes:
        raise HTTPException(status_code=400, detail="no sound above the silence threshold")
    return store_sound_takes(db, model_id, takes, rate)


def store_sound_takes(db: Session, model_id: str, takes, rate: int, pet_id: int | None = None):
    created = []
    dest_dir = CONFIG.sounds_dir / model_id
    dest_dir.mkdir(parents=True, exist_ok=True)
    for take in takes:
        clip = SoundClip(
            model_id=model_id,
            pet_id=pet_id,
            label="other",
            filename="pending.wav",
            duration=len(take) / rate,
        )
        db.add(clip)
        db.commit()
        db.refresh(clip)
        filename = f"clip_{clip.id}.wav"
        write_wav(dest_dir / filename, take, rate)
        clip.filename = filename
        db.commit()
        db.refresh(clip)
        created.append(_clip_dict(clip))
    return created


@router.patch("/{model_id}/sounds/{clip_id}")
def label_sound(model_id: str, clip_id: int, body: LabelBody, db: Session = Depends(get_db)):
    clip = db.query(SoundClip).filter(SoundClip.id == clip_id, SoundClip.model_id == model_id).first()
    if clip is None:
        raise HTTPException(status_code=404, detail="sound not found")
    try:
        clip.label = validate_label(body.label)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    db.commit()
    db.refresh(clip)
    return _clip_dict(clip)


@router.post("/{model_id}/videos")
async def upload_video(
    model_id: str,
    file: UploadFile = File(...),
    action: str = Form(...),
    db: Session = Depends(get_db),
):
    static, _rigged = _model_paths(model_id)
    raw = await file.read()
    CONFIG.videos_dir.mkdir(parents=True, exist_ok=True)
    video_path = CONFIG.videos_dir / f"{model_id}_{action}.mp4"
    video_path.write_bytes(raw)
    try:
        result = ingest_action_video(video_path, action.strip().lower())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    sidecar = CONFIG.models_dir / f"{model_id}_owner_clips.json"
    stored = _load_owner_json(sidecar)
    stored.update(_encode_clips(result["clips"]))
    sidecar.write_text(json.dumps(stored))
    rigged = rig_static_model(static, _decode_clips(stored))
    sounds, sound_error = _sounds_from_video(db, model_id, video_path)
    return {
        "model_id": model_id,
        "keypoint_source": result["source"],
        "replaced_presets": result["replaced"],
        "rigged_model_url": f"/models/{rigged.name}" if rigged else None,
        "sounds": sounds,
        "sound_error": sound_error,
    }


def _sounds_from_video(db: Session, model_id: str, video_path: Path) -> tuple[list, str | None]:
    wav_path = video_path.with_suffix(".wav")
    try:
        extract_wav_from_video(video_path, wav_path)
        samples, rate = read_wav(wav_path)
        takes = split_on_energy(samples, rate)
        if not takes:
            return [], "No audible sound was found in that video."
        return store_sound_takes(db, model_id, takes, rate), None
    except ValueError as exc:
        logger.info("video sound skipped: %s", exc)
        return [], str(exc)
    finally:
        if wav_path.exists():
            wav_path.unlink()


def _encode_clips(clips: dict) -> dict:
    encoded = {}
    for name, clip in clips.items():
        encoded[name] = {
            "times": [float(t) for t in clip["times"]],
            "rotations": {bone: _rows(values) for bone, values in clip["rotations"].items()},
            "translations": {bone: _rows(values) for bone, values in clip.get("translations", {}).items()},
        }
    return encoded


def _decode_clips(raw: dict) -> dict:
    import numpy as np
    decoded = {}
    for name, clip in raw.items():
        decoded[name] = {
            "times": np.asarray(clip["times"], dtype=np.float64),
            "rotations": {bone: np.asarray(values, dtype=np.float64) for bone, values in clip["rotations"].items()},
            "translations": {bone: np.asarray(values, dtype=np.float64) for bone, values in clip.get("translations", {}).items()},
        }
    return decoded


def _load_owner_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def _rows(values) -> list:
    return [[float(x) for x in row] for row in values]
