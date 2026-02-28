"""
Pet routes — CRUD + 3D generation
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
from sqlalchemy.orm import Session

from config import CONFIG
from database import get_db
from db_models import Pet, User
from auth import get_current_user
from pipeline import Pet3DModelPipeline

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
def list_pets(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    pets = db.query(Pet).filter(Pet.user_id == user.id).order_by(Pet.created_at.desc()).all()
    return [_pet_to_dict(p) for p in pets]


@router.get("/{pet_id}")
def get_pet(pet_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    pet = db.query(Pet).filter(Pet.id == pet_id, Pet.user_id == user.id).first()
    if not pet:
        raise HTTPException(status_code=404, detail="Pet not found")
    return _pet_to_dict(pet)


@router.post("")
async def create_pet(
    file: UploadFile = File(...),
    name: str = Form(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
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

    pet = Pet(
        user_id=user.id,
        name=name,
        species=profile.get("species", "dog"),
        breed=profile.get("breed", ""),
        breed_confidence=profile.get("breed_confidence", 0.0),
        profile_json=json.dumps(profile),
        texture_prompt=result.get("prompt", ""),
        model_filename=output_filename if result.get("model_path") else "",
    )
    db.add(pet)
    db.commit()
    db.refresh(pet)

    return _pet_to_dict(pet)


@router.delete("/{pet_id}")
def delete_pet(pet_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    pet = db.query(Pet).filter(Pet.id == pet_id, Pet.user_id == user.id).first()
    if not pet:
        raise HTTPException(status_code=404, detail="Pet not found")
    db.delete(pet)
    db.commit()
    return {"success": True}


def _pet_to_dict(pet: Pet) -> dict:
    return {
        "id": pet.id,
        "name": pet.name,
        "species": pet.species,
        "breed": pet.breed,
        "breed_confidence": pet.breed_confidence,
        "profile": json.loads(pet.profile_json) if pet.profile_json else {},
        "texture_prompt": pet.texture_prompt,
        "model_url": f"/models/{pet.model_filename}" if pet.model_filename else None,
        "created_at": pet.created_at.isoformat() if pet.created_at else None,
    }
