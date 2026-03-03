"""
Pet routes — CRUD + 3D generation (Supabase backend)
"""

import json
import logging
import uuid
import time
import io

import cv2
import numpy as np
from PIL import Image
from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException, status

from pet_soul.config import CONFIG
from pet_soul.db.auth import get_current_user, get_user_id
from pet_soul.db.supabase_client import get_supabase
from pet_soul.appearance.pipeline import Pet3DModelPipeline

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/pets", tags=["pets"])

# Shared pipeline instance — set from app.py
_pipeline: Pet3DModelPipeline | None = None


def set_pipeline(p: Pet3DModelPipeline):
    global _pipeline
    _pipeline = p


def _get_pipeline() -> Pet3DModelPipeline:
    if _pipeline is None:
        raise HTTPException(status_code=503, detail="Pipeline not ready")
    return _pipeline


@router.get("")
def list_pets(user_id: str = Depends(get_user_id)):
    sb = get_supabase()
    resp = (
        sb.table("pets")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )
    return [_row_to_dict(row) for row in resp.data]


@router.get("/{pet_id}")
def get_pet(pet_id: int, user_id: str = Depends(get_user_id)):
    sb = get_supabase()
    resp = (
        sb.table("pets")
        .select("*")
        .eq("id", pet_id)
        .eq("user_id", user_id)
        .maybe_single()
        .execute()
    )
    if resp.data is None:
        raise HTTPException(status_code=404, detail="Pet not found")
    return _row_to_dict(resp.data)


@router.post("")
async def create_pet(
    file: UploadFile = File(...),
    name: str = Form(...),
    user_id: str = Depends(get_user_id),
):
    pipeline = _get_pipeline()

    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    # Read and decode
    contents = await file.read()
    image = Image.open(io.BytesIO(contents))
    image_array = np.array(image)

    if len(image_array.shape) != 3 or image_array.shape[2] not in (3, 4):
        raise HTTPException(status_code=400, detail="Invalid image format")

    if image_array.shape[2] == 4:
        image_rgb = cv2.cvtColor(image_array, cv2.COLOR_RGBA2RGB)
    else:
        image_rgb = image_array

    # Generate model
    model_id = f"pet_{uuid.uuid4().hex[:8]}_{int(time.time())}"
    output_filename = f"{model_id}.glb"
    output_path = CONFIG.models_dir / output_filename

    result = pipeline.process(image_rgb, output_path=str(output_path))

    if "error" in result and "profile" not in result:
        raise HTTPException(status_code=500, detail=result["error"])

    profile = result.get("profile", {})

    # Insert into Supabase
    sb = get_supabase()
    row = {
        "user_id": user_id,
        "name": name,
        "species": profile.get("species", "dog"),
        "breed": profile.get("breed", ""),
        "breed_confidence": profile.get("breed_confidence", 0.0),
        "profile_json": profile,
        "texture_prompt": result.get("prompt", ""),
        "model_filename": output_filename if result.get("model_path") else "",
    }
    resp = sb.table("pets").insert(row).execute()
    pet = resp.data[0] if resp.data else row

    return _row_to_dict(pet)


@router.delete("/{pet_id}")
def delete_pet(pet_id: int, user_id: str = Depends(get_user_id)):
    sb = get_supabase()
    resp = (
        sb.table("pets")
        .delete()
        .eq("id", pet_id)
        .eq("user_id", user_id)
        .execute()
    )
    if not resp.data:
        raise HTTPException(status_code=404, detail="Pet not found")
    return {"success": True}


def _row_to_dict(row: dict) -> dict:
    profile = row.get("profile_json", {})
    if isinstance(profile, str):
        profile = json.loads(profile)
    return {
        "id": row.get("id"),
        "name": row.get("name", ""),
        "species": row.get("species", "dog"),
        "breed": row.get("breed", ""),
        "breed_confidence": row.get("breed_confidence", 0.0),
        "profile": profile,
        "texture_prompt": row.get("texture_prompt", ""),
        "model_url": f"/models/{row['model_filename']}" if row.get("model_filename") else None,
        "created_at": row.get("created_at"),
    }
