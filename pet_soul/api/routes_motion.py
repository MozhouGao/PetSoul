"""
Motion routes — video upload, pose extraction, motion analysis.
"""

import logging
import tempfile
from pathlib import Path

import numpy as np
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException

from pet_soul.db.auth import get_user_id
from pet_soul.db.supabase_client import get_supabase
from pet_soul.motion.pose_extractor import PoseExtractor
from pet_soul.motion.lift_2d_to_3d import lift_sequence, smooth_trajectory
from pet_soul.motion.motion_features import compute_motion_stats, build_personality_vector
from pet_soul.behavior.personality import profile_from_motion_stats

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/motion", tags=["motion"])

# Lazy-initialised pose extractor
_pose_extractor: PoseExtractor | None = None


def _get_extractor() -> PoseExtractor:
    global _pose_extractor
    if _pose_extractor is None:
        _pose_extractor = PoseExtractor(backend="mediapipe")
    return _pose_extractor


@router.post("/analyze-video")
async def analyze_video(
    file: UploadFile = File(...),
    pet_id: int | None = None,
    user_id: str = Depends(get_user_id),
):
    """Upload a pet video and extract motion data + personality profile.

    Steps:
        1. Extract 2D keypoints via MediaPipe
        2. Lift to 3D + temporal smoothing
        3. Compute motion statistics
        4. Derive personality profile
        5. (Optional) Store results linked to a pet in Supabase

    Returns JSON with keypoints summary, stats, and personality.
    """
    if not file.content_type or not file.content_type.startswith("video/"):
        raise HTTPException(status_code=400, detail="File must be a video")

    # Save upload to temp file (MediaPipe needs a file path)
    contents = await file.read()
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
        tmp.write(contents)
        tmp_path = tmp.name

    try:
        extractor = _get_extractor()

        # 1. Pose extraction
        keypoints_2d = extractor.extract_from_video(tmp_path)
        if keypoints_2d.shape[0] == 0:
            raise HTTPException(status_code=422, detail="No poses detected in video")

        # 2. 3D lifting + smoothing
        keypoints_3d = lift_sequence(keypoints_2d)
        keypoints_3d = smooth_trajectory(keypoints_3d)

        # 3. Motion statistics
        stats = compute_motion_stats(keypoints_3d)

        # 4. Personality profile
        personality = profile_from_motion_stats(stats)
        personality_dict = personality.to_dict()

        # 5. Store in Supabase if pet_id provided
        if pet_id is not None:
            sb = get_supabase()
            sb.table("motion_data").insert({
                "pet_id": pet_id,
                "user_id": user_id,
                "keypoints": {
                    "shape": list(keypoints_3d.shape),
                    "frames": keypoints_3d.shape[0],
                },
                "stats": stats,
            }).execute()

            sb.table("personality_profiles").insert({
                "pet_id": pet_id,
                "user_id": user_id,
                "vector": personality_dict,
            }).execute()

        return {
            "success": True,
            "frames_analyzed": keypoints_3d.shape[0],
            "motion_stats": stats,
            "personality": personality_dict,
        }

    finally:
        Path(tmp_path).unlink(missing_ok=True)


@router.post("/analyze-audio")
async def analyze_audio(
    file: UploadFile = File(...),
    pet_id: int | None = None,
    user_id: str = Depends(get_user_id),
):
    """Upload a pet audio clip and extract vocal features + classification."""
    if not file.content_type or not file.content_type.startswith("audio/"):
        raise HTTPException(status_code=400, detail="File must be audio")

    contents = await file.read()
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp.write(contents)
        tmp_path = tmp.name

    try:
        from pet_soul.audio.feature_extractor import load_audio, extract_mfcc, extract_audio_stats
        from pet_soul.audio.audio_classifier import PetAudioClassifier

        waveform = load_audio(tmp_path)
        mfcc = extract_mfcc(waveform)
        audio_stats = extract_audio_stats(waveform)

        classifier = PetAudioClassifier()
        classification = classifier.classify(mfcc)

        return {
            "success": True,
            "audio_stats": audio_stats,
            "classification": classification,
        }

    finally:
        Path(tmp_path).unlink(missing_ok=True)


@router.get("/personality/{pet_id}")
def get_personality(pet_id: int, user_id: str = Depends(get_user_id)):
    """Retrieve the latest personality profile for a pet."""
    sb = get_supabase()
    resp = (
        sb.table("personality_profiles")
        .select("*")
        .eq("pet_id", pet_id)
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    if not resp.data:
        raise HTTPException(status_code=404, detail="No personality profile found")
    return resp.data[0]
